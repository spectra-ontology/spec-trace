#!/usr/bin/env python3
"""Offline synthetic regression for residual producer and CQ contracts.

Spec: docs/common/process/spectra_operations_rulebook.md §3.1, §4.1.
Ontology: scoped meeting replacement, clause identities, canonical JSON-LD.
Cycle: synthetic inputs -> production functions -> preserved/validated bytes.
No research logs, model calls, Neo4j connections or repository output writes.
배경: producer failure boundaries must preserve the previous paired artifacts.
사용: python3 -B -m unittest discover -s scripts/tsg/RAN/formal/common -p test_residual_generation_contracts.py.
LLM 호출: none. Synthetic temporary inputs only.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import hashlib
import json
import os
from pathlib import Path
import signal
import struct
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
sys.path.insert(0, str(ROOT / 'scripts/common'))
FORMAL = ROOT / 'scripts/tsg/RAN/formal'


def load(relative):
    """Isolate same-named WG parser dependencies, keeping the actual entrypoint."""
    def local_module(value):
        filename = getattr(value, '__file__', '') or ''
        return any(str(FORMAL / wg) + '/' in filename
                   for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'))
    previous = {name: value for name, value in sys.modules.items() if local_module(value)}
    for name in previous:
        sys.modules.pop(name, None)
    path = FORMAL / relative
    spec = importlib.util.spec_from_file_location('residual_' + relative.replace('/', '_'), path)
    module = importlib.util.module_from_spec(spec)
    source = path
    if os.environ.get('SPECTRA_RESIDUAL_BEFORE_DIR'):
        source = Path(os.environ['SPECTRA_RESIDUAL_BEFORE_DIR']) / path.relative_to(ROOT)
    try:
        sys.modules[spec.name] = module
        # Common dependencies can already be cached from a previous WG import.
        # Supply their actual search paths without relying on import side effects.
        with patch.object(sys, 'path', [str(path.parent), str(FORMAL / 'common'),
                                      str(ROOT / 'scripts/common/common'), *sys.path]):
            exec(compile(source.read_bytes(), str(path), 'exec'), module.__dict__)
    finally:
        for name, value in list(sys.modules.items()):
            if local_module(value):
                sys.modules.pop(name, None)
        sys.modules.update(previous)
    return module


def publication_writer(writer, target, boundary, error):
    """선택한 파일의 실제 writer에 동기화·교체 오류만 주입합니다."""
    def write(path, *args, **kwargs):
        guard = (patch.object(os, boundary.split('_')[0], side_effect=error)
                 if Path(path) == target and boundary.startswith(('fsync', 'replace'))
                 else contextlib.nullcontext())
        with guard:
            return writer(path, *args, **kwargs)
    return write


class ProducerContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))

    def module(self, relative):
        module = load(relative)
        self.stack.enter_context(patch.object(module, 'PROJECT_ROOT', self.root))
        # A concurrently added disposition producer has its own bound root.
        # Keep this suite restricted to the synthetic producer boundary.
        if hasattr(module, 'generate_for_wg'):
            self.stack.enter_context(patch.object(module, 'generate_for_wg', return_value={}))
        return module

    def test_module_loader_uses_requested_parser_and_restores_previous_alias(self):
        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5', 'RAN1'):
            previous = sys.modules.get('report_parser')
            m = self.module(f'{wg}/phase-2/report-parser/01_parse_all.py')
            self.assertTrue(Path(m.ReportParser.parse.__code__.co_filename).is_relative_to(FORMAL / wg))
            self.assertIs(sys.modules.get('report_parser'), previous)

    def test_readonly_cq_replay_preserves_previous_report_on_publication_failure(self):
        from common import atomic_io

        module = load('common/replay_formal_cqs_readonly.py')
        self.stack.enter_context(patch.object(module, 'ROOT', self.root))
        # Empty, bounded datasets isolate publication from CQ domain evaluation.
        # Actual main/audit_wg still open each WG session and read all 25 files.
        for wg in range(1, 6):
            for phase in range(1, 6):
                directory = module.axis.tree_path('logs', wg=f'RAN{wg}', phase=phase, root=self.root)
                directory.mkdir(parents=True)
                (directory / 'cq_test_dataset.json').write_text('{"questions": []}', encoding='utf-8')

        class Connection:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def session(self, **kwargs):
                if kwargs.get('default_access_mode') != module.READ_ACCESS:
                    raise AssertionError('replay must use a read-only session')
                return Connection()

        self.stack.enter_context(patch.object(module.credentials, 'neo4j_auth',
                                             return_value=('fixture', 'fixture')))
        self.stack.enter_context(patch.object(module.GraphDatabase, 'driver',
                                             side_effect=lambda *args, **kwargs: Connection()))
        target = self.root / 'replay.json'
        previous = b'{"operator":"previous replay"}\n'
        expected = json.dumps({f'RAN{wg}': [] for wg in range(1, 6)},
                              ensure_ascii=False, indent=2).encode('utf-8')
        self.stack.enter_context(patch.object(sys, 'argv', [module.__file__, '--out', str(target)]))
        for boundary in ('fsync', 'replace'):
            for error in (OSError, KeyboardInterrupt):
                with self.subTest(boundary=boundary, error=error.__name__):
                    target.write_bytes(previous)
                    target.chmod(0o640)
                    with patch.object(atomic_io.os, boundary, side_effect=error('replay publication')):
                        with self.assertRaisesRegex(error, 'replay publication'):
                            module.main()
                    self.assertEqual(target.read_bytes(), previous)
                    self.assertEqual(target.stat().st_mode & 0o777, 0o640)
                    self.assertEqual(list(target.parent.glob('.replay.json.*.tmp')), [])
                    for _ in range(2):
                        with self.assertRaises(SystemExit) as stopped:
                            module.main()
                        self.assertEqual(stopped.exception.code, 0)
                        self.assertEqual(target.read_bytes(), expected)
                        self.assertEqual(target.stat().st_mode & 0o777, 0o640)
                        self.assertEqual(list(target.parent.glob('.replay.json.*.tmp')), [])

    def test_canonical_failure_preserves_reference_bytes(self):
        for wg in ('RAN4', 'RAN5'):
            with self.subTest(wg=wg):
                m = self.module(f'{wg}/phase-1/jsonld/02_reference_classes.py')
                out = self.root / (wg + '.jsonld'); out.write_bytes(b'preserve reference')
                with patch.object(m, 'canonical_document', side_effect=ValueError('invalid identity')):
                    with self.assertRaises(ValueError):
                        m.save_jsonld({'a': {'@id': 'tdoc:company/a'}}, out, 'Company')
                self.assertEqual(out.read_bytes(), b'preserve reference')

    def test_canonical_failure_preserves_report_bytes(self):
        for wg in ('RAN4', 'RAN5'):
            with self.subTest(wg=wg):
                m = self.module(f'{wg}/phase-2/report-parser/01_parse_all.py')
                out = self.root / (wg + '-report.jsonld'); out.write_bytes(b'preserve report')
                with patch.object(m, 'canonical_document', side_effect=ValueError('invalid identity')):
                    with self.assertRaises(ValueError):
                        m._save_jsonld(out, {}, [])
                self.assertEqual(out.read_bytes(), b'preserve report')

    def test_tdoc_validation_precedes_contact_scoping(self):
        for wg in ('RAN4', 'RAN5'):
            with self.subTest(wg=wg):
                m = self.module(f'{wg}/phase-1/jsonld/03_tdoc_instances.py')
                inputs = self.root / wg / 'input'; inputs.mkdir(parents=True)
                (inputs / 'fixture.xlsx').write_bytes(b'placeholder')
                output = self.root / wg / 'out'; output.mkdir()
                for name in ('tdocs.jsonld', 'contacts.jsonld'):
                    (output / name).write_bytes(b'preserve paired output')
                # Source overlays read the existing reference population before
                # canonical validation. Supply an empty, valid synthetic set.
                for name in ('companies', 'meetings', 'specs', 'releases', 'work_items'):
                    (output / (name + '.jsonld')).write_text(json.dumps({'@graph': []}))
                row = {'@id':'tdoc:R4-0000001', 'tdoc:tdocNumber':'R4-0000001'}
                with patch.multiple(m, INPUT_DIR=inputs, OUTPUT_DIR=output), \
                     patch.object(m, 'load_company_aliases', return_value={}), \
                     patch.object(m, 'process_file', return_value=([row], {'Tdoc':1}, 0)), \
                     patch.object(m, 'canonical_document', side_effect=ValueError('invalid identity')), \
                     patch.object(m, 'scope_contacts') as scope:
                    with self.assertRaises(ValueError): m.main()
                    scope.assert_not_called()
                for name in ('tdocs.jsonld', 'contacts.jsonld'):
                    self.assertEqual((output / name).read_bytes(), b'preserve paired output')

    def test_ts_release_main_preserves_outputs_without_source_slots(self):
        from datetime import datetime
        from types import SimpleNamespace
        from unittest.mock import Mock

        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            m = self.module(f'{wg}/phase-3/ts-parser/parse_ts_docx.py')
            for case in ('empty_source', 'metadata_only', 'excluded_only',
                         'valid', 'all_skipped', 'mixed'):
                with self.subTest(wg=wg, case=case):
                    root = self.root / wg / case
                    source = root / 'TS' / wg / 'source'
                    source.mkdir(parents=True)
                    if case == 'metadata_only':
                        (source / 'metadata').mkdir()
                    elif case == 'excluded_only':
                        (source / '38.211').mkdir()
                    elif case in ('valid', 'all_skipped', 'mixed'):
                        release = source / '38.211' / 'Rel-18'
                        release.mkdir(parents=True)
                        if case != 'all_skipped':
                            (release / 'body.docx').write_bytes(b'synthetic body boundary')
                        if case == 'mixed':
                            (source / '38.212' / 'Rel-18').mkdir(parents=True)
                    output = root / 'ontology/output/tsg/RAN/formal/parsed_ts' / wg
                    output.mkdir(parents=True)
                    previous = output / 'ts_38.211_Rel-18.json'
                    previous.write_bytes(b'previous parsed TS')
                    summary = output / 'parse_summary_release.json'
                    summary.write_bytes(b'previous summary')
                    skipped = output / 'ts_38.212_Rel-18.json'
                    if case == 'mixed':
                        skipped.write_bytes(b'previous skipped TS')
                    inputs = {str(p.relative_to(source)): p.read_bytes()
                              for p in source.rglob('*') if p.is_file()}
                    result = m.TSParseResult(spec_number='38.211', release='Rel-18',
                                            spec_version='18.0.0', parts=['body.docx'])
                    result.sections = [m.SectionData(section_id='38.211-Rel-18-1',
                        section_number='1', section_title='Scope', level=1)]
                    parse = Mock(return_value=result)
                    empty = (case in ('empty_source', 'metadata_only', 'excluded_only')
                             or (wg == 'RAN5' and case == 'all_skipped'))
                    with patch.multiple(m, PROJECT_ROOT=root, TS_DIR=root / 'TS',
                                        datetime=SimpleNamespace(now=lambda: datetime(2026, 1, 1))), \
                         patch.object(m, 'find_body_parts', side_effect=lambda p: sorted(p.glob('*.docx'))), \
                         patch.object(m, 'parse_spec_release', parse), \
                         patch.object(sys, 'argv', [str(m.__file__), '--wg', wg]):
                        if empty:
                            with self.assertRaises(SystemExit) as error:
                                m.main()
                            self.assertNotIn(error.exception.code, (None, 0))
                            self.assertEqual(previous.read_bytes(), b'previous parsed TS')
                            self.assertEqual(summary.read_bytes(), b'previous summary')
                            parse.assert_not_called()
                        else:
                            self.assertIsNone(m.main())
                            report = json.loads(summary.read_text())
                            self.assertEqual(report['total']['spec_releases'], int(case != 'all_skipped'))
                            self.assertEqual(len(report['skipped_spec_releases']),
                                             int(case in ('all_skipped', 'mixed')))
                            if case == 'all_skipped':
                                self.assertFalse(previous.exists())
                                parse.assert_not_called()
                            else:
                                parse.assert_called_once()
                                expected = json.dumps(m.to_output_dict(result), ensure_ascii=False, indent=2)
                                self.assertEqual(previous.read_bytes(), expected.encode())
                            if case == 'mixed':
                                self.assertFalse(skipped.exists())
                    self.assertEqual(inputs, {str(p.relative_to(source)): p.read_bytes()
                                              for p in source.rglob('*') if p.is_file()})

    def test_annex_identity_review_main_preserves_previous_file(self):
        from collections import Counter

        m = load('common/build_annex_identity_reviews.py')
        for boundary in ('serialize', 'fsync_os', 'fsync_interrupt',
                         'replace_os', 'replace_interrupt', 'success',
                         'dry_run', 'no_new'):
            with self.subTest(boundary=boundary), contextlib.ExitStack() as stack:
                root = self.root / boundary
                reports = root / 'ontology/output/tsg/RAN/formal/parsed_reports/RAN1'
                reports.mkdir(parents=True)
                report = reports / 'synthetic-report.json'
                report.write_text('{}')
                target = root / ('ontology/input/tsg/RAN/formal/meetings/RAN1/'
                                 'document_decision_identity_reviews.json')
                target.parent.mkdir(parents=True)
                retained = dict(meetingId='RAN1#100', targetTdocNumber='R1-000001',
                    decisionEvidence={'locator': 'synthetic-old'},
                    identityStatus='same_document_source_verified')
                previous = dict(schema=1, scope='Synthetic retained review', reviews=[retained])
                old = (json.dumps(previous, ensure_ascii=False, indent=1) + '\n').encode()
                target.write_bytes(old)
                target.chmod(0o640)
                added = {**retained, 'targetTdocNumber': 'R1-000002',
                         'decisionEvidence': {'locator': 'synthetic-new'}}
                if boundary == 'serialize':
                    added['synthetic_invalid'] = object()
                stack.enter_context(patch.object(m.d, 'ROOT', root))
                pool_class = stack.enter_context(patch.object(m, 'ProcessPoolExecutor'))
                pool = pool_class.return_value.__enter__.return_value
                pool.map.return_value = [([] if boundary == 'no_new' else [added], Counter())]
                # 원문을 읽는 프로세스 풀의 결과만 합성하고 실제 main과 저장 함수를 실행합니다.
                argv = ['build_annex_identity_reviews.py', '--wg', 'RAN1']
                if boundary == 'dry_run':
                    argv.append('--dry-run')
                stack.enter_context(patch.object(sys, 'argv', argv))
                error = (KeyboardInterrupt('synthetic') if boundary.endswith('interrupt')
                         else OSError('synthetic'))
                writer = publication_writer(m.write_text_atomic, target, boundary, error)
                write = stack.enter_context(patch.object(m, 'write_text_atomic', side_effect=writer))
                if boundary in ('success', 'dry_run', 'no_new'):
                    m.main()
                    if boundary == 'success':
                        expected = {**previous, 'reviews': [retained, added]}
                        self.assertEqual(target.read_bytes(),
                            (json.dumps(expected, ensure_ascii=False, indent=1) + '\n').encode())
                        write.assert_called_once()
                    else:
                        self.assertEqual(target.read_bytes(), old)
                        write.assert_not_called()
                else:
                    with self.assertRaises(TypeError if boundary == 'serialize' else type(error)) as got:
                        m.main()
                    if boundary != 'serialize':
                        self.assertIs(got.exception, error)
                    self.assertEqual(target.read_bytes(), old)
                pool.map.assert_called_once()
                function, arguments = pool.map.call_args.args
                self.assertIs(function, m.reviews_of)
                self.assertEqual(arguments, [(str(report), 'RAN1',
                    {('RAN1#100', 'R1-000001', 'synthetic-old')})])
                self.assertEqual(target.stat().st_mode & 0o777, 0o640)
                self.assertEqual(list(target.parent.iterdir()), [target])

    def test_ran1_ts_jsonld_generation_preserves_complete_set_and_retries(self):
        from common import atomic_io
        from ontology import jsonld_context

        m = self.module('RAN1/phase-3/ts-parser/generate_ts_jsonld.py')
        wg = 'RAN2'  # The public selector controls both source and canonical scope.
        parsed = self.root / 'ontology/output/tsg/RAN/formal/parsed_ts' / wg
        parsed.mkdir(parents=True)
        output = self.root / 'ontology/output/tsg/RAN/formal/instances/phase-3' / wg / 'release-aware'
        output.mkdir(parents=True)
        sid = '38.201-Rel-19-1'
        row = dict(spec_number='38.201', release='Rel-19', specVersion='19.0.0',
                   sections=[dict(sectionId=sid, sectionNumber='1', sectionTitle='Scope',
                                  level=1, isVoid=False, parentSectionId=None, childSectionIds=[])],
                   tables=[dict(tableId=sid + '-T1', tableNumber='1', sectionId=sid)],
                   figures=[dict(figureId=sid + '-F1', figureNumber='1', sectionId=sid)])
        source = parsed / 'ts_38.201_Rel-19.json'
        original = json.dumps(row).encode()
        source.write_bytes(original)
        names = ('sections.jsonld', 'ts_tables.jsonld', 'ts_figures.jsonld', 'spec_extensions.jsonld')

        def seed():
            for name in names:
                (output / name).write_bytes(('previous ' + name).encode())
                (output / name).chmod(0o640)

        def unchanged():
            for name in names:
                self.assertEqual((output / name).read_bytes(), ('previous ' + name).encode())
                self.assertEqual((output / name).stat().st_mode & 0o777, 0o640)
            self.assertEqual(sorted(p.name for p in output.iterdir()), sorted(names))

        def retry():
            for _ in range(2):
                self.assertIsNone(m.main())
                documents = [json.loads((output / name).read_text()) for name in names]
                self.assertEqual([len(d['@graph']) for d in documents], [1, 1, 1, 1])
                self.assertEqual(documents[0]['@graph'][0]['belongsToSpec'], 'tdoc:spec/38_201/Rel-19')
                self.assertEqual(documents[0]['@graph'][0]['containsTable'], ['tdoc:ts_table/' + sid + '-T1'])
                self.assertEqual(documents[0]['@graph'][0]['containsFigure'], ['tdoc:ts_figure/' + sid + '-F1'])
                self.assertEqual(documents[3]['@graph'][0]['specInRelease'], 'tdoc:release/Rel_19')
                self.assertEqual(sorted(p.name for p in output.iterdir()), sorted(names))

        with patch.object(sys, 'argv', ['generate', '--wg', wg]), \
             patch.object(jsonld_context, 'company_reference_aliases', return_value={}) as scope:
            seed()
            invalid = {**row, 'tables': [{}]}
            source.write_text(json.dumps(invalid))
            with self.assertRaises(KeyError): m.main()
            unchanged()
            source.write_bytes(original)
            retry()
            self.assertEqual(scope.call_args.args, (wg,))
            for invalid_at in range(1, 5):
                seed()
                canonical, calls = m.canonical_document, []
                def validate(document, **kwargs):
                    calls.append(document)
                    if len(calls) == invalid_at: raise ValueError('invalid canonical artifact')
                    return canonical(document, **kwargs)
                with patch.object(m, 'canonical_document', side_effect=validate), self.assertRaises(ValueError):
                    m.main()
                unchanged()
                retry()
            replace = atomic_io.os.replace
            for error in (OSError, KeyboardInterrupt):
                for boundary in ('fsync', 'replace'):
                    for fail_at in ((1,) if boundary == 'fsync' else range(1, 5)):
                        for after in ((False,) if boundary == 'fsync' else (False, True)):
                            seed()
                            calls = []
                            def swap(src, dst):
                                canonical_output = Path(dst).parent == output
                                if canonical_output: calls.append(dst)
                                fail = canonical_output and len(calls) == fail_at
                                if fail and not after: raise error('install failure')
                                result = replace(src, dst)
                                if fail and after: raise error('interrupted after install')
                                return result
                            effect = swap if boundary == 'replace' else error('sync failure')
                            with self.subTest(error=error.__name__, boundary=boundary, fail_at=fail_at, after=after), \
                                 patch.object(atomic_io.os, boundary, side_effect=effect), self.assertRaises(error):
                                m.main()
                            unchanged()
                            retry()
            source.unlink()
            seed()
            with self.assertRaises(SystemExit): m.main()
            unchanged()
            source.write_bytes(original)
            retry()
            with patch.object(sys, 'argv', ['generate', '--wg', '../outside']), self.assertRaises(SystemExit):
                m.main()
        self.assertEqual(source.read_bytes(), original)

    def test_all_wgs_ts_docx_publish_results_summary_and_skips_together(self):
        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            with self.subTest(wg=wg):
                self._assert_ts_publication_boundary(wg)

    def _assert_ts_publication_boundary(self, wg):
        from common import atomic_io
        from docx import Document
        from docx.enum.style import WD_STYLE_TYPE

        m = self.module(f'{wg}/phase-3/ts-parser/parse_ts_docx.py')
        ts = self.root / 'TS'
        source = ts / wg / 'source/38.201/Rel-19'
        source.mkdir(parents=True)
        (ts / wg / 'source/38.202/Rel-19').mkdir(parents=True)
        document = Document()
        for name in ('TH', 'TF'): document.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        document.add_heading('1 Scope', 1)
        document.add_paragraph('See clause 1.1.')
        document.add_heading('1.1 Details', 2)
        document.add_paragraph('Table 1.1-1: A table', 'TH')
        document.add_table(rows=1, cols=1).cell(0, 0).text = 'Table body'
        document.add_paragraph('Figure 1.1-1: A figure', 'TF')
        docx = source / 'body.docx'
        document.save(docx)
        original = docx.read_bytes()
        output = self.root / 'ontology/output/tsg/RAN/formal/parsed_ts' / wg
        output.mkdir(parents=True)
        names = ('ts_38.201_Rel-19.json', 'ts_38.202_Rel-19.json', 'parse_summary_release.json')

        def seed():
            for name in names:
                (output / name).write_bytes(('previous ' + name).encode())
                (output / name).chmod(0o640)

        def unchanged():
            for name in names:
                self.assertEqual((output / name).read_bytes(), ('previous ' + name).encode())
                self.assertEqual((output / name).stat().st_mode & 0o777, 0o640)
            self.assertEqual(sorted(p.name for p in output.iterdir()), sorted(names))

        def retry():
            for _ in range(2):
                self.assertIsNone(m.main())
                parsed = json.loads((output / names[0]).read_text())
                self.assertEqual(parsed['stats']['sections'], 2)
                self.assertEqual(parsed['sections'][0]['references'], ['38.201-Rel-19-1.1'])
                self.assertEqual(parsed['sections'][1]['parentSectionId'], '38.201-Rel-19-1')
                self.assertEqual(parsed['tables'][0]['sectionId'], '38.201-Rel-19-1.1')
                self.assertEqual(parsed['figures'][0]['sectionId'], '38.201-Rel-19-1.1')
                self.assertFalse((output / names[1]).exists())
                self.assertEqual(json.loads((output / names[2]).read_text())['total']['spec_releases'], 1)
                self.assertEqual(sorted(p.name for p in output.iterdir()), sorted((names[0], names[2])))

        with patch.object(m, 'TS_DIR', ts), patch.object(sys, 'argv', ['parser']):
            dumps = json.dumps
            def serialize(value, *args, **kwargs):
                if isinstance(value, dict) and 'per_spec_release' in value:
                    raise TypeError('synthetic summary serialization failure')
                return dumps(value, *args, **kwargs)
            for stage in ('result', 'summary'):
                seed()
                guard = (patch.object(m, 'to_output_dict', return_value={'invalid': {object()}})
                         if stage == 'result' else patch.object(m.json, 'dumps', side_effect=serialize))
                with self.subTest(stage=stage), guard, self.assertRaises(TypeError):
                    m.main()
                unchanged()
                retry()
            replace, unlink = atomic_io.os.replace, Path.unlink
            for error in (OSError, KeyboardInterrupt):
                for boundary in ('fsync', 'replace', 'unlink'):
                    targets = (1, 2) if boundary == 'replace' else (1,)
                    for fail_at in targets:
                        for after in ((False,) if boundary == 'fsync' else (False, True)):
                            seed()
                            calls = []
                            def swap(src, dst):
                                target = Path(dst).parent == output
                                if target: calls.append(dst)
                                fail = target and len(calls) == fail_at
                                if fail and not after: raise error('install failure')
                                result = replace(src, dst)
                                if fail and after: raise error('interrupted after install')
                                return result
                            def remove(path, *args, **kwargs):
                                target = path == output / names[1] and not calls
                                if target: calls.append(path)
                                if target and not after: raise error('deletion failure')
                                result = unlink(path, *args, **kwargs)
                                if target and after: raise error('interrupted after deletion')
                                return result
                            owner = Path if boundary == 'unlink' else atomic_io.os
                            effect = swap if boundary == 'replace' else remove if boundary == 'unlink' else error('sync failure')
                            with self.subTest(error=error.__name__, boundary=boundary, fail_at=fail_at, after=after), \
                                 patch.object(owner, boundary, side_effect=effect, autospec=boundary == 'unlink'), \
                                 self.assertRaises(error):
                                m.main()
                            unchanged()
                            retry()
        self.assertEqual(docx.read_bytes(), original)

    def test_tdoc_main_requires_instances_before_replacing_paired_outputs(self):
        import ast
        import shutil
        from types import SimpleNamespace
        from unittest.mock import Mock
        from common.atomic_io import publish_text_set

        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            source = FORMAL / wg / 'phase-1/jsonld/03_tdoc_instances.py'
            main = next(node for node in ast.parse(source.read_bytes()).body
                        if isinstance(node, ast.FunctionDef) and node.name == 'main')
            for case in ('no_files', 'empty', 'valid', 'mixed'):
                with self.subTest(wg=wg, case=case):
                    root = self.root / wg / case
                    inputs = root / 'input'; inputs.mkdir(parents=True)
                    names = [] if case == 'no_files' else (
                        ['empty.xlsx', 'valid.xlsx'] if case == 'mixed' else [case + '.xlsx'])
                    for name in names: (inputs / name).write_bytes(b'synthetic placeholder')
                    output = root / 'out'; output.mkdir()
                    for name in ('tdocs.jsonld', 'contacts.jsonld', 'duplicate_input_merge.txt'):
                        (output / name).write_bytes(b'previous complete artifact')
                    row = {'@id': 'tdoc:synthetic', 'tdoc:tdocNumber': 'synthetic'}

                    def process(path, *args):
                        rows = [row] if path.stem == 'valid' else []
                        result = (rows, {'Tdoc': len(rows), 'CR': 0, 'LS': 0})
                        return result if wg == 'RAN1' else (*result, 0)

                    scope = Mock()
                    namespace = dict(INPUT_DIR=inputs, OUTPUT_DIR=output, PROJECT_ROOT=self.root,
                                     load_company_aliases=Mock(return_value={}),
                                     process_file=Mock(side_effect=process), CONTEXT={}, json=json,
                                     canonical_document=lambda document, **kwargs: document,
                                     tempfile=tempfile, shutil=shutil, Path=Path,
                                     publish_text_set=publish_text_set,
                                     scope_contacts=scope, CONTACT_SCOPE_REPORT='scope.txt',
                                     drop_placeholder_references=Mock(),
                                     write_text_atomic=lambda path, text: path.write_text(text),
                                     supplement_instances=Mock(return_value=[]),
                                     reference_graphs=Mock(return_value={'meetings': []}),
                                     extract_meeting_from_filename=Mock(return_value=wg + '#100'))
                    for name in ('_CLASS_SHIFT', '_MERGE_FILLED'): namespace[name] = {}
                    for name in ('_SEEN_TDOCS', '_MERGE_ROW', '_MERGE_MEETING', '_MERGE_SCHEMA',
                                 '_MERGE_INSTANCE', '_MERGE_CLASS'): namespace[name] = {}
                    for name in ('_MERGE_PROMOTED', '_FIELD_CONFLICTS', '_DATE_TEXT_KEPT',
                                 '_IDENTITY_COLLISIONS', '_CROSS_MEETING_DUPS', '_UNREBUILT',
                                 'DATE_SWAP_NOTES', 'SKIPPED_NON_TDOC_FILES'): namespace[name] = []
                    modules = {
                        'tdoc_revision_evidence': SimpleNamespace(
                            EVIDENCE_FILE='revision_evidence.jsonld',
                            qualify_revisions=Mock(return_value=[]), write_evidence=Mock()),
                        'tdoc_source_identity_corrections': SimpleNamespace(overlay_identity_corrections=Mock(return_value=[])),
                        'tdoc_source_classification': SimpleNamespace(apply_source_classifications=Mock()),
                        'tdoc_source_supplements': SimpleNamespace(reference_graphs=namespace['reference_graphs'])}
                    exec(compile(ast.Module(body=[main], type_ignores=[]), str(source), 'exec'), namespace)
                    with patch.dict(sys.modules, modules):
                        if case in ('no_files', 'empty'):
                            with self.assertRaises(SystemExit): namespace['main']()
                            scope.assert_not_called()
                            for name in ('tdocs.jsonld', 'contacts.jsonld', 'duplicate_input_merge.txt'):
                                self.assertEqual((output / name).read_bytes(), b'previous complete artifact')
                        else:
                            self.assertIsNone(namespace['main']())
                            scope.assert_called_once()
                            self.assertEqual(json.loads((output / 'tdocs.jsonld').read_text())['@graph'], [row])
                            self.assertEqual((output / 'contacts.jsonld').read_bytes(), b'previous complete artifact')

    def test_cr_cover_preserves_all_four_wg_slot_identity_and_atomic_output(self):
        from docx import Document
        from common import atomic_io
        for number in range(1, 5):
            wg, foreign_wg = f'RAN{number}', f'RAN{number + 1}'
            with self.subTest(wg=wg):
                m = self.module(f'{wg}/phase-4/cr-parser/01_parse_cover_sheets.py')
                root = self.root / wg
                slots = {name: root / name for name in (wg, foreign_wg)}
                output = root / 'output'
                output.mkdir(parents=True)
                target = output / 'cover_sheets.json'
                target.write_bytes(b'previous complete')
                target.chmod(0o640)
                tdoc = f'R{number}-' + ('000001' if wg == 'RAN3' else '0000001')
                originals = {}
                for slot, pack in ((wg, 'RP-000001'), (foreign_wg, 'RP-000002')):
                    folder = slots[slot] / 'Rel-19/TSG' / pack / 'contents'
                    folder.mkdir(parents=True)
                    source = folder / (pack + '_cover.docx')
                    doc = Document()
                    doc.add_paragraph('3GPP TSG-RAN Meeting #101')
                    table = doc.add_table(rows=2, cols=13)
                    headers = ['TS', 'CR', 'Rev', 'Rel', 'Title', 'Cat', 'Vsn', '@ Mtg',
                               'TD#', 'Source to WG', 'Work Item', 'Clauses affected', 'Other Aff Specs']
                    values = ['38.201', '0001', '1', 'Rel-19', 'Fixture', 'F', '19.0.0',
                              f'{wg}#101', tdoc, 'Fixture', 'WI', '1', '']
                    for cells, row in ((table.rows[0].cells, headers), (table.rows[1].cells, values)):
                        for cell, value in zip(cells, row):
                            cell.text = value
                    doc.save(source)
                    originals[source] = source.read_bytes()
                foreign = slots[foreign_wg] / 'Rel-19/TSG/RP-000002'
                with patch.multiple(m, INPUT_DIR=slots[wg], OUTPUT_DIR=output), \
                        patch.object(m, 'configure_logging'), \
                        patch.object(m.cr_inputs, 'derived_dir', side_effect=lambda name:
                                     slots.get(name, root / name)), \
                        patch.object(m.cr_other_wg, 'foreign_packs', return_value=[(foreign, 'Rel-19')]), \
                        patch.object(m.pool_run, 'run_all', side_effect=lambda fn, args, *rest:
                                     [fn(*item) for item in args]):
                    def verify():
                        self.assertEqual(m.main(), 0)
                        data = json.loads(target.read_text())
                        self.assertEqual({row['cr_pack_id'] for row in data['crpacks']},
                                         {'RP-000001', 'RP-000002'})
                        self.assertEqual(data['metadata']['total_cr_entries'], 2)
                        self.assertTrue(all(row['tsg_meeting'] == 'RAN#101' for row in data['crpacks']))
                        self.assertTrue(all(row['cr_entries'][0]['tdoc_number'] == tdoc
                                            for row in data['crpacks']))
                        text = json.dumps(data, ensure_ascii=False, indent=2)
                        self.assertEqual(target.read_bytes(), (text + ('\n' if wg == 'RAN1' else '')).encode())
                        self.assertEqual(target.stat().st_mode & 0o777, 0o640)
                        return data
                    self.assertEqual(verify(), verify())
                    for boundary in ('serialize', 'fsync', 'replace'):
                        for error in ((TypeError,) if boundary == 'serialize' else (OSError, KeyboardInterrupt)):
                            with self.subTest(boundary=boundary, error=error):
                                previous = target.read_bytes()
                                encode = json.dumps

                                def serialize(value, *args, **kwargs):
                                    if isinstance(value, dict) and 'crpacks' in value:
                                        value = {**value, 'synthetic_invalid': object()}
                                    return encode(value, *args, **kwargs)

                                fault = (patch.object(atomic_io.json, 'dumps', side_effect=serialize)
                                         if boundary == 'serialize' else
                                         patch.object(atomic_io.os, boundary, side_effect=error('publication')))
                                with fault, self.assertRaises(error):
                                    m.main()
                                self.assertEqual(target.read_bytes(), previous)
                                self.assertEqual(target.stat().st_mode & 0o777, 0o640)
                                self.assertEqual(sorted(p.name for p in output.iterdir()), ['cover_sheets.json'])
                                self.assertEqual(verify(), verify())
                    previous = target.read_bytes()
                    with patch.object(m, 'pack_dirs', return_value=[]):
                        self.assertEqual(m.main(), 1)
                    self.assertEqual(target.read_bytes(), previous)
                for source, before in originals.items():
                    self.assertEqual(source.read_bytes(), before)

    def test_cr_document_main_requires_final_records_before_replacing_outputs(self):
        import ast
        from collections import defaultdict
        from types import SimpleNamespace
        from unittest.mock import Mock
        from common import atomic_io

        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            filename = '01_parse_cr_documents.py' if wg == 'RAN5' else '02_parse_cr_documents.py'
            source = FORMAL / wg / 'phase-4/cr-parser' / filename
            main = next(n for n in ast.parse(source.read_bytes()).body
                        if isinstance(n, ast.FunctionDef) and n.name == 'main')
            scenarios = ('empty_input', 'empty_parse', 'no_form', 'no_identity',
                         'valid', 'mixed', 'errors', 'known_unopenable')
            if wg != 'RAN1':
                scenarios += ('source_only',)
            for scenario in scenarios:
                with self.subTest(wg=wg, scenario=scenario):
                    output = self.root / wg / scenario
                    output.mkdir(parents=True)
                    previous = {name: ('previous ' + name).encode() for name in
                                ('cr_documents.json', 'crpacks.json', 'parse_summary.json')}
                    for name, data in previous.items():
                        (output / name).write_bytes(data)
                        (output / name).chmod(0o640)
                    record = SimpleNamespace(tdoc_number='fixture', source_path='fixture.docx',
                        reason_for_change='reason', summary_of_change='summary',
                        consequences_if_not_approved='', clauses_affected=['1'],
                        affects_core_spec=False, affects_test_spec=False, affects_om_spec=False,
                        errors=['unreadable'] if scenario in ('errors', 'known_unopenable') else [],
                        rejected_spec_refs=[], release='Rel-18')
                    unidentified = SimpleNamespace(**{**vars(record), 'tdoc_number': None})
                    rows = [] if scenario in ('empty_input', 'empty_parse', 'source_only') else [record]
                    if scenario == 'no_identity':
                        rows = [unidentified]
                    elif scenario == 'mixed':
                        rows.append(unidentified)
                    def project(parser, records):
                        if scenario == 'source_only':
                            records.append(record)
                        return {'sourceClassifications': []}
                    noop = Mock()
                    ns = dict(__name__=__name__, __file__=str(source), Path=Path, sys=sys,
                        json=json, write_json_atomic=atomic_io.write_json_atomic,
                        write_text_atomic=atomic_io.write_text_atomic,
                        publish_text_set=atomic_io.publish_text_set,
                        defaultdict=defaultdict, PROJECT_ROOT=self.root, WG=wg,
                        OUTPUT_DIR=output, INPUT_DIR=self.root, log=Mock(),
                        configure_logging=noop, setup_output_and_logging=noop,
                        collect_cr_documents=lambda: [] if scenario == 'empty_input' else ['input'],
                        cr_other_wg=SimpleNamespace(collect=lambda wg: ([], [], {})),
                        pool_run=SimpleNamespace(run_all=lambda *args: rows), parse_cr_document=noop,
                        cr_attachments=SimpleNamespace(METADATA_KEY='attachments', NO_FORM_KEY='no_form',
                            split=lambda records, *args: (records, {}),
                            split_no_form=lambda records: ([], {'fixture.docx': 'fixture'})
                                if scenario == 'no_form' else (records, {})),
                        tsg_cr_decision=SimpleNamespace(split_tsg_cr=lambda records: (records, []),
                            reconcile_cover_numbers=lambda *args: {}, correct_identity=lambda records: ({}, 0, {})),
                        _TDOC_RE=None, _norm_tdoc=noop, cover_number=noop,
                        deduplicate_by_tdoc=lambda records, *args: [r for r in records if r.tdoc_number],
                        cr_unopenable=SimpleNamespace(load=lambda path: [], list_path=lambda path: path,
                            split=lambda records, *args: ([], records, [], [])
                                if scenario == 'known_unopenable' else
                                ([r for r in records if r.errors], [], [], [])),
                        tsg_direct_list=lambda *args: [], duplicate_paths=lambda *args: {},
                        docx_text=SimpleNamespace(strict_opened=lambda: []),
                        cr_record=lambda r: {'tdoc_number': r.tdoc_number},
                        BATCH_SIZE=10, MAX_WORKERS=1, RESUME_FILE=output / 'resume.json',
                        input_fingerprint=lambda docs: 'fingerprint', cleanup_partial_files=noop,
                        save_partial_results=noop, save_resume_state=noop, cover_listed=lambda rows: {},
                        correct_revision=noop, build_crpacks=lambda records: ([],
                            dict(with_cover=0, no_cover=[], unreadable=[], conflict=[])))
                    exec(compile(ast.Module(body=[main], type_ignores=[]), str(source), 'exec'), ns)
                    def run_main():
                        # Source supplement I/O stays synthetic for the first
                        # call, the injected failure and every successful retry.
                        with patch.dict(sys.modules, {
                                'tdoc_source_metadata': SimpleNamespace(phase4_sources=project)}):
                            return ns['main']()
                    result = run_main()
                    if scenario in ('empty_input', 'empty_parse', 'no_form', 'no_identity'):
                        self.assertEqual(result, 1)
                        for name, data in previous.items():
                            self.assertEqual((output / name).read_bytes(), data)
                    else:
                        self.assertEqual(result, 1 if scenario == 'errors' else 0)
                        key = 'cr_documents' if wg == 'RAN1' else 'documents'
                        self.assertEqual(json.loads((output / 'cr_documents.json').read_text())[key],
                                         [{'tdoc_number': 'fixture'}])
                        if scenario == 'valid':
                            for boundary in ('serialize', 'fsync', 'replace'):
                                for error in ((TypeError,) if boundary == 'serialize'
                                              else (OSError, KeyboardInterrupt)):
                                    previous = {name: (output / name).read_bytes() for name in previous}
                                    fault = (patch.dict(ns, cr_record=lambda row: {'tdoc_number': object()})
                                             if boundary == 'serialize' else
                                             patch.object(atomic_io.os, boundary, side_effect=error('publication')))
                                    with fault, self.assertRaises(error):
                                        run_main()
                                    self.assertEqual({name: (output / name).read_bytes() for name in previous}, previous)
                                    for name in previous:
                                        self.assertEqual((output / name).stat().st_mode & 0o777, 0o640)
                                    self.assertEqual(sorted(p.name for p in output.iterdir()), sorted(previous))
                                    for _ in range(2):
                                        self.assertEqual(run_main(), 0)
                                        self.assertEqual(json.loads((output / 'cr_documents.json').read_text())[key],
                                                         [{'tdoc_number': 'fixture'}])

    def test_ran5_cr_main_preserves_final_generation_on_publication_failure(self):
        from types import SimpleNamespace
        from common import atomic_io

        m = self.module('RAN5/phase-4/cr-parser/01_parse_cr_documents.py')
        names = ('cr_documents.json', 'crpacks.json', 'parse_summary.json')
        for name in names:
            for boundary in ('serialize', 'fsync_os', 'fsync_interrupt',
                             'replace_os', 'replace_interrupt', 'publish_os',
                             'publish_interrupt', 'publish_after_os',
                             'publish_after_interrupt', 'aggregate', 'success'):
                with self.subTest(name=name, boundary=boundary), contextlib.ExitStack() as stack:
                    root = self.root / name / boundary
                    output, logs = root / 'output', root / 'logs'
                    output.mkdir(parents=True)
                    logs.mkdir()
                    inputs = root / 'input'
                    inputs.mkdir()
                    source = inputs / 'R5-000001.docx'
                    source.write_bytes(b'synthetic DOCX input boundary')
                    old = '{"설명": "기존 결과"}'.encode()
                    for filename in names:
                        (output / filename).write_bytes(old)
                        (output / filename).chmod(0o640)
                    target = output / name
                    row = m.CRDocumentData(tdoc_number='R5-000001', cr_pack_id='RP-000001',
                        release='Rel-18', spec_number='38.999', title='새 결과',
                        source_path='input/R5-000001.docx')
                    stack.enter_context(patch.multiple(m, PROJECT_ROOT=root, OUTPUT_DIR=output,
                        LOG_DIR=logs, INPUT_DIR=inputs, RESUME_FILE=logs / 'resume.json'))
                    stack.enter_context(patch.object(m, 'setup_output_and_logging'))
                    stack.enter_context(patch.object(m, 'collect_cr_documents',
                                                    return_value=[(source, 'Rel-18')]))
                    stack.enter_context(patch.object(m.cr_other_wg, 'collect', return_value=([], [], {})))
                    parse = stack.enter_context(patch.object(m.pool_run, 'run_all', return_value=[row]))
                    stack.enter_context(patch.object(m, 'input_fingerprint', return_value='synthetic'))
                    stack.enter_context(patch.object(m, 'collect_pack_covers', return_value={}))
                    stack.enter_context(patch.object(m.tsg_cr_decision, '_lists',
                                                    return_value=({}, frozenset(), {}, {})))
                    stack.enter_context(patch.object(m.cr_unopenable, 'load', return_value={}))
                    # 추가 입력 목록을 읽는 경계만 대체하고 분류·집계·저장 함수는 실행합니다.
                    stack.enter_context(patch.dict(sys.modules, {
                        m.__name__: m,
                        'tdoc_source_metadata': SimpleNamespace(phase4_sources=lambda *a: {}),
                    }))
                    encode = json.dumps
                    failure_enabled = [True]

                    def serialize(value, *args, **kwargs):
                        matches = (isinstance(value, dict) and
                            (('documents' in value if name == names[0] else
                              'packs' in value if name == names[1] else
                              value.get('script') == '01_parse_cr_documents.py')))
                        if failure_enabled[0] and boundary == 'serialize' and matches:
                            value = {**value, 'synthetic_invalid': object()}
                        return encode(value, *args, **kwargs)

                    stack.enter_context(patch.object(m.json, 'dumps', side_effect=serialize))
                    error = (KeyboardInterrupt('synthetic') if boundary.endswith('interrupt')
                             else OSError('synthetic'))
                    writer_globals = m.publish_text_set.__globals__
                    atomic_writer = writer_globals['write_text_atomic']

                    def write(path, *args, **kwargs):
                        # 묶음의 준비 파일을 쓰는 실제 writer에만 I/O 오류를 줍니다.
                        selected = Path(path).name == name
                        guard = (patch.object(os, boundary.split('_')[0], side_effect=error)
                                 if failure_enabled[0] and selected and boundary.startswith(('fsync', 'replace'))
                                 else contextlib.nullcontext())
                        with guard:
                            return atomic_writer(path, *args, **kwargs)

                    stack.enter_context(patch.dict(writer_globals, write_text_atomic=write))
                    replace = atomic_io.os.replace
                    injected = [False]

                    def publish_replace(source_path, destination):
                        fail = (failure_enabled[0] and boundary.startswith('publish')
                                and Path(destination) == target and not injected[0])
                        if fail:
                            injected[0] = True
                            if 'after' not in boundary:
                                raise error
                        result = replace(source_path, destination)
                        if fail:
                            raise error
                        return result

                    stack.enter_context(patch.object(atomic_io.os, 'replace', side_effect=publish_replace))
                    aggregate = m.build_crpacks

                    def build_crpacks(rows):
                        result = aggregate(rows)
                        if failure_enabled[0] and boundary == 'aggregate':
                            raise error
                        return result

                    stack.enter_context(patch.object(m, 'build_crpacks', side_effect=build_crpacks))
                    if boundary == 'success':
                        self.assertEqual(m.main(), 0)
                        data = json.loads(target.read_bytes())
                        if name == names[0]:
                            self.assertEqual(data['documents'][0]['title'], '새 결과')
                        elif name == names[1]:
                            self.assertEqual(data['packs'][0]['tdocNumbers'], ['R5-000001'])
                        else:
                            self.assertEqual(data['unique_crs'], 1)
                        self.assertEqual(target.read_bytes(),
                                         encode(data, ensure_ascii=False, indent=2).encode())
                        self.assertEqual({p.name for p in output.iterdir()}, set(names))
                        self.assertFalse(m.RESUME_FILE.exists())
                    else:
                        with self.assertRaises(TypeError if boundary == 'serialize' else type(error)) as got:
                            m.main()
                        if boundary != 'serialize':
                            self.assertIs(got.exception, error)
                        for filename in names:
                            self.assertEqual((output / filename).read_bytes(), old)
                            self.assertEqual((output / filename).stat().st_mode & 0o777, 0o640)
                        # 최종 게시가 실패해도 이미 저장한 재개 입력은 다음 실행에 사용합니다.
                        self.assertEqual(json.loads(m.RESUME_FILE.read_bytes())['batch_idx'], 0)
                        self.assertEqual(len(json.loads((output / 'cr_documents_batch_000.json').read_bytes())), 1)
                        self.assertEqual({p.name for p in output.iterdir()},
                                         {*names, 'cr_documents_batch_000.json'})
                        failure_enabled[0] = False
                        for _ in range(2):
                            self.assertEqual(m.main(), 0)
                            self.assertEqual(json.loads((output / names[0]).read_bytes())['documents'][0]['title'], '새 결과')
                            self.assertEqual(json.loads((output / names[1]).read_bytes())['packs'][0]['tdocNumbers'], ['R5-000001'])
                            self.assertEqual(json.loads((output / names[2]).read_bytes())['unique_crs'], 1)
                            self.assertEqual({p.name for p in output.iterdir()}, set(names))
                            self.assertFalse(m.RESUME_FILE.exists())
                    self.assertEqual(parse.call_count, 1 if boundary == 'success' else 2)
                    self.assertEqual(source.read_bytes(), b'synthetic DOCX input boundary')
                    self.assertEqual(target.stat().st_mode & 0o777, 0o640)
                    self.assertFalse(list(root.rglob('.*.tmp')))

    def test_cr_checkpoint_functions_preserve_each_previous_file_and_retry(self):
        for wg in ('RAN4', 'RAN5'):
            filename = '01_parse_cr_documents.py' if wg == 'RAN5' else '02_parse_cr_documents.py'
            m = self.module(f'{wg}/phase-4/cr-parser/{filename}')
            for kind in ('resume', 'batch'):
                for boundary in ('serialize', 'fsync_os', 'fsync_interrupt',
                                 'replace_os', 'replace_interrupt', 'success'):
                    with self.subTest(wg=wg, kind=kind, boundary=boundary), contextlib.ExitStack() as stack:
                        output = self.root / wg / kind / boundary
                        output.mkdir(parents=True)
                        target = output / ('resume.json' if kind == 'resume'
                                           else 'cr_documents_batch_000.json')
                        old = '{"설명": "기존 결과"}'.encode()
                        target.write_bytes(old)
                        target.chmod(0o640)
                        stack.enter_context(patch.multiple(m, OUTPUT_DIR=output, RESUME_FILE=target))
                        tdoc = f'R{wg[-1]}-' + ('000001' if wg == 'RAN5' else '0000001')
                        row = m.CRDocumentData(tdoc_number=tdoc, cr_pack_id='RP-000001',
                                              release='Rel-18', title='새 결과')
                        bad = boundary == 'serialize'
                        if kind == 'batch' and bad:
                            row.title = object()
                        if kind == 'resume':
                            invoke = lambda: m.save_resume_state(object() if bad else 0, [row], 'synthetic')
                        else:
                            invoke = lambda: m.save_partial_results([row], 0)
                        error = (KeyboardInterrupt('synthetic') if boundary.endswith('interrupt')
                                 else OSError('synthetic'))
                        write = publication_writer(m.write_text_atomic, target, boundary, error)
                        if boundary != 'success':
                            with patch.object(m, 'write_text_atomic', side_effect=write), \
                                    self.assertRaises(TypeError if bad else type(error)) as got:
                                invoke()
                            if not bad:
                                self.assertIs(got.exception, error)
                            self.assertEqual(target.read_bytes(), old)
                            self.assertEqual(target.stat().st_mode & 0o777, 0o640)
                            self.assertEqual(list(output.iterdir()), [target])
                        bad = False
                        row.title = '새 결과'
                        for _ in range(2):
                            result = invoke()
                            data = json.loads(target.read_bytes())
                            if kind == 'resume':
                                self.assertEqual(data, dict(batch_idx=0, results_count=1,
                                                           input_fingerprint='synthetic'))
                                self.assertEqual(target.read_bytes(), json.dumps(data).encode())
                            else:
                                self.assertEqual(result, target)
                                self.assertEqual(data[0]['title'], '새 결과')
                                self.assertEqual(target.read_bytes(),
                                                 json.dumps(data, ensure_ascii=False, indent=2).encode())
                            self.assertEqual(target.stat().st_mode & 0o777, 0o640)
                            self.assertEqual(list(output.iterdir()), [target])

    def test_cr_generators_preserve_actual_four_document_generation_all_four_wgs(self):
        from common import atomic_io

        names = ('crpacks.jsonld', 'cr_extensions.jsonld', 'section_extensions.jsonld', 'spec_dynamic.jsonld')
        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4'):
            with self.subTest(wg=wg), contextlib.ExitStack() as stack:
                with patch.dict(os.environ, {'NEO4J_PASSWORD': 'synthetic-test-only'}):
                    m = self.module(f'{wg}/phase-4/cr-parser/03_generate_cr_jsonld.py')
                root = self.root / 'actual-cr-generation' / wg
                parsed, output = root / 'parsed', root / 'out'
                parsed.mkdir(parents=True)
                output.mkdir()
                tdoc = f'R{wg[-1]}-0000001'
                pack = 'RP-000001'
                section = '38.999-Rel-18-1'
                cover = {'metadata': {'unique_crpacks': 1}, 'crpacks': [{
                    'cr_pack_id': pack, 'tsg_meeting': 'RAN#1', 'cr_entries': [{
                        'tdoc_number': tdoc, 'spec': '38.999', 'cr_number': '0001'}]}]}
                record = {'tdoc_number': tdoc, 'cr_pack_id': pack,
                          'spec_number': '38.999', 'release': 'Rel-18',
                          'reason_for_change': 'Synthetic requested change',
                          'summary_of_change': 'Synthetic revised condition',
                          'clauses_affected': '1', 'affects_core_spec': ['38.998'],
                          'source_path': f'{tdoc}_CR0001.docx'}
                key = 'cr_documents' if wg == 'RAN1' else 'documents'
                (parsed / 'cover_sheets.json').write_text(json.dumps(cover))
                (parsed / 'cr_documents.json').write_text(json.dumps({
                    'metadata': {'unique_crs': 1}, key: [record]}))
                titles = root / 'spec_titles.json'
                titles.write_text(json.dumps({'specs': {'38.998': 'Synthetic linked specification'}}))
                inputs_before = {p: p.read_bytes() for p in (parsed / 'cover_sheets.json',
                                  parsed / 'cr_documents.json', titles)}
                stack.enter_context(patch.multiple(m, PARSED_DIR=parsed, OUTPUT_DIR=output,
                                                  SPEC_TITLES_FILE=titles))
                stack.enter_context(patch.object(m, 'configure_logging'))
                # Phase-1 파일·기존 KG를 읽는 경계만 합성 입력으로 대체한다.
                stack.enter_context(patch.object(m, 'load_phase1_crs', return_value={tdoc}))
                stack.enter_context(patch.object(m, 'load_phase1_specs', return_value={'38.999'}))
                loader = 'load_neo4j_sections' if wg == 'RAN4' else 'load_phase3_sections'
                stack.enter_context(patch.object(m, loader,
                                                return_value=m.SectionIndex([(section, '1')])))
                # 회사 참조가 없는 입력이므로 개인 회사 카탈로그 파일 접근만 격리한다.
                stack.enter_context(patch.dict(m.canonical_document.__globals__,
                                              company_reference_aliases=lambda _wg: {}))
                self.assertEqual(m.main(), 0)
                expected = {name: (output / name).read_bytes() for name in names}
                graphs = {name: json.loads(raw)['@graph'] for name, raw in expected.items()}
                self.assertEqual([len(graphs[name]) for name in names], [1, 1, 1, 1])
                self.assertEqual(graphs[names[0]][0]['hasCR'], f'tdoc:{tdoc}')
                self.assertEqual(graphs[names[1]][0]['modifiesSection'], f'tdoc:section/{section}')
                self.assertEqual(graphs[names[2]][0]['modifiedByCR'], f'tdoc:{tdoc}')
                self.assertEqual(graphs[names[3]][0]['tdoc:specNumber'], '38.998')

                cases = [('fsync', None, False)] + [
                    ('replace', index, after) for index in range(1, 5) for after in (False, True)]
                for boundary, fail_at, after in cases:
                    for error in (OSError, KeyboardInterrupt):
                        with self.subTest(boundary=boundary, fail_at=fail_at, after=after, error=error):
                            previous = {name: f'previous {wg} {name}'.encode() for name in names}
                            for name, raw in previous.items():
                                (output / name).write_bytes(raw)
                                (output / name).chmod(0o640)
                            replace = atomic_io.os.replace
                            count = [0]

                            def fail_replace(source, destination):
                                canonical = Path(destination).parent == output
                                if canonical:
                                    count[0] += 1
                                fail = canonical and count[0] == fail_at
                                if fail and not after:
                                    raise error('publication')
                                result = replace(source, destination)
                                if fail and after:
                                    raise error('publication')
                                return result

                            fault = (dict(side_effect=error('publication')) if boundary == 'fsync'
                                     else dict(side_effect=fail_replace))
                            with patch.object(atomic_io.os, boundary, **fault):
                                with self.assertRaises(error):
                                    m.main()
                            self.assertEqual({name: (output / name).read_bytes() for name in names}, previous)
                            self.assertEqual(sorted(p.name for p in output.iterdir()), sorted(names))
                            for name in names:
                                self.assertEqual((output / name).stat().st_mode & 0o777, 0o640)
                            for _ in range(2):
                                self.assertEqual(m.main(), 0)
                                self.assertEqual({name: (output / name).read_bytes() for name in names}, expected)
                            self.assertEqual({p: p.read_bytes() for p in inputs_before}, inputs_before)

    def test_cr_batch_is_validated_before_first_output_replacement(self):
        from types import SimpleNamespace
        from common import atomic_io
        names = ('crpacks.jsonld','cr_extensions.jsonld','section_extensions.jsonld','spec_dynamic.jsonld')
        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4'):
            for invalid_at in (1, 2, 3, 4, None):
                with self.subTest(wg=wg, invalid_at=invalid_at):
                    # RAN4는 import 시 자격증명을 읽는다. 실제 조회는 아래에서
                    # 대체하므로 개인 .env 대신 이 검사에서만 쓰는 값을 제공한다.
                    with patch.dict(os.environ, {'NEO4J_PASSWORD': 'synthetic-test-only'}):
                        m = self.module(f'{wg}/phase-4/cr-parser/03_generate_cr_jsonld.py')
                    root = self.root / wg / str(invalid_at)
                    parsed = root / 'parsed'; parsed.mkdir(parents=True)
                    (parsed / 'cover_sheets.json').write_text(json.dumps({'metadata':{'unique_crpacks':0}}))
                    key = 'cr_documents' if wg == 'RAN1' else 'documents'
                    (parsed / 'cr_documents.json').write_text(json.dumps({'metadata':{'unique_crs':0},key:[]}))
                    output = root / 'out'; output.mkdir()
                    for name in names: (output / name).write_bytes(b'complete old batch')
                    documents = []

                    def canonical(document, **kwargs):
                        documents.append(document)
                        if len(documents) == invalid_at:
                            raise ValueError('synthetic artifact invalid')
                        return document

                    loader = 'load_neo4j_sections' if wg == 'RAN4' else 'load_phase3_sections'
                    with patch.multiple(m, PARSED_DIR=parsed, OUTPUT_DIR=output), \
                         patch.object(m, 'configure_logging'), \
                         patch.object(m, 'load_phase1_crs', return_value=set()), \
                         patch.object(m, 'load_phase1_specs', return_value=set()), \
                         patch.object(m, loader, return_value=SimpleNamespace(sid_by={},stats={})), \
                         patch.object(m, 'generate_crpacks', return_value=[]), \
                         patch.object(m, 'generate_cr_extensions', return_value=([],set())), \
                         patch.object(m, 'generate_section_extensions', return_value=[]), \
                         patch.object(m, 'generate_dynamic_specs', return_value=[]), \
                         patch.object(m, 'canonical_document', side_effect=canonical):
                        if invalid_at is None:
                            self.assertEqual(m.main(), 0)
                            if wg == 'RAN1':
                                normal_documents = documents.copy()
                                previous = {name: (output / name).read_bytes() for name in names}
                                cases = [('fsync', None, False)] + [
                                    ('replace', index, after) for index in range(1, 5)
                                    for after in (False, True)]
                                for boundary, fail_at, after in cases:
                                    for error in (OSError, KeyboardInterrupt):
                                        replace = atomic_io.os.replace
                                        calls = []

                                        def fail_replace(source, destination):
                                            canonical = Path(destination).parent == output
                                            if canonical:
                                                calls.append(destination)
                                            fail = canonical and len(calls) == fail_at
                                            if fail and not after:
                                                raise error('publication')
                                            result = replace(source, destination)
                                            if fail and after:
                                                raise error('publication')
                                            return result

                                        with self.subTest(boundary=boundary, fail_at=fail_at,
                                                          after=after, error=error):
                                            fault = (dict(side_effect=error('publication'))
                                                     if boundary == 'fsync' else dict(side_effect=fail_replace))
                                            with patch.object(atomic_io.os, boundary, **fault):
                                                with self.assertRaises(error):
                                                    m.main()
                                            self.assertEqual({name: (output / name).read_bytes()
                                                              for name in names}, previous)
                                            self.assertEqual(sorted(p.name for p in output.iterdir()), sorted(names))
                                            for _ in range(2):
                                                self.assertEqual(m.main(), 0)
                                                self.assertEqual({name: (output / name).read_bytes()
                                                                  for name in names}, previous)
                                documents[:] = normal_documents
                        else:
                            with self.assertRaises(ValueError): m.main()
                    self.assertEqual(len(documents), invalid_at or 4)
                    for index, name in enumerate(names):
                        expected = (json.dumps(documents[index], ensure_ascii=False, indent=2).encode()
                                    if invalid_at is None else b'complete old batch')
                        self.assertEqual((output / name).read_bytes(), expected)

    def test_empty_valid_reference_input_preserves_existing_files(self):
        import pandas as pd
        for wg in ('RAN4', 'RAN5'):
            with self.subTest(wg=wg):
                m = self.module(f'{wg}/phase-1/jsonld/02_reference_classes.py')
                inputs = self.root / wg / 'input'; inputs.mkdir(parents=True)
                (inputs / 'TDoc_List_Meeting.xlsx').write_bytes(b'synthetic placeholder')
                intermediate = self.root / wg / 'intermediate'
                aliases = intermediate / wg / 'phase-1/company_aliases_significant.json'
                aliases.parent.mkdir(parents=True); aliases.write_text('{}')
                output = self.root / wg / 'out'; output.mkdir()
                sentinel = output / 'releases.jsonld'; sentinel.write_bytes(b'existing releases')
                with patch.multiple(m, INPUT_DIR=inputs, INTERMEDIATE_DIR=intermediate, OUTPUT_DIR=output), \
                     patch.object(m, 'load_excel_file', return_value=pd.DataFrame()), \
                     patch.object(m, 'load_spec_titles', return_value={}), \
                     patch.object(m, 'save_jsonld') as save:
                    with self.assertRaises(SystemExit):
                        m.main()
                    save.assert_not_called()
                self.assertEqual(sentinel.read_bytes(), b'existing releases')

    def test_reference_main_requires_rows_before_replacing_outputs(self):
        import ast
        import pandas as pd
        from unittest.mock import Mock
        from common.atomic_io import publish_json_set

        classes = ('meetings', 'releases', 'companies', 'contacts',
                   'work_items', 'agenda_items', 'specs', 'working_groups')
        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            source = FORMAL / wg / 'phase-1/jsonld/02_reference_classes.py'
            main = next(node for node in ast.parse(source.read_bytes()).body
                        if isinstance(node, ast.FunctionDef) and node.name == 'main')
            for case in ('empty', 'valid', 'mixed'):
                with self.subTest(wg=wg, case=case):
                    root = self.root / wg / case
                    inputs = root / 'input'; inputs.mkdir(parents=True)
                    filenames = ('empty.xlsx', 'valid.xlsx') if case == 'mixed' else (case + '.xlsx',)
                    for name in filenames: (inputs / name).write_bytes(b'synthetic placeholder')
                    intermediate = root / 'intermediate'
                    aliases = intermediate / wg / 'phase-1/company_aliases_significant.json'
                    aliases.parent.mkdir(parents=True); aliases.write_text('{}')
                    output = root / 'out'; output.mkdir()
                    for name in classes: (output / (name + '.jsonld')).write_bytes(b'previous reference')
                    rows = pd.DataFrame({'TDoc': ['synthetic']})
                    data = {'synthetic': {'@id': 'synthetic'}}
                    namespace = {'INPUT_DIR': inputs, 'INTERMEDIATE_DIR': intermediate,
                                 'OUTPUT_DIR': output,
                                 'load_excel_file': Mock(side_effect=lambda p: rows if p.stem == 'valid' else pd.DataFrame())}
                    for name in classes:
                        namespace['generate_' + name] = Mock(return_value=data)

                    def save(document, path, class_name):
                        path.write_text(json.dumps(document))

                    namespace['save_jsonld'] = Mock(side_effect=save)
                    namespace['prepare_jsonld'] = Mock(side_effect=lambda document, label:
                                                       {'@graph': list(document.values())})
                    namespace['publish_json_set'] = publish_json_set
                    exec(compile(ast.Module(body=[main], type_ignores=[]), str(source), 'exec'), namespace)
                    if case == 'empty':
                        with self.assertRaises(SystemExit): namespace['main']()
                        namespace['save_jsonld'].assert_not_called()
                        for name in classes:
                            namespace['generate_' + name].assert_not_called()
                            self.assertEqual((output / (name + '.jsonld')).read_bytes(), b'previous reference')
                    else:
                        self.assertIsNone(namespace['main']())
                        namespace['save_jsonld'].assert_not_called()
                        self.assertEqual(namespace['prepare_jsonld'].call_count, len(classes))
                        self.assertEqual(namespace['generate_meetings'].call_args.args, (sorted(inputs.iterdir()),))
                        for name in ('releases', 'contacts', 'work_items', 'specs', 'working_groups'):
                            accepted = namespace['generate_' + name].call_args.args[0]
                            self.assertEqual(len(accepted), 1)
                            self.assertIs(accepted[0], rows)
                        for name in classes:
                            self.assertEqual(json.loads((output / (name + '.jsonld')).read_text()),
                                             {'@graph': list(data.values())})

    def test_conversion_cleans_temporary_directories_after_allocation_failure(self):
        import ast
        import shutil
        import signal
        import subprocess
        import zipfile
        import zlib
        import xml.etree.ElementTree as ET
        from unittest.mock import Mock
        from bootstrap.process_stream import stop_process_group
        from native_word_conversion import validate_docx

        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            source = FORMAL / wg / 'phase-10/data-collection/03_transform_meeting.py'
            function = next(node for node in ast.parse(source.read_bytes()).body
                            if isinstance(node, ast.FunctionDef) and node.name == 'convert_to_docx')
            for case in ('first_allocation', 'second_allocation', 'launch_error',
                         'publish_error', 'timeout', 'success', 'existing'):
                with self.subTest(wg=wg, case=case):
                    root = self.root / wg / case; root.mkdir(parents=True)
                    src = root / 'document.doc'; src.write_bytes(b'original document')
                    output = root / 'document.docx'
                    if case == 'existing': output.write_bytes(b'existing document')
                    allocated = []
                    calls = []

                    def allocate(*, prefix):
                        calls.append(prefix)
                        if (case == 'first_allocation' and len(calls) == 1
                                or case == 'second_allocation' and len(calls) == 2):
                            raise OSError('synthetic allocation failure')
                        directory = root / prefix; directory.mkdir()
                        allocated.append(directory)
                        return str(directory)

                    process = Mock(returncode=0, pid=123)
                    if case == 'timeout':
                        process.communicate.side_effect = subprocess.TimeoutExpired('synthetic', 1)

                    def launch(*args, **kwargs):
                        if case == 'launch_error': raise OSError('synthetic launch failure')
                        (allocated[1] / 'document.docx').write_bytes(b'converted document')
                        return process

                    def publish(produced, target, original, **kwargs):
                        if case == 'publish_error': raise ValueError('synthetic validation failure')
                        self.assertEqual(original, src)
                        shutil.copyfile(produced, target)

                    namespace = {'Path': Path, 'tempfile': tempfile, 'shutil': shutil,
                                 'subprocess': subprocess, 'os': os, 'signal': signal,
                                 'CONVERT_TIMEOUT_SEC': 1, 'OUTCOME_OK': 'ok',
                                 'OUTCOME_ERROR': 'error', 'OUTCOME_TIMEOUT': 'timeout',
                                 'stop_process_group': stop_process_group,
                                 'validate_docx': validate_docx, 'zipfile': zipfile,
                                 'ET': ET, 'zlib': zlib,
                                 'publish_validated_conversion': Mock(side_effect=publish)}
                    tree = ast.parse(source.read_bytes())
                    helpers = [node for node in tree.body
                               if isinstance(node, ast.FunctionDef) and node.name == 'valid_docx']
                    if helpers:
                        exec(compile(ast.Module(body=helpers, type_ignores=[]), str(source), 'exec'), namespace)
                    exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), namespace)
                    with patch.object(tempfile, 'mkdtemp', side_effect=allocate), \
                         patch.object(subprocess, 'Popen', side_effect=launch) as popen, \
                         patch.object(os, 'getpgid', return_value=123), patch.object(os, 'killpg') as killpg:
                        invalid_existing = wg in ('RAN1', 'RAN2', 'RAN3') and case == 'existing'
                        expected = ('error' if invalid_existing else 'ok' if case in ('success', 'existing')
                                    else 'timeout' if case == 'timeout' else 'error')
                        try:
                            outcome = namespace['convert_to_docx'](src, output, 'synthetic-soffice')
                        finally:
                            self.assertFalse(any(path.exists() for path in allocated))
                        self.assertEqual(outcome, expected)
                    self.assertEqual(src.read_bytes(), b'original document')
                    if case in ('success', 'existing'):
                        self.assertEqual(output.read_bytes(), b'existing document' if case == 'existing' else b'converted document')
                    else:
                        self.assertFalse(output.exists())
                    if case in ('first_allocation', 'second_allocation', 'existing'):
                        popen.assert_not_called()
                    if case == 'timeout':
                        self.assertEqual(killpg.call_args_list,
                                         [unittest.mock.call(123, signal.SIGTERM),
                                          unittest.mock.call(123, signal.SIGKILL)])
                        self.assertEqual(process.wait.call_count, 2)

    def test_missing_incremental_report_preserves_all_meetings(self):
        m = self.module('RAN4/phase-2/report-parser/01_parse_all.py')
        output = self.root / 'parsed'; output.mkdir()
        instances = self.root / 'instances'; instances.mkdir()
        before = {}
        for name in m.JSONLD_FILES:
            p = instances / name
            p.write_text(json.dumps({'@graph': [{'@id':'old', 'madeAt':'tdoc:meeting/RAN4_100'}]}))
            before[p] = p.read_bytes()
        with patch.multiple(m, OUTPUT_DIR=output, INSTANCES_DIR=instances):
            with self.assertRaises((ValueError, SystemExit)):
                m.generate_jsonld_incremental([{'meeting_id':'RAN4#100', 'status':'success'}])
        self.assertEqual({p:p.read_bytes() for p in before}, before)

    def test_wrong_incremental_report_identity_preserves_all_meetings(self):
        m = self.module('RAN4/phase-2/report-parser/01_parse_all.py')
        output = self.root / 'parsed'; output.mkdir()
        (output / 'RAN4_100.json').write_text(json.dumps({'meeting_id':'RAN4#101'}))
        instances = self.root / 'instances'; instances.mkdir()
        with patch.multiple(m, OUTPUT_DIR=output, INSTANCES_DIR=instances), \
             patch.object(m, '_save_jsonld') as save:
            with self.assertRaises((ValueError, SystemExit)):
                m.generate_jsonld_incremental([{'meeting_id':'RAN4#100', 'status':'success'}])
            save.assert_not_called()

    def test_empty_report_directory_preserves_existing_jsonld(self):
        for wg in ('RAN4', 'RAN5'):
            with self.subTest(wg=wg):
                m = self.module(f'{wg}/phase-2/report-parser/01_parse_all.py')
                output = self.root / wg / 'parsed'; output.mkdir(parents=True)
                instances = self.root / wg / 'instances'; instances.mkdir()
                out = instances / 'tables.jsonld'; out.write_bytes(b'old tables')
                with patch.multiple(m, OUTPUT_DIR=output, INSTANCES_DIR=instances):
                    with self.assertRaises(SystemExit):
                        m.generate_jsonld()
                self.assertEqual(out.read_bytes(), b'old tables')

    def test_report_cli_requires_sources_and_preserves_incremental_contract(self):
        import argparse
        import ast
        from collections import defaultdict
        from datetime import datetime
        from types import SimpleNamespace
        from unittest.mock import Mock
        from common.atomic_io import write_json_atomic, write_text_atomic

        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            source = FORMAL / wg / 'phase-2/report-parser/01_parse_all.py'
            main = next(node for node in ast.parse(source.read_bytes()).body
                        if isinstance(node, ast.FunctionDef) and node.name == 'main')
            for case in ('empty_full', 'valid_full', 'failed_full',
                         'missing_incremental', 'valid_incremental'):
                with self.subTest(wg=wg, case=case):
                    root = self.root / wg / case
                    output = root / 'parsed'; output.mkdir(parents=True)
                    instances = root / 'instances'; instances.mkdir()
                    # Stale parsed data must not make an empty source run successful.
                    parsed = output / 'old.json'; parsed.write_bytes(b'old parsed report')
                    jsonld = instances / 'tables.jsonld'; jsonld.write_bytes(b'old tables')
                    summary = output / '_summary_report.json'
                    summary.write_bytes(b'old complete summary')
                    row = defaultdict(int, status='error' if case == 'failed_full' else 'success',
                                      meeting_id=wg + '#100', error='synthetic parse failure')
                    report = root / 'synthetic.docx'
                    parse = Mock(return_value=row)
                    generate, incremental_generate = Mock(), Mock()
                    namespace = dict(argparse=argparse, sys=sys, json=json, datetime=datetime,
                                     INPUT_DIR=root / 'input', OUTPUT_DIR=output,
                                     INSTANCES_DIR=instances, TABLE_DIR=root / 'tables',
                                     FIGURE_DIR=root / 'figures', EMBEDDED_DIR=root / 'embedded',
                                     get_all_reports=Mock(return_value=[] if case == 'empty_full' else [report]),
                                     _filter_reports=Mock(return_value=[] if case == 'missing_incremental' else [report]),
                                     _canonical_meeting_id=lambda mid: mid,
                                     ReportParser=SimpleNamespace(_extract_meeting_id=lambda path: wg + '#100'),
                                     write_json_atomic=write_json_atomic,
                                     write_text_atomic=write_text_atomic,
                                     parse_single_report=parse, generate_jsonld=generate,
                                     generate_jsonld_incremental=incremental_generate)
                    exec(compile(ast.Module(body=[main], type_ignores=[]), str(source), 'exec'), namespace)
                    argv = [str(source)]
                    if case.endswith('incremental'):
                        argv += ['--meetings', wg + '#100']
                    with patch.object(sys, 'argv', argv):
                        try:
                            namespace['main']()
                        except SystemExit as exc:
                            code = exc.code
                        else:
                            code = 0
                    expected = 2 if case in ('empty_full', 'missing_incremental') else (
                        1 if case == 'failed_full' else 0)
                    self.assertEqual(code, expected)
                    self.assertEqual(parse.call_count, int(case not in ('empty_full', 'missing_incremental')))
                    successful = case in ('valid_full', 'valid_incremental')
                    self.assertEqual(generate.call_count, int(successful and wg != 'RAN1' and
                                                             not (wg == 'RAN4' and case == 'valid_incremental')))
                    self.assertEqual(incremental_generate.call_count,
                                     int(wg == 'RAN4' and case == 'valid_incremental'))
                    if case in ('empty_full', 'missing_incremental', 'valid_incremental'):
                        self.assertEqual(summary.read_bytes(), b'old complete summary')
                    elif case == 'valid_full':
                        self.assertEqual(json.loads(summary.read_text())['totals']['total_meetings'], 1)
                    self.assertEqual(parsed.read_bytes(), b'old parsed report')
                    self.assertEqual(jsonld.read_bytes(), b'old tables')

    def test_ran2_report_jsonld_preserves_each_file_on_publication_failure(self):
        """실제 JSON-LD 생성과 단일 파일 writer의 실패 경계를 검사한다."""
        m = self.module('RAN2/phase-2/report-parser/01_parse_all.py')
        output = self.root / 'ran2-jsonld'; output.mkdir()
        target_path = output / 'tables.jsonld'
        target_path.write_bytes(b'previous complete JSON-LD')
        target_path.chmod(0o640)
        writer = m.write_text_atomic
        writer_os = writer.__globals__['os']
        writer_json = writer.__globals__['json']
        writer_tempfile = writer.__globals__['tempfile']
        allocate = writer_tempfile.NamedTemporaryFile
        # A new PC need not have a company catalog. Keep that input boundary
        # empty while running the real canonicalizer and schema bindings.
        with patch.dict(m.canonical_document.__globals__, company_reference_aliases=lambda wg: {}):
            for error in (OSError, KeyboardInterrupt):
                for boundary in ('serialize', 'partial', 'fsync', 'replace'):
                    before = target_path.read_bytes()
                    target, name = ((writer_json, 'dumps') if boundary == 'serialize'
                                    else (writer_tempfile, 'NamedTemporaryFile') if boundary == 'partial'
                                    else (writer_os, boundary))
                    def fail_partial(*args, **kwargs):
                        stream = allocate(*args, **kwargs)
                        write = stream.write
                        def fail_write(text):
                            write(text[:10])
                            raise error('synthetic partial write')
                        stream.write = fail_write
                        return stream
                    effect = fail_partial if boundary == 'partial' else error('synthetic publication failure')
                    with self.subTest(error=error.__name__, boundary=boundary), \
                         patch.object(target, name, side_effect=effect), self.assertRaises(error):
                        m._save_jsonld(target_path, {}, [])
                    self.assertEqual(target_path.read_bytes(), before)
                    self.assertEqual(target_path.stat().st_mode & 0o777, 0o640)
                    self.assertEqual([p.name for p in output.iterdir()], ['tables.jsonld'])
                    for _ in range(2):
                        m._save_jsonld(target_path, {}, [])
                        saved = json.loads(target_path.read_text())
                        self.assertEqual(saved['@graph'], [])
                        self.assertEqual(saved['@context']['tdoc'], 'https://w3id.org/spectra#')
                        self.assertFalse(target_path.read_bytes().endswith(b'\n'))
                        self.assertEqual(target_path.stat().st_mode & 0o777, 0o640)
                        self.assertEqual([p.name for p in output.iterdir()], ['tables.jsonld'])

    def test_report_main_preserves_each_summary_on_publication_failure(self):
        from collections import defaultdict
        from unittest.mock import Mock

        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            m = self.module(f'{wg}/phase-2/report-parser/01_parse_all.py')
            output = self.root / (wg + '-parsed'); output.mkdir()
            source = self.root / f'Final_Report_{wg}-100.docx'
            source.write_bytes(b'synthetic parser boundary')
            summary = output / '_summary_report.json'
            summary.write_bytes(b'previous complete summary')
            summary.chmod(0o640)
            parsed = output / f'{wg}_100.json'; parsed.write_bytes(b'previous parsed report')
            row = defaultdict(int, status='success', meeting_id=wg + '#100')
            parse = Mock(return_value=row)
            writer = m.write_json_atomic if wg == 'RAN1' else m.write_text_atomic
            writer_os = writer.__globals__['os']
            writer_json = writer.__globals__['json']
            writer_tempfile = writer.__globals__['tempfile']
            allocate = writer_tempfile.NamedTemporaryFile

            with contextlib.ExitStack() as stack:
                stack.enter_context(patch.multiple(m, OUTPUT_DIR=output, INPUT_DIR=self.root,
                                                  INSTANCES_DIR=output / 'instances', create=True))
                stack.enter_context(patch.object(m, 'get_all_reports', return_value=[source]))
                stack.enter_context(patch.object(m, 'parse_single_report', parse))
                stack.enter_context(patch.object(sys, 'argv', [str(m.__file__)]))
                if hasattr(m, 'generate_jsonld'):
                    stack.enter_context(patch.object(m, 'generate_jsonld'))
                if hasattr(m, 'generate_jsonld_incremental'):
                    stack.enter_context(patch.object(m, 'generate_jsonld_incremental'))
                for error in (OSError, KeyboardInterrupt):
                    for boundary in ('serialize', 'partial', 'fsync', 'replace'):
                        before = summary.read_bytes()
                        target, name = ((writer_json, 'dumps') if boundary == 'serialize'
                                        else (writer_tempfile, 'NamedTemporaryFile') if boundary == 'partial'
                                        else (writer_os, boundary))
                        def fail_partial(*args, **kwargs):
                            stream = allocate(*args, **kwargs)
                            write = stream.write
                            def fail_write(text):
                                write(text[:10])
                                raise error('synthetic partial write')
                            stream.write = fail_write
                            return stream
                        effect = fail_partial if boundary == 'partial' else error('synthetic publication failure')
                        with self.subTest(wg=wg, error=error.__name__, boundary=boundary), \
                             patch.object(target, name, side_effect=effect), self.assertRaises(error):
                            m.main()
                        self.assertEqual(summary.read_bytes(), before)
                        self.assertEqual(summary.stat().st_mode & 0o777, 0o640)
                        self.assertEqual(sorted(p.name for p in output.iterdir() if p.is_file()),
                                         [f'{wg}_100.json', '_summary_report.json'])
                        for _ in range(2):
                            self.assertIsNone(m.main())
                            self.assertEqual(json.loads(summary.read_text())['totals']['total_meetings'], 1)
                            self.assertEqual(summary.stat().st_mode & 0o777, 0o640)
                            self.assertEqual(sorted(p.name for p in output.iterdir() if p.is_file()),
                                             [f'{wg}_100.json', '_summary_report.json'])
                before = summary.read_bytes()
                with patch.object(sys, 'argv', [str(m.__file__), '--meetings', wg + '#100']):
                    m.main()
                self.assertEqual(summary.read_bytes(), before)
                with patch.object(sys, 'argv', [str(m.__file__), '--meetings', wg + '#101']):
                    with self.assertRaises(SystemExit) as error:
                        m.main()
                    self.assertEqual(error.exception.code, 2)
                self.assertEqual(summary.read_bytes(), before)
            self.assertEqual(source.read_bytes(), b'synthetic parser boundary')
            self.assertEqual(parsed.read_bytes(), b'previous parsed report')

    def test_partial_tr_parse_keeps_both_previous_outputs(self):
        m = self.module('RAN5/phase-5/tr-parser/01_parse_tr_docs.py')
        inputs = self.root / 'input'; inputs.mkdir()
        for name in ('38.900', '38.901'): (inputs / name).mkdir()
        output = self.root / 'out'; output.mkdir()
        before = {}
        for name in ('tr_documents.json', 'tr_impacts.json'):
            p = output / name; p.write_bytes(b'old complete output'); before[p] = p.read_bytes()
        row = {'trNumber':'38.900','trVersion':'18.0.0','trStatus':'Completed',
               'scope':'scope','conclusions':'conclusions','referencesTR':[]}
        with patch.multiple(m, TR_INPUT_DIR=inputs, OUTPUT_DIR=output), \
             patch.object(m, 'parse_single_tr', side_effect=[row, None]), \
             patch.object(m, 'load_impact_mapping', return_value=[]):
            with self.assertRaises(SystemExit): m.main()
        self.assertEqual({p:p.read_bytes() for p in before}, before)

    def csv_module(self, rows):
        m = self.module('RAN5/phase-5/tr-parser/01_parse_tr_docs.py')
        p = self.root / 'mapping.csv'; p.write_text(
            'trNumber,impactType,impactsSpec,impactsSection,impactDescription\n' + rows)
        self.stack.enter_context(patch.object(m, 'IMPACT_CSV', p))
        return m

    def test_tr_clause_identities_are_distinct(self):
        m = self.csv_module('38.900,NewSection,38.999,5.1,first\n38.900,NewSection,38.999,5.2,second\n')
        # Evidence classification may annotate candidates; it must retain both identities.
        impacts = m.load_impact_mapping()
        self.assertEqual(len({r['trImpactId'] for r in impacts}), 2)

    def test_duplicate_tr_identity_is_explicitly_rejected(self):
        m = self.csv_module('38.900,NewSection,38.999,5.1,first\n38.900,NewSection,38.999,5.1,second\n')
        with self.assertRaises((ValueError, SystemExit)): m.load_impact_mapping()

    def test_tr_mapping_extra_csv_cells_are_rejected(self):
        m = self.csv_module('38.900,NewSection,38.999,5.1,first,UNQUOTED\n')
        with self.assertRaises((ValueError, SystemExit)): m.load_impact_mapping()


class DocFieldSourceRoutingContracts(unittest.TestCase):
    @contextlib.contextmanager
    def bounded_prc_reads(self):
        """동일 Prc 길이를 다시 읽는 즉시 실패해 손상 입력의 무한 반복을 막는다."""
        unpack = struct.unpack_from
        visited = set()

        def checked(fmt, data, offset=0):
            if fmt == '<h':
                key = (data, offset)
                self.assertNotIn(key, visited, 'Prc cursor did not advance')
                visited.add(key)
            return unpack(fmt, data, offset)

        with patch.object(self.module.struct, 'unpack_from', side_effect=checked):
            yield

    def read_clx(self, clx):
        """본문이 비어 있는 Word FIB와 검사할 CLX만 CFB 경계에 제공한다."""
        wd = bytearray(512)
        struct.pack_into('<HH', wd, 0, 0xA5EC, 101)
        struct.pack_into('<H', wd, 34, 9)
        fib = 72
        struct.pack_into('<H', wd, fib, 34)
        struct.pack_into('<II', wd, fib + 2 + 33 * 8, 0, len(clx))
        streams = {'WordDocument': bytes(wd), '0Table': clx}
        with patch.object(self.module, '_Cfb') as cfb:
            cfb.return_value.stream.side_effect = streams.__getitem__
            return self.module._doc_read(b'synthetic CFB boundary', False)

    def test_clx_prc_rejects_negative_or_overrun_lengths_without_repeating(self):
        pcdt = b'\x02' + struct.pack('<II', 4, 0)
        for cb in (-32768, -3, -2, -1):
            with self.subTest(length=cb), self.bounded_prc_reads():
                with self.assertRaises(self.module.DocError):
                    self.read_clx(b'\x01' + struct.pack('<h', cb) + pcdt)
        with self.assertRaises(self.module.DocError):
            self.read_clx(b'\x01' + struct.pack('<h', 12) + b'x')
        for prefix in (b'', b'\x01\x00\x00', b'\x01\x02\x00ab',
                       b'\x01\x00\x00\x01\x02\x00ab'):
            with self.subTest(prefix=prefix):
                self.assertEqual(self.read_clx(prefix + pcdt), (('', '', '', ''), None))

    def test_character_prc_rejects_negative_or_overrun_lengths_without_repeating(self):
        wd = bytes(512)
        for cb in (-32768, -3, -2, -1):
            with self.subTest(length=cb), self.bounded_prc_reads():
                with self.assertRaises(self.module.DocError):
                    self.module._char_marks(wd, b'', 0,
                                            b'\x01' + struct.pack('<h', cb), [], 0)
        with self.assertRaises(self.module.DocError):
            self.module._char_marks(wd, b'', 0, b'\x01\x02\x00x', [], 0)
        for prcs in (b'', b'\x01\x00\x00', b'\x01\x02\x00ab',
                     b'\x01\x00\x00\x01\x02\x00ab'):
            with self.subTest(prcs=prcs):
                self.assertEqual(self.module._char_marks(wd, b'', 0, prcs, [], 0),
                                 (None, {}))

    def setUp(self):
        import doc_fields
        self.module = doc_fields
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def converted(self, path, application=b'LibreOffice'):
        import zipfile
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('docProps/app.xml', application)
        return path

    def test_same_folder_native_source_and_non_lo_document(self):
        source = self.root / 'input.doc'
        source.write_bytes(b'native source')
        output = self.converted(self.root / 'input.docx')
        self.assertEqual(self.module.lo_source(output), str(source))
        self.converted(output, b'Microsoft Word')
        self.assertIsNone(self.module.lo_source(output))

    def test_collision_avoiding_doc_suffix_resolves_original(self):
        source = self.root / 'input.doc'
        source.write_bytes(b'native source')
        output = self.converted(self.root / 'input.doc.docx')
        self.assertEqual(self.module.lo_source(output), str(source))

    def test_ts_derived_slot_resolves_source_slot(self):
        source = self.root / 'TS/RAN1/source/38.201/Rel-15/input.doc'
        source.parent.mkdir(parents=True)
        source.write_bytes(b'native source')
        output = self.converted(self.root / 'TS/RAN1/derived/38.201/Rel-15/input.docx')
        self.assertEqual(self.module.lo_source(output), str(source))

    def test_ole_shipped_with_docx_suffix_requires_native_signature(self):
        source = self.root / 'input.docx'
        source.write_bytes(self.module._SIG + b'native source')
        output = self.converted(self.root / 'input.docx.docx')
        self.assertEqual(self.module.lo_source(output), str(source))
        source.write_bytes(b'PK ordinary OOXML')
        self.assertIsNone(self.module.lo_source(output))

    def test_directory_cache_observes_added_and_removed_source(self):
        source = self.root / 'input.doc'
        output = self.converted(self.root / 'input.docx')
        self.assertIsNone(self.module.lo_source(output))
        source.write_bytes(b'native source')
        self.assertEqual(self.module.lo_source(output), str(source))
        source.unlink()
        self.assertIsNone(self.module.lo_source(output))

    def test_native_title_cache_observes_source_creation_and_replacement(self):
        import cr_word_title
        source = self.root / 'title.doc'
        self.assertIsNone(cr_word_title.doc_title(str(source)))

        def read(data, _fields):
            return (("Title\x07" + data.decode() + "\x07", '', '', ''), None)

        with patch.object(self.module, '_doc_read', side_effect=read) as reader:
            source.write_bytes(b'old')
            before = source.stat()
            self.assertEqual(cr_word_title.doc_title(str(source)), 'old')
            self.assertEqual(cr_word_title.doc_title(str(source)), 'old')
            self.assertEqual(reader.call_count, 1)
            replacement = self.root / 'replacement.doc'
            replacement.write_bytes(b'new')
            os.utime(replacement, ns=(before.st_atime_ns, before.st_mtime_ns))
            replacement.replace(source)
            self.assertEqual(cr_word_title.doc_title(str(source)), 'new')
            self.assertEqual(reader.call_count, 2)

    def test_native_cache_observes_replaced_file_with_same_mtime_and_size(self):
        source = self.root / 'input.doc'
        source.write_bytes(b'old')
        before = source.stat()
        with patch.object(self.module, '_doc_read', return_value=(('text', '', '', ''), None)) as reader:
            self.module.doc_load(str(source))
            replacement = self.root / 'replacement.doc'
            replacement.write_bytes(b'new')
            os.utime(replacement, ns=(before.st_atime_ns, before.st_mtime_ns))
            os.replace(replacement, source)
            self.module.doc_load(str(source))
            self.assertEqual(reader.call_count, 2)


class ContactScopeWriteContracts(unittest.TestCase):
    def test_contact_replacement_failure_preserves_old_artifact(self):
        module = load('common/contact_scope.py')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contacts, report = root / 'contacts.jsonld', root / 'scope.txt'
            original = json.dumps({'@graph': [{'@id': 'kept'}, {'@id': 'unused'}]}).encode()
            contacts.write_bytes(original)
            report.write_bytes(b'old report')
            with patch('atomic_io.os.replace', side_effect=OSError('synthetic replacement failure')):
                with self.assertRaisesRegex(OSError, 'synthetic replacement failure'):
                    module.scope_contacts([{'hasContact': 'kept'}], contacts, report)
            self.assertEqual(contacts.read_bytes(), original)
            self.assertEqual(report.read_bytes(), b'old report')
            self.assertEqual(sorted(p.name for p in root.iterdir()), ['contacts.jsonld', 'scope.txt'])

    def test_scope_report_replacement_failure_preserves_old_report(self):
        module = load('common/contact_scope.py')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contacts, report = root / 'contacts.jsonld', root / 'scope.txt'
            contacts.write_text(json.dumps({'@graph': [{'@id': 'kept'}]}))
            original = contacts.read_bytes()
            report.write_bytes(b'old report')
            with patch('atomic_io.os.replace', side_effect=OSError('synthetic report failure')):
                with self.assertRaisesRegex(OSError, 'synthetic report failure'):
                    module.scope_contacts([{'hasContact': 'kept'}], contacts, report)
            self.assertEqual(contacts.read_bytes(), original)
            self.assertEqual(report.read_bytes(), b'old report')
            self.assertEqual(sorted(p.name for p in root.iterdir()), ['contacts.jsonld', 'scope.txt'])


class SyntheticCQContracts(unittest.TestCase):
    @contextlib.contextmanager
    def cq_runner(self, wg):
        """실제 CQ 진입점을 임시 입력과 Neo4j I/O 대역으로 실행한다."""
        from types import SimpleNamespace

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = root / 'cq.json'
            dataset.write_text(json.dumps({'questions': [{
                'id': 'synthetic-1', 'category': 'synthetic',
                'question': 'Synthetic row count', 'cypher': 'RETURN 1 AS n',
                'expected_min_rows': 1,
            }]}))
            output = root / 'result.json'
            output.write_bytes(b'previous complete CQ report')
            output.chmod(0o640)
            with patch.dict(os.environ, NEO4J_PASSWORD='synthetic-cq-fixture'):
                module = load(f'{wg}/phase-2/validation/01_validate_cq_cypher.py')

            class Result(list):
                def consume(self):
                    return SimpleNamespace(notifications=[])

            class Session:
                def __enter__(self):
                    if driver.boundary == 'enter':
                        raise driver.error('synthetic session enter failure')
                    return self

                def __exit__(self, *args):
                    if driver.boundary == 'exit':
                        raise driver.error('synthetic session exit failure')

                def run(self, query, **params):
                    driver.queries.append(query)
                    return Result([{'n': 1}] if query == 'RETURN 1 AS n' else [])

            class Driver:
                boundary = None
                error = OSError

                def __init__(self):
                    self.closed = 0
                    self.queries = []

                def session(self, **kwargs):
                    if self.boundary == 'session':
                        raise self.error('synthetic session creation failure')
                    return Session()

                def close(self):
                    self.closed += 1

            driver = Driver()

            def invoke():
                if wg in ('RAN1', 'RAN2'):
                    return module.run_validation()
                with self.assertRaises(SystemExit) as stopped:
                    module.main()
                self.assertEqual(stopped.exception.code, 0)

            # Dataset, output and driver are the only execution boundaries.
            # Production run_cq, guard_defects, serialization and writers run.
            with patch.multiple(module, DATASET=dataset, OUTPUT=output,
                                CQ_DATASET_PATH=dataset, OUTPUT_PATH=output, create=True), \
                 patch.object(module.GraphDatabase, 'driver', return_value=driver), \
                 contextlib.redirect_stdout(io.StringIO()):
                yield module, driver, output, dataset, invoke

    def test_actual_five_wg_cq_reports_preserve_bytes_on_publication_failure(self):
        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            with self.cq_runner(wg) as (module, driver, output, dataset, invoke):
                writer = module.write_json_atomic if wg == 'RAN1' else module.write_text_atomic
                writer_os = writer.__globals__['os']
                writer_json = writer.__globals__['json']
                writer_tempfile = writer.__globals__['tempfile']
                allocate = writer_tempfile.NamedTemporaryFile
                source_bytes = dataset.read_bytes()
                for error in (OSError, KeyboardInterrupt):
                    for boundary in ('serialize', 'partial', 'fsync', 'replace'):
                        before = output.read_bytes()
                        target, name = ((writer_json, 'dumps') if boundary == 'serialize'
                                        else (writer_tempfile, 'NamedTemporaryFile') if boundary == 'partial'
                                        else (writer_os, boundary))

                        def fail_partial(*args, **kwargs):
                            stream = allocate(*args, **kwargs)
                            write = stream.write

                            def fail_write(text):
                                write(text[:10])
                                raise error('synthetic partial CQ write')

                            stream.write = fail_write
                            return stream

                        effect = fail_partial if boundary == 'partial' else error('synthetic CQ publication failure')
                        closed = driver.closed
                        with self.subTest(wg=wg, error=error.__name__, boundary=boundary), \
                             patch.object(target, name, side_effect=effect), self.assertRaises(error):
                            invoke()
                        self.assertEqual(driver.closed, closed + 1)
                        self.assertEqual(output.read_bytes(), before)
                        self.assertEqual(output.stat().st_mode & 0o777, 0o640)
                        self.assertEqual(sorted(p.name for p in output.parent.iterdir()), ['cq.json', 'result.json'])
                        for _ in range(2):
                            closed = driver.closed
                            invoke()
                            saved = json.loads(output.read_text())
                            self.assertEqual(saved['results'][0]['id'], 'synthetic-1')
                            self.assertEqual(saved['results'][0]['status'], 'PASS')
                            self.assertEqual(output.read_bytes().endswith(b'\n'), wg == 'RAN1')
                            self.assertEqual(output.stat().st_mode & 0o777, 0o640)
                            self.assertEqual(driver.closed, closed + 1)
                            self.assertEqual(sorted(p.name for p in output.parent.iterdir()), ['cq.json', 'result.json'])
                self.assertEqual(dataset.read_bytes(), source_bytes)
                self.assertIn('RETURN 1 AS n', driver.queries)
                self.assertIn('EXPLAIN RETURN 1 AS n', driver.queries)

    def test_actual_five_wg_cq_drivers_close_on_session_failure_or_interrupt(self):
        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            with self.cq_runner(wg) as (_, driver, output, dataset, invoke):
                source_bytes, before = dataset.read_bytes(), output.read_bytes()
                for error in (OSError, KeyboardInterrupt):
                    driver.error = error
                    for boundary in ('session', 'enter', 'exit'):
                        driver.boundary = boundary
                        closed = driver.closed
                        with self.subTest(wg=wg, error=error.__name__, boundary=boundary), self.assertRaises(error):
                            invoke()
                        self.assertEqual(driver.closed, closed + 1)
                        self.assertEqual(output.read_bytes(), before)
                        self.assertEqual(dataset.read_bytes(), source_bytes)
                        self.assertEqual(sorted(p.name for p in output.parent.iterdir()), ['cq.json', 'result.json'])

    def approval(self, cypher):
        import cq_anchor_guard as guard
        return guard.approval_contract_defects({'question':'승인한 Resolution 목록은?', 'cypher':cypher})

    def test_approval_predicates_accept_bound_maps_and_where_equalities(self):
        for query in (
            "MATCH (r:Resolution)-[:HAS_DISPOSITION]->(d:DecisionDisposition {dispositionCode:'agreed', evidenceStatus:'source_verified'})-[:DISPOSITION_TARGET]->(t) RETURN t",
            'MATCH (r:Agreement)-[:HAS_DISPOSITION]->(d:DecisionDisposition {dispositionCode:"agreed", evidenceStatus:"source_verified"})-[:DISPOSITION_TARGET]->(t) RETURN t',
            "MATCH (r:Resolution)-[:HAS_DISPOSITION]->(d:DecisionDisposition)-[:DISPOSITION_TARGET]->(t) WHERE d.dispositionCode = 'agreed' AND 'source_verified' = d.evidenceStatus RETURN t",
            "MATCH (t)<-[:DISPOSITION_TARGET]-(d:DecisionDisposition)<-[:HAS_DISPOSITION]-(r:Resolution) WHERE d.dispositionCode = 'agreed' AND d.evidenceStatus = 'source_verified' RETURN t",
        ):
            with self.subTest(query=query): self.assertEqual(self.approval(query), [])

    def test_approval_comments_display_and_wrong_variable_do_not_constrain(self):
        base = 'MATCH (r:Resolution)-[:HAS_DISPOSITION]->(d:DecisionDisposition)-[:DISPOSITION_TARGET]->(t) '
        for tail in (
            "RETURN t // dispositionCode:'agreed' evidenceStatus:'source_verified'",
            "RETURN t /* dispositionCode:'agreed' evidenceStatus:'source_verified' */",
            'RETURN t, "dispositionCode:\'agreed\' evidenceStatus:\'source_verified\'" AS display',
            "MATCH (x:Other {dispositionCode:'agreed', evidenceStatus:'source_verified'}) RETURN t",
            "MATCH (x:DecisionDisposition {dispositionCode:'agreed', evidenceStatus:'source_verified'}) RETURN t",
            "RETURN d.dispositionCode = 'agreed', d.evidenceStatus = 'source_verified'",
        ):
            with self.subTest(tail=tail): self.assertTrue(self.approval(base + tail))

    def test_approval_negated_or_disjunctive_equalities_do_not_constrain(self):
        base = 'MATCH (r:Resolution)-[:HAS_DISPOSITION]->(d:DecisionDisposition)-[:DISPOSITION_TARGET]->(t) WHERE '
        for condition in (
            "NOT d.dispositionCode = 'agreed' AND d.evidenceStatus = 'source_verified'",
            "d.dispositionCode = 'agreed' AND d.evidenceStatus = 'source_verified' OR true",
        ):
            with self.subTest(condition=condition): self.assertTrue(self.approval(base + condition + ' RETURN t'))

    def test_approval_disconnected_tokens_do_not_prove_a_target_path(self):
        self.assertTrue(self.approval("MATCH (r:Resolution)-[:HAS_DISPOSITION]->(d:DecisionDisposition {dispositionCode:'agreed', evidenceStatus:'source_verified'}) MATCH (x)-[:DISPOSITION_TARGET]->(t) RETURN t"))
        import cq_anchor_guard as guard
        self.assertEqual(guard.approval_contract_defects({
            'question':'Agreement가 참조한 Tdoc 목록은? (CR 승인 관련 원본 추적)',
            'cypher':'MATCH(a:Agreement)-[:REFERENCES]->(t:Tdoc) RETURN t'}), [])

    def test_literal_fixture_has_no_original_log_dependency(self):
        import cq_anchor_guard as guard
        query = "MATCH (n:Spec) WHERE n.specNumber =~ '38[.]213' RETURN n"
        self.assertEqual(guard.extract_anchors(query), [])

    def test_latest_document_roles_are_checked_and_literals_are_opaque(self):
        import cq_anchor_guard as guard
        for label in ('Summary', 'SessionNotes'):
            for relation in ('MADE_AT', 'RESOLUTION_BELONGS_TO'):
                self.assertEqual(len(guard.document_role_defects(
                    f'MATCH (d:{label}) MATCH (d)-[:{relation}]->(x) RETURN d')), 1)
        for query in (
            'MATCH (d:Summary)-[:PRESENTED_AT]->(x) RETURN d',
            'MATCH (d:Resolution)-[:MADE_AT]->(x) RETURN d',
            'RETURN "MATCH (d:Summary)-[:MADE_AT]->(x)" AS text',
            '// MATCH (d:Summary)-[:MADE_AT]->(x)\nRETURN 1',
        ):
            self.assertEqual(guard.document_role_defects(query), [])


class ReceiptContracts(unittest.TestCase):
    def setUp(self):
        import tr_impact_evidence
        self.helper = tr_impact_evidence
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source.txt'
        self.source.write_text('explicitly retained synthetic primary evidence')

    def row(self, typ='NewSection'):
        return {'trImpactId':'38.900-38.999-S5.1', 'trNumber':'38.900',
                'impactType':typ, 'impactsSpec':'38.999', 'impactsSection':'5.1',
                'impactDescription':'reviewed synthetic description'}

    def receipt(self, row, *, tamper=False, wg='RAN4'):
        evidence = {'path':'source.txt', 'sha256':hashlib.sha256(self.source.read_bytes()).hexdigest(),
                    'quote':self.source.read_text(), 'locator':'synthetic line 1', 'kind':'incorporation'}
        if tamper: evidence['sha256'] = '0' * 64
        entry = {'claim':self.helper.claim_of(row), 'status':'verified',
                 'verifiedImpactDescription':row['impactDescription'],
                 'reviewExplanation':'synthetic local adjudication', 'incorporationEvidence':evidence}
        scope = {'NoChange':'explicit_no_change', 'NewSection':'new_section'}.get(row['impactType'], 'existing_section_change')
        entry['verifiedImpactScope'] = scope
        entry['scopeAssessment'] = {'scope':scope,
            'explanation':'The synthetic source fixture binds exactly this operation scope.',
            'evidence':[evidence]}
        path = self.root / 'ontology/input/tsg/RAN/formal/TR/RAN4/tr_impact_evidence.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'wg':wg, 'schema':1, 'claims':[entry]}))

    def test_causal_tampered_receipt_is_rejected(self):
        row = self.row(); self.receipt(row, tamper=True)
        with self.assertRaises(self.helper.ImpactEvidenceError):
            self.helper.assess_impacts(self.root, 'RAN4', [row])

    def test_nochange_tampered_receipt_cannot_claim_source_verified(self):
        row = self.row('NoChange'); self.receipt(row, tamper=True)
        with self.assertRaises(self.helper.ImpactEvidenceError):
            self.helper.assess_impacts(self.root, 'RAN4', [row])

    def test_unknown_verified_type_is_rejected(self):
        row = self.row('NewSectoin'); self.receipt(row)
        with self.assertRaises(self.helper.ImpactEvidenceError):
            self.helper.assess_impacts(self.root, 'RAN4', [row])

    def test_pending_empty_and_nochange_records_remain_usable(self):
        self.assertEqual(self.helper.assess_impacts(self.root, 'RAN4', []), [])
        rows = [self.row('NoChange'), self.row('TopicalCandidate')]
        self.helper.assess_impacts(self.root, 'RAN4', rows)
        self.assertEqual([r['evidenceStatus'] for r in rows], ['pending', 'pending'])

    def test_nochange_verified_source_keeps_noncausal_target_role(self):
        self.source.write_text('Within clause 5.1 of TS 38.999, this study requires no changes.')
        row = self.row('NoChange')
        row['impactDescription'] = self.source.read_text()
        self.receipt(row)
        path = self.root / 'ontology/input/tsg/RAN/formal/TR/RAN4/tr_impact_evidence.json'
        manifest = json.loads(path.read_text())
        manifest['claims'][0]['incorporationEvidence']['kind'] = 'explicit_no_change'
        manifest['claims'][0]['boundedScope'] = 'TS 38.999 clause 5.1 in the synthetic study'
        path.write_text(json.dumps(manifest))
        self.helper.evidence_instance(self.root, 'RAN4', row)
        self.assertEqual(row['evidenceStatus'], 'source_verified')
        self.assertNotIn('impactsSpec', row)
        self.assertEqual(row['candidateImpactsSpec'], '38.999')
        calls = []
        class Session:
            def run(self, query, **params):
                calls.append((query, params))
                return type('Result', (), {'single':lambda _: {'count':1}, 'consume':lambda _: None})()
        self.helper.link_assessed_impact_targets(Session(), self.root, 'RAN4', [row])
        self.assertIn('[r:CANDIDATE_IMPACTS_SPEC]', calls[0][0])
        self.assertNotIn('[:SPEC_IMPACTED_BY]', calls[0][0])

    def test_canonical_saved_references_match_reviewed_claim(self):
        from ontology.jsonld_context import canonical_document
        row = self.row(); self.receipt(row)
        node = {'@id':'impact:' + row['trImpactId'], '@type':'TRImpact',
                'trImpactId':row['trImpactId'], 'impactType':row['impactType'],
                'impactOfTR':{'@id':'tr:38.900'},
                'impactsSpec':{'@id':'spec:38.999'},
                'impactsSection':{'@id':'section:38.999-Rel-18-5.1'},
                'impactDescription':row['impactDescription']}
        saved = json.loads(json.dumps(canonical_document({'@graph':[node]})))['@graph'][0]
        self.assertEqual(self.helper.claim_of(saved), self.helper.claim_of(row))
        self.helper.require_verified_impacts(self.root, 'RAN4', [saved])

    def test_loader_retains_raw_and_candidate_clause_metadata(self):
        calls = []
        class Session:
            def run(self, query, **params):
                calls.append((query, params))
                return type('Result', (), {'single':lambda _: {'count':1}, 'consume':lambda _: None})()
        row = self.row()
        self.helper.evidence_instance(self.root, 'RAN4', row)
        self.helper.load_assessed_impact_nodes(Session(), self.root, 'RAN4', [row])
        self.assertEqual(calls[0][1]['rows'][0]['affectedSection'], '5.1')

    def test_manifest_working_group_identity_is_checked_for_nochange(self):
        row = self.row('NoChange'); self.receipt(row, wg='RAN5')
        with self.assertRaises(self.helper.ImpactEvidenceError):
            self.helper.assess_impacts(self.root, 'RAN4', [row])


class CRRangeContracts(unittest.TestCase):
    def test_actual_heading_candidates_preserve_range_and_prefix_rules(self):
        with patch.object(sys, 'path', [str(FORMAL / 'common'), *sys.path]):
            import cr_clause
            import cr_revision_marks
        cases = [
            ('2-11', ['2', '3.1', '7', '11', '12'], ['3', '7']),
            ('Annex A - D', ['A', 'B.2', 'C', 'D', 'E'], ['B', 'C']),
            ('A.1-A.4', ['A.1', 'A.2.3', 'A.3', 'A.4'], ['A.2', 'A.3']),
            ('9.A-9.D', ['9.A', '9.B.2', '9.C', '9.D'], ['9.B', '9.C']),
            ('5.1~4', ['5.1', '5.2.7', '5.4', '5.5'], ['5.2', '5.4']),
            ('5.1～4', ['5.1', '5.2.7', '5.4', '5.5'], ['5.2', '5.4']),
            ('5.1〜4', ['5.1', '5.2.7', '5.4', '5.5'], ['5.2', '5.4']),
            ('5.01-5.04', ['5.2', '5.02', '5.3'], ['5.2', '5.3']),
            ('5.4-5.1', ['5.1', '5.2', '5.4'], []),
            ('5.4~1', ['5.1', '5.2', '5.4'], []),
            ('5.1-6.4', ['5.2', '5.5', '6.1'], []),
            ('Table 5.2-1', ['5.1', '5.2', '5.3'], []),
            ('G-FR1-A4', ['A.2', 'A.3', 'A.4'], []),
            ('5.1/5.4', ['5.2', '5.3'], []),
            ('5.2.x (new)', ['5.2', '5.2.1'], []),
            ('', ['5.2'], []),
            (None, ['5.2'], []),
        ]
        for cell, headings, expected in cases:
            with self.subTest(cell=cell):
                self.assertEqual(cr_clause.range_clauses(cell, iter(headings)), expected)
        self.assertEqual(cr_clause.placeholder_clauses('5.2.x (new)'), ['5.2.x'])
        self.assertEqual(cr_clause.clause_candidates('5.1-5.4'), [('5.1',), ('5.4',)])
        retained = cr_clause.range_clauses('5.1-5.4', ['5.2.7', '5.3', '5.2.7'])
        self.assertEqual(retained, ['5.2', '5.3'])
        self.assertTrue(cr_revision_marks.declared('5.2.7', retained))
        self.assertTrue(cr_revision_marks.declared('5', retained))
        self.assertFalse(cr_revision_marks.declared('5.20', retained))

    def test_billion_endpoints_only_inspect_actual_headings_and_their_parents(self):
        with patch.object(sys, 'path', [str(FORMAL / 'common'), *sys.path]):
            import cr_clause
        cases = [
            ('2-1000000000', ['2', '3.9', '999999999.1', '1000000000', '1000000001'],
             ['3', '999999999']),
            ('5.1-5.1000000000', ['5.1', '5.2.7', '5.999999999.1', '5.1000000000', '5.1000000001'],
             ['5.2', '5.999999999']),
            ('5.1~1000000000', ['5.1', '5.2.7', '5.999999999.1', '5.1000000000', '5.1000000001'],
             ['5.2', '5.999999999', '5.1000000000']),
        ]
        for cell, headings, expected in cases:
            with self.subTest(cell=cell):
                self.assertEqual(cr_clause.range_clauses(cell, iter(headings)), expected)
        self.assertEqual(cr_clause.range_clauses('2-1000000000', iter(())), [])

    def test_all_five_actual_phase8_entrypoints_use_finite_headings(self):
        from types import SimpleNamespace
        from xml.etree import ElementTree as ET
        with patch.object(sys, 'path', [str(FORMAL / 'common'), *sys.path]):
            import cr_clause
            import tdoc_body_source_metadata
            import tdoc_source_metadata
        cases = [
            ('5.1-5.4', ['5', '5.1', '5.2.7', '5.3', '5.4', '5.5', '9.9'],
             [True, True, True, True, True, False, True], ['5.1', '5.4']),
            ('5.1-5.1000000000', ['5.1', '5.2.7', '5.999999999.1', '5.1000000000', '5.1000000001', '9.9'],
             [True, True, True, True, False, True], ['5.1', '5.1000000000']),
            ('5.1~1000000000', ['5.1', '5.2.7', '5.999999999.1', '5.1000000000', '5.1000000001', '9.9'],
             [True, True, True, True, False, True], ['5.1']),
        ]
        word = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            m = load(f'{wg}/phase-8/cr-parser/01_parse_cr_chunks.py')
            for cell, numbers, expected_keep, expected_clauses in cases:
                with self.subTest(wg=wg, cell=cell), tempfile.TemporaryDirectory() as temp, \
                        contextlib.ExitStack() as stack:
                    root = Path(temp)
                    tdoc = f'R{wg[-1]}-100001'
                    omitted = []
                    seen = []
                    def selected_range(text, sections):
                        actual = list(sections)
                        seen.append(actual)
                        return cr_clause.range_clauses(text, actual)
                    stack.enter_context(patch.object(m, 'PROJECT_ROOT', root))
                    stack.enter_context(patch.object(m, 'count_tokens', side_effect=lambda text: len(text.split())))
                    stack.enter_context(patch.object(m, 'range_clauses', side_effect=selected_range))
                    if wg == 'RAN5':
                        stack.enter_context(patch.object(tdoc_source_metadata, 'identity_fields', return_value={}))
                        form = m.CRFormData(tdoc_number=tdoc, spec_number='38.999', clauses=cell,
                                            title='Synthetic input ' * 15)
                        sections = [(f'{number} Synthetic heading', number, f'body_item_{i}', number == '9.9')
                                    for i, number in enumerate(numbers)]
                        chunks = m.generate_cr_chunks(form, '\n'.join(row[2] for row in sections),
                                                      sections, False, False, omitted=omitted)
                        snippet = chunks[0].body_snippet
                        self.assertEqual(chunks[0].section_ids, [f'38.999-{n}' for n in expected_clauses])
                        self.assertEqual(chunks[0].clauses_affected, cell)
                    else:
                        elements = []
                        for i, number in enumerate(numbers):
                            heading = ET.Element(word + 'p')
                            props = ET.SubElement(heading, word + 'pPr')
                            ET.SubElement(props, word + 'pStyle', {word + 'val': 'Heading1'})
                            ET.SubElement(ET.SubElement(heading, word + 'r'), word + 't').text = f'{number} Synthetic heading'
                            paragraph = ET.Element(word + 'p')
                            parent = ET.SubElement(paragraph, word + 'ins') if number == '9.9' else paragraph
                            ET.SubElement(ET.SubElement(parent, word + 'r'), word + 't').text = f'body_item_{i}'
                            elements.extend([('p', heading), ('p', paragraph)])
                        stack.enter_context(patch.object(m, 'identity', return_value=SimpleNamespace(
                            resolve=lambda _: ('38.999', 'CR0001', tdoc))))
                        stack.enter_context(patch.object(m, 'parse_body_xml', return_value=elements))
                        stack.enter_context(patch.object(m.tsg_cr_decision, 'sheet_cr_label', side_effect=lambda label, *args: label))
                        stack.enter_context(patch.object(tdoc_body_source_metadata, 'validate_source_selection'))
                        chunks = m.parse_single_cr(root / 'synthetic.docx', {},
                                                   {tdoc: {'clauses_affected': cell}}, omitted=omitted)
                        snippet = chunks[0].bodySnippet
                        self.assertEqual(chunks[0].clausesAffected, expected_clauses)
                        self.assertEqual(chunks[0].sectionIds, [f'38.999-{n}' for n in expected_clauses])
                    self.assertEqual(seen, [numbers])
                    self.assertEqual(omitted, [number for number, keep in zip(numbers, expected_keep) if not keep])
                    for i, keep in enumerate(expected_keep):
                        self.assertEqual(f'body_item_{i}' in snippet, keep)
                    self.assertEqual(list(root.iterdir()), [])


class NativeConversionProcessContracts(unittest.TestCase):
    CHILD_PROGRAM = '''import os, signal, sys, time
signal.signal(signal.SIGTERM, signal.SIG_IGN)
with open(sys.argv[1], 'w') as stream:
    stream.write(str(os.getpid()))
while True:
    time.sleep(1)
'''
    WORKER_PROGRAM = '''import hashlib, json, os, signal, subprocess, sys, time, zipfile
from pathlib import Path
pidfile, child_code, ready, mode, source, output, receipt = sys.argv[1:]
if mode in ('timeout', 'term_error'):
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
child = subprocess.Popen([sys.executable, '-B', '-c', child_code, ready],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
deadline = time.monotonic() + 5
while not Path(ready).exists():
    if time.monotonic() > deadline:
        raise RuntimeError('Synthetic grandchild did not start')
    time.sleep(0.01)
Path(pidfile).write_text(json.dumps({'leader': os.getpid(), 'child': child.pid, 'group': os.getpgrp()}))
if mode == 'success':
    with zipfile.ZipFile(output, 'w') as archive:
        archive.writestr('word/document.xml', '<document><text>Synthetic conversion</text></document>')
    digest = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
    Path(receipt).write_text(json.dumps({'status':'verified', 'sourceSha256':digest(source),
        'outputSha256':digest(output), 'strictXml':True, 'redlinesAfter':0,
        'acceptedRenderedText':{'equal':True}}))
else:
    while True:
        time.sleep(1)
'''

    @staticmethod
    def wait_ready(path):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if path.exists():
                try:
                    return json.loads(path.read_text())
                except json.JSONDecodeError:
                    pass
            time.sleep(0.01)
        raise AssertionError('Synthetic process tree did not become ready')

    def assert_not_running(self, pid):
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            try:
                state = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[0]
            except (FileNotFoundError, ProcessLookupError):
                # Linux can reap the task between opening and reading procfs.
                return
            # An adopted child can remain briefly as an init-owned zombie;
            # it has no running converter and no live address space.
            if state == 'Z':
                return
            time.sleep(0.01)
        self.fail(f'Synthetic converter process {pid} is still running')

    def test_process_exit_during_proc_read_is_distinct_from_unreadable_or_live_process(self):
        for error in (FileNotFoundError(2, 'reaped'), ProcessLookupError(3, 'reaped')):
            with self.subTest(error=type(error).__name__), \
                    patch.object(Path, 'read_text', side_effect=error), \
                    patch.object(time, 'sleep') as pause:
                self.assert_not_running(2147483647)
                pause.assert_not_called()
        with patch.object(Path, 'read_text', side_effect=PermissionError('unreadable')):
            with self.assertRaises(PermissionError):
                self.assert_not_running(2147483647)
        with patch.object(Path, 'read_text', return_value='1 (fixture) S'), \
                patch.object(time, 'monotonic', side_effect=[0, 0, 4]), \
                patch.object(time, 'sleep'):
            with self.assertRaisesRegex(AssertionError, 'still running'):
                self.assert_not_running(2147483647)

    def conversion(self, mode):
        with patch.object(sys, 'path', [str(FORMAL / 'common'), *sys.path]):
            import native_word_conversion as m
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, produced = root / 'source.doc', root / 'produced.docx'
            pidfile, ready = root / 'pids.json', root / 'child-ready'
            source.write_bytes(b'Synthetic native source')
            previous = b'previous malformed converter output'
            produced.write_bytes(previous)
            produced.chmod(0o640)
            real_popen = subprocess.Popen
            real_killpg = os.killpg
            real_stop = m._stop_owned_group
            processes = []
            metadata = {}
            previous_handler = signal.getsignal(signal.SIGTERM)

            def launch(command, **kwargs):
                self.assertIn('--supervised-process-group', command)
                self.assertIs(kwargs.get('start_new_session'), True)
                output = command[command.index('--output') + 1]
                receipt = command[command.index('--receipt') + 1]
                process = real_popen([sys.executable, '-B', '-c', self.WORKER_PROGRAM,
                                      str(pidfile), self.CHILD_PROGRAM, str(ready), mode,
                                      str(source), output, receipt], **kwargs)
                processes.append(process)
                communicate = process.communicate

                def interrupted_communication(timeout):
                    metadata.update(self.wait_ready(pidfile))
                    self.assertEqual(metadata['group'], process.pid)
                    if mode == 'keyboard':
                        raise KeyboardInterrupt('synthetic interruption')
                    if mode == 'sigterm':
                        os.kill(os.getpid(), signal.SIGTERM)
                        raise AssertionError('SIGTERM did not interrupt supervised conversion')
                    return communicate(timeout=timeout)

                process.communicate = interrupted_communication
                return process

            def fail_term(group, signum):
                if signum == signal.SIGTERM:
                    raise PermissionError('synthetic TERM signal boundary')
                return real_killpg(group, signum)

            try:
                with contextlib.ExitStack() as stack:
                    stack.enter_context(patch.object(m.subprocess, 'Popen', side_effect=launch))
                    stack.enter_context(patch.object(m, '_stop_owned_group',
                        side_effect=lambda process: real_stop(process, timeout=0.1)))
                    if mode == 'term_error':
                        stack.enter_context(patch.object(m.os, 'killpg', side_effect=fail_term))
                    if mode == 'success':
                        result = m.ensure_valid_conversion(produced, source, timeout=2)
                        self.assertEqual(result['status'], 'verified')
                        m.validate_docx(produced)
                    else:
                        expected = {'timeout': TimeoutError, 'keyboard': KeyboardInterrupt,
                                    'sigterm': SystemExit, 'term_error': PermissionError}[mode]
                        with self.assertRaises(expected) as caught:
                            m.ensure_valid_conversion(produced, source, timeout=0.05)
                        if mode == 'sigterm':
                            self.assertEqual(caught.exception.code, 143)
                        self.assertEqual(produced.read_bytes(), previous)
                        self.assertEqual(produced.stat().st_mode & 0o777, 0o640)
                self.assertEqual(signal.getsignal(signal.SIGTERM), previous_handler)
                self.assertEqual(source.read_bytes(), b'Synthetic native source')
                self.assertEqual(sorted(path.name for path in root.iterdir()),
                                 ['child-ready', 'pids.json', 'produced.docx', 'source.doc'])
                self.assertTrue(processes)
                self.assertIsNotNone(processes[0].returncode)
                self.assertTrue(processes[0].stdout.closed)
                self.assertTrue(processes[0].stderr.closed)
                self.assert_not_running(metadata['leader'])
                self.assert_not_running(metadata['child'])
            finally:
                for process in processes:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait(timeout=5)
                    for stream in (process.stdout, process.stderr):
                        if stream is not None:
                            stream.close()
                signal.signal(signal.SIGTERM, previous_handler)

    def test_timeout_interrupt_and_sigterm_stop_the_owned_process_tree(self):
        for mode in ('timeout', 'keyboard', 'sigterm', 'term_error'):
            with self.subTest(mode=mode):
                self.conversion(mode)

    def test_success_also_stops_descendants_after_the_worker_exits(self):
        self.conversion('success')

    def test_independent_and_supervised_recovery_keep_their_session_contract(self):
        from types import ModuleType
        with patch.object(sys, 'path', [str(FORMAL / 'common'), *sys.path]):
            import native_word_conversion as m
        modules = {name: ModuleType(name) for name in ('uno', 'com', 'com.sun', 'com.sun.star', 'com.sun.star.beans')}
        modules['com.sun.star.beans'].PropertyValue = object
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / 'source.doc'
            source.write_bytes(b'Synthetic native source')
            for supervised in (False, True):
                with self.subTest(supervised=supervised), patch.dict(sys.modules, modules), \
                     patch.object(m.os, 'getpgrp', return_value=os.getpid()), \
                     patch.object(m.subprocess, 'Popen', side_effect=RuntimeError('synthetic startup boundary')) as launch:
                    with self.assertRaisesRegex(RuntimeError, 'synthetic startup boundary'):
                        m.recover_native_word(source, Path(temporary) / 'new.docx',
                                              supervised_process_group=supervised)
                    self.assertEqual(launch.call_args.kwargs['start_new_session'], not supervised)
            self.assertEqual([path.name for path in Path(temporary).iterdir()], ['source.doc'])

    def test_own_caller_group_is_never_signalled(self):
        from types import SimpleNamespace
        with patch.object(sys, 'path', [str(FORMAL / 'common'), *sys.path]):
            import native_word_conversion as m
        with patch.object(m.os, 'killpg') as send:
            with self.assertRaisesRegex(ValueError, 'caller process group'):
                m._signal_process(SimpleNamespace(pid=os.getpgrp()), signal.SIGKILL, process_group=True)
            send.assert_not_called()
        with patch.object(m.os, 'killpg') as send, \
             patch.object(m.os, 'getpgid', return_value=os.getpgrp()):
            with self.assertRaisesRegex(ValueError, 'separate process group'):
                m._signal_process(SimpleNamespace(pid=os.getpgrp() + 1000000),
                                  signal.SIGKILL, process_group=True)
            send.assert_not_called()


class CompoundFileHeaderContracts(unittest.TestCase):
    @staticmethod
    def compound_file(major):
        """루트 디렉터리와 FAT만 가진 작은 CFB를 형식에 맞게 만든다."""
        sector_shift = {3: 9, 4: 12}[major]
        sector_size = 1 << sector_shift
        header = bytearray(sector_size)
        header[:8] = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'
        struct.pack_into('<5H', header, 0x18, 0x003E, major, 0xFFFE, sector_shift, 6)
        struct.pack_into('<III', header, 0x28, 0 if major == 3 else 1, 1, 0)
        struct.pack_into('<5I', header, 0x38, 4096, 0xFFFFFFFE, 0, 0xFFFFFFFE, 0)
        struct.pack_into('<109I', header, 0x4C, 1, *([0xFFFFFFFF] * 108))
        directory = bytearray(sector_size)
        name = 'Root Entry\0'.encode('utf-16-le')
        directory[:len(name)] = name
        struct.pack_into('<HBBIII', directory, 0x40, len(name), 5, 1,
                         0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF)
        struct.pack_into('<IQ', directory, 0x74, 0xFFFFFFFE, 0)
        fat = struct.pack('<%dI' % (sector_size // 4),
                          0xFFFFFFFE, 0xFFFFFFFD, *([0xFFFFFFFF] * (sector_size // 4 - 2)))
        return bytes(header + directory + fat)

    def test_normal_512_and_4096_byte_sectors_are_read(self):
        with patch.object(sys, 'path', [str(FORMAL / 'common'), *sys.path]):
            import doc_fields
            import ole_cfb
        for major, sector_size in ((3, 512), (4, 4096)):
            with self.subTest(major=major):
                parsed = doc_fields._Cfb(self.compound_file(major))
                self.assertEqual((parsed.ss, parsed.mss, parsed.cutoff), (sector_size, 64, 4096))
                self.assertEqual(parsed.entries, {})
                self.assertEqual(parsed.ministream, b'')
                self.assertEqual(parsed.fat[:2], [0xFFFFFFFE, 0xFFFFFFFD])
                self.assertEqual(ole_cfb.streams(self.compound_file(major)), {})

    def test_short_or_invalid_header_is_rejected_before_sector_read(self):
        with patch.object(sys, 'path', [str(FORMAL / 'common'), *sys.path]):
            import doc_fields
            import ole_cfb
        valid = self.compound_file(3)
        cases = [('short-' + str(size), valid[:size]) for size in (0, 7, 8, 31, 511)]
        for field, offset, fmt, value in (
            ('version-2', 0x1A, '<H', 2),
            ('version-5', 0x1A, '<H', 5),
            ('version4-sector512', 0x1A, '<H', 4),
            ('version3-sector4096', 0x1E, '<H', 12),
            ('sector-shift31', 0x1E, '<H', 31),
            ('sector-shift65535', 0x1E, '<H', 65535),
            ('byte-order', 0x1C, '<H', 0xFEFF),
            ('mini-shift5', 0x20, '<H', 5),
            ('mini-shift31', 0x20, '<H', 31),
            ('mini-shift65535', 0x20, '<H', 65535),
            ('cutoff0', 0x38, '<I', 0),
            ('cutoff4095', 0x38, '<I', 4095),
        ):
            damaged = bytearray(valid)
            struct.pack_into(fmt, damaged, offset, value)
            cases.append((field, bytes(damaged)))
        damaged_signature = bytearray(valid)
        damaged_signature[0] = 0
        cases.append(('signature', bytes(damaged_signature)))
        for label, data in cases:
            with self.subTest(header=label):
                with patch.object(doc_fields._Cfb, '_sector', side_effect=AssertionError('sector read before header validation')) as sector:
                    with self.assertRaises(doc_fields.DocError):
                        doc_fields._Cfb(data)
                    sector.assert_not_called()
                with patch.object(ole_cfb.struct, 'unpack', side_effect=AssertionError('FAT read before header validation')) as fat:
                    with self.assertRaises(ole_cfb.CFBError):
                        ole_cfb.streams(data)
                    fat.assert_not_called()


class FigureMediaContracts(unittest.TestCase):
    def test_nested_media_name_collisions_keep_every_distinct_part(self):
        import docx_figures
        from types import SimpleNamespace
        names = ['/word/media/image1.png', '/media/image1.png',
                 '/word/media/media/image1.png', '/word/media/media/media/image1.png']
        paths = docx_figures._media_paths(names)
        self.assertEqual(len(set(paths.values())), len(names))
        self.assertEqual(paths, docx_figures._media_paths(reversed(names)))
        for name in names:
            if name.startswith('/word/media/'):
                self.assertEqual(paths[name], docx_figures.media_path(name))
        parts = {name: SimpleNamespace(partname=name, blob=name.encode()) for name in names}
        document = SimpleNamespace(part=SimpleNamespace(rels={name: SimpleNamespace(
            is_external=False, target_part=part) for name, part in parts.items()}))
        figures = [docx_figures.Figure(str(index), '', '', paths[name], (name,))
                   for index, name in enumerate(names)]
        exported = docx_figures.media_parts(document, figures)
        self.assertEqual({path: part.blob for path, part in exported.items()},
                         {paths[name]: name.encode() for name in names})


if __name__ == '__main__':
    # tempfile/shutil use fd-relative os.open during cleanup. Bind the audit
    # path to that directory rather than mistaking a temp "logs" for ROOT/logs.
    open_bases = []
    original_os_open = os.open
    def scoped_os_open(path, flags, mode=0o777, *, dir_fd=None):
        base = Path(os.readlink(f'/proc/self/fd/{dir_fd}')) if dir_fd is not None else Path.cwd()
        open_bases.append(base)
        try:
            return original_os_open(path, flags, mode, dir_fd=dir_fd)
        finally:
            open_bases.pop()
    os.open = scoped_os_open
    def synthetic_only(event, args):
        if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
            raw = Path(os.fsdecode(args[0]))
            base = open_bases[-1] if args[1] is None and open_bases else Path.cwd()
            path = raw if raw.is_absolute() else base / raw
            if any(path.is_relative_to(ROOT / prefix) for prefix in
                   ('logs', 'data/corpus', 'ontology/output', 'ontology/input')):
                raise RuntimeError(f'Synthetic suite refused original data access: {path}')
            mode = args[1] or ''
            if path.is_relative_to(ROOT) and any(c in str(mode) for c in 'wax+'):
                raise RuntimeError(f'Synthetic suite refused repository write: {path}')
        if event == 'subprocess.Popen':
            executable, argv = args[:2]
            allowed = (executable == sys.executable and isinstance(argv, (list, tuple)) and len(argv) == 11
                       and list(argv[:3]) == [sys.executable, '-B', '-c']
                       and argv[3] == NativeConversionProcessContracts.WORKER_PROGRAM
                       and argv[5] == NativeConversionProcessContracts.CHILD_PROGRAM
                       and argv[7] in ('timeout', 'keyboard', 'sigterm', 'term_error', 'success')
                       and all(Path(argv[index]).is_absolute() and Path(argv[index]).is_relative_to(Path(tempfile.gettempdir()))
                               for index in (4, 6, 8, 9, 10)))
            if not allowed:
                raise RuntimeError('Synthetic suite refused external execution')
        if event == 'socket.connect':
            raise RuntimeError('Synthetic suite refused external execution')
    sys.addaudithook(synthetic_only)
    unittest.main()
