"""참조 SQL 을 PostgreSQL 에서 통계 유무와 조인 순서 지정에 따라 실행해 시간과 실행 계획을 적는다 (모델 호출 없음).

SQLite 측정(time_sql_plan_variants.py)과 같은 문항 · 같은 참조 SQL · 같은 표와 색인을 쓴다. 조건은 넷이고,
revision_chain 의 두 변형은 통계가 없는 상태와 ANALYZE 뒤 상태 양쪽에서 잰다.
  stored            내보낸 표를 적재하고 색인을 만든 그대로 (ANALYZE 없음, autovacuum 꺼짐). 일곱 유형 전부.
  analyzed          ANALYZE 뒤. 일곱 유형 전부.
  orderedJoin       revision_chain 에 join_collapse_limit = 1 을 걸어 적힌 조인 순서를 지킨다.
  materializedHint  revision_chain 의 재귀 공통 표 식에 MATERIALIZED 를 붙인다.

서버는 임시 컨테이너 하나이고 드라이버 없이 docker exec 의 psql 로만 다룬다. 조건마다 첫 실행에서 행 집합을
gold 와 비교하고(워밍업 겸용), 이어서 EXPLAIN (ANALYZE, TIMING OFF) 를 3회 실행해 서버가 적은 계획 시간과
실행 시간의 합을 문항별 중앙값으로 쓴다. anchor 는 문자열 리터럴로 넣는다.

사용:
  python3 -B <이 파일> up                     # 컨테이너 시작
  python3 -B <이 파일> load                   # 다섯 SQLite 내보내기를 스키마 ran1~ran5 로 적재
  python3 -B <이 파일> measure --out <json> [--smoke N]
  python3 -B <이 파일> down                   # 컨테이너와 익명 볼륨 삭제
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import statistics
import subprocess
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
CONTAINER = "spectra-pg-bench"
IMAGE = "public.ecr.aws/docker/library/postgres:17-alpine"
CPUSET = "16-19"
MEMORY = "4g"
TIMED_PASSES = 3
MARK = "@@MARK@@"
SETTINGS = ["server_version", "autovacuum", "shared_buffers", "work_mem", "effective_cache_size", "random_page_cost",
            "join_collapse_limit", "from_collapse_limit", "geqo_threshold", "max_parallel_workers_per_gather", "jit"]


def psql(script: str, timeout: int = 3000) -> str:
    done = subprocess.run(["docker", "exec", "-i", CONTAINER, "psql", "-X", "-q", "-t", "-A", "-v", "ON_ERROR_STOP=1",
                           "-U", "postgres", "-d", "bench", "-f", "-"],
                          input=script, capture_output=True, text=True, timeout=timeout)
    if done.returncode != 0:
        raise SystemExit(f"psql exit {done.returncode}: {done.stderr[-600:]}")
    return done.stdout


def up() -> None:
    subprocess.run(["docker", "run", "-d", "--name", CONTAINER, "--cpuset-cpus", CPUSET, "--memory", MEMORY,
                    "--shm-size", "1g", "-e", "POSTGRES_HOST_AUTH_METHOD=trust", "-e", "POSTGRES_DB=bench",
                    IMAGE, "-c", "autovacuum=off"], check=True)
    for _ in range(60):
        ready = subprocess.run(["docker", "exec", CONTAINER, "psql", "-X", "-q", "-t", "-A", "-U", "postgres",
                                "-d", "bench", "-c", "SELECT 1"], capture_output=True, text=True)
        if ready.returncode == 0 and ready.stdout.strip() == "1":
            print("ready", flush=True)
            return
        time.sleep(1)
    raise SystemExit("server did not become ready")


def down() -> None:
    subprocess.run(["docker", "rm", "-f", "-v", CONTAINER], check=True)


def csv_field(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return str(value)
    assert isinstance(value, str), type(value)
    return '"' + value.replace('"', '""') + '"'


def load() -> None:
    summary = {}
    for path in sorted(SQLITE_DIR.glob("RAN*.sqlite")):
        schema = path.stem.lower()
        db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        objects = db.execute("SELECT type, name, sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type DESC, name").fetchall()
        tables = [(name, " ".join(sql.split())) for kind, name, sql in objects if kind == "table"]
        indexes = [" ".join(sql.split()) for kind, name, sql in objects if kind == "index"]
        proc = subprocess.Popen(["docker", "exec", "-i", CONTAINER, "psql", "-X", "-q", "-v", "ON_ERROR_STOP=1",
                                 "-U", "postgres", "-d", "bench", "-f", "-"],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out = proc.stdin
        out.write(f"CREATE SCHEMA {schema};\nSET search_path = {schema};\n")
        counts = {}
        for name, ddl in tables:
            out.write(ddl + ";\n")
            out.write(f"COPY {name} FROM STDIN (FORMAT csv);\n")
            rows = 0
            for row in db.execute(f"SELECT * FROM {name}"):
                out.write(",".join(csv_field(value) for value in row) + "\n")
                rows += 1
            out.write("\\.\n")
            counts[name] = rows
        for ddl in indexes:
            out.write(ddl + ";\n")
        out.close()
        stdout = proc.stdout.read()
        stderr = proc.stderr.read()
        code = proc.wait()
        if code != 0:
            raise SystemExit(f"{schema}: psql exit {code}: {stderr[-600:]} {stdout[-300:]}")
        check = psql("".join(f"SELECT '{name}', count(*) FROM {schema}.{name};\n" for name, _ in tables))
        loaded = {line.split("|")[0]: int(line.split("|")[1]) for line in check.splitlines() if line.strip()}
        assert loaded == counts, (schema, loaded, counts)
        summary[schema] = {"tables": len(tables), "explicitIndexes": len(indexes), "rows": sum(counts.values())}
        print(schema, summary[schema], flush=True)
        db.close()
    statistics_rows = psql("SELECT count(*) FROM pg_stats WHERE schemaname LIKE 'ran%';").strip()
    print(json.dumps({"loaded": summary, "pgStatsRowsBeforeAnalyze": int(statistics_rows)}))


def literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def bind(sql: str, anchor: str) -> str:
    assert ":anchor" in sql
    return re.sub(r":anchor\b", lambda _: literal(anchor), " ".join(sql.split()))


def blocks(output: str) -> dict[str, str]:
    result: dict[str, list[str]] = {}
    current = None
    for line in output.splitlines():
        if line.startswith(MARK):
            current = line[len(MARK):].strip()
            result[current] = []
        elif current is not None:
            result[current].append(line)
    return {key: "\n".join(lines).strip() for key, lines in result.items()}


def plan_lines(node: dict, depth: int = 0) -> list[str]:
    label = node["Node Type"]
    if node.get("Join Type"):
        label += f" [{node['Join Type']}]"
    for key in ("Relation Name", "Index Name", "CTE Name"):
        if node.get(key):
            label += f" {key.split()[0].lower()}={node[key]}"
    if node.get("Alias") and node.get("Alias") != node.get("Relation Name"):
        label += f" as {node['Alias']}"
    label += f" rows={node.get('Actual Rows')} loops={node.get('Actual Loops')}"
    lines = ["  " * depth + label]
    for child in node.get("Plans", []):
        lines.extend(plan_lines(child, depth + 1))
    return lines


def sequential_scans(node: dict) -> list[str]:
    found = []
    if node["Node Type"] in ("Seq Scan", "Parallel Seq Scan"):
        found.append(node["Relation Name"])
    for child in node.get("Plans", []):
        found.extend(sequential_scans(child))
    return found


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def measure_condition(items: list[dict], queries: dict, label: str, session_setup: str = "") -> dict:
    script = [session_setup]
    for index, item in enumerate(items):
        text = bind(queries[item["family"]], item["anchor"])
        script.append(f"SET search_path = {item['wg'].lower()};")
        script.append(f"\\echo {MARK}{index} rows")
        script.append(f"SELECT json_agg(t) FROM ({text}) t;")
    for attempt in range(TIMED_PASSES):
        for index, item in enumerate(items):
            text = bind(queries[item["family"]], item["anchor"])
            script.append(f"SET search_path = {item['wg'].lower()};")
            script.append(f"\\echo {MARK}{index} plan{attempt}")
            script.append(f"EXPLAIN (ANALYZE, TIMING OFF, FORMAT JSON) {text};")
    begun = time.perf_counter()
    parsed = blocks(psql("\n".join(script) + "\n"))
    wall = time.perf_counter() - begun
    mismatches = 0
    medians, planning, execution = [], [], []
    scans: dict[str, dict[str, int]] = {}
    samples: dict[str, dict] = {}
    for index, item in enumerate(items):
        raw = parsed[f"{index} rows"]
        rows = json.loads(raw, object_pairs_hook=lambda pairs: tuple(value for _, value in pairs)) if raw else []
        if {tuple(row) for row in rows} != {tuple(row) for row in item["gold"]}:
            mismatches += 1
        totals, plans, executions = [], [], []
        for attempt in range(TIMED_PASSES):
            document = json.loads(parsed[f"{index} plan{attempt}"])[0]
            plans.append(document["Planning Time"])
            executions.append(document["Execution Time"])
            totals.append(document["Planning Time"] + document["Execution Time"])
        medians.append(statistics.median(totals))
        planning.append(statistics.median(plans))
        execution.append(statistics.median(executions))
        last = json.loads(parsed[f"{index} plan{TIMED_PASSES - 1}"])[0]
        family_scans = scans.setdefault(item["family"], {})
        key = "+".join(sorted(sequential_scans(last["Plan"]))) or "none"
        family_scans[key] = family_scans.get(key, 0) + 1
        sample_key = f"{item['family']}|{item['wg']}"
        if sample_key not in samples:
            samples[sample_key] = {"item": item["id"], "plan": plan_lines(last["Plan"]), "jit": "JIT" in last}

    def summary(values: list[float]) -> dict:
        return {"items": len(values), "medianMs": round(percentile(values, 0.5), 4),
                "p95Ms": round(percentile(values, 0.95), 4), "maxMs": round(max(values), 4)}

    by_family: dict[str, dict[str, list[float]]] = {}
    for item, total, plan_ms, run_ms in zip(items, medians, planning, execution):
        group = by_family.setdefault(item["family"], {"total": [], "planning": [], "execution": []})
        group["total"].append(total)
        group["planning"].append(plan_ms)
        group["execution"].append(run_ms)
    print(f"{label}: items={len(items)} mismatches={mismatches} wall={wall:.1f}s", flush=True)
    return {"items": len(items), "goldMismatches": mismatches, "wallSeconds": round(wall, 1),
            "all": summary(medians),
            "byFamily": {family: {"total": summary(group["total"]), "planning": summary(group["planning"]),
                                  "execution": summary(group["execution"])}
                         for family, group in sorted(by_family.items())},
            "sequentialScansByFamily": {family: dict(sorted(counts.items())) for family, counts in sorted(scans.items())},
            "samplePlans": samples,
            "perItemMedianMs": {item["id"]: round(value, 4) for item, value in zip(items, medians)}}


def measure(out: Path, smoke: int | None) -> None:
    items = []
    for path in ITEM_FILES:
        with path.open() as lines:
            items.extend(json.loads(line) for line in lines)
    if smoke:
        kept: dict[str, int] = {}
        chosen = []
        for item in items:
            if kept.get(item["family"], 0) < smoke:
                kept[item["family"]] = kept.get(item["family"], 0) + 1
                chosen.append(item)
        items = chosen
    reference = {family: text.format(**VARIANTS["cr_side"]) for family, text in SQL.items()}
    chain_items = [item for item in items if item["family"] == "revision_chain"]
    assert reference["revision_chain"].count("later(id) AS (") == 1
    hinted = {"revision_chain": reference["revision_chain"].replace("later(id) AS (", "later(id) AS MATERIALIZED (")}
    chain_only = {"revision_chain": reference["revision_chain"]}

    settings = {name: psql(f"SHOW {name};").strip() for name in SETTINGS}
    statistics_before = int(psql("SELECT count(*) FROM pg_stats WHERE schemaname LIKE 'ran%';").strip())
    assert statistics_before == 0, statistics_before
    started_load = list(os.getloadavg())
    conditions = {
        "stored": measure_condition(items, reference, "stored"),
        "stored.orderedJoin": measure_condition(chain_items, chain_only, "stored.orderedJoin", "SET join_collapse_limit = 1;"),
        "stored.materializedHint": measure_condition(chain_items, hinted, "stored.materializedHint"),
    }
    begun = time.perf_counter()
    psql("ANALYZE;")
    analyze_seconds = round(time.perf_counter() - begun, 2)
    statistics_after = int(psql("SELECT count(*) FROM pg_stats WHERE schemaname LIKE 'ran%';").strip())
    conditions["analyzed"] = measure_condition(items, reference, "analyzed")
    conditions["analyzed.orderedJoin"] = measure_condition(chain_items, chain_only, "analyzed.orderedJoin",
                                                           "SET join_collapse_limit = 1;")
    conditions["analyzed.materializedHint"] = measure_condition(chain_items, hinted, "analyzed.materializedHint")
    record = {"scope": "reference SQL on PostgreSQL: loaded and indexed without ANALYZE, after ANALYZE, written join "
                       "order kept (join_collapse_limit = 1), MATERIALIZED hint",
              "design": {"items": len(items), "revisionChainItems": len(chain_items), "smokePerFamily": smoke,
                         "goldCheck": "first execution of every query in every condition, row set against gold",
                         "timedPasses": TIMED_PASSES,
                         "perQueryTime": "median over the timed passes of server-reported Planning Time + Execution Time "
                                         "from EXPLAIN (ANALYZE, TIMING OFF, FORMAT JSON)",
                         "anchor": "inlined as a string literal",
                         "percentile": "linear interpolation between order statistics, position (n - 1) * q"},
              "context": {"image": IMAGE, "container": {"cpuset": CPUSET, "memory": MEMORY, "shm": "1g",
                                                        "serverOption": "autovacuum=off"},
                          "settings": settings, "pgStatsRowsBeforeAnalyze": statistics_before,
                          "pgStatsRowsAfterAnalyze": statistics_after, "analyzeSeconds": analyze_seconds,
                          "loadAverageAtStart": started_load, "loadAverageAtEnd": list(os.getloadavg())},
              "queries": {"reference": " ".join(reference["revision_chain"].split()),
                          "materializedHint": " ".join(hinted["revision_chain"].split())},
              "conditions": conditions}
    out.write_text(json.dumps(record, indent=1) + "\n")
    print(json.dumps({"out": str(out), "mismatches": {k: v["goldMismatches"] for k, v in conditions.items()}}))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["up", "load", "measure", "down"])
    parser.add_argument("--out", type=Path)
    parser.add_argument("--smoke", type=int)
    args = parser.parse_args()
    if args.command == "up":
        up()
    elif args.command == "load":
        load()
    elif args.command == "measure":
        assert args.out is not None
        measure(args.out, args.smoke)
    else:
        down()


if __name__ == "__main__":
    main()
