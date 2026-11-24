"""Generate one SQLite query per RAN5 packet item from the packet's schema and question text."""
import json
import re
import sys

PKT = sys.argv[1]
OUT = sys.argv[2]


def lit(s):
    return "'" + s.replace("'", "''") + "'"


def REL(e):
    # 'Rel-18', 'Rel18', 'Release 18', '18' -> '18'
    return (f"replace(replace(replace(replace(replace(lower(trim({e})),"
            f"'release',''),'rel',''),'-',''),' ',''),'_','')")


def NORM(e):
    return f"replace(replace(replace(lower(trim({e})),'_',''),'-',''),' ','')"


def WGN(e):
    return f"replace(replace(replace(upper(trim({e})),' ',''),'_',''),'-','')"


VERIFIED = f"{NORM('d.evidence_status')} = 'sourceverified'"
WHOLE = (f"{NORM('d.scope')} IN ('wholedocument','document','whole','doc','wholedoc',"
         f"'fulldocument','entiredocument','entire','full')")
RAN5 = (f"({WGN('m.wg')} IN ('RAN5','R5','RANWG5','WG5','TSGRANWG5','TSGR5') "
        f"OR (m.wg IS NULL AND ({WGN('m.label')} LIKE 'RAN5%' OR {WGN('m.label')} LIKE 'R5%' "
        f"OR {WGN('m.label')} LIKE 'TSGR5%')))")

COMMON = f"""dref(ref, did) AS (
  SELECT id, id FROM document
  UNION
  SELECT number, id FROM document WHERE number IS NOT NULL
),
inpack(did, pid) AS (
  SELECT r.did, l.pack_id FROM cr_in_pack l JOIN dref r ON r.ref = l.cr
  UNION
  SELECT r.did, l.pack_id FROM pack_member l JOIN dref r ON r.ref = l.cr
),
mods(did, sid) AS (
  SELECT r.did, l.section_id FROM cr_modifies_section l JOIN dref r ON r.ref = l.cr
  UNION
  SELECT r.did, l.section_id FROM section_modified_by l JOIN dref r ON r.ref = l.cr
),
vdisp(did, code, wg_meeting) AS (
  SELECT r.did, d.code, COALESCE(m.label, m.id)
  FROM disposition d
  JOIN dref r ON r.ref = d.target
  JOIN resolution res ON res.id = d.resolution_id
  JOIN meeting m ON m.id = res.meeting_id
  WHERE {VERIFIED} AND {WHOLE} AND {RAN5}
)"""


def pack_ctes(pack):
    p = lit(pack)
    return COMMON + f""",
tp(pid, tnum) AS (
  SELECT id, tsg_number FROM cr_pack WHERE pack_number = {p} OR id = {p}
),
base(did, dnum, spec, clause, rel, tnum) AS (
  SELECT DISTINCT doc.id, doc.number, s.spec, s.clause, {REL('s.release')}, tp.tnum
  FROM tp
  JOIN inpack ip ON ip.pid = tp.pid
  JOIN document doc ON doc.id = ip.did
  JOIN mods mo ON mo.did = doc.id
  JOIN section s ON s.id = mo.sid
  WHERE {REL('s.release')} = {REL('doc.target_release')}
    AND EXISTS (SELECT 1 FROM vdisp v WHERE v.did = doc.id)
),
bsec(spec, clause, rel, tnum) AS (
  SELECT DISTINCT spec, clause, rel, tnum FROM base
),
hist(spec, clause, rel, btnum, pack_number, tsg_meeting, tsg_number) AS (
  SELECT DISTINCT bs.spec, bs.clause, bs.rel, bs.tnum, p2.pack_number, p2.tsg_meeting, p2.tsg_number
  FROM bsec bs
  JOIN section s2 ON s2.spec = bs.spec AND s2.clause = bs.clause
  JOIN mods mo2 ON mo2.sid = s2.id
  JOIN document d2 ON d2.id = mo2.did
  JOIN inpack ip2 ON ip2.did = d2.id
  JOIN cr_pack p2 ON p2.id = ip2.pid
  WHERE {REL('s2.release')} = bs.rel
    AND {REL('d2.target_release')} = bs.rel
    AND p2.tsg_number < bs.tnum
)"""


def first_change(pack):
    return "WITH " + pack_ctes(pack) + """
SELECT DISTINCT b.dnum AS document, b.spec AS specification, b.clause AS clause
FROM base b
WHERE NOT EXISTS (
  SELECT 1 FROM hist h
  WHERE h.spec = b.spec AND h.clause = b.clause AND h.rel = b.rel AND h.btnum = b.tnum
)"""


def latest_earlier(pack):
    return "WITH " + pack_ctes(pack) + """
SELECT DISTINCT h.spec AS specification, h.clause AS clause, h.pack_number AS cr_pack, h.tsg_meeting AS tsg_meeting
FROM hist h
WHERE h.tsg_number = (
  SELECT MAX(h2.tsg_number) FROM hist h2
  WHERE h2.spec = h.spec AND h2.clause = h.clause AND h2.rel = h.rel AND h2.btnum = h.btnum
)"""


def same_clause_others(doc, rel):
    d = lit(doc)
    r = REL(lit(rel))
    return "WITH " + COMMON + f""",
x(did) AS (
  SELECT id FROM document WHERE number = {d} OR id = {d}
),
xs(spec, clause, rel) AS (
  SELECT DISTINCT s.spec, s.clause, {REL('s.release')}
  FROM x
  JOIN mods mo ON mo.did = x.did
  JOIN section s ON s.id = mo.sid
  WHERE {REL('s.release')} = {r}
)
SELECT DISTINCT xs.clause AS clause, d2.number AS document, v.code AS disposition,
       v.wg_meeting AS wg_meeting, p.pack_number AS cr_pack
FROM xs
JOIN section s2 ON s2.spec = xs.spec AND s2.clause = xs.clause
JOIN mods mo2 ON mo2.sid = s2.id
JOIN document d2 ON d2.id = mo2.did
JOIN vdisp v ON v.did = d2.id
JOIN inpack ip ON ip.did = d2.id
JOIN cr_pack p ON p.id = ip.pid
WHERE {REL('s2.release')} = xs.rel
  AND {REL('d2.target_release')} = xs.rel
  AND d2.id NOT IN (SELECT did FROM x)
  AND COALESCE(d2.number, '') <> {d}"""


def main():
    with open(PKT, encoding="utf-8") as f:
        pkt = json.load(f)
    lines = []
    for it in pkt["items"]:
        qtext = it["question"]
        fields = it["fields"]
        if "Keep the clauses that the pack changes first" in qtext:
            assert fields == ["document", "specification", "clause"], it["id"]
            pack = re.search(r"CR pack (RP-\d+)", qtext).group(1)
            sql = first_change(pack)
        elif "latest earlier TSG RAN meeting" in qtext:
            assert fields == ["specification", "clause", "cr_pack", "tsg_meeting"], it["id"]
            pack = re.search(r"CR pack (RP-\d+)", qtext).group(1)
            sql = latest_earlier(pack)
        elif qtext.startswith("Change request "):
            assert fields == ["clause", "document", "disposition", "wg_meeting", "cr_pack"], it["id"]
            m = re.match(r"Change request (R5-\d+) \(CR \S+ to TS \S+\) targets (Rel-\d+)\.", qtext)
            sql = same_clause_others(m.group(1), m.group(2))
        else:
            raise SystemExit("unhandled item " + it["id"])
        lines.append(json.dumps({"id": it["id"], "sql": sql}, ensure_ascii=False))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(len(lines))


if __name__ == "__main__":
    main()
