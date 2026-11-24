"""관계형 질의 풀이(text2sql)가 놓친 문항을 원인별로 가른다 (모델 호출 없음).

저장된 응답을 `score_chain_eval.score` 로 채점하고, 정답 행 집합과 다른 문항마다 실행된 SQL 과 관계형 내보내기
파일을 읽어 다음 다섯 가운데 하나로 분류한다. 위에서부터 처음 맞는 것을 고른다. 파일은 읽기 전용으로 연다.

- execution_deadline: 질의가 풀이 때의 실행 상한(60초)에 걸려 중단됐다. `--rerun-seconds` 를 주면 같은 질의를
  그 상한으로 다시 실행해 정답과 같아지는지, 몇 초 걸렸는지를 함께 적는다.
- execution_error: 질의 실행이 그 밖의 오류로 끝났다. 오류 문장의 앞부분을 적는다.
- filter_list_omits_stored_value: 질의가 열 하나를 읽는 식(열 그대로이거나 `LOWER`·`TRIM`·`REPLACE` 등으로
  정규화한 식)을 문자열 목록과 `IN (...)` 으로 비교하는데, 그 열의 저장값을 같은 식으로 바꾼 값 가운데 목록에
  없는 것이 있고, 그 값 하나를 목록에 더해 다시 실행하면 응답이 정답과 같아진다. 식은 관계형 파일에서 저장값마다
  그대로 계산한다. 표 · 열 · 식 · 더한 값을 함께 적는다. `diagnose_subagent_misses.py` 의 같은 이름 원인과 같은
  판정이다.
- filter_list_excludes_gold_rows: 목록에 저장값 하나를 더해서는 정답이 되지 않고, 위와 같은 `IN (...)` 비교
  하나를 `1` 로 바꿔 다시 실행하면 응답이 정답과 같아진다. 정답 행 가운데 그 열이 비었거나 목록과 무관한 값을 가진
  기록에서 온 것이 있다는 뜻이다. 표 · 열 · 식과 그 표에서 열이 빈 행 수를 적는다.
- unclassified: 위 넷에 해당하지 않는다. 정답에만 있는 행과 응답에만 있는 행을 함께 적는다.

사용: python3 diagnose_text2sql_misses.py --items <jsonl> [<jsonl> ...] --responses <jsonl> [<jsonl> ...] \
          --sqlite-dir <dir> [--rerun-seconds 600] --out <json>
관계형 파일은 `<dir>/<WG>.sqlite` 로 찾는다. 저장소 루트에서
`PYTHONPATH=scripts/common:scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark` 로 실행한다.
"""
from __future__ import annotations

import argparse
import ast
import collections
import json
import re
import sqlite3
import time
from pathlib import Path

from score_chain_eval import key, score

NAME = r"[A-Za-z_][A-Za-z0-9_]*"
# <식> IN ('a', 'b', ...) — 목록은 문자열 상수만 담는다(부분 질의 `IN (SELECT ...)` 는 고르지 않는다)
IN_LIST = re.compile(r"\s+IN\s*\(\s*('(?:[^']|'')*'(?:\s*,\s*'(?:[^']|'')*')*)\s*\)", re.IGNORECASE)
STRING_LITERAL = re.compile(r"'(?:[^']|'')*'")
COLUMN_READ = re.compile(rf'\b({NAME})\.("?)({NAME})\2')
TRAILING_NAME = re.compile(rf"{NAME}\s*$")
TRAILING_READ = re.compile(rf'{NAME}\."?{NAME}"?$')
TABLE_ALIAS = re.compile(rf"\b(?:FROM|JOIN)\s+({NAME})\s+(?:AS\s+)?({NAME})\b", re.IGNORECASE)
LITERAL = re.compile(r"'((?:[^']|'')*)'")
SQL_WORDS = {"on", "where", "join", "left", "inner", "group", "order", "union", "select", "limit", "using"}


def parsed(value):
    return ast.literal_eval(value) if isinstance(value, str) else value


def executed_query(response: dict) -> tuple[str, str | None]:
    attempts = parsed(response.get("attempts")) or []
    if not attempts:
        return "", None
    return attempts[-1].get("sql", ""), attempts[-1].get("error")


def run(db, sql: str, seconds: float) -> tuple[list[list[str | None]] | None, str | None, float]:
    deadline = time.time() + seconds
    started = time.time()
    db.set_progress_handler(lambda: 1 if time.time() > deadline else 0, 100000)
    try:
        rows = db.execute(sql).fetchall()
    except Exception as error:
        return None, str(error)[:300], round(time.time() - started, 1)
    finally:
        db.set_progress_handler(None, 0)
    return [[None if c is None else str(c) for c in row] for row in rows], None, round(time.time() - started, 1)


def masked(sql: str) -> str:
    """문자열 상수의 내용을 공백으로 바꾼다. 길이가 같으므로 위치는 원래 질의와 그대로 맞는다."""
    return STRING_LITERAL.sub(lambda m: "'" + " " * (len(m.group(0)) - 2) + "'", sql)


def operand_before(text: str, end: int) -> tuple[int, int] | None:
    """`IN` 바로 앞 피연산자의 (시작, 끝). 괄호로 끝나면 짝 괄호와 그 앞 함수 이름까지, 아니면 `a.col` 하나."""
    stop = end
    while stop > 0 and text[stop - 1].isspace():
        stop -= 1
    if stop and text[stop - 1] == ")":
        depth, at = 0, stop - 1
        while at >= 0:
            depth += {")": 1, "(": -1}.get(text[at], 0)
            if depth == 0:
                break
            at -= 1
        if at < 0:
            return None
        name = TRAILING_NAME.search(text[:at])
        return (name.start() if name else at), stop
    read = TRAILING_READ.search(text[:stop])
    return (read.start(), stop) if read else None


def list_filters(sql: str):
    """`<식> IN (목록)` 비교 가운데 식이 표 하나의 열 하나만 읽는 것을 차례로 돌려준다.

    돌려주는 값은 (목록 match, 식의 (시작, 끝), 표, 열, 저장값마다 계산할 식). `NOT` 이 붙은 비교는 목록이 거르는
    값이 아니라 빼는 값이므로 고르지 않는다.
    """
    aliases = {alias: table for table, alias in TABLE_ALIAS.findall(sql) if alias.lower() not in SQL_WORDS}
    text = masked(sql)
    for match in IN_LIST.finditer(text):
        span = operand_before(text, match.start())
        if span is None or re.search(r"\bNOT\s*$", text[:span[0]], re.IGNORECASE):
            continue
        reads = [(m.group(1), m.group(3), m.span()) for m in COLUMN_READ.finditer(text[span[0]:span[1]])]
        if len({(alias, column) for alias, column, _ in reads}) != 1:
            continue
        alias, column, _ = reads[0]
        expression = sql[span[0]:span[1]]
        for _, _, (start, stop) in sorted(reads, key=lambda r: -r[2][0]):
            expression = expression[:start] + "v" + expression[stop:]
        yield match, span, aliases.get(alias, alias), column, expression


def omitted_value_repairs(db, sql: str, gold) -> list[dict]:
    """`<식> IN (목록)` 에서, 식이 읽는 열의 저장값을 같은 식으로 바꾼 값 가운데 목록에 없는 것 하나를 더했을 때
    정답과 같아지는 경우를 모두 돌려준다. 정규화는 파이썬으로 흉내 내지 않고 관계형 파일에서 같은 식을 계산한다."""
    repairs = []
    for match, span, table, column, expression in list_filters(sql):
        try:
            stored = {n for (n,) in db.execute(
                f'SELECT DISTINCT {expression} FROM (SELECT DISTINCT "{column}" AS v FROM "{table}" '
                f'WHERE "{column}" IS NOT NULL)')}
        except sqlite3.Error:
            continue
        listed_values = {v.replace("''", "'") for v in LITERAL.findall(sql[match.start(1):match.end(1)])}
        for value in sorted(v for v in stored if isinstance(v, str) and v not in listed_values):
            escaped = value.replace("'", "''")
            patched = sql[:match.start(1)] + f"'{escaped}', " + sql[match.start(1):]
            rows, error, _ = run(db, patched, 60)
            if error is None and score(gold, rows)["exact"]:
                repairs.append({"table": table, "column": column, "expression": sql[span[0]:span[1]],
                                "addedValue": value})
    return repairs


def dropped_filter_repairs(db, sql: str, gold) -> list[dict]:
    """`<식> IN (목록)` 비교 하나를 `1` 로 바꿔 다시 실행하면 정답과 같아지는 경우를 모두 돌려준다."""
    repairs = []
    for match, span, table, column, _ in list_filters(sql):
        patched = sql[:span[0]] + "1" + sql[match.end():]
        rows, error, _ = run(db, patched, 60)
        if error is not None or not score(gold, rows)["exact"]:
            continue
        try:
            total, missing = db.execute(
                f'SELECT count(*), sum("{column}" IS NULL) FROM "{table}"').fetchone()
            counts = {"records": total, "recordsWithoutProperty": missing}
        except sqlite3.Error:
            counts = {}
        repairs.append({"table": table, "column": column, "expression": sql[span[0]:span[1]], **counts})
    return repairs


def run_label(response: dict) -> str:
    model = response.get("model", "")
    return model.rsplit("-", 1)[-1] if "-run" in model else model


def classify(db, item: dict, response: dict, rerun_seconds: float | None) -> dict:
    sql, error = executed_query(response)
    gold = parsed(item["gold"])
    given = {key(row) for row in parsed(response.get("rows")) or []}
    wanted = {key(row) for row in gold}
    detail = {"id": item["id"], "family": item["family"],
              "onlyInGold": sorted(wanted - given)[:5], "onlyInResponse": sorted(given - wanted)[:5]}
    if error == "interrupted":
        out = {**detail, "cause": "execution_deadline"}
        if rerun_seconds:
            rows, rerun_error, seconds = run(db, sql, rerun_seconds)
            out["rerun"] = {"limitSeconds": rerun_seconds, "seconds": seconds, "error": rerun_error,
                            "exact": bool(rows is not None and score(gold, rows)["exact"])}
        return out
    if error:
        return {**detail, "cause": "execution_error", "error": error[:200]}
    repairs = omitted_value_repairs(db, sql, gold)
    if repairs:
        return {**detail, "cause": "filter_list_omits_stored_value", "repairs": repairs}
    repairs = dropped_filter_repairs(db, sql, gold)
    if repairs:
        return {**detail, "cause": "filter_list_excludes_gold_rows", "repairs": repairs}
    return {**detail, "cause": "unclassified"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, nargs="+", required=True)
    parser.add_argument("--responses", type=Path, nargs="+", required=True)
    parser.add_argument("--sqlite-dir", type=Path, required=True)
    parser.add_argument("--rerun-seconds", type=float, default=None,
                        help="실행 상한에 걸린 질의를 이 상한으로 다시 실행한다")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    items = {item["id"]: item for path in args.items for item in map(json.loads, path.read_text().splitlines())}
    by_wg: dict[str, list[dict]] = collections.defaultdict(list)
    for path in args.responses:
        for response in map(json.loads, path.read_text().splitlines()):
            if response["id"] in items:
                by_wg[response["wg"]].append(response)

    exact: dict[str, dict[str, list[int]]] = {}
    totals: dict[str, dict[str, list[int]]] = collections.defaultdict(
        lambda: {"answerable": [0, 0], "empty": [0, 0]})
    misses: list[dict] = []
    for wg, responses in sorted(by_wg.items()):
        path = args.sqlite_dir / f"{wg}.sqlite"
        db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        for response in sorted(responses, key=lambda r: (run_label(r), r["id"])):
            item = items[response["id"]]
            label = run_label(response)
            gold = parsed(item["gold"])
            hit = score(gold, parsed(response.get("rows")))["exact"]
            cell = exact.setdefault(wg, {}).setdefault(label, [0, 0])
            cell[0] += hit
            cell[1] += 1
            part = totals[label]["answerable" if gold else "empty"]
            part[0] += hit
            part[1] += 1
            if not hit:
                misses.append({"wg": wg, "run": label, **classify(db, item, response, args.rerun_seconds)})
        db.close()
    causes = collections.Counter((m["cause"], m["wg"], m["run"], m["family"]) for m in misses)
    report = {
        "scope": "text2sql responses scored against the current items; each missed item classified from its "
                 "executed query and the relational export",
        "exact": exact, "totals": dict(totals),
        "byCause": [{"cause": c, "wg": w, "run": r, "family": f, "items": n}
                    for (c, w, r, f), n in sorted(causes.items())],
        "misses": misses,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("exact", "totals", "byCause")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
