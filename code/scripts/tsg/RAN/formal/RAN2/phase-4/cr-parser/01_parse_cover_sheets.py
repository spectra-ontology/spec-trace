#!/usr/bin/env python3
"""
RAN2 Phase-4 Step 1-1: Cover Sheet 파싱
- 입력: data/corpus/tsg/RAN/formal/change-requests/RAN2/derived/Rel-*/TSG/{팩}/*_cover.docx (`.doc` 표지는 슬롯의 `.docx` 변환본)
  + 다른 WG 슬롯에 놓였지만 이 WG 의 CR 이 든 팩(`cr_other_wg.foreign_packs`)
- 출력: ontology/output/tsg/RAN/formal/parsed_cr/RAN2/cover_sheets.json

Spec Step 2 §5.1 CRPack, Step 7 §5 CRPack 인스턴스 생성
표지가 `.doc` 로만 배포된 팩은 Phase-0 이 슬롯에 둔 `.docx` 변환본을 읽는다
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
import pool_run  # noqa: E402 — 워커가 죽어도 항목을 잃지 않는 풀
import cr_inputs  # noqa: E402 — Phase-0 CR 산출 슬롯
import cr_other_wg  # noqa: E402  (다른 WG 슬롯에 놓인 이 WG 의 CR)
import os_residue  # noqa: E402 — 압축 도구가 남긴 잔재 이름(cr_inputs 가 경로를 더한 공용 모듈)
INPUT_DIR = cr_inputs.derived_dir("RAN2")
OUTPUT_DIR = PROJECT_ROOT / "ontology" / "output" / "tsg" / "RAN" / "formal" / "parsed_cr" / "RAN2"
LOG_DIR = PROJECT_ROOT / "logs" / "tsg" / "RAN" / "formal" / "RAN2" / "phase-4"


def configure_logging() -> None:
    """실행 진입점에서만 로그를 준비한다.

    로그 파일은 mode="w" 로 열리므로 이 설정이 모듈 최상위에 있으면 import 만으로
    운영 로그가 비워진다. 측정 도구나 Phase-11 작업이 이 모듈을 import할 때
    기존 실행 기록을 지우지 않도록 main()에서만 로그 파일을 연다.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_DIR / "01_parse_cover_sheets.log", mode="w"),
        ],
    )


log = logging.getLogger(__name__)


# === 데이터 모델 ===
@dataclass
class CoverSheetEntry:
    spec: str
    cr_number: str
    rev: str
    release: str
    title: str
    category: str
    version: str
    meeting: str
    tdoc_number: str
    source: str
    work_item: str
    clauses_affected: str
    other_aff_specs: str
    # 번호 칸이 자릿수를 넘었지만 앞부분이 이 팩의 CR 문서 번호와 같아 그 번호로 받은 행의 경고(`overflow_tdoc`).
    # 정상 행은 빈 문자열이다.
    tdoc_number_warning: str = ""


@dataclass
class CoverSheetData:
    cr_pack_id: str
    tsg_meeting: str
    release: str
    source_path: str
    cr_entries: list = field(default_factory=list)
    errors: list = field(default_factory=list)


# === 파싱 함수 ===

def extract_tsg_meeting(doc: Document) -> str:
    """Cover Sheet 첫 5개 paragraph에서 TSG Meeting 번호 추출.

    패턴: "3GPP TSG-RAN Meeting #NNN"
    정규화: "RAN#NNN" 형식으로 반환
    """
    for p in doc.paragraphs[:5]:
        text = docx_text.final_text(p)
        if not text:
            continue
        m = re.search(r"(?:TSG[- ]?)?RAN\s*(?:Meeting\s*)?#(\d+)", text, re.IGNORECASE)
        if m:
            return f"RAN#{m.group(1)}"
    return ""


def pack_cr_tdocs(pack_dir: Path) -> frozenset:
    """팩 안 CR 문서(`.doc` · `.docx`) 파일 이름에 든 이 WG 번호 집합.

    표지 행의 번호가 자릿수를 넘을 때 그 앞부분이 이 팩에 실제로 든 CR 인지 대조하는 데 쓴다.
    하위 폴더(안쪽 zip 을 푼 폴더)까지 보고 압축 도구 잔재(`__MACOSX` · `._*`)는 건너뛴다.
    """
    found = set()
    for f in pack_dir.rglob("*"):
        if not f.is_file() or os_residue.classify_path(f.relative_to(pack_dir)):
            continue
        if f.suffix.lower() in (".docx", ".doc"):
            m = re.search(r"(R2-\d{7})(?!\d)", f.name)
            if m:
                found.add(m.group(1))
    return frozenset(found)


def overflow_tdoc(tdoc_raw: str, pack_tdocs: frozenset) -> tuple[str, str]:
    """자릿수를 넘친 번호 칸을 이 팩의 실제 CR 번호로 받을 수 있으면 `(번호, 경고)`, 아니면 `("", "")`.

    뒤 숫자 배제 때문에 번호를 못 찾은 칸(`R2-` 뒤 숫자가 7자리를 넘는 칸)만 대상이다. 앞 7자리가
    같은 팩의 CR 문서 파일 번호와 같을 때만 받는다. 팩에 그 CR 문서가 없으면 의도한 번호를 알 수
    없으므로 받지 않는다(앞부분만 잘라 받으면 엉뚱한 CR 에 붙을 수 있다).
    """
    m = re.search(r"R2-(\d{8,})", tdoc_raw)
    if not m:
        return "", ""
    head = "R2-" + m.group(1)[:7]
    if head not in pack_tdocs:
        return "", ""
    return head, (f"tdoc cell has {len(m.group(1))} digits (expected 7); "
                  "leading digits match a CR document in this pack")


def parse_cr_table(table, pack_tdocs: frozenset = frozenset()) -> list[CoverSheetEntry]:
    """Cover Sheet의 CR 목록 테이블 파싱.

    테이블 구조 (13컬럼):
    TS | CR | Rev | Rel | Title | Cat | Vsn | @ Mtg | TD# | Source to WG | Work Item | Clauses affected | Other Aff Specs
    """
    entries = []
    rows = table.rows

    if len(rows) < 2:
        return entries

    # 헤더 행 확인 (첫 행)
    header_cells = [docx_text.cell_text(c).lower() for c in rows[0].cells]

    # 컬럼 인덱스 매핑
    col_map = {}
    expected = {
        "ts": "spec", "cr": "cr_number", "rev": "rev", "rel": "release",
        "title": "title", "cat": "category", "vsn": "version",
        "@ mtg": "meeting", "td#": "tdoc_number",
        "source to wg": "source", "work item": "work_item",
        "clauses affected": "clauses_affected", "other aff specs": "other_aff_specs",
    }
    for i, h in enumerate(header_cells):
        for key, field_name in expected.items():
            if key in h:
                col_map[field_name] = i
                break

    # 데이터 행 파싱 (헤더 이후)
    for row in rows[1:]:
        cells = [docx_text.cell_text(c) for c in row.cells]
        if not cells or not any(cells):
            continue

        # TD# 컬럼에서 R2-XXXXXXX 추출
        tdoc_idx = col_map.get("tdoc_number", 8)
        tdoc_raw = cells[tdoc_idx] if tdoc_idx < len(cells) else ""

        # R2 패턴이 없으면 빈 행으로 간주
        # 셀에는 회의명(`R2-NNNChicago,…`)·수정 표기(`revof…`)·자릿수 오타가 붙어 오기도 한다.
        # 셀 전체가 아니라 패턴에 맞은 부분만 번호로 삼아야 CR 파일의 tdoc 과 같은 키가 된다.
        # 자릿수가 넘치는 번호는 그대로 잘라 받지 않는다 — CR 문서 파서도 같은 파일명을 거부하므로,
        # 잘라 받으면 의도한 번호를 추측해 엉뚱한 CR 에 붙일 수 있다.
        tdoc_match = re.search(r"R2-\d{7}(?!\d)", tdoc_raw)
        # 넘친 번호는 앞 7자리가 이 팩의 CR 문서일 때만 그 번호로 받고 경고를 남긴다(`overflow_tdoc`).
        tdoc_number, tdoc_warning = ((tdoc_match.group(0), "") if tdoc_match
                                     else overflow_tdoc(tdoc_raw, pack_tdocs))
        if not tdoc_number:
            continue

        entry = CoverSheetEntry(
            spec=cells[col_map.get("spec", 0)] if col_map.get("spec", 0) < len(cells) else "",
            cr_number=cells[col_map.get("cr_number", 1)] if col_map.get("cr_number", 1) < len(cells) else "",
            rev=cells[col_map.get("rev", 2)] if col_map.get("rev", 2) < len(cells) else "",
            release=cells[col_map.get("release", 3)] if col_map.get("release", 3) < len(cells) else "",
            title=cells[col_map.get("title", 4)] if col_map.get("title", 4) < len(cells) else "",
            category=cells[col_map.get("category", 5)] if col_map.get("category", 5) < len(cells) else "",
            version=cells[col_map.get("version", 6)] if col_map.get("version", 6) < len(cells) else "",
            meeting=cells[col_map.get("meeting", 7)] if col_map.get("meeting", 7) < len(cells) else "",
            tdoc_number=tdoc_number,
            tdoc_number_warning=tdoc_warning,
            source=cells[col_map.get("source", 9)] if col_map.get("source", 9) < len(cells) else "",
            work_item=cells[col_map.get("work_item", 10)] if col_map.get("work_item", 10) < len(cells) else "",
            clauses_affected=cells[col_map.get("clauses_affected", 11)] if col_map.get("clauses_affected", 11) < len(cells) else "",
            other_aff_specs=cells[col_map.get("other_aff_specs", 12)] if col_map.get("other_aff_specs", 12) < len(cells) else "",
        )
        entries.append(entry)

    return entries


def parse_cover_sheet(cover_path: Path, release: str) -> CoverSheetData:
    """단일 Cover Sheet 파싱."""
    cr_pack_id = cr_other_wg.pack_id(cover_path)  # 슬롯의 팩 번호를 읽고 내부 포장 폴더는 제외한다.
    result = CoverSheetData(
        cr_pack_id=cr_pack_id,
        tsg_meeting="",
        release=release,
        source_path=str(cover_path.relative_to(PROJECT_ROOT)),
    )

    try:
        doc = docx_text.open_document(str(cover_path))
    except Exception as e:
        result.errors.append(f"DOCX open failed: {e}")
        return result

    # TSG Meeting 추출
    result.tsg_meeting = extract_tsg_meeting(doc)
    if not result.tsg_meeting:
        result.errors.append("TSG meeting not found in paragraphs")

    # CR 테이블 파싱
    if not doc.tables:
        result.errors.append("No tables found in cover sheet")
        return result

    # 첫 번째 테이블이 CR 목록
    entries = parse_cr_table(doc.tables[0], pack_cr_tdocs(cover_path.parent))
    for e in entries:
        if e.tdoc_number_warning:
            log.warning(f"  {cr_pack_id}: {e.tdoc_number} — {e.tdoc_number_warning}")
    result.cr_entries = [asdict(e) for e in entries]

    if not entries:
        result.errors.append("No CR entries found in table")

    return result


def cover_dir(pack_dir: Path) -> Path:
    """팩의 표지가 놓인 폴더.

    zip 이 내용 전체를 한 폴더로 감싼 채 풀린 팩은 팩 바로 아래에 파일이 없고 폴더가 하나뿐이다.
    그때 표지는 그 폴더 안에 있다. 팩 바로 아래만
    보면 표지를 못 찾아 최소 CRPack(tsgMeeting 없음)이 된다. 안쪽 zip 을 푼 폴더는 그 zip 이 옆에
    남으므로 이 경우에 걸리지 않는다. 압축 도구 잔재(`__MACOSX` · `._*`)는 세지 않는다.
    """
    entries = [e for e in pack_dir.iterdir()
               if not os_residue.classify_path(e.relative_to(pack_dir))]
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return pack_dir


def pack_dirs() -> list[tuple[Path, str]]:
    """읽을 팩 `(팩 디렉토리, 디렉토리 Release)`. Release → 팩 순서.

    자기 슬롯의 팩 다음에 이 WG 의 CR 이 놓인 다른 WG 슬롯의 팩(`cr_other_wg.foreign_packs`)을 더한다.
    그 팩의 표지는 이 WG 슬롯에 없어서, 더하지 않으면 그 CR 의 CRPack 이 `tsgMeeting` 없이 만들어진다.
    표의 행과 파일 이름은 이 WG 번호로 거르므로 그 팩의 다른 WG CR 은 들어오지 않는다.
    """
    own = [(p, p.parent.parent.name) for p in sorted(INPUT_DIR.glob("Rel-*/TSG/*")) if p.is_dir()]
    return own + cr_other_wg.foreign_packs("RAN2")


def collect_cover_sheets() -> list[tuple[Path, str]]:
    """Release 폴더·팩 순서로 표지를 모은다. `.doc` 표지는 슬롯에 놓인 `.docx` 변환본으로 읽는다."""
    covers = []
    for pack_dir, release in pack_dirs():
        for f in sorted(cover_dir(pack_dir).iterdir()):
            if f.name.lower().endswith("_cover.docx"):
                covers.append((f, release))
    return covers


def collect_packs_without_covers() -> list[CoverSheetData]:
    """Cover Sheet가 없는 Pack 디렉토리에서 최소 CRPack 데이터 생성.

    CR 문서는 팩 바로 아래뿐 아니라 하위 폴더에서도 모은다. Phase-0 은 팩 안의 zip 을 그 zip 옆
    같은 이름 폴더에 풀고 zip 을 남기므로, 안쪽 zip 에 든 CR 은 하위 폴더에 놓인다. 표지는 팩 바로
    아래 또는 zip 이 내용을 감싼 한 폴더 안에 놓인다(`cover_dir`). 압축 도구 잔재(`__MACOSX` · `._*`)는 건너뛴다.
    """
    # Cover가 있는 pack 목록 수집
    packs_with_cover = set()
    for pack_dir, release in pack_dirs():
        # .doc 또는 .docx cover 있으면 cover 있는 것
        has_cover = any(
            f.name.lower().endswith(("_cover.doc", "_cover.docx"))
            for f in cover_dir(pack_dir).iterdir()
        )
        if has_cover:
            packs_with_cover.add(pack_dir.name)

    # Cover 없는 pack에서 CR tdoc 수집
    results = []
    for pack_dir, release in pack_dirs():
        if pack_dir.name in packs_with_cover:
            continue

        cr_entries = []
        for f in sorted(pack_dir.rglob("*")):
            if not f.is_file() or os_residue.classify_path(f.relative_to(pack_dir)):
                continue
            if f.suffix.lower() in (".docx", ".doc"):
                m = re.search(r"(R2-\d{7})(?!\d)", f.name)
                if m and {"tdoc_number": m.group(1)} not in cr_entries:
                    cr_entries.append({"tdoc_number": m.group(1)})

        # Spec §13.1: hasCR 최소 1개. CR 엔트리 0건이면 CRPack 생성 안 함
        if not cr_entries:
            continue

        result = CoverSheetData(
            cr_pack_id=pack_dir.name,
            tsg_meeting="",
            release=release,
            source_path=str(pack_dir.relative_to(PROJECT_ROOT)),
            cr_entries=cr_entries,
            errors=["No cover sheet found - minimal CRPack from directory"],
        )
        results.append(result)
    return results


def deduplicate_by_rp(results: list[CoverSheetData]) -> list[CoverSheetData]:
    """RP번호 기준 first-seen 중복 제거 (Rel-15→19 순서)."""
    seen = {}
    for r in results:
        if r.cr_pack_id not in seen:
            seen[r.cr_pack_id] = r
    return list(seen.values())


# === 메인 ===

def main():
    configure_logging()
    log.info("=" * 60)
    log.info("RAN2 Phase-4 Step 1-1: Cover Sheet 파싱 시작")
    log.info("=" * 60)

    covers = collect_cover_sheets()
    log.info(f"Cover Sheet 발견: {len(covers)}개")

    # 병렬 파싱
    results = []
    errors_total = 0

    for result in pool_run.run_all(parse_cover_sheet, covers, 8, log):
        results.append(result)
        if result.errors:
            errors_total += 1
            log.warning(f"  {result.cr_pack_id}: {result.errors}")

    # Cover 없는 팩도 추가
    no_cover_packs = collect_packs_without_covers()
    log.info(f"Cover 없는 Pack: {len(no_cover_packs)}개")
    results.extend(no_cover_packs)

    # RP번호 first-seen 순서 유지를 위해 정렬 후 중복 제거
    results.sort(key=lambda r: r.source_path)
    unique_results = deduplicate_by_rp(results)

    # 읽은 팩이 0개면 빈 목록을 쓰지 않는다. 빈 결과가 정상 산출처럼 기존 cover_sheets.json 을
    # 덮어쓰므로 저장 전에 멈춘다.
    if not unique_results:
        log.error(f"CRPack 0개 — 입력 {INPUT_DIR} 확인. 기존 출력은 그대로 둔다")
        return 1

    # 통계 계산
    total_cr_entries = sum(len(r.cr_entries) for r in unique_results)
    total_with_meeting = sum(1 for r in unique_results if r.tsg_meeting)
    total_with_errors = sum(1 for r in unique_results if r.errors)
    total_overflow = sum(1 for r in unique_results for e in r.cr_entries if e.get("tdoc_number_warning"))

    # 릴리스별 통계
    by_release = {}
    for r in unique_results:
        by_release.setdefault(r.release, []).append(r)

    log.info("")
    log.info("=" * 60)
    log.info("파싱 결과 요약")
    log.info("=" * 60)
    log.info(f"  Cover Sheet 입력: {len(covers)}개")
    log.info(f"  Unique CRPack (RP 기준): {len(unique_results)}개")
    log.info(f"  CR 엔트리 총계: {total_cr_entries}개")
    log.info(f"  TSG Meeting 추출 성공: {total_with_meeting}/{len(unique_results)}")
    log.info(f"  에러 있는 CRPack: {total_with_errors}개")
    log.info(f"  넘친 번호를 팩의 CR 로 받은 행: {total_overflow}개")
    log.info("")
    for rel in sorted(by_release.keys()):
        packs = by_release[rel]
        crs = sum(len(p.cr_entries) for p in packs)
        log.info(f"  {rel}: {len(packs)} packs, {crs} CR entries")

    # JSON 출력
    output = {
        "metadata": {
            "total_covers_found": len(covers),
            "unique_crpacks": len(unique_results),
            "total_cr_entries": total_cr_entries,
            "tsg_meeting_found": total_with_meeting,
            "packs_with_errors": total_with_errors,
            "tdoc_number_overflow_recovered": total_overflow,
            "by_release": {
                rel: {"packs": len(packs), "cr_entries": sum(len(p.cr_entries) for p in packs)}
                for rel, packs in sorted(by_release.items())
            },
        },
        "crpacks": [asdict(r) for r in unique_results],
    }

    output_path = OUTPUT_DIR / "cover_sheets.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_text_atomic(output_path, json.dumps(output, ensure_ascii=False, indent=2))

    log.info(f"\n출력: {output_path}")
    log.info(f"파일 크기: {output_path.stat().st_size / 1024:.1f} KB")

    return 0


if __name__ == "__main__":
    sys.exit(main())
