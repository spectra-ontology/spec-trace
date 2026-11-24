#!/usr/bin/env python3
"""Reproduce all 37 current M2 conditions from released files, fully offline.

The packaged analyze_template_session.py performs every score and bootstrap.
This adapter only restores its historical repository-relative input layout in a
temporary workspace and points its meeting-name lookup at released SQLite.
The release directory is opened read only. Requires Python 3.11 and numpy.
"""
from __future__ import annotations

import argparse
import contextlib
import gzip
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

TRACK_NAME = "vldb-2027-experiment-analysis-benchmark"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--release", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--expected", type=Path,
                    help="Optional published reference JSON with the expected analysis output SHA-256")
    ap.add_argument("--work-parent", type=Path, help="Optional parent of the disposable adapter workspace")
    args = ap.parse_args()
    release = args.release.resolve()
    scripts = release / "code/scripts/publication/paper/ongoing" / TRACK_NAME
    if not scripts.is_dir():
        raise SystemExit("Missing the packaged VLDB scripts: " + str(scripts))
    if not any((parent / ".git").exists() for parent in scripts.parents):
        raise SystemExit("Create the documented root marker first: mkdir -p RELEASE/code/.git")
    source_names = ["analyze_template_session.py", "build_chain_items.py", "score_chain_eval.py",
                    "score_meeting_spelling_sensitivity.py", "score_meeting_suffix_insensitive.py",
                    "summarize_text_route_full.py"]
    source_hashes = {name: hashlib.sha256((scripts / name).read_bytes()).hexdigest() for name in source_names}
    if args.work_parent:
        args.work_parent.mkdir(parents=True, exist_ok=True)
    args.out = args.out.resolve()
    args.report = args.report.resolve()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vldb-m2-", dir=args.work_parent) as temporary:
        adapter = Path(temporary)
        track = adapter / "logs/publication/paper/ongoing" / TRACK_NAME
        track.mkdir(parents=True)
        (track.parent / "sigir-2027-research").symlink_to(track, target_is_directory=True)
        (track / "chain_eval").symlink_to(release / "responses/chain_eval", target_is_directory=True)
        (track / "final").symlink_to(release / "responses/final", target_is_directory=True)
        integration = track / "integration"
        integration.mkdir()
        (integration / "items_final").symlink_to(release / "benchmark/items_final", target_is_directory=True)
        databases = integration / "sqlite_final"
        databases.mkdir()
        for n in range(1, 6):
            name = f"RAN{n}.sqlite"
            source = release / "sqlite" / name
            target = databases / name
            if source.is_file():
                target.symlink_to(source)
            else:
                with gzip.open(source.with_suffix(".sqlite.gz"), "rb") as inp, target.open("wb") as out:
                    shutil.copyfileobj(inp, out)
        # Import the unmodified scoring dependency first so that the lookup
        # called during analyzer import reads the released database copies.
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(scripts))
        spelling = importlib.import_module("score_meeting_spelling_sensitivity")
        spelling.ROOT = adapter
        analyzer = importlib.import_module("analyze_template_session")
        analyzer.ROOT = adapter
        stdout_path = args.report.with_suffix(".stdout.txt")
        previous_argv = sys.argv
        try:
            sys.argv = [str(scripts / "analyze_template_session.py"), "--out", str(args.out)]
            with stdout_path.open("w") as stdout, contextlib.redirect_stdout(stdout):
                analyzer.main()
        finally:
            sys.argv = previous_argv
    output = json.loads(args.out.read_text())
    if source_hashes != {name: hashlib.sha256((scripts / name).read_bytes()).hexdigest() for name in source_names}:
        raise SystemExit("An original scoring/analysis source changed during reproduction")
    conditions = output["conditions"]
    if len(conditions) != 37 or output["itemCount"] != 667:
        raise SystemExit("Unexpected current-condition or admitted-item count")
    report = {
        "items": output["itemCount"], "conditions": len(conditions),
        "analysis_script": "code/scripts/publication/paper/ongoing/" + TRACK_NAME + "/analyze_template_session.py",
        "analysis_script_sha256": hashlib.sha256((scripts / "analyze_template_session.py").read_bytes()).hexdigest(),
        "original_source_sha256": source_hashes,
        "adapted_module_globals": ["score_meeting_spelling_sensitivity.ROOT",
                                   "analyze_template_session.ROOT"],
        "output_sha256": hashlib.sha256(args.out.read_bytes()).hexdigest(),
        "scope": "Original packaged scoring, template/session assignment and 10000-draw bootstraps; only filesystem paths adapted. No model calls, database queries beyond reading meeting labels, or network requests.",
        "conditions_exact": {name: value["answered"] for name, value in conditions.items()},
        "method_means": output["clusterBootstrap"]["methodMean"],
        "session_bootstrap": output["sessionBootstrap"],
    }
    if args.expected:
        expected = json.loads(args.expected.read_text())
        report["expected_output_sha256"] = expected["output_sha256"]
        report["matches_expected_output"] = report["output_sha256"] == expected["output_sha256"]
        if not report["matches_expected_output"]:
            args.report.write_text(json.dumps(report, indent=2) + "\n")
            raise SystemExit("Reproduced analysis differs from the published reference hash")
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"items": report["items"], "conditions": report["conditions"],
                      "output_sha256": report["output_sha256"]}))


if __name__ == "__main__":
    main()
