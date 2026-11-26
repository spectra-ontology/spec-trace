#!/usr/bin/env python3
"""Capture and restore the native graph inputs consumed by preserved Cypher queries.

The release's dependency-projected graph serializer supplies complete topology,
typed properties, two-pass source fingerprints, and verified empty-target restore.
This adapter binds that serializer to the actual query study rather than CQ inputs.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import logging
import os
from pathlib import Path
import re
import sys
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
GROUPS = tuple(f"RAN{i}" for i in range(1, 6))
logging.getLogger("neo4j").setLevel(logging.CRITICAL)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def helper_directory(explicit=None):
    if explicit is not None:
        return explicit.resolve()
    for parent in HERE.parents:
        candidate = parent / "restore/competency_queries"
        if (candidate / "graph_snapshot.py").is_file():
            return candidate
        if (parent / "CLAUDE.md").is_file():
            return parent / ("logs/publication/paper/ongoing/"
                "vldb-2027-experiment-analysis-benchmark/release_preparation/"
                "vldb_release/restore/competency_queries")
    raise ValueError("Supply --cq-tools with the release's graph serializer directory")


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def query_inputs(guard):
    """Inspect every executed first-query byte, retaining a conservative superset.

    Fixed property names from temporary maps also enter the whitelist. This
    over-inclusion preserves graph values and requires no heuristic node/map
    distinction. Complete graph topology covers all node and relationship tokens.
    Whole-property/dynamic access is rejected for explicit review.
    """
    analysis = load(STUDY / "analysis.json")
    queries, properties, tokens = [], set(), set()
    sources = {}
    for rid, run in analysis["runs"].items():
        if run["language"] != "cypher" or not run["nativeQueriesExecuted"]:
            continue
        filename = f"cypher_{run['repetition']}.jsonl"
        path = STUDY / "submissions" / rid / filename
        commitment = load(path.parent / "commitment.json")
        if digest(path) != commitment["querySha256"]:
            raise ValueError("Committed query digest differs: " + rid)
        sources[str(path.relative_to(STUDY))] = digest(path)
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            syntax, _ = guard._query_syntax(item["query"])
            if re.search(r"\b(?:keys|properties|id|elementId)\s*\(", syntax, re.I):
                raise ValueError("Whole-property/internal-ID consumption requires review: " + rid + "/" + item["id"])
            dynamic = re.finditer(r"\b([A-Za-z_]\w*)\s*\[\s*(?:['\"$]|[A-Za-z_]\w*\s*\])", syntax)
            if any(match.group(1).upper() not in {"IN", "RETURN", "WITH", "AS", "UNWIND", "THEN", "ELSE"}
                   for match in dynamic):
                # The fixed cohort uses list/map indexing only with numeric or
                # computed indices. Named dynamic graph access gets no fallback.
                raise ValueError("Dynamic named property access requires review: " + rid + "/" + item["id"])
            if re.search(r"\.\s*\*", syntax):
                raise ValueError("Wildcard property consumption requires review: " + rid)
            used = set(re.findall(r"\b[A-Za-z_]\w*\s*\.\s*`?([A-Za-z_]\w*)`?", syntax))
            used.update(re.findall(r"(?:\{|,)\s*`?([A-Za-z_]\w*)`?\s*:", syntax))
            properties.update(used)
            tokens.update(re.findall(r"[:|]\s*`?([A-Za-z_]\w*)`?", syntax))
            queries.append({"runId": rid, "packetId": item["id"],
                "querySha256": hashlib.sha256(item["query"].encode()).hexdigest(),
                "properties": sorted(used),
                "unboundValueParameters": sorted(set(re.findall(r"\$([A-Za-z_]\w*)", syntax)))})
    if len(queries) != 750:
        raise ValueError("Expected exactly 750 actually executed Cypher first queries")
    return {"format": "spectra-native-query-dependencies-1", "queries": queries,
        "queryFiles": sources, "analysisSha256": digest(STUDY / "analysis.json"),
        "properties": sorted(properties), "text_labels": [], "text_properties": [],
        "structure": "All nodes, every node label, all relationship occurrences, endpoints, directions and types.",
        "property_rule": "All fixed property names consumed by the 750 query texts, including a conservative superset of temporary-map field names; same whitelist applies to nodes and relationships.",
        "access_forms": "Fixed property access; fixed labels/relationship types; variable paths, entity equality, startNode/endNode and type consume preserved topology. Direct id(), elementId(), keys(), properties(), wildcard or dynamic named property consumption is checked. Original unbound value parameters remain unchanged and reproduce missing-parameter errors.",
        "tokenProbes": {"labels": sorted(tokens), "relationship_types": sorted(tokens),
                        "property_keys": sorted(properties)}}


def connection(args):
    user, password = os.environ.get(args.user_env), os.environ.get(args.password_env)
    if user is None or password is None:
        raise ValueError("Set selected user/password environment variables")
    return {"uri": args.bolt, "user": user, "password_env": args.password_env,
            "database": args.database}


def reuse_topology(gs, helper, group, dependency, capture=False):
    """Bind the full published topology and store exact native property deltas.

    Every source record is compared with the corresponding published record.
    Any topology/order mismatch stops capture. Delta records replace the complete
    projected property map, so removed values are represented exactly as well.
    """
    release = helper.parent.parent
    base = release / "sources/competency_queries/graph_view" / group
    manifest_path = base / "manifest.json"
    manifest = load(manifest_path)
    original_read, original_shards = gs.read_records, gs.Shards
    whitelist = set(dependency["properties"])
    checked = {}
    binding = {"manifestPathFromRelease": str(manifest_path.relative_to(release)),
               "manifestSha256": digest(manifest_path), "counts": manifest["before_counts"]}

    class DeltaShards:
        def __init__(self, directory, kind):
            self.kind, self.base = kind, iter(original_read(base, manifest["records"][kind]))
            self.inner = original_shards(directory, kind + "-property-overlay")
            self.count = self.deltas = 0
            self.files = []

        def write(self, rows):
            overlays = []
            for row in rows:
                prior = next(self.base)
                topology = lambda item: {k: v for k, v in item.items() if k != "properties"}
                if topology(row) != topology(prior):
                    raise ValueError("Published/native topology or record order differs: " + self.kind + "/" + row["id"])
                properties = {k: v for k, v in prior["properties"].items() if k in whitelist}
                if properties != row["properties"]:
                    overlays.append({"id": row["id"], "properties": row["properties"]})
                    self.deltas += 1
                self.count += 1
            if overlays:
                self.inner.write(overlays)

        def close_current(self):
            if next(self.base, None) is not None:
                raise ValueError("Native capture has fewer records than published topology")
            self.inner.close_current()
            self.files = self.inner.files
            checked[self.kind] = {"allTopologyRecordsEqual": True,
                "recordsCompared": self.count, "propertyOverlayRecords": self.deltas}

    if capture:
        gs.Shards = DeltaShards

    def composed_records(directory, record):
        current = load(directory / "manifest.json")
        selected = current["query_study"]["reusedBaseView"]
        if selected["manifestSha256"] != digest(manifest_path):
            raise ValueError("Published base topology manifest digest differs")
        if selected["manifestPathFromRelease"] != binding["manifestPathFromRelease"]:
            raise ValueError("Published base topology reference differs")
        kind = record["kind"]
        overlays = {}
        for row in original_read(directory, record):
            if row["id"] in overlays:
                raise ValueError("Duplicate property overlay ID")
            overlays[row["id"]] = row["properties"]
        for row in original_read(base, manifest["records"][kind]):
            row = dict(row)
            row["properties"] = overlays.pop(row["id"],
                {k: v for k, v in row["properties"].items() if k in whitelist})
            yield row
        if overlays:
            raise ValueError("Property overlays contain IDs outside published topology")

    return binding, checked, composed_records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("dependencies", "export", "restore", "check"))
    parser.add_argument("--working-group", choices=GROUPS)
    parser.add_argument("--bolt")
    parser.add_argument("--database", default="neo4j")
    parser.add_argument("--user-env", default="NEO4J_USER")
    parser.add_argument("--password-env", default="NEO4J_PASSWORD")
    parser.add_argument("--cq-tools", type=Path)
    parser.add_argument("--source", type=Path, default=HERE / "source")
    parser.add_argument("--output", type=Path, default=HERE / "receipts")
    parser.add_argument("--timeout", type=float, default=1800)
    parser.add_argument("--confirm-empty-target", action="store_true")
    args = parser.parse_args()
    helper = helper_directory(args.cq_tools)
    sys.path.insert(0, str(helper))
    gs = module("native_query_graph_serializer", helper / "graph_snapshot.py")
    guard = module("native_query_syntax_guard", helper / "cq_anchor_guard.py")
    dependency = query_inputs(guard)
    definition = {"format": "spectra-native-query-definition-1", "queryFiles": dependency["queryFiles"],
                  "analysisSha256": dependency["analysisSha256"], "properties": dependency["properties"]}
    contract = {"definition_contract": definition, "graph_views": []}
    # Reuse the serializer's tested graph mechanics with this study's explicit
    # dependency proof; original helper files and CQ definitions stay byte-bound.
    gs.dependencies = lambda *_: dependency
    gs.token_probes = lambda *_: dependency["tokenProbes"]
    if args.mode == "dependencies":
        target = HERE / "dependencies.json"
        if target.exists() and load(target) != dependency:
            raise ValueError("Preserve the prior dependency definition")
        save(target, dependency)
        print(json.dumps({"queries": len(dependency["queries"]), "properties": dependency["properties"]}))
        return
    if not args.working_group:
        parser.error("Select --working-group")
    base_binding, topology_checked, composed_records = reuse_topology(
        gs, helper, args.working_group, dependency, capture=args.mode == "export")
    if args.mode != "export":
        gs.read_records = composed_records
    directory = args.source.resolve() / args.working_group
    selected = {"working_group": args.working_group,
                "manifest_path": str((directory / "manifest.json").relative_to(HERE)),
                "definition_binding_path": str((directory / "definition_binding.json").relative_to(HERE))}
    if args.mode == "check":
        manifest = load(directory / "manifest.json")
        if manifest["dependency"] != dependency:
            raise ValueError("Snapshot dependencies differ from actual committed queries")
        for kind, record in manifest["records"].items():
            fp = gs.Fingerprint()
            for row in gs.read_records(directory, record):
                fp.add(row)
            if fp.value() != record["fingerprint"]:
                raise ValueError("Logical shard content differs: " + kind)
        print(json.dumps({"checked": args.working_group, "counts": manifest["before_counts"]}))
        return
    if not args.bolt:
        parser.error("Supply --bolt")
    conn = connection(args)
    common = SimpleNamespace(working_group=args.working_group, timeout=args.timeout,
                             output=args.source.resolve(), snapshot=directory,
                             confirm_empty_target=args.confirm_empty_target)
    if args.mode == "export":
        gs.export(HERE, contract, [], {"contract_sha256": hashlib.sha256(gs.canonical(definition)).hexdigest()}, conn, common)
        gs.capture_label_order(conn, common)
        gs.capture_schema_tokens(HERE, contract, [], conn, common)
        observation = directory / "schema_token_observations.json"
        save(directory / "definition_binding.json", {"definition_contract": definition,
            "schema_token_observations": {"path": str(observation.relative_to(HERE)),
                                           "sha256": digest(observation)}})
        manifest = load(directory / "manifest.json")
        manifest["query_study"] = {"definition_contract": definition,
            "reusedBaseView": base_binding, "topologyComparison": topology_checked,
            "serializerSha256": digest(helper / "graph_snapshot.py"),
            "runnerSha256": digest(helper / "runner.py"),
            "adapterSha256": digest(Path(__file__)),
            "scope": "Separately captured native input for the preserved Cypher query study; source and historical study outputs are related by subsequent exact per-query replay."}
        save(directory / "manifest.json", manifest)
        for kind, record in manifest["records"].items():
            record["kind"] = kind
        save(directory / "manifest.json", manifest)
        print(json.dumps({"export_complete": args.working_group, "manifestSha256": digest(directory / "manifest.json")}))
    else:
        manifest = load(directory / "manifest.json")
        if digest(helper / "graph_snapshot.py") != manifest["query_study"]["serializerSha256"]:
            raise ValueError("Graph serializer source digest differs")
        selected["manifest_sha256"] = digest(directory / "manifest.json")
        contract["graph_views"] = [selected]
        common.output = args.output.resolve()
        expected = common.output / (args.working_group + "-restore.json")
        if expected.exists():
            raise ValueError("Preserve an existing restore receipt")
        gs.restore(HERE, contract, [], conn, common)
        receipt = load(expected)
        receipt["scope"] = "Fresh restoration of the query-study dependency projection into an initially empty target."
        receipt["adapterSha256"] = digest(Path(__file__))
        receipt["finishedUtc"] = datetime.now(timezone.utc).isoformat()
        save(expected, receipt)


if __name__ == "__main__":
    main()
