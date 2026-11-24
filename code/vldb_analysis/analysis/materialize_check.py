"""새 SQLite 에서만 시간 상한에 걸린 저장 SQL 을, 옛 라이브러리가 구체화(MATERIALIZE)했던 CTE 에 MATERIALIZED 를 붙여 다시 돌린다.

같은 질의 · 같은 데이터 · 같은 60초 상한에서 CTE 구체화 결정 하나만 옛 계획대로 고정했을 때
시간 초과가 풀리는지 본다. 읽기 전용이며 저장된 응답은 바꾸지 않는다.

사용: <python> -B <이 파일> --wg <WG> --out <json>   (저장소 루트에서 실행)
입력: replay/{WG}_new.json · replay/{WG}_old.json · plans/plans_new.json · plans/plans_old.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import re
import sqlite3
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("replay_stored_sql", HERE / "replay_stored_sql.py")
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


def timed_out(entry: dict) -> bool:
    return bool(entry.get("replayed") and entry.get("error") and "interrupt" in entry["error"])


def flipped(old_plan: list[str], new_plan: list[str]) -> list[str]:
    materialized = {m.group(1) for line in old_plan for m in [re.match(r"MATERIALIZE (\S+)", line)] if m}
    coroutine = {m.group(1) for line in new_plan for m in [re.match(r"CO-ROUTINE (\S+)", line)] if m}
    return sorted(materialized & coroutine)


def force_materialized(sql: str, names: list[str]) -> tuple[str, list[str]]:
    applied = []
    for name in names:
        pattern = re.compile(r"(?<![\w\"])(\"?" + re.escape(name) + r"\"?\s*(?:\([^()]*\))?\s+AS)\s*\(", re.IGNORECASE)
        rewritten, count = pattern.subn(r"\1 MATERIALIZED (", sql, count=1)
        if count:
            sql = rewritten
            applied.append(name)
    return sql, applied


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wg", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    new = {f"{r['condition']}|{r['id']}": r for r in json.loads((HERE / f"replay/{args.wg}_new.json").read_text())["results"]}
    old = {f"{r['condition']}|{r['id']}": r for r in json.loads((HERE / f"replay/{args.wg}_old.json").read_text())["results"]}
    plans_new = json.loads((HERE / "plans/plans_new.json").read_text())["plans"]
    plans_old = json.loads((HERE / "plans/plans_old.json").read_text())["plans"]

    gold = {}
    for name in ("core", "ran5"):
        with (replay.LOGS / f"integration/items_final/gate/{name}/chain_items_admitted.jsonl").open() as handle:
            for line in handle:
                item = json.loads(line)
                gold[item["id"]] = item

    sql_of = {}
    for condition, path in replay.response_files(args.wg):
        with path.open() as handle:
            for line in handle:
                record = json.loads(line)
                last = record["attempts"][-1] if record.get("attempts") else {}
                sql_of[f"{condition}|{record['id']}"] = last.get("sql")

    database = replay.LOGS / f"integration/sqlite_final/{args.wg}.sqlite"
    db = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    started_load = list(os.getloadavg())
    results = []
    for key, entry in new.items():
        if not timed_out(entry):
            continue
        plan_key = f"{args.wg}|{key}"
        names = flipped(plans_old[plan_key], plans_new[plan_key])
        sql, applied = force_materialized(sql_of[key], names)
        result = {"key": plan_key, "family": entry["family"], "timedOutOld": timed_out(old[key]),
                  "oldSeconds": old[key].get("seconds"), "flippedCtes": names, "appliedCtes": applied}
        if not applied:
            result["rerun"] = False
            results.append(result)
            continue
        plan = [row[3] for row in db.execute("EXPLAIN QUERY PLAN " + sql).fetchall()]
        deadline = time.time() + replay.CAP_SECONDS
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
        result.update({"rerun": True, "planMaterializes": sorted(n for n in applied if f"MATERIALIZE {n}" in plan),
                       "seconds": round(seconds, 3), "error": error,
                       "rowCount": None if rows is None else len(rows),
                       "exact": None if shown is None else replay.score(gold[entry["id"]]["gold"], shown)["exact"],
                       "exactOld": old[key].get("exact")})
        results.append(result)
        print(plan_key, result.get("seconds"), result.get("error"), flush=True)
    db.close()
    record = {"scope": "stored SQL that hit the cap only under the newer SQLite, rerun with MATERIALIZED on the CTEs the older library materialized",
              "wg": args.wg, "capSeconds": replay.CAP_SECONDS, "interpreter": sys.executable,
              "python": platform.python_version(), "sqliteLibrary": sqlite3.sqlite_version,
              "cpuAffinity": sorted(os.sched_getaffinity(0)), "loadAverageAtStart": started_load,
              "loadAverageAtEnd": list(os.getloadavg()), "records": len(results), "results": results}
    args.out.write_text(json.dumps(record) + "\n")
    print(f"{args.wg} done: {len(results)} records", flush=True)


if __name__ == "__main__":
    main()
