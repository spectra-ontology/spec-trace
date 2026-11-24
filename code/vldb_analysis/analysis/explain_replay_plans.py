"""저장된 SQL 응답의 실행 계획(EXPLAIN QUERY PLAN)을 인터프리터에 딸린 SQLite 라이브러리로 적는다 (읽기 전용, 질의 실행 없음).

replay_stored_sql.py 와 같은 응답 파일 · 같은 마지막 시도 SQL 을 읽고, 레코드마다 계획 줄 목록을 남긴다.
두 인터프리터로 돌려 같은 SQL 의 계획이 라이브러리 판에 따라 달라지는지 견준다.

사용: <python> -B <이 파일> --out <json>   (저장소 루트에서 실행, 다섯 작업 그룹 전부)
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("replay_stored_sql", HERE / "replay_stored_sql.py")
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    plans = {}
    for wg in ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5"):
        database = replay.LOGS / f"integration/sqlite_final/{wg}.sqlite"
        db = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
        for condition, path in replay.response_files(wg):
            with path.open() as handle:
                for line in handle:
                    record = json.loads(line)
                    last = record["attempts"][-1] if record.get("attempts") else {}
                    sql = last.get("sql")
                    if sql is None:
                        continue
                    try:
                        plan = [row[3] for row in db.execute("EXPLAIN QUERY PLAN " + sql).fetchall()]
                    except Exception as problem:
                        plan = ["ERROR " + str(problem)[:200]]
                    plans[f"{wg}|{condition}|{record['id']}"] = plan
        db.close()
    args.out.write_text(json.dumps({"python": platform.python_version(), "sqliteLibrary": sqlite3.sqlite_version,
                                    "interpreter": sys.executable, "plans": plans}) + "\n")
    print("plans", len(plans), sqlite3.sqlite_version)


if __name__ == "__main__":
    main()
