"""결정 기록이 직접 가리키지 않는 CR이 회의 보고서 원문에 어떻게 적혀 있는지 센다 (모델 호출 없음).

CR마다 제출 회의의 Final Report DOCX에서 문서 번호가 든 문단을 모으고 여섯 갈래로 나눈다.
- verified: 원문 대조를 통과한 처분 기록이 이 CR을 가리킨다
- pending: 처분 기록이 있으나 범위·처분 판정이 보류돼 있다
- inline_predicate: 기록은 없고, 번호가 든 문단에 처분 표현이 함께 있다
- block_predicate: 기록은 없고, 번호로 시작하는 목록 줄과 다음 목록 줄 사이의 문단에 처분 표현이 있다
- listed_only: 기록은 없고, 번호가 든 문단과 그 뒤 구간 어디에도 처분 표현이 없다
- absent: 제출 회의 보고서에 번호가 없다

모집단은 `--population` 으로 고른다. `cr` 는 문서 목록이 유형 `CR` 로 적은 문서 전체이고,
`pack` 은 그중 총회 CR 묶음에 실린 문서다(`draftCR` · `pCR` 유형은 묶음에 실리지 않아 두 모집단 모두 밖이다).
각 갈래를 TDoc 목록의 상태 값(`tdoc:status`)과 교차 집계하고, 기록이 없고 보고서에 번호가 있는 세 갈래에서
문단 표본을 뽑아 함께 저장한다. 처분 표현 판정은 키워드 규칙이며 원문 해석이 아니다.

보고서 파일명의 회의 표기(`101Bis` · `109_e` · `121-bis` 등)는 phase-1 이 파일명에서 회의 ID를 읽는
정본 규칙(`scripts/tsg/RAN/formal/{WG}/phase-1/jsonld/meeting_id.py`)으로 읽어 문서 목록의 회의 ID와 맞춘다.
인스턴스 파일이 없는 작업반은 `--neo4j WG=PORT` 로 준 실행 중인 그래프에서 같은 정의로 CR과 처분 기록을 읽고,
그래프의 회의 ID에 맞는 보고서가 없으면 그 회의의 `canonicalMeetingNumber`(개최 형식 표시를 뺀 번호)로 찾는다.
`--phase2-root` 를 주면 처분 기록을 그 디렉토리의 `{WG}/` 아래에서 읽는다(예: 목록 줄 재구축 전 첫 빌드의
phase-2 사본). 문서 목록과 묶음 기록은 그대로 인스턴스에서 읽는다.

사용: python3 measure_decision_link_gap.py --wg RAN1 RAN2 RAN3 RAN4 RAN5 --neo4j RAN5=7691 \
        --population pack --sample 40 --seed 20261111 --out <json>
저장소 루트에서 실행한다.
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
INSTANCES = Path("ontology/output/tsg/RAN/formal/instances")
PHASE1_RULE = "scripts/tsg/RAN/formal/{wg}/phase-1/jsonld/meeting_id.py"
REPORTS = Path("ontology/input/tsg/RAN/formal/meetings")
PREDICATE = re.compile(
    r"agreed|endorsed|approved|revised|not\s+pursued|noted|withdrawn|postponed|merged|rejected|not\s+treated",
    re.IGNORECASE)
NUMBER = re.compile(r"R\d-\d{6,7}")
GRAPH_CRS = """
MATCH (c:CR {type: 'CR'})-[:PRESENTED_AT]->(m:Meeting)
WHERE $population = 'cr' OR EXISTS{(c)-[:BELONGS_TO_CR_PACK]->()}
OPTIONAL MATCH (d:DecisionDisposition)-[:DISPOSITION_TARGET]->(c)
RETURN c.id AS id, c.tdocNumber AS number, c.status AS status,
       collect(DISTINCT [m.id, m.canonicalMeetingNumber]) AS meetings,
       collect(DISTINCT d.evidenceStatus) AS statuses
"""
# 목록 줄 뒤에서 살피는 문단 수의 상한. 한 문서의 논의가 길어도 다음 목록 줄에서 먼저 끊긴다.
BLOCK_LIMIT = 30


def paragraphs(path: Path) -> list[str]:
    """문단 텍스트. `w:noBreakHyphen` 은 화면에 보이는 대로 "-" 로 읽고(문서 번호 `R1-1911675` 의 하이픈이 이 요소일 수 있다),
    탭·줄바꿈·기호 요소(`w:tab` · `w:ptab` · `w:br` · `w:cr` · `w:sym`)는 공백으로 읽는다."""
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    out = []
    for paragraph in root.iter(W + "p"):
        parts = []
        for element in paragraph.iter():
            if element.tag == W + "t":
                parts.append(element.text or "")
            elif element.tag == W + "noBreakHyphen":
                parts.append("-")
            elif element.tag in (W + "tab", W + "ptab", W + "br", W + "cr", W + "sym"):
                parts.append(" ")
        text = re.sub(r"\s+", " ", "".join(parts)).strip()
        if text:
            out.append(text)
    return out


def phase1_meeting_rule(wg: str):
    """phase-1 이 파일명에서 회의 ID(`RAN3#101bis`)를 읽는 정본 규칙을 불러온다."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(f"meeting_id_{wg}", PHASE1_RULE.format(wg=wg))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.extract_meeting_from_filename


def meeting_key(meeting: str) -> str:
    """문서 목록 · 그래프의 회의 ID(`tdoc:meeting/RAN3_101bis`)를 보고서 색인 키(`RAN3#101bis`)로 바꾼다."""
    return meeting.removeprefix("tdoc:meeting/").replace("_", "#", 1)


def report_index(wg: str) -> dict[str, dict[str, dict[str, list[str]]]]:
    """회의 ID -> 문서 번호 -> {"inline": 번호가 든 문단, "block": 목록 줄 뒤 구간의 문단}."""
    index = {}
    read_meeting = phase1_meeting_rule(wg)
    for path in sorted((REPORTS / wg / "Final_Report").glob("Final_Report_*.docx")):
        meeting = read_meeting(f"TSGR{wg[-1]}_{path.stem.removeprefix(f'Final_Report_{wg}-')}")
        if not meeting:
            raise SystemExit(f"{path.name}: phase-1 rule reads no meeting")
        if meeting in index:
            raise SystemExit(f"{wg}: two reports share the meeting key {meeting}")
        by_number: dict[str, dict[str, list[str]]] = collections.defaultdict(
            lambda: {"inline": [], "block": []})
        texts = paragraphs(path)
        leading = [NUMBER.match(text) for text in texts]
        for position, text in enumerate(texts):
            for number in set(NUMBER.findall(text)):
                by_number[number]["inline"].append(text)
            if leading[position]:
                block = by_number[leading[position].group()]["block"]
                for following, lead in zip(texts[position + 1:position + 1 + BLOCK_LIMIT],
                                           leading[position + 1:]):
                    if lead:
                        break
                    block.append(following)
        index[meeting] = by_number
    return index


def from_jsonld(wg: str, population: str, phase2: Path) -> tuple[list[dict], dict[str, set[str]]]:
    load = lambda rel: json.loads((INSTANCES / rel).read_text())["@graph"]
    crs = [r for r in load(f"phase-1/{wg}/tdocs.jsonld")
           if r.get("@type") == "tdoc:CR" and r.get("tdoc:type") == "CR"]
    if population == "pack":
        packed = {r["@id"] for r in load(f"phase-4/{wg}/cr_extensions.jsonld") if r.get("belongsToCRPack")}
        crs = [r for r in crs if r["@id"] in packed]
    status_of_target: dict[str, set[str]] = collections.defaultdict(set)
    for record in json.loads((phase2 / wg / "decision_dispositions.jsonld").read_text())["@graph"]:
        status_of_target[record["dispositionTarget"]].add(record["evidenceStatus"])
    return crs, status_of_target


def from_neo4j(port: int, population: str) -> tuple[list[dict], dict[str, set[str]]]:
    sys.path.insert(0, "scripts/common")
    from common.credentials import neo4j_auth
    from neo4j import GraphDatabase

    with GraphDatabase.driver(f"bolt://localhost:{port}", auth=neo4j_auth()) as driver:
        rows = driver.execute_query(GRAPH_CRS, population=population).records
    crs, status_of_target = [], {}
    for row in rows:
        if len(row["meetings"]) != 1:
            raise SystemExit(f"{row['number']}: expected one presenting meeting, got {row['meetings']}")
        meeting_id, canonical = row["meetings"][0]
        crs.append({"@id": row["id"], "tdoc:tdocNumber": row["number"], "presentedAt": meeting_id,
                    "canonicalMeeting": canonical, "tdoc:type": "CR", "tdoc:status": row["status"]})
        status_of_target[row["id"]] = set(row["statuses"])
    return crs, status_of_target


def measure(wg: str, population: str, sample: int, rng: random.Random, port: int | None,
            phase2: Path) -> dict:
    crs, status_of_target = from_neo4j(port, population) if port else from_jsonld(wg, population, phase2)
    index = report_index(wg)
    cells: collections.Counter[tuple[str, str, str]] = collections.Counter()
    pool: dict[str, list[dict]] = collections.defaultdict(list)
    without_report = 0
    group_without_report: collections.Counter[str] = collections.Counter()
    for cr in crs:
        number = cr["tdoc:tdocNumber"]
        meeting = meeting_key(cr["presentedAt"])
        if meeting not in index and cr.get("canonicalMeeting") in index:
            meeting = cr["canonicalMeeting"]
        if meeting not in index:
            without_report += 1
        found = index.get(meeting, {}).get(number, {"inline": [], "block": []})
        hits, block = found["inline"], found["block"]
        statuses = status_of_target.get(cr["@id"], set())
        if "source_verified" in statuses:
            group = "verified"
        elif statuses:
            group = "pending"
        elif not hits:
            group = "absent"
        elif any(PREDICATE.search(text) for text in hits):
            group = "inline_predicate"
        elif any(PREDICATE.search(text) for text in block):
            group = "block_predicate"
        else:
            group = "listed_only"
        cells[(group, cr["tdoc:type"], cr["tdoc:status"])] += 1
        if meeting not in index:
            group_without_report[group] += 1
        if group in ("inline_predicate", "block_predicate", "listed_only"):
            pool[group].append({"tdoc": number, "meeting": meeting, "type": cr["tdoc:type"],
                                "listStatus": cr["tdoc:status"],
                                "paragraphs": [text[:400] for text in hits[:4]],
                                "block": [text[:300] for text in block[:6]]})
    fold = lambda position: dict(sorted(collections.Counter(
        {key: sum(n for cell, n in cells.items() if cell[position] == key)
         for key in {cell[position] for cell in cells}}).items()))
    return {
        "wg": wg, "source": "live graph" if port else f"instance JSON-LD, phase-2 from {phase2}",
        "population": population, "cr": len(crs), "crWithoutMeetingReport": without_report,
        "groups": fold(0),
        "groupsWithoutMeetingReport": dict(sorted(group_without_report.items())),
        "groupByType": {g: dict(sorted(collections.Counter(
            {t: sum(n for (gg, tt, _), n in cells.items() if gg == g and tt == t)
             for (gg, t, _) in cells if gg == g}).items())) for g in fold(0)},
        "groupByListStatus": {g: dict(sorted(collections.Counter(
            {s: sum(n for (gg, _, ss), n in cells.items() if gg == g and ss == s)
             for (gg, _, s) in cells if gg == g}).items(), key=lambda kv: -kv[1])) for g in fold(0)},
        "samples": {g: rng.sample(rows, min(sample, len(rows))) for g, rows in sorted(pool.items())},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--wg", nargs="+", default=["RAN1", "RAN2"])
    parser.add_argument("--population", choices=("cr", "pack"), default="cr",
                        help="cr: 목록 유형이 CR 인 문서 전체, pack: 그중 총회 CR 묶음에 실린 문서")
    parser.add_argument("--neo4j", action="append", default=[], metavar="WG=PORT",
                        help="인스턴스 파일 대신 실행 중인 그래프에서 읽을 작업반")
    parser.add_argument("--phase2-root", type=Path, default=INSTANCES / "phase-2",
                        help="처분 기록을 읽을 phase-2 디렉토리(작업반 하위 디렉토리를 둔다)")
    parser.add_argument("--sample", type=int, required=True, help="갈래별 문단 표본 건수")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rng = random.Random(args.seed)
    live = dict(item.split("=") for item in args.neo4j)
    result = {"population": args.population, "samplePerGroup": args.sample, "seed": args.seed,
              "workingGroups": [measure(wg, args.population, args.sample, rng,
                                        int(live[wg]) if wg in live else None, args.phase2_root)
                                for wg in args.wg]}
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    for row in result["workingGroups"]:
        print(row["wg"], row["cr"], row["crWithoutMeetingReport"], row["groups"],
              "without report:", row["groupsWithoutMeetingReport"])
        for group, by_status in row["groupByListStatus"].items():
            print("  ", group, by_status)


if __name__ == "__main__":
    main()
