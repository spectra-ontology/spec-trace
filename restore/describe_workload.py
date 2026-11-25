"""Describe the admitted workload directly from its released item records."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
from pathlib import Path


def describe(release, name, paths):
    families = {}
    identities = set()
    sources = []
    for relative in paths:
        path = release / relative
        sources.append({"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                item = json.loads(line)
                if item["id"] in identities:
                    raise ValueError("Repeated item identity: " + item["id"])
                identities.add(item["id"])
                row = families.setdefault(item["family"], {
                    "items": 0, "empty_gold": 0, "hops": set(), "fields": set(), "by_wg": collections.Counter()
                })
                row["items"] += 1
                row["empty_gold"] += not bool(item["gold"])
                row["hops"].add(item["hops"])
                row["fields"].add(tuple(item["fields"]))
                row["by_wg"][item["wg"]] += 1
    for row in families.values():
        row["hops"] = sorted(row["hops"])
        row["fields"] = [list(fields) for fields in sorted(row["fields"])]
        row["by_wg"] = dict(sorted(row["by_wg"].items()))
    return {"workload": name, "items": len(identities), "sources": sources,
            "families": dict(sorted(families.items()))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    workloads = []
    for name, prefix in (("Main", "items_final"), ("Order-sensitive extension", "headroom")):
        paths = [f"benchmark/{prefix}/gate/{part}/chain_items_admitted.jsonl" for part in ("core", "ran5")]
        workloads.append(describe(args.release, name, paths))
    report = {"scope": "Recorded admitted-item counts, requested fields and declared record hops; these are workload definitions rather than measured solver complexity.",
              "workloads": workloads, "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if args.markdown:
        link = lambda path: Path(os.path.relpath(path, args.markdown.parent)).as_posix()
        lines = ["# Benchmark families and requested fields", "",
                 "The released questions exercise documentary operations over contributions, dispositions, meetings, packs and clauses. This inventory is computed from the admitted item records, with each source file bound by SHA-256 in [the machine-readable inventory](" + link(args.out) + ").", "",
                 "| Workload | Family | Items | Empty gold | Record hops | Requested fields | WG item counts |",
                 "|---|---|---:|---:|---|---|---|"]
        for workload in workloads:
            for family, row in workload["families"].items():
                fields = "; ".join(", ".join(f"`{field}`" for field in values) for values in row["fields"])
                counts = ", ".join(f"{wg}: {count}" for wg, count in row["by_wg"].items())
                lines.append(f"| {workload['workload']} | `{family}` | {row['items']} | {row['empty_gold']} | {', '.join(map(str, row['hops']))} | {fields} | {counts} |")
        lines += ["", "Record hops describe each family's construction contract. A solver may answer the released projection with a different number of joins. The item records retain their anchor, evidence and complete gold row set; the independent gate derives answers from the released relations.", "",
                  "Seven main family labels include an empty-gold variant of pack lookup. The three extension families add clause-set comparison and meeting-order conditions. Main and extension results retain their separate analysis scopes.", "",
                  "Recompute this inventory from the checkout:", "", "```sh", "free -h", "python3 restore/describe_workload.py --release . --out work/workload_inventory.json --markdown work/BENCHMARK.md", "```", "",
                  "[The builder](" + link(args.release / "code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/build_chain_items.py") + ") defines the family contracts; [reproduction instructions](" + link(args.release / "REPRODUCING.md") + ") connect fixed-anchor construction, independent admission and scoring. Preserve item identity, requested fields and gold row sets when adding a comparison.", ""]
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text("\n".join(lines))
    print(json.dumps({workload["workload"]: workload["items"] for workload in workloads}))


if __name__ == "__main__":
    main()
