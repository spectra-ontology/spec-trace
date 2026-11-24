"""밀집 검색이 모델에 주는 문맥에 정답이 들어 있는지 센다 (모델 호출 없음).

`run_chain_eval.py`의 dense 방법과 같은 검색(`retrieve`)과 같은 자르기(청크마다 메타데이터와 본문 앞 1500자)로
문맥을 만든다. 정답 행의 모든 칸이 그 문맥에 문자열로 들어 있으면 그 행을 "담김"으로 센다. 견주기 전에
채점(`score_chain_eval.cell_key`)과 같이 대소문자를 무시하고 bis 회의 표기를 한 가지 철자로 맞춘다.
- allRows: 정답 행이 모두 담긴 문항 수. 어떤 독해 모델이든 이 문맥만으로 낼 수 있는 정확 일치의 상한이다.
- anyRow: 정답 행이 하나라도 담긴 문항 수.
칸이 문맥의 서로 다른 청크에 흩어져 있어도 담긴 것으로 세므로 상한은 느슨한 쪽으로 잡힌다.
빈 정답 문항은 세지 않는다.

사용: PYTHONPATH=scripts/common:<이 디렉토리> python3 measure_dense_context_ceiling.py --items <jsonl> --out <json>
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

from run_chain_eval import retrieve
from score_chain_eval import cell_key, meeting_spelling


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--top", type=int, default=8, help="문맥에 넣는 청크 수(dense 실행과 같은 값)")
    args = parser.parse_args()
    counts: dict[tuple[str, str], collections.Counter] = collections.defaultdict(collections.Counter)
    for item in map(json.loads, args.items.read_text().splitlines()):
        if not item["gold"]:
            continue
        context = meeting_spelling("\n".join(
            json.dumps(chunk["meta"], ensure_ascii=False) + "\n" + chunk["text"][:1500]
            for chunk in retrieve(item, args.top)).lower())
        held = [all(cell_key(cell) in context for cell in row) for row in item["gold"]]
        for group in (("all", "all"), ("wg", item["wg"]), ("family", item["family"])):
            counts[group].update(n=1, allRows=all(held), anyRow=any(held))
    report = [{"by": by, "value": value, "n": c["n"], "allRows": c["allRows"], "anyRow": c["anyRow"]}
              for (by, value), c in sorted(counts.items())]
    args.out.write_text(json.dumps({"top": args.top, "groups": report}, ensure_ascii=False, indent=2) + "\n")
    for row in report:
        print(row)


if __name__ == "__main__":
    main()
