"""한도에 걸린 SQL 질의를 인터프리터에 딸린 SQLite 라이브러리로 다시 실행해 걸린 시간과 정답 일치를 적는다.

대상은 저장된 응답 파일에서 마지막 시도가 `interrupted` 로 끝난 레코드다. 질의 문자열은 응답에 적힌 그대로 쓰고,
읽기 전용 연결에서 실행기(run_chain_eval.py)와 같은 진행 처리기 방식으로 한도를 건다. 모델 호출은 없다.
표준 라이브러리만 쓰므로 두 인터프리터에서 같은 파일을 그대로 실행한다.

사용: taskset -c 12-15 <python> -B <이 파일> --responses <jsonl> --wg RAN1 --cap 90 --out <json>
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--responses", type=Path, required=True)
    parser.add_argument("--wg", required=True)
    parser.add_argument("--cap", type=float, default=90.0)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    gold = {}
    for name in ("core", "ran5"):
        with (LOGS / f"integration/items_final/gate/{name}/chain_items_admitted.jsonl").open() as handle:
            for line in handle:
                item = json.loads(line)
                gold[item["id"]] = item

    targets = []
    with args.responses.open() as handle:
        for line in handle:
            record = json.loads(line)
            last = record["attempts"][-1]
            if last.get("error") == "interrupted":
                targets.append((record["id"], record["family"], last["sql"]))

    database = LOGS / f"integration/sqlite_final/{args.wg}.sqlite"
    db = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    results = []
    for identifier, family, sql in targets:
        deadline = time.time() + args.cap
        db.set_progress_handler(lambda: 1 if time.time() > deadline else 0, 100000)
        started = time.perf_counter()
        error = None
        rows = None
        try:
            rows = db.execute(sql).fetchall()
        except Exception as problem:
            error = str(problem)[:200]
        finally:
            db.set_progress_handler(None, 0)
        seconds = time.perf_counter() - started
        shown = None if rows is None else [[None if cell is None else str(cell) for cell in row] for row in rows]
        results.append({"id": identifier, "family": family, "seconds": round(seconds, 2), "error": error,
                        "rowCount": None if rows is None else len(rows),
                        "exact": None if rows is None else score(gold[identifier]["gold"], shown)["exact"]})
        print(json.dumps(results[-1]), flush=True)
    db.close()

    record = {"scope": "stored SQL responses whose last attempt was interrupted, re-executed unchanged and read-only",
              "responses": str(args.responses), "database": str(database.relative_to(ROOT)),
              "capSeconds": args.cap, "interpreter": sys.executable, "python": platform.python_version(),
              "sqliteLibrary": sqlite3.sqlite_version, "cpuAffinity": sorted(os.sched_getaffinity(0)),
              "loadAverage": list(os.getloadavg()), "results": results}
    args.out.write_text(json.dumps(record, indent=1) + "\n")


if __name__ == "__main__":
    main()
