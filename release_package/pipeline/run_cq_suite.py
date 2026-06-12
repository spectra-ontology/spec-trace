#!/usr/bin/env python3
"""run_cq_suite.py — execute the released CQ suite (cqs/spectra_cq_v1.0/cypher/*.cypher) against Neo4j and record PASS/FAIL.

Re-executes all 137 SpectraCQ queries on a graph restored with
load_released_kg.py and compares the verdicts with the released
expectation file (validation/cq_results.json).

Usage: python3 run_cq_suite.py --bolt bolt://localhost:7697 --user neo4j \
           --password replaytest [--cypher-dir ../cqs/spectra_cq_v1.0/cypher] \
           [--expected ../validation/cq_results.json] --out results.json

Verdict: PASS = at least one result row. Zero rows or an execution error
is recorded as FAIL, as-is. Output JSON: per-CQ
{id, rows, pass, elapsed_ms, error?} + per-phase totals + a mismatch list
against --expected when provided.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import time
from pathlib import Path


def natural_key(name: str):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", name)]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    here = Path(__file__).resolve().parent
    ap.add_argument("--bolt", required=True)
    ap.add_argument("--user", default="neo4j")
    ap.add_argument("--password", required=True)
    ap.add_argument("--cypher-dir", type=Path,
                    default=here.parent / "cqs" / "spectra_cq_v1.0" / "cypher")
    ap.add_argument("--expected", type=Path,
                    default=here.parent / "validation" / "cq_results.json")
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    from neo4j import GraphDatabase

    files = sorted(args.cypher_dir.glob("*.cypher"),
                   key=lambda p: natural_key(p.stem))
    if not files:
        raise SystemExit(f"no .cypher files in {args.cypher_dir}")

    expected = {}
    if args.expected and args.expected.exists():
        exp = json.loads(args.expected.read_text())
        for r in exp.get("results", []):
            expected[r["id"]] = r.get("pass", r.get("status") == "PASS")

    drv = GraphDatabase.driver(args.bolt, auth=(args.user, args.password))
    results = []
    with drv.session() as s:
        for f in files:
            cq_id = f.stem
            query = f.read_text(encoding="utf-8")
            t0 = time.time()
            entry = {"id": cq_id, "file": f.name}
            try:
                rows = len(list(s.run(query)))
                entry["rows"] = rows
                entry["pass"] = rows > 0
            except Exception as e:  # 실행 오류도 FAIL 로 기록
                entry["rows"] = 0
                entry["pass"] = False
                entry["error"] = f"{type(e).__name__}: {e}"
            entry["elapsed_ms"] = round((time.time() - t0) * 1000, 1)
            results.append(entry)
            mark = "PASS" if entry["pass"] else "FAIL"
            print(f"  {cq_id:<14} {mark} rows={entry['rows']:<6} "
                  f"{entry['elapsed_ms']:>8.1f}ms"
                  + (f"  ERROR: {entry['error'][:80]}" if "error" in entry else ""),
                  flush=True)
    drv.close()

    by_phase: dict[str, dict] = {}
    for r in results:
        ph = r["id"].split("_")[0]
        d = by_phase.setdefault(ph, {"total": 0, "pass": 0, "fail": 0})
        d["total"] += 1
        d["pass" if r["pass"] else "fail"] += 1

    mismatches = [
        {"id": r["id"], "replay_pass": r["pass"],
         "expected_pass": expected[r["id"]]}
        for r in results
        if r["id"] in expected and bool(expected[r["id"]]) != r["pass"]]

    out = {
        "metadata": {
            "executed_at": dt.datetime.now().isoformat(timespec="seconds"),
            "bolt": args.bolt,
            "cypher_dir": str(args.cypher_dir),
            "pass_criterion": "rows >= 1 (non-empty result)",
            "source": "release package artifacts only "
                      "(kg/per_wg TTL loaded via load_released_kg.py)",
        },
        "summary": {
            "total": len(results),
            "pass": sum(1 for r in results if r["pass"]),
            "fail": sum(1 for r in results if not r["pass"]),
            "by_phase": by_phase,
            "expected_compared": len(expected),
            "mismatches_vs_expected": mismatches,
        },
        "results": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nsummary: {out['summary']['pass']}/{out['summary']['total']} PASS, "
          f"mismatches vs expected: {len(mismatches)}")
    print(f"results -> {args.out}")


if __name__ == "__main__":
    main()
