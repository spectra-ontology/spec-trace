"""Bounded transport and saved-response replay tests; no actual CLI is invoked."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import evidence_workflow as workflow
from test_condition_recovery import Caller, request
from test_answer_maintenance import Agent, packet


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.config = self.root / "runner.json"
        self.config.write_text(json.dumps({"argv": ["synthetic-agent"]}))
        self.request_path = self.root / "request.json"
        self.output = self.root / "logs" / "run-1"

    def invoke(self, agent):
        def invoke(argv, **kwargs):
            stage = json.loads(kwargs["input"].split("\n", 1)[1])
            response = agent(stage["stage"], stage["payload"])
            return subprocess.CompletedProcess(argv, 0, json.dumps({"agent": "synthetic-reviewer", "result": response}), "diagnostic stderr")
        return invoke

    def create(self, mode="recover", *, agent=None, **kwargs):
        agent = agent or (Caller("Ask", ["u1"]) if mode == "recover" else Agent())
        self.request_path.write_text(json.dumps(request() if mode == "recover" else packet()))
        with patch.object(workflow, "invoke", side_effect=self.invoke(agent)) as mocked:
            receipt = workflow.run_workflow(mode, self.request_path, self.output, self.config,
                                            root=self.root, **kwargs)
        self.assertEqual(mocked.call_count, receipt["physical_dispatches"])
        return receipt

    def update_json(self, path, mutate):
        value = workflow.strict_json(path.read_bytes())
        mutate(value)
        workflow.write_json(path, value)
        return value

    def test_success_replays_without_cli_and_registered_binding_matches(self):
        for mode in ("recover", "maintain"):
            with self.subTest(mode=mode):
                self.output = self.root / "logs" / mode
                receipt = self.create(mode)
                self.assertEqual(receipt["review_status"], "ready_for_independent_review")
                self.assertEqual(receipt["accounting"]["prior_initial_answer_generation"], "not measured")
                artifact = self.output / "candidate.md"
                with patch.object(workflow, "invoke", side_effect=AssertionError("Replay must not invoke agents")):
                    binding = workflow.verified_binding(self.output, artifact, root=self.root)
                    workflow.verify_registered([binding], artifact, root=self.root)
                self.assertEqual(binding["mode"], mode)

    def test_recovery_completion_requires_semantic_coverage_and_resolved_conditions(self):
        result = {"status": "completed", "action": "Stop", "final_answer": "A candidate",
                  "assessments": {"final": {"whole_answer_supported": True, "complete": True}}}
        self.assertTrue(workflow.review_ready("recover", result))
        for key, value in (("unresolved_condition_ids", ["c1"]), ("final_answer", "  "),
                           ("action", "Uncertain"), ("status", "complete")):
            changed = deepcopy(result)
            changed[key] = value
            self.assertFalse(workflow.review_ready("recover", changed))
        result["assessments"]["final"]["complete"] = False
        self.assertFalse(workflow.review_ready("recover", result))

    def test_maintenance_fallback_is_ready_only_when_every_physical_call_returned(self):
        for failed_transport in (True, False):
            with self.subTest(failed_transport=failed_transport):
                self.output = self.root / "logs" / ("failed-call" if failed_transport else "invalid-decision")
                agent = Agent()
                if failed_transport:
                    agent.responses["maintenance_decision"] = RuntimeError("synthetic transport failure")
                else:
                    agent.responses["maintenance_decision"]["action"] = "invalid_action"
                receipt = self.create("maintain", agent=agent)
                result = workflow.strict_json((self.output / "result.json").read_bytes())
                self.assertEqual(result["status"], "complete")
                self.assertEqual(result["action"], "full_qa")
                self.assertEqual(receipt["review_status"], "review_required" if failed_transport
                                 else "ready_for_independent_review")
                self.assertEqual(sum(record["status"] == "failed" for record in receipt["calls"]),
                                 int(failed_transport))
                artifact = self.output / "candidate.md"
                if failed_transport:
                    with self.assertRaisesRegex(ValueError, "stage did not return"):
                        workflow.verified_binding(self.output, artifact, root=self.root)
                else:
                    workflow.verified_binding(self.output, artifact, root=self.root)

    def test_candidate_tamper_and_stale_output_are_rejected(self):
        self.create()
        artifact = self.output / "candidate.md"
        artifact.write_text("changed")
        with self.assertRaisesRegex(ValueError, "artifact changed"):
            workflow.verified_binding(self.output, artifact, root=self.root)
        with self.assertRaisesRegex(ValueError, "already exists"):
            workflow.run_workflow("recover", self.request_path, self.output, self.config, root=self.root)

    def test_renewed_result_and_candidate_hashes_do_not_bind_an_invented_answer(self):
        self.create()
        result_path = self.output / "result.json"
        self.update_json(result_path, lambda result: result.update(final_answer="Invented replacement"))
        artifact = self.output / "candidate.md"
        artifact.write_text("Invented replacement")
        self.update_json(self.output / "receipt.json", lambda receipt: receipt.update(
            result_sha256=workflow.sha(result_path.read_bytes()), candidate_sha256=workflow.sha(artifact.read_bytes())))
        with self.assertRaisesRegex(ValueError, "does not reproduce"):
            workflow.verified_binding(self.output, artifact, root=self.root)

    def test_renewed_request_hash_cannot_reuse_unrelated_call_payloads(self):
        self.create()
        path = self.output / "request.json"
        self.update_json(path, lambda value: value.update(question="An unrelated question"))
        self.update_json(self.output / "receipt.json", lambda receipt: receipt.update(request_sha256=workflow.sha(path.read_bytes())))
        with self.assertRaisesRegex(ValueError, "replay stage or payload mismatch"):
            workflow.verified_binding(self.output, self.output / "candidate.md", root=self.root)

    def test_changed_saved_input_with_refreshed_call_hash_is_rejected(self):
        self.create()
        call = self.output / "calls" / "001-recovery_conditions"
        self.update_json(call / "input.json", lambda value: value.update(question="Changed stage question"))
        record = self.update_json(call / "receipt.json", lambda value: value.update(
            input_sha256=workflow.sha((call / "input.json").read_bytes())))
        self.update_json(self.output / "receipt.json", lambda value: value["calls"].__setitem__(0, record))
        with self.assertRaisesRegex(ValueError, "replay stage or payload mismatch"):
            workflow.verified_binding(self.output, self.output / "candidate.md", root=self.root)

    def test_failed_response_bytes_and_returncode_are_preserved_before_parse(self):
        for returncode, stdout in ((0, "malformed JSON"), (0, '{"result":{}}'), (7, "process failure output")):
            with self.subTest(returncode=returncode, stdout=stdout):
                output = self.root / ("failed-" + str(returncode) + "-" + str(len(stdout)))
                caller = workflow.ApprovedCaller(self.config, output, root=self.root)
                with patch.object(workflow, "invoke", return_value=subprocess.CompletedProcess(
                        ["synthetic-agent"], returncode, stdout, "failure details")):
                    with self.assertRaises((ValueError, RuntimeError)):
                        caller("recovery_diagnosis", {"question": "q"})
                directory = output / "calls" / "001-recovery_diagnosis"
                self.assertEqual((directory / "response.json").read_text(), stdout)
                self.assertEqual((directory / "stderr.txt").read_text(), "failure details")
                record = workflow.strict_json((directory / "receipt.json").read_bytes())
                self.assertEqual(record["returncode"], returncode)
                self.assertEqual(record["status"], "failed")
                self.assertEqual(record["response_sha256"], workflow.sha(stdout.encode()))

    def test_timeout_partial_streams_are_preserved(self):
        caller = workflow.ApprovedCaller(self.config, self.output, root=self.root)
        with patch.object(workflow, "invoke", side_effect=subprocess.TimeoutExpired(
                "synthetic-agent", 1, output=b"partial output", stderr=b"partial errors")):
            with self.assertRaises(subprocess.TimeoutExpired):
                caller("recovery_conditions", {})
        directory = self.output / "calls" / "001-recovery_conditions"
        self.assertEqual((directory / "partial_stdout.txt").read_bytes(), b"partial output")
        self.assertEqual((directory / "partial_stderr.txt").read_bytes(), b"partial errors")

    def test_call_budget_is_enforced_before_an_extra_invocation(self):
        agent = Caller("Ask", ["u1"])
        with self.assertRaisesRegex(RuntimeError, "budget exhausted"):
            self.create(agent=agent, max_calls=1)
        receipt = workflow.strict_json((self.output / "receipt.json").read_bytes())
        self.assertEqual(receipt["physical_dispatches"], 1)
        self.assertEqual(receipt["state"], "failed")
        self.assertFalse((self.output / "candidate.md").exists())
        with self.assertRaisesRegex(ValueError, "no completed candidate"):
            workflow.verified_binding(self.output, self.output / "candidate.md", root=self.root)

    def test_invalid_request_creates_no_workflow_and_invokes_no_agent(self):
        self.request_path.write_text(json.dumps({"question": "incomplete"}))
        with patch.object(workflow, "invoke", side_effect=AssertionError("Unexpected call")):
            with self.assertRaises(ValueError):
                workflow.run_workflow("recover", self.request_path, self.output, self.config, root=self.root)
        self.assertFalse(self.output.exists())

    def test_strict_json_rejects_duplicates_and_nonfinite_numbers(self):
        for raw in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":1e999}'):
            with self.assertRaises(ValueError):
                workflow.strict_json(raw)

    def test_receipt_replace_failure_preserves_previous_record(self):
        path = self.root / 'receipt.json'
        path.write_bytes(b'{"state":"started"}\n')
        with patch('os.replace', side_effect=OSError('replace failed')):
            with self.assertRaises(OSError):
                workflow.write_json(path, {'state': 'candidate_generated'})
        self.assertEqual(path.read_bytes(), b'{"state":"started"}\n')
        self.assertFalse(list(self.root.glob('.receipt.json.*.tmp')))

    def test_receipt_symlink_and_invalid_json_preserve_existing_record(self):
        path = self.root / 'receipt.json'
        path.write_bytes(b'preserved\n')
        link = self.root / 'link.json'
        link.symlink_to(path)
        for destination, value in ((link, {'state': 'returned'}), (path, {'value': float('nan')})):
            with self.subTest(destination=destination), self.assertRaises(ValueError):
                workflow.write_json(destination, value)
            self.assertEqual(path.read_bytes(), b'preserved\n')


if __name__ == "__main__":
    unittest.main()
