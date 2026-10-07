#!/usr/bin/env python3
"""Pin every completed structured receipt before uniform follow-up execution."""
import argparse
import json
from pathlib import Path

import replay_generated_read_queries as replay


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    protocol = json.loads(replay.PROTOCOL.read_text())
    replay.check_protocol(protocol)
    adapter_path = replay.BASE / "generated_read_query_replay_adapter_protocol_v1.json"
    adapter = json.loads(adapter_path.read_text())
    for name, digest in adapter["code_pins"].items():
        if replay.sha(replay.BASE / name) != digest:
            raise ValueError("fixed input adapter or execution code changed")
    expected = {item["id"]: item["wg"] for item in protocol["eligible_items"]}
    paths = sorted(args.primary_dir.glob("*.json"))
    if {path.name for path in paths} != {item_id + ".json" for item_id in expected}:
        raise ValueError("all 36 fixed-cohort completed receipt files required, with no extras")
    query_items, manifest_items = [], []
    for path in paths:
        record = json.loads(path.read_text())
        item_id = path.stem
        if record["original_id"] != item_id or record["wg"].upper() != expected[item_id]:
            raise ValueError("primary receipt identity/WG mismatch")
        if record["arm"] != "structured" or not isinstance(record["generation_abstain"], bool):
            raise ValueError("completed structured receipt and explicit abstention flag required")
        query = record["generated_query"]
        if not isinstance(query, str) and not (query is None and record["generation_abstain"]):
            raise ValueError("query must be the exact saved string or an explicit null abstention")
        if "prediction" not in record or "execution" not in record:
            raise ValueError("unfinished primary receipt")
        query_items.append({"id": item_id, "wg": expected[item_id], "query": query})
        manifest_items.append({"id": item_id, "wg": expected[item_id],
                               "receipt_basename": path.name,
                               "primary_receipt_sha256": replay.sha(path),
                               "generated_query_sha256": replay.query_sha(query),
                               "generated_query_is_null": query is None,
                               "generation_abstain": record["generation_abstain"],
                               "primary_query_identity": record["id"],
                               "variant_id": record["variant_id"],
                               "call_number": record["call_number"]})
    args.output_dir.mkdir(parents=True, exist_ok=True)
    names = ["complete_primary_structured_manifest_v1.json", "saved_generated_queries_v1.json",
             "primary_completion_attestation_v1.json"]
    if any((args.output_dir / name).exists() for name in names):
        raise ValueError("input freeze is exclusive; refusing to overwrite")
    primary = {"version": 1, "kind": "complete byte-preserved primary structured receipt manifest",
               "created_utc": replay.utc(), "expected_n": 36, "completed_n": len(manifest_items),
               "protocol_sha256": replay.sha(replay.PROTOCOL),
               "adapter_protocol_sha256": replay.sha(adapter_path),
               "receipt_directory_path_exported": False, "query_rewriting": False,
               "original_receipts_modified": False, "items": manifest_items}
    for name, payload in zip(names[:2], [primary, {"items": query_items}]):
        with (args.output_dir / name).open("x") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    completion = {"status": "complete", "expected_n": 36, "completed_n": 36,
                  "created_utc": replay.utc(),
                  "query_manifest_sha256": replay.sha(args.output_dir / names[1]),
                  "primary_artifact_sha256": replay.sha(args.output_dir / names[0]),
                  "all_primary_receipt_hashes_verified": True,
                  "model_calls_in_input_freeze": 0}
    with (args.output_dir / names[2]).open("x") as stream:
        json.dump(completion, stream, indent=2)
        stream.write("\n")
    replay.verify_primary_receipts(args.output_dir / names[0], args.primary_dir)
    replay.validate_inputs(args.output_dir / names[1], args.output_dir / names[2],
                           args.output_dir / names[0], protocol)
    print("frozen_complete_receipts", len(manifest_items))
    for name in names:
        print(name, replay.sha(args.output_dir / name))


if __name__ == "__main__":
    main()
