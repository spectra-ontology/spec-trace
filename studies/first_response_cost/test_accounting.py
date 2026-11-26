#!/usr/bin/env python3
"""Regression checks for completion cutoffs, streamed usage and retained evidence."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from analyze import jsonl, summarize
from collect import extract


def assistant(message_id, timestamp, usage, content, stop=None):
    return {"type": "assistant", "timestamp": timestamp, "message": {"id": message_id,
        "usage": {"input_tokens": usage, "output_tokens": 1}, "content": content, "stop_reason": stop}}


class CutoffTests(unittest.TestCase):
    def extract_rows(self, rows):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "session.jsonl"
            path.write_text("".join(json.dumps(r) + "\n" for r in rows))
            return extract(path, "test-session")

    def test_late_repair_and_duplicate_stream_do_not_change_first_usage(self):
        start = {"type": "user", "timestamp": "2026-01-01T00:00:00Z", "message": {"content": "task"}}
        done = [{"type": "tool_use", "id": "done", "name": "SubagentHandback", "input": {"message": "done"}}]
        rows = [start, assistant("first", "2026-01-01T00:00:01Z", 10, []),
            assistant("first", "2026-01-01T00:00:02Z", 20, done),
            {"type": "user", "timestamp": "2026-01-01T00:00:03Z", "message": {"content": [{"type": "tool_result", "tool_use_id": "done", "content": "ok"}]}}]
        before, first_events = self.extract_rows(rows)
        rows.append(assistant("repair", "2026-01-02T00:00:01Z", 9999, [{"type": "text", "text": "repair done"}], "end_turn"))
        after, events = self.extract_rows(rows)
        self.assertEqual(before["first_submission_cutoff"], after["first_submission_cutoff"])
        self.assertEqual(before["first_submission_seconds"], 3)
        self.assertEqual([e for e in events if e["interval"] == "first_submission"], first_events)
        self.assertEqual(sum(e["usage"]["input_tokens"] for e in first_events), 20)
        self.assertEqual(len(first_events), 1)

    def test_enforced_handback_delivery_is_initial_cost(self):
        rows = [assistant("plain", "2026-01-01T00:00:01Z", 10, [{"type": "text", "text": "done"}], "end_turn"),
            {"type": "user", "timestamp": "2026-01-01T00:00:02Z", "message": {"content": "[handback-send-enforce] deliver now"}},
            assistant("delivered", "2026-01-01T00:00:03Z", 30, [{"type": "tool_use", "id": "done", "name": "SubagentHandback", "input": {"message": "done"}}]),
            {"type": "user", "timestamp": "2026-01-01T00:00:04Z", "message": {"content": [{"type": "tool_result", "tool_use_id": "done", "content": "ok"}]}}]
        session, events = self.extract_rows(rows)
        self.assertEqual(session["first_submission_cutoff"]["completion_kind"], "SubagentHandback")
        self.assertTrue(session["first_submission_cutoff"]["tool_result_acknowledged"])
        self.assertEqual(session["first_submission_cutoff"]["timestamp"], "2026-01-01T00:00:04Z")
        self.assertTrue(all(e["interval"] == "first_submission" for e in events))

    def test_missing_handback_acknowledgment_remains_unresolved(self):
        session, events = self.extract_rows([assistant("pending", "2026-01-01T00:00:01Z", 10,
            [{"type": "tool_use", "id": "done", "name": "SubagentHandback", "input": {"message": "done"}}])])
        self.assertIsNone(session["first_submission_seconds"])
        self.assertIsNone(session["first_submission_cutoff"])
        self.assertEqual(session["cutoff_status"], "unresolved_missing_handback_acknowledgment")
        self.assertEqual(events[0]["interval"], "uncut")

    def test_missing_completion_remains_unresolved(self):
        session, events = self.extract_rows([assistant("partial", "2026-01-01T00:00:01Z", 10,
            [{"type": "tool_use", "id": "read", "name": "Bash", "input": {"command": "read"}}])])
        self.assertIsNone(session["first_submission_seconds"])
        self.assertEqual(session["cutoff_status"], "unresolved_no_completion_event")
        self.assertEqual(events[0]["interval"], "uncut")

    def test_released_first_summary_ignores_arbitrary_late_usage(self):
        folder = Path(__file__).resolve().parent
        sessions, messages = jsonl(folder / "sessions.jsonl"), jsonl(folder / "message_usage.jsonl")
        build = json.loads((folder / "build_records.json").read_text())
        baseline = summarize(sessions, messages, build)
        changed = copy.deepcopy(messages)
        tail = next(m for m in changed if m["interval"] == "after_first_submission")
        tail["usage"]["input_tokens"] += 123456789
        comparison = summarize(sessions, changed, build)
        for route in baseline["routes"]:
            self.assertEqual(baseline["routes"][route]["first_submission"], comparison["routes"][route]["first_submission"])
        self.assertNotEqual(baseline, comparison)
        with self.assertRaisesRegex(AssertionError, "Duplicate message"):
            summarize(sessions, messages + [messages[0]], build)


if __name__ == "__main__":
    unittest.main()
