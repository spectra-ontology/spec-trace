#!/usr/bin/env python3
"""Measure what the rebuilt disposition records change against the stored build.

Usage: python3 scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/measure_integration_diff.py
Reads the stored Phase-2 instance files and the rebuilt files; writes counts only.
LLM calls: zero. No database access.
"""
import json
from collections import Counter
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
STORED = ROOT / "ontology/output/tsg/RAN/formal/instances/phase-2"
LOGS = ROOT / "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
FILES = {"sourceEvents": ("resolutions_document_dispositions.jsonld", "resolutionId"),
         "dispositions": ("decision_dispositions.jsonld", "dispositionId")}


def graph(path, key):
    return {row[key]: row for row in json.loads(path.read_text())["@graph"]}


def main():
    report = {}
    for wg in ("RAN1", "RAN2", "RAN3", "RAN4"):
        report[wg] = {}
        for name, (file, key) in FILES.items():
            old, new = graph(STORED / wg / file, key), graph(LOGS / "disposition_rebuild" / wg / file, key)
            added, removed = sorted(set(new) - set(old)), sorted(set(old) - set(new))
            changed = [i for i in set(old) & set(new) if old[i] != new[i]]
            entry = {"stored": len(old), "rebuilt": len(new), "added": len(added), "removed": len(removed),
                     "changed": len(changed), "removedIds": removed}
            if name == "sourceEvents":
                entry["contentChanged"] = sum(old[i].get("content") != new[i].get("content") for i in changed)
                entry["addedContentChars"] = sum(len(new[i].get("content") or "") for i in added)
            else:
                entry["removedByStatus"] = dict(Counter(old[i].get("evidenceStatus") for i in removed))
            report[wg][name] = entry
            print(wg, name, {k: v for k, v in entry.items() if k != "removedIds"}, flush=True)
    out = LOGS / "integration/integration_diff.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    main()
