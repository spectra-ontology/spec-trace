"""추적 연결률을 모집단별로 나눠 센다 (모델 호출 없음).

CR 전체를 분모로 한 비율 하나 대신 세 모집단을 구분한다.
- 전체 CR: 작업반 문서 목록이 유형 `CR` 로 적은 문서(`tdoc:type == "CR"`)
- 총회 CR 묶음에 실린 CR: 그중 규격 반영 대상으로 총회 묶음에 올라간 CR
- 그중 절 단위 대상이 기록된 CR

문서 목록은 CR 양식을 쓰는 문서에 `CR` 외에 `draftCR` · `pCR` 유형도 적는다. 이 두 유형은
묶음에 실리지 않으므로 전체 CR 모집단에서 빼고 `otherListTypes` 에 따로 센다.
묶음이 싣는 문서 가운데 문서 목록에 없거나 목록이 다른 유형으로 적은 문서도 모집단 밖이며
`packListedOutsideList` 에 센다(인스턴스 JSON-LD 에서는 phase-1 목록에 `tdoc:CR` 로 없는
묶음 소속 확장 레코드, 그래프에서는 목록 유형 속성이 없는 CR 노드).

각 모집단에서 원문 대조를 통과한(`source_verified`) 처분 기록이 직접 가리키는 CR을 센다.

결의(Resolution) 기록도 같은 방식으로 나눈다(`resolutions`). 문서 하나에 대한 결정을 적은 결의는
대상 문서(`aboutTdoc`)를 가진다. 그 밖의 결의(합의 · 결론 · 작업 가정)는 기술적 결과를 적으며,
본문이 문서를 인용할 때만 `references` 를 가진다. 결의 하나를 문서 결정과 기술 결의 중 한쪽에만 센다.

RAN1~4는 인스턴스 JSON-LD에서, 인스턴스 파일이 없는 작업반은 `--neo4j WG=PORT`로 준
실행 중인 그래프에서 같은 정의로 센다. `--phase2-root` 를 주면 처분 기록과 결의를 그 디렉토리의
`{WG}/` 아래에서 읽는다(예: 목록 줄 재구축 전 첫 빌드의 phase-2 사본). 문서 목록과 묶음·절 기록은
그대로 인스턴스에서 읽는다. 저장소 루트에서 실행한다.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

INSTANCES = Path("ontology/output/tsg/RAN/formal/instances")
OUTSIDE = "outsideList"
CYPHER = """
MATCH (c:CR)
WITH coalesce(c.type, $outside) AS kind,
     EXISTS{(c)-[:BELONGS_TO_CR_PACK]->()} AS pack,
     EXISTS{(c)-[:MODIFIES_SECTION]->()} AS section,
     EXISTS{(d:DecisionDisposition)-[:DISPOSITION_TARGET]->(c)
            WHERE d.evidenceStatus = 'source_verified'} AS verified
RETURN kind, pack, section, verified, count(*) AS n
"""
RESOLUTION_CYPHER = """
MATCH (r:Resolution)
WITH [l IN labels(r) WHERE l <> 'Resolution'] AS kinds,
     EXISTS{(r)-[:ABOUT_TDOC]->()} AS about,
     EXISTS{(r)-[:REFERENCES]->()} AS cites
RETURN CASE WHEN size(kinds) = 0 THEN 'Resolution' ELSE kinds[0] END AS kind,
       about, cites, count(*) AS n
"""


def summarize_resolutions(cells: list[tuple[str, bool, bool, int]]) -> dict:
    """cells: (결의 유형, 대상 문서 있음, 문서 인용 있음, 건수)."""
    other: dict[str, dict[str, int]] = {}
    for kind, about, cites, n in cells:
        if about:
            continue
        entry = other.setdefault(kind, {"resolutions": 0, "citingDocument": 0})
        entry["resolutions"] += n
        entry["citingDocument"] += n if cites else 0
    return {"resolutions": sum(n for *_, n in cells),
            "aboutDocument": sum(n for _, about, _, n in cells if about),
            "otherByKind": other}


def summarize(cells: list[tuple[str, bool, bool, bool, int]], source: str) -> dict:
    """cells: (목록 유형, 묶음 소속, 절 기록, 확인된 처분, 건수)."""
    def total(kinds: set[str], keep) -> int:
        return sum(n for k, p, s, v, n in cells if k in kinds and keep(p, s, v))

    cr = {"CR"}
    others = sorted({k for k, *_ in cells} - cr - {OUTSIDE})
    return {
        "source": source,
        "cr": total(cr, lambda p, s, v: True),
        "crWithVerifiedDisposition": total(cr, lambda p, s, v: v),
        "crWithSection": total(cr, lambda p, s, v: s),
        "crWithVerifiedDispositionAndSection": total(cr, lambda p, s, v: s and v),
        "packCr": total(cr, lambda p, s, v: p),
        "packCrWithVerifiedDisposition": total(cr, lambda p, s, v: p and v),
        "packCrWithSection": total(cr, lambda p, s, v: p and s),
        "packCrWithVerifiedDispositionAndSection": total(cr, lambda p, s, v: p and s and v),
        "otherListTypes": {k: {"documents": total({k}, lambda p, s, v: True),
                               "withVerifiedDisposition": total({k}, lambda p, s, v: v),
                               "inPack": total({k}, lambda p, s, v: p),
                               "withSection": total({k}, lambda p, s, v: s)} for k in others},
        "packListedOutsideList": {
            "documents": total({OUTSIDE}, lambda p, s, v: p),
            "withVerifiedDisposition": total({OUTSIDE}, lambda p, s, v: p and v),
            "withSection": total({OUTSIDE}, lambda p, s, v: p and s)},
    }


def from_jsonld(wg: str, phase2: Path) -> dict:
    load = lambda rel: json.loads((INSTANCES / rel).read_text())["@graph"]
    kind = {r["@id"]: r.get("tdoc:type") or OUTSIDE
            for r in load(f"phase-1/{wg}/tdocs.jsonld") if r.get("@type") == "tdoc:CR"}
    dispositions = json.loads((phase2 / wg / "decision_dispositions.jsonld").read_text())["@graph"]
    verified = {r["dispositionTarget"] for r in dispositions if r["evidenceStatus"] == "source_verified"}
    extensions = load(f"phase-4/{wg}/cr_extensions.jsonld")
    pack = {r["@id"] for r in extensions if r.get("belongsToCRPack")}
    section = {r["@id"] for r in extensions if r.get("modifiesSection")}
    cells = [(k, c in pack, c in section, c in verified, 1) for c, k in kind.items()]
    cells += [(OUTSIDE, True, c in section, c in verified, 1) for c in pack - kind.keys()]
    resolutions = []
    for path in sorted((phase2 / wg).glob("resolutions_*.jsonld")):
        for r in json.loads(path.read_text())["@graph"]:
            types = [t for t in r["@type"] if t != "Resolution"]
            resolutions.append((types[0] if types else "Resolution",
                                bool(r.get("aboutTdoc")), bool(r.get("references")), 1))
    return {**summarize(cells, f"instance JSON-LD, phase-2 from {phase2}"),
            "resolutions": summarize_resolutions(resolutions)}


def from_neo4j(port: int) -> dict:
    sys.path.insert(0, "scripts/common")
    from common.credentials import neo4j_auth
    from neo4j import GraphDatabase

    with GraphDatabase.driver(f"bolt://localhost:{port}", auth=neo4j_auth()) as driver:
        rows = driver.execute_query(CYPHER, outside=OUTSIDE).records
        resolutions = driver.execute_query(RESOLUTION_CYPHER).records
    return {**summarize([(r["kind"], r["pack"], r["section"], r["verified"], r["n"]) for r in rows],
                        "live graph"),
            "resolutions": summarize_resolutions(
                [(r["kind"], r["about"], r["cites"], r["n"]) for r in resolutions])}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--neo4j", action="append", default=[], metavar="WG=PORT")
    parser.add_argument("--phase2-root", type=Path, default=INSTANCES / "phase-2")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    live = dict(item.split("=") for item in args.neo4j)
    result = {}
    for wg in ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5"):
        result[wg] = from_neo4j(int(live[wg])) if wg in live else from_jsonld(wg, args.phase2_root)
        print(wg, json.dumps(result[wg], ensure_ascii=False))
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
