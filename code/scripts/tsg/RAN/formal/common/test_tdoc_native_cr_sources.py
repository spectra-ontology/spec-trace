#!/usr/bin/env python3
"""Verify native CR source ownership and exact Annex-row binding.

Spec: retained assigned CR forms outside the historical pack population.
Ontology: source-body identity is distinct from classification and approval.
Cycle: synthetic native DOCX + exact Annex row → validated body-only input.
배경: missing native bodies need independently checked source ownership.
사용: python3 -B -m unittest discover -s scripts/tsg/RAN/formal/common -p test_tdoc_native_cr_sources.py.
LLM 호출: 없음. 임시 DOCX·XLSX·ZIP·검증 입력만 사용하며 개인 자료는 읽지 않는다.
"""
from contextlib import ExitStack
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / 'scripts/common'))
from common import review_artifacts
from tdoc_native_cr_sources import ledger_path, validate_native_source, validated_native_sources


class NativeCRSources(unittest.TestCase):
    def setUp(self):
        from docx import Document
        import hashlib
        import openpyxl
        import zipfile
        import cr_form
        import docx_text
        import decision_disposition as disposition
        import document_decision_source as decision_source
        import tdoc_native_cr_sources as native
        from reconcile_tdoc_source_metadata import full_points
        self.full_points = full_points
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / '.git').mkdir()
        self.all_rows = []
        self.cover_paths = {}
        variants = [(1, {}), (2, {}), (3, {'release': 'REL-13'}),
            (4, {'release': 'Rel- 13'}), (5, {'revision': '<Rev#>'}),
            (6, {'revision': '2-'}), (7, {'spec_prefix': 'TR '}),
            (8, {'help_markers': True}),
            *[(number, {'glyph': True}) for number in range(9, 13)],
            (13, {'header': True}), (14, {'literal': True})]
        for number, options in variants:
            target = f'R2-{990000 + number}'
            cover_path = self.root / 'synthetic' / (target + '.docx')
            cover_path.parent.mkdir(parents=True, exist_ok=True)
            cover = Document()
            own = ('draft' + target.split('-')[1] if options.get('literal')
                   else 'Tdoc ⌘ ' + target if options.get('glyph') else target)
            cover.add_paragraph('Synthetic meeting cover' if options.get('header') else own)
            if options.get('header'):
                cover.sections[0].header.paragraphs[0].text = target
            if options.get('help_markers'):
                cover.add_paragraph('Use the pop-up text over the ⌘ symbols for this synthetic form.')
            cover.add_paragraph('CHANGE REQUEST')
            mark = '⌘ ' if options.get('help_markers') else ''
            release = options.get('release', 'Rel-17')
            cells = [
                [mark + options.get('spec_prefix', '') + '38.331', 'CR', str(7000 + number),
                 'rev', options.get('revision', '3'), 'Current version:', '17.1.0'],
                ['Release:', mark + release], ['Title:', mark + 'Synthetic proposal ' + str(number)],
                ['Category:', mark + 'F'], ['Source to WG:', mark + 'Example Company'],
                ['Work item code:', mark + 'SYNTHETIC_WI'],
                ['Reason for change:', 'Synthetic reason'], ['Summary of change:', 'Synthetic summary'],
                ['Consequences if not approved:', 'Synthetic consequence'], ['Clauses affected:', '1'],
                ['Synthetic field 1', 'Synthetic value 1'], ['Synthetic field 2', 'Synthetic value 2']]
            table = cover.add_table(rows=len(cells), cols=7)
            for row, values in zip(table.rows, cells):
                for cell, value in zip(row.cells, values):
                    cell.text = value
            cover.save(cover_path)
            self.cover_paths[target] = cover_path
            texts, digest, _ = disposition.source_blocks(str(cover_path))
            evidence = [dict(path=cover_path.relative_to(self.root).as_posix(), sha256=digest,
                locator=f'word/document.xml accepted body blocks [{index},{index + 1})', quote=text)
                for index, text in enumerate(texts)]
            if options.get('header'):
                evidence.append(dict(path=cover_path.relative_to(self.root).as_posix(), sha256=digest,
                    locator='word/header1.xml accepted paragraphs [0,1)', quote=target))
            metadata = {'Title': 'Synthetic proposal ' + str(number), 'Release': release,
                'Category': 'F', 'Source to WG': 'Example Company', 'Work item code': 'SYNTHETIC_WI'}
            row = {'target': target, 'meetingId': 'RAN2#999',
                'coverIdentity': {'path': cover_path.relative_to(self.root).as_posix(),
                    'sha256': digest, 'metadata': metadata},
                'review': {'actualDocumentEvidence': evidence}}
            if options.get('literal'):
                master = self.root / 'synthetic' / 'master.xlsx'
                book = openpyxl.Workbook(); sheet = book.active; sheet.title = 'Master'
                sheet.append(['TDoc', 'Title']); sheet.append([target, metadata['Title']])
                book.save(master); book.close()
                archive = self.root / 'synthetic' / 'original.zip'
                with zipfile.ZipFile(archive, 'w') as zipped:
                    zipped.writestr(cover_path.name, cover_path.read_bytes())
                row['officialSourceArchive'] = dict(path=archive.relative_to(self.root).as_posix(),
                    sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                    members=[dict(name=cover_path.name, sha256=digest)])
                row['sourceIdentityReview'] = dict(targetTdocNumber=target,
                    classification='literal_own_cover_label_format_bound_by_original_archive_and_master',
                    actualDocumentEvidence=evidence, literalOwnHeader=own,
                    registeredMasterEvidence=[dict(path=master.relative_to(self.root).as_posix(),
                        sha256=hashlib.sha256(master.read_bytes()).hexdigest(), sheet='Master', row=2,
                        cells=[target, metadata['Title']])])
            self.all_rows.append(row)
        report_path = self.root / 'synthetic' / 'report.docx'
        report = Document(); report.add_paragraph('Annex A: List of agreed CRs')
        headers = ['Spec', 'Title', 'CR', 'Rev', 'Rel', 'RAN2 TDoc', 'RAN2 status']
        table = report.add_table(rows=len(self.all_rows) + 1, cols=len(headers))
        for cell, value in zip(table.rows[0].cells, headers): cell.text = value
        for number, (row, table_row) in enumerate(zip(self.all_rows, table.rows[1:]), 1):
            for cell, value in zip(table_row.cells, ['38.331', row['coverIdentity']['metadata']['Title'],
                    str(7000 + number), '3', 'Rel-17', row['target'], 'agreed']): cell.text = value
        report.save(report_path)
        events, _ = decision_source.annex_cr_table_events(
            {'meeting_id': 'RAN2#999', 'docx_path': report_path.relative_to(self.root).as_posix()}, self.root)
        by_target = {event['subject_tdoc']: event for event in events}
        self.assertEqual(set(by_target), {row['target'] for row in self.all_rows})
        for row in self.all_rows:
            event = by_target[row['target']]
            checked = decision_source.annex_source_evidence(event, self.root)
            row['reportEntry'] = dict(path=checked['path'], sourceSHA256=checked['sha256'],
                meeting='RAN2#999', locator=checked['locator'], quote=checked['quote'], sourceEvent=event)
            if 'sourceIdentityReview' in row:
                row['sourceIdentityReview']['decisionEvidence'] = checked
        ledger = ledger_path(self.root, 'RAN2'); ledger.parent.mkdir(parents=True)
        ledger.write_text(json.dumps({'schema': 1, 'wg': 'RAN2', 'records': self.all_rows}))
        self.rows = self.all_rows[:2]
        self.addCleanup(disposition.source_blocks.cache_clear)
        self.addCleanup(decision_source._ANNEX_CACHE.clear)
        self.contexts = ExitStack()
        self.addCleanup(self.contexts.close)
        self.contexts.enter_context(patch.object(native, '_VALIDATED_CACHE', {}))
        read_bytes, read_text = Path.read_bytes, Path.read_text
        def only_temporary(method):
            def read(path, *args, **kwargs):
                self.assertTrue(path.resolve().is_relative_to(self.root), str(path))
                return method(path, *args, **kwargs)
            return read
        self.contexts.enter_context(patch.object(Path, 'read_bytes', only_temporary(read_bytes)))
        self.contexts.enter_context(patch.object(Path, 'read_text', only_temporary(read_text)))

    def test_original_sources_support_body_fields_without_approval(self):
        self.assertEqual(len(self.rows), 2)
        for source in self.rows:
            row = validate_native_source(self.root, source)
            self.assertEqual(row['nativeSourceKind'], 'retained_assigned_cr_form')
            self.assertEqual({d['field'] for d in row['deltas']},
                {'modifies', 'tdoc:crNumber', 'tdoc:crRevision', 'targetRelease'})
            self.assertNotIn('isAgreement', row)

    def test_other_tdoc_cannot_borrow_retained_form(self):
        row = deepcopy(self.rows[0]); row['target'] = 'R2-999999'
        with self.assertRaisesRegex(ValueError, 'own exact header'):
            validate_native_source(self.root, row)

    def test_original_source_quote_is_required(self):
        row = deepcopy(self.rows[0]); row['review']['actualDocumentEvidence'][0]['quote'] += ' changed'
        with self.assertRaisesRegex(ValueError, 'quote or locator'):
            validate_native_source(self.root, row)

    def test_body_metadata_cannot_come_from_another_cover(self):
        row = deepcopy(self.rows[0]); row['coverIdentity']['metadata']['Release'] = 'Rel-99'
        with self.assertRaisesRegex(ValueError, 'metadata differs'):
            validate_native_source(self.root, row)

    def test_adjacent_annex_row_cannot_supply_disposition_context(self):
        row = deepcopy(self.rows[0])
        row['reportEntry']['sourceEvent']['document_entry']['annexTable']['acceptedRow'] += 1
        with self.assertRaises(ValueError):
            validate_native_source(self.root, row)

    def test_source_bytes_are_fenced(self):
        row = deepcopy(self.rows[0]); row['coverIdentity']['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            validate_native_source(self.root, row)

    def test_duplicate_target_rejected_before_source_projection(self):
        path = ledger_path(self.root, 'RAN2')
        path.write_text(json.dumps({'schema': 1, 'wg': 'RAN2', 'records': [self.rows[0], self.rows[0]]}))
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            validated_native_sources(self.root, 'RAN2')

    def test_body_only_projection_does_not_read_registered_payloads(self):
        client = Mock()
        self.assertEqual(self.full_points(client, 'ran2_tdoc_chunks', set()), [])
        client.scroll.assert_not_called()

    def test_cached_evidence_still_fences_original_bytes(self):
        import tdoc_native_cr_sources as native
        path = self.root / 'cache-ledger.json'
        path.write_text(json.dumps({'schema': 1, 'wg': 'RAN2', 'records': [self.rows[0]]}))
        with patch.object(native, 'ledger_path', return_value=path), \
             patch.object(native, '_VALIDATED_CACHE', {}), \
             patch.object(native, 'validate_native_source', wraps=validate_native_source) as validate:
            first = validated_native_sources(self.root, 'RAN2')
            self.assertEqual(validated_native_sources(self.root, 'RAN2'), first)
            self.assertEqual(validate.call_count, 1)
            with patch.object(native, 'checked_path', side_effect=ValueError('changed original bytes')):
                with self.assertRaisesRegex(ValueError, 'changed original bytes'):
                    validated_native_sources(self.root, 'RAN2')

    def test_actual_release_variants_and_unknown_revision_remain_explicit(self):
        selected = {'R2-990003', 'R2-990004', 'R2-990005'}
        rows = {r['target']: r for r in validated_native_sources(self.root, 'RAN2', selected_targets=selected)}
        self.assertEqual(set(rows), selected)
        self.assertEqual(rows['R2-990003']['coverIdentity']['metadata']['Release'], 'REL-13')
        self.assertEqual(rows['R2-990004']['coverIdentity']['metadata']['Release'], 'Rel- 13')
        for target in selected - {'R2-990005'}:
            self.assertEqual(rows[target]['nativeSourceIdentity']['release'], 'Rel-13')
        unspecified = rows['R2-990005']
        self.assertEqual(unspecified['nativeSourceIdentity']['revisionRaw'], '<Rev#>')
        self.assertIsNone(unspecified['nativeSourceIdentity']['crRevision'])
        self.assertEqual(unspecified['nativeSourceIdentity']['revisionEvidenceStatus'], 'unspecified_placeholder')
        self.assertEqual(next(d['sourceBackedValue'] for d in unspecified['deltas']
                              if d['field'] == 'tdoc:crRevision'), '')

    def test_unfilled_form_fields_do_not_become_neighboring_labels(self):
        import cr_form
        import docx_text
        from docx import Document
        for category in ('', 'F'):
            with self.subTest(category=category):
                path = self.root / ('unfilled-' + (category or 'empty') + '.docx')
                doc = Document()
                table = doc.add_table(rows=12, cols=7)
                values = [['38.331', 'CR', '7100', 'rev', '', 'Current version:', '17.1.0'],
                    ['Title:', 'Synthetic proposal'], ['Category:', category], ['Release:', 'Rel-17'],
                    ['Work item code:', ''], ['Date:', ''], ['Source to WG:', 'Example Company'],
                    ['Reason for change:', 'Synthetic reason'], ['Summary of change:', 'Synthetic summary']]
                for row, cells in zip(table.rows, values):
                    for cell, value in zip(row.cells, cells): cell.text = value
                doc.save(path)
                actual = cr_form.form_fields(docx_text.open_document(path))
                self.assertFalse(actual.get('work_item'))
                self.assertNotIn(actual.get('category'), {'Release:', 'Date:'})
                self.assertEqual(actual.get('category') or '', category)

    def test_actual_ambiguous_revision_is_retained_without_number_inference(self):
        row = next(row for row in self.all_rows if row['target'] == 'R2-990006')
        actual = validate_native_source(self.root, row)
        self.assertEqual(actual['nativeSourceIdentity']['revisionRaw'], '2-')
        self.assertIsNone(actual['nativeSourceIdentity']['crRevision'])
        self.assertEqual(actual['nativeSourceIdentity']['revisionEvidenceStatus'], 'ambiguous_literal')

    def test_observed_tr_prefix_and_help_markers_preserve_literal_source(self):
        rows = {row['target']: row for row in self.all_rows}
        for target in ('R2-990007', 'R2-990008'):
            with self.subTest(target=target):
                actual = validate_native_source(self.root, rows[target])
                self.assertEqual(actual['review'], rows[target]['review'])
                self.assertTrue(int(actual['nativeSourceIdentity']['crNumber']))

    def test_heading_glyph_is_not_a_structural_form_marker(self):
        rows = validated_native_sources(self.root, 'RAN2', selected_targets={f'R2-{990000 + n}' for n in range(9, 13)})
        self.assertEqual(len(rows), 4)
        self.assertTrue(all('Tdoc ⌘ R2-' in '\n'.join(e['quote'] for e in r['review']['actualDocumentEvidence']) for r in rows))

    def test_original_word_headers_and_registered_literal_own_formats(self):
        selected = {'R2-990013', 'R2-990014'}
        rows = validated_native_sources(self.root, 'RAN2', selected_targets=selected)
        self.assertEqual({r['target'] for r in rows}, selected)
        header = next(r for r in rows if r['target'] == 'R2-990013')
        changed = deepcopy(header)
        next(e for e in changed['review']['actualDocumentEvidence'] if e['locator'].startswith('word/header'))['quote'] += ' changed'
        with self.assertRaisesRegex(ValueError, 'Word header quote'):
            validate_native_source(self.root, changed)


if __name__ == '__main__':
    unittest.main()
