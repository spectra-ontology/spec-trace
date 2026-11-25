#!/usr/bin/env python3
"""test_agenda_source_supplements.py — source-only report agenda closure fixtures.

Spec: RAN1 Phase-2 step1_parsing.md source-heading placement contract.
Ontology: meeting/agenda identity; independent registered and reported contexts.
Cycle: synthetic promoted XLSX/DOCX -> source ledger -> reference closure.
배경: fresh builds reconstruct report-only agendas before sealing source counts.
사용: python3 -B -m unittest discover -s scripts/tsg/RAN/formal/common -p test_agenda_source_supplements.py
LLM 호출: none. Every fixture is temporary; no DB, model or network calls.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parent))
import agenda_source_supplements as s
from role_agenda_evidence import evidence_document


class SourceAgendaClosure(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='spectra-agenda-fixture-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.inputs = self.root / 'ontology/input/tsg/RAN/formal/meetings/RAN1'
        (self.inputs / 'TDoc_List').mkdir(parents=True)
        (self.inputs / 'Final_Report').mkdir()

    def make_sources(self, meeting='115', *, tocs=((2, '5.1 Topic Alpha'),),
                     headings=((2, 'Topic Alpha'),), registered=('5.1.1',)):
        master = self.inputs / f'TDoc_List/TDoc_List_TSGR1_{meeting}.xlsx'
        book = Workbook()
        sheet = book.active
        sheet.title = 'TDoc_List'
        sheet.append(['Agenda item'])
        for number in registered:
            sheet.append([number])
        book.save(master)
        book.close()
        report = self.inputs / f'Final_Report/Final_Report_RAN1-{meeting}.docx'
        document = Document()
        for level in range(1, 6):
            document.styles.add_style(f'TOC {level}', WD_STYLE_TYPE.PARAGRAPH)
        for level, text in tocs:
            document.add_paragraph(text, style=f'TOC {level}')
        for level, text in headings:
            document.add_paragraph(text, style=f'Heading {level}')
        document.save(report)
        return master, report

    def prepare(self, meetings=('RAN1#115',)):
        return s.prepare_source_ledger(self.root, 'RAN1', meetings)

    def ledger(self):
        return json.loads(s.ledger_path(self.root, 'RAN1').read_text())

    def test_absent_ledger_builds_from_selected_raw_inputs_and_keeps_primary_bytes(self):
        master, report = self.make_sources()
        original = {p: p.read_bytes() for p in (master, report)}
        self.assertFalse(s.ledger_path(self.root, 'RAN1').exists())
        self.assertEqual(s.validated_records(self.root, 'RAN1'), [])
        result = self.prepare()
        self.assertTrue(result['created'])
        self.assertEqual(set(result['inputs']), {p.relative_to(self.root).as_posix() for p in original})
        self.assertEqual({p: p.read_bytes() for p in original}, original)
        records = s.validated_records(self.root, 'RAN1')
        self.assertEqual([r['id'] for r in records], ['tdoc:agenda/115-5.1'])
        self.assertFalse((self.root / 'ontology/output').exists())
        references = {('115', '5.1.1'): {'@id': 'tdoc:agenda/115-5.1.1'}}
        self.assertIn(('115', '5.1'), s.supplement_agenda_items(self.root, 'RAN1', references))
        self.assertEqual(list(references), [('115', '5.1.1')])

    def test_selected_scope_does_not_read_unselected_docx_bytes(self):
        self.make_sources()
        _, unselected = self.make_sources('116')
        unselected.write_bytes(b'not a DOCX; outside the selected source scope')
        result = self.prepare()
        self.assertEqual(self.ledger()['selectedMeetings'], ['115'])
        self.assertTrue(all('116' not in name for name in result['inputs']))
        self.assertEqual(unselected.read_bytes(), b'not a DOCX; outside the selected source scope')

    def test_repeated_meeting_rows_reuse_the_pure_canonical_identity(self):
        s._meeting.cache_clear()
        self.addCleanup(s._meeting.cache_clear)
        loader = s.importlib.util.spec_from_file_location
        with patch.object(s.importlib.util, 'spec_from_file_location', wraps=loader) as load:
            self.assertEqual([s._meeting('RAN1#121-bis-e') for _ in range(50)], ['121bis'] * 50)
        self.assertEqual(load.call_count, 1)
        self.assertEqual(s._meeting('RAN1#121'), '121')

    def test_exact_child_toc_parent_closes_the_generated_assertion_target(self):
        master, report = self.make_sources(tocs=((2, '5.1 Topic Alpha'),),
            headings=((1, 'Maintenance'), (2, 'Topic Alpha')), registered=('5.1',))
        document = Document(report)
        role = document.add_paragraph('R1-1234567\tFL summary of maintenance\tModerator (Fixture)')
        document.paragraphs[-2]._p.addprevious(role._p)
        document.save(report)
        primary = master.read_bytes()
        tools = s._placement_tools()
        sections, paragraphs, toc = tools.source_sections(report, include_toc=True)
        index = next(i for i, paragraph in enumerate(paragraphs)
                     if s.docx_text.final_text(paragraph).startswith('R1-1234567'))
        parsed = {'meeting_id': 'RAN1#115', 'docx_path': report.relative_to(self.root).as_posix(),
                  'fl_summaries': [{'tdoc_number': 'R1-1234567', 'paragraph_index': index,
                                    'agenda_item': '5'}]}
        placements = tools.role_placement_records(parsed, sections, paragraphs, toc,
                                                  hashlib.sha256(report.read_bytes()).hexdigest())
        self.assertEqual(placements[0]['method'],
                         'exact_child_toc_common_parent_within_source_heading_boundary')
        generated = evidence_document(placements, {})
        self.prepare()
        records = s.validated_records(self.root, 'RAN1')
        self.assertEqual([row['id'] for row in records], ['tdoc:agenda/115-5'])
        references = s.supplement_agenda_items(self.root, 'RAN1', {
            ('115', '5.1'): {'@id': 'tdoc:agenda/115-5.1'}})
        targets = {row['@id'] for row in references.values()}
        assertions = [row for row in generated['@graph'] if row['@type'] == 'EvidenceAssertion']
        self.assertEqual(len(assertions), 1)
        self.assertTrue(all(row['evidenceStatus'] == 'source_verified'
                            and row['assertionObject'] in targets for row in assertions))
        self.assertEqual(master.read_bytes(), primary)
        for role in ('direct_child_heading_binding_parent', 'numbered_child_table_of_contents_entry'):
            altered = self.ledger()
            altered['records'][0]['evidence'] = [item for item in altered['records'][0]['evidence']
                                                if item['role'] != role]
            with self.subTest(missing=role), self.assertRaisesRegex(ValueError, 'not bound'):
                s.validated_records(self.root, 'RAN1', document=altered)

    def test_child_toc_after_peer_boundary_does_not_supply_the_previous_parent(self):
        self.make_sources(tocs=((2, '5.1 Topic Alpha'),),
            headings=((1, 'Maintenance'), (1, '7. Other boundary'), (2, 'Topic Alpha')),
            registered=('5.1', '7'))
        self.prepare()
        self.assertEqual(self.ledger()['records'], [])

    def test_children_from_different_toc_parents_do_not_supply_a_parent(self):
        self.make_sources(tocs=((2, '5.1 Topic Alpha'), (2, '6.1 Topic Beta')),
            headings=((1, 'Maintenance'), (2, 'Topic Alpha'), (2, 'Topic Beta')),
            registered=('5.1', '6.1'))
        self.prepare()
        self.assertEqual(self.ledger()['records'], [])

    def test_bis_and_e_identity_remain_distinct_from_regular_meeting(self):
        self.make_sources('115-bis-e')
        self.make_sources('115')
        self.prepare(('RAN1#115-bis-e',))
        self.assertEqual([r['id'] for r in self.ledger()['records']], ['tdoc:agenda/115bis-5.1'])
        self.assertEqual(s.validated_records(self.root, 'RAN1', {'RAN1#115'}), [])

    def test_explicit_number_without_toc_is_verified_but_fuzzy_heading_is_pending(self):
        self.make_sources(tocs=(), headings=((2, '5.1 Topic Alpha'),))
        self.prepare()
        self.assertEqual(len(self.ledger()['records']), 1)
        self.assertEqual(self.ledger()['records'][0]['evidence'][0]['quote'], '5.1 Topic Alpha')
        with tempfile.TemporaryDirectory(prefix='spectra-pending-fixture-') as directory:
            other = Path(directory)
            relative = self.inputs.relative_to(self.root)
            with patch.object(self, 'root', other), patch.object(self, 'inputs', other / relative):
                (self.inputs / 'TDoc_List').mkdir(parents=True)
                (self.inputs / 'Final_Report').mkdir()
                self.make_sources(headings=((2, 'Topic Alphx'),))
                self.prepare()
                self.assertEqual(self.ledger()['records'], [])

    def test_unrelated_toc_title_or_wrong_level_cannot_be_laundered_as_verified(self):
        self.make_sources()
        self.prepare()
        valid = self.ledger()
        report = self.inputs / 'Final_Report/Final_Report_RAN1-115.docx'
        for headings in [((2, 'Entirely unrelated Heading Beta'),), ((3, 'Topic Alpha'),)]:
            with self.subTest(headings=headings):
                self.make_sources(headings=headings)
                forged = deepcopy(valid)
                record = forged['records'][0]
                record['source']['sha256'] = hashlib.sha256(report.read_bytes()).hexdigest()
                forged['sourceInputs']={name:hashlib.sha256((self.root/name).read_bytes()).hexdigest()
                                        for name in forged['sourceInputs']}
                record['tdocList']['sha256']=forged['sourceInputs'][record['tdocList']['path']]
                record['agendaDescription'] = headings[0][1]
                for evidence in record['evidence']:
                    if evidence['role'] == 'source_heading':
                        evidence['quote'] = headings[0][1]
                with self.assertRaisesRegex(ValueError, 'not bound'):
                    s.validated_records(self.root, 'RAN1', document=forged)

    def test_same_title_under_other_parent_does_not_prove_wrong_agenda(self):
        self.make_sources(tocs=((1, '5. Parent Alpha'), (2, '5.1 Topic Alpha'),
                                (1, '6. Parent Beta'), (2, '6.1 Topic Alpha')),
                          headings=((1, '6. Parent Beta'), (2, 'Topic Alpha')))
        self.prepare()
        valid = self.ledger()
        row = next(r for r in valid['records'] if r['agendaNumber'] == '6.1')
        forged = deepcopy(valid)
        forged['records'] = [deepcopy(row)]
        wrong = forged['records'][0]
        wrong.update(id='tdoc:agenda/115-5.1', agendaNumber='5.1')
        for evidence in wrong['evidence']:
            if evidence['role'] == 'numbered_table_of_contents_entry':
                evidence.update(paragraphIndex=1, quote='5.1 Topic Alpha')
        with self.assertRaisesRegex(ValueError, 'not bound'):
            s.validated_records(self.root, 'RAN1', document=forged)

    def test_quote_and_source_mutations_are_rejected_without_overwriting_ledger(self):
        _, report = self.make_sources()
        self.prepare()
        ledger = s.ledger_path(self.root, 'RAN1')
        original = ledger.read_bytes()
        document = self.ledger()
        document['records'][0]['evidence'][0]['quote'] = 'invented quote'
        with self.assertRaises(ValueError):
            s.validated_records(self.root, 'RAN1', document=document)
        report.write_bytes(report.read_bytes() + b'drift')
        with self.assertRaisesRegex(ValueError, 'SHA drift'):
            self.prepare()
        self.assertEqual(ledger.read_bytes(), original)

    def test_duplicate_records_and_conflicting_source_files_are_rejected(self):
        _, report = self.make_sources()
        self.prepare()
        document = self.ledger()
        document['records'].append(deepcopy(document['records'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            s.validated_records(self.root, 'RAN1', document=document)
        duplicate = report.with_name('Final_Report_RAN1-115_e.docx')
        duplicate.write_bytes(report.read_bytes() + b'different source bytes')
        with self.assertRaisesRegex(ValueError, 'Conflicting promoted'):
            self.prepare()

    def test_identical_canonical_source_duplicates_are_pinned_and_folded(self):
        _, report = self.make_sources()
        duplicate = report.with_name('Final_Report_RAN1-115_e.docx')
        shutil.copy2(report, duplicate)
        result = self.prepare()
        self.assertEqual(len(result['inputs']), 3)
        self.assertEqual(len(self.ledger()['records']), 1)

    def test_regular_and_electronic_masters_use_registered_union_and_pin_both(self):
        master,report=self.make_sources('100',tocs=((2,'5.1 Topic Alpha'),(2,'5.2 Topic Beta')),
            headings=((2,'Topic Alpha'),(2,'Topic Beta')),registered=('5.1.1',))
        electronic=master.with_name('TDoc_List_TSGR1_100_e.xlsx')
        book=Workbook();sheet=book.active;sheet.title='TDoc_List'
        sheet.append(['Agenda item']);sheet.append(['5.1']);book.save(electronic);book.close()
        before={path:path.read_bytes() for path in (master,electronic)}
        result=self.prepare(('RAN1#100',))
        self.assertEqual([row['id'] for row in self.ledger()['records']],['tdoc:agenda/100-5.2'])
        self.assertEqual(len(result['inputs']),3)
        self.assertEqual({path:path.read_bytes() for path in before},before)
        forged=deepcopy(self.ledger())
        wrong=forged['records'][0]
        section,receipt=next((section,receipt) for section,receipt in
            s._report_receipts(report,s._placement_tools()) if section['agenda_number']=='5.1')
        wrong.update(id='tdoc:agenda/100-5.1',agendaNumber='5.1',
                     agendaDescription=section['title'],evidence=receipt['evidence'])
        with self.assertRaisesRegex(ValueError,'selected source XLSX edition'):
            s.validated_records(self.root,'RAN1',document=forged)
        original=s.ledger_path(self.root,'RAN1').read_bytes()
        electronic.write_bytes(electronic.read_bytes()+b'input drift')
        with self.assertRaises(ValueError): self.prepare(('RAN1#100',))
        self.assertEqual(s.ledger_path(self.root,'RAN1').read_bytes(),original)

    def test_resume_preserves_existing_bytes_and_rejects_changed_scope(self):
        self.make_sources()
        first = self.prepare()
        ledger = s.ledger_path(self.root, 'RAN1')
        original = ledger.read_bytes()
        second = self.prepare()
        self.assertFalse(second['created'])
        self.assertEqual(first['sha256'], second['sha256'])
        self.assertEqual(ledger.read_bytes(), original)
        self.make_sources('116')
        with self.assertRaisesRegex(ValueError, 'refusing replacement'):
            self.prepare(('RAN1#115', 'RAN1#116'))
        self.assertEqual(ledger.read_bytes(), original)

    def test_valid_manual_ledger_is_reused_without_reformatting(self):
        self.make_sources()
        self.prepare()
        ledger = s.ledger_path(self.root, 'RAN1')
        manual = self.ledger()
        manual.pop('selectedMeetings')
        manual.pop('sourceInputs')
        original = json.dumps(manual, ensure_ascii=False, indent=4).encode()
        ledger.write_bytes(original)
        self.assertFalse(self.prepare()['created'])
        self.assertEqual(ledger.read_bytes(), original)

    def test_legacy_minimal_evidence_keeps_parent_binding_and_byte_preserving_reuse(self):
        self.make_sources(tocs=((1, '5. Parent'), (2, '5.1 Topic Alpha')),
                          headings=((1, '5. Parent'), (2, 'Topic Alpha')),
                          registered=('5', '5.1.1'))
        self.prepare()
        ledger = s.ledger_path(self.root, 'RAN1')
        manual = self.ledger()
        manual.pop('selectedMeetings')
        manual.pop('sourceInputs')
        for record in manual['records']:
            record['evidence'] = [e for e in reversed(record['evidence']) if e['role'] != 'enclosing_heading']
        raw = json.dumps(manual).encode()
        ledger.write_bytes(raw)
        self.assertEqual(len(s.validated_records(self.root, 'RAN1')), 1)
        self.assertFalse(self.prepare()['created'])
        self.assertEqual(ledger.read_bytes(), raw)

    def test_source_drift_after_publish_removes_only_the_owned_new_ledger(self):
        _, report = self.make_sources()
        link = s.os.link
        def publish_then_drift(source, target):
            link(source, target)
            report.write_bytes(report.read_bytes() + b'drift after publication')
        with patch.object(s.os, 'link', side_effect=publish_then_drift):
            with self.assertRaisesRegex(ValueError, 'changed during'):
                self.prepare()
        self.assertFalse(s.ledger_path(self.root, 'RAN1').exists())
        self.assertEqual(list(self.inputs.glob('.agenda-source-*')), [])
        self.assertTrue(report.exists())

    def test_concurrent_foreign_ledger_is_preserved(self):
        self.make_sources()
        foreign = b'{"schemaVersion":"foreign","records":[]}'
        def other_writer(source, target):
            Path(target).write_bytes(foreign)
            raise FileExistsError()
        with patch.object(s.os, 'link', side_effect=other_writer):
            with self.assertRaises(ValueError):
                self.prepare()
        self.assertEqual(s.ledger_path(self.root, 'RAN1').read_bytes(), foreign)
        self.assertEqual(list(self.inputs.glob('.agenda-source-*')), [])

    def test_replacement_after_publication_is_detected_and_preserved(self):
        self.make_sources()
        link = s.os.link
        foreign = b'{"owned":"another writer"}'
        def publish_then_replace(source, target):
            link(source, target)
            Path(target).unlink()
            Path(target).write_bytes(foreign)
        with patch.object(s.os, 'link', side_effect=publish_then_replace):
            with self.assertRaisesRegex(ValueError, 'changed during publication'):
                self.prepare()
        self.assertEqual(s.ledger_path(self.root, 'RAN1').read_bytes(), foreign)

    def test_failed_publication_preserves_foreign_bytes_and_original_error(self):
        self.make_sources()
        ledger = s.ledger_path(self.root, 'RAN1')
        selected_sources = s._selected_sources
        actual_read = Path.read_bytes
        for mode in ('own', 'inplace', 'replacement', 'deleted', 'unreadable'):
            with self.subTest(mode=mode):
                ledger.unlink(missing_ok=True)
                original_error = RuntimeError('selected input fence failed')
                expected = []
                foreign = b'foreign in-place agenda ledger'

                def selected_after_link(*args):
                    if ledger.exists():
                        encoded = actual_read(ledger)
                        expected.append(encoded)
                        if mode == 'inplace':
                            ledger.write_bytes(foreign)
                        elif mode == 'replacement':
                            ledger.unlink()
                            ledger.write_bytes(encoded)
                        elif mode == 'deleted':
                            ledger.unlink()
                        raise original_error
                    return selected_sources(*args)

                def read_bytes(path):
                    if mode == 'unreadable' and path == ledger:
                        raise PermissionError('concurrent ledger cannot be read')
                    return actual_read(path)

                with patch.object(s, '_selected_sources', side_effect=selected_after_link), \
                     patch.object(Path, 'read_bytes', read_bytes):
                    with self.assertRaises(RuntimeError) as caught:
                        self.prepare()
                self.assertIs(original_error, caught.exception)
                self.assertEqual(len(expected), 1)
                if mode in ('own', 'deleted'):
                    self.assertFalse(ledger.exists())
                else:
                    self.assertEqual(foreign if mode == 'inplace' else expected[0],
                                     ledger.read_bytes())
                self.assertEqual(list(self.inputs.glob('.agenda-source-*')), [])

    def test_inplace_change_after_publication_is_detected_and_preserved(self):
        self.make_sources()
        link = s.os.link
        foreign = b'foreign in-place source agenda ledger'

        def publish_then_change(source, target):
            link(source, target)
            Path(target).write_bytes(foreign)

        with patch.object(s.os, 'link', side_effect=publish_then_change):
            with self.assertRaisesRegex(ValueError, 'changed during publication'):
                self.prepare()
        self.assertEqual(s.ledger_path(self.root, 'RAN1').read_bytes(), foreign)
        self.assertEqual(list(self.inputs.glob('.agenda-source-*')), [])

    def test_selected_source_addition_before_publication_is_fenced(self):
        _, report = self.make_sources()
        build = s._build_source_document
        def build_then_add(*args):
            document = build(*args)
            shutil.copy2(report, report.with_name('Final_Report_RAN1-115_e.docx'))
            return document
        with patch.object(s, '_build_source_document', side_effect=build_then_add):
            with self.assertRaisesRegex(ValueError, 'changed during closure'):
                self.prepare()
        self.assertFalse(s.ledger_path(self.root, 'RAN1').exists())

    def test_source_symlink_and_missing_selected_workbook_are_refused(self):
        _, report = self.make_sources()
        real = report.with_suffix('.source')
        report.rename(real)
        report.symlink_to(real)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.prepare()
        report.unlink()
        with self.assertRaisesRegex(ValueError, 'no promoted Tdoc-list'):
            self.prepare(('RAN1#116',))

    def test_unreceipted_source_is_refused_before_publication(self):
        master, report = self.make_sources()
        expected = {master.relative_to(self.root).as_posix(): hashlib.sha256(master.read_bytes()).hexdigest()}
        with self.assertRaisesRegex(ValueError, 'promotion receipt'):
            s.prepare_source_ledger(self.root, 'RAN1', ['RAN1#115'], expected_inputs=expected)
        self.assertFalse(s.ledger_path(self.root, 'RAN1').exists())
        expected[report.relative_to(self.root).as_posix()] = hashlib.sha256(report.read_bytes()).hexdigest()
        self.assertTrue(s.prepare_source_ledger(self.root, 'RAN1', ['RAN1#115'], expected_inputs=expected)['created'])

    def test_other_working_group_selection_is_refused_and_other_wgs_are_unchanged(self):
        self.make_sources()
        with self.assertRaisesRegex(ValueError, 'another working group'):
            self.prepare(('RAN2#115',))
        self.assertIsNone(s.prepare_source_ledger(self.root, 'RAN2', ['RAN2#115'])['ledger'])


if __name__ == '__main__':
    unittest.main()
