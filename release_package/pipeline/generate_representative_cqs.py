#!/usr/bin/env python3
"""generate_representative_cqs.py — regenerate cqs/representative_cqs.md.

Selects the 14 RAN1 competency questions whose reference Cypher is mirrored
under queries/cypher/ (two or three per phase, all five phases), pulls the
question text / category / gold row count from cqs/spectra_cq_v2.0/questions.json
(the benchmark's single source of truth), and quotes each released Cypher file
verbatim. Appends the phase-agnostic MULTI_HOP_traceability example, which
ships in both Cypher and SPARQL form.

Usage: cd release_package && python3 pipeline/generate_representative_cqs.py
"""
from __future__ import annotations

import json
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
QUESTIONS = PKG / "cqs" / "spectra_cq_v2.0" / "questions.json"
CYPHER_DIR = PKG / "cqs" / "spectra_cq_v2.0" / "cypher"
MIRROR_DIR = PKG / "queries" / "cypher"
OUT = PKG / "cqs" / "representative_cqs.md"

# Mirror basenames under queries/cypher/, grouped by phase. Each maps to the
# released RAN1_<basename>.cypher file it is a byte-identical copy of.
PHASE_PICKS = {
    1: ["P1_CQ1-1", "P1_CQ1-2", "P1_CQ1-3"],
    2: ["P2_CQ1-1", "P2_CQ1-2", "P2_CQ1-3"],
    3: ["P3_CQ001", "P3_CQ002", "P3_CQ003", "P3_CQ004"],
    4: ["P4_CQ1-1", "P4_CQ1-2"],
    5: ["P5_CQ1-1", "P5_CQ1-2"],
}

# Phase → domain wording carried from cqs/spectra_cq_v2.0/README.md.
PHASE_TITLES = {
    1: "Phase 1 — TDoc metadata",
    2: "Phase 2 — Meeting resolutions",
    3: "Phase 3 — TS structure",
    4: "Phase 4 — CR documents",
    5: "Phase 5 — Technical Reports",
}


def main() -> None:
    d = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    meta = d["metadata"]
    by_id = {c["id"]: c for c in d["cqs"]}
    released = meta["released_scored_cqs"]

    n_picks = sum(len(v) for v in PHASE_PICKS.values())
    lines = [
        "# Representative competency questions (RAN1 subset)",
        "",
        f"This file presents {n_picks} of the {released} competency questions "
        "released in SpectraCQ v2.0, chosen to cover all five phases of the "
        "benchmark with full question text and executable reference Cypher. "
        "Each query below is quoted verbatim from its released file under "
        "`spectra_cq_v2.0/cypher/`; the copies under `../queries/cypher/` are "
        "byte-identical mirrors kept for standalone browsing. The complete "
        "per-CQ index (all five working groups) is in `cq_index.md`; question "
        "text, Cypher, and gold answer sets for every released CQ are under "
        "`spectra_cq_v2.0/`.",
        "",
        "Gold row counts below are carried from "
        "`spectra_cq_v2.0/questions.json`, where each gold answer set was "
        "produced by executing the reference Cypher against the corresponding "
        "working-group knowledge graph (no human- or LLM-authored answers).",
    ]

    for phase in sorted(PHASE_PICKS):
        lines += ["", f"## {PHASE_TITLES[phase]}"]
        for base in PHASE_PICKS[phase]:
            rid = f"RAN1_{base}"
            cq = by_id[rid]
            assert cq["phase"] == phase, (rid, cq["phase"], phase)
            released_file = CYPHER_DIR / f"{rid}.cypher"
            mirror_file = MIRROR_DIR / f"{base}.cypher"
            body = released_file.read_text(encoding="utf-8")
            assert body == mirror_file.read_text(encoding="utf-8"), (
                f"mirror drift: {mirror_file}")
            cat = cq["category"] or "(uncategorized)"
            gold = cq["gold"]
            lines += [
                "",
                f"### `{rid}`",
                "",
                f"**Question**: {cq['question_en']}",
                "",
                f"**Category**: {cat} · **Gold**: {gold['row_count']} rows "
                f"(primary column `{gold['primary_column']}`) · "
                f"**Files**: `spectra_cq_v2.0/cypher/{rid}.cypher` "
                f"(mirror `../queries/cypher/{base}.cypher`)",
                "",
                "```cypher",
                body.rstrip("\n"),
                "```",
            ]

    multihop_cy = (MIRROR_DIR / "MULTI_HOP_traceability.cypher").read_text(
        encoding="utf-8")
    lines += [
        "",
        "## Phase-agnostic example — multi-hop traceability",
        "",
        "Beyond the per-phase CQs, the release ships one phase-agnostic "
        "example that chains two traceability layers (change requests "
        "modifying a section, and technical reports shaping the parent "
        "specification) in both query languages: "
        "`../queries/cypher/MULTI_HOP_traceability.cypher` and "
        "`../queries/sparql/MULTI_HOP_traceability.rq`. Both return the same "
        "609 rows (87 CRs × 7 TRs) on the released RAN1 KG — the SPARQL form "
        "against `kg/per_wg/RAN1-body.ttl` directly, the Cypher form against "
        "the property graph restored by `pipeline/load_released_kg.py` "
        "(evidence: `../validation/example_queries_results.json`).",
        "",
        "```cypher",
        multihop_cy.rstrip("\n"),
        "```",
    ]

    text = "\n".join(lines) + "\n"
    OUT.write_text(text, encoding="utf-8")
    print(f"[write] {OUT.relative_to(PKG)}: {n_picks} CQs + MULTI_HOP, "
          f"{text.count(chr(10))} lines")


if __name__ == "__main__":
    main()
