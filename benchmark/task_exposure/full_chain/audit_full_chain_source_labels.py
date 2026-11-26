#!/usr/bin/env python3
"""Compare released full-chain labels to their pinned CR form fields offline."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import importlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import tempfile


TRACK = Path("publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark")
GOLD_PATHS = [
    Path(f"benchmark/items_final/gate/{name}/chain_items_admitted.jsonl")
    for name in ("core", "ran5")
]
MANIFEST = Path("restore/source_links/benchmark_clause_manifest.json")
RECONSTRUCTED_MANIFEST = Path("restore/source_links/reconstructed_source_manifest.json")
MODULES = ("audit_clause_links.py", "analyze_template_session.py", "score_chain_eval.py",
           "build_chain_items.py", "score_meeting_spelling_sensitivity.py",
           "score_meeting_suffix_insensitive.py", "summarize_text_route_full.py")
ASN_MARKER = re.compile(r"\bASN\.?\s*1\b", re.I)
SPEC_OR_RELEASE_IN_PROSE = re.compile(
    r"\b(?:for|to)\s+(?:(?:TS|TR)\s+)?\d{5}\b|\bR(?:el)?[\s-]+\d+\b",
    re.I,
)
PLACEHOLDER_LABEL = re.compile(r"(?<![\w.])\d+(?:\.\d+)*\.x+(?![\w.]|\.\w)", re.I)


def digest(path: Path) -> str:
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(2**20), b""):
            checksum.update(block)
    return checksum.hexdigest()


def form_labels(reader, field: str) -> tuple[set[str], set[str]]:
    """Enumerate numeric and lettered clause labels without looking at gold."""
    field = reader.TDOC.sub(" ; ", field)
    field = ASN_MARKER.sub(" ; ", field)
    field = SPEC_OR_RELEASE_IN_PROSE.sub(" ; ", field)
    text, _, tables = reader.masked(field)
    if tables or reader.SLASH.search(text) or reader.RANGE.search(text):
        raise ValueError(f"Unadjudicated table, shorthand, or range syntax: {field!r}")
    placeholders = {match.group().lower() for match in PLACEHOLDER_LABEL.finditer(text)}
    text = PLACEHOLDER_LABEL.sub(" ; ", text)
    candidates = {match.group() for match in reader.TOKEN.finditer(text)}
    return {label.lower() for label in candidates if reader.literal(text, label)}, placeholders


def from_labels(item: dict, labels: set[str]) -> dict:
    prefixes = {tuple(row[:-1]) for row in item["gold"]}
    gold_labels = {row[-1].lower() for row in item["gold"]}
    original = {tuple(row[:-1]) + (row[-1].lower(),) for row in item["gold"]}
    if original != {prefix + (label,) for prefix in prefixes for label in gold_labels}:
        raise ValueError(f'{item["id"]}: stored rows are not a full prefix-label product')
    return {**item, "gold": [list(prefix + (label,)) for prefix in sorted(prefixes)
                             for label in sorted(labels)]}


def load_items(release: Path) -> tuple[dict, dict]:
    items = {}
    for path in GOLD_PATHS:
        for line in (release / path).read_text().splitlines():
            item = json.loads(line)
            if item["id"] in items:
                raise ValueError(f'Duplicate item {item["id"]}')
            items[item["id"]] = item
    full_chain = {key: item for key, item in items.items() if item["family"] == "full_chain"}
    if len(items) != 667 or len(full_chain) != 100:
        raise ValueError("Unexpected admitted workload size")
    return items, full_chain


def check_sqlite_pins(sqlite_root: Path, release: Path) -> dict[str, str]:
    pins = {}
    for line in (release / "sqlite/SHA256SUMS.txt").read_text().splitlines():
        checksum, name = line.split()
        if name.endswith(".sqlite"):
            if digest(sqlite_root / name) != checksum:
                raise ValueError(f"{name}: scoring snapshot differs from release")
            pins[name] = checksum
    return pins


def compare(checkout: Path, release: Path) -> dict:
    vendored = release / "code/scripts" / TRACK
    scripts = checkout / "scripts" / TRACK
    script_hashes = {name: digest(vendored / name) for name in MODULES}
    if script_hashes != {name: digest(scripts / name) for name in MODULES}:
        raise ValueError("Local form reader or scorer bytes differ from release")
    sys.path.insert(0, str(scripts))
    reader = importlib.import_module("audit_clause_links")
    analyzer = importlib.import_module("analyze_template_session")

    sqlite_root = checkout / "logs" / TRACK / "integration/sqlite_final"
    sqlite_pins = check_sqlite_pins(sqlite_root, release)

    manifest = json.loads((release / MANIFEST).read_text())
    if manifest["reader_sha256"] != script_hashes["audit_clause_links.py"]:
        raise ValueError("Unexpected reader hash in source manifest")
    reconstruction = json.loads((release / RECONSTRUCTED_MANIFEST).read_text())
    reconstructed = {(f["wg"], f["cr"]): f for f in reconstruction["forms"]}

    items, full_chain = load_items(release)

    by_item = defaultdict(list)
    for entry in manifest["entries"]:
        for key in entry["item_ids"]:
            if key in full_chain:
                by_item[key].append(entry)
    if set(full_chain) != set(by_item):
        raise ValueError("Unexpected coverage of released full-chain items")

    form_report = {}
    strict, literal, at_source_release = {}, {}, {}
    for key, item in sorted(full_chain.items()):
        entries = by_item[key]
        expected = {(e["source_path"], e["form_sha256"], e["local_archive"], e["archive_sha256"])
                    for e in entries}
        if len(expected) != 1 or any(e["cr"] != item["anchor"].removeprefix("tdoc:") for e in entries):
            raise ValueError(f"{key}: expected one pinned form for the anchor")
        source_path, form_hash, archive_name, archive_hash = expected.pop()
        source = entries[0]
        replacement = reconstructed.get((source["wg"], source["cr"]))
        if replacement:
            if (replacement["archive_sha256"], replacement["historical_form_sha256"]) != (archive_hash, form_hash):
                raise ValueError(f"{key}: reconstructed source does not match historical source")
            official_url, selectors = replacement["url"], replacement["member_chain"]
        else:
            official_url = source["url"]
            selectors = [{"name": source["member"], "sha256": source["member_sha256"]}]
        if digest(checkout / source_path) != form_hash or digest(checkout / archive_name) != archive_hash:
            raise ValueError(f"{key}: pinned source or archive bytes differ")
        form = reader.read_form(str(checkout / source_path))
        if form["status"] != "ok" or not form["release"]:
            raise ValueError(f"{key}: source affected field or release unreadable")
        clauses, placeholders = form_labels(reader, form["clauses"])
        if not clauses:
            raise ValueError(f"{key}: no explicit label in source field")
        sections = [reader.SECTION.fullmatch(e["section"]).groupdict() for e in entries]
        if {s["spec"] for s in sections} != {form["header_spec"] or form["file_spec"]}:
            raise ValueError(f"{key}: source and stored-section specifications differ")
        released = {row[-1].lower() for row in item["gold"]}
        projected = {s["clause"].lower() for s in sections}
        if released != projected:
            raise ValueError(f"{key}: pinned sections do not project to gold")
        release_labels = {s["clause"].lower() for s in sections if s["release"] == form["release"]}
        strict[key] = from_labels(item, clauses)
        literal[key] = from_labels(item, clauses | placeholders)
        at_source_release[key] = from_labels(item, release_labels)
        exact_sections = {}
        source_only = clauses - released
        if source_only:
            with sqlite3.connect((sqlite_root / (item["wg"] + ".sqlite")).as_uri() + "?mode=ro",
                                 uri=True) as connection:
                for clause in sorted(source_only):
                    spec = sections[0]["spec"]
                    exact_sections[clause] = [
                        row[0] for row in connection.execute(
                            """SELECT id FROM section WHERE spec = ? AND lower(replace(clause, '.', ''))
                               = replace(?, '.', '') ORDER BY id""",
                            (spec, clause),
                        )
                    ]
        form_report[key] = {
            "source_path": source_path,
            "archive": archive_name,
            "official_pack_url": official_url,
            "official_member_chain": selectors,
            "source_preparation_status": source["preparation_status"],
            "form_sha256": form_hash,
            "archive_sha256": archive_hash,
            "affected_field_sha256": hashlib.sha256(form["clauses"].encode()).hexdigest(),
            "source_form_release": form["release"],
            "source_explicit_labels": sorted(clauses),
            "source_placeholders": sorted(placeholders),
            "stored_projected_labels": sorted(released),
            "source_only_explicit": sorted(source_only),
            "same_spec_stored_ids_allowing_dot_spelling": exact_sections,
            "stored_only": sorted(released - clauses),
            "other_edition_section_ids": sorted(e["section"] for e, s in zip(entries, sections)
                                                if s["release"] != form["release"]),
            "labels_lost_under_form_release_filter": sorted(released - release_labels),
        }

    summary = Counter()
    for form in form_report.values():
        summary.update({
            "source_gold_set_equal": not (form["source_only_explicit"] or form["stored_only"]),
            "source_only_explicit_labels": len(form["source_only_explicit"]),
            "stored_only_labels": len(form["stored_only"]),
            "explicit_source_label_occurrences": len(form["source_explicit_labels"]),
            "gold_label_occurrences": len(form["stored_projected_labels"]),
            "items_with_placeholders": bool(form["source_placeholders"]),
            "source_placeholders": len(form["source_placeholders"]),
            "items_with_other_edition_links": bool(form["other_edition_section_ids"]),
            "other_edition_links": len(form["other_edition_section_ids"]),
            "items_changed_by_form_release_filter": bool(form["labels_lost_under_form_release_filter"]),
            "labels_lost_under_form_release_filter": len(form["labels_lost_under_form_release_filter"]),
        })

    return {
        "items": len(full_chain), "manifest_section_pairs": sum(map(len, by_item.values())),
        "summary": dict(summary),
        "source_manifest_sha256": digest(release / MANIFEST),
        "reconstructed_source_manifest_sha256": digest(release / RECONSTRUCTED_MANIFEST),
        "gold_sha256": {str(path): digest(release / path) for path in GOLD_PATHS},
        "sqlite_sha256": sqlite_pins,
        "scorer_and_reader_sha256": script_hashes,
        "forms": form_report,
        **score(analyzer, release, items, full_chain, strict, literal, at_source_release),
    }


def score(analyzer, release, items, full_chain, strict, literal, at_source_release):
    replays = defaultdict(list)
    saved_response_hashes = {}
    conditions = analyzer.conditions()
    for condition in conditions:
        paths = [release / f"responses/{Path(name).relative_to(Path('logs') / TRACK)}"
                 for name in condition["files"]]
        saved_response_hashes.update({str(path.relative_to(release)): digest(path) for path in paths})
        records, _ = analyzer.load_responses({**condition, "files": paths}, items)
        changed = {}
        actual_scores = {}
        for key, item in items.items():
            rows = records.get(key, {}).get("rows")
            actual_scores[key] = analyzer.exact(item, rows, analyzer.IDENTITY_KEY)
        baseline_main = sum(actual_scores.values())
        baseline_family = sum(actual_scores[key] for key in full_chain)
        for name, alternative in (("explicit_source_labels", strict),
                                  ("literal_placeholders", literal),
                                  ("form_release_only", at_source_release)):
            gained, lost = [], []
            for key in full_chain:
                original = actual_scores[key]
                alternative_exact = analyzer.exact(alternative[key], records.get(key, {}).get("rows"),
                                                   analyzer.IDENTITY_KEY)
                if alternative_exact and not original:
                    gained.append(key)
                if original and not alternative_exact:
                    lost.append(key)
            delta = len(gained) - len(lost)
            changed[name] = {"exact": baseline_family + delta,
                             "all_main_exact": baseline_main + delta,
                             "gains": sorted(gained), "losses": sorted(lost)}
        replays[condition["method"]].append({
            "run": condition["run"], "received": len(set(records) & set(full_chain)),
            "stored_gold_exact": baseline_family, "all_main_stored_gold_exact": baseline_main,
            "alternative": changed,
        })
    return {
        "conditions": len(conditions), "distinct_meeting_alias_exceptions": sorted(analyzer.KEPT),
        "main_items_per_run": len(items), "response_sha256": saved_response_hashes,
        "replays": dict(replays),
    }


def replay(release: Path, receipt: dict) -> dict:
    vendored = release / "code/scripts" / TRACK
    if receipt["scorer_and_reader_sha256"] != {name: digest(vendored / name) for name in MODULES}:
        raise ValueError("Released scorer and reader do not match the source-label receipt")
    if receipt["source_manifest_sha256"] != digest(release / MANIFEST):
        raise ValueError("Source manifest differs from receipt")
    if receipt["reconstructed_source_manifest_sha256"] != digest(release / RECONSTRUCTED_MANIFEST):
        raise ValueError("Reconstructed source manifest differs from receipt")
    if receipt["gold_sha256"] != {str(path): digest(release / path) for path in GOLD_PATHS}:
        raise ValueError("Released benchmark does not match the source-label receipt")
    items, full_chain = load_items(release)
    if set(full_chain) != set(receipt["forms"]):
        raise ValueError("Receipt does not cover the released full-chain IDs")
    strict, literal, at_source_release = {}, {}, {}
    for key, item in full_chain.items():
        form = receipt["forms"][key]
        labels = set(form["source_explicit_labels"])
        strict[key] = from_labels(item, labels)
        literal[key] = from_labels(item, labels | set(form["source_placeholders"]))
        release_labels = {row[-1].lower() for row in item["gold"]}
        at_source_release[key] = from_labels(item, release_labels - set(form["labels_lost_under_form_release_filter"]))

    with tempfile.TemporaryDirectory(prefix="spectra-full-chain-") as work:
        adapter = Path(work)
        (adapter / ".git").mkdir()
        scripts = adapter / "scripts"
        scripts.mkdir()
        for name in MODULES:
            shutil.copyfile(vendored / name, scripts / name)
        sqlite_root = adapter / "logs" / TRACK / "integration/sqlite_final"
        sqlite_root.mkdir(parents=True)
        for name in receipt["sqlite_sha256"]:
            source = release / "sqlite" / name
            target = sqlite_root / name
            if source.exists():
                target.symlink_to(source)
            else:
                with gzip.open(source.with_suffix(".sqlite.gz"), "rb") as inp, target.open("wb") as out:
                    shutil.copyfileobj(inp, out)
        if receipt["sqlite_sha256"] != check_sqlite_pins(sqlite_root, release):
            raise ValueError("Released scoring databases do not match the source-label receipt")
        sys.path.insert(0, str(scripts))
        try:
            analyzer = importlib.import_module("analyze_template_session")
            scores = score(analyzer, release, items, full_chain, strict, literal, at_source_release)
        finally:
            sys.path.pop(0)
    if any(receipt[name] != value for name, value in scores.items()):
        raise ValueError("Replayed saved-response scores differ from the source-label receipt")
    return {"status": "PASS", "items": len(full_chain), **scores}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, default=Path.cwd())
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--label-receipt", type=Path,
                        help="Replay scores from a saved source-label receipt without the CR forms")
    args = parser.parse_args()
    if args.label_receipt:
        receipt = json.loads(args.label_receipt.read_text())
        report = replay(args.release.resolve(), receipt)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(f'{report["status"]}: {report["items"]} frozen label sets, {report["conditions"]} scored conditions')
        return
    report = compare(args.checkout.resolve(), args.release.resolve())
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report["summary"], sort_keys=True))
    for method, runs in report["replays"].items():
        print(method, sum(r["stored_gold_exact"] for r in runs),
              {name: sum(r["alternative"][name]["exact"] for r in runs)
               for name in runs[0]["alternative"]}, len(runs) * report["items"])


if __name__ == "__main__":
    main()
