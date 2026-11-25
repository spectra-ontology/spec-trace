"""WG 접속 대상을 결정할 때 다른 WG 환경이 섞이는 반례를 검사한다."""
import ast
from contextlib import redirect_stdout
import io
import os
from pathlib import Path
import sys
import re
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import axis, service_endpoints as endpoints

ROOT = Path(__file__).resolve().parents[3]


class ServiceEndpointTests(unittest.TestCase):
    def test_default_and_same_wg_endpoint_follow_registry(self):
        for wg in axis.ALL_PARTITIONS:
            with self.subTest(wg=wg), patch.dict(os.environ, {}, clear=True):
                self.assertEqual(endpoints.neo4j_uri(wg), axis.bolt_uri(wg))
                value = f'neo4j+s://approved.example:{axis.bolt_port(wg)}'
                for name in ('NEO4J_URI', 'NEO4J_BOLT'):
                    with patch.dict(os.environ, {name: value}, clear=True):
                        self.assertEqual(endpoints.neo4j_uri(wg), value)

    def test_foreign_wg_is_rejected_for_environment_and_explicit_argument(self):
        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            foreign = axis.bolt_uri('RAN2' if wg == 'RAN1' else 'RAN1')
            for key in ('NEO4J_URI', 'NEO4J_BOLT'):
                with self.subTest(wg=wg, key=key), patch.dict(os.environ, {key: foreign}, clear=True):
                    with self.assertRaisesRegex(ValueError, '레지스트리'):
                        endpoints.neo4j_uri(wg)
            with patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(ValueError, '레지스트리'):
                endpoints.neo4j_uri(wg, override=foreign)

    def test_explicit_target_takes_precedence_and_errors_keep_secrets_private(self):
        with patch.dict(os.environ, {'NEO4J_URI': axis.bolt_uri('RAN2')}, clear=True):
            self.assertEqual(endpoints.neo4j_uri('RAN1', override=axis.bolt_uri('RAN1')),
                             axis.bolt_uri('RAN1'))
        for value in ('http://localhost:7687', 'bolt://private-user:private-secret@host:7687',
                      'bolt://localhost:bad', 'bolt://localhost:0', 'bolt://localhost:65536',
                      'bolt://localhost:7687#fragment',
                      'bolt://', 'bolt://host name:7687'):
            with self.subTest(value=value), self.assertRaises(ValueError) as caught:
                endpoints.neo4j_uri('RAN1', override=value)
            self.assertNotIn(value, str(caught.exception))
            self.assertNotIn('private-secret', str(caught.exception))

    def test_actual_parser_resolvers_reject_foreign_environment_before_connection(self):
        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            base = ROOT / f'scripts/tsg/RAN/formal/{wg}/phase-6/tdoc-parser'
            source = base / 'parse_tdoc_lib.py'
            cls = next(n for n in ast.parse(source.read_text()).body
                       if isinstance(n, ast.ClassDef) and n.name == 'MetadataResolver')
            method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '__init__')
            env = {'endpoints': endpoints, 'DEFAULT_WG': wg}
            # Only compile the actual constructor; model/parser imports and credentials stay unused.
            exec(compile(ast.Module(body=[method], type_ignores=[]), str(source), 'exec'), env)
            resolver = type('ResolverFixture', (), {'DEFAULT_AUTH': ('fixture', 'fixture'),
                                                    '__init__': env['__init__']})
            helper_source = base / '03_parse_full_scope.py'
            helper = next(n for n in ast.parse(helper_source.read_text()).body
                          if isinstance(n, ast.FunctionDef) and n.name == 'get_neo4j_uri')
            env['WG'] = wg
            exec(compile(ast.Module(body=[helper], type_ignores=[]), str(helper_source), 'exec'), env)
            foreign = axis.bolt_uri('RAN2' if wg == 'RAN1' else 'RAN1')
            with self.subTest(wg=wg), patch.dict(os.environ, {'NEO4J_URI': foreign}, clear=True):
                with self.assertRaisesRegex(ValueError, '레지스트리'):
                    resolver(wg=wg)
                with self.assertRaisesRegex(ValueError, '레지스트리'):
                    env['get_neo4j_uri'](wg)
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(resolver(wg=wg).neo4j_uri, axis.bolt_uri(wg))

    def test_feature_planning_reads_current_registry_instead_of_port_arithmetic(self):
        source = ROOT / 'scripts/capability/feature-planning/planning_common.py'
        node = next(n for n in ast.parse(source.read_text()).body
                    if isinstance(n, ast.FunctionDef) and n.name == 'bolt_uri')
        env = {'re': re, 'axis': axis}
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), 'exec'), env)
        with patch.object(axis, 'bolt_uri', return_value='bolt://registry.example:20000') as lookup:
            self.assertEqual(env['bolt_uri']('RAN4'), 'bolt://registry.example:20000')
            lookup.assert_called_once_with('RAN4')
        for invalid in ('RAN0', 'RAN6', 'RAN4:7687', 'foreign'):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                env['bolt_uri'](invalid)

    def test_ran5_kg_validators_use_registry_and_refuse_foreign_ports_before_connecting(self):
        for phase, name in ((8, 'validate_kg_links'), (9, 'phase_c')):
            source = ROOT / f'scripts/tsg/RAN/formal/RAN5/phase-{phase}/validation/01_validate_search.py'
            tree = ast.parse(source.read_text())
            node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
            config_node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Config')
            default = next(n.value for n in config_node.body
                           if isinstance(n, ast.AnnAssign) and n.target.id == 'neo4j_port')
            namespace = {'axis': axis, 'Config': object,
                         'credentials': SimpleNamespace(neo4j_auth=lambda: ('fixture', 'fixture'))}
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), 'exec'), namespace)
            driver = Mock(side_effect=RuntimeError('fixture connection stop'))
            module = SimpleNamespace(GraphDatabase=SimpleNamespace(driver=driver))
            with self.subTest(phase=phase), \
                    patch.object(axis, 'bolt_port', return_value=20000), \
                    patch.object(axis, 'bolt_uri', return_value='bolt://registry.example:20000') as lookup, \
                    patch.dict(sys.modules, {'neo4j': module}), redirect_stdout(io.StringIO()):
                self.assertEqual(eval(compile(ast.Expression(default), str(source), 'eval'), namespace), 20000)
                for port in (20000, 20001):
                    driver.reset_mock()
                    lookup.reset_mock()
                    config = SimpleNamespace(neo4j_port=port)
                    result = (namespace[name]([], config) if phase == 8 else namespace[name](config, []))
                    if port == 20000:
                        lookup.assert_called_once_with('RAN5')
                        driver.assert_called_once_with('bolt://registry.example:20000', auth=('fixture', 'fixture'))
                    else:
                        lookup.assert_not_called()
                        driver.assert_not_called()
                        self.assertEqual(result[0]['status'], 'SKIP')
                        self.assertIn('레지스트리', result[0]['reason'])


if __name__ == '__main__':
    unittest.main()
