#!/usr/bin/env python3
"""Run the original census over local inputs with explicit reconstructed forms.

The input tree and original auditor files remain unchanged. A read-path adapter
substitutes only explicitly named clause-form bytes, retaining each requested
logical corpus path and the new file's actual SHA-1. All original parsing,
deduplication, judgment, denominator and comparison routines execute normally.
This is a local corpus with selected replacements, not a fresh corpus rebuild.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

_FORM_READER = None
_REPLACEMENTS = {}
_EVENT_LOG = None


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replaced_form_reader(path_text):
    path = Path(path_text)
    candidates = _REPLACEMENTS.get(path.name, ())
    for original, replacement in candidates:
        if path.resolve() == original:
            result = _FORM_READER(str(replacement))
            result["path"] = path_text
            record = {"requested_path": path_text, "replacement_sha256": sha(replacement),
                      "replacement_actual_sha1": result.get("sha1"), "status": result.get("status")}
            descriptor = os.open(_EVENT_LOG, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            try:
                os.write(descriptor, (json.dumps(record) + "\n").encode())
            finally:
                os.close(descriptor)
            return result
    return _FORM_READER(path_text)


def main():
    global _FORM_READER, _REPLACEMENTS, _EVENT_LOG
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runner-module", type=Path, required=True)
    p.add_argument("--stage", type=Path, required=True)
    p.add_argument("--artifact", type=Path, required=True)
    p.add_argument("--reference", type=Path, required=True)
    p.add_argument("--replacement", action="append", required=True, metavar="ORIGINAL=RECONSTRUCTED")
    p.add_argument("--audit", action="append", choices=("pack", "clause"))
    p.add_argument("--workers", type=int, default=1)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        p.error("--out must be new or empty")
    args.out.mkdir(parents=True, exist_ok=True)
    args.out = args.out.resolve()
    replacements = []
    for entry in args.replacement:
        original, replacement = map(lambda v: Path(v).resolve(strict=True), entry.split("=", 1))
        if original.name != replacement.name:
            p.error("Reconstructed form must retain the original basename")
        _REPLACEMENTS.setdefault(original.name, []).append((original, replacement))
        replacements.append({"original": str(original), "original_sha256": sha(original),
                             "replacement": str(replacement), "replacement_sha256": sha(replacement)})
    _EVENT_LOG = str(args.out / "replacement_reads.jsonl")
    sys.path.insert(0, str(args.runner_module.resolve().parent))
    spec = importlib.util.spec_from_file_location("original_census_replacement_runner", args.runner_module)
    runner = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = runner
    spec.loader.exec_module(runner)
    original_load = runner.load

    def adapted_load(path, name):
        global _FORM_READER
        module = original_load(path, name)
        if name == "census_original_clause_audit":
            _FORM_READER = module.read_form
            module.read_form = replaced_form_reader
        return module

    runner.load = adapted_load
    args.audits = args.audit or ["pack", "clause"]
    args.wg = tuple(f"RAN{i}" for i in range(1, 6))
    args.source_mode = "local_original_read_only_inputs_with_explicit_reconstructed_form_replacements"
    condition = {"source_mode": args.source_mode, "whole_corpus_freshly_rebuilt": False,
                 "replacement_condition": replacements, "runner_sha256": sha(args.runner_module),
                 "wrapper_sha256": sha(Path(__file__)), "audits": args.audits,
                 "original_auditor_source_unchanged": True,
                 "read_adapter": "Only explicit reconstructed clause-form bytes replace selected reads. Original path retained, actual reconstructed SHA-1 retained; original deduplication and all judges unchanged."}
    (args.out / "replacement_condition.json").write_text(json.dumps(condition, indent=2) + "\n")
    try:
        runner.audit(args)
    finally:
        condition["original_and_replacement_hashes_unchanged"] = all(
            sha(Path(row["original"])) == row["original_sha256"] and
            sha(Path(row["replacement"])) == row["replacement_sha256"] for row in replacements)
        condition["replacement_read_events"] = sum(1 for _ in Path(_EVENT_LOG).open()) if Path(_EVENT_LOG).exists() else 0
        (args.out / "replacement_condition.json").write_text(json.dumps(condition, indent=2) + "\n")


if __name__ == "__main__":
    main()
