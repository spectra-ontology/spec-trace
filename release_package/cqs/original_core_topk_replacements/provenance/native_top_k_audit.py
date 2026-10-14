#!/usr/bin/env python3
"""Replay capped and uncapped top-k pools only in idle owned archival instances."""
from collections import Counter
import hashlib
import importlib.util
import json
import logging
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[7]
OUT = Path(__file__).resolve().parent
COMMIT = '2b6f57e9b0cac90252b9fb4c8847bd67315a3222'
CORE = ROOT / 'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/external_download' / COMMIT / 'checkout' / ('spec-trace-' + COMMIT) / 'release_package/cqs/original_core_repair'
RUNNER = ROOT / 'logs/pending-tasks/spectracq-core-contract-2026-10-13/execute_candidates.py'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def text_sha(value):
    return hashlib.sha256(value.encode()).hexdigest()

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def inspection(name):
    info = json.loads(subprocess.check_output(['docker', 'inspect', name]))[0]
    return info, {'name': info['Name'], 'state': info['State'], 'labels': info['Config'].get('Labels'),
                  'memory': info['HostConfig']['Memory'], 'nano_cpus': info['HostConfig']['NanoCpus'],
                  'port_bindings': info['HostConfig']['PortBindings']}

def main():
    start = time.monotonic()
    execute = load(RUNNER, 'independent_native_capture')
    guard, source, native = execute.helpers()
    # Change the imported runner's output destination only in this process.
    # The historical producer files and outputs remain byte-identical.
    execute.BASE = OUT / 'native_top_k_runs'
    execute.BASE.mkdir(exist_ok=True)
    sys.path.insert(0, str(CORE))
    import scorer
    import original_scorer
    import verify_release
    tasks = {r['id']: (n, r) for n, text in enumerate((CORE / 'tasks.jsonl').read_text().splitlines(), 1)
             for r in [scorer.get_kernel().loads_exact(text)]}
    wanted = [r for _, r in tasks.values() if r['cardinality_policy']['mode'] == 'top_k'
              and r['collection']['kind'] != 'top_k_boundary_ties']
    gold = {}
    for text in (CORE / 'reference_gold.jsonl').open():
        row = scorer.get_kernel().loads_exact(text)
        if row['id'] in {r['id'] for r in wanted}: gold[row['id']] = row
    report = {'kind': 'New guarded read-only capped/uncapped pool execution; original tasks unmodified',
              'commit': COMMIT, 'script_sha256': sha(Path(__file__)), 'capture_runner_sha256': sha(RUNNER),
              'helper_sha256': {name: sha(execute.HELPERS / name) for name in
                 ['replay_generated_read_queries.py', 'execute_frozen_reference_gold.py', 'load_frozen_ttl_neo4j.py', 'execute_reference_gold.py', 'typed_json.py']},
              'native_kernel_sha256': sha(Path(native.__file__)), 'commands': [], 'groups': [], 'items': [],
              'source_guard_limit': 'Inventory counts and pinned TTL hashes; same-count external property mutation is not ruled out',
              'model_calls': 0, 'domain_expert_validation': False}
    logging.getLogger('neo4j.notifications').setLevel(logging.ERROR)
    for wg in sorted({t['id'].split('_')[0] for t in wanted}):
        name = 'kdd-db-frozen-v1-' + wg.lower()
        info, observation = inspection(name)
        manifest_path = execute.HELPERS / '_frozen_ttl_v1' / wg.lower() / 'import_manifest.json'
        manifest = json.loads(manifest_path.read_text())
        if info['State']['Running']:
            raise ValueError('refusing to adopt or stop an active container: ' + name)
        labels = info['Config'].get('Labels') or {}
        if (labels.get('spectra.frozen.owner') != 'contract_repair_v1'
                or labels.get('spectra.frozen.run_uuid') != manifest['run_uuid']
                or labels.get('spectra.frozen.source_sha256') != manifest['source']['sha256']
                or info['HostConfig']['Memory'] != 2 * 1024**3
                or info['HostConfig']['NanoCpus'] != 10**9
                or info['HostConfig']['PortBindings'] != {'7687/tcp': [{'HostIp': '127.0.0.1', 'HostPort': str(guard.PORTS[wg])}]}):
            raise ValueError('idle container ownership, source or resource budget differs')
        group = {'wg': wg, 'container_before': observation, 'manifest_sha256': sha(manifest_path)}
        report['commands'].append(['docker', 'start', name])
        subprocess.run(['docker', 'start', name], check=True, stdout=subprocess.DEVNULL)
        try:
            from neo4j import GraphDatabase
            for _ in range(60):
                try:
                    with GraphDatabase.driver(f'bolt://127.0.0.1:{guard.PORTS[wg]}', auth=None, connection_timeout=2) as driver:
                        driver.verify_connectivity()
                    break
                except Exception:
                    time.sleep(1)
            else: raise RuntimeError('owned archival database did not become ready')
            guard.owned_container_guard(wg)
            group['source_before'] = source.source_guard(wg)
            if group['source_before'] != json.loads((CORE / 'manifest.json').read_text())['graph_sources'][wg]:
                raise ValueError('fresh source differs from the public repair source')
            for task in [t for t in wanted if t['id'].startswith(wg + '_')]:
                query = task['reference_query']
                match = re.search(r'\s+LIMIT\s+(\d+)\s*$', query, re.I)
                if not match or int(match.group(1)) != task['cardinality_policy']['value']:
                    raise ValueError('expected one terminal explicit top-k LIMIT')
                uncapped = query[:match.start()]
                runs = {}
                for label, q in [('capped', query), ('uncapped', uncapped)]:
                    item = {'id': task['id'] + '__' + label, 'wg': wg, 'candidate_query': q}
                    receipt = execute.execute(item, guard, native)
                    if receipt['status'] != 'OK': raise ValueError('native pool replay incomplete: ' + task['id'])
                    values = [scorer.get_kernel().loads_exact(t) for t in (execute.BASE / receipt['rows_file']).read_text().splitlines()]
                    rows = [dict(zip(receipt['columns'], row)) for row in values]
                    records = verify_release.project(rows, task['required_fields'], receipt['columns'])
                    runs[label] = {'receipt': receipt, 'native_rows': rows, 'projected_rows': records}
                original = gold[task['id']]
                replayed_score = original_scorer.score(task, original['records'], runs['capped']['projected_rows'], order_groups=original['order_groups'])
                if not replayed_score['exact']: raise ValueError('fresh capped answers disagree with public gold')
                pool = runs['uncapped']['native_rows']
                if task['collection']['kind'] == 'native_ordered_ties':
                    keys = task['collection']['source_order_keys']
                    if len(keys) != 1: raise ValueError('independent cutoff audit expects one requested ranking key')
                    ranking_column = keys[0]['source_column']
                else:
                    ranking_column = 'tdocCount'
                k = task['cardinality_policy']['value']
                cutoff = pool[k - 1][ranking_column] if len(pool) >= k else None
                above = [i for i, r in enumerate(pool) if cutoff is not None and r[ranking_column] > cutoff]
                tied = [i for i, r in enumerate(pool) if cutoff is not None and r[ranking_column] == cutoff]
                excluded_tied = [i for i in tied if i >= k]
                entry = {'id': task['id'], 'tasks_line': tasks[task['id']][0], 'original_query_sha256': text_sha(query),
                         'uncapped_query_sha256': text_sha(uncapped), 'terminal_limit_removed_only': True,
                         'capped_receipt_file': str((execute.BASE / (task['id'] + '__capped') / (text_sha(query) + '.json')).relative_to(OUT)),
                         'uncapped_receipt_file': str((execute.BASE / (task['id'] + '__uncapped') / (text_sha(uncapped) + '.json')).relative_to(OUT)),
                         'capped_n': len(runs['capped']['projected_rows']), 'full_pool_n': len(pool),
                         'fresh_capped_matches_public_gold': replayed_score, 'ranking_column': ranking_column,
                         'cutoff_value': cutoff, 'above_cutoff_n': len(above), 'cutoff_tie_n': len(tied),
                         'excluded_cutoff_tie_n': len(excluded_tied), 'cutoff_tie_native_rows': [pool[i] for i in tied]}
                if excluded_tied:
                    pred = list(runs['capped']['projected_rows'])
                    pred[-1] = runs['uncapped']['projected_rows'][excluded_tied[0]]
                    entry['same_frequency_boundary_alternative'] = {'records': pred,
                        'replaced': runs['capped']['projected_rows'][-1],
                        'replacement_native_row': pool[excluded_tied[0]],
                        'score_under_published_contract': original_scorer.score(task, original['records'], pred, order_groups=original['order_groups'])}
                report['items'].append(entry)
                print(json.dumps({k: entry[k] for k in ['id', 'full_pool_n', 'cutoff_value', 'excluded_cutoff_tie_n']}), flush=True)
            group['source_after'] = source.source_guard(wg)
            group['inventory_and_source_pins_unchanged'] = group['source_before'] == group['source_after']
            if not group['inventory_and_source_pins_unchanged']: raise ValueError('archival source inventory changed')
        finally:
            report['commands'].append(['docker', 'stop', '--time', '20', name])
            subprocess.run(['docker', 'stop', '--time', '20', name], check=True, stdout=subprocess.DEVNULL)
            _, group['container_after'] = inspection(name)
            report['groups'].append(group)
            (OUT / 'native_top_k_report.json').write_text(scorer.get_kernel().json_exact(report) + '\n')
    report['elapsed_seconds'] = time.monotonic() - start
    report['actual_excluded_cutoff_tie_tasks_n'] = sum(i['excluded_cutoff_tie_n'] > 0 for i in report['items'])
    (OUT / 'native_top_k_report.json').write_text(scorer.get_kernel().json_exact(report) + '\n')

if __name__ == '__main__':
    main()
