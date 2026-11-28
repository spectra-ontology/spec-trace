"""Replay the pack-origin diagnostic on the released RAN3 graph."""
import argparse
import importlib.util
import json
import re
import time
from pathlib import Path

import verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", required=True, type=Path)
    parser.add_argument("--bolt", help="Read-only RAN3 endpoint for native replay")
    parser.add_argument("--neo4j-user-env", default="NEO4J_USER")
    parser.add_argument("--neo4j-password-env", default="NEO4J_PASSWORD")
    parser.add_argument("--neo4j-database", default="neo4j")
    args = parser.parse_args()
    release = args.release.resolve()
    study = Path(__file__).resolve().parent
    receipt = json.loads((study / "pack_anchor.json").read_text())
    runs = [r for r in verify.stream("full667.jsonl.gz") if r["run"] == receipt["run"] and r["family"] == "pack_origin"]
    queries = [r["query"] for r in verify.stream("queries.jsonl.gz") if r["querySha256"] == receipt["originalQuerySha256"]]
    if len(runs) != 20 or len(queries) != 1 or any(r["exact"] or r["status"] != "execution_error" or r.get("errorKind") != "row_limit" or r["querySha256"] != receipt["originalQuerySha256"] for r in runs):
        raise ValueError("Archived diagnostic cohort mismatch")
    original = queries[0]
    if not original.startswith("MATCH (d:Tdoc)") or "CRPack" in original:
        raise ValueError("Original query shape differs")
    manifest = (release / "studies/codex_model_comparison/native_restore/source/RAN3/manifest.json").read_bytes()
    if verify.sha(manifest) != receipt["graphManifestSha256"]:
        raise ValueError("Released RAN3 graph manifest differs")
    source = None
    scorer, kept, gold = verify.gold_inputs(release)
    by_id = {row["id"]: row for row in gold["full667"]}
    if args.bolt:
        spec = importlib.util.spec_from_file_location("native", release / "studies/codex_model_comparison/replay_queries.py")
        native = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(native)
        args.bolt, args.working_group = ["RAN3=" + args.bolt], "RAN3"
        args.graph_identity = "Published RAN3 query graph"
        source = native.CypherInputs(args, release / "studies/matched_domains")
    try:
        if source and source.before["RAN3"] != json.loads(manifest)["before_counts"]:
            raise ValueError("RAN3 graph population differs from source")
        for r in runs:
            cid = r["id"]
            item = by_id[cid]
            observed = receipt["items"][cid]
            packs = re.findall(r"\bRP-\d+\b", item["question"])
            if packs != [observed["pack"]]:
                raise ValueError("Question anchor mismatch for " + cid)
            anchor = '(d:Tdoc)-[:BELONGS_TO_CR_PACK|HAS_CR]-(pack:CRPack {crPackId: ' + json.dumps(packs[0]) + '})'
            edited = original.replace("MATCH (d:Tdoc)", "MATCH " + anchor, 1)
            expected = verify.fingerprint(scorer, item, item["gold"], kept)
            if verify.sha(edited.encode()) != observed["editedQuerySha256"] or observed["returnedSetSha256"] != expected:
                raise ValueError("Reconstructed query or stored answer mismatch for " + cid)
            if source:
                fields, found = source.execute("RAN3", edited, time.monotonic())
                rows = [[None if v is None else str(v) for v in row] for row in found]
                if len(rows) > 2000 or len(fields) != len(item["fields"]) or verify.fingerprint(scorer, item, rows, kept) != expected:
                    raise ValueError("Native replay mismatch for " + cid)
        if source:
            source.verify_unchanged()
    finally:
        if source:
            source.close()
    print(json.dumps({"items":len(runs), "originalExact":0, "anchoredExact":20, "nativeReplay":bool(source)}))


if __name__ == "__main__":
    main()
