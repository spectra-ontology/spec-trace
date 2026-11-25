#!/usr/bin/env python3
"""Exercise byte, query-binding, and row-score rejection on temporary copies."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True
import rescore


def rejected(action, expected):
    try:
        action()
    except rescore.VerificationError as exc:
        rescore.require(str(exc).startswith(expected + ":"), "mutation_wrong_rejection", str(exc))
        return {"expectedRejection": expected, "actualRejection": str(exc), "rejected": True}
    raise rescore.VerificationError(f"mutation_accepted: expected {expected}")


def control(study):
    baseline = rescore.verify(study)
    data = rescore.load_data(study)
    manifest = rescore.load(study / "provenance_manifest.json")
    by_packet, _ = rescore.verify_design(study, manifest, data)
    kept = set(rescore.load(study / "evidence/meeting_identity_source.json")["rules"]["keptElectronicSpellings"])
    cases = {}
    with tempfile.TemporaryDirectory(prefix="matched-domains-control-") as temporary:
        changed = Path(temporary) / "study"
        shutil.copytree(study, changed)
        with (changed / "queries/sql_A.jsonl").open("ab") as stream:
            stream.write(b"\n")
        cases["queryBytes"] = rejected(lambda: rescore.verify(changed), "source_hash")
    changed_data = copy.deepcopy(data)
    changed_data["executions"]["sql_A"][0]["query"] += " -- altered stored query"
    cases["queryExecutionBinding"] = rejected(
        lambda: rescore.verify_executions(changed_data, by_packet, kept), "executed_packet_binding")
    changed_data = copy.deepcopy(data)
    target = changed_data["executions"]["sql_A"][0]
    rescore.require(bool(target["rows"]), "mutation_fixture", "first selected rowset must be nonempty")
    target["rows"][0][0] = "deliberate mutation control value"
    cases["storedRowsVsRecomputedScore"] = rejected(
        lambda: rescore.verify_executions(changed_data, by_packet, kept), "stored_score_disagrees")
    return {"status": "pass", "baselineBindingsVerified": baseline["queryPacketGoldRowBindingsVerified"],
            "controlsRejected": len(cases), "cases": cases,
            "scope": "Byte mutation uses an isolated file copy; semantic controls use deep copies after the baseline byte check."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        result = control(args.study_dir)
    except (rescore.VerificationError, OSError, ValueError, KeyError) as exc:
        result = {"status": "fail", "error": str(exc)}
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
