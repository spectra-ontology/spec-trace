"""Generate one SQLite query per packet item for the RAN1 text-to-SQL packet."""
import json
import re
import sys

PACKET = sys.argv[1]
OUT = sys.argv[2]


def q(s):
    return "'" + s.replace("'", "''") + "'"


def nrel(expr):
    # 'Rel-17', 'Release 17', 'rel_17', 'R17', '17' -> '17'
    return ("replace(replace(replace(replace(replace(replace(lower(" + expr +
            "),'release',''),'rel',''),'r',''),'-',''),'_',''),' ','')")


def rel_literal(r):
    return re.sub(r"[^0-9]", "", r)


VERIFIED = ("lower(replace(replace(trim(di.evidence_status),'_','-'),' ','-')) = 'source-verified'")
WHOLE = ("(lower(replace(replace(trim(di.scope),'_',' '),'-',' ')) IN "
         "('whole document','document','whole','full document','full','entire document','doc','whole doc')"
         " OR lower(trim(di.scope)) LIKE 'whole%')")
RAN1 = ("upper(replace(replace(replace(trim(mt.wg),' ',''),'_',''),'-','')) IN "
        "('RAN1','R1','RANWG1','WG1','TSGRANWG1')")

BASE = (
    "dk AS (SELECT id AS doc_id, id AS k FROM document "
    "UNION SELECT id, number FROM document WHERE number IS NOT NULL), "
    "pkk AS (SELECT id AS pid, id AS k FROM cr_pack "
    "UNION SELECT id, pack_number FROM cr_pack WHERE pack_number IS NOT NULL), "
    "mem AS (SELECT DISTINCT dk.doc_id AS doc_id, pkk.pid AS pid FROM "
    "(SELECT cr, pack_id FROM cr_in_pack UNION SELECT cr, pack_id FROM pack_member) e "
    "JOIN dk ON dk.k = e.cr JOIN pkk ON pkk.k = e.pack_id), "
    "crsec AS (SELECT DISTINCT dk.doc_id AS doc_id, s.spec AS spec, s.clause AS clause, "
    + nrel("s.release") + " AS rel FROM "
    "(SELECT cr, section_id FROM cr_modifies_section UNION SELECT cr, section_id FROM section_modified_by) e "
    "JOIN dk ON dk.k = e.cr JOIN document d ON d.id = dk.doc_id JOIN section s ON s.id = e.section_id "
    "WHERE " + nrel("s.release") + " = " + nrel("d.target_release") + "), "
    "vdoc AS (SELECT DISTINCT dk.doc_id AS doc_id, di.code AS code, COALESCE(mt.label, mt.id) AS wg_meeting "
    "FROM disposition di JOIN dk ON dk.k = di.target JOIN resolution r ON r.id = di.resolution_id "
    "JOIN meeting mt ON mt.id = r.meeting_id WHERE " + VERIFIED + " AND " + WHOLE + " AND " + RAN1 + ")"
)


def target_pack_ctes(pack, rels):
    rel_in = ", ".join(q(rel_literal(r)) for r in rels)
    return (
        "tp AS (SELECT id AS pid, tsg_number FROM cr_pack WHERE pack_number = " + q(pack) +
        " OR id = " + q(pack) + "), "
        "tc AS (SELECT DISTINCT tp.tsg_number AS tnum, COALESCE(d.number, d.id) AS document, "
        "cs.spec AS spec, cs.clause AS clause, cs.rel AS rel FROM tp "
        "JOIN mem ON mem.pid = tp.pid JOIN crsec cs ON cs.doc_id = mem.doc_id "
        "JOIN document d ON d.id = cs.doc_id "
        "WHERE cs.doc_id IN (SELECT doc_id FROM vdoc) AND cs.rel IN (" + rel_in + "))"
    )


def sql_latest_earlier(pack, rels):
    return (
        "WITH " + BASE + ", " + target_pack_ctes(pack, rels) + ", "
        "tcl AS (SELECT DISTINCT tnum, spec, clause, rel FROM tc), "
        "earlier AS (SELECT DISTINCT tcl.tnum AS tnum, tcl.spec AS spec, tcl.clause AS clause, tcl.rel AS rel, "
        "pk.pack_number AS pack_number, pk.tsg_meeting AS tsg_meeting, pk.tsg_number AS tsg_number "
        "FROM tcl JOIN crsec o ON o.spec = tcl.spec AND o.clause = tcl.clause AND o.rel = tcl.rel "
        "JOIN mem ON mem.doc_id = o.doc_id JOIN cr_pack pk ON pk.id = mem.pid "
        "WHERE pk.tsg_number < tcl.tnum), "
        "latest AS (SELECT tnum, spec, clause, rel, MAX(tsg_number) AS mx FROM earlier "
        "GROUP BY tnum, spec, clause, rel) "
        "SELECT DISTINCT e.spec AS specification, e.clause AS clause, e.pack_number AS cr_pack, "
        "e.tsg_meeting AS tsg_meeting FROM earlier e JOIN latest l ON l.tnum = e.tnum AND l.spec = e.spec "
        "AND l.clause = e.clause AND l.rel = e.rel AND e.tsg_number = l.mx"
    )


def sql_first_change(pack, rels):
    return (
        "WITH " + BASE + ", " + target_pack_ctes(pack, rels) + " "
        "SELECT DISTINCT tc.document AS document, tc.spec AS specification, tc.clause AS clause FROM tc "
        "WHERE NOT EXISTS (SELECT 1 FROM crsec o JOIN mem ON mem.doc_id = o.doc_id "
        "JOIN cr_pack pk ON pk.id = mem.pid WHERE o.spec = tc.spec AND o.clause = tc.clause "
        "AND o.rel = tc.rel AND pk.tsg_number < tc.tnum)"
    )


def sql_same_clause(docnum, rel):
    r = q(rel_literal(rel))
    return (
        "WITH " + BASE + ", "
        "x AS (SELECT id AS doc_id FROM document WHERE number = " + q(docnum) + " OR id = " + q(docnum) + "), "
        "xc AS (SELECT DISTINCT s.spec AS spec, s.clause AS clause FROM "
        "(SELECT cr, section_id FROM cr_modifies_section UNION SELECT cr, section_id FROM section_modified_by) e "
        "JOIN dk ON dk.k = e.cr JOIN section s ON s.id = e.section_id "
        "WHERE dk.doc_id IN (SELECT doc_id FROM x) AND " + nrel("s.release") + " = " + r + ") "
        "SELECT DISTINCT xc.clause AS clause, COALESCE(d.number, d.id) AS document, v.code AS disposition, "
        "v.wg_meeting AS wg_meeting, pk.pack_number AS cr_pack FROM xc "
        "JOIN crsec o ON o.spec = xc.spec AND o.clause = xc.clause AND o.rel = " + r + " "
        "JOIN document d ON d.id = o.doc_id JOIN vdoc v ON v.doc_id = o.doc_id "
        "JOIN mem ON mem.doc_id = o.doc_id JOIN cr_pack pk ON pk.id = mem.pid "
        "WHERE o.doc_id NOT IN (SELECT doc_id FROM x) AND COALESCE(d.number, '') <> " + q(docnum)
    )


FAM_A = ["specification", "clause", "cr_pack", "tsg_meeting"]
FAM_B = ["document", "specification", "clause"]
FAM_C = ["clause", "document", "disposition", "wg_meeting", "cr_pack"]

with open(PACKET, encoding="utf-8") as f:
    packet = json.load(f)

lines = []
for it in packet["items"]:
    qs = it["question"]
    fields = it["fields"]
    if fields == FAM_C:
        docnum = re.search(r"Change request (R1-\d+)", qs).group(1)
        rel = re.search(r"targets (Rel-\d+)", qs).group(1)
        sql = sql_same_clause(docnum, rel)
    else:
        pack = re.search(r"CR pack (RP-\d+)", qs).group(1)
        rel_text = re.search(r"targets \(([^)]*)\)", qs).group(1)
        rels = re.findall(r"Rel-\d+", rel_text)
        assert rels, it["id"]
        if fields == FAM_A and "latest earlier" in qs:
            sql = sql_latest_earlier(pack, rels)
        elif fields == FAM_B and "changes first" in qs:
            sql = sql_first_change(pack, rels)
        else:
            raise SystemExit("unknown family: " + it["id"])
    lines.append(json.dumps({"id": it["id"], "sql": sql}, ensure_ascii=False))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print(len(lines))
