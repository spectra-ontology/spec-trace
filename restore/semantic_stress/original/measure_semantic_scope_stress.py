"""저장 SQL의 출처 상태·문서 범위 집행을 합성 distractor로 검사한다.

원본 SQLite를 읽기 전용으로 열어 메모리에 복사한다. 각 문항에서 금표준에
기여하는 문서에 상태만, 범위만, 둘 다 부적격인 합성 처분을 별도로 추가한다.
상태만 부적격인 pending/whole_target는 생성기 계약 밖의 관계형 guard 진단이다.
부분 범위 source_verified/subdocument와 pending/undetermined는 생성기 유형을 따른다.
완전한 참조 SQL은 원래 gold를 유지해야 하고, 해당 조건을 제거한 참조 SQL은
합성 행을 반환해야 한다. 실제 기록의 정확도나 역사적 사실을 다시 추정하지 않는다.

각 (WG, family)에서 SHA-256(seed|itemId)가 가장 작은 문항 하나를 고정한다.
원실험과 같은 60초 cap으로 baseline이 gold와 일치한 저장 SQL만 stress와 비교한다.
Python 표준 라이브러리만 쓰며 /usr/bin/python3의 SQLite 3.37.2로 실행한다.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from measure_relational_equivalence import SQL, VARIANTS

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
TRACK = Path("logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark")
SEED = "semantic-scope-contract-stress"
CAP_SECONDS = 60
SCENARIOS = {
    "status_only": ("pending", "whole_target"),
    "scope_only": ("source_verified", "subdocument"),
    "combined": ("pending", "undetermined"),
}
SCENARIO_VALIDITY = {
    "status_only": "out-of-builder-contract relational guard diagnostic: ambiguous/pending/whole_target",
    "scope_only": "builder-compatible tuple type: partially_agreed/source_verified/subdocument; synthetic evidence is not source verification",
    "combined": "builder-compatible tuple type: ambiguous/pending/undetermined",
}
PREDICATES = {
    "status_only": "d.evidence_status = 'source_verified'",
    "scope_only": "d.scope = 'whole_target'",
    "combined": "d.evidence_status = 'source_verified' AND d.scope = 'whole_target'",
}
DISPOSITION_FAMILIES = set(SQL) - {"pack_lookup", "pack_lookup_empty"}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical(item: dict, rows) -> set | None:
    if rows is None:
        return None
    def cell(value) -> str:
        s = "" if value is None else str(value).strip().lower()
        s = re.sub(r"(#\d+)-e-b(?:is)?(?![a-z0-9])", r"\1bis-e", s)
        return re.sub(r"(#\d+)-?b(?:is)?(?![a-z0-9])", r"\1bis", s)
    return {tuple(cell(v) for v in row) for row in rows}


def execute(db: sqlite3.Connection, item: dict, sql: str, params=None) -> dict:
    started = time.monotonic()
    deadline = started + CAP_SECONDS
    db.set_progress_handler(lambda: int(time.monotonic() > deadline), 100000)
    try:
        rows = db.execute(sql, params or {}).fetchall()
        wanted, got = canonical(item, item["gold"]), canonical(item, rows)
        return {"exact": got == wanted, "error": None, "rowCount": len(rows),
                "extraRowCount": len(got - wanted), "missingRowCount": len(wanted - got),
                "timeout": False, "seconds": round(time.monotonic() - started, 6)}
    except sqlite3.Error as error:
        return {"exact": False, "error": str(error), "rowCount": None,
                "timeout": str(error) == "interrupted" and time.monotonic() >= deadline,
                "seconds": round(time.monotonic() - started, 6)}
    finally:
        db.set_progress_handler(None, 0)


def selected_items() -> list[dict]:
    groups = collections.defaultdict(list)
    for part in ("core", "ran5"):
        path = ROOT / TRACK / f"integration/items_final/gate/{part}/chain_items_admitted.jsonl"
        for line in path.read_text().splitlines():
            item = json.loads(line)
            groups[item["wg"], item["family"]].append(item)
    return [min(rows, key=lambda item: hashlib.sha256(f"{SEED}|{item['id']}".encode()).hexdigest())
            for _, rows in sorted(groups.items())]


def response_paths(wg: str) -> list[tuple[str, Path]]:
    ce = ROOT / TRACK / "chain_eval"
    paths = [(f"opus_sql_run{run}", ce / f"text2sql/{wg}_text2sql_run{run}.jsonl")
             for run in "ABCDEFGHIJ"]
    paths.extend([
        ("codex_sql_schema", ce / f"codex/chain_sql_{wg}_codex.jsonl"),
        ("codex_sql_domains", ce / f"codex_v2/responses/{wg}_sql_dom_codex.jsonl"),
        ("codex_sql_exploration", ce / f"codex_v2/responses/{wg}_sql_exp_codex.jsonl"),
    ])
    return paths


def contributing_dispositions(db: sqlite3.Connection, item: dict) -> list[tuple]:
    """문항의 gold에 참여한 각 문서에서 원래 적격 처분 하나를 고른다."""
    if item["family"] not in DISPOSITION_FAMILIES:
        targets = [item["anchor"]]
    elif item["family"] in ("full_chain", "disposition_pack"):
        targets = [item["anchor"]]
    else:
        field = "final_document" if item["family"] == "revision_chain" else "document"
        column = item["fields"].index(field)
        targets = []
        for number in sorted({row[column] for row in item["gold"]}):
            found = db.execute("SELECT id FROM document WHERE number = ? ORDER BY id", (number,)).fetchall()
            if len(found) != 1:
                raise RuntimeError(f"document identity is not unique: {item['id']} {number}: {found}")
            targets.append(found[0][0])
    answer = []
    for target in sorted(set(targets)):
        row = db.execute("SELECT * FROM disposition WHERE target = ? "
                         "AND evidence_status = 'source_verified' AND scope = 'whole_target' "
                         "ORDER BY id LIMIT 1", (target,)).fetchone()
        if row is None and item["family"] not in DISPOSITION_FAMILIES:
            row = db.execute("SELECT * FROM disposition WHERE target = ? ORDER BY id LIMIT 1", (target,)).fetchone()
        if row is None:
            if item["family"] in DISPOSITION_FAMILIES:
                raise RuntimeError(f"no eligible disposition: {item['id']} {target}")
            continue
        answer.append(row)
    return answer


def insert_distractors(db: sqlite3.Connection, item: dict, sources: list[tuple], scenario: str) -> list[dict]:
    status, scope = SCENARIOS[scenario]
    details = []
    for source in sources:
        row = list(source)
        existing_codes = {r[0] for r in db.execute("SELECT code FROM disposition WHERE target = ? "
                                                 "AND evidence_status = 'source_verified' AND scope = 'whole_target'",
                                                 (row[2],))}
        # 생성기의 부분 처분 유형을 그대로 쓴다. pending/whole_target만 별도로
        # 명시한 생성기 계약 밖의 관계형 진단이며, 결과를 배포 데이터에 외삽하지 않는다.
        code = "ambiguous" if status == "pending" else "partially_agreed"
        if code in existing_codes:
            raise RuntimeError(f"synthetic code is not distinguishable: {item['id']} {row[2]} {code}")
        identifier = "synthetic:scope-stress/" + hashlib.sha256(
            f"{item['id']}|{scenario}|{row[2]}".encode()).hexdigest()
        row[0], row[3], row[4], row[5] = identifier, code, status, scope
        row[6], row[7] = "synthetic:relational-contract-only", None
        db.execute("INSERT INTO disposition VALUES (?, ?, ?, ?, ?, ?, ?, ?)", row)
        details.append({"id": identifier, "target": row[2], "resolutionId": row[1],
                        "code": code, "evidenceStatus": status, "scope": scope,
                        "synthetic": True, "sourceRecordId": source[0]})
    return details


def summarize(rows: list[dict]) -> dict:
    report = {}
    for condition in sorted({r["condition"] for r in rows}):
        group = [r for r in rows if r["condition"] == condition]
        eligible = [r for r in group if r["baseline"]["exact"]]
        changed = {}
        for scenario in SCENARIOS:
            trials = [r["stress"][scenario] for r in eligible]
            changed[scenario] = {"executed": len(trials),
                                 "goldRetained": sum(t["exact"] for t in trials),
                                 "differentRows": sum(not t["exact"] and t["error"] is None for t in trials),
                                 "executionError": sum(t["error"] is not None for t in trials),
                                 "timeout": sum(t["timeout"] for t in trials),
                                 "runtimeSeconds": round(sum(t["seconds"] for t in trials), 6),
                                 "maximumRuntimeSeconds": max((t["seconds"] for t in trials), default=None)}
        report[condition] = {"selectedQueries": len(group), "baselineExact": len(eligible),
                             "baselineDifferentRows": sum(not r["baseline"]["exact"] and
                                                          r["baseline"]["error"] is None for r in group),
                             "baselineExecutionError": sum(r["baseline"]["error"] is not None for r in group),
                             "baselineTimeout": sum(r["baseline"]["timeout"] for r in group),
                             "baselineRuntimeSeconds": round(sum(r["baseline"]["seconds"] for r in group), 6),
                             "byScenario": changed}
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--pilot", action="store_true", help="RAN1 full_chain 하나와 Opus runA만 검사")
    args = ap.parse_args()
    if sqlite3.sqlite_version != "3.37.2":
        raise SystemExit(f"use /usr/bin/python3 with SQLite 3.37.2; found {sqlite3.sqlite_version}")
    chosen = selected_items()
    if args.pilot:
        chosen = [i for i in chosen if i["wg"] == "RAN1" and i["family"] == "full_chain"]
    started = time.monotonic()
    report = {"purpose": "Synthetic relational contract stress; historical corpus, gold and responses unchanged",
              "design": {"selection": "one minimum SHA-256(seed|itemId) per (WG, family), before outcome inspection",
                         "seed": SEED, "selectedItems": [{k: i[k] for k in ("id", "wg", "family")} for i in chosen],
                         "pilot": args.pilot, "scenarios": SCENARIOS, "capSeconds": CAP_SECONDS,
                         "scenarioValidity": SCENARIO_VALIDITY,
                         "designRevisionBeforeFullRun": "Builder code forces ambiguous -> pending/undetermined. Combined was changed from pending/subdocument before the full run, independent of stored-query outcomes. Status-only remains explicitly outside builder contract.",
                         "capReason": "same 60-second execution cap as original agent evaluation",
                         "score": "recorded-notation normalized exact row set; SQL original scores coincide with identity scores",
                         "eligibility": "actual baseline execution on this engine equals original gold",
                         "syntheticMeaning": "SQL contract counterexamples; not source-verified historical records or record-quality estimates"},
              "environment": {"python": sys.version, "sqlite": sqlite3.sqlite_version,
                              "cpuAffinity": sorted(os.sched_getaffinity(0)), "loadAtStart": list(os.getloadavg())},
              "scriptSha256": digest(Path(__file__)), "inputFiles": {}, "observedDispositionTypes": {},
              "items": [], "queries": []}
    for path in [Path(__file__), Path(__file__).with_name("measure_relational_equivalence.py")] + [
            ROOT / TRACK / f"integration/items_final/gate/{part}/chain_items_admitted.jsonl"
            for part in ("core", "ran5")]:
        report["inputFiles"][str(path.relative_to(ROOT))] = digest(path)
    for wg in sorted({i["wg"] for i in chosen}):
        database = ROOT / TRACK / f"integration/sqlite_final/{wg}.sqlite"
        report["inputFiles"][str(database.relative_to(ROOT))] = digest(database)
        source = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
        db = sqlite3.connect(":memory:")
        source.backup(db)
        source.close()
        report["observedDispositionTypes"][wg] = [
            {"evidenceStatus": r[0], "scope": r[1], "count": r[2]}
            for r in db.execute("SELECT evidence_status, scope, count(*) FROM disposition "
                                "GROUP BY evidence_status, scope ORDER BY evidence_status, scope")]
        responses = {}
        for condition, path in response_paths(wg):
            if args.pilot and condition != "opus_sql_runA":
                continue
            report["inputFiles"][str(path.relative_to(ROOT))] = digest(path)
            responses[condition] = {r["id"]: r for r in map(json.loads, path.read_text().splitlines())}
        for item in [i for i in chosen if i["wg"] == wg]:
            refs = {name: SQL[item["family"]].format(**names) for name, names in VARIANTS.items()}
            db.execute("PRAGMA query_only = ON")
            base_refs = {name: execute(db, item, sql, {"anchor": item["anchor"]}) for name, sql in refs.items()}
            if not all(r["exact"] for r in base_refs.values()):
                raise RuntimeError(f"baseline reference mismatch: {item['id']}: {base_refs}")
            sources = contributing_dispositions(db, item)
            entry = {"id": item["id"], "wg": wg, "family": item["family"],
                     "baselineReferences": base_refs, "scenarios": {}}
            query_rows = []
            for condition, records in responses.items():
                response = records[item["id"]]
                if response.get("questionSha256") != hashlib.sha256(item["question"].encode()).hexdigest():
                    raise RuntimeError(f"stale question: {condition} {item['id']}")
                if len(response.get("attempts") or []) != 1:
                    raise RuntimeError(f"not first-execution-only: {condition} {item['id']}")
                sql = response["attempts"][0]["sql"]
                query_rows.append({"id": item["id"], "wg": wg, "family": item["family"],
                                   "condition": condition, "sqlSha256": hashlib.sha256(sql.encode()).hexdigest(),
                                   "baseline": execute(db, item, sql), "stress": {}, "_sql": sql})
                baseline = query_rows[-1]["baseline"]
                query_rows[-1]["stressExclusionReason"] = (None if baseline["exact"] else
                    "baseline_timeout" if baseline["timeout"] else
                    "baseline_execution_error" if baseline["error"] else "baseline_different_rows")
            for scenario in SCENARIOS:
                db.execute("PRAGMA query_only = OFF")
                db.execute("SAVEPOINT synthetic_stress")
                injected = insert_distractors(db, item, sources, scenario)
                db.execute("PRAGMA query_only = ON")
                ref_result = {name: execute(db, item, sql, {"anchor": item["anchor"]}) for name, sql in refs.items()}
                if not all(r["exact"] for r in ref_result.values()):
                    raise RuntimeError(f"gold changed by synthetic distractor: {item['id']} {scenario}: {ref_result}")
                positive = None
                if item["family"] in DISPOSITION_FAMILIES:
                    sql = refs["cr_side"].replace(PREDICATES[scenario], "1 = 1")
                    positive = execute(db, item, sql, {"anchor": item["anchor"]})
                    if positive["error"] or positive["exact"] or positive["extraRowCount"] == 0:
                        raise RuntimeError(f"ineffective distractor: {item['id']} {scenario}: {positive}")
                entry["scenarios"][scenario] = {"injected": injected, "references": ref_result,
                                                  "removedPredicatePositiveControl": positive}
                for row in query_rows:
                    if row["baseline"]["exact"]:
                        row["stress"][scenario] = execute(db, item, row["_sql"])
                db.execute("PRAGMA query_only = OFF")
                db.execute("ROLLBACK TO synthetic_stress")
                db.execute("RELEASE synthetic_stress")
            for row in query_rows:
                del row["_sql"]
            report["items"].append(entry)
            report["queries"].extend(query_rows)
            print(wg, item["family"], "baselineExact", sum(r["baseline"]["exact"] for r in query_rows),
                  "/", len(query_rows), "elapsed", round(time.monotonic() - started, 1), flush=True)
        db.close()
    report["summary"] = summarize(report["queries"])
    report["summaryDispositionFamilies"] = summarize([
        r for r in report["queries"] if r["family"] in DISPOSITION_FAMILIES])
    report["summaryNegativeControls"] = summarize([
        r for r in report["queries"] if r["family"] not in DISPOSITION_FAMILIES])
    report["seconds"] = round(time.monotonic() - started, 3)
    report["environment"]["loadAtEnd"] = list(os.getloadavg())
    report["originalInputHashesUnchanged"] = all(digest(ROOT / p) == h for p, h in report["inputFiles"].items())
    if not report["originalInputHashesUnchanged"]:
        raise RuntimeError("original input changed")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("WROTE", args.out, "seconds", report["seconds"], flush=True)


if __name__ == "__main__":
    main()
