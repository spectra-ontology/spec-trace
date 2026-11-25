#!/usr/bin/env python3
"""Spec: Phase-0/6/10 safety; Ontology: existing TS/CR identities; Cycle: 7.
배경: 전수조사에서 확인한 변환·삭제·인용 경계의 회귀를 고정한다.
사용: python3 -m unittest discover -s scripts/tsg/RAN/formal/common -p test_audit_safety_contracts.py
LLM/DB/FTP/LibreOffice 호출 없이 실제 함수와 격리 입력을 사용한다.
"""
import argparse
import ast
import contextlib
import io
import json
from pathlib import Path
import runpy
import sys
import tempfile
import time
from types import SimpleNamespace as NS
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[5]
COMMON = ROOT / "scripts/tsg/RAN/formal/common"

def function(path, name, env):
    tree = ast.parse(path.read_text())
    node = next(n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), env)
    return env[name]

class SafetyContracts(unittest.TestCase):
    def test_classified_points_stops_repeated_empty_cursor(self):
        from unittest.mock import Mock
        client = Mock()
        client.scroll.side_effect = [([], 'same'), ([], 'same'), AssertionError('unbounded scroll')]
        env = {'models': NS(Filter=NS, FieldCondition=NS, MatchAny=NS)}
        points = function(COMMON / 'reconcile_tdoc_classified_views.py', 'points_for', env)
        with self.assertRaisesRegex(RuntimeError, 'Repeated'):
            points(client, 'synthetic', ['R4-000001'])
        self.assertEqual(client.scroll.call_count, 2)

    def test_multi_part_citations(self):
        sys.path.insert(0, str(COMMON))
        try:
            import ts_citation
            for text in ("TR 37.863-01-01 clause 5.1", "clause 5.1 of TR 37.863-01-01"):
                refs, cleaned = ts_citation.split_external(text, {})
                self.assertIn(("37.863-01-01", "5.1"), refs)
                self.assertEqual(ts_citation.resolve(text, {}, "38.331", "Rel19", "none", {"37.863-01-01"}, {"37.863-01-01-Rel19-5.1", "38.331-Rel19-5.1"}), {"37.863-01-01-Rel19-5.1"})
        finally:
            sys.path.remove(str(COMMON))

    def test_cover_collision_and_clause_boundaries(self):
        env = {"_norm": lambda x: str(x).upper(), "decision": lambda *a: ("absent",), "NOT_LISTED": "absent", "rank": lambda *a: 0}
        recs = [NS(tdoc_number=n, cr_pack_id="P", source_path=n) for n in ("A", "B")]
        fixed = function(COMMON / "tsg_cr_decision.py", "reconcile_cover_numbers", env)(recs, lambda _: "C")
        self.assertEqual([r.tdoc_number for r in recs], ["C", "B"])
        self.assertEqual(list(fixed), ["A"])
        cl = function(COMMON / "cr_cq_gold.py", "cl", {})
        for clause, expected in (("5.2", True), ("5.2.1", True), ("5.20", False), ("5.20.1", False)):
            self.assertEqual(cl({"clauses": [clause]}, "5.2"), expected)

    def test_vertical_merge_requires_adjacent_surviving_row(self):
        def cell(text, col=0, merge="continue"):
            return NS(tc=text, col=col, vmerge=merge)
        env = {"DROP": "drop", "MARK": "mark", "cell_text": lambda tc, **kw: tc}
        table_rows = function(COMMON / "docx_text.py", "table_rows", env)
        for rows, expected in (([(False,[cell("A",merge="restart")]),(False,[cell("B",col=1,merge=None)]),(False,[cell("C")])], [["A"],["B"],["C"]]), ([(False,[cell("A",merge="restart")]),(False,[cell("C")])], [["A"],["A"]])):
            env["table_grid"] = lambda *a, **kw: rows
            self.assertEqual(table_rows(None), expected)

    def test_prune_checks_moved_count_before_delete(self):
        deleted=[]
        stale = dict(verdict="prune", name="old", twin="new", reason="", edges=1, meetings=[], element_id="o", twin_element_id="n")
        class Result:
            def __init__(self, row): self.row=row
            def single(self): return self.row
        class Session:
            def run(self, q, **kw):
                return Result({"labels":[], "props":{}, "rels":[]} if q == "snapshot" else {"anchors":2, "already":0})
            def execute_write(self, tx): return tx(self)
        session=Session()
        def run_tx(q, **kw):
            if q == "delete": deleted.append(True)
            return Result({"c":1})
        session.execute_write=lambda tx: tx(NS(run=run_tx))
        # This test isolates move-count ordering; preimage drift has its own regression suite.
        env={"_assert_prune_preimage":lambda *a:None, "backfill_provenance":NS(stale_nodes=lambda *a:[stale]), "Q_SNAPSHOT":"snapshot", "Q_ALREADY":"already", "Q_MOVE":"move", "Q_DELETE":"delete", "_plain":lambda x:x, "_record":lambda *a:ROOT/"unused", "PROJECT_ROOT":ROOT}
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(RuntimeError):
            function(COMMON / "prune_stale_backfill.py", "_prune_nodes", env)(session,"RAN1",True)
        self.assertFalse(deleted)

    @staticmethod
    def _docm_transform(wg):
        path = ROOT / f"scripts/tsg/RAN/formal/RAN{wg}/phase-10/data-collection/03_transform_meeting.py"
        with mock.patch.object(sys, "path", list(sys.path)):
            transform = runpy.run_path(str(path), run_name=f"docm_safety_RAN{wg}")
            from native_word_conversion import validate_docx
            transform["_fixture_validate_docx"] = validate_docx
            return transform

    @staticmethod
    def _write_docm_fixture(path):
        """같은 본문에서 그림·스타일·OLE 관계를 참조하는 작은 OOXML 패키지."""
        parts = {
            "[Content_Types].xml": b'''<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="png" ContentType="image/png"/><Default Extension="bin" ContentType="application/vnd.openxmlformats-officedocument.oleObject"/><Override PartName="/word/document.xml" ContentType="application/vnd.ms-word.document.macroEnabled.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/><Override PartName="/word/vbaProject.bin" ContentType="application/vnd.ms-office.vbaProject"/></Types>''',
            "_rels/.rels": b'''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="root" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>''',
            "word/document.xml": b'''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:o="urn:schemas-microsoft-com:office:office"><w:body><w:p><w:r><w:t>Synthetic body</w:t><w:drawing><a:blip r:embed="image"/></w:drawing><w:object><o:OLEObject r:id="equation"/></w:object></w:r></w:p></w:body></w:document>''',
            "word/_rels/document.xml.rels": b'''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="image" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png"/><Relationship Id="styles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/><Relationship Id="equation" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject" Target="embeddings/oleObject1.bin"/><Relationship Id="macro" Type="http://schemas.microsoft.com/office/2006/relationships/vbaProject" Target="vbaProject.bin"/></Relationships>''',
            "word/styles.xml": b'''<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:style w:type="paragraph" w:styleId="Normal"><w:rPr><w:color w:val="111111"/></w:rPr></w:style></w:styles>''',
            "word/media/image1.png": b"synthetic image one",
            "word/media/image2.png": b"synthetic image two",
            "word/embeddings/oleObject1.bin": b"synthetic equation object one",
            "word/vbaProject.bin": b"synthetic macro project",
        }
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, body in parts.items():
                archive.writestr(name, body)

    @staticmethod
    def _change_docm_part(path, part):
        with zipfile.ZipFile(path) as archive:
            contents = {info.filename: archive.read(info.filename) for info in archive.infolist()}
        if part.endswith(".rels"):
            contents[part] = contents[part].replace(b'Target="media/image1.png"', b'Target="media/image2.png"')
        elif part.endswith("styles.xml"):
            contents[part] = contents[part].replace(b'111111', b'222222')
        else:
            contents[part] += b" changed"
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, body in contents.items():
                archive.writestr(name, body)

    def test_docm_reuses_actual_repackaged_document(self):
        for wg in range(1, 6):
            transform = self._docm_transform(wg)
            with self.subTest(wg=wg), tempfile.TemporaryDirectory() as tmp:
                source = Path(tmp) / "a.docm"
                self._write_docm_fixture(source)
                target = source.with_suffix(".docx")
                self.assertTrue(transform["repackage_docm_to_docx"](source, target))
                transform["_fixture_validate_docx"](target)
                with zipfile.ZipFile(target) as archive:
                    self.assertNotIn("word/vbaProject.bin", archive.namelist())
                before = {p.name: p.read_bytes() for p in Path(tmp).iterdir()}
                self.assertEqual(transform["docm_target"](source), target)
                self.assertEqual({p.name: p.read_bytes() for p in Path(tmp).iterdir()}, before)

    def test_docm_nonbody_parts_select_fallback(self):
        parts = ("word/media/image1.png", "word/_rels/document.xml.rels",
                 "word/styles.xml", "word/embeddings/oleObject1.bin")
        for wg in range(1, 6):
            transform = self._docm_transform(wg)
            for part in parts:
                with self.subTest(wg=wg, part=part), tempfile.TemporaryDirectory() as tmp:
                    source = Path(tmp) / "a.docm"
                    self._write_docm_fixture(source)
                    target = source.with_suffix(".docx")
                    self.assertTrue(transform["repackage_docm_to_docx"](source, target))
                    self._change_docm_part(target, part)
                    transform["_fixture_validate_docx"](target)
                    with zipfile.ZipFile(source) as left, zipfile.ZipFile(target) as right:
                        self.assertEqual(left.read("word/document.xml"), right.read("word/document.xml"))
                    before = {p.name: p.read_bytes() for p in Path(tmp).iterdir()}
                    selected = transform["docm_target"](source)
                    self.assertEqual({p.name: p.read_bytes() for p in Path(tmp).iterdir()}, before)
                    fallback = Path(tmp) / "a.docm.docx"
                    self.assertEqual(selected, fallback)
                    self.assertTrue(transform["repackage_docm_to_docx"](source, fallback))
                    self.assertEqual(transform["docm_target"](source), fallback)
                    self.assertEqual(source.read_bytes(), before[source.name])
                    self.assertEqual(target.read_bytes(), before[target.name])

    def test_docm_secondary_collision_preserves_package_parts(self):
        parts = ("word/media/image1.png", "word/_rels/document.xml.rels",
                 "word/styles.xml", "word/embeddings/oleObject1.bin")
        for wg in range(1, 6):
            transform = self._docm_transform(wg)
            for part in parts:
                with self.subTest(wg=wg, part=part), tempfile.TemporaryDirectory() as tmp:
                    source = Path(tmp) / "a.docm"
                    self._write_docm_fixture(source)
                    target = source.with_suffix(".docx")
                    fallback = Path(tmp) / "a.docm.docx"
                    for output in (target, fallback):
                        self.assertTrue(transform["repackage_docm_to_docx"](source, output))
                        self._change_docm_part(output, part)
                    before = {p.name: p.read_bytes() for p in Path(tmp).iterdir()}
                    try:
                        with self.assertRaises(FileExistsError):
                            transform["docm_target"](source)
                    finally:
                        self.assertEqual({p.name: p.read_bytes() for p in Path(tmp).iterdir()}, before)

    def test_docm_ambiguous_part_names_are_not_reused(self):
        for wg in range(1, 6):
            transform = self._docm_transform(wg)
            for side in ("source", "target"):
                for duplicate in ("word/media/image1.png", "word/media/IMAGE1.png"):
                    with self.subTest(wg=wg, side=side, duplicate=duplicate), tempfile.TemporaryDirectory() as tmp:
                        source = Path(tmp) / "a.docm"
                        self._write_docm_fixture(source)
                        target = source.with_suffix(".docx")
                        self.assertTrue(transform["repackage_docm_to_docx"](source, target))
                        changed = source if side == "source" else target
                        with zipfile.ZipFile(changed, "a") as archive:
                            body = archive.read("word/media/image1.png")
                            if duplicate == "word/media/image1.png":
                                with self.assertWarnsRegex(UserWarning, "Duplicate name"):
                                    archive.writestr(duplicate, body)
                            else:
                                archive.writestr(duplicate, body)
                        before = {p.name: p.read_bytes() for p in Path(tmp).iterdir()}
                        self.assertFalse(transform["same_document_body"](source, target))
                        self.assertEqual({p.name: p.read_bytes() for p in Path(tmp).iterdir()}, before)

    def test_docm_unmodified_media_and_ole_use_bounded_reads(self):
        original_read = zipfile.ZipExtFile.read
        for wg in range(1, 6):
            transform = self._docm_transform(wg)
            with self.subTest(wg=wg), tempfile.TemporaryDirectory() as tmp:
                source = Path(tmp) / "a.docm"
                self._write_docm_fixture(source)
                target = source.with_suffix(".docx")
                self.assertTrue(transform["repackage_docm_to_docx"](source, target))
                reads = []
                def bounded_read(stream, size=-1):
                    if stream.name.endswith((".png", ".bin")):
                        self.assertGreaterEqual(size, 0)
                        self.assertLessEqual(size, 1 << 20)
                        reads.append((stream.name, size))
                    return original_read(stream, size)
                with mock.patch.object(zipfile.ZipExtFile, "read", bounded_read):
                    self.assertTrue(transform["same_document_body"](source, target))
                self.assertTrue(any(name.endswith(".png") for name, _ in reads))
                self.assertTrue(any(name.endswith("oleObject1.bin") for name, _ in reads))

    def test_not_ready_exit_and_nested_report_scan(self):
        for wg in range(1, 6):
            with self.subTest(wg=wg), tempfile.TemporaryDirectory() as tmp, \
                    mock.patch.object(sys, "path", list(sys.path)), mock.patch.dict(sys.modules):
                # 각 WG의 core facade를 새로 읽고 실제 CLI의 보고서 확인·하위 폴더 탐색을 실행한다.
                for name in list(sys.modules):
                    if name == "core" or name.startswith("core."):
                        del sys.modules[name]
                path = ROOT / f"scripts/tsg/RAN/formal/RAN{wg}/phase-10/data-collection/01_download_meeting.py"
                module = runpy.run_path(str(path), run_name=f"download_safety_RAN{wg}")
                main = module["main"]
                env = main.__globals__
                env["SESSION"].close()
                root = Path(tmp)
                meeting = f"TSGR{wg}_123"
                base_url = f"https://example.invalid/{meeting}/"
                scan = mock.Mock()
                session = mock.Mock()
                session.get.side_effect = AssertionError("실제 네트워크 호출 금지")

                def configure(selected_wg):
                    self.assertEqual(selected_wg, f"RAN{wg}")
                    env.update(WG=selected_wg, BASE_FTP_URL="https://example.invalid/",
                               SOURCE_DIR=root / "source", LOGS_DIR=root / "logs")

                replacements = dict(_configure_wg=configure, SESSION=session,
                                    check_final_report=mock.Mock(return_value={
                                        "status": "NOT_READY", "reason": "pending"}),
                                    scan_ftp_flat=scan)
                with mock.patch.dict(env, replacements), \
                        mock.patch.object(sys, "argv", [str(path), meeting, "--dry-run"]), \
                        contextlib.redirect_stdout(io.StringIO()), \
                        self.assertRaises(SystemExit) as caught:
                    main()
                self.assertEqual(caught.exception.code, env["EXIT_NOT_READY"])
                scan.assert_not_called()
                self.assertFalse((root / "logs").exists())

                calls = []
                def ftp(url):
                    calls.append(url)
                    if url == base_url + "Report/nested/":
                        final = url + "final.docx"
                        return [final], [], {final: "10"}
                    return [], ["nested"] if url == base_url + "Report/" else [], {}

                replacements.update(check_final_report=lambda _: {
                    "status": "COMPLETE", "file": "final.docx"},
                    discover_report_folders=lambda _: ["Report"], scan_ftp_flat=ftp)
                with mock.patch.dict(env, replacements), \
                        mock.patch.object(sys, "argv", [str(path), meeting, "--dry-run"]), \
                        contextlib.redirect_stdout(io.StringIO()):
                    main()
                input_file = root / "logs" / f"aria2c_input_{meeting}.txt"
                self.assertIn(base_url + "Report/nested/final.docx", input_file.read_text())
                self.assertIn(base_url + "Report/nested/", calls)
                self.assertFalse((root / "source").exists())
                session.get.assert_not_called()

    def test_metadata_dry_run_preserves_existing_report(self):
        import os
        with mock.patch.object(sys, "path", [str(ROOT / "scripts/common"), str(COMMON), *sys.path]):
            from common import credentials
            import tdoc_body_source_metadata
            for wg in range(1, 6):
                with self.subTest(wg=wg), tempfile.TemporaryDirectory() as tmp, \
                        mock.patch.object(credentials, "neo4j_auth", return_value=("fixture", "fixture")), \
                        mock.patch.dict(os.environ):
                    os.environ.pop("NEO4J_URI", None)
                    os.environ.pop("NEO4J_BOLT", None)
                    path = ROOT / f"scripts/tsg/RAN/formal/RAN{wg}/phase-6/metadata/01_enrich_metadata.py"
                    module = runpy.run_path(str(path), run_name=f"metadata_safety_RAN{wg}")
                    main = module["main"]
                    env = main.__globals__
                    root = Path(tmp)
                    report = root / "metadata_enrich_report.json"
                    report.write_text("preserve")
                    target = f"R{wg}-0000001"
                    output = root / f"RAN{wg}#123" / target / "chunks.json"
                    output.parent.mkdir(parents=True)
                    output.write_text(json.dumps({"metadata": {}, "chunks": [{"content": "synthetic body"}]}))
                    original = output.read_bytes()
                    metadata = {target: dict(title="synthetic title", type="discussion",
                        source=["synthetic company"], release="Rel-19", agendaItem="1")}
                    driver = mock.Mock()
                    update = mock.Mock(wraps=module["update_chunks_files"])
                    fetch = mock.Mock(return_value=metadata)
                    argv = [str(path), "--dry-run"]
                    if wg != 2:
                        argv += ["--wg", f"RAN{wg}"]
                    with mock.patch.dict(env, {"get_parsed_base": lambda *args: root,
                            "GraphDatabase": NS(driver=lambda *a, **kw: driver),
                            "fetch_all_metadata": fetch, "update_chunks_files": update}), \
                            mock.patch.object(tdoc_body_source_metadata, "project",
                                side_effect=lambda root, wg, view, number, payload: payload), \
                            mock.patch.object(sys, "argv", argv), \
                            contextlib.redirect_stdout(io.StringIO()):
                        status = main()
                    self.assertEqual(status, 0)
                    expected_kwargs = {"dry_run": True}
                    if wg in (4, 5):
                        expected_kwargs["wg"] = f"RAN{wg}"
                    update.assert_called_once_with(root, metadata, **expected_kwargs)
                    fetch.assert_called_once_with(driver, tdoc_prefix=f"R{wg}-")
                    driver.close.assert_called_once_with()
                    self.assertEqual(report.read_text(), "preserve")
                    self.assertEqual(output.read_bytes(), original)

    def test_metadata_update_resolves_source_overlay_in_standalone_path(self):
        import builtins
        import importlib.machinery
        from unittest.mock import patch
        with patch.object(sys, "path", [str(ROOT / "scripts/common"), *sys.path]):
            from common.atomic_io import write_json_atomic

        path = ROOT / "scripts/tsg/RAN/formal/RAN2/phase-6/metadata/01_enrich_metadata.py"
        ordinary_import = builtins.__import__
        for dry_run in (False, True):
            with self.subTest(dry_run=dry_run), tempfile.TemporaryDirectory() as tmp:
                target = "R2-0000001"
                output = Path(tmp) / "meeting" / target / "chunks.json"
                output.parent.mkdir(parents=True)
                output.write_text(json.dumps({"metadata": {"extra": "preserve"},
                                              "chunks": [{"text": "synthetic body"}]}))
                before = output.read_bytes()
                calls = []
                def project(root, wg, view, number, payload):
                    calls.append((root, wg, view, number))
                    return {**payload, "coverSourceTitle": "synthetic cover"}
                def checked_import(name, *args, **kwargs):
                    if name == "tdoc_body_source_metadata":
                        spec = importlib.machinery.PathFinder.find_spec(name, sys.path)
                        if spec is None:
                            raise ModuleNotFoundError("No module named 'tdoc_body_source_metadata'")
                        self.assertEqual(Path(spec.origin), COMMON / "tdoc_body_source_metadata.py")
                        return NS(project=project)
                    return ordinary_import(name, *args, **kwargs)
                isolated = [value for value in sys.path
                            if Path(value or ".").resolve() != COMMON.resolve()]
                env = {"Path": Path, "json": json, "sys": sys, "PROJECT_ROOT": ROOT,
                       "__file__": str(path), "parent_tdoc_number": lambda value: value,
                       "write_json_atomic": write_json_atomic}
                data = {target: dict(title="registration", type="CR", source=["company"],
                                     release="Rel-18", agendaItem="1")}
                with patch.object(sys, "path", isolated), patch.object(builtins, "__import__", checked_import):
                    stats = function(path, "update_chunks_files", env)(Path(tmp), data, dry_run=dry_run)
                self.assertEqual(stats["errors"], [])
                self.assertEqual(stats["updated"], 1)
                self.assertEqual(calls, [(ROOT, "RAN2", "tdoc", target)])
                if dry_run:
                    self.assertEqual(output.read_bytes(), before)
                else:
                    after = json.loads(output.read_text())
                    self.assertEqual(after["chunks"], [{"text": "synthetic body"}])
                    self.assertEqual(after["metadata"]["extra"], "preserve")
                    self.assertEqual(after["metadata"]["coverSourceTitle"], "synthetic cover")



class SourceExtensionRollback(unittest.TestCase):
    """Execute the real projection CLI with isolated files and a fake DB."""
    def scenario(self, mode):
        import copy
        import gzip
        import hashlib
        import os
        from unittest.mock import patch

        source = COMMON / "reconcile_tdoc_source_extensions.py"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p4 = root / "ontology/output/tsg/RAN/formal/parsed_cr/RAN4/cr_documents.json"
            p4.parent.mkdir(parents=True)
            p4.write_text('{"documents":[]}')
            canonical = root / "ontology/output/tsg/RAN/formal/instances/phase-4/RAN4/cr_extensions.jsonld"
            canonical.parent.mkdir(parents=True)
            original = json.dumps({"@graph": [{"@id": "tdoc:R4-0000001", "@type": "tdoc:CR"}]}).encode()
            canonical.write_bytes(original)
            parser = root / "scripts/tsg/RAN/formal/RAN4/phase-4/cr-parser/01_parse_cr_documents.py"
            parser.parent.mkdir(parents=True)
            parser.touch()
            metadata = root / "metadata.json"
            metadata.write_text(json.dumps({
                "mode": "applied_exact_readback", "wg": "RAN4", "sourceFences": {},
                "phase4DocumentsAfterSha256": "unused",
                "phase4": {"projection": {"sourceSupplements": [], "sourceClassifications": []},
                           "sourceSupplementsAdded": ["R4-0000001"]}}))
            before = {"nodes": [{"properties": {"id": "tdoc:R4-0000001"}, "labels": ["CR"]}], "edges": []}
            state = copy.deepcopy(before)
            properties = {"tdoc:R4-0000001": {"reasonForChange": "actual source form"}}
            foreign = b'{"@graph":[],"foreign_concurrent_change":"preserve"}\n'
            class Driver:
                def __enter__(self): return self
                def __exit__(self, *args): pass
                def session(self, **kwargs): return self
                def execute_write(self, callback): return callback(self)
            def apply(tx, proposal, preimage):
                if mode == "interrupt":
                    raise KeyboardInterrupt("synthetic interrupt")
                if mode == "foreign":
                    canonical.write_bytes(foreign)
                elif mode == "removed":
                    canonical.unlink()
                elif mode == "same_bytes_replacement":
                    replacement = canonical.with_suffix(".new")
                    replacement.write_bytes(canonical.read_bytes())
                    replacement.replace(canonical)
                if mode in {"success", "acknowledgement_lost", "committed_interrupt"}:
                    state["nodes"][0]["properties"].update(properties["tdoc:R4-0000001"])
                if mode == "committed_interrupt":
                    raise KeyboardInterrupt("synthetic interrupt after commit")
                if mode != "success":
                    raise RuntimeError("synthetic transaction failure")
                return copy.deepcopy(state)
            env = {
                "argparse": argparse, "copy": copy, "gc": NS(collect=lambda: None),
                "gzip": gzip, "hashlib": hashlib, "json": json, "os": os, "Path": Path,
                "ROOT": root, "__file__": str(root / "tool.py"),
                "FIELDS": {"reason_for_change": "reasonForChange"},
                "sha": lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest() if Path(p).exists() else "unused",
                "check_sources": lambda *args: None, "load_module": lambda *args: object(),
                "source_properties": lambda *args: properties,
                "write_text_atomic": lambda p, text: Path(p).write_text(text),
                "durable_json": lambda p, value: Path(p).write_text(json.dumps(value)),
                "review_artifacts": NS(__file__=str(root / "review.py")),
                "guarded": NS(
                    __file__=str(root / "guarded.py"),
                    GraphDatabase=NS(driver=lambda *args, **kwargs: Driver()),
                    axis=NS(bolt_uri=lambda wg: "fake"), credentials=NS(neo4j_auth=lambda: None),
                    READ_ACCESS="READ", snapshot=lambda *args: copy.deepcopy(state),
                    check_endpoints=lambda *args: None, digest=lambda value: json.dumps(value, sort_keys=True),
                    apply_transaction=apply)}
            for name in ("project_extensions", "expected_live"):
                function(source, name, env)
            error = None
            with patch.object(sys, "argv", ["tool", "--wg", "RAN4", "--metadata-receipt",
                                           str(metadata), "--out", str(root / "result.json"), "--apply"]), \
                    contextlib.redirect_stdout(io.StringIO()):
                try:
                    function(source, "main", env)()
                except (RuntimeError, KeyboardInterrupt) as caught:
                    error = caught
            return (canonical.read_bytes() if canonical.exists() else None,
                    original, foreign, json.loads((root / "result.json").read_text()), error)

    def test_foreign_change_and_removal_survive_failed_transaction(self):
        for mode in ("foreign", "removed"):
            with self.subTest(mode=mode):
                current, original, foreign, report, error = self.scenario(mode)
                self.assertIsInstance(error, RuntimeError)
                self.assertEqual(current, foreign if mode == "foreign" else None)
                self.assertEqual(report["mode"], "canonical_changed_requires_review")
                self.assertIn("canonicalRollbackSkipped", report)

    def test_only_own_postimage_is_rolled_back_after_failure(self):
        for mode in ("owned", "same_bytes_replacement"):
            with self.subTest(mode=mode):
                current, original, foreign, report, error = self.scenario(mode)
                self.assertIsInstance(error, RuntimeError)
                self.assertEqual(current, original)
                self.assertEqual(report["mode"], "transaction_failed_rollback_verified")

    def test_interrupt_restores_owned_canonical_postimage(self):
        current, original, _, report, error = self.scenario('interrupt')
        self.assertIsInstance(error, KeyboardInterrupt)
        self.assertEqual(current, original)
        self.assertEqual(report['mode'], 'transaction_failed_rollback_verified')

    def test_interrupt_after_commit_preserves_projection_and_interrupt(self):
        current, _, _, report, error = self.scenario('committed_interrupt')
        self.assertIsInstance(error, KeyboardInterrupt)
        self.assertEqual(json.loads(current)['@graph'][0]['tdoc:reasonForChange'], 'actual source form')
        self.assertEqual(report['mode'], 'transaction_interrupted_live_projection_verified')

    def test_success_and_committed_acknowledgement_recovery_keep_projection(self):
        for mode in ("success", "acknowledgement_lost"):
            with self.subTest(mode=mode):
                current, original, foreign, report, error = self.scenario(mode)
                self.assertIsNone(error)
                self.assertEqual(report["mode"], "applied_exact_readback")
                self.assertEqual(json.loads(current)["@graph"][0]["tdoc:reasonForChange"],
                                 "actual source form")
                self.assertEqual(report.get("transactionAcknowledgementRecoveredByExactReadback", False),
                                 mode == "acknowledgement_lost")

class QdrantReconciliationLifetime(unittest.TestCase):
    """Run each real client-owned tail with tiny preflight state and no services."""
    def test_supplement_cleanup_note_preserves_existing_context(self):
        with mock.patch.object(sys, "path", [str(ROOT / "scripts/common"), *sys.path]):
            from common.exception_notes import add_exception_note
        error = KeyboardInterrupt('primary interruption')
        notes = error.__notes__ = ['original context']
        note = function(COMMON / 'tdoc_supplement_vectors.py', '_note_secondary_error',
                        {'add_exception_note': add_exception_note})
        note(error, 'first cleanup failure')
        note(error, 'second cleanup failure')
        self.assertIs(error.__notes__, notes)
        self.assertEqual(notes, ['original context', 'first cleanup failure', 'second cleanup failure'])

    def tail(self, filename, name, env):
        source = COMMON / filename
        tree = ast.parse(source.read_text())
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
        start = next(i for i, n in enumerate(node.body) if isinstance(n, ast.Assign)
                     and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name)
                     and n.value.func.id == 'QdrantClient')
        # Only preflight is supplied by fixtures; execute the actual constructor,
        # complete client-owned body and finally block, including normal returns.
        node.body = node.body[start:]
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), 'exec'), env)
        return env[name]

    def test_success_error_and_interrupt_close_each_real_client_owned_tail(self):
        from collections import Counter
        from copy import deepcopy
        import gzip
        import hashlib
        from unittest.mock import Mock
        with mock.patch.object(sys, "path", [str(ROOT / "scripts/common"), *sys.path]):
            from common.service_endpoints import QDRANT_URL
            from common.exception_notes import add_exception_note
        for route in ('slides', 'classified', 'metadata', 'resume', 'identity'):
            for error_type in (None, ValueError, KeyboardInterrupt):
                with self.subTest(route=route, error=error_type), tempfile.TemporaryDirectory() as folder:
                    root = Path(folder)
                    client = Mock()
                    client.count.return_value = NS(count=0)
                    client.get_collection.return_value = NS(config=NS(params=NS(vectors=NS(size=2, distance='Cosine'))))
                    env = dict(sys=sys, json=json, gzip=gzip, Path=Path, ROOT=root,
                               Counter=Counter, deepcopy=deepcopy,
                               add_exception_note=add_exception_note,
                               QdrantClient=lambda **kwargs: client, QDRANT_URL=QDRANT_URL,
                               sha=lambda path: 'sha',
                               digest=lambda value: 'sha', check_fence=lambda *a: None,
                               source_fence=lambda *a: None, durable_json=lambda *a: None,
                               full_points=lambda *a: [], remaining_payload_groups=lambda *a: [])
                    if route == 'slides':
                        keys = ['11794328178286834859', '13055629634629439117'] + [str(i) for i in range(18)]
                        before = {k: dict(id=k, payload=dict(chunkId=k, content='tiny', tokenCount=1), vector=[1.,0.]) for k in keys}
                        historical = root / 'before.gz'
                        historical.write_bytes(gzip.compress(json.dumps({'points': list(before.values())}).encode()))
                        generated = {k: before[k]['payload'] for k in keys}
                        env.update(proposal={'fullBeforeImages': {'pointsPath': historical.name, 'pointsSHA256': 'sha'},
                                             'points': [dict(pointId=k, proposedPayload=before[k]['payload']) for k in keys[:2]]},
                                   collection='fake', rows=[{'target': 'R5-tiny'}], snapshot=lambda *a: before,
                                   generated=generated, current_chunks=generated, artifact_images=[],
                                   report={'changedPoints': []}, fences={}, output=root,
                                   require_local=lambda *a: NS(), load_local_tokenizer=lambda *a: None,
                                   same_point=lambda a,b: a==b, atomic_json=lambda *a: None,
                                   atomic_bytes=lambda path,raw: path.write_bytes(raw), encoded=lambda value: json.dumps(value).encode(),
                                   asdict=lambda value: {}, model_files=lambda *a: [],
                                   subprocess=NS(check_output=lambda *a,**kw: ''), assert_fence=lambda *a: None)
                        fn = self.tail('reconcile_pptx_search_text.py', 'reconcile', env)
                        invoke = lambda: fn(root/'proposal.json', root, apply=False)
                        first = client.count
                    elif route == 'classified':
                        payload = root / 'payload.gz'
                        payload.write_bytes(gzip.compress(b'{"1":{"text":"tiny"}}'))
                        out = root / 'report.json'
                        out.write_text(json.dumps(dict(status='complete', sourceFiles={},
                            preparedPayloads={'path':'unused','sha256':'sha'}, targets=['R4-tiny'],
                            finalPointsSha256='sha', artifactAfterSha256='sha')))
                        env.update(args=NS(out=out), collection='fake', artifact=root/'artifact',
                                   encoder_for=lambda *a: NS(dim=2),
                                   review_artifacts=NS(resolve_recorded_path=lambda *a: payload),
                                   points_for=lambda *a: {1: {'payload': {'text':'tiny'}}},
                                   validate_new_points=lambda *a: {})
                        fn = self.tail('reconcile_tdoc_classified_views.py', 'main', env)
                        invoke = fn
                        first = client.get_collection
                    elif route == 'metadata':
                        p4 = root / 'p4.json'
                        env.update(args=NS(wg='RAN1', apply=False, out=root/'report.json'), targets=set(), fields={},
                                   body_only_targets=set(), fences={}, added=[], projection={},
                                   p4before={'documents':[]}, p4after={'documents':[]}, p4path=p4,
                                   files={p4:{'beforeSha256':'sha','after':{}}}, tdoc_inventory={},
                                   crprojection={'changed':[]})
                        fn = self.tail('reconcile_tdoc_source_metadata.py', 'main', env)
                        invoke = fn
                        first = client.count
                    elif route == 'resume':
                        env.update(args=NS(out=root/'report.json',wg='RAN1'), inventory={
                            'fields':{}, 'collections':{'fake':{'updates':[],'beforeCount':0}},
                            'appliedCollections':[]}, before={'fake':[]}, fences={})
                        fn = self.tail('reconcile_tdoc_source_metadata.py', 'resume_projection', env)
                        invoke = lambda: fn(env['args'])
                        first = client.count
                    else:
                        (root / 'config.json').write_text('{"resolutions": []}')
                        save = Mock()
                        env.update(CONFIG='config.json', hashlib=hashlib, report={}, save=save)
                        fn = self.tail('reconcile_tr_source_identity.py', 'main', env)
                        invoke = fn
                        first = save
                    if error_type is not None:
                        primary = error_type('primary synthetic error')
                        original_notes = primary.__notes__ = ['original synthetic context']
                        first.side_effect = primary
                        client.close.side_effect = OSError('secondary close failure')
                        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(error_type) as caught:
                            invoke()
                        self.assertIs(caught.exception, primary)
                        self.assertIs(type(caught.exception), error_type)
                        self.assertIs(caught.exception.__notes__, original_notes)
                        self.assertEqual(original_notes, ['original synthetic context',
                            'Qdrant client close also failed: OSError: secondary close failure'])
                    else:
                        with contextlib.redirect_stdout(io.StringIO()):
                            invoke()
                    client.close.assert_called_once_with()
                    if route == 'resume' and error_type is None:
                        client.close.reset_mock()
                        client.close.side_effect = OSError('standalone close failure')
                        with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(
                                OSError, 'standalone close failure'):
                            invoke()
                        client.close.assert_called_once_with()

if __name__ == "__main__": unittest.main()
