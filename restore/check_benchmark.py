#!/usr/bin/env python3
"""Rebuild and gate every stored item from a clean released-record workspace.

Run restore_sources.py into --source-root first. This checker uses only released
code/records, stored anchors and the hash-checked source documents. Working
groups run sequentially; each subprocess releases its memory before the next.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def lines(path, wg=None):
    return [line for line in path.read_bytes().splitlines() if line.strip()
            and (wg is None or json.loads(line)["wg"] == wg)]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--release", type=Path, required=True)
    ap.add_argument("--source-root", type=Path, required=True)
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--wg", nargs="+", default=["RAN1", "RAN2", "RAN3", "RAN4", "RAN5"])
    args = ap.parse_args()
    release, source_root, work = args.release.resolve(), args.source_root.resolve(), args.work.resolve()
    if work.exists() and any(work.iterdir()):
        raise SystemExit("Use an empty --work directory so the check starts from released records.")
    work.mkdir(parents=True, exist_ok=True)
    scripts = release / "code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
    reports = []
    for wg in args.wg:
        wd = work / wg
        instances = wd / "ontology/output/tsg/RAN/formal/instances"
        for phase in ("phase-1", "phase-2", "phase-4"):
            src = release / "records" / phase / wg
            if not src.exists():
                continue
            target = instances / phase / wg
            target.mkdir(parents=True, exist_ok=True)
            for path in sorted(src.iterdir()):
                if path.suffix == ".gz":
                    with gzip.open(path, "rb") as inp, (target / path.stem).open("wb") as out:
                        shutil.copyfileobj(inp, out)
                else:
                    (target / path.name).symlink_to(path)
        source_input = source_root / "ontology/input"
        (wd / "ontology/input").symlink_to(source_input, target_is_directory=True)
        part = "ran5" if wg == "RAN5" else "core"
        anchors = release / "benchmark" / ("chain_items_ran5" if wg == "RAN5" else "chain_items_rebuilt") / "chain_items.jsonl"
        extra = []
        if wg == "RAN5":
            (instances / "RAN5_graph_export").symlink_to(release / "records/RAN5_graph_export", target_is_directory=True)
            extra = ["--phase4-root", str(instances / "RAN5_graph_export")]
        out = wd / "rebuilt"
        (out / "gate").mkdir(parents=True, exist_ok=True)
        commands = [
            [sys.executable, "-I", "-B", str(scripts / "build_chain_items.py"), "--wg", wg,
             "--per-cell", "20", "--seed", "20261111", "--anchors-from", str(anchors),
             "--out-dir", str(out), *extra],
            [sys.executable, "-I", "-B", str(scripts / "verify_chain_items.py"),
             "--items", str(out / "chain_items.jsonl"), "--out-dir", str(out / "gate"), *extra],
        ]
        for n, command in enumerate(commands):
            with (wd / f"step{n+1}.stdout").open("w") as stdout, (wd / f"step{n+1}.stderr").open("w") as stderr:
                subprocess.run(command, cwd=wd, stdout=stdout, stderr=stderr, check=True)
        stored = lines(release / f"benchmark/items_final/{part}/chain_items.jsonl", wg)
        built = lines(out / "chain_items.jsonl")
        expected = lines(release / f"benchmark/items_final/gate/{part}/chain_items_admitted.jsonl", wg)
        admitted = lines(out / "gate/chain_items_admitted.jsonl")
        report = {"wg": wg, "stored_drawn": len(stored), "rebuilt_drawn": len(built),
                  "drawn_byte_identical": stored == built, "stored_admitted": len(expected),
                  "gated_admitted": len(admitted), "admitted_byte_identical": expected == admitted,
                  "admitted_sha256": hashlib.sha256(b"\n".join(admitted)).hexdigest()}
        reports.append(report)
        print(json.dumps(report), flush=True)
        if stored != built or expected != admitted:
            raise SystemExit("Stored and regenerated benchmark differ; inspect the clean work directory.")
    report = {"working_groups": reports, "drawn": sum(x["rebuilt_drawn"] for x in reports),
              "admitted": sum(x["gated_admitted"] for x in reports),
              "all_byte_identical": all(x["drawn_byte_identical"] and x["admitted_byte_identical"] for x in reports),
              "source_scope": "Sources read from --source-root at their cited paths; gate recomputes each cited source SHA-256."}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k:v for k,v in report.items() if k != "working_groups"}))


if __name__ == "__main__":
    main()
