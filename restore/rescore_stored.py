#!/usr/bin/env python3
"""Rescore the 60 historical stored-score entries from released items and stored responses."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--release", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    release = args.release.resolve()
    responses = []
    for line in (release / "responses/chain_eval/scores.inputs").read_text().splitlines():
        suffix = line.split("/chain_eval/", 1)[1]
        responses.append(str(release / "responses/chain_eval" / suffix))
    scorer = release / "code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/score_chain_eval.py"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-I", "-B", str(scorer), "--items",
        str(release / "benchmark/items_final/gate/core/chain_items_admitted.jsonl"),
        str(release / "benchmark/items_final/gate/ran5/chain_items_admitted.jsonl"),
        "--responses", *responses, "--out", str(args.out)], check=True)
    expected = json.loads((release / "responses/chain_eval/scores.json").read_text())
    actual = json.loads(args.out.read_text())
    strip = lambda row: {k: v for k, v in row.items() if k != "responses"}
    matches = sum(strip(x) == strip(y) for x, y in zip(expected, actual))
    print(json.dumps({"stored_entries": len(expected), "rescored_entries": len(actual),
                      "identical_except_response_path": matches}))
    raise SystemExit(0 if [strip(x) for x in expected] == [strip(x) for x in actual] else 1)


if __name__ == "__main__":
    main()
