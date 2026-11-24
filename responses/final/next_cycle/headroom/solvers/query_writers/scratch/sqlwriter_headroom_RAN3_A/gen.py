"""Generate one SQLite query per RAN3 packet item from the schema and question text."""
import json
import re
import sys

PACKET = sys.argv[1]
OUT = sys.argv[2]


def norm_rel(expr):
    """Release value reduced to its digits ('Rel-16', 'R16', '16' -> '16')."""
    e = f"LOWER(TRIM({expr}))"
    for tok in ["release", "rel", "r", "-", " ", "_", "."]:
        e = f"REPLACE({e}, '{tok}', '')"
    return e


def q(s):
    return s.replace("'", "''")


STATUS = (
    "(LOWER(ds.evidence_status) LIKE '%verified%' "
    "AND LOWER(ds.evidence_status) NOT LIKE '%unverified%' "
    "AND LOWER(ds.evidence_status) NOT LIKE '%not%' "
    "AND LOWER(ds.evidence_status) NOT LIKE '%non%' "
    "AND (LOWER(ds.evidence_status) LIKE '%source%' OR LOWER(ds.evidence_status) = 'verified'))"
)
SCOPE = (
    "(LOWER(ds.scope) LIKE '%whole%' OR LOWER(ds.scope) LIKE '%entire%' "
    "OR LOWER(ds.scope) LIKE 'full%' "
    "OR LOWER(ds.scope) IN ('document', 'doc', 'tdoc', 'all'))"
)
WG3 = (
    "(UPPER(m.wg) LIKE 'RAN3%' OR UPPER(m.wg) LIKE 'R3%' OR UPPER(m.wg) LIKE '%WG3%' "
    "OR UPPER(REPLACE(REPLACE(m.wg, ' ', ''), '_', '')) LIKE '%RAN3%')"
)

COMMON = f"""dk AS (
  SELECT id AS doc_id, id AS k FROM document
  UNION SELECT id AS doc_id, number AS k FROM document WHERE number IS NOT NULL
),
pkk AS (
  SELECT id AS pack_id, id AS k FROM cr_pack
  UNION SELECT id AS pack_id, pack_number AS k FROM cr_pack WHERE pack_number IS NOT NULL
),
inpack AS (
  SELECT DISTINCT dk.doc_id, pkk.pack_id
  FROM (SELECT cr, pack_id FROM cr_in_pack UNION SELECT cr, pack_id FROM pack_member) x
  JOIN dk ON dk.k = x.cr
  JOIN pkk ON pkk.k = x.pack_id
),
modsec AS (
  SELECT DISTINCT dk.doc_id, s.spec, s.release, s.clause
  FROM (SELECT cr, section_id FROM cr_modifies_section UNION SELECT cr, section_id FROM section_modified_by) y
  JOIN dk ON dk.k = y.cr
  JOIN section s ON s.id = y.section_id
  JOIN document d ON d.id = dk.doc_id
  WHERE {norm_rel('s.release')} = {norm_rel('d.target_release')}
),
qdisp AS (
  SELECT DISTINCT dk.doc_id, ds.code, COALESCE(m.label, m.id) AS wg_meeting
  FROM disposition ds
  JOIN dk ON dk.k = ds.target
  JOIN resolution r ON r.id = ds.resolution_id
  JOIN meeting m ON m.id = r.meeting_id
  WHERE {STATUS} AND {SCOPE} AND {WG3}
)"""


def pack_base(pack):
    p = q(pack)
    return f"""target_pack AS (
  SELECT id AS pack_id, tsg_number FROM cr_pack WHERE pack_number = '{p}' OR id = '{p}'
),
base AS (
  SELECT DISTINCT ip.doc_id, tp.tsg_number AS p_num, ms.spec, ms.release, ms.clause
  FROM target_pack tp
  JOIN inpack ip ON ip.pack_id = tp.pack_id
  JOIN qdisp qd ON qd.doc_id = ip.doc_id
  JOIN modsec ms ON ms.doc_id = ip.doc_id
)"""


def sql_first(pack):
    return f"""WITH {COMMON},
{pack_base(pack)}
SELECT DISTINCT COALESCE(d.number, d.id) AS document, b.spec AS specification, b.clause AS clause
FROM base b
JOIN document d ON d.id = b.doc_id
WHERE NOT EXISTS (
  SELECT 1
  FROM modsec ms2
  JOIN inpack ip2 ON ip2.doc_id = ms2.doc_id
  JOIN cr_pack cp2 ON cp2.id = ip2.pack_id
  WHERE ms2.spec = b.spec AND ms2.clause = b.clause AND ms2.release = b.release
    AND cp2.tsg_number < b.p_num
)"""


def sql_latest_earlier(pack):
    return f"""WITH {COMMON},
{pack_base(pack)},
cand AS (
  SELECT DISTINCT b.spec, b.release, b.clause, cp2.id AS pack_id,
         COALESCE(cp2.pack_number, cp2.id) AS pack_number, cp2.tsg_meeting, cp2.tsg_number
  FROM (SELECT DISTINCT spec, release, clause, p_num FROM base) b
  JOIN modsec ms2 ON ms2.spec = b.spec AND ms2.clause = b.clause AND ms2.release = b.release
  JOIN inpack ip2 ON ip2.doc_id = ms2.doc_id
  JOIN cr_pack cp2 ON cp2.id = ip2.pack_id
  WHERE cp2.tsg_number < b.p_num
)
SELECT DISTINCT c.spec AS specification, c.clause AS clause, c.pack_number AS cr_pack, c.tsg_meeting AS tsg_meeting
FROM cand c
WHERE c.tsg_number = (
  SELECT MAX(c3.tsg_number) FROM cand c3
  WHERE c3.spec = c.spec AND c3.clause = c.clause AND c3.release = c.release
)"""


def sql_cr_peers(cr):
    c = q(cr)
    return f"""WITH {COMMON},
xdoc AS (
  SELECT id AS doc_id FROM document WHERE number = '{c}' OR id = '{c}'
),
xsec AS (
  SELECT DISTINCT ms.spec, ms.release, ms.clause
  FROM xdoc JOIN modsec ms ON ms.doc_id = xdoc.doc_id
)
SELECT DISTINCT xs.clause AS clause, COALESCE(d2.number, d2.id) AS document, qd.code AS disposition,
       qd.wg_meeting AS wg_meeting, COALESCE(cp.pack_number, cp.id) AS cr_pack
FROM xsec xs
JOIN modsec ms2 ON ms2.spec = xs.spec AND ms2.clause = xs.clause AND ms2.release = xs.release
JOIN document d2 ON d2.id = ms2.doc_id
JOIN qdisp qd ON qd.doc_id = ms2.doc_id
JOIN inpack ip ON ip.doc_id = ms2.doc_id
JOIN cr_pack cp ON cp.id = ip.pack_id
WHERE ms2.doc_id NOT IN (SELECT doc_id FROM xdoc)
  AND COALESCE(d2.number, '') <> '{c}'"""


FIELDS = {
    "first": ["document", "specification", "clause"],
    "latest": ["specification", "clause", "cr_pack", "tsg_meeting"],
    "peers": ["clause", "document", "disposition", "wg_meeting", "cr_pack"],
}


def main():
    with open(PACKET) as f:
        packet = json.load(f)
    lines = []
    for it in packet["items"]:
        qs = it["question"]
        if "Keep the clauses that the pack changes first" in qs:
            fam = "first"
            pack = re.search(r"CR pack (RP-\d+)", qs).group(1)
            sql = sql_first(pack)
        elif "latest earlier TSG RAN meeting" in qs:
            fam = "latest"
            pack = re.search(r"CR pack (RP-\d+)", qs).group(1)
            sql = sql_latest_earlier(pack)
        elif qs.startswith("Change request R3-"):
            fam = "peers"
            cr = re.match(r"Change request (R3-\d+)", qs).group(1)
            sql = sql_cr_peers(cr)
        else:
            raise SystemExit(f"unclassified item {it['id']}")
        if it["fields"] != FIELDS[fam]:
            raise SystemExit(f"field mismatch {it['id']}: {it['fields']}")
        lines.append(json.dumps({"id": it["id"], "sql": sql}, ensure_ascii=False))
    with open(OUT, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(len(lines))


if __name__ == "__main__":
    main()
