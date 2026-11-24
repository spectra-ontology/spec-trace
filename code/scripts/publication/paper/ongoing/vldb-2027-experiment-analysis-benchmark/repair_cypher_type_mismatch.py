"""Neo4j 가 컴파일 단계 타입 검사에서 거절한 text2cypher 질의를 값이 바뀌지 않게 고쳐 다시 실행한다 (모델 호출 없음).

저장된 응답 가운데 마지막 시도가 `Type mismatch: expected String but was ...` 로 끝난 질의마다(뒤에 오는 형은
`Boolean` 이나 `Any or Boolean`), 오류가
가리키는 위치의 변수를 `toString(...)` 으로 감싸고 `EXPLAIN` 으로 다시 컴파일한다. 컴파일될 때까지 오류 위치마다
한 번씩 되풀이하고, 컴파일되면 읽기 트랜잭션으로 실행해 정답과 견준다. 감싼 변수가 문자열이나 null 만 받으면
고친 질의는 원래 질의와 같은 값을 계산한다. 그래서 거절된 질의가 읽는 (레이블, 속성)마다 저장값의 종류를 함께 센다.

채점 규칙은 둘이다. 회의 동일성 규칙은 `score_meeting_spelling_sensitivity` 의 `same_meeting` 으로, 회의 칸의
끝 `-e` 를 양쪽에서 떼되 기록이 두 표기를 따로 담은 회의 이름은 그대로 둔다. 기록 표기 규칙은 같은 파일의 `recorded` 다. 결과 행은 `diagnose_subagent_misses.rerun_matches_gold` 와 같게 칸마다 문자열로 바꾸고 앞 2,000 행만 본다.

대조군: 같은 세션에서 오류 없이 끝난 응답의 질의를 같은 방법으로 다시 실행해, 저장된 행으로 매긴 결과와 다시
실행한 행으로 매긴 결과가 같은지 센다. 행 변환 규약이 채점 결과를 바꾸지 않는지 확인하는 검사다.

사용: python3 repair_cypher_type_mismatch.py --items <jsonl> [<jsonl> ...] --responses <jsonl> [<jsonl> ...] \
          --bolt RAN4=bolt://localhost:7690 [--bolt ...] --out <json>
저장소 루트에서 `PYTHONPATH=scripts/common:scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark` 로 실행한다.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

from neo4j import GraphDatabase

from common.credentials import neo4j_auth
from diagnose_subagent_misses import RERUN_SECONDS, executed_query, property_reads, run_label
from score_meeting_spelling_sensitivity import exact, make_row_key, separately_recorded_meetings

TYPE_MISMATCH = re.compile(r"Type mismatch: expected String but was (?P<found>[A-Za-z ]+?) "
                           r"\(line \d+, column \d+ \(offset: (?P<offset>\d+)\)\)")
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
PREFIX = "EXPLAIN "
MAX_WRAPS = 40


def compile_error(session, query: str) -> str | None:
    try:
        session.run(PREFIX + query).consume()
    except Exception as error:  # noqa: BLE001 - 컴파일 오류 문장을 그대로 적는다
        return str(getattr(error, "message", error)).split("\n")[0]
    return None


def repair(session, query: str) -> dict:
    """오류 위치의 변수를 `toString` 으로 감싸 컴파일될 때까지 되풀이한다."""
    wrapped = []
    for _ in range(MAX_WRAPS):
        message = compile_error(session, query)
        if message is None:
            return {"compiles": True, "query": query, "wrapped": wrapped}
        found = TYPE_MISMATCH.search(message)
        if not found:
            return {"compiles": False, "query": query, "wrapped": wrapped, "error": message[:200]}
        offset = int(found.group("offset")) - len(PREFIX)
        name = IDENTIFIER.match(query, offset)
        if not name or (offset > 0 and re.match(r"[A-Za-z0-9_.]", query[offset - 1])):
            return {"compiles": False, "query": query, "wrapped": wrapped,
                    "error": f"no variable at offset {offset}: {query[offset:offset + 30]!r}"}
        wrapped.append(name.group(0))
        query = f"{query[:offset]}toString({name.group(0)}){query[name.end():]}"
    return {"compiles": False, "query": query, "wrapped": wrapped, "error": "wrap limit reached"}


def run_rows(session, query: str):
    try:
        rows = session.execute_read(
            lambda tx: [list(row.values()) for row in tx.run(query, timeout=RERUN_SECONDS)])
    except Exception as error:  # noqa: BLE001 - 실행 오류는 행 없음으로 적는다
        return None, str(getattr(error, "message", error)).split("\n")[0][:200]
    return [[None if c is None else str(c) for c in row] for row in rows[:2000]], None


def value_types(session, reads) -> dict[str, dict[str, int]]:
    out = {}
    for kind, names, prop in sorted(reads):
        label = ":".join(f"`{n}`" for n in names)
        pattern = f"(x:{label})" if kind == "node" else f"()-[x:{label}]->()"
        rows = session.run(f"MATCH {pattern} WHERE x.`{prop}` IS NOT NULL "
                           f"RETURN valueType(x.`{prop}`) AS t, count(*) AS n").data()
        out[f"{':'.join(names)}.{prop}"] = {row["t"]: row["n"] for row in rows}
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, nargs="+", required=True)
    parser.add_argument("--responses", type=Path, nargs="+", required=True)
    parser.add_argument("--bolt", action="append", required=True, help="WG=bolt URL, WG 마다 한 번")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    bolts = dict(entry.split("=", 1) for entry in args.bolt)
    items = {item["id"]: item for path in args.items for item in map(json.loads, path.read_text().splitlines())}
    kept = separately_recorded_meetings()
    identity_key, recorded_key = make_row_key("same_meeting", kept), make_row_key("recorded", kept)

    sessions = []
    rejected_rows = []
    for path in args.responses:
        responses = [r for r in map(json.loads, path.read_text().splitlines()) if r["id"] in items]
        rejected = [r for r in responses if TYPE_MISMATCH.search(executed_query(r)[1] or "")]
        if not rejected:
            continue
        wg = responses[0]["wg"]
        with GraphDatabase.driver(bolts[wg], auth=neo4j_auth()) as driver, \
                driver.session(default_access_mode="READ") as session:
            reads = set()
            outcome = collections.Counter()
            for response in rejected:
                item = items[response["id"]]
                query, stored_error = executed_query(response)
                reported = TYPE_MISMATCH.search(stored_error).group("found")
                reads |= property_reads(query)
                fixed = repair(session, query)
                rows, error = run_rows(session, fixed["query"]) if fixed["compiles"] else (None, fixed.get("error"))
                identity = exact(item, rows, identity_key)
                recorded = exact(item, rows, recorded_key)
                outcome["rejected"] += 1
                outcome["compilesAfterRepair"] += fixed["compiles"]
                outcome["runs"] += rows is not None
                outcome["identityCorrect"] += identity
                outcome["recordedCorrect"] += recorded
                rejected_rows.append({"wg": wg, "run": run_label(response), "id": item["id"],
                                      "family": item["family"], "reportedType": reported,
                                      "wrapped": fixed["wrapped"],
                                      "compiles": fixed["compiles"], "identity": identity,
                                      "recorded": recorded, **({"error": error} if error else {})})
            control = collections.Counter()
            for response in responses:
                query, error = executed_query(response)
                if error or not query:
                    continue
                item = items[response["id"]]
                rows, rerun_error = run_rows(session, query)
                stored = exact(item, response.get("rows") or [], identity_key)
                again = exact(item, rows, identity_key)
                control["queries"] += 1
                control["sameOutcome"] += stored == again
                control["storedIdentityCorrect"] += stored
                control["rerunIdentityCorrect"] += again
                control["rerunErrors"] += rows is None
            sessions.append({"responses": str(path), "wg": wg, "run": run_label(rejected[0]),
                             "rejected": dict(outcome), "control": dict(control),
                             "valueTypesOfPropertiesRead": value_types(session, reads)})

    totals = collections.Counter()
    for entry in sessions:
        totals.update(entry["rejected"])
    wraps = collections.Counter(len(row["wrapped"]) for row in rejected_rows)
    result = {"scope": "text2cypher responses whose executed query Neo4j rejected with "
                       "'Type mismatch: expected String but was <type>'",
              "reportedTypes": dict(collections.Counter(row["reportedType"] for row in rejected_rows)),
              "repair": "wrap the variable at each reported offset in toString(), recompile with EXPLAIN, repeat",
              "totals": dict(totals), "wrapsPerQuery": dict(sorted(wraps.items())),
              "sessions": sessions, "queries": rejected_rows}
    args.out.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({"totals": result["totals"], "wrapsPerQuery": result["wrapsPerQuery"],
                      "sessions": [{k: e[k] for k in ("wg", "run", "rejected", "control")} for e in sessions]}))


if __name__ == "__main__":
    main()
