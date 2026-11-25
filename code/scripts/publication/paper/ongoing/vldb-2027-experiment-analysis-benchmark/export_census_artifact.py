#!/usr/bin/env python3
"""Export text-free inputs consumed by the pack and clause census audits.

This is an input projection and validation tool. It preserves the original
audit algorithms and does not claim to restore the CR document corpus.
"""
from __future__ import annotations

import argparse
import collections
from concurrent.futures import ThreadPoolExecutor
import csv
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import time
from urllib.parse import quote, urlsplit
import urllib.request
import zipfile

TRACK = Path('publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark')
PORTAL = Path('data/inventory/RAN/portal_data_all_ran.json')
SCOPE = Path('data/inventory/RAN/wg_spec_mapping.json')
FIELDS = ('wg_tdoc', 'tsg_tdoc', 'tsg_status', 'spec_number')
WGS = ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5')
QUERY = ('MATCH (s:Section) RETURN s.sectionId, s.sectionNumber, s.isVoid, '
         'COUNT { (s)-[:HAS_SUB_SECTION]->(:Section) } > 0, '
         'COUNT { (s)-[:BELONGS_TO_SPEC]->(:Spec) } > 0')


def guard():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            if int(line.split()[1]) < 8 * 1024 ** 2:
                raise RuntimeError('At least 8 GiB available memory is required')
            return
    raise RuntimeError('Cannot read available memory')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def canonical(value):
    if isinstance(value, dict):
        return {str(k): canonical(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, set):
        return sorted((canonical(v) for v in value), key=lambda v: json.dumps(v, sort_keys=True))
    if isinstance(value, (tuple, list)):
        return [canonical(v) for v in value]
    return value


def logical_sha(value):
    return hashlib.sha256(json.dumps(canonical(value), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n').encode()
    if path.suffix == '.gz':
        with path.open('wb') as stream:
            with gzip.GzipFile(fileobj=stream, mode='wb', filename='', mtime=0) as zipped:
                zipped.write(raw)
    else:
        path.write_bytes(raw)


def read_json(path):
    path = Path(path)
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt') as stream:
        return json.load(stream)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class JsonInput:
    def __init__(self, portal, scope):
        self.portal, self.scope = portal, scope

    def json(self, path):
        if path == PORTAL:
            return self.portal
        if path == SCOPE:
            return self.scope
        raise ValueError(f'Unexpected audit input: {path}')


def structure_value(value):
    return {key: value[key] for key in ('records', 'tally', 'shape', 'keys', 'releases')}


def export_auxiliary_metadata(pack, clause, root, out):
    corpus, parsed = pack.CORPUS, clause.PARSED_CR
    source_records, checks = {}, {}
    pack.CORPUS = root / corpus
    try:
        original_lists = pack.read_cr_lists()
        for source in sorted(pack.CORPUS.glob('*/source/Rel-*/metadata/cr_list.csv')):
            relative = source.relative_to(pack.CORPUS)
            target = out / 'cr_lists' / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            fields = ('wg_tdoc', 'tsg_tdoc', 'tsg_status', 'target_release')
            with source.open(encoding='utf-8', errors='replace', newline='') as handle:
                rows = list(csv.DictReader(handle))
            with target.open('w', encoding='utf-8', newline='') as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerows({k: row.get(k, '') for k in fields} for row in rows)
            source_records[str(corpus / relative)] = {'sha256': sha(source), 'bytes': source.stat().st_size,
                                                      'rows': len(rows), 'projectedFields': list(fields)}
        pack.CORPUS = out / 'cr_lists'
        restored_lists = pack.read_cr_lists()
        if original_lists != restored_lists:
            raise RuntimeError('CR-list projection changes the original audit input')
        checks['crListWgDocumentKeys'] = len(restored_lists)
        checks['crListReaderOutputSha256'] = logical_sha(restored_lists)
        checks['crListReaderOutputEqual'] = True
    finally:
        pack.CORPUS = corpus
    checks['parsedCr'] = {}
    for wg in WGS:
        source = root / parsed / wg / 'cr_documents.json'
        data = read_json(source)
        rows = data.get('cr_documents') or data.get('documents') or []
        fields = ('tdoc_number', 'source_path', 'release')
        projected = {'cr_documents': [{k: row[k] for k in fields if k in row} for row in rows]}
        target = out / 'parsed_cr' / wg / 'cr_documents.json'
        write_json(target, projected)
        try:
            clause.PARSED_CR = root / parsed
            original = clause.build_parse(wg)
            clause.PARSED_CR = out / 'parsed_cr'
            restored = clause.build_parse(wg)
        finally:
            clause.PARSED_CR = parsed
        if original != restored:
            raise RuntimeError(f'{wg}: Parsed-CR projection changes the original audit input')
        source_records[str(parsed / wg / 'cr_documents.json')] = {'sha256': sha(source), 'bytes': source.stat().st_size,
                                                                'rows': len(rows), 'projectedFields': list(fields)}
        checks['parsedCr'][wg] = {'readerOutputSha256': logical_sha(restored), 'readerOutputEqual': True,
                                   'pathKeys': len(restored[0]), 'releaseKeys': len(restored[1])}
    return source_records, checks


def install_structure_adapter(module, artifact):
    """Make the original load_structure algorithm consume the exported rows.

    Only the one original read query is accepted. This does not replace the
    other corpus or service inputs consumed elsewhere in the census program.
    """
    artifact = Path(artifact)
    module.STRUCTURE_FILE = {}
    module.STRUCTURE_NEO4J = {wg: wg for wg in WGS}

    def rows(wg, query):
        if query != QUERY:
            raise ValueError('The adapter accepts only the pinned structure query')
        return read_json(artifact / 'structure' / f'{wg}.json.gz')

    module.neo4j_rows = rows
    original_loader = module.load_structure

    def load(wg):
        result = original_loader(wg)
        result['source'] = 'artifact/structure/' + wg + '.json.gz'
        return result

    module.load_structure = load
    return module


def export(args):
    started = time.monotonic()
    root, out = Path(args.repository).resolve(), Path(args.out).resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError('Export destination must be empty')
    out.mkdir(parents=True, exist_ok=True)
    guard()
    code = root / 'scripts' / TRACK
    pack = load_module(code / 'audit_pack_links.py', 'census_pack_original')
    clause = load_module(code / 'audit_clause_links.py', 'census_clause_original')
    original_portal = read_json(root / PORTAL)
    scope = read_json(root / SCOPE)
    projected = {release: [{k: row[k] for k in FIELDS if k in row} for row in rows]
                 if isinstance(rows, list) else rows for release, rows in original_portal.items()}
    original_inputs = JsonInput(original_portal, scope)
    projected_inputs = JsonInput(projected, scope)
    old_portal, new_portal = pack.read_portal(original_inputs), pack.read_portal(projected_inputs)
    if old_portal != new_portal:
        raise RuntimeError('Portal projection changes the original audit input')
    write_json(out / 'inputs/portal_audit_fields.json.gz', projected)
    (out / 'inputs').mkdir(exist_ok=True)
    shutil.copyfile(root / SCOPE, out / 'inputs/wg_spec_mapping.json')
    historical_pack = read_json(root / 'logs' / TRACK / 'pack_link_audit.json')
    historical_inputs = {row['path']: row['sha256'] for row in historical_pack['inputs']}
    historic_structure = read_json(root / 'logs' / TRACK / 'final/reconciliation/clause_link_audit_rerun.json')['structureSources']
    manifest = {'schema': 'spectra-census-inputs', 'scope': 'Portal fields, collection scope and complete structure resolver metadata; original CR/archive text and other census service inputs remain separate.',
                'code': {name: sha(code / name) for name in ['audit_pack_links.py', 'audit_clause_links.py']},
                'sources': {str(p): {'sha256': sha(root / p), 'bytes': (root / p).stat().st_size,
                                     'sameAsHistoricalPackInput': sha(root / p) == historical_inputs.get(str(p))}
                            for p in [PORTAL, SCOPE]},
                'portalFields': list(FIELDS), 'structure': {}}
    checks = {'portalRows': sum(len(rows) for rows in projected.values() if isinstance(rows, list)),
              'portalWgDocumentKeys': len(new_portal), 'portalReaderOutputSha256': logical_sha(new_portal),
              'portalReaderOutputEqual': old_portal == new_portal, 'scopeReaderOutputSha256': logical_sha(pack.read_spec_scope(original_inputs)),
              'scopeBytesEqual': sha(root / SCOPE) == sha(out / 'inputs/wg_spec_mapping.json'), 'structure': {}}
    auxiliary_sources, auxiliary_checks = export_auxiliary_metadata(pack, clause, root, out)
    manifest['auxiliarySources'] = auxiliary_sources
    checks.update(auxiliary_checks)
    for wg in WGS:
        guard()
        saved_query = clause.neo4j_rows
        saved_graph = clause.graph
        saved_structure = dict(clause.STRUCTURE_FILE)
        captured = []
        if wg in clause.STRUCTURE_FILE:
            path = clause.STRUCTURE_FILE[wg]
            records = read_json(root / path)['@graph']
            captured = [(r.get('sectionId'), r.get('sectionNumber'), r.get('isVoid'), bool(clause.as_list(r.get('hasSubSection'))), True) for r in records]
            clause.graph = lambda unused, records=records: records
            source = {'kind': 'file', 'path': str(path), 'sha256': sha(root / path), 'bytes': (root / path).stat().st_size}
        else:
            if not args.live_structure:
                raise ValueError('RAN4/RAN5 require --live-structure read-only access to the existing services')
            def capture(port, query):
                rows = saved_query(port, query)
                captured.extend(rows)
                return rows
            clause.neo4j_rows = capture
            source = {'kind': 'existing-readonly-service', 'port': clause.STRUCTURE_NEO4J[wg], 'query': QUERY}
        try:
            original = clause.load_structure(wg)
        finally:
            clause.neo4j_rows, clause.graph = saved_query, saved_graph
            clause.STRUCTURE_FILE = saved_structure
        write_json(out / 'structure' / f'{wg}.json.gz', captured)
        original_digest = logical_sha(structure_value(original))
        expected = historic_structure[wg]
        summary = {'records': original['records'], 'tally': original['tally'], 'resolverKeys': len(original['keys'])}
        same_historical = all(summary[k] == expected[k] for k in summary)
        manifest['structure'][wg] = {'source': source, 'logicalOutputSha256': original_digest,
                                      'historicalSummary': expected, 'currentSummary': summary,
                                      'sameAsHistoricalSummary': same_historical}
        checks['structure'][wg] = {'originalLogicalOutputSha256': original_digest, 'sameAsHistoricalSummary': same_historical}
    offline = load_module(code / 'audit_clause_links.py', 'census_clause_offline')
    install_structure_adapter(offline, out)
    for wg in WGS:
        digest = logical_sha(structure_value(offline.load_structure(wg)))
        checks['structure'][wg].update(offlineLogicalOutputSha256=digest, exactLogicalOutputMatch=digest == manifest['structure'][wg]['logicalOutputSha256'])
        if not checks['structure'][wg]['exactLogicalOutputMatch']:
            raise RuntimeError(f'{wg}: Offline structure projection differs')
    manifest['files'] = {str(p.relative_to(out)): {'sha256': sha(p), 'bytes': p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file()}
    write_json(out / 'manifest.json', manifest)
    checks['seconds'] = round(time.monotonic() - started, 3)
    write_json(out / 'validation.json', checks)
    print(json.dumps(checks, ensure_ascii=False))


def verify(args):
    artifact, code = Path(args.artifact).resolve(), Path(args.code_directory).resolve()
    manifest = read_json(artifact / 'manifest.json')
    for name, info in manifest['files'].items():
        p = (artifact / name).resolve()
        if not p.is_relative_to(artifact) or sha(p) != info['sha256']:
            raise ValueError(f'Artifact checksum mismatch: {name}')
    for name, expected in manifest['code'].items():
        if sha(code / name) != expected:
            raise ValueError(f'Original audit source mismatch: {name}')
    pack = load_module(code / 'audit_pack_links.py', 'census_verify_pack')
    clause = install_structure_adapter(load_module(code / 'audit_clause_links.py', 'census_verify_clause'), artifact)
    projected = JsonInput(read_json(artifact / 'inputs/portal_audit_fields.json.gz'), read_json(artifact / 'inputs/wg_spec_mapping.json'))
    prior = read_json(artifact / 'validation.json')
    portal_digest = logical_sha(pack.read_portal(projected))
    if portal_digest != prior['portalReaderOutputSha256']:
        raise ValueError('Portal reader output mismatch')
    scope_digest = logical_sha(pack.read_spec_scope(projected))
    if scope_digest != prior['scopeReaderOutputSha256']:
        raise ValueError('Collection scope reader output mismatch')
    pack.CORPUS = artifact / 'cr_lists'
    cr_list_digest = logical_sha(pack.read_cr_lists())
    if cr_list_digest != prior['crListReaderOutputSha256']:
        raise ValueError('CR-list reader output mismatch')
    clause.PARSED_CR = artifact / 'parsed_cr'
    parsed_digests = {wg: logical_sha(clause.build_parse(wg)) for wg in WGS}
    for wg, digest in parsed_digests.items():
        if digest != prior['parsedCr'][wg]['readerOutputSha256']:
            raise ValueError(f'{wg}: Parsed-CR reader output mismatch')
    structures = {wg: logical_sha(structure_value(clause.load_structure(wg))) for wg in WGS}
    for wg, digest in structures.items():
        if digest != manifest['structure'][wg]['logicalOutputSha256']:
            raise ValueError(f'{wg}: Structure reader output mismatch')
    report = {'checkedFiles': len(manifest['files']), 'portalReaderOutputSha256': portal_digest,
              'scopeReaderOutputSha256': scope_digest,
              'crListReaderOutputSha256': cr_list_digest, 'parsedCrReaderOutputSha256': parsed_digests,
              'structureLogicalOutputSha256': structures, 'offline': True,
              'scope': manifest['scope']}
    if args.report:
        write_json(args.report, report)
    print(json.dumps(report))


def source_inventory(args):
    """Pin every existing CR source archive without distributing its body."""
    root, out = Path(args.repository).resolve(), Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    destination = out / 'archives.jsonl.gz'
    if destination.exists():
        raise ValueError('Source inventory destination already exists')
    started = time.monotonic()
    corpus = root / 'data/corpus/tsg/RAN/formal/change-requests'
    urls = collections.defaultdict(set)
    metadata_files = []
    def add_urls(row):
        for key, url_keys in [('wg_tdoc', ('wg_tdoc_url',)), ('tsg_tdoc', ('tsg_tdoc_url', 'tsg_ftp_url'))]:
            identifier = (row.get(key) or '').strip().upper()
            for url_key in url_keys:
                value = (row.get(url_key) or '').strip()
                parsed = urlsplit(value)
                if identifier and parsed.scheme in ('http', 'https') and (parsed.hostname == '3gpp.org' or (parsed.hostname or '').endswith('.3gpp.org')):
                    urls[identifier].add(value)
    for path in sorted(corpus.glob('*/source/Rel-*/metadata/cr_list.csv')):
        with path.open(encoding='utf-8', errors='replace', newline='') as handle:
            for row in csv.DictReader(handle):
                add_urls(row)
        metadata_files.append({'path': str(path.relative_to(root)), 'sha256': sha(path), 'bytes': path.stat().st_size})
    portal_source = root / PORTAL
    for rows in read_json(portal_source).values():
        for row in rows if isinstance(rows, list) else []:
            add_urls(row)
    metadata_files.append({'path': str(PORTAL), 'sha256': sha(portal_source), 'bytes': portal_source.stat().st_size})
    groups = collections.defaultdict(list)
    for path in sorted(corpus.glob('*/source/Rel-*/**/*.zip')):
        if path.is_file():
            stat = path.stat()
            groups[(stat.st_dev, stat.st_ino)].append(path)
    counts = collections.Counter()
    bytes_total = 0
    with destination.open('wb') as stream:
        with gzip.GzipFile(fileobj=stream, mode='wb', filename='', mtime=0) as zipped:
            for index, paths in enumerate(groups.values()):
                if index % 1000 == 0:
                    guard()
                path = paths[0]
                candidates = sorted(set().union(*(urls.get(p.stem.upper(), set()) for p in paths)))
                record = {'paths': [str(p.relative_to(root)) for p in paths], 'sha256': sha(path),
                          'bytes': path.stat().st_size, 'candidateUrls': candidates,
                          'urlBasis': 'Official URL fields in local CR-list and Portal metadata; not a network restoration receipt'}
                try:
                    with zipfile.ZipFile(path) as archive:
                        record['members'] = [{'name': item.filename, 'bytes': item.file_size, 'crc32': item.CRC, 'isDirectory': item.is_dir()} for item in archive.infolist()]
                    counts['zipDirectoryReadable'] += 1
                    counts['members'] += len(record['members'])
                except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile, NotImplementedError, UnicodeError, RuntimeError) as error:
                    record['archiveDirectoryError'] = type(error).__name__
                    counts['zipDirectoryUnreadable'] += 1
                counts['archives'] += 1
                counts['paths'] += len(paths)
                counts['archivesWithCandidateUrl' if candidates else 'archivesWithoutCandidateUrl'] += 1
                bytes_total += record['bytes']
                zipped.write((json.dumps(record, ensure_ascii=False, separators=(',', ':')) + '\n').encode())
    summary = {'schema': 'spectra-cr-source-inventory', 'counts': dict(counts), 'bytesAcrossDistinctInodes': bytes_total,
               'metadataFiles': metadata_files, 'manifestSha256': sha(destination), 'manifestBytes': destination.stat().st_size,
               'seconds': round(time.monotonic() - started, 3),
               'scope': 'Complete existing CR source-zip path/inode census with archive SHA-256 and native ZIP member directory metadata. Member CRCs are ZIP metadata, not cryptographic member hashes. Candidate URLs are provenance, not confirmed download availability. Original derived-file conversions and archive-member restoration remain separate.'}
    write_json(out / 'summary.json', summary)
    print(json.dumps(summary))


def stage(args):
    """Stage the projected metadata at the paths the original audits read."""
    artifact, destination = Path(args.artifact).resolve(), Path(args.destination).resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ValueError('Metadata staging destination must be empty')
    manifest = read_json(artifact / 'manifest.json')
    for name, record in manifest['files'].items():
        path = (artifact / name).resolve()
        if not path.is_relative_to(artifact) or sha(path) != record['sha256']:
            raise ValueError(f'Artifact checksum mismatch: {name}')
    write_json(destination / PORTAL, read_json(artifact / 'inputs/portal_audit_fields.json.gz'))
    (destination / SCOPE).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(artifact / 'inputs/wg_spec_mapping.json', destination / SCOPE)
    shutil.copytree(artifact / 'cr_lists', destination / 'data/corpus/tsg/RAN/formal/change-requests', dirs_exist_ok=False)
    shutil.copytree(artifact / 'parsed_cr', destination / 'ontology/output/tsg/RAN/formal/parsed_cr', dirs_exist_ok=False)
    print(json.dumps({'staged': True, 'destination': str(destination),
                      'scope': 'Text-free audit metadata only; source archives, original derived documents and graph records are separate inputs.'}))


def merge_source_urls(args):
    """Join the plenary source frontier by the exact archive content hash."""
    folder = Path(args.inventory).resolve()
    summary = read_json(folder / 'summary.json')
    frontier = collections.defaultdict(set)
    if args.plenary_files:
        join_source = Path(args.plenary_files).resolve()
        with gzip.open(join_source, 'rt') as stream:
            rows = [json.loads(line) for line in stream]
        url_field, label = 'official_urls', 'plenary'
    else:
        join_source = Path(args.local_meeting_candidates).resolve()
        rows = read_json(join_source)['matches']
        url_field, label = 'candidateUrls', 'local_meeting'
    for row in rows:
        for url in row.get(url_field) or []:
            parsed = urlsplit(url)
            if parsed.scheme not in ('http', 'https') or not (parsed.hostname == '3gpp.org' or (parsed.hostname or '').endswith('.3gpp.org')):
                raise ValueError('Source frontier contains a URL outside the official host scope')
            frontier[row['sha256']].add(url)
    source = folder / 'archives.jsonl.gz'
    before = folder / f'archives_before_{label}_join.jsonl.gz'
    if before.exists():
        raise ValueError('This URL join has already been recorded')
    prior_sha = summary['manifestSha256']
    if sha(source) != prior_sha:
        raise ValueError('Source inventory checksum mismatch')
    source.rename(before)
    counts = collections.Counter()
    original_digest, joined_digest = hashlib.sha256(), hashlib.sha256()
    with gzip.open(before, 'rt') as incoming, source.open('wb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as outgoing:
            for line in incoming:
                row = json.loads(line)
                fixed = {k: v for k, v in row.items() if k not in ('candidateUrls', 'urlBasis')}
                original_digest.update(json.dumps(fixed, sort_keys=True, ensure_ascii=False).encode() + b'\n')
                old = set(row['candidateUrls'])
                new = old | frontier.get(row['sha256'], set())
                counts['archives'] += 1
                counts['newlyMappedArchives'] += bool(new) and not bool(old)
                counts['archivesWithCandidateUrl' if new else 'archivesWithoutCandidateUrl'] += 1
                row['candidateUrls'] = sorted(new)
                row['urlBasis'] = 'Official metadata URL fields or identical-SHA actual meeting-source path and FTP layout; not a network restoration receipt'
                fixed_after = {k: v for k, v in row.items() if k not in ('candidateUrls', 'urlBasis')}
                joined_digest.update(json.dumps(fixed_after, sort_keys=True, ensure_ascii=False).encode() + b'\n')
                outgoing.write((json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n').encode())
    if original_digest.digest() != joined_digest.digest():
        raise RuntimeError('URL join changed pinned archive or member metadata')
    summary['counts'].update({k: counts[k] for k in ['archivesWithCandidateUrl', 'archivesWithoutCandidateUrl']})
    summary['manifestSha256'], summary['manifestBytes'] = sha(source), source.stat().st_size
    field = 'plenaryUrlJoin' if label == 'plenary' else 'localMeetingUrlJoin'
    recorded_path = str(join_source.relative_to(Path.cwd())) if join_source.is_relative_to(Path.cwd()) else str(join_source)
    summary[field] = {'path': recorded_path, 'sha256': sha(join_source), 'priorManifestSha256': prior_sha,
                                'newlyMappedArchives': counts['newlyMappedArchives'],
                                'allPinnedArchiveAndMemberMetadataUnchanged': True,
                                'pinnedArchiveAndMemberLogicalSha256': original_digest.hexdigest()}
    write_json(folder / 'summary.json', summary)
    print(json.dumps({'counts': summary['counts'], field: summary[field],
                      'manifestSha256': summary['manifestSha256'], 'manifestBytes': summary['manifestBytes']}))


def local_meeting_urls(args):
    """Locate identical archive bytes in the actual meeting-source trees."""
    root, folder = Path(args.repository).resolve(), Path(args.inventory).resolve()
    registry_path = root / 'scripts/common/common/axis.py'
    registry = load_module(registry_path, 'census_axis_registry')
    missing = []
    byname = collections.defaultdict(set)
    with gzip.open(folder / 'archives.jsonl.gz', 'rt') as stream:
        for line in stream:
            row = json.loads(line)
            if not row['candidateUrls']:
                missing.append(row['sha256'])
                for path in row['paths']:
                    byname[Path(path).name.casefold()].add(row['sha256'])
    matches, scanned = [], 0
    for wg in WGS:
        start = root / f'data/corpus/tsg/RAN/formal/meetings/{wg}/source'
        for directory, _, files in os.walk(start):
            scanned += len(files)
            for name in files:
                if name.casefold() not in byname:
                    continue
                path = Path(directory) / name
                digest = sha(path)
                if digest not in byname[name.casefold()]:
                    continue
                relative = path.relative_to(root)
                local = path.relative_to(start)
                if len(local.parts) != 3 or local.parts[1] not in ('Docs', 'Report'):
                    raise ValueError('Meeting-source path is outside the pinned FTP layout')
                remote = registry.ftp_dir(wg)
                url = 'https://www.3gpp.org/ftp/tsg_ran/' + remote + '/' + '/'.join(quote(p, safe='') for p in local.parts)
                matches.append({'sha256': digest, 'localSourcePath': str(relative), 'candidateUrls': [url],
                                'bytes': path.stat().st_size,
                                'basis': 'Identical local archive bytes at actual meeting-source path plus official FTP layout; network restoration separate'})
    report = {'missingBefore': len(missing), 'fileNamesScanned': scanned, 'identicalArchiveMatches': len(matches),
              'distinctArchivesMatched': len({row['sha256'] for row in matches}), 'matches': matches,
              'ftpRegistry': {'path': str(registry_path.relative_to(root)), 'sha256': sha(registry_path)}}
    write_json(args.out, report)
    print(json.dumps({key: value for key, value in report.items() if key != 'matches'}))


def verify_local_urls(args):
    """Download every newly located archive and check its original byte hash."""
    candidates, cache = Path(args.candidates).resolve(), Path(args.cache).resolve()
    cache.mkdir(parents=True, exist_ok=True)
    selected = read_json(candidates)['matches']
    started = time.monotonic()

    def fetch(row):
        if len(row['sha256']) != 64 or any(c not in '0123456789abcdef' for c in row['sha256']) or not isinstance(row['bytes'], int) or row['bytes'] < 0:
            raise ValueError('Archive hash or pinned size is invalid')
        target = cache / (row['sha256'] + '.zip')
        result = {'localSourcePath': row['localSourcePath'], 'expectedSha256': row['sha256'],
                  'expectedBytes': row['bytes'], 'attempts': []}
        if target.exists() and target.stat().st_size == row['bytes'] and sha(target) == row['sha256']:
            return {**result, 'status': 'verified_cache', 'bytes': target.stat().st_size}
        for url in row['candidateUrls']:
            parsed = urlsplit(url)
            if parsed.scheme != 'https' or not (parsed.hostname == '3gpp.org' or (parsed.hostname or '').endswith('.3gpp.org')):
                raise ValueError('Candidate URL is outside the official HTTPS host scope')
            attempt = {'url': url}
            temporary = target.with_suffix('.part')
            try:
                request = urllib.request.Request(url, headers={'User-Agent': 'SPECTRA-source-check/1.0'})
                with urllib.request.urlopen(request, timeout=60) as response, temporary.open('wb') as output:
                    final = response.geturl()
                    host = urlsplit(final).hostname or ''
                    if host != '3gpp.org' and not host.endswith('.3gpp.org'):
                        raise ValueError('Download redirected outside the official host scope')
                    attempt['finalUrl'] = final
                    count, digest = 0, hashlib.sha256()
                    while True:
                        block = response.read(1 << 20)
                        if not block:
                            break
                        count += len(block)
                        if count > row['bytes']:
                            raise ValueError('Download exceeds the pinned archive size')
                        output.write(block)
                        digest.update(block)
                attempt.update(bytes=count, sha256=digest.hexdigest())
                if count != row['bytes'] or digest.hexdigest() != row['sha256']:
                    raise ValueError('Downloaded archive differs from the pinned original bytes')
                temporary.replace(target)
                result['attempts'].append(attempt)
                return {**result, 'status': 'verified_download', 'bytes': count}
            except (OSError, ValueError) as error:
                attempt.update(error=type(error).__name__, detail=str(error))
                result['attempts'].append(attempt)
                temporary.unlink(missing_ok=True)
        return {**result, 'status': 'source_unavailable'}

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        results = list(executor.map(fetch, selected))
    report = {'candidatesSha256': sha(candidates), 'selected': len(selected),
              'selection': 'Every archive newly located in actual meeting-source trees',
              'statusCounts': dict(collections.Counter(row['status'] for row in results)),
              'seconds': round(time.monotonic() - started, 3), 'results': results,
              'scope': 'Official archive byte restoration for these local-meeting URL mappings; not derived-file extraction or complete source-census execution.'}
    write_json(args.report, report)
    print(json.dumps({key: value for key, value in report.items() if key != 'results'}))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='mode', required=True)
    ex = sub.add_parser('export')
    ex.add_argument('--repository', required=True)
    ex.add_argument('--out', required=True)
    ex.add_argument('--live-structure', action='store_true')
    ve = sub.add_parser('verify')
    ve.add_argument('--artifact', required=True)
    ve.add_argument('--code-directory', required=True)
    ve.add_argument('--report')
    si = sub.add_parser('source-inventory')
    si.add_argument('--repository', required=True)
    si.add_argument('--out', required=True)
    st = sub.add_parser('stage')
    st.add_argument('--artifact', required=True)
    st.add_argument('--destination', required=True)
    me = sub.add_parser('merge-source-urls')
    me.add_argument('--inventory', required=True)
    choose = me.add_mutually_exclusive_group(required=True)
    choose.add_argument('--plenary-files')
    choose.add_argument('--local-meeting-candidates')
    lo = sub.add_parser('local-meeting-urls')
    lo.add_argument('--repository', required=True)
    lo.add_argument('--inventory', required=True)
    lo.add_argument('--out', required=True)
    vu = sub.add_parser('verify-local-urls')
    vu.add_argument('--candidates', required=True)
    vu.add_argument('--cache', required=True)
    vu.add_argument('--report', required=True)
    vu.add_argument('--workers', type=int, default=4)
    args = p.parse_args()
    {'export': export, 'verify': verify, 'source-inventory': source_inventory, 'stage': stage,
     'merge-source-urls': merge_source_urls, 'local-meeting-urls': local_meeting_urls,
     'verify-local-urls': verify_local_urls}[args.mode](args)


if __name__ == '__main__':
    main()
