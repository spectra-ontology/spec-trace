"""그래프 질의 풀이(text2cypher)가 놓친 문항을 원인별로 가른다 (모델 호출 없음).

저장된 응답을 `score_chain_eval.score` 로 채점하고, 정답 행 집합과 다른 문항마다 실행된 질의와 그래프를
읽어 다음 여덟 가운데 하나로 분류한다. 위에서부터 처음 맞는 것을 고른다. 그래프는 읽기 트랜잭션으로만 연다.

- execution_error: 질의 실행이 오류로 끝나 행이 없다(컴파일 단계의 타입 검사 오류 포함). 오류 문장의 앞부분을
  적는다. 실행되지 않은 질의는 그래프 내용과 무관하게 행을 내지 못하므로 아래 원인보다 먼저 고른다.
- property_absent_in_graph: 질의가 레이블을 붙여 묶은 변수의 속성을 읽는데(`t.release`, 노드 패턴 안의
  `{release: ...}`), 그 레이블의 어느 노드 · 관계에도 그 속성이 없다. 질의가 그 속성으로 거르면 행이 비고,
  돌려주면 빈 칸이 된다. 읽은 (레이블, 속성) 쌍을 함께 적는다.
- filter_list_omits_stored_value: 질의가 속성 하나를 읽는 식(속성 그대로이거나 `toLower`·`trim`·`replace`
  등으로 정규화한 식)을 문자열 목록과 `IN [...]` 으로 비교하는데, 그 레이블에 저장된 값을 같은 식으로 바꾼 값
  가운데 목록에 없는 것이 있고, 그 값 하나를 목록에 더해 다시 실행하면 응답이 정답과 같아진다. 식은 그래프에서
  저장값마다 그대로 계산한다. 레이블 · 속성 · 식 · 더한 값을 함께 적는다. `diagnose_text2sql_misses.py` 의 같은
  이름 원인과 같은 판정이다.
- filter_list_excludes_gold_rows: 목록에 저장값 하나를 더해서는 정답이 되지 않고, 위와 같은 `IN [...]` 비교
  하나를 `true` 로 바꿔 다시 실행하면 응답이 정답과 같아진다. 정답 행 가운데 그 속성이 비었거나 목록과 무관한
  값을 가진 기록에서 온 것이 있다는 뜻이다. 레이블 · 속성 · 식과 그 레이블에서 속성이 빈 기록 수를 적는다.
  `diagnose_text2sql_misses.py` 의 같은 이름 원인과 같은 판정이다.
- canonical_meeting_number_returned: 질의가 `Meeting` 으로 묶은 변수의 `canonicalMeetingNumber` 를 읽고,
  그 읽기를 모두 `meetingNumber` 로 바꿔 다시 실행하면 응답이 정답과 같아진다. 두 속성은 `RAN1#104-e` 와
  `RAN1#104` 처럼 회의 표기가 다르고, 정답은 회의 기록의 표기(`meetingNumber`)를 쓴다.
- section_spec_number_missing: 절을 묻는 문항(`clause_history`·`full_chain`)이고, `Section` 으로 묶은 변수의
  `specNumber` 를 질의가 읽으며, 그 문항이 가리키는 Section 가운데 `specNumber` 속성이 없는 노드가 있다.
  질의 어딘가에 `specNumber` 라는 낱말이 있다는 것만으로는 고르지 않는다(Spec 노드의 `specNumber` 는 이
  원인이 아니다).
- revision_walk_bound: 개정 사슬 문항(`revision_chain`)이고, 질의의 가변 길이 경로 상한이 시작 문서에서
  어떤 정답 문서까지의 최단 개정 거리보다 작다. 거리는 `IS_REVISION_OF`·`REVISED_TO` 를 방향 없이 따라 잰다.
- unclassified: 위 일곱에 해당하지 않는다. 정답에만 있는 행과 응답에만 있는 행을 함께 적는다.

같은 그래프에서 Section 노드 수와 `specNumber` 가 없는 Section 노드 수도 센다.

사용: python3 diagnose_subagent_misses.py --items <jsonl> [<jsonl> ...] --responses <jsonl> [<jsonl> ...] \
          --bolt RAN3=bolt://localhost:7689 [--bolt ...] --out <json>
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
from crosscheck_chain_items_graph import graph_key
from score_chain_eval import key, score

SECTION_FAMILIES = {"clause_history", "full_chain"}
# `*..N`, `*1..N`, `*0..N` 처럼 위 끝이 정해진 가변 길이 경로. 위 끝이 없는 `*` · `*1..` 는 상한이 없다.
BOUNDED_WALK = re.compile(r"\*\s*\d*\s*\.\.\s*(\d+)")
NAME = r"[A-Za-z_][A-Za-z0-9_]*"
# `(t:Tdoc:CR {k: v})` 의 변수 · 레이블들 · 속성 지도, `[r:REL {k: v}]` 도 같은 꼴로 읽는다.
NODE_PATTERN = re.compile(rf"\(\s*({NAME})?\s*((?::\s*`?{NAME}`?\s*)+)(\{{[^}}]*\}})?")
REL_PATTERN = re.compile(rf"\[\s*({NAME})?\s*:\s*`?({NAME})`?[^\]{{]*(\{{[^}}]*\}})?")
PROPERTY_READ = re.compile(rf"\b({NAME})\.`?({NAME})`?")
MAP_KEY = re.compile(rf"({NAME})\s*:")
STRING_LITERAL = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"")
# `<식> IN ['a', 'b']` 의 목록. 문자열 내용을 지운 질의 위에서 찾으므로 문자열 안의 `]` 에 걸리지 않는다.
IN_LIST = re.compile(r"\s+IN\s*\[([^\]]*)\]", re.IGNORECASE)
TRAILING_NAME = re.compile(rf"{NAME}\s*$")
TRAILING_READ = re.compile(rf"{NAME}\.`?{NAME}`?$")
LIST_LITERAL = re.compile(r"'((?:[^'\\]|\\.)*)'")
CANONICAL_MEETING_READ = re.compile(rf"\b({NAME})\.`?canonicalMeetingNumber`?")
RERUN_SECONDS = 60
SECTIONS_OF = {
    "clause_history": "MATCH (s:Section {sectionId: $anchor}) RETURN count(s) AS n, "
                      "count(CASE WHEN s.specNumber IS NULL THEN 1 END) AS missing",
    "full_chain": "MATCH (:CR {tdocNumber: $anchor})-[:MODIFIES_SECTION]->(s:Section) RETURN count(DISTINCT s) AS n, "
                  "count(DISTINCT CASE WHEN s.specNumber IS NULL THEN s END) AS missing",
}
REVISION_DISTANCE = ("MATCH (a {tdocNumber: $anchor}), (b {tdocNumber: $target}) "
                     "MATCH p = shortestPath((a)-[:IS_REVISION_OF|REVISED_TO*1..40]-(b)) RETURN length(p) AS d")


def executed_query(response: dict) -> tuple[str, str | None]:
    attempts = response.get("attempts") or []
    if not attempts:
        return "", None
    return attempts[-1].get("cypher", ""), attempts[-1].get("error")


def bindings(query: str) -> tuple[dict[str, set[tuple[str, tuple[str, ...]]]], set[tuple[str, tuple[str, ...], str]]]:
    """변수마다 붙은 (종류, 레이블들)과, 패턴 안의 속성 지도에서 읽는 (종류, 레이블들, 속성)."""
    text = STRING_LITERAL.sub("''", query)
    bound: dict[str, set[tuple[str, tuple[str, ...]]]] = collections.defaultdict(set)
    reads: set[tuple[str, tuple[str, ...], str]] = set()
    for var, labels, props in NODE_PATTERN.findall(text):
        names = tuple(sorted(re.findall(NAME, labels.replace("`", ""))))
        if var:
            bound[var].add(("node", names))
        reads |= {("node", names, k) for k in MAP_KEY.findall(props.strip("{}"))}
    for var, rel, props in REL_PATTERN.findall(text):
        if var:
            bound[var].add(("rel", (rel,)))
        reads |= {("rel", (rel,), k) for k in MAP_KEY.findall(props.strip("{}"))}
    return bound, reads


def property_reads(query: str) -> set[tuple[str, tuple[str, ...], str]]:
    """질의가 읽는 (종류, 레이블들, 속성). 종류는 `node` 또는 `rel` 이다.

    문자열 상수는 먼저 지운다(그 안의 `a.b` 는 속성 읽기가 아니다). 레이블 없이 묶은 변수, 함수 이름
    (`toLower` 등), 같은 이름에 서로 다른 레이블이 붙은 변수는 읽지 않는다 — 어느 레이블을 볼지 정할 수 없다.
    """
    text = STRING_LITERAL.sub("''", query)
    bound, reads = bindings(query)
    for var, prop in PROPERTY_READ.findall(text):
        if len(bound.get(var, ())) == 1:
            kind, names = next(iter(bound[var]))
            reads.add((kind, names, prop))
    return reads


def absent_properties(session, reads) -> list[str]:
    """그래프의 어느 노드 · 관계에도 없는 (레이블, 속성)을 `Label.prop` 꼴로 돌려준다."""
    absent = []
    for kind, names, prop in sorted(reads):
        label = ":".join(f"`{n}`" for n in names)
        pattern = f"(x:{label})" if kind == "node" else f"()-[x:{label}]->()"
        found = session.run(f"MATCH {pattern} WHERE x.`{prop}` IS NOT NULL RETURN 1 AS hit LIMIT 1").single()
        if found is None:
            absent.append(f"{':'.join(names)}.{prop}")
    return absent


def rerun_matches_gold(session, query: str, gold) -> bool:
    """고친 질의를 읽기 트랜잭션으로 다시 실행해 정답 행 집합과 같은지 본다. 실패하면 같지 않다고 본다."""
    try:
        rows = session.execute_read(
            lambda tx: [list(row.values()) for row in tx.run(query, timeout=RERUN_SECONDS)])
    except Exception:
        return False
    return bool(score(gold, [[None if c is None else str(c) for c in row] for row in rows[:2000]])["exact"])


def masked(query: str) -> str:
    """문자열 상수의 내용을 공백으로 바꾼다. 길이가 같으므로 위치는 원래 질의와 그대로 맞는다."""
    return STRING_LITERAL.sub(lambda m: m.group(0)[0] + " " * (len(m.group(0)) - 2) + m.group(0)[-1], query)


def operand_before(text: str, end: int) -> tuple[int, int] | None:
    """`IN` 바로 앞 피연산자의 (시작, 끝). 괄호로 끝나면 짝 괄호와 그 앞 함수 이름까지, 아니면 `x.prop` 하나."""
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


def list_filters(query: str):
    """`<식> IN [목록]` 비교 가운데 식이 레이블 하나로 묶은 변수의 속성 하나만 읽는 것을 차례로 돌려준다.

    돌려주는 값은 (목록 match, 식의 (시작, 끝), 레이블 이름들, 속성, 그래프에서 저장값마다 계산할 MATCH 패턴과 식).
    `NOT` 이 앞에 붙은 비교는 목록이 거르는 값이 아니라 빼는 값이므로 고르지 않는다.
    """
    bound, _ = bindings(query)
    text = masked(query)
    for match in IN_LIST.finditer(text):
        span = operand_before(text, match.start())
        if span is None or re.search(r"\bNOT\s*$", text[:span[0]], re.IGNORECASE):
            continue
        reads = {(m.group(1), m.group(2), m.span()) for m in PROPERTY_READ.finditer(text[span[0]:span[1]])}
        if len({(var, prop) for var, prop, _ in reads}) != 1:
            continue
        var, prop, _ = next(iter(reads))
        if len(bound.get(var, ())) != 1:
            continue
        kind, names = next(iter(bound[var]))
        label = ":".join(f"`{n}`" for n in names)
        pattern = f"(x:{label})" if kind == "node" else f"()-[x:{label}]->()"
        expression = query[span[0]:span[1]]
        for _, _, (start, stop) in sorted(reads, key=lambda r: -r[2][0]):
            expression = expression[:start] + "v" + expression[stop:]
        yield match, span, names, prop, pattern, expression


def omitted_value_repairs(session, query: str, gold) -> list[dict]:
    """`<식> IN [목록]` 에서, 식이 읽는 속성의 저장값을 같은 식으로 바꾼 값 가운데 목록에 없는 것 하나를 더했을 때
    정답과 같아지는 경우를 모두 돌려준다.

    정규화(`toLower`·`trim`·`replace` 무엇이든, 지우든 다른 글자로 바꾸든)는 파이썬으로 흉내 내지 않고 그래프에서
    같은 식을 저장값마다 계산해 얻는다.
    """
    repairs = []
    for match, span, names, prop, pattern, expression in list_filters(query):
        try:
            stored = {r["n"] for r in session.execute_read(lambda tx: list(tx.run(
                f"MATCH {pattern} WHERE x.`{prop}` IS NOT NULL WITH DISTINCT x.`{prop}` AS v "
                f"RETURN DISTINCT {expression} AS n", timeout=RERUN_SECONDS)))}
        except Exception:
            continue
        listed_values = set(LIST_LITERAL.findall(query[match.start(1):match.end(1)]))
        for value in sorted(v for v in stored if isinstance(v, str) and v not in listed_values):
            insert_at = match.start(1)
            escaped = value.replace("\\", "\\\\").replace("'", "\\'")
            patched = query[:insert_at] + f"'{escaped}', " + query[insert_at:]
            if rerun_matches_gold(session, patched, gold):
                repairs.append({"label": ":".join(names), "property": prop, "expression": query[span[0]:span[1]],
                                "addedValue": value})
    return repairs


def dropped_filter_repairs(session, query: str, gold) -> list[dict]:
    """`<식> IN [목록]` 비교 하나를 `true` 로 바꿔 다시 실행하면 정답과 같아지는 경우를 모두 돌려준다.

    목록에 값을 더해서는 정답이 되지 않는데 비교를 빼면 정답이 되는 경우다. 정답 행 가운데 그 속성이 비었거나
    목록과 무관한 값을 가진 기록에서 온 것이 있어, 그 속성으로 거르는 것 자체가 정답 행을 뺀다. 그 레이블에서
    속성이 빈 기록 수를 함께 적는다.
    """
    repairs = []
    for match, span, names, prop, pattern, _ in list_filters(query):
        patched = query[:span[0]] + "true" + query[match.end():]
        if not rerun_matches_gold(session, patched, gold):
            continue
        try:
            row = session.execute_read(lambda tx: tx.run(
                f"MATCH {pattern} RETURN count(x) AS n, count(CASE WHEN x.`{prop}` IS NULL THEN 1 END) AS missing",
                timeout=RERUN_SECONDS).single())
            counts = {"records": row["n"], "recordsWithoutProperty": row["missing"]}
        except Exception:
            counts = {}
        repairs.append({"label": ":".join(names), "property": prop, "expression": query[span[0]:span[1]], **counts})
    return repairs


def canonical_meeting_repair(session, query: str, gold) -> bool:
    """`Meeting` 변수의 `canonicalMeetingNumber` 읽기를 `meetingNumber` 로 바꿔 정답과 같아지는지 본다."""
    bound, _ = bindings(query)
    meeting_vars = {var for var in CANONICAL_MEETING_READ.findall(query)
                    if bound.get(var) == {("node", ("Meeting",))}}
    if not meeting_vars:
        return False
    patched = query
    for var in meeting_vars:
        patched = re.sub(rf"\b{var}\.`?canonicalMeetingNumber`?", f"{var}.meetingNumber", patched)
    return rerun_matches_gold(session, patched, gold)


def run_label(response: dict) -> str:
    model = response.get("model", "")
    return model.rsplit("-", 1)[-1] if "-run" in model else model


def classify(session, item: dict, response: dict) -> dict:
    query, error = executed_query(response)
    anchor = graph_key(item["anchor"])
    gold = {key(row) for row in item["gold"]}
    given = {key(row) for row in response.get("rows") or []}
    detail = {"id": item["id"], "family": item["family"],
              "onlyInGold": sorted(gold - given)[:5], "onlyInResponse": sorted(given - gold)[:5]}
    if error:
        message = error.split("message:", 1)[-1].strip()
        return {**detail, "cause": "execution_error", "error": message[:200]}
    reads = property_reads(query)
    absent = absent_properties(session, reads)
    if absent:
        return {**detail, "cause": "property_absent_in_graph", "absentProperties": absent}
    repairs = omitted_value_repairs(session, query, item["gold"])
    if repairs:
        return {**detail, "cause": "filter_list_omits_stored_value", "repairs": repairs}
    repairs = dropped_filter_repairs(session, query, item["gold"])
    if repairs:
        return {**detail, "cause": "filter_list_excludes_gold_rows", "repairs": repairs}
    if canonical_meeting_repair(session, query, item["gold"]):
        return {**detail, "cause": "canonical_meeting_number_returned"}
    if item["family"] in SECTION_FAMILIES and any(
            "Section" in names and prop == "specNumber" for _, names, prop in reads):
        row = session.run(SECTIONS_OF[item["family"]], anchor=anchor).single()
        if row["missing"]:
            return {**detail, "cause": "section_spec_number_missing",
                    "sections": row["n"], "sectionsWithoutSpecNumber": row["missing"]}
    if item["family"] == "revision_chain":
        bounds = [int(n) for n in BOUNDED_WALK.findall(query)]
        distances = []
        for target in sorted({row[0] for row in item["gold"]}):
            found = session.run(REVISION_DISTANCE, anchor=anchor, target=target).single()
            distances.append(found["d"] if found else None)
        known = [d for d in distances if d is not None]
        if bounds and known and max(known) > min(bounds):
            return {**detail, "cause": "revision_walk_bound", "walkBound": min(bounds),
                    "longestGoldDistance": max(known)}
    return {**detail, "cause": "unclassified"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, nargs="+", required=True)
    parser.add_argument("--responses", type=Path, nargs="+", required=True)
    parser.add_argument("--bolt", action="append", required=True, help="WG=bolt URL, WG 마다 한 번")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    bolts = dict(entry.split("=", 1) for entry in args.bolt)
    items = {item["id"]: item for path in args.items for item in map(json.loads, path.read_text().splitlines())}
    by_wg: dict[str, list[dict]] = collections.defaultdict(list)
    for path in args.responses:
        for response in map(json.loads, path.read_text().splitlines()):
            if response["id"] in items:
                by_wg[response["wg"]].append(response)
    missing_bolt = sorted(set(by_wg) - set(bolts))
    if missing_bolt:
        raise SystemExit(f"그래프 주소가 없는 WG: {missing_bolt}")

    exact: dict[str, dict[str, list[int]]] = {}
    totals: dict[str, dict[str, list[int]]] = collections.defaultdict(
        lambda: {"answerable": [0, 0], "empty": [0, 0]})
    misses: list[dict] = []
    sections: dict[str, dict[str, int]] = {}
    for wg, responses in sorted(by_wg.items()):
        with GraphDatabase.driver(bolts[wg], auth=neo4j_auth()) as driver, driver.session() as session:
            row = session.run("MATCH (s:Section) RETURN count(s) AS n, "
                              "count(CASE WHEN s.specNumber IS NULL THEN 1 END) AS missing").single()
            sections[wg] = {"sectionNodes": row["n"], "sectionNodesWithoutSpecNumber": row["missing"]}
            for response in sorted(responses, key=lambda r: (run_label(r), r["id"])):
                item = items[response["id"]]
                run = run_label(response)
                hit = score(item["gold"], response.get("rows"))["exact"]
                cell = exact.setdefault(wg, {}).setdefault(run, [0, 0])
                cell[0] += hit
                cell[1] += 1
                part = totals[run]["answerable" if item["gold"] else "empty"]
                part[0] += hit
                part[1] += 1
                if not hit:
                    misses.append({"wg": wg, "run": run, **classify(session, item, response)})
    causes = collections.Counter((m["cause"], m["wg"], m["run"]) for m in misses)
    report = {
        "scope": "text2cypher responses scored against the current items; each missed item classified from its "
                 "executed query and the loaded graph",
        "exact": exact, "totals": dict(totals), "sections": sections,
        "byCause": [{"cause": c, "wg": w, "run": r, "items": n} for (c, w, r), n in sorted(causes.items())],
        "misses": misses,
    }
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("exact", "totals", "byCause")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
