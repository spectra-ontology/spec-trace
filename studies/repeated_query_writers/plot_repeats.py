"""Render the repeated-writer panel in Figure 3 from the verified public summary."""
import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


MODELS = [
    ("claude-opus-5-5", "Opus 5.5"), ("claude-fable-5-2", "Fable 5.2"),
    ("claude-sonnet-5-5", "Sonnet 5.5"), ("claude-haiku-5-5", "Haiku 5.5"),
    ("gpt-6.2-sol", "Sol 6.2"), ("gpt-6.2-astra", "Astra 6.2"),
    ("gpt-6.1-terra", "Terra 6.1"), ("gpt-6-luna", "Luna 6"),
]
STYLES = [("sql", "SQL", "#245b79", "o", -.16),
          ("cypher", "Cypher", "#934820", "s", .16)]


def render(summary, output):
    series = {(row["model"], row["language"]): row for row in summary["full667"]}
    if len(series) != 16:
        raise ValueError("Expected eight models in both languages")
    plt.rcParams.update({"font.size": 7.3, "pdf.fonttype": 42, "font.family": "DejaVu Sans"})
    fig, ax = plt.subplots(figsize=(3.36, 2.28))
    fig.subplots_adjust(left=.29, right=.96, bottom=.17, top=.84)
    handles = []
    for language, label, color, marker, offset in STYLES:
        handles.append(Line2D([0], [0], color=color, marker=marker, lw=1, ms=3, label=label))
        for index, (model, _) in enumerate(MODELS):
            row = series[model, language]
            runs = row["perRepeat"]
            if set(runs) != set("ABCDEFGHIJ") or any(v["assigned"] != 667 for v in runs.values()):
                raise ValueError(f"Incomplete repetition for {model} {language}")
            exact = sum(v["exact"] for v in runs.values())
            if row["exact"] != exact or row["assigned"] != 6670:
                raise ValueError(f"Pooled count differs for {model} {language}")
            observed = [100 * v["exact"] / 667 for v in runs.values()]
            y = index + offset
            ax.plot([min(observed), max(observed)], [y, y], color=color, lw=1.05,
                    solid_capstyle="round", clip_on=False)
            ax.plot(100 * exact / 6670, y, color=color, marker=marker, ms=3, clip_on=False)
    ax.axhline(3.5, color="#bbb", lw=.5)
    ax.set(yticks=range(len(MODELS)), yticklabels=[name for _, name in MODELS],
           ylim=(7.55, -.55), xlim=(0, 100), xticks=[0, 25, 50, 75, 100],
           xlabel="Exact match (%)")
    ax.set_axisbelow(True)
    ax.grid(axis="x", color="#ddd", lw=.45)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", length=2, width=.5)
    ax.spines[["left", "right", "top"]].set_visible(False)
    ax.spines["bottom"].set_linewidth(.5)
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(.49, 1.0),
              ncol=2, borderpad=0, frameon=False, handlelength=1.5)
    fig.savefig(output, metadata={"Title": "Repeated query writing on 667 questions", "CreationDate": None})
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    render(json.loads(args.summary.read_text()), args.output)
