#!/usr/bin/env python3
"""헤드룸 분할에서 질의 작성 세션이 틀린 문항을, 미리 고정한 읽기 규칙대로 분류한다 (모델 호출 없음).

읽기 규칙은 `final/next_cycle/headroom/solvers/miss_classification_reading.json` 이다. 틀린 문항은 첫 질의의 결과가
주 규칙(`score_chain_eval.score` 의 정확 행 집합 일치)으로 정답과 다른 채택 문항이다.

단계는 셋이고 차례로 실행한다.

inventory  응답 기록에서 틀린 문항을 모은다. 저장된 응답만으로 정해지는 부류(`execution_deadline` ·
           `execution_error` · `no_query`)를 먼저 적고, 나머지는 질의에서 문항의 기준 식별자를 `{ANCHOR}` 로 바꾼
           틀로 묶는다. 틀마다 본문 파일(`templates/<sha12>.<sql|cypher>`)을 쓴다.
apply      틀마다의 읽기(`--readings`)를 받아 검사하고, 틀린 문항마다 질의를 쓴 그대로와 빠진 조건을 차례로 하나씩
           더한 형태로 실행한다. 두 질의를 모두 저장하고 정답 일치 여부를 적는다.
summarize  계열 · 언어 · 회차마다 부류별 개수를 낸다. 틀린 문항은 정확히 한 부류를 받는다.

읽기 파일은 틀의 sha12 를 키로 하는 JSON 이다.

    {"<sha12>": {"held": {"<조건>": "<그 조건을 나타내는 술어, 틀에 그대로 있는 문자열>"},
                 "lacking": [{"condition": "<조건>", "find": "<틀에 한 번 있는 문자열>", "replace": "<바꿀 문자열>"}]}}

`held` 와 `lacking` 은 합쳐서 그 계열의 조건을 모두 한 번씩 담고, `lacking` 은 읽기 규칙의 조건 차례를 따른다.
`find` 는 직전 단계까지 적용한 질의에 정확히 한 번 있어야 하므로, 한 단계는 질의의 한 자리만 바꾼다.

사용(저장소 루트에서):
    PYTHONPATH=scripts/common:scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark \\
        python3 -B classify_headroom_query_misses.py inventory --runs A B C D E
        python3 -B classify_headroom_query_misses.py apply --readings <json> [--bolt RAN1=bolt://localhost:7687 ...]
        python3 -B classify_headroom_query_misses.py summarize --runs A B C D E
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sqlite3
from pathlib import Path

import analyze_headroom as headroom
from run_chain_eval import solve_text2cypher, solve_text2sql
from score_chain_eval import key, score

ROOT = headroom.ROOT
SOLVERS = f"{headroom.NEXT}/headroom/solvers"
READING = f"{SOLVERS}/miss_classification_reading.json"
RESPONSES = f"{SOLVERS}/responses/query_writers"
OUT = f"{SOLVERS}/miss_classification"
SQLITE = f"{headroom.sens.TRACK}/integration/sqlite_final"
LANGUAGES = {"text2sql": "sql", "text2cypher": "cypher"}
WGS = ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5")
STORED_CLASSES = ("execution_deadline", "execution_error", "no_query")
PLACEHOLDER = "{ANCHOR}"


def load_items() -> dict:
    return headroom.load_items(json.loads((ROOT / headroom.RECORD).read_text(encoding="utf-8")))


def condition_order() -> dict[str, list[str]]:
    """읽기 규칙이 적은 계열별 조건 이름을 차례대로 돌려준다."""
    reading = json.loads((ROOT / READING).read_text(encoding="utf-8"))
    return {family: [entry["name"] for entry in sorted(entries, key=lambda e: e["order"])]
            for family, entries in reading["conditionOrder"].items()}


def anchor_literal(item: dict) -> str:
    """문항의 기준 식별자에서 질의에 쓰이는 부분(`tdoc:R1-…` 의 `R1-…`, `tdoc:crpack/RP-…` 의 `RP-…`)."""
    return item["anchor"].split(":", 1)[-1].rsplit("/", 1)[-1]


def stored_class(record: dict, language: str) -> str | None:
    """저장된 응답만으로 정해지는 부류. 60초 상한에 걸린 SQL 은 SQLite 가 `interrupted` 로 적는다."""
    attempts = record.get("attempts") or []
    if not attempts or not attempts[0].get(LANGUAGES[language]):
        return "no_query"
    error = attempts[0].get("error")
    if error is None:
        return None
    if language == "text2sql":
        return "execution_deadline" if error == "interrupted" else "execution_error"
    lowered = error.lower()
    return "execution_deadline" if ("timeout" in lowered or "timed out" in lowered) else "execution_error"


def response_file(wg: str, language: str, run: str) -> Path:
    return ROOT / RESPONSES / f"{wg}_{language}_run{run}.jsonl"


def inventory(args) -> None:
    items = load_items()
    out = ROOT / OUT
    (out / "templates").mkdir(parents=True, exist_ok=True)
    misses, templates, sessions = [], {}, []
    for run in args.runs:
        for language, field in LANGUAGES.items():
            for wg in WGS:
                path = response_file(wg, language, run)
                records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
                expected = {i for i, item in items.items() if item["wg"] == wg}
                if {r["id"] for r in records} != expected or len(records) != len(expected):
                    headroom.fail(f"{path.name}: 기록이 그 작업반의 채택 문항과 다르다")
                wrong = 0
                for record in records:
                    item = items[record["id"]]
                    if score(item["gold"], record.get("rows"))["exact"]:
                        continue
                    wrong += 1
                    entry = {"id": item["id"], "wg": wg, "family": item["family"], "language": language, "run": run}
                    fixed = stored_class(record, language)
                    if fixed:
                        entry["storedClass"] = fixed
                        entry["error"] = (record.get("attempts") or [{}])[0].get("error")
                    else:
                        query = record["attempts"][0][field]
                        literal = anchor_literal(item)
                        if literal not in query:
                            headroom.fail(f"{item['id']} {language} run{run}: 질의에 기준 식별자 {literal} 가 없다")
                        template = query.replace(literal, PLACEHOLDER)
                        sha = hashlib.sha256(template.encode()).hexdigest()[:12]
                        known = templates.setdefault(sha, {"language": language, "family": item["family"],
                                                           "text": template, "members": []})
                        if (known["language"], known["family"]) != (language, item["family"]):
                            headroom.fail(f"틀 {sha} 가 두 계열 또는 두 언어에 걸친다")
                        known["members"].append({"id": item["id"], "wg": wg, "run": run})
                        entry["template"] = sha
                    misses.append(entry)
                sessions.append({"run": run, "language": language, "wg": wg, "records": len(records), "misses": wrong})
    for sha, entry in templates.items():
        (out / "templates" / f"{sha}.{LANGUAGES[entry['language']]}").write_text(entry["text"] + "\n", encoding="utf-8")
    record = {
        "reading": {"path": READING, "sha256": hashlib.sha256((ROOT / READING).read_bytes()).hexdigest()},
        "runs": args.runs, "sessions": sessions, "misses": misses,
        "templates": {sha: {"language": e["language"], "family": e["family"], "characters": len(e["text"]),
                            "members": len(e["members"]),
                            "sessions": sorted({f"{m['wg']} run{m['run']}" for m in e["members"]})}
                      for sha, e in sorted(templates.items())},
    }
    (out / "inventory.json").write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    by = collections.Counter((m["language"], m["run"], m.get("storedClass", "to_read")) for m in misses)
    for (language, run, kind), count in sorted(by.items()):
        print(f"{language} run{run} {kind} {count}")
    print(f"misses {len(misses)} templates {len(templates)}")


def checked_readings(path: Path, inventory_record: dict, order: dict[str, list[str]]) -> dict:
    """읽기 파일이 모든 틀을 다루고, 조건을 빠짐없이 한 번씩 담고, 인용이 틀에 실제로 있는지 본다."""
    readings = json.loads(path.read_text(encoding="utf-8"))
    for sha, meta in inventory_record["templates"].items():
        if sha not in readings:
            headroom.fail(f"읽기에 틀 {sha} 가 없다")
        text = (ROOT / OUT / "templates" / f"{sha}.{LANGUAGES[meta['language']]}").read_text(encoding="utf-8")[:-1]
        reading, names = readings[sha], order[meta["family"]]
        lacking = [step["condition"] for step in reading["lacking"]]
        if sorted(lacking + list(reading["held"])) != sorted(names):
            headroom.fail(f"틀 {sha}: held 와 lacking 이 계열의 조건을 한 번씩 담지 않는다")
        if lacking != [name for name in names if name in lacking]:
            headroom.fail(f"틀 {sha}: lacking 이 조건 차례와 다르다")
        for name, quote in reading["held"].items():
            if not quote or quote not in text:
                headroom.fail(f"틀 {sha}: held {name} 의 인용이 틀에 없다")
        current = text
        for step in reading["lacking"]:
            if current.count(step["find"]) != 1:
                headroom.fail(f"틀 {sha}: {step['condition']} 의 find 가 질의에 {current.count(step['find'])}번 있다")
            current = current.replace(step["find"], step["replace"])
    return readings


def executed(language: str, item: dict, query: str, db, session) -> dict:
    if language == "text2sql":
        result = solve_text2sql(item, db, [query])
    else:
        result = solve_text2cypher(item, "", session, "", 0, 0, [query])
    attempt = result["attempts"][0]
    rows = result["rows"]
    out = {"query": query, "rowCount": attempt.get("rowCount"), "error": attempt.get("error"),
           "exact": bool(score(item["gold"], rows)["exact"])}
    if rows is not None:
        gold, given = {key(row) for row in item["gold"]}, {key(row) for row in rows}
        out["goldOnly"], out["responseOnly"] = len(gold - given), len(given - gold)
    return out


def apply(args) -> None:
    items = load_items()
    order = condition_order()
    inventory_record = json.loads((ROOT / OUT / "inventory.json").read_text(encoding="utf-8"))
    readings = checked_readings(args.readings, inventory_record, order)
    bolt = dict(pair.split("=", 1) for pair in args.bolt)
    drivers, connections = {}, {}
    out_path = ROOT / OUT / "checks.jsonl"
    with out_path.open("w", encoding="utf-8") as out:
        for miss in inventory_record["misses"]:
            if "storedClass" in miss:
                continue
            item, language, wg = items[miss["id"]], miss["language"], miss["wg"]
            db = session = None
            if language == "text2sql":
                if wg not in connections:
                    connections[wg] = sqlite3.connect(f"file:{ROOT / SQLITE / (wg + '.sqlite')}?mode=ro", uri=True)
                db = connections[wg]
            else:
                if wg not in drivers:
                    from neo4j import GraphDatabase
                    from common.credentials import neo4j_auth
                    if wg not in bolt:
                        headroom.fail(f"--bolt {wg}=<url> 이 필요하다")
                    drivers[wg] = GraphDatabase.driver(bolt[wg], auth=neo4j_auth())
                session = drivers[wg].session()
            reading = readings[miss["template"]]
            suffix = LANGUAGES[language]
            text = (ROOT / OUT / "templates" / f"{miss['template']}.{suffix}").read_text(encoding="utf-8")[:-1]
            literal = anchor_literal(item)
            written = text.replace(PLACEHOLDER, literal)
            record = {**miss, "class": reading["lacking"][0]["condition"] if reading["lacking"] else "no_listed_condition",
                      "asWritten": executed(language, item, written, db, session), "withConditions": []}
            if record["asWritten"]["exact"]:
                headroom.fail(f"{miss['id']} {language} run{miss['run']}: 쓴 그대로 다시 실행하니 정답과 같다")
            current = text
            for step in reading["lacking"]:
                current = current.replace(step["find"], step["replace"])
                result = executed(language, item, current.replace(PLACEHOLDER, literal), db, session)
                record["withConditions"].append({"added": step["condition"], **result})
                if result["exact"]:
                    break
            if session is not None:
                session.close()
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()
    for driver in drivers.values():
        driver.close()
    print(f"checks written: {headroom.shown(out_path)}")


def summarize(args) -> None:
    items = load_items()
    order = condition_order()
    inventory_record = json.loads((ROOT / OUT / "inventory.json").read_text(encoding="utf-8"))
    if inventory_record["runs"] != args.runs:
        headroom.fail(f"목록의 회차 {inventory_record['runs']} 가 요청한 회차와 다르다")
    checks = {}
    path = ROOT / OUT / "checks.jsonl"
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                checks[(record["id"], record["language"], record["run"])] = record
    families = sorted(order)
    table = collections.defaultdict(collections.Counter)
    recovered = collections.defaultdict(collections.Counter)
    for miss in inventory_record["misses"]:
        spot = (miss["language"], miss["run"], miss["family"])
        if "storedClass" in miss:
            table[spot][miss["storedClass"]] += 1
            continue
        check = checks.get((miss["id"], miss["language"], miss["run"]))
        if check is None:
            headroom.fail(f"{miss['id']} {miss['language']} run{miss['run']}: 실행 기록이 없다")
        table[spot][check["class"]] += 1
        steps = check["withConditions"]
        if steps and steps[0]["exact"]:
            recovered[spot]["goldWithFirstCondition"] += 1
        elif steps and steps[-1]["exact"]:
            recovered[spot]["goldWithLaterConditions"] += 1
        else:
            recovered[spot]["notGold"] += 1
    sessions = collections.Counter()
    for session in inventory_record["sessions"]:
        sessions[(session["language"], session["run"])] += session["misses"]
    rows = []
    for language in LANGUAGES:
        for run in args.runs:
            for family in families:
                spot = (language, run, family)
                n = sum(1 for item in items.values() if item["family"] == family)
                wrong = sum(table[spot].values())
                rows.append({"language": language, "run": run, "family": family, "items": n, "exact": n - wrong,
                             "misses": wrong, "classes": dict(sorted(table[spot].items())),
                             "afterCheck": dict(sorted(recovered[spot].items()))})
            total = sum(row["misses"] for row in rows if (row["language"], row["run"]) == (language, run))
            if total != sessions[(language, run)]:
                headroom.fail(f"{language} run{run}: 부류의 합 {total} 이 틀린 문항 수 {sessions[(language, run)]} 와 다르다")
    record = {"reading": inventory_record["reading"], "runs": args.runs, "byFamilyLanguageRun": rows,
              "inventory": f"{OUT}/inventory.json", "checks": f"{OUT}/checks.jsonl" if checks else None}
    (ROOT / OUT / "summary.json").write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for row in rows:
        if row["misses"]:
            print(row["language"], f"run{row['run']}", row["family"], f"{row['exact']}/{row['items']}",
                  row["classes"], row["afterCheck"])
    print("misses", sum(row["misses"] for row in rows))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="stage", required=True)
    first = sub.add_parser("inventory")
    first.add_argument("--runs", nargs="+", required=True)
    second = sub.add_parser("apply")
    second.add_argument("--readings", type=Path, required=True)
    second.add_argument("--bolt", nargs="*", default=[], metavar="WG=URL")
    third = sub.add_parser("summarize")
    third.add_argument("--runs", nargs="+", required=True)
    args = parser.parse_args()
    {"inventory": inventory, "apply": apply, "summarize": summarize}[args.stage](args)


if __name__ == "__main__":
    main()
