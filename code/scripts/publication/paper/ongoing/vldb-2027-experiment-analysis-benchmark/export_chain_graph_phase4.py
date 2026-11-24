"""적재된 그래프에서 묶음·절 기록을 읽어 사슬 문항 스크립트가 읽는 JSON-LD 모양으로 내보낸다 (읽기 전용).

RAN5의 구축 공정은 파싱 결과를 곧바로 그래프에 적재하고 phase-4 인스턴스 JSON-LD를 만들지 않는다. 절 연결
(`MODIFIES_SECTION`)은 적재기가 그래프의 Section을 보고 정하므로 파싱 결과 파일에도 없다. 그래서 RAN5의
묶음·절 기록은 그래프에서만 얻을 수 있다. 이 스크립트는 그 기록을 `<out-root>/<WG>/` 아래 세 파일로 쓴다.
구축 공정의 인스턴스 파일이 아니므로 `ontology/output`에는 쓰지 않는다.

방향이 다른 간선을 따로 읽어 따로 쓴다. `build_chain_items.py`는 CR 쪽 기록을, `verify_chain_items.py`는
반대쪽 기록을 읽으므로 두 방향이 그래프에서 어긋나 있으면 통과 검사에서 드러난다.
- cr_extensions.jsonld       `(CR)-[:BELONGS_TO_CR_PACK]->(CRPack)` · `(CR)-[:MODIFIES_SECTION]->(Section)`
- crpacks.jsonld             `CRPack` 노드 · `(CRPack)-[:HAS_CR]->(CR)`
- section_extensions.jsonld  `(Section)-[:MODIFIED_BY_CR]->(CR)`

`--parsed-crpacks`를 주면 내보낸 묶음 소속과 총회 회의를 파싱 결과(`crpacks.json`)와 맞대어 차이를 기록한다.

사용: python3 export_chain_graph_phase4.py --wg RAN5 --bolt bolt://localhost:7691 --out-root <dir>
          [--parsed-crpacks ontology/output/tsg/RAN/formal/parsed_cr/RAN5/crpacks.json]
저장소 루트에서 `PYTHONPATH=scripts/common`으로 실행한다.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path

from neo4j import READ_ACCESS, GraphDatabase

from common.credentials import neo4j_auth

CONTEXT = {
    "@vocab": "https://w3id.org/spectra#", "tdoc": "https://w3id.org/spectra#",
    "hasCR": {"@id": "tdoc:hasCR", "@type": "@id"},
    "belongsToCRPack": {"@id": "tdoc:belongsToCRPack", "@type": "@id"},
    "modifiesSection": {"@id": "tdoc:modifiesSection", "@type": "@id"},
    "modifiedByCR": {"@id": "tdoc:modifiedByCR", "@type": "@id"},
}
QUERIES = {
    "packs": "MATCH (p:CRPack) RETURN p.crPackId, p.tsgMeeting",
    "has_cr": "MATCH (p:CRPack)-[:HAS_CR]->(c) RETURN p.crPackId, c.tdocNumber",
    "belongs_to_cr_pack": "MATCH (c)-[:BELONGS_TO_CR_PACK]->(p:CRPack) RETURN c.tdocNumber, p.crPackId",
    "modifies_section": "MATCH (c)-[:MODIFIES_SECTION]->(s:Section) RETURN c.tdocNumber, s.sectionId",
    "modified_by_cr": "MATCH (s:Section)-[:MODIFIED_BY_CR]->(c) RETURN s.sectionId, c.tdocNumber",
}


def grouped(pairs: list[tuple[str, str]]) -> dict[str, list[str]]:
    out: dict[str, set[str]] = collections.defaultdict(set)
    for key, value in pairs:
        out[key].add(value)
    return {key: sorted(values) for key, values in sorted(out.items())}


def references(prefix: str, values: list[str]):
    """참조가 하나면 문자열, 여럿이면 목록으로 적는다(다른 작업반의 인스턴스 파일과 같은 모양)."""
    ids = [f"{prefix}{value}" for value in values]
    return ids[0] if len(ids) == 1 else ids


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--wg", required=True)
    parser.add_argument("--bolt", required=True)
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--parsed-crpacks", type=Path, help="맞대어 볼 파싱 결과 crpacks.json")
    args = parser.parse_args()
    out_dir = args.out_root / args.wg
    out_dir.mkdir(parents=True, exist_ok=True)

    with GraphDatabase.driver(args.bolt, auth=neo4j_auth()) as driver, \
            driver.session(default_access_mode=READ_ACCESS) as session:
        rows = {name: [tuple(record.values()) for record in session.run(query)] for name, query in QUERIES.items()}
    for name, records in rows.items():
        missing = sum(1 for record in records if record[0] is None or (name != "packs" and record[1] is None))
        if missing:
            raise SystemExit(f"{name}: 키 속성이 빈 행 {missing}개 — 내보내지 않는다")

    tsg_of = dict(rows["packs"])
    has_cr = grouped(rows["has_cr"])
    belongs, modifies = grouped(rows["belongs_to_cr_pack"]), grouped(rows["modifies_section"])
    modified_by = grouped(rows["modified_by_cr"])

    graphs = {
        "cr_extensions.jsonld": [
            {"@id": f"tdoc:{cr}", "@type": "tdoc:CR",
             **({"belongsToCRPack": references("tdoc:crpack/", belongs[cr])} if cr in belongs else {}),
             **({"modifiesSection": references("tdoc:section/", modifies[cr])} if cr in modifies else {})}
            for cr in sorted(set(belongs) | set(modifies))],
        "crpacks.jsonld": [
            {"@id": f"tdoc:crpack/{pack}", "@type": "CRPack", "tdoc:crPackId": pack, "tdoc:tsgMeeting": tsg_of[pack],
             **({"hasCR": references("tdoc:", has_cr[pack])} if pack in has_cr else {})}
            for pack in sorted(tsg_of)],
        "section_extensions.jsonld": [
            {"@id": f"tdoc:section/{section}", "@type": "Section", "modifiedByCR": references("tdoc:", crs)}
            for section, crs in modified_by.items()],
    }
    files = {}
    for name, graph in graphs.items():
        text = json.dumps({"@context": CONTEXT, "@graph": graph}, ensure_ascii=False, indent=1) + "\n"
        (out_dir / name).write_text(text)
        files[name] = {"records": len(graph), "sha256": hashlib.sha256(text.encode()).hexdigest()}

    forward = {(cr, pack) for cr, packs in belongs.items() for pack in packs}
    backward = {(cr, pack) for pack, crs in has_cr.items() for cr in crs}
    section_forward = {(cr, section) for cr, sections in modifies.items() for section in sections}
    section_backward = {(cr, section) for section, crs in modified_by.items() for cr in crs}
    manifest = {
        "wg": args.wg, "bolt": args.bolt, "queries": QUERIES, "files": files,
        "graphRows": {name: len(records) for name, records in rows.items()},
        "packsWithoutTsgMeeting": sum(1 for meeting in tsg_of.values() if not meeting),
        "directionAgreement": {
            "packPairsOnlyInBelongsToCrPack": len(forward - backward),
            "packPairsOnlyInHasCr": len(backward - forward),
            "sectionPairsOnlyInModifiesSection": len(section_forward - section_backward),
            "sectionPairsOnlyInModifiedByCr": len(section_backward - section_forward)},
    }
    if args.parsed_crpacks:
        parsed = json.loads(args.parsed_crpacks.read_text())["packs"]
        parsed_pairs = {(cr, pack["crPackId"]) for pack in parsed for cr in pack.get("tdocNumbers", ())}
        parsed_tsg = {pack["crPackId"]: pack.get("tsgMeeting") for pack in parsed}
        manifest["parsedCrpacks"] = {
            "path": str(args.parsed_crpacks),
            "sha256": hashlib.sha256(args.parsed_crpacks.read_bytes()).hexdigest(),
            "packs": len(parsed_tsg), "memberPairs": len(parsed_pairs),
            "memberPairsOnlyInGraph": len(backward - parsed_pairs),
            "memberPairsOnlyInParsed": len(parsed_pairs - backward),
            "packsOnlyInGraph": len(set(tsg_of) - set(parsed_tsg)),
            "packsOnlyInParsed": len(set(parsed_tsg) - set(tsg_of)),
            "packsWithDifferentTsgMeeting": sum(
                1 for pack in set(tsg_of) & set(parsed_tsg) if tsg_of[pack] != parsed_tsg[pack])}
    (out_dir / "export_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: value for key, value in manifest.items() if key != "queries"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
