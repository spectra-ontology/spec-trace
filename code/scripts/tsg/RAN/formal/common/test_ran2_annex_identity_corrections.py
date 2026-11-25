#!/usr/bin/env python3
"""합성 CR 표지와 정확한 부록 행을 사용해 신원 교정 계약을 검증한다.

Spec: Phase-1 CR identity; independently bound accepted Annex source rows.
Ontology: CR number/revision and exact evidence ownership across document views.
Cycle: synthetic source ledger → accepted DOCX verification → narrow overlay.
배경: 원문과 보고서 행이 직접 뒷받침하는 메타데이터만 교정한다.
사용: python3 -B -m unittest discover -s scripts/tsg/RAN/formal/common -p test_ran2_annex_identity_corrections.py.
LLM 호출: 없음. 임시 입력만 사용하며 모델·서비스·네트워크에 접근하지 않는다.
"""
from contextlib import ExitStack
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tdoc_source_identity_corrections import validate_correction, validated_corrections


class AnnexIdentityCorrections(unittest.TestCase):
    def setUp(self):
        from docx import Document
        import decision_disposition as d
        import document_decision_source as source
        import tdoc_source_identity_corrections as corrections
        from reconcile_tdoc_source_metadata import load_module, phase4_parser_path
        from tdoc_classification_views import source_body_rows, source_fields
        self.parser = load_module(phase4_parser_path('RAN2'))
        self.source_body_rows = source_body_rows
        self.source_fields = source_fields
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / '.git').mkdir()
        self.targets = {f'R2-99000{number}' for number in range(1, 6)}
        self.rows = []
        covers = {}
        for number, target in enumerate(sorted(self.targets), 1):
            cover_path = self.root / 'synthetic' / (target + '.docx')
            cover_path.parent.mkdir(parents=True, exist_ok=True)
            cover = Document()
            cover.add_paragraph('3GPP TSG-RAN2 Meeting #999 ' + target)
            cells = [
                ['38.331', 'CR', str(1230 + number), 'rev', '3', 'Current version:', '17.1.0'],
                ['Release:', 'Rel-17'], ['Title:', 'Synthetic proposal ' + str(number)],
                ['Category:', 'F'], ['Source to WG:', 'Example Company'],
                ['Work item code:', 'SYNTHETIC_WI'], ['Reason for change:', 'Synthetic reason'],
                ['Summary of change:', 'Synthetic summary'],
                ['Consequences if not approved:', 'Synthetic consequence'],
                ['Clauses affected:', '1'], ['Synthetic field 1', 'Synthetic value 1'],
                ['Synthetic field 2', 'Synthetic value 2'],
            ]
            table = cover.add_table(rows=len(cells), cols=7)
            for row, values in zip(table.rows, cells):
                for cell, value in zip(row.cells, values):
                    cell.text = value
            cover.save(cover_path)
            texts, sha, _ = d.source_blocks(str(cover_path))
            covers[target] = [dict(path=str(cover_path.relative_to(self.root)), sha256=sha,
                locator=f'word/document.xml accepted body blocks [{index},{index + 1})',
                quote=texts[index]) for index in range(len(texts))]
        report_path = self.root / 'synthetic' / 'RAN2-report.docx'
        report = Document()
        report.add_paragraph('Annex A: List of agreed CRs')
        headers = ['Spec', 'Title', 'CR', 'Rev', 'Rel', 'RAN2 TDoc', 'RAN2 status']
        table = report.add_table(rows=6, cols=len(headers))
        for cell, value in zip(table.rows[0].cells, headers):
            cell.text = value
        for number, (target, row) in enumerate(zip(sorted(self.targets), table.rows[1:]), 1):
            for cell, value in zip(row.cells, ['38.331', 'Synthetic proposal ' + str(number),
                    str(1230 + number), '3', 'Rel-17', target, 'agreed']):
                cell.text = value
        report.save(report_path)
        events, _ = source.annex_cr_table_events(
            {'meeting_id': 'RAN2#999', 'docx_path': str(report_path.relative_to(self.root))}, self.root)
        self.assertEqual({event['subject_tdoc'] for event in events}, self.targets)
        for event in events:
            target = event['subject_tdoc']
            checked = source.annex_source_evidence(event, self.root)
            fields = event['document_entry']['sourceFields']
            self.rows.append({'target': target, 'meetingId': 'RAN2#999',
                'scope': 'synthetic_annex_identity', 'recoverNativeBody': True,
                'review': {'actualDocumentEvidence': covers[target]},
                'reportEntry': dict(path=checked['path'], sourceSHA256=checked['sha256'],
                    meeting='RAN2#999', locator=checked['locator'], quote=checked['quote'],
                    sourceEvent=event),
                'deltas': [
                    dict(field='modifies', before='tdoc:spec/38_000', sourceBackedValue='tdoc:spec/38_331'),
                    dict(field='tdoc:crNumber', before='0000', sourceBackedValue=fields['crNumber']),
                    dict(field='tdoc:crRevision', before='0', sourceBackedValue='3'),
                    dict(field='targetRelease', before='tdoc:release/Rel_16',
                         sourceBackedValue='tdoc:release/Rel_17')],
            })
        path = corrections.ledger_path(self.root, 'RAN2')
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({'schema': 1, 'wg': 'RAN2', 'records': self.rows}))
        self.addCleanup(d.source_blocks.cache_clear)
        self.addCleanup(source._ANNEX_CACHE.clear)
        read_bytes, read_text = Path.read_bytes, Path.read_text
        self.input_reads = []
        def checked_read(method):
            def read(path, *args, **kwargs):
                self.assertTrue(path.resolve().is_relative_to(self.root), str(path))
                self.input_reads.append(path)
                return method(path, *args, **kwargs)
            return read
        self.contexts = ExitStack()
        self.addCleanup(self.contexts.close)
        self.contexts.enter_context(patch.object(Path, 'read_bytes', checked_read(read_bytes)))
        self.contexts.enter_context(patch.object(Path, 'read_text', checked_read(read_text)))

    def test_all_five_retained_covers_and_exact_source_rows(self):
        rows = validated_corrections(self.root, 'RAN2')
        self.assertEqual(len(rows), 5)
        self.assertEqual({row['target'] for row in rows}, self.targets)
        self.assertTrue(self.input_reads)

    def test_adjacent_row_cannot_supply_identity(self):
        row = deepcopy(self.rows[0])
        row['reportEntry']['sourceEvent']['document_entry']['annexTable']['acceptedRow'] += 1
        with self.assertRaises(ValueError):
            validate_correction(self.root, row)

    def test_unbound_proposed_number_is_rejected(self):
        row = deepcopy(self.rows[0])
        row['deltas'][0]['sourceBackedValue'] = '9999'
        with self.assertRaises(ValueError):
            validate_correction(self.root, row)

    def test_modified_report_revision_is_rejected(self):
        row = deepcopy(self.rows[0])
        row['reportEntry']['sourceEvent']['document_entry']['sourceFields']['crRevision'] = '99'
        with self.assertRaises(ValueError):
            validate_correction(self.root, row)

    def test_evidence_quote_is_exact_and_not_only_a_filename(self):
        row = deepcopy(self.rows[0])
        row['review']['actualDocumentEvidence'][0]['quote'] += ' fabricated'
        with self.assertRaises(ValueError):
            validate_correction(self.root, row)
        changed = deepcopy(self.rows[0])
        changed['review']['actualDocumentEvidence'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'SHA changed'):
            validate_correction(self.root, changed)
        changed = deepcopy(self.rows[0])
        changed['reportEntry']['sourceSHA256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'SHA changed'):
            validate_correction(self.root, changed)

    def test_different_document_cannot_borrow_source(self):
        row = deepcopy(self.rows[0])
        row['target'] = 'R2-999999'
        with self.assertRaises(ValueError):
            validate_correction(self.root, row)

    def test_native_meeting_sources_have_no_invented_pack(self):
        parser = self.parser
        selected = set(sorted(self.targets)[:2])
        rows = self.source_body_rows(self.root, 'RAN2', selected_targets=selected)
        self.assertEqual({row['target'] for row in rows}, selected)
        with patch.object(parser, 'PROJECT_ROOT', self.root), \
                patch.object(parser.cr_other_wg, 'pack_id', side_effect=AssertionError('Native source is not in a CR pack')):
            for row in rows:
                fields = self.source_fields(row)
                actual = parser.parse_cr_document(self.root / row['coverIdentity']['path'],
                    fields['release'], source_pack_id='')
                self.assertEqual(actual.errors, [])
                self.assertEqual(actual.tdoc_number, row['target'])
                self.assertEqual(actual.spec_number, fields['spec_number'])
                self.assertEqual(actual.cr_pack_id, '')


if __name__ == '__main__':
    unittest.main()
