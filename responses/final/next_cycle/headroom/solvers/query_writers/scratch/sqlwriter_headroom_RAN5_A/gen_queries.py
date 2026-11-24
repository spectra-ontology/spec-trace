"""Generate one SQLite query per packet item for the RAN5 text-to-SQL packet.

Usage: python3 gen_queries.py PACKET_JSON OUTPUT_JSONL
"""
import json
import re
import sys


def norm(x):
    """Lower-case and drop '_', '-', spaces so label variants compare equal."""
    return f"LOWER(REPLACE(REPLACE(REPLACE(TRIM({x}),'_',''),'-',''),' ',''))"


def nrel(x):
    """Reduce 'Rel-19' / 'Release 19' / 'R19' / '19' to '19'."""
    return (
        "LTRIM(REPLACE(REPLACE(REPLACE(REPLACE(LOWER(TRIM("
        f"{x}"
        ")),'release',''),'rel',''),'-',''),' ',''),'r')"
    )


EVIDENCE_OK = f"{norm('d.evidence_status')} IN ('sourceverified','verifiedsource','verifiedfromsource')"
SCOPE_OK = (
    f"{norm('d.scope')} IN ('wholedocument','document','whole','fulldocument','full',"
    "'entiredocument','entire','doc','wholedoc','documentlevel','tdoc')"
)
WG_OK = f"{norm('m.wg')} IN ('ran5','r5','ranwg5','tsgranwg5','wg5')"

COMMON = f"""
dk AS (
  SELECT id AS k, id AS doc_id FROM document
  UNION
  SELECT number AS k, id AS doc_id FROM document WHERE number IS NOT NULL
),
pk AS (
  SELECT id AS k, id AS pack_id FROM cr_pack
  UNION
  SELECT pack_number AS k, id AS pack_id FROM cr_pack WHERE pack_number IS NOT NULL
),
mk AS (
  SELECT id AS k, id AS meeting_id FROM meeting
  UNION
  SELECT label AS k, id AS meeting_id FROM meeting WHERE label IS NOT NULL
),
mem AS (
  SELECT DISTINCT dk.doc_id AS doc_id, pk.pack_id AS pack_id
  FROM (SELECT cr, pack_id FROM cr_in_pack UNION SELECT cr, pack_id FROM pack_member) e
  JOIN dk ON dk.k = e.cr
  JOIN pk ON pk.k = e.pack_id
),
mods AS (
  SELECT DISTINCT dk.doc_id AS doc_id, e.section_id AS section_id
  FROM (SELECT cr, section_id FROM cr_modifies_section
        UNION SELECT cr, section_id FROM section_modified_by) e
  JOIN dk ON dk.k = e.cr
),
disp AS (
  SELECT DISTINCT dk.doc_id AS doc_id, d.code AS code,
         COALESCE(m.label, m.id) AS wg_meeting
  FROM disposition d
  JOIN dk ON dk.k = d.target
  JOIN resolution r ON r.id = d.resolution_id
  JOIN mk ON mk.k = r.meeting_id
  JOIN meeting m ON m.id = mk.meeting_id
  WHERE {EVIDENCE_OK}
    AND {SCOPE_OK}
    AND {WG_OK}
)"""


def pack_cte(rp):
    return f"""
P AS (
  SELECT id AS pack_id, tsg_number AS tn FROM cr_pack
  WHERE pack_number = '{rp}' OR id = '{rp}'
)"""


BASE_JOINS = f"""
  FROM P
  JOIN mem ON mem.pack_id = P.pack_id
  JOIN document doc ON doc.id = mem.doc_id
  JOIN mods ON mods.doc_id = doc.id
  JOIN section s ON s.id = mods.section_id
  WHERE {nrel('s.release')} = {nrel('doc.target_release')}
    AND EXISTS (SELECT 1 FROM disp WHERE disp.doc_id = doc.id)"""

# Change requests of the clause's release that modify the same clause
# (same spec, release, clause) and sit in a CR pack.
SAME_CLAUSE_IN_PACK = f"""
  JOIN section s2 ON s2.spec = {{o}}.spec AND s2.release = {{o}}.rel AND s2.clause = {{o}}.clause
  JOIN mods m2 ON m2.section_id = s2.id
  JOIN document d2 ON d2.id = m2.doc_id
  JOIN mem me2 ON me2.doc_id = d2.id
  JOIN cr_pack cp ON cp.id = me2.pack_id"""


def first_change_sql(rp):
    return f"""WITH {COMMON},{pack_cte(rp)},
base AS (
  SELECT DISTINCT COALESCE(doc.number, doc.id) AS document, s.spec AS spec,
         s.release AS rel, s.clause AS clause, P.tn AS tn{BASE_JOINS}
)
SELECT DISTINCT b.document AS document, b.spec AS specification, b.clause AS clause
FROM base b
WHERE NOT EXISTS (
  SELECT 1
  FROM section s2
  JOIN mods m2 ON m2.section_id = s2.id
  JOIN document d2 ON d2.id = m2.doc_id
  JOIN mem me2 ON me2.doc_id = d2.id
  JOIN cr_pack cp ON cp.id = me2.pack_id
  WHERE s2.spec = b.spec AND s2.release = b.rel AND s2.clause = b.clause
    AND {nrel('d2.target_release')} = {nrel('s2.release')}
    AND cp.tsg_number < b.tn
)"""


def latest_earlier_sql(rp):
    return f"""WITH {COMMON},{pack_cte(rp)},
base AS (
  SELECT DISTINCT s.spec AS spec, s.release AS rel, s.clause AS clause, P.tn AS tn{BASE_JOINS}
),
cand AS (
  SELECT DISTINCT b.spec AS spec, b.rel AS rel, b.clause AS clause, b.tn AS tn,
         COALESCE(cp.pack_number, cp.id) AS pack_number, cp.tsg_meeting AS tsg_meeting,
         cp.tsg_number AS ptn
  FROM base b{SAME_CLAUSE_IN_PACK.format(o='b')}
  WHERE {nrel('d2.target_release')} = {nrel('s2.release')}
    AND cp.tsg_number < b.tn
)
SELECT DISTINCT c.spec AS specification, c.clause AS clause,
       c.pack_number AS cr_pack, c.tsg_meeting AS tsg_meeting
FROM cand c
WHERE c.ptn = (
  SELECT MAX(c3.ptn) FROM cand c3
  WHERE c3.spec = c.spec AND c3.rel = c.rel AND c3.clause = c.clause AND c3.tn = c.tn
)"""


def same_clause_peers_sql(num):
    return f"""WITH {COMMON},
X AS (
  SELECT id AS doc_id, target_release AS tr FROM document
  WHERE number = '{num}' OR id = '{num}'
),
xs AS (
  SELECT DISTINCT s.spec AS spec, s.release AS rel, s.clause AS clause
  FROM X
  JOIN mods ON mods.doc_id = X.doc_id
  JOIN section s ON s.id = mods.section_id
  WHERE {nrel('s.release')} = {nrel('X.tr')}
)
SELECT DISTINCT xs.clause AS clause, COALESCE(d2.number, d2.id) AS document,
       disp.code AS disposition, disp.wg_meeting AS wg_meeting,
       COALESCE(cp.pack_number, cp.id) AS cr_pack
FROM xs{SAME_CLAUSE_IN_PACK.format(o='xs')}
  JOIN disp ON disp.doc_id = d2.id
WHERE {nrel('d2.target_release')} = {nrel('s2.release')}
  AND d2.id NOT IN (SELECT doc_id FROM X)
  AND COALESCE(d2.number, '') <> '{num}'"""


FAMILIES = {
    "first": (["document", "specification", "clause"], first_change_sql),
    "latest": (["specification", "clause", "cr_pack", "tsg_meeting"], latest_earlier_sql),
    "peers": (["clause", "document", "disposition", "wg_meeting", "cr_pack"], same_clause_peers_sql),
}


def classify(q):
    m = re.match(r"TSG RAN CR pack (RP-\d+) carries", q)
    if m:
        if "Keep the clauses that the pack changes first" in q:
            return "first", m.group(1)
        if "latest earlier TSG RAN meeting" in q:
            return "latest", m.group(1)
    m = re.match(r"Change request (R5-\d+) \(CR ", q)
    if m and "other than " + m.group(1) in q:
        return "peers", m.group(1)
    raise ValueError("unclassified question: " + q[:80])


def main():
    packet = json.load(open(sys.argv[1], encoding="utf-8"))
    out = []
    for it in packet["items"]:
        fam, key = classify(it["question"])
        fields, fn = FAMILIES[fam]
        assert it["fields"] == fields, (it["id"], it["fields"])
        sql = re.sub(r"\s+", " ", fn(key)).strip()
        out.append({"id": it["id"], "sql": sql})
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        for row in out:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    counts = {}
    for it in packet["items"]:
        fam, _ = classify(it["question"])
        counts[fam] = counts.get(fam, 0) + 1
    print(len(out), counts)


if __name__ == "__main__":
    main()
