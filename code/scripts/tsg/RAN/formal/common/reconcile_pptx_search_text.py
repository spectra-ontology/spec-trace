#!/usr/bin/env python3
"""reconcile_pptx_search_text.py — selectively repair source-backed slide text.

Spec: RAN5 Phase-6 native source / chunk / encoder preservation contract.
Ontology: document disposition, identity and foreign payload fields are retained.
Cycle: source replay → complete cohort preimages → local embedding → exact readback.
배경: plain slide getters omitted explicit run roles and editable math shapes.
사용: --proposal JSON --output NEW_DIRECTORY [--apply], with exclusive writer freeze.
LLM 호출: 없음. The registry-pinned local encoder embeds changed bodies only.

Precommit checks require an exclusive writer window; Qdrant has no atomic
compare-and-swap here. Rollback restores only our exact postimages. Source
evidence quotes and original presentation bytes are never rewritten.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
from qdrant_client import QdrantClient, models

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
sys.path[:0] = [str(Path(__file__).parent), str(ROOT / 'scripts/common')]
import tdoc_supplement_vectors as producer
from tdoc_document_supplements import native_blocks
from common.chunker import enforce_hard_max
from common.atomic_io import write_bytes_atomic
from common.exception_notes import add_exception_note
from common.embedding_registry import require_local, load_local_tokenizer, embed_local
from common.local_model import BGE_M3_FILES


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def sha(path):
    return producer.sha(path)


def atomic_bytes(path, raw):
    write_bytes_atomic(path, raw)
    descriptor = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_json(path, value):
    atomic_bytes(path, encoded(value) + b'\n')


def same_point(actual, expected):
    return (str(actual['id']) == str(expected['id']) and actual['payload'] == expected['payload']
            and np.array_equal(np.asarray(actual['vector'], dtype=np.float32),
                               np.asarray(expected['vector'], dtype=np.float32)))


def snapshot(client, collection, targets):
    rows, offset = {}, None
    seen_offsets = set()
    scope = models.Filter(must=[models.FieldCondition(key='tdocNumber', match=models.MatchAny(any=targets))])
    while True:
        points, offset = client.scroll(collection, scroll_filter=scope, limit=128,
            offset=offset, with_payload=True, with_vectors=True)
        for point in points:
            key = str(point.id)
            if key in rows:
                raise ValueError('duplicate point ID')
            rows[key] = {'id': point.id, 'payload': point.payload, 'vector': point.vector}
        if offset is None:
            return rows
        if offset in seen_offsets:
            raise ValueError('Repeated Qdrant scroll offset: ' + repr(offset))
        seen_offsets.add(offset)


def assert_snapshot(actual, expected):
    if set(actual) != set(expected) or any(not same_point(actual[key], row) for key, row in expected.items()):
        raise ValueError('cohort payload/vector/population comparison failed')


def assert_fence(fences):
    for path, expected in fences.items():
        if sha(ROOT / path) != expected:
            raise ValueError('source/code fence changed: ' + path)


def model_files(enc):
    from huggingface_hub.constants import HF_HUB_CACHE
    directory = Path(HF_HUB_CACHE) / ('models--' + enc.model.replace('/', '--')) / 'snapshots' / enc.revision
    records = []
    for name, declared in BGE_M3_FILES.items():
        path = directory / name
        # Large weights are hashed as a stream, without a second in-memory copy.
        actual = sha(path)
        if len(declared) == 64:
            check = actual
        else:
            digest = hashlib.sha1(b'blob ' + str(path.stat().st_size).encode() + b'\0')
            with path.open('rb') as stream:
                for part in iter(lambda: stream.read(1024 * 1024), b''):
                    digest.update(part)
            check = digest.hexdigest()
        if check != declared:
            raise ValueError('pinned model mismatch: ' + name)
        records.append({'file': name, 'sha256': actual, 'bytes': path.stat().st_size, 'declaredHash': declared})
    return records


def rollback_owned(client, collection, before, desired, attempted, artifact_images):
    """Do not overwrite a concurrent/foreign point or file after a failure."""
    actual = {str(p.id): {'id': p.id, 'payload': p.payload, 'vector': p.vector}
              for p in client.retrieve(collection, ids=[before[key]['id'] for key in attempted],
                                       with_payload=True, with_vectors=True)}
    for key in attempted:
        current = actual.get(key)
        if current is not None and same_point(current, before[key]):
            continue
        if current is None or not same_point(current, desired[key]):
            raise ValueError('rollback refuses foreign point state: ' + key)
        row = before[key]
        client.upsert(collection, points=[models.PointStruct(**row)], wait=True)
    for path, old, new in artifact_images:
        current = path.read_bytes()
        if current == old:
            continue
        if current != new:
            raise ValueError('rollback refuses foreign artifact state: ' + str(path))
        atomic_bytes(path, old)


def prepare_vectors(enc, changed, desired):
    vectors = embed_local(enc, [c['newPayload']['content'] for c in changed], batch_size=1)
    if len(vectors) != len(changed):
        raise ValueError('source repair embedding cardinality mismatch')
    for change, vector in zip(changed, vectors):
        array = np.asarray(vector, dtype=np.float32)
        if array.shape != (enc.dim,) or not np.isfinite(array).all() or abs(float(np.linalg.norm(array)) - 1) > 1e-5:
            raise ValueError('invalid new embedding')
        desired[change['pointId']]['vector'] = array.tolist()


def reconcile(proposal_path, output, *, apply=False):
    output.mkdir(parents=True, exist_ok=False)
    proposal_raw = proposal_path.read_bytes()
    proposal = json.loads(proposal_raw)
    collection = proposal['collection']
    if collection != 'ran5_tdoc_chunks':
        raise ValueError('this maintained repair is scoped to RAN5 native Tdoc slides')
    report = {'status': 'preflight', 'startedAt': datetime.now(timezone.utc).isoformat(),
        'apply': apply, 'collection': collection, 'proposalPath': str(proposal_path.relative_to(ROOT)),
        'proposalSHA256': sha_bytes(proposal_raw), 'writerRequirement': 'exclusive collection writer freeze; non-atomic precommit comparisons',
        'sourceIdentityReaderChanged': False, 'changedPoints': [], 'artifactChanges': []}
    atomic_json(output / 'receipt.json', report)
    manifest = ROOT / 'ontology/input/tsg/RAN/formal/meetings/RAN5/tdoc_source_supplements.json'
    rows = [r for r in json.loads(manifest.read_text())['records'] if r['path'].lower().endswith('.pptx')]
    if {r['target'] for r in rows} != {'R5-185183', 'R5-192663', 'R5-192869'}:
        raise ValueError('reviewed three-source cohort changed')
    fences = producer.source_fence('RAN5', rows)
    fences[str(Path(__file__).relative_to(ROOT))] = sha(Path(__file__))
    fences[str(proposal_path.relative_to(ROOT))] = report['proposalSHA256']
    lib = producer.load_module(ROOT / 'scripts/tsg/RAN/formal/RAN5/phase-6/tdoc-parser/parse_tdoc_lib.py', '_pptx_repair_lib')
    artifact_images, generated, current_chunks = [], {}, {}
    for row in rows:
        target = row['target']
        paths = list((ROOT / 'vectordb/parsed/tdocs/RAN5').glob('*/' + target + '/chunks.json'))
        if len(paths) != 1:
            raise ValueError('ambiguous retained source artifact: ' + target)
        path = paths[0]
        old_raw = path.read_bytes()
        document = json.loads(old_raw)
        legacy = native_blocks(ROOT, row)
        sections = [lib.Section(title=k, level=1, content=f'[{k}] {v}', start_idx=i, end_idx=i + 1)
                    for i, (k, v) in enumerate(legacy.items()) if v.strip()]
        legacy_chunks = enforce_hard_max(lib.ChunkEngine().chunk_sections(sections, tdoc_number=target), hard_max=6500)
        parsed = producer.native_content(lib, 'RAN5', row)
        chunks = enforce_hard_max(lib.ChunkEngine().chunk_sections(parsed.sections, tdoc_number=target), hard_max=6500)
        if len(chunks) != len(document['chunks']) or len(chunks) != len(legacy_chunks):
            raise ValueError('source repair changes chunk population')
        revised = deepcopy(document)
        for old, baseline, new in zip(document['chunks'], legacy_chunks, chunks):
            if old != baseline and old != new:
                raise ValueError('artifact is neither source legacy nor source search projection')
            if old['chunkId'] != new['chunkId'] or old['chunkIndex'] != new['chunkIndex']:
                raise ValueError('source repair changes chunk identity')
            if {key for key in old if old[key] != new[key]} - {'content', 'tokenCount'} or set(old) != set(new):
                raise ValueError('unexpected artifact field change')
            generated[new['chunkId']], current_chunks[old['chunkId']] = new, old
        revised['chunks'] = chunks
        if revised != document:
            new_raw = json.dumps(revised, ensure_ascii=False, indent=2).encode() + b'\n'
            artifact_images.append((path, old_raw, new_raw))
            report['artifactChanges'].append({'path': str(path.relative_to(ROOT)), 'beforeSHA256': sha_bytes(old_raw),
                'afterSHA256': sha_bytes(new_raw)})
        backup = output / (target + '.artifact_before.json.gz')
        atomic_bytes(backup, gzip.compress(old_raw, mtime=0))
        report.setdefault('artifactPreimages', []).append({'path': str(path.relative_to(ROOT)),
            'backup': str(backup.relative_to(ROOT)), 'sha256': sha_bytes(old_raw), 'gzipSHA256': sha(backup)})
    client = QdrantClient(host='localhost', port=6333, grpc_port=6334, prefer_grpc=True, timeout=120)
    try:
        count = client.count(collection, exact=True).count
        before = snapshot(client, collection, [r['target'] for r in rows])
        historical_path = proposal_path.parent / Path(proposal['fullBeforeImages']['pointsPath']).name
        if sha(historical_path) != proposal['fullBeforeImages']['pointsSHA256']:
            raise ValueError('historical full preimages changed')
        historical = {str(p['id']): p for p in json.loads(gzip.decompress(historical_path.read_bytes()))['points']}
        if set(before) != set(historical) or len(before) != 20:
            raise ValueError('reviewed 20-point cohort changed')
        requested = {str(p['pointId']): p for p in proposal['points']}
        if set(requested) != {'11794328178286834859', '13055629634629439117'}:
            raise ValueError('approved two-point scope changed')
        desired = deepcopy(before)
        enc, tokenizer = require_local(collection), load_local_tokenizer(require_local(collection))
        for key, old in before.items():
            cid = old['payload']['chunkId']
            new = generated[cid]
            if key not in requested:
                if not same_point(old, historical[key]) or current_chunks[cid] != new:
                    raise ValueError('unrelated historical point/artifact changed')
                continue
            approved = requested[key]
            payload = dict(old['payload'], content=new['content'], tokenCount=new['tokenCount'])
            if payload != approved['proposedPayload']:
                raise ValueError('source regeneration differs from approved full payload')
            if old['payload'] == payload:
                continue
            if old['payload'] != approved['expectedBeforePayload'] or not same_point(old, historical[key]):
                raise ValueError('point differs from approved full preimage')
            tokens = len(tokenizer(payload['content'], add_special_tokens=True, truncation=False)['input_ids'])
            if not 0 < tokens <= min(6500, enc.max_tokens):
                raise ValueError('embedding token budget exceeded')
            desired[key]['payload'] = payload
            report['changedPoints'].append({'pointId': key, 'chunkId': cid, 'newPayload': payload,
                'oldBodySHA256': sha_bytes(old['payload']['content'].encode()),
                'newBodySHA256': sha_bytes(payload['content'].encode()), 'encoderTokensIncludingSpecial': tokens})
        changed = report['changedPoints']
        if bool(changed) != bool(artifact_images) or len(changed) not in {0, 2}:
            raise ValueError('partial repair or stale artifact/payload state')
        preimage = output / 'full_cohort_preimages.json.gz'
        atomic_bytes(preimage, gzip.compress(encoded(before), mtime=0))
        report.update(pointsBefore=count, cohortPoints=len(before), sourceAndCodeFences=fences,
            preimageSHA256=sha(preimage), encoder=asdict(enc), changedPointCount=len(changed),
            artifactChangedCount=len(artifact_images), localModelFiles=model_files(enc))
        report['hardware'] = subprocess.check_output(['nvidia-smi', '--query-gpu=name,memory.total,driver_version', '--format=csv,noheader'], text=True).strip()
        report['status'] = 'prepared'
        atomic_json(output / 'receipt.json', report)
        assert_fence(fences)
        if not apply:
            return report
        prepare_vectors(enc, changed, desired)
        atomic_json(output / 'prepared_points.json', {key: desired[key] for key in requested})
        assert_fence(fences)
        assert_snapshot(snapshot(client, collection, [r['target'] for r in rows]), before)
        if client.count(collection, exact=True).count != count or any(path.read_bytes() != old for path, old, _ in artifact_images):
            raise ValueError('precommit artifact or collection population changed')
        report['status'], report['attemptedPointIds'] = 'applying', []
        atomic_json(output / 'receipt.json', report)
        try:
            for change in changed:
                key = change['pointId']
                report['attemptedPointIds'].append(key)
                atomic_json(output / 'receipt.json', report)
                client.upsert(collection, points=[models.PointStruct(**desired[key])], wait=True)
            for path, old, new in artifact_images:
                if path.read_bytes() != old:
                    raise ValueError('artifact changed before atomic replacement')
                atomic_bytes(path, new)
            assert_snapshot(snapshot(client, collection, [r['target'] for r in rows]), desired)
            if client.count(collection, exact=True).count != count or any(path.read_bytes() != new for path, _, new in artifact_images):
                raise ValueError('artifact or collection readback mismatch')
            assert_fence(fences)
        except BaseException as error:
            report['error'] = repr(error)
            try:
                rollback_owned(client, collection, before, desired, report['attemptedPointIds'], artifact_images)
                assert_snapshot(snapshot(client, collection, [r['target'] for r in rows]), before)
                report['status'] = 'rolled_back_exact_owned_preimages'
            except BaseException as rollback_error:
                report['status'], report['rollbackError'] = 'failed_preserved_preimages', repr(rollback_error)
            atomic_json(output / 'receipt.json', report)
            raise
        report.update(status='complete', finishedAt=datetime.now(timezone.utc).isoformat(),
            pointsAfter=count, changedVectorsExactReadBack=len(changed), untouchedCohortExact=20-len(changed),
            cohortAfterSHA256=sha_bytes(encoded(desired)), sourceAndCodeFencePass=True,
            originalSourceWrites=0, identityOrDispositionChanges=0)
        atomic_json(output / 'receipt.json', report)
        return report
    finally:
        primary_error = sys.exc_info()[1]
        try:
            client.close()
        except BaseException as close_error:
            if primary_error is None:
                raise
            add_exception_note(primary_error, f'Qdrant client close also failed: {type(close_error).__name__}: {close_error}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proposal', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    result = reconcile(args.proposal.resolve(), args.output.resolve(), apply=args.apply)
    print(json.dumps({key: result[key] for key in ('status', 'changedPointCount', 'pointsBefore')}))
