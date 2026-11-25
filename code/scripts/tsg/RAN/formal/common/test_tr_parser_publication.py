"""TR 청크와 요약 파일의 게시 실패·중단 시 이전 결과 보존을 확인합니다."""
import ast
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[5]


def atomic_writer():
    source = ROOT / "scripts/common/common/atomic_io.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef)
             and n.name in {"_atomic_writer", "write_text_atomic"}]
    env = dict(contextmanager=contextlib.contextmanager, Path=Path, os=os, tempfile=tempfile)
    exec(compile(ast.Module(nodes, []), str(source), "exec"), env)
    return env["write_text_atomic"]


def publication(source, output, kind, bad):
    """파서는 실행하지 않고 실제 저장 함수 또는 main의 마지막 요약 저장문을 읽습니다."""
    tree = ast.parse(source.read_text(encoding="utf-8"))
    name = "save_chunks" if kind == "chunks" else "main"
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    if kind == "summary":
        start = next(i for i, n in enumerate(node.body)
                     if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == "summary_path" for t in n.targets))
        node.body = node.body[start:]
    env = dict(Path=Path, json=json, OUTPUT_DIR=output, write_text_atomic=atomic_writer(),
               datetime=SimpleNamespace(now=lambda: SimpleNamespace(isoformat=lambda: "synthetic")),
               logger=SimpleNamespace(info=lambda *a: None), all_tr_numbers=["99.999"],
               total_sections=1, total_excluded=0, total_giant=0, total_chunks=1,
               all_chunk_ids={"synthetic"}, all_section_ids={"synthetic"}, dup_chunk_ids=[],
               all_stats={"bad": object()} if bad else {"설명": "새 결과"})
    exec(compile(ast.Module([node], []), str(source), "exec"), env)
    if kind == "chunks":
        chunks = [{"bad": object()}] if bad else [{"text": "새 결과"}]
        return lambda: env[name](chunks, {"totalChunks": 1}, "99.999")
    return env[name]


def phase5_module(wg, filename):
    """실제 진입점을 읽으며 DOCX·근거 파일 읽기는 각 검사에서 대체합니다."""
    source = ROOT / "scripts/tsg/RAN/formal" / wg / "phase-5/tr-parser" / filename
    spec = importlib.util.spec_from_file_location(f"tr_publication_{wg}_{source.stem}", source)
    module = importlib.util.module_from_spec(spec)
    with patch.object(sys, "path", [str(source.parent), *sys.path]):
        spec.loader.exec_module(module)
    return module


def report_row():
    return dict(trNumber="38.999", trVersion="1.0.0", trTitle="새 결과",
                trStatus="Completed", scope="합성 범위", conclusions="합성 결론",
                targetRelease="Rel-19", referencesTR=[], studyItemRpNumber=None,
                workItemRpNumber=None)


def guarded_writer(writer, target, boundary, error):
    """대상 파일의 실제 atomic writer에서 fsync 또는 교체 오류만 주입합니다."""
    def write(path, *args, **kwargs):
        guard = (patch.object(os, boundary.split("_")[0], side_effect=error)
                 if Path(path) == target and boundary.startswith(("fsync", "replace"))
                 else contextlib.nullcontext())
        with guard:
            return writer(path, *args, **kwargs)
    return write


class TRParserPublication(unittest.TestCase):
    def test_phase5_parsers_accept_uppercase_and_mixed_case_docx_bodies(self):
        for wg in ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5"):
            module = phase5_module(wg, "01_parse_tr_docs.py")
            for suffix in (".docx", ".DOCX", ".DoCx"):
                with self.subTest(wg=wg, suffix=suffix), \
                     tempfile.TemporaryDirectory() as tmp, \
                     patch.object(module, "PROJECT_ROOT", Path(tmp)), \
                     contextlib.redirect_stdout(io.StringIO()):
                    directory = Path(tmp) / "38.999"
                    directory.mkdir()
                    body = directory / f"38999-j00_cl{suffix}"
                    document = module.Document()
                    document.add_paragraph("3GPP TR 38.999 V19.0.0")
                    document.add_paragraph("(Release 19)")
                    document.add_heading("1 Scope", level=1)
                    document.add_paragraph("Synthetic extension selection scope.")
                    document.add_heading("2 References", level=1)
                    document.add_paragraph("Synthetic references.")
                    document.add_heading("6 Conclusions", level=1)
                    document.add_paragraph("Synthetic extension selection conclusion.")
                    document.save(body)
                    original = body.read_bytes()
                    # 새로 교정한 WG에서는 DOCX처럼 이름 붙은 디렉터리를 후보에서 제외합니다.
                    if wg in {"RAN1", "RAN2", "RAN3"}:
                        (directory / "38999-z00_cl.docx").mkdir()
                    for companions in (False, True):
                        with self.subTest(companions=companions):
                            if companions:
                                for name in ("38999-j00_cover.docx", "38999-j00_annex.docx",
                                             "38999-j00_rm.docx"):
                                    (directory / name).write_bytes(original)
                            before = {path.name for path in directory.iterdir()}
                            if wg in {"RAN4", "RAN5"}:
                                result = module.parse_single_tr(directory, directory.name,
                                                                {directory.name})
                            else:
                                result = module.parse_single_tr(directory, {directory.name})
                            self.assertIsNotNone(result)
                            self.assertEqual(result["trNumber"], directory.name)
                            self.assertEqual(result.get("sourceFile", result.get("fileName",
                                                                     result.get("_sourceFile"))),
                                             body.name)
                            self.assertEqual(result["trVersion"], "19.0.0")
                            self.assertEqual(result["targetRelease"], "Rel-19")
                            self.assertIn("Synthetic extension selection scope.", result["scope"])
                            self.assertEqual(body.read_bytes(), original)
                            self.assertEqual({path.name for path in directory.iterdir()}, before)

    def test_tsg_phase5_selection_requires_regular_case_insensitive_docx_bodies(self):
        module = phase5_module("TSG_RAN", "01_parse_tr_docs.py")
        for suffix, directory_present, body_present in (
                (".docx", False, True), (".DOCX", False, True),
                (".DoCx", False, True), (".DOCX", True, True),
                (".docx", True, True), (".docx", True, False)):
            with self.subTest(suffix=suffix, directory_present=directory_present,
                              body_present=body_present), \
                 tempfile.TemporaryDirectory() as tmp, contextlib.ExitStack() as stack:
                root = Path(tmp)
                inputs, output = root / "input", root / "output"
                directory = inputs / "38.999"
                directory.mkdir(parents=True)
                output.mkdir()
                target = output / "tr_documents.json"
                old = '{"설명": "기존 결과"}'.encode()
                target.write_bytes(old)
                target.chmod(0o640)
                body = directory / f"38999-j00_cl{suffix}"
                if body_present:
                    document = module.Document()
                    document.add_paragraph("3GPP TR 38.999 V19.0.0")
                    document.add_paragraph("(Release 19)")
                    document.add_heading("1 Scope", level=1)
                    document.add_paragraph("Synthetic TSG selection scope.")
                    document.add_heading("6 Conclusions", level=1)
                    document.add_paragraph("Synthetic TSG selection conclusion.")
                    document.save(body)
                if directory_present:
                    (directory / "38999-z00_cl.docx").mkdir()
                original = {path.name: path.read_bytes() for path in directory.iterdir()
                            if path.is_file()}
                names = {path.name for path in directory.iterdir()}
                stack.enter_context(patch.multiple(module, PROJECT_ROOT=root,
                                                   TR_INPUT_DIR=inputs, OUTPUT_DIR=output))
                stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                self.assertEqual(module.select_main_docx(directory),
                                 body if body_present else None)
                writer = stack.enter_context(patch.object(module, "write_text_atomic",
                                                         wraps=module.write_text_atomic))
                if body_present:
                    module.main()
                    rows = json.loads(target.read_bytes())["documents"]
                    self.assertEqual(len(rows), 1)
                    self.assertEqual(rows[0]["fileName"], body.name)
                    self.assertEqual(rows[0]["trVersion"], "19.0.0")
                    self.assertEqual(rows[0]["targetRelease"], "Rel-19")
                    self.assertEqual(rows[0]["scope"], "Synthetic TSG selection scope.")
                    writer.assert_called_once()
                else:
                    with self.assertRaises(SystemExit) as error:
                        module.main()
                    self.assertIn("38.999", str(error.exception))
                    writer.assert_not_called()
                    self.assertEqual(target.read_bytes(), old)
                self.assertEqual(target.stat().st_mode & 0o777, 0o640)
                self.assertEqual(list(output.iterdir()), [target])
                self.assertEqual({path.name for path in directory.iterdir()}, names)
                self.assertEqual({path.name: path.read_bytes() for path in directory.iterdir()
                                  if path.is_file()}, original)

    def test_phase5_parsers_require_results_for_every_selected_tr(self):
        for wg in ("RAN3", "TSG_RAN"):
            module = phase5_module(wg, "01_parse_tr_docs.py")
            for present, code, version, cover_release in (
                    ((True, False), "j", "19.0.0", None),
                    ((False, False), "j", "19.0.0", None),
                    ((), "j", "19.0.0", None),
                    ((True, True), "j", "19.0.0", None),
                    ((True, True), "i", "19.0.0", 19),
                    ((True, True), "i", "0.1.0", None)):
                with self.subTest(wg=wg, docx_present=present, filename_release=code,
                                  cover_version=version, cover_release=cover_release), \
                     tempfile.TemporaryDirectory() as tmp, \
                     contextlib.ExitStack() as stack:
                    root = Path(tmp)
                    inputs, output = root / "input", root / "output"
                    inputs.mkdir()
                    output.mkdir()
                    target = output / "tr_documents.json"
                    old = '{"설명": "기존 결과"}'.encode()
                    target.write_bytes(old)
                    target.chmod(0o640)
                    # 두 main의 현재 선택 조건은 38.xxx 폴더입니다.
                    numbers = ("38.998", "38.999")
                    for number, exists in zip(numbers, present):
                        directory = inputs / number
                        directory.mkdir()
                        if exists:
                            document = module.Document()
                            document.add_paragraph(f"3GPP TR {number} V{version}")
                            if cover_release is not None:
                                document.add_paragraph(f"(Release {cover_release})")
                            document.add_heading("1 Scope", level=1)
                            document.add_paragraph("Synthetic parser publication scope.")
                            document.add_heading("6 Conclusions", level=1)
                            document.add_paragraph("Synthetic parser publication conclusion.")
                            document.save(directory / f"{number.replace('.', '')}-{code}00.docx")
                    stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                    stack.enter_context(patch.multiple(module, PROJECT_ROOT=root,
                                                       TR_INPUT_DIR=inputs, OUTPUT_DIR=output))
                    parse = stack.enter_context(patch.object(module, "parse_single_tr",
                                                            wraps=module.parse_single_tr))
                    writer = stack.enter_context(patch.object(module, "write_text_atomic",
                                                             wraps=module.write_text_atomic))
                    if present and all(present):
                        module.main()
                        documents = json.loads(target.read_bytes())["documents"]
                        self.assertEqual([row["trNumber"] for row in documents], list(numbers))
                        expected_release = (cover_release if cover_release is not None
                                            else {"i": 18, "j": 19}[code])
                        self.assertTrue(all(row["trVersion"] == version for row in documents))
                        self.assertTrue(all(row["targetRelease"] == f"Rel-{expected_release}"
                                            for row in documents))
                        writer.assert_called_once()
                    else:
                        with self.assertRaises(SystemExit) as error:
                            module.main()
                        for number, exists in zip(numbers, present):
                            if not exists:
                                self.assertIn(number, str(error.exception))
                        if not present:
                            self.assertIn("0건", str(error.exception))
                        self.assertEqual(target.read_bytes(), old)
                        writer.assert_not_called()
                    self.assertEqual(parse.call_count, len(present))
                    self.assertEqual(target.stat().st_mode & 0o777, 0o640)
                    self.assertEqual(list(output.iterdir()), [target])

    def test_phase5_parser_preserves_each_previous_file_on_write_failure(self):
        # RAN5의 두 파일은 각각 게시됩니다. 이 검사는 파일별 보존 계약을 확인하며
        # 두 파일 또는 별도 study assertion의 일괄 교체를 보증하지 않습니다.
        for wg in ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5"):
            module = phase5_module(wg, "01_parse_tr_docs.py")
            names = (["tr_metadata.json"] if wg == "RAN1" else
                     ["tr_documents.json", "tr_impacts.json"] if wg == "RAN5" else
                     ["tr_documents.json"])
            writer_name = "write_json_atomic" if wg == "RAN1" else "write_text_atomic"
            for name in names:
                for boundary in ("serialize", "fsync_os", "fsync_interrupt",
                                 "replace_os", "replace_interrupt", "success"):
                    with self.subTest(wg=wg, name=name, boundary=boundary), \
                         tempfile.TemporaryDirectory() as tmp, contextlib.ExitStack() as stack:
                        root = Path(tmp)
                        inputs, output = root / "input", root / "output"
                        (inputs / "38.999").mkdir(parents=True)
                        output.mkdir()
                        old = '{"설명": "기존 결과"}'.encode()
                        for filename in names:
                            (output / filename).write_bytes(old)
                            (output / filename).chmod(0o640)
                        target = output / name
                        row = report_row()
                        impacts = [dict(trNumber="38.999", impactType="NoChange")]
                        if boundary == "serialize":
                            (impacts[0] if name == "tr_impacts.json" else row)["bad"] = object()
                        stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                        stack.enter_context(patch.multiple(module, PROJECT_ROOT=root,
                                                           TR_INPUT_DIR=inputs, OUTPUT_DIR=output))
                        parse = stack.enter_context(patch.object(module, "parse_single_tr", return_value=row))
                        if wg == "RAN5":
                            stack.enter_context(patch.object(module, "load_impact_mapping", return_value=impacts))
                            stack.enter_context(patch.object(module, "write_study_assertions_document"))
                        error = (KeyboardInterrupt("synthetic") if boundary.endswith("interrupt")
                                 else OSError("synthetic"))
                        writer = guarded_writer(getattr(module, writer_name), target, boundary, error)
                        stack.enter_context(patch.object(module, writer_name, side_effect=writer))
                        if boundary == "success":
                            module.main()
                            self.assertIn("새 결과" if name != "tr_impacts.json" else "NoChange",
                                          target.read_text(encoding="utf-8"))
                            json.loads(target.read_bytes())
                        else:
                            with self.assertRaises(TypeError if boundary == "serialize" else type(error)) as got:
                                module.main()
                            if boundary != "serialize":
                                self.assertIs(got.exception, error)
                            self.assertEqual(target.read_bytes(), old)
                        parse.assert_called_once()
                        self.assertEqual(target.stat().st_mode & 0o777, 0o640)
                        self.assertEqual({path.name for path in output.iterdir()}, set(names))

    def test_phase5_ran2_jsonld_preserves_previous_file_on_write_failure(self):
        module = phase5_module("RAN2", "02_generate_tr_jsonld.py")
        for boundary in ("serialize", "fsync_os", "fsync_interrupt",
                         "replace_os", "replace_interrupt", "success"):
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as tmp, \
                 contextlib.ExitStack() as stack:
                output = Path(tmp)
                target = output / "tr_ontology.jsonld"
                old = '{"설명": "기존 결과"}'.encode()
                target.write_bytes(old)
                target.chmod(0o640)
                row = report_row()
                if boundary == "serialize":
                    row["trTitle"] = object()
                stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                stack.enter_context(patch.multiple(module, PROJECT_ROOT=output, OUTPUT_DIR=output))
                stack.enter_context(patch.object(module, "load_tr_documents", return_value=[row]))
                stack.enter_context(patch.object(module, "load_csv_mapping", return_value=[]))
                stack.enter_context(patch.object(module, "assess_impacts"))
                stack.enter_context(patch.object(module, "write_study_assertions_document"))
                error = (KeyboardInterrupt("synthetic") if boundary.endswith("interrupt")
                         else OSError("synthetic"))
                writer = guarded_writer(module.write_text_atomic, target, boundary, error)
                stack.enter_context(patch.object(module, "write_text_atomic", side_effect=writer))
                if boundary == "success":
                    module.main()
                    self.assertIn("새 결과", target.read_text(encoding="utf-8"))
                    json.loads(target.read_bytes())
                else:
                    expected = (TypeError, ValueError) if boundary == "serialize" else type(error)
                    with self.assertRaises(expected) as got:
                        module.main()
                    if boundary != "serialize":
                        self.assertIs(got.exception, error)
                    self.assertEqual(target.read_bytes(), old)
                self.assertEqual(target.stat().st_mode & 0o777, 0o640)
                self.assertEqual(list(output.iterdir()), [target])

    def test_previous_results_survive_publication_failures(self):
        for wg in ("RAN2", "TSG_RAN"):
            source = ROOT / "scripts/tsg/RAN/formal" / wg / "phase-9/tr-parser/01_parse_tr_chunks.py"
            for kind in ("chunks", "summary"):
                for boundary in ("serialize", "fsync_os", "fsync_interrupt",
                                 "replace_os", "replace_interrupt", "success"):
                    with self.subTest(wg=wg, kind=kind, boundary=boundary), tempfile.TemporaryDirectory() as tmp:
                        output = Path(tmp)
                        target = (output / "99.999/chunks.json" if kind == "chunks"
                                  else output / "parse_summary.json")
                        target.parent.mkdir(parents=True, exist_ok=True)
                        old = '{"설명": "기존 결과"}'.encode()
                        target.write_bytes(old)
                        target.chmod(0o640)
                        invoke = publication(source, output, kind, boundary == "serialize")
                        error = (KeyboardInterrupt("synthetic") if boundary.endswith("interrupt")
                                 else OSError("synthetic"))
                        guard = (patch.object(os, boundary.split("_")[0], side_effect=error)
                                 if boundary.startswith(("fsync", "replace")) else contextlib.nullcontext())
                        with guard:
                            if boundary == "success":
                                invoke()
                            else:
                                with self.assertRaises(TypeError if boundary == "serialize" else type(error)) as got:
                                    invoke()
                                if boundary != "serialize":
                                    self.assertIs(got.exception, error)
                        self.assertEqual(target.stat().st_mode & 0o777, 0o640)
                        if boundary == "success":
                            data = json.loads(target.read_bytes())
                            self.assertEqual(target.read_bytes(), json.dumps(data, ensure_ascii=False, indent=2).encode())
                            self.assertIn("새 결과", target.read_text(encoding="utf-8"))
                        else:
                            self.assertEqual(target.read_bytes(), old)
                        self.assertEqual([p for p in output.rglob("*") if p.is_file()], [target])


if __name__ == "__main__":
    unittest.main()
