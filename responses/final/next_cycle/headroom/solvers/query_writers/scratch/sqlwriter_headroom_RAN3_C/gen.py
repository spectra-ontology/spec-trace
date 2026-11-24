"""Generate one SQLite query per item of the RAN3 text-to-SQL packet.

Three question families are recognised from the question text:
  first   : clauses that a given CR pack changes first
  latest  : packs of the latest earlier TSG RAN meeting touching the same clause
  others  : other qualifying CRs that modify the clauses of a given CR
"""
import json
import re
import sys

PACKET = sys.argv[1]
OUT = sys.argv[2]


def nr(expr):
    """Release normaliser: 'Rel-16', 'Release 16', 'rel16', '16' -> '16'."""
    return (
        "REPLACE(REPLACE(REPLACE(REPLACE(LOWER(TRIM({e})),'release',''),'rel',''),'-',''),' ','')"
    ).format(e=expr)


def norm_tok(expr):
    return "REPLACE(REPLACE(LOWER(TRIM({e})),'-','_'),' ','_')".format(e=expr)


def qual_pred(x, m):
    """Source-verified, whole-document, RAN3 disposition predicates."""
    ev = (
        "({x}.evidence_status LIKE '%source%' AND {x}.evidence_status LIKE '%verif%' "
        "AND {x}.evidence_status NOT LIKE '%unverif%' AND {x}.evidence_status NOT LIKE '%not%')"
    ).format(x=x)
    sc = (
        "({x}.scope LIKE '%whole%' OR {x}.scope LIKE '%entire%' OR {n} IN "
        "('document','doc','tdoc','full','full_document','all'))"
    ).format(x=x, n=norm_tok(x + ".scope"))
    wg = (
        "UPPER(REPLACE(REPLACE(REPLACE(TRIM({m}.wg),' ',''),'_',''),'-','')) IN "
        "('RAN3','R3','RANWG3','TSGRANWG3','TSGRAN3','WG3')"
    ).format(m=m)
    return "{} AND {} AND {}".format(ev, sc, wg)


def qual_exists(doc):
    return (
        "EXISTS (SELECT 1 FROM disposition x JOIN resolution r ON r.id = x.resolution_id "
        "JOIN meeting m ON m.id = r.meeting_id WHERE x.target IN ({d}.id, {d}.number) AND {q})"
    ).format(d=doc, q=qual_pred("x", "m"))


LINK = (
    "link AS (SELECT cr, pack_id FROM cr_in_pack UNION SELECT cr, pack_id FROM pack_member), "
    "mods AS (SELECT cr, section_id FROM cr_modifies_section UNION SELECT cr, section_id FROM section_modified_by)"
)


def lit(s):
    return "'" + s.replace("'", "''") + "'"


def base_cte(pack):
    return (
        "tp AS (SELECT id, tsg_number FROM cr_pack WHERE pack_number = {p} OR id = {p}), "
        "base AS (SELECT DISTINCT d.id AS doc_id, d.number AS doc_number, s.spec AS spec, s.clause AS clause, "
        "{rd} AS rel, tp.tsg_number AS ref_num "
        "FROM tp JOIN link l ON l.pack_id = tp.id JOIN document d ON d.id = l.cr "
        "JOIN mods mo ON mo.cr = d.id JOIN section s ON s.id = mo.section_id "
        "WHERE {rs} = {rd} AND {q})"
    ).format(p=lit(pack), rd=nr("d.target_release"), rs=nr("s.release"), q=qual_exists("d"))


def earlier_join(alias_b):
    """Join from a (spec, clause, rel, ref_num) row to CR packs of earlier TSG RAN meetings
    that carried a CR of that release modifying the same clause."""
    return (
        "JOIN section s2 ON s2.spec = {b}.spec AND s2.clause = {b}.clause "
        "JOIN mods mo2 ON mo2.section_id = s2.id "
        "JOIN document d2 ON d2.id = mo2.cr "
        "JOIN link l2 ON l2.cr = d2.id "
        "JOIN cr_pack cp2 ON cp2.id = l2.pack_id "
        "WHERE {rs2} = {b}.rel AND {rd2} = {b}.rel AND cp2.tsg_number < {b}.ref_num"
    ).format(b=alias_b, rs2=nr("s2.release"), rd2=nr("d2.target_release"))


def sql_first(pack):
    return (
        "WITH {link}, {base}, "
        "earlier AS (SELECT DISTINCT b.spec, b.clause, b.rel, b.ref_num "
        "FROM (SELECT DISTINCT spec, clause, rel, ref_num FROM base) b {ej}) "
        "SELECT DISTINCT b.doc_number AS document, b.spec AS specification, b.clause AS clause "
        "FROM base b WHERE NOT EXISTS (SELECT 1 FROM earlier e WHERE e.spec = b.spec AND e.clause = b.clause "
        "AND e.rel = b.rel AND e.ref_num = b.ref_num)"
    ).format(link=LINK, base=base_cte(pack), ej=earlier_join("b"))


def sql_latest(pack):
    return (
        "WITH {link}, {base}, "
        "cand AS (SELECT DISTINCT b.spec AS spec, b.clause AS clause, b.rel AS rel, b.ref_num AS ref_num, "
        "cp2.pack_number AS pack_number, cp2.tsg_meeting AS tsg_meeting, cp2.tsg_number AS tsg_number "
        "FROM (SELECT DISTINCT spec, clause, rel, ref_num FROM base) b {ej}) "
        "SELECT DISTINCT c.spec AS specification, c.clause AS clause, c.pack_number AS cr_pack, "
        "c.tsg_meeting AS tsg_meeting FROM cand c "
        "WHERE c.tsg_number = (SELECT MAX(c2.tsg_number) FROM cand c2 WHERE c2.spec = c.spec "
        "AND c2.clause = c.clause AND c2.rel = c.rel AND c2.ref_num = c.ref_num)"
    ).format(link=LINK, base=base_cte(pack), ej=earlier_join("b"))


def sql_others(doc, rel):
    relv = re.sub(r"[^0-9]", "", rel)
    return (
        "WITH {link}, "
        "src AS (SELECT id FROM document WHERE number = {d} OR id = {d}), "
        "src_sec AS (SELECT DISTINCT s.spec AS spec, s.clause AS clause FROM src "
        "JOIN mods mo ON mo.cr = src.id JOIN section s ON s.id = mo.section_id WHERE {rs} = {rv}) "
        "SELECT DISTINCT ss.clause AS clause, d2.number AS document, x.code AS disposition, "
        "m.label AS wg_meeting, cp.pack_number AS cr_pack "
        "FROM src_sec ss "
        "JOIN section s2 ON s2.spec = ss.spec AND s2.clause = ss.clause "
        "JOIN mods mo2 ON mo2.section_id = s2.id "
        "JOIN document d2 ON d2.id = mo2.cr "
        "JOIN disposition x ON x.target IN (d2.id, d2.number) "
        "JOIN resolution r ON r.id = x.resolution_id "
        "JOIN meeting m ON m.id = r.meeting_id "
        "JOIN link l ON l.cr = d2.id "
        "JOIN cr_pack cp ON cp.id = l.pack_id "
        "WHERE {rs2} = {rv} AND {rd2} = {rv} "
        "AND d2.id NOT IN (SELECT id FROM src) AND COALESCE(d2.number, '') <> {d} "
        "AND {q}"
    ).format(
        link=LINK,
        d=lit(doc),
        rs=nr("s.release"),
        rs2=nr("s2.release"),
        rd2=nr("d2.target_release"),
        rv=lit(relv),
        q=qual_pred("x", "m"),
    )


def main():
    with open(PACKET, encoding="utf-8") as f:
        packet = json.load(f)
    lines = []
    for it in packet["items"]:
        q = it["question"]
        fields = it["fields"]
        if "Keep the clauses that the pack changes first" in q:
            pack = re.search(r"CR pack (RP-\d+)", q).group(1)
            assert fields == ["document", "specification", "clause"], it["id"]
            sql = sql_first(pack)
        elif "latest earlier TSG RAN meeting" in q:
            pack = re.search(r"CR pack (RP-\d+)", q).group(1)
            assert fields == ["specification", "clause", "cr_pack", "tsg_meeting"], it["id"]
            sql = sql_latest(pack)
        elif q.startswith("Change request "):
            m = re.match(r"Change request (R3-\d+) \(CR \d+ to TS [\d.]+\) targets (Rel-\d+)\.", q)
            assert m, it["id"]
            assert fields == ["clause", "document", "disposition", "wg_meeting", "cr_pack"], it["id"]
            sql = sql_others(m.group(1), m.group(2))
        else:
            raise SystemExit("unrecognised family: " + it["id"])
        lines.append(json.dumps({"id": it["id"], "sql": sql}, ensure_ascii=False))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(len(lines))


if __name__ == "__main__":
    main()
