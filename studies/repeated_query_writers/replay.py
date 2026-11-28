#!/usr/bin/env python3
"""Re-execute one saved query or one scheduled batch with the released native adapters."""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import time

import verify as v


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--release", required=True, type=Path)
    ap.add_argument("--study", choices=["full667", "matched50"], required=True)
    ap.add_argument("--run", required=True, help="run identifier in runs.json")
    ap.add_argument("--first-write", action="store_true", help="replay reconstructed first writes in the three audited batches")
    ap.add_argument("--id", help="limit replay to one canonical question ID")
    ap.add_argument("--sqlite-dir", type=Path, help="five uncompressed RAN1.sqlite through RAN5.sqlite inputs")
    ap.add_argument("--bolt", action="append", default=[], help="RANn=URI, one per selected Cypher group")
    ap.add_argument("--neo4j-user-env", default="NEO4J_USER")
    ap.add_argument("--neo4j-password-env", default="NEO4J_PASSWORD")
    ap.add_argument("--neo4j-database", default="neo4j")
    args = ap.parse_args()
    release = args.release.resolve()
    run = next((r for r in v.load(v.HERE/"runs.json") if r["run"] == args.run and r["study"] == args.study), None)
    v.require(run, "Unknown run")
    records = [r for r in v.stream(args.study+".jsonl.gz")
               if r["run"] == args.run and (args.id is None or r["id"] == args.id)]
    v.require(records, "Unknown question for run")
    needed = {r["querySha256"] for r in records if r["querySha256"] is not None}
    queries = {r["querySha256"]:r["query"] for r in v.stream("queries.jsonl.gz") if r["querySha256"] in needed}
    v.require(set(queries) == needed and all(v.sha(text.encode()) == h for h,text in queries.items()), "Query hash")
    if args.first_write:
        changes = {r["id"]: r for r in v.stream("first_writes.jsonl.gz") if r["run"] == args.run and r["study"] == args.study}
        v.require(changes, "This run has no first-write reconstruction")
        for r in records:
            if r["id"] in changes:
                pair = changes[r["id"]]
                first = pair["first"]
                v.require(v.sha(pair["firstQuery"].encode()) == first["querySha256"], "Reconstructed query hash")
                queries[first["querySha256"]] = pair["firstQuery"]
                r.update(first)
    stored = v.load(v.HERE/"items.json")
    for name, h in stored["inputs"].items():
        v.require(v.sha((release/name).read_bytes()) == h, "Pinned scorer or input checksum: " + name)
    scorer, kept, groups = v.gold_inputs(release)
    gold = {item["id"]:item for item in groups[args.study]}
    native_name = "studies/codex_model_comparison/replay_queries.py"
    spec = importlib.util.spec_from_file_location("spectra_replay", release/native_name)
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    wgs = sorted({r["wg"] for r in records})
    args.working_group = wgs[0] if len(wgs) == 1 else None
    args.graph_identity = "Published five-working-group projection with assessmentMethod"
    source = None
    failures = []
    counts = Counter()
    try:
        if needed:
            matched = release/"studies/matched_domains"
            if run["language"] == "sql":
                source = native.SqlInputs(args,matched)
            else:
                source = native.CypherInputs(args,matched)
                for wg in wgs:
                    name = "studies/codex_model_comparison/native_restore/source/"+wg+"/manifest.json"
                    v.require(source.before[wg] == v.load(release/name)["before_counts"], "Graph population: "+wg)
        for r in records:
            q = queries.get(r["querySha256"])
            item = gold[r["id"]]
            if q is None:
                counts["no_query"] += 1
                v.require(r["returnedIdentitySetSha256"] is None and r["exact"] == 0, "Missing-query accounting")
                continue
            try:
                fields, found = source.execute(r["wg"], q, time.monotonic())
                v.require(len(found) <= 2000 and len(fields) == len(item["fields"]), "Row or column limit")
                rows = [[None if v is None else str(v) for v in row] for row in found]
            except Exception as exc:
                if type(exc).__name__ in {"AuthError","ServiceUnavailable","SessionExpired","BoltError","IncompleteCommit"}:
                    raise
                rows = None
            result = v.fingerprint(scorer,item,rows,kept)
            success = result == r["returnedIdentitySetSha256"]
            counts["matching_outcomes" if success else "different_outcomes"] += 1
            if not success:
                failures.append(r["id"])
        if source:
            source.verify_unchanged()
    finally:
        if source:
            source.close()
    print(json.dumps({"run":args.run,"positions":len(records),"outcomes":dict(counts),"different":failures}))
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
