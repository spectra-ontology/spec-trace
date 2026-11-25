#!/usr/bin/env python3
"""RAN5 TS의 비어 있지 않은 절과 저장 실패 시 이전 결과 묶음 보존을 검사합니다."""
import argparse
import ast
from collections import Counter, defaultdict
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[5]
PARSER = ROOT / 'scripts/tsg/RAN/formal/RAN5/phase-3/ts-parser'


def functions(name, env):
    path = PARSER / name
    nodes = [n for n in ast.parse(path.read_text()).body if isinstance(n, ast.FunctionDef)]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), env)
    return env


def parser_module():
    """실제 파서를 읽고 임시 모듈 이름과 import 경로는 호출 전 상태로 복원합니다."""
    source = PARSER / 'parse_ts_docx.py'
    name = 'ran5_small_scope_parser'
    spec = importlib.util.spec_from_file_location(name, source)
    module = importlib.util.module_from_spec(spec)
    absent = object()
    previous = sys.modules.get(name, absent)
    try:
        sys.modules[name] = module
        with mock.patch.object(sys, 'path', [str(source.parent), *sys.path]):
            spec.loader.exec_module(module)
    finally:
        if previous is absent:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
    return module


class SmallScope(unittest.TestCase):
    def test_each_parsed_file_survives_publication_failure(self):
        # 실제 게시 함수를 실행하고, 각 파일을 준비하는 writer에만 오류를 주입합니다.
        # 최종 교체·삭제 중단 뒤의 복원은 actual5WG publication 회귀에서도 검사합니다.
        module = parser_module()
        names = ('ts_38.521-1_Rel-18.json', 'parse_summary_release.json')
        for name in names:
            for boundary in ('serialize', 'fsync_os', 'fsync_interrupt',
                             'replace_os', 'replace_interrupt', 'success'):
                with self.subTest(name=name, boundary=boundary), \
                     tempfile.TemporaryDirectory() as td, contextlib.ExitStack() as stack:
                    root = Path(td)
                    output = root / 'ontology/output/tsg/RAN/formal/parsed_ts/RAN5'
                    output.mkdir(parents=True)
                    old = '{"설명": "기존 결과"}'.encode()
                    for filename in names:
                        (output / filename).write_bytes(old)
                        (output / filename).chmod(0o640)
                    target = output / name
                    result = module.TSParseResult(spec_number='38.521-1', release='Rel-18',
                                                  spec_version='18.0.0', parts=['body.docx'])
                    result.sections = [module.SectionData(section_id='38.521-1-Rel-18-1',
                        section_number='1', section_title='새 결과', level=1)]
                    excluded = []
                    if boundary == 'serialize':
                        if name == names[0]:
                            result.parts = [object()]
                        else:
                            excluded = [('99.999', object())]
                    scope = SimpleNamespace(pairs=[('38.521-1', 'Rel-18', root)], skipped=[],
                                            scope_specs={'38.521-1'}, excluded_specs=excluded)
                    stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                    stack.enter_context(mock.patch.multiple(module, PROJECT_ROOT=root, TS_DIR=root))
                    stack.enter_context(mock.patch.object(module, 'release_scope', return_value=scope))
                    parse = stack.enter_context(mock.patch.object(module, 'parse_spec_release',
                                                                 return_value=result))
                    stack.enter_context(mock.patch.object(sys, 'argv', ['parse']))
                    writer_globals = module.publish_text_set.__globals__
                    writer = writer_globals['write_text_atomic']
                    error = (KeyboardInterrupt('synthetic') if boundary.endswith('interrupt')
                             else OSError('synthetic'))

                    def write(path, *args, **kwargs):
                        guard = (mock.patch.object(os, boundary.split('_')[0], side_effect=error)
                                 if Path(path).name == target.name and boundary.startswith(('fsync', 'replace'))
                                 else contextlib.nullcontext())
                        with guard:
                            return writer(path, *args, **kwargs)

                    stack.enter_context(mock.patch.dict(writer_globals, write_text_atomic=write))
                    if boundary == 'success':
                        module.main()
                        data = json.loads(target.read_bytes())
                        if name == names[0]:
                            self.assertEqual(data['sections'][0]['sectionTitle'], '새 결과')
                            self.assertEqual(data['stats']['sections'], 1)
                        else:
                            self.assertEqual(data['total']['sections'], 1)
                            self.assertEqual(data['total']['spec_releases'], 1)
                        self.assertEqual(target.read_bytes(),
                                         json.dumps(data, ensure_ascii=False, indent=2).encode())
                    else:
                        with self.assertRaises(TypeError if boundary == 'serialize' else type(error)) as got:
                            module.main()
                        if boundary != 'serialize':
                            self.assertIs(got.exception, error)
                        self.assertEqual({filename: (output / filename).read_bytes() for filename in names},
                                         {filename: old for filename in names})
                    parse.assert_called_once()
                    self.assertEqual(target.stat().st_mode & 0o777, 0o640)
                    self.assertEqual({p.name for p in output.iterdir()}, set(names))

    def test_zero_sections_fails_and_one_section_passes(self):
        for count in (0, 1):
            with self.subTest(sections=count), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                output = root / 'ontology/output/tsg/RAN/formal/parsed_ts/RAN5'
                output.mkdir(parents=True)
                data = {'spec_number': '38.521-1', 'release': 'Rel-18', 'specVersion': '18.0.0',
                        'sections': [{'sectionId': '38.521-1-Rel-18-1', 'level': 1}] * count,
                        'tables': [], 'figures': []}
                (output / 'ts_38.521-1_Rel-18.json').write_text(json.dumps(data))
                totals = dict(spec_releases=1, sections=count, tables=0, figures=0,
                              void_sections=0, references=0, references_spec=0)
                summary = {'total': totals, 'per_spec_release': {'38.521-1_Rel-18': {'sections': count}}}
                (output / 'parse_summary_release.json').write_text(json.dumps(summary))
                env = dict(argparse=argparse, json=json, re=re, sys=sys, Counter=Counter,
                           defaultdict=defaultdict, PROJECT_ROOT=root, Path=Path,
                           SID_RE=re.compile(r'^(.+?)-(Rel-\d+)-(.+)$'))
                functions('validate_release_integrity.py', env)
                with mock.patch.object(sys, 'argv', ['validate']), contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(SystemExit) as result:
                        env['main']()
                self.assertEqual(result.exception.code, 0 if count else 1)

    def test_empty_parse_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            output = root / 'ontology/output/tsg/RAN/formal/parsed_ts/RAN5'
            output.mkdir(parents=True)
            previous = output / 'ts_38.521-1_Rel-18.json'
            previous.write_bytes(b'previous generation')
            path = PARSER / 'parse_ts_docx.py'
            node = next(n for n in ast.parse(path.read_text()).body
                        if isinstance(n, ast.FunctionDef) and n.name == 'main')
            env = dict(argparse=argparse, PROJECT_ROOT=root, TS_DIR=root, find_body_parts=None,
                       release_scope=lambda *a: SimpleNamespace(pairs=[('38.521-1', 'Rel-18', root)],
                           skipped=[], scope_specs={'38.521-1'}, excluded_specs=[]),
                       parse_spec_release=lambda *a: SimpleNamespace(spec_number='38.521-1',
                           release='Rel-18', sections=[]))
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), env)
            with mock.patch.object(sys, 'argv', ['parse']), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    env['main']()
            self.assertEqual(previous.read_bytes(), b'previous generation')


if __name__ == '__main__':
    unittest.main()
