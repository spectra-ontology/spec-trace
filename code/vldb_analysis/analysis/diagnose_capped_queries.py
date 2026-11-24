"""실행 상한에 걸린 에이전트 작성 질의를 저장된 응답에서 모아 실행 계획으로 진단한다 (모델 호출 없음, 읽기 전용).

대상은 저장된 응답 기록 100 파일이다(작업반 다섯 × 실행 A~J, SQL 과 Cypher 각각). 풀이 때 SQL 은 진행 처리기가
60초 뒤에 실행을 끊어 SQLite 가 `interrupted` 오류를 내고, Cypher 는 트랜잭션 제한 60초로 실행했다
(`run_chain_eval.py` 의 `solve_text2sql` · `solve_text2cypher`). 그래서 상한에 걸린 시도는 `attempts` 의 오류 문장이
아래 `CAP_ERROR` 에 맞는 것으로 고르고, 기록의 `seconds` 로 한 번 더 맞대 본다.

걸린 질의는 다시 실행하지 않는다. SQL 은 그 작업반의 SQLite 파일을 `mode=ro` 로 열어 `EXPLAIN QUERY PLAN` 만
받고, 같은 문항의 참조 SQL(`cr_side` 벌)도 같은 방식으로 받아 둘을 나란히 적는다. Cypher 는 읽기 세션에서
`EXPLAIN` 만 받는다. 표의 행 수를 세는 `count(*)` 는 계획을 읽는 데 쓰는 배경 수치다.

질의 꼴은 문자열 상수를 자리로 바꾼 본문이 같은 것끼리 묶는다. 묶음 안에서 값이 달라지는 자리는 그 문항의
기준 식별자나 질문 문장에서 온 값인지 확인하고, 그렇지 않은 자리가 있으면 그 값으로 묶음을 다시 나눈다.
묶음 안에서 값이 같은 상수는 꼴의 일부로 남긴다.

사용: PYTHONPATH=scripts/common taskset -c 12-15 python3 -B <이 파일> --out <json>
저장소 루트에서 실행한다.
"""
from __future__ import annotations

import argparse
import ast
import collections
import datetime
import json
import os
import platform
import re
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
RECORD_ROOT = LOGS / "chain_eval"
MAIN_FILES = {
    "sql": (RECORD_ROOT / "text2sql", re.compile(r"^(RAN[1-5])_text2sql_run([A-J])\.jsonl$")),
    "cypher": (RECORD_ROOT, re.compile(r"^(RAN[1-5])_text2cypher_claude_subagent_run([A-J])\.jsonl$")),
}
BOLT_PORT = {"RAN1": 7687, "RAN2": 7688, "RAN3": 7689, "RAN4": 7690, "RAN5": 7691}
LONG_CAP_RERUN = LOGS / "final/diagnosis/text2sql_deadline_rerun_runs_B_D.json"
VARIANT = "cr_side"
CAP_SECONDS = 60
MIN_AVAILABLE_GIB = 8
# 풀이 때의 상한이 남기는 오류 문장. SQLite 는 `interrupted`, Neo4j 는 트랜잭션 제한 초과 문장을 낸다.
CAP_ERROR = re.compile(r"interrupt|timed\s?out|timeout|terminat|deadline", re.IGNORECASE)
NAME = r"[A-Za-z_][A-Za-z0-9_]*"
STRING_LITERAL = re.compile(r"'(?:[^']|'')*'")
TABLE_ALIAS = re.compile(rf"\b(?:FROM|JOIN)\s+({NAME})(?:\s+(?:AS\s+)?({NAME}))?", re.IGNORECASE)
CTE_NAME = re.compile(rf"(?:\bWITH(?:\s+RECURSIVE)?|,)\s*({NAME})\s*(?:\([^()]*\))?\s+AS\s*"
                      rf"(?:(?:NOT\s+)?MATERIALIZED\s*)?\(", re.IGNORECASE)
SQL_WORDS = {"on", "where", "join", "left", "inner", "cross", "natural", "group", "order", "union", "select",
             "limit", "using", "except", "intersect", "as"}
TEXT_COUNTS = {
    "lower(": r"\blower\s*\(", "upper(": r"\bupper\s*\(", "replace(": r"\breplace\s*\(", "trim(": r"\btrim\s*\(",
    "coalesce(": r"\bcoalesce\s*\(", "substr(": r"\bsubstr\s*\(", "instr(": r"\binstr\s*\(", "LIKE": r"\bLIKE\b",
    "EXISTS": r"\bEXISTS\b", "UNION": r"\bUNION\b", "JOIN": r"\bJOIN\b", "OR": r"\bOR\b", "IN (": r"\bIN\s*\(",
    "CASE": r"\bCASE\b", "DISTINCT": r"\bDISTINCT\b",
}

sys.path.insert(0, str(RESEARCH))
from crosscheck_chain_items_graph import graph_key  # noqa: E402
from measure_relational_equivalence import SQL, VARIANTS  # noqa: E402


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


def parsed(value):
    return ast.literal_eval(value) if isinstance(value, str) else value


def records_of(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def error_class(text: str) -> str:
    code = re.search(r"Neo\.[A-Za-z.]+", text)
    return code.group(0) if code else text.split(":")[0][:60]


def alnum(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def collect_main(language: str) -> tuple[list[dict], dict]:
    """한 언어의 본 실행 기록을 줄 단위로 읽어 상한에 걸린 시도와 맞대 볼 수치를 모은다."""
    directory, pattern = MAIN_FILES[language]
    capped, files, records = [], 0, 0
    classes: collections.Counter[str] = collections.Counter()
    seconds_bins: collections.Counter[str] = collections.Counter()
    at_cap_without_error, slow_uncapped = [], collections.Counter()
    max_seconds = 0.0
    for path in sorted(directory.iterdir()):
        match = pattern.match(path.name)
        if not match:
            continue
        files += 1
        wg, run = match.groups()
        for record in records_of(path):
            records += 1
            attempts = parsed(record.get("attempts")) or []
            seconds = float(record.get("seconds") or 0.0)
            max_seconds = max(max_seconds, seconds)
            hit = False
            for position, attempt in enumerate(attempts):
                error = attempt.get("error")
                if error is None:
                    continue
                if CAP_ERROR.search(error):
                    hit = True
                    capped.append({"language": language, "file": path.name, "wg": wg, "run": run,
                                   "id": record["id"], "family": record["family"], "recordSeconds": seconds,
                                   "recordRowsIsNull": record.get("rows") is None, "attemptPosition": position + 1,
                                   "attemptsInRecord": len(attempts), "error": error[:200],
                                   "text": attempt.get(language, "")})
                else:
                    classes[error_class(error)] += 1
            label = ("under 1 s" if seconds < 1 else "1 to under 10 s" if seconds < 10 else
                     "10 to under 30 s" if seconds < 30 else "30 to under 59.5 s" if seconds < 59.5 else
                     "59.5 s or more")
            seconds_bins[label] += 1
            if not hit and seconds >= 59.5:
                at_cap_without_error.append({"file": path.name, "id": record["id"], "seconds": seconds})
            if not hit and seconds >= 30:
                slow_uncapped[(run, wg, record["family"])] += 1
    order = ["under 1 s", "1 to under 10 s", "10 to under 30 s", "30 to under 59.5 s", "59.5 s or more"]
    return capped, {
        "files": files, "records": records, "maxRecordSeconds": max_seconds,
        "recordSecondsBins": {label: seconds_bins[label] for label in order},
        "recordsAtCapSecondsWithoutCapError": {"n": len(at_cap_without_error), "first": at_cap_without_error[:20]},
        "uncappedRecordsOf30SecondsOrMore": [{"run": run, "wg": wg, "family": family, "n": n}
                                              for (run, wg, family), n in sorted(slow_uncapped.items())],
        "otherErrorAttemptsByClass": dict(classes.most_common(15)),
    }


def tally(rows: list[dict]) -> dict:
    def by(*keys):
        counts = collections.Counter(tuple(row[key] for key in keys) for row in rows)
        return [{**dict(zip(keys, values)), "n": n} for values, n in sorted(counts.items())]
    return {"n": len(rows), "byLanguage": by("language"), "byRun": by("run"), "byWg": by("wg"),
            "byFamily": by("family"), "byRunWgFamily": by("run", "wg", "family"),
            "errorTexts": dict(collections.Counter(row["error"] for row in rows)),
            "recordSeconds": {str(value): n for value, n in
                              sorted(collections.Counter(row["recordSeconds"] for row in rows).items())},
            "attemptPositionOfAttempts": {f"{row_key[0]} of {row_key[1]}": n for row_key, n in sorted(
                collections.Counter((row["attemptPosition"], row["attemptsInRecord"]) for row in rows).items())},
            "recordRowsIsNull": sum(row["recordRowsIsNull"] for row in rows)}


def shapes_of(capped: list[dict], items: dict) -> list[dict]:
    """문자열 상수 자리를 뺀 본문으로 묶고, 문항에서 오지 않은 값이 달라지는 자리가 있으면 그 값으로 다시 나눈다."""
    groups: dict[str, list[tuple[dict, list[str]]]] = collections.defaultdict(list)
    for row in capped:
        literals = STRING_LITERAL.findall(row["text"])
        skeleton = " ".join(STRING_LITERAL.sub("\x00", row["text"]).split())
        groups[skeleton].append((row, literals))
    shapes = []
    for skeleton, members in groups.items():
        slots = len(members[0][1])
        varying = [slot for slot in range(slots) if len({literals[slot] for _, literals in members}) > 1]

        def from_item(row: dict, literal: str) -> bool:
            item = items[row["id"]]
            sources = [graph_key(item["anchor"]), item["anchor"], item["question"]]
            inner = literal[1:-1].replace("''", "'").strip("%")
            if not inner:
                return False
            return any(inner.lower() in source.lower() for source in sources) or (
                len(alnum(inner)) >= 2 and any(alnum(inner) in alnum(source) for source in sources))

        item_slots = [slot for slot in varying if all(from_item(row, literals[slot]) for row, literals in members)]
        other_slots = [slot for slot in varying if slot not in item_slots]
        split: dict[tuple, list[tuple[dict, list[str]]]] = collections.defaultdict(list)
        for row, literals in members:
            split[tuple(literals[slot] for slot in other_slots)].append((row, literals))
        for part in split.values():
            first_literals = part[0][1]
            pieces = skeleton.split("\x00")
            masked = pieces[0]
            for slot in range(slots):
                masked += (f"'<item value {item_slots.index(slot) + 1}>'" if slot in item_slots
                           else first_literals[slot]) + pieces[slot + 1]
            shapes.append({
                "members": [row for row, _ in part],
                "maskedText": masked,
                "stringLiteralSlots": slots,
                "itemValueSlots": [{"slot": slot + 1, "label": f"<item value {index + 1}>",
                                    "distinctValues": len({literals[slot] for _, literals in part}),
                                    "examples": sorted({literals[slot] for _, literals in part})[:3]}
                                   for index, slot in enumerate(item_slots)],
                "splitOnNonItemLiterals": [{"slot": slot + 1, "value": first_literals[slot]} for slot in other_slots],
            })
    shapes.sort(key=lambda shape: (shape["members"][0]["run"], shape["members"][0]["wg"],
                                   shape["members"][0]["family"], shape["maskedText"]))
    return shapes


def explain_sql(db: sqlite3.Connection, sql: str, parameters: dict | None = None) -> dict:
    """`EXPLAIN QUERY PLAN` 만 받는다. 질의 본문은 실행하지 않는다."""
    deadline = time.time() + 30
    db.set_progress_handler(lambda: 1 if time.time() > deadline else 0, 100000)
    try:
        rows = db.execute("EXPLAIN QUERY PLAN " + sql, parameters or {}).fetchall()
    except Exception as error:
        return {"error": str(error)[:300]}
    finally:
        db.set_progress_handler(None, 0)
    return plan_from_rows([(node, parent, detail) for node, parent, _, detail in rows])


def plan_from_rows(rows: list) -> dict:
    depth: dict[int, int] = {0: -1}
    steps = []
    for node, parent, detail in rows:
        depth[node] = depth.get(parent, -1) + 1
        steps.append({"id": node, "parent": parent, "depth": depth[node], "detail": detail})
    return {"steps": steps, "tree": ["  " * step["depth"] + step["detail"] for step in steps]}


# 다른 인터프리터의 SQLite 라이브러리로 같은 계획만 받는 프로그램. 표준 입력으로 받은 질의마다 `EXPLAIN QUERY PLAN` 을 돌린다.
SECOND_LIBRARY_PROGRAM = r"""
import json, sqlite3, sys, time
tasks = json.load(sys.stdin)
out = {"python": sys.version.split()[0], "sqliteLibrary": sqlite3.sqlite_version, "plans": []}
connections = {}
for task in tasks:
    if task["db"] not in connections:
        connections[task["db"]] = sqlite3.connect("file:" + task["db"] + "?mode=ro", uri=True)
    db = connections[task["db"]]
    deadline = time.time() + 30
    db.set_progress_handler(lambda: 1 if time.time() > deadline else 0, 100000)
    try:
        rows = db.execute("EXPLAIN QUERY PLAN " + task["sql"], task["parameters"]).fetchall()
        out["plans"].append({"rows": [[row[0], row[1], row[3]] for row in rows]})
    except Exception as error:
        out["plans"].append({"error": str(error)[:300]})
    finally:
        db.set_progress_handler(None, 0)
json.dump(out, sys.stdout)
"""


def second_library_plans(interpreter: str, tasks: list[dict]) -> dict:
    done = subprocess.run([interpreter, "-B", "-c", SECOND_LIBRARY_PROGRAM], input=json.dumps(tasks),
                          capture_output=True, text=True, timeout=300)
    if done.returncode != 0:
        return {"error": done.stderr.strip()[-300:]}
    answer = json.loads(done.stdout)
    answer["plans"] = [plan if "error" in plan else plan_from_rows(plan["rows"]) for plan in answer["plans"]]
    return answer


def names_in(sql: str, base_tables: set[str]) -> tuple[dict[str, list[str]], list[str]]:
    """본문에서 별칭이 가리키는 표 이름과 CTE 이름을 얻는다. 한 별칭이 범위마다 다른 표를 가리키면 모두 적는다."""
    text = STRING_LITERAL.sub("''", sql)
    ctes = sorted({name for name in CTE_NAME.findall(text) if name.lower() not in base_tables})
    aliases: dict[str, set[str]] = collections.defaultdict(set)
    for table, alias in TABLE_ALIAS.findall(text):
        if alias and alias.lower() not in SQL_WORDS:
            aliases[alias].add(table)
        else:
            aliases[table].add(table)
    return {alias: sorted(tables) for alias, tables in aliases.items()}, ctes


def plan_features(plan: dict, sql: str, table_rows: dict[str, int]) -> dict:
    """계획의 단계 문장에서 읽히는 사실만 센다. 풀 스캔은 조인 블록 안에서 몇 번째 루프인지도 적는다."""
    if "error" in plan:
        return {"error": plan["error"]}
    aliases, ctes = names_in(sql, set(table_rows))
    loops: dict[int, int] = collections.Counter()
    scans, searches, automatic, indexes = [], 0, 0, collections.Counter()
    counts: collections.Counter[str] = collections.Counter()
    named = {"MATERIALIZE": [], "CO-ROUTINE": []}
    for step in plan["steps"]:
        detail = step["detail"]
        access = re.match(r"(SCAN|SEARCH) (\S+)(?: USING (.*))?", detail)
        if access:
            loops[step["parent"]] += 1
            kind, name, using = access.groups()
            using = using or ""
            index = re.match(r"(?:COVERING )?INDEX (\S+)", using)
            if "AUTOMATIC" in using:
                automatic += 1
            elif index:
                indexes[index.group(1)] += 1
            elif "PRIMARY KEY" in using:
                indexes["rowid"] += 1
            if kind == "SEARCH":
                searches += 1
                continue
            tables = aliases.get(name, [name])
            scans.append({
                "name": name,
                "refersTo": [{"table": table, "rows": table_rows[table]} if table in table_rows
                             else {"derived": table} for table in tables],
                "using": using or None, "loopInBlock": loops[step["parent"]], "depth": step["depth"]})
            continue
        for label in named:
            if detail.startswith(label + " "):
                named[label].append(detail[len(label) + 1:])
        for label, needle in (("tempBtreeSteps", "TEMP B-TREE"), ("multiIndexOr", "MULTI-INDEX OR"),
                              ("correlatedSubqueries", "CORRELATED"), ("listSubqueries", "LIST SUBQUERY"),
                              ("scalarSubqueries", "SCALAR SUBQUERY"), ("bloomFilters", "BLOOM FILTER"),
                              ("recursiveSteps", "RECURSIVE STEP"), ("compoundQueries", "COMPOUND QUERY")):
            if needle in detail:
                counts[label] += 1
    base_scans = [scan for scan in scans if any("table" in target for target in scan["refersTo"])]
    return {
        "topLevelLoopOrder": [step["detail"] for step in plan["steps"]
                              if step["parent"] == 0 and re.match(r"(SCAN|SEARCH) ", step["detail"])],
        "steps": len(plan["steps"]), "searchSteps": searches, "fullScanSteps": len(scans),
        "fullScanStepsNotFirstLoopOfBlock": sum(scan["loopInBlock"] > 1 for scan in scans),
        "fullScansOverBaseTables": len(base_scans), "fullScans": scans,
        "schemaIndexUse": dict(sorted(indexes.items())), "automaticIndexSteps": automatic,
        "materialized": named["MATERIALIZE"], "coRoutines": named["CO-ROUTINE"],
        "cteNamesInText": ctes,
        **{label: counts[label] for label in ("tempBtreeSteps", "multiIndexOr", "correlatedSubqueries",
                                                "listSubqueries", "scalarSubqueries", "bloomFilters",
                                                "recursiveSteps", "compoundQueries")},
    }


def text_features(sql: str, base_tables: set[str]) -> dict:
    text = STRING_LITERAL.sub("''", sql)
    mentioned = sorted(table for table in base_tables if re.search(rf"\b{re.escape(table)}\b", text, re.IGNORECASE))
    return {"characters": len(sql), "stringLiterals": len(STRING_LITERAL.findall(sql)),
            "baseTablesReferenced": mentioned,
            "counts": {label: len(re.findall(pattern, text, re.IGNORECASE)) for label, pattern in TEXT_COUNTS.items()}}


def differences(capped: dict, reference: dict, capped_text: dict, reference_text: dict) -> list[str]:
    """두 계획과 두 본문에서 센 값만으로 차이를 문장으로 적는다."""
    if "error" in capped or "error" in reference:
        return ["plan unavailable for at least one side; see the stored error"]

    def scan_names(features: dict) -> str:
        parts = []
        for scan in features["fullScans"]:
            targets = "/".join(f"{target['table']} ({target['rows']} rows)" if "table" in target
                               else f"{target['derived']} (derived)" for target in scan["refersTo"])
            parts.append(f"{scan['name']}={targets}, loop {scan['loopInBlock']} of its block")
        return "; ".join(parts) if parts else "none"

    functions = ("lower(", "upper(", "replace(", "trim(", "coalesce(", "substr(", "instr(")
    lines = [
        f"top-level join, loops from outermost to innermost: capped {capped['topLevelLoopOrder']}; "
        f"reference {reference['topLevelLoopOrder']}",
        f"plan steps: capped {capped['steps']}, reference {reference['steps']}",
        f"full-scan steps: capped {capped['fullScanSteps']} "
        f"({capped['fullScanStepsNotFirstLoopOfBlock']} of them not the first loop of their join block), "
        f"reference {reference['fullScanSteps']} ({reference['fullScanStepsNotFirstLoopOfBlock']} not first)",
        f"capped full scans: {scan_names(capped)}",
        f"reference full scans: {scan_names(reference)}",
        f"index-search steps: capped {capped['searchSteps']} of which {capped['automaticIndexSteps']} use an "
        f"automatic index built at run time, reference {reference['searchSteps']} of which "
        f"{reference['automaticIndexSteps']} automatic",
        f"schema indexes named in the plan: capped {capped['schemaIndexUse'] or 'none'}, "
        f"reference {reference['schemaIndexUse'] or 'none'}",
        f"materialized subqueries: capped {capped['materialized'] or 'none'}, "
        f"reference {reference['materialized'] or 'none'}; co-routines: capped {capped['coRoutines'] or 'none'}, "
        f"reference {reference['coRoutines'] or 'none'}",
        f"correlated subquery steps: capped {capped['correlatedSubqueries']}, "
        f"reference {reference['correlatedSubqueries']}; temp b-tree steps: capped {capped['tempBtreeSteps']}, "
        f"reference {reference['tempBtreeSteps']}; multi-index OR steps: capped {capped['multiIndexOr']}, "
        f"reference {reference['multiIndexOr']}",
        "function calls in the text (" + ", ".join(functions) + "): capped "
        + str({name: capped_text["counts"][name] for name in functions if capped_text["counts"][name]}) + ", reference "
        + str({name: reference_text["counts"][name] for name in functions if reference_text["counts"][name]}),
        f"LIKE / EXISTS / UNION / OR / JOIN counts: capped "
        f"{[capped_text['counts'][name] for name in ('LIKE', 'EXISTS', 'UNION', 'OR', 'JOIN')]}, reference "
        f"{[reference_text['counts'][name] for name in ('LIKE', 'EXISTS', 'UNION', 'OR', 'JOIN')]}",
        f"base tables referenced: capped {capped_text['baseTablesReferenced']}, "
        f"reference {reference_text['baseTablesReferenced']}",
        f"text length in characters: capped {capped_text['characters']}, reference {reference_text['characters']}",
    ]
    return lines


def diagnose_sql(shapes: list[dict], items: dict, second_python: str | None) -> tuple[list[dict], dict, dict]:
    connections, context, out = {}, {}, []
    second = {"interpreter": second_python, "used": False}
    if second_python:
        tasks = []
        for shape in shapes:
            for row in shape["members"]:
                item = items[row["id"]]
                db_path = str(SQLITE_DIR / f"{row['wg']}.sqlite")
                tasks.append({"db": db_path, "sql": row["text"], "parameters": {}})
                tasks.append({"db": db_path, "sql": SQL[item["family"]].format(**VARIANTS[VARIANT]),
                              "parameters": {"anchor": item["anchor"]}})
        answer = second_library_plans(second_python, tasks)
        second = {"interpreter": second_python, "used": "error" not in answer,
                  **{key: answer[key] for key in ("python", "sqliteLibrary", "error") if key in answer}}
        other_plans = iter(answer.get("plans", []))
    for shape in shapes:
        members = shape["members"]
        wgs = sorted({row["wg"] for row in members})
        plans_capped, plans_reference = collections.Counter(), collections.Counter()
        other_seen = {"capped": collections.Counter(), "reference": collections.Counter()}
        first = {}
        for row in members:
            wg = row["wg"]
            if wg not in connections:
                path = SQLITE_DIR / f"{wg}.sqlite"
                db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
                tables = [name for (name,) in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
                connections[wg] = db
                context[wg] = {
                    "file": str(path), "bytes": path.stat().st_size,
                    "tableRows": {name: db.execute(f'SELECT count(*) FROM "{name}"').fetchone()[0] for name in tables},
                    "hasSqliteStat1": bool(db.execute(
                        "SELECT count(*) FROM sqlite_master WHERE name='sqlite_stat1'").fetchone()[0]),
                    "indexes": [name for (name,) in db.execute(
                        "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name")]}
            db = connections[wg]
            item = items[row["id"]]
            capped_plan = explain_sql(db, row["text"])
            reference_sql = SQL[item["family"]].format(**VARIANTS[VARIANT])
            reference_plan = explain_sql(db, reference_sql, {"anchor": item["anchor"]})
            plans_capped[json.dumps(capped_plan.get("tree", capped_plan), ensure_ascii=False)] += 1
            plans_reference[json.dumps(reference_plan.get("tree", reference_plan), ensure_ascii=False)] += 1
            if second["used"]:
                other_capped, other_reference = next(other_plans), next(other_plans)
                other_seen["capped"][json.dumps(other_capped.get("tree", other_capped), ensure_ascii=False)] += 1
                other_seen["reference"][json.dumps(other_reference.get("tree", other_reference),
                                                   ensure_ascii=False)] += 1
            if not first:
                first = {"row": row, "cappedPlan": capped_plan, "referenceSql": reference_sql,
                         "referencePlan": reference_plan, "anchor": item["anchor"]}
                if second["used"]:
                    first["other"] = (other_capped, other_reference)
        row = first["row"]
        table_rows = context[row["wg"]]["tableRows"]
        capped_features = plan_features(first["cappedPlan"], row["text"], table_rows)
        reference_features = plan_features(first["referencePlan"], first["referenceSql"], table_rows)
        capped_text = text_features(row["text"], set(table_rows))
        reference_text = text_features(first["referenceSql"], set(table_rows))
        other = None
        if second["used"]:
            other_capped, other_reference = first["other"]
            other_features = {"capped": plan_features(other_capped, row["text"], table_rows),
                              "reference": plan_features(other_reference, first["referenceSql"], table_rows)}
            other = {
                "sqliteLibrary": second["sqliteLibrary"],
                "cappedPlanSameAsUnderTheMeasuringLibrary":
                    other_capped.get("tree") == first["cappedPlan"].get("tree"),
                "referencePlanSameAsUnderTheMeasuringLibrary":
                    other_reference.get("tree") == first["referencePlan"].get("tree"),
                "distinctCappedPlansAcrossMembers": len(other_seen["capped"]),
                "distinctReferencePlansAcrossMembers": len(other_seen["reference"]),
                "cappedPlan": other_capped.get("tree", other_capped),
                "referencePlan": other_reference.get("tree", other_reference),
                "planFeatures": other_features,
                "differences": differences(other_features["capped"], other_features["reference"],
                                           capped_text, reference_text)}
        out.append({
            "n": len(members),
            "runs": sorted({member["run"] for member in members}), "wgs": wgs,
            "families": sorted({member["family"] for member in members}),
            "items": [{"id": member["id"], "run": member["run"], "wg": member["wg"], "file": member["file"],
                       "recordSeconds": member["recordSeconds"],
                       "attempt": f"{member['attemptPosition']} of {member['attemptsInRecord']}",
                       "characters": len(member["text"])} for member in members],
            "maskedText": shape["maskedText"], "stringLiteralSlots": shape["stringLiteralSlots"],
            "itemValueSlots": shape["itemValueSlots"], "splitOnNonItemLiterals": shape["splitOnNonItemLiterals"],
            "distinctCappedPlansAcrossMembers": len(plans_capped),
            "distinctReferencePlansAcrossMembers": len(plans_reference),
            "planShownFor": {"id": row["id"], "wg": row["wg"], "anchor": first["anchor"]},
            "cappedPlan": first["cappedPlan"].get("tree", first["cappedPlan"]),
            "referenceSql": " ".join(first["referenceSql"].split()),
            "referencePlan": first["referencePlan"].get("tree", first["referencePlan"]),
            "planFeatures": {"capped": capped_features, "reference": reference_features},
            "textFeatures": {"capped": capped_text, "reference": reference_text},
            "differences": differences(capped_features, reference_features, capped_text, reference_text),
            "underSecondLibrary": other,
        })
    for db in connections.values():
        db.close()
    return out, context, second


def diagnose_cypher(capped: list[dict]) -> list[dict]:
    """상한에 걸린 Cypher 가 있을 때만 읽기 세션에서 `EXPLAIN` 을 받는다. 본문이 같은 것끼리 묶는다."""
    if not capped:
        return []
    import neo4j
    from neo4j import GraphDatabase

    from common.credentials import neo4j_auth

    groups: dict[str, list[dict]] = collections.defaultdict(list)
    for row in capped:
        groups[" ".join(STRING_LITERAL.sub("'?'", row["text"]).split())].append(row)

    def operators(plan: dict, depth: int = 0) -> list[str]:
        lines = ["  " * depth + plan["operatorType"]]
        for child in plan.get("children", []):
            lines.extend(operators(child, depth + 1))
        return lines

    out = []
    for masked, members in groups.items():
        row = members[0]
        try:
            with GraphDatabase.driver(f"bolt://localhost:{BOLT_PORT[row['wg']]}", auth=neo4j_auth()) as driver, \
                    driver.session(default_access_mode=neo4j.READ_ACCESS) as session:
                plan = operators(session.run("EXPLAIN " + row["text"]).consume().plan)
        except Exception as error:
            plan = {"error": str(error)[:300]}
        out.append({"n": len(members), "runs": sorted({m["run"] for m in members}),
                    "wgs": sorted({m["wg"] for m in members}), "families": sorted({m["family"] for m in members}),
                    "items": [m["id"] for m in members], "maskedText": masked, "planShownFor": row["id"],
                    "explainOperators": plan})
    return out


def other_record_files(capped_sql: list[dict]) -> dict:
    """본 실행 100 파일 밖의 기록. 같은 폴더의 다른 응답 파일은 본 실행의 걸린 질의와 본문을 맞대 본다."""
    by_key = {(row["language"], row["wg"], row["run"], row["id"]): row["text"] for row in capped_sql}
    siblings = []
    for language, (directory, pattern) in MAIN_FILES.items():
        for path in sorted(directory.glob("*.jsonl")):
            if pattern.match(path.name) or f"text2{language}" not in path.name:
                continue
            label = re.match(r"^(RAN[1-5])_.*?_run([A-J])", path.name)
            wg, run = label.groups() if label else (None, None)
            counts: collections.Counter[str] = collections.Counter()
            finished = []
            records = 0
            for record in records_of(path):
                records += 1
                attempts = parsed(record.get("attempts")) or []
                main_text = by_key.get((language, wg, run, record.get("id")))
                for position, attempt in enumerate(attempts):
                    text, error = attempt.get(language, ""), attempt.get("error")
                    same = main_text is not None and text == main_text
                    if error is not None and CAP_ERROR.search(error):
                        counts["cappedAttempts"] += 1
                        counts["cappedAttemptsWithTextIdenticalToMainRunCappedQuery" if same
                               else "cappedAttemptsWithOtherText"] += 1
                    elif same and error is None:
                        counts["mainRunCappedTextFinishedHere"] += 1
                        finished.append({"id": record["id"], "family": record.get("family"),
                                         "recordSeconds": record.get("seconds"),
                                         "attempt": f"{position + 1} of {len(attempts)}",
                                         "rowCount": attempt.get("rowCount")})
                if main_text is not None:
                    counts["recordsForMainRunCappedItems"] += 1
                    last = attempts[-1] if attempts else {}
                    counts["thoseWhoseLastAttemptHasNoError" if last.get("error") is None
                           else "thoseWhoseLastAttemptHasError"] += 1
                    if last.get(language, "") != main_text:
                        counts["thoseWhoseLastAttemptTextDiffersFromMainRun"] += 1
            siblings.append({"file": str(path.relative_to(LOGS)), "language": language, "records": records,
                             **dict(sorted(counts.items())), "mainRunCappedTextFinishedHereItems": finished})

    def errors_in(node):
        if isinstance(node, dict):
            error = node.get("error")
            if isinstance(error, str) and CAP_ERROR.search(error) and ("sql" in node or "cypher" in node):
                yield node
            for value in node.values():
                yield from errors_in(value)
        elif isinstance(node, list):
            for value in node:
                yield from errors_in(value)

    elsewhere = []
    main_paths = {path for language, (directory, pattern) in MAIN_FILES.items()
                  for path in directory.glob("*.jsonl") if pattern.match(path.name)}
    scanned = 0
    for path in sorted(RECORD_ROOT.rglob("*.jsonl")):
        if path in main_paths:
            continue
        scanned += 1
        found = 0
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not CAP_ERROR.search(line):
                    continue
                try:
                    found += sum(1 for _ in errors_in(json.loads(line)))
                except json.JSONDecodeError:
                    continue
        if found:
            elsewhere.append({"file": str(path.relative_to(LOGS)), "queriesWithCapError": found})
    return {"otherResponseFilesInTheSameFolders": siblings,
            "anyJsonlUnderChainEvalOutsideTheMainFiles": {"filesScanned": scanned, "filesWithCapError": elsewhere}}


def long_cap_rerun(sql_shapes: list[dict]) -> dict:
    """이미 있는 600초 재실행 기록을 읽어 꼴마다 맞대 적는다. 이 스크립트가 잰 값이 아니다."""
    if not LONG_CAP_RERUN.exists():
        return {"file": str(LONG_CAP_RERUN), "present": False}
    report = json.loads(LONG_CAP_RERUN.read_text())
    by_key = {(row["run"], row["wg"], row["id"]): row for row in report["items"]}
    per_shape = []
    for index, shape in enumerate(sql_shapes):
        rows = [by_key.get(("run" + member["run"], member["wg"], member["id"])) for member in shape["items"]]
        rows = [row for row in rows if row is not None]
        done = sorted(row["seconds"] for row in rows if row["error"] is None)
        per_shape.append({"shape": index + 1, "itemsFoundInRecord": len(rows), "finishedWithinLimit": len(done),
                          "exactAmongFinished": sum(row["exact"] for row in rows if row["error"] is None),
                          "finishedSecondsMinMedianMax": [done[0], statistics.median(done), done[-1]]
                          if done else None,
                          "stillInterrupted": sum(row["error"] is not None for row in rows)})
    return {"file": str(LONG_CAP_RERUN), "present": True, "note": "read from an existing record, not measured here",
            "limitSeconds": report.get("limitSeconds"), "rerun": report.get("rerun"),
            "finishedWithinLimit": report.get("finishedWithinLimit"), "exact": report.get("exact"),
            "perShape": per_shape}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--second-python", help="다른 SQLite 라이브러리를 쓰는 인터프리터. 주면 같은 계획을 한 번 더 받는다")
    args = parser.parse_args()
    memory = available_gib()
    if memory < MIN_AVAILABLE_GIB:
        raise SystemExit(f"available memory {memory:.2f} GiB is under {MIN_AVAILABLE_GIB} GiB; not started")

    items = {item["id"]: item for path in ITEM_FILES for item in records_of(path)}
    capped_sql, sql_scan = collect_main("sql")
    capped_cypher, cypher_scan = collect_main("cypher")
    capped = capped_sql + capped_cypher
    missing = sorted({row["id"] for row in capped if row["id"] not in items})
    if missing:
        raise SystemExit(f"capped records without an item: {missing[:5]}")

    sql_shapes, sqlite_context, second = diagnose_sql(shapes_of(capped_sql, items), items, args.second_python)
    for index, shape in enumerate(sql_shapes):
        shape_id = {"shape": index + 1}
        sql_shapes[index] = {**shape_id, **shape}
    cypher_shapes = diagnose_cypher(capped_cypher)

    report = {
        "scope": "agent-written queries whose execution hit the 60 s cap or a timeout in the stored response "
                 "records (five working groups, runs A to J, SQL and Cypher); plans only, no capped query executed",
        "method": {
            "capDefinition": "an entry of `attempts` whose `error` matches " + CAP_ERROR.pattern
                             + " (case-insensitive); SQLite reports `interrupted` when the 60 s progress-handler "
                               "deadline fires, Neo4j runs with a 60 s transaction timeout (run_chain_eval.py)",
            "capSeconds": CAP_SECONDS,
            "shapeDefinition": "texts are grouped when they are identical after whitespace normalisation with "
                               "every string literal replaced by a slot; a slot whose value varies inside a group "
                               "must come from the item's anchor or question, otherwise the group is split on it",
            "planOnly": "SQL: EXPLAIN QUERY PLAN on the working group's SQLite file opened with mode=ro; "
                        "Cypher: EXPLAIN in a read-access session; neither executes the query",
            "referenceSql": f"measure_relational_equivalence.SQL[family] with the `{VARIANT}` table names, "
                            "anchor bound as a parameter",
            "loopInBlock": "position of a SCAN or SEARCH step among the SCAN/SEARCH steps that share its parent "
                           "in the EXPLAIN QUERY PLAN tree (1 is the outermost loop of that join block)",
        },
        "context": {
            "measuredAt": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            "python": platform.python_version(), "sqliteLibrary": sqlite3.sqlite_version,
            "sqliteLibraryAtTheOriginalRuns": "not stored in the response records",
            "secondLibrary": second,
            "cpuAffinity": sorted(os.sched_getaffinity(0)), "uptime": command_output(["uptime"]),
            "availableGiB": round(memory, 2), "sqlite": sqlite_context,
        },
        "recordsScanned": {"sql": sql_scan, "cypher": cypher_scan, "items": len(items)},
        "capped": tally(capped),
        "sqlShapes": sql_shapes,
        "cypherShapes": cypher_shapes,
        "existingLongCapRerun": long_cap_rerun(sql_shapes),
        "otherRecordFiles": other_record_files(capped_sql),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({"capped": {key: report["capped"][key] for key in ("n", "byLanguage", "byRunWgFamily")},
                      "sqlShapes": [{"shape": shape["shape"], "n": shape["n"], "families": shape["families"],
                                     "distinctCappedPlans": shape["distinctCappedPlansAcrossMembers"],
                                     "samePlanUnderSecondLibrary": (shape["underSecondLibrary"] or {}).get(
                                         "cappedPlanSameAsUnderTheMeasuringLibrary")}
                                    for shape in sql_shapes],
                      "cypherShapes": len(cypher_shapes)}, ensure_ascii=False)[:1500])


if __name__ == "__main__":
    main()
