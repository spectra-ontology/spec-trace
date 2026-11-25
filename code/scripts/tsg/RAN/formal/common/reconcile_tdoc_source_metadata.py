#!/usr/bin/env python3
"""reconcile_tdoc_source_metadata.py — guarded source identity projection across document views.

Spec: Phase-1 source identity ledgers and Phase-4/6/8 maintained projections.
Ontology: one source-owned CR identity; exact document and section provenance.
Cycle: validate original evidence → inventory/full preimages → metadata-only updates → readback.
배경: spreadsheet and registry identity corrections must reach existing parsed/search artifacts.
사용: --out retained-receipt.json [--apply]; default inventories the retained views.
LLM 호출: none. Existing vectors and source bodies are preserved; no embedding calls.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

import json_stream
from tdoc_source_supplements import source_inputs
from tdoc_source_identity_corrections import source_inputs as correction_inputs
from tdoc_source_classification import source_inputs as classification_inputs
from tdoc_native_cr_sources import source_inputs as native_source_inputs
from tdoc_source_classification import target_selection
from tdoc_source_metadata import identity_fields, overlay_chunk, phase4_sources
from document_decision_storage import durable_json

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
sys.path.insert(0, str(ROOT / 'scripts/common'))
from common.atomic_io import write_text_atomic
from common.exception_notes import add_exception_note
from common.service_endpoints import QDRANT_URL
from common import review_artifacts
from qdrant_client import QdrantClient, models


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(1 << 20), b''): h.update(part)
    return h.hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def read_json_pinned(path):
    original = path.read_bytes()
    return json.loads(original), hashlib.sha256(original).hexdigest()


def load_module(path):
    spec = importlib.util.spec_from_file_location('_source_metadata_phase4', path)
    module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def phase4_parser_path(wg):
    paths = list((ROOT / f'scripts/tsg/RAN/formal/{wg}/phase-4/cr-parser').glob('*_parse_cr_documents.py'))
    if len(paths) != 1:
        raise ValueError('Expected one maintained Phase-4 CR document parser: ' + wg)
    return paths[0]


def phase4_projection(wg, selected_targets=None, *, input_fences=None):
    path = ROOT / f'ontology/output/tsg/RAN/formal/parsed_cr/{wg}/cr_documents.json'
    data, source_sha = read_json_pinned(path)
    if input_fences is not None:
        input_fences[path] = source_sha
    before = copy.deepcopy(data)
    parser = load_module(phase4_parser_path(wg))
    records = [SimpleNamespace(**r) for r in data['documents']]
    projection = phase4_sources(parser, records, selected_targets=selected_targets,
        progress=lambda count: print(json.dumps({'stage': 'phase4_native_parsed', 'documents': count}), flush=True))
    by_target = {r.tdoc_number: r for r in records}
    old_ids = [r['tdoc_number'] for r in before['documents']]
    added = sorted(set(by_target) - set(old_ids))
    documents = []
    for target in old_ids + added:
        record = by_target[target]
        documents.append(vars(record) if isinstance(record, SimpleNamespace) else parser.cr_record(record))
    data['documents'] = documents
    meta = data['metadata']
    meta['unique_crs'] = len(documents)
    meta['total_cr_docs_found'] += len(added)
    attrs = {'reasonForChange': 'reason_for_change', 'summaryOfChange': 'summary_of_change',
      'consequencesIfNotApproved': 'consequences_if_not_approved', 'clausesAffected': 'clauses_affected'}
    meta['field_coverage'] = {k: sum(bool(r.get(v)) for r in documents) for k, v in attrs.items()}
    meta['field_coverage']['crossSpecAffects'] = sum(bool(r.get('affects_core_spec') or r.get('affects_test_spec') or r.get('affects_om_spec')) for r in documents)
    if added or projection['identityCorrections'] or 'source_identity_projection' not in meta:
        previous = meta.get('source_identity_projection', {})
        projection['sourceSupplements'] = sorted(set(previous.get('sourceSupplements', [])) | set(projection['sourceSupplements']))
        projection['sourceClassifications'] = sorted(set(previous.get('sourceClassifications', [])) | set(projection['sourceClassifications']))
        projection['sourceNativeBodies'] = sorted(set(previous.get('sourceNativeBodies', [])) | set(projection.get('sourceNativeBodies', [])))
        projection['identityCorrections'] = {**previous.get('identityCorrections', {}), **projection['identityCorrections']}
        meta['source_identity_projection'] = projection
    # Every original body and unreviewed field must remain exactly represented.
    permitted = {'spec_number', 'release', 'cr_number', 'rev', 'category'}
    original = {r['tdoc_number']: r for r in before['documents']}
    for record in documents:
        if record['tdoc_number'] in original:
            old = original[record['tdoc_number']]
            if {k: v for k, v in record.items() if k not in permitted} != {k: v for k, v in old.items() if k not in permitted}:
                raise ValueError('Phase-4 unrelated field or body changed')
    return path, before, data, added, projection


def backup(path, directory):
    out = directory / (hashlib.sha256(str(path.relative_to(ROOT)).encode()).hexdigest() + '.gz')
    with path.open('rb') as src, gzip.open(out, 'xb') as dst: shutil.copyfileobj(src, dst)
    with out.open('rb') as stream: os.fsync(stream.fileno())
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path),
            'backup': out.relative_to(ROOT).as_posix(), 'backupSha256': sha(out)}


def project_cr_file(path, fields, output=None):
    """Stream every original JSON value, preserving unknown top-level keys and row order."""
    counts = Counter(); changed = []; expected = hashlib.sha256(); top = hashlib.sha256()
    writer = output.open('w', encoding='utf-8') if output is not None else None
    try:
        with path.open(encoding='utf-8') as stream:
            reader = json_stream._Reader(stream); reader.expect('{')
            if writer: writer.write('{')
            first = True; found = False; seen = set()
            while reader.peek() != '}':
                if not first: reader.expect(',')
                key = reader.value(); reader.expect(':')
                if not isinstance(key, str): raise ValueError('Artifact top-level key must be a string')
                if key in seen: raise ValueError('Duplicate artifact top-level key')
                seen.add(key)
                if writer:
                    if not first: writer.write(',')
                    json.dump(key, writer); writer.write(':')
                first = False
                if key != 'chunks':
                    value = reader.value(); top.update(canonical([key, value]))
                    if writer: json.dump(value, writer, ensure_ascii=False, separators=(',', ':'))
                    continue
                found = True; reader.expect('[')
                if writer: writer.write('[\n')
                row_first = True
                while reader.peek() != ']':
                    if not row_first: reader.expect(',')
                    original = reader.value(); target = original.get('tdocNumber')
                    after = overlay_chunk(original, fields[target]) if target in fields else original
                    if target in fields:
                        counts[target] += 1
                        if 'sectionChunkIds' in original:
                            # Opaque TS vector keys need a source-backed resolver;
                            # never manufacture a different UUID by changing its text.
                            if original['sectionChunkIds'] and 'spec_number' in fields[target]:
                                raise ValueError('An opaque sectionChunkIds binding requires explicit source re-resolution')
                    if after != original:
                        changed.append({'chunkId': original['chunkId'], 'target': target,
                          'fields': {k: [original.get(k), v] for k, v in after.items() if original.get(k) != v}})
                    if after.get('text') != original.get('text') or after.get('chunkId') != original.get('chunkId'):
                        raise ValueError('Artifact body or chunk identity changed')
                    expected.update(canonical(after)); expected.update(b'\n')
                    if writer:
                        if not row_first: writer.write(',\n')
                        json.dump(after, writer, ensure_ascii=False, separators=(',', ':'))
                    row_first = False
                reader.expect(']')
                if writer: writer.write(']')
            reader.expect('}')
            if reader.peek() or not found: raise ValueError('Incomplete CR artifact')
            if writer:
                writer.write('}\n'); writer.flush(); os.fsync(writer.fileno())
    finally:
        if writer: writer.close()
    return {'targetCounts': dict(counts), 'changed': changed, 'allProjectedRowsSha256': expected.hexdigest(), 'unknownTopLevelValuesSha256': top.hexdigest()}


def full_points(client, collection, targets):
    if not targets:
        return []
    points = []; offset = None
    seen_offsets = set()
    condition = models.Filter(must=[models.FieldCondition(key='tdocNumber', match=models.MatchAny(any=sorted(targets)))])
    while True:
        page, offset = client.scroll(collection, scroll_filter=condition, offset=offset, limit=128, with_payload=True, with_vectors=True)
        points.extend({'id': p.id, 'payload': p.payload, 'vector': p.vector} for p in page)
        if offset is None: break
        if offset in seen_offsets:
            raise ValueError('Repeated Qdrant scroll offset: ' + repr(offset))
        seen_offsets.add(offset)
    return sorted(points, key=lambda p: str(p['id']))


def source_fence(fences):
    for relative, expected in fences.items():
        try:
            review_artifacts.resolve_recorded_path(ROOT, relative, expected)
        except (OSError, ValueError) as error:
            raise ValueError('Source/producer SHA fence changed: ' + relative) from error


def remaining_payload_groups(before, current, changes):
    """Accept only original or exactly intended full points after a lost ACK."""
    old = {p['id']: p for p in before}; got = {p['id']: p for p in current}
    if len(old) != len(before) or len(got) != len(current) or set(old) != set(got):
        raise ValueError('Interrupted metadata point identities changed')
    updates = {p['id']: p for p in changes}
    groups = {}
    for pid, point in got.items():
        desired = updates[pid]['afterPayload'] if pid in updates else old[pid]['payload']
        if point['vector'] != old[pid]['vector'] or point['payload'] not in (old[pid]['payload'], desired):
            raise ValueError('Interrupted metadata full preimage has an unrelated change')
        if point['payload'] != desired:
            delta = updates[pid]['delta']; key = canonical(delta)
            groups.setdefault(key, {'delta': delta, 'ids': []})['ids'].append(pid)
    return list(groups.values())


def resume_projection(args):
    inventory = json.loads(args.out.read_text())
    if inventory['wg'] != args.wg or inventory['mode'] not in {'applying', 'applied_exact_readback'}:
        raise ValueError('Resume requires an applying or exactly completed metadata journal')
    relative = Path(__file__).relative_to(ROOT).as_posix()
    fences = dict(inventory['sourceFences'])
    # The retained generation hash remains in sourceFences. The new recovery
    # entry point independently guards its own code and changes no proposal.
    previous_contract = fences.pop(relative)
    current_contract = sha(Path(__file__))
    if inventory.get('resumeContractSha256', current_contract) != current_contract:
        raise ValueError('The recorded resume contract changed')
    inventory['resumeContractSha256'] = current_contract
    inventory['generationContractSha256'] = previous_contract
    source_fence(fences)
    for path, info in inventory['files'].items():
        if not info.get('afterSha256'):
            raise ValueError('Resume requires completed, unchanged artifact projections')
        try:
            review_artifacts.resolve_recorded_path(ROOT, path, info['afterSha256'])
        except (OSError, ValueError) as error:
            raise ValueError('Resume requires completed, unchanged artifact projections') from error
    crpath = ROOT / f'vectordb/parsed/cr/{args.wg}/{args.wg.lower()}_cr_chunks.json'
    if inventory['phase8Artifact']['changed'] and sha(crpath) != inventory['phase8Artifact']['afterSha256']:
        raise ValueError('Interrupted canonical CR artifact changed')
    try:
        backup = review_artifacts.resolve_recorded_path(ROOT, inventory['pointPreimage']['path'],
                                                        inventory['pointPreimage']['sha256'])
    except (OSError, ValueError) as error:
        raise ValueError('Interrupted full point preimage bytes changed') from error
    before = json.loads(gzip.decompress(backup.read_bytes()))
    client = QdrantClient(url=QDRANT_URL, timeout=120)
    try:
        targets = set(inventory['fields'])
        inventory['resumeAttempts'] = inventory.get('resumeAttempts', 0) + 1
        durable_json(args.out, inventory)
        for name, info in inventory['collections'].items():
            current = full_points(client, name, targets)
            groups = remaining_payload_groups(before[name], current, info['updates'])
            source_fence(fences)
            for group in groups:
                client.set_payload(name, group['delta'], group['ids'], wait=True)
            got = full_points(client, name, targets)
            if remaining_payload_groups(before[name], got, info['updates']):
                raise ValueError('Interrupted metadata desired readback incomplete')
            info['afterCount'] = client.count(name, exact=True).count
            if info['afterCount'] != info['beforeCount']:
                raise ValueError('Interrupted metadata collection cardinality changed')
            info['afterSha256'] = digest(got)
            if name not in inventory['appliedCollections']: inventory['appliedCollections'].append(name)
            inventory.setdefault('resumePayloadGroups', {})[name] = len(groups)
            source_fence(fences); durable_json(args.out, inventory)
        source_fence(fences)
        inventory.update(mode='applied_exact_readback', bodyIdentityVectorOrUnknownFieldChanges=0,
            phase4DocumentsAfterSha256=sha(ROOT / f'ontology/output/tsg/RAN/formal/parsed_cr/{args.wg}/cr_documents.json'))
        durable_json(args.out, inventory)
        print(json.dumps(dict(mode=inventory['mode'], resumedPayloadGroups=inventory['resumePayloadGroups'])))
    finally:
        primary_error = sys.exc_info()[1]
        try:
            client.close()
        except BaseException as close_error:
            if primary_error is None:
                raise
            add_exception_note(primary_error, f'Qdrant client close also failed: {type(close_error).__name__}: {close_error}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wg', default='RAN5', choices=['RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'])
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--resume', action='store_true', help='Guarded recovery of an existing metadata-only point journal')
    parser.add_argument('--targets-file', type=Path, help='Retained JSON array defining an incremental document scope')
    args = parser.parse_args(); args.out = args.out.resolve()
    if not args.out.is_relative_to(ROOT): parser.error('Retain the receipt inside the repository')
    if args.resume:
        if not args.apply or not args.out.exists(): parser.error('Resume requires --apply and an existing retained journal')
        resume_projection(args); return
    if args.out.exists(): parser.error('Use a new retained receipt path inside the repository')
    if args.apply and args.out.with_suffix('').exists():
        parser.error('Use a new receipt path; its preparation directory already exists')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    selected, selected_fences = target_selection(ROOT, args.wg, args.targets_file) if args.targets_file else (None, {})
    fields = identity_fields(ROOT, args.wg, selected); targets = set(fields)
    # A retained native source can supply a missing parsed/body view while its
    # registered metadata remains outside this reconciliation's write scope.
    from tdoc_native_cr_sources import validated_native_sources
    native_targets = {r['target'] for r in validated_native_sources(ROOT, args.wg, selected_targets=selected)}
    print(json.dumps({'stage': 'native_sources_validated', 'documents': len(native_targets)}), flush=True)
    body_only_targets = native_targets - targets
    if selected is not None and targets | native_targets != set(selected):
        raise ValueError('Selected document lacks a verified metadata or native source identity')
    fences = source_inputs(ROOT, args.wg, None); fences.update(correction_inputs(ROOT, args.wg, None))
    fences.update(classification_inputs(ROOT, args.wg, None, selected_targets=selected)); fences.update(selected_fences)
    fences.update(native_source_inputs(ROOT, args.wg, selected_targets=selected))
    for relative in [Path(__file__).relative_to(ROOT), Path(review_artifacts.__file__).relative_to(ROOT),
      *[Path(__file__).with_name(name).relative_to(ROOT) for name in
        ('tdoc_source_metadata.py', 'tdoc_source_identity_corrections.py', 'tdoc_native_cr_sources.py', 'tdoc_source_supplements.py',
         'tdoc_source_classification.py', 'tdoc_classification_views.py', 'json_stream.py', 'document_decision_storage.py',
         'document_decision_source.py', 'native_word_conversion.py', 'cr_form.py', 'docx_text.py',
         'cr_form_slot.py', 'cr_word_title.py')],
      Path(f'ontology/output/tsg/RAN/formal/instances/phase-1/{args.wg}/meetings.jsonld'),
      phase4_parser_path(args.wg).relative_to(ROOT),
      Path(f'scripts/tsg/RAN/formal/{args.wg}/phase-8/cr-parser/01_parse_cr_chunks.py')]: fences[relative.as_posix()] = sha(ROOT / relative)
    parsed_fences = {}
    p4path, p4before, p4after, added, projection = phase4_projection(args.wg, selected, input_fences=parsed_fences)
    files = {p4path: {'beforeSha256': parsed_fences[p4path], 'after': p4after}}
    summary_path = p4path.with_name('parse_summary.json')
    if summary_path.exists():
        summary, summary_sha = read_json_pinned(summary_path)
        before = copy.deepcopy(summary)
        summary['unique_crs'] = len(p4after['documents']); summary['total_files_found'] += len(added)
        summary['field_coverage'] = p4after['metadata']['field_coverage']
        summary['release_stats'] = dict(sorted(Counter(r['release'] for r in p4after['documents']).items()))
        summary['source_identity_projection'] = p4after['metadata']['source_identity_projection']
        if before != summary: files[summary_path] = {'beforeSha256': summary_sha, 'after': summary}
    tdoc_inventory = {}; tdoc_base = ROOT / f'vectordb/parsed/tdocs/{args.wg}'
    for target in sorted(targets):
        paths = list(tdoc_base.glob(f'*/{target}/chunks.json'))
        tdoc_inventory[target] = [p.relative_to(ROOT).as_posix() for p in paths]
        if len(paths) > 1: raise ValueError('Ambiguous document artifact owner: ' + target)
        for path in paths:
            before, source_sha = read_json_pinned(path)
            after = copy.deepcopy(before)
            if 'release' in fields[target]: after['metadata']['release'] = fields[target]['release']
            if 'document_type' in fields[target]: after['metadata']['type'] = fields[target]['document_type']
            if after != before: files[path] = {'beforeSha256': source_sha, 'after': after}
    crpath = ROOT / f'vectordb/parsed/cr/{args.wg}/{args.wg.lower()}_cr_chunks.json'
    crsha = sha(crpath); crprojection = project_cr_file(crpath, fields)
    client = QdrantClient(url=QDRANT_URL, timeout=120)
    try:
        collections = {}; point_preimages = {}
        for name in [args.wg.lower() + '_tdoc_chunks', args.wg.lower() + '_cr_chunks']:
            points = full_points(client, name, targets) if targets else []
            point_preimages[name] = points
            updates = []
            for point in points:
                payload = point['payload']; after = overlay_chunk(payload, fields[payload['tdocNumber']], tdoc=name.endswith('_tdoc_chunks'))
                if payload != after:
                    updates.append({'id': point['id'], 'beforeSha256': digest(point), 'afterPayload': after,
                      'delta': {k: v for k, v in after.items() if payload.get(k) != v}})
            collections[name] = {'matched': len(points), 'byTarget': dict(Counter(p['payload']['tdocNumber'] for p in points)),
              'updates': updates, 'preimageSha256': digest(points), 'beforeCount': client.count(name, exact=True).count}
        inventory = {'mode': 'read_only_inventory', 'wg': args.wg, 'fields': fields,
          'sourceBodyOnlyTargets': sorted(body_only_targets), 'sourceFences': fences,
          'phase4': {'before': len(p4before['documents']), 'after': len(p4after['documents']), 'sourceSupplementsAdded': added,
            'projection': projection, 'existingCorrectionTargets': sorted(targets & {r['tdoc_number'] for r in p4before['documents']})},
          'phase6Artifacts': tdoc_inventory, 'phase8Artifact': crprojection, 'collections': collections,
          'files': {p.relative_to(ROOT).as_posix(): {'beforeSha256': v['beforeSha256']} for p, v in files.items()}}
        if not args.apply:
            durable_json(args.out, inventory); print(json.dumps({'mode': inventory['mode'], 'phase4': inventory['phase4'], 'collections': {n: {'matched': v['matched'], 'updates': len(v['updates'])} for n, v in collections.items()}}, ensure_ascii=False)); return
        run_dir = args.out.with_suffix(''); run_dir.mkdir()
        source_fence(fences)
        for p, value in files.items():
            if sha(p) != value['beforeSha256']: raise ValueError('Artifact changed before durable backup')
            value['preimage'] = backup(p, run_dir)
        if crprojection['changed']:
            crbackup = backup(crpath, run_dir)
            crtemp = run_dir / 'cr_chunks.projected.json'
            generated = project_cr_file(crpath, fields, crtemp)
            if generated != crprojection or sha(crpath) != crsha: raise ValueError('CR artifact changed during projection')
            inventory['phase8Artifact']['preimage'] = crbackup
            inventory['phase8Artifact']['afterSha256'] = sha(crtemp)
        else: crtemp = None
        point_backup = run_dir / 'qdrant_full_preimages.json.gz'
        with gzip.open(point_backup, 'xb') as stream: stream.write(canonical(point_preimages))
        with point_backup.open('rb') as stream: os.fsync(stream.fileno())
        inventory['pointPreimage'] = {'path': point_backup.relative_to(ROOT).as_posix(), 'sha256': sha(point_backup)}
        inventory['files'] = {p.relative_to(ROOT).as_posix(): {'beforeSha256': v['beforeSha256'], 'preimage': v['preimage']} for p, v in files.items()}
        inventory['mode'] = 'prepared_with_full_preimages'; durable_json(args.out, inventory)
        # Every source/artifact/whole matching point is fenced immediately before the
        # first write. Partial distributed progress remains explicit in the journal.
        source_fence(fences)
        for p, value in files.items():
            if sha(p) != value['beforeSha256']: raise ValueError('Artifact changed before apply')
        if sha(crpath) != crsha: raise ValueError('CR artifact changed before apply')
        for name, points in point_preimages.items():
            if digest(full_points(client, name, targets) if targets else []) != digest(points):
                raise ValueError('Full payload/vector preimage changed')
        inventory['mode'] = 'applying'; inventory['appliedFiles'] = []; inventory['appliedCollections'] = []; durable_json(args.out, inventory)
        for path, value in files.items():
            encoded = json.dumps(value['after'], ensure_ascii=False, indent=2) + '\n'
            write_text_atomic(path, encoded)
            if json.loads(path.read_text()) != value['after']: raise ValueError('Artifact exact readback failed')
            inventory['files'][path.relative_to(ROOT).as_posix()]['afterSha256'] = sha(path)
            inventory['appliedFiles'].append(path.relative_to(ROOT).as_posix()); durable_json(args.out, inventory)
        if crtemp:
            os.replace(crtemp, crpath)
            directory = os.open(crpath.parent, os.O_RDONLY)
            try: os.fsync(directory)
            finally: os.close(directory)
            if sha(crpath) != inventory['phase8Artifact']['afterSha256']: raise ValueError('CR artifact file SHA readback failed')
            readback = project_cr_file(crpath, fields)
            if readback['changed'] or readback['allProjectedRowsSha256'] != crprojection['allProjectedRowsSha256'] or readback['unknownTopLevelValuesSha256'] != crprojection['unknownTopLevelValuesSha256']:
                raise ValueError('Full CR artifact metadata/body/unknown value readback failed')
            inventory['appliedFiles'].append(crpath.relative_to(ROOT).as_posix()); durable_json(args.out, inventory)
        for name, info in collections.items():
            groups = remaining_payload_groups(point_preimages[name], point_preimages[name], info['updates'])
            for group in groups:
                source_fence(fences)
                client.set_payload(name, group['delta'], group['ids'], wait=True)
            info['appliedPayloadGroups'] = len(groups)
            got = full_points(client, name, targets) if targets else []
            old_by_id = {p['id']: p for p in point_preimages[name]}
            updates = {p['id']: p['afterPayload'] for p in info['updates']}
            if len(got) != len(old_by_id): raise ValueError('Matching point set changed during apply')
            for point in got:
                old = old_by_id[point['id']]
                if point['vector'] != old['vector'] or point['payload'] != updates.get(point['id'], old['payload']):
                    raise ValueError('Exact payload/vector readback failed')
            info['afterCount'] = client.count(name, exact=True).count
            if info['afterCount'] != info['beforeCount']: raise ValueError('Collection cardinality changed during metadata apply')
            info['afterSha256'] = digest(got)
            inventory['appliedCollections'].append(name); durable_json(args.out, inventory)
        source_fence(fences)
        inventory.update(mode='applied_exact_readback', bodyIdentityVectorOrUnknownFieldChanges=0,
            phase4DocumentsAfterSha256=sha(p4path))
        durable_json(args.out, inventory)
        print(json.dumps({'mode': inventory['mode'], 'phase4Added': added,
          'files': len(files), 'phase8ChangedChunks': len(crprojection['changed']),
          'collections': {n: {'matched': v['matched'], 'updates': len(v['updates'])} for n, v in collections.items()}}, ensure_ascii=False))
    finally:
        primary_error = sys.exc_info()[1]
        try:
            client.close()
        except BaseException as close_error:
            if primary_error is None:
                raise
            add_exception_note(primary_error, f'Qdrant client close also failed: {type(close_error).__name__}: {close_error}')


if __name__ == '__main__': main()
