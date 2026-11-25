"""Phase-6 기존 파싱·보강 CLI의 단일 TDoc 선택 조건.

Spec: docs/tsg/RAN/formal/RAN1/phase-6/design-spec/tdoc_vectordb_specs(Tdoc).md
Ontology: 회의와 WG 안에서 원래 tdocNumber를 그대로 선택한다.
Cycle: 명시한 회의·번호 확인 → 소유권 판정 → 선택 문서의 파싱·보강.
배경: 문서 수 제한과 특정 문서 선택을 구분하고 비대상 산출물을 보존한다.
사용: 기존 03~07 CLI의 --tdoc와 collect_tasks가 공통으로 호출한다.
LLM 호출: 없음.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

_SCRIPTS_COMMON = Path(__file__).resolve().parents[4] / "common"
if str(_SCRIPTS_COMMON) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_COMMON))
from common.tdoc_number import tdoc_number_of


class TdocSelectionError(ValueError):
    """명시한 단일 문서의 범위나 필수 입력이 유효하지 않다."""


def add_argument(parser) -> None:
    parser.add_argument(
        "--tdoc", metavar="TDOC_NUMBER",
        help="지정한 회의에서 이 TDoc 번호만 처리 (회의 지정 필수; --limit와 별개)",
    )


def _component(value: str) -> bool:
    return bool(value) and value not in {".", ".."} and not any(
        char in value for char in ("/", "\\", "\x00", "\r", "\n")
    )


def validate_scope(wg: str, tdoc: str | None, meeting: str | None,
                   *, meeting_prefix: str | None = None) -> str | None:
    """선택 번호를 정규화하고 단일 회의·WG 범위를 검사한다. 선택이 없으면 기존 범위를 유지한다."""
    if tdoc is None:
        return None
    if not re.fullmatch(r"RAN[1-5]", wg):
        raise TdocSelectionError("--tdoc는 RAN1~RAN5에서 지원합니다")
    number = tdoc_number_of(tdoc)
    # 접미사가 있는 실제 첨부 문서 번호는 유지한다. 숫자 자리 수로 과거 회의를 배제하지 않는다.
    if not _component(number) or not re.fullmatch(rf"R{wg[-1]}-\d+[^/\\\r\n]*", number):
        raise TdocSelectionError(f"--tdoc 번호가 {wg}와 일치하지 않거나 유효하지 않습니다: {tdoc!r}")
    if not isinstance(meeting, str) or not _component(meeting) or "," in meeting:
        raise TdocSelectionError("--tdoc에는 회의 한 개를 함께 지정해야 합니다")
    prefix = meeting_prefix if meeting_prefix is not None else f"{wg}#"
    if not prefix or not meeting.startswith(prefix) or meeting == prefix:
        raise TdocSelectionError(f"--tdoc의 회의가 {wg} 범위와 일치하지 않습니다: {meeting!r}")
    return number


def validate_arguments(parser, args, *, wg: str, meeting_prefix: str | None = None) -> None:
    """파일·서비스에 접근하기 전에 CLI의 한정 조건을 확인한다."""
    meeting = getattr(args, "meetings", None) if meeting_prefix is not None else args.meeting
    try:
        args.tdoc = validate_scope(getattr(args, "wg", wg), args.tdoc, meeting, meeting_prefix=meeting_prefix)
        if args.tdoc is not None and getattr(args, "test", False):
            raise TdocSelectionError("--tdoc와 --test는 함께 사용할 수 없습니다")
    except TdocSelectionError as error:
        parser.error(str(error))


def collect_or_error(parser, collect_tasks, *args, **kwargs):
    """입력 선택 오류를 기존 CLI의 사용 오류로 보고한다. 작업 자체의 실패는 그대로 전달한다."""
    try:
        return collect_tasks(*args, **kwargs)
    except TdocSelectionError as error:
        parser.error(str(error))


def parsed_target(parsed_base: Path, wg: str, meeting: str | None,
                  tdoc: str | None) -> str | None:
    """04~07은 선택 문서의 03 산출물이 있을 때만 진행한다. 그림·수식이 없는 문서도 유효하다."""
    selected = validate_scope(wg, tdoc, meeting)
    if selected is not None:
        directory = parsed_base / meeting / selected
        if not directory.is_dir():
            raise TdocSelectionError(f"선택한 TDoc 파싱 폴더가 없습니다: {meeting}/{selected}")
        if not (directory / "chunks.json").is_file():
            raise TdocSelectionError(f"선택한 TDoc의 chunks.json이 없습니다. 03 파싱을 먼저 실행하세요: {meeting}/{selected}")
    return selected


def require_found(tdoc: str | None, found: bool, meeting: str) -> None:
    if tdoc is not None and not found:
        raise TdocSelectionError(
            f"선택한 TDoc의 유효한 Word 입력이 없습니다: {meeting}/{tdoc}. "
            "회의·번호·DOCX 변환 결과와 문서 소유권 제외 내역을 확인하세요."
        )
