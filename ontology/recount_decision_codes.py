#!/usr/bin/env python3
"""Count every released disposition by formal code and working group (stdlib only)."""

import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def formal_codes(path):
    # This extracts the one named property shape in the packaged Turtle syntax.
    text = path.read_text(encoding="utf-8")
    shape = re.search(r"(?ms)^tdoc:DecisionDispositionShape\b.*?(?=^tdoc:|\Z)", text)
    if shape is None:
        raise ValueError("DecisionDispositionShape is absent")
    properties = re.findall(
        r"\[([^\[\]]*\bsh:path\s+tdoc:dispositionCode\b[^\[\]]*)\]",
        shape.group(), re.S)
    if len(properties) != 1:
        raise ValueError("Expected one dispositionCode property shape")
    values = re.search(r"sh:in\s*\((.*?)\)", properties[0], re.S)
    if values is None:
        raise ValueError("dispositionCode has no closed sh:in list")
    codes = re.findall(r'"([a-z_]+)"', values.group(1))
    remainder = re.sub(r'"[a-z_]+"', "", values.group(1))
    if remainder.strip() or len(codes) != 16 or len(set(codes)) != 16:
        raise ValueError("Expected sixteen distinct literal disposition codes")
    return codes


def recount(release):
    shapes = release / "docs/spectra-shapes.ttl"
    codebook = release / "studies/disposition_reading/codebook.md"
    codes = formal_codes(shapes)
    definitions = codebook.read_text(encoding="utf-8").split("## Codes\n", 1)[1].split("## Scope\n", 1)[0]
    reader_codes = re.findall(r"(?m)^\| ([a-z_]+) \|", definitions)
    if set(reader_codes) != set(codes) | {"cannot_tell"}:
        raise ValueError("Reader codebook differs from formal codes plus cannot_tell")
    sources = {path.relative_to(release).as_posix(): sha256(path)
               for path in (shapes, codebook)}
    groups = {}
    total = Counter()
    for number in range(1, 6):
        wg = f"RAN{number}"
        directory = release / "records/phase-2" / wg
        candidates = [directory / "decision_dispositions.jsonld",
                      directory / "decision_dispositions.jsonld.gz"]
        paths = [path for path in candidates if path.is_file()]
        if len(paths) != 1:
            raise ValueError(f"Expected exactly one disposition input for {wg}")
        path = paths[0]
        sources[path.relative_to(release).as_posix()] = sha256(path)
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rt", encoding="utf-8") as source:
            graph = json.load(source)["@graph"]
        counts = Counter()
        for record in graph:
            if record.get("@type") != "DecisionDisposition":
                raise ValueError(f"Unexpected record type in {wg}")
            code = record.get("dispositionCode")
            if code not in codes:
                raise ValueError(f"Code outside formal set in {wg}: {code!r}")
            counts[code] += 1
        groups[wg] = {"total": len(graph), "codes": {code: counts[code] for code in codes}}
        total.update(counts)
        del graph
    return {
        "population": "All released phase-2 DecisionDisposition records, across evidence statuses and scopes",
        "formal_shape": "docs/spectra-shapes.ttl:DecisionDispositionShape/dispositionCode",
        "formal_codes": codes,
        "auxiliary_reader_code": "cannot_tell",
        "auxiliary_reader_code_role": "Reader assessment of insufficient packet evidence; stored record counts use the formal code set",
        "total": sum(total.values()),
        "codes": {code: total[code] for code in codes},
        "working_groups": groups,
        "source_sha256": sources,
        "script_sha256": sha256(Path(__file__)),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out", type=Path, help="JSON output; defaults to stdout")
    parser.add_argument("--expect-total", type=int, help="Reject a different total")
    args = parser.parse_args()
    report = recount(args.release.resolve())
    if args.expect_total is not None and report["total"] != args.expect_total:
        raise ValueError(f"Expected {args.expect_total} records; found {report['total']}")
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
