"""Assemble a full plenary FTS index from locally verified reconstruction caches."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import sqlite3
import sys
import time

import export_retrieval_artifact as frontier


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bundle', type=Path, required=True)
    ap.add_argument('--text-cache', type=Path, required=True)
    ap.add_argument('--out-index', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    started = time.monotonic()
    schema, receipt = frontier.verify_bundle(args.bundle)
    if schema['kind'] != 'plenary':
        raise ValueError('Expected a plenary frontier')
    partial = args.out_index.with_suffix('.partial')
    if args.out_index.exists() or partial.exists():
        raise ValueError('Output already exists')
    groups = iter((k, list(v)) for k, v in itertools.groupby(
        frontier.rows(args.bundle, 'chunks'), key=lambda row: row['file_id']))
    current = next(groups, None)
    files, chunks, cache_records, seen = 0, 0, [], set()
    con = frontier.prepare_output(partial, schema)
    try:
        for record in frontier.rows(args.bundle, 'files'):
            file_id = record['id']
            if file_id in seen:
                raise ValueError('Repeated original file identity')
            seen.add(file_id)
            if current and current[0] < file_id:
                raise ValueError('Chunk groups do not match original file ordering')
            expected = current[1] if current and current[0] == file_id else []
            if expected:
                current = next(groups, None)
            cache = args.text_cache / f"{file_id}_{record['sha256']}.jsonl.gz"
            with gzip.open(cache, 'rt', encoding='utf-8') as stream:
                header = json.loads(next(stream))
                if (header['file_id'], header['archive_sha256']) != (file_id, record['sha256']):
                    raise ValueError('Cache source identity differs')
                cached_rows = (json.loads(line) for line in stream)
                for chunk, cached in itertools.zip_longest(expected, cached_rows):
                    if chunk is None or cached is None or chunk['id'] != cached['id']:
                        raise ValueError('Cache chunk identities or counts differ')
                    text = cached['text']
                    raw = text.encode('utf-8')
                    if (hashlib.sha256(raw).hexdigest(), len(raw), len(text)) != (
                            chunk['text_sha256'], chunk['text_bytes'], chunk['text_chars']):
                        raise ValueError('Cache text differs at chunk ' + str(chunk['id']))
                    frontier.insert(con, 'chunks', {**chunk, 'text': text})
                    chunks += 1
            cache_records.append({'file_id': file_id, 'cache_sha256': frontier.digest(cache),
                                  'producer_modules_sha256': header['original_modules_sha256'],
                                  'chunks': len(expected)})
            files += 1
            if files % 1000 == 0:
                print(json.dumps({'files': files, 'chunks': chunks}), flush=True)
        if current or files != receipt['rows']['files'] or chunks != receipt['rows']['chunks']:
            raise ValueError('Complete frontier coverage differs')
        for table in schema['tables']:
            if table != 'chunks':
                for row in frontier.rows(args.bundle, table):
                    frontier.insert(con, table, row)
        frontier.finish(con, schema)
        con = None
        partial.replace(args.out_index)
    except Exception as error:
        if con:
            con.close()
            con = None
        partial.unlink(missing_ok=True)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps({'status': 'failed', 'files_verified': files,
                                          'chunks_verified': chunks, 'error': type(error).__name__,
                                          'detail': str(error), 'partial_removed': not partial.exists(),
                                          'seconds': time.monotonic() - started}, indent=2) + '\n')
        raise
    finally:
        if con:
            con.close()
    report = {'files': files, 'chunks': chunks, 'cache_records': cache_records,
              'sqlite_version': sqlite3.sqlite_version, 'python': sys.version,
              'frontier_receipt_sha256': frontier.digest(args.bundle / 'receipt.json'),
              'assembler_sha256': frontier.digest(Path(__file__)), 'output_bytes': args.out_index.stat().st_size,
              'seconds': time.monotonic() - started,
              'scope': 'Every frozen chunk digest checked before full FTS construction from local reconstruction caches. Raw acquisition and extraction are recorded in the cache producer receipts.'}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'cache_records'}))


if __name__ == '__main__':
    main()
