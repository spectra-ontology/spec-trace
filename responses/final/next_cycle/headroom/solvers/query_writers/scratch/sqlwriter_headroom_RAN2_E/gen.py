"""Generate one SQLite query per packet item for the RAN2 text-to-SQL packet."""
import json
import re
import sys

PACKET = sys.argv[1]
OUT = sys.argv[2]


def q(s):
    return "'" + s.replace("'", "''") + "'"


def reln(x):
    """Release normalisation: 'Rel-16', 'REL16', 'R16', '16.3.0' all map to '16'."""
    t = (
        "replace(replace(replace(replace(replace(replace(upper(trim(" + x + ")),"
        "'RELEASE',''),'REL',''),'-',''),'_',''),' ',''),'R','')"
    )
    return "(CASE WHEN instr(" + t + ",'.') > 0 THEN substr(" + t + ",1,instr(" + t + ",'.')-1) ELSE " + t + " END)"


def reln_lit(v):
    t = v.strip().upper()
    for a in ("RELEASE", "REL", "-", "_", " ", "R"):
        t = t.replace(a, "")
    if "." in t:
        t = t[: t.index(".")]
    return q(t)


def norm(x):
    return "replace(replace(replace(lower(trim(" + x + ")),'-',''),'_',''),' ','')"


VERIFIED = (
    norm("x.evidence_status")
    + " IN ('sourceverified','verified','verifiedsource','verifiedfromsource','verifiedagainstsource')"
)
WHOLE = (
    norm("x.scope")
    + " IN ('wholedocument','document','whole','entiredocument','entire','fulldocument','full',"
    "'all','alldocument','doc','wholedoc','fulldoc','tdoc','wholetdoc')"
)
RAN2 = (
    "(" + norm("mt.wg") + " IN ('ran2','r2','ranwg2','wg2','tsgranwg2','tsgr2')"
    " OR " + norm("mt.wg") + " LIKE '%ran2%' OR " + norm("mt.wg") + " LIKE '%ranwg2%')"
)

COMMON = (
    "dkey AS ("
    "SELECT id AS k, id AS doc_id FROM document "
    "UNION SELECT number AS k, id AS doc_id FROM document WHERE number IS NOT NULL), "
    "docn AS (SELECT id AS doc_id, COALESCE(number, id) AS doc_number, " + reln("target_release") + " AS doc_rel "
    "FROM document), "
    "mods AS ("
    "SELECT cr, section_id FROM cr_modifies_section "
    "UNION SELECT cr, section_id FROM section_modified_by), "
    "crmod AS ("
    "SELECT DISTINCT dk.doc_id AS doc_id, dn.doc_number AS doc_number, dn.doc_rel AS doc_rel, "
    "s.spec AS spec, s.clause AS clause, " + reln("s.release") + " AS sec_rel "
    "FROM mods m JOIN dkey dk ON dk.k = m.cr JOIN docn dn ON dn.doc_id = dk.doc_id "
    "JOIN section s ON s.id = m.section_id), "
    "mems AS ("
    "SELECT cr, pack_id FROM cr_in_pack "
    "UNION SELECT cr, pack_id FROM pack_member), "
    "pkey AS ("
    "SELECT id AS k, id AS pid FROM cr_pack "
    "UNION SELECT pack_number AS k, id AS pid FROM cr_pack WHERE pack_number IS NOT NULL), "
    "crpack AS ("
    "SELECT DISTINCT dk.doc_id AS doc_id, p.id AS pack_id, p.pack_number AS pack_number, "
    "p.tsg_meeting AS tsg_meeting, p.tsg_number AS tsg_number "
    "FROM mems y JOIN dkey dk ON dk.k = y.cr JOIN pkey pky ON pky.k = y.pack_id JOIN cr_pack p ON p.id = pky.pid), "
    "vdisp AS ("
    "SELECT DISTINCT dk.doc_id AS doc_id, x.code AS code, mt.label AS label "
    "FROM disposition x JOIN dkey dk ON dk.k = x.target "
    "JOIN resolution r ON r.id = x.resolution_id JOIN meeting mt ON mt.id = r.meeting_id "
    "WHERE " + VERIFIED + " AND " + WHOLE + " AND " + RAN2 + ")"
)


def family_a(doc, rel):
    r = reln_lit(rel)
    return (
        "WITH " + COMMON + ", "
        "xdoc AS (SELECT doc_id FROM dkey WHERE k = " + q(doc) + "), "
        "xcl AS ("
        "SELECT DISTINCT cm.spec AS spec, cm.clause AS clause, cm.sec_rel AS sec_rel "
        "FROM crmod cm WHERE cm.doc_id IN (SELECT doc_id FROM xdoc) AND cm.sec_rel = " + r + ") "
        "SELECT DISTINCT c.clause AS clause, o.doc_number AS document, v.code AS disposition, "
        "v.label AS wg_meeting, cp.pack_number AS cr_pack "
        "FROM xcl c "
        "JOIN crmod o ON o.spec = c.spec AND o.clause = c.clause AND o.sec_rel = c.sec_rel "
        "JOIN vdisp v ON v.doc_id = o.doc_id "
        "JOIN crpack cp ON cp.doc_id = o.doc_id "
        "WHERE o.doc_id NOT IN (SELECT doc_id FROM xdoc) "
        "AND o.doc_rel = " + r
    )


def pack_ctes(pack, rels):
    rel_list = ", ".join(reln_lit(x) for x in rels)
    return (
        "WITH " + COMMON + ", "
        "pk AS (SELECT p.id AS pid, p.tsg_number AS tsg_number FROM cr_pack p "
        "WHERE p.pack_number = " + q(pack) + " OR p.id = " + q(pack) + "), "
        "pnum AS (SELECT MIN(tsg_number) AS n FROM pk), "
        "pcr AS (SELECT DISTINCT cp.doc_id AS doc_id FROM crpack cp "
        "WHERE cp.pack_id IN (SELECT pid FROM pk) AND cp.doc_id IN (SELECT doc_id FROM vdisp)), "
        "pcl AS ("
        "SELECT DISTINCT cm.doc_number AS document, cm.spec AS spec, cm.clause AS clause, "
        "cm.sec_rel AS sec_rel "
        "FROM pcr JOIN crmod cm ON cm.doc_id = pcr.doc_id "
        "WHERE cm.sec_rel = cm.doc_rel AND cm.sec_rel IN (" + rel_list + "))"
    )


def family_b(pack, rels):
    return (
        pack_ctes(pack, rels) + " "
        "SELECT DISTINCT c.document AS document, c.spec AS specification, c.clause AS clause "
        "FROM pcl c "
        "WHERE NOT EXISTS ("
        "SELECT 1 FROM crmod o "
        "JOIN crpack op ON op.doc_id = o.doc_id "
        "WHERE o.spec = c.spec AND o.clause = c.clause AND o.sec_rel = c.sec_rel "
        "AND o.doc_rel = c.sec_rel "
        "AND op.tsg_number < (SELECT n FROM pnum))"
    )


def family_c(pack, rels):
    return (
        pack_ctes(pack, rels) + ", "
        "earlier AS ("
        "SELECT DISTINCT c.spec AS spec, c.clause AS clause, c.sec_rel AS sec_rel, "
        "op.pack_number AS pack_number, op.tsg_meeting AS tsg_meeting, op.tsg_number AS tsg_number "
        "FROM (SELECT DISTINCT spec, clause, sec_rel FROM pcl) c "
        "JOIN crmod o ON o.spec = c.spec AND o.clause = c.clause AND o.sec_rel = c.sec_rel "
        "JOIN crpack op ON op.doc_id = o.doc_id "
        "WHERE o.doc_rel = c.sec_rel "
        "AND op.tsg_number < (SELECT n FROM pnum)), "
        "latest AS (SELECT spec, clause, sec_rel, MAX(tsg_number) AS mx FROM earlier "
        "GROUP BY spec, clause, sec_rel) "
        "SELECT DISTINCT e.spec AS specification, e.clause AS clause, e.pack_number AS cr_pack, "
        "e.tsg_meeting AS tsg_meeting "
        "FROM earlier e JOIN latest l ON l.spec = e.spec AND l.clause = e.clause "
        "AND l.sec_rel = e.sec_rel AND l.mx = e.tsg_number"
    )


RE_A = re.compile(r"^Change request (R2-\d+) \(CR \S+ to TS \S+\) targets (Rel-\d+)\.")
RE_PACK = re.compile(r"^TSG RAN CR pack (RP-\d+) carries")
RE_RELS = re.compile(r"the release that change request targets \(([^)]*)\)")

with open(PACKET) as f:
    packet = json.load(f)

FIELDS_A = ["clause", "document", "disposition", "wg_meeting", "cr_pack"]
FIELDS_B = ["document", "specification", "clause"]
FIELDS_C = ["specification", "clause", "cr_pack", "tsg_meeting"]

lines = []
for it in packet["items"]:
    qn, fields = it["question"], it["fields"]
    m = RE_A.match(qn)
    if m:
        assert fields == FIELDS_A, it["id"]
        sql = family_a(m.group(1), m.group(2))
    else:
        mp = RE_PACK.match(qn)
        mr = RE_RELS.search(qn)
        assert mp and mr, it["id"]
        rels = re.findall(r"Rel-\d+", mr.group(1))
        assert rels, it["id"]
        if "changes first" in qn:
            assert fields == FIELDS_B, it["id"]
            sql = family_b(mp.group(1), rels)
        elif "latest earlier TSG RAN meeting" in qn:
            assert fields == FIELDS_C, it["id"]
            sql = family_c(mp.group(1), rels)
        else:
            raise SystemExit("unrecognised item " + it["id"])
    lines.append(json.dumps({"id": it["id"], "sql": sql}, ensure_ascii=False))

with open(OUT, "w") as f:
    f.write("\n".join(lines) + "\n")
print(len(lines))
