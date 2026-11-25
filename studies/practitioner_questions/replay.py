#!/usr/bin/env python3
"""Replay the released question analysis and two curated record illustrations.

Uses Python's standard library, a temporary database and read-only SQLite.
Optional private inputs are checked by hash; their text and paths are not emitted.
"""

import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile


HERE = Path(__file__).resolve().parent


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_checksums():
    manifest = HERE / "SHA256SUMS"
    require(manifest.is_file(), "Local SHA256SUMS is required")
    root = HERE.resolve()
    for line in manifest.read_text().splitlines():
        expected, name = line.split("  ", 1)
        require(not Path(name).is_absolute(), "Invalid local manifest entry: " + name)
        path = (root / name).resolve()
        require(path.is_relative_to(root) and path.is_file(),
                "Invalid local manifest entry: " + name)
        require(digest(path) == expected, "Local file checksum mismatch: " + name)


def question_summary(analysis):
    units = analysis["units"]
    require([u["unit_id"] for u in units] == [f"U{i:03d}" for i in range(1, 34)],
            "Question-unit identity/order mismatch")
    require(all(u["question_paraphrase_en"].strip() for u in units), "Missing paraphrase")
    process = [u for u in units if u["first_judgment"]["type"] in ("mixed", "process_trace")]
    followups = sum(u["is_followup"] for u in units)
    union = set().union(*(set(u["first_judgment"]["benchmarkElementsRequired"]) for u in units))
    summary = {
        "units": len(units),
        "cases": len(units) - followups,
        "followups": followups,
        "units_by_type": dict(Counter(u["first_judgment"]["type"] for u in units)),
        "process_or_mixed_units": len(process),
        "first_family_mapping_on_process_or_mixed": dict(Counter(
            u["first_judgment"]["familyMapping"] for u in process)),
        "type_agreement": [sum(u["first_judgment"]["type"] == u["second_judgment"]["type"]
                               for u in units), len(units)],
        "family_mapping_agreement_on_process_or_mixed": [sum(
            u["first_judgment"]["familyMapping"] == u["second_judgment"]["familyMapping"]
            for u in process), len(process)],
        "units_requiring_any_benchmark_element": sum(
            bool(u["first_judgment"]["benchmarkElementsRequired"]) for u in process),
        "units_requiring_only_outside_elements": sum(
            bool(u["first_judgment"]["outsideElementsRequired"])
            and not u["first_judgment"]["benchmarkElementsRequired"] for u in process),
        "benchmark_elements_required_by_any_unit": len(union),
    }
    require(summary == analysis["reported_summary"], "Question summary mismatch")
    disagreements = [{
        "unit_id": u["unit_id"],
        "first_family_mapping": u["first_judgment"]["familyMapping"],
        "second_family_mapping": u["second_judgment"]["familyMapping"],
        "second_nearest_family": u["second_judgment"]["nearestFamily"],
    } for u in process if u["first_judgment"]["familyMapping"] != u["second_judgment"]["familyMapping"]]
    require(disagreements == analysis["preserved_disagreements"], "Disagreement mismatch")
    return summary


def verify_private(args, analysis, hashes, workflow, illustration):
    result = {}
    if args.private_source_root:
        root = args.private_source_root
        for item in hashes["private_source_files"]:
            path = root / item["source_id"]
            require(path.is_file() and digest(path) == item["sha256"],
                    "Private analysis source checksum mismatch")
        first = read_json(root / "practitioner_question_sources.json")
        second = read_json(root / "practitioner_question_second_judge.json")
        second_by_unit = {u["unit"]: u for u in second["secondJudgments"]}
        require(len(first["judgments"]) == len(analysis["units"]), "Private unit count mismatch")
        for original, public in zip(first["judgments"], analysis["units"]):
            require(original["isFollowup"] == public["is_followup"], "Follow-up label mismatch")
            require({k: original.get(k) for k in public["first_judgment"]}
                    == public["first_judgment"], "First judgment mismatch")
            require({k: second_by_unit[original["unit"]].get(k)
                     for k in public["second_judgment"]} == public["second_judgment"],
                    "Second judgment mismatch")
        chain = read_json(root / workflow["source_derivation"])
        require(chain["goldRows"] == workflow["gold_rows"], "Private derived gold mismatch")
        require(chain["rephrasedQuestion"] == workflow["supported_subquery"],
                "Private derived question mismatch")
        require(chain["sql"] == workflow["sql"], "Private derived SQL mismatch")
        result["analysis_files_verified"] = len(hashes["private_source_files"])
        result["recorded_judgments_verified"] = len(analysis["units"])
        if args.private_cases_root:
            count = 0
            for original, projected in zip(first["judgments"], hashes["question_source_files"]):
                require(len(original["questionFiles"]) == len(projected["files"]),
                        "Question source-file count mismatch")
                for name, expected in zip(original["questionFiles"], projected["files"]):
                    path = args.private_cases_root / original["unit"] / name
                    require(path.is_file() and digest(path) == expected["sha256"],
                            "Private question source checksum mismatch")
                    count += 1
            result["question_source_files_verified"] = count
    require(not args.private_cases_root or args.private_source_root,
            "Private case verification also requires --private-source-root")
    if args.private_illustration_source:
        prov = illustration["source_provenance"]
        require(digest(args.private_illustration_source) == prov["original_source_sha256"],
                "Private illustration source checksum mismatch")
        source = read_json(args.private_illustration_source)
        span = source[prov["source_field"]][prov["start"]:prov["end"]]
        require(hashlib.sha256(span.encode("utf-8")).hexdigest() == prov["span_utf8_sha256"],
                "Private illustration source-span mismatch")
        result["posthoc_source_span_verified"] = True
    return result


def markdown_table(fields, rows):
    return "\n".join([
        "| " + " | ".join(fields) + " |",
        "|" + "|".join("---" for _ in fields) + "|",
        *("| " + " | ".join(str(value) for value in row) + " |" for row in rows),
    ])


def readme_examples(workflow, illustration, binding, rowsets, context_rows, record_rows, refresh):
    """Render README record examples from the rowsets just executed and checked."""
    example_rows = [row for row in rowsets["cr_side"] if row[0] == "R4-2115103"]
    require(len(example_rows) == 1, "README clause-history example is not unique")
    context = [row for row in context_rows if row == workflow["context_row"]["row"]]
    require(len(context) == 1, "README context example is not unique")
    discrepancy = [row for row in rowsets["cr_side"] if row == binding["row"]]
    require(len(discrepancy) == 1, "README source-discrepancy example is not unique")
    expected = {
        "clause_history": markdown_table(workflow["gold_fields"], example_rows),
        "rel16_context": markdown_table(workflow["gold_fields"], context),
        "source_discrepancy": markdown_table(workflow["gold_fields"], discrepancy),
        "coordination": markdown_table(illustration["fields"][:6], [row[:6] for row in record_rows]),
    }
    readme = HERE / "README.md"
    text = readme.read_text(encoding="utf-8")
    for name, table in expected.items():
        start = "<!-- BEGIN REPLAY:" + name + " -->"
        end = "<!-- END REPLAY:" + name + " -->"
        require(text.count(start) == text.count(end) == 1, "README example markers mismatch: " + name)
        before, remainder = text.split(start, 1)
        current, after = remainder.split(end, 1)
        if refresh:
            text = before + start + "\n" + table + "\n" + end + after
        else:
            require(current == "\n" + table + "\n", "README example row mismatch: " + name)
    if refresh:
        readme.write_text(text, encoding="utf-8")
    return {"tables": len(expected), "rows": sum((len(example_rows), len(context),
            len(discrepancy), len(record_rows))), "matches_executed_rowsets": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, help="Override released RAN4.sqlite or .sqlite.gz")
    parser.add_argument("--out", type=Path, help="Write JSON report in addition to stdout")
    parser.add_argument("--private-source-root", type=Path)
    parser.add_argument("--private-cases-root", type=Path)
    parser.add_argument("--private-illustration-source", type=Path)
    parser.add_argument("--refresh-readme-examples", action="store_true",
                        help="Regenerate marked README tables from verified query rows; then refresh checksums")
    args = parser.parse_args()
    require(not args.out or args.out.resolve().parent != HERE,
            "Write replay reports outside this immutable package folder")
    require(not args.refresh_readme_examples or not args.out,
            "README regeneration and writing a replay receipt are separate operations")
    verify_checksums()
    analysis = read_json(HERE / "question_analysis.json")
    workflow = read_json(HERE / "workflow_example.json")
    illustration = read_json(HERE / "posthoc_record_illustration.json")
    binding = read_json(HERE / "row_source_binding.json")
    hashes = read_json(HERE / "source_hashes.json")
    require(binding["row"] in workflow["gold_rows"], "Retained source discrepancy row mismatch")
    summary = question_summary(analysis)
    private = verify_private(args, analysis, hashes, workflow, illustration)
    database = args.database or (HERE / workflow["database"]["path"]).resolve()
    expected_db_sha = workflow["database"]["uncompressed_sha256"]
    with tempfile.TemporaryDirectory(prefix="practitioner-question-replay-") as temp:
        if database.suffix == ".gz":
            require(digest(database) == workflow["database"]["compressed_sha256"],
                    "Compressed database checksum mismatch")
            db = Path(temp) / "RAN4.sqlite"
            with gzip.open(database, "rb") as source, db.open("wb") as target:
                shutil.copyfileobj(source, target)
        else:
            db = database.resolve()
        require(digest(db) == expected_db_sha, "Database checksum mismatch")
        connection = sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)
        connection.execute("PRAGMA query_only = ON")
        anchor = {"anchor": workflow["supported_subquery"]["anchor"]}
        rowsets = {k: sorted([list(row) for row in connection.execute(sql, anchor)])
                   for k, sql in workflow["sql"].items()}
        require(all(rows == sorted(workflow["gold_rows"]) for rows in rowsets.values()),
                "Derived clause-history rowset mismatch")
        context_rows = [list(row) for row in connection.execute(
            workflow["sql"]["cr_side"], {"anchor": workflow["context_row"]["anchor"]})]
        require(workflow["context_row"]["row"] in context_rows, "Rel-16 context row mismatch")
        record_rows = [list(row) for row in connection.execute(
            illustration["sql"], illustration["parameters"])]
        require(record_rows == illustration["returned_rows"], "Post-hoc record row mismatch")
        readme = readme_examples(workflow, illustration, binding, rowsets, context_rows,
                                record_rows, args.refresh_readme_examples)
        connection.close()
    if args.refresh_readme_examples:
        print(json.dumps({"status": "README_UPDATED", "readme_examples": readme,
                          "next_step": "Refresh local checksums, then run the read-only public replay."},
                         indent=2))
        return
    report = {
        "status": "PASS",
        "question_analysis": summary,
        "database_sha256": expected_db_sha,
        "derived_clause_history": {
            "rows_per_sql_formulation": {k: len(v) for k, v in rowsets.items()},
            "matches_existing_derived_gold": True,
            "rel16_context_row_present": True,
        },
        "separate_posthoc_record_illustration": {
            "rows": len(record_rows), "matches_stored_source_bound_row": True,
        },
        "readme_examples": readme,
        "scope": "Offline aggregation and read-only record queries; existing labels and curated illustrations",
    }
    if private:
        report["private_verification"] = private
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
    print(output, end="")


if __name__ == "__main__":
    main()
