"""Generate one SQLite query per packet item for the RAN5 text-to-SQL packet."""
import json
import re
import sys

PACKET = sys.argv[1]
OUT = sys.argv[2]


def nrel(x):
    """Release label normalized to its number, so 'Rel-18', 'Release 18' and '18' compare equal."""
    return ("REPLACE(REPLACE(REPLACE(REPLACE(LOWER(TRIM(" + x + ")),'release',''),'rel',''),'-',''),' ','')")


def lit(v):
    return "'" + v.replace("'", "''") + "'"


STATUS_OK = ("REPLACE(REPLACE(LOWER(TRIM(x.evidence_status)),'-','_'),' ','_') "
             "IN ('source_verified','sourceverified')")
SCOPE_NORM = "REPLACE(REPLACE(LOWER(TRIM(x.scope)),'-','_'),' ','_')"
SCOPE_OK = ("(" + SCOPE_NORM + " IN ('document','whole_document','whole','full_document',"
            "'entire_document','doc','tdoc','whole_tdoc','full','whole_doc') OR "
            + SCOPE_NORM + " LIKE 'whole%')")
WG_OK = ("UPPER(REPLACE(REPLACE(REPLACE(TRIM(mt.wg),' ',''),'_',''),'-','')) "
         "IN ('RAN5','R5','RANWG5','WG5','TSGRANWG5')")

PRELUDE = (
    "WITH doc AS ("
    "SELECT id AS k, COALESCE(number, id) AS num, " + nrel("target_release") + " AS nrel FROM document "
    "UNION "
    "SELECT number AS k, number AS num, " + nrel("target_release") + " AS nrel FROM document WHERE number IS NOT NULL"
    "), "
    "pk AS ("
    "SELECT id AS k, id AS pid, COALESCE(pack_number, id) AS pnum, tsg_meeting AS tm, tsg_number AS tn FROM cr_pack "
    "UNION "
    "SELECT pack_number AS k, id AS pid, pack_number AS pnum, tsg_meeting AS tm, tsg_number AS tn FROM cr_pack "
    "WHERE pack_number IS NOT NULL"
    "), "
    "memb AS ("
    "SELECT DISTINCT d.num AS num, p.pid AS pid, p.pnum AS pnum, p.tm AS tm, p.tn AS tn "
    "FROM (SELECT cr, pack_id FROM cr_in_pack UNION SELECT cr, pack_id FROM pack_member) l "
    "JOIN doc d ON d.k = l.cr JOIN pk p ON p.k = l.pack_id"
    "), "
    "cs AS ("
    "SELECT DISTINCT d.num AS num, s.spec AS spec, s.clause AS clause, d.nrel AS nrel "
    "FROM (SELECT cr, section_id FROM cr_modifies_section UNION SELECT cr, section_id FROM section_modified_by) l "
    "JOIN doc d ON d.k = l.cr JOIN section s ON s.id = l.section_id "
    "WHERE " + nrel("s.release") + " = d.nrel"
    "), "
    "okd AS ("
    "SELECT DISTINCT d.num AS num, x.code AS code, mt.label AS wgm "
    "FROM disposition x JOIN doc d ON d.k = x.target "
    "JOIN resolution r ON r.id = x.resolution_id JOIN meeting mt ON mt.id = r.meeting_id "
    "WHERE " + STATUS_OK + " AND " + SCOPE_OK + " AND " + WG_OK +
    ")"
)


def tgt_cte(pack):
    return (
        ", tgt AS ("
        "SELECT DISTINCT m.num AS num, m.tn AS ptn, c.spec AS spec, c.clause AS clause, c.nrel AS nrel "
        "FROM memb m JOIN cs c ON c.num = m.num "
        "WHERE m.pid IN (SELECT pid FROM pk WHERE k = " + lit(pack) + ") "
        "AND EXISTS (SELECT 1 FROM okd o WHERE o.num = m.num)"
        ")"
    )


def first_change(pack):
    return (
        PRELUDE + tgt_cte(pack) +
        " SELECT DISTINCT t.num AS document, t.spec AS specification, t.clause AS clause "
        "FROM tgt t WHERE NOT EXISTS ("
        "SELECT 1 FROM cs c2 JOIN memb m2 ON m2.num = c2.num "
        "WHERE c2.spec = t.spec AND c2.clause = t.clause AND c2.nrel = t.nrel AND m2.tn < t.ptn)"
    )


def latest_earlier(pack):
    return (
        PRELUDE + tgt_cte(pack) +
        ", earlier AS ("
        "SELECT DISTINCT t.spec AS spec, t.clause AS clause, t.nrel AS nrel, t.ptn AS ptn, "
        "m2.pnum AS pnum, m2.tm AS tm, m2.tn AS tn "
        "FROM tgt t JOIN cs c2 ON c2.spec = t.spec AND c2.clause = t.clause AND c2.nrel = t.nrel "
        "JOIN memb m2 ON m2.num = c2.num WHERE m2.tn < t.ptn"
        ")"
        " SELECT DISTINCT e.spec AS specification, e.clause AS clause, e.pnum AS cr_pack, e.tm AS tsg_meeting "
        "FROM earlier e WHERE e.tn = ("
        "SELECT MAX(e2.tn) FROM earlier e2 "
        "WHERE e2.spec = e.spec AND e2.clause = e.clause AND e2.nrel = e.nrel AND e2.ptn = e.ptn)"
    )


def same_clause(cr):
    return (
        PRELUDE +
        ", x0 AS (SELECT DISTINCT num FROM doc WHERE k = " + lit(cr) + ")"
        ", xs AS (SELECT DISTINCT c.spec AS spec, c.clause AS clause, c.nrel AS nrel "
        "FROM cs c JOIN x0 ON x0.num = c.num)"
        " SELECT DISTINCT xs.clause AS clause, c2.num AS document, o.code AS disposition, "
        "o.wgm AS wg_meeting, m2.pnum AS cr_pack "
        "FROM xs JOIN cs c2 ON c2.spec = xs.spec AND c2.clause = xs.clause AND c2.nrel = xs.nrel "
        "JOIN okd o ON o.num = c2.num JOIN memb m2 ON m2.num = c2.num "
        "WHERE c2.num NOT IN (SELECT num FROM x0) AND c2.num <> " + lit(cr)
    )


def main():
    packet = json.load(open(PACKET))
    lines = []
    fam_count = {}
    for it in packet["items"]:
        q = it["question"]
        f = it["fields"]
        if "changes first" in q:
            assert f == ["document", "specification", "clause"], it["id"]
            pack = re.search(r"CR pack (RP-\d+)", q).group(1)
            sql, fam = first_change(pack), "first_change"
        elif "latest earlier TSG RAN meeting" in q:
            assert f == ["specification", "clause", "cr_pack", "tsg_meeting"], it["id"]
            pack = re.search(r"CR pack (RP-\d+)", q).group(1)
            sql, fam = latest_earlier(pack), "latest_earlier"
        elif q.startswith("Change request "):
            assert f == ["clause", "document", "disposition", "wg_meeting", "cr_pack"], it["id"]
            cr = re.match(r"Change request (R5-\d+)", q).group(1)
            sql, fam = same_clause(cr), "same_clause"
        else:
            raise SystemExit("unclassified item " + it["id"])
        fam_count[fam] = fam_count.get(fam, 0) + 1
        lines.append(json.dumps({"id": it["id"], "sql": sql}, ensure_ascii=False))
    with open(OUT, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print(len(lines), fam_count)


main()
