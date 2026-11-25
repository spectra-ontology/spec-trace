"""동적 보조 컬렉션 이름과 실제 인코더 선언의 연결을 검사한다.

운영 함수의 AST를 실행하며 axis·embedding_registry는 실제 모듈을 사용한다.
원문 추출·Qdrant·모델 로드는 대체하고 작은 임시 JSON만 읽는다.
"""
import argparse
import ast
from collections import Counter
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch

import axis
import embedding_registry as registry

ROOT = next(path for path in Path(__file__).resolve().parents if (path / '.git').exists())
PHASE7 = ROOT / 'scripts/tsg/RAN/formal/common/phase-7'


def production_functions(filename, names, namespace):
    tree = ast.parse((PHASE7 / filename).read_text())
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in functions} != set(names):
        raise AssertionError(f'{filename}: production function missing')
    module = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0),
                              *functions], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), filename, 'exec'), namespace)


def production_literal(filename, name):
    tree = ast.parse((PHASE7 / filename).read_text())
    for node in tree.body:
        target = node.target if isinstance(node, ast.AnnAssign) else (
            node.targets[0] if isinstance(node, ast.Assign) else None)
        if isinstance(target, ast.Name) and target.id == name:
            return ast.literal_eval(node.value)
    raise AssertionError(f'{filename}: {name} declaration missing')


class DynamicEmbeddingConsumerTests(unittest.TestCase):
    def test_all_formal_search_clients_use_the_query_prefix(self):
        adapter = registry.TextPrefixAdapter("text_prefix", "passage: ", "query: ")
        encoder = registry.Encoder("prefix-fixture", "local", "fixture/model", 2, 64, "a" * 40, adapter)
        model = synthetic_prefix_model()
        paths = [ROOT / f'scripts/tsg/RAN/formal/RAN{wg}/phase-{phase}/validation/'
                 f'{"04" if phase == 6 else "01"}_validate_search.py'
                 for wg in range(1, 6) for phase in range(6, 10)]
        paths.append(ROOT / 'scripts/tsg/RAN/formal/TSG_RAN/phase-9/validation/01_validate_search.py')
        client = SimpleNamespace(encoder=encoder, config=SimpleNamespace(encoder=encoder))
        with patch.object(registry, 'load_local_encoder', return_value=model):
            for path in paths:
                with self.subTest(path=str(path.relative_to(ROOT))):
                    namespace = {'embed_local': registry.embed_local}
                    production_query_function(path, 'embed_query', namespace)
                    self.assertEqual(namespace['embed_query'](client, 'mobility'), [1., 0.])
                    self.assertEqual(model.encode.call_args.args[0], ['query: mobility'])
                    self.assertTrue(model.encode.call_args.kwargs['normalize_embeddings'])
        self.assertEqual(model.encode.call_count, len(paths))

    def test_board_probe_query_cache_keeps_encoder_profiles_separate(self):
        encoders = {key: registry.Encoder(key, 'local', 'fixture/model', 2, 64, 'a' * 40,
                    registry.TextPrefixAdapter('text_prefix', 'passage: ', prefix))
                    for key, prefix in [('first', 'query: '), ('second', 'question: ')]}
        model = synthetic_prefix_model()
        namespace = {'embed_local': registry.embed_local,
                     'local_encoder_for': lambda collection: encoders[collection], '_EMBED_CACHE': {}}
        path = ROOT / 'scripts/capability/answer/answer_pipeline/board_semantic_probe.py'
        production_query_function(path, 'embed', namespace)
        with patch.object(registry, 'load_local_encoder', return_value=model):
            for collection in ('first', 'first', 'second'):
                self.assertEqual(namespace['embed']('mobility', collection), [1., 0.])
        self.assertEqual([call.args[0] for call in model.encode.call_args_list],
                         [['query: mobility'], ['question: mobility']])

    def test_ran5_auxiliary_dispatches_to_registered_description_collection(self):
        loader = 'p1_1b_extract_ie_descriptions.py'
        run_step = Mock(return_value=0)
        dispatch = dict(argparse=argparse, re=re,
                        AUX_STEPS=production_literal('run_phase7_auxiliary.py', 'AUX_STEPS'),
                        run_step=run_step)
        production_functions('run_phase7_auxiliary.py', ['main'], dispatch)
        for selected in (None, ['38.523-1', '38.523-3']):
            with self.subTest(selected=selected):
                run_step.reset_mock()
                argv = ['auxiliary', '--wg', 'RAN5', '--apply']
                for spec in selected or []:
                    argv.extend(['--spec', spec])
                with patch.object(sys, 'argv', argv), redirect_stdout(io.StringIO()):
                    self.assertEqual(dispatch['main'](), 0)
                self.assertEqual(run_step.call_args_list, [
                    call('apply_p1_to_wg.py:p12', 'RAN5', True, targets=selected),
                    call(loader, 'RAN5', True),
                ])

        client = Mock()
        sync = Mock(return_value={'points': 2})
        namespace = dict(argparse=argparse, WG_SPECS=production_literal(loader, 'WG_SPECS'),
                         spec_dir=lambda *args: Path('fixture'), find_docx_parts=lambda path: [path / 'fixture.docx'],
                         extract_docx_text_with_tables=lambda path: ('fixture body', []),
                         extract_ie_descriptions=lambda *args: [{'body': 'fixture body'}],
                         count_tokens=lambda text: 3,
                         make_chunks=lambda ies, spec: [{'chunkId': spec + '-fixture', 'text': 'fixture body'}],
                         axis=axis, QdrantClient=Mock(return_value=client), QDRANT_TIMEOUT=120,
                         local_encoder_for=registry.local_encoder_for, sync_collection=sync)
        production_functions(loader, ['main'], namespace)
        with patch.object(registry, 'load_local_encoder') as model, \
                patch.object(sys, 'argv', [loader, '--wg', 'RAN5', '--apply']), redirect_stdout(io.StringIO()):
            namespace['main']()
        expected = registry.encoder_for('ran5_ts_ie_descriptions')
        model.assert_called_once_with(expected)
        self.assertEqual(sync.call_args.args[:3], (client, 'ran5_ts_ie_descriptions', expected))
        self.assertEqual(len(sync.call_args.args[3]), len(namespace['WG_SPECS']['RAN5']))
        client.close.assert_called_once_with()

    def test_ran3_p12_reindex_uses_registered_separate_collection(self):
        client = Mock()
        sync = Mock(return_value={'points': 1})
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec = root / '38.413'
            spec.mkdir()
            chunk = {'chunkId': 'fixture-chunk', 'text': 'fixture body'}
            (spec / 'chunks.json').write_text(json.dumps({'chunks': [chunk]}))
            namespace = dict(json=json, Counter=Counter,
                             axis=SimpleNamespace(tree_path=lambda *args, **kwargs: root,
                                                  qdrant_collection=axis.qdrant_collection),
                             QdrantClient=Mock(return_value=client), QDRANT_TIMEOUT=120,
                             local_encoder_for=registry.local_encoder_for, sync_collection=sync)
            production_functions('apply_p1_to_wg.py', ['reindex_main_collection', '_duplicate_chunk_ids'], namespace)
            with patch.object(registry, 'load_local_encoder') as model, redirect_stdout(io.StringIO()):
                result = namespace['reindex_main_collection']('RAN3', False)
        expected = registry.encoder_for('ran3_ts_sections_p12')
        model.assert_called_once_with(expected)
        sync.assert_called_once_with(client, 'ran3_ts_sections_p12', expected, [chunk], replace_specs=None)
        client.close.assert_called_once_with()
        self.assertEqual(result['points'], 1)


def production_query_function(path, name, namespace):
    """Execute a query method's actual body without importing a model or DB client."""
    matches = [node for node in ast.walk(ast.parse(path.read_text()))
               if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(matches) != 1:
        raise AssertionError(f'{path}: expected one {name} function')
    module = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0),
                              matches[0]], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(path), 'exec'), namespace)


def synthetic_prefix_model():
    def tokenize(texts, **kwargs):
        ids = [[ord(char) for char in text] for text in texts] if isinstance(texts, list) else [
            ord(char) for char in texts]
        return {'input_ids': ids}
    tokenizer = Mock(side_effect=tokenize)
    tokenizer.num_special_tokens_to_add.return_value = 2
    vector = SimpleNamespace(tolist=lambda: [1., 0.])
    return SimpleNamespace(tokenizer=tokenizer, encode=Mock(return_value=[vector]))


if __name__ == '__main__':
    unittest.main()
