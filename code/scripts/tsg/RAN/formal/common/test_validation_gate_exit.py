#!/usr/bin/env python3
"""test_validation_gate_exit.py — 검증 보고서 실패의 CLI 종료 코드 전파를 검증한다.

Spec: Email Phase-1/2 필수 CQ 및 formal Cypher·Phase-6 무결성·Phase-7/9 검색 검증 gate 계약.
Ontology: 기존 CQ와 필수 필드·token 범위를 유지한다.
Cycle: 임시 입력 → 실제 검증 함수 → 보고서와 반환 코드 확인.
배경: FAIL/UNKNOWN 또는 빈 본문을 성공 종료로 전달하지 않는다.
사용: python3 -B scripts/tsg/RAN/formal/common/test_validation_gate_exit.py
LLM 호출·DB·모델·네트워크: 없음. 검색 응답과 경로를 임시 fixture로 대체한다.
"""
import argparse
import ast
from collections import defaultdict
import contextlib
from datetime import datetime
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock, patch

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())


def execute(path, names, env):
    nodes = [n for n in ast.parse(path.read_text()).body
             if isinstance(n, ast.FunctionDef) and (names is None or n.name in names)]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), env)
    return env


class Client:
    def __init__(self, config):
        self.qdrant = SimpleNamespace(close=Mock())

    def search(self, **kwargs):
        return []

    def get_collection_count(self):
        return 1

    def close(self):
        self.qdrant.close()


class GateTests(unittest.TestCase):
    def test_phase1_publication_checks_precede_atomic_report_write(self):
        with patch.object(sys, "path", [str(ROOT / "scripts/common"), *sys.path]):
            from common.atomic_io import write_text_atomic
        for wg in range(1, 6):
            path = ROOT / f"scripts/tsg/RAN/formal/RAN{wg}/phase-1/jsonld/04_validation.py"
            for case in ("valid", "source", "verdict", "checkpoint", "fsync", "replace", "symlink"):
                with self.subTest(wg=wg, case=case), tempfile.TemporaryDirectory() as td:
                    root = Path(td)
                    report = root / "VALIDATION_REPORT.md"
                    report.write_bytes(b"previous report")
                    target = root / "user-report"
                    if case == "symlink":
                        target.write_bytes(b"user report")
                        report.unlink()
                        report.symlink_to(target)
                    def checked(stage):
                        if stage == case:
                            raise ValueError("synthetic " + stage)
                        return 0
                    contract = SimpleNamespace(
                        jsonld_checkpoint=lambda *a: "synthetic-checkpoint",
                        verify_source_validation_results=lambda *a: checked("source"),
                        verify_jsonld_checkpoint=lambda *a: checked("checkpoint"))
                    env = dict(sys=sys, PROJECT_ROOT=root, OUTPUT_DIR=root / "output",
                               REPORT_DIR=root, write_text_atomic=write_text_atomic,
                               validate_instance_count=lambda: (True, {}),
                               validate_required_properties=lambda: (True, []),
                               validate_internal_references=lambda: (True, {}, [], []),
                               validate_enum_values=lambda: (True, []),
                               validate_multi_value_refs=lambda: (0, 0, 0),
                               generate_report=lambda results: "synthetic report",
                               verdict_exit_code=lambda *a: checked("verdict"))
                    execute(path, {"main"}, env)
                    boundary = (patch("common.atomic_io.os." + case, side_effect=OSError("synthetic"))
                                if case in ("fsync", "replace") else contextlib.nullcontext())
                    with patch.dict(sys.modules, {"phase1_count_contract": contract}), boundary, \
                            patch.object(sys, "path", sys.path.copy()), contextlib.redirect_stdout(io.StringIO()):
                        if case == "valid":
                            self.assertEqual(env["main"](), 0)
                            self.assertEqual(report.read_text(), "synthetic report")
                        else:
                            with self.assertRaises((ValueError, OSError)):
                                env["main"]()
                            if case == "symlink":
                                self.assertTrue(report.is_symlink())
                                self.assertEqual(target.read_bytes(), b"user report")
                            else:
                                self.assertEqual(report.read_bytes(), b"previous report")
                    self.assertEqual(sorted(p.name for p in root.iterdir()),
                                     ["VALIDATION_REPORT.md", "user-report"] if case == "symlink"
                                     else ["VALIDATION_REPORT.md"])

    def test_phase3_driver_cleanup_and_retry(self):
        for wg in range(1, 6):
            path = ROOT / f"scripts/tsg/RAN/formal/RAN{wg}/phase-3/validation/01_validate_cq_cypher.py"
            for case in ("valid", "minimum_rows", "connect_error", "session_error", "interrupt",
                         "close_error", "interrupt_close_error"):
                with self.subTest(wg=wg, case=case), tempfile.TemporaryDirectory() as td:
                    temp = Path(td)
                    dataset, output = temp / "cq.json", temp / "out.json"
                    dataset.write_text(json.dumps({"metadata": {"version": "fixture"},
                        "questions": [{"id": "fixture", "category": "synthetic",
                        "question": "Fixture", "cypher": "RETURN 1",
                        "expected_min_rows": 2 if case == "minimum_rows" else 1}]}))
                    output.write_bytes(b"previous report")
                    session = MagicMock()
                    session.run.return_value = [{"value": 1}]
                    driver = MagicMock()
                    driver.session.return_value.__enter__.return_value = session
                    original = KeyboardInterrupt("original interruption") if "interrupt" in case else RuntimeError("original failure")
                    if case == "connect_error":
                        if wg in (1, 2):
                            driver.verify_connectivity.side_effect = original
                        else:
                            driver.session.side_effect = original
                    elif case == "session_error":
                        driver.session.return_value.__enter__.side_effect = original
                    elif "interrupt" in case:
                        session.run.side_effect = original
                    if "close_error" in case:
                        driver.close.side_effect = RuntimeError("close failure")
                    env = {"json": json, "sys": sys, "datetime": datetime,
                           "GraphDatabase": SimpleNamespace(driver=lambda *a, **k: driver),
                           "URI": "fixture", "NEO4J_URI": "fixture", "AUTH": ("fixture", "fixture"),
                           "NEO4J_USER": "fixture", "NEO4J_PASSWORD": "fixture", "READ_ACCESS": "READ", "guard_defects": lambda *a, **k: []}
                    with patch.object(sys, "path", [str(ROOT / "scripts/common"), *sys.path]):
                        from common.atomic_io import write_text_atomic
                    env["write_text_atomic"] = write_text_atomic
                    env.update({key: dataset for key in ("DATASET", "CQ_PATH")})
                    env.update({key: output for key in ("OUTPUT", "OUTPUT_PATH")})
                    execute(path, None, env)
                    for attempt in range(2):
                        caught = None
                        with contextlib.redirect_stdout(io.StringIO()):
                            try:
                                env["main"]()
                            except SystemExit as exc:
                                self.assertEqual(exc.code, int(case == "minimum_rows"))
                            except BaseException as exc:
                                caught = exc
                        driver.close.assert_called_once()
                        if attempt == 0 and case not in ("valid", "minimum_rows"):
                            self.assertIsNotNone(caught)
                            if case != "close_error":
                                self.assertIs(caught, original)
                            self.assertEqual(output.read_bytes(), b"previous report")
                        else:
                            self.assertIsNone(caught)
                            self.assertEqual(json.loads(output.read_text())["results"][0]["status"] == "PASS",
                                             case != "minimum_rows")
                        driver.reset_mock(side_effect=True)
                        driver.session.return_value.__enter__.side_effect = None
                        driver.session.return_value.__enter__.return_value = session
                        session.run.side_effect = None

    def test_phase3_atomic_report_preserves_previous_and_retries(self):
        with patch.object(sys, "path", [str(ROOT / "scripts/common"), *sys.path]):
            from common.atomic_io import write_text_atomic
        for wg in range(1, 6):
            path = ROOT / f"scripts/tsg/RAN/formal/RAN{wg}/phase-3/validation/01_validate_cq_cypher.py"
            for error in (OSError("replace failure"), KeyboardInterrupt("replace interruption")):
                with self.subTest(wg=wg, error=type(error).__name__), tempfile.TemporaryDirectory() as td:
                    temp = Path(td)
                    dataset, output = temp / "cq.json", temp / "out.json"
                    dataset.write_text(json.dumps({"metadata": {"version": "fixture"},
                        "questions": [{"id": "fixture", "category": "synthetic",
                        "question": "Fixture", "cypher": "RETURN 1"}]}))
                    output.write_bytes(b"previous report")
                    session, driver = MagicMock(), MagicMock()
                    session.run.return_value = [{"value": 1}]
                    driver.session.return_value.__enter__.return_value = session
                    env = {"json": json, "sys": sys, "datetime": datetime,
                           "GraphDatabase": SimpleNamespace(driver=lambda *a, **k: driver),
                           "URI": "fixture", "NEO4J_URI": "fixture", "AUTH": ("fixture", "fixture"),
                           "NEO4J_USER": "fixture", "NEO4J_PASSWORD": "fixture", "READ_ACCESS": "READ",
                           "guard_defects": lambda *a, **k: [], "write_text_atomic": write_text_atomic}
                    env.update({key: dataset for key in ("DATASET", "CQ_PATH")})
                    env.update({key: output for key in ("OUTPUT", "OUTPUT_PATH")})
                    execute(path, None, env)
                    with patch("common.atomic_io.os.replace", side_effect=error), contextlib.redirect_stdout(io.StringIO()):
                        with self.assertRaises(type(error)) as caught:
                            env["main"]()
                    self.assertIs(caught.exception, error)
                    self.assertEqual(output.read_bytes(), b"previous report")
                    self.assertEqual(sorted(p.name for p in temp.iterdir()), ["cq.json", "out.json"])
                    driver.close.assert_called_once()
                    with contextlib.redirect_stdout(io.StringIO()):
                        try:
                            env["main"]()
                        except SystemExit as exc:
                            self.assertEqual(exc.code, 0)
                    self.assertEqual(json.loads(output.read_text())["results"][0]["status"], "PASS")

    def test_ran1_tr_search_cleanup_atomic_report_and_retry(self):
        with patch.object(sys, "path", [str(ROOT / "scripts/common"), *sys.path]):
            from common.atomic_io import write_text_atomic
        path = ROOT / "scripts/tsg/RAN/formal/RAN1/phase-9/validation/01_validate_search.py"
        cases = ("valid", "query_error", "interrupt", "close_error", "interrupt_close_error",
                 "replace_error", "replace_interrupt", "init_error")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as td:
                temp = Path(td)
                dataset, output = temp / "cq.json", temp / "out.json"
                dataset.write_text(json.dumps({"questions": [{"id": "fixture", "category": "keyword",
                                                              "search_query": "synthetic"}]}))
                before = dataset.read_bytes()
                output.write_bytes(b"previous report")
                client = MagicMock()
                client.search.return_value = []
                factory = Mock(return_value=client)
                original = KeyboardInterrupt("original interruption") if "interrupt" in case else OSError("original failure")
                if case == "init_error":
                    factory.side_effect = original
                elif case in ("query_error", "interrupt", "interrupt_close_error"):
                    client.search.side_effect = original
                if "close_error" in case:
                    client.qdrant.close.side_effect = RuntimeError("close failure")
                env = {"Config": SimpleNamespace, "SearchClient": factory, "json": json, "datetime": datetime,
                       "sys": sys, "write_text_atomic": write_text_atomic,
                       "evaluate_cq": lambda *args: {"status": "PASS", "top_score": 0}}
                run = execute(path, {"run_validation"}, env)["run_validation"]
                config = SimpleNamespace(cq_path=dataset, output_path=output,
                                         collection_name="synthetic", qdrant_host="fixture", qdrant_port=0)
                for attempt in range(2):
                    caught, code = None, None
                    replacing = case.startswith("replace") and attempt == 0
                    boundary = patch("common.atomic_io.os.replace", side_effect=original) if replacing else contextlib.nullcontext()
                    with boundary, contextlib.redirect_stdout(io.StringIO()):
                        try:
                            code = run(config)
                        except BaseException as exc:
                            caught = exc
                    self.assertEqual(dataset.read_bytes(), before)
                    if attempt == 0 and case == "init_error":
                        self.assertEqual(code, 1)
                        client.qdrant.close.assert_not_called()
                    else:
                        client.qdrant.close.assert_called_once()
                    if attempt == 0 and case not in ("valid", "init_error"):
                        self.assertIsNotNone(caught)
                        if case != "close_error":
                            self.assertIs(caught, original)
                    else:
                        self.assertIsNone(caught)
                    if attempt == 0 and case != "valid":
                        self.assertEqual(output.read_bytes(), b"previous report")
                        self.assertEqual(sorted(p.name for p in temp.iterdir()), ["cq.json", "out.json"])
                    else:
                        self.assertEqual(code, 0)
                        self.assertEqual(json.loads(output.read_text())["results"][0]["evaluation"]["status"], "PASS")
                    factory.side_effect = None
                    client.reset_mock(side_effect=True)
                    client.search.return_value = []

    def test_ts_jsonld_requires_a_top_level_section_for_each_spec(self):
        import re
        from collections import Counter

        with patch.object(sys, "path", [str(ROOT / "scripts/common"), *sys.path]):
            from ontology.jsonld_context import canonical_document, require_core_rdf_targets

        cases = ("empty_graph", "valid", "valid_multi", "empty_spec",
                 "missing_has_section", "multi_empty_spec", "lower_only",
                 "unknown_target", "cross_spec", "duplicate_target",
                 "missing_spec_number", "wrong_spec_number")
        for wg in range(1, 4):
            path = ROOT / f"scripts/tsg/RAN/formal/RAN{wg}/phase-3/ts-parser/validate_ts_jsonld.py"
            for case in cases:
                with self.subTest(wg=wg, case=case), tempfile.TemporaryDirectory() as td:
                    temp = Path(td)
                    count = 0 if case == "empty_graph" else 2 if case in ("valid_multi", "multi_empty_spec", "cross_spec") else 1
                    specs = [{"@id": f"tdoc:spec/38_21{i}/Rel-18", "@type": "Spec",
                              "specNumber": f"38.21{i}", "specRelease": "Rel-18",
                              "specInRelease": "tdoc:release/Rel_18", "specVersion": "18.0.0",
                              "hasSection": [f"tdoc:section/38.21{i}-Rel-18-1"]}
                             for i in range(count)]
                    sections = [{"@id": f"tdoc:section/38.21{i}-Rel-18-1", "@type": "Section",
                                 "sectionId": f"38.21{i}-Rel-18-1", "sectionNumber": "1",
                                 "sectionTitle": "Scope", "level": 1, "isVoid": False,
                                 "belongsToSpec": spec["@id"], "specNumber": spec["specNumber"]}
                                for i, spec in enumerate(specs)]
                    if case in ("empty_spec", "missing_has_section", "multi_empty_spec"):
                        specs[-1]["hasSection"] = []
                        sections.pop()
                        if case == "missing_has_section":
                            del specs[-1]["hasSection"]
                    elif case == "lower_only":
                        sections[0]["level"] = 2
                    elif case == "unknown_target":
                        specs[0]["hasSection"] = ["tdoc:section/unknown-Rel-18-1"]
                    elif case == "cross_spec":
                        specs[0]["hasSection"], specs[1]["hasSection"] = specs[1]["hasSection"], specs[0]["hasSection"]
                    elif case == "duplicate_target":
                        specs[0]["hasSection"] *= 2
                    elif case == "missing_spec_number":
                        del sections[0]["specNumber"]
                    elif case == "wrong_spec_number":
                        sections[0]["specNumber"] = "38.999"
                    instances = temp / f"ontology/output/tsg/RAN/formal/instances/phase-3/RAN{wg}/release-aware"
                    instances.mkdir(parents=True)
                    for name, nodes in (("sections", sections), ("ts_tables", []),
                                        ("ts_figures", []), ("spec_extensions", specs)):
                        (instances / f"{name}.jsonld").write_text(json.dumps(
                            canonical_document({"@context": {}, "@graph": nodes})))
                    summary = temp / f"ontology/output/tsg/RAN/formal/parsed_ts/RAN{wg}/parse_summary_release.json"
                    summary.parent.mkdir(parents=True)
                    summary.write_text(json.dumps({"total": {"sections": len(sections),
                        "tables": 0, "figures": 0, "spec_releases": len(specs)},
                        "per_spec_release": {f'{spec["specNumber"]}_Rel-18': {
                            "sections": sum(s["belongsToSpec"] == spec["@id"] for s in sections)}
                            for spec in specs}}))
                    before = {str(p.relative_to(temp)): p.read_bytes() for p in temp.rglob("*") if p.is_file()}
                    env = {"argparse": argparse, "json": json, "sys": sys, "Counter": Counter, "Path": Path,
                           "defaultdict": defaultdict, "PROJECT_ROOT": temp,
                           "SID_RE": re.compile(r"^(.+?)-(Rel-\d+)-(.+)$"),
                           "require_core_rdf_targets": require_core_rdf_targets}
                    execute(path, None, env)
                    with patch.object(sys, "argv", [str(path)]), contextlib.redirect_stdout(io.StringIO()):
                        with self.assertRaises(SystemExit) as error:
                            env["main"]()
                    expected = 0 if case in ("valid", "valid_multi") else 1
                    self.assertEqual(error.exception.code, expected)
                    self.assertEqual(before, {str(p.relative_to(temp)): p.read_bytes()
                                              for p in temp.rglob("*") if p.is_file()})

    def test_spot_text_gate_rejects_empty_loaded_chunks(self):
        import difflib
        import random
        import re

        with patch.object(sys, "path", [str(ROOT / "scripts/common"), *sys.path]):
            from common.atomic_io import write_json_atomic

        path = ROOT / "scripts/tsg/RAN/formal/RAN1/phase-7/validation/02_spot_check_text.py"
        names = {"main", "load_all_chunks", "select_samples", "normalize_text",
                 "skeleton", "compare_texts", "exact_overlap",
                 "validate_giant_section_connectivity"}
        for case in ("empty_directory", "empty_chunks", "PASS", "WARN", "FAIL", "SKIP"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as td:
                temp = Path(td)
                chunks_base = temp / "chunks"
                chunks_base.mkdir()
                output = temp / "report.json"
                output.write_bytes(b"previous report")
                source = None
                if case != "empty_directory":
                    folder = chunks_base / "38.211"
                    folder.mkdir()
                    chunk = {"chunkId": "38.211-1-001", "sectionId": "38.211-1",
                             "sectionNumber": "1", "text": "a" * 100,
                             "tokenCount": 20, "totalChunks": 1, "chunkIndex": 1}
                    source = folder / "chunks.json"
                    source.write_text(json.dumps({"specNumber": "38.211",
                                                  "chunks": [] if case == "empty_chunks" else [chunk]}))
                    before = source.read_bytes()
                ref_text = "a" * 84 + "b" * 16 if case == "WARN" else "b" * 100 if case == "FAIL" else "a" * 100
                reference = Mock(return_value={"found": True, "text": ref_text,
                    "has_math": False, "omml_para_count": 0, "total_para_count": 1,
                    "table_count": 0})
                find_docx = Mock(return_value=None if case == "SKIP" else temp / "reference.docx")
                env = {"json": json, "random": random, "re": re, "difflib": difflib,
                       "datetime": datetime, "CHUNKS_BASE": chunks_base, "OUTPUT_PATH": output,
                       "write_json_atomic": write_json_atomic,
                       "find_docx_paths": find_docx, "extract_sources_independent": reference}
                execute(path, names, env)
                with patch.object(sys, "argv", [str(path)]), contextlib.redirect_stdout(io.StringIO()):
                    code = env["main"]()
                if source is not None:
                    self.assertEqual(source.read_bytes(), before)
                if case.startswith("empty"):
                    self.assertEqual(code, 1)
                    self.assertEqual(output.read_bytes(), b"previous report")
                    find_docx.assert_not_called()
                    reference.assert_not_called()
                else:
                    self.assertEqual(code, int(case in ("FAIL", "SKIP")))
                    report = json.loads(output.read_text())
                    self.assertEqual(report["totalSamples"], 1)
                    self.assertEqual(report["results"][0]["verdict"], case)
                    self.assertEqual(report["summary"],
                                     {key: int(key == case.lower()) for key in ("pass", "warn", "fail", "skip")})

    def test_email_kg_declarations_and_cli_exit(self):
        with patch.object(sys, "path", [str(ROOT / "scripts/common"), *sys.path]):
            from common.atomic_io import write_json_atomic
        from neo4j import READ_ACCESS
        shared = execute(ROOT / "scripts/tsg/RAN/email/common/phase-1/email_cq.py",
                         None, {"json": json, "Path": Path, "sys": sys,
                                "READ_ACCESS": READ_ACCESS, "write_json_atomic": write_json_atomic})
        for wg in range(1, 6):
            path = ROOT / f"scripts/tsg/RAN/email/RAN{wg}/phase-1/validation/01_validate_email_cq.py"
            tree = ast.parse(path.read_text())
            nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                     or (isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
                         and isinstance(node.test.left, ast.Name)
                         and node.test.left.id == "__name__")]
            for case in ("empty", "valid", "false", "missing_verdict", "numeric_verdict",
                         "no_data", "multiple_rows", "query_error"):
                with self.subTest(wg=wg, case=case), tempfile.TemporaryDirectory() as td:
                    temp = Path(td)
                    dataset, output = temp / "cq.json", temp / "out.json"
                    question = {"id": "fixture", "category": "synthetic",
                                "question": "Fixture?", "cypher": "RETURN true AS pass"}
                    dataset.write_text(json.dumps({"questions": [] if case == "empty" else [question]}))
                    before = dataset.read_bytes()
                    output.write_bytes(b"previous report")
                    row = {} if case == "missing_verdict" else {
                        "pass": True if case == "valid" else 1 if case == "numeric_verdict" else False}
                    rows = [] if case == "no_data" else [row, row] if case == "multiple_rows" else [row]
                    session = MagicMock()
                    session.run.return_value = rows
                    if case == "query_error":
                        session.run.side_effect = RuntimeError("synthetic query failure")
                    driver = MagicMock()
                    driver.session.return_value.__enter__.return_value = session
                    factory = Mock(return_value=driver)
                    env = {"__name__": "__main__", "json": json, "sys": sys,
                           "PROJECT_ROOT": temp, "CQ_DATASET_PATH": dataset, "OUTPUT_PATH": output,
                           "URI": "fixture", "AUTH": ("fixture", "fixture"), "__version__": "fixture",
                           "GraphDatabase": SimpleNamespace(driver=factory),
                           "load_dotenv": lambda *args, **kwargs: None,
                           "credentials": SimpleNamespace(neo4j_auth=lambda: ("fixture", "fixture")),
                           "_run_validation": shared["run_validation"]}
                    code = None
                    try:
                        with contextlib.redirect_stdout(io.StringIO()):
                            exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), env)
                    except SystemExit as exc:
                        code = exc.code
                    self.assertEqual(code, 0 if case == "valid" else 1)
                    self.assertEqual(dataset.read_bytes(), before)
                    if case == "empty":
                        factory.assert_not_called()
                        self.assertEqual(output.read_bytes(), b"previous report")
                    else:
                        report = json.loads(output.read_text())
                        self.assertEqual(report["metadata"]["total"], 1)
                        self.assertEqual(report["metadata"]["gate_100pct"], case == "valid")
                        self.assertEqual(report["results"][0]["status"] == "PASS", case == "valid")
                        session.run.assert_called_once_with("RETURN true AS pass")

    def test_formal_cypher_declarations_and_cli_exit(self):
        with patch.object(sys, "path", [str(ROOT / "scripts/common"), *sys.path]):
            from common.atomic_io import write_json_atomic, write_text_atomic
        from neo4j import READ_ACCESS
        paths = sorted((ROOT / "scripts/tsg/RAN/formal").glob(
            "RAN[1-5]/phase-[1-5]/validation/*_validate_cq_cypher.py"))
        self.assertEqual(len(paths), 25)
        for path in paths:
            tree = ast.parse(path.read_text())
            nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                     or (isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
                         and isinstance(node.test.left, ast.Name)
                         and node.test.left.id == "__name__")]
            for case in ("empty", "valid", "no_data", "guard_failure", "query_error"):
                with self.subTest(path=path.relative_to(ROOT), case=case), tempfile.TemporaryDirectory() as td:
                    temp = Path(td)
                    dataset, output = temp / "cq.json", temp / "out.json"
                    question = {"id": "fixture", "category": "synthetic", "question": "Fixture?",
                                "description": "Fixture", "cypher": "RETURN 1", "expected_min_rows": 1}
                    dataset.write_text(json.dumps({"metadata": {"version": "fixture"},
                                                   "questions": [] if case == "empty" else [question]}))
                    before = dataset.read_bytes()
                    output.write_bytes(b"previous report")
                    result = MagicMock()
                    rows = [] if case == "no_data" else [{"value": 1}]
                    result.__iter__.side_effect = lambda: iter(rows)
                    result.data.return_value = rows
                    session = MagicMock()
                    session.run.return_value = result
                    if case == "query_error":
                        session.run.side_effect = RuntimeError("synthetic query failure")
                    driver = MagicMock()
                    driver.session.return_value.__enter__.return_value = session
                    factory = Mock(return_value=driver)
                    env = {"__name__": "__main__", "json": json, "sys": sys, "datetime": datetime,
                           "GraphDatabase": SimpleNamespace(driver=factory), "URI": "fixture", "NEO4J_URI": "fixture",
                           "AUTH": ("fixture", "fixture"), "NEO4J_USER": "fixture", "NEO4J_PASSWORD": "fixture",
                           "READ_ACCESS": READ_ACCESS,
                           "guard_defects": lambda *args, **kwargs: ["synthetic anchor defect"] if case == "guard_failure" else [],
                           "get_cache_metadata_with_hash": lambda **kwargs: {"fixture": True},
                           "closing": contextlib.closing,
                           "write_json_atomic": write_json_atomic,
                           "write_text_atomic": write_text_atomic}
                    env.update({key: dataset for key in ("DATASET", "CQ_PATH", "CQ_INPUT", "CQ_DATASET_PATH")})
                    env.update({key: output for key in ("OUTPUT", "OUTPUT_PATH", "CQ_OUTPUT")})
                    code = 0
                    try:
                        with contextlib.redirect_stdout(io.StringIO()):
                            exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), env)
                    except SystemExit as exc:
                        code = exc.code
                    self.assertEqual(code == 0 or code is None, case == "valid")
                    self.assertEqual(dataset.read_bytes(), before)
                    if case == "empty":
                        factory.assert_not_called()
                        self.assertEqual(output.read_bytes(), b"previous report")
                    else:
                        report = json.loads(output.read_text())
                        self.assertEqual(len(report["results"]), 1)
                        self.assertEqual(report["results"][0]["status"] == "PASS", case == "valid")
                        session.run.assert_called_once_with("RETURN 1")

    def test_search_reports_control_exit(self):
        with patch.object(sys, "path", [str(ROOT / "scripts/common"), *sys.path]):
            from common.atomic_io import write_json_atomic, write_text_atomic
        for wg in range(1, 6):
            for phase in (7, 9):
                if wg == 5 and phase == 9:
                    continue
                path = ROOT / f"scripts/tsg/RAN/formal/RAN{wg}/phase-{phase}/validation/01_validate_search.py"
                for status, expected in (("PASS", 0), ("FAIL", 1), ("UNKNOWN", 1)):
                    with self.subTest(wg=wg, phase=phase, status=status), tempfile.TemporaryDirectory() as td:
                        temp = Path(td)
                        cq = {"id": "fixture", "category": "keyword", "search_query": "synthetic"}
                        (temp / "cq.json").write_text(json.dumps({"questions": [cq]}))
                        cfg = SimpleNamespace(cq_path=temp / "cq.json", output_path=temp / "out.json",
                                              collection_name="synthetic", qdrant_host="fixture", qdrant_port=0)
                        env = {"Config": SimpleNamespace, "SearchClient": Client, "json": json, "datetime": datetime, "sys": sys,
                               "write_json_atomic": write_json_atomic,
                               "write_text_atomic": write_text_atomic,
                               "evaluate_cq": lambda *args: {"status": status, "top_score": 0}}
                        run = execute(path, {"run_validation", "_run_with_client"}, env)["run_validation"]
                        with contextlib.redirect_stdout(io.StringIO()):
                            self.assertEqual(run(cfg), expected)
                        report = json.loads(cfg.output_path.read_text())
                        self.assertEqual(report["results"][0]["evaluation"]["status"], status)
                        self.assertEqual(report["metadata"]["unknownCount"], int(status == "UNKNOWN"))

    def test_ran5_search_gates(self):
        with patch.object(sys, "path", [str(ROOT / "scripts/common"), *sys.path]):
            from common.atomic_io import write_json_atomic, write_text_atomic
        for phase in (8, 9):
            path = ROOT / f"scripts/tsg/RAN/formal/RAN5/phase-{phase}/validation/01_validate_search.py"
            for status, expected in (("PASS", 0), ("FAIL", 1), ("UNKNOWN", 1)):
                with self.subTest(phase=phase, status=status), tempfile.TemporaryDirectory() as td:
                    temp = Path(td)
                    cfg = SimpleNamespace(cq_path=temp / "cq.json", chunks_path=temp / "absent", chunks_root=temp,
                                          output_path=temp / "out.json", skip_kg=True, collection_name="synthetic")
                    (temp / "cq.json").write_text(json.dumps({"questions": [{"cq_id": "fixture", "query": "synthetic"}]}))
                    cached_loader = Mock(name="load_slim_chunks")
                    gold_cache = {"fixture": "previous gold"}
                    env = {"argparse": argparse, "json": json, "datetime": datetime,
                           "Config": lambda **kwargs: cfg, "SearchClient": Client,
                           "load_slim_chunks": cached_loader, "_GOLD_CACHE": gold_cache,
                           "write_json_atomic": write_json_atomic, "write_text_atomic": write_text_atomic,
                           "evaluate_cq": lambda *args: {"status": status, "top_score": 0},
                           "validate_parsing": lambda *args: {"status": "OK"},
                           "phase_b": lambda *args: ([{"evaluation": {"status": status}}], {status: 1})}
                    name = "run_validation" if phase == 8 else "main"
                    names = {name, "save_results"} if phase == 8 else {name}
                    run = execute(path, names, env)[name]
                    with patch.object(sys, "argv", [str(path)]), contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(run(cfg) if phase == 8 else run(), expected)
                    report = json.loads(cfg.output_path.read_text())
                    self.assertEqual(report["searchResults"][0]["evaluation"]["status"], status)
                    self.assertEqual(report["parsingValidation"]["status"], "OK")
                    if phase == 8:
                        cached_loader.cache_clear.assert_called_once_with()
                        cached_loader.assert_not_called()
                        self.assertEqual(gold_cache, {})
                        self.assertEqual(report["metadata"]["totalCQs"], 1)
                        self.assertEqual(report["metadata"]["passCount"], int(status == "PASS"))

    def test_email_vdb_requires_all_declared_blocking_checks(self):
        with patch.object(sys, "path", [str(ROOT / "scripts/common"), *sys.path]):
            from common.atomic_io import write_json_atomic
        spec = importlib.util.spec_from_file_location(
            "spectra_email_vdb_verdicts_gate_test",
            ROOT / "scripts/tsg/RAN/email/common/phase-2/vdb_verdicts.py")
        shared = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(shared)
        questions = [{"id": f"CQ{i}", "category": "synthetic", "question": "Fixture?",
                      "blocking": i < 8} for i in range(1, 9)]
        cases = (("empty", []), ("record_only", questions[7:]),
                 ("missing_required", questions[1:]),
                 ("downgraded", [{**q, "blocking": False} for q in questions]),
                 ("missing_flag", [{k: v for k, v in q.items() if k != "blocking"}
                                   for q in questions]),
                 ("numeric_flag", [{**q, "blocking": int(q["blocking"])} for q in questions]))
        for wg in range(1, 6):
            path = ROOT / f"scripts/tsg/RAN/email/RAN{wg}/phase-2/validation/01_validate_email_vdb_cq.py"
            for label, declared in cases + (("valid", questions), ("failed_verdict", questions)):
                with self.subTest(wg=wg, case=label), tempfile.TemporaryDirectory() as td:
                    temp = Path(td)
                    dataset = temp / "cq.json"
                    output = temp / "out.json"
                    dataset.write_text(json.dumps({"questions": declared}))
                    before = dataset.read_bytes()
                    restream = Mock(return_value=(1, 0, set()))
                    neo = Mock(return_value=(1, {"m"}, {"d"}, {"t": {"S"}}))
                    client = Mock()
                    client.count.return_value = SimpleNamespace(count=1)
                    factory = Mock(return_value=client)
                    qd = {"msg_ids": {"m"}, "sender_keys": {"d"}, "thread_specs": {"t": {"S"}},
                          "msg_total_chunks": {"m": 1}, "max_token": 1, "scrolled": 1}
                    env = {"json": json, "CQ_DATASET_PATH": dataset, "OUTPUT_PATH": output,
                           "closing": contextlib.closing, "write_json_atomic": write_json_atomic,
                           "PROJECT_ROOT": temp, "LOAD_LOG": temp / "unused", "COLLECTION": "synthetic",
                           "QDRANT_HOST": "fixture", "QDRANT_PORT": 0, "EMBED_DIM": 3,
                           "DISTANCE_NAME": "Cosine", "HARD_MAX": 7500, "__version__": "fixture",
                           "restream_empty_and_total": restream, "fetch_neo4j": neo,
                           "parse_metrics_chunks": lambda *args: 2 if label == "failed_verdict" else 1,
                           "QdrantClient": factory, "vector_config": lambda *args: (3, "Cosine"),
                           "_build_verdicts": shared.build_verdicts,
                           "scroll_qdrant": lambda *args: qd}
                    execute(path, {"main", "build_verdicts"}, env)
                    with contextlib.redirect_stdout(io.StringIO()):
                        code = env["main"]()
                    self.assertEqual(code, 0 if label == "valid" else 1)
                    self.assertEqual(dataset.read_bytes(), before)
                    if label in ("valid", "failed_verdict"):
                        report = json.loads(output.read_text())
                        self.assertEqual(report["metadata"]["blocking_total"], 7)
                        self.assertEqual(report["metadata"]["gate_100pct"], label == "valid")
                        self.assertEqual(report["results"][-1]["status"], "RECORD")
                    else:
                        restream.assert_not_called()
                        neo.assert_not_called()
                        factory.assert_not_called()
                        self.assertFalse(output.exists())

    def test_empty_content_and_zero_token_fail_integrity(self):
        with patch.object(sys, "path", [str(ROOT / "scripts/common"), *sys.path]):
            from common.atomic_io import write_json_atomic
        for wg in range(1, 6):
            path = ROOT / f"scripts/tsg/RAN/formal/RAN{wg}/phase-6/validation/01_validate_data_integrity.py"
            for content, tokens, expected in (("", 100, 1), ("body", 0, 1), ("body", 100, 0)):
                with self.subTest(wg=wg, content=content, tokens=tokens), tempfile.TemporaryDirectory() as td:
                    temp = Path(td)
                    base = temp / "parsed"
                    folder = base / f"RAN{wg}#1/T1"
                    folder.mkdir(parents=True)
                    meta = {"tdocNumber": "T1", "meetingId": f"RAN{wg}#1", "source": [], "type": "Tdoc", "agendaItem": "1", "title": "Title"}
                    chunk = {"chunkIndex": 1, "sectionTitle": "Scope", "content": content, "tokenCount": tokens, "chunkId": "T1-001"}
                    (folder / "chunks.json").write_text(json.dumps({"tdocNumber": "T1", "meetingId": f"RAN{wg}#1", "metadata": meta, "chunks": [chunk]}))
                    env = {"Path": Path, "json": json, "sys": sys, "argparse": argparse, "defaultdict": defaultdict,
                           "datetime": datetime, "time": time, "PROJECT_ROOT": temp, "LOG_DIR": temp / "reports",
                           "write_json_atomic": write_json_atomic,
                           "DEFAULT_WG": f"RAN{wg}", "WG": f"RAN{wg}", "MIN_TOKENS": 100, "MAX_TOKENS": 2000}
                    execute(path, None, env)
                    env.update(get_parsed_base=lambda *args: base, tree_path=lambda *args, **kwargs: temp / "reports",
                               write_text_atomic=lambda path, text: path.write_text(text))
                    with patch.object(sys, "argv", [str(path)]), contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(env["main"](), expected)
                    report = json.loads(next((temp / "reports").rglob("*.json")).read_text())
                    self.assertEqual(report["summary"]["all_pass"], expected == 0)


if __name__ == "__main__":
    unittest.main()
