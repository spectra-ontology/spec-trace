"""Counterexamples for condition provenance, dispatch isolation and recovery bounds.

Uses fabricated source text and deterministic callbacks; no model or DB access.
"""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.condition_recovery import run, validate_request


def request():
    return {"question": "When is the operation allowed?", "initial_answer": "Original\n",
            "source_units": [
                {"unit_id": "u1", "document_id": "doc-a", "version": "v1", "locator": "p1",
                 "native_text": "Only if enabled. Proposal, pending approval.",
                 "text": "Only if enabled. Proposal, pending approval."},
                {"unit_id": "u2", "document_id": "doc-b", "version": "v2", "locator": "p2",
                 "native_text": "λ🙂e\u0301", "text": "λ🙂e\u0301"},
                {"unit_id": "u3", "document_id": "doc-c", "version": "v1", "locator": "p3",
                 "native_text": "SECRET UNSUPPLIED UNIT", "text": "SECRET UNSUPPLIED UNIT"}],
            "initial_unit_ids": ["u1"], "added_unicode_character_budget": 4}


class Caller:
    def __init__(self, action="Stop", selected=None):
        self.calls = []
        self.action = action
        self.selected = [] if selected is None else selected
        self.override = {}
        self.initial_conveyance = "absent"
        self.final_conveyance = "full"

    def __call__(self, stage, payload):
        self.calls.append((stage, deepcopy(payload)))
        if stage in self.override:
            return deepcopy(self.override[stage])
        if stage == "recovery_conditions":
            return {"conditions": [{"condition_id": "c1", "kind": "condition",
                                    "text": "Enabled state is required.",
                                    "evidence": [{"unit_id": "u1", "quote": "Only if enabled."}]}]}
        if stage == "recovery_support":
            return {"conditions": [{"condition_id": c["condition_id"], "supported": True,
                                    "relevant": True} for c in payload["conditions"]]}
        if stage == "recovery_assessment":
            label = self.initial_conveyance if payload["phase"] == "initial" else self.final_conveyance
            return {"conditions": [{"condition_id": c["condition_id"], "conveyance": label,
                                    "reason": "The source condition is assessed in this whole answer.",
                                    "answer_quote": payload["answer"] if label in {"full", "partial"} else ""}
                                    for c in payload["conditions"]], "whole_answer_supported": True}
        if stage == "recovery_diagnosis":
            return {"action": self.action, "unit_ids": self.selected,
                    "reason": "PRIVATE DIAGNOSTIC WORDING"}
        if stage == "recovery_reader":
            return {"answer": "Final answer", "_receipt": {"job_id": "physical-reader-1"}}
        raise AssertionError(stage)


class RecoveryTests(unittest.TestCase):
    def test_validation_is_public_pure_and_allowlisted(self):
        req = request()
        req["private_transport_metadata"] = "not an agent input"
        normalized = validate_request(req)
        self.assertNotIn("private_transport_metadata", normalized)
        normalized["initial_unit_ids"].clear()
        normalized["source_units"][0]["text"] = "changed"
        self.assertEqual(req["initial_unit_ids"], ["u1"])
        self.assertNotEqual(req["source_units"][0]["text"], "changed")

    def test_stop_and_uncertain_preserve_exact_original_without_reader_or_reassessment(self):
        for action in ("Stop", "Uncertain"):
            with self.subTest(action=action):
                call = Caller(action)
                result = run(request(), call)
                self.assertEqual(result["status"], "completed")
                self.assertEqual(result["final_answer"], "Original\n")
                self.assertEqual(result["initial_answer_sha256"], result["final_answer_sha256"])
                self.assertNotIn("recovery_reader", [s for s, _ in call.calls])
                self.assertEqual(sum(s == "recovery_assessment" for s, _ in call.calls), 1)
                self.assertEqual(result["assessments"]["initial"], result["assessments"]["final"])

    def test_native_reference_stages_have_no_initial_or_final_answer(self):
        call = Caller("Ask", ["u1"])
        run(request(), call)
        for stage, payload in call.calls[:2]:
            self.assertIn(stage, {"recovery_conditions", "recovery_support"})
            self.assertNotIn("answer", payload)
            self.assertNotIn("initial_answer", payload)
            self.assertNotIn("reader_sources", payload)
            self.assertNotIn("Original", repr(payload))

    def test_diagnosis_is_independent_of_reference_and_evaluation_outputs(self):
        call = Caller()
        run(request(), call)
        diagnosis = next(p for s, p in call.calls if s == "recovery_diagnosis")
        self.assertEqual(set(diagnosis), {"question", "sources", "native_sources", "initial_unit_ids",
                                          "initial_answer", "added_unicode_character_budget", "contract"})
        self.assertNotIn("Enabled state is required", repr(diagnosis))
        for field in ("conditions", "assessment", "provenance", "support"):
            self.assertNotIn(field, diagnosis)

    def test_unresolved_support_and_relevance_are_preserved_separately_from_false(self):
        for supported, relevant, unresolved in ((None, True, True), (True, None, True),
                                                  (False, True, False), (True, False, False)):
            with self.subTest(supported=supported, relevant=relevant):
                call = Caller()
                call.override["recovery_support"] = {"conditions": [
                    {"condition_id": "c1", "supported": supported, "relevant": relevant}]}
                result = run(request(), call)
                self.assertEqual(result["status"], "completed")
                self.assertEqual(result["unresolved_condition_ids"], ["c1"] if unresolved else [])
                self.assertEqual(result["eligible_condition_ids"], [])

    def test_support_unknown_requires_explicit_null_not_missing_keys(self):
        call = Caller()
        call.override["recovery_support"] = {"conditions": [{"condition_id": "c1", "supported": True}]}
        result = run(request(), call)
        self.assertEqual(result["status"], "invalid_support")

    def test_full_and_partial_require_exact_nonempty_answer_evidence(self):
        for label, quote in (("full", ""), ("partial", "fabricated quote")):
            call = Caller()
            call.override["recovery_assessment"] = {"conditions": [
                {"condition_id": "c1", "conveyance": label, "reason": "claimed coverage",
                 "answer_quote": quote}], "whole_answer_supported": True}
            result = run(request(), call)
            self.assertEqual(result["status"], "invalid_initial_assessment")
            self.assertNotIn("recovery_diagnosis", [s for s, _ in call.calls])

    def test_empty_answer_cannot_receive_full_credit(self):
        req = request()
        req["initial_answer"] = ""
        call = Caller()
        call.initial_conveyance = "full"
        result = run(req, call)
        self.assertEqual(result["status"], "invalid_initial_assessment")
        self.assertNotIn("recovery_reader", [s for s, _ in call.calls])

    def test_ask_reader_isolation_and_fixed_semantic_denominator(self):
        call = Caller("Ask", ["u1"])
        result = run(request(), call)
        self.assertEqual(result["status"], "completed")
        reader = next(p for s, p in call.calls if s == "recovery_reader")
        self.assertEqual([u["unit_id"] for u in reader["sources"]], ["u1"])
        self.assertEqual(reader["attention_unit_ids"], ["u1"])
        self.assertEqual(set(reader), {"question", "initial_answer", "sources", "attention_unit_ids", "contract"})
        self.assertNotIn("PRIVATE DIAGNOSTIC", repr(reader))
        self.assertNotIn("Enabled state is required", repr(reader))
        self.assertNotIn("SECRET UNSUPPLIED UNIT", repr(reader))
        self.assertEqual(result["assessments"]["initial"]["eligible_count"], 1)
        self.assertEqual(result["assessments"]["final"]["eligible_count"], 1)
        self.assertEqual(result["transitions"], [{"condition_id": "c1", "initial": "absent", "final": "full"}])
        self.assertEqual(result["dispatches"][-2]["receipt"]["job_id"], "physical-reader-1")

    def test_acquire_counts_unicode_codepoints_and_keeps_initial_units(self):
        call = Caller("Acquire", ["u2"])
        result = run(request(), call)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(len("λ🙂e\u0301"), 4)
        self.assertEqual(result["added_unicode_characters"], 4)
        self.assertEqual(result["final_unit_ids"], ["u1", "u2"])
        self.assertEqual([u["unit_id"] for u in result["reader_input"]["sources"]], ["u1", "u2"])

    def test_whole_unit_budget_refuses_partial_truncation(self):
        req = request()
        req["added_unicode_character_budget"] = 3
        call = Caller("Acquire", ["u2"])
        result = run(req, call)
        self.assertEqual(result["status"], "invalid_diagnosis")
        self.assertNotIn("recovery_reader", [s for s, _ in call.calls])
        self.assertEqual(result["final_answer"], req["initial_answer"])

    def test_invalid_actions_ids_and_selection_never_fallback(self):
        diagnoses = [
            {"action": "Retry", "unit_ids": []},
            {"action": "Stop", "unit_ids": ["u1"]},
            {"action": "Uncertain", "unit_ids": ["u1"]},
            {"action": "Ask", "unit_ids": []},
            {"action": "Ask", "unit_ids": ["u2"]},
            {"action": "Acquire", "unit_ids": []},
            {"action": "Acquire", "unit_ids": ["u1"]},
            {"action": "Acquire", "unit_ids": ["missing"]},
            {"action": "Ask", "unit_ids": ["u1", "u1"]},
            {"action": "Ask", "unit_ids": "u1"},
            {"action": "Ask", "unit_ids": ["u1"], "answer": "injected"},
            {"action": ["Ask"], "unit_ids": []},
        ]
        for diagnosis in diagnoses:
            with self.subTest(diagnosis=diagnosis):
                call = Caller()
                call.override["recovery_diagnosis"] = diagnosis
                result = run(request(), call)
                self.assertEqual(result["status"], "invalid_diagnosis")
                self.assertNotIn("recovery_reader", [s for s, _ in call.calls])
                self.assertEqual(result["final_answer"], "Original\n")

    def test_early_invalid_request_executes_no_calls(self):
        alterations = [
            ("added_unicode_character_budget", -1), ("added_unicode_character_budget", True),
            ("added_unicode_character_budget", 1.5), ("initial_unit_ids", ["missing"]),
            ("initial_unit_ids", ["u1", "u1"]), ("source_units", []),
        ]
        for key, value in alterations:
            with self.subTest(key=key, value=value):
                req = request()
                req[key] = value
                call = Caller()
                with self.assertRaises(ValueError):
                    run(req, call)
                self.assertEqual(call.calls, [])
        req = request()
        del req["source_units"][0]["version"]
        with self.assertRaises(ValueError):
            run(req, Caller())

    def test_invented_quote_is_structurally_rejected_before_semantic_calls(self):
        call = Caller()
        call.override["recovery_conditions"] = {"conditions": [
            {"condition_id": "c1", "kind": "condition", "text": "invented",
             "evidence": [{"unit_id": "u1", "quote": "A fabricated quote"}]}]}
        result = run(request(), call)
        self.assertEqual(result["status"], "invalid_conditions")
        self.assertEqual(len(call.calls), 1)

    def test_source_presence_does_not_replace_semantic_support(self):
        call = Caller()
        call.override["recovery_support"] = {"conditions": [
            {"condition_id": "c1", "supported": False, "relevant": True}]}
        result = run(request(), call)
        self.assertEqual(result["eligible_condition_ids"], [])
        self.assertIsNone(result["assessments"]["initial"]["coverage"])
        self.assertIsNone(result["assessments"]["initial"]["complete"])

    def test_semantic_assessment_cannot_add_drop_or_duplicate_conditions(self):
        for conditions in ([], [{"condition_id": "other", "conveyance": "full"}],
                           [{"condition_id": "c1", "conveyance": "full"}] * 2):
            call = Caller("Ask", ["u1"])
            call.override["recovery_assessment"] = {"conditions": conditions, "whole_answer_supported": True}
            result = run(request(), call)
            self.assertEqual(result["status"], "invalid_initial_assessment")
            self.assertNotIn("recovery_reader", [s for s, _ in call.calls])

    def test_projection_loss_and_withheld_source_are_separate(self):
        for mode, expected in (("projected_out", "projection_review"),
                               ("withheld", "acquisition_candidate"),
                               ("supplied", "reread_candidate")):
            with self.subTest(mode=mode):
                req = request()
                if mode == "projected_out":
                    req["source_units"][0]["text"] = "A topic-only projection."
                if mode == "withheld":
                    req["initial_unit_ids"] = []
                result = run(req, Caller())
                self.assertEqual(result["provenance"][0]["evidence"][0]["review_location"], expected)

    def test_partial_and_uncertain_are_not_full_coverage(self):
        for label in ("partial", "uncertain", "absent"):
            call = Caller()
            call.initial_conveyance = label
            result = run(request(), call)
            self.assertEqual(result["assessments"]["initial"]["coverage"], 0)
            self.assertFalse(result["assessments"]["initial"]["complete"])

    def test_followup_can_lose_coverage_and_records_the_regression(self):
        call = Caller("Ask", ["u1"])
        call.initial_conveyance = "full"
        call.final_conveyance = "partial"
        result = run(request(), call)
        self.assertEqual(result["transitions"], [
            {"condition_id": "c1", "initial": "full", "final": "partial"}])
        self.assertTrue(result["assessments"]["initial"]["complete"])
        self.assertFalse(result["assessments"]["final"]["complete"])
        evidence = result["final_provenance"][0]["evidence"][0]
        self.assertEqual((evidence["document_id"], evidence["version"], evidence["locator"]),
                         ("doc-a", "v1", "p1"))

    def test_final_assessment_cannot_change_the_frozen_condition_set(self):
        call = Caller("Ask", ["u1"])
        def drop_final(stage, payload):
            if stage == "recovery_assessment" and payload["phase"] == "final":
                call.calls.append((stage, deepcopy(payload)))
                return {"conditions": [], "whole_answer_supported": True}
            return call(stage, payload)
        result = run(request(), drop_final)
        self.assertEqual(result["status"], "invalid_final_assessment")
        self.assertEqual(result["eligible_condition_ids"], ["c1"])
        self.assertEqual(result["final_answer"], "Final answer")
        self.assertEqual(sum(s == "recovery_reader" for s, _ in call.calls), 1)

    def test_request_and_dispatched_record_resist_callback_mutation(self):
        req = request()
        before = deepcopy(req)
        original = Caller("Ask", ["u1"])
        def mutate(stage, payload):
            answer = original(stage, payload)
            payload.clear()
            return answer
        result = run(req, mutate)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(req, before)
        self.assertTrue(all(record["payload"] for record in result["dispatches"]))

    def test_malformed_reader_does_not_retry_or_silently_accept(self):
        call = Caller("Ask", ["u1"])
        call.override["recovery_reader"] = {"answer": 4}
        result = run(request(), call)
        self.assertEqual(result["status"], "invalid_reader")
        self.assertEqual(sum(s == "recovery_reader" for s, _ in call.calls), 1)
        self.assertEqual(result["final_answer"], "Original\n")


if __name__ == "__main__":
    unittest.main()
