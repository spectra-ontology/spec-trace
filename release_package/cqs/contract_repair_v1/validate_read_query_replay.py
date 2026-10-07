#!/usr/bin/env python3
"""Record synthetic guard tests and actual plan types, without model queries."""
import argparse
import json
from pathlib import Path
import unittest

import replay_generated_read_queries as replay
import test_replay_generated_read_queries as tests


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("refusing to overwrite synthetic validation")
    protocol = json.loads(replay.PROTOCOL.read_text())
    replay.check_protocol(protocol)
    suite = unittest.defaultTestLoader.loadTestsFromModule(tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit("unit checks failed; no validation artifact written")
    from neo4j import GraphDatabase, READ_ACCESS
    import neo4j
    from execute_frozen_reference_gold import source_guard
    replay.owned_container_guard("RAN3")
    before = source_guard("RAN3")
    benign = [
        ("plain_return", "RETURN 1 AS x"),
        ("anonymous_importing_with", "WITH 7 AS x CALL { WITH x RETURN x + 1 AS y } RETURN y"),
        ("anonymous_empty_scope", "CALL () { RETURN 1 AS x } RETURN x"),
        ("anonymous_variable_scope", "WITH 7 AS x CALL (x) { RETURN x + 1 AS y } RETURN y"),
        ("source_plan", "MATCH (n:Meeting) RETURN count(n) AS x"),
        ("literal_keyword", "RETURN 'CREATE CALL dbms' AS x"),
    ]
    observed = []
    for name, query in benign:
        execution = replay.run_query("RAN3", query)
        if execution["status"] != "OK" or execution["plan_query_type"] != "r":
            raise RuntimeError("synthetic read did not pass both gates: " + name)
        observed.append({"name": name, "query": query, "status": execution["status"],
                         "plan_query_type": execution["plan_query_type"],
                         "execution_query_type": execution["execution_query_type"],
                         "plan_operators": execution["plan_operators"],
                         "rollback_requested": execution["rollback_requested"],
                         "result_values_exported": False})
    blocked = [
        ("mutation", "CREATE (n:_ReadReplaySynthetic) RETURN n"),
        ("nested_mutation", "CALL { CREATE (n:_ReadReplaySynthetic) RETURN n } RETURN n"),
        ("csv", "LOAD CSV FROM 'file:///never_read.csv' AS x RETURN x"),
        ("procedure", "CALL db.labels() YIELD label RETURN label"),
        ("apoc", "CALL apoc.help('x')"),
        ("dbms", "CALL dbms.components()"),
    ]
    for name, query in blocked:
        execution = replay.run_query("RAN3", query)
        if execution["status"] != "GUARD_REJECTED" or execution["rollback_requested"]:
            raise RuntimeError("synthetic forbidden query reached a transaction: " + name)
        observed.append({"name": name, "query": query, "status": execution["status"],
                         "submitted_to_server": False})
    # EXPLAIN ONLY, deliberately bypassing the lexical screen for a synthetic
    # write so the server classifier is observed. The write is never executed.
    write = "CREATE (n:_ReadReplaySynthetic) RETURN n"
    with GraphDatabase.driver("bolt://127.0.0.1:57689", auth=None) as driver:
        with driver.session(database="neo4j", default_access_mode=READ_ACCESS) as session:
            tx = session.begin_transaction(timeout=30)
            try:
                summary = tx.run("EXPLAIN " + write).consume()
                if summary.query_type not in {"w", "rw"} or summary.counters.contains_updates:
                    raise RuntimeError("server write-plan classification unexpected")
                try:
                    replay.require_read_plan(summary)
                except replay.PlanRejected:
                    pass
                else:
                    raise RuntimeError("server write plan was accepted")
                observed.append({"name": "write_plan_only", "query": write,
                                 "plan_query_type": summary.query_type,
                                 "plan_operators": replay.plan_operators(summary.plan),
                                 "actual_write_executed": False,
                                 "read_gate_rejected": True})
            finally:
                tx.rollback()
    cap = replay.run_query("RAN3", "UNWIND range(1, 2001) AS x RETURN x")
    if cap["status"] != "ROW_CAP" or cap["row_count_retained"] != 2000:
        raise RuntimeError("actual row-cap detection failed")
    observed.append({"name": "row_cap", "status": cap["status"],
                     "row_count_retained": cap["row_count_retained"],
                     "plan_query_type": cap["plan_query_type"],
                     "rollback_requested": cap["rollback_requested"],
                     "result_values_exported": False})
    after = source_guard("RAN3")
    if before != after:
        raise RuntimeError("source guard changed during synthetic validation")
    payload = {"version": 1, "kind": "synthetic execution guard validation; no scientific query replay",
               "created_utc": replay.utc(), "protocol_sha256": replay.sha(replay.PROTOCOL),
               "code_pins": {name: replay.sha(replay.BASE / name) for name in
                             ["replay_generated_read_queries.py", "test_replay_generated_read_queries.py",
                              "validate_read_query_replay.py"]},
               "driver_version": neo4j.__version__, "restored_server_version": "5.26.0",
               "unit_tests_passed": result.testsRun, "synthetic_checks": observed,
               "source_guard_before": before, "source_guard_after": after,
               "model_queries_read": 0, "model_calls": 0, "correctness_scores_computed": 0,
               "human_expert_validation_n": 0,
               "same_count_external_property_mutations_detected": False,
               "official_documentation": protocol["official_documentation"]}
    with args.output.open("x") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print("validation_sha256", replay.sha(args.output))


if __name__ == "__main__":
    main()
