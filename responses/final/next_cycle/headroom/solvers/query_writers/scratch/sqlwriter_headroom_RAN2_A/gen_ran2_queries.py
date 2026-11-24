"""Generate one SQLite query per item of the RAN2 text-to-SQL packet.

Reads only the packet given as argv[1] and writes JSON lines to argv[2].
Three question families are recognised from the question text:
  pair  : clause neighbours of one named change request
  first : clauses that a CR pack changes first
  prev  : CR packs of the latest earlier TSG RAN meeting per clause
"""
import json
import re
import sys


def norm_rel(expr):
    """Release text to its bare number: 'Rel-16', 'Release 16', 'R16' -> '16'."""
    e = f"lower(trim({expr}))"
    for old in ("release", "rel", "-", "_", " ", "."):
        e = f"replace({e}, '{old}', '')"
    return f"ltrim({e}, 'r')"


def squash(expr, case="lower"):
    e = f"{case}(trim({expr}))"
    for old in (" ", "_", "-"):
        e = f"replace({e}, '{old}', '')"
    return e


def lit(s):
    return "'" + s.replace("'", "''") + "'"


STATUS_OK = (
    f"({squash('dp.evidence_status')} IN ('sourceverified','verifiedsource',"
    f"'verifiedagainstsource','verifiedfromsource') "
    f"OR {squash('dp.evidence_status')} LIKE 'sourceverified%')"
)
SCOPE_OK = (
    f"({squash('dp.scope')} IN ('document','wholedocument','whole','fulldocument',"
    f"'full','entiredocument','entire','doc','wholedoc','all','tdoc','wholetdoc') "
    f"OR {squash('dp.scope')} LIKE '%whole%')"
)
WG_OK = (
    f"({squash('m.wg', 'upper')} IN ('RAN2','R2','RANWG2','TSGRANWG2','WG2') "
    f"OR {squash('m.label', 'upper')} LIKE 'RAN2#%' "
    f"OR {squash('m.label', 'upper')} LIKE 'RANWG2#%')"
)

COMMON = f"""dk AS (
  SELECT id AS k, id AS doc_id FROM document WHERE id IS NOT NULL
  UNION SELECT number AS k, id AS doc_id FROM document WHERE number IS NOT NULL
),
pk AS (
  SELECT id AS k, id AS pack_id FROM cr_pack WHERE id IS NOT NULL
  UNION SELECT pack_number AS k, id AS pack_id FROM cr_pack WHERE pack_number IS NOT NULL
),
modrel AS (
  SELECT cr, section_id FROM cr_modifies_section
  UNION SELECT cr, section_id FROM section_modified_by
),
memrel AS (
  SELECT cr, pack_id FROM cr_in_pack
  UNION SELECT cr, pack_id FROM pack_member
),
docr AS (
  SELECT id, number, {norm_rel('target_release')} AS trn FROM document
),
dmod AS (
  SELECT DISTINCT dk.doc_id, s.spec, s.clause, {norm_rel('s.release')} AS rn
  FROM modrel r JOIN dk ON dk.k = r.cr JOIN section s ON s.id = r.section_id
),
dpack AS (
  SELECT DISTINCT dk.doc_id, cp.id AS pack_id, cp.pack_number, cp.tsg_meeting, cp.tsg_number
  FROM memrel r JOIN dk ON dk.k = r.cr JOIN pk ON pk.k = r.pack_id
  JOIN cr_pack cp ON cp.id = pk.pack_id
),
disp AS (
  SELECT DISTINCT dk.doc_id, dp.code, COALESCE(m.label, m.id) AS wg_meeting
  FROM disposition dp JOIN dk ON dk.k = dp.target
  JOIN resolution rs ON rs.id = dp.resolution_id
  JOIN meeting m ON m.id = rs.meeting_id
  WHERE {STATUS_OK} AND {SCOPE_OK} AND {WG_OK}
)"""


def rel_num(rel):
    return re.fullmatch(r"Rel-(\d+)", rel).group(1)


def q_pair(doc_number, rel):
    rn = lit(rel_num(rel))
    dn = lit(doc_number)
    return f"""WITH {COMMON},
src AS (
  SELECT DISTINCT m.spec, m.clause, m.rn
  FROM docr d JOIN dmod m ON m.doc_id = d.id
  WHERE d.number = {dn} AND m.rn = {rn}
)
SELECT DISTINCT src.clause AS clause, d2.number AS document, ds.code AS disposition,
  ds.wg_meeting AS wg_meeting, pp.pack_number AS cr_pack
FROM src
JOIN dmod m2 ON m2.spec = src.spec AND m2.clause = src.clause AND m2.rn = src.rn
JOIN docr d2 ON d2.id = m2.doc_id
JOIN disp ds ON ds.doc_id = d2.id
JOIN dpack pp ON pp.doc_id = d2.id
WHERE d2.number <> {dn} AND d2.trn = {rn}"""


def base_cte(pack, rels):
    rl = ",".join(lit(rel_num(r)) for r in rels)
    return f"""p AS (
  SELECT id, tsg_number FROM cr_pack WHERE pack_number = {lit(pack)}
),
ptsg AS (
  SELECT MIN(tsg_number) AS t FROM p
),
base AS (
  SELECT DISTINCT d.id AS doc_id, d.number, m.spec, m.clause, m.rn
  FROM p JOIN dpack pp ON pp.pack_id = p.id
  JOIN docr d ON d.id = pp.doc_id
  JOIN dmod m ON m.doc_id = d.id AND m.rn = d.trn
  WHERE d.id IN (SELECT doc_id FROM disp) AND d.trn IN ({rl})
)"""


def q_first(pack, rels):
    return f"""WITH {COMMON},
{base_cte(pack, rels)}
SELECT DISTINCT b.number AS document, b.spec AS specification, b.clause AS clause
FROM base b
WHERE NOT EXISTS (
  SELECT 1 FROM dmod m2
  JOIN docr d2 ON d2.id = m2.doc_id
  JOIN dpack pp2 ON pp2.doc_id = d2.id
  WHERE m2.spec = b.spec AND m2.clause = b.clause AND m2.rn = b.rn
    AND d2.trn = b.rn
    AND pp2.tsg_number < (SELECT t FROM ptsg)
)"""


def q_prev(pack, rels):
    return f"""WITH {COMMON},
{base_cte(pack, rels)},
bc AS (
  SELECT DISTINCT spec, clause, rn FROM base
),
earlier AS (
  SELECT DISTINCT bc.spec, bc.clause, bc.rn, pp2.pack_number, pp2.tsg_meeting, pp2.tsg_number
  FROM bc
  JOIN dmod m2 ON m2.spec = bc.spec AND m2.clause = bc.clause AND m2.rn = bc.rn
  JOIN docr d2 ON d2.id = m2.doc_id AND d2.trn = bc.rn
  JOIN dpack pp2 ON pp2.doc_id = d2.id
  WHERE pp2.tsg_number < (SELECT t FROM ptsg)
)
SELECT DISTINCT e.spec AS specification, e.clause AS clause, e.pack_number AS cr_pack,
  e.tsg_meeting AS tsg_meeting
FROM earlier e
WHERE e.tsg_number = (
  SELECT MAX(e2.tsg_number) FROM earlier e2
  WHERE e2.spec = e.spec AND e2.clause = e.clause AND e2.rn = e.rn
)"""


FIELDS = {
    "pair": ["clause", "document", "disposition", "wg_meeting", "cr_pack"],
    "first": ["document", "specification", "clause"],
    "prev": ["specification", "clause", "cr_pack", "tsg_meeting"],
}


def build(item):
    q = item["question"]
    m = re.match(r"Change request (R2-\d+) \(CR \w+ to TS [\d.]+\) targets (Rel-\d+)\.", q)
    if m:
        fam, sql = "pair", q_pair(m.group(1), m.group(2))
    else:
        mp = re.match(r"TSG RAN CR pack (RP-\d+) carries", q)
        mr = re.search(r"the release that change request targets \(([^)]*)\)", q)
        if not (mp and mr):
            raise SystemExit(f"unrecognised question: {item['id']}")
        rels = re.findall(r"Rel-\d+", mr.group(1))
        if "Keep the clauses that the pack changes first" in q:
            fam, sql = "first", q_first(mp.group(1), rels)
        elif "latest earlier TSG RAN meeting" in q:
            fam, sql = "prev", q_prev(mp.group(1), rels)
        else:
            raise SystemExit(f"unrecognised family: {item['id']}")
    if item["fields"] != FIELDS[fam]:
        raise SystemExit(f"field mismatch for {item['id']}: {item['fields']}")
    return fam, sql


def main():
    packet = json.load(open(sys.argv[1], encoding="utf-8"))
    counts = {}
    with open(sys.argv[2], "w", encoding="utf-8") as out:
        for item in packet["items"]:
            fam, sql = build(item)
            counts[fam] = counts.get(fam, 0) + 1
            out.write(json.dumps({"id": item["id"], "sql": sql}, ensure_ascii=False) + "\n")
    print(counts)


if __name__ == "__main__":
    main()
