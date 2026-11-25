"""Bounded reference selection tests; source text and identifiers stay intact."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from scripts.common.common.search_evidence import (
    candidate_limit, reference_only_targets, select_body_evidence,
)

ROOT = Path(__file__).resolve().parents[3]
STUB = 'Example input processing is described in clause 7.4.3.'


class SearchEvidenceTests(unittest.TestCase):
    def test_reference_sentence_is_identified_but_short_definitions_survive(self):
        self.assertEqual(reference_only_targets(STUB), ['7.4.3'])
        self.assertEqual(reference_only_targets('See clauses 4.4.3 and 4.4.4.'), ['4.4.3', '4.4.4'])
        for body in ('A block contains twelve subcarriers.',
                     'The value shall be one. See clause 4.4.3.',
                     'The rule is specified in clause 4.4.3. A different value is permitted.'):
            self.assertEqual(reference_only_targets(body), [])
            self.assertEqual(select_body_evidence([{'text': body}])[0]['text'], body)

    def test_stub_selection_preserves_source_and_explicit_reference_access(self):
        source = [{'chunkId': 'ref', 'text': STUB, 'score': .9},
                  {'chunkId': 'body', 'text': 'A resource block has twelve subcarriers.', 'score': .8}]
        selected = select_body_evidence(source)
        self.assertEqual([r['chunkId'] for r in selected], ['body'])
        self.assertEqual(selected[0]['score'], .8)
        self.assertNotIn('evidence_kind', source[0])
        self.assertEqual(source[0]['text'], STUB)
        explicit = select_body_evidence(source, include_references=True)
        self.assertEqual(explicit[0]['evidence_kind'], 'reference_only')
        self.assertEqual(explicit[0]['reference_targets'], ['7.4.3'])
        self.assertEqual(select_body_evidence(source[:1]), [])

    def test_content_field_precedence_and_bounded_window(self):
        payload = {'text': STUB, 'content': 'The actual value is twelve.'}
        self.assertEqual(select_body_evidence([payload]), [])
        self.assertEqual(len(select_body_evidence([payload], text_keys=('content', 'text'))), 1)
        self.assertEqual(candidate_limit(5), 40)
        self.assertEqual(candidate_limit(512), 512)
        for invalid in (None, True, 0, -1, 513, 1.5):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                candidate_limit(invalid)

    def test_all_five_ts_search_clients_look_past_repeated_reference_stubs(self):
        for wg in range(1, 6):
            with self.subTest(wg=wg):
                path = ROOT / f'scripts/tsg/RAN/formal/RAN{wg}/phase-7/validation/01_validate_search.py'
                node = next(n for n in ast.parse(path.read_text()).body
                            if isinstance(n, ast.ClassDef) and n.name == 'SearchClient')
                env = {'Config': object, 'Filter': lambda **kw: SimpleNamespace(**kw),
                       'FieldCondition': lambda **kw: SimpleNamespace(**kw),
                       'MatchValue': lambda **kw: SimpleNamespace(**kw),
                       'candidate_limit': candidate_limit, 'select_body_evidence': select_body_evidence}
                exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), env)
                client = object.__new__(env['SearchClient'])
                client.config = SimpleNamespace(top_k=5, collection_name=f'ran{wg}_ts_sections', use_rerank=False)
                client.embed_query = Mock(return_value=[.1])
                points = [SimpleNamespace(payload={'text': STUB, 'sectionId': 'ref', 'chunkId': str(n)}, score=.9)
                          for n in range(5)]
                points.append(SimpleNamespace(payload={'text': 'Twelve subcarriers form a resource block.',
                                                       'sectionId': '38.211-4.4.4.1', 'chunkId': 'body'}, score=.8))
                client.qdrant = SimpleNamespace(query_points=Mock(return_value=SimpleNamespace(points=points)))
                hits = client.search('resource blocks', top_k=5)
                self.assertEqual([h['chunkId'] for h in hits], ['body'])
                self.assertEqual(hits[0]['score'], .8)
                self.assertEqual(client.qdrant.query_points.call_args.kwargs['limit'], 40)


if __name__ == '__main__':
    unittest.main()
