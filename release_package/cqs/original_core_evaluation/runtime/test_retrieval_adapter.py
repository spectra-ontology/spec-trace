"""Synthetic adapter checks; no model, graph gold or historical outputs used."""
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import retrieval_adapter as a


class FakeCaller:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def call(self, request_id, messages, max_tokens=8192):
        self.calls.append({'id': request_id, 'messages': messages, 'max_tokens': max_tokens})
        value = self.responses.pop(0)
        return {'ok': True, 'provider': 'synthetic', 'finish_reason': 'stop',
                'usage': {'prompt_tokens': 10, 'completion_tokens': 10},
                'content': json.dumps(value), **({'finish_reason': 'length'} if value.get('_length') else {})}


class RetrievalAdapterTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.corpus = self.base / 'corpus'
        self.corpus.mkdir()
        for i in range(1, 6):
            c = sqlite3.connect(self.corpus / ('ran' + str(i) + '.sqlite3'))
            c.execute('CREATE TABLE docs(id INTEGER PRIMARY KEY,collection TEXT,point_id TEXT,chunk_id TEXT,metadata TEXT,text TEXT)')
            c.execute("CREATE VIRTUAL TABLE search USING fts5(text,content='docs',content_rowid='id',tokenize='unicode61 remove_diacritics 2')")
            for n, text in enumerate(['needle points to target alpha', 'target alpha links synthetic-result', 'needle ' + 'long source ' * 1000], 1):
                c.execute('INSERT INTO docs VALUES(?,?,?,?,?,?)', (n, 'ran' + str(i) + '_ts_sections', str(n), 'synthetic-' + str(n), json.dumps({'specNumber': 'synthetic'}), text))
                c.execute('INSERT INTO search(rowid,text) VALUES(?,?)', (n, text))
            c.commit()
            c.close()
        self.task = {'id': 'SYNTHETIC_Q', 'WG': 'RAN1', 'repair_sha256': 'opaque-identity-not-for-reader',
                     'question_en': 'List needle records.',
                     'required_fields': [{'name': 'answer', 'type': 'string', 'nullable': False,
                                          'source_column_or_expression': 'native_alias_not_for_reader'}],
                     'collection': {'kind': 'set'}, 'cardinality_policy': {'mode': 'all', 'notes': 'not for reader'}}
        self.patcher = patch.object(a, 'CORPUS_DIR', self.corpus)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.temp.cleanup()

    def test_single_call_and_no_opaque_or_native_alias_leak(self):
        caller = FakeCaller([{'records': [{'answer': 'synthetic-result'}], 'abstain': False, 'complete': False}])
        result = a.evaluate(self.task, 'C', caller, self.base / 'single')
        self.assertEqual(result['status'], 'partial')
        self.assertEqual(len(caller.calls), 1)
        self.assertEqual(result['repair_sha256'], self.task['repair_sha256'])
        serialized = json.dumps(caller.calls)
        self.assertNotIn('opaque-identity', serialized)
        self.assertNotIn('native_alias', serialized)
        self.assertLessEqual(result['context_stats']['characters'], 48000)
        self.assertEqual(result['source_cutoff_relation_to_frozen_graph'], 'UNKNOWN')

    def test_iterative_exactly_two_model_calls_and_two_retrievals(self):
        caller = FakeCaller([{'query': 'target alpha'}, {'records': [{'answer': 'synthetic-result'}], 'abstain': False, 'complete': True}])
        result = a.evaluate(self.task, 'D', caller, self.base / 'iterative')
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(len(caller.calls), 2)
        self.assertEqual(caller.calls[0]['max_tokens'], 1024)
        self.assertEqual(caller.calls[1]['max_tokens'], 8192)
        self.assertEqual(len(result['retrieval_statuses']), 2)
        context = json.loads((self.base / 'iterative/retrieval/D/SYNTHETIC_Q/final_context.json').read_text())
        self.assertTrue(any(d['point_id'] == '2' for d in context['documents']))
        self.assertTrue(all(len(d['formatted']) <= 4000 for d in context['documents']))

    def test_output_length_failure_is_not_salvaged_or_retried(self):
        caller = FakeCaller([{'records': [{'answer': 'partial'}], 'abstain': False, 'complete': True, '_length': True}])
        result = a.evaluate(self.task, 'C', caller, self.base / 'length')
        self.assertEqual(result['status'], 'output_truncated')
        self.assertEqual(result['records'], [])
        self.assertEqual(len(caller.calls), 1)

    def test_missing_requested_field_is_not_synthetically_completed(self):
        caller = FakeCaller([{'records': [{}], 'abstain': False, 'complete': True}])
        result = a.evaluate(self.task, 'C', caller, self.base / 'missing')
        self.assertEqual(result['records'], [{}])
        self.assertFalse(result['requested_population_completeness_verified'])

    def test_input_gold_and_schema_hints_rejected_before_call(self):
        caller = FakeCaller([])
        with self.assertRaises(ValueError):
            a.evaluate(dict(self.task, reference_query='gold query'), 'C', caller, self.base / 'leak')
        with self.assertRaises(ValueError):
            a.structural_schema({'type': 'string', 'enum': ['gold']})
        self.assertEqual(caller.calls, [])

    def test_bounded_query_and_nonfinite_output(self):
        compiled = a.lexical_expression(' '.join('word' + str(i) for i in range(80)), 32)
        self.assertTrue(compiled['terms_truncated'])
        self.assertEqual(len(compiled['terms']), 32)
        with self.assertRaises(ValueError):
            a.parse_answer('{"records":[{"answer":NaN}],"abstain":false,"complete":true}')

    def test_nested_set_contract_and_requested_order_are_preserved(self):
        task = dict(self.task, required_fields=[
            {'name': 'items', 'type': 'json', 'nullable': False,
             'json_schema': {'type': 'array', 'items': {'type': 'string'}},
             'nested_array_semantics': {'$': 'set'}}],
            collection={'kind': 'ordered', 'order_keys': [{'field': 'items', 'direction': 'asc'}]})
        contract = a.public_contract(task)
        self.assertEqual(contract['required_fields'][0]['nested_array_semantics'], {'$': 'set'})
        self.assertEqual(contract['collection']['order_keys'], task['collection']['order_keys'])
        with self.assertRaises(ValueError):
            a.structural_schema({'type': 'object', 'additionalProperties': {'enum': ['gold']}})


if __name__ == '__main__':
    unittest.main()
