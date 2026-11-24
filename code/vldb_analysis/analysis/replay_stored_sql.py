"""저장된 SQL 응답을 인터프리터에 딸린 SQLite 라이브러리로 다시 실행해 한도·행·정답 일치를 적는다 (읽기 전용, 모델 호출 없음).

대상은 한 작업 그룹의 Text-to-SQL 응답 파일(Opus 열 회차, Codex 세 조건)이다. 레코드마다 마지막 시도의 SQL 을
적힌 그대로 읽기 전용 연결에서 한 번 실행하고, 실행기(run_chain_eval.py)와 같은 진행 처리기로 60초 한도를 건다.
결과로 걸린 시간, 오류, 행 수, 저장된 행과 같은지, gold 와 정확히 같은지를 남긴다.
표준 라이브러리만 쓰므로 두 인터프리터에서 같은 파일을 그대로 실행한다.

사용: taskset -c <코어> <python> -B <이 파일> --wg RAN1 --out <json>
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import platform
import sqlite3
import sys
import time
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
TRACK = "publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
LOGS = ROOT / "logs" / TRACK
sys.path.insert(0, str(ROOT / "scripts" / TRACK))
score = importlib.import_module("score_chain_eval").score
CAP_SECONDS = 60


def response_files(wg: str) -> list[tuple[str, Path]]:
    files = [(f"opus_run{run}", LOGS / f"chain_eval/text2sql/{wg}_text2sql_run{run}.jsonl") for run in "ABCDEFGHIJ"]
    files.append(("codex_schema", LOGS / f"chain_eval/codex/chain_sql_{wg}_codex.jsonl"))
    files.append(("codex_value_domains", LOGS / f"chain_eval/codex_v2/responses/{wg}_sql_dom_codex.jsonl"))
    files.append(("codex_exploration", LOGS / f"chain_eval/codex_v2/responses/{wg}_sql_exp_codex.jsonl"))
    return files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wg", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    gold = {}
    for name in ("core", "ran5"):
        with (LOGS / f"integration/items_final/gate/{name}/chain_items_admitted.jsonl").open() as handle:
            for line in handle:
                item = json.loads(line)
                gold[item["id"]] = item

    database = LOGS / f"integration/sqlite_final/{args.wg}.sqlite"
    db = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    started_load = list(os.getloadavg())
    results = []
    for condition, path in response_files(args.wg):
        count = 0
        with path.open() as handle:
            for line in handle:
                record = json.loads(line)
                count += 1
                last = record["attempts"][-1] if record.get("attempts") else {}
                stored_rows = record.get("rows")
                entry = {"condition": condition, "id": record["id"], "family": record["family"],
                         "attempts": len(record.get("attempts") or []),
                         "storedError": last.get("error"), "storedSeconds": record.get("seconds"),
                         "storedRowCount": None if stored_rows is None else len(stored_rows),
                         "storedExact": None if stored_rows is None else score(gold[record["id"]]["gold"], stored_rows)["exact"]}
                sql = last.get("sql")
                if sql is None:
                    entry["replayed"] = False
                    results.append(entry)
                    continue
                deadline = time.time() + CAP_SECONDS
                db.set_progress_handler(lambda: 1 if time.time() > deadline else 0, 100000)
                begun = time.perf_counter()
                error = None
                rows = None
                try:
                    rows = db.execute(sql).fetchall()
                except Exception as problem:
                    error = str(problem)[:200]
                finally:
                    db.set_progress_handler(None, 0)
                seconds = time.perf_counter() - begun
                shown = None if rows is None else [[None if cell is None else str(cell) for cell in row] for row in rows[:2000]]
                entry.update({"replayed": True, "seconds": round(seconds, 3), "error": error,
                              "rowCount": None if rows is None else len(rows),
                              "rowsEqualStored": None if shown is None or stored_rows is None else shown == stored_rows,
                              "rowSetEqualStored": None if shown is None or stored_rows is None else
                              sorted(map(repr, shown)) == sorted(map(repr, stored_rows)),
                              "exact": None if shown is None else score(gold[record["id"]]["gold"], shown)["exact"]})
                results.append(entry)
        print(f"{args.wg} {condition}: {count} records", flush=True)
    db.close()

    record = {"scope": "stored Text-to-SQL responses of one working group, last attempt re-executed unchanged and read-only",
              "wg": args.wg, "database": str(database.relative_to(ROOT)), "capSeconds": CAP_SECONDS,
              "interpreter": sys.executable, "python": platform.python_version(),
              "sqliteLibrary": sqlite3.sqlite_version, "cpuAffinity": sorted(os.sched_getaffinity(0)),
              "loadAverageAtStart": started_load, "loadAverageAtEnd": list(os.getloadavg()),
              "records": len(results), "results": results}
    args.out.write_text(json.dumps(record) + "\n")
    print(f"{args.wg} done: {len(results)} records", flush=True)


if __name__ == "__main__":
    main()
