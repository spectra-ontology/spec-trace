#!/usr/bin/env python3
"""
RAN3 Phase-4 Step 1-2: CR 문서 파싱
- 입력: data/corpus/tsg/RAN/formal/change-requests/RAN3/derived/Rel-*/TSG/{팩}/ — `cr_inputs` 가 모은다(표지 제외)
- 출력: ontology/output/tsg/RAN/formal/parsed_cr/RAN3/cr_documents.json

Spec §2 CR 클래스 확장, §4 CR 문서 파싱 규칙 (RAN3 고유)
RAN3 고유: CR Form Table 기반 파싱 (RAN1과 동일 구조 확인됨)
"""

import json
import re
import sys
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path

from docx import Document

# === 경로 설정 ===
PROJECT_ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "common"))
from common.atomic_io import write_text_atomic  # noqa: E402
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "tsg" / "RAN" / "formal" / "common"))
import docx_text  # noqa: E402 — 문단 · 표 칸 읽기 규칙(변경 표시 · 필드 안의 글까지)
import pool_run  # noqa: E402 — 병렬 파싱과 항목별 실패 보고
import cr_form  # noqa: E402 — CR 서식이 적은 spec · CR 번호 · 제목
import cr_word_title  # noqa: E402 — LibreOffice 변환본의 표지 제목을 원본 .doc 글로 읽는다
import cr_form_slot  # noqa: E402 — CR 서식의 필드 이름이 손상된 경우에도 고정 셀 위치로 본문 필드를 읽는다
import cr_inputs  # noqa: E402 — Phase-0 CR 산출 슬롯에서 입력 모으기
import tsg_cr_decision  # noqa: E402 — TSG 회의가 팩 안 CR 마다 내린 판정
import cr_attachments  # noqa: E402 — CR 폴더의 첨부 문서를 CR 본문과 구분한다
import cr_other_wg  # noqa: E402 — 다른 WG 슬롯에 놓인 이 WG 의 CR · 이 슬롯에 놓인 다른 WG 의 CR
import cr_unopenable  # noqa: E402 — 기존에 확인한 열기 실패와 새 오류를 구분한다
WG = "RAN3"
INPUT_DIR = cr_inputs.derived_dir(WG)
OUTPUT_DIR = PROJECT_ROOT / "ontology" / "output" / "tsg" / "RAN" / "formal" / "parsed_cr" / "RAN3"
LOG_DIR = PROJECT_ROOT / "logs" / "tsg" / "RAN" / "formal" / "RAN3" / "phase-4"


def configure_logging() -> None:
    """main() 실행 시 로그 디렉토리와 파일 핸들러를 준비한다. 모듈 import만으로 기존 로그를 열거나 비우지 않는다."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_DIR / "02_parse_cr_documents.log", mode="w"),
        ],
    )


log = logging.getLogger(__name__)


# === 데이터 모델 ===
@dataclass
class CRDocumentData:
    tdoc_number: str
    cr_pack_id: str
    release: str
    spec_number: str | None = None
    reason_for_change: str | None = None
    summary_of_change: str | None = None
    consequences_if_not_approved: str | None = None
    clauses_affected: str | None = None
    affects_core_spec: list = field(default_factory=list)
    affects_test_spec: list = field(default_factory=list)
    affects_om_spec: list = field(default_factory=list)
    # 별도 팩 표지가 없는 CR도 자체 CR 서식에서 문서 번호와 제목을 추출한다(cr_form.form_fields).
    cr_number: str | None = None
    rev: str | None = None
    title: str | None = None
    category: str | None = None
    work_item: str | None = None
    source: str | None = None
    source_path: str = ""
    errors: list = field(default_factory=list)
    tsg_number: str | None = None
    tsg_revision_of: str | None = None


# === tdocNumber 추출 ===

# 현재 CR의 제출 번호는 파일명 또는 표지 헤더에서 읽는다. CR 서식 본문의 참조 번호를
# 현재 번호로 사용하지 않도록 서식 표 셀은 이 판별에 사용하지 않는다.
# 번호 뒤에 숫자가 더 이어지는 토큰은 정규식에서 제외한다.
_TDOC_RE = re.compile(r"(R3[-_]\d{6})(?!\d)")
_RP_RE = re.compile(r"(?<![0-9A-Za-z])RP[-_](\d{6})(?!\d)")
_CHANGE_MARK = re.compile(
    r"Reason for change|Summary of change|CHANGE REQUEST|Proposed change", re.I)

# 표지 줄에서 옛 판을 가리키는 말. RP 이름 문서 203 건의 표지 전수에서 나온 꼴이다.
_EARLIER_VERSION = re.compile(r"revision\s+of|based\s+on|\bwas\b", re.I)
#: 파일 이름에서 옛 판을 가리키는 말. 이 말 바로 뒤에 오는 번호는 이 문서의 번호가 아니다.
_FILENAME_EARLIER = re.compile(r"\b(?:rev(?:ision)?|revised|replaces?|based|was)\b[\s_.-]*(?:of|on)?[\s_.-]*$", re.I)


def _own_tdoc(text: str) -> re.Match | None:
    """줄 안의 첫 WG 번호. 「revision of」 · 「based on」 · 「was」 뒤 번호는 이 문서가 고친 옛 판의 번호라 건너뛴다."""
    for m in _TDOC_RE.finditer(text):
        if not _EARLIER_VERSION.search(text[:m.start()]):
            return m
    return None


def _revised_tdoc(cover: list[str]) -> str | None:
    """표지 줄에서 옛 판을 가리키는 말 뒤 첫 WG 번호."""
    for text in cover:
        r = _EARLIER_VERSION.search(text)
        m = _TDOC_RE.search(text, r.end()) if r else None
        if m:
            return _norm_tdoc(m.group(1))
    return None


def _norm_tdoc(tok: str) -> str:
    """파일명에서 읽은 WG 문서 번호의 공백을 제거하고 언더스코어를 대시로 정규화한다."""
    return tok.replace(" ", "").replace("_", "-")


#: 파일명이 RP 번호로 시작하면 TSG 직접 제출 문서로 구분한다.
_RP_FILENAME = re.compile(r"^RP[-_]\d{6}(?!\d)")


def extract_tdoc_from_filename(filename: str) -> str | None:
    """파일명에서 현재 CR의 WG 제출 번호를 읽는다.

    RP 번호로 시작하는 파일은 TSG 직접 제출 문서이므로 파일명 안의 WG 번호를 현재 문서 번호로
    사용하지 않는다. 이전 판본을 뜻하는 표현 바로 뒤의 번호도 제외한다. 해당하는 번호가 없으면
    문서 표지에서 현재 번호를 찾으며, RP 파일명 안의 이전 WG 번호는 filename_revised_tdoc이 기록한다."""
    if _RP_FILENAME.match(filename):
        return None
    for m in _TDOC_RE.finditer(filename):
        if not _FILENAME_EARLIER.search(filename[:m.start()]):
            return _norm_tdoc(m.group(1))
    return None


def filename_revised_tdoc(filename: str) -> str | None:
    """RP 번호로 시작하는 파일명 속 첫 WG 번호. 이 TSG 직접 CR 이 대신한 옛 WG 판이다."""
    if not _RP_FILENAME.match(filename):
        return None
    m = _TDOC_RE.search(filename)
    return _norm_tdoc(m.group(1)) if m else None


def extract_tdoc_from_document(doc: Document, has_cr_form: bool = False, filename: str = "") -> str | None:
    """커버 헤더 문단에서만 TD# 추출 (테이블 미사용 — 참조 오염 차단).
    1순위: '3GPP TSG' 앵커 줄의 WG 번호(이 문서 자신의 번호).
    아래는 CR Form Table 보유 문서 한정.
    2순위: 변경마커 이전 첫 WG 토큰.
    두 순위 모두 옛 판을 가리키는 말(「revision of」 등) 뒤 번호는 받지 않는다.
    RP 번호는 CR 의 번호가 아니다(`tsg_submission_number`).
    비-CR discussion paper는 커버 윈도 산문에 타 문서 인용이 흔해
    2순위가 인용 토큰을 자기 번호로 오인하므로 차단."""
    cover = [docx_text.final_text(p) for p in doc.paragraphs[:8]]
    for text in cover:
        if "3GPP" in text and "TSG" in text:
            m = _own_tdoc(text)
            if m:
                return _norm_tdoc(m.group(1))
    if not has_cr_form:
        return None
    for text in cover:
        if _CHANGE_MARK.search(text):
            break
        m = _own_tdoc(text)
        if m:
            return _norm_tdoc(m.group(1))
    return None


def tsg_submission_number(doc: Document, filename: str) -> str | None:
    """WG 번호 없이 TSG 에 바로 낸 CR 서식 문서의 RP 번호(앵커 줄, 없으면 파일명).

    Spec Step 7 §3 · §6.1 은 CR 을 WG 번호(Phase-1 기존 인스턴스)로만 식별하므로 이 번호는 CR 의
    신원이 아니다. 기록에서 빠진 문서를 조용히 잃지 않도록 산출 메타데이터 `tsg_direct_cr` 에만 남긴다.
    이 문서가 고친 WG 판 번호는 `_revised_tdoc` 가 따로 준다."""
    for text in (docx_text.final_text(p) for p in doc.paragraphs[:8]):
        if "3GPP" in text and "TSG" in text:
            m = _RP_RE.search(text)
            if m:
                return f"RP-{m.group(1)}"
    m = _RP_RE.search(filename)
    return f"RP-{m.group(1)}" if m else None


# === Release 추출 ===
# 동일 CR pack이 여러 Rel-N 디렉토리에 복제되므로 디렉토리명은 CR의 target
# release가 아니다(첫 디렉토리로 오귀속됨). 위계: 파일명 `(Rel-N)` 토큰 →
# CR Form `Release:` 필드 → 디렉토리명(최후 fallback).

# 표기 변형(코퍼스 파일명 전수 실측): Rel-17 / Rel17 / REL-15 / REL_17 /
# rel 18 / Release 17. `RRCRelease`·`relay` 등은 영숫자 lookbehind+숫자
# 후행 요구로 배제. 추출값은 `Rel-{N}`으로 정규화.
_REL_TOKEN_RE = re.compile(
    r"(?<![0-9A-Za-z])rel(?:ease)?[ _-]?(\d{1,2})(?!\d)", re.IGNORECASE)


def extract_release_from_filename(filename: str) -> str | None:
    m = _REL_TOKEN_RE.search(filename)
    return f"Rel-{m.group(1)}" if m else None


def extract_release_from_cr_form(table) -> str | None:
    """CR Form의 `Release:` 라벨 행에서 release 값 셀 추출 (셀 전체일치만)."""
    rows = [r for t in cr_form.form_block(table) for r in t.rows]  # 서식이 표 여럿으로 쪼개진 문서
    for row in rows:
        cells = [docx_text.cell_text(c) for c in row.cells]
        for i, t in enumerate(cells):
            if t == "Release:":
                for v in cells[i + 1:]:
                    m = _REL_TOKEN_RE.fullmatch(v)
                    if m:
                        return f"Rel-{m.group(1)}"
    return None


# === CR Form Table 파싱 ===

def find_cr_form_table(doc: Document):
    """CR 서식 필드 이름을 포함한 표를 찾는다. 중첩 표도 검사한다.

    빈 문단을 사이에 두고 나뉜 서식은 cr_form.form_block으로 묶고, 서식 필드 이름을 가진
    표들의 행 수를 합산해 10행 이상인지 검사한다. 예를 들어 8행과 6행으로 나뉜 서식도 포함한다.
    표지 제목 등 서식 필드 이름이 없는 표의 행은 합산하지 않아 작은 인용 표를 CR 서식으로
    잘못 분류하지 않도록 한다.
    """
    for table in cr_form.form_tables(doc):
        if not cr_form.is_form_table(table):
            continue
        body = [t for t in cr_form.form_block(table) if t is table or _has_form_label(t)]
        if sum(len(t.rows) for t in body) >= 10:
            return table
    return None


def _has_form_label(table) -> bool:
    """앞 두 칸에 서식 본문 이름 칸(`cr_form.FORM_LABELS`)이 있는 행을 가진 표."""
    return any(cr_form.is_label(c.strip(), label)
               for cells in docx_text.table_rows(table) for c in cells[:2] for label in cr_form.FORM_LABELS)


def extract_other_specs(table) -> tuple[list[str], list[str], list[str]]:
    """'Other specs affected' 섹션에서 Spec 번호 추출.

    반환: (core_specs, test_specs, om_specs)
    """
    rows = [r for t in cr_form.form_block(table) for r in t.rows]  # 서식이 표 여럿으로 쪼개진 문서
    core_specs = []
    test_specs = []
    om_specs = []


    for i, row in enumerate(rows):
        cells = [docx_text.cell_text(c) for c in row.cells]
        row_text = " ".join(cells).lower()

        if "other specs" not in row_text and "other core" not in row_text:
            continue

        for j in range(i, min(i + 4, len(rows))):
            row_cells = [docx_text.cell_text(c) for c in rows[j].cells]
            row_full = " ".join(row_cells).lower()

            all_text = " ".join(row_cells)
            specs_found = cr_form.text_specs(all_text, WG)

            if "core" in row_full:
                core_specs.extend(specs_found)
            elif "test" in row_full:
                test_specs.extend(specs_found)
            elif "o&m" in row_full or "o & m" in row_full:
                om_specs.extend(specs_found)
            else:
                if j == i and specs_found:
                    core_specs.extend(specs_found)

        break

    return list(dict.fromkeys(core_specs)), list(dict.fromkeys(test_specs)), list(dict.fromkeys(om_specs))


# === 단일 CR 문서 파싱 ===

def parse_cr_document(cr_path: Path, release: str, *, source_pack_id: str | None = None) -> CRDocumentData:
    """단일 CR 문서 파싱."""
    cr_pack_id = cr_other_wg.pack_id(cr_path) if source_pack_id is None else source_pack_id

    tdoc_number = extract_tdoc_from_filename(cr_path.name)
    spec_number = cr_form.filename_spec(cr_path.name)
    fname_release = extract_release_from_filename(cr_path.name)

    result = CRDocumentData(
        tdoc_number=tdoc_number or "",
        cr_pack_id=cr_pack_id,
        release=fname_release or release,
        spec_number=spec_number,
        source_path=str(cr_path.relative_to(PROJECT_ROOT)),
    )

    try:
        doc = docx_text.open_document(str(cr_path))
    except Exception as e:
        result.errors.append(f"DOCX open failed: {e}")
        if not result.tdoc_number:
            result.errors.append("tdocNumber extraction failed (no filename match, cannot open doc)")
        return result

    # CR Form Table — 필드 추출과 문서경유 키 신뢰 판별에 함께 사용
    cr_table = find_cr_form_table(doc)

    # 파일명이 spec 을 주지 못하면 서식 머리 줄에서
    if not result.spec_number:
        result.spec_number = cr_form.header_spec(doc)

    # 파일명 `(Rel-N)` 토큰이 없으면 CR Form `Release:` 필드로 보정
    if not fname_release and cr_table is not None:
        form_release = extract_release_from_cr_form(cr_table)
        if form_release:
            result.release = form_release

    # 파일명에서 R3를 못 찾은 경우 문서 내부 검색
    if not result.tdoc_number:
        result.tdoc_number = extract_tdoc_from_document(
            doc, has_cr_form=cr_table is not None, filename=cr_path.name) or ""
        if not result.tdoc_number:
            result.tdoc_number = cr_form.cover_tdoc(
                cr_form.cover_entries(OUTPUT_DIR / "cover_sheets.json").get(cr_pack_id, []),
                cr_path.name) or ""
        if not result.tdoc_number:
            if cr_table is not None:
                result.tsg_number = tsg_submission_number(doc, cr_path.name)
                result.tsg_revision_of = _revised_tdoc(
                    [docx_text.final_text(p) for p in doc.paragraphs[:8]]) or filename_revised_tdoc(cr_path.name)
            result.errors.append("tdocNumber extraction failed (filename + document)")
            return result

    if not cr_table:
        result.errors.append("CR Form Table not found")
        return result

    # 필드 추출
    for key, value in cr_form.form_fields(doc).items():
        setattr(result, key, value)
    # 주의: LibreOffice 변환본의 제목은 원본 .doc 이 보여 주는 Title 칸 글로 바로잡는다(`cr_word_title`).
    result.title = cr_word_title.form_title(result.title, cr_path)
    # 주의: 작업 항목 칸의 같은 잔재는 원본 칸에 결과가 빈 필드나 겹친 필드가 있는 경우에만 바로잡는다(`cr_word_title.form_work_item`).
    result.work_item = cr_word_title.form_work_item(result.work_item, cr_path)
    result.reason_for_change = cr_form_slot.form_value(cr_table, "reason for change")
    result.summary_of_change = cr_form_slot.form_value(cr_table, "summary of change")
    result.consequences_if_not_approved = cr_form_slot.form_value(cr_table, "consequences if not approved")

    clauses = cr_form_slot.form_value(cr_table, "clauses affected")
    if clauses:
        result.clauses_affected = clauses

    # Cross-Spec 영향
    core, test, om = extract_other_specs(cr_table)
    result.affects_core_spec = core
    result.affects_test_spec = test
    result.affects_om_spec = om

    return result


# === 파일 수집 ===

def collect_cr_documents() -> list[tuple[Path, str]]:
    """공용 입력 선택 규칙으로 CR 문서와 디렉토리 Release 목록을 모은다.

    팩 표지는 _cover.docx 접미로 제외한다. 개별 CR의 표지에는 CR 서식이 있을 수 있으므로 함께
    파싱하며, 같은 문서의 표지와 본문 중에서는 deduplicate_by_tdoc이 오류 없는 기록을 우선한다.
    Phase-8 본문 청킹은 별도 without_covers 규칙으로 이러한 표지를 제외한다.

    변환되지 않은 DOC나 열리지 않는 DOCX도 입력에 포함해 열기 오류와 파일명에서 확인한 신원을
    기록한다. 같은 번호의 읽을 수 있는 사본이 있으면 그 기록이 우선한다. WG 번호를 얻지 못한
    TSG 직접 제출 CR은 일반 CR 결과 대신 tsg_direct_cr 메타데이터에 기록한다.

    파일명 번호가 다른 WG를 가리키는 문서는 해당 WG가 처리하고 other_wg_cr로 기록한다.
    다른 WG 입력 폴더에 놓인 현재 WG 문서는 포함하되 팩과 Release는 실제 입력 경로를 따른다."""
    files, unconverted, _ = cr_other_wg.collect(WG)
    cr_docs = [(f, release) for f, release in files if not f.name.lower().endswith("_cover.docx")]
    log.info(f"  CR 문서 {len(cr_docs)}개 · 표지 제외 {len(files) - len(cr_docs)}개")
    if unconverted:
        log.warning(f"  읽을 수 없는 문서(변환본 없는 .doc · ZIP 아닌 .docx) {len(unconverted)}개 — 열기 실패 기록으로 남김(산출 메타데이터 `unconverted_doc`)")
    cr_docs += [(f, cr_other_wg.release(f)) for f in unconverted
                if not f.name.lower().endswith("_cover.docx")]
    return cr_docs


def duplicate_paths(results: list[CRDocumentData], unique_results: list[CRDocumentData]) -> dict[str, str]:
    """중복 제거에서 빠진 파일의 `source_path` → tdoc."""
    kept = {r.source_path for r in unique_results}
    return {r.source_path: r.tdoc_number
            for r in sorted(results, key=lambda r: r.source_path)
            if r.tdoc_number and r.source_path not in kept}


def cover_listed(cover_path: Path) -> set[tuple[str, str]]:
    """(팩, tdoc) 가운데 그 팩의 표지 문서가 실제로 적은 것.

    표지 문서가 없는 팩은 01 이 폴더의 파일명으로 최소 팩을 만들고 그 사실을 오류로 남긴다.
    그 목록은 폴더를 다시 적은 것일 뿐 TSG 가 그 팩에 실었다는 근거가 아니라 넣지 않는다.
    """
    if not cover_path.exists():
        return set()
    with open(cover_path, encoding="utf-8") as f:
        packs = json.load(f).get("crpacks", [])
    return {(p["cr_pack_id"], e["tdoc_number"]) for p in packs
            if not any(err.startswith("No cover sheet found") for err in p.get("errors", []))
            for e in p.get("cr_entries", []) if e.get("tdoc_number")}


def deduplicate_by_tdoc(results: list[CRDocumentData],
                        listed: set[tuple[str, str]] = frozenset()) -> list[CRDocumentData]:
    """같은 제출 번호의 CR 사본 중 하나를 선택하고 입력 경로 순으로 반환한다.

    오류가 없는 기록, TSG CR 목록의 판정 우선순위, 실제 팩 표지에 해당 문서가 포함된 기록,
    입력 경로 순서로 비교한다. 재배포된 팩이나 Release별 사본이 함께 있을 때 열리지 않는 사본이
    정상 사본을 가리거나, 더 우선하는 회의 판정을 가진 팩이 경로 순서 때문에 제외되는 것을 막는다.
    CR 목록에서 판정을 구분할 수 없는 사본은 팩 표지 포함 여부와 경로 순서로 결정한다."""
    seen = {}
    for r in sorted(results, key=lambda r: (bool(r.errors), tsg_cr_decision.rank(r.tdoc_number, r.cr_pack_id),
                                            (r.cr_pack_id, r.tdoc_number) not in listed, r.source_path)):
        if r.tdoc_number and r.tdoc_number not in seen:
            seen[r.tdoc_number] = r
    return sorted(seen.values(), key=lambda r: r.source_path)


def cover_number(source_path: str) -> str | None:
    """서식 머리가 적은 이 문서의 WG 번호(`extract_tdoc_from_document`). 문서를 열지 못하면 None.

    파일 이름 번호가 그 팩의 CR 이 아닐 때 `tsg_cr_decision.reconcile_cover_numbers` 가 부른다. 파싱은
    파일 이름 번호를 먼저 쓰므로 서식 번호는 그 기록에 남지 않아 문서를 다시 연다.
    """
    try:
        doc = docx_text.open_document(str(PROJECT_ROOT / source_path))
    except Exception:
        return None
    return extract_tdoc_from_document(doc, has_cr_form=find_cr_form_table(doc) is not None,
                                      filename=Path(source_path).name)


def tsg_direct_list(no_tdoc: list[CRDocumentData], tsg_own: list[CRDocumentData]) -> list[dict]:
    """CR 기록에서 빠진 TSG 직접 제출 CR 서식 문서(RP 번호마다 하나).

    `no_tdoc` 은 WG 번호가 없는 문서, `tsg_own` 은 TSG CR 디렉토리에 든 문서다(`tsg_cr_decision.split_tsg_cr`).
    `wg_tdoc` 은 `tsg_own` 문서가 파일 이름 · 서식 머리에 적은 WG 번호이고 그 WG CR 의 신원이 아니다.
    """
    seen = {}
    for r in sorted(no_tdoc, key=lambda r: r.source_path):
        if r.tsg_number and r.tsg_number not in seen:
            seen[r.tsg_number] = {"rp": r.tsg_number, "revision_of": r.tsg_revision_of, "wg_tdoc": None,
                                  "spec_number": r.spec_number, "source_path": r.source_path}
    for r in sorted(tsg_own, key=lambda r: (bool(r.errors), r.source_path)):
        if r.cr_pack_id not in seen:
            seen[r.cr_pack_id] = {"rp": r.cr_pack_id, "revision_of": None, "wg_tdoc": r.tdoc_number,
                                  "spec_number": r.spec_number, "source_path": r.source_path}
    return sorted(seen.values(), key=lambda e: e["rp"])


def cr_record(r: CRDocumentData) -> dict:
    """CR 기록. `tsg_*` 는 빠진 문서에만 쓰이므로 기록에 싣지 않는다."""
    d = asdict(r)
    d.pop("tsg_number")
    d.pop("tsg_revision_of")
    return d


# === 메인 ===

def main():
    configure_logging()
    log.info("=" * 60)
    log.info("RAN3 Phase-4 Step 1-2: CR 문서 파싱 시작")
    log.info("=" * 60)

    cr_docs = collect_cr_documents()
    _, unconverted_paths, other_wg = cr_other_wg.collect(WG)
    unconverted = [str(p.relative_to(PROJECT_ROOT)) for p in unconverted_paths]
    log.info(f"CR 문서 발견: {len(cr_docs)}개")

    # 병렬 파싱
    results = []

    results.extend(pool_run.run_all(parse_cr_document, cr_docs, 8, log))

    # 정렬 후 중복 제거
    # 팩 안 CR 폴더에 든 첨부 문서는 CR 이 아니다(`cr_attachments`). 중복 제거보다 먼저 가린다.
    results, attachments = cr_attachments.split(results, _TDOC_RE, _norm_tdoc)
    # TSG 회의에 RP 번호로 바로 올라온 CR 디렉토리의 문서는 WG CR 이 아니다(`tsg_cr_decision.split_tsg_cr`).
    results, tsg_own = tsg_cr_decision.split_tsg_cr(results)
    # 파일 이름 번호가 그 팩의 CR 이 아니면 서식 머리의 번호로 고친다(`tsg_cr_decision.reconcile_cover_numbers`).
    cover_fixes = tsg_cr_decision.reconcile_cover_numbers(results, cover_number)
    # CR 서식이 없는 문서는 팩 안에 놓였어도 CR 이 아니다(`cr_attachments.split_no_form`).
    results, no_form = cr_attachments.split_no_form(results)
    results.sort(key=lambda r: r.source_path)
    unique_results = deduplicate_by_tdoc(results, cover_listed(OUTPUT_DIR / "cover_sheets.json"))
    # 파일 이름 · 서식이 적은 Spec · CR 번호 · Release 를 TSG 회의 CR 시트 값으로 맞춘다(`tsg_cr_decision.correct_identity`).
    identity_fixes, identity_unlisted, identity_kept_spec = tsg_cr_decision.correct_identity(unique_results)
    from tdoc_source_metadata import phase4_sources
    source_projection = phase4_sources(sys.modules[__name__], unique_results)

    if not unique_results:
        log.error("유효한 CR 문서가 없습니다. 기존 출력은 유지합니다.")
        return 1

    # 통계
    total_with_reason = sum(1 for r in unique_results if r.reason_for_change)
    total_with_summary = sum(1 for r in unique_results if r.summary_of_change)
    total_with_consequences = sum(1 for r in unique_results if r.consequences_if_not_approved)
    total_with_clauses = sum(1 for r in unique_results if r.clauses_affected)
    total_with_cross_spec = sum(
        1 for r in unique_results
        if r.affects_core_spec or r.affects_test_spec or r.affects_om_spec
    )
    # 열 수 없다고 확인해 둔 문서(파서 옆 `known_unopenable.json`)의 열기 실패는 오류와 따로 센다(`cr_unopenable`).
    errors_unlisted, known_unopenable, unopenable_stale, unopenable_sha_mismatch = cr_unopenable.split(
        unique_results, cr_unopenable.load(cr_unopenable.list_path(Path(__file__).resolve().parent)), PROJECT_ROOT)
    total_with_errors = len(errors_unlisted)
    no_tdoc = [r for r in results if not r.tdoc_number]

    log.info("")
    log.info("=" * 60)
    log.info("파싱 결과 요약")
    log.info("=" * 60)
    log.info(f"  CR 문서 입력: {len(cr_docs)}개")
    log.info(f"  Unique CR (tdocNumber 기준): {len(unique_results)}개")
    log.info(f"  중복 제거: {len(results) - len(no_tdoc) - len(unique_results)}개")
    log.info(f"  tdocNumber 추출 실패: {len(no_tdoc)}개")
    log.info(f"  팩 CR 폴더의 첨부 문서 제외: {len(attachments)}개")
    log.info(f"  CR 서식이 없는 문서 제외(`no_cr_form` 으로 남김): {len(no_form)}개")
    log.info(f"  다른 WG 번호의 CR 제외(그 WG 가 읽음, `other_wg_cr`): {len(other_wg)}개")
    log.info(f"  TSG CR 디렉토리의 문서 제외(`tsg_direct_cr` 로 남김): {len(tsg_own)}개")
    log.info(f"  CR 시트 값으로 맞춘 CR: {len(identity_fixes)}개 (시트에 쌍이 없는 CR {identity_unlisted}개)")
    log.info(f"  파일 이름 · 서식 머리가 같아 시트와 달라도 둔 Spec: {len(identity_kept_spec)}개")
    log.info(f"  파일 이름 번호가 팩의 CR 이 아니라 서식 번호로 고친 CR: {len(cover_fixes)}개")
    log.info("")
    if unique_results:
        n = len(unique_results)
        log.info(f"  reasonForChange: {total_with_reason}/{n} ({total_with_reason/n*100:.1f}%)")
        log.info(f"  summaryOfChange: {total_with_summary}/{n} ({total_with_summary/n*100:.1f}%)")
        log.info(f"  consequencesIfNotApproved: {total_with_consequences}/{n} ({total_with_consequences/n*100:.1f}%)")
        log.info(f"  clausesAffected: {total_with_clauses}/{n} ({total_with_clauses/n*100:.1f}%)")
        log.info(f"  Cross-Spec 관계: {total_with_cross_spec}/{n} ({total_with_cross_spec/n*100:.1f}%)")
    log.info(f"  에러 있는 CR: {total_with_errors}개")
    log.info(f"  열 수 없다고 확인해 둔 문서의 열기 실패(오류와 따로 셈): {len(known_unopenable)}개")
    for p in unopenable_sha_mismatch:
        log.warning(f"    목록에 있으나 sha256 이 달라 오류로 셈: {p}")
    for p in unopenable_stale:
        log.warning(f"    목록에 있으나 이번 실행에서 열기 실패로 나오지 않음(목록 점검 필요): {p}")

    if no_tdoc:
        log.warning("\n  tdocNumber 추출 실패 파일:")
        for r in no_tdoc[:10]:
            log.warning(f"    {r.source_path}: {r.errors}")

    # JSON 출력
    output = {
        "metadata": {
            "total_cr_docs_found": len(cr_docs),
            "unconverted_doc": unconverted,
            "unique_crs": len(unique_results),
            "duplicates_removed": len(results) - len(no_tdoc) - len(unique_results),
            "tdoc_extraction_failed": len(no_tdoc),
            "tsg_direct_cr": tsg_direct_list(no_tdoc, tsg_own),
            "tdoc_extraction_failed_paths": sorted(r.source_path for r in no_tdoc),
            cr_attachments.METADATA_KEY: dict(sorted(attachments.items())),
            # CR 서식이 없어 CR 기록에서 뺀 문서 경로 → 그 문서 번호. Phase-8 이 이 번호를 청크로 만들지 않는다.
            cr_attachments.NO_FORM_KEY: no_form,
            # 이 슬롯에 놓였지만 파일 이름의 WG 번호가 다른 WG 인 CR → 그 WG. 그 WG 의 파서가 읽는다.
            "other_wg_cr": other_wg,
            # CR 시트 값으로 바꾼 필드 → [문서에서 읽은 값, 시트 값]
            "registry_identity_corrections": identity_fixes,
            "registry_identity_unlisted": identity_unlisted,
            "registry_identity_kept_spec": identity_kept_spec,
            "source_identity_projection": source_projection,
            # 파일 이름 번호 → [서식 번호, 팩, source_path]
            "registry_cover_number_corrections": cover_fixes,
            # 중복으로 걸러 낸 사본 → 그 tdoc. 다른 팩 · Release 폴더에 이름을 바꿔 다시 실린 사본은
            # 파일명으로 tdoc 을 읽을 수 없어, Phase-8 은 이 표로 사본을 알아본다.
            "duplicate_paths": duplicate_paths(results, unique_results),
            "strict_namespace_opened": docx_text.strict_opened(),
            "field_coverage": {
                "reasonForChange": total_with_reason,
                "summaryOfChange": total_with_summary,
                "consequencesIfNotApproved": total_with_consequences,
                "clausesAffected": total_with_clauses,
                "crossSpecAffects": total_with_cross_spec,
            },
            "errors_count": total_with_errors,
            # 열 수 없다고 확인해 둔 문서의 열기 실패. errors_count 에 넣지 않는다(`cr_unopenable`).
            "known_unopenable": sorted(r.source_path for r in known_unopenable),
            "known_unopenable_stale": unopenable_stale,
            "known_unopenable_sha_mismatch": unopenable_sha_mismatch,
        },
        "documents": [cr_record(r) for r in unique_results],
    }

    output_path = OUTPUT_DIR / "cr_documents.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_text_atomic(output_path, json.dumps(output, ensure_ascii=False, indent=2))

    log.info(f"\n출력: {output_path}")
    log.info(f"파일 크기: {output_path.stat().st_size / 1024:.1f} KB")

    # 오류가 있는 CR 은 결과에 남기되, 호출자(Phase-11 CR-1 등)가 다음 단계로 넘어가지 않도록 실패로 알린다.
    # 열 수 없다고 확인해 둔 문서의 열기 실패는 여기에 들지 않는다 — 목록 밖 오류만 1 로 끝낸다.
    if total_with_errors > 0:
        log.error(f"에러 있는 CR {total_with_errors}개 — 종료 코드 1")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
