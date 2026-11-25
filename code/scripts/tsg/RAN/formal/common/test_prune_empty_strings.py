"""The empty-string cleanup records before writing, guards the written key and re-checks the graph."""
import contextlib
import io
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import prune_stale_backfill as prune
from common import backfill_provenance


def _rows(*rows):
    return SimpleNamespace(data=lambda: list(rows))


class EmptyStringProperties(unittest.TestCase):
    def test_unsafe_key_is_blocked_and_safe_keys_are_dropped(self):
        session = SimpleNamespace(run=lambda *a, **k: _rows(
            {"e": "a", "n": "R3-000001", "labels": ["Tdoc"], "created_by": "phase-6-backfill",
             "ks": ["release", "title"]},
            {"e": "b", "n": "R3-000002", "labels": ["Tdoc"], "created_by": "phase-6-backfill",
             "ks": ["bad key"]}))
        found = backfill_provenance.empty_string_properties(session)
        self.assertEqual([e["verdict"] for e in found], ["drop", "blocked"])
        self.assertEqual(found[0]["keys"], ["release", "title"])

    def test_query_keeps_the_empty_value_precondition_and_rejects_unsafe_names(self):
        query = prune._q_drop_empty("release")
        self.assertIn("t.`release` = ''", query)
        self.assertIn("REMOVE t.`release`", query)
        for key in ("bad key", "x`) DETACH DELETE t //", ""):
            with self.subTest(key=key), self.assertRaises(ValueError):
                prune._q_drop_empty(key)


class DropEmptyStrings(unittest.TestCase):
    def setUp(self):
        self.found = [{"element_id": "a", "name": "R3-000001", "labels": ["Tdoc"],
                       "created_by": "phase-6-backfill", "keys": ["release"], "verdict": "drop",
                       "reason": None}]
        self.calls = []

    def _session(self, removed):
        def execute_write(fn):
            self.calls.append("write")
            return removed
        return SimpleNamespace(execute_write=execute_write)

    def _run(self, apply, removed, after):
        results = iter([self.found, after])
        with patch.object(backfill_provenance, "empty_string_properties", lambda s: next(results)), \
                patch.object(prune, "_record", side_effect=lambda *a: self.calls.append("record")
                             or prune.PROJECT_ROOT / "logs" / "x.json"), \
                contextlib.redirect_stdout(io.StringIO()):
            return prune._drop_empty_strings(self._session(removed), "RAN3", apply)

    def test_dry_run_neither_records_nor_writes(self):
        self.assertEqual(self._run(False, 1, []), 0)
        self.assertEqual(self.calls, [])

    def test_apply_records_before_writing_and_passes_when_nothing_remains(self):
        self.assertEqual(self._run(True, 1, []), 0)
        self.assertEqual(self.calls, ["record", "write"])

    def test_apply_fails_when_the_removed_count_differs_or_values_remain(self):
        self.assertEqual(self._run(True, 0, []), 1)
        self.calls.clear()
        self.assertEqual(self._run(True, 1, self.found), 1)


if __name__ == "__main__":
    unittest.main()
