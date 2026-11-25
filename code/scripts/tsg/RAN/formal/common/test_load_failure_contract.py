#!/usr/bin/env python3
"""test_load_failure_contract.py — 배치 오류와 원문 의제 보존을 검증한다.

Spec: Phase-1 재적재 정합화 및 배치 오류 전파 계약.
Ontology: 현재 선언과 다른 간선 정리; 타 생성 코드의 backfill 보존.
Cycle: 실제 함수 AST → 합성 APOC 결과/질의 수집 → 오류와 범위 확인.
배경: 결과 행으로 보고된 배치 실패와 null 원본 자료의 선언을 조용히 넘기지 않는다.
사용: python3 -B scripts/tsg/RAN/formal/common/test_load_failure_contract.py
LLM 호출·DB·모델·네트워크: 없음. 메모리 세션만 사용한다.
"""
import ast
import contextlib
from copy import deepcopy
import io
import json
import re
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import uuid

import agenda_retention
import agenda_number
from attachment_accounting import AttachAccounting

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())


class Record(dict):
    def data(self):
        return dict(self)


class Rows(list):
    def single(self):
        return self[0]


class Session:
    def __init__(self, rows=None):
        self.rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def run(self, query, *args, **kwargs):
        if self.rows is not None:
            return Rows(self.rows)
        if "labels(n)[0]" in query:
            return Rows([{"label": "Tdoc", "count": 1}])
        if "type(r) AS relType" in query:
            return Rows([{"relType": "HAS_CONTACT", "count": 1}])
        if "count(n) AS cnt" in query:
            return Rows([{"cnt": 1}])
        return Rows()

    def execute_write(self, callback, *args, **kwargs):
        return callback(self, *args, **kwargs)


class Driver:
    def __init__(self, rows=None):
        self.rows = rows

    def session(self, *args, **kwargs):
        return Session(self.rows)

    def close(self):
        pass


class LoadFailureTests(unittest.TestCase):
    def source(self, wg):
        return ROOT / f"scripts/tsg/RAN/formal/RAN{wg}/phase-1/neo4j/01_load_kg.py"

    def function(self, wg, name, env):
        path = self.source(wg)
        node = next(n for n in ast.parse(path.read_text()).body
                    if isinstance(n, ast.FunctionDef) and n.name == name)
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), env)
        return env[name]

    def test_apoc_errors_raise_and_success_returns(self):
        cases = [{"failedBatches": 1, "errorMessages": {}},
                 {"failedBatches": 0, "errorMessages": {"synthetic failure": 1}},
                 {"total": 9}]
        for wg in range(1, 6):
            run = self.function(wg, "run_query", {"time": time})
            for case in cases:
                with self.subTest(wg=wg, case=case), self.assertRaises(RuntimeError):
                    run(Driver([Record(case)]), "CALL apoc.periodic.iterate(...)")
            with self.subTest(wg=wg, empty=True), self.assertRaises(RuntimeError):
                run(Driver([]), "CALL apoc.periodic.iterate(...)")
            with contextlib.redirect_stdout(io.StringIO()):
                records, _ = run(Driver([Record(failedBatches=0, errorMessages={}, total=9)]),
                                 "CALL apoc.periodic.iterate(...)")
                self.assertEqual(records[0]["total"], 9)
                run(Driver([Record(total=9)]), "RETURN 9 AS total")

    def test_emitted_batch_queries_and_owned_null_references(self):
        for wg in range(1, 6):
            with self.subTest(wg=wg), contextlib.redirect_stdout(io.StringIO()):
                queries = []
                def capture(driver, query, *args, **kwargs):
                    queries.append(query)
                    return [], 0
                env = {"time": time, "Path": Path, "sys": sys, "json": json,
                       "GraphDatabase": type("GraphDatabase", (), {"driver": staticmethod(lambda *a, **k: Driver())}),
                       "URI": "synthetic", "AUTH": None, "JSONLD_BASE": "synthetic", "COMPANIES_JSONLD": "synthetic",
                       "SOURCE_FIRST_INVERSE": {"IS_REVISION_OF": "_isRevisionOf"}, "CURRENT_TARGET_ONLY": {"SUBMITTED_BY"},
                       "run_query": capture, "current_company_ids": lambda driver: ["company/current"],
                       "remove_orphan_contacts": lambda driver: 0, "report_reference_misses": lambda *args: 0,
                       "__file__": str(self.source(wg))}
                revision = SimpleNamespace(preflight_revision_document=lambda *args: {},
                                           load_evidence=lambda *args: None)
                helpers = {node.name for node in ast.parse(self.source(wg).read_text()).body
                           if isinstance(node, ast.FunctionDef)}
                for helper in ("load_spec_release_references", "_close_driver"):
                    if helper in helpers:
                        self.function(wg, helper, env)
                with patch.dict(sys.modules, {"tdoc_revision_evidence": revision}):
                    self.function(wg, "main", env)()
                self.assertTrue(any("MERGE (r:Release" in query for query in queries))
                self.assertTrue(any("MERGE (s:Spec" in query for query in queries))
                batches = [q for q in queries if "apoc.periodic.iterate" in q]
                self.assertGreater(len(batches), 15)
                for query in batches:
                    self.assertIn("YIELD batches, total, failedBatches, errorMessages", query)
                    self.assertIn("RETURN batches, total, failedBatches, errorMessages", query)
                load = next(q for q in batches if "MERGE (t:Tdoc" in q)
                self.assertIn("t._p1ReferenceSource = true", load)
                contact = next(q for q in batches if "r:HAS_CONTACT" in q and "DELETE r" in q)
                self.assertIn("coalesce(t._p1ReferenceSource, false) OR t._hasContact IS NOT NULL", contact)
                self.assertIn("CASE WHEN t._hasContact IS NULL THEN []", contact)
                meeting = next(q for q in batches if "r:PRESENTED_AT" in q and "DELETE r" in q)
                self.assertIn("CASE WHEN t._presentedAt IS NULL THEN []", meeting)
                if wg == 1:
                    self.assertIn("NOT m.id IN coalesce(t._reportedAt, [])", meeting)


class ResolutionReferenceTests(unittest.TestCase):
    def test_shared_agenda_split_preserves_unknown_and_legacy_references(self):
        for value, expected in (("121-bis-UNKNOWN", ("121-bis", "UNKNOWN")),
                                ("105-UNKNOWN", ("105", "UNKNOWN")),
                                ("121-misc", ("121", "misc")),
                                ("121", (None, None))):
            with self.subTest(value=value):
                self.assertEqual(agenda_number.split_meeting_agenda(value), expected)

    def test_agenda_parameters_preserve_hyphenated_meeting_identifiers(self):
        for number in range(1, 6):
            path = ROOT / f"scripts/tsg/RAN/formal/RAN{number}/phase-2/neo4j/01_load_decisions.py"
            tree = ast.parse(path.read_text())
            captured = []
            def run(query, **params):
                captured.append(params)
                return Rows([Record(match_type="miss")])
            env = {"RUN": "synthetic-run", "re": re, "AGENDA_NUMBER": agenda_number.NUMBER,
                   "ATTACHMENTS": SimpleNamespace(run=lambda *args, **kwargs: None)}
            for node in tree.body:
                if ((isinstance(node, ast.ImportFrom) and node.module == "agenda_number")
                        or (isinstance(node, ast.FunctionDef)
                            and node.name in ("_split_meeting_agenda", "_normalize_canonical_meeting",
                                              "create_resolution_relationships"))):
                    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), env)
            for meeting in ("121", "121-bis", "114bis-e"):
                for agenda in ("8.1", "11.4.6a"):
                    with self.subTest(wg=number, meeting=meeting, agenda=agenda):
                        captured.clear()
                        resolution = {"resolutionId": "resolution/synthetic",
                                      "resolutionBelongsTo": f"tdoc:agenda/{meeting}-{agenda}"}
                        with contextlib.redirect_stdout(io.StringIO()):
                            missing = env["create_resolution_relationships"](SimpleNamespace(run=run), [resolution])
                        self.assertEqual(missing, [("resolution/synthetic", meeting, agenda)])
                        self.assertEqual([(p["meetingNum"], p["agendaItem"]) for p in captured],
                                         [(meeting, agenda)])

    def test_references_match_scalar_tdoc_numbers_for_every_working_group(self):
        for number in range(1, 6):
            wg = f"RAN{number}"
            path = ROOT / f"scripts/tsg/RAN/formal/{wg}/phase-2/neo4j/01_load_decisions.py"
            node = next(node for node in ast.parse(path.read_text()).body
                        if isinstance(node, ast.FunctionDef)
                        and node.name == "create_references_relationships")
            captured = []
            env = {"RUN": "synthetic-run", "ATTACHMENTS": SimpleNamespace(
                run=lambda tx, relation, query, **params: captured.append((relation, query, params)))}
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), env)
            tdoc_number = f"R{number}-2000001"
            for references in (f"tdoc:{tdoc_number}", [f"tdoc:{tdoc_number}"]):
                with self.subTest(wg=wg, references=references):
                    captured.clear()
                    env[node.name](object(), [{"resolutionId": "resolution/synthetic", "references": references}])
                    self.assertEqual(len(captured), 1)
                    relation, query, params = captured[0]
                    self.assertEqual(relation, "REFERENCES")
                    self.assertIn("MATCH (t:Tdoc {tdocNumber: $tdocNum})", query)
                    self.assertEqual(params, {"resolutionId": "resolution/synthetic",
                                              "tdocNum": tdoc_number, "run": "synthetic-run"})


class AgendaTransaction:
    """Synthetic transaction state; a failed callback restores nodes and edges."""
    def __init__(self, nodes=None, during_query=None):
        self.nodes = deepcopy(nodes or [])
        self.edges = ["stale"]
        self.queries = []
        self.during_query = during_query
        self.commits = 0
        self.rollbacks = 0

    def execute_write(self, callback):
        before = deepcopy((self.nodes, self.edges))
        try:
            value = callback(self)
        except BaseException:
            self.nodes, self.edges = before
            self.rollbacks += 1
            raise
        self.commits += 1
        return value

    def run(self, query, **params):
        self.queries.append((query, params))
        if "a._createdBy = 'phase-2-backfill' AND NOT (a)--()" not in query:
            raise AssertionError("producer and incident-edge restrictions missing")
        if "coalesce(a.id, '') IN $canonical_ids" not in query:
            raise AssertionError("canonical id protection missing")
        if "coalesce(a.meetingNumber, ''), coalesce(a.agendaNumber, '')] IN $canonical_keys" not in query:
            raise AssertionError("canonical composite protection missing")
        retained = []
        for node in self.nodes:
            protected = (node.get("id") in params["canonical_ids"]
                         or [node.get("meetingNumber", ""), node.get("agendaNumber", "")]
                         in params["canonical_keys"])
            if node.get("_createdBy") != "phase-2-backfill" or node.get("degree", 0) or protected:
                retained.append(node)
        swept = len(self.nodes) - len(retained)
        self.nodes = retained
        if self.during_query:
            self.during_query()
        return Rows([Record(swept=swept)])


class AgendaRetentionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def path(self, wg="RAN1"):
        return agenda_retention.canonical_agenda_path(self.root, wg)

    def write_source(self, wg="RAN1", rows=None):
        if rows is None:
            rows = [{"@id": f"tdoc:agenda/{wg}-1", "@type": "tdoc:AgendaItem",
                     "tdoc:meetingNumber": wg, "tdoc:agendaNumber": "1"}]
        path = self.path(wg)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"@graph": rows}), encoding="utf-8")
        return rows

    def wrapper(self, wg):
        path = ROOT / f"scripts/tsg/RAN/formal/{wg}/phase-2/neo4j/01_load_decisions.py"
        tree = ast.parse(path.read_text())
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                        and node.name == "sweep_orphan_backfill_agenda_items")
        env = {"PROJECT_ROOT": self.root,
               "sweep_unsupported_agendas": agenda_retention.sweep_unsupported_agendas}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), "exec"), env)
        return env[function.name]

    def test_all_five_loaders_preserve_either_source_identity_and_other_owners(self):
        for number in range(1, 6):
            wg = f"RAN{number}"
            with self.subTest(wg=wg), contextlib.redirect_stdout(io.StringIO()):
                row = self.write_source(wg)[0]
                canonical_id = {"name": "canonical-id", "id": row["@id"],
                                "meetingNumber": "drift", "agendaNumber": "drift", "_createdBy": "phase-2-backfill"}
                canonical_key = {"name": "canonical-composite", "meetingNumber": wg, "agendaNumber": "1",
                                 "_createdBy": "phase-2-backfill"}
                unrelated = {"name": "unsupported", "meetingNumber": "old", "agendaNumber": "9",
                             "_createdBy": "phase-2-backfill"}
                other_owner = {"name": "other-producer", "_createdBy": "phase-6-backfill"}
                connected = {"name": "connected", "degree": 1, "_createdBy": "phase-2-backfill"}
                tx = AgendaTransaction([canonical_id, canonical_key, unrelated, other_owner, connected])
                self.assertEqual(self.wrapper(wg)(tx), 1)
                self.assertEqual([node["name"] for node in tx.nodes],
                                 ["canonical-id", "canonical-composite", "other-producer", "connected"])
                self.assertEqual(tx.queries[0][1]["canonical_ids"], [row["@id"]])
                self.assertEqual(tx.queries[0][1]["canonical_keys"], [[wg, "1"]])

    def test_main_cleanup_calls_the_guard_inside_transaction_for_every_wg(self):
        for number in range(1, 6):
            wg = f"RAN{number}"
            path = ROOT / f"scripts/tsg/RAN/formal/{wg}/phase-2/neo4j/01_load_decisions.py"
            tree = ast.parse(path.read_text())
            calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Name) and node.func.id == "guarded_cleanup"]
            self.assertEqual(len(calls), 1)
            self.assertEqual(ast.dump(calls[0].args[1]), ast.dump(ast.Name(id="PROJECT_ROOT", ctx=ast.Load())))
            self.assertEqual(calls[0].args[2].value, wg)
            self.assertEqual([arg.id for arg in calls[0].args[3:]],
                             ["reclaim_stale_edges", "sweep_orphan_backfill_agenda_items"])
            transactions = [node for node in ast.walk(tree) if isinstance(node, ast.With)
                            and calls[0] in ast.walk(node)
                            and any(isinstance(item.context_expr, ast.Call)
                                    and isinstance(item.context_expr.func, ast.Attribute)
                                    and item.context_expr.func.attr == "begin_transaction"
                                    and isinstance(item.optional_vars, ast.Name)
                                    and item.optional_vars.id == "tx" for item in node.items)]
            self.assertEqual(len(transactions), 1)
            self.assertEqual(calls[0].args[0].id, "tx")
            commits = [node for node in ast.walk(transactions[0]) if isinstance(node, ast.Call)
                       and isinstance(node.func, ast.Attribute) and node.func.attr == "commit"
                       and isinstance(node.func.value, ast.Name) and node.func.value.id == "tx"]
            self.assertEqual(len(commits), 1)
            self.assertLess(calls[0].lineno, commits[0].lineno)
            self.assertEqual([(kw.arg, kw.value.id) for kw in calls[0].keywords], [("source", "agenda_source")])

    def test_main_rejects_missing_canonical_source_before_opening_a_driver(self):
        for number in range(1, 6):
            wg = f"RAN{number}"
            path = ROOT / f"scripts/tsg/RAN/formal/{wg}/phase-2/neo4j/01_load_decisions.py"
            tree = ast.parse(path.read_text())
            node = next(node for node in tree.body
                        if isinstance(node, ast.FunctionDef) and node.name == "main")
            relations = next(node.value for node in tree.body if isinstance(node, ast.Assign)
                             and any(isinstance(target, ast.Name) and target.id == "_ATTACHMENT_RELATIONS"
                                     for target in node.targets))
            driver = Mock()
            env = {"prepare_for_wg": lambda *args: {}, "_accept_inputs": lambda: {},
                   "PROJECT_ROOT": self.root, "load_agenda_retention": agenda_retention.load_agenda_retention,
                   "GraphDatabase": SimpleNamespace(driver=driver), "uuid": uuid,
                   "_AttachAccounting": AttachAccounting,
                   "_ATTACHMENT_RELATIONS": ast.literal_eval(relations)}
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), env)
            with self.subTest(wg=wg), self.assertRaises(FileNotFoundError):
                env["main"]()
            self.assertIsInstance(env["ATTACHMENTS"], AttachAccounting)
            driver.assert_not_called()

    def test_missing_empty_malformed_and_duplicate_sources_stop_before_any_deletion(self):
        row = self.write_source()[0]
        invalid = [None, {}, {"@graph": []}, {"@graph": {}}, {"@graph": [False]},
                   {"@graph": [{**row, "@id": ""}]}, {"@graph": [{**row, "tdoc:agendaNumber": None}]},
                   {"@graph": [{**row, "@type": "tdoc:Tdoc"}]},
                   {"@graph": [row, {**row, "tdoc:agendaNumber": "2"}]},
                   {"@graph": [row, {**row, "@id": "other"}]}]
        for payload in invalid:
            with self.subTest(payload=payload):
                if payload is None:
                    self.path().unlink(missing_ok=True)
                else:
                    self.path().write_text(json.dumps(payload))
                tx = AgendaTransaction()
                calls = []
                with self.assertRaises((OSError, ValueError)):
                    agenda_retention.guarded_cleanup(tx, self.root, "RAN1",
                                                     lambda value: calls.append("delete"), self.wrapper("RAN1"))
                self.assertEqual(calls, [])
                self.assertEqual(tx.queries, [])
        self.path().write_text('{"@graph":[],"@graph":[' + json.dumps(row) + ']}')
        with self.assertRaisesRegex(ValueError, "duplicate canonical agenda JSON key"):
            agenda_retention.load_agenda_retention(self.root, "RAN1")

    def test_source_change_during_reclaim_rolls_back_and_prevents_sweep(self):
        row = self.write_source()[0]
        tx = AgendaTransaction([{"name": "unsupported", "_createdBy": "phase-2-backfill"}])
        def reclaim(value):
            value.edges.clear()
            self.write_source(rows=[{**row, "tdoc:agendaNumber": "2"}])
        with self.assertRaisesRegex(RuntimeError, "canonical agenda source changed"):
            tx.execute_write(lambda value: agenda_retention.guarded_cleanup(
                value, self.root, "RAN1", reclaim, self.wrapper("RAN1")))
        self.assertEqual(tx.edges, ["stale"])
        self.assertEqual(tx.queries, [])
        self.assertEqual((tx.commits, tx.rollbacks), (0, 1))

    def test_preflight_source_changed_before_transaction_prevents_all_deletions(self):
        row = self.write_source()[0]
        source = agenda_retention.load_agenda_retention(self.root, "RAN1")
        self.write_source(rows=[{**row, "tdoc:agendaNumber": "2"}])
        tx = AgendaTransaction()
        reclaim = Mock()
        with self.assertRaisesRegex(RuntimeError, "canonical agenda source changed"):
            tx.execute_write(lambda value: agenda_retention.guarded_cleanup(
                value, self.root, "RAN1", reclaim, self.wrapper("RAN1"), source=source))
        reclaim.assert_not_called()
        self.assertEqual(tx.queries, [])
        self.assertEqual((tx.commits, tx.rollbacks), (0, 1))

    def test_source_change_during_sweep_rolls_back_both_edges_and_nodes(self):
        row = self.write_source()[0]
        nodes = [{"name": "unsupported", "_createdBy": "phase-2-backfill"}]
        tx = AgendaTransaction(nodes, during_query=lambda: self.write_source(
            rows=[{**row, "tdoc:agendaNumber": "2"}]))
        with self.assertRaisesRegex(RuntimeError, "canonical agenda source changed"):
            tx.execute_write(lambda value: agenda_retention.guarded_cleanup(
                value, self.root, "RAN1", lambda state: state.edges.clear(), self.wrapper("RAN1")))
        self.assertEqual((tx.nodes, tx.edges), (nodes, ["stale"]))
        self.assertEqual((tx.commits, tx.rollbacks), (0, 1))

    def test_source_scope_mismatch_and_symlink_are_rejected(self):
        self.write_source()
        source = agenda_retention.load_agenda_retention(self.root, "RAN1")
        tx = AgendaTransaction()
        with self.assertRaisesRegex(ValueError, "scope differs"):
            agenda_retention.sweep_unsupported_agendas(tx, self.root, "RAN2", source)
        self.path().rename(self.path().with_suffix(".json"))
        self.path().symlink_to(self.path().with_suffix(".json"))
        with self.assertRaisesRegex(ValueError, "regular paths"):
            agenda_retention.load_agenda_retention(self.root, "RAN1")
        self.assertEqual(tx.queries, [])


if __name__ == "__main__":
    unittest.main()
