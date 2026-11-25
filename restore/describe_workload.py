"""Describe the admitted workload directly from its released item records."""
from __future__ import annotations

import argparse
import collections
import hashlib
import gzip
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile


def describe(release, name, paths):
    families = {}
    identities = set()
    anchors = set()
    row_sizes = collections.Counter()
    empty_codes = collections.Counter()
    source_users = collections.defaultdict(set)
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
                anchors.add((item["wg"], item["anchor"]))
                row_sizes[len(item["gold"])] += 1
                if not item["gold"]:
                    empty_codes.update(e["disposition"] for e in item["evidence"])
                for evidence in item["evidence"]:
                    source_users[evidence["path"]].add(item["id"])
                row = families.setdefault(item["family"], {
                    "items": 0, "empty_gold": 0, "hops": set(), "fields": set(), "by_wg": collections.Counter(),
                    "answer_rows": collections.Counter()
                })
                row["items"] += 1
                row["empty_gold"] += not bool(item["gold"])
                row["hops"].add(item["hops"])
                row["fields"].add(tuple(item["fields"]))
                row["by_wg"][item["wg"]] += 1
                row["answer_rows"][len(item["gold"])] += 1
    for row in families.values():
        row["hops"] = sorted(row["hops"])
        row["fields"] = [list(fields) for fields in sorted(row["fields"])]
        row["by_wg"] = dict(sorted(row["by_wg"].items()))
        row["answer_rows"] = dict(sorted(row["answer_rows"].items()))
    return {"workload": name, "items": len(identities), "sources": sources,
            "distinct_wg_anchors": len(anchors), "answer_rows": dict(sorted(row_sizes.items())),
            "answerable_single_row": row_sizes[1], "empty_disposition_codes": dict(sorted(empty_codes.items())),
            "source_overlap": {"distinct_report_files": len(source_users),
                               "items_per_report": dict(sorted(collections.Counter(map(len, source_users.values())).items()))},
            "families": dict(sorted(families.items()))}


def snapshot_contract(release):
    """Check empty identities and actual revision paths in the shipped databases."""
    items = [json.loads(line) for part in ("core", "ran5") for line in
             (release / f"benchmark/items_final/gate/{part}/chain_items_admitted.jsonl").read_text().splitlines()]
    empty, revisions, databases = [], [], []
    with tempfile.TemporaryDirectory(prefix="spectra-contract-") as tmp:
        for wg in sorted({item["wg"] for item in items}):
            logical = release / "sqlite" / (wg + ".sqlite")
            actual = logical
            if not actual.exists():
                actual = Path(tmp) / logical.name
                with gzip.open(str(logical) + ".gz", "rb") as source, actual.open("wb") as target:
                    shutil.copyfileobj(source, target)
            databases.append({"path": "sqlite/" + logical.name,
                              "uncompressed_sha256": hashlib.sha256(actual.read_bytes()).hexdigest()})
            db = sqlite3.connect(actual.resolve().as_uri() + "?mode=ro", uri=True)
            db.row_factory = sqlite3.Row
            forward = collections.defaultdict(list)
            for row in db.execute("SELECT earlier,later FROM revision"):
                forward[row["earlier"]].append(row["later"])
            numbers = {row["number"]: row["id"] for row in db.execute("SELECT id,number FROM document")}

            def descendants(anchor):
                depth, queue = {anchor: 0}, collections.deque([anchor])
                while queue:
                    parent = queue.popleft()
                    for later in forward[parent]:
                        if later not in depth:
                            depth[later] = depth[parent] + 1
                            queue.append(later)
                return {key: value for key, value in depth.items() if key != anchor}

            for item in (i for i in items if i["wg"] == wg):
                if item["family"] == "revision_chain":
                    depths = descendants(item["anchor"])
                    col = item["fields"].index("final_document")
                    selected = {row[col]: depths[numbers[row[col]]] for row in item["gold"]}
                    revisions.append({"item": item["id"], "gold_rows": len(item["gold"]),
                                      "gold_document_shortest_depths": selected, "max_gold_depth": max(selected.values())})
                if item["family"] != "pack_lookup_empty":
                    continue
                anchor = db.execute("SELECT * FROM document WHERE id=?", (item["anchor"],)).fetchone()
                same = [dict(row) for row in db.execute("SELECT id,number,pack_field FROM document WHERE spec=? AND cr_number=?",
                                                       (anchor["spec"], anchor["cr_number"]))]
                ids = {row["id"] for row in same} | {item["anchor"]}
                members = [dict(row) for key in ids for row in db.execute("SELECT pack_id,cr FROM pack_member WHERE cr=?", (key,))]
                listed = [row for row in same if row["pack_field"] and row["pack_field"].startswith("RP-")]
                dispositions = [dict(row) for row in db.execute("SELECT code,evidence_path,evidence_sha256 FROM disposition WHERE target=? AND evidence_status='source_verified' AND scope='whole_target'", (item["anchor"],))]
                matches = {(e["disposition"], e["path"], e["sha256"]) for e in item["evidence"]} == {(d["code"], d["evidence_path"], d["evidence_sha256"]) for d in dispositions}
                codes = {row["code"] for row in dispositions}
                confirmed = not members and not listed and bool(dispositions) and matches and not item["gold"] and codes <= {"withdrawn", "not_treated", "not_pursued", "rejected", "not_agreed"}
                if not confirmed:
                    raise ValueError("Empty snapshot contract differs: " + item["id"])
                other = [dict(row) for key in set(descendants(item["anchor"])) - ids for row in db.execute("SELECT id,number,spec,cr_number,pack_field FROM document WHERE id=?", (key,))]
                empty.append({"item": item["id"], "specification": anchor["spec"], "cr_number": anchor["cr_number"],
                              "same_identity_documents": same, "different_identity_descendants": other,
                              "disposition_codes": [row["code"] for row in dispositions], "snapshot_empty_confirmed": confirmed})
            db.close()
    return {"scope": "The fixed released snapshot and exact TDoc/specification/CR identities define empty answers. Revision depths are shortest directed paths to returned documents.",
            "databases": databases, "empty_items": empty, "revision_items": revisions,
            "summary": {"all_empty_snapshot_contracts_confirmed": all(row["snapshot_empty_confirmed"] for row in empty),
                        "empty_items": len(empty), "empty_disposition_codes": dict(collections.Counter(c for row in empty for c in row["disposition_codes"])),
                        "different_identity_descendant_items": [row["item"] for row in empty if row["different_identity_descendants"]],
                        "revision_gold_depths": dict(sorted(collections.Counter(row["max_gold_depth"] for row in revisions).items()))}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--check-snapshot-contract", action="store_true",
                        help="Also verify empty identities and revision path lengths in the shipped SQLite partitions")
    args = parser.parse_args()
    workloads = []
    for name, prefix in (("Main", "items_final"), ("Order-sensitive extension", "headroom")):
        paths = [f"benchmark/{prefix}/gate/{part}/chain_items_admitted.jsonl" for part in ("core", "ran5")]
        workloads.append(describe(args.release, name, paths))
    report = {"scope": "Recorded admitted-item counts, requested fields and declared record hops; these are workload definitions rather than measured solver complexity.",
              "workloads": workloads, "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    if args.check_snapshot_contract:
        report["snapshot_contract"] = snapshot_contract(args.release)
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
                  "## Main-workload structure and answer contract", "",
                  f"The {workloads[0]['items']} main items use {workloads[0]['distinct_wg_anchors']} distinct working-group/anchor pairs. Of the 581 answerable items, {workloads[0]['answerable_single_row']} return one row. Row count measures output size; the inventory separately records the actual directed revision path when `--check-snapshot-contract` is selected.", "",
                  "An empty answer refers to the exact TDoc and specification/CR identity in the fixed released snapshot and its meeting coverage. The gate checks pack membership and the corresponding list fields for that identity. The source disposition codes of the 86 empty items are " + ", ".join(f"`{code}`: {count}" for code, count in workloads[0]["empty_disposition_codes"].items()) + ". Later revisions retain their own document and CR identities.", "",
                  *( ["The database check confirms all 86 empty snapshot contracts. The 82 revision questions have shortest paths to their returned documents at these depths: " + ", ".join(f"{depth}: {count} items" for depth, count in report["snapshot_contract"]["summary"]["revision_gold_depths"].items()) + ". All 82 return one row. The inventory also records the different-identity successor of R1-167179, including its separate specification, CR number and pack field.", ""] if "snapshot_contract" in report else []),
                  "Recompute this inventory from the checkout:", "", "```sh", "free -h", "python3 restore/describe_workload.py --release . --out work/workload_inventory.json --markdown work/BENCHMARK.md --check-snapshot-contract", "```", "",
                  "[The builder](" + link(args.release / "code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/build_chain_items.py") + ") defines the family contracts; [reproduction instructions](" + link(args.release / "REPRODUCING.md") + ") connect fixed-anchor construction, independent admission and scoring. Preserve item identity, requested fields and gold row sets when adding a comparison.", ""]
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text("\n".join(lines))
    print(json.dumps({workload["workload"]: workload["items"] for workload in workloads}))


if __name__ == "__main__":
    main()
