"""Generate one SQLite query per packet item for the RAN1 text-to-SQL packet.

Usage: python gen.py <packet.json> <out.jsonl>
"""
import json
import re
import sys


def rel(x):
    """Release value to an integer (Rel-17, Release 17, 17, 17.6.0 -> 17; empty -> NULL)."""
    return (
        "NULLIF(CAST(trim(replace(replace(replace(replace(replace(replace("
        f"lower(trim({x})),'release',''),'rel',''),'r',''),'v',''),'-',''),'_','')) "
        "AS INTEGER), 0)"
    )


def q(s):
    return "'" + s.replace("'", "''") + "'"


ES = "lower(replace(replace(trim(COALESCE(ds.evidence_status,'')),'-','_'),' ','_'))"
SC = "lower(replace(replace(trim(COALESCE(ds.scope,'')),'-','_'),' ','_'))"
WG = "upper(replace(replace(replace(trim(COALESCE(mt.wg,'')),' ',''),'_',''),'-',''))"
LB = "upper(replace(COALESCE(mt.label,''),' ',''))"

DISP_COND = (
    f"({ES} IN ('verified','source_verified','sourceverified','verified_source','verified_from_source') "
    f"OR {ES} LIKE 'source_verified%') "
    f"AND ({SC} LIKE '%whole%' OR {SC} LIKE '%entire%' OR {SC} IN "
    "('document','doc','full','full_document','complete','complete_document','all','tdoc')) "
    f"AND ({WG} IN ('RAN1','R1','RANWG1','TSGRANWG1','WG1','TSGR1') "
    f"OR ({WG} = '' AND ({LB} LIKE 'RAN1%' OR {LB} LIKE 'R1-%' OR {LB} LIKE 'R1#%' OR {LB} LIKE 'TSGR1%')))"
)

COMMON = f"""doc_key(k, doc_id) AS (
  SELECT id, id FROM document
  UNION SELECT number, id FROM document WHERE number IS NOT NULL
),
pack_key(k, pack_id) AS (
  SELECT id, id FROM cr_pack
  UNION SELECT pack_number, id FROM cr_pack WHERE pack_number IS NOT NULL
),
meeting_key(k, meeting_id) AS (
  SELECT id, id FROM meeting
  UNION SELECT label, id FROM meeting WHERE label IS NOT NULL
),
mem(cr, pack_id) AS (
  SELECT cr, pack_id FROM cr_in_pack
  UNION SELECT cr, pack_id FROM pack_member
),
link(doc_id, pack_id) AS (
  SELECT DISTINCT dk.doc_id, pk.pack_id
  FROM mem m JOIN doc_key dk ON dk.k = m.cr JOIN pack_key pk ON pk.k = m.pack_id
),
mods(cr, section_id) AS (
  SELECT cr, section_id FROM cr_modifies_section
  UNION SELECT cr, section_id FROM section_modified_by
),
crsec(doc_id, spec, clause, srel) AS (
  SELECT DISTINCT dk.doc_id, s.spec, s.clause, {rel('s.release')}
  FROM mods mo JOIN doc_key dk ON dk.k = mo.cr JOIN section s ON s.id = mo.section_id
),
docrel(doc_id, number, trel) AS (
  SELECT id, COALESCE(number, id), {rel('target_release')} FROM document
),
qdisp(doc_id, code, wg_meeting) AS (
  SELECT DISTINCT dk.doc_id, ds.code, COALESCE(mt.label, mt.id)
  FROM disposition ds
  JOIN doc_key dk ON dk.k = ds.target
  JOIN resolution r ON r.id = ds.resolution_id
  JOIN meeting_key mk ON mk.k = r.meeting_id
  JOIN meeting mt ON mt.id = mk.meeting_id
  WHERE {DISP_COND}
)"""


def pack_clause_ctes(pack):
    return f""",
tp(pack_id, tsg_number) AS (
  SELECT id, tsg_number FROM cr_pack WHERE pack_number = {q(pack)} OR id = {q(pack)}
),
pc(doc_id, tsg_number, spec, clause, srel) AS (
  SELECT DISTINCT l.doc_id, tp.tsg_number, cs.spec, cs.clause, cs.srel
  FROM tp
  JOIN link l ON l.pack_id = tp.pack_id
  JOIN qdisp qd ON qd.doc_id = l.doc_id
  JOIN docrel dr ON dr.doc_id = l.doc_id
  JOIN crsec cs ON cs.doc_id = l.doc_id AND cs.srel = dr.trel
),
earlier_mods(spec, clause, srel, tsg_number, pack_number, tsg_meeting) AS (
  SELECT DISTINCT cs.spec, cs.clause, cs.srel, p.tsg_number, COALESCE(p.pack_number, p.id), p.tsg_meeting
  FROM crsec cs
  JOIN docrel dr ON dr.doc_id = cs.doc_id AND dr.trel = cs.srel
  JOIN link l ON l.doc_id = cs.doc_id
  JOIN cr_pack p ON p.id = l.pack_id
)"""


def family_latest_earlier(pack):
    return (
        "WITH " + COMMON + pack_clause_ctes(pack) + """,
cand(spec, clause, srel, tsg_number, pack_number, tsg_meeting) AS (
  SELECT pc.spec, pc.clause, pc.srel, e.tsg_number, e.pack_number, e.tsg_meeting
  FROM pc JOIN earlier_mods e
    ON e.spec = pc.spec AND e.clause = pc.clause AND e.srel = pc.srel
   AND e.tsg_number < pc.tsg_number
),
latest_mt(spec, clause, srel, mx) AS (
  SELECT spec, clause, srel, MAX(tsg_number) FROM cand GROUP BY spec, clause, srel
)
SELECT DISTINCT c.spec AS specification, c.clause AS clause, c.pack_number AS cr_pack, c.tsg_meeting AS tsg_meeting
FROM cand c JOIN latest_mt lm
  ON lm.spec = c.spec AND lm.clause = c.clause AND lm.srel = c.srel AND c.tsg_number = lm.mx"""
    )


def family_first_change(pack):
    return (
        "WITH " + COMMON + pack_clause_ctes(pack) + """
SELECT DISTINCT dr.number AS document, pc.spec AS specification, pc.clause AS clause
FROM pc JOIN docrel dr ON dr.doc_id = pc.doc_id
WHERE NOT EXISTS (
  SELECT 1 FROM earlier_mods e
  WHERE e.spec = pc.spec AND e.clause = pc.clause AND e.srel = pc.srel
    AND e.tsg_number < pc.tsg_number
)"""
    )


def family_same_clause(doc, release):
    return (
        "WITH " + COMMON + f""",
td(doc_id) AS (
  SELECT doc_id FROM doc_key WHERE k = {q(doc)}
),
tc(spec, clause, srel) AS (
  SELECT DISTINCT cs.spec, cs.clause, cs.srel
  FROM crsec cs JOIN td ON td.doc_id = cs.doc_id
  WHERE cs.srel = {release}
)
SELECT DISTINCT tc.clause AS clause, dr.number AS document, qd.code AS disposition,
       qd.wg_meeting AS wg_meeting, COALESCE(p.pack_number, p.id) AS cr_pack
FROM tc
JOIN crsec cs ON cs.spec = tc.spec AND cs.clause = tc.clause AND cs.srel = tc.srel
JOIN docrel dr ON dr.doc_id = cs.doc_id AND dr.trel = {release}
JOIN qdisp qd ON qd.doc_id = cs.doc_id
JOIN link l ON l.doc_id = cs.doc_id
JOIN cr_pack p ON p.id = l.pack_id
WHERE cs.doc_id NOT IN (SELECT doc_id FROM td)
  AND dr.number <> {q(doc)}"""
    )


def build(item):
    text = item["question"]
    fields = item["fields"]
    if text.startswith("Change request "):
        m = re.match(r"Change request (\S+) \(", text)
        r = re.search(r"targets Rel-(\d+)", text)
        assert m and r, item["id"]
        assert fields == ["clause", "document", "disposition", "wg_meeting", "cr_pack"], item["id"]
        return family_same_clause(m.group(1), int(r.group(1)))
    m = re.search(r"CR pack (RP-\d+)", text)
    assert m, item["id"]
    if "latest earlier TSG RAN meeting" in text:
        assert fields == ["specification", "clause", "cr_pack", "tsg_meeting"], item["id"]
        return family_latest_earlier(m.group(1))
    if "changes first" in text:
        assert fields == ["document", "specification", "clause"], item["id"]
        return family_first_change(m.group(1))
    raise ValueError(item["id"])


def main():
    packet = json.load(open(sys.argv[1], encoding="utf-8"))
    with open(sys.argv[2], "w", encoding="utf-8") as out:
        for item in packet["items"]:
            out.write(json.dumps({"id": item["id"], "sql": build(item)}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
