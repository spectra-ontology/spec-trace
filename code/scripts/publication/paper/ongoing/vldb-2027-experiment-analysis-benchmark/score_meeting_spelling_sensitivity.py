#!/usr/bin/env python3
"""모든 풀이 경로의 저장된 응답을 회의 표기 규칙 세 가지로 다시 채점하고 경로 사이의 차를 같은 규칙 안에서 비교한다.

모델 호출과 데이터베이스 질의는 없고, 저장된 응답 파일과 문항 파일, 기록 SQLite 의 회의 목록만 읽는다.

규칙
- `recorded` (주 규칙): `score_chain_eval.cell_key` 그대로다. 칸의 앞뒤 공백을 걷고 소문자로 바꾼 뒤
  회의 번호 뒤의 bis 표시만 한 철자로 맞춘다. 전자 회의 표시 `-e` 는 기록에 적힌 그대로 비교한다.
- `same_meeting`: 위 값에서 `tsg_meeting` · `wg_meeting` 칸 끝의 `-e` 를 양쪽 모두 걷는다. 단 기록이 `#N` 과
  `#N-e` 를 서로 다른 회의로 함께 담은 번호(`RECORD_SQLITE` 의 `meeting.label` 과 `cr_pack.tsg_meeting` 에서
  찾는다)는 걷지 않고 그대로 둔다. 회의가 같으면 같은 값으로 보고, 다른 회의는 계속 다른 값으로 둔다.
- `literal`: 칸의 앞뒤 공백을 걷고 소문자로만 바꾼다. bis 철자도 맞추지 않는다.

경로마다 세 규칙의 정확 일치 수(전체 · 정답 있는 문항 · 빈 정답 문항 · 경로가 응답한 문항)와 규칙을 바꿀 때 결과가
달라지는 문항을 적는다. 쌍 비교는 `summarize_text_route_full.py` 와 같은 (작업반, 종류) 35군집 짝 부트스트랩
(다시 뽑기 10,000번, 씨앗 20261112, 모든 비교가 같은 다시 뽑기 표를 쓴다)이다. 여러 번 실행한 경로(질의 작성
다섯 실행, 메타데이터 포함 전문 검색 세 실행)는 실행마다의 결과를 군집 안에서 모두 더해 평균 비율로 센다.
전문 검색의 실행 목록은 `summarize_text_route_full.py` 의 실행 계획 검사를 그대로 따른다.

사용: python3 score_meeting_spelling_sensitivity.py [--out <json>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

import numpy as np

from score_chain_eval import cell_key
from score_meeting_suffix_insensitive import E_SUFFIX, MEETING_FIELDS
from summarize_text_route_full import (CLUSTERS, ITEMS, QUERY_SUMMARY, RESAMPLES, RUN_DIRS, RUN_PLAN, SEED, WGS,
                                       percent)
from summarize_text_route_full import ROUTES as TEXT_ROUTES

ROOT = next(path for path in Path(__file__).resolve().parents if (path / ".git").exists())
TRACK = "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
RECORD_SQLITE = f"{TRACK}/integration/sqlite_final/{{wg}}.sqlite"
DEFAULT_OUT = f"{TRACK}/final/meeting_spelling_sensitivity/summary.json"
RULES = ("recorded", "same_meeting", "literal")
CE = f"{TRACK}/chain_eval"
EXPRESSIBLE_BY_CRDB = {"pack_lookup", "pack_lookup_empty", "pack_origin", "disposition_pack", "revision_chain"}


def per_wg(pattern: str) -> list[str]:
    return [pattern.format(wg=wg) for wg in WGS]


SINGLE_ROUTES = {
    "closed_book_llama3_1_8b": per_wg(f"{CE}/{{wg}}_closed_book_llama3_1_8b.jsonl"),
    "closed_book_qwen2_5_14b": per_wg(f"{CE}/{{wg}}_closed_book_qwen2_5_14b.jsonl"),
    "dense_llama3_1_8b": per_wg(f"{CE}/{{wg}}_dense_llama3_1_8b.jsonl"),
    "dense_qwen2_5_14b": per_wg(f"{CE}/{{wg}}_dense_qwen2_5_14b.jsonl"),
    "oracle_evidence_llama3_1_8b": per_wg(f"{CE}/oracle_evidence/{{wg}}_oracle_evidence_llama3_1_8b.jsonl"),
    "oracle_evidence_qwen2_5_14b": per_wg(f"{CE}/oracle_evidence/{{wg}}_oracle_evidence_qwen2_5_14b.jsonl"),
    "oracle_evidence_textonly_llama3_1_8b":
        per_wg(f"{CE}/oracle_evidence/{{wg}}_oracle_evidence_textonly_llama3_1_8b.jsonl"),
    "identifier_raw_source_llama3_1_8b": per_wg(f"{CE}/identifier_route/{{wg}}_raw_source_llama3_1_8b.jsonl"),
    "identifier_raw_source_qwen2_5_14b": per_wg(f"{CE}/identifier_route/{{wg}}_raw_source_qwen2_5_14b.jsonl"),
    "identifier_hopkey_llama3_1_8b": per_wg(f"{CE}/identifier_route/{{wg}}_hopkey_llama3_1_8b.jsonl"),
    "identifier_hopkey_qwen2_5_14b": per_wg(f"{CE}/identifier_route/{{wg}}_hopkey_qwen2_5_14b.jsonl"),
    "text_search_text_only": per_wg(TEXT_ROUTES["text_search_text_only"]["runA"]),
    "codex_text2sql_schema": per_wg(f"{CE}/codex/chain_sql_{{wg}}_codex.jsonl"),
    "codex_text2sql_value_domains": per_wg(f"{CE}/codex_v2/responses/{{wg}}_sql_dom_codex.jsonl"),
    "codex_text2sql_exploration": per_wg(f"{CE}/codex_v2/responses/{{wg}}_sql_exp_codex.jsonl"),
    "codex_text2cypher_schema": per_wg(f"{CE}/codex/chain_cy_{{wg}}_codex.jsonl"),
    "codex_text2cypher_value_domains": per_wg(f"{CE}/codex_v2/responses/{{wg}}_cy_dom_codex.jsonl"),
    "codex_text2cypher_exploration": per_wg(f"{CE}/codex_v2/responses/{{wg}}_cy_exp_codex.jsonl"),
    "crdb_lookup": per_wg(f"{TRACK}/final/crdb_baseline/{{wg}}_crdb_lookup.jsonl"),
    "rederivation": per_wg(f"{TRACK}/final/chain_rederivation/answers_{{wg}}.jsonl"),
}
QUERY_METHODS = ("claude_text2cypher", "claude_text2sql")


def separately_recorded_meetings() -> set[str]:
    """기록이 `#N` 과 `#N-e` 를 둘 다 회의 이름으로 담은 경우의 `#N-e` 쪽 소문자 이름."""
    labels: set[str] = set()
    for wg in WGS:
        connection = sqlite3.connect(f"file:{ROOT / RECORD_SQLITE.format(wg=wg)}?mode=ro", uri=True)
        for (value,) in connection.execute("SELECT label FROM meeting UNION SELECT tsg_meeting FROM cr_pack"):
            if value:
                labels.add(str(value).strip().lower())
        connection.close()
    return {label + "-e" for label in labels if label + "-e" in labels}


def read_responses(paths: list[str], items: dict) -> tuple[dict, dict]:
    """응답을 문항 id 로 모은다. 현재 문항에 없는 id 와 질문 해시가 현재 질문과 다른 응답은 빼고 그 수를 센다.

    질문 해시를 적지 않은 응답(재유도 답)은 그대로 받고 `withoutQuestionHash` 로 센다.
    """
    responses, tally = {}, {"notInItems": 0, "staleQuestion": 0, "withoutQuestionHash": 0}
    for path in paths:
        for line in (ROOT / path).read_text().splitlines():
            if not line.strip():
                continue
            response = json.loads(line)
            item = items.get(response["id"])
            if item is None:
                tally["notInItems"] += 1
                continue
            question = response.get("questionSha256")
            if question is None:
                tally["withoutQuestionHash"] += 1
            elif question != hashlib.sha256(item["question"].encode()).hexdigest():
                tally["staleQuestion"] += 1
                continue
            responses[response["id"]] = response
    return responses, tally


def make_row_key(rule: str, kept: set[str]):
    def literal_cell(cell) -> str:
        return "" if cell is None else str(cell).strip().lower()

    def row_key(fields: list[str], row) -> tuple[str, ...]:
        cells = []
        for index, cell in enumerate(row):
            if rule == "literal":
                cells.append(literal_cell(cell))
                continue
            value = cell_key(cell)
            if rule == "same_meeting" and index < len(fields) and fields[index] in MEETING_FIELDS \
                    and value not in kept:
                value = E_SUFFIX.sub("", value)
            cells.append(value)
        return tuple(cells)
    return row_key


def exact(item: dict, rows, row_key) -> bool:
    if rows is None:
        return False
    return {row_key(item["fields"], row) for row in item["gold"]} == {row_key(item["fields"], row) for row in rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, default=ROOT / DEFAULT_OUT)
    args = parser.parse_args()

    items = {item["id"]: item for path in ITEMS for item in map(json.loads, (ROOT / path).read_text().splitlines())}
    cluster_names = sorted({(item["wg"], item["family"]) for item in items.values()})
    if len(cluster_names) != CLUSTERS:
        raise SystemExit(f"군집 수가 계획과 다르다: {len(cluster_names)}")
    cluster_index = {name: c for c, name in enumerate(cluster_names)}
    cluster_of = {identifier: cluster_index[(item["wg"], item["family"])] for identifier, item in items.items()}
    resample = np.random.default_rng(SEED).integers(0, CLUSTERS, size=(RESAMPLES, CLUSTERS))
    kept = separately_recorded_meetings()
    row_keys = {rule: make_row_key(rule, kept) for rule in RULES}
    answerable = [i for i, item in items.items() if not item["expectsEmpty"]]
    empty_gold = [i for i, item in items.items() if item["expectsEmpty"]]

    def cluster_rate(outcomes: dict[str, list[bool]]) -> tuple[float, np.ndarray]:
        hits, totals = np.zeros(CLUSTERS), np.zeros(CLUSTERS)
        for identifier, values in outcomes.items():
            hits[cluster_of[identifier]] += sum(values)
            totals[cluster_of[identifier]] += len(values)
        return float(hits.sum() / totals.sum()), hits[resample].sum(axis=1) / totals[resample].sum(axis=1)

    def outcomes_for(paths: list[str]) -> tuple[dict, dict, int]:
        responses, tally = read_responses(paths, items)
        by_rule = {rule: {identifier: bool(identifier in responses and exact(item, responses[identifier].get("rows"),
                                                                             row_keys[rule]))
                          for identifier, item in items.items()} for rule in RULES}
        return by_rule, responses, tally

    def counts(outcome: dict[str, bool], responded: set[str]) -> dict:
        return {"all": sum(outcome.values()), "answerable": sum(outcome[i] for i in answerable),
                "emptyGold": sum(outcome[i] for i in empty_gold), "responded": sum(outcome[i] for i in responded)}

    def changes(base: dict[str, bool], other: dict[str, bool]) -> dict:
        gained = sorted(i for i in items if other[i] and not base[i])
        lost = sorted(i for i in items if base[i] and not other[i])
        return {"gained": len(gained), "lost": len(lost), "gainedIds": gained, "lostIds": lost}

    routes, pooled_outcomes = {}, {}
    single_outcomes = {}
    for route, paths in SINGLE_ROUTES.items():
        by_rule, responses, tally = outcomes_for(paths)
        responded = set(responses)
        single_outcomes[route] = by_rule
        block = {"responses": paths, "respondedItems": len(responded), **tally,
                 "exact": {rule: counts(by_rule[rule], responded) for rule in RULES},
                 "changesFromRecorded": {rule: changes(by_rule["recorded"], by_rule[rule]) for rule in RULES[1:]}}
        if route == "crdb_lookup":
            expressible = {i for i in items if items[i]["family"] in EXPRESSIBLE_BY_CRDB}
            block["expressibleItems"] = len(expressible)
            block["exactExpressible"] = {rule: sum(by_rule[rule][i] for i in expressible) for rule in RULES}
        routes[route] = block

    summary = json.loads((ROOT / QUERY_SUMMARY).read_text())
    planned = json.loads((ROOT / RUN_PLAN).read_text())["runs"]
    if planned != list(RUN_DIRS["text_search"]):
        raise SystemExit(f"실행 계획의 실행 목록과 전문 검색 실행 목록이 다르다: {planned}")
    multi_run = {method: {"runsPooled": summary["primary"]["methods"][method]["runsPooled"],
                          "runs": summary["primary"]["methods"][method]["runs"]} for method in QUERY_METHODS}
    multi_run["text_search"] = {"runsPooled": planned,
                                "runs": [{"run": run, "responses": per_wg(TEXT_ROUTES["text_search"][run])}
                                         for run in planned]}
    for method, block in multi_run.items():
        pooled = [run for run in block["runs"] if run["run"] in block["runsPooled"]]
        if [run["run"] for run in pooled] != list(block["runsPooled"]):
            raise SystemExit(f"{method}: 모을 실행의 응답 목록이 실행 목록과 다르다")
        per_run, pooled_by_rule = {}, {rule: {i: [] for i in items} for rule in RULES}
        for run in pooled:
            by_rule, responses, tally = outcomes_for(run["responses"])
            per_run[run["run"]] = {"responses": run["responses"], "respondedItems": len(responses), **tally,
                                   "exact": {rule: counts(by_rule[rule], set(responses)) for rule in RULES},
                                   "changesFromRecorded": {rule: {k: v for k, v in
                                                                  changes(by_rule["recorded"], by_rule[rule]).items()
                                                                  if not k.endswith("Ids")} for rule in RULES[1:]}}
            for rule in RULES:
                for identifier, value in by_rule[rule].items():
                    pooled_by_rule[rule][identifier].append(value)
        pooled_outcomes[method] = pooled_by_rule
        routes[method] = {"runsPooled": block["runsPooled"], "runs": per_run,
                          "meanExactAll": {rule: round(sum(per_run[r]["exact"][rule]["all"] for r in per_run)
                                                       / len(per_run), 2) for rule in RULES},
                          "meanExactAnswerable": {rule: round(sum(per_run[r]["exact"][rule]["answerable"]
                                                                  for r in per_run) / len(per_run), 2)
                                                  for rule in RULES}}

    def as_lists(outcome: dict[str, bool]) -> dict[str, list[bool]]:
        return {identifier: [value] for identifier, value in outcome.items()}

    comparisons = (("text_search", "text_search_text_only"), ("text_search", "claude_text2cypher"),
                   ("text_search", "claude_text2sql"), ("claude_text2cypher", "claude_text2sql"))
    paired = []
    for rule in RULES:
        rates = {}
        rates["text_search_text_only"] = cluster_rate(as_lists(single_outcomes["text_search_text_only"][rule]))
        for method in multi_run:
            rates[method] = cluster_rate(pooled_outcomes[method][rule])
        for first, second in comparisons:
            difference = rates[first][1] - rates[second][1]
            low, high = np.percentile(difference, [2.5, 97.5])
            paired.append({"rule": rule, "first": first, "second": second,
                           "firstExactRatePercent": percent([rates[first][0]])[0],
                           "secondExactRatePercent": percent([rates[second][0]])[0],
                           "exactRateDifferencePercent": percent([rates[first][0] - rates[second][0]])[0],
                           "pairedClusterBootstrap95Percent": percent([low, high]),
                           "intervalExcludesZero": bool(low > 0 or high < 0)})

    result = {"items": list(ITEMS), "rules": {
                  "recorded": "score_chain_eval.cell_key (strip, lower, one spelling for the bis mark)",
                  "same_meeting": "recorded, then a trailing '-e' removed from tsg_meeting and wg_meeting cells on "
                                  "both sides, except for meeting names the records hold both with and without '-e'",
                  "literal": "strip and lower only"},
              "keptElectronicSpellings": sorted(kept), "recordSqlite": per_wg(RECORD_SQLITE),
              "querySummary": QUERY_SUMMARY,
              "bootstrap": {"resamples": RESAMPLES, "seed": SEED, "unit": "(wg, family) cluster",
                            "interval": "percentile 95%"},
              "routes": routes, "paired": paired}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=1) + "\n")
    for route, block in routes.items():
        if "exact" in block:
            extra = f" expressible {block['exactExpressible']}" if "exactExpressible" in block else ""
            print(route, block["respondedItems"], {rule: block["exact"][rule]["all"] for rule in RULES},
                  {rule: block["exact"][rule]["answerable"] for rule in RULES}, extra)
        else:
            print(route, block["meanExactAll"],
                  {run: [block["runs"][run]["exact"][rule]["all"] for rule in RULES] for run in block["runs"]})
    for row in paired:
        print(row["rule"], row["first"], "-", row["second"], row["exactRateDifferencePercent"],
              row["pairedClusterBootstrap95Percent"])


if __name__ == "__main__":
    main()
