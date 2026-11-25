"""Source-grounded condition review and bounded follow-up for local agent workflows.

``run(request, call)`` delegates semantic work to an approved caller. This module
validates structure, binds evidence to versioned text, and constructs reader
inputs. It performs no I/O, model selection, retries, or database access.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json


CONVEYANCE = {"full", "partial", "absent", "uncertain"}
KINDS = {"condition", "qualification", "role", "authority"}


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _string(value, name, empty=False):
    _require(isinstance(value, str) and (empty or bool(value.strip())), name + " must be a string")
    return value


def _ids(value, name):
    _require(isinstance(value, list), name + " must be a list")
    for entry in value:
        _string(entry, name + " entry")
    _require(len(value) == len(set(value)), name + " has duplicate IDs")
    return value


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _request(request):
    _require(isinstance(request, dict), "request must be an object")
    question = _string(request.get("question"), "question")
    initial = _string(request.get("initial_answer"), "initial_answer", empty=True)
    budget = request.get("added_unicode_character_budget")
    _require(type(budget) is int and budget >= 0, "added_unicode_character_budget must be a nonnegative integer")
    raw = request.get("source_units")
    _require(isinstance(raw, list) and bool(raw), "source_units must be a nonempty list")
    sources = []
    for unit in raw:
        _require(isinstance(unit, dict), "source unit must be an object")
        sources.append({key: _string(unit.get(key), "source unit " + key,
                                    empty=key in {"text", "native_text"})
                        for key in ("unit_id", "document_id", "version", "locator", "native_text", "text")})
    all_ids = [u["unit_id"] for u in sources]
    _require(len(all_ids) == len(set(all_ids)), "source_units has duplicate IDs")
    supplied = _ids(request.get("initial_unit_ids"), "initial_unit_ids")
    _require(set(supplied) <= set(all_ids), "initial_unit_ids contains unknown IDs")
    return question, initial, budget, sources, list(supplied)


def validate_request(request: dict) -> dict:
    """Validate without dispatching; return an isolated allowlisted request.

    ``native_text`` is the upstream source text; ``text`` is the actual reader
    projection, and may differ. Their comparison is retained as literal
    provenance rather than treated as semantic support or answer correctness.
    """
    question, initial, budget, sources, supplied = _request(request)
    return {"question": question, "initial_answer": initial, "source_units": sources,
            "initial_unit_ids": supplied, "added_unicode_character_budget": budget}


def _conditions(response, units):
    rows = response.get("conditions")
    _require(isinstance(rows, list), "conditions must be a list")
    result = []
    for row in rows:
        _require(isinstance(row, dict), "condition must be an object")
        item = {"condition_id": _string(row.get("condition_id"), "condition_id"),
                "kind": row.get("kind"), "text": _string(row.get("text"), "condition text")}
        _require(item["kind"] in KINDS, "unknown condition kind")
        evidence = row.get("evidence")
        _require(isinstance(evidence, list) and bool(evidence), "condition evidence must be nonempty")
        item["evidence"] = []
        for span in evidence:
            _require(isinstance(span, dict), "evidence must be an object")
            uid = _string(span.get("unit_id"), "evidence unit_id")
            quote = _string(span.get("quote"), "evidence quote")
            _require(uid in units, "evidence names unknown source unit")
            _require(quote in units[uid]["native_text"], "evidence quote absent from native text")
            item["evidence"].append({"unit_id": uid, "quote": quote})
        for key in ("speaker", "authority"):
            if key in row:
                item[key] = _string(row[key], key, empty=True)
        result.append(item)
    _ids([r["condition_id"] for r in result], "condition IDs")
    return result


def _rows(response, expected, stage):
    rows = response.get("conditions")
    _require(isinstance(rows, list), stage + " conditions must be a list")
    _require(all(isinstance(r, dict) for r in rows), stage + " condition must be an object")
    ids = _ids([r.get("condition_id") for r in rows], stage + " condition IDs")
    _require(set(ids) == set(expected), stage + " must assess exactly the fixed condition set")
    return {r["condition_id"]: r for r in rows}


def _support(response, conditions):
    rows = _rows(response, [r["condition_id"] for r in conditions], "support")
    result = {}
    for cid, row in rows.items():
        _require("supported" in row and "relevant" in row,
                 "support and relevance must be explicitly supplied")
        _require(all(value is None or type(value) is bool
                     for value in (row["supported"], row["relevant"])),
                 "support and relevance must be true, false or null")
        result[cid] = {"supported": row["supported"], "relevant": row["relevant"]}
    return result


def _assessment(response, eligible, answer):
    rows = _rows(response, eligible, "assessment")
    labels, reviews = {}, {}
    for cid, row in rows.items():
        _require(row.get("conveyance") in CONVEYANCE, "unknown conveyance label")
        labels[cid] = row["conveyance"]
        reason = _string(row.get("reason"), "assessment reason")
        quote = _string(row.get("answer_quote", ""), "assessment answer_quote", empty=True)
        _require(not quote or quote in answer, "assessment answer_quote absent from answer")
        if labels[cid] in {"full", "partial"}:
            _require(bool(quote.strip()), "full or partial conveyance requires a nonempty answer_quote")
        reviews[cid] = {"conveyance": labels[cid], "reason": reason, "answer_quote": quote}
    _require(type(response.get("whole_answer_supported")) is bool,
             "whole_answer_supported must be boolean")
    full = sum(value == "full" for value in labels.values())
    return {"conditions": labels, "condition_reviews": reviews,
            "whole_answer_supported": response["whole_answer_supported"],
            "fully_conveyed": full, "eligible_count": len(eligible),
            "coverage": full / len(eligible) if eligible else None,
            "complete": full == len(eligible) if eligible else None}


def _diagnosis(response, units, supplied, budget):
    _require(set(response) <= {"action", "unit_ids", "reason", "_receipt"},
             "diagnosis has unknown fields")
    action = response.get("action")
    _require(isinstance(action, str) and action in {"Stop", "Uncertain", "Ask", "Acquire"},
             "invalid diagnosis action")
    chosen = _ids(response.get("unit_ids"), "diagnosis unit_ids")
    _require(set(chosen) <= set(units), "diagnosis contains unknown IDs")
    if "reason" in response:
        _string(response["reason"], "diagnosis reason", empty=True)
    if action in {"Stop", "Uncertain"}:
        _require(not chosen, "no-call action must select no units")
    elif action == "Ask":
        _require(bool(chosen) and set(chosen) <= set(supplied), "Ask must select supplied units")
    else:
        _require(bool(chosen) and set(chosen) <= set(units) - set(supplied),
                 "Acquire must select previously unsupplied units")
        _require(sum(len(units[uid]["text"]) for uid in chosen) <= budget,
                 "Acquire exceeds whole-unit Unicode character budget")
    return action, chosen


def _source_view(sources, native=False):
    return [{"unit_id": u["unit_id"], "document_id": u["document_id"],
             "version": u["version"], "locator": u["locator"],
             "text": u["native_text"] if native else u["text"]} for u in sources]


def _locations(conditions, units, supplied, labels):
    result = []
    for condition in conditions:
        cid = condition["condition_id"]
        spans = []
        for evidence in condition["evidence"]:
            uid, quote = evidence["unit_id"], evidence["quote"]
            unit = units[uid]
            projected = quote in unit["text"]
            delivered = projected and uid in supplied
            if not projected:
                location = "projection_review"
            elif not delivered:
                location = "acquisition_candidate"
            elif labels.get(cid) != "full":
                location = "reread_candidate"
            else:
                location = "conveyed"
            spans.append({**evidence, "document_id": unit["document_id"],
                          "version": unit["version"], "locator": unit["locator"],
                          "native_present": True, "projected_present": projected,
                          "reader_input_present": delivered, "review_location": location})
        result.append({"condition_id": cid, "evidence": spans})
    return result


def run(request: dict, call) -> dict:
    """Run one diagnostic follow-up; invalid responses never trigger a fallback.

    Input requires question, initial_answer, ordered source_units (unit_id,
    document_id, version, locator, native_text, text), initial_unit_ids, and an
    explicit added_unicode_character_budget. ``text`` is the reader projection;
    ``native_text`` is its upstream source. Metadata is supplied by retrieval.
    Semantic callbacks return structured decisions; literal validation establishes
    exact source location, independently of those semantic decisions. The caller
    owns durable physical dispatch/cost receipts, including initial-answer cost.
    """
    normalized = validate_request(request)
    question, initial = normalized["question"], normalized["initial_answer"]
    budget, sources = normalized["added_unicode_character_budget"], normalized["source_units"]
    supplied = normalized["initial_unit_ids"]
    _require(callable(call), "call must be callable")
    units = {u["unit_id"]: u for u in sources}
    initial_sources = [units[uid] for uid in supplied]
    result = {"schema": "spectra_condition_recovery_v1", "status": "running",
              "initial_answer": initial, "final_answer": initial, "action": None,
              "conditions": [], "eligible_condition_ids": [], "assessments": {},
              "unresolved_condition_ids": [],
              "transitions": [], "dispatches": [], "controller_call_count": 0,
              "initial_input": {"unit_ids": supplied, "sources": _source_view(initial_sources)},
              "source_pool_sha256": _digest(sources),
              "initial_answer_sha256": hashlib.sha256(initial.encode()).hexdigest(),
              "added_unicode_character_budget": budget,
              "accounting": "Caller combines initial, diagnostic and reader physical receipts; evaluation stages are separate."}
    native = _source_view(sources, native=True)
    projected = _source_view(sources)

    def invoke(stage, payload):
        # Keep immutable evidence of what was dispatched before handing an isolated
        # copy to callers that may mutate their own transport payload.
        result["dispatches"].append({"stage": stage, "payload": deepcopy(payload),
                                     "payload_sha256": _digest(payload)})
        result["controller_call_count"] += 1
        response = call(stage, deepcopy(payload))
        _require(isinstance(response, dict), stage + " response must be an object")
        if "_receipt" in response:
            result["dispatches"][-1]["receipt"] = deepcopy(response["_receipt"])
        return response

    stage = "conditions"
    try:
        conditions = _conditions(invoke("recovery_conditions", {
            "question": question, "sources": native,
            "contract": "Extract source-grounded conditions, qualifications, record roles and authority independently. Preserve version, speaker and scope. Return conditions with condition_id, kind (condition/qualification/role/authority), text, and evidence [{unit_id, quote}] using exact native quotes; speaker/authority optional."}), units)
        result["conditions"] = conditions
        stage = "support"
        support = _support(invoke("recovery_support", {
            "question": question, "sources": native, "conditions": conditions,
            "contract": "Judge each condition's source support and question relevance independently of an answer. Return conditions [{condition_id,supported:true|false|null,relevant:true|false|null}]. Use null for unresolved support or relevance; preserve the distinction from false. Record identity or a proposal alone does not establish adoption."}), conditions)
        result["support"] = support
        result["unresolved_condition_ids"] = [c["condition_id"] for c in conditions
                                              if any(v is None for v in support[c["condition_id"]].values())]
        eligible = [c["condition_id"] for c in conditions
                    if support[c["condition_id"]]["supported"] and support[c["condition_id"]]["relevant"]]
        result["eligible_condition_ids"] = eligible
        eligible_conditions = [c for c in conditions if c["condition_id"] in eligible]
        result["eligible_set_sha256"] = _digest(eligible_conditions)

        def assess(answer, ids, phase):
            return _assessment(invoke("recovery_assessment", {
                "question": question, "phase": phase, "answer": answer,
                "sources": native, "reader_sources": _source_view([units[uid] for uid in ids]),
                "conditions": eligible_conditions,
                "contract": "Assess each fixed condition in the whole answer semantically as full, partial, absent or uncertain; also assess whole-answer support. Return conditions [{condition_id,conveyance,reason,answer_quote}] and whole_answer_supported:bool. Give a source-grounded reason for each judgment. Full or partial requires a nonempty literal answer_quote occurring in this exact answer; absent/uncertain may use an empty quote. Preserve condition IDs; do not regenerate eligibility."}), eligible, answer)

        stage = "initial_assessment"
        first = assess(initial, supplied, "initial")
        result["assessments"]["initial"] = first
        result["provenance"] = _locations(eligible_conditions, units, supplied, first["conditions"])
        stage = "diagnosis"
        diagnosis = invoke("recovery_diagnosis", {
            "question": question, "sources": projected, "native_sources": native,
            "initial_unit_ids": supplied, "initial_answer": initial,
            "added_unicode_character_budget": budget,
            "contract": "Independently diagnose the question, source pool, actual initial input and initial answer. Check conditions, qualification, scope, source version and authority from these sources. Return only action, unit_ids, optional reason. Stop/Uncertain select []; Ask selects nonempty supplied IDs; Acquire selects nonempty unsupplied IDs within the whole-unit text budget. Projection loss requires source projection review."})
        action, chosen = _diagnosis(diagnosis, units, supplied, budget)
        result["action"] = action
        result["diagnosis"] = {k: deepcopy(v) for k, v in diagnosis.items() if k != "_receipt"}
        final_ids = list(supplied)
        if action == "Acquire":
            final_ids += chosen
        result["added_unicode_characters"] = sum(len(units[uid]["text"]) for uid in chosen) if action == "Acquire" else 0
        if action in {"Ask", "Acquire"}:
            stage = "reader"
            # Deliberately omit conditions, judgments, diagnosis, native-only text,
            # and all unselected source units from this allowlisted reader input.
            reader_input = {"question": question, "initial_answer": initial,
                            "sources": _source_view([units[uid] for uid in final_ids]),
                            "attention_unit_ids": chosen,
                            "contract": "Read these actual sources, attending to the selected units. Return {answer: string}. Preserve source scope, version, conditions and authority."}
            result["reader_input"] = deepcopy(reader_input)
            answer = invoke("recovery_reader", reader_input)
            result["final_answer"] = _string(answer.get("answer"), "reader answer", empty=True)
            stage = "final_assessment"
            final = assess(result["final_answer"], final_ids, "final")
        else:
            # Same exact answer and same fixed eligible set: reuse the assessment.
            final = deepcopy(first)
        result["final_unit_ids"] = final_ids
        result["assessments"]["final"] = final
        result["transitions"] = [{"condition_id": cid,
                                   "initial": first["conditions"][cid],
                                   "final": final["conditions"][cid]} for cid in eligible]
        result["final_provenance"] = _locations(eligible_conditions, units, final_ids, final["conditions"])
        result["status"] = "completed"
    except (ValueError, TypeError, KeyError) as error:
        result["status"] = "invalid_" + stage
        result["error"] = str(error)
    result["final_answer_sha256"] = hashlib.sha256(result["final_answer"].encode()).hexdigest()
    return result
