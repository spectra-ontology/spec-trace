"""참조 SQL 을 통계 유무와 조인 순서 지정에 따라 실행해 시간과 실행 계획을 적는다 (읽기 전용, 모델 호출 없음).

조건은 넷이다.
  stored            내보낸 SQLite 파일 그대로 (통계 표 없음), 참조 SQL 그대로. 일곱 유형 전부.
  analyzed          사본에 ANALYZE 를 실행한 뒤, 참조 SQL 그대로. 일곱 유형 전부.
  orderedJoin       내보낸 파일 그대로, revision_chain 의 최상위 조인을 CROSS JOIN 으로 적어 적힌 순서를 지킨다.
  materializedHint  내보낸 파일 그대로, revision_chain 의 재귀 공통 표 식에 MATERIALIZED 를 붙인다.

원본 파일은 읽기 전용으로만 열고, ANALYZE 는 --work 폴더의 사본에만 실행한다. 조건마다 워밍업 1회 뒤 3회를 재고
문항별 중앙값을 쓴다. 매 실행에서 행 집합을 gold 와 비교한다. 표준 라이브러리만 쓰므로 인터프리터에 딸린
SQLite 판본을 바꿔 가며 같은 파일을 실행할 수 있다.

사용: taskset -c 12-15 <python> -B <이 파일> --work <빈 폴더> --out <json>
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
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


def one_pass(connections: dict, items: list[dict], queries: dict) -> list[dict]:
    results = []
    for item in items:
        db = connections[item["wg"]]
        started = time.perf_counter()
        rows = db.execute(queries[item["family"]], {"anchor": item["anchor"]}).fetchall()
        elapsed = time.perf_counter() - started
        results.append({"ms": elapsed * 1000,
                        "same": {tuple(row) for row in rows} == {tuple(row) for row in item["gold"]}})
    return results


def measure(connections: dict, items: list[dict], queries: dict, label: str) -> dict:
    warm = one_pass(connections, items, queries)
    passes = [one_pass(connections, items, queries) for _ in range(TIMED_PASSES)]
    medians = [statistics.median(p[i]["ms"] for p in passes) for i in range(len(items))]
    mismatches = sum(1 for p in [warm] + passes for r in p if not r["same"])
    by_family: dict[str, list[float]] = {}
    by_family_wg: dict[str, dict[str, list[float]]] = {}
    for item, value in zip(items, medians):
        by_family.setdefault(item["family"], []).append(value)
        by_family_wg.setdefault(item["family"], {}).setdefault(item["wg"], []).append(value)

    def summary(values: list[float]) -> dict:
        return {"items": len(values), "medianMs": round(percentile(values, 0.5), 4),
                "p95Ms": round(percentile(values, 0.95), 4), "maxMs": round(max(values), 4)}

    print(f"{label}: items={len(items)} mismatches={mismatches}", flush=True)
    return {"items": len(items), "mismatchesInAllPasses": mismatches, "all": summary(medians),
            "byFamily": {family: summary(values) for family, values in sorted(by_family.items())},
            "byFamilyAndWg": {family: {wg: summary(values) for wg, values in sorted(groups.items())}
                              for family, groups in sorted(by_family_wg.items())},
            "perItemMedianMs": {item["id"]: round(value, 4) for item, value in zip(items, medians)}}


def plan(db, sql: str, anchor: str) -> list[str]:
    rows = db.execute("EXPLAIN QUERY PLAN " + sql, {"anchor": anchor}).fetchall()
    depth = {0: -1}
    lines = []
    for identifier, parent, _, detail in rows:
        depth[identifier] = depth.get(parent, -1) + 1
        lines.append("  " * depth[identifier] + detail)
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    assert not any(args.work.iterdir()), "--work 는 빈 폴더여야 한다"

    items = []
    for path in ITEM_FILES:
        with path.open() as lines:
            items.extend(json.loads(line) for line in lines)
    groups = sorted({item["wg"] for item in items})
    reference = {family: text.format(**VARIANTS["cr_side"]) for family, text in SQL.items()}
    chain_items = [item for item in items if item["family"] == "revision_chain"]

    head, marker, tail = reference["revision_chain"].partition("SELECT DISTINCT doc.number")
    assert marker and tail.count(" JOIN ") + tail.count("\n        JOIN ") >= 5
    ordered_tail = tail.replace("JOIN ", "CROSS JOIN ")
    assert ordered_tail.count("CROSS JOIN ") == 5, ordered_tail.count("CROSS JOIN ")
    ordered = {"revision_chain": head + marker + ordered_tail}
    assert reference["revision_chain"].count("later(id) AS (") == 1
    hinted = {"revision_chain": reference["revision_chain"].replace("later(id) AS (", "later(id) AS MATERIALIZED (")}

    started_load = list(os.getloadavg())
    stored = {wg: sqlite3.connect(f"file:{SQLITE_DIR / (wg + '.sqlite')}?mode=ro", uri=True) for wg in groups}
    statistics_rows = {}
    analyze_seconds = {}
    analyzed = {}
    for wg in groups:
        assert stored[wg].execute("SELECT count(*) FROM sqlite_master WHERE name = 'sqlite_stat1'").fetchone()[0] == 0
        copy = args.work / f"{wg}.sqlite"
        shutil.copyfile(SQLITE_DIR / f"{wg}.sqlite", copy)
        writable = sqlite3.connect(copy)
        begun = time.perf_counter()
        writable.execute("ANALYZE")
        writable.commit()
        analyze_seconds[wg] = round(time.perf_counter() - begun, 2)
        statistics_rows[wg] = writable.execute("SELECT count(*) FROM sqlite_stat1").fetchone()[0]
        writable.close()
        analyzed[wg] = sqlite3.connect(f"file:{copy}?mode=ro", uri=True)

    conditions = {
        "stored": measure(stored, items, reference, "stored"),
        "analyzed": measure(analyzed, items, reference, "analyzed"),
        "orderedJoin": measure(stored, chain_items, ordered, "orderedJoin"),
        "materializedHint": measure(stored, chain_items, hinted, "materializedHint"),
    }
    first = {}
    for item in chain_items:
        first.setdefault(item["wg"], item)
    plans = {wg: {"item": item["id"],
                  "stored": plan(stored[wg], reference["revision_chain"], item["anchor"]),
                  "analyzed": plan(analyzed[wg], reference["revision_chain"], item["anchor"]),
                  "orderedJoin": plan(stored[wg], ordered["revision_chain"], item["anchor"]),
                  "materializedHint": plan(stored[wg], hinted["revision_chain"], item["anchor"])}
             for wg, item in sorted(first.items())}
    other_plans_changed = {}
    for family in sorted(reference):
        if family == "revision_chain":
            continue
        sample = next(item for item in items if item["family"] == family)
        before = plan(stored[sample["wg"]], reference[family], sample["anchor"])
        after = plan(analyzed[sample["wg"]], reference[family], sample["anchor"])
        other_plans_changed[family] = {"item": sample["id"], "samePlan": before == after, "stored": before, "analyzed": after}
    table_rows = {wg: {name: stored[wg].execute(f"SELECT count(*) FROM {name}").fetchone()[0]
                       for name in ("revision", "disposition", "document", "cr_in_pack")} for wg in groups}
    for db in list(stored.values()) + list(analyzed.values()):
        db.close()
    shutil.rmtree(args.work)

    record = {"scope": "reference SQL under four conditions: exported file, after ANALYZE on a copy, "
                       "written join order kept, MATERIALIZED hint; read-only on the exported files",
              "design": {"items": len(items), "revisionChainItems": len(chain_items), "warmupPasses": 1,
                         "timedPasses": TIMED_PASSES, "perQueryTime": "median of the timed passes",
                         "percentile": "linear interpolation between order statistics, position (n - 1) * q",
                         "analyzeOn": "copies in the work folder, removed at the end"},
              "context": {"interpreter": sys.executable, "python": platform.python_version(),
                          "sqliteLibrary": sqlite3.sqlite_version, "cpuAffinity": sorted(os.sched_getaffinity(0)),
                          "loadAverageAtStart": started_load, "loadAverageAtEnd": list(os.getloadavg()),
                          "analyzeSeconds": analyze_seconds, "statisticsRowsAfterAnalyze": statistics_rows,
                          "tableRows": table_rows},
              "queries": {"reference": " ".join(reference["revision_chain"].split()),
                          "orderedJoin": " ".join(ordered["revision_chain"].split()),
                          "materializedHint": " ".join(hinted["revision_chain"].split())},
              "conditions": conditions, "revisionChainPlans": plans, "otherFamilyPlans": other_plans_changed}
    args.out.write_text(json.dumps(record, indent=1) + "\n")
    print(json.dumps({"out": str(args.out), "mismatches": {k: v["mismatchesInAllPasses"] for k, v in conditions.items()}}))


if __name__ == "__main__":
    main()
