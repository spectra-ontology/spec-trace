#!/usr/bin/env python3
"""Download pinned official archives, then check CR forms without any DB server.

--offline never opens a URL. Manifest preparation is separate from checking;
archive and member hashes are independently verified against pinned values.
The released audit module is imported, never its server-dependent main().
"""
import argparse
import collections
import hashlib
import importlib.util
import json
import re
import time
import urllib.request
import zipfile
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--release", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--timeout", type=int, default=45)
    ap.add_argument("--wg", nargs="+", help="Check only these manifest working groups")
    args = ap.parse_args()
    manifest = json.loads(args.manifest.read_text())
    checker_sha256 = sha(Path(__file__).read_bytes())
    parser = args.release / "code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/audit_clause_links.py"
    if sha(parser.read_bytes()) != manifest["reader_sha256"]:
        raise SystemExit("Released reader hash differs from manifest")
    spec = importlib.util.spec_from_file_location("released_clause_reader", parser)
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    args.work.mkdir(parents=True, exist_ok=True)
    archives, checks, results = {}, {}, []
    released_links = {}
    released_items = {}
    for part in ("core", "ran5"):
        item_path = args.release / f"benchmark/items_final/gate/{part}/chain_items_admitted.jsonl"
        for line in item_path.read_text().splitlines():
            item = json.loads(line)
            released_items[item["id"]] = item
    start = time.monotonic()
    for entry in manifest["entries"]:
        if args.wg and entry["wg"] not in args.wg:
            continue
        out = {k: entry[k] for k in ("wg", "cr", "section", "rank_within_wg", "item_ids")}
        if entry["wg"] not in released_links:
            folder = "records/RAN5_graph_export/RAN5" if entry["wg"] == "RAN5" else f"records/phase-4/{entry['wg']}"
            rows = json.loads((args.release / folder / "cr_extensions.jsonld").read_text())["@graph"]
            released_links[entry["wg"]] = {r["@id"].removeprefix("tdoc:"): r for r in rows}
        record = released_links[entry["wg"]].get(entry["cr"], {})
        sections = record.get("modifiesSection", [])
        sections = [sections] if isinstance(sections, str) else sections
        match = reader.SECTION.fullmatch(entry["section"])
        if not match:
            results.append(dict(out, status="validation_failed", reason="invalid_released_section_identifier"))
            continue
        membership = bool(entry["item_ids"]) and entry["section"] in sections and bool(match)
        for item_id in entry["item_ids"]:
            item = released_items.get(item_id, {})
            if item.get("wg") != entry["wg"]:
                membership = False
            elif item.get("family") == "full_chain":
                membership &= item["anchor"] == f"tdoc:{entry['cr']}" and any(
                    dict(zip(item["fields"], row)).get("clause") == match["clause"] for row in item["gold"])
            elif item.get("family") == "clause_history":
                membership &= item["anchor"] == entry["section"] and any(
                    dict(zip(item["fields"], row)).get("document") == entry["cr"] for row in item["gold"])
            else:
                membership = False
        if not membership:
            results.append(dict(out, status="validation_failed", reason="manifest_pair_not_in_released_benchmark"))
            continue
        out["released_link_and_benchmark_membership"] = True
        if entry["preparation_status"] != "ready_native_ooxml":
            results.append(dict(out, status="source_unavailable", reason=entry["preparation_status"]))
            continue
        digest = entry["archive_sha256"]
        if digest not in archives:
            target = args.work / f"{digest}.zip"
            record = {"url": entry["url"], "expected_sha256": digest, "cache_path": str(target), "downloaded_this_run": False}
            try:
                if not target.exists():
                    if args.offline:
                        raise FileNotFoundError("Offline cache lacks pinned archive")
                    if not re.match(r"^https://www\.3gpp\.org/ftp/", entry["url"]):
                        raise ValueError("Manifest URL is outside official archive")
                    before = time.monotonic()
                    request = urllib.request.Request(entry["url"], headers={"User-Agent": "SPECTRA-source-check/1.0"})
                    with urllib.request.urlopen(request, timeout=args.timeout) as response:
                        data = response.read(256 * 1024 * 1024 + 1)
                        record.update(final_url=response.url, http_status=response.status)
                    if len(data) > 256 * 1024 * 1024:
                        raise ValueError("Archive exceeds 256 MiB download limit")
                    if sha(data) != digest:
                        raise ValueError("Downloaded archive SHA256 differs")
                    target.write_bytes(data)
                    record.update(downloaded_this_run=True, download_seconds=time.monotonic()-before)
                raw = target.read_bytes()
                record.update(actual_sha256=sha(raw), bytes=len(raw))
                if record["actual_sha256"] != digest:
                    raise ValueError("Cached archive SHA256 differs")
                archives[digest] = (target, None)
                record["status"] = "hash_verified"
            except Exception as error:
                record.update(status="source_access_failed", error=type(error).__name__, detail=str(error))
                archives[digest] = (None, record["status"])
            checks[digest] = record
        path, error = archives[digest]
        if error:
            results.append(dict(out, status=error))
            continue
        try:
            with zipfile.ZipFile(path) as archive:
                member = archive.getinfo(entry["member"])
                if member.file_size > 64 * 1024 * 1024:
                    raise ValueError("Form exceeds 64 MiB member limit")
                data = archive.read(member)
            if sha(data) != entry["member_sha256"]:
                raise ValueError("Member SHA256 differs")
            target = args.work / "forms" / entry["wg"] / entry["cr"] / Path(entry["member"]).name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            form = reader.read_form(str(target))
            names = reader.TDOC.findall(target.name)
            identity = entry["cr"] in form.get("tdocs_before_label", []) or bool(names and names[0].upper() == entry["cr"].upper())
            out.update(member_sha256=sha(data), form_status=form["status"], cr_identity_confirmed=identity)
            if form["status"] != "ok":
                out.update(status="form_unavailable", reason=form["status"])
            elif not identity:
                out.update(status="cr_identity_unconfirmed")
            else:
                match = reader.SECTION.fullmatch(entry["section"])
                if not match:
                    raise ValueError("Invalid released section identifier")
                category, spec_source = reader.judge(form, match["spec"], match["clause"], set())
                out.update(status="confirmed" if category in reader.CONFIRMED else "not_confirmed",
                           category=category, spec_source=spec_source, form_release=form.get("release"),
                           section_release=match["release"], clause_cell_sha256=sha(form["clauses"].encode()),
                           clause_cell_characters=len(form["clauses"]))
        except Exception as error:
            out.update(status="validation_failed", error=type(error).__name__, detail=str(error))
        results.append(out)
    report = {"schema": "spectra-cr-source-check-v1", "manifest_sha256": sha(args.manifest.read_bytes()),
              "reader_sha256": manifest["reader_sha256"], "checker_sha256": checker_sha256,
              "offline": args.offline, "working_groups": args.wg,
              "scope": "Native OOXML CR form/spec/clause confirmation only. No whole-census, release-resolution, clause-body coverage, pack membership, or disposition rerun.",
              "pairs": len(results), "status_counts": dict(collections.Counter(r["status"] for r in results)),
              "archives": list(checks.values()), "results": results, "elapsed_seconds": time.monotonic()-start}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("pairs", "status_counts", "elapsed_seconds")}))
    if any(r["status"] in ("source_access_failed", "validation_failed") for r in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
