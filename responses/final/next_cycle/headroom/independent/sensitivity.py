"""For the same 15 items: does the independent derivation change when one condition is dropped? (read only)"""
import json, sys, random, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import rederive as r
db_dir = Path(sys.argv[1]); items = [json.loads(l) for p in sys.argv[2:] for l in open(p)]
chosen = []
for fam in r.FAMILIES:
    for wg in ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5"):
        cell = sorted((i for i in items if i["family"] == fam and i["wg"] == wg), key=lambda i: i["id"])
        chosen.append(random.Random(f"independent:{fam}:{wg}").choice(cell))
def pp_all_earlier(t, s, anchor):
    rows = set(); here = t["pack"][anchor]["n"]
    for cr in s["members"].get(anchor, ()):
        if cr not in t["doc"] or cr not in t["verified_any"]: continue
        for sid in s["changes"].get(cr, ()):
            spec, srel, clause = t["section"][sid]
            if r.release(t, cr) != srel: continue
            rows.update((spec, clause, t["pack"][p]["number"], t["pack"][p]["meeting"]) for e in s["crs_of_section"][sid]
                        if r.release(t, e) == srel for p in s["packs_of"].get(e, ()) if t["pack"][p]["n"] < here)
    return rows
def fc_any_release(t, s, anchor):
    rows = set(); here = t["pack"][anchor]["n"]
    for cr in s["members"].get(anchor, ()):
        if cr not in t["doc"] or cr not in t["verified_any"]: continue
        for sid in s["changes"].get(cr, ()):
            spec, srel, clause = t["section"][sid]
            if r.release(t, cr) != srel: continue
            same = {x for x, v in t["section"].items() if v[0] == spec and v[2] == clause}
            if not any(t["pack"][p]["n"] < here for x in same for e in s["crs_of_section"].get(x, ()) for p in s["packs_of"].get(e, ())):
                rows.add((t["doc"][cr]["number"], spec, clause))
    return rows
def cn_any_release(t, s, anchor):
    saved = r.release
    rows = set(); rel = r.release(t, anchor)
    for sid in s["changes"].get(anchor, ()):
        spec, srel, clause = t["section"][sid]
        if srel != rel: continue
        for other in s["crs_of_section"][sid]:
            if other == anchor or other not in t["doc"]: continue
            for code, meeting in t["verified"].get(other, ()):
                for p in s["packs_of"].get(other, ()):
                    rows.add((clause, t["doc"][other]["number"], code, meeting, t["pack"][p]["number"]))
    return rows
VAR = {"clause_neighbours": ("other change requests of any release", cn_any_release),
       "first_change": ("earlier change matched by (spec, clause) across releases", fc_any_release),
       "previous_pack": ("every earlier pack instead of the latest earlier meeting", pp_all_earlier)}
tables = {}; res = collections.defaultdict(lambda: [0, 0])
for it in chosen:
    if it["wg"] not in tables: tables[it["wg"]] = r.load(db_dir / f"{it['wg']}.sqlite")
    t = tables[it["wg"]]; s = t["sides"]["container_side"]
    gold = {tuple(x) for x in it["gold"]}
    name, fn = VAR[it["family"]]
    res[it["family"]][0] += 1; res[it["family"]][1] += fn(t, s, it["anchor"]) != gold
for fam, (n, d) in res.items(): print(fam, VAR[fam][0], f"changes gold in {d} of {n}")
