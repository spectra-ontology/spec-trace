"""재유도 답이 정답과 어긋난 문항마다, 어긋난 행에 나온 문서·회의·CR 묶음·절을 기록 파일에서 직접 찾아 적는다 (모델 호출 없음).

`score_fresh_rederivation.py score` 가 쓴 결과에서 고른 답 묶음의 어긋난 문항을 읽는다. 문항마다 다음을 기록에서 찾는다.
  - 문서: 기준 문서(anchor 가 문서일 때)와 어긋난 행(정답에만 있는 행, 답에만 있는 행)의 문서 칸 값, 그리고 이들에서
    `isRevisionOf`·`revisedTo` 로 이어지는 문서 전부. 문서마다 `tdoc:status`, 발표 회의(`presentedAt` 의 meetingNumber),
    `tdoc:tsgCRPack`, 개정 연결, 대상 release, 처분 기록(처분 코드·근거 상태·판정 범위·결정 회의), 그 문서를 담은 CR 묶음과
    TSG 회의, 그 문서가 고치는 절.
  - 회의: 어긋난 행의 `wg_meeting` 값과 같은 meetingNumber 또는 canonicalMeetingNumber 를 가진 회의 기록.
  - CR 묶음: anchor 가 CR 묶음일 때와 어긋난 행의 `cr_pack` 값의 묶음 기록(TSG 회의, 담긴 CR 수).
  - 절: anchor 가 절일 때 그 절을 고치는 CR.
행 비교는 `score_chain_eval.cell_key()` 기준이다. 이 스크립트는 사실만 모으고 갈래를 다시 매기지 않는다.

사용 (저장소 루트에서 `PYTHONPATH=scripts/common:<이 폴더>`):
  python3 verify_fresh_rederivation_disagreements.py --result <score result.json> --sets <이름> [...] \
      --items <admitted.jsonl> [...] --out <json>
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

from score_chain_eval import cell_key

INSTANCES = "ontology/output/tsg/RAN/formal/instances"
RAN5_EXPORT = "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/RAN5_graph_export/RAN5"
DOCUMENT_FIELDS = ("document", "final_document")


def graph(path: str) -> list[dict]:
    with open(path) as handle:
        return json.load(handle)["@graph"]


def as_list(value) -> list:
    return [] if value is None else value if isinstance(value, list) else [value]


def bare(iri) -> str:
    return str(iri).removeprefix("tdoc:")


def differing(item: dict, disagreement: dict) -> tuple[list, list]:
    gold = {tuple(map(cell_key, row)): row for row in disagreement["gold"]}
    given = {tuple(map(cell_key, row)): row for row in disagreement["answer"] or []}
    return ([gold[k] for k in sorted(set(gold) - set(given))], [given[k] for k in sorted(set(given) - set(gold))])


def verify_wg(wg: str, cases: list[dict]) -> list[dict]:
    phase4 = RAN5_EXPORT if wg == "RAN5" else f"{INSTANCES}/phase-4/{wg}"
    meetings = graph(f"{INSTANCES}/phase-1/{wg}/meetings.jsonld")
    meeting_name = {m["@id"]: m.get("tdoc:meetingNumber") for m in meetings}
    tdocs = {r["tdoc:tdocNumber"]: r for r in graph(f"{INSTANCES}/phase-1/{wg}/tdocs.jsonld")}
    wanted: set[str] = set()
    for case in cases:
        closure: set[str] = set()
        seeds = set(case["documents"])
        while seeds:
            number = seeds.pop()
            if number in closure:
                continue
            closure.add(number)
            record = tdocs.get(number, {})
            seeds |= {bare(v) for key in ("isRevisionOf", "revisedTo") for v in as_list(record.get(key))} - closure
        case["closure"] = sorted(closure)
        wanted |= closure
    documents = {number: tdocs.get(number) for number in wanted}
    del tdocs
    dispositions = collections.defaultdict(list)
    for record in graph(f"{INSTANCES}/phase-2/{wg}/decision_dispositions.jsonld"):
        if record.get("targetTdocNumber") in wanted:
            dispositions[record["targetTdocNumber"]].append(record)
    resolutions_needed = {bare(r["dispositionOf"]) for rows in dispositions.values() for r in rows}
    made_at = {}
    for path in sorted(Path(f"{INSTANCES}/phase-2/{wg}").glob("*.jsonld")):
        if path.name == "decision_dispositions.jsonld":
            continue
        for record in graph(str(path)):
            if bare(record.get("@id")) in resolutions_needed:
                made_at[bare(record["@id"])] = meeting_name.get(record.get("madeAt"), record.get("madeAt"))
    packs = {p["tdoc:crPackId"]: p for p in graph(f"{phase4}/crpacks.jsonld")}
    pack_of = collections.defaultdict(list)
    for pack in packs.values():
        for member in as_list(pack.get("hasCR")):
            pack_of[bare(member)].append(pack["tdoc:crPackId"])
    sections_of = collections.defaultdict(set)
    modifiers = collections.defaultdict(set)
    for section in graph(f"{phase4}/section_extensions.jsonld"):
        for cr in as_list(section.get("modifiedByCR")):
            sections_of[bare(cr)].add(bare(section["@id"]))
            modifiers[bare(section["@id"])].add(bare(cr))
    for record in graph(f"{phase4}/cr_extensions.jsonld"):
        for section in as_list(record.get("modifiesSection")):
            sections_of[bare(record["@id"])].add(bare(section))
            modifiers[bare(section)].add(bare(record["@id"]))
    reports = []
    for case in cases:
        def document(number: str) -> dict:
            record = documents.get(number)
            if record is None:
                return {"document": number, "inRecords": False}
            return {"document": number, "inRecords": True, "status": record.get("tdoc:status"),
                    "presentedAt": meeting_name.get(record.get("presentedAt"), record.get("presentedAt")),
                    "tsgCRPack": record.get("tdoc:tsgCRPack"), "isRevisionOf": record.get("isRevisionOf"),
                    "revisedTo": record.get("revisedTo"), "targetRelease": record.get("targetRelease"),
                    "modifies": record.get("modifies"),
                    "dispositions": [{"id": r["dispositionId"], "code": r["dispositionCode"],
                                      "evidenceStatus": r["evidenceStatus"], "decidedAt": made_at.get(bare(r["dispositionOf"])),
                                      "assessmentMethod": str(r.get("assessmentMethod"))[:160]}
                                     for r in dispositions.get(number, [])],
                    "inCrPacks": [{"crPack": p, "tsgMeeting": packs[p].get("tdoc:tsgMeeting")} for p in pack_of.get(number, [])],
                    "modifiesSections": sorted(sections_of.get(number, ()))}
        meeting_values = {cell for row in case["goldOnly"] + case["answerOnly"]
                          for field, cell in zip(case["fields"], row) if field == "wg_meeting"}
        pack_values = {cell for row in case["goldOnly"] + case["answerOnly"]
                       for field, cell in zip(case["fields"], row) if field == "cr_pack"} | set(case["anchorPacks"])
        reports.append({
            **{k: case[k] for k in ("set", "id", "class", "anchor", "fields", "goldOnly", "answerOnly", "note")},
            "documents": [document(number) for number in case["closure"]],
            "meetings": {value: [[m.get("tdoc:meetingNumber"), m.get("tdoc:canonicalMeetingNumber")] for m in meetings
                                 if cell_key(value) in {cell_key(m.get("tdoc:meetingNumber")),
                                                        cell_key(m.get("tdoc:canonicalMeetingNumber"))}]
                         for value in sorted(meeting_values)},
            "crPacks": {value: ({"tsgMeeting": packs[value].get("tdoc:tsgMeeting"), "members": len(as_list(packs[value].get("hasCR")))}
                                if value in packs else None) for value in sorted(pack_values)},
            "sectionModifiers": {section: sorted(modifiers.get(section, ())) for section in case["anchorSections"]}})
    return reports


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--sets", nargs="+", required=True)
    parser.add_argument("--items", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    items = {}
    for path in args.items:
        for line in path.read_text().splitlines():
            if line.strip():
                item = json.loads(line)
                items[item["id"]] = item
    result = json.loads(args.result.read_text())
    by_wg = collections.defaultdict(list)
    for name in args.sets:
        for disagreement in result["sets"][name]["disagreements"]:
            item = items[disagreement["id"]]
            gold_only, answer_only = differing(item, disagreement)
            anchor = bare(item["anchor"])
            values = {cell for row in gold_only + answer_only
                      for field, cell in zip(item["fields"], row) if field in DOCUMENT_FIELDS}
            if re.fullmatch(r"R\d-\d+", anchor):
                values.add(anchor)
            values |= set(re.findall(r"\bR\d-\d+\b", item["question"]))
            by_wg[item["wg"]].append({"set": name, "id": item["id"], "class": disagreement["class"], "anchor": anchor,
                                      "fields": item["fields"], "goldOnly": gold_only, "answerOnly": answer_only,
                                      "note": disagreement.get("note"), "documents": sorted(values),
                                      "anchorPacks": [anchor.removeprefix("crpack/")] if anchor.startswith("crpack/") else [],
                                      "anchorSections": [anchor] if anchor.startswith("section/") else []})
    reports = []
    for wg in sorted(by_wg):
        reports += verify_wg(wg, by_wg[wg])
        print(wg, len(by_wg[wg]), "disagreements checked")
    args.out.write_text(json.dumps({"method": __doc__.split("\n\n")[1], "result": str(args.result),
                                    "sets": args.sets, "cases": reports}, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    main()
