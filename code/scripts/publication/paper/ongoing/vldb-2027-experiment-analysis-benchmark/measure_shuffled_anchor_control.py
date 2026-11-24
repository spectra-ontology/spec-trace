"""앵커를 섞은 대조 문항을 만든다: 문항마다 같은 칸(WG · 종류)의 다른 문항 질문을 붙이고 정답은 제 것을 둔다.

원본 글 식별자 따라가기(`measure_raw_source_route.py`)가 정답을 담는 까닭이 질문에 적힌 식별자인지 확인하는
대조다. 질문의 식별자가 다른 문항 것으로 바뀌면 같은 절차가 제 정답을 담는 수가 얼마나 남는지 센다.

- 칸은 (wg, family) 다. 칸 안의 문항을 `sha256("shuffled-anchor:" + id)` 순으로 늘어놓고, 문항마다 바로 다음
  문항(끝은 처음으로 돌아감)의 질문을 받는다. 문항이 하나뿐인 칸은 빼고 그 수를 적는다.
- 낸 파일의 문항은 `question` 만 바뀌고 `id` · `gold` · `fields` 는 그대로다. 받은 질문의 주인은 `donorId` 에 적는다.
- 질문을 준 문항과 정답 행이 한 줄이라도 겹치는 문항 수를 함께 적는다(겹치면 섞어도 담길 수 있다).

사용 (저장소 루트에서):
  python3 scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/measure_shuffled_anchor_control.py
  PYTHONPATH=scripts/common:scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark python3 \
      scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/measure_raw_source_route.py \
      --items logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/final/supplement_cycle/shuffled_anchor/items_shuffled.jsonl \
      --out-dir logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/final/supplement_cycle/shuffled_anchor
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
TRACK = ROOT / "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
ITEM_FILES = (TRACK / "integration/items_final/gate/core/chain_items_admitted.jsonl",
              TRACK / "integration/items_final/gate/ran5/chain_items_admitted.jsonl")
OUT_DIR = TRACK / "final/supplement_cycle/shuffled_anchor"
SALT = "shuffled-anchor:"


def order_key(item: dict) -> str:
    return hashlib.sha256((SALT + item["id"]).encode()).hexdigest()


def rows(item: dict) -> set[str]:
    return {json.dumps(row, ensure_ascii=False, sort_keys=True) for row in item.get("gold") or []}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, nargs="+", default=list(ITEM_FILES))
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    items = [json.loads(line) for path in args.items for line in path.read_text().splitlines() if line.strip()]
    cells: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for item in items:
        cells[item["wg"], item["family"]].append(item)
    shuffled, single, shared, same_question = [], [], 0, 0
    for cell in sorted(cells):
        members = sorted(cells[cell], key=order_key)
        if len(members) < 2:
            single.extend(member["id"] for member in members)
            continue
        for position, item in enumerate(members):
            donor = members[(position + 1) % len(members)]
            shared += bool(rows(item) & rows(donor))
            same_question += item["question"] == donor["question"]
            shuffled.append({**item, "question": donor["question"], "donorId": donor["id"]})
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / "items_shuffled.jsonl"
    out.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in shuffled))
    design = {"rule": "칸 (wg, family) 안에서 sha256('shuffled-anchor:' + id) 순으로 늘어놓고 다음 문항의 질문을 받는다",
              "items": len(items), "cells": len(cells), "shuffled": len(shuffled),
              "singleItemCellsLeftOut": single, "sharesGoldRowWithDonor": shared,
              "sameQuestionAsDonor": same_question,
              "itemsFileSha256": hashlib.sha256(out.read_bytes()).hexdigest()}
    (args.out_dir / "design.json").write_text(json.dumps(design, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(design, ensure_ascii=False))


if __name__ == "__main__":
    main()
