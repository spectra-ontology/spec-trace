#!/usr/bin/env python3
"""Rerun the original native pilot with a fixed field policy and its readers.

Writes a new local diagnostic tree. All source documents, original pilot
receipts and original audit modules remain read-only. Each converter owns a
separate LibreOffice profile. Source-derived packages/text stay in this tree.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, path):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def canonical(v):
    if isinstance(v, dict):
        return {k: canonical(x) for k, x in sorted(v.items())}
    if isinstance(v, (list, tuple)):
        return [canonical(x) for x in v]
    if isinstance(v, set):
        return sorted(canonical(x) for x in v)
    return v


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pilot-receipt", type=Path, required=True)
    p.add_argument("--source-root", type=Path, required=True)
    p.add_argument("--adapter", type=Path, required=True)
    p.add_argument("--native-module", type=Path, required=True)
    p.add_argument("--clause-module", type=Path, required=True)
    p.add_argument("--pack-module", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--workers", type=int, choices=(1, 2), default=2)
    args = p.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        p.error("--out must be new or empty")
    args.out.mkdir(parents=True, exist_ok=True)
    args.out = args.out.resolve()
    for key in ("adapter", "native_module", "source_root", "clause_module", "pack_module"):
        setattr(args, key, getattr(args, key).resolve())
    old = json.loads(args.pilot_receipt.read_text())
    todo = []
    for row in old["records"]:
        for conversion in row.get("conversion", []):
            match = next(v for v in row["files"] if v["path"] == conversion["input"])
            todo.append({"source": args.source_root / match["originalPath"],
                         "pack": Path(row["archivePath"]).stem,
                         "original_conversion_success": conversion["success"]})
    clause = load("fixed_field_batch_clause", args.clause_module)
    pack = load("fixed_field_batch_pack", args.pack_module)

    def run(row):
        source = row["source"]
        directory = args.out / source.stem
        output = directory / "candidate" / source.with_suffix(".docx").name
        receipt = directory / "receipt.json"
        command = ["/usr/bin/python3", "-B", str(args.adapter), "--native-module", str(args.native_module),
                   "--source", str(source), "--output", str(output), "--receipt", str(receipt),
                   "--metadata-dir", str(directory / "field_metadata"), "--policy", "literal"]
        source_sha = sha(source)
        started = time.monotonic()
        result = subprocess.run(command, capture_output=True, text=True, timeout=600)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "execution.stdout").write_text(result.stdout)
        (directory / "execution.stderr").write_text(result.stderr)
        record = {"source": str(source.relative_to(args.source_root)), "source_sha256": source_sha,
                  "source_unchanged": sha(source) == source_sha, "candidate": str(output.relative_to(args.out)),
                  "original_conversion_success": row["original_conversion_success"],
                  "exit_code": result.returncode, "seconds": time.monotonic() - started}
        if receipt.exists():
            proof = json.loads(receipt.read_text())
            record["strict_export_reopen_passed"] = proof.get("passed", False)
            record["receipt_sha256"] = sha(receipt)
            record["accepted_rendered_text"] = proof.get("original_converter_result", {}).get("acceptedRenderedText")
        if output.exists():
            expected = source.with_suffix(".docx")
            actual_clause, expected_clause = clause.read_form(str(output)), clause.read_form(str(expected))
            for value in (actual_clause, expected_clause):
                value.pop("path", None)
                value.pop("sha1", None)
            actual_pack, expected_pack = canonical(pack.read_cover(output)), canonical(pack.read_cover(expected))
            record.update(candidate_sha256=sha(output), original_docx_sha256=sha(expected),
                          clause_input=bool(clause.TDOC.search(output.name)),
                          clause_reader_equal=actual_clause == expected_clause,
                          clause_actual=canonical(actual_clause), clause_expected=canonical(expected_clause),
                          pack_cover_input=bool(re.fullmatch(pack.COVER_NAME.format(pack=re.escape(row["pack"])), output.name, re.I)),
                          pack_reader_equal=actual_pack == expected_pack, pack_actual=actual_pack, pack_expected=expected_pack)
        (directory / "reader_comparison.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"source": source.name, "strict_pass": record.get("strict_export_reopen_passed"),
                          "clause_equal": record.get("clause_reader_equal"),
                          "cover_equal": record.get("pack_reader_equal")}), flush=True)
        return record

    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(run, todo))
    passed = all(r.get("strict_export_reopen_passed") and r["source_unchanged"] and
                 (not r.get("clause_input") or r.get("clause_reader_equal")) and
                 (not r.get("pack_cover_input") or r.get("pack_reader_equal")) for r in results)
    report = {"passed": passed, "policy": "literal accepted field displays, preserve original field metadata/export sidecar",
              "source_mode": "Seven read-only original native pilot inputs with newly reconstructed DOCX outputs",
              "whole_corpus_freshly_rebuilt": False, "seconds": time.monotonic() - started,
              "native_pilot_inputs": len(results), "strict_passes": sum(bool(r.get("strict_export_reopen_passed")) for r in results),
              "applicable_clause_inputs": sum(r.get("clause_input", False) for r in results),
              "applicable_clause_reader_matches": sum(r.get("clause_input", False) and r.get("clause_reader_equal", False) for r in results),
              "applicable_pack_cover_inputs": sum(r.get("pack_cover_input", False) for r in results),
              "applicable_pack_cover_reader_matches": sum(r.get("pack_cover_input", False) and r.get("pack_reader_equal", False) for r in results),
              "input_receipt_sha256": sha(args.pilot_receipt), "adapter_sha256": sha(args.adapter),
              "native_module_sha256": sha(args.native_module), "records": results}
    (args.out / "receipt.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "records"}))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
