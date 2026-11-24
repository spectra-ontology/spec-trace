"""과정 기록에서 직접 세는 네 가지 관찰 (모델 호출 없음).

`export_chain_records_sqlite.py` 가 내보낸 작업반별 SQLite 파일만 읽는다. 문항이 쓰는 것과 같은 기록이다.
처분은 문항과 같이 "원문 확인(source_verified)·문서 전체(whole_target)" 기록만 쓰고, 묶음 소속은 CR 쪽 기록
(`cr_in_pack`), 절 수정은 CR 쪽 기록(`cr_modifies_section`)을 쓴다. 각 수치의 분모와 제외 조건은 결과 JSON 의
`unit`·`excluded` 칸에 적는다.

(a) WG 처분 회의에서 총회 묶음의 TSG 회의까지의 경과
    회의 기록에는 날짜 칸이 없고(`meetingRecordKeys`), 묶음 기록의 총회 회의는 `RAN#79` 같은 차수뿐이다.
    WG 회의 차수와 총회 차수는 서로 다른 번호열이라 그대로 뺄 수 없으므로 총회 차수 안에서 간격을 센다.
    기준 총회는 그 WG 회의에서 처분된 CR 이 가장 많이 실린 총회(동률이면 앞선 차수)이고, 간격은
    (CR 이 실린 총회 차수 − 기준 총회 차수)다. 가장 이른 총회를 기준으로 한 간격도 함께 싣는다.
    한 총회에 CR 을 올린 WG 회의 수(`wgMeetingsPerTsgMeeting`)도 센다.
(b) 개정 사슬 길이: 문서의 `isRevisionOf` 를 처음 판까지 거슬러 올라간 연결 수.
(c) 처분 코드별 총회 묶음 등재 비율: 그 코드의 처분을 받은 CR 가운데 묶음에 실린 CR, 그리고 자신이나
    개정 후속판이 묶음에 실린 CR.
(d) 한 절을 고친 CR 수의 분포와 release 별 추이.

사용: python3 measure_process_record_observations.py --db-dir <dir> --wg RAN1 RAN2 --manifest <json> --out <json>
저장소 루트에서 실행한다.
"""
from __future__ import annotations

import argparse
import collections
import json
import sqlite3
import statistics
from pathlib import Path

# 문항이 쓰는 처분 기록: 원문 확인·문서 전체. 회의는 처분이 가리키는 결정 기록의 회의다.
VERIFIED_DISPOSITION = """
    SELECT DISTINCT d.target AS doc, d.code AS code, r.meeting_id AS meeting
    FROM disposition d JOIN resolution r ON r.id = d.resolution_id
    WHERE d.evidence_status = 'source_verified' AND d.scope = 'whole_target'"""


def histogram(values) -> dict[str, int]:
    return {str(key): count for key, count in sorted(collections.Counter(values).items())}


def summary(values: list[int]) -> dict:
    if not values:
        return {"n": 0}
    return {"n": len(values), "min": min(values), "median": statistics.median(values),
            "mean": round(statistics.fmean(values), 3), "max": max(values)}


def elapsed(db: sqlite3.Connection) -> dict:
    rows = db.execute(f"""
        SELECT DISTINCT v.doc, v.code, v.meeting, p.tsg_number
        FROM ({VERIFIED_DISPOSITION}) v
        JOIN document doc ON doc.id = v.doc AND doc.doc_type = 'tdoc:CR'
        JOIN cr_in_pack m ON m.cr = v.doc JOIN cr_pack p ON p.id = m.pack_id
        WHERE p.tsg_number IS NOT NULL""").fetchall()
    # 단위: (CR, WG 처분 회의, 총회 차수). 한 CR 이 같은 회의에서 처분 코드를 둘 받아도 한 번만 센다.
    units = sorted({(doc, meeting, tsg) for doc, _, meeting, tsg in rows})
    per_meeting: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for _, meeting, tsg in units:
        per_meeting[meeting][tsg] += 1
    modal = {meeting: min(t for t, n in counts.items() if n == max(counts.values()))
             for meeting, counts in per_meeting.items()}
    earliest = {meeting: min(counts) for meeting, counts in per_meeting.items()}
    feeding: dict[int, set[str]] = collections.defaultdict(set)
    for _, meeting, tsg in units:
        feeding[tsg].add(meeting)
    from_modal = [tsg - modal[meeting] for _, meeting, tsg in units]
    from_earliest = [tsg - earliest[meeting] for _, meeting, tsg in units]
    by_code: dict[str, list[int]] = collections.defaultdict(list)
    for doc, code, meeting, tsg in sorted(set(rows)):
        by_code[code].append(tsg - modal[meeting])
    return {
        "unit": "원문 확인·문서 전체 처분을 받고 총회 묶음에 실린 CR 문서의 (CR, WG 처분 회의, 총회 차수) 조합",
        "measure": "총회 차수 간격. 날짜가 기록에 없어 일수는 세지 못한다",
        "units": len(units), "crDocuments": len({doc for doc, _, _ in units}), "wgMeetings": len(per_meeting),
        "wgMeetingsWhoseCrsReachOneTsgMeeting": sum(len(c) == 1 for c in per_meeting.values()),
        "tsgMeetingsPerWgMeeting": histogram(len(c) for c in per_meeting.values()),
        "wgMeetingsPerTsgMeeting": histogram(len(m) for m in feeding.values()),
        "unitsAtTsgMeetingsFedByMoreThanOneWgMeeting": sum(len(feeding[tsg]) > 1 for _, _, tsg in units),
        "gapFromModalTsgMeeting": {"histogram": histogram(from_modal), **summary(from_modal),
                                   "atModal": sum(g == 0 for g in from_modal),
                                   "later": sum(g > 0 for g in from_modal), "earlier": sum(g < 0 for g in from_modal)},
        "gapFromEarliestTsgMeeting": {"histogram": histogram(from_earliest), **summary(from_earliest)},
        "gapFromModalByDispositionCode": {
            code: {"units": len(gaps), "atModal": sum(g == 0 for g in gaps), "later": sum(g > 0 for g in gaps),
                   "earlier": sum(g < 0 for g in gaps)} for code, gaps in sorted(by_code.items())},
        "excluded": {
            "packLinksWithoutTsgNumber": db.execute(
                "SELECT COUNT(*) FROM cr_in_pack m JOIN cr_pack p ON p.id = m.pack_id WHERE p.tsg_number IS NULL").fetchone()[0],
            "packedCrDocumentsWithoutVerifiedWholeDisposition": db.execute(f"""
                SELECT COUNT(DISTINCT m.cr) FROM cr_in_pack m JOIN document doc ON doc.id = m.cr AND doc.doc_type = 'tdoc:CR'
                WHERE m.cr NOT IN (SELECT doc FROM ({VERIFIED_DISPOSITION}))""").fetchone()[0],
            "packLinksWhoseCrIsNotACrDocumentRecord": db.execute("""
                SELECT COUNT(*) FROM cr_in_pack m
                WHERE NOT EXISTS (SELECT 1 FROM document doc WHERE doc.id = m.cr AND doc.doc_type = 'tdoc:CR')""").fetchone()[0]},
    }


def revision_chains(db: sqlite3.Connection) -> dict:
    kind = dict(db.execute("SELECT id, doc_type FROM document"))
    earlier_of: dict[str, list[str]] = collections.defaultdict(list)
    has_later = set()
    for earlier, later in db.execute("SELECT earlier, later FROM revision"):
        earlier_of[later].append(earlier)
        has_later.add(earlier)
    multiple = sum(len(v) > 1 for v in earlier_of.values())
    cycles = 0

    def depth(identifier: str) -> tuple[int, bool]:
        """처음 판까지의 연결 수와, 사슬이 문서 목록 밖의 앞선 판에서 끝나는지."""
        nonlocal cycles
        hops, seen, current = 0, {identifier}, identifier
        while earlier_of.get(current):
            current = earlier_of[current][0]
            if current in seen:
                cycles += 1
                break
            seen.add(current)
            hops += 1
        return hops, current not in kind

    terminal = [identifier for identifier in kind if identifier not in has_later]
    depths = {identifier: depth(identifier) for identifier in terminal}
    packed = [cr for (cr,) in db.execute("SELECT DISTINCT cr FROM cr_in_pack") if cr in kind]
    packed_depths = [depth(cr)[0] for cr in packed]
    all_lengths = [hops for hops, _ in depths.values()]
    cr_lengths = [depths[i][0] for i in terminal if kind[i] == "tdoc:CR"]
    return {
        "unit": "뒤 판이 없는 문서(사슬의 마지막 판). 길이는 그 문서에서 처음 판까지의 isRevisionOf 연결 수이고 0 은 개정 관계가 없는 문서",
        "documents": len(kind), "revisionLinks": sum(len(v) for v in earlier_of.values()),
        "terminalDocuments": {"histogram": histogram(all_lengths), **summary(all_lengths),
                              "withAtLeastOneRevision": sum(v > 0 for v in all_lengths)},
        "terminalCrDocuments": {"histogram": histogram(cr_lengths), **summary(cr_lengths),
                                "withAtLeastOneRevision": sum(v > 0 for v in cr_lengths)},
        "crDocumentsInPack": {
            "unit": "총회 묶음에 실렸고 문서 기록이 있는 문서. 값은 그 문서에서 처음 판까지의 연결 수",
            "histogram": histogram(packed_depths), **summary(packed_depths),
            "withAtLeastOneEarlierVersion": sum(v > 0 for v in packed_depths)},
        "excluded": {"note": "앞선 판이 이 작업반의 문서 목록에 없는 연결도 길이에 1 로 센다",
                     "chainsEndingAtAnEarlierVersionOutsideTheDocumentList": sum(out for _, out in depths.values()),
                     "documentsWithMoreThanOneEarlierVersion": multiple, "cyclesStopped": cycles,
                     "revisionLinksFromADocumentToItself": db.execute(
                         "SELECT COUNT(*) FROM revision WHERE earlier = later").fetchone()[0]},
    }


def pack_rate_by_code(db: sqlite3.Connection) -> dict:
    packed = {cr for (cr,) in db.execute("SELECT DISTINCT cr FROM cr_in_pack")}
    later_of: dict[str, list[str]] = collections.defaultdict(list)
    for earlier, later in db.execute("SELECT earlier, later FROM revision"):
        later_of[earlier].append(later)

    def reaches_pack(identifier: str) -> bool:
        seen, queue = {identifier}, [identifier]
        while queue:
            current = queue.pop()
            if current in packed:
                return True
            for later in later_of.get(current, ()):
                if later not in seen:
                    seen.add(later)
                    queue.append(later)
        return False

    codes: dict[str, set[str]] = collections.defaultdict(set)
    for doc, code in db.execute(f"""
            SELECT DISTINCT v.doc, v.code FROM ({VERIFIED_DISPOSITION}) v
            JOIN document doc ON doc.id = v.doc AND doc.doc_type = 'tdoc:CR'"""):
        codes[code].add(doc)
    everyone = set().union(*codes.values()) if codes else set()
    reach = {doc: reaches_pack(doc) for doc in everyone}
    code_count = collections.Counter(doc for docs in codes.values() for doc in docs)
    return {
        "unit": "그 코드의 원문 확인·문서 전체 처분을 하나 이상 받은 CR 문서(문서 목록의 유형이 CR). 코드를 둘 이상 받은 문서는 코드마다 센다",
        "crDocumentsWithVerifiedWholeDisposition": len(everyone),
        "crDocumentsWithMoreThanOneCode": sum(n > 1 for n in code_count.values()),
        "byCode": {code: {"crDocuments": len(docs), "inPack": len(docs & packed),
                          "inPackSelfOrLaterVersion": sum(reach[d] for d in docs)}
                   for code, docs in sorted(codes.items(), key=lambda kv: -len(kv[1]))},
        "excluded": {
            "crDocumentsWithoutVerifiedWholeDisposition": db.execute(f"""
                SELECT COUNT(*) FROM document WHERE doc_type = 'tdoc:CR'
                AND id NOT IN (SELECT doc FROM ({VERIFIED_DISPOSITION}))""").fetchone()[0],
            "crDocuments": db.execute("SELECT COUNT(*) FROM document WHERE doc_type = 'tdoc:CR'").fetchone()[0]},
    }


def clause_changes(db: sqlite3.Connection) -> dict:
    links = db.execute("""
        SELECT DISTINCT c.section_id, c.cr, s.release, doc.target_release, s.clause IS NOT NULL, doc.id IS NOT NULL
        FROM cr_modifies_section c JOIN section s ON s.id = c.section_id
        LEFT JOIN document doc ON doc.id = c.cr""").fetchall()
    same = [(section, cr, release) for section, cr, release, target, parsed, known in links
            if parsed and known and target == release]
    per_section = collections.Counter(section for section, _, _ in same)
    release_of = {section: release for section, _, release in same}
    by_release: dict[str, list[int]] = collections.defaultdict(list)
    for section, count in per_section.items():
        by_release[release_of[section]].append(count)
    any_release = collections.Counter(section for section, *_ in links)
    packed = db.execute("SELECT COUNT(DISTINCT cr) FROM cr_in_pack").fetchone()[0]
    with_links = db.execute("SELECT COUNT(DISTINCT cr) FROM cr_modifies_section").fetchone()[0]
    with_links_packed = db.execute(
        "SELECT COUNT(DISTINCT cr) FROM cr_modifies_section WHERE cr IN (SELECT cr FROM cr_in_pack)").fetchone()[0]
    return {
        "unit": "CR 이 하나 이상 고친 절(규격·release·절 번호). 값은 대상 release 가 절의 release 와 같은 서로 다른 CR 문서 수",
        "sections": len(per_section), "sectionCrLinks": len(same),
        "crsPerSection": {"histogram": histogram(per_section.values()), **summary(list(per_section.values())),
                          "sectionsModifiedByOneCr": sum(v == 1 for v in per_section.values())},
        "byRelease": {release: {"sections": len(counts), "sectionCrLinks": sum(counts),
                                "meanCrsPerSection": round(statistics.fmean(counts), 3),
                                "medianCrsPerSection": statistics.median(counts), "maxCrsPerSection": max(counts),
                                "sectionsModifiedByOneCr": sum(v == 1 for v in counts)}
                      for release, counts in sorted(by_release.items(), key=lambda kv: int(kv[0].split("-")[1]))},
        "withoutReleaseCondition": {"sections": len(any_release), "sectionCrLinks": len(links),
                                    **summary(list(any_release.values()))},
        "coverage": {"crsInPack": packed, "crsWithSectionLinks": with_links,
                     "crsInPackWithSectionLinks": with_links_packed,
                     "note": "절 기록은 CR 표지에서 절 번호가 추출된 CR 에만 있다. 한 번도 수정되지 않은 절은 이 기록에 없다"},
        "excluded": {
            "linksWhoseCrTargetReleaseDiffersFromSectionRelease": sum(
                1 for *_, release, target, parsed, known in links if parsed and known and target is not None and target != release),
            "linksWhoseCrHasNoTargetRelease": sum(1 for *_, target, parsed, known in links if parsed and known and target is None),
            "linksWhoseCrHasNoDocumentRecord": sum(1 for *_, known in links if not known),
            "linksWhoseSectionIdentifierIsNotParsed": sum(1 for *_, parsed, _ in links if not parsed)},
    }


def record_notes(db: sqlite3.Connection) -> dict:
    """참조 SQL 과 생성기의 읽기가 갈릴 수 있는 기록 수."""
    one = lambda sql: db.execute(sql).fetchone()[0]
    return {
        "resolutionsWhoseMeetingHasNoMeetingRecord": one(
            "SELECT COUNT(*) FROM resolution WHERE meeting_id NOT IN (SELECT id FROM meeting)"),
        "verifiedWholeDispositionsAtSuchMeetings": one(f"""
            SELECT COUNT(*) FROM ({VERIFIED_DISPOSITION}) v WHERE v.meeting NOT IN (SELECT id FROM meeting)"""),
        "dispositionsWhoseResolutionHasNoMeeting": one(
            "SELECT COUNT(*) FROM disposition WHERE resolution_id NOT IN (SELECT id FROM resolution)"),
        "packLinksOnlyInCrSideRecord": one(
            "SELECT COUNT(*) FROM (SELECT cr, pack_id FROM cr_in_pack EXCEPT SELECT cr, pack_id FROM pack_member)"),
        "packLinksOnlyInPackSideRecord": one(
            "SELECT COUNT(*) FROM (SELECT cr, pack_id FROM pack_member EXCEPT SELECT cr, pack_id FROM cr_in_pack)"),
        "sectionLinksOnlyInCrSideRecord": one(
            "SELECT COUNT(*) FROM (SELECT cr, section_id FROM cr_modifies_section EXCEPT SELECT cr, section_id FROM section_modified_by)"),
        "sectionLinksOnlyInSectionSideRecord": one(
            "SELECT COUNT(*) FROM (SELECT cr, section_id FROM section_modified_by EXCEPT SELECT cr, section_id FROM cr_modifies_section)"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--db-dir", type=Path, required=True)
    parser.add_argument("--wg", nargs="+", required=True)
    parser.add_argument("--manifest", type=Path, required=True, help="내보내기 기록(회의 기록의 칸 목록을 읽는다)")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    exports = json.loads(args.manifest.read_text())["exports"]
    report = {"dateFields": {
        "meetingRecordKeys": {wg: exports[wg]["meetingRecordKeys"] for wg in args.wg},
        "finding": "회의 기록과 묶음 기록에 날짜 칸이 없다. 문서 기록에는 번호 예약·올린 시각(tdoc:reservationDate·"
                   "tdoc:uploadedDate)이 있으나 회의 날짜가 아니고 묶음에는 없어, WG 회의에서 총회까지의 일수는 이 기록으로 셀 수 없다"},
        "byWg": {}}
    for wg in args.wg:
        db = sqlite3.connect(f"file:{args.db_dir / (wg + '.sqlite')}?mode=ro", uri=True)
        report["byWg"][wg] = {"a_dispositionToPlenary": elapsed(db), "b_revisionChainLength": revision_chains(db),
                              "c_packRateByDispositionCode": pack_rate_by_code(db), "d_crsPerClause": clause_changes(db),
                              "recordNotes": record_notes(db)}
        db.close()
        print(wg, "done", flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
