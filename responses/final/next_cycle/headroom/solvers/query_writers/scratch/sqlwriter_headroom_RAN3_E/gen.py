"""Write one SQLite query per packet item for the RAN3 text-to-SQL packet.

Three question families appear in the packet:
  first   : clauses that a CR pack changes before any earlier TSG RAN meeting
  latest  : packs of the latest earlier TSG RAN meeting touching the same clause
  cr      : other CRs of the same release that modify the clauses of one CR
"""
import json
import re
import sys

PACKET = sys.argv[1]
OUT = sys.argv[2]


def norm(expr):
    return ("REPLACE(REPLACE(REPLACE(LOWER(TRIM(COALESCE(%s,''))),'-',''),'_',''),' ','')" % expr)


def normrel(expr):
    base = ("REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(UPPER(TRIM(COALESCE(%s,''))),"
            "'RELEASE',''),'REL',''),'R',''),'-',''),'_',''),' ','')" % expr)
    return "(CASE WHEN INSTR(%s,'.')>0 THEN SUBSTR(%s,1,INSTR(%s,'.')-1) ELSE %s END)" % (base, base, base, base)


STATUS_OK = "('sourceverified','verifiedsource','verifiedfromsource','verified')"
SCOPE_OK = ("('wholedocument','document','whole','fulldocument','entiredocument','full','entire',"
            "'doc','wholedoc','tdoc','all','wholetdoc','fulltdoc')")
WG_OK = "('ran3','r3','ranwg3','wg3','tsgranwg3','tsgran3','ranw3')"

COMMON = f"""WITH
docref AS (
  SELECT id AS ref, id AS doc_id FROM document
  UNION
  SELECT number, id FROM document WHERE number IS NOT NULL
),
packref AS (
  SELECT id AS ref, id AS pack_key FROM cr_pack
  UNION
  SELECT pack_number, id FROM cr_pack WHERE pack_number IS NOT NULL
),
memb AS (
  SELECT DISTINCT dr.doc_id AS doc_id, pr.pack_key AS pack_key
  FROM (SELECT cr, pack_id FROM cr_in_pack UNION SELECT cr, pack_id FROM pack_member) m
  JOIN docref dr ON dr.ref = m.cr
  JOIN packref pr ON pr.ref = m.pack_id
),
docr AS (
  SELECT id AS doc_id, COALESCE(number, id) AS doc_no, {normrel('target_release')} AS rel FROM document
),
cmod AS (
  SELECT DISTINCT d.doc_id AS doc_id, s.spec AS spec, s.clause AS clause, d.rel AS rel
  FROM (SELECT cr, section_id FROM cr_modifies_section UNION SELECT cr, section_id FROM section_modified_by) x
  JOIN docref dr ON dr.ref = x.cr
  JOIN docr d ON d.doc_id = dr.doc_id
  JOIN section s ON s.id = x.section_id
  WHERE d.rel <> '' AND {normrel('s.release')} = d.rel
),
vdisp AS (
  SELECT DISTINCT dr.doc_id AS doc_id, di.code AS code, COALESCE(mt.label, mt.id) AS wg_meeting
  FROM disposition di
  JOIN docref dr ON dr.ref = di.target
  JOIN resolution rs ON rs.id = di.resolution_id
  JOIN meeting mt ON mt.id = rs.meeting_id
  WHERE {norm('di.evidence_status')} IN {STATUS_OK}
    AND {norm('di.scope')} IN {SCOPE_OK}
    AND ({norm('mt.wg')} IN {WG_OK}
         OR (mt.wg IS NULL AND ({norm('mt.label')} LIKE 'ran3%' OR {norm('mt.label')} LIKE 'r3%'
                                OR {norm('mt.label')} LIKE 'ranwg3%')))
)"""


def pack_ctes(pack):
    return f""",
tp AS (
  SELECT id AS pack_key, tsg_number AS tn FROM cr_pack WHERE pack_number = '{pack}' OR id = '{pack}'
),
pc AS (
  SELECT DISTINCT c.doc_id AS doc_id, c.spec AS spec, c.clause AS clause, c.rel AS rel, tp.tn AS tn
  FROM tp
  JOIN memb mb ON mb.pack_key = tp.pack_key
  JOIN cmod c ON c.doc_id = mb.doc_id
  WHERE c.doc_id IN (SELECT doc_id FROM vdisp)
),
earlier AS (
  SELECT DISTINCT k.spec AS spec, k.clause AS clause, k.rel AS rel, k.tn AS tn,
         p.tsg_number AS tsg_number, COALESCE(p.pack_number, p.id) AS pack_number, p.tsg_meeting AS tsg_meeting
  FROM (SELECT DISTINCT spec, clause, rel, tn FROM pc) k
  JOIN cmod c ON c.spec = k.spec AND c.clause = k.clause AND c.rel = k.rel
  JOIN memb mb ON mb.doc_id = c.doc_id
  JOIN cr_pack p ON p.id = mb.pack_key
  WHERE p.tsg_number < k.tn
)"""


def q_first(pack):
    return COMMON + pack_ctes(pack) + """
SELECT DISTINCT d.doc_no AS document, pc.spec AS specification, pc.clause AS clause
FROM pc
JOIN docr d ON d.doc_id = pc.doc_id
WHERE NOT EXISTS (
  SELECT 1 FROM earlier e
  WHERE e.spec = pc.spec AND e.clause = pc.clause AND e.rel = pc.rel AND e.tn = pc.tn
)"""


def q_latest(pack):
    return COMMON + pack_ctes(pack) + """
SELECT DISTINCT e.spec AS specification, e.clause AS clause, e.pack_number AS cr_pack, e.tsg_meeting AS tsg_meeting
FROM earlier e
WHERE e.tsg_number = (
  SELECT MAX(e2.tsg_number) FROM earlier e2
  WHERE e2.spec = e.spec AND e2.clause = e.clause AND e2.rel = e.rel AND e2.tn = e.tn
)"""


def q_cr(cr):
    return COMMON + f""",
tgt AS (
  SELECT id AS doc_id FROM document WHERE number = '{cr}' OR id = '{cr}'
),
tsec AS (
  SELECT DISTINCT c.spec AS spec, c.clause AS clause, c.rel AS rel
  FROM cmod c WHERE c.doc_id IN (SELECT doc_id FROM tgt)
)
SELECT DISTINCT ts.clause AS clause, d.doc_no AS document, v.code AS disposition,
       v.wg_meeting AS wg_meeting, COALESCE(p.pack_number, p.id) AS cr_pack
FROM tsec ts
JOIN cmod c ON c.spec = ts.spec AND c.clause = ts.clause AND c.rel = ts.rel
JOIN docr d ON d.doc_id = c.doc_id
JOIN vdisp v ON v.doc_id = c.doc_id
JOIN memb mb ON mb.doc_id = c.doc_id
JOIN cr_pack p ON p.id = mb.pack_key
WHERE c.doc_id NOT IN (SELECT doc_id FROM tgt) AND d.doc_no <> '{cr}'"""


FIELDS = {
    "first": ["document", "specification", "clause"],
    "latest": ["specification", "clause", "cr_pack", "tsg_meeting"],
    "cr": ["clause", "document", "disposition", "wg_meeting", "cr_pack"],
}


def classify(q):
    m = re.match(r"TSG RAN CR pack (RP-\d+) carries change requests from RAN3\.", q)
    if m:
        if "Keep the clauses that the pack changes first" in q:
            return "first", m.group(1)
        if "latest earlier TSG RAN meeting" in q:
            return "latest", m.group(1)
    m = re.match(r"Change request (R3-\d+) \(CR \d+ to TS [\d.]+\) targets Rel-\d+\.", q)
    if m and "other than " + m.group(1) in q:
        return "cr", m.group(1)
    raise ValueError("unrecognised question: " + q[:80])


def main():
    with open(PACKET, encoding="utf-8") as fh:
        packet = json.load(fh)
    lines = []
    for item in packet["items"]:
        fam, key = classify(item["question"])
        if item["fields"] != FIELDS[fam]:
            raise ValueError("field mismatch for " + item["id"])
        sql = {"first": q_first, "latest": q_latest, "cr": q_cr}[fam](key)
        lines.append(json.dumps({"id": item["id"], "sql": sql}, ensure_ascii=False))
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(len(lines))


if __name__ == "__main__":
    main()
