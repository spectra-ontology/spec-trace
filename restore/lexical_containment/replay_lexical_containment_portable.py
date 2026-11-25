#!/usr/bin/env python3
"""Remeasure twelve deterministic containment routes from explicit restored indices.

Uses the released original Index, identifier/hop routines and judge. All SQLite
connections are read-only. Dense retrieval, rank fusion and model/network calls
are excluded. Timing is measured afresh and excluded from historical equality.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import time

ROUTES = ("bm25_8x1500", "bm25_12x4000", "tdoc_1500", "tdoc_full",
          "idkey_1500", "idkey_full", "idany_1500", "idany_full",
          "hopkey_1500", "hopkey_full", "hopany_1500", "hopany_full")


def records(path):
    with path.open() as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def file_sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()


def measured_item(module, item, index):
    named = module.named_identifiers(item["question"])
    looked_up = set(named["docs"] + named["packs"])
    lexical = index.bm25(item["question"], module.FUSION_DEPTH)
    contexts = {"bm25_8x1500": (lexical[:8], 1500), "bm25_12x4000": (lexical[:12], 4000)}
    literal = set().union(*(index.tdoc_ids(ident) for ident in looked_up))
    contexts["tdoc_1500"], contexts["tdoc_full"] = (index.rows(literal), 1500), (index.rows(literal), None)
    hops = {}
    for mention, name in ((False, "key"), (True, "any")):
        seeds = module.seed_ids(index, named, mention)
        for limit, suffix in ((1500, "1500"), (None, "full")):
            contexts[f"id{name}_{suffix}"] = (index.rows(seeds), limit)
            ids, followed = module.hop_ids(index, seeds, looked_up, limit, mention)
            contexts[f"hop{name}_{suffix}"] = (index.rows(ids), limit)
            hops[f"hop{name}_{suffix}"] = {"identifiersFollowed": followed, "chunksAdded": len(ids)-len(seeds)}
    return {"id": item["id"], "questionSha256": hashlib.sha256(item["question"].encode()).hexdigest(),
            "goldSha256": module.gold_sha(item), "wg": item["wg"], "family": item["family"],
            "fields": item["fields"], "goldRows": len(item["gold"]), "named": named, "anchor": item["anchor"],
            "routes": {route: module.judge(*contexts[route], item) for route in ROUTES}, "hops": hops}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--route-module", type=Path, required=True)
    p.add_argument("--items", type=Path, action="append", required=True)
    p.add_argument("--gate", type=Path, action="append", required=True)
    p.add_argument("--historical-items", type=Path, required=True)
    p.add_argument("--index", action="append", required=True, metavar="WG=SQLITE")
    p.add_argument("--wg", action="append", choices=[f"RAN{i}" for i in range(1,6)])
    p.add_argument("--expected-items", type=int, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        p.error("--out must be a new or empty directory")
    args.out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(args.route_module.resolve().parent))
    spec = importlib.util.spec_from_file_location("original_lexical_containment", args.route_module)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    def blocked(*args, **kwargs):
        raise RuntimeError("Network, dense and fusion paths are outside this deterministic replay")
    for name in ("post", "retrieve", "point_count", "dense_chunks", "fuse"):
        setattr(module, name, blocked)
    index_paths = {}
    for entry in args.index:
        wg, path = entry.split("=", 1)
        if wg in index_paths:
            p.error("Duplicate index WG: " + wg)
        index_paths[wg] = Path(path)
    def connect(wg):
        con = sqlite3.connect(index_paths[wg].resolve().as_uri()+"?mode=ro", uri=True)
        con.execute("PRAGMA query_only=ON")
        con.execute("PRAGMA cache_size=-65536")
        return con
    module.connect_index = connect
    rejected = {r["id"] for file in args.gate for r in json.loads(file.read_text())["rejectedItems"]}
    selected = set(args.wg or index_paths)
    items = {r["id"]:r for file in args.items for r in records(file) if r["wg"] in selected and r["id"] not in rejected}
    if len(items) != args.expected_items:
        raise ValueError(f"Expected {args.expected_items} admitted items, found {len(items)}")
    historical = {r["id"]:r for r in records(args.historical_items) if r["id"] in items}
    failures = []
    counts = {route:{"compared":0,"exact":0} for route in ROUTES}
    started = time.monotonic()
    per_wg = {}
    metadata_keys = ("id","questionSha256","wg","family","fields","goldRows","named","anchor")
    with (args.out/"items.jsonl").open("w") as output:
        for wg in sorted(selected):
            module.guard_memory()
            index = module.Index(wg)
            wg_started = time.monotonic()
            todo = [r for r in items.values() if r["wg"]==wg]
            try:
                for position,item in enumerate(todo,1):
                    module.guard_memory()
                    before = time.monotonic()
                    actual = measured_item(module,item,index)
                    actual["seconds"] = time.monotonic()-before
                    output.write(json.dumps(actual,ensure_ascii=False)+"\n")
                    output.flush()
                    prior = historical.get(item["id"])
                    if prior is None:
                        failures.append({"id":item["id"],"kind":"missing_historical_item"})
                        continue
                    for key in metadata_keys:
                        if actual[key] != prior.get(key):
                            failures.append({"id":item["id"],"kind":"item_metadata","key":key})
                    if "goldSha256" in prior and actual["goldSha256"] != prior["goldSha256"]:
                        failures.append({"id":item["id"],"kind":"gold_hash"})
                    if actual["hops"] != prior["hops"]:
                        failures.append({"id":item["id"],"kind":"hop_details","actual":actual["hops"],"expected":prior["hops"]})
                    for route in ROUTES:
                        counts[route]["compared"] += 1
                        equal = actual["routes"][route] == prior["routes"][route]
                        counts[route]["exact"] += int(equal)
                        if not equal:
                            failures.append({"id":item["id"],"route":route,"kind":"route_details","actual":actual["routes"][route],"expected":prior["routes"][route]})
                    if position%5==0 or position==len(todo):
                        print(json.dumps({"wg":wg,"done":position,"of":len(todo),"elapsed_seconds":round(time.monotonic()-wg_started,3),"last_seconds":round(actual["seconds"],3),"failure_count":len(failures)}),flush=True)
            finally:
                index.con.close()
            per_wg[wg] = {"items":len(todo),"seconds":time.monotonic()-wg_started,"index_name":index_paths[wg].name,"index_bytes":index_paths[wg].stat().st_size}
    summary = {"passed":not failures,"items":len(items),"routes":counts,"working_groups":per_wg,
               "seconds":time.monotonic()-started,"failures":failures,
               "comparison":"Exact chunks/documents/chars/row labels/fieldsHeld for 12 routes, hop counts and item metadata; timing and dense/RRF/integrity summaries excluded.",
               "historical_gold_sha_present_items":sum("goldSha256" in r for r in historical.values()),
               "model_calls":0,"network_calls":0,"source_passages_written":False,
               "inputs":[{"role":role,"name":file.name,"sha256":file_sha(file)} for role,group in (("route_module",[args.route_module]),("items",args.items),("gate",args.gate),("historical_items",[args.historical_items])) for file in group]}
    (args.out/"receipt.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"passed":summary["passed"],"items":len(items),"route_records":sum(r["compared"] for r in counts.values()),"seconds":summary["seconds"],"failure_count":len(failures)}))
    if failures:
        raise SystemExit(1)


if __name__=="__main__":
    main()
