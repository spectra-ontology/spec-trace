#!/usr/bin/env python3
"""Reproduce the synthetic relational-contract stress from released files.

The default is the small RAN1 pilot; --full runs the fixed 35-anchor design.
Only filesystem paths are adapted. Original code, inputs and historical gold
are read only; synthetic rows live in in-memory SQLite copies.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile

TRACK = Path("logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark")


def sha(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--release", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--out", type=Path, required=True, help="Output outside the release directory")
    ap.add_argument("--full", action="store_true", help="Run all 35 anchors and 13 stored SQL conditions")
    ap.add_argument("--work-parent", type=Path, help="Optional parent of disposable workspace")
    args = ap.parse_args()
    release, output = args.release.resolve(), args.out.resolve()
    if output == release or release in output.parents:
        raise SystemExit("Write results outside the release directory")
    if sqlite3.sqlite_version != "3.37.2":
        raise SystemExit(f"Use /usr/bin/python3 with SQLite 3.37.2; found {sqlite3.sqlite_version}")
    package = Path(__file__).resolve().parent
    manifest = json.loads((package / "manifest.json").read_text())
    if any(sha(package / name) != expected for name, expected in manifest["originalCodeSha256"].items()):
        raise SystemExit("An original stress or reference-SQL source differs from its manifest")
    if args.work_parent:
        args.work_parent.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    source_hashes = {}
    adapted_paths = {}
    sys.dont_write_bytecode = True
    with tempfile.TemporaryDirectory(prefix="spectra-semantic-stress-", dir=args.work_parent) as temporary:
        root = Path(temporary)
        (root / ".git").mkdir()
        scripts = root / "scripts/publication/paper/ongoing" / TRACK.name
        scripts.mkdir(parents=True)
        for name in ["measure_semantic_scope_stress.py", "measure_relational_equivalence.py"]:
            source, target = package / "original" / name, scripts / name
            shutil.copyfile(source, target)
            source_hashes[str(source.relative_to(release))] = sha(source)
            adapted_paths[str(target.relative_to(root))] = str(source.relative_to(release))
        track = root / TRACK
        integration = track / "integration"
        integration.mkdir(parents=True)
        (integration / "items_final").symlink_to(release / "benchmark/items_final", target_is_directory=True)
        (track / "chain_eval").symlink_to(release / "responses/chain_eval", target_is_directory=True)
        databases = integration / "sqlite_final"
        databases.mkdir()
        groups = range(1, 6) if args.full else [1]
        for number in groups:
            source = release / "sqlite" / f"RAN{number}.sqlite"
            target = databases / source.name
            if source.is_file():
                target.symlink_to(source)
            else:
                source = source.with_suffix(".sqlite.gz")
                with gzip.open(source, "rb") as inp, target.open("wb") as out:
                    shutil.copyfileobj(inp, out)
            source_hashes[str(source.relative_to(release))] = sha(source)
            adapted_paths[str(target.relative_to(root))] = str(source.relative_to(release))
        for part in ["core", "ran5"]:
            source = release / f"benchmark/items_final/gate/{part}/chain_items_admitted.jsonl"
            adapted_paths[str((integration / "items_final/gate" / part / source.name).relative_to(root))] = str(source.relative_to(release))
            source_hashes[str(source.relative_to(release))] = sha(source)
        response_names = [f"text2sql/RAN{n}_text2sql_run{run}.jsonl"
                          for n in groups for run in ("ABCDEFGHIJ" if args.full else "A")]
        if args.full:
            response_names.extend(f"codex/chain_sql_RAN{n}_codex.jsonl" for n in groups)
            response_names.extend(f"codex_v2/responses/RAN{n}_sql_{mode}_codex.jsonl"
                                  for n in groups for mode in ["dom", "exp"])
        for name in response_names:
            source = release / "responses/chain_eval" / name
            source_hashes[str(source.relative_to(release))] = sha(source)
            adapted_paths[str((track / "chain_eval" / name).relative_to(root))] = str(source.relative_to(release))
        sys.path.insert(0, str(scripts))
        spec = importlib.util.spec_from_file_location("semantic_scope_stress_original", scripts / "measure_semantic_scope_stress.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        previous_argv = sys.argv
        try:
            sys.argv = [str(scripts / "measure_semantic_scope_stress.py"), "--out", str(output)]
            if not args.full:
                sys.argv.append("--pilot")
            module.main()
        finally:
            sys.argv = previous_argv
    unchanged = all(sha(release / name) == expected for name, expected in source_hashes.items())
    if not unchanged:
        raise SystemExit("A released input or original script changed during reproduction")
    result = json.loads(output.read_text())
    result["releaseReproduction"] = {
        "mode": "full" if args.full else "pilot",
        "adaptation": "filesystem paths only; original stress and reference SQL copied byte-for-byte",
        "releasedInputHashesUnchanged": unchanged,
        "releasedInputSha256": source_hashes,
        "logicalToReleasedPath": adapted_paths,
        "referenceFullSha256": sha(package / "reference_full.json"),
        "dependencies": "Python standard library; SQLite 3.37.2; no model or network calls",
    }
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"mode": result["releaseReproduction"]["mode"],
                      "originalInputsUnchanged": result["originalInputHashesUnchanged"],
                      "releasedInputsUnchanged": unchanged, "outputSha256": sha(output)}))


if __name__ == "__main__":
    main()
