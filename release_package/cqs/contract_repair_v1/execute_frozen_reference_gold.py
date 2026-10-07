#!/usr/bin/env python3
"""Execute new formal reference tasks only against restored deposited graphs.

The fixed loopback ports refer to newly owned instances, never the live research
databases. Instance ownership/source manifests are checked before any query.
Query execution produces graph-relative gold, not domain expert validation.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import time

from execute_reference_gold import safe_query, valid_value as base_valid_value
from typed_json import matches

BASE = Path(__file__).resolve().parent
PORTS = {f'RAN{i}': 57686 + i for i in range(1, 6)}


def valid_value(value, field):
    if not base_valid_value(value, field):
        return False
    if field['type'] == 'json':
        return 'json_schema' in field and matches(value, field['json_schema'])
    return True


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_guard(wg):
    from neo4j import GraphDatabase, READ_ACCESS
    path = BASE / '_frozen_ttl_v1' / wg.lower() / 'import_manifest.json'
    manifest = json.loads(path.read_text())
    uri = f'bolt://127.0.0.1:{PORTS[wg]}'
    assert manifest['status'] == 'restored_inventory_match'
    assert manifest['working_group'] == wg
    assert manifest['source']['published_md5_verified'] is True
    assert manifest['target']['container'] == f'kdd-db-frozen-v1-{wg.lower()}'
    assert manifest['target']['bolt'] == uri and manifest['target']['loopback_only'] is True
    assert sha(manifest['source']['path']) == manifest['source']['sha256']
    with GraphDatabase.driver(uri, auth=None) as driver:
        with driver.session(default_access_mode=READ_ACCESS) as session:
            nodes = session.run('MATCH (n) RETURN count(n) AS count').single()['count']
            relationships = session.run('MATCH ()-[r]->() RETURN count(r) AS count').single()['count']
    assert nodes == manifest['published_inventory']['nodes']
    assert relationships == manifest['published_inventory']['relationships']
    return {'wg': wg, 'import_manifest_sha256': sha(path),
            'source': {k: manifest['source'][k] for k in ('sha256', 'md5', 'bytes', 'published_md5_verified')},
            'nodes': nodes, 'relationships': relationships,
            'shipped_loader_sha256': manifest['shipped_loader']['sha256'],
            'restoration_wrapper_sha256': manifest['wrapper']['sha256']}


def run_query(wg, query, *, row_cap=2000, timeout_s=30):
    from neo4j import GraphDatabase, READ_ACCESS
    started = utc()
    before = time.monotonic()
    rows = []
    try:
        query = safe_query(query)
        with GraphDatabase.driver(f'bolt://127.0.0.1:{PORTS[wg]}', auth=None) as driver:
            with driver.session(default_access_mode=READ_ACCESS) as session:
                with session.begin_transaction(timeout=timeout_s) as tx:
                    result = tx.run(query)
                    columns = list(result.keys())
                    truncated = False
                    for row in result:
                        if len(rows) == row_cap:
                            truncated = True
                            break
                        rows.append(row.data())
                    tx.rollback()
        status = 'ROW_CAP' if truncated else 'OK'
        error = None
    except Exception as exc:
        status, error, columns, truncated = 'ERROR', type(exc).__name__, [], False
        rows = []
    return {'status': status, 'error_class': error, 'rows': rows,
            'columns': columns, 'row_count_retained': len(rows), 'truncated': truncated,
            'started_utc': started, 'finished_utc': utc(),
            'elapsed_s': round(time.monotonic() - before, 4)}


def execute_tasks(taskset):
    records = []
    for item in taskset['items']:
        if not item.get('reference_query') or not item.get('task_question'):
            result = {'status': 'UNRESOLVED_DEFINITION', 'rows': [], 'columns': [],
                      'row_count_retained': 0, 'truncated': False}
            typed = False
        else:
            result = run_query(item['wg'], item['reference_query'])
            typed = (result['status'] == 'OK'
                     and all(field['name'] in result['columns'] for field in item['required_fields'])
                     and all(
                all(field['name'] in row and valid_value(row[field['name']], field)
                    for field in item['required_fields']) for row in result['rows']))
        records.append({'id': item['id'], 'variant_id': item.get('variant_id'), 'wg': item['wg'],
                        'reference_query_sha256': hashlib.sha256((item['reference_query'] or '').encode()).hexdigest(),
                        'required_types_match': typed, 'eligible': typed, 'execution': result})
        print(item['id'], result['status'], result['row_count_retained'], 'typed', typed, flush=True)
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('taskset', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Refusing to overwrite a previous execution')
    taskset = json.loads(args.taskset.read_text())
    rules = taskset['eligibility_rule']
    assert rules['reference_timeout_seconds'] == 30 and rules['reference_row_cap'] == 2000
    guards = [source_guard(wg) for wg in sorted({item['wg'] for item in taskset['items']})]
    payload = {'kind': 'reference execution over restored deposited TTL; not model output',
               'started_utc': utc(), 'taskset_sha256': sha(args.taskset),
               'runner_sha256': sha(__file__), 'read_query_guard_sha256': sha(BASE / 'execute_reference_gold.py'),
               'nested_type_guard_sha256': sha(BASE / 'typed_json.py'),
               'source_guards_before': guards, 'row_cap': 2000, 'timeout_seconds': 30,
               'domain_expert_validation': False, 'original_benchmark_modified': False,
               'restored_deposited_source': True,
               'same_count_external_property_mutations_detected': False,
               'items': execute_tasks(taskset)}
    payload['source_guards_after'] = [source_guard(wg) for wg in sorted({item['wg'] for item in taskset['items']})]
    assert payload['source_guards_before'] == payload['source_guards_after']
    payload['finished_utc'] = utc()
    with args.output.open('x') as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print('eligible', sum(item['eligible'] for item in payload['items']), 'of', len(payload['items']))
    print('output_sha256', sha(args.output))


if __name__ == '__main__':
    main()
