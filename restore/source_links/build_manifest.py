#!/usr/bin/env python3
"""Prepare an identifier/hash-only CR-form manifest from released benchmark gold.

Preparation reads the original local corpus to pin archive/member bytes. The
checker needs only this manifest, the public release, and downloaded archives.
Selection precedes source availability checks; unresolved sources stay visible.
"""
import argparse
import collections
import hashlib
import json
import re
import zipfile
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_graph(path):
    return json.loads(path.read_text())["@graph"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--release", type=Path, required=True)
    ap.add_argument("--repository", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--inventory", type=Path, required=True)
    ap.add_argument("--per-wg", type=int, default=2, help="0 selects every benchmark clause pair")
    args = ap.parse_args()
    release, repo = args.release.resolve(), args.repository.resolve()
    items = []
    for part in ("core", "ran5"):
        p = release / f"benchmark/items_final/gate/{part}/chain_items_admitted.jsonl"
        items.extend(json.loads(line) for line in p.read_text().splitlines() if line.strip())
    pairs = collections.defaultdict(lambda: collections.defaultdict(set))
    cr_packs = set()
    records = {}
    for wg in (f"RAN{n}" for n in range(1, 6)):
        folder = release / ("records/RAN5_graph_export/RAN5" if wg == "RAN5" else f"records/phase-4/{wg}")
        records[wg] = {r["@id"].removeprefix("tdoc:"): r for r in read_graph(folder / "cr_extensions.jsonld")}
    for item in items:
        wg, family = item["wg"], item["family"]
        fields = item["fields"]
        for row in item["gold"]:
            vals = dict(zip(fields, row))
            cr = vals.get("document", vals.get("final_document", item["anchor"].removeprefix("tdoc:")))
            pack = vals.get("cr_pack")
            if family == "pack_origin":
                pack = item["anchor"].rsplit("/", 1)[-1]
            if pack:
                cr_packs.add((wg, cr, pack))
            if family == "clause_history":
                pairs[wg][(cr, item["anchor"])].add(item["id"])
            elif family == "full_chain":
                r = records[wg].get(cr, {})
                sections = r.get("modifiesSection", [])
                if isinstance(sections, str):
                    sections = [sections]
                for section in sections:
                    if section.rsplit("-", 1)[-1] == vals["clause"]:
                        pairs[wg][(cr, section)].add(item["id"])
    portal = json.loads((repo / "data/inventory/RAN/portal_data_all_ran.json").read_text())
    pack_meta = {}
    for group in portal.values():
        for row in group:
            if row.get("tsg_tdoc") and row.get("tsg_meeting"):
                pack_meta.setdefault(row["tsg_tdoc"], row)
    source_map = {}
    for wg in pairs:
        p = repo / f"ontology/output/tsg/RAN/formal/parsed_cr/{wg}/cr_documents.json"
        parsed = json.loads(p.read_text())
        source_map[wg] = {r["tdoc_number"]: r for r in parsed.get("cr_documents", parsed.get("documents", []))}

    def source(wg, cr):
        form = source_map[wg].get(cr)
        if not form:
            return {"preparation_status": "parsed_source_path_unavailable"}
        local = repo / form["source_path"]
        pack = form.get("cr_pack_id")
        parts = Path(form["source_path"]).parts
        if "derived" not in parts or "TSG" not in parts or not pack:
            return {"preparation_status": "non_tsg_source_path", "source_path": form["source_path"]}
        rel = parts[parts.index("derived") + 1]
        archive = repo / f"data/corpus/tsg/RAN/formal/change-requests/{wg}/source/{rel}/TSG/{pack}.zip"
        info = {"pack": pack, "source_path": form["source_path"], "local_archive": str(archive.relative_to(repo))}
        meta = pack_meta.get(pack, {})
        meeting = meta.get("tsg_meeting", "")
        m = re.fullmatch(r"RAN#(\d+)(?:-e)?", meeting)
        if m:
            meetings = repo / "data/corpus/tsg/RAN/formal/meetings/TSG_RAN/source"
            folders = sorted(p.name for p in meetings.glob(f"TSGR_{m[1]}*")
                             if re.fullmatch(rf"TSGR_{m[1]}e?", p.name))
            directory = folders[0] if len(folders) == 1 else f"TSGR_{m[1]}"
            info["url"] = f"https://www.3gpp.org/ftp/tsg_ran/TSG_RAN/{directory}/Docs/{pack}.zip"
            info["url_directory_evidence"] = str(meetings.relative_to(repo) / directory)
        info["meeting"] = meeting
        if not archive.exists() or not local.exists():
            return dict(info, preparation_status="local_archive_or_form_unavailable")
        info.update(archive_sha256=sha(archive.read_bytes()), archive_bytes=archive.stat().st_size,
                    form_sha256=sha(local.read_bytes()), form_bytes=local.stat().st_size)
        try:
            with zipfile.ZipFile(archive) as z:
                exact = [n for n in z.namelist() if not n.endswith("/") and Path(n).name == local.name]
                matched = [n for n in exact if sha(z.read(n)) == info["form_sha256"]]
                if not matched:
                    return dict(info, preparation_status="native_member_not_byte_identical")
                member = sorted(matched)[0]
                info.update(member=member, member_sha256=info["form_sha256"])
        except (zipfile.BadZipFile, OSError) as e:
            return dict(info, preparation_status="archive_unreadable", error=type(e).__name__)
        return dict(info, preparation_status="ready_native_ooxml" if info.get("url") else "official_url_unresolved")

    cache = {}
    all_entries = []
    for wg in sorted(pairs):
        ranked = sorted(pairs[wg], key=lambda pair: sha((wg + "|" + "|".join(pair)).encode()))
        for rank, (cr, section) in enumerate(ranked, 1):
            key = (wg, cr)
            if key not in cache:
                cache[key] = source(*key)
            all_entries.append({"wg": wg, "cr": cr, "section": section, "rank_within_wg": rank,
                                "item_ids": sorted(pairs[wg][(cr, section)]), **cache[key]})
    chosen = [e for e in all_entries if not args.per_wg or e["rank_within_wg"] <= args.per_wg]
    parser = release / "code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/audit_clause_links.py"
    manifest = {"schema": "spectra-cr-source-links-v1", "release_commit": "fb610a6e3c748b809f4df46a0e3a2d20ad232a83",
                "selection": {"population": "unique CR-to-section pairs used by released full_chain/clause_history gold",
                              "order": "ascending SHA256(WG|CR|section), first per-wg; no availability filtering",
                              "per_wg": args.per_wg}, "reader_sha256": sha(parser.read_bytes()), "entries": chosen}
    by_status = collections.Counter(e["preparation_status"] for e in all_entries)
    all_gold_sources = {}
    for wg, cr, pack in sorted(cr_packs):
        if (wg, cr) not in cache:
            cache[(wg, cr)] = source(wg, cr)
        all_gold_sources[(wg, cr)] = cache[(wg, cr)]
    archives = {e.get("archive_sha256"): e.get("archive_bytes", 0) for e in all_entries if e.get("archive_sha256")}
    inv = {"benchmark_items": len(items), "benchmark_gold_rows": sum(len(x["gold"]) for x in items),
           "unique_gold_cr_pack_pairs": len(cr_packs), "unique_gold_crs": len({(w, c) for w, c, p in cr_packs}),
           "unique_gold_packs": len({p for w, c, p in cr_packs}),
           "benchmark_clause_pairs": len(all_entries), "unique_clause_crs": len({(e['wg'], e['cr']) for e in all_entries}),
           "local_source_status_by_pair": dict(by_status), "unique_locally_hashed_clause_archives": len(archives),
           "unique_locally_hashed_clause_archive_bytes": sum(archives.values()),
           "all_gold_source_status_by_cr": dict(collections.Counter(e['preparation_status'] for e in all_gold_sources.values())),
           "all_gold_unique_locally_hashed_archives": len({e['archive_sha256'] for e in all_gold_sources.values() if e.get('archive_sha256')}),
           "all_gold_unique_locally_hashed_archive_bytes": sum({e['archive_sha256']: e['archive_bytes'] for e in all_gold_sources.values() if e.get('archive_sha256')}.values()),
           "selected_pairs": len(chosen), "all_entries": all_entries,
           "scope": "Inventories benchmark gold; not the full 54,487/105,363-link census. 5,610 raw-pass links include other relation types."}
    for path, obj in ((args.out, manifest), (args.inventory, inv)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k:v for k,v in inv.items() if k != "all_entries"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
