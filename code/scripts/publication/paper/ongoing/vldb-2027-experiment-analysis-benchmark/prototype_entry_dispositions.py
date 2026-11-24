"""RAN1·RAN2 회의 보고서의 문서 목록 줄과 그 뒤 결정 줄에서 문서별 처분을 읽어 본다 (모델 호출 없음).

정식 구축의 문서 entry 문법은 `Type:`·`Source:` 필드가 있는 보고서 양식을 읽는다.
RAN1·RAN2 보고서는 `번호 제목 제출사` 한 줄 뒤에 `Decision: …`, `=> …`, `[NNN] …` 또는
처분 표현으로 시작하는 줄이 오는 양식이다. 이 스크립트는 그 양식을 읽는 규칙을 연구 트랙에서
먼저 시험하고, 읽은 처분을 사무국 TDoc 목록의 상태 값과 맞대어 일치 건수를 센다.

읽는 규칙
- 목록 줄: 자기 WG 문서 번호로 시작하고, 번호 뒤 글이 TDoc 목록의 제목 앞부분과 같다.
- entry 범위: 목록 줄 다음부터, 문서 번호로 시작하는 다음 줄 또는 의제 제목 줄 앞까지.
- 결정 줄: `Decision:`·`=>`·`[NNN]` 표지가 있거나 처분 표현으로 시작하는 줄.
  주어(`The CR is`, `CR0019 to 38.900 is` 등)를 걷어 낸 첫 표현이 처분 표현일 때만 읽는다.
- 결정 줄은 절 단위로 읽는다(`The document is noted and CR0607 to 36.213 is agreed`는 두 처분).
- `agreed in R1-xxxx`·`endorsed in R1-xxxx` 꼴로 다른 문서를 가리키면 그 문서가 처분을 받고,
  목록 줄 문서는 그 문서로 이어졌으므로 `revised`다. `revised in R1-xxxx`는 목록 줄 문서만 `revised`다.
- `in principle`이 붙은 처분은 최종 처분과 구분해 따로 센다.
- 한 문서가 받은 처분은 모두 모으고, 목록 상태가 그 안에 있으면 일치로 센다.
  처분이 하나뿐인 문서의 일치 건수(`singleCodeAgree`)를 따로 적는다.

사용: python3 prototype_entry_dispositions.py --sample 30 --seed 20261111 --out <json>
저장소 루트에서 실행한다.
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import re
from pathlib import Path

from measure_cross_source_agreement import LIST_WITHOUT_DISPOSITION, canonical
from measure_decision_link_gap import INSTANCES, REPORTS, paragraphs

ANY_NUMBER = re.compile(r"(?:R\d|RP|S\d|C\d|SP|CP)-\d{6,7}")
AGENDA_HEADING = re.compile(r"^\d{1,2}(?:\.\d{1,2}){0,5}\s+[A-Z\[]")
MARKER = re.compile(r"^(?:(?:[A-Z][a-z]+day\s+)?decision\s*:|=>|\[\d{3}\])\s*", re.IGNORECASE)
SUBJECT = re.compile(
    r"^(?:as\s+per\s+(?:the\s+)?email\s+decision\s+posted\s+on\s+[^,]{1,30},\s*)?"
    r"(?:\([^)]*\)\s*)?"
    r"(?:(?:the|this)\s+)?(?:final\s+)?(?:rel-\d+\s+)?(?:draft\s+)?(?:crs?|document|tdoc)?"
    r"(?:\s*#?\d{3,4}(?:r\d+)?)?(?:\s+in\s+R\d-\d{6,7})?"
    r"(?:\s+(?:to|for)\s+.{1,60}?)?(?:\s*\([^)]*\))?\s*(?:is|are|was|were)\s+",
    re.IGNORECASE)
PREDICATE = re.compile(
    r"^(?:(?:further|then|also|later)\s+)?(?P<principle>in[\s-]+principle\s+)?"
    r"(?P<code>not\s+pursued|not\s+agreed|not\s+treated|noted|withdrawn|postponed|merged|revised|rejected"
    r"|endorsed|agreed|approved)\b(?P<after>\s+in[\s-]+principle)?(?P<rest>.*)",
    re.IGNORECASE)
# 처분 표현 바로 뒤가 이 꼴이면 처분 문장이 아니다(절 표제, 편입 예정, 병합용 표시).
NOT_A_DISPOSITION = re.compile(r"^\s*(?:[/:]|\(?for\s+merge|to\s+be\b|unseen\s+to\s+be\b)", re.IGNORECASE)
# 처분 표현 뒤에서 다른 문서를 가리키는 꼴: `in R1-x`, `as R2-x`, `agreed R1-x`, 줄 끝의 `in:`.
MOVED = re.compile(r"^(?:(?:[^.;]|\.(?=\d))*?\b(?:in|as)\s*:?\s*|\s*)(?=R\d-\d{6,7})", re.IGNORECASE)
CONTINUES = re.compile(r"\bin\s*:\s*$", re.IGNORECASE)
CLAUSE = re.compile(r"(?<=[a-z0-9)])\.\s+|;\s+|\s+and\s+|\s+[–-]\s+")
OWN_NUMBER = re.compile(r"R\d-\d{6,7}")
PASSES_ON = {"agreed", "endorsed"}


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def read_line(line: str) -> tuple[list[tuple[str, list[str]]], int]:
    """결정 줄 -> ([(처분, 처분을 받은 다른 문서들)], in principle 절 수).

    다른 문서 목록이 비어 있으면 목록 줄 문서가 그 처분을 받는다.
    첫 절을 읽지 못하면 줄 전체를 읽지 않는다.
    """
    marked = MARKER.match(line)
    body = line[marked.end():] if marked else line
    read: list[tuple[str, list[str]]] = []
    principle = 0
    for order, clause in enumerate(CLAUSE.split(body)):
        clause = clause.strip()
        if order and read and read[-1][1] and OWN_NUMBER.match(clause):
            read[-1][1].extend(OWN_NUMBER.findall(clause))
            continue
        subject = SUBJECT.match(clause)
        predicate = PREDICATE.match(clause[subject.end():] if subject else clause)
        readable = predicate is not None and not NOT_A_DISPOSITION.match(predicate["rest"])
        if order == 0 and not (readable and (marked or subject or len(body) <= 120)):
            return [], 0
        if not readable:
            continue
        if predicate["principle"] or predicate["after"]:
            principle += 1
            continue
        code = canonical(re.sub(r"\s+", " ", predicate["code"]))
        moved = MOVED.match(predicate["rest"])
        if moved:
            read.append((code, OWN_NUMBER.findall(predicate["rest"][moved.end():])))
        elif CONTINUES.search(predicate["rest"]):
            # 처분을 받은 문서 번호가 다음 줄에 있다. 목록 줄 문서는 그 문서로 이어졌다.
            read.append(("revised", []))
        else:
            read.append((code, []))
    return read, principle


def read_report(path: Path, titles: dict[str, str], prefix: str):
    """(문서, 처분, 근거 줄) 목록과 entry 통계를 돌려준다."""
    texts = paragraphs(path)
    rows, stats = [], collections.Counter()
    position = 0
    while position < len(texts):
        text = texts[position]
        lead = ANY_NUMBER.match(text)
        position += 1
        if not lead or not lead.group().startswith(prefix) or lead.group() not in titles:
            continue
        number, rest = lead.group(), norm(text[lead.end():])
        title = norm(titles[number])
        if not rest:
            stats["numberOnlyLines"] += 1
            continue
        if not title or not rest.startswith(title[:25]):
            stats["titleDiffers"] += 1
            continue
        stats["entries"] += 1
        end = position
        while (end < len(texts) and end - position < 40
               and not ANY_NUMBER.match(texts[end]) and not AGENDA_HEADING.match(texts[end])):
            end += 1
        readable = False
        for line in texts[position:end]:
            clauses, principle = read_line(line)
            stats["inPrincipleDecisions"] += principle
            readable = readable or bool(clauses)
            for code, others in clauses:
                others = [other for other in others if other != number]
                if not others:
                    rows.append((number, code, line))
                    continue
                # 다른 문서가 처분을 받았다는 문장은 목록 줄 문서가 그 문서로 이어졌음을 함께 말한다.
                rows.append((number, "revised", line))
                if code in PASSES_ON:
                    rows.extend((other, code, line) for other in others)
        stats["entriesWithoutReadableDecision"] += not readable
    return rows, stats


def measure(wg: str, sample: int, rng: random.Random) -> dict:
    load = lambda rel: json.loads((INSTANCES / rel).read_text())["@graph"]
    tdocs = {r["tdoc:tdocNumber"]: r for r in load(f"phase-1/{wg}/tdocs.jsonld") if "tdoc:tdocNumber" in r}
    titles = {number: r.get("tdoc:title", "") for number, r in tdocs.items()}
    verified: dict[str, set[str]] = collections.defaultdict(set)
    for record in load(f"phase-2/{wg}/decision_dispositions.jsonld"):
        if record["evidenceStatus"] == "source_verified":
            verified[record["targetTdocNumber"]].add(canonical(record["dispositionCode"]))
    read: dict[str, dict[str, str]] = collections.defaultdict(dict)
    stats: collections.Counter[str] = collections.Counter()
    for path in sorted((REPORTS / wg / "Final_Report").glob("Final_Report_*.docx")):
        rows, report_stats = read_report(path, titles, f"R{wg[-1]}-")
        stats.update(report_stats)
        for number, code, line in rows:
            if number in tdocs:
                read[number][code] = line
            else:
                stats["readTargetsAbsentFromTdocList"] += 1
    out = {"wg": wg, "entryStats": dict(stats), "documentsRead": len(read)}
    for label, keep in (("allDocuments", lambda r: True), ("cr", lambda r: r.get("@type") == "tdoc:CR")):
        cell: collections.Counter[str] = collections.Counter()
        differences: collections.Counter[tuple[str, str]] = collections.Counter()
        examples = []
        for number, codes in read.items():
            record = tdocs[number]
            if not keep(record):
                continue
            cell["read"] += 1
            new = number not in verified
            cell["newlyLinked"] += new
            if not new:
                cell["alsoInBuild"] += 1
                cell["sameCodeAsBuild"] += bool(set(codes) & verified[number])
            status = canonical(record["tdoc:status"])
            if status in LIST_WITHOUT_DISPOSITION:
                cell["listWithoutDisposition"] += 1
                continue
            cell["compared"] += 1
            cell["comparedNewlyLinked"] += new
            cell["singleCode"] += len(codes) == 1
            if status in codes:
                cell["agree"] += 1
                cell["agreeNewlyLinked"] += new
                cell["singleCodeAgree"] += len(codes) == 1
            else:
                differences[(status, "+".join(sorted(codes)))] += 1
                examples.append({"tdoc": number, "listStatus": status, "read": codes})
        out[label] = {**dict(cell),
                      "agreeShare": round(cell["agree"] / cell["compared"], 4) if cell["compared"] else None,
                      "differences": [{"listStatus": s, "read": c, "n": n}
                                      for (s, c), n in differences.most_common(12)],
                      "differenceSamples": rng.sample(examples, min(sample, len(examples)))}
    total_cr = sum(1 for r in tdocs.values() if r.get("@type") == "tdoc:CR")
    linked_cr = sum(1 for n, r in tdocs.items() if r.get("@type") == "tdoc:CR" and n in verified)
    out["crLinkRate"] = {"cr": total_cr, "linkedInBuild": linked_cr,
                         "linkedWithEntryReading": linked_cr + out["cr"].get("newlyLinked", 0)}
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--wg", nargs="+", default=["RAN1", "RAN2"])
    parser.add_argument("--sample", type=int, required=True, help="불일치 표본 건수")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rng = random.Random(args.seed)
    result = {"seed": args.seed, "workingGroups": [measure(wg, args.sample, rng) for wg in args.wg]}
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    for row in result["workingGroups"]:
        print(row["wg"], row["entryStats"], row["crLinkRate"])
        for label in ("allDocuments", "cr"):
            cell = {k: v for k, v in row[label].items() if k not in ("differences", "differenceSamples")}
            print("  ", label, cell)
            print("    ", [(d["listStatus"], d["read"], d["n"]) for d in row[label]["differences"][:8]])


if __name__ == "__main__":
    main()
