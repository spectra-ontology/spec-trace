#!/usr/bin/env python3
"""test_document_decision_source.py — 원문 문서 entry의 경계·처분 회귀 검사.

Spec: docs/tsg/build/standards/decision_disposition_contract.md.
Ontology: document Decision events qualify their own checked document or named output.
Cycle: actual accepted DOCX entries + adverse status fields → parser/classifier checks.
배경: 논의 속 문서 인용·수정본 승인·기술 Decision은 서로 다른 대상과 범위다.
사용: python3 -m unittest discover -s scripts/tsg/RAN/formal/common -p test_document_decision_source.py.
LLM 호출: 없음.
"""
import json
import copy
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

import decision_disposition as d
from document_decision_source import (classify_document_decision, document_decisions,
                                     annex_cr_table_events, annex_source_evidence,
                                     approval_outputs, incorporation, INCORPORATION_RULE,
                                     IN_PRINCIPLE_WORD, LIST_LINE_METHOD, output_qualifiers_end)
from unittest.mock import patch


def event(text, target='R5-213430', formal_count=1):
    return {'subject_tdoc': target, 'meeting_id': 'RAN5#91', 'document_entry': {
        'decisionText': 'Decision: ' + text, 'formalDocumentDecisionParagraphs': formal_count}}


class DocumentStatusRules(unittest.TestCase):
    def code(self, text, target=None):
        return classify_document_decision(event(text), target)[0]

    def test_observed_past_email_fields(self):
        for text in ['The document was email approved.', 'The document was for email approved.',
                     'The document was email agreed.']:
            self.assertEqual(self.code(text), 'agreed', text)
        self.assertEqual(self.code('The document was email endorsed.'), 'endorsed')
        self.assertEqual(self.code('The document was for revised to R5-213682.'), 'revised')
        self.assertEqual(self.code('Revised to R5-213682.'), 'revised')

    def test_email_field_preserves_modality_scope_and_history(self):
        for text in ['The document will be email approved.',
                     'The document was not email approved.',
                     'The document was email approved if the CR is corrected.',
                     'The document was email approved in RAN5#90.',
                     'The document was previously email approved.']:
            self.assertNotEqual(self.code(text), 'agreed', text)
        self.assertEqual(self.code('The document was email approved with changes.'), 'conditionally_agreed')
        self.assertEqual(self.code('The document was email approved except section 2.'), 'partially_agreed')

    def test_named_output_approval_belongs_to_output(self):
        for text in ['The document was email approved as R5-213682.',
                     'The document was revised and email approved as R5-213682.',
                     'The document was revised and approved as R5-213682.']:
            self.assertEqual(self.code(text), 'revised', text)
            self.assertEqual(self.code(text, 'R5-213682'), 'agreed', text)
        # The change phrase after a distinct output number describes how the output was produced.
        changed = 'The document was email approved as R5-213682 with changes.'
        self.assertEqual(self.code(changed, 'R5-213682'), 'agreed')

    def test_named_output_keeps_unresolved_context_pending(self):
        for text in ['The document will be approved as R5-213682.',
                     'The document was not approved as R5-213682.',
                     'The document was approved as R5-213682 if it is corrected.',
                     'The document was previously approved as R5-213682.',
                     'The document was approved as R5-213682 in RAN5#90.']:
            self.assertEqual(self.code(text), 'ambiguous', text)
            self.assertNotEqual(self.code(text, 'R5-213682'), 'agreed', text)

    def test_technical_and_multiple_formal_decisions_remain_pending(self):
        self.assertEqual(self.code('20.1 and 20.2 shall be merged.'), 'ambiguous')
        self.assertEqual(classify_document_decision(event('The document was agreed.', formal_count=2))[0], 'ambiguous')

    def test_explicit_formal_nonapproval_and_qualified_fields(self):
        statuses = {'not treated': 'not_treated', 'merged': 'merged',
                    'not concluded': 'not_concluded', 'replied to': 'replied_to',
                    'technically endorsed': 'endorsed', 'Partially approved': 'partially_agreed',
                    'Partially-approved': 'partially_agreed'}
        for status, expected in statuses.items():
            self.assertEqual(self.code('The document was ' + status + '.'), expected)
        self.assertEqual(self.code('The document was merged to R5-213682.'), 'merged')
        self.assertEqual(self.code('The document was replied to in R5-213682.'), 'replied_to')
        self.assertEqual(self.code('The document was merged to R5-213682.', 'R5-213682'), 'ambiguous')
        self.assertEqual(self.code('The document was replied to in R5-213682.', 'R5-213682'), 'ambiguous')
        for text in ['The document will be merged.', 'The document was not merged.',
                     'The document was merged if the CR is corrected.',
                     'The document was previously merged.', 'The document was merged in RAN5#90.',
                     'The document was Partially approved if corrected.',
                     'The document was technically endorsed in RAN5#90.']:
            self.assertEqual(self.code(text), 'ambiguous', text)

    def test_actual_ran3_formal_extended_status_fields(self):
        cases = [(100, 'R3-183546', 324, 'not_treated'),
                 (100, 'R3-182701', 1107, 'merged'),
                 (101, 'R3-185026', 4408, 'not_concluded'),
                 (105, 'R3-194552', 452, 'endorsed'),
                 ('105bis', 'R3-194910', 2944, 'replied_to'),
                 (95, 'R3-170356', 2343, 'partially_agreed')]
        for number, target, index, expected in cases:
            source = d.ROOT / f'ontology/input/tsg/RAN/formal/meetings/RAN3/Final_Report/Final_Report_RAN3-{number}.docx'
            texts, _, _ = d.source_blocks(str(source.resolve()))
            actual = event('', target=target)
            actual['meeting_id'] = f'RAN3#{number}'
            actual['document_entry']['decisionText'] = texts[index]
            self.assertEqual(classify_document_decision(actual)[0], expected, texts[index])
            d.source_blocks.cache_clear()

    def test_actual_ran4_observed_withdrawn_typo_keeps_scope(self):
        source = d.ROOT / 'ontology/input/tsg/RAN/formal/meetings/RAN4/Final_Report/Final_Report_RAN4-83.docx'
        texts, _, _ = d.source_blocks(str(source.resolve()))
        self.assertTrue(texts[2041].startswith('R4-1705855\t'))
        self.assertIn('was withdrawn due to the collision of the t-doc number', texts[2045])
        self.assertEqual(texts[2047], 'Decision: \t\tThe document was withdrrawn.')
        actual = event('', target='R4-1705855')
        actual['meeting_id'] = 'RAN4#83'
        actual['document_entry']['decisionText'] = texts[2047]
        self.assertEqual(classify_document_decision(actual)[0], 'withdrawn')
        for text in ['The document will be withdrrawn.',
                     'The document was not withdrrawn.',
                     'The document was withdrrawn if corrected.',
                     'The document was previously withdrrawn.',
                     'The document was withdrrawn in RAN4#82.']:
            self.assertEqual(self.code(text), 'ambiguous', text)
        d.source_blocks.cache_clear()


def list_line_event(text, target='R2-1904609'):
    return {'subject_tdoc': target, 'meeting_id': 'RAN2#105bis', 'document_entry': {
        'decisionText': '=>\t' + text, 'formalDocumentDecisionParagraphs': 1,
        'typeEvidenceMethod': LIST_LINE_METHOD, 'statusLineFollowsHeader': True,
        'emptyParagraphBeforeStatusLine': False}}


class QualifiedRevisionOutputs(unittest.TestCase):
    """An approval that names its output with a qualifier before the number revises the header."""
    HEADER, OUTPUT = 'R2-1904609', 'R2-1905373'

    def codes(self, text):
        row = list_line_event(text, self.HEADER)
        if text.startswith('Decision:'):
            row['document_entry']['decisionText'] = text
        elif text.startswith('The CR '):
            # `The CR` names the header document when the TDoc list registers it as a CR.
            row['document_entry']['listedCR'] = {'crNumber': '1234', 'spec': '38.331'}
        return {target: classify_document_decision(row, target)[0]
                for target in [self.HEADER] + approval_outputs(row['document_entry']['decisionText'])}

    def test_leading_qualifier_names_the_output(self):
        cases = {'Agreed in principle in R2-1905373': 'conditionally_agreed',
                 'Agreed-in-principle in R2-1905373': 'conditionally_agreed',
                 'agreed in-principle in R2-1905373': 'conditionally_agreed',
                 'Agreed (in principle) in R2-1905373': 'conditionally_agreed',
                 'Agreed in principle (with the changes above) in R2-1905373': 'conditionally_agreed',
                 'Agreed in principle unseen in R2-1905373': 'conditionally_agreed',
                 'Agreed with these changes as R2-1905373 (Rel-16)': 'agreed',
                 'Agreed with this change as R2-1905373': 'agreed',
                 'Agreed with the changes above in R2-1905373': 'agreed',
                 'Agreed without the second change in R2-1905373': 'agreed',
                 'Agreed unseen in R2-1905373': 'agreed',
                 'Agreed as CR0223 to 36.212 (Rel-14) in R2-1905373': 'agreed',
                 'Agreed in a new CR 1432 rev6 in R2-1905373': 'agreed',
                 'Agreed as v0.6.0 in R2-1905373': 'agreed'}
        for text, expected in cases.items():
            self.assertEqual(self.codes(text), {self.HEADER: 'revised', self.OUTPUT: expected}, text)

    def test_formal_field_with_leading_change_names_the_output(self):
        text = 'The document was approved with changes as R5-213682.'
        self.assertEqual(classify_document_decision(event(text))[0], 'revised')
        self.assertEqual(classify_document_decision(event(text), 'R5-213682')[0], 'agreed')
        self.assertEqual(approval_outputs('Decision: ' + text), ['R5-213682'])

    def test_change_phrase_reads_the_same_on_either_side_of_the_output(self):
        self.assertEqual(self.codes('Agreed in R2-1905373'), {self.HEADER: 'revised', self.OUTPUT: 'agreed'})
        for before, after in [('Agreed with changes in R2-1905373', 'Agreed in R2-1905373 with changes'),
                              ('Agreed with the change above in R2-1905373', 'The CR is agreed in R2-1905373 with the change above'),
                              ('Agreed with the editorial change above in R2-1905373',
                               'The CR is agreed in R2-1905373 with the editorial change above'),
                              ('Agreed in principle with the changes above in R2-1905373',
                               'The CR is agreed in principle in R2-1905373 with the changes above')]:
            self.assertEqual(self.codes(before), self.codes(after), after)
        self.assertEqual(self.codes('The CR is agreed in R2-1905373 with the change above'),
                         {self.HEADER: 'revised', self.OUTPUT: 'agreed'})
        self.assertEqual(self.codes('Agreed in R2-1905373 in principle with the changes above'),
                         {self.HEADER: 'revised', self.OUTPUT: 'conditionally_agreed'})

    def test_output_descriptor_before_a_trailing_change_phrase(self):
        for text in ['The CR is agreed in R2-1905373 r1 with the change above',
                     'The CR is agreed in R2-1905373 CR rev2 with the changes above',
                     'Agreed in R2-1905373 36213CR0948r1 with addition of clauses affected on CR cover sheet.',
                     'Decision: Final CR is agreed in R2-1905373 (TS36.213, Rel-15, CR1190) with “subframe i” modified to “a subframe”',
                     'Agreed in R2-1905373 38.802 CR0003 Rel-14, F with correction of “base graph” on cover sheet',
                     'Agreed in R2-1905373 (with revision number 1)',
                     'Decision: The CR is agreed in R2-1905373, with the following changes:']:
            # A `Decision:` field names no header subject (`Final CR is agreed in Y`), so only the
            # output's reading is stated there.
            expected = {self.OUTPUT: 'agreed'} if text.startswith('Decision:') else {self.HEADER: 'revised', self.OUTPUT: 'agreed'}
            self.assertEqual({k: v for k, v in self.codes(text).items() if k in expected}, expected, text)

    def test_parenthesized_number_after_a_change_phrase_is_the_output(self):
        for text in ['Agreed with the above change (R2-1905373).', 'Agreed with the above correction (R2-1905373)',
                     'Agreed with the correction of cover page (including typo and CR affects) (R2-1905373)',
                     'Agreed with adding “and reception” after “transmission” in the field description (R2-1905373)']:
            self.assertEqual(self.codes(text), {self.HEADER: 'revised', self.OUTPUT: 'agreed'}, text)
        self.assertEqual(self.codes('Agreed with the above change (R2-1905373)'),
                         self.codes('Agreed with the above change in R2-1905373'))
        # Without a change before it, a parenthesized number names no output.
        for text in ['Agreed (R2-1905373)', 'Agreed in principle (R2-1905373)', 'Agreed only with NOTE (R2-1905373)',
                     'Agreed with the proposal (R2-1905373)', 'Agreed with the changes proposed (R2-1905373)',
                     'The CR is agreed (and R2-1905373 for revision is withdrawn)']:
            self.assertEqual(approval_outputs(text), [], text)
            self.assertNotEqual(self.codes(text)[self.HEADER], 'revised', text)

    def test_change_phrase_after_the_output_may_name_where_the_change_came_from(self):
        # The number after the change belongs to the change; the output is already named.
        for text in ['Agreed in R2-1905373, with reflecting the change in R2-1905380',
                     'Agreed in R2-1905373, with the changes from R2-1905380']:
            self.assertEqual(self.codes(text), {self.HEADER: 'revised', self.OUTPUT: 'agreed'}, text)
        self.assertEqual(output_qualifiers_end(', with reflecting the change in R2-1905380'),
                         len(', with reflecting the change in R2-1905380'))

    def test_bare_cr_number_after_the_output_is_its_descriptor(self):
        for text in ['Agreed in R2-1905373 CR0013, with correct deletion of the whole table',
                     'Agreed in R2-1905373 CR0013 rev 1 to TS 38.211', 'Agreed in R2-1905373 CR#0013']:
            self.assertEqual(self.codes(text), {self.HEADER: 'revised', self.OUTPUT: 'agreed'}, text)

    def test_text_after_the_output_that_is_not_a_change_phrase_is_read_as_stated(self):
        # A condition and a relation to other documents are not changes the output carries.
        self.assertEqual(self.codes('Agreed in R2-1905373, assuming the following update: “collides”')[self.OUTPUT],
                         'conditionally_agreed')
        self.assertEqual(output_qualifiers_end(', with shadow CRs in R2-2403798 and R2-2403799'), 0)
        self.assertEqual(output_qualifiers_end(' (not agreed)'), 0)

    def test_number_that_is_not_the_approved_output_is_not_an_output(self):
        for text in ['Agreed as in R2-1905373', 'Agreed with the proposal in R2-1905373',
                     'Agreed with the changes proposed in R2-1905373', 'Agreed with the changes as in R2-1905373',
                     'Agreed, but then revised by MCC in R2-1905373', 'Agreed and merged in R2-1905373',
                     'Agreed, final version in R2-1905373',
                     'Agreed in a first step as R2-1905373', 'Agreed in principle for all proposals in R2-1905373',
                     'Agreed with the addition of the DTCH in the table as in R2-1905373']:
            self.assertEqual(approval_outputs(text), [], text)
            self.assertNotEqual(self.codes(text)[self.HEADER], 'revised', text)

    def test_baseline_approval_coordinated_with_a_revision_revises_the_header(self):
        # The revision is not an approval output, but `and revised in` is the header's own
        # disposition in the same decision, unlike the later `but then revised by MCC in`.
        text = 'Agreed as a baseline and revised in R2-1905373'
        self.assertEqual(approval_outputs(text), [], text)
        self.assertEqual(self.codes(text)[self.HEADER], 'revised', text)

    def test_change_phrase_does_not_cross_a_nested_approval(self):
        text = 'Agreed with addition of space in last line: agreed in R2-1905373'
        self.assertEqual(self.codes(text), {self.HEADER: 'ambiguous', self.OUTPUT: 'ambiguous'})

    def test_change_phrase_does_not_run_into_a_final_version(self):
        for text in ['Approved with this change, final version in R2-1905373',
                     'Agreed with these changes, final version in R2-1905373']:
            self.assertEqual(approval_outputs(text), [], text)
            self.assertNotEqual(self.codes(text)[self.HEADER], 'revised', text)

    def test_field_that_revises_the_header_keeps_revised_when_its_output_stays_pending(self):
        # A comma or dash join gives the output's approval no clause of its own.
        for text in ['Revised, with this update, agreed unseen in R2-1905373 (rev 1)',
                     'Revised in R2-1905380 – agreed in R2-1905373 as CR0858 to 36.213 Rel-14, F.']:
            self.assertEqual(approval_outputs(text), [self.OUTPUT], text)
            self.assertEqual(self.codes(text), {self.HEADER: 'revised', self.OUTPUT: 'ambiguous'}, text)
        # `The CR is revised` speaks for the header only when the TDoc list registers it as a CR.
        text = 'The CR is revised with the above change and agreed in R2-1905373 unseen.'
        row = list_line_event(text, self.HEADER)
        self.assertEqual(classify_document_decision(row)[::2], ('ambiguous', 'CR_subject_on_header_not_listed_as_CR'))
        row['document_entry']['listedCR'] = {'crNumber': '1234', 'spec': '38.331'}
        self.assertEqual(classify_document_decision(row)[0], 'revised')
        self.assertEqual(classify_document_decision(row, self.OUTPUT)[::2],
                         ('agreed', 'explicit_document_revision_output_clause_approval'))

    def test_output_clause_after_the_header_revision_carries_the_output_approval(self):
        cases = {'Revised for cover sheet update, revision is agreed unseen in R2-1905373': 'agreed',
                 'Revised to be Cat F CR. Agreed in principle in R2-1905373': 'conditionally_agreed'}
        for text, expected in cases.items():
            self.assertEqual(approval_outputs(text), [self.OUTPUT], text)
            self.assertEqual(self.codes(text), {self.HEADER: 'revised', self.OUTPUT: expected}, text)

    def test_output_clause_does_not_decide_a_header_with_another_predicate(self):
        # The output's own clause carries its approval; the header's `Endorsed` is not a revision.
        for text in ['Endorsed and agreed in R2-1905373 by email', 'Endorsed. Final version agreed in R2-1905373']:
            self.assertEqual(self.codes(text), {self.HEADER: 'ambiguous', self.OUTPUT: 'agreed'}, text)
        self.assertEqual(self.codes('Endorsed. Final version agreed in principle in R2-1905373'),
                         {self.HEADER: 'ambiguous', self.OUTPUT: 'conditionally_agreed'})
        self.assertEqual(self.codes('Endorsed. Final version will be agreed in R2-1905373'),
                         {self.HEADER: 'ambiguous', self.OUTPUT: 'ambiguous'})
        row = list_line_event('Endorsed. Final version agreed in R2-1905373 to be included in the running CR', self.HEADER)
        self.assertEqual(classify_document_decision(row, self.OUTPUT)[::2],
                         ('ambiguous', INCORPORATION_RULE))

    def test_source_event_references_the_qualified_output(self):
        import document_decision_source as source
        texts = ['R5-9990001\tFirst listed title\tSource A', 'Type: CR',
                 'Decision: The document was agreed with these changes as R5-9990011.']
        blocks = [ET.Element(source.W + 'p') for _ in texts]
        self.addCleanup(source._EVENT_CACHE.clear)
        source._EVENT_CACHE.clear()
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(d, 'source_blocks', return_value=(texts, 'synthetic qualified output hash', blocks)):
            events, _ = document_decisions({'meeting_id': 'RAN5#994', 'docx_path': 'source.docx'}, Path(directory))
        self.assertEqual(events[0]['referenced_tdocs'], ['R5-9990001', 'R5-9990011'])
        self.assertEqual(classify_document_decision(events[0])[0], 'revised')
        self.assertEqual(classify_document_decision(events[0], 'R5-9990011')[0], 'agreed')

    def test_hyphenated_in_principle_is_conditional(self):
        for text in ['Agreed-in-principle', 'Agreed in-principle', 'Agreed in principle']:
            self.assertEqual(self.codes(text), {self.HEADER: 'conditionally_agreed'}, text)

    def test_misspelled_in_principle_is_conditional(self):
        # The reports' own misspellings of the qualifier carry the same reading, on the header
        # and on a named output alike.
        for spelling in ['inprinciple', 'in princple', 'in principe', 'in principel', 'in principal', 'in priciple']:
            self.assertEqual(self.codes('Agreed ' + spelling), {self.HEADER: 'conditionally_agreed'}, spelling)
            self.assertEqual(self.codes(f'Agreed {spelling} in R2-1905373'),
                             {self.HEADER: 'revised', self.OUTPUT: 'conditionally_agreed'}, spelling)
        # The statement classifier reads the same spellings as the document reader.
        self.assertEqual(d.IN_PRINCIPLE_WORD, IN_PRINCIPLE_WORD)
        for spelling in ['in principle', 'in-principle', 'inprinciple', 'in princple', 'in principel', 'in principal']:
            self.assertEqual(d.classify_statement(f'{self.OUTPUT} is agreed {spelling}', self.OUTPUT)[0],
                             'conditionally_agreed', spelling)
        self.assertEqual(d.classify_statement(f'{self.OUTPUT} is agreed', self.OUTPUT)[0], 'agreed')
        for text in ['Agreed principle', 'Agreed with the principle of option 2', 'Agreed, principal changes only']:
            self.assertNotEqual(self.codes(text)[self.HEADER], 'conditionally_agreed', text)

    def test_incorporation_is_not_whole_unconditional_approval(self):
        # Every phrasing that puts the paper's content into another document: a purpose clause,
        # an active `to include`, a coordinated `and merged into`, a comma-joined finite merge and
        # a parenthesised purpose, whatever the receiving document is.
        for text in ['Agreed to be included in the running CR', 'Agreed to be added to the rapporteur CR',
                     'Agreed to be merged into the MAC running CR', 'Agreed to be included in the RRC rapporteur CR',
                     'Agreed to be merged into R2-1815793', 'Agreed to be included in the running 36.331 CR',
                     'Agreed to be added to the TR', 'Agreed to be added to next version of TR',
                     'Agreed to be added to TS', 'Agreed to be included in revised SI TP',
                     'Agreed to include TP in running CR', 'Agreed to include in the rapporteur CR on EN-DC corrections.',
                     'Agreed changes to be merged into R2-1815793', 'Agreed, merge with rapporteur CR',
                     'Agreed, Merged with the rapporteur CR', 'Agreed and merged into R2-1809143/R2-1808981',
                     'Agreed as "and RA resource selection" and added to the rapporteur CR',
                     'Agreed (To be included in the baseline).']:
            row = list_line_event(text, self.HEADER)
            self.assertEqual(classify_document_decision(row)[::2], ('ambiguous', INCORPORATION_RULE), text)
        self.assertEqual(self.codes('Agreed in R2-1905373 to be included in the running CR'),
                         {self.HEADER: 'revised', self.OUTPUT: 'ambiguous'})
        self.assertEqual(self.codes('Agreed in R2-1905373 to be included in the TR'),
                         {self.HEADER: 'revised', self.OUTPUT: 'ambiguous'})
        # `The CR is agreed and merged into R2-x` on an entry the TDoc list registers as a CR.
        row = list_line_event('The CR is agreed and merged into R2-1809143', self.HEADER)
        row['document_entry']['listedCR'] = {'crNumber': '1234', 'spec': '38.331'}
        self.assertEqual(classify_document_decision(row)[::2], ('ambiguous', INCORPORATION_RULE))

    def test_incorporation_reading_needs_a_receiving_document_and_no_negation(self):
        for text in ['Agreed not to be merged into the running CR', 'Agreed, never to be included in the TR',
                     'Agreed to be included in the next meeting agenda', 'Agreed to include the note',
                     'Agreed to be merged and revised by the rapporteur', 'Agreed with the changes included above']:
            self.assertIsNone(incorporation(text), text)
        # A receiver phrase stops at a clause word: `included in the CR` is the receiver, `which` opens another clause.
        self.assertEqual(incorporation('Agreed to be included in the CR which is endorsed')[0],
                         'to be included in the CR')

    def test_inclusion_rule_leaves_other_predicates(self):
        self.assertEqual(self.codes('Endorsed to be merged in the rapporteur CR'), {self.HEADER: 'endorsed'})
        self.assertEqual(self.codes('Agreed in principle (to be merged into a single LPP CR)'),
                         {self.HEADER: 'conditionally_agreed'})
        self.assertEqual(self.codes('Agreed in principe, to be merged with the rapporteur CR'),
                         {self.HEADER: 'conditionally_agreed'})

    def test_TP_object_approval_accepts_part_of_the_paper(self):
        # `Agreed TP` accepts the text proposal the paper carries, not the whole paper.
        for text in ['Agreed TP and editor will reflect it', 'Agreed TPs, and editors will take care it',
                     'Agreed TPs for 36.211 and 36.300 (not 36.301), and editors will take care it',
                     'Agreed TP, and editors will take care it', 'Approved the text proposal',
                     'Agreed TP to be included in the running CR']:
            row = list_line_event(text, self.HEADER)
            self.assertEqual(classify_document_decision(row)[::2], ('partially_agreed', 'document_TP_object_approval'),
                             text)
        # A TP approval that names another document, or with a condition, keeps its own reading.
        self.assertEqual(self.codes('Agreed TP with changes'), {self.HEADER: 'conditionally_agreed'})
        row = list_line_event('Agreed TP in R2-1702219', self.HEADER)
        self.assertNotEqual(classify_document_decision(row)[2], 'document_TP_object_approval')

    def test_approval_of_another_bare_number_leaves_the_header_unresolved(self):
        # No `in`/`as` relates the header to the number, and the number is not an output.
        for text in ['Agreed R2-1702219', 'Agreed R2-1702219 CR Rev 1', 'Approved CR R2-1702219',
                     'Agreed in principle R2-1702219']:
            self.assertEqual(approval_outputs(text), [], text)
            row = list_line_event(text, self.HEADER)
            self.assertEqual(classify_document_decision(row)[::2],
                             ('ambiguous', 'approval_of_another_number_without_relation'), text)
        row = list_line_event('The CR is agreed R2-2313963 with the changes above', self.HEADER)
        row['document_entry']['listedCR'] = {'crNumber': '1234', 'spec': '38.331'}
        self.assertEqual(classify_document_decision(row)[::2], ('ambiguous', 'approval_of_another_number_without_relation'))
        # The header's own number after the approval is the header itself.
        self.assertEqual(self.codes('Agreed R2-1904609'), {self.HEADER: 'agreed'})


class OutputClauseInLongerField(unittest.TestCase):
    """An approval clause that names an output inside a longer Decision field settles that output alone."""
    HEADER, OUTPUT, SECOND = 'R1-1706000', 'R1-1706707', 'R1-1706708'

    def codes(self, text):
        row = {'subject_tdoc': self.HEADER, 'meeting_id': 'RAN1#89', 'document_entry': {
            'decisionText': 'Decision: ' + text, 'formalDocumentDecisionParagraphs': 1}}
        return {target: classify_document_decision(row, target)[0]
                for target in [self.HEADER] + approval_outputs(row['document_entry']['decisionText'])}

    def test_output_clause_after_another_statement_is_read_on_the_output(self):
        cases = {'The draft LS is endorsed. Final LS is approved in R1-1706707.': 'agreed',
                 'The draft LS is endorsed, final LS is approved in R1-1706707.': 'agreed',
                 'The draft CR is endorsed & final CR is agreed in R1-1706707.': 'agreed',
                 'The draft CR is endorsed.and final CR is agreed in R1-1706707 (38.214, CR0029).': 'agreed',
                 'As per email decision posted on May 20th, the final CR is agreed in R1-1706707.': 'agreed',
                 'The CR is endorsed. Final CR is agreed as CR0779r1 to 36.213 (Rel-14, F) in R1-1706707.': 'agreed',
                 # A change phrase after the output number describes how the output was produced.
                 'The draft LS is endorsed. Final LS is approved in R1-1706707 with the following updates: x.':
                     'agreed',
                 'The draft CR is endorsed. Final CR is agreed in R1-1706707 (TS36.212, Rel-15, CR1267) with the '
                 'Summary of Change section in the header modified to:': 'agreed',
                 'The draft CR is endorsed. Final CR is agreed in R1-1706707 (38.214, CR0027), assuming the following '
                 'updates:': 'conditionally_agreed',
                 # A condition on the endorsed draft does not qualify the final output approved after it.
                 'The draft LS is endorsed, assuming "RAN1 meeting" modified to "RAN WG1 meeting". Final LS is '
                 'approved in R1-1706707.': 'agreed',
                 'The draft CR is endorsed. Final CR is agreed in principle in R1-1706707.': 'conditionally_agreed'}
        for text, expected in cases.items():
            self.assertEqual(self.codes(text), {self.HEADER: 'ambiguous', self.OUTPUT: expected}, text)

    def test_noted_header_and_agreed_output_are_separate_statements(self):
        for text in ['The document is noted and agreed as CR0216 to 36.211 in R1-1706707.',
                     'The document is noted. Agreed as CR0560 to 36.213 in R1-1706707.']:
            self.assertEqual(self.codes(text), {self.HEADER: 'ambiguous', self.OUTPUT: 'agreed'}, text)

    def test_each_coordinated_clause_settles_its_own_output(self):
        text = 'CR0751r1 to 36.213 is agreed in R1-1706707 and CR0752r1 to 36.213 is agreed in R1-1706708.'
        self.assertEqual(self.codes(text), {self.HEADER: 'ambiguous', self.OUTPUT: 'agreed', self.SECOND: 'agreed'})

    def test_clause_that_does_not_settle_its_output_stays_pending(self):
        for text in ['The CR is endorsed. Final CR to be prepared and agreed as CR0325 to 36.211 in R1-1706707',
                     'The draft LS is endorsed (assuming RAN4 being deleted from ACTION) and final LS is approved in '
                     'R1-1706707.',
                     'The document is noted, agreed in R1-1706707.',
                     'The draft CR is endorsed. Final CR is agreed in R1-1706707 (38.214, CR0151). Decision is '
                     'reverted, and therefore R1-1706707 is considered withdrawn.',
                     'The document is noted, further revised and agreed in R1-1706707. The FFS parts in R1-1706707 '
                     'are for email discussion.',
                     'Final LS is approved in R1-1706707, revised post-meeting in R1-1706800 due to a typo.']:
            self.assertEqual(self.codes(text)[self.OUTPUT], 'ambiguous', text)
        # Related clauses (`then further agreed as rev1`) leave both outputs pending.
        text = 'The document is noted and agreed as CR0216 to 36.211 in R1-1706707, then further agreed as rev1 in R1-1706708.'
        self.assertEqual(self.codes(text), {self.HEADER: 'ambiguous', self.OUTPUT: 'ambiguous', self.SECOND: 'ambiguous'})
        # An output revised again in its own clause stays pending; the final output keeps its approval.
        text = ('The document is endorsed and final version is approved in R1-1706707, further revised to correct '
                'Rel and WI code. Finally approved in R1-1706708.')
        self.assertEqual(self.codes(text), {self.HEADER: 'ambiguous', self.OUTPUT: 'ambiguous', self.SECOND: 'agreed'})


class SyntheticDocumentCache(unittest.TestCase):
    def test_reusing_source_bytes_preserves_each_report_meeting(self):
        import document_decision_source as source
        texts = ['R5-9990001 Synthetic title', 'Type: CR', 'Decision: The document was agreed.']
        blocks = [ET.Element(source.W + 'p') for _ in texts]
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(d, 'source_blocks', return_value=(texts, 'synthetic source hash', blocks)):
            root = Path(directory)
            first, _ = document_decisions({'meeting_id': 'RAN5#991', 'docx_path': 'source.docx'}, root)
            second, _ = document_decisions({'meeting_id': 'RAN5#992', 'docx_path': 'source.docx'}, root)
        self.assertEqual(first[0]['meeting_id'], 'RAN5#991')
        self.assertEqual(second[0]['meeting_id'], 'RAN5#992')
        self.assertTrue(first[0]['decision_id'].startswith('DOC-991-'))
        self.assertTrue(second[0]['decision_id'].startswith('DOC-992-'))


class ListLineHeaders(unittest.TestCase):
    """A header without Type or Source metadata is accepted on the TDoc list's own title."""
    TEXTS = ['R5-9990001\tFirst listed title\tSource A', 'Decision: CR0017 to 38.202 is agreed.',
             'R5-9990002\tA title the list does not carry\tSource B', 'Decision: The document is noted.',
             'R5-9990003\tThird listed title\tSource C', 'Decision: The document is noted.']
    LISTED = {'R5-9990001': ('first listed title', '0017', '38.202'),
              'R5-9990002': ('second listed title', None, ''),
              'R5-9990003': ('third listed title', None, '')}

    def source(self, listed):
        import document_decision_source as source
        blocks = [ET.Element(source.W + 'p') for _ in self.TEXTS]
        self.addCleanup(source._EVENT_CACHE.clear)
        source._EVENT_CACHE.clear()
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(d, 'source_blocks', return_value=(self.TEXTS, 'synthetic list-line hash', blocks)), \
                patch.object(source, '_list_titles', return_value=(listed, 'synthetic list hash')):
            return document_decisions({'meeting_id': 'RAN5#993', 'docx_path': 'source.docx'}, Path(directory))

    def test_listed_title_binds_each_decision_to_its_nearest_header(self):
        events, stats = self.source(self.LISTED)
        self.assertEqual([(e['subject_tdoc'], e['body_blocks']) for e in events],
                         [('R5-9990001', [0, 2]), ('R5-9990003', [4, 6])])
        self.assertEqual(stats['listLineHeaders'], 2)
        self.assertEqual(events[0]['document_entry']['listedCR'], {'crNumber': '0017', 'spec': '38.202'})
        self.assertNotIn('listedCR', events[1]['document_entry'])

    def test_noted_document_with_own_cr_agreed_reads_as_agreed(self):
        own, _ = self.source(self.LISTED)
        def read(text, listed=True):
            entry = {**own[0]['document_entry'], 'decisionText': 'Decision: ' + text}
            if not listed:
                entry.pop('listedCR')
            return classify_document_decision({**own[0], 'document_entry': entry})[::2]
        for text in ['The document is noted and CR0017 to 38.202 is agreed.',
                     'The document is noted and Rel-15 CR0017 to 38.202 is agreed.',
                     'The document is noted and shadow CR0017 to 38.202 Rel-16 is agreed.',
                     'The document is noted and CR0017 cat F to 38.202 (Rel-15) is agreed.',
                     'The document is noted and CR0017 to Rel-15 38.202 is agreed']:
            self.assertEqual(read(text), ('agreed', 'noted_document_own_CR_descriptor_agreement'), text)
        for text in ['The document is noted and CR0017r1 to 38.202 is agreed.',
                     'The document is noted and CR0018 to 38.202 is agreed.',
                     'The document is noted and CR0017 to 38.212 is agreed.',
                     'The document is noted and CR0017 to 38.202 is agreed in principle.',
                     'The document is noted and CR0017 to 38.202 is agreed. Cover sheet to be corrected by MCC.',
                     'The document is noted and agreed as CR0017 to 38.202 in R5-9990009.']:
            self.assertEqual(read(text), ('ambiguous', 'noted_document_CR_agreement_requires_adjudication'), text)
        second = ('ambiguous', 'noted_document_with_second_outcome_requires_adjudication')
        for text, listed in [('The document is noted and CR0017 to 38.202 is not agreed.', True),
                             ('The document is noted and the TP is agreed.', True),
                             ('The document is noted and CR0017 to 38.202 is agreed.', False),
                             ('The document is noted and agreed as CR0216 to 36.211 in R5-9990009.', False),
                             ('The document is noted. Agreed as CR0233 to 36.211 in R5-9990009.', False),
                             ('The document is noted, revised in R5-9990009 and agreed as CR0236 to 36.211 in:', False),
                             ('The document is noted. Further revised in R5-9990009.', False),
                             ('The document is noted and LS is agreed.', False),
                             ('The document is noted and the draft CR is endorsed.', False),
                             ('The document (CR0246 to 36.211) is noted and revised in:', False),
                             ('The document (TR38.802 v0.2.1) is noted and endorsed as version 0.3.0 in R5-9990009.', False),
                             ('The document (RAN3 response to RAN1 LS in R5-9990009) is noted. RAN3 has agreed to update '
                              'its specifications.', False)]:
            self.assertEqual(read(text, listed), second, text)
        self.assertEqual(read('The document (CR0017 to 38.202) is noted and CR0017 to 38.202 is agreed.'),
                         ('agreed', 'noted_document_own_CR_descriptor_agreement'))
        for text in ['The document is noted.', 'The document is noted for information.',
                     'The document was noted (some proposals to be discussed offline)',
                     'The document (draft LS) is noted.']:
            self.assertEqual(read(text, listed=False)[0], 'noted', text)

    def test_unlisted_documents_produce_no_event(self):
        events, stats = self.source({})
        self.assertEqual(events, [])
        self.assertEqual(stats.get('listLineHeaders', 0), 0)

    def test_named_cr_agreement_requires_the_header_documents_own_cr(self):
        own, _ = self.source(self.LISTED)
        self.assertEqual(classify_document_decision(own[0])[::2], ('agreed', 'explicit_own_CR_descriptor_agreement'))
        for number, spec in [('0018', '38.202'), ('0017', '38.212')]:
            other, _ = self.source({**self.LISTED, 'R5-9990001': ('first listed title', number, spec)})
            self.assertEqual(classify_document_decision(other[0])[::2],
                             ('ambiguous', 'named_CR_differs_from_header_document'))

    def test_listed_line_quoted_inside_an_open_fielded_entry_starts_no_entry(self):
        texts = ['R5-9990004\tDiscussion paper', 'Type: discussion\t\tFor: Endorsement', 'Abstract:',
                 'R5-9990001\tFirst listed title\t38.202', 'Decision: The document was noted.',
                 'R5-9990003\tThird listed title', 'Decision: The document was agreed.']
        with patch.object(self, 'TEXTS', texts):
            events, stats = self.source(self.LISTED)
        self.assertEqual([(e['subject_tdoc'], e['body_blocks']) for e in events],
                         [('R5-9990004', [0, 5]), ('R5-9990003', [5, 7])])
        self.assertEqual(stats['listLineHeaders'], 1)

    def status_events(self, texts, listed=None):
        with patch.object(self, 'TEXTS', texts):
            return self.source(listed or self.LISTED)[0]

    def test_label_less_status_lines_are_fields_of_list_line_entries_only(self):
        events = self.status_events([
            'R5-9990001\tFirst listed title\tSource A', '=>\tThe CR is agreed',
            'R5-9990003\tThird listed title\tSource C', '[218] Noted',
            'R5-9990004\tFielded paper', 'Type: discussion\t\tFor: Endorsement', 'Noted'])
        self.assertEqual([(e['subject_tdoc'], classify_document_decision(e)[0]) for e in events],
                         [('R5-9990001', 'agreed'), ('R5-9990003', 'noted')])

    def test_caption_lines_and_cr_subject_on_non_cr_header_are_not_dispositions(self):
        events = self.status_events([
            'R5-9990003\tThird listed title\tSource C', 'Withdrawn contributions:', '=> Not pursued CRs:',
            '=> The CR is endorsed'])
        self.assertEqual([classify_document_decision(e)[::2] for e in events],
                         [('ambiguous', 'CR_subject_on_header_not_listed_as_CR')])

    def test_bare_status_word_after_discussion_binds_only_in_a_cr_entry(self):
        cr, paper = self.status_events([
            'R5-9990001\tFirst listed title\tSource A', 'Company X asks about the release.', 'Agreed',
            'R5-9990003\tThird listed title\tSource C', 'Proposal 1: use option A.', 'Agreed'])
        self.assertEqual(classify_document_decision(cr)[0], 'agreed')
        self.assertEqual(classify_document_decision(paper)[::2],
                         ('ambiguous', 'bare_status_line_after_discussion_in_non_CR_entry'))
        marked, adjacent = self.status_events([
            'R5-9990003\tThird listed title\tSource C', 'Proposal 1: use option A.', '=> Noted',
            'R5-9990002\tSecond listed title\tSource B', 'Noted'])
        self.assertEqual([classify_document_decision(e)[0] for e in (marked, adjacent)], ['noted', 'noted'])

    def test_bare_status_word_after_an_empty_paragraph_names_no_document(self):
        detached, marked = self.status_events([
            'R5-9990001\tFirst listed title\tSource A', '', 'Not treated.',
            'R5-9990003\tThird listed title\tSource C', '', '=> Noted'])
        self.assertEqual(classify_document_decision(detached)[::2],
                         ('ambiguous', 'bare_status_line_detached_by_empty_paragraph'))
        self.assertEqual(classify_document_decision(marked)[0], 'noted')

    def test_actual_ran1_group_not_treated_line_stays_pending(self):
        report = json.loads((d.ROOT / 'ontology/output/tsg/RAN/formal/parsed_reports/RAN1/RAN1_85.json').read_text())
        events, _ = document_decisions(report)
        self.addCleanup(d.source_blocks.cache_clear)
        line = next(e for e in events if e['subject_tdoc'] == 'R1-164311')
        self.assertEqual(line['document_entry']['decisionText'], 'Not treated.')
        self.assertEqual(classify_document_decision(line)[::2],
                         ('ambiguous', 'bare_status_line_detached_by_empty_paragraph'))

    def test_actual_ran5_quoted_cr_list_keeps_the_decision_with_its_discussion_paper(self):
        report = json.loads((d.ROOT / 'ontology/output/tsg/RAN/formal/parsed_reports/RAN5/RAN5_103.json').read_text())
        events, _ = document_decisions(report)
        self.addCleanup(d.source_blocks.cache_clear)
        self.assertEqual({e['subject_tdoc'] for e in events if e['document_entry']['decisionBlock'] == 10134},
                         {'R5-242177'})

    def test_named_cr_sentence_forms(self):
        from document_decision_source import named_cr_agreement
        self.assertEqual(named_cr_agreement('As per email decision posted on August 28th, CR0017 to 38.202 is agreed.'),
                         ('38.202', 17))
        for text in ['The document is noted and CR0550r1 to 36.213 is agreed.',
                     'CR0017 to 38.202 is agreed in principle.',
                     'CR0017 to 38.202 and CR0018 to 38.212 are agreed.']:
            self.assertIsNone(named_cr_agreement(text), text)

    def test_actual_ran1_email_decision_names_its_own_cr(self):
        report = json.loads((d.ROOT / 'ontology/output/tsg/RAN/formal/parsed_reports/RAN1/RAN1_102-e.json').read_text())
        events, _ = document_decisions(report)
        self.addCleanup(d.source_blocks.cache_clear)
        found = [e for e in events if e['subject_tdoc'] == 'R1-2007360']
        self.assertEqual(sorted(e['document_entry'].get('sourceKind') == 'annex_cr_table_row' for e in found), [False, True])
        rows = [e for e in found if e['document_entry'].get('sourceKind') != 'annex_cr_table_row']
        self.assertEqual(rows[0]['document_entry']['listedCR'], {'crNumber': '0017', 'spec': '38.202'})
        self.assertEqual(classify_document_decision(rows[0])[0], 'agreed')

    def test_actual_ran4_decision_moves_from_the_preceding_document_to_its_own_header(self):
        report = json.loads((d.ROOT / 'ontology/output/tsg/RAN/formal/parsed_reports/RAN4/RAN4_102-e.json').read_text())
        events, _ = document_decisions(report)
        self.addCleanup(d.source_blocks.cache_clear)
        at_block = {e['subject_tdoc'] for e in events if e['document_entry']['decisionBlock'] == 8174}
        self.assertEqual(at_block, {'R4-2205027'})


class ActualDocumentEntries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events = {}
        wanted = {'R5-235183', 'R5-235182', 'R5-234674', 'R5-213430', 'R5-214045',
                  'R5-174044', 'R5-174673'}
        for number in [100, 91, 76]:
            report = json.loads((d.ROOT / f'ontology/output/tsg/RAN/formal/parsed_reports/RAN5/RAN5_{number}.json').read_text())
            events, stats = document_decisions(report)
            if stats['unboundTypeMetadataBlocks']:
                raise AssertionError(stats['unboundTypeMetadataBlocks'])
            for item in events:
                if item['subject_tdoc'] in wanted:
                    cls.events[(number, item['subject_tdoc'], item['document_entry']['decisionBlock'])] = item
            d.source_blocks.cache_clear()

    def test_discussion_document_citations_do_not_cut_entry(self):
        row = self.events[(100, 'R5-235183', 5648)]
        self.assertIn('R4-2313639 was agreed without additional changes.', row['content'])
        self.assertEqual(classify_document_decision(row)[0], 'agreed')
        self.assertEqual(classify_document_decision(self.events[(100, 'R5-235182', 5867)])[0], 'revised')

    def test_actual_approved_as_revises_checked_predecessor(self):
        for target, block, output in [('R5-213430', 10920, 'R5-213682'), ('R5-214045', 11321, 'R5-213681')]:
            row = self.events[(91, target, block)]
            self.assertEqual(row['referenced_tdocs'], [target, output])
            self.assertEqual(classify_document_decision(row)[0], 'revised')
            self.assertEqual(classify_document_decision(row, output)[0], 'agreed')

    def test_actual_legacy_and_technical_decisions_keep_scope(self):
        row = self.events[(76, 'R5-174044', 7069)]
        self.assertEqual(row['document_entry']['documentType'], 'CR')
        self.assertEqual(row['document_entry']['formalDocumentDecisionParagraphs'], 1)
        self.assertEqual(classify_document_decision(row)[0], 'revised')
        self.assertEqual(classify_document_decision(self.events[(76, 'R5-174044', 7068)])[0], 'ambiguous')
        self.assertEqual(classify_document_decision(self.events[(100, 'R5-234674', 1605)])[0], 'ambiguous')
        self.assertEqual(classify_document_decision(self.events[(100, 'R5-234674', 1606)])[0], 'noted')
        self.assertEqual(classify_document_decision(self.events[(76, 'R5-174673', 8517)])[0], 'agreed')


class ActualQualifiedRevisionOutputs(unittest.TestCase):
    """Accepted report entries whose approval names a new number after a qualifier."""
    CASES = {('RAN2', '103bis', 'R2-1814490', 4968): ('R2-1815915', 'conditionally_agreed'),
             ('RAN2', '103bis', 'R2-1814234', 5617): ('R2-1815866', 'conditionally_agreed'),
             ('RAN2', '105bis', 'R2-1903854', 1040): ('R2-1905349', 'conditionally_agreed'),
             ('RAN2', '105bis', 'R2-1904609', 1694): ('R2-1905373', 'conditionally_agreed'),
             ('RAN2', '111-e', 'R2-2008257', 532): ('R2-2008259', 'agreed'),
             ('RAN2', '134', 'R2-2603061', 1144): ('R2-2604319', 'agreed'),
             ('RAN2', '134', 'R2-2603120', 1195): ('R2-2604205', 'agreed'),
             ('RAN1', '86b', 'R1-1610859', 745): ('R1-1610886', 'agreed')}

    @classmethod
    def setUpClass(cls):
        cls.events = {}
        meetings = {(wg, meeting) for wg, meeting, _, _ in cls.CASES} | {('RAN2', '105bis')}
        for wg, meeting in sorted(meetings):
            report = json.loads((d.ROOT / f'ontology/output/tsg/RAN/formal/parsed_reports/{wg}/{wg}_{meeting}.json').read_text())
            events, _ = document_decisions(report)
            for item in events:
                if item['document_entry'].get('sourceKind') != 'annex_cr_table_row':
                    cls.events[(wg, meeting, item['subject_tdoc'], item['document_entry']['decisionBlock'])] = item
            d.source_blocks.cache_clear()

    def test_header_is_revised_and_output_carries_the_approval(self):
        for key, (output, expected) in self.CASES.items():
            row = self.events[key]
            self.assertEqual(row['referenced_tdocs'], [key[2], output], key)
            self.assertEqual(classify_document_decision(row)[0], 'revised', key)
            self.assertEqual(classify_document_decision(row, output)[0], expected, key)

    def test_running_CR_inclusion_stays_pending(self):
        row = self.events[('RAN2', '105bis', 'R2-1905461', 2588)]
        self.assertEqual(row['document_entry']['decisionText'], '=>\tAgreed to be included in the running CR')
        self.assertEqual(classify_document_decision(row)[::2], ('ambiguous', INCORPORATION_RULE))


class ActualApprovalObjects(unittest.TestCase):
    """Accepted report entries whose approval object is not the whole header document."""
    CASES = {('RAN1', '87', 'R1-1612013', 878): ('Decision: Agreed TP and editor will reflect it',
                                                 'partially_agreed', 'document_TP_object_approval'),
             ('RAN2', '97', 'R2-1700949', 4734): ('=>\tAgreed R2-1702219',
                                                  'ambiguous', 'approval_of_another_number_without_relation'),
             ('RAN2', '102', 'R2-1807272', 5187): ('Agreed, merge with rapporteur CR', 'ambiguous', INCORPORATION_RULE),
             ('RAN3', '96', 'R3-171959', 3017): ('Decision: \t\tThe document was Agreed (To be included in the baseline).',
                                                 'ambiguous', INCORPORATION_RULE),
             ('RAN2', '95bis', 'R2-167256', 896): ('=>\tAgreed in principel', 'conditionally_agreed',
                                                   'checked_document_decision_field:explicit_target_predicate'),
             ('RAN2', '99bis', 'R2-1711857', 1002): ('=>\tThe CR is agreed in principle R2-1711860 with impact analysis added',
                                                    'ambiguous', 'approval_of_another_number_without_relation')}

    @classmethod
    def setUpClass(cls):
        cls.events = {}
        for wg, meeting in sorted({(wg, meeting) for wg, meeting, _, _ in cls.CASES}):
            report = json.loads((d.ROOT / f'ontology/output/tsg/RAN/formal/parsed_reports/{wg}/{wg}_{meeting}.json').read_text())
            events, _ = document_decisions(report)
            for item in events:
                if item['document_entry'].get('sourceKind') != 'annex_cr_table_row':
                    cls.events[(wg, meeting, item['subject_tdoc'], item['document_entry']['decisionBlock'])] = item
            d.source_blocks.cache_clear()

    def test_each_entry_keeps_its_approval_object(self):
        for key, (text, code, rule) in self.CASES.items():
            row = self.events[key]
            self.assertEqual(row['document_entry']['decisionText'], text, key)
            self.assertEqual(row['referenced_tdocs'], [key[2]], key)
            self.assertEqual(classify_document_decision(row)[::2], (code, rule), key)


class ActualCoordinatedRevisionOutput(unittest.TestCase):
    """`The CR is agreed as a baseline and revised in R2-y` revises the header document."""

    @classmethod
    def setUpClass(cls):
        report = json.loads((d.ROOT / 'ontology/output/tsg/RAN/formal/parsed_reports/RAN2/RAN2_93.json').read_text())
        events, _ = document_decisions(report)
        cls.row = next(item for item in events if item['subject_tdoc'] == 'R2-161177'
                       and item['document_entry'].get('decisionBlock') == 4986)
        d.source_blocks.cache_clear()

    def test_header_is_revised_and_output_is_not_disposed_here(self):
        self.assertEqual(self.row['document_entry']['decisionText'],
                         '=>\tThe CR is agreed as a baseline and revised in R2-161798')
        self.assertEqual(classify_document_decision(self.row)[::2],
                         ('revised', 'checked_document_decision_field:explicit_target_coordinated_revision_output'))
        self.assertEqual(classify_document_decision(self.row, 'R2-161798')[0], 'ambiguous')


class ActualOutputClauses(unittest.TestCase):
    """Accepted report entries whose output approval is one clause of a longer Decision field."""
    CASES = {('RAN1', '84', 'R1-160511', 703): {'R1-160511': 'ambiguous', 'R1-161137': 'agreed'},
             ('RAN1', '98', 'R1-1909835', 280): {'R1-1909835': 'ambiguous', 'R1-1909852': 'agreed'},
             ('RAN1', '98', 'R1-1908714', 574): {'R1-1908714': 'ambiguous', 'R1-1909629': 'agreed'},
             ('RAN1', '103-e', 'R1-2009599', 1981): {'R1-2009599': 'ambiguous', 'R1-2009740': 'ambiguous'},
             ('RAN1', '88b', 'R1-1706695', 2829): {'R1-1706695': 'ambiguous', 'R1-1706707': 'ambiguous',
                                                    'R1-1706717': 'agreed'},
             ('RAN2', '104', 'R2-1816411', 1501): {'R2-1816411': 'revised', 'R2-1818653': 'agreed'}}

    @classmethod
    def setUpClass(cls):
        cls.events = {}
        for wg, meeting in sorted({(wg, meeting) for wg, meeting, _, _ in cls.CASES}):
            report = json.loads((d.ROOT / f'ontology/output/tsg/RAN/formal/parsed_reports/{wg}/{wg}_{meeting}.json').read_text())
            events, _ = document_decisions(report)
            for item in events:
                if item['document_entry'].get('sourceKind') != 'annex_cr_table_row':
                    cls.events[(wg, meeting, item['subject_tdoc'], item['document_entry']['decisionBlock'])] = item
            d.source_blocks.cache_clear()

    def test_each_output_is_read_from_its_own_clause(self):
        for key, expected in self.CASES.items():
            row = self.events[key]
            self.assertEqual(row['referenced_tdocs'], list(expected), key)
            self.assertEqual({target: classify_document_decision(row, target)[0] for target in expected}, expected, key)


class ActualAnnexRows(unittest.TestCase):
    def source(self, meeting):
        report = {'meeting_id': 'RAN2#' + meeting,
            'docx_path': f'ontology/input/tsg/RAN/formal/meetings/RAN2/Final_Report/Final_Report_RAN2-{meeting}.docx'}
        result = annex_cr_table_events(report)
        self.addCleanup(d.source_blocks.cache_clear)
        return result

    def test_actual_ran2_target_has_its_exact_row_without_approving_its_neighbor(self):
        events, stats = self.source('116-e')
        self.assertEqual(len(events), 68)
        row = next(e for e in events if e['subject_tdoc'] == 'R2-2110023')
        self.assertEqual(row['document_entry']['annexTable']['acceptedRow'], 3)
        self.assertEqual(classify_document_decision(row)[0], 'agreed')
        self.assertEqual(row['document_entry']['sourceFields'],
            {'title': 'Correction on R16 UE capability of supportedSINR-meas-r16',
             'spec': '38.331', 'crNumber': '2822', 'crRevision': None, 'release': 'Rel-16'})
        self.assertNotIn('R2-2110024', {e['subject_tdoc'] for e in events})
        self.assertIn('R2-2111577', {e['subject_tdoc'] for e in events})
        source = annex_source_evidence(row)
        self.assertIn('table block 12518 row 3;', source['locator'])
        self.assertNotIn('R2-2109580', source['quote'])
        self.assertEqual(row['referenced_tdocs'], ['R2-2110023'])

    def test_actual_principle_footer_cannot_become_whole_approval(self):
        events, _ = self.source('101bis')
        self.assertEqual(len(events), 53)
        self.assertEqual({classify_document_decision(e)[0] for e in events}, {'ambiguous'})
        self.assertTrue(all('53 CR agreed in priciple.' in e['content'] for e in events))

    def test_source_event_total_includes_annex_without_inventing_headers(self):
        report = {'meeting_id': 'RAN2#116-e',
            'docx_path': 'ontology/input/tsg/RAN/formal/meetings/RAN2/Final_Report/Final_Report_RAN2-116-e.docx'}
        events, stats = document_decisions(report)
        self.addCleanup(d.source_blocks.cache_clear)
        self.assertEqual(stats['sourceDecisionEvents'], len(events))
        self.assertEqual(stats['annexSourceRowEvents'], 68)
        self.assertEqual(stats['sourceDecisionEvents'], stats['headerDecisionEvents'] + 68)
        self.assertEqual(stats['explicitCREvents'], stats['headerExplicitCREvents'] + 68)
        # This report writes no `Decision:` label; every header event is a label-less status line.
        self.assertEqual(stats['headerDecisionEvents'], stats['listStatusLines'])
        self.assertEqual(stats['headerDecisionEvents'], 578)
        self.assertEqual(stats['checkedHeaders'], stats['listLineHeaders'])

    def test_actual_separate_agreed_and_draft_lists_keep_their_own_scope(self):
        events, stats = self.source('95bis')
        agreed = [e for e in events if classify_document_decision(e)[0] == 'agreed']
        pending = [e for e in events if classify_document_decision(e)[0] == 'ambiguous']
        self.assertEqual({e['subject_tdoc'] for e in agreed}, {'R2-166847', 'R2-166857'})
        self.assertEqual(len(pending), 55)
        self.assertEqual(len(stats['annexUnboundRows']), 49)
        self.assertTrue(all(e['document_entry']['annexTable']['tableBlock'] == 4390 for e in pending))
        self.assertTrue(all('104 in principle agreed draftCRs' not in e['content'] for e in agreed))

    def test_actual_mixed_table_uses_wg_column_and_does_not_dispose_remarks_ids(self):
        events, _ = self.source('93')
        row = next(e for e in events if e['subject_tdoc'] == 'R2-161891')
        self.assertEqual(row['document_entry']['annexTable']['targetColumn'], 5)
        self.assertEqual(classify_document_decision(row)[0], 'agreed')
        self.assertEqual(row['referenced_tdocs'], ['R2-161891'])
        # A company RAN row mentions this ID in Remarks, while the same RAN2
        # document has its own separate row. Only its own row is a target.
        self.assertFalse(any(e['document_entry']['annexTable']['acceptedRow'] == 152 for e in events))
        self.assertEqual(len(events), 150)
        self.assertEqual(sum(classify_document_decision(e)[0]=='endorsed' for e in events), 2)
        annex_source_evidence(row)

    def test_actual_wg_agreement_does_not_take_tsg_approval_status(self):
        events, _ = self.source('94')
        row = next(e for e in events if e['subject_tdoc'] == 'R2-164349')
        self.assertIn('can therefore not be considered approved', row['content'])
        self.assertEqual(classify_document_decision(row)[0], 'agreed')
        self.assertEqual(row['document_entry']['annexTable']['statusSource']['kind'], 'explicit_WG_status_cell')
        self.assertEqual(row['document_entry']['annexTable']['statusSource']['column'], 9)

    def test_actual_endorsed_neighbor_table_cannot_inherit_agreed_caption(self):
        events, _ = self.source('97')
        self.assertEqual(sum(classify_document_decision(e)[0]=='agreed' for e in events), 198)
        self.assertEqual(sum(classify_document_decision(e)[0]=='endorsed' for e in events), 10)

    def test_row_header_scope_field_and_source_sha_tampering_are_rejected(self):
        events, _ = self.source('116-e')
        original = next(e for e in events if e['subject_tdoc'] == 'R2-2110023')
        mutations = [lambda e: e['document_entry']['annexTable']['rowCells'].__setitem__(0,'R2-2110024'),
                     lambda e: e['document_entry']['annexTable']['headerCells'].__setitem__(0,'RAN Tdoc'),
                     lambda e: e['document_entry']['annexTable']['governingContext'][0].__setitem__('text','Approved CRs'),
                     lambda e: e['document_entry']['annexTable'].__setitem__('sourceSha256','0'*64),
                     lambda e: e['document_entry']['sourceFields'].__setitem__('crRevision','9')]
        for mutate in mutations:
            row=copy.deepcopy(original); mutate(row)
            with self.assertRaises(ValueError): annex_source_evidence(row)

    def test_wgs_without_annex_column_names_keep_their_existing_source_production(self):
        for wg in ('RAN3', 'RAN4', 'RAN5'):
            self.assertEqual(annex_cr_table_events({'meeting_id': wg+'#100'}), ([], {}))

    def ran1(self, meeting):
        report = {'meeting_id': 'RAN1#' + meeting,
            'docx_path': f'ontology/input/tsg/RAN/formal/meetings/RAN1/Final_Report/Final_Report_RAN1-{meeting}.docx'}
        events, census = annex_cr_table_events(report)
        return {e['subject_tdoc']: e for e in events}, census

    def test_ran1_heading_and_lead_in_paragraph_set_each_table_scope(self):
        cases = [('100-e', 'R1-2001224', 'agreed', 1), ('120b', 'R1-2503129', 'endorsed', 1),
                 ('121', 'R1-2504976', 'endorsed', 2), ('90b', 'R1-1719232', 'endorsed', 2),
                 ('96b', 'R1-1905905', 'endorsed', 2), ('84', 'R1-161253', 'agreed', 2)]
        for meeting, target, scope, context in cases:
            events, _ = self.ran1(meeting)
            row = events[target]
            table = row['document_entry']['annexTable']
            self.assertEqual((table['tableScope'], len(table['governingContext'])), (scope, context), (meeting, target))
            self.assertEqual(classify_document_decision(row)[0], scope)
            self.assertEqual(annex_source_evidence(row)['subjectChecked'], True)
            self.assertRegex(table['governingContext'][0]['text'], r'^Annex B:\tList of (draft )?CRs (agreed|endorsed) at RAN1 #')

    def test_ran1_rows_bind_only_a_written_ran1_document_number(self):
        events, _ = self.ran1('100-e')
        self.assertTrue(events)
        for target, row in events.items():
            self.assertRegex(target, r'^R1-\d{6,8}$')
            self.assertIn(target, row['document_entry']['annexTable']['rowCells'])

    def test_generated_event_cannot_mutate_cached_source_truth(self):
        events, _ = self.source('116-e')
        row = next(e for e in events if e['subject_tdoc'] == 'R2-2110023')
        old, replacement = row['subject_tdoc'], 'R2-9999999'
        row['subject_tdoc'] = replacement
        row['referenced_tdocs'] = [replacement]
        row['decision_id'] = row['decision_id'].replace(old, replacement)
        row['content'] = row['content'].replace(old, replacement)
        row['document_entry']['decisionText'] = row['document_entry']['decisionText'].replace(old, replacement)
        row['document_entry']['annexTable']['rowCells'][0] = replacement
        with self.assertRaisesRegex(ValueError, 'changed'):
            annex_source_evidence(row)

    def test_global_principle_footer_takes_priority_over_wg_agreed_cell(self):
        w='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
        with tempfile.TemporaryDirectory(prefix='annex-source-',dir='/tmp') as directory:
            root=Path(directory); path=root/'source.docx'
            doc=ET.Element(w+'document');body=ET.SubElement(doc,w+'body')
            def para(parent,text):
                p=ET.SubElement(parent,w+'p');r=ET.SubElement(p,w+'r');ET.SubElement(r,w+'t').text=text
            para(body,'Annex E: List of agreed CRs')
            table=ET.SubElement(body,w+'tbl')
            for row in [['Spec','CR #','rev','cat','REL','RAN2 Tdoc','Title','SI/WI','RAN2 Source','RAN2 status','RAN Tdoc','RAN status','Remarks'],
                        ['38.331','0001','1','F','Rel-17','R2-2200001','Actual title','WI','Company','agreed','RP-2200001','approved','']]:
                tr=ET.SubElement(table,w+'tr')
                for text in row:para(ET.SubElement(tr,w+'tc'),text)
            para(body,'1 CR agreed in principle.')
            with zipfile.ZipFile(path,'w') as z:z.writestr('word/document.xml',ET.tostring(doc))
            events,_=annex_cr_table_events({'meeting_id':'RAN2#120','docx_path':'source.docx'},root)
            self.assertEqual(len(events),1)
            self.assertEqual(classify_document_decision(events[0])[0],'ambiguous')
            self.assertEqual(events[0]['document_entry']['annexTable']['statusSource']['kind'],'in_principle_table_scope')
            annex_source_evidence(events[0],root)


if __name__ == '__main__':
    unittest.main()
