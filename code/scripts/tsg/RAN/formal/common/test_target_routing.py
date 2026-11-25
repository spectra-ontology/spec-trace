#!/usr/bin/env python3
"""test_target_routing.py — 적재·자동 수집·WG 입력 선택 대상을 검증한다.

Spec: Phase-3 TS 적재, Phase-11 TR auto, Phase-6/7 입력 범위.
Ontology: 기존 WG 및 spec-release 경계를 유지한다.
Cycle: 실제 함수 AST → 임시 파일/자식 호출 대역 → 명시 대상 확인.
배경: 삭제·재적재·CQ 대상과 입력 WG가 같은 실행 범위를 사용해야 한다.
사용: python3 -B scripts/tsg/RAN/formal/common/test_target_routing.py
LLM 호출·DB·모델·네트워크·자식 프로세스: 없음.
"""
import argparse
import ast
import contextlib
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]


def load_functions(path, names, env):
    nodes = [n for n in ast.parse(path.read_text()).body if isinstance(n, ast.FunctionDef) and n.name in names]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), env)
    return env


class RoutingTests(unittest.TestCase):
    def test_tsgran_recreation_rejects_missing_document_output(self):
        path = ROOT / "scripts/tsg/RAN/formal/TSG_RAN/phase-9/qdrant/01_load_qdrant.py"
        for missing in (False, True):
            for recreate in (False, True):
                with self.subTest(missing=missing, recreate=recreate), tempfile.TemporaryDirectory() as td:
                    folder = Path(td)
                    (folder / "38.999").mkdir()
                    chunk = {"chunkId": "one", "trSectionId": "38.999-1", "trNumber": "38.999",
                             "sectionNumber": "1", "sectionTitle": "Scope", "level": 1,
                             "text": "synthetic body", "chunkIndex": 0, "totalChunks": 1}
                    (folder / "38.999/chunks.json").write_text(json.dumps({"chunks": [chunk]}))
                    if missing:
                        (folder / "38.998").mkdir()
                    events = []
                    class Manager:
                        mode = "synthetic"
                        def open_target(self, **kwargs):
                            events.append("open")
                        def upsert_points(self, points):
                            events.append("upsert")
                        def finish_replace(self, ids):
                            events.append("finish")
                            return len(ids)
                        def get_collection_info(self):
                            return {"points_count": 1}
                        def point_ids(self):
                            return set()
                    config = SimpleNamespace(collection_name="synthetic", embedding_model="synthetic",
                                             embedding_dim=1, encoder=SimpleNamespace(provider="local"),
                                             parsed_base=folder, tr_ontology=ROOT / "synthetic-titles.json",
                                             batch_size=2)
                    env = {"Config": object, "EmbeddingClient": lambda config: SimpleNamespace(
                               embed_texts=lambda texts: [[0.1] for text in texts]),
                           "QdrantManager": lambda config: Manager(), "PointStruct": lambda **kw: SimpleNamespace(**kw),
                           "Path": Path, "json": json, "sys": sys, "time": time,
                           "hashlib": hashlib, "PROJECT_ROOT": ROOT,
                           "_abandon_staging_on_error": lambda load: load,
                           "load_tr_titles": lambda path: {"38.999": "Synthetic title"}}
                    load_functions(path, {"read_chunks", "load_all_chunks", "embedding_text", "generate_point_id",
                                          "process_batch", "load_to_qdrant"}, env)
                    with contextlib.redirect_stdout(io.StringIO()):
                        if missing and recreate:
                            with self.assertRaises(FileNotFoundError):
                                env["load_to_qdrant"](config, recreate=True)
                            self.assertEqual(events, [])
                        else:
                            env["load_to_qdrant"](config, recreate=recreate)
                            self.assertEqual(events, ["open", "upsert"] + (["finish"] if recreate else []))

    def test_ts_loader_accepts_explicit_neo4j_uri_for_every_wg(self):
        for wg in range(1, 6):
            base = ROOT / f"scripts/tsg/RAN/formal/RAN{wg}/phase-3/neo4j"
            uri = "bolt://synthetic-host:17687"
            tree = ast.parse((base / "01_load_ts_structure.py").read_text())
            main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
            stop = next(i for i, n in enumerate(main.body) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "NEO4J_URI" for t in n.targets))
            main.body = main.body[:stop + 1]
            env = {"argparse": argparse, "NEO4J_URI": "bolt://default:1", "Path": Path}
            exec(compile(ast.Module(body=[main], type_ignores=[]), str(base), "exec"), env)
            with patch.object(sys, "argv", ["loader", "--neo4j-uri", uri]):
                env["main"]()
            self.assertEqual(env["NEO4J_URI"], uri)

    def test_auto_targets_drive_cq_targets(self):
        for wg in range(1, 6):
            path = ROOT / f"scripts/tsg/RAN/formal/RAN{wg}/phase-11/pipelines/tr_pipeline.py"
            tree = ast.parse(path.read_text())
            main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
            blocks = [n.body for n in ast.walk(main) if isinstance(n, ast.If)]
            block = next(b for b in blocks if any(isinstance(n, ast.Assign) and isinstance(n.value, ast.ListComp) and any(isinstance(t, ast.Name) and t.id == "targets" for t in n.targets) for n in b))
            idx = next(i for i, n in enumerate(block) if isinstance(n, ast.Assign) and isinstance(n.value, ast.ListComp) and any(isinstance(t, ast.Name) and t.id == "targets" for t in n.targets))
            for collected in ([{"spec": "38.999"}], [{"spec": "38.999"}, {"spec": "38.998"}]):
                env = {"collected": collected, "target_id": "38.111"}
                exec(compile(ast.Module(body=block[idx:idx + 2], type_ignores=[]), str(path), "exec"), env)
                resolve = load_functions(path, {"_resolve_cq_targets"}, env)["_resolve_cq_targets"]
                self.assertEqual(resolve(env["target_id"], {"TR-0": {"collected": collected}}), [c["spec"] for c in collected])

    def test_cross_wg_parser_accepts_selected_issuer(self):
        for wg in (1, 4, 5):
            path = ROOT / f"scripts/tsg/RAN/formal/RAN{wg}/phase-6/tdoc-parser/03_parse_full_scope.py"
            env = {"Path": Path, "DEFAULT_WG": f"RAN{wg}", "WG_TDOC_PREFIX": {f"RAN{i}": f"R{i}-" for i in range(1, 6)},
                   "_TDOC_ISSUER": re.compile(r"([A-Za-z]+\d*)-\d"), "find_docx_file": lambda folder: folder / "doc.docx",
                   "tdoc_number_of": lambda name: name, "tdoc_copy_owner": SimpleNamespace(foreign_copies=lambda *args: {})}
            slots = load_functions(path, {"meeting_slots"}, env)["meeting_slots"]
            with tempfile.TemporaryDirectory() as td:
                folder = Path(td)
                (folder / "R2-260001").mkdir()
                accepted, left, _ = slots(folder, "RAN2#132", None, wg="RAN2")
                self.assertEqual([s[2] for s in accepted], ["R2-260001"])
                self.assertEqual(left["foreign_wg"], [])
                rejected, left, _ = slots(folder, "RAN2#132", None)
                self.assertEqual(rejected, [])
                self.assertEqual(len(left["foreign_wg"]), 1)

    def test_release_plan_is_not_missing_spec_output(self):
        path = ROOT / "scripts/tsg/RAN/formal/RAN5/phase-7/qdrant/01_load_qdrant.py"
        load = load_functions(path, {"load_all_chunks"}, {"Path": Path, "json": json})["load_all_chunks"]
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            (folder / "release-aware").mkdir()
            (folder / "38.533").mkdir()
            (folder / "38.533/chunks.json").write_text(json.dumps({"specNumber": "38.533", "chunks": [{"chunkId": "one"}]}))
            missing = []
            self.assertEqual(len(load(folder, missing)), 1)
            self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
