#!/usr/bin/env python3
"""헤드룸 분할(세 계열, 채택 문항 297개)의 풀이 결과를 사전 분석 계획대로 채점한다 (모델 호출 없음).

분석 계획은 `final/next_cycle/analysis_plan_headroom.json`, 문항은 `final/next_cycle/headroom/implementation_record.json`
이 적은 두 파일이다(SHA-256 을 기록과 대조한다). 풀이 방법과 회차는 `--manifest` 의 JSON 이 차례대로 적는다.

    {"methods": [{"name": "...", "solver": "...", "access": "...", "runs": [{"run": "A", "files": ["...jsonl", ...]}]}]}

회차의 파일들은 `run_chain_eval.py` · `run_local_agent_eval.py` 가 쓰는 응답 기록(JSONL, 문항마다 `id` · `rows`,
있으면 `questionSha256`)이고, 한 회차의 기록은 분할의 문항 전체를 한 번씩 담아야 한다. 끝내지 못한 조건은 회차에
`"incomplete": "<이유>"` 를 적으면 푼 문항만으로 세고, 보고에 미완으로 표시하며 푼 문항 수를 함께 낸다(계획의
notAnalysed). 점수와 관계없이 manifest 의 모든 방법과 회차를 낸다.

채점은 기존 채점기를 불러 쓴다.
- 주 규칙 `recorded`: `score_chain_eval.score` 의 정확 행 집합 일치.
- 보조 규칙 `same_meeting`: `score_meeting_spelling_sensitivity` 의 같은 규칙. 주 규칙 옆에 함께 낸다.
- 방법과 회차마다, 전체와 계열마다: 정확 수 / 문항 수와 Wilson 95% 구간(`summarize_chain_scores.wilson` 의 비율,
  `summarize_text_route_full.wilson` 의 백분율). 회차가 둘 이상이면 정확 수의 평균과 범위.
- 세션 기록(`turns` · `tokens` · `seconds` · `endedBy`)이 있는 회차: 문항마다의 중앙값과 답 없이 끝난 세션 수.

`rows` 가 null 인 기록은 기존 채점기의 읽을 수 없는 응답과 같이 정확 0 으로 세고 분모에 남긴다. 분할의 문항은 모두
정답이 있으므로(빈 정답 문항 없음) 기권 지표는 내지 않는다.

사용: PYTHONPATH=scripts/common:scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark \\
          python3 -B analyze_headroom.py --manifest <json> --out <json>   (저장소 루트에서 실행)
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import statistics
from pathlib import Path

import score_meeting_spelling_sensitivity as sens
import summarize_text_route_full as route_full
from score_chain_eval import score
from summarize_chain_scores import wilson

ROOT = sens.ROOT
NEXT = f"{sens.TRACK}/final/next_cycle"
PLAN = f"{NEXT}/analysis_plan_headroom.json"
RECORD = f"{NEXT}/headroom/implementation_record.json"
PRIMARY, SECONDARY = "recorded", "same_meeting"
SESSION_NUMBERS = ("turns", "tokens", "seconds")


def fail(message: str) -> None:
    raise SystemExit(f"analyze_headroom: {message}")


def shown(path: Path) -> str:
    resolved = path.resolve()
    return str(resolved.relative_to(ROOT)) if resolved.is_relative_to(ROOT) else str(resolved)


def load_items(record: dict) -> dict:
    items = {}
    for entry in record["itemFiles"].values():
        data = (ROOT / entry["path"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            fail(f"문항 파일의 SHA-256 이 구현 기록과 다르다: {entry['path']}")
        for line in data.decode("utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                if item["id"] in items:
                    fail(f"문항 id 가 겹친다 {item['id']}")
                if item["expectsEmpty"] or not item["gold"]:
                    fail(f"분할에 빈 정답 문항이 있다 {item['id']}")
                items[item["id"]] = item
    if len(items) != record["admitted"]:
        fail(f"문항 수가 구현 기록과 다르다: {len(items)} / {record['admitted']}")
    return items


def load_run(where: str, files: list[str], items: dict, incomplete: bool) -> tuple[dict, list[str]]:
    records, used = {}, []
    for name in files:
        path = ROOT / name
        if not path.is_file():
            fail(f"{where}: 응답 파일이 없다: {name}")
        used.append(shown(path))
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            spot = f"{where} {path.name}:{number}"
            record = json.loads(line)
            identifier = record.get("id")
            item = items.get(identifier)
            if item is None:
                fail(f"{spot}: 분할 문항에 없는 id {identifier}")
            if identifier in records:
                fail(f"{spot}: id 가 겹친다 {identifier}")
            sha = record.get("questionSha256")
            if sha is not None and sha != hashlib.sha256(item["question"].encode()).hexdigest():
                fail(f"{spot}: 질문 SHA-256 이 현재 문항과 다르다 {identifier}")
            rows = record.get("rows")
            if rows is not None and not (isinstance(rows, list) and all(isinstance(row, list) for row in rows)):
                fail(f"{spot}: rows 가 null 도 행 목록도 아니다 {identifier}")
            records[identifier] = record
    if not incomplete and len(records) != len(items):
        absent = sorted(set(items) - set(records))
        fail(f"{where}: 기록 {len(records)}개, 문항 {len(items)}개. 빠진 문항 예: {absent[:5]}")
    return records, used


def counted(hits: int, n: int) -> dict:
    block = {"exact": hits, "n": n}
    if n:
        block["wilson95"] = wilson(hits, n)
        block["wilson95Percent"] = route_full.wilson(hits, n)
    return block


def rule_block(rule: str, items: dict, records: dict, row_key, families: list[str]) -> tuple[dict, dict]:
    outcome = {}
    for identifier in sorted(records):
        item, rows = items[identifier], records[identifier].get("rows")
        hit = bool(sens.exact(item, rows, row_key))
        if rule == PRIMARY and bool(score(item["gold"], rows)["exact"]) != hit:
            fail(f"score_chain_eval.score 와 recorded 규칙의 정확 판정이 다르다 {identifier}")
        outcome[identifier] = hit
    by_family = {}
    for family in families:
        ids = [i for i in outcome if items[i]["family"] == family]
        by_family[family] = counted(sum(outcome[i] for i in ids), len(ids))
    return {"rule": rule, "all": counted(sum(outcome.values()), len(outcome)), "byFamily": by_family}, outcome


def session_block(records: dict) -> dict | None:
    values = list(records.values())
    if not values or not all(all(name in record for name in SESSION_NUMBERS) and "endedBy" in record
                             for record in values):
        return None
    ended = collections.Counter(record["endedBy"] for record in values)
    return {"endedBy": dict(sorted(ended.items())),
            "endedWithoutAnswer": sum(count for name, count in ended.items() if name != "answer"),
            "contextOverflow": sum(bool(record.get("contextOverflow")) for record in values),
            "medianPerItem": {name: statistics.median(record[name] for record in values) for name in SESSION_NUMBERS}}


def spread(values: list[int]) -> dict:
    return {"mean": round(statistics.mean(values), 2), "min": min(values), "max": max(values), "runs": len(values)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    plan_bytes = (ROOT / PLAN).read_bytes()
    record_bytes = (ROOT / RECORD).read_bytes()
    record = json.loads(record_bytes)
    if record["plan"]["sha256"] != hashlib.sha256(plan_bytes).hexdigest():
        fail("분석 계획의 SHA-256 이 구현 기록과 다르다")
    items = load_items(record)
    families = list(json.loads(plan_bytes)["families"])
    families = [family for family in families if any(item["family"] == family for item in items.values())]
    if {item["family"] for item in items.values()} != set(families):
        fail("문항의 계열이 계획의 계열과 다르다")
    kept = sens.separately_recorded_meetings()
    row_keys = {rule: sens.make_row_key(rule, kept) for rule in (PRIMARY, SECONDARY)}
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))

    methods, seen = [], set()
    for entry in manifest["methods"]:
        name = entry["name"]
        if name in seen:
            fail(f"방법 이름이 겹친다 {name}")
        seen.add(name)
        runs = []
        for run in entry["runs"]:
            where = f"{name}/{run['run']}"
            reason = run.get("incomplete")
            records, files = load_run(where, run["files"], items, reason is not None)
            block = {"run": run["run"], "files": files, "records": len(records),
                     "unreadable": sum(record.get("rows") is None for record in records.values()),
                     "emptyResponse": sum(record.get("rows") == [] for record in records.values())}
            if reason is not None:
                block["incomplete"] = {"reason": reason, "solved": len(records), "items": len(items)}
            outcomes = {}
            for rule in (PRIMARY, SECONDARY):
                block[rule], outcomes[rule] = rule_block(rule, items, records, row_keys[rule], families)
            block["secondaryChanges"] = {
                "gained": sorted(i for i in outcomes[PRIMARY] if outcomes[SECONDARY][i] and not outcomes[PRIMARY][i]),
                "lost": sorted(i for i in outcomes[PRIMARY] if outcomes[PRIMARY][i] and not outcomes[SECONDARY][i])}
            session = session_block(records)
            if session is not None:
                block["session"] = session
            runs.append(block)
        method = {key: value for key, value in entry.items() if key != "runs"}
        method["runs"] = runs
        complete = [run for run in runs if "incomplete" not in run]
        if len(complete) > 1:
            method["acrossRuns"] = {rule: {
                "all": spread([run[rule]["all"]["exact"] for run in complete]),
                "byFamily": {family: spread([run[rule]["byFamily"][family]["exact"] for run in complete])
                             for family in families}} for rule in (PRIMARY, SECONDARY)}
        methods.append(method)

    report = {
        "description": __doc__.split("\n")[0],
        "plan": PLAN, "planSha256": hashlib.sha256(plan_bytes).hexdigest(),
        "implementationRecord": RECORD, "implementationRecordSha256": hashlib.sha256(record_bytes).hexdigest(),
        "manifest": shown(args.manifest),
        "manifestSha256": hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
        "items": {"count": len(items),
                  "byFamily": {family: sum(item["family"] == family for item in items.values())
                               for family in families}},
        "rules": {"primary": PRIMARY, "secondary": SECONDARY},
        "keptElectronicSpellings": sorted(kept),
        "unreadable": "rows null: exact 0 under both rules, kept in the denominator",
        "wilson95": "summarize_chain_scores.wilson (proportion, 4 decimals)",
        "wilson95Percent": "summarize_text_route_full.wilson (percent rounded once from the raw value)",
        "methods": methods,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    for method in methods:
        for run in method["runs"]:
            tail = " INCOMPLETE" if "incomplete" in run else ""
            for rule in (PRIMARY, SECONDARY):
                block = run[rule]
                per = " ".join(f"{family} {block['byFamily'][family]['exact']}/{block['byFamily'][family]['n']}"
                               for family in families)
                print(f"{method['name']:34s} {run['run']:3s} {rule:12s} "
                      f"{block['all']['exact']}/{block['all']['n']} | {per}{tail}")


if __name__ == "__main__":
    main()
