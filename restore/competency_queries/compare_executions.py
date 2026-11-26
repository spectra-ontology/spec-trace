#!/usr/bin/env python3
"""Compare fresh source/view CQ executions without changing either result."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys


def compare(source, restored):
    def indexed(report):
        result = {}
        for row in report["results"]:
            key = (row["working_group"], row["phase"], row["id"])
            if key in result:
                raise ValueError(f"Duplicate executed CQ: {key}")
            result[key] = row
        return result
    original, view = indexed(source), indexed(restored)
    if set(original) != set(view):
        raise ValueError("Source and restored executions have different CQ identities")
    fields = ["query_sha256", "status", "row_count", "expected_min_rows", "minimum_satisfied", "guard_defects",
              "row_multiset_sha256", "ordered_rows_sha256"]
    differences, counts = [], Counter()
    for key in sorted(original):
        for required in ("row_multiset_sha256", "ordered_rows_sha256"):
            if required not in original[key] or required not in view[key]:
                raise ValueError(f"Missing actual result fingerprint: {key}/{required}")
        changed = {field: {"source": original[key].get(field), "restored": view[key].get(field)}
                   for field in fields if original[key].get(field) != view[key].get(field)}
        if changed:
            differences.append({"working_group": key[0], "phase": key[1], "id": key[2], "differences": changed})
            counts.update(changed.keys())
    substantive = any(set(row["differences"]) - {"ordered_rows_sha256"} for row in differences)
    return {"scope": "Itemwise comparison of separately executed source and restored CQ graphs.",
            "questions_compared": len(original), "all_654_compared": len(original) == 654,
            "source_counts": source["counts"], "restored_counts": restored["counts"],
            "field_difference_counts": dict(counts), "differences": differences,
            "all_row_multisets_match": not counts["row_multiset_sha256"],
            "operational_fields_and_row_multisets_match": not substantive,
            "ordered_rows": "Ordered result digests are recorded separately; inspect query ORDER BY and ties when row orders differ."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--restored", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    source, restored = json.loads(args.source.read_text()), json.loads(args.restored.read_text())
    result = compare(source, restored)
    result["source_receipt_sha256"] = hashlib.sha256(args.source.read_bytes()).hexdigest()
    result["restored_receipt_sha256"] = hashlib.sha256(args.restored.read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "differences"}))
    return int(not result["operational_fields_and_row_multisets_match"])


if __name__ == "__main__":
    sys.exit(main())
