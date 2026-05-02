"""SPECTRA pipeline — Stage 05: bulk Neo4j load via parallel Cypher MERGE.

Reads Stage 02/03 JSON-LD records and idempotently loads them into a Neo4j
graph using MERGE on SPECTRA functional properties (e.g., tdocNumber,
crNumber, sectionId).

Sanitized for public release (Slack/incident hooks, internal hostnames,
hard-coded credentials removed).

Usage:
    export NEO4J_URI=bolt://localhost:7687
    export NEO4J_USER=neo4j
    export NEO4J_PASSWORD=<password>
    python load_neo4j.py --jsonld out/*.jsonld --batch-size 1000 --workers 4
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Any, Iterable

from neo4j import GraphDatabase

SPECTRA = "https://w3id.org/spectra#"

# Map SPECTRA @type → Neo4j label + key (functional property used by MERGE)
TYPE_TO_LABEL = {
    f"{SPECTRA}Tdoc":               ("Tdoc",              f"{SPECTRA}tdocNumber"),
    f"{SPECTRA}CR":                 ("CR",                f"{SPECTRA}crNumber"),
    f"{SPECTRA}LS":                 ("LS",                f"{SPECTRA}tdocNumber"),
    f"{SPECTRA}Summary":            ("Summary",           f"{SPECTRA}tdocNumber"),
    f"{SPECTRA}SessionNotes":       ("SessionNotes",      f"{SPECTRA}tdocNumber"),
    f"{SPECTRA}Agreement":          ("Agreement",         "@id"),
    f"{SPECTRA}Conclusion":         ("Conclusion",        "@id"),
    f"{SPECTRA}WorkingAssumption":  ("WorkingAssumption", "@id"),
    f"{SPECTRA}Section":            ("Section",           "@id"),
    f"{SPECTRA}Spec":               ("Spec",              "@id"),
    f"{SPECTRA}TechnicalReport":    ("TechnicalReport",   f"{SPECTRA}trNumber"),
    f"{SPECTRA}TRImpact":           ("TRImpact",          "@id"),
    f"{SPECTRA}Meeting":            ("Meeting",           "@id"),
    f"{SPECTRA}Company":            ("Company",           "@id"),
    f"{SPECTRA}WorkingGroup":       ("WorkingGroup",      "@id"),
    f"{SPECTRA}AgendaItem":         ("AgendaItem",        "@id"),
    f"{SPECTRA}CRPack":             ("CRPack",            "@id"),
    f"{SPECTRA}WorkItem":           ("WorkItem",          "@id"),
    f"{SPECTRA}Release":            ("Release",           "@id"),
    f"{SPECTRA}Contact":            ("Contact",           "@id"),
}


def relation_label_from_predicate(pred: str) -> str:
    """SPECTRA predicate IRI → Neo4j relationship type (UPPER_SNAKE_CASE)."""
    local = pred.replace(SPECTRA, "")
    # camelCase → UPPER_SNAKE_CASE
    s = ""
    for ch in local:
        if ch.isupper():
            s += "_" + ch
        else:
            s += ch.upper()
    return s.lstrip("_")


def split_node_and_edges(record: Dict[str, Any]) -> tuple[Dict[str, Any], List[Dict[str, str]]]:
    """Separate scalar properties (DataProperty) from outgoing edges (ObjectProperty)."""
    node_props: Dict[str, Any] = {"@id": record["@id"]}
    edges: List[Dict[str, str]] = []
    for k, v in record.items():
        if k in ("@id", "@type"):
            continue
        # Edges: dict or list[dict] with @id
        if isinstance(v, dict) and "@id" in v:
            edges.append({"pred": k, "target": v["@id"]})
        elif isinstance(v, list) and v and isinstance(v[0], dict) and "@id" in v[0]:
            for item in v:
                edges.append({"pred": k, "target": item["@id"]})
        else:
            node_props[k.replace(SPECTRA, "")] = v
    return node_props, edges


def merge_node_cypher(label: str, key_pred: str, props: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    """Build MERGE Cypher for one node."""
    if key_pred == "@id":
        key_value = props["@id"]
        cypher = f"MERGE (n:{label} {{iri: $iri}}) SET n += $props"
        params = {"iri": key_value, "props": {k: v for k, v in props.items() if k != "@id"}}
    else:
        key_local = key_pred.replace(SPECTRA, "")
        key_value = props.get(key_local, props["@id"])
        cypher = f"MERGE (n:{label} {{{key_local}: $key, iri: $iri}}) SET n += $props"
        params = {
            "key": key_value,
            "iri": props["@id"],
            "props": {k: v for k, v in props.items() if k != "@id"},
        }
    return cypher, params


def load_record(driver, record: Dict[str, Any]) -> None:
    rec_type = record.get("@type", "")
    label_info = TYPE_TO_LABEL.get(rec_type)
    if not label_info:
        return  # unknown type — skip
    label, key_pred = label_info
    node_props, edges = split_node_and_edges(record)
    cypher, params = merge_node_cypher(label, key_pred, node_props)
    with driver.session() as s:
        s.run(cypher, **params)
        for edge in edges:
            rel = relation_label_from_predicate(edge["pred"])
            s.run(
                f"MATCH (a {{iri: $src}}), (b {{iri: $tgt}}) "
                f"MERGE (a)-[:{rel}]->(b)",
                src=record["@id"], tgt=edge["target"],
            )


def iter_records(jsonld_paths: Iterable[Path]) -> Iterable[Dict[str, Any]]:
    for p in jsonld_paths:
        if not p.exists():
            print(f"WARN: input not found, skipping: {p}", file=sys.stderr)
            continue
        data = json.loads(p.read_text())
        for rec in data.get("@graph", []):
            yield rec


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jsonld", required=True, type=Path, nargs="+",
                    help="Stage 02/03 JSON-LD inputs")
    ap.add_argument("--batch-size", type=int, default=1000)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD")
    if not password:
        sys.exit("ERROR: set NEO4J_PASSWORD environment variable")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    n = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = []
        for rec in iter_records(args.jsonld):
            futs.append(pool.submit(load_record, driver, rec))
            if len(futs) >= args.batch_size:
                for f in as_completed(futs):
                    f.result()
                    n += 1
                futs.clear()
                print(f"[load_neo4j] loaded {n} records...")
        for f in as_completed(futs):
            f.result()
            n += 1
    driver.close()
    print(f"[load_neo4j] done — {n} records loaded into Neo4j ({uri})")


if __name__ == "__main__":
    main()
