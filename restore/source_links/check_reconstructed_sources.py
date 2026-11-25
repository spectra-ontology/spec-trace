#!/usr/bin/env python3
"""Replay the pinned conversion/nested-ZIP source frontier without model calls.

The expected reader digests stay fixed. Native archives, nested members, fresh
conversion receipts and current benchmark membership are checked separately.
Source documents and converted files remain in --work; reports contain hashes.
"""
import argparse
import collections
import concurrent.futures
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import urllib.request
import zipfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    if isinstance(value, dict):
        return {str(k): canonical(v) for k, v in sorted(value.items())}
    if isinstance(value, (set, frozenset)):
        return sorted((canonical(v) for v in value), key=lambda v: json.dumps(v, sort_keys=True))
    if isinstance(value, (list, tuple)):
        return [canonical(v) for v in value]
    return value


def reader_digest(form):
    data = {k: v for k, v in form.items() if k not in ("path", "sha1")}
    return sha(json.dumps(canonical(data), ensure_ascii=False, separators=(",", ":")).encode())


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def conversion_receipt(source, target, receipt):
    result = json.loads(receipt.read_text())
    if not (result.get("status") == "verified" and result.get("strictXml") is True
            and result.get("sourceSha256") == sha(source.read_bytes())
            and result.get("outputSha256") == sha(target.read_bytes())):
        raise ValueError("Conversion receipt does not bind native/output bytes")
    if result.get("method") != "original_direct_export_strict_xml" and result.get("acceptedRenderedText", {}).get("equal") is not True:
        raise ValueError("Accepted-native conversion requires its original full-text equality")
    return result


def convert(converter, source, target, receipt, timeout, python):
    process = subprocess.Popen([python, "-B", str(converter), "--source", str(source),
        "--output", str(target), "--receipt", str(receipt), "--supervised-process-group"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
        raise TimeoutError("Owned conversion process exceeded its cap")
    if process.returncode:
        raise RuntimeError("Native conversion failed: " + stderr[-1500:])
    return conversion_receipt(source, target, receipt)


def convert_original(constructor, native, source, target, receipt, timeout, python):
    before = sha(source.read_bytes())
    snippet = "import importlib.util,json,sys; p=sys.argv[1]; s=importlib.util.spec_from_file_location('original_doc_constructor',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); r=m.convert_doc_to_docx(__import__('pathlib').Path(sys.argv[2]),__import__('pathlib').Path(sys.argv[3])); print(json.dumps(r)); sys.exit(0 if r.get('success') else 1)"
    environment = dict(os.environ, SPECTRA_DOC_CONVERT_TIMEOUT=str(timeout))
    process = subprocess.run([python, "-B", "-c", snippet, str(constructor), str(source), str(target)],
                             capture_output=True, text=True, timeout=timeout + 30, env=environment)
    if process.returncode:
        raise RuntimeError("Original direct constructor failed: " + process.stdout[-1000:] + process.stderr[-500:])
    native.validate_docx(target)
    if sha(source.read_bytes()) != before:
        raise ValueError("Native source changed during direct construction")
    result = {"status": "verified", "method": "original_direct_export_strict_xml",
              "constructorSha256": sha(constructor.read_bytes()), "sourceSha256": before,
              "outputSha256": sha(target.read_bytes()), "strictXml": True,
              "acceptedFullTextCompared": False,
              "scope": "Original constructor and complete scientific-reader comparison; whole-document text equality is a separate predicate."}
    native_receipt = Path(str(target) + ".conversion.json")
    if native_receipt.exists():
        result["nativeRecoveryReceiptSha256"] = sha(native_receipt.read_bytes())
    receipt.write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--release", type=Path, default=Path("."))
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--workers", type=int, choices=(1, 2), default=1)
    ap.add_argument("--conversion-timeout", type=int, default=120)
    ap.add_argument("--conversion-python", default=sys.executable,
                    help="Python with LibreOffice pyUNO; often /usr/bin/python3 on Linux")
    ap.add_argument("--conversion-policy", choices=("original", "accepted"), default="original",
                    help="Original census constructor, or the stronger whole-text accepted-native/reopen route")
    args = ap.parse_args()
    args.release = args.release.resolve()
    args.work = args.work.resolve()
    fixture = json.loads(args.manifest.read_text())
    code = args.release / "code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
    reader_path = code / "audit_clause_links.py"
    converter = args.release / "code/scripts/tsg/RAN/formal/common/native_word_conversion.py"
    constructor = args.release / "code/scripts/tsg/RAN/formal/RAN3/phase-0/transform/01_transform_doc_to_docx.py"
    for path, expected in [(reader_path, fixture["reader_sha256"]),
                           (converter, fixture["converter_sha256"]),
                           (args.release / "restore/source_links/benchmark_clause_manifest.json", fixture["original_manifest_sha256"]),
                           (constructor, fixture["original_constructor_sha256"])]:
        if sha(path.read_bytes()) != expected:
            raise ValueError("Pinned code or original manifest differs: " + str(path))
    reader = load(reader_path, "restoration_clause_reader")
    native = load(converter, "restoration_native_validation")
    preflight = subprocess.run([args.conversion_python, "-c", "import uno"], capture_output=True, text=True)
    if preflight.returncode:
        raise SystemExit("LibreOffice pyUNO is required for native conversion. Install it for the selected interpreter or pass --conversion-python /usr/bin/python3.")
    original = json.loads((args.release / "restore/source_links/benchmark_clause_manifest.json").read_text())
    frontier = {(e["wg"], e["cr"], e["section"]): e for e in original["entries"]
                if e["preparation_status"] != "ready_native_ooxml"}
    selected = {(e["wg"], e["cr"], p["section"]) for e in fixture["forms"] for p in e["pairs"]}
    if selected != set(frontier):
        raise ValueError("Restoration fixture must cover the complete historical exception frontier")
    items, records = {}, {}
    for part in ("core", "ran5"):
        path = args.release / f"benchmark/items_final/gate/{part}/chain_items_admitted.jsonl"
        items.update((item["id"], item) for item in map(json.loads, path.read_text().splitlines()) if item)
    for entry in fixture["forms"]:
        wg = entry["wg"]
        if wg not in records:
            folder = "records/RAN5_graph_export/RAN5" if wg == "RAN5" else f"records/phase-4/{wg}"
            rows = json.loads((args.release / folder / "cr_extensions.jsonld").read_text())["@graph"]
            records[wg] = {row["@id"].removeprefix("tdoc:"): row for row in rows}
        sections = records[wg].get(entry["cr"], {}).get("modifiesSection", [])
        sections = [sections] if isinstance(sections, str) else sections
        for pair in entry["pairs"]:
            previous = frontier[(wg, entry["cr"], pair["section"])]
            if pair["item_ids"] != previous["item_ids"] or pair["section"] not in sections:
                raise ValueError("Released pair membership differs")
            match = reader.SECTION.fullmatch(pair["section"])
            for item_id in pair["item_ids"]:
                item = items[item_id]
                gold = [dict(zip(item["fields"], row)) for row in item["gold"]]
                full = item["family"] == "full_chain" and item["anchor"] == "tdoc:" + entry["cr"] and any(r.get("clause") == match["clause"] for r in gold)
                history = item["family"] == "clause_history" and item["anchor"] == pair["section"] and any(r.get("document") == entry["cr"] for r in gold)
                if item["wg"] != wg or not (full or history):
                    raise ValueError("Released item/gold membership differs")
    args.work.mkdir(parents=True, exist_ok=True)
    archives = {}
    for entry in fixture["forms"]:
        key = entry["archive_sha256"]
        if key in archives:
            continue
        path = args.work / "archives" / (key + ".zip")
        path.parent.mkdir(parents=True, exist_ok=True)
        downloaded = False
        if not path.exists():
            if args.offline:
                raise FileNotFoundError("Offline archive missing: " + key)
            if not re.match(r"^https://www\.3gpp\.org/ftp/", entry["url"]):
                raise ValueError("Expected official 3GPP archive URL")
            request = urllib.request.Request(entry["url"], headers={"User-Agent": "SPECTRA-source-restoration/1.0"})
            with urllib.request.urlopen(request, timeout=45) as response:
                data = response.read(256 * 1024 * 1024 + 1)
            if len(data) > 256 * 1024 * 1024 or sha(data) != key:
                raise ValueError("Downloaded archive size/hash differs")
            path.write_bytes(data)
            downloaded = True
        if sha(path.read_bytes()) != key:
            raise ValueError("Cached archive hash differs: " + key)
        archives[key] = {"sha256": key, "bytes": path.stat().st_size, "url": entry["url"],
                         "downloaded_this_run": downloaded}
    start = time.monotonic()

    def check(entry):
        result = {k: entry[k] for k in ("wg", "cr", "archive_sha256", "source_kind", "pairs")}
        directory = args.work / "forms" / entry["wg"] / entry["cr"]
        directory.mkdir(parents=True, exist_ok=True)
        try:
            data = (args.work / "archives" / (entry["archive_sha256"] + ".zip")).read_bytes()
            for member in entry["member_chain"]:
                with zipfile.ZipFile(io.BytesIO(data)) as archive:
                    info = archive.getinfo(member["name"])
                    if info.file_size > 64 * 1024 * 1024:
                        raise ValueError("Native member exceeds 64 MiB")
                    data = archive.read(info)
                if sha(data) != member["sha256"]:
                    raise ValueError("Native/nested member hash differs")
            source = directory / Path(entry["member_chain"][-1]["name"]).name
            source.write_bytes(data)
            result["native_sha256"] = sha(data)
            target = source
            if entry["source_kind"] == "legacy_doc_conversion":
                target = directory / "accepted.docx"
                receipt = directory / "conversion.json"
                if target.exists() and receipt.exists():
                    conversion = conversion_receipt(source, target, receipt)
                    result["conversion_executed_this_run"] = False
                elif target.exists() or receipt.exists():
                    raise FileExistsError("Incomplete conversion cache: use a fresh work directory")
                else:
                    if args.conversion_policy == "original":
                        conversion = convert_original(constructor, native, source, target, receipt,
                                                      args.conversion_timeout, args.conversion_python)
                    else:
                        conversion = convert(converter, source, target, receipt, args.conversion_timeout, args.conversion_python)
                    result["conversion_executed_this_run"] = True
                result.update(conversion_receipt_sha256=sha(receipt.read_bytes()),
                              conversion=conversion)
            native.validate_docx(target)
            # The reader also checks the specification encoded in the filename.
            # Preserve that source context while retaining the converter's actual receipt.
            reader_path = directory / "reader_view" / Path(entry["historical_source_path"]).name
            reader_path.parent.mkdir(exist_ok=True)
            reader_path.write_bytes(target.read_bytes())
            if sha(reader_path.read_bytes()) != sha(target.read_bytes()):
                raise ValueError("Reader view differs from actual constructor output")
            form = reader.read_form(str(reader_path))
            actual_digest = reader_digest(form)
            equivalent = actual_digest == entry["historical_reader_digest"]
            result.update(output_sha256=sha(target.read_bytes()), historical_form_sha256=entry["historical_form_sha256"],
                          reader_filename=reader_path.name,
                          historical_reader_digest=entry["historical_reader_digest"],
                          actual_reader_digest=actual_digest, reader_equivalent=equivalent)
            names = reader.TDOC.findall(Path(entry["historical_source_path"]).name)
            identity = entry["cr"] in form.get("tdocs_before_label", []) or bool(names and names[0].upper() == entry["cr"].upper())
            pair_results = []
            for pair in entry["pairs"]:
                match = reader.SECTION.fullmatch(pair["section"])
                category, spec_source = reader.judge(form, match["spec"], match["clause"], set())
                pair_results.append({**pair, "category": category, "spec_source": spec_source,
                    "confirmed": identity and category in reader.CONFIRMED})
            result.update(cr_identity_confirmed=identity, pairs=pair_results,
                          status="reader_equivalent_confirmed" if equivalent and all(p["confirmed"] for p in pair_results) else "reader_or_pair_difference")
        except Exception as error:
            result.update(status="failed", error=type(error).__name__, detail=str(error))
        return result

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(check, fixture["forms"]))
    pair_counts = collections.Counter()
    for result in results:
        pair_counts[result["status"]] += len(result["pairs"])
    report = {"schema": "spectra-reconstructed-benchmark-sources-v1", "offline": args.offline,
        "manifest_sha256": sha(args.manifest.read_bytes()), "checker_sha256": sha(Path(__file__).read_bytes()),
        "reader_sha256": fixture["reader_sha256"], "converter_sha256": fixture["converter_sha256"],
        "scope": "Selected 53 historical native-check exceptions; exact archive/member provenance and reader-equivalent clause confirmation. Full corpus, new model execution and complete system cost are separate scopes.",
        "forms": len(results), "pairs": sum(pair_counts.values()), "items": len({i for r in results for p in r["pairs"] for i in p["item_ids"]}),
        "pair_status_counts": dict(pair_counts), "archives": list(archives.values()),
        "results": results, "elapsed_seconds": time.monotonic() - start}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("forms", "pairs", "items", "pair_status_counts", "elapsed_seconds")}))
    if any(r["status"] != "reader_equivalent_confirmed" for r in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
