#!/usr/bin/env python3
"""여러 번 실행한 풀이의 구간을 풀이 세션까지 다시 뽑는 두 단계 부트스트랩으로 다시 내고, 군집만 다시 뽑는 주 구간과 나란히 적는다.

모델 호출과 데이터베이스 질의는 없다. 저장된 응답과 문항을 `score_meeting_spelling_sensitivity.py` 와 같은 규칙
(`recorded` · `same_meeting` · `literal`)과 같은 실행 목록으로 다시 채점한다.

풀이 세션은 응답을 낸 서로 다른 하위 에이전트 하나다(`chain_eval/subagent_model_provenance.json`).
질의 작성은 (작업반, 실행)마다 한 세션이 그 작업반의 모든 문항을 쓰고(언어마다 25세션),
메타데이터 포함 전문 검색은 (작업반, 3분할, 실행)마다 한 세션이 분할 파일의 문항에 답한다(실행마다 15세션,
분할은 `text_search_packets_full/parts/` 가 정하고 세 실행이 같은 분할을 읽는다).

- 주 구간(`clusterOnly`): 35개 (작업반, 종류) 군집을 복원 추출하고, 뽑힌 군집의 모든 문항에서 모든 실행의 결과를 더한다.
  씨앗 20261112 의 다시 뽑기 표 10,000행을 그대로 쓰므로 `meeting_spelling_sensitivity/summary.json` 의 구간과 같아야 한다.
- 두 단계 구간(`sessionsAndClusters`): 다시 뽑기마다 세션 무리(질의 작성은 작업반, 전문 검색은 작업반의 분할)별로
  그 무리의 실행 수만큼 세션을 복원 추출하고, 같은 군집 다시 뽑기 행 위에서 뽑힌 세션의 결과를 더한다.
  세션 다시 뽑기는 씨앗 20261113 의 한 생성기에서 풀이 순서대로 따로 뽑는다(서로 다른 풀이의 세션은 짝이 없다).
- 비교값(`runLabelsAndClusters`): 같은 실행 글자를 단 세션을 모든 작업반에 걸쳐 한 덩어리로 묶어 실행 글자를
  다시 뽑는다. 서로 다른 에이전트를 묶는 가정이라 설계 단위는 아니며, 세션 단위 구간과 나란히 보이려고 남긴다.
- 한 번 실행한 풀이는 세션을 다시 뽑지 않는다. 비교는 원고의 네 쌍과 보수 라운드(실행 오류를 원 작성자에게 한 번
  돌려준 응답, `repeated_runs/summary_runs_A_to_E.json` 의 `repaired`)의 Cypher − SQL 한 쌍이고, 구간은 모두 백분위 95% 이다.
  보수 라운드는 같은 세션이 고쳐 쓴 응답이라 세션 무리가 첫 실행과 같다(작업반).

사용: python3 bootstrap_with_run_resampling.py [--out <json>]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

import score_meeting_spelling_sensitivity as sens

ROOT = sens.ROOT
DEFAULT_OUT = f"{sens.TRACK}/final/run_resampling_bootstrap/summary.json"
PARTS = f"{sens.TRACK}/chain_eval/text_search_packets_full/parts"
PROVENANCE = f"{sens.TRACK}/chain_eval/subagent_model_provenance.json"
RUN_SEED = 20261113
COMPARISONS = (("text_search", "text_search_text_only"), ("text_search", "claude_text2cypher"),
               ("text_search", "claude_text2sql"), ("claude_text2cypher", "claude_text2sql"),
               ("claude_text2cypher_repaired", "claude_text2sql_repaired"))
DESIGNS = ("clusterOnly", "sessionsAndClusters", "runLabelsAndClusters")


def percentile(values: np.ndarray) -> list[float]:
    return [round(100 * float(x), 1) for x in np.percentile(values, [2.5, 97.5])]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, default=ROOT / DEFAULT_OUT)
    args = parser.parse_args()

    items = {item["id"]: item for path in sens.ITEMS
             for item in map(json.loads, (ROOT / path).read_text().splitlines())}
    order = sorted(items)
    cluster_names = sorted({(item["wg"], item["family"]) for item in items.values()})
    if len(cluster_names) != sens.CLUSTERS:
        raise SystemExit(f"군집 수가 계획과 다르다: {len(cluster_names)}")
    cluster_of = np.array([cluster_names.index((items[i]["wg"], items[i]["family"])) for i in order])
    membership = (cluster_of[:, None] == np.arange(sens.CLUSTERS)).astype(float)       # items x clusters
    resample = np.random.default_rng(sens.SEED).integers(0, sens.CLUSTERS, size=(sens.RESAMPLES, sens.CLUSTERS))
    kept = sens.separately_recorded_meetings()
    row_keys = {rule: sens.make_row_key(rule, kept) for rule in sens.RULES}

    part_of_packet = {}
    for path in sorted((ROOT / PARTS).glob("*.json")):
        for item in json.loads(path.read_text())["items"]:
            if item["id"] in part_of_packet:
                raise SystemExit(f"한 문항이 두 분할에 있다: {item['id']}")
            part_of_packet[item["id"]] = path.stem
    packet_of = {}
    for run in sens.RUN_DIRS["text_search"]:
        for path in sens.per_wg(sens.TEXT_ROUTES["text_search"][run]):
            for record in map(json.loads, (ROOT / path).read_text().splitlines()):
                if packet_of.setdefault(record["id"], record["packetId"]) != record["packetId"]:
                    raise SystemExit(f"실행마다 문항의 패킷 ID 가 다르다: {record['id']}")
    if set(packet_of) != set(items) or set(packet_of.values()) != set(part_of_packet):
        raise SystemExit("전문 검색 분할이 문항 전체와 다르다")
    part_of = {identifier: part_of_packet[packet] for identifier, packet in packet_of.items()}

    summary = json.loads((ROOT / sens.QUERY_SUMMARY).read_text())
    planned = json.loads((ROOT / sens.RUN_PLAN).read_text())["runs"]
    if planned != list(sens.RUN_DIRS["text_search"]):
        raise SystemExit(f"실행 계획의 실행 목록과 전문 검색 실행 목록이 다르다: {planned}")
    runs = {}
    for method in sens.QUERY_METHODS:
        block = summary["primary"]["methods"][method]
        pooled = [r for r in block["runs"] if r["run"] in block["runsPooled"]]
        if [r["run"] for r in pooled] != list(block["runsPooled"]):
            raise SystemExit(f"{method}: 모을 실행의 응답 목록이 실행 목록과 다르다")
        runs[method] = {r["run"]: r["responses"] for r in pooled}
    runs["text_search"] = {run: sens.per_wg(sens.TEXT_ROUTES["text_search"][run]) for run in planned}
    runs["text_search_text_only"] = {"runA": sens.SINGLE_ROUTES["text_search_text_only"]}
    # 보수 라운드는 끝에 붙인다: 세션 다시 뽑기 생성기를 풀이 순서대로 쓰므로 앞 풀이의 뽑기가 그대로 남는다.
    for method in sens.QUERY_METHODS:
        block = summary["repaired"]["methods"][method]
        if [r["run"] for r in block["runs"]] != list(runs[method]):
            raise SystemExit(f"{method}: 보수 라운드의 실행 목록이 첫 실행과 다르다")
        runs[f"{method}_repaired"] = {r["run"]: r["responses"] for r in block["runs"]}
    session_group = {"claude_text2cypher": lambda i: items[i]["wg"], "claude_text2sql": lambda i: items[i]["wg"],
                     "claude_text2cypher_repaired": lambda i: items[i]["wg"],
                     "claude_text2sql_repaired": lambda i: items[i]["wg"],
                     "text_search": lambda i: part_of[i], "text_search_text_only": lambda i: part_of[i]}

    provenance = json.loads((ROOT / PROVENANCE).read_text())["conditions"]
    sessions_seen = {}
    for method, conditions in (("claude_text2cypher", ("text2cypher_runA_runB", "text2cypher_runs_C_to_E")),
                               ("claude_text2sql", ("text2sql_runA_runB", "text2sql_runs_C_to_E"))):
        agents = [(wg, entry["run"], entry["agentId"]) for condition in conditions
                  for wg, entries in provenance[condition].items() for entry in entries]
        if len({a for *_, a in agents}) != len(agents) or len({(w, r) for w, r, _ in agents}) != len(agents):
            raise SystemExit(f"{method}: (작업반, 실행)마다 서로 다른 에이전트 하나가 아니다")
        sessions_seen[method] = len(agents)
    sessions_seen["text_search"] = sum(len({e["agentId"] for entries in provenance[c].values() for e in entries})
                                       for c in ("text_search", "text_search_runB", "text_search_runC"))

    exact = {}
    for method, by_run in runs.items():
        for run, paths in by_run.items():
            responses, _ = sens.read_responses(paths, items)
            for rule in sens.RULES:
                exact[(method, run, rule)] = np.array(
                    [i in responses and bool(sens.exact(items[i], responses[i].get("rows"), row_keys[rule]))
                     for i in order], dtype=float)

    run_rng = np.random.default_rng(RUN_SEED)
    counts = {}
    for method, by_run in runs.items():
        groups = sorted({session_group[method](i) for i in order})
        n = len(by_run)
        draws = run_rng.integers(0, n, size=(sens.RESAMPLES, len(groups), n))
        counts[(method, "sessions")] = (groups, np.stack([(draws == k).sum(axis=2) for k in range(n)], axis=2))
        label_draws = run_rng.integers(0, n, size=(sens.RESAMPLES, n))
        counts[(method, "labels")] = np.stack([(label_draws == k).sum(axis=1) for k in range(n)], axis=1)

    def cluster_rates(item_hits: np.ndarray, item_totals: np.ndarray) -> np.ndarray:
        """다시 뽑기 행마다 뽑힌 군집의 맞힌 수 합 / 문항 수 합. item_hits 는 (다시 뽑기, 문항) 또는 (문항,)."""
        hits, totals = item_hits @ membership, item_totals @ membership
        if hits.ndim == 1:
            return hits[resample].sum(axis=1) / totals[resample].sum(axis=1)
        rows = np.arange(sens.RESAMPLES)[:, None]
        return hits[rows, resample].sum(axis=1) / totals[resample].sum(axis=1)

    report = {"description": __doc__.split("\n")[0], "items": list(sens.ITEMS),
              "clusterResamples": {"count": sens.RESAMPLES, "seed": sens.SEED, "unit": "(wg, family) cluster"},
              "sessionResamples": {"seed": RUN_SEED,
                                   "runsPerMethod": {m: list(r) for m, r in runs.items()},
                                   "sessionGroups": {"claude_text2cypher": "working group",
                                                     "claude_text2sql": "working group",
                                                     "claude_text2cypher_repaired": "working group",
                                                     "claude_text2sql_repaired": "working group",
                                                     "text_search": "working-group part (parts/*.json)"},
                                   "distinctAgentsInProvenance": sessions_seen,
                                   "rule": "per resample, each session group draws as many sessions as it has runs, "
                                           "with replacement; single-run methods fixed"},
              "methods": {}, "comparisons": []}
    for rule in sens.RULES:
        rates, point = {design: {} for design in DESIGNS}, {}
        for method, by_run in runs.items():
            matrix = np.stack([exact[(method, run, rule)] for run in by_run])          # runs x items
            n = len(by_run)
            totals = np.full(len(order), float(n))
            point[method] = float(matrix.sum() / (n * len(order)))
            rates["clusterOnly"][method] = cluster_rates(matrix.sum(axis=0), totals)
            misses = {}
            if n == 1:
                rates["sessionsAndClusters"][method] = rates["runLabelsAndClusters"][method] = \
                    rates["clusterOnly"][method]
            else:
                groups, weights = counts[(method, "sessions")]                          # resamples x groups x runs
                item_group = np.array([groups.index(session_group[method](i)) for i in order])
                item_hits = np.einsum("bik,ki->bi", weights[:, item_group, :], matrix)
                rates["sessionsAndClusters"][method] = cluster_rates(item_hits, totals)
                rates["runLabelsAndClusters"][method] = cluster_rates(counts[(method, "labels")] @ matrix, totals)
                # 세션 하나 = (세션 묶음, 실행). 놓친 문항 수가 0 이 아닌 세션만 적는다.
                for g, group in enumerate(groups):
                    for k, run in enumerate(by_run):
                        missed = int((matrix[k, item_group == g] == 0).sum())
                        if missed:
                            misses[f"{group}/{run}"] = missed
            report["methods"].setdefault(method, {})[rule] = {
                "runs": n, "meanExactCount": round(float(matrix.sum() / n), 1),
                "exactRatePercent": round(100 * float(matrix.sum() / (n * len(order))), 1),
                "perRunExact": {run: int(row.sum()) for run, row in zip(by_run, matrix)},
                **{f"{design}95Percent": percentile(rates[design][method]) for design in DESIGNS}}
            if n > 1:
                report["methods"][method][rule].update({
                    "sessions": len(groups) * n,
                    "missTotal": int((matrix == 0).sum()),
                    "sessionsWithMisses": len(misses),
                    "missesBySession": dict(sorted(misses.items(), key=lambda kv: (-kv[1], kv[0])))})
        for first, second in COMPARISONS:
            entry = {"rule": rule, "first": first, "second": second,
                     "differencePercent": round(100 * (point[first] - point[second]), 1)}
            for design in DESIGNS:
                low, high = np.percentile(rates[design][first] - rates[design][second], [2.5, 97.5])
                entry[f"{design}95Percent"] = [round(100 * float(low), 1), round(100 * float(high), 1)]
                entry[f"{design}ExcludesZero"] = bool(low > 0 or high < 0)
            report["comparisons"].append(entry)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    print("세션 수", sessions_seen)
    for method, by_rule in report["methods"].items():
        for rule, value in by_rule.items():
            print(method, rule, {k: v for k, v in value.items() if k != "perRunExact"})
    for entry in report["comparisons"]:
        print(entry)


if __name__ == "__main__":
    main()
