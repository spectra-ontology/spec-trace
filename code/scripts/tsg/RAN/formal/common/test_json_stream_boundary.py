#!/usr/bin/env python3
"""Spec: Phase-8 chunk input; Ontology: top-level chunks array; Cycle: streamed input.
배경: 중복 최상위 키와 잘린 입력을 정상 완료로 취급하는 경계를 검증한다.
사용: python3 -B scripts/tsg/RAN/formal/common/test_json_stream_boundary.py
LLM 호출: 0. 임시 파일만 사용한다.
"""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import json_stream


class StreamBoundaryTests(unittest.TestCase):
    def parse(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "chunks.json"
            path.write_text(text)
            return list(json_stream.iter_array(path, "chunks"))

    def test_duplicate_top_level_keys_are_rejected(self):
        for text in ('{"chunks":[1],"chunks":[2]}', '{"metadata":{},"metadata":{},"chunks":[]}', '{"chunks":[],"chunks":[]}'):
            for size in (1, 3, 64):
                with self.subTest(text=text, size=size), patch.object(json_stream, "_READ", size), self.assertRaises(ValueError):
                    self.parse(text)

    def test_empty_and_missing_are_distinct(self):
        self.assertEqual(self.parse('{"metadata":{},"chunks":[]}'), [])
        with self.assertRaises(KeyError):
            self.parse('{"metadata":{}}')

    def test_truncated_tail_cannot_finish_successfully(self):
        for text in ('{"chunks":[1]', '{"chunks":[1],"metadata":', '{"chunks":[1]} trailing'):
            with self.subTest(text=text), self.assertRaises((ValueError, json.JSONDecodeError)):
                self.parse(text)

    def test_fragmented_valid_values_match_standard_decoder(self):
        text = '{"metadata":{"n":7},"chunks":[{"text":"한글\\n"},1e-5,false,null],"tail":[]}'
        for size in (1, 2, 7, 1024):
            with self.subTest(size=size), patch.object(json_stream, "_READ", size):
                self.assertEqual(self.parse(text), json.loads(text)["chunks"])


if __name__ == "__main__":
    unittest.main()
