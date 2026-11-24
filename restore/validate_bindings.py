#!/usr/bin/env python3
"""Validate rehydrated JSON-LD with the released vocabulary and all SHACL shapes.

RDF 1.1 simple strings and explicitly typed xsd:string have the same datatype.
Normalize that parser representation in both graphs before applying the original
constraints. This does not change a shape, data value, status, or target.
"""
import argparse
import json
from pathlib import Path
from rdflib import Graph, Literal, XSD
from pyshacl import validate


def normalize_strings(graph):
    count = 0
    for s, p, value in list(graph):
        if isinstance(value, Literal) and value.datatype is None and value.language is None:
            graph.remove((s, p, value))
            graph.add((s, p, Literal(str(value), datatype=XSD.string)))
            count += 1
    return count


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--release", type=Path, required=True)
    ap.add_argument("--records", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()
    data = Graph().parse(args.records, format="json-ld")
    shapes = Graph().parse(args.release / "docs/spectra-shapes.ttl")
    ontology = Graph().parse(args.release / "docs/spectra.ttl")
    normalized = {name: normalize_strings(graph) for name, graph in
                  (("data", data), ("shapes", shapes), ("ontology", ontology))}
    conforms, report, text = validate(data, shacl_graph=shapes, ont_graph=ontology, inference="rdfs")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps({"conforms": bool(conforms), "data_triples": len(data),
                                     "rdf11_strings_normalized": normalized, "validation_report": text}, indent=2) + "\n")
    print(text.strip())
    raise SystemExit(0 if conforms else 1)


if __name__ == "__main__":
    main()
