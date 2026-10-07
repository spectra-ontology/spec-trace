#!/usr/bin/env python3
"""Verify a local portable audit export without model or database access.

Checks bytes, input/prompts, source spans, raw AI JSON and host diagnostics.
It does not certify question semantics, source completeness or gold truth.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

EXPECTED_AUDIT_CODE_SHA256 = "31ec881c17dd4d13aae349f76d0e7395a67bc14eece12a8af1d76ef3c0942d70"
EXPECTED_AUDIT_PROTOCOL_SHA256 = "6c888208774bd32dbe2734ca04283cfe0bcc077d10e293aad8952a1fdd098d3e"
EXPECTED_AUDIT_MANIFEST_SHA256 = "0d7a50f3eb3c1c441d3000b1c4e9fb553ffd0e8214f902b0c234ddc15f27c080"


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(root):
    root = Path(root)
    exported = read(root / "portable_export_manifest_v1.json")
    expected = {x["path"]: x["sha256"] for x in exported["files"]}
    if len(expected) != len(exported["files"]):
        raise ValueError("duplicate exported file path")
    actual = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}
    if actual != set(expected) | {"portable_export_manifest_v1.json"}:
        raise ValueError("export file allowlist differs from actual directory")
    for relative, digest in expected.items():
        target = root / relative
        if target.resolve().is_relative_to(root.resolve()) is False or sha(target) != digest:
            raise ValueError("exported path/hash mismatch")
    code = root / "semantic_alignment_audit_v1.py"
    protocol = root / "semantic_alignment_audit_protocol_v1.json"
    if (sha(code) != exported["audit_code_sha256"] or sha(protocol) != exported["audit_protocol_sha256"] or
            sha(code) != EXPECTED_AUDIT_CODE_SHA256 or sha(protocol) != EXPECTED_AUDIT_PROTOCOL_SHA256 or
            sha(root / "frozen_input_manifest.json") != EXPECTED_AUDIT_MANIFEST_SHA256):
        raise ValueError("audit code/protocol differs from exported provenance")
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("portable_fixed_semantic_audit", code)
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    _, manifest = audit.verify_preparation(root, protocol)
    closed = read(root / "semantic_alignment_audit_closed_manifest_v1.json")
    if (closed.get("closed") is not True or closed["audit_manifest_sha256"] != sha(root / "frozen_input_manifest.json") or
            closed["code_sha256"] != sha(code) or closed["protocol_sha256"] != sha(protocol)):
        raise ValueError("closed manifest belongs to different frozen input")
    closed_index = {row["call_id"]: row for row in closed["calls"]}
    export_calls = {row["call"]: row for row in exported["calls"]}
    fixed = {r + "_" + batch["id"] for batch in manifest["batches"] for r in ("A", "B")}
    if (len(fixed) != 112 or len(closed["calls"]) != 112 or len(exported["calls"]) != 112 or
            set(closed_index) != fixed or set(export_calls) != fixed):
        raise ValueError("closed/exported calls do not cover exact fixed112")
    validity = {"valid": 0, "invalid": 0}
    per_rater = {"A": {"valid": 0, "invalid": 0}, "B": {"valid": 0, "invalid": 0}}
    for batch in manifest["batches"]:
        items = read(root / "batches" / batch["id"] / "items.json")["items"]
        for rater in ("A", "B"):
            name = rater + "_" + batch["id"]
            receipt_path = root / "calls" / name / "receipt_allowlist.json"
            safe = read(receipt_path)
            pinned = export_calls[name]
            original = closed_index[name]
            if (sha(receipt_path) != pinned["allowlist_sha256"] or
                    safe["original_private_receipt_sha256"] != original["receipt_sha256"] or
                    safe["original_private_reservation_sha256"] != original["reservation_sha256"] or
                    safe["stdout_sha256"] != original["stdout_sha256"] or
                    safe["stderr_sha256"] != original["stderr_sha256"] or
                    original["rater"] != rater or original["batch_id"] != batch["id"] or
                    safe["rater"] != rater or safe["batch_id"] != batch["id"] or
                    safe["item_ids"] != batch["item_ids"] or
                    safe["prompt_sha256"] != batch["prompts"][rater]["sha256"]):
                raise ValueError("allowlisted receipt does not match closed call/source hashes")
            if original["valid_status"] not in ("VALID", "INVALID"):
                raise ValueError("closed receipt has no valid/invalid disposition")
            for key in ("original_receipt_operational_status", "closure_derived_technical_status",
                        "technical_unavailability_reasons"):
                if safe.get(key) != original.get(key):
                    raise ValueError("allowlisted operational and derived technical dispositions differ")
            if (safe.get("closure_valid_status") != original["valid_status"] or
                    safe.get("closure_error_category") != original["error_category"]):
                raise ValueError("allowlisted closure disposition differs from closed manifest")
            if original["original_receipt_operational_status"] not in ("VALID", "INVALID") or original[
                    "closure_derived_technical_status"] not in ("VALID", "INVALID"):
                raise ValueError("missing separate operational/technical closure status")
            if (original["original_receipt_operational_status"] == "VALID" and
                    "raw_output" in safe and "output" in safe and safe["raw_output"] != safe["output"]):
                raise ValueError("original successful raw/output contradiction is not waived by technical INVALID")
            state = original["valid_status"].lower()
            validity[state] += 1
            per_rater[rater][state] += len(items)
            if state == "valid":
                if (original["original_receipt_operational_status"] != "VALID" or
                        original["closure_derived_technical_status"] != "VALID"):
                    raise ValueError("semantic labels retained despite unavailable original/technical evidence")
                if original["error_category"] is not None or any(original.get(k) is None for k in
                        ("receipt_sha256", "reservation_sha256", "stdout_sha256", "stderr_sha256")):
                    raise ValueError("valid receipt has error or unavailable runtime byte anchor")
                value = audit.validate_response(safe["raw_output"], items)
                if (safe["output"] != value or safe["tool_action_n"] != 0 or safe["returncode"] != 0 or
                        safe["host_derived_original_full_contract"] != [
                            {"id": row["id"], "status": audit.derived_contract_status(row)} for row in value["items"]] or
                        safe["resolved_evidence"] != audit.resolved_evidence(value, items)):
                    raise ValueError("raw/validated AI JSON or host source diagnostic mismatch")
            elif original["error_category"] is None:
                raise ValueError("invalid receipt has no preserved error category")
    if any(sum(values.values()) != 560 for values in per_rater.values()):
        raise ValueError("invalid/missing original IDs disappeared from denominator")
    return {"status": "PASS", "export_manifest_sha256": sha(root / "portable_export_manifest_v1.json"),
            "closed_manifest_sha256": sha(root / "semantic_alignment_audit_closed_manifest_v1.json"),
            "files_verified": len(expected), "fixed_calls": 112, "call_validity": validity,
            "per_rater_complete_dispositions": per_rater,
            "model_calls": 0, "database_queries": 0, "expert_validation_n": 0,
            "private_runtime_transcript_binding_recomputed_from_export": False,
            "private_runtime_transcripts": "Not exported; fixed producer closure verifies their binding and retains byte hashes.",
            "semantic_truth_or_source_completeness_certified": False}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("export_directory")
    args = ap.parse_args()
    print(json.dumps(verify(args.export_directory), ensure_ascii=False))


if __name__ == "__main__":
    main()
