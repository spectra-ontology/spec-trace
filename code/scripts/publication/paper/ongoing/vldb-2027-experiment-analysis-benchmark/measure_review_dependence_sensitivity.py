"""신원 검토 기록에 기대는 문항을 빼고 각 조건을 다시 채점한다 (모델 호출 · 데이터베이스 질의 없음).

신원 검토에 기대는 문항은 `measure_identity_reviews.py` 의 결과(`gold.itemIdsDependingOnAnyReview`)다.
RAN1 문항의 검토는 빌드 스크립트가 만들고, RAN2 문항의 검토는 저장소에 생성 스크립트가 없다. 그래서 두 부분집합을 뺀다:
`withoutScriptless` = RAN2 의존 문항을 뺀 집합, `withoutAnyReview` = 의존 문항 전부를 뺀 집합.
채점은 `analyze_template_session.py` 의 조건 목록 · 응답 읽기 · 규칙(주 규칙 identity, 보조 규칙 recorded)을 그대로 쓴다.

사용 (저장소 루트에서):
    .venv/bin/python3 -I scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/measure_review_dependence_sensitivity.py \
        --reviews <identity_reviews.json> --out <json>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analyze_template_session import KEPT, ROOT, conditions, load_items, load_responses, outcomes  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--reviews", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    gold = json.loads((ROOT / args.reviews).read_text(encoding="utf-8"))["gold"]
    dependent = set(gold["itemIdsDependingOnAnyReview"])
    scriptless = {i for i in dependent if i.startswith("RAN2-")}
    items = load_items()
    if not dependent <= set(items):
        raise SystemExit("의존 문항 id 가 문항 집합에 없다")
    subsets = {"all": set(items), "withoutScriptless": set(items) - scriptless,
               "withoutAnyReview": set(items) - dependent, "onlyDependent": dependent}
    out = {"reviews": str(args.reviews), "items": len(items), "dependent": len(dependent),
           "scriptlessDependent": len(scriptless),
           "subsetSizes": {k: len(v) for k, v in subsets.items()}, "conditions": {}}
    source_files = [Path(__file__), Path(__file__).with_name("analyze_template_session.py"),
                    Path(__file__).with_name("score_meeting_spelling_sensitivity.py"), ROOT / args.reviews]
    out["scoring"] = {"identityRule": "same_meeting with separately recorded electronic meetings preserved",
                      "keptElectronicSpellings": sorted(KEPT),
                      "sourceFiles": [{"path": str(p.relative_to(ROOT)),
                                       "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in source_files]}
    for condition in conditions():
        records, tally = load_responses(condition, items)
        result = outcomes(items, records)
        row = {"checks": tally}
        for rule, by_item in result.items():
            row[rule] = {k: {"correct": sum(by_item[i] for i in ids), "share": sum(by_item[i] for i in ids) / len(ids)}
                         for k, ids in subsets.items()}
        out["conditions"][condition["name"]] = row
        r = row["identity"]
        print(f"{condition['name']:28s} all={r['all']['share']:.4f} noRAN2dep={r['withoutScriptless']['share']:.4f} "
              f"noDep={r['withoutAnyReview']['share']:.4f} dep={r['onlyDependent']['correct']}/{len(dependent)}", flush=True)
    (ROOT / args.out).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
