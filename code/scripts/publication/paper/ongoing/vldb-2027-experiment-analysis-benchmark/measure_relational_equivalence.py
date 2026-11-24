"""추적 사슬 문항의 정답이 관계형 테이블과 SQL 만으로 재현되는지 센다 (모델 호출 없음).

`export_chain_records_sqlite.py` 가 인스턴스 JSON-LD 에서 내보낸 작업반별 SQLite 파일에 문항 종류별 참조 SQL 을
실행하고, 결과 행 집합이 문항의 gold 와 완전히 같은 문항 수를 센다. 테이블은 기록을 거르지 않고 실었으므로
"원문 확인·문서 전체 처분", "CR 의 대상 release 가 절의 release 와 같음" 같은 조건은 모두 SQL 문 안에 있다.

참조 SQL 은 두 벌이다. `cr_side` 는 생성기가 따라간 CR 쪽 기록(`belongsToCRPack`·`modifiesSection`)을,
`container_side` 는 반대쪽 기록(`CRPack.hasCR`·`Section.modifiedByCR`)을 쓴다. `pack_origin` 은 묶음이 출발점이라
생성기가 묶음 쪽 기록을 쓰므로 두 벌의 방향이 다른 종류와 반대다.

행 집합이 다르면 SQL 을 고치지 않고 문항별로 gold 에만 있는 행과 SQL 에만 있는 행을 그대로 적는다.
비교가 조건에 민감한지는 대조 실행으로 본다. `cr_side` SQL 에서 조건 하나를 뺀 질의(원문 확인·문서 전체 조건,
절과 CR 의 release 일치 조건)를 같은 문항에 실행해 gold 와 달라지는 문항 수를 센다.
조인 수와 테이블 수는 SQL 문에서 센다(`JOIN` 낱말 수, 재귀 공통 테이블식 안의 것 포함 / 서로 다른 기본 테이블 수).

절 단위 종류(`clause_neighbours`·`first_change`·`previous_pack`)의 참조 SQL 과 대조 질의는 `CLAUSE_SET_SQL`·
`CLAUSE_SET_CONTROLS` 에 따로 둔다. 그 종류의 문항이 입력에 있을 때만 실행하고 보고에 싣는다. 두 벌의 방향은
`cr_side` 가 CR 쪽 기록, `container_side` 가 반대쪽 기록이다. 총회 회의의 앞뒤는 `cr_pack.tsg_number` 로 정한다.
대조 질의는 바꿀 문자열과 바꿔 넣을 문자열의 쌍이다(빈 문자열이면 그 조건을 지운다).

사용: python3 measure_relational_equivalence.py --db-dir <dir> --items <jsonl> [<jsonl> ...] --out <json>
저장소 루트에서 실행한다.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sqlite3
from pathlib import Path

VERIFIED = "d.evidence_status = 'source_verified' AND d.scope = 'whole_target'"
SQL = {
    "pack_lookup": """
        SELECT DISTINCT p.pack_number, p.tsg_meeting
        FROM {member} m JOIN cr_pack p ON p.id = m.pack_id
        WHERE m.cr = :anchor""",
    "disposition_pack": f"""
        SELECT DISTINCT d.code, g.label, p.pack_number, p.tsg_meeting
        FROM disposition d
        JOIN resolution r ON r.id = d.resolution_id JOIN meeting g ON g.id = r.meeting_id
        JOIN {{member}} m ON m.cr = d.target JOIN cr_pack p ON p.id = m.pack_id
        WHERE d.target = :anchor AND {VERIFIED}""",
    "full_chain": f"""
        SELECT DISTINCT d.code, g.label, p.pack_number, p.tsg_meeting, s.clause
        FROM disposition d
        JOIN resolution r ON r.id = d.resolution_id JOIN meeting g ON g.id = r.meeting_id
        JOIN {{member}} m ON m.cr = d.target JOIN cr_pack p ON p.id = m.pack_id
        JOIN {{change}} c ON c.cr = d.target JOIN section s ON s.id = c.section_id
        WHERE d.target = :anchor AND {VERIFIED} AND s.clause IS NOT NULL""",
    "revision_chain": f"""
        WITH RECURSIVE later(id) AS (
            SELECT later FROM revision WHERE earlier = :anchor
            UNION SELECT v.later FROM revision v JOIN later l ON v.earlier = l.id)
        SELECT DISTINCT doc.number, d.code, p.pack_number
        FROM later
        JOIN document doc ON doc.id = later.id
        JOIN disposition d ON d.target = later.id JOIN resolution r ON r.id = d.resolution_id
        JOIN {{member}} m ON m.cr = later.id JOIN cr_pack p ON p.id = m.pack_id
        WHERE {VERIFIED}""",
    "clause_history": f"""
        SELECT DISTINCT doc.number, d.code, g.label, p.pack_number
        FROM {{change}} c
        JOIN section s ON s.id = c.section_id JOIN document doc ON doc.id = c.cr
        JOIN disposition d ON d.target = c.cr
        JOIN resolution r ON r.id = d.resolution_id JOIN meeting g ON g.id = r.meeting_id
        JOIN {{member}} m ON m.cr = c.cr JOIN cr_pack p ON p.id = m.pack_id
        WHERE c.section_id = :anchor AND doc.target_release = s.release AND {VERIFIED}""",
    "pack_origin": f"""
        SELECT DISTINCT doc.number, d.code, g.label
        FROM {{origin}} m
        JOIN document doc ON doc.id = m.cr JOIN disposition d ON d.target = m.cr
        JOIN resolution r ON r.id = d.resolution_id JOIN meeting g ON g.id = r.meeting_id
        WHERE m.pack_id = :anchor AND {VERIFIED}""",
}
SQL["pack_lookup_empty"] = SQL["pack_lookup"]
# 절 단위 종류의 참조 SQL. 위 SQL 을 읽는 다른 스크립트의 집계가 바뀌지 않도록 따로 둔다.
# 묶음이 대상인 두 종류는 규격 열을 내어, 여러 규격에 걸친 묶음에서 같은 절 번호가 다른 행으로 남는다.
CLAUSE_SET_SQL = {
    "clause_neighbours": f"""
        SELECT DISTINCT s.clause, o.number, d.code, g.label, p.pack_number
        FROM {{change}} cx
        JOIN document x ON x.id = cx.cr JOIN section s ON s.id = cx.section_id
        JOIN {{change}} co ON co.section_id = s.id JOIN document o ON o.id = co.cr
        JOIN disposition d ON d.target = o.id
        JOIN resolution r ON r.id = d.resolution_id JOIN meeting g ON g.id = r.meeting_id
        JOIN {{member}} m ON m.cr = o.id JOIN cr_pack p ON p.id = m.pack_id
        WHERE cx.cr = :anchor AND o.id <> :anchor AND x.target_release = s.release
            AND o.target_release = s.release AND {VERIFIED}""",
    "first_change": f"""
        SELECT DISTINCT doc.number, s.spec, s.clause
        FROM {{member}} m JOIN cr_pack p ON p.id = m.pack_id JOIN document doc ON doc.id = m.cr
        JOIN disposition d ON d.target = m.cr JOIN resolution r ON r.id = d.resolution_id
        JOIN {{change}} c ON c.cr = m.cr JOIN section s ON s.id = c.section_id
        WHERE m.pack_id = :anchor AND doc.target_release = s.release AND {VERIFIED}
            AND NOT EXISTS (
                SELECT 1 FROM {{change}} c2 JOIN document d2 ON d2.id = c2.cr
                JOIN {{member}} m2 ON m2.cr = c2.cr JOIN cr_pack p2 ON p2.id = m2.pack_id
                WHERE c2.section_id = s.id AND d2.target_release = s.release
                    AND p2.tsg_number < p.tsg_number)""",
    "previous_pack": f"""
        WITH touched AS (
            SELECT DISTINCT s.id AS sid, s.spec, s.clause, s.release, p.tsg_number AS t
            FROM {{member}} m JOIN cr_pack p ON p.id = m.pack_id JOIN document doc ON doc.id = m.cr
            JOIN disposition d ON d.target = m.cr JOIN resolution r ON r.id = d.resolution_id
            JOIN {{change}} c ON c.cr = m.cr JOIN section s ON s.id = c.section_id
            WHERE m.pack_id = :anchor AND doc.target_release = s.release AND {VERIFIED}),
        prev AS (
            SELECT t.sid, t.spec, t.clause, p2.pack_number, p2.tsg_meeting, p2.tsg_number
            FROM touched t JOIN {{change}} c2 ON c2.section_id = t.sid JOIN document d2 ON d2.id = c2.cr
            JOIN {{member}} m2 ON m2.cr = c2.cr JOIN cr_pack p2 ON p2.id = m2.pack_id
            WHERE d2.target_release = t.release AND p2.tsg_number < t.t)
        SELECT DISTINCT spec, clause, pack_number, tsg_meeting FROM prev
        WHERE tsg_number = (SELECT max(q.tsg_number) FROM prev q WHERE q.sid = prev.sid)""",
}
# 두 벌의 참조 SQL 이 읽는 기록 방향.
VARIANTS = {
    "cr_side": {"member": "cr_in_pack", "change": "cr_modifies_section", "origin": "pack_member"},
    "container_side": {"member": "pack_member", "change": "section_modified_by", "origin": "cr_in_pack"},
}
# 조건 하나를 뺀 대조 질의: (SQL 에서 지울 문자열, 그 조건이 들어 있는 문항 종류).
CONTROLS = {
    "without_source_verified_whole_target_condition": (
        f" AND {VERIFIED}", ("disposition_pack", "full_chain", "clause_history", "pack_origin")),
    "without_release_match_condition": (" AND doc.target_release = s.release", ("clause_history",)),
}
# 절 단위 종류의 대조 질의: 이름 → {문항 종류: (바꿀 문자열, 바꿔 넣을 문자열)}.
CLAUSE_SET_CONTROLS = {
    "without_source_verified_whole_target_condition": {
        family: (f" AND {VERIFIED}", "") for family in CLAUSE_SET_SQL},
    "without_release_match_of_other_change_requests": {
        "clause_neighbours": (" AND o.target_release = s.release", ""),
        "first_change": (" AND d2.target_release = s.release", ""),
        "previous_pack": ("WHERE d2.target_release = t.release AND ", "WHERE ")},
    # 앞선 묶음을 같은 절 식별자(규격·release·절)가 아니라 같은 규격·절 번호로 찾으면 다른 release 판본의 변경이 섞인다.
    "earlier_change_matched_by_clause_number_across_releases": {
        "first_change": ("WHERE c2.section_id = s.id AND d2.target_release = s.release",
                         "JOIN section s2 ON s2.id = c2.section_id WHERE s2.spec = s.spec AND s2.clause = s.clause")},
    "without_latest_earlier_meeting_condition": {
        "previous_pack": ("WHERE tsg_number = (SELECT max(q.tsg_number) FROM prev q WHERE q.sid = prev.sid)", "")},
}
TABLE_REF = re.compile(r"\b(?:FROM|JOIN)\s+([a-z_]+)")


def shape(sql: str) -> dict:
    """SQL 문의 조인 수와 읽는 기본 테이블."""
    tables = sorted(set(TABLE_REF.findall(sql)) - {"later", "touched", "prev"})
    return {"joins": len(re.findall(r"\bJOIN\b", sql)), "tables": len(tables), "tableNames": tables,
            "recursive": "WITH RECURSIVE" in sql}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--db-dir", type=Path, required=True)
    parser.add_argument("--items", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    items = [(path, json.loads(line)) for path in args.items for line in path.read_text().splitlines()]
    present = {item["family"] for _, item in items}
    queries = {**SQL, **{family: sql for family, sql in CLAUSE_SET_SQL.items() if family in present}}
    databases: dict[str, sqlite3.Connection] = {}
    report = {"itemFiles": [{"path": str(path), "items": sum(1 for p, _ in items if p == path)} for path in args.items],
              "items": len(items), "comparison": "SELECT DISTINCT 결과 행 집합과 gold 행 집합의 완전 일치", "variants": {}}
    for variant, names in VARIANTS.items():
        match: collections.Counter[tuple[str, str]] = collections.Counter()
        total: collections.Counter[tuple[str, str]] = collections.Counter()
        mismatches = []
        for _, item in items:
            if item["wg"] not in databases:
                databases[item["wg"]] = sqlite3.connect(f"file:{args.db_dir / (item['wg'] + '.sqlite')}?mode=ro", uri=True)
            sql = queries[item["family"]].format(**names)
            derived = {tuple(row) for row in databases[item["wg"]].execute(sql, {"anchor": item["anchor"]})}
            gold = {tuple(row) for row in item["gold"]}
            total[(item["family"], item["wg"])] += 1
            if derived == gold:
                match[(item["family"], item["wg"])] += 1
            else:
                mismatches.append({"id": item["id"], "family": item["family"], "wg": item["wg"],
                                   "goldRows": len(gold), "sqlRows": len(derived),
                                   "onlyInGold": sorted(gold - derived), "onlyInSql": sorted(derived - gold)})
        families = {}
        for family in queries:
            sql = queries[family].format(**names)
            cells = {wg: {"match": match[(f, wg)], "items": n} for (f, wg), n in sorted(total.items()) if f == family}
            families[family] = {**shape(sql), "match": sum(c["match"] for c in cells.values()),
                                "items": sum(c["items"] for c in cells.values()), "byWg": cells,
                                "sql": " ".join(sql.split())}
        report["variants"][variant] = {
            "records": names, "match": sum(match.values()), "items": sum(total.values()),
            "byItemFile": [{"path": str(path),
                            "match": sum(1 for p, i in items if p == path) - sum(
                                1 for p, i in items if p == path and any(m["id"] == i["id"] and m["wg"] == i["wg"] for m in mismatches)),
                            "items": sum(1 for p, _ in items if p == path)} for path in args.items],
            "byFamily": families, "mismatches": mismatches}
    report["conditionControls"] = {}
    for name, (clause, families) in CONTROLS.items():
        changed: collections.Counter[str] = collections.Counter()
        total_by_family: collections.Counter[str] = collections.Counter()
        for _, item in items:
            if item["family"] not in families:
                continue
            full = SQL[item["family"]].format(**VARIANTS["cr_side"])
            assert clause in full, (name, item["family"])
            derived = {tuple(row) for row in databases[item["wg"]].execute(full.replace(clause, ""), {"anchor": item["anchor"]})}
            total_by_family[item["family"]] += 1
            changed[item["family"]] += derived != {tuple(row) for row in item["gold"]}
        report["conditionControls"][name] = {
            "removedFromSql": clause.strip(), "itemsDifferingFromGold": sum(changed.values()),
            "items": sum(total_by_family.values()),
            "byFamily": {f: {"differ": changed[f], "items": total_by_family[f]} for f in families}}
    if present & set(CLAUSE_SET_SQL):
        report["clauseSetConditionControls"] = {}
        for name, by_family in CLAUSE_SET_CONTROLS.items():
            changed = collections.Counter()
            total_by_family = collections.Counter()
            for _, item in items:
                if item["family"] not in by_family:
                    continue
                old, new = by_family[item["family"]]
                full = CLAUSE_SET_SQL[item["family"]].format(**VARIANTS["cr_side"])
                assert full.count(old) == 1, (name, item["family"])
                derived = {tuple(row) for row in databases[item["wg"]].execute(full.replace(old, new),
                                                                               {"anchor": item["anchor"]})}
                total_by_family[item["family"]] += 1
                changed[item["family"]] += derived != {tuple(row) for row in item["gold"]}
            report["clauseSetConditionControls"][name] = {
                "replaced": {f: {"from": " ".join(old.split()), "to": " ".join(new.split())}
                             for f, (old, new) in by_family.items()},
                "itemsDifferingFromGold": sum(changed.values()), "items": sum(total_by_family.values()),
                "byFamily": {f: {"differ": changed[f], "items": total_by_family[f]} for f in by_family}}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    for variant, result in report["variants"].items():
        print(variant, f"{result['match']} / {result['items']}", [(b["match"], b["items"]) for b in result["byItemFile"]])
        for family, row in result["byFamily"].items():
            print(f"  {family:18s} {row['match']:3d} / {row['items']:3d}  joins={row['joins']} tables={row['tables']}"
                  f" recursive={row['recursive']}")
        print("  mismatches:", [m["id"] for m in result["mismatches"]])
    for name, control in {**report["conditionControls"], **report.get("clauseSetConditionControls", {})}.items():
        print(name, f"{control['itemsDifferingFromGold']} / {control['items']}", control["byFamily"])


if __name__ == "__main__":
    main()
