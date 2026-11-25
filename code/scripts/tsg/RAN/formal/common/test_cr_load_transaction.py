#!/usr/bin/env python3
"""Missing CR endpoints or failed reconciliation preserve the prior graph."""
import argparse
import ast
import contextlib
import io
import importlib.util
import os
from pathlib import Path
import sys
import time
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[5]
WG = os.environ.get('SPECTRA_TEST_WG', 'RAN2')
if WG not in {f'RAN{i}' for i in range(1, 6)}:
    raise ValueError('SPECTRA_TEST_WG must select RAN1 through RAN5')
SOURCE = ROOT / 'scripts/tsg/RAN/formal' / WG / 'phase-4/neo4j/01_load_cr_ontology.py'


class SharedSectionIndex(unittest.TestCase):
    def test_release_resolution_and_missing_sections_match_in_every_wg(self):
        """JSON-LD 생성 4경로와 RAN5 raw-input 적재의 release 선택을 대조한다."""
        entries = [('38.999-Rel-16-1.2', '1.2'), ('38.999-Rel-18-1.2', '1.2'),
                   ('38.999-Rel-19-1.3', '1.3'), ('legacy-without-release-1.4', '1.4')]
        for number in range(1, 6):
            wg = f'RAN{number}'
            # 실제 모듈의 import에는 합성 자격증명을 제공해 로컬 .env와 무관하게 검사한다.
            with self.subTest(wg=wg), mock.patch.object(sys, 'path', sys.path.copy()), \
                 mock.patch.dict(os.environ, {'NEO4J_PASSWORD': 'synthetic-cr-section-index'}):
                filename = ('neo4j/01_load_cr_ontology.py' if number == 5
                            else 'cr-parser/03_generate_cr_jsonld.py')
                path = ROOT / 'scripts/tsg/RAN/formal' / wg / 'phase-4' / filename
                spec = importlib.util.spec_from_file_location('shared_cr_index_' + wg, path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)
                index = module.SectionIndex(entries)
                self.assertEqual(index.resolve('38.999', '1.2', 'Rel-18'), '38.999-Rel-18-1.2')
                self.assertEqual(index.resolve('38.999', '1.2', 'Rel-17'), '38.999-Rel-16-1.2')
                self.assertEqual(index.resolve('38.999', '1.2', 'Rel-15'), '38.999-Rel-18-1.2')
                self.assertEqual(index.resolve('38.999', '1.3', None), '38.999-Rel-19-1.3')
                self.assertIsNone(index.resolve('38.999', '1.4', 'Rel-19'))
                self.assertIsNone(index.resolve('38.998', '1', 'Rel-19'))
                self.assertEqual(index.stats, dict(exact=1, **{
                    'fallback-le': 1, 'fallback-fwd': 1, 'latest': 1,
                    'drop-nosec': 1, 'drop-nospec': 1}))


class CRTransaction(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_complete_input_commits_once_and_failures_never_commit(self):
        node = next(n for n in ast.parse(SOURCE.read_text()).body
                    if isinstance(n, ast.FunctionDef) and n.name == 'main')
        for missing in ('pack', 'spec', 'section', 'reconcile', None):
            with self.subTest(missing=missing):
                tx = SimpleNamespace(commit=mock.Mock(), run=lambda *a, **kw: SimpleNamespace(single=lambda: {'cnt': 0}))
                session = mock.MagicMock()
                session.__enter__.return_value = session
                session.begin_transaction.return_value = tx
                session.run.return_value.single.return_value = {'cnt': 1}
                driver = SimpleNamespace(session=lambda: session, close=mock.Mock(), verify_connectivity=lambda: None)
                writers = []
                def writer(db, *args):
                    writers.append(db)
                    return 1
                def reconcile(db, *args, **kw):
                    writers.append(db)
                    if missing == 'reconcile':
                        raise RuntimeError('synthetic reconciliation failure')
                    return {}
                def numbers(*args, report_path=None, **kwargs):
                    if report_path is not None:
                        report_path.write_text('{}')
                    return {}
                env = dict(argparse=argparse, sys=sys, tempfile=tempfile, Path=Path,
                    write_text_atomic=lambda path, text: path.write_text(text),
                    NEO4J_URI='unused', NEO4J_USER='unused',
                    NEO4J_PASSWORD='unused', CR_DOCUMENTS=Path('unused'), CRNUMBER_REPORT=self.root / 'report.json',
                    GraphDatabase=SimpleNamespace(driver=lambda *a, **kw: driver),
                    load_jsonld=lambda name: ([{'@id': 'tdoc:R2-1'}] if name != 'spec_dynamic.jsonld' else []),
                    _accept_cr_inputs=lambda *args: None, load_phase1_spec_numbers=lambda: {'38.331'},
                    load_form_records=lambda path: {}, load_number_records=lambda path: {}, uri_to_id=lambda value: value,
                    create_indexes=lambda db: None, load_crpack_nodes=writer, load_dynamic_specs=writer,
                    ensure_cr_labels=writer, absorb_backfill_twins=lambda *a, **kw: {},
                    load_cr_extensions=writer, fill_backfill_form=lambda *a, **kw: {},
                    reconcile_cr_numbers=numbers, reconcile=reconcile,
                    load_crpack_relationships=lambda *a: int(missing != 'pack'),
                    crpack_pairs=lambda *a: ({('CR', 'pack')}, 0),
                    AFFECTS_FIELDS=[('AFFECTS_CORE_SPEC', 'affectsCoreSpec', 'core')],
                    desired_affects=lambda *a: {('CR', 'AFFECTS_CORE_SPEC', '38.331')},
                    load_affects_spec=lambda *a: {'core': int(missing != 'spec'), 'test': 0, 'om': 0},
                    load_modifies_section=lambda *a: int(missing != 'section'),
                    desired_sections=lambda *a: {('CR', 'section')})
                if WG == 'RAN5':
                    def section_writer(db, docs, index, want, **kw):
                        writers.append(db)
                        want.add(('CR', 'section'))
                        return int(missing != 'section')
                    env.update(time=time, load_json=lambda name: {
                        'packs': [{'crPackId': 'pack', 'tdocNumbers': ['CR']}],
                        'documents': [{'tdoc_number': 'CR'}]},
                        _input_records=lambda data, key: data[key],
                        load_section_index=lambda db: SimpleNamespace(sid_by={'section': 'unused'}, stats={}),
                        load_crpacks=writer,
                        desired_cross_spec=lambda docs: {('CR', 'AFFECTS_CORE_SPEC', '38.331')},
                        CROSS_SPEC_FIELDS=[('affects_core_spec', 'AFFECTS_CORE_SPEC')],
                        load_cross_spec=lambda *a: (int(missing != 'spec'), 0, 0, 0),
                        load_modifies_section=section_writer, normalize_spec_number=lambda value: value)
                exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), 'exec'), env)
                with mock.patch.object(sys, 'argv', ['loader']), contextlib.redirect_stdout(io.StringIO()):
                    if missing:
                        with self.assertRaises(RuntimeError):
                            env['main']()
                        tx.commit.assert_not_called()
                    else:
                        result = env['main']()
                        self.assertEqual(result, None if WG == 'RAN5' else 0)
                        tx.commit.assert_called_once_with()
                self.assertTrue(writers)
                self.assertTrue(all(db is tx for db in writers))
                driver.close.assert_called_once_with()

    def test_ran1_actual_main_publishes_number_report_after_commit_and_cleans_staging(self):
        import importlib.util
        import json
        with mock.patch.object(sys, 'path', [str(ROOT / 'scripts/common'),
                str(ROOT / 'scripts/tsg/RAN/formal/common'), *sys.path]):
            from common import credentials, atomic_io
            source = ROOT / 'scripts/tsg/RAN/formal/RAN1/phase-4/neo4j/01_load_cr_ontology.py'
            spec = importlib.util.spec_from_file_location('ran1_cr_report_boundary', source)
            module = importlib.util.module_from_spec(spec)
            with mock.patch.object(credentials, 'neo4j_password', return_value='synthetic'):
                spec.loader.exec_module(module)
        instances = self.root / 'instances/phase-4/RAN1'
        instances.mkdir(parents=True)
        def write(path, value):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value))
        write(instances / 'crpacks.jsonld', {'@graph': [
            {'tdoc:crPackId': 'RP-000001', 'hasCR': 'tdoc:R1-0000001'}]})
        write(instances / 'cr_extensions.jsonld', {'@graph': [
            {'@id': 'tdoc:R1-0000001', 'belongsToCRPack': 'tdoc:crpack/RP-000001'}]})
        write(instances / 'spec_dynamic.jsonld', {'@graph': []})
        write(instances.parent.parent / 'phase-1/RAN1/specs.jsonld',
              {'@graph': [{'tdoc:specNumber': '38.201'}]})
        documents = self.root / 'parsed.json'
        write(documents, {'cr_documents': [{'tdoc_number': 'R1-0000001'}]})
        report = self.root / 'report.json'
        originals = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        state = {'failure': None}
        transactions, drivers = [], []

        class Result:
            def __init__(self, count): self.count = count
            def single(self): return {'cnt': self.count}
            def data(self): return []
            def __iter__(self): return iter([])

        class Transaction:
            def __init__(self): self.committed = False
            def run(self, query, **params):
                if state['failure'] == 'query' and 'BELONGS_TO_CR_PACK]->' in query:
                    raise KeyboardInterrupt('synthetic query interrupt')
                count = len(params.get('batch', []))
                if state['failure'] == 'membership' and 'MERGE (c)-[:BELONGS_TO_CR_PACK]' in query:
                    count = 0
                return Result(count)
            def commit(self):
                if state['failure'] == 'commit': raise OSError('synthetic commit failure')
                self.committed = True

        def driver(*args, **kwargs):
            tx = Transaction(); transactions.append(tx)
            session = mock.MagicMock()
            session.__enter__.return_value = session
            session.begin_transaction.return_value = tx
            session.run.side_effect = tx.run
            value = SimpleNamespace(session=lambda: session, close=mock.Mock())
            drivers.append(value)
            return value

        with mock.patch.multiple(module, INSTANCES_DIR=instances, CR_DOCUMENTS=documents,
                                 CRNUMBER_REPORT=report), \
             mock.patch.object(module.GraphDatabase, 'driver', side_effect=driver), \
             mock.patch.object(sys, 'argv', ['loader']), contextlib.redirect_stdout(io.StringIO()):
            for failure in ('membership', 'query', 'commit', 'fsync', 'replace', None):
                state['failure'] = failure
                report.write_bytes(b'previous committed report')
                if failure in ('fsync', 'replace'):
                    fault = mock.patch.object(atomic_io.os, failure, side_effect=KeyboardInterrupt('publication'))
                else:
                    fault = contextlib.nullcontext()
                with self.subTest(failure=failure), fault:
                    if failure:
                        with self.assertRaises((RuntimeError, OSError, KeyboardInterrupt)):
                            module.main()
                        self.assertEqual(report.read_bytes(), b'previous committed report')
                        self.assertEqual(transactions[-1].committed, failure in ('fsync', 'replace'))
                    else:
                        self.assertEqual(module.main(), 0)
                        self.assertFalse(json.loads(report.read_text())['dry_run'])
                        self.assertTrue(transactions[-1].committed)
                self.assertFalse(list(self.root.glob('.crnumber-*')))
                drivers[-1].close.assert_called_once_with()
                state['failure'] = None
                for _ in range(2):
                    self.assertEqual(module.main(), 0)
                    self.assertFalse(json.loads(report.read_text())['dry_run'])
                    drivers[-1].close.assert_called_once_with()
            previous = report.read_bytes()
            with mock.patch.object(sys, 'argv', ['loader', '--dry-run']):
                self.assertEqual(module.main(), 0)
                self.assertEqual(report.read_bytes(), previous)
        self.assertTrue(all(p.read_bytes() == data for p, data in originals.items()))


if __name__ == '__main__':
    unittest.main()
