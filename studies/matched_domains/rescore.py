#!/usr/bin/env python3
"""Verify frozen study bindings and rescore stored rows using the standard library.

An optional SQLite replay runs the original SQL submissions against hash-matched
exports in read-only connections. The default action needs only this directory.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys
import time

RUNS = ("sql_A", "cypher_A", "cypher_B", "sql_B")
HERE = Path(__file__).resolve().parent
E_BEFORE_BIS = re.compile(r"(#\d+)-e-b(?:is)?(?![a-z0-9])")
BIS_MARK = re.compile(r"(#\d+)-?b(?:is)?(?![a-z0-9])")


class VerificationError(ValueError):
    pass


def require(condition, code, detail):
    if not condition:
        raise VerificationError(f"{code}: {detail}")


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sha_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def packet_id(item):
    return item["wg"] + "-q" + sha_text("packet:" + item["id"])[:12]


def unique_by(rows, key, code):
    mapped = {row[key]: row for row in rows}
    require(len(mapped) == len(rows), code, f"duplicate {key}")
    return mapped


def verify_hashes(study):
    manifest = load(study / "provenance_manifest.json")
    seen = set()
    for record in manifest["sourceFiles"]:
        name = record["path"]
        path = (study / name).resolve()
        require(path.is_relative_to(study.resolve()), "source_path", name)
        require(name not in seen, "source_path", f"duplicate {name}")
        seen.add(name)
        require(path.is_file(), "source_missing", name)
        require(path.stat().st_size == record["bytes"] and digest(path) == record["sha256"],
                "source_hash", name)
    checksum_file = study / "SHA256SUMS"
    checksums = 0
    if checksum_file.exists():
        for line in checksum_file.read_text(encoding="utf-8").splitlines():
            expected, name = line.split("  ", 1)
            path = (study / name).resolve()
            require(path.is_relative_to(study.resolve()), "checksum_path", name)
            require(path.is_file() and digest(path) == expected, "package_hash", name)
            checksums += 1
    return manifest, len(seen), checksums


def cell_key(cell):
    lowered = "" if cell is None else str(cell).strip().lower()
    return BIS_MARK.sub(r"\1bis", E_BEFORE_BIS.sub(r"\1bis-e", lowered))


def score(gold, rows):
    wanted = {tuple(cell_key(cell) for cell in row) for row in gold}
    if rows is None:
        return {"exact": 0, "precision": 0.0, "recall": 0.0, "f1": 0.0, "unreadable": 1}
    given = {tuple(cell_key(cell) for cell in row) for row in rows}
    if not wanted and not given:
        return {"exact": 1, "precision": 1.0, "recall": 1.0, "f1": 1.0, "unreadable": 0}
    hits = len(wanted & given)
    precision = hits / len(given) if given else 0.0
    recall = hits / len(wanted) if wanted else 0.0
    return {"exact": int(wanted == given), "precision": precision, "recall": recall,
            "f1": 2 * precision * recall / (precision + recall) if hits else 0.0, "unreadable": 0}


def identity_rows(item, rows, kept):
    if rows is None:
        return None
    out = []
    for row in rows:
        values = []
        for index, cell in enumerate(row):
            value = cell_key(cell)
            if item["fields"][index] in {"wg_meeting", "tsg_meeting"} and value not in kept:
                value = re.sub(r"-e$", "", value)
            values.append(value)
        out.append(values)
    return out


def summarize(scores):
    n = len(scores)
    require(n > 0, "summary_empty", "empty group")
    return {"n": n, "exact": sum(s["exact"] for s in scores),
            **{name: round(sum(s[name] for s in scores) / n, 4)
               for name in ("precision", "recall", "f1")},
            "unreadable": sum(s["unreadable"] for s in scores)}


def raw_set(rows):
    return {tuple(row) for row in rows}


def load_data(study):
    return {
        "gold": load(study / "gold/selected_items.json"),
        "queries": {run: jsonl(study / f"queries/{run}.jsonl") for run in RUNS},
        "queryCopies": {run: load(study / f"execution/queries/{run}.json") for run in RUNS},
        "executions": {run: load(study / f"execution/{run}.json") for run in RUNS},
        "summary": load(study / "execution/summary.json"),
        "metadata": load(study / "execution/generation_metadata.json"),
    }


def verify_design(study, manifest, data):
    protocol = load(study / "frozen/protocol.json")
    codex_protocol = load(study / "provenance/protocol.json")
    pin = load(study / "provenance/execution_pin.json")
    require(digest(study / "evidence/execution_source.py.snapshot") == pin["scorerSha256"],
            "execution_pin", "original execution source")
    require(digest(study / "provenance/protocol.json") == pin["protocolSha256"],
            "execution_pin", "Codex protocol")
    for name, expected in codex_protocol["inputs"].items():
        require(digest(study / "frozen" / name) == expected, "protocol_input", name)
    require(load(study / "provenance/generation_metadata_input.json") == data["metadata"],
            "generation_metadata", "input differs from execution copy")
    gold_by_id = unique_by(data["gold"], "id", "gold_identity")
    require(len(gold_by_id) == 50, "gold_count", "expected 50 fixed strata")
    require(collections.Counter(i["suite"] for i in data["gold"]) == {"main": 35, "extension": 15},
            "suite_counts", "expected 35 main and 15 extension")
    cells = collections.defaultdict(list)
    for source in manifest["selectionSources"]:
        path = study / source["path"]
        require(digest(path) == protocol["sourceFiles"][source["protocolSourcePath"]],
                "selection_source_pin", source["path"])
        for item in jsonl(path):
            cells[(source["suite"], item["wg"], item["family"])].append(item)
    require(sum(map(len, cells.values())) == 967 and len(cells) == 50,
            "selection_pool", "expected 667 main and 300 drawn extension candidates")
    require(sum(len(v) for k, v in cells.items() if k[0] == "main") == 667,
            "selection_pool", "main candidate count")
    selections = load(study / "frozen/selection.json")
    require(len(selections) == 50, "selection_count", "expected 50 cells")
    seen_cells = set()
    for entry in selections:
        key = (entry["suite"], entry["wg"], entry["family"])
        require(key not in seen_cells and key in cells, "selection_cell", str(key))
        seen_cells.add(key)
        candidates = cells[key]
        selected = min(candidates, key=lambda i: (sha_text(i["anchor"]), i["id"]))
        require(entry["eligible"] == len(candidates) and entry["selectedId"] == selected["id"]
                and entry["anchorSha256"] == sha_text(selected["anchor"])
                and entry["packetId"] == packet_id(selected), "selection_minimum", str(key))
        require(gold_by_id.get(selected["id"]) == dict(selected, suite=entry["suite"]),
                "selection_gold", selected["id"])
    admitted = {}
    for name in manifest["admittedExtensionFiles"]:
        for item in jsonl(study / name):
            require(item["id"] not in admitted, "admission_identity", item["id"])
            admitted[item["id"]] = item
    require(len(admitted) == 297, "admission_count", "expected 297 admitted extension items")
    for item in data["gold"]:
        if item["suite"] == "extension":
            require(admitted.get(item["id"]) == {k: v for k, v in item.items() if k != "suite"},
                    "selected_admission", item["id"])
        require(bool(item["expectsEmpty"]) == (not item["gold"]), "empty_contract", item["id"])
    by_packet = {packet_id(item): item for item in data["gold"]}
    require(len(by_packet) == 50, "packet_collision", "packet IDs must be unique")
    domains = load(study / "frozen/categorical_domains.json")
    packet_views = {}
    for language in ("sql", "cypher"):
        path = study / f"frozen/writer_{language}.txt"
        require(digest(path) == protocol["writerInputs"][language], "writer_pin", language)
        groups = json.loads(path.read_text(encoding="utf-8").split("\n\n", 1)[1])
        require([g["wg"] for g in groups] == [f"RAN{n}" for n in range(1, 6)],
                "writer_groups", language)
        packet_views[language] = []
        for group in groups:
            require(group["categorical_domains"] == domains[group["wg"]], "writer_domains", group["wg"])
            expected = [{"id": packet_id(item), "question": item["question"], "fields": item["fields"]}
                        for item in data["gold"] if item["wg"] == group["wg"]]
            require(group["items"] == expected, "writer_questions", group["wg"])
            packet_views[language].append((group["items"], group["categorical_domains"]))
    require(packet_views["sql"] == packet_views["cypher"], "writer_parity", "question/domain views")
    for run in RUNS:
        query_hash = digest(study / f"queries/{run}.jsonl")
        receipt = load(study / f"provenance/{run}.json")
        metadata = data["metadata"][run]
        require(query_hash == pin["query_files"][run] == receipt["outputSha256"] == metadata["querySha256"],
                "query_pin", run)
        require(receipt["outputFile"] == f"{run}.jsonl" and receipt["items"] == 50
                and receipt["firstSubmission"] is True, "writer_receipt", run)
        require(receipt["actualModelId"] is None and metadata["actualModels"] == []
                and metadata["modelIdentityStatus"] == "unavailable", "model_provenance", run)
    return by_packet, {"selectionCandidates": 967, "mainCandidates": 667, "drawnExtensionCandidates": 300,
                       "admittedExtensionPopulation": 297, "selectedAdmittedExtension": 15,
                       "strata": 50, "mainStrata": 35, "extensionStrata": 15,
                       "writerQuestionAndDomainParity": True}


def verify_executions(data, by_packet, kept):
    summaries, strict = {}, {}
    for run in RUNS:
        queries = data["queries"][run]
        by_query = unique_by(queries, "id", "query_identity")
        require(len(queries) == 50 and set(by_query) == set(by_packet), "query_packet_coverage", run)
        require(data["queryCopies"][run] == queries, "query_serialization", run)
        executed = data["executions"][run]
        by_execution = unique_by(executed, "packetId", "executed_packet_identity")
        require(len(executed) == 50 and set(by_execution) == set(by_packet), "executed_packet_coverage", run)
        require([r["packetId"] for r in executed] == [q["id"] for q in queries], "executed_order", run)
        strict[run] = 0
        for row in executed:
            item = by_packet[row["packetId"]]
            require(all(row[key] == item[key] for key in ("id", "wg", "family", "suite"))
                    and row["query"] == by_query[row["packetId"]]["query"], "executed_packet_binding", run)
            require(row["error"] is None and row["blocked"] is False and isinstance(row["rows"], list),
                    "execution_status", run + ":" + row["packetId"])
            require(all(isinstance(r, list) and len(r) == len(item["fields"]) for r in row["rows"]),
                    "row_shape", row["packetId"])
            computed = score(item["gold"], row["rows"])
            computed_identity = score(identity_rows(item, item["gold"], kept), identity_rows(item, row["rows"], kept))
            require(computed == row["scores"], "stored_score_disagrees", run + ":" + row["packetId"])
            require(computed_identity == row["identityScores"], "identity_score_disagrees", run + ":" + row["packetId"])
            strict[run] += int(raw_set(item["gold"]) == raw_set(row["rows"]))
        summaries[run] = {suite: summarize([r["scores"] for r in executed if suite == "all" or r["suite"] == suite])
                          for suite in ("all", "main", "extension")}
        summaries[run]["blocked"] = sum(r["blocked"] for r in executed)
        summaries[run]["identity"] = {
            suite: summarize([r["identityScores"] for r in executed if suite == "all" or r["suite"] == suite])
            for suite in ("all", "main", "extension")}
    return summaries, strict


def replay_sql(study, sqlite_dir, data, by_packet):
    require(sqlite3.sqlite_version == "3.37.2", "sqlite_version", sqlite3.sqlite_version)
    protocol = load(study / "frozen/protocol.json")
    connections, before, details = {}, {}, []
    try:
        for wg in [f"RAN{n}" for n in range(1, 6)]:
            path = (sqlite_dir / f"{wg}.sqlite").resolve()
            require(path.is_file(), "sqlite_missing", path.name)
            before[wg] = digest(path)
            require(before[wg] == protocol["databases"][wg]["sqliteSha256"], "sqlite_hash", wg)
            db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
            db.execute("PRAGMA query_only=ON")
            require(db.execute("PRAGMA query_only").fetchone()[0] == 1, "sqlite_query_only", wg)
            connections[wg] = db
        for run in ("sql_A", "sql_B"):
            executed = {r["packetId"]: r for r in data["executions"][run]}
            for query in data["queries"][run]:
                item = by_packet[query["id"]]
                require(re.match(r"\s*(SELECT|WITH)\b", query["query"], re.I), "sql_read_only", query["id"])
                db = connections[item["wg"]]
                start = time.monotonic()
                db.set_progress_handler(lambda: int(time.monotonic() - start > 60), 10000)
                try:
                    cursor = db.execute(query["query"])
                    require(len(cursor.description) == len(item["fields"]), "sql_field_count", query["id"])
                    rows = [[None if c is None else str(c) for c in row] for row in cursor.fetchmany(2001)]
                finally:
                    db.set_progress_handler(None, 0)
                require(len(rows) <= 2000, "sql_row_cap", query["id"])
                require(raw_set(rows) == raw_set(executed[query["id"]]["rows"]), "sql_stored_rowset", query["id"])
                require(score(item["gold"], rows) == executed[query["id"]]["scores"], "sql_gold_score", query["id"])
                details.append({"run": run, "packetId": query["id"], "rows": len(rows),
                                "rawStoredRowsetEqual": True, "exact": score(item["gold"], rows)["exact"]})
    finally:
        for db in connections.values():
            db.close()
    after = {wg: digest(sqlite_dir / f"{wg}.sqlite") for wg in before}
    require(before == after, "sqlite_changed", "input exports changed")
    return {"sqliteVersion": sqlite3.sqlite_version, "queryOnly": True, "queriesReexecuted": len(details),
            "rawStoredRowsetsEqual": sum(d["rawStoredRowsetEqual"] for d in details),
            "exact": sum(d["exact"] for d in details), "databaseHashes": before,
            "databaseHashesUnchanged": True, "items": details}


def verify(study, sqlite_dir=None):
    manifest, count, checksums = verify_hashes(study)
    data = load_data(study)
    by_packet, design = verify_design(study, manifest, data)
    identity_path = study / "evidence/meeting_identity_source.json"
    kept = set(load(identity_path)["rules"]["keptElectronicSpellings"])
    summaries, strict = verify_executions(data, by_packet, kept)
    recomputed = {"sameActualModelAcrossAllSessions": None, "modelIdentityComplete": False,
                  "identityRulesSourceSha256": digest(identity_path), "keptElectronicSpellings": sorted(kept),
                  "actualModels": [], "runs": summaries}
    require(recomputed == data["summary"], "summary_disagrees", "complete original summary")
    report = {"status": "pass", "copiedSourceFilesVerified": count, "packageChecksumsVerified": checksums,
              "design": design, "queryPacketGoldRowBindingsVerified": 200,
              "strictRawRowsetExact": strict, "storedRowsetsRescored": 200,
              "summaryEqualsOriginal": True, "recomputedSummary": recomputed,
              "liveSql": {"status": "not_requested"},
              "scope": "50 fixed strata, four first submissions per stratum; descriptive diagnostic"}
    if sqlite_dir is not None:
        report["liveSql"] = {"status": "pass", **replay_sql(study, sqlite_dir, data, by_packet)}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-dir", type=Path, default=HERE)
    parser.add_argument("--sqlite-dir", type=Path, help="Optional directory containing the five frozen RAN*.sqlite exports")
    parser.add_argument("--out", type=Path, help="Write a receipt; stdout always contains the compact result")
    args = parser.parse_args()
    try:
        report = verify(args.study_dir, args.sqlite_dir)
    except (VerificationError, OSError, ValueError, KeyError, sqlite3.Error) as exc:
        report = {"status": "fail", "error": str(exc)}
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in {"recomputedSummary", "liveSql"}}, ensure_ascii=False))
    if report["status"] != "pass":
        return 1
    if args.sqlite_dir:
        print(json.dumps({"liveSql": {k: v for k, v in report["liveSql"].items() if k != "items"}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
