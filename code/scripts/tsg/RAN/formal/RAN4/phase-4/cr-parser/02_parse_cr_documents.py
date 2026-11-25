#!/usr/bin/env python3
"""
RAN4 Phase-4 Step 1-2: CR 문서 파싱
- 입력: data/corpus/tsg/RAN/formal/change-requests/RAN4/derived/Rel-*/TSG/{팩}/ — `cr_inputs` 가 모은다(표지 제외)
- 출력: ontology/output/tsg/RAN/formal/parsed_cr/RAN4/cr_documents.json

Spec §2 CR 클래스 확장, §4 CR 문서 파싱 규칙 (RAN4 고유)
RAN4 고유: 29,000+건 대규모 → 프로세스 풀(pool_run) + Resume 로직
           R4-\d{7} 패턴 (7자리)
"""

import hashlib
import json
import re
import sys
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path

from docx import Document

# === 경로 설정 ===
PROJECT_ROOT = Path(__file__).resolve().parents[7]
_SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "common"))
from common.atomic_io import write_text_atomic  # noqa: E402
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "tsg" / "RAN" / "formal" / "common"))
import docx_text  # noqa: E402 — 문단 · 표 칸 읽기 규칙(변경 표시 · 필드 안의 글까지)
import pool_run  # noqa: E402 — 워커가 죽어도 항목을 잃지 않는 풀
import cr_form  # noqa: E402 — CR 서식이 적은 spec · CR 번호 · 제목
import cr_word_title  # noqa: E402 — LibreOffice 변환본의 표지 제목을 원본 .doc 글로 읽는다
import cr_form_slot  # noqa: E402 — CR 서식 본문 네 칸을 이름 칸이 망가져도 서식 틀의 자리로 읽는다
import cr_inputs  # noqa: E402 — Phase-0 CR 산출 슬롯에서 입력 모으기
import tsg_cr_decision  # noqa: E402 — TSG 회의가 팩 안 CR 마다 내린 판정
import cr_attachments  # noqa: E402 — 팩 안 CR 폴더에 든 첨부 문서 가리기
import cr_other_wg  # noqa: E402 — 다른 WG 슬롯에 놓인 이 WG 의 CR · 이 슬롯에 놓인 다른 WG 의 CR
import cr_unopenable  # noqa: E402 — 열 수 없다고 확인해 둔 CR 문서 목록과 오류 가르기
WG = "RAN4"
INPUT_DIR = cr_inputs.derived_dir(WG)
OUTPUT_DIR = PROJECT_ROOT / "ontology" / "output" / "tsg" / "RAN" / "formal" / "parsed_cr" / "RAN4"
LOG_DIR = PROJECT_ROOT / "logs" / "tsg" / "RAN" / "formal" / "RAN4" / "phase-4"
RESUME_FILE = LOG_DIR / "02_resume_state.json"


def configure_logging() -> None:
    """실행 진입점에서만 로그를 준비한다.

    로그 파일은 mode="w" 로 열리므로 이 설정이 모듈 최상위에 있으면 import 만으로
    운영 로그가 비워진다. 이 모듈을 싣기만 하는 쪽(측정 도구, Phase-11 작업)이
    남의 기록을 지우지 않도록 main() 이 부를 때만 연다.
    """
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

# 대용량 처리(Spec Step 7 §2 '대용량 처리 전략') — 배치 크기·워커 수는 step1_cr_parsing.md 'Step 1-2: CR 문서 파싱'
BATCH_SIZE = 2000
MAX_WORKERS = 8


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
    # CR 서식이 적은 값. 표지가 없는 팩의 CR 은 이 자리에서만 CR 번호 · 제목을 얻는다(`cr_form.form_fields`).
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

# 근본 원칙: 이 CR 자신의 제출번호(TD#)는 파일명 또는
# 커버 헤더 문단에서만 추출한다. CR Form Table 셀(Reason/Summary/Other comments
# prose)에 등장하는 R{N}- 토큰은 *다른* CR 에 대한 *참조*이므로 자기 번호로 쓰면
# 오노드 MERGE → instantiation 통계 오염. python-docx 의 doc.paragraphs(본문 문단)
# 와 doc.tables(폼 셀)는 분리 스트림이라 문단만 보면 참조 오염이 구조적으로 차단됨.
# 근거: DROP 케이스는 전부 CR Form Table 단독 출현(=참조), 커버/파일명엔 자기 토큰 없음.
# 추가: RAN4 일부 파일명은 R4_2100248 처럼 언더스코어 → 정규화로 R4-2100248 복구.
# 번호 뒤에 숫자가 이어지면 번호가 아니다(파일명 오타 `R5-2474883` 을 `R5-247488` 로 잘라 남의 번호를 받는다).
_TDOC_RE = re.compile(r"(R4[-_]\d{6,8})(?!\d)")
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
    """파일명-safe 언더스코어(R4_2100248)를 표준 대시 형태로 정규화."""
    return tok.replace(" ", "").replace("_", "-")


def extract_tdoc_from_filename(filename: str) -> str | None:
    """파일명에서 이 CR 자신의 TD#(R4-NNNNNNN, 대시/언더스코어) 추출. Spec §4.2

    주의: 옛 판을 가리키는 말 바로 뒤의 번호는 건너뛴다. RAN4 RP-252400 디렉토리 `R4-2511845/` 에 든
    `Rev of R4-2509437 CR on fragmented carriers TR_v2_HW_EAB.docx` 는 머리글이 `R4-2511845` 이고
    RAN#109 CR 시트도 RP-252400 의 38.755 CR0002 rev 1 을 `R4-2511845` 로 둔다. 이름의 첫 번호를 받으면
    옛 판 번호가 이 CR 의 기록이 되어 팩의 CR 을 잃는다. 이름에 다른 번호가 없으면 문서 안에서 찾는다.
    """
    for m in _TDOC_RE.finditer(filename):
        if not _FILENAME_EARLIER.search(filename[:m.start()]):
            return _norm_tdoc(m.group(1))
    return None


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
    """CR Form Table 찾기 (서식 본문 이름 칸을 가진 표 — `cr_form.is_form_table`). 겉 표 칸 안에 든 서식 표도 찾는다.

    10행 하한은 서식 본문 한 벌에 건다. 빈 문단으로 끊긴 서식은 앞뒤로 이어진 표(`cr_form.form_block`)
    가운데 서식 이름 칸(`cr_form.FORM_LABELS`)을 가진 표의 행을 더한다. 아래 읽기 함수가 모두 그 묶음을
    읽기 때문이다. 표 한 장에 걸면 8+6 처럼 나뉜 서식은 두 표 모두 하한에 못 미쳐 버려진다.
    이름 칸이 없는 표(머리 줄 표 · 붙어 있는 다른 표)의 행은 세지 않는다. 세면 이름 칸을 인용한
    작은 표가 옆 표의 행을 빌려 서식이 되고, 글 있는 문단으로 끊긴 서식 조각이 머리 줄 표의 행을
    빌려 하한을 넘는다.
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
    Spec §4.3: specNumber 패턴 \\d{2}\\.\\d{3}(-\\d+)?
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

    return (
        list(dict.fromkeys(core_specs)),
        list(dict.fromkeys(test_specs)),
        list(dict.fromkeys(om_specs)),
    )


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

    # 파일명에서 R4를 못 찾은 경우 문서 내부 검색
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
                    [docx_text.final_text(p) for p in doc.paragraphs[:8]])
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

    # Cross-Spec 영향 (Spec §4.3)
    core, test, om = extract_other_specs(cr_table)
    result.affects_core_spec = core
    result.affects_test_spec = test
    result.affects_om_spec = om

    return result


# === 파일 수집 ===

def collect_cr_documents() -> list[tuple[Path, str]]:
    """CR 문서 `(경로, 디렉토리 Release)` 목록. 모으는 규칙은 `cr_inputs` 이고 여기서는 표지만 뺀다.

    표지는 `_cover.docx` 접미로만 가른다(`Recovery` · `Coverage` 가 든 CR 이름을 잘못 빼지 않게).
    CR 하나의 표지(같은 Tdoc 본문 곁에 실린 `R4-1816258 … - Cover page.docx` · `RP-182899 Cover.docx`)는
    빼지 않는다. Phase-4 가 읽는 것은 CR 서식이고, 이런 묶음에서는 서식이 표지에 있다(TSG 에 바로 낸
    `RP-182899` · `RP-190747` 은 표지만 서식을 가져 `tsg_direct_cr` 기록이 표지에서 나온다). 같은 Tdoc 의
    표지와 본문 기록 가운데 하나는 `deduplicate_by_tdoc` 가 오류 없는 쪽으로 고른다. 본문 청크를 만드는
    Phase-8 은 반대로 이런 표지를 뺀다(`cr_inputs.without_covers`).
    RP 번호 이름의 문서(`RP-NNNNNN.docx`)도 모은다. WG 번호를 얻지 못한 문서는 CR 기록에서 빠지며,
    그중 CR 서식을 가진 TSG 직접 제출 문서는 메타데이터 `tsg_direct_cr` 에 남는다.

    주의: 읽을 수 없는 문서(변환본 없는 `.doc` · ZIP 아닌 `.docx`)도 목록에 넣는다. 열기에서 실패해
    파일 이름에서 얻은 Tdoc · Spec · CR 번호 · Release 와 `DOCX open failed` 오류만 가진 기록이 된다.
    빼면 그 CR 이 팩의 CR 목록과 `crCount` 에서 사라진다(RAN5 `RP-240174` 의 IRM 암호화 CR
    `R5-241785`~`R5-241788` 이 빠져 34 가 30 이 됐다). 같은 Tdoc 의 읽힌 사본이 있으면
    `deduplicate_by_tdoc` 가 오류 없는 쪽을 고르므로 읽힌 기록을 가리지 않는다. 목록 자체는 메타데이터
    `unconverted_doc` 에도 남는다.

    주의: 파일 이름의 WG 번호가 다른 WG 인 CR 은 이 목록에서 빠지고(그 WG 가 읽는다, 메타데이터
    `other_wg_cr`), 다른 WG 슬롯에 놓인 이 WG 의 CR 은 들어온다(`cr_other_wg`). 팩 번호와 Release 는
    파일이 놓인 슬롯을 기준으로 읽는다.
    """
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


def deduplicate_by_tdoc(results: list[CRDocumentData]) -> list[CRDocumentData]:
    """tdocNumber 마다 기록 하나. 오류 없는 기록, TSG 회의 판정이 앞서는 팩의 기록, 경로 순서의 첫 기록 차례로 고른다.

    같은 CR 이 여러 Release 폴더 · 팩에 다시 배포된다. 경로 순서만으로 고르면 열리지 않거나
    서식이 없는 사본이 먼저 와서 읽힌 사본을 가린다.

    주의: 같은 CR 이 두 팩 디렉토리에 놓이면 어느 팩이 그 CR 을 다뤘는지는 경로 · 팩 번호로 정할 수 없다.
    RAN#87-e 은 RP-200401 를 RP-200484 로 다시 냈고(TDoc 목록의 CR 시트에서 `R4-2002340` 은 RP-200401 `reissued`,
    RP-200484 `approved`), 경로 순서로는 옛 팩이 이긴다. 그래서 TSG 회의 TDoc 목록의 판정 순위
    (`tsg_cr_decision.rank`)가 앞서는 팩의 사본을 먼저 고른다.
    """
    seen = {}
    for r in sorted(results, key=lambda r: (bool(r.errors), tsg_cr_decision.rank(r.tdoc_number, r.cr_pack_id),
                                            r.source_path)):
        if r.tdoc_number and r.tdoc_number not in seen:
            seen[r.tdoc_number] = r
    return sorted(seen.values(), key=lambda r: r.source_path)


# === Resume 로직 ===

def input_fingerprint(cr_docs: list[tuple[Path, str]]) -> str:
    """재개 상태를 묶는 지문 — 배치 크기 · 파서와 저장소 안에서 import 한 모듈의 원문 · 입력 경로 · Release · 파일 내용.

    재개는 앞 배치의 부분 결과를 그대로 쓰고 순번이 다음인 배치부터 돈다. 그사이 입력 목록이나 내용,
    배치 크기, 파서 코드가 바뀌면 같은 순번이 다른 파일을 가리켜 지운 문서가 남고 새 문서가 빠진다.
    """
    h = hashlib.sha256()
    h.update(f"batch_size={BATCH_SIZE}\n".encode())
    sources = {Path(__file__).resolve()}
    for m in list(sys.modules.values()):
        src = getattr(m, "__file__", None)
        if src and Path(src).resolve().is_relative_to(_SCRIPTS_DIR):
            sources.add(Path(src).resolve())
    for src in sorted(sources):
        h.update(f"{src.relative_to(_SCRIPTS_DIR)}\n".encode())
        h.update(src.read_bytes())
    for path, release in cr_docs:
        h.update(f"{path.relative_to(PROJECT_ROOT)}\t{release}\n".encode())
        h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()


def save_resume_state(batch_idx: int, results_so_far: list[dict], fingerprint: str):
    """중간 상태 저장 (Resume 지원). 지문이 다음 실행의 지문과 다르면 재개하지 않는다."""
    state = {
        "batch_idx": batch_idx,
        "results_count": len(results_so_far),
        "input_fingerprint": fingerprint,
    }
    write_text_atomic(RESUME_FILE, json.dumps(state))


def save_partial_results(results: list[CRDocumentData], batch_idx: int):
    """배치별 부분 결과 저장."""
    partial_path = OUTPUT_DIR / f"cr_documents_batch_{batch_idx:03d}.json"
    data = [asdict(r) for r in results]
    partial_path.parent.mkdir(parents=True, exist_ok=True)
    write_text_atomic(partial_path, json.dumps(data, ensure_ascii=False, indent=2))
    return partial_path


def load_partial_results(start_batch: int) -> list[CRDocumentData]:
    """재개할 때 앞 배치들의 부분 결과를 다시 읽는다. 하나라도 없으면 멈춘다(없는 배치는 산출에서 빠진다)."""
    results = []
    for bi in range(start_batch):
        partial_path = OUTPUT_DIR / f"cr_documents_batch_{bi:03d}.json"
        if not partial_path.exists():
            raise FileNotFoundError(f"재개할 앞 배치 결과가 없음: {partial_path} — Resume 파일을 지우고 처음부터 돌릴 것")
        with open(partial_path, encoding="utf-8") as f:
            results.extend(CRDocumentData(**d) for d in json.load(f))
    return results


def cleanup_partial_files():
    """부분 결과 파일 삭제."""
    for partial in OUTPUT_DIR.glob("cr_documents_batch_*.json"):
        partial.unlink()
    if RESUME_FILE.exists():
        RESUME_FILE.unlink()


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
    log.info("RAN4 Phase-4 Step 1-2: CR 문서 파싱 시작")
    log.info("=" * 60)

    cr_docs = collect_cr_documents()
    _, unconverted_paths, other_wg = cr_other_wg.collect(WG)
    unconverted = [str(p.relative_to(PROJECT_ROOT)) for p in unconverted_paths]
    log.info(f"CR 문서 발견: {len(cr_docs)}개")

    # 배치 처리 (Resume 지원)
    all_results = []
    total_batches = (len(cr_docs) + BATCH_SIZE - 1) // BATCH_SIZE

    # Resume 체크 — 지금 입력 · 배치 크기 · 파서의 지문이 상태 파일과 같을 때만 이어 간다
    fingerprint = input_fingerprint(cr_docs)
    start_batch = 0
    if RESUME_FILE.exists():
        with open(RESUME_FILE, encoding="utf-8") as f:
            resume = json.load(f)
        if resume.get("input_fingerprint") != fingerprint:
            log.warning("  Resume 상태가 지금 입력 · 배치 크기 · 파서와 맞지 않음 — 앞 배치 결과를 지우고 처음부터 돈다")
            cleanup_partial_files()
        else:
            start_batch = resume.get("batch_idx", 0) + 1
            log.info(f"  Resume: batch {start_batch}부터 재시작 (이전 {resume.get('results_count', 0)}건)")
            all_results = load_partial_results(start_batch)

    for batch_idx in range(start_batch, total_batches):
        batch_start = batch_idx * BATCH_SIZE
        batch_end = min(batch_start + BATCH_SIZE, len(cr_docs))
        batch = cr_docs[batch_start:batch_end]
        log.info(f"  배치 {batch_idx + 1}/{total_batches}: {len(batch)}건 ({batch_start}~{batch_end - 1})")

        batch_results = []
        batch_results.extend(pool_run.run_all(parse_cr_document, batch, MAX_WORKERS, log))

        # 배치 부분 결과 저장
        save_partial_results(batch_results, batch_idx)
        all_results.extend(batch_results)
        save_resume_state(batch_idx, all_results, fingerprint)
        log.info(f"    → {len(batch_results)}건 파싱 완료 (누적: {len(all_results)})")

    # 정렬 후 중복 제거
    # 팩 안 CR 폴더에 든 첨부 문서는 CR 이 아니다(`cr_attachments`). 중복 제거보다 먼저 가린다.
    all_results, attachments = cr_attachments.split(all_results, _TDOC_RE, _norm_tdoc)
    # TSG 회의에 RP 번호로 바로 올라온 CR 디렉토리의 문서는 WG CR 이 아니다(`tsg_cr_decision.split_tsg_cr`).
    all_results, tsg_own = tsg_cr_decision.split_tsg_cr(all_results)
    # 파일 이름 번호가 그 팩의 CR 이 아니면 서식 머리의 번호로 고친다(`tsg_cr_decision.reconcile_cover_numbers`).
    cover_fixes = tsg_cr_decision.reconcile_cover_numbers(all_results, cover_number)
    # CR 서식이 없는 문서는 팩 안에 놓였어도 CR 이 아니다(`cr_attachments.split_no_form`).
    all_results, no_form = cr_attachments.split_no_form(all_results)
    all_results.sort(key=lambda r: r.source_path)
    unique_results = deduplicate_by_tdoc(all_results)
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
    no_tdoc = [r for r in all_results if not r.tdoc_number]

    log.info("")
    log.info("=" * 60)
    log.info("파싱 결과 요약")
    log.info("=" * 60)
    log.info(f"  CR 문서 입력: {len(cr_docs)}개")
    log.info(f"  Unique CR (tdocNumber 기준): {len(unique_results)}개")
    log.info(f"  중복 제거: {len(all_results) - len(no_tdoc) - len(unique_results)}개")
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

    # 최종 JSON 출력
    output = {
        "metadata": {
            "total_cr_docs_found": len(cr_docs) + len(source_projection['sourceClassifications']),
            "unconverted_doc": unconverted,
            "unique_crs": len(unique_results),
            "duplicates_removed": len(all_results) + len(source_projection['sourceClassifications']) - len(no_tdoc) - len(unique_results),
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
            "duplicate_paths": duplicate_paths(all_results, unique_results),
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
    log.info(f"파일 크기: {output_path.stat().st_size / 1024 / 1024:.1f} MB")

    # 부분 결과 정리
    cleanup_partial_files()
    log.info("Resume 파일 정리 완료")

    # 오류가 있는 CR 은 결과에 남기되, 호출자(Phase-11 CR-1 등)가 다음 단계로 넘어가지 않도록 실패로 알린다.
    # 열 수 없다고 확인해 둔 문서의 열기 실패는 여기에 들지 않는다 — 목록 밖 오류만 1 로 끝낸다.
    if total_with_errors > 0:
        log.error(f"에러 있는 CR {total_with_errors}개 — 종료 코드 1")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
