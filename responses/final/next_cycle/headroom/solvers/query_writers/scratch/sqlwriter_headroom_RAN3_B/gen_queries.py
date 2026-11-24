"""Generate one SQLite query per item of the RAN3 text-to-SQL packet.

Reads only the packet given on the command line and writes one JSON line per
item ({"id", "sql"}) in packet order.
"""
import json
import re
import sys


def rel(x):
    """Release value normalised to an integer ('Rel-16', 'Release 16', '16' -> 16)."""
    return (
        "CAST(TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(LOWER(%s),"
        "'release',''),'rel',''),'r',''),'-',''),'_','')) AS INTEGER)" % x
    )


def norm_lower(x):
    return "LOWER(REPLACE(REPLACE(REPLACE(TRIM(%s),' ',''),'_',''),'-',''))" % x


def norm_upper(x):
    return "UPPER(REPLACE(REPLACE(REPLACE(TRIM(%s),' ',''),'_',''),'-',''))" % x


STATUS = norm_lower("dp.evidence_status") + " IN ('sourceverified','verifiedsource')"
SCOPE = norm_lower("dp.scope") + (
    " IN ('wholedocument','document','whole','fulldocument','entiredocument',"
    "'doc','wholedoc','tdoc','wholetdoc','entiretdoc','fulltdoc')"
)
WG = (
    "(" + norm_upper("m.wg") + " IN ('RAN3','R3','RANWG3','TSGRANWG3','WG3','3','RAN3WG')"
    " OR (m.wg IS NULL AND (m.label LIKE 'R3%' OR m.label LIKE '%RAN3%'"
    " OR m.label LIKE '%RAN_WG3%')))"
)

COMMON = f"""
docref AS (
  SELECT id AS ref, id AS doc_id FROM document WHERE id IS NOT NULL
  UNION
  SELECT number AS ref, id AS doc_id FROM document WHERE number IS NOT NULL
),
packref AS (
  SELECT id AS ref, id AS pack_id FROM cr_pack WHERE id IS NOT NULL
  UNION
  SELECT pack_number AS ref, id AS pack_id FROM cr_pack WHERE pack_number IS NOT NULL
),
inpack AS (
  SELECT DISTINCT dr.doc_id AS doc_id, pr.pack_id AS pack_id
  FROM (SELECT cr, pack_id FROM cr_in_pack UNION SELECT cr, pack_id FROM pack_member) e
  JOIN docref dr ON dr.ref = e.cr
  JOIN packref pr ON pr.ref = e.pack_id
),
modsec AS (
  SELECT DISTINCT dr.doc_id AS doc_id, e.section_id AS section_id
  FROM (SELECT cr, section_id FROM cr_modifies_section
        UNION SELECT cr, section_id FROM section_modified_by) e
  JOIN docref dr ON dr.ref = e.cr
),
mods AS (
  SELECT DISTINCT ms.doc_id AS doc_id, s.spec AS spec, s.clause AS clause,
         {rel('s.release')} AS rel
  FROM modsec ms
  JOIN document d ON d.id = ms.doc_id
  JOIN section s ON s.id = ms.section_id
  WHERE {rel('s.release')} = {rel('d.target_release')}
),
verified AS (
  SELECT DISTINCT dr.doc_id AS doc_id, dp.code AS code, m.label AS wg_meeting
  FROM disposition dp
  JOIN docref dr ON dr.ref = dp.target
  JOIN resolution r ON r.id = dp.resolution_id
  JOIN meeting m ON (m.id = r.meeting_id OR m.label = r.meeting_id)
  WHERE {STATUS}
    AND {SCOPE}
    AND {WG}
)"""


def pack_seed_ctes(pack, rels):
    rel_list = ", ".join(str(r) for r in rels)
    return f""",
target_pack AS (
  SELECT id AS pack_id, tsg_number AS p_num FROM cr_pack
  WHERE pack_number = '{pack}' OR id = '{pack}'
),
seeds AS (
  SELECT DISTINCT tp.p_num AS p_num, m.doc_id AS doc_id, m.spec AS spec,
         m.clause AS clause, m.rel AS rel
  FROM target_pack tp
  JOIN inpack ip ON ip.pack_id = tp.pack_id
  JOIN mods m ON m.doc_id = ip.doc_id
  WHERE m.rel IN ({rel_list})
    AND m.doc_id IN (SELECT doc_id FROM verified)
)"""


def q_first(pack, rels):
    return "WITH" + COMMON + pack_seed_ctes(pack, rels) + """
SELECT DISTINCT COALESCE(d.number, d.id) AS document, s.spec AS specification,
       s.clause AS clause
FROM seeds s
JOIN document d ON d.id = s.doc_id
WHERE NOT EXISTS (
  SELECT 1
  FROM mods m2
  JOIN inpack ip2 ON ip2.doc_id = m2.doc_id
  JOIN cr_pack cp2 ON cp2.id = ip2.pack_id
  WHERE m2.spec = s.spec AND m2.clause = s.clause AND m2.rel = s.rel
    AND cp2.tsg_number < s.p_num
)"""


def q_latest_earlier(pack, rels):
    return "WITH" + COMMON + pack_seed_ctes(pack, rels) + """,
cand AS (
  SELECT DISTINCT s.p_num AS p_num, s.spec AS spec, s.clause AS clause, s.rel AS rel,
         cp2.pack_number AS pack_number, cp2.tsg_meeting AS tsg_meeting,
         cp2.tsg_number AS tsg_number
  FROM seeds s
  JOIN mods m2 ON m2.spec = s.spec AND m2.clause = s.clause AND m2.rel = s.rel
  JOIN inpack ip2 ON ip2.doc_id = m2.doc_id
  JOIN cr_pack cp2 ON cp2.id = ip2.pack_id
  WHERE cp2.tsg_number < s.p_num
)
SELECT DISTINCT c.spec AS specification, c.clause AS clause, c.pack_number AS cr_pack,
       c.tsg_meeting AS tsg_meeting
FROM cand c
WHERE c.tsg_number = (
  SELECT MAX(c2.tsg_number) FROM cand c2
  WHERE c2.p_num = c.p_num AND c2.spec = c.spec AND c2.clause = c.clause
    AND c2.rel = c.rel
)"""


def q_others(doc, release):
    return "WITH" + COMMON + f""",
xdocs AS (
  SELECT id AS doc_id FROM document WHERE number = '{doc}' OR id = '{doc}'
),
xclauses AS (
  SELECT DISTINCT s.spec AS spec, s.clause AS clause, {rel('s.release')} AS rel
  FROM modsec ms
  JOIN section s ON s.id = ms.section_id
  WHERE ms.doc_id IN (SELECT doc_id FROM xdocs)
    AND {rel('s.release')} = {release}
)
SELECT DISTINCT x.clause AS clause, COALESCE(o.number, o.id) AS document,
       v.code AS disposition, v.wg_meeting AS wg_meeting, cp.pack_number AS cr_pack
FROM xclauses x
JOIN mods m ON m.spec = x.spec AND m.clause = x.clause AND m.rel = x.rel
JOIN document o ON o.id = m.doc_id
JOIN verified v ON v.doc_id = o.id
JOIN inpack ip ON ip.doc_id = o.id
JOIN cr_pack cp ON cp.id = ip.pack_id
WHERE o.id NOT IN (SELECT doc_id FROM xdocs)
  AND COALESCE(o.number, '') <> '{doc}'"""


F_FIRST = ["document", "specification", "clause"]
F_LATEST = ["specification", "clause", "cr_pack", "tsg_meeting"]
F_OTHERS = ["clause", "document", "disposition", "wg_meeting", "cr_pack"]


def build(item):
    q = item["question"]
    f = item["fields"]
    if f in (F_FIRST, F_LATEST):
        pack = re.search(r"CR pack (RP-\d+)", q).group(1)
        paren = re.search(r"targets \(([^)]*)\)", q).group(1)
        rels = [int(r) for r in re.findall(r"Rel-(\d+)", paren)]
        assert rels, item["id"]
        if f == F_FIRST:
            assert "changes first" in q, item["id"]
            return q_first(pack, rels)
        assert "latest earlier" in q, item["id"]
        return q_latest_earlier(pack, rels)
    if f == F_OTHERS:
        m = re.search(r"Change request (R3-\d+) \(CR \d+ to TS [\d.]+\) targets Rel-(\d+)", q)
        doc, release = m.group(1), int(m.group(2))
        assert f"in Rel-{release}" in q and f"other than {doc}" in q, item["id"]
        return q_others(doc, release)
    raise ValueError("unknown family: %s" % item["id"])


def main(src, dst):
    with open(src, encoding="utf-8") as fh:
        packet = json.load(fh)
    with open(dst, "w", encoding="utf-8") as out:
        for item in packet["items"]:
            sql = re.sub(r"[ \t]+\n", "\n", build(item)).strip()
            out.write(json.dumps({"id": item["id"], "sql": sql}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
