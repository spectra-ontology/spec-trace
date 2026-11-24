"""추적 사슬 문항의 정답을 적재된 Neo4j 그래프에서 Cypher로 다시 구해 맞댄다 (모델 호출 없음).

`verify_chain_items.py`는 인스턴스 JSON-LD에서 정답을 다시 구한다. 이 검사는 같은 문항을 적재가 끝난
그래프에 물어, 파일로 구한 정답과 그래프가 돌려주는 답이 같은지 본다. 문항 종류마다 Cypher가 하나씩 있고,
이 Cypher는 문항과 함께 공개하는 참조 질의다. 실행 중인 WG 인스턴스에만 접속하며 읽기 전용이다.
절 단위 종류(`clause_neighbours`·`first_change`·`previous_pack`)의 Cypher 는 `CLAUSE_SET_CYPHER` 에 따로 두고,
그 종류의 문항이 입력에 있을 때만 실행하고 보고의 참조 질의에 싣는다. 총회 회의의 앞뒤는 `RAN#n` 표기의 번호로 정한다.

사용: python3 crosscheck_chain_items_graph.py --items <jsonl> --wg RAN4 --bolt bolt://localhost:7690 --out <json>
저장소 루트에서 `PYTHONPATH=scripts/common`으로 실행한다.
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

from neo4j import GraphDatabase

from common.credentials import neo4j_auth

# 원문 대조를 통과하고 문서 전체를 대상으로 한 처분 기록과 그 결정이 내려진 회의.
DISPOSITION = """
    MATCH (cr)<-[:DISPOSITION_TARGET]-(d:DecisionDisposition {evidenceStatus: 'source_verified'})
          -[:DISPOSITION_OF]->(:Resolution)-[:MADE_AT]->(m:Meeting)
    WHERE d.assessmentMethod CONTAINS '"scope": "whole_target"'"""
PACK = "MATCH (cr)-[:BELONGS_TO_CR_PACK]->(p:CRPack)"
CYPHER = {
    "pack_lookup": f"MATCH (cr:CR {{tdocNumber: $anchor}}) {PACK} RETURN DISTINCT p.crPackId, p.tsgMeeting",
    "disposition_pack": f"""MATCH (cr:CR {{tdocNumber: $anchor}}) {DISPOSITION} {PACK}
        RETURN DISTINCT d.dispositionCode, m.meetingNumber, p.crPackId, p.tsgMeeting""",
    "full_chain": f"""MATCH (cr:CR {{tdocNumber: $anchor}}) {DISPOSITION} {PACK}
        MATCH (cr)-[:MODIFIES_SECTION]->(s:Section)
        RETURN DISTINCT d.dispositionCode, m.meetingNumber, p.crPackId, p.tsgMeeting, s.sectionNumber""",
    "revision_chain": f"""MATCH (:CR {{tdocNumber: $anchor}})<-[:IS_REVISION_OF*1..]-(cr) {DISPOSITION} {PACK}
        RETURN DISTINCT cr.tdocNumber, d.dispositionCode, p.crPackId""",
    "clause_history": f"""MATCH (:Section {{sectionId: $anchor}})<-[:MODIFIES_SECTION]-(cr)
        MATCH (cr)-[:TARGET_RELEASE]->(release:Release) WHERE $anchor CONTAINS ('-' + release.releaseName + '-')
        {DISPOSITION} {PACK}
        RETURN DISTINCT cr.tdocNumber, d.dispositionCode, m.meetingNumber, p.crPackId""",
    "pack_origin": f"""MATCH (:CRPack {{crPackId: $anchor}})-[:HAS_CR]->(cr) {DISPOSITION}
        RETURN DISTINCT cr.tdocNumber, d.dispositionCode, m.meetingNumber""",
}
CYPHER["pack_lookup_empty"] = CYPHER["pack_lookup"]
# 절 단위 종류. 대상 CR·묶음의 CR 이 자기 대상 release 판본에서 고친 절만 따라가고(절 식별자에 release 가 들어 있다),
# 같은 절을 고친 다른 CR 도 같은 release 를 대상으로 한 것만 본다.
OWN_RELEASE_SECTION = """
    MATCH (cr)-[:TARGET_RELEASE]->(release:Release)
    MATCH (cr)-[:MODIFIES_SECTION]->(s:Section) WHERE s.sectionId CONTAINS ('-' + release.releaseName + '-')"""
TSG_NUMBER = "toInteger(substring({pack}.tsgMeeting, 4))"
CLAUSE_SET_CYPHER = {
    "clause_neighbours": f"""MATCH (x:CR {{tdocNumber: $anchor}})-[:TARGET_RELEASE]->(release:Release)
        MATCH (x)-[:MODIFIES_SECTION]->(s:Section) WHERE s.sectionId CONTAINS ('-' + release.releaseName + '-')
        MATCH (s)<-[:MODIFIES_SECTION]-(cr)-[:TARGET_RELEASE]->(other:Release)
        WHERE cr <> x AND other.releaseName = release.releaseName
        {DISPOSITION} {PACK}
        RETURN DISTINCT s.sectionNumber, cr.tdocNumber, d.dispositionCode, m.meetingNumber, p.crPackId""",
    "first_change": f"""MATCH (p:CRPack {{crPackId: $anchor}})-[:HAS_CR]->(cr) {DISPOSITION} {OWN_RELEASE_SECTION}
        WITH DISTINCT p, cr, s, release
        WHERE NOT EXISTS {{
            MATCH (s)<-[:MODIFIES_SECTION]-(e)-[:TARGET_RELEASE]->(er:Release)
            MATCH (e)-[:BELONGS_TO_CR_PACK]->(ep:CRPack)
            WHERE er.releaseName = release.releaseName
              AND {TSG_NUMBER.format(pack="ep")} < {TSG_NUMBER.format(pack="p")} }}
        RETURN DISTINCT cr.tdocNumber, s.specNumber, s.sectionNumber""",
    "previous_pack": f"""MATCH (p:CRPack {{crPackId: $anchor}})-[:HAS_CR]->(cr) {DISPOSITION} {OWN_RELEASE_SECTION}
        WITH DISTINCT p, s, release
        MATCH (s)<-[:MODIFIES_SECTION]-(e)-[:TARGET_RELEASE]->(er:Release) WHERE er.releaseName = release.releaseName
        MATCH (e)-[:BELONGS_TO_CR_PACK]->(ep:CRPack)
        WHERE {TSG_NUMBER.format(pack="ep")} < {TSG_NUMBER.format(pack="p")}
        WITH s, max({TSG_NUMBER.format(pack="ep")}) AS latest, collect(DISTINCT ep) AS earlier
        UNWIND earlier AS ep
        WITH s, ep, latest WHERE {TSG_NUMBER.format(pack="ep")} = latest
        RETURN DISTINCT s.specNumber, s.sectionNumber, ep.crPackId, ep.tsgMeeting""",
}


def graph_key(anchor: str) -> str:
    """인스턴스 IRI에서 그래프 노드의 키 속성 값을 얻는다."""
    for prefix in ("tdoc:section/", "tdoc:crpack/", "tdoc:"):
        if anchor.startswith(prefix):
            return anchor[len(prefix):]
    return anchor


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, required=True)
    parser.add_argument("--wg", required=True)
    parser.add_argument("--bolt", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    items = [item for item in map(json.loads, args.items.read_text().splitlines()) if item["wg"] == args.wg]
    present = {item["family"] for item in items}
    queries = {**CYPHER, **{family: text for family, text in CLAUSE_SET_CYPHER.items() if family in present}}
    counts: collections.Counter[tuple[str, str]] = collections.Counter()
    differing = []
    with GraphDatabase.driver(args.bolt, auth=neo4j_auth()) as driver, driver.session() as session:
        for item in items:
            rows = session.run(queries[item["family"]], anchor=graph_key(item["anchor"]))
            from_graph = sorted(tuple(row.values()) for row in rows)
            gold = sorted(tuple(row) for row in item["gold"])
            same = from_graph == gold
            counts[(item["family"], "same" if same else "differs")] += 1
            if not same:
                differing.append({"id": item["id"], "onlyInGold": sorted(set(gold) - set(from_graph))[:5],
                                  "onlyInGraph": sorted(set(from_graph) - set(gold))[:5]})
    report = {"wg": args.wg, "checked": len(items),
              "same": sum(n for (_, result), n in counts.items() if result == "same"),
              "byFamily": [{"family": f, "result": r, "n": n} for (f, r), n in sorted(counts.items())],
              "referenceCypher": {family: " ".join(text.split()) for family, text in queries.items()},
              "differing": differing}
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("wg", "checked", "same", "byFamily")}, ensure_ascii=False))
    for row in differing[:8]:
        print(row)


if __name__ == "__main__":
    main()
