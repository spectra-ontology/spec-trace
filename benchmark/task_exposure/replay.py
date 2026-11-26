#!/usr/bin/env python3
"""Check the archived main-task exposure inventory without model calls."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(row):
    return sha(json.dumps({"question": row["question"], "fields": row["fields"]},
                          ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())


def check(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    release = args.release.resolve()
    audit = json.loads((release / "benchmark/task_exposure/audit.json").read_text())
    items = []
    for name in ("core", "ran5"):
        path = release / f"benchmark/items_final/gate/{name}/chain_items_admitted.jsonl"
        items.extend(json.loads(line) for line in path.read_text().splitlines() if line.strip())
    by_fingerprint = {fingerprint(row): row for row in items}
    check(len(items) == len(by_fingerprint) == 667, "canonical question inventory differs")
    counts = {}
    for condition, inventory in audit["conditions"].items():
        seen = set()
        for entry in inventory["files"]:
            path = release / entry["path"]
            check(sha(path.read_bytes()) == entry["sha256"], f"packet bytes differ: {path}")
            packet = json.loads(path.read_text())
            check(packet["task"] == entry["task"] and sha(packet["task"].encode()) == entry["taskSha256"], "task differs")
            mappings = []
            for item in packet["items"]:
                key = fingerprint(item)
                canonical = by_fingerprint.get(key)
                check(canonical is not None, "unmatched archived question")
                seen.add(canonical["id"])
                mappings.append({"historicalId": item["id"], "canonicalId": canonical["id"],
                                 "family": canonical["family"], "questionFieldsSha256": key})
            check(mappings == entry["questionMap"], "question/field mapping differs")
        check(len(seen) == inventory["canonicalItemsMatched"] == 667, "condition coverage differs")
        counts[condition] = {"packetFiles": len(inventory["files"]), "admittedItems": len(seen)}
    for entry in audit["writerPrompts"]:
        check(sha((release / entry["path"]).read_bytes()) == entry["sha256"], "writer prompt bytes differ")
    result = {"status": "PASS", "conditions": counts, "writerPromptFiles": len(audit["writerPrompts"]),
              "auditSha256": sha((release / "benchmark/task_exposure/audit.json").read_bytes()),
              "historicalInputsChanged": False}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
