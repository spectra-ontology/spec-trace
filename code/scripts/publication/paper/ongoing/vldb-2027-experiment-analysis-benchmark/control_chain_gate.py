"""구축 통과 검사가 훼손된 문항을 실제로 걸러내는지 확인한다 (모델 호출 없음).

채택 문항에서 종류별로 표본을 뽑아 한 군데씩 훼손한 대조 문항을 만들고 `verify_chain_items.check`에 넣는다.
훼손마다 검사가 내야 하는 실패 사유를 정해 두고, 그 사유로 걸렸는지 센다.
- drop_row · alter_value · extra_row · fill_empty · false_empty: 정답 행 집합이 재유도 결과와 달라진다
- drop_column: 정답 행의 열 수가 요청 필드 수와 달라진다
- bad_sha: 근거 원문 파일의 해시가 달라진다
- blank_question: 질문이 요청 필드를 말하지 않는다
- packed_sibling: 문서를 묻는 문항의 문서와 규격·CR 번호가 같은 가상 문서를 정답에 없는 묶음에 넣는다.
  이 대조는 문항이 아니라 기록을 훼손하므로 작업반 데이터베이스의 사본에서 실행한다

사용: python3 control_chain_gate.py --items <chain_items.jsonl> --per-family 6 --seed 7 --out <json>
재구축한 처분 기록으로 만든 문항은 생성 때와 같은 `--phase2-root`를, 그래프에서 내보낸 묶음·절 기록으로 만든
문항은 생성 때와 같은 `--phase4-root`를 준다.
저장소 루트에서 실행한다.
"""
from __future__ import annotations

import argparse
import collections
import copy
import json
import random
import sqlite3
from pathlib import Path

from verify_chain_items import CR_PACK_COLUMN, check, database

GOLD, WIDTH = "gold_differs_from_independent_derivation", "row_width_differs_from_requested_fields"
SIBLING = "same_cr_identity_packed_outside_gold"


def with_packed_sibling(db: sqlite3.Connection, item: dict) -> sqlite3.Connection:
    """문항의 문서와 규격·CR 번호가 같은 가상 문서를 정답에 없는 묶음에 넣은 데이터베이스 사본."""
    copied = sqlite3.connect(":memory:")
    db.backup(copied)
    cr, spec = copied.execute("SELECT cr, spec FROM doc WHERE id = ?", (item["anchor"],)).fetchone()
    named = {row[CR_PACK_COLUMN[item["family"]]] for row in item["gold"]}
    pack_id, pack = next(row for row in copied.execute("SELECT id, substr(id, instr(id, '/') + 1) FROM pack")
                         if row[1] not in named)
    copied.execute("INSERT INTO doc VALUES ('tdoc:CONTROL-SIBLING', 'CONTROL-SIBLING', '', '', ?, ?)", (cr, spec))
    copied.execute("INSERT INTO pack_member VALUES ('tdoc:CONTROL-SIBLING', ?, ?)", (pack_id, pack))
    return copied


def controls(items: list[dict], per_family: int, rng: random.Random) -> list[tuple[str, str, dict]]:
    by_family: dict[str, list[dict]] = collections.defaultdict(list)
    for item in items:
        by_family[item["family"]].append(item)
    out = []

    def add(kind: str, expected: str, item: dict, **changes) -> None:
        out.append((kind, expected, {**copy.deepcopy(item), **changes}))

    for family in sorted(by_family):
        for item in rng.sample(by_family[family], min(per_family, len(by_family[family]))):
            gold = item["gold"]
            if gold:
                add("drop_row", GOLD, item, gold=gold[1:])
                add("alter_value", GOLD, item, gold=[[f"{gold[0][0]}X", *gold[0][1:]], *gold[1:]])
                add("extra_row", GOLD, item, gold=[*gold, [*gold[0][:-1], "ZZ"]])
                add("drop_column", WIDTH, item, gold=[row[:-1] for row in gold])
            else:
                add("fill_empty", GOLD, item, gold=[["RP-000000", "RAN#1"]])
            if item["evidence"]:
                add("bad_sha", "evidence_source_changed", item,
                    evidence=[{**item["evidence"][0], "sha256": "0" * 64}, *item["evidence"][1:]])
            add("blank_question", "question_does_not_name_a_requested_field", item, question="Which one?")
            if family in CR_PACK_COLUMN:
                add("packed_sibling", SIBLING, item)
    for item in rng.sample(by_family["pack_lookup"], min(per_family, len(by_family["pack_lookup"]))):
        add("false_empty", GOLD, item, family="pack_lookup_empty", gold=[], expectsEmpty=True)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, required=True)
    parser.add_argument("--per-family", type=int, required=True, help="종류별로 훼손할 문항 수")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--phase2-root", type=Path, help="재구축한 phase-2 파일이 WG별로 놓인 디렉토리")
    parser.add_argument("--phase4-root", type=Path, help="그래프에서 내보낸 phase-4 파일이 WG별로 놓인 디렉토리")
    args = parser.parse_args()
    items = [json.loads(line) for line in args.items.read_text().splitlines()]
    databases, sha_of = {}, {}
    counts: collections.Counter[tuple[str, str]] = collections.Counter()
    for kind, expected, item in controls(items, args.per_family, random.Random(args.seed)):
        if item["wg"] not in databases:
            databases[item["wg"]] = database(item["wg"], args.phase2_root, args.phase4_root)
        db = databases[item["wg"]]
        if kind == "packed_sibling":
            db = with_packed_sibling(db, item)
        failures = check(item, db, sha_of)
        counts[(kind, "caught_for_expected_reason" if expected in failures
                else "caught_for_other_reason" if failures else "admitted")] += 1
    report = {"perFamily": args.per_family, "seed": args.seed, "controls": sum(counts.values()),
              "admitted": sum(n for (_, result), n in counts.items() if result == "admitted"),
              "byKind": [{"kind": kind, "result": result, "n": n} for (kind, result), n in sorted(counts.items())]}
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
