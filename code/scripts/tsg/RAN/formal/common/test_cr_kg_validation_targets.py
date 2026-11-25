#!/usr/bin/env python3
"""CR KG 검증에서 빈 대상과 실제 연결 결과를 구분한다.

Spec: RAN1 Phase-8 §4.7, step3_validation.md KG 점검·종료 상태.
Ontology: 기존 TDoc·Spec·CRPack·MODIFIES·TS 절 연결 범위를 유지한다.
Cycle: 실제 함수 AST에 합성 Neo4j·Qdrant 응답을 주입해 판정한다.
사용: python3 -B scripts/tsg/RAN/formal/common/test_cr_kg_validation_targets.py
DB·모델·원본·네트워크 호출: 없음.
"""
import ast
import contextlib
import io
from pathlib import Path
import random
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock, patch

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
SOURCE = ROOT / "scripts/tsg/RAN/formal/RAN1/phase-8/validation/01_validate_search.py"


class KgTargetsTests(unittest.TestCase):
    def run_case(self, chunks, *, found=True, excluded=False, wg=1, connected_tdocs=None):
        session = MagicMock()

        def query(statement, **params):
            if "AS meetings" in statement:
                return [{"meetings": ["RAN1#fixture"]}]
            if "AS cnt" in statement:
                return [{"cnt": int(found if connected_tdocs is None else params.get("tdoc") in connected_tdocs)}]
            values = next(iter(params.values()))
            return [{"found": found} for _ in values]

        session.execute_read.side_effect = lambda callback: callback(SimpleNamespace(run=query))
        driver = MagicMock()
        driver.__enter__.return_value.session.return_value.__enter__.return_value = session
        qdrant = Mock()
        point = SimpleNamespace(payload={"specNumber": "38.214", "sectionId": "38.214-5"})

        def scroll(**kwargs):
            if "scroll_filter" not in kwargs:
                return ([point], None)
            return ([point] if found else [], None)

        qdrant.scroll.side_effect = scroll
        modules = {
            "neo4j": SimpleNamespace(GraphDatabase=SimpleNamespace(driver=lambda *a, **k: driver)),
            "qdrant_client": SimpleNamespace(QdrantClient=lambda **k: qdrant),
            "qdrant_client.http": SimpleNamespace(),
            "qdrant_client.http.models": SimpleNamespace(
                **{name: lambda **k: SimpleNamespace(**k)
                   for name in ("Filter", "FieldCondition", "MatchValue")}),
        }
        env = {"Config": object, "sys": sys, "random": random,
               "axis": SimpleNamespace(bolt_uri=lambda wg: "fixture"),
               "credentials": SimpleNamespace(neo4j_auth=lambda: ("fixture", "fixture")),
               "load_phase7_ts_parser": lambda: object(),
               "phase7_design_exclusions": lambda *a: {"5": "void"} if excluded else {}}
        source = SOURCE if wg == 1 else ROOT / f"scripts/tsg/RAN/formal/RAN{wg}/phase-8/validation/01_validate_search.py"
        tree = ast.parse(source.read_text())
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                    and n.name == "validate_kg_links")
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), "exec"), env)
        with patch.dict(sys.modules, modules), contextlib.redirect_stdout(io.StringIO()):
            results = env["validate_kg_links"](chunks, SimpleNamespace(qdrant_host="fixture", qdrant_port=0))
        if wg in (1, 4):
            qdrant.close.assert_called_once()
        return {row["cq_id"]: row for row in results}

    @staticmethod
    def chunk(**changes):
        return {"chunkType": "header", "tdocNumber": "R1-fixture", "meeting": "RAN1#fixture",
                "specNumber": "38.214", "crPackId": "RP-fixture", "clausesAffected": ["5"],
                "sectionIds": ["38.214-5"], **changes}

    def test_empty_targets_are_not_passes(self):
        for chunks in ([], [{"meeting": "RAN1#other"}]):
            with self.subTest(chunks=chunks):
                rows = self.run_case(chunks)
                self.assertTrue(all(row["status"] != "PASS" for row in rows.values()))
                self.assertEqual(rows["K-03"]["status"], "SKIP")

    def test_positive_targets_keep_match_and_missing_results(self):
        for found, status in ((True, "PASS"), (False, "WARN")):
            with self.subTest(found=found):
                rows = self.run_case([self.chunk()], found=found)
                self.assertEqual({row["status"] for row in rows.values()}, {status})
                for key in ("K-01", "K-02", "K-04"):
                    self.assertEqual(rows[key]["total"], 1)
                self.assertEqual(rows["K-05"]["sample"], 1)

    def test_scope_filters_do_not_make_empty_populations_pass(self):
        rows = self.run_case([self.chunk(meeting="RAN1#other", crPackId="", specNumber="36.211")])
        for key in ("K-01", "K-04", "K-05"):
            self.assertNotEqual(rows[key]["status"], "PASS")
        self.assertEqual(rows["K-02"]["status"], "PASS")

    def test_all_design_exclusions_are_separate_from_verified_links(self):
        rows = self.run_case([self.chunk()], found=False, excluded=True)
        self.assertEqual(rows["K-03"]["judged"], 0)
        self.assertEqual(rows["K-03"]["design_excluded"], 1)
        self.assertNotEqual(rows["K-03"]["status"], "PASS")


    def test_other_wg_targets_require_nonempty_verified_populations(self):
        for wg in (2, 3, 4):
            for chunks in ([], [{}]):
                with self.subTest(wg=wg, chunks=chunks):
                    rows = self.run_case(chunks, wg=wg)
                    self.assertTrue(all(row["status"] != "PASS" for row in rows.values()))
            for found, expected in ((True, "PASS"), (False, "WARN")):
                with self.subTest(wg=wg, found=found):
                    rows = self.run_case([self.chunk()], wg=wg, found=found)
                    self.assertEqual({row["status"] for row in rows.values()}, {expected})
            with self.subTest(wg=wg, excluded=True):
                rows = self.run_case([self.chunk()], wg=wg, found=False, excluded=True)
                self.assertEqual(rows["K-03"]["judged"], 0)
                self.assertNotEqual(rows["K-03"]["status"], "PASS")

    def test_sampled_link_check_requires_every_sample_in_other_wgs(self):
        chunks = [self.chunk(tdocNumber=f"R-fixture-{i}") for i in range(10)]
        for wg in (2, 3, 4):
            for connected, expected in ((1, "WARN"), (8, "WARN"), (10, "PASS")):
                with self.subTest(wg=wg, connected=connected):
                    rows = self.run_case(chunks, wg=wg,
                                         connected_tdocs={c["tdocNumber"] for c in chunks[:connected]})
                    self.assertEqual(rows["K-05"]["sample"], 10)
                    self.assertEqual(rows["K-05"]["matched"], connected)
                    self.assertEqual(rows["K-05"]["status"], expected)


if __name__ == "__main__":
    unittest.main()
