#!/usr/bin/env python3
"""Stage and replay the original census audits and reconstruct CR archives.

The released relation records and projected metadata feed the original audit
functions. Local source attachment and archive reconstruction are explicit,
separate modes; receipts distinguish their evidence. Full text stays in the
chosen scratch tree, while receipts contain identities, hashes and counts.
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
import urllib.parse
import urllib.request

TRACK = Path('publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark')
SCRIPT = Path(__file__).resolve()
WGS = ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5')
CORPUS = Path('data/corpus/tsg/RAN/formal/change-requests')
INSTANCES = Path('ontology/output/tsg/RAN/formal/instances')
PARSED = Path('ontology/output/tsg/RAN/formal/parsed_cr')
MEETINGS = Path('data/corpus/tsg/RAN/formal/meetings/TSG_RAN/source')
AGREEMENTS = tuple(Path('logs/publication/paper/ongoing/sigir-2027-research') / name
                   for name in ('pack_source_agreement.json', 'pack_source_agreement_RAN5.json'))
EXPORTER_SHA = 'c660f70ee0966c3092e4188d4e8a9e1642159f73d944fabf70d1a4129ffc5e2a'
ARCHIVES_SHA = 'ef1668bfead171a7fc549fa63e67e8e7970073d3d6b413fb60980b8d9eb01b1a'


def guard():
    available = next(int(v.split()[1]) for v in Path('/proc/meminfo').read_text().splitlines()
                     if v.startswith('MemAvailable:'))
    if available < 8 * 1024 ** 2:
        raise RuntimeError('At least 8 GiB available memory is required')
    return available / 1024 ** 2


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    opener = gzip.open if Path(path).suffix == '.gz' else open
    with opener(path, 'rt', encoding='utf-8') as stream:
        return json.load(stream)


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def rows(path):
    with gzip.open(path, 'rt', encoding='utf-8') as stream:
        for line in stream:
            yield json.loads(line)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def safe(root, relative):
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Input path is outside the relative corpus layout')
    return root / relative


def original_modules():
    exporter = SCRIPT.with_name('export_census_artifact.py')
    if sha(exporter) != EXPORTER_SHA:
        raise ValueError('The frozen metadata exporter changed')
    return load(exporter, 'census_metadata_exporter')


def checked_inventory(path):
    if sha(path) != ARCHIVES_SHA:
        raise ValueError('The pinned archive inventory changed')
    return rows(path)


@contextlib.contextmanager
def cwd(path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def stage(args):
    """Expand released records at the original readers' relative paths."""
    exporter = original_modules()
    destination = args.destination.resolve()
    artifact = args.artifact.resolve()
    release = args.release.resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ValueError('The staging destination must be empty')
    exporter.stage(argparse.Namespace(artifact=artifact, destination=destination))
    receipts = []
    for wg in WGS:
        for relative in (Path('phase-1') / wg / 'tdocs.jsonld',
                         Path('phase-4') / wg / 'crpacks.jsonld',
                         Path('phase-4') / wg / 'cr_extensions.jsonld',
                         Path('phase-4') / wg / 'section_extensions.jsonld'):
            guard()
            released_relative = (Path('RAN5_graph_export') / wg / relative.name
                                 if wg == 'RAN5' and relative.parts[0] == 'phase-4' else relative)
            source = release / 'records' / released_relative
            if not source.is_file():
                source = source.with_suffix(source.suffix + '.gz')
            target = destination / INSTANCES / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.suffix == '.gz':
                with gzip.open(source, 'rb') as incoming, target.open('wb') as outgoing:
                    shutil.copyfileobj(incoming, outgoing)
            else:
                shutil.copyfile(source, target)
            receipts.append({'releasedPath': str(source.relative_to(release)),
                             'releasedSha256': sha(source), 'stagedPath': str(target.relative_to(destination)),
                             'stagedSha256': sha(target), 'stagedBytes': target.stat().st_size})
    attachment = None
    if args.local_source_root:
        original = args.local_source_root.resolve()
        links = []
        for wg_dir in sorted((original / CORPUS).iterdir()):
            if not wg_dir.is_dir():
                continue
            for slot in ('derived',):
                source = wg_dir / slot
                if source.is_dir():
                    target = destination / CORPUS / wg_dir.name / slot
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.symlink_to(source, target_is_directory=True)
                    links.append(str(target.relative_to(destination)))
            for release_dir in sorted((wg_dir / 'source').glob('Rel-*')):
                for source in sorted(release_dir.iterdir()):
                    if source.name == 'metadata':
                        continue
                    target = destination / CORPUS / wg_dir.name / 'source' / release_dir.name / source.name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.symlink_to(source, target_is_directory=source.is_dir())
                    links.append(str(target.relative_to(destination)))
        target = destination / MEETINGS
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(original / MEETINGS, target_is_directory=True)
        links.append(str(MEETINGS))
        attachment = {'mode': args.source_mode, 'linkedInputs': links,
                      'newOfficialDownloadPerformedByStage': False,
                      'archiveReconstructionPerformedByStage': False}
    agreements = []
    for relative in AGREEMENTS:
        source = release / 'responses' / relative.name
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        agreements.append({'path': str(relative), 'sha256': sha(source)})
    receipt = {'metadataArtifactManifestSha256': sha(artifact / 'manifest.json'),
               'metadataExporterSha256': EXPORTER_SHA, 'releasedRecords': receipts,
               'agreementDiagnostics': agreements, 'sourceAttachment': attachment}
    write(args.receipt, receipt)
    print(json.dumps({'stagedRecords': len(receipts), 'sourceMode': attachment['mode'] if attachment else 'unattached'}))


def differences(left, right, path=''):
    if isinstance(left, dict) and isinstance(right, dict):
        result = []
        for key in sorted(set(left) | set(right)):
            here = f'{path}/{key}'
            if key not in left or key not in right:
                result.append({'path': here, 'expected': left.get(key), 'actual': right.get(key)})
            else:
                result.extend(differences(left[key], right[key], here))
        return result
    if left == right:
        return []
    return [{'path': path, 'expected': left, 'actual': right}]


def counts_only(value):
    """Examples retain stage-dependent paths; scientific fields remain exact."""
    if isinstance(value, dict):
        return {key: counts_only(item) for key, item in value.items()
                if key not in ('examples', 'source', 'sources')}
    if isinstance(value, list):
        return [counts_only(item) for item in value]
    return value


def audit(args):
    exporter = original_modules()
    stage_root = args.stage.resolve()
    artifact = args.artifact.resolve()
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest = read(artifact / 'manifest.json')
    code_hashes = manifest['code']
    modules = {}
    for kind in args.audits:
        path = SCRIPT.with_name(f'audit_{kind}_links.py')
        actual = sha(path)
        # These source hashes are also copied into the executable receipt.
        declared = code_hashes[path.name]
        if isinstance(declared, dict):
            declared = declared.get('sha256')
        if declared and actual != declared:
            raise ValueError(f'Original auditor changed: {path.name}')
        modules[kind] = load(path, f'census_original_{kind}_audit')
    results = {}
    for kind, module in modules.items():
        guard()
        start = time.monotonic()
        target = output / f'{kind}_audit.json'
        with cwd(stage_root):
            previous = sys.argv
            try:
                if kind == 'clause':
                    exporter.install_structure_adapter(module, artifact)
                    module.RAN5_EXPORT = module.PHASE4 / 'RAN5'
                    sys.argv = [module.__file__, '--wg', *args.wg, '--workers', str(args.workers),
                                '--no-qdrant', '--out', str(target),
                                '--unconfirmed-jsonl', str(output / 'clause_unconfirmed.jsonl')]
                else:
                    sys.argv = [module.__file__, '--wg', *args.wg, '--out', str(target),
                                '--items', str(output / 'pack_items.jsonl'), '--min-available-gib', '8',
                                '--agreement', *map(str, AGREEMENTS)]
                module.main()
            finally:
                sys.argv = previous
        actual = read(target)
        expected_file = (args.reference / ('pack_link_audit.json' if kind == 'pack' else
                         'final/reconciliation/clause_link_audit_rerun.json')).resolve()
        expected = read(expected_file)
        if kind == 'pack':
            compared = ['total'] if tuple(args.wg) == WGS else []
            comparison = {key: differences(counts_only(expected[key]), counts_only(actual[key]), '/' + key)
                          for key in compared}
            expected_wg = {item['wg']: item for item in expected['byWg'] if item['wg'] in args.wg}
            actual_wg = {item['wg']: item for item in actual['byWg']}
            comparison['byWg'] = differences(counts_only(expected_wg), counts_only(actual_wg), '/byWg')
        else:
            comparison = {'wg': differences(counts_only({wg: expected['wg'][wg] for wg in args.wg}),
                                             counts_only(actual['wg']), '/wg')}
            if tuple(args.wg) == WGS:
                comparison['corpus'] = differences(expected['corpus'], actual['corpus'], '/corpus')
            comparison['bodyText'] = differences(expected['bodyText'], actual['bodyText'], '/bodyText')
        results[kind] = {'auditorSha256': sha(Path(module.__file__)), 'outputSha256': sha(target),
                         'referenceSha256': sha(expected_file), 'elapsedSeconds': time.monotonic() - start,
                         'comparison': comparison, 'allComparedFieldsMatch': not any(comparison.values())}
        write(output / 'replay_receipt.json', {'metadataExporterSha256': EXPORTER_SHA,
              'audits': results, 'condition': 'Original full census condition, --no-qdrant for clause audit',
              'sourceMode': args.source_mode})
        print(json.dumps({'audit': kind, 'elapsedSeconds': results[kind]['elapsedSeconds'],
                          'allComparedFieldsMatch': results[kind]['allComparedFieldsMatch']}), flush=True)
    if any(not result['allComparedFieldsMatch'] for result in results.values()):
        raise SystemExit(1)


def verify_sources(args):
    start = time.monotonic()
    counts = collections.Counter()
    failures = []
    checked = hashlib.sha256()
    for row in checked_inventory(args.inventory):
        if counts['archiveInodes'] % 1024 == 0:
            guard()
        path = next((safe(args.source_root, value) for value in row['paths']
                     if safe(args.source_root, value).is_file()), None)
        if path is None:
            failures.append({'paths': row['paths'], 'error': 'missing'})
            continue
        actual = sha(path)
        counts['archiveInodes'] += 1
        counts['archivePaths'] += len(row['paths'])
        counts['archiveBytes'] += row['bytes']
        counts['nativeDirectoryErrorsPreserved'] += bool(row.get('archiveDirectoryError'))
        if path.stat().st_size != row['bytes'] or actual != row['sha256']:
            failures.append({'path': str(path.relative_to(args.source_root)), 'expected': row['sha256'], 'actual': actual})
        checked.update((row['sha256'] + '\n').encode())
    write(args.receipt, {'mode': 'local_original_archive_hash_verification', 'inventorySha256': sha(args.inventory),
                         'counts': dict(counts), 'failures': failures,
                         'verifiedInventoryOrderSha256': checked.hexdigest(), 'elapsedSeconds': time.monotonic() - start,
                         'newOfficialDownload': False})
    print(json.dumps({'counts': dict(counts), 'failures': len(failures), 'elapsedSeconds': time.monotonic() - start}))
    if failures:
        raise SystemExit(1)


def derived_frontier(args):
    """Pin names, empty directories and bytes consumed by the corpus readers."""
    counts = collections.Counter()
    output = args.frontier
    output.parent.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    with output.open('wb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as zipped:
            for wg in WGS:
                base = args.root / CORPUS / wg / 'derived'
                for path in sorted(base.rglob('*')):
                    if counts['files'] % 1024 == 0:
                        guard()
                    record = {'path': str(path.relative_to(args.root)), 'kind': 'directory' if path.is_dir() else 'file'}
                    if path.is_file():
                        first, second = hashlib.sha256(), hashlib.sha1()
                        size = 0
                        with path.open('rb') as stream:
                            for block in iter(lambda: stream.read(4 << 20), b''):
                                first.update(block)
                                second.update(block)
                                size += len(block)
                        record.update({'bytes': size, 'sha256': first.hexdigest(), 'sha1': second.hexdigest()})
                        counts['files'] += 1
                        counts['bytes'] += size
                        counts['wordFiles'] += path.suffix.lower() in ('.doc', '.docx')
                    else:
                        counts['directories'] += 1
                    zipped.write((json.dumps(record, ensure_ascii=False, separators=(',', ':')) + '\n').encode())
    write(args.receipt, {'mode': 'local_original_derived_metadata_frontier', 'counts': dict(counts),
                        'frontierSha256': sha(output), 'frontierBytes': output.stat().st_size,
                        'elapsedSeconds': time.monotonic() - start, 'sourceTextIncluded': False,
                        'newArchiveReconstructionPerformed': False})
    print(json.dumps({'counts': dict(counts), 'elapsedSeconds': time.monotonic() - start}))


def verify_derived(args):
    receipt = read(args.frontier_receipt)
    if sha(args.frontier) != receipt['frontierSha256']:
        raise ValueError('Derived frontier checksum differs')
    counts = collections.Counter()
    failures = []
    for row in rows(args.frontier):
        if counts['files'] % 1024 == 0:
            guard()
        path = safe(args.root, row['path'])
        if row['kind'] == 'directory':
            counts['directories'] += 1
            if not path.is_dir():
                failures.append({'path': row['path'], 'error': 'missing_directory'})
        else:
            counts['files'] += 1
            if not path.is_file():
                failures.append({'path': row['path'], 'error': 'missing_file'})
            elif path.stat().st_size != row['bytes'] or sha(path) != row['sha256']:
                failures.append({'path': row['path'], 'error': 'bytes_differ'})
    write(args.receipt, {'frontierSha256': receipt['frontierSha256'], 'counts': dict(counts), 'failures': failures})
    if failures:
        raise SystemExit(1)


def bundle_code(args):
    files = [Path('scripts') / TRACK / name for name in
             ('restore_census_artifact.py', 'export_census_artifact.py', 'audit_pack_links.py', 'audit_clause_links.py')]
    files += [Path('scripts') / name for name in (
        'tsg/RAN/formal/RAN3/phase-0/extract/extract_crs.py',
        'tsg/RAN/formal/RAN3/phase-0/transform/01_transform_doc_to_docx.py',
        'tsg/RAN/formal/common/native_word_conversion.py',
        'common/common/atomic_io.py', 'common/common/os_residue.py',
        'common/common/zip_names.py', 'common/common/rar_archive.py',
        'common/bootstrap/process_stream.py')]
    manifest = {}
    for relative in files:
        source, target = safe(args.root, relative), safe(args.destination, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        manifest[str(relative)] = {'sha256': sha(source), 'bytes': source.stat().st_size}
    write(args.receipt, {'files': manifest, 'scope': 'Unmodified native constructor dependencies and census replay adapter'})


def stage_plenary_sources(args):
    """Restore meeting ZIP names from independently verified raw archives."""
    if sha(args.frontier) != args.frontier_sha256:
        raise ValueError('Plenary source frontier checksum differs')
    counts = collections.Counter()
    failures = []
    evidence = []
    for row in rows(args.frontier):
        paths = json.loads(row['paths']) if isinstance(row['paths'], str) else row['paths']
        destinations = [Path(path) for path in paths if Path(path).is_relative_to(MEETINGS)]
        if not destinations:
            continue
        guard()
        cached = args.cache / row['sha256'] / 'source.archive' if args.cache else None
        source = cached if cached and cached.is_file() else None
        mode = 'hash_verified_cache'
        if source is None and args.local_source_root:
            source = next((safe(args.local_source_root, path) for path in paths
                           if safe(args.local_source_root, path).is_file()), None)
            mode = 'local_original_read_only_input'
        if source is None:
            failures.append({'sha256': row['sha256'], 'error': 'archive_absent'})
            continue
        if source.stat().st_size != row['bytes'] or sha(source) != row['sha256']:
            failures.append({'sha256': row['sha256'], 'error': 'archive_bytes_differ'})
            continue
        for relative in destinations:
            target = safe(args.destination, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                raise ValueError('Meeting source destination already exists')
            try:
                target.hardlink_to(source)
            except OSError:
                shutil.copyfile(source, target)
            counts['paths'] += 1
        counts['archives'] += 1
        evidence.append({'sha256': row['sha256'], 'bytes': row['bytes'], 'mode': mode,
                         'restoredPaths': list(map(str, destinations))})
        if args.limit and counts['archives'] >= args.limit:
            break
    write(args.receipt, {'frontierSha256': args.frontier_sha256, 'counts': dict(counts),
                        'failures': failures, 'archives': evidence, 'selectionLimit': args.limit,
                        'fullFrontierRestored': not args.limit and not failures})
    if failures:
        raise SystemExit(1)


def acquire(row, args):
    target = args.cache / (row['sha256'] + '.zip')
    if target.is_file():
        mode = 'hash_verified_cache'
    elif args.local_source_root:
        target = next((safe(args.local_source_root, path) for path in row['paths']
                       if safe(args.local_source_root, path).is_file()), None)
        if target is None:
            raise ValueError('Pinned local archive absent')
        mode = 'local_original_archive'
    elif not args.offline:
        errors = []
        args.cache.mkdir(parents=True, exist_ok=True)
        for url in row['candidateUrls']:
            parsed = urllib.parse.urlsplit(url)
            if parsed.scheme not in ('http', 'https') or not (parsed.hostname == '3gpp.org' or
                    (parsed.hostname or '').endswith('.3gpp.org')):
                raise ValueError('URL outside official source scope')
            url = urllib.parse.urlunsplit(('https', parsed.netloc, parsed.path, parsed.query, parsed.fragment))
            partial = target.with_suffix('.partial')
            try:
                request = urllib.request.Request(url, headers={'User-Agent': 'SPECTRA-source-check/1.0'})
                with urllib.request.urlopen(request, timeout=120) as incoming, partial.open('wb') as outgoing:
                    total = 0
                    for block in iter(lambda: incoming.read(1 << 20), b''):
                        total += len(block)
                        if total > row['bytes']:
                            raise ValueError('Downloaded size exceeds pinned archive')
                        outgoing.write(block)
                    final = urllib.parse.urlsplit(incoming.url)
                    if not (final.hostname == '3gpp.org' or (final.hostname or '').endswith('.3gpp.org')):
                        raise ValueError('Redirect outside official source scope')
                if sha(partial) != row['sha256'] or partial.stat().st_size != row['bytes']:
                    raise ValueError('Downloaded archive hash differs')
                partial.replace(target)
                mode = 'official_download_verified'
                break
            except (OSError, ValueError) as error:
                partial.unlink(missing_ok=True)
                errors.append(type(error).__name__)
        else:
            raise ValueError('Official acquisition failed: ' + ', '.join(errors))
    else:
        raise ValueError('Pinned archive absent from offline cache')
    if target.stat().st_size != row['bytes'] or sha(target) != row['sha256']:
        raise ValueError('Archive bytes differ from pinned inventory')
    return target, mode


def derived_path(relative):
    parts = list(Path(relative).parts)
    slot = parts.index('source')
    parts[slot] = 'derived'
    return Path(*parts[:-1]) / Path(parts[-1]).stem


def reconstruction_rows(args, chosen):
    for row in checked_inventory(args.inventory):
        if chosen is not None and row['sha256'] not in chosen:
            continue
        for path in row['paths']:
            if args.scope == 'all' or Path(path).parts[-2] == 'TSG':
                yield row, Path(path)


def reconstruct(args):
    """Use original recursive extraction and original native Word conversion."""
    original_modules()
    project = args.code_root.resolve()
    scratch = args.destination.resolve()
    if scratch.exists() and any(scratch.iterdir()):
        raise ValueError('Reconstruction destination must be empty; use a new tree for an independent run')
    scratch.mkdir(parents=True, exist_ok=True)
    if args.local_source_root and scratch.is_relative_to(args.local_source_root.resolve() / CORPUS):
        raise ValueError('Reconstruction destination must be separate from original CR corpus')
    extractor_path = project / 'scripts/tsg/RAN/formal/RAN3/phase-0/extract/extract_crs.py'
    converter_path = project / 'scripts/tsg/RAN/formal/RAN3/phase-0/transform/01_transform_doc_to_docx.py'
    extractor = load(extractor_path, 'census_native_cr_extractor')
    converter = load(converter_path, 'census_native_word_converter')
    clause = load(SCRIPT.with_name('audit_clause_links.py'), 'census_reconstruction_form_reader')
    pack = load(SCRIPT.with_name('audit_pack_links.py'), 'census_reconstruction_cover_reader')
    chosen = {row['sha256'] for row in read(args.selection)['matches']} if args.selection else None
    by_filename = collections.defaultdict(list)
    if args.compare_root:
        for path in (args.compare_root / CORPUS).glob('*/derived/**/*'):
            if path.is_file():
                by_filename[path.name].append(path)
    records = []
    start = time.monotonic()
    for row, relative in reconstruction_rows(args, chosen):
        guard()
        source, mode = acquire(row, args)
        source_path = safe(scratch, relative)
        source_path.parent.mkdir(parents=True, exist_ok=True)
        if not source_path.exists():
            shutil.copyfile(source, source_path)
        elif sha(source_path) != row['sha256']:
            raise ValueError('Staged archive differs from pinned bytes')
        destination = safe(scratch, derived_path(relative))
        if destination.is_symlink():
            raise ValueError('Reconstruction destination is a symlink')
        statuses = extractor.extract_zip_recursive(source_path, dest=destination)
        before = {str(path.relative_to(destination)): sha(path) for path in destination.rglob('*') if path.is_file()}
        conversion = []
        if args.convert:
            for path in sorted(destination.rglob('*')):
                if not path.is_file() or not converter.needs_conversion(path):
                    continue
                guard()
                target = converter.conversion_target(path)
                if converter.is_drm_wrapped(path) or converter.ole_named_docx(path) == 'irm':
                    conversion.append({'input': str(path.relative_to(destination)), 'status': 'wrapped_source_preserved'})
                    continue
                if target.exists():
                    continue
                kind = 'docx' if converter.is_ooxml(path) else 'doc'
                result = converter.process_file((path, target, kind))
                conversion_record = {'input': str(path.relative_to(destination)), 'output': str(target.relative_to(destination)),
                                     'kind': kind, **{k: v for k, v in result.items() if k != 'file'}}
                native_receipt = Path(str(target) + '.conversion.json')
                if native_receipt.is_file():
                    receipt_destination = scratch / 'conversion_receipts' / native_receipt.relative_to(scratch)
                    receipt_destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(native_receipt, receipt_destination)
                    conversion_record['validationReceipt'] = str(receipt_destination.relative_to(scratch))
                    conversion_record['validationReceiptSha256'] = sha(receipt_destination)
                conversion.append(conversion_record)
        comparison = collections.Counter()
        mismatches = []
        file_receipts = []
        for path in sorted(destination.rglob('*')):
            if not path.is_file():
                continue
            relative_file = path.relative_to(destination)
            pinned_path = derived_path(relative) / relative_file
            file_record = {'path': str(relative_file), 'bytes': path.stat().st_size, 'sha256': sha(path),
                           'nativeExtracted': str(relative_file) in before}
            comparison['reconstructedFiles'] += 1
            if args.compare_root:
                expected = safe(args.compare_root, pinned_path)
                location = 'same_relative_derived_path'
                if not expected.is_file():
                    matching = next((candidate for candidate in by_filename.get(path.name, [])
                                     if sha(candidate) == file_record['sha256']), None)
                    if matching is not None:
                        expected = matching
                        location = 'identical_member_bytes_at_other_corpus_path'
                file_record['originalExists'] = expected.is_file()
                if expected.is_file():
                    file_record['comparisonLocation'] = location
                    file_record['originalPath'] = str(expected.relative_to(args.compare_root))
                    file_record['originalSha256'] = sha(expected)
                    same_bytes = file_record['sha256'] == file_record['originalSha256']
                    comparison['nativeBytesMatch' if file_record['nativeExtracted'] and same_bytes else
                               'convertedBytesMatch' if same_bytes else 'bytesDiffer'] += 1
                    if path.suffix.lower() in ('.doc', '.docx'):
                        a, b = clause.read_form(str(expected)), clause.read_form(str(path))
                        for value in (a, b):
                            value.pop('path', None)
                            value.pop('sha1', None)
                        file_record['clauseReaderExact'] = a == b
                        comparison['clauseReaderMatch' if a == b else 'clauseReaderDiffers'] += 1
                        file_record['clauseFormNameInput'] = bool(clause.TDOC.search(path.name))
                        if file_record['clauseFormNameInput']:
                            comparison['clauseFormReaderMatch' if a == b else 'clauseFormReaderDiffers'] += 1
                        a, b = pack.read_cover(expected), pack.read_cover(path)
                        file_record['packReaderExact'] = exporter_canonical(a) == exporter_canonical(b)
                        comparison['packReaderMatch' if file_record['packReaderExact'] else 'packReaderDiffers'] += 1
                        file_record['packCoverInput'] = bool(re.fullmatch(
                            pack.COVER_NAME.format(pack=re.escape(relative.stem)), path.name, re.I))
                        if file_record['packCoverInput']:
                            comparison['packCoverReaderMatch' if file_record['packReaderExact'] else 'packCoverReaderDiffers'] += 1
                    if not same_bytes:
                        mismatches.append(str(relative_file))
                else:
                    comparison['originalPathAbsent'] += 1
            file_receipts.append(file_record)
        records.append({'archiveSha256': row['sha256'], 'archivePath': str(relative), 'acquisitionMode': mode,
                        'originalNativeDirectoryError': row.get('archiveDirectoryError'),
                        'extractionStatus': [[status, str(path.relative_to(scratch))] for status, path in statuses],
                        'conversion': conversion, 'comparison': dict(comparison), 'byteMismatches': mismatches,
                        'files': file_receipts})
        if args.limit and len(records) >= args.limit:
            break
    totals = collections.Counter()
    for record in records:
        totals.update(record['comparison'])
    write(args.receipt, {'inventorySha256': ARCHIVES_SHA, 'extractorSha256': sha(extractor_path),
                        'converterSha256': sha(converter_path), 'metadataExporterSha256': EXPORTER_SHA,
                        'archivePlacements': len(records), 'distinctArchiveHashes': len({r['archiveSha256'] for r in records}),
                        'selectedHashCount': len(chosen) if chosen is not None else None,
                        'elapsedSeconds': time.monotonic() - start, 'counts': dict(totals), 'records': records,
                        'condition': 'Original native recursive extraction; original conversion when --convert is selected',
                        'constructorScope': args.scope,
                        'fullInventoryProcessed': chosen is None and not args.limit and args.scope == 'all' and len(records) == 111299,
                        'fullCorpusRestorationCertified': False,
                        'certificationCondition': 'Compare complete derived inventory and all census outputs after full reconstruction'})
    print(json.dumps({'archives': len(records), 'counts': dict(totals), 'elapsedSeconds': time.monotonic() - start}))
    if (any(result.get('success') is False for record in records for result in record['conversion'])
            or any(status in ('bad_zip', 'error') for record in records
                   for status, _ in record['extractionStatus'])):
        raise SystemExit(1)


def exporter_canonical(value):
    if isinstance(value, dict):
        return {str(k): exporter_canonical(v) for k, v in value.items()}
    if isinstance(value, set):
        return sorted((exporter_canonical(v) for v in value), key=lambda x: json.dumps(x, sort_keys=True))
    if isinstance(value, (list, tuple)):
        return [exporter_canonical(v) for v in value]
    return value


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='command', required=True)
    st = sub.add_parser('stage')
    st.add_argument('--artifact', type=Path, required=True)
    st.add_argument('--release', type=Path, required=True)
    st.add_argument('--destination', type=Path, required=True)
    st.add_argument('--local-source-root', type=Path)
    st.add_argument('--source-mode', choices=('local_original_read_only_inputs', 'archive_reconstructed'),
                    default='local_original_read_only_inputs')
    st.add_argument('--receipt', type=Path, required=True)
    st.set_defaults(run=stage)
    au = sub.add_parser('audit')
    au.add_argument('--stage', type=Path, required=True)
    au.add_argument('--artifact', type=Path, required=True)
    au.add_argument('--reference', type=Path, required=True)
    au.add_argument('--out', type=Path, required=True)
    au.add_argument('--wg', nargs='+', choices=WGS, default=list(WGS))
    au.add_argument('--audits', nargs='+', choices=('pack', 'clause'), default=['pack', 'clause'])
    au.add_argument('--workers', type=int, default=1)
    au.add_argument('--source-mode', choices=('local_original_read_only_inputs', 'archive_reconstructed'), required=True)
    au.set_defaults(run=audit)
    ve = sub.add_parser('verify-sources')
    ve.add_argument('--inventory', type=Path, required=True)
    ve.add_argument('--source-root', type=Path, required=True)
    ve.add_argument('--receipt', type=Path, required=True)
    ve.set_defaults(run=verify_sources)
    fr = sub.add_parser('derived-frontier')
    fr.add_argument('--root', type=Path, required=True)
    fr.add_argument('--frontier', type=Path, required=True)
    fr.add_argument('--receipt', type=Path, required=True)
    fr.set_defaults(run=derived_frontier)
    vd = sub.add_parser('verify-derived')
    vd.add_argument('--root', type=Path, required=True)
    vd.add_argument('--frontier', type=Path, required=True)
    vd.add_argument('--frontier-receipt', type=Path, required=True)
    vd.add_argument('--receipt', type=Path, required=True)
    vd.set_defaults(run=verify_derived)
    bu = sub.add_parser('bundle-code')
    bu.add_argument('--root', type=Path, required=True)
    bu.add_argument('--destination', type=Path, required=True)
    bu.add_argument('--receipt', type=Path, required=True)
    bu.set_defaults(run=bundle_code)
    pl = sub.add_parser('stage-plenary-sources')
    pl.add_argument('--frontier', type=Path, required=True)
    pl.add_argument('--frontier-sha256', required=True)
    pl.add_argument('--cache', type=Path)
    pl.add_argument('--local-source-root', type=Path)
    pl.add_argument('--destination', type=Path, required=True)
    pl.add_argument('--receipt', type=Path, required=True)
    pl.add_argument('--limit', type=int)
    pl.set_defaults(run=stage_plenary_sources)
    re = sub.add_parser('reconstruct')
    re.add_argument('--inventory', type=Path, required=True)
    re.add_argument('--code-root', type=Path, default=Path.cwd())
    re.add_argument('--cache', type=Path, required=True)
    re.add_argument('--destination', type=Path, required=True)
    re.add_argument('--receipt', type=Path, required=True)
    re.add_argument('--local-source-root', type=Path)
    re.add_argument('--compare-root', type=Path)
    re.add_argument('--selection', type=Path, help='Explicit matches[].sha256 selection; omit for full inventory')
    re.add_argument('--scope', choices=('audit', 'all'), default='audit',
                    help='Original CR constructor selects TSG pack archives; all additionally reconstructs wg_docs')
    re.add_argument('--limit', type=int)
    re.add_argument('--offline', action='store_true')
    re.add_argument('--convert', action='store_true')
    re.set_defaults(run=reconstruct)
    args = ap.parse_args()
    guard()
    args.run(args)


if __name__ == '__main__':
    main()
