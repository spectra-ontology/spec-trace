"""Generate SQLite queries for the RAN4 text-to-SQL packet (run B).

Usage: python gen.py <packet.json> <out.jsonl>
"""
import json
import re
import sys


def norm(expr):
    return ("replace(replace(replace(lower(COALESCE(%s,'')),'-',''),'_',''),' ','')" % expr)


REL = "CAST(ltrim(upper(trim(%s)), 'RELASEV-_ .#') AS INTEGER)"

STATUS_OK = (
    "{n} LIKE '%source%' AND {n} LIKE '%verified%' AND {n} NOT LIKE '%unverif%' "
    "AND {n} NOT LIKE 'not%' AND {n} NOT LIKE '%notverif%' AND {n} NOT LIKE '%fail%'"
).format(n=norm("di.evidence_status"))

SCOPE_OK = (
    "({n} LIKE '%whole%' OR {n} IN ('document','doc','tdoc','full','fulldocument',"
    "'entire','entiredocument','all')) AND {n} NOT LIKE '%part%'"
).format(n=norm("di.scope"))

WG_NORM = "replace(replace(replace(upper(COALESCE(m.wg,'')),' ',''),'_',''),'-','')"
RAN4_OK = (
    "({w} IN ('RAN4','R4','RANWG4','WG4','TSGRANWG4','RAN04','TSGRAN4','RANWG04','TSGR4') "
    "OR (COALESCE(m.wg,'') = '' AND (upper(m.label) LIKE '%RAN4%' OR upper(m.label) LIKE '%R4%' "
    "OR upper(m.label) LIKE '%WG4%')))"
).format(w=WG_NORM)

COMMON = f"""docmap AS (
  SELECT id AS k, id AS doc FROM document
  UNION
  SELECT number AS k, id AS doc FROM document WHERE number IS NOT NULL
),
packs AS (
  SELECT id AS pid, COALESCE(pack_number, id) AS pnum, tsg_meeting,
         COALESCE(tsg_number, CAST(ltrim(upper(trim(tsg_meeting)), 'TSGRAN#_- P') AS INTEGER)) AS tn
  FROM cr_pack
),
packmap AS (
  SELECT id AS k, id AS pid FROM cr_pack
  UNION
  SELECT pack_number AS k, id AS pid FROM cr_pack WHERE pack_number IS NOT NULL
),
membership AS (
  SELECT DISTINCT dm.doc AS doc, pm.pid AS pid
  FROM (SELECT cr, pack_id FROM cr_in_pack UNION SELECT cr, pack_id FROM pack_member) x
  JOIN docmap dm ON dm.k = x.cr
  JOIN packmap pm ON pm.k = x.pack_id
),
modifies AS (
  SELECT DISTINCT dm.doc AS doc, x.section_id AS sid
  FROM (SELECT cr, section_id FROM cr_modifies_section
        UNION SELECT cr, section_id FROM section_modified_by) x
  JOIN docmap dm ON dm.k = x.cr
),
docrel AS (
  SELECT id AS doc, COALESCE(number, id) AS dnum, {REL % 'target_release'} AS rel
  FROM document
),
secn AS (
  SELECT id AS sid, spec, clause, {REL % 'release'} AS rel
  FROM section
),
qualdisp AS (
  SELECT DISTINCT dm.doc AS doc, di.code AS code, COALESCE(m.label, m.id) AS wg_meeting
  FROM disposition di
  JOIN docmap dm ON dm.k = di.target
  JOIN resolution r ON r.id = di.resolution_id
  JOIN meeting m ON m.id = r.meeting_id
  WHERE {STATUS_OK}
    AND {SCOPE_OK}
    AND {RAN4_OK}
)"""

PACK_BASE = """anchor AS (
  SELECT pid, tn FROM packs WHERE pnum = '{pack}' OR pid = '{pack}'
),
base AS (
  SELECT DISTINCT a.tn AS tn, d.doc AS doc, d.dnum AS dnum, s.spec AS spec, s.clause AS clause, s.rel AS rel
  FROM anchor a
  JOIN membership mb ON mb.pid = a.pid
  JOIN docrel d ON d.doc = mb.doc
  JOIN modifies mo ON mo.doc = d.doc
  JOIN secn s ON s.sid = mo.sid AND s.rel = d.rel
  WHERE d.doc IN (SELECT doc FROM qualdisp)
),
prior AS (
  SELECT DISTINCT k.spec AS spec, k.clause AS clause, k.rel AS rel, k.tn AS atn,
         p2.pid AS pid, p2.pnum AS pnum, p2.tsg_meeting AS tsg_meeting, p2.tn AS tn2
  FROM (SELECT DISTINCT spec, clause, rel, tn FROM base) k
  JOIN secn s2 ON s2.spec = k.spec AND s2.clause = k.clause AND s2.rel = k.rel
  JOIN modifies mo2 ON mo2.sid = s2.sid
  JOIN docrel d2 ON d2.doc = mo2.doc AND d2.rel = k.rel
  JOIN membership mb2 ON mb2.doc = d2.doc
  JOIN packs p2 ON p2.pid = mb2.pid
  WHERE p2.tn < k.tn
)"""

FIRST_FINAL = """SELECT DISTINCT b.dnum AS document, b.spec AS specification, b.clause AS clause
FROM base b
WHERE NOT EXISTS (
  SELECT 1 FROM prior p
  WHERE p.spec = b.spec AND p.clause = b.clause AND p.rel = b.rel AND p.atn = b.tn
)"""

LATEST_FINAL = """,
latest AS (
  SELECT spec, clause, rel, atn, MAX(tn2) AS mx FROM prior GROUP BY spec, clause, rel, atn
)
SELECT DISTINCT p.spec AS specification, p.clause AS clause, p.pnum AS cr_pack, p.tsg_meeting AS tsg_meeting
FROM prior p
JOIN latest l ON l.spec = p.spec AND l.clause = p.clause AND l.rel = p.rel AND l.atn = p.atn AND p.tn2 = l.mx"""

SIBLING = """anchor AS (
  SELECT doc FROM docrel WHERE dnum = '{cr}' OR doc = '{cr}'
),
asec AS (
  SELECT DISTINCT s.spec AS spec, s.clause AS clause, s.rel AS rel
  FROM anchor a
  JOIN modifies mo ON mo.doc = a.doc
  JOIN secn s ON s.sid = mo.sid
  WHERE s.rel = {rel}
)
SELECT DISTINCT k.clause AS clause, d2.dnum AS document, q.code AS disposition,
       q.wg_meeting AS wg_meeting, p.pnum AS cr_pack
FROM asec k
JOIN secn s2 ON s2.spec = k.spec AND s2.clause = k.clause AND s2.rel = k.rel
JOIN modifies mo2 ON mo2.sid = s2.sid
JOIN docrel d2 ON d2.doc = mo2.doc
JOIN qualdisp q ON q.doc = d2.doc
JOIN membership mb ON mb.doc = d2.doc
JOIN packs p ON p.pid = mb.pid
WHERE d2.rel = {rel}
  AND d2.doc NOT IN (SELECT doc FROM anchor)
  AND d2.dnum <> '{cr}'"""


def build(item):
    q = item["question"]
    fields = item["fields"]
    if "Keep the clauses that the pack changes first" in q:
        assert fields == ["document", "specification", "clause"], item["id"]
        pack = re.search(r"CR pack (RP-\d+)", q).group(1)
        return "WITH " + COMMON + ",\n" + PACK_BASE.format(pack=pack) + "\n" + FIRST_FINAL
    if "latest earlier TSG RAN meeting" in q:
        assert fields == ["specification", "clause", "cr_pack", "tsg_meeting"], item["id"]
        pack = re.search(r"CR pack (RP-\d+)", q).group(1)
        return "WITH " + COMMON + ",\n" + PACK_BASE.format(pack=pack) + LATEST_FINAL
    m = re.match(r"Change request (R4-\d+) \(CR \S+ to TS \S+\) targets Rel-(\d+)\.", q)
    if m:
        assert fields == ["clause", "document", "disposition", "wg_meeting", "cr_pack"], item["id"]
        cr, rel = m.group(1), int(m.group(2))
        assert f"in Rel-{rel}," in q and f"other than {cr}" in q, item["id"]
        return "WITH " + COMMON + ",\n" + SIBLING.format(cr=cr, rel=rel)
    raise ValueError("unrecognised question: " + item["id"])


def main():
    packet = json.load(open(sys.argv[1], encoding="utf-8"))
    with open(sys.argv[2], "w", encoding="utf-8") as out:
        for item in packet["items"]:
            out.write(json.dumps({"id": item["id"], "sql": build(item)}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
