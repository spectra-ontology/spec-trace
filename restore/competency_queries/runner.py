#!/usr/bin/env python3
"""Verify all CQ inputs or execute them against explicitly supplied Neo4j graphs."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import logging
import os
from pathlib import Path
import re
import sys
import time

logging.getLogger("neo4j").setLevel(logging.CRITICAL)


def canonical_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def file_digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify(row_count, question, defects):
    minimum = question.get("expected_min_rows")
    if defects or (minimum is not None and row_count < minimum):
        return "FAIL"
    if row_count or minimum == 0 or question.get("allow_zero") is True:
        return "PASS"
    return "NO_DATA"


def release_path(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Artifact path escapes release: {relative}")
    return path


def definition_identity(contract):
    """Identify authored executable inputs independently of package/snapshot metadata."""
    artifacts = {item["path"]: item for item in contract["artifacts"]}
    return {"format": "spectra-cq-definition-contract-1",
            "guard_artifacts": {key: {"path": contract["guard"][key],
                "sha256": artifacts[contract["guard"][key]]["sha256"]}
                for key in ("path", "ontology_path")},
            "datasets": [{key: item[key] for key in
                ("working_group", "phase", "definition_path", "definition_sha256", "question_count")} |
                {"questions": [{key: question[key] for key in
                    ("id", "definition_sha256", "query_sha256")} for question in item["bindings"]]}
                for item in contract["datasets"]]}


def definition_queries(contract):
    return [{"key": f"{item['working_group']}/phase-{item['phase']}/{question['id']}",
             "query_sha256": question["query_sha256"]}
            for item in contract["datasets"] for question in item["bindings"]]


def verify(root):
    contract_path = root / "sources/competency_queries/contract.json"
    contract = json.loads(contract_path.read_text())
    if contract.get("format") != "spectra-cq-contract-1":
        raise ValueError("Unsupported CQ contract format")
    paths = set()
    for artifact in contract["artifacts"]:
        path = release_path(root, artifact["path"])
        if artifact["path"] in paths:
            raise ValueError(f"Duplicate artifact: {artifact['path']}")
        paths.add(artifact["path"])
        if not path.is_file():
            raise ValueError(f"Missing CQ artifact: {artifact['path']}")
        if path.stat().st_size != artifact["bytes"] or file_digest(path) != artifact["sha256"]:
            raise ValueError(f"CQ artifact digest/size differs: {artifact['path']}")
    datasets, keys, statuses, query_bindings, dataset_bindings = [], set(), Counter(), Counter(), Counter()
    for item in contract["datasets"]:
        definition_path = release_path(root, item["definition_path"])
        receipt_path = release_path(root, item["receipt_path"])
        for path, expected in [(definition_path, item["definition_sha256"]), (receipt_path, item["receipt_sha256"])]:
            if str(path.relative_to(root)) not in paths or file_digest(path) != expected:
                raise ValueError(f"Dataset file absent from pinned artifacts: {path.relative_to(root)}")
        definition = json.loads(definition_path.read_text())
        receipt = json.loads(receipt_path.read_text())
        questions = definition["questions"]
        results = receipt["results"]
        if len({r["id"] for r in results}) != len(results):
            raise ValueError("Duplicate historical result ID")
        by_id = {r["id"]: r for r in results}
        bindings = {b["id"]: b for b in item["bindings"]}
        if len(bindings) != len(item["bindings"]) or len(questions) != item["question_count"]:
            raise ValueError("Duplicate binding or dataset count mismatch")
        if {q["id"] for q in questions} != set(by_id) or set(bindings) != set(by_id):
            raise ValueError("CQ IDs differ across definitions, receipts and bindings")
        recorded = receipt["metadata"].get("dataset_hash")
        binding = item["historical_dataset_binding"]
        expected_status = "recorded_prefix_matches" if recorded else "digest_unrecorded"
        if (recorded != binding["recorded_sha256_prefix"] or binding["status"] != expected_status or
                (recorded and not item["definition_sha256"].startswith(recorded))):
            raise ValueError("Historical dataset digest binding differs")
        dataset_bindings[expected_status] += 1
        for question in questions:
            key = (item["working_group"], item["phase"], question["id"])
            if key in keys:
                raise ValueError(f"Duplicate CQ identity: {key}")
            keys.add(key)
            old, bound = by_id[question["id"]], bindings[question["id"]]
            if not isinstance(question.get("cypher"), str) or not question["cypher"].strip():
                raise ValueError(f"Missing query: {key}")
            if canonical_digest(question) != bound["definition_sha256"]:
                raise ValueError(f"Question/declared assertions differ: {key}")
            if hashlib.sha256(question["cypher"].encode()).hexdigest() != bound["query_sha256"]:
                raise ValueError(f"Bound query differs: {key}")
            if canonical_digest(old) != bound["historical_result_sha256"] or old["status"] != bound["historical_status"]:
                raise ValueError(f"Bound historical result differs: {key}")
            recorded_query = old.get("query")
            query_status = "exact_text_match" if recorded_query is not None else "query_text_unrecorded"
            if (bound["historical_query_binding"] != query_status or
                    (recorded_query is not None and recorded_query != question["cypher"])):
                raise ValueError(f"Historical query text differs: {key}")
            statuses[old["status"]] += 1
            query_bindings[query_status] += 1
        datasets.append((item, questions))
    if len(datasets) != contract["dataset_count"] or len(keys) != contract["question_count"]:
        raise ValueError("Contract dataset/question count differs")
    if {(item["working_group"], item["phase"]) for item, _ in datasets} != {
            (f"RAN{wg}", phase) for wg in range(1, 6) for phase in range(1, 6)}:
        raise ValueError("Expected exactly the 25 regular WG/phase datasets")
    identity_binding = contract["definition_contract"]
    identity_path = release_path(root, identity_binding["path"])
    if (identity_binding["path"] not in paths or file_digest(identity_path) != identity_binding["sha256"] or
            json.loads(identity_path.read_text()) != definition_identity(contract)):
        raise ValueError("Independent CQ definition contract differs")
    expected_queries = definition_queries(contract)
    view_groups = set()
    for view in contract.get("graph_views", []):
        path = release_path(root, view["manifest_path"])
        if view["working_group"] in view_groups or file_digest(path) != view["manifest_sha256"]:
            raise ValueError("Duplicate graph view or graph manifest digest differs")
        view_groups.add(view["working_group"])
        captured = json.loads(path.read_text())
        if (captured["working_group"] != view["working_group"] or captured["before_counts"] != view["counts"] or
                not captured["consistency"]["repeated_content_fingerprints_match"]):
            raise ValueError("Graph view identity/count/consistency declaration differs")
        binding_path = release_path(root, view["definition_binding_path"])
        if (view["definition_binding_path"] not in paths or
                file_digest(binding_path) != view["definition_binding_sha256"]):
            raise ValueError("CQ graph definition sidecar digest differs")
        binding = json.loads(binding_path.read_text())
        captured_queries = [{key: row[key] for key in ("key", "query_sha256")}
                            for row in captured["dependency"]["questions"]]
        if (binding["format"] != "spectra-cq-view-definition-binding-1" or
                binding["working_group"] != view["working_group"] or
                binding["snapshot_manifest_sha256"] != view["manifest_sha256"] or
                binding["definition_contract"] != identity_binding or
                captured_queries != expected_queries or
                binding["captured_query_identity_sha256"] != canonical_digest(captured_queries) or
                binding["dependency_sha256"] != canonical_digest(captured["dependency"])):
            raise ValueError("CQ graph/definition dependency binding differs")
        schema_binding = binding["schema_token_observations"]
        schema_path = release_path(root, schema_binding["path"])
        if schema_binding["path"] not in paths or file_digest(schema_path) != schema_binding["sha256"]:
            raise ValueError("CQ schema-token observations digest differs")
        schema = json.loads(schema_path.read_text())
        schema_probes = [(kind, name) for kind, names in schema["probes"].items() for name in names]
        observed = [(row["kind"], row["name"]) for row in schema["observations"]]
        known = {kind: [row["name"] for row in schema["observations"] if row["kind"] == kind and row["known"]]
                 for kind in schema["probes"]}
        if (schema["format"] != "spectra-cq-schema-token-observations-1" or
                schema["working_group"] != view["working_group"] or
                schema["snapshot_manifest_sha256"] != view["manifest_sha256"] or
                schema["definition_contract"] != identity_binding or schema["source_counts"] != view["counts"] or
                not schema["repeated_probes_match"] or schema_probes != observed or schema["known_tokens"] != known):
            raise ValueError("CQ schema-token observation binding differs")
    summary = {"datasets": len(datasets), "questions": len(keys), "historical_statuses": dict(statuses),
               "historical_query_bindings": dict(query_bindings),
               "historical_dataset_bindings": dict(dataset_bindings),
               "contract_sha256": file_digest(contract_path),
               "definition_contract_sha256": identity_binding["sha256"]}
    return contract, datasets, summary


class ReadTransaction:
    """Keep query and guard reads in one rolled-back transaction per CQ."""
    def __init__(self):
        self.transaction = None

    def run(self, query, **parameters):
        return self.transaction.run(query, **parameters)


def run(root, contract, datasets, summary, args):
    from neo4j import GraphDatabase, READ_ACCESS, Query
    spec = importlib.util.spec_from_file_location("spectra_cq_guard", release_path(root, contract["guard"]["path"]))
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    guard._ONTOLOGY_PATH = release_path(root, contract["guard"]["ontology_path"])
    connections = json.loads(args.connections.read_text())
    selected = set(args.working_group or [f"RAN{wg}" for wg in range(1, 6)])
    if selected - connections.keys():
        raise ValueError(f"Missing connection entries for: {sorted(selected - connections.keys())}")
    report = {"scope": "Fresh read-only operational execution; historical outcomes remain separate.",
              "started_utc": datetime.now(timezone.utc).isoformat(), "input_verification": summary,
              "graph_identity": args.graph_identity, "working_groups": sorted(selected), "results": []}
    for wg in sorted(selected):
        connection = connections[wg]
        password_env = connection["password_env"]
        if password_env not in os.environ:
            raise ValueError(f"Set the password environment variable named by {wg}.password_env")
        with GraphDatabase.driver(connection["uri"], auth=(connection["user"], os.environ[password_env]),
                                  connection_timeout=args.timeout) as driver:
            with driver.session(database=connection.get("database", "neo4j"), default_access_mode=READ_ACCESS) as session:
                readonly = ReadTransaction()
                inventory = {}
                for name, query in [("nodes", "MATCH (n) RETURN count(n) AS count"),
                                    ("relationships", "MATCH ()-[r]->() RETURN count(r) AS count")]:
                    inventory[name] = session.run(Query(query, timeout=args.timeout)).single()["count"]
                report.setdefault("graph_inventory", {})[wg] = inventory
                for item, questions in datasets:
                    if item["working_group"] != wg:
                        continue
                    for cq in questions:
                        started = time.monotonic()
                        row = {"working_group": wg, "phase": item["phase"], "id": cq["id"],
                               "query_sha256": hashlib.sha256(cq["cypher"].encode()).hexdigest(),
                               "historical_status": next(b["historical_status"] for b in item["bindings"] if b["id"] == cq["id"])}
                        tx = session.begin_transaction(timeout=args.timeout)
                        readonly.transaction = tx
                        rows = None
                        try:
                            syntax, _ = guard._query_syntax(cq["cypher"])
                            if re.search(r"\b(?:CREATE|MERGE|SET|DELETE|DETACH|REMOVE|DROP)\b|\bLOAD\s+CSV\b|\bCALL\s+(?!\{)", syntax, re.I):
                                raise ValueError("CQ execution accepts read-only query syntax and CALL subqueries")
                            rows = tx.run(cq["cypher"]).data()
                            row["row_count"] = len(rows)
                            row["ordered_rows_sha256"] = canonical_digest(rows)
                            row_digests = sorted(canonical_digest(value) for value in rows)
                            row["row_multiset_sha256"] = canonical_digest(row_digests)
                            row["guard_defects"] = guard.guard_defects(readonly, cq, rows=rows)
                            minimum = cq.get("expected_min_rows")
                            if minimum is not None:
                                row["expected_min_rows"] = minimum
                                row["minimum_satisfied"] = len(rows) >= minimum
                            row["status"] = classify(len(rows), cq, row["guard_defects"])
                        except Exception as exc:
                            row["status"] = "ERROR"
                            # Driver messages can include connection details; record the error class only.
                            row["error_type"] = type(exc).__name__
                        finally:
                            tx.rollback()
                        row["seconds"] = round(time.monotonic() - started, 6)
                        row["historical_status_matches"] = row["status"] == row["historical_status"]
                        report["results"].append(row)
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    report["counts"] = dict(Counter(row["status"] for row in report["results"]))
    report["executed"] = len(report["results"])
    report["all_654_executed"] = report["executed"] == contract["question_count"]
    report["historical_status_mismatches"] = sum(not row["historical_status_matches"] for row in report["results"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({key: report[key] for key in ("executed", "all_654_executed", "counts", "historical_status_mismatches")}))
    return int(any(report["counts"].get(status, 0) for status in ("FAIL", "ERROR")))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, required=True, help="Explicit public release root")
    parser.add_argument("--mode", choices=("verify", "run"), default="verify")
    parser.add_argument("--connections", type=Path, help="WG-keyed JSON with uri, user, password_env and optional database")
    parser.add_argument("--working-group", action="append", choices=[f"RAN{wg}" for wg in range(1, 6)])
    parser.add_argument("--graph-identity", help="Input snapshot digest or explicit current-service description")
    parser.add_argument("--timeout", type=float, default=8)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    if args.mode == "run" and not all((args.connections, args.graph_identity, args.out)):
        parser.error("run requires --connections, --graph-identity and --out")
    try:
        contract, datasets, summary = verify(args.release.resolve())
        if args.mode == "verify":
            print(json.dumps(summary, indent=2))
            return 0
        return run(args.release.resolve(), contract, datasets, summary, args)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"CQ input/contract error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
