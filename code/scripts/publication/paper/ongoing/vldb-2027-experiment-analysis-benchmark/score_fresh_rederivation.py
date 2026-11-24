"""재유도 답을 정답과 맞춰 정확 일치와 표기 무관 일치를 세고, 어긋난 문항을 갈래별로 적는다 (모델 호출 없음).

두 하위 명령을 쓴다.

`survey` 는 기록이 같은 값을 두 가지로 적는 표기를 작업반마다 센다. 표기 무관 일치에 쓰는 정규화는 이 집계로
두 표기가 모두 기록에 있음을 보인 것만 둔다.
  - 작업반 회의 `-e` 접미사: 회의 기록이 전자 회의를 `tdoc:meetingNumber` 로는 `RAN5#94-e`, `tdoc:canonicalMeetingNumber`
    로는 `RAN5#94` 로 함께 적는다. 정식 회의 번호가 같은 회의 기록이 둘 이상인 경우(예: 대면 회의와 전자 회의가 같은
    번호를 쓴 경우)도 따로 센다. 정규화는 이 둘을 한 값으로 합치기 때문이다.
  - 처분 값의 빈칸과 밑줄: 문서 기록의 `tdoc:status` 는 `not pursued` 처럼 빈칸으로, 처분 기록의 `dispositionCode` 는
    `not_pursued` 처럼 밑줄로 적는다. 빈칸을 밑줄로 바꾸면 같아지는 값의 쌍과 각 표기의 건수를 센다.
  정규화하지 않는 필드(CR 묶음 번호·TSG 회의·절 번호·문서 번호)도 기록의 표기가 한 가지인지 같은 자리에서 센다.

`score` 는 답 묶음마다 문항별로 두 점수를 낸다.
  (a) 정확 일치: `score_chain_eval.score()` 의 행 집합 일치. 칸 비교는 `cell_key()`(빈칸 제거·소문자·bis 표기 통일)다.
  (b) 표기 무관 일치: `cell_key()` 뒤에 `wg_meeting` 칸의 끝 `-e` 를 떼고 `disposition` 칸의 빈칸을 밑줄로 바꾼 행 집합
      일치. 정답과 답에 같은 함수를 쓴다.
  어긋난 문항은 (b) 가 맞으면 notation, 답이 없으면 no_answer, (b) 행 집합에서 답이 정답의 진부분집합이면 missing_row,
  정답이 답의 진부분집합이면 extra_row, 그 밖은 different_record 로 적는다. 갈래는 행 집합 관계만으로 정하고,
  기록 대조는 `verify_fresh_rederivation_disagreements.py` 가 따로 한다.
  답 묶음의 질문이 지금 문항 파일의 질문과 다르면 stale 로 적고, 점수는 전체와 stale 을 뺀 것을 함께 낸다.
  정규화가 서로 다른 두 회의 기록을 합치는 회의(survey 의 distinctMeetingsMergedByNormalization)가 정답이나 답에 걸린
  문항 수와, 그 가운데 (b) 로만 맞은 문항 수를 함께 센다.

사용 (저장소 루트에서 `PYTHONPATH=scripts/common:<이 폴더>`):
  python3 score_fresh_rederivation.py survey --out <normalization_evidence.json>
  python3 score_fresh_rederivation.py score --items <admitted.jsonl> [...] --evidence <normalization_evidence.json> \
      --packet-map <sample.json> --set <이름> '<답 glob>' '<묶음 glob>' [--set ...] --out <result.json>
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import re
from pathlib import Path

from score_chain_eval import cell_key, score

INSTANCES = "ontology/output/tsg/RAN/formal/instances"
RAN5_EXPORT = "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/RAN5_graph_export/RAN5"
WGS = ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5")
E_SUFFIX = re.compile(r"-e$")


def graph(path: str) -> list[dict]:
    with open(path) as handle:
        return json.load(handle)["@graph"]


def phase4(wg: str) -> str:
    return RAN5_EXPORT if wg == "RAN5" else f"{INSTANCES}/phase-4/{wg}"


def survey_wg(wg: str) -> dict:
    meetings = graph(f"{INSTANCES}/phase-1/{wg}/meetings.jsonld")
    suffixed = [m for m in meetings if str(m.get("tdoc:meetingNumber", "")).endswith("-e")]
    paired = [m for m in suffixed if m.get("tdoc:canonicalMeetingNumber") == m["tdoc:meetingNumber"][:-2]]
    by_canonical = collections.defaultdict(list)
    for m in meetings:
        by_canonical[cell_key(E_SUFFIX.sub("", cell_key(m.get("tdoc:meetingNumber"))))].append(m["tdoc:meetingNumber"])
    merged = {key: sorted(names) for key, names in sorted(by_canonical.items()) if len(names) > 1}
    tdocs = graph(f"{INSTANCES}/phase-1/{wg}/tdocs.jsonld")
    status = collections.Counter(str(r.get("tdoc:status")) for r in tdocs)
    numbers = [str(r.get("tdoc:tdocNumber")) for r in tdocs]
    del tdocs
    codes = collections.Counter(str(r.get("dispositionCode"))
                                for r in graph(f"{INSTANCES}/phase-2/{wg}/decision_dispositions.jsonld"))
    pairs = [{"status": value, "statusCount": count, "code": value.replace(" ", "_"),
              "codeCount": codes[value.replace(" ", "_")]}
             for value, count in sorted(status.items()) if " " in value and codes[value.replace(" ", "_")]]
    packs = graph(f"{phase4(wg)}/crpacks.jsonld")
    tsg = collections.Counter(str(p.get("tdoc:tsgMeeting")) for p in packs)
    sections = [re.sub(r"^.*?-Rel-\d+-", "", str(s["@id"])) for s in graph(f"{phase4(wg)}/section_extensions.jsonld")]
    return {
        "wgMeetingSuffix": {"meetingRecords": len(meetings), "meetingNumberEndsWithE": len(suffixed),
                            "canonicalEqualsWithoutE": len(paired),
                            "examples": [[m["tdoc:meetingNumber"], m["tdoc:canonicalMeetingNumber"]] for m in paired[:3]],
                            "distinctMeetingsMergedByNormalization": merged},
        "dispositionSpaceUnderscore": {"pairs": pairs, "statusValues": dict(status.most_common()),
                                       "dispositionCodes": dict(codes.most_common())},
        "notNormalized": {
            "tsgMeetingValues": len(tsg), "tsgMeetingEndsWithE": sum(c for v, c in tsg.items() if v.endswith("-e")),
            "tsgMeetingOtherShape": sorted(v for v in tsg if not re.fullmatch(r"RAN#\d+", v)),
            "crPackIdOtherShape": sorted(str(p.get("tdoc:crPackId")) for p in packs
                                         if not re.fullmatch(r"RP-\d{6}", str(p.get("tdoc:crPackId")))),
            "sectionIds": len(sections),
            "clauseWithSpace": sorted(c for c in set(sections) if " " in c),
            "clauseWithZeroPaddedPart": sorted(c for c in set(sections) if re.search(r"(^|\.)0\d", c)),
            "tdocNumbers": len(numbers),
            "tdocNumberOtherShape": sorted(set(n for n in numbers if not re.fullmatch(r"R\d-\d+", n)))[:20]}}


def survey(out: Path) -> None:
    report = {"method": __doc__.split("\n\n")[2], "byWg": {}}
    for wg in WGS:
        report["byWg"][wg] = survey_wg(wg)
        print(wg, json.dumps({k: v for k, v in report["byWg"][wg]["wgMeetingSuffix"].items() if k != "examples"})[:300])
    report["totals"] = {
        "meetingNumberEndsWithE": sum(w["wgMeetingSuffix"]["meetingNumberEndsWithE"] for w in report["byWg"].values()),
        "canonicalEqualsWithoutE": sum(w["wgMeetingSuffix"]["canonicalEqualsWithoutE"] for w in report["byWg"].values()),
        "dispositionPairs": sum(len(w["dispositionSpaceUnderscore"]["pairs"]) for w in report["byWg"].values())}
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")


def notation_key(fields: list[str], row) -> tuple[str, ...]:
    cells = []
    for field, cell in zip(fields, row):
        value = cell_key(cell)
        if field == "wg_meeting":
            value = E_SUFFIX.sub("", value)
        elif field == "disposition":
            value = value.replace(" ", "_")
        cells.append(value)
    return tuple(cells) + tuple(cell_key(cell) for cell in list(row)[len(fields):])


def classify(fields: list[str], gold: list, rows) -> str:
    if rows is None:
        return "no_answer"
    wanted = {notation_key(fields, row) for row in gold}
    given = {notation_key(fields, row) for row in rows}
    if wanted == given:
        return "notation"
    if given < wanted:
        return "missing_row"
    if wanted < given:
        return "extra_row"
    return "different_record"


def read_lines(pattern: str) -> list[dict]:
    paths = sorted(glob.glob(pattern))
    if not paths:
        raise SystemExit(f"파일이 없다: {pattern}")
    return [json.loads(line) for path in paths for line in Path(path).read_text().splitlines() if line.strip()]


def tally(results: list[dict], key: str) -> dict:
    table: dict[str, dict] = collections.defaultdict(lambda: {"n": 0, "exact": 0, "notationInsensitive": 0})
    for result in results:
        cell = table[result[key]]
        cell["n"] += 1
        cell["exact"] += result["exact"]
        cell["notationInsensitive"] += result["notationInsensitive"]
    return dict(sorted(table.items()))


def summary(results: list[dict]) -> dict:
    return {"n": len(results), "exact": sum(r["exact"] for r in results),
            "notationInsensitive": sum(r["notationInsensitive"] for r in results),
            "byWg": tally(results, "wg"), "byFamily": tally(results, "family"),
            "disagreementClasses": dict(collections.Counter(r["class"] for r in results if not r["exact"])),
            "itemsTouchingMergedMeetings": sum(r["touchesMergedMeeting"] for r in results),
            "notationMatchesTouchingMergedMeetings": sum(r["touchesMergedMeeting"] and r["notationInsensitive"]
                                                         and not r["exact"] for r in results)}


def touches(fields: list[str], rows, merged: set[str]) -> bool:
    if "wg_meeting" not in fields or not rows:
        return False
    column = fields.index("wg_meeting")
    return any(len(row) > column and E_SUFFIX.sub("", cell_key(row[column])) in merged for row in rows)


def score_set(name: str, answers_glob: str, packets_glob: str, items: dict, packet_map: dict,
              merged: dict[str, set[str]]) -> dict:
    def item_id(value: str) -> str:
        return value if value in items else packet_map[value]
    packets = {item_id(p["id"]): p for p in read_lines(packets_glob)}
    answers: dict[str, dict] = {}
    for answer in read_lines(answers_glob):
        identifier = item_id(answer["id"])
        if identifier in answers:
            raise SystemExit(f"{name}: 같은 문항의 답이 두 번 있다: {identifier}")
        answers[identifier] = answer
    unexpected = sorted(set(answers) - set(packets))
    if unexpected:
        raise SystemExit(f"{name}: 묶음에 없는 문항의 답: {unexpected[:5]}")
    results = []
    for identifier, packet in sorted(packets.items()):
        item = items[identifier]
        rows = answers[identifier].get("rows") if identifier in answers else None
        exact = score(item["gold"], rows)["exact"]
        result = {"id": identifier, "packetId": packet["id"], "wg": item["wg"], "family": item["family"],
                  "stale": packet["question"] != item["question"], "exact": exact,
                  "notationInsensitive": int(rows is not None and {notation_key(item["fields"], r) for r in item["gold"]}
                                             == {notation_key(item["fields"], r) for r in rows}),
                  "touchesMergedMeeting": touches(item["fields"], item["gold"], merged[item["wg"]])
                  or touches(item["fields"], rows, merged[item["wg"]])}
        if not exact:
            result.update({"class": classify(item["fields"], item["gold"], rows), "fields": item["fields"],
                           "gold": item["gold"], "answer": rows, "note": answers.get(identifier, {}).get("note")})
        else:
            result["class"] = "match"
        results.append(result)
    current = [r for r in results if not r["stale"]]
    return {"answers": answers_glob, "packets": packets_glob, "all": summary(results),
            "staleQuestions": len(results) - len(current),
            "currentQuestionsOnly": summary(current) if len(current) != len(results) else "same as all",
            "disagreements": [r for r in results if not r["exact"]]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("survey")
    one.add_argument("--out", type=Path, required=True)
    two = sub.add_parser("score")
    two.add_argument("--items", type=Path, nargs="+", required=True)
    two.add_argument("--evidence", type=Path, required=True, help="survey 가 쓴 표기 집계")
    two.add_argument("--packet-map", type=Path, required=True, help="묶음 id → 문항 id 가 담긴 sample.json")
    two.add_argument("--set", nargs=3, action="append", required=True, metavar=("NAME", "ANSWERS", "PACKETS"))
    two.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "survey":
        survey(args.out)
        return
    evidence = json.loads(args.evidence.read_text())
    if not evidence["totals"]["canonicalEqualsWithoutE"] or not evidence["totals"]["dispositionPairs"]:
        raise SystemExit("정규화의 근거 집계가 비었다")
    items = {}
    for path in args.items:
        for line in path.read_text().splitlines():
            if line.strip():
                item = json.loads(line)
                items[item["id"]] = item
    packet_map = json.loads(args.packet_map.read_text())["packetIds"]
    # 정규화가 서로 다른 두 회의 기록을 한 값으로 합치는 경우. 이런 회의가 걸린 문항은 따로 센다.
    merged = {wg: set(entry["wgMeetingSuffix"]["distinctMeetingsMergedByNormalization"])
              for wg, entry in evidence["byWg"].items()}
    report = {"method": __doc__.split("\n\n")[3], "evidence": str(args.evidence),
              "sets": {name: score_set(name, answers, packets, items, packet_map, merged)
                       for name, answers, packets in args.set}}
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    for name, entry in report["sets"].items():
        print(name, json.dumps({k: entry["all"][k] for k in ("n", "exact", "notationInsensitive", "disagreementClasses")}),
              "stale", entry["staleQuestions"])


if __name__ == "__main__":
    main()
