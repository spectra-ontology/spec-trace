#!/usr/bin/env python3
"""test_document_decision_storage.py — 문서처분의 신원·원본 자료 충돌 회귀.

Spec: docs/tsg/build/standards/decision_disposition_contract.md.
Ontology: canonical source-event identities and qualified target assertions.
Cycle: adversarial identity fixtures → guarded serializer → exact assertions.
배경: 전자회의 IRI와 CR번호·규격·release 불일치를 승인으로 승격하지 않는다.
사용: python3 -m unittest discover -s scripts/tsg/RAN/formal/common -p test_document_decision_storage.py.
LLM 호출: 없음.
"""
import json
from pathlib import Path
import tempfile
import unittest
import copy
import hashlib
import io
import zipfile
import xml.etree.ElementTree as ET
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

import document_decision_storage as storage


class CanonicalIdentity(unittest.TestCase):

    @staticmethod
    def write_synthetic_docx(path, paragraphs, table=None):
        namespace = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        word = '{' + namespace + '}'
        document = ET.Element(word + 'document')
        body = ET.SubElement(document, word + 'body')
        def paragraph(parent, text):
            node = ET.SubElement(parent, word + 'p')
            run = ET.SubElement(node, word + 'r')
            ET.SubElement(run, word + 't').text = text
        for text in paragraphs:
            paragraph(body, text)
        if table is not None:
            node = ET.SubElement(body, word + 'tbl')
            for cells in table:
                row = ET.SubElement(node, word + 'tr')
                for text in cells:
                    paragraph(ET.SubElement(row, word + 'tc'), text)
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('word/document.xml', ET.tostring(document, encoding='utf-8'))

    @staticmethod
    def write_synthetic_master(path, rows):
        import openpyxl
        path.parent.mkdir(parents=True, exist_ok=True)
        book = openpyxl.Workbook()
        try:
            sheet = book.active
            sheet.title = 'Master'
            for row in rows:
                sheet.append(row)
            book.save(path)
        finally:
            book.close()

    @staticmethod
    def synthetic_receipt(root, path):
        return {'path': str(path.relative_to(root)),
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

    @contextmanager
    def fixture_only_reads(self, root):
        """합성 입력만 읽으며 개발 PC의 원문·검수 로그에 접근하지 않는지 확인한다."""
        read_bytes, read_text = Path.read_bytes, Path.read_text
        reads = []
        def checked(method):
            def read(path, *args, **kwargs):
                self.assertTrue(path.resolve().is_relative_to(root.resolve()), str(path))
                reads.append(path)
                return method(path, *args, **kwargs)
            return read
        with patch.object(Path, 'read_bytes', checked(read_bytes)), \
                patch.object(Path, 'read_text', checked(read_text)):
            yield
        self.assertTrue(reads)

    def synthetic_own_header_review(self, root, target, *, cover_number=None, revision_correction=False):
        cover_number = cover_number or target
        cover = root / 'synthetic' / (target + '.docx')
        quote = cover_number + '\n| 38.331 | CR | 1234 | rev | 1 | Current version: | 17.1.0 |'
        self.write_synthetic_docx(cover, quote.split('\n'))
        actual = dict(self.synthetic_receipt(root, cover),
                      locator='word/document.xml accepted body blocks [0,2)', quote=quote)
        own = [''] * 24
        own[0], own[19], own[22], own[23] = target, '38.331', '1234', '3'
        rows = [own]
        classification = 'cover_revision_label_correction_explicit_in_same_annex_row'
        if not revision_correction:
            classification = 'own_cover_tdoc_header_typo_bound_by_original_archive_and_master'
            own[17] = target.split('-')[0] + '-' + str(int(target.split('-')[1]) + 10)
            correction = [''] * 24
            correction[0], correction[7], correction[16] = own[17], 'TDoc number correction', target
            rows.append(correction)
        master_path = root / 'synthetic' / (target + '.xlsx')
        self.write_synthetic_master(master_path, [['field' + str(i) for i in range(24)]] + rows)
        master = dict(self.synthetic_receipt(root, master_path), rows=[
            {'sheet': 'Master', 'row': index + 2, 'cells': row} for index, row in enumerate(rows)])
        archive_path = root / 'synthetic' / (target + '.zip')
        with zipfile.ZipFile(archive_path, 'w') as archive:
            archive.writestr('cover.docx', cover.read_bytes())
        archive = dict(self.synthetic_receipt(root, archive_path),
                       members=[{'name': 'cover.docx', 'sha256': actual['sha256']}])
        review = {'targetTdocNumber': target, 'classification': classification,
                  'actualDocumentEvidence': [actual],
                  'sourceIdentityAdjudication': {'master': master, 'archive': archive}}
        if revision_correction:
            review['sourceIdentityAdjudication'].update(coverRevision=1, reportRevision=3)
            review['sourceAnnexFields'] = {'spec': '38.331', 'crNumber': '1234', 'crRevision': 3}
            review['decisionEvidence'] = {
                'decisionText': 'CR rev3 is correct but CR rev1 used in CR coversheet'}
        return review

    def synthetic_alias_events(self, root, wg, expected, *, annex=False):
        import decision_disposition as d
        import document_decision_source as source
        (root / '.git').mkdir()
        self.addCleanup(d.source_blocks.cache_clear)
        self.addCleanup(source._EVENT_CACHE.clear)
        self.addCleanup(source._ANNEX_CACHE.clear)
        for cached in (storage._target_aliases, storage._tdoc_index,
                       storage._phase1, storage._endpoint_index):
            self.addCleanup(cached.cache_clear)
        phase1 = root / f'ontology/output/tsg/RAN/formal/instances/phase-1/{wg}'
        phase1.mkdir(parents=True)
        (phase1 / 'tdocs.jsonld').write_text(json.dumps({'@graph': [
            {'@id': 'tdoc:' + resolved, 'tdoc:tdocNumber': resolved, 'tdoc:type': 'CR',
             'tdoc:crNumber': '1234', 'tdoc:modifies': 'tdoc:spec/38_331',
             'tdoc:crRevision': 3, 'tdoc:targetRelease': 'tdoc:release/Rel_17'}
            for resolved in expected.values()]}))
        meeting = wg + '#999'
        (phase1 / 'meetings.jsonld').write_text(json.dumps({'@graph': [
            {'@id': 'tdoc:meeting/' + wg + '_999', 'tdoc:meetingNumber': meeting,
             'tdoc:canonicalMeetingNumber': meeting}]}))
        report_path = root / 'synthetic' / (wg + '-report.docx')
        if annex:
            header = ['Spec', 'Title', 'CR', 'Rev', 'Rel', 'RAN2 TDoc', 'RAN2 status']
            rows = [header] + [['38.331', 'Synthetic proposal', '1234', '3', 'Rel-17',
                                original, 'agreed'] for original in expected]
            self.write_synthetic_docx(report_path, ['Annex A: List of agreed CRs'], table=rows)
        else:
            paragraphs = [text for original in expected for text in (
                original + ' Synthetic proposal', 'Type: CR', 'Decision: The document was agreed.')]
            self.write_synthetic_docx(report_path, paragraphs)
        report = {'meeting_id': meeting, 'docx_path': str(report_path.relative_to(root))}
        events, _ = source.document_decisions(report, root)
        aliases = []
        for event in events:
            original = event['subject_tdoc']
            resolved = expected[original]
            cover = root / 'synthetic' / (resolved + '.docx')
            cover_text = resolved + '\n| 38.331 | CR | 1234 | rev | 3 | Current version: | 17.1.0 |'
            self.write_synthetic_docx(cover, cover_text.split('\n'))
            proof = dict(self.synthetic_receipt(root, cover),
                         locator='word/document.xml accepted body blocks [0,2)', quote=cover_text)
            master_path = root / 'synthetic' / (resolved + '.xlsx')
            fields = {'TDoc': resolved, 'Spec': '38.331', 'CR': '1234', 'Revision': '3'}
            self.write_synthetic_master(master_path, [list(fields), list(fields.values())])
            master = dict(self.synthetic_receipt(root, master_path),
                          sheet='Master', row=2, fields=fields)
            archives = []
            for index in range(3 if annex else 1):
                archive_path = root / 'synthetic' / (resolved + '-' + str(index) + '.zip')
                member = resolved + '.docx'
                with zipfile.ZipFile(archive_path, 'w') as archive:
                    archive.writestr(member, cover.read_bytes())
                archives.append(dict(self.synthetic_receipt(root, archive_path),
                                     members=[{'name': member, 'sha256': proof['sha256']}]))
            decision = (source.annex_source_evidence(event, root) if annex else
                        dict(self.synthetic_receipt(root, report_path),
                             locator=storage.document_evidence_locator(event), quote=event['content']))
            aliases.append({'meetingId': meeting, 'sourceTdocNumber': original,
                            'resolvedTdocNumber': resolved, 'decisionEvidence': decision,
                            'actualDocumentEvidence': [proof], 'masterEvidence': master,
                            'rawZipEvidence': archives})
        alias_path = root / f'ontology/input/tsg/RAN/formal/meetings/{wg}/document_decision_target_aliases.json'
        alias_path.parent.mkdir(parents=True)
        alias_path.write_text(json.dumps({'aliases': aliases}))
        return events

    def event(self):
        return {'meeting_id': 'RAN5#91', 'decision_id': 'DOC-91-R5-213430-b10920',
            'subject_tdoc': 'R5-213430', 'referenced_tdocs': ['R5-213430'],
            'agenda_item': '7.1', 'sequence': 10920, 'content': 'actual full entry',
            'document_entry': {'formalDocumentDecisionParagraphs': 1,
                'decisionText': 'Decision: The document was agreed.', 'sourcePath': 'source.docx',
                'documentType': 'CR', 'typeBlock': 1, 'headerText': 'R5-213430 title'}}

    def test_electronic_meeting_keeps_actual_phase1_iri(self):
        indexes = {'meetings': {('RAN5#91',): ['tdoc:meeting/RAN5_91-e']},
                   'agenda_items': {('91', '7.1'): ['tdoc:agenda/91-7.1']}}
        with patch.object(storage, 'endpoint_index', side_effect=lambda wg, name, keys, root: indexes[name]), \
                patch.object(storage, 'assess_document_identity', side_effect=lambda event, target, code, assessment, root: (code, assessment)):
            node = storage.document_resolution_node(self.event())
        self.assertEqual(node['madeAt'], 'tdoc:meeting/RAN5_91-e')
        self.assertEqual(node['resolutionBelongsTo'], 'tdoc:agenda/91-7.1')
        self.assertEqual(node['content'], 'actual full entry')
        self.assertIn('Agreement', node['@type'])

    def test_cancelled_meeting_and_its_replacement_resolve_by_exact_meeting_number(self):
        indexes = {('meetings', ('canonicalMeetingNumber',)): {('RAN5#91',): ['tdoc:meeting/RAN5_91', 'tdoc:meeting/RAN5_91-e']},
                   ('meetings', ('meetingNumber',)): {('RAN5#91',): ['tdoc:meeting/RAN5_91']},
                   ('agenda_items', ('meetingNumber', 'agendaNumber')): {('91', '7.1'): ['tdoc:agenda/91-7.1']}}
        with patch.object(storage, 'endpoint_index', side_effect=lambda wg, name, keys, root: indexes[(name, keys)]), \
                patch.object(storage, 'assess_document_identity', side_effect=lambda event, target, code, assessment, root: (code, assessment)):
            node = storage.document_resolution_node(self.event())
        self.assertEqual(node['madeAt'], 'tdoc:meeting/RAN5_91')

    def test_ambiguous_meeting_fails_before_serialization(self):
        with patch.object(storage, 'endpoint_index', return_value={('RAN5#91',): ['one', 'two']}):
            with self.assertRaisesRegex(ValueError, 'exactly one'):
                storage.document_resolution_node(self.event())

    def assess(self, metadata, actual, document_type='CR'):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'ontology/output/tsg/RAN/formal/instances/phase-1/RAN5/tdocs.jsonld'
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({'@graph': [actual]}))
            with patch('decision_disposition.source_blocks', return_value=(['header', metadata], 'sha', [])):
                event = self.event()
                event['document_entry']['documentType'] = document_type
                return storage.assess_document_identity(event, 'R5-213430', 'agreed', {'rule': 'source_rule'}, root)

    def target(self):
        return {'@id': 'tdoc:R5-213430', 'tdoc:tdocNumber': 'R5-213430',
            'tdoc:type': 'CR', 'tdoc:crNumber': '0055',
            'tdoc:modifies': 'tdoc:spec/38_521-3', 'tdoc:targetRelease': 'tdoc:release/Rel_17'}

    def test_matching_descriptor_retains_literal_approval(self):
        code, method = self.assess('Type: CR\n38.521-3 v17.1.0 CR-0055 Cat:F (Rel-17)', self.target())
        self.assertEqual(code, 'agreed')
        self.assertTrue(method['targetIdentity']['targetPresent'])

    def test_annex_identity_uses_checked_cells_and_preserves_zero_revision(self):
        actual = dict(self.target(), **{'tdoc:crRevision': 0})
        event = self.event()
        event['document_entry'].update(sourceKind='annex_cr_table_row',
            sourceFields={'spec': '38.521-3', 'crNumber': '0055',
                          'crRevision': 0, 'release': 'Rel-17'})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'ontology/output/tsg/RAN/formal/instances/phase-1/RAN5/tdocs.jsonld'
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({'@graph': [actual]}))
            with patch('decision_disposition.source_blocks', return_value=(['unrelated Rel-12 title'], 'sha', [])), \
                    patch.object(storage, 'document_identity_review', return_value={
                        'identityStatus': 'same_document_source_verified'}):
                code, method = storage.assess_document_identity(event, 'R5-213430', 'agreed', {}, root)
        self.assertEqual(code, 'agreed')
        self.assertEqual(method['targetIdentity']['sourceCrRevision'], 0)
        self.assertEqual(method['targetIdentity']['sourceRelease'], 'Rel-17')
        self.assertEqual(method['identityReview']['identityStatus'], 'same_document_source_verified')

    def annex_assess(self, status):
        event = self.event()
        event['document_entry'].update(sourceKind='annex_cr_table_row',
            sourceFields={'spec': '38.521-3', 'crNumber': '0055', 'crRevision': '0', 'release': 'Rel-17'})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'ontology/output/tsg/RAN/formal/instances/phase-1/RAN5/tdocs.jsonld'
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({'@graph': [self.target()]}))
            with patch('decision_disposition.source_blocks', return_value=(['title'], 'sha', [])), \
                    patch.object(storage, 'document_identity_review', return_value={'identityStatus': status}):
                return storage.assess_document_identity(event, 'R5-213430', 'agreed', {}, root)

    def test_reviewed_own_cover_binds_the_revision_absent_from_registration(self):
        code, method = self.annex_assess('same_document_source_verified')
        self.assertEqual(code, 'agreed')
        self.assertEqual(method['targetIdentity']['crRevisionBoundBy'], 'own_cover_identity_review')
        self.assertNotIn('conflicts', method['targetIdentity'])

    def test_metadata_discrepancy_review_leaves_unregistered_revision_unbound(self):
        code, method = self.annex_assess('same_document_metadata_discrepancy')
        self.assertEqual(code, 'ambiguous')
        self.assertIn('source_CR_revision_not_bound_to_target', method['targetIdentity']['conflicts'])

    def own_cover(self, number, revision, release, fields, scope='agreed'):
        quote = f'38.521-3 | CR | {number} | rev | {revision} | Current version: | 17.1.0\nRelease: | {release}'
        storage.check_annex_own_cr_fields(
            {'document_entry': {'sourceFields': fields, 'annexTable': {'tableScope': scope}}},
            {'identityStatus': 'same_document_source_verified', 'actualDocumentEvidence': [{'quote': quote}]})

    def test_own_cover_notation_variants_equal_the_report_row(self):
        row = {'spec': '38.521-3', 'crNumber': '0055', 'crRevision': '0', 'release': 'Rel-17'}
        self.own_cover('0055', '-', 'Rel-17', row)
        self.own_cover('<0055>', '0', 'Rel-17', row)
        self.own_cover('CR0055', '0', 'Rel-17 Use one of the following releases: Rel-8 (Release 8)', row)
        self.own_cover('---', '-', 'Rel-17', dict(row, crNumber=None), scope='endorsed')

    def test_own_cover_differences_are_rejected(self):
        row = {'spec': '38.521-3', 'crNumber': '0055', 'crRevision': '1', 'release': 'Rel-17'}
        for number, revision, release, fields, scope in [
                ('0055', '-', 'Rel-17', row, 'agreed'),
                ('0055', '2', 'Rel-17', row, 'agreed'),
                ('0056', '1', 'Rel-17', row, 'agreed'),
                ('0055', '1', 'Rel-16', row, 'agreed'),
                ('---', '1', 'Rel-17', row, 'endorsed'),
                ('---', '1', 'Rel-17', dict(row, crNumber=None), 'agreed')]:
            with self.assertRaises(ValueError):
                self.own_cover(number, revision, release, fields, scope)

    def test_annex_matching_registration_needs_actual_own_source_review(self):
        actual = dict(self.target(), **{'tdoc:crRevision': 0})
        event = self.event()
        event['document_entry'].update(sourceKind='annex_cr_table_row',
            sourceFields={'spec': '38.521-3', 'crNumber': '0055',
                          'crRevision': 0, 'release': 'Rel-17'})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'ontology/output/tsg/RAN/formal/instances/phase-1/RAN5/tdocs.jsonld'
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({'@graph': [actual]}))
            with patch('decision_disposition.source_blocks', return_value=([], 'sha', [])):
                code, method = storage.assess_document_identity(event, 'R5-213430', 'agreed', {}, root)
        self.assertEqual(code, 'ambiguous')
        self.assertEqual(method['sourceDispositionCode'], 'agreed')
        self.assertEqual(method['rule'], 'annex_target_identity_requires_own_source_review')

    def test_normal_own_source_review_cannot_use_filename_for_wrong_cover_id(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / '.git').mkdir()
            path = root / 'review.json'
            review = {'meetingId': 'RAN5#91', 'targetTdocNumber': 'R5-213430',
                'identityStatus': 'same_document_source_verified',
                'decisionEvidence': {'locator': 'checked row'},
                'actualDocumentEvidence': [{'path': 'R5-213430.docx',
                                             'quote': 'R5-213431 another own cover'}]}
            path.write_text(json.dumps({'reviews': [review]}))
            stat = path.stat()
            with self.assertRaisesRegex(ValueError, 'exact document number in source text'):
                storage._document_identity_reviews(str(path), stat.st_mtime_ns, stat.st_size)

    def test_actual_header_typo_adjudication_checks_original_rows_and_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reviews = [self.synthetic_own_header_review(root, target, cover_number=wrong)
                       for target, wrong in [('R2-990001', 'R2-9990001'),
                                             ('R2-990002', 'R2-9990002')]]
            self.assertEqual({row['targetTdocNumber'] for row in reviews},
                             {'R2-990001', 'R2-990002'})
            with self.fixture_only_reads(root):
                for review in reviews:
                    storage.check_own_header_adjudication(review, root)
                    changed = copy.deepcopy(review)
                    changed['sourceIdentityAdjudication']['master']['rows'][0]['cells'][0] = 'R2-0000000'
                    with self.assertRaisesRegex(ValueError, 'exact master row changed'):
                        storage.check_own_header_adjudication(changed, root)
                    changed = copy.deepcopy(review)
                    changed['sourceIdentityAdjudication']['archive']['sha256'] = '0' * 64
                    with self.assertRaisesRegex(ValueError, 'original archive changed'):
                        storage.check_own_header_adjudication(changed, root)

    def test_actual_same_annex_row_explicitly_corrects_its_cover_revision_label(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            review = self.synthetic_own_header_review(root, 'R2-990003', revision_correction=True)
            with self.fixture_only_reads(root):
                storage.check_own_header_adjudication(review, root)
                changed = copy.deepcopy(review)
                changed['decisionEvidence']['decisionText'] = 'A different row merely says agreed.'
                with self.assertRaisesRegex(ValueError, 'exact same-row and master support'):
                    storage.check_own_header_adjudication(changed, root)

    def test_normal_annex_approval_is_bound_to_actual_cover_revision(self):
        event = self.event()
        event['document_entry']['sourceFields'] = {'spec':'38.521-3', 'crNumber':'55',
                                                   'crRevision':1, 'release':'Rel-17'}
        review = {'identityStatus':'same_document_source_verified', 'actualDocumentEvidence':[
            {'quote':'| 38.521-3 | CR | 0055 | rev | 1 | Current version: | 17.1.0 |\n| Release: | Rel-17 |'}]}
        storage.check_annex_own_cr_fields(event, review)
        for observed in ('| TS38.521-3 | CR | 0055 |', '| TS 38.521-3 | CR | CR0055 |'):
            changed = copy.deepcopy(review)
            changed['actualDocumentEvidence'][0]['quote'] = review['actualDocumentEvidence'][0]['quote'].replace('| 38.521-3 | CR | 0055 |', observed)
            storage.check_annex_own_cr_fields(event, changed)
        for observed in ('Release 17', '<Release> Rel-17', '<Release>Rel-17', 'R17', '17'):
            changed = copy.deepcopy(review)
            changed['actualDocumentEvidence'][0]['quote'] = review['actualDocumentEvidence'][0]['quote'].replace('Rel-17', observed)
            storage.check_annex_own_cr_fields(event, changed)
        for field, value in [('spec', '38.521-2'), ('crNumber', '56'), ('crRevision', 2), ('release', 'Rel-18')]:
            changed = copy.deepcopy(event)
            changed['document_entry']['sourceFields'][field] = value
            with self.assertRaisesRegex(ValueError, 'Normal Annex actual CR'):
                storage.check_annex_own_cr_fields(changed, review)
        initial = copy.deepcopy(event)
        initial['document_entry']['sourceFields']['crRevision'] = 0
        # 빈 칸과 양식 자리표시는 개정을 정하지 않는다. 표지의 '-'는 최초본 표기라서 행의 0과 같다.
        for raw_revision in ('', '<Rev#>'):
            changed = copy.deepcopy(review)
            changed['actualDocumentEvidence'][0]['quote'] = review['actualDocumentEvidence'][0]['quote'].replace('| rev | 1 |', f'| rev | {raw_revision} |')
            with self.assertRaisesRegex(ValueError, 'actual CR revision'):
                storage.check_annex_own_cr_fields(initial, changed)
        changed = copy.deepcopy(review)
        changed['actualDocumentEvidence'][0]['quote'] = review['actualDocumentEvidence'][0]['quote'].replace('| rev | 1 |', '| rev | - |')
        storage.check_annex_own_cr_fields(initial, changed)
        with self.assertRaisesRegex(ValueError, 'actual CR revision'):
            storage.check_annex_own_cr_fields(event, changed)

    def test_unassigned_draft_is_bound_to_explicit_in_principle_row(self):
        event = self.event()
        event['document_entry'].update(sourceFields={'spec': '36.331', 'crNumber': None,
                                                     'crRevision': None, 'release': 'Rel-13'},
                                       annexTable={'tableScope': 'in_principle'})
        for token in ('', '-', 'xxx', 'xxxx', 'CRNum', 'Num', 'draftCR', 'DRAFT'):
            review = {'identityStatus': 'same_document_source_verified', 'actualDocumentEvidence': [
                {'quote': f'| 36.331 | CR | {token} | rev | - | Current version: | 13.3.0 |\n| Release: | Rel-13 |'}]}
            storage.check_annex_own_cr_fields(event, review)
            changed = copy.deepcopy(event)
            changed['document_entry']['sourceFields']['crNumber'] = '1234'
            with self.assertRaisesRegex(ValueError, 'explicitly unassigned draft scope'):
                storage.check_annex_own_cr_fields(changed, review)
            changed = copy.deepcopy(event)
            changed['document_entry']['annexTable']['tableScope'] = 'agreed'
            with self.assertRaisesRegex(ValueError, 'explicitly unassigned draft scope'):
                storage.check_annex_own_cr_fields(changed, review)

    def test_header_number_evidence_uses_accepted_text_and_exact_part(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.docx'
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('word/header1.xml', '<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p/><w:p><w:del><w:r><w:delText>R2-1700000</w:delText></w:r></w:del><w:ins><w:r><w:t>R2-1701757</w:t></w:r></w:ins></w:p></w:hdr>')
            evidence = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'locator': 'word/header1.xml accepted paragraphs [1,2)', 'quote': 'R2-1701757'}
            storage.check_word_header_evidence(path, [evidence])
            for changed in (dict(evidence, quote='R2-1700000'),
                            dict(evidence, locator='word/header1.xml accepted paragraphs [0,1)'),
                            dict(evidence, sha256='0' * 64)):
                with self.assertRaises(ValueError):
                    storage.check_word_header_evidence(path, [changed])

    def test_annex_revision_conflict_cannot_approve_current_target(self):
        actual = dict(self.target(), **{'tdoc:crRevision': 2})
        event = self.event()
        event['document_entry'].update(sourceKind='annex_cr_table_row',
            sourceFields={'spec': '38.521-3', 'crNumber': '0055',
                          'crRevision': '1', 'release': 'Rel-17'})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'ontology/output/tsg/RAN/formal/instances/phase-1/RAN5/tdocs.jsonld'
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({'@graph': [actual]}))
            with patch('decision_disposition.source_blocks', return_value=([], 'sha', [])):
                code, method = storage.assess_document_identity(event, 'R5-213430', 'agreed', {}, root)
        self.assertEqual(code, 'ambiguous')
        self.assertEqual(method['sourceDispositionCode'], 'agreed')
        self.assertIn('source_CR_revision_differs_from_target', method['targetIdentity']['conflicts'])

    def test_annex_review_is_bound_to_exact_row_and_checked_row_quote(self):
        event = self.event()
        event['body_blocks'] = [10, 14]
        event['document_entry'].update(sourceKind='annex_cr_table_row',
            annexTable={'tableBlock': 11, 'acceptedRow': 2})
        locator = storage.document_evidence_locator(event)
        checked = {'path': 'source.docx', 'sha256': 'checked_source_sha',
                   'locator': locator, 'quote': 'header and this row only'}
        review = {'identityStatus': 'identity_conflict', 'decisionEvidence': checked,
                  'actualDocumentEvidence': []}
        key = (event['meeting_id'], event['subject_tdoc'], locator)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'ontology/input/tsg/RAN/formal/meetings/RAN5/document_decision_identity_reviews.json'
            path.parent.mkdir(parents=True)
            path.write_text('{}')
            with patch.object(storage, '_document_identity_reviews', return_value={key: review}), \
                    patch('document_decision_source.annex_source_evidence', return_value=checked) as verify:
                self.assertEqual(storage.document_identity_review(event, event['subject_tdoc'], root), review)
                verify.assert_called_once_with(event, root)
                neighbor = copy.deepcopy(event)
                neighbor['document_entry']['annexTable']['acceptedRow'] = 3
                self.assertIsNone(storage.document_identity_review(neighbor, event['subject_tdoc'], root))
                changed = dict(checked, quote='quote from another row')
                with patch('document_decision_source.annex_source_evidence', return_value=changed):
                    with self.assertRaisesRegex(ValueError, 'report source changed'):
                        storage.document_identity_review(event, event['subject_tdoc'], root)

    def test_annex_alias_is_bound_to_exact_row_without_rewriting_source_number(self):
        event = self.event()
        event['body_blocks'] = [10, 14]
        event['document_entry'].update(sourceKind='annex_cr_table_row',
            annexTable={'tableBlock': 11, 'acceptedRow': 2})
        locator = storage.document_evidence_locator(event)
        checked = {'path': 'source.docx', 'sha256': 'checked_source_sha',
                   'locator': locator, 'quote': 'source number and this row only'}
        alias = {'resolvedTdocNumber': 'R5-213431', 'decisionEvidence': checked}
        key = (event['meeting_id'], event['subject_tdoc'], locator)
        original = copy.deepcopy(event)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'ontology/input/tsg/RAN/formal/meetings/RAN5/document_decision_target_aliases.json'
            path.parent.mkdir(parents=True)
            path.write_text('{}')
            with patch.object(storage, '_target_aliases', return_value={key: alias}), \
                    patch('document_decision_source.annex_source_evidence', return_value=checked):
                self.assertEqual(storage.resolve_document_target(event, event['subject_tdoc'], root),
                                 ('R5-213431', alias))
                neighbor = copy.deepcopy(event)
                neighbor['document_entry']['annexTable']['acceptedRow'] = 3
                self.assertEqual(storage.resolve_document_target(neighbor, event['subject_tdoc'], root),
                                 (event['subject_tdoc'], None))
                with patch('document_decision_source.annex_source_evidence', return_value=dict(checked, quote='another row')):
                    with self.assertRaisesRegex(ValueError, 'report source changed'):
                        storage.resolve_document_target(event, event['subject_tdoc'], root)
        self.assertEqual(event, original)

    def test_pending_census_separates_principle_and_missing_source_revision(self):
        from decision_disposition import pending_assessment
        row = {'dispositionId': 'RAN2:DOC-1-R2-000001-t11-r2:R2-000001',
               'targetTdocNumber': 'R2-000001', 'evidencePath': 'source.docx',
               'evidenceSha256': 'checked_sha',
               'evidenceLocator': 'word/document.xml accepted table block 11 row 2; governing body blocks [10,14)',
               'evidenceQuote': 'List of CRs agreed in principle\nR2-000001'}
        for rule, status, expected in [
                ('annex_in_principle_requires_final_source', None,
                 'explicit_in_principle_without_final_document_approval'),
                ('source_target_identity_review_pending', 'unresolved_source_document',
                 'source_document_or_report_revision_not_recovered'),
                ('source_target_identity_review_pending', 'identity_conflict',
                 'source_target_identity_conflict')]:
            row['assessmentMethod'] = json.dumps({'decisionBodyBlocks': [10, 14],
                                                  'rule': rule, 'identityStatus': status})
            self.assertEqual(pending_assessment(row)['category'], expected)

    def test_exact_report_revision_is_part_of_the_approval_target(self):
        actual = dict(self.target(), **{'tdoc:crRevision': 1})
        code, method = self.assess('38.521-3 CR-0055 rev1 Cat:F (Rel-17)', actual)
        self.assertEqual(code, 'agreed')
        self.assertEqual(method['targetIdentity']['sourceCrRevision'], 1)

    def test_same_document_review_cannot_approve_another_retained_revision(self):
        review = {'identityStatus': 'same_document_metadata_discrepancy'}
        actual = dict(self.target(), **{'tdoc:crRevision': 0})
        with patch.object(storage, 'document_identity_review', return_value=review):
            code, method = self.assess('38.521-3 CR-0055 rev1 Cat:F (Rel-17)', actual)
        self.assertEqual(code, 'ambiguous')
        self.assertEqual(method['sourceDispositionCode'], 'agreed')
        self.assertIn('source_CR_revision_differs_from_target', method['targetIdentity']['conflicts'])

    def test_annex_review_contract_preserves_existing_header_assessment_shape(self):
        with patch.object(storage, 'document_identity_review', return_value={
                'identityStatus': 'same_document_metadata_discrepancy'}):
            code, method = self.assess('38.521-3 CR-0055 Cat:F (Rel-17)', self.target())
        self.assertEqual(code, 'agreed')
        self.assertEqual(set(method), {'rule', 'targetIdentity'})

    def test_report_revision_cannot_bind_to_unknown_target_revision(self):
        code, method = self.assess('38.521-3 CR-0055 rev. 1 Cat:F (Rel-17)', self.target())
        self.assertEqual(code, 'ambiguous')
        self.assertIn('source_CR_revision_not_bound_to_target', method['targetIdentity']['conflicts'])

    def test_other_type_cannot_bypass_an_explicit_report_revision(self):
        actual = dict(self.target(), **{'tdoc:type': 'other'})
        code, method = self.assess('38.521-3 CR-0055 rev1 Cat:F (Rel-17)', actual, 'other')
        self.assertEqual(code, 'ambiguous')
        self.assertIn('source_CR_revision_not_bound_to_target', method['targetIdentity']['conflicts'])

    def test_cr_number_spec_release_conflicts_preserve_original_disposition(self):
        code, method = self.assess('Type: CR\n38.521-1 v16.1.0 CR-0056 Cat:F (Rel-16)', self.target())
        self.assertEqual(code, 'ambiguous')
        self.assertEqual(method['sourceDispositionCode'], 'agreed')
        self.assertEqual(set(method['targetIdentity']['conflicts']), {
            'source_CR_number_differs_from_target', 'source_CR_spec_differs_from_target',
            'source_CR_release_differs_from_target'})

    def test_source_cr_cannot_approve_actual_discussion(self):
        actual = dict(self.target(), **{'tdoc:type': 'discussion'})
        code, method = self.assess('Type: CR', actual)
        self.assertEqual(code, 'ambiguous')
        self.assertIn('source_CR_type_differs_from_target_type', method['targetIdentity']['conflicts'])

    def test_title_release_is_not_the_cr_descriptor_release(self):
        code, method = self.assess('Correction of Rel-13 cases; 38.521-3 v17.1.0 CR-0055 Cat:F (Rel-17)', self.target())
        self.assertEqual(code, 'agreed')
        self.assertEqual(method['targetIdentity']['sourceRelease'], 'Rel-17')

    def test_non_cr_title_release_does_not_define_cr_identity(self):
        actual = {'@id': 'tdoc:R5-213430', 'tdoc:tdocNumber': 'R5-213430',
                  'tdoc:type': 'Work Plan', 'tdoc:targetRelease': 'tdoc:release/Rel_17'}
        code, method = self.assess('Work Plan for Rel-13 tests', actual, 'legacy_type_unspecified')
        self.assertEqual(code, 'agreed')
        self.assertNotIn('sourceRelease', method['targetIdentity'])

    def test_draft_placeholder_does_not_retype_a_discussion_as_formal_cr(self):
        actual = dict(self.target(), **{'tdoc:type': 'discussion', 'tdoc:crNumber': '0000'})
        code, method = self.assess('38.521-3 CR-0055 Cat:F (Rel-17)', actual, 'draft CR')
        self.assertEqual(code, 'agreed')
        self.assertEqual(method['targetIdentity']['type'], 'discussion')
        self.assertNotIn('conflicts', method['targetIdentity'])

    def test_unknown_cr_number_preserves_numbered_source_claim(self):
        actual = dict(self.target(), **{'tdoc:crNumber': '0000'})
        code, method = self.assess('38.521-3 CR-0055 Cat:F (Rel-17)', actual, 'draft CR')
        self.assertEqual(code, 'agreed')
        self.assertEqual(method['targetIdentity']['sourceCrNumber'], '0055')

    def test_pcr_is_in_the_existing_phase1_cr_family(self):
        actual = dict(self.target(), **{'tdoc:type': 'pCR', 'tdoc:crNumber': None})
        code, method = self.assess('Type: CR', actual)
        self.assertEqual(code, 'agreed')
        self.assertEqual(method['targetIdentity']['type'], 'pCR')

    def test_direct_unresolved_source_review_is_binding_without_descriptor_conflict(self):
        review = {'identityStatus': 'unresolved_source_document',
                  'inventoryReason': 'No accepted own document in the checked source inventory',
                  'actualDocumentEvidence': []}
        with patch.object(storage, 'document_identity_review', return_value=review):
            code, method = self.assess('38.521-3 CR-0055 Cat:F (Rel-17)', self.target())
        self.assertEqual(code, 'ambiguous')
        self.assertEqual(method['sourceDispositionCode'], 'agreed')
        self.assertEqual(method['identityStatus'], 'unresolved_source_document')

    def test_direct_different_document_review_cannot_be_bypassed_by_type_relaxation(self):
        review = {'identityStatus': 'identity_conflict', 'actualDocumentEvidence': []}
        with patch.object(storage, 'document_identity_review', return_value=review):
            code, method = self.assess('discussion', self.target(), 'draft CR')
        self.assertEqual(code, 'ambiguous')
        self.assertEqual(method['identityStatus'], 'identity_conflict')

    def test_durable_journal_roundtrip_leaves_no_temporary_files(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'receipt.json'
            storage.durable_json(path, {'한글': '원문', 'state': 'prepared'})
            storage.durable_json(path, {'state': 'committed'})
            self.assertEqual(json.loads(path.read_text()), {'state': 'committed'})
            self.assertEqual([item.name for item in path.parent.iterdir()], ['receipt.json'])

    def test_durable_journal_replace_failure_preserves_preimage_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'receipt.json'
            path.write_bytes(b'previous complete journal')
            with patch.object(storage.os, 'replace', side_effect=OSError('synthetic replace failure')):
                with self.assertRaisesRegex(OSError, 'synthetic replace failure'):
                    storage.durable_json(path, {'state': 'prepared'})
            self.assertEqual(path.read_bytes(), b'previous complete journal')
            self.assertEqual([item.name for item in path.parent.iterdir()], ['receipt.json'])

    def test_durable_journal_serialization_failure_leaves_no_temp(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'receipt.json'
            path.write_bytes(b'previous complete journal')
            with self.assertRaises(TypeError):
                storage.durable_json(path, {'invalid': object()})
            self.assertEqual(path.read_bytes(), b'previous complete journal')
            self.assertEqual([item.name for item in path.parent.iterdir()], ['receipt.json'])

    def test_archived_native_pptx_checks_container_member_and_exact_slide_quote(self):
        payload = io.BytesIO()
        with zipfile.ZipFile(payload, 'w') as presentation:
            presentation.writestr('ppt/slides/slide1.xml', '<a:txBody xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:t>R4-1816332</a:t><a:t>Updated assumptions</a:t></a:txBody>')
        member = payload.getvalue()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'original.zip'
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('original.pptx', member)
            evidence = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                'zipMember': 'original.pptx', 'memberSha256': hashlib.sha256(member).hexdigest(),
                'locator': 'ppt/slides/slide1.xml drawing:a:t text sequence',
                'quote': 'R4-1816332\nUpdated assumptions'}
            storage.check_archived_slide_evidence(path, [evidence])
            with self.assertRaisesRegex(ValueError, 'slide quote changed'):
                storage.check_archived_slide_evidence(path, [dict(evidence, quote='R4-1816334')])
            with self.assertRaisesRegex(ValueError, 'member changed'):
                storage.check_archived_slide_evidence(path, [dict(evidence, memberSha256='0' * 64)])

    def test_actual_report_alias_preserves_source_identity_and_is_entry_specific(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected = {'R3-9990001': 'R3-990001', 'R3-9990002': 'R3-990002'}
            events = self.synthetic_alias_events(root, 'RAN3', expected)
            self.assertEqual(len(events), 2)
            with self.fixture_only_reads(root):
                for event in events:
                    source = event['subject_tdoc']
                    resolved, receipt = storage.resolve_document_target(event, source, root)
                    self.assertEqual(resolved, expected[source])
                    self.assertEqual(receipt['sourceTdocNumber'], source)
                    node = storage.document_resolution_node(event, root)
                    self.assertIn(source, node['resolutionId'])
                    self.assertIn(source, node['content'])
                    self.assertEqual(node['aboutTdoc'], 'tdoc:' + resolved)
                    unrelated = copy.deepcopy(event)
                    unrelated['body_blocks'][1] += 1
                    self.assertEqual(storage.resolve_document_target(unrelated, source, root), (source, None))

    def test_actual_annex_alias_checks_row_master_and_all_original_archives(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected = {'R2-9990001': 'R2-990001'}
            events = self.synthetic_alias_events(root, 'RAN2', expected, annex=True)
            self.assertEqual(len(events), 1)
            event = events[0]
            source = event['subject_tdoc']
            with self.fixture_only_reads(root):
                resolved, receipt = storage.resolve_document_target(event, source, root)
                self.assertEqual(resolved, expected[source])
                self.assertEqual(len(storage.raw_zip_receipts(receipt)), 3)
                code, method = storage.assess_document_identity(event, source, 'agreed', {}, root)
                self.assertEqual(code, 'agreed')
                self.assertEqual(method['targetAlias']['sourceTdocNumber'], source)
                self.assertEqual(int(method['targetIdentity']['crRevision']), 3)
                self.assertEqual(event['subject_tdoc'], source)
                self.assertIn(source, event['content'])
                alias_path = root / 'ontology/input/tsg/RAN/formal/meetings/RAN2/document_decision_target_aliases.json'
                original = json.loads(alias_path.read_text())
                for archive in original['aliases'][0]['rawZipEvidence']:
                    with self.subTest(archive=archive['path']):
                        changed = copy.deepcopy(original)
                        selected = next(item for item in changed['aliases'][0]['rawZipEvidence']
                                        if item['path'] == archive['path'])
                        selected['sha256'] = '0' * 64
                        alias_path.write_text(json.dumps(changed))
                        storage._target_aliases.cache_clear()
                        with self.assertRaisesRegex(ValueError, 'raw ZIP changed'):
                            storage.resolve_document_target(event, source, root)
                alias_path.write_text(json.dumps(original))
                storage._target_aliases.cache_clear()
                changed = copy.deepcopy(original)
                changed['aliases'][0]['masterEvidence']['fields']['TDoc'] = 'R2-990002'
                alias_path.write_text(json.dumps(changed))
                with self.assertRaisesRegex(ValueError, 'exact master row changed'):
                    storage.resolve_document_target(event, source, root)
                alias_path.write_text(json.dumps(original))
                storage._target_aliases.cache_clear()
                changed_event = copy.deepcopy(event)
                changed_event['document_entry']['annexTable']['rowCells'][1] = 'Changed title'
                with self.assertRaisesRegex(ValueError, 'Annex row, header, governing scope, identity or source fields changed'):
                    storage.resolve_document_target(changed_event, source, root)

    def test_disposition_fence_uses_committed_source_stage_and_rechecks_initial_files(self):
        import decision_disposition as d
        properties = {'dispositionId': 'RAN5:DOC-91-R5-213430-b1:R5-213430'}
        payload = [{'properties': properties, 'resolutionId': 'DOC-91-R5-213430-b1', 'tdocNumber': 'R5-213430'}]
        state, snapshots, checks = {'stage': 0}, [], []
        class Result:
            def __init__(self, value=None): self.value = value
            def consume(self): return None
            def single(self): return self.value
            def data(self): return self.value
        class Session:
            def run(self, query, **kwargs):
                if 'RETURN count(DISTINCT d) AS assertions' in query: return Result({'assertions': 1, 'missingTargets': 0})
                if 'RETURN count(d) AS count' in query: return Result({'count': 1})
                if 'RETURN properties(d) AS properties,edges' in query:
                    return Result([{'properties': properties, 'edges': [
                        {'type': 'DISPOSITION_OF', 'resolutionId': payload[0]['resolutionId'], 'target': None},
                        {'type': 'DISPOSITION_TARGET', 'resolutionId': None, 'target': 'R5-213430'}],
                        'inverse': [payload[0]['resolutionId']]}])
                if 'RETURN t.tdocNumber AS number' in query: return Result([{'number': 'R5-213430'}])
                return Result()
            def execute_write(self, callback): return callback(self)
        def snapshot(*args):
            snapshots.append(state['stage'])
            return [{'endpointStage': state['stage']}]
        def source_stage(*args):
            state['stage'] = 1
            journal = d.ROOT / 'logs/common/RAN5/verification/decision-dispositions/source-event-preimage-current.json'
            journal.parent.mkdir(parents=True, exist_ok=True)
            storage.durable_json(journal, {'state': 'committed', 'sourceFiles': initial,
                'qualificationStatus': 'awaiting_dispositions'})
            return {'sourceEvents': 1, 'preimageJournal': str(journal.relative_to(d.ROOT))}
        actual_fingerprint_check = storage.check_fingerprints
        def fingerprints_check(value, root):
            checks.append(dict(value))
            actual_fingerprint_check(value, root)
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            source_path = Path(directory) / 'source'
            source_path.write_bytes(b'original accepted document bytes')
            initial = {'source': hashlib.sha256(source_path.read_bytes()).hexdigest()}
            for module, name, value in [(d, 'ROOT', Path(directory)), (d, 'validate_dispositions', lambda rows: None),
                    (d, 'neo4j_rows', lambda rows: payload), (d, 'reports_for_wg', lambda wg: []),
                    (d, 'disposition_snapshot', snapshot), (d, 'resolution_snapshot', lambda *args: []),
                    (storage, 'document_resolution_nodes', lambda reports: []),
                    (storage, 'load_document_resolutions', source_stage),
                    (storage, 'source_fingerprints', lambda *args: initial),
                    (storage, 'check_fingerprints', fingerprints_check)]:
                stack.enter_context(patch.object(module, name, value))
            self.assertEqual(d.load_dispositions(Session(), [{}])['assertions'], 1)
            self.assertEqual(snapshots, [1, 1, 1])
            self.assertEqual(checks, [initial, initial])
            journals = [path for path in (Path(directory) / 'logs/common/RAN5/verification/decision-dispositions').glob('preimage-*.json')
                        if not path.name.endswith('.result.json')]
            self.assertEqual(len(journals), 1)
            self.assertEqual(json.loads(journals[0].read_text())['sourceFingerprints'], initial)
            source_journal = journals[0].with_name('source-event-preimage-current.json')
            source_receipt = json.loads(source_journal.read_text())
            self.assertEqual(source_receipt['qualificationStatus'], 'complete')
            self.assertEqual(source_receipt['sourceFiles'], initial)
            self.assertFalse((Path(directory) / 'logs/common/verification/decision-dispositions').exists())
            # An external file change during the source stage still aborts the
            # assertion transaction; only the owned source endpoint changed.
            def source_and_external_change(*args):
                state['stage'] = 2
                source_path.write_bytes(b'external replacement document bytes')
                return {'sourceEvents': 1}
            stack.enter_context(patch.object(storage, 'load_document_resolutions', source_and_external_change))
            with self.assertRaisesRegex(ValueError, 'Source/identity artifact changed before commit'):
                d.load_dispositions(Session(), [{}])

    def test_source_event_preimage_is_prepared_under_its_workgroup_slot(self):
        class Prepared(Exception):
            pass
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            observed = []
            def prepare(path, receipt):
                observed.append((path, receipt))
                raise Prepared
            with patch.object(storage, 'storage_rows', return_value=[{
                    'properties': {'resolutionId': 'DOC-current'}}]), \
                    patch.object(storage, 'source_event_snapshot', return_value=[]), \
                    patch.object(storage, 'source_fingerprints', return_value={}), \
                    patch.object(storage, 'durable_json', side_effect=prepare):
                with self.assertRaises(Prepared):
                    storage.load_document_resolutions(None, [{'madeAt': 'tdoc:meeting/RAN1_123'}], root)
            path, receipt = observed[0]
            self.assertEqual(path.parent, root / 'logs/common/RAN1/verification/decision-dispositions')
            self.assertTrue(path.name.startswith('source-event-preimage-'))
            self.assertEqual(receipt['state'], 'prepared')
            self.assertEqual(receipt['qualificationStatus'], 'awaiting_dispositions')
            self.assertEqual(receipt['wg'], 'RAN1')
            self.assertFalse((root / 'logs/common/verification/decision-dispositions').exists())

    def test_source_fence_reads_relocated_bytes_without_rewriting_the_binding(self):
        from common import review_artifacts
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old_parent = 'synthetic_source_observation'
            current_parent = 'synthetic-source-observation'
            old = str(review_artifacts.LEGACY_REVIEW_ROOT / old_parent / 'receipt.json')
            current = root / 'logs/common/RAN3/verification/ontology-system-review' / current_parent / 'receipt.json'
            current.parent.mkdir(parents=True)
            current.write_bytes(b'completed source observation')
            digest = hashlib.sha256(current.read_bytes()).hexdigest()
            fingerprints = {old: digest}
            with patch.object(review_artifacts, 'DIRECTORY_RENAMES', {old_parent: current_parent}), \
                    patch.object(review_artifacts, 'DIRECTORY_WORKGROUPS', {old_parent: 'RAN3'}), \
                    self.fixture_only_reads(root):
                storage.check_fingerprints(fingerprints, root)
                self.assertEqual(fingerprints, {old: digest})
                current.write_bytes(b'changed observation')
                with self.assertRaisesRegex(ValueError, 'Source/identity artifact changed'):
                    storage.check_fingerprints(fingerprints, root)
                current.write_bytes(b'completed source observation')
                legacy = root / old
                legacy.parent.mkdir(parents=True)
                legacy.write_bytes(current.read_bytes())
                with self.assertRaisesRegex(ValueError, 'Source/identity artifact changed'):
                    storage.check_fingerprints(fingerprints, root)

    def test_source_fence_does_not_borrow_an_old_code_generation_or_unsafe_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'scripts/producer.py'
            source.parent.mkdir()
            source.write_bytes(b'old code generation')
            original = hashlib.sha256(source.read_bytes()).hexdigest()
            source.write_bytes(b'new code generation')
            with self.assertRaisesRegex(ValueError, 'Source/identity artifact changed'):
                storage.check_fingerprints({'scripts/producer.py': original}, root)
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            for coordinate in ('../producer.py', str(source), 'scripts/../scripts/producer.py'):
                with self.subTest(coordinate=coordinate), self.assertRaises(ValueError):
                    storage.check_fingerprints({coordinate: digest}, root)
            alias = root / 'scripts/alias.py'
            alias.symlink_to(source)
            with self.assertRaises(ValueError):
                storage.check_fingerprints({'scripts/alias.py': digest}, root)

    def test_source_event_commit_errors_require_exact_readback(self):
        from neo4j.exceptions import IncompleteCommit
        row = {'properties': {'resolutionId': 'DOC-current',
                             'resolutionScope': 'document_disposition'},
               'agreement': False, 'meetingId': 'tdoc:meeting/RAN1_123',
               'agendaId': None, 'references': [], 'aboutTdoc': 'R1-current'}
        after = [{'resolutionId': 'DOC-current', 'properties': row['properties'],
                  'labels': ['Resolution'], 'edges': [
                      {'type': 'MADE_AT', 'properties': {}, 'target': row['meetingId']}]}]
        class Result:
            def __init__(self, value): self.value = value
            def data(self): return self.value
            def consume(self): pass
        class Transaction:
            def __init__(self): self.snapshots = 0
            def run(self, query, **kwargs):
                if 'RETURN id,count(m)' in query:
                    return Result([{'id': row['meetingId'], 'n': 1}])
                return Result([])
        for mode, expected in [('success', 'committed'),
                               ('rollback', 'rolled_back'),
                               ('committed', 'committed'),
                               ('foreign', 'changed_requires_review'),
                               ('unavailable', 'commit_outcome_unknown'),
                               ('rejected', 'rolled_back'),
                               ('failed_retry', 'changed_requires_review')]:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                error = ValueError('endpoint rejected') if mode == 'rejected' else IncompleteCommit('response lost')
                state = {'value': [], 'error': None}
                class Session:
                    def execute_write(self, callback):
                        if mode == 'rejected':
                            raise error
                        result = callback(Transaction())
                        if mode == 'success':
                            state['value'] = after
                            return result
                        state['value'] = after if mode in ('committed', 'failed_retry') else []
                        if mode == 'foreign':
                            state['value'] = [dict(after[0], properties={'resolutionId': 'DOC-foreign'})]
                        if mode == 'unavailable':
                            state['error'] = OSError('readback unavailable')
                        if mode == 'failed_retry':
                            try:
                                callback(Transaction())
                            except ValueError:
                                pass
                        raise error
                session = Session()
                callback_count = 0
                def snapshot(reader, ids):
                    nonlocal callback_count
                    if isinstance(reader, Transaction):
                        reader.snapshots += 1
                        if reader.snapshots == 1:
                            callback_count += 1
                            if mode == 'failed_retry' and callback_count == 2:
                                raise ValueError('later retry rejected')
                            return []
                        return after
                    if state['error'] is not None:
                        raise state['error']
                    return state['value']
                stack.enter_context(patch.object(storage, 'storage_rows', return_value=[row]))
                stack.enter_context(patch.object(storage, 'source_fingerprints', return_value={}))
                stack.enter_context(patch.object(storage, 'check_fingerprints'))
                stack.enter_context(patch.object(storage, 'source_event_snapshot', side_effect=snapshot))
                root = Path(directory)
                if mode == 'success':
                    result = storage.load_document_resolutions(session, [{'madeAt': row['meetingId']}], root)
                    self.assertEqual(result['sourceEvents'], 1)
                else:
                    with self.assertRaises(type(error)) as raised:
                        storage.load_document_resolutions(session, [{'madeAt': row['meetingId']}], root)
                    self.assertIs(raised.exception, error)
                receipt = json.loads(next(root.rglob('source-event-preimage-*.json')).read_text())
                self.assertEqual(receipt['state'], expected)
                self.assertEqual(receipt['qualificationStatus'], 'awaiting_dispositions')
                self.assertEqual(receipt['before'], [])
                self.assertEqual(receipt['incoming'], [row])
                if mode == 'committed':
                    self.assertEqual(receipt['transactionReadback'], 'matches_verified_postimage')
                    self.assertEqual(receipt['result']['sourceEvents'], 1)
                if mode == 'unavailable':
                    self.assertEqual(receipt['readbackError'], 'readback unavailable')
                if mode in ('foreign', 'failed_retry'):
                    self.assertEqual(receipt['transactionReadback'], 'differs_from_expected')

    def test_disposition_commit_errors_preserve_source_stage_and_unknown_outcome(self):
        import decision_disposition as d
        from neo4j.exceptions import IncompleteCommit
        properties = {'dispositionId': 'RAN5:DOC-current:R5-current'}
        payload = [{'properties': properties, 'resolutionId': 'DOC-current', 'tdocNumber': 'R5-current'}]
        before, after = [{'snapshot': 'before'}], [{'snapshot': 'after'}]
        class Result:
            def __init__(self, value=None): self.value = value
            def consume(self): pass
            def single(self): return self.value
            def data(self): return self.value
        for mode, expected in [('success', 'committed'),
                               ('rollback', 'dispositions_rolled_back'),
                               ('committed', 'committed'),
                               ('foreign', 'changed_requires_review'),
                               ('unavailable', 'commit_outcome_unknown'),
                               ('postcondition_foreign', 'changed_requires_review'),
                               ('postcondition_unavailable', 'commit_outcome_unknown')]:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                root = Path(directory)
                error = IncompleteCommit('disposition response lost')
                state = {'value': before, 'callback': False, 'finished': False}
                source_path = root / 'source-event.json'
                storage.durable_json(source_path, {'state': 'committed', 'qualificationStatus': 'awaiting_dispositions'})
                source_result = {'sourceEvents': 1, 'preimageJournal': source_path.name}
                class Session:
                    def run(self, query, **kwargs):
                        if 'RETURN count(DISTINCT d) AS assertions' in query:
                            return Result({'assertions': 1, 'missingTargets': 0})
                        if 'RETURN count(d) AS count' in query:
                            return Result({'count': 0 if mode.startswith('postcondition_') else 1})
                        if 'RETURN properties(d) AS properties,edges' in query:
                            return Result([{'properties': properties, 'edges': [
                                {'type': 'DISPOSITION_OF', 'resolutionId': 'DOC-current', 'target': None},
                                {'type': 'DISPOSITION_TARGET', 'resolutionId': None, 'target': 'R5-current'}],
                                'inverse': ['DOC-current']}])
                        if 'RETURN t.tdocNumber AS number' in query:
                            return Result([{'number': 'R5-current'}])
                        return Result()
                    def execute_write(self, callback):
                        state['callback'] = True
                        try:
                            result = callback(self)
                        except Exception as callback_error:
                            state['callback'] = False
                            state['finished'] = True
                            state['value'] = [{'snapshot': 'foreign'}]
                            state['raised'] = callback_error
                            raise
                        state['callback'] = False
                        state['finished'] = True
                        state['value'] = after if mode in ('success', 'committed') else before
                        if mode == 'foreign':
                            state['value'] = [{'snapshot': 'foreign'}]
                        if mode == 'success':
                            return result
                        raise error
                def snapshot(*args):
                    if state['callback']:
                        state['callback_reads'] = state.get('callback_reads', 0) + 1
                        return before if state['callback_reads'] == 1 else after
                    if state['finished'] and mode in ('unavailable', 'postcondition_unavailable'):
                        raise OSError('disposition readback unavailable')
                    return state['value']
                for module, name, value in [
                        (d, 'ROOT', root), (d, 'validate_dispositions', lambda rows: None),
                        (d, 'neo4j_rows', lambda rows: payload), (d, 'reports_for_wg', lambda wg: []),
                        (d, 'disposition_snapshot', snapshot), (d, 'resolution_snapshot', lambda *args: []),
                        (storage, 'document_resolution_nodes', lambda reports: []),
                        (storage, 'load_document_resolutions', lambda *args: source_result),
                        (storage, 'source_fingerprints', lambda *args: {}),
                        (storage, 'check_fingerprints', lambda *args: None)]:
                    stack.enter_context(patch.object(module, name, value))
                if mode == 'success':
                    self.assertEqual(d.load_dispositions(Session(), [{}])['assertions'], 1)
                else:
                    with self.assertRaises(ValueError if mode.startswith('postcondition_') else IncompleteCommit) as raised:
                        d.load_dispositions(Session(), [{}])
                    self.assertIs(raised.exception, state.get('raised', error))
                    if mode.startswith('postcondition_'):
                        self.assertIn('Disposition postcondition failed', str(raised.exception))
                receipt = json.loads(next(root.rglob('preimage-*.result.json')).read_text())
                self.assertEqual(receipt['state'], expected)
                source_receipt = json.loads(source_path.read_text())
                self.assertEqual(source_receipt['state'], 'committed')
                self.assertEqual(source_receipt['qualificationStatus'],
                                 'complete' if mode == 'success' else 'awaiting_dispositions')
                if mode != 'success':
                    self.assertEqual(receipt['sourceEventStage'], source_result)
                if mode == 'committed':
                    self.assertEqual(receipt['transactionReadback'], 'matches_verified_postimage')
                    self.assertEqual(receipt['result']['assertions'], 1)
                if mode in ('unavailable', 'postcondition_unavailable'):
                    self.assertEqual(receipt['readbackError'], 'disposition readback unavailable')


class AbsentSourceEventRetirement(unittest.TestCase):
    """An event the source no longer yields leaves only with what this layer owns."""

    def event(self, *edges):
        return {'resolutionId': 'DOC-78-R4-161048-b14406', 'labels': ['Resolution'],
                'properties': {'resolutionId': 'DOC-78-R4-161048-b14406',
                               'resolutionScope': 'document_disposition'},
                'edges': [dict({'properties': {}, 'labels': [], 'disposition': None}, **edge) for edge in edges]}

    def owned(self):
        return [{'type': 'MADE_AT', 'outgoing': True, 'neighbour': 'tdoc:meeting/RAN4_78'},
                {'type': 'ABOUT_TDOC', 'outgoing': True, 'neighbour': 'R4-161048'},
                {'type': 'HAS_DISPOSITION', 'outgoing': True, 'neighbour': 'RAN4:old',
                 'disposition': {'evidenceStatus': 'pending'}},
                {'type': 'DISPOSITION_OF', 'outgoing': False, 'neighbour': 'RAN4:old',
                 'disposition': {'evidenceStatus': 'pending'}},
                {'type': 'ANCHORS', 'outgoing': False, 'neighbour': 'mail',
                 'properties': {'channel': 'resolution', 'state': 'candidate'}}]

    def test_owned_attachments_are_retirable(self):
        storage.check_retirable_event(self.event(*self.owned()), set())

    def test_current_or_verified_assertion_or_foreign_edge_stops_retirement(self):
        verified = {'type': 'HAS_DISPOSITION', 'outgoing': True, 'neighbour': 'RAN4:old',
                    'disposition': {'evidenceStatus': 'source_verified'}}
        confirmed = {'type': 'ANCHORS', 'outgoing': False, 'neighbour': 'mail',
                     'properties': {'channel': 'resolution', 'state': 'confirmed'}}
        foreign = {'type': 'REFERENCES', 'outgoing': False, 'neighbour': 'AGR-1'}
        for edge in (verified, confirmed, foreign):
            with self.subTest(edge=edge['type']), self.assertRaises(ValueError):
                storage.check_retirable_event(self.event(*self.owned(), edge), set())
        with self.assertRaises(ValueError):
            storage.check_retirable_event(self.event(*self.owned()), {'RAN4:old'})
        technical = self.event(*self.owned())
        technical['properties']['resolutionScope'] = None
        with self.assertRaises(ValueError):
            storage.check_retirable_event(technical, set())

    def test_retirement_journals_the_preimage_and_checks_the_remaining_generation(self):
        prior = [self.event(*self.owned())]
        class Result:
            def __init__(self, value): self.value = value
            def data(self): return self.value
            def consume(self): pass
        class Graph:
            def __init__(self): self.ids, self.deleted = ['DOC-current', prior[0]['resolutionId']], []
            def run(self, query, **kwargs):
                if 'DETACH DELETE r' in query:
                    self.ids = ['DOC-current']
                if 'DETACH DELETE' in query:
                    self.deleted.append(kwargs['ids'])
                if 'RETURN events' in query:
                    return Result([{'events': 0, 'assertions': 0}])
                return Result([{'id': value} for value in self.ids])
            def execute_write(self, callback): return callback(self)
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(storage, 'absent_event_snapshot', return_value=prior):
            root, graph = Path(directory), Graph()
            result = storage.retire_absent_document_events(
                graph, 'RAN4', [{'resolutionId': 'DOC-current'}], ['RAN4:current'], root)
            self.assertEqual(graph.deleted, [['RAN4:old'], [prior[0]['resolutionId']]])
            self.assertEqual((result['retiredSourceEvents'], result['retiredAssertions'],
                              result['retiredCandidateAnchors']), (1, 1, 1))
            journal = json.loads((root / result['preimageJournal']).read_text())
            self.assertEqual((journal['state'], journal['before']), ('committed', prior))
            with self.assertRaises(ValueError):
                storage.retire_absent_document_events(Graph(), 'RAN4', [{'resolutionId': 'DOC-unloaded'}], [], root)


if __name__ == '__main__':
    unittest.main()
