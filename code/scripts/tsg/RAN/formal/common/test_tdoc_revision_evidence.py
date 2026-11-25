#!/usr/bin/env python3
"""test_tdoc_revision_evidence.py — immediate lineage and retained registration regressions.

Spec: selected XLSX prior/forward cells and revision qualification ledger.
Ontology: inverse functional-cardinality consequences, source claim versus interpretation.
Cycle: synthetic source fixture → canonical qualification → RDF/guard counterexamples.
배경: final replacements and merge inputs must retain their source without collapsing identities.
사용: python -m unittest discover -s scripts/tsg/RAN/formal/common -p test_tdoc_revision_evidence.py.
LLM 호출: none; all fixtures are local and database-free.
"""
from contextlib import ExitStack
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import openpyxl
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import OWL
from owlrl import DeductiveClosure, OWLRL_Semantics

import tdoc_revision_evidence as e
import reconcile_tdoc_revisions as reconcile
from common import review_artifacts


def record():
    cell = {'path': 'master.xlsx', 'sha256': 'x', 'sheet': 'TDoc_List', 'row': 2,
            'column': 3, 'headerColumn': 3, 'columnLetter': 'C', 'rawValue': 'R3-3'}
    prior = {**cell, 'row': 3, 'column': 2, 'headerColumn': 2, 'columnLetter': 'B', 'rawValue': 'R3-2'}
    return {'source': 'R3-1', 'target': 'R3-3', 'keptParent': 'R3-2',
            'classification': 'ancestor_final_target', 'assessment': 'Explicit own predecessor is the intermediate.',
            'interpretationStatus': 'rejected', 'sourceCell': cell, 'priorCell': prior}


def nodes():
    return [{'@id': 'tdoc:R3-1', 'revisedTo': ['tdoc:R3-2', 'tdoc:R3-3'], 'unknown': 42},
            {'@id': 'tdoc:R3-2', 'isRevisionOf': 'tdoc:R3-1', 'revisedTo': 'tdoc:R3-3'},
            {'@id': 'tdoc:R3-3', 'isRevisionOf': 'tdoc:R3-2'}]


class RevisionQualification(unittest.TestCase):
    def setUp(self):
        self.contexts = ExitStack()
        self.addCleanup(self.contexts.close)

    def test_forward_cell_requires_a_complete_document_identifier(self):
        target = 'R3-123456'
        for raw, valid in ((target, True), ('[' + target + ']', True),
                           (target + 'X', False), ('x' + target, False),
                           (target + '-2', False), (target + '_2', False)):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source = root / 'tiny.xlsx'
                book = openpyxl.Workbook()
                try:
                    sheet = book.active
                    sheet.title = 'TDoc_List'
                    sheet.append(['TDoc', 'Is revision of', 'Revised to'])
                    sheet.append(['R3-654321', '', raw])
                    sheet.append([target, 'R3-111111', ''])
                    book.save(source)
                finally:
                    book.close()
                row = record()
                row.update(source='R3-654321', target=target, keptParent='R3-111111')
                for key in ('sourceCell', 'priorCell'):
                    row[key].update(path='tiny.xlsx', sha256=e.sha(source))
                row['sourceCell']['rawValue'] = raw
                row['priorCell']['rawValue'] = 'R3-111111'
                ledger = e.ledger_path(root, 'RAN3')
                ledger.parent.mkdir(parents=True)
                ledger.write_text(json.dumps({'workingGroup': 'RAN3',
                    'contract': 'immediate_predecessor_from_own_registered_row_v1', 'reviews': [row]}))
                if valid:
                    self.assertEqual(e.validated_reviews(root, 'RAN3'), [row])
                else:
                    with self.assertRaisesRegex(ValueError, 'forward target'):
                        e.validated_reviews(root, 'RAN3')

    def test_reviewed_final_target_preserves_other_branch_and_source_value(self):
        n, r = nodes(), record(); raw = copy.deepcopy(r)
        active = e.qualify_revisions(Path('.'), 'RAN3', n, reviews=[r])
        self.assertEqual(n[0], {'@id': 'tdoc:R3-1', 'revisedTo': ['tdoc:R3-2'], 'unknown': 42})
        self.assertEqual(r, raw)
        self.assertEqual(active, [r]); self.assertEqual(e.revision_conflicts(n), {})

    def test_direct_branching_from_one_parent_remains_supported(self):
        n = [{'@id': 'tdoc:A', 'revisedTo': ['tdoc:B', 'tdoc:C']}, {'@id': 'tdoc:B', 'isRevisionOf': 'tdoc:A'}, {'@id': 'tdoc:C', 'isRevisionOf': 'tdoc:A'}]
        before = copy.deepcopy(n); self.assertEqual(e.qualify_revisions(Path('.'), 'RAN1', n, reviews=[]), []); self.assertEqual(n, before)

    def test_unknown_conflict_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'Unreviewed'):
            e.qualify_revisions(Path('.'), 'RAN3', nodes(), reviews=[])

    def test_changed_own_predecessor_fails_closed(self):
        n = nodes(); n[-1]['isRevisionOf'] = 'tdoc:R3-1'
        with self.assertRaisesRegex(ValueError, 'Own immediate'):
            e.qualify_revisions(Path('.'), 'RAN3', n, reviews=[record()])

    def test_qualification_idempotent_and_selected_subset_supported(self):
        n = nodes(); e.qualify_revisions(Path('.'), 'RAN3', n, reviews=[record()]); before = copy.deepcopy(n)
        e.qualify_revisions(Path('.'), 'RAN3', n, reviews=[record()]); self.assertEqual(n, before)
        self.assertEqual(e.qualify_revisions(Path('.'), 'RAN3', n[:1], reviews=[record()]), [])

    def test_rejected_interpretation_keeps_literal_source_fact_and_no_direct_edge(self):
        doc = e.evidence_document([record()], 'RAN3'); g = Graph().parse(data=json.dumps(doc), format='json-ld')
        t = Namespace('https://w3id.org/spectra#')
        self.assertFalse(list(g.triples((t['R3-1'], t.revisedTo, t['R3-3']))))
        self.assertIn('"rawRegistrationFactStatus": "source_verified"', doc['@graph'][0]['assessmentMethod'])
        self.assertEqual(doc['@graph'][0]['evidenceStatus'], 'rejected')
        self.assertEqual({n.get('evidenceQuote') for n in doc['@graph'][1:]}, {'R3-3', 'R3-2'})

    def test_owl_inverse_no_longer_entails_distinct_prior_equality(self):
        t = Namespace('https://w3id.org/spectra#')
        def infer(n):
            g = Graph(); g.add((t.isRevisionOf, OWL.inverseOf, t.revisedTo)); g.add((t.isRevisionOf, URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), OWL.FunctionalProperty))
            for item in n:
                for prop in ('revisedTo', 'isRevisionOf'):
                    for target in e.values(item.get(prop)):
                        g.add((t[item['@id'].removeprefix('tdoc:')], t[prop], t[target.removeprefix('tdoc:')]))
            DeductiveClosure(OWLRL_Semantics).expand(g); return g
        n = nodes(); self.assertIn((t['R3-1'], OWL.sameAs, t['R3-2']), infer(n))
        e.qualify_revisions(Path('.'), 'RAN3', n, reviews=[record()]); self.assertNotIn((t['R3-1'], OWL.sameAs, t['R3-2']), infer(n))

    def test_real_physical_source_cells_then_sha_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); p = root / 'master.xlsx'; book = openpyxl.Workbook(); sh = book.active; sh.title = 'TDoc_List'
            sh.append(['TDoc', 'Is revision of', 'Revised to']); sh.append(['R3-1', '', 'R3-3']); sh.append(['R3-3', 'R3-2', '']); book.save(p)
            r = record()
            for key in ('sourceCell', 'priorCell'): r[key]['sha256'] = e.sha(p)
            path = e.ledger_path(root, 'RAN3'); path.parent.mkdir(parents=True)
            path.write_text(json.dumps({'workingGroup': 'RAN3', 'contract': 'immediate_predecessor_from_own_registered_row_v1', 'reviews': [r]}))
            self.assertEqual(len(e.validated_reviews(root, 'RAN3')), 1)
            sh['C2'] = 'R3-4'; book.save(p)
            with self.assertRaisesRegex(ValueError, 'SHA changed'): e.validated_reviews(root, 'RAN3')

    def test_retained_native_sources_keep_ledger_bytes_and_current_fences(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = str(review_artifacts.LEGACY_REVIEW_ROOT / 'synthetic-old/conversion.json')
            new = 'logs/common/RAN3/verification/ontology-system-review/synthetic-current/conversion.json'
            self.contexts.enter_context(patch.object(review_artifacts, 'RECORDED_FILE_RELOCATIONS', {old: new}))
            target = root / new
            target.parent.mkdir(parents=True)
            target.write_bytes(b'{"retained":true}')
            digest = e.sha(target)
            ledger = e.ledger_path(root, 'RAN3')
            ledger.parent.mkdir(parents=True)
            ledger.write_text(json.dumps({
                'workingGroup': 'RAN3',
                'contract': 'immediate_predecessor_from_own_registered_row_v1',
                'reviews': [],
                'additionalSourceInputs': [{'path': old, 'sha256': digest}],
            }))
            before = ledger.read_bytes()
            sources = e.source_inputs(root, 'RAN3')
            self.assertNotIn(old, sources)
            self.assertEqual(sources[new], digest)
            self.assertEqual(e.validated_reviews(root, 'RAN3'), [])
            self.assertEqual(ledger.read_bytes(), before)
            target.write_bytes(b'changed source')
            with self.assertRaisesRegex(ValueError, 'SHA256'):
                e.source_inputs(root, 'RAN3')
            target.write_bytes(b'{"retained":true}')
            original = root / old
            original.parent.mkdir(parents=True)
            original.write_bytes(target.read_bytes())
            with self.assertRaisesRegex(ValueError, 'ambiguous'):
                e.source_inputs(root, 'RAN3')
            original.unlink()
            target.unlink()
            with self.assertRaises(FileNotFoundError):
                e.source_inputs(root, 'RAN3')
            self.assertEqual(ledger.read_bytes(), before)

    def test_wrong_physical_row_identity_rejected_even_with_matching_quote(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); p = root / 'master.xlsx'; book = openpyxl.Workbook(); sh = book.active; sh.title = 'TDoc_List'
            sh.append(['TDoc', 'Is revision of', 'Revised to']); sh.append(['R3-999', '', 'R3-3']); sh.append(['R3-3', 'R3-2', '']); book.save(p)
            r = record()
            for key in ('sourceCell', 'priorCell'): r[key]['sha256'] = e.sha(p)
            path = e.ledger_path(root, 'RAN3'); path.parent.mkdir(parents=True); path.write_text(json.dumps({'workingGroup': 'RAN3', 'contract': 'immediate_predecessor_from_own_registered_row_v1', 'reviews': [r]}))
            with self.assertRaisesRegex(ValueError, 'identity changed'): e.validated_reviews(root, 'RAN3')

    def test_qualification_foreign_edge_is_preserved(self):
        old = {'nodes': [], 'edges': [{'startId': 'tdoc:foreign', 'type': 'REFERENCES', 'endId': 'tdoc:R3-3'}]}
        new = copy.deepcopy(old); new['edges'].append({'startId': 'tdoc:assertion/RAN3:revision-source:R3-1:R3-3', 'type': 'ASSERTION_OBJECT', 'endId': 'tdoc:R3-3'})
        reconcile.check_owned_qualification_delta(old, new, e.evidence_document([record()], 'RAN3'))
        new['edges'].pop(0)
        with self.assertRaisesRegex(ValueError, 'unrelated incident'): reconcile.check_owned_qualification_delta(old, new, e.evidence_document([record()], 'RAN3'))

    def test_changed_selection_replaces_stale_evidence_with_exact_empty_document(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / e.EVIDENCE_FILE).write_text(json.dumps(e.evidence_document([record()], 'RAN3')))
            (directory / 'tdocs.jsonld').write_text(json.dumps({'@graph': []}))
            with patch.object(e.axis, 'tree_path', return_value=directory), patch.object(e, 'validated_reviews', return_value=[]):
                with self.assertRaisesRegex(ValueError, 'evidence differs'):
                    e.preflight_revision_document(directory, 'RAN3')
                e.write_evidence(directory, 'RAN3', [], directory)
                self.assertEqual(e.preflight_revision_document(directory, 'RAN3')['@graph'], [])


if __name__ == '__main__':
    unittest.main()
