"""Generate one SQLite query per item of the RAN5 text2sql packet (run B)."""
import json
import re
import sys

PACKET = sys.argv[1]
OUT = sys.argv[2]


def norm_rel(x):
    """Reduce a release value such as 'Rel-18', 'Release 18' or '18' to '18'."""
    return (
        "replace(replace(replace(replace(replace(lower(trim(" + x + ")),"
        "'release',''),'rel',''),'r',''),'-',''),' ','')"
    )


def norm_tok(x):
    return "replace(replace(lower(trim(" + x + ")),'-','_'),' ','_')"


EVIDENCE_OK = (
    "(({e} LIKE '%source%verified%' OR {e} = 'verified') "
    "AND {e} NOT LIKE '%unverified%' AND {e} NOT LIKE '%not%' AND {e} NOT LIKE '%non%')"
).format(e=norm_tok("ds.evidence_status"))

SCOPE_OK = (
    "({s} LIKE '%whole%' OR {s} IN ('document','full','full_document','entire_document','doc'))"
).format(s=norm_tok("ds.scope"))

WG_OK = "upper(replace(replace(replace(mt.wg,' ',''),'_',''),'-','')) IN ('RAN5','R5','RANWG5','WG5')"

COMMON = f"""dk AS (
  SELECT id AS doc_id, id AS k FROM document
  UNION SELECT id, number FROM document WHERE number IS NOT NULL
),
pk AS (
  SELECT id AS pid, id AS k FROM cr_pack
  UNION SELECT id, pack_number FROM cr_pack WHERE pack_number IS NOT NULL
),
link AS (
  SELECT DISTINCT dk.doc_id, pk.pid
  FROM (SELECT cr, pack_id FROM cr_in_pack UNION SELECT cr, pack_id FROM pack_member) lr
  JOIN dk ON dk.k = lr.cr
  JOIN pk ON pk.k = lr.pack_id
),
mods AS (
  SELECT DISTINCT dk.doc_id, mr.section_id
  FROM (SELECT cr, section_id FROM cr_modifies_section UNION SELECT cr, section_id FROM section_modified_by) mr
  JOIN dk ON dk.k = mr.cr
),
qd AS (
  SELECT DISTINCT dk.doc_id, ds.code, mt.label AS wg_meeting
  FROM disposition ds
  JOIN dk ON dk.k = ds.target
  JOIN resolution r ON r.id = ds.resolution_id
  JOIN meeting mt ON mt.id = r.meeting_id
  WHERE {WG_OK} AND {EVIDENCE_OK} AND {SCOPE_OK}
),
dsec AS (
  SELECT DISTINCT mo.doc_id, s.spec, s.release, s.clause
  FROM mods mo
  JOIN document d ON d.id = mo.doc_id
  JOIN section s ON s.id = mo.section_id
  WHERE {norm_rel('s.release')} = {norm_rel('d.target_release')}
)"""


def base_ctes(pack):
    return f"""tp AS (
  SELECT id AS pid, tsg_number FROM cr_pack WHERE pack_number = '{pack}' OR id = '{pack}'
),
base AS (
  SELECT DISTINCT dsx.doc_id, dsx.spec, dsx.release, dsx.clause, tp.tsg_number
  FROM tp
  JOIN link l ON l.pid = tp.pid
  JOIN qd ON qd.doc_id = l.doc_id
  JOIN dsec dsx ON dsx.doc_id = l.doc_id
),
earlier AS (
  SELECT DISTINCT b.spec, b.release, b.clause, b.tsg_number AS t0,
         p2.id AS pid2, p2.pack_number, p2.tsg_meeting, p2.tsg_number AS t2
  FROM (SELECT DISTINCT spec, "release", clause, tsg_number FROM base) b
  JOIN dsec e ON e.spec = b.spec AND e.release = b.release AND e.clause = b.clause
  JOIN link l2 ON l2.doc_id = e.doc_id
  JOIN cr_pack p2 ON p2.id = l2.pid
  WHERE p2.tsg_number < b.tsg_number
)"""


def sql_first(pack):
    return f"""WITH {COMMON},
{base_ctes(pack)}
SELECT DISTINCT d.number AS document, b.spec AS specification, b.clause AS clause
FROM base b
JOIN document d ON d.id = b.doc_id
WHERE NOT EXISTS (
  SELECT 1 FROM earlier e
  WHERE e.spec = b.spec AND e.release = b.release AND e.clause = b.clause AND e.t0 = b.tsg_number
)"""


def sql_latest(pack):
    return f"""WITH {COMMON},
{base_ctes(pack)},
latest AS (
  SELECT spec, "release", clause, t0, MAX(t2) AS mt FROM earlier GROUP BY spec, "release", clause, t0
)
SELECT DISTINCT e.spec AS specification, e.clause AS clause, e.pack_number AS cr_pack, e.tsg_meeting AS tsg_meeting
FROM earlier e
JOIN latest lt ON lt.spec = e.spec AND lt.release = e.release AND lt.clause = e.clause
              AND lt.t0 = e.t0 AND e.t2 = lt.mt"""


def sql_others(cr, rel):
    relnum = re.sub(r"\D", "", rel)
    return f"""WITH {COMMON},
x AS (
  SELECT id AS xid FROM document
  WHERE (number = '{cr}' OR id = '{cr}') AND {norm_rel('target_release')} = '{relnum}'
),
xs AS (
  SELECT DISTINCT dsx.spec, dsx.release, dsx.clause
  FROM x JOIN dsec dsx ON dsx.doc_id = x.xid
)
SELECT DISTINCT xs.clause AS clause, d2.number AS document, q.code AS disposition,
       q.wg_meeting AS wg_meeting, p.pack_number AS cr_pack
FROM xs
JOIN dsec o ON o.spec = xs.spec AND o.release = xs.release AND o.clause = xs.clause
JOIN document d2 ON d2.id = o.doc_id
JOIN qd q ON q.doc_id = d2.id
JOIN link l ON l.doc_id = d2.id
JOIN cr_pack p ON p.id = l.pid
WHERE d2.id NOT IN (SELECT xid FROM x)
  AND COALESCE(d2.number, '') <> '{cr}' AND d2.id <> '{cr}'"""


FIELDS = {
    "first": ["document", "specification", "clause"],
    "latest": ["specification", "clause", "cr_pack", "tsg_meeting"],
    "others": ["clause", "document", "disposition", "wg_meeting", "cr_pack"],
}


def main():
    with open(PACKET, encoding="utf-8") as f:
        packet = json.load(f)
    rows = []
    for it in packet["items"]:
        q = it["question"]
        if "Keep the clauses that the pack changes first" in q:
            fam = "first"
            pack = re.search(r"CR pack (RP-\d+)", q).group(1)
            sql = sql_first(pack)
        elif "latest earlier TSG RAN meeting" in q:
            fam = "latest"
            pack = re.search(r"CR pack (RP-\d+)", q).group(1)
            sql = sql_latest(pack)
        elif q.startswith("Change request R5-"):
            fam = "others"
            m = re.match(r"Change request (R5-\d+) \(CR \S+ to TS \S+\) targets (Rel-\d+)\.", q)
            sql = sql_others(m.group(1), m.group(2))
        else:
            raise SystemExit("unknown family: " + it["id"])
        if it["fields"] != FIELDS[fam]:
            raise SystemExit("field mismatch: " + it["id"])
        rows.append({"id": it["id"], "sql": sql})
    with open(OUT, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(len(rows))


if __name__ == "__main__":
    main()
