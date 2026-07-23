#!/usr/bin/env python3
"""load_released_kg.py — load a released per-WG TTL (kg/per_wg/RAN*-body.ttl) into a Neo4j property graph.

Materializes the released RDF back into a property graph so the full
SpectraCQ suite (624 Cypher CQs across the five RAN working groups) can be
re-executed from released artifacts only, without access to any operational KG.

Usage: python3 load_released_kg.py --ttl ../kg/per_wg/RAN1-body.ttl \
           --bolt bolt://localhost:7697 --user neo4j --password replaytest \
           [--report out.json]

Restoration rules (inverse of the export conventions documented in
kg/per_wg/README.md):
  * label: the TTL's rdf:type spectra:<Label> becomes the Neo4j label.
  * property key: the spectra:<key> local name, verbatim.
  * relationship: the export converted SCREAMING_SNAKE relationship types
      to camelCase predicates; the loader inverts this (insert '_' at each
      uppercase boundary, then uppercase). Round-trip self-check
      screaming_to_camel(camel_to_screaming(p)) == p aborts on mismatch.
  * node identity: one subject IRI == one node. The export serializes each
      source node exactly once at its canonical class IRI (a multi-label
      node emits several rdf:type triples under that single subject, not one
      subject per label), so distinct subject IRIs always denote distinct
      source nodes and are loaded as distinct nodes -- even when two share a
      business-id segment across an rdfs:subClassOf boundary (e.g. a genuine
      CR and a genuine Tdoc that happen to carry the same id): those are two
      different source nodes and must not be merged. The loader trusts the
      subject IRI verbatim and never re-canonicalizes onto the class root.
  * load key: the subject IRI is stored as a loader-only `iri` property
      (an auxiliary key that does not exist in the source KG).

TTL parser: a streaming parser for the regular subset emitted by the
  rdflib serializer (long \"\"\"literal\"\"\" multi-line strings, escapes,
  bare int/float/boolean, ^^datatype, ',' object lists). No dependencies
  beyond the neo4j driver.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

INST_RE = re.compile(
    r"^https://w3id\.org/spectra/inst/(?P<wg>[^/]+)/(?P<cls>[A-Za-z]+)/(?P<nid>.+)$"
)

ESCAPES = {
    't': '\t', 'b': '\b', 'n': '\n', 'r': '\r', 'f': '\f',
    '"': '"', "'": "'", '\\': '\\',
}


# ---------------------------------------------------------------- name maps
def screaming_to_camel(rel: str) -> str:
    """Same forward transform as export_per_wg_body_kg.py (round-trip verification)."""
    parts = rel.split("_")
    if not parts:
        return rel
    out = [parts[0].lower()]
    for p in parts[1:]:
        out.append(p[:1].upper() + p[1:].lower() if len(p) > 1 else p.upper())
    return "".join(out)


def camel_to_screaming(name: str) -> str:
    """camelCase → SCREAMING_SNAKE (inverse of screaming_to_camel). hasCr→HAS_CR, ccTo→CC_TO."""
    return re.sub(r"(?<=.)([A-Z])", r"_\1", name).upper()


def decode_rel_type(local: str) -> str:
    """TTL predicate local name → Neo4j rel type. Inverse of the exporter's rel_to_predicate.

    A reserved leading underscore (_) escapes predicates whose live type is
    already camelCase (definedInSection, disjointWith); the SCREAMING round-trip
    would lowercase-mangle them, so just the underscore is stripped and the name
    used verbatim. Others are SCREAMING_SNAKE, round-trip-checked via camel_to_screaming."""
    if local.startswith("_"):
        return local[1:]
    rel_type = camel_to_screaming(local)
    if screaming_to_camel(rel_type) != local:
        raise SystemExit(
            f"round-trip mismatch: {local} -> {rel_type} -> {screaming_to_camel(rel_type)}")
    return rel_type




# ---------------------------------------------------------------- TTL lexer
class StatementReader:
    """Stream statement-sized text chunks out of rdflib turtle output.

    Long literals (\"\"\") span multiple lines, so a per-line state machine
    detects 'line ends with . while outside a string' = end of statement.
    """

    def __init__(self, fh):
        self.fh = fh

    def __iter__(self):
        buf: list[str] = []
        in_long = False
        for line in self.fh:
            buf.append(line)
            in_long = self._scan(line, in_long)
            if not in_long:
                stripped = line.rstrip()
                if stripped.endswith("."):
                    yield "".join(buf)
                    buf = []
        if buf and "".join(buf).strip():
            raise ValueError("TTL ended inside an unterminated statement")

    @staticmethod
    def _scan(line: str, in_long: bool) -> bool:
        i, n = 0, len(line)
        while i < n:
            if in_long:
                j = line.find('"', i)
                k = line.find("\\", i)
                if k != -1 and (j == -1 or k < j):
                    i = k + 2  # escape pair
                    continue
                if j == -1:
                    return True  # long literal continues to end of line
                run = j
                while run < n and line[run] == '"':
                    run += 1
                if run - j >= 3:
                    in_long = False  # last 3 quotes of the run close it
                i = run
            else:
                c = line[i]
                if c == "<":
                    e = line.find(">", i)
                    i = (e + 1) if e != -1 else n
                elif c == '"':
                    if line.startswith('"""', i):
                        in_long = True
                        i += 3
                    else:  # short literal closes on the same line
                        i += 1
                        while i < n:
                            if line[i] == "\\":
                                i += 2
                            elif line[i] == '"':
                                i += 1
                                break
                            else:
                                i += 1
                else:
                    i += 1
        return in_long


def _unescape(s: str) -> str:
    if "\\" not in s:
        return s
    out = []
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c != "\\":
            out.append(c)
            i += 1
            continue
        e = s[i + 1]
        if e == "u":
            out.append(chr(int(s[i + 2:i + 6], 16)))
            i += 6
        elif e == "U":
            out.append(chr(int(s[i + 2:i + 10], 16)))
            i += 10
        else:
            out.append(ESCAPES.get(e, e))
            i += 2
    return "".join(out)


PNAME_RE = re.compile(r"([A-Za-z][\w-]*):([A-Za-z0-9_]*)")
NUM_RE = re.compile(r"[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?")


def tokenize(stmt: str):
    """statement string → token list. ('iri',v)/('pname',(p,l))/('lit',v)/
    ('punct',c)/('kw','a')"""
    toks = []
    i, n = 0, len(stmt)
    while i < n:
        c = stmt[i]
        if c in " \t\r\n":
            i += 1
            continue
        if c == "<":
            e = stmt.index(">", i)
            toks.append(("iri", stmt[i + 1:e]))
            i = e + 1
        elif c == '"':
            if stmt.startswith('"""', i):
                j = i + 3
                while True:
                    q = stmt.index('"', j)
                    b = stmt.find("\\", j, q)
                    if b != -1:
                        j = b + 2
                        continue
                    run = q
                    while run < n and stmt[run] == '"':
                        run += 1
                    if run - q >= 3:
                        # last 3 quotes of the run are the closer, the rest is content
                        val = stmt[i + 3:run - 3]
                        i = run
                        break
                    j = run
                toks.append(("lit", _unescape(val)))
            else:
                j = i + 1
                while True:
                    if stmt[j] == "\\":
                        j += 2
                    elif stmt[j] == '"':
                        break
                    else:
                        j += 1
                toks.append(("lit", _unescape(stmt[i + 1:j])))
                i = j + 1
            # datatype / lang tag (if any, ignore rather than attach to the last lit;
            # all body-TTL literals are plain, only the header's ^^xsd:date has one)
            if stmt.startswith("^^", i):
                i += 2
                if stmt[i] == "<":
                    i = stmt.index(">", i) + 1
                else:
                    m = PNAME_RE.match(stmt, i)
                    i = m.end()
            elif i < n and stmt[i] == "@":
                while i < n and stmt[i] not in " \t\r\n;,.":
                    i += 1
        elif c in ";,.":
            toks.append(("punct", c))
            i += 1
        elif c == "@":  # @prefix declaration
            toks.append(("at", stmt[i:].split(None, 1)[0]))
            i += len(toks[-1][1])
        elif stmt.startswith("true", i) and (i + 4 == n or not stmt[i + 4].isalnum()):
            toks.append(("lit", True))
            i += 4
        elif stmt.startswith("false", i) and (i + 5 == n or not stmt[i + 5].isalnum()):
            toks.append(("lit", False))
            i += 5
        else:
            m = PNAME_RE.match(stmt, i)
            if m:
                toks.append(("pname", (m.group(1), m.group(2))))
                i = m.end()
                continue
            if c == "a" and (i + 1 == n or stmt[i + 1] in " \t\r\n"):
                toks.append(("kw", "a"))
                i += 1
                continue
            m = NUM_RE.match(stmt, i)
            if m:
                txt = m.group(0)
                val = float(txt) if ("." in txt or "e" in txt or "E" in txt) else int(txt)
                toks.append(("lit", val))
                i = m.end()
                continue
            raise ValueError(f"unexpected char {c!r} at {i} in: {stmt[:120]!r}")
    return toks


def parse_statement(stmt: str):
    """statement → (subject_iri, [(pred, [obj,...]), ...]) or None (@prefix)."""
    toks = tokenize(stmt)
    if not toks or toks[0][0] == "at":
        return None
    kind, subj = toks[0]
    if kind != "iri":
        raise ValueError(f"subject is not IRI: {toks[0]}")
    preds = []
    i = 1
    while i < len(toks):
        t = toks[i]
        if t == ("punct", "."):
            break
        if t[0] == "kw":  # 'a'
            pred = ("rdf", "type")
        elif t[0] == "pname":
            pred = t[1]
        else:
            raise ValueError(f"bad predicate token {t} in {stmt[:120]!r}")
        i += 1
        objs = []
        while True:
            ot = toks[i]
            if ot[0] in ("iri", "lit", "pname"):
                objs.append(ot)
            else:
                raise ValueError(f"bad object token {ot}")
            i += 1
            if toks[i] == ("punct", ","):
                i += 1
                continue
            break
        preds.append((pred, objs))
        if toks[i] == ("punct", ";"):
            i += 1
    return subj, preds


# ---------------------------------------------------------------- load core
def parse_ttl(ttl_path: Path):
    """Stream-parse the whole TTL into node/relationship collections."""
    nodes: dict[tuple, dict] = {}   # (cls, nid) -> {labels,set props,...}
    rels: set[tuple] = set()        # (aKey, REL_TYPE, bKey)
    stats = {"statements": 0, "skipped_subjects": 0, "prop_conflicts": [],
             "rel_pred_camel": Counter(), "class_subjects": Counter()}

    def key_of(iri: str):
        # Trust the subject IRI as-is (exporter already serialized the canonical class).
        # Renormalizing to the subClassOf root would merge distinct nodes sharing an id.
        m = INST_RE.match(iri)
        if not m:
            return None
        cls, nid = m.group("cls"), m.group("nid")
        return (cls, nid), cls

    t0 = time.time()
    with open(ttl_path, encoding="utf-8") as fh:
        for stmt in StatementReader(fh):
            parsed = parse_statement(stmt)
            if parsed is None:
                continue
            stats["statements"] += 1
            subj, preds = parsed
            sk = key_of(subj)
            if sk is None:  # header ontology node etc.
                stats["skipped_subjects"] += 1
                continue
            skey, scls = sk
            rec = nodes.setdefault(skey, {"labels": set(), "props": {}})
            for (prefix, local), objs in preds:
                if prefix == "rdf" and local == "type":
                    for ot, ov in objs:
                        if ot == "pname" and ov[0] == "spectra":
                            rec["labels"].add(ov[1])
                            stats["class_subjects"][ov[1]] += 1
                    continue
                if prefix != "spectra":
                    continue  # dcterms/rdfs/owl are header-only
                lits = [ov for ot, ov in objs if ot == "lit"]
                iris = [ov for ot, ov in objs if ot == "iri"]
                if lits:
                    val = lits[0] if len(lits) == 1 else sorted(map(str, lits))
                    old = rec["props"].get(local)
                    if old is None:
                        rec["props"][local] = val
                    elif old != val and len(stats["prop_conflicts"]) < 200:
                        stats["prop_conflicts"].append(
                            {"node": list(skey), "key": local,
                             "kept": str(old)[:80], "dropped": str(val)[:80]})
                for oiri in iris:
                    ok = key_of(oiri)
                    if ok is None:
                        continue
                    rel_type = decode_rel_type(local)
                    stats["rel_pred_camel"][local] += 1
                    rels.add((skey, rel_type, ok[0]))
            if stats["statements"] % 20000 == 0:
                print(f"  parsed {stats['statements']:>7,} statements "
                      f"({time.time()-t0:,.0f}s, nodes={len(nodes):,}, "
                      f"rels={len(rels):,})", flush=True)
    print(f"  parse done: {stats['statements']:,} statements, "
          f"{len(nodes):,} merged nodes, {len(rels):,} unique rels "
          f"({time.time()-t0:,.0f}s)")
    return nodes, rels, stats


def load_neo4j(bolt: str, user: str, password: str,
               nodes: dict, rels: set, batch: int):
    from neo4j import GraphDatabase

    drv = GraphDatabase.driver(bolt, auth=(user, password))
    all_labels = sorted({l for r in nodes.values() for l in r["labels"]})
    with drv.session() as s:
        for lab in all_labels:
            s.run(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:`{lab}`) "
                  f"REQUIRE n.iri IS UNIQUE").consume()
        s.run("CALL db.awaitIndexes(300)").consume()

        # --- nodes: grouped per label set. Keys are unique subject IRIs, so CREATE suffices.
        groups: dict[frozenset, list] = defaultdict(list)
        for (cls, nid), rec in nodes.items():
            iri = f"https://w3id.org/spectra/inst/_/{cls}/{nid}"
            props = dict(rec["props"])
            if "iri" in props:
                print("  [warn] data property 'iri' collides with loader key, "
                      "preserved as _orig_iri")
                props["_orig_iri"] = props.pop("iri")
            props["iri"] = iri
            groups[frozenset(rec["labels"])].append(props)
        t0 = time.time()
        n_created = 0
        for labset, rows in groups.items():
            labels = ":".join(f"`{l}`" for l in sorted(labset))
            q = f"UNWIND $rows AS row CREATE (n:{labels}) SET n = row"
            for i in range(0, len(rows), batch):
                s.run(q, rows=rows[i:i + batch]).consume()
                n_created += len(rows[i:i + batch])
            print(f"  [nodes] {sorted(labset)} {len(rows):,} "
                  f"(total {n_created:,}, {time.time()-t0:,.0f}s)", flush=True)

        # --- rels: grouped by (type, labelA, labelB)
        # MATCH labels must actually exist on the node. key[0] is the canonical
        # class the exporter serialized, so it is always in the label set.
        def match_label(key: tuple) -> str:
            labs = nodes[key]["labels"]
            return key[0] if key[0] in labs else sorted(labs)[0]

        rgroups: dict[tuple, list] = defaultdict(list)
        missing_endpoints = 0
        for (akey, rt, bkey) in rels:
            if akey not in nodes or bkey not in nodes:
                missing_endpoints += 1
                continue
            ia = f"https://w3id.org/spectra/inst/_/{akey[0]}/{akey[1]}"
            ib = f"https://w3id.org/spectra/inst/_/{bkey[0]}/{bkey[1]}"
            rgroups[(rt, match_label(akey), match_label(bkey))].append(
                {"a": ia, "b": ib})
        if missing_endpoints:
            print(f"  [warn] rels skipped for missing endpoints: {missing_endpoints:,}")
        r_created = 0
        t0 = time.time()
        for (rt, al, bl), rows in sorted(rgroups.items()):
            q = (f"UNWIND $rows AS row "
                 f"MATCH (a:`{al}` {{iri: row.a}}) "
                 f"MATCH (b:`{bl}` {{iri: row.b}}) "
                 f"CREATE (a)-[:`{rt}`]->(b)")
            for i in range(0, len(rows), batch):
                s.run(q, rows=rows[i:i + batch]).consume()
            r_created += len(rows)
            print(f"  [rels] {rt:28s} {al}->{bl} {len(rows):>9,} "
                  f"(total {r_created:,}, {time.time()-t0:,.0f}s)", flush=True)

        # --- measured counts
        label_counts = {
            lab: s.run(f"MATCH (n:`{lab}`) RETURN count(n) AS c").single()["c"]
            for lab in all_labels}
        rel_counts = {
            row["t"]: row["c"] for row in
            s.run("MATCH ()-[r]->() RETURN type(r) AS t, count(r) AS c "
                  "ORDER BY t")}
        total_nodes = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
    drv.close()
    return {"total_nodes": total_nodes, "label_counts": label_counts,
            "rel_counts": rel_counts}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ttl", required=True, type=Path)
    ap.add_argument("--bolt", required=True)
    ap.add_argument("--user", default="neo4j")
    ap.add_argument("--password", required=True)
    ap.add_argument("--batch-size", type=int, default=2000)
    ap.add_argument("--report", type=Path, default=None)
    args = ap.parse_args()

    print(f"parsing {args.ttl} …")
    nodes, rels, stats = parse_ttl(args.ttl)

    print(f"loading into {args.bolt} …")
    counts = load_neo4j(args.bolt, args.user, args.password,
                        nodes, rels, args.batch_size)

    # cross-check against TTL inventory
    expected_rels = {decode_rel_type(k): v
                     for k, v in stats["rel_pred_camel"].items()}
    mismatch = {
        "labels": {l: {"ttl_subjects": stats["class_subjects"][l],
                       "neo4j": counts["label_counts"].get(l, 0)}
                   for l in stats["class_subjects"]
                   if stats["class_subjects"][l] != counts["label_counts"].get(l, 0)},
        "rels": {t: {"ttl": expected_rels[t],
                     "neo4j": counts["rel_counts"].get(t, 0)}
                 for t in expected_rels
                 if expected_rels[t] != counts["rel_counts"].get(t, 0)},
    }
    report = {
        "ttl": str(args.ttl), "bolt": args.bolt,
        "parse_stats": {"statements": stats["statements"],
                        "nodes": len(nodes),
                        "unique_rel_triples": len(rels),
                        "prop_conflicts_sample": stats["prop_conflicts"][:20],
                        "prop_conflict_count": len(stats["prop_conflicts"])},
        "ttl_inventory": {"class_subjects": dict(stats["class_subjects"]),
                          "rel_predicates_camel": dict(stats["rel_pred_camel"])},
        "neo4j_counts": counts,
        "inventory_mismatch": mismatch,
    }
    print(json.dumps({"total_nodes": counts["total_nodes"],
                      "inventory_mismatch": mismatch},
                     indent=2, ensure_ascii=False))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"report -> {args.report}")
    if mismatch["labels"] or mismatch["rels"]:
        print("[warn] TTL inventory and Neo4j counts disagree - check mismatch above")
        sys.exit(2)


if __name__ == "__main__":
    main()
