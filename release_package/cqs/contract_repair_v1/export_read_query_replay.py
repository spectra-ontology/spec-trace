#!/usr/bin/env python3
"""Export completed replay files and allowlisted preservation provenance.

Copies the already completed artifacts byte for byte. Does not rerun queries,
compute correctness, modify primary receipts, or disclose local connection data.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

import replay_generated_read_queries as replay

FILES = ["complete_primary_structured_manifest_v1.json", "saved_generated_queries_v1.json",
         "primary_completion_attestation_v1.json", "generated_read_query_replay_results_v1.json"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay-dir", required=True, type=Path)
    parser.add_argument("--primary-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    protocol = json.loads(replay.PROTOCOL.read_text())
    replay.check_protocol(protocol)
    primary_path = args.replay_dir / FILES[0]
    receipts = replay.verify_primary_receipts(primary_path, args.primary_dir)
    queries = replay.validate_inputs(args.replay_dir / FILES[1], args.replay_dir / FILES[2],
                                     primary_path, protocol)
    result_path = args.replay_dir / FILES[3]
    result = json.loads(result_path.read_text())
    if len(result["items"]) != 36 or result["source_guards_before"] != result["source_guards_after"]:
        raise ValueError("incomplete replay or source guard mismatch")
    observed = {item["id"]: item for item in result["items"]}
    if len(observed) != 36 or set(observed) != set(receipts):
        raise ValueError("replay cohort differs from all-36 primary receipt cohort")
    comparisons = []
    for query in queries:
        item_id = query["id"]
        item, receipt = observed[item_id], receipts[item_id]
        execution = item["execution"]
        if (item["query"] != query["query"] or execution["query_sha256"] != replay.query_sha(query["query"])
                or item["primary_receipt_sha256"] != receipt["primary_receipt_sha256"]
                or item["generation_abstain"] != receipt["generation_abstain"]):
            raise ValueError("replay changed primary query or abstention identity")
        if execution["status"] == "OK" and (execution["plan_query_type"] != "r"
                                              or execution["execution_query_type"] != "r"
                                              or execution["rollback_requested"] is not True):
            raise ValueError("successful replay did not record both read-only gates and rollback")
        old = json.loads((args.primary_dir / receipt["receipt_basename"]).read_text())
        old_execution = old.get("execution") or {}
        comparisons.append({"id": item_id, "wg": query["wg"],
                            "primary_receipt_sha256": receipt["primary_receipt_sha256"],
                            "saved_query_sha256": receipt["generated_query_sha256"],
                            "replay_query_sha256": execution["query_sha256"],
                            "query_unchanged": True, "generation_abstain": receipt["generation_abstain"],
                            "primary_execution_status": old_execution.get("status"),
                            "primary_error_class": old_execution.get("error_class"),
                            "replay_execution_status": execution["status"],
                            "replay_plan_query_type": execution.get("plan_query_type"),
                            "replay_execution_query_type": execution.get("execution_query_type")})
    names = FILES + ["generated_read_query_replay_provenance_v1.json"]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if any((args.output_dir / name).exists() for name in names):
        raise ValueError("refusing to overwrite any public export")
    for name in FILES:
        with (args.output_dir / name).open("xb") as stream:
            stream.write((args.replay_dir / name).read_bytes())
    replay.verify_primary_receipts(primary_path, args.primary_dir)
    provenance = {"version": 1, "kind": "allowlisted full-cohort execution-repair provenance, not correctness scores",
                  "created_utc": replay.utc(), "all_primary_receipts_unchanged": True,
                  "all_saved_query_strings_unchanged": True, "all_36_items_accounted": True,
                  "source_guards_unchanged": True, "source_pins": protocol["input_pins"],
                  "protocol_sha256": replay.sha(replay.PROTOCOL),
                  "adapter_protocol_sha256": replay.sha(replay.BASE / "generated_read_query_replay_adapter_protocol_v1.json"),
                  "synthetic_validation_sha256": result["synthetic_validation_sha256"],
                  "exporter_sha256": replay.sha(__file__),
                  "exported_files": {name: replay.sha(args.output_dir / name) for name in FILES},
                  "replay_execution_dispositions": dict(Counter(item["execution"]["status"] for item in result["items"])),
                  "primary_comparison": comparisons, "model_calls": 0,
                  "correctness_scores_computed_by_replay_or_exporter": 0,
                  "human_expert_validation_n": 0, "original_benchmark_modified": False,
                  "interpretation": "Anonymous read subqueries accepted under a uniform lexical and EXPLAIN-r guard; successful execution does not certify answer correctness or domain semantics; primary experiment retained separately",
                  "connection_environment_credentials_or_local_paths_exported": False,
                  "same_count_external_property_mutations_detected": False,
                  "official_documentation": protocol["official_documentation"]}
    with (args.output_dir / names[-1]).open("x") as stream:
        json.dump(provenance, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print("all_36_query_and_receipt_hashes_unchanged", True)
    print("operational_dispositions", provenance["replay_execution_dispositions"])
    print("provenance_sha256", replay.sha(args.output_dir / names[-1]))


if __name__ == "__main__":
    main()
