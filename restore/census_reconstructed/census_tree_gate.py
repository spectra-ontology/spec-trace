#!/usr/bin/env python3
"""Verify reconstructed census inputs and run the unchanged original auditors.

Expected fixtures contain paths, byte identities and reader-output digests only.
Conversion receipts bind a fresh output to an exact native input and the pinned
constructor. Scientific equivalence excludes only the reader's path and SHA1;
the full auditor always receives the actual reconstructed SHA1 for deduplication.
"""
from __future__ import annotations

import argparse
import collections
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time

SCHEMA = "census-scientific-tree-gate"
PIN_FILES = ("restore_census_artifact.py", "export_census_artifact.py",
             "audit_clause_links.py", "audit_pack_links.py")
_AUDIT_FORM_READER = None
_AUDIT_REPLACEMENTS = {}
_AUDIT_EVENTS = None
_AUDIT_ROOT = None


def digest(path, algorithm="sha256"):
    h = hashlib.new(algorithm)
    with Path(path).open("rb") as stream:
        while block := stream.read(1 << 20):
            h.update(block)
    return h.hexdigest()


def canonical(value):
    if isinstance(value, dict):
        return {str(k): canonical(v) for k, v in sorted(value.items())}
    if isinstance(value, (set, frozenset)):
        return sorted((canonical(v) for v in value), key=lambda v: json.dumps(v, sort_keys=True))
    if isinstance(value, (list, tuple)):
        return [canonical(v) for v in value]
    return value


def logical_digest(value):
    return hashlib.sha256(json.dumps(canonical(value), ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def safe(root, relative):
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Expected a safe relative corpus path")
    return Path(root) / path


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def modules(code, native):
    code = Path(code).resolve()
    sys.path.insert(0, str(code))
    pins = {name: digest(code / name) for name in PIN_FILES}
    pins["native_word_conversion.py"] = digest(native)
    return pins, load(code / "audit_clause_links.py", "gate_clause"), \
        load(code / "audit_pack_links.py", "gate_pack"), load(native, "gate_native")


def reader_digests(path, clause, pack, wanted):
    result = {}
    if "clause" in wanted:
        value = clause.read_form(str(path))
        # Comparison only: do not inject a historical hash into the auditor.
        result["clause"] = logical_digest({k: v for k, v in value.items() if k not in ("path", "sha1")})
    if "pack" in wanted:
        result["pack"] = logical_digest(pack.read_cover(path))
    return result


def constructor_rows(constructor):
    files, events = {}, {}
    for record in constructor["records"]:
        base = str(Path(record["archivePath"]).parent).replace("/source/", "/derived/") + "/" + Path(record["archivePath"]).stem
        for row in record["files"]:
            files[base + "/" + row["path"]] = row
        for event in record["conversion"]:
            events[base + "/" + event["output"]] = {**event, "nativePath": base + "/" + event["input"]}
    return files, events


def make_fixture(args):
    pins, clause, pack, _ = modules(args.code, args.native_module)
    constructor = read(args.constructor)
    frontier_receipt = read(args.frontier_receipt)
    if digest(args.frontier) != frontier_receipt["frontierSha256"]:
        raise ValueError("Released derived frontier hash differs")
    selected, events = constructor_rows(constructor)
    roots = sorted({str(Path(path).parent) for path in selected})
    frontier = []
    with gzip.open(args.frontier, "rt") as stream:
        for line in stream:
            row = json.loads(line)
            if any(row["path"] == root or row["path"].startswith(root + "/") for root in roots):
                frontier.append(row)
    files = []
    for row in frontier:
        if row.get("kind") != "file":
            continue
        relative = row["path"]
        if relative not in selected:
            raise ValueError("Constructor path coverage differs from selected historical frontier")
        original = safe(args.original_root, relative)
        if digest(original) != row["sha256"] or original.stat().st_size != row["bytes"]:
            raise ValueError("Original source differs from released frontier: " + relative)
        converted = not selected[relative]["nativeExtracted"]
        wanted = ["clause"] if original.suffix.lower() in (".doc", ".docx") else []
        if re.fullmatch(pack.COVER_NAME.format(pack=re.escape(original.parent.name)), original.name, re.I):
            wanted.append("pack")
        required = []
        if converted and selected[relative].get("clauseFormNameInput"):
            required.append("clause")
        if converted and "pack" in wanted:
            required.append("pack")
        files.append({"path": relative, "bytes": row["bytes"], "sha256": row["sha256"],
                      "sha1": row["sha1"], "converted": converted,
                      "nativePath": events[relative]["nativePath"] if converted else None,
                      "readerDigests": reader_digests(original, clause, pack, wanted),
                      "requiredFullAuditReaders": required})
    if set(selected) != {r["path"] for r in files}:
        raise ValueError("Selected constructor files differ from original frontier")
    archives = [{"path": r["archivePath"], "sha256": r["archiveSha256"]}
                for r in constructor["records"]]
    for archive in archives:
        path = safe(args.original_root, archive["path"])
        if digest(path) != archive["sha256"]:
            raise ValueError("Original archive differs")
        archive["bytes"] = path.stat().st_size
    result = {"schema": SCHEMA, "scope": "selected_archive_frontier",
              "wholeCorpusExpected": False, "sourceTextIncluded": False,
              "publicCommit": args.public_commit, "pins": pins,
              "constructorPins": {k: constructor[k] for k in ("inventorySha256", "extractorSha256", "converterSha256", "metadataExporterSha256")},
              "frontierSha256": digest(args.frontier), "frontierReceiptSha256": digest(args.frontier_receipt),
              "scopeRoots": roots, "directories": sorted({r["path"] for r in frontier if r.get("kind") == "directory"} | set(roots)),
              "archives": archives, "files": files,
              "comparison": "Pinned reader output, excluding only path and sha1; actual SHA1 retained in full audits"}
    write(args.out, result)
    return {"files": len(files), "converted": sum(r["converted"] for r in files), "fixtureSha256": digest(args.out)}


def make_conversion_proof(args):
    fixture, constructor = read(args.fixture), read(args.constructor)
    pins, _, _, native = modules(args.code, args.native_module)
    if pins != fixture["pins"]:
        raise ValueError("Pinned code differs")
    if any(constructor.get(k) != v for k, v in fixture["constructorPins"].items()):
        raise ValueError("Constructor source pins differ")
    all_files, events = constructor_rows(constructor)
    conversions = []
    for row in fixture["files"]:
        if not row["converted"]:
            continue
        path, source = safe(args.root, row["path"]), safe(args.root, row["nativePath"])
        file_record, event = all_files[row["path"]], events[row["path"]]
        if event.get("success") is not True or file_record.get("nativeExtracted") is not False:
            raise ValueError("Missing successful explicit conversion")
        if digest(path) != file_record["sha256"]:
            raise ValueError("Output differs from constructor record")
        native.validate_docx(path)  # ZIP CRC and every XML/rels part, unchanged predicate.
        proof = {"path": row["path"], "nativePath": row["nativePath"],
                 "sourceSha256": digest(source), "outputSha256": digest(path),
                 "outputSha1": digest(path, "sha1"), "strictXml": True,
                 "method": "original_direct_export_strict_xml",
                 "acceptedFullTextCompared": False}
        if event.get("validationReceipt"):
            receipt = safe(args.root, event["validationReceipt"])
            if digest(receipt) != event["validationReceiptSha256"]:
                raise ValueError("Original conversion receipt hash differs")
            result = read(receipt)
            original = result.get("original_converter_result", result)
            if not (original.get("status") == "verified" and original.get("sourceSha256") == proof["sourceSha256"]
                    and original.get("outputSha256") == proof["outputSha256"] and original.get("strictXml") is True
                    and original.get("redlinesAfter") == 0 and original.get("acceptedRenderedText", {}).get("equal") is True):
                raise ValueError("Strict native recovery receipt differs")
            if "original_converter_result" in result and not (result.get("passed") is True and result.get("source_hash_unchanged") is True):
                raise ValueError("Explicit fallback receipt differs")
            proof.update(method=event.get("method", original["method"]), acceptedFullTextCompared=True,
                         acceptedRenderedText=original["acceptedRenderedText"], conversionReceiptSha256=digest(receipt))
        conversions.append(proof)
    result = {"schema": SCHEMA, "fixtureSha256": digest(args.fixture), "constructorReceiptSha256": digest(args.constructor),
              "pins": pins, "sourceTextIncluded": False, "conversions": conversions}
    write(args.out, result)
    return {"conversions": len(conversions), "fullTextComparisons": sum(r["acceptedFullTextCompared"] for r in conversions)}


def verify_inputs(root, fixture_path, proof_path, code, native_module):
    started = time.monotonic()
    fixture, proof = read(fixture_path), read(proof_path)
    pins, clause, pack, native = modules(code, native_module)
    failures, rows, counts = [], [], collections.Counter()
    if pins != fixture["pins"] or proof.get("pins") != pins or proof.get("fixtureSha256") != digest(fixture_path):
        failures.append({"error": "code_or_fixture_binding"})
    expected_paths = {r["path"] for r in fixture["files"]}
    actual_paths, actual_dirs = set(), set()
    for scope in fixture["scopeRoots"]:
        base = safe(root, scope)
        if base.is_dir():
            actual_dirs.add(scope)
            for path in base.rglob("*"):
                relative = path.relative_to(root).as_posix()
                if path.is_symlink():
                    failures.append({"path": relative, "error": "scoped_symlink"})
                elif path.is_file():
                    actual_paths.add(relative)
                elif path.is_dir():
                    actual_dirs.add(relative)
    for label, expected, actual in (("file", expected_paths, actual_paths), ("directory", set(fixture["directories"]), actual_dirs)):
        for path in sorted(expected - actual):
            failures.append({"path": path, "error": label + "_missing"})
        for path in sorted(actual - expected):
            failures.append({"path": path, "error": label + "_unexpected"})
    conversions = {r["path"]: r for r in proof["conversions"]}
    expected_conversions = {r["path"] for r in fixture["files"] if r["converted"]}
    if set(conversions) != expected_conversions or len(conversions) != len(proof["conversions"]):
        failures.append({"error": "conversion_coverage"})
    for archive in fixture["archives"]:
        path = safe(root, archive["path"])
        if not path.is_file() or digest(path) != archive["sha256"] or path.stat().st_size != archive["bytes"]:
            failures.append({"path": archive["path"], "error": "archive_bytes"})
        else:
            counts["exactArchives"] += 1
    for expected in fixture["files"]:
        path = safe(root, expected["path"])
        if not path.is_file():
            continue
        actual = {"path": expected["path"], "sha256": digest(path), "sha1": digest(path, "sha1"), "bytes": path.stat().st_size}
        counts["filesPresent"] += 1
        if expected["converted"]:
            counts["convertedFiles"] += 1
            receipt = conversions.get(expected["path"], {})
            source = safe(root, expected["nativePath"])
            if not source.is_file() or not (receipt.get("nativePath") == expected["nativePath"]
                    and receipt.get("sourceSha256") == digest(source) and receipt.get("outputSha256") == actual["sha256"]
                    and receipt.get("outputSha1") == actual["sha1"] and receipt.get("strictXml") is True):
                failures.append({"path": expected["path"], "error": "conversion_binding"})
            try:
                native.validate_docx(path)
            except Exception as error:
                failures.append({"path": expected["path"], "error": "strict_xml", "exception": type(error).__name__})
            counts["historicalConvertedBytesDiffer"] += actual["sha256"] != expected["sha256"]
            if receipt.get("acceptedFullTextCompared"):
                counts["nativeFullTextRecoveryReceipts"] += 1
        elif actual["sha256"] != expected["sha256"] or actual["sha1"] != expected["sha1"] or actual["bytes"] != expected["bytes"]:
            failures.append({"path": expected["path"], "error": "unconverted_bytes"})
        else:
            counts["exactUnconvertedFiles"] += 1
        try:
            scientific = reader_digests(path, clause, pack, expected["readerDigests"])
            actual["readerDigests"] = scientific
            if scientific != expected["readerDigests"]:
                failures.append({"path": expected["path"], "error": "scientific_reader_digest"})
            else:
                counts["readerComparisonsMatched"] += len(scientific)
        except Exception as error:
            failures.append({"path": expected["path"], "error": "reader_exception", "exception": type(error).__name__})
        rows.append(actual)
    return {"schema": SCHEMA, "scope": fixture["scope"], "fixtureSha256": digest(fixture_path),
            "conversionProofSha256": digest(proof_path), "pins": pins,
            "selectedInputGatePassed": not failures, "completeScopedPathCoverage": expected_paths == actual_paths and set(fixture["directories"]) == actual_dirs,
            "wholeCorpusFreshlyReconstructed": False, "fullScientificAuditRequired": True,
            "inputSetDigest": logical_digest(rows), "counts": dict(counts), "files": rows,
            "failures": failures, "elapsedSeconds": time.monotonic() - started}


def append_event(path, value):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(descriptor, (json.dumps(value) + "\n").encode())
    finally:
        os.close(descriptor)


def replaced_form_reader(path_text):
    """Top-level callable preserves the original process-pool execution path."""
    replacement = _AUDIT_REPLACEMENTS.get(Path(path_text).resolve())
    if replacement is None:
        return _AUDIT_FORM_READER(path_text)
    value = _AUDIT_FORM_READER(str(replacement))
    actual_sha1 = digest(replacement, "sha1")
    if value.get("sha1") != actual_sha1:
        raise ValueError("Original reader must return actual reconstructed SHA1")
    value["path"] = path_text
    append_event(_AUDIT_EVENTS, {"reader": "clause", "logicalPath": str(Path(path_text)),
                               "corpusRelativePath": replacement.relative_to(_AUDIT_ROOT).as_posix(),
                               "replacementSha256": digest(replacement), "actualSha1": actual_sha1})
    return value


def run_audit(args):
    global _AUDIT_FORM_READER, _AUDIT_REPLACEMENTS, _AUDIT_EVENTS, _AUDIT_ROOT
    # The unchanged runner changes cwd to the stage while it reads sources.
    for field in ("root", "fixture", "proof", "code", "native_module", "original_root", "stage", "artifact", "reference"):
        setattr(args, field, getattr(args, field).resolve())
    result = verify_inputs(args.root, args.fixture, args.proof, args.code, args.native_module)
    if not result["selectedInputGatePassed"]:
        raise ValueError("Selected input gate failed")
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError("Audit output must be new or empty")
    out.mkdir(parents=True, exist_ok=True)
    write(out / "input_gate.json", result)
    runner_path = args.code / "restore_census_artifact.py"
    runner = load(runner_path, "gate_original_runner")
    original_load = runner.load
    replacements = {safe(args.original_root, r["path"]).resolve(): safe(args.root, r["path"]).resolve() for r in result["files"]}
    events = out / "replacement_reads.jsonl"
    _AUDIT_REPLACEMENTS, _AUDIT_EVENTS, _AUDIT_ROOT = replacements, events, args.root

    def adapted_load(path, name):
        global _AUDIT_FORM_READER
        module = original_load(path, name)
        if name == "census_original_clause_audit":
            _AUDIT_FORM_READER = module.read_form
            module.read_form = replaced_form_reader
        elif name == "census_original_pack_audit":
            original = module.read_cover

            def read_cover(source):
                replacement = replacements.get(Path(source).resolve()) if isinstance(source, (str, Path)) else None
                if replacement is None:
                    return original(source)
                append_event(events, {"reader": "pack", "logicalPath": str(source),
                                      "corpusRelativePath": replacement.relative_to(args.root.resolve()).as_posix(),
                                      "replacementSha256": digest(replacement), "actualSha1": digest(replacement, "sha1")})
                return original(replacement)
            module.read_cover = read_cover
        return module

    runner.load = adapted_load
    condition = {"schema": SCHEMA, "fixtureSha256": digest(args.fixture), "conversionProofSha256": digest(args.proof),
                 "inputSetDigest": result["inputSetDigest"], "pins": result["pins"],
                 "helperSha256": digest(__file__), "wholeCorpusFreshlyReconstructed": False,
                 "sourceMode": "local_original_inputs_with_complete_selected_archive_read_replacements",
                 "actualReconstructedSha1Retained": True, "originalDeduplicationUnchanged": True,
                 "audits": ["pack", "clause"], "wg": [f"RAN{i}" for i in range(1, 6)]}
    write(out / "audit_condition.json", condition)
    audit_args = argparse.Namespace(stage=args.stage, artifact=args.artifact, reference=args.reference, out=out,
                                    audits=condition["audits"], wg=tuple(condition["wg"]), workers=1,
                                    source_mode=condition["sourceMode"])
    try:
        runner.audit(audit_args)
    finally:
        after = verify_inputs(args.root, args.fixture, args.proof, args.code, args.native_module)
        condition["selectedInputsUnchanged"] = after["inputSetDigest"] == result["inputSetDigest"] and after["selectedInputGatePassed"]
        condition["readEventsSha256"] = digest(events) if events.exists() else None
        condition["readEvents"] = sum(1 for _ in events.open()) if events.exists() else 0
        write(out / "audit_condition.json", condition)
    return condition


def certify(args):
    result = verify_inputs(args.root, args.fixture, args.proof, args.code, args.native_module)
    audit_passed = False
    if args.audit_directory:
        directory = args.audit_directory
        condition, replay = read(directory / "audit_condition.json"), read(directory / "replay_receipt.json")
        event_rows = [json.loads(line) for line in (directory / "replacement_reads.jsonl").open()]
        expected_reads = {(row["path"], kind) for row in read(args.fixture)["files"] for kind in row["requiredFullAuditReaders"]}
        actual_reads = {(row["corpusRelativePath"], row["reader"]) for row in event_rows}
        identities = {row["path"]: row for row in result["files"]}
        checks = [condition.get("fixtureSha256") == digest(args.fixture), condition.get("conversionProofSha256") == digest(args.proof),
                  condition.get("inputSetDigest") == result["inputSetDigest"], condition.get("pins") == result["pins"],
                  condition.get("helperSha256") == digest(__file__), condition.get("selectedInputsUnchanged") is True,
                  condition.get("actualReconstructedSha1Retained") is True, condition.get("originalDeduplicationUnchanged") is True,
                  condition.get("wg") == [f"RAN{i}" for i in range(1, 6)], set(replay.get("audits", {})) == {"pack", "clause"},
                  replay.get("sourceMode") == condition.get("sourceMode"),
                  condition.get("readEventsSha256") == digest(directory / "replacement_reads.jsonl"),
                  expected_reads <= actual_reads,
                  all(row.get("actualSha1") == identities[row["corpusRelativePath"]]["sha1"] and row.get("replacementSha256") == identities[row["corpusRelativePath"]]["sha256"] for row in event_rows)]
        for kind in ("pack", "clause"):
            row = replay.get("audits", {}).get(kind, {})
            reference = args.reference / ("pack_link_audit.json" if kind == "pack" else "final/reconciliation/clause_link_audit_rerun.json")
            checks.extend([row.get("allComparedFieldsMatch") is True, not any(row.get("comparison", {"missing": [1]}).values()),
                           row.get("auditorSha256") == result["pins"][f"audit_{kind}_links.py"],
                           row.get("outputSha256") == digest(directory / f"{kind}_audit.json"),
                           row.get("referenceSha256") == digest(reference)])
        audit_passed = all(checks)
    result.update(fullScientificAuditPassed=audit_passed,
                  selectedReconstructionWithFullAuditPassed=result["selectedInputGatePassed"] and audit_passed,
                  fullCorpusReconstructionCertified=False)
    write(args.out, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("fixture", "conversion-proof", "verify", "run-audit", "certify"):
        child = sub.add_parser(name)
        for field in ("code", "native-module", "out"):
            child.add_argument("--" + field, type=Path, required=True)
        if name != "fixture":
            child.add_argument("--fixture", type=Path, required=True)
            child.add_argument("--root", type=Path, required=True)
        if name in ("fixture", "conversion-proof"):
            child.add_argument("--constructor", type=Path, required=True)
        if name == "fixture":
            child.add_argument("--original-root", type=Path, required=True)
            child.add_argument("--frontier", type=Path, required=True)
            child.add_argument("--frontier-receipt", type=Path, required=True)
            child.add_argument("--public-commit", required=True)
        if name in ("verify", "run-audit", "certify"):
            child.add_argument("--proof", type=Path, required=True)
        if name in ("run-audit", "certify"):
            child.add_argument("--reference", type=Path, required=True)
        if name == "run-audit":
            for field in ("original-root", "stage", "artifact"):
                child.add_argument("--" + field, type=Path, required=True)
        if name == "certify":
            child.add_argument("--audit-directory", type=Path)
    args = parser.parse_args()
    if args.command == "fixture":
        result = make_fixture(args)
    elif args.command == "conversion-proof":
        result = make_conversion_proof(args)
    elif args.command == "run-audit":
        result = run_audit(args)
    elif args.command == "certify":
        result = certify(args)
    else:
        result = verify_inputs(args.root, args.fixture, args.proof, args.code, args.native_module)
        write(args.out, result)
    print(json.dumps({k: v for k, v in result.items() if k not in ("files", "pins")}, ensure_ascii=False))
    if args.command == "verify" and not result["selectedInputGatePassed"]:
        raise SystemExit(1)
    if args.command == "certify" and not result["selectedReconstructionWithFullAuditPassed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
