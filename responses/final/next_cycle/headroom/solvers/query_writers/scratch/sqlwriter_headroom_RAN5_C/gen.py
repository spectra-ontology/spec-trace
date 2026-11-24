"""Generate SQLite queries for the RAN5 text2sql packet (run C).

Reads only the packet file and writes one JSON line per item.
"""
import json
import re
import sys

PACKET = sys.argv[1]
OUT = sys.argv[2]

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def norm_rel(expr):
    """Release text such as 'Rel-18', 'R18', '18' or '18.3.0' as the integer 18."""
    return (
        f"CAST(LTRIM(TRIM(COALESCE({expr}, '')), '{LETTERS}-_#: ') AS INTEGER)"
    )


def lit(value):
    return "'" + value.replace("'", "''") + "'"


VERIFIED = (
    "(LOWER(COALESCE(x.evidence_status, '')) LIKE '%source%verif%'"
    " AND LOWER(x.evidence_status) NOT LIKE '%unverif%'"
    " AND LOWER(x.evidence_status) NOT LIKE 'not%'"
    " AND LOWER(x.evidence_status) NOT LIKE '%fail%')"
)

SCOPE_NORM = "LOWER(REPLACE(REPLACE(TRIM(COALESCE(x.scope, '')), '-', '_'), ' ', '_'))"
WHOLE = (
    f"({SCOPE_NORM} LIKE '%whole%' OR {SCOPE_NORM} LIKE '%entire%'"
    f" OR {SCOPE_NORM} IN ('document', 'doc', 'full', 'full_document', 'tdoc', 'all'))"
)

WG_NORM = (
    "UPPER(REPLACE(REPLACE(REPLACE(TRIM(COALESCE(mt.wg, '')), ' ', ''), '_', ''), '-', ''))"
)
RAN5 = f"({WG_NORM} IN ('RAN5', 'R5', 'RANWG5', 'WG5', 'TSGRANWG5', 'RAN5WG'))"

BASE = f"""dk(doc_id, k) AS (
  SELECT id, id FROM document WHERE id IS NOT NULL
  UNION
  SELECT id, number FROM document WHERE number IS NOT NULL AND number <> ''
),
pk(pack_id, k) AS (
  SELECT id, id FROM cr_pack WHERE id IS NOT NULL
  UNION
  SELECT id, pack_number FROM cr_pack WHERE pack_number IS NOT NULL AND pack_number <> ''
),
mem(doc_id, pack_id) AS (
  SELECT DISTINCT dk.doc_id, pk.pack_id
  FROM (SELECT cr, pack_id FROM cr_in_pack UNION SELECT cr, pack_id FROM pack_member) e
  JOIN dk ON dk.k = e.cr
  JOIN pk ON pk.k = e.pack_id
),
doc(doc_id, number, rel) AS (
  SELECT id, COALESCE(NULLIF(number, ''), id), {norm_rel('target_release')} FROM document
),
cms(doc_id, section_id) AS (
  SELECT DISTINCT dk.doc_id, s.id
  FROM (SELECT cr, section_id FROM cr_modifies_section UNION SELECT cr, section_id FROM section_modified_by) e
  JOIN dk ON dk.k = e.cr
  JOIN section s ON s.id = e.section_id
),
cmod(doc_id, spec, clause, rel) AS (
  SELECT DISTINCT m.doc_id, s.spec, s.clause, d.rel
  FROM cms m
  JOIN doc d ON d.doc_id = m.doc_id
  JOIN section s ON s.id = m.section_id
  WHERE d.rel > 0 AND {norm_rel('s."release"')} = d.rel
),
vdisp(doc_id, code, wg_meeting) AS (
  SELECT DISTINCT dk.doc_id, x.code, COALESCE(mt.label, mt.id)
  FROM disposition x
  JOIN dk ON dk.k = x.target
  JOIN resolution r ON r.id = x.resolution_id
  JOIN meeting mt ON mt.id = r.meeting_id
  WHERE {VERIFIED} AND {WHOLE} AND {RAN5}
)"""


def pack_cands(pack):
    return f""",
tp(pack_id, tn) AS (
  SELECT DISTINCT p.id, p.tsg_number FROM cr_pack p
  WHERE p.id IN (SELECT pack_id FROM pk WHERE k = {lit(pack)})
),
cand(doc_id, spec, clause, rel, tn) AS (
  SELECT DISTINCT c.doc_id, c.spec, c.clause, c.rel, tp.tn
  FROM tp
  JOIN mem m ON m.pack_id = tp.pack_id
  JOIN cmod c ON c.doc_id = m.doc_id
  WHERE m.doc_id IN (SELECT doc_id FROM vdisp)
)"""


def q_first(pack):
    return (
        "WITH " + BASE + pack_cands(pack) + """
SELECT DISTINCT d.number AS document, cand.spec AS specification, cand.clause AS clause
FROM cand
JOIN doc d ON d.doc_id = cand.doc_id
WHERE NOT EXISTS (
  SELECT 1
  FROM cmod c2
  JOIN mem m2 ON m2.doc_id = c2.doc_id
  JOIN cr_pack p2 ON p2.id = m2.pack_id
  WHERE c2.spec = cand.spec AND c2.clause = cand.clause AND c2.rel = cand.rel
    AND p2.tsg_number < cand.tn
)"""
    )


def q_latest_earlier(pack):
    return (
        "WITH " + BASE + pack_cands(pack) + """,
ep(spec, clause, rel, pack_number, tsg_meeting, tsg_number) AS (
  SELECT DISTINCT cand.spec, cand.clause, cand.rel, p2.pack_number, p2.tsg_meeting, p2.tsg_number
  FROM cand
  JOIN cmod c2 ON c2.spec = cand.spec AND c2.clause = cand.clause AND c2.rel = cand.rel
  JOIN mem m2 ON m2.doc_id = c2.doc_id
  JOIN cr_pack p2 ON p2.id = m2.pack_id
  WHERE p2.tsg_number < cand.tn
),
mx(spec, clause, rel, mtn) AS (
  SELECT spec, clause, rel, MAX(tsg_number) FROM ep GROUP BY spec, clause, rel
)
SELECT DISTINCT ep.spec AS specification, ep.clause AS clause, ep.pack_number AS cr_pack, ep.tsg_meeting AS tsg_meeting
FROM ep
JOIN mx ON mx.spec = ep.spec AND mx.clause = ep.clause AND mx.rel = ep.rel AND ep.tsg_number = mx.mtn"""
    )


def q_siblings(cr):
    return (
        "WITH " + BASE + f""",
g(doc_id) AS (SELECT DISTINCT doc_id FROM dk WHERE k = {lit(cr)}),
gc(spec, clause, rel) AS (
  SELECT DISTINCT c.spec, c.clause, c.rel FROM cmod c WHERE c.doc_id IN (SELECT doc_id FROM g)
)
SELECT DISTINCT gc.clause AS clause, d.number AS document, v.code AS disposition,
  v.wg_meeting AS wg_meeting, p.pack_number AS cr_pack
FROM gc
JOIN cmod c2 ON c2.spec = gc.spec AND c2.clause = gc.clause AND c2.rel = gc.rel
JOIN doc d ON d.doc_id = c2.doc_id
JOIN vdisp v ON v.doc_id = c2.doc_id
JOIN mem m ON m.doc_id = c2.doc_id
JOIN cr_pack p ON p.id = m.pack_id
WHERE c2.doc_id NOT IN (SELECT doc_id FROM g)"""
    )


def build(item):
    q = item["question"]
    fields = item["fields"]
    m_pack = re.match(r"TSG RAN CR pack (RP-\d+) ", q)
    m_cr = re.match(r"Change request (R5-\d+) ", q)
    if m_pack and "changes first" in q and fields == ["document", "specification", "clause"]:
        return q_first(m_pack.group(1))
    if m_pack and "latest earlier TSG RAN meeting" in q and fields == [
        "specification", "clause", "cr_pack", "tsg_meeting"
    ]:
        return q_latest_earlier(m_pack.group(1))
    if m_cr and fields == ["clause", "document", "disposition", "wg_meeting", "cr_pack"]:
        return q_siblings(m_cr.group(1))
    raise ValueError(f"unrecognised item {item['id']}")


def main():
    with open(PACKET, encoding="utf-8") as fh:
        packet = json.load(fh)
    with open(OUT, "w", encoding="utf-8") as fh:
        for item in packet["items"]:
            fh.write(json.dumps({"id": item["id"], "sql": build(item)}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
