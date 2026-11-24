#!/usr/bin/env python3
"""헤드룸 분할의 Codex 세션 20개가 실제로 어떻게 돌았는지를 세션 기록에서 다시 재어 적는다.

적는 것은 점수에 들어가지 않는 실행 사실이다: 세션 시간 창이 서로 겹친 정도, stderr 에 남은 줄의 종류,
이벤트 기록의 항목 종류(MCP 도구 호출 유무), 탐색 Cypher 세션의 읽기 전용 프록시 응답 수,
그리고 분석 스크립트의 해시와 수정 시각.

점수를 본 뒤에 더한 기록이다. 세션 기록 · 문항 · 분석 계획 · 구현 기록은 읽기만 한다.

사용:
    PYTHONPATH=scripts/common:scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark \
        python3 -B scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/record_headroom_codex_run_facts.py [--out 경로]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True

PROJECT_ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
os.chdir(PROJECT_ROOT)
L = Path("logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark")
H = L / "final/next_cycle/headroom"
RUNS = H / "codex/run_records"
ANALYSIS_SCRIPT = Path("scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/analyze_headroom.py")

# stderr 줄의 종류. 두 문구는 Codex CLI 가 쓰는 줄에서 그대로 가져왔다.
STDIN_NOTICE = "Reading additional input from stdin..."
CONNECTOR_AUTH = "AuthRequired"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def session_windows(rows: list[dict]) -> dict:
    """세션 시간 창이 겹친 정도. 같은 질의 언어끼리는 차례로 돌았는지도 본다."""
    spans = sorted((datetime.fromisoformat(r["startedAt"]), datetime.fromisoformat(r["endedAt"]), r["name"], r["language"])
                   for r in rows)
    events = sorted([(s, 1) for s, _, _, _ in spans] + [(e, -1) for _, e, _, _ in spans], key=lambda x: (x[0], x[1]))
    open_now = peak = 0
    for _, step in events:
        open_now += step
        peak = max(peak, open_now)
    pairs = [(a, b) for i, a in enumerate(spans) for b in spans[i + 1:] if b[0] < a[1]]
    first, last = spans[0][0], max(e for _, e, _, _ in spans)
    return {
        "sessions": len(spans),
        "firstStart": first.isoformat(), "lastEnd": last.isoformat(),
        "elapsedSeconds": int((last - first).total_seconds()),
        "wallSecondsSummed": sum(r["wallSeconds"] for r in rows),
        "mostSessionsOpenAtOnce": peak,
        "overlappingPairs": len(pairs),
        "overlappingPairsWithinOneLanguage": sum(1 for a, b in pairs if a[3] == b[3]),
        "languagesOfSessions": dict(Counter(r["language"] for r in rows)),
    }


def stderr_lines(names: list[str]) -> dict:
    kinds: Counter = Counter()
    per_session = {}
    for name in names:
        lines = [l for l in (RUNS / name / "stderr.txt").read_text(errors="replace").splitlines() if l.strip()]
        here = Counter("stdinNotice" if l.strip() == STDIN_NOTICE else
                       "connectorAuthenticationRequired" if CONNECTOR_AUTH in l else "other" for l in lines)
        kinds.update(here)
        per_session[name] = dict(here)
    return {"lineKindsAllSessions": dict(kinds), "perSession": per_session}


def event_items(names: list[str]) -> dict:
    kinds: Counter = Counter()
    unparsed = 0
    for name in names:
        for line in (RUNS / name / "events.jsonl").read_text(errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                unparsed += 1
                continue
            if event.get("type") == "item.completed":
                kinds[(event.get("item") or {}).get("type", "<no type>")] += 1
    return {"completedItemKindsAllSessions": dict(kinds), "mcpToolCalls": kinds.get("mcp_tool_call", 0),
            "unparsedLines": unparsed}


def proxy_logs(names: list[str]) -> dict:
    out = {}
    for name in names:
        log = RUNS / name / "proxy_log.jsonl"
        if not log.exists():
            continue
        rows = [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
        out[name] = {"requests": len(rows), "status": dict(Counter(r["status"] for r in rows)),
                     "proxyStderrBytes": (RUNS / name / "proxy.stderr").stat().st_size}
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, default=H / "codex/run_facts.json")
    args = parser.parse_args()

    runs_file = RUNS / "runs.jsonl"
    rows = [json.loads(l) for l in runs_file.read_text().splitlines() if l.strip()]
    names = [r["name"] for r in rows]
    if sorted(names) != sorted(p.name for p in RUNS.iterdir() if p.is_dir()):
        sys.exit("run records and session folders name different sessions")
    windows = session_windows(rows)
    modified = datetime.fromtimestamp(ANALYSIS_SCRIPT.stat().st_mtime, timezone.utc)
    record = {
        "purpose": "Run facts of the twenty Codex sessions on the headroom split that the scores do not carry: "
                   "how the session windows overlapped, what the sessions wrote to stderr, which item kinds the "
                   "event logs hold, how the read-only Cypher proxy answered, and which analysis script scored them.",
        "status": "added after the scores were seen; reads the session records only",
        "recordedAtUtc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runRecords": {"file": str(runs_file), "sha256": sha256(runs_file),
                       "exitCodes": dict(Counter(str(r["exit"]) for r in rows)),
                       "sessionsWithSandboxNetworkAccess": sorted(r["name"] for r in rows if r["networkAccess"]),
                       "sessionsWithoutIt": sum(1 for r in rows if not r["networkAccess"])},
        "sessionWindows": windows,
        "stderr": stderr_lines(names),
        "eventLogs": event_items(names),
        "cypherProxy": proxy_logs(names),
        "analysisScript": {
            "file": str(ANALYSIS_SCRIPT), "sha256": sha256(ANALYSIS_SCRIPT),
            "lastModifiedUtc": modified.isoformat(timespec="seconds"),
            "modifiedBeforeLastSessionEnded": modified < datetime.fromisoformat(windows["lastEnd"]),
            "note": "The modification time is file-system evidence only; the hash is the one of the script as it "
                    "stands when this record is written.",
        },
        "thisScriptSha256": sha256(Path(__file__).resolve().relative_to(PROJECT_ROOT)),
    }
    args.out.write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: record[k] for k in ("runRecords", "sessionWindows", "eventLogs", "cypherProxy")}, ensure_ascii=False))
    print(json.dumps(record["stderr"]["lineKindsAllSessions"]), json.dumps(record["analysisScript"], ensure_ascii=False))
    print("wrote", args.out)


if __name__ == "__main__":
    main()
