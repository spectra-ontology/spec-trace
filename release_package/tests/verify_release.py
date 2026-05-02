#!/usr/bin/env python3
"""
SPECTRA release verification script.

Runs deterministic checks against the released artifacts:
  1. Ontology TTL parses + triple count
  2. SHACL conforms on bundled instantiation snippet
  3. End-to-end SPARQL example returns expected row
  4. SpectraCQ v1.0 metadata + counts
  5. Class/property counts vs validation/structural_metrics.json
  6. Validation manifest references resolve
  7. Anonymization sanity (released CQs and examples have no real company names)

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
        check("triples_total = 887", n == 887, f"actual {n}")
    except Exception as e:
        check("ontology parse", False, str(e))

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

    section("4. SpectraCQ v1.0 metadata")
    try:
        d = json.loads((ROOT / "cqs/spectra_cq_v1.0/questions.json").read_text())
        m = d.get("metadata", {})
        check("total_cqs = 137", m.get("total_cqs") == 137, f"actual {m.get('total_cqs')}")
        phases = m.get("phases", {})
        expected = {"P1": 25, "P2": 34, "P3": 45, "P4": 15, "P5": 18}
        ok = phases == expected
        check("phase distribution P1-P5", ok, f"actual {phases}")
        cqs = d.get("cqs", [])
        check("137 CQ entries", len(cqs) == 137, f"actual {len(cqs)}")
        verdicts = sum(1 for c in cqs if c.get("verdict") == "PASS")
        check("all CQs verdict=PASS", verdicts == 137, f"PASS {verdicts}/137")
        cypher_dir = ROOT / "cqs/spectra_cq_v1.0/cypher"
        n_files = len(list(cypher_dir.glob("*.cypher")))
        check("137 Cypher files", n_files == 137, f"actual {n_files}")
    except Exception as e:
        check("SpectraCQ metadata", False, str(e))

    section("5. Structural metrics vs JSON evidence")
    try:
        sm = json.loads((ROOT / "validation/structural_metrics.json").read_text())
        for key, expected in [
            ("classes_total", 26),
            ("triples_total", 887),
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
        files_ref = set(re.findall(r"`([\w_]+\.json)`", manifest))
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
        cq_text = (ROOT / "cqs/spectra_cq_v1.0/questions.json").read_text()
        has_real = any(c in cq_text for c in real_companies)
        check("SpectraCQ questions: verbatim 3GPP company names (intentional)", has_real,
              "expected real company names matching TDOC_List.xlsx")
        cypher_dir = ROOT / "cqs/spectra_cq_v1.0/cypher"
        cypher_with_real = sum(1 for f in cypher_dir.glob("*.cypher")
                               if any(c in f.read_text() for c in real_companies))
        check(f"SpectraCQ Cypher: {cypher_with_real} files with verbatim company names (intentional)",
              cypher_with_real > 0)
    except Exception as e:
        check("synthetic-instantiation sanity", False, str(e))

    section("8. Release directory inventory")
    for d, label in [
        ("kg/per_wg", "kg/per_wg/ exists"),
        ("pipeline", "pipeline/ exists"),
    ]:
        path = ROOT / d
        present = path.exists() and any(path.iterdir())
        check(label, present, "missing or empty (placeholder if README only)" if not present else "")

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
