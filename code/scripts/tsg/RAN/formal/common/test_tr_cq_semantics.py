#!/usr/bin/env python3
"""test_tr_cq_semantics.py — TR 원문에 명시된 주장과 인과 답변의 의미 계약 회귀.

Spec: docs/tsg/build/standards/tr_source_evidence_contract.md.
Ontology: claim ownership/type inventory is distinct from verified causal impact.
Cycle: maintained datasets/bootstrap → question-specific query contract.
배경: 후보의 종류 조회를 검증 완료 인과로 제한하거나 음성 주장을 승격하지 않는다.
사용: python3 -m unittest discover -s scripts/tsg/RAN/formal/common -p test_tr_cq_semantics.py.
LLM 호출: 없음.
"""
import hashlib
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path
import unittest

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / '.git').exists())


class TRQuestionMeaning(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.directory.cleanup)
        cls.root = Path(cls.directory.name)
        seeds = Path('scripts/common/bootstrap/seeds/formal-cq')
        shutil.copytree(ROOT / seeds, cls.root / seeds)
        scope = cls.root / 'logs/common/bootstrap/scope.json'
        scope.parent.mkdir(parents=True)
        scope.write_text(json.dumps({'wgs': [f'RAN{i}' for i in range(1, 6)]}))
        path = ROOT / 'scripts/common/bootstrap/materialize_formal_cq.py'
        spec = importlib.util.spec_from_file_location('tr_cq_materializer_fixture', path)
        materializer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(materializer)
        for number in range(1, 6):
            receipt = materializer.materialize(cls.root, f'RAN{number}')
            if receipt['status'] != 'definitions_ready':
                raise AssertionError('CQ materialization did not complete')

    def dataset(self, wg):
        return json.loads((self.root / f'logs/tsg/RAN/formal/{wg}/phase-5/cq_test_dataset.json').read_text())

    def test_inventory_preserves_candidate_status_and_bootstrap_projection(self):
        selected = {'RAN2': ['TR-CQ-2-2', 'TR-CQ-2-3', 'TR-CQ-2-4'],
                    'RAN3': ['TR-CQ-2-2', 'TR-CQ-2-3', 'TR-CQ-2-4', 'TR-CQ-5-3'],
                    'RAN4': ['CQ2-2'], 'RAN5': ['CQ2-2', 'CQ3-3']}
        for wg, ids in selected.items():
            current = {q['id']: q for q in self.dataset(wg)['questions']}
            bootstrap = {q['id']: q for q in json.loads((ROOT / f'scripts/common/bootstrap/seeds/formal-cq/{wg}/phase-5.json').read_text())['questions']}
            for identifier in ids:
                with self.subTest(wg=wg, identifier=identifier):
                    q = current[identifier]
                    self.assertIn('imp.evidenceStatus', q['cypher'])
                    self.assertIn('imp.verifiedImpactScope', q['cypher'])
                    self.assertNotIn("evidenceStatus: 'source_verified'", q['cypher'])
                    self.assertEqual(q['cypher'], bootstrap[identifier]['cypher'])
                    self.assertEqual(q['claim_contract'], bootstrap[identifier]['claim_contract'])

    def test_causal_and_bounded_negative_questions_retain_verified_gate(self):
        for wg in (f'RAN{i}' for i in range(1, 6)):
            for q in self.dataset(wg)['questions']:
                if ':IMPACTS_SPEC' in q['cypher'] or ':IMPACTS_SECTION' in q['cypher']:
                    with self.subTest(wg=wg, identifier=q['id']):
                        self.assertIn("evidenceStatus: 'source_verified'", q['cypher'])
        no_change = next(q for q in self.dataset('RAN5')['questions'] if q['id'] == 'CQ2-4')
        self.assertIn("impactType: 'NoChange', evidenceStatus: 'source_verified'", no_change['cypher'])

    def test_creation_and_extension_require_the_assessed_operation_scope(self):
        scopes = {'RAN1': {'CQ2-2': 'new_section', 'CQ2-5': 'new_specification', 'CQ3-2': 'new_section'},
                  'RAN4': {'CQ2-3': 'new_specification', 'CQ2-4': 'existing_section_change'},
                  'RAN5': {'CQ2-3': 'existing_section_change', 'CQ2-4': 'explicit_no_change'}}
        for wg, expected in scopes.items():
            current = {q['id']: q for q in self.dataset(wg)['questions']}
            for identifier, scope in expected.items():
                with self.subTest(wg=wg, identifier=identifier):
                    self.assertIn(f"verifiedImpactScope: '{scope}'", current[identifier]['cypher'])
        # These are authored scope contracts, not counts measured in a developer DB.
        # Exercise every supported scope against a temporary, hash-bound source.
        from tr_impact_evidence import VERIFIED_IMPACT_SCOPES, _verified_scope
        source = self.root / 'synthetic-scope.txt'
        source.write_text('Synthetic assessment of a source-bound operation.')
        evidence = {'path': source.relative_to(self.root).as_posix(),
                    'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                    'locator': 'paragraph 1', 'quote': source.read_text()}
        for scope in VERIFIED_IMPACT_SCOPES:
            with self.subTest(scope=scope):
                claim = {'impactType': 'NoChange' if scope == 'explicit_no_change' else 'ExtendSection'}
                entry = {'verifiedImpactScope': scope, 'scopeAssessment': {
                    'scope': scope, 'explanation': 'Synthetic assessed scope.', 'evidence': [evidence]}}
                self.assertEqual(_verified_scope(self.root, entry, claim), scope)
                changed = {**entry, 'scopeAssessment': {**entry['scopeAssessment'], 'scope': 'different'}}
                with self.assertRaisesRegex(ValueError, 'operation scope'):
                    _verified_scope(self.root, changed, claim)

    def test_research_result_returns_source_conclusion_without_inventing_no_change(self):
        q = next(q for q in self.dataset('RAN5')['questions'] if q['id'] == 'CQ3-3')
        self.assertIn('tr.conclusions', q['cypher'])
        self.assertIn('OPTIONAL MATCH', q['cypher'])
        self.assertIn('imp.evidenceStatus', q['cypher'])
        self.assertEqual(q['expected_min_rows'], 1)

    def test_scope_projection_preserves_aggregate_groups_and_claim_pairing(self):
        # A raw scope added beside collect/count becomes a Cypher grouping key.
        # Scope belongs inside each collected claim, or in its own set, so a TR
        # with both verified changes and a reuse remains one ownership group.
        for wg in ('RAN2', 'RAN3'):
            current = {q['id']: q for q in self.dataset(wg)['questions']}
            self.assertIn('count(imp) AS cnt, collect(DISTINCT imp.verifiedImpactScope)',
                          current['TR-CQ-2-2']['cypher'])
            self.assertIn('type: imp.impactType, verifiedScope: imp.verifiedImpactScope}',
                          current['TR-CQ-4-1']['cypher'])
        query = next(q['cypher'] for q in self.dataset('RAN3')['questions'] if q['id'] == 'TR-CQ-5-3')
        self.assertIn('evidenceStatus: imp.evidenceStatus, verifiedScope: imp.verifiedImpactScope}', query)
        self.assertNotIn('AS claims, imp.verifiedImpactScope', query)


if __name__ == '__main__':
    unittest.main()
