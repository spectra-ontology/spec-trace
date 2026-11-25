#!/usr/bin/env python3
"""reconcile_tdoc_classified_views.py — source-owned CR body recovery.

Spec: Phase-4 actual CR parser and Phase-8 native CR chunk/embedding contracts.
Ontology: numbered source document identity; body provenance independent of disposition.
Cycle: validated classification → ordinary source chunker → prepared payloads → guarded append/readback.
배경: generic reservation classes can omit existing source CR bodies from retrieval.
사용: --wg RAN4 --out retained-receipt.json; repeat with --apply after preparing.
LLM 호출: none. New vectors use the pinned local collection encoder only.
"""
from __future__ import annotations
import argparse
from collections import Counter
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
sys.path.insert(0, str(ROOT / 'scripts/common'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import review_artifacts
from common.service_endpoints import QDRANT_URL
from common.exception_notes import add_exception_note
from common.embedding_registry import encoder_for, embed_local, force_hf_offline
from common.gpu_duty import rested
from common.resolution_vectors import valid_vector
from document_decision_storage import durable_json
from json_stream import iter_array
from qdrant_client import QdrantClient, models
from tdoc_source_classification import source_inputs, ledger_path, target_selection
from tdoc_source_identity_corrections import source_inputs as correction_inputs
from tdoc_native_cr_sources import source_inputs as native_source_inputs
from tdoc_classification_views import phase8_classified_chunks, source_body_rows
from tdoc_supplement_vectors import append_cr_artifact, load_module, sha


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def durable_blob(path, value):
    with path.open('xb') as stream:
        stream.write(value); stream.flush(); os.fsync(stream.fileno())
    fd = os.open(path.parent, os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)


def check_fence(fences):
    for relative, expected in fences.items():
        try:
            review_artifacts.resolve_recorded_path(ROOT, relative, expected)
        except (OSError, ValueError) as error:
            raise RuntimeError('Prepared source or maintained contract changed: ' + relative) from error


def points_for(client, collection, targets):
    result, offset = {}, None
    seen_offsets = set()
    condition = models.Filter(must=[models.FieldCondition(key='tdocNumber', match=models.MatchAny(any=sorted(targets)))])
    while True:
        points, offset = client.scroll(collection, scroll_filter=condition, offset=offset, limit=128,
                                       with_payload=True, with_vectors=True)
        for point in points:
            if point.id in result:
                raise RuntimeError('Duplicate source point')
            result[point.id] = dict(id=point.id, payload=point.payload, vector=point.vector)
        if offset is None:
            return result
        if offset in seen_offsets:
            raise RuntimeError('Repeated Qdrant scroll offset: ' + repr(offset))
        seen_offsets.add(offset)


def validate_new_points(expected, actual):
    # An occupied body is retained verbatim; a different source generation needs
    # its own review rather than an implicit overwrite of bytes or vectors.
    for pid, point in actual.items():
        if pid not in expected or point['payload'] != expected[pid]:
            raise RuntimeError('Occupied CR source projection differs: ' + str(pid))
    return {pid: payload for pid, payload in expected.items() if pid not in actual}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wg', required=True, choices=['RAN2', 'RAN3', 'RAN4', 'RAN5'])
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--targets-file', type=Path, help='Retained JSON array defining an incremental document scope')
    args = parser.parse_args(); args.out = args.out.resolve()
    if not args.out.is_relative_to(ROOT):
        parser.error('Retain the journal within the repository')
    run_dir = args.out.with_suffix('')
    collection = args.wg.lower() + '_cr_chunks'
    artifact = ROOT / f'vectordb/parsed/cr/{args.wg}/{collection}.json'
    client = QdrantClient(url=QDRANT_URL, timeout=120)
    try:
        encoder = encoder_for(collection)
        config = client.get_collection(collection).config.params.vectors
        if config.size != encoder.dim or str(config.distance).casefold() != 'cosine':
            raise ValueError('Source body collection encoder/distance mismatch')
        if args.out.exists():
            report = json.loads(args.out.read_text())
            if report['status'] == 'complete':
                check_fence(report['sourceFiles'])
                try:
                    payload_path = review_artifacts.resolve_recorded_path(ROOT, report['preparedPayloads']['path'],
                                                                          report['preparedPayloads']['sha256'])
                except (OSError, ValueError) as error:
                    raise ValueError('Prepared body payload bytes changed') from error
                expected = {int(k): v for k, v in json.loads(gzip.decompress(payload_path.read_bytes())).items()}
                current = points_for(client, collection, report['targets'])
                if set(current) != set(expected) or validate_new_points(expected, current):
                    raise RuntimeError('Completed source body readback differs')
                if digest(current) != report['finalPointsSha256'] or sha(artifact) != report['artifactAfterSha256']:
                    raise RuntimeError('Completed source body/vector or artifact bytes changed')
                print(json.dumps(dict(status='already_complete', points=len(current)))); return
            if report['status'] != 'prepared' or not args.apply:
                parser.error('Use a new retained receipt path, or apply a prepared plan')
        else:
            if args.apply:
                parser.error('Prepare the source bodies before applying')
            # Check the maintained cover projection before the larger native-source
            # population, so a changed extraction contract fails before that work.
            from tdoc_body_source_metadata import source_inputs as body_source_inputs
            body_fences = body_source_inputs(ROOT, args.wg)
            selected, selection_fences = target_selection(ROOT, args.wg, args.targets_file) if args.targets_file else (None, {})
            rows = source_body_rows(ROOT, args.wg, selected_targets=selected)
            if selected is not None and {r['target'] for r in rows} != set(selected):
                raise ValueError('Selected source body input is absent')
            fences = source_inputs(ROOT, args.wg, None, selected_targets=selected); fences.update(selection_fences)
            fences.update(correction_inputs(ROOT, args.wg, None))
            fences.update(native_source_inputs(ROOT, args.wg, selected_targets=selected))
            fences.update(body_fences)
            p4path = ROOT / f'ontology/output/tsg/RAN/formal/parsed_cr/{args.wg}/cr_documents.json'
            files = [Path(__file__), Path(__file__).with_name('tdoc_classification_views.py'),
                Path(__file__).with_name('tdoc_source_classification.py'), Path(__file__).with_name('tdoc_supplement_vectors.py'),
                ROOT / f'scripts/tsg/RAN/formal/{args.wg}/phase-8/cr-parser/01_parse_cr_chunks.py',
                ROOT / f'scripts/tsg/RAN/formal/{args.wg}/phase-8/qdrant/01_load_qdrant.py', p4path,
                ROOT / f'ontology/output/tsg/RAN/formal/instances/phase-1/{args.wg}/tdocs.jsonld',
                ROOT / 'scripts/common/common/embedding_registry.py', ROOT / 'scripts/common/common/local_model.py',
                Path(review_artifacts.__file__)]
            files.extend(Path(__file__).with_name(name) for name in
                ('tdoc_native_cr_sources.py', 'tdoc_source_identity_corrections.py', 'tdoc_source_metadata.py',
                 'document_decision_source.py', 'document_decision_storage.py', 'cr_form.py', 'docx_text.py',
                 'native_word_conversion.py', 'tdoc_body_source_metadata.py'))
            fences.update({p.relative_to(ROOT).as_posix(): sha(p) for p in files})
            original_sha = sha(artifact)
            occupied_targets = {c['tdocNumber'] for c in iter_array(artifact, 'chunks')}
            missing = [r for r in rows if r['target'] not in occupied_targets]
            if not missing:
                raise ValueError('No source-classified bodies are missing from the canonical CR artifact')
            native = load_module(files[4], '_classified_native_cr')
            records = json.loads(p4path.read_text())['documents']
            chunks = phase8_classified_chunks(native, missing, records,
                progress=lambda count: print(json.dumps({'stage': 'native_bodies_parsed', 'documents': count}), flush=True))
            loader = load_module(files[5], '_classified_native_loader')
            expected = {}
            for chunk in chunks:
                pid = loader.generate_point_id(chunk['chunkId'])
                if pid in expected or not chunk['text'].strip():
                    raise ValueError('Source body has duplicate point identity or empty text')
                expected[pid] = chunk
            targets = sorted(r['target'] for r in missing)
            if set(targets) != {c['tdocNumber'] for c in chunks}:
                raise ValueError('Missing source body coverage')
            actual = points_for(client, collection, targets)
            additions = validate_new_points(expected, actual)
            if any(not valid_vector(p['vector'], encoder.dim) for p in actual.values()):
                raise ValueError('Invalid existing source body vector')
            check_fence(fences)
            if sha(artifact) != original_sha:
                raise RuntimeError('CR artifact changed while preparing source bodies')
            run_dir.mkdir(parents=True)
            payload_path = run_dir / 'prepared_payloads.json.gz'
            durable_blob(payload_path, gzip.compress(json.dumps(expected, ensure_ascii=False).encode(), mtime=0))
            preimages = run_dir / 'qdrant_full_preimages.json.gz'
            durable_blob(preimages, gzip.compress(json.dumps(actual, ensure_ascii=False).encode(), mtime=0))
            report = dict(status='prepared', wg=args.wg, collection=collection, targets=targets,
                sourceBodyInputs=len(rows), sourceClassificationLedgerEntries=(
                    len(json.loads(ledger_path(ROOT,args.wg).read_text())['records'])
                    if ledger_path(ROOT,args.wg).exists() else 0),
                sourceFiles=fences, encoder=vars(encoder),
                artifact=dict(path=artifact.relative_to(ROOT).as_posix(), beforeSha256=original_sha),
                preparedPayloads=dict(path=payload_path.relative_to(ROOT).as_posix(), sha256=sha(payload_path)),
                pointPreimage=dict(path=preimages.relative_to(ROOT).as_posix(), sha256=sha(preimages)),
                beforePointCount=client.count(collection, exact=True).count, expectedPoints=len(expected),
                newPoints=len(additions), chunksByTarget=dict(Counter(c['tdocNumber'] for c in chunks)),
                occupiedPointsSha256=digest(actual), newPointIds=sorted(additions))
            durable_json(args.out, report)
            print(json.dumps({k:report[k] for k in ['status','sourceBodyInputs','expectedPoints','newPoints']})); return
        check_fence(report['sourceFiles'])
        try:
            payload_path = review_artifacts.resolve_recorded_path(ROOT, report['preparedPayloads']['path'],
                                                                  report['preparedPayloads']['sha256'])
        except (OSError, ValueError) as error:
            raise RuntimeError('Prepared body bytes changed') from error
        expected = {int(k):v for k,v in json.loads(gzip.decompress(payload_path.read_bytes())).items()}
        actual = points_for(client, collection, report['targets'])
        if digest(actual) != report['occupiedPointsSha256'] or sha(artifact) != report['artifact']['beforeSha256']:
            raise RuntimeError('Prepared artifact or full point preimage changed')
        additions = validate_new_points(expected, actual)
        # All body/identity/space/source/preimage checks precede writes.
        report['status'] = 'applying'; durable_json(args.out, report)
        report['artifact']['append'] = append_cr_artifact(artifact, list(expected.values()), run_dir,
                                                        provenance_field='sourceRecoveredBodies')
        durable_json(args.out, report)
        force_hf_offline()
        written = {}
        addition_items = list(additions.items())
        for start in range(0, len(addition_items), 64):
            selected = addition_items[start:start+64]
            vectors = rested(embed_local, encoder, [p['text'] for _,p in selected], batch_size=4)
            if len(vectors) != len(selected) or any(not valid_vector(v, encoder.dim) for v in vectors):
                raise RuntimeError('Source body embedding cardinality/vector invalid')
            check_fence(report['sourceFiles'])
            if client.retrieve(collection, [pid for pid,_ in selected], with_payload=False, with_vectors=False):
                raise RuntimeError('New source body point appeared concurrently')
            client.upsert(collection, [models.PointStruct(id=pid,payload=p,vector=v) for (pid,p),v in zip(selected,vectors)],wait=True)
            written.update({pid:v for (pid,_),v in zip(selected,vectors)})
            report['writtenPointIds'] = sorted(written); durable_json(args.out, report)
        got = points_for(client, collection, report['targets'])
        if set(got) != set(expected): raise RuntimeError('Source body final point coverage failed')
        for pid, point in got.items():
            if point['payload'] != expected[pid] or not valid_vector(point['vector'], encoder.dim):
                raise RuntimeError('Source body exact payload/vector readback failed')
            if pid in actual and point['vector'] != actual[pid]['vector']:
                raise RuntimeError('Existing source body vector changed')
            if pid in written:
                norm = math.sqrt(sum(v*v for v in written[pid])); epsilon = 8*2**-23
                if any(not math.isclose(a,b/norm,rel_tol=epsilon,abs_tol=epsilon) for a,b in zip(point['vector'],written[pid])):
                    raise RuntimeError('New source body vector readback differs')
        artifact_chunks = {c['chunkId']:c for c in iter_array(artifact,'chunks') if c['tdocNumber'] in set(report['targets'])}
        if artifact_chunks != {c['chunkId']:c for c in expected.values()}:
            raise RuntimeError('Source body canonical artifact readback differs')
        check_fence(report['sourceFiles'])
        report.update(status='complete', newVectorsReadBack=len(written), finalPointsSha256=digest(got),
            artifactAfterSha256=sha(artifact), afterPointCount=client.count(collection,exact=True).count,
            existingBodyIdentityVectorOrUnknownFieldChanges=0)
        if report['afterPointCount'] != report['beforePointCount'] + len(written):
            raise RuntimeError('Source body collection cardinality changed concurrently')
        durable_json(args.out, report)
        print(json.dumps(dict(status='complete',newVectorsReadBack=len(written),targets=len(report['targets']))))
    finally:
        primary_error = sys.exc_info()[1]
        try:
            client.close()
        except BaseException as close_error:
            if primary_error is None:
                raise
            add_exception_note(primary_error, f'Qdrant client close also failed: {type(close_error).__name__}: {close_error}')


if __name__ == '__main__': main()
