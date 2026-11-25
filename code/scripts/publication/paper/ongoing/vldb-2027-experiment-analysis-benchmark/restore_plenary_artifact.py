#!/usr/bin/env python3
"""Reconstruct pinned plenary chunks with the original extraction functions.

The frontier supplies original identities, metadata and text digests. Source
archives come from a local source tree or their official URLs. Verification
checks every selected chunk; index construction requires the complete frontier.
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import datetime
import gzip
import hashlib
import importlib
import importlib.metadata
import itertools
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import time
import urllib.parse
import urllib.request


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read_rows(bundle, table):
    with gzip.open(bundle / (table + '.jsonl.gz'), 'rt', encoding='utf-8') as f:
        for line in f:
            yield json.loads(line)


def grouped(iterator, key):
    return iter((k, list(v)) for k, v in itertools.groupby(iterator, key=key))


def take_group(current, iterator, key):
    while current is not None and current[0] < key:
        current = next(iterator, None)
    if current is not None and current[0] == key:
        return current[1], next(iterator, None)
    return [], current


def safe_path(root, relative):
    target = (root / relative).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError('Source path escapes the specified tree')
    return target


def acquire(record, args):
    if args.source_root:
        for relative in json.loads(record['paths']):
            p = safe_path(args.source_root, relative)
            if p.is_file():
                if p.stat().st_size != record['bytes'] or sha(p) != record['sha256']:
                    raise ValueError('Local archive differs from pinned bytes')
                return p, 'local_pinned_archive'
    folder = args.cache / record['sha256']
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / 'source.archive'
    if target.is_file():
        if target.stat().st_size == record['bytes'] and sha(target) == record['sha256']:
            return target, 'cached_pinned_archive'
        raise ValueError('Cached archive differs from pinned bytes')
    if args.offline:
        raise ValueError('Pinned archive is absent from offline inputs')
    errors = []
    for url in record.get('official_urls', []):
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != 'https' or parsed.hostname not in ('www.3gpp.org', 'ftp.3gpp.org'):
            raise ValueError('Manifest URL is outside the official HTTPS source')
        partial = target.with_suffix('.partial')
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'SPECTRA-source-check/1.0'})
            with urllib.request.urlopen(request, timeout=120) as source, partial.open('wb') as sink:
                total = 0
                for block in iter(lambda: source.read(1 << 20), b''):
                    total += len(block)
                    if total > record['bytes']:
                        raise ValueError('Downloaded archive exceeds pinned size')
                    sink.write(block)
            if partial.stat().st_size != record['bytes'] or sha(partial) != record['sha256']:
                raise ValueError('Downloaded archive differs from pinned bytes')
            partial.replace(target)
            return target, url
        except (OSError, ValueError) as error:
            partial.unlink(missing_ok=True)
            errors.append(type(error).__name__ + ': ' + str(error)[:120])
    raise ValueError('Official archive unavailable: ' + '; '.join(errors))


@contextlib.contextmanager
def converter_environment(clock):
    if not clock:
        yield
        return
    values = {'LD_PRELOAD': str(clock['library']) +
              ((':' + os.environ['LD_PRELOAD']) if os.environ.get('LD_PRELOAD') else ''),
              'FAKETIME': '@' + clock['date'] + ' 12:00:00',
              'FAKETIME_DONT_FAKE_MONOTONIC': '1', 'NO_FAKE_STAT': '1', 'TZ': 'UTC'}
    old = {key: os.environ.get(key) for key in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for key, value in old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def extract(original, archive, record, scratch, clock=None):
    work = Path(tempfile.mkdtemp(prefix='plenary-source-', dir=scratch))
    reader = original.Extractor(work, scratch / 'libreoffice-profile')
    try:
        names = json.loads(record['names'])
        opener = reader.visit_archive(archive, [names[0]], record['bytes'])
        reader.native()
        with converter_environment(clock):
            reader.convert()
        reader.read()
        by_chain = collections.defaultdict(list)
        for member in reader.members:
            by_chain[' / '.join(member['chain'][1:])].append(member)
        return opener, by_chain
    finally:
        shutil.rmtree(work)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bundle', type=Path, required=True)
    ap.add_argument('--cache', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    ap.add_argument('--source-root', type=Path)
    ap.add_argument('--offline', action='store_true')
    ap.add_argument('--file-id', type=int, action='append',
                    help='Verify selected original file IDs; omit for the complete frontier')
    ap.add_argument('--shard-count', type=int, default=1)
    ap.add_argument('--shard-index', type=int, default=0)
    ap.add_argument('--out-index', type=Path,
                    help='Construct a complete logical index; incompatible with --file-id')
    ap.add_argument('--text-cache', type=Path,
                    help='Save verified text locally for subsequent index assembly; source text stays outside the release')
    ap.add_argument('--converter-date', help='Recorded conversion date for automatic presentation fields (ISO date)')
    ap.add_argument('--converter-clock-library', type=Path,
                    help='Locally built libfaketimeMT.so.1; scoped to converter subprocesses')
    args = ap.parse_args()
    if args.shard_count < 1 or not 0 <= args.shard_index < args.shard_count:
        ap.error('Require 0 <= shard-index < positive shard-count')
    if args.out_index and (args.file_id or args.shard_count != 1):
        ap.error('A complete index requires every original file')
    if bool(args.converter_date) != bool(args.converter_clock_library):
        ap.error('Converter date and clock library must be supplied together')
    clock = None
    if args.converter_date:
        date = datetime.date.fromisoformat(args.converter_date).isoformat()
        library = args.converter_clock_library.resolve(strict=True)
        clock = {'date': date, 'library': library, 'library_sha256': sha(library),
                 'scope': 'Converter subprocess calendar only; parent clocks and source text are preserved'}
    args.cache.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    import export_retrieval_artifact as frontier
    import build_plenary_index as original
    schema, receipt = frontier.verify_bundle(args.bundle)
    if schema['kind'] != 'plenary':
        raise ValueError('Expected a plenary frontier')
    source_modules = [Path(__file__), Path(frontier.__file__), Path(original.__file__),
                      Path(importlib.import_module('raw_source_text').__file__),
                      Path(importlib.import_module('word97_text').__file__)]
    source_hashes = {p.name: sha(p) for p in source_modules}
    selected = set(args.file_id or [])
    known = set()
    members_iter = grouped(read_rows(args.bundle, 'members'), lambda r: r['file_id'])
    chunks_iter = grouped(read_rows(args.bundle, 'chunks'), lambda r: r['file_id'])
    members_current, chunks_current = next(members_iter, None), next(chunks_iter, None)
    results, failures, tested_chunks = [], [], 0
    con = None
    started = time.monotonic()
    if args.out_index:
        partial = args.out_index.with_suffix(args.out_index.suffix + '.partial')
        if args.out_index.exists() or partial.exists():
            raise ValueError('Index output already exists')
        con = frontier.prepare_output(partial, schema)
    try:
        with tempfile.TemporaryDirectory(prefix='plenary-extraction-') as temporary:
            scratch = Path(temporary)
            for record in read_rows(args.bundle, 'files'):
                file_id = record['id']
                known.add(file_id)
                members, members_current = take_group(members_current, members_iter, file_id)
                chunks, chunks_current = take_group(chunks_current, chunks_iter, file_id)
                if selected and file_id not in selected:
                    continue
                if file_id % args.shard_count != args.shard_index:
                    continue
                if original.available_gib() < 8:
                    raise RuntimeError('Available RAM is below the repository 8GiB execution floor')
                step = time.monotonic()
                cached = None
                cache_partial = None
                try:
                    archive, acquired = acquire(record, args)
                    opener, extracted = extract(original, archive, record, scratch, clock)
                    by_member = {m['id']: m for m in members}
                    current_members = [m for values in extracted.values() for m in values]
                    original_chains = {m['chain'] for m in members}
                    original_chunk_members = {c['member_id'] for c in chunks}
                    excluded_new_text = [
                        {'chain': chain, 'outcome': value['outcome'], 'chars': value['chars']}
                        for chain, values in extracted.items() for value in values
                        if value['outcome'] == 'extracted' and
                        not any(m['chain'] == chain and m['id'] in original_chunk_members for m in members)]
                    outcome_audit = {
                        'original_file_outcome': record['outcome'],
                        'original_member_outcomes': dict(collections.Counter(m['outcome'] for m in members)),
                        'current_member_outcomes': dict(collections.Counter(m['outcome'] for m in current_members)),
                        'original_chunk_members': len(original_chunk_members),
                        'original_chains_missing_now': sorted(original_chains - set(extracted)),
                        'newly_extracted_members_excluded_from_frozen_snapshot': excluded_new_text,
                        'current_nonextracted_members': [
                            {'chain': chain, 'outcome': value['outcome'], 'reason': value['reason']}
                            for chain, values in extracted.items() for value in values
                            if value['outcome'] != 'extracted']}
                    generated = {}
                    if args.text_cache:
                        args.text_cache.mkdir(parents=True, exist_ok=True)
                        cache_final = args.text_cache / f"{file_id}_{record['sha256']}.jsonl.gz"
                        if cache_final.exists():
                            raise ValueError('Verified text cache output already exists')
                        cache_partial = cache_final.with_suffix('.partial')
                        cached = gzip.open(cache_partial, 'wt', encoding='utf-8')
                        cached.write(json.dumps({'file_id': file_id, 'archive_sha256': record['sha256'],
                                                 'source': acquired, 'original_modules_sha256': source_hashes,
                                                 'converter_clock': {k: str(v) for k, v in clock.items()} if clock else None,
                                                 'outcome_audit': outcome_audit}, ensure_ascii=False) + '\n')
                    for chunk in chunks:
                        member = by_member[chunk['member_id']]
                        matches = extracted.get(member['chain'], [])
                        if len(matches) != 1:
                            raise ValueError('Expected member chain is missing or ambiguous')
                        key = member['id']
                        if key not in generated:
                            generated[key] = original.chunk_text(matches[0]['text'])
                        pieces = generated[key]
                        if chunk['seq'] >= len(pieces):
                            raise ValueError('Expected chunk sequence is absent')
                        text = pieces[chunk['seq']]
                        data = text.encode('utf-8')
                        if (hashlib.sha256(data).hexdigest(), len(data), len(text)) != (
                                chunk['text_sha256'], chunk['text_bytes'], chunk['text_chars']):
                            raise ValueError('Extracted text differs at chunk ' + str(chunk['id']))
                        if con:
                            frontier.insert(con, 'chunks', {**chunk, 'text': text})
                        if cached:
                            cached.write(json.dumps({'id': chunk['id'], 'text': text}, ensure_ascii=False) + '\n')
                    expected_sizes = collections.Counter(c['member_id'] for c in chunks)
                    for member_id, count in expected_sizes.items():
                        if len(generated[member_id]) != count:
                            raise ValueError('Extraction produced a different chunk count')
                    if cached:
                        cached.close()
                        cached = None
                        cache_partial.replace(cache_final)
                    tested_chunks += len(chunks)
                    results.append({'file_id': file_id, 'archive_sha256': record['sha256'],
                                    'source': acquired, 'chunks_verified': len(chunks),
                                    'original_opener': record['opener'], 'current_opener': opener,
                                    'outcome_audit': outcome_audit,
                                    'seconds': time.monotonic() - step})
                except (OSError, ValueError, RuntimeError) as error:
                    failures.append({'file_id': file_id, 'error': type(error).__name__,
                                     'detail': str(error)[:300]})
                    if con:
                        raise
                finally:
                    if cached:
                        cached.close()
                    if cache_partial:
                        cache_partial.unlink(missing_ok=True)
                if len(results) % 100 == 0 and results:
                    print(json.dumps({'files_verified': len(results), 'chunks_verified': tested_chunks}), flush=True)
        if selected - known:
            failures.append({'unknown_file_ids': sorted(selected - known)})
        if con:
            if failures:
                raise ValueError('Input reconstruction has failures')
            if tested_chunks != receipt['rows']['chunks']:
                raise ValueError('Complete index does not cover every original chunk')
            for table in schema['tables']:
                if table == 'chunks':
                    continue
                for record in read_rows(args.bundle, table):
                    frontier.insert(con, table, record)
            frontier.finish(con, schema)
            con = None
            partial.replace(args.out_index)
    finally:
        if con:
            con.close()
        changed = {p.name: sha(p) for p in source_modules} != source_hashes
        report = {'scope': 'Pinned archive and original indexed chunk verification, with original/current member outcomes recorded. Frozen exclusions are retained; successful snapshot verification does not mean every source member was extractable.',
                  'runtime': {'python': sys.version, 'executable': sys.executable,
                              'sqlite_version': sqlite3.sqlite_version,
                              'packages': {name: importlib.metadata.version(name) for name in
                                           ('python-docx', 'python-pptx', 'openpyxl', 'pypdf', 'lxml')}},
                  'selected_file_ids': sorted(selected) if selected else None,
                  'converter_clock': {k: str(v) for k, v in clock.items()} if clock else None,
                  'shard_count': args.shard_count, 'shard_index': args.shard_index,
                  'frontier_rows': receipt['rows'], 'verified_files': len(results),
                  'verified_chunks': tested_chunks, 'failures': failures, 'results': results,
                  'seconds': time.monotonic() - started, 'original_modules_sha256': source_hashes,
                  'original_modules_unchanged': not changed,
                  'complete_frontier_verified': not selected and args.shard_count == 1 and not failures and len(results) == receipt['rows']['files'] and tested_chunks == receipt['rows']['chunks'],
                  'index_written': bool(args.out_index and args.out_index.exists())}
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    if failures or changed:
        raise SystemExit(1)
    print(json.dumps({k: v for k, v in report.items() if k not in ('results', 'failures')}))


if __name__ == '__main__':
    main()
