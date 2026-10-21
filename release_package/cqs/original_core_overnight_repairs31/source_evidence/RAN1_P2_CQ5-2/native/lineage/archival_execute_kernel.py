#!/usr/bin/env python3
"""Execute local proposed references on owned archived graphs, one WG at a time.

No public code, benchmark, graph property or historical measurement is edited.
References are streamed as native positional values. Every transaction rolls
back. Incomplete or unsupported outputs never become gold. Receipts are keyed
by query SHA256 and preserved independently of the current candidate ledger.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import logging
from pathlib import Path
import subprocess
import sys
import time

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
HELPERS = Path('/home/sihyeon/workspace/spectra-public/spec-trace/release_package/cqs/contract_repair_v1')
SOURCE = ROOT / 'logs/publication/paper/under-review/kdd-2027-datasets-benchmarks/baseline-runs/_source_contract_expansion_v1'
ROW_LIMIT = 100000
BYTE_LIMIT = 256 * 1024 * 1024
TIMEOUT_SECONDS = 60


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(mod)
    return mod


def helpers():
    frozen = json.loads((SOURCE / 'frozen_manifest.json').read_text())
    for entry in frozen['helper_pins'] + frozen['graph_import_pins']:
        if sha(HELPERS / entry['relative_path']) != entry['sha256']:
            raise ValueError('owned source helper/import manifest changed')
    sys.path.insert(0, str(HELPERS))
    import replay_generated_read_queries as guard
    import execute_frozen_reference_gold as source
    mod = load(ROOT / 'scripts/publication/paper/under-review/kdd-2027-datasets-benchmarks/rebuttal/new_measurement_v1/source_contract_expansion_v1.py', 'native_source_kernel')
    if sha(mod.__file__) != frozen['runner_sha256']:
        raise ValueError('native source capture kernel changed')
    return guard, source, mod


def output_paths(item):
    query_hash = hashlib.sha256(item['candidate_query'].encode()).hexdigest()
    parent = BASE / 'reference_outputs' / item['id']
    parent.mkdir(parents=True, exist_ok=True)
    return query_hash, parent / (query_hash + '.jsonl'), parent / (query_hash + '.json')


def execute(item, guard, native):
    from neo4j import GraphDatabase, READ_ACCESS
    query_hash, rows_path, receipt_path = output_paths(item)
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if (receipt.get('id') != item['id'] or receipt.get('wg') != item['wg']
                or receipt.get('query_sha256') != query_hash
                or receipt.get('query') != item['candidate_query']
                or receipt.get('rows_file') != str(rows_path.relative_to(BASE))):
            raise ValueError('cached reference identity/query/path mismatch')
        if receipt['rows_sha256'] != sha(rows_path):
            raise ValueError('captured reference rows changed')
        if receipt['status'] == 'OK' and not (
                receipt.get('full_rows_available') is True and receipt.get('rollback_completed') is True
                and receipt.get('execution_summary_complete') is True
                and receipt.get('execution_query_type') == 'r'
                and receipt.get('plan_query_type') == 'r' and receipt.get('truncated') is False):
            raise ValueError('cached success lacks complete read-only evidence')
        # Failed captures remain failures. A retry needs an explicit separately
        # recorded attempt, never an overwrite of a historical receipt.
        return receipt
    query = item['candidate_query']
    result = {'id': item['id'], 'wg': item['wg'], 'query_sha256': query_hash,
              'query': query, 'started_utc': utc(), 'status': 'ERROR',
              'rows_file': str(rows_path.relative_to(BASE)), 'columns': [],
              'truncated': False, 'rollback_completed': False,
              'source': 'new read-only execution on owned archived TTL restoration',
              'limits': {'rows': ROW_LIMIT, 'bytes': BYTE_LIMIT, 'timeout_s': TIMEOUT_SECONDS}}
    count, written, begin = 0, 0, time.monotonic()
    with rows_path.open('x', encoding='utf-8') as stream:
        try:
            guard.screen_query(query)
            guard.owned_container_guard(item['wg'])
            with GraphDatabase.driver(f'bolt://127.0.0.1:{guard.PORTS[item["wg"]]}', auth=None,
                                      connection_timeout=5, max_transaction_retry_time=0) as driver:
                with driver.session(database='neo4j', default_access_mode=READ_ACCESS, fetch_size=100) as session:
                    tx = session.begin_transaction(timeout=TIMEOUT_SECONDS)
                    try:
                        plan = tx.run('EXPLAIN ' + query).consume()
                        guard.require_read_plan(plan)
                        result['plan_query_type'] = plan.query_type
                        cursor = tx.run(query)
                        result['columns'] = list(cursor.keys())
                        if len(set(result['columns'])) != len(result['columns']):
                            raise ValueError('duplicate returned field names')
                        for record in cursor:
                            row = [record[i] for i in range(len(result['columns']))]
                            if not all(native.simple_json(value) for value in row):
                                result['status'] = 'UNSUPPORTED_NATIVE_VALUE'
                                break
                            encoded = json.dumps(row, ensure_ascii=False, allow_nan=False, separators=(',', ':')) + '\n'
                            if count >= ROW_LIMIT or written + len(encoded.encode()) > BYTE_LIMIT:
                                result.update(status='STORAGE_LIMIT', truncated=True)
                                break
                            stream.write(encoded)
                            count += 1
                            written += len(encoded.encode())
                        else:
                            actual = cursor.consume()
                            if actual.query_type != 'r' or actual.counters.contains_updates or actual.counters.contains_system_updates:
                                raise ValueError('execution was not an ordinary read')
                            result.update(status='OK', execution_query_type=actual.query_type,
                                          execution_summary_complete=True)
                    finally:
                        tx.rollback()
                        result['rollback_completed'] = True
        except Exception as exc:
            result.update(status='ERROR', error_class=type(exc).__name__, error=str(exc)[:1500])
    result.update(rows_retained=count, bytes_retained=written, rows_sha256=sha(rows_path),
                  finished_utc=utc(), elapsed_s=round(time.monotonic()-begin, 4),
                  full_rows_available=result['status']=='OK')
    receipt_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    with (BASE / 'execution_events.jsonl').open('a') as stream:
        stream.write(json.dumps({'id': item['id'], 'query_sha256': query_hash,
                                'receipt': str(receipt_path.relative_to(BASE)),
                                'status': result['status'], 'finished_utc': result['finished_utc']}) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wg', required=True, choices=[f'RAN{i}' for i in range(1,6)])
    parser.add_argument('--input', type=Path, required=True)
    args = parser.parse_args()
    guard, source, native = helpers()
    input_hash = sha(args.input)
    input_text = args.input.read_text()
    if sha(args.input) != input_hash:
        raise ValueError('execution input changed while reading')
    items = [json.loads(line) for line in input_text.splitlines() if line.strip()]
    items = [row for row in items if row['id'].startswith(args.wg + '_') and row['status'] != 'quarantine']
    for item in items:
        item['wg'] = args.wg
        if not item.get('candidate_query'):
            raise ValueError('admitted task has no query')
    # Only previously owned, budgeted archival containers may be started. Do
    # not adopt an active container or change its resource limits/mounts.
    name = f'kdd-db-frozen-v1-{args.wg.lower()}'
    info = json.loads(subprocess.check_output(['docker','inspect',name]))[0]
    if info['State']['Running']:
        raise ValueError('expected idle owned container; refusing to adopt active run')
    labels = info['Config'].get('Labels') or {}
    manifest = json.loads((HELPERS / '_frozen_ttl_v1' / args.wg.lower() / 'import_manifest.json').read_text())
    if labels.get('spectra.frozen.owner') != 'contract_repair_v1' or labels.get('spectra.frozen.run_uuid') != manifest['run_uuid']:
        raise ValueError('container ownership mismatch')
    if info['HostConfig']['Memory'] != 2*1024**3 or info['HostConfig']['NanoCpus'] != 10**9:
        raise ValueError('container resource budget mismatch')
    logging.getLogger('neo4j.notifications').setLevel(logging.ERROR)
    subprocess.run(['docker','start',name],check=True,stdout=subprocess.DEVNULL)
    try:
        from neo4j import GraphDatabase
        for _ in range(60):
            try:
                with GraphDatabase.driver(f'bolt://127.0.0.1:{guard.PORTS[args.wg]}',auth=None,connection_timeout=2) as driver:
                    driver.verify_connectivity()
                break
            except Exception:
                time.sleep(1)
        else:
            raise RuntimeError('owned archival database did not become ready')
        guard.owned_container_guard(args.wg)
        before = source.source_guard(args.wg)
        results = []
        for index, item in enumerate(items):
            receipt = execute(item, guard, native)
            results.append({'id': item['id'], 'status': receipt['status'],
                            'query_sha256': receipt['query_sha256'], 'rows': receipt['rows_retained']})
            if (index+1)%10 == 0 or receipt['status'] != 'OK':
                print(json.dumps({'wg':args.wg,'done':index+1,'n':len(items),**results[-1]}),flush=True)
        after = source.source_guard(args.wg)
        if sha(args.input) != input_hash:
            raise ValueError('execution input changed during the run')
        (BASE / ('execution_' + args.wg + '.json')).write_text(json.dumps(
            {'input_sha256':input_hash,'runner_sha256':sha(__file__),
             'protocol_sha256':sha(BASE/'execution_protocol.json'),
             'source_before':before,'source_after':after,
             'inventory_unchanged':before==after,'items':results,'model_calls':0,
             'expert_validation':False},indent=2)+'\n')
        if before != after:
            raise ValueError('archival inventory changed')
    finally:
        subprocess.run(['docker','stop','--time','20',name],check=True,stdout=subprocess.DEVNULL)


if __name__ == '__main__':
    main()
