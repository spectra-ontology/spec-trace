#!/usr/bin/env python3
"""verify_benchmark.py — two-mode verifier for the released SPECTRA artifacts.

The released one-command verifier (``release_package/tests/verify_release.py``)
answers a narrow question: *are the shipped files present, parseable, and in
agreement with the counts the paper prints?* It re-reads recorded verdicts. It
never re-derives an answer, so it cannot detect a graph/query/gold combination
that has silently stopped producing the published answers.

This script keeps that cheap check and adds the missing one:

  --quick  Artifact-integrity mode. Delegates to the shipped release verifier
           (presence, RDF/SHACL parse, class & property counts, benchmark
           cardinalities, manifest reference resolution, per-WG file inventory)
           and additionally verifies every checksum the release itself ships
           (Croissant ``sha256`` entries) plus the shipped file counts. No
           database, no query execution.

  --full   Answer-reproduction mode. Wipes a scratch Neo4j, reloads a released
           per-WG body TTL with the SHIPPED loader, re-executes every released
           reference Cypher query against that fresh store, canonicalizes the
           result (positional column identity, datatype normalization, row
           sorting) and compares it against the released gold answer key at two
           levels: the published primary-value set + row count, and the full
           multi-column row multiset. Everything except the gold key itself is
           recomputed from the released bytes.

Scope honesty: --full reloads and re-queries whichever working groups are named
by ``--wg``. A run that covers fewer than all five WGs is recorded as a partial
reproduction, with the covered scope written into the output JSON; the mode
itself is complete and takes ``--wg all``.

Outputs: a report on stdout, plus machine-readable JSON under the directory
given by ``--out`` (default ``verifier_output/`` under the current working
directory): ``verifier_modes.json`` for either mode and, for --full,
``verifier_full_replay_detail.json`` together with the shipped loader's per-WG
reports. Nothing inside the release package is written by a run.

Usage:
  python3 release_package/tests/verify_benchmark.py --quick
  python3 release_package/tests/verify_benchmark.py --full --wg all \
      --bolt bolt://HOST:PORT --user neo4j --password PASSWORD

--full WIPES the database it connects to, so --bolt and --password have no
defaults: point it at a scratch instance, never at a store whose contents
matter.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RELEASE = REPO / "release_package"
QUICK_VERIFIER = RELEASE / "tests/verify_release.py"
CQ_ROOT = RELEASE / "cqs/spectra_cq_v2.0"
BENCH = CQ_ROOT / "benchmark.jsonl"
CYP_DIR = CQ_ROOT / "cypher"
SPARQL_DIR = CQ_ROOT / "sparql"
GOLD_DIR = CQ_ROOT / "gold"
CROISSANT = CQ_ROOT / "croissant.json"
TTL_DIR = RELEASE / "kg/per_wg"
LOADER = RELEASE / "pipeline/load_released_kg.py"

# Machine-readable output and the shipped loader's scratch reports. Relocated
# by --out; kept outside the release package so a run never mutates it.
OUT_DIR = Path("verifier_output")
OUT_JSON_NAME = "verifier_modes.json"
DETAIL_JSON_NAME = "verifier_full_replay_detail.json"

WGS = ["RAN1", "RAN2", "RAN3", "RAN4", "RAN5"]

# ---------------------------------------------------------------------------
# canonical form
# ---------------------------------------------------------------------------
# Stage 1 is the *same* base rendering the gold builder used, so that a value
# read back from Neo4j lands in the identical string space as the stored gold.
def _base_render(v):
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True, default=str)
    return str(v)


_NUM_RE = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$")
_ISO_RE = re.compile(
    r"^(?P<d>\d{4}-\d{2}-\d{2})"
    r"(?:[T ](?P<t>\d{2}:\d{2}:\d{2})(?P<f>\.\d+)?)?"
    r"(?P<z>Z|[+-]\d{2}:?\d{2})?$"
)
NULL_TOKEN = "\x00null"


def canon_strict(s) -> str:
    """Lossless canonical form: unicode form, whitespace runs and boolean/null
    spelling only. Two values that differ here differ as data, so this level can
    never hide a changed answer. Identifier case is preserved — 3GPP identifiers
    are case-bearing."""
    s = unicodedata.normalize("NFKC", str(s))
    s = re.sub(r"\s+", " ", s).strip()
    low = s.lower()
    if low in ("none", "null"):
        return NULL_TOKEN
    if low in ("true", "false"):
        return low
    return s


def canon_tolerant(s) -> str:
    """Strict form plus datatype-spelling normalization: numeric trailing zeros
    and exponent form, ISO-8601 fractional seconds and timezone spelling. This
    absorbs driver/serializer rendering differences across a reload.

    It is deliberately reported separately from the strict level, because a
    dotted identifier that happens to parse as a decimal (a spec number such as
    ``38.210``) is normalized as a number, so this level could in principle
    equate two values a reader would consider distinct. The strict count is
    therefore always published next to it."""
    s = canon_strict(s)
    if s == NULL_TOKEN or s in ("true", "false"):
        return s
    m = _ISO_RE.match(s)
    if m and (m.group("t") or m.group("z")):
        frac = (m.group("f") or "").rstrip("0").rstrip(".")
        tz = m.group("z") or ""
        if tz == "Z":
            tz = "+00:00"
        elif tz and ":" not in tz:
            tz = tz[:3] + ":" + tz[3:]
        out = m.group("d")
        if m.group("t"):
            out += "T" + m.group("t") + frac
        return out + tz
    if _NUM_RE.match(s):
        try:
            d = Decimal(s).normalize()
            if d == d.to_integral_value():
                d = d.quantize(Decimal(1))
            return format(d, "f")
        except (InvalidOperation, ValueError):
            return s
    return s


def norm_alias(c: str) -> str:
    """Alias-insensitive column identity: drop backticks, binding-variable
    prefix and case, so ``t.tdocNumber`` / ``T.TdocNumber`` / ``tdocNumber``
    collapse. Used for reporting alias drift only — the value comparison is
    positional and therefore alias-independent by construction."""
    c = str(c).replace("`", "").strip().lower()
    return c.rsplit(".", 1)[-1]


def canon_rows(rows: list[dict], order: list[str], render) -> list[tuple]:
    """Row multiset in canonical form: values in the given column order, each
    canonicalized, rows sorted so that result ordering never matters."""
    out = [tuple(render(r.get(c)) for c in order) for r in rows]
    return sorted(out)


_JSON_LIST_RE = re.compile(r"^\[.*\]$", re.S)


def collection_order_insensitive(s: str) -> str:
    """Sort the elements of a rendered JSON array.

    Cypher's ``collect()`` has no defined element order unless the query orders
    its input, so a reload can return the same collection in a different
    sequence. This variant is applied only in a clearly labelled second pass, so
    that queries whose ordering IS meaningful stay visible in the strict count.
    """
    if not _JSON_LIST_RE.match(s.strip()):
        return s
    try:
        v = json.loads(s)
    except Exception:  # noqa: BLE001
        return s
    if not isinstance(v, list):
        return s
    return json.dumps(sorted(v, key=lambda x: json.dumps(x, sort_keys=True, default=str)),
                      ensure_ascii=False, sort_keys=True, default=str)


# ---------------------------------------------------------------------------
# quick mode
# ---------------------------------------------------------------------------
def sha256_file(p: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def croissant_checksums() -> list[dict]:
    """Every checksum the release itself ships (Croissant FileObject sha256)."""
    checks = []
    if not CROISSANT.exists():
        return checks
    d = json.loads(CROISSANT.read_text())
    for dist in d.get("distribution", []):
        want = dist.get("sha256")
        url = dist.get("contentUrl")
        if not (want and url):
            continue
        p = CQ_ROOT / url
        if not p.exists():
            checks.append({"name": f"croissant sha256 {url}", "pass": False,
                           "detail": "file missing"})
            continue
        got = sha256_file(p)
        checks.append({"name": f"croissant sha256 {url}", "pass": got == want,
                       "detail": "match" if got == want else f"got {got[:16]}… want {want[:16]}…"})
    return checks


def file_count_checks() -> list[dict]:
    """Shipped file counts that the benchmark's own cardinality claims imply."""
    out = []
    for label, pattern, expected in [
        ("cypher/*.cypher", "cypher/*.cypher", 624),
        ("sparql/*.rq", "sparql/*.rq", 142),
        ("gold/RAN*_gold.json", "gold/RAN*_gold.json", 5),
    ]:
        n = len(list(CQ_ROOT.glob(pattern)))
        out.append({"name": f"file count {label} = {expected}", "pass": n == expected,
                    "detail": f"actual {n}"})
    return out


def run_quick() -> dict:
    """Delegate to the shipped verifier, then add checksum + file-count checks."""
    t0 = time.perf_counter()
    proc = subprocess.run([sys.executable, str(QUICK_VERIFIER)],
                          capture_output=True, text=True)
    delegated_s = time.perf_counter() - t0
    lines = proc.stdout.splitlines()
    passed = [l for l in lines if "[PASS]" in l]
    failed = [l for l in lines if "[FAIL]" in l]
    skipped = [l for l in lines if "[SKIP]" in l]

    extra = croissant_checksums() + file_count_checks()
    elapsed = time.perf_counter() - t0

    return {
        "mode": "quick",
        "what_it_verifies": [
            "shipped files exist and parse (ontology TTL, SHACL shapes, examples)",
            "SHACL conformance of the bundled instantiation and process-KG snippets",
            "one end-to-end SPARQL example returns its expected row (in-memory rdflib)",
            "benchmark cardinalities recorded in questions.json / benchmark.jsonl / held / gold summary",
            "class, property and axiom counts against validation/structural_metrics.json",
            "validation-manifest JSON references resolve",
            "synthetic-vs-verbatim naming policy in the example and CQ sets",
            "release directory inventory and per-WG TTL size floors",
            "every checksum the release ships (Croissant sha256 FileObject entries)",
            "shipped file counts (Cypher, SPARQL, per-WG gold)",
        ],
        "what_it_does_not_verify": [
            "no database is started, no Cypher is executed",
            "gold answer sets are read as recorded, never re-derived",
        ],
        "delegated_script": str(QUICK_VERIFIER.relative_to(REPO)),
        "delegated_exit_code": proc.returncode,
        "delegated_checks": len(passed) + len(failed),
        "delegated_passed": len(passed),
        "delegated_failed": len(failed),
        "delegated_skipped": len(skipped),
        "delegated_elapsed_s": round(delegated_s, 2),
        "added_checks": len(extra),
        "added_passed": sum(1 for c in extra if c["pass"]),
        "added_failed": sum(1 for c in extra if not c["pass"]),
        "added_detail": extra,
        "checks_total": len(passed) + len(failed) + len(extra),
        "passed": len(passed) + sum(1 for c in extra if c["pass"]),
        "failed": len(failed) + sum(1 for c in extra if not c["pass"]),
        "elapsed_s": round(elapsed, 2),
        "failed_names": [l.strip() for l in failed]
                        + [c["name"] for c in extra if not c["pass"]],
    }


# ---------------------------------------------------------------------------
# full mode
# ---------------------------------------------------------------------------
def wipe(bolt: str, user: str, pw: str) -> None:
    """Leave the scratch store empty: drop constraints, then delete all nodes."""
    from neo4j import GraphDatabase
    drv = GraphDatabase.driver(bolt, auth=(user, pw))
    with drv.session() as s:
        for r in list(s.run("SHOW CONSTRAINTS YIELD name RETURN name")):
            s.run(f"DROP CONSTRAINT `{r['name']}` IF EXISTS").consume()
        while True:
            c = s.run("MATCH (n) WITH n LIMIT 50000 "
                      "DETACH DELETE n RETURN count(n) AS c").single()["c"]
            if c == 0:
                break
        left = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
    drv.close()
    if left:
        raise RuntimeError(f"scratch store not empty after wipe: {left} nodes")


def load_released(wg: str, bolt: str, user: str, pw: str, batch: int) -> dict:
    """Load the released body TTL with the SHIPPED loader; return its report."""
    ttl = TTL_DIR / f"{wg}-body.ttl"
    if not ttl.exists():
        raise FileNotFoundError(
            f"{ttl} absent — the body TTLs are a Zenodo deposit "
            f"(see {TTL_DIR / 'README.md'}); download them for --full")
    report_dir = OUT_DIR / "loader_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{wg.lower()}_load_report.json"
    cmd = [sys.executable, str(LOADER), "--ttl", str(ttl), "--bolt", bolt,
           "--user", user, "--password", pw, "--batch-size", str(batch),
           "--report", str(report_path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"shipped loader failed for {wg}: {r.stderr[-800:]}")
    return json.loads(report_path.read_text())


def load_gold(wg: str) -> dict:
    """Per-WG gold with full rows, keyed by released CQ id (``{WG}_P{n}_{id}``)."""
    p = GOLD_DIR / f"{wg}_gold.json"
    if not p.exists():
        return {}
    d = json.loads(p.read_text())
    out = {}
    for g in d.get("gold", []):
        out[f"{wg}_P{g['phase']}_{g['id']}"] = g
    return out


def compare_cq(sess, row: dict, gold_full: dict | None) -> dict:
    """Re-execute one released reference query and compare to the released gold.

    Level 1 (published gold key): canonical SET of the primary column plus the
    row count — exactly the pair the benchmark publishes per CQ.
    Level 2 (stronger): the canonical multiset of FULL rows across all returned
    columns, available whenever the per-WG gold row dump is not truncated.
    """
    cypher = (CYP_DIR / f"{row['id']}.cypher").read_text()
    rec = {"id": row["id"], "wg": row["wg"], "phase": row["phase"]}
    try:
        recs = list(sess.run(cypher))
    except Exception as e:  # noqa: BLE001
        rec.update(pass_l1=False, level2="error", error=f"{type(e).__name__}: {str(e)[:200]}")
        return rec

    cols = list(recs[0].keys()) if recs else []
    datas = [r.data() for r in recs]
    pcol = cols[0] if cols else None
    raw_got = [_base_render(d.get(pcol)) for d in datas] if pcol else []
    raw_gold = list(row.get("gold_primary_values") or [])

    got_rc = len(recs)
    gold_rc = int(row.get("gold_row_count"))
    rc_eq = got_rc == gold_rc

    def set_eq_at(fn) -> bool:
        return sorted({fn(v) for v in raw_got}) == sorted({fn(v) for v in raw_gold})

    eq_exact = sorted(set(raw_got)) == sorted(set(raw_gold))
    eq_strict = set_eq_at(canon_strict)
    eq_tolerant = set_eq_at(canon_tolerant)

    rec.update(rc_equal=rc_eq, got_rc=got_rc, gold_rc=gold_rc,
               got_n=len(set(raw_got)), gold_n=len(set(raw_gold)),
               set_equal_exact=eq_exact, set_equal_strict=eq_strict,
               set_equal_canonical=eq_tolerant,
               pass_l1=eq_tolerant and rc_eq,
               pass_l1_strict=eq_strict and rc_eq)

    # alias drift (reporting only — value comparison is positional)
    gold_cols = row.get("gold_columns") or []
    rec["alias_exact"] = list(cols) == list(gold_cols)
    rec["alias_normalized"] = [norm_alias(c) for c in cols] == [norm_alias(c) for c in gold_cols]

    if not eq_tolerant:
        gs = {canon_tolerant(v) for v in raw_gold}
        os_ = {canon_tolerant(v) for v in raw_got}
        rec["only_got"] = sorted(os_ - gs)[:8]
        rec["only_gold"] = sorted(gs - os_)[:8]

    # level 2: full multi-column row multiset
    if gold_full and gold_full.get("rows") is not None and not gold_full.get("truncated"):
        g_cols = gold_full.get("columns") or []
        if [norm_alias(c) for c in g_cols] != [norm_alias(c) for c in cols]:
            rec["level2"] = "column_shape_mismatch"
            rec["pass_l2"] = False
        else:
            rec["level2"] = "compared"

            def rows_eq(fn) -> bool:
                got = canon_rows(datas, cols, lambda v: fn(_base_render(v)))
                gold = canon_rows(gold_full["rows"], g_cols, fn)
                return Counter(got) == Counter(gold)

            rec["rows_equal_strict"] = rows_eq(canon_strict)
            rec["rows_equal_canonical"] = rows_eq(canon_tolerant)
            rec["rows_equal_collection_order_insensitive"] = rows_eq(
                lambda s: collection_order_insensitive(canon_tolerant(s)))
            rec["pass_l2"] = rec["rows_equal_canonical"]
            if not rec["pass_l2"]:
                got = Counter(canon_rows(datas, cols,
                                         lambda v: canon_tolerant(_base_render(v))))
                gold = Counter(canon_rows(gold_full["rows"], g_cols, canon_tolerant))
                rec["rows_only_got"] = [[x[:200] for x in t][:6]
                                        for t in list((got - gold).elements())[:2]]
                rec["rows_only_gold"] = [[x[:200] for x in t][:6]
                                         for t in list((gold - got).elements())[:2]]
                diff_cols = set()
                for t in list((got - gold).elements())[:20]:
                    for i, c in enumerate(cols):
                        if all(t[i] != g[i] for g in gold):
                            diff_cols.add(c)
                rec["rows_diff_columns"] = sorted(diff_cols)[:8]
    else:
        rec["level2"] = "truncated_gold" if (gold_full or {}).get("truncated") else "no_row_gold"

    return rec


def full_wg(wg: str, cqs: list[dict], bolt: str, user: str, pw: str,
            batch: int, limit: int | None) -> dict:
    from neo4j import GraphDatabase

    t0 = time.perf_counter()
    wipe(bolt, user, pw)
    t_wipe = time.perf_counter() - t0

    t1 = time.perf_counter()
    rep = load_released(wg, bolt, user, pw, batch)
    t_load = time.perf_counter() - t1

    nc = rep["neo4j_counts"]
    nodes = nc["total_nodes"]
    rels = sum(nc["rel_counts"].values())
    ps = rep["parse_stats"]
    load_checks = {
        "nodes_live_eq_parsed": nodes == ps["nodes"],
        "rels_live_eq_parsed": rels == ps["unique_rel_triples"],
        "label_inventory_matches_ttl": not rep.get("inventory_mismatch", {}).get("labels"),
        "rel_inventory_matches_ttl": not rep.get("inventory_mismatch", {}).get("rels"),
        "prop_conflicts": ps.get("prop_conflict_count", 0),
    }

    gold_full = load_gold(wg)
    todo = cqs[:limit] if limit else cqs

    t2 = time.perf_counter()
    results = []
    drv = GraphDatabase.driver(bolt, auth=(user, pw))
    with drv.session() as s:
        for row in todo:
            results.append(compare_cq(s, row, gold_full.get(row["id"])))
    drv.close()
    t_query = time.perf_counter() - t2

    l1 = sum(1 for r in results if r.get("pass_l1"))
    l2_cmp = [r for r in results if r.get("level2") == "compared"]
    l2_pass = sum(1 for r in l2_cmp if r.get("pass_l2"))
    by_phase = defaultdict(lambda: {"total": 0, "pass": 0})
    for r in results:
        by_phase[str(r["phase"])]["total"] += 1
        if r.get("pass_l1"):
            by_phase[str(r["phase"])]["pass"] += 1

    return {
        "wg": wg,
        "ttl": str((TTL_DIR / f"{wg}-body.ttl").relative_to(REPO)),
        "ttl_bytes": (TTL_DIR / f"{wg}-body.ttl").stat().st_size,
        "loaded_nodes": nodes,
        "loaded_relationships": rels,
        "load_checks": load_checks,
        "cqs_reexecuted": len(results),
        "l1_match": l1,
        "l1_mismatch": len(results) - l1,
        "l2_compared": len(l2_cmp),
        "l2_match": l2_pass,
        "l2_mismatch": len(l2_cmp) - l2_pass,
        "l2_skipped_truncated_gold": sum(1 for r in results if r.get("level2") == "truncated_gold"),
        "l2_skipped_no_row_gold": sum(1 for r in results if r.get("level2") == "no_row_gold"),
        "l1_match_strict": sum(1 for r in results if r.get("pass_l1_strict")),
        "l1_match_before_canonicalization": sum(1 for r in results if r.get("set_equal_exact")),
        "l2_match_strict": sum(1 for r in l2_cmp if r.get("rows_equal_strict")),
        "l2_match_collection_order_insensitive":
            sum(1 for r in l2_cmp if r.get("rows_equal_collection_order_insensitive")),
        "alias_exact": sum(1 for r in results if r.get("alias_exact")),
        "alias_normalized": sum(1 for r in results if r.get("alias_normalized")),
        "errors": sum(1 for r in results if r.get("level2") == "error"),
        "by_phase": {k: dict(v) for k, v in sorted(by_phase.items())},
        "seconds": {"wipe": round(t_wipe, 1), "load": round(t_load, 1),
                    "query": round(t_query, 1),
                    "total": round(t_wipe + t_load + t_query, 1)},
        "_results": results,
    }


def run_full(wgs: list[str], bolt: str, user: str, pw: str, batch: int,
             limit: int | None) -> tuple[dict, dict]:
    rows = [json.loads(l) for l in BENCH.read_text().splitlines() if l.strip()]
    by_wg = defaultdict(list)
    for o in rows:
        by_wg[o["wg"]].append(o)

    t0 = time.perf_counter()
    per_wg = {}
    for wg in wgs:
        if not by_wg.get(wg):
            continue
        print(f"=== {wg}: reload + re-execute {len(by_wg[wg])} released CQs ===", flush=True)
        r = full_wg(wg, by_wg[wg], bolt, user, pw, batch, limit)
        per_wg[wg] = r
        print(f"  {wg}: L1 {r['l1_match']}/{r['cqs_reexecuted']}  "
              f"L2 {r['l2_match']}/{r['l2_compared']}  "
              f"nodes={r['loaded_nodes']:,} rels={r['loaded_relationships']:,}  "
              f"{r['seconds']['total']}s (load {r['seconds']['load']}s)", flush=True)
    elapsed = time.perf_counter() - t0

    released_total = len(rows)
    reexec = sum(r["cqs_reexecuted"] for r in per_wg.values())
    l1 = sum(r["l1_match"] for r in per_wg.values())
    l2c = sum(r["l2_compared"] for r in per_wg.values())
    l2 = sum(r["l2_match"] for r in per_wg.values())
    covered = sorted(per_wg)
    partial = reexec < released_total

    summary = {
        "mode": "full",
        "what_it_verifies": [
            "scratch Neo4j is emptied (constraints dropped, zero nodes) before each load",
            "released per-WG body TTL is reparsed and reloaded by the SHIPPED loader",
            "live node/relationship counts equal the loader's independent parse counts",
            "every released reference Cypher query is re-executed against that fresh store",
            "results are canonicalized (positional columns, datatype normalization, row sorting)",
            "canonical primary-value SET and row count are compared to the released gold (level 1)",
            "canonical FULL-row multiset is compared to the per-WG gold row dump (level 2)",
        ],
        "what_it_does_not_verify": [
            "the gold answer key itself is taken as given; it is the comparison target",
            "SPARQL translations and the SHACL/ontology layer are covered by --quick, not here",
        ],
        "scope": {
            "wgs_covered": covered,
            "wgs_total": WGS,
            "released_cqs_total": released_total,
            "cqs_reexecuted": reexec,
            "partial_reproduction": partial,
            "per_wg_cq_limit": limit,
        },
        "gold_source": {
            "level1": "release_package/cqs/spectra_cq_v2.0/benchmark.jsonl "
                      "(gold_primary_values, gold_row_count)",
            "level2": "release_package/cqs/spectra_cq_v2.0/gold/{WG}_gold.json (rows[], capped at 2000)",
        },
        "canonicalization": {
            "column_identity": "positional (first RETURN column for level 1; full column order for level 2) "
                               "— alias-independent by construction; alias drift is reported separately",
            "levels": {
                "before_canonicalization": "raw rendered values compared verbatim",
                "strict": "lossless only: NFKC, whitespace collapse, boolean/null spelling",
                "canonical": "strict + numeric normalization (trailing zeros, exponent form) "
                             "and ISO-8601 fraction/timezone spelling; this is the headline verdict",
                "collection_order_insensitive": "canonical + elements of a returned list sorted, "
                                                "isolating collect() element order (undefined in Cypher "
                                                "unless the query orders its input)",
            },
            "row_order": "level 1 compares sorted sets; level 2 compares sorted multisets",
        },
        "results": {
            "l1_match": l1,
            "l1_mismatch": reexec - l1,
            "l1_match_strict": sum(r["l1_match_strict"] for r in per_wg.values()),
            "l1_match_before_canonicalization":
                sum(r["l1_match_before_canonicalization"] for r in per_wg.values()),
            "l2_compared": l2c,
            "l2_match": l2,
            "l2_mismatch": l2c - l2,
            "l2_match_strict": sum(r["l2_match_strict"] for r in per_wg.values()),
            "l2_match_collection_order_insensitive":
                sum(r["l2_match_collection_order_insensitive"] for r in per_wg.values()),
            "errors": sum(r["errors"] for r in per_wg.values()),
        },
        "graph_reloaded": {
            "nodes": sum(r["loaded_nodes"] for r in per_wg.values()),
            "relationships": sum(r["loaded_relationships"] for r in per_wg.values()),
            "ttl_bytes": sum(r["ttl_bytes"] for r in per_wg.values()),
        },
        "per_wg": {k: {kk: vv for kk, vv in v.items() if kk != "_results"}
                   for k, v in per_wg.items()},
        "elapsed_s": round(elapsed, 1),
        "seconds_breakdown": {
            "load_total": round(sum(r["seconds"]["load"] for r in per_wg.values()), 1),
            "query_total": round(sum(r["seconds"]["query"] for r in per_wg.values()), 1),
            "wipe_total": round(sum(r["seconds"]["wipe"] for r in per_wg.values()), 1),
        },
        "bolt": bolt,
    }
    detail = {
        "generated_by": "release_package/tests/verify_benchmark.py --full",
        "scope": summary["scope"],
        "mismatches": [r for wg in per_wg for r in per_wg[wg]["_results"]
                       if not r.get("pass_l1") or r.get("pass_l2") is False],
        "per_cq": {wg: per_wg[wg]["_results"] for wg in per_wg},
    }
    return summary, detail


# ---------------------------------------------------------------------------
def merge_out(payload: dict) -> None:
    """Merge one mode's record into the output JSON without dropping the other."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_json = OUT_DIR / OUT_JSON_NAME
    doc = {}
    if out_json.exists():
        try:
            doc = json.loads(out_json.read_text())
        except Exception:  # noqa: BLE001
            doc = {}
    doc.setdefault("generated_by", "release_package/tests/verify_benchmark.py")
    doc.setdefault("modes", {})
    doc["modes"].update(payload)
    doc["last_run_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out_json.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
    print(f"-> {out_json}")


def main() -> int:
    global OUT_DIR
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--quick", action="store_true",
                    help="artifact-integrity mode (no database)")
    ap.add_argument("--full", action="store_true",
                    help="answer-reproduction mode (reload + re-execute)")
    ap.add_argument("--wg", default="all",
                    help="comma-separated WGs for --full, or 'all'")
    ap.add_argument("--bolt",
                    help="scratch Neo4j for --full (WIPED — never a store whose "
                         "contents matter); required with --full")
    ap.add_argument("--user", default="neo4j")
    ap.add_argument("--password", help="required with --full")
    ap.add_argument("--batch-size", type=int, default=2000)
    ap.add_argument("--limit", type=int, default=None,
                    help="re-execute only the first N CQs per WG (partial run)")
    ap.add_argument("--out", type=Path, default=OUT_DIR,
                    help="directory for the JSON output and loader reports "
                         "(default: verifier_output/ under the working directory)")
    args = ap.parse_args()
    if not (args.quick or args.full):
        # Bare invocation runs the database-free gate, so the release stays
        # verifiable with no arguments from a Git-only checkout.
        args.quick = True
    if args.full and not (args.bolt and args.password):
        ap.error("--full needs --bolt and --password (the target is wiped)")
    OUT_DIR = args.out

    rc = 0
    if args.quick:
        q = run_quick()
        print(f"\n=== QUICK: {q['passed']}/{q['checks_total']} checks passed "
              f"in {q['elapsed_s']}s ===")
        for n in q["failed_names"]:
            print(f"  FAIL {n}")
        merge_out({"quick": q})
        rc |= 0 if q["failed"] == 0 else 1

    if args.full:
        for p in (RELEASE / "kg/per_wg", CYP_DIR, GOLD_DIR):
            if not p.exists():
                print(f"missing required release path: {p}", file=sys.stderr)
                return 2
        wgs = WGS if args.wg == "all" else [w.strip() for w in args.wg.split(",")]
        summary, detail = run_full(wgs, args.bolt, args.user, args.password,
                                  args.batch_size, args.limit)
        r = summary["results"]
        s = summary["scope"]
        print(f"\n=== FULL: level1 {r['l1_match']}/{s['cqs_reexecuted']} re-executed CQs "
              f"reproduce their released gold "
              f"(level2 full-row {r['l2_match']}/{r['l2_compared']}) "
              f"in {summary['elapsed_s']}s ===")
        if s["partial_reproduction"]:
            print(f"    PARTIAL scope: {s['cqs_reexecuted']}/{s['released_cqs_total']} "
                  f"released CQs, WGs {s['wgs_covered']}")
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        detail_json = OUT_DIR / DETAIL_JSON_NAME
        detail_json.write_text(json.dumps(detail, indent=2, ensure_ascii=False))
        print(f"-> {detail_json}")
        merge_out({"full": summary})
        rc |= 0 if (r["l1_mismatch"] == 0 and r["l2_mismatch"] == 0
                    and r["errors"] == 0) else 1

    return rc


if __name__ == "__main__":
    sys.exit(main())
