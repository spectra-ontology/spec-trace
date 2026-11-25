#!/usr/bin/env python3
"""test_decision_disposition.py — 대상·revision·modality 결속의 회귀 검사.

Spec: docs/tsg/build/standards/decision_disposition_contract.md.
Ontology: qualified dispositions preserve references and distinguish approval predicates.
Cycle: authored DOCX/report fixtures + adversarial sentences → source-bound rules.
배경: 승인 단어의 존재나 현재 전역 status로 대상별 승인을 만들지 않는다.
사용: python3 -m unittest discover -s scripts/tsg/RAN/formal/common -p test_decision_disposition.py.
LLM 호출: 없음.
"""
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
import zipfile

from decision_disposition import (ROOT, build_report_dispositions as build_all_report_dispositions, classify_statement,
                                  validate_dispositions, load_dispositions)
from cq_anchor_guard import approval_contract_defects


def build_report_dispositions(report, root=ROOT):
    """These regressions select authored decisions; document fields have separate tests."""
    return build_all_report_dispositions(report, root=root, include_document=False)


class AcceptedSourceBytes(unittest.TestCase):
    @staticmethod
    def package(text):
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as archive:
            archive.writestr('word/document.xml',
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:body><w:p><w:r><w:t>' + text + '</w:t></w:r></w:p></w:body></w:document>')
        return data.getvalue()

    def test_changed_source_path_uses_current_generation_and_retains_uncached_api(self):
        import decision_disposition as d
        self.addCleanup(d.source_blocks.cache_clear)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.docx'
            first, second = self.package('First source'), self.package('Other source')
            path.write_bytes(first)
            self.assertEqual(d.source_blocks(str(path))[0][0], 'First source')
            path.write_bytes(second)
            texts, digest, _ = d.source_blocks(str(path))
            self.assertEqual(texts[0], 'Other source')
            self.assertEqual(digest, hashlib.sha256(second).hexdigest())
            self.assertEqual(d.source_blocks.__wrapped__(str(path))[0][0], 'Other source')

    def test_hash_and_parsed_text_bind_the_same_bytes_during_replacement(self):
        import decision_disposition as d
        self.addCleanup(d.source_blocks.cache_clear)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.docx'
            first, second = self.package('First source'), self.package('Other source')
            path.write_bytes(first)
            zip_reader = zipfile.ZipFile
            def replace_after_open(*args, **kwargs):
                archive = zip_reader(*args, **kwargs)
                replacement = path.with_suffix('.replacement')
                replacement.write_bytes(second)
                replacement.replace(path)
                return archive
            with patch.object(d.zipfile, 'ZipFile', side_effect=replace_after_open):
                texts, digest, _ = d.source_blocks(str(path))
            self.assertEqual(texts[0], 'First source')
            self.assertEqual(digest, hashlib.sha256(first).hexdigest())


class DispositionArtifactWrites(unittest.TestCase):
    def test_failed_replacement_preserves_previous_artifacts_and_cleans_temporary(self):
        import decision_disposition as d
        import document_decision_storage as storage
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            previous = {'decision_dispositions.jsonld': b'{"old":"assertions"}\n',
                        'resolutions_document_dispositions.jsonld': b'{"old":"events"}\n'}
            for name, data in previous.items():
                (output / name).write_bytes(data)
            with patch.object(d, 'validate_dispositions', return_value=[]), \
                    patch.object(storage, 'document_resolution_nodes', return_value=[]), \
                    patch('common.atomic_io.os.replace', side_effect=OSError('synthetic replacement failure')):
                with self.assertRaisesRegex(OSError, 'synthetic replacement failure'):
                    d.write_dispositions([], output, prepared_rows=[])
            self.assertEqual({p.name: p.read_bytes() for p in output.iterdir()}, previous)


class TargetRules(unittest.TestCase):
    def code(self, text, target='R1-2601728', **kwargs):
        return classify_statement(text, target, **kwargs)[0]

    def test_shared_approved_list(self):
        text = 'Final CRs agreed in R1-2601728 (TS38.213) and R1-2601678 (TS38.211)'
        self.assertEqual(self.code(text), 'agreed')
        self.assertEqual(self.code(text, 'R1-2601678'), 'agreed')
        self.assertEqual(self.code('Final CR are agreed in R1-2601728 (38.213) and R1-2601678.'), 'agreed')
        self.assertEqual(self.code('The tdoc R1-2601728: Corrections on requirements (vivo) is endorsed.'), 'endorsed')
        self.assertEqual(self.code('Support spatial relation and agree R1-2601728 (with revisions as needed).'), 'conditionally_agreed')

    def test_withdrawal_and_approval_are_bound_to_each_target(self):
        text = 'R1-2601678 withdrawn. R1-2601728 agreed.'
        self.assertEqual(self.code(text, 'R1-2601678'), 'withdrawn')
        self.assertEqual(self.code(text), 'agreed')

    def test_multiline_metadata_belongs_to_its_tdoc_entry(self):
        text = 'R1-2601678\tCR title\n(Rel19, 36.213) is withdrawn.\nR1-2601728\tCR title\n(Rel19, 38.213) is agreed.'
        self.assertEqual(self.code(text, 'R1-2601678'), 'withdrawn')
        self.assertEqual(self.code(text), 'agreed')

    def test_revision_does_not_approve_predecessor(self):
        text = 'R1-2601678 is revised to R1-2601728 which is agreed.'
        self.assertEqual(self.code(text, 'R1-2601678'), 'revised')
        self.assertEqual(self.code(text), 'agreed')
        self.assertEqual(self.code('R1-2601678 Rev in R1-2601728 Agreed'), 'agreed')
        self.assertEqual(self.code('R1-2601678 Rev in R1-2601728 Agreed', 'R1-2601678'), 'revised')

    def test_content_adoption_does_not_approve_incidental_sources(self):
        self.assertEqual(self.code('Adopt TP #2 in Section 3 of R1-2601728.'), 'partially_agreed')
        self.assertEqual(self.code('Adopt TP #2 in R1-2601728 (cover sheet information in R1-2601678).', 'R1-2601678'), 'ambiguous')
        self.assertEqual(self.code('Adopt proposed TP2 in R1-2601728, on top of changes in R1-2601678.', 'R1-2601678'), 'ambiguous')
        self.assertEqual(self.code('Do not adopt the changes in R1-2601728.'), 'not_agreed')
        self.assertNotEqual(self.code('If no objection, adopt the TP in R1-2601728.'), 'agreed')

    def test_future_and_conditions_are_not_unqualified_agreement(self):
        for text in ['R1-2601728 will be agreed at next meeting',
                     'R1-2601728 to be approved',
                     'If the CR is corrected, R1-2601728 is agreed']:
            self.assertNotEqual(self.code(text), 'agreed')
        self.assertEqual(self.code('R1-2601728 agreed with changes'), 'conditionally_agreed')

    def test_change_condition_does_not_depend_on_the_determiner(self):
        for text in ['R1-2601728 agreed with this change', 'R1-2601728 agreed with these changes',
                     'R1-2601728 agreed with the above change', 'R1-2601728 agreed with the editorial change above',
                     'R1-2601728 agreed with an update to the spreadsheet', 'R1-2601728 agreed with tdoc number correction']:
            self.assertEqual(self.code(text), 'conditionally_agreed', text)
        for text in ['R1-2601728 agreed with no changes', 'R1-2601728 agreed without changes']:
            self.assertEqual(self.code(text), 'agreed', text)

    def test_scope_is_preserved(self):
        self.assertEqual(self.code('Proposal 1 of R1-2601728 is agreed'), 'partially_agreed')
        self.assertEqual(self.code('The TP in R1-2601728 Annex B is agreed'), 'partially_agreed')
        self.assertEqual(self.code('R1-2601728 is endorsed'), 'endorsed')
        for text in ['The proposals in section 12 of R1-2601728 are agreed.',
                     'The text proposals in R1-2601728 are agreed.',
                     'Table 8 and Table 9 in R1-2601728 are agreed.',
                     'Rows 5-32 as in R1-2601728 are agreed.',
                     'The first proposal under Wed. session in R1-2601728 is agreed.']:
            self.assertNotEqual(self.code(text), 'agreed', text)

    def test_change_noun_naming_target_content_is_scope_not_condition(self):
        for text in ['Agree with the first change in R1-2601728.',
                     'R1 agree with the intention of change-4/5 of R1-2601728 and change in R1-2601678.',
                     'Agree the first change in R1-2601728 with one update as follows: "text"']:
            self.assertEqual(self.code(text), 'partially_agreed', text)
        self.assertEqual(self.code('R1-2601728 agreed with the editorial change above'), 'conditionally_agreed')
        self.assertEqual(self.code('Agree R1-2601728 in principle with the first change in R1-2601678.'), 'conditionally_agreed')

    def test_final_cr_for_draft_targets_only_the_final_revision(self):
        text = 'The final CR for draft CR in R1-2601678 is agreed in R1-2601728 (TS38.213).'
        self.assertEqual(self.code(text), 'agreed')
        self.assertNotEqual(self.code(text, 'R1-2601678'), 'agreed')
        self.assertEqual(self.code('R1-2601728 is agreed with following update.'), 'conditionally_agreed')

    def test_reference_does_not_inherit_another_target_status(self):
        self.assertEqual(self.code('R1-2601678 is agreed. R1-2601728 is discussed.'), 'ambiguous')
        self.assertEqual(self.code('R1-2601728 replaces the text added in R1-2601678'), 'ambiguous')

    def test_negative_dispositions(self):
        for phrase, code in [('not agreed', 'not_agreed'), ('rejected', 'rejected'),
                             ('not pursued', 'not_pursued'), ('postponed', 'postponed'),
                             ('noted', 'noted')]:
            self.assertEqual(self.code('R1-2601728 is ' + phrase), code)

    def test_ambiguous_conflicting_events_preserved(self):
        self.assertEqual(self.code('R1-2601728 agreed. R1-2601728 withdrawn.'), 'ambiguous')

    def test_checked_subject_binding_is_explicit(self):
        self.assertEqual(self.code('The proposals are accepted.', subject=True), 'partially_agreed')
        self.assertEqual(self.code('The CR is accepted.', subject=True), 'agreed')
        self.assertEqual(self.code('The proposals are accepted.'), 'ambiguous')

    def test_synthetic_audit_counterexamples_do_not_promote_status_words(self):
        # Authored fixtures exercise scope, history and modality without report quotations.
        for text in [
            'The following response to Question 7 in the fixture RAN2 LS (R1-2601728) is agreed:',
            'The following response for the synthetic RAN2 LS in R1-2601728 is agreed.',
            'Can the fixture work scope in R1-2601728 be agreed?',
            'According to the synthetic reply LS [R1-2601728], it is agreed not to enhance fixture stage 9 specs.',
            'Clarify a fixture rule in the agreed TC list (R1-2601728).',
            'R1-2601728 will be merged: it was agreed that fixture documents will be merged.',
            'Maintain the synthetic baseline already agreed in R1-2601728 during the previous meeting.',
            'R1-2601678 (was R1-2601728) is agreed for the fixture scenario.',
            'The fixture assumption in Issue 9-8-7 agreed in R1-2601728 during the previous meeting is maintained.',
            'Fixture receiver rules are the same as fixture sender rules (agreed in [R1-2601728]).',
            '[Agreement] Fixture option 7 is agreed and R1-2601728 can be endorsed.',
        ]:
            self.assertNotEqual(self.code(text), 'agreed', text)
        self.assertEqual(self.code('The proposal cannot be accepted.', subject=True), 'not_agreed')
        self.assertNotEqual(self.code('R1-2601728 agreed with a modification on its cover sheet'), 'agreed')
        self.assertEqual(self.code('Agree R1-2601728 (with revisions as needed).'), 'conditionally_agreed')
        self.assertNotEqual(self.code('The plan for CR work split in R1-2601728 agreed.'), 'agreed')


class SourceBoundDispositions(unittest.TestCase):
    """실제 DOCX·보고서·SHA 검증을 직접 작성한 소규모 입력으로 실행한다."""

    def setUp(self):
        import decision_disposition as d
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.addCleanup(d.source_blocks.cache_clear)
        self.addCleanup(d._review_index.cache_clear)
        self.root = Path(temporary.name)
        self.report_number = 0

    def report(self, text, targets, *, wg='RAN1', group='agreements'):
        """검증기가 독립적으로 다시 읽을 DOCX와 파싱 결과를 함께 만든다."""
        self.report_number += 1
        number = 990 + self.report_number
        document = ET.Element('{%s}document' % 'http://schemas.openxmlformats.org/wordprocessingml/2006/main')
        word = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
        body = ET.SubElement(document, word + 'body')
        for paragraph in text.split('\n'):
            node = ET.SubElement(ET.SubElement(ET.SubElement(body, word + 'p'), word + 'r'), word + 't')
            node.text = paragraph
        source = self.root / f'sources/fixture-{number}.docx'
        source.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(source, 'w') as archive:
            archive.writestr('word/document.xml', ET.tostring(document, encoding='utf-8'))
        prefix = {'agreements': 'AGR', 'conclusions': 'CON', 'working_assumptions': 'WA'}[group]
        decision = {'decision_id': f'{prefix}-{number}-fixture-001',
                    'body_blocks': [0, len(text.split('\n'))], 'referenced_tdocs': list(targets)}
        report = {'meeting_id': f'{wg}#{number}', 'docx_path': str(source.relative_to(self.root)),
                  'agreements': [], 'conclusions': [], 'working_assumptions': []}
        report[group] = [decision]
        output = self.root / f'ontology/output/tsg/RAN/formal/parsed_reports/{wg}/fixture-{number}.json'
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report), encoding='utf-8')
        # 적재기의 출처 사전 점검이 읽는 세 파일도 이 입력에 속하는 합성 산출물이다.
        phase1 = self.root / f'ontology/output/tsg/RAN/formal/instances/phase-1/{wg}'
        phase1.mkdir(parents=True, exist_ok=True)
        for name in ('tdocs', 'meetings', 'agenda_items'):
            (phase1 / f'{name}.jsonld').write_text(json.dumps({'@graph': []}), encoding='utf-8')
        return report

    def rows(self, report):
        return build_report_dispositions(report, root=self.root)

    def validate(self, rows):
        return validate_dispositions(rows, root=self.root)

    def withdrawal_rows(self):
        report = self.report('R1-9900001 is withdrawn. R1-9900002 is agreed.',
                             ['R1-9900001', 'R1-9900002'])
        rows = self.rows(report)
        self.assertEqual(len(rows), 2)
        self.validate(rows)
        return rows

    def test_ls_response_counterexamples_do_not_approve_referenced_documents(self):
        target = 'R1-9900001'
        texts = [f'The following response to Question 7 in the fixture RAN2 LS ({target}) is agreed:',
                 f'The following response for the synthetic RAN2 LS in {target} is agreed.',
                 f'According to the synthetic reply LS [{target}], it is agreed not to enhance fixture stage 9 specs.',
                 f'Can the fixture work scope in {target} be agreed?']
        for text in texts:
            with self.subTest(text=text):
                rows = self.rows(self.report(text, [target]))
                self.assertEqual(len(rows), 1)
                self.assertEqual((rows[0]['dispositionCode'], rows[0]['evidenceStatus']), ('ambiguous', 'pending'))
                self.validate(rows)

    def test_intent_scope_history_and_modified_text_are_source_bound(self):
        cases = [
            ('RAN2', 'The proposal in R2-9900001 is agreed. The proposal in R2-9900002 is agreed. The proposal in R2-9900003 is agreed.',
             {'R2-9900001': 'partially_agreed', 'R2-9900002': 'partially_agreed', 'R2-9900003': 'partially_agreed'}),
            ('RAN1', 'The intent in R1-9900010 is agreed.', {'R1-9900010': 'partially_agreed'}),
            ('RAN1', 'Maintain the synthetic baseline already agreed in R1-9900011 during the previous meeting.',
             {'R1-9900011': 'ambiguous'}),
            ('RAN1', 'R1-9900012 is agreed with changes.', {'R1-9900012': 'conditionally_agreed'}),
            ('RAN2', 'The parameters in R2-9900013 are agreed.', {'R2-9900013': 'partially_agreed'}),
            ('RAN2', 'The text proposal in R2-9900014 is agreed.', {'R2-9900014': 'partially_agreed'}),
            ('RAN2', 'R2-9900015 agreed with changes. R2-9900016 agreed with changes.',
             {'R2-9900015': 'conditionally_agreed', 'R2-9900016': 'conditionally_agreed'}),
        ]
        for wg, text, expected in cases:
            with self.subTest(wg=wg, text=text):
                rows = self.rows(self.report(text, expected, wg=wg))
                self.assertEqual({r['targetTdocNumber']: r['dispositionCode'] for r in rows}, expected)
                self.validate(rows)

    def test_issue_handling_is_not_whole_document_approval(self):
        text = ('The issues raised in R1-9900001 are agreed to be fixed. '
                'The issues raised in R1-9900002 are agreed to be fixed.')
        rows = self.rows(self.report(text, ['R1-9900001', 'R1-9900002'], group='conclusions'))
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(r['dispositionCode'] == 'partially_agreed' for r in rows))
        self.validate(rows)

    def test_literal_id_does_not_override_source_grounded_identity_conflict(self):
        import decision_disposition as d
        from openpyxl import Workbook
        for wg, target in [('RAN1', 'R1-9900001'), ('RAN1', 'R1-9900002'),
                           ('RAN1', 'R1-9900003'), ('RAN2', 'R2-9900004')]:
            with self.subTest(wg=wg, target=target):
                report = self.report(f'{target} is agreed.', [target], wg=wg)
                decision = report['agreements'][0]
                source = d.decision_source(report, decision, self.root)
                identity = f'{wg}:{decision["decision_id"]}:{target}'
                workbook = Workbook()
                sheet = workbook.active
                sheet.title = 'Fixture'
                fields = {'tdocNumber': target, 'title': 'Different synthetic document'}
                sheet.append(list(fields))
                sheet.append(list(fields.values()))
                master = self.root / f'sources/identity-{self.report_number}.xlsx'
                workbook.save(master)
                workbook.close()
                review = {'dispositionId': identity, 'decisionEvidence': source,
                          'targetIdentityEvidence': {'path': str(master.relative_to(self.root)),
                              'sha256': hashlib.sha256(master.read_bytes()).hexdigest(),
                              'sheet': 'Fixture', 'row': 2, 'fields': fields}}
                path = self.root / f'ontology/input/tsg/RAN/formal/meetings/{wg}/decision_disposition_identity_reviews.json'
                path.parent.mkdir(parents=True, exist_ok=True)
                payload = json.loads(path.read_text()) if path.exists() else {'reviews': []}
                payload['reviews'].append(review)
                path.write_text(json.dumps(payload), encoding='utf-8')
                rows = self.rows(report)
                self.assertEqual(len(rows), 1)
                row = rows[0]
                self.assertEqual((row['dispositionCode'], row['evidenceStatus']), ('ambiguous', 'pending'))
                self.assertEqual(json.loads(row['assessmentMethod'])['sourceDispositionCode'], 'agreed')
                self.validate(rows)
                forged = copy.deepcopy(row)
                forged['assessmentMethod'] = json.dumps(dict(json.loads(row['assessmentMethod']), identityStatus='confirmed'))
                with self.assertRaises(ValueError):
                    self.validate([forged])
                original = master.read_bytes()
                try:
                    master.write_bytes(b'changed synthetic identity evidence')
                    with self.assertRaisesRegex(ValueError, 'Identity-review target source changed'):
                        self.validate(rows)
                finally:
                    master.write_bytes(original)

    def test_content_scope_and_future_disposition_remain_distinct(self):
        cases = [('The content in R1-9900001 is agreed.', 'partially_agreed'),
                 ('R1-9900001 will be agreed at the next fixture meeting.', 'ambiguous'),
                 ('The assumption in R1-9900001 is agreed.', 'partially_agreed')]
        for text, expected in cases:
            with self.subTest(text=text):
                rows = self.rows(self.report(text, ['R1-9900001']))
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]['dispositionCode'], expected)
                self.validate(rows)

    def test_revision_output_does_not_inherit_the_revised_disposition(self):
        text = 'R1-9900001 is revised in R1-9900002 to update the fixture.'
        self.assertEqual(classify_statement(text, 'R1-9900001')[0], 'revised')
        self.assertEqual(classify_statement(text, 'R1-9900002')[0], 'ambiguous')
        self.assertEqual(classify_statement('Draft CR revised in R1-9900003.', 'R1-9900003')[0], 'ambiguous')
        self.assertEqual(classify_statement('R4-9900004 was revised to R4-9900004.', 'R4-9900004')[0], 'revised')

    def test_approval_coordinated_with_a_revision_output_revises_the_subject(self):
        text = 'R2-9900001 was agreed as a baseline and revised in R2-9900002'
        self.assertEqual(classify_statement(text, 'R2-9900001', subject=True)[::2],
                         ('revised', 'explicit_target_coordinated_revision_output'))
        self.assertEqual(classify_statement(text, 'R2-9900002', subject=True)[0], 'ambiguous')
        self.assertEqual(classify_statement('R2-9900001 is endorsed and revised to R2-9900002.', 'R2-9900001')[0], 'revised')
        self.assertEqual(classify_statement('R2-9900001 will be agreed as a baseline and revised in R2-9900002.',
                                            'R2-9900001')[0], 'ambiguous')
        other = 'R5-9900001 is approved. CR R4-9900002 was agreed as a baseline and revised to R4-9900003.'
        self.assertEqual(classify_statement(other, 'R5-9900001')[::2], ('agreed', 'explicit_target_predicate'))

    def test_explicit_scopes_are_revalidated_against_source_bytes(self):
        cases = [('R1-9900001 is agreed.', 'agreed', 'whole_target'),
                 ('R1-9900001 will be agreed at the next fixture meeting.', 'ambiguous', 'undetermined'),
                 ('Adopt TP #7 in Section 9 of R1-9900001.', 'partially_agreed', 'subdocument'),
                 ('The proposal in R1-9900001 is endorsed.', 'endorsed', 'subdocument')]
        for text, code, scope in cases:
            with self.subTest(text=text):
                rows = self.rows(self.report(text, ['R1-9900001']))
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]['dispositionCode'], code)
                self.assertEqual(json.loads(rows[0]['assessmentMethod'])['scope'], scope)
                self.validate(rows)

    def test_withdrawal_and_approval_are_bound_to_separate_source_targets(self):
        rows = self.withdrawal_rows()
        self.assertEqual({r['dispositionTarget']: r['dispositionCode'] for r in rows},
                         {'tdoc:R1-9900001': 'withdrawn', 'tdoc:R1-9900002': 'agreed'})

    def test_final_cr_list_does_not_approve_historical_references(self):
        final = ['R1-9900001', 'R1-9900002', 'R1-9900003']
        historical = ['R1-9900004', 'R1-9900005', 'R1-9900006']
        text = ('Final CRs agreed in R1-9900001, R1-9900002 and R1-9900003. '
                'The fixture references R1-9900004, R1-9900005 and R1-9900006 from the previous meeting.')
        rows = self.rows(self.report(text, final + historical))
        self.assertEqual({r['targetTdocNumber'] for r in rows if r['dispositionCode'] == 'agreed'}, set(final))
        self.assertEqual(len(rows), 6)
        self.assertTrue(all(r['evidenceStatus'] == 'pending' for r in rows if r['targetTdocNumber'] in historical))
        self.validate(rows)

    def test_inflated_code_or_invented_quote_rejected_before_loading(self):
        original = self.withdrawal_rows()[0]
        for field, value in [('dispositionCode', 'agreed'),
                             ('evidenceQuote', original['evidenceQuote'] + '\nInvented fixture approval'),
                             ('evidenceSha256', '0' * 64), ('evidenceLocator', 'word/document.xml accepted body blocks [1,2)')]:
            with self.subTest(field=field):
                row = copy.deepcopy(original)
                row[field] = value
                with self.assertRaises(ValueError):
                    self.validate([row])

    def test_loader_independently_checks_source_before_any_database_access(self):
        import decision_disposition as d
        from functools import partial
        row = copy.deepcopy(self.withdrawal_rows()[0])
        row['targetTdocNumber'] = 'R1-9999999'
        # 같은 실제 검증기에 임시 입력 경로를 지정한다. 판정 결과를 대체하지 않는다.
        with patch.object(d, 'ROOT', self.root), \
                patch.object(d, 'validate_dispositions', partial(validate_dispositions, root=self.root)):
            with self.assertRaisesRegex(ValueError, 'Disposition target identity mismatch'):
                load_dispositions(None, [row])

    def test_subject_and_resolution_attribution_cannot_be_forged(self):
        original = self.withdrawal_rows()[0]
        for field, value in [('dispositionOf', 'tdoc:resolution/AGR-999-other-001'),
                             ('evidenceStatus', 'pending')]:
            with self.subTest(field=field):
                row = copy.deepcopy(original)
                row[field] = value
                with self.assertRaises(ValueError):
                    self.validate([row])


class ApprovalQuestions(unittest.TestCase):
    def test_keyword_or_reference_only_queries_do_not_prove_approval(self):
        q = {'question': 'CR이 승인된 Agreement 목록은?',
             'cypher': "MATCH (a:Agreement)-[:REFERENCES]->(cr:CR) WHERE a.content CONTAINS 'agreed' RETURN cr"}
        self.assertTrue(approval_contract_defects(q))

    def test_all_current_authored_cqs_match_approval_contract(self):
        count = 0
        for path in (ROOT / 'scripts/common/bootstrap/seeds/formal-cq').glob('RAN[1-5]/phase-[1-5].json'):
            for cq in json.loads(path.read_text())['questions']:
                self.assertEqual(approval_contract_defects(cq), [], (str(path), cq['id']))
                count += 1
        self.assertEqual(count, 654)

    def test_reference_questions_preserve_reference_semantics(self):
        self.assertEqual(approval_contract_defects({'question': 'Agreement가 참조한 Tdoc 목록은? (CR 승인 관련 원본 추적)',
            'cypher': 'MATCH(a:Agreement)-[:REFERENCES]->(t:Tdoc) RETURN t'}), [])


if __name__ == '__main__':
    unittest.main()
