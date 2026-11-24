"""질문 문장만으로 정답이 정해지는지 보는 재유도 검사의 문항 추출과 대조 (모델 호출 없음).

통과 검사·그래프 대조는 생성기와 같은 기록에서 출발하므로 문항과 기록의 정합만 본다. 이 검사는 생성기·통과 검사·
정답을 보지 않은 풀이자가 질문 문장과 기록 파일만으로 구한 행 집합이 정답과 같은지 본다.

- `--export`: 작업반·문항 종류 칸마다 한 문항(`--per-cell`로 여러 문항)을 고정 seed로 뽑아 정답과 근거를 뺀 묶음(JSONL)을
  쓴다. `--exclude`로 준 묶음의 문항은 빼고 뽑는다.
- `--score`: 풀이자가 낸 답 파일(JSONL, 줄마다 {"id", "rows", "note"})을 정답과 맞대어 결과 JSON을 쓴다.
  대조 대상은 `--packet`으로 준 묶음의 문항이다. 추출 뒤 채택 집합이 바뀌어도 풀이자가 실제로 받은 문항을
  그대로 채점하고, 그 사이 채택에서 빠진 문항은 `withdrawn`으로 따로 센다.

사용 (저장소 루트에서 실행):
  python3 rederive_chain_items.py --items <admitted.jsonl> [<admitted.jsonl> ...] --export <packet.jsonl>
  python3 rederive_chain_items.py --items <admitted.jsonl> [...] --packet <packet.jsonl> --score <answers.jsonl> [...] --out <json>
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

SEED = 20261112


def load(paths: list[Path]) -> list[dict]:
    return [json.loads(line) for path in paths for line in path.read_text().splitlines() if line.strip()]


def sample(items: list[dict], per_cell: int = 1, exclude: frozenset[str] = frozenset()) -> list[dict]:
    cells: dict[tuple[str, str], list[dict]] = {}
    for item in items:
        cells.setdefault((item["wg"], item["family"]), []).append(item)
    rng = random.Random(SEED)
    first = {cell: rng.choice(sorted(cells[cell], key=lambda item: item["id"])) for cell in sorted(cells)}
    if per_cell == 1 and not exclude:
        return list(first.values())
    chosen = []
    for cell in sorted(cells):
        pool = [item for item in sorted(cells[cell], key=lambda item: item["id"]) if item["id"] not in exclude]
        chosen.extend(rng.sample(pool, min(per_cell, len(pool))))
    return chosen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, nargs="+", required=True)
    parser.add_argument("--export", type=Path)
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--per-cell", type=int, default=1, help="칸마다 뽑는 문항 수")
    parser.add_argument("--exclude", type=Path, nargs="*", default=[], help="이미 낸 묶음. 그 문항은 다시 뽑지 않는다")
    parser.add_argument("--score", type=Path, nargs="+")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    admitted = load(args.items)
    if args.export:
        chosen = sample(admitted, args.per_cell, frozenset(entry["id"] for entry in load(args.exclude)))
        with args.export.open("w") as handle:
            for item in chosen:
                handle.write(json.dumps({key: item[key] for key in ("id", "wg", "question", "fields")},
                                        ensure_ascii=False) + "\n")
        print(json.dumps({"exported": len(chosen)}))
        return
    answers = {answer["id"]: answer for answer in load(args.score)}
    by_id = {item["id"]: item for item in admitted}
    packet = [entry["id"] for entry in load([args.packet])]
    withdrawn = [identifier for identifier in packet if identifier not in by_id]
    chosen = [by_id[identifier] for identifier in packet if identifier in by_id]
    results = []
    for item in chosen:
        answer = answers.get(item["id"])
        gold = sorted(tuple(row) for row in item["gold"])
        given = None if answer is None else sorted({tuple(str(value) for value in row) for row in answer["rows"]})
        results.append({"id": item["id"], "wg": item["wg"], "family": item["family"], "goldRows": len(gold),
                        "answered": answer is not None, "match": given == gold,
                        "note": "" if answer is None else answer.get("note", "")})
    report = {"seed": SEED, "packet": len(packet), "withdrawn": withdrawn, "sampled": len(chosen), "answered": sum(r["answered"] for r in results),
              "match": sum(r["match"] for r in results), "items": results}
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("packet", "withdrawn", "sampled", "answered", "match")}))


if __name__ == "__main__":
    main()
