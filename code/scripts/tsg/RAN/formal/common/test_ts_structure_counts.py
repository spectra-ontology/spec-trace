#!/usr/bin/env python3
"""TS structure commits only when all required source relationships were linked."""
import argparse
import ast
import contextlib
import io
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[5]
WG = os.environ.get('SPECTRA_TEST_WG', 'RAN2')
if WG not in {f'RAN{i}' for i in range(1, 6)}:
    raise ValueError('SPECTRA_TEST_WG must select RAN1 through RAN5')
SOURCE = ROOT / 'scripts/tsg/RAN/formal' / WG / 'phase-3/neo4j/01_load_ts_structure.py'


class RequiredRelationships(unittest.TestCase):
    def test_ran1_verification_failure_closes_driver_and_dryrun_retries(self):
        source = ROOT / 'scripts/tsg/RAN/formal/RAN1/phase-3/neo4j/01_load_ts_structure.py'
        node = next(n for n in ast.parse(source.read_text()).body
                    if isinstance(n, ast.FunctionDef) and n.name == 'main')
        for error in (OSError, KeyboardInterrupt):
            driver = mock.MagicMock()
            driver.verify_connectivity.side_effect = error('verification failure')
            factory = mock.Mock(return_value=driver)
            env = dict(argparse=argparse, sys=sys, NEO4J_URI='synthetic',
                       NEO4J_USER='synthetic', NEO4J_PASSWORD='synthetic',
                       BATCH_SIZE=1, OWNED_REL_TYPES=[], load_jsonld=lambda name: [],
                       reconcile_structure=lambda *args: ({}, {}),
                       GraphDatabase=SimpleNamespace(driver=factory))
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), 'exec'), env)
            with mock.patch.object(sys, 'argv', ['loader', '--dry-run']), \
                 contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit if error is OSError else KeyboardInterrupt) as failure:
                    env['main']()
                if error is OSError: self.assertEqual(failure.exception.code, 1)
                driver.close.assert_called_once_with()
                driver.session.assert_not_called()
                driver.verify_connectivity.side_effect = None
                for _ in range(2):
                    driver.close.reset_mock()
                    env['main']()
                    driver.close.assert_called_once_with()
                for factory_error in (OSError, KeyboardInterrupt):
                    driver.close.reset_mock()
                    factory.side_effect = factory_error('factory failure')
                    with self.assertRaises(SystemExit if factory_error is OSError else KeyboardInterrupt):
                        env['main']()
                    driver.close.assert_not_called()
                    factory.side_effect = None

    def test_missing_parent_never_commits_and_complete_source_commits(self):
        node = next(n for n in ast.parse(SOURCE.read_text()).body
                    if isinstance(n, ast.FunctionDef) and n.name == 'main')
        for missing in ('hub', 'release', 'section', None):
            with self.subTest(missing=missing):
                tx = SimpleNamespace(commit=mock.Mock())
                session = mock.MagicMock()
                session.__enter__.return_value = session
                session.begin_transaction.return_value = tx
                driver = SimpleNamespace(verify_connectivity=lambda: None,
                    session=lambda: session, close=mock.Mock())
                env = dict(argparse=argparse, sys=sys, NEO4J_URI='unused',
                    NEO4J_USER='unused', NEO4J_PASSWORD='unused', BATCH_SIZE=1,
                    GraphDatabase=SimpleNamespace(driver=lambda *a, **kw: driver),
                    Path=Path, time=time,
                    load_all_parsed=lambda: [{'spec_number':'38.331','release':'Rel-19',
                        'sections':[{'sectionId':'38.331-Rel-19-1'}], 'tables':[], 'figures':[]}],
                    stamp_labels=lambda *args, **kwargs: [],
                    load_sections=lambda *args: (1, int(missing != 'section')),
                    load_hierarchy=lambda *args: 0, load_has_section=lambda *args: 1,
                    load_tables=lambda *args: (0, 0), load_figures=lambda *args: (0, 0),
                    load_refs_section=lambda *args: 0, load_refs_spec=lambda *args: 0,
                    OWNED_REL_TYPES=[], parse_spec_ref=lambda ref: ('38.331', 'Rel-19'),
                    create_indexes=lambda db: None,
                    reconcile_structure=lambda *args: ({}, {}),
                    load_jsonld=lambda name: ([{'sectionId': '38.331-Rel-19-1'}] if name == 'sections.jsonld'
                        else [{'@id': 'tdoc:spec/38_331/Rel-19', 'hasSection': ['tdoc:section/38.331-Rel-19-1']}]
                        if name == 'spec_extensions.jsonld' else []),
                    load_release_spec_nodes=lambda *args: (1, int(missing != 'hub'), int(missing != 'release')),
                    load_section_nodes=lambda *args: (1, int(missing != 'section')),
                    load_section_hierarchy=lambda *args: 0,
                    load_table_nodes=lambda *args: (0, 0), load_figure_nodes=lambda *args: (0, 0),
                    load_references=lambda *args: 0, load_references_spec=lambda *args: 0,
                    load_spec_has_section=lambda *args: 1, load_spec_extensions=lambda *args: 1)
                exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), 'exec'), env)
                with mock.patch.object(sys, 'argv', ['loader']), contextlib.redirect_stdout(io.StringIO()):
                    if missing in ("hub", "section"):
                        with self.assertRaises(RuntimeError):
                            env['main']()
                        tx.commit.assert_not_called()
                    else:
                        env['main']()
                        tx.commit.assert_called_once_with()
                driver.close.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
