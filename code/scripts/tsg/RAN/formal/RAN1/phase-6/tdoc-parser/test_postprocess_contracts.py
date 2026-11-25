"""Small, offline checks for TDoc postprocessing outcomes and section labels."""
import ast
import argparse
import contextlib
import io
import os
import json
import re
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
import sys
import time
from datetime import datetime

ROOT = Path(__file__).resolve().parents[7]
WG = os.environ.get("SPECTRA_TEST_WG", "RAN1")
if WG not in {f"RAN{i}" for i in range(1, 6)}:
    raise ValueError("Select RAN1 through RAN5")
HERE = ROOT / "scripts/tsg/RAN/formal" / WG / "phase-6/tdoc-parser"
sys.path.insert(0, str(ROOT / 'scripts/common'))
from common.atomic_io import write_json_atomic
import common.atomic_io as atomic_io
sys.path.insert(0, str(ROOT / 'scripts/tsg/RAN/formal/common'))
import tdoc_selection


def extract(filename, names, env):
    env.setdefault('tdoc_selection', tdoc_selection)
    env.setdefault('WG_FOLDER_PREFIX', {WG: f'TSGR{WG[-1]}_'})
    source = HERE / filename
    tree = ast.parse(source.read_text())
    selected = [node for node in tree.body if getattr(node, 'name', '') in names]
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(source), 'exec'), env)
    return env


class PostprocessContracts(unittest.TestCase):
    def test_both_merge_paths_preserve_both_section_titles(self):
        env = extract('parse_tdoc_lib.py', {'ChunkEngine'}, {'Section': object})
        engine = env['ChunkEngine']()
        plain = extract('07_rechunk_all.py', {'count_tokens', 'merge_small_chunks'},
                        dict(MIN_TOKENS=100, MAX_TOKENS=2000))
        for merge in (engine._merge_small_chunks, plain['merge_small_chunks']):
            for sizes in ((120, 10), (10, 120)):
                with self.subTest(function=merge.__qualname__, sizes=sizes):
                    chunks = [dict(chunkIndex=i + 1, sectionTitle=title,
                                   content='x' * (size * 4), tokenCount=size)
                              for i, (title, size) in enumerate(zip(('Overview', 'Procedure'), sizes))]
                    result = merge(chunks)
                    self.assertEqual(len(result), 1)
                    self.assertEqual(result[0]['sectionTitle'], 'Overview / Procedure')
                    self.assertEqual(result[0]['content'], chunks[0]['content'] + '\n' + chunks[1]['content'])

    def test_missing_equation_source_is_an_error(self):
        env = extract('05_enhance_equations.py', {'enhance_single_tdoc'},
                      dict(get_source_docs=lambda *args: []))
        result = env['enhance_single_tdoc']((Path('unused'), 'RAN1#999', 'R1-999999', Path('unused'), 'RAN1'))
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['reason'], 'no_source_docx')

    def test_rechunk_worker_error_has_failure_exit_status(self):
        with tempfile.TemporaryDirectory() as temp:
            env = dict(argparse=argparse, DEFAULT_WG=WG, WG=WG, MIN_TOKENS=100,
                       MAX_TOKENS=2000, get_parsed_base=lambda wg: Path(temp),
                       collect_tasks=lambda *args, **kwargs: [('synthetic',)],
                       POOL_SLICE=2000, time=time, json=json, datetime=datetime,
                       write_json_atomic=write_json_atomic,
                       LOG_DIR=Path(temp), log=None, rechunk_single_tdoc=None,
                       pool_run=types.SimpleNamespace(run_all=lambda *args: iter([
                           dict(status='error', tdocNumber='R1-999999', reason='invalid_json')])) )
            extract('07_rechunk_all.py', {'main'}, env)
            with patch.object(sys, 'argv', ['rechunk']):
                self.assertEqual(env['main'](), 1)


@unittest.skipUnless(WG == 'RAN1', 'Atomic IO regressions cover the RAN1 parser path')
class AtomicStorageContracts(unittest.TestCase):
    def test_invalid_worker_counts_fail_before_path_or_service_access(self):
        def unexpected(*args):
            self.fail('Invalid workers reached data or service setup')

        for filename in ('03_parse_full_scope.py', '04_enhance_figures.py',
                         '05_enhance_equations.py', '06_update_chunks.py', '07_rechunk_all.py'):
            for workers in (0, -1):
                with self.subTest(filename=filename, workers=workers):
                    env = extract(filename, {'main'}, dict(
                        argparse=argparse, DEFAULT_WG=WG,
                        get_data_base=unexpected, get_parsed_base=unexpected))
                    with patch.object(sys, 'argv', [filename, '--workers', str(workers)]), \
                            contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as result:
                        env['main']()
                    self.assertEqual(result.exception.code, 2)

    def test_rechunk_failure_preserves_source_and_retry_completes(self):
        names = {'count_tokens', 'split_into_sentences', 'merge_small_chunks',
                 'split_oversized_chunks', 'add_chunk_ids', 'rechunk_single_tdoc'}
        env = extract('07_rechunk_all.py', names, dict(
            json=json, re=re, datetime=datetime, MIN_TOKENS=100,
            MAX_TOKENS=2000, write_json_atomic=write_json_atomic))
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            path = folder / 'chunks.json'
            before = json.dumps(dict(metadata={'source': 'synthetic'}, chunks=[
                dict(content='x' * 480, tokenCount=120, sectionTitle='Overview')])).encode()
            for operation in ('fsync', 'replace'):
                for failure in (OSError, KeyboardInterrupt):
                    with self.subTest(operation=operation, failure=failure.__name__):
                        path.write_bytes(before)
                        path.chmod(0o640)
                        with patch.object(atomic_io.os, operation, side_effect=failure('synthetic')), \
                                self.assertRaises(failure):
                            env['rechunk_single_tdoc']((folder, 'RAN1#999', 'R1-999999', False))
                        self.assertEqual(path.read_bytes(), before)
                        self.assertEqual(list(folder.iterdir()), [path])
                        result = env['rechunk_single_tdoc']((folder, 'RAN1#999', 'R1-999999', False))
                        self.assertEqual(result['status'], 'success')
                        self.assertEqual(path.stat().st_mode & 0o777, 0o640)
                        self.assertEqual(json.loads(path.read_bytes())['metadata']['source'], 'synthetic')
                        self.assertEqual(env['rechunk_single_tdoc'](
                            (folder, 'RAN1#999', 'R1-999999', False))['reason'], 'already_v3')

    def test_parser_report_failure_preserves_previous_report(self):
        from collections import Counter

        with tempfile.TemporaryDirectory() as temp:
            env = extract('03_parse_full_scope.py', {'save_report'}, dict(
                LOG_DIR=Path(temp), time=time, Counter=Counter, write_json_atomic=write_json_atomic))
            with patch.object(time, 'strftime', return_value='synthetic'), \
                    contextlib.redirect_stdout(io.StringIO()):
                report = env['save_report']([], [], 0, 'test')
                before = report.read_bytes()
                for operation in ('fsync', 'replace'):
                    for failure in (OSError, KeyboardInterrupt):
                        with self.subTest(operation=operation, failure=failure.__name__):
                            with patch.object(atomic_io.os, operation, side_effect=failure('synthetic')), \
                                    self.assertRaises(failure):
                                env['save_report']([], [], 1, 'test')
                            self.assertEqual(report.read_bytes(), before)
                            self.assertEqual(list(report.parent.iterdir()), [report])
                            env['save_report']([], [], 0, 'test')
                            self.assertEqual(report.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
