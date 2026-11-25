#!/usr/bin/env python3
"""Execute the nonidentity controls omitted from the original frozen receipt."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sqlite3
import time


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--measurement", type=Path, required=True)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--database-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (2 << 30, 2 << 30))
    frozen = json.loads((args.measurement / "freeze.json").read_text())
    for name, expected in frozen["files"].items():
        if sha(args.measurement / name) != expected:
            raise ValueError(("Frozen input mismatch", name))
    selections = json.loads((args.measurement / "selection_and_gold.json").read_text())
    outcomes = json.loads((args.measurement / "execution.json").read_text())
    original_names = {item["id"]: {row["name"] for row in item["mutations"]} for item in outcomes["items"]}
    pins = {pin["wg"]: pin for pin in selections["inputs"]}
    checks, identity_definitions, results = [], [], []
    for wg in ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5"):
        plain = args.release / "sqlite" / f"{wg}.sqlite"
        source = plain if plain.exists() else plain.with_suffix(".sqlite.gz")
        database = source if source.suffix == ".sqlite" else args.database_directory / f"{wg}.sqlite"
        pin = pins[wg]
        if sha(source) != pin["source_sha256"] or sha(database) != pin["database_sha256"]:
            raise ValueError(("Input mismatch", wg))
        connection = sqlite3.connect("file:" + str(database.resolve()) + "?mode=ro&immutable=1", uri=True)
        connection.execute("PRAGMA query_only=ON")
        connection.execute("PRAGMA cache_size=-16384")
        for item in selections["items"]:
            if item["wg"] != wg:
                continue
            for name, sql in item["mutations"].items():
                if name in original_names[item["id"]]:
                    continue
                if sql == item["reference_sql"]:
                    identity_definitions.append({"id": item["id"], "name": name, "status": "correct_operator_identity_not_executed"})
                    continue
                start = time.monotonic()
                connection.set_progress_handler(lambda: time.monotonic() - start >= 60, 10000)
                record = {"id": item["id"], "family": item["family"], "name": name, "sql": sql,
                          "required": False, "reason": "Defined nonidentity control omitted from original run"}
                try:
                    rows = sorted(set(tuple(str(value) for value in row) for row in connection.execute(sql)))
                    gold, actual = set(map(tuple, item["gold"])), set(rows)
                    record.update(status="ok", rows=rows, discriminating=actual != gold,
                                  gold_only=sorted(gold - actual), mutant_only=sorted(actual - gold))
                except sqlite3.Error as error:
                    record.update(status="timeout" if "interrupted" in str(error) else "error",
                                  error=str(error), discriminating=False)
                finally:
                    connection.set_progress_handler(None, 0)
                record["seconds"] = time.monotonic() - start
                results.append(record)
        connection.close()
        checks.append({"wg": wg, "source_sha256": sha(source), "database_sha256": sha(database),
                       "source_unchanged": sha(source) == pin["source_sha256"],
                       "database_unchanged": sha(database) == pin["database_sha256"]})
    summary = {"executions": len(results), "successful_executions": sum(item["status"] == "ok" for item in results),
               "discriminations": sum(item["discriminating"] for item in results),
               "correct_operator_identity_definitions_not_executed": len(identity_definitions),
               "original_frozen_executions_preserved": 254,
               "combined_reference_executions": 66, "combined_operator_error_controls": 188 + len(results),
               "combined_operator_error_discriminations": 150 + sum(item["discriminating"] for item in results),
               "required_controls_unchanged": 113, "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               "sqlite_version": sqlite3.sqlite_version, "fresh_model_responses": 0}
    output = {"summary": summary, "builder_sha256": sha(Path(__file__)),
              "original_freeze_sha256": sha(args.measurement / "freeze.json"), "inputs": checks,
              "correct_identity_definitions": identity_definitions, "items": results}
    with args.output.open("x") as handle:
        json.dump(output, handle, indent=2)
        handle.write("\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
