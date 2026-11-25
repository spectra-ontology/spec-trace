#!/usr/bin/env python3
"""test_docx_search_fragments.py — recovered source string presentation.

Spec: source-bound TS heading recovery and opt-in Word search roles.
Ontology: typography does not infer heading acceptance or clause membership.
Cycle: observed fused NOTE structure → role preservation → ambiguity rejection.
배경: 복구된 NOTE의 하첨자 손실과 수식 누락의 조용한 전파를 차단한다.
사용: python3 -B scripts/tsg/RAN/formal/common/test_docx_search_fragments.py
LLM 호출: 없음.
"""
import unittest

from lxml import etree

import docx_text
from docx_search_fragments import SourceFragmentMismatch, search_fragment
from docx_search_styles import SearchStyles


W = docx_text.W_NS
M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'


def paragraph(body):
    return etree.fromstring(f'<w:p xmlns:w="{W}" xmlns:m="{M}">{body}</w:p>')


class RecoveredFragmentPresentation(unittest.TestCase):
    def test_observed_fused_note_structure_keeps_actual_subscript_and_xml(self):
        # Minimal structural reproduction of the observed 38.533 NOTE+heading.
        p = paragraph('<w:r><w:t>NOTE: The delay may be up to 2xTTI</w:t></w:r>'
                      '<w:r><w:rPr><w:vertAlign w:val="subscript"/></w:rPr>'
                      '<w:t>DCCH</w:t></w:r><w:r><w:t> higher.</w:t><w:tab/>'
                      '<w:t>19.5.2.3</w:t><w:tab/><w:t>Next test</w:t></w:r>')
        before = etree.tostring(p)
        lead = 'NOTE: The delay may be up to 2xTTIDCCH higher.'
        self.assertEqual(search_fragment(p, lead),
                         'NOTE: The delay may be up to 2xTTI<sub>DCCH</sub> higher.')
        self.assertEqual(etree.tostring(p), before)
        self.assertEqual(docx_text.final_text(p), lead + '\t19.5.2.3\tNext test')

    def test_unrelated_source_fragment_is_rejected(self):
        p = paragraph('<w:r><w:t>actual source</w:t></w:r>')
        with self.assertRaisesRegex(SourceFragmentMismatch, 'primary quotation'):
            search_fragment(p, 'another source')

    def test_repeated_fragment_with_conflicting_roles_is_rejected(self):
        p = paragraph('<w:r><w:t>x</w:t></w:r><w:r><w:rPr>'
                      '<w:vertAlign w:val="subscript"/></w:rPr><w:t>1</w:t></w:r>'
                      '<w:r><w:t xml:space="preserve"> and x</w:t></w:r>'
                      '<w:r><w:rPr><w:vertAlign w:val="superscript"/>'
                      '</w:rPr><w:t>1</w:t></w:r>')
        with self.assertRaisesRegex(SourceFragmentMismatch, 'ambiguous'):
            search_fragment(p, 'x1')

    def test_fragment_cannot_silently_drop_an_intervening_equation(self):
        p = paragraph('<w:r><w:t>before </w:t></w:r><m:oMath><m:r><m:t>x</m:t>'
                      '</m:r></m:oMath><w:r><w:t> after</w:t></w:r>')
        self.assertEqual(docx_text.final_text(p), 'before  after')
        with self.assertRaisesRegex(SourceFragmentMismatch, 'no_body_match'):
            search_fragment(p, 'before  after')

    def test_explicit_document_style_reader_is_supported(self):
        styles = etree.fromstring(f'<w:styles xmlns:w="{W}"><w:style w:type="character" '
                                  'w:styleId="font11"><w:rPr><w:vertAlign '
                                  'w:val="superscript"/></w:rPr></w:style></w:styles>')
        p = paragraph('<w:r><w:t>20</w:t></w:r><w:r><w:rPr>'
                      '<w:rStyle w:val="font11"/></w:rPr><w:t>1</w:t></w:r>')
        self.assertEqual(search_fragment(p, '201', render=SearchStyles(styles).read),
                         '20<sup>1</sup>')

    def test_literal_markup_is_rejected_and_deleted_text_is_not_restored(self):
        p = paragraph('<w:r><w:t>literal &lt;sup&gt;x&lt;/sup&gt;</w:t></w:r>')
        with self.assertRaisesRegex(SourceFragmentMismatch, 'preserve'):
            search_fragment(p, 'literal <sup>x</sup>')
        p = paragraph('<w:del><w:r><w:delText>old claim</w:delText></w:r></w:del>'
                      '<w:r><w:t>current claim</w:t></w:r>')
        with self.assertRaisesRegex(SourceFragmentMismatch, 'primary quotation'):
            search_fragment(p, 'old claim')
        self.assertEqual(search_fragment(p, 'current claim'), 'current claim')


if __name__ == '__main__':
    unittest.main()
