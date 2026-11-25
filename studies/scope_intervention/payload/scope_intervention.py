#!/usr/bin/env python3
"""Frozen-cohort scope literal intervention, using the released offline evaluator."""
from __future__ import annotations

import argparse
import ast
import collections
import difflib
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import resource
import shutil
import sqlite3
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / 'AGENTS.md').exists())
PACKAGE = ROOT / 'logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/release_preparation/vldb_release'
CODE = PACKAGE / 'code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark'
ITEM_FILES = ['benchmark/items_final/gate/core/chain_items_admitted.jsonl',
              'benchmark/items_final/gate/ran5/chain_items_admitted.jsonl']
SESSIONS = [('RAN2', 'A'), ('RAN2', 'E'), ('RAN5', 'C')]
EXPECTED = {('RAN2', 'A'): 100, ('RAN2', 'E'): 100, ('RAN5', 'C'): 98}
PATTERN = re.compile(r"\bscope\b(?P<tail>[^;]*?)\bIN\s*\(\s*(?P<literal>'wholedocument')", re.I)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def load_original_functions():
    source = (CODE / 'run_chain_eval.py').read_text()
    tree = ast.parse(source)
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'solve_text2sql')
    namespace = {'time': time}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(CODE / 'run_chain_eval.py'), 'exec'), namespace)
    spec = importlib.util.spec_from_file_location('released_score', CODE / 'score_chain_eval.py')
    scorer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scorer)
    return namespace['solve_text2sql'], scorer


def prepare():
    assert not (HERE / 'edit_manifest.json').exists(), 'Preserve the already frozen manifest'
    inputs = {p: sha(PACKAGE / p) for p in ITEM_FILES}
    inputs['classifier'] = sha(PACKAGE / 'responses/final/supplement_cycle/query_writers/miss_clusters_ten_runs.json')
    for name in ['run_chain_eval.py', 'score_chain_eval.py', 'summarize_repeated_run_misses.py', 'measure_relational_equivalence.py']:
        inputs['code/' + name] = sha(CODE / name)
    items = {x['id']: x for rel in ITEM_FILES for x in rows(PACKAGE / rel)}
    assert len(items) == 667
    cohort = []
    for wg, run in SESSIONS:
        rel = f'responses/chain_eval/text2sql/{wg}_text2sql_run{run}.jsonl'
        inputs[rel] = sha(PACKAGE / rel)
        selected = 0
        for record in rows(PACKAGE / rel):
            item = items[record['id']]
            query = record['attempts'][0]['sql']
            compact = query.lower().replace('_', '').replace('-', '').replace(' ', '')
            if record.get('rows') != [] or 'scope' not in compact or 'wholetarget' in compact:
                continue
            assert item['gold']
            assert record['questionSha256'] == hashlib.sha256(item['question'].encode()).hexdigest()
            matches = list(PATTERN.finditer(query))
            assert len(matches) == 1, (record['id'], len(matches))
            start, end = matches[0].span('literal')
            fixed = query[:start] + "'wholetarget'" + query[end:]
            assert query.count('scope') == 1
            identifier = f"{wg}|run{run}|{item['id']}"
            cohort.append({'case': identifier, 'wg': wg, 'session': 'run' + run, 'family': item['family'],
                           'id': item['id'], 'questionSha256': record['questionSha256'], 'fields': item['fields'],
                           'gold': item['gold'], 'originalSql': query, 'fixedSql': fixed,
                           'edit': {'start': start, 'end': end, 'before': "'wholedocument'", 'after': "'wholetarget'"},
                           'diff': ''.join(difflib.unified_diff([query + '\n'], [fixed + '\n'], fromfile='original.sql', tofile='fixed.sql')),
                           'selectionHash': hashlib.sha256(identifier.encode()).hexdigest()})
            selected += 1
        assert selected == EXPECTED[(wg, run)], (wg, run, selected)
    assert len(cohort) == 298
    strata = collections.defaultdict(list)
    for entry in cohort:
        strata[(entry['wg'], entry['session'], entry['family'])].append(entry)
    pilot = sorted(min(values, key=lambda e: e['selectionHash'])['case'] for values in strata.values())
    db_dir = HERE / 'sqlite'
    db_dir.mkdir(exist_ok=True)
    checksums = dict(line.split()[::-1] for line in (PACKAGE / 'sqlite/SHA256SUMS.txt').read_text().splitlines())
    databases = {}
    for wg in sorted({wg for wg, _ in SESSIONS}):
        source = PACKAGE / 'sqlite' / f'{wg}.sqlite.gz'
        target = db_dir / f'{wg}.sqlite'
        assert sha(source) == checksums[source.name]
        if not target.exists():
            with gzip.open(source, 'rb') as src, target.open('wb') as out:
                shutil.copyfileobj(src, out)
        assert sha(target) == checksums[target.name]
        target.chmod(0o444)
        databases[wg] = {'source': str(source.relative_to(ROOT)), 'compressedSha256': sha(source),
                         'path': str(target.relative_to(HERE)), 'sha256': sha(target), 'bytes': target.stat().st_size}
    manifest = {'protocolSha256': sha(HERE / 'protocol.md'), 'scriptSha256': sha(__file__),
                'inputSha256': inputs, 'databases': databases, 'pilotCases': pilot, 'cases': cohort,
                'cohortCounts': {'|'.join(key): len(value) for key, value in sorted(strata.items())}}
    write_json(HERE / 'edit_manifest.json', manifest)
    write_json(HERE / 'pre_execution_pin.json', {'editManifestSha256': sha(HERE / 'edit_manifest.json'),
                'protocolSha256': sha(HERE / 'protocol.md'), 'scriptSha256': sha(__file__),
                'python': sys.version, 'sqlite': sqlite3.sqlite_version,
                'createdUtc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'outcomeExecutionsBeforePin': 0})
    print(json.dumps({'cases': len(cohort), 'pilot': len(pilot), 'strata': manifest['cohortCounts'],
                      'manifestSha256': sha(HERE / 'edit_manifest.json')}, ensure_ascii=False), flush=True)


def run(stage):
    manifest = json.loads((HERE / 'edit_manifest.json').read_text())
    pin = json.loads((HERE / 'pre_execution_pin.json').read_text())
    assert sha(HERE / 'edit_manifest.json') == pin['editManifestSha256']
    assert sha(HERE / 'protocol.md') == pin['protocolSha256']
    assert sys.version.startswith('3.10.12') and sqlite3.sqlite_version == '3.37.2'
    for name in ['run_chain_eval.py', 'score_chain_eval.py']:
        assert sha(CODE / name) == manifest['inputSha256']['code/' + name]
    solve, scorer = load_original_functions()
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024 ** 3, 2 * 1024 ** 3))
    connections = {}
    for wg, meta in manifest['databases'].items():
        path = HERE / meta['path']
        assert sha(path) == meta['sha256']
        db = sqlite3.connect(f'file:{path}?mode=ro&immutable=1', uri=True)
        db.execute('PRAGMA query_only=ON')
        db.execute('PRAGMA temp_store=FILE')
        db.execute('PRAGMA cache_size=-32768')
        connections[wg] = db
    output = HERE / 'paired_results.jsonl'
    existing = {x['case']: x for x in rows(output)} if output.exists() else {}
    cases = [e for e in manifest['cases'] if stage == 'full' or e['case'] in manifest['pilotCases']]
    started = time.monotonic()
    with output.open('a') as handle:
        for entry in cases:
            if entry['case'] in existing:
                continue
            if time.monotonic() - started > 3600:
                print('CHECKPOINT: batch wall clock reached 60 minutes', flush=True)
                break
            result = {k: entry[k] for k in ['case', 'wg', 'session', 'family', 'id', 'questionSha256', 'gold']}
            result['goldSet'] = sorted([list(row) for row in {scorer.key(row) for row in entry['gold']}])
            for arm, field in [('original', 'originalSql'), ('fixed', 'fixedSql')]:
                tick = time.monotonic()
                value = solve(entry, connections[entry['wg']], [entry[field]])
                attempt = value['attempts'][0]
                given = None if value['rows'] is None else {scorer.key(row) for row in value['rows']}
                wanted = {scorer.key(row) for row in entry['gold']}
                error = attempt.get('error')
                result[arm] = {'seconds': time.monotonic() - tick, 'rows': value['rows'],
                    'set': None if given is None else sorted([list(row) for row in given]),
                    'rowCountBefore2000Limit': attempt.get('rowCount'), 'error': error,
                    'status': 'timeout' if error == 'interrupted' else 'error' if error else 'returned',
                    'score': scorer.score(entry['gold'], value['rows']),
                    'goldOnly': None if given is None else len(wanted - given),
                    'responseOnly': None if given is None else len(given - wanted),
                    'sqlSha256': hashlib.sha256(entry[field].encode()).hexdigest()}
            handle.write(json.dumps(result, ensure_ascii=False) + '\n')
            handle.flush()
            print(json.dumps({'case': entry['case'], 'originalExact': result['original']['score']['exact'],
                  'fixedExact': result['fixed']['score']['exact'], 'fixedStatus': result['fixed']['status'],
                  'seconds': round(result['original']['seconds'] + result['fixed']['seconds'], 3)}, ensure_ascii=False), flush=True)
    for db in connections.values():
        db.close()
    checks = {wg: {'sha256After': sha(HERE / meta['path']), 'matches': sha(HERE / meta['path']) == meta['sha256']}
              for wg, meta in manifest['databases'].items()}
    write_json(HERE / f'{stage}_execution_receipt.json', {'stage': stage, 'python': sys.version,
               'sqlite': sqlite3.sqlite_version, 'platform': platform.platform(), 'loadAverage': os.getloadavg(),
               'elapsedSecondsThisBatch': time.monotonic() - started, 'rlimitAsBytes': 2 * 1024 ** 3,
               'maxRssKiB': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               'databaseAfter': checks, 'editManifestSha256': sha(HERE / 'edit_manifest.json'),
               'scriptSha256': sha(__file__), 'resultSha256': sha(output)})
    summarize()


def summarize():
    records = rows(HERE / 'paired_results.jsonl')
    manifest = json.loads((HERE / 'edit_manifest.json').read_text())
    def count(entries):
        return {'n': len(entries), **{arm: {'exact': sum(e[arm]['score']['exact'] for e in entries),
                 'status': dict(collections.Counter(e[arm]['status'] for e in entries)),
                 'seconds': sum(e[arm]['seconds'] for e in entries)} for arm in ['original', 'fixed']},
                 'recovered': sum(not e['original']['score']['exact'] and e['fixed']['score']['exact'] for e in entries)}
    groups = {}
    for axes in [('wg',), ('session',), ('family',), ('wg', 'session'), ('wg', 'session', 'family')]:
        buckets = collections.defaultdict(list)
        for entry in records:
            buckets['|'.join(entry[a] for a in axes)].append(entry)
        groups['+'.join(axes)] = {k: count(v) for k, v in sorted(buckets.items())}
    report = {'planned': len(manifest['cases']), 'executed': len(records), 'overall': count(records),
              'groups': groups, 'residual': [{k: e[k] for k in ['case', 'family', 'fixed']} for e in records if not e['fixed']['score']['exact']],
              'manifestSha256': sha(HERE / 'edit_manifest.json'), 'resultsSha256': sha(HERE / 'paired_results.jsonl')}
    write_json(HERE / 'summary.json', report)
    print(json.dumps(report['overall']), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['prepare', 'pilot', 'full', 'summarize'])
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare()
    elif args.command == 'summarize':
        summarize()
    else:
        run(args.command)
