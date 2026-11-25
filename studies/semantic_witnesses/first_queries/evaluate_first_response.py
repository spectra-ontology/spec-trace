#!/usr/bin/env python3
"""Execute the frozen pilot's first SQL response; retain all outcomes."""
import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import time


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def norm(rows):
    return sorted(set(tuple(str(value) for value in row) for row in rows))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--frozen', type=Path, required=True)
    ap.add_argument('--responses', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--release', type=Path, help='Portable public checkout; original source hashes still apply')
    ap.add_argument('--database-directory', type=Path, help='Scratch directory for decompressed databases')
    a = ap.parse_args()
    assert not a.output.exists(), 'Preserve completed attempts with a new output path'
    freeze = json.loads((a.frozen / 'freeze.json').read_text())
    for name, expected in freeze['files'].items():
        assert sha(a.frozen / name) == expected, name
    study = json.loads((a.frozen / 'selection_and_gold.json').read_text())
    responses = json.loads(a.responses.read_text())
    responses = responses['responses'] if isinstance(responses, dict) else responses
    by_id = {row['id']: row for row in responses}
    assert len(by_id) == len(responses) == len(study['items'])
    assert set(by_id) == {row['id'] for row in study['items']}
    assert sqlite3.sqlite_version == '3.37.2', sqlite3.sqlite_version
    dbs = {row['wg']: row for row in study['inputs']}
    if a.release:
        assert a.database_directory, '--database-directory is required with --release'
        a.database_directory.mkdir(parents=True, exist_ok=True)
        for wg, source in dbs.items():
            original_name = Path(source['source']).name
            current_source = a.release / 'sqlite' / original_name
            assert sha(current_source) == source['source_sha256'], wg
            current_database = current_source
            if current_source.suffix == '.gz':
                current_database = a.database_directory / (wg + '.sqlite')
                if not current_database.exists():
                    with gzip.open(current_source, 'rb') as src, current_database.open('xb') as dst:
                        shutil.copyfileobj(src, dst)
            source['source'] = str(current_source)
            source['database'] = str(current_database)
    for source in dbs.values():
        assert sha(Path(source['database'])) == source['database_sha256']
        assert sha(Path(source['source'])) == source['source_sha256']
    results = []
    for item in study['items']:
        sql = by_id[item['id']]['sql']
        conn = sqlite3.connect('file:' + str(Path(dbs[item['wg']]['database']).resolve()) + '?mode=ro', uri=True)
        conn.execute('PRAGMA query_only=ON')
        start = time.monotonic()
        conn.set_progress_handler(lambda: time.monotonic() - start > 60, 10000)
        row = {'id': item['id'], 'wg': item['wg'], 'family': item['family'], 'sql': sql, 'exact': False}
        try:
            cursor = conn.execute(sql)
            assert cursor.description is not None, 'A result set is required'
            actual = norm(cursor.fetchall())
            row.update(status='returned', actual=actual, exact=actual == norm(item['gold']),
                       missing=sorted(set(norm(item['gold'])) - set(actual)),
                       extra=sorted(set(actual) - set(norm(item['gold']))))
        except Exception as error:
            row.update(status='timeout' if time.monotonic() - start >= 60 else 'error', error=str(error))
        row['seconds'] = time.monotonic() - start
        conn.close()
        results.append(row)
    for source in dbs.values():
        assert sha(Path(source['database'])) == source['database_sha256']
        assert sha(Path(source['source'])) == source['source_sha256']
    groups = {}
    for key in ['family', 'wg']:
        grouped = collections.defaultdict(list)
        for row in results:
            grouped[row[key]].append(row)
        groups[key] = {name: {'n': len(rows), 'exact': sum(r['exact'] for r in rows),
                             'statuses': dict(collections.Counter(r['status'] for r in rows))}
                       for name, rows in sorted(grouped.items())}
    receipt = {'runtime': {'python_sqlite': sqlite3.sqlite_version, 'cap_seconds': 60,
                          'interface': 'schema and complete relevant value domains; one first response; no execution feedback'},
               'freeze_sha256': sha(a.frozen / 'freeze.json'), 'response_sha256': sha(a.responses),
               'evaluator_sha256': sha(Path(__file__)), 'source_inputs_unchanged': True,
               'n': len(results), 'exact': sum(r['exact'] for r in results), 'groups': groups, 'results': results}
    a.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: receipt[k] for k in ['n', 'exact', 'groups', 'source_inputs_unchanged']}))


if __name__ == '__main__':
    main()
