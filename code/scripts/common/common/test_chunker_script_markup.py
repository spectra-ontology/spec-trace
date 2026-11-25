#!/usr/bin/env python3
"""Verify literal characters and script roles through actual tokenizer cuts.

Spec: Phase-7 hard token budget and generated script presentation.
Ontology: boundary handling preserves source characters and sub/sup roles.
Cycle: balanced source → actual split/truncation → independent role oracle.
배경: 분할 경계에서 태그 일부가 일반 문자로 남는 재발을 검증한다.
사용: PYTHONPATH=scripts/common python3 -B -m unittest common.test_chunker_script_markup.
LLM 호출: 없음. Uses only the pinned local tokenizer, no model or DB.
"""
import unittest
from unittest.mock import patch
import json
from pathlib import Path
import tempfile

from common import chunker
from common.test_script_markup import rendered_characters


def roles(text):
    return rendered_characters(text)


class ChunkerScriptMarkupTests(unittest.TestCase):
    def test_blank_primary_body_uses_the_same_content_for_measurement_and_rewrite(self):
        chunk = {"chunkId": "synthetic", "text": "  ", "content": "oversized content"}
        self.assertEqual(chunker.body_key(chunk), "content")
        self.assertEqual(chunker.chunk_body(chunk, "synthetic"), "oversized content")
        with patch.object(chunker, "count_tokens", side_effect=len):
            self.assertFalse(chunker.validate_chunk_size([chunk], hard_max=5)["pass"])

    def test_malformed_body_cannot_pass_as_an_empty_chunk(self):
        for chunk in ({}, {"text": []}, {"content": 0}, {"text": "valid", "content": {}}):
            with self.subTest(chunk=chunk), self.assertRaises(chunker.ChunkShapeError):
                chunker.validate_chunk_size([chunk])

    def test_producer_and_validator_reject_the_same_malformed_bodies_before_encoding(self):
        for chunk in ({}, {"text": []}, {"content": 0}, {"text": "valid", "content": {}}, None):
            for operation in (lambda row: chunker.enforce_hard_max([row]),
                              chunker.split_existing_chunk,
                              lambda row: chunker.validate_chunk_size([row])):
                with self.subTest(chunk=chunk, operation=operation), patch.object(chunker, "count_tokens") as count:
                    with self.assertRaises(chunker.ChunkShapeError):
                        operation(chunk)
                    count.assert_not_called()

    def test_custom_body_field_and_blank_fallback_keep_the_selected_original_key(self):
        with patch.object(chunker, "count_tokens", side_effect=len):
            original = {"chunkId": "custom", "body": "abcdefghijk", "chunkIndex": 0}
            result = chunker.enforce_hard_max([original], hard_max=5, text_keys=("body",))
            self.assertEqual("".join(row["body"] for row in result), original["body"])
            self.assertTrue(all(row["tokenCount"] <= 5 and "text" not in row for row in result))
            fallback = {"chunkId": "fallback", "text": "  ", "content": "abcdefghijk"}
            result = chunker.split_existing_chunk(fallback, hard_max=5)
            self.assertEqual("".join(row["content"] for row in result), fallback["content"])
            self.assertTrue(all(row["text"] == "  " for row in result))
            with self.assertRaises(chunker.ChunkShapeError):
                chunker.enforce_hard_max([original], text_keys=())

    def test_previously_split_chunks_keep_their_indices_when_no_new_split_occurs(self):
        original = [{"chunkId": "old-child", "chunkIndex": 8, "totalChunks": 12,
                     "text": "small", "_hardMaxEnforced": True},
                    {"chunkId": "sibling", "chunkIndex": 11, "totalChunks": 12, "text": "small"}]
        with patch.object(chunker, "count_tokens", side_effect=len):
            result = chunker.enforce_hard_max(original, hard_max=10)
        self.assertEqual([row["chunkIndex"] for row in result], [8, 11])
        self.assertEqual([row["totalChunks"] for row in result], [12, 12])

    def test_chunk_json_keeps_input_shape_and_rolls_back_invalid_serialization(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "chunks.json"
            original = {"source": "synthetic", "chunks": []}
            chunks = [{"chunkId": "synthetic", "text": "body"}]
            chunker.write_chunk_file(path, original, chunks)
            self.assertEqual(json.loads(path.read_text()), original)
            saved = path.read_bytes()
            with self.assertRaises(ValueError):
                chunker.write_chunk_file(path, original, [{"text": "body", "score": float("nan")}])
            self.assertEqual(path.read_bytes(), saved)
            self.assertEqual(original["chunks"], chunks)
            self.assertEqual(list(path.parent.iterdir()), [path])

    def test_zero_overlap_character_windows_preserve_every_source_role(self):
        text = "A<sup>" + "xβ" * 71 + "</sup>B<sub>" + "2" * 83 + "</sub>C"
        for width in range(1, 12):
            with self.subTest(width=width):
                pieces = chunker.split_huge_paragraph_by_chars(text, target_tokens=width, overlap_tokens=0)
                self.assertEqual([item for piece in pieces for item in roles(piece)], roles(text))

    def test_force_split_measures_added_wrappers_and_preserves_raw_progress(self):
        for text in (
            "head <sup>" + "αβ12 " * 180 + "</sup> tail",
            "<sub>" + "x" * 900 + "<sup>" + "2β" * 400 + "</sup>" + "x" * 50 + "</sub>",
            ("x<sup>12</sup> y<sub>β</sub> < 7 <= 8\n" * 70),
        ):
            pieces = chunker._force_split_by_chars(text, hard_max=80)
            self.assertGreater(len(pieces), 1)
            self.assertTrue(all(chunker.count_tokens(piece) <= 80 for piece in pieces))
            self.assertEqual([item for piece in pieces for item in roles(piece)], roles(text))

    def test_row_split_keeps_script_roles_across_source_newlines(self):
        header = "caption | header"
        body = "<sup>" + "\n".join("row %d | value 12345" % i for i in range(24)) + "</sup>"
        text = header + "\n" + body
        pieces = chunker.split_huge_paragraph_by_rows(text, target_tokens=45)
        self.assertGreater(len(pieces), 1)
        restored = roles(pieces[0])
        prefix = roles(header)
        for piece in pieces[1:]:
            current = roles(piece)
            self.assertEqual(current[:len(prefix)], prefix)
            restored.extend(current[len(prefix):])
        self.assertEqual(restored, roles(text))

    def test_paragraph_overlap_is_a_source_owned_balanced_suffix(self):
        first = "A <sup>" + "12345 " * 100 + "</sup>"
        second = "after boundary " * 100
        pieces = chunker.split_giant_section_v2([first, second], target=400, overlap=20, hard_max=None)
        self.assertEqual(len(pieces), 2)
        self.assertEqual(roles(pieces[0]), roles(first))
        suffix = roles(pieces[1])[:-len(roles("\n" + second))]
        self.assertTrue(suffix)
        self.assertEqual(suffix, roles(first)[-len(suffix):])

    def test_truncation_returns_an_exact_source_prefix_with_original_roles(self):
        text = "begin <sup>" + "αβ12345 " * 400 + "</sup> end"
        original = roles(text)
        for budget in (20, 79, 180):
            with self.subTest(budget=budget):
                shortened = chunker.truncate_to_token_budget(text, budget)
                self.assertTrue(shortened)
                self.assertLessEqual(chunker.count_tokens(shortened), budget)
                self.assertEqual(roles(shortened), original[:len(roles(shortened))])
        self.assertEqual(chunker.truncate_to_token_budget("α<sup>2</sup>", 100), "α<sup>2</sup>")

    def test_plain_text_and_literal_comparison_windows_keep_the_native_contract(self):
        text = "x < 7; y <= 8; z > 9\n" * 50
        pieces = chunker.split_huge_paragraph_by_chars(text, 7, 0)
        self.assertEqual("".join(pieces), text)
        self.assertEqual(pieces, [text[i:i+28] for i in range(0, len(text), 28)])
        pieces = chunker._force_split_by_chars(text, hard_max=80)
        self.assertEqual("".join(pieces), text)
        self.assertTrue(all(chunker.count_tokens(p) <= 80 for p in pieces))

    def test_small_hard_budget_uses_the_bound_when_role_wrappers_exceed_margin(self):
        text = "<sup><sub>" + "x " * 40 + "</sub></sup>"
        pieces = chunker._force_split_by_chars(text, hard_max=15)
        self.assertTrue(all(chunker.count_tokens(p) <= 15 for p in pieces))
        self.assertEqual([item for piece in pieces for item in roles(piece)], roles(text))
        self.assertEqual(chunker.truncate_to_token_budget(text, 0), "")


if __name__ == "__main__":
    unittest.main()
