#!/usr/bin/env python3
"""Uniform, byte-preserving follow-up execution of all 36 saved Cypher queries.

This does not change the primary experiment, benchmark, model, or query text.
Anonymous read subqueries are allowed only after lexical screening and an actual
EXPLAIN summary classified as read-only by the restored Neo4j server.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import logging
from pathlib import Path
import time

BASE = Path(__file__).resolve().parent
PROTOCOL = BASE / "generated_read_query_replay_protocol_v1.json"
PORTS = {f"RAN{i}": 57686 + i for i in range(1, 6)}
ROW_CAP = 2000
TIMEOUT_SECONDS = 30
BLOCKED = frozenset({
    "CREATE", "MERGE", "INSERT", "SET", "DELETE", "DETACH", "REMOVE",
    "FOREACH", "LOAD", "CSV", "APOC", "DBMS", "DROP", "ALTER", "GRANT",
    "DENY", "REVOKE", "TERMINATE", "START", "STOP", "USE", "SHOW",
    "EXPLAIN", "PROFILE", "TRANSACTIONS",
})


class GuardRejected(ValueError):
    """Explicit lexical rejection; the original query is never submitted."""


class PlanRejected(ValueError):
    """Server did not classify the proposed query as an ordinary read."""


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def query_sha(query):
    if query is None:
        return None
    return hashlib.sha256(query.encode("utf-8")).hexdigest()


def tokens(query):
    """Lexical analysis only: no transformed string is ever executed."""
    if not isinstance(query, str) or not query or len(query.encode("utf-8")) > 1024 * 1024:
        raise GuardRejected("query must be a nonempty string of at most 1 MiB")
    found = []
    cursor = 0
    while cursor < len(query):
        char = query[cursor]
        if char.isspace():
            cursor += 1
            continue
        if query.startswith("//", cursor):
            cursor += 2
            while cursor < len(query) and query[cursor] not in "\r\n":
                cursor += 1
            continue
        if query.startswith("/*", cursor):
            depth = 1
            cursor += 2
            while cursor < len(query) and depth:
                if query.startswith("/*", cursor):
                    depth += 1
                    cursor += 2
                elif query.startswith("*/", cursor):
                    depth -= 1
                    cursor += 2
                else:
                    cursor += 1
            if depth:
                raise GuardRejected("unterminated block comment")
            continue
        if char in "'\"`":
            quote = char
            quoted_identifier = quote == "`"
            cursor += 1
            closed = False
            while cursor < len(query):
                if query[cursor] == "\\" and not quoted_identifier:
                    cursor += 2
                elif query[cursor] == quote:
                    if cursor + 1 < len(query) and query[cursor + 1] == quote:
                        cursor += 2
                    else:
                        cursor += 1
                        closed = True
                        break
                else:
                    cursor += 1
            if not closed:
                raise GuardRejected("unterminated string or quoted identifier")
            found.append(("ID" if quoted_identifier else "LITERAL", "opaque"))
            continue
        if char.isalpha() or char == "_":
            begin = cursor
            cursor += 1
            while cursor < len(query) and (query[cursor].isalnum() or query[cursor] == "_"):
                cursor += 1
            found.append(("WORD", query[begin:cursor].upper()))
            continue
        if char == "\\" or ord(char) < 32:
            raise GuardRejected("unsupported escape or control character outside a literal")
        found.append(("SYMBOL", char))
        cursor += 1
    return found


def screen_query(query):
    """Return the same string object on success; reject procedure/write syntax."""
    parts = tokens(query)
    if not parts:
        raise GuardRejected("empty query after comments")
    stack = []
    opening = {"(": ")", "[": "]", "{": "}"}
    for index, (kind, value) in enumerate(parts):
        if kind == "WORD" and value in BLOCKED:
            raise GuardRejected("prohibited token: " + value)
        if kind == "SYMBOL":
            if value == ";" and index != len(parts) - 1:
                raise GuardRejected("multiple or nonterminal statement separators")
            if value in opening:
                stack.append(opening[value])
            elif value in opening.values():
                if not stack or stack.pop() != value:
                    raise GuardRejected("unmatched delimiter")
        if kind == "WORD" and value == "CALL":
            following = index + 1
            if following < len(parts) and parts[following] == ("SYMBOL", "("):
                following += 1
                scope = []
                while following < len(parts) and parts[following] != ("SYMBOL", ")"):
                    scope.append(parts[following])
                    following += 1
                if following == len(parts):
                    raise GuardRejected("unterminated anonymous CALL scope")
                valid_scope = (not scope or scope == [("SYMBOL", "*")] or
                               all((entry[0] in {"WORD", "ID"} if position % 2 == 0
                                    else entry == ("SYMBOL", ","))
                                   for position, entry in enumerate(scope))
                               and len(scope) % 2 == 1)
                if not valid_scope:
                    raise GuardRejected("anonymous CALL scope must contain only variable names")
                following += 1
            if following >= len(parts) or parts[following] != ("SYMBOL", "{"):
                raise GuardRejected("procedure CALL is prohibited; only anonymous subqueries are allowed")
    if stack:
        raise GuardRejected("unmatched delimiter")
    return query


def require_read_plan(summary):
    if summary.query_type != "r" or not isinstance(summary.plan, dict):
        raise PlanRejected("EXPLAIN must provide a plan with query_type r")
    if summary.counters.contains_updates or summary.counters.contains_system_updates:
        raise PlanRejected("EXPLAIN reported updates")


def plan_operators(plan):
    """Record plan operators, excluding values and population estimates."""
    operators = []
    if isinstance(plan, dict):
        operators.append(plan.get("operatorType"))
        for child in plan.get("children", []):
            operators.extend(plan_operators(child))
    return operators


def owned_container_guard(wg):
    """No URI override and no adoption of a live/foreign database."""
    if wg not in PORTS:
        raise GuardRejected("working group must be RAN1..RAN5")
    from load_frozen_ttl_neo4j import guard_container, inspection
    manifest_path = BASE / "_frozen_ttl_v1" / wg.lower() / "import_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    name = f"kdd-db-frozen-v1-{wg.lower()}"
    if (manifest.get("status") != "restored_inventory_match"
            or manifest.get("working_group") != wg
            or manifest["target"]["container"] != name
            or manifest["target"]["bolt"] != f"bolt://127.0.0.1:{PORTS[wg]}"
            or manifest["target"].get("loopback_only") is not True):
        raise GuardRejected("restoration manifest does not identify the pinned isolated source")
    guard_container(inspection(name), name, PORTS[wg], manifest["run_uuid"],
                    manifest["source"]["sha256"])


def execute_in_transaction(tx, query):
    """Plan and run the exact query in one transaction; caller must rollback."""
    screen_query(query)
    summary = tx.run("EXPLAIN " + query).consume()
    require_read_plan(summary)
    plan_type = summary.query_type
    operators = plan_operators(summary.plan)
    result = tx.run(query)
    columns = list(result.keys())
    rows = []
    for record in result:
        if len(rows) == ROW_CAP:
            return {"status": "ROW_CAP", "rows": rows, "columns": columns,
                    "row_count_retained": len(rows), "truncated": True,
                    "plan_query_type": plan_type, "plan_operators": operators,
                    "execution_query_type": None, "execution_summary_complete": False}
        rows.append(record.data())
    actual = result.consume()
    if (actual.query_type != "r" or actual.counters.contains_updates
            or actual.counters.contains_system_updates):
        raise PlanRejected("executed query summary is not read-only")
    return {"status": "OK", "rows": rows, "columns": columns,
            "row_count_retained": len(rows), "truncated": False,
            "plan_query_type": plan_type, "plan_operators": operators,
            "execution_query_type": actual.query_type, "execution_summary_complete": True}


def run_query(wg, query):
    from neo4j import GraphDatabase, READ_ACCESS
    logging.getLogger("neo4j.notifications").setLevel(logging.ERROR)
    started, begin = utc(), time.monotonic()
    tx = None
    result = None
    try:
        screen_query(query)
        owned_container_guard(wg)
        with GraphDatabase.driver(f"bolt://127.0.0.1:{PORTS[wg]}", auth=None,
                                  connection_timeout=5, connection_acquisition_timeout=5,
                                  max_transaction_retry_time=0) as driver:
            with driver.session(database="neo4j", default_access_mode=READ_ACCESS,
                                fetch_size=100) as session:
                tx = session.begin_transaction(timeout=TIMEOUT_SECONDS)
                try:
                    result = execute_in_transaction(tx, query)
                finally:
                    tx.rollback()
        result["error_class"] = None
    except Exception as exc:
        status = ("GUARD_REJECTED" if isinstance(exc, GuardRejected) else
                  "PLAN_REJECTED" if isinstance(exc, PlanRejected) else "ERROR")
        result = {"status": status, "error_class": type(exc).__name__,
                  "rows": [], "columns": [], "row_count_retained": 0,
                  "truncated": False}
    result.update({"started_utc": started, "finished_utc": utc(),
                   "elapsed_s": round(time.monotonic() - begin, 4),
                   "query_sha256": query_sha(query), "query_modified": False,
                   "rollback_requested": tx is not None})
    return result


def validate_inputs(query_path, completion_path, primary_path, protocol):
    """No database access before all-36 completeness and artifact pins pass."""
    completion = json.loads(Path(completion_path).read_text())
    if (completion.get("status") != "complete"
            or completion.get("expected_n") != 36 or completion.get("completed_n") != 36
            or completion.get("query_manifest_sha256") != sha(query_path)
            or completion.get("primary_artifact_sha256") != sha(primary_path)):
        raise ValueError("complete primary artifact and all-36 extraction attestation required")
    payload = json.loads(Path(query_path).read_text())
    items = payload.get("items")
    expected = {item["id"]: item["wg"] for item in protocol["eligible_items"]}
    if not isinstance(items, list) or len(items) != 36:
        raise ValueError("exactly all 36 saved queries are required")
    observed = {}
    for item in items:
        if (set(item) != {"id", "wg", "query"} or item["id"] in observed
                or not (isinstance(item["query"], str) or item["query"] is None)):
            raise ValueError("query entries require unique ID, WG, and unmodified saved query string")
        observed[item["id"]] = item["wg"]
    if observed != expected:
        raise ValueError("query cohort differs from the prospectively fixed all-36 eligible cohort")
    primary = json.loads(Path(primary_path).read_text())
    if primary.get("kind") == "complete byte-preserved primary structured receipt manifest":
        by_id = {record["id"]: record for record in primary["items"]}
        if set(by_id) != set(expected) or len(primary["items"]) != 36:
            raise ValueError("primary receipt manifest does not account for exactly all 36")
        for item in items:
            if (query_sha(item["query"]) != by_id[item["id"]]["generated_query_sha256"]
                    or item["wg"] != by_id[item["id"]]["wg"]):
                raise ValueError("query extraction differs from preserved primary receipt")
            if item["query"] is None and by_id[item["id"]]["generation_abstain"] is not True:
                raise ValueError("null saved query requires a primary generation abstention")
    return sorted(items, key=lambda item: item["id"])


def verify_primary_receipts(primary_path, primary_dir):
    primary = json.loads(Path(primary_path).read_text())
    if primary.get("kind") != "complete byte-preserved primary structured receipt manifest":
        raise ValueError("uniform saved-receipt manifest required")
    expected_names = {record["receipt_basename"] for record in primary["items"]}
    if {path.name for path in Path(primary_dir).glob("*.json")} != expected_names:
        raise ValueError("primary receipt directory differs from complete frozen manifest")
    for record in primary["items"]:
        if Path(record["receipt_basename"]).name != record["receipt_basename"]:
            raise ValueError("receipt basename must not contain a path")
        if sha(Path(primary_dir) / record["receipt_basename"]) != record["primary_receipt_sha256"]:
            raise ValueError("primary receipt changed since input freeze")
    return {record["id"]: record for record in primary["items"]}


def check_protocol(protocol):
    if (protocol["eligible_n"] != 36 or protocol["guard"]["allowed_wg_ports"] != PORTS
            or protocol["guard"]["transaction_timeout_seconds"] != TIMEOUT_SECONDS
            or protocol["guard"]["row_cap"] != ROW_CAP
            or set(protocol["guard"]["blocked_tokens"]) != BLOCKED):
        raise ValueError("implementation differs from the fixed replay protocol")
    for name, digest in protocol["input_pins"].items():
        if sha(BASE / name) != digest:
            raise ValueError("pinned input changed: " + name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", required=True, type=Path)
    parser.add_argument("--completion", required=True, type=Path)
    parser.add_argument("--primary", required=True, type=Path)
    parser.add_argument("--primary-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("refusing to overwrite any existing result")
    protocol = json.loads(PROTOCOL.read_text())
    check_protocol(protocol)
    items = validate_inputs(args.queries, args.completion, args.primary, protocol)
    primary_receipts = verify_primary_receipts(args.primary, args.primary_dir)
    adapter_protocol = BASE / "generated_read_query_replay_adapter_protocol_v1.json"
    adapter = json.loads(adapter_protocol.read_text())
    for name, digest in adapter["code_pins"].items():
        if sha(BASE / name) != digest:
            raise ValueError("fixed replay implementation changed: " + name)
    from execute_frozen_reference_gold import source_guard
    groups = sorted({item["wg"] for item in items})
    for wg in groups:
        owned_container_guard(wg)
    guards = [source_guard(wg) for wg in groups]
    payload = {"version": 1, "kind": "uniform secondary saved-query replay after execution-guard repair",
               "started_utc": utc(), "protocol_sha256": sha(PROTOCOL),
               "runner_sha256": sha(__file__), "primary_artifact_sha256": sha(args.primary),
               "query_manifest_sha256": sha(args.queries), "completion_attestation_sha256": sha(args.completion),
               "adapter_protocol_sha256": sha(adapter_protocol),
               "synthetic_validation_sha256": sha(BASE / adapter["synthetic_validation_file"]),
               "source_guards_before": guards, "row_cap": ROW_CAP,
               "transaction_timeout_seconds": TIMEOUT_SECONDS,
               "primary_artifact_modified": False, "query_rewriting": False,
               "model_calls": 0, "human_expert_validation_n": 0,
               "original_benchmark_modified": False, "items": []}
    for item in items:
        receipt = primary_receipts[item["id"]]
        if receipt["generation_abstain"] is True:
            execution = {"status": "GENERATION_ABSTAIN", "error_class": None,
                         "rows": [], "columns": [], "row_count_retained": 0,
                         "truncated": False, "query_sha256": query_sha(item["query"]),
                         "query_modified": False, "rollback_requested": False}
        else:
            execution = run_query(item["wg"], item["query"])
        payload["items"].append({**item, "generation_abstain": receipt["generation_abstain"],
                                 "primary_receipt_sha256": receipt["primary_receipt_sha256"],
                                 "execution": execution})
        print(item["id"], execution["status"], flush=True)
    payload["source_guards_after"] = [source_guard(wg) for wg in groups]
    verify_primary_receipts(args.primary, args.primary_dir)
    if (payload["source_guards_before"] != payload["source_guards_after"]
            or sha(args.primary) != payload["primary_artifact_sha256"]
            or sha(args.queries) != payload["query_manifest_sha256"]):
        raise RuntimeError("source or primary/query artifact changed during execution; no output written")
    payload["same_count_external_property_mutations_detected"] = False
    payload["finished_utc"] = utc()
    with args.output.open("x") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print("output_sha256", sha(args.output))


if __name__ == "__main__":
    main()
