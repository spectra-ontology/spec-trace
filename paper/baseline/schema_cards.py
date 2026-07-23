#!/usr/bin/env python3
"""Generate a compact per-WG schema card for the KG-grounded baseline prompt.

Data-driven from the live graph (no hand-authored schema): node labels with
their property keys (db.schema.nodeTypeProperties) and the relationship
patterns actually present (db.schema.visualization -> (Start)-[:TYPE]->(End)).

Writes schema_cards.json = {wg: {"labels": {...}, "rels": [...], "card": "<text>"}}.
The card text is what gets embedded in the Text2Cypher prompt.
"""
import json
import os
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
PORTS = {'RAN1': 7687, 'RAN2': 7688, 'RAN3': 7689, 'RAN4': 7690, 'RAN5': 7691}
# properties worth surfacing first (identity/label-bearing); others still listed
PRIORITY_PROPS = ['tdocNumber', 'crNumber', 'specNumber', 'sectionId', 'sectionNumber',
                  'title', 'name', 'meetingNumber', 'canonicalMeetingNumber',
                  'meetingNumberInt', 'companyName', 'releaseCode', 'status', 'tableNumber']


def node_props(session):
    props = defaultdict(set)
    for r in session.run("CALL db.schema.nodeTypeProperties()"):
        labels = r.get('nodeLabels') or []
        pk = r.get('propertyName')
        for lb in labels:
            if pk:
                props[lb].add(pk)
    return {k: sorted(v) for k, v in props.items()}


def rel_patterns(session):
    """(StartLabel)-[:TYPE]->(EndLabel) triples from schema visualization."""
    pats = set()
    try:
        rec = session.run("CALL db.schema.visualization()").single()
        nodes = {n.element_id: (list(n.labels)[0] if n.labels else '?')
                 for n in rec['nodes']}
        for rel in rec['relationships']:
            s = nodes.get(rel.start_node.element_id, '?')
            e = nodes.get(rel.end_node.element_id, '?')
            pats.add((s, rel.type, e))
    except Exception as e:
        print(f"    (visualization failed: {type(e).__name__}: {e})")
    return sorted(pats)


def order_props(plist):
    pri = [p for p in PRIORITY_PROPS if p in plist]
    rest = [p for p in plist if p not in PRIORITY_PROPS]
    return pri + rest


def build_card(wg, labels, rels):
    lines = [f"# Neo4j schema for 3GPP {wg} process graph", "", "## Node labels (with properties)"]
    for lb in sorted(labels):
        ps = order_props(labels[lb])
        shown = ps[:12]
        more = f" (+{len(ps)-12} more)" if len(ps) > 12 else ""
        lines.append(f"- (:{lb}) {{{', '.join(shown)}}}{more}")
    lines += ["", "## Relationship patterns"]
    for s, t, e in rels:
        lines.append(f"- (:{s})-[:{t}]->(:{e})")
    return "\n".join(lines)


def main():
    from neo4j import GraphDatabase
    pw = os.environ.get('NEO4J_PASSWORD')
    if not pw:
        raise SystemExit('set NEO4J_PASSWORD to your Neo4j bolt password before running')
    out = {}
    for wg, port in PORTS.items():
        drv = GraphDatabase.driver(f"bolt://localhost:{port}", auth=("neo4j", pw))
        with drv.session() as s:
            labels = node_props(s)
            rels = rel_patterns(s)
        drv.close()
        card = build_card(wg, labels, rels)
        out[wg] = {'labels': labels, 'rels': rels, 'card': card}
        print(f"{wg}: {len(labels)} labels, {len(rels)} rel-patterns, card {len(card)} chars")
    (HERE / 'schema_cards.json').write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"-> wrote {HERE / 'schema_cards.json'}")


if __name__ == '__main__':
    main()
