"""Caller-owned disposition transactions retain one atomic data generation.

These fixtures reject nested Session writes and schema queries inside a data
transaction. Real Neo4j commit/rollback is checked separately in private smoke.
"""
from contextlib import ExitStack, redirect_stdout
import ast
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import decision_disposition as disposition
import document_decision_storage as storage


class Result:
    def __init__(self, value=None):
        self.value = value

    def consume(self):
        return None

    def single(self):
        return self.value

    def data(self):
        return self.value


class NoSessionWrites:
    def run(self, *args, **kwargs):
        raise AssertionError('caller data escaped its transaction')

    def execute_write(self, *args, **kwargs):
        raise AssertionError('nested transaction')


class CallerDispositionTransactionTests(unittest.TestCase):
    def test_reconciler_coverage_publication_preserves_previous_file_and_retries(self):
        import common.atomic_io as atomic_io
        import reconcile_decision_dispositions as reconciler

        class Transaction:
            def run(self, query, **kwargs):
                if not query.lstrip().startswith(('MATCH', 'OPTIONAL MATCH')):
                    raise AssertionError('empty source fixture must not write the database')
                return Result([])

            def rollback(self):
                pass

        class Session(Transaction):
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def begin_transaction(self):
                return Transaction()

        class Driver:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def session(self, **kwargs):
                return Session()

        # Keep source preparation, plan validation, artifact serialization and
        # the actual writer active. Only local report inventory and DB I/O are
        # substituted; an empty inventory legitimately yields zero assertions.
        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            for operation in ('fsync', 'replace'):
                for failure in (OSError, KeyboardInterrupt):
                    with self.subTest(wg=wg, operation=operation, failure=failure.__name__), \
                            tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                        root = Path(directory)
                        output = root / f'ontology/output/tsg/RAN/formal/instances/phase-2/{wg}'
                        output.mkdir(parents=True)
                        coverage_path = output / 'decision_disposition_coverage.json'
                        previous = b'{"previous":"coverage"}\n'
                        coverage_path.write_bytes(previous)
                        coverage_path.chmod(0o640)
                        plan_path, result_path = root / 'plan.json', root / 'result.json'
                        stack.enter_context(patch.object(reconciler, 'ROOT', root))
                        stack.enter_context(patch.object(disposition, 'reports_for_wg', return_value=[]))
                        stack.enter_context(patch.object(reconciler, 'reports_for_wg', return_value=[]))
                        stack.enter_context(patch.object(reconciler.credentials, 'neo4j_auth', return_value=('fixture', 'fixture')))
                        stack.enter_context(patch.object(reconciler.GraphDatabase, 'driver', return_value=Driver()))
                        stack.enter_context(redirect_stdout(io.StringIO()))
                        stack.enter_context(patch.object(sys, 'argv', [str(Path(reconciler.__file__)),
                            '--wg', wg, '--out', str(result_path), '--plan', str(plan_path), '--apply']))
                        storage.durable_json(plan_path, reconciler.plan(wg, [], Driver()))
                        expected = (json.dumps(reconciler.coverage_for_wg(wg, []),
                                              ensure_ascii=False, indent=2) + '\n').encode('utf-8')
                        actual_writer = reconciler.write_text_atomic

                        def failed_writer(path, text):
                            self.assertEqual(path, coverage_path)
                            with patch.object(atomic_io.os, operation,
                                              side_effect=failure('synthetic coverage publication failure')):
                                return actual_writer(path, text)

                        with patch.object(reconciler, 'write_text_atomic', side_effect=failed_writer):
                            with self.assertRaisesRegex(failure, 'synthetic coverage publication failure'):
                                reconciler.main()
                        self.assertEqual(coverage_path.read_bytes(), previous)
                        self.assertEqual(coverage_path.stat().st_mode & 0o777, 0o640)
                        self.assertEqual(list(output.glob('.decision_disposition_coverage.json.*.tmp')), [])
                        self.assertFalse(result_path.exists())
                        for _ in range(2):
                            reconciler.main()
                            self.assertEqual(coverage_path.read_bytes(), expected)
                            self.assertEqual(coverage_path.stat().st_mode & 0o777, 0o640)
                            self.assertEqual(list(output.glob('.decision_disposition_coverage.json.*.tmp')), [])
                            self.assertEqual(json.loads(result_path.read_text())['mode'],
                                             'applied_with_preimage_and_postconditions')

    def test_schema_is_prepared_before_every_wg_data_transaction(self):
        queries = []
        class Session:
            def run(self, query):
                queries.append(query)
                return Result()
        disposition.prepare_disposition_indexes(Session())
        self.assertEqual(len(queries), 2)
        self.assertTrue(queries[0].startswith('CREATE INDEX decision_disposition_identity'))
        self.assertEqual(queries[1], 'CALL db.awaitIndexes(300)')
        formal = Path(__file__).resolve().parents[1]
        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            with self.subTest(wg=wg):
                tree = ast.parse((formal / wg / 'phase-2/neo4j/01_load_decisions.py').read_text())
                main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
                calls = [n for n in ast.walk(main) if isinstance(n, ast.Call)]
                prepare = next(n for n in calls if isinstance(n.func, ast.Name) and
                               n.func.id == 'prepare_disposition_indexes')
                begin = next(n for n in calls if isinstance(n.func, ast.Attribute) and
                             n.func.attr == 'begin_transaction')
                load = next(n for n in calls if isinstance(n.func, ast.Name) and
                            n.func.id == 'load_dispositions')
                commit = next(n for n in calls if isinstance(n.func, ast.Attribute) and
                              n.func.attr == 'commit')
                finish = next(n for n in calls if isinstance(n.func, ast.Name) and
                              n.func.id == 'finalize_disposition_transaction')
                self.assertLess(prepare.lineno, begin.lineno)
                self.assertEqual(ast.unparse(load.args[0]), 'session')
                self.assertEqual([(k.arg, ast.unparse(k.value)) for k in load.keywords],
                                 [('transaction', 'tx')])
                self.assertLess(load.lineno, commit.lineno)
                self.assertLess(commit.lineno, finish.lineno)

    def test_source_event_receipt_waits_for_the_outer_commit(self):
        row = {'properties': {'resolutionId': 'DOC-current'}, 'agreement': False,
               'meetingId': 'tdoc:meeting/RAN1_115', 'references': [],
               'agendaId': '', 'aboutTdoc': ''}
        after = [{'resolutionId': 'DOC-current', 'properties': row['properties'],
                  'labels': ['Resolution'], 'edges': [
                      {'type': 'MADE_AT', 'target': row['meetingId'], 'properties': {}}]}]
        class Transaction:
            def run(self, query, **kwargs):
                if query.lstrip().startswith('CREATE'):
                    raise AssertionError('schema in data transaction')
                if 'RETURN id,count(m) AS n' in query:
                    return Result([{'id': row['meetingId'], 'n': 1}])
                if 'RETURN t.tdocNumber AS number,t.id AS id' in query or 'RETURN a.id AS id' in query:
                    return Result([])
                return Result()
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            stack.enter_context(patch.object(storage, 'storage_rows', return_value=[row]))
            stack.enter_context(patch.object(storage, 'source_event_snapshot', side_effect=[[], [], after]))
            stack.enter_context(patch.object(storage, 'source_fingerprints', return_value={}))
            stack.enter_context(patch.object(storage, 'check_fingerprints'))
            result = storage.load_document_resolutions(NoSessionWrites(),
                [{'madeAt': row['meetingId']}], root, transaction=Transaction())
            receipt = json.loads((root / result['preimageJournal']).read_text())
            self.assertEqual(result['sourceEvents'], 1)
            self.assertEqual(receipt['state'], 'awaiting_outer_commit')
            self.assertEqual(receipt['qualificationStatus'], 'awaiting_dispositions')

    def disposition_fixture(self, root, stack, snapshots=None):
        properties = {'dispositionId': 'RAN1:AGR-current:R1-current'}
        payload = [{'properties': properties, 'resolutionId': 'AGR-current', 'tdocNumber': 'R1-current'}]
        before_resolution = [{'resolutionId': 'AGR-current', 'properties': {}, 'references': []}]
        postimage = [{'elementId': 'one', 'properties': properties, 'edges': []}]
        class Transaction:
            def run(self, query, **kwargs):
                if query.lstrip().startswith('CREATE') or 'awaitIndexes' in query:
                    raise AssertionError('schema in data transaction')
                if 'RETURN count(DISTINCT d) AS assertions' in query:
                    return Result({'assertions': 1, 'missingTargets': 1})
                if 'RETURN count(d) AS count' in query:
                    return Result({'count': 1})
                if 'RETURN properties(d) AS properties,edges' in query:
                    return Result([{'properties': properties, 'edges': [
                        {'type': 'DISPOSITION_OF', 'resolutionId': 'AGR-current', 'target': None}],
                        'inverse': ['AGR-current']}])
                if 'RETURN t.tdocNumber AS number' in query:
                    return Result([])
                return Result()
        for module, name, value in [
                (disposition, 'ROOT', root),
                (disposition, 'validate_dispositions', lambda rows: None),
                (disposition, 'neo4j_rows', lambda rows: payload),
                (disposition, 'reports_for_wg', lambda wg: []),
                (disposition, 'resolution_snapshot', lambda *args: before_resolution),
                (storage, 'document_resolution_nodes', lambda reports: []),
                (storage, 'source_fingerprints', lambda *args: {}),
                (storage, 'check_fingerprints', lambda *args: None)]:
            stack.enter_context(patch.object(module, name, value))
        stack.enter_context(patch.object(disposition, 'disposition_snapshot',
            side_effect=[[], [], postimage] if snapshots is None else snapshots))
        result = disposition.load_dispositions(NoSessionWrites(), [{}], transaction=Transaction())
        return result, postimage

    def test_dispositions_share_caller_transaction_and_publish_after_readback(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            result, postimage = self.disposition_fixture(root, stack)
            receipt_path = (root / result['preimageJournal']).with_suffix('.result.json')
            self.assertTrue(result['outerTransactionPending'])
            self.assertEqual(json.loads(receipt_path.read_text())['state'], 'awaiting_outer_commit')
            with patch.object(disposition, 'disposition_snapshot', return_value=postimage):
                completed = disposition.finalize_disposition_transaction(NoSessionWrites(), result)
            self.assertNotIn('outerTransactionPending', completed)
            self.assertEqual(completed['assertions'], 1)
            self.assertEqual(completed['missingTargets'], 1)
            self.assertEqual(json.loads(receipt_path.read_text())['state'], 'committed')

    def test_rolled_back_or_unknown_outer_outcome_cannot_publish_success(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            result, _ = self.disposition_fixture(root, stack)
            receipt_path = (root / result['preimageJournal']).with_suffix('.result.json')
            with patch.object(disposition, 'disposition_snapshot', return_value=[]):
                with self.assertRaisesRegex(ValueError, 'committed readback differs'):
                    disposition.finalize_disposition_transaction(NoSessionWrites(), result)
            self.assertEqual(json.loads(receipt_path.read_text())['state'], 'awaiting_outer_commit')


    def test_partial_finalization_and_repeated_readback_are_retryable(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            result, postimage = self.disposition_fixture(root, stack)
            journal = root / result['preimageJournal']
            receipt_path = journal.with_suffix('.result.json')
            event_path = journal.with_name('source-event-fixture.json')
            source_events = {'sourceEvents': 1, 'preimageJournal': str(event_path.relative_to(root)),
                'postimageSha256': hashlib.sha256(json.dumps([], sort_keys=True).encode()).hexdigest()}
            result['documentSourceEvents'] = source_events
            clean = {key: value for key, value in result.items() if key != 'outerTransactionPending'}
            receipt = json.loads(receipt_path.read_text()); receipt['result'] = clean
            storage.durable_json(receipt_path, receipt)
            storage.durable_json(event_path, {'state': 'awaiting_outer_commit', 'result': source_events,
                'incoming': [{'properties': {'resolutionId': 'DOC-fixture'}}], 'sourceFiles': {}})
            original_write = storage.durable_json
            def fail_second_receipt(path, value):
                if path == receipt_path and value.get('state') == 'committed':
                    raise OSError('receipt disk unavailable')
                original_write(path, value)
            with patch.object(disposition, 'disposition_snapshot', return_value=postimage), \
                    patch.object(storage, 'source_event_snapshot', return_value=[]):
                with patch.object(storage, 'durable_json', side_effect=fail_second_receipt):
                    with self.assertRaisesRegex(OSError, 'disk unavailable'):
                        disposition.finalize_disposition_transaction(NoSessionWrites(), result)
                self.assertEqual(json.loads(event_path.read_text())['state'], 'committed')
                self.assertEqual(json.loads(receipt_path.read_text())['state'], 'awaiting_outer_commit')
                for _ in range(2):
                    self.assertEqual(disposition.finalize_disposition_transaction(NoSessionWrites(), result), clean)
            self.assertEqual(json.loads(receipt_path.read_text())['state'], 'committed')

    def test_unknown_commit_keeps_evidence_and_requires_readback_to_recover(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            result, postimage = self.disposition_fixture(root, stack)
            receipt_path = (root / result['preimageJournal']).with_suffix('.result.json')
            disposition.record_disposition_commit_failure(result, RuntimeError('commit response lost'))
            receipt = json.loads(receipt_path.read_text())
            self.assertEqual(receipt['state'], 'commit_outcome_unknown')
            self.assertEqual(receipt['postimage'], postimage)
            with patch.object(disposition, 'disposition_snapshot', return_value=[]):
                with self.assertRaisesRegex(ValueError, 'committed readback differs'):
                    disposition.finalize_disposition_transaction(NoSessionWrites(), result)
            self.assertEqual(json.loads(receipt_path.read_text())['state'], 'commit_outcome_unknown')
            with patch.object(disposition, 'disposition_snapshot', return_value=postimage):
                disposition.finalize_disposition_transaction(NoSessionWrites(), result)
            self.assertEqual(json.loads(receipt_path.read_text())['state'], 'committed')

    def test_disposition_caller_write_failure_keeps_unknown_outcome_receipt(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            with self.assertRaisesRegex(RuntimeError, 'data write failed'):
                self.disposition_fixture(root, stack, snapshots=[[], RuntimeError('data write failed')])
            receipts = list(root.rglob('preimage-*.result.json'))
            self.assertEqual(len(receipts), 1)
            saved = json.loads(receipts[0].read_text())
            self.assertEqual(saved['state'], 'commit_outcome_unknown')
            self.assertEqual(saved['stage'], 'caller_write_failed')

    def test_source_caller_write_failure_keeps_unknown_outcome_receipt(self):
        row = {'properties': {'resolutionId': 'DOC-current'}, 'agreement': False,
            'meetingId': 'tdoc:meeting/RAN1_115', 'references': [], 'agendaId': '', 'aboutTdoc': ''}
        class Transaction:
            def run(self, *args, **kwargs):
                raise RuntimeError('source write failed')
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            stack.enter_context(patch.object(storage, 'storage_rows', return_value=[row]))
            stack.enter_context(patch.object(storage, 'source_event_snapshot', return_value=[]))
            stack.enter_context(patch.object(storage, 'source_fingerprints', return_value={}))
            stack.enter_context(patch.object(storage, 'check_fingerprints'))
            with self.assertRaisesRegex(RuntimeError, 'source write failed'):
                storage.load_document_resolutions(NoSessionWrites(), [{'madeAt': row['meetingId']}],
                    root, transaction=Transaction())
            receipts = list(root.rglob('source-event-preimage-*.json'))
            self.assertEqual(len(receipts), 1)
            saved = json.loads(receipts[0].read_text())
            self.assertEqual(saved['state'], 'commit_outcome_unknown')
            self.assertEqual(saved['stage'], 'caller_write_failed')


if __name__ == '__main__':
    unittest.main()
