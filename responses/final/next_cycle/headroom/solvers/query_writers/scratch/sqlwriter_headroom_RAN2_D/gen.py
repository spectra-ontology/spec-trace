"""Generate one SQLite query per packet item for the RAN2 text-to-SQL packet.

Usage: python gen.py <packet.json> <out.jsonl>
"""
import json
import re
import sys


def norm(x):
    """Lower-case and strip separators so 'SOURCE_VERIFIED' and 'source-verified' compare equal."""
    return (
        "replace(replace(replace(replace(lower(trim(" + x + ")),'-',''),'_',''),' ',''),'#','')"
    )


def rel(x):
    """Reduce a release label such as 'Rel-16' or 'R16' to its number text '16'."""
    return "ltrim(lower(trim(" + x + ")),'release-_ v')"


def q(s):
    return "'" + s.replace("'", "''") + "'"


COMMON_CTES = (
    "mods AS (SELECT cr, section_id FROM cr_modifies_section "
    "UNION SELECT cr, section_id FROM section_modified_by), "
    "packs AS (SELECT cr, pack_id FROM cr_in_pack "
    "UNION SELECT cr, pack_id FROM pack_member)"
)


def disp_filter(alias_dp, alias_m):
    return (
        f"{norm(alias_dp + '.evidence_status')} = 'sourceverified' "
        f"AND {norm(alias_dp + '.scope')} IN "
        "('wholedocument','document','wholedoc','entiredocument','fulldocument') "
        f"AND {norm(alias_m + '.wg')} IN ('ran2','r2','ranwg2','tsgranwg2','tsgr2','wg2')"
    )


def disp_exists(doc_alias):
    return (
        "EXISTS (SELECT 1 FROM disposition dq "
        "JOIN resolution rq ON rq.id = dq.resolution_id "
        "JOIN meeting mq ON mq.id = rq.meeting_id "
        f"WHERE dq.target = {doc_alias}.id AND {disp_filter('dq', 'mq')})"
    )


def rel_list(rels):
    return "(" + ",".join(q(r) for r in rels) + ")"


def family_a(tdoc, release):
    r = q(release)
    return (
        f"WITH {COMMON_CTES}, "
        f"anchor AS (SELECT id FROM document WHERE number = {q(tdoc)} OR id = {q(tdoc)}) "
        "SELECT DISTINCT s1.clause AS clause, COALESCE(o.number, o.id) AS document, "
        "dp.code AS disposition, m.label AS wg_meeting, cp.pack_number AS cr_pack "
        "FROM anchor a "
        "JOIN mods ma ON ma.cr = a.id "
        f"JOIN section s1 ON s1.id = ma.section_id AND {rel('s1.release')} = {r} "
        "JOIN section s2 ON s2.spec = s1.spec AND s2.release = s1.release AND s2.clause = s1.clause "
        "JOIN mods mo ON mo.section_id = s2.id "
        f"JOIN document o ON o.id = mo.cr AND {rel('o.target_release')} = {r} "
        "JOIN disposition dp ON dp.target = o.id "
        "JOIN resolution rs ON rs.id = dp.resolution_id "
        "JOIN meeting m ON m.id = rs.meeting_id "
        "JOIN packs p ON p.cr = o.id "
        "JOIN cr_pack cp ON cp.id = p.pack_id "
        f"WHERE o.id NOT IN (SELECT id FROM anchor) "
        f"AND COALESCE(o.number, '') <> {q(tdoc)} AND o.id <> {q(tdoc)} "
        f"AND {disp_filter('dp', 'm')}"
    )


def base_cte(pack, rels):
    return (
        f"pk AS (SELECT id, tsg_number FROM cr_pack WHERE pack_number = {q(pack)} OR id = {q(pack)}), "
        "base AS (SELECT DISTINCT COALESCE(c.number, c.id) AS document, s.spec AS spec, "
        "s.release AS release, s.clause AS clause "
        "FROM pk JOIN packs p ON p.pack_id = pk.id "
        "JOIN document c ON c.id = p.cr "
        "JOIN mods mc ON mc.cr = c.id "
        f"JOIN section s ON s.id = mc.section_id AND {rel('s.release')} = {rel('c.target_release')} "
        f"WHERE {rel('c.target_release')} IN {rel_list(rels)} AND {disp_exists('c')})"
    )


def earlier_pack_join(b):
    """Packs at a TSG RAN meeting before the given pack that carry a CR of the clause's release
    modifying the same clause."""
    return (
        f"JOIN section s2 ON s2.spec = {b}.spec AND s2.release = {b}.release AND s2.clause = {b}.clause "
        "JOIN mods m2 ON m2.section_id = s2.id "
        f"JOIN document c2 ON c2.id = m2.cr AND {rel('c2.target_release')} = {rel(b + '.release')} "
        "JOIN packs p2 ON p2.cr = c2.id "
        "JOIN cr_pack cp2 ON cp2.id = p2.pack_id "
        "JOIN pk ON cp2.tsg_number < pk.tsg_number"
    )


def family_b(pack, rels):
    return (
        f"WITH {COMMON_CTES}, {base_cte(pack, rels)} "
        "SELECT DISTINCT b.document AS document, b.spec AS specification, b.clause AS clause "
        "FROM base b "
        f"WHERE NOT EXISTS (SELECT 1 FROM (SELECT 1) z {earlier_pack_join('b')})"
    )


def family_c(pack, rels):
    return (
        f"WITH {COMMON_CTES}, {base_cte(pack, rels)}, "
        "clauses AS (SELECT DISTINCT spec, release, clause FROM base), "
        "earlier AS (SELECT b.spec AS spec, b.release AS release, b.clause AS clause, "
        "cp2.pack_number AS pack_number, cp2.tsg_meeting AS tsg_meeting, cp2.tsg_number AS tsg_number "
        f"FROM clauses b {earlier_pack_join('b')}) "
        "SELECT DISTINCT e.spec AS specification, e.clause AS clause, "
        "e.pack_number AS cr_pack, e.tsg_meeting AS tsg_meeting "
        "FROM earlier e "
        "WHERE e.tsg_number = (SELECT MAX(e2.tsg_number) FROM earlier e2 "
        "WHERE e2.spec = e.spec AND e2.release = e.release AND e2.clause = e.clause)"
    )


FIELDS_A = ["clause", "document", "disposition", "wg_meeting", "cr_pack"]
FIELDS_B = ["document", "specification", "clause"]
FIELDS_C = ["specification", "clause", "cr_pack", "tsg_meeting"]


def build(item):
    qt = item["question"]
    m = re.match(r"Change request (R2-\d+) \(CR \S+ to TS \S+\) targets Rel-(\d+)\.", qt)
    if m:
        assert item["fields"] == FIELDS_A, item["id"]
        return family_a(m.group(1), m.group(2))
    pm = re.match(r"TSG RAN CR pack (RP-\d+) carries change requests from RAN2\.", qt)
    assert pm, item["id"]
    paren = re.search(r"the release that change request targets \(([^)]*)\)", qt)
    assert paren, item["id"]
    rels = re.findall(r"Rel-(\d+)", paren.group(1))
    assert rels, item["id"]
    if "Keep the clauses that the pack changes first" in qt:
        assert item["fields"] == FIELDS_B, item["id"]
        return family_b(pm.group(1), rels)
    if "latest earlier TSG RAN meeting" in qt:
        assert item["fields"] == FIELDS_C, item["id"]
        return family_c(pm.group(1), rels)
    raise AssertionError("unrecognized family: " + item["id"])


def main():
    packet_path, out_path = sys.argv[1], sys.argv[2]
    with open(packet_path, encoding="utf-8") as f:
        packet = json.load(f)
    with open(out_path, "w", encoding="utf-8") as out:
        for item in packet["items"]:
            out.write(json.dumps({"id": item["id"], "sql": build(item)}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
