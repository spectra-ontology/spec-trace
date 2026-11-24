#!/usr/bin/env python3
"""공개 가중치 모델이 도구를 쓰며 푼 네 조건(모델 둘 × 경로 둘)을 사전 분석 계획대로 채점한다 (모델 호출 없음).

분석 계획은 `final/next_cycle/analysis_plan_local_agent.json` 이다. 조건은 계획의 `models` × `routes` 이고 계획의 차례
(모델 차례, 그 안에서 경로 차례)로 모두 적는다. 점수와 관계없이 네 조건을 모두 낸다.

검사. 조건마다 작업반 다섯 파일(`{WG}_{route}_{model tag}.jsonl`, 꼬리는 `run_local_agent_eval.main` 과 같은 변환)이
모두 있고, 기록이 문항 수(667)와 같으며 id 가 겹치지 않고 문항 전체와 같아야 한다. 기록마다 질문 SHA-256 · 작업반 ·
method · model 이 문항과 계획에 맞아야 하고 `rows` 는 null 이거나 행 목록이어야 한다. 하나라도 어긋나면 멈춘다.

채점은 기존 채점기를 불러 쓴다.
- 주 규칙 `recorded`: `score_chain_eval.score` 의 정확 행 집합 일치. 정답 있는 581 문항의 정확 수와 Wilson 95% 구간
  (`summarize_chain_scores.wilson` 의 비율, `summarize_text_route_full.wilson` 의 원값에서 한 번 반올림한 백분율),
  빈 정답 86 문항의 정확 수, fabricated(빈 정답 문항에 행을 하나 이상 낸 수), 짝 기권 지표 D · D_X.
  D · D_X 는 결과 표의 로컬 독자 행과 같이 `summarize_chain_scores.abstention_by_template` 의 `pack_lookup` 틀에서
  읽는다(discrimination = D, correctnessAware = D_X). `summarize_text_route_full.abstention` 의 구성 개수와 같아야 한다.
- 보조 규칙 `same_meeting`: `score_meeting_spelling_sensitivity` 의 같은 규칙으로 같은 값을 다시 센다.
- 세션: 문항마다의 turns · tokens · seconds 중앙값, endedBy 값마다의 수(`no_answer_at_budget` 포함), contextOverflow 수.

`rows` 가 null 인 기록(예산에 닿아 답을 내지 못함, 답 SQL 이 실행되지 않음, 답 행의 형식이 틀림)은 기존 채점기의
읽을 수 없는 응답과 같이 센다. 두 층 모두 정확 0 이고, 빈 응답으로도 fabricated 로도 세지 않으며, 분모는 581 · 86
그대로다. 그래서 정답 있는 짝 문항의 null 은 D 를 바꾸지 않고 D_X 만 낮추며, 빈 정답 문항의 null 은 둘 다 낮춘다.

사용: PYTHONPATH=scripts/common:scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark \\
          python3 -B analyze_local_agent.py --responses-dir <dir> --out <json> [--plan <json>]   (저장소 루트에서 실행)
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import statistics
import sys
from pathlib import Path

import score_meeting_spelling_sensitivity as sens
import summarize_text_route_full as route_full
from score_chain_eval import score, summarize
from summarize_chain_scores import abstention_by_template, wilson

ROOT = sens.ROOT
PLAN = f"{sens.TRACK}/final/next_cycle/analysis_plan_local_agent.json"
ANSWERABLE, EMPTY_GOLD = 581, 86  # 계획의 scoring.primary 가 적은 두 층의 문항 수
PRIMARY, SECONDARY = "recorded", "same_meeting"
TEMPLATE = "pack_lookup"  # 빈 정답 문항(`pack_lookup_empty`)과 같은 질문 틀
RECORD_KEYS = {"id", "wg", "family", "method", "model", "questionSha256", "rows", "endedBy", "turns", "tokens",
               "contextOverflow", "seconds", "trace"}
SESSION_NUMBERS = ("turns", "tokens", "seconds")
NULL_ROWS = ("rows null (no_answer_at_budget, an answer SQL that did not execute, or answer rows not in list-of-lists "
             "form) is an unreadable response as in score_chain_eval.score: exact 0 on answerable and empty-gold items, "
             "counted neither as an empty response (D, D_X numerators) nor as fabricated; denominators stay 581 and 86")
RULES = {"recorded": "score_chain_eval.cell_key (strip, lower, one spelling for the bis mark)",
         "same_meeting": "recorded, then a trailing '-e' removed from tsg_meeting and wg_meeting cells on both sides, "
                         "except for meeting names the records hold both with and without '-e' "
                         "(score_meeting_spelling_sensitivity.make_row_key)"}


def fail(message: str) -> None:
    raise SystemExit(f"analyze_local_agent: {message}")


def model_tag(model: str) -> str:
    """`run_local_agent_eval.main` 이 응답 파일 이름에 붙이는 모델 꼬리."""
    return model.replace(":", "_").replace(".", "_")


def shown(path: Path) -> str:
    resolved = path.resolve()
    return str(resolved.relative_to(ROOT)) if resolved.is_relative_to(ROOT) else str(resolved)


def load_condition(directory: Path, route: str, model: str, items: dict, wgs: list[str]) -> tuple[dict, list[str]]:
    method = f"local_agent_{route}"
    records, files = {}, []
    for wg in wgs:
        path = directory / f"{wg}_{route}_{model_tag(model)}.jsonl"
        if not path.is_file():
            fail(f"{route} {model}: 응답 파일이 없다: {path}")
        files.append(shown(path))
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            where = f"{path.name}:{number}"
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                fail(f"{where}: JSON 기록이 아니다 ({error})")
            if not isinstance(record, dict):
                fail(f"{where}: JSON 객체가 아니다")
            if RECORD_KEYS - set(record):
                fail(f"{where}: 기록 칸이 모자란다: {sorted(RECORD_KEYS - set(record))}")
            identifier = record["id"]
            item = items.get(identifier)
            if item is None:
                fail(f"{where}: 문항에 없는 id {identifier}")
            if identifier in records:
                fail(f"{where}: id 가 겹친다 {identifier}")
            if record["wg"] != wg or item["wg"] != wg:
                fail(f"{where}: 작업반이 다르다 (기록 {record['wg']}, 문항 {item['wg']}, 파일 {wg})")
            if record["method"] != method or record["model"] != model:
                fail(f"{where}: method/model 이 조건과 다르다 ({record['method']}, {record['model']})")
            if record["questionSha256"] != hashlib.sha256(item["question"].encode()).hexdigest():
                fail(f"{where}: 질문 SHA-256 이 현재 문항과 다르다 {identifier}")
            rows = record["rows"]
            if rows is not None and not (isinstance(rows, list) and all(isinstance(row, list) for row in rows)):
                fail(f"{where}: rows 가 null 도 행 목록도 아니다 {identifier}")
            if record["endedBy"] == "no_answer_at_budget" and rows is not None:
                fail(f"{where}: no_answer_at_budget 인데 rows 가 있다 {identifier}")
            if any(isinstance(record[name], bool) or not isinstance(record[name], (int, float))
                   for name in SESSION_NUMBERS):
                fail(f"{where}: turns/tokens/seconds 가 수가 아니다 {identifier}")
            records[identifier] = record
    if len(records) != len(items):
        absent = sorted(set(items) - set(records))
        fail(f"{route} {model}: 기록 {len(records)}개, 문항 {len(items)}개. 빠진 문항 예: {absent[:5]}")
    return records, files


def rule_block(rule: str, items: dict, records: dict, row_key) -> tuple[dict, dict[str, bool]]:
    order = sorted(items)
    results = {}
    for identifier in order:
        item, rows = items[identifier], records[identifier]["rows"]
        hit = int(sens.exact(item, rows, row_key))
        if rule == PRIMARY:
            result = score(item["gold"], rows)
            if result["exact"] != hit:
                fail(f"score_chain_eval.score 와 recorded 규칙의 정확 판정이 다르다 {identifier}")
        else:
            result = {"exact": hit}
        results[identifier] = result
    answerable = [i for i in order if not items[i]["expectsEmpty"]]
    empty = [i for i in order if items[i]["expectsEmpty"]]
    hits = sum(results[i]["exact"] for i in answerable)
    empty_hits = sum(results[i]["exact"] for i in empty)
    fabricated = sum(bool(records[i]["rows"]) for i in empty)
    template = next((entry for entry in abstention_by_template(
        [(items[i], records[i]["rows"], results[i]) for i in order]) if entry["template"] == TEMPLATE), None)
    if template is None:
        fail(f"{TEMPLATE} 틀의 기권 지표가 없다")
    outcome = {i: bool(results[i]["exact"]) for i in order}
    check = route_full.abstention(items, records, outcome)
    counts = ("emptyItems", "answerableItems", "onEmpty", "onAnswerable", "exactOnAnswerable")
    if any(check[name] != template[name] for name in counts):
        fail(f"두 기권 지표 정의의 구성 개수가 다르다: {check} / {template}")
    if template["emptyItems"] != len(empty) or template["onEmpty"] != empty_hits \
            or template["fabricatedOnEmpty"] != fabricated:
        fail("빈 정답 문항 전체가 pack_lookup 틀의 빈 정답 문항과 같지 않다")
    block = {
        "rule": rule,
        "answerable": {"exact": hits, "n": len(answerable), "wilson95": wilson(hits, len(answerable)),
                       "wilson95Percent": route_full.wilson(hits, len(answerable))},
        "emptyGold": {"exact": empty_hits, "n": len(empty)},
        "fabricated": fabricated,
        "abstention": {"template": TEMPLATE, **{name: template[name] for name in counts},
                       "unreadableOnEmpty": template["unreadableOnEmpty"],
                       "D": template["discrimination"], "D_X": template["correctnessAware"]},
    }
    if rule == PRIMARY:
        block["scoreChainEvalAll"] = summarize(list(results.values()))
    return block, outcome


def session_block(items: dict, records: dict) -> dict:
    values = list(records.values())
    ended = collections.Counter(record["endedBy"] for record in values)
    null = [i for i, record in records.items() if record["rows"] is None]
    return {
        "endedBy": dict(sorted(ended.items())),
        "noAnswerAtBudget": ended.get("no_answer_at_budget", 0),
        "contextOverflow": sum(bool(record["contextOverflow"]) for record in values),
        "nullRows": {"all": len(null), "answerable": sum(not items[i]["expectsEmpty"] for i in null),
                     "emptyGold": sum(items[i]["expectsEmpty"] for i in null),
                     "byEndedBy": dict(sorted(collections.Counter(records[i]["endedBy"] for i in null).items()))},
        "emptyResponseOnAnswerable": sum(record["rows"] == [] for i, record in records.items()
                                         if not items[i]["expectsEmpty"]),
        "medianPerItem": {name: statistics.median(record[name] for record in values) for name in SESSION_NUMBERS},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--responses-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--plan", type=Path, default=ROOT / PLAN)
    args = parser.parse_args()

    plan_bytes = args.plan.read_bytes()
    plan = json.loads(plan_bytes)
    items = {}
    for path in plan["items"]:
        for line in (ROOT / path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                if item["id"] in items:
                    fail(f"문항 id 가 겹친다 {item['id']}")
                items[item["id"]] = item
    answerable = sum(not item["expectsEmpty"] for item in items.values())
    if (len(items), answerable, len(items) - answerable) != (plan["itemCount"], ANSWERABLE, EMPTY_GOLD):
        fail(f"문항 수가 계획과 다르다: {len(items)} / 정답 있는 {answerable}")
    wgs = sorted({item["wg"] for item in items.values()})
    runner = ROOT / plan["runner"]["script"]
    runner_sha = hashlib.sha256(runner.read_bytes()).hexdigest()
    if runner_sha != plan["runner"]["sha256"]:
        print(f"경고: 풀이 스크립트의 SHA-256 이 계획과 다르다 ({runner_sha})", file=sys.stderr)
    kept = sens.separately_recorded_meetings()
    row_keys = {rule: sens.make_row_key(rule, kept) for rule in (PRIMARY, SECONDARY)}

    conditions, order = {}, []
    for model in plan["models"]:
        for route in plan["routes"]:
            name = f"{route}_{model_tag(model)}"
            records, files = load_condition(args.responses_dir, route, model, items, wgs)
            primary, primary_outcome = rule_block(PRIMARY, items, records, row_keys[PRIMARY])
            secondary, secondary_outcome = rule_block(SECONDARY, items, records, row_keys[SECONDARY])
            gained = sorted(i for i in items if secondary_outcome[i] and not primary_outcome[i])
            lost = sorted(i for i in items if primary_outcome[i] and not secondary_outcome[i])
            secondary["changesFromPrimary"] = {"gained": len(gained), "lost": len(lost),
                                               "gainedIds": gained, "lostIds": lost}
            conditions[name] = {"route": route, "model": model, "method": f"local_agent_{route}", "files": files,
                                "records": len(records), "session": session_block(items, records),
                                "primary": primary, "secondary": secondary}
            order.append(name)

    report = {
        "description": __doc__.split("\n")[0],
        "plan": shown(args.plan), "planSha256": hashlib.sha256(plan_bytes).hexdigest(),
        "runner": {"script": plan["runner"]["script"], "sha256Recorded": plan["runner"]["sha256"],
                   "sha256Current": runner_sha, "matches": runner_sha == plan["runner"]["sha256"]},
        "items": {"paths": plan["items"], "count": len(items), "answerable": answerable,
                  "emptyGold": len(items) - answerable,
                  "packLookupAnswerable": sum(item["family"] == TEMPLATE for item in items.values())},
        "responsesDir": shown(args.responses_dir),
        "rules": {"primary": PRIMARY, "secondary": SECONDARY, **RULES},
        "keptElectronicSpellings": sorted(kept),
        "nullRows": NULL_ROWS,
        "metrics": {"fabricated": "empty-gold items whose response has at least one row",
                    "D": "onEmpty/emptyItems - onAnswerable/answerableItems over the pack_lookup template",
                    "D_X": "onEmpty/emptyItems - (1 - exactOnAnswerable/answerableItems) over the pack_lookup template",
                    "wilson95": "summarize_chain_scores.wilson (proportion, 4 decimals)",
                    "wilson95Percent": "summarize_text_route_full.wilson (percent rounded once from the raw value)"},
        "conditionOrder": order,
        "conditions": conditions,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    for name in order:
        block = conditions[name]
        for rule in ("primary", "secondary"):
            r = block[rule]
            print(f"{name:26s} {r['rule']:12s} answerable {r['answerable']['exact']}/{r['answerable']['n']} "
                  f"{r['answerable']['wilson95Percent']} empty-gold {r['emptyGold']['exact']}/{r['emptyGold']['n']} "
                  f"fabricated {r['fabricated']} D {r['abstention']['D']} D_X {r['abstention']['D_X']}")
        s = block["session"]
        print(f"{name:26s} endedBy {s['endedBy']} null {s['nullRows']['all']} median {s['medianPerItem']}")


if __name__ == "__main__":
    main()
