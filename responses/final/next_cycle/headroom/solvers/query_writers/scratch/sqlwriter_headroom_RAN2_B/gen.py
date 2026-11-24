"""Generate one SQLite query per packet item for the RAN2 text-to-SQL packet."""
import json
import re
import sys

PACKET = sys.argv[1]
OUT = sys.argv[2]


def rel(expr):
    return f"ltrim(lower(trim({expr})),'release- _')"


STATUS = (
    "lower(ds.evidence_status) LIKE '%source%' "
    "AND lower(ds.evidence_status) LIKE '%verified%' "
    "AND lower(ds.evidence_status) NOT LIKE '%unverified%' "
    "AND lower(ds.evidence_status) NOT LIKE '%not%' "
    "AND lower(ds.evidence_status) NOT LIKE '%non%verified%'"
)
SCOPE = (
    "(lower(trim(ds.scope)) IN ('document','doc','whole','whole_document','whole-document',"
    "'whole document','entire_document','entire document','full','full_document','full document',"
    "'tdoc','all') OR lower(ds.scope) LIKE '%whole%' OR lower(ds.scope) LIKE '%entire%')"
)
RAN2 = (
    "(upper(replace(replace(replace(trim(m.wg),' ',''),'_',''),'-','')) IN "
    "('RAN2','R2','RANWG2','TSGRANWG2','WG2','TSGRAN2') "
    "OR (m.wg IS NULL AND (upper(m.label) LIKE 'RAN2%' OR upper(m.label) LIKE 'R2%' "
    "OR upper(m.label) LIKE 'RAN WG2%')))"
)

COMMON = f"""WITH
dk(k, doc_id) AS (
  SELECT id, id FROM document WHERE id IS NOT NULL
  UNION SELECT number, id FROM document WHERE number IS NOT NULL),
pk(k, pack_id) AS (
  SELECT id, id FROM cr_pack WHERE id IS NOT NULL
  UNION SELECT pack_number, id FROM cr_pack WHERE pack_number IS NOT NULL),
mk(k, meeting_id) AS (
  SELECT id, id FROM meeting WHERE id IS NOT NULL
  UNION SELECT label, id FROM meeting WHERE label IS NOT NULL),
inpack(doc_id, pack_id) AS (
  SELECT DISTINCT dk.doc_id, pk.pack_id
  FROM (SELECT cr, pack_id FROM cr_in_pack UNION SELECT cr, pack_id FROM pack_member) r
  JOIN dk ON dk.k = r.cr
  JOIN pk ON pk.k = r.pack_id),
modrel(cr, section_id) AS (
  SELECT cr, section_id FROM cr_modifies_section
  UNION SELECT cr, section_id FROM section_modified_by),
crsec(doc_id, spec, clause, relk) AS (
  SELECT DISTINCT dk.doc_id, s.spec, s.clause, {rel('s.release')}
  FROM modrel r
  JOIN dk ON dk.k = r.cr
  JOIN section s ON s.id = r.section_id
  JOIN document d ON d.id = dk.doc_id
  WHERE {rel('s.release')} = {rel('d.target_release')}),
qd(doc_id, code, wg_meeting) AS (
  SELECT DISTINCT dk.doc_id, ds.code, COALESCE(m.label, m.id)
  FROM disposition ds
  JOIN dk ON dk.k = ds.target
  JOIN resolution rs ON rs.id = ds.resolution_id
  JOIN mk ON mk.k = rs.meeting_id
  JOIN meeting m ON m.id = mk.meeting_id
  WHERE {STATUS}
    AND {SCOPE}
    AND {RAN2})"""


def q(s):
    return "'" + s.replace("'", "''") + "'"


def family_cr(doc, release):
    return COMMON + f""",
tgt(doc_id) AS (
  SELECT id FROM document WHERE id = {q(doc)} OR number = {q(doc)}),
tcl(spec, clause, relk) AS (
  SELECT DISTINCT s.spec, s.clause, {rel('s.release')}
  FROM modrel r
  JOIN dk ON dk.k = r.cr
  JOIN tgt ON tgt.doc_id = dk.doc_id
  JOIN section s ON s.id = r.section_id
  WHERE {rel('s.release')} = {rel(q(release))})
SELECT DISTINCT t.clause AS clause,
       COALESCE(d2.number, d2.id) AS document,
       qd.code AS disposition,
       qd.wg_meeting AS wg_meeting,
       COALESCE(p.pack_number, p.id) AS cr_pack
FROM tcl t
JOIN crsec c ON c.spec = t.spec AND c.clause = t.clause AND c.relk = t.relk
JOIN document d2 ON d2.id = c.doc_id
JOIN qd ON qd.doc_id = c.doc_id
JOIN inpack ip ON ip.doc_id = c.doc_id
JOIN cr_pack p ON p.id = ip.pack_id
WHERE c.doc_id NOT IN (SELECT doc_id FROM tgt)"""


def pack_base(pack, with_doc):
    doc_col = "c.doc_id, " if with_doc else ""
    doc_def = "doc_id, " if with_doc else ""
    return f""",
P(pack_id, tn) AS (
  SELECT id, tsg_number FROM cr_pack WHERE pack_number = {q(pack)} OR id = {q(pack)}),
base({doc_def}spec, clause, relk, tn) AS (
  SELECT DISTINCT {doc_col}c.spec, c.clause, c.relk, P.tn
  FROM P
  JOIN inpack ip ON ip.pack_id = P.pack_id
  JOIN crsec c ON c.doc_id = ip.doc_id
  WHERE c.doc_id IN (SELECT doc_id FROM qd))"""


def family_first(pack):
    return COMMON + pack_base(pack, True) + """
SELECT DISTINCT COALESCE(d.number, d.id) AS document,
       b.spec AS specification,
       b.clause AS clause
FROM base b
JOIN document d ON d.id = b.doc_id
WHERE NOT EXISTS (
  SELECT 1
  FROM crsec c2
  JOIN inpack ip2 ON ip2.doc_id = c2.doc_id
  JOIN cr_pack p2 ON p2.id = ip2.pack_id
  WHERE c2.spec = b.spec AND c2.clause = b.clause AND c2.relk = b.relk
    AND p2.tsg_number < b.tn)"""


def family_latest(pack):
    return COMMON + pack_base(pack, False) + """,
earlier(spec, clause, relk, cr_pack, tsg_meeting, tsg_number) AS (
  SELECT DISTINCT b.spec, b.clause, b.relk, COALESCE(p2.pack_number, p2.id), p2.tsg_meeting, p2.tsg_number
  FROM base b
  JOIN crsec c2 ON c2.spec = b.spec AND c2.clause = b.clause AND c2.relk = b.relk
  JOIN inpack ip2 ON ip2.doc_id = c2.doc_id
  JOIN cr_pack p2 ON p2.id = ip2.pack_id
  WHERE p2.tsg_number < b.tn),
mx(spec, clause, relk, mt) AS (
  SELECT spec, clause, relk, MAX(tsg_number) FROM earlier GROUP BY spec, clause, relk)
SELECT DISTINCT e.spec AS specification,
       e.clause AS clause,
       e.cr_pack AS cr_pack,
       e.tsg_meeting AS tsg_meeting
FROM earlier e
JOIN mx ON mx.spec = e.spec AND mx.clause = e.clause AND mx.relk = e.relk AND e.tsg_number = mx.mt"""


RE_CR = re.compile(r"^Change request (R2-\d+) \(CR \w+ to TS [\d.]+\) targets (Rel-\d+)\.")
RE_PACK = re.compile(r"^TSG RAN CR pack (RP-\d+) carries change requests from RAN2\.")

F_CR = ["clause", "document", "disposition", "wg_meeting", "cr_pack"]
F_FIRST = ["document", "specification", "clause"]
F_LATEST = ["specification", "clause", "cr_pack", "tsg_meeting"]

with open(PACKET, encoding="utf-8") as fh:
    packet = json.load(fh)

lines = []
for item in packet["items"]:
    qtext = item["question"]
    fields = item["fields"]
    m = RE_CR.match(qtext)
    if m:
        assert fields == F_CR, item["id"]
        sql = family_cr(m.group(1), m.group(2))
    else:
        m = RE_PACK.match(qtext)
        assert m, item["id"]
        if "Keep the clauses that the pack changes first" in qtext:
            assert fields == F_FIRST, item["id"]
            sql = family_first(m.group(1))
        elif "give every CR pack of the latest earlier TSG RAN meeting" in qtext:
            assert fields == F_LATEST, item["id"]
            sql = family_latest(m.group(1))
        else:
            raise SystemExit("unrecognised item " + item["id"])
    lines.append(json.dumps({"id": item["id"], "sql": sql}, ensure_ascii=False))

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")
print(len(lines))
