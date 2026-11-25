#!/usr/bin/env python3
"""test_ts_search_presentation.py — source-bound TS search presentation.

Spec: reembedding_policy.md; exact source/body and physical table correspondence.
Ontology: source typography is kept separately from normative interpretation.
Cycle: actual matching contract → ambiguity rejection → exact plain projection.
배경: 반복 표 머리글과 기존 청크 경계가 첨자 역할을 잘못 전파하지 않게 한다.
사용: python3 -B scripts/tsg/RAN/formal/common/test_ts_search_presentation.py
LLM 호출: 없음.
"""
import unittest

from ts_search_presentation import TAG, ScriptRanges, normalize, project, project_lines, source_info


class SourceBoundPresentation(unittest.TestCase):
    def exact(self, payload, source):
        _, norm, roles = source_info(source)
        pnorm, mapping = normalize(payload)
        return project(payload, pnorm, mapping, norm, roles)

    def test_band_and_unit_note_remain_distinct_with_original_payload_whitespace(self):
        actual, status = self.exact('n5121 | 127504,5 MHz', 'n512<sup>1</sup> | 12750<sup>4,5</sup> MHz')
        self.assertEqual(status, 'matched')
        self.assertEqual(actual['text'], 'n512<sup>1</sup> | 12750<sup>4,5</sup> MHz')
        self.assertEqual(TAG.sub('', actual['text']), 'n5121 | 127504,5 MHz')

    def test_whitespace_normalization_does_not_replace_payload_characters(self):
        actual, status = self.exact('N\tRB\nend', 'N <sub>RB</sub> end')
        self.assertEqual(status, 'matched')
        self.assertEqual(actual['text'], 'N\t<sub>RB</sub>\nend')

    def test_chunk_may_start_inside_a_script_but_its_marker_is_closed(self):
        actual, status = self.exact('345 tail', 'x<sup>12345</sup> tail')
        self.assertEqual(status, 'matched')
        self.assertEqual(actual['text'], '<sup>345</sup> tail')

    def test_repeated_equal_presentation_is_supported(self):
        actual, status = self.exact('x1', 'x<sub>1</sub> and x<sub>1</sub>')
        self.assertEqual(status, 'matched')
        self.assertEqual(actual['samePresentationOccurrences'], 2)

    def test_repeated_conflicting_presentation_is_rejected(self):
        actual, status = self.exact('x1', 'x<sub>1</sub> and x<sup>1</sup>')
        self.assertIsNone(actual)
        self.assertEqual(status, 'repeated_span_style_ambiguous')

    def test_missing_or_invalid_source_is_not_guessed(self):
        self.assertEqual(self.exact('absent', 'present')[1], 'no_body_match')
        with self.assertRaisesRegex(ValueError, 'unbalanced'):
            source_info('x</sub>')
        with self.assertRaisesRegex(ValueError, 'overlap'):
            source_info('<sup>x<sub>1</sub></sup>')

    def table_context(self, source, table_body, header, locator):
        _, norm, _ = source_info(source)
        _, table_norm, _ = source_info(table_body)
        _, header_norm, header_roles = source_info(header)
        start = norm.index(table_norm)
        return dict(headerPlain=header_norm, headerRoles=header_roles, start=start,
                    end=start+len(table_norm), path='actual.docx', sha256='source-sha', locator=locator)

    def test_repeated_header_is_bound_to_actual_table_by_unique_following_source_line(self):
        # The maximal following run includes text after the table. Its first line
        # is wholly within the actual table and establishes which header applies.
        source = 'N<sub>RB</sub> | value\ninitial | 1\nalpha | 5\nafter A\nNRB | value\nbeta | 8\nafter B'
        table = self.table_context(source, 'N<sub>RB</sub> | value\ninitial | 1\nalpha | 5', 'N<sub>RB</sub> | value', 'table 0')
        _, norm, roles = source_info(source)
        actual, status = project_lines('NRB | value\nalpha | 5\nafter A', norm, roles, [table])
        self.assertEqual(status, 'matched')
        self.assertEqual(actual['text'], 'N<sub>RB</sub> | value\nalpha | 5\nafter A')
        self.assertEqual(actual['sourceLineSpans'][0]['headerSourceBinding']['locator'], 'table 0')

    def test_header_from_another_table_or_conflicting_candidates_cannot_be_used(self):
        source = 'N<sub>RB</sub> | value\ninitial | 1\nalpha | 5\nafter A\nNRB | value\nbeta | 8\nafter B'
        wrong = self.table_context(source, 'NRB | value\nbeta | 8', 'NRB | value', 'table 1')
        _, norm, roles = source_info(source)
        actual, status = project_lines('NRB | value\nalpha | 5\nafter A', norm, roles, [wrong])
        self.assertIsNone(actual)
        right = self.table_context(source, 'N<sub>RB</sub> | value\ninitial | 1\nalpha | 5', 'N<sub>RB</sub> | value', 'table 0')
        conflicting = dict(right, headerRoles=ScriptRanges([]), locator='invalid competing table')
        actual, status = project_lines('NRB | value\nalpha | 5\nafter A', norm, roles, [right, conflicting])
        self.assertIsNone(actual)
        self.assertEqual(status, 'actual_table_header_presentation_ambiguous')


if __name__ == '__main__':
    unittest.main()
