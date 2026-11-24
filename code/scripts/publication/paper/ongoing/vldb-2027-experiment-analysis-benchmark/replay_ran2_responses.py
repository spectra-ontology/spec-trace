"""RAN2 관계형 사본을 다시 내보내기 전에 쓴 RAN2 응답의 질의를 다시 실행해, 저장된 결과가 공개 사본과 현재
그래프에서 그대로 나오는지 잰다 (모델 호출 없음).

RAN2 기록 하나(R2-161177)의 처분 코드가 `agreed` 에서 `revised` 로 바뀐 뒤 RAN2 관계형 사본을 다시 내보냈다.
보고에 쓰인 RAN2 질의 작성 응답은 그 전에 실행됐으므로 Codex 탐색 실행 기록(`codex_v2/run_records/runs.jsonl`)은
이전 사본의 해시를 적는다. 이 스크립트는 세 가지를 잰다.

1. 두 사본의 테이블마다 행 단위 차집합(이전에만 있는 행, 공개 사본에만 있는 행).
2. 보고에 쓰인 RAN2 Text-to-SQL 응답 8개 파일의 모든 시도를 두 사본에서 읽기 전용으로, 실행기
   (`run_chain_eval.py` 의 `solve_text2sql`)와 같은 60초 상한으로 다시 실행한다. 시도마다 저장된 상태(성공 · 오류)가
   다시 나오는지, 처음 성공한 시도의 행(실행기처럼 칸을 문자열로 바꾸고 2,000행까지)과 행 수가 저장된 값과 같은지,
   두 사본의 결과(상태와 전체 행)가 같은지를 센다. 행 순서까지 같은 경우와 순서만 다른 경우를 따로 센다.
3. 보고에 쓰인 RAN2 Text-to-Cypher 응답 8개 파일의 모든 시도를 현재 RAN2 그래프의 읽기 트랜잭션에서 실행기
   (`solve_text2cypher`)와 같은 60초 상한으로 다시 실행해 같은 방식으로 견준다. 행 순서까지 같은 경우와 순서만
   다른 경우를 따로 센다.

결과에는 입력 응답 파일과 두 사본의 sha256, 그래프의 노드 · 관계 수, 실행한 SQLite 판본을 함께 적는다.
`ORDER BY` 없는 질의의 행 순서는 SQLite 판본에 따라 달라질 수 있으므로, 저장된 행 순서를 견주려면 응답을 만든
실행기와 같은 판본의 SQLite 를 쓰는 파이썬으로 실행한다.

사용 (저장소 루트에서):
  PYTHONPATH=scripts/common <파이썬> scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/replay_ran2_responses.py \
      --predecessor <이전 RAN2.sqlite> [--bolt bolt://localhost:7688] \
      --out logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/final/ran2_query_replay/replay.json
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sqlite3
import time
from pathlib import Path

ROOT = next(path for path in Path(__file__).resolve().parents if (path / ".git").exists())
L = Path("logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark")
RELEASE = L / "integration/sqlite_final/RAN2.sqlite"
SQL_FILES = tuple(
    [L / f"chain_eval/text2sql/RAN2_text2sql_run{run}.jsonl" for run in "ABCDE"]
    + [L / "chain_eval/codex/chain_sql_RAN2_codex.jsonl"]
    + [L / f"chain_eval/codex_v2/responses/RAN2_sql_{cond}_codex.jsonl" for cond in ("dom", "exp")])
CYPHER_FILES = tuple(
    [L / f"chain_eval/RAN2_text2cypher_claude_subagent_run{run}.jsonl" for run in "ABCDE"]
    + [L / "chain_eval/codex/chain_cy_RAN2_codex.jsonl"]
    + [L / f"chain_eval/codex_v2/responses/RAN2_cy_{cond}_codex.jsonl" for cond in ("dom", "exp")])
LIMIT_SECONDS = 60
STORED_ROWS = 2000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def stringified(rows: list) -> list:
    return [[None if cell is None else str(cell) for cell in row] for row in rows[:STORED_ROWS]]


def run_sql(db: sqlite3.Connection, sql: str):
    deadline = time.time() + LIMIT_SECONDS
    db.set_progress_handler(lambda: 1 if time.time() > deadline else 0, 100000)
    try:
        return "ok", db.execute(sql).fetchall()
    except Exception as error:
        return "error", str(error)[:200]
    finally:
        db.set_progress_handler(None, 0)


def store_difference(predecessor: Path, release: Path) -> dict:
    con = sqlite3.connect(f"file:{ROOT / release}?mode=ro", uri=True)
    con.execute(f"ATTACH 'file:{predecessor}?mode=ro' AS o")
    tables = sorted(row[0] for row in con.execute("SELECT name FROM main.sqlite_master WHERE type='table'"))
    other = sorted(row[0] for row in con.execute("SELECT name FROM o.sqlite_master WHERE type='table'"))
    out = {"tables": len(tables), "sameTableNames": tables == other, "tablesWithDifferences": {}}
    for table in tables:
        only_release = con.execute(f'SELECT * FROM main."{table}" EXCEPT SELECT * FROM o."{table}"').fetchall()
        only_predecessor = con.execute(f'SELECT * FROM o."{table}" EXCEPT SELECT * FROM main."{table}"').fetchall()
        if only_release or only_predecessor:
            out["tablesWithDifferences"][table] = {
                "rowsPredecessor": con.execute(f'SELECT count(*) FROM o."{table}"').fetchone()[0],
                "rowsRelease": con.execute(f'SELECT count(*) FROM main."{table}"').fetchone()[0],
                "onlyPredecessor": [list(map(str, row[:4])) for row in only_predecessor],
                "onlyRelease": [list(map(str, row[:4])) for row in only_release]}
    con.close()
    return out


def replay_sql(predecessor: Path) -> dict:
    old = sqlite3.connect(f"file:{predecessor}?mode=ro", uri=True)
    new = sqlite3.connect(f"file:{ROOT / RELEASE}?mode=ro", uri=True)
    files, totals = {}, collections.Counter()
    for path in SQL_FILES:
        stats, mismatches = collections.Counter(), []
        for line in (ROOT / path).read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            stats["records"] += 1
            answered = False
            for k, attempt in enumerate(record.get("attempts") or []):
                if "sql" not in attempt:
                    continue
                stats["attempts"] += 1
                stored_ok = "rowCount" in attempt
                result = {}
                for name, db in (("predecessor", old), ("release", new)):
                    status, rows = run_sql(db, attempt["sql"])
                    result[name] = (status, rows)
                    if status == "error" and "interrupted" in rows:
                        stats[f"deadline_{name}"] += 1
                if result["predecessor"] == result["release"]:
                    stats["sameOnBoth"] += 1
                for name in ("predecessor", "release"):
                    status, rows = result[name]
                    if stored_ok != (status == "ok"):
                        mismatches.append({"id": record["id"], "attempt": k, "store": name, "storedOk": stored_ok,
                                           "now": status})
                        continue
                    if not stored_ok:
                        stats[f"errorAgain_{name}"] += 1
                    elif not answered:
                        now, stored = stringified(rows), record.get("rows") or []
                        if len(rows) != attempt["rowCount"]:
                            same = "no"
                        elif now == stored:
                            same = "order"
                        elif collections.Counter(map(tuple, now)) == collections.Counter(map(tuple, stored)):
                            same = "multiset"
                        else:
                            same = "no"
                        if same == "order":
                            stats[f"rowsAsStored_{name}"] += 1
                        elif same == "multiset":
                            stats[f"rowsAsStoredOtherOrder_{name}"] += 1
                        else:
                            mismatches.append({"id": record["id"], "attempt": k, "store": name,
                                               "storedCount": attempt["rowCount"], "nowCount": len(rows)})
                if stored_ok and not answered:
                    answered = True
                    stats["answeredRecords"] += 1
        files[str(path)] = {"sha256": sha256(ROOT / path), "counts": dict(stats), "mismatches": mismatches}
        totals.update(stats)
        print(path.name, dict(stats), len(mismatches), flush=True)
    old.close()
    new.close()
    return {"limitSeconds": LIMIT_SECONDS, "sqliteVersion": sqlite3.sqlite_version, "files": files,
            "totals": dict(totals)}


def replay_cypher(bolt: str) -> dict:
    from neo4j import GraphDatabase
    from common.credentials import neo4j_auth

    driver = GraphDatabase.driver(bolt, auth=neo4j_auth())
    session = driver.session()

    def run(cypher: str):
        try:
            rows = session.execute_read(
                lambda tx: [list(row.values()) for row in tx.run(cypher, timeout=LIMIT_SECONDS)])
            return "ok", stringified(rows), len(rows)
        except Exception as error:
            return "error", str(error)[:200], None

    signature = {
        "nodes": session.execute_read(lambda tx: tx.run("MATCH (n) RETURN count(n) AS c").single()["c"]),
        "relationships": session.execute_read(lambda tx: tx.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]),
        "R2-161177.status": session.execute_read(
            lambda tx: [row["s"] for row in tx.run("MATCH (t:Tdoc {tdocNumber: 'R2-161177'}) RETURN t.status AS s")])}
    files, totals = {}, collections.Counter()
    for path in CYPHER_FILES:
        stats, mismatches = collections.Counter(), []
        for line in (ROOT / path).read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            stats["records"] += 1
            answered = False
            for k, attempt in enumerate(record.get("attempts") or []):
                if "cypher" not in attempt:
                    continue
                stats["attempts"] += 1
                status, rows, count = run(attempt["cypher"])
                stored_ok = "rowCount" in attempt
                if stored_ok != (status == "ok"):
                    mismatches.append({"id": record["id"], "attempt": k, "storedOk": stored_ok, "now": status})
                    continue
                if not stored_ok:
                    stats["errorAgain"] += 1
                elif not answered:
                    answered = True
                    stats["answeredRecords"] += 1
                    stored = record.get("rows") or []
                    if rows == stored and count == attempt["rowCount"]:
                        stats["rowsSameOrder"] += 1
                    elif (collections.Counter(map(tuple, rows)) == collections.Counter(map(tuple, stored))
                          and count == attempt["rowCount"]):
                        stats["rowsSameMultisetOtherOrder"] += 1
                    else:
                        mismatches.append({"id": record["id"], "attempt": k, "storedCount": attempt["rowCount"],
                                           "nowCount": count})
        files[str(path)] = {"sha256": sha256(ROOT / path), "counts": dict(stats), "mismatches": mismatches}
        totals.update(stats)
        print(path.name, dict(stats), len(mismatches), flush=True)
    session.close()
    driver.close()
    return {"bolt": bolt, "limitSeconds": LIMIT_SECONDS, "graph": signature, "files": files, "totals": dict(totals)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--predecessor", type=Path, required=True, help="다시 내보내기 전의 RAN2.sqlite")
    parser.add_argument("--bolt", default="bolt://localhost:7688")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    started = time.time()
    result = {
        "purpose": "RAN2 responses written before the RAN2 relational re-export, re-executed read-only on the "
                   "predecessor copy, the release copy and the current RAN2 graph, and compared with the stored results.",
        "script": str(Path(__file__).resolve().relative_to(ROOT)),
        "stores": {"predecessor": {"sha256": sha256(args.predecessor), "bytes": args.predecessor.stat().st_size},
                   "release": {"path": str(RELEASE), "sha256": sha256(ROOT / RELEASE),
                               "bytes": (ROOT / RELEASE).stat().st_size}},
        "storeDifference": store_difference(args.predecessor, RELEASE),
        "sql": replay_sql(args.predecessor),
        "cypher": replay_cypher(args.bolt),
    }
    result["seconds"] = round(time.time() - started, 1)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"sql": result["sql"]["totals"], "cypher": result["cypher"]["totals"],
                      "seconds": result["seconds"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
