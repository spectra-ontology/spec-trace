#!/usr/bin/env python3
"""Check actual read-only DOCX reopen text against a captured native baseline.

Uses the original strict predicate and an isolated, owned LibreOffice process.
Each candidate has an explicit expected pass/fail outcome for negative controls.
Inputs remain unchanged; output receipts contain hashes, counts and gate results.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    import uno
    from com.sun.star.beans import PropertyValue

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--native-module", type=Path, required=True)
    p.add_argument("--baseline-text", type=Path, required=True)
    p.add_argument("--candidate", action="append", required=True, metavar="pass|fail=DOCX")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--soffice", default="soffice")
    args = p.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        p.error("--out must be new or empty")
    args.out.mkdir(parents=True, exist_ok=True)
    args.out = args.out.resolve()
    sys.path.insert(0, str(args.native_module.resolve().parent))
    spec = importlib.util.spec_from_file_location("strict_native_reopen_verifier", args.native_module)
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    baseline = args.baseline_text.read_text()
    todo = []
    for entry in args.candidate:
        expected, path = entry.split("=", 1)
        if expected not in ("pass", "fail"):
            p.error("Candidate outcome must be pass or fail")
        path = Path(path).resolve(strict=True)
        native.validate_docx(path)
        todo.append((expected == "pass", path, sha(path)))

    def props(**values):
        result = []
        for name, value in values.items():
            item = PropertyValue()
            item.Name, item.Value = name, value
            result.append(item)
        return tuple(result)

    records = []
    with tempfile.TemporaryDirectory(prefix=".strict-reopen-", dir=args.out) as directory:
        pipe = "spectra_reopen_" + uuid.uuid4().hex
        process = subprocess.Popen([args.soffice, "--headless", "-env:UserInstallation=" + (Path(directory) / "profile").as_uri(),
            "--accept=pipe,name=" + pipe + ";urp;StarOffice.ComponentContext", "--norestore", "--nodefault", "--nofirststartwizard"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        desktop = None
        document = None
        try:
            local = uno.getComponentContext()
            resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
            for _ in range(100):
                try:
                    context = resolver.resolve("uno:pipe,name=" + pipe + ";urp;StarOffice.ComponentContext")
                    break
                except Exception:
                    if process.poll() is not None:
                        raise RuntimeError("Isolated LibreOffice exited during startup")
                    time.sleep(0.1)
            else:
                raise TimeoutError("Isolated LibreOffice startup timed out")
            desktop = context.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", context)
            properties = props(Hidden=True, ReadOnly=True,
                UpdateDocMode=uno.getConstantByName("com.sun.star.document.UpdateDocMode.NO_UPDATE"),
                MacroExecutionMode=uno.getConstantByName("com.sun.star.document.MacroExecMode.NEVER_EXECUTE"))
            for expected, path, digest in todo:
                document = desktop.loadComponentFromURL(path.as_uri(), "_blank", 0, properties)
                if document is None or document.Redlines.Count:
                    raise ValueError("DOCX must reopen with zero unresolved redlines")
                actual = document.Text.String
                row = {"candidate": path.name, "candidate_sha256": digest,
                       "expected_original_predicate_pass": expected,
                       "reopened_characters": len(actual),
                       "reopened_normalized_characters": len(native.normalized_rendered_text(actual)),
                       "reopened_normalized_sha256": hashlib.sha256(native.normalized_rendered_text(actual).encode()).hexdigest()}
                try:
                    row["original_comparison"] = native.require_same_rendered_text(baseline, actual)
                    row["original_predicate_pass"] = True
                except ValueError as error:
                    row["original_predicate_pass"] = False
                    row["error"] = str(error)
                row["expected_outcome_observed"] = row["original_predicate_pass"] == expected
                records.append(row)
                document.close(True)
                document = None
        finally:
            if document is not None:
                document.close(True)
            if desktop is not None:
                desktop.terminate()
            native._stop(process)
    report = {"passed": all(r["expected_outcome_observed"] for r in records), "records": records,
              "baseline_text_sha256": sha(args.baseline_text), "native_module_sha256": sha(args.native_module),
              "verifier_sha256": sha(Path(__file__)), "candidate_hashes_unchanged": all(sha(path) == digest for _, path, digest in todo),
              "original_predicate_unchanged": True, "source_passages_written": False}
    (args.out / "receipt.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "cases": len(records), "candidate_hashes_unchanged": report["candidate_hashes_unchanged"]}))
    if not report["passed"] or not report["candidate_hashes_unchanged"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
