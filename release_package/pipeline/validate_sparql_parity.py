#!/usr/bin/env python3
"""validate_sparql_parity.py — execute every shipped SpectraCQ SPARQL
translation against the released RAN1-body.ttl and compare row counts with the Neo4j
Cypher replay results (validation/cq_replay/ran1_replay_results.json).

Verifies translation fidelity using released artifacts only: the per-WG body
KG, the SPARQL translations under cqs/spectra_cq_v2.0/sparql/, and the shipped
Cypher replay oracle.

Two levels of evidence are recorded per CQ:

  * row-count parity (`match`): the SPARQL result cardinality equals the Cypher
    reference cardinality.

  * parity class (`parity_class`): whether that cardinality match reflects the
    full result set or a shared LIMIT. A CQ whose query carries `LIMIT N` and
    whose reference cardinality is exactly N can match trivially: both engines
    truncate a larger result to N rows, so N == N regardless of which N rows
    each returns. To separate these, every LIMIT query is re-executed with its
    trailing `LIMIT` removed; the unbounded cardinality is compared with the
    reference:
      - `exact_cardinality` — no LIMIT, or LIMIT non-binding (unbounded ==
        reference). The count is the true result-set cardinality.
      - `limit_bound_topn` — LIMIT binding (unbounded > reference). The count
        match is guaranteed by the shared LIMIT and evidences cardinality only,
        not that the same rows are returned. Closing this to value-level
        equivalence is tracked as future work (a cross-engine result-set
        harness loading the released TTL into both rdflib and Neo4j).

Usage: python3 validate_sparql_parity.py [--ttl PATH] [--out PATH]
       [--timeout SECONDS] [--no-classify]
"""
from __future__ import annotations

__version__ = "1.1.0"

import argparse
import glob
import json
import os
import re
import signal
import time


class QueryTimeout(Exception):
    pass


def _alarm(_sig, _frm):
    raise QueryTimeout()


_LIMIT_TAIL = re.compile(r"\s*LIMIT\s+\d+\s*$", re.IGNORECASE)


def _strip_trailing_limit(query: str) -> tuple[str, int | None]:
    """Return (query_without_trailing_limit, limit_value_or_None)."""
    m = re.search(r"LIMIT\s+(\d+)\s*$", query, re.IGNORECASE)
    if not m:
        return query, None
    return _LIMIT_TAIL.sub("\n", query), int(m.group(1))


def main() -> None:
    ap = argparse.ArgumentParser()
    base = os.path.dirname(os.path.abspath(__file__))
    pkg = os.path.dirname(base)
    ap.add_argument("--ttl", default=os.path.join(pkg, "kg/per_wg/RAN1-body.ttl"))
    ap.add_argument("--sparql-dir", default=os.path.join(pkg, "cqs/spectra_cq_v2.0/sparql"))
    ap.add_argument("--oracle", default=os.path.join(
        pkg, "validation/cq_replay/ran1_replay_results.json"))
    ap.add_argument("--out", default=os.path.join(
        pkg, "validation/cq_replay/sparql_parity_results.json"))
    ap.add_argument("--timeout", type=int, default=600, help="per-query seconds")
    ap.add_argument("--no-classify", action="store_true",
                    help="skip the unbounded re-run that classifies LIMIT queries")
    args = ap.parse_args()

    from rdflib import Graph

    t0 = time.time()
    g = Graph()
    g.parse(args.ttl, format="turtle")
    load_s = time.time() - t0
    print(f"loaded {len(g):,} triples in {load_s:.0f}s", flush=True)

    # Oracle = the Cypher reference cardinality reproduced on the current graph.
    # replay_released_cqs.py records it as got_rc (== gold_rc when the CQ passed);
    # the legacy replay format used a flat "rows" field. Accept either.
    # The SPARQL translations are named without a WG prefix (P1_CQ1-1.rq) while the
    # replay oracle keys carry it (RAN1_P1_CQ1-1); index by both so the join holds.
    oracle = {}
    for r in json.load(open(args.oracle))["results"]:
        rc = r.get("got_rc") if r.get("got_rc") is not None else r.get("rows")
        oracle[r["id"]] = rc
        oracle[re.sub(r"^RAN\d+_", "", r["id"])] = rc

    signal.signal(signal.SIGALRM, _alarm)
    results = []
    for path in sorted(glob.glob(os.path.join(args.sparql_dir, "*.rq"))):
        cq_id = os.path.splitext(os.path.basename(path))[0]
        q = open(path).read()
        ref = oracle.get(cq_id)
        entry = {"id": cq_id, "cypher_rows": ref}
        t1 = time.time()
        try:
            signal.alarm(args.timeout)
            rows = len(list(g.query(q)))
            signal.alarm(0)
            entry["sparql_rows"] = rows
            entry["match"] = (rows == ref)
            entry["non_empty"] = rows >= 1
        except QueryTimeout:
            entry["sparql_rows"] = None
            entry["match"] = False
            entry["error"] = f"timeout>{args.timeout}s"
        except Exception as e:  # noqa: BLE001
            entry["sparql_rows"] = None
            entry["match"] = False
            entry["error"] = f"{type(e).__name__}: {e}"[:200]

        # Classify the parity: is the count the true cardinality, or LIMIT-bound?
        q_nolimit, limit_val = _strip_trailing_limit(q)
        if limit_val is None:
            entry["limit"] = None
            entry["unbounded_rows"] = entry.get("sparql_rows")
            entry["parity_class"] = "exact_cardinality" if entry.get("match") else None
        else:
            entry["limit"] = limit_val
            if args.no_classify or "error" in entry:
                entry["unbounded_rows"] = None
                entry["parity_class"] = "unclassified"
            else:
                try:
                    signal.alarm(args.timeout)
                    ub = len(list(g.query(q_nolimit)))
                    signal.alarm(0)
                    entry["unbounded_rows"] = ub
                    if not entry.get("match"):
                        entry["parity_class"] = None
                    elif ub == ref:
                        entry["parity_class"] = "exact_cardinality"
                    else:  # ub > ref: the LIMIT truncates a larger result set
                        entry["parity_class"] = "limit_bound_topn"
                except (QueryTimeout, Exception):  # noqa: BLE001
                    entry["unbounded_rows"] = None
                    entry["parity_class"] = "unclassified"

        entry["elapsed_s"] = round(time.time() - t1, 1)
        results.append(entry)
        pc = entry.get("parity_class") or "-"
        print(f"{cq_id}: sparql={entry['sparql_rows']} cypher={entry['cypher_rows']} "
              f"{'OK' if entry.get('match') else 'DIFF'} [{pc}] ({entry['elapsed_s']}s)",
              flush=True)

    matched = [r for r in results if r.get("match")]
    summary = {
        "total": len(results),
        "row_count_match": len(matched),
        "non_empty": sum(1 for r in results if r.get("non_empty")),
        "exact_cardinality": sum(1 for r in matched if r.get("parity_class") == "exact_cardinality"),
        "limit_bound_topn": sum(1 for r in matched if r.get("parity_class") == "limit_bound_topn"),
        "unclassified": sum(1 for r in matched if r.get("parity_class") == "unclassified"),
        "errors": [r["id"] for r in results if "error" in r],
        "mismatches": [r["id"] for r in results if not r.get("match") and "error" not in r],
        "ttl_load_seconds": round(load_s),
    }
    out = {
        "summary": summary,
        "results": results,
        "source": "released artifacts only (RAN1-body.ttl + sparql/*.rq); oracle = Neo4j replay rows",
        "parity_class_note": (
            "exact_cardinality = count equals the full (unbounded) result-set "
            "cardinality; limit_bound_topn = count equals a shared LIMIT that "
            "truncates a larger result set, evidencing cardinality only, not "
            "row-level equivalence."),
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(out, open(args.out, "w"), indent=1)
    print(json.dumps(summary, indent=1), flush=True)


if __name__ == "__main__":
    main()
