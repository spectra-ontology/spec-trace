#!/usr/bin/env python3
"""
Phase-4 Step 1-2: CR 문서 파싱
- 입력: ontology/input/RAN/formal/CR/RAN1/Rel-*/TSG/*/*.docx (cover 제외, 2,119개)
- 출력: ontology/output/RAN/formal/parsed_cr/cr_documents.json

Spec: tdoc_ontology_specs(CR).md §3.1 CR 본문 정보, §3.2 Cross-Spec 영향
"""

import json
import re
import sys
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

from docx import Document

# === 경로 설정 ===
PROJECT_ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
INPUT_DIR = PROJECT_ROOT / "ontology" / "input" / "RAN" / "formal" / "CR" / "RAN1"
OUTPUT_DIR = PROJECT_ROOT / "ontology" / "output" / "RAN" / "formal" / "parsed_cr" / "RAN1"
LOG_DIR = PROJECT_ROOT / "logs" / "RAN" / "formal" / "RAN1" / "phase-4"

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
    source_path: str = ""
    errors: list = field(default_factory=list)


# === tdocNumber 추출 ===

# 근본 원칙: 이 CR 자신의 제출번호(TD#)는 파일명 또는
# 커버 헤더 문단에서만 추출한다. CR Form Table 셀(Reason/Summary/Other comments
# prose)에 등장하는 R{N}- 토큰은 *다른* CR 에 대한 *참조*이므로 자기 번호로 쓰면
# 오노드 MERGE → instantiation 통계 오염. python-docx 의 doc.paragraphs(본문 문단)
# 와 doc.tables(폼 셀)는 분리 스트림이라 문단만 보면 참조 오염이 구조적으로 차단됨.
# 근거: DROP 케이스는 전부 CR Form Table 단독 출현(=참조), 커버/파일명엔 자기 토큰 없음.
_TDOC_RE = re.compile(r"(R1[-_]\d{7})")
_CHANGE_MARK = re.compile(
    r"Reason for change|Summary of change|CHANGE REQUEST|Proposed change", re.I)


def _norm_tdoc(tok: str) -> str:
    """파일명-safe 언더스코어(R1_1900001)를 표준 대시 형태로 정규화."""
    return tok.replace(" ", "").replace("_", "-")


def extract_tdoc_from_filename(filename: str) -> str | None:
    """파일명에서 이 CR 자신의 TD#(R1-NNNNNNN, 대시/언더스코어) 추출."""
    m = _TDOC_RE.search(filename)
    return _norm_tdoc(m.group(1)) if m else None


def extract_tdoc_from_document(doc: Document, has_cr_form: bool = False) -> str | None:
    """커버 헤더 문단에서만 TD# 추출 (테이블 미사용 — 참조 오염 차단).
    1순위: '3GPP TSG' 앵커 줄(이 문서 자신의 번호).
    2순위: 변경마커 이전 첫 토큰 — CR Form Table 보유 문서 한정.
    비-CR discussion paper는 커버 윈도 산문에 타 문서 인용이 흔해
    2순위가 인용 토큰을 자기 번호로 오인하므로 차단."""
    cover = doc.paragraphs[:8]
    for p in cover:
        if "3GPP" in p.text and "TSG" in p.text:
            m = _TDOC_RE.search(p.text)
            if m:
                return _norm_tdoc(m.group(1))
    if not has_cr_form:
        return None
    for p in cover:
        if _CHANGE_MARK.search(p.text):
            break
        m = _TDOC_RE.search(p.text)
        if m:
            return _norm_tdoc(m.group(1))
    return None


def extract_spec_from_filename(filename: str) -> str | None:
    """파일명에서 Spec 번호 추출 (예: 38212 → 38.212)."""
    m = re.match(r"(\d{2})(\d{3})_", filename)
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    return None


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
    for row in table.rows:
        cells = [c.text.strip() for c in row.cells]
        for i, t in enumerate(cells):
            if t == "Release:":
                for v in cells[i + 1:]:
                    m = _REL_TOKEN_RE.fullmatch(v)
                    if m:
                        return f"Rel-{m.group(1)}"
    return None


# === CR Form Table 파싱 ===

def find_cr_form_table(doc: Document):
    """CR Form Table 찾기 (≥15행, 'Reason for change' 포함)."""
    for table in doc.tables:
        if len(table.rows) < 10:
            continue
        full_text = " ".join(c.text for row in table.rows for c in row.cells)
        if "Reason for change" in full_text:
            return table
    return None


def get_field_value(table, field_label: str) -> str | None:
    """CR Form Table에서 특정 필드의 값 추출.

    Table 구조: 셀이 병합되어 있으므로 label이 포함된 행에서 cells[2]를 읽음.
    """
    for row in table.rows:
        cells = [c.text.strip() for c in row.cells]
        # 특정 라벨을 포함하는 행 찾기
        row_text = " ".join(cells[:2]).lower()
        if field_label.lower() in row_text:
            # 병합된 셀에서 값 추출 - cells[2] 이후에서 unique한 값 찾기
            # cells[0-1]은 label, cells[2+]는 값 (병합으로 동일)
            if len(cells) > 2:
                value = cells[2].strip()
                if value and value.lower() != field_label.lower():
                    return value
    return None


def extract_other_specs(table) -> tuple[list[str], list[str], list[str]]:
    """'Other specs affected' 섹션에서 Spec 번호 추출.

    Table 구조:
    - "Other specs" 행 이후 3행이 Core/Test/O&M
    - Y/N 마커와 Spec 번호 포함

    반환: (core_specs, test_specs, om_specs)
    """
    core_specs = []
    test_specs = []
    om_specs = []

    spec_pattern = re.compile(r"\b(\d{2})\.\s*(\d{3})\b")

    # "Other specs" 행 찾기
    for i, row in enumerate(table.rows):
        cells = [c.text.strip() for c in row.cells]
        row_text = " ".join(cells).lower()

        if "other specs" not in row_text and "other core" not in row_text:
            continue

        # 이 행부터 3행을 순회하며 Core/Test/O&M 추출
        for j in range(i, min(i + 4, len(table.rows))):
            row_cells = [c.text.strip() for c in table.rows[j].cells]
            row_full = " ".join(row_cells).lower()

            # 모든 셀에서 Spec 번호 추출
            all_text = " ".join(row_cells)
            specs_found = [f"{m.group(1)}.{m.group(2)}" for m in spec_pattern.finditer(all_text)]

            if "core" in row_full:
                core_specs.extend(specs_found)
            elif "test" in row_full:
                test_specs.extend(specs_found)
            elif "o&m" in row_full or "o & m" in row_full:
                om_specs.extend(specs_found)
            else:
                # 첫 번째 매칭 행이 Core인 경우가 많음
                if j == i and specs_found:
                    core_specs.extend(specs_found)

        break  # Other specs 섹션은 한 번만

    # 중복 제거
    return list(dict.fromkeys(core_specs)), list(dict.fromkeys(test_specs)), list(dict.fromkeys(om_specs))


# === 단일 CR 문서 파싱 ===

def parse_cr_document(cr_path: Path, release: str) -> CRDocumentData:
    """단일 CR 문서 파싱."""
    cr_pack_id = cr_path.parent.name  # RP-XXXXXX

    # tdocNumber 추출: 파일명 우선
    tdoc_number = extract_tdoc_from_filename(cr_path.name)
    spec_number = extract_spec_from_filename(cr_path.name)
    fname_release = extract_release_from_filename(cr_path.name)

    result = CRDocumentData(
        tdoc_number=tdoc_number or "",
        cr_pack_id=cr_pack_id,
        release=fname_release or release,
        spec_number=spec_number,
        source_path=str(cr_path.relative_to(PROJECT_ROOT)),
    )

    try:
        doc = Document(str(cr_path))
    except Exception as e:
        result.errors.append(f"DOCX open failed: {e}")
        # 파일명에서 tdocNumber를 못 찾았으면 문서 fallback 불가
        if not result.tdoc_number:
            result.errors.append("tdocNumber extraction failed (no filename match, cannot open doc)")
        return result

    # CR Form Table — 필드 추출과 문서경유 키 신뢰 판별에 함께 사용
    cr_table = find_cr_form_table(doc)

    # 파일명 `(Rel-N)` 토큰이 없으면 CR Form `Release:` 필드로 보정
    if not fname_release and cr_table is not None:
        form_release = extract_release_from_cr_form(cr_table)
        if form_release:
            result.release = form_release

    # 파일명에서 R1을 못 찾은 경우 문서 내부 검색 (28개 비표준)
    if not result.tdoc_number:
        result.tdoc_number = extract_tdoc_from_document(
            doc, has_cr_form=cr_table is not None) or ""
        if not result.tdoc_number:
            result.errors.append("tdocNumber extraction failed (filename + document)")
            return result

    if not cr_table:
        result.errors.append("CR Form Table not found")
        return result

    # 필드 추출
    result.reason_for_change = get_field_value(cr_table, "reason for change")
    result.summary_of_change = get_field_value(cr_table, "summary of change")
    result.consequences_if_not_approved = get_field_value(cr_table, "consequences if not approved")

    clauses = get_field_value(cr_table, "clauses affected")
    if clauses:
        result.clauses_affected = clauses

    # Cross-Spec 영향
    core, test, om = extract_other_specs(cr_table)
    result.affects_core_spec = core
    result.affects_test_spec = test
    result.affects_om_spec = om

    return result


# === 파일 수집 ===

# CR Pack 문서 패턴: RP-XXXXXX.docx (순수 CR Pack 커버, 개별 CR 아님)
_CR_PACK_PURE_RE = re.compile(r"^RP-\d+\.docx$", re.IGNORECASE)


def collect_cr_documents() -> list[tuple[Path, str]]:
    """모든 CR 문서 경로 수집 (cover + 순수 CR Pack 제외, Rel-15→19 순서).

    제외 대상:
    - *_cover.docx: CR Pack 커버시트 (01_parse_cover_sheets.py에서 처리)
    - RP-XXXXXX.docx: 순수 CR Pack 문서 (개별 CR이 아님)
      → 내용 중 참조된 R1 번호를 잘못 추출하는 근본 원인 방지
      예: RP-200483.docx → R1-2001146 (discussion 문서) 잘못 추출
    """
    cr_docs = []
    skipped_crpack = 0
    for rel_dir in sorted(INPUT_DIR.iterdir()):
        if not rel_dir.is_dir() or not rel_dir.name.startswith("Rel-"):
            continue
        release = rel_dir.name
        tsg_dir = rel_dir / "TSG"
        if not tsg_dir.exists():
            continue
        for pack_dir in sorted(tsg_dir.iterdir()):
            if not pack_dir.is_dir():
                continue
            for f in sorted(pack_dir.iterdir()):
                if f.suffix.lower() != ".docx":
                    continue
                if f.name.lower().endswith("_cover.docx"):
                    continue
                if _CR_PACK_PURE_RE.match(f.name):
                    skipped_crpack += 1
                    continue
                cr_docs.append((f, release))
    if skipped_crpack:
        log.info(f"  CR Pack 문서 {skipped_crpack}개 제외 (RP-XXXXXX.docx)")
    return cr_docs


def deduplicate_by_tdoc(results: list[CRDocumentData]) -> list[CRDocumentData]:
    """tdocNumber 기준 first-seen 중복 제거."""
    seen = {}
    for r in results:
        if r.tdoc_number and r.tdoc_number not in seen:
            seen[r.tdoc_number] = r
    return list(seen.values())


# === 메인 ===

def main():
    log.info("=" * 60)
    log.info("Phase-4 Step 1-2: CR 문서 파싱 시작")
    log.info("=" * 60)

    cr_docs = collect_cr_documents()
    log.info(f"CR 문서 발견: {len(cr_docs)}개")

    # 병렬 파싱
    results = []

    with ProcessPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(parse_cr_document, path, release): path
            for path, release in cr_docs
        }
        for future in as_completed(futures):
            path = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                log.error(f"  {path.name}: {e}")

    # 정렬 후 중복 제거
    results.sort(key=lambda r: r.source_path)
    unique_results = deduplicate_by_tdoc(results)

    # 통계
    total_with_reason = sum(1 for r in unique_results if r.reason_for_change)
    total_with_summary = sum(1 for r in unique_results if r.summary_of_change)
    total_with_consequences = sum(1 for r in unique_results if r.consequences_if_not_approved)
    total_with_clauses = sum(1 for r in unique_results if r.clauses_affected)
    total_with_cross_spec = sum(
        1 for r in unique_results
        if r.affects_core_spec or r.affects_test_spec or r.affects_om_spec
    )
    total_with_errors = sum(1 for r in unique_results if r.errors)
    no_tdoc = [r for r in results if not r.tdoc_number]

    log.info("")
    log.info("=" * 60)
    log.info("파싱 결과 요약")
    log.info("=" * 60)
    log.info(f"  CR 문서 입력: {len(cr_docs)}개")
    log.info(f"  Unique CR (tdocNumber 기준): {len(unique_results)}개")
    log.info(f"  중복 제거: {len(results) - len(unique_results)}개")
    log.info(f"  tdocNumber 추출 실패: {len(no_tdoc)}개")
    log.info("")
    log.info(f"  reasonForChange: {total_with_reason}/{len(unique_results)} ({total_with_reason/len(unique_results)*100:.1f}%)")
    log.info(f"  summaryOfChange: {total_with_summary}/{len(unique_results)} ({total_with_summary/len(unique_results)*100:.1f}%)")
    log.info(f"  consequencesIfNotApproved: {total_with_consequences}/{len(unique_results)} ({total_with_consequences/len(unique_results)*100:.1f}%)")
    log.info(f"  clausesAffected: {total_with_clauses}/{len(unique_results)} ({total_with_clauses/len(unique_results)*100:.1f}%)")
    log.info(f"  Cross-Spec 관계: {total_with_cross_spec}/{len(unique_results)} ({total_with_cross_spec/len(unique_results)*100:.1f}%)")
    log.info(f"  에러 있는 CR: {total_with_errors}개")

    if no_tdoc:
        log.warning(f"\n  tdocNumber 추출 실패 파일:")
        for r in no_tdoc:
            log.warning(f"    {r.source_path}: {r.errors}")

    # JSON 출력
    output = {
        "metadata": {
            "total_cr_docs_found": len(cr_docs),
            "unique_crs": len(unique_results),
            "duplicates_removed": len(results) - len(unique_results),
            "tdoc_extraction_failed": len(no_tdoc),
            "field_coverage": {
                "reasonForChange": total_with_reason,
                "summaryOfChange": total_with_summary,
                "consequencesIfNotApproved": total_with_consequences,
                "clausesAffected": total_with_clauses,
                "crossSpecAffects": total_with_cross_spec,
            },
            "errors_count": total_with_errors,
        },
        "cr_documents": [asdict(r) for r in unique_results],
    }

    output_path = OUTPUT_DIR / "cr_documents.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    log.info(f"\n출력: {output_path}")
    log.info(f"파일 크기: {output_path.stat().st_size / 1024:.1f} KB")

    return 0


if __name__ == "__main__":
    sys.exit(main())
