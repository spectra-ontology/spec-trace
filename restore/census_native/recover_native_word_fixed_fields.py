#!/usr/bin/env python3
"""Preserve accepted native field displays through a separate scratch adapter.

Imports an explicit original native converter, keeps its strict export/reopen
text predicate and source-identity checks, and transforms only its newly
exported scratch DOCX. Field metadata and the pre-transform package are retained
locally. Requires system Python's PyUNO and lxml. No source file is saved.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import traceback
import zipfile

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
Q = lambda local: "{" + W + "}" + local


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1 << 20):
            h.update(block)
    return h.hexdigest()


def transform_fields(path, metadata_dir, policy):
    from lxml import etree as ET
    before = metadata_dir / "pretransform_export.docx"
    shutil.copyfile(path, before)
    parts, fields, changed = {}, [], []
    with zipfile.ZipFile(path) as source:
        entries = source.infolist()
        for entry in entries:
            data = source.read(entry.filename)
            if not entry.filename.startswith("word/") or not entry.filename.endswith(".xml"):
                parts[entry.filename] = data
                continue
            root = ET.fromstring(data)
            nodes = list(root.iter())
            begins = [v for v in nodes if v.tag == Q("fldChar") and v.get(Q("fldCharType")) == "begin"]
            simples = [v for v in nodes if v.tag == Q("fldSimple")]
            if not begins and not simples:
                parts[entry.filename] = data
                continue
            stack = []
            remove = []
            for node in nodes:
                if node.tag == Q("fldChar"):
                    kind = node.get(Q("fldCharType"))
                    if kind == "begin":
                        row = {"part": entry.filename, "index": len(fields), "kind": "complex",
                               "begin_xml": ET.tostring(node, encoding="unicode"),
                               "instruction": "", "cached_text": "", "separated": False}
                        fields.append(row)
                        stack.append(row)
                        if policy == "lock":
                            node.set(Q("fldLock"), "true")
                    elif kind == "separate":
                        if not stack or stack[-1]["separated"]:
                            raise ValueError("Unsupported unbalanced/repeated field separator")
                        stack[-1]["separated"] = True
                    elif kind == "end":
                        if not stack or not stack[-1]["separated"]:
                            raise ValueError("Unsupported unbalanced/uncached complex field")
                        stack.pop()
                    else:
                        raise ValueError("Unsupported field character type")
                    if policy == "literal":
                        remove.append(node)
                elif node.tag == Q("instrText"):
                    if not stack:
                        raise ValueError("Instruction text outside a balanced complex field")
                    stack[-1]["instruction"] += node.text or ""
                    if policy == "literal":
                        remove.append(node)
                elif node.tag in (Q("t"), Q("tab"), Q("br")):
                    for row in stack:
                        if row["separated"]:
                            row["cached_text"] += node.text or ("\t" if node.tag == Q("tab") else "\n" if node.tag == Q("br") else "")
                    if policy == "literal" and any(not row["separated"] for row in stack):
                        remove.append(node)
            if stack:
                raise ValueError("Unclosed complex field")
            for node in simples:
                fields.append({"part": entry.filename, "index": len(fields), "kind": "simple",
                               "xml": ET.tostring(node, encoding="unicode"),
                               "instruction": node.get(Q("instr")),
                               "cached_text": "".join(node.itertext())})
                if policy == "lock":
                    node.set(Q("fldLock"), "true")
                else:
                    parent = node.getparent()
                    position = parent.index(node)
                    for child in list(node):
                        parent.insert(position, child)
                        position += 1
                    parent.remove(node)
            for node in remove:
                if node.getparent() is not None:
                    node.getparent().remove(node)
            changed.append(entry.filename)
            parts[entry.filename] = ET.tostring(root, encoding="UTF-8", xml_declaration=True, standalone=True)
    temporary = metadata_dir / "transformed.docx"
    with zipfile.ZipFile(temporary, "x") as target:
        for entry in entries:
            target.writestr(entry, parts[entry.filename])
    shutil.copyfile(temporary, path)
    temporary.unlink()
    result = {"policy": policy, "fields": fields, "field_count": len(fields),
              "changed_parts": changed, "pretransform_sha256": sha(before),
              "transformed_sha256": sha(path),
              "metadata_scope": "Original field instructions, cached display text and field XML; complete original exported package retained separately."}
    (metadata_dir / "fields.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--native-module", type=Path, required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--metadata-dir", type=Path, required=True)
    p.add_argument("--policy", choices=("lock", "literal"), required=True)
    p.add_argument("--soffice", default="soffice")
    args = p.parse_args()
    if args.metadata_dir.exists() and any(args.metadata_dir.iterdir()):
        p.error("--metadata-dir must be new or empty")
    if args.output.exists() or args.receipt.exists():
        p.error("--output and --receipt must be new")
    args.metadata_dir.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(args.native_module.resolve().parent))
    spec = importlib.util.spec_from_file_location("original_native_field_adapter", args.native_module)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original_validate = module.validate_docx
    original_compare = module.require_same_rendered_text
    observed = {}

    def validate_export(path):
        original_validate(path)
        observed["field_transformation"] = transform_fields(path, args.metadata_dir, args.policy)
        original_validate(path)

    def compare_rendered(before, after):
        (args.metadata_dir / "accepted_native.txt").write_text(before)
        (args.metadata_dir / "reopened_docx.txt").write_text(after)
        return original_compare(before, after)

    module.validate_docx = validate_export
    module.require_same_rendered_text = compare_rendered
    before_sha = sha(args.source)
    result = {"adapter": "accepted_field_display_preservation", "policy": args.policy,
              "original_native_module_sha256": sha(args.native_module),
              "adapter_sha256": sha(Path(__file__)), "source_sha256": before_sha,
              "original_strict_predicate_retained": True}
    try:
        result["original_converter_result"] = module.recover_native_word(
            args.source, args.output, soffice=args.soffice)
        result["passed"] = True
    except Exception as error:
        result["passed"] = False
        result["error"] = type(error).__name__ + ": " + str(error)
        (args.metadata_dir / "failure.txt").write_text(traceback.format_exc())
    result["source_hash_unchanged"] = sha(args.source) == before_sha
    result["observed"] = observed
    args.receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"], "source_unchanged": result["source_hash_unchanged"],
                      "fields": observed.get("field_transformation", {}).get("field_count")}))
    if not result["passed"] or not result["source_hash_unchanged"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
