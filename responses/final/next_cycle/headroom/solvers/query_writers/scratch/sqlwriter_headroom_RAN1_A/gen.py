"""Generate one SQLite query per packet item for the RAN1 text-to-SQL packet.

Three question families appear in the packet:
  A  latest earlier CR pack per clause   -> specification, clause, cr_pack, tsg_meeting
  B  clauses the pack changes first      -> document, specification, clause
  C  sibling CRs on the anchor's clauses -> clause, document, disposition, wg_meeting, cr_pack
"""
import json
import re
import sys

PACKET = sys.argv[1]
OUT = sys.argv[2]


def relnorm(col):
    # 'Rel-17', 'Release 17', 'R17', '17', '17.3.0' -> '17'
    return (
        "ltrim(replace(replace(replace(replace(replace(lower(trim(" + col + ")),"
        "'release',''),'rel',''),'-',''),' ',''),'_',''),'r')"
    )


def cut_dot(col):
    return f"CASE WHEN instr({col},'.')>0 THEN substr({col},1,instr({col},'.')-1) ELSE {col} END"


COMMON = f"""
mods AS (SELECT cr, section_id FROM cr_modifies_section UNION SELECT cr, section_id FROM section_modified_by),
mems AS (SELECT cr, pack_id FROM cr_in_pack UNION SELECT cr, pack_id FROM pack_member),
dkey AS (SELECT id AS doc_id, id AS k FROM document UNION SELECT id AS doc_id, number AS k FROM document WHERE number IS NOT NULL),
pkey AS (SELECT id AS pack_id, id AS k FROM cr_pack UNION SELECT id AS pack_id, pack_number AS k FROM cr_pack WHERE pack_number IS NOT NULL),
doc0 AS (SELECT id, number, {relnorm('target_release')} AS r FROM document),
docr AS (SELECT id, COALESCE(number, id) AS number, {cut_dot('r')} AS rel FROM doc0),
sec0 AS (SELECT id, spec, clause, {relnorm(chr(34)+'release'+chr(34))} AS r FROM section),
secr AS (SELECT id, spec, clause, {cut_dot('r')} AS rel FROM sec0),
cm AS (SELECT DISTINCT d.id AS doc_id, d.number AS doc_number, s.spec AS spec, s.rel AS rel, s.clause AS clause
       FROM mods m JOIN dkey k ON k.k = m.cr JOIN docr d ON d.id = k.doc_id JOIN secr s ON s.id = m.section_id
       WHERE s.rel IS NOT NULL AND s.rel <> '' AND s.rel = d.rel AND s.clause IS NOT NULL),
pk AS (SELECT DISTINCT k.doc_id AS doc_id, p.id AS pack_id, p.pack_number AS pack_number,
              p.tsg_meeting AS tsg_meeting, p.tsg_number AS tsg_number
       FROM mems m JOIN dkey k ON k.k = m.cr JOIN pkey pq ON pq.k = m.pack_id JOIN cr_pack p ON p.id = pq.pack_id),
ok AS (SELECT DISTINCT k.doc_id AS doc_id, ds.code AS code, COALESCE(mt.label, mt.id) AS wg_meeting
       FROM disposition ds JOIN dkey k ON k.k = ds.target
       JOIN resolution r ON r.id = ds.resolution_id JOIN meeting mt ON mt.id = r.meeting_id
       WHERE upper(replace(replace(replace(trim(mt.wg),' ',''),'_',''),'-','')) IN ('RAN1','R1','RANWG1','TSGRANWG1','WG1')
         AND lower(ds.evidence_status) LIKE '%source%' AND lower(ds.evidence_status) LIKE '%verif%'
         AND lower(ds.evidence_status) NOT LIKE '%unverif%' AND lower(ds.evidence_status) NOT LIKE '%not%verif%'
         AND (lower(ds.scope) LIKE '%whole%' OR lower(ds.scope) LIKE '%entire%' OR lower(ds.scope) LIKE '%full%'
              OR lower(trim(ds.scope)) IN ('document','doc','all','tdoc')))
""".strip()


def lit(v):
    return "'" + v.replace("'", "''") + "'"


def pack_anchor_ctes(pack):
    return f"""
tpack AS (SELECT cp.id AS pack_id, cp.tsg_number AS tsg_number FROM pkey pq JOIN cr_pack cp ON cp.id = pq.pack_id WHERE pq.k = {lit(pack)}),
anchor AS (SELECT DISTINCT pk.doc_id AS doc_id, tpack.tsg_number AS ptsg FROM pk JOIN tpack ON pk.pack_id = tpack.pack_id
           WHERE pk.doc_id IN (SELECT doc_id FROM ok)),
aclause AS (SELECT DISTINCT cm.doc_id AS doc_id, cm.doc_number AS doc_number, cm.spec AS spec, cm.rel AS rel,
                   cm.clause AS clause, anchor.ptsg AS ptsg
            FROM cm JOIN anchor ON anchor.doc_id = cm.doc_id),
earlier AS (SELECT DISTINCT a.spec AS spec, a.rel AS rel, a.clause AS clause, a.ptsg AS ptsg,
                   q.pack_number AS pack_number, q.tsg_meeting AS tsg_meeting, q.tsg_number AS tsg_number
            FROM (SELECT DISTINCT spec, rel, clause, ptsg FROM aclause) a
            JOIN cm x ON x.spec = a.spec AND x.rel = a.rel AND x.clause = a.clause
            JOIN pk q ON q.doc_id = x.doc_id
            WHERE q.tsg_number < a.ptsg)
""".strip()


def family_a(pack):
    return (
        "WITH " + COMMON + ",\n" + pack_anchor_ctes(pack) + ",\n"
        "latest AS (SELECT spec, rel, clause, ptsg, MAX(tsg_number) AS mx FROM earlier GROUP BY spec, rel, clause, ptsg)\n"
        "SELECT DISTINCT e.spec AS specification, e.clause AS clause, e.pack_number AS cr_pack, e.tsg_meeting AS tsg_meeting\n"
        "FROM earlier e JOIN latest l ON l.spec = e.spec AND l.rel = e.rel AND l.clause = e.clause AND l.ptsg = e.ptsg\n"
        "WHERE e.tsg_number = l.mx"
    )


def family_b(pack):
    return (
        "WITH " + COMMON + ",\n" + pack_anchor_ctes(pack) + "\n"
        "SELECT DISTINCT a.doc_number AS document, a.spec AS specification, a.clause AS clause\n"
        "FROM aclause a\n"
        "WHERE NOT EXISTS (SELECT 1 FROM earlier e WHERE e.spec = a.spec AND e.rel = a.rel AND e.clause = a.clause AND e.ptsg = a.ptsg)"
    )


def family_c(docnum):
    return (
        "WITH " + COMMON + ",\n"
        f"anchor AS (SELECT DISTINCT doc_id FROM dkey WHERE k = {lit(docnum)}),\n"
        "aclause AS (SELECT DISTINCT cm.spec AS spec, cm.rel AS rel, cm.clause AS clause FROM cm WHERE cm.doc_id IN (SELECT doc_id FROM anchor))\n"
        "SELECT DISTINCT a.clause AS clause, x.doc_number AS document, ok.code AS disposition, ok.wg_meeting AS wg_meeting, q.pack_number AS cr_pack\n"
        "FROM aclause a\n"
        "JOIN cm x ON x.spec = a.spec AND x.rel = a.rel AND x.clause = a.clause\n"
        "JOIN ok ON ok.doc_id = x.doc_id\n"
        "JOIN pk q ON q.doc_id = x.doc_id\n"
        f"WHERE x.doc_id NOT IN (SELECT doc_id FROM anchor) AND x.doc_number <> {lit(docnum)}"
    )


def build(item):
    q = item["question"]
    fields = item["fields"]
    m = re.match(r"Change request (R1-\d+) ", q)
    if m:
        assert fields == ["clause", "document", "disposition", "wg_meeting", "cr_pack"], item["id"]
        return family_c(m.group(1))
    m = re.match(r"TSG RAN CR pack (RP-\d+) carries", q)
    assert m, item["id"]
    pack = m.group(1)
    if "latest earlier TSG RAN meeting" in q:
        assert fields == ["specification", "clause", "cr_pack", "tsg_meeting"], item["id"]
        return family_a(pack)
    if "changes first" in q:
        assert fields == ["document", "specification", "clause"], item["id"]
        return family_b(pack)
    raise ValueError(item["id"])


def main():
    with open(PACKET, encoding="utf-8") as fh:
        packet = json.load(fh)
    with open(OUT, "w", encoding="utf-8") as fh:
        for item in packet["items"]:
            fh.write(json.dumps({"id": item["id"], "sql": build(item)}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
