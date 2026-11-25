#!/usr/bin/env python3
"""reconcile_tdoc_source_supplements.py — guarded source-ledger Phase-1 reconciliation.

Spec: Phase-1 selected-source identity/count contract and retained CR source ledgers.
Ontology: source-identified Tdoc/CR and exact references; immediate revision inverses.
Cycle: validate originals → durable file/live preimages → fenced transaction → readback.
배경: missing spreadsheet rows and checked identity corrections share one source overlay.
사용: --out retained-receipt.json [--apply]; default produces a read-only plan.
LLM 호출: none. Local sources and explicit Neo4j writes only; no embeddings.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys

from tdoc_source_supplements import (SupplementError, reference_graphs, source_inputs,
                                     supplement_instances, validated_records)
from tdoc_source_identity_corrections import (overlay_identity_corrections,
    source_inputs as correction_inputs, validated_corrections)
from document_decision_storage import durable_json

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
sys.path.insert(0, str(ROOT / 'scripts/common'))
from common import axis, credentials
from common.atomic_io import write_text_atomic
from neo4j import GraphDatabase, READ_ACCESS

RELATIONS = {'submittedBy': ('SUBMITTED_BY', 'Company'), 'presentedAt': ('PRESENTED_AT', 'Meeting'),
 'modifies': ('MODIFIES', 'Spec'), 'targetRelease': ('TARGET_RELEASE', 'Release'),
 'relatedTo': ('RELATED_TO', 'WorkItem'), 'isRevisionOf': ('IS_REVISION_OF', 'Tdoc'),
 'revisedTo': ('REVISED_TO', 'Tdoc')}
INVERSE = {'IS_REVISION_OF': 'REVISED_TO', 'REVISED_TO': 'IS_REVISION_OF'}


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()


def snapshot(tx, numbers):
    nodes = tx.run('MATCH(n) WHERE n.tdocNumber IN $numbers RETURN elementId(n) AS elementId, labels(n) AS labels, properties(n) AS properties ORDER BY n.tdocNumber', numbers=numbers).data()
    for node in nodes:
        node['labels'].sort()
    edges = tx.run('''MATCH(n)-[r]-(m) WHERE n.tdocNumber IN $numbers
       WITH DISTINCT r RETURN elementId(r) AS elementId, elementId(startNode(r)) AS start,
       elementId(endNode(r)) AS end, type(r) AS type, properties(r) AS properties,
       startNode(r).id AS startId, endNode(r).id AS endId ORDER BY elementId''', numbers=numbers).data()
    return {'nodes': nodes, 'edges': edges}


def build_proposal(root, wg):
    directory = axis.tree_path('ontology_instances', wg=wg, phase=1, root=root)
    path = directory / 'tdocs.jsonld'
    original = path.read_bytes()
    document = json.loads(original)
    instances = document['@graph']
    references = reference_graphs(directory)
    # All selected meeting identities come from the existing canonical references.
    selected = {n['tdoc:meetingNumber'] for n in references['meetings']}
    rows = validated_records(root, wg, selected)
    corrections = validated_corrections(root, wg, selected)
    original_count = len(instances)
    supplements = supplement_instances(root, wg, instances, references, selected)
    instances.extend(supplements)
    changed = overlay_identity_corrections(root, wg, instances, references, selected)
    by_id = {n['@id']: n for n in instances}
    if len(by_id) != len(instances):
        raise SupplementError('Canonical document identity collision')
    affected = sorted({r['target'] for r in rows + corrections})
    props, add, remove, endpoints, labels = {}, set(), set(), {}, {}
    for row in rows:
        node = by_id['tdoc:' + row['target']]
        primary = node['@type']
        if primary not in {'tdoc:Tdoc', 'tdoc:CR', 'tdoc:LS'}:
            raise SupplementError('Unsupported document supplement class')
        labels[node['@id']] = sorted({'Tdoc', primary.removeprefix('tdoc:')})
        p = {'id': node['@id'], '_p1ReferenceSource': True}
        p.update({k.removeprefix('tdoc:'): v for k, v in node.items() if k.startswith('tdoc:')})
        for field, (rel, label) in RELATIONS.items():
            if field not in node:
                continue
            p['_' + field] = node[field]
            values = node[field] if isinstance(node[field], list) else [node[field]]
            for endpoint in values:
                add.add((node['@id'], rel, endpoint)); endpoints[endpoint] = label
                if rel in INVERSE:
                    add.add((endpoint, INVERSE[rel], node['@id']))
        props[node['@id']] = p
    for row in corrections:
        id_ = 'tdoc:' + row['target']
        for delta in row['deltas']:
            field, before, after = delta['field'], delta['before'], delta['sourceBackedValue']
            props.setdefault(id_, {})[field.removeprefix('tdoc:') if field.startswith('tdoc:') else '_' + field] = after
            if field in RELATIONS:
                rel, label = RELATIONS[field]
                remove.add((id_, rel, before)); add.add((id_, rel, after)); endpoints[after] = label
                if rel in INVERSE:
                    remove.add((before, INVERSE[rel], id_)); add.add((after, INVERSE[rel], id_))
    fences = source_inputs(root, wg, selected)
    fences.update(correction_inputs(root, wg, selected))
    for name in ('companies', 'meetings', 'specs', 'releases', 'work_items'):
        p = directory / (name + '.jsonld')
        fences[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    for name in ('reconcile_tdoc_source_supplements.py', 'tdoc_source_supplements.py', 'document_decision_source.py',
                 'tdoc_source_identity_corrections.py', 'tdoc_document_supplements.py'):
        p = Path(__file__).with_name(name)
        fences[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    encoded = json.dumps(document, ensure_ascii=False, indent=2)
    return {'wg': wg, 'path': path, 'original': original, 'encoded': encoded, 'fences': fences,
      'beforeCount': original_count, 'afterCount': len(instances), 'newCanonicalNodes': supplements,
      'supplementTargets': [r['target'] for r in rows], 'affected': affected,
      'sourceDispositions': dict(Counter(r['report']['sourceDocumentDisposition'] for r in rows)),
      'correctionScopes': dict(Counter(r['scope'] for r in corrections)), 'changedCanonicalFields': changed,
      'properties': props, 'labels': labels, 'addEdges': sorted(add), 'removeEdges': sorted(remove), 'endpoints': endpoints}


def source_fence(proposal):
    for relative, sha in proposal['fences'].items():
        if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != sha:
            raise SupplementError('Retained source/reference changed before commit: ' + relative)


def check_endpoints(tx, proposal):
    supplements = {'tdoc:' + x for x in proposal['supplementTargets']}
    endpoint_rows = tx.run('MATCH(n) WHERE n.id IN $ids RETURN n.id AS canonicalId, labels(n) AS labels, elementId(n) AS element', ids=sorted(proposal['endpoints'])).data()
    for id_, label in proposal['endpoints'].items():
        if id_ not in supplements and len([r for r in endpoint_rows if r['canonicalId'] == id_ and label in r['labels']]) != 1:
            raise SupplementError('Live canonical endpoint is absent/ambiguous: ' + id_)
    numbers = proposal['affected']
    rows = tx.run('MATCH(n) WHERE n.tdocNumber IN $numbers OR n.id IN $ids RETURN elementId(n) AS id, n.tdocNumber AS number, n.id AS canonicalId', numbers=numbers, ids=['tdoc:' + n for n in numbers]).data()
    for number in numbers:
        selected = [r for r in rows if r['number'] == number or r['canonicalId'] == 'tdoc:' + number]
        if len(selected) > 1 or (not selected and 'tdoc:' + number not in supplements):
            raise SupplementError('Live document identity absent/ambiguous: ' + number)
        if selected and (selected[0]['number'] != number or selected[0]['canonicalId'] not in (None, 'tdoc:' + number)):
            raise SupplementError('Live document has a different canonical identity: ' + number)


def apply_transaction(tx, proposal, before):
    if digest(snapshot(tx, proposal['affected'])) != digest(before):
        raise SupplementError('Live full node/edge preimage changed before apply')
    check_endpoints(tx, proposal)
    old_nodes = {n['properties']['tdocNumber']: n for n in before['nodes']}
    updates, creates = {}, {}
    for id_, properties in proposal['properties'].items():
        labels = tuple(sorted(proposal.get('labels', {}).get(id_, [])))
        if any(label not in {'Tdoc', 'CR', 'LS'} for label in labels):
            raise SupplementError('Unsupported supplement label')
        node = old_nodes.get(id_.removeprefix('tdoc:'))
        if node:
            updates.setdefault(labels, []).append(dict(element=node['elementId'], properties=properties))
        else:
            if not labels:
                raise SupplementError('A correction cannot invent a document')
            creates.setdefault(labels, []).append(dict(properties=properties))
    for labels, rows in updates.items():
        label_set = 'SET n:' + ':'.join(labels) + ' ' if labels else ''
        count = tx.run(f'UNWIND $rows AS row MATCH(n) WHERE elementId(n)=row.element {label_set}SET n += row.properties RETURN count(n) AS n', rows=rows).single()['n']
        if count != len(rows):
            raise SupplementError('Document element identity changed during apply')
    for labels, rows in creates.items():
        count = tx.run('UNWIND $rows AS row CREATE(n:' + ':'.join(labels) + ') SET n += row.properties RETURN count(n) AS n', rows=rows).single()['n']
        if count != len(rows):
            raise SupplementError('Created document cardinality differs')
    edge_ids = sorted({id_ for edges in (proposal['removeEdges'], proposal['addEdges']) for a, _, b in edges for id_ in (a, b)})
    bindings = {}
    for node in tx.run('MATCH(n) WHERE n.id IN $ids RETURN n.id AS id, elementId(n) AS element', ids=edge_ids).data():
        bindings.setdefault(node['id'], []).append(node['element'])
    for source, _, target in proposal['addEdges']:
        if len(bindings.get(source, [])) != 1 or len(bindings.get(target, [])) != 1:
            raise SupplementError('Relation endpoint became ambiguous during apply')
    for operation, key in [('remove', 'removeEdges'), ('add', 'addEdges')]:
        groups = {}
        for source, rel, target in proposal[key]:
            # Removing an absent edge is an idempotent no-op, as in the original
            # bound-property MATCH. Adds require exactly one endpoint above.
            for left in bindings.get(source, []):
                for right in bindings.get(target, []):
                    groups.setdefault(rel, []).append(dict(source=left, target=right))
        for rel, rows in groups.items():
            prefix = 'UNWIND $rows AS row MATCH(a),(b) WHERE elementId(a)=row.source AND elementId(b)=row.target '
            if operation == 'remove':
                tx.run(prefix + f'MATCH(a)-[r:{rel}]->(b) DELETE r', rows=rows).consume()
            else:
                count = tx.run(prefix + f'MERGE(a)-[r:{rel}]->(b) RETURN count(r) AS n', rows=rows).single()['n']
                if count != len(rows):
                    raise SupplementError('Relation endpoint or existing edge became ambiguous during apply')
    after = snapshot(tx, proposal['affected'])
    by_id = {n['properties']['id']: n for n in after['nodes']}
    for id_, properties in proposal['properties'].items():
        node = by_id[id_]
        if not set(proposal.get('labels', {}).get(id_, [])) <= set(node['labels']) or any(node['properties'].get(k) != v for k, v in properties.items()):
            raise SupplementError('Exact source property/label readback failed: ' + id_)
    removed = set(map(tuple, proposal['removeEdges']))
    added = set(map(tuple, proposal['addEdges']))
    old_edges = {e['elementId']: e for e in before['edges']}
    new_edges = {e['elementId']: e for e in after['edges']}
    for eid, edge in old_edges.items():
        stable = ('elementId', 'start', 'end', 'type', 'properties')
        if ((edge['startId'], edge['type'], edge['endId']) not in removed
                and (eid not in new_edges or any(new_edges[eid][k] != edge[k] for k in stable))):
            raise SupplementError('An unrelated live relationship changed')
    actual_keys = {(e['startId'], e['type'], e['endId']) for e in after['edges']}
    if not added <= actual_keys or (removed - added) & actual_keys:
        raise SupplementError('Exact source relation readback failed')
    for node in before['nodes']:
        id_ = node['properties'].get('id') or 'tdoc:' + node['properties']['tdocNumber']
        expected = {**node['properties'], **proposal['properties'].get(id_, {})}
        if by_id[id_]['properties'] != expected:
            raise SupplementError('An unrelated live property changed')
    for id_ in {'tdoc:' + r for r in proposal['affected']}:
        if len({e['endId'] for e in after['edges'] if e['startId'] == id_ and e['type'] == 'IS_REVISION_OF'}) > 1:
            raise SupplementError('Functional immediate revision identity violated')
    return after


def main(*, proposal_builder=None, wg_choices=('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5')):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wg', default='RAN5', choices=wg_choices)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    args.out = args.out.resolve()
    if not args.out.is_relative_to(ROOT):
        parser.error('Keep the durable reconciliation receipt within the repository')
    if args.out.exists():
        parser.error('Use a new receipt path; retain the existing journal')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    proposal = (proposal_builder or build_proposal)(ROOT, args.wg)
    source_fence(proposal)
    with GraphDatabase.driver(axis.bolt_uri(args.wg), auth=credentials.neo4j_auth()) as driver:
        with driver.session(default_access_mode=READ_ACCESS) as session:
            before = snapshot(session, proposal['affected']); check_endpoints(session, proposal)
            before_counts = session.run('MATCH(n) RETURN count(n) AS nodes, count(CASE WHEN n:Tdoc THEN 1 END) AS Tdoc, count(CASE WHEN n:CR THEN 1 END) AS CR').single().data()
        receipt = {k: v for k, v in proposal.items() if k not in ('path', 'original', 'encoded')}
        receipt.update(mode='read_only_plan', canonicalPath=proposal['path'].relative_to(ROOT).as_posix(),
          canonicalBeforeSha256=hashlib.sha256(proposal['original']).hexdigest(),
          canonicalAfterSha256=hashlib.sha256(proposal['encoded'].encode()).hexdigest(),
          livePreimage=before, livePreimageSha256=digest(before), liveBeforeCounts=before_counts)
        if args.apply:
            backup = args.out.with_suffix('.canonical-preimage.jsonld.gz')
            if backup.exists():
                if gzip.decompress(backup.read_bytes()) != proposal['original']:
                    raise SupplementError('Existing durable preimage belongs to a different canonical source')
            else:
                with backup.open('xb') as stream:
                    stream.write(gzip.compress(proposal['original'], mtime=0)); stream.flush()
                    import os
                    os.fsync(stream.fileno())
            receipt['canonicalPreimage'] = {'path': backup.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(backup.read_bytes()).hexdigest(), 'uncompressedSha256': receipt['canonicalBeforeSha256']}
            receipt['mode'] = 'prepared_with_durable_preimages'
            durable_json(args.out, receipt)
            replaced = False
            commit_started = False
            try:
                with driver.session() as session:
                    tx = session.begin_transaction()
                    try:
                        source_fence(proposal)
                        if proposal['path'].read_bytes() != proposal['original']:
                            raise SupplementError('Canonical file changed before apply')
                        after = apply_transaction(tx, proposal, before)
                        receipt['livePreparedReadbackSha256'] = digest(after)
                        source_fence(proposal)
                        write_text_atomic(proposal['path'], proposal['encoded']); replaced = True
                        receipt['mode'] = 'canonical_written_transaction_pending'
                        durable_json(args.out, receipt)
                        commit_started = True
                        tx.commit()
                    except BaseException:
                        if not commit_started:
                            tx.rollback()
                        raise
            except BaseException:
                # A transport exception during commit does not prove rollback.
                # Preserve both durable states for exact recovery instead of
                # restoring the file against a possibly committed transaction.
                if commit_started:
                    receipt['mode'] = 'commit_outcome_requires_readback'
                    durable_json(args.out, receipt)
                    raise
                if replaced and hashlib.sha256(proposal['path'].read_bytes()).hexdigest() == receipt['canonicalAfterSha256']:
                    write_text_atomic(proposal['path'], proposal['original'].decode())
                receipt['mode'] = 'rolled_back_restore_preimage'; durable_json(args.out, receipt); raise
            with driver.session(default_access_mode=READ_ACCESS) as session:
                readback = snapshot(session, proposal['affected'])
                receipt['liveAfterCounts'] = session.run('MATCH(n) RETURN count(n) AS nodes, count(CASE WHEN n:Tdoc THEN 1 END) AS Tdoc, count(CASE WHEN n:CR THEN 1 END) AS CR').single().data()
            if digest(readback) != digest(after):
                raise SupplementError('Committed live readback changed; retained recovery journal requires inspection')
            if hashlib.sha256(proposal['path'].read_bytes()).hexdigest() != receipt['canonicalAfterSha256']:
                raise SupplementError('Committed canonical file SHA readback failed')
            receipt.update(mode='applied_exact_readback', liveReadback=readback,
              liveReadbackSha256=digest(readback), unrelatedPropertyOrRelationChanges=0,
              functionalRevisionViolations=0)
        durable_json(args.out, receipt)
        print(json.dumps({k: receipt[k] for k in ('mode', 'beforeCount', 'afterCount', 'sourceDispositions', 'correctionScopes', 'canonicalBeforeSha256', 'canonicalAfterSha256')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
