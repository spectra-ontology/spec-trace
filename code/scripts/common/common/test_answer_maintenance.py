"""Small synthetic contract and failure tests for whole-answer maintenance."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from answer_maintenance import changed_line_inventory, run, validate_request


OLD_SOURCE = "When enabled, the device shall retain the value.\n"
NEW_SOURCE = "When enabled, the device shall retain the value and report it.\n"
OLD_ANSWER = "When enabled, retain the value."
NEW_ANSWER = "When enabled, retain the value and report it."


def unit(body, edition="OLD", ident="rule"):
    return {"unit_id": ident, "text": body,
            "provenance": {"source_id": "synthetic-rule", "edition": edition,
                           "locator": "synthetic/unit", "sha256": hashlib.sha256(body.encode()).hexdigest()}}


def packet():
    return {"schema": 1, "question": "What is required when enabled?",
            "context": "The device is enabled.", "old_answer": OLD_ANSWER,
            "old_units": [unit(OLD_SOURCE)], "new_units": [unit(NEW_SOURCE, "NEW")]}


def evidence(body):
    return [{"unit_id": "rule", "quote": body.strip()}]


def assertion(answer):
    return {"id": "a1", "start": 0, "end": len(answer), "text": answer}


def criteria():
    return {"old_required": [{"id": "o1", "requirement": "Retain the value when enabled.",
                              "evidence": evidence(OLD_SOURCE)}],
            "new_required": [{"id": "n1", "requirement": "Retain the value when enabled.",
                              "evidence": evidence(NEW_SOURCE)},
                             {"id": "n2", "requirement": "Report the value when enabled.",
                              "evidence": evidence(NEW_SOURCE)}],
            "continuing_links": [{"old_id": "o1", "new_id": "n1", "reason": "The retention duty continues."}],
            "scope_uncertainties": []}


def assessment(answer, body, ident):
    coverage = [{"requirement_id": key, "label": "full", "reason": "This required content is stated.",
                 "answer_quote": answer, "evidence": evidence(body)}
                for key in (["n1", "n2"] if ident == "n1" else [ident])]
    return {"coverage": coverage,
            "assertion_support": [{**assertion(answer), "label": "supported",
                                   "reason": "The source states this duty and its guard.", "evidence": evidence(body)}],
            "scope_uncertainties": []}


class Agent:
    """An explicit deterministic response fixture, never a real model."""

    def __init__(self, action="replace", answer=NEW_ANSWER):
        self.calls = []
        self.responses = {
            "maintenance_criteria": criteria(),
            "maintenance_assertions": {"assertions": [assertion(OLD_ANSWER)]},
            "maintenance_decision": {"action": action, "answer": "" if action == "full_qa" else answer,
                                     "reason": "The new duty is considered.", "dispositions": [
                                         {"assertion_id": "a1", "status": "revised", "reason": "The guard is kept and the new duty is added."}]},
            "maintenance_fresh_qa": {"answer": answer},
            "maintenance_assess_old": assessment(OLD_ANSWER, OLD_SOURCE, "o1"),
            "maintenance_assess_new": assessment(answer, NEW_SOURCE, "n1"),
        }

    def __call__(self, stage, payload):
        self.calls.append((stage, deepcopy(payload)))
        response = self.responses[stage]
        if isinstance(response, Exception):
            raise response
        return deepcopy(response)


class AnswerMaintenanceTests(unittest.TestCase):
    def test_replace_checks_sources_before_answers_and_hides_policy_from_assessor(self):
        agent = Agent()
        result = run(packet(), agent)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["final_answer"], NEW_ANSWER)
        self.assertEqual(result["action"], "replace")
        self.assertEqual(result["continuing_content"][0]["label"], "preserved")
        self.assertEqual([s for s, _ in agent.calls], ["maintenance_criteria", "maintenance_assertions",
                                                     "maintenance_decision", "maintenance_assess_old", "maintenance_assess_new"])
        for key in ("old_answer", "candidate", "action", "decision"):
            self.assertNotIn(key, agent.calls[0][1])
        for stage, payload in agent.calls:
            if "assess_" in stage:
                for key in ("action", "decision", "old_answer", "changed_lines"):
                    self.assertNotIn(key, payload)
        decision = dict(agent.calls)["maintenance_decision"]
        self.assertNotIn("old_units", decision)
        self.assertNotIn("new_units", decision)
        self.assertEqual(decision["changed_lines"], result["changed_lines"])

    def test_reuse_preserves_exact_utf8_bytes_including_whitespace(self):
        request = packet()
        answer = "  État actif: retain the value.\r\n"
        request["old_answer"] = answer
        request["new_units"] = [unit(OLD_SOURCE, "NEW")]
        agent = Agent("reuse", answer)
        agent.responses["maintenance_assertions"] = {"assertions": [assertion(answer)]}
        agent.responses["maintenance_decision"]["dispositions"][0]["status"] = "retained"
        agent.responses["maintenance_criteria"]["new_required"] = [
            {"id": "n1", "requirement": "Retain the value when enabled.", "evidence": evidence(OLD_SOURCE)}]
        agent.responses["maintenance_assess_old"] = assessment(answer, OLD_SOURCE, "o1")
        agent.responses["maintenance_assess_new"] = assessment(answer, OLD_SOURCE, "n1")
        agent.responses["maintenance_assess_new"]["coverage"] = agent.responses["maintenance_assess_new"]["coverage"][:1]
        result = run(request, agent)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["final_answer"].encode(), answer.encode())
        self.assertEqual(result["changed_lines"], [])
        self.assertNotIn("maintenance_fresh_qa", result["call_stages"])

    def test_explicit_full_qa_receives_complete_new_sources_once_without_old_answer(self):
        agent = Agent("full_qa")
        result = run(packet(), agent)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["action"], "full_qa")
        self.assertEqual(result["call_stages"].count("maintenance_fresh_qa"), 1)
        fresh = dict(agent.calls)["maintenance_fresh_qa"]
        self.assertEqual(fresh["new_units"], packet()["new_units"])
        for key in ("old_answer", "old_units", "old_assertions", "decision"):
            self.assertNotIn(key, fresh)

    def test_invalid_decisions_get_one_fresh_answer_instead_of_silent_update_retry(self):
        mutations = [
            lambda d: d.update(action="reuse", answer=NEW_ANSWER),
            lambda d: d.update(answer=""),
            lambda d: d.update(action="full_qa", answer=NEW_ANSWER),
            lambda d: d.update(dispositions=[]),
            lambda d: d["dispositions"][0].update(reason=""),
            lambda d: d["dispositions"].append(deepcopy(d["dispositions"][0])),
            lambda d: d.update(action="invented_action"),
            lambda d: d["dispositions"][0].update(evidence=[{"unit_id": "rule", "quote": "fabricated quote"}]),
        ]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                agent = Agent()
                mutate(agent.responses["maintenance_decision"])
                result = run(packet(), agent)
                self.assertEqual(result["status"], "complete")
                self.assertEqual(result["action"], "full_qa")
                self.assertIn("decision_error", result)
                self.assertEqual(result["call_stages"].count("maintenance_decision"), 1)
                self.assertEqual(result["call_stages"].count("maintenance_fresh_qa"), 1)

    def test_failed_decision_call_can_fall_back_but_failed_fresh_answer_is_not_retried(self):
        agent = Agent()
        agent.responses["maintenance_decision"] = RuntimeError("synthetic decision failure")
        agent.responses["maintenance_fresh_qa"] = {"answer": ""}
        result = run(packet(), agent)
        self.assertEqual(result["status"], "review_required")
        self.assertEqual(result["final_answer"], "")
        self.assertEqual(result["validation_errors"][0]["stage"], "maintenance_fresh_qa")
        self.assertEqual(result["call_stages"].count("maintenance_fresh_qa"), 1)
        self.assertNotIn("maintenance_assess_new", result["call_stages"])

    def test_input_hash_scope_and_inventory_fail_before_agent_call(self):
        requests = []
        bad = packet(); bad["old_units"][0]["text"] += "hidden change"; requests.append(bad)
        bad = packet(); bad["new_units"][0]["unit_id"] = "different"; requests.append(bad)
        bad = packet(); bad["changed_lines"] = []; requests.append(bad)
        bad = packet(); bad["new_units"][0]["provenance"]["edition"] = ""; requests.append(bad)
        bad = packet(); bad["old_units"].append(deepcopy(bad["old_units"][0])); requests.append(bad)
        bad = packet(); bad["schema"] = True; requests.append(bad)
        for request in requests:
            with self.subTest(request=request):
                agent = Agent()
                with self.assertRaises(ValueError):
                    run(request, agent)
                self.assertEqual(agent.calls, [])

    def test_inventory_covers_additions_deletions_newlines_and_reconstructs_new_bytes(self):
        examples = [("", "added\n"), ("removed\n", ""), ("a\r\n", "a\n"), ("a\nb\nc", "a\nx\nc\n"),
                    ("same", "same")]
        for before, after in examples:
            with self.subTest(before=before, after=after):
                old, new = [unit(before)], [unit(after, "NEW")]
                edits = changed_line_inventory(old, new)
                lines = before.splitlines(keepends=True)
                for edit in reversed(edits):
                    a, b = edit["old_range"]
                    self.assertEqual(lines[a:b], edit["old_lines"])
                    lines[a:b] = edit["new_lines"]
                self.assertEqual("".join(lines).encode(), after.encode())

    def test_validate_request_returns_derived_inventory_without_mutating_input(self):
        request = packet()
        before = deepcopy(request)
        validated = validate_request(request)
        self.assertEqual(request, before)
        self.assertEqual(validated["changed_lines"], changed_line_inventory(request["old_units"], request["new_units"]))
        validated["old_units"][0]["text"] = "mutated"
        self.assertEqual(request, before)

    def test_criteria_wrong_edition_quote_and_unknown_link_stop_before_answer_access(self):
        for kind in ("quote", "link", "duplicate"):
            with self.subTest(kind=kind):
                agent = Agent()
                response = agent.responses["maintenance_criteria"]
                if kind == "quote":
                    response["old_required"][0]["evidence"] = evidence(NEW_SOURCE)
                elif kind == "link":
                    response["continuing_links"][0]["new_id"] = "unknown"
                else:
                    response["new_required"].append(deepcopy(response["new_required"][0]))
                result = run(packet(), agent)
                self.assertEqual(result["status"], "review_required")
                self.assertEqual(result["call_stages"], ["maintenance_criteria"])
                self.assertEqual(result["validation_errors"][0]["stage"], "maintenance_criteria")

    def test_assertion_inventory_cannot_silently_skip_or_overlap_old_answer_content(self):
        for rows in ([], [{"id": "a1", "start": 5, "end": len(OLD_ANSWER), "text": OLD_ANSWER[5:]}],
                     [assertion(OLD_ANSWER), {**assertion(OLD_ANSWER), "id": "a2"}]):
            with self.subTest(rows=rows):
                agent = Agent()
                agent.responses["maintenance_assertions"] = {"assertions": rows}
                result = run(packet(), agent)
                self.assertEqual(result["status"], "review_required")
                self.assertNotIn("maintenance_decision", result["call_stages"])

    def test_literal_assertions_without_offsets_are_located_deterministically(self):
        agent = Agent()
        for stage, field in (("maintenance_assertions", "assertions"),
                             ("maintenance_assess_old", "assertion_support"),
                             ("maintenance_assess_new", "assertion_support")):
            for row in agent.responses[stage][field]:
                del row["start"]
                del row["end"]
        result = run(packet(), agent)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["old_assertions"][0]["start"], 0)
        self.assertEqual(result["old_assertions"][0]["end"], len(OLD_ANSWER))
        self.assertEqual(result["assessments"]["new"]["assertion_support"][0]["end"], len(NEW_ANSWER))

    def test_invalid_or_incomplete_assessment_never_reports_completion(self):
        mutations = [
            lambda a: a.update(coverage=[]),
            lambda a: a["coverage"][0].update(answer_quote="invented answer text"),
            lambda a: a["coverage"][0].update(evidence=evidence(OLD_SOURCE)),
            lambda a: a.update(assertion_support=[]),
            lambda a: a["assertion_support"][0].update(evidence=[]),
            lambda a: a["assertion_support"][0].update(label="invented"),
            lambda a: a.update(scope_uncertainties="not an array"),
        ]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                agent = Agent()
                mutate(agent.responses["maintenance_assess_new"])
                result = run(packet(), agent)
                self.assertEqual(result["status"], "review_required")
                self.assertEqual(result["final_answer"], NEW_ANSWER)
                self.assertEqual(result["validation_errors"][0]["stage"], "maintenance_assess_new")
                self.assertEqual(result["call_stages"].count("maintenance_assess_new"), 1)

    def test_new_omission_is_reported_as_lost_eligible_content(self):
        agent = Agent()
        agent.responses["maintenance_assess_new"]["coverage"][0].update(label="partial")
        result = run(packet(), agent)
        self.assertEqual(result["status"], "review_required")
        self.assertEqual(result["continuing_content"][0]["label"], "lost")

    def test_inherited_old_omission_is_not_claimed_as_new_preservation_loss(self):
        agent = Agent()
        agent.responses["maintenance_assess_old"]["coverage"][0].update(label="missing", answer_quote="")
        agent.responses["maintenance_assess_old"]["assertion_support"][0].update(label="unsupported")
        result = run(packet(), agent)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["continuing_content"][0]["label"], "not_eligible")
        self.assertFalse(result["continuing_content"][0]["eligible"])

    def test_missing_new_requirement_is_separate_from_preservation_of_old_content(self):
        agent = Agent()
        agent.responses["maintenance_assess_new"]["coverage"][1].update(label="missing", answer_quote="")
        result = run(packet(), agent)
        self.assertEqual(result["status"], "review_required")
        self.assertEqual(result["continuing_content"][0]["label"], "preserved")
        self.assertTrue(result["continuing_content"][0]["eligible"])

    def test_unsupported_or_uncertain_new_assertion_requires_review(self):
        for label in ("unsupported", "uncertain"):
            with self.subTest(label=label):
                agent = Agent()
                agent.responses["maintenance_assess_new"]["assertion_support"][0].update(label=label)
                result = run(packet(), agent)
                self.assertEqual(result["status"], "review_required")
                self.assertTrue(result["review_issues"])

    def test_uncertain_old_baseline_or_unresolved_assessment_is_not_hidden(self):
        for field in ("coverage", "assertion_support", "scope_uncertainties"):
            with self.subTest(field=field):
                agent = Agent()
                response = agent.responses["maintenance_assess_old"]
                if field == "scope_uncertainties":
                    response[field] = ["A required dependency could not be resolved."]
                else:
                    response[field][0]["label"] = "uncertain"
                result = run(packet(), agent)
                self.assertEqual(result["status"], "review_required")

    def test_source_first_scope_uncertainty_cannot_be_erased_by_full_assessments(self):
        agent = Agent()
        issue = "A required referenced unit is outside the supplied scope."
        agent.responses["maintenance_criteria"]["scope_uncertainties"] = [issue]
        result = run(packet(), agent)
        self.assertEqual(result["status"], "review_required")
        self.assertIn("source-first", result["review_issues"][0])
        for stage, payload in agent.calls:
            if "assess_" in stage:
                self.assertEqual(payload["source_scope_uncertainties"], [issue])
            if stage == "maintenance_decision":
                for key in ("criteria", "old_required", "new_required", "source_scope_uncertainties", "old_units", "new_units"):
                    self.assertNotIn(key, payload)


if __name__ == "__main__":
    unittest.main()
