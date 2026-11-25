#!/usr/bin/env python3
"""Source ownership and role preservation across generated marker cut points.

Spec: chunking_standards.md P7-V11; ScriptMarkup raw-codepoint slicing contract.
Ontology: a plain digit and a superscript digit retain distinct source roles.
Cycle: source interval → balanced chunk → exact plain-character/role comparison.
배경: 태그 중간 분할, 중첩, 개행, 반복 구간의 문자·역할 손실을 검증한다.
사용: PYTHONPATH=scripts/common python -m unittest common.test_script_markup.
LLM 호출: 없음. No tokenizer, model, filesystem, or database calls.
"""

import unittest
from unittest.mock import patch

from common.script_markup import ScriptMarkup, SourceSpan


def fixture(parts):
    """Write known text/roles, recording ownership during writing, without parsing."""
    text = []
    owned = []
    raw_position = 0
    for literal, roles in parts:
        prefix = "".join(f"<{role}>" for role in roles)
        suffix = "".join(f"</{role}>" for role in reversed(roles))
        text.append(prefix + literal + suffix)
        owned.extend((raw_position + len(prefix) + i, char, roles)
                     for i, char in enumerate(literal))
        raw_position += len(prefix) + len(literal) + len(suffix)
    return "".join(text), owned


def rendered_characters(text):
    """Independent grammar oracle: recursive productions emit (character, stack)."""
    position = 0

    def sequence(roles=()):
        nonlocal position
        out = []
        while position < len(text):
            if text.startswith("</sup>", position) or text.startswith("</sub>", position):
                if not roles or not text.startswith(f"</{roles[-1]}>", position):
                    raise ValueError("Invalid closing marker")
                position += len(f"</{roles[-1]}>")
                return out
            if text.startswith("<sup>", position) or text.startswith("<sub>", position):
                role = "sup" if text.startswith("<sup>", position) else "sub"
                position += len(f"<{role}>")
                out.extend(sequence(roles + (role,)))
            else:
                out.append((text[position], roles))
                position += 1
        if roles:
            raise ValueError("Missing closing marker")
        return out

    return sequence()


class ScriptMarkupTests(unittest.TestCase):
    def assert_owned(self, markup, owned, start, end):
        low, high, _ = slice(start, end).indices(len(markup.text))
        expected = [(char, roles) for position, char, roles in owned if low <= position < high]
        self.assertEqual(rendered_characters(markup.slice(start, end)), expected)

    def test_every_raw_interval_preserves_owned_characters_and_roles(self):
        text, owned = fixture([
            ("α<≤", ()), ("7\nβ", ("sup",)), ("𝛥", ("sub",)), ("z", ()),
        ])
        markup = ScriptMarkup(text)
        for start in range(len(text) + 1):
            for end in range(start, len(text) + 1):
                with self.subTest(start=start, end=end):
                    self.assert_owned(markup, owned, start, end)

    def test_zero_overlap_partition_reassembles_exact_plain_characters_and_roles(self):
        text, owned = fixture([
            ("BW20", ()), ("1", ("sup",)), ("/H", ()), ("2", ("sub",)),
            ("\nline1\nline2", ("sup", "sub")), (" end", ()),
        ])
        markup = ScriptMarkup(text)
        expected = [(char, roles) for _, char, roles in owned]
        for width in range(1, len(text) + 1):
            chunks = [markup.slice(start, start + width) for start in range(0, len(text), width)]
            self.assertEqual([char for chunk in chunks for char in rendered_characters(chunk)], expected)

    def test_overlap_owns_only_each_requested_source_interval(self):
        text, owned = fixture([("pre ", ()), ("abcdef\ngh", ("sup",)), (" tail", ())])
        markup = ScriptMarkup(text)
        for start in range(0, len(text), 3):
            self.assert_owned(markup, owned, start, start + 11)

    def test_nested_mixed_and_repeated_roles_close_and_reopen_at_cut(self):
        text = "A<sup>b<sub>c<sup>d</sup>e</sub>f</sup>G"
        expected = [("A", ()), ("b", ("sup",)), ("c", ("sup", "sub")),
                    ("d", ("sup", "sub", "sup")), ("e", ("sup", "sub")),
                    ("f", ("sup",)), ("G", ())]
        markup = ScriptMarkup(text)
        self.assertEqual(rendered_characters(markup.slice()), expected)
        middle = markup.slice(text.index("c"), text.index("e") + 1)
        self.assertEqual(middle, "<sup><sub>c<sup>d</sup>e</sub></sup>")
        repeated = ScriptMarkup("<sup>a<sup>b</sup>c</sup>")
        self.assertEqual(repeated.slice(11, 12), "<sup><sup>b</sup></sup>")

    def test_source_map_is_immutable_and_maps_only_non_marker_raw_intervals(self):
        text = "A<sup>12</sup><sub>x\ny</sub>Z"
        markup = ScriptMarkup(text)
        self.assertIsInstance(markup.source_map, tuple)
        self.assertEqual(markup.source_map, (
            SourceSpan(0, 1, ()), SourceSpan(6, 8, ("sup",)),
            SourceSpan(19, 22, ("sub",)), SourceSpan(28, 29, ()),
        ))
        with self.assertRaises(AttributeError):
            markup.source_map[0].roles = ("sup",)
        mapped = [(position, text[position], span.roles)
                  for span in markup.source_map for position in range(span.raw_start, span.raw_end)]
        self.assertEqual(mapped, [
            (0, "A", ()), (6, "1", ("sup",)), (7, "2", ("sup",)),
            (19, "x", ("sub",)), (20, "\n", ("sub",)), (21, "y", ("sub",)), (28, "Z", ()),
        ])

    def test_plain_text_native_slice_fast_path_and_literal_comparisons(self):
        text = "x < 7; y <= 2; a > b &amp; <SUP>literal</SUP> <sup x='1'>"
        markup = ScriptMarkup(text)
        self.assertFalse(markup.has_markup)
        for start in (None, -1000, -2, 0, 4, len(text) + 1):
            for end in (None, -1000, -1, 0, 7, len(text) + 1):
                self.assertEqual(markup.slice(start, end), text[start:end])
        self.assertEqual(ScriptMarkup("").slice(), "")

    def test_marker_boundaries_negative_and_out_of_range_match_raw_ownership(self):
        text, owned = fixture([("a", ()), ("23", ("sup",)), ("z", ())])
        markup = ScriptMarkup(text)
        for start in (None, -100, -8, -1, 0, 2, len(text), len(text) + 1):
            for end in (None, -100, -8, -1, 0, 4, len(text), len(text) + 1):
                self.assert_owned(markup, owned, start, end)
        self.assertEqual(markup.slice(2, 5), "")  # Opening marker only.
        self.assertEqual(markup.slice(7, 10), "<sup>3</sup>")  # Closing marker cut.
        self.assertEqual(ScriptMarkup("<sup></sup><sub></sub>").slice(1, 7), "")

    def test_whole_source_retains_exact_marker_bytes_and_reversed_interval_is_empty(self):
        text = "<sup></sup>A<sup>x</sup><sup>y\n<sub>z</sub></sup><sub></sub>"
        markup = ScriptMarkup(text)
        for start, end in ((None, None), (0, len(text)), (-1000, 1000)):
            self.assertEqual(markup.slice(start, end), text)
        self.assertEqual(ScriptMarkup("<sup></sup><sub></sub>").slice(), "<sup></sup><sub></sub>")
        self.assertEqual(markup.slice(20, 4), "")
        self.assertEqual(markup.slice(20, 20), "")

    def test_rejects_unbalanced_crossed_or_extra_generated_markers(self):
        for text in ("<sup>a", "a</sup>", "<sub></sup>",
                     "<sup><sub>x</sup></sub>", "<sup>x</sup></sup>"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                ScriptMarkup(text)
        with self.assertRaises(TypeError):
            ScriptMarkup(None)

    def test_long_single_script_is_parsed_once_and_sliceable_at_every_character(self):
        literal = "aβ\n" * 10_000
        markup = ScriptMarkup("<sub>" + literal + "</sub>")
        with patch("common.script_markup._MARKER") as marker:
            marker.finditer.side_effect = AssertionError("Slices must reuse the source map")
            pieces = [markup.slice(start, start + 137) for start in range(0, len(markup.text), 137)]
        actual = [char for piece in pieces for char in rendered_characters(piece)]
        self.assertEqual(actual, [(char, ("sub",)) for char in literal])

    def test_plain_equality_does_not_hide_script_role_or_number_changes(self):
        expected = rendered_characters(ScriptMarkup("20<sup>1</sup> H<sub>2</sub>").slice())
        for wrong in ("201 H2", "20<sub>1</sub> H<sub>2</sub>", "20<sup>2</sup> H<sub>2</sub>"):
            self.assertNotEqual(rendered_characters(wrong), expected)
        self.assertEqual("".join(char for char, _ in rendered_characters("201 H2")),
                         "".join(char for char, _ in expected))


if __name__ == "__main__":
    unittest.main()
