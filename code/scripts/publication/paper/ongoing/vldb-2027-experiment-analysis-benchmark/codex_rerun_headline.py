"""Codex 재실행 집계(summary.json)에서 조건 · 언어마다 정확 일치 수와 pack_lookup 기권 지표를 뽑는다 (모델 호출 없음).

`summarize_chain_scores.py` 의 출력은 응답이 있는 문항만 센다. 여기서는 전체 문항 수를 분모로 두고, 응답이 없는
문항은 틀린 것으로 센다. 정답 없는 문항은 `pack_lookup_empty` 문항 종류 하나에만 있으므로 그 종류의 정확 일치를
k/빈 정답 문항 수로, 나머지 종류의 합을 k/정답 있는 문항 수로 적는다. 문항 종류가 이 구성을 벗어나면 멈춘다.
pack_lookup 의 correctnessAware(D/C)는 집계가 낸 값을 그대로 옮긴다(응답이 있는 문항 기준).

사용: python3 codex_rerun_headline.py --summary <summary.json> --items <jsonl> [...] --out <json>
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

EMPTY_FAMILY = "pack_lookup_empty"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--items", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    items = [json.loads(line) for path in args.items for line in path.read_text().splitlines() if line]
    families = collections.Counter(item["family"] for item in items)
    empty_families = {item["family"] for item in items if not item["gold"]}
    if empty_families != {EMPTY_FAMILY} or any(item["gold"] for item in items if item["family"] == EMPTY_FAMILY):
        raise SystemExit(f"정답 없는 문항이 {EMPTY_FAMILY} 한 종류에만 있지 않다: {sorted(empty_families)}")
    total, empty = len(items), families[EMPTY_FAMILY]
    summary = json.loads(args.summary.read_text())
    rows = []
    for run in summary["runs"]:
        by_family = {group["value"]: group for group in run["groups"] if group["by"] == "family"}
        overall = next(group for group in run["groups"] if group["by"] == "all")
        exact_empty = by_family.get(EMPTY_FAMILY, {"exact": 0})["exact"]
        exact_answerable = sum(group["exact"] for family, group in by_family.items() if family != EMPTY_FAMILY)
        if exact_empty + exact_answerable != overall["exact"]:
            raise SystemExit(f"{run['method']}/{run['model']}: 문항 종류 합이 전체와 다르다")
        pack = next((entry for entry in run["abstentionByTemplate"] if entry["template"] == "pack_lookup"), None)
        rows.append({
            "method": run["method"], "model": run["model"], "wgs": run["wgs"],
            "answered": overall["n"], "missing": run["missing"], "unreadable": overall["unreadable"],
            "exact": f"{overall['exact']}/{total}", "exactAnswerable": f"{exact_answerable}/{total - empty}",
            "exactEmptyGold": f"{exact_empty}/{empty}",
            "packLookupCorrectnessAware": pack and pack["correctnessAware"],
            "packLookup": pack and {key: pack[key] for key in ("emptyItems", "answerableItems", "onEmpty",
                                                               "fabricatedOnEmpty", "onAnswerable",
                                                               "exactOnAnswerable")},
            "errorTypes": run["errorTypes"]["all"]})
    args.out.write_text(json.dumps({"summary": str(args.summary), "items": total, "answerable": total - empty,
                                    "emptyGold": empty, "rule": __doc__.split("\n\n")[1].replace("\n", " "),
                                    "runs": rows}, ensure_ascii=False, indent=1) + "\n")
    for row in rows:
        print(row["method"], row["model"], row["exact"], row["exactAnswerable"], row["exactEmptyGold"],
              "missing", row["missing"], "D/C", row["packLookupCorrectnessAware"])


if __name__ == "__main__":
    main()
