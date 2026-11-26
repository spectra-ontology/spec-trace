#!/usr/bin/env python3
"""Replay the released disposition scopes, SQLite projection, and gold uses."""

import argparse
from collections import Counter
from contextlib import closing
import gzip
import json
from pathlib import Path
import shutil
import sqlite3
from tempfile import TemporaryDirectory


SCOPES = ("whole_target", "subdocument", "undetermined")


def packaged_file(path):
    return path if path.is_file() else path.with_suffix(path.suffix + ".gz")


def load_graph(path):
    path = packaged_file(path)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)["@graph"]


def scope_projection(release, group):
    files = release / "records" / "phase-2" / group
    event_ids = set()
    for event in load_graph(files / "resolutions_document_dispositions.jsonld"):
        if event["resolutionScope"] != "document_disposition":
            raise ValueError(f"{group}: unexpected marker on {event['@id']}")
        event_ids.add(event["@id"])

    projected, counts, marked_counts = {}, Counter(), Counter()
    for record in load_graph(files / "decision_dispositions.jsonld"):
        record_id = record["@id"]
        scope = json.loads(record["assessmentMethod"])["scope"]
        if record_id in projected or scope not in SCOPES:
            raise ValueError(f"{group}: duplicate disposition or unknown scope on {record_id}")
        projected[record_id] = (record["dispositionOf"], scope, record["evidenceStatus"])
        counts[scope] += 1
        if record["dispositionOf"] in event_ids:
            marked_counts[scope] += 1

    sqlite_path = packaged_file(release / "sqlite" / f"{group}.sqlite")
    with TemporaryDirectory(prefix="spectra-scope-") as temporary:
        if sqlite_path.suffix == ".gz":
            unpacked = Path(temporary) / f"{group}.sqlite"
            with gzip.open(sqlite_path, "rb") as source, unpacked.open("wb") as target:
                shutil.copyfileobj(source, target)
            sqlite_path = unpacked
        with closing(sqlite3.connect(f"{sqlite_path.resolve().as_uri()}?mode=ro", uri=True)) as db:
            sql_rows = db.execute("SELECT id, resolution_id, scope, evidence_status FROM disposition")
            relational = {row_id: (resolution, scope, status) for row_id, resolution, scope, status in sql_rows}

    missing = projected.keys() - relational.keys()
    extra = relational.keys() - projected.keys()
    mismatch = sum(projected[key] != relational[key] for key in projected.keys() & relational.keys())
    if missing or extra or mismatch:
        raise ValueError(f"{group}: {len(missing)} missing, {len(extra)} extra, {mismatch} differing SQLite rows")
    return {
        "matchedRows": len(projected),
        "scopeCounts": {scope: counts[scope] for scope in SCOPES},
        "documentDispositionEvents": len(event_ids),
        "scopeCountsLinkedToDocumentDisposition": {scope: marked_counts[scope] for scope in SCOPES},
    }


def reading_and_gold(release):
    study = release / "studies" / "disposition_reading"
    keys = json.loads((study / "keys.json").read_text(encoding="utf-8"))
    sample = [row for row in keys.values() if "random_verified" in row["sets"]]
    scope_counts = Counter(row["scope"] for row in sample)
    code_counts = Counter(row["code"] for row in sample)
    cases = json.loads((study / "followups.json").read_text(encoding="utf-8"))["cases"]
    items, uses = 0, Counter()
    for partition in ("core", "ran5"):
        path = release / "benchmark" / "items_final" / "gate" / partition / "chain_items_admitted.jsonl"
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                row = json.loads(line)
                items += 1
                uses.update(evidence["dispositionId"] for evidence in row["evidence"] if "dispositionId" in evidence)
    return {
        "randomVerifiedScopeCounts": {scope: scope_counts[scope] for scope in SCOPES},
        "randomVerifiedCodeCounts": dict(sorted(code_counts.items())),
        "mainItems": items,
        "mainDispositionEvidenceUses": sum(uses.values()),
        "jointContradictionMainUses": {
            case["dispositionId"]: uses[case["dispositionId"]] for case in cases
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, default=Path("."))
    args = parser.parse_args()
    working_groups = {group: scope_projection(args.release, group) for group in ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5")}
    print(json.dumps({"byWorkingGroup": working_groups, "readingAndGold": reading_and_gold(args.release)}, indent=2))


if __name__ == "__main__":
    main()
