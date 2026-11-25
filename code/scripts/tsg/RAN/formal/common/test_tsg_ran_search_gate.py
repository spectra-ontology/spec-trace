#!/usr/bin/env python3
"""Spec: TSG_RAN P9 search gate; Ontology: existing TR Section payload; Cycle: 10.
배경: 검색 판정·무결성 실패가 bootstrap 종료 코드로 전달되도록 회귀를 고정한다.
사용: python3 -B -m unittest discover -s scripts/tsg/RAN/formal/common -p test_tsg_ran_search_gate.py
실제 함수/메서드와 격리 CQ·보고서를 사용하며 DB·모델·네트워크를 호출하지 않는다.
"""
import argparse
import ast
import contextlib
from datetime import datetime
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from test_audit_safety_contracts import function, ROOT

PATH = ROOT / "scripts/tsg/RAN/formal/TSG_RAN/phase-9/validation/01_validate_search.py"
HIT = {"trSectionId": "38.811-5", "score": .8, "release": "Rel-18"}
CQ = {"id": "synthetic", "category": "synthetic", "question": "synthetic question",
      "search_query": "synthetic query", "expected_sections": ["38.811-5"],
      "match_mode": "prefix"}


def evaluator():
    env = {}
    function(PATH, "_validated_filters", env)
    return function(PATH, "evaluate_cq", env)


class TsgRanSearchGate(unittest.TestCase):
    def run_fixture(self, questions, hits=None, gate=True, search_error=None):
        with tempfile.TemporaryDirectory() as tmp:
            config = NS(cq_path=Path(tmp)/"cq.json", output_path=Path(tmp)/"report.json",
                        qdrant_host="fake", qdrant_port=0, collection_name="fake")
            config.cq_path.write_text(json.dumps({"questions": questions}))
            def search(**kw):
                if search_error:
                    raise ValueError(search_error)
                return hits if hits is not None else [dict(HIT)]
            env = {"Config": object, "json": json, "sys": sys, "datetime": datetime,
                   "SearchClient": lambda _: NS(search=search), "evaluate_cq": evaluator(),
                   "integrity_gate": lambda *a: {"pass": gate, "synthetic": True}}
            with contextlib.redirect_stdout(io.StringIO()):
                code = function(PATH, "run_validation", env)(config)
            return code, json.loads(config.output_path.read_text())

    def test_pass_preserves_report_and_returns_zero(self):
        code, report = self.run_fixture([dict(CQ)])
        self.assertEqual(code, 0)
        self.assertEqual(report["metadata"]["overallStatus"], "PASS")
        self.assertEqual(set(report), {"metadata", "categoryStats", "results"})
        self.assertEqual(report["metadata"]["unknownCount"], 0)
        self.assertEqual(report["results"][0]["search_results"], [HIT])
        self.assertEqual(report["results"][0]["evaluation"]["status"], "PASS")

    def test_failure_unknown_integrity_and_search_error_are_nonzero(self):
        fixtures = [([dict(CQ)], [], True, None, "FAIL"),
                    ([{**CQ, "match_mode": "unsupported"}], [HIT], True, None, "UNKNOWN"),
                    ([dict(CQ)], [HIT], False, None, "PASS"),
                    ([dict(CQ)], [], True, "unsupported filter", "FAIL")]
        for questions, hits, gate, error, status in fixtures:
            with self.subTest(status=status, gate=gate, error=error):
                code, report = self.run_fixture(questions, hits, gate, error)
                self.assertEqual(code, 1)
                self.assertEqual(report["metadata"]["overallStatus"], "FAIL")
                self.assertEqual(report["results"][0]["evaluation"]["status"], status)
                self.assertEqual(report["metadata"]["unknownCount"], int(status == "UNKNOWN"))

    def test_empty_active_skip_and_defer_keep_evidence_without_success(self):
        for questions in ([], [{**CQ, "defer": True}], [{**CQ, "search_query": " "}],
                          [dict(CQ), {**CQ, "id": "empty", "search_query": ""}]):
            with self.subTest(questions=questions):
                code, report = self.run_fixture(questions)
                self.assertEqual(code, 1)
                self.assertNotEqual(report["metadata"]["overallStatus"], "PASS")
                self.assertEqual(len(report["results"]), len(questions))
        code, report = self.run_fixture([dict(CQ), {**CQ, "id": "deferred", "defer": True}])
        self.assertEqual(code, 0)
        self.assertEqual(report["results"][1]["evaluation"]["status"], "DEFER")

    def test_filter_check_requires_supported_filter_and_observed_match(self):
        evaluate = evaluator()
        good = {**CQ, "match_mode": "filter_check", "filters": {"release": "Rel-18"}}
        self.assertEqual(evaluate(good, [HIT])["status"], "PASS")
        for filters, hits in (({}, [HIT]), ({"release": "Rel-18"}, []),
                              ({"release": "Rel-19"}, [HIT]), ({"unknown": 1}, [HIT]),
                              ({"release": []}, [HIT]), ([], [HIT])):
            with self.subTest(filters=filters, hits=hits):
                result = evaluate({**good, "filters": filters}, hits)
                self.assertEqual(result["status"], "FAIL")
                self.assertFalse(result["all_match"])
                self.assertTrue(result["violations"])

    def test_search_validates_filters_before_embedding_and_qdrant(self):
        calls = []
        env = {"Config": object, "FieldCondition": lambda **kw: NS(**kw),
               "MatchValue": lambda **kw: NS(**kw), "Filter": lambda **kw: NS(**kw)}
        function(PATH, "_validated_filters", env)
        node = next(n for n in ast.parse(PATH.read_text()).body
                    if isinstance(n, ast.ClassDef) and n.name == "SearchClient")
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(PATH), "exec"), env)
        client = object.__new__(env["SearchClient"])
        client.config = NS(top_k=10, collection_name="fake")
        client.embed_query = lambda q: calls.append(("embed", q)) or [0.0]
        client.qdrant = NS(query_points=lambda **kw: calls.append(("query", kw)) or NS(points=[]))
        for filters in ({"unknown": "x"}, {"release": []}, {"release": 18},
                        {"release": " "}, {"isAnnex": 1}, {"level": True},
                        {"level": -1}, [], "release"):
            with self.subTest(filters=filters), self.assertRaises(ValueError):
                client.search("q", filters=filters)
            self.assertEqual(calls, [])
        filters = {"trNumber": "38.811", "release": "Rel-18", "status": "Completed",
                   "isAnnex": True, "level": 1}
        self.assertEqual(client.search("q", filters=filters), [])
        query = calls[1][1]
        self.assertEqual({c.key: c.match.value for c in query["query_filter"].must}, filters)
        self.assertEqual(query["query_filter"].must_not[0].key, "releaseAware")
        self.assertTrue(query["query_filter"].must_not[0].match.value)

    def test_prefix_needs_expected_target_and_hit_but_noise_contract_is_preserved(self):
        evaluate = evaluator()
        for expected, hits in (([], []), ([], [HIT]), (["38.811-5"], [])):
            self.assertEqual(evaluate({**CQ, "expected_sections": expected}, hits)["status"], "FAIL")
        self.assertEqual(evaluate({**CQ, "match_mode": "noise_check", "max_score": 0}, [])["status"], "PASS")
        self.assertEqual(evaluate({**CQ, "match_mode": "noise_check", "max_score": 0}, [HIT])["status"], "WARN")
        self.assertEqual(evaluate({**CQ, "match_mode": "none"}, [])["status"], "SKIP")

    def test_prefix_respects_section_and_document_boundaries(self):
        evaluate = evaluator()
        cases = (("38.811-1", "38.811-10", "FAIL"),
                 ("38.811-1", "38.811-1", "PASS"),
                 ("38.811-1", "38.811-1.2", "PASS"),
                 ("38.811-1", "38.811-1-1", "PASS"),
                 ("38.811", "38.811-1", "PASS"),
                 ("38.811", "38.8110-1", "FAIL"))
        for expected, found, status in cases:
            with self.subTest(expected=expected, found=found):
                cq = {**CQ, "expected_sections": [expected]}
                result = evaluate(cq, [{**HIT, "trSectionId": found}])
                self.assertEqual(result["status"], status)
                self.assertEqual(result["recall"], float(status == "PASS"))

    def test_cli_propagates_result_code(self):
        class Parser:
            def __init__(self, *a, **kw): pass
            def add_argument(self, *a, **kw): pass
            def parse_args(self): return NS(collection="fake")
        for code in (0, 1):
            env = {"argparse": NS(ArgumentParser=Parser), "Config": lambda **kw: NS(**kw),
                   "run_validation": lambda _: code, "sys": sys, "__name__": "__main__"}
            function(PATH, "main", env)
            entry = next(n for n in ast.parse(PATH.read_text()).body if isinstance(n, ast.If)
                         and ast.unparse(n.test) == "__name__ == '__main__'")
            with self.assertRaises(SystemExit) as caught:
                exec(compile(ast.Module(body=[entry], type_ignores=[]), str(PATH), "exec"), env)
            self.assertEqual(caught.exception.code, code)


if __name__ == "__main__":
    unittest.main()
