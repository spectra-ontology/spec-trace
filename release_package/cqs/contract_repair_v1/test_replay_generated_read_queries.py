"""Synthetic checks; no model queries, answer keys, or correctness scores."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import replay_generated_read_queries as replay


def summary(kind="r", plan=True, updates=False):
    return SimpleNamespace(query_type=kind,
                           plan={"operatorType": "ProduceResults"} if plan else None,
                           counters=SimpleNamespace(contains_updates=updates,
                                                    contains_system_updates=False))


class Result:
    def __init__(self, rows, info):
        self.rows, self.info = rows, info

    def keys(self):
        return ["x"]

    def __iter__(self):
        for row in self.rows:
            yield SimpleNamespace(data=lambda row=row: row)

    def consume(self):
        return self.info


class Transaction:
    def __init__(self, query, rows, kind="r"):
        self.query, self.rows, self.kind = query, rows, kind
        self.calls = []

    def run(self, query):
        self.calls.append(query)
        if query.startswith("EXPLAIN "):
            return Result([], summary(self.kind))
        return Result(self.rows, summary())


class GuardTests(unittest.TestCase):
    def test_benign_queries_preserve_same_string(self):
        queries = [
            " RETURN 1 AS x \n", "RETURN 'CREATE CALL dbms' AS x",
            'RETURN "DELETE /* */" AS x', "RETURN 'a\\\'b' AS x",
            "RETURN 1 AS `SET`", "RETURN {x: 1} AS x; // trailing comment",
            "// CALL db.labels()\nRETURN 1 AS x",
            "/* CREATE /* SET */ DELETE */ RETURN 1 AS x",
            "WITH 7 AS x CALL { WITH x RETURN x + 1 AS y } RETURN y",
            "CALL { CALL { RETURN 1 AS x } RETURN x } RETURN x",
            "CALL () { RETURN 1 AS x } RETURN x",
            "WITH 1 AS x CALL (x) { RETURN x + 1 AS y } RETURN y",
            "WITH 1 AS x, 2 AS y CALL (x,y) { RETURN x+y AS z } RETURN z",
            "WITH 1 AS x CALL (*) { RETURN x+1 AS y } RETURN y",
            "CALL (`a``b`) { RETURN 1 AS x } RETURN x",
        ]
        for query in queries:
            with self.subTest(query=query):
                self.assertIs(replay.screen_query(query), query)

    def test_mutation_csv_procedure_and_malformed_rejections(self):
        queries = [
            "CREATE (n)", "MATCH(n) SET n.x=1 RETURN n", "MERGE(n)",
            "MATCH(n) DETACH DELETE n", "CALL { CREATE(n) RETURN n } RETURN n",
            "LOAD CSV FROM 'file:///x.csv' AS x RETURN x",
            "CALL db.labels() YIELD label RETURN label", "CALL `db`.`labels`()",
            "CALL apoc.cypher.run('RETURN 1',{})", "RETURN apoc.version()",
            "CALL dbms.components()", "CALL { RETURN 1 AS x } IN TRANSACTIONS",
            "USE other RETURN 1", "RETURN 1; RETURN 2", "RETURN 1;;",
            "PROFILE RETURN 1", "EXPLAIN RETURN 1", "SHOW DATABASES",
            "RETURN 'unclosed", 'RETURN "unclosed', "RETURN `unclosed",
            "RETURN 1 /* unclosed", "RETURN (1]", "RETURN {x:1", "RETURN 1\\x",
            "CALL (x AS y) { RETURN 1 AS z } RETURN z",
            "CALL (x,) { RETURN 1 AS z } RETURN z", "CALL (1) { RETURN 1 }",
            "CALL (`db.labels`)()", "// only comment", "", "RETURN \x00",
        ]
        for query in queries:
            with self.subTest(query=query):
                with self.assertRaises(replay.GuardRejected):
                    replay.screen_query(query)

    def test_every_nonread_or_missing_plan_rejected(self):
        replay.require_read_plan(summary())
        for kind in ["rw", "w", "s", None]:
            with self.subTest(kind=kind), self.assertRaises(replay.PlanRejected):
                replay.require_read_plan(summary(kind))
        for info in [summary(plan=False), summary(updates=True)]:
            with self.assertRaises(replay.PlanRejected):
                replay.require_read_plan(info)

    def test_original_query_executes_exactly_after_plan(self):
        query = " \nCALL { RETURN 1 AS x } RETURN x; // exact bytes\n"
        tx = Transaction(query, [{"x": 1}])
        result = replay.execute_in_transaction(tx, query)
        self.assertEqual(tx.calls, ["EXPLAIN " + query, query])
        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["plan_query_type"], "r")

    def test_no_execution_after_nonread_plan(self):
        tx = Transaction("RETURN 1 AS x", [], kind="rw")
        with self.assertRaises(replay.PlanRejected):
            replay.execute_in_transaction(tx, tx.query)
        self.assertEqual(tx.calls, ["EXPLAIN " + tx.query])

    def test_exact_2000_rows_valid_but_2001_is_explicit_cap(self):
        for n, expected in [(0, "OK"), (2000, "OK"), (2001, "ROW_CAP")]:
            with self.subTest(n=n):
                tx = Transaction("RETURN 1 AS x", [{"x": i} for i in range(n)])
                result = replay.execute_in_transaction(tx, tx.query)
                self.assertEqual(result["status"], expected)
                self.assertEqual(result["row_count_retained"], min(n, 2000))

    def test_partial_or_changed_cohort_cannot_execute(self):
        protocol = json.loads(replay.PROTOCOL.read_text())
        items = [{**entry, "query": "RETURN 1 AS x"} for entry in protocol["eligible_items"]]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            primary = path / "primary.json"
            primary.write_text('{"complete": true}')
            query_path, completion = path / "queries.json", path / "completion.json"
            for candidate, valid in [(items, True), (items[:-1], False),
                                     (items[:-1] + [items[0]], False),
                                     ([{**items[0], "wg": "RAN9"}] + items[1:], False)]:
                query_path.write_text(json.dumps({"items": candidate}))
                completion.write_text(json.dumps({"status": "complete", "expected_n": 36,
                                                 "completed_n": 36,
                                                 "query_manifest_sha256": replay.sha(query_path),
                                                 "primary_artifact_sha256": replay.sha(primary)}))
                if valid:
                    self.assertEqual(len(replay.validate_inputs(query_path, completion, primary, protocol)), 36)
                else:
                    with self.assertRaises(ValueError):
                        replay.validate_inputs(query_path, completion, primary, protocol)
            query_path.write_text(json.dumps({"items": items}))
            completion.write_text(json.dumps({"status": "running", "expected_n": 36, "completed_n": 35}))
            with self.assertRaises(ValueError):
                replay.validate_inputs(query_path, completion, primary, protocol)


if __name__ == "__main__":
    unittest.main(verbosity=2)
