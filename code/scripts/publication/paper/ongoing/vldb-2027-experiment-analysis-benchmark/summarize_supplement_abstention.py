"""보충 측정의 에이전트 조건마다 실행별 기권 지표를 낸다 (모델 호출 없음).

`analyze_supplement_cycle.py` 와 같은 응답 파일을 읽고 주 규칙(`recorded`)의 정확 일치로 센다.
실행마다 정답 있는 문항 정확 일치 수, 빈 정답 문항 가운데 빈 응답 수와 행을 낸 수(fabricated),
`pack_lookup` 정답 있는 문항 가운데 빈 응답 수와 정확 일치 수, D = N_empty − N_plus, D_X = N_empty − (1 − X_plus)
를 적고, 조건마다 실행 평균을 적는다. 응답이 없는 문항은 빈 응답이 아니라 읽을 수 없는 응답으로 센다.

사용: python3 summarize_supplement_abstention.py [--out <json>]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import analyze_supplement_cycle as cycle
import score_meeting_spelling_sensitivity as sens

ROOT = sens.ROOT
DEFAULT_OUT = f"{cycle.SUP}/analysis/abstention.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, default=ROOT / DEFAULT_OUT)
    args = parser.parse_args()
    items = {item["id"]: item for path in sens.ITEMS
             for item in map(json.loads, (ROOT / path).read_text().splitlines())}
    row_key = sens.make_row_key("recorded", sens.separately_recorded_meetings())
    runs = {"text_search": {run: sens.per_wg(sens.TEXT_ROUTES["text_search"][run])
                            for run in sens.RUN_DIRS["text_search"]},
            "text_search_text_only": {"runA": sens.SINGLE_ROUTES["text_search_text_only"]}}
    for method, by_run in cycle.COLLECTED.items():
        runs.setdefault(method, {}).update({run: sens.per_wg(pattern) for run, pattern in by_run.items()})
    empty_ids = [i for i, item in items.items() if item["expectsEmpty"]]
    plus_ids = [i for i, item in items.items() if not item["expectsEmpty"] and item["family"] == "pack_lookup"]
    answerable_ids = [i for i, item in items.items() if not item["expectsEmpty"]]
    out = {"rule": "recorded", "emptyGoldItems": len(empty_ids), "packLookupAnswerableItems": len(plus_ids),
           "answerableItems": len(answerable_ids), "methods": {}}
    for method, by_run in runs.items():
        per_run = {}
        for run, paths in sorted(by_run.items()):
            responses, _ = sens.read_responses(paths, items)

            def rows(i):
                return (responses.get(i) or {}).get("rows")
            empty_on_empty = sum(rows(i) == [] for i in empty_ids)
            fabricated = sum(bool(rows(i)) for i in empty_ids)
            empty_on_plus = sum(rows(i) == [] for i in plus_ids)
            exact_plus = sum(sens.exact(items[i], rows(i), row_key) for i in plus_ids)
            n_empty = empty_on_empty / len(empty_ids)
            per_run[run] = {
                "answerableExact": sum(sens.exact(items[i], rows(i), row_key) for i in answerable_ids),
                "emptyGoldEmptyResponse": empty_on_empty, "fabricated": fabricated,
                "packLookupEmptyResponse": empty_on_plus, "packLookupExact": exact_plus,
                "D": n_empty - empty_on_plus / len(plus_ids),
                "DX": n_empty - (1 - exact_plus / len(plus_ids)),
            }
        count = len(per_run)
        out["methods"][method] = {"runs": per_run,
                                  "meanD": sum(r["D"] for r in per_run.values()) / count,
                                  "meanDX": sum(r["DX"] for r in per_run.values()) / count,
                                  "meanFabricated": sum(r["fabricated"] for r in per_run.values()) / count}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    for method, block in out["methods"].items():
        print(method, f"D {block['meanD']:.3f} DX {block['meanDX']:.3f} fabricated {block['meanFabricated']:.2f}")
        for run, r in block["runs"].items():
            print("  ", run, r)


if __name__ == "__main__":
    main()
