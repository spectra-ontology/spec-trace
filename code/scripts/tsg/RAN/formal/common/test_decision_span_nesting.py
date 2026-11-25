"""Synthetic boundaries for nested decisions; grammar helpers are isolated."""

import re
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import decision_marks


class NestedDecisionBoundaries(unittest.TestCase):
    def test_nested_quotes_preserve_boundaries_and_all_source_spans(self):
        # Each row is (paragraph, exclusive end, quote form, inline text).
        cases = (
            ("empty", [], []),
            ("disjoint", [(0, 2, None, None), (2, 4, None, None)], [0, 2]),
            ("nested quote", [(0, 4, None, None), (2, 5, "quote", None)], [0]),
            ("prior quote", [(0, 5, "quote", None), (2, 6, None, None)], [0]),
            ("empty inline", [(0, 5, "quote", ""), (2, 6, None, None)], [0, 2]),
            ("exclusive end", [(0, 2, None, None), (2, 4, "quote", None)], [0, 2]),
            ("suppressed prior still covers", [(0, 3, None, None),
                                               (1, 6, "quote", None),
                                               (4, 6, None, None)], [0]),
            ("restated", [(0, 2, None, None), (2, 4, "restated", None)], [0, 2]),
        )
        for label, rows, expected in cases:
            with self.subTest(label=label):
                texts = [f"body{i}" for i in range(8)]
                marks, forms, ends = {}, {}, {}
                for i, end, form, inline in rows:
                    texts[i] = f"mark{i}"
                    mark = SimpleNamespace(lead=None, inline=inline, kind="agreement")
                    marks[texts[i]] = mark
                    forms[texts[i]] = form
                    ends[id(mark)] = end
                spans, restated = [], {}
                # All quote bodies have a clarifying line. Only nesting decides
                # whether these marks reach the public iterator's result.
                with patch.multiple(
                    decision_marks,
                    template_head=lambda text: None,
                    ENTRY_LINE=re.compile(r"(?!)"),
                    classify=lambda text, kinds: marks.get(text),
                    quote_form=lambda text, own: forms.get(text),
                    lead_form=lambda *args: None,
                    content_end=lambda rows, mark, *args: ends[id(mark)],
                    _introduced=lambda *args: (set(), {}),
                    CLARIFY_LINE=re.compile(r".*"),
                    reprinted=lambda *args: False,
                    unseen_lines=lambda lines, earlier: [x for x in lines if x not in earlier],
                ):
                    result = list(decision_marks.decision_spans(
                        texts, [False] * 8, [False] * 8, [],
                        spans=spans, restated=restated))
                self.assertEqual([i for i, mark, end in result], expected)
                self.assertEqual(spans, [(i, end) for i, end, form, inline in rows])
                self.assertTrue(all(mark is marks[texts[i]] and end == ends[id(mark)]
                                    for i, mark, end in result))
                self.assertEqual(restated, {2: ["body3"]} if label == "restated" else {})


if __name__ == "__main__":
    unittest.main()
