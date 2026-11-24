"""`The document is noted` 뒤에 두 번째 결과가 이어지는 결정문을 TDoc 목록의 상태 값과 맞대어 센다 (모델 호출 없음).

회의 보고서의 문서별 결정문에는 `The document is noted and agreed as CR0216 to 36.211 in R1-161172`,
`The document is noted. Further revised in R1-2004937.`처럼 한 필드가 결과 둘을 적는 경우가 있다.
처분 코드는 값 하나만 담으므로 빌더(`document_decision_source.classify_document_decision`)는 이
유형을 보류(`ambiguous`)로 읽고, 필드가 문서 자신의 CR 을 이름으로 적어 승인한 경우만 `agreed`로
읽는다. 두 판정이 회의 보고서와 다른 원자료인 사무국 TDoc 목록의 상태 값과 맞는지 확인하려고,
설치된 처분 기록을 세 집단으로 나누어 대상 문서의 목록 상태를 센다.

- compound  `noted`·`source_verified`로 설치되어 있고 빌더가 두 번째 결과 규칙으로 보류하는 기록.
            `noted` 뒤에서 처음 나오는 결과 동사별로 나눈다.
- simple    같은 조건에서 필드가 `The document is noted.`뿐인 기록 (대조군).
- ownCr     문서 자신의 CR 승인 규칙으로 `agreed`가 된 기록.

집단은 처분 기록에 저장된 문서 entry 로 빌더 함수를 다시 불러 정하고, 빌더의 정규식을 직접 댄
결과와 어긋나는 건수를 함께 적는다. 목록 원천(`phase-1/{WG}/tdocs.jsonld`의 `tdoc:status`)과 상태
표기 정규화는 `measure_cross_source_agreement.py`의 것을 그대로 쓴다. 목록 상태가
`available`·`reserved`인 문서는 목록에 처분이 적히지 않은 경우이므로, 일치 비율을 전체 기록 기준과
그런 문서를 뺀 기준 두 가지로 적는다.

compound 기록은 일부 회의와 CR 문서에 몰려 있다. 문장 형태가 아니라 회의·문서 유형의 구성 때문에
생기는 차이를 가려내려고, 대조군을 같은 회의로 좁힌 분포, compound 의 층(회의, 회의×목록 유형)별
건수를 가중치로 쓴 대조군의 `noted` 기대 비율, 목록 유형(CR 여부)별 분포를 함께 적는다.
`noted` 뒤에 결과 동사가 있는데 주어 표기가 달라 규칙에 걸리지 않는 기록은 따로 나열한다.

사용: python3 measure_compound_noted_decisions.py --wg RAN1 --out <json>
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
BUILDER = Path("scripts/tsg/RAN/formal/common/document_decision_source.py")
sys.path.insert(0, str(ROOT / BUILDER.parent))
import document_decision_source as builder  # noqa: E402
from measure_cross_source_agreement import INSTANCES, LIST_WITHOUT_DISPOSITION, canonical  # noqa: E402

SECOND_OUTCOME_RULE = "noted_document_with_second_outcome_requires_adjudication"
OWN_CR_RULE = "noted_document_own_CR_descriptor_agreement"
DOCUMENT_EVENT = re.compile(r"DOC-(?P<meeting>.+)-(?P<subject>R[1-5]-\d{6,8})-b\d+")
DOCUMENT_NUMBER = re.compile(r"R[1-5]-\d{6,8}")
ABSENT = "absent_from_tdoc_list"
NO_STATUS = "status_not_recorded"
NOT_STATED = LIST_WITHOUT_DISPOSITION | {ABSENT, NO_STATUS}


def read_graph(relative: Path) -> tuple[list[dict], str]:
    data = (ROOT / relative).read_bytes()
    return json.loads(data)["@graph"], hashlib.sha256(data).hexdigest()


def share(part: float, whole: int) -> float | None:
    return round(part / whole, 4) if whole else None


def source_event(record: dict, method: dict) -> dict | None:
    """처분 기록에 저장된 문서 entry 로 빌더가 판정하는 결정 사건을 다시 만든다. 부록 표의 행은 대상이 아니다."""
    wg, decision_id, _ = record["dispositionId"].split(":")
    match = DOCUMENT_EVENT.fullmatch(decision_id)
    if match is None or "documentEntry" not in method:
        return None
    return {"subject_tdoc": match["subject"], "meeting_id": f"{wg}#{match['meeting']}",
            "document_entry": method["documentEntry"]}


def stated_field(entry: dict) -> str | None:
    """빌더가 `NOTED_THEN`에 대는 문장. 표지 없는 상태 줄에는 빌더와 같은 방식으로 주어를 붙인다."""
    text = builder.decision_field(entry["decisionText"], entry.get("typeEvidenceMethod") == builder.LIST_LINE_METHOD)
    if text is None:
        return None
    text = text.strip()
    if builder.DECISION.match(entry["decisionText"]):
        return text
    subject = builder.STATUS_SUBJECT.match(text)
    return "The document was " + text[subject.end() if subject else 0:]


def field_form(stated: str | None) -> tuple[str, str | None]:
    """판정 문장의 형태와 `noted` 뒤에 남은 글."""
    noted = builder.NOTED_THEN.fullmatch(stated) if stated else None
    if noted is None:
        return "other_subject_form", None
    rest = noted["rest"]
    if builder.SECOND_OUTCOME.search(rest):
        return "compound", rest
    return ("simple" if rest.strip() in {"", "."} else "noted_with_other_text"), rest


def summarize(rows: list[dict], code: str) -> dict:
    """목록 상태 분포와, 목록 상태가 `code`와 같은 기록의 수·비율."""
    counts = collections.Counter(row["listStatus"] for row in rows)
    stated = sum(n for status, n in counts.items() if status not in NOT_STATED)
    return {"records": len(rows), "distinctTargets": len({row["target"] for row in rows}),
            "listStatus": dict(counts.most_common()), "listStatesDisposition": stated,
            "listEqualsCode": {"code": code, "n": counts[code], "shareOfRecords": share(counts[code], len(rows)),
                               "shareOfListStated": share(counts[code], stated)}}


def by_list_type(rows: list[dict], code: str) -> dict:
    groups = collections.defaultdict(list)
    for row in rows:
        groups["cr" if row["listType"] == "tdoc:CR" else "other"].append(row)
    return {name: summarize(groups[name], code) for name in ("cr", "other")}


def expected_noted_share(compound: list[dict], simple: list[dict], stratum) -> dict:
    """compound 의 층별 건수를 가중치로, 같은 층의 simple 기록이 보인 `noted` 비율을 평균한다."""
    reference = collections.defaultdict(collections.Counter)
    for row in simple:
        reference[stratum(row)][row["listStatus"]] += 1
    weights = collections.Counter(stratum(row) for row in compound)
    covered = {key: n for key, n in weights.items() if key in reference}
    total = sum(covered.values())
    expected = sum(n * reference[key]["noted"] / sum(reference[key].values()) for key, n in covered.items())
    observed = sum(row["listStatus"] == "noted" for row in compound if stratum(row) in covered)
    return {"compoundRecordsInStrataWithSimple": total,
            "compoundRecordsInStrataWithoutSimple": len(compound) - total,
            "simpleExpectedNotedShareOfRecords": share(expected, total),
            "compoundObservedNotedShareOfRecords": share(observed, total)}


def outcome_table(rows: list[dict]) -> dict:
    """`noted` 뒤에서 처음 나오는 결과 동사별 목록 상태 분포."""
    groups = collections.defaultdict(list)
    for row in rows:
        groups[row["secondOutcome"]].append(row)
    table = {}
    for word, members in sorted(groups.items(), key=lambda item: -len(item[1])):
        cell = summarize(members, "noted")
        cell["listEqualsSecondOutcome"] = sum(row["listStatus"] == canonical(word) for row in members)
        named = [row for row in members if row["namedDocuments"]]
        unnamed = [row for row in members if not row["namedDocuments"]]
        cell["byOutput"] = {"names_other_document": summarize(named, "noted"),
                            "no_other_document_named": summarize(unnamed, "noted")}
        cell["namedDocumentListStatus"] = dict(collections.Counter(
            doc["listStatus"] for row in named for doc in row["namedDocuments"]).most_common())
        table[word] = cell
    return table


def measure(wg: str) -> dict:
    dispositions_path = INSTANCES / f"phase-2/{wg}/decision_dispositions.jsonld"
    tdocs_path = INSTANCES / f"phase-1/{wg}/tdocs.jsonld"
    records, dispositions_sha = read_graph(dispositions_path)
    tdoc_rows, tdocs_sha = read_graph(tdocs_path)
    tdocs = {row["@id"]: row for row in tdoc_rows}

    def list_status(identifier: str) -> str:
        row = tdocs.get(identifier)
        if row is None:
            return ABSENT
        return canonical(row["tdoc:status"]) if "tdoc:status" in row else NO_STATUS

    population = collections.Counter()
    forms = collections.Counter()
    label_less = collections.Counter()
    scopes = collections.defaultdict(collections.Counter)
    replay_noted = collections.Counter()
    replay_own = collections.Counter()
    rule_by_installed = collections.Counter()
    disagree = 0
    groups = collections.defaultdict(list)
    for record in records:
        method = json.loads(record["assessmentMethod"])
        noted = record["dispositionCode"] == "noted" and record["evidenceStatus"] == "source_verified"
        population["notedSourceVerified"] += noted
        event = source_event(record, method)
        if event is None:
            population["notedSourceVerifiedWithoutDocumentEntry"] += noted
            continue
        entry = event["document_entry"]
        target = record["targetTdocNumber"]
        code, _, rule = builder.classify_document_decision(event, target)
        installed = f"{record['dispositionCode']}|{record['evidenceStatus']}"
        if rule == SECOND_OUTCOME_RULE:
            rule_by_installed[f"{installed}|{method.get('rule')}"] += 1
        row = {"dispositionId": record["dispositionId"], "target": record["dispositionTarget"],
               "meeting": DOCUMENT_EVENT.fullmatch(record["dispositionId"].split(":")[1])["meeting"],
               "decisionText": entry["decisionText"], "listStatus": list_status(record["dispositionTarget"]),
               "listType": tdocs.get(record["dispositionTarget"], {}).get("@type")}
        if method.get("rule") == OWN_CR_RULE:
            replay_own[f"{installed} -> {code}|{rule}"] += 1
            if record["dispositionCode"] == "agreed" and record["evidenceStatus"] == "source_verified":
                groups["ownCr"].append({**row, "listedCR": entry.get("listedCR")})
        if not noted:
            continue
        population["notedSourceVerifiedWithDocumentEntry"] += 1
        replay_noted[f"{code}|{rule}"] += 1
        stated = stated_field(entry)
        form, rest = field_form(stated)
        held = rule == SECOND_OUTCOME_RULE
        disagree += held != (form == "compound")
        if held:
            form = "compound"
        forms[form] += 1
        label_less[form] += builder.DECISION.match(entry["decisionText"]) is None
        scopes[form][method.get("scope")] += 1
        if form == "compound":
            noted_match = builder.NOTED_THEN.fullmatch(stated)
            rest = noted_match["rest"]
            words = [word.lower() for word in builder.SECOND_OUTCOME.findall(rest)]
            named = [number for number in dict.fromkeys(DOCUMENT_NUMBER.findall(rest)) if number != target]
            row.update(secondOutcome=words[0], outcomeWords=list(dict.fromkeys(words)),
                       namedDocuments=[{"tdoc": number, "listStatus": list_status("tdoc:" + number)}
                                       for number in named])
        elif form == "other_subject_form" and stated:
            # 주어 표기가 달라 규칙이 읽지 않는 필드에서, 첫 `noted` 뒤에 결과 동사가 나오는 기록.
            first = re.search(r"\bnoted\b", stated, re.I)
            if first and builder.SECOND_OUTCOME.search(stated[first.end():]):
                groups["outcomeWordOutsideRule"].append(row)
        groups[form].append(row)

    compound, simple = groups["compound"], groups["simple"]
    compound_meetings = {row["meeting"] for row in compound}
    simple_same_meetings = [row for row in simple if row["meeting"] in compound_meetings]
    word_sets = collections.defaultdict(collections.Counter)
    for row in compound:
        word_sets["+".join(row["outcomeWords"])][row["listStatus"]] += 1
    return {
        "source": {"dispositions": dispositions_path.as_posix(), "dispositionsSha256": dispositions_sha,
                   "tdocList": tdocs_path.as_posix(), "tdocListSha256": tdocs_sha,
                   "builder": BUILDER.as_posix(),
                   "builderSha256": hashlib.sha256((ROOT / BUILDER).read_bytes()).hexdigest()},
        "population": {**dict(population), "fieldForms": dict(forms.most_common()),
                       "labelLessStatusLines": {form: n for form, n in label_less.items() if n},
                       "scope": {form: dict(counter) for form, counter in scopes.items()}},
        "builderReplay": {"notedSourceVerified": dict(replay_noted.most_common()),
                          "secondOutcomeRuleByInstalledCodeAndRule": dict(rule_by_installed.most_common()),
                          "ownCr": dict(replay_own.most_common()),
                          "builderAndPatternDisagree": disagree},
        "compound": {**summarize(compound, "noted"),
                     "byListType": by_list_type(compound, "noted"),
                     "byMeeting": dict(collections.Counter(row["meeting"] for row in compound).most_common()),
                     "bySecondOutcome": outcome_table(compound),
                     "byOutcomeWords": {words: {"records": sum(counter.values()), "listStatus": dict(counter.most_common())}
                                        for words, counter in sorted(word_sets.items(), key=lambda item: -sum(item[1].values()))},
                     "rows": sorted(compound, key=lambda row: row["dispositionId"])},
        "simple": {**summarize(simple, "noted"),
                   "byListType": by_list_type(simple, "noted"),
                   "inCompoundMeetings": {**summarize(simple_same_meetings, "noted"),
                                          "byListType": by_list_type(simple_same_meetings, "noted")},
                   "weightedByCompoundStrata": {
                       "meeting": expected_noted_share(compound, simple, lambda row: row["meeting"]),
                       "meetingAndListType": expected_noted_share(
                           compound, simple, lambda row: (row["meeting"], row["listType"] == "tdoc:CR"))}},
        "notedWithOtherText": summarize(groups["noted_with_other_text"], "noted"),
        "otherSubjectForm": summarize(groups["other_subject_form"], "noted"),
        "outcomeWordOutsideRule": {**summarize(groups["outcomeWordOutsideRule"], "noted"),
                                   "rows": sorted(groups["outcomeWordOutsideRule"], key=lambda row: row["dispositionId"])},
        "ownCr": {**summarize(groups["ownCr"], "agreed"),
                  "byListType": by_list_type(groups["ownCr"], "agreed"),
                  "rows": sorted(groups["ownCr"], key=lambda row: row["dispositionId"])},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--wg", nargs="+", required=True, help="작업반 이름 (예: RAN1)")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = {wg: measure(wg) for wg in args.wg}
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    for wg, row in result.items():
        for name in ("compound", "simple", "notedWithOtherText", "otherSubjectForm", "outcomeWordOutsideRule", "ownCr"):
            cell = row[name]
            print(wg, name, cell["records"], cell["listEqualsCode"], cell["listStatus"])
        for word, cell in row["compound"]["bySecondOutcome"].items():
            print(wg, "compound", word, cell["records"], cell["listStatus"])
        print(wg, "builderReplay", row["builderReplay"])


if __name__ == "__main__":
    main()
