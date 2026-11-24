"""첫 재유도 회차에만 들어간 문항이 지금 문항 문장으로 받은 답과 최종 정답이 같은지 센다 (모델 호출 없음).

재유도 검사는 두 회차로 돌았다. 둘째 회차의 문항 묶음은 첫 회차의 묶음과 거의 겹치지만 같지는 않다.
이 스크립트는 두 회차의 문항 집합을 맞대어 첫 회차에만 있는 문항을 찾고, 그 문항마다 첫 회차의 풀이자가
받은 질문 문장 가운데 최종 문항의 문장과 글자까지 같은 것이 있는지, 그 문장에 낸 행 집합이 최종 정답과 같은지 적는다.
행 집합의 대조는 `rederive_chain_items.py --score` 와 같은 정확 일치다.

`--first` 는 묶음 파일 하나와 그 묶음의 답 파일들을 한 벌로 받고 여러 번 줄 수 있다.

사용 (저장소 루트에서 실행):
  python3 measure_first_round_only_items.py --items <admitted.jsonl>... --first <packet.jsonl> <answers.jsonl>...
      [--first ...] --second-packets <packet.jsonl>... --out <json>
"""
from __future__ import annotations

import argparse
import json
import pathlib


def load(path: pathlib.Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=pathlib.Path, nargs="+", required=True)
    parser.add_argument("--first", type=pathlib.Path, nargs="+", action="append", required=True)
    parser.add_argument("--second-packets", type=pathlib.Path, nargs="+", required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()

    final = {item["id"]: item for path in args.items for item in load(path)}
    asked: dict[str, list[dict]] = {}
    for packet_path, *answer_paths in args.first:
        answers = {answer["id"]: answer for path in answer_paths for answer in load(path)}
        for entry in load(packet_path):
            asked.setdefault(entry["id"], []).append(
                {"packet": str(packet_path), "question": entry["question"], "fields": entry["fields"],
                 "answer": answers.get(entry["id"])})
    second = {entry["id"] for path in args.second_packets for entry in load(path)}
    first = set(asked)

    rows = []
    for identifier in sorted(first - second):
        item = final.get(identifier)
        record = {"id": identifier, "admitted": item is not None, "askings": []}
        if item is not None:
            gold = sorted(tuple(row) for row in item["gold"])
            record.update(wg=item["wg"], family=item["family"], goldRows=len(gold))
            for asking in asked[identifier]:
                answer = asking["answer"]
                given = None if answer is None else sorted({tuple(str(v) for v in row) for row in answer["rows"]})
                record["askings"].append({
                    "packet": asking["packet"],
                    "presentWording": asking["question"] == item["question"] and asking["fields"] == item["fields"],
                    "answered": answer is not None, "match": given == gold})
        record["matchOnPresentWording"] = any(a["presentWording"] and a["match"] for a in record["askings"])
        rows.append(record)

    report = {
        "items": [str(path) for path in args.items],
        "first": [[str(path) for path in group] for group in args.first],
        "secondPackets": [str(path) for path in args.second_packets],
        "admittedItems": len(final),
        "firstRoundItems": len(first), "secondRoundItems": len(second),
        "shared": len(first & second), "union": len(first | second),
        "outsideBothRounds": len(set(final) - first - second),
        "firstRoundOnly": rows,
        "firstRoundOnlyCount": len(rows),
        "firstRoundOnlyMatchOnPresentWording": sum(row["matchOnPresentWording"] for row in rows),
    }
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in report if key not in ("items", "first", "secondPackets",
                                                                       "firstRoundOnly")}))
    for row in rows:
        print(row["id"], row["matchOnPresentWording"], [(a["presentWording"], a["match"]) for a in row["askings"]])


if __name__ == "__main__":
    main()
