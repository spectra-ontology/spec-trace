"""Generate SQLite queries for the RAN2 text-to-SQL packet (run C)."""
import json
import re
import sys

PACKET = sys.argv[1]
OUT = sys.argv[2]


def q(s):
    return "'" + s.replace("'", "''") + "'"


def rel(expr):
    """Normalize a release string such as 'Rel-16', 'Release 16', '16.3.0' to '16'."""
    x = (
        "replace(replace(replace(replace(replace(replace(lower(trim(" + expr + ")),"
        "'release',''),'rel',''),'r',''),'-',''),' ',''),'_','')"
    )
    return "(CASE WHEN instr(" + x + ",'.')>0 THEN substr(" + x + ",1,instr(" + x + ",'.')-1) ELSE " + x + " END)"


def squash(expr):
    return "lower(replace(replace(replace(trim(" + expr + "),'_',''),' ',''),'-',''))"


EVS = squash("dp.evidence_status") + " IN ('sourceverified','verifiedsource')"
SCOPE = squash("dp.scope") + (
    " IN ('wholedocument','document','whole','fulldocument','entiredocument',"
    "'doc','wholedoc','tdoc','wholetdoc','full')"
)
WGN = "upper(replace(replace(replace(trim(COALESCE(mm.wg,'')),' ',''),'_',''),'-',''))"
WG = (
    "(" + WGN + " IN ('RAN2','R2','RANWG2','TSGRANWG2','WG2','TSGR2','RWG2') OR "
    + WGN + " LIKE 'RAN2%')"
)

COMMON = [
    "docs AS (SELECT id, COALESCE(number, id) AS num, " + rel("target_release") + " AS rel FROM document)",
    "docmap AS (SELECT id AS doc_id, id AS k FROM document "
    "UNION SELECT id AS doc_id, number AS k FROM document WHERE number IS NOT NULL)",
    "packmap AS (SELECT id AS pack_id, id AS k FROM cr_pack "
    "UNION SELECT id AS pack_id, pack_number AS k FROM cr_pack WHERE pack_number IS NOT NULL)",
    "meetmap AS (SELECT id AS k, COALESCE(label, id) AS label, wg FROM meeting "
    "UNION SELECT label AS k, COALESCE(label, id) AS label, wg FROM meeting WHERE label IS NOT NULL)",
    "sec AS (SELECT id, spec, clause, " + rel('"release"') + " AS rel FROM section)",
    "modraw AS (SELECT cr, section_id FROM cr_modifies_section "
    "UNION SELECT cr, section_id FROM section_modified_by)",
    "mods AS (SELECT DISTINCT dm.doc_id AS doc_id, mr.section_id AS section_id "
    "FROM modraw mr JOIN docmap dm ON dm.k = mr.cr)",
    "packraw AS (SELECT cr, pack_id FROM cr_in_pack UNION SELECT cr, pack_id FROM pack_member)",
    "inpack AS (SELECT DISTINCT dm.doc_id AS doc_id, pm.pack_id AS pack_id "
    "FROM packraw pr JOIN docmap dm ON dm.k = pr.cr JOIN packmap pm ON pm.k = pr.pack_id)",
    "okdisp AS (SELECT DISTINCT dm.doc_id AS doc_id, dp.code AS code, mm.label AS wg_meeting "
    "FROM disposition dp JOIN docmap dm ON dm.k = dp.target "
    "JOIN resolution r ON r.id = dp.resolution_id "
    "JOIN meetmap mm ON mm.k = r.meeting_id "
    "WHERE " + EVS + " AND " + SCOPE + " AND " + WG + ")",
]


def with_clause(extra):
    return "WITH " + ",\n".join(COMMON + extra) + "\n"


def fam_cr(number, relnum):
    extra = [
        "anchor AS (SELECT id FROM document WHERE number = " + q(number) + " OR id = " + q(number) + ")",
        "acl AS (SELECT DISTINCT s.spec, s.rel, s.clause FROM anchor a "
        "JOIN mods mo ON mo.doc_id = a.id JOIN sec s ON s.id = mo.section_id "
        "WHERE s.rel = " + q(relnum) + ")",
    ]
    body = (
        "SELECT DISTINCT s2.clause AS clause, d.num AS document, od.code AS disposition, "
        "od.wg_meeting AS wg_meeting, COALESCE(cp.pack_number, cp.id) AS cr_pack\n"
        "FROM acl JOIN sec s2 ON s2.spec = acl.spec AND s2.rel = acl.rel AND s2.clause = acl.clause\n"
        "JOIN mods mo ON mo.section_id = s2.id\n"
        "JOIN docs d ON d.id = mo.doc_id\n"
        "JOIN okdisp od ON od.doc_id = d.id\n"
        "JOIN inpack ip ON ip.doc_id = d.id\n"
        "JOIN cr_pack cp ON cp.id = ip.pack_id\n"
        "WHERE d.rel = " + q(relnum) + " AND d.id NOT IN (SELECT id FROM anchor)"
    )
    return with_clause(extra) + body


def pack_ctes(pack, rels):
    rel_list = "(" + ",".join(q(r) for r in rels) + ")"
    return [
        "P AS (SELECT id, tsg_number FROM cr_pack WHERE pack_number = " + q(pack) + " OR id = " + q(pack) + ")",
        "pcr AS (SELECT DISTINCT d.id AS doc_id, d.num AS num, d.rel AS rel, P.tsg_number AS ptsg "
        "FROM P JOIN inpack ip ON ip.pack_id = P.id JOIN docs d ON d.id = ip.doc_id "
        "WHERE d.id IN (SELECT doc_id FROM okdisp) AND d.rel IN " + rel_list + ")",
        "pcl AS (SELECT DISTINCT pc.num AS document, s.spec AS spec, s.rel AS rel, s.clause AS clause, "
        "pc.ptsg AS ptsg FROM pcr pc JOIN mods mo ON mo.doc_id = pc.doc_id "
        "JOIN sec s ON s.id = mo.section_id WHERE s.rel = pc.rel)",
    ]


def fam_first(pack, rels):
    body = (
        "SELECT DISTINCT pc.document AS document, pc.spec AS specification, pc.clause AS clause\n"
        "FROM pcl pc\n"
        "WHERE NOT EXISTS (SELECT 1 FROM sec s2 JOIN mods mo ON mo.section_id = s2.id "
        "JOIN docs d2 ON d2.id = mo.doc_id JOIN inpack ip ON ip.doc_id = d2.id "
        "JOIN cr_pack cp ON cp.id = ip.pack_id "
        "WHERE s2.spec = pc.spec AND s2.rel = pc.rel AND s2.clause = pc.clause "
        "AND d2.rel = pc.rel AND cp.tsg_number < pc.ptsg)"
    )
    return with_clause(pack_ctes(pack, rels)) + body


def fam_latest(pack, rels):
    extra = pack_ctes(pack, rels) + [
        "cand AS (SELECT DISTINCT pc.spec AS spec, pc.rel AS rel, pc.clause AS clause, pc.ptsg AS ptsg, "
        "cp.id AS pack_id, cp.tsg_number AS tsg "
        "FROM (SELECT DISTINCT spec, rel, clause, ptsg FROM pcl) pc "
        "JOIN sec s2 ON s2.spec = pc.spec AND s2.rel = pc.rel AND s2.clause = pc.clause "
        "JOIN mods mo ON mo.section_id = s2.id "
        "JOIN docs d2 ON d2.id = mo.doc_id AND d2.rel = pc.rel "
        "JOIN inpack ip ON ip.doc_id = d2.id "
        "JOIN cr_pack cp ON cp.id = ip.pack_id "
        "WHERE cp.tsg_number < pc.ptsg)",
        "best AS (SELECT spec, rel, clause, ptsg, MAX(tsg) AS mx FROM cand GROUP BY spec, rel, clause, ptsg)",
    ]
    body = (
        "SELECT DISTINCT c.spec AS specification, c.clause AS clause, "
        "COALESCE(cp.pack_number, cp.id) AS cr_pack, cp.tsg_meeting AS tsg_meeting\n"
        "FROM cand c JOIN best b ON b.spec = c.spec AND b.rel = c.rel AND b.clause = c.clause "
        "AND b.ptsg = c.ptsg AND c.tsg = b.mx\n"
        "JOIN cr_pack cp ON cp.id = c.pack_id"
    )
    return with_clause(extra) + body


FAM_CR = re.compile(r"^Change request (\S+) \(CR \S+ to TS \S+\) targets Rel-(\d+)\.")
FAM_PACK = re.compile(r"^TSG RAN CR pack (\S+) carries change requests from RAN2\.")
REL_LIST = re.compile(r"the release that change request targets \(([^)]*)\)")

FIELDS = {
    "cr": ["clause", "document", "disposition", "wg_meeting", "cr_pack"],
    "first": ["document", "specification", "clause"],
    "latest": ["specification", "clause", "cr_pack", "tsg_meeting"],
}


def main():
    with open(PACKET) as f:
        pkt = json.load(f)
    lines = []
    for it in pkt["items"]:
        qs = it["question"]
        m = FAM_CR.match(qs)
        if m:
            fam = "cr"
            sql = fam_cr(m.group(1), m.group(2))
        else:
            m = FAM_PACK.match(qs)
            if not m:
                raise SystemExit("unrecognized question: " + it["id"])
            rm = REL_LIST.search(qs)
            if not rm:
                raise SystemExit("no release list: " + it["id"])
            rels = re.findall(r"Rel-(\d+)", rm.group(1))
            if not rels:
                raise SystemExit("empty release list: " + it["id"])
            if "changes first" in qs:
                fam = "first"
                sql = fam_first(m.group(1), rels)
            elif "latest earlier TSG RAN meeting" in qs:
                fam = "latest"
                sql = fam_latest(m.group(1), rels)
            else:
                raise SystemExit("unrecognized pack family: " + it["id"])
        if it["fields"] != FIELDS[fam]:
            raise SystemExit("field mismatch for " + it["id"] + ": " + repr(it["fields"]))
        lines.append(json.dumps({"id": it["id"], "sql": sql}, ensure_ascii=False))
    with open(OUT, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(len(lines))


if __name__ == "__main__":
    main()
