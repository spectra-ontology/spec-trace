#!/usr/bin/env python3
"""Metadata filter checks use observed collection payloads and fake Qdrant calls.

The actual validator functions are extracted with AST; no production imports,
documents, models or services are used.
"""
import argparse
import ast
from collections import defaultdict
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime
import io
import json
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest


ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
SOURCE = ROOT / 'scripts/tsg/RAN/formal/RAN3/phase-6/validation/02_validate_metadata_filters.py'


class Model:
    def __init__(self, **values):
        self.__dict__.update(values)


class FakeClient:
    def __init__(self, payloads, wrong_positive=False, negative_overreturn=False):
        self.payloads = payloads
        self.calls = []
        self.close_count = 0
        self.empty_positive = False
        self.scroll_error = None
        self.error_on_filtered = False
        self.wrong_positive = wrong_positive
        self.negative_overreturn = negative_overreturn

    def matching(self, query):
        if query is None:
            return self.payloads
        def matches(payload):
            for condition in query.must:
                actual = payload.get(condition.key)
                if hasattr(condition.match, 'any'):
                    if not isinstance(actual, list) or not any(v in actual for v in condition.match.any):
                        return False
                elif actual != condition.match.value:
                    return False
            return True
        return [p for p in self.payloads if matches(p)]

    def count(self, **kwargs):
        self.calls.append(('count', kwargs))
        selected = self.matching(kwargs.get('count_filter'))
        return SimpleNamespace(count=len(selected) or int(self.negative_overreturn))

    def close(self):
        self.close_count += 1

    def scroll(self, **kwargs):
        if self.scroll_error is not None and (not self.error_on_filtered or kwargs.get("scroll_filter") is not None):
            raise self.scroll_error
        self.calls.append(('scroll', kwargs))
        query = kwargs.get('scroll_filter')
        selected = self.matching(query)
        if query is not None and (self.wrong_positive or (self.negative_overreturn and not selected)):
            selected = [{'source': ['WRONG'], 'meetingId': 'WRONG', 'agendaItem': 'WRONG',
                         'release': 'WRONG', 'type': 'WRONG', 'tdocNumber': 'synthetic-wrong'}]
        if self.empty_positive and query is not None:
            selected = []
        return [SimpleNamespace(payload=p) for p in selected[:kwargs['limit']]], None


class MetadataFilterScopeTests(unittest.TestCase):
    wg = "RAN3"
    def run_main(self, payloads, args=(), **faults):
        options = {key: faults.pop(key) for key in list(faults) if key in {"empty_positive", "scroll_error", "error_on_filtered"}}
        client = FakeClient(payloads, **faults)
        for key, value in options.items():
            setattr(client, key, value)
        self.last_client = client
        source = Path(str(SOURCE).replace("RAN3/", self.wg + "/"))
        tree = ast.parse(source.read_text(), filename=str(source))
        constants = {'QDRANT_HOST', 'QDRANT_PORT', 'COLLECTION_NAME', 'DEFAULT_WG',
                     'SINGLE_FILTER_TESTS', 'COMBINED_FILTER_TESTS'}
        nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) or
                 isinstance(n, ast.Assign) and all(isinstance(t, ast.Name) and t.id in constants for t in n.targets)]
        with tempfile.TemporaryDirectory(prefix='spectra-filter-scope-') as temporary:
            namespace = dict(argparse=argparse, defaultdict=defaultdict, datetime=datetime,
                             json=json, Path=Path, sys=sys, time=time,
                             QdrantClient=lambda **kwargs: client,
                             Filter=Model, FieldCondition=Model, MatchValue=Model, MatchAny=Model,
                             LOG_DIR=Path(temporary),
                             axis=SimpleNamespace(qdrant_collection=lambda wg, family: self.wg.lower() + '_tdoc_chunks'))
            helper = ROOT / "scripts/common/common/metadata_filter_scope.py"
            if helper.exists():
                exec(compile(ast.parse(helper.read_text()), str(helper), "exec"), namespace)
            exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), namespace)
            previous_argv = sys.argv
            sys.argv = [str(SOURCE), *args]
            try:
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    try:
                        code = namespace['main']()
                    except SystemExit as error:
                        code = error.code
            finally:
                sys.argv = previous_argv
            reports = list(Path(temporary).rglob('level3_filter_validation_*.json'))
            report = json.loads(reports[0].read_text()) if reports else None
        self.assertFalse(Path(temporary).exists())
        return code, report, client.calls

    @staticmethod
    def payload():
        return {'source': ['SelectedCompany'], 'meetingId': 'RAN3#140', 'agendaItem': '4.7',
                'release': 'Rel-19', 'type': 'selected_type', 'tdocNumber': 'synthetic'}

    def test_selected_collection_drives_positive_and_coherent_combined_cases(self):
        code, report, calls = self.run_main([self.payload()])
        self.assertEqual(code, 0)
        self.assertTrue(report['summary']['overall_pass'])
        positives = [r for r in report['single_filter_tests'] if r['count'] > 0]
        self.assertEqual(len(positives), 5)
        self.assertTrue(report['combined_filter_tests'])
        self.assertTrue(all(r['count'] > 0 and r['accuracy'] == 'PASS' for r in report['combined_filter_tests']))
        self.assertEqual({c['collection_name'] for _, c in calls}, {self.wg.lower() + '_tdoc_chunks'})

    def test_negative_collision_and_wrong_payload_are_checked(self):
        collided = dict(source=['NonExistentCompany'], meetingId=self.wg + '#999', agendaItem='99.99.99',
                        release='Rel-99', type='unknown_type')
        code, report, _ = self.run_main([collided])
        self.assertEqual(code, 0)
        self.assertTrue(any(r['accuracy'] == 'PASS(빈 결과 예상)' for r in report['single_filter_tests']))
        for faults in [{'wrong_positive': True}, {'negative_overreturn': True}]:
            with self.subTest(faults=faults):
                code, report, _ = self.run_main([self.payload()], **faults)
                self.assertEqual(code, 1)
                self.assertTrue(any(r['accuracy'] == 'FAIL' for r in report['single_filter_tests']))

    def test_empty_and_unsupported_collections_fail_without_positive_samples(self):
        for payloads in [[], [{'unrelated': 'value'}]]:
            with self.subTest(payloads=payloads):
                code, report, _ = self.run_main(payloads)
                self.assertEqual(code, 1)
                self.assertIn('sample_support', report)
                self.assertEqual(report['sample_support']['positive_cases'], 0)
        code, report, _ = self.run_main([{'source': ['OnlySource']}])
        self.assertEqual(code, 0)
        self.assertEqual(set(report['sample_support']['unsupported_fields']), {'meetingId', 'agendaItem', 'release', 'type'})

    def test_collection_option_and_payload_read_bounds_are_wired(self):
        code, report, calls = self.run_main([self.payload()], ['--collection', 'selected_chunks'])
        self.assertEqual(code, 0)
        self.assertEqual(report['collection'], 'selected_chunks')
        self.assertEqual({c['collection_name'] for _, c in calls}, {'selected_chunks'})
        scrolls = [c for kind, c in calls if kind == 'scroll']
        self.assertEqual(scrolls[0]['limit'], 100)
        self.assertTrue(all(c['with_vectors'] is False and c['with_payload'] is True for c in scrolls))
        self.assertTrue(all(c['limit'] <= 1000 for c in scrolls))


    def test_positive_count_requires_nonempty_accuracy_samples(self):
        code, report, _ = self.run_main([dict(self.payload(), source=['Ericsson'])], empty_positive=True)
        self.assertEqual(code, 1)
        self.assertTrue(any(r['count'] > 0 and r['accuracy'] == 'FAIL'
                            for r in report['single_filter_tests']))

    def test_client_closes_once_on_success_query_fault_and_interrupt(self):
        self.run_main([self.payload()])
        self.assertEqual(self.last_client.close_count, 1)
        for error, filtered in [(OSError('synthetic-query'), False),
                                (KeyboardInterrupt('synthetic-interrupt'), True)]:
            with self.subTest(error=type(error).__name__):
                with self.assertRaises(type(error)) as caught:
                    self.run_main([self.payload()], scroll_error=error, error_on_filtered=filtered)
                self.assertIs(caught.exception, error)
                self.assertEqual(self.last_client.close_count, 1)

    def test_historical_cases_remain_explicit(self):
        _, report, _ = self.run_main([self.payload()], ['--historical-fixtures'])
        self.assertIsNotNone(report, 'historical option must produce a report')
        self.assertEqual(report['sample_support']['mode'], 'historical')
        self.assertEqual(len(report['single_filter_tests']), 19)
        self.assertEqual(len(report['combined_filter_tests']), 5)


class Ran4MetadataFilterScopeTests(MetadataFilterScopeTests):
    wg = 'RAN4'


class Ran5MetadataFilterScopeTests(MetadataFilterScopeTests):
    wg = 'RAN5'


if __name__ == '__main__':
    unittest.main()
