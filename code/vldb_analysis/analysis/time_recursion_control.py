"""revision_chain 참조 SQL 의 느린 계획이 재귀 공통 표 식 때문인지 가르는 대조 측정 (읽기 전용, 모델 호출 없음).

내보낸 SQLite 파일(통계 표 없음)에서 바깥 조인 다섯 개는 그대로 두고 입력 `later` 만 바꾼 세 조건을 잰다.
  recursive   참조 SQL 그대로: later 는 재귀 공통 표 식.
  oneStep     later 를 재귀 없는 한 단계 공통 표 식(SELECT later FROM revision WHERE earlier = :anchor)으로 바꾼다.
              행 집합은 개정 사슬이 한 단계인 문항에서만 gold 와 같으므로, 계획과 시간의 대조로만 쓴다.
  tableInput  재귀 결과를 문항마다 임시 표 later_input(id) 에 미리 담고(통계 없음), 바깥 조인만 잰다.
              행 집합은 gold 와 같아야 한다. 임시 표를 채우는 시간은 재지 않는다.
조건마다 워밍업 1회 뒤 3회를 재고 문항별 중앙값을 쓴다. 작업반마다 첫 문항의 EXPLAIN QUERY PLAN 을 적고,
가장 바깥 루프가 disposition 전체 훑기인지 센다. 표준 라이브러리만 쓰므로 인터프리터에 딸린 SQLite 판본을
바꿔 같은 파일을 실행할 수 있다.

사용: taskset -c 12-15 <python> -B <이 파일> --out <json>
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sqlite3
import statistics
import sys
import time
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
TRACK = "publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
LOGS = ROOT / "logs" / TRACK
sys.path.insert(0, str(ROOT / "scripts" / TRACK))
from measure_relational_equivalence import SQL, VARIANTS  # noqa: E402

ITEM_FILES = [LOGS / "integration/items_final/gate/core/chain_items_admitted.jsonl",
              LOGS / "integration/items_final/gate/ran5/chain_items_admitted.jsonl"]
SQLITE_DIR = LOGS / "integration/sqlite_final"
TIMED_PASSES = 3


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def plan(db, sql: str, anchor: str) -> list[str]:
    rows = db.execute("EXPLAIN QUERY PLAN " + sql, {"anchor": anchor}).fetchall()
    depth = {0: -1}
    lines = []
    for identifier, parent, _, detail in rows:
        depth[identifier] = depth.get(parent, -1) + 1
        lines.append("  " * depth[identifier] + detail)
    return lines


def outermost_scans_disposition(lines: list[str]) -> bool:
    top = [line.strip() for line in lines if not line.startswith(" ")]
    loops = [line for line in top if line.startswith(("SCAN", "SEARCH"))]
    return bool(loops) and loops[0].split()[:2] == ["SCAN", "d"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    items = []
    for path in ITEM_FILES:
        with path.open() as lines:
            items.extend(json.loads(line) for line in lines)
    chain_items = [item for item in items if item["family"] == "revision_chain"]
    recursive = SQL["revision_chain"].format(**VARIANTS["cr_side"])
    head, marker, tail = recursive.partition("SELECT DISTINCT doc.number")
    assert marker and head.count("WITH RECURSIVE later(id) AS (") == 1
    one_step = ("WITH later(id) AS (SELECT later FROM revision WHERE earlier = :anchor)\n        "
                + marker + tail)
    table_input = (marker + tail).replace("FROM later\n        JOIN document doc ON doc.id = later.id",
                                          "FROM later_input later\n        JOIN document doc ON doc.id = later.id")
    assert "later_input later" in table_input
    chain_only = head.strip() + "\n        SELECT id FROM later"

    connections = {}
    for wg in sorted({item["wg"] for item in chain_items}):
        db = sqlite3.connect(f"file:{SQLITE_DIR / (wg + '.sqlite')}?mode=ro", uri=True)
        assert db.execute("SELECT count(*) FROM sqlite_master WHERE name = 'sqlite_stat1'").fetchone()[0] == 0
        db.execute("CREATE TEMP TABLE later_input(id TEXT)")
        connections[wg] = db

    def load_input(item) -> None:
        db = connections[item["wg"]]
        db.execute("DELETE FROM temp.later_input")
        db.executemany("INSERT INTO temp.later_input(id) VALUES (?)",
                       db.execute(chain_only, {"anchor": item["anchor"]}).fetchall())

    def one_pass(sql: str, prepare: bool) -> list[dict]:
        results = []
        for item in chain_items:
            db = connections[item["wg"]]
            if prepare:
                load_input(item)
            started = time.perf_counter()
            rows = db.execute(sql, {"anchor": item["anchor"]}).fetchall()
            elapsed = time.perf_counter() - started
            results.append({"ms": elapsed * 1000,
                            "same": {tuple(r) for r in rows} == {tuple(r) for r in item["gold"]}})
        return results

    started_load = list(os.getloadavg())
    conditions = {}
    for name, sql, prepare in (("recursive", recursive, False), ("oneStep", one_step, False),
                               ("tableInput", table_input, True)):
        one_pass(sql, prepare)
        passes = [one_pass(sql, prepare) for _ in range(TIMED_PASSES)]
        medians = [statistics.median(p[i]["ms"] for p in passes) for i in range(len(chain_items))]
        conditions[name] = {"items": len(chain_items),
                            "medianMs": round(percentile(medians, 0.5), 4),
                            "p95Ms": round(percentile(medians, 0.95), 4),
                            "itemsWithGoldRowsInEveryPass": sum(all(p[i]["same"] for p in passes)
                                                               for i in range(len(chain_items)))}
        print(name, conditions[name], flush=True)

    first = {}
    for item in chain_items:
        first.setdefault(item["wg"], item)
    plans = {}
    for wg, item in sorted(first.items()):
        load_input(item)
        db = connections[wg]
        plans[wg] = {"item": item["id"],
                     "recursive": plan(db, recursive, item["anchor"]),
                     "oneStep": plan(db, one_step, item["anchor"]),
                     "tableInput": plan(db, table_input, item["anchor"])}
    outer_scan = {name: sum(outermost_scans_disposition(plans[wg][name]) for wg in plans)
                  for name in ("recursive", "oneStep", "tableInput")}
    for db in connections.values():
        db.close()

    record = {"scope": "revision_chain reference SQL on the exported files without statistics, with the "
                       "input `later` given as the recursive CTE, a one-step non-recursive CTE, or a temporary "
                       "table holding the recursive result; outer joins unchanged; read-only on the files",
              "design": {"warmupPasses": 1, "timedPasses": TIMED_PASSES,
                         "perQueryTime": "median of the timed passes; tableInput times the outer query only",
                         "percentile": "linear interpolation between order statistics, position (n - 1) * q"},
              "context": {"interpreter": sys.executable, "python": platform.python_version(),
                          "sqliteLibrary": sqlite3.sqlite_version, "cpuAffinity": sorted(os.sched_getaffinity(0)),
                          "loadAverageAtStart": started_load, "loadAverageAtEnd": list(os.getloadavg())},
              "queries": {"recursive": " ".join(recursive.split()), "oneStep": " ".join(one_step.split()),
                          "tableInput": " ".join(table_input.split()), "chainOnly": " ".join(chain_only.split())},
              "conditions": conditions,
              "workingGroupsWithDispositionScanOutermost": outer_scan,
              "plans": plans}
    args.out.write_text(json.dumps(record, indent=1) + "\n")
    print(json.dumps({"out": str(args.out), "outerScan": outer_scan}))


if __name__ == "__main__":
    main()
