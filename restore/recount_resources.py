#!/usr/bin/env python3
"""Recount the packaged ontology and archived competency-query outcomes."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from rdflib import Graph, OWL, RDF, SH, URIRef


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--release", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    release = args.release.resolve()
    ontology = Graph().parse(release / "docs/spectra.ttl")
    shapes = Graph().parse(release / "docs/spectra-shapes.ttl")
    named = lambda graph, kind: sum(isinstance(s, URIRef) and str(s).startswith("https://w3id.org/spectra#")
                                    for s in set(graph.subjects(RDF.type, kind)))
    counts = {key: named(graph, kind) for key, graph, kind in (
        ("classes", ontology, OWL.Class), ("object_properties", ontology, OWL.ObjectProperty),
        ("datatype_properties", ontology, OWL.DatatypeProperty), ("node_shapes", shapes, SH.NodeShape))}
    index = json.loads((release / "sources/competency_queries/index.json").read_text())
    outcomes = Counter()
    for entry in index["receipts"]:
        path = release / entry["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError("Competency receipt hash differs: " + entry["path"])
        receipt = json.loads(path.read_text())
        if receipt["original_receipt"]["sha256"] != entry["source_sha256"]:
            raise ValueError("Original receipt provenance differs")
        actual = Counter(row["status"] for row in receipt["results"])
        if dict(actual) != entry["counts"] or dict(actual) != receipt["counts"]:
            raise ValueError("Competency receipt outcome counts differ")
        outcomes.update(actual)
    if dict(outcomes) != index["total"]:
        raise ValueError("Competency index outcome counts differ")
    report = {"ontology": counts, "cq_receipts": len(index["receipts"]), "cq_total": dict(outcomes),
              "cq_scope": "Recount of sanitized original loaded-graph execution receipts; not a fresh execution and not restricted to the released query graph."}
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
