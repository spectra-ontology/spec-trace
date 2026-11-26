#!/usr/bin/env python3
"""Bind family answer definitions to the released rows and reference queries.

This is an evaluation contract. Historical task exposure is recorded separately.
It measures complete sets in a finite record snapshot; original-document recall
is measured by the separate source censuses.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile


RULES = {
    "pack_lookup": ("Document TDoc ID; CR number is qualified by specification.",
                    "All packs containing the anchor, joined to their plenary meeting.",
                    "Pack membership and document-list pack fields agree at admission."),
    "pack_lookup_empty": ("Exact TDoc and specification/CR identity in the snapshot.",
                          "The pack-lookup row set is empty for this identity.",
                          "Whole-target source-verified dispositions use the five closed-without-pack codes; same-identity pack/list checks also pass."),
    "disposition_pack": ("Anchor TDoc ID.",
                         "Every eligible disposition/working-group meeting crossed with every recorded pack/plenary meeting.",
                         "Disposition evidence_status=source_verified and scope=whole_target; its resolution has a meeting."),
    "full_chain": ("Anchor TDoc ID; stored section IDs project to clause labels.",
                   "Disposition-pack rows crossed with the anchor's stored section-change links having a parsed clause label.",
                   "Same disposition eligibility as disposition_pack. This family uses all stored section links, including edition-projected links; it applies no target-release filter."),
    "revision_chain": ("Directed revision reachability from the anchor, with duplicate reachable IDs removed.",
                       "Every later reachable document with an eligible disposition and pack, including qualifying intermediate versions.",
                       "Anchor has revised dispositions at construction; returned versions have source_verified, whole_target dispositions whose resolution exists."),
    "clause_history": ("Exact section ID: specification, release and clause; children are separate IDs.",
                       "All documents changing that exact section in their own target release, with eligible dispositions/meetings/packs.",
                       "document.target_release=section.release, source_verified and whole_target; admission checks relevant pack sources."),
    "pack_origin": ("Anchor pack ID and its recorded member document IDs.",
                    "All recorded member documents having eligible dispositions and working-group meetings.",
                    "source_verified and whole_target; returned membership comes from pack-side records in the first reference direction."),
    "clause_neighbours": ("Anchor document's exact section IDs in its target release; other document ID differs from anchor.",
                          "Every same-release other document changing a shared exact section, with eligible disposition/meeting/pack.",
                          "Both documents' target releases equal the section release; other document has source_verified, whole_target disposition."),
    "first_change": ("Anchor pack; exact section ID and CR target release.",
                     "Each eligible anchor-pack member/section with no same-release changer in any pack at a smaller plenary meeting number.",
                     "Current member has source_verified, whole_target disposition; earlier changers use recorded membership regardless of disposition eligibility."),
    "previous_pack": ("Anchor pack; exact section ID and CR target release.",
                      "All packs tied at the largest plenary meeting number strictly below the anchor meeting for each touched section.",
                      "Current member has source_verified, whole_target disposition; earlier changers use recorded membership regardless of disposition eligibility. Sections with no earlier pack contribute no row."),
}
SCRIPTS = "code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def reference(release):
    path = release / SCRIPTS / "measure_relational_equivalence.py"
    spec = importlib.util.spec_from_file_location("spectra_answer_reference", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def boundary_checks(release, module):
    """Exercise meaning-changing alternatives on small declared record graphs."""
    path = release / SCRIPTS / "export_chain_records_sqlite.py"
    spec = importlib.util.spec_from_file_location("spectra_answer_schema", path)
    schema = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(schema)
    results = []
    cases = [
        ("whole_document_disposition", "disposition_pack", "a", {("agreed", "RAN1#1", "RP-3", "RAN#3")},
         [("disposition", {"id": "partial", "target": "a", "resolution_id": "r", "code": "rejected", "evidence_status": "source_verified", "scope": "partial_target"}),
          ("disposition", {"id": "pending", "target": "a", "resolution_id": "r", "code": "noted", "evidence_status": "pending", "scope": "whole_target"})]),
        ("exact_section_and_release", "clause_history", "s", {("A", "agreed", "RAN1#1", "RP-3")},
         [("section", {"id": "child", "spec": "38.1", "release": "Rel-18", "clause": "6.1.1"}),
          ("document", {"id": "b", "number": "B", "target_release": "Rel-18"}),
          ("document", {"id": "c", "number": "C", "target_release": "Rel-19"}),
          ("disposition", {"id": "db", "target": "b", "resolution_id": "r", "code": "agreed", "evidence_status": "source_verified", "scope": "whole_target"}),
          ("disposition", {"id": "dc", "target": "c", "resolution_id": "r", "code": "agreed", "evidence_status": "source_verified", "scope": "whole_target"}),
          ("membership", ("b", "p3")), ("membership", ("c", "p3")),
          ("change", ("b", "child")), ("change", ("c", "s"))]),
        ("full_chain_stored_edition_links", "full_chain", "a",
         {("agreed", "RAN1#1", "RP-3", "RAN#3", "6.1"), ("agreed", "RAN1#1", "RP-3", "RAN#3", "6.2")},
         [("section", {"id": "edition", "spec": "38.1", "release": "Rel-19", "clause": "6.2"}), ("change", ("a", "edition"))]),
        ("revision_intermediate_and_branches", "revision_chain", "a",
         {("B", "agreed", "RP-3"), ("C", "agreed", "RP-3"), ("D", "agreed", "RP-3")},
         [("document", {"id": name.lower(), "number": name}) for name in "BCD"] +
         [("disposition", {"id": "d" + name, "target": name.lower(), "resolution_id": "r", "code": "agreed", "evidence_status": "source_verified", "scope": "whole_target"}) for name in "BCD"] +
         [("membership", (name.lower(), "p3")) for name in "BCD"] +
         [("revision", {"earlier": x, "later": y}) for x, y in (("a", "b"), ("b", "c"), ("a", "d"))]),
        ("all_latest_earlier_ties", "previous_pack", "p3", {("38.1", "6.1", "RP-1", "RAN#2"), ("38.1", "6.1", "RP-2", "RAN#2")},
         [("document", {"id": name, "number": name.upper(), "target_release": "Rel-18"}) for name in ("b", "c", "d")] +
         [("cr_pack", {"id": name, "pack_number": "RP-" + name[1:], "tsg_meeting": "RAN#" + str(number), "tsg_number": number}) for name, number in (("p0", 1), ("p1", 2), ("p2", 2))] +
         [("membership", pair) for pair in (("b", "p0"), ("c", "p1"), ("d", "p2"))] +
         [("change", (name, "s")) for name in ("b", "c", "d")]),
        ("earlier_changer_needs_no_disposition", "first_change", "p3", set(),
         [("document", {"id": "b", "number": "B", "target_release": "Rel-18"}),
          ("cr_pack", {"id": "p1", "pack_number": "RP-1", "tsg_meeting": "RAN#1", "tsg_number": 1}),
          ("membership", ("b", "p1")), ("change", ("b", "s"))]),
        ("different_identity_successor_is_separate", "pack_lookup_empty", "empty", set(),
         [("document", {"id": "empty", "number": "EMPTY", "spec": "38.1", "cr_number": "1"}),
          ("revision", {"earlier": "empty", "later": "a"})]),
        ("new_section_first_in_snapshot", "first_change", "p3", {("A", "38.1", "6.1")}, []),
    ]
    for name, family, anchor, expected, extra in cases:
        db = sqlite3.connect(":memory:")
        try:
            db.executescript(schema.SCHEMA)
            base = [("document", {"id": "a", "number": "A", "target_release": "Rel-18", "spec": "38.1", "cr_number": "2"}),
                    ("meeting", {"id": "g", "label": "RAN1#1"}),
                    ("resolution", {"id": "r", "meeting_id": "g"}),
                    ("disposition", {"id": "da", "target": "a", "resolution_id": "r", "code": "agreed", "evidence_status": "source_verified", "scope": "whole_target"}),
                    ("cr_pack", {"id": "p3", "pack_number": "RP-3", "tsg_meeting": "RAN#3", "tsg_number": 3}),
                    ("section", {"id": "s", "spec": "38.1", "release": "Rel-18", "clause": "6.1"}),
                    ("membership", ("a", "p3")), ("change", ("a", "s"))]
            for table, values in base + extra:
                if table in ("membership", "change"):
                    targets = (("cr_in_pack", "pack_id"), ("pack_member", "pack_id")) if table == "membership" else (("cr_modifies_section", "section_id"), ("section_modified_by", "section_id"))
                    for target, column in targets:
                        db.execute(f"INSERT INTO {target}(cr,{column}) VALUES (?,?)", values)
                else:
                    columns = ",".join(values)
                    db.execute(f"INSERT INTO {table}({columns}) VALUES ({','.join('?' for _ in values)})", tuple(values.values()))
            for variant, names in module.VARIANTS.items():
                query = {**module.SQL, **module.CLAUSE_SET_SQL}[family].format(**names)
                actual = set(db.execute(query, {"anchor": anchor}))
                results.append({"case": name, "family": family, "variant": variant,
                                "expected": sorted(expected), "actual": sorted(actual), "pass": actual == expected})
        finally:
            db.close()
    return results


def check(release):
    module, implementation = reference(release)
    templates = {**module.SQL, **module.CLAUSE_SET_SQL}
    files, items = [], []
    for prefix in ("items_final", "headroom"):
        for part in ("core", "ran5"):
            path = release / f"benchmark/{prefix}/gate/{part}/chain_items_admitted.jsonl"
            rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
            files.append({"path": str(path.relative_to(release)), "sha256": digest(path), "items": len(rows)})
            items.extend(dict(row, workload=prefix) for row in rows)
    if len({row["id"] for row in items}) != len(items):
        raise ValueError("Duplicate item identity")
    if set(templates) != set(RULES) or {row["family"] for row in items} != set(RULES):
        raise ValueError("Reference, definition and actual family populations differ")
    counts = Counter(row["family"] for row in items)
    families = {}
    for family, (identity, answer, eligibility) in RULES.items():
        group = [row for row in items if row["family"] == family]
        fields = {tuple(row["fields"]) for row in group}
        if len(fields) != 1:
            raise ValueError("Inconsistent requested fields: " + family)
        families[family] = {"items": counts[family], "fields": list(next(iter(fields))),
                            "identity": identity, "answer_universe": answer, "eligibility": eligibility,
                            "queries": {variant: templates[family].format(**names).strip()
                                        for variant, names in module.VARIANTS.items()}}
    mismatches, databases, compared = [], [], Counter()
    population, coverage = {}, {}
    with tempfile.TemporaryDirectory(prefix="spectra-answer-contract-") as temporary:
        for wg in sorted({row["wg"] for row in items}):
            original = release / f"sqlite/{wg}.sqlite"
            actual = original
            if not actual.exists():
                original = original.with_suffix(".sqlite.gz")
                actual = Path(temporary) / f"{wg}.sqlite"
                with gzip.open(original, "rb") as source, actual.open("wb") as target:
                    shutil.copyfileobj(source, target)
            databases.append({"path": str(original.relative_to(release)), "sha256": digest(original),
                              "uncompressed_sha256": digest(actual)})
            db = sqlite3.connect(actual.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
            try:
                db.execute("PRAGMA query_only=ON")
                tables = sorted(name for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='table'"))
                population[wg] = {name: db.execute('SELECT count(*) FROM "' + name + '"').fetchone()[0] for name in tables}
                coverage[wg] = {
                    "working_group_meeting_labels": [row[0] for row in db.execute("SELECT DISTINCT label FROM meeting ORDER BY label")],
                    "plenary_meeting_labels": [row[0] for row in db.execute("SELECT DISTINCT tsg_meeting FROM cr_pack ORDER BY tsg_number,tsg_meeting")],
                    "section_specification_release_counts": [
                        {"specification": spec, "release": release, "sections": n}
                        for spec, release, n in db.execute("SELECT spec,release,count(*) FROM section GROUP BY spec,release ORDER BY spec,release")],
                }
                for item in (row for row in items if row["wg"] == wg):
                    expected = {tuple(row) for row in item["gold"]}
                    if any(len(row) != len(item["fields"]) for row in expected):
                        raise ValueError("Invalid row width: " + item["id"])
                    for variant, query in families[item["family"]]["queries"].items():
                        actual_rows = set(db.execute(query, {"anchor": item["anchor"]}))
                        compared[variant] += 1
                        if actual_rows != expected:
                            mismatches.append({"item": item["id"], "variant": variant,
                                               "only_in_gold": sorted(expected - actual_rows),
                                               "only_in_reference": sorted(actual_rows - expected)})
            finally:
                db.close()
    boundaries = boundary_checks(release, module)
    return {"scope": "Complete projected row sets over the fixed released record snapshot and each item's WG partition.",
            "source_scope": "Source censuses and original-document readers measure source coverage and stored-link confirmation separately.",
            "historical_exposure": "This evaluation definition is distinct from the historical solver-task exposure; original tasks and questions remain unchanged.",
            "row_semantics": "Distinct projected rows; exact section identity, directed revision reachability and numeric plenary order follow the family-specific queries.",
            "item_files": files, "reference": {"path": str(implementation.relative_to(release)), "sha256": digest(implementation)},
            "databases": databases, "record_population": population, "coverage": coverage,
            "families": families, "semantic_boundary_checks": boundaries,
            "summary": {"items": len(items), "compared_by_direction": dict(compared),
                        "mismatches": mismatches, "all_row_sets_match": not mismatches,
                        "semantic_boundary_checks": len(boundaries), "all_boundaries_pass": all(row["pass"] for row in boundaries)}}


def markdown(report):
    lines = ["# Answer universe and family contracts", "",
             "SPECTRA supplies exact answer sets for documentary operations over its released record snapshot. Each item identifies its working-group partition, anchor and requested fields. The table below states which records contribute rows; the machine-readable contract includes both executable reference directions and their input hashes.", "",
             "| Family | Items | Identity and universe | Eligibility |", "|---|---:|---|---|"]
    for family, row in report["families"].items():
        lines.append(f"| `{family}` | {row['items']} | {row['identity']} {row['answer_universe']} | {row['eligibility']} |")
    lines += ["", "The two reference directions independently use CR-side and container-side membership/change records. The checker compares both with every released main and extension gold set and reports actual differences.", "",
              "## Coverage and interpretation", "",
              "Snapshot completeness means that every qualifying projected row in the specified records is returned. Source-document coverage and source recall are evaluated by the separate censuses and native-source readers. Stored-link confirmation uses the stored-link population as its denominator.", "",
              "The historical solver tasks, schemas and questions retain their original bytes. This explicit evaluation contract and the separately recorded task-exposure audit distinguish the scoring definition from information actually supplied to a historical model.", "",
              "Recompute the contract and its row-set comparisons from the release root:", "", "```sh", "free -h",
              "python3 -B restore/check_answer_contract.py --release . --out work/answer_contract.json --markdown work/ANSWER_CONTRACT.md", "```", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    report = check(args.release.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(markdown(report))
    print(json.dumps(report["summary"]))
    if not report["summary"]["all_row_sets_match"] or not report["summary"]["all_boundaries_pass"]:
        raise SystemExit("Reference rows differ; inspect the preserved differences")


if __name__ == "__main__":
    main()
