#!/usr/bin/env python3
"""Audit every package checksum manifest, including decompressed SQLite pins."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re


def digest(path, compressed=False):
    h = hashlib.sha256()
    with (gzip.open if compressed else open)(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def audit(root):
    cache = {}
    records = []
    for manifest in sorted(root.rglob('*')):
        if manifest.relative_to(root).parts[0] in {'work', '.git'}:
            continue
        if not manifest.is_file() or manifest.name not in {'SHA256SUMS', 'SHA256SUMS.txt'}:
            continue
        entries = []
        for number, line in enumerate(manifest.read_text().splitlines(), 1):
            match = re.fullmatch(r'([0-9a-f]{64})[ \t]+\*?(.+)', line)
            if not match:
                entries.append({'line': number, 'status': 'malformed'})
                continue
            expected, name = match.groups()
            target = (manifest.parent / name).resolve()
            record = {'line': number, 'name': name, 'expected': expected}
            if not target.is_relative_to(manifest.parent.resolve()):
                record['status'] = 'escape'
            elif target.is_file():
                if target not in cache:
                    cache[target] = digest(target)
                record.update(actual=cache[target], status='match' if cache[target] == expected else 'mismatch')
            elif manifest.parent == root / 'sqlite' and target.suffix == '.sqlite' and target.with_suffix('.sqlite.gz').is_file():
                actual = digest(target.with_suffix('.sqlite.gz'), compressed=True)
                record.update(actual=actual, status='decompressed_match' if actual == expected else 'decompressed_mismatch')
            else:
                record['status'] = 'missing'
            entries.append(record)
        records.append({'path': str(manifest.relative_to(root)), 'entries': entries})
    failures = [{'manifest': r['path'], **e} for r in records for e in r['entries'] if e['status'] not in {'match', 'decompressed_match'}]
    duplicates = [str(m.parent.relative_to(root)) for m in root.rglob('SHA256SUMS') if m.relative_to(root).parts[0] not in {'work', '.git'} and m.with_name('SHA256SUMS.txt').exists()]
    return {'excluded_top_level_scratch_paths': ['work', '.git'], 'manifest_count': len(records), 'verified_entries': sum(len(r['entries']) for r in records), 'failures': failures, 'duplicate_manifest_directories': duplicates, 'manifests': records, 'pass': not failures and not duplicates}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.release.resolve())
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'manifests'}))
    raise SystemExit(0 if report['pass'] else 1)
