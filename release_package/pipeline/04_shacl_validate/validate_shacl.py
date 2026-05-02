"""SPECTRA pipeline — Stage 04: SHACL conformance validation.

Loads Stage 02/03 JSON-LD records into rdflib + the SPECTRA ontology, runs
pyshacl with the SPECTRA SHACL shapes, and emits a conformance report.

Sanitized for public release.

Usage:
    python validate_shacl.py \
        --shapes ../../shapes/spectra-core.shacl.ttl \
        --ontology ../../ontology/spectra.ttl \
        --jsonld out/02_metadata_parse/*.jsonld out/03_document_parse/*.jsonld \
        --report-out logs/shacl_report.txt
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import List

from rdflib import Graph
from pyshacl import validate


def load_data(jsonld_paths: List[Path], ontology_path: Path) -> Graph:
    """Merge Stage 02/03 JSON-LD records and SPECTRA ontology TBox into one graph."""
    g = Graph()
    g.parse(str(ontology_path), format="turtle")
    for p in jsonld_paths:
        if not p.exists():
            print(f"WARN: input not found, skipping: {p}", file=sys.stderr)
            continue
        # rdflib supports JSON-LD with `format="json-ld"` if pyld installed,
        # else manual context expansion. Here we assume rdflib's default JSON-LD plugin.
        g.parse(str(p), format="json-ld")
    return g


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--shapes", required=True, type=Path,
                    help="Path to spectra-core.shacl.ttl")
    ap.add_argument("--ontology", required=True, type=Path,
                    help="Path to ontology/spectra.ttl (used as ont_graph for inference)")
    ap.add_argument("--jsonld", required=True, type=Path, nargs="+",
                    help="One or more Stage 02/03 JSON-LD inputs")
    ap.add_argument("--report-out", type=Path, default=None,
                    help="Optional path to write the human-readable conformance report")
    ap.add_argument("--strict", action="store_true",
                    help="Exit non-zero on the first SHACL violation")
    args = ap.parse_args()

    data_graph = load_data(args.jsonld, args.ontology)
    shapes_graph = Graph().parse(str(args.shapes), format="turtle")
    ont_graph = Graph().parse(str(args.ontology), format="turtle")

    conforms, results_graph, results_text = validate(
        data_graph,
        shacl_graph=shapes_graph,
        ont_graph=ont_graph,
        inference="rdfs",
        debug=False,
    )

    summary = f"Conforms: {conforms}\n\n{results_text}\n"
    if args.report_out:
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(summary)

    print(summary)
    if not conforms and args.strict:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
