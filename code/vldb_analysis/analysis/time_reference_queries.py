"""추적 사슬 문항의 참조 질의를 두 엔진에서 실행해 질의당 실행 시간을 잰다 (모델 호출 없음, 읽기 전용).

문항마다 참조 SQL(`cr_side` 벌)을 그 작업반의 SQLite 파일에, 참조 Cypher 를 그 작업반의 Neo4j 에 실행한다.
엔진과 작업반마다 연결 하나를 쓰고 문항을 파일 순서대로 차례로 실행한다. 엔진마다 시간을 재지 않는 준비 회차를
한 번 돌린 뒤 시간을 재는 회차를 세 번 돌리고, 질의당 시간은 세 회차의 중앙값이다. 재는 구간은 실행부터 결과 행을
모두 받을 때까지이고 `time.perf_counter` 로 잰다. 정답 비교는 재는 구간 밖에서 한다.

정답 비교는 참조 질의를 둔 두 스크립트와 같은 식이다. SQL 은 결과 행 집합과 gold 행 집합의 일치
(`measure_relational_equivalence.py`), Cypher 는 정렬한 결과 행 목록과 정렬한 gold 행 목록의 일치
(`crosscheck_chain_items_graph.py`)다. 다르면 질의를 고치지 않고 문항을 그대로 적는다.

SQLite 는 재는 프로세스 안에서 돌고 Neo4j 는 컨테이너의 서버에 localhost Bolt 로 접속하므로, Neo4j 쪽 시간에는
드라이버와 서버 사이의 왕복이 들어 있다. `taskset` 은 재는 프로세스만 묶고 Neo4j 서버 프로세스는 묶지 않는다.

백분위수는 정렬한 값 사이를 선형 보간해 구한다(위치 = (n - 1) × q).

사용: PYTHONPATH=scripts/common taskset -c 12-15 python3 -B <이 파일> --out <json> [--smoke N]
저장소 루트에서 실행한다. `--smoke N` 은 작업반마다 앞의 N 문항만 실행해 코드 경로를 확인한다.
"""
from __future__ import annotations

import argparse
import collections
import datetime
import json
import math
import os
import platform
import sqlite3
import statistics
import subprocess
import sys
import time
from pathlib import Path

RESEARCH = Path("scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark")
LOGS = Path("logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark")
ITEM_FILES = [LOGS / "integration/items_final/gate/core/chain_items_admitted.jsonl",
              LOGS / "integration/items_final/gate/ran5/chain_items_admitted.jsonl"]
SQLITE_DIR = LOGS / "integration/sqlite_final"
BOLT_PORT = {"RAN1": 7687, "RAN2": 7688, "RAN3": 7689, "RAN4": 7690, "RAN5": 7691}
CONTAINER = {"RAN1": "neo4j-tdoc", "RAN2": "neo4j-tdoc-ran2", "RAN3": "neo4j-tdoc-ran3",
             "RAN4": "neo4j-tdoc-ran4", "RAN5": "neo4j-tdoc-ran5"}
VARIANT = "cr_side"
TIMED_PASSES = 3
MIN_AVAILABLE_GIB = 8

sys.path.insert(0, str(RESEARCH))
import neo4j  # noqa: E402
from neo4j import GraphDatabase  # noqa: E402

from common.credentials import neo4j_auth  # noqa: E402
from crosscheck_chain_items_graph import CLAUSE_SET_CYPHER, CYPHER, graph_key  # noqa: E402
from measure_relational_equivalence import CLAUSE_SET_SQL, SQL, VARIANTS  # noqa: E402


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    low, high = math.floor(position), math.ceil(position)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def command_output(command: list[str]) -> str:
    try:
        return subprocess.run(command, capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception as error:  # 기록용 명령이 없거나 실패하면 그 사실을 적는다
        return f"unavailable: {error}"


def available_gib() -> float:
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) / 1024 / 1024
    raise RuntimeError("MemAvailable not found")


def load_items(limit: int | None) -> list[dict]:
    items = []
    taken: collections.Counter[str] = collections.Counter()
    for path in ITEM_FILES:
        with path.open() as lines:
            for line in lines:
                item = json.loads(line)
                if limit is not None and taken[item["wg"]] >= limit:
                    continue
                taken[item["wg"]] += 1
                items.append(item)
    return items


def sqlite_pass(connections: dict, items: list[dict], queries: dict) -> list[dict]:
    """문항마다 (걸린 ms, 행 수, gold 와 같은가, 다르면 차이)를 낸다."""
    results = []
    for item in items:
        db = connections[item["wg"]]
        sql = queries[item["family"]]
        parameters = {"anchor": item["anchor"]}
        started = time.perf_counter()
        rows = db.execute(sql, parameters).fetchall()
        elapsed = time.perf_counter() - started
        derived = {tuple(row) for row in rows}
        gold = {tuple(row) for row in item["gold"]}
        result = {"ms": elapsed * 1000, "rows": len(rows), "same": derived == gold}
        if derived != gold:
            result["difference"] = {"onlyInGold": sorted(gold - derived, key=repr)[:5],
                                    "onlyInEngine": sorted(derived - gold, key=repr)[:5]}
        results.append(result)
    return results


def neo4j_pass(sessions: dict, items: list[dict], queries: dict) -> list[dict]:
    results = []
    for item in items:
        session = sessions[item["wg"]]
        query = queries[item["family"]]
        key = graph_key(item["anchor"])
        started = time.perf_counter()
        records = list(session.run(query, anchor=key))
        elapsed = time.perf_counter() - started
        result = {"ms": elapsed * 1000, "rows": len(records)}
        try:
            from_graph = sorted(tuple(record.values()) for record in records)
            gold = sorted(tuple(row) for row in item["gold"])
            result["same"] = from_graph == gold
        except TypeError as error:  # 정렬할 수 없는 값이 섞이면 비교하지 못한 것으로 따로 센다
            result["same"] = None
            result["comparisonError"] = str(error)
            from_graph, gold = [tuple(record.values()) for record in records], [tuple(row) for row in item["gold"]]
        if result["same"] is False:
            result["difference"] = {"onlyInGold": sorted(set(gold) - set(from_graph), key=repr)[:5],
                                    "onlyInEngine": sorted(set(from_graph) - set(gold), key=repr)[:5]}
        results.append(result)
    return results


def measure(run_pass, handles: dict, items: list[dict], queries: dict, label: str) -> dict:
    """준비 회차 한 번과 시간을 재는 회차 세 번. 회차마다 gold 와 다른 문항을 적는다."""
    passes = []
    pass_records = []
    for number in range(TIMED_PASSES + 1):
        name = "warmup" if number == 0 else f"timed{number}"
        started = time.perf_counter()
        results = run_pass(handles, items, queries)
        wall = time.perf_counter() - started
        differing = [{"id": item["id"], "wg": item["wg"], "family": item["family"], "rows": result["rows"],
                      "goldRows": len(item["gold"]), **result.get("difference", {}),
                      **({"comparisonError": result["comparisonError"]} if "comparisonError" in result else {})}
                     for item, result in zip(items, results) if result["same"] is not True]
        pass_records.append({"pass": name, "timed": number > 0, "items": len(results),
                             "matchingGold": sum(result["same"] is True for result in results),
                             "mismatches": len(differing), "differing": differing,
                             "wallSeconds": round(wall, 3), "loadAverageAfter": list(os.getloadavg())})
        print(f"{label} {name}: items={len(results)} mismatches={len(differing)}", flush=True)
        if number > 0:
            passes.append(results)
    per_item = []
    for index, item in enumerate(items):
        times = [results[index]["ms"] for results in passes]
        rows = [results[index]["rows"] for results in passes]
        per_item.append({"ms": [round(value, 4) for value in times], "medianMs": statistics.median(times),
                         "rows": rows[0], "rowsSameInEveryTimedPass": len(set(rows)) == 1})
    return {"passes": pass_records, "perItem": per_item}


def summary(rows: list[tuple[dict, dict]]) -> dict:
    times = [measured["medianMs"] for _, measured in rows]
    return {"items": len(rows), "medianMs": round(statistics.median(times), 4),
            "p95Ms": round(percentile(times, 0.95), 4), "maxMs": round(max(times), 4),
            "meanRows": round(statistics.fmean(measured["rows"] for _, measured in rows), 4)}


def summarize(items: list[dict], per_item: list[dict]) -> dict:
    pairs = list(zip(items, per_item))
    families = sorted({item["family"] for item in items})
    groups = sorted({item["wg"] for item in items})
    return {"all": summary(pairs),
            "byFamily": {family: summary([pair for pair in pairs if pair[0]["family"] == family]) for family in families},
            "byWg": {wg: summary([pair for pair in pairs if pair[0]["wg"] == wg]) for wg in groups}}


def sqlite_context(connections: dict) -> dict:
    context = {}
    for wg, db in connections.items():
        objects = db.execute("SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY type, name").fetchall()
        tables = [name for kind, name, _, _ in objects if kind == "table"]
        context[wg] = {
            "file": str(SQLITE_DIR / f"{wg}.sqlite"), "fileBytes": (SQLITE_DIR / f"{wg}.sqlite").stat().st_size,
            "sqliteVersion": db.execute("SELECT sqlite_version()").fetchone()[0],
            "pageSize": db.execute("PRAGMA page_size").fetchone()[0],
            "cacheSize": db.execute("PRAGMA cache_size").fetchone()[0],
            "mmapSize": (db.execute("PRAGMA mmap_size").fetchone() or [None])[0],
            "statisticsTablePresent": "sqlite_stat1" in tables,
            "tableRows": {name: db.execute(f"SELECT count(*) FROM {name}").fetchone()[0] for name in tables},
            "indexes": [{"name": name, "table": table, "sql": sql} for kind, name, table, sql in objects if kind == "index"]}
    return context


def neo4j_context(sessions: dict) -> dict:
    context = {}
    for wg, session in sessions.items():
        entry = {"bolt": f"bolt://localhost:{BOLT_PORT[wg]}", "container": CONTAINER[wg],
                 "components": [dict(record) for record in session.run("CALL dbms.components()")],
                 "indexes": [{key: record[key] for key in ("name", "type", "entityType", "labelsOrTypes", "properties", "state")}
                             for record in session.run("SHOW INDEXES")],
                 "nodes": session.run("MATCH (n) RETURN count(n) AS n").single()["n"],
                 "relationships": session.run("MATCH ()-[r]->() RETURN count(r) AS n").single()["n"]}
        try:
            entry["memorySettings"] = {record["name"]: record["value"] for record in session.run(
                "SHOW SETTINGS YIELD name, value WHERE name STARTS WITH 'server.memory' RETURN name, value")}
        except Exception as error:  # 설정을 읽을 권한이 없으면 그 사실을 적는다
            entry["memorySettings"] = f"unavailable: {str(error)[:200]}"
        entry["containerLimits"] = command_output(
            ["docker", "inspect", "--format",
             "cpuset={{.HostConfig.CpusetCpus}} nanoCpus={{.HostConfig.NanoCpus}} memoryBytes={{.HostConfig.Memory}}",
             CONTAINER[wg]])
        context[wg] = entry
    return context


def plan_operators(plan: dict, depth: int = 0) -> list[dict]:
    arguments = plan.get("args") or {}
    here = {"depth": depth, "operator": plan.get("operatorType"), "details": arguments.get("Details")}
    return [here] + [row for child in plan.get("children") or [] for row in plan_operators(child, depth + 1)]


def plans(items: list[dict], connections: dict, sessions: dict, sql_queries: dict, cypher_queries: dict) -> dict:
    """문항 종류마다 파일 순서로 첫 문항의 실행 계획. 질의를 실행하지 않는다."""
    first: dict[str, dict] = {}
    for item in items:
        first.setdefault(item["family"], item)
    report = {}
    for family, item in first.items():
        sql, cypher = sql_queries[family], cypher_queries[family]
        steps = connections[item["wg"]].execute("EXPLAIN QUERY PLAN " + sql, {"anchor": item["anchor"]}).fetchall()
        plan = sessions[item["wg"]].run("EXPLAIN " + cypher, anchor=graph_key(item["anchor"])).consume().plan
        arguments = plan.get("args") or {}
        report[family] = {
            "item": item["id"], "wg": item["wg"],
            "sql": " ".join(sql.split()),
            "sqliteExplainQueryPlan": [{"id": step[0], "parent": step[1], "detail": step[3]} for step in steps],
            "cypher": " ".join(cypher.split()),
            "neo4jExplain": {"planner": arguments.get("planner"), "plannerImpl": arguments.get("planner-impl"),
                             "runtime": arguments.get("runtime"), "runtimeImpl": arguments.get("runtime-impl"),
                             "version": arguments.get("version"),
                             "operators": plan_operators(plan)}}
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--smoke", type=int, default=None)
    args = parser.parse_args()
    memory = available_gib()
    if memory < MIN_AVAILABLE_GIB:
        raise SystemExit(f"available memory {memory:.1f} GiB is under {MIN_AVAILABLE_GIB} GiB; not measuring")
    host = {"measuredAt": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            "uptimeAtStart": command_output(["uptime"]), "loadAverageAtStart": list(os.getloadavg()),
            "availableMemoryGiBAtStart": round(memory, 2), "logicalCpus": os.cpu_count(),
            "cpuAffinityOfMeasuringProcess": sorted(os.sched_getaffinity(0)),
            "pinning": "taskset -c 12-15 on the measuring Python process (driver and in-process SQLite); "
                       "the Neo4j server processes run in containers and are not pinned by it",
            "otherJobsRunning": True,
            "busiestProcessesAtStart": command_output(["ps", "-eo", "pcpu,comm", "--sort=-pcpu"]).splitlines()[:9],
            "platform": platform.platform(), "python": platform.python_version(),
            "sqliteLibrary": sqlite3.sqlite_version, "neo4jDriver": neo4j.__version__}

    items = load_items(args.smoke)
    present = {item["family"] for item in items}
    sql_queries = {family: text.format(**VARIANTS[VARIANT])
                   for family, text in {**SQL, **{f: s for f, s in CLAUSE_SET_SQL.items() if f in present}}.items()}
    cypher_queries = {**CYPHER, **{f: c for f, c in CLAUSE_SET_CYPHER.items() if f in present}}
    groups = sorted({item["wg"] for item in items})

    connections = {wg: sqlite3.connect(f"file:{SQLITE_DIR / (wg + '.sqlite')}?mode=ro", uri=True) for wg in groups}
    auth = neo4j_auth()
    drivers = {wg: GraphDatabase.driver(f"bolt://localhost:{BOLT_PORT[wg]}", auth=auth) for wg in groups}
    sessions = {wg: drivers[wg].session(default_access_mode=neo4j.READ_ACCESS) for wg in groups}
    try:
        context = {"host": host, "sqlite": sqlite_context(connections), "neo4j": neo4j_context(sessions)}
        relational = measure(sqlite_pass, connections, items, sql_queries, "sqlite")
        graph = measure(neo4j_pass, sessions, items, cypher_queries, "neo4j")
        explained = plans(items, connections, sessions, sql_queries, cypher_queries)
    finally:
        for session in sessions.values():
            session.close()
        for driver in drivers.values():
            driver.close()
        for db in connections.values():
            db.close()
    host["uptimeAtEnd"] = command_output(["uptime"])

    report = {
        "scope": "execution time of the reference SQL (cr_side) on SQLite and the reference Cypher on Neo4j, "
                 "one query per item, read-only",
        "design": {"items": len(items), "itemFiles": [str(path) for path in ITEM_FILES], "smoke": args.smoke,
                   "sqlVariant": VARIANT, "order": "items in file order; SQLite first, then Neo4j",
                   "connections": "one SQLite connection and one Neo4j session per working group, sequential",
                   "warmupPassesPerEngine": 1, "timedPassesPerEngine": TIMED_PASSES,
                   "perQueryTime": "median of the timed passes",
                   "timedRegion": "time.perf_counter around execute and fetch-all; gold comparison outside",
                   "sqliteTimedCall": "connection.execute(sql, {'anchor': anchor}).fetchall()",
                   "neo4jTimedCall": "list(session.run(cypher, anchor=graph_key(anchor))) in a READ_ACCESS session",
                   "neo4jIncludesClientServerRoundTrip": True,
                   "percentile": "linear interpolation between order statistics, position (n - 1) * q",
                   "goldComparison": {"sqlite": "set of returned rows == set of gold rows",
                                      "neo4j": "sorted list of returned rows == sorted list of gold rows"}},
        "context": context,
        "sqlite": {"mismatchesInTimedPasses": sum(p["mismatches"] for p in relational["passes"] if p["timed"]),
                   "mismatchesInWarmup": relational["passes"][0]["mismatches"],
                   "passes": relational["passes"], **summarize(items, relational["perItem"])},
        "neo4j": {"mismatchesInTimedPasses": sum(p["mismatches"] for p in graph["passes"] if p["timed"]),
                  "mismatchesInWarmup": graph["passes"][0]["mismatches"],
                  "passes": graph["passes"], **summarize(items, graph["perItem"])},
        "rowCountChecks": {
            "sqliteRowsSameInEveryTimedPass": all(row["rowsSameInEveryTimedPass"] for row in relational["perItem"]),
            "neo4jRowsSameInEveryTimedPass": all(row["rowsSameInEveryTimedPass"] for row in graph["perItem"]),
            "itemsWhereEnginesReturnDifferentRowCounts": [
                item["id"] for item, a, b in zip(items, relational["perItem"], graph["perItem"]) if a["rows"] != b["rows"]]},
        "plansForFirstItemPerFamily": explained,
        "perItem": [{"id": item["id"], "wg": item["wg"], "family": item["family"], "goldRows": len(item["gold"]),
                     "sqlite": {"ms": a["ms"], "medianMs": round(a["medianMs"], 4), "rows": a["rows"]},
                     "neo4j": {"ms": b["ms"], "medianMs": round(b["medianMs"], 4), "rows": b["rows"]}}
                    for item, a, b in zip(items, relational["perItem"], graph["perItem"])],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({"items": len(items), "out": str(args.out),
                      "sqliteMismatches": report["sqlite"]["mismatchesInTimedPasses"],
                      "neo4jMismatches": report["neo4j"]["mismatchesInTimedPasses"]}))


if __name__ == "__main__":
    main()
