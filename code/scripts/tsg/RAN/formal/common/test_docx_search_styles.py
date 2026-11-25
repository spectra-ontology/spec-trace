#!/usr/bin/env python3
"""test_docx_search_styles.py — style-inherited search superscripts/subscripts.

Spec: WordprocessingML style inheritance; standards/reembedding_policy.md.
Ontology: source typography is preserved without inferring its technical meaning.
Cycle: resolve styles → search presentation → exact primary-reader projection.
배경: 실제 TS의 font11 스타일이 숫자 주석의 superscript를 지정한다.
사용: python3 -B scripts/tsg/RAN/formal/common/test_docx_search_styles.py
LLM 호출: 없음.
"""
from __future__ import annotations

import re
import unittest

from lxml import etree

import docx_text as d
from docx_search_styles import SearchStyles


def xml(kind, content):
    return etree.fromstring((f'<w:{kind} xmlns:w="{d.W_NS}">' + content + f'</w:{kind}>').encode())


def run(text, properties=''):
    return '<w:r><w:rPr>' + properties + '</w:rPr><w:t xml:space="preserve">' + text + '</w:t></w:r>'


class InheritedSearchStyles(unittest.TestCase):
    def check(self, style_content, paragraph_content, expected, deleted=d.DROP):
        styles = xml('styles', style_content)
        paragraph = xml('p', paragraph_content)
        before = (etree.tostring(styles), etree.tostring(paragraph))
        primary_before = d.final_text(paragraph)
        baseline = d.chunk_text(paragraph, deleted=deleted)
        result = SearchStyles(styles).read(paragraph, deleted=deleted)
        self.assertEqual(result, expected)
        self.assertEqual(re.sub(r'</?(?:sup|sub)>', '', result), baseline)
        self.assertEqual(d.final_text(paragraph), primary_before)
        self.assertEqual((etree.tostring(styles), etree.tostring(paragraph)), before)

    def test_actual_font11_shape_preserves_numeric_footnote_role(self):
        styles = '<w:style w:type="character" w:styleId="font11"><w:rPr><w:vertAlign w:val="superscript"/></w:rPr></w:style>'
        self.check(styles, run('20') + run('1', '<w:rStyle w:val="font11"/>') + run(' MHz'),
                   '20<sup>1</sup> MHz')

    def test_based_on_chain_and_paragraph_style(self):
        styles = ('<w:style w:type="paragraph" w:styleId="base"><w:rPr><w:vertAlign w:val="subscript"/></w:rPr></w:style>'
                  '<w:style w:type="paragraph" w:styleId="child"><w:basedOn w:val="base"/></w:style>')
        self.check(styles, '<w:pPr><w:pStyle w:val="child"/></w:pPr>' + run('RB'), '<sub>RB</sub>')

    def test_character_style_overrides_paragraph_and_direct_baseline_overrides_both(self):
        styles = ('<w:style w:type="paragraph" w:styleId="p"><w:rPr><w:vertAlign w:val="subscript"/></w:rPr></w:style>'
                  '<w:style w:type="character" w:styleId="c"><w:rPr><w:vertAlign w:val="superscript"/></w:rPr></w:style>')
        self.check(styles, '<w:pPr><w:pStyle w:val="p"/></w:pPr>'
                   + run('a', '<w:rStyle w:val="c"/>')
                   + run('b', '<w:rStyle w:val="c"/><w:vertAlign w:val="baseline"/>'), '<sup>a</sup>b')

    def test_document_defaults_and_inherited_baseline(self):
        styles = ('<w:docDefaults><w:rPrDefault><w:rPr><w:vertAlign w:val="superscript"/></w:rPr></w:rPrDefault></w:docDefaults>'
                  '<w:style w:type="character" w:styleId="plain"><w:rPr><w:vertAlign w:val="baseline"/></w:rPr></w:style>')
        self.check(styles, run('a') + run('b', '<w:rStyle w:val="plain"/>'), '<sup>a</sup>b')

    def test_position_and_missing_style_do_not_establish_a_script_role(self):
        self.check('', run('x') + run('2', '<w:position w:val="6"/><w:rStyle w:val="absent"/>'), 'x2')

    def test_symbol_decoding_happens_before_inherited_role_markup(self):
        styles = '<w:style w:type="character" w:styleId="c"><w:rPr><w:vertAlign w:val="superscript"/></w:rPr></w:style>'
        self.check(styles, run('2') + run('m', '<w:rStyle w:val="c"/><w:rFonts w:ascii="Symbol" w:hAnsi="Symbol"/>'),
                   '2<sup>μ</sup>')

    def test_tracked_changes_keep_existing_drop_mark_and_keep_contracts(self):
        styles = '<w:style w:type="character" w:styleId="c"><w:rPr><w:vertAlign w:val="superscript"/></w:rPr></w:style>'
        p = run('x') + '<w:del>' + run('2', '<w:rStyle w:val="c"/>') + '</w:del>' + run('3', '<w:rStyle w:val="c"/>')
        self.check(styles, p, 'x<sup>3</sup>')
        self.check(styles, p, 'x[DEL]<sup>2</sup>[/DEL]<sup>3</sup>', d.MARK)
        self.check(styles, p, 'x<sup>23</sup>', d.KEEP)

    def test_only_a_used_style_cycle_is_rejected(self):
        styles = xml('styles', '<w:style w:styleId="a"><w:basedOn w:val="b"/></w:style><w:style w:styleId="b"><w:basedOn w:val="a"/></w:style>')
        reader = SearchStyles(styles)
        self.assertEqual(reader.read(xml('p', run('x'))), 'x')
        with self.assertRaisesRegex(ValueError, 'Cycle'):
            reader.read(xml('p', run('x', '<w:rStyle w:val="a"/>')))


if __name__ == '__main__':
    unittest.main()
