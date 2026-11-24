"""교차 모델 질의 작성기(Codex)의 이전 응답이 놓친 문항을 값 형식 · 구조 · 기타로 가른다 (모델 호출 없음).

두 언어(그래프 질의 · 관계형 질의)의 저장된 응답을 `score_chain_eval.score` 로 다시 채점해 놓친 문항을 모은다.
놓친 문항 전부에 대해서는 기존 원인 조사(`diagnose_subagent_misses.py` · `diagnose_text2sql_misses.py` 가 쓴
`--census` 파일)의 원인을 읽어 세 갈래로 묶고, 놓친 문항 집합이 원인 조사 파일의 것과 같은지 대조한다.
그다음 (언어, WG, 문항 갈래) 층마다 `--per-stratum` 개(층이 더 작으면 전부)를 `--seed` 로 뽑아, 기존 분류 함수를
그 자리에서 다시 실행하고(그래프는 읽기 트랜잭션, 관계형 파일은 읽기 전용) 질의 안의 `IN` 목록 비교마다 목록에
적힌 문자열 가운데 저장값(같은 정규화 식을 저장값마다 계산한 값)에 없는 것과, 저장값 가운데 목록에 없는 것을 적는다.

세 갈래는 다음과 같다.

- value_format: 값 하나를 목록에 더하거나(filter_list_omits_stored_value), 값 비교 하나를 빼거나
  (filter_list_excludes_gold_rows), 회의 표기 속성을 바꾸면(canonical_meeting_number_returned) 응답이 정답과
  같아진다. 질의의 모양은 맞고 비교한 값의 형식만 저장값과 다르다. 고친 속성 · 열로 세부 갈래를 붙인다
  (scope · disposition_code · meeting_label · release · evidence_status · identifier).
- structural: 그래프에 없는 속성을 읽거나(property_absent_in_graph), 절 번호 속성이 빈 노드를 거치거나
  (section_spec_number_missing), 개정 사슬 경로 상한이 정답까지의 거리보다 짧다(revision_walk_bound).
- other: 실행 오류 · 실행 상한 · 위 어디에도 들지 않는 경우.

사용: python3 diagnose_codex_previous_misses.py --items <jsonl> [<jsonl> ...] \
          --cypher-responses <jsonl> [...] --sql-responses <jsonl> [...] \
          --cypher-census <json> --sql-census <json> --bolt RAN1=bolt://localhost:7687 [--bolt ...] \
          --sqlite-dir <dir> [--per-stratum 3] [--seed 20271] --out <json>
저장소 루트에서 `PYTHONPATH=scripts/common:scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark` 로 실행한다.
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import sqlite3
from pathlib import Path

from neo4j import GraphDatabase

import diagnose_subagent_misses as cy
import diagnose_text2sql_misses as sq
from common.credentials import neo4j_auth
from score_chain_eval import score

CLASS_OF = {
    "filter_list_omits_stored_value": "value_format",
    "filter_list_excludes_gold_rows": "value_format",
    "canonical_meeting_number_returned": "value_format",
    "property_absent_in_graph": "structural",
    "section_spec_number_missing": "structural",
    "revision_walk_bound": "structural",
    "execution_error": "other",
    "execution_deadline": "other",
    "unclassified": "other",
}
# 고친 속성(그래프) · 열(관계형)의 이름으로 값 형식 세부 갈래를 붙인다.
SUBCLASS_OF = {
    "resolutionScope": "scope", "scope": "scope",
    "dispositionCode": "disposition_code", "code": "disposition_code",
    "meetingNumber": "meeting_label", "canonicalMeetingNumber": "meeting_label", "label": "meeting_label",
    "releaseName": "release", "release": "release", "target_release": "release",
    "evidenceStatus": "evidence_status", "evidence_status": "evidence_status",
}


def read_jsonl(paths: list[Path]) -> list[dict]:
    return [json.loads(line) for path in paths for line in path.read_text().splitlines() if line.strip()]


def subclass(entry: dict) -> str | None:
    if entry["cause"] == "canonical_meeting_number_returned":
        return "meeting_label"
    repairs = entry.get("repairs") or []
    if not repairs:
        return None
    names = sorted({SUBCLASS_OF.get(r.get("property") or r.get("column"), "identifier") for r in repairs})
    return "+".join(names)


def cypher_literal_audit(session, query: str) -> list[dict]:
    """질의의 `<식> IN [목록]` 마다 목록 문자열 가운데 저장값에 없는 것과 저장값 가운데 목록에 없는 것."""
    out = []
    for match, span, names, prop, pattern, expression in cy.list_filters(query):
        listed = set(cy.LIST_LITERAL.findall(query[match.start(1):match.end(1)]))
        try:
            stored = {r["n"] for r in session.execute_read(lambda tx: list(tx.run(
                f"MATCH {pattern} WHERE x.`{prop}` IS NOT NULL WITH DISTINCT x.`{prop}` AS v "
                f"RETURN DISTINCT {expression} AS n", timeout=cy.RERUN_SECONDS)))}
        except Exception as error:
            out.append({"label": ":".join(names), "property": prop, "error": str(error)[:200]})
            continue
        stored = {v for v in stored if isinstance(v, str)}
        out.append({"label": ":".join(names), "property": prop, "expression": query[span[0]:span[1]],
                    "listed": sorted(listed), "listedNotStored": sorted(listed - stored),
                    "storedNotListed": sorted(stored - listed)[:20], "storedDistinct": len(stored)})
    return out


def sql_literal_audit(db, sql: str) -> list[dict]:
    out = []
    for match, span, table, column, expression in sq.list_filters(sql):
        listed = {v.replace("''", "'") for v in sq.LITERAL.findall(sql[match.start(1):match.end(1)])}
        try:
            stored = {n for (n,) in db.execute(
                f'SELECT DISTINCT {expression} FROM (SELECT DISTINCT "{column}" AS v FROM "{table}" '
                f'WHERE "{column}" IS NOT NULL)') if isinstance(n, str)}
        except sqlite3.Error as error:
            out.append({"table": table, "column": column, "error": str(error)[:200]})
            continue
        out.append({"table": table, "column": column, "expression": sql[span[0]:span[1]],
                    "listed": sorted(listed), "listedNotStored": sorted(listed - stored),
                    "storedNotListed": sorted(stored - listed)[:20], "storedDistinct": len(stored)})
    return out


def misses_of(items: dict, responses: list[dict]) -> list[dict]:
    out = []
    for response in responses:
        item = items[response["id"]]
        gold = sq.parsed(item["gold"])
        if not score(gold, sq.parsed(response.get("rows")))["exact"]:
            out.append(response)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, nargs="+", required=True)
    parser.add_argument("--cypher-responses", type=Path, nargs="+", required=True)
    parser.add_argument("--sql-responses", type=Path, nargs="+", required=True)
    parser.add_argument("--cypher-census", type=Path, required=True)
    parser.add_argument("--sql-census", type=Path, required=True)
    parser.add_argument("--census-run", default="codex-gpt-6.1-sol", help="원인 조사 파일에서 읽을 run 이름")
    parser.add_argument("--bolt", action="append", required=True, help="WG=bolt URL, WG 마다 한 번")
    parser.add_argument("--sqlite-dir", type=Path, required=True)
    parser.add_argument("--per-stratum", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20271)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    bolts = dict(entry.split("=", 1) for entry in args.bolt)
    items = {item["id"]: item for item in read_jsonl(args.items)}
    rng = random.Random(args.seed)

    report: dict = {
        "scope": "previous cross-model query-writer responses rescored against the current items; every miss "
                 "grouped from the existing per-item cause census, and a seeded stratified sample re-executed",
        "inputs": {"items": [str(p) for p in args.items],
                   "cypherResponses": [str(p) for p in args.cypher_responses],
                   "sqlResponses": [str(p) for p in args.sql_responses],
                   "cypherCensus": str(args.cypher_census), "sqlCensus": str(args.sql_census)},
        "sampling": {"perStratum": args.per_stratum, "seed": args.seed,
                     "stratum": "(language, wg, family) over missed items, ids sorted before sampling"},
        "languages": {},
    }
    for lang, paths, census_path in (("cypher", args.cypher_responses, args.cypher_census),
                                     ("sql", args.sql_responses, args.sql_census)):
        responses = [r for r in read_jsonl(paths) if r["id"] in items]
        misses = misses_of(items, responses)
        census = {m["id"]: m for m in json.loads(census_path.read_text())["misses"] if m["run"] == args.census_run}
        miss_ids = {r["id"] for r in misses}
        by_class = collections.Counter()
        by_sub = collections.Counter()
        by_class_family = collections.Counter()
        for response in misses:
            entry = census.get(response["id"])
            cls = CLASS_OF.get(entry["cause"], "other") if entry else "not_in_census"
            by_class[cls] += 1
            by_class_family[(cls, response["family"])] += 1
            if cls == "value_format":
                by_sub[subclass(entry)] += 1
        strata: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
        for response in misses:
            strata[(response["wg"], response["family"])].append(response)
        sample: list[dict] = []
        for key_ in sorted(strata):
            group = sorted(strata[key_], key=lambda r: r["id"])
            sample.extend(rng.sample(group, min(args.per_stratum, len(group))))

        rows: list[dict] = []
        by_wg: dict[str, list[dict]] = collections.defaultdict(list)
        for response in sample:
            by_wg[response["wg"]].append(response)
        for wg in sorted(by_wg):
            if lang == "cypher":
                driver = GraphDatabase.driver(bolts[wg], auth=neo4j_auth())
                session = driver.session(default_access_mode="READ")
                handle = session
            else:
                handle = sqlite3.connect(f"file:{args.sqlite_dir / f'{wg}.sqlite'}?mode=ro", uri=True)
            try:
                for response in sorted(by_wg[wg], key=lambda r: r["id"]):
                    item = items[response["id"]]
                    if lang == "cypher":
                        fresh = cy.classify(handle, item, response)
                        query, _ = cy.executed_query(response)
                        audit = cypher_literal_audit(handle, query)
                    else:
                        fresh = sq.classify(handle, item, response, None)
                        query, _ = sq.executed_query(response)
                        audit = sql_literal_audit(handle, query)
                    entry = census.get(response["id"])
                    rows.append({
                        "wg": wg, "id": response["id"], "family": response["family"],
                        "class": CLASS_OF.get(fresh["cause"], "other"), "cause": fresh["cause"],
                        "subclass": subclass(fresh) if CLASS_OF.get(fresh["cause"]) == "value_format" else None,
                        "censusCause": entry["cause"] if entry else None,
                        "agreesWithCensus": bool(entry and entry["cause"] == fresh["cause"]),
                        "repairs": fresh.get("repairs"), "inListAudit": audit,
                        "onlyInGold": fresh.get("onlyInGold"), "onlyInResponse": fresh.get("onlyInResponse"),
                    })
            finally:
                if lang == "cypher":
                    session.close()
                    driver.close()
                else:
                    handle.close()
        sample_class = collections.Counter(r["class"] for r in rows)
        sample_sub = collections.Counter(r["subclass"] for r in rows if r["subclass"])
        exact = len(responses) - len(misses)
        report["languages"][lang] = {
            "exact": [exact, len(responses)],
            "misses": len(misses),
            "censusCoverage": {"missesInCensus": len(miss_ids & set(census)),
                               "missesNotInCensus": sorted(miss_ids - set(census))[:20],
                               "censusEntriesNotMissedNow": sorted(set(census) - miss_ids)[:20]},
            "allMissesByClass": dict(by_class),
            "allMissesValueFormatBySubclass": dict(by_sub),
            "allMissesByClassFamily": [{"class": c, "family": f, "items": n}
                                       for (c, f), n in sorted(by_class_family.items())],
            "sample": {"strata": len(strata), "items": len(rows),
                       "byClass": dict(sample_class), "valueFormatBySubclass": dict(sample_sub),
                       "agreesWithCensus": [sum(r["agreesWithCensus"] for r in rows), len(rows)],
                       "strataSizes": {f"{w}/{f}": len(v) for (w, f), v in sorted(strata.items())}},
            "sampled": rows,
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({lang: {k: v for k, v in body.items() if k not in ("sampled", "allMissesByClassFamily")}
                      for lang, body in report["languages"].items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
