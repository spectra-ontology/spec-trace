"""Synthetic malformed email records and the legacy verification exit contract."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import email_fetch_status as status


class EmailStatusTests(unittest.TestCase):
    def test_every_stored_value_has_a_defined_hashable_classification(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "message.json"
            cases = [("ok", "ok"), ("no_body_url", "no_body_url"),
                     ("body_failed", "body_failed"), ("detail_failed", "detail_failed"),
                     (None, "unknown"), ([], "unknown"), ({}, "unknown"),
                     (False, "unknown"), ("unrecognized", "unknown")]
            for value, expected in cases:
                with self.subTest(value=value):
                    path.write_text(json.dumps({"fetch_status": value}))
                    actual = status.message_file_status(path)
                    self.assertEqual(actual, expected)
                    hash(actual)
            for raw in ("[1]", "{broken"):
                path.write_text(raw)
                self.assertEqual(status.message_file_status(path), "parse_error")
            path.unlink()
            self.assertEqual(status.message_file_status(path), "parse_error")

    def test_legacy_verifier_reports_malformed_files_and_propagates_failure(self):
        directory = Path(__file__).resolve().parents[1] / "corpus-collection/src/scripts/emails"
        common_spec = importlib.util.spec_from_file_location("legacy_email_common", directory / "common.py")
        common = importlib.util.module_from_spec(common_spec)
        common_spec.loader.exec_module(common)
        spec = importlib.util.spec_from_file_location("legacy_email_verify", directory / "04_verify.py")
        verifier = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"common": common}):
            spec.loader.exec_module(verifier)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            messages = root / "messages"
            messages.mkdir()
            message = messages / "one.json"
            message.write_text('{"fetch_status": []}')
            with patch.object(verifier, "data_raw_path", return_value=root), \
                 patch.object(verifier, "log_path", return_value=root / "logs"), \
                 patch.object(sys, "argv", ["verify", "--wg", "RAN1"]), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(verifier.main(), 1)
                failed = root / "logs/04_verify_failed.jsonl"
                self.assertEqual(json.loads(failed.read_text()),
                                 {"path": "messages/one.json", "fetch_status": "unknown"})
                message.write_text('{"fetch_status": "no_body_url"}')
                self.assertEqual(verifier.main(), 0)
                self.assertEqual(failed.read_bytes(), b"")
                with patch.object(sys, "argv", ["verify", "--wg", "WRONG"]), \
                     contextlib.redirect_stderr(io.StringIO()), \
                     patch.object(verifier, "verify_wg") as verify:
                    with self.assertRaises(SystemExit) as raised:
                        verifier.main()
                    self.assertEqual(raised.exception.code, 2)
                    verify.assert_not_called()


if __name__ == "__main__":
    unittest.main()
