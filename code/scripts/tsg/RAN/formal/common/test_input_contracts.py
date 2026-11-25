#!/usr/bin/env python3
"""Spec: parsing/input/CQ contracts; Ontology: existing section and version keys; Cycle: 8.
배경: 손상 입력·분할 청크·구조 수식이 정상 완료로 오인되는 경계를 검증한다.
사용: python3 -m unittest discover -s scripts/tsg/RAN/formal/common -p test_input_contracts.py
LLM/DB/네트워크 및 실제 변환 호출 없이 scratch 입력만 사용한다.
"""
import ast
from collections import defaultdict
import contextlib
import importlib.util
import io
import json
import logging
from pathlib import Path
import re
import shutil
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET
import zipfile
import zlib
from test_audit_safety_contracts import function, ROOT, COMMON

class InputContracts(unittest.TestCase):
    def test_ran1_tr_generator_publishes_one_generation_with_source_bound_assertions(self):
        import hashlib
        with patch('socket.socket.connect', side_effect=AssertionError('network denied')), \
                patch('socket.create_connection', side_effect=AssertionError('network denied')):
            self.addCleanup(sys.path.__setitem__, slice(None), sys.path.copy())
            sys.path.insert(0, str(ROOT / 'scripts/common'))
            from common import atomic_io
            path = ROOT / 'scripts/tsg/RAN/formal/RAN1/phase-5/tr-parser/02_generate_tr_jsonld.py'
            spec = importlib.util.spec_from_file_location('_actual_ran1_tr_generator', path)
            generator = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(generator)
            with tempfile.TemporaryDirectory() as td, contextlib.redirect_stdout(io.StringIO()):
                td = Path(td)
                generator.PROJECT_ROOT = td
                generator.PARSED_DIR, generator.PHASE1_DIR = td / 'parsed', td / 'phase1'
                generator.OUTPUT_DIR = td / 'ontology/output/tsg/RAN/formal/instances/phase-5/RAN1'
                for folder in (generator.PARSED_DIR, generator.PHASE1_DIR, generator.OUTPUT_DIR):
                    folder.mkdir(parents=True)
                generator.IMPACT_CSV, generator.SPEC_TITLES_FILE = td / 'impacts.csv', td / 'titles.json'
                generator.SPEC_TITLES_FILE.write_text(json.dumps({'specs': {'38.001': 'Synthetic target'}}))
                phase1 = generator.PHASE1_DIR / 'specs.jsonld'
                phase1_text = json.dumps(generator.canonical_document({'@graph': []}, wg='RAN1'))
                phase1.write_text(phase1_text)
                (generator.PARSED_DIR / 'tr_metadata.json').write_text(json.dumps({'technicalReports': [
                    dict(trNumber='38.000', trVersion='19.0.0', trTitle='Synthetic source',
                         trStatus='Completed', scope='Synthetic scope', conclusions='Synthetic conclusion')]}))
                header = 'trNumber,impactType,impactsSpec,impactsSection,impactDescription\n'
                candidate = header + '38.000,NewTS,38.001,,Synthetic proposed change\n'
                generator.IMPACT_CSV.write_text(candidate)
                source = td / 'source.txt'
                source.write_text('Synthetic study discusses 38.001.')
                receipt = dict(path='source.txt', sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                               locator='line1', quote=source.read_text())
                manifest = td / 'ontology/input/tsg/RAN/formal/TR/RAN1/tr_impact_evidence.json'
                manifest.parent.mkdir(parents=True)
                manifest.write_text(json.dumps({'wg': 'RAN1', 'schema': 1, 'claims': [{
                    'claim': dict(trNumber='38.000', impactType='NewTS', impactsSpec='38.001', impactsSection=''),
                    'status': 'pending', 'supportedStudyAssertions': [{
                        'predicate': 'discussesSpec', 'description': 'Synthetic study finding', 'evidence': receipt}]}]}))
                names = ('technical_reports.jsonld', 'tr_impacts.jsonld', 'spec_section_dynamic.jsonld',
                         'generation_metadata.json', 'tr_source_assertions.jsonld')
                old = {name: ('old ' + name).encode() for name in names}
                def restore():
                    for name, data in old.items(): (generator.OUTPUT_DIR / name).write_bytes(data)
                def unchanged():
                    self.assertEqual({name: (generator.OUTPUT_DIR / name).read_bytes() for name in names}, old)
                    self.assertEqual(list(generator.OUTPUT_DIR.glob('.tr-generation-*')), [])
                    self.assertEqual(list(generator.OUTPUT_DIR.glob('.json-set-*')), [])
                real_replace = atomic_io.os.replace
                for index in range(len(names)):
                    for after in (False, True):
                        for error in (OSError, KeyboardInterrupt):
                            restore()
                            target, fired = generator.OUTPUT_DIR / names[index], []
                            def replace(src, dst):
                                if Path(dst) == target and not fired:
                                    fired.append(True)
                                    if after: real_replace(src, dst)
                                    raise error('synthetic generation publication')
                                return real_replace(src, dst)
                            with patch.object(atomic_io.os, 'replace', side_effect=replace), self.assertRaises(error):
                                generator.main()
                            unchanged()
                            generator.main()
                report = json.loads((generator.OUTPUT_DIR / 'generation_metadata.json').read_text())
                self.assertEqual(report['statistics']['technicalReports'], 1)
                self.assertEqual(report['statistics']['trImpacts'], 1)
                self.assertEqual(report['statistics']['dynamicInstances'], 1)
                self.assertIn('discussesSpec', (generator.OUTPUT_DIR / 'tr_source_assertions.jsonld').read_text())
                self.assertIn('candidateImpactsSpec', (generator.OUTPUT_DIR / 'tr_impacts.jsonld').read_text())
                self.assertEqual(source.read_text(), receipt['quote'])
                validator_path = path.with_name('03_validate_jsonld.py')
                validator_spec = importlib.util.spec_from_file_location('_actual_ran1_tr_validator', validator_path)
                validator = importlib.util.module_from_spec(validator_spec)
                validator_spec.loader.exec_module(validator)
                validator.PROJECT_ROOT, validator.INSTANCE_DIR = td, generator.OUTPUT_DIR
                validator.PHASE1_SPECS, validator.LOGS_DIR = phase1, td / 'validation'
                validation_report = validator.LOGS_DIR / 'jsonld_validation_report.json'
                self.assertEqual(validator.main(), 0, validation_report.read_text() if validation_report.exists() else '')
                self.assertEqual(json.loads(validation_report.read_text())['status'], 'PASS')
                tr_path = generator.OUTPUT_DIR / 'technical_reports.jsonld'
                valid_document = json.loads(tr_path.read_text())
                row = valid_document['@graph'][0]
                malformed = [dict(valid_document, **{'@graph': graph}) for graph in (
                    [row, row], [row, dict(row, **{'@id': 'tr:other'})],
                    [dict(row, **{'@type': 'Spec'})], [dict(row, **{'@type': ['TechnicalReport']})],
                    [dict(row, **{'@type': 3})], [], [None])]
                malformed.extend(([], {'@graph': 'invalid'}))
                for document in malformed:
                    tr_path.write_text(json.dumps(document))
                    self.assertEqual(validator.main(), 1)
                    self.assertEqual(json.loads(validation_report.read_text())['status'], 'FAIL')
                    generator.main()
                    self.assertEqual(validator.main(), 0)
                for boundary in ('fsync', 'replace'):
                    for error in (OSError, KeyboardInterrupt):
                        previous_report = validation_report.read_bytes()
                        with patch.object(atomic_io.os, boundary, side_effect=error('synthetic validator publication')), \
                                self.assertRaises(error):
                            validator.main()
                        self.assertEqual(validation_report.read_bytes(), previous_report)
                        self.assertEqual(list(validator.LOGS_DIR.glob('*.tmp')), [])
                        for _ in range(2): self.assertEqual(validator.main(), 0)
                for content in ('{invalid', '[]', '{"@graph":[null]}'):
                    restore()
                    phase1.write_text(content)
                    with self.assertRaises(ValueError): generator.main()
                    unchanged()
                phase1.write_text(phase1_text)
                restore()
                source.write_text('Changed synthetic source')
                with self.assertRaises(ValueError): generator.main()
                unchanged()
                source.write_text(receipt['quote'])
                generator.IMPACT_CSV.write_text(header)
                restore()
                # Fail once so rollback can restore the existing metadata too.
                calls = []
                def fail_once(src, dst):
                    if Path(dst) == generator.OUTPUT_DIR / 'generation_metadata.json' and not calls:
                        calls.append(True)
                        raise OSError('synthetic after stale deletion')
                    return real_replace(src, dst)
                with patch.object(atomic_io.os, 'replace', side_effect=fail_once), self.assertRaises(OSError):
                    generator.main()
                unchanged()
                for _ in range(2): generator.main()
                self.assertFalse((generator.OUTPUT_DIR / 'spec_section_dynamic.jsonld').exists())

    def test_ran1_tr_parser_actual_docx_publication_and_retry(self):
        with patch('socket.socket.connect', side_effect=AssertionError('network denied')), \
                patch('socket.create_connection', side_effect=AssertionError('network denied')):
            self.addCleanup(sys.path.__setitem__, slice(None), sys.path.copy())
            sys.path.insert(0, str(ROOT / 'scripts/common'))
            from common import atomic_io
            from docx import Document
            path = ROOT / 'scripts/tsg/RAN/formal/RAN1/phase-5/tr-parser/01_parse_tr_docs.py'
            spec = importlib.util.spec_from_file_location('_actual_ran1_tr_parser', path)
            parser = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(parser)
            with tempfile.TemporaryDirectory() as td, contextlib.redirect_stdout(io.StringIO()):
                td = Path(td)
                parser.TR_INPUT_DIR, parser.OUTPUT_DIR = td / 'input', td / 'output'
                folder = parser.TR_INPUT_DIR / '38.000'
                folder.mkdir(parents=True)
                source = folder / '38000-j00.docx'
                document = Document()
                for text in ('3GPP TR 38.000 V19.0.0', 'Study on synthetic source', '(Release 19)'):
                    document.add_paragraph(text)
                for title, text in (('1 Scope', 'Synthetic study scope.'),
                                    ('2 References', 'Study Item RP-000001'),
                                    ('3 Conclusions', 'Synthetic source conclusion.')):
                    document.add_heading(title, level=1)
                    document.add_paragraph(text)
                document.save(source)
                source_bytes = source.read_bytes()
                output = parser.OUTPUT_DIR / 'tr_metadata.json'
                def run():
                    parser.main()
                    return json.loads(output.read_text())
                report = run()
                row = report['technicalReports'][0]
                self.assertEqual((row['trNumber'], row['trVersion'], row['targetRelease']),
                                 ('38.000', '19.0.0', 'Rel-19'))
                self.assertEqual(row['trTitle'], 'Study on synthetic source')
                self.assertEqual(row['scope'], 'Synthetic study scope.')
                self.assertEqual(row['conclusions'], 'Synthetic source conclusion.')
                self.assertEqual(row['studyItemRpNumber'], 'RP-000001')
                self.assertIsNone(row['workItemRpNumber'])
                self.assertEqual(report['statistics']['totalTRs'], 1)
                self.assertEqual(run()['technicalReports'], report['technicalReports'])
                for boundary in ('fsync', 'replace'):
                    for error in (OSError, KeyboardInterrupt):
                        previous = output.read_bytes()
                        with patch.object(atomic_io.os, boundary, side_effect=error('synthetic publication')), \
                                self.assertRaises(error): parser.main()
                        self.assertEqual(output.read_bytes(), previous)
                        self.assertEqual(list(parser.OUTPUT_DIR.glob('.tr_metadata.json.*.tmp')), [])
                        for _ in range(2):
                            self.assertEqual(run()['technicalReports'], report['technicalReports'])
                previous = output.read_bytes()
                source.write_bytes(b'broken synthetic docx')
                with self.assertRaises(ValueError): parser.main()
                self.assertEqual(output.read_bytes(), previous)
                source.write_bytes(source_bytes)
                for _ in range(2):
                    self.assertEqual(run()['technicalReports'], report['technicalReports'])
                empty = td / 'empty'
                empty.mkdir()
                with patch.object(parser, 'TR_INPUT_DIR', empty), self.assertRaises(ValueError):
                    parser.main()
                self.assertEqual(source.read_bytes(), source_bytes)

    def test_ran1_tr_release_preflight_gates_publication_and_retry(self):
        with patch('socket.socket.connect', side_effect=AssertionError('network denied')), \
                patch('socket.create_connection', side_effect=AssertionError('network denied')):
            self.addCleanup(sys.path.__setitem__, slice(None), sys.path.copy())
            sys.path.insert(0, str(ROOT / 'scripts/common'))
            from common import credentials, atomic_io
            path = ROOT / 'scripts/tsg/RAN/formal/RAN1/phase-5/neo4j/02_load_tr_release_specs.py'
            spec = importlib.util.spec_from_file_location('_actual_ran1_tr_releases', path)
            loader = importlib.util.module_from_spec(spec)
            with patch.object(credentials, 'neo4j_password', return_value='synthetic'):
                spec.loader.exec_module(loader)
            mode, committed, closed, queries = {'case': 'normal'}, [], [], []
            class Rows(list):
                def single(self): return self[0] if self else None
            class Transaction:
                def __enter__(self): return self
                def __exit__(self, *args): pass
                def run(self, query, **params):
                    queries.append(query)
                    if query == loader.MERGE_VARIANT:
                        if mode['case'] == 'error': raise OSError('synthetic merge')
                        if mode['case'] == 'interrupt': raise KeyboardInterrupt('synthetic merge')
                        if mode['case'] == 'missing_hub': return Rows()
                        return Rows([{'hub_linked': 0 if mode['case'] == 'hub_zero' else 1,
                                      'rel_linked': 0 if mode['case'] == 'foreign_release' else 1}])
                    if query == loader.VERIFY_VARIANT:
                        return Rows([{'variants': 1, 'in_release_of': 1,
                                      'spec_in_release': 0 if mode['case'] == 'gate' else 1}])
                    return Rows([{'n': 1}])
                def commit(self):
                    if mode['case'] == 'commit': raise OSError('synthetic commit')
                    committed.append(True)
            class Session:
                def __enter__(self): return self
                def __exit__(self, *args): pass
                def begin_transaction(self): return Transaction()
            class Driver:
                def session(self):
                    if mode['case'] == 'session': raise OSError('synthetic session')
                    return Session()
                def close(self): closed.append(True)
            with tempfile.TemporaryDirectory() as td, \
                    patch.object(loader.GraphDatabase, 'driver', return_value=Driver()) as connect, \
                    contextlib.redirect_stdout(io.StringIO()):
                td = Path(td)
                loader.CSV_PATH, loader.REPORT_DIR = td / 'metadata.csv', td / 'reports'
                header = 'spec,release,version,status\n'
                accepted = '38.000,Rel-18,18.0.0,Exists\n'
                skipped = '38.001,Rel-18,18.0.0,Failed\n'
                for text in (header, header + skipped, 'wrong,header\n',
                             header + ',Rel-18,18.0.0,Exists\n',
                             header + accepted + accepted,
                             header + '38.000,Rel-18,,Downloaded\n'):
                    loader.CSV_PATH.write_text(text)
                    with self.assertRaises(ValueError): loader.main()
                    connect.assert_not_called()
                loader.CSV_PATH.write_text(header + accepted + skipped)
                source = loader.CSV_PATH.read_bytes()
                loader.REPORT_DIR.mkdir()
                output = loader.REPORT_DIR / 'tr_kg_report.json'
                output.write_bytes(b'previous report')
                for case in ('normal', 'gate', 'missing_hub', 'hub_zero', 'foreign_release',
                             'error', 'interrupt', 'commit', 'session'):
                    mode['case'] = case
                    previous, count, closed_count = output.read_bytes(), len(committed), len(closed)
                    if case == 'normal': self.assertIsNone(loader.main())
                    else:
                        error = (SystemExit if case in ('gate', 'hub_zero', 'foreign_release') else ValueError if case == 'missing_hub'
                                 else KeyboardInterrupt if case == 'interrupt' else OSError)
                        with self.assertRaises(error): loader.main()
                        self.assertEqual(output.read_bytes(), previous)
                    self.assertEqual(len(committed), count + (case == 'normal'))
                    self.assertEqual(len(closed), closed_count + 1)
                    mode['case'] = 'normal'
                    for _ in range(2):
                        loader.main()
                        report = json.loads(output.read_text())
                        self.assertTrue(all(report['gates'].values()))
                        self.assertEqual(len(report['variants']), 1)
                        self.assertEqual(report['skipped_not_on_disk'], 1)
                for boundary in ('fsync', 'replace'):
                    for error in (OSError, KeyboardInterrupt):
                        previous, count = output.read_bytes(), len(committed)
                        with patch.object(atomic_io.os, boundary, side_effect=error('synthetic publication')), \
                                self.assertRaises(error): loader.main()
                        self.assertEqual(len(committed), count + 1)
                        self.assertEqual(output.read_bytes(), previous)
                        self.assertEqual(list(loader.REPORT_DIR.glob('.tr_kg_report.json.*.tmp')), [])
                        loader.main()
                self.assertEqual(loader.CSV_PATH.read_bytes(), source)
                self.assertTrue(queries)

    def test_ran1_tr_loader_preflight_transaction_close_and_retry(self):
        with patch('socket.socket.connect', side_effect=AssertionError('network denied')), \
                patch('socket.create_connection', side_effect=AssertionError('network denied')):
            self.addCleanup(sys.path.__setitem__, slice(None), sys.path.copy())
            sys.path.insert(0, str(ROOT / 'scripts/common'))
            from common import credentials
            path = ROOT / 'scripts/tsg/RAN/formal/RAN1/phase-5/neo4j/01_load_tr_ontology.py'
            spec = importlib.util.spec_from_file_location('_actual_ran1_tr_loader', path)
            loader = importlib.util.module_from_spec(spec)
            with patch.object(credentials, 'neo4j_password', return_value='synthetic'):
                spec.loader.exec_module(loader)
            mode, queries, commits, closed = {'case': 'normal'}, [], [], []
            class Rows(list):
                def single(self): return self[0]
                def consume(self): return None
            class Transaction:
                def __enter__(self): return self
                def __exit__(self, *args): pass
                def run(self, query, **params):
                    queries.append(('transaction', query))
                    if 'UNWIND $rows AS row' in query:
                        if mode['case'] == 'query_error': raise OSError('synthetic late query')
                        if mode['case'] == 'interrupt': raise KeyboardInterrupt('synthetic late interruption')
                    count = len(params.get('batch', []))
                    if mode['case'] == 'count_mismatch' and 'MERGE (t:TechnicalReport' in query:
                        count = 0
                    return Rows([{'cnt': count, 'count': len(params.get('rows', []))}])
                def commit(self):
                    if mode['case'] == 'commit_error': raise OSError('synthetic commit')
                    commits.append(True)
            class Session:
                def __enter__(self): return self
                def __exit__(self, *args): pass
                def run(self, query, **params):
                    queries.append(('schema', query))
                    return Rows()
                def begin_transaction(self): return Transaction()
            class Driver:
                def session(self):
                    if mode['case'] == 'session_error': raise OSError('synthetic session')
                    return Session()
                def close(self): closed.append(True)
            with tempfile.TemporaryDirectory() as td, \
                    patch.object(loader.GraphDatabase, 'driver', return_value=Driver()) as connect, \
                    contextlib.redirect_stdout(io.StringIO()):
                td = Path(td)
                loader.PROJECT_ROOT = loader.INSTANCES_DIR = td
                loader.TR_WORKITEM_CSV = td / 'mapping.csv'
                names = ('technical_reports.jsonld', 'tr_impacts.jsonld', 'spec_section_dynamic.jsonld')
                valid = [[{'trNumber': '38.000', 'scope': 'synthetic source'}], [], []]
                def prepare(graphs):
                    for name, graph in zip(names, graphs):
                        (td / name).write_text(json.dumps({'@graph': graph}))
                    loader.TR_WORKITEM_CSV.write_text('trNumber,workItemCode\n')
                for invalid in ([[], [], []], [[{}], [], []],
                                [[{'trNumber': ' '}], [], []],
                                [[{'trNumber': '38.000'}, {'trNumber': '38.000'}], [], []],
                                [valid[0], [None], []], [valid[0], [{'trImpactId': ''}], []],
                                [valid[0], [], [None]]):
                    prepare(invalid)
                    with self.assertRaises(ValueError): loader.main()
                    connect.assert_not_called()
                for csv_text in (None, 'wrong,columns\n', 'trNumber,workItemCode\n38.000\n'):
                    prepare(valid)
                    if csv_text is None: loader.TR_WORKITEM_CSV.unlink()
                    else: loader.TR_WORKITEM_CSV.write_text(csv_text)
                    with self.assertRaises((SystemExit, ValueError)): loader.main()
                    connect.assert_not_called()
                prepare(valid)
                before = {p.name: p.read_bytes() for p in td.iterdir()}
                for case in ('normal', 'query_error', 'interrupt', 'count_mismatch',
                             'commit_error', 'session_error'):
                    mode['case'] = case
                    commit_count, close_count = len(commits), len(closed)
                    if case == 'normal': self.assertIsNone(loader.main())
                    else:
                        error = KeyboardInterrupt if case == 'interrupt' else SystemExit
                        with self.assertRaises(error): loader.main()
                    self.assertEqual(len(commits), commit_count + (case == 'normal'))
                    self.assertEqual(len(closed), close_count + 1)
                    mode['case'] = 'normal'
                    for _ in range(2):
                        commit_count = len(commits)
                        self.assertIsNone(loader.main())
                        self.assertEqual(len(commits), commit_count + 1)
                self.assertTrue(any('MERGE (t:TechnicalReport' in query for scope, query in queries))
                self.assertTrue(all(scope == 'transaction' or query.startswith('CREATE INDEX')
                                    for scope, query in queries))
                self.assertEqual({p.name: p.read_bytes() for p in td.iterdir()}, before)

    def test_ran1_embedded_identity_preflight_and_actual_transaction_retry(self):
        with patch('socket.socket.connect', side_effect=AssertionError('network denied')), \
                patch('socket.create_connection', side_effect=AssertionError('network denied')), \
                patch.dict('os.environ', {'NEO4J_PASSWORD': 'synthetic'}):
            path = ROOT / 'scripts/tsg/RAN/formal/RAN1/phase-2/neo4j/03_load_embedded.py'
            spec = importlib.util.spec_from_file_location('_actual_embedded_input', path)
            loader = importlib.util.module_from_spec(spec)
            before_path = sys.path[:]
            self.addCleanup(lambda: sys.path.__setitem__(slice(None), before_path))
            spec.loader.exec_module(loader)
            names = ('figures.jsonld', 'tables.jsonld', 'charts.jsonld',
                     'resolutions_agreements.jsonld', 'resolutions_conclusions.jsonld',
                     'resolutions_working_assumptions.jsonld')
            valid = {'figures.jsonld': [{'figureId': 'F-1', 'containedIn': 'tdoc:meeting/RAN1#1'}],
                     'tables.jsonld': [{'tableId': 'T-1', 'equations': ['x = y']}],
                     'charts.jsonld': [{'chartId': 'C-1'}],
                     'resolutions_agreements.jsonld': [{'resolutionId': 'AGR-1',
                         'hasFigure': 'tdoc:figure/F-1', 'hasTable': ['tdoc:table/T-1'],
                         'hasChart': 'tdoc:chart/C-1'}]}
            from unittest.mock import Mock, MagicMock
            def result(rows):
                return type('Rows', (list,), {'single': lambda self: self[0],
                                              'consume': lambda self: None})(rows)
            active = [None]
            def run(query, **params):
                if active[0] and 'MERGE (tbl:Table' in query:
                    raise active[0]
                if 'RETURN fig_cnt, tbl_cnt' in query:
                    return result([dict(fig_cnt=1, tbl_cnt=1, cht_cnt=1)])
                if ' AS nid' in query:
                    return result([])
                if 'RETURN count(*) AS n' in query:
                    return result([{'n': 1}])
                if 'RETURN count(r) AS c' in query:
                    return result([{'c': 0}])
                return result([])
            tx = MagicMock()
            tx.__enter__.return_value = tx
            tx.run.side_effect = run
            session = MagicMock()
            session.__enter__.return_value = session
            session.run.side_effect = run
            session.begin_transaction.return_value = tx
            session.execute_write.side_effect = lambda callback: callback(tx)
            driver = NS(session=lambda: session, close=Mock())
            with tempfile.TemporaryDirectory() as temp, \
                    patch.object(loader, 'INSTANCES_DIR', Path(temp)), \
                    patch.object(loader.GraphDatabase, 'driver', return_value=driver) as connect, \
                    contextlib.redirect_stdout(io.StringIO()):
                def write(changes):
                    for name in names:
                        (Path(temp) / name).write_text(json.dumps({'@graph': changes.get(name, [])}))
                invalid = [dict(valid, **{'figures.jsonld': [{'figureId': ''}]}),
                           dict(valid, **{'tables.jsonld': [{'tableId': '  '}]}),
                           dict(valid, **{'charts.jsonld': [{'chartId': 'C-1'}, {'chartId': 'C-1'}]}),
                           dict(valid, **{'resolutions_agreements.jsonld': [{'resolutionId': None}]}),
                           dict(valid, **{'resolutions_conclusions.jsonld': [{'resolutionId': 'AGR-1'}]})]
                for graphs in invalid:
                    write(graphs)
                    before = [(Path(temp) / name).read_bytes() for name in names]
                    with self.assertRaises(ValueError):
                        loader.main()
                    connect.assert_not_called()
                    self.assertEqual([(Path(temp) / name).read_bytes() for name in names], before)
                write(valid)
                for fault in (None, OSError('synthetic write'), KeyboardInterrupt()):
                    active[0] = fault
                    tx.commit.reset_mock()
                    driver.close.reset_mock()
                    if fault:
                        with self.assertRaises(type(fault)):
                            loader.main()
                        tx.commit.assert_not_called()
                    else:
                        self.assertEqual(loader.main()['figures'], 1)
                        tx.commit.assert_called_once()
                    driver.close.assert_called_once()
                    active[0] = None
                    for _ in range(2):
                        tx.commit.reset_mock()
                        self.assertEqual(loader.main()['tables'], 1)
                        tx.commit.assert_called_once()

    def test_ran1_resolution_identity_preflight_and_actual_transaction_retry(self):
        with patch('socket.socket.connect', side_effect=AssertionError('network denied')), \
                patch('socket.create_connection', side_effect=AssertionError('network denied')), \
                patch.dict('os.environ', {'NEO4J_PASSWORD': 'synthetic'}):
            path = ROOT / 'scripts/tsg/RAN/formal/RAN1/phase-2/neo4j/01_load_decisions.py'
            spec = importlib.util.spec_from_file_location('_actual_resolution_input', path)
            loader = importlib.util.module_from_spec(spec)
            before_path = sys.path[:]
            self.addCleanup(lambda: sys.path.__setitem__(slice(None), before_path))
            spec.loader.exec_module(loader)
            names = ('resolutions_agreements.jsonld', 'resolutions_conclusions.jsonld',
                     'resolutions_working_assumptions.jsonld')
            valid = {'resolutionId': 'AGR-123-1-001', 'content': 'Synthetic agreement',
                     'madeAt': 'tdoc:meeting/RAN1#123', 'resolutionBelongsTo': 'tdoc:agenda/123-1',
                     'references': ['tdoc:R1-1']}
            from unittest.mock import Mock, MagicMock
            def result(rows):
                return type('Rows', (list,), {'single': lambda self: self[0],
                                              'consume': lambda self: None})(rows)
            active = [None]
            def run(query, **params):
                if active[0] and 'SET res.content' in query:
                    raise active[0]
                if 'RETURN agr, con' in query:
                    return result([{'agr': 1, 'con': 0, 'wa': 0}])
                if 'RETURN n.resolutionId AS rid' in query:
                    return result([])
                if 'RETURN match_type' in query:
                    return result([{'match_type': 'exact'}])
                if 'RETURN count(*) AS n' in query:
                    return result([{'n': len(params['resolutions']) if 'resolutions' in params else 1}])
                if 'RETURN count(r) AS c' in query:
                    return result([{'c': 0}])
                if 'RETURN labels(r)' in query:
                    return result([{'labels': ['Resolution', 'Agreement'], 'count': 1}])
                return result([])
            tx = MagicMock()
            tx.__enter__.return_value = tx
            tx.run.side_effect = run
            session = MagicMock()
            session.__enter__.return_value = session
            session.run.side_effect = run
            session.begin_transaction.return_value = tx
            session.execute_write.side_effect = lambda callback: callback(tx)
            driver = NS(session=lambda: session, close=Mock())
            with tempfile.TemporaryDirectory() as temp, \
                    patch.object(loader, 'INSTANCES_DIR', Path(temp)), \
                    patch.object(loader, 'prepare_for_wg', return_value=[]), \
                    patch.object(loader, 'load_agenda_retention', return_value=object()), \
                    patch.object(loader, 'guarded_cleanup', side_effect=lambda db, *a, **k: loader.reclaim_stale_edges(db)), \
                    patch.object(loader, 'load_dispositions', return_value={}), \
                    patch.object(loader.GraphDatabase, 'driver', return_value=driver) as connect, \
                    contextlib.redirect_stdout(io.StringIO()):
                def write(graphs):
                    for filename, graph in zip(names, graphs):
                        (Path(temp) / filename).write_text(json.dumps({'@graph': graph}))
                for graphs in (([dict(valid, resolutionId='')], [], []),
                               ([dict(valid, resolutionId='  ')], [], []),
                               ([valid, dict(valid)], [], []), ([valid], [dict(valid)], [])):
                    write(graphs)
                    before = [(Path(temp) / name).read_bytes() for name in names]
                    with self.assertRaises(ValueError):
                        loader.main()
                    connect.assert_not_called()
                    self.assertEqual([(Path(temp) / name).read_bytes() for name in names], before)
                write(([valid], [], []))
                for fault in (OSError('synthetic write'), KeyboardInterrupt(), None):
                    active[0] = fault
                    tx.commit.reset_mock()
                    driver.close.reset_mock()
                    if fault:
                        with self.assertRaises(type(fault)):
                            loader.main()
                        tx.commit.assert_not_called()
                    else:
                        self.assertEqual(loader.main()['agreements'], 1)
                        tx.commit.assert_called_once()
                    driver.close.assert_called_once()
                    active[0] = None
                    for _ in range(2):
                        tx.commit.reset_mock()
                        self.assertEqual(loader.main()['agreements'], 1)
                        tx.commit.assert_called_once()

    def test_tr_main_retains_outputs_when_metadata_is_unavailable(self):
        spec = importlib.util.spec_from_file_location('_input_contract_atomic',
            ROOT / 'scripts/common/common/atomic_io.py')
        atomic = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(atomic)
        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'TSG_RAN'):
            path = ROOT / f"scripts/tsg/RAN/formal/{wg}/phase-9/tr-parser/01_parse_tr_chunks.py"
            for case in ('missing', 'missing_key', 'wrong_list', 'malformed', 'valid'):
                with self.subTest(wg=wg, case=case), tempfile.TemporaryDirectory() as tmp:
                    base = Path(tmp)
                    raw = base / 'input'; raw.mkdir()
                    out = base / 'output'; (out / '38.811').mkdir(parents=True)
                    chunk = out / '38.811/chunks.json'
                    summary = out / 'parse_summary.json'
                    chunk.write_bytes(b'existing chunks'); summary.write_bytes(b'existing summary')
                    metadata = base / 'metadata.json'
                    key = 'technicalReports' if wg in ('RAN1', 'RAN4') else 'documents'
                    row = {'trNumber': '38.811', 'targetRelease': 'Rel-15',
                           'trStatus': 'Under change control'}
                    if case == 'valid':
                        metadata.write_text(json.dumps([row] if wg == 'RAN4' else {key: [row]}))
                    elif case == 'missing_key': metadata.write_text('{}')
                    elif case == 'wrong_list': metadata.write_text(json.dumps({key: {}}))
                    elif case == 'malformed': metadata.write_text('{invalid')
                    parsed = []
                    def parse(*args):
                        parsed.append(args)
                        return []
                    def generate(sections, tr_number, release, status):
                        return ([{'chunkId': tr_number + '-4-001', 'trSectionId': tr_number + '-4',
                                  'release': release, 'status': status}],
                                dict(totalSections=1, excludedVoid=0, excludedContainer=0,
                                     chunkTargetSections=1, giantSections=0, annexSections=0,
                                     introductionCount=0, totalChunks=1, tokenDistribution={}))
                    env = dict(Path=Path, json=json, tempfile=tempfile,
                               write_json_atomic=atomic.write_json_atomic,
                               write_text_atomic=atomic.write_text_atomic, INPUT_DIR=raw, OUTPUT_DIR=out,
                               METADATA_PATH=metadata, configure_logging=lambda: None,
                               logger=NS(info=lambda *a: None, warning=lambda *a: None,
                                         error=lambda *a: None),
                               datetime=NS(now=lambda: NS(isoformat=lambda: 'fixed-time')),
                               discover_tr_files=lambda: {'38.811': raw / 'body.docx' if wg in ('RAN2', 'TSG_RAN')
                                                          else {'main': raw / 'body.docx', 'annexes': []}},
                               parse_tr_with_annexes=parse, parse_tr_for_vectordb=parse,
                               generate_chunks=generate)
                    function(path, 'load_tr_metadata', env)
                    function(path, 'save_chunks', env)
                    main = function(path, 'main', env)
                    if case == 'valid':
                        self.assertEqual(main(), 0)
                        self.assertEqual(len(parsed), 1)
                        saved = json.loads(chunk.read_text())['chunks'][0]
                        self.assertEqual((saved['release'], saved['status']),
                                         ('Rel-15', 'Under change control'))
                        self.assertEqual(json.loads(summary.read_text())['totalChunks'], 1)
                    else:
                        with self.assertRaises(json.JSONDecodeError if case == 'malformed' else SystemExit):
                            main()
                        self.assertEqual(parsed, [])
                        self.assertEqual(chunk.read_bytes(), b'existing chunks')
                        self.assertEqual(summary.read_bytes(), b'existing summary')

    def test_tsgran_loader_validates_before_open_and_rejects_embedding_loss(self):
        path = ROOT / "scripts/tsg/RAN/formal/TSG_RAN/phase-9/qdrant/01_load_qdrant.py"
        valid = dict(chunkId="38.999-4-001", trSectionId="38.999-4", trNumber="38.999",
                     sectionNumber="4", sectionTitle="Synthetic", level=1,
                     chunkIndex=1, totalChunks=1, text="Synthetic body")
        for case in ("duplicate", "collision", "missing_id", "missing_field", "title", "text", "lost_embedding"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                opened = []
                chunk = dict(valid)
                chunks = [chunk]
                titles = {"38.999": "Synthetic report"}
                if case in ("duplicate", "collision"):
                    chunks.append({**chunk, "chunkId": chunk["chunkId"] if case == "duplicate" else "different"})
                if case == "missing_id": chunk.pop("chunkId")
                if case == "missing_field": chunk.pop("level")
                if case == "title": titles.clear()
                if case == "text": chunk["text"] = None
                manager = NS(open_target=lambda **kw: opened.append(1),
                             get_collection_info=lambda: {"points_count": 0}, point_ids=lambda: set())
                config = NS(collection_name="synthetic", embedding_model="synthetic", embedding_dim=1,
                            parsed_base=root, tr_ontology=root / "titles.json", batch_size=1,
                            encoder=NS(provider="local"))
                env = dict(Config=object, EmbeddingClient=lambda _: object(), QdrantManager=lambda _: manager,
                           _abandon_staging_on_error=lambda fn: fn, PROJECT_ROOT=root, sys=sys,
                           load_all_chunks=lambda *a, **kw: chunks, load_tr_titles=lambda _: titles,
                           generate_point_id=(lambda _: 1) if case == "collision" else (lambda value: value),
                           time=NS(time=lambda: 1.0), process_batch=lambda *a: ([], 1))
                function(path, "embedding_text", env)
                run = function(path, "load_to_qdrant", env)
                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(RuntimeError if case == "lost_embedding" else (ValueError, KeyError)):
                        run(config)
                self.assertEqual(opened, [1] if case == "lost_embedding" else [])

    def test_cr_success_exit_requires_every_download_target(self):
        path = ROOT / "scripts/tsg/RAN/formal/RAN2/phase-0/change-requests/03_download_with_aria2c.py"
        spec = importlib.util.spec_from_file_location("synthetic_ran2_cr_download", path)
        producer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(producer)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = root / "input.txt"
            target = root / "RP-9990001.zip"
            plan.write_text(f"https://example.invalid/{target.name}\n  dir={root}\n  out={target.name}\n")
            with patch.object(producer, "unshare_aria2c_targets", return_value=0), \
                    patch.object(producer.subprocess, "run", return_value=NS(returncode=0)), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertFalse(producer.download_with_aria2c(plan, root / "run.log", "synthetic"))

    def test_json_number_boundaries_and_object_keys(self):
        spec=importlib.util.spec_from_file_location("json_stream_test",COMMON/"json_stream.py")
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"x.json"
            for read in (1,2,3,4,7):
                mod._READ=read
                for raw in ('{"chunks":[1e2,-3.75,0.001,1E-3]}','{"before":-1.25e+2,"chunks":[{"n":2e3}],"after":0.3}'):
                    p.write_text(raw)
                    self.assertEqual(list(mod.iter_array(p,"chunks")),json.loads(raw)["chunks"])
                for raw in ('{1:[],"chunks":[]}','{"chunks":[1e]}','{"chunks":[1.]}'):
                    p.write_text(raw)
                    with self.assertRaises((ValueError,json.JSONDecodeError)): list(mod.iter_array(p,"chunks"))

    def test_malformed_mail_index_fails_before_network(self):
        mail=ROOT/"scripts/tsg/RAN/email/common/phase-0"
        spec=importlib.util.spec_from_file_location('mail_index_contract',ROOT/'scripts/common/common/email_message_index.py')
        index=importlib.util.module_from_spec(spec);spec.loader.exec_module(index)
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            env={"source_path":lambda _:base,"json":json,
                 "load_archive_records":index.load_archive_records,"index_identities":index.index_identities}
            for filename,name,inputname in (("03_crawl_message_detail.py","crawl_details_for_wg","message_index.jsonl"),("02b_refresh_message_index.py","refresh_wg","archives.jsonl")):
                for raw in ("{invalid}\n", "[]\n", "{}\n"):
                    (base/inputname).write_text(raw)
                    with contextlib.redirect_stdout(io.StringIO()): result=function(mail/filename,name,env)("RAN1")
                    self.assertFalse(result if isinstance(result,bool) else result["ok"])

    def test_every_http_retry_acquires_token(self):
        path=ROOT/"scripts/tsg/RAN/email/common/phase-0/03_crawl_message_detail.py"
        acquired=[];calls=[]
        class HTTPError(Exception): pass
        def get(*a,**kw):
            calls.append(1)
            if len(calls)<3: raise OSError("temporary")
            return NS(content=b"ok",encoding="utf-8",raise_for_status=lambda:None)
        env={"_acquire_token":lambda:acquired.append(1),"requests":NS(get=get,HTTPError=HTTPError),"HEADERS":{},"time":NS(sleep=lambda _:None)}
        self.assertEqual(function(path,"fetch_with_rate_limit",env)("unused"),(b"ok","utf-8"))
        self.assertEqual(len(acquired),3)

    def test_cypher_string_literals(self):
        path=ROOT/"scripts/tsg/RAN/domain-vocab/domain_utils.py"
        env={"Optional":__import__('typing').Optional,"get_ts_terms":lambda *a,**kw:[],"expand_search_term":lambda *a,**kw:re.escape(a[0])}
        literal=function(path,"_cypher_literal",env)
        contains=function(path,"expand_cypher_contains",env)
        regex=function(path,"expand_cypher_regex",env)
        text="vendor's \\ beam\n"
        self.assertEqual(contains(text),f"(content CONTAINS {literal(text)})")
        self.assertEqual(regex(text),f"sectionTitle =~ {literal('(?i).*'+re.escape(text)+'.*')}")
        self.assertIn("\\'",literal(text));self.assertIn("\\n",literal(text))

    def test_split_impact_section_aggregates_all_chunks(self):
        path=ROOT/"scripts/tsg/RAN/formal/TSG_RAN/phase-5/tr-parser/03_build_impact_evidence.py"
        chunks=[dict(trSectionId="38.1-5",sectionNumber="5",sectionTitle="Impact",chunkIndex=i,text=t) for i,t in ((2,"second"),(1,"first"),(3,"third"))]
        env={"QdrantClient":object,"Embedder":object,"scroll_tr_sections":lambda *a:chunks,"IMPACT_TITLE_RE":re.compile("Impact"),"SOURCE_COLLECTION":"unused","A1_SEMANTIC_TOPK":1,"Filter":lambda **kw:kw,"FieldCondition":lambda **kw:kw,"MatchValue":lambda **kw:kw}
        qc=NS(query_points=lambda **kw:NS(points=[]));emb=NS(embed=lambda *a:[])
        result=function(path,"select_impact_sections",env)(qc,emb,{"trNumber":"38.1"})
        self.assertEqual(result[0]["text"],"first\nsecond\nthird")

    def test_version_stem_and_structured_equation(self):
        for wg in range(1,6):
            p=ROOT/f"scripts/tsg/RAN/formal/RAN{wg}/phase-5/tr-parser/01_parse_tr_docs.py"
            if wg == 1:
                fn=function(p,"extract_tr_version_from_filename",{"re":re})
                self.assertEqual(fn("38769-j00"),"19.0.0");self.assertEqual(fn("38765-020"),"0.2.0")
            elif wg in (2,3):
                fn=function(p,"extract_version_and_release",{"re":re,"RELEASE_CODE":{"j":19},"_hex_digit":lambda x:int(x,36)})
                self.assertEqual(fn("38769-j00")[0],"19.0.0")
            p=ROOT/f"scripts/tsg/RAN/formal/RAN{wg}/phase-6/tdoc-parser/05_enhance_equations.py"
            fn=function(p,"omml_to_latex_simple",{"docx_text":NS(math_text=lambda _:"x2")})
            structured=ET.fromstring('<m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"><m:sSup><m:e><m:r><m:t>x</m:t></m:r></m:e><m:sup><m:r><m:t>2</m:t></m:r></m:sup></m:sSup></m:oMath>')
            self.assertEqual(fn(structured),"")
            self.assertEqual(fn(ET.fromstring('<oMath><r><t>x2</t></r></oMath>')),"x2")

    def test_nested_failure_remains_failure_on_resume(self):
        for wg in range(1,6):
            path=ROOT/f"scripts/tsg/RAN/formal/RAN{wg}/phase-0/extract/extract_meetings.py"
            with tempfile.TemporaryDirectory() as tmp:
                source=Path(tmp)/"source";source.mkdir();dest=Path(tmp)/"derived"
                archive=source/"outer.zip"
                with zipfile.ZipFile(archive,"w") as z:z.writestr("inner.zip",b"bad zip")
                env={"SOURCE_DIR":source,"EXTRACT_DIR":dest,"zipfile":zipfile,"zlib":zlib,"logging":logging,"os_residue":NS(classify_path=lambda _:None),"zip_names":NS(extractall=lambda z,p:z.extractall(p)),"cleanup_os_metadata":lambda _:None,"extract_with_7z":lambda *a:False,"rar_archive":NS(extract=lambda *a:False),"failure_kind":lambda _:"binary","drop_failed_output":lambda p:shutil.rmtree(p,ignore_errors=True)}
                function(path,"extract_nested_archives",env);fn=function(path,"extract_zip_recursive",env)
                with self.assertLogs(level="ERROR"):
                    self.assertEqual(fn(archive)[0],"nested_error")
                    self.assertEqual(fn(archive)[0],"nested_error")

    def test_release_plan_keeps_existing_on_input_only(self):
        for wg in (1,2,4,5):
            path=ROOT/f"scripts/tsg/RAN/formal/RAN{wg}/phase-9/tr-parser/02_parse_release_chunks.py"
            with tempfile.TemporaryDirectory() as tmp:
                raw=Path(tmp)/"raw";(raw/"38.1"/"Rel-19").mkdir(parents=True)
                out=Path(tmp)/"out";out.mkdir();plan=out/"release_groups.json";plan.write_text("keep")
                parser=NS(load_tr_meta_from_neo4j=lambda:{},TR_FILES={},load_tr_metadata=lambda:{},discover_tr_files=lambda:{"38.1":{}},parse_tr_with_annexes=lambda *a:[],generate_chunks=lambda *a:([{"sectionNumber":"5","text":"input"}],{}))
                env={"OUT_DIR":out,"RAW_DIR":raw,"WG":f"RAN{wg}","p9":parser,"defaultdict":defaultdict,"rel_key":lambda x:str(x),"INPUT_REL":"__input__","find_main_docx":lambda *a:None,"hashlib":__import__('hashlib'),"sys":sys,"json":json}
                with contextlib.redirect_stdout(io.StringIO()),self.assertRaises(SystemExit) as ex: function(path,"main",env)()
                self.assertEqual(ex.exception.code,1);self.assertEqual(plan.read_text(),"keep")

    def test_release_plan_rejects_empty_release_among_valid_releases(self):
        for wg in (1,2,4,5):
            path=ROOT/f"scripts/tsg/RAN/formal/RAN{wg}/phase-9/tr-parser/02_parse_release_chunks.py"
            with tempfile.TemporaryDirectory() as tmp:
                raw=Path(tmp)/"raw"
                for rel in ("Rel-18","Rel-19"):(raw/"38.1"/rel).mkdir(parents=True)
                out=Path(tmp)/"out";out.mkdir();plan=out/"release_groups.json";plan.write_text("keep")
                parser=NS(load_tr_meta_from_neo4j=lambda:{},load_tr_metadata=lambda:{},discover_tr_files=lambda:{},TR_FILES={})
                def parse(tr,docx,*args):
                    return [] if docx.parent.name=="Rel-18" else [{"sectionNumber":"5","text":"valid"}]
                env={"OUT_DIR":out,"RAW_DIR":raw,"WG":f"RAN{wg}","p9":parser,"defaultdict":defaultdict,"rel_key":lambda x:str(x),"INPUT_REL":"__input__","find_main_docx":lambda d,*a:d/"body.docx","parse_docx":parse,"hashlib":__import__('hashlib'),"sys":sys,"json":json}
                with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit) as ex:function(path,"main",env)()
                self.assertEqual(ex.exception.code,1);self.assertEqual(plan.read_text(),"keep")

if __name__ == "__main__": unittest.main()
