#!/usr/bin/env python3
"""
RAN5 Phase-4 CQ 15개 Cypher 검증

Reads: logs/RAN/formal/RAN5/phase-4/cq_test_dataset.json
Writes: logs/RAN/formal/RAN5/phase-4/cq_cypher_results.json

Spec: tdoc_ontology_specs(CR).md §3 CQ
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from neo4j import GraphDatabase

PROJECT_ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())

# RAN5 Neo4j (port 7691)
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7691")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

CQ_PATH = PROJECT_ROOT / "logs" / "RAN" / "formal" / "RAN5" / "phase-4" / "cq_test_dataset.json"
OUTPUT_PATH = PROJECT_ROOT / "logs" / "RAN" / "formal" / "RAN5" / "phase-4" / "cq_cypher_results.json"


def load_cq_dataset() -> tuple[dict, list[dict]]:
    with open(CQ_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["metadata"], data["questions"]


def serialize_value(val):
    if val is None:
        return None
    if isinstance(val, (int, float, str, bool)):
        return val
    if isinstance(val, list):
        return [serialize_value(v) for v in val]
    if isinstance(val, dict):
        return {k: serialize_value(v) for k, v in val.items()}
    return str(val)


def main():
    metadata, questions = load_cq_dataset()
    total = len(questions)
    print("=" * 70)
    print(f"RAN5 Phase-4 CQ Validation: {total} questions (v{metadata['version']})")
    print("=" * 70)
    print()

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    driver.verify_connectivity()

    results = []
    pass_count = 0
    no_data_count = 0
    error_count = 0

    categories = {}

    with driver.session() as session:
        for i, cq in enumerate(questions, 1):
            cq_id = cq["id"]
            category = cq["category"]
            question = cq["question"]
            query = cq["cypher"]

            try:
                result = session.run(query)
                records = list(result)

                if len(records) > 0:
                    status = "PASS"
                    pass_count += 1
                else:
                    status = "NO_DATA"
                    no_data_count += 1

                sample = None
                if records:
                    sample = serialize_value(dict(records[0]))

                entry = {
                    "id": cq_id,
                    "category": category,
                    "question": question,
                    "status": status,
                    "row_count": len(records),
                    "sample": sample,
                }

            except Exception as e:
                status = "ERROR"
                error_count += 1
                entry = {
                    "id": cq_id,
                    "category": category,
                    "question": question,
                    "status": status,
                    "error": str(e),
                }

            results.append(entry)
            categories.setdefault(category, []).append(status)

            icon = {"PASS": "✅", "NO_DATA": "⚠️", "ERROR": "❌"}.get(status, "?")
            row_info = f" ({entry.get('row_count', 0)} rows)" if 'row_count' in entry else ""
            print(f"  [{i:2d}/{total}] {icon} {cq_id}: {status}{row_info}")

    driver.close()

    # 요약
    print()
    print("=" * 70)
    print("결과 요약")
    print("=" * 70)
    print(f"  PASS: {pass_count}/{total}")
    print(f"  NO_DATA: {no_data_count}/{total}")
    print(f"  ERROR: {error_count}/{total}")
    print()

    for cat, statuses in sorted(categories.items()):
        cat_pass = statuses.count("PASS")
        print(f"  {cat}: {cat_pass}/{len(statuses)} PASS")

    # 결과 저장
    output = {
        "metadata": {
            **metadata,
            "validated_at": datetime.now().isoformat(),
            "neo4j_uri": NEO4J_URI,
        },
        "summary": {
            "total": total,
            "pass": pass_count,
            "no_data": no_data_count,
            "error": error_count,
        },
        "results": results,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n결과: {OUTPUT_PATH}")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
