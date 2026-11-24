"""관계형 질의 풀이에서 실행 상한(60초)에 걸린 질의를 더 긴 상한으로 다시 실행한다 (모델 호출 없음).

`diagnose_text2sql_misses.py` 의 `--rerun-seconds` 와 같은 판정이다. 저장된 응답 가운데 마지막 시도의 오류가
`interrupted` 인 문항만 골라, 같은 SQL 을 관계형 내보내기에 읽기 전용으로 다시 실행하고, 걸린 초와 정답 일치
여부를 적는다. 문항마다 독립이므로 프로세스 여러 개로 나눠 돌린다(질의 하나는 프로세스 하나에서 돈다).

사용: python3 rerun_text2sql_deadline_misses.py --items <jsonl> [<jsonl> ...] --responses <jsonl> [<jsonl> ...] \
          --sqlite-dir <dir> [--seconds 600] [--workers 8] --out <json>
저장소 루트에서 `PYTHONPATH=scripts/common:scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark` 로 실행한다.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from diagnose_text2sql_misses import executed_query, parsed, run, run_label
from score_chain_eval import score


def rerun_one(task: tuple[str, str, str, list, float]) -> dict:
    item_id, db_path, sql, gold, seconds = task
    db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows, error, took = run(db, sql, seconds)
    finally:
        db.close()
    return {"id": item_id, "limitSeconds": seconds, "seconds": took, "error": error,
            "exact": bool(rows is not None and score(gold, rows)["exact"])}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, nargs="+", required=True)
    parser.add_argument("--responses", type=Path, nargs="+", required=True)
    parser.add_argument("--sqlite-dir", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=600)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    items = {item["id"]: item for path in args.items for item in map(json.loads, path.read_text().splitlines())}

    tasks, labels = [], {}
    for path in args.responses:
        for response in map(json.loads, path.read_text().splitlines()):
            item = items.get(response["id"])
            if item is None:
                continue
            sql, error = executed_query(response)
            if error != "interrupted":
                continue
            labels[item["id"]] = {"wg": response["wg"], "run": run_label(response), "family": item["family"]}
            tasks.append((item["id"], str(args.sqlite_dir / f"{response['wg']}.sqlite"), sql,
                          parsed(item["gold"]), args.seconds))

    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        results = [{**labels[result["id"]], **result} for result in pool.map(rerun_one, tasks)]
    report = {
        "scope": "text2sql responses whose last attempt was interrupted at the solving-time cap, re-executed "
                 "unchanged and read-only with a longer cap",
        "responses": [str(path) for path in args.responses],
        "limitSeconds": args.seconds,
        "rerun": len(results),
        "exact": sum(result["exact"] for result in results),
        "finishedWithinLimit": sum(result["error"] is None for result in results),
        "maxSecondsFinished": max((result["seconds"] for result in results if result["error"] is None), default=None),
        "items": sorted(results, key=lambda result: (result["run"], result["wg"], result["id"])),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "items"}, indent=1))


if __name__ == "__main__":
    main()
