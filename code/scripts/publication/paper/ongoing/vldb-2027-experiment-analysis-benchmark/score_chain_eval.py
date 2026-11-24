"""저장된 응답을 추적 사슬 문항의 정답 행 집합과 맞대어 채점한다 (모델 호출 없음).

행은 칸의 앞뒤 공백을 걷고 소문자로 바꾼 값의 튜플로 비교한다. 그 밖의 변환은 하나뿐이다. 회의 번호 뒤에
붙는 "bis" 회의 표시는 한 가지 철자로 맞춘다(`meeting_spelling`). 같은 회의를 기록마다 다르게 적기 때문이다.
그래프와 정답은 RAN1 에서 `RAN1#100b-e`, RAN3·RAN4 에서 `RAN4#104bis-e` 로 적고, 글 검색 색인의 메타데이터와
본문은 같은 회의를 `RAN1#100bis-e` · `RAN1#104-b-e` · `RAN4#104-bis-e` · `RAN3#99-Bis` · `RAN4#94-e-bis` 로도
적는다. 풀이 규칙이 "기록에 적힌 그대로" 쓰라고 하므로 이 표기들은 모두 같은 회의의 이름으로 본다.
`RAN1#100` 과 `RAN1#100-e` 처럼 회의가 다른 표기는 그대로 둔다.
- exact: 응답 행 집합이 정답 행 집합과 같다(빈 정답 문항은 빈 응답일 때).
- precision · recall · f1: 문항별 행 단위 값의 평균. 정답과 응답이 모두 비면 1, 한쪽만 비면 0이다.
- unreadable: 응답이 행 목록 형식이 아니거나 질의가 끝내 실행되지 않은 문항 수. 점수는 0으로 센다.
- abstention: 빈 정답 문항(`pack_lookup_empty`)과 같은 질문 틀의 정답 있는 문항(`pack_lookup`)을 짝지어 본다.
  `onEmpty`는 빈 정답 문항에서 빈 응답을 낸 비율, `onAnswerable`은 정답 있는 문항에서 빈 응답을 낸 비율,
  `discrimination`은 둘의 차다. 모든 문항에 빈 응답을 내는 풀이는 0이 된다. 읽을 수 없는 응답은 빈 응답으로 세지 않는다.
응답 파일에 없는 문항은 `missing`으로 따로 세고 평균에 넣지 않는다. 응답에 적힌 질문 문장의 SHA-256이 현재 문항의
질문과 다르거나 없는 응답은 다른 문장에 대한 답이므로 `staleQuestion`으로 세고 없는 응답과 같이 다룬다.

사용: python3 score_chain_eval.py --items <jsonl> [<jsonl> ...] --responses <jsonl> [<jsonl> ...] --out <json>
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
from pathlib import Path

# 소문자로 바꾼 글에서 회의 번호(`#` 뒤 숫자) 바로 뒤의 bis 표시. 문서 번호·절 번호에는 `#` 이 없어 걸리지 않는다.
# `-e-bis` 는 bis 표시가 `-e` 뒤에 온 표기라 먼저 `bis-e` 차례로 바꾼다.
E_BEFORE_BIS = re.compile(r"(#\d+)-e-b(?:is)?(?![a-z0-9])")
BIS_MARK = re.compile(r"(#\d+)-?b(?:is)?(?![a-z0-9])")


def meeting_spelling(lowered: str) -> str:
    """소문자 글 안의 bis 회의 표기를 `#<번호>bis` 로 맞춘다(`#100b-e` · `#104-bis-e` · `#94-e-bis` → `…bis-e`)."""
    return BIS_MARK.sub(r"\1bis", E_BEFORE_BIS.sub(r"\1bis-e", lowered))


def cell_key(cell) -> str:
    return "" if cell is None else meeting_spelling(str(cell).strip().lower())


def key(row) -> tuple[str, ...]:
    return tuple(cell_key(cell) for cell in row)


def score(gold: list, rows) -> dict:
    wanted = {key(row) for row in gold}
    if rows is None:
        return {"exact": 0, "precision": 0.0, "recall": 0.0, "f1": 0.0, "unreadable": 1}
    given = {key(row) for row in rows}
    if not wanted and not given:
        return {"exact": 1, "precision": 1.0, "recall": 1.0, "f1": 1.0, "unreadable": 0}
    hit = len(wanted & given)
    precision = hit / len(given) if given else 0.0
    recall = hit / len(wanted) if wanted else 0.0
    f1 = 2 * precision * recall / (precision + recall) if hit else 0.0
    return {"exact": int(wanted == given), "precision": precision, "recall": recall, "f1": f1, "unreadable": 0}


def summarize(scores: list[dict]) -> dict:
    n = len(scores)
    return {"n": n, "exact": sum(s["exact"] for s in scores),
            **{name: round(sum(s[name] for s in scores) / n, 4) for name in ("precision", "recall", "f1")},
            "unreadable": sum(s["unreadable"] for s in scores)}


def abstention(pairs: list[tuple[dict, object]]) -> dict | None:
    def rate(family: str) -> tuple[int, int]:
        rows = [rows for item, rows in pairs if item["family"] == family]
        return sum(rows is not None and not rows for rows in rows), len(rows)
    (empty_hit, empty_n), (answerable_hit, answerable_n) = rate("pack_lookup_empty"), rate("pack_lookup")
    if not empty_n or not answerable_n:
        return None
    return {"onEmpty": [empty_hit, empty_n], "onAnswerable": [answerable_hit, answerable_n],
            "discrimination": round(empty_hit / empty_n - answerable_hit / answerable_n, 4)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, nargs="+", required=True)
    parser.add_argument("--responses", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    items = {item["id"]: item for path in args.items for item in map(json.loads, path.read_text().splitlines())}
    report = []
    for path in args.responses:
        loaded = {record["id"]: record for record in map(json.loads, path.read_text().splitlines())}
        if not loaded:
            continue
        first = next(iter(loaded.values()))
        records = {identifier: record for identifier, record in loaded.items() if identifier in items
                   and record.get("questionSha256") == hashlib.sha256(items[identifier]["question"].encode()).hexdigest()}
        stale = sum(identifier in items for identifier in loaded) - len(records)
        scope = [item for item in items.values() if item["wg"] == first["wg"]]
        groups: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
        pairs = [(item, records[item["id"]].get("rows")) for item in scope if item["id"] in records]
        for item in scope:
            if item["id"] not in records:
                continue
            result = score(item["gold"], records[item["id"]].get("rows"))
            for group in (("all", "all"), ("family", item["family"]), ("hops", str(item["hops"])),
                          ("expectsEmpty", str(item["expectsEmpty"]).lower())):
                groups[group].append(result)
        report.append({"responses": str(path), "wg": first["wg"], "method": first["method"], "model": first["model"],
                       "missing": sum(item["id"] not in records for item in scope), "staleQuestion": stale,
                       "abstention": abstention(pairs),
                       "groups": [{"by": by, "value": value, **summarize(scores)}
                                  for (by, value), scores in sorted(groups.items())]})
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    for run in report:
        overall = next((group for group in run["groups"] if group["by"] == "all"), "no current-question responses")
        print(run["wg"], run["method"], run["model"], "missing", run["missing"], "stale", run["staleQuestion"], overall, run["abstention"])


if __name__ == "__main__":
    main()
