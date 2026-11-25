"""Compare a restored WG index with the immutable experimental index."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import sqlite3
import sys
import time
from pathlib import Path

import search_records_text


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode() + b"\n"


def readonly(path):
    con = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    con.execute("PRAGMA cache_size=-65536")
    return con


def fingerprint(path):
    s = path.stat()
    return {"bytes": s.st_size, "mtime_ns": s.st_mtime_ns, "inode": s.st_ino}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", required=True, type=Path)
    parser.add_argument("--restored", required=True, type=Path)
    parser.add_argument("--wg", required=True, choices=search_records_text.WGS)
    parser.add_argument("--items", required=True, type=Path, nargs="+")
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    started = time.monotonic()
    before = [fingerprint(p) for p in (args.original, args.restored)]
    cons = [readonly(p) for p in (args.original, args.restored)]
    report = {"wg": args.wg, "python": sys.version, "executable": sys.executable,
              "sqlite_version": sqlite3.sqlite_version, "tables": {}, "queries": [],
              "verifier_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "original": str(args.original), "restored": str(args.restored)}
    schemas = [c.execute("SELECT type,name,sql FROM sqlite_master WHERE sql IS NOT NULL "
                         "AND name NOT LIKE 'search_%' ORDER BY type,name").fetchall() for c in cons]
    if schemas[0] != schemas[1]:
        raise ValueError("Logical schemas differ")
    report["schema_sha256"] = hashlib.sha256(encoded(schemas[0])).hexdigest()
    for table, order in (("docs", "id"), ("cr_clause", "spec,clause,id"),
                         ("manifest", "collection"), ("build_info", "name")):
        cursors = [c.execute(f'SELECT * FROM "{table}" ORDER BY {order}') for c in cons]
        count, digest = 0, hashlib.sha256()
        for left, right in itertools.zip_longest(*cursors):
            if left != right:
                raise ValueError(f"Logical row differs: table={table}, ordinal={count}")
            digest.update(encoded(left))
            count += 1
        report["tables"][table] = {"rows": count, "logical_sha256": digest.hexdigest()}
        print(json.dumps({"verified_table": table, "rows": count}), flush=True)
    items = [json.loads(line) for path in args.items for line in path.read_text().splitlines() if line]
    selected = [item for item in items if item["wg"] == args.wg]
    if not selected or len({i["id"] for i in selected}) != len(selected):
        raise ValueError("Expected nonempty benchmark items with unique IDs")
    for item in selected:
        for text_only in (False, True):
            results = []
            for con in cons:
                search_records_text.connect_index = lambda _wg, con=con: con
                results.append(search_records_text.search(args.wg, item["question"], None, 12,
                                                           None, False, text_only))
            if results[0] != results[1]:
                raise ValueError(f"Search differs: item={item['id']}, text_only={text_only}")
            report["queries"].append({"item_id": item["id"], "text_only": text_only,
                                      "rows": len(results[0]),
                                      "result_sha256": hashlib.sha256(encoded(results[0])).hexdigest()})
            if len(report["queries"]) % 20 == 0:
                print(json.dumps({"wg": args.wg, "queries_verified": len(report["queries"])}), flush=True)
    report["quick_check"] = [c.execute("PRAGMA quick_check").fetchall() for c in cons]
    if report["quick_check"] != [[("ok",)], [("ok",)]]:
        raise ValueError("SQLite quick_check failed")
    for con in cons:
        con.close()
    report["unchanged_stat"] = [fingerprint(p) for p in (args.original, args.restored)] == before
    if not report["unchanged_stat"]:
        raise ValueError("An input database changed during verification")
    report.update(benchmark_items=len(selected), query_count=len(report["queries"]),
                  all_logical_rows_equal=True, all_query_results_equal=True,
                  seconds=time.monotonic() - started,
                  scope="Logical tables and original BM25 search over every supplied WG benchmark question; source acquisition is recorded separately.")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_bytes(encoded(report))
    print(json.dumps({k: report[k] for k in ("benchmark_items", "query_count", "all_logical_rows_equal",
                                            "all_query_results_equal", "seconds")}))


if __name__ == "__main__":
    main()
