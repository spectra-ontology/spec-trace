#!/usr/bin/env python3
"""보완 주기의 조건을 한 표로 채점한다: 실행 평균, 군집 부트스트랩 구간, 세션까지 다시 뽑는 구간, 조건 사이의 차이.

모델 호출과 데이터베이스 질의는 없다. 저장된 응답을 `score_meeting_spelling_sensitivity.py` 의 세 규칙
(`recorded` · `same_meeting` · `literal`)으로 채점하고, 분석 계획(`final/supplement_cycle/analysis_plan.json`)이
정한 대로 35개 (작업반, 종류) 군집을 씨앗 20261112 로 10,000번 다시 뽑는다. 두 번째 구간은
`bootstrap_with_run_resampling.py` 와 같은 방식으로 세션 무리마다 실행 수만큼 세션을 복원 추출한다
(질의 작성은 작업반, 도구를 쓰는 풀이는 작업반의 분할이 세션 무리다).

조건과 실행 목록
- 질의 작성(Cypher · SQL): `query_writers/summary_ten_runs.json` 의 열 실행(첫 질의와 보수 라운드).
- 메타데이터 포함 전문 검색: 기존 세 실행.
- 본문만 보이는 전문 검색: 기존 실행 A 와 새 실행 B · C.
- 원색인 검색 · 밀집 검색 도구: 새 실행 A · B.
- 한 번 실행한 고정 문맥 풀이(밀집 상위 8 · 식별자 따라가기): 접근 방식 × 독자 표의 로컬 독자 행.

실행 폴더가 없는 조건은 `--allow-missing` 을 줄 때만 건너뛰고 건너뛴 목록을 출력에 적는다.

사용: python3 analyze_supplement_cycle.py [--allow-missing] [--out <json>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

import score_meeting_spelling_sensitivity as sens

ROOT = sens.ROOT
SUP = f"{sens.TRACK}/final/supplement_cycle"
DEFAULT_OUT = f"{SUP}/analysis/summary.json"
PLAN = f"{SUP}/analysis_plan.json"
TEN_RUNS = f"{SUP}/query_writers/summary_ten_runs.json"
PARTS = f"{sens.TRACK}/chain_eval/text_search_packets_full/parts"
RUN_SEED = 20261113
COLLECTED = {
    "text_search_text_only": {run: f"{SUP}/text_only_agent/{run}/collected/{{wg}}_text_only_claude_subagent.jsonl"
                              for run in ("runB", "runC")},
    "raw_index": {run: f"{SUP}/raw_agent/{run}/collected/{{wg}}_raw_index_claude_subagent.jsonl"
                  for run in ("runA", "runB")},
    "dense_tool": {run: f"{SUP}/dense_agent/{run}/collected/{{wg}}_dense_tool_claude_subagent.jsonl"
                   for run in ("runA", "runB")},
    "dense_tool_capped": {
        "runA": f"{SUP}/dense_capped_agent/runA/collected/{{wg}}_dense_tool_capped_claude_subagent.jsonl"},
}
FIXED_CONTEXT = ("dense_llama3_1_8b", "dense_qwen2_5_14b", "identifier_raw_source_llama3_1_8b",
                 "identifier_raw_source_qwen2_5_14b", "identifier_hopkey_llama3_1_8b", "identifier_hopkey_qwen2_5_14b")
COMPARISONS = (("text_search", "text_search_text_only"), ("text_search", "raw_index"), ("text_search", "dense_tool"),
               ("dense_tool", "raw_index"), ("dense_tool", "dense_tool_capped"),
               ("text_search", "dense_tool_capped"), ("dense_tool_capped", "dense_qwen2_5_14b"),
               ("text_search_text_only", "raw_index"),
               ("text_search", "claude_text2cypher"), ("text_search", "claude_text2sql"),
               ("claude_text2cypher", "claude_text2sql"),
               ("claude_text2cypher_repaired", "claude_text2sql_repaired"),
               ("dense_tool", "dense_qwen2_5_14b"), ("text_search", "identifier_hopkey_qwen2_5_14b"),
               ("raw_index", "identifier_raw_source_qwen2_5_14b"))
DESIGNS = ("clusterOnly", "sessionsAndClusters")
BY_PART = {"text_search", "text_search_text_only", "raw_index", "dense_tool", "dense_tool_capped"}


def percentile(values: np.ndarray) -> list[float]:
    return [round(100 * float(x), 1) for x in np.percentile(values, [2.5, 97.5])]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--allow-missing", action="store_true", help="응답 파일이 없는 실행을 건너뛰고 목록에 적는다")
    parser.add_argument("--out", type=Path, default=ROOT / DEFAULT_OUT)
    args = parser.parse_args()

    items = {item["id"]: item for path in sens.ITEMS
             for item in map(json.loads, (ROOT / path).read_text().splitlines())}
    order = sorted(items)
    answerable = np.array([not items[i]["expectsEmpty"] for i in order])
    cluster_names = sorted({(item["wg"], item["family"]) for item in items.values()})
    if len(cluster_names) != sens.CLUSTERS:
        raise SystemExit(f"군집 수가 계획과 다르다: {len(cluster_names)}")
    cluster_of = np.array([cluster_names.index((items[i]["wg"], items[i]["family"])) for i in order])
    membership = (cluster_of[:, None] == np.arange(sens.CLUSTERS)).astype(float)
    resample = np.random.default_rng(sens.SEED).integers(0, sens.CLUSTERS, size=(sens.RESAMPLES, sens.CLUSTERS))
    kept = sens.separately_recorded_meetings()
    row_keys = {rule: sens.make_row_key(rule, kept) for rule in sens.RULES}

    part_of = {}
    for path in sorted((ROOT / PARTS).glob("*.json")):
        for packet in json.loads(path.read_text())["items"]:
            part_of[packet["id"]] = path.stem
    packet_to_item = {}
    for path in sens.per_wg(sens.TEXT_ROUTES["text_search"]["runA"]):
        for record in map(json.loads, (ROOT / path).read_text().splitlines()):
            packet_to_item[record["packetId"]] = record["id"]
    part_of = {packet_to_item[packet]: part for packet, part in part_of.items()}
    if set(part_of) != set(items):
        raise SystemExit("분할이 문항 전체와 다르다")

    ten = json.loads((ROOT / TEN_RUNS).read_text())
    runs: dict[str, dict[str, list[str]]] = {}
    for method in sens.QUERY_METHODS:
        runs[method] = {r["run"]: r["responses"] for r in ten["primary"]["methods"][method]["runs"]}
    runs["text_search"] = {run: sens.per_wg(sens.TEXT_ROUTES["text_search"][run])
                           for run in sens.RUN_DIRS["text_search"]}
    runs["text_search_text_only"] = {"runA": sens.SINGLE_ROUTES["text_search_text_only"]}
    for method, by_run in COLLECTED.items():
        runs.setdefault(method, {}).update({run: sens.per_wg(pattern) for run, pattern in by_run.items()})
    for method in FIXED_CONTEXT:
        runs[method] = {"single": sens.SINGLE_ROUTES[method]}
    for method in sens.QUERY_METHODS:
        runs[f"{method}_repaired"] = {r["run"]: r["responses"] for r in ten["repaired"]["methods"][method]["runs"]}

    skipped = []
    for method in list(runs):
        for run in list(runs[method]):
            absent = [p for p in runs[method][run] if not (ROOT / p).exists()]
            if absent:
                if not args.allow_missing:
                    raise SystemExit(f"{method}/{run}: 응답 파일이 없다: {absent[0]}")
                skipped.append(f"{method}/{run}")
                del runs[method][run]
        if not runs[method]:
            del runs[method]

    def group(method: str, identifier: str) -> str:
        return part_of[identifier] if method in BY_PART else items[identifier]["wg"]

    exact, unanswered = {}, {}
    for method, by_run in runs.items():
        for run, paths in by_run.items():
            responses, _ = sens.read_responses(paths, items)
            unanswered[(method, run)] = sum(1 for i in order if i not in responses)
            for rule in sens.RULES:
                exact[(method, run, rule)] = np.array(
                    [i in responses and bool(sens.exact(items[i], responses[i].get("rows"), row_keys[rule]))
                     for i in order], dtype=float)

    run_rng = np.random.default_rng(RUN_SEED)
    weights = {}
    for method, by_run in runs.items():
        n = len(by_run)
        groups = sorted({group(method, i) for i in order})
        draws = run_rng.integers(0, n, size=(sens.RESAMPLES, len(groups), n))
        weights[method] = (groups, np.stack([(draws == k).sum(axis=2) for k in range(n)], axis=2))

    def cluster_rates(item_hits: np.ndarray, item_totals: np.ndarray) -> np.ndarray:
        hits, totals = item_hits @ membership, item_totals @ membership
        if hits.ndim == 1:
            return hits[resample].sum(axis=1) / totals[resample].sum(axis=1)
        rows = np.arange(sens.RESAMPLES)[:, None]
        return hits[rows, resample].sum(axis=1) / totals[resample].sum(axis=1)

    report = {"description": __doc__.split("\n")[0], "plan": PLAN,
              "planSha256": hashlib.sha256((ROOT / PLAN).read_bytes()).hexdigest(),
              "items": len(order), "answerableItems": int(answerable.sum()),
              "clusterResamples": {"count": sens.RESAMPLES, "seed": sens.SEED, "clusters": sens.CLUSTERS},
              "sessionResamples": {"seed": RUN_SEED, "sessionGroup": {m: ("working-group part" if m in BY_PART
                                                                        else "working group") for m in runs}},
              "runsSkippedAsMissing": skipped, "methods": {}, "comparisons": []}
    for rule in sens.RULES:
        rates, point = {design: {} for design in DESIGNS}, {}
        for method, by_run in runs.items():
            matrix = np.stack([exact[(method, run, rule)] for run in by_run])
            n = len(by_run)
            totals = np.full(len(order), float(n))
            point[method] = float(matrix.sum() / (n * len(order)))
            rates["clusterOnly"][method] = cluster_rates(matrix.sum(axis=0), totals)
            if n == 1:
                rates["sessionsAndClusters"][method] = rates["clusterOnly"][method]
            else:
                groups, w = weights[method]
                item_group = np.array([groups.index(group(method, i)) for i in order])
                rates["sessionsAndClusters"][method] = cluster_rates(
                    np.einsum("bik,ki->bi", w[:, item_group, :], matrix), totals)
            ans_hits = matrix[:, answerable].sum(axis=1)
            report["methods"].setdefault(method, {})[rule] = {
                "runs": n, "perRunExact": {run: int(row.sum()) for run, row in zip(by_run, matrix)},
                "perRunUnanswered": {run: unanswered[(method, run)] for run in by_run},
                "meanExactCount": round(float(matrix.sum() / n), 1),
                "exactRatePercent": round(100 * point[method], 1),
                "meanAnswerableExact": round(float(ans_hits.mean()), 1),
                "answerableRatePercent": round(100 * float(ans_hits.mean() / answerable.sum()), 1),
                "meanEmptyGoldExact": round(float(matrix[:, ~answerable].sum(axis=1).mean()), 1),
                **{f"{design}95Percent": percentile(rates[design][method]) for design in DESIGNS}}
        for first, second in COMPARISONS:
            if first not in runs or second not in runs:
                continue
            entry = {"rule": rule, "first": first, "second": second,
                     "differencePercent": round(100 * (point[first] - point[second]), 1)}
            for design in DESIGNS:
                low, high = np.percentile(rates[design][first] - rates[design][second], [2.5, 97.5])
                entry[f"{design}95Percent"] = [round(100 * float(low), 1), round(100 * float(high), 1)]
                entry[f"{design}ExcludesZero"] = bool(low > 0 or high < 0)
            report["comparisons"].append(entry)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    print("건너뛴 실행:", skipped)
    for method, by_rule in report["methods"].items():
        for rule in ("recorded", "same_meeting"):
            v = by_rule[rule]
            print(f"{method:38s} {rule:12s} runs={v['runs']} mean={v['meanExactCount']} ({v['exactRatePercent']}%) "
                  f"answerable={v['meanAnswerableExact']} ({v['answerableRatePercent']}%) "
                  f"cluster={v['clusterOnly95Percent']} session={v['sessionsAndClusters95Percent']}")
    for entry in report["comparisons"]:
        if entry["rule"] != "literal":
            print(entry)


if __name__ == "__main__":
    main()
