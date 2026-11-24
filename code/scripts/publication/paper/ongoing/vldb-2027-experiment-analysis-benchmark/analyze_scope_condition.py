"""처분 기록의 "원문 확인 · 문서 전체" 조건이 문항마다 정답을 바꾸는지와, 성공한 질의가 그 조건을 걸었는지 잰다 (모델 호출 없음).

무엇을 재는가.
- 문항 민감도: 처분 조건이 들어 있는 다섯 종류(`disposition_pack` · `full_chain` · `revision_chain` · `clause_history` ·
  `pack_origin`, 481 문항)마다 참조 질의를 네 벌로 실행해 결과 행 집합이 gold 와 같은지 본다.
  `base`(조건 그대로) · `drop_both`(두 조건 모두 뺌) · `drop_evidence`(원문 확인 조건만 뺌) · `drop_scope`(문서 전체 조건만 뺌).
  관계형 쪽은 `measure_relational_equivalence.SQL` 의 `cr_side` 질의에서 `VERIFIED` 식을 바꾸어 넣고
  `integration/sqlite_final/RAN{N}.sqlite` 에 읽기 전용으로 실행한다.
  그래프 쪽은 `crosscheck_chain_items_graph.CYPHER` 에서 `{evidenceStatus: 'source_verified'}` 속성 조건과
  `assessmentMethod` 의 `"scope": "whole_target"` WHERE 줄을 지우고 작업반별 Neo4j 에 읽기 세션으로 실행한다.
  비교는 원래 스크립트들처럼 결과 행 튜플 집합과 gold 행 튜플 집합의 완전 일치다.
- 기록 분포: 두 저장소에서 처분 기록을 (원문 확인 상태, 범위) 로 센다. 그래프는 범위를 `assessmentMethod` JSON 에서 읽고
  `Resolution.resolutionScope` 도 함께 센다.
- 성공 질의 분류: Opus Text2Cypher · Text2SQL 실행 A~J(와 Codex 두 번째 판 네 조건)의 응답 중 위 다섯 종류에서
  회의 동일성 규칙(`score_meeting_spelling_sensitivity` 의 `same_meeting`: 회의 칸 끝 `-e` 를 양쪽에서 떼되 기록이 두
  표기를 따로 담은 회의 이름은 그대로 둔다)으로 정답인 것의 최종 질의(`attempts[-1]`)를
  낱말 단위로 나눈다. SQL 은 `evidence_status` 와 `scope` 열 이름, Cypher 는 `evidenceStatus` · `assessmentMethod` ·
  `resolutionScope` 속성 이름이 질의 문자열 안에 있는지로 본다(조건절인지 반환 열인지는 가리지 않는다).
  이 분류를 각 언어가 실행되는 저장소의 문항 민감도와 교차해, 조건을 걸지 않은 질의가 민감한 문항에서 성공했는지 센다.
  질의 문자열에 `verif` · `whole` 조각이 있는지도 대소문자 없이 따로 센다.

사용 (저장소 루트에서, Neo4j RAN1~RAN5 가 7687~7691 에 떠 있어야 한다):
    .venv/bin/python3 -I scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/analyze_scope_condition.py [--out <json>]
기본 출력은 `final/next_cycle/analysis/m12_scope_condition.json` 이다.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(path for path in HERE.parents if (path / ".git").exists())
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "scripts" / "common"))

from neo4j import GraphDatabase  # noqa: E402

from common.credentials import neo4j_auth  # noqa: E402
from crosscheck_chain_items_graph import CYPHER, graph_key  # noqa: E402
from measure_relational_equivalence import SQL, VARIANTS, VERIFIED  # noqa: E402
from score_meeting_spelling_sensitivity import exact, make_row_key, separately_recorded_meetings  # noqa: E402

TRACK = "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
CE = f"{TRACK}/chain_eval"
ITEMS = [f"{TRACK}/integration/items_final/gate/core/chain_items_admitted.jsonl",
         f"{TRACK}/integration/items_final/gate/ran5/chain_items_admitted.jsonl"]
SQLITE = f"{TRACK}/integration/sqlite_final"
DEFAULT_OUT = f"{TRACK}/final/next_cycle/analysis/m12_scope_condition.json"
WGS = [f"RAN{n}" for n in range(1, 6)]
BOLT = {wg: f"bolt://localhost:{7686 + n}" for n, wg in enumerate(WGS, start=1)}
FAMILIES = ("disposition_pack", "full_chain", "revision_chain", "clause_history", "pack_origin")
RUNS = "ABCDEFGHIJ"

SQL_CONDITION = {"base": VERIFIED, "drop_both": "1 = 1",
                 "drop_evidence": "d.scope = 'whole_target'",
                 "drop_scope": "d.evidence_status = 'source_verified'"}
GRAPH_EVIDENCE = " {evidenceStatus: 'source_verified'}"
GRAPH_SCOPE = """WHERE d.assessmentMethod CONTAINS '"scope": "whole_target"'"""
GRAPH_DROPS = {"base": (), "drop_both": (GRAPH_EVIDENCE, GRAPH_SCOPE),
               "drop_evidence": (GRAPH_EVIDENCE,), "drop_scope": (GRAPH_SCOPE,)}
SCOPE_IN_METHOD = re.compile(r'"scope":\s*"([^"]+)"')


def sql_query(family: str, variant: str) -> str:
    text = SQL[family].format(**VARIANTS["cr_side"])
    assert text.count(VERIFIED) == 1, family
    return text.replace(VERIFIED, SQL_CONDITION[variant])


def graph_query(family: str, variant: str) -> str:
    text = CYPHER[family]
    for piece in GRAPH_DROPS[variant]:
        assert text.count(piece) == 1, (family, piece)
        text = text.replace(piece, "")
    return text


def responses(pattern: str) -> dict[str, dict]:
    out = {}
    for wg in WGS:
        for line in (ROOT / pattern.format(wg=wg)).read_text().splitlines():
            if line.strip():
                record = json.loads(line)
                out[record["id"]] = record
    return out


def classify(language: str, query: str) -> str:
    """최종 질의 문자열이 가리키는 조건 속성으로 나눈 부류."""
    if language == "sql":
        evidence = re.search(r"evidence_status", query, re.I) is not None
        scope = re.search(r"\bscope\b", query, re.I) is not None
        return {(True, True): "evidence_and_scope", (True, False): "evidence_only",
                (False, True): "scope_only", (False, False): "neither"}[(evidence, scope)]
    evidence = "evidenceStatus" in query
    method = "assessmentMethod" in query
    resolution = "resolutionScope" in query
    if method:
        return "evidence_and_assessmentMethod" if evidence else "assessmentMethod_only"
    if resolution:
        return "evidence_and_resolutionScope" if evidence else "resolutionScope_only"
    return "evidence_only" if evidence else "neither"


def reads_condition_attribute(label: str) -> bool:
    """부류가 처분 기록의 원문 확인 상태나 범위 속성을 하나라도 읽는가. `resolutionScope` 는 결정 쪽 속성이라 세지 않는다."""
    return label not in ("neither", "resolutionScope_only")


VERIFIED_LITERAL = re.compile(r"verif", re.I)
WHOLE_LITERAL = re.compile(r"whole", re.I)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, default=ROOT / DEFAULT_OUT)
    args = parser.parse_args()

    items = {}
    for path in ITEMS:
        for line in (ROOT / path).read_text().splitlines():
            item = json.loads(line)
            items[item["id"]] = item
    target = sorted(i for i, item in items.items() if item["family"] in FAMILIES)
    kept = separately_recorded_meetings()
    identity_key = make_row_key("same_meeting", kept)

    # 문항 민감도: SQLite
    databases = {wg: sqlite3.connect(f"file:{ROOT / SQLITE / (wg + '.sqlite')}?mode=ro", uri=True) for wg in WGS}
    sensitivity: dict[str, dict] = {i: {"family": items[i]["family"], "wg": items[i]["wg"], "sql": {}, "graph": {}}
                                    for i in target}
    for identifier in target:
        item = items[identifier]
        gold = {tuple(row) for row in item["gold"]}
        for variant in SQL_CONDITION:
            rows = {tuple(row) for row in databases[item["wg"]].execute(sql_query(item["family"], variant),
                                                                         {"anchor": item["anchor"]})}
            sensitivity[identifier]["sql"][variant] = {"equalsGold": rows == gold, "rows": len(rows),
                                                       "extraRows": len(rows - gold), "lostRows": len(gold - rows)}
    record_counts = {"sql": {}, "graph": {}}
    for wg, db in databases.items():
        record_counts["sql"][wg] = [list(row) for row in db.execute(
            "SELECT evidence_status, scope, count(*) FROM disposition GROUP BY 1, 2 ORDER BY 1, 2")]

    # 문항 민감도: Neo4j
    for wg in WGS:
        with GraphDatabase.driver(BOLT[wg], auth=neo4j_auth()) as driver, \
                driver.session(default_access_mode="READ") as session:
            for identifier in (i for i in target if items[i]["wg"] == wg):
                item = items[identifier]
                gold = {tuple(row) for row in item["gold"]}
                for variant in GRAPH_DROPS:
                    rows = {tuple(r.values()) for r in session.run(graph_query(item["family"], variant),
                                                                    anchor=graph_key(item["anchor"]))}
                    sensitivity[identifier]["graph"][variant] = {"equalsGold": rows == gold, "rows": len(rows),
                                                                 "extraRows": len(rows - gold),
                                                                 "lostRows": len(gold - rows)}
            tally = collections.Counter()
            for row in session.run("MATCH (d:DecisionDisposition)-[:DISPOSITION_OF]->(r:Resolution) "
                                   "RETURN d.evidenceStatus AS e, d.assessmentMethod AS a, r.resolutionScope AS s"):
                scope = SCOPE_IN_METHOD.search(row["a"] or "")
                tally[(row["e"], scope.group(1) if scope else None, row["s"])] += 1
            unlinked = session.run("MATCH (d:DecisionDisposition) WHERE NOT (d)-[:DISPOSITION_OF]->(:Resolution) "
                                   "RETURN count(d) AS n").single()["n"]
            record_counts["graph"][wg] = {"byEvidenceScopeResolutionScope": [[*k, n] for k, n in sorted(
                tally.items(), key=lambda kv: tuple(str(x) for x in kv[0]))], "dispositionsWithoutResolution": unlinked}

    def sensitive(identifier: str, store: str, variant: str) -> bool:
        return not sensitivity[identifier][store][variant]["equalsGold"]

    summary = {}
    for store in ("sql", "graph"):
        base_ok = sum(sensitivity[i][store]["base"]["equalsGold"] for i in target)
        by_family = {}
        for family in FAMILIES:
            members = [i for i in target if items[i]["family"] == family]
            by_family[family] = {"items": len(members), **{
                variant: sum(sensitive(i, store, variant) for i in members) for variant in SQL_CONDITION
                if variant != "base"}}
            by_family[family]["dropBothSharePercent"] = round(100 * by_family[family]["drop_both"] / len(members), 1)
        summary[store] = {"items": len(target), "baseEqualsGold": base_ok,
                          **{variant: sum(sensitive(i, store, variant) for i in target)
                             for variant in SQL_CONDITION if variant != "base"},
                          "byFamily": by_family,
                          "sensitiveItemsDropBoth": [i for i in target if sensitive(i, store, "drop_both")]}
    agreement = collections.Counter((sensitive(i, "sql", "drop_both"), sensitive(i, "graph", "drop_both"))
                                    for i in target)

    # 성공 질의 분류
    conditions = {f"claude_text2cypher_run{r}": ("cypher", f"{CE}/{{wg}}_text2cypher_claude_subagent_run{r}.jsonl")
                  for r in RUNS}
    conditions.update({f"claude_text2sql_run{r}": ("sql", f"{CE}/text2sql/{{wg}}_text2sql_run{r}.jsonl") for r in RUNS})
    conditions.update({f"codex_v2_{k}": ("cypher" if k.startswith("cy") else "sql",
                                         f"{CE}/codex_v2/responses/{{wg}}_{k}_codex.jsonl")
                       for k in ("cy_dom", "cy_exp", "sql_dom", "sql_exp")})
    sha = {i: hashlib.sha256(items[i]["question"].encode()).hexdigest() for i in target}
    crosstab: dict[str, dict] = {}
    unfiltered_on_sensitive = []
    for name, (language, pattern) in conditions.items():
        store = "graph" if language == "cypher" else "sql"
        records = responses(pattern)
        table = collections.defaultdict(collections.Counter)
        for identifier in target:
            record = records.get(identifier)
            if record is None or record.get("questionSha256") != sha[identifier]:
                table["missingOrStale"]["n"] += 1
                continue
            ok = exact(items[identifier], record.get("rows"), identity_key)
            query = record["attempts"][-1][language]
            label = classify(language, query)
            outcome = "success" if ok else "failure"
            for variant in ("drop_both", "drop_scope", "drop_evidence"):
                key = f"{outcome}|{label}|{variant}:{'sensitive' if sensitive(identifier, store, variant) else 'insensitive'}"
                table[key]["n"] += 1
            table[f"{outcome}|literal verif={bool(VERIFIED_LITERAL.search(query))}|"
                  f"whole={bool(WHOLE_LITERAL.search(query))}"]["n"] += 1
            if ok and not reads_condition_attribute(label):
                table[f"success|no condition attribute|drop_both:"
                      f"{'sensitive' if sensitive(identifier, store, 'drop_both') else 'insensitive'}"]["n"] += 1
            if ok and not reads_condition_attribute(label) and sensitive(identifier, store, "drop_both"):
                unfiltered_on_sensitive.append({"condition": name, "id": identifier, "class": label,
                                                "family": items[identifier]["family"]})
        crosstab[name] = {"language": language, "store": store,
                          "cells": {k: c["n"] for k, c in sorted(table.items())}}

    def pooled(prefix: str) -> dict:
        cells = collections.Counter()
        for name, info in crosstab.items():
            if name.startswith(prefix):
                cells.update(info["cells"])
        return dict(sorted(cells.items()))

    report = {
        "families": FAMILIES, "items": len(target),
        "comparison": "set of result row tuples equals set of gold row tuples (as in the reference scripts)",
        "sqlConditions": SQL_CONDITION,
        "graphRemovedPieces": {k: list(v) for k, v in GRAPH_DROPS.items()},
        "recordCounts": record_counts,
        "itemSensitivity": summary,
        "sqlGraphAgreementDropBoth": {f"sql={a}|graph={b}": n for (a, b), n in sorted(agreement.items())},
        "perItem": sensitivity,
        "successQueryClasses": {
            "rule": "identity (score_meeting_spelling_sensitivity same_meeting: trailing '-e' removed from meeting "
                    "cells on both sides except names the records hold as a separate meeting); final query "
                    "attempts[-1]",
            "keptElectronicSpellings": sorted(kept),
            "sqlClasses": "evidence_status / \\bscope\\b column names present in the query text",
            "cypherClasses": "evidenceStatus / assessmentMethod / resolutionScope property names present in the "
                             "query text",
            "store": "Cypher classes crossed with graph-side item sensitivity, SQL classes with SQLite-side",
            "perCondition": crosstab,
            "pooledOpusCypherRunsAtoJ": pooled("claude_text2cypher"),
            "pooledOpusSqlRunsAtoJ": pooled("claude_text2sql"),
            "pooledCodexV2Cypher": pooled("codex_v2_cy"),
            "pooledCodexV2Sql": pooled("codex_v2_sql"),
            "literalFlags": "'verif' and 'whole' substrings anywhere in the final query, case-insensitive",
            "successesWithoutConditionAttributeOnSensitiveItems": unfiltered_on_sensitive,
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    for store, row in summary.items():
        print(store, {k: v for k, v in row.items() if k not in ("byFamily", "sensitiveItemsDropBoth")})
        for family, counts in row["byFamily"].items():
            print("  ", family, counts)
    print("agreement", report["sqlGraphAgreementDropBoth"])
    print("successes without a condition attribute on sensitive items", len(unfiltered_on_sensitive))


if __name__ == "__main__":
    main()
