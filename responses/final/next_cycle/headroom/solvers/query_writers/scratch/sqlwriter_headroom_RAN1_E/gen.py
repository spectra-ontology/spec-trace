"""Generate one SQLite query per packet item for the RAN1 text-to-SQL packet (run E)."""
import json
import re
import sys

PACKET = sys.argv[1]
OUT = sys.argv[2]


def rel(x):
    """Normalize a release value ('Rel-17', 'Release 17', 'R17', '17') to its number."""
    return (
        "replace(replace(replace(replace(replace(replace(lower(trim(%s)),"
        "'release',''),'rel',''),'-',''),'_',''),' ',''),'r','')" % x
    )


def norm(x):
    return "lower(replace(replace(replace(trim(%s),'-',''),'_',''),' ',''))" % x


def wg(x):
    return "upper(replace(replace(replace(trim(%s),' ',''),'_',''),'-',''))" % x


BASE_CTES = (
    "am AS (SELECT cr, pack_id FROM cr_in_pack UNION SELECT cr, pack_id FROM pack_member), "
    "mods AS (SELECT cr, section_id FROM cr_modifies_section UNION SELECT cr, section_id FROM section_modified_by), "
    "qd AS (SELECT DISTINCT ds.target AS doc_id, ds.code AS code, r.meeting_id AS meeting_id "
    "FROM disposition ds JOIN resolution r ON r.id = ds.resolution_id "
    "JOIN meeting m ON m.id = r.meeting_id "
    "WHERE " + norm("ds.evidence_status") + " IN ('sourceverified','verifiedsource') "
    "AND (" + norm("ds.scope") + " LIKE '%whole%' OR " + norm("ds.scope")
    + " IN ('document','doc','tdoc','full','fulldocument','entire','entiredocument','documentlevel')) "
    "AND " + wg("m.wg") + " IN ('RAN1','RANWG1','R1','WG1','TSGRANWG1'))"
)


def anchor_ctes(pack):
    return (
        "anchor AS (SELECT id, tsg_number FROM cr_pack WHERE pack_number = '%s' OR id = '%s'), " % (pack, pack)
        + "cs AS (SELECT DISTINCT a.tsg_number AS anchor_n, d.number AS doc, s.spec AS spec, s.clause AS clause, "
        + rel("s.release") + " AS rel "
        "FROM anchor a JOIN am ON am.pack_id = a.id "
        "JOIN document d ON d.id = am.cr "
        "JOIN mods ON mods.cr = d.id "
        "JOIN section s ON s.id = mods.section_id "
        "WHERE " + rel("s.release") + " = " + rel("d.target_release") + " "
        "AND d.id IN (SELECT doc_id FROM qd)), "
        "ck AS (SELECT DISTINCT anchor_n, spec, clause, rel FROM cs), "
        "earlier AS (SELECT DISTINCT ck.anchor_n AS anchor_n, ck.spec AS spec, ck.clause AS clause, ck.rel AS rel, "
        "p.pack_number AS pack_number, p.tsg_meeting AS tsg_meeting, p.tsg_number AS tsg_number "
        "FROM ck JOIN section s2 ON s2.spec = ck.spec AND s2.clause = ck.clause "
        "JOIN mods md ON md.section_id = s2.id "
        "JOIN document d2 ON d2.id = md.cr "
        "JOIN am a2 ON a2.cr = d2.id "
        "JOIN cr_pack p ON p.id = a2.pack_id "
        "WHERE " + rel("s2.release") + " = ck.rel AND " + rel("d2.target_release") + " = ck.rel "
        "AND p.tsg_number < ck.anchor_n)"
    )


def q_latest_earlier(pack):
    return (
        "WITH " + BASE_CTES + ", " + anchor_ctes(pack) + " "
        "SELECT DISTINCT e.spec AS specification, e.clause AS clause, e.pack_number AS cr_pack, "
        "e.tsg_meeting AS tsg_meeting FROM earlier e "
        "WHERE e.tsg_number = (SELECT MAX(e2.tsg_number) FROM earlier e2 "
        "WHERE e2.anchor_n = e.anchor_n AND e2.spec = e.spec AND e2.clause = e.clause AND e2.rel = e.rel)"
    )


def q_first_change(pack):
    return (
        "WITH " + BASE_CTES + ", " + anchor_ctes(pack) + " "
        "SELECT DISTINCT cs.doc AS document, cs.spec AS specification, cs.clause AS clause FROM cs "
        "WHERE NOT EXISTS (SELECT 1 FROM earlier e WHERE e.anchor_n = cs.anchor_n "
        "AND e.spec = cs.spec AND e.clause = cs.clause AND e.rel = cs.rel)"
    )


def q_same_clause(doc, relnum):
    return (
        "WITH " + BASE_CTES + ", "
        "x AS (SELECT id FROM document WHERE number = '%s' OR id = '%s'), " % (doc, doc)
        + "xs AS (SELECT DISTINCT s.spec AS spec, s.clause AS clause FROM x "
        "JOIN mods ON mods.cr = x.id JOIN section s ON s.id = mods.section_id "
        "WHERE " + rel("s.release") + " = '%s') " % relnum
        + "SELECT DISTINCT xs.clause AS clause, d2.number AS document, q.code AS disposition, "
        "mt.label AS wg_meeting, p.pack_number AS cr_pack "
        "FROM xs JOIN section s2 ON s2.spec = xs.spec AND s2.clause = xs.clause "
        "JOIN mods md ON md.section_id = s2.id "
        "JOIN document d2 ON d2.id = md.cr "
        "JOIN qd q ON q.doc_id = d2.id "
        "JOIN meeting mt ON mt.id = q.meeting_id "
        "JOIN am a2 ON a2.cr = d2.id "
        "JOIN cr_pack p ON p.id = a2.pack_id "
        "WHERE " + rel("s2.release") + " = '%s' AND " % relnum
        + rel("d2.target_release") + " = '%s' " % relnum
        + "AND d2.id NOT IN (SELECT id FROM x) AND COALESCE(d2.number, '') <> '%s'" % doc
    )


FIELDS_A = ["specification", "clause", "cr_pack", "tsg_meeting"]
FIELDS_B = ["document", "specification", "clause"]
FIELDS_C = ["clause", "document", "disposition", "wg_meeting", "cr_pack"]

packet = json.load(open(PACKET))
lines = []
for it in packet["items"]:
    q = it["question"]
    f = it["fields"]
    if "latest earlier TSG RAN meeting" in q:
        assert f == FIELDS_A, it["id"]
        pack = re.search(r"CR pack (RP-\d+) carries", q).group(1)
        sql = q_latest_earlier(pack)
    elif "changes first" in q:
        assert f == FIELDS_B, it["id"]
        pack = re.search(r"CR pack (RP-\d+) carries", q).group(1)
        sql = q_first_change(pack)
    elif q.startswith("Change request "):
        assert f == FIELDS_C, it["id"]
        m = re.match(r"Change request (R1-\d+) \(CR \d+ to TS [\d.]+\) targets Rel-(\d+)\.", q)
        doc, relnum = m.group(1), m.group(2)
        assert ("other than %s" % doc) in q and ("in Rel-%s" % relnum) in q, it["id"]
        sql = q_same_clause(doc, relnum)
    else:
        raise SystemExit("unknown family: " + it["id"])
    lines.append(json.dumps({"id": it["id"], "sql": sql}, ensure_ascii=False))

with open(OUT, "w") as fh:
    fh.write("\n".join(lines) + "\n")
print(len(lines))
