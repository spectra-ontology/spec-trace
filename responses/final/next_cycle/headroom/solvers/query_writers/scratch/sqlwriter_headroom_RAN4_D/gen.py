"""Generate one SQLite query per packet item for the RAN4 text-to-SQL packet."""
import json
import re
import sys

PACKET = sys.argv[1]
OUT = sys.argv[2]


def norm_rel(x):
    """Release value reduced to its number: 'Rel-17', 'Release 17', 'R17', '17' -> '17'."""
    e = f"lower(trim({x}))"
    for a in ("release", "rel", "r", "-", " ", "_", "."):
        e = f"replace({e},'{a}','')"
    return e


def snorm(x):
    return f"lower(replace(replace(trim({x}),'-','_'),' ','_'))"


VERIFIED = (
    f"({snorm('x.evidence_status')} LIKE 'source%verified%' "
    f"AND {snorm('x.evidence_status')} NOT LIKE '%unverified%' "
    f"AND {snorm('x.evidence_status')} NOT LIKE '%not%')"
)
WHOLE = (
    f"({snorm('x.scope')} IN ('document','doc','whole','full','entire') "
    f"OR {snorm('x.scope')} LIKE 'whole%' OR {snorm('x.scope')} LIKE 'entire%' "
    f"OR {snorm('x.scope')} LIKE 'full_doc%')"
)
WGN = "upper(replace(replace(replace(trim(mt.wg),' ',''),'_',''),'-',''))"
RAN4 = (
    f"({WGN} IN ('RAN4','R4','RANWG4','WG4','TSGRANWG4') "
    "OR (mt.wg IS NULL AND (upper(mt.label) LIKE 'RAN4%' OR upper(mt.label) LIKE 'R4%' "
    "OR upper(mt.id) LIKE 'RAN4%')))"
)

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
inpack AS (
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
cs AS (
  SELECT DISTINCT m.doc_id AS doc_id, s.id AS section_id, s.spec AS spec, s.clause AS clause,
         {norm_rel('s.release')} AS rel
  FROM mods m
  JOIN document d ON d.id = m.doc_id
  JOIN section s ON s.id = m.section_id
  WHERE {norm_rel('s.release')} = {norm_rel('d.target_release')}
),
vd AS (
  SELECT DISTINCT dk.doc_id AS doc_id, x.id AS disp_id, x.code AS code, mt.label AS wg_meeting
  FROM disposition x
  JOIN dk ON dk.k = x.target
  JOIN resolution r ON r.id = x.resolution_id
  JOIN meeting mt ON mt.id = r.meeting_id
  WHERE {VERIFIED} AND {WHOLE} AND {RAN4}
)"""


def q(s):
    return "'" + s.replace("'", "''") + "'"


def pack_cand(pack, rels):
    rel_list = ",".join(q(re.sub(r"\D", "", r)) for r in rels)
    return f""",
tgt AS (
  SELECT id AS pack_id, tsg_number FROM cr_pack WHERE pack_number = {q(pack)} OR id = {q(pack)}
),
cand AS (
  SELECT DISTINCT c.doc_id AS doc_id, d.number AS document, c.spec AS spec, c.clause AS clause,
         c.rel AS rel, t.tsg_number AS tsg_number
  FROM tgt t
  JOIN inpack ip ON ip.pack_id = t.pack_id
  JOIN cs c ON c.doc_id = ip.doc_id
  JOIN document d ON d.id = c.doc_id
  WHERE c.rel IN ({rel_list})
    AND EXISTS (SELECT 1 FROM vd WHERE vd.doc_id = c.doc_id)
),
hist AS (
  SELECT DISTINCT cand.spec AS spec, cand.clause AS clause, cand.rel AS rel,
         p2.id AS pack_id, p2.pack_number AS pack_number, p2.tsg_meeting AS tsg_meeting,
         p2.tsg_number AS tsg_number
  FROM cand
  JOIN cs c2 ON c2.spec = cand.spec AND c2.clause = cand.clause AND c2.rel = cand.rel
  JOIN inpack ip2 ON ip2.doc_id = c2.doc_id
  JOIN cr_pack p2 ON p2.id = ip2.pack_id
  WHERE p2.tsg_number < cand.tsg_number
)"""


def family_first(pack, rels):
    return ("WITH" + COMMON + pack_cand(pack, rels) + """
SELECT DISTINCT cand.document AS document, cand.spec AS specification, cand.clause AS clause
FROM cand
WHERE NOT EXISTS (
  SELECT 1 FROM hist h
  WHERE h.spec = cand.spec AND h.clause = cand.clause AND h.rel = cand.rel
)""")


def family_latest(pack, rels):
    return ("WITH" + COMMON + pack_cand(pack, rels) + """
SELECT DISTINCT h.spec AS specification, h.clause AS clause, h.pack_number AS cr_pack,
       h.tsg_meeting AS tsg_meeting
FROM hist h
WHERE h.tsg_number = (
  SELECT MAX(h2.tsg_number) FROM hist h2
  WHERE h2.spec = h.spec AND h2.clause = h.clause AND h2.rel = h.rel
)""")


def family_others(doc, rel):
    reln = q(re.sub(r"\D", "", rel))
    return ("WITH" + COMMON + f""",
tgtdoc AS (
  SELECT id AS doc_id FROM document WHERE number = {q(doc)} OR id = {q(doc)}
),
tc AS (
  SELECT DISTINCT s.spec AS spec, s.clause AS clause, {norm_rel('s.release')} AS rel
  FROM tgtdoc t
  JOIN mods m ON m.doc_id = t.doc_id
  JOIN section s ON s.id = m.section_id
  WHERE {norm_rel('s.release')} = {reln}
)
SELECT DISTINCT tc.clause AS clause, d2.number AS document, vd.code AS disposition,
       vd.wg_meeting AS wg_meeting, p.pack_number AS cr_pack
FROM tc
JOIN cs c2 ON c2.spec = tc.spec AND c2.clause = tc.clause AND c2.rel = tc.rel
JOIN document d2 ON d2.id = c2.doc_id
JOIN vd ON vd.doc_id = c2.doc_id
JOIN inpack ip ON ip.doc_id = c2.doc_id
JOIN cr_pack p ON p.id = ip.pack_id
WHERE c2.doc_id NOT IN (SELECT doc_id FROM tgtdoc)
  AND COALESCE(d2.number, '') <> {q(doc)}""")


def main():
    with open(PACKET, encoding="utf-8") as f:
        packet = json.load(f)
    lines = []
    for it in packet["items"]:
        qs = it["question"]
        fields = it["fields"]
        if "Keep the clauses that the pack changes first" in qs:
            assert fields == ["document", "specification", "clause"], it["id"]
            pack = re.search(r"CR pack (RP-\d+)", qs).group(1)
            rels = re.findall(r"Rel-\d+", re.search(r"targets \(([^)]*)\)", qs).group(1))
            sql = family_first(pack, rels)
        elif "latest earlier TSG RAN meeting" in qs:
            assert fields == ["specification", "clause", "cr_pack", "tsg_meeting"], it["id"]
            pack = re.search(r"CR pack (RP-\d+)", qs).group(1)
            rels = re.findall(r"Rel-\d+", re.search(r"targets \(([^)]*)\)", qs).group(1))
            sql = family_latest(pack, rels)
        elif qs.startswith("Change request "):
            assert fields == ["clause", "document", "disposition", "wg_meeting", "cr_pack"], it["id"]
            m = re.match(r"Change request (R4-\d+) \(CR \S+ to TS \S+\) targets (Rel-\d+)\.", qs)
            sql = family_others(m.group(1), m.group(2))
        else:
            raise SystemExit("unknown family: " + it["id"])
        lines.append(json.dumps({"id": it["id"], "sql": sql.strip()}, ensure_ascii=False))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(len(lines))


if __name__ == "__main__":
    main()
