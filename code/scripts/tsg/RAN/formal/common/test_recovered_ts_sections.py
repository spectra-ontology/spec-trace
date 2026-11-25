"""Source-shaped regressions for RAN5 test headings glued to preceding bullets."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
import copy
import json

from docx import Document
from docx.enum.style import WD_STYLE_TYPE

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
COMMON = ROOT / 'scripts/tsg/RAN/formal/common'
sys.path.insert(0, str(COMMON))
import ts_section_number
from ts_structure_reconcile import _missing_section_verify

_spec = importlib.util.spec_from_file_location(
    'recovered_ts_parser', ROOT / 'scripts/tsg/RAN/formal/RAN5/phase-3/ts-parser/parse_ts_docx.py')
parser = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = parser
_spec.loader.exec_module(parser)


class RecoveredHeadingTests(unittest.TestCase):
    # Wording and tab boundaries observed in the four actual source clauses.
    CASES = [
        ('14.1.1.2.3', '14.1.1.2.3.1', '14.1.1.2.3.2', 'Test procedure sequence',
         '-\tThe UE is in state 1N-A.-\tUE is made not interested in receiving MBS Broadcast services'),
        ('7.2.2.2.5_1', None, '7.2.2.2.5_1.1', 'Test Purpose', '-\tminimum test time'),
        ('6.3G.3.1_1', '6.3G.3.1_1.4', '6.3G.3.1_1.5', 'Test requirement',
         '-\tThe ON power is measured as sum of all tansmit antenna connectors.'),
        ('6.5.7A.1', None, '6.5.7A.1.1', 'Test purpose',
         '-\tTest parameter are still in brackets in 38.133'),
    ]

    def test_actual_heading_shapes_and_body_ownership(self):
        for parent, prior, target, title, lead in self.CASES:
            with self.subTest(target=target), tempfile.TemporaryDirectory() as tmp:
                doc = Document()
                doc.styles.add_style('H6', WD_STYLE_TYPE.PARAGRAPH)
                doc.add_paragraph(parent + '\tParent', 'H6')
                if prior:
                    doc.add_paragraph(prior + '\tPrevious', 'H6')
                doc.add_paragraph(lead + target + '\t' + title, 'H6')
                doc.add_paragraph('The newly recovered clause owns this sentence.')
                path = Path(tmp) / 'source.docx'
                doc.save(path)
                sections, _, _ = parser.parse_part_elements(path, '38.000-Rel-18-', [], {}, set(), set())
                by = {s.section_number: s for s in sections}
                self.assertIn(target, by)
                self.assertEqual(by[target].section_title, title)
                self.assertEqual(by[target]._body_paragraphs, ['The newly recovered clause owns this sentence.'])
                previous = by[prior or parent]
                self.assertEqual(previous._body_paragraphs, [lead.replace('\t', ' ')])
                self.assertNotIn(target, ''.join(previous._body_paragraphs))

    def test_recovery_does_not_invent_out_of_sequence_or_duplicate_clauses(self):
        seq = ts_section_number.HeadingSequence()
        seq.accept('7.2.2.2.5_1')
        self.assertIsNone(seq.recover('-\tminimum time7.2.2.2.5_1.3\tTest Purpose'))
        self.assertIsNone(seq.recover('-\tMIB\tASN.1 definition'))
        seq.accept('7.2.2.2.5_1.1')
        self.assertIsNone(seq.recover('-\tminimum time7.2.2.2.5_1.1\tTest Purpose'))


class SharedPartPolicyTests(unittest.TestCase):
    def test_wg_caption_and_toc_policies_survive_shared_traversal(self):
        """같은 합성 DOCX에서 기존 WG별 캡션·목차 처리 차이를 확인한다."""
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'source.docx'
            doc = Document()
            for name in ('TH', 'TF', 'toc 1'):
                if name not in doc.styles:
                    doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
            doc.add_paragraph('1\tIntroduction', 'Heading 1')
            doc.add_paragraph('Index text inside a clause', 'toc 1')
            for _ in range(2):
                doc.add_paragraph('Table 1: Synthetic table', 'TH')
                doc.add_paragraph('Figure 1: Synthetic figure', 'TF')
            doc.add_paragraph('Unnumbered table caption', 'TH')
            doc.add_paragraph('Unnumbered figure caption', 'TF')
            doc.add_paragraph('The clause body remains attached.')
            doc.save(path)
            for number in range(1, 6):
                wg = f'RAN{number}'
                with self.subTest(wg=wg):
                    source = ROOT / 'scripts/tsg/RAN/formal' / wg / 'phase-3/ts-parser/parse_ts_docx.py'
                    spec = importlib.util.spec_from_file_location('shared_part_' + wg, source)
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[spec.name] = module
                    spec.loader.exec_module(module)
                    warnings = []
                    args = (path, '38.999-Rel-18-', warnings)
                    sections, tables, figures = module.parse_part_elements(
                        *args, **({} if wg == 'RAN1' else dict(
                            section_by_id={}, table_id_set=set(), figure_id_set=set())))
                    self.assertEqual(len(sections), 1)
                    self.assertIsInstance(sections[0], module.SectionData)
                    self.assertEqual([t.table_id for t in tables], [
                        '38.999-Rel-18-T1',
                        '38.999-Rel-18-T1' if wg == 'RAN1' else '38.999-Rel-18-T1_2'])
                    self.assertEqual([f.figure_id for f in figures], [
                        '38.999-Rel-18-F1',
                        '38.999-Rel-18-F1' if wg == 'RAN1' else '38.999-Rel-18-F1_2'])
                    self.assertEqual(sum('Unmatched ' in w for w in warnings), 2 if wg == 'RAN1' else 0)
                    self.assertEqual(sum('Duplicate ' in w for w in warnings), 0 if wg == 'RAN1' else 2)
                    self.assertEqual(all(t.enclosing_section_id == sections[0].section_id for t in tables), True)
                    expected = ['The clause body remains attached.']
                    if wg != 'RAN5':
                        expected.insert(0, 'Index text inside a clause')
                    self.assertEqual(sections[0]._body_paragraphs, expected)


class RepairBoundaryTests(unittest.TestCase):
    def fixture(self):
        def key(*args): return json.dumps(args)
        def node(eid, props, labels): return [{'eid': eid, 'properties': props, 'labels': labels}]
        sec = dict(sectionId='38.000-Rel-18-1.2', sectionNumber='1.2', sectionTitle='Test purpose',
                   level=2, isVoid=False, parentSectionId='38.000-Rel-18-1', childSectionIds=[],
                   references=['38.001-Rel-18-4.5'], referencesSpec=['38.001'])
        repair = {'section': sec, 'previousSectionId': '38.000-Rel-18-1.1',
                  'specNumber': '38.000', 'release': 'Rel-18', 'tableMoves': [{'tableId': 'table'}]}
        nodes = {key('Section', 'sectionId', sec['sectionId']): [],
                 key('Section', 'sectionId', sec['parentSectionId']): node('parent', {'level': 1}, ['Section']),
                 key('Section', 'sectionId', repair['previousSectionId']): node('previous', {}, ['Section']),
                 key('Spec', 'specNumber', '38.000', 'Rel-18'): node('spec', {}, ['Spec']),
                 key('TSTable', 'tableId', 'table'): node('table', {}, ['TSTable']),
                 key('Section', 'sectionId', '38.001-Rel-18-4.5'): node('referred', {}, ['Section']),
                 key('Spec', 'specNumber', '38.001', None): node('hub', {}, ['Spec'])}
        def edge(eid, start, kind, end): return {'eid': eid, 'start': start, 'type': kind, 'end': end, 'properties': {}}
        before = {'nodes': nodes, 'edges': [edge('old1', 'previous', 'CONTAINS_TABLE', 'table'),
                    edge('old2', 'table', 'TABLE_IN_SECTION', 'previous'),
                    edge('old3', 'previous', 'REFERENCES_SECTION', 'referred'),
                    edge('old4', 'referred', 'REFERENCED_BY_SECTION', 'previous'),
                    edge('foreign', 'parent', 'FOREIGN_PRODUCER', 'other')]}
        after = copy.deepcopy(before)
        props = {k: sec[k] for k in ('sectionId', 'sectionNumber', 'sectionTitle', 'level', 'isVoid')}
        props.update(specNumber='38.000', granularity='section')
        after['nodes'][key('Section', 'sectionId', sec['sectionId'])] = node('fresh', props, ['ConformanceTest', 'Section'])
        pairs = [('fresh', 'BELONGS_TO_SPEC', 'spec'), ('fresh', 'PARENT_SECTION', 'parent'),
                 ('parent', 'HAS_SUB_SECTION', 'fresh'), ('fresh', 'CONTAINS_TABLE', 'table'),
                 ('table', 'TABLE_IN_SECTION', 'fresh'), ('fresh', 'REFERENCES_SECTION', 'referred'),
                 ('referred', 'REFERENCED_BY_SECTION', 'fresh'), ('fresh', 'REFERENCES_SPEC', 'hub')]
        after['edges'] = [before['edges'][-1]] + [edge('new'+str(i), *parts) for i, parts in enumerate(pairs)]
        return before, after, [repair]

    def test_exact_source_owned_delta_passes(self):
        _missing_section_verify(*self.fixture())

    def test_existing_node_property_change_is_rejected(self):
        before, after, repairs = self.fixture()
        after['nodes'][json.dumps(('Section', 'sectionId', repairs[0]['section']['parentSectionId']))][0]['properties']['level'] = 9
        with self.assertRaisesRegex(ValueError, 'existing node changed'):
            _missing_section_verify(before, after, repairs)

    def test_unrelated_edge_loss_is_rejected(self):
        before, after, repairs = self.fixture()
        after['edges'] = after['edges'][1:]
        with self.assertRaisesRegex(ValueError, 'graph delta exceeds'):
            _missing_section_verify(before, after, repairs)

    def test_excess_new_edge_is_rejected(self):
        before, after, repairs = self.fixture()
        after['edges'].append(dict(eid='extra', start='fresh', type='IMPACTS_SPEC', end='spec', properties={}))
        with self.assertRaisesRegex(ValueError, 'graph delta exceeds'):
            _missing_section_verify(before, after, repairs)


if __name__ == '__main__':
    unittest.main()
