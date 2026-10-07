#!/usr/bin/env python3
"""Summarize the fixed dual-AI Core560 audit without repair or new calls.

Missing/invalid receipts remain in the complete denominator. Agreement is an
AI artifact diagnostic, not truth, source completeness or expert validation.
Portable export is an exclusive new local directory, never a public commit.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def optional_sha(path):
    return sha(path) if Path(path).is_file() else None


def read(path):
    return json.loads(Path(path).read_text())


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def load_auditor(code_path):
    spec = importlib.util.spec_from_file_location("fixed_semantic_audit", code_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def column_role_signature(row):
    # A multi-column requested field remains grouped; do not infer equivalence
    # between a grouped record and separate fields merely from identical names.
    return sorted([{"returned_column_names": sorted(f["returned_column_names"]),
                    "role_code": f["role_code"]} for f in row["requested_fields"]],
                  key=canonical)


def collection_signature(row):
    return {k: value for k, value in row["contract_signature"].items()
            if k != "source_spans"}


def usage_numbers(receipt):
    totals = collections.Counter()
    events = receipt.get("usage_events", [])
    for event in events:
        usage = event.get("usage", {})
        for key, value in usage.items():
            if type(value) is int and value >= 0:
                totals[key] += value
    return {"observed_usage_event_n": len(events), "token_fields": dict(totals),
            "provider_internal_retries": receipt.get("provider_internal_retries", "not observed")}


def error_category(error):
    if error is None:
        return None
    if error in ("CLI_timeout", "CLI_nonzero_exit", "audit_RSS_budget_exceeded",
                 "tool_action_invalidates_audit"):
        return error
    if error.startswith("ValueError:"):
        return "output_schema_or_source_evidence_validation"
    if error.startswith("JSONDecodeError:"):
        return "output_JSON_parse_failure"
    if error.startswith("FileNotFoundError:"):
        return "missing_output_artifact"
    return error.split(":", 1)[0]


def verify_runtime_receipt(receipt, directory):
    unavailable = []
    texts = {}
    for field, filename in (("stdout", "stdout.jsonl"), ("stderr", "stderr.txt")):
        path = directory / filename
        texts[field] = path.read_text() if path.is_file() else None
        if field in receipt:
            if texts[field] is None:
                # The fixed runner can embed runtime text only after reading
                # its captured file. Its later disappearance is integrity loss.
                raise ValueError("preserved runtime text exists but captured file is missing")
            if texts[field] != receipt[field]:
                raise ValueError("raw stdout/stderr files differ from preserved receipt")
        else:
            unavailable.append(field + "_metadata_not_created")
            if texts[field] is None:
                unavailable.append(field + "_file_not_created")
    stdout = texts["stdout"] or ""
    events, bad_lines = [], 0
    for line in stdout.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            bad_lines += 1
    if "events" in receipt:
        if events != receipt["events"]:
            raise ValueError("parsed stdout events differ from preserved receipt")
    else:
        unavailable.append("event_metadata_not_created")
    malformed_events = sum(not isinstance(e, dict) or
                           ("item" in e and not isinstance(e["item"], dict)) for e in events)
    object_events = [e for e in events if isinstance(e, dict)]
    event_n = collections.Counter(e.get("type") for e in object_events)
    messages = [e["item"] for e in object_events if isinstance(e.get("item"), dict) and
                e["item"].get("type") == "agent_message"]
    actions = [e for e in object_events if isinstance(e.get("item"), dict) and
               e["item"].get("type") not in (None, "reasoning", "agent_message")]
    if "tool_actions" in receipt:
        if actions != receipt["tool_actions"]:
            raise ValueError("tool-action provenance differs from stdout")
    else:
        unavailable.append("tool_action_metadata_not_created")
    direct_json_equal = None
    if messages:
        try:
            value = json.loads(messages[-1]["text"])
            direct_json_equal = value == receipt.get("raw_output")
        except (json.JSONDecodeError, KeyError, TypeError):
            direct_json_equal = False
    # Invalid operation/validation is retained, never salvaged by trace checks.
    # Its original raw stdout may be truncated by the fixed timeout.
    if "raw_output" in receipt and direct_json_equal is not True:
        raise ValueError("preserved raw_output is not the final agent-message JSON")
    if (receipt.get("error") is None and "raw_output" in receipt and "output" in receipt and
            receipt["raw_output"] != receipt["output"]):
        raise ValueError("successful preserved raw AI JSON differs from validated output")
    technical_reasons = list(unavailable)
    if bad_lines:
        technical_reasons.append("malformed_stdout_lines")
    if malformed_events:
        technical_reasons.append("scalar_or_non_object_item_in_captured_events")
    for event_type in ("thread.started", "turn.started", "turn.completed"):
        if event_n[event_type] != 1:
            technical_reasons.append("captured_" + event_type + "_count_not_one")
    if not messages or direct_json_equal is not True:
        technical_reasons.append("captured_final_AI_JSON_binding_unavailable")
    if receipt.get("error") is None and actions:
        raise ValueError("original receipt claims operation success despite captured tools")
    return {"binding_availability": "UNAVAILABLE_BINDING" if unavailable else "AVAILABLE",
            "closure_derived_technical_status": "INVALID" if technical_reasons else "VALID",
            "technical_unavailability_reasons": technical_reasons,
            "unavailable_fields": unavailable,
            "stdout_file_equals_receipt": True if "stdout" in receipt else None,
            "stderr_file_equals_receipt": True if "stderr" in receipt else None,
            "parsed_events_equal_receipt": True if "events" in receipt else None, "event_counts": dict(event_n),
            "unparseable_stdout_line_n": bad_lines, "tool_action_n": len(actions),
            "final_agent_message_direct_JSON_equals_raw_output": direct_json_equal}


def collect(out, protocol_path, auditor):
    protocol, manifest = auditor.verify_preparation(out, protocol_path)
    # Close the availability gate before reading any semantic model outputs.
    # Operational monitoring is a separate labels-free task, never a partial
    # scientific summary or a way to salvage one failed batch.
    expected = [(rater, batch["id"]) for batch in manifest["batches"] for rater in ("A", "B")]
    if len(expected) != 112 or any(not (out / "calls" / (r + "_" + b) / "receipt.json").is_file()
                                  for r, b in expected):
        raise ValueError("all112 actual receipts must exist before semantic output inspection")
    items = read(out / "fixture_items.json")["items"]
    index = {item["id"]: item for item in items}
    states = {i: {} for i in index}
    calls = []
    for batch in manifest["batches"]:
        group = read(out / "batches" / batch["id"] / "items.json")["items"]
        for rater in ("A", "B"):
            rel = Path("calls") / (rater + "_" + batch["id"])
            reservation, receipt_path = out / rel / "reservation.json", out / rel / "receipt.json"
            provenance = {"call": rel.name, "rater": rater, "batch_id": batch["id"],
                          "item_ids": batch["item_ids"], "state": "not_reserved",
                          "reservation_sha256": sha(reservation) if reservation.exists() else None,
                          "receipt_path": str(rel / "receipt.json"), "receipt_sha256": None,
                          "prompt_sha256": batch["prompts"][rater]["sha256"],
                          "schema_sha256": batch["schema_sha256"], "error": None}
            rows = {}
            if receipt_path.exists():
                receipt = read(receipt_path)
                if not reservation.exists():
                    raise ValueError("closed receipt has no durable reservation")
                reserved = read(reservation)
                if (reserved.get("rater") != rater or reserved.get("batch_id") != batch["id"] or
                        reserved.get("attempt") != 1 or reserved.get("new_model_attempt") is not True or
                        len(reserved.get("cpu_affinity", [])) != 2):
                    raise ValueError("durable reservation does not match fixed one-attempt plan")
                runtime = verify_runtime_receipt(receipt, out / rel)
                provenance.update(receipt_sha256=sha(receipt_path), state="invalid",
                                  error=receipt.get("error"), error_category=error_category(receipt.get("error")),
                                  original_receipt_operational_status="VALID" if receipt.get("error") is None else "INVALID",
                                  closure_derived_technical_status=runtime["closure_derived_technical_status"],
                                  returncode=receipt.get("returncode"),
                                  elapsed_seconds=receipt.get("elapsed_seconds"),
                                  tool_action_n=len(receipt.get("tool_actions", [])),
                                  RSS_monitor=receipt.get("RSS_monitor"), usage=usage_numbers(receipt),
                                  raw_runtime_binding=runtime)
                if (receipt.get("rater") != rater or receipt.get("batch_id") != batch["id"] or
                        receipt.get("item_ids") != batch["item_ids"] or
                        receipt.get("prompt_sha256") != batch["prompts"][rater]["sha256"] or
                        receipt.get("model_requested") != protocol["model_requested"]):
                    raise ValueError("closed receipt provenance does not match fixed call")
                if receipt.get("error") is None and receipt.get("returncode") != 0:
                    raise ValueError("original receipt claims operation success despite nonzero exit")
                if receipt.get("error") is None and runtime["closure_derived_technical_status"] == "INVALID":
                    provenance.update(error="closure_derived_technical_INVALID: source evidence unavailable",
                                      error_category="source_evidence_unavailable")
                elif receipt.get("error") is None:
                    value = auditor.validate_response(receipt["output"], group)
                    if receipt.get("raw_output") != value:
                        raise ValueError("validated output differs from preserved raw model output")
                    derived = [{"id": row["id"], "status": auditor.derived_contract_status(row)}
                               for row in value["items"]]
                    if receipt.get("host_derived_original_full_contract") != derived:
                        raise ValueError("host-derived diagnostic does not match fixed rule")
                    if receipt.get("resolved_evidence") != auditor.resolved_evidence(value, group):
                        raise ValueError("resolved source evidence does not match fixed catalogue")
                    if receipt.get("tool_actions") or receipt.get("returncode") != 0:
                        raise ValueError("receipt marked valid despite operation failure")
                    rows = {row["id"]: row for row in value["items"]}
                    provenance["state"] = "valid"
            elif reservation.exists():
                provenance["state"] = "reserved_not_closed"
            calls.append(provenance)
            for i in batch["item_ids"]:
                states[i][rater] = {"state": provenance["state"], "call": rel.name,
                                    "receipt_path": provenance["receipt_path"],
                                    "receipt_sha256": provenance["receipt_sha256"],
                                    "original_receipt_operational_status": provenance.get("original_receipt_operational_status"),
                                    "closure_derived_technical_status": provenance.get("closure_derived_technical_status"),
                                    "output": rows.get(i)}
    return protocol, manifest, items, states, calls


def aggregate(items, states, calls, auditor):
    axes = ("original_question_determinacy", "reference_query_alignment",
            "original_scored_field_coverage", "native_output_support")
    totals = {r: {"state_counts": collections.Counter(),
                  "label_counts": {key: collections.Counter() for key in axes},
                  "host_full_contract_counts": collections.Counter(),
                  "blocker_item_counts": collections.Counter(),
                  "blocker_occurrence_counts": collections.Counter(),
                  "dimension_counts": {d: {k: collections.Counter() for k in
                                           ("requirement", "query_alignment", "scored_field_coverage")}
                                       for d in auditor.DIMENSIONS}}
              for r in ("A", "B")}
    comparisons = {key: collections.Counter() for key in axes +
                   ("host_full_contract", "requested_column_role_signature", "contract_signature",
                    "joint_column_role_and_contract_signature")}
    dimension_agreement = {d: {key: collections.Counter() for key in
                              ("requirement", "query_alignment", "scored_field_coverage")}
                           for d in auditor.DIMENSIONS}
    disposition = collections.Counter()
    diagnostics = []
    for item in items:
        i = item["id"]
        entry = {"id": i, "wg": item["wg"],
                 "source_field_metadata": item["source_field_metadata"],
                 "raters": {}, "pair_disposition": "not_both_valid", "agreement": None}
        for rater in ("A", "B"):
            state = states[i][rater]
            row = state["output"]
            entry["raters"][rater] = {k: v for k, v in state.items() if k != "output"}
            totals[rater]["state_counts"][state["state"]] += 1
            if row is None:
                continue
            for key in axes:
                totals[rater]["label_counts"][key][row[key]] += 1
            derived = auditor.derived_contract_status(row)
            totals[rater]["host_full_contract_counts"][derived] += 1
            totals[rater]["blocker_item_counts"].update({b["label"] for b in row["blockers"]})
            totals[rater]["blocker_occurrence_counts"].update(b["label"] for b in row["blockers"])
            for dimension in row["dimensions"]:
                for key in ("requirement", "query_alignment", "scored_field_coverage"):
                    totals[rater]["dimension_counts"][dimension["name"]][key][dimension[key]] += 1
            entry["raters"][rater].update(independent_labels={key: row[key] for key in axes},
                host_full_contract=derived, requested_column_role_signature=column_role_signature(row),
                contract_signature=collection_signature(row), blockers=row["blockers"],
                dimensions=row["dimensions"], requested_fields=row["requested_fields"],
                extra_returned_fields=row["extra_returned_fields"], conclusion=row["conclusion"],
                conclusion_evidence=row["conclusion_evidence"])
        a, b = states[i]["A"]["output"], states[i]["B"]["output"]
        if a is not None and b is not None:
            agreement = {key: a[key] == b[key] for key in axes}
            agreement["host_full_contract"] = auditor.derived_contract_status(a) == auditor.derived_contract_status(b)
            agreement["requested_column_role_signature"] = column_role_signature(a) == column_role_signature(b)
            agreement["contract_signature"] = collection_signature(a) == collection_signature(b)
            agreement["joint_column_role_and_contract_signature"] = (
                agreement["requested_column_role_signature"] and agreement["contract_signature"])
            for key, equal in agreement.items():
                comparisons[key]["agree" if equal else "disagree"] += 1
            ad, bd = ({d["name"]: d for d in row["dimensions"]} for row in (a, b))
            for d in auditor.DIMENSIONS:
                for key in ("requirement", "query_alignment", "scored_field_coverage"):
                    dimension_agreement[d][key]["agree" if ad[d][key] == bd[d][key] else "disagree"] += 1
            entry.update(pair_disposition="both_valid", agreement=agreement)
        else:
            for key in comparisons:
                comparisons[key]["not_both_valid"] += 1
            for d in auditor.DIMENSIONS:
                for key in dimension_agreement[d]:
                    dimension_agreement[d][key]["not_both_valid"] += 1
        disposition[entry["pair_disposition"]] += 1
        diagnostics.append(entry)
    n = len(items)
    for rater in totals:
        assert sum(totals[rater]["state_counts"].values()) == n
    for key in comparisons:
        assert sum(comparisons[key].values()) == n
    token_totals = collections.Counter()
    for call in calls:
        token_totals.update(call.get("usage", {}).get("token_fields", {}))
    return {"denominator_per_rater": n, "paired_denominator": n,
            "raters": totals, "pair_disposition_counts": disposition,
            "axis_and_signature_agreement_counts": comparisons,
            "dimension_agreement_counts": dimension_agreement,
            "actual_call_state_counts": collections.Counter(c["state"] for c in calls),
            "observed_token_fields_all_closed_calls": token_totals,
            "items": diagnostics, "calls": calls}


def summarize(args, auditor):
    out = Path(args.out)
    protocol, manifest, items, states, calls = collect(out, args.protocol, auditor)
    complete = len(calls) == 112 and all(c["state"] in ("valid", "invalid") for c in calls)
    if not complete:
        raise ValueError("refuse final summary before all 112 fixed calls close")
    report = {"version": 1, "kind": "Complete-denominator dual-AI original-Core560 artifact-alignment diagnostic",
              "closure": "all112_closed",
              "summary_code_sha256": sha(__file__), "audit_code_sha256": sha(args.audit_code),
              "audit_protocol_sha256": sha(args.protocol),
              "frozen_manifest_sha256": sha(out / "frozen_input_manifest.json"),
              "fixture_sha256": manifest["fixture_sha256"],
              "human_domain_expert_validation_n": 0,
              "agreement_is_semantic_certification": False,
              "native_JSON_support_is_source_completeness": False,
              "source_completeness_or_independent_truth_measured": False,
              "model_calls_or_repairs_by_summary": 0,
              "interpretation": "Matching AI labels include matching unresolved/unknown labels. Valid receipt is format/provenance validity. Neither is alignment success, source completeness or human/expert validation.",
              "missing_invalid_policy": "Every original ID remains in each rater and paired denominator; no salvage, retry, relaunch, score or question/query repair.",
              **aggregate(items, states, calls, auditor)}
    write_new(args.report, report)
    return {"report": str(args.report), "sha256": sha(args.report), "closure": report["closure"],
            "denominator_per_rater": len(items), "call_states": report["actual_call_state_counts"]}


def private_path_hits(value):
    hits = []
    def walk(x, pointer):
        if isinstance(x, dict):
            for k, v in x.items():
                walk(v, pointer + "/" + k.replace("~", "~0").replace("/", "~1"))
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, pointer + "/" + str(i))
        elif isinstance(x, str) and any(p in x for p in ("/home/", "/tmp/", "/root/", "/workspace/")):
            hits.append(pointer)
    walk(value, "")
    return hits


def close_manifest(args, auditor):
    out = Path(args.out)
    protocol, manifest, items, states, calls = collect(out, args.protocol, auditor)
    if len(calls) != 112 or any(c["state"] not in ("valid", "invalid") for c in calls):
        raise ValueError("refuse closed manifest before all112 actual receipts exist")
    pins = []
    for call in calls:
        directory = out / "calls" / call["call"]
        pins.append({"call_id": call["call"], "receipt_sha256": sha(directory / "receipt.json"),
                     "reservation_sha256": sha(directory / "reservation.json"),
                     "stdout_sha256": optional_sha(directory / "stdout.jsonl"),
                     "stderr_sha256": optional_sha(directory / "stderr.txt"), "rater": call["rater"],
                     "batch_id": call["batch_id"], "valid_status": call["state"].upper(),
                     "error_category": call.get("error_category"),
                     "original_receipt_operational_status": call["original_receipt_operational_status"],
                     "closure_derived_technical_status": call["closure_derived_technical_status"],
                     "technical_unavailability_reasons": call["raw_runtime_binding"]["technical_unavailability_reasons"],
                     "binding_availability": call["raw_runtime_binding"]["binding_availability"]})
    value = {"version": 1, "closed": True, "kind": "Actual closed fixed112 dual-AI audit receipt byte manifest",
             "audit_manifest_sha256": sha(out / "frozen_input_manifest.json"),
             "code_sha256": sha(args.audit_code), "protocol_sha256": sha(args.protocol),
             "summary_code_sha256": sha(__file__), "calls": pins,
             "planned_cli_invocations": 112, "actual_reservations": len(pins), "actual_closed_receipts": len(pins),
             "invalid_receipts_retained": True, "retries_by_wrapper": 0,
             "scientific_availability": "All112 closed and all560 per-rater dispositions retained. Invalid/missing items stay in denominators; an invalid outside a fixed analysis cohort does not suppress unrelated valid receipts. No salvage or retry.",
             "provider_internal_retries_independently_observed": False, "expert_validation_n": 0}
    write_new(args.closed_manifest, value)
    return {"closed_manifest": str(args.closed_manifest), "sha256": sha(args.closed_manifest),
            "calls": len(pins), "state_counts": collections.Counter(c["valid_status"] for c in pins)}


def export_local(args, auditor):
    """Allowlist outputs; original raw private receipts remain immutable."""
    out, target = Path(args.out), Path(args.export)
    protocol, manifest, items, states, calls = collect(out, args.protocol, auditor)
    if any(c["state"] not in ("valid", "invalid") for c in calls):
        raise ValueError("portable export requires all112 closed")
    if target.exists():
        raise FileExistsError("refuse to overwrite local portable export")
    target.mkdir(parents=True)
    for name in ("fixture_items.json", "source_pointers.json", "frozen_input_manifest.json", "root_authorization.json"):
        shutil.copyfile(out / name, target / name)
    shutil.copytree(out / "batches", target / "batches")
    shutil.copyfile(args.audit_code, target / "semantic_alignment_audit_v1.py")
    shutil.copyfile(args.protocol, target / "semantic_alignment_audit_protocol_v1.json")
    shutil.copyfile(__file__, target / Path(__file__).name)
    if args.report:
        report = read(args.report)
        if report["frozen_manifest_sha256"] != sha(out / "frozen_input_manifest.json") or report["closure"] != "all112_closed":
            raise ValueError("report does not match closed frozen audit")
        # A private runtime path in an error is not part of a model judgment.
        # Preserve its source report SHA and omit only that runtime error text.
        for call in report["calls"]:
            if private_path_hits(call.get("error")):
                call["error"] = "private runtime path omitted; original error anchored by receipt SHA"
        report["original_private_report_sha256"] = sha(args.report)
        write_new(target / "semantic_alignment_audit_report_v1.json", report)
    if args.closed_manifest:
        closed = read(args.closed_manifest)
        if closed["audit_manifest_sha256"] != sha(out / "frozen_input_manifest.json") or len(closed["calls"]) != 112:
            raise ValueError("closed manifest does not match fixed audit")
        shutil.copyfile(args.closed_manifest, target / "semantic_alignment_audit_closed_manifest_v1.json")
    call_allowlist = ("rater", "batch_id", "item_ids", "prompt_sha256", "started_unix", "finished_unix",
                      "elapsed_seconds", "model_requested", "model_returned_identity", "hidden_CLI_system_prompt",
                      "provider_internal_retries", "returncode", "raw_output", "output", "resolved_evidence",
                      "host_derived_original_full_contract", "RSS_monitor", "usage_events")
    omitted = []
    for call in calls:
        directory = out / "calls" / call["call"]
        raw = read(directory / "receipt.json")
        # Exact raw AI JSON remains identical. Runtime command/stderr/events
        # retain their SHA anchors privately; scratch/private paths are omitted.
        safe = {key: raw[key] for key in call_allowlist if key in raw}
        safe.update(error_class_or_fixed_validation_message=raw.get("error") if not private_path_hits(raw.get("error")) else
                    "private runtime path omitted; original error anchored by receipt SHA",
                    tool_action_n=len(raw.get("tool_actions", [])),
                    original_private_receipt_sha256=sha(directory / "receipt.json"),
                    original_private_reservation_sha256=sha(directory / "reservation.json"),
                    stdout_sha256=optional_sha(directory / "stdout.jsonl"), stderr_sha256=optional_sha(directory / "stderr.txt"),
                    original_receipt_operational_status=call["original_receipt_operational_status"],
                    closure_derived_technical_status=call["closure_derived_technical_status"],
                    closure_valid_status=call["state"].upper(),
                    closure_error_category=call.get("error_category"),
                    technical_unavailability_reasons=call["raw_runtime_binding"]["technical_unavailability_reasons"],
                    export_omissions=["runtime command paths", "stdout/stderr bytes", "CLI event/tool-action bodies"])
        hits = private_path_hits(safe)
        if hits:
            raise ValueError("portable allowlist contains a private path at " + canonical(hits))
        write_new(target / "calls" / call["call"] / "receipt_allowlist.json", safe)
        omitted.append({"call": call["call"], "original_receipt_sha256": safe["original_private_receipt_sha256"],
                        "allowlist_sha256": sha(target / "calls" / call["call"] / "receipt_allowlist.json")})
    # All fixture/prompt bytes are preserved. If a public original question or
    # query itself embeds a path, stop for explicit provenance review.
    audited = []
    for path in sorted(target.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix == ".json" and private_path_hits(read(path)):
            raise ValueError("private path audit failed for " + str(path.relative_to(target)))
        if path.suffix == ".txt" and private_path_hits(path.read_text()):
            raise ValueError("private path audit failed for " + str(path.relative_to(target)))
        audited.append({"path": str(path.relative_to(target)), "sha256": sha(path)})
    export_manifest = {"version": 1, "state": "local_only_not_published",
                       "audit_code_sha256": sha(args.audit_code), "audit_protocol_sha256": sha(args.protocol),
                       "frozen_input_manifest_sha256": sha(out / "frozen_input_manifest.json"),
                       "summary_code_sha256": sha(__file__), "files": audited, "calls": omitted,
                       "raw_AI_JSON_preserved": True, "private_runtime_text_exported": False,
                       "private_path_allowlist_audit": "PASS for JSON/text payloads; executable source contains only generic system path literals",
                       "expert_validation_n": 0, "agreement_is_truth_certification": False,
                       "public_commit_or_upload_performed": False}
    write_new(target / "portable_export_manifest_v1.json", export_manifest)
    return {"export": str(target), "manifest_sha256": sha(target / "portable_export_manifest_v1.json"),
            "files": len(audited), "calls": len(omitted), "publication": "local_only"}


def self_test(auditor):
    item = {"id": "SYNTHETIC", "wg": "SYNTHETIC", "source_field_metadata": {"native_support": "unknown"}}
    row = {"requested_fields": [{"returned_column_names": ["name"], "role_code": "entity_identifier"}],
           "contract_signature": {"collection_kind": "set", "nested_array_kind": "not_applicable",
                                  "order_key_columns": [], "cap_kind": "none", "cap_value": None,
                                  "tie_policy": "no_cutoff", "scope_alignment": "aligned", "source_spans": []}}
    assert column_role_signature(row) == [{"returned_column_names": ["name"], "role_code": "entity_identifier"}]
    assert "source_spans" not in collection_signature(row)
    assert private_path_hits({"a": "/home/private/source"}) == ["/a"]
    assert not private_path_hits({"a": "source_column"})
    states = {"SYNTHETIC": {"A": {"state": "invalid", "call": "A", "receipt_path": "calls/A/receipt.json",
                                   "receipt_sha256": "s", "output": None},
                            "B": {"state": "not_reserved", "call": "B", "receipt_path": "calls/B/receipt.json",
                                   "receipt_sha256": None, "output": None}}}
    summary = aggregate([item], states, [], auditor)
    assert summary["denominator_per_rater"] == 1
    assert summary["raters"]["A"]["state_counts"] == {"invalid": 1}
    assert all(c["not_both_valid"] == 1 for c in summary["axis_and_signature_agreement_counts"].values())
    original = {"id": "SYNTHETIC_1", "wg": "SYNTHETIC", "question_en": "Which entities?",
                "cypher": "MATCH (n) RETURN n.name", "gold_primary_column": "n.name"}
    contract = {"answer_type": "scalar_set", "answer_columns": ["n.name"], "ordering_required": False,
                "ordering_key": None, "cardinality": None}
    first = auditor.project_item(original, contract)
    second = auditor.project_item(dict(original, id="SYNTHETIC_2"), contract)
    a = auditor.synthetic_result(first)["items"][0]
    b = json.loads(json.dumps(a))
    b["original_scored_field_coverage"] = "partial"
    auditor.validate_response({"items": [a]}, [first])
    auditor.validate_response({"items": [b]}, [first])
    c = auditor.synthetic_result(second)["items"][0]
    def slot(output, state="valid"):
        return {"state": state, "call": "synthetic", "receipt_path": "synthetic/receipt.json",
                "receipt_sha256": "synthetic", "output": output}
    paired = aggregate([first, second], {first["id"]: {"A": slot(a), "B": slot(b)},
                       second["id"]: {"A": slot(None, "invalid"), "B": slot(c)}}, [], auditor)
    assert paired["paired_denominator"] == 2
    assert paired["pair_disposition_counts"] == {"both_valid": 1, "not_both_valid": 1}
    assert paired["axis_and_signature_agreement_counts"]["host_full_contract"] == {
        "disagree": 1, "not_both_valid": 1}
    assert paired["axis_and_signature_agreement_counts"]["contract_signature"] == {
        "agree": 1, "not_both_valid": 1}
    events = [{"type": "thread.started", "thread_id": "synthetic"}, {"type": "turn.started"},
              {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps({"items": [a]})}},
              {"type": "turn.completed", "usage": {"input_tokens": 1, "output_tokens": 1}}]
    stdout = "".join(json.dumps(e) + "\n" for e in events)
    raw = {"stdout": stdout, "stderr": "", "events": events, "tool_actions": [],
           "error": None, "raw_output": {"items": [a]}}
    with tempfile.TemporaryDirectory(prefix="synthetic_audit_runtime_") as temporary:
        directory = Path(temporary)
        (directory / "stdout.jsonl").write_text(stdout)
        (directory / "stderr.txt").write_text("")
        assert verify_runtime_receipt(raw, directory)["final_agent_message_direct_JSON_equals_raw_output"] is True
        try:
            verify_runtime_receipt(dict(raw, raw_output={"items": []}), directory)
        except ValueError:
            pass
        else:
            raise AssertionError("raw AI JSON not bound to final stdout message was accepted")
        invalid = dict(raw, error="ValueError: synthetic validation failure", stdout="tampered")
        try:
            verify_runtime_receipt(invalid, directory)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid receipt waived a present runtime-text mismatch")
        incomplete = {}
        for name, changed_events in (
                ("missing_completed_turn", events[:-1]),
                ("scalar_event", events + [1]),
                ("null_item_event", events + [{"type": "item.completed", "item": None}])):
            changed_stdout = "".join(json.dumps(event) + "\n" for event in changed_events)
            candidate = dict(raw, events=changed_events, stdout=changed_stdout)
            (directory / "stdout.jsonl").write_text(changed_stdout)
            observed = verify_runtime_receipt(candidate, directory)
            assert candidate["error"] is None
            assert observed["closure_derived_technical_status"] == "INVALID"
            assert observed["final_agent_message_direct_JSON_equals_raw_output"] is True
            incomplete[name] = observed
        changed_stdout = stdout + "synthetic malformed non-JSON line\n"
        (directory / "stdout.jsonl").write_text(changed_stdout)
        observed = verify_runtime_receipt(dict(raw, stdout=changed_stdout), directory)
        assert observed["closure_derived_technical_status"] == "INVALID"
        assert observed["unparseable_stdout_line_n"] == 1
        try:
            verify_runtime_receipt(dict(raw, stdout=changed_stdout, output={"items": []}), directory)
        except ValueError:
            pass
        else:
            raise AssertionError("technical-unavailable trace waived successful raw/output contradiction")
    with tempfile.TemporaryDirectory(prefix="synthetic_audit_setup_") as temporary:
        unavailable = verify_runtime_receipt({"error": "FileNotFoundError: synthetic setup"}, Path(temporary))
        assert unavailable["binding_availability"] == "UNAVAILABLE_BINDING"
        assert optional_sha(Path(temporary) / "stdout.jsonl") is None
    return {"status": "PASS", "tests": ["exact_column_role_signature", "evidence_does_not_change_machine_signature",
           "private_path_detection", "missing_invalid_full_denominator_retained",
           "valid_disagreement_and_host_diagnostic_preserved", "matching_unresolved_signatures_not_alignment_success",
           "stdout_stderr_events_and_single_closed_turn_bound", "altered_raw_AI_JSON_binding_rejected",
           "invalid_never_waives_existing_runtime_mismatch", "invalid_setup_genuine_missing_binding_null_hash",
           "missing_completed_turn_is_derived_technical_invalid_not_integrity_contradiction",
           "scalar_event_is_derived_technical_invalid", "null_item_event_is_derived_technical_invalid",
           "matching_capture_with_malformed_line_is_derived_technical_invalid",
           "incomplete_trace_does_not_waive_existing_raw_validated_output_mismatch"],
           "actual_model_calls": 0, "actual_source_queries": 0, "summary_code_sha256": sha(__file__)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["summarize", "close", "export", "self-test"])
    base = Path(__file__).parent
    ap.add_argument("--audit-code", default=str(base / "semantic_alignment_audit_v1.py"))
    ap.add_argument("--protocol", default=str(base / "semantic_alignment_audit_protocol_v1.json"))
    ap.add_argument("--out")
    ap.add_argument("--report")
    ap.add_argument("--export")
    ap.add_argument("--closed-manifest")
    ap.add_argument("--require-closed", action="store_true")
    args = ap.parse_args()
    auditor = load_auditor(args.audit_code)
    if args.command == "self-test":
        value = self_test(auditor)
    elif args.command == "summarize":
        if not args.out or not args.report:
            ap.error("summarize requires --out and exclusive new --report")
        value = summarize(args, auditor)
    elif args.command == "close":
        if not args.out or not args.closed_manifest:
            ap.error("close requires --out and exclusive new --closed-manifest")
        value = close_manifest(args, auditor)
    else:
        if not args.out or not args.export:
            ap.error("export requires --out and exclusive new --export")
        value = export_local(args, auditor)
    print(json.dumps(value, ensure_ascii=False))


if __name__ == "__main__":
    main()
