#!/usr/bin/env python3
"""validate_example_queries.py — run the bundled example SPARQL queries against the released RAN1 TTL.

Executes every query under queries/sparql/ on the released per-WG body KG
(kg/per_wg/RAN1-body.ttl by default) with a per-query timeout, and records
row counts to a JSON report. Used to keep the representative examples
execution-validated against the released data.

사용: cd release_package/pipeline && python3 validate_example_queries.py
      [--ttl PATH] [--out PATH] [--timeout SECONDS]
LLM 호출: 없음
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import rdflib

PKG = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ttl", default=str(PKG / "kg" / "per_wg" / "RAN1-body.ttl"),
                    help="released body-text TTL to query (default: kg/per_wg/RAN1-body.ttl)")
    ap.add_argument("--queries", default=str(PKG / "queries" / "sparql"),
                    help="directory of .rq files (default: queries/sparql)")
    ap.add_argument("--out", default=str(PKG / "validation" / "example_queries_results.json"),
                    help="JSON report path (default: validation/example_queries_results.json)")
    ap.add_argument("--timeout", type=int, default=600, help="per-query seconds (default: 600)")
    args = ap.parse_args()

    ttl = Path(args.ttl)
    if not ttl.exists():
        raise SystemExit(f"TTL not found: {ttl}")
    print(f"[load] {ttl}", flush=True)
    t0 = time.time()
    g = rdflib.Graph()
    g.parse(ttl, format="turtle")
    print(f"[load] {len(g)} triples in {time.time()-t0:.0f}s", flush=True)

    def run_one(text: str, q: mp.Queue) -> None:
        try:
            rows = list(g.query(text))
            q.put({"rows": len(rows), "error": None,
                   "sample": str(rows[0]) if rows else None})
        except Exception as e:  # noqa: BLE001 — record every per-query failure
            q.put({"rows": None, "error": f"{type(e).__name__}: {e}", "sample": None})

    results = []
    for rq in sorted(Path(args.queries).glob("*.rq")):
        text = rq.read_text(encoding="utf-8")
        t1 = time.time()
        q: mp.Queue = mp.Queue()
        # fork shares the loaded graph copy-on-write — per-query timeout
        # isolation without reloading the TTL for every query
        p = mp.get_context("fork").Process(target=run_one, args=(text, q))
        p.start()
        p.join(args.timeout)
        if p.is_alive():
            p.terminate()
            p.join()
            res = {"rows": None, "error": f"timeout>{args.timeout}s", "sample": None}
        else:
            res = q.get() if not q.empty() else {"rows": None, "error": "no result returned", "sample": None}
        res.update({"query": rq.name, "elapsed_s": round(time.time() - t1, 1)})
        results.append(res)
        print(f"[run] {rq.name}: rows={res['rows']} error={res['error']} ({res['elapsed_s']:.0f}s)", flush=True)

    summary = {
        "ttl": str(ttl),
        "triples": len(g),
        "total_queries": len(results),
        "zero_row": [r["query"] for r in results if r["rows"] == 0],
        "errors": [r["query"] for r in results if r["error"]],
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"summary": summary, "results": results}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    sys.exit(main())
