#!/usr/bin/env python3
"""Verify the release and reproduce its stored-response results offline."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time


def verify(release: Path) -> int:
    count = 0
    for line in (release / "SHA256SUMS").read_text().splitlines():
        expected, name = line.split(maxsplit=1)
        path = release / name.lstrip("*")
        h = hashlib.sha256()
        with path.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                h.update(block)
        if h.hexdigest() != expected:
            raise ValueError("Package checksum differs: " + name)
        count += 1
    if not count:
        raise ValueError("Package checksum manifest is empty")
    return count


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--release", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--out", type=Path, default=Path("work/replay"))
    args = ap.parse_args()
    if sys.version_info < (3, 11):
        raise SystemExit("Use Python 3.11 or later")
    if importlib.util.find_spec("numpy") is None:
        raise SystemExit("Install replay dependencies: python3 -m pip install -r requirements-replay.txt")
    release, out = args.release.resolve(), args.out.resolve()
    started = time.monotonic()
    verified = verify(release)
    out.mkdir(parents=True, exist_ok=True)
    (release / "code/.git").mkdir(exist_ok=True)
    tasks = {
        "historical_scores": ["rescore_stored.py", "--out", str(out / "historical_scores.json")],
        "current_tables": ["reproduce_current_tables.py", "--out", str(out / "current_tables.json"),
                           "--report", str(out / "current_tables_report.json"),
                           "--expected", str(release / "sources/current_tables_reference.json")],
    }
    steps = {}
    for name, arguments in tasks.items():
        command = [sys.executable, "-I", "-B", str(release / "restore" / arguments[0]),
                   "--release", str(release), *arguments[1:]]
        tick = time.monotonic()
        with (out / (name + ".stdout.txt")).open("w") as log:
            subprocess.run(command, cwd=release, stdout=log, stderr=subprocess.STDOUT, check=True)
        steps[name] = {"exit_code": 0, "seconds": round(time.monotonic() - tick, 3)}
    report = {"verified_files": verified, "steps": steps,
              "seconds": round(time.monotonic() - started, 3),
              "scope": "Offline checksum verification, 60 historical score entries and all 37 current conditions from stored responses. Source restoration and new model generation are separate workflows."}
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
