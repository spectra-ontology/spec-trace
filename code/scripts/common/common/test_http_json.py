#!/usr/bin/env python3
"""Offline transport contracts, payload-query imports and partition scope.

All HTTP responses are synthetic. No encoder, credential or corpus is loaded.
Run directly with python3; the suite uses only the standard library.
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.http_json import post_json  # noqa: E402


class JsonPostTests(unittest.TestCase):
    def setUp(self):
        self.response = mock.MagicMock()
        self.response.__enter__.return_value.read.return_value = b'{"result": {"points": []}}'
        self.patch = mock.patch("urllib.request.urlopen", return_value=self.response)
        self.network = self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_request_envelope_and_default_timeout(self):
        body = {"query": [0.1], "filter": {"value": "합성"}}
        result = post_json("https://synthetic.invalid/points/query", body)
        self.assertEqual(result, {"result": {"points": []}})
        self.network.assert_called_once()
        request = self.network.call_args.args[0]
        self.assertEqual(request.full_url, "https://synthetic.invalid/points/query")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Content-type"), "application/json")
        self.assertEqual(request.data, json.dumps(body).encode())
        self.assertEqual(self.network.call_args.kwargs, {"timeout": 30.0})
        self.response.__exit__.assert_called_once_with(None, None, None)

    def test_explicit_timeout_is_forwarded(self):
        post_json("https://synthetic.invalid", {}, timeout=60)
        self.assertEqual(self.network.call_args.kwargs, {"timeout": 60})

    def test_unicode_response_is_decoded(self):
        self.response.__enter__.return_value.read.return_value = '{"text": "합성"}'.encode()
        self.assertEqual(post_json("https://synthetic.invalid", {}), {"text": "합성"})

    def test_serialization_failure_never_opens_url(self):
        with self.assertRaises(TypeError):
            post_json("https://synthetic.invalid", {"bad": object()})
        self.network.assert_not_called()

    def test_nonfinite_numbers_are_rejected_before_request(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                post_json("https://synthetic.invalid", {"vector": [value]})
        self.network.assert_not_called()

    def test_network_exception_is_preserved(self):
        error = TimeoutError("synthetic unavailable")
        self.network.side_effect = error
        with self.assertRaises(TimeoutError) as caught:
            post_json("https://synthetic.invalid", {})
        self.assertIs(caught.exception, error)

    def test_invalid_json_propagates_and_closes_response(self):
        self.response.__enter__.return_value.read.return_value = b"invalid synthetic JSON"
        with self.assertRaises(json.JSONDecodeError):
            post_json("https://synthetic.invalid", {})
        self.response.__exit__.assert_called_once()
        self.assertIs(self.response.__exit__.call_args.args[0], json.JSONDecodeError)

    def test_read_failure_propagates_and_closes_response(self):
        error = OSError("synthetic read failure")
        self.response.__enter__.return_value.read.side_effect = error
        with self.assertRaises(OSError) as caught:
            post_json("https://synthetic.invalid", {})
        self.assertIs(caught.exception, error)
        self.response.__exit__.assert_called_once()


class FetchImportTests(unittest.TestCase):
    def test_payload_fetch_import_does_not_require_encoder_or_credentials(self):
        root = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
        path = root / "scripts/capability/answer/answer_pipeline/board_fetch_chunks.py"
        spec = importlib.util.spec_from_file_location("spectra_fetch_offline_test", path)
        module = importlib.util.module_from_spec(spec)
        old_path, old_environment = list(sys.path), dict(os.environ)
        blocked = {name: None for name in ["board_semantic_probe",
                   "common.embedding_registry", "common.credentials"]}
        try:
            with mock.patch.dict(sys.modules, blocked), mock.patch(
                    "urllib.request.urlopen", side_effect=AssertionError("offline test")) as network:
                spec.loader.exec_module(module)
            network.assert_not_called()
            self.assertEqual(dict(os.environ), old_environment)
            self.assertTrue(callable(module.fetch_one))
            self.assertTrue(callable(module.qpost))
        finally:
            sys.path[:] = old_path


class PartitionProbeTests(unittest.TestCase):
    def setUp(self):
        root = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
        path = root / "scripts/capability/answer/answer_pipeline/probe_entity_partitions.py"
        spec = importlib.util.spec_from_file_location("spectra_partition_offline_test", path)
        self.module = importlib.util.module_from_spec(spec)
        old_path, old_environment = list(sys.path), dict(os.environ)
        self.addCleanup(lambda: sys.path.__setitem__(slice(None), old_path))
        blocked = {name: None for name in ["board_semantic_probe",
                   "common.embedding_registry", "common.credentials"]}
        with mock.patch.dict(sys.modules, blocked), mock.patch(
                "urllib.request.urlopen", side_effect=AssertionError("offline test")) as network:
            spec.loader.exec_module(self.module)
        network.assert_not_called()
        self.assertEqual(dict(os.environ), old_environment)
        self.network_patch = mock.patch(
            "urllib.request.urlopen", side_effect=AssertionError("offline test"))
        self.network_patch.start()
        self.addCleanup(self.network_patch.stop)

    def test_partition_transport_preserves_endpoint_and_timeouts(self):
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = b'{"result": {"points": []}}'
        body = {"filter": {"value": "합성"}}
        with mock.patch.object(self.module, "QDRANT", "https://synthetic.invalid"), \
                mock.patch("urllib.request.urlopen", return_value=response) as network:
            for timeout in (None, 2.5):
                with self.subTest(timeout=timeout):
                    kwargs = {} if timeout is None else {"timeout": timeout}
                    self.assertEqual(self.module._post("/synthetic", body, **kwargs),
                                     {"result": {"points": []}})
                    request = network.call_args.args[0]
                    self.assertEqual(request.full_url, "https://synthetic.invalid/synthetic")
                    self.assertEqual(request.get_method(), "POST")
                    self.assertEqual(request.data, json.dumps(body).encode())
                    self.assertEqual(network.call_args.kwargs,
                                     {"timeout": 15.0 if timeout is None else timeout})

    def test_absence_message_identifies_wg_and_query_fields(self):
        output = io.StringIO()
        listing = {"result": {"collections": [{"name": "ran5_synthetic"},
                   {"name": "ran4_synthetic"}, {"name": "unrelated_synthetic"}]}}
        with mock.patch.object(self.module, "_get", return_value=listing), \
                mock.patch.object(self.module, "_post",
                                  return_value={"result": {"points": []}}) as post, \
                mock.patch.object(sys, "argv", ["probe", "--id", "R5-synthetic"]), \
                redirect_stdout(output):
            self.assertEqual(self.module.main(), 0)
        self.assertEqual(post.call_count, 4)
        self.assertTrue(all(c.args[0] == "/collections/ran5_synthetic/points/scroll"
                            for c in post.call_args_list))
        keys = [c.args[1]["filter"]["must"][0]["key"] for c in post.call_args_list]
        self.assertEqual(keys, ["tdocNumber", "crNumber", "specNumber", "sectionId"])
        self.assertIn("조회 범위: ran5_*", output.getvalue())
        self.assertIn("payload keys=" + ", ".join(keys), output.getvalue())
        self.assertNotIn("전수 확인됨", output.getvalue())

    def test_incomplete_lookup_remains_inconclusive_and_later_hit_is_present(self):
        empty = {"result": {"points": []}}
        hit = {"result": {"points": [{"payload": {"text": "synthetic"}}]}}
        cases = [("no_collections", [], [], "INCONCLUSIVE"),
                 ("failed_lookup", ["ran5_synthetic"], [TimeoutError("synthetic"),
                  empty, empty, empty], "INCONCLUSIVE"),
                 ("later_hit", ["ran5_synthetic"], [TimeoutError("synthetic"),
                  hit], "RETRIEVABLE")]
        for name, collections, responses, verdict in cases:
            with self.subTest(name=name), \
                    mock.patch.object(self.module, "list_wg_collections", return_value=collections), \
                    mock.patch.object(self.module, "_post", side_effect=responses):
                result = self.module.probe("R5-synthetic", 5)
            self.assertEqual(result["verdict"], verdict)
            self.assertEqual(result["absent_from"], [])
            if responses:
                self.assertEqual(len(result["details"][0]["errors"]), 1)

    def test_count_is_first_matching_page_and_stops_at_first_hit(self):
        points = [{"payload": {"text": "synthetic"}} for _ in range(2)]
        with mock.patch.object(self.module, "_post", return_value={"result": {
                "points": points, "next_page_offset": "synthetic-next"}}) as post:
            result = self.module.probe_collection("ran5_synthetic", "R5-synthetic", sample=2)
        post.assert_called_once()
        self.assertEqual(post.call_args.args[1]["limit"], 2)
        self.assertEqual(result["matched_key"], "tdocNumber")
        self.assertEqual(result["count"], 2)
        self.assertTrue(result["capped"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
