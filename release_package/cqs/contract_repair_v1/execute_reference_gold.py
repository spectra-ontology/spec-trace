#!/usr/bin/env python3
"""Execute prospective reference tasks as bounded, read-only graph queries.

New source-limited gold is separate from SpectraCQ v2.0 and from model outputs.
This script does not certify domain truth, original snapshot identity, or causal
effects. Supply NEO4J_PASSWORD through the environment; credentials are neither
written to output nor accepted on the command line. Neo4j is the sole optional
dependency. Completed query rows, errors, truncation, and source checks remain
visible. Files are created exclusively; an existing result is never replaced.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import time

PORTS = {f"RAN{i}": 7686 + i for i in range(1, 6)}
FORBIDDEN = re.compile(r"\b(?:CREATE|MERGE|SET|REMOVE|DELETE|DETACH|DROP|LOAD|CSV|CALL|FOREACH|SHOW|USE)\b|(?:apoc|dbms)\s*\.", re.I)


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe_query(query):
    if not isinstance(query, str) or not query.strip():
        raise ValueError("empty query")
    # Strip comments and string literals for the keyword guard. This is a
    # conservative allow-list guard, not a complete Cypher parser or permission.
    skeleton = re.sub(r"'(?:\\.|''|[^'\\])*'|\"(?:\\.|\"\"|[^\"\\])*\"|/\*[\s\S]*?\*/|//[^\n]*", " ", query)
    if FORBIDDEN.search(skeleton) or ";" in skeleton.rstrip().rstrip(";"):
        raise ValueError("query rejected by read-only guard")
    if not re.match(r"^\s*(?:MATCH|OPTIONAL\s+MATCH|WITH|RETURN)\b", skeleton, re.I):
        raise ValueError("unsupported read query prefix")
    return query.strip().rstrip(";")


def run_query(wg, query, *, row_cap=2000, timeout_s=30):
    from neo4j import GraphDatabase, READ_ACCESS
    clean = safe_query(query)
    password = os.environ.get("NEO4J_PASSWORD")
    if not password:
        raise RuntimeError("NEO4J_PASSWORD unavailable")
    driver = GraphDatabase.driver(f"bolt://localhost:{PORTS[wg]}", auth=("neo4j", password))
    started = utc()
    t0 = time.monotonic()
    try:
        with driver.session(default_access_mode=READ_ACCESS) as session:
            with session.begin_transaction(timeout=timeout_s) as tx:
                result = tx.run(clean)
                columns = list(result.keys())
                rows = []
                capped = False
                for record in result:
                    if len(rows) == row_cap:
                        capped = True
                        break
                    rows.append(record.data())
                # Roll back even read queries. Driver read routing and this
                # guard are additional safeguards, not proof of server roles.
                tx.rollback()
        return {"status": "ROW_CAP" if capped else "OK", "rows": rows,
                "columns": columns, "row_count_retained": len(rows),
                "truncated": capped, "started_utc": started,
                "finished_utc": utc(), "elapsed_s": round(time.monotonic() - t0, 4)}
    except Exception as exc:
        # Detailed Neo4j errors can contain URLs or connection configuration.
        # Preserve the class without emitting credentials in public artifacts.
        return {"status": "ERROR", "error_class": type(exc).__name__,
                "rows": [], "columns": [], "row_count_retained": 0,
                "truncated": False, "started_utc": started,
                "finished_utc": utc(), "elapsed_s": round(time.monotonic() - t0, 4)}
    finally:
        driver.close()


def valid_value(value, field):
    if value is None:
        return field.get("nullable", False) or field["type"] == "null"
    kind = field["type"]
    return ((kind == "string" and isinstance(value, str)) or
            (kind == "integer" and type(value) is int) or
            (kind == "number" and type(value) in (int, float)) or
            (kind == "boolean" and type(value) is bool) or kind == "json")


def execute_tasks(taskset):
    records = []
    for item in taskset["items"]:
        result = run_query(item["wg"], item["reference_query"])
        fields = item["required_fields"]
        typed = (result["status"] == "OK" and
                 all(all(f["name"] in r and valid_value(r[f["name"]], f)
                         for f in fields) for r in result["rows"]))
        records.append({"id": item["id"], "wg": item["wg"],
                        "reference_query_sha256": hashlib.sha256(item["reference_query"].encode()).hexdigest(),
                        "required_types_match": typed, "eligible": typed,
                        "execution": result})
        print(item["id"], result["status"], result["row_count_retained"], "typed", typed, flush=True)
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("taskset", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing to overwrite an existing gold execution")
    taskset = json.loads(args.taskset.read_text())
    payload = {"kind": "new reference-query execution, not a model run",
               "taskset_sha256": sha(args.taskset), "code_sha256": sha(__file__),
               "started_utc": utc(), "row_cap": 2000, "timeout_s": 30,
               "domain_expert_validation": False, "original_snapshot_identity_verified": False,
               "graph_atomic_snapshot": False,
               "items": execute_tasks(taskset), "finished_utc": utc()}
    with args.output.open("x") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print("output_sha256", sha(args.output))


if __name__ == "__main__":
    main()
