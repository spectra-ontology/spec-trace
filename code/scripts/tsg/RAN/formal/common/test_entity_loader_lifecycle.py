"""Entity loader main lifecycle; synthetic AST-only checks for Linux/WSL."""

from __future__ import annotations

import ast
import contextlib
import io
from pathlib import Path
import socket
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[5]


class EntityLoaderLifecycle(unittest.TestCase):
    """Four boundaries for each selected loader; no project module imports."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._guards = contextlib.ExitStack()
        cls.addClassCleanup(cls._guards.close)
        for owner, name in ((socket.socket, "connect"), (socket, "create_connection"),
                            (subprocess, "Popen"), (subprocess, "run")):
            cls._guards.enter_context(mock.patch.object(
                owner, name, side_effect=AssertionError("External execution forbidden")))

    def _check(self, fid: str, wg: str, performance: bool) -> None:
        name = "04_load_performance_requirements.py" if performance else "05_load_conformance_tests.py"
        path = ROOT / "scripts/tsg/RAN/formal" / wg / "phase-3/entity-loader" / name
        tree = ast.parse(path.read_text())
        main_node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        self.assertFalse(any(isinstance(node, (ast.Import, ast.ImportFrom)) for node in ast.walk(main_node)))
        for case in ("missing", "dry", "extract", "normal"):
            with self.subTest(fid=fid, wg=wg, loader=name, case=case):
                self._one(path, main_node, wg, performance, case)

    def _one(self, path, main_node, wg, performance, case) -> None:
        events, reports = [], []
        fault = ValueError("synthetic extraction failed")
        cfg = SimpleNamespace(sections_collection="tiny-sections", qdrant_host="fake",
                              qdrant_port=0, neo4j_port=0)
        client = SimpleNamespace(collection_exists=lambda name: events.append(("exists", name)) or case != "missing",
                                 close=lambda: events.append("qclose"))
        driver = SimpleNamespace(close=lambda: events.append("nclose"))
        row = SimpleNamespace(spec_number="38.141-1", section_id="38.141-1-Rel-19-1",
                              section_number="1", perf_req_name="요구사항", test_case_id="시험")
        expected = dict(spec_number=row.spec_number, section_id=row.section_id, section_number="1")
        expected["perf_req_name" if performance else "test_case_id"] = "요구사항" if performance else "시험"

        def extract(q, collection, *args):
            self.assertIs(q, client)
            self.assertEqual(collection, cfg.sections_collection)
            if not performance:
                specs = ({"38.141-1", "38.141-2", "38.181"} if wg == "RAN4" else
                         {"38.508-1", "38.509", "38.521-1", "38.521-2", "38.521-3", "38.521-4", "38.523-1", "38.533"})
                self.assertEqual(args, (specs,))
            events.append("extract")
            if case == "extract":
                raise fault
            return [row]

        def neo(config):
            self.assertIs(config, cfg)
            events.append("neo")
            return driver

        def load(db, cypher, rows):
            self.assertIs(db, driver)
            self.assertEqual(cypher, "synthetic-cypher")
            self.assertEqual(rows, [expected])
            events.append("load")
            return dict(requested=1, linked=1)

        def report(value):
            reports.append(vars(value).copy())
            events.append("report")
            return "synthetic-report"

        env = dict(RAN=wg, ENTITY_CLASS="PerformanceRequirement" if performance else "ConformanceTest",
                   RAN_CONFIGS={wg: cfg}, LoaderReport=lambda **kw: SimpleNamespace(**kw),
                   iso_now=lambda: "synthetic-time", get_qdrant=lambda config: client, get_neo4j=neo,
                   load_entities=load, write_report=report, sys=sys,
                   CYPHER_LOAD_PERF_REQ="synthetic-cypher", CYPHER_LOAD_CONF_TEST="synthetic-cypher",
                   extract_performance_requirements=extract, extract_conformance_tests=extract)
        exec(compile(ast.Module(body=[main_node], type_ignores=[]), str(path), "exec"), env)
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            if case == "extract":
                with self.assertRaises(ValueError) as caught:
                    env["main"]()
                self.assertIs(caught.exception, fault)
            else:
                self.assertEqual(env["main"](dry_run=case == "dry"), 1 if case == "missing" else 0)
        if case != "normal":
            self.assertNotIn("neo", events)
            self.assertEqual(reports, [])
        else:
            self.assertEqual(len(reports), 1)
            self.assertEqual((reports[0]["extracted"], reports[0]["loaded"]), (1, 1))
            self.assertEqual(reports[0]["links"], {"definedInSection": dict(requested=1, linked=1)})
            self.assertEqual(events.count("nclose"), 1)
        if case == "dry":
            self.assertEqual(ast.literal_eval(output.getvalue().split("Sample: ", 1)[1].strip()), [expected])
        self.assertEqual(events.count("qclose"), 1, "Qdrant owner must close exactly once")
        if case == "normal":
            self.assertLess(events.index("qclose"), events.index("neo"))

    def test_ran4_performance(self):
        self._check("F3398", "RAN4", True)

    def test_ran4_conformance(self):
        self._check("F3399", "RAN4", False)

    def test_ran5_conformance(self):
        self._check("F3522", "RAN5", False)


if __name__ == "__main__":
    unittest.main()
