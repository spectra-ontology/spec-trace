"""Generate SQLite queries for the RAN3 text-to-SQL packet (run D).

Usage: python gen.py <packet.json> <out.jsonl>
"""
import json
import re
import sys


def rel_norm(expr):
    """Release text -> integer release number ('Rel-16', 'R16', '16', '16.3.0' -> 16)."""
    inner = f"upper(trim({expr}))"
    for token in ("RELEASE", "REL", "-", " ", "_"):
        inner = f"replace({inner}, '{token}', '')"
    return f"CAST(ltrim({inner}, 'RV.') AS INTEGER)"


def sep_norm(expr, case="lower"):
    inner = f"{case}(trim({expr}))"
    for token in ("_", "-", " "):
        inner = f"replace({inner}, '{token}', '')"
    return inner


EVID = sep_norm("disp.evidence_status")
SCOPE = sep_norm("disp.scope")
WG = sep_norm("m.wg", case="upper")

COMMON = f"""
lp AS (
  SELECT cr, pack_id FROM cr_in_pack
  UNION
  SELECT cr, pack_id FROM pack_member
),
ls AS (
  SELECT cr, section_id FROM cr_modifies_section
  UNION
  SELECT cr, section_id FROM section_modified_by
),
dk AS (
  SELECT id AS doc_id, id AS k FROM document
  UNION
  SELECT id AS doc_id, number AS k FROM document WHERE number IS NOT NULL
),
pk AS (
  SELECT id AS pid, id AS k FROM cr_pack
  UNION
  SELECT id AS pid, pack_number AS k FROM cr_pack WHERE pack_number IS NOT NULL
),
docs AS (
  SELECT id AS doc_id, COALESCE(number, id) AS docnum, {rel_norm('target_release')} AS trel
  FROM document
),
cp_map AS (
  SELECT DISTINCT dk.doc_id AS doc_id, pk.pid AS pid
  FROM lp JOIN dk ON dk.k = lp.cr JOIN pk ON pk.k = lp.pack_id
),
cs_map AS (
  SELECT DISTINCT dk.doc_id AS doc_id, s.spec AS spec, s.clause AS clause,
         {rel_norm('s."release"')} AS rel
  FROM ls JOIN dk ON dk.k = ls.cr JOIN section s ON s.id = ls.section_id
),
gd AS (
  SELECT DISTINCT dk.doc_id AS doc_id, disp.code AS code, m.label AS wg_label
  FROM disposition disp
  JOIN dk ON dk.k = disp.target
  JOIN resolution r ON r.id = disp.resolution_id
  JOIN meeting m ON m.id = r.meeting_id
  WHERE ({EVID} LIKE '%sourceverified%' OR {EVID} IN ('verifiedsource', 'verifiedfromsource', 'verifiedagainstsource'))
    AND {EVID} NOT LIKE '%not%' AND {EVID} NOT LIKE '%unverified%'
    AND {SCOPE} IN ('document', 'wholedocument', 'whole', 'wholedoc', 'fulldocument', 'full', 'entiredocument', 'entire', 'doc')
    AND ({WG} LIKE '%RAN3%' OR {WG} LIKE '%RANWG3%' OR {WG} IN ('R3', 'WG3'))
)"""


def esc(s):
    return s.replace("'", "''")


def pack_cand(pack, rels):
    rel_list = ", ".join(str(r) for r in rels)
    return f"""
target_pack AS (
  SELECT id AS pid, tsg_number AS tnum FROM cr_pack
  WHERE pack_number = '{esc(pack)}' OR id = '{esc(pack)}'
),
cand AS (
  SELECT DISTINCT d.doc_id AS doc_id, d.docnum AS docnum, cs.spec AS spec, cs.clause AS clause,
         cs.rel AS rel, tp.tnum AS tnum
  FROM target_pack tp
  JOIN cp_map cm ON cm.pid = tp.pid
  JOIN docs d ON d.doc_id = cm.doc_id
  JOIN cs_map cs ON cs.doc_id = d.doc_id AND cs.rel = d.trel
  WHERE d.trel IN ({rel_list})
    AND EXISTS (SELECT 1 FROM gd WHERE gd.doc_id = d.doc_id)
),
cc AS (
  SELECT DISTINCT spec, clause, rel, tnum FROM cand
),
other_packs AS (
  SELECT DISTINCT cs2.spec AS spec, cs2.clause AS clause, cs2.rel AS rel,
         p2.tsg_number AS pnum, COALESCE(p2.pack_number, p2.id) AS pack_number, p2.tsg_meeting AS tsg_meeting
  FROM (SELECT DISTINCT spec, clause, rel FROM cand) k
  JOIN cs_map cs2 ON cs2.spec = k.spec AND cs2.clause = k.clause AND cs2.rel = k.rel
  JOIN docs d2 ON d2.doc_id = cs2.doc_id AND d2.trel = cs2.rel
  JOIN cp_map cm2 ON cm2.doc_id = d2.doc_id
  JOIN cr_pack p2 ON p2.id = cm2.pid
)"""


def family_first(pack, rels):
    return (
        "WITH" + COMMON + "," + pack_cand(pack, rels) + """
SELECT DISTINCT c.docnum AS document, c.spec AS specification, c.clause AS clause
FROM cand c
WHERE NOT EXISTS (
  SELECT 1 FROM other_packs e
  WHERE e.spec = c.spec AND e.clause = c.clause AND e.rel = c.rel AND e.pnum < c.tnum
)"""
    )


def family_latest(pack, rels):
    return (
        "WITH" + COMMON + "," + pack_cand(pack, rels) + """,
eb AS (
  SELECT c.spec AS spec, c.clause AS clause, c.rel AS rel, e.pnum AS pnum,
         e.pack_number AS pack_number, e.tsg_meeting AS tsg_meeting
  FROM cc c
  JOIN other_packs e ON e.spec = c.spec AND e.clause = c.clause AND e.rel = c.rel AND e.pnum < c.tnum
),
mx AS (
  SELECT spec, clause, rel, MAX(pnum) AS mp FROM eb GROUP BY spec, clause, rel
)
SELECT DISTINCT eb.spec AS specification, eb.clause AS clause, eb.pack_number AS cr_pack,
       eb.tsg_meeting AS tsg_meeting
FROM eb JOIN mx ON mx.spec = eb.spec AND mx.clause = eb.clause AND mx.rel = eb.rel AND eb.pnum = mx.mp"""
    )


def family_comod(doc, rel):
    return (
        "WITH" + COMMON + f""",
anchor AS (
  SELECT id AS doc_id FROM document WHERE number = '{esc(doc)}' OR id = '{esc(doc)}'
),
asec AS (
  SELECT DISTINCT cs.spec AS spec, cs.clause AS clause, cs.rel AS rel
  FROM anchor a JOIN cs_map cs ON cs.doc_id = a.doc_id
  WHERE cs.rel = {rel}
)
SELECT DISTINCT asec.clause AS clause, d2.docnum AS document, gd.code AS disposition,
       gd.wg_label AS wg_meeting, COALESCE(p.pack_number, p.id) AS cr_pack
FROM asec
JOIN cs_map cs2 ON cs2.spec = asec.spec AND cs2.clause = asec.clause AND cs2.rel = asec.rel
JOIN docs d2 ON d2.doc_id = cs2.doc_id AND d2.trel = {rel}
JOIN gd ON gd.doc_id = d2.doc_id
JOIN cp_map cm ON cm.doc_id = d2.doc_id
JOIN cr_pack p ON p.id = cm.pid
WHERE d2.doc_id NOT IN (SELECT doc_id FROM anchor) AND d2.docnum <> '{esc(doc)}'"""
    )


RE_PACK = re.compile(r"TSG RAN CR pack (RP-\d+) carries")
RE_RELS = re.compile(r"the release that change request targets \(([^)]*)\)")
RE_DOC = re.compile(r"Change request (R3-\d+) \(CR \S+ to TS [\d.]+\) targets Rel-(\d+)\.")


def build(item):
    q = item["question"]
    fields = item["fields"]
    if fields == ["document", "specification", "clause"]:
        pack = RE_PACK.search(q).group(1)
        rels = [int(x) for x in re.findall(r"Rel-(\d+)", RE_RELS.search(q).group(1))]
        assert "Keep the clauses that the pack changes first" in q
        return family_first(pack, rels)
    if fields == ["specification", "clause", "cr_pack", "tsg_meeting"]:
        pack = RE_PACK.search(q).group(1)
        rels = [int(x) for x in re.findall(r"Rel-(\d+)", RE_RELS.search(q).group(1))]
        assert "latest earlier TSG RAN meeting" in q
        return family_latest(pack, rels)
    if fields == ["clause", "document", "disposition", "wg_meeting", "cr_pack"]:
        m = RE_DOC.search(q)
        doc, rel = m.group(1), int(m.group(2))
        assert f"other than {doc}" in q and f"Rel-{rel} change requests" in q
        return family_comod(doc, rel)
    raise ValueError(f"unknown family: {item['id']}")


def main():
    packet = json.load(open(sys.argv[1], encoding="utf-8"))
    with open(sys.argv[2], "w", encoding="utf-8") as out:
        for item in packet["items"]:
            sql = " ".join(build(item).split())
            out.write(json.dumps({"id": item["id"], "sql": sql}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
