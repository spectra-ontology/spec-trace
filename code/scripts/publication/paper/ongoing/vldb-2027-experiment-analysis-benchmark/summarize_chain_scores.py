"""여러 작업반의 저장된 응답을 풀이(방법·모델)마다 모아 구간 추정과 함께 집계한다 (모델 호출 없음).

채점 규칙은 `score_chain_eval.py` 와 같다(행 비교·bis 회의 표기 맞춤·질문 SHA-256 이 다른 응답 제외).
이 스크립트는 그 위에 다음을 더한다.
- 정확 일치 비율의 Wilson 95% 구간. 작업반·문항 종류·작업반×문항 종류마다 낸다.
- 행 단위 F1 평균의 백분위 부트스트랩 95% 구간(문항을 복원 추출). 전체와 작업반마다 낸다.
- 질문 틀마다의 기권 지표. 문항 종류 이름에서 `_empty` 를 뗀 것을 질문 틀로 본다
  (`pack_lookup_empty` 와 `pack_lookup` 은 같은 질문 틀이다). 빈 정답 문항과 정답 있는 문항이 둘 다 있는
  질문 틀에서만 낸다.
  - onEmpty: 빈 정답 문항에서 빈 응답을 낸 비율. fabricatedOnEmpty: 빈 정답 문항에서 행을 하나 이상 지어낸 비율.
  - onAnswerable: 정답 있는 문항에서 빈 응답을 낸 비율. discrimination = onEmpty − onAnswerable.
  - exactOnAnswerable: 정답 있는 문항의 정확 일치 비율.
  - correctnessAware = onEmpty − (1 − exactOnAnswerable). 정답 있는 문항에서 비우거나 틀린 답을 모두 벌점으로
    본다. 모두 비우는 풀이는 0, 모두 맞히는 풀이는 1, 늘 틀린 행을 지어내는 풀이는 −1 이다.
  읽을 수 없는 응답은 빈 응답으로도 지어낸 응답으로도 세지 않는다.
- 모든 문항에서 빈 응답 수를 빈 정답 문항과 정답 있는 문항으로 나눠 센다.
- 정답 있는 문항의 응답을 일곱 갈래로 나눈다(`errorTypes`, 전체와 문항 종류마다). exact · empty(빈 응답) ·
  superset(정답 행을 모두 담고 다른 행도 냄) · subset(낸 행이 모두 정답이지만 일부 정답 행이 빠짐) ·
  partial(맞은 행과 틀린 행이 섞임) · disjoint(맞은 행이 없음) · unreadable.
- 두 풀이가 함께 답한 문항에서 정확 일치의 짝 비교. 한쪽만 맞힌 문항 수(b, c), 정확 McNemar 양측 p 값,
  정확 일치 비율 차의 짝 부트스트랩 95% 구간.

부트스트랩 반복은 10,000회, 씨앗은 `--seed` 로 정한다. 백분위 구간의 끝점이 반복 수에 따라 흔들리는 폭을
2.5% 분위수의 몬테카를로 표준오차로 따지면 10,000회에서 문항 수 수백 개의 비율 차에 대해 0.002 안팎이라
보고 자릿수(소수 셋째 자리)보다 작다.

사용: python3 summarize_chain_scores.py --items <jsonl> [...] --responses <jsonl> [...] --out <json> [--seed N]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from score_chain_eval import score

Z = 1.959963984540054
RESAMPLES = 10_000


def wilson(hit: int, n: int) -> list[float] | None:
    if not n:
        return None
    p = hit / n
    centre = (p + Z * Z / (2 * n)) / (1 + Z * Z / n)
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / (1 + Z * Z / n)
    return [round(centre - half, 4), round(centre + half, 4)]


def bootstrap_mean(values: list[float], rng: np.random.Generator) -> list[float] | None:
    if len(values) < 2:
        return None
    data = np.asarray(values, dtype=float)
    means = data[rng.integers(0, len(data), size=(RESAMPLES, len(data)))].mean(axis=1)
    return [round(float(np.percentile(means, 2.5)), 4), round(float(np.percentile(means, 97.5)), 4)]


def mcnemar_exact(b: int, c: int) -> float:
    n = b + c
    if not n:
        return 1.0
    tail = sum(math.comb(n, k) for k in range(min(b, c) + 1)) / 2 ** n
    return float(f"{min(1.0, 2 * tail):.3g}")


def proportion(scores: list[dict], rng: np.random.Generator, with_f1: bool) -> dict:
    n = len(scores)
    exact = sum(s["exact"] for s in scores)
    out = {"n": n, "exact": exact, "exactRate": round(exact / n, 4) if n else None, "exactWilson95": wilson(exact, n),
           "unreadable": sum(s["unreadable"] for s in scores)}
    if with_f1:
        f1 = [s["f1"] for s in scores]
        out["f1"] = round(sum(f1) / n, 4) if n else None
        out["f1Bootstrap95"] = bootstrap_mean(f1, rng)
    return out


def abstention_by_template(records: list[tuple[dict, object, dict]]) -> list[dict]:
    templates: dict[str, list[tuple[dict, object, dict]]] = collections.defaultdict(list)
    for item, rows, result in records:
        templates[item["family"].removesuffix("_empty")].append((item, rows, result))
    report = []
    for template, group in sorted(templates.items()):
        empty = [(rows, result) for item, rows, result in group if not item["gold"]]
        answerable = [(rows, result) for item, rows, result in group if item["gold"]]
        if not empty or not answerable:
            continue
        on_empty = sum(rows is not None and not rows for rows, _ in empty)
        fabricated = sum(bool(rows) for rows, _ in empty)
        on_answerable = sum(rows is not None and not rows for rows, _ in answerable)
        exact_answerable = sum(result["exact"] for _, result in answerable)
        e_rate, a_rate, x_rate = on_empty / len(empty), on_answerable / len(answerable), exact_answerable / len(answerable)
        report.append({"template": template, "emptyItems": len(empty), "answerableItems": len(answerable),
                       "onEmpty": on_empty, "fabricatedOnEmpty": fabricated,
                       "unreadableOnEmpty": sum(rows is None for rows, _ in empty),
                       "onAnswerable": on_answerable, "exactOnAnswerable": exact_answerable,
                       "discrimination": round(e_rate - a_rate, 4),
                       "correctnessAware": round(e_rate - (1 - x_rate), 4)})
    return report


def error_type(rows, result: dict) -> str:
    if result["unreadable"]:
        return "unreadable"
    if result["exact"]:
        return "exact"
    if not rows:
        return "empty"
    if result["recall"] == 1:
        return "superset"
    if result["precision"] == 1:
        return "subset"
    return "partial" if result["f1"] > 0 else "disjoint"


def error_types(records: list[tuple[dict, object, dict]]) -> dict:
    answerable = [(item, rows, result) for item, rows, result in records if item["gold"]]
    by_family: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for item, rows, result in answerable:
        by_family[item["family"]][error_type(rows, result)] += 1
    return {"all": dict(sum(by_family.values(), collections.Counter())),
            "family": {family: dict(counts) for family, counts in sorted(by_family.items())}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, nargs="+", required=True)
    parser.add_argument("--responses", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261112)
    args = parser.parse_args()
    rng = np.random.default_rng(args.seed)
    items = {item["id"]: item for path in args.items for item in map(json.loads, path.read_text().splitlines())}
    digest = {identifier: hashlib.sha256(item["question"].encode()).hexdigest() for identifier, item in items.items()}

    runs: dict[tuple[str, str], dict[str, dict]] = collections.defaultdict(dict)
    files: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
    stale: collections.Counter = collections.Counter()
    for path in args.responses:
        for record in map(json.loads, path.read_text().splitlines()):
            run = (record["method"], record["model"])
            if str(path) not in files[run]:
                files[run].append(str(path))
            if record["id"] not in items:
                continue
            if record.get("questionSha256") != digest[record["id"]]:
                stale[run] += 1
                continue
            if record["id"] in runs[run]:
                raise SystemExit(f"{run}: 같은 문항 {record['id']} 의 응답이 두 번 있다")
            runs[run][record["id"]] = record

    report, exact_by_run = [], {}
    no_current = [{"method": run[0], "model": run[1], "responses": files[run], "staleQuestion": stale[run]}
                  for run in sorted(files) if not runs.get(run)]
    for run, answered in sorted((run, answered) for run, answered in runs.items() if answered):
        wgs = sorted({record["wg"] for record in answered.values()})
        scope = [item for item in items.values() if item["wg"] in wgs]
        records = [(item, answered[item["id"]].get("rows"), score(item["gold"], answered[item["id"]].get("rows")))
                   for item in scope if item["id"] in answered]
        exact_by_run[run] = {item["id"]: result["exact"] for item, _, result in records}
        groups: dict[tuple[str, ...], list[dict]] = collections.defaultdict(list)
        for item, _, result in records:
            for group in (("all",), ("wg", item["wg"]), ("family", item["family"]), ("wgFamily", item["wg"], item["family"])):
                groups[group].append(result)
        empty_answers = collections.Counter(
            ("emptyGold" if not item["gold"] else "answerableGold") for item, rows, _ in records if rows is not None and not rows)
        report.append({
            "method": run[0], "model": run[1], "responses": files[run], "wgs": wgs,
            "missing": sum(item["id"] not in answered for item in scope), "staleQuestion": stale[run],
            "emptyAnswers": {"onEmptyGold": empty_answers["emptyGold"], "onAnswerableGold": empty_answers["answerableGold"],
                             "emptyGoldItems": sum(not item["gold"] for item, _, _ in records),
                             "answerableGoldItems": sum(bool(item["gold"]) for item, _, _ in records)},
            "errorTypes": error_types(records),
            "abstentionByTemplate": abstention_by_template(records),
            "abstentionByWgTemplate": {wg: abstention_by_template([r for r in records if r[0]["wg"] == wg]) for wg in wgs},
            "groups": [{"by": key[0], "value": "/".join(key[1:]) or "all",
                        **proportion(scores, rng, with_f1=key[0] in ("all", "wg"))}
                       for key, scores in sorted(groups.items())],
        })

    paired = []
    names = sorted(exact_by_run)
    for i, first in enumerate(names):
        for second in names[i + 1:]:
            common = sorted(set(exact_by_run[first]) & set(exact_by_run[second]))
            if not common:
                continue
            a = np.asarray([exact_by_run[first][c] for c in common], dtype=float)
            b = np.asarray([exact_by_run[second][c] for c in common], dtype=float)
            only_first, only_second = int(((a == 1) & (b == 0)).sum()), int(((a == 0) & (b == 1)).sum())
            diffs = (a - b)[rng.integers(0, len(common), size=(RESAMPLES, len(common)))].mean(axis=1)
            paired.append({"first": "/".join(first), "second": "/".join(second), "commonItems": len(common),
                           "firstExact": int(a.sum()), "secondExact": int(b.sum()),
                           "onlyFirstExact": only_first, "onlySecondExact": only_second,
                           "mcnemarExactP": mcnemar_exact(only_first, only_second),
                           "exactRateDifference": round(float((a - b).mean()), 4),
                           "differenceBootstrap95": [round(float(np.percentile(diffs, 2.5)), 4),
                                                     round(float(np.percentile(diffs, 97.5)), 4)]})

    args.out.write_text(json.dumps({
        "items": [str(path) for path in args.items], "itemCount": len(items), "seed": args.seed, "resamples": RESAMPLES,
        "runs": report, "runsWithoutCurrentResponses": no_current, "paired": paired}, ensure_ascii=False, indent=2) + "\n")
    for run in no_current:
        print("no current-question responses:", run["method"], run["model"], "stale", run["staleQuestion"])
    for run in report:
        overall = next(group for group in run["groups"] if group["by"] == "all")
        print(run["method"], run["model"], run["wgs"], "missing", run["missing"], "stale", run["staleQuestion"],
              overall["exact"], "/", overall["n"], overall["exactWilson95"], run["abstentionByTemplate"])


if __name__ == "__main__":
    main()
