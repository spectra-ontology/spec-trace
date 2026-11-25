#!/usr/bin/env python3
"""test_ts_source_context_split.py — source-context split acceptance and rejection.

Spec: reembedding_policy.md §3.1.1 and exact source-coordinate correspondence.
Ontology: context never turns an empty source cell into an inferred row value.
Cycle: overlap/partial-row examples → explicit context checks → fail-closed bounds.
배경: 기존 plain split의 토큰 통과와 문맥 보존은 서로 다른 검증이다.
사용: python3 -B scripts/tsg/RAN/formal/common/test_ts_source_context_split.py.
LLM 호출: 없음.
"""
import unittest
from lxml import etree

from ts_search_presentation import TAG, source_info
from ts_source_context_split import (SourceContextError, bind_source, context_for,
                                     normalized, split_bound_source, explicit_note_references)
from prepare_ts_source_context_split import (_note_match, shared_note_scope,
    qualify_note_dependencies, apply_reviewed_table_fields)
import docx_text as d


class QualifiedSourceSplit(unittest.TestCase):
    def test_reviewed_source_header_includes_units_and_rejects_other_docx_xpath_alias(self):
        table = self.table(['Power | Channels', 'Power | Low MHz | High MHz', '23 | 100 | 200'])
        plan = dict(sourcePath='actual.docx', tableXPath='/table[1]', captionQuote='Table 1: source',
                    firstRenderedRows=table['flatRows'], renderedHeaderRows=[0, 1], rationale='Actual units')
        apply_reviewed_table_fields(table, plan)
        section = 'Table 1: source\n' + '\n'.join(table['flatRows'])
        bound = self.bind('23 | 100 | 200', section, [table])
        units, _, _ = context_for(bound, [(0, 14)])
        self.assertTrue(any(u['kind'] == 'reviewed_column_header_row' and 'Low MHz' in u['text'] for u in units))
        wrong_file = dict(table, path='other_part.docx')
        with self.assertRaisesRegex(SourceContextError, 'fields changed'):
            apply_reviewed_table_fields(wrong_file, plan)

    def test_only_reviewed_numeric_source_field_adds_its_actual_note(self):
        note = dict(number=1, quote='NOTE 1: Applies at 200 MHz.', paragraphXPath='/note')
        table = self.table(['Power | Formula', '23 | x2'])
        table.update(sourceGridRows={'0': [], '1': [dict(column=0, presentation='23<sup>1</sup>'),
                                                  dict(column=1, presentation='x<sup>2</sup>')]},
                     sourceNumberedNotes={'1': [note]})
        plan = dict(sourcePath='actual.docx', tableXPath='/table[1]', captionQuote='Table 1: source',
                    firstRenderedRows=table['flatRows'], footnoteColumns=[0],
                    examples=[dict(renderedRow=1, column=0, presentation='23<sup>1</sup>')],
                    numberedNoteDefinitions={'1':[note]}, rationale='Reviewed power field')
        apply_reviewed_table_fields(table, plan)
        self.assertEqual(table['reviewedRowFootnoteReferences']['1']['numbers'], [1])

    def table(self, rows, **extra):
        return dict(ownerSectionId='38.1-1', path='actual.docx', tableXPath='/table[1]',
                    flatRows=rows, explicitHeaders=[dict(renderedLine=0)],
                    actualAdjacentCaption=dict(quote='Table 1: source', paragraphXPath='/caption'),
                    sourceNumberedNotes={}, sourceRowNoteReferences={}, **extra)

    def bind(self, parent, section, tables, spans=None):
        plain, _, _ = source_info(parent)
        sn = source_info(section)[1]
        if spans is None:
            spans = [dict(payloadStart=0, payloadEnd=len(plain),
                          startInNormalizedSource=sn.index(normalized(plain)))]
        return bind_source(parent, section, spans, tables,
                           edition=('RAN4', '38.1', 'Rel-19'), section_id='38.1-1')

    def test_partial_row_and_repeated_overlap_keep_distinct_payload_coordinates(self):
        section = 'Table 1: source\nA | B\nleft | x<sub>2</sub> tail\nnext | 3'
        parent = 'x<sub>2</sub>\nx<sub>2</sub> tail'
        start = source_info(section)[1].index('x2 tail')
        spans = [dict(payloadStart=0, payloadEnd=3, startInNormalizedSource=start),
                 dict(payloadStart=3, payloadEnd=10, startInNormalizedSource=start)]
        bound = self.bind(parent, section, [self.table(['A | B', 'left | x2 tail', 'next | 3'])], spans)
        images = split_bound_source(bound, len, target=4, hard_max=2000)
        self.assertEqual(''.join(TAG.sub('', c['coreText']) for c in images), 'x2\nx2 tail')
        self.assertTrue(all(c['sourceRows'][0]['renderedRows'] == [1] for c in images))
        self.assertTrue(all('A | B' in c['text'] for c in images))
        self.assertTrue(all(c['tokens'] <= 2000 for c in images))

    def test_explicit_local_note_is_added_to_the_referencing_row(self):
        note = 'NOTE 27: Applicable only when bandwidth is 20 MHz.'
        section = 'Table 1: source\nBand | NOTE\nn84 | 27\n' + note
        table = self.table(['Band | NOTE', 'n84 | 27', note])
        table['sourceRowNoteReferences'] = {'1': dict(numbers=[27])}
        table['sourceNumberedNotes'] = {'27': [dict(quote=note, paragraphXPath='/note27')]}
        bound = self.bind('n84 | 27', section, [table])
        context, _, _ = context_for(bound, [(0, 8)])
        self.assertEqual([u['text'] for u in context if u['kind'] == 'direct_numbered_note'], [note])

    def test_superscript_number_does_not_establish_a_note_reference(self):
        note = 'NOTE 2: Source condition.'
        section = 'Table 1: source\nA | B\nx<sup>2</sup> | 3\n' + note
        table = self.table(['A | B', 'x2 | 3', note])
        table['sourceNumberedNotes'] = {'2': [dict(quote=note, paragraphXPath='/note2')]}
        bound = self.bind('x<sup>2</sup> | 3', section, [table])
        context, _, _ = context_for(bound, [(0, 6)])
        self.assertFalse(any(u['kind'] == 'direct_numbered_note' for u in context))

    def test_undefined_source_note_is_flagged_without_borrowing_another_table_note(self):
        section = 'Table 1: source\nBand | NOTE\nn84 | 27'
        table = self.table(['Band | NOTE', 'n84 | 27'])
        table['sourceRowNoteReferences'] = {'1': dict(numbers=[27])}
        bound = self.bind('n84 | 27', section, [table])
        images = split_bound_source(bound, len)
        unresolved = [u for c in images for u in c['context']
                      if u['kind'] == 'unresolved_source_note_reference']
        self.assertEqual(len(unresolved), 1)
        self.assertEqual(unresolved[0]['number'], 27)
        self.assertFalse(any(u['kind'] == 'direct_numbered_note' for c in images for u in c['context']))

    def test_explicit_above_tables_scope_is_preserved_with_its_literal_declaration(self):
        note = 'NOTE 3: Refer to the applicable SCS in Table 5.3.5-1.'
        section = 'Table 1: source\nA | B (NOTE 3)\nx | 2'
        table = self.table(['A | B (NOTE 3)', 'x | 2'])
        scope = dict(quote='The following notes are applied to the above tables.',
                     paragraphXPath='/scope', tableXPaths=['/table[1]'])
        table['explicitSharedNumberedNotes'] = {'3': [dict(quote=note,
            paragraphXPath='/note3', explicitScope=scope)]}
        bound = self.bind('x | 2', section, [table])
        units = split_bound_source(bound, len)[0]['context']
        added = next(u for u in units if u['kind'] == 'direct_numbered_note')
        self.assertEqual(added['text'], note)
        self.assertEqual(added['explicitScopes'], [scope])

    def test_conflicting_actual_note_definitions_block(self):
        section = 'Table 1: source\nBand | NOTE\nn84 | 27'
        table = self.table(['Band | NOTE', 'n84 | 27'])
        table['sourceRowNoteReferences'] = {'1': dict(numbers=[27])}
        table['sourceNumberedNotes'] = {'27': [dict(quote=x, paragraphXPath='/note')
            for x in ('NOTE 27: only 20 MHz', 'NOTE 27: only 40 MHz')]}
        with self.assertRaisesRegex(SourceContextError, 'no unique table-local'):
            split_bound_source(self.bind('n84 | 27', section, [table]), len)

    def test_blank_source_cell_is_reported_and_only_explicit_merge_adds_anchor(self):
        section = 'Table 1: source\nA | B\nn48 | 2'
        table = self.table(['A | B', 'n48 | 2'], sourceEmptyCellColumns={'1': [0]},
                           sourceGridRows={'1': [dict(column=0, span=1, presentation=''),
                                                dict(column=1, span=1, presentation='n48'),
                                                dict(column=2, span=1, presentation='2')]})
        bound = self.bind('n48 | 2', section, [table])
        context, _, _ = context_for(bound, [(0, 7)])
        self.assertFalse(any(u['kind'] == 'explicit_vertical_merge_anchor' for u in context))
        self.assertIn('column 1: [empty source cell]', next(u['text'] for u in context if u['kind'] == 'source_row_column_positions'))

    def test_all_context_counts_toward_the_bound(self):
        section = 'Long applicable condition preceding the table.\nTable 1: source\nA | B\nx | 2'
        bound = self.bind('x | 2', section, [self.table(['A | B', 'x | 2'])])
        with self.assertRaisesRegex(SourceContextError, 'qualified context exceed'):
            split_bound_source(bound, len, hard_max=20)

    def test_multiple_source_occurrences_cannot_be_silently_chosen(self):
        with self.assertRaisesRegex(SourceContextError, 'not unique'):
            self.bind('x | 2', 'x | 2\nx | 2', [])

    def test_intertable_whitespace_does_not_shift_a_quotation_role(self):
        section = ('Table 1: source\nA | B\nx | 1\n  A condition with P<sub>max</sub>.\n'
                   'Table 2: source\nC | D\ny | 2')
        first = self.table(['A | B', 'x | 1'])
        second = self.table(['C | D', 'y | 2'])
        second['tableXPath'] = '/table[2]'
        second['actualAdjacentCaption']['quote'] = 'Table 2: source'
        images = split_bound_source(self.bind('y | 2', section, [first, second]), len)
        self.assertIn('A condition with P<sub>max</sub>.', images[0]['text'])

    def test_final_parent_caption_roles_survive_a_plain_stage_caption(self):
        parent = 'Table 1: P<sub>max</sub>\nA | B\nx | 1'
        section = 'Table 1: Pmax\nA | B\nx | 1'
        image = split_bound_source(self.bind(parent, section, [self.table(['A | B', 'x | 1'])]), len)[0]
        self.assertEqual(image['coreText'], parent)

    def test_numbered_note_tab_is_a_definition_but_bare_formula_reference_is_not(self):
        self.assertEqual(_note_match('NOTE 4\tOne muted symbol is configured.')[1], '4')
        self.assertEqual(_note_match('NOTE 2:\tSource definition.')[1], '2')
        self.assertIsNone(_note_match('M2 Note 2 x DRX cycle'))
        self.assertIsNone(_note_match('Note 2 is referenced below'))

    def test_explicit_note_lists_retain_each_reference_and_exclude_definitions(self):
        self.assertEqual(explicit_note_references('Condition NOTE1,2 | T_SSB'), {1, 2})
        self.assertEqual(explicit_note_references('NOTE 3:\tA definition. NOTE 4\tAnother.'), set())
        self.assertEqual(explicit_note_references('See Notes 2 and 4.'), {2, 4})

    def test_shared_note_requires_its_literal_source_scope_declaration(self):
        w = '{' + d.W_NS + '}'
        root = etree.Element(w + 'document', nsmap={'w': d.W_NS})
        body = etree.SubElement(root, w + 'body')
        table = etree.SubElement(body, w + 'tbl')
        def paragraph(text):
            p = etree.SubElement(body, w + 'p')
            etree.SubElement(etree.SubElement(p, w + 'r'), w + 't').text = text
            return p
        declaration = paragraph('The following notes are applied to the above tables.')
        paragraph('NOTE 3:\tApplicable SCS is given in Table 5.3.5-1.')
        tree = root.getroottree()
        class Styles:
            read = staticmethod(d.chunk_text)
        records = [dict(tableXPath=tree.getpath(table), ownerSectionId='38.1-1')]
        notes = shared_note_scope(tree, records, Styles())
        self.assertEqual(notes['3'][0]['explicitScope']['tableXPaths'], [tree.getpath(table)])
        declaration[0][0].text = 'The following notes are applied to the above tables:'
        paragraph('NOTE 14 Minimum requirements apply only to this configuration.')
        self.assertIn('14', shared_note_scope(tree, records, Styles()))
        declaration[0][0].text = 'Unrelated source prose.'
        self.assertEqual(shared_note_scope(tree, records, Styles()), {})

    def test_source_declared_ca_field_footnotes_and_symbol_dependencies(self):
        table = self.table(['NR CA configuration | Channel bandwidth', 'n48 | 50, 10012'],
            sourceGridRows={'1': [dict(column=1, span=1, presentation='50, 100<sup>12</sup>')]})
        table['actualAdjacentCaption']['quote'] = 'NR CA configurations and bandwidth combinations sets'
        table['explicitSharedNumberedNotes'] = {'12': [dict(quote='NOTE 12: Only DL SCell.',
            paragraphXPath='/note12', explicitScope=dict(quote='The following notes apply to the above tables:',
            paragraphXPath='/scope', tableXPaths=['/table[1]']))]}
        qualify_note_dependencies(table)
        section = 'NR CA configurations and bandwidth combinations sets\n' + '\n'.join(table['flatRows'])
        child = split_bound_source(self.bind('n48 | 50, 100<sup>12</sup>', section, [table]), len)[0]
        self.assertTrue(any(u.get('number') == 12 for u in child['context']))
        table = self.table(['F bounds | NOTE', 'FDL_low | 27'])
        table['sourceRowNoteReferences'] = {'1': dict(numbers=[27])}
        table['actualAdjacentCaption']['quote'] = 'Requirements for spurious emissions for UE co-existence'
        table['sourceNumberedNotes'] = {str(n): [dict(quote=q, paragraphXPath='/note' + str(n))] for n, q in (
            (1, 'NOTE 1: FDL_low and FDL_high refer to each frequency band.'),
            (3, 'NOTE 3: 15 kHz SCS is assumed when RB is mentioned in the note.'),
            (27, 'NOTE 27: Applicable for an allocation of 10 RB.'))}
        qualify_note_dependencies(table)
        section = table['actualAdjacentCaption']['quote'] + '\n' + '\n'.join(table['flatRows'])
        child = split_bound_source(self.bind('FDL_low | 27', section, [table]), len)[0]
        self.assertEqual({u['number'] for u in child['context'] if u['kind'] == 'direct_numbered_note'}, {1, 3, 27})


if __name__ == '__main__':
    unittest.main()
