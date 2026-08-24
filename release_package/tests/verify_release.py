#!/usr/bin/env python3
"""
SPECTRA release verification script.

Runs deterministic checks against the released artifacts:
  1. Ontology TTL parses + triple count
  2. SHACL conforms on bundled instantiation snippet
  3. End-to-end SPARQL example returns expected row
  4. SpectraCQ v2.0 benchmark counts + gold integrity
     (624 released scored / 654 authored / 30 held-out)
  5. Class/property counts vs validation/structural_metrics.json
  6. Validation manifest references resolve
  7. Synthetic-instantiation sanity (real_world_mini uses no operational-KG names; SpectraCQ retains verbatim public 3GPP company names)

Designed for a vanilla Python env: pip install rdflib pyshacl
Run from release_package/ root: python3 tests/verify_release.py
Exit code 0 = all checks pass; non-zero = at least one failure.

Reviewers can use this script to independently confirm the public claims
without reading any LLM-generated summaries or trusting interpretations.
"""
from __future__ import annotations
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
results: list[tuple[str, bool, str]] = []  # (name, passed, detail)


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}{(' — ' + detail) if detail else ''}")


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> int:
    section("1. Ontology TTL")
    try:
        import rdflib
        g = rdflib.Graph()
        g.parse(ROOT / "ontology/spectra.ttl", format="turtle")
        n = len(g)
        check("triples_total = 914", n == 914, f"actual {n}")
    except Exception as e:
        check("ontology parse", False, str(e))

    section("1b. Documentation copy byte-identical to canonical ontology")
    # The ontology ships once as the authoritative source (ontology/spectra.ttl)
    # and once more as the download target of the PyLODE page (docs/spectra.ttl,
    # linked as <a href="spectra.ttl">). Those are physical copies of one logical
    # artifact: nothing but this check keeps them in step, and an earlier hand
    # edit to the canonical file left the doc copy stale. The released package
    # must therefore never carry a doc copy that diverges from the canonical.
    canonical = ROOT / "ontology/spectra.ttl"
    doc_ttl = ROOT / "docs/spectra.ttl"
    try:
        canon_bytes = canonical.read_bytes()
        if not doc_ttl.exists():
            check("docs/spectra.ttl present", False,
                  "missing — PyLODE 'RDF (turtle)' download link has no target")
        else:
            same = doc_ttl.read_bytes() == canon_bytes
            check("docs/spectra.ttl is byte-identical to ontology/spectra.ttl",
                  same,
                  "OK" if same else
                  "DRIFT — regenerate docs/spectra.ttl from the canonical ontology")
    except Exception as e:
        check("doc-copy identity", False, str(e))

    section("2. SHACL conformance on instantiation snippet")
    try:
        from pyshacl import validate
        from rdflib import Graph
        data = Graph().parse(ROOT / "examples/instantiation_snippet.ttl", format="turtle")
        shapes = Graph().parse(ROOT / "shapes/spectra-core.shacl.ttl", format="turtle")
        ont = Graph().parse(ROOT / "ontology/spectra.ttl", format="turtle")
        ok, _, msg = validate(data, shacl_graph=shapes, ont_graph=ont)
        check("Conforms: True", bool(ok), "" if ok else msg.splitlines()[0] if msg else "")
    except Exception as e:
        check("SHACL validate", False, str(e))

    section("2b. SHACL conformance on metadata-only process KG (Appendix G)")
    try:
        from pyshacl import validate
        from rdflib import Graph
        data = Graph()
        for f in ("examples/process_kg/ls_routing.ttl",
                  "examples/process_kg/cr_routing.ttl",
                  "examples/process_kg/ran1_tdoc_metadata.ttl"):
            p = ROOT / f
            if p.exists():
                data.parse(p, format="turtle")
        shapes = Graph().parse(ROOT / "shapes/spectra-core.shacl.ttl", format="turtle")
        ont = Graph().parse(ROOT / "ontology/spectra.ttl", format="turtle")
        ok, _, msg = validate(data, shacl_graph=shapes, ont_graph=ont)
        check("Process-KG union conforms (Appendix G claim)", bool(ok), "" if ok else (msg.splitlines()[0] if msg else ""))
    except Exception as e:
        check("Process-KG SHACL", False, str(e))

    section("3. End-to-end SPARQL example")
    try:
        import rdflib
        g = rdflib.Graph()
        g.parse(ROOT / "ontology/spectra.ttl", format="turtle")
        g.parse(ROOT / "examples/end_to_end/data.ttl", format="turtle")
        q = (ROOT / "examples/end_to_end/query.sparql").read_text()
        rows = list(g.query(q))
        ok = len(rows) >= 1 and any("R1-2599998" in str(r) for r in rows)
        check("E2E query returns R1-2599998 row", ok, f"{len(rows)} rows")
    except Exception as e:
        check("E2E SPARQL", False, str(e))

    section("4. SpectraCQ v2.0 benchmark counts + gold integrity")
    # Canonical counts: release_package/MANIFEST.md §2. Gold = the SET of the
    # first RETURN column of each reference Cypher plus a row count; no LLM and
    # no human annotation is in the gold path.
    try:
        cq_root = ROOT / "cqs/spectra_cq_v2.0"
        d = json.loads((cq_root / "questions.json").read_text())
        m = d.get("metadata", {})
        check("released_scored_cqs = 624", m.get("released_scored_cqs") == 624,
              f"actual {m.get('released_scored_cqs')}")
        check("authored_cqs = 654", m.get("authored_cqs") == 654,
              f"actual {m.get('authored_cqs')}")
        check("held_cqs = 30", m.get("held_cqs") == 30, f"actual {m.get('held_cqs')}")
        split_ok = (m.get("authored_cqs") ==
                    (m.get("released_scored_cqs") or 0) + (m.get("held_cqs") or 0))
        check("authored = released + held", split_ok,
              f"{m.get('authored_cqs')} = {m.get('released_scored_cqs')} + {m.get('held_cqs')}")
        expected_wg = {"RAN1": 142, "RAN2": 128, "RAN3": 123, "RAN4": 117, "RAN5": 114}
        check("released_by_wg (5 WGs)", m.get("released_by_wg") == expected_wg,
              f"actual {m.get('released_by_wg')}")
        expected_phase = {"P1": 123, "P2": 112, "P3": 233, "P4": 75, "P5": 81}
        check("released_by_phase P1-P5", m.get("released_by_phase") == expected_phase,
              f"actual {m.get('released_by_phase')}")
        cqs = d.get("cqs", [])
        check("624 CQ entries", len(cqs) == 624, f"actual {len(cqs)}")
        gold_pass = sum(1 for c in cqs
                        if isinstance(c.get("gold"), dict)
                        and c["gold"].get("status") == "PASS")
        check("all released CQs carry gold.status = PASS", gold_pass == 624,
              f"PASS {gold_pass}/624")
        n_cypher = len(list((cq_root / "cypher").glob("*.cypher")))
        check("624 Cypher reference queries", n_cypher == 624, f"actual {n_cypher}")
        n_sparql = len(list((cq_root / "sparql").glob("*.rq")))
        check("142 SPARQL translations (all released RAN1 CQs)", n_sparql == 142,
              f"actual {n_sparql}")

        bench_rows = [json.loads(line)
                      for line in (cq_root / "benchmark.jsonl").read_text().splitlines()
                      if line.strip()]
        check("benchmark.jsonl: 624 rows", len(bench_rows) == 624,
              f"actual {len(bench_rows)}")
        bad_gold = [r["id"] for r in bench_rows
                    if not r.get("gold_primary_values")
                    or not isinstance(r.get("gold_row_count"), int)
                    or r["gold_row_count"] < 1]
        check("benchmark.jsonl: every row has non-empty gold set + row count",
              not bad_gold, f"degenerate: {bad_gold[:5]}" if bad_gold else "")
        ids_equal = {c["id"] for c in cqs} == {r["id"] for r in bench_rows}
        check("questions.json ids == benchmark.jsonl ids", ids_equal)

        held = json.loads((cq_root / "held/held_cqs.json").read_text())
        held_ok = held.get("count") == 30 and len(held.get("held", [])) == 30
        check("held/held_cqs.json: 30 held-out CQs", held_ok,
              f"count={held.get('count')} len={len(held.get('held', []))}")
        gs = json.loads((cq_root / "gold/_gold_summary.json").read_text())
        gs_ok = (gs.get("authored_total") == 654
                 and gs.get("released_scored_total") == 624
                 and gs.get("held_total") == 30)
        check("gold/_gold_summary.json: 654 authored / 624 released / 30 held", gs_ok,
              f"{gs.get('authored_total')}/{gs.get('released_scored_total')}/{gs.get('held_total')}")
    except Exception as e:
        check("SpectraCQ benchmark counts", False, str(e))

    section("5. Structural metrics vs JSON evidence")
    try:
        sm = json.loads((ROOT / "validation/structural_metrics.json").read_text())
        for key, expected in [
            ("classes_total", 32),
            ("triples_total", 914),
        ]:
            ok = sm.get(key) == expected
            check(f"{key} = {expected}", ok, f"actual {sm.get(key)}")
        for key, expected_len in [
            ("object_properties", 53),
            ("data_properties", 81),
            ("functional_properties", 20),
            ("inverse_functional_properties", 2),
            ("inverse_property_pairs", 15),
            ("irreflexive_properties", 6),
            ("asymmetric_properties", 2),
        ]:
            v = sm.get(key)
            n = len(v) if isinstance(v, list) else v
            check(f"{key} count = {expected_len}", n == expected_len, f"actual {n}")
        n_axioms = len(sm.get("prov_o_alignment", {}).get("subclass_axioms", []))
        check("PROV-O subclass axioms = 6", n_axioms == 6, f"actual {n_axioms}")
    except Exception as e:
        check("structural_metrics", False, str(e))

    section("6. Validation manifest references resolve")
    try:
        manifest = (ROOT / "validation/validation_manifest.md").read_text()
        # bare names resolve at validation/ top level; one-level prefixed
        # names (e.g. cq_replay/graph_counts.json) resolve beneath it
        files_ref = set(re.findall(r"`((?:[\w_]+/)?[\w_]+\.json)`", manifest))
        missing = [f for f in files_ref if not (ROOT / "validation" / f).exists()]
        check(f"all {len(files_ref)} JSON refs exist", len(missing) == 0,
              f"missing {missing}" if missing else f"{len(files_ref)} files")
    except Exception as e:
        check("manifest", False, str(e))

    section("7. Synthetic-instantiation sanity")
    # SpectraCQ and process_kg deliberately use verbatim 3GPP company names
    # (matching the public TDOC_List.xlsx); only the synthetic example set
    # (real_world_mini) must NOT leak operational-KG names.
    real_companies = [
        "Samsung", "Huawei", "Ericsson", "Nokia", "Qualcomm", "Apple",
        "Intel", "MediaTek", "ZTE", "Vodafone", "AT&T", "NTT DOCOMO",
        "InterDigital", "LG Electronics", "Sony", "HiSilicon",
    ]
    try:
        text = (ROOT / "examples/real_world_mini/data.ttl").read_text()
        leaks = [c for c in real_companies if c in text]
        check("real_world_mini data.ttl: only synthetic identifiers", not leaks,
              f"leaks: {leaks}" if leaks else "")
        # Confirm SpectraCQ uses verbatim names (positive check; expected presence)
        cq_text = (ROOT / "cqs/spectra_cq_v2.0/questions.json").read_text()
        has_real = any(c in cq_text for c in real_companies)
        check("SpectraCQ questions: verbatim 3GPP company names (intentional)", has_real,
              "expected real company names matching TDOC_List.xlsx")
        cypher_dir = ROOT / "cqs/spectra_cq_v2.0/cypher"
        cypher_with_real = sum(1 for f in cypher_dir.glob("*.cypher")
                               if any(c in f.read_text() for c in real_companies))
        check(f"SpectraCQ Cypher: {cypher_with_real} files with verbatim company names (intentional)",
              cypher_with_real > 0)
    except Exception as e:
        check("synthetic-instantiation sanity", False, str(e))

    section("8. Release directory inventory")
    for d, label in [
        ("kg/per_wg", "kg/per_wg/ exists"),
        ("kg/per_wg_schema", "kg/per_wg_schema/ exists"),
        ("supplement", "supplement/ exists"),
        ("pipeline", "pipeline/ exists"),
    ]:
        path = ROOT / d
        present = path.exists() and any(path.iterdir())
        check(label, present, "missing or empty (placeholder if README only)" if not present else "")

    # 8b. Per-WG body-text TTLs are deposited on Zenodo (DOI in
    # kg/per_wg/README.md), NOT in this Git repository, because four of
    # the five files exceed GitHub's 100 MB-per-file limit (~903 MB total
    # for the five WGs). When run inside a Git checkout the body files
    # are absent by design; when run inside a Zenodo download they are
    # present. We accept either layout.
    section("8b. Per-WG body-text KGs (Zenodo deposit, optional in Git checkout)")
    body_dir = ROOT / "kg/per_wg"
    body_present_count = 0
    expected_body_files = {
        f"RAN{n}-body.ttl": 10 * 1024 * 1024  # require >= 10 MB each when present
        for n in range(1, 6)
    }
    for fname, min_bytes in expected_body_files.items():
        p = body_dir / fname
        if not p.exists():
            print(f"  [SKIP] {fname}: not in this checkout (Zenodo deposit; see kg/per_wg/README.md)")
            continue
        body_present_count += 1
        sz = p.stat().st_size
        check(f"{fname} >= {min_bytes // (1024*1024)} MB (body-text KG)",
              sz >= min_bytes,
              f"actual {sz / (1024*1024):.1f} MB")
    print(f"  body TTLs present in checkout: {body_present_count}/5 "
          f"({'Zenodo download' if body_present_count == 5 else 'Git checkout'})")

    # Per-WG schema TTLs must exist (much smaller; >= 5 KB)
    expected_schema_files = {f"RAN{n}-schema.ttl": 5 * 1024 for n in range(1, 6)}
    for fname, min_bytes in expected_schema_files.items():
        p = ROOT / "kg/per_wg_schema" / fname
        if not p.exists():
            check(f"{fname} exists", False, "MISSING — paper RAS claims this file is shipped")
            continue
        sz = p.stat().st_size
        check(f"{fname} >= {min_bytes // 1024} KB", sz >= min_bytes,
              f"actual {sz / 1024:.1f} KB")

    # Summary
    print()
    total = len(results)
    passed = sum(1 for _, ok, _ in results if ok)
    failed = total - passed
    print(f"=== Summary: {passed}/{total} checks passed ===")
    if failed:
        print(f"Failures:")
        for name, ok, detail in results:
            if not ok:
                print(f"  - {name}: {detail}")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
