#!/usr/bin/env python3
"""tdoc_revision_evidence.py — qualify registered revision claims against immediate lineage.

Spec: Phase-1 selected registration rows and retained revision qualification ledger.
Ontology: functional isRevisionOf/inverse revisedTo; rejected interpretations retain EvidenceAssertion.
Cycle: exact XLSX cells → qualified canonical relations → evidence export → guarded loader.
배경: a registered final target or merge input is distinct from an immediate predecessor.
사용: qualify_revisions(root, wg, nodes); preflight_revision_document(root, wg).
LLM 호출: none. Only retained local source cells and explicit evidence are used.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
sys.path.insert(0, str(ROOT / 'scripts/common'))
from common import axis, review_artifacts
from common.atomic_io import write_text_atomic
from ontology.jsonld_context import canonical_document

PREDICATE = 'https://w3id.org/spectra#revisedTo'
EVIDENCE_FILE = 'revision_source_assertions.jsonld'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ledger_path(root, wg):
    return Path(root) / f'ontology/input/tsg/RAN/formal/meetings/{wg}/tdoc_revision_qualification.json'


def values(value):
    return value if isinstance(value, list) else ([] if value is None else [value])


def source_inputs(root, wg):
    path = ledger_path(root, wg)
    if not path.exists():
        return {}
    ledger = json.loads(path.read_text())
    result = {str(path.relative_to(root)): sha(path)}
    for item in [*ledger.get('additionalSourceInputs', []), *([ledger['primaryAdjudication']] if ledger.get('primaryAdjudication') else [])]:
        result[item['path']] = item['sha256']
    for record in ledger['reviews']:
        for cell in (record['sourceCell'], record['priorCell']):
            if cell['path'] in result and result[cell['path']] != cell['sha256']:
                raise ValueError('Conflicting revision source editions')
            result[cell['path']] = cell['sha256']
    for item in ledger.get('nativeSourceEvidence', []):
        result[item['path']] = item['sha256']
    return {
        str(review_artifacts.resolve_recorded_path(root, relative, expected)
            .relative_to(Path(root).absolute())): expected
        for relative, expected in result.items()
    }


def validated_reviews(root, wg):
    path = ledger_path(root, wg)
    if not path.exists():
        return []
    ledger = json.loads(path.read_text())
    if ledger['workingGroup'] != wg or ledger['contract'] != 'immediate_predecessor_from_own_registered_row_v1':
        raise ValueError('Revision qualification ledger contract differs')
    records = ledger['reviews']
    keys = {(r['source'], r['target']) for r in records}
    if len(keys) != len(records):
        raise ValueError('Duplicate revision qualification')
    groups = {}
    for row in records:
        if row['source'] == row['keptParent'] or row['interpretationStatus'] != 'rejected':
            raise ValueError('A revision assessment cannot reject its own immediate predecessor')
        for kind, cell in [('source', row['sourceCell']), ('prior', row['priorCell'])]:
            groups.setdefault(cell['path'], []).append((kind, row, cell))
    import openpyxl
    for relative, cells in groups.items():
        source = (Path(root) / relative).resolve()
        source.relative_to(Path(root).resolve())
        before = sha(source)
        if any(c['sha256'] != before for _, _, c in cells):
            raise ValueError('Revision registration source SHA changed: ' + relative)
        book = openpyxl.load_workbook(source, read_only=True, data_only=True)
        try:
            for kind, row, cell in cells:
                actual = next(book[cell['sheet']].iter_rows(min_row=cell['row'], max_row=cell['row'], values_only=True))
                if str(actual[cell['column'] - 1] or '') != cell['rawValue'] or actual[0] != (row['source'] if kind == 'source' else row['target']):
                    raise ValueError('Revision source physical cell/row identity changed')
                header = next(book[cell['sheet']].iter_rows(min_row=1, max_row=1, values_only=True))
                header_column = cell['headerColumn']
                if header[header_column - 1] != ('Revised to' if kind == 'source' else 'Is revision of'):
                    raise ValueError('Revision source column role changed')
                if kind == 'source' and row['target'] not in re.findall(r'(?<![\w-])R[1-5]-\d+(?![\w-])', cell['rawValue']):
                    raise ValueError('Registered forward target is not present in its actual cell')
                if kind == 'prior' and cell['rawValue'] != row['keptParent']:
                    raise ValueError('Own registered predecessor differs from the adjudicated predecessor')
        finally:
            book.close()
        if sha(source) != before:
            raise ValueError('Revision source changed during validation')
    for relative, expected in source_inputs(root, wg).items():
        if sha(Path(root) / relative) != expected:
            raise ValueError('Revision source evidence changed: ' + relative)
    return records


def revision_conflicts(nodes):
    """Check the inverse closure without treating OWL equality as source truth."""
    by_id = {node['@id']: node for node in nodes}
    candidates = {}
    for node in nodes:
        for parent in values(node.get('isRevisionOf')):
            candidates.setdefault(node['@id'], set()).add(parent)
        for child in values(node.get('revisedTo')):
            if child in by_id:
                candidates.setdefault(child, set()).add(node['@id'])
    return {key: sorted(parents) for key, parents in candidates.items() if len(parents) > 1}


def qualify_revisions(root, wg, nodes, *, reviews=None):
    """Remove only reviewed non-immediate interpretations; retain literal registration evidence."""
    records = validated_reviews(root, wg) if reviews is None else reviews
    by_id = {node['@id']: node for node in nodes}
    if len(by_id) != len(nodes):
        raise ValueError('Duplicate canonical document identity')
    active = []
    for record in records:
        source, child, parent = ('tdoc:' + record[k] for k in ('source', 'target', 'keptParent'))
        if source not in by_id or child not in by_id:
            continue  # Selected meetings are allowed to contain a strict subset of this source ledger.
        if values(by_id[child].get('isRevisionOf')) != [parent]:
            raise ValueError('Own immediate predecessor differs from the reviewed source: ' + child)
        old = values(by_id[source].get('revisedTo'))
        new = [value for value in old if value != child]
        if new:
            by_id[source]['revisedTo'] = new if isinstance(by_id[source].get('revisedTo'), list) else new[0]
        else:
            by_id[source].pop('revisedTo', None)
        active.append(record)
    conflicts = revision_conflicts(nodes)
    if conflicts:
        raise ValueError('Unreviewed immediate revision inverse conflict: ' + json.dumps(conflicts, sort_keys=True))
    return active


def evidence_document(records, wg):
    assertions, fragments = [], {}
    for row in records:
        iid = f'{wg}:revision-source:{row["source"]}:{row["target"]}'
        a = {'@id': 'tdoc:assertion/' + iid, '@type': 'EvidenceAssertion', 'assertionId': iid,
             'evidenceStatus': 'rejected', 'assertionSubject': 'tdoc:' + row['source'],
             'assertionObject': 'tdoc:' + row['target'], 'assertionPredicateIRI': PREDICATE,
             'assessmentMethod': json.dumps({'method': 'source_registered_revision_qualification_v1',
                 'rawRegistrationFactStatus': 'source_verified', 'rawRegisteredValue': row['sourceCell']['rawValue'],
                 'interpretationScope': 'immediate_predecessor_inverse_only', 'classification': row['classification'],
                 'keptImmediatePredecessor': 'tdoc:' + row['keptParent'], 'assessment': row['assessment']}, ensure_ascii=False, sort_keys=True),
             'hasEvidence': []}
        for key in ('sourceCell', 'priorCell'):
            cell = row[key]
            props = {'evidencePath': cell['path'], 'evidenceSha256': cell['sha256'],
                     'evidenceLocator': f'XLSX {cell["sheet"]}!{cell["columnLetter"]}{cell["row"]}; physical row Tdoc={row["source"] if key == "sourceCell" else row["target"]}',
                     'evidenceQuote': cell['rawValue']}
            fid = 'tdoc:evidence/revision-' + hashlib.sha256(json.dumps(props, sort_keys=True).encode()).hexdigest()
            fragments[fid] = {'@id': fid, '@type': 'EvidenceFragment', **props}
            a['hasEvidence'].append(fid)
        assertions.append(a)
    return canonical_document({'@graph': [*assertions, *fragments.values()]}, wg=wg)


def write_evidence(root, wg, records, output_dir):
    document = evidence_document(records, wg)
    path = Path(output_dir) / EVIDENCE_FILE
    if document['@graph'] or path.exists():
        write_text_atomic(path, json.dumps(document, ensure_ascii=False, indent=2))
    return document


def preflight_revision_document(root, wg):
    directory = axis.tree_path('ontology_instances', wg=wg, phase=1, root=root)
    doc = json.loads((directory / 'tdocs.jsonld').read_text())
    nodes = copy.deepcopy(doc['@graph'])
    records = qualify_revisions(root, wg, nodes)
    if nodes != doc['@graph']:
        raise ValueError('Canonical revision claims need source qualification before loading')
    expected = evidence_document(records, wg)
    path = directory / EVIDENCE_FILE
    if (records and not path.exists()) or (path.exists() and json.loads(path.read_text()) != expected):
        raise ValueError('Canonical revision interpretation evidence differs from the validated source')
    return expected


def load_evidence(tx, document):
    """Materialize the qualification record, never its rejected immediate-lineage triple."""
    nodes = document['@graph']
    assertions = [n for n in nodes if n['@type'] == 'EvidenceAssertion']
    if not assertions:
        return
    ids = sorted({n[k] for n in assertions for k in ('assertionSubject', 'assertionObject')})
    found = tx.run('MATCH(n:Tdoc) WHERE n.id IN $ids RETURN n.id AS id, count(n) AS n', ids=ids).data()
    if {r['id']: r['n'] for r in found} != {id_: 1 for id_ in ids}:
        raise ValueError('Qualified revision evidence endpoint is absent/ambiguous')
    for node in nodes:
        label, identity = ('EvidenceAssertion', 'assertionId') if node['@type'] == 'EvidenceAssertion' else ('EvidenceFragment', 'evidenceId')
        props = {k: v for k, v in node.items() if not k.startswith('@') and k not in {'assertionSubject', 'assertionObject', 'hasEvidence'}}
        props.update(id=node['@id'])
        if label == 'EvidenceFragment':
            props[identity] = node['@id'].removeprefix('tdoc:evidence/')
        old = tx.run(f'MATCH(n:{label} {{{identity}:$key}}) RETURN properties(n) AS props', key=props[identity]).data()
        if old and (len(old) != 1 or any(old[0]['props'].get(k) != v for k, v in props.items())):
            raise ValueError('Existing revision qualification record differs; guarded reconciliation required')
        tx.run(f'MERGE(n:{label} {{{identity}:$key}}) SET n += $props', key=props[identity], props=props).consume()
    for a in assertions:
        tx.run('''MATCH(a:EvidenceAssertion {assertionId:$aid}),(s:Tdoc {id:$subject}),(o:Tdoc {id:$object})
           MERGE(a)-[:ASSERTION_SUBJECT]->(s) MERGE(a)-[:ASSERTION_OBJECT]->(o)''', aid=a['assertionId'], subject=a['assertionSubject'], object=a['assertionObject']).consume()
        for fid in a['hasEvidence']:
            tx.run('''MATCH(a:EvidenceAssertion {assertionId:$aid}),(e:EvidenceFragment {id:$fid})
               MERGE(a)-[:HAS_EVIDENCE]->(e)''', aid=a['assertionId'], fid=fid).consume()
    verify_evidence(tx, document)


def verify_evidence(tx, document):
    for node in document['@graph']:
        label = node['@type']
        actual = tx.run(f'MATCH(n:{label} {{id:$id}}) RETURN properties(n) AS p', id=node['@id']).data()
        expected = {k: v for k, v in node.items() if not k.startswith('@') and k not in {'assertionSubject', 'assertionObject', 'hasEvidence'}}
        if len(actual) != 1 or any(actual[0]['p'].get(k) != v for k, v in expected.items()):
            raise ValueError('Revision qualification property readback differs')
        if label == 'EvidenceAssertion':
            expected_edges = {('ASSERTION_SUBJECT', node['assertionSubject']), ('ASSERTION_OBJECT', node['assertionObject'])} | {('HAS_EVIDENCE', fid) for fid in node['hasEvidence']}
            edges = tx.run('''MATCH(a:EvidenceAssertion {id:$id})-[r]->(n)
              RETURN type(r) AS type,n.id AS id''', id=node['@id']).data()
            if len(edges) != len(expected_edges) or {(e['type'], e['id']) for e in edges} != expected_edges:
                raise ValueError('Revision qualification owned relation readback differs')
