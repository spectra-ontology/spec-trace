#!/usr/bin/env python3
"""generate_cq_index.py — regenerate cqs/cq_index.md from the benchmark metadata.

Reads cqs/spectra_cq_v2.0/questions.json (the single source of truth for the
released SpectraCQ v2.0 benchmark) and emits a per-WG schema-area index table
of every released competency question. Category labels are carried verbatim
from the benchmark metadata; an empty label is rendered as "(uncategorized)".

Usage: cd release_package && python3 pipeline/generate_cq_index.py
"""
from __future__ import annotations

import json
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
QUESTIONS = PKG / "cqs" / "spectra_cq_v2.0" / "questions.json"
OUT = PKG / "cqs" / "cq_index.md"

WG_ORDER = ["RAN1", "RAN2", "RAN3", "RAN4", "RAN5"]


def schema_area_cell(sa: dict) -> str:
    classes = ", ".join(sorted(sa.get("classes", [])))
    rels = ", ".join(sorted(sa.get("relationships", [])))
    parts = []
    if classes:
        parts.append(f"classes={{{classes}}}")
    if rels:
        parts.append(f"rels={{{rels}}}")
    return "; ".join(parts) if parts else "—"


def main() -> None:
    d = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    meta, cqs = d["metadata"], d["cqs"]

    by_wg: dict[str, list[dict]] = {wg: [] for wg in WG_ORDER}
    for c in cqs:
        by_wg[c["wg"]].append(c)

    released = meta["released_scored_cqs"]
    by_wg_counts = meta["released_by_wg"]
    by_phase = meta["released_by_phase"]
    assert released == len(cqs), f"metadata says {released}, file has {len(cqs)}"
    for wg in WG_ORDER:
        assert by_wg_counts[wg] == len(by_wg[wg]), wg

    wg_counts_str = ", ".join(f"{wg}={by_wg_counts[wg]}" for wg in WG_ORDER)
    phase_counts_str = ", ".join(f"{k}={by_phase[k]}" for k in sorted(by_phase))

    lines = [
        f"# Schema-area index of the {released} released SpectraCQ v2.0 competency questions",
        "",
        f"This file enumerates all {released} scored competency questions released in "
        "SpectraCQ v2.0, generated directly from `cqs/spectra_cq_v2.0/questions.json` "
        "(the benchmark's single source of truth; regenerate with "
        "`python3 pipeline/generate_cq_index.py`). The full question text, executable "
        "reference Cypher (one file per CQ), and per-CQ gold answer sets are shipped "
        "under `cqs/spectra_cq_v2.0/` (see `cqs/spectra_cq_v2.0/README.md`). For each "
        "CQ this index publishes the **identifier**, **phase**, **category** (carried "
        "verbatim from the benchmark metadata; an empty label is shown as "
        "*(uncategorized)*), and **schema area exercised**, so third parties can "
        "verify at a glance (i) the breadth of the released CQ set and (ii) which "
        "ontology classes / relationships each CQ traverses.",
        "",
        f"**Total**: {released} released CQs across 5 working groups "
        f"({wg_counts_str}) and 5 phases ({phase_counts_str}). "
        f"{meta['authored_cqs']} CQs were authored in total; "
        f"{meta['held_cqs']} are withheld as a held-out set "
        "(see `cqs/spectra_cq_v2.0/README.md` for the hold-out policy).",
        "",
        "A representative subset of CQs (with full question text and executable "
        "Cypher/SPARQL) is in `representative_cqs.md`. A category-by-phase "
        "distribution is rendered as `../diagrams/cq_distribution.png`. The "
        "design-phase validation evidence that preceded this benchmark is indexed "
        "in `../validation/validation_manifest.md`.",
    ]

    for wg in WG_ORDER:
        rows = by_wg[wg]
        lines += [
            "",
            f"## {wg} ({len(rows)} CQs)",
            "",
            "| ID | Phase | Category | Schema area exercised |",
            "|----|------:|----------|------------------------|",
        ]
        for c in rows:
            cat = c["category"] or "*(uncategorized)*"
            lines.append(
                f"| `{c['id']}` | {c['phase']} | {cat} | {schema_area_cell(c['schema_area'])} |"
            )

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[write] {OUT.relative_to(PKG)}: {released} CQs, {len(lines)+1} lines")


if __name__ == "__main__":
    main()
