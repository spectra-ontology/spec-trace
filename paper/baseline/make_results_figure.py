#!/usr/bin/env python3
"""Build the SpectraCQ results figure from the measured baseline scores.

Reads results/scores.json (9 models x 3 settings x 624 scored answers, all
produced by the released harness) and renders a grouped bar chart of Set F1
per model per setting. No values are invented: every bar height is read
directly from scores.json['scores'][setting][model]['overall'].

Output: fig3_results.pdf next to this script
        (vector, fonts embedded via pdf.fonttype=42)

Story the figure carries: for every one of the nine models, the two text-only
settings (closed-book, retrieval-augmented) stay near zero while grounding the
same model in the process graph lifts Set F1 by an order of magnitude. The
separation is a property of the task, not of any single model.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

BASE = Path(__file__).resolve().parent
SCORES = BASE / "results/scores.json"
OUT = BASE / "fig3_results.pdf"

# Liberation Sans is a metric-compatible Helvetica/Arial stand-in and embeds cleanly.
for cand in ("Liberation Sans", "DejaVu Sans"):
    if any(f.name == cand for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = cand
        break
plt.rcParams["pdf.fonttype"] = 42   # TrueType -> fonts embedded, no Type-3
plt.rcParams["ps.fonttype"] = 42

SETTINGS = [
    # (key, label, fill, hatch, edge) — the two text-only baselines carry distinct
    # hatch patterns so they stay separable in grayscale print, not just by fill.
    ("closed_book", "Closed-book",          "#D9D9D9", "///", "#777777"),
    ("rag",         "Retrieval-augmented",  "#9A9A9A", "..",  "#555555"),
    ("kg_grounded", "KG-grounded",          "#0072B2", None,  "white"),
]
METRIC = "f1"   # Set F1: continuous, shows the text-only baselines' partial credit

# Shorter display names for the x axis.
DISPLAY = {
    "claude-opus-4.8":  "Claude\nOpus 4.8",
    "claude-haiku-4.5": "Claude\nHaiku 4.5",
    "deepseek-v3.1":    "DeepSeek\nV3.1",
    "gemini-2.5-pro":   "Gemini\n2.5 Pro",
    "gemini-2.5-flash": "Gemini\n2.5 Flash",
    "gpt-5.1":          "GPT-5.1",
    "gpt-5-mini":       "GPT-5\nmini",
    "llama-3.3-70b":    "Llama-3.3\n70B",
    "qwen3-235b":       "Qwen3\n235B",
}


def main():
    data = json.loads(SCORES.read_text())
    scores = data["scores"]

    models = sorted(scores["kg_grounded"].keys())
    # Order by KG-grounded F1 descending so the hero series reads as a clean envelope.
    models.sort(key=lambda m: scores["kg_grounded"][m]["overall"][METRIC], reverse=True)

    n = len(models)
    n_set = len(SETTINGS)
    group_w = 0.80
    bar_w = group_w / n_set
    xs = list(range(n))

    fig, ax = plt.subplots(figsize=(7.0, 2.55))  # double-column width

    for si, (key, label, color, hatch, edge) in enumerate(SETTINGS):
        vals = [scores[key][m]["overall"][METRIC] for m in models]
        offset = (si - (n_set - 1) / 2) * bar_w
        bars = ax.bar([x + offset for x in xs], vals, bar_w,
                      label=label, color=color, hatch=hatch,
                      edgecolor=edge, linewidth=0.4)
        # Value labels only on the hero series to keep the chart uncluttered.
        if key == "kg_grounded":
            for b, v in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, v + 0.006, f"{v:.2f}",
                        ha="center", va="bottom", fontsize=7.0, color="#005A8F")

    ax.set_ylabel("Set F1", fontsize=9)
    ax.set_ylim(0, 0.36)
    ax.set_yticks([0.0, 0.1, 0.2, 0.3])
    ax.set_xticks(xs)
    ax.set_xticklabels([DISPLAY.get(m, m) for m in models], fontsize=7.2)
    ax.tick_params(axis="y", labelsize=7.5)
    ax.tick_params(axis="x", length=0)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#666666")
    ax.spines["bottom"].set_color("#666666")
    ax.yaxis.grid(True, color="#E6E6E6", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)

    ax.legend(loc="upper right", frameon=False, fontsize=7.6,
              handlelength=1.1, handletextpad=0.5, borderaxespad=0.2,
              ncol=3, columnspacing=1.2)

    fig.tight_layout(pad=0.4)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")

    # Echo the exact numbers drawn, for the audit trail.
    print("\nSet F1 drawn (model | closed_book | rag | kg_grounded):")
    for m in models:
        row = [scores[k][m]["overall"][METRIC] for k, _, _, _, _ in SETTINGS]
        print(f"  {m:<18} " + "  ".join(f"{v:.3f}" for v in row))


if __name__ == "__main__":
    main()
