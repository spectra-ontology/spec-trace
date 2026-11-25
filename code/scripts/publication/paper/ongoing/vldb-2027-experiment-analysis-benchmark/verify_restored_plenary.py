"""Compare restored plenary rows and the original raw-text search interface."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import sqlite3
import sys
import time

import search_raw_text


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode() + b"\n"


def stat(path):
    value = path.stat()
    return {"bytes": value.st_size, "mtime_ns": value.st_mtime_ns, "inode": value.st_ino}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--original", type=Path, required=True)
    ap.add_argument("--restored", type=Path, required=True)
    ap.add_argument("--items", type=Path, nargs="+", required=True)
    ap.add_argument("--owner-limit", type=int, default=100,
                    help="Evenly spaced indexed-owner filters; 0 checks every owner")
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()
    started = time.monotonic()
    paths = [args.original.resolve(), args.restored.resolve()]
    before = [stat(path) for path in paths]
    cons = [sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) for path in paths]
    report = {"tables": {}, "queries": [], "python": sys.version,
              "sqlite_version": sqlite3.sqlite_version,
              "verifier_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    schemas = [con.execute("SELECT type,name,sql FROM sqlite_master WHERE sql IS NOT NULL "
                           "AND name NOT LIKE 'search_%' ORDER BY type,name").fetchall() for con in cons]
    if schemas[0] != schemas[1]:
        raise ValueError("Logical schemas differ")
    report["schema_sha256"] = hashlib.sha256(encode(schemas[0])).hexdigest()
    for table, order in (("files", "id"), ("members", "id"), ("chunks", "id"),
                         ("inodes", "inode"), ("owners", "own,file_id"),
                         ("member_owner", "own,member_id"), ("build_info", "name")):
        digest = hashlib.sha256()
        count = 0
        cursors = [con.execute(f'SELECT * FROM "{table}" ORDER BY {order}') for con in cons]
        for left, right in itertools.zip_longest(*cursors):
            if left != right:
                raise ValueError(f"Logical row differs: {table}, ordinal={count}")
            digest.update(encode(left))
            count += 1
        report["tables"][table] = {"rows": count, "logical_sha256": digest.hexdigest()}
        print(json.dumps({"verified_table": table, "rows": count}), flush=True)
    items = [json.loads(line) for path in args.items for line in path.read_text().splitlines() if line]
    if not items or len({item["id"] for item in items}) != len(items):
        raise ValueError("Expected nonempty items with unique IDs")
    cases = [(item["id"], search_raw_text.query_expression(item["question"]), None) for item in items]
    if args.owner_limit < 0:
        raise ValueError("Owner limit must be nonnegative")
    owners = [row[0] for row in cons[0].execute(
        "SELECT own FROM owners UNION SELECT own FROM member_owner ORDER BY own")]
    selected_owners = owners
    if 0 < args.owner_limit < len(owners):
        selected_owners = [owners[index * (len(owners) - 1) // max(1, args.owner_limit - 1)]
                           for index in range(args.owner_limit)]
    cases += [("owner:" + owner, "", owner) for owner in selected_owners]
    for identity, expression, doc in cases:
        if not expression and doc is None:
            raise ValueError("Question has no searchable expression: " + identity)
        found = []
        for path in paths:
            search_raw_text.PLENARY = path
            found.append(search_raw_text.search_plenary(expression, doc, 10))
        if found[0] != found[1]:
            raise ValueError("Raw-text search differs: " + identity)
        report["queries"].append({"id": identity, "document_filter": doc,
                                  "rows": len(found[0]), "result_sha256": hashlib.sha256(encode(found[0])).hexdigest()})
        if len(report["queries"]) % 100 == 0:
            print(json.dumps({"queries_verified": len(report["queries"])}), flush=True)
    report["quick_check"] = [con.execute("PRAGMA quick_check").fetchall() for con in cons]
    if report["quick_check"] != [[("ok",)], [("ok",)]]:
        raise ValueError("SQLite integrity check failed")
    for con in cons:
        con.close()
    report["unchanged_stat"] = [stat(path) for path in paths] == before
    if not report["unchanged_stat"]:
        raise ValueError("An input changed during verification")
    report.update(benchmark_questions=len(items), owner_filters=len(cases) - len(items),
                  indexed_owners=len(owners), owner_selection="All owners" if selected_owners == owners
                  else "Evenly spaced positions in the sorted distinct indexed-owner list",
                  query_count=len(cases), all_logical_rows_equal=True, all_query_results_equal=True,
                  seconds=time.monotonic() - started,
                  scope="All logical rows, every supplied question and the reported owner-filter selection through the original raw-text plenary search interface.")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_bytes(encode(report))
    print(json.dumps({key: report[key] for key in ("benchmark_questions", "owner_filters", "query_count",
                                                 "all_logical_rows_equal", "all_query_results_equal", "seconds")}))


if __name__ == "__main__":
    main()
