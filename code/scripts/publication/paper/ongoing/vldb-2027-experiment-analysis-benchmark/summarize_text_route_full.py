"""전문 검색 두 경로(메타데이터 포함 · 본문만)를 전 문항에서 집계하고 질의 작성 풀이와 비교한다 (모델 호출 없음).

채점은 `score_chain_eval.score` 의 정확 일치다. 구간과 비교는 `summarize_repeated_runs.py` 와 같은 규칙을 쓴다.
군집은 (작업반, 문항 종류) 35개이고, 같은 씨앗으로 한 번 뽑은 군집 재표본 행렬을 모든 풀이와 비교에 함께 쓴다.

메타데이터 포함 경로는 실행 계획(chain_eval/text_search_full_runC/run_plan.json)이 정한 실행 A · B · C 를
문항마다 모은 실행 평균으로 본다(질의 작성 풀이의 분석 계획과 같은 규칙). 실행 계획의 실행 목록과
이 파일의 실행 목록이 다르거나 한 실행이라도 응답 파일이 없으면 집계하지 않는다.
본문만 경로는 실행 하나다. 질의 작성 풀이는 그 요약(final/repeated_runs/summary_runs_A_to_E.json)의
`primary` 에 적힌 실행을 모두 모아(`runsPooled`) 한 풀이로 본다.

내는 것.
- results.<경로>.runs.<실행>: 정확 일치 수(전체 · 정답 있는 문항 · 빈 정답 문항), 정답 있는 문항의 Wilson 95% 구간,
  빈 정답 문항에 행을 낸 수(fabricated), 정답 있는 문항에서 빈 응답을 낸 수, 정답 있는 문항의 틀린 갈래
  (superset · subset · partial · disjoint · empty), 짝 거절 지표 D · Dₓ, 문항마다의 검색 횟수(trace 의 `commands` 가운데
  도구 도움말 `--help` 를 뺀 호출 수. trace 의 `searches` 는 도움말까지 센 호출 수다),
  메타데이터 포함 경로는 틀린 문항 목록(id · 종류 · 갈래 · 정답 행 수 · 응답 행 수)까지.
- results.<경로>: 실행 평균 정확 일치 수와 최소 · 최대, 실행을 모은 전체 정확 일치 비율과 그 군집 부트스트랩 95% 구간,
  실행마다 검색 횟수를 모은 중앙값.
- paired: 메타데이터 포함 경로(실행 평균)와 본문만 경로의 비율 차 · 군집 부트스트랩 구간, 실행마다의 한쪽만 맞힌 수와
  정확 McNemar 양측 p, 메타데이터 포함 경로와 질의 작성 풀이(실행 평균)의 군집 부트스트랩 비율 차 구간.
- `…Percent` 칸: 같은 비율 차와 구간을 원값에서 한 번만 반올림한 백분율(소수 한 자리). 원고에 옮기는 값이다.

사용: python3 summarize_text_route_full.py [--runs runA,runB] [--out <json>]
`--runs` 는 계획보다 적은 실행으로 미리 보는 용도이고, 이때는 기본 출력 경로에 쓰지 않는다.
저장소 루트에서 `PYTHONPATH=scripts/common:scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark` 로 실행한다.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from pathlib import Path

import numpy as np

from score_chain_eval import cell_key, score

ROOT = next(path for path in Path(__file__).resolve().parents if (path / ".git").exists())
TRACK = "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
ITEMS = (f"{TRACK}/integration/items_final/gate/core/chain_items_admitted.jsonl",
         f"{TRACK}/integration/items_final/gate/ran5/chain_items_admitted.jsonl")
WGS = ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5")
RUN_PLAN = f"{TRACK}/chain_eval/text_search_full_runC/run_plan.json"
RUN_DIRS = {
    "text_search": {"runA": "text_search_full", "runB": "text_search_full_runB", "runC": "text_search_full_runC"},
    "text_search_text_only": {"runA": "text_only_full"},
}
ANSWERS = {
    "text_search": "{wg}_text_search_claude_subagent.jsonl",
    "text_search_text_only": "{wg}_text_search_text_only_claude_subagent.jsonl",
}
ROUTES = {route: {run: f"{TRACK}/chain_eval/{folder}/{ANSWERS[route]}" for run, folder in runs.items()}
          for route, runs in RUN_DIRS.items()}
TRACES = {route: {run: f"{TRACK}/chain_eval/{folder}/solver_logs" for run, folder in runs.items()}
          for route, runs in RUN_DIRS.items()}
QUERY_SUMMARY = f"{TRACK}/final/repeated_runs/summary_runs_A_to_E.json"
QUERY_METHODS = ("claude_text2cypher", "claude_text2sql")
DEFAULT_OUT = f"{TRACK}/chain_eval/text_search_full/route_comparison.json"
RESAMPLES = 10_000
SEED = 20261112
CLUSTERS = 35


def wilson(hits: int, n: int, z: float = 1.959963984540054) -> list[float]:
    centre = (hits + z * z / 2) / (n + z * z)
    half = z * math.sqrt(hits * (n - hits) / n + z * z / 4) / (n + z * z)
    return [round(100 * (centre - half), 1), round(100 * (centre + half), 1)]


def percent(values) -> list[float]:
    """비율을 원값에서 한 번만 반올림해 백분율 소수 한 자리로 낸다.

    원고는 이 값을 그대로 옮긴다. 네 자리로 반올림해 둔 비율을 다시 반올림하면
    넷째 자리가 5인 값에서 끝자리가 하나 올라가므로, 백분율은 반드시 원값에서 만든다.
    """
    return [float(Decimal(repr(100 * float(x))).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)) for x in values]


def mcnemar_exact(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, k) for k in range(0, min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def miss_kind(item: dict, rows) -> str:
    if rows is None:
        return "unreadable"
    if not rows:
        return "empty"
    width = len(item["fields"])
    gold = {tuple(cell_key(cell) for cell in row[:width]) for row in item["gold"]}
    got = {tuple(cell_key(cell) for cell in row[:width]) for row in rows}
    if gold < got:
        return "superset"
    if got < gold:
        return "subset"
    return "partial" if gold & got else "disjoint"


def read_responses(paths: list[str], items: dict) -> tuple[dict, int]:
    responses, stale = {}, 0
    for path in paths:
        for line in (ROOT / path).open():
            response = json.loads(line)
            item = items[response["id"]]
            if response.get("questionSha256") not in (None, hashlib.sha256(item["question"].encode()).hexdigest()):
                stale += 1
                continue
            responses[response["id"]] = response
    return responses, stale


def abstention(items: dict, responses: dict, outcome: dict) -> dict:
    """빈 정답 문항(`pack_lookup_empty`)과 같은 질문 틀의 정답 있는 문항(`pack_lookup`)의 짝 거절 지표.

    D = 빈 정답에서 빈 응답 비율 − 짝 문항에서 빈 응답 비율, C = 빈 정답에서 빈 응답 비율 − 짝 문항 오답 비율.
    """
    empty = [i for i, item in items.items() if item["family"] == "pack_lookup_empty"]
    paired = [i for i, item in items.items() if item["family"] == "pack_lookup"]
    on_empty = sum(responses.get(i, {}).get("rows") == [] for i in empty)
    on_paired = sum(responses.get(i, {}).get("rows") == [] for i in paired)
    exact_paired = sum(outcome[i] for i in paired)
    e0, ep, xp = Fraction(on_empty, len(empty)), Fraction(on_paired, len(paired)), Fraction(exact_paired, len(paired))
    return {"onEmpty": on_empty, "emptyItems": len(empty), "onAnswerable": on_paired, "answerableItems": len(paired),
            "exactOnAnswerable": exact_paired, "D": round(float(e0 - ep), 4), "C": round(float(e0 - (1 - xp)), 4)}


def searches(trace_dir: Path) -> list[int]:
    counts = []
    for wg in WGS:
        for path in sorted(trace_dir.glob(f"{wg}_part*_trace.jsonl")):
            counts += [sum("--help" not in command.split() for command in json.loads(line)["commands"])
                       for line in path.read_text().splitlines() if line.strip()]
    return counts


def search_block(counts: list[int]) -> dict:
    return {"items": len(counts), "total": sum(counts), "median": statistics.median(counts),
            "max": max(counts), "min": min(counts)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--runs", help="메타데이터 포함 경로에서 모을 실행(쉼표 구분). 기본은 실행 계획의 전부")
    parser.add_argument("--out", type=Path, default=ROOT / DEFAULT_OUT)
    args = parser.parse_args()

    planned = json.loads((ROOT / RUN_PLAN).read_text())["runs"]
    if planned != list(RUN_DIRS["text_search"]):
        raise SystemExit(f"실행 계획의 실행 목록과 이 파일의 실행 목록이 다르다: {planned} != {list(RUN_DIRS['text_search'])}")
    chosen = args.runs.split(",") if args.runs else planned
    if chosen != planned and args.out.resolve() == (ROOT / DEFAULT_OUT).resolve():
        raise SystemExit("계획보다 적은 실행은 기본 출력 경로에 쓰지 않는다(--out 을 따로 준다)")
    runs_of = {"text_search": chosen, "text_search_text_only": list(RUN_DIRS["text_search_text_only"])}
    for route, runs in runs_of.items():
        for run in runs:
            absent = [wg for wg in WGS if not (ROOT / ROUTES[route][run].format(wg=wg)).exists()]
            if absent:
                raise SystemExit(f"{route} {run} 의 응답 파일이 없다: {absent}")

    items = {item["id"]: item for path in ITEMS for item in map(json.loads, (ROOT / path).read_text().splitlines())}
    cluster_names = sorted({(item["wg"], item["family"]) for item in items.values()})
    if len(cluster_names) != CLUSTERS:
        raise SystemExit(f"군집 수가 계획과 다르다: {len(cluster_names)}")
    index = {name: c for c, name in enumerate(cluster_names)}
    cluster_of = {identifier: index[(item["wg"], item["family"])] for identifier, item in items.items()}
    resample = np.random.default_rng(SEED).integers(0, CLUSTERS, size=(RESAMPLES, CLUSTERS))
    answerable = [i for i, item in items.items() if not item["expectsEmpty"]]
    empty_gold = [i for i, item in items.items() if item["expectsEmpty"]]

    def cluster_rate(exact_by_id: dict[str, list[bool]]) -> tuple[float, np.ndarray]:
        hits, totals = np.zeros(CLUSTERS), np.zeros(CLUSTERS)
        for identifier, outcomes in exact_by_id.items():
            hits[cluster_of[identifier]] += sum(outcomes)
            totals[cluster_of[identifier]] += len(outcomes)
        return float(hits.sum() / totals.sum()), hits[resample].sum(axis=1) / totals[resample].sum(axis=1)

    exact, rates, results = {}, {}, {}
    for route, runs in runs_of.items():
        exact[route], blocks, all_searches = {}, {}, []
        for run in runs:
            responses, stale = read_responses([ROUTES[route][run].format(wg=wg) for wg in WGS], items)
            outcome = {identifier: bool(identifier in responses and responses[identifier].get("rows") is not None
                                        and score(item["gold"], responses[identifier]["rows"])["exact"])
                       for identifier, item in items.items()}
            exact[route][run] = outcome
            kinds: dict[str, int] = {}
            for identifier in answerable:
                if not outcome[identifier]:
                    kind = miss_kind(items[identifier], responses.get(identifier, {}).get("rows"))
                    kinds[kind] = kinds.get(kind, 0) + 1
            hits_answerable = sum(outcome[i] for i in answerable)
            block = {
                "responses": ROUTES[route][run],
                "missing": len(set(items) - set(responses)), "staleQuestion": stale,
                "exact": {"all": sum(outcome.values()), "answerable": hits_answerable,
                          "emptyGold": sum(outcome[i] for i in empty_gold)},
                "answerableWilson95Percent": wilson(hits_answerable, len(answerable)),
                "fabricatedOnEmptyGold": sum(bool(responses.get(i, {}).get("rows")) for i in empty_gold),
                "emptyOnAnswerable": sum(responses.get(i, {}).get("rows") == [] for i in answerable),
                "answerableMissKinds": dict(sorted(kinds.items())),
                "abstention": abstention(items, responses, outcome),
            }
            trace_dir = ROOT / TRACES[route][run]
            if trace_dir.is_dir() and any(trace_dir.glob("*_trace.jsonl")):
                counts = searches(trace_dir)
                block["searchesPerItem"] = search_block(counts)
                all_searches += counts
            if route == "text_search":
                block["misses"] = [
                    {"id": identifier, "family": items[identifier]["family"],
                     "kind": ("fabricated" if items[identifier]["expectsEmpty"]
                              else miss_kind(items[identifier], responses[identifier].get("rows"))),
                     "goldRows": len(items[identifier]["gold"]),
                     "responseRows": len(responses[identifier]["rows"] or [])}
                    for identifier in items if not outcome[identifier]]
            blocks[run] = block
        point, rate = cluster_rate({i: [exact[route][run][i] for run in runs] for i in items})
        rates[route] = (point, rate)
        counts_of = {part: [blocks[run]["exact"][part] for run in runs] for part in ("all", "answerable", "emptyGold")}
        results[route] = {
            "runsPooled": runs,
            "items": {"all": len(items), "answerable": len(answerable), "emptyGold": len(empty_gold)},
            "meanExact": {part: round(sum(values) / len(values), 4) for part, values in counts_of.items()},
            "exactRange": {part: [min(values), max(values)] for part, values in counts_of.items()},
            "meanExactRate": round(point, 4), "meanExactRatePercent": percent([point])[0],
            "allClusterBootstrap95": [round(float(x), 4) for x in np.percentile(rate, [2.5, 97.5])],
            "allClusterBootstrap95Percent": percent(np.percentile(rate, [2.5, 97.5])),
            "runs": blocks,
        }
        if all_searches:
            results[route]["searchesPerItemAllRuns"] = search_block(all_searches)

    first_runs = runs_of["text_search"]
    (only_run,) = runs_of["text_search_text_only"]
    second = exact["text_search_text_only"][only_run]
    per_run = []
    for run in first_runs:
        first = exact["text_search"][run]
        only_first = sum(first[i] and not second[i] for i in items)
        only_second = sum(second[i] and not first[i] for i in items)
        per_run.append({"run": run, "onlyFirstExact": only_first, "onlySecondExact": only_second,
                        "mcnemarExactP": float(f"{mcnemar_exact(only_first, only_second):.3g}")})
    difference = rates["text_search"][1] - rates["text_search_text_only"][1]
    gap = rates["text_search"][0] - rates["text_search_text_only"][0]
    paired = [{"first": "text_search", "firstRuns": first_runs, "second": "text_search_text_only",
               "secondRuns": [only_run], "perFirstRun": per_run,
               "exactRateDifference": round(gap, 4),
               "pairedClusterBootstrap95": [round(float(x), 4) for x in np.percentile(difference, [2.5, 97.5])],
               "exactRateDifferencePercent": percent([gap])[0],
               "pairedClusterBootstrap95Percent": percent(np.percentile(difference, [2.5, 97.5]))}]

    summary = json.loads((ROOT / QUERY_SUMMARY).read_text())
    for method in QUERY_METHODS:
        block = summary["primary"]["methods"][method]
        pooled = [run for run in block["runs"] if run["run"] in block["runsPooled"]]
        by_id: dict[str, list[bool]] = {}
        for run in pooled:
            responses, _ = read_responses(run["responses"], items)
            for identifier, item in items.items():
                rows = responses.get(identifier, {}).get("rows")
                by_id.setdefault(identifier, []).append(bool(rows is not None and score(item["gold"], rows)["exact"]))
        point, rate = cluster_rate(by_id)
        difference = rates["text_search"][1] - rate
        low, high = (round(float(x), 4) for x in np.percentile(difference, [2.5, 97.5]))
        paired.append({"first": "text_search", "firstRuns": first_runs, "second": method,
                       "secondRuns": block["runsPooled"], "secondMeanExactRate": round(point, 4),
                       "exactRateDifference": round(rates["text_search"][0] - point, 4),
                       "pairedClusterBootstrap95": [low, high], "intervalExcludesZero": low > 0 or high < 0,
                       "exactRateDifferencePercent": percent([rates["text_search"][0] - point])[0],
                       "pairedClusterBootstrap95Percent": percent(np.percentile(difference, [2.5, 97.5]))})

    result = {"items": list(ITEMS), "runPlan": RUN_PLAN,
              "routes": {route: {run: ROUTES[route][run] for run in runs} for route, runs in runs_of.items()},
              "querySummary": QUERY_SUMMARY,
              "bootstrap": {"resamples": RESAMPLES, "seed": SEED, "unit": "(wg, family) cluster",
                            "interval": "percentile 95%"},
              "results": results, "paired": paired}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=1) + "\n")
    brief = {route: {**{k: v for k, v in block.items() if k != "runs"},
                     "runs": {run: {k: v for k, v in rb.items() if k != "misses"} for run, rb in block["runs"].items()}}
             for route, block in results.items()}
    print(json.dumps(brief, indent=1))
    print(json.dumps(paired, indent=1))


if __name__ == "__main__":
    main()
