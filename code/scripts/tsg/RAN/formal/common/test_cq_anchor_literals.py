#!/usr/bin/env python3
"""Spec: formal CQ anchor contract; Ontology: identifier string predicates; Cycle: scope.
배경: 쿼리 문자열과 실제 KG parameter가 같은 값을 가리키는지 검증한다.
사용: python3 -B scripts/tsg/RAN/formal/common/test_cq_anchor_literals.py
LLM 호출: 0. Neo4j 세션은 오프라인 대역으로만 확인한다.
Source: https://neo4j.com/docs/cypher-manual/current/values-and-types/boolean-numeric-string/
"""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import cq_anchor_guard as guard


class LiteralTests(unittest.TestCase):
    def test_all_anchor_forms_decode_actual_values(self):
        for query in (r"MATCH (n:X {id:'O\'Brien'}) RETURN n",
                      r"MATCH (n:X) WHERE n.id = 'O\'Brien' RETURN n",
                      r"MATCH (n:X) WHERE 'O\'Brien' = n.id RETURN n",
                      r"MATCH (n:X) WHERE n.id IN ['O\'Brien'] RETURN n",
                      r"MATCH (n:X) WHERE 'O\'Brien' IN n.id RETURN n"):
            with self.subTest(query=query):
                self.assertEqual(guard.extract_anchors(query)[0]['value'], "O'Brien")

    def test_unicode_and_control_sequences_preserve_unescaped_unicode(self):
        query = r"MATCH (n:X) WHERE n.id IN ['한글\u0041','a\tb','c\\d','\uD83D\uDE00'] RETURN n"
        self.assertEqual([a['value'] for a in guard.extract_anchors(query)], ['한글A', 'a\tb', 'c\\d', '😀'])

    def test_comments_and_query_text_are_not_anchors(self):
        query = """// MATCH (ghost:Missing {id:'absent'})
MATCH (n:X {id:'present'})
/* WHERE n.id IN ['also absent'] */
RETURN "MATCH (ghost:Missing {id:'inside string'})" AS example"""
        self.assertEqual([a['value'] for a in guard.extract_anchors(query)], ['present'])

    def test_double_quoted_literals_and_quoted_comment_markers(self):
        query = 'MATCH (n:X {id:"https://example/a/*b*/"}) WHERE n.other IN ["A", "B"] RETURN n'
        self.assertEqual([a['value'] for a in guard.extract_anchors(query)], ['https://example/a/*b*/', 'A', 'B'])

    def test_commented_edges_do_not_change_spec_identity_roles(self):
        query = "MATCH (s:Spec)-[:BELONGS]->(x) RETURN s // MATCH (s)-[:MODIFIES]->(y)"
        roles = guard.spec_roles(query, {('BELONGS', True): 'release', ('MODIFIES', True): 'hub'})
        self.assertEqual(roles, {'s': {'release': {'BELONGS'}}})

    def test_decoded_value_reaches_parameterized_existence_query(self):
        seen = []
        class Session:
            def run(self, query, **parameters):
                seen.append((query, parameters))
                return SimpleNamespace(single=lambda: {'hit': 1} if parameters['v'] == 'A' else None)
        anchors = guard.check_anchors(Session(), r"MATCH (n:X {id:'\u0041'}) RETURN n")
        self.assertTrue(anchors[0]['exists'])
        self.assertEqual(seen[0][1], {'v': 'A'})
        self.assertNotIn('\\u0041', seen[0][0])

    def test_regex_and_display_strings_are_opaque_to_anchor_decoder(self):
        query = r"MATCH (n:X {id:'A'}) WHERE n.text =~ '38\.213' RETURN '\q' AS example"
        self.assertEqual([a['value'] for a in guard.extract_anchors(query)], ['A'])
        self.assertEqual(guard.spec_roles(query, {}), {})

    def test_invalid_anchor_escape_is_still_rejected(self):
        with self.assertRaisesRegex(ValueError, 'escape'):
            guard.extract_anchors(r"MATCH (n:X {id:'A\q'}) RETURN n")

    def test_semantic_qualifiers_do_not_require_a_nonempty_population(self):
        query = "MATCH (r:Resolution {resolutionId:'AGR-X'})-[:HAS_DISPOSITION]->(d:DecisionDisposition {evidenceStatus:'source_verified', dispositionCode:'agreed'}) RETURN d"
        anchors = guard.extract_anchors(query)
        self.assertEqual([(a['prop'], a['value']) for a in anchors], [('resolutionId', 'AGR-X')])
        self.assertEqual(guard.extract_anchors("MATCH (d:TRImpact) WHERE d.evidenceStatus IN ['source_verified'] RETURN count(d)"), [])

    def test_verified_impact_scope_is_a_population_qualifier(self):
        for query in (
            "MATCH (d:TRImpact {verifiedImpactScope:'new_specification'}) RETURN d.verifiedImpactScope",
            "MATCH (d:TRImpact) WHERE d.verifiedImpactScope IN ['explicit_no_change'] RETURN count(d)",
        ):
            self.assertEqual(guard.extract_anchors(query), [])

    @staticmethod
    def unknown_session(*names):
        notes = [{'code': 'Neo.ClientNotification.Statement.UnknownPropertyKeyWarning',
                  'description': f'The property key does not exist (the missing property name is: {name})'}
                 for name in names]
        return SimpleNamespace(run=lambda query: SimpleNamespace(
            consume=lambda: SimpleNamespace(notifications=notes)))

    def test_declared_optional_qualifier_may_have_no_live_property_token(self):
        query = "MATCH (d:TRImpact {verifiedImpactScope:'new_specification'}) RETURN d.verifiedImpactScope"
        self.assertEqual(guard.schema_unknowns(self.unknown_session('verifiedImpactScope'), query), [])
        self.assertEqual(guard.schema_unknowns(self.unknown_session('verifiedImpactScop', 'id'), query),
                         [{'kind': 'property', 'name': 'verifiedImpactScop'},
                          {'kind': 'property', 'name': 'id'}])

    def test_qualifier_exemption_requires_a_current_core_declaration(self):
        with patch.object(guard, '_current_declared_semantic_qualifiers', return_value=frozenset()):
            self.assertEqual(guard.schema_unknowns(self.unknown_session('verifiedImpactScope'), 'RETURN 1'),
                             [{'kind': 'property', 'name': 'verifiedImpactScope'}])

    def test_authored_cq026_has_no_string_escape_ambiguity(self):
        import json
        from pathlib import Path
        root = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
        data = json.loads((root / 'scripts/common/bootstrap/seeds/formal-cq/RAN1/phase-3.json').read_text())
        cq = next(row for row in data['questions'] if row['id'] == 'CQ026')
        self.assertIn('38[.]213', cq['cypher'])
        self.assertEqual(guard.extract_anchors(cq['cypher']), [])


class NonnullContractTests(unittest.TestCase):
    def test_ran1_phase5_actual_seed_rows_minimum_read_and_retry(self):
        import importlib.util
        import io
        import json
        import sys
        import tempfile
        from contextlib import redirect_stdout
        from pathlib import Path
        root = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
        self.addCleanup(sys.path.__setitem__, slice(None), sys.path.copy())
        sys.path.insert(0, str(root / 'scripts/common'))
        from common import credentials, atomic_io
        path = root / 'scripts/tsg/RAN/formal/RAN1/phase-5/validation/01_validate_cq_cypher.py'
        spec = importlib.util.spec_from_file_location('actual_ran1_phase5_cq', path)
        consumer = importlib.util.module_from_spec(spec)
        with patch.object(credentials, 'neo4j_password', return_value='synthetic'):
            spec.loader.exec_module(consumer)
        seed = json.loads((root / 'scripts/common/bootstrap/seeds/formal-cq/RAN1/phase-5.json').read_text())
        self.assertEqual(len(seed['questions']), 18)
        class Rows(list):
            def single(self): return self[0] if self else None
            def consume(self): return SimpleNamespace(notifications=[])
        mode, sessions, closed, queries = {'case': 'normal'}, [], [], []
        class Session:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def run(self, query, **parameters):
                if query.startswith('EXPLAIN') or query == guard._SPEC_IDENTITY_Q: return Rows()
                if 'RETURN 1 AS hit' in query: return Rows([{'hit': 1}])
                queries.append(query)
                if mode['case'] == 'error': raise OSError('synthetic query failure')
                if mode['case'] == 'interrupt': raise KeyboardInterrupt('synthetic interruption')
                if mode['case'] == 'empty': return Rows()
                return Rows([{'tr.scope': None if mode['case'] == 'null' else 'source scope',
                              'tr.conclusions': 'source conclusion'}])
        class Driver:
            def verify_connectivity(self):
                if mode['case'] == 'connectivity': raise OSError('synthetic connection failure')
            def session(self, **options):
                sessions.append(options)
                if mode['case'] == 'session': raise OSError('synthetic session failure')
                return Session()
            def close(self): closed.append(True)
        with tempfile.TemporaryDirectory() as td, patch.object(consumer.GraphDatabase, 'driver', return_value=Driver()):
            td = Path(td)
            consumer.CQ_PATH, consumer.OUTPUT_PATH = td / 'dataset.json', td / 'result.json'
            consumer.CQ_PATH.write_text(json.dumps(seed))
            def run():
                with redirect_stdout(io.StringIO()):
                    try: code = consumer.main()
                    except SystemExit as exc: code = exc.code
                return code, json.loads(consumer.OUTPUT_PATH.read_text())
            for case, expected in (('normal', None), ('empty', 1), ('error', 1), ('null', 1), ('normal', None)):
                mode['case'] = case
                before, start = len(closed), len(queries)
                code, report = run()
                self.assertEqual(code, expected)
                self.assertEqual(queries[start:], [q['cypher'] for q in seed['questions']])
                self.assertEqual(len(closed), before + 1)
                if case in ('empty', 'error'):
                    self.assertTrue(all(r['status'] == ('NO_DATA' if case == 'empty' else 'ERROR') for r in report['results']))
            seed['questions'][0]['expected_min_rows'] = 2
            consumer.CQ_PATH.write_text(json.dumps(seed))
            code, report = run()
            self.assertEqual(code, 1)
            self.assertEqual(report['results'][0]['status'], 'FAIL')
            seed['questions'][0]['expected_min_rows'] = 0
            consumer.CQ_PATH.write_text(json.dumps(seed))
            mode['case'] = 'empty'
            self.assertEqual(run()[1]['results'][0]['status'], 'PASS')
            mode['case'] = 'error'
            self.assertEqual(run()[1]['results'][0]['status'], 'ERROR')
            mode['case'] = 'normal'
            for invalid_minimum in (True, -1, '2'):
                seed['questions'][0]['expected_min_rows'] = invalid_minimum
                consumer.CQ_PATH.write_text(json.dumps(seed))
                old, before = consumer.OUTPUT_PATH.read_bytes(), len(closed)
                with self.assertRaises(ValueError): run()
                self.assertEqual(consumer.OUTPUT_PATH.read_bytes(), old)
                self.assertEqual(len(closed), before)
            seed['questions'][0].pop('expected_min_rows')
            consumer.CQ_PATH.write_text(json.dumps(seed))
            self.assertIsNone(run()[0])
            for case, error in (('connectivity', OSError), ('session', OSError), ('interrupt', KeyboardInterrupt)):
                mode['case'] = case
                old, before = consumer.OUTPUT_PATH.read_bytes(), len(closed)
                with self.assertRaises(error): run()
                self.assertEqual(consumer.OUTPUT_PATH.read_bytes(), old)
                self.assertEqual(len(closed), before + 1)
                mode['case'] = 'normal'
                self.assertIsNone(run()[0])
            for boundary in ('fsync', 'replace'):
                for error in (OSError, KeyboardInterrupt):
                    old = consumer.OUTPUT_PATH.read_bytes()
                    with patch.object(atomic_io.os, boundary, side_effect=error('synthetic publication')), self.assertRaises(error): run()
                    self.assertEqual(consumer.OUTPUT_PATH.read_bytes(), old)
                    self.assertFalse(list(td.glob('.result.json.*.tmp')))
                    for _ in range(2): self.assertIsNone(run()[0])
            self.assertTrue(all(s == {'default_access_mode': consumer.READ_ACCESS} for s in sessions))

    def test_ran1_phase4_generated_dataset_reaches_actual_consumer_and_retries(self):
        import importlib.util
        import io
        import json
        import sys
        import tempfile
        from contextlib import redirect_stdout
        from pathlib import Path
        root = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
        self.addCleanup(sys.path.__setitem__, slice(None), sys.path.copy())
        sys.path.insert(0, str(root / 'scripts/common'))
        from common import credentials
        from common import atomic_io
        modules = []
        for name, filename in (('producer', '01_create_cq_dataset.py'),
                               ('consumer', '02_validate_cq_cypher.py')):
            path = root / 'scripts/tsg/RAN/formal/RAN1/phase-4/validation' / filename
            spec = importlib.util.spec_from_file_location('cq_ran1_phase4_' + name, path)
            module = importlib.util.module_from_spec(spec)
            with patch.object(credentials, 'neo4j_password', return_value='synthetic'):
                spec.loader.exec_module(module)
            modules.append(module)
        producer, consumer = modules
        class Rows(list):
            def single(self): return self[0] if self else None
            def consume(self): return SimpleNamespace(notifications=[])
        mode, queries, sessions, closed = {'case': 'normal'}, [], [], []
        class Session:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def run(self, query, **parameters):
                if query.startswith('EXPLAIN') or query == guard._SPEC_IDENTITY_Q:
                    return Rows()
                if 'RETURN 1 AS hit' in query:
                    return Rows([{'hit': 1}])
                queries.append(query)
                if mode['case'] == 'error': raise OSError('synthetic query failure')
                if mode['case'] == 'interrupt': raise KeyboardInterrupt('synthetic query interruption')
                return Rows() if mode['case'] == 'empty' else Rows([{'source': 'synthetic'}])
        class Driver:
            def verify_connectivity(self): pass
            def session(self, **options): sessions.append(options); return Session()
            def close(self): closed.append(True)
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            producer.OUTPUT_PATH = consumer.CQ_PATH = td / 'dataset.json'
            consumer.OUTPUT_PATH = td / 'result.json'
            def produce():
                with redirect_stdout(io.StringIO()): return producer.main()
            self.assertEqual(produce(), 0)
            data = json.loads(producer.OUTPUT_PATH.read_text())
            self.assertEqual(len(data['questions']), 15)
            self.assertEqual(len({q['id'] for q in data['questions']}), 15)
            self.assertEqual([sum(q['category'].startswith(cat) for q in data['questions'])
                              for cat in ('CQ1_', 'CQ2_', 'CQ3_', 'CQ4_')], [3, 4, 3, 5])
            self.assertEqual(produce(), 0)
            for boundary in ('fsync', 'replace'):
                for error in (OSError, KeyboardInterrupt):
                    previous = producer.OUTPUT_PATH.read_bytes()
                    with patch.object(atomic_io.os, boundary, side_effect=error('synthetic publication')), \
                            self.assertRaises(error):
                        produce()
                    self.assertEqual(producer.OUTPUT_PATH.read_bytes(), previous)
                    self.assertEqual(list(td.glob('.dataset.json.*.tmp')), [])
                    self.assertEqual(produce(), 0)
                    self.assertEqual(json.loads(producer.OUTPUT_PATH.read_text()), data)
            with patch.object(consumer.GraphDatabase, 'driver', return_value=Driver()):
                for case, expected in (('normal', 0), ('empty', 1), ('error', 1),
                                       ('normal', 0), ('normal', 0)):
                    mode['case'] = case
                    start, close_count = len(queries), len(closed)
                    with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as result:
                        consumer.main()
                    self.assertEqual(result.exception.code, expected)
                    self.assertEqual(queries[start:], [q['cypher'] for q in data['questions']])
                    report = json.loads(consumer.OUTPUT_PATH.read_text())
                    self.assertEqual(report['summary']['total'], 15)
                    field = {'normal': 'pass', 'empty': 'no_data', 'error': 'error'}[case]
                    self.assertEqual(report['summary'][field], 15)
                    self.assertEqual(len(closed), close_count + 1)
                mode['case'] = 'interrupt'
                previous, close_count = consumer.OUTPUT_PATH.read_bytes(), len(closed)
                with redirect_stdout(io.StringIO()), self.assertRaises(KeyboardInterrupt):
                    consumer.main()
                self.assertEqual(consumer.OUTPUT_PATH.read_bytes(), previous)
                self.assertEqual(len(closed), close_count + 1)
                mode['case'] = 'normal'
                with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as result:
                    consumer.main()
                self.assertEqual(result.exception.code, 0)
                self.assertTrue(all(s == {'default_access_mode': consumer.READ_ACCESS} for s in sessions))
            self.assertEqual(json.loads(producer.OUTPUT_PATH.read_text()), data)

    def test_ran1_phase1_rows_read_close_publication_and_cli_contract(self):
        self._check_ran1_early_consumer(1)

    def test_ran1_phase2_rows_close_publication_and_cli_contract(self):
        self._check_ran1_early_consumer(2)

    def _check_ran1_early_consumer(self, phase):
        import ast
        import importlib.util
        import io
        import json
        import sys
        import tempfile
        from contextlib import closing, redirect_stdout
        from datetime import datetime
        from pathlib import Path
        root = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
        atomic_spec = importlib.util.spec_from_file_location(
            'cq_phase2_fixture_atomic_io', root / 'scripts/common/common/atomic_io.py')
        atomic_io = importlib.util.module_from_spec(atomic_spec)
        atomic_spec.loader.exec_module(atomic_io)
        path = root / f'scripts/tsg/RAN/formal/RAN1/phase-{phase}/validation/01_validate_cq_cypher.py'
        tree = ast.parse(path.read_text())
        functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
        entry = ast.Module(body=[tree.body[-1]], type_ignores=[])
        mode, closed, sessions = {'case': 'normal'}, [], []
        class Rows(list):
            def consume(self): return SimpleNamespace(notifications=[])
        class Session:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def run(self, query, **parameters):
                if query.startswith('EXPLAIN') or query == guard._SPEC_IDENTITY_Q:
                    return Rows()
                if mode['case'] == 'query_error': raise OSError('synthetic query')
                if mode['case'] == 'interrupt': raise KeyboardInterrupt('synthetic interruption')
                if mode['case'] == 'empty': return Rows()
                row = {'scope': 'source evidence', 'n': 1}
                if mode['case'] == 'null': row['scope'] = None
                if mode['case'] == 'zero': row['n'] = 0
                if mode['case'] == 'missing': row.clear()
                if mode['case'] == 'mixed': return Rows([row, {**row, 'scope': None}])
                return Rows([row])
        class Driver:
            def session(self, **options):
                sessions.append(options)
                if mode['case'] == 'session_error': raise OSError('synthetic session')
                return Session()
            def close(self): closed.append(True)
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            dataset, output = td / 'cq.json', td / 'result.json'
            question = dict(id='synthetic-CQ', category='fixture', question='fixture',
                cypher='RETURN 1 AS n', nonnull_columns=['scope'], nonzero_columns=['n'])
            dataset.write_text(json.dumps({'questions': [question]}))
            namespace = dict(__name__='__main__', json=json, sys=sys, datetime=datetime, closing=closing,
                GraphDatabase=SimpleNamespace(driver=lambda *args, **kwargs: Driver()),
                guard_defects=guard.guard_defects, write_json_atomic=atomic_io.write_json_atomic,
                READ_ACCESS='READ',
                get_cache_metadata_with_hash=lambda **values: {key: value for key, value in values.items()
                                                               if key != 'dataset_path'},
                CQ_DATASET_PATH=dataset, OUTPUT_PATH=output, URI='fixture', AUTH=('fixture', 'fixture'))
            exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), 'exec'), namespace)
            def run():
                with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as exit_value:
                    exec(compile(entry, str(path), 'exec'), namespace)
                return exit_value.exception.code, json.loads(output.read_text())
            for case, expected in (('normal', 'PASS'), ('null', 'FAIL'), ('zero', 'FAIL'),
                    ('missing', 'FAIL'), ('mixed', 'FAIL'), ('empty', 'NO_DATA'),
                    ('query_error', 'FAIL'), ('normal', 'PASS')):
                mode['case'] = case
                count = len(closed)
                code, report = run()
                self.assertEqual(report['results'][0]['status'], expected)
                self.assertEqual(code, 0 if expected == 'PASS' else 1)
                self.assertEqual(len(closed), count + 1)
            first = report['results']
            self.assertEqual(run()[1]['results'], first)
            for case, error in (('session_error', OSError), ('interrupt', KeyboardInterrupt)):
                mode['case'] = case
                previous, count = output.read_bytes(), len(closed)
                with self.assertRaises(error), redirect_stdout(io.StringIO()):
                    namespace['run_validation']()
                self.assertEqual(output.read_bytes(), previous)
                self.assertEqual(len(closed), count + 1)
            mode['case'] = 'normal'
            for boundary in ('fsync', 'replace'):
                for error in (OSError, KeyboardInterrupt):
                    previous = output.read_bytes()
                    with patch.object(atomic_io.os, boundary, side_effect=error('synthetic publication')), \
                            self.assertRaises(error), redirect_stdout(io.StringIO()):
                        namespace['run_validation']()
                    self.assertEqual(output.read_bytes(), previous)
                    self.assertEqual(list(td.glob('.result.json.*.tmp')), [])
                    self.assertEqual(run()[0], 0)
            previous, count = output.read_bytes(), len(closed)
            dataset.write_text(json.dumps({'questions': []}))
            with self.assertRaises(SystemExit), redirect_stdout(io.StringIO()):
                namespace['run_validation']()
            self.assertEqual(output.read_bytes(), previous)
            self.assertEqual(len(closed), count)
            if phase == 1:
                self.assertTrue(sessions)
                self.assertTrue(all(options == {'default_access_mode': 'READ'} for options in sessions))

    def test_ran5_phase1_rows_read_close_publication_and_retry(self):
        self._check_ran5_formal_consumer(1)

    def test_ran5_phase2_rows_read_close_publication_and_retry(self):
        self._check_ran5_formal_consumer(2)

    def _check_ran5_formal_consumer(self, phase):
        import importlib.util
        import io
        import json
        import sys
        import tempfile
        from contextlib import redirect_stdout
        from pathlib import Path
        root = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
        sys.path.insert(0, str(root / 'scripts/common'))
        from common import credentials, atomic_io
        path = root / f'scripts/tsg/RAN/formal/RAN5/phase-{phase}/validation/01_validate_cq_cypher.py'
        spec = importlib.util.spec_from_file_location(f'ran5_phase{phase}_actual_fixture', path)
        module = importlib.util.module_from_spec(spec)
        with patch.object(credentials, 'neo4j_auth', return_value=('fixture', 'fixture')):
            spec.loader.exec_module(module)
        mode, closed, sessions = {'case': 'normal'}, [], []
        class Rows(list):
            def consume(self): return SimpleNamespace(notifications=[])
            def single(self): return self[0] if self else None
        class Session:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def run(self, cypher, **params):
                if cypher.startswith('EXPLAIN') or cypher == guard._SPEC_IDENTITY_Q: return Rows()
                if mode['case'] == 'query_error': raise OSError('synthetic query')
                if mode['case'] == 'interrupt': raise KeyboardInterrupt('synthetic interruption')
                if mode['case'] == 'empty': return Rows()
                row = dict(scope='source evidence', n=1)
                if mode['case'] == 'null': row['scope'] = None
                if mode['case'] == 'zero': row['n'] = 0
                if mode['case'] == 'missing': row.clear()
                if mode['case'] == 'mixed': return Rows([row, dict(row, scope=None)])
                return Rows([row])
        class Driver:
            def session(self, **options):
                sessions.append(options)
                if mode['case'] == 'session_error': raise OSError('synthetic session')
                return Session()
            def close(self): closed.append(True)
        with tempfile.TemporaryDirectory() as td, patch.object(module.GraphDatabase, 'driver', side_effect=lambda *a, **kw: Driver()):
            td = Path(td)
            dataset, output = td / 'cq.json', td / 'result.json'
            question = dict(id='synthetic-CQ', category='fixture', question='fixture', cypher='RETURN 1 AS n',
                            nonnull_columns=['scope'], nonzero_columns=['n'])
            dataset.write_text(json.dumps(dict(questions=[question])))
            if phase == 1:
                module.CQ_INPUT, module.CQ_OUTPUT = dataset, output
            else:
                module.DATASET, module.OUTPUT = dataset, output
            def run():
                with redirect_stdout(io.StringIO()):
                    try: value = module.main()
                    except SystemExit as error: value = error.code
                return value, json.loads(output.read_text())
            for case, status in (('normal', 'PASS'), ('null', 'FAIL'), ('zero', 'FAIL'),
                                 ('missing', 'FAIL'), ('mixed', 'FAIL'), ('empty', 'FAIL'),
                                 ('query_error', 'ERROR'), ('normal', 'PASS')):
                mode['case'] = case
                before = len(closed)
                code, report = run()
                self.assertEqual(report['results'][0]['status'], status)
                self.assertIn(code, (0, None) if status == 'PASS' else (1,))
                self.assertEqual(len(closed), before + 1)
            normal = output.read_bytes()
            self.assertEqual(run()[1], report)
            question['expected_min_rows'] = 2
            dataset.write_text(json.dumps(dict(questions=[question])))
            code, minimum_report = run()
            self.assertEqual(code, 1)
            self.assertEqual(minimum_report['results'][0]['status'], 'WARN')
            question.pop('expected_min_rows')
            dataset.write_text(json.dumps(dict(questions=[question])))
            self.assertIn(run()[0], (0, None))
            self.assertEqual(output.read_bytes(), normal)
            question['expected_min_rows'] = 0
            dataset.write_text(json.dumps(dict(questions=[question])))
            for case, status, expected_code in (('empty', 'PASS', 0), ('query_error', 'ERROR', 1)):
                mode['case'] = case
                code, zero_report = run()
                self.assertIn(code, (0, None) if expected_code == 0 else (1,))
                self.assertEqual(zero_report['results'][0]['status'], status)
            mode['case'] = 'normal'
            question.pop('expected_min_rows')
            dataset.write_text(json.dumps(dict(questions=[question])))
            self.assertIn(run()[0], (0, None))
            self.assertEqual(output.read_bytes(), normal)
            for case, error in (('session_error', OSError), ('interrupt', KeyboardInterrupt)):
                mode['case'] = case
                before = len(closed)
                with self.assertRaises(error): run()
                self.assertEqual(output.read_bytes(), normal)
                self.assertEqual(len(closed), before + 1)
                mode['case'] = 'normal'
                self.assertIn(run()[0], (0, None))
            for operation in ('fsync', 'replace'):
                for error in (OSError, KeyboardInterrupt):
                    with patch.object(atomic_io.os, operation, side_effect=error('synthetic publication')):
                        with self.assertRaises(error): run()
                    self.assertEqual(output.read_bytes(), normal)
                    self.assertFalse(list(td.glob('.*.tmp')))
                    self.assertIn(run()[0], (0, None))
            before = len(closed)
            dataset.write_text(json.dumps(dict(questions=[])))
            with self.assertRaises(SystemExit), redirect_stdout(io.StringIO()):
                module.main()
            self.assertEqual(output.read_bytes(), normal)
            self.assertEqual(len(closed), before)
            self.assertTrue(sessions)
            self.assertTrue(all(options == dict(default_access_mode=module.READ_ACCESS) for options in sessions))

    def test_nonnull_preserves_false_zero_and_empty_string(self):
        cq = {'nonnull_columns': ['scope']}
        self.assertEqual(guard.nonnull_defects(cq, [{'scope': x} for x in (0, False, '', 'text')]), [])
        self.assertEqual(guard.nonnull_defects(cq, []), [])
        self.assertEqual(guard.nonnull_defects({}, None), [])

    def test_null_missing_and_mixed_rows_are_defects(self):
        cq = {'nonnull_columns': ['scope']}
        for rows in (None, [{}], [{'scope': None}], [{'scope': 'text'}, {'scope': None}]):
            with self.subTest(rows=rows):
                self.assertTrue(guard.nonnull_defects(cq, rows))
        for cols in (None, 'scope', [None], [''], [1]):
            with self.subTest(cols=cols):
                self.assertTrue(guard.nonnull_defects({'nonnull_columns': cols}, []))

    def test_actual_seed_contracts_reach_ten_consumers(self):
        import ast
        import importlib.util
        import io
        import json
        import sys
        import tempfile
        from contextlib import closing, redirect_stdout
        from datetime import datetime
        from pathlib import Path
        root = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
        atomic_spec = importlib.util.spec_from_file_location(
            'cq_fixture_atomic_io', root / 'scripts/common/common/atomic_io.py')
        atomic_io = importlib.util.module_from_spec(atomic_spec)
        atomic_spec.loader.exec_module(atomic_io)
        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            for phase in (4, 5):
                with self.subTest(wg=wg, phase=phase), tempfile.TemporaryDirectory() as td:
                    td = Path(td)
                    seed = json.loads((root / f'scripts/common/bootstrap/seeds/formal-cq/{wg}/phase-{phase}.json').read_text())
                    questions = ([dict(seed['questions'][0], nonnull_columns=['cr.reasonForChange'])]
                                 if wg == 'RAN1' and phase == 4 else
                                 [q for q in seed['questions'] if q.get('nonnull_columns')])
                    self.assertEqual(len(questions), (1 if phase == 4 else 6) if wg == 'RAN1' else 3 if phase == 4 else 4 if wg == 'RAN2' else 2)
                    dataset, output = td / 'cq.json', td / 'result.json'
                    dataset.write_text(json.dumps({**seed, 'questions': questions}))
                    query_columns = {q['cypher']: q['nonnull_columns'] for q in questions}
                    mode = {'case': 'normal'}
                    closed = []
                    class Rows(list):
                        def single(self):
                            return self[0] if self else None
                        def consume(self):
                            return SimpleNamespace(notifications=[])
                    class Session:
                        def __enter__(self):
                            return self
                        def __exit__(self, *args):
                            pass
                        def run(self, query, **parameters):
                            if query.startswith('EXPLAIN') or query == guard._SPEC_IDENTITY_Q:
                                return Rows()
                            if 'RETURN 1 AS hit' in query:
                                return Rows([{'hit': 1}])
                            if mode['case'] == 'query_error':
                                raise RuntimeError('synthetic query error')
                            if mode['case'] == 'interrupted':
                                raise KeyboardInterrupt('synthetic interruption')
                            row = {column: 'source evidence' for column in query_columns[query]}
                            if mode['case'] == 'null':
                                return Rows([{column: None for column in row}])
                            if mode['case'] == 'missing':
                                return Rows([{}])
                            if mode['case'] == 'mixed':
                                return Rows([row, {column: None for column in row}])
                            if mode['case'] == 'empty':
                                return Rows()
                            return Rows([row])
                    class Driver:
                        def session(self, **options):
                            if mode['case'] == 'session_error':
                                raise RuntimeError('synthetic session error')
                            return Session()
                        def verify_connectivity(self):
                            if mode['case'] == 'connectivity_error':
                                raise RuntimeError('synthetic connectivity error')
                        def close(self):
                            closed.append(True)
                    filename = '02_validate_cq_cypher.py' if wg == 'RAN1' and phase == 4 else '01_validate_cq_cypher.py'
                    path = root / f'scripts/tsg/RAN/formal/{wg}/phase-{phase}/validation/{filename}'
                    functions = [n for n in ast.parse(path.read_text()).body if isinstance(n, ast.FunctionDef)]
                    namespace = dict(json=json, sys=sys, datetime=datetime, closing=closing,
                        GraphDatabase=SimpleNamespace(driver=lambda *args, **kwargs: Driver()),
                        guard_defects=guard.guard_defects, CQ_PATH=dataset, DATASET=dataset, CQ_INPUT=dataset,
                        write_json_atomic=atomic_io.write_json_atomic, READ_ACCESS='READ',
                        write_text_atomic=atomic_io.write_text_atomic,
                        OUTPUT_PATH=output, OUTPUT=output, CQ_OUTPUT=output,
                        NEO4J_URI='fixture', NEO4J_USER='fixture', NEO4J_PASSWORD='fixture',
                        URI='fixture', AUTH=('fixture', 'fixture'))
                    exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), 'exec'), namespace)
                    def run():
                        with redirect_stdout(io.StringIO()):
                            try:
                                code = namespace['main']()
                            except SystemExit as error:
                                code = error.code
                        return code, json.loads(output.read_text())
                    for case, expected in (('normal', 'PASS'), ('null', 'FAIL'), ('missing', 'FAIL'),
                            ('mixed', 'FAIL'), ('empty', 'NO_DATA' if phase == 4 or wg in ('RAN1', 'RAN2') else 'FAIL'),
                            ('query_error', 'ERROR'), ('normal', 'PASS')):
                        mode['case'] = case
                        code, report = run()
                        self.assertTrue(all(r['status'] == expected for r in report['results']))
                        self.assertIn(code, (0, None) if expected == 'PASS' else (1,))
                    first = report['results']
                    _, report = run()
                    self.assertEqual(first, report['results'])
                    mode['case'] = 'session_error'
                    previous = output.read_bytes()
                    with self.assertRaisesRegex(RuntimeError, 'synthetic session error'):
                        run()
                    self.assertEqual(previous, output.read_bytes())
                    self.assertEqual(len(closed), 9)
                    expected_closed = 9
                    if phase == 4 or wg in ('RAN1', 'RAN2'):
                        mode['case'] = 'connectivity_error'
                        with self.assertRaisesRegex(RuntimeError, 'synthetic connectivity error'):
                            run()
                        self.assertEqual(previous, output.read_bytes())
                        expected_closed += 1
                        self.assertEqual(len(closed), expected_closed)
                    mode['case'] = 'interrupted'
                    with self.assertRaisesRegex(KeyboardInterrupt, 'synthetic interruption'):
                        run()
                    self.assertEqual(previous, output.read_bytes())
                    expected_closed += 1
                    self.assertEqual(len(closed), expected_closed)
                    mode['case'] = 'normal'
                    _, report = run()
                    self.assertTrue(all(r['status'] == 'PASS' for r in report['results']))
                    expected_closed += 1
                    self.assertEqual(len(closed), expected_closed)
                    original_temporary = atomic_io.tempfile.NamedTemporaryFile
                    class PartialWrite:
                        def __init__(self, stream, error):
                            self.stream, self.error = stream, error
                        def __enter__(self):
                            self.stream.__enter__()
                            return self
                        def __exit__(self, *args):
                            return self.stream.__exit__(*args)
                        def __getattr__(self, name):
                            return getattr(self.stream, name)
                        def write(self, text):
                            self.stream.write(text[:3])
                            self.stream.flush()
                            raise self.error('synthetic partial report write')
                    for error in (OSError, KeyboardInterrupt):
                        for boundary in ('partial_write', 'fsync', 'replace'):
                            with self.subTest(error=error.__name__, boundary=boundary):
                                previous = output.read_bytes()
                                def temporary(*args, **kwargs):
                                    return PartialWrite(original_temporary(*args, **kwargs), error)
                                target = atomic_io.tempfile if boundary == 'partial_write' else atomic_io.os
                                name = 'NamedTemporaryFile' if boundary == 'partial_write' else boundary
                                effects = {'side_effect': temporary} if boundary == 'partial_write' else {
                                    'side_effect': error('synthetic report publication failure')}
                                with patch.object(target, name, **effects), self.assertRaises(error):
                                    run()
                                self.assertEqual(previous, output.read_bytes())
                                self.assertEqual(list(td.glob('.result.json.*.tmp')), [])
                                _, report = run()
                                self.assertTrue(all(r['status'] == 'PASS' for r in report['results']))
                    if phase == 4:
                        original_minimum = questions[0].get('expected_min_rows')
                        questions[0]['expected_min_rows'] = 2
                        dataset.write_text(json.dumps({**seed, 'questions': questions}))
                        code, report = run()
                        self.assertEqual(code, 1)
                        self.assertEqual(report['results'][0]['status'], 'FAIL')
                        if original_minimum is None:
                            questions[0].pop('expected_min_rows')
                        else:
                            questions[0]['expected_min_rows'] = original_minimum
                        dataset.write_text(json.dumps({**seed, 'questions': questions}))
                        self.assertEqual(run()[0], 0)


class AuthoredQuestionMeaningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import importlib.util
        import json
        import shutil
        import sys
        import tempfile
        from pathlib import Path
        cls.repository = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        cls.addClassCleanup(sys.path.__setitem__, slice(None), sys.path.copy())
        relative = Path('scripts/common/bootstrap/seeds/formal-cq')
        shutil.copytree(cls.repository / relative, cls.root / relative)
        scope = cls.root / 'logs/common/bootstrap/scope.json'
        scope.parent.mkdir(parents=True)
        scope.write_text(json.dumps({'wgs': [f'RAN{i}' for i in range(1, 6)]}))
        path = cls.repository / 'scripts/common/bootstrap/materialize_formal_cq.py'
        spec = importlib.util.spec_from_file_location('cq_meaning_materializer', path)
        materializer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(materializer)
        for number in range(1, 6):
            receipt = materializer.materialize(cls.root, f'RAN{number}')
            if receipt['status'] != 'definitions_ready':
                raise AssertionError('CQ materialization did not complete')
        # RAN1 Phase-4 is delegated to this actual producer instead of being copied.
        path = cls.repository / 'scripts/tsg/RAN/formal/RAN1/phase-4/validation/01_create_cq_dataset.py'
        spec = importlib.util.spec_from_file_location('cq_meaning_ran1_producer', path)
        producer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(producer)
        cls.ran1_phase4 = producer.build_dataset()

    def questions(self, wg, phase):
        import json
        data = (self.ran1_phase4 if (wg, phase) == ('RAN1', 4) else json.loads(
            (self.root / f'logs/tsg/RAN/formal/{wg}/phase-{phase}/cq_test_dataset.json').read_text()))
        return {q['id']: q for q in data['questions']}

    def test_cross_spec_cr_totals_and_lists_count_documents_once(self):
        import json
        for number in range(1, 6):
            wg = f'RAN{number}'
            with self.subTest(wg=wg):
                question = self.questions(wg, 4)['CQ2-3']
                source = json.loads((self.repository / f'scripts/common/bootstrap/seeds/formal-cq/{wg}/phase-4.json').read_text())
                authored = next(q for q in source['questions'] if q['id'] == 'CQ2-3')
                self.assertEqual(question, authored)
                query = question['cypher']
                self.assertIn('AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC', query)
                if number == 1:
                    self.assertIn('count(DISTINCT cr) AS crCount', query)
                    self.assertIn('collect(DISTINCT cr.tdocNumber) AS crList', query)
                    self.assertNotIn('expected_min_rows', question)
                else:
                    self.assertIn('RETURN DISTINCT c.tdocNumber', query)
                    self.assertIn('ORDER BY c.tdocNumber DESC LIMIT 10', query)
                    self.assertEqual(question.get('expected_min_rows'), None if number == 2 else 1)

    def test_submitter_coverage_counts_tdocs_instead_of_submission_edges(self):
        for wg in ('RAN4', 'RAN5'):
            with self.subTest(wg=wg):
                question = self.questions(wg, 1)['CQ5-3']
                query = question['cypher']
                self.assertIn('OPTIONAL MATCH (t)-[:SUBMITTED_BY]->(c:Company)', query)
                self.assertIn('count(DISTINCT t) AS total', query)
                self.assertIn('count(DISTINCT CASE WHEN c IS NOT NULL THEN t END) AS withCompany', query)
                self.assertEqual(question['expected_min_rows'], 1)

    def test_reference_revision_alias_does_not_assert_approval(self):
        for identifier in ('CQ4-2', 'CQ4-5'):
            with self.subTest(identifier=identifier):
                question = self.questions('RAN5', 4)[identifier]
                self.assertIn('다루거나 참조', question['question'])
                self.assertIn('ABOUT_TDOC|REFERENCES', question['cypher'])
                self.assertIn('REVISED_TO*0..', question['cypher'])
                self.assertIn('AS revisionTdocNumber', question['cypher'])
                self.assertNotIn('agreedTdocNumber', question['cypher'])
                self.assertIn('referenced', question['expected'])
                self.assertIn('revision', question['expected'])
                self.assertNotIn('agreed', question['expected'])
                self.assertEqual(question['expected_min_rows'], 1)

    def test_zero_allowed_diagnostic_keeps_its_original_scope(self):
        question = self.questions('RAN5', 2)['CQ2-3']
        self.assertEqual(question['expected_min_rows'], 0)
        self.assertIs(question['allow_zero'], True)
        self.assertIn('현재 KG에 존재한다는 보증과 구분', question['note'])
        self.assertNotIn('닻', question['note'])

    def test_step8_conditions_are_materialized_with_wg_absence_policy(self):
        for wg in ('RAN1', 'RAN2', 'RAN3'):
            with self.subTest(wg=wg):
                questions = self.questions(wg, 3)
                self.assertEqual(questions['P3-S8-CQ02']['equal_columns'], [['linked', 'total']])
                expected = questions['P3-S8-CQ06']
                if wg == 'RAN1':
                    self.assertNotIn('true_columns', expected)
                    self.assertEqual(expected['absent_by_design'], ['label:RRCParameter', 'property:ieName'])
                    self.assertIn('모든 IE가 존재한다는 뜻이 아니라', expected['note'])
                else:
                    self.assertEqual(expected['true_columns'], ['found'])

    def test_step8_actual_consumers_fail_on_any_incomplete_result_row(self):
        import importlib.util
        import io
        import json
        import sys
        import tempfile
        from contextlib import redirect_stdout
        from pathlib import Path
        self.addCleanup(sys.path.__setitem__, slice(None), sys.path.copy())
        sys.path.insert(0, str(self.repository / 'scripts/common'))
        from common import credentials
        for wg in ('RAN1', 'RAN2', 'RAN3'):
            with self.subTest(wg=wg), tempfile.TemporaryDirectory() as temporary:
                path = self.repository / f'scripts/tsg/RAN/formal/{wg}/phase-3/validation/01_validate_cq_cypher.py'
                spec = importlib.util.spec_from_file_location(f'cq_meaning_consumer_{wg}', path)
                consumer = importlib.util.module_from_spec(spec)
                with patch.object(credentials, 'neo4j_password', return_value='synthetic'), \
                        patch.object(credentials, 'neo4j_auth', return_value=('fixture', 'synthetic')):
                    spec.loader.exec_module(consumer)
                questions = self.questions(wg, 3)
                selected = [questions[key] for key in ('P3-S8-CQ02', 'P3-S8-CQ06')]
                temporary = Path(temporary)
                dataset, output = temporary / 'dataset.json', temporary / 'result.json'
                dataset.write_text(json.dumps({'metadata': {'version': 'synthetic'}, 'questions': selected}))
                consumer.CQ_PATH = consumer.DATASET = dataset
                consumer.OUTPUT_PATH = consumer.OUTPUT = output
                mode = {'case': 'normal'}
                closed = []
                class Rows(list):
                    def single(self): return self[0] if self else None
                    def consume(self):
                        notes = ([{'code': f'Neo.ClientNotification.Statement.Unknown{kind}Warning',
                                   'description': f'(the missing property name is: {name})'}
                                  for kind, name in (('Label', 'RRCParameter'), ('PropertyKey', 'ieName'))]
                                 if wg == 'RAN1' and self == ['explain_ie'] else [])
                        return SimpleNamespace(notifications=notes)
                class Session:
                    def __enter__(self): return self
                    def __exit__(self, *args): pass
                    def run(self, query, **parameters):
                        if query.startswith('EXPLAIN'):
                            return Rows(['explain_ie']) if 'ieName: expected' in query else Rows()
                        if query == guard._SPEC_IDENTITY_Q: return Rows()
                        if 'RETURN 1 AS hit' in query: return Rows([{'hit': 1}])
                        if query == selected[0]['cypher']:
                            return Rows([{'class': 'Procedure', 'total': 2,
                                          'linked': 1 if mode['case'] == 'link_missing' else 2,
                                          'link_pct': 100.0}])
                        if query == selected[1]['cypher']:
                            return Rows([{'expected': f'IE-{index}',
                                          'found': wg != 'RAN1' and (mode['case'] != 'ie_missing' or index != 0),
                                          'spec': 'synthetic', 'release': 'Rel-19'} for index in range(6)])
                        raise AssertionError('unexpected query')
                class Driver:
                    def verify_connectivity(self): pass
                    def session(self, **options): return Session()
                    def close(self): closed.append(True)
                with patch.object(consumer.GraphDatabase, 'driver', return_value=Driver()):
                    for case in ('normal', 'link_missing', 'ie_missing', 'normal'):
                        mode['case'] = case
                        with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as result:
                            consumer.main()
                        self.assertEqual(result.exception.code, 1 if case == 'link_missing' or (case == 'ie_missing' and wg != 'RAN1') else 0)
                        results = {r['id']: r for r in json.loads(output.read_text())['results']}
                        failed = 'P3-S8-CQ02' if case == 'link_missing' else 'P3-S8-CQ06'
                        if result.exception.code:
                            self.assertEqual(results[failed]['status'], 'FAIL')
                            self.assertTrue(any(failed in d for d in results[failed]['guard_defects']))
                            samples = results[failed].get('sample_answers', results[failed].get('sample'))
                            self.assertTrue(samples)
                            if case == 'link_missing':
                                self.assertNotEqual(samples[0]['linked'], samples[0]['total'])
                            else:
                                self.assertIs(samples[0]['found'], False)
                    self.assertEqual(len(closed), 4)


class RowConditionTests(unittest.TestCase):
    def test_equal_columns_reject_missing_type_mismatch_and_nonfinite_counts(self):
        contract = {'id': 'LINKS', 'equal_columns': [['linked', 'total']]}
        for value in (0, 2, 2.5):
            self.assertEqual(guard.equal_column_defects(contract, [{'linked': value, 'total': value}]), [])
        self.assertEqual(guard.equal_column_defects({}, None), [])
        self.assertEqual(guard.equal_column_defects(contract, []), [])
        self.assertTrue(guard.equal_column_defects(contract, None))
        for row in ({}, {'linked': 1}, {'linked': None, 'total': None},
                    {'linked': True, 'total': True}, {'linked': '2', 'total': '2'},
                    {'linked': 2, 'total': 2.0}, {'linked': 1, 'total': 2},
                    {'linked': float('nan'), 'total': float('nan')},
                    {'linked': float('inf'), 'total': float('inf')},
                    {'linked': -float('inf'), 'total': -float('inf')}):
            with self.subTest(row=row):
                defects = guard.equal_column_defects(contract, [{'linked': 2, 'total': 2}, row])
                self.assertEqual(len(defects), 1)
                self.assertIn('LINKS', defects[0])
                self.assertIn('[2]', defects[0])
        for invalid in (None, 'linked', [['linked']], [['linked', 'linked']], [['', 'total']], [1]):
            with self.subTest(invalid=invalid):
                self.assertTrue(guard.equal_column_defects({'equal_columns': invalid}, []))

    def test_true_columns_require_true_in_every_row(self):
        contract = {'id': 'IE', 'true_columns': ['found']}
        self.assertEqual(guard.true_column_defects(contract, [{'found': True}, {'found': True}]), [])
        self.assertEqual(guard.true_column_defects({}, None), [])
        self.assertEqual(guard.true_column_defects(contract, []), [])
        self.assertTrue(guard.true_column_defects(contract, None))
        for row in ({}, {'found': None}, {'found': False}, {'found': 1}, {'found': 'true'}):
            with self.subTest(row=row):
                defects = guard.true_column_defects(contract, [{'found': True}, row])
                self.assertEqual(len(defects), 1)
                self.assertIn('IE', defects[0])
                self.assertIn('[2]', defects[0])
        for invalid in (None, 'found', [None], [''], [1]):
            with self.subTest(invalid=invalid):
                self.assertTrue(guard.true_column_defects({'true_columns': invalid}, []))


if __name__ == '__main__':
    unittest.main()
