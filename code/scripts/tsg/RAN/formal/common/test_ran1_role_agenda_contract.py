#!/usr/bin/env python3
"""Source-placement and shared-Tdoc identity regressions for RAN1 role artifacts.

Spec: docs/tsg/RAN/formal/RAN1/phase-2/step1_parsing.md.
Ontology: functional tdoc:belongsTo; Summary/SessionNotes extend Tdoc.
Cycle: synthetic report headings and registration -> production JSON-LD functions.
배경: repeated TOC titles need parent context; title topics preserve role coverage.
사용: python3 -B -m unittest discover -s scripts/tsg/RAN/formal/common -p test_ran1_role_agenda_contract.py.
LLM 호출: none. No repository-output or database writes.
"""
import importlib.util
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parent))
from report_decision_identity import preserve_decision_ids

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
PHASE = ROOT / 'scripts/tsg/RAN/formal/RAN1/phase-2'


def load(relative, wg=None):
    phase = PHASE if wg is None else ROOT / f'scripts/tsg/RAN/formal/{wg}/phase-2'
    path = phase / relative
    names = ('models', 'agenda_matcher', 'role_extractor', 'annex')
    if wg is not None:
        names = tuple(dict.fromkeys((*names, *(
            item.stem for item in path.parent.glob('*.py')
            if item.stem.isidentifier()
        ))))
    previous = {name: sys.modules.get(name) for name in names}
    with patch.object(sys, 'path', [str(path.parent), *sys.path]):
        for name in names:
            sys.modules.pop(name, None)
        try:
            name = 'role_contract_' + (wg + '_' if wg else '') + path.stem
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
        finally:
            # Restore only phase-local aliases. Removing newly imported RDF
            # dependencies invalidates rdflib's retained parser/type registry.
            for name, value in previous.items():
                if value is None: sys.modules.pop(name, None)
                else: sys.modules[name] = value
    return module


class HeadingContext(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load('report-parser/agenda_matcher.py')

    def entries(self):
        E = self.m.TocEntry
        return [E('6.2', 'Maintenance', 2),
                E('6.2.1', 'MTC', 3), E('6.2.2', 'NB-IoT', 3),
                E('6.2.1.1', 'UE-group wake-up signal', 4),
                E('6.2.2.1', 'UE-group wake-up signal', 4)]

    def test_repeated_real_heading_title_selects_each_parent_branch(self):
        b = self.m.SectionBuilder(self.m.AgendaMatcher(self.entries()))
        b.process_heading('Maintenance', 2, 704)
        b.process_heading('MTC', 3, 722)
        self.assertEqual(b.process_heading('UE-group wake-up signal', 4, 723).agenda_number, '6.2.1.1')
        b.process_heading('NB-IoT', 3, 900)
        self.assertEqual(b.process_heading('UE-group wake-up signal', 4, 901).agenda_number, '6.2.2.1')

    def test_ambiguous_title_without_parent_does_not_choose_last_toc_entry(self):
        m = self.m.AgendaMatcher(self.entries())
        self.assertIsNone(m.match('UE-group wake-up signal'))
        self.assertEqual(m.match_with_fallback('UE-group wake-up signal', '6.2'), '6.2')

    def test_normalized_duplicate_preserves_parent_context(self):
        self.assertEqual(self.m.AgendaMatcher(self.entries()).match('  ue-group wake-up signal. ', '6.2.1'), '6.2.1.1')

    def test_repeated_other_under_parent_uses_toc_heading_level(self):
        E = self.m.TocEntry
        b = self.m.SectionBuilder(self.m.AgendaMatcher([
            E('8', 'NR', 2), E('8.1', 'Feature', 3),
            E('8.1.4', 'Other', 4), E('8.13', 'Other', 3)]))
        b.process_heading('NR', 2, 1)
        self.assertEqual(b.process_heading('Other', 3, 100).agenda_number, '8.13')

    def test_unique_title_from_other_parent_is_not_a_source_location(self):
        E = self.m.TocEntry
        m = self.m.AgendaMatcher([E('8.1', 'A particular topic', 3)])
        self.assertIsNone(m.match('A particular topic', '7', 3))

    def test_explicit_heading_number_retains_source_precedence(self):
        self.assertEqual(self.m.AgendaMatcher(self.entries()).match('6.2.1.1 UE-group wake-up signal', '6.2.2'), '6.2.1.1')

    def test_same_number_in_other_toc_level_cannot_overwrite_title_level_binding(self):
        E=self.m.TocEntry
        m=self.m.AgendaMatcher([E('2','Approval of Agenda',1),E('2','Reference',2)])
        self.assertEqual(m.match('Approval of Agenda',None,1),'2')
        self.assertEqual(m.match('approval of agenda.',None,1),'2')
        self.assertIsNone(m.match('Approval of Agenda',None,2))

    def test_prefix_and_fuzzy_ties_use_parent_instead_of_first_title(self):
        E = self.m.TocEntry
        title = 'A source heading with a repeated sufficiently long title for matching'
        m = self.m.AgendaMatcher([E('6.1.1', title, 3), E('6.2.1', title, 3)])
        self.assertEqual(m.match(title[:-8], '6.1'), '6.1.1')
        self.assertEqual(m.match(title.replace('repeated', 'repeateD?'), '6.2'), '6.2.1')

    def test_missing_opening_toc_parent_uses_actual_exact_children_before_closing_fuzzy(self):
        E=self.m.TocEntry
        matcher=self.m.AgendaMatcher([E('1.1','Call for IPR',2),
            E('1.2','Competition law statement',2),E('1.3','Network usage conditions',2),
            E('2','Approval of Agenda',1),E('8','Closing of the meeting',1)])
        headings=[(155,1,'Opening of the meeting'),(158,2,'Call for IPR'),
                  (164,2,'Competition law statement'),(168,2,'Network usage conditions'),
                  (171,1,'Approval of Agenda')]
        sections=self.m.build_sections(headings,matcher,200)
        self.assertEqual([s.agenda_number for s in sections],['1','1.1','1.2','1.3','2'])
        hint=self.m.child_parent_receipts(headings,matcher)[155]
        self.assertEqual(hint['agenda'],'1')
        self.assertEqual([at for at,_ in hint['children']],[158,164,168])

    def test_fuzzy_shared_meeting_words_cannot_equate_opening_and_closing(self):
        E=self.m.TocEntry
        for actual,opposite in [('Closing of the meeting','Opening of the meeting'),
                                ('Opening of the meeting','Closing of the meeting')]:
            matcher=self.m.AgendaMatcher([E('1',opposite,1)])
            self.assertIsNone(matcher.match(actual,None,1))
            self.assertEqual(matcher.match_with_fallback(actual,None,1),'UNKNOWN')
        matcher=self.m.AgendaMatcher([E('8','Final closing of the meeting',1)])
        self.assertEqual(matcher.match('Final Closing of the meeting.',None,1),'8')

    def test_parent_binding_requires_actual_child_occurrences_in_its_boundary(self):
        E=self.m.TocEntry
        matcher=self.m.AgendaMatcher([E('2.1','Another topic',2),E('1','Opening',1)])
        self.assertEqual(self.m.child_parent_receipts(
            [(1,1,'General'),(2,1,'Opening'),(3,2,'Another topic')],matcher),{})

    def test_conflicting_or_ambiguous_child_parents_cannot_qualify_missing_parent(self):
        E=self.m.TocEntry
        for entries in ([E('1.1','A',2),E('2.1','B',2)],
                        [E('1.1','A',2),E('2.1','A',2)]):
            headings=[(1,1,'Missing parent'),(2,2,'A')]
            if entries[1].title=='B': headings.append((3,2,'B'))
            self.assertEqual(self.m.child_parent_receipts(headings,self.m.AgendaMatcher(entries)),{})

    def test_unnumbered_runs_match_independent_neighbor_oracle_and_repeat(self):
        from itertools import product
        from types import SimpleNamespace

        modules = [(wg, load('report-parser/agenda_matcher.py', wg))
                   for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5')]

        def continues(previous, following):
            if following.startswith(previous + '.'):
                return True
            if '.' not in previous or '.' not in following:
                return False
            def key(agenda):
                return tuple((0, int(part)) if part.isdigit() else (1, part)
                             for part in agenda.split('.'))
            return (previous.rsplit('.', 1)[0] == following.rsplit('.', 1)[0]
                    and key(following) > key(previous))

        for length in range(6):
            for given in product(('UNKNOWN', '', '1', '1.1', '1.2', '2'), repeat=length):
                expected = list(given)
                for index, agenda in enumerate(given):
                    if agenda != 'UNKNOWN':
                        continue
                    previous = next((value for value in reversed(given[:index]) if value != 'UNKNOWN'), None)
                    following = next((value for value in given[index + 1:] if value != 'UNKNOWN'), None)
                    if previous and following and continues(previous, following):
                        expected[index] = previous
                for wg, module in modules:
                    with self.subTest(wg=wg, given=given):
                        for _ in range(2):
                            sections = [SimpleNamespace(agenda_number=value) for value in given]
                            module.inherit_unnumbered(sections)
                            self.assertEqual([section.agenda_number for section in sections], expected)
                            module.inherit_unnumbered(sections)
                            self.assertEqual([section.agenda_number for section in sections], expected)

        class CountedSections(list):
            def __init__(self, values):
                super().__init__(values)
                self.visits = 0
                self.indexed = 0

            def __iter__(self):
                for value in super().__iter__():
                    self.visits += 1
                    yield value

            def __getitem__(self, index):
                if isinstance(index, slice):
                    raise AssertionError('상속 판정은 전체 UNKNOWN 구간을 복사하지 않는다')
                self.indexed += 1
                return super().__getitem__(index)

        for wg, module in modules:
            for previous, following, inherited in [('1.1', '1.2', True),
                                                    ('1.2', '1.1', False)]:
                with self.subTest(wg=wg, previous=previous, following=following):
                    given = [previous] + ['UNKNOWN'] * 5000 + [following]
                    sections = CountedSections(SimpleNamespace(agenda_number=value) for value in given)
                    with patch.object(module, '_continues', wraps=module._continues) as compare:
                        module.inherit_unnumbered(sections)
                    self.assertEqual(sections.visits, len(given))
                    self.assertLessEqual(sections.indexed, len(given))
                    self.assertEqual(compare.call_count, 1)
                    expected = [previous] * 5001 + [following] if inherited else given
                    self.assertEqual([section.agenda_number for section in sections], expected)

    def test_annex_outline_bounds_agree_for_paragraph_and_block_views(self):
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn

        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            m = load('report-parser/annex.py', wg)
            for outline, annex in [('-1', False), ('0', True), ('8', True),
                                   ('9', False), ('10', False), ('invalid', False)]:
                with self.subTest(wg=wg, outline=outline), tempfile.TemporaryDirectory() as directory:
                    doc = Document(); doc.add_paragraph('Before')
                    doc.add_table(rows=1, cols=1)
                    paragraph = doc.add_paragraph('Annex A source topic')
                    level = OxmlElement('w:outlineLvl'); level.set(qn('w:val'), outline)
                    paragraph._p.get_or_add_pPr().append(level)
                    doc.add_paragraph('Following decision')
                    path = Path(directory) / 'fixture.docx'; doc.save(path)
                    before = path.read_bytes()
                    for _ in range(2):
                        current = Document(path)
                        blocks = list(current.element.body)
                        p = current.paragraphs[1]
                        self.assertEqual(m.is_annex_heading(p.text, p.style.name.lower(),
                                                           m.outline_level(p._element)), annex)
                        if hasattr(m, 'paragraph_annex_start'):
                            self.assertEqual(m.paragraph_annex_start(current.paragraphs),
                                             1 if annex else len(current.paragraphs))
                        if wg == 'RAN2':
                            self.assertEqual(m.annex_blocks(path, blocks),
                                             set(range(2, len(blocks))) if annex else set())
                        else:
                            self.assertEqual(m.block_annex_start(path, blocks),
                                             2 if annex else len(blocks))
                    self.assertEqual(path.read_bytes(), before)
            self.assertTrue(m.is_annex_heading('Annex A', 'heading 1', -1))
            self.assertFalse(m.is_annex_heading('Annex A', 'toc 1', 0))
            self.assertFalse(m.is_annex_heading('Body mentions Annex A', 'heading 1', 0))
            if wg == 'RAN2':
                self.assertTrue(m.annex_is_body('Annex B Break-out session results'))


class WorkingGroupHeadingContext(unittest.TestCase):
    def modules(self):
        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            yield wg, load('report-parser/agenda_matcher.py', wg)

    def test_actual_wg_report_section_builders_keep_repeated_titles_in_each_parent(self):
        for wg, matcher_module in self.modules():
            with self.subTest(wg=wg), tempfile.TemporaryDirectory() as directory:
                # RAN5 treats Heading 1 as document text; its first agenda heading is Heading 2.
                parent_level = 2 if wg == 'RAN5' else 1
                child_level = parent_level + 1
                E = matcher_module.TocEntry
                title = 'Synthetic shared topic'
                entries = [E('1', 'Example parent one', parent_level),
                           E('1.1', title, child_level),
                           E('2', 'Example parent two', parent_level),
                           E('2.1', title, child_level)]
                document = Document()
                document.add_heading('1.\tExample parent one', level=parent_level)
                document.add_heading(title, level=child_level)
                document.add_paragraph('Synthetic first body')
                document.add_heading('2.\tExample parent two', level=parent_level)
                document.add_heading(title, level=child_level)
                document.add_paragraph('Synthetic second body')
                path = Path(directory) / 'synthetic-report.docx'
                document.save(path)
                before = path.read_bytes()
                module = load('report-parser/report_parser.py', wg)
                parser = module.ReportParser.__new__(module.ReportParser)
                parser.docx_path = path
                for _ in range(2):
                    matcher = module.AgendaMatcher(entries)
                    sections = parser._build_sections(matcher)
                    self.assertEqual([s.agenda_number for s in sections],
                                     ['1', '1.1', '2', '2.1'])
                self.assertEqual(path.read_bytes(), before)

    def test_all_wgs_distinguish_unique_ambiguous_and_parent_fallback_candidates(self):
        for wg, module in self.modules():
            with self.subTest(wg=wg):
                E = module.TocEntry
                matcher = module.AgendaMatcher([
                    E('1.1', 'Synthetic repeated topic', 2),
                    E('2.1', 'Synthetic repeated topic', 2),
                    E('3.1', 'A unique fixture heading', 2)])
                self.assertEqual(matcher.match('A unique fixture heading'), '3.1')
                self.assertIsNone(matcher.match('Synthetic repeated topic'))
                self.assertEqual(matcher.match_with_fallback('Synthetic repeated topic'), 'UNKNOWN')
                self.assertEqual(matcher.match('Synthetic repeated topic', '1', 2), '1.1')
                self.assertIsNone(matcher.match('Synthetic repeated topic', '3', 2))
                self.assertEqual(matcher.match_with_fallback('Synthetic repeated topic', '3', 2), '3')
                ambiguous = module.AgendaMatcher([
                    E('1.1', 'Synthetic repeated topic', 2),
                    E('1.2', 'Synthetic repeated topic', 2)])
                self.assertEqual(ambiguous.match_with_fallback('Synthetic repeated topic', '1', 2), '1')

    def test_all_wgs_preserve_title_level_binding_and_context_for_all_match_modes(self):
        for wg, module in self.modules():
            with self.subTest(wg=wg):
                E = module.TocEntry
                title = 'A synthetic source heading with repeated words and enough characters for matching'
                matcher = module.AgendaMatcher([
                    E('1.1', title, 2), E('2.1', title, 2)])
                headings = [title, '  ' + title.upper() + '.  ', title[:-8],
                            title.replace('repeated', 'repeateD?')]
                for heading in headings:
                    with self.subTest(heading=heading):
                        self.assertEqual(matcher.match(heading, '1', 2), '1.1')
                        self.assertEqual(matcher.match(heading, '2', 2), '2.1')
                        self.assertIsNone(matcher.match(heading, None, 2))
                        self.assertIsNone(matcher.match(heading, '3', 2))
                levels = module.AgendaMatcher([
                    E('1', 'Synthetic top topic', 1),
                    E('1', 'Synthetic reference label', 2),
                    E('1.1', 'Repeated level label', 2),
                    E('1.1.1', 'Repeated level label', 3)])
                self.assertEqual(levels.match('Synthetic top topic', None, 1), '1')
                self.assertIsNone(levels.match('Synthetic top topic', None, 2))
                self.assertEqual(levels.match('Repeated level label', '1', 2), '1.1')
                self.assertEqual(levels.match('Repeated level label', '1', 3), '1.1.1')

    def test_all_wgs_keep_explicit_agenda_number_precedence_and_supported_heading_depth(self):
        depths = {'RAN1': 5, 'RAN2': 6, 'RAN3': 6, 'RAN4': 7, 'RAN5': 8}
        for wg, module in self.modules():
            with self.subTest(wg=wg):
                matcher = module.AgendaMatcher([])
                for heading, expected in [
                    ('1. Example numbered topic', '1'),
                    ('1.2 Example numbered topic', '1.2'),
                    ('7.2a Example numbered topic', '7.2a'),
                    ('2\tExample numbered topic', '2'),
                    ('3.4', '3.4'),
                ]:
                    self.assertEqual(matcher.match(heading, '9', 8), expected)
                self.assertIsNone(matcher.match('10 MHz synthetic body text'))
                level = depths[wg]
                E = module.TocEntry
                builder = module.SectionBuilder(module.AgendaMatcher([
                    E('6', 'Synthetic parent', level - 1),
                    E('6.1a', 'Synthetic deepest topic', level)]))
                builder.process_heading('6.\tSynthetic parent', level - 1, 0)
                self.assertEqual(builder.process_heading(
                    'Synthetic deepest topic', level, 1).agenda_number, '6.1a')

    def test_ran2_restated_normal_paragraph_requires_unchanged_number_and_full_title(self):
        module = load('report-parser/agenda_matcher.py', 'RAN2')
        matcher = module.AgendaMatcher([
            module.TocEntry('4.2', 'Synthetic complete heading', 2)])
        self.assertEqual(matcher.restated_entry('4.2 Synthetic complete heading'), '4.2')
        self.assertIsNone(matcher.restated_entry('4.2 Synthetic complete'))
        self.assertIsNone(matcher.restated_entry('4.3 Synthetic complete heading'))


class DecisionBodyMapping(unittest.TestCase):
    def test_actual_equation_converter_reaches_paragraph_and_table_decision_views(self):
        from docx.oxml import OxmlElement
        from types import SimpleNamespace

        m = load('report-parser/decision_extractor.py')
        eq = sys.modules[m.build_text_with_latex.__module__]
        def math(paragraph):
            equation = OxmlElement('m:oMath'); run = OxmlElement('m:r')
            text = OxmlElement('m:t'); text.text = 'x'
            run.append(text); equation.append(run); paragraph._p.append(equation)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'Final_Report_RAN1-123.docx'
            doc = Document(); doc.add_paragraph('Agreement:')
            math(doc.add_paragraph('Value '))
            math(doc.add_table(rows=1, cols=1).cell(0, 0).paragraphs[0]); doc.save(path)
            before = path.read_bytes(); converter = eq.EquationConverter(max_workers=1)
            def pandoc(args, **kwargs):
                self.assertEqual(args[0], 'pandoc')
                import zipfile
                with zipfile.ZipFile(args[1]) as package:
                    self.assertIn(b'oMath', package.read('word/document.xml'))
                return SimpleNamespace(returncode=0, stdout=r'\(x\)')
            try:
                with patch.object(eq.shutil, 'which', return_value='/synthetic/pandoc'), \
                     patch.object(eq.subprocess, 'run', side_effect=pandoc):
                    for _ in range(2):
                        agreement = m.extract_decisions_from_docx(path, [], 'RAN1#123', converter)[0][0]
                        self.assertEqual(agreement.content, 'Value [EQUATION]\n| [EQUATION] |')
                        self.assertEqual(agreement.content_with_equations, 'Value $x$\n| $x$ |')
                        self.assertEqual(agreement.body_blocks, [0, 3])
                        self.assertEqual(list(converter._temp_base.iterdir()), [])
                self.assertEqual(path.read_bytes(), before)
            finally:
                work = converter._temp_base
                converter.cleanup()
                if work is not None: self.assertFalse(work.exists())

    def test_real_docx_table_note_scope_and_repeated_extraction(self):
        m = load('report-parser/decision_extractor.py')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'Final_Report_RAN1-123.docx'
            doc = Document(); doc.add_paragraph('Topic', style='Heading 1')
            doc.add_paragraph('Agreement:')
            table = doc.add_table(rows=1, cols=2)
            table.cell(0, 0).text = 'R1-1234567'; table.cell(0, 1).text = 'is agreed'
            doc.add_paragraph('Note: preserve note')
            doc.add_paragraph('Conclusion: no consensus on TBD')
            doc.add_paragraph('Working assumption: FFS is retained')
            doc.add_paragraph('Annex A', style='Heading 1')
            doc.add_paragraph('Agreement: excluded annex'); doc.save(path)
            before = path.read_bytes()
            sections = [m.Section(title='Topic', heading_level=1, start_index=0,
                                  end_index=5, agenda_number='6.1')]
            previous = None
            for _ in range(2):
                current = m.docx_text.open_document(path)
                paragraphs = m.docx_text.body_paragraphs(current)
                extractor = m.DecisionExtractor(sections, docx_path=path)
                for _ in range(2):
                    groups = extractor.extract_decisions(paragraphs, 'RAN1#123')
                    self.assertEqual([len(group) for group in groups], [1, 1, 1])
                    agreement, conclusion, assumption = [group[0] for group in groups]
                    self.assertEqual(agreement.content, '| R1-1234567 | is agreed |')
                    self.assertEqual(agreement.note, 'preserve note')
                    self.assertEqual(agreement.referenced_tdocs, ['R1-1234567'])
                    self.assertEqual(agreement.body_blocks, [1, 4])
                    self.assertEqual(conclusion.body_blocks, [4, 5])
                    self.assertFalse(conclusion.has_consensus); self.assertTrue(conclusion.has_tbd)
                    self.assertTrue(assumption.has_ffs)
                    self.assertEqual([row.agenda_item for row in (agreement, conclusion, assumption)], ['6.1']*3)
                    actual = [[vars(row) for row in group] for group in groups]
                    if previous is not None: self.assertEqual(actual, previous)
                    previous = actual
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(m.extract_decisions_from_docx(path, sections, 'RAN1#123'), groups)
            from docx.opc.exceptions import PackageNotFoundError
            with self.assertRaises(PackageNotFoundError):
                m.extract_decisions_from_docx(path.with_name('missing.docx'), sections, 'RAN1#123')
            broken = path.with_name('broken.docx'); broken.write_bytes(b'invalid ZIP')
            with self.assertRaisesRegex(ValueError, 'Word 문서 형식'):
                m.extract_decisions_from_docx(broken, sections, 'RAN1#123')


class ReportPipeline(unittest.TestCase):
    def test_embedded_generation_and_json_restore_then_actual_cli_retries(self):
        import shutil
        m = load('report-parser/report_parser.py')
        eq = sys.modules[m.EquationConverter.__module__]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); path = root/'Final_Report_RAN1-123.docx'
            doc = Document(); doc.styles.add_style('toc 1', WD_STYLE_TYPE.PARAGRAPH)
            doc.add_paragraph('6\tMaintenance\t1', style='toc 1')
            doc.add_paragraph('Maintenance', style='Heading 1')
            doc.add_paragraph('Table 1: Values'); doc.add_table(rows=2, cols=2)
            doc.save(path); source = path.read_bytes()
            previous_json = json.dumps({'meeting_id': 'RAN1#123', 'docx_path': str(path)}).encode()
            base = root/'artifacts'; output = root/'parsed/RAN1_123.json'
            output.parent.mkdir()
            slots = [base/kind/'RAN1/RAN1_123' for kind in ('figures', 'charts', 'tables')]
            foreign = base/'figures/RAN1/RAN1_999/keep'
            foreign.parent.mkdir(parents=True); foreign.write_bytes(b'other meeting')

            def seed():
                for slot in slots:
                    if slot.exists(): shutil.rmtree(slot)
                    slot.mkdir(parents=True); (slot/'old').write_bytes(slot.parts[-3].encode())
                output.write_bytes(previous_json); output.chmod(0o640)

            def old_intact():
                for slot in slots:
                    self.assertEqual(list(slot.iterdir()), [slot/'old'])
                    self.assertEqual((slot/'old').read_bytes(), slot.parts[-3].encode())
                self.assertEqual(output.read_bytes(), previous_json)
                self.assertEqual(output.stat().st_mode & 0o777, 0o640)
                self.assertEqual(list(base.glob('.report-generation-*')), [])
                self.assertEqual(foreign.read_bytes(), b'other meeting')

            def retry():
                for _ in range(2):
                    report = m.parse_report(path, output_base=base, output_path=output)
                    self.assertEqual(report.total_embedded, 1)
                    self.assertTrue(Path(report.tables[0].file_path).is_file())
                    self.assertNotIn('.report-generation-', report.tables[0].file_path)
                    self.assertEqual(json.loads(output.read_text())['tables'][0]['file_path'],
                                     report.tables[0].file_path)
                    self.assertEqual(list(slots[0].iterdir()), [])
                    self.assertEqual(list(slots[1].iterdir()), [])
                    self.assertEqual(list(base.glob('.report-generation-*')), [])
                    self.assertEqual(output.stat().st_mode & 0o777, 0o640)

            with patch.object(eq.shutil, 'which', return_value='/synthetic/pandoc'), \
                 patch.object(eq.subprocess, 'run', side_effect=AssertionError('native converter denied')):
                for error in (OSError, KeyboardInterrupt):
                    seed()
                    with patch.object(m.ReportParser, '_extract_figures_and_charts', side_effect=error('extract')):
                        with self.assertRaises(error): m.parse_report(path, output_base=base, output_path=output)
                    old_intact(); retry()
                seed()
                with patch.object(m.ParsedReport, 'to_dict', return_value={
                        'meeting_id': 'RAN1#123', 'docx_path': str(path), 'bad': object()}):
                    with self.assertRaises(TypeError): m.parse_report(path, output_base=base, output_path=output)
                old_intact(); retry()
                replace = m.os.replace
                for error in (OSError, KeyboardInterrupt):
                    for after in (False, True):
                        for move in range(8):
                            seed(); seen = [0]
                            def fail_move(src, dst):
                                publication = Path(dst) in [*slots, output] or Path(dst).parent.name == '.previous'
                                if publication:
                                    index = seen[0]; seen[0] += 1
                                    if index == move:
                                        if after: replace(src, dst)
                                        raise error('generation move')
                                return replace(src, dst)
                            with self.subTest(error=error.__name__, after=after, move=move), \
                                 patch.object(m.os, 'replace', side_effect=fail_move):
                                with self.assertRaises(error):
                                    m.parse_report(path, output_base=base, output_path=output)
                            old_intact(); retry()
                seed()
                def fail_install_and_restore(src, dst):
                    if Path(dst) == slots[0]:
                        raise OSError('install and rollback fault')
                    return replace(src, dst)
                with patch.object(m.os, 'replace', side_effect=fail_install_and_restore):
                    with self.assertRaisesRegex(m.GenerationRecoveryError, 'retained originals at') as failure:
                        m.parse_report(path, output_base=base, output_path=output)
                recovery = list(base.glob('.report-generation-*'))
                self.assertEqual(len(recovery), 1)
                self.assertIn(str(recovery[0]), str(failure.exception))
                backup = recovery[0]/'.previous/0'
                self.assertEqual((backup/'old').read_bytes(), b'figures')
                self.assertEqual(output.read_bytes(), previous_json)
                replace(backup, slots[0]); shutil.rmtree(recovery[0])
                old_intact(); retry()
                with patch.dict(sys.modules, {'report_parser': m}):
                    cli = load('report-parser/01_parse_all.py')
                cli.OUTPUT_DIR = output.parent; cli.EMBEDDED_DIR = base
                seed()
                with patch.object(m.ReportParser, '_extract_figures_and_charts', side_effect=OSError('CLI extract')):
                    self.assertEqual(cli.parse_single_report(path)['status'], 'error')
                old_intact()
                for _ in range(2): self.assertEqual(cli.parse_single_report(path)['status'], 'success')
            self.assertEqual(path.read_bytes(), source)
            self.assertEqual(foreign.read_bytes(), b'other meeting')

    def test_nested_table_equations_follow_displayed_merged_cells(self):
        from xml.etree import ElementTree as ET

        for wg in ('RAN1', 'RAN2', 'RAN4'):
            m = load('report-parser/table_extractor.py', wg)

            def cell(value, merge=None):
                properties = (f'<w:tcPr><w:vMerge w:val="{merge}"/></w:tcPr>'
                              if merge else '')
                return (f'<w:tc>{properties}<w:p><m:oMath><m:r><m:t>{value}</m:t>'
                        '</m:r></m:oMath></w:p></w:tc>')

            def table(rows):
                return '<w:tbl>' + ''.join(f'<w:tr>{row}</w:tr>' for row in rows) + '</w:tbl>'

            cases = (
                ('merged', [cell('visible', 'restart'), cell('hidden', 'continue')], ['visible']),
                ('ordinary', [cell('first'), cell('second')], ['first', 'second']),
                ('orphan_continue', [cell('visible', 'continue')], ['visible']),
            )
            for name, rows, expected in cases:
                for nested in (False, True):
                    with self.subTest(wg=wg, case=name, nested=nested):
                        content = table(rows)
                        if nested:
                            content = table([f'<w:tc>{content}<w:p/></w:tc>'])
                        root = ET.fromstring(
                            f'<w:document xmlns:w="{m.W_NS}" xmlns:m="{m.M_NS}">'
                            f'{content}</w:document>')[0]
                        seen = []
                        cleaned = []

                        class Converter:
                            def preprocess_paragraphs(self, paragraphs):
                                for paragraph in paragraphs:
                                    seen.append(''.join(paragraph._element.itertext()))
                                return {i: {0: value} for i, value in enumerate(seen)}

                            def cleanup(self):
                                cleaned.append(True)

                        with patch.object(m, 'EquationConverter', Converter):
                            equations = m._extract_cell_equations(root)
                        self.assertEqual(seen, expected)
                        self.assertEqual(equations, [f'${value}$' for value in expected]
                                         if wg == 'RAN1' else expected)
                        self.assertEqual(cleaned, [True])
                        self.assertIn('[EQUATION]', m._convert_table_to_html(root))

    def test_actual_table_html_preserves_output_on_failure_and_scope_on_retry(self):
        m = load('report-parser/table_extractor.py')
        shared = sys.modules[m.save_bytes_atomic.__module__]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); path = root/'Final_Report_RAN1-123.docx'
            doc = Document(); doc.add_paragraph('Table 1.2-3: A & B')
            table = doc.add_table(rows=4, cols=2)
            for index, row in enumerate(table.rows):
                row.cells[0].text = f'A & <{index}'; row.cells[1].text = str(index)
            table.cell(0, 0).merge(table.cell(1, 0))
            table.cell(2, 0).merge(table.cell(2, 1))
            doc.add_paragraph('Annex A', style='Heading 1')
            doc.add_paragraph('Table 2: excluded'); doc.add_table(rows=2, cols=2)
            doc.save(path); source_bytes = path.read_bytes()
            out = root/'tables'; out.mkdir()
            target = out/'TBL-123-001_1-2-3.html'; target.write_bytes(b'previous HTML'); target.chmod(0o640)
            for failure in (OSError, KeyboardInterrupt):
                for boundary in ('fsync', 'replace'):
                    target.write_bytes(b'previous HTML')
                    with self.subTest(failure=failure.__name__, boundary=boundary):
                        with patch.object(shared.os, boundary, side_effect=failure('table publication')):
                            with self.assertRaises(failure): m.extract_tables_from_docx(path, 'RAN1#123', out)
                        self.assertEqual(target.read_bytes(), b'previous HTML')
                        self.assertEqual(target.stat().st_mode & 0o777, 0o640)
                        self.assertEqual(list(root.rglob('*.tmp')), [])
                        previous = None
                        for _ in range(2):
                            actual = m.extract_tables_from_docx(path, 'RAN1#123', out)
                            self.assertEqual(len(actual), 1)
                            self.assertEqual(actual[0].table_id, 'TBL-123-001')
                            self.assertEqual(actual[0].caption, 'Table 1.2-3: A & B')
                            self.assertEqual(actual[0].file_path, str(target))
                            markup = target.read_text()
                            self.assertIn('rowspan="2"', markup); self.assertIn('colspan="2"', markup)
                            self.assertIn('A &amp; &lt;0', markup)
                            if previous is not None: self.assertEqual(markup, previous)
                            previous = markup
            self.assertEqual(path.read_bytes(), source_bytes)

    def test_actual_docx_pipeline_and_atomic_report_save_retry(self):
        m = load('report-parser/report_parser.py')
        eq = sys.modules[m.EquationConverter.__module__]
        ChartInfo = m.ParsedReport.to_dict.__globals__['ChartInfo']
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'Final_Report_RAN1-123.docx'
            doc = Document(); doc.styles.add_style('toc 1', WD_STYLE_TYPE.PARAGRAPH)
            doc.add_paragraph('6\tMaintenance\t1', style='toc 1')
            doc.add_paragraph('Maintenance', style='Heading 1')
            doc.add_paragraph('Agreement: R1-1234567 is agreed.')
            doc.add_paragraph('Table 1: Values')
            table = doc.add_table(rows=2, cols=2)
            for cell, text in zip((table.cell(0, 0), table.cell(0, 1),
                                   table.cell(1, 0), table.cell(1, 1)),
                                  ('Parameter', 'Value', 'alpha', '1')):
                cell.text = text
            doc.save(path); source_bytes = path.read_bytes()
            with patch.object(eq.shutil, 'which', return_value='/synthetic/pandoc'), \
                 patch.object(eq.subprocess, 'run', side_effect=AssertionError('native converter denied')):
                report = m.parse_report(path)
                second = m.ReportParser(path).parse()
            actual = report.to_dict(); repeated = second.to_dict()
            actual.pop('parsed_at'); repeated.pop('parsed_at')
            self.assertEqual(actual, repeated)
            self.assertEqual(report.meeting_id, 'RAN1#123')
            self.assertEqual([row.agenda_item for row in report.agreements], ['6'])
            self.assertEqual(report.agreements[0].referenced_tdocs, ['R1-1234567'])
            self.assertEqual(report.tables[0].caption, 'Table 1: Values')
            self.assertEqual(report.total_decisions, 1)
            self.assertEqual(report.total_embedded, 1)
            output = Path(directory)/'report.json'
            m.save_report(report, output); output.chmod(0o640)
            previous = output.read_bytes()
            report.charts.append(ChartInfo('C-1', report.meeting_id, object(), 'chart.xml', 'line', 0))
            with self.assertRaises(TypeError): m.save_report(report, output)
            self.assertEqual(output.read_bytes(), previous)
            report.charts.clear()
            for failure in (OSError, KeyboardInterrupt):
                for boundary in ('fsync', 'replace'):
                    with self.subTest(failure=failure.__name__, boundary=boundary):
                        with patch.object(m.meeting_slot.os, boundary, side_effect=failure('report publication')):
                            with self.assertRaises(failure): m.save_report(report, output)
                        self.assertEqual(output.read_bytes(), previous)
                        self.assertEqual(output.stat().st_mode & 0o777, 0o640)
                        self.assertEqual(list(Path(directory).rglob('*.tmp')), [])
                        for _ in range(2): m.save_report(report, output)
                        self.assertEqual(output.read_bytes(), previous)
            output.write_bytes(b'invalid previous JSON')
            with self.assertRaises(json.JSONDecodeError): m.save_report(report, output)
            self.assertEqual(output.read_bytes(), b'invalid previous JSON')
            output.write_bytes(previous)
            for _ in range(2): m.save_report(report, output)
            self.assertEqual(output.read_bytes(), previous)
            self.assertEqual(path.read_bytes(), source_bytes)


class RolePlacement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load('report-parser/role_extractor.py')

    def test_multiple_title_topics_do_not_override_report_placement(self):
        class S:
            start_index = 704
            agenda_number = '6.2'
        title = 'Session notes for 6.2.1 (MTC) and 6.2.2 (NB-IoT)'
        r = self.m.RoleExtractor('RAN1#100b-e', [S()], {'6.2.1', '6.2.2'})
        self.assertEqual(r._extract_agenda(title, 721), '6.2')

    def test_unknown_report_placement_does_not_invent_primary_title_membership(self):
        r = self.m.RoleExtractor('RAN1#100b-e')
        self.assertEqual(r._extract_agenda('Session notes for 6.2.1 (MTC)', 721), 'UNKNOWN')

    def test_all_role_kinds_deduplicate_per_call_and_repeat_after_failure(self):
        from types import SimpleNamespace
        doc = Document()
        doc.add_paragraph('R1-1234567\tSession notes for Topic\tModerator (ZTE)')
        doc.add_paragraph('R1-1234567\tSession notes for Topic\tModerator (ZTE)')
        doc.add_paragraph('R1-1234568\tFL summary #0 Topic\tFeature Lead (NTT DOCOMO, INC.)')
        doc.add_paragraph('R1-1234569\tModerator summary Round 2 Topic\tModerator (Ericsson)')
        doc.add_paragraph('R1-1234570\tSession notes for template To be used for sharing updates\tModerator (ZTE)')
        doc.add_paragraph('R1-1234571\tSession notes for styled text\tModerator (ZTE)', style='Heading 2')
        doc.add_paragraph('Annex A', style='Heading 1')
        doc.add_paragraph('R1-1234572\tSession notes for Annex\tModerator (ZTE)')
        sections = [SimpleNamespace(start_index=0, agenda_number='6.1')]
        r = self.m.RoleExtractor('RAN1#123', sections)
        expected = None
        for _ in range(2):
            result = r.extract_roles(doc.paragraphs)
            self.assertEqual([len(rows) for rows in result], [1, 1, 1])
            self.assertEqual([rows[0].agenda_item for rows in result], ['6.1']*3)
            self.assertEqual(result[1][0].round_number, 0)
            self.assertEqual(result[1][0].company, 'NTT DOCOMO')
            self.assertEqual(result[2][0].round_number, 2)
            if expected is not None: self.assertEqual(result, expected)
            expected = result
        reader = self.m.docx_text.final_text
        def fail_after_first_role(paragraph):
            if paragraph._p is doc.paragraphs[2]._p:
                raise ValueError('synthetic role text failure')
            return reader(paragraph)
        with patch.object(self.m.docx_text, 'final_text', side_effect=fail_after_first_role):
            with self.assertRaisesRegex(ValueError, 'role text failure'):
                r.extract_roles(doc.paragraphs)
        for _ in range(2): self.assertEqual(r.extract_roles(doc.paragraphs), expected)
        self.assertEqual(r.extract_roles([]), ([], [], []))
        self.assertEqual(r.extract_roles(doc.paragraphs), expected)


class SharedRoleIdentity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load('ontology/01_generate_jsonld.py')

    def report(self):
        return {'meeting_id': 'RAN1#100b-e',
                'fl_summaries': [{'tdoc_number': 'R1-2002705', 'title': 'FL Summary of Maintenance for group MWUS',
                                  'company': 'Qualcomm Incorporated', 'agenda_item': '6.2.2.1', 'paragraph_index': 724}],
                'session_notes': [{'tdoc_number': 'R1-2003132',
                                   'title': 'Session notes for 6.2.1 (MTC) and 6.2.2 (NB-IoT)',
                                   'company': 'Samsung', 'agenda_item': '6.2.1', 'paragraph_index': 721}]}

    def placements(self):
        return {'RAN1:role-agenda:100b-e:R1-2002705:p724':
                    {'evidenceStatus': 'source_verified', 'agendaId': 'tdoc:agenda/100b-6.2.1.1'},
                'RAN1:role-agenda:100b-e:R1-2003132:p721':
                    {'evidenceStatus': 'source_verified', 'agendaId': 'tdoc:agenda/100b-6.2'}}

    def test_actual_main_publishes_complete_generation_or_preserves_previous_bytes(self):
        import contextlib
        import io
        atomic_os = self.m.publish_json_set.__globals__['os']
        names = ('summaries.jsonld', 'session_notes.jsonld', 'role_agenda_evidence.jsonld',
                 'resolutions_agreements.jsonld', 'resolutions_conclusions.jsonld',
                 'resolutions_working_assumptions.jsonld', 'figures.jsonld', 'tables.jsonld',
                 'charts.jsonld', 'decision_dispositions.jsonld', 'resolutions_document_dispositions.jsonld')
        report = {'meeting_id': 'RAN1#1', 'agreements': [{'decision_id': 'AGR-1',
                  'content': 'Synthetic agreement', 'agenda_item': '1', 'body_blocks': None}]}
        fault = [None]
        def dispositions(wg, directory, *, root):
            self.assertEqual(wg, 'RAN1')
            self.assertNotEqual(directory, out)
            for name in names[-2:]:
                (directory/name).write_text(json.dumps({'@graph': []}))
                if fault[0]: raise fault[0]('synthetic staged disposition failure')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            out = root/'generation'
            out.mkdir()
            def reset():
                for name in names: (out/name).write_bytes(('old '+name).encode())
            def snapshot(): return {name: (out/name).read_bytes() for name in names}
            reset()
            with patch.object(self.m, 'OUTPUT_DIR', out), \
                 patch.object(self.m, 'load_all_reports', return_value=[report]), \
                 patch.object(self.m, 'load_registered_role_agendas', return_value={}), \
                 patch.object(self.m, 'prepare_role_placements', return_value={}), \
                 patch.object(self.m, 'generate_for_wg', side_effect=dispositions), \
                 contextlib.redirect_stdout(io.StringIO()):
                previous = snapshot()
                report['charts'] = [{'chart_id': 'C-1', 'paragraph_index': 1}]
                with self.assertRaises(KeyError): self.m.main([])
                self.assertEqual(snapshot(), previous)
                report.pop('charts')
                for error in (OSError, KeyboardInterrupt):
                    for boundary in ('disposition', 'fsync', 'install'):
                        with self.subTest(error=error, boundary=boundary):
                            reset(); previous = snapshot()
                            fault[0] = error if boundary == 'disposition' else None
                            replace = atomic_os.replace
                            fired = []
                            def install(source, destination):
                                if Path(destination) == out/'session_notes.jsonld' and not fired:
                                    fired.append(True)
                                    raise error('synthetic install failure')
                                return replace(source, destination)
                            with contextlib.ExitStack() as stack:
                                if boundary == 'fsync':
                                    stack.enter_context(patch.object(atomic_os, 'fsync', side_effect=error('synthetic fsync failure')))
                                elif boundary == 'install':
                                    stack.enter_context(patch.object(atomic_os, 'replace', side_effect=install))
                                with self.assertRaises(error): self.m.main([])
                            self.assertEqual(snapshot(), previous)
                            self.assertEqual(sorted(p.name for p in root.iterdir()), ['generation'])
                            self.assertEqual(sorted(p.name for p in out.iterdir()), sorted(names))
                            fault[0] = None
                            for _ in range(2):
                                self.m.main([])
                                self.assertEqual(json.loads((out/'resolutions_agreements.jsonld').read_text())['@graph'][0]['resolutionId'], 'AGR-1')
                for error in (OSError, KeyboardInterrupt):
                    reset(); previous = snapshot()
                    with patch.object(atomic_os, 'fsync', side_effect=error('synthetic single save failure')):
                        with self.assertRaises(error): self.m.save_jsonld({'@graph': []}, names[0])
                    self.assertEqual(snapshot(), previous)
                    self.m.save_jsonld({'@graph': []}, names[0])
                    self.assertEqual(json.loads((out/names[0]).read_text())['@graph'], [])

    def test_both_role_producers_use_registered_primary_agenda_and_keep_title(self):
        report = self.report()
        registered = {'tdoc:R1-2002705': 'tdoc:agenda/100b-6.2.1.1',
                      'tdoc:R1-2003132': 'tdoc:agenda/100b-6.2'}
        summary = self.m.generate_summaries_jsonld([report], registered, self.placements())['@graph'][0]
        notes = self.m.generate_session_notes_jsonld([report], registered, self.placements())['@graph'][0]
        self.assertEqual(summary['agenda'], registered[summary['@id']])
        self.assertEqual(notes['agenda'], registered[notes['@id']])
        self.assertEqual(notes['title'], report['session_notes'][0]['title'])
        self.assertEqual(summary['reportedUnderAgenda'], 'tdoc:agenda/100b-6.2.1.1')

    def test_pending_source_placement_does_not_create_direct_reported_edge(self):
        placements = self.placements()
        placements['RAN1:role-agenda:100b-e:R1-2002705:p724']['evidenceStatus'] = 'pending'
        row = self.m.generate_summaries_jsonld([self.report()],
            {'tdoc:R1-2002705': 'tdoc:agenda/100b-6.2.1.1'}, placements)['@graph'][0]
        self.assertNotIn('reportedUnderAgenda', row)

    def test_missing_registration_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Phase-1 source registration'):
            self.m.generate_summaries_jsonld([self.report()], {})

    def test_conflicting_registration_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / 'tdocs.jsonld'
            p.write_text(json.dumps({'@graph': [
                {'@id': 'tdoc:R1-1', 'belongsTo': 'tdoc:agenda/100-6'},
                {'@id': 'tdoc:R1-1', 'belongsTo': 'tdoc:agenda/100-7'}]}))
            with self.assertRaisesRegex(ValueError, 'Conflicting Phase-1'):
                self.m.load_registered_role_agendas(p)

    def test_roles_preflight_before_any_derived_write(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            for name in ('summaries.jsonld', 'session_notes.jsonld'):
                (out / name).write_bytes(b'prior source-bound role artifact')
            with patch.object(self.m, 'OUTPUT_DIR', out), \
                 patch.object(self.m, 'load_all_reports', return_value=[self.report()]), \
                 patch.object(self.m, 'load_registered_role_agendas', return_value={'tdoc:R1-2002705': 'tdoc:agenda/100b-6.2.1.1'}), \
                 patch.object(self.m, 'generate_for_wg') as derived:
                with self.assertRaisesRegex(ValueError, 'Phase-1 source registration'):
                    self.m.main(['--roles-only'])
                derived.assert_not_called()
            for name in ('summaries.jsonld', 'session_notes.jsonld'):
                self.assertEqual((out / name).read_bytes(), b'prior source-bound role artifact')


class DecisionOccurrenceIdentity(unittest.TestCase):
    def report(self):
        return {'meeting_id': 'RAN1#100b-e', 'docx_path': 'retained/report.docx',
                'agreements': [{'decision_id': 'AGR-100b-6.2.2.1-001',
                                'decision_type': 'Agreement', 'paragraph_index': 726,
                                'body_blocks': [730, 735], 'content': 'R1-2001576 is agreed.',
                                'referenced_tdocs': ['R1-2001576'],
                                'agenda_item': '6.2.2.1', 'sequence': 1}]}

    def test_corrected_agenda_and_sequence_keep_same_accepted_occurrence_id(self):
        previous = self.report()
        current = self.report()
        current['agreements'][0].update(decision_id='AGR-100b-6.2.1.1-003', agenda_item='6.2.1.1', sequence=3)
        result = preserve_decision_ids(current, previous)
        self.assertEqual(result['agreements'][0]['decision_id'], previous['agreements'][0]['decision_id'])
        self.assertEqual(result['agreements'][0]['agenda_item'], '6.2.1.1')
        self.assertEqual(current['agreements'][0]['decision_id'], 'AGR-100b-6.2.1.1-003')

    def test_changed_body_span_target_or_kind_does_not_reuse_old_id(self):
        for field, value in [('content', 'R1-2001576 is withdrawn.'), ('body_blocks', [731, 735]),
                             ('referenced_tdocs', ['R1-2001577']), ('decision_type', 'Conclusion')]:
            current = self.report()
            current['agreements'][0].update(decision_id='new-source-occurrence', **{field: value})
            self.assertEqual(preserve_decision_ids(current, self.report())['agreements'][0]['decision_id'],
                             'new-source-occurrence', field)

    def test_other_source_path_and_colliding_ids_fail_before_save(self):
        current = self.report(); current['docx_path'] = 'another/report.docx'
        with self.assertRaisesRegex(ValueError, 'different meeting or source'):
            preserve_decision_ids(current, self.report())
        current = self.report(); current['agreements'].append(dict(current['agreements'][0], paragraph_index=800))
        with self.assertRaisesRegex(ValueError, 'collision'):
            preserve_decision_ids(current, self.report())


class SourcePlacementReconciliation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load('report-parser/reconcile_agendas.py')

    def test_repair_changes_only_agenda_preserving_occurrence_and_unknown_fields(self):
        section = dict(title='A topic', heading_level=2, start_index=1, end_index=9,
                       agenda_number='6.2')
        source = {'meeting_id': 'RAN1#100', 'sections': [dict(section, agenda_number='7.2')],
                  'agreements': [{'decision_id': 'AGR-100-7.2-001', 'agenda_item': '7.2',
                                  'paragraph_index': 3, 'content': 'agreed text',
                                  'body_blocks': [4, 5], 'referenced_tdocs': ['R1-1'],
                                  'unrelated': ['retained']}]}
        expected = deepcopy(source); expected['sections'][0]['agenda_number'] = '6.2'
        expected['agreements'][0]['agenda_item'] = '6.2'
        actual, changes = self.m.repair_report(source, [section])
        self.assertEqual(actual, expected)
        self.assertEqual(len(changes), 2)
        self.assertEqual(source['agreements'][0]['agenda_item'], '7.2')
        with self.assertRaisesRegex(ValueError, 'topology changed'):
            self.m.repair_report(source, [dict(section, end_index=10)])

    def test_verified_enclosing_agenda_does_not_invent_unnumbered_subtopic(self):
        doc = Document()
        doc.styles.add_style('toc 1', WD_STYLE_TYPE.PARAGRAPH)
        doc.add_paragraph('6\tMaintenance\t1', style='toc 1')
        doc.add_paragraph('Maintenance', style='Heading 1')
        doc.add_paragraph('Unnumbered actual topic', style='Heading 2')
        sections = [dict(title='Maintenance', heading_level=1, start_index=1, agenda_number='6'),
                    dict(title='Unnumbered actual topic', heading_level=2, start_index=2, agenda_number='6')]
        toc = [self.m.AgendaMatcher.__init__.__globals__['TocEntry']('6', 'Maintenance', 1,
                                                                  paragraph_index=0)]
        result = self.m.placement_receipts(sections, doc.paragraphs, toc)
        self.assertEqual(result[2]['evidenceStatus'], 'source_verified')
        self.assertEqual(result[2]['agenda'], '6')
        self.assertIn('without_invented_subtopic', result[2]['method'])

    def test_role_requires_actual_source_document_number(self):
        doc = Document(); doc.add_paragraph('R1-1234567\tActual summary\tModerator (X)')
        report = {'meeting_id': 'RAN1#100', 'docx_path': 'source.docx',
                  'fl_summaries': [{'tdoc_number': 'R1-1234568', 'paragraph_index': 0, 'agenda_item': 'UNKNOWN'}]}
        with self.assertRaisesRegex(ValueError, 'actual source paragraph'):
            self.m.role_placement_records(report, [], doc.paragraphs, [], 'f' * 64)

    def test_file_cas_and_partial_failure_restore_only_our_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); out = root / 'receipt'; out.mkdir()
            source = root / 'source'; source.write_bytes(b'fixed source')
            a, b = root / 'a.json', root / 'b.json'
            a.write_bytes(b'old a'); b.write_bytes(b'old b')
            rows = [dict(path=p.name, beforeSha256=self.m.sha(p.read_bytes()), changes=[1], after={'new':p.name})
                    for p in (a,b)]
            writer = self.m.atomic_bytes
            def inject(path, data):
                if path == b:
                    raise OSError('injected second write failure')
                return writer(path, data)
            with patch.object(self.m, 'atomic_bytes', side_effect=inject):
                with self.assertRaisesRegex(OSError, 'second write'):
                    self.m.apply_files(rows, {'source':self.m.sha(source.read_bytes())}, out, root=root)
            self.assertEqual(a.read_bytes(), b'old a'); self.assertEqual(b.read_bytes(), b'old b')
            self.assertEqual(json.loads((out/'file_journal.json').read_text())['status'], 'failed_own_writes_restored')
            a.write_bytes(b'foreign before transaction')
            with self.assertRaisesRegex(ValueError, 'Canonical SHA fence'):
                self.m.apply_files(rows, {}, out, root=root)
            self.assertEqual(a.read_bytes(), b'foreign before transaction')

    def test_rollback_keeps_foreign_edit_and_records_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); out = root / 'receipt'; out.mkdir()
            a, b = root/'a', root/'b'; a.write_bytes(b'A'); b.write_bytes(b'B')
            rows = [dict(path=p.name, beforeSha256=self.m.sha(p.read_bytes()), changes=[1], after={'ours':1}) for p in (a,b)]
            writer = self.m.atomic_bytes
            def inject(path,data):
                if path == b:
                    a.write_bytes(b'foreign concurrent edit')
                    raise OSError('after first write')
                return writer(path,data)
            with patch.object(self.m, 'atomic_bytes', side_effect=inject), self.assertRaises(OSError):
                self.m.apply_files(rows, {}, out, root=root)
            self.assertEqual(a.read_bytes(), b'foreign concurrent edit')
            journal = json.loads((out/'file_journal.json').read_text())
            self.assertEqual(journal['status'], 'failed_requires_review')
            self.assertEqual(journal['requiresReview'], ['a'])

    def test_post_install_failure_restores_existing_and_new_files_then_retries(self):
        for existing in (False, True):
            for failure in (OSError, KeyboardInterrupt):
                with self.subTest(existing=existing, failure=failure.__name__), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory); out = root / 'receipt'; out.mkdir()
                    target = root / 'a.json'
                    if existing:
                        target.write_bytes(b'original'); target.chmod(0o640)
                    before = self.m.sha(b'original') if existing else None
                    rows = [dict(path=target.name, beforeSha256=before,
                                 changes=[1], after={'corrected': True})]
                    writer = self.m.atomic_bytes
                    fired = False
                    def inject(path, data):
                        nonlocal fired
                        writer(path, data)
                        if path == target and not fired:
                            fired = True
                            raise failure('after canonical installation')
                    with patch.object(self.m, 'atomic_bytes', side_effect=inject), self.assertRaises(failure):
                        self.m.apply_files(rows, {}, out, root=root)
                    self.assertTrue(fired)
                    if existing:
                        self.assertEqual(target.read_bytes(), b'original')
                        self.assertEqual(target.stat().st_mode & 0o777, 0o640)
                        self.assertEqual(gzip.decompress((out / 'preimages' / (before + '.gz')).read_bytes()), b'original')
                    else:
                        self.assertFalse(target.exists())
                    journal = json.loads((out / 'file_journal.json').read_text())
                    self.assertEqual(journal['status'], 'failed_own_writes_restored')
                    self.assertEqual(journal['requiresReview'], [])
                    self.assertTrue(journal['records'][0]['restored'])
                    self.assertEqual(list(root.rglob('*.tmp')), [])
                    for _ in range(2):
                        result = self.m.apply_files(rows, {}, out, root=root)
                        self.assertEqual(result['status'], 'complete')
                        self.assertEqual(json.loads(target.read_bytes()), {'corrected': True})
                        rows[0]['beforeSha256'] = self.m.sha(target.read_bytes())

    def test_post_write_checkpoint_failure_restores_files_and_preserves_foreign_edits(self):
        for foreign in (False, True):
            for failure in (OSError, KeyboardInterrupt):
                with self.subTest(foreign=foreign, failure=failure.__name__), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory); out = root / 'receipt'; out.mkdir()
                    target = root / 'a.json'; target.write_bytes(b'original')
                    rows = [dict(path=target.name, beforeSha256=self.m.sha(b'original'),
                                 changes=[1], after={'corrected': True})]
                    writer = self.m.atomic_bytes
                    fired = False
                    def inject(path, data):
                        nonlocal fired
                        if path == out / 'file_journal.json' and not fired and target.read_bytes() != b'original':
                            fired = True
                            if foreign:
                                target.write_bytes(b'foreign edit after installation')
                            raise failure('post-write checkpoint')
                        writer(path, data)
                    with patch.object(self.m, 'atomic_bytes', side_effect=inject), self.assertRaises(failure):
                        self.m.apply_files(rows, {}, out, root=root)
                    self.assertTrue(fired)
                    journal = json.loads((out / 'file_journal.json').read_text())
                    self.assertEqual(target.read_bytes(), b'foreign edit after installation' if foreign else b'original')
                    self.assertEqual(journal['requiresReview'], [target.name] if foreign else [])
                    self.assertEqual(journal['status'], 'failed_requires_review' if foreign else 'failed_own_writes_restored')
                    self.assertEqual(list(root.rglob('*.tmp')), [])
                    rows[0]['beforeSha256'] = self.m.sha(target.read_bytes())
                    self.assertEqual(self.m.apply_files(rows, {}, out, root=root)['status'], 'complete')


class SourceAgendaClosure(unittest.TestCase):
    def fixture(self, root):
        from agenda_source_supplements import ledger_path
        source = root/'ontology/input/tsg/RAN/formal/meetings/RAN1/Final_Report/Final_Report_RAN1-100.docx'
        source.parent.mkdir(parents=True)
        doc = Document()
        doc.styles.add_style('toc 1', WD_STYLE_TYPE.PARAGRAPH)
        doc.add_paragraph('6\tMaintenance\t1', style='toc 1')
        doc.add_paragraph('Maintenance', style='Heading 1'); doc.save(source)
        master = root/'ontology/input/tsg/RAN/formal/meetings/RAN1/TDoc_List/TDoc_List_TSGR1_100.xlsx'
        master.parent.mkdir(parents=True)
        book = Workbook(); sheet=book.active; sheet.title='TDoc_List'
        sheet.append(['TDoc','Agenda item']); sheet.append(['R1-1234567','6.1']); book.save(master)
        record = {'id':'tdoc:agenda/100-6','meetingId':'RAN1#100', 'agendaNumber':'6', 'agendaDescription':'Maintenance',
                  'source':{'path':str(source.relative_to(root)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()},
                  'tdocList':{'path':str(master.relative_to(root)),'sha256':hashlib.sha256(master.read_bytes()).hexdigest(),'sheet':'TDoc_List'},
                  'evidence':[{'paragraphIndex':1,'quote':'Maintenance','role':'source_heading'},
                              {'paragraphIndex':0,'quote':'6\tMaintenance\t1','role':'numbered_table_of_contents_entry'}]}
        document = {'schemaVersion':'1.0.0','wg':'RAN1','records':[record]}
        path = ledger_path(root,'RAN1'); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(document))
        return record, document

    def test_actual_toc_heading_and_xlsx_absence_bind_source_agenda(self):
        from agenda_source_supplements import validated_records, supplement_agenda_items, legacy_expected_counts
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); record, document=self.fixture(root)
            self.assertEqual(validated_records(root,'RAN1'), [record])
            self.assertEqual(validated_records(root,'RAN1',{'RAN1#101'}), [])
            actual=supplement_agenda_items(root,'RAN1',{}, {'RAN1#100'})
            self.assertEqual(actual[('100','6')]['@id'], record['id'])
            self.assertEqual(legacy_expected_counts(root,'RAN1',{'AgendaItem':2})['AgendaItem'],3)
            document['records'][0]['evidence'][0]['quote']='fabricated heading'
            with self.assertRaisesRegex(ValueError,'not bound'):
                validated_records(root,'RAN1',document=document)

    def test_source_change_or_number_without_actual_toc_rejected(self):
        from agenda_source_supplements import validated_records
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); record, document=self.fixture(root)
            document['records'][0]['agendaNumber']='7'; document['records'][0]['id']='tdoc:agenda/100-7'
            with self.assertRaisesRegex(ValueError,'not bound'):
                validated_records(root,'RAN1',document=document)
            document['records'][0]['source']['sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'SHA drift'):
                validated_records(root,'RAN1',document=document)

    def test_complete_closure_unions_physical_master_editions_and_fences_both(self):
        m=load('report-parser/reconcile_agendas.py')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); record,_=self.fixture(root)
            source=root/record['source']['path']
            doc=Document(source)
            doc.add_paragraph('7\tNew source parent\t2',style='toc 1')
            doc.add_paragraph('New source parent',style='Heading 1');doc.save(source)
            second=root/'ontology/input/tsg/RAN/formal/meetings/RAN1/TDoc_List/TDoc_List_TSGR1_100_e.xlsm'
            book=Workbook();sheet=book.active;sheet.title='TDoc_List'
            sheet.append(['TDoc','Agenda item']);sheet.append(['R1-7654321','6']);book.save(second)
            phase1=root/'ontology/output/tsg/RAN/formal/instances/phase-1/RAN1'
            phase1.mkdir(parents=True)
            (phase1/'agenda_items.jsonld').write_text(json.dumps({'@graph':[]}))
            sections,paragraphs,toc=m.source_sections(source,include_toc=True)
            report={'after':{'meeting_id':'RAN1#100','sections':sections},
                    'source':{'path':str(source.relative_to(root)),
                              'sha256':hashlib.sha256(source.read_bytes()).hexdigest()},
                    'headingPlacementAssessments':m.placement_receipts(sections,paragraphs,toc)}
            artifacts=[{'after':{'@graph':[]}} for _ in range(5)]
            with patch.object(m,'ROOT',root),patch.object(m,'PHASE1',phase1):
                closure,records=m.agenda_closure([report],artifacts)
            self.assertEqual([r['id'] for r in records],['tdoc:agenda/100-7'])
            ledger=closure[0]['after']
            self.assertEqual(len(ledger['sourceInputs']),3)
            self.assertIn(str(second.relative_to(root)),ledger['sourceInputs'])
            self.assertEqual(closure[1]['after']['@graph'][0]['tdoc:agendaNumber'],'7')


class LivePlacementGuard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=load('neo4j/reconcile_agenda_placements.py')

    def fixture(self):
        before={'nodes':[{'element':'doc','labels':['Tdoc'], 'properties':{'title':'preserved','unknown':[1,2]}}],
                'edges':[{'element':'primary','start':'doc','end':'registered','type':'BELONGS_TO','properties':{'source':'P1'}},
                         {'element':'foreign','start':'doc','end':'company','type':'SUBMITTED_BY','properties':{}}]}
        plan={'creates':{},'elements':['doc'],'before':before,'changedResolutions':{},'bindings':{}}
        contract={'fences':{},'agendas':{},'edges':[]}
        return contract,plan,deepcopy(before)

    def test_source_fence_tracks_report_population_and_repair_before_transaction(self):
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as directory, patch.object(self.m, 'ROOT', Path(directory)):
            root = Path(directory)
            reports = root/'ontology/output/tsg/RAN/formal/parsed_reports/RAN1'
            reports.mkdir(parents=True)
            source = reports/'RAN1_100.json'
            source.write_bytes(b'{}')
            relative = source.relative_to(root).as_posix()
            contract, plan, _ = self.fixture()
            contract.update(parsedReportPaths=[relative],
                            fences={relative: hashlib.sha256(source.read_bytes()).hexdigest()})
            extra = reports/'RAN1_101.json'
            tx = Mock()
            for mutation in ('add', 'remove', 'bytes'):
                if mutation == 'add': extra.write_bytes(b'{}')
                elif mutation == 'remove': source.unlink()
                else: source.write_bytes(b'changed')
                with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, 'source list|generation drift'):
                    self.m.apply_transaction(tx, contract, plan)
                tx.run.assert_not_called()
                extra.unlink(missing_ok=True)
                source.write_bytes(b'{}')
                for _ in range(2): self.m.source_fence(contract)

    def test_source_or_population_drift_fails_before_first_write(self):
        contract,plan,_=self.fixture()
        tx=__import__('unittest').mock.Mock()
        with patch.object(self.m,'source_fence',side_effect=ValueError('source drift')):
            with self.assertRaisesRegex(ValueError,'source drift'):
                self.m.apply_transaction(tx,contract,plan)
        tx.run.assert_not_called()
        changed=deepcopy(plan); changed['elements'].append('new-foreign-node')
        with patch.object(self.m,'source_fence'), patch.object(self.m,'prepare',return_value=changed):
            with self.assertRaisesRegex(ValueError,'preimage/endpoint population'):
                self.m.apply_transaction(tx,contract,plan)
        tx.run.assert_not_called()

    def test_exact_readback_rejects_any_existing_property_or_primary_relation_change(self):
        contract,plan,after=self.fixture()
        for mutate in ('property','primary'):
            current=deepcopy(after)
            if mutate=='property': current['nodes'][0]['properties']['title']='foreign edit'
            else: current['edges'][0]['end']='reported-instead-of-registered'
            with patch.object(self.m,'source_fence'), patch.object(self.m,'prepare',return_value=plan), \
                 patch.object(self.m,'endpoint_bindings',return_value={}), \
                 patch.object(self.m,'full_snapshot',return_value=current):
                with self.assertRaisesRegex(ValueError,'existing live node|unrelated incident'):
                    self.m.apply_transaction(None,contract,plan)

    def test_no_change_transaction_preserves_unknown_properties_and_primary_edge(self):
        contract,plan,after=self.fixture()
        with patch.object(self.m,'source_fence'), patch.object(self.m,'prepare',return_value=plan), \
             patch.object(self.m,'endpoint_bindings',return_value={}), \
             patch.object(self.m,'full_snapshot',return_value=after):
            self.assertEqual(self.m.apply_transaction(None,contract,plan),plan['before'])

    def test_agenda_iri_cannot_substitute_for_class_or_actual_composite_key(self):
        from unittest.mock import Mock
        identity='tdoc:agenda/100-2'
        agendas={identity:{'id':identity,'meetingNumber':'100','agendaNumber':'2'}}
        for labels,meeting,number in [(['Feature'],'100','2'),(['AgendaItem'],'99','7')]:
            tx=Mock(); tx.run.return_value.data.return_value=[{
                'element':'foreign','labels':labels,
                'properties':{'id':identity,'meetingNumber':meeting,'agendaNumber':number}}]
            with self.assertRaisesRegex(ValueError,'class/composite key'):
                self.m.endpoint_bindings(tx,{identity},agendas)

    def test_unqualified_extra_reported_edge_requires_review_without_deleting_it(self):
        contract,plan,before=self.fixture()
        contract.update(primaries={'tdoc:R1-1':'tdoc:agenda/100-1'},
                        edges=[('tdoc:R1-1','REPORTED_UNDER_AGENDA','tdoc:agenda/100-2')])
        bindings={'tdoc:R1-1':{'element':'doc'},'tdoc:agenda/100-2':{'element':'new'}}
        before['edges'].append({'element':'old-reported','start':'doc','end':'old',
                                'type':'REPORTED_UNDER_AGENDA','properties':{}})
        original=deepcopy(before)
        with self.assertRaisesRegex(ValueError,'outside the canonical qualified source scope'):
            self.m.check_reported_scope(before,bindings,contract)
        self.assertEqual(before,original)

    def test_multiple_canonical_qualified_reported_contexts_are_supported(self):
        contract,_,before=self.fixture()
        contract.update(primaries={'tdoc:R1-1':'registered'},edges=[
            ('tdoc:R1-1','REPORTED_UNDER_AGENDA','a'),
            ('tdoc:R1-1','REPORTED_UNDER_AGENDA','b')])
        bindings={'tdoc:R1-1':{'element':'doc'},'a':{'element':'a'},'b':{'element':'b'}}
        for target in ('a','b'):
            before['edges'].append({'element':target,'start':'doc','end':target,
                                    'type':'REPORTED_UNDER_AGENDA','properties':{}})
        self.m.check_reported_scope(before,bindings,contract)

    def test_unqualified_reported_edge_added_during_write_fails_readback(self):
        contract,plan,after=self.fixture()
        contract.update(primaries={'tdoc:R1-1':'registered'})
        bindings={'tdoc:R1-1':{'element':'doc'}}
        plan['bindings']=bindings
        after['edges'].append({'element':'foreign-report','start':'doc','end':'foreign',
                                'type':'REPORTED_UNDER_AGENDA','properties':{}})
        with patch.object(self.m,'source_fence'), patch.object(self.m,'prepare',return_value=plan), \
             patch.object(self.m,'endpoint_bindings',return_value=bindings), \
             patch.object(self.m,'full_snapshot',return_value=after):
            with self.assertRaisesRegex(ValueError,'outside the canonical qualified source scope'):
                self.m.apply_transaction(None,contract,plan)


if __name__ == '__main__':
    unittest.main()
