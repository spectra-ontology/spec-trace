"""Generate one SQLite query per RAN4 packet item (run C)."""
import json
import re
import sys

PACKET = sys.argv[1]
OUT = sys.argv[2]

COMMON = """
dockey AS (
  SELECT id AS k, id AS doc_id FROM document
  UNION SELECT number AS k, id AS doc_id FROM document WHERE number IS NOT NULL
),
packkey AS (
  SELECT id AS k, id AS pid FROM cr_pack
  UNION SELECT pack_number AS k, id AS pid FROM cr_pack WHERE pack_number IS NOT NULL
),
inpack AS (
  SELECT DISTINCT dk.doc_id AS doc_id, pk.pid AS pid
  FROM (SELECT cr, pack_id FROM cr_in_pack UNION SELECT cr, pack_id FROM pack_member) x
  JOIN dockey dk ON dk.k = x.cr
  JOIN packkey pk ON pk.k = x.pack_id
),
mods AS (
  SELECT DISTINCT dk.doc_id AS doc_id, x.section_id AS section_id
  FROM (SELECT cr, section_id FROM cr_modifies_section
        UNION SELECT cr, section_id FROM section_modified_by) x
  JOIN dockey dk ON dk.k = x.cr
),
okdoc AS (
  SELECT DISTINCT dk.doc_id AS doc_id, di.code AS code, COALESCE(m.label, m.id) AS wg_meeting
  FROM disposition di
  JOIN dockey dk ON dk.k = di.target
  JOIN resolution r ON r.id = di.resolution_id
  JOIN meeting m ON m.id = r.meeting_id
  WHERE (di.evidence_status LIKE '%source_verified%'
         OR di.evidence_status LIKE '%sourceverified%'
         OR lower(di.evidence_status) = 'verified')
    AND (lower(di.scope) LIKE '%whole%' OR lower(di.scope) LIKE '%entire%'
         OR lower(di.scope) LIKE '%full%'
         OR lower(di.scope) IN ('document', 'doc', 'all', 'tdoc'))
    AND replace(replace(replace(upper(m.wg), ' ', ''), '_', ''), '-', '')
        IN ('RAN4', 'R4', 'WG4', 'RANWG4', 'TSGRANWG4', 'TSGR4')
),
modsec AS (
  SELECT DISTINCT d.id AS doc_id, d.number AS number, d.target_release AS rel,
         s.spec AS spec, s.clause AS clause
  FROM document d
  JOIN mods mo ON mo.doc_id = d.id
  JOIN section s ON s.id = mo.section_id
  WHERE s.release = d.target_release
),
prior AS (
  SELECT DISTINCT ms.spec AS spec, ms.clause AS clause, ms.rel AS rel,
         p.tsg_number AS tn, p.pack_number AS pack_number, p.tsg_meeting AS tsg_meeting
  FROM modsec ms
  JOIN inpack ip ON ip.doc_id = ms.doc_id
  JOIN cr_pack p ON p.id = ip.pid
)
"""

BASE = """
base AS (
  SELECT DISTINCT ms.number AS number, ms.spec AS spec, ms.clause AS clause,
         ms.rel AS rel, p.tsg_number AS tn
  FROM cr_pack p
  JOIN inpack ip ON ip.pid = p.id
  JOIN modsec ms ON ms.doc_id = ip.doc_id
  WHERE (p.pack_number = '{pack}' OR p.id = '{pack}')
    AND ms.doc_id IN (SELECT doc_id FROM okdoc)
)
"""

FIRST = ("WITH " + COMMON + "," + BASE + """
SELECT DISTINCT b.number AS document, b.spec AS specification, b.clause AS clause
FROM base b
WHERE NOT EXISTS (
  SELECT 1 FROM prior pr
  WHERE pr.spec = b.spec AND pr.clause = b.clause AND pr.rel = b.rel AND pr.tn < b.tn
)
""")

LATEST = ("WITH " + COMMON + "," + BASE + """,
cand AS (
  SELECT DISTINCT b.spec AS spec, b.clause AS clause, b.rel AS rel, b.tn AS btn,
         pr.tn AS ptn, pr.pack_number AS pack_number, pr.tsg_meeting AS tsg_meeting
  FROM base b
  JOIN prior pr ON pr.spec = b.spec AND pr.clause = b.clause AND pr.rel = b.rel
               AND pr.tn < b.tn
),
latest AS (
  SELECT spec, clause, rel, btn, MAX(ptn) AS mt FROM cand GROUP BY spec, clause, rel, btn
)
SELECT DISTINCT c.spec AS specification, c.clause AS clause,
       c.pack_number AS cr_pack, c.tsg_meeting AS tsg_meeting
FROM cand c
JOIN latest l ON l.spec = c.spec AND l.clause = c.clause AND l.rel = c.rel
             AND l.btn = c.btn AND c.ptn = l.mt
""")

PEERS = ("WITH " + COMMON + """,
src AS (
  SELECT id AS doc_id FROM document WHERE number = '{doc}' OR id = '{doc}'
),
tgt AS (
  SELECT DISTINCT ms.spec AS spec, ms.clause AS clause, ms.rel AS rel
  FROM modsec ms JOIN src ON src.doc_id = ms.doc_id
)
SELECT DISTINCT t.clause AS clause, ms.number AS document, od.code AS disposition,
       od.wg_meeting AS wg_meeting, p.pack_number AS cr_pack
FROM tgt t
JOIN modsec ms ON ms.spec = t.spec AND ms.clause = t.clause AND ms.rel = t.rel
JOIN okdoc od ON od.doc_id = ms.doc_id
JOIN inpack ip ON ip.doc_id = ms.doc_id
JOIN cr_pack p ON p.id = ip.pid
WHERE ms.doc_id NOT IN (SELECT doc_id FROM src)
  AND COALESCE(ms.number, '') <> '{doc}'
""")


def squash(sql):
    return re.sub(r"\s+", " ", sql).strip()


def main():
    with open(PACKET, encoding="utf-8") as f:
        packet = json.load(f)
    lines = []
    for item in packet["items"]:
        q = item["question"]
        fields = item["fields"]
        if "Keep the clauses that the pack changes first" in q:
            assert fields == ["document", "specification", "clause"], item["id"]
            pack = re.search(r"CR pack (RP-\d+)", q).group(1)
            sql = FIRST.format(pack=pack)
        elif "latest earlier TSG RAN meeting" in q:
            assert fields == ["specification", "clause", "cr_pack", "tsg_meeting"], item["id"]
            pack = re.search(r"CR pack (RP-\d+)", q).group(1)
            sql = LATEST.format(pack=pack)
        elif q.startswith("Change request "):
            assert fields == ["clause", "document", "disposition", "wg_meeting", "cr_pack"], item["id"]
            doc = re.match(r"Change request (R4-\d+)", q).group(1)
            sql = PEERS.format(doc=doc)
        else:
            raise SystemExit("unknown family: " + item["id"])
        lines.append(json.dumps({"id": item["id"], "sql": squash(sql)}, ensure_ascii=False))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(len(lines))


if __name__ == "__main__":
    main()
