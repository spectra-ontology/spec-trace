"""Generate one SQLite query per packet item for the RAN1 text-to-SQL packet."""
import json
import re
import sys

PACKET = sys.argv[1]
OUT = sys.argv[2]


def norm_rel(x):
    """Reduce a release string such as 'Rel-17', 'Release 17' or 'R17' to '17'."""
    return (
        "REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(UPPER(TRIM(" + x + ")),"
        "'RELEASE',''),'REL',''),'R',''),'-',''),' ','')"
    )


def lit(s):
    return "'" + s.replace("'", "''") + "'"


# Mirror relation tables are unioned so that a link recorded in either direction counts.
CTE_LINKS = (
    "cip AS (SELECT cr, pack_id FROM cr_in_pack UNION SELECT cr, pack_id FROM pack_member), "
    "cms AS (SELECT cr, section_id FROM cr_modifies_section UNION SELECT cr, section_id FROM section_modified_by)"
)

WG_RAN1 = (
    "UPPER(REPLACE(REPLACE(REPLACE(TRIM(m.wg),' ',''),'_',''),'-','')) "
    "IN ('RAN1','R1','RANWG1','TSGRANWG1','TSGR1','RANWG01')"
)
SRC_VERIFIED = (
    "(LOWER(d.evidence_status) LIKE '%source%verif%' "
    "OR REPLACE(REPLACE(LOWER(TRIM(d.evidence_status)),'-','_'),' ','_') IN ('verified','verified_source','source_verified')) "
    "AND LOWER(d.evidence_status) NOT LIKE '%unverif%' "
    "AND LOWER(d.evidence_status) NOT LIKE '%not%verif%'"
)
WHOLE_DOC = (
    "(LOWER(d.scope) LIKE '%whole%' OR LOWER(d.scope) LIKE '%entire%' OR LOWER(d.scope) LIKE '%full%' "
    "OR REPLACE(REPLACE(LOWER(TRIM(d.scope)),'-','_'),' ','_') IN ('document','doc','tdoc','whole_document','all')) "
    "AND LOWER(d.scope) NOT LIKE '%part%' AND LOWER(d.scope) NOT LIKE '%not%'"
)

CTE_OKD = (
    "okd AS (SELECT DISTINCT d.target AS doc_id, d.code AS code, m.label AS wg_label "
    "FROM disposition d JOIN resolution r ON r.id = d.resolution_id "
    "JOIN meeting m ON m.id = r.meeting_id "
    "WHERE " + WG_RAN1 + " AND " + SRC_VERIFIED + " AND " + WHOLE_DOC + ")"
)


def pack_base(pack):
    """Qualifying (CR, clause) pairs of the pack: CR has a source-verified RAN1
    whole-document disposition and the clause is in the release the CR targets."""
    return (
        "p AS (SELECT id, tsg_number FROM cr_pack WHERE pack_number = " + lit(pack) + " OR id = " + lit(pack) + "), "
        "base AS (SELECT DISTINCT c.id AS doc_id, c.number AS doc_number, s.spec AS spec, s.clause AS clause, "
        "s.release AS rel, p.tsg_number AS p_num "
        "FROM p JOIN cip ON cip.pack_id = p.id "
        "JOIN document c ON c.id = cip.cr "
        "JOIN cms ON cms.cr = c.id "
        "JOIN section s ON s.id = cms.section_id "
        "WHERE " + norm_rel("s.release") + " = " + norm_rel("c.target_release") + " "
        "AND EXISTS (SELECT 1 FROM okd o WHERE o.doc_id = c.id))"
    )


def q_latest_earlier(pack):
    return (
        "WITH " + CTE_LINKS + ", " + CTE_OKD + ", " + pack_base(pack) + ", "
        "earlier AS (SELECT DISTINCT b.spec AS spec, b.clause AS clause, b.rel AS rel, "
        "cp2.pack_number AS pack_number, cp2.tsg_meeting AS tsg_meeting, cp2.tsg_number AS tsg_number "
        "FROM base b "
        "JOIN section s2 ON s2.spec = b.spec AND s2.clause = b.clause "
        "AND " + norm_rel("s2.release") + " = " + norm_rel("b.rel") + " "
        "JOIN cms m2 ON m2.section_id = s2.id "
        "JOIN document c2 ON c2.id = m2.cr "
        "JOIN cip i2 ON i2.cr = c2.id "
        "JOIN cr_pack cp2 ON cp2.id = i2.pack_id "
        "WHERE " + norm_rel("c2.target_release") + " = " + norm_rel("b.rel") + " "
        "AND cp2.tsg_number < b.p_num), "
        "latest AS (SELECT spec, clause, rel, MAX(tsg_number) AS mx FROM earlier GROUP BY spec, clause, rel) "
        "SELECT DISTINCT e.spec AS specification, e.clause AS clause, e.pack_number AS cr_pack, "
        "e.tsg_meeting AS tsg_meeting "
        "FROM earlier e JOIN latest l ON l.spec = e.spec AND l.clause = e.clause AND l.rel = e.rel "
        "AND e.tsg_number = l.mx"
    )


def q_first_change(pack):
    return (
        "WITH " + CTE_LINKS + ", " + CTE_OKD + ", " + pack_base(pack) + " "
        "SELECT DISTINCT b.doc_number AS document, b.spec AS specification, b.clause AS clause "
        "FROM base b "
        "WHERE NOT EXISTS (SELECT 1 FROM section s2 "
        "JOIN cms m2 ON m2.section_id = s2.id "
        "JOIN document c2 ON c2.id = m2.cr "
        "JOIN cip i2 ON i2.cr = c2.id "
        "JOIN cr_pack cp2 ON cp2.id = i2.pack_id "
        "WHERE s2.spec = b.spec AND s2.clause = b.clause "
        "AND " + norm_rel("s2.release") + " = " + norm_rel("b.rel") + " "
        "AND " + norm_rel("c2.target_release") + " = " + norm_rel("b.rel") + " "
        "AND cp2.tsg_number < b.p_num)"
    )


def q_same_clause(doc):
    return (
        "WITH " + CTE_LINKS + ", " + CTE_OKD + ", "
        "x AS (SELECT id, number, target_release FROM document WHERE number = " + lit(doc) + " OR id = " + lit(doc) + "), "
        "xs AS (SELECT DISTINCT s.spec AS spec, s.clause AS clause, s.release AS rel, x.target_release AS xrel "
        "FROM x JOIN cms ON cms.cr = x.id JOIN section s ON s.id = cms.section_id "
        "WHERE " + norm_rel("s.release") + " = " + norm_rel("x.target_release") + ") "
        "SELECT DISTINCT xs.clause AS clause, c2.number AS document, o.code AS disposition, "
        "o.wg_label AS wg_meeting, cp.pack_number AS cr_pack "
        "FROM xs "
        "JOIN section s2 ON s2.spec = xs.spec AND s2.clause = xs.clause "
        "AND " + norm_rel("s2.release") + " = " + norm_rel("xs.rel") + " "
        "JOIN cms m2 ON m2.section_id = s2.id "
        "JOIN document c2 ON c2.id = m2.cr "
        "JOIN okd o ON o.doc_id = c2.id "
        "JOIN cip i2 ON i2.cr = c2.id "
        "JOIN cr_pack cp ON cp.id = i2.pack_id "
        "WHERE " + norm_rel("c2.target_release") + " = " + norm_rel("xs.xrel") + " "
        "AND c2.id NOT IN (SELECT id FROM x) "
        "AND (c2.number IS NULL OR c2.number <> " + lit(doc) + ")"
    )


def main():
    with open(PACKET) as f:
        packet = json.load(f)
    lines = []
    for it in packet["items"]:
        q = it["question"]
        fields = it["fields"]
        if "give every CR pack of the latest earlier TSG RAN meeting" in q:
            assert fields == ["specification", "clause", "cr_pack", "tsg_meeting"], it["id"]
            pack = re.search(r"TSG RAN CR pack (RP-\d+) carries", q).group(1)
            sql = q_latest_earlier(pack)
        elif "Keep the clauses that the pack changes first" in q:
            assert fields == ["document", "specification", "clause"], it["id"]
            pack = re.search(r"TSG RAN CR pack (RP-\d+) carries", q).group(1)
            sql = q_first_change(pack)
        elif re.match(r"Change request R1-\d+ \(CR \d+ to TS [\d.]+\) targets Rel-\d+\.", q):
            assert fields == ["clause", "document", "disposition", "wg_meeting", "cr_pack"], it["id"]
            doc = re.match(r"Change request (R1-\d+) ", q).group(1)
            assert ("other than " + doc) in q, it["id"]
            sql = q_same_clause(doc)
        else:
            raise SystemExit("unrecognized item " + it["id"])
        lines.append(json.dumps({"id": it["id"], "sql": sql}, ensure_ascii=False))
    with open(OUT, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(len(lines))


if __name__ == "__main__":
    main()
