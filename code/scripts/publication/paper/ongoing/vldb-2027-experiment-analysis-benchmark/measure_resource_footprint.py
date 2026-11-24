"""Count the prepared ontology and the stored competency-query results.

The graph execution logs establish CQ outcomes; this command recounts those
logs and fingerprints the inputs rather than executing graph queries again.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from rdflib import Graph, OWL, RDF, SH, URIRef


def measure(root: Path, ontology_dir: Path) -> dict:
    paths = [ontology_dir / "spectra.ttl", ontology_dir / "spectra-shapes.ttl"]
    ontology, shapes = (Graph().parse(p) for p in paths)

    def fingerprint(path: Path) -> dict:
        return {"path": str(path.relative_to(root)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    def named(graph: Graph, kind: URIRef) -> int:
        return sum(isinstance(term, URIRef) and
                   str(term).startswith("https://w3id.org/spectra#")
                   for term in set(graph.subjects(RDF.type, kind)))

    counts = {key: named(graph, kind) for key, graph, kind in (
        ("classes", ontology, OWL.Class),
        ("object_properties", ontology, OWL.ObjectProperty),
        ("datatype_properties", ontology, OWL.DatatypeProperty),
        ("node_shapes", shapes, SH.NodeShape))}
    partitions = []
    for wg in range(1, 6):
        total = Counter()
        inputs = []
        for phase in range(1, 6):
            path = root / f"logs/tsg/RAN/formal/RAN{wg}/phase-{phase}/cq_cypher_results.json"
            data = json.loads(path.read_text())
            outcomes = Counter(row["status"] for row in data["results"])
            if set(outcomes) - {"PASS", "NO_DATA", "FAIL"}:
                raise ValueError(f"Unknown CQ status in {path}")
            meta, summary = data.get("metadata", {}), data.get("summary", {})
            totals = [summary.get("total"), data.get("total"),
                      meta.get("total"), meta.get("total_questions")]
            if any(value != len(data["results"]) for value in totals if value is not None):
                raise ValueError(f"CQ result/summary total mismatch in {path}")
            for status in ("PASS", "NO_DATA", "FAIL", "ERROR", "WARN"):
                values = [summary.get(status), summary.get(status.lower()),
                          meta.get(status.lower() + "_count")]
                if any(value != outcomes[status] for value in values if value is not None):
                    raise ValueError(f"CQ {status} result/summary mismatch in {path}")
            inputs.append({**fingerprint(path), "counts": dict(outcomes)})
            total.update(outcomes)
        partitions.append({"working_group": f"RAN{wg}",
                           "counts": dict(total), "inputs": inputs})
    return {
        "ontology": counts,
        "ontology_files": [fingerprint(p) for p in paths],
        "cq_partitions": partitions,
        "cq_total": dict(sum((Counter(p["counts"]) for p in partitions), Counter())),
        "scope": "Named SPECTRA terms in the prepared public ontology; competency checks over existing per-partition loaded-graph execution logs, not a fresh CQ execution.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ontology-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
    result = measure(root, args.ontology_dir.resolve())
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"ontology": result["ontology"], "cq_total": result["cq_total"]}))


if __name__ == "__main__":
    main()
