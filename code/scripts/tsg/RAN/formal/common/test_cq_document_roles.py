#!/usr/bin/env python3
"""Summary 문서와 Resolution 결정의 서로 다른 provenance 역할을 검사한다.

Spec: docs/common/process/spectra_operations_rulebook.md §3.1, §4.1.
Ontology: Summary/SessionNotes는 Tdoc; MADE_AT은 Resolution 역할이다.
Cycle: typed Cypher → 역할 검사 → canonical 관계로 실제 조회.
배경: 존재하는 관계 이름도 다른 역할에 조인하면 0건을 만들 수 있다.
사용: python3 -m unittest discover -s scripts/tsg/RAN/formal/common -p test_cq_document_roles.py
LLM 호출: 없음.
"""
import json
from pathlib import Path
import unittest
from cq_anchor_guard import document_role_defects


class DocumentRoles(unittest.TestCase):
    def test_wrong_summary_role_is_rejected(self):
        query = 'MATCH(s:Summary)-[:RESOLUTION_BELONGS_TO]->(a:AgendaItem) MATCH(s)-[:MADE_AT]->(m:Meeting) RETURN s'
        self.assertEqual(len(document_role_defects(query)), 2)

    def test_correct_document_and_decision_roles_are_accepted(self):
        self.assertEqual(document_role_defects('MATCH(s:Summary)-[:BELONGS_TO]->(a) MATCH(s)-[:PRESENTED_AT]->(m) MATCH(r:Agreement)-[:MADE_AT]->(m) RETURN s,r'), [])

    def test_unrelated_decision_variable_and_literals_are_opaque(self):
        self.assertEqual(document_role_defects("MATCH(s:Summary) MATCH(r:Resolution)-[:MADE_AT]->(m) RETURN '(s)-[:MADE_AT]->(m)' // (s)-[:MADE_AT]->(m)"), [])

    def test_session_notes_document_role_is_checked(self):
        self.assertTrue(document_role_defects('MATCH(s:SessionNotes) MATCH(s)-[r:MADE_AT]->(m) RETURN m'))

    def test_all_core_document_subclasses_and_reversed_patterns_are_checked(self):
        for kind in ('Tdoc', 'CR', 'LS', 'Summary', 'SessionNotes'):
            with self.subTest(kind=kind):
                self.assertEqual(len(document_role_defects(f'MATCH(d:{kind}) MATCH(m:Meeting)<-[:MADE_AT]-(d) RETURN d')), 1)
                self.assertEqual(len(document_role_defects(f'MATCH(a:AgendaItem)-[:HAS_RESOLUTIONS]->(d:{kind}) RETURN d')), 1)

    def test_decision_subclasses_cannot_use_document_provenance(self):
        for kind in ('Resolution', 'Agreement', 'Conclusion', 'WorkingAssumption'):
            with self.subTest(kind=kind):
                self.assertEqual(len(document_role_defects(f'MATCH(m:Meeting)<-[:PRESENTED_AT]-(d:{kind}) RETURN d')), 1)

    def test_anonymous_nodes_have_independent_inline_roles(self):
        self.assertEqual(document_role_defects('MATCH(:Summary) MATCH(:Resolution)-[:MADE_AT]->(m:Meeting) RETURN m'), [])
        self.assertEqual(len(document_role_defects('MATCH(:CR)-[:MADE_AT]->(m:Meeting) RETURN m')), 1)

    def test_all_current_cqs_obey_document_decision_role_contract(self):
        root = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
        count = 0
        for path in (root / 'scripts/common/bootstrap/seeds/formal-cq').glob('RAN[1-5]/phase-[1-5].json'):
            for question in json.loads(path.read_text())['questions']:
                self.assertEqual(document_role_defects(question['cypher']), [], (str(path), question['id']))
                count += 1
        self.assertEqual(count, 654)

    def test_current_summary_cqs_use_document_relations(self):
        root = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
        questions = json.loads((root / 'scripts/common/bootstrap/seeds/formal-cq/RAN3/phase-2.json').read_text())['questions']
        summary = [q for q in questions if ':Summary' in q['cypher']]
        self.assertEqual(len(summary), 4)
        self.assertTrue(all(not document_role_defects(q['cypher']) for q in summary))


if __name__ == '__main__':
    unittest.main()
