#!/usr/bin/env python3
"""test_semantic_validation_contracts.py — 검증 범위와 실제 데이터 대조를 검증한다.

Spec: E-3 state, E-4 보존, E-5 real-hit 및 formal Phase-6 type 계약.
Ontology: 기존 state와 앵커·청크·스레드 식별자 계약을 유지한다.
Cycle: 실제 함수 AST → 합성 저장값/주입값 → PASS와 FAIL 경계 확인.
배경: 전건 검증과 결측·상태 전이에 대한 기존 계약을 구현한다.
사용: python3 -B scripts/tsg/RAN/formal/common/test_semantic_validation_contracts.py
LLM 호출·DB·모델·네트워크: 없음.
"""
import ast
import contextlib
from datetime import datetime
import io
import tempfile
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(ROOT / "scripts/common"))
from common.atomic_io import write_json_atomic


def function(path, name, env):
    node = next(n for n in ast.parse(path.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), env)
    return env[name]


class Rows(list):
    def data(self):
        return self

    def single(self):
        return self[0] if self else None


class Session:
    def __init__(self, query):
        self.query = query

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def run(self, query, **kwargs):
        return self.query(query, kwargs)


class SemanticValidationTests(unittest.TestCase):
    def test_release_aware_kg_mismatch_reasons(self):
        path = ROOT / "scripts/tsg/RAN/formal/RAN1/phase-7/validation/03_validate_kg_connection.py"
        env = {"re": __import__("re")}
        for name in ("_text", "_section_ident", "_section_parts", "classify_mismatch"):
            function(path, name, env)
        classify = env["classify_mismatch"]
        for release in ("Rel-17", "Rel-18", "Rel-19"):
            for ident, p7, p3, expected in (
                    ("2", False, True, "references_excluded"),
                    ("3", False, True, "container_or_excluded"),
                    ("9.A", True, False, "hybrid_section_not_in_phase3"),
                    ("5.1", True, False, "phase7_only"),
                    ("5.1", True, True, "unknown")):
                with self.subTest(release=release, section=ident, p7=p7, p3=p3):
                    self.assertEqual(classify(f"38.214-{release}-{ident}", p7, p3), expected)
        self.assertEqual(classify("invalid", False, True), "invalid_format")

    def test_ran1_filter_only_checks_implicit_combined_filters(self):
        path = ROOT / "scripts/tsg/RAN/formal/RAN1/phase-8/validation/01_validate_search.py"
        evaluate = function(path, "evaluate_cq", {"SearchClient": object, "math": math})
        filters = {"category": "B", "workItem": "NR_MIMO_Ph5-Core", "specNumber": "38.214"}
        cq = {"match_mode": "filter_only", "filters": filters}
        good = {"score": 0.7, **filters}
        cases = [("matching", [good], "PASS"), ("empty", [], "FAIL"),
                 ("missing-payload", [{"score": 0.7}], "FAIL")]
        for field in filters:
            wrong = {**good, field: "different"}
            missing = {k: v for k, v in good.items() if k != field}
            cases.extend([(f"wrong-{field}", [wrong], "FAIL"),
                          (f"mixed-{field}", [good, wrong], "FAIL"),
                          (f"missing-{field}", [missing], "FAIL")])
        before = json.dumps({"cq": cq, "cases": cases}, sort_keys=True)
        for label, hits, expected in cases:
            with self.subTest(case=label):
                result = evaluate(cq, hits)
                self.assertEqual(result["status"], expected)
                if hits:
                    self.assertEqual(result["all_match"], expected == "PASS")
                    self.assertEqual(result["checked_filters"], filters)
                else:
                    self.assertEqual(result, {"status": "FAIL", "note": "no results (filter too restrictive or no data)",
                                              "top_score": 0.0})
        self.assertEqual(json.dumps({"cq": cq, "cases": cases}, sort_keys=True), before)
        with self.subTest(case="no-filter-contract"):
            self.assertEqual(evaluate({"match_mode": "filter_only"}, [good])["status"], "FAIL")
        for field, value in filters.items():
            explicit = {**cq, "verify_filter": field}
            for hits, expected in (([good], True), ([{**good, field: "different"}], False),
                                   ([good, {**good, field: "different"}], False)):
                with self.subTest(explicit_field=field, hits=len(hits), matches=expected):
                    self.assertEqual(evaluate(explicit, hits),
                                     {"status": "PASS" if expected else "FAIL", "filter_field": field,
                                      "expected_value": value, "total_results": len(hits),
                                      "all_match": expected, "top_score": 0.7})

    def test_partial_search_counts_preserve_rows_and_kg_scope(self):
        path = ROOT / "scripts/tsg/RAN/formal/RAN4/phase-8/validation/01_validate_search.py"
        for statuses, expected in ((["PARTIAL", "PASS", "PARTIAL", "FAIL", "PARTIAL"], (1, 3, 1, 0)),
                                   (["PASS", "WARN", "PARTIAL", "FAIL", "SKIP", "DEFER"], (1, 2, 1, 2))):
            for nested in (False, True):
                with self.subTest(statuses=statuses, nested=nested), tempfile.TemporaryDirectory() as td:
                    output = Path(td) / "out.json"
                    config = SimpleNamespace(collection_name="synthetic", output_path=output)
                    search = [{"cq_id": f"CQ{i}", **({"evaluation": {"status": status}}
                              if nested else {"status": status})} for i, status in enumerate(statuses)]
                    kg = [{"cq_id": f"K{i}", "status": "PASS"} for i in range(5)]
                    original = json.dumps({"search": search, "kg": kg}, sort_keys=True)
                    env = {"Config": SimpleNamespace, "json": json, "datetime": datetime,
                           "write_json_atomic": write_json_atomic}
                    save = function(path, "save_results", env)
                    with contextlib.redirect_stdout(io.StringIO()):
                        save(config, {"status": "OK"}, search, kg, [{}] * len(search))
                    report = json.loads(output.read_text())
                    meta = report["metadata"]
                    self.assertEqual(tuple(meta[key] for key in
                                           ("passCount", "warnCount", "failCount", "skipCount")), expected)
                    self.assertEqual(meta["totalCQs"], len(search))
                    self.assertEqual(sum(expected), len(search))
                    self.assertEqual(meta["kgChecks"], {"total": 5, "PASS": 5})
                    self.assertEqual(report["searchResults"], search)
                    self.assertEqual(report["kgResults"], kg)
                    self.assertEqual(json.dumps({"search": search, "kg": kg}, sort_keys=True), original)

    def test_filter_gate_requires_nonempty_matching_results(self):
        for wg in range(1, 6):
            path = ROOT / f"scripts/tsg/RAN/formal/RAN{wg}/phase-7/validation/01_validate_search.py"
            for field, value, other in (("specNumber", "38.423", "38.413"), ("level", 1, 2)):
                good = {"sectionId": "synthetic-section", field: value, "score": 0.7}
                wrong = {**good, field: other}
                missing = {"sectionId": "synthetic-section", "score": 0.7}
                for label, hits, expected in (("empty", [], 1), ("matching", [good], 0),
                                               ("wrong", [wrong], 1), ("mixed", [good, wrong], 1),
                                               ("missing", [missing], 1)):
                    with self.subTest(wg=wg, field=field, case=label), tempfile.TemporaryDirectory() as td:
                        temp = Path(td)
                        config = SimpleNamespace(cq_path=temp / "cq.json", output_path=temp / "out.json",
                                                 collection_name="synthetic", qdrant_host="fixture", qdrant_port=0)
                        question = {"id": "filter", "category": "F_메타데이터필터", "search_query": "fixture",
                                    "match_mode": "filter_check", "filters": {field: value},
                                    "expected_filter_field": field, "expected_filter_value": value}
                        config.cq_path.write_text(json.dumps({"questions": [question]}))
                        before = config.cq_path.read_bytes()
                        hits_before = json.dumps(hits, sort_keys=True)
                        client = SimpleNamespace(search=lambda **kwargs: hits, close=lambda: None,
                                                 qdrant=SimpleNamespace(close=lambda: None))
                        env = {"Config": SimpleNamespace, "json": json, "datetime": datetime,
                               "sys": sys, "math": math, "write_json_atomic": write_json_atomic,
                               "SearchClient": lambda config: client}
                        env["evaluate_cq"] = function(path, "evaluate_cq", env)
                        if wg == 1:
                            function(path, "_run_with_client", env)
                        run = function(path, "run_validation", env)
                        with contextlib.redirect_stdout(io.StringIO()):
                            self.assertEqual(run(config), expected)
                        report = json.loads(config.output_path.read_text())
                        evaluation = report["results"][0]["evaluation"]
                        self.assertEqual(evaluation["status"], "PASS" if expected == 0 else "FAIL")
                        self.assertEqual(evaluation["all_match"], expected == 0)
                        self.assertEqual(evaluation["total_results"], len(hits))
                        self.assertEqual(config.cq_path.read_bytes(), before)
                        self.assertEqual(json.dumps(hits, sort_keys=True), hits_before)
            evaluate = function(path, "evaluate_cq", {})
            for mode, expected_status in (("none", "PASS"), ("noise_check", "UNVERIFIED_LABELS")):
                with self.subTest(wg=wg, separate_empty_policy=mode):
                    self.assertEqual(evaluate({"match_mode": mode}, [])["status"], expected_status)

    def test_real_hit_checks_every_record_and_matches_stored_values(self):
        for wg in range(1, 6):
            path = ROOT / f"scripts/tsg/RAN/email/RAN{wg}/phase-5/validation/01_validate_injection_cq.py"
            for case in ("valid", "text", "21st", "entity", "date", "easy_spec"):
                with self.subTest(wg=wg, case=case):
                    def query(query, params):
                        if "EmailMessage" in query:
                            self.assertIn("END = $entity", query)
                            return Rows([{"rel": 0.8}]) if params["entity"] == "R1-1" else Rows()
                        self.assertIn("sp:Spec {specNumber:$spec}", query)
                        return Rows([{"ld": "2026-01-01"}]) if params["spec"] == "38.331" else Rows()
                    driver = SimpleNamespace(session=lambda **kwargs: Session(query))
                    payloads = {f"c{i}": {"chunkId": f"c{i}", "text": "source"} for i in range(21)}
                    hard = [{"deliberation_chunkId": f"c{i}", "channel": "tdoc", "text": "source",
                             "relevance_score": 0.8, "d_entity": "R1-1"} for i in range(21)]
                    easy = [{"threadKey": "thread", "d_entity": "38.331", "latestDate": "2026-01-01", "provenance": "neo4j-thread-tier"}]
                    if case == "text":
                        hard[0]["text"] = "different"
                    elif case == "21st":
                        del payloads["c20"]
                    elif case == "entity":
                        hard[0]["d_entity"] = "different"
                    elif case == "date":
                        easy[0]["latestDate"] = "2026-02-01"
                    elif case == "easy_spec":
                        easy[0]["d_entity"] = "different"
                    env = {"json": json, "math": math, "READ_ACCESS": "READ", "dc": SimpleNamespace(SEM_CHANNELS={"tdoc", "section", "resolution"}),
                           "_qdrant_payload": lambda cid: payloads.get(cid)}
                    build = {"_deliberation_context": hard, "_deliberation_threads": easy,
                             "_deliberation_meta": {"method": "score-bearing"}}
                    result = function(path, "cq_5_6", env)(driver, build)
                    self.assertEqual(result["pass"], case == "valid")
                    self.assertEqual(result["detail"]["hard_checked"], 21)

    def test_active_to_stale_preserves_total_but_deletion_fails(self):
        for wg in range(1, 5):
            path = ROOT / f"scripts/tsg/RAN/email/RAN{wg}/phase-4/verification/cq_probe_anchor_health.py"
            for missing, expected in ((0, "PASS"), (1, "FAIL")):
                before = {"nodes": 20, "rels": 10, "anchors_total": 10, "active": 10, "stale": 0, "candidate": 0}
                after = dict(before, active=9, stale=1 - missing)
                output = []
                env = {"drv": SimpleNamespace(session=lambda **kwargs: Session(lambda *a: Rows())), "READ_ACCESS": "READ",
                       "m01": SimpleNamespace(CY_AUDIT="synthetic", q=lambda *args: [after]),
                       "SI": {"audit_before": before, "audit_after": after}, "AUDIT": {"stored": after, "live": after},
                       "record": lambda *args: output.append(args)}
                function(path, "cq3", env)()
                self.assertEqual(output[0][1], expected)

    def test_both_missing_types_are_both_counted(self):
        for wg in range(1, 6):
            path = ROOT / f"scripts/tsg/RAN/formal/RAN{wg}/phase-6/validation/03_validate_kg_consistency.py"
            env = {"fetch_qdrant_sample": lambda *args: [{"tdocNumber": "fixture", "type": ""}],
                   "fetch_neo4j_metadata": lambda *args: {"fixture": {"tdocNumber": "fixture", "type": ""}}}
            stats = function(path, "validate_metadata_consistency", env)(None, None, 1)["consistency"]["type"]
            self.assertEqual(stats["neo4j_empty"], 1)
            self.assertEqual(stats["qdrant_empty"], 1)
            self.assertEqual(stats["mismatch"], 0)


if __name__ == "__main__":
    unittest.main()
