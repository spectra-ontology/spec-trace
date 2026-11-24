"""Generate one SQLite query per RAN4 schema-packet item (run E)."""
import json
import re
import sys

PACKET = sys.argv[1]
OUT = sys.argv[2]

LETTERS = "abcdefghijklmnopqrstuvwxyz -_.#"


def q(value):
    return "'" + value.replace("'", "''") + "'"


def rel(expr):
    """Release label normalised to its major number: 'Rel-17' -> '17'."""
    t = f"ltrim(lower(trim({expr})), '{LETTERS}')"
    return f"(CASE WHEN instr({t}, '.') > 0 THEN substr({t}, 1, instr({t}, '.') - 1) ELSE {t} END)"


VERIFIED = (
    "((lower(di.evidence_status) LIKE '%source%' AND lower(di.evidence_status) LIKE '%verif%') "
    "OR lower(trim(di.evidence_status)) = 'verified') "
    "AND lower(di.evidence_status) NOT LIKE '%unverif%' "
    "AND lower(di.evidence_status) NOT LIKE '%non%verif%' "
    "AND lower(di.evidence_status) NOT LIKE 'not%' "
    "AND instr(lower(di.evidence_status), '_not') = 0 "
    "AND instr(lower(di.evidence_status), '-not') = 0 "
    "AND instr(lower(di.evidence_status), ' not') = 0"
)
WHOLE = (
    "(lower(di.scope) LIKE '%whole%' OR lower(di.scope) LIKE '%entire%' OR lower(di.scope) LIKE 'full%' "
    "OR lower(trim(di.scope)) IN ('document', 'doc', 'tdoc', 'all')) "
    "AND lower(di.scope) NOT LIKE '%part%'"
)
RAN4 = (
    "replace(replace(replace(upper(m.wg), ' ', ''), '_', ''), '-', '') "
    "IN ('RAN4', 'R4', 'RANWG4', 'WG4', 'TSGRANWG4')"
)

COMMON = f"""WITH
dk AS (
  SELECT id AS k, id AS doc_id FROM document
  UNION SELECT number AS k, id AS doc_id FROM document WHERE number IS NOT NULL
),
pk AS (
  SELECT id AS k, id AS pid FROM cr_pack
  UNION SELECT pack_number AS k, id AS pid FROM cr_pack WHERE pack_number IS NOT NULL
),
cp AS (
  SELECT DISTINCT dk.doc_id AS doc_id, p.id AS pack_id, p.pack_number AS pack_number,
         p.tsg_meeting AS tsg_meeting, p.tsg_number AS tsg_number
  FROM (SELECT cr, pack_id FROM cr_in_pack UNION SELECT cr, pack_id FROM pack_member) mem
  JOIN dk ON dk.k = mem.cr
  JOIN pk ON pk.k = mem.pack_id
  JOIN cr_pack p ON p.id = pk.pid
),
cc AS (
  SELECT DISTINCT d.id AS doc_id, s.spec AS spec, s.clause AS clause, {rel('s.release')} AS rel
  FROM (SELECT cr, section_id FROM cr_modifies_section UNION SELECT cr, section_id FROM section_modified_by) md
  JOIN dk ON dk.k = md.cr
  JOIN document d ON d.id = dk.doc_id
  JOIN section s ON s.id = md.section_id
  WHERE {rel('s.release')} = {rel('d.target_release')}
),
okd AS (
  SELECT DISTINCT dk.doc_id AS doc_id, di.code AS code, m.label AS wg_meeting
  FROM disposition di
  JOIN resolution r ON r.id = di.resolution_id
  JOIN meeting m ON m.id = r.meeting_id
  JOIN dk ON dk.k = di.target
  WHERE {VERIFIED}
    AND {WHOLE}
    AND {RAN4}
)"""


def anchor_pack(pack):
    return (
        "anc AS (\n"
        f"  SELECT id AS pack_id, tsg_number AS atn FROM cr_pack WHERE pack_number = {q(pack)} OR id = {q(pack)}\n"
        ")"
    )


def sql_first(pack):
    return f"""{COMMON},
{anchor_pack(pack)},
a AS (
  SELECT DISTINCT cp.doc_id AS doc_id, anc.atn AS atn
  FROM anc JOIN cp ON cp.pack_id = anc.pack_id
  WHERE cp.doc_id IN (SELECT doc_id FROM okd)
)
SELECT DISTINCT COALESCE(d.number, d.id) AS document, c.spec AS specification, c.clause AS clause
FROM a
JOIN document d ON d.id = a.doc_id
JOIN cc c ON c.doc_id = a.doc_id
WHERE NOT EXISTS (
  SELECT 1 FROM cc c2 JOIN cp p2 ON p2.doc_id = c2.doc_id
  WHERE c2.spec = c.spec AND c2.clause = c.clause AND c2.rel = c.rel
    AND p2.tsg_number < a.atn
)"""


def sql_latest(pack):
    return f"""{COMMON},
{anchor_pack(pack)},
b AS (
  SELECT DISTINCT c.spec AS spec, c.clause AS clause, c.rel AS rel, anc.atn AS atn
  FROM anc
  JOIN cp ON cp.pack_id = anc.pack_id
  JOIN cc c ON c.doc_id = cp.doc_id
  WHERE cp.doc_id IN (SELECT doc_id FROM okd)
),
ea AS (
  SELECT DISTINCT b.spec AS spec, b.clause AS clause, b.rel AS rel, b.atn AS atn,
         p2.pack_number AS pack_number, p2.tsg_meeting AS tsg_meeting, p2.tsg_number AS tsg_number
  FROM b
  JOIN cc c2 ON c2.spec = b.spec AND c2.clause = b.clause AND c2.rel = b.rel
  JOIN cp p2 ON p2.doc_id = c2.doc_id
  WHERE p2.tsg_number < b.atn
),
mx AS (
  SELECT spec, clause, rel, atn, MAX(tsg_number) AS mt FROM ea GROUP BY spec, clause, rel, atn
)
SELECT DISTINCT ea.spec AS specification, ea.clause AS clause, ea.pack_number AS cr_pack, ea.tsg_meeting AS tsg_meeting
FROM ea
JOIN mx ON mx.spec = ea.spec AND mx.clause = ea.clause AND mx.rel = ea.rel AND mx.atn = ea.atn
       AND ea.tsg_number = mx.mt"""


def sql_cr(number, release):
    return f"""{COMMON},
anc AS (
  SELECT id FROM document WHERE number = {q(number)} OR id = {q(number)}
),
ac AS (
  SELECT DISTINCT c.spec AS spec, c.clause AS clause, c.rel AS rel
  FROM cc c
  WHERE c.doc_id IN (SELECT id FROM anc) AND c.rel = {q(release)}
)
SELECT DISTINCT ac.clause AS clause, COALESCE(d2.number, d2.id) AS document, o.code AS disposition,
       o.wg_meeting AS wg_meeting, p2.pack_number AS cr_pack
FROM ac
JOIN cc c2 ON c2.spec = ac.spec AND c2.clause = ac.clause AND c2.rel = ac.rel
JOIN document d2 ON d2.id = c2.doc_id
JOIN okd o ON o.doc_id = d2.id
JOIN cp p2 ON p2.doc_id = d2.id
WHERE d2.id NOT IN (SELECT id FROM anc)
  AND COALESCE(d2.number, '') <> {q(number)}"""


RE_CR = re.compile(r"^Change request (\S+) \(CR \S+ to TS \S+\) targets Rel-(\d+)\.")
RE_PACK = re.compile(r"^TSG RAN CR pack (RP-\d+) carries change requests from RAN4\.")

FIELDS = {
    "first": ["document", "specification", "clause"],
    "latest": ["specification", "clause", "cr_pack", "tsg_meeting"],
    "cr": ["clause", "document", "disposition", "wg_meeting", "cr_pack"],
}


def main():
    with open(PACKET, encoding="utf-8") as fh:
        packet = json.load(fh)
    lines = []
    for item in packet["items"]:
        question = item["question"]
        m_cr = RE_CR.match(question)
        m_pack = RE_PACK.match(question)
        if m_cr:
            family = "cr"
            sql = sql_cr(m_cr.group(1), m_cr.group(2))
        elif m_pack and "Keep the clauses that the pack changes first" in question:
            family = "first"
            sql = sql_first(m_pack.group(1))
        elif m_pack and "latest earlier TSG RAN meeting" in question:
            family = "latest"
            sql = sql_latest(m_pack.group(1))
        else:
            raise SystemExit(f"unrecognised item {item['id']}")
        if item["fields"] != FIELDS[family]:
            raise SystemExit(f"field mismatch {item['id']}: {item['fields']}")
        lines.append(json.dumps({"id": item["id"], "sql": sql}, ensure_ascii=False))
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(len(lines))


if __name__ == "__main__":
    main()
