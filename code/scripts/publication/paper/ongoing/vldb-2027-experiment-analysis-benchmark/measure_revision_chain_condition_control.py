"""`revision_chain` 참조 SQL 에서 "원문 확인·문서 전체" 조건을 뺀 대조 질의가 정답과 달라지는 문항 수를 센다 (모델 호출 없음).

`measure_relational_equivalence.py` 의 대조 실행은 조건 문자열 ` AND {VERIFIED}` 를 지우므로 그 문자열이 들어 있는 네 종류만
다룬다. `revision_chain` 의 참조 SQL 은 같은 조건을 `WHERE {VERIFIED}` 로 적으므로 여기서 그 문자열을 지우고 같은 비교를 한다.
참조 SQL · 기록 방향 · 조건 문자열은 그 모듈의 값을 그대로 불러 쓴다.

두 절차가 같은 비교임을 보이려고 네 종류의 대조도 같은 함수로 다시 세어 함께 적는다. 조건을 둔 질의가 정답을 재현하는
문항 수도 적는다. 달라진 문항마다 정답에만 있는 행 수와 질의에만 있는 행 수를 남긴다.

사용: python3 measure_revision_chain_condition_control.py --db-dir <dir> --items <jsonl> [<jsonl> ...] --out <json>
저장소 루트에서 실행한다.
"""
from __future__ import annotations

import argparse
import collections
import json
import sqlite3
from pathlib import Path

from measure_relational_equivalence import CONTROLS, SQL, VARIANTS, VERIFIED

FAMILY = "revision_chain"
REMOVED = f"WHERE {VERIFIED}"
FOUR_FAMILY_CONTROL = "without_source_verified_whole_target_condition"


def row_set(database: sqlite3.Connection, sql: str, anchor: str) -> set[tuple]:
    return {tuple(row) for row in database.execute(sql, {"anchor": anchor})}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--db-dir", type=Path, required=True)
    parser.add_argument("--items", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    items = [json.loads(line) for path in args.items for line in path.read_text().splitlines() if line.strip()]
    databases: dict[str, sqlite3.Connection] = {}

    def database(wg: str) -> sqlite3.Connection:
        if wg not in databases:
            databases[wg] = sqlite3.connect(f"file:{args.db_dir / (wg + '.sqlite')}?mode=ro", uri=True)
        return databases[wg]

    full = SQL[FAMILY].format(**VARIANTS["cr_side"])
    if full.count(REMOVED) != 1:
        raise SystemExit("revision_chain 참조 SQL 에 지울 조건 문자열이 한 번 들어 있지 않다")
    reproduced = 0
    by_wg: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    differing = []
    for item in items:
        if item["family"] != FAMILY:
            continue
        gold = {tuple(row) for row in item["gold"]}
        reproduced += row_set(database(item["wg"]), full, item["anchor"]) == gold
        derived = row_set(database(item["wg"]), full.replace(REMOVED, ""), item["anchor"])
        by_wg[item["wg"]]["items"] += 1
        if derived != gold:
            by_wg[item["wg"]]["differ"] += 1
            differing.append({"id": item["id"], "wg": item["wg"], "goldRows": len(gold), "sqlRows": len(derived),
                              "onlyInGold": len(gold - derived), "onlyInSql": len(derived - gold)})

    clause, families = CONTROLS[FOUR_FAMILY_CONTROL]
    four: dict[str, collections.Counter[str]] = {family: collections.Counter() for family in families}
    for item in items:
        if item["family"] not in families:
            continue
        sql = SQL[item["family"]].format(**VARIANTS["cr_side"])
        if sql.count(clause) != 1:
            raise SystemExit(f"{item['family']} 참조 SQL 에 지울 조건 문자열이 한 번 들어 있지 않다")
        four[item["family"]]["items"] += 1
        four[item["family"]]["differ"] += (row_set(database(item["wg"]), sql.replace(clause, ""), item["anchor"])
                                           != {tuple(row) for row in item["gold"]})

    revision = {"removedFromSql": REMOVED, "items": sum(c["items"] for c in by_wg.values()),
                "reproducedWithCondition": reproduced, "itemsDifferingFromGold": len(differing),
                "byWg": {wg: {"differ": c["differ"], "items": c["items"]} for wg, c in sorted(by_wg.items())},
                "differing": differing}
    recount = {"removedFromSql": clause.strip(), "items": sum(c["items"] for c in four.values()),
               "itemsDifferingFromGold": sum(c["differ"] for c in four.values()),
               "byFamily": {family: {"differ": c["differ"], "items": c["items"]} for family, c in four.items()}}
    report = {"itemFiles": [str(path) for path in args.items], "items": len(items),
              "comparison": "SELECT DISTINCT 결과 행 집합과 gold 행 집합의 완전 일치",
              "condition": VERIFIED, FAMILY: revision, "fourFamiliesRecount": recount,
              "fiveFamilies": {"items": revision["items"] + recount["items"],
                               "itemsDifferingFromGold": revision["itemsDifferingFromGold"]
                               + recount["itemsDifferingFromGold"]}}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(FAMILY, f"{revision['itemsDifferingFromGold']} / {revision['items']}", "재현", reproduced, revision["byWg"])
    print("네 종류", f"{recount['itemsDifferingFromGold']} / {recount['items']}", recount["byFamily"])
    print("다섯 종류", report["fiveFamilies"])


if __name__ == "__main__":
    main()
