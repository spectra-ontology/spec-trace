#!/usr/bin/env python3
"""결과 표(tab:results)의 조건마다 저장된 비용 측정이 무엇인지 적고, 원 기록에서 요약한다.

모델 · 네트워크 · 서비스 호출 없이 저장된 파일만 읽는다(SQLite 는 `mode=ro` 로 연다). 묶음은 여섯이다.

1. queryWriters: SQL · Cypher 질의 작성(Opus 하위 에이전트 실행 A 부터 J, Codex 세 조건)의 문항별 `seconds`.
   이 값은 밖에서 쓴 질의를 실행기가 실행하는 데 걸린 시간이고(질의를 쓰는 데 든 시간이 아니다) 0.1초로 반올림되어 있다.
   60초 상한은 `attempts` 의 오류 문구로도 본다(SQLite 는 `interrupted`, Neo4j 는 시간 초과 · 중단 오류 코드).
2. codex: `access_audit.json` 의 토큰 사용량 · 명령 수와 실행 기록의 벽시계 시간.
3. searchAgents: 풀이 세션이 스스로 적은 추적 기록의 문항별 명령 수(저장소 규칙대로 `--help` 실행은 뺀다),
   명령 기록(cmdlog), 도구 쪽 사용 기록(원문 검색 · 밀집 검색 도구), 저장된 요약과 세션 관찰 기록.
4. localReaders: 로컬 읽기 모델(closed book · dense · oracle)의 `seconds` 와 토큰 필드.
5. claudeSessions: 하위 에이전트 대화 기록의 처음 · 끝 시각과 응답 메시지 수(토큰 필드가 있는지도 본다).
6. corpusScale: 관계형 내보내기 · 그래프 · 벡터 컬렉션 · 글 색인의 크기와 건수.

조건마다 기록되지 않은 것은 `notRecorded` 에 적는다. 분위수는 가장 가까운 순위 방식이다
(정렬한 값에서 ceil(0.95·n) 번째). 중앙값은 `statistics.median`(짝수 개면 가운데 두 값의 평균)이다.
저장소 루트에서 실행한다.
"""
from __future__ import annotations

import argparse
import collections
import datetime
import hashlib
import json
import math
import re
import sqlite3
import statistics
import sys
from pathlib import Path

ROOT = Path.cwd()
TRACK = "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
SCRIPTS = "scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
README = "docs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/README.md"
ITEM_FILES = (f"{TRACK}/integration/items_final/gate/core/chain_items_admitted.jsonl",
              f"{TRACK}/integration/items_final/gate/ran5/chain_items_admitted.jsonl")
CE = f"{TRACK}/chain_eval"
SUP = f"{TRACK}/final/supplement_cycle"
ANALYSIS = f"{TRACK}/final/next_cycle/work/vldb_draft/analysis"
DEFAULT_OUT = f"{ANALYSIS}/stored_cost_inventory.json"
PROVENANCE = f"{CE}/subagent_model_provenance.json"
WGS = ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5")
RUNS = [f"run{letter}" for letter in "ABCDEFGHIJ"]
SURVEY_WORDS = ("input_tokens", "output_tokens", "total_tokens", "totalTokens", "subagentTokens", "tokensUsed",
                "wallSeconds", "wall_seconds", "wallClock", "wall=", "durationMs", "duration_ms", "elapsedSeconds")
SURVEY_SUFFIXES = (".json", ".jsonl", ".log", ".md", ".txt")

if not (ROOT / ".git").exists() or not (ROOT / CE).exists():
    sys.exit("저장소 루트에서 실행한다: 현재 폴더에 .git 과 결과 폴더가 없다")


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def jsonl(path: Path):
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def per_wg(template: str) -> list[str]:
    return [template.format(wg=wg) for wg in WGS]


def spread(values: list) -> dict:
    """건수 · 합 · 최소 · 중앙값 · 95번째 백분위(가장 가까운 순위) · 최대."""
    if not values:
        return {"count": 0}
    ordered = sorted(values)
    return {"count": len(ordered), "sum": round(sum(ordered), 3), "min": ordered[0],
            "median": round(statistics.median(ordered), 4), "p95": ordered[math.ceil(0.95 * len(ordered)) - 1],
            "max": ordered[-1]}


def counted(counter) -> dict:
    return {str(key): value for key, value in sorted(counter.items(), key=lambda pair: str(pair[0]))}


# ---------------------------------------------------------------- 1. 질의 작성

def query_conditions() -> list[tuple]:
    """(조건 이름, 표의 행, 질의 언어, {실행: 응답 파일})."""
    return [
        ("sql_claude", "Text-to-SQL, 10 runs | Opus 5.5", "sql",
         {run: per_wg(f"{CE}/text2sql/{{wg}}_text2sql_{run}.jsonl") for run in RUNS}),
        ("cypher_claude", "Text-to-Cypher, 10 runs | Opus 5.5", "cypher",
         {run: per_wg(f"{CE}/{{wg}}_text2cypher_claude_subagent_{run}.jsonl") for run in RUNS}),
        ("sql_codex_schema", "Text-to-SQL, schema | gpt-6.1-sol (Codex)", "sql",
         {"single": per_wg(f"{CE}/codex/chain_sql_{{wg}}_codex.jsonl")}),
        ("sql_codex_value_domains", "Text-to-SQL, value domains or exploration | gpt-6.1-sol (Codex)", "sql",
         {"single": per_wg(f"{CE}/codex_v2/responses/{{wg}}_sql_dom_codex.jsonl")}),
        ("sql_codex_exploration", "Text-to-SQL, value domains or exploration | gpt-6.1-sol (Codex)", "sql",
         {"single": per_wg(f"{CE}/codex_v2/responses/{{wg}}_sql_exp_codex.jsonl")}),
        ("cypher_codex_schema", "Text-to-Cypher, schema | gpt-6.1-sol (Codex)", "cypher",
         {"single": per_wg(f"{CE}/codex/chain_cy_{{wg}}_codex.jsonl")}),
        ("cypher_codex_value_domains", "Text-to-Cypher, value domains or exploration | gpt-6.1-sol (Codex)", "cypher",
         {"single": per_wg(f"{CE}/codex_v2/responses/{{wg}}_cy_dom_codex.jsonl")}),
        ("cypher_codex_exploration", "Text-to-Cypher, value domains or exploration | gpt-6.1-sol (Codex)", "cypher",
         {"single": per_wg(f"{CE}/codex_v2/responses/{{wg}}_cy_exp_codex.jsonl")}),
    ]


def error_kind(language: str, text: str) -> str:
    """오류 문구의 종류. Neo4j 는 오류 코드, SQLite 는 문구 앞부분."""
    if language == "cypher":
        code = re.search(r"code: ([\w.]+)", text)
        if code:
            return code.group(1)
    return text[:80]


def is_timeout(language: str, text: str) -> bool:
    """60초 상한에 걸린 오류인가. SQLite 는 진행 처리기가 끊어 `interrupted`, Neo4j 는 시간 초과 · 중단 코드."""
    if language == "sql":
        return text.strip().lower() == "interrupted"
    return bool(re.search(r"TimedOut|Timeout|Terminated", error_kind(language, text)))


def timed(records: list[dict]) -> dict:
    values = [r["seconds"] for r in records if r["seconds"] is not None]
    block = spread(values)
    block.update({
        "over1s": sum(v > 1 for v in values),
        "atOrAbove60s": sum(v >= 60 for v in values),
        "timeoutError": sum(r["timeout"] for r in records),
        "atOrAbove60sOrTimeoutError": sum(r["capped"] for r in records),
        "recordedAsZero": sum(v == 0 for v in values),
        "secondsMissing": len(records) - len(values)})
    return block


def by(records: list[dict], key: str) -> dict:
    groups = collections.defaultdict(list)
    for record in records:
        groups[record[key]].append(record)
    return {str(name): timed(group) for name, group in sorted(groups.items(), key=lambda pair: str(pair[0]))}


def where(records: list[dict]) -> dict:
    return {"records": len(records), "distinctItems": len({r["id"] for r in records}),
            "byRun": counted(collections.Counter(r["run"] for r in records)),
            "byFamily": counted(collections.Counter(r["family"] for r in records)),
            "byWg": counted(collections.Counter(r["wg"] for r in records)),
            "byRunAndFamily": counted(collections.Counter(f"{r['run']}/{r['family']}" for r in records))}


def brief(record: dict) -> dict:
    return {name: record[name] for name in ("run", "wg", "id", "family", "seconds", "errors")}


def query_writers(items: dict, qsha: dict) -> dict:
    out = {}
    for name, row, language, runs in query_conditions():
        records, tally = [], collections.Counter()
        attempts_per_record = collections.Counter()
        errors = collections.defaultdict(collections.Counter)
        for run, paths in runs.items():
            seen = set()
            for path in paths:
                for record in jsonl(ROOT / path):
                    tally["lines"] += 1
                    identifier = record["id"]
                    if identifier not in items:
                        tally["notInItems"] += 1
                        continue
                    if record.get("questionSha256") != qsha[identifier]:
                        tally["staleQuestion"] += 1
                        continue
                    tally["repeatedId"] += identifier in seen
                    seen.add(identifier)
                    attempts = record.get("attempts") or []
                    attempts_per_record[len(attempts)] += 1
                    texts = [str(a["error"]) for a in attempts if "error" in a]
                    kinds = [error_kind(language, text) for text in texts]
                    for kind in kinds:
                        errors[run][kind] += 1
                    seconds = record.get("seconds")
                    timeout = any(is_timeout(language, text) for text in texts)
                    records.append({"run": run, "wg": items[identifier]["wg"], "id": identifier,
                                    "family": items[identifier]["family"], "hops": items[identifier]["hops"],
                                    "seconds": seconds, "errors": kinds, "timeout": timeout,
                                    "rowsNone": record.get("rows") is None,
                                    "capped": timeout or (seconds is not None and seconds >= 60)})
        slow = [r for r in records if r["seconds"] is not None and r["seconds"] > 1]
        capped = [r for r in records if r["capped"]]
        slowest = sorted((r for r in records if r["seconds"] is not None), key=lambda r: -r["seconds"])[:10]
        out[name] = {
            "tableRow": row, "language": language, "runs": list(runs), "files": sum(len(p) for p in runs.values()),
            "recordTally": dict(tally), "records": len(records),
            "attemptsPerRecord": counted(attempts_per_record),
            "errorKindsByRun": {run: dict(kinds) for run, kinds in errors.items()},
            "rowsNone": sum(r["rowsNone"] for r in records),
            "all": timed(records), "perFamily": by(records, "family"), "perHops": by(records, "hops"),
            "perRun": by(records, "run"), "perWg": by(records, "wg"),
            "slow": {"over1s": where(slow), "atOrAbove60sOrTimeoutError": {**where(capped),
                                                                           "list": [brief(r) for r in capped]},
                     "slowest": [brief(r) for r in slowest]}}
    return {
        "what": "문항별 seconds = 실행기가 밖에서 쓴 질의를 실행한 시간(run_chain_eval.py 의 round(time.time() - started, 1)). "
                "질의를 쓰는 데 든 시간은 문항별로 기록되어 있지 않다. 상한은 질의당 60초"
                "(Cypher 는 tx.run(timeout=60), SQL 은 진행 처리기)이고 걸리면 오류로 남는다.",
        "filter": "id 가 지금 문항에 있고 questionSha256 이 지금 질문과 같은 줄",
        "conditions": out}


# ---------------------------------------------------------------- 2. Codex

def stamp(text: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_record_states() -> dict:
    """Codex 실행 기록의 before · after: 그래프 탐색 실행은 노드 · 관계 수, SQL 탐색 실행은 SQLite 파일의 sha256, 나머지는 빈 값."""
    graph, digests = {}, {}
    names = {"graphCounts": [], "sqliteSha256": [], "empty": [], "other": []}
    for run in jsonl(ROOT / f"{CE}/codex_v2/run_records/runs.jsonl"):
        states = [run.get("before"), run.get("after")]
        if all(isinstance(state, dict) for state in states):
            names["graphCounts"].append(run["name"])
            graph.setdefault(run["wg"], set()).update(json.dumps(state, sort_keys=True) for state in states)
        elif all(isinstance(state, str) for state in states):
            names["sqliteSha256"].append(run["name"])
            digests.setdefault(run["wg"], set()).update(states)
        elif all(state is None for state in states):
            names["empty"].append(run["name"])
        else:
            names["other"].append(run["name"])
    now = {wg: file_sha256(ROOT / f"{TRACK}/integration/sqlite_final/{wg}.sqlite") for wg in sorted(digests)}
    replay_path = f"{TRACK}/final/ran2_query_replay/replay.json"
    replay = None
    if (ROOT / replay_path).is_file():
        stored = json.loads((ROOT / replay_path).read_text())
        stores, totals = stored["stores"], stored["sql"]["totals"]
        replay = {"source": replay_path, "purpose": stored["purpose"],
                  "predecessorSha256": stores["predecessor"]["sha256"], "releaseSha256": stores["release"]["sha256"],
                  "predecessorEqualsRunRecord": digests.get("RAN2") == {stores["predecessor"]["sha256"]},
                  "releaseEqualsFileNow": now.get("RAN2") == stores["release"]["sha256"],
                  "tablesWithDifferences": {table: {"rowsPredecessor": block["rowsPredecessor"],
                                                    "rowsRelease": block["rowsRelease"],
                                                    "onlyPredecessor": len(block["onlyPredecessor"]),
                                                    "onlyRelease": len(block["onlyRelease"])}
                                            for table, block in stored["storeDifference"]["tablesWithDifferences"].items()},
                  "sqlResponseFiles": sorted(stored["sql"]["files"]), "sqlTotals": totals}
    return {"source": f"{CE}/codex_v2/run_records/runs.jsonl",
            "ran2ReplayRecord": replay,
            "runsByKind": names,
            "graphCountsByWg": {wg: [json.loads(text) for text in sorted(values)] for wg, values in sorted(graph.items())},
            "graphNote": "WG 마다 값이 하나면 그 실행의 앞과 뒤에서 수가 같았다는 뜻이다. 이 스크립트는 그래프에 접속하지 않는다.",
            "sqliteSha256ByWg": {wg: sorted(values) for wg, values in sorted(digests.items())},
            "sqliteSha256Now": now,
            "sqliteFileNowEqualsRunRecord": {wg: digests[wg] == {now[wg]} for wg in sorted(digests)}}


def codex_block() -> dict:
    names = {("chain", "sql"): "sql_codex_schema", ("chain", "cy"): "cypher_codex_schema",
             ("abs", "cy"): "abstention_cypher (tab:results 의 조건이 아니다)",
             ("dom", "sql"): "sql_codex_value_domains", ("dom", "cy"): "cypher_codex_value_domains",
             ("exp", "sql"): "sql_codex_exploration", ("exp", "cy"): "cypher_codex_exploration"}
    conditions: dict[str, dict] = {}

    def slot(kind: str, language: str) -> dict:
        return conditions.setdefault(names[(kind, language)], {"runs": 0, "usage": collections.Counter(),
                                                               "nCommands": 0, "perWg": {}})

    sources = {"schema": f"{CE}/codex/access_audit.json", "valueDomainsAndExploration": f"{CE}/codex_v2/access_audit.json"}
    for path in sources.values():
        for run in json.loads((ROOT / path).read_text())["runs"]:
            kind, language, wg = (run.get("dir") or run["name"]).split("_")
            block = slot(kind, language)
            block["runs"] += 1
            block["nCommands"] += run["nCommands"]
            block["usage"].update({k: v for k, v in run["usage"].items() if isinstance(v, (int, float))})
            block["perWg"][wg] = {"usage": run["usage"], "nCommands": run["nCommands"]}

    # 벽시계 시간: 스키마 조건은 호출 기록의 시작 · 끝 줄에서, 뒤 두 조건은 실행 기록의 wallSeconds 에서 읽는다.
    wall_sources = {"schema": f"{CE}/codex/invocation/run_all.log", "valueDomainsAndExploration":
                    f"{CE}/codex_v2/run_records/runs.jsonl"}
    started = {}
    for line in (ROOT / wall_sources["schema"]).read_text().splitlines():
        begin = re.fullmatch(r"start (\S+) (\S+)", line.strip())
        end = re.fullmatch(r"end (\S+) exit=(\d+) (\S+)(?: lines=(\d+))?", line.strip())
        if begin:
            started[begin.group(1)] = stamp(begin.group(2))
        elif end and end.group(1) in started:
            kind, language, wg = end.group(1).split("_")
            block = slot(kind, language)
            seconds = (stamp(end.group(3)) - started[end.group(1)]).total_seconds()
            block.setdefault("wall", {})[wg] = {"seconds": seconds, "exit": int(end.group(2)),
                                                "from": "invocation/run_all.log 의 start · end 시각 차이"}
    for run in jsonl(ROOT / wall_sources["valueDomainsAndExploration"]):
        block = slot(run["condition"], run["language"])
        block.setdefault("wall", {})[run["wg"]] = {"seconds": run["wallSeconds"], "exit": run["exit"],
                                                   "items": run["items"], "queryLines": run["queryLines"],
                                                   "from": "run_records/runs.jsonl 의 wallSeconds"}
    for block in conditions.values():
        block["usage"] = dict(block["usage"])
        walls = [w["seconds"] for w in block.get("wall", {}).values()]
        block["wallSecondsSum"] = round(sum(walls), 1) if walls else None
        block["wallRuns"] = len(walls)

    # 질의 실행(평가) 쪽 벽시계 시간: 뒤 두 조건만 eval_all.log 에 WG 별로 남아 있다.
    evaluation = collections.defaultdict(dict)
    for line in (ROOT / f"{CE}/codex_v2/responses/eval_all.log").read_text().splitlines():
        found = re.fullmatch(r"eval (\w+)_(\w+)_(RAN\d) exit=(\d+) wall=(\d+)s lines=(\d+)", line.strip())
        if found:
            evaluation[names[(found.group(1), found.group(2))]][found.group(3)] = int(found.group(5))
    return {
        "what": "토큰은 Codex `--json` 이벤트에서 감사 스크립트가 옮겨 적은 usage 값을 조건별로 더한 것이다. "
                "cached_input_tokens 가 input_tokens 에 포함되는지는 기록에 적혀 있지 않다. 한 실행은 한 WG 의 문항 묶음 전체다.",
        "sources": {"tokens": sources, "wall": wall_sources, "evaluationWall": f"{CE}/codex_v2/responses/eval_all.log"},
        "conditions": conditions,
        "evaluationWallSecondsByWg": {name: {"byWg": walls, "sum": sum(walls.values())}
                                      for name, walls in evaluation.items()},
        "beforeAfterInRunRecords": run_record_states()}


# ---------------------------------------------------------------- 3. 검색 에이전트

def search_runs() -> list[tuple]:
    """(조건, 표의 행, {실행: (추적 기록 폴더, 응답 파일)})."""
    def supplement(agent: str, run: str, name: str) -> tuple:
        return (f"{SUP}/{agent}/{run}/collected/session_outputs",
                per_wg(f"{SUP}/{agent}/{run}/collected/{{wg}}_{name}_claude_subagent.jsonl"))

    def chain(folder: str, name: str) -> tuple:
        return (f"{CE}/{folder}/solver_logs", per_wg(f"{CE}/{folder}/{{wg}}_{name}_claude_subagent.jsonl"))

    return [
        ("text_search_text_only", "Text search, text only, 3 runs | Opus 5.5",
         {"runA": chain("text_only_full", "text_search_text_only"),
          "runB": supplement("text_only_agent", "runB", "text_only"),
          "runC": supplement("text_only_agent", "runC", "text_only")}),
        ("text_search", "Text search, 3 runs | Opus 5.5",
         {"runA": chain("text_search_full", "text_search"), "runB": chain("text_search_full_runB", "text_search"),
          "runC": chain("text_search_full_runC", "text_search")}),
        ("raw_text_search", "Raw-text search, 2 runs | Opus 5.5",
         {run: supplement("raw_agent", run, "raw_index") for run in ("runA", "runB")}),
        ("dense_tool", "Dense tool, 2 runs | Opus 5.5",
         {run: supplement("dense_agent", run, "dense_tool") for run in ("runA", "runB")}),
        ("dense_tool_capped", "Dense tool, 61 chunks per call | Opus 5.5",
         {"runA": supplement("dense_capped_agent", "runA", "dense_tool_capped")}),
    ]


def small(values: list[int]) -> dict:
    block = spread(values)
    return {"items": block["count"], "total": block.get("sum"), "median": block.get("median"),
            "p95": block.get("p95"), "max": block.get("max"), "min": block.get("min")}


def trace_run(folder: str, responses: list[str], items: dict) -> dict:
    """한 실행의 추적 기록. 문항별 명령 수는 저장소의 세는 법(`--help` 가 든 명령은 뺀다)을 따른다."""
    packet = {}
    for path in responses:
        for record in jsonl(ROOT / path):
            if record.get("packetId"):
                packet[record["packetId"]] = record["id"]
    per_item: dict[str, dict] = {}
    sessions: dict[str, int] = {}
    tally = collections.Counter()
    odd_names = []
    files = sorted((ROOT / folder).glob("*_trace.jsonl"))
    for path in files:
        session = path.name[:-len("_trace.jsonl")]
        if not re.fullmatch(r"RAN\d_part\d+", session):
            odd_names.append(path.name)
        sessions[session] = 0
        for record in jsonl(path):
            commands = [str(c) for c in (record.get("commands") or [])]
            non_help = sum("--help" not in c.split() for c in commands)
            tally["traceLines"] += 1
            tally["commands"] += len(commands)
            tally["nonHelpCommands"] += non_help
            if isinstance(record.get("searches"), int):
                tally["searchesFieldSum"] += record["searches"]
            else:
                tally["searchesFieldMissing"] += 1
            tally["repeatedIds"] += record["id"] in per_item
            sessions[session] += non_help
            per_item[record["id"]] = {"nonHelp": non_help, "session": session}
    families, hops = collections.defaultdict(list), collections.defaultdict(list)
    unmapped = 0
    for identifier, entry in per_item.items():
        item = items.get(packet.get(identifier, identifier))
        if item is None:
            unmapped += 1
            continue
        families[item["family"]].append(entry["nonHelp"])
        hops[str(item["hops"])].append(entry["nonHelp"])
    values = [entry["nonHelp"] for entry in per_item.values()]
    logs = sorted((ROOT / folder).glob("*_cmdlog.jsonl"))
    logged = {path.name[:-len("_cmdlog.jsonl")]: sum(1 for _ in jsonl(path)) for path in logs}
    return {
        "traceFolder": folder, "traceFiles": len(files), "unexpectedTraceFileNames": odd_names,
        **{name: tally.get(name, 0) for name in ("traceLines", "commands", "nonHelpCommands", "searchesFieldSum",
                                                 "searchesFieldMissing", "repeatedIds")},
        "idsNotMappedToAnItem": unmapped,
        "perItemNonHelpCommands": {**small(values), "itemsWithZero": sum(v == 0 for v in values)},
        "perSessionNonHelpCommands": {**small(list(sessions.values())), "bySession": sessions},
        "perFamilyNonHelpCommands": {family: small(v) for family, v in sorted(families.items())},
        "perHopsNonHelpCommands": {hop: small(v) for hop, v in sorted(hops.items())},
        "cmdlog": {"files": len(logs), "lines": sum(logged.values()),
                   "sessionsWithTraceButNoCmdlog": sorted(set(sessions) - set(logged))}}


def usage_stats(records: list[dict], session_of) -> dict:
    """도구 쪽 사용 기록(호출 한 번이 한 줄)의 요약."""
    per_session = collections.Counter(session_of(r) for r in records)
    seconds = [r["seconds"] for r in records if isinstance(r.get("seconds"), (int, float))]
    results = [r["results"] for r in records if isinstance(r.get("results"), (int, float))]
    tops = [r["top"] for r in records if isinstance(r.get("top"), (int, float))]
    return {"calls": len(records), "sessions": len(per_session),
            "callsPerSession": {**{k: v for k, v in spread(list(per_session.values())).items() if k != "count"},
                                "bySession": counted(per_session)},
            "secondsPerCall": spread(seconds), "secondsMissing": len(records) - len(seconds),
            "resultsPerCall": spread(results), "requestedTopMedian": statistics.median(tops) if tops else None}


def tool_side_usage() -> dict:
    out = {}
    raw = {}
    for run in ("runA", "runB"):
        folder = ROOT / f"{SUP}/raw_agent/{run}/usage"
        records, files, set_aside = [], {}, {}
        for path in sorted(folder.glob("*.jsonl")):
            lines = [{**record, "_session": path.stem} for record in jsonl(path)]
            if re.fullmatch(r"RAN\d_part\d+", path.stem):
                files[path.stem] = len(lines)
                records += lines
            else:
                set_aside[path.name] = len(lines)
        raw[run] = {"folder": f"{SUP}/raw_agent/{run}/usage", "files": len(files) + len(set_aside),
                    "linesAllFiles": sum(files.values()) + sum(set_aside.values()),
                    "filesNotNamedAsOneSession": set_aside,
                    **usage_stats(records, lambda r: r["_session"])}
    out["raw_text_search"] = {"recordKeys": "wg, query, doc, source, top, chars, raw, results, seconds", "runs": raw}

    for name, path, pattern in (("dense_tool", f"{SUP}/dense_tool/usage.jsonl", r"dense_(run[A-Z])_(RAN\d_part\d+)"),
                                ("dense_tool_capped", f"{SUP}/dense_tool/usage_capped.jsonl",
                                 r"dense_capped_(run[A-Z])_(RAN\d_part\d+)")):
        grouped, other, lines = collections.defaultdict(list), collections.Counter(), 0
        for record in jsonl(ROOT / path):
            lines += 1
            found = re.fullmatch(pattern, str(record.get("label")))
            if found:
                grouped[found.group(1)].append({**record, "_session": found.group(2)})
            else:
                other[str(record.get("label"))] += 1
        out[name] = {"file": path, "lines": lines, "linesWithOtherLabels": counted(other),
                     "recordKeys": "wg, query, top, collection, label, results, seconds"
                                   + (", maxTop" if name.endswith("capped") else ""),
                     "runs": {run: usage_stats(records, lambda r: r["_session"]) for run, records in sorted(grouped.items())}}
    stored = {name: json.loads((ROOT / f"{SUP}/dense_tool/{name}").read_text())
              for name in ("usage_summary.json", "usage_capped_summary.json")}
    dense_runs = out["dense_tool"]["runs"]
    out["storedSummaries"] = {
        "files": {name: f"{SUP}/dense_tool/{name}" for name in stored}, "content": stored,
        "callsAgreeWithThisScript": {
            "dense_runA": stored["usage_summary.json"]["runs"]["dense_runA"]["calls"] == dense_runs["runA"]["calls"],
            "dense_runB": stored["usage_summary.json"]["runs"]["dense_runB"]["calls"] == dense_runs["runB"]["calls"],
            "dense_capped_runA": stored["usage_capped_summary.json"]["calls"]
            == out["dense_tool_capped"]["runs"]["runA"]["calls"]}}
    out["notLogged"] = ("글 색인 검색 도구(text search · text only)는 도구 쪽 사용 기록이 없다. 원문 검색 · 밀집 검색 도구의 "
                        "사용 기록에는 문항 id 가 없어 호출을 문항에 붙일 수 없다(세션 단위까지만).")
    return out


def self_reports() -> dict:
    """세션이 끝나며 스스로 알린 도구 실행 수(관찰 기록에 옮겨 적힌 값)."""
    out = {}
    for agent in ("text_only_agent", "dense_agent", "dense_capped_agent"):
        path = f"{SUP}/{agent}/session_observations.jsonl"
        runs = collections.defaultdict(lambda: {"sessionsReporting": 0, "toolRunsReported": 0})
        lines = 0
        for record in jsonl(ROOT / path):
            lines += 1
            if isinstance(record.get("toolRunsReported"), (int, float)):
                runs[str(record.get("run"))]["sessionsReporting"] += 1
                runs[str(record.get("run"))]["toolRunsReported"] += record["toolRunsReported"]
        out[agent] = {"file": path, "lines": lines, "byRun": dict(sorted(runs.items()))}
    path = f"{SUP}/raw_agent/session_incidents.jsonl"
    out["raw_agent"] = {"file": path, "lines": sum(1 for _ in jsonl(ROOT / path)),
                        "note": "사건 기록이며 toolRunsReported 필드는 없다"}
    return out


def find_key(value, key: str, trail: str = "") -> dict:
    found = {}
    if isinstance(value, dict):
        for name, inner in value.items():
            if name == key:
                found[f"{trail}/{name}"] = inner
            else:
                found.update(find_key(inner, key, f"{trail}/{name}"))
    elif isinstance(value, list):
        for index, inner in enumerate(value):
            found.update(find_key(inner, key, f"{trail}[{index}]"))
    return found


def search_agents(items: dict) -> dict:
    conditions = {}
    for name, row, runs in search_runs():
        conditions[name] = {"tableRow": row,
                            "runs": {run: trace_run(folder, responses, items) for run, (folder, responses) in runs.items()}}
    stored = f"{CE}/text_search_full/route_comparison.json"
    return {
        "what": "추적 기록(_trace.jsonl)은 풀이 세션이 문항마다 스스로 적은 명령 목록이다. 문항별 시간 · 토큰은 없다.",
        "conditions": conditions,
        "toolSideUsage": tool_side_usage(),
        "sessionSelfReports": self_reports(),
        "storedSearchesPerItem": {"file": stored,
                                  "blocks": find_key(json.loads((ROOT / stored).read_text()), "searchesPerItem")}}


# ---------------------------------------------------------------- 4. 로컬 읽기 모델

def local_readers(items: dict, qsha: dict) -> dict:
    listed = [
        ("closed_book | llama3.1:8b", f"{CE}/{{wg}}_closed_book_llama3_1_8b.jsonl"),
        ("closed_book | qwen2.5:14b", f"{CE}/{{wg}}_closed_book_qwen2_5_14b.jsonl"),
        ("dense_8_chunks | llama3.1:8b", f"{CE}/{{wg}}_dense_llama3_1_8b.jsonl"),
        ("dense_8_chunks | qwen2.5:14b", f"{CE}/{{wg}}_dense_qwen2_5_14b.jsonl"),
        ("oracle_evidence | llama3.1:8b", f"{CE}/oracle_evidence/{{wg}}_oracle_evidence_llama3_1_8b.jsonl"),
        ("oracle_evidence | qwen2.5:14b", f"{CE}/oracle_evidence/{{wg}}_oracle_evidence_qwen2_5_14b.jsonl"),
        ("oracle_evidence_text_only | llama3.1:8b",
         f"{CE}/oracle_evidence/{{wg}}_oracle_evidence_textonly_llama3_1_8b.jsonl"),
    ]
    out = {}
    for name, template in listed:
        seconds, families = [], collections.defaultdict(list)
        keys, oracle_keys, attempt_keys = collections.Counter(), collections.Counter(), collections.Counter()
        tally, attempts_per_record, contexts = collections.Counter(), collections.Counter(), collections.Counter()
        tokens, problems = collections.Counter(), collections.Counter()
        for path in per_wg(template):
            for record in jsonl(ROOT / path):
                tally["lines"] += 1
                identifier = record["id"]
                if identifier not in items:
                    tally["notInItems"] += 1
                    continue
                if record.get("questionSha256") != qsha[identifier]:
                    tally["staleQuestion"] += 1
                    continue
                tally["kept"] += 1
                tally["rowsNone"] += record.get("rows") is None
                if "error" in record:
                    problems[f"record.error: {str(record['error'])[:60]}"] += 1
                keys.update(record.keys())
                if isinstance(record.get("seconds"), (int, float)):
                    seconds.append(record["seconds"])
                    families[items[identifier]["family"]].append(record["seconds"])
                oracle = record.get("oracle")
                if isinstance(oracle, dict):
                    oracle_keys.update(oracle.keys())
                    attempts = oracle.get("attempts") or []
                    attempts_per_record[len(attempts)] += 1
                    tokens["promptChars"] += oracle.get("promptChars") or 0
                    for index, attempt in enumerate(attempts):
                        attempt_keys.update(attempt.keys())
                        if attempt.get("timedOut"):
                            problems[f"attempt.timedOut: {attempt['timedOut']}"] += 1
                        tokens["prompt_eval_count_allAttempts"] += attempt.get("prompt_eval_count") or 0
                        tokens["eval_count_allAttempts"] += attempt.get("eval_count") or 0
                        if index == len(attempts) - 1:
                            tokens["prompt_eval_count_lastAttempt"] += attempt.get("prompt_eval_count") or 0
                            tokens["eval_count_lastAttempt"] += attempt.get("eval_count") or 0
                            contexts[attempt.get("numCtx")] += 1
        token_like = sorted(k for k in list(keys) + list(oracle_keys) + list(attempt_keys)
                            if re.search(r"token|eval_count", k, re.I))
        out[name] = {"files": per_wg(template), "recordTally": dict(tally),
                     "recordKeys": sorted(keys), "oracleKeys": sorted(oracle_keys), "attemptKeys": sorted(attempt_keys),
                     "tokenLikeKeys": token_like, "errorsAndTimeouts": dict(problems),
                     "seconds": {**spread(seconds), "over1s": sum(v > 1 for v in seconds),
                                 "atOrAbove60s": sum(v >= 60 for v in seconds)},
                     "secondsPerFamily": {family: spread(v) for family, v in sorted(families.items())},
                     **({"oracle": {"sums": dict(tokens), "attemptsPerRecord": counted(attempts_per_record),
                                    "numCtxOfLastAttempt": counted(contexts)}} if oracle_keys else {})}
    return {"what": "seconds = 실행기가 문항 하나를 푸는 데 걸린 벽시계 시간(0.1초 단위). dense 는 검색(질문 임베딩 · 벡터 검색)과 "
                    "생성이 한 값에 합쳐져 있다. 토큰 수는 oracle 조건의 attempts 에만 있다(ollama 의 prompt_eval_count · eval_count).",
            "conditions": out}


# ---------------------------------------------------------------- 5. Opus 하위 에이전트 세션

ROW_OF = {
    "Text-to-SQL, 10 runs": ("text2sql_runA_runB", "text2sql_runs_C_to_E", "text2sql_runs_F_to_J"),
    "Text-to-Cypher, 10 runs": ("text2cypher_runA_runB", "text2cypher_runs_C_to_E", "text2cypher_runs_F_to_J"),
    "Text search, 3 runs": ("text_search", "text_search_runB", "text_search_runC"),
    "Text search, text only, 3 runs": ("text_search_text_only", "text_search_text_only_runB", "text_search_text_only_runC"),
    "Raw-text search, 2 runs": ("raw_index_runA", "raw_index_runB"),
    "Dense tool, 2 runs": ("dense_tool_runA", "dense_tool_runB"),
    "Dense tool, 61 chunks per call": ("dense_tool_capped_runA",),
}


def keys_like(value, pattern: str, trail: str = "", found=None) -> dict:
    found = collections.Counter() if found is None else found
    if isinstance(value, dict):
        for name, inner in value.items():
            if re.search(pattern, name, re.I):
                found[re.sub(r"\[\d+\]", "[]", f"{trail}/{name}")] += 1
            keys_like(inner, pattern, f"{trail}/{name}", found)
    elif isinstance(value, list):
        for index, inner in enumerate(value):
            keys_like(inner, pattern, f"{trail}[{index}]", found)
    return found


def claude_sessions(transcript_root: Path | None) -> dict:
    record = json.loads((ROOT / PROVENANCE).read_text())
    conditions, agent_condition = {}, {}
    for name, by_wg in record["conditions"].items():
        agents = [agent for wg in by_wg for agent in by_wg[wg]]
        spans = [(stamp(a["ended"]) - stamp(a["started"])).total_seconds() for a in agents]
        earlier = [e for a in agents for e in (a.get("relaunchOf") or []) if isinstance(e, dict)]
        earlier_spans = [(stamp(e["ended"]) - stamp(e["started"])).total_seconds()
                         for e in earlier if e.get("started") and e.get("ended")]
        models = collections.Counter(model for a in agents for model in a.get("models", []))
        followups = collections.Counter()
        for agent in agents:
            followups.update(agent.get("followupKinds") or {})
            agent_condition[agent["agentId"]] = name
        block = {"tableRow": next((row for row, names in ROW_OF.items() if name in names), None),
                 "agents": len(agents), "agentsByWg": {wg: len(by_wg[wg]) for wg in by_wg},
                 "spanSeconds": {k: round(v, 1) for k, v in spread(spans).items()},
                 "assistantMessages": sum(a.get("assistantMessages") or 0 for a in agents),
                 "models": dict(models), "followupKinds": dict(followups),
                 "agentsWithEarlierAttempt": sum(bool(a.get("relaunchOf")) for a in agents),
                 "earlierAttempts": len(earlier),
                 "earlierAttemptSpanSecondsSum": round(sum(earlier_spans), 1),
                 "tokenLikeKeysInAgentRecords": dict(keys_like(agents, r"token|usage|cost"))}
        if transcript_root is not None:
            present = usage_lines = 0
            for agent in agents:
                path = transcript_root / str(agent.get("session")) / "subagents" / f"agent-{agent['agentId']}.jsonl"
                if path.exists():
                    present += 1
                    with open(path, "rb") as handle:
                        usage_lines += sum(b'"usage"' in line for line in handle)
            block["transcripts"] = {"present": present, "linesWithUsageField": usage_lines}
        conditions[name] = block
    rows = {}
    for row, names in ROW_OF.items():
        blocks = [conditions[name] for name in names if name in conditions]
        rows[row] = {"provenanceConditions": [name for name in names if name in conditions],
                     "agents": sum(b["agents"] for b in blocks),
                     "spanSecondsSum": round(sum(b["spanSeconds"].get("sum", 0) for b in blocks), 1),
                     "spanSecondsMax": max((b["spanSeconds"].get("max", 0) for b in blocks), default=None),
                     "assistantMessages": sum(b["assistantMessages"] for b in blocks),
                     "agentsWithEarlierAttempt": sum(b["agentsWithEarlierAttempt"] for b in blocks),
                     "earlierAttemptSpanSecondsSum": round(sum(b["earlierAttemptSpanSecondsSum"] for b in blocks), 1)}
    audit = record.get("accessAudit", {}).get("agents", {})
    tools, covered = collections.Counter(), collections.Counter()
    for agent_id, entry in audit.items():
        tools.update(entry.get("tools") or {})
        covered[agent_condition.get(agent_id, "provenance conditions 의 현재 에이전트 목록에 없음")] += 1
    return {
        "source": PROVENANCE,
        "what": "started · ended 는 수집 스크립트(chain_eval/collect_subagent_model_provenance.py)가 대화 기록 줄들의 "
                "timestamp 최솟값 · 최댓값으로 적은 것이다. 따라서 span 은 도구 실행 대기 · 쉬는 시간 · 뒤따른 지시까지 담은 "
                "처음부터 끝까지의 길이이며 모델이 일한 시간이 아니다. 여러 세션이 함께 돌았으므로 합은 벽시계 시간이 아니다.",
        "tokenFields": "provenance 의 Claude 에이전트 기록에는 토큰 필드가 없다(tokenLikeKeysInAgentRecords 참조). "
                       "networkOrDbTokens 는 접근 감사가 찾은 낱말 목록이며 토큰 사용량이 아니다.",
        "conditions": conditions, "byTableRow": rows,
        "accessAuditToolCalls": {"agents": len(audit), "agentsByCondition": dict(covered), "tools": dict(tools)},
        "transcriptCheck": None if transcript_root is None else
        "대화 기록 파일이 있는지와 `\"usage\"` 가 든 줄 수만 셌다. 토큰 합은 내지 않았다(같은 응답의 줄이 usage 를 되풀이해 "
        "싣는지 확인하지 않았다). 대화 기록은 저장소 밖의 호스트 자원이다."}


# ---------------------------------------------------------------- 6. 말뭉치 규모

def corpus_scale() -> dict:
    manifest_path = f"{TRACK}/integration/sqlite_final/export_manifest.json"
    manifest = json.loads((ROOT / manifest_path).read_text())["exports"]
    relational = {}
    for wg in WGS:
        path = ROOT / f"{TRACK}/integration/sqlite_final/{wg}.sqlite"
        db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            tables = [name for (name,) in db.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
            rows = {table: db.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0] for table in tables}
        finally:
            db.close()
        relational[wg] = {"file": str(path.relative_to(ROOT)), "bytesOnDisk": path.stat().st_size,
                          "manifestDatabaseBytes": manifest[wg]["databaseBytes"],
                          "rowsCountedNow": rows, "rowsTotal": sum(rows.values()),
                          "rowsEqualManifest": rows == manifest[wg]["tableRows"],
                          "bytesEqualManifest": path.stat().st_size == manifest[wg]["databaseBytes"]}
    composition_path = f"{TRACK}/text_route_ceiling/index_composition.json"
    composition = json.loads((ROOT / composition_path).read_text())["wgs"]
    vectors, totals = {}, collections.Counter()
    for wg in WGS:
        vectors[wg] = {}
        for kind, entry in composition[wg].items():
            index = entry.get("index") or {}
            vectors[wg][kind] = {"collection": entry["collection"], "points": entry["points"],
                                 "vectorSize": entry["vectors"]["size"], "distance": entry["vectors"]["distance"],
                                 "documents": index.get("documents"), "storedInTextIndex": index.get("stored")}
            totals[f"{kind}.points"] += entry["points"]
            totals[f"{kind}.documents"] += index.get("documents") or 0
            totals["all.points"] += entry["points"]
    text_index = {}
    for wg in WGS:
        path = ROOT / f"{TRACK}/text_route_ceiling/index/{wg.lower()}.sqlite3"
        db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            columns = [row[1] for row in db.execute("PRAGMA table_info(manifest)")]
            listed = [dict(zip(columns, row)) for row in db.execute("SELECT * FROM manifest")]
            info = dict(db.execute("SELECT name, value FROM build_info").fetchall())
        finally:
            db.close()
        text_index[wg] = {"file": str(path.relative_to(ROOT)), "bytesOnDisk": path.stat().st_size,
                          "manifestTable": listed, "buildInfoTable": info,
                          "storedTotal": sum(row.get("stored") or 0 for row in listed)}
    census_path = f"{TRACK}/final/raw_source_route/plenary_census.json"
    census = json.loads((ROOT / census_path).read_text())
    raw_path = ROOT / f"{TRACK}/final/raw_source_route/index/plenary.sqlite3"
    states = run_record_states()
    return {
        "relationalExport": {"manifest": manifest_path, "byWg": relational,
                             "bytesTotal": sum(entry["bytesOnDisk"] for entry in relational.values()),
                             "rowsTotal": sum(entry["rowsTotal"] for entry in relational.values()),
                             "documentRowsTotal": sum(entry["rowsCountedNow"].get("document", 0)
                                                      for entry in relational.values())},
        "graph": {"source": f"{CE}/codex_v2/run_records/runs.jsonl 의 before · after(그래프 탐색 실행 앞뒤에 센 노드 · 관계 수)",
                  "runs": states["runsByKind"]["graphCounts"], "byWg": states["graphCountsByWg"],
                  "nodesTotal": sum(counts[0]["nodes"] for counts in states["graphCountsByWg"].values()
                                    if len(counts) == 1),
                  "relationshipsTotal": sum(counts[0]["relationships"] for counts in states["graphCountsByWg"].values()
                                            if len(counts) == 1),
                  "note": states["graphNote"]},
        "vectorCollections": {"source": composition_path, "byWg": vectors, "totals": dict(totals),
                              "note": "기록된 값을 옮긴 것이며 이 스크립트는 벡터 저장소에 접속하지 않는다."},
        "textIndex": {"byWg": text_index, "bytesTotal": sum(entry["bytesOnDisk"] for entry in text_index.values()),
                      "storedTotal": sum(entry["storedTotal"] for entry in text_index.values())},
        "rawTextIndex": {"file": str(raw_path.relative_to(ROOT)), "bytesOnDisk": raw_path.stat().st_size,
                         "census": census_path,
                         "censusFigures": {name: census.get(name) for name in
                                           ("inodesStored", "distinctContents", "filesByOpener", "filesByOutcome",
                                            "chunks", "memberOwnNumbers", "indexBytes")},
                         "membersFound": (census.get("members") or {}).get("found"),
                         "membersByOutcome": (census.get("members") or {}).get("byOutcome"),
                         "bytesEqualCensus": raw_path.stat().st_size == census.get("indexBytes")}}


# ---------------------------------------------------------------- 저장 기록 훑기

def survey() -> dict:
    """결과 폴더의 글 파일에서 토큰 · 벽시계 시간 필드 이름을 찾는다(이 분석 폴더는 뺀다)."""
    pattern = re.compile("|".join(re.escape(word) for word in SURVEY_WORDS).encode())
    base, skip = ROOT / TRACK, ROOT / ANALYSIS
    hits, scanned, size = [], 0, 0
    for path in sorted(base.rglob("*")):
        if path.suffix not in SURVEY_SUFFIXES or not path.is_file() or skip in path.parents:
            continue
        scanned += 1
        size += path.stat().st_size
        tail = b""
        with open(path, "rb") as handle:
            while True:
                chunk = handle.read(4 * 1024 * 1024)
                if not chunk:
                    break
                if pattern.search(tail + chunk):
                    hits.append(str(path.relative_to(base)))
                    break
                tail = chunk[-32:]
    groups = collections.Counter("/".join(hit.split("/")[:3]) for hit in hits)
    return {"searchedFor": list(SURVEY_WORDS), "suffixes": list(SURVEY_SUFFIXES), "filesScanned": scanned,
            "bytesScanned": size, "filesWithAHit": len(hits), "hitsByFolder": counted(groups),
            "hitsOutsideRunRecords": [hit for hit in hits if "/run_records/" not in hit]}


def readme_lines() -> list[dict]:
    found = []
    with open(ROOT / README, encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if re.search(r"token|토큰|wall", line, re.I):
                found.append({"line": number, "text": line.strip()[:200]})
    return found


def other_records() -> dict:
    """표의 조건이 아닌 다른 실행에 대한 토큰 · 벽시계 기록(있다는 사실과 합만 적는다)."""
    out = {}
    headroom = f"{TRACK}/final/next_cycle/work/opus_headroom/run_log.json"
    if (ROOT / headroom).exists():
        log = json.loads((ROOT / headroom).read_text())
        out["opusHeadroomRunLog"] = {
            "file": headroom, "purpose": log.get("purpose"),
            "launches": [{name: launch.get(name) for name in ("kind", "runs", "sessions", "returned", "relaunched",
                                                             "width", "wallSeconds", "subagentTokens", "toolUses")}
                         for launch in log.get("launches", [])],
            "note": "다음 주기의 헤드룸 분할에서 새로 띄운 세션의 기록이며 tab:results 의 실행이 아니다."}
    for name, path in (("codexSecond", f"{SUP}/codex_second/access_audit.json"),
                       ("freshCodex", f"{TRACK}/final/chain_rederivation/fresh_codex/access_audit.json")):
        if (ROOT / path).exists():
            total = collections.Counter()
            by_wg = json.loads((ROOT / path).read_text()).get("byWg", {})
            for entry in by_wg.values():
                total.update({k: v for k, v in (entry.get("usage") or {}).items() if isinstance(v, (int, float))})
            out[name] = {"file": path, "wgs": sorted(by_wg), "usageSum": dict(total),
                         "commands": sum(entry.get("commands") or 0 for entry in by_wg.values()),
                         "note": "tab:results 의 행이 아닌 다른 Codex 실행의 감사 기록."}
    return out


NOT_RECORDED = {
    "Closed-book | llama3.1:8b, qwen2.5:14b": [
        "토큰 수(프롬프트 · 생성) 필드가 응답 기록에 없다", "seconds 는 문항당 한 값이고 0.1초 단위다"],
    "Dense, 8 chunks | llama3.1:8b / qwen2.5:14b": [
        "토큰 수 필드가 없다", "검색 시간과 생성 시간이 나뉘어 있지 않다(한 seconds 값)"],
    "Oracle evidence (text only 포함) | llama3.1:8b / qwen2.5:14b": [
        "빈 정답 문항 86개는 응답 자체가 없다(581 문항만)", "토큰 수는 ollama 의 prompt_eval_count · eval_count 로만 있다"],
    "Text search, 3 runs / Text search, text only, 3 runs | Opus 5.5": [
        "문항별 시간", "세션의 토큰 사용량", "도구 쪽 사용 기록(호출별 시간 · 결과 수)",
        "추적 기록 · cmdlog 는 세션이 남긴 명령 목록이며 시간이 없다", "text only 실행 A 는 cmdlog 가 일부 세션에만 있다"],
    "Raw-text search, 2 runs | Opus 5.5": [
        "문항별 시간", "세션의 토큰 사용량", "도구 쪽 사용 기록의 호출을 문항에 붙일 열쇠(세션 단위까지만)"],
    "Dense tool, 2 runs / Dense tool, 61 chunks per call | Opus 5.5": [
        "문항별 시간", "세션의 토큰 사용량", "도구 쪽 사용 기록의 호출을 문항에 붙일 열쇠(세션 표지까지만)"],
    "Text-to-SQL, 10 runs / Text-to-Cypher, 10 runs | Opus 5.5": [
        "질의를 쓰는 데 든 문항별 시간(seconds 는 실행 시간이다)", "세션의 토큰 사용량",
        "도구 호출 수는 접근 감사가 다룬 에이전트에만 있다(accessAuditToolCalls.agentsByCondition)"],
    "Text-to-SQL · Text-to-Cypher, schema / value domains or exploration | gpt-6.1-sol (Codex)": [
        "문항별 토큰 · 작성 시간(한 실행이 한 WG 묶음 전체다)", "금액",
        "스키마 조건은 wallSeconds 필드가 없고 호출 기록의 시작 · 끝 시각만 있다"],
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, default=Path(DEFAULT_OUT), help="결과 JSON 경로(저장소 루트 기준)")
    parser.add_argument("--transcript-root", type=Path, default=None,
                        help="하위 에이전트 대화 기록이 있는 프로젝트 폴더(저장소 밖). 주면 파일이 있는지와 usage 줄 수만 센다")
    parser.add_argument("--skip-survey", action="store_true", help="결과 폴더 전체에서 토큰 · 벽시계 필드를 찾는 훑기를 건너뛴다")
    args = parser.parse_args()

    items = {item["id"]: item for path in ITEM_FILES for item in jsonl(ROOT / path)}
    qsha = {identifier: sha(item["question"]) for identifier, item in items.items()}
    result = {
        "description": "tab:results 의 조건마다 저장된 비용 측정의 목록과 원 기록 요약. 새로 잰 값은 없다.",
        "method": {"p95": "가장 가까운 순위: 정렬한 값의 ceil(0.95·n) 번째", "median": "statistics.median",
                   "items": {"total": len(items), "files": list(ITEM_FILES)}},
        "queryWriters": query_writers(items, qsha),
        "codex": codex_block(),
        "searchAgents": search_agents(items),
        "localReaders": local_readers(items, qsha),
        "claudeSessions": claude_sessions(args.transcript_root),
        "corpusScale": corpus_scale(),
        "tokenAndWallFieldSurvey": None if args.skip_survey else survey(),
        "readmeLinesMentioningTokenOrWall": readme_lines(),
        "otherStoredRecords": other_records(),
        "notRecorded": NOT_RECORDED,
    }
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    for name, block in result["queryWriters"]["conditions"].items():
        every = block["all"]
        print(f"{name:27} n={every['count']:5} median={every['median']} p95={every['p95']} max={every['max']} "
              f">1s={every['over1s']} cap={every['atOrAbove60sOrTimeoutError']}")
    for name, block in result["codex"]["conditions"].items():
        print(f"codex {name[:30]:30} runs={block['runs']} usage={block['usage']} cmds={block['nCommands']} "
              f"wall={block['wallSecondsSum']}"[:250])
    for name, block in result["searchAgents"]["conditions"].items():
        for run, entry in block["runs"].items():
            per_item = entry["perItemNonHelpCommands"]
            print(f"search {name:22} {run} items={per_item['items']} total={per_item['total']} "
                  f"median={per_item['median']} max={per_item['max']}")
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
