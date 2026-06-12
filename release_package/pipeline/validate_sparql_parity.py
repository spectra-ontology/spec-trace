#!/usr/bin/env python3
"""validate_sparql_parity.py — execute all 137 SpectraCQ SPARQL translations
against the released RAN1-body.ttl and compare row counts with the Neo4j
Cypher replay results (validation/cq_replay/ran1_replay_results.json).

Verifies translation fidelity (row-count parity per CQ) using released
artifacts only: the per-WG body KG, the SPARQL translations under
cqs/spectra_cq_v1.0/sparql/, and the shipped Cypher replay oracle.

Usage: python3 validate_sparql_parity.py [--ttl PATH] [--out PATH] [--timeout SECONDS]
"""
from __future__ import annotations

__version__ = "1.0.0"

import argparse
import glob
import json
import os
import signal
import time


class QueryTimeout(Exception):
    pass


def _alarm(_sig, _frm):
    raise QueryTimeout()


def main() -> None:
    ap = argparse.ArgumentParser()
    base = os.path.dirname(os.path.abspath(__file__))
    pkg = os.path.dirname(base)
    ap.add_argument("--ttl", default=os.path.join(pkg, "kg/per_wg/RAN1-body.ttl"))
    ap.add_argument("--sparql-dir", default=os.path.join(pkg, "cqs/spectra_cq_v1.0/sparql"))
    ap.add_argument("--oracle", default=os.path.join(
        pkg, "validation/cq_replay/ran1_replay_results.json"))
    ap.add_argument("--out", default=os.path.join(
        pkg, "validation/cq_replay/sparql_parity_results.json"))
    ap.add_argument("--timeout", type=int, default=600, help="per-query seconds")
    args = ap.parse_args()

    from rdflib import Graph

    t0 = time.time()
    g = Graph()
    g.parse(args.ttl, format="turtle")
    load_s = time.time() - t0
    print(f"loaded {len(g):,} triples in {load_s:.0f}s", flush=True)

    oracle = {r["id"]: r["rows"] for r in json.load(open(args.oracle))["results"]}

    signal.signal(signal.SIGALRM, _alarm)
    results = []
    for path in sorted(glob.glob(os.path.join(args.sparql_dir, "*.rq"))):
        cq_id = os.path.splitext(os.path.basename(path))[0]
        q = open(path).read()
        entry = {"id": cq_id, "cypher_rows": oracle.get(cq_id)}
        t1 = time.time()
        try:
            signal.alarm(args.timeout)
            rows = len(list(g.query(q)))
            signal.alarm(0)
            entry["sparql_rows"] = rows
            entry["match"] = (rows == oracle.get(cq_id))
            entry["non_empty"] = rows >= 1
        except QueryTimeout:
            entry["sparql_rows"] = None
            entry["match"] = False
            entry["error"] = f"timeout>{args.timeout}s"
        except Exception as e:  # noqa: BLE001
            entry["sparql_rows"] = None
            entry["match"] = False
            entry["error"] = f"{type(e).__name__}: {e}"[:200]
        entry["elapsed_s"] = round(time.time() - t1, 1)
        results.append(entry)
        print(f"{cq_id}: sparql={entry['sparql_rows']} cypher={entry['cypher_rows']} "
              f"{'OK' if entry.get('match') else 'DIFF'} ({entry['elapsed_s']}s)", flush=True)

    summary = {
        "total": len(results),
        "row_count_match": sum(1 for r in results if r.get("match")),
        "non_empty": sum(1 for r in results if r.get("non_empty")),
        "errors": [r["id"] for r in results if "error" in r],
        "mismatches": [r["id"] for r in results if not r.get("match") and "error" not in r],
        "ttl_load_seconds": round(load_s),
    }
    out = {"summary": summary, "results": results,
           "source": "released artifacts only (RAN1-body.ttl + sparql/*.rq); oracle = Neo4j replay rows"}
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(out, open(args.out, "w"), indent=1)
    print(json.dumps(summary, indent=1), flush=True)


if __name__ == "__main__":
    main()
