#!/usr/bin/env python3
"""test_docx_search_text.py — 검색 본문에서 첨자의 역할과 원래 글을 함께 보존한다.

Spec: docs/tsg/build/standards/reembedding_policy.md.
Ontology: 원문 인용과 검색 표현의 출처를 구별한다.
Cycle: Word 검색 본문 표현 회귀.
배경: 밴드 번호·주석 번호의 접합과 일반 run 첨자 소실을 검출한다.
사용: python3 -B scripts/tsg/RAN/formal/common/test_docx_search_text.py
LLM 호출: 없음.
"""
from __future__ import annotations

import re
import unittest
from lxml import etree

import docx_text as d


def paragraph(body):
    return etree.fromstring((f'<w:p xmlns:w="{d.W_NS}" xmlns:m="{d.M_NS}">' + body + '</w:p>').encode())


def run(text, role=None, font=None):
    properties = (f'<w:vertAlign w:val="{role}"/>' if role else '')
    properties += (f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}"/>' if font else '')
    return f'<w:r><w:rPr>{properties}</w:rPr><w:t xml:space="preserve">{text}</w:t></w:r>'


class SearchTextPreservation(unittest.TestCase):
    def assert_projection(self, p, expected, deleted=d.DROP):
        before = etree.tostring(p)
        old = d.chunk_text(p, deleted=deleted)
        actual = d.search_text(p, deleted=deleted)
        self.assertEqual(actual, expected)
        self.assertEqual(re.sub(r'</?(?:sup|sub)>', '', actual), old)
        self.assertEqual(etree.tostring(p), before)
        return old

    def test_band_and_unit_footnote_labels_stay_separate_from_numbers(self):
        p = paragraph(run('n512') + run('1', 'superscript') + run(' | 10700 MHz – 12750')
                      + run('4,5', 'superscript') + run(' MHz'))
        old = self.assert_projection(p, 'n512<sup>1</sup> | 10700 MHz – 12750<sup>4,5</sup> MHz')
        self.assertEqual(old, 'n5121 | 10700 MHz – 127504,5 MHz')
        self.assertEqual(d.final_text(p), old)

    def test_symbol_font_script_is_marked_after_character_decoding(self):
        p = paragraph(run('180*2') + run('m', 'superscript', 'Symbol') + run(' kHz; ')
                      + run('g', font='Symbol') + run('1', 'subscript'))
        self.assert_projection(p, '180*2<sup>μ</sup> kHz; γ<sub>1</sub>')

    def test_whitespace_and_multiple_text_leaves_preserve_exact_baseline(self):
        p = paragraph(run('N') + '<w:r><w:rPr><w:vertAlign w:val="subscript"/></w:rPr>'
                      '<w:t xml:space="preserve">  RB</w:t><w:t xml:space="preserve">, c  </w:t></w:r>'
                      + run(' end'))
        self.assert_projection(p, 'N  <sub>RB, c</sub>   end')

    def test_adjacent_script_runs_share_one_role_without_losing_spaces(self):
        p = paragraph(run('x') + run('A ', 'subscript') + run(' B', 'subscript') + run(' limit'))
        self.assert_projection(p, 'x<sub>A  B</sub> limit')

    def test_math_boundary_spacing_uses_the_existing_linear_reader(self):
        p = paragraph(run('N') + run('1', 'subscript')
                      + '<m:oMath><m:r><m:t>x</m:t></m:r></m:oMath>' + run('y'))
        self.assert_projection(p, 'N<sub>1</sub> x y')
        self.assertEqual(d.final_text(p), 'N1y')

    def test_accepted_and_marked_deleted_scripts_keep_change_roles(self):
        p = paragraph(run('x') + '<w:del>' + run('2', 'superscript') + '</w:del>'
                      + '<w:ins>' + run('3', 'superscript') + '</w:ins>')
        self.assert_projection(p, 'x<sup>3</sup>')
        self.assert_projection(p, 'x[DEL]<sup>2</sup>[/DEL]<sup>3</sup>', d.MARK)
        self.assert_projection(p, 'x<sup>23</sup>', d.KEEP)

    def test_whitespace_only_script_run_does_not_invent_annotation(self):
        p = paragraph(run('a') + run('  ', 'superscript') + run('b'))
        self.assert_projection(p, 'a  b')

    def test_baseline_override_and_inherited_style_are_not_guessed(self):
        p = paragraph(run('x') + run('2', 'baseline')
                      + '<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/></w:rPr><w:t>3</w:t></w:r>')
        self.assert_projection(p, 'x23')

    def test_symbol_element_retains_its_script_role(self):
        p = paragraph(run('angle ')
                      + '<w:r><w:rPr><w:vertAlign w:val="superscript"/></w:rPr>'
                      '<w:sym w:font="Symbol" w:char="F061"/></w:r>')
        self.assert_projection(p, 'angle <sup>α</sup>')

    def test_script_run_with_tab_and_break_preserves_each_separator(self):
        p = paragraph(run('x')
                      + '<w:r><w:rPr><w:vertAlign w:val="subscript"/></w:rPr>'
                      '<w:t>A</w:t><w:tab/><w:t>B</w:t><w:br/><w:t>C</w:t></w:r>')
        self.assert_projection(p, 'x<sub>A\tB\nC</sub>')

    def test_literal_tag_text_is_preserved_as_source_characters(self):
        p = paragraph(run('&lt;sup&gt;literal&lt;/sup&gt; x') + run('2', 'superscript'))
        before = etree.tostring(p)
        self.assertEqual(d.chunk_text(p), '<sup>literal</sup> x2')
        self.assertEqual(d.search_text(p), '<sup>literal</sup> x<sup>2</sup>')
        self.assertEqual(etree.tostring(p), before)

    def test_math_and_annotated_equation_object_keep_baseline_spacing(self):
        p = paragraph(run('a') + run('1', 'subscript')
                      + '<m:oMath><m:r><m:t>x</m:t></m:r></m:oMath>'
                      + run('2', 'superscript')
                      + '<w:r><w:object equation-text="z^2"/></w:r>' + run('b'))
        old = d.chunk_text(p)
        actual = d.search_text(p)
        self.assertIn('a<sub>1</sub>', actual)
        self.assertIn('<sup>2</sup>', actual)
        self.assertIn('z^2', actual)
        self.assertEqual(re.sub(r'</?(?:sup|sub)>', '', actual), old)


if __name__ == '__main__':
    unittest.main()
