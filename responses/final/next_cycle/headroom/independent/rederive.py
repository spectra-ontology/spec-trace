"""Independent re-derivation of clause-set gold answers.

Tables are read with plain `SELECT * FROM <table>` into Python dicts; every join, filter, set difference and
per-clause maximum below is plain Python over those dicts. Section spec/release/clause come from the section
table columns (the gate parses them from the section identifier). TSG meeting numbers are parsed from the
tsg_meeting label and checked against the tsg_number column. Both record directions are derived.
Usage: python3 rederive.py <db_dir> <out.json> <admitted.jsonl>...
"""
import collections
import json
import random
import sqlite3
import sys
from pathlib import Path

FAMILIES = ("clause_neighbours", "first_change", "previous_pack")
SIDES = {"cr_side": ("cr_in_pack", "cr_modifies_section"), "container_side": ("pack_member", "section_modified_by")}


def table(con, name):
    cur = con.execute(f"SELECT * FROM {name}")
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, row)) for row in cur]


def load(db):
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    doc = {r["id"]: r for r in table(con, "document")}
    meeting = {r["id"]: r["label"] for r in table(con, "meeting")}
    resolution = {r["id"]: r["meeting_id"] for r in table(con, "resolution")}
    verified = collections.defaultdict(set)      # with the working-group meeting (clause_neighbours joins meeting)
    verified_any = set()                          # resolution present (pack families join resolution only)
    for r in table(con, "disposition"):
        if r["evidence_status"] == "source_verified" and r["scope"] == "whole_target" and r["resolution_id"] in resolution:
            verified_any.add(r["target"])
            mid = resolution[r["resolution_id"]]
            if mid in meeting:
                verified[r["target"]].add((r["code"], meeting[mid]))
    pack = {}
    label_mismatch = 0
    for r in table(con, "cr_pack"):
        label = r["tsg_meeting"]
        number = int(label[4:]) if label.startswith("RAN#") and label[4:].isdigit() else None
        if number != r["tsg_number"]:
            label_mismatch += 1
        pack[r["id"]] = {"number": r["pack_number"], "meeting": label, "n": number}
    section = {r["id"]: (r["spec"], r["release"], r["clause"]) for r in table(con, "section")}
    sides = {}
    for side, (member_table, change_table) in SIDES.items():
        packs_of, members = collections.defaultdict(set), collections.defaultdict(set)
        for r in table(con, member_table):
            if r["pack_id"] in pack:
                packs_of[r["cr"]].add(r["pack_id"])
                members[r["pack_id"]].add(r["cr"])
        changes, crs_of_section = collections.defaultdict(set), collections.defaultdict(set)
        missing_section = 0
        for r in table(con, change_table):
            if r["section_id"] not in section:
                missing_section += 1
                continue
            changes[r["cr"]].add(r["section_id"])
            crs_of_section[r["section_id"]].add(r["cr"])
        sides[side] = {"packs_of": packs_of, "members": members, "changes": changes,
                       "crs_of_section": crs_of_section, "missingSection": missing_section}
    return {"doc": doc, "verified": verified, "verified_any": verified_any, "pack": pack, "section": section, "sides": sides,
            "labelMismatch": label_mismatch}


def release(t, cr):
    return t["doc"][cr]["target_release"] if cr in t["doc"] else None


def neighbours(t, s, anchor):
    rows = set()
    rel = release(t, anchor)
    for sid in s["changes"].get(anchor, ()):
        spec, srel, clause = t["section"][sid]
        if srel != rel:
            continue
        for other in s["crs_of_section"][sid]:
            if other == anchor or release(t, other) != srel:
                continue
            for code, meeting in t["verified"].get(other, ()):
                for p in s["packs_of"].get(other, ()):
                    rows.add((clause, t["doc"][other]["number"], code, meeting, t["pack"][p]["number"]))
    return rows


def pack_family(t, s, anchor, family):
    rows = set()
    here = t["pack"][anchor]["n"]
    for cr in s["members"].get(anchor, ()):
        if cr not in t["doc"] or cr not in t["verified_any"]:
            continue
        for sid in s["changes"].get(cr, ()):
            spec, srel, clause = t["section"][sid]
            if release(t, cr) != srel:
                continue
            earlier = {p for e in s["crs_of_section"][sid] if release(t, e) == srel
                       for p in s["packs_of"].get(e, ()) if t["pack"][p]["n"] < here}
            if family == "first_change" and not earlier:
                rows.add((t["doc"][cr]["number"], spec, clause))
            elif family == "previous_pack" and earlier:
                latest = max(t["pack"][p]["n"] for p in earlier)
                rows.update((spec, clause, t["pack"][p]["number"], t["pack"][p]["meeting"])
                            for p in earlier if t["pack"][p]["n"] == latest)
    return rows


def main():
    db_dir, out = Path(sys.argv[1]), Path(sys.argv[2])
    items = [json.loads(line) for path in sys.argv[3:] for line in open(path)]
    chosen = []
    for family in FAMILIES:
        for wg in ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5"):
            cell = sorted((i for i in items if i["family"] == family and i["wg"] == wg), key=lambda i: i["id"])
            if cell:
                chosen.append(random.Random(f"independent:{family}:{wg}").choice(cell))
    tables, results = {}, []
    for item in chosen:
        if item["wg"] not in tables:
            tables[item["wg"]] = load(db_dir / f"{item['wg']}.sqlite")
        t = tables[item["wg"]]
        anchor = item["anchor"]
        anchor = anchor if item["family"] == "clause_neighbours" else (
            anchor if anchor in t["pack"] else next(p for p in t["pack"] if p.endswith(anchor.rsplit("/", 1)[-1])))
        gold = {tuple(r) for r in item["gold"]}
        derived = {side: (neighbours(t, s, anchor) if item["family"] == "clause_neighbours"
                          else pack_family(t, s, anchor, item["family"])) for side, s in t["sides"].items()}
        results.append({"id": item["id"], "wg": item["wg"], "family": item["family"], "goldRows": len(gold),
                        **{f"{side}Rows": len(rows) for side, rows in derived.items()},
                        **{f"{side}Equal": rows == gold for side, rows in derived.items()},
                        "goldOnly": sorted(gold - derived["container_side"])[:3],
                        "derivedOnly": sorted(derived["container_side"] - gold)[:3]})
        print(json.dumps(results[-1]), flush=True)
    report = {"dbDir": str(db_dir), "items": results, "checked": len(results),
              "allEqualBothSides": all(r["cr_sideEqual"] and r["container_sideEqual"] for r in results),
              "byFamily": dict(collections.Counter(r["family"] for r in results)),
              "tableNotes": {wg: {"tsgLabelNumberMismatch": t["labelMismatch"],
                                  "linksToMissingSection": {s: v["missingSection"] for s, v in t["sides"].items()}}
                             for wg, t in tables.items()}}
    out.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    print("checked", report["checked"], "allEqualBothSides", report["allEqualBothSides"])


if __name__ == "__main__":
    main()
