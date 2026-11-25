#!/usr/bin/env python3
"""reconcile_tdoc_revisions.py — reconcile qualified immediate revision edges and raw claims.

Spec: selected XLSX physical cells in tdoc_revision_qualification.json.
Ontology: revisedTo inverse isRevisionOf; rejected interpretations remain EvidenceAssertion.
Cycle: full file/live preimages → source/code CAS → locked transaction → exact readback.
배경: source registration facts and immediate-lineage interpretations have distinct status.
사용: --wg RAN3 --out NEW_DIRECTORY [--apply]; the default is read-only.
LLM 호출: none. No embeddings, original document edits, or unrelated relationship updates.
"""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import os
from pathlib import Path

import tdoc_revision_evidence as e
import reconcile_tdoc_source_supplements as base
from document_decision_storage import durable_json
from common import axis, credentials
from common.atomic_io import write_text_atomic
from neo4j import GraphDatabase, READ_ACCESS

ROOT = e.ROOT


def proposal(root, wg):
    directory = axis.tree_path('ontology_instances', wg=wg, phase=1, root=root)
    path = directory / 'tdocs.jsonld'
    original = path.read_bytes()
    doc = json.loads(original)
    before = copy.deepcopy(doc['@graph'])
    records = e.qualify_revisions(root, wg, doc['@graph'])
    if not records:
        raise ValueError('No reviewed revision qualifications in the selected population')
    by_id = {n['@id']: n for n in doc['@graph']}
    affected = sorted({r[k] for r in records for k in ('source', 'target', 'keptParent')})
    props = {'tdoc:' + r['source']: {'_revisedTo': by_id['tdoc:' + r['source']].get('revisedTo', [])} for r in records}
    remove = sorted({edge for r in records for edge in [
        ('tdoc:' + r['source'], 'REVISED_TO', 'tdoc:' + r['target']),
        ('tdoc:' + r['target'], 'IS_REVISION_OF', 'tdoc:' + r['source'])]})
    fences = e.source_inputs(root, wg)
    paths = [Path(__file__), Path(e.__file__), Path(base.__file__),
             root / f'scripts/tsg/RAN/formal/{wg}/phase-1/jsonld/03_tdoc_instances.py',
             root / f'scripts/tsg/RAN/formal/{wg}/phase-1/neo4j/01_load_kg.py',
             root / 'scripts/common/ontology/jsonld_context.py', root / 'ontology/schema/tdoc-ontology.ttl']
    fences.update({str(p.relative_to(root)): e.sha(p) for p in paths})
    changed = [{'id': a['@id'], 'before': a.get('revisedTo'), 'after': b.get('revisedTo')}
               for a, b in zip(before, doc['@graph']) if a != b]
    for a, b in zip(before, doc['@graph']):
        if {k: v for k, v in a.items() if k != 'revisedTo'} != {k: v for k, v in b.items() if k != 'revisedTo'}:
            raise ValueError('An unrelated canonical document field changed')
    return {'wg': wg, 'path': path, 'original': original, 'encoded': json.dumps(doc, ensure_ascii=False, indent=2),
            'fences': fences, 'affected': affected, 'properties': props, 'labels': {}, 'addEdges': [],
            'removeEdges': remove, 'endpoints': {'tdoc:' + number: 'Tdoc' for number in affected},
            'supplementTargets': [], 'beforeCount': len(before), 'afterCount': len(doc['@graph']),
            'changedFields': changed, 'records': records, 'evidence': e.evidence_document(records, wg)}


def evidence_snapshot(tx, document):
    ids = [n['@id'] for n in document['@graph']]
    nodes = tx.run('MATCH(n) WHERE n.id IN $ids RETURN elementId(n) AS elementId, labels(n) AS labels, properties(n) AS properties ORDER BY n.id', ids=ids).data()
    edges = tx.run('''MATCH(n)-[r]-(m) WHERE n.id IN $ids WITH DISTINCT r
       RETURN elementId(r) AS elementId,type(r) AS type,properties(r) AS properties,
       startNode(r).id AS startId,endNode(r).id AS endId ORDER BY elementId''', ids=ids).data()
    return {'nodes': nodes, 'edges': edges}


def save_preimage(path, data):
    with path.open('xb') as stream:
        stream.write(gzip.compress(data, mtime=0)); stream.flush(); os.fsync(stream.fileno())
    return {'path': str(path.relative_to(ROOT)), 'sha256': e.sha(path),
            'uncompressedSha256': hashlib.sha256(data).hexdigest()}


def check_owned_qualification_delta(core_after, after, document):
    if core_after['nodes'] != after['nodes']:
        raise ValueError('Qualification records changed an unrelated Tdoc property')
    aids = {n['@id'] for n in document['@graph'] if n['@type'] == 'EvidenceAssertion'}
    filtered = [r for r in after['edges'] if not (r['startId'] in aids and r['type'] in {'ASSERTION_SUBJECT', 'ASSERTION_OBJECT'})]
    if filtered != core_after['edges']:
        raise ValueError('Qualification records changed an unrelated incident edge')


def run(root, wg, out, apply=False):
    out = out.resolve(); out.relative_to(root)
    if out.exists():
        raise FileExistsError('Retain the previous journal and use a new directory')
    p = proposal(root, wg)
    evidence_path = p['path'].with_name(e.EVIDENCE_FILE)
    if evidence_path.exists():
        raise FileExistsError('An evidence document already exists; inspect the prior reconciliation')
    base.source_fence(p)
    out.mkdir(parents=True)
    with GraphDatabase.driver(axis.bolt_uri(wg), auth=credentials.neo4j_auth()) as driver:
        with driver.session(default_access_mode=READ_ACCESS) as session:
            before = base.snapshot(session, p['affected']); base.check_endpoints(session, p)
            evidence_before = evidence_snapshot(session, p['evidence'])
        if evidence_before['nodes'] or evidence_before['edges']:
            raise ValueError('Qualification identity already exists; inspect before attempting replacement')
        receipt = {'status': 'read_only_plan', 'wg': wg, 'sourceFences': p['fences'],
                   'canonicalPath': str(p['path'].relative_to(root)), 'beforeCount': p['beforeCount'],
                   'afterCount': p['afterCount'], 'changedFields': p['changedFields'],
                   'canonicalBeforeSha256': hashlib.sha256(p['original']).hexdigest(),
                   'canonicalAfterSha256': hashlib.sha256(p['encoded'].encode()).hexdigest(),
                   'removeEdges': p['removeEdges'], 'liveFullPreimage': before,
                   'liveEvidenceFullPreimage': evidence_before, 'evidenceDocument': p['evidence']}
        durable_json(out / 'plan.json', receipt)
        if not apply:
            return receipt
        receipt['canonicalPreimage'] = save_preimage(out / 'tdocs.before.jsonld.gz', p['original'])
        evidence_bytes = json.dumps(p['evidence'], ensure_ascii=False, indent=2).encode()
        receipt['evidenceAfterSha256'] = hashlib.sha256(evidence_bytes).hexdigest()
        receipt['evidenceBefore'] = {'path': str(evidence_path.relative_to(root)), 'exists': False}
        durable_json(out / 'plan.json', receipt)
        replaced = []; commit_started = False
        try:
            with driver.session() as session:
                tx = session.begin_transaction()
                try:
                    base.source_fence(p)
                    if p['path'].read_bytes() != p['original'] or evidence_path.exists():
                        raise ValueError('Canonical input/evidence file changed before write')
                    tx.run('MATCH(n:Tdoc) WHERE n.tdocNumber IN $ids SET n._revisedTo=n._revisedTo', ids=p['affected']).consume()
                    if evidence_snapshot(tx, p['evidence']) != evidence_before:
                        raise ValueError('Qualification identity changed before write')
                    core_after = base.apply_transaction(tx, p, before)
                    e.load_evidence(tx, p['evidence'])
                    after = base.snapshot(tx, p['affected'])
                    check_owned_qualification_delta(core_after, after, p['evidence'])
                    evidence_after = evidence_snapshot(tx, p['evidence'])
                    base.source_fence(p)
                    if p['path'].read_bytes() != p['original'] or evidence_path.exists():
                        raise ValueError('Canonical file changed during transaction')
                    write_text_atomic(p['path'], p['encoded']); replaced.append(p['path'])
                    write_text_atomic(evidence_path, evidence_bytes.decode()); replaced.append(evidence_path)
                    receipt.update(status='canonical_written_transaction_pending', livePreparedReadback=after,
                                   liveEvidencePreparedReadback=evidence_after)
                    durable_json(out / 'progress.json', receipt)
                    commit_started = True; tx.commit()
                except BaseException:
                    if not commit_started:
                        tx.rollback()
                    raise
        except BaseException:
            if commit_started:
                receipt['status'] = 'commit_outcome_requires_readback'
            else:
                if evidence_path in replaced and e.sha(evidence_path) == receipt['evidenceAfterSha256']:
                    evidence_path.unlink()
                if p['path'] in replaced and e.sha(p['path']) == receipt['canonicalAfterSha256']:
                    write_text_atomic(p['path'], p['original'].decode())
                receipt['status'] = 'rolled_back_owned_changes'
            durable_json(out / 'result.json', receipt)
            raise
        with driver.session(default_access_mode=READ_ACCESS) as session:
            actual = base.snapshot(session, p['affected']); actual_evidence = evidence_snapshot(session, p['evidence'])
            e.verify_evidence(session, p['evidence'])
        if actual != after or actual_evidence != evidence_after:
            raise ValueError('Committed exact live readback changed; inspect retained journal')
        if e.sha(p['path']) != receipt['canonicalAfterSha256'] or e.sha(evidence_path) != receipt['evidenceAfterSha256']:
            raise ValueError('Committed exact canonical readback changed')
        e.preflight_revision_document(root, wg)
        base.source_fence(p)
        receipt.update(status='complete', interpretationsQualified=len(p['records']),
                       rawRegistrationSourceWrites=0, unrelatedPropertyOrRelationshipChanges=0,
                       liveReadback=actual, liveEvidenceReadback=actual_evidence)
        durable_json(out / 'result.json', receipt)
        return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wg', choices=['RAN2', 'RAN3', 'RAN4'], required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    r = run(ROOT, args.wg, args.out, args.apply)
    print(json.dumps({k: r[k] for k in ['status', 'wg', 'beforeCount', 'afterCount', 'canonicalAfterSha256']}))


if __name__ == '__main__':
    main()
