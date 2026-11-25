#!/usr/bin/env python3
"""test_ts_search_renderer.py — actual five-WG producer search semantics.

Spec: Phase-7 Word styles, table cells, equation captions and clause identity.
Ontology: preserve native evidence without changing heading recognition.
Cycle: native DOCX fixture → actual parser → identity/body/source comparisons.
배경: producer integration must retain source roles across later ingestions.
사용: python3 -B -m unittest discover -s scripts/tsg/RAN/formal/common -p test_ts_search_renderer.py
LLM 호출: 없음. No database or encoder/model execution.
"""
from concurrent.futures import ThreadPoolExecutor
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement

import docx_text
import ts_search_renderer as renderer

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())


def sample(path, *, superscript=True):
    document = Document()
    document.styles.add_style('TH', WD_STYLE_TYPE.PARAGRAPH)
    character = document.styles.add_style('SourceScript', WD_STYLE_TYPE.CHARACTER)
    character.font.superscript = superscript
    document.add_paragraph('5.3 Actual procedure', style='Heading 2')
    p = document.add_paragraph('value n512')
    p.add_run('1').style = character
    p.add_run(' shall apply.')
    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).text = 'Band'
    table.cell(0, 1).text = 'Limit'
    table.cell(1, 0).text = 'n512'
    p = table.cell(1, 1).paragraphs[0]
    p.add_run('X')
    r = p.add_run('2'); r.font.subscript = True
    p = document.add_paragraph('Table 5.3-1: limit ', style='TH')
    math = OxmlElement('m:oMath')
    run = OxmlElement('m:r'); text = OxmlElement('m:t'); text.text = 'X=2'
    run.append(text); math.append(run); p._p.append(math)
    document.add_paragraph('5.4 Next procedure', style='Heading 2')
    document.add_paragraph('A separate clause.')
    document.save(path)


class NativeProducerIntegration(unittest.TestCase):
    def test_all_five_actual_parsers_keep_source_roles_equations_and_clause_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.docx'; sample(path)
            original = path.read_bytes()
            for wg in range(1, 6):
                with self.subTest(wg=wg):
                    name = f'ts_search_producer_ran{wg}'
                    source = ROOT / f'scripts/tsg/RAN/formal/RAN{wg}/phase-7/ts-parser/01_parse_ts_sections.py'
                    spec = importlib.util.spec_from_file_location(name, source)
                    module = importlib.util.module_from_spec(spec); sys.modules[name] = module; spec.loader.exec_module(module)
                    units, _ = module._parse_part('38.214', path, module.ts_section_number.HeadingSequence())
                    self.assertEqual([s.section_id for s in units], ['38.214-5.3', '38.214-5.4'])
                    self.assertEqual(units[0].section_title, 'Actual procedure')
                    body = '\n'.join(units[0].blocks)
                    self.assertIn('n512<sup>1</sup>', body)
                    self.assertIn('X<sub>2</sub>', body)
                    self.assertIn('X=2', '\n'.join(units[0].table_captions))
                    self.assertEqual(path.read_bytes(), original)

    def test_document_styles_are_isolated_between_parallel_calls_and_reset_on_exception(self):
        with tempfile.TemporaryDirectory() as directory:
            a, b = Path(directory) / 'a.docx', Path(directory) / 'b.docx'
            sample(a); sample(b, superscript=False)

            @renderer.document_styles
            def render(_spec, path, *, fail=False):
                p = Document(path).paragraphs[1]
                value = renderer.read(p)
                if fail:
                    raise ValueError('test interruption')
                return value

            with ThreadPoolExecutor(2) as pool:
                values = list(pool.map(lambda p: render('38.214', p), [a, b] * 4))
            self.assertTrue(all('<sup>1</sup>' in s for s in values[::2]))
            self.assertTrue(all('<sup>' not in s for s in values[1::2]))
            with self.assertRaisesRegex(ValueError, 'interruption'):
                render('38.214', a, fail=True)
            p = Document(a).paragraphs[1]
            self.assertEqual(renderer.read(p), docx_text.search_text(p))


if __name__ == '__main__':
    unittest.main()
