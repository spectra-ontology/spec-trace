#!/usr/bin/env python3
"""generate_cq_distribution.py — regenerate diagrams/cq_distribution.png.

Renders the category-by-phase distribution of the released SpectraCQ
questions as a stacked horizontal bar chart, computed directly from
cqs/spectra_cq_v2.0/questions.json (the benchmark's single source of
truth). Categories are the verbatim `category` strings from the released
questions (empty string shown as "(uncategorized)"); a category whose
questions sit in several phases is drawn as a stacked bar. Ordering
(descending total, then name) and colors are fixed, so the output is
deterministic for a given questions.json.

Usage: cd release_package && python3 pipeline/generate_cq_distribution.py
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PKG = Path(__file__).resolve().parents[1]
QUESTIONS = PKG / "cqs" / "spectra_cq_v2.0" / "questions.json"
OUT = PKG / "diagrams" / "cq_distribution.png"

PHASES = [1, 2, 3, 4, 5]
# One fixed color per phase (matplotlib "tab10" hues).
PHASE_COLORS = {
    1: "#1f77b4",
    2: "#ff7f0e",
    3: "#2ca02c",
    4: "#d62728",
    5: "#9467bd",
}


def main() -> None:
    d = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    cqs = d["cqs"]
    total = len(cqs)
    assert total == d["metadata"]["released_scored_cqs"], (
        total, d["metadata"]["released_scored_cqs"])

    cross: dict[str, Counter] = defaultdict(Counter)
    for c in cqs:
        cross[c["category"] or "(uncategorized)"][c["phase"]] += 1

    # Descending total, then category name — a fixed, reproducible order.
    cats = sorted(cross, key=lambda k: (-sum(cross[k].values()), k))
    assert sum(sum(v.values()) for v in cross.values()) == total

    fig, ax = plt.subplots(figsize=(11, 8.5))
    y = range(len(cats))
    left = [0] * len(cats)
    for ph in PHASES:
        widths = [cross[c].get(ph, 0) for c in cats]
        ax.barh(y, widths, left=left, height=0.72,
                color=PHASE_COLORS[ph],
                label=f"Phase {ph} ({sum(v.get(ph, 0) for v in cross.values())})")
        left = [l + w for l, w in zip(left, widths)]

    for i, c in enumerate(cats):
        ax.text(left[i] + 1.2, i, str(sum(cross[c].values())),
                va="center", fontsize=8)

    ax.set_yticks(list(y))
    ax.set_yticklabels(cats, fontsize=8.5, family="monospace")
    ax.invert_yaxis()
    ax.set_xlabel("Number of released CQs")
    ax.set_title(
        f"SpectraCQ v2.0 — category-by-phase distribution "
        f"({total} released CQs, {len(cats)} categories, all five WGs)")
    ax.legend(loc="lower right", framealpha=0.95)
    ax.set_xlim(0, max(left) * 1.08)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", linewidth=0.4, alpha=0.4)
    fig.tight_layout()
    fig.savefig(OUT, dpi=170)
    print(f"[write] {OUT.relative_to(PKG)}: {total} CQs, {len(cats)} "
          f"categories, phases {PHASES}")


if __name__ == "__main__":
    main()
