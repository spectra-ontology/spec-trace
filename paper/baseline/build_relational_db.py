#!/usr/bin/env python3
"""build_relational_db.py: flatten each per-WG Neo4j graph into a SQLite mirror.

Purpose: give the NL-to-SQL baseline the SAME records the KG-grounded condition
queries, so a score gap measures the access structure (relational vs graph) and
not the underlying data. The mapping is the textbook property-graph -> relational
one and is information-preserving in both directions:

  node(node_id, labels)                 global entity registry (labels = JSON array)
  "<Label>"(node_id PK, <properties>)   one table per entity class; a multi-class
                                        entity appears in each of its class tables
                                        under the SAME node_id
  "rel_<TYPE>"(src_id, dst_id, <props>) one join table per relationship type,
                                        both columns FK -> node(node_id)

Column set per entity table = exactly the property union that
db.schema.nodeTypeProperties() reports for that label, i.e. the same property
list the KG-grounded schema card advertises, so neither condition sees a field
the other cannot.

Value encoding is chosen so that canonicalisation parity holds with the graph
path (bench_common.canon): strings/ints/floats round-trip natively, booleans are
stored as TEXT 'true'/'false' (SQLite has no boolean type; scoring casefolds, so
'true' == Neo4j's True), list properties are stored as the canon JSON array text
(queryable with the built-in json1 functions), and NULL canonises to 'None' on
both sides. Nothing is aggregated, dropped or renamed.

Outputs (relative to this directory; the SQLite files are not tracked):
  relational/{WG}.sqlite
  relational/manifest.json        per-table row counts + graph counts
  sql_schema_cards.json                   prompt cards (mirror of schema_cards.json)

Usage:
  python3 build_relational_db.py --wg RAN1            # one WG
  python3 build_relational_db.py                      # all five
  python3 build_relational_db.py --cards-only         # regenerate cards only
  python3 build_relational_db.py --verify-only        # recount, no rebuild
"""
import argparse
import json
import os
import re
import sqlite3
import sys
import time
from collections import defaultdict
from pathlib import Path

import bench_common as bc

HERE = Path(__file__).parent
OUT_DIR = HERE / 'relational'
CARDS_OUT = HERE / 'sql_schema_cards.json'
KG_CARDS = HERE / 'schema_cards.json'
WGS = ['RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5']
BATCH = 4000

# identical ordering rule to schema_cards.py so the two cards surface the same
# fields in the same order (fairness: matched information content)
PRIORITY_PROPS = ['tdocNumber', 'crNumber', 'specNumber', 'sectionId', 'sectionNumber',
                  'title', 'name', 'meetingNumber', 'canonicalMeetingNumber',
                  'meetingNumberInt', 'companyName', 'releaseCode', 'status', 'tableNumber']
CARD_PROP_CAP = 12          # same cap schema_cards.build_card uses
INDEX_SUFFIX = re.compile(r'(Number|Id|Code|Name|Type|Release|Status|Key|Uri|URI)$')


# ---------------------------------------------------------------- schema probe
def probe_schema(session):
    """Live inventory: {label: {prop: sqlite_type}}, {relType: {prop: type}},
    and the (srcLabel, TYPE, dstLabel) patterns (same source as the KG card)."""
    ntypes = defaultdict(lambda: defaultdict(set))
    for r in session.run('CALL db.schema.nodeTypeProperties()'):
        pk = r.get('propertyName')
        if not pk:
            continue
        for lb in (r.get('nodeLabels') or []):
            ntypes[lb][pk] |= set(r.get('propertyTypes') or [])
    rtypes = defaultdict(lambda: defaultdict(set))
    for r in session.run('CALL db.schema.relTypeProperties()'):
        rt = (r.get('relType') or '').strip(':`')
        pk = r.get('propertyName')
        if rt and pk:
            rtypes[rt][pk] |= set(r.get('propertyTypes') or [])
    # every relationship type present, including property-less ones
    all_rel_types = [r['t'] for r in session.run(
        'MATCH ()-[r]->() RETURN DISTINCT type(r) AS t ORDER BY t')]
    for rt in all_rel_types:
        rtypes.setdefault(rt, defaultdict(set))
    pats = set()
    rec = session.run('CALL db.schema.visualization()').single()
    nodes = {n.element_id: (list(n.labels)[0] if n.labels else '?') for n in rec['nodes']}
    for rel in rec['relationships']:
        pats.add((nodes.get(rel.start_node.element_id, '?'), rel.type,
                  nodes.get(rel.end_node.element_id, '?')))
    labels = {lb: {p: sqlite_type(ts) for p, ts in props.items()}
              for lb, props in ntypes.items()}
    # a label may exist with zero properties -> still needs a table
    for lb in [r['l'] for r in session.run(
            'MATCH (n) UNWIND labels(n) AS l RETURN DISTINCT l AS l ORDER BY l')]:
        labels.setdefault(lb, {})
    rels = {rt: {p: sqlite_type(ts) for p, ts in props.items()}
            for rt, props in rtypes.items()}
    return labels, rels, sorted(pats)


def sqlite_type(types):
    """Neo4j reported property types -> SQLite column type.

    Arrays and booleans become TEXT (JSON array / 'true'|'false'); a property
    with more than one observed type gets no affinity (ANY) so the native value
    is stored verbatim and canonicalisation still matches the graph.
    """
    ts = {t for t in types if t}
    if not ts:
        return 'TEXT'
    if len(ts) > 1:
        return 'ANY'
    t = next(iter(ts))
    if t in ('Long', 'Integer'):
        return 'INTEGER'
    if t in ('Double', 'Float'):
        return 'REAL'
    return 'TEXT'          # String, *Array, Boolean, temporal, Point


# ---------------------------------------------------------------- value coding
def to_sqlite(v):
    if v is None or isinstance(v, (int, float, str)) and not isinstance(v, bool):
        return v
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, (list, tuple, dict)):
        return bc.canon(list(v) if isinstance(v, tuple) else v)
    return str(v)          # neo4j temporal / spatial types


# ---------------------------------------------------------------- ddl
def q(name):
    return '"' + name.replace('"', '""') + '"'


def entity_ddl(label, props):
    cols = ['node_id INTEGER PRIMARY KEY REFERENCES node(node_id)']
    for p in order_props(list(props)):
        cols.append(f'{q(p)} {props[p]}')
    return f'CREATE TABLE {q(label)} (\n  ' + ',\n  '.join(cols) + '\n)'


def rel_ddl(rt, props):
    cols = ['src_id INTEGER NOT NULL REFERENCES node(node_id)',
            'dst_id INTEGER NOT NULL REFERENCES node(node_id)']
    for p in sorted(props):
        cols.append(f'{q(p)} {props[p]}')
    return f'CREATE TABLE {q("rel_" + rt)} (\n  ' + ',\n  '.join(cols) + '\n)'


def order_props(plist):
    pri = [p for p in PRIORITY_PROPS if p in plist]
    rest = sorted(p for p in plist if p not in PRIORITY_PROPS)
    return pri + rest


# ---------------------------------------------------------------- build
def build_wg(wg, driver, rebuild=True):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dbp = OUT_DIR / f'{wg}.sqlite'
    with driver.session() as s:
        labels, rels, pats = probe_schema(s)
    if rebuild and dbp.exists():
        dbp.unlink()
    con = sqlite3.connect(str(dbp))
    con.executescript('PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF; '
                      'PRAGMA temp_store=MEMORY; PRAGMA cache_size=-400000;')
    con.execute('CREATE TABLE node (node_id INTEGER PRIMARY KEY, labels TEXT NOT NULL)')
    for lb in sorted(labels):
        con.execute(entity_ddl(lb, labels[lb]))
    for rt in sorted(rels):
        con.execute(rel_ddl(rt, rels[rt]))
    con.commit()

    ent_cols = {lb: order_props(list(labels[lb])) for lb in labels}
    ent_sql = {lb: f'INSERT INTO {q(lb)} (node_id{"".join("," + q(c) for c in ent_cols[lb])}) '
                   f'VALUES ({",".join("?" * (1 + len(ent_cols[lb])))})' for lb in labels}
    t0 = time.time()
    n_nodes = 0
    buf = defaultdict(list)
    nbuf = []

    def flush():
        if nbuf:
            con.executemany('INSERT INTO node (node_id, labels) VALUES (?,?)', nbuf)
            nbuf.clear()
        for lb, rows in buf.items():
            if rows:
                con.executemany(ent_sql[lb], rows)
                rows.clear()

    with driver.session() as s:
        for rec in s.run('MATCH (n) RETURN id(n) AS i, labels(n) AS l, properties(n) AS p'):
            nid, labs, props = rec['i'], rec['l'], rec['p']
            nbuf.append((nid, bc.canon(labs)))
            for lb in labs:
                cols = ent_cols.get(lb)
                if cols is None:      # label appeared after the probe
                    continue
                buf[lb].append(tuple([nid] + [to_sqlite(props.get(c)) for c in cols]))
            n_nodes += 1
            if n_nodes % BATCH == 0:
                flush()
        flush()
    con.commit()
    print(f'  {wg}: {n_nodes} nodes in {time.time()-t0:.0f}s', flush=True)

    n_rels = 0
    for rt in sorted(rels):
        rcols = sorted(rels[rt])
        ins = (f'INSERT INTO {q("rel_" + rt)} (src_id,dst_id'
               f'{"".join("," + q(c) for c in rcols)}) '
               f'VALUES ({",".join("?" * (2 + len(rcols)))})')
        rows = []
        with driver.session() as s:
            for rec in s.run(f'MATCH (a)-[r:{q(rt).replace(chr(34), "`")}]->(b) '
                             'RETURN id(a) AS s, id(b) AS d, properties(r) AS p'):
                p = rec['p']
                rows.append(tuple([rec['s'], rec['d']] + [to_sqlite(p.get(c)) for c in rcols]))
                if len(rows) >= BATCH:
                    con.executemany(ins, rows)
                    n_rels += len(rows)
                    rows = []
            if rows:
                con.executemany(ins, rows)
                n_rels += len(rows)
        con.commit()
    print(f'  {wg}: {n_rels} relationships in {time.time()-t0:.0f}s', flush=True)

    # ---- indexes (both conditions must be able to answer inside the timeout)
    n_idx = 0
    for rt in sorted(rels):
        t = 'rel_' + rt
        con.execute(f'CREATE INDEX {q("ix_" + t + "_src")} ON {q(t)} (src_id)')
        con.execute(f'CREATE INDEX {q("ix_" + t + "_dst")} ON {q(t)} (dst_id)')
        n_idx += 2
    for lb in sorted(labels):
        for c in labels[lb]:
            if c in PRIORITY_PROPS or INDEX_SUFFIX.search(c):
                con.execute(f'CREATE INDEX {q("ix_" + lb + "_" + c)} ON {q(lb)} ({q(c)})')
                n_idx += 1
    con.execute('CREATE INDEX ix_node_labels ON node (labels)')
    n_idx += 1
    con.commit()
    con.executescript('PRAGMA optimize; ANALYZE;')
    con.commit()
    con.close()
    print(f'  {wg}: {n_idx} indexes, {dbp.stat().st_size/1e9:.2f} GB, '
          f'{time.time()-t0:.0f}s total', flush=True)
    return labels, rels, pats


# ---------------------------------------------------------------- verify
def verify_wg(wg, driver):
    """Row-count parity per table against the graph (no sampling)."""
    dbp = OUT_DIR / f'{wg}.sqlite'
    con = sqlite3.connect(f'file:{dbp}?mode=ro', uri=True)
    rep = {'db_bytes': dbp.stat().st_size, 'labels': {}, 'rels': {}, 'mismatches': []}
    with driver.session() as s:
        g_nodes = s.run('MATCH (n) RETURN count(n) AS c').single()['c']
        g_rels = s.run('MATCH ()-[r]->() RETURN count(r) AS c').single()['c']
        g_lab = {r['l']: r['c'] for r in s.run(
            'MATCH (n) UNWIND labels(n) AS l RETURN l, count(*) AS c')}
        g_rt = {r['t']: r['c'] for r in s.run(
            'MATCH ()-[r]->() RETURN type(r) AS t, count(*) AS c')}
    s_nodes = con.execute('SELECT count(*) FROM node').fetchone()[0]
    rep['nodes'] = {'graph': g_nodes, 'sqlite': s_nodes}
    if g_nodes != s_nodes:
        rep['mismatches'].append(f'node {g_nodes} != {s_nodes}')
    tot_rel = 0
    for lb, c in sorted(g_lab.items()):
        sc = con.execute(f'SELECT count(*) FROM {q(lb)}').fetchone()[0]
        rep['labels'][lb] = {'graph': c, 'sqlite': sc}
        if c != sc:
            rep['mismatches'].append(f'{lb} {c} != {sc}')
    for rt, c in sorted(g_rt.items()):
        sc = con.execute(f'SELECT count(*) FROM {q("rel_" + rt)}').fetchone()[0]
        rep['rels'][rt] = {'graph': c, 'sqlite': sc}
        tot_rel += sc
        if c != sc:
            rep['mismatches'].append(f'rel_{rt} {c} != {sc}')
    rep['relationships'] = {'graph': g_rels, 'sqlite': tot_rel}
    if g_rels != tot_rel:
        rep['mismatches'].append(f'relationships {g_rels} != {tot_rel}')
    con.close()
    print(f'  {wg}: nodes {g_nodes}/{s_nodes}, rels {g_rels}/{tot_rel}, '
          f'mismatches={len(rep["mismatches"])}', flush=True)
    return rep


# ---------------------------------------------------------------- prompt card
def build_card(wg, labels, rels, pats):
    """Mirror of schema_cards.build_card: same labels, same property order, same
    12-property cap, same relationship pattern list, rendered as SQL objects."""
    lines = [f'# SQLite schema for 3GPP {wg} process database',
             '# Relational mirror of the process records: one table per entity class,',
             '# one join table per relationship type.',
             '#',
             '# Conventions:',
             '#  * every entity has an integer node_id (PRIMARY KEY of its class table);',
             '#    an entity belonging to several classes appears in each class table',
             '#    under the same node_id. Table node(node_id, labels) lists all',
             '#    entities; labels is a JSON array of that entity\'s class names.',
             '#  * join tables rel_<TYPE>(src_id, dst_id) hold one row per',
             '#    relationship; both columns are foreign keys to node(node_id) and',
             '#    join to any class table on its node_id.',
             '#  * BOOLEAN columns are TEXT \'true\'/\'false\'; list-valued columns are',
             '#    TEXT holding a JSON array (use json_each(col) if you need members).',
             '#  * standard SQLite is available (JOIN, GROUP BY, aggregate functions,',
             '#    ORDER BY, LIMIT, WITH / WITH RECURSIVE, json1 functions).',
             '',
             '## Entity tables (with columns)']
    for lb in sorted(labels):
        ps = order_props(list(labels[lb]))
        shown = ps[:CARD_PROP_CAP]
        more = f' (+{len(ps)-CARD_PROP_CAP} more)' if len(ps) > CARD_PROP_CAP else ''
        cols = ', '.join(['node_id'] + [f'{p} {labels[lb][p]}' for p in shown])
        lines.append(f'- "{lb}"({cols}){more}')
    lines += ['', '## Join tables (src_id -> dst_id, both REFERENCES node(node_id))']
    seen = set()
    for s, t, e in pats:
        extra = ''
        if rels.get(t) and t not in seen:      # announce extra columns once per type
            extra = f'  [extra columns: {", ".join(sorted(rels[t]))}]'
        seen.add(t)
        lines.append(f'- "rel_{t}": "{s}".node_id -> "{e}".node_id{extra}')
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--wg', nargs='*', default=WGS)
    ap.add_argument('--cards-only', action='store_true')
    ap.add_argument('--verify-only', action='store_true')
    args = ap.parse_args()

    bc.load_env()
    if not os.environ.get('NEO4J_PASSWORD'):
        print('NEO4J_PASSWORD not set', file=sys.stderr)
        return 2
    from neo4j import GraphDatabase
    pw = os.environ['NEO4J_PASSWORD']

    cards = {}
    if CARDS_OUT.exists():
        cards = json.loads(CARDS_OUT.read_text())
    manifest = {}
    mpath = OUT_DIR / 'manifest.json'
    if mpath.exists():
        manifest = json.loads(mpath.read_text())

    kg = json.loads(KG_CARDS.read_text())
    for wg in args.wg:
        print(f'=== {wg}', flush=True)
        drv = GraphDatabase.driver(f'bolt://localhost:{bc.NEO4J_PORTS[wg]}',
                                   auth=('neo4j', pw), notifications_min_severity='OFF')
        try:
            if args.cards_only or args.verify_only:
                with drv.session() as s:
                    labels, rels, pats = probe_schema(s)
            else:
                labels, rels, pats = build_wg(wg, drv)
            if not args.cards_only:
                OUT_DIR.mkdir(parents=True, exist_ok=True)
                manifest[wg] = verify_wg(wg, drv)
                mpath.write_text(json.dumps(manifest, indent=2))
        finally:
            drv.close()
        card = build_card(wg, labels, rels, pats)
        # fairness check: identical label set and relationship-pattern set as the
        # KG card the graph condition was prompted with
        kg_labels = set(kg[wg]['labels'])
        kg_pats = {tuple(x) for x in kg[wg]['rels']}
        parity = {
            'labels_equal': kg_labels == set(labels),
            'patterns_equal': kg_pats == set(pats),
            'props_equal': all(set(kg[wg]['labels'][lb]) == set(labels[lb])
                               for lb in kg_labels & set(labels)),
            'kg_card_chars': len(kg[wg]['card']), 'sql_card_chars': len(card),
        }
        cards[wg] = {'tables': {lb: labels[lb] for lb in sorted(labels)},
                     'join_tables': {rt: rels[rt] for rt in sorted(rels)},
                     'patterns': [list(p) for p in pats],
                     'card': card, 'kg_card_parity': parity}
        print(f'  {wg}: card {len(card)} chars (KG card {parity["kg_card_chars"]}), '
              f'parity={parity["labels_equal"] and parity["patterns_equal"] and parity["props_equal"]}',
              flush=True)
    CARDS_OUT.write_text(json.dumps(cards, indent=2, ensure_ascii=False))
    print(f'-> {CARDS_OUT}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
