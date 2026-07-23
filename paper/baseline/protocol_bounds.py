#!/usr/bin/env python3
"""Recompute the protocol-level bounds quoted in the paper from recorded artifacts.

Three measurements, none of which calls a model:

1. Retrieval coverage bound (Section 6, Appendix F): for each of the 624
   questions, whether at least one / every one of its gold identifiers appears
   verbatim in the first k recorded retrieved passages (k in {1, 3, 5, 10}).
   Reads results/_rag_cache/ and the released benchmark.jsonl.
2. KG-grounded failure accounting (Section 6, Appendix F): distribution of
   execution statuses across the nine recorded KG-grounded runs.
3. Gold answer-set cardinality (Section 5): min / median / mean / max of
   gold_row_count over the 624 released questions.

Everything is derived from files in this repository plus the released
benchmark; run it from the repository root after fetching the release.
"""
import ast
import collections
import glob
import gzip
import json
import statistics
from pathlib import Path

BASE = Path(__file__).resolve().parent
BENCH = BASE.parent.parent / "release_package/cqs/spectra_cq_v2.0/benchmark.jsonl"
CACHE = BASE / "results/_rag_cache"
KG_RUNS = BASE / "results/kg_grounded"


def gold_values(row):
    g = row["gold_primary_values"]
    return [str(x) for x in (g if isinstance(g, list) else ast.literal_eval(g))]


def retrieval_coverage(rows):
    ks = (1, 3, 5, 10)
    stats = {k: {"any": 0, "all": 0} for k in ks}
    n = 0
    for r in rows:
        path = CACHE / r["wg"] / f"{r['id']}.json"
        if not path.exists():
            raise SystemExit(f"missing retrieval cache for {r['id']}")
        prov = json.loads(path.read_text())["provenance"]
        gold = gold_values(r)
        n += 1
        for k in ks:
            blob = " ".join(
                (c.get("text") or "") + " " + str(c.get("chunkId") or "")
                + " " + str(c.get("spec") or "") for c in prov[:k])
            hits = [g in blob for g in gold]
            stats[k]["any"] += any(hits)
            stats[k]["all"] += all(hits)
    print(f"retrieval coverage over n={n} questions "
          "(gold identifier present verbatim in top-k passages):")
    for k in ks:
        a, f = stats[k]["any"], stats[k]["all"]
        print(f"  top-{k:>2}: any-gold {a}/{n} = {a/n:.3f}   "
              f"full-set {f}/{n} = {f/n:.3f}")


def kg_failures():
    agg = collections.Counter()
    for fp in sorted(glob.glob(str(KG_RUNS / "*/all.jsonl.gz"))):
        model = Path(fp).parent.name
        c = collections.Counter()
        for line in gzip.open(fp, "rt"):
            row = json.loads(line)
            c[row.get("exec_status") or "NO_STATUS"] += 1
        agg.update(c)
        print(f"  {model:<20} {dict(sorted(c.items()))}")
    total = sum(agg.values())
    fail = total - agg.get("OK", 0)
    print(f"kg-grounded attempts: {total}; failures {fail} "
          f"({fail/total:.1%}) = {dict(sorted(agg.items()))}")


def gold_cardinality(rows):
    cards = [int(r["gold_row_count"]) for r in rows]
    print(f"gold answer-set size over n={len(cards)}: min {min(cards)}, "
          f"median {statistics.median(cards):.0f}, "
          f"mean {statistics.mean(cards):.1f}, max {max(cards)}; "
          f"non-empty: {all(c >= 1 for c in cards)}")


def main():
    rows = [json.loads(l) for l in open(BENCH)]
    print(f"== gold cardinality (benchmark.jsonl, {len(rows)} rows)")
    gold_cardinality(rows)
    print("== KG-grounded execution outcomes (recorded runs)")
    kg_failures()
    print("== retrieval coverage bound (recorded logs, no model calls)")
    retrieval_coverage(rows)


if __name__ == "__main__":
    main()
