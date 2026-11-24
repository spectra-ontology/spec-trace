"""저장 기록에서 비용 · 규모 수치를 직접 다시 센다 (읽기 전용, 모델 호출 없음).

  queryExecution  Opus 질의 작성 응답의 seconds 칸(실행기가 적힌 질의를 실행한 시간)을 언어별로 요약한다.
  codexTokens     Codex 실행 기록 events.jsonl 의 usage 를 조건별로 더한다 (줄 단위로 읽는다).
  relationalRows  내보낸 SQLite 다섯 파일의 표별 행 수.

사용: python3 -B <이 파일> --out <json>
"""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import statistics
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
LOGS = ROOT / "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
GROUPS = ["RAN1", "RAN2", "RAN3", "RAN4", "RAN5"]


def nearest_rank(values: list[float], q: float) -> float:
    ordered = sorted(values)
    return ordered[math.ceil(q * len(ordered)) - 1]


def query_execution() -> dict:
    patterns = {"sql": "chain_eval/text2sql/{wg}_text2sql_run{run}.jsonl",
                "cypher": "chain_eval/{wg}_text2cypher_claude_subagent_run{run}.jsonl"}
    out = {}
    for language, pattern in patterns.items():
        seconds = []
        errors: dict[str, int] = {}
        by_family: dict[str, list[float]] = {}
        for wg in GROUPS:
            for run in "ABCDEFGHIJ":
                with (LOGS / pattern.format(wg=wg, run=run)).open() as handle:
                    for line in handle:
                        record = json.loads(line)
                        seconds.append(record["seconds"])
                        by_family.setdefault(record["family"], []).append(record["seconds"])
                        last = record["attempts"][-1] if record.get("attempts") else {}
                        if "error" in last:
                            key = last["error"][:40]
                            errors[key] = errors.get(key, 0) + 1
        out[language] = {"records": len(seconds), "sumSeconds": round(sum(seconds), 1),
                         "median": statistics.median(seconds), "p95": nearest_rank(seconds, 0.95),
                         "max": max(seconds), "aboveOneSecond": sum(1 for s in seconds if s > 1.0),
                         "aboveOneSecondByFamily": {f: sum(1 for s in v if s > 1.0) for f, v in sorted(by_family.items())},
                         "lastAttemptErrors": dict(sorted(errors.items(), key=lambda kv: -kv[1])[:6])}
    return out


def codex_tokens() -> dict:
    out = {}
    folders = {"schema": LOGS / "chain_eval/codex/run_records", "v2": LOGS / "chain_eval/codex_v2/run_records"}
    for label, folder in folders.items():
        for events in sorted(folder.glob("*/events.jsonl")):
            usage_events = []
            commands = 0
            with events.open() as handle:
                for line in handle:
                    if '"usage"' not in line and '"command_execution"' not in line:
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(event.get("usage"), dict):
                        usage_events.append(event["usage"])
                    item = event.get("item") or {}
                    if event.get("type") == "item.completed" and item.get("type") == "command_execution":
                        commands += 1
            total: dict[str, int] = {}
            for usage in usage_events:
                for key, value in usage.items():
                    if isinstance(value, int):
                        total[key] = total.get(key, 0) + value
            out[f"{label}/{events.parent.name}"] = {"usageEvents": len(usage_events), "usage": total, "commands": commands}
    return out


def relational_rows() -> dict:
    out = {}
    for wg in GROUPS:
        db = sqlite3.connect(f"file:{LOGS / 'integration/sqlite_final' / (wg + '.sqlite')}?mode=ro", uri=True)
        tables = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")]
        out[wg] = {name: db.execute(f"SELECT count(*) FROM {name}").fetchone()[0] for name in tables}
        db.close()
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    record = {"queryExecution": query_execution(), "codexTokens": codex_tokens(), "relationalRows": relational_rows()}
    args.out.write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(record["queryExecution"], ensure_ascii=False)[:1500])
    groups: dict[str, dict] = {}
    for name, entry in record["codexTokens"].items():
        label, run = name.split("/")
        parts = run.split("_")
        key = f"{label}:{'_'.join(parts[:-1])}"
        slot = groups.setdefault(key, {"runs": 0, "commands": 0, "usageEvents": 0})
        slot["runs"] += 1
        slot["commands"] += entry["commands"]
        slot["usageEvents"] += entry["usageEvents"]
        for k, v in entry["usage"].items():
            slot[k] = slot.get(k, 0) + v
    for key, slot in sorted(groups.items()):
        print(key, slot)
    totals: dict[str, int] = {}
    for wg, tables in record["relationalRows"].items():
        for name, count in tables.items():
            totals[name] = totals.get(name, 0) + count
    print(totals, sum(totals.values()))


if __name__ == "__main__":
    main()
