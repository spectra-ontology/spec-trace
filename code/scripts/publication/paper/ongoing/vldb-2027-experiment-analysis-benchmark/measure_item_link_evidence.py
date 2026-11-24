"""문항 정답 사슬의 연결마다 원문에 적힌 근거를 다시 찾아 연결 종류별로 센다 (모델 호출 없음).

정답 행 하나는 여러 연결을 따라가 얻는다. 연결 종류마다 "원문 문서가 그 연결을 적었는가"를
인스턴스 값과 따로 원자료에서 다시 확인한다. 같은 회의에 있었다는 사실만으로 이은 연결은 직접 근거로 세지 않는다.

연결 종류와 직접 근거의 판정
- document_disposition  문서 → 처분 기록. 처분 기록이 원문 대조 통과(`source_verified`)·문서 전체 범위이고,
                        근거 파일·SHA·위치·인용 네 값이 모두 있고, 문항에 실린 파일·SHA·위치가 그 기록과 같고,
                        근거 파일의 SHA-256 이 기록과 같고, 인용문이 대상 문서 번호를 적는다.
- disposition_meeting   처분 → 작업반 회의. 처분 기록의 근거 파일이 그 회의의 보고서다
                        (보고서 파일 이름의 회의 번호 = 결정 기록 `madeAt` 의 회의 번호 = 정답의 회의.
                        회의 번호는 대소문자와 `-`·`_` 표기 차이를 무시하고 견주며, 전자회의 접미사 e 만 다른 경우는 따로 센다).
- cr_pack               CR → 총회 CR 묶음. 묶음 표지의 CR 행, 작업반 TDoc 목록의 `TSG CR Pack` 칸,
                        TSG 회의 TDoc 목록 CR 시트의 (묶음, 작업반 문서) 행 가운데 하나 이상이 그 쌍을 적는다.
                        CR 파일이 묶음 디렉터리에 놓여 있다는 사실만 있는 쌍은 따로 센다.
- pack_tsg_meeting      묶음 → TSG 회의. 묶음 표지 머리글에서 읽은 회의가 정답과 같다.
                        TSG 회의 TDoc 목록이 그 묶음을 실은 회의와의 일치는 따로 센다.
- cr_section            CR → 규격 절. CR 서식의 `Clauses affected` 칸이 그 절 번호를 적고 규격 번호가 같다.
                        절 기록의 release 가 CR 의 release(서식 또는 CR 시트)와 같은 경우와 다른 경우를 나눠 센다.
- revision              개정 연결. 작업반 TDoc 목록에서 후속 문서 행의 `Is revision of` 칸이 앞 문서를 적거나
                        앞 문서 행의 `Revised to` 칸이 후속 문서를 적거나, 앞 문서의 원문 대조 통과 `revised`
                        처분 기록의 인용문(회의 보고서)이 후속 문서 번호를 적는다.
- no_pack               빈 정답 문항. 위 묶음 출처 넷(표지·작업반 목록·CR 시트·디렉터리) 어디에도 그 CR 이 없다.

사용 (저장소 루트에서 실행):
  python3 measure_item_link_evidence.py --items <chain_items_admitted.jsonl> [--phase2-root <dir>] --out <json>
"""
from __future__ import annotations

import argparse
import collections
import functools
import hashlib
import html
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "scripts/tsg/RAN/formal/common")
import cr_clause  # noqa: E402
import tsg_cr_decision  # noqa: E402
from build_chain_items import INSTANCES, SECTION, as_list, local, meeting_label  # noqa: E402

MEETINGS = Path("ontology/input/tsg/RAN/formal/meetings")
PARSED_CR = Path("ontology/output/tsg/RAN/formal/parsed_cr")
CR_CORPUS = Path("data/corpus/tsg/RAN/formal/change-requests")
EVIDENCE_KEYS = ("evidencePath", "evidenceSha256", "evidenceLocator", "evidenceQuote")
LIST_COLUMNS = ("Is revision of", "Revised to", "TSG CR Pack")
# 작업반 TDoc 목록의 머리글 표기(소문자, 끝의 # 제거) → 칸의 뜻. 목록 서식이 둘이라 표기도 둘씩이다.
LIST_HEADERS = {"is revision of": "Is revision of", "replaces": "Is revision of",
                "revised to": "Revised to", "replaced-by": "Revised to",
                "tsg cr pack": "TSG CR Pack", "crpack": "TSG CR Pack", "cr pack tdoc": "TSG CR Pack"}
REPORT_NAME = re.compile(r"^Final_Report_(RAN\d)-(.+)\.docx$")
TSG_MEETING = re.compile(r"RAN#(\d+)")


def header_name(cell) -> str:
    return str(cell if cell is not None else "").strip().rstrip("#").strip().lower()


def squash(text) -> str:
    return re.sub(r"\s+", "", str(text or ""))


def numbers(cell) -> list[str]:
    """칸에 적힌 문서 번호들. 표기는 `tsg_cr_decision` 의 정규형을 따른다."""
    return [f"{m.group(1)}-{m.group(2)}" if m.group(1) else f"{m.group(3)}s{m.group(4)}"
            for m in tsg_cr_decision._TDOC.finditer(str(cell or "").upper())]


def number(value) -> str:
    return tsg_cr_decision._norm(value) or squash(value)


def names(doc_number: str, text: str) -> bool:
    """text 가 문서 번호를 적는가. 번호 안의 공백은 무시하고, 더 긴 번호의 앞부분인 경우는 세지 않는다."""
    pattern = r"\s*".join(re.escape(ch) for ch in squash(doc_number)) + r"(?!\d)"
    return re.search(pattern, text, re.IGNORECASE) is not None


@functools.lru_cache(maxsize=None)
def file_sha256(path: str) -> str | None:
    target = Path(path)
    if not target.is_file():
        return None
    digest = hashlib.sha256()
    with target.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def docx_plain(path: str) -> str:
    """docx 본문의 글자열. 변경 추적의 삭제분과 필드 명령문은 빼고 문단·칸 끝은 줄바꿈으로 둔다."""
    xml = zipfile.ZipFile(path).read("word/document.xml").decode("utf8")
    xml = re.sub(r"<w:del\b[^>]*>.*?</w:del>", "", xml, flags=re.S)
    xml = re.sub(r"<w:instrText\b[^>]*>.*?</w:instrText>", "", xml, flags=re.S)
    xml = re.sub(r"</w:(p|tc)>", "\n", xml)
    return html.unescape(re.sub(r"<[^>]+>", "", xml))


@functools.lru_cache(maxsize=8)
def docx_squashed(path: str) -> str:
    return squash(docx_plain(path))


def quote_located(path: str, quote: str, doc_number: str) -> bool | None:
    """인용문에서 대상 문서 번호를 적은 조각이 근거 파일 본문에 그대로 있는가. docx 가 아니면 None."""
    if not path.endswith(".docx") or not Path(path).is_file():
        return None
    pieces = [piece for piece in re.split(r"[\n|]", quote) if names(doc_number, piece)]
    body = docx_squashed(path)
    return bool(pieces) and all(squash(piece) in body for piece in pieces)


def meeting_fold(token: str) -> str:
    """회의 번호에서 대소문자·구분 기호 표기와 전자회의 접미사(e)를 걷어 낸 형태."""
    return re.sub(r"e$", "", meeting_plain(token))


def meeting_plain(token: str) -> str:
    """회의 번호에서 대소문자와 구분 기호(-, _) 표기만 걷어 낸 형태. 127-bis 와 127bis 가 같아진다."""
    return re.sub(r"[-_]", "", token.lower())


class WgMeetings:
    """작업반 회의 식별자와, 보고서 파일 이름이 그 회의를 가리키는지의 판정."""

    def __init__(self, wg: str):
        records = json.loads((INSTANCES / f"phase-1/{wg}/meetings.jsonld").read_text())["@graph"]
        tokens = [local(r["@id"]).split("_", 1)[1] for r in records
                  if r.get("@type") == "tdoc:Meeting" and local(r["@id"]).startswith(f"{wg}_")]
        folded = collections.Counter(meeting_fold(t) for t in tokens)
        self.wg = wg
        # 전자회의 접미사(-e)를 떼면 서로 같아지는 회의 식별자. 이 회의는 접미사 없는 대조를 쓰지 않는다.
        self.fold_collisions = sorted(t for t in tokens if folded[meeting_fold(t)] > 1)
        plain = collections.Counter(meeting_plain(t) for t in tokens)
        # 구분 기호만 다른 회의 식별자가 둘 이상이면 그 회의는 표기까지 같은 경우만 같은 회의로 본다.
        self.plain_collisions = sorted(t for t in tokens if plain[meeting_plain(t)] > 1)

    def report_matches(self, evidence_path: str, made_at: str | None) -> str:
        match = REPORT_NAME.match(Path(evidence_path).name)
        if not match or not made_at:
            return "not_a_meeting_report"
        report, target = match.group(2), local(made_at).split("_", 1)[-1]
        if match.group(1) != self.wg or not local(made_at).startswith(f"{self.wg}_"):
            return "different_meeting"
        if report.lower() == target.lower() or (
                meeting_plain(report) == meeting_plain(target) and target not in self.plain_collisions):
            return "same_meeting_number"
        if meeting_fold(report) == meeting_fold(target) and target not in self.fold_collisions:
            return "same_meeting_number_without_e_suffix"
        return "different_meeting"


class ListCells:
    """작업반 TDoc 목록의 개정·묶음 칸. 값마다 (파일, 시트, 행)을 남긴다."""

    def __init__(self, wg: str):
        import openpyxl

        self.cells = {column: collections.defaultdict(dict) for column in LIST_COLUMNS}
        self.files, self.unreadable = 0, []
        for path in sorted((MEETINGS / wg / "TDoc_List").iterdir()):
            if path.suffix.lower() not in (".xlsx", ".xlsm") or path.name.startswith("~$"):
                continue
            try:
                workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
            except Exception as error:
                self.unreadable.append(f"{path.name}: {type(error).__name__}")
                continue
            self.files += 1
            try:
                for sheet in workbook.sheetnames:
                    rows = workbook[sheet].iter_rows(values_only=True)
                    header = [header_name(c) for c in next(rows, ())]
                    wanted = {LIST_HEADERS[h]: i for i, h in enumerate(header) if h in LIST_HEADERS}
                    # 문서 목록 시트는 행의 문서가 `TDoc` 칸에, CR 묶음 시트는 `WG Tdoc` 칸에 있다.
                    key = next((i for i, h in enumerate(header) if h == ("wg tdoc" if "cr pack tdoc" in header else "tdoc")), None)
                    if key is None or not wanted:
                        continue
                    for line, row in enumerate(rows, start=2):
                        if key >= len(row) or row[key] is None:
                            continue
                        doc = number(row[key])
                        for column, index in wanted.items():
                            if index < len(row) and row[index] is not None:
                                for value in numbers(row[index]):
                                    self.cells[column][doc].setdefault(value, f"{path.name}#{sheet}!row{line}")
            finally:
                workbook.close()

    def revision(self, later: str, earlier: str) -> dict[str, str]:
        """개정 연결을 적은 칸 → 위치."""
        found = {}
        if earlier in self.cells["Is revision of"].get(later, {}):
            found["Is revision of"] = self.cells["Is revision of"][later][earlier]
        if later in self.cells["Revised to"].get(earlier, {}):
            found["Revised to"] = self.cells["Revised to"][earlier][later]
        return found

    def packs(self, doc: str) -> dict[str, str]:
        return self.cells["TSG CR Pack"].get(doc, {})


class PackSources:
    """CR 의 묶음 소속과 묶음의 TSG 회의를 적는 출처들."""

    def __init__(self, wg: str, lists: ListCells):
        data = json.loads((PARSED_CR / wg / "cr_documents.json").read_text())
        self.forms: dict[str, list[dict]] = collections.defaultdict(list)
        self.directory: set[tuple[str, str]] = set()
        for form in data.get("cr_documents") or data.get("documents"):
            doc = number(form["tdoc_number"])
            self.forms[doc].append(form)
            self.directory.add((doc, form["cr_pack_id"]))
        self.cover_rows: set[tuple[str, str]] = set()
        self.cover_meeting: dict[str, str] = {}
        self.cover_unread: list[str] = []
        covers = PARSED_CR / wg / "cover_sheets.json"
        if covers.exists():
            self.cover_source = f"{covers} (구축 공정이 표지에서 읽어 둔 행)"
            for pack in json.loads(covers.read_text())["crpacks"]:
                self.cover_meeting[pack["cr_pack_id"]] = pack["tsg_meeting"]
                for entry in pack["cr_entries"]:
                    self.cover_rows.add((number(entry["tdoc_number"]), pack["cr_pack_id"]))
        else:
            # 표지 행을 저장해 둔 파일이 없는 작업반은 표지 docx 본문에서 문서 번호를 직접 읽는다.
            self.cover_source = f"{CR_CORPUS / wg}/derived/Rel-*/TSG/<pack>/<pack>_cover.docx (이 스크립트가 본문에서 번호를 직접 읽음)"
            for pack in json.loads((PARSED_CR / wg / "crpacks.json").read_text())["packs"]:
                self.cover_meeting[pack["crPackId"]] = pack["tsgMeeting"]
                files = sorted((CR_CORPUS / wg / "derived").glob(f"Rel-*/TSG/{pack['crPackId']}/{pack['crPackId']}_cover.docx"))
                if not files:
                    self.cover_unread.append(pack["crPackId"])
                for cover in files:
                    try:
                        text = docx_plain(str(cover))
                    except Exception:
                        self.cover_unread.append(pack["crPackId"])
                        continue
                    self.cover_rows.update((doc, pack["crPackId"]) for doc in numbers(re.sub(r"-\s+(?=\d)", "-", text)))
        self.sheet_pairs, _, self.plenary, self.sheet_identity = tsg_cr_decision._lists()
        self.sheet_meetings: dict[str, set[str]] = collections.defaultdict(set)
        for (pack, _), (_, meeting) in self.sheet_pairs.items():
            self.sheet_meetings[pack].add(meeting)
        for pack, (_, _, meeting) in self.plenary.items():
            self.sheet_meetings[pack].add(meeting)
        self.lists = lists
        self.by_doc: dict[str, set[str]] = collections.defaultdict(set)
        for doc, pack in self.directory | self.cover_rows:
            self.by_doc[doc].add(pack)
        for pack, doc in self.sheet_pairs:
            self.by_doc[doc].add(pack)

    def membership(self, doc: str, pack: str) -> list[str]:
        """그 (CR, 묶음) 쌍을 적은 출처 이름들."""
        found = []
        if (doc, pack) in self.cover_rows:
            found.append("pack_cover_row")
        if pack in self.lists.packs(doc):
            found.append("wg_tdoc_list_cell")
        if (pack, doc) in self.sheet_pairs:
            found.append("tsg_cr_sheet_row")
        if (doc, pack) in self.directory:
            found.append("pack_directory_file")
        return found

    def any_pack(self, doc: str) -> list[str]:
        """그 CR 을 어떤 묶음에든 실은 출처 이름들."""
        found = []
        if any(d == doc for d, _ in self.cover_rows):
            found.append("pack_cover_row")
        if self.lists.packs(doc):
            found.append("wg_tdoc_list_cell")
        if any(d == doc for _, d in self.sheet_pairs):
            found.append("tsg_cr_sheet_row")
        if doc in self.forms:
            found.append("pack_directory_file")
        return found

    def meeting(self, pack: str, gold: str) -> tuple[bool, str]:
        """(표지 머리글의 회의가 정답과 같은가, TSG 회의 TDoc 목록과의 대조 결과)."""
        listed = {m.group(0) for meeting in self.sheet_meetings.get(pack, ()) if (m := TSG_MEETING.search(meeting))}
        other = "tsg_list_absent" if not listed else "tsg_list_same" if listed == {gold} else "tsg_list_different"
        return self.cover_meeting.get(pack) == gold, other

    def section(self, doc: str, section: str) -> str:
        match = SECTION.match(section)
        if not match:
            return "section_id_unreadable"
        outcome = "clause_not_written"
        for form in self.forms.get(doc, ()):
            written = {s for group in cr_clause.clause_candidates(form.get("clauses_affected") or "") for s in group}
            if form.get("spec_number") != match["spec"] or match["clause"] not in written:
                continue
            releases = {form.get("release")}
            identity = self.sheet_identity.get((form["cr_pack_id"], doc))
            if identity:
                releases.add(identity[3])
            if match["release"] in releases:
                return "clause_written_same_release"
            outcome = "clause_written_other_release"
        return outcome


class Dispositions:
    """처분 기록과 결정 기록의 회의."""

    def __init__(self, wg: str, phase2_root: Path | None):
        def source(name: str) -> Path:
            staged = phase2_root / wg / name if phase2_root else None
            return staged if staged and staged.exists() else INSTANCES / f"phase-2/{wg}/{name}"

        self.made_at: dict[str, str] = {}
        for path in sorted((INSTANCES / f"phase-2/{wg}").glob("resolutions_*.jsonld")):
            for record in json.loads(source(path.name).read_text())["@graph"]:
                if "madeAt" in record:
                    self.made_at[record["@id"]] = record["madeAt"]
        self.path = source("decision_dispositions.jsonld")
        self.by_id: dict[str, list[dict]] = collections.defaultdict(list)
        self.by_target: dict[str, list[dict]] = collections.defaultdict(list)
        for record in json.loads(self.path.read_text())["@graph"]:
            if "dispositionId" in record:
                self.by_id[record["dispositionId"]].append(record)
                self.by_target[record["dispositionTarget"]].append(record)


def disposition_basis(record: dict, doc: str, code: str, entry: dict) -> tuple[bool, str]:
    """(직접 근거인가, 근거 규칙 이름 또는 처음 걸린 조건)."""
    method = json.loads(record.get("assessmentMethod") or "{}")
    checks = [
        ("record_targets_other_document", number(local(record["dispositionTarget"])) == doc),
        ("record_has_other_code", record.get("dispositionCode") == code),
        ("not_source_verified", record.get("evidenceStatus") == "source_verified"),
        ("not_whole_document_scope", method.get("scope") == "whole_target"),
        ("evidence_attribute_missing", all(record.get(key) for key in EVIDENCE_KEYS)),
        ("item_evidence_differs_from_record", (entry["path"], entry["sha256"], entry["locator"]) == (
            record.get("evidencePath"), record.get("evidenceSha256"), record.get("evidenceLocator"))),
        ("evidence_file_missing", file_sha256(record.get("evidencePath") or "") is not None),
        ("evidence_file_sha_differs", file_sha256(record.get("evidencePath") or "") == record.get("evidenceSha256")),
        ("quote_lacks_document_number", names(doc, record.get("evidenceQuote") or "")),
    ]
    failed = next((name for name, passed in checks if not passed), None)
    return failed is None, failed or str(method.get("rule"))


class Measure:
    def __init__(self, wg: str, phase2_root: Path | None):
        self.wg = wg
        self.meetings = WgMeetings(wg)
        self.lists = ListCells(wg)
        self.packs = PackSources(wg, self.lists)
        self.dispositions = Dispositions(wg, phase2_root)
        self.successors: dict[str, list[str]] = collections.defaultdict(list)
        for record in json.loads((INSTANCES / f"phase-1/{wg}/tdocs.jsonld").read_text())["@graph"]:
            for earlier in as_list(record.get("isRevisionOf")):
                self.successors[number(local(earlier))].append(number(local(record["@id"])))

    def revision_path(self, start: str, goal: str) -> list[tuple[str, str]] | None:
        """start 에서 goal 까지 개정 관계를 따라간 (앞 문서, 후속 문서) 쌍들."""
        parent, queue = {start: None}, [start]
        while queue:
            current = queue.pop(0)
            if current == goal:
                steps = []
                while parent[current] is not None:
                    steps.append((parent[current], current))
                    current = parent[current]
                return steps[::-1]
            for later in self.successors.get(current, ()):
                if later not in parent:
                    parent[later] = current
                    queue.append(later)
        return None

    def disposition_links(self, item: dict, doc: str, code: str, meeting: str | None):
        """정답 행의 (문서, 처분[, 회의])에 해당하는 근거 항목마다 연결을 낸다."""
        entries = [e for e in item["evidence"] if number(e["document"]) == doc and e["disposition"] == code
                   and (meeting is None or e["wgMeeting"] == meeting)]
        if not entries:
            yield "document_disposition", (doc, code, meeting), False, "item_has_no_evidence_entry", {}
            return
        for entry in entries:
            key = (doc, code, entry["wgMeeting"])
            records = self.dispositions.by_id.get(entry["dispositionId"], [])
            if len(records) != 1:
                yield "document_disposition", key, False, f"record_count_{len(records)}", {}
                continue
            record = records[0]
            direct, basis = disposition_basis(record, doc, code, entry)
            located = quote_located(record.get("evidencePath") or "", record.get("evidenceQuote") or "", doc)
            word = code.replace("_", " ").lower() in (record.get("evidenceQuote") or "").lower()
            yield "document_disposition", key, direct, basis, {
                "quoteLocatedInFile": {None: "not_docx", True: "located", False: "not_located"}[located],
                "codeWordInQuote": "yes" if word else "no"}
            if "wg_meeting" in item["fields"]:
                made = self.dispositions.made_at.get(record["dispositionOf"])
                outcome = self.meetings.report_matches(record.get("evidencePath") or "", made)
                same = bool(made) and meeting_label(made) == entry["wgMeeting"]
                yield ("disposition_meeting", key, outcome.startswith("same_meeting_number") and same,
                       outcome if same else "decision_record_meeting_differs_from_gold", {})

    def pack_link(self, doc: str, pack: str):
        found = self.packs.membership(doc, pack)
        written = [name for name in found if name != "pack_directory_file"]
        basis = "+".join(written) if written else "pack_directory_file_only" if found else "no_source"
        return "cr_pack", (doc, pack), bool(written), basis, {"sources": "+".join(found) or "none"}

    def links(self, item: dict):
        family, gold = item["family"], [tuple(row) for row in item["gold"]]
        anchor = local(item["anchor"])
        if family == "pack_lookup_empty":
            doc = number(anchor)
            for entry in item["evidence"]:
                yield from self.disposition_links(item, doc, entry["disposition"], entry["wgMeeting"])
            found = self.packs.any_pack(doc)
            yield "no_pack", (doc,), not found, "absent_from_all_pack_sources" if not found else "+".join(found), {}
        elif family in ("pack_lookup", "disposition_pack", "full_chain"):
            doc = number(anchor)
            for row in gold:
                named = dict(zip(item["fields"], row))
                if "disposition" in named:
                    yield from self.disposition_links(item, doc, named["disposition"], named["wg_meeting"])
                yield self.pack_link(doc, named["cr_pack"])
                direct, other = self.packs.meeting(named["cr_pack"], named["tsg_meeting"])
                yield ("pack_tsg_meeting", (named["cr_pack"], named["tsg_meeting"]), direct,
                       "pack_cover_header" if direct else "cover_header_differs_or_absent", {"tsgList": other})
                if "clause" in named:
                    yield self.section_link(doc, named["clause"])
        elif family == "revision_chain":
            start = number(anchor)
            for entry in item["evidence"]:
                if number(entry["document"]) == start:
                    yield from self.disposition_links(item, start, entry["disposition"], entry["wgMeeting"])
            for final, code, pack in gold:
                final = number(final)
                yield from self.disposition_links(item, final, code, None)
                yield self.pack_link(final, pack)
                path = self.revision_path(start, final)
                if path is None:
                    yield "revision", (start, final), False, "no_revision_path_in_instance", {}
                    continue
                for earlier, later in path:
                    cells = self.lists.revision(later, earlier)
                    quoted = any(names(later, r.get("evidenceQuote") or "")
                                 for r in self.dispositions.by_target.get(f"tdoc:{earlier}", ())
                                 if r.get("evidenceStatus") == "source_verified" and r.get("dispositionCode") == "revised")
                    basis = [f"list_cell[{name}]" for name in sorted(cells)] + ["report_revised_to_quote"] * quoted
                    yield "revision", (earlier, later), bool(basis), "+".join(basis) or "no_written_source", {}
        elif family == "clause_history":
            for doc, code, meeting, pack in gold:
                doc = number(doc)
                basis = self.packs.section(doc, item["anchor"])
                yield "cr_section", (doc, anchor), basis == "clause_written_same_release", basis, {}
                yield from self.disposition_links(item, doc, code, meeting)
                yield self.pack_link(doc, pack)
        elif family == "pack_origin":
            for doc, code, meeting in gold:
                doc = number(doc)
                yield self.pack_link(doc, anchor)
                yield from self.disposition_links(item, doc, code, meeting)
        else:
            raise ValueError(family)

    def section_link(self, doc: str, clause: str):
        """full_chain 의 절: 정답은 절 번호만 적으므로, 그 번호가 CR 서식에 적혔는지와 release 일치를 본다."""
        outcome = "clause_not_written"
        for form in self.packs.forms.get(doc, ()):
            basis = self.packs.section(doc, f"tdoc:section/{form.get('spec_number')}-{form.get('release')}-{clause}")
            if basis == "clause_written_same_release":
                outcome = "clause_written"
        return "cr_section", (doc, clause), outcome == "clause_written", outcome, {}


def summarize(rows: list[dict]) -> dict:
    """rows: 문항별 연결 기록. 연결 종류마다 서로 다른 연결 수와 문항 수를 센다."""
    out = {}
    for kind in sorted({r["kind"] for r in rows}):
        of_kind = [r for r in rows if r["kind"] == kind]
        distinct = {(r["wg"], r["key"]): r for r in of_kind}
        items = collections.defaultdict(list)
        for r in of_kind:
            items[r["item"]].append(r["direct"])
        extras = collections.defaultdict(collections.Counter)
        for r in distinct.values():
            for name, value in r["extra"].items():
                extras[name][value] += 1
        out[kind] = {
            "links": len(distinct),
            "linksDirect": sum(r["direct"] for r in distinct.values()),
            "linksByBasis": dict(collections.Counter(r["basis"] for r in distinct.values()).most_common()),
            "items": len(items),
            "itemsAllDirect": sum(all(flags) for flags in items.values()),
            "itemsWithNonDirect": sum(not all(flags) for flags in items.values()),
            **{name: dict(counter.most_common()) for name, counter in sorted(extras.items())},
        }
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, required=True)
    parser.add_argument("--phase2-root", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    items = [json.loads(line) for line in args.items.read_text().splitlines() if line.strip()]
    rows, sources = [], {}
    for wg in sorted({item["wg"] for item in items}):
        measure = Measure(wg, args.phase2_root)
        sources[wg] = {
            "dispositionRecords": str(measure.dispositions.path),
            "wgTdocListFiles": measure.lists.files,
            "wgTdocListUnreadable": measure.lists.unreadable,
            "packCoverRows": measure.packs.cover_source,
            "packCoversUnread": measure.packs.cover_unread,
            "meetingIdsCollidingWithoutESuffix": measure.meetings.fold_collisions,
        }
        for item in items:
            if item["wg"] != wg:
                continue
            for kind, key, direct, basis, extra in measure.links(item):
                rows.append({"item": item["id"], "wg": wg, "family": item["family"], "kind": kind,
                             "key": "|".join(str(part) for part in key), "direct": direct, "basis": basis,
                             "extra": extra})
        docx_squashed.cache_clear()
        print(wg, json.dumps({k: (v["linksDirect"], v["links"]) for k, v in
                              summarize([r for r in rows if r["wg"] == wg]).items()}))
    by_item = collections.defaultdict(list)
    for row in rows:
        by_item[row["item"]].append(row)
    non_direct = list({(row["item"], row["kind"], row["key"]): {k: row[k] for k in ("item", "family", "kind", "key", "basis")}
                       for row in rows if not row["direct"]}.values())
    report = {
        "items": str(args.items),
        "itemCount": len(items),
        "itemsWithLinks": len(by_item),
        "itemsAllLinksDirect": sum(all(r["direct"] for r in group) for group in by_item.values()),
        "itemsWithNonDirectLink": sum(not all(r["direct"] for r in group) for group in by_item.values()),
        "byLinkKind": summarize(rows),
        "byWg": {wg: summarize([r for r in rows if r["wg"] == wg]) for wg in sorted(sources)},
        "byFamily": {family: {kind: {"links": v["links"], "linksDirect": v["linksDirect"], "items": v["items"],
                                     "itemsWithNonDirect": v["itemsWithNonDirect"]}
                              for kind, v in summarize([r for r in rows if r["family"] == family]).items()}
                     for family in sorted({r["family"] for r in rows})},
        "nonDirectLinks": non_direct,
        "sources": sources,
    }
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("itemCount", "itemsWithLinks", "itemsAllLinksDirect", "itemsWithNonDirectLink")}))
    for kind, value in report["byLinkKind"].items():
        print(kind, value["linksDirect"], "/", value["links"], value["linksByBasis"])


if __name__ == "__main__":
    main()
