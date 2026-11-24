"""절 단위 대상이 기록된 CR 의 범위를 작업반·release 별로 세고, 기록되지 않은 사유를 나눈다 (모델 호출 없음).

모집단 셋을 release 마다 센다.
- 전체 CR: 작업반 문서 목록이 유형 `CR` 로 적은 문서(`tdoc:type == "CR"`). `draftCR` · `pCR` 유형은
  묶음에 실리지 않으므로 빼며, `measure_traceability_denominators.py` 와 같은 정의다
- 총회 CR 묶음에 실린 CR
- 그중 절 단위 대상(`modifiesSection`)이 기록된 CR

묶음에 실렸는데 절 대상이 없는 CR 은 CR 서식의 `Clauses affected` 칸과 절 기록의 유무로 사유를 나눈다.
- form_not_read                       묶음 디렉터리에서 읽은 CR 서식이 없다
- clauses_cell_without_clause_number  서식의 칸이 비었거나 절 번호로 읽히는 표기가 없다
- spec_without_section_records        칸에 절 번호가 있으나 그 규격의 절 기록이 그래프에 하나도 없다
- clause_absent_from_section_records  규격의 절 기록은 있으나 칸의 절 번호와 같은 번호의 절 기록이 없다
- clause_present_in_section_records   같은 번호의 절 기록이 있는데 연결이 없다

절 대상이 있는 CR 은 연결된 절 기록의 release 가 CR 의 대상 release 와 같은지도 센다.
원문 대조를 통과한 처분 기록이 가리키는 CR 의 수는 `--phase2-root` 로 준 처분 기록으로 센다.

절 기록은 Phase-3 인스턴스 파일에서 읽고, 그 파일이 없는 작업반은 `--neo4j WG=PORT` 로 준
실행 중인 그래프에서 읽기 질의로 읽는다. 저장소 루트에서 실행한다.
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, "scripts/tsg/RAN/formal/common")
import cr_clause  # noqa: E402

INSTANCES = Path("ontology/output/tsg/RAN/formal/instances")
PARSED_CR = Path("ontology/output/tsg/RAN/formal/parsed_cr")
SECTIONS = "MATCH (s:Section)-[:BELONGS_TO_SPEC]->(:Spec) RETURN s.sectionId AS sid, s.sectionNumber AS num"
LIVE = """
MATCH (c:CR) WHERE c.type = 'CR'
OPTIONAL MATCH (c)-[:TARGET_RELEASE]->(r:Release)
WITH c, collect(r.id)[0] AS release
RETURN release, EXISTS{(c)-[:BELONGS_TO_CR_PACK]->()} AS pack,
       EXISTS{(c)-[:MODIFIES_SECTION]->()} AS section, count(*) AS n
"""


def as_list(value) -> list:
    return [] if value is None else value if isinstance(value, list) else [value]


def graph(path: Path) -> list[dict]:
    return json.loads(path.read_text())["@graph"]


def release_label(identifier: str | None) -> str:
    return identifier.rsplit("/", 1)[-1].replace("_", "-") if identifier else "release_not_recorded"


def split_section(section_id: str, number: str) -> tuple[str, str] | None:
    """절 기록 식별자 `{규격}-Rel-{N}-{절 번호}` 에서 (규격, release)."""
    stem = section_id.removeprefix("tdoc:section/")
    if not stem.endswith("-" + number) or "-Rel-" not in stem[: -(len(number) + 1)]:
        return None
    spec, tail = stem[: -(len(number) + 1)].rsplit("-Rel-", 1)
    return spec, f"Rel-{tail}"


def section_records(wg: str, live: dict[str, int]) -> tuple[list[tuple[str, str]], str]:
    path = INSTANCES / f"phase-3/{wg}/release-aware/sections.jsonld"
    if path.exists():
        return [(r["sectionId"], str(r["sectionNumber"])) for r in graph(path)
                if r.get("sectionId") and r.get("sectionNumber") not in (None, "")], str(path)
    if wg not in live:
        raise SystemExit(f"{wg}: {path} 가 없다. --neo4j {wg}=PORT 로 절 기록을 읽을 그래프를 준다.")
    return [(r["sid"], str(r["num"])) for r in query(live[wg], SECTIONS) if r["sid"] and r["num"] is not None], \
        f"bolt://localhost:{live[wg]} {SECTIONS}"


def query(port: int, cypher: str) -> list:
    sys.path.insert(0, "scripts/common")
    from common.credentials import neo4j_auth
    from neo4j import GraphDatabase

    with GraphDatabase.driver(f"bolt://localhost:{port}", auth=neo4j_auth()) as driver:
        return driver.execute_query(cypher).records


def measure(wg: str, phase2_root: Path | None, phase4_root: Path | None, live: dict[str, int]) -> dict:
    def phase4(name: str) -> Path:
        staged = phase4_root / wg / name if phase4_root else None
        return staged if staged and staged.exists() else INSTANCES / f"phase-4/{wg}/{name}"

    release_of = {r["@id"]: release_label(r.get("targetRelease"))
                  for r in graph(INSTANCES / f"phase-1/{wg}/tdocs.jsonld")
                  if r.get("@type") == "tdoc:CR" and r.get("tdoc:type") == "CR"}
    extensions = graph(phase4("cr_extensions.jsonld"))
    pack = {r["@id"] for r in extensions if r.get("belongsToCRPack")}
    sections = {r["@id"]: as_list(r["modifiesSection"]) for r in extensions if r.get("modifiesSection")}

    staged = phase2_root / wg / "decision_dispositions.jsonld" if phase2_root else None
    dispositions = staged if staged and staged.exists() else INSTANCES / f"phase-2/{wg}/decision_dispositions.jsonld"
    verified, verified_whole = set(), set()
    for r in graph(dispositions):
        if r.get("evidenceStatus") == "source_verified":
            verified.add(r["dispositionTarget"])
            if json.loads(r.get("assessmentMethod") or "{}").get("scope") == "whole_target":
                verified_whole.add(r["dispositionTarget"])

    records, section_source = section_records(wg, live)
    numbers_by_spec: dict[str, set[str]] = collections.defaultdict(set)
    for sid, num in records:
        parsed = split_section(sid, num)
        if parsed:
            numbers_by_spec[parsed[0]].add(num)

    data = json.loads((PARSED_CR / wg / "cr_documents.json").read_text())
    forms: dict[str, list[dict]] = collections.defaultdict(list)
    for form in data.get("cr_documents") or data.get("documents"):
        forms[f"tdoc:{form['tdoc_number']}"].append(form)

    def reason(cr: str) -> str:
        outcomes = set()
        for form in forms.get(cr, ()):
            written = [s for group in cr_clause.clause_candidates(form.get("clauses_affected") or "") for s in group]
            known = numbers_by_spec.get(form.get("spec_number") or "")
            outcomes.add("clauses_cell_without_clause_number" if not written
                         else "spec_without_section_records" if not known
                         else "clause_present_in_section_records" if known.intersection(written)
                         else "clause_absent_from_section_records")
        # 같은 CR 의 서식이 여럿이면 연결에 가장 가까운 사유를 고른다.
        for name in ("clause_present_in_section_records", "clause_absent_from_section_records",
                     "spec_without_section_records", "clauses_cell_without_clause_number"):
            if name in outcomes:
                return name
        return "form_not_read"

    def count(members) -> dict:
        members = list(members)
        in_pack = [c for c in members if c in pack]
        with_section = [c for c in in_pack if c in sections]
        edges = [(c, s) for c in with_section for s in sections[c]]
        same = sum(1 for c, s in edges if f"-{release_of[c]}-" in s)
        return {
            "cr": len(members),
            "crWithVerifiedDisposition": sum(c in verified for c in members),
            "crWithVerifiedWholeDocumentDisposition": sum(c in verified_whole for c in members),
            "crWithSection": sum(c in sections for c in members),
            "packCr": len(in_pack),
            "packCrWithVerifiedDisposition": sum(c in verified for c in in_pack),
            "packCrWithSection": len(with_section),
            "packCrWithVerifiedDispositionAndSection": sum(c in verified for c in with_section),
            "packCrWithoutSection": dict(collections.Counter(
                reason(c) for c in in_pack if c not in sections).most_common()),
            "sectionLinks": len(edges),
            "sectionLinksToSameReleaseRecord": same,
            "sectionLinksToOtherReleaseRecord": len(edges) - same,
        }

    by_release = collections.defaultdict(list)
    for cr, release in release_of.items():
        by_release[release].append(cr)
    out = {
        "sources": {"cr": str(INSTANCES / f"phase-1/{wg}/tdocs.jsonld"), "packAndSection": str(phase4("cr_extensions.jsonld")),
                    "dispositions": str(dispositions), "sectionRecords": section_source,
                    "crForms": str(PARSED_CR / wg / "cr_documents.json")},
        "sectionRecords": len(records),
        "specsWithSectionRecords": len(numbers_by_spec),
        "packRecordsNotClassifiedAsCr": sum(r["@id"] not in release_of for r in extensions if r.get("belongsToCRPack")),
        "packRecordsNotClassifiedAsCrWithSection": sum(
            r["@id"] not in release_of for r in extensions if r.get("belongsToCRPack") and r.get("modifiesSection")),
        "all": count(release_of),
        "byRelease": {release: count(by_release[release]) for release in
                      sorted(by_release, key=lambda x: (not x.startswith("Rel-"), int(x[4:]) if x[4:].isdigit() else 0))},
    }
    if wg in live:
        cells = collections.defaultdict(lambda: collections.Counter())
        for r in query(live[wg], LIVE):
            release = release_label(r["release"])
            cells[release]["cr"] += r["n"]
            cells[release]["packCr"] += r["n"] * r["pack"]
            cells[release]["packCrWithSection"] += r["n"] * (r["pack"] and r["section"])
        out["liveGraph"] = {"all": dict(sum(cells.values(), collections.Counter())),
                            "byRelease": {release: dict(cells[release]) for release in sorted(cells)}}
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--wg", nargs="+", default=["RAN1", "RAN2", "RAN3", "RAN4", "RAN5"])
    parser.add_argument("--phase2-root", type=Path, help="재구축 처분 기록의 뿌리. 파일이 있는 작업반만 그 파일을 쓴다")
    parser.add_argument("--phase4-root", type=Path, help="Phase-4 파일의 뿌리. 파일이 있는 작업반만 그 파일을 쓴다")
    parser.add_argument("--neo4j", action="append", default=[], metavar="WG=PORT")
    parser.add_argument("--compare", type=Path, help="앞서 잰 모집단 결과 JSON. 같은 이름의 수를 견준다")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    live = {wg: int(port) for wg, port in (item.split("=") for item in args.neo4j)}
    earlier = json.loads(args.compare.read_text()) if args.compare else {}
    result = {}
    for wg in args.wg:
        result[wg] = measure(wg, args.phase2_root, args.phase4_root, live)
        if wg in earlier:
            result[wg]["comparedWith"] = {"path": str(args.compare), "source": earlier[wg].get("source"), "values": {
                key: {"earlier": value, "now": result[wg]["all"].get(key),
                      "nowLiveGraph": result[wg].get("liveGraph", {}).get("all", {}).get(key)}
                for key, value in earlier[wg].items() if key != "source"}}
        total = result[wg]["all"]
        print(wg, {k: v for k, v in total.items()})
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
