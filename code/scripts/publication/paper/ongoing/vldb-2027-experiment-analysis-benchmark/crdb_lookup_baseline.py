"""공식 3GPP CR 데이터베이스(CRDB) 한 벌만으로 추적 사슬 문항에 답하는 결정적 기준선을 만든다 (모델 호출 없음).

CRDB 는 3GPP 가 www.3gpp.org/ftp/Information/Databases/Change_Request/ 에 올리는 `CRDB_<날짜>.zip` 이다.
압축 안의 엑셀 파일 한 개가 `Query1` 시트에 CR 개정본마다 한 행을 싣는다(18 칸). 이 스크립트는 그 zip 을 풀어 쓰지
않고 표준 라이브러리(zipfile · xml.etree)로 바로 읽는다. 내려받은 파일은 신뢰하지 않는 자료이므로 이 스크립트는
`python3 -I` 로 실행하고, zip 은 이 스크립트와 다른 빈 디렉토리에 둔다.

하위 명령
- answer: 문항마다 문항 자신의 입력(id · wg · family · anchor · question · fields)과 CRDB 행만으로 답 행을 만든다.
  문항 파일의 나머지 키(gold · evidence · expectsEmpty · hops)는 읽는 즉시 버린다(`load_inputs`). 그래서 답은 정답이나
  다른 풀이의 응답에 기대지 않는다. 결과는 WG 마다 응답 파일 하나(`<WG>_crdb_lookup.jsonl`)다. 채점기
  `score_chain_eval.py` 가 응답 파일의 첫 응답이 가진 wg 로 채점 범위를 정하기 때문이다. 문항마다 쓴 CRDB 행은
  `crdb_lookup_trace.jsonl` 에, 스냅숏 출처와 고정 규칙은 `crdb_lookup_run.json` 에 적는다.
- summarize: 채점이 끝난 뒤 정답과 CRDB 값을 맞대어 종류·층마다 정확 일치 수를 세고, 표현 가능 문항(CRDB 칸으로
  표현 가능한 다섯 종류)의 오답을 원인 갈래로 나눈다. 정답은 이 사후 분석에만 쓴다. 채점기와 같은 행 비교 함수
  (`score_chain_eval.score`)로 문항별 일치를 다시 구하고, 그 합이 채점기 출력과 같은지 확인한다.

고정 규칙(`RULES`)은 채점 전에 정했고 실행 결과 파일에 그대로 적는다. 요지는 다음과 같다.
- 칸 대응: 처분 = `WG-level status`, WG 회의 = `Meeting WG-level`, 문서 = `WG Tdoc`, CR 묶음 = `TSG Tdoc`,
  총회 회의 = `Meeting TSG-level`, 개정 차례 = 같은 (`Spec number`, `CR number`) 안의 `Revision`.
- WG 칸(처분 · WG 회의)은 문서에 딸린 값이고 TSG 칸(묶음 · 총회 회의)은 제출에 딸린 값이다. 같은 WG Tdoc 이 여러 행에
  나오면(같은 CR 을 다른 총회에 다시 올린 행 등) 두 갈래를 따로 모은 뒤 곱해 답 행을 만든다.
- 질문이 요구하는 칸이 하나라도 CRDB 에 비어 있으면(`-` 또는 빈 칸) 그 답 행을 만들지 않는다.
- `pack_lookup_empty` 는 `pack_lookup` 과 같은 질문 틀이므로 같은 규칙으로 푼다. 종류 이름으로 빈 답을 정하지 않는다.
- `full_chain` · `clause_history` 는 CRDB 에 고친 절 칸이 없어 표현할 수 없다. 빈 행으로 답하고 `notExpressible` 로 적는다.

사용(저장소 루트에서 실행):
  python3 -I scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/crdb_lookup_baseline.py answer \
      --crdb-zip <CRDB_*.zip> --source-url <URL> --items <jsonl> [<jsonl> ...] --out-dir <dir>
  python3 scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/score_chain_eval.py --items ... \
      --responses <dir>/RAN1_crdb_lookup.jsonl ... --out <dir>/scores.json
  python3 -I scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/crdb_lookup_baseline.py summarize \
      --crdb-zip <CRDB_*.zip> --items <jsonl> [<jsonl> ...] --out-dir <dir> --scores <dir>/scores.json
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import io
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

METHOD = "crdb_lookup"
MODEL = "none"
INPUT_KEYS = ("id", "wg", "family", "anchor", "question", "fields")
EXPRESSIBLE = ("pack_lookup", "pack_lookup_empty", "pack_origin", "disposition_pack", "revision_chain")
NOT_EXPRESSIBLE = ("full_chain", "clause_history")
SHEET = "Query1"
COLUMNS = ("Spec number", "CR number", "Revision", "Subject", "Meeting WG-level", "WG-level status",
           "Meeting TSG-level", "TSG-level status", "WGSourceOrganizations", "TSGSourceOrganizations", "WG Tdoc",
           "Category", "Release", "Version-current", "Version-new", "Date", "TSG Tdoc", "Work items")
KEPT = {"spec": "Spec number", "cr": "CR number", "revision": "Revision", "wgMeeting": "Meeting WG-level",
        "wgStatus": "WG-level status", "tsgMeeting": "Meeting TSG-level", "tsgStatus": "TSG-level status",
        "wgTdoc": "WG Tdoc", "tsgTdoc": "TSG Tdoc", "release": "Release"}
MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PKG = "{http://schemas.openxmlformats.org/package/2006/relationships}"
CR_IN_QUESTION = re.compile(r"\(CR (\S+) to TS (\S+)\)")
SCORER = Path(__file__).with_name("score_chain_eval.py")
REPO = Path(__file__).resolve().parents[5]

RULES = {
    "inputsUsed": "Answers read only the item keys id, wg, family, anchor, question and fields, and the CRDB "
                  "rows. gold, evidence, expectsEmpty and hops are dropped when the item file is read; no "
                  "earlier response file is read.",
    "columnMapping": {
        "document / final_document": "WG Tdoc",
        "disposition": "WG-level status",
        "wg_meeting": "Meeting WG-level",
        "cr_pack": "TSG Tdoc",
        "tsg_meeting": "Meeting TSG-level",
        "revision order": "Revision within one (Spec number, CR number)",
        "not used": "Subject, TSG-level status, source organisations, Category, Release, versions, Date, "
                    "Work items",
    },
    "familyRules": {
        "pack_lookup": "rows of the anchor WG Tdoc -> one row [TSG Tdoc, Meeting TSG-level] per distinct "
                       "submission whose TSG Tdoc is an RP document and whose meeting is a TSG RAN plenary",
        "pack_lookup_empty": "same question template and same rule as pack_lookup; the family label is not used",
        "disposition_pack": "rows of the anchor WG Tdoc -> every distinct (WG-level status, Meeting WG-level) "
                            "with both filled, times every distinct (TSG Tdoc, Meeting TSG-level) as in "
                            "pack_lookup",
        "pack_origin": "rows whose TSG Tdoc is the anchor pack and whose WG Tdoc is a document of the item's "
                       "WG -> for each such WG Tdoc, every distinct (WG-level status, Meeting WG-level) with "
                       "both filled, gathered over that WG Tdoc's rows of the same (Spec number, CR number)",
        "revision_chain": "rows of the anchor WG Tdoc give (Spec number, CR number, Revision); every other WG "
                          "Tdoc of the item's WG in the same (Spec number, CR number) with a strictly higher "
                          "Revision -> every distinct WG-level status times every distinct RP TSG Tdoc of that "
                          "document; a document with no status or no RP pack gives no row",
        "full_chain": "not expressible: the CRDB has no modified-clause column; answered with no rows",
        "clause_history": "not expressible: the CRDB has no modified-clause column; answered with no rows",
    },
    "normalisation": {
        "document numbers": "upper-case, whitespace and parentheses removed, runs of '-' collapsed to one "
                            "('RP--080615' -> 'RP-080615'); no suffix is stripped ('R4-79AH-0008' stays as it is)",
        "WG document of RANn": "normalised WG Tdoc starting with 'Rn-' (RAN5 also 'R5S', its signalling "
                               "sub-group prefix)",
        "CR pack": "normalised TSG Tdoc matching RP-<digits>; any other TSG Tdoc value counts as no pack",
        "meeting labels": "surrounding and inner whitespace removed, leading '3GPP' removed, '-#' -> '#' "
                          "('3GPPRAN1#100-bis-e' -> 'RAN1#100-bis-e', '3GPPRAN-#18' -> 'RAN#18'); a TSG "
                          "meeting counts only when it starts with 'RAN#'; bis spellings are left to the "
                          "scorer's meeting_spelling",
        "CR number": "compared upper-case without leading zeros ('0058' == '58')",
        "Revision": "'-' and '0' are revision 0; other values are their integer; a non-numeric value has no "
                    "order and is never 'later'",
        "empty cell": "'-', '' and a missing cell are no value",
    },
    "statusVocabulary": {
        "source": "the answer rules every method receives (run_chain_eval.ANSWER_RULES): 'Disposition values "
                  "are lower-case codes such as agreed, revised, noted, endorsed, withdrawn, not_pursued'",
        "mapping": "CRDB WG-level status lower-cased with spaces replaced by '_' (agreed, revised, noted, "
                   "endorsed, withdrawn, 'not pursued' -> not_pursued, postponed, merged, rejected, "
                   "'not treated' -> not_treated, reissued); '-' is no disposition",
    },
    "multipleRows": {
        "same WG Tdoc in several rows": "WG-level values (status, WG meeting) and TSG-level values (pack, "
                                        "plenary meeting) are gathered separately as distinct pairs and "
                                        "combined; a row with WG-level status '-' still contributes its pack",
        "question names CR and spec": "pack_lookup, pack_lookup_empty and disposition_pack questions state "
                                      "'(CR <n> to TS <spec>)'; when some rows of the WG Tdoc match that CR "
                                      "and spec only those rows are used, otherwise all rows of the WG Tdoc",
        "several CRDB revisions": "revision_chain keeps every later revision that satisfies the conditions; "
                                  "no single 'final' revision is chosen",
        "incomplete answer row": "a requested field that the CRDB leaves empty drops that answer row",
    },
}


def load_inputs(paths: list[Path]) -> list[dict]:
    """문항 파일을 읽어 허용된 입력 키만 남긴다. 정답·근거 키는 여기서 버려져 답 만들기에 닿지 않는다."""
    items = []
    for path in paths:
        for line in path.read_text().splitlines():
            record = json.loads(line)
            items.append({key: record[key] for key in INPUT_KEYS})
    return items


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def column_index(reference: str) -> int:
    number = 0
    for letter in re.match(r"[A-Z]+", reference).group(0):
        number = number * 26 + ord(letter) - 64
    return number - 1


def read_query1(zip_path: Path) -> tuple[list[dict], dict]:
    """CRDB zip 안 엑셀의 Query1 시트를 행 사전 목록으로 읽는다. 파일을 디스크에 풀지 않는다."""
    outer = zipfile.ZipFile(zip_path)
    members = [info for info in outer.infolist() if info.filename.lower().endswith(".xlsx")]
    if len(members) != 1:
        raise SystemExit(f"expected one .xlsx member in {zip_path.name}, found {len(members)}")
    member = members[0]
    inner = zipfile.ZipFile(io.BytesIO(outer.read(member.filename)))
    workbook = ET.fromstring(inner.read("xl/workbook.xml"))
    sheet_ids = {sheet.get("name"): sheet.get(REL + "id") for sheet in workbook.iter(MAIN + "sheet")}
    if SHEET not in sheet_ids:
        raise SystemExit(f"sheet {SHEET} not in {member.filename}: {sorted(sheet_ids)}")
    rels = ET.fromstring(inner.read("xl/_rels/workbook.xml.rels"))
    target = next(rel.get("Target") for rel in rels.iter(PKG + "Relationship") if rel.get("Id") == sheet_ids[SHEET])
    sheet_path = target.lstrip("/") if target.startswith("/") else "xl/" + target
    shared = []
    if "xl/sharedStrings.xml" in inner.namelist():
        for _, element in ET.iterparse(inner.open("xl/sharedStrings.xml")):
            if element.tag == MAIN + "si":
                shared.append("".join(text.text or "" for text in element.iter(MAIN + "t")))
                element.clear()
    header, rows = None, []
    for _, element in ET.iterparse(inner.open(sheet_path)):
        if element.tag != MAIN + "row":
            continue
        cells, position = {}, 0
        for cell in element.findall(MAIN + "c"):
            position = column_index(cell.get("r")) if cell.get("r") else position
            kind, value = cell.get("t"), cell.find(MAIN + "v")
            if kind == "s":
                text = shared[int(value.text)]
            elif kind == "inlineStr":
                text = "".join(part.text or "" for part in cell.iter(MAIN + "t"))
            else:
                text = value.text if value is not None else None
            cells[position] = text
            position += 1
        element.clear()
        values = [cells.get(index) for index in range(len(COLUMNS))]
        if header is None:
            header = values
            if tuple(header) != COLUMNS:
                raise SystemExit(f"unexpected {SHEET} header: {header}")
            continue
        row = dict(zip(COLUMNS, values))
        rows.append({name: (row[column] or "") for name, column in KEPT.items()})
    provenance = {"zipFile": zip_path.name, "zipBytes": zip_path.stat().st_size, "zipSha256": file_sha256(zip_path),
                  "xlsxMember": member.filename, "xlsxBytes": member.file_size,
                  "xlsxZipTimestamp": "%04d-%02d-%02dT%02d:%02d:%02d" % member.date_time,
                  "sheet": SHEET, "sheetPath": sheet_path, "dataRows": len(rows), "columns": list(COLUMNS)}
    return rows, provenance


def no_value(text: str) -> bool:
    return text.strip() in ("", "-")


def norm_doc(text: str) -> str:
    return "" if no_value(text) else re.sub(r"-+", "-", re.sub(r"[\s()]", "", text.upper()))


def norm_meeting(text: str) -> str:
    if no_value(text):
        return ""
    label = re.sub(r"\s", "", text)
    label = label[4:] if label.upper().startswith("3GPP") else label
    return label.replace("-#", "#")


def norm_status(text: str) -> str:
    return "" if no_value(text) else re.sub(r"\s+", "_", text.strip().lower())


def norm_cr(text: str) -> str:
    return text.strip().upper().lstrip("0") or "0"


def revision_order(text: str) -> int | None:
    value = text.strip()
    if value in ("", "-"):
        return 0
    return int(value) if value.isdigit() else None


def is_pack(document: str) -> bool:
    return re.fullmatch(r"RP-\d+", document) is not None


def is_plenary(meeting: str) -> bool:
    return meeting.startswith("RAN#")


def is_wg_document(document: str, wg: str) -> bool:
    number = wg.removeprefix("RAN")
    return document.startswith(f"R{number}-") or (number == "5" and document.startswith("R5S"))


class CRDB:
    """정규화한 칸과 세 가지 찾기 색인(WG Tdoc · TSG Tdoc · (규격, CR 번호))."""

    def __init__(self, rows: list[dict]):
        self.rows = []
        self.by_document = collections.defaultdict(list)
        self.by_pack = collections.defaultdict(list)
        self.by_cr = collections.defaultdict(list)
        for index, raw in enumerate(rows):
            row = {"row": index, "spec": raw["spec"].strip(), "cr": norm_cr(raw["cr"]),
                   "revision": revision_order(raw["revision"]), "document": norm_doc(raw["wgTdoc"]),
                   "status": norm_status(raw["wgStatus"]), "wgMeeting": norm_meeting(raw["wgMeeting"]),
                   "pack": norm_doc(raw["tsgTdoc"]), "tsgMeeting": norm_meeting(raw["tsgMeeting"]),
                   "raw": raw}
            self.rows.append(row)
            if row["document"]:
                self.by_document[row["document"]].append(row)
            if row["pack"]:
                self.by_pack[row["pack"]].append(row)
            self.by_cr[(row["spec"], row["cr"])].append(row)

    def document_rows(self, document: str, spec: str | None = None, cr: str | None = None) -> tuple[list, bool]:
        rows = self.by_document.get(document, [])
        if spec is None:
            return rows, False
        matching = [row for row in rows if row["spec"] == spec and row["cr"] == norm_cr(cr)]
        return (matching, True) if matching else (rows, False)


def dispositions(rows: list[dict], need_meeting: bool) -> list[tuple[str, str]]:
    return sorted({(row["status"], row["wgMeeting"]) for row in rows
                   if row["status"] and (row["wgMeeting"] or not need_meeting)})


def submissions(rows: list[dict], need_meeting: bool) -> list[tuple[str, str]]:
    return sorted({(row["pack"], row["tsgMeeting"]) for row in rows
                   if is_pack(row["pack"]) and (is_plenary(row["tsgMeeting"]) or not need_meeting)})


def trace_row(row: dict) -> dict:
    return {"row": row["row"], **row["raw"]}


def answer(item: dict, db: CRDB) -> tuple[list[list[str]], dict]:
    family, anchor = item["family"], item["anchor"].split(":", 1)[1]
    trace = {"id": item["id"], "wg": item["wg"], "family": family, "expressible": family in EXPRESSIBLE}
    if family in NOT_EXPRESSIBLE:
        trace["note"] = "not expressible: the CRDB has no modified-clause column"
        return [], trace
    if family in ("pack_lookup", "pack_lookup_empty", "disposition_pack"):
        stated = CR_IN_QUESTION.search(item["question"])
        spec, cr = (stated.group(2), stated.group(1)) if stated else (None, None)
        rows, filtered = db.document_rows(norm_doc(anchor), spec, cr)
        trace.update({"document": norm_doc(anchor), "statedCr": cr, "statedSpec": spec,
                      "crSpecFilterApplied": filtered, "crdbRows": [trace_row(row) for row in rows]})
        packs = submissions(rows, need_meeting=True)
        if family == "disposition_pack":
            answer_rows = [[status, meeting, pack, plenary] for status, meeting in dispositions(rows, True)
                           for pack, plenary in packs]
        else:
            answer_rows = [[pack, plenary] for pack, plenary in packs]
        return answer_rows, trace
    if family == "pack_origin":
        pack = norm_doc(anchor.split("/", 1)[1])
        pack_rows = db.by_pack.get(pack, [])
        answer_rows, used = set(), {}
        for row in pack_rows:
            if not is_wg_document(row["document"], item["wg"]):
                continue
            siblings = [other for other in db.by_document[row["document"]]
                        if (other["spec"], other["cr"]) == (row["spec"], row["cr"])]
            for other in siblings:
                used[other["row"]] = other
            answer_rows.update((row["document"], status, meeting) for status, meeting in dispositions(siblings, True))
        trace.update({"pack": pack, "packRows": [trace_row(row) for row in pack_rows],
                      "documentRows": [trace_row(row) for row in used.values()]})
        return [list(row) for row in sorted(answer_rows)], trace
    if family == "revision_chain":
        document = norm_doc(anchor)
        anchor_rows = db.by_document.get(document, [])
        answer_rows, later_rows = set(), {}
        for start in anchor_rows:
            if start["revision"] is None:
                continue
            later = collections.defaultdict(list)
            for row in db.by_cr[(start["spec"], start["cr"])]:
                if (row["revision"] is not None and row["revision"] > start["revision"]
                        and row["document"] != document and is_wg_document(row["document"], item["wg"])):
                    later[row["document"]].append(row)
            for later_document in later:
                rows = [row for row in db.by_document[later_document]
                        if (row["spec"], row["cr"]) == (start["spec"], start["cr"])]
                for row in rows:
                    later_rows[row["row"]] = row
                answer_rows.update((later_document, status, pack) for status, _ in dispositions(rows, False)
                                   for pack, _ in submissions(rows, False))
        cr_rows = {row["row"]: row for start in anchor_rows for row in db.by_cr[(start["spec"], start["cr"])]}
        trace.update({"document": document, "anchorRows": [trace_row(row) for row in anchor_rows],
                      "sameCrRows": [trace_row(row) for row in sorted(cr_rows.values(), key=lambda r: r["row"])],
                      "laterRows": [trace_row(row) for row in later_rows.values()]})
        return [list(row) for row in sorted(answer_rows)], trace
    raise SystemExit(f"unknown family {family} in {item['id']}")


def run_answer(args: argparse.Namespace) -> None:
    items = load_inputs(args.items)
    rows, provenance = read_query1(args.crdb_zip)
    provenance.update({"sourceUrl": args.source_url, "listingEntry": args.listing_entry,
                       "httpLastModified": args.last_modified, "retrieved": args.retrieved,
                       "snapshotDateInFileName": (re.search(r"(\d{8})", args.crdb_zip.name) or [None, None])[1]})
    db = CRDB(rows)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    by_wg = collections.defaultdict(list)
    traces, counts = [], collections.defaultdict(collections.Counter)
    for item in items:
        answer_rows, trace = answer(item, db)
        trace["answerRows"] = answer_rows
        traces.append(trace)
        counts[item["family"]]["items"] += 1
        counts[item["family"]]["nonEmptyAnswers"] += bool(answer_rows)
        by_wg[item["wg"]].append({"id": item["id"], "wg": item["wg"], "family": item["family"], "method": METHOD,
                                  "model": MODEL,
                                  "questionSha256": hashlib.sha256(item["question"].encode()).hexdigest(),
                                  "rows": answer_rows})
    responses = {}
    for wg, records in sorted(by_wg.items()):
        path = args.out_dir / f"{wg}_{METHOD}.jsonl"
        path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records))
        responses[wg] = {"path": str(path), "items": len(records)}
    (args.out_dir / "crdb_lookup_trace.jsonl").write_text(
        "".join(json.dumps(trace, ensure_ascii=False) + "\n" for trace in traces))
    run = {"method": METHOD, "model": MODEL, "items": len(items), "itemFiles": [str(path) for path in args.items],
           "snapshot": provenance, "rules": RULES, "responses": responses,
           "answerCounts": {family: dict(counter) for family, counter in sorted(counts.items())}}
    (args.out_dir / "crdb_lookup_run.json").write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"items": len(items), "snapshot": {k: provenance[k] for k in ("zipFile", "zipSha256", "dataRows")},
                      "answerCounts": run["answerCounts"]}, ensure_ascii=False))


MISS_CLASSES = {
    "cr_row_absent": "the anchor WG Tdoc or CR pack has no CRDB row",
    "revision_chain_unnumbered_predecessor": "revision_chain anchor has no CRDB row while every expected later "
                                             "document is in the CRDB as the first revision ('-') of its CR: the "
                                             "revision step precedes the CR number, the pattern of an unnumbered "
                                             "draftCR",
    "revision_chain_crosses_cr": "an expected later document is in the CRDB under a different (Spec number, "
                                 "CR number) than the anchor",
    "snapshot_timing": "an expected CR pack or TSG meeting appears nowhere in the snapshot, or a CRDB-only pack "
                       "or document belongs to a plenary or WG meeting later than the latest one of that body in "
                       "any expected row (the latest expected meeting stands in for the benchmark's data cutoff)",
    "pack_differs": "after aligning meeting labels the set of CR packs differs (CRDB lists an extra pack, "
                    "lacks an expected pack, or gives another one)",
    "pack_membership_differs": "pack_origin: after aligning meeting labels the set of documents carried by the "
                               "pack differs",
    "status_differs": "after aligning meeting labels and on the shared packs or documents, only the "
                      "disposition differs: CRDB WG-level status is not the WG resolution disposition expected",
    "meeting_label_differs": "the answer equals the expected rows once a trailing '-e' is removed from meeting "
                             "labels on both sides, and nothing else differs",
    "other": "none of the above explains the difference",
}
CLASS_ORDER = ("cr_row_absent", "revision_chain_unnumbered_predecessor", "revision_chain_crosses_cr",
               "meeting_label_differs", "snapshot_timing", "pack_differs", "pack_membership_differs",
               "status_differs", "other")
ENTITY_COLUMN = {"pack_lookup": "cr_pack", "pack_lookup_empty": "cr_pack", "disposition_pack": "cr_pack",
                 "revision_chain": "cr_pack", "pack_origin": "document"}


def load_scorer():
    spec = importlib.util.spec_from_file_location("score_chain_eval", SCORER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def drop_e(cell: str) -> str:
    return cell[:-2] if "#" in cell and cell.endswith("-e") else cell


def plenary_number(label: str) -> int | None:
    match = re.fullmatch(r"ran#(\d+)(?:-e)?", label)
    return int(match.group(1)) if match else None


def compact(row: dict) -> list[str]:
    return [row[name] for name in ("spec", "cr", "revision", "wgTdoc", "wgStatus", "wgMeeting", "tsgTdoc", "tsgMeeting")]


def classify(item: dict, trace: dict, db: CRDB, scorer, snapshot: dict) -> dict:
    """사후 분석: 한 오답의 원인 갈래를 고정 순서(`CLASS_ORDER`)로 하나 고르고, 함께 보인 다른 원인을 적는다."""
    family, fields = item["family"], item["fields"]
    key = scorer.key
    given = {key(row) for row in trace["answerRows"]}
    wanted = {key(row) for row in item["gold"]}
    aligned_given = {tuple(map(drop_e, row)) for row in given}
    aligned_wanted = {tuple(map(drop_e, row)) for row in wanted}
    flags, detail = [], {}
    label_pairs = collections.Counter()
    for a in given - wanted:
        for g in wanted - given:
            if tuple(map(drop_e, a)) == tuple(map(drop_e, g)):
                for name, x, y in zip(fields, a, g):
                    if x != y:
                        label_pairs[f"{name}: crdb '{x}' / expected '{y}'"] += 1
    if label_pairs:
        flags.append("meeting_label_differs")
        detail["meetingLabelPairs"] = sorted(label_pairs)
    anchor_rows = trace.get("crdbRows", trace.get("anchorRows", trace.get("packRows")))
    if not anchor_rows:
        if family == "revision_chain":
            column = fields.index("final_document")
            expected_docs = sorted({row[column] for row in item["gold"]})
            found = {doc: [compact(row["raw"]) for row in db.by_document.get(norm_doc(doc), [])] for doc in expected_docs}
            detail["expectedDocumentRowsInCrdb"] = found
            if found and all(rows and all(row[2] in ("-", "0") for row in rows) for rows in found.values()):
                flags.insert(0, "revision_chain_unnumbered_predecessor")
            else:
                flags.insert(0, "cr_row_absent")
        else:
            flags.insert(0, "cr_row_absent")
        return {"flags": flags, "class": flags[0], **detail}
    if family == "revision_chain":
        anchor_crs = {(row["spec"].strip(), norm_cr(row["cr"])) for row in anchor_rows}
        column = fields.index("final_document")
        crossing = {}
        for doc in sorted({row[column] for row in item["gold"]}):
            crs = {(row["spec"], row["cr"]) for row in db.by_document.get(norm_doc(doc), [])}
            if crs and not crs & anchor_crs:
                crossing[doc] = sorted(map(list, crs))
        if crossing:
            flags.insert(0, "revision_chain_crosses_cr")
            detail["expectedDocumentCrs"] = crossing
            detail["anchorCrs"] = sorted(map(list, anchor_crs))
    entity = fields.index(ENTITY_COLUMN[family])
    status = fields.index("disposition") if "disposition" in fields else None
    entities_given = {row[entity] for row in aligned_given}
    entities_wanted = {row[entity] for row in aligned_wanted}
    if entities_given != entities_wanted:
        extra, missing = sorted(entities_given - entities_wanted), sorted(entities_wanted - entities_given)
        detail.update({"crdbOnly": extra, "expectedOnly": missing,
                       "entityDifference": "crdbExtra" if not missing else "crdbMissing" if not extra else "replaced"})
        timing = {}
        for value in missing:
            if family != "pack_origin" and value.upper() not in db.by_pack:
                timing[value] = "expected pack not in snapshot"
        if "tsg_meeting" in fields:
            column = fields.index("tsg_meeting")
            for row in wanted:
                if row[entity] in missing and drop_e(row[column]) not in snapshot["tsgMeetings"]:
                    timing[row[column]] = "expected TSG meeting not in snapshot"
            for row in given:
                number = plenary_number(row[column]) if row[entity] in extra else None
                if number is not None and number > snapshot["latestExpectedPlenary"]:
                    timing[row[entity]] = f"CRDB plenary {row[column]} later than latest expected plenary"
        if "wg_meeting" in fields:
            column = fields.index("wg_meeting")
            for row in given:
                match = re.fullmatch(r"ran\d#(\d+).*", row[column]) if row[entity] in extra else None
                if match and int(match.group(1)) > snapshot["latestExpectedWgMeeting"][item["wg"]]:
                    timing[row[entity]] = (f"CRDB WG meeting {row[column]} later than latest expected "
                                           f"{item['wg']} meeting")
        if timing:
            flags.append("snapshot_timing")
            detail["snapshotTiming"] = timing
        flags.append("pack_membership_differs" if family == "pack_origin" else "pack_differs")
        if family == "pack_origin":
            detail["crdbRowsOfDifferingDocuments"] = {
                doc: [compact(row["raw"]) for row in db.by_document.get(norm_doc(doc), [])]
                for doc in extra + missing}
    shared = entities_given & entities_wanted
    rest_given = {row for row in aligned_given if row[entity] in shared}
    rest_wanted = {row for row in aligned_wanted if row[entity] in shared}
    if rest_given != rest_wanted:
        if status is not None and ({row[:status] + row[status + 1:] for row in rest_given}
                                   == {row[:status] + row[status + 1:] for row in rest_wanted}):
            flags.append("status_differs")
            detail["statusOnlyRows"] = {"crdbOnly": sorted(map(list, rest_given - rest_wanted)),
                                        "expectedOnly": sorted(map(list, rest_wanted - rest_given))}
            detail["statusDifference"] = ("expectedAdditionalDisposition" if not rest_given - rest_wanted
                                          else "crdbAdditionalStatus" if not rest_wanted - rest_given
                                          else "differentDisposition")
        else:
            flags.append("other")
            detail["otherRows"] = {"crdbOnly": sorted(map(list, rest_given - rest_wanted)),
                                   "expectedOnly": sorted(map(list, rest_wanted - rest_given))}
    if family == "pack_origin" and rest_given != rest_wanted:
        documents = sorted({row[entity] for row in rest_given ^ rest_wanted})
        detail.setdefault("crdbRowsOfDifferingDocuments", {}).update({
            doc: [compact(row["raw"]) for row in db.by_document.get(norm_doc(doc), [])] for doc in documents})
    if aligned_given == aligned_wanted:
        primary = "meeting_label_differs"
    else:
        primary = next(name for name in CLASS_ORDER if name in flags and name != "meeting_label_differs") \
            if any(name != "meeting_label_differs" for name in flags) else "other"
    return {"flags": flags, "class": primary, **detail}


def run_summarize(args: argparse.Namespace) -> None:
    scorer = load_scorer()
    run = json.loads((args.out_dir / "crdb_lookup_run.json").read_text())
    if file_sha256(args.crdb_zip) != run["snapshot"]["zipSha256"]:
        raise SystemExit("CRDB zip differs from the one the answers were built from")
    items = [record for path in args.items for record in map(json.loads, path.read_text().splitlines())]
    traces = {trace["id"]: trace for trace in map(json.loads, (args.out_dir / "crdb_lookup_trace.jsonl").read_text().splitlines())}
    responses = {}
    for wg, entry in run["responses"].items():
        for record in map(json.loads, Path(entry["path"]).read_text().splitlines()):
            responses[record["id"]] = record
    rows, _ = read_query1(args.crdb_zip)
    db = CRDB(rows)
    snapshot = {"tsgMeetings": {drop_e(scorer.cell_key(row["tsgMeeting"])) for row in db.rows if row["tsgMeeting"]}}
    latest = [plenary_number(scorer.cell_key(cell)) for item in items for row in item["gold"]
              for name, cell in zip(item["fields"], row) if name == "tsg_meeting"]
    snapshot["latestExpectedPlenary"] = max(number for number in latest if number is not None)
    snapshot["latestExpectedWgMeeting"] = {}
    for item in items:
        for row in item["gold"]:
            for name, cell in zip(item["fields"], row):
                match = re.fullmatch(r"ran(\d)#(\d+).*", scorer.cell_key(cell)) if name == "wg_meeting" else None
                if match:
                    wg = "RAN" + match.group(1)
                    snapshot["latestExpectedWgMeeting"][wg] = max(snapshot["latestExpectedWgMeeting"].get(wg, 0),
                                                                  int(match.group(2)))
    exact = {}
    for item in items:
        record = responses[item["id"]]
        if record["questionSha256"] != hashlib.sha256(item["question"].encode()).hexdigest():
            raise SystemExit(f"stale response for {item['id']}")
        if record["rows"] != traces[item["id"]]["answerRows"]:
            raise SystemExit(f"trace and response differ for {item['id']}")
        exact[item["id"]] = scorer.score(item["gold"], record["rows"])["exact"]

    def count(selected: list[dict]) -> dict:
        return {"exact": sum(exact[item["id"]] for item in selected), "n": len(selected)}

    by_family = {family: count([item for item in items if item["family"] == family])
                 for family in EXPRESSIBLE + NOT_EXPRESSIBLE}
    by_wg = {wg: count([item for item in items if item["wg"] == wg]) for wg in sorted({item["wg"] for item in items})}
    totals = {"expressible": count([item for item in items if item["family"] in EXPRESSIBLE]),
              "answerable": count([item for item in items if not item["expectsEmpty"]]),
              "emptyGold": count([item for item in items if item["expectsEmpty"]]),
              "all": count(items)}
    scored = json.loads(args.scores.read_text())
    scorer_by_wg = {run_report["wg"]: next(group for group in run_report["groups"] if group["by"] == "all")
                    for run_report in scored}
    scorer_family = collections.Counter()
    for run_report in scored:
        for group in run_report["groups"]:
            if group["by"] == "family":
                scorer_family[group["value"]] += group["exact"]
    consistency = {"perWg": all(scorer_by_wg[wg]["exact"] == by_wg[wg]["exact"] and scorer_by_wg[wg]["n"] == by_wg[wg]["n"]
                                for wg in by_wg),
                   "perFamily": all(scorer_family[family] == by_family[family]["exact"] for family in by_family),
                   "missingOrStale": sum(run_report["missing"] + run_report["staleQuestion"] for run_report in scored)}
    if not (consistency["perWg"] and consistency["perFamily"] and consistency["missingOrStale"] == 0):
        raise SystemExit(f"recount disagrees with {args.scores}: {consistency}")
    misses = []
    for item in items:
        if item["family"] in EXPRESSIBLE and not exact[item["id"]]:
            trace = traces[item["id"]]
            result = classify(item, trace, db, scorer, snapshot)
            used = trace.get("crdbRows", trace.get("sameCrRows", []))
            misses.append({"id": item["id"], "family": item["family"], **result,
                           **({"crdbRows": [compact(row) for row in used]} if used else {}),
                           "crdbAnswer": trace["answerRows"], "expected": item["gold"]})
    classes = collections.Counter(miss["class"] for miss in misses)
    flags = collections.Counter(flag for miss in misses for flag in miss["flags"])
    by_class_family = collections.defaultdict(collections.Counter)
    for miss in misses:
        by_class_family[miss["class"]][miss["family"]] += 1
    examples = {name: [{key: value for key, value in miss.items() if key not in ("flags",)}
                       for miss in misses if miss["class"] == name][:3] for name in CLASS_ORDER}
    subtypes = {name: dict(collections.Counter(miss[field] for miss in misses if miss["class"] == name and field in miss))
                for name, field in (("pack_differs", "entityDifference"), ("pack_membership_differs", "entityDifference"),
                                    ("status_differs", "statusDifference"))}
    label_pairs = collections.Counter(pair for miss in misses for pair in miss.get("meetingLabelPairs", []))
    label_columns = collections.Counter(pair.split(":", 1)[0] for pair in label_pairs.elements())
    summary = {
        "method": METHOD, "model": MODEL,
        "snapshot": run["snapshot"], "rules": run["rules"],
        "scoring": {"scorer": str(SCORER.resolve().relative_to(REPO)), "scores": str(args.scores), "runs": 1,
                    "recountMatchesScorer": consistency},
        "exactMatch": {"byFamily": by_family, "byWg": by_wg, **totals},
        "missDecomposition": {
            "scope": "the 467 expressible items that are not an exact match; expected rows read only here, "
                     "after scoring",
            "misses": len(misses),
            "classDefinitions": MISS_CLASSES, "classOrder": list(CLASS_ORDER),
            "primaryClassCounts": {name: classes[name] for name in CLASS_ORDER},
            "primaryClassByFamily": {name: dict(by_class_family[name]) for name in CLASS_ORDER if by_class_family[name]},
            "primaryClassSubtypes": subtypes,
            "flagCounts": {name: flags[name] for name in CLASS_ORDER},
            "meetingLabelDifferencesByColumn": dict(label_columns),
            "examples": examples,
        },
        "latestExpectedMeetings": {"plenary": snapshot["latestExpectedPlenary"],
                                   "wg": snapshot["latestExpectedWgMeeting"]},
        "misses": misses,
    }
    (args.out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"exactMatch": {key: summary["exactMatch"][key] for key in ("expressible", "answerable", "emptyGold", "all")},
                      "byFamily": by_family, "primaryClassCounts": summary["missDecomposition"]["primaryClassCounts"],
                      "flagCounts": summary["missDecomposition"]["flagCounts"],
                      "meetingLabelDifferencesByColumn": dict(label_columns)}, ensure_ascii=False, indent=1))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("answer", help="CRDB 행만으로 응답 파일을 만든다")
    build.add_argument("--crdb-zip", type=Path, required=True)
    build.add_argument("--source-url", required=True)
    build.add_argument("--listing-entry", default=None, help="내려받은 목록 페이지에 적힌 파일 행(기록용)")
    build.add_argument("--last-modified", default=None, help="내려받을 때 받은 Last-Modified 머리글(기록용)")
    build.add_argument("--retrieved", default=None, help="내려받을 때 받은 Date 머리글(기록용)")
    build.add_argument("--items", type=Path, nargs="+", required=True)
    build.add_argument("--out-dir", type=Path, required=True)
    report = commands.add_parser("summarize", help="채점 뒤 정확 일치 수를 세고 오답을 원인 갈래로 나눈다")
    report.add_argument("--crdb-zip", type=Path, required=True)
    report.add_argument("--items", type=Path, nargs="+", required=True)
    report.add_argument("--out-dir", type=Path, required=True)
    report.add_argument("--scores", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "answer":
        run_answer(args)
    else:
        run_summarize(args)


if __name__ == "__main__":
    main()
