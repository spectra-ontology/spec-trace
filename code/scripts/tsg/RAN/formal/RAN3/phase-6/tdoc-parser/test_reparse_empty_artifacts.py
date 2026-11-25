"""Check parser publication and bounded document hashing with synthetic input."""
import ast
from contextlib import contextmanager
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[7] / 'scripts/common'))
from common import credentials

SOURCE = Path(__file__).with_name('parse_tdoc_lib.py')


class DocumentDigest(unittest.TestCase):
    def setUp(self):
        tree = ast.parse(SOURCE.read_text())
        node = next(n for n in tree.body if getattr(n, 'name', '') == '_digest')
        env = dict(Path=Path, hashlib=hashlib)
        exec(compile(ast.Module([node], []), str(SOURCE), 'exec'), env)
        self.digest = env['_digest']

    def test_digest_uses_bounded_reads_and_preserves_hash(self):
        content = b'bounded synthetic document\x00' * 6000
        sizes = []

        class Stream(io.BytesIO):
            def read(self, size=-1):
                if not 0 < size <= 64 * 1024:
                    raise AssertionError('document reads must be bounded')
                sizes.append(size)
                return super().read(size)

        stream = Stream(content)
        source = types.SimpleNamespace(
            open=lambda mode: stream if mode == 'rb' else self.fail('binary read required'),
            read_bytes=lambda: self.fail('whole document read is forbidden'))
        self.assertEqual(self.digest(source), hashlib.sha1(content).hexdigest())
        self.assertTrue(stream.closed)
        self.assertGreater(len(sizes), 2)

    def test_digest_matches_empty_short_and_unicode_files(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'synthetic.bin'
            for content in [b'', b'x', '문서 비교'.encode('utf-8')]:
                with self.subTest(content=content):
                    path.write_bytes(content)
                    self.assertEqual(self.digest(path), hashlib.sha1(content).hexdigest())

    def test_digest_closes_stream_on_read_failure(self):
        class Stream(io.BytesIO):
            def read(self, size=-1):
                raise OSError('synthetic read failure')

        stream = Stream(b'')

        source = types.SimpleNamespace(
            open=lambda mode: stream,
            read_bytes=lambda: self.fail('whole document read is forbidden'))
        with self.assertRaisesRegex(OSError, 'synthetic read failure'):
            self.digest(source)
        self.assertTrue(stream.closed)


class ReparseArtifacts(unittest.TestCase):
    @contextmanager
    def parser(self, wg):
        """Import the actual WG parser; replace only external metadata and tokenization."""
        source = SOURCE.parents[3] / wg / 'phase-6/tdoc-parser/parse_tdoc_lib.py'
        name = f'synthetic_optional_artifacts_{wg.lower()}'
        spec = importlib.util.spec_from_file_location(name, source)
        module = importlib.util.module_from_spec(spec)
        metadata_module = types.ModuleType('tdoc_body_source_metadata')
        metadata_module.project = lambda root, wg, kind, identity, metadata: metadata
        with patch.object(sys, 'path', list(sys.path)), \
                patch.dict(sys.modules, {name: module, 'tdoc_body_source_metadata': metadata_module}), \
                patch.object(credentials, 'neo4j_auth', return_value=('synthetic', 'synthetic')), \
                patch.object(socket.socket, 'connect', side_effect=AssertionError('network is forbidden')), \
                patch('socket.create_connection', side_effect=AssertionError('network is forbidden')):
            spec.loader.exec_module(module)
            with patch.object(module, '_enforce_hard_max', side_effect=lambda chunks, **kw: chunks):
                yield module

    def content(self, parser, wg, revision, *, optional=True):
        number = f'R{wg[-1]}-999999'
        content = parser.ParsedContent(number, 'discussion', paragraph_count=1)
        if optional:
            content.figures = [parser.FigureInfo(
                f'FIG-{number}-001', '1', f'{revision} figure', 'media/image1.png')]
            content.tables = [parser.TableInfo(
                f'TABLE-{number}-001', '1', f'{revision} table',
                f'<table><tr><td>{revision} λ</td></tr></table>', f'{revision} λ',
                equations=[f'EQ-{number}-001'])]
            content.equations = [
                parser.EquationInfo(f'EQ-{number}-001', 1, f'{revision}+x',
                                    f'{revision} context', source='omml', text=f'{revision}+x'),
                parser.EquationInfo(f'EQ-{number}-002', 2, '',
                                    f'{revision} object context', source='ole', text='[EQUATION]'),
            ]
        return content

    def test_new_empty_extraction_replaces_previous_optional_indexes(self):
        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            with self.subTest(wg=wg), self.parser(wg) as parser, tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                content = self.content(parser, wg, 'empty', optional=False)
                meeting = f'{wg}#999'
                out = root / meeting / content.tdoc_number
                for name, payload in [('figures/index.json', {'figures': ['old']}),
                                      ('tables/index.json', {'tables': ['old']}),
                                      ('equations.json', {'equations': ['old'], 'enhanced': True})]:
                    path = out / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(json.dumps(payload), encoding='utf-8')
                parser.OutputGenerator(root).generate(content, [], {}, meeting)
                self.assertEqual(json.loads((out / 'figures/index.json').read_text())['figures'], [])
                self.assertEqual(json.loads((out / 'tables/index.json').read_text())['tables'], [])
                equations = json.loads((out / 'equations.json').read_text())
                self.assertEqual(equations['equations'], [])
                self.assertEqual([equations[key] for key in ('total_count', 'omml_count', 'ole_count')], [0, 0, 0])
                self.assertNotIn('enhanced', equations)
                # A first parse without optional content creates only chunks.json.
                fresh_root = root / 'fresh'
                fresh = parser.OutputGenerator(fresh_root).generate(content, [], {}, meeting)
                self.assertEqual(list(fresh.iterdir()), [fresh / 'chunks.json'])

    def test_nonempty_extraction_preserves_artifact_shapes_and_content(self):
        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            with self.subTest(wg=wg), self.parser(wg) as parser, tempfile.TemporaryDirectory() as temp:
                content = self.content(parser, wg, 'new')
                chunks = [{'content': 'new body λ'}]
                metadata = {'title': 'synthetic title'}
                meeting = f'{wg}#999'
                out = parser.OutputGenerator(Path(temp)).generate(content, chunks, metadata, meeting)
                figures = json.loads((out / 'figures/index.json').read_text())
                self.assertEqual(figures, {'tdocNumber': content.tdoc_number, 'figures': [{
                    'figureId': content.figures[0].figure_id, 'figureNumber': '1',
                    'caption': 'new figure', 'filePath': 'media/image1.png'}]})
                tables = json.loads((out / 'tables/index.json').read_text())
                self.assertEqual(tables['tdocNumber'], content.tdoc_number)
                self.assertEqual(tables['tables'], [{
                    'tableId': content.tables[0].table_id, 'tableNumber': '1', 'caption': 'new table',
                    'filePath': f'html/{content.tables[0].table_id}.html',
                    'equations': [content.equations[0].equationId], 'isAgreementBox': False}])
                self.assertEqual((out / 'tables' / tables['tables'][0]['filePath']).read_text(),
                                 content.tables[0].html)
                equations = json.loads((out / 'equations.json').read_text())
                self.assertEqual(equations['equations'][0]['latex'], 'new+x')
                self.assertEqual(equations['equations'][0]['text'], 'new+x')
                self.assertEqual(equations['equations'][1]['source'], 'ole')
                self.assertEqual([equations[key] for key in ('total_count', 'omml_count', 'ole_count')], [2, 1, 1])
                stored = json.loads((out / 'chunks.json').read_text())
                self.assertEqual(stored['tdocNumber'], content.tdoc_number)
                self.assertEqual(stored['meetingId'], meeting)
                self.assertEqual(stored['chunks'], chunks)
                self.assertEqual(stored['metadata'], metadata)

    def test_failed_file_replacement_preserves_previous_bytes_and_cleans_temporary_file(self):
        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            with self.parser(wg) as parser:
                old = self.content(parser, wg, 'old')
                new = self.content(parser, wg, 'new')
                targets = ('figures/index.json', f'tables/html/{old.tables[0].table_id}.html',
                           'tables/index.json', 'equations.json', 'chunks.json')
                for target in targets:
                    for failure_type in (OSError, KeyboardInterrupt):
                        with self.subTest(wg=wg, target=target, failure=failure_type.__name__), \
                                tempfile.TemporaryDirectory() as temp:
                            generator = parser.OutputGenerator(Path(temp))
                            out = generator.generate(old, [{'content': 'old body'}], {}, f'{wg}#999')
                            failed_path = out / target
                            previous = failed_path.read_bytes()
                            previous_chunks = (out / 'chunks.json').read_bytes()
                            original_replace = os.replace

                            def replace(source, destination):
                                if Path(destination) == failed_path:
                                    raise failure_type('synthetic publication failure')
                                return original_replace(source, destination)

                            with patch('common.atomic_io.os.replace', side_effect=replace):
                                with self.assertRaisesRegex(failure_type, 'synthetic publication failure'):
                                    generator.generate(new, [{'content': 'new body'}], {}, f'{wg}#999')
                            # Publication is atomic per file; previously replaced files may already differ.
                            self.assertEqual(failed_path.read_bytes(), previous)
                            self.assertEqual((out / 'chunks.json').read_bytes(), previous_chunks)
                            self.assertEqual(list(out.rglob('*.tmp')), [])


if __name__ == '__main__':
    unittest.main()
