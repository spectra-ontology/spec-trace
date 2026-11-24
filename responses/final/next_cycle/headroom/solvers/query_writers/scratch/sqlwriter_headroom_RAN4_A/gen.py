"""Generate one SQLite query per packet item for the RAN4 text-to-SQL packet."""
import json
import re
import sys

PACKET = sys.argv[1]
OUT = sys.argv[2]


def rel(expr):
    """Normalise a release label such as 'Rel-17', 'Release 17' or '17' to '17'."""
    e = f"lower(trim({expr}))"
    for token in ("release", "rel", "r", "-", " ", "."):
        e = f"replace({e}, '{token}', '')"
    return e


VERIFIED = (
    "replace(replace(lower(trim(di.evidence_status)), '_', '-'), ' ', '-') "
    "IN ('source-verified', 'verified', 'sourceverified', 'verified-source')"
)
WHOLE = (
    "replace(replace(lower(trim(di.scope)), '_', ' '), '-', ' ') "
    "IN ('whole document', 'document', 'whole', 'full document', 'full', "
    "'entire document', 'whole doc', 'doc', 'whole tdoc', 'tdoc', 'full tdoc', 'entire', 'all')"
)
RAN4 = (
    "upper(replace(replace(replace(trim(m.wg), ' ', ''), '_', ''), '-', '')) "
    "IN ('RAN4', 'R4', 'RANWG4', 'WG4', 'TSGRANWG4')"
)

BASE = f"""
WITH
doc_key AS (
  SELECT id AS k, id AS doc_id FROM document
  UNION
  SELECT number AS k, id AS doc_id FROM document WHERE number IS NOT NULL
),
docn AS (
  SELECT id AS doc_id, number, {rel('target_release')} AS trel FROM document
),
pack AS (
  SELECT id AS pack_id,
         COALESCE(pack_number, id) AS pack_number,
         tsg_meeting,
         CASE WHEN tsg_number IS NOT NULL THEN tsg_number
              WHEN instr(tsg_meeting, '#') > 0
                THEN CAST(substr(tsg_meeting, instr(tsg_meeting, '#') + 1) AS INTEGER)
         END AS tsg_num
  FROM cr_pack
),
pack_key AS (
  SELECT pack_id AS k, pack_id FROM pack
  UNION
  SELECT pack_number AS k, pack_id FROM pack
),
mem AS (
  SELECT cr, pack_id FROM cr_in_pack
  UNION
  SELECT cr, pack_id FROM pack_member
),
docpack AS (
  SELECT DISTINCT dk.doc_id, p.pack_id, p.pack_number, p.tsg_meeting, p.tsg_num
  FROM mem
  JOIN doc_key dk ON dk.k = mem.cr
  JOIN pack_key pk ON pk.k = mem.pack_id
  JOIN pack p ON p.pack_id = pk.pack_id
),
mods AS (
  SELECT cr, section_id FROM cr_modifies_section
  UNION
  SELECT cr, section_id FROM section_modified_by
),
secn AS (
  SELECT id AS section_id, spec, clause, {rel('release')} AS rel FROM section
),
crclause AS (
  SELECT DISTINCT dk.doc_id, s.spec, s.clause, s.rel
  FROM mods
  JOIN doc_key dk ON dk.k = mods.cr
  JOIN secn s ON s.section_id = mods.section_id
  JOIN docn d ON d.doc_id = dk.doc_id
  WHERE s.rel = d.trel AND s.rel <> ''
),
vdisp AS (
  SELECT DISTINCT dk.doc_id, di.code, COALESCE(m.label, m.id) AS wg_meeting
  FROM disposition di
  JOIN doc_key dk ON dk.k = di.target
  JOIN resolution r ON r.id = di.resolution_id
  JOIN meeting m ON m.id = r.meeting_id
  WHERE {VERIFIED}
    AND {WHOLE}
    AND {RAN4}
)
"""


def pack_ctes(pack):
    return f""",
tc AS (
  SELECT DISTINCT dp.doc_id, dp.tsg_num
  FROM docpack dp
  WHERE (dp.pack_number = '{pack}' OR dp.pack_id = '{pack}')
    AND dp.doc_id IN (SELECT doc_id FROM vdisp)
),
tcl AS (
  SELECT DISTINCT cc.doc_id, cc.spec, cc.clause, cc.rel, tc.tsg_num
  FROM crclause cc
  JOIN tc ON tc.doc_id = cc.doc_id
),
tclk AS (
  SELECT DISTINCT spec, clause, rel FROM tcl
),
cpk AS (
  SELECT DISTINCT cc.spec, cc.clause, cc.rel, dp.pack_number, dp.tsg_meeting, dp.tsg_num
  FROM crclause cc
  JOIN tclk k ON k.spec = cc.spec AND k.clause = cc.clause AND k.rel = cc.rel
  JOIN docpack dp ON dp.doc_id = cc.doc_id
)
"""


def first_change(pack):
    return BASE + pack_ctes(pack) + """
SELECT DISTINCT COALESCE(d.number, d.doc_id) AS document,
       t.spec AS specification,
       t.clause AS clause
FROM tcl t
JOIN docn d ON d.doc_id = t.doc_id
WHERE NOT EXISTS (
  SELECT 1 FROM cpk e
  WHERE e.spec = t.spec AND e.clause = t.clause AND e.rel = t.rel
    AND e.tsg_num < t.tsg_num
)
"""


def latest_earlier(pack):
    return BASE + pack_ctes(pack) + """
SELECT DISTINCT t.spec AS specification,
       t.clause AS clause,
       e.pack_number AS cr_pack,
       e.tsg_meeting AS tsg_meeting
FROM tcl t
JOIN cpk e ON e.spec = t.spec AND e.clause = t.clause AND e.rel = t.rel
WHERE e.tsg_num = (
  SELECT MAX(e2.tsg_num) FROM cpk e2
  WHERE e2.spec = t.spec AND e2.clause = t.clause AND e2.rel = t.rel
    AND e2.tsg_num < t.tsg_num
)
"""


def same_clause_others(tdoc):
    return BASE + f""",
x AS (
  SELECT doc_id FROM docn WHERE number = '{tdoc}' OR doc_id = '{tdoc}'
),
xcl AS (
  SELECT DISTINCT cc.spec, cc.clause, cc.rel
  FROM crclause cc
  JOIN x ON x.doc_id = cc.doc_id
)
SELECT DISTINCT xc.clause AS clause,
       COALESCE(d2.number, d2.doc_id) AS document,
       v.code AS disposition,
       v.wg_meeting AS wg_meeting,
       dp.pack_number AS cr_pack
FROM xcl xc
JOIN crclause c2 ON c2.spec = xc.spec AND c2.clause = xc.clause AND c2.rel = xc.rel
JOIN docn d2 ON d2.doc_id = c2.doc_id
JOIN vdisp v ON v.doc_id = c2.doc_id
JOIN docpack dp ON dp.doc_id = c2.doc_id
WHERE c2.doc_id NOT IN (SELECT doc_id FROM x)
  AND COALESCE(d2.number, '') <> '{tdoc}'
"""


def squash(sql):
    return re.sub(r"\s+", " ", sql).strip()


def main():
    with open(PACKET) as f:
        packet = json.load(f)
    lines = []
    for item in packet["items"]:
        q = item["question"]
        fields = item["fields"]
        if "Keep the clauses that the pack changes first" in q:
            assert fields == ["document", "specification", "clause"], item["id"]
            pack = re.search(r"CR pack (RP-\d+)", q).group(1)
            sql = first_change(pack)
        elif "latest earlier TSG RAN meeting" in q:
            assert fields == ["specification", "clause", "cr_pack", "tsg_meeting"], item["id"]
            pack = re.search(r"CR pack (RP-\d+)", q).group(1)
            sql = latest_earlier(pack)
        elif q.startswith("Change request R4-"):
            assert fields == ["clause", "document", "disposition", "wg_meeting", "cr_pack"], item["id"]
            tdoc = re.match(r"Change request (R4-\d+)", q).group(1)
            sql = same_clause_others(tdoc)
        else:
            raise SystemExit(f"unrecognised family: {item['id']}")
        lines.append(json.dumps({"id": item["id"], "sql": squash(sql)}))
    with open(OUT, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(len(lines))


if __name__ == "__main__":
    main()
