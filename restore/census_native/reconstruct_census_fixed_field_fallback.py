#!/usr/bin/env python3
"""Explicit field-display fallback around the original census constructor.

The original extraction/conversion executes first. Only the original accepted
native text/reopen failure selects the separate fixed-field adapter. The
adapter retains the original strict predicate, source checks and XML checks.
All full source-derived evidence stays in an explicit local scratch directory.
Original constructor and native converter files remain unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1 << 20):
            h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runner-module", type=Path, required=True)
    p.add_argument("--fixed-field-adapter", type=Path, required=True)
    p.add_argument("--native-module", type=Path, required=True)
    p.add_argument("--fallback-evidence", type=Path, required=True)
    p.add_argument("--fallback-receipt", type=Path, required=True)
    args, forwarded = p.parse_known_args()
    if forwarded[:1] == ["--"]:
        forwarded = forwarded[1:]
    if args.fallback_evidence.exists() and any(args.fallback_evidence.iterdir()):
        p.error("--fallback-evidence must be new or empty")
    if args.fallback_receipt.exists():
        p.error("--fallback-receipt must be new")
    args.fallback_evidence.mkdir(parents=True, exist_ok=True)
    args.fallback_evidence = args.fallback_evidence.resolve()
    for key in ("runner_module", "fixed_field_adapter", "native_module"):
        setattr(args, key, getattr(args, key).resolve(strict=True))
    args.fallback_receipt = args.fallback_receipt.absolute()
    args.fallback_receipt.parent.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location("original_census_field_fallback", args.runner_module)
    runner = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = runner
    sys.path.insert(0, str(args.runner_module.parent))
    spec.loader.exec_module(runner)
    original_load = runner.load
    events = []
    proof = {"policy": "Original conversion first; explicit literal-field adapter only after original accepted-text/reopen failure",
             "original_source_modules_unchanged": True, "original_strict_predicate_retained": True,
             "runner_sha256": sha(args.runner_module), "native_module_sha256": sha(args.native_module),
             "adapter_sha256": sha(args.fixed_field_adapter), "wrapper_sha256": sha(Path(__file__)),
             "events": events}

    def adapted_load(path, name):
        module = original_load(path, name)
        if name != "census_native_word_converter":
            return module
        original_process = module.process_file

        def process(file_info):
            result = original_process(file_info)
            if result.get("success") or "Accepted native text changed on DOCX reopen" not in result.get("error", ""):
                return result
            source, output, kind = file_info
            source, output = Path(source).resolve(), Path(output).absolute()
            if kind != "doc" or output.exists() or output.is_symlink() or source == output:
                return result
            identifier = hashlib.sha256(str(source).encode()).hexdigest()[:20]
            directory = args.fallback_evidence / identifier
            directory.mkdir()
            receipt = directory / "receipt.json"
            source_sha = sha(source)
            command = ["/usr/bin/python3", "-B", str(args.fixed_field_adapter), "--native-module", str(args.native_module),
                       "--source", str(source), "--output", str(output), "--receipt", str(receipt),
                       "--metadata-dir", str(directory / "field_metadata"), "--policy", "literal"]
            started = time.monotonic()
            run = subprocess.run(command, capture_output=True, text=True, timeout=600)
            (directory / "execution.stdout").write_text(run.stdout)
            (directory / "execution.stderr").write_text(run.stderr)
            event = {"source": str(source), "source_sha256": source_sha, "original_failure": result,
                     "adapter_exit_code": run.returncode, "seconds": time.monotonic() - started,
                     "source_unchanged": sha(source) == source_sha, "receipt": str(receipt)}
            events.append(event)
            args.fallback_receipt.write_text(json.dumps(proof, indent=2) + "\n")
            if run.returncode or not receipt.is_file():
                return {**result, "fieldFallback": {"passed": False, "receipt": str(receipt)}}
            actual = json.loads(receipt.read_text())
            original = actual.get("original_converter_result", {})
            if not (actual.get("passed") is True and actual.get("source_hash_unchanged") is True
                    and original.get("sourceSha256") == source_sha and sha(source) == source_sha
                    and original.get("strictXml") is True and original.get("redlinesAfter") == 0
                    and original.get("acceptedRenderedText", {}).get("equal") is True
                    and output.is_file() and sha(output) == original.get("outputSha256")):
                raise ValueError("Fixed-field fallback proof does not match its source/output")
            # Retain the original constructor's validated-output sidecar handoff.
            Path(str(output) + ".conversion.json").write_text(json.dumps(actual, indent=2) + "\n")
            event["passed"] = True
            event["output_sha256"] = sha(output)
            event["strict_normalized_chars"] = original["acceptedRenderedText"]["normalizedCharacters"]
            args.fallback_receipt.write_text(json.dumps(proof, indent=2) + "\n")
            return {"success": True, "file": str(source), "method": "explicit_accepted_field_display_fallback",
                    "originalFailurePreserved": True, "fieldFallbackReceiptSha256": sha(receipt)}

        module.process_file = process
        return module

    runner.load = adapted_load
    previous = sys.argv
    try:
        sys.argv = [str(args.runner_module), "reconstruct", *forwarded]
        runner.main()
    finally:
        sys.argv = previous
        args.fallback_receipt.write_text(json.dumps(proof, indent=2) + "\n")


if __name__ == "__main__":
    main()
