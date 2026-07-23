#!/usr/bin/env python3
"""count_triples.py — count RDF triples in each released per-WG body KG.

Reproducible from released artifacts only, with no database: streams every
statement in ``kg/per_wg/{WG}-body.ttl`` using the SAME parser the shipped
loader uses (``load_released_kg.StatementReader`` / ``parse_statement``).

An RDF triple is one (subject, predicate, object). parse_statement() returns
(subject, [(predicate, [object, ...]), ...]); a statement's triple count is
sum(len(objects)) over its predicates. ``@prefix`` lines parse to None.

Two totals per WG:
  * total_triples     — every statement (incl. the ontology header block)
  * instance_triples  — only INST_RE-matching instance subjects (the data graph)

instance_subjects equals the loaded node count (each instance subject becomes
one node); this is the cross-check tying triples to graph_counts.json nodes.

Output: validation/cq_replay/triple_counts.json

Usage:
  python3 release_package/pipeline/count_triples.py
"""
import json
import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
PKG = BASE.parent
sys.path.insert(0, str(BASE))
from load_released_kg import StatementReader, parse_statement, INST_RE  # noqa: E402

TTL_DIR = PKG / "kg/per_wg"
OUT = PKG / "validation/cq_replay/triple_counts.json"
WGS = ["RAN1", "RAN2", "RAN3", "RAN4", "RAN5"]


def count_wg(wg):
    ttl = TTL_DIR / f"{wg}-body.ttl"
    total = inst = subj_total = subj_inst = 0
    with open(ttl, encoding="utf-8") as fh:
        for stmt in StatementReader(fh):
            parsed = parse_statement(stmt)
            if parsed is None:
                continue
            subj, preds = parsed
            n = sum(len(objs) for _, objs in preds)
            total += n
            subj_total += 1
            if INST_RE.match(subj):
                inst += n
                subj_inst += 1
    return {
        "wg": wg,
        "total_triples": total,
        "instance_triples": inst,
        "total_subjects": subj_total,
        "instance_subjects": subj_inst,
    }


def main():
    per_wg = []
    gt = gi = 0
    for wg in WGS:
        r = count_wg(wg)
        per_wg.append(r)
        gt += r["total_triples"]
        gi += r["instance_triples"]
        print(f"{wg}: total_triples={r['total_triples']:,} "
              f"instance_triples={r['instance_triples']:,} "
              f"(subjects total={r['total_subjects']:,} "
              f"instance={r['instance_subjects']:,})", flush=True)
    out = {
        "source": "released kg/per_wg/*.ttl streamed via the shipped loader parser",
        "triple_definition": "one (subject, predicate, object); @prefix lines excluded",
        "per_wg": per_wg,
        "grand_total_triples": gt,
        "grand_instance_triples": gi,
    }
    os.makedirs(OUT.parent, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2))
    print(f"\n=== TOTAL RDF triples = {gt:,} "
          f"(instance-only = {gi:,}) -> {OUT.relative_to(PKG)} ===")


if __name__ == "__main__":
    main()
