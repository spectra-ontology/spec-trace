"""Count release agreement on the pinned SQLite clause links."""

from __future__ import annotations

import argparse
from contextlib import closing
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
from tempfile import TemporaryDirectory


GROUPS = ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5")
CENSUS = """
SELECT
    COUNT(*) AS storedLinks,
    COUNT(*) FILTER (WHERE d.id IS NOT NULL AND s.id IS NOT NULL) AS joinedLinks,
    COUNT(*) FILTER (WHERE d.id IS NULL AND s.id IS NOT NULL) AS missingDocument,
    COUNT(*) FILTER (WHERE s.id IS NULL AND d.id IS NOT NULL) AS missingSection,
    COUNT(*) FILTER (WHERE d.id IS NULL AND s.id IS NULL) AS missingBoth,
    COUNT(*) FILTER (WHERE d.target_release = s.release) AS sameRelease,
    COUNT(*) FILTER (WHERE d.target_release <> s.release) AS differentRelease,
    COUNT(*) FILTER (WHERE d.id IS NOT NULL AND s.id IS NOT NULL
        AND (d.target_release IS NULL OR s.release IS NULL)) AS releaseUnrecorded,
    COUNT(*) FILTER (WHERE d.id IS NOT NULL AND s.id IS NOT NULL
        AND d.target_release IS NULL) AS targetReleaseUnrecorded,
    COUNT(*) FILTER (WHERE d.id IS NOT NULL AND s.id IS NOT NULL
        AND s.release IS NULL) AS sectionReleaseUnrecorded
FROM cr_modifies_section AS x
LEFT JOIN document AS d ON d.id = x.cr
LEFT JOIN section AS s ON s.id = x.section_id
"""


def verify_sha256(path: Path, hashes: dict[str, str]) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != hashes[path.name]:
        raise ValueError(f"SHA-256 mismatch for {path.name}")
    return actual


def census(folder: Path) -> dict:
    hashes = {}
    for line in (folder / "SHA256SUMS.txt").read_text().splitlines():
        digest, filename = line.split()
        hashes[filename] = digest
    per_group = {}
    inputs = {}
    for group in GROUPS:
        db_name = f"{group}.sqlite"
        released_file = folder / (db_name if group == "RAN1" else f"{db_name}.gz")
        inputs[released_file.name] = verify_sha256(released_file, hashes)
        with TemporaryDirectory(prefix="spectra-section-editions-") as temporary:
            database = released_file
            if released_file.suffix == ".gz":
                database = Path(temporary) / db_name
                with gzip.open(released_file, "rb") as source, database.open("wb") as target:
                    shutil.copyfileobj(source, target)
                inputs[db_name] = verify_sha256(database, hashes)

            with closing(sqlite3.connect(f"{database.as_uri()}?mode=ro&immutable=1", uri=True)) as db:
                db.row_factory = sqlite3.Row
                per_group[group] = dict(db.execute(CENSUS).fetchone())

    totals = {
        field: sum(counts[field] for counts in per_group.values())
        for field in per_group[GROUPS[0]]
    }
    return {"sqliteSha256": inputs, "workingGroups": per_group, "total": totals}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db-dir", type=Path, default=Path(__file__).resolve().parents[2] / "sqlite",
        help="directory containing the release databases and SHA256SUMS.txt",
    )
    parser.add_argument("--check", type=Path, help="compare reproduced output with a saved receipt")
    args = parser.parse_args()
    report = census(args.db_dir.resolve())
    if args.check is not None and report != json.loads(args.check.read_text()):
        raise SystemExit(f"Edition census differs from {args.check}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
