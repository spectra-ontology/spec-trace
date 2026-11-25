#!/usr/bin/env python3
"""Spec: RAN4 P6 label review; Ontology: existing CQ labels; Cycle: 10.
배경: 과거 라벨 검토 플래그가 품질 PASS를 만들지 않도록 한다.
사용: python3 -m unittest discover -s scripts/tsg/RAN/formal/common -p test_review_label_contract.py
LLM/DB/모델/네트워크 호출 없이 실제 평가·집계 함수와 임시 보고서를 사용한다.
"""
import argparse
import ast
import contextlib
from datetime import datetime
import io
import json
import math
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
from test_audit_safety_contracts import function, ROOT

sys.path.insert(0, str(ROOT / "scripts/common"))
from common.atomic_io import write_json_atomic

PATH=ROOT/"scripts/tsg/RAN/formal/RAN4/phase-6/validation/04_validate_search.py"

class ReviewLabels(unittest.TestCase):
    def test_unverified_labels_keep_search_and_block_gate(self):
        for wg in range(1,6):
            with self.subTest(wg=wg):
                self._assert_review_gate(wg)

    def _assert_review_gate(self, wg):
        path=ROOT/f"scripts/tsg/RAN/formal/RAN{wg}/phase-6/validation/04_validate_search.py"
        cq={"id":"VDB-CQ003","category":"topic","question":"original question","search_query":"original query","expected_tdocs":["R4-X"],"label_review_required":True}
        hits=[{"tdocNumber":"R4-X","score":0.9}]
        evaluate=function(path,"evaluate_result",{})
        result=evaluate(cq,hits)
        self.assertEqual(result["status"],"UNVERIFIED_LABELS")
        self.assertIsNone(result["recall_at_k"])
        self.assertEqual(result["found_tdocs"],["R4-X"])
        normal=dict(cq);normal.pop("label_review_required")
        self.assertEqual(evaluate(normal,hits)["status"],"PASS")
        with tempfile.TemporaryDirectory() as tmp:
            config=NS(cq_dataset_path=Path(tmp)/"unused",qdrant_host="fake",qdrant_port=0,collection_name="fake",output_path=Path(tmp)/"report.json")
            calls=[]
            def search(**kw):calls.append(kw);return hits
            client=NS(search=search,close=lambda:None,qdrant=NS(close=lambda:None))
            env={"Config":object,"load_cq_dataset":lambda _:({"evaluation_scope":"historical"},[cq]),"SearchClient":lambda _:client,"evaluate_result":evaluate,"datetime":datetime,"json":json,"sys":sys,"write_json_atomic":write_json_atomic}
            if wg == 1:
                function(path,"_run_with_client",env)
            with contextlib.redirect_stdout(io.StringIO()): output=function(path,"run_validation",env)(config)
            self.assertEqual(len(calls),1)
            self.assertEqual(output["summary"]["unverified_labels"],1)
            self.assertEqual(output["summary"]["pass"],0)
            self.assertEqual(output["results"][0]["status"],"UNVERIFIED_LABELS")
            class Parser:
                def __init__(self,*a,**kw):pass
                def add_argument(self,*a,**kw):pass
                def parse_args(self):return NS(wg=f"RAN{wg}",collection="fake",host="fake",port=0)
            env={"argparse":NS(ArgumentParser=Parser),"DEFAULT_WG":f"RAN{wg}","WG":f"RAN{wg}","Config":lambda **kw:NS(**kw),"PROJECT_ROOT":Path(tmp),"run_validation":lambda _:output,"sys":sys,"axis":NS(WG_REGISTRY={f"RAN{i}":None for i in range(1,6)},qdrant_collection=lambda *args:"fake")}
            with self.assertRaises(SystemExit) as ex:function(path,"main",env)()
            self.assertEqual(ex.exception.code,1)

    def test_empty_labels_require_an_explicit_empty_result_expectation(self):
        for wg in (1, 3, 4):
            path = ROOT / f"scripts/tsg/RAN/formal/RAN{wg}/phase-6/validation/04_validate_search.py"
            evaluate = function(path, "evaluate_result", {})
            hit = {"tdocNumber": "synthetic", "score": .8}
            for hits in ([], [hit]):
                for expected in ({}, {"expected_tdocs": []}, {"expected_tdocs": [], "expect_empty": False}):
                    with self.subTest(wg=wg, hits=hits, expected=expected):
                        result = evaluate(expected, hits)
                        self.assertEqual(result["status"], "UNVERIFIED_LABELS")
                        self.assertIsNone(result["recall_at_k"])
            cq = {"expected_tdocs": [], "expect_empty": True}
            self.assertEqual(evaluate(cq, [])["status"], "PASS")
            self.assertEqual(evaluate(cq, [hit])["status"], "FAIL")
            self.assertEqual(evaluate({**cq, "label_review_required": True}, [])["status"], "UNVERIFIED_LABELS")

    def test_filter_check_requires_filter_and_result(self):
        for wg in (1,2,3,4):
            path=ROOT/f"scripts/tsg/RAN/formal/RAN{wg}/phase-9/validation/01_validate_search.py"
            evaluate=function(path,"evaluate_cq",{"math":math})
            hit={"trSectionId":"38.1-5","score":.7,"release":"Rel-15"}
            cq={"match_mode":"filter_check","filters":{"release":"Rel-15"}}
            self.assertEqual(evaluate(cq,[hit])["status"],"PASS")
            for filters,hits in (({},[hit]),({"release":"Rel-15"},[]),({},[]),({"release":"Rel-17"},[hit])):
                with self.subTest(wg=wg,filters=filters,hits=hits):
                    out=evaluate({**cq,"filters":filters},hits)
                    self.assertEqual(out["status"],"FAIL")
                    self.assertFalse(out["all_match"])
                    self.assertTrue(out["violations"])

    def test_score_comparison_requires_header_and_body_results(self):
        # RAN2 재정렬은 합성 점수를 그대로 반환하며 모델을 불러오지 않는다.
        reranker = NS(shared=lambda: NS(rerank=lambda query, rows, **kw: [
            {**row, "rerank_score": row["score"]} for row in rows
        ]))
        modules = {"llm_quality": NS(), "llm_quality.reranker_module": NS(Reranker=reranker)}
        for wg in (2, 3, 4):
            path = ROOT / f"scripts/tsg/RAN/formal/RAN{wg}/phase-8/validation/01_validate_search.py"
            evaluate = function(path, "evaluate_cq", {"math": math, "__file__": str(path)})
            for mode in ("header_higher", "body_higher"):
                preferred = "header" if mode == "header_higher" else "body"
                other = "body" if preferred == "header" else "header"
                cases = [([], "WARN"),
                         ([{"chunkType": "header", "score": .8}], "WARN"),
                         ([{"chunkType": "body", "score": .8}], "WARN"),
                         ([{"chunkType": preferred, "score": .8}, {"chunkType": other, "score": .2}], "PASS"),
                         ([{"chunkType": preferred, "score": .2}, {"chunkType": other, "score": .8}], "WARN"),
                         ([{"chunkType": "header", "score": 0.0}, {"chunkType": "body", "score": 0.0}], "PASS")]
                for rows, expected in cases:
                    client = NS(search=lambda query, filters, **kw: [row for row in rows if row["chunkType"] == filters["chunkType"]])
                    with self.subTest(wg=wg, mode=mode, rows=rows), patch.dict(sys.modules, modules):
                        result = evaluate({"match_mode": mode}, rows, client=client)
                        self.assertEqual(result["status"], expected)

    def test_tsg_ran_filename_stem(self):
        path=ROOT/"scripts/tsg/RAN/formal/TSG_RAN/phase-5/tr-parser/01_parse_tr_docs.py"
        fn=function(path,"extract_version_and_release",{"re":re,"_hex_digit":lambda x:int(x,36),"RELEASE_CODE":{"j":19,"k":20}})
        self.assertEqual(fn("38744-j01"),("19.0.1","Rel-19"))
        self.assertEqual(fn("38914-k00"),("20.0.0","Rel-20"))

if __name__ == "__main__":unittest.main()
