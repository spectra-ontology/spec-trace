#!/usr/bin/env python3
"""
RAN5 Phase-4 Step 1: CR 문서 파싱 (통합 스크립트)
- 입력: data/corpus/tsg/RAN/formal/change-requests/RAN5/derived/Rel-*/TSG/{팩}/ — cr_inputs 가 모은다(표지 제외)
- 출력: ontology/output/tsg/RAN/formal/parsed_cr/RAN5/cr_documents.json
        ontology/output/tsg/RAN/formal/parsed_cr/RAN5/crpacks.json
        ontology/output/tsg/RAN/formal/parsed_cr/RAN5/parse_summary.json

Spec §1.4: CR 메타데이터는 CR 문서 안의 CR-Form 에서 읽는다. 팩 커버(`RP-NNNNNN_cover.docx`)는
CR 이 아니므로 CR 로 수집하지 않고, CRPack.tsgMeeting 의 출처로만 쓴다.
Spec §1.6: R5-\\d{6} (6자리), 전부 .docx (원본), .doc→.docx 변환본 포함
입력 문서가 수만 건이라 프로세스 풀(pool_run) + Resume 로직
"""

import hashlib
import json
import re
import sys
import logging
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path

from docx import Document

# === 경로 설정 ===
PROJECT_ROOT = Path(__file__).resolve().parents[7]
_SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "common"))
from common.atomic_io import publish_text_set, write_text_atomic  # noqa: E402
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "tsg" / "RAN" / "formal" / "common"))
import docx_text  # noqa: E402 — 문단 · 표 칸 읽기 규칙(변경 표시 · 필드 안의 글까지)
import pool_run  # noqa: E402 — 워커가 죽어도 항목을 잃지 않는 풀
import cr_form  # noqa: E402 — CR 서식 머리행의 Spec 번호
import cr_word_title  # noqa: E402 — LibreOffice 변환본의 표지 제목을 원본 .doc 글로 읽는다
import cr_form_slot  # noqa: E402 — CR 서식 본문 네 칸을 이름 칸이 망가져도 서식 틀의 자리로 읽는다
import cr_inputs  # noqa: E402 — Phase-0 산출 슬롯에서 CR 문서를 모으는 규칙
import os_residue  # noqa: E402 — 압축 도구가 남긴 잔재 이름(cr_inputs 가 경로를 더한 공용 모듈)
import tsg_cr_decision  # noqa: E402 — TSG 회의가 팩 안 CR 마다 내린 판정
import cr_attachments  # noqa: E402 — 팩 안 CR 폴더에 든 첨부 문서 가리기
import cr_other_wg  # noqa: E402  (다른 WG 슬롯에 놓인 이 WG 의 CR · 이 슬롯에 놓인 다른 WG 의 CR)
import cr_unopenable  # noqa: E402 — 열 수 없다고 확인해 둔 CR 문서 목록과 오류 가르기
WG = "RAN5"
INPUT_DIR = cr_inputs.derived_dir(WG)
OUTPUT_DIR = PROJECT_ROOT / "ontology" / "output" / "tsg" / "RAN" / "formal" / "parsed_cr" / "RAN5"
LOG_DIR = PROJECT_ROOT / "logs" / "tsg" / "RAN" / "formal" / "RAN5" / "phase-4"
RESUME_FILE = LOG_DIR / "01_resume_state.json"

log = logging.getLogger(__name__)


def setup_output_and_logging() -> None:
    """디렉토리 생성 + 로깅 설정. 실행 진입점에서만 호출한다.

    모듈 import 만으로 로그 파일이 mode="w" 로 잘리고 루트 로거가 재설정되면,
    Spec 참조 게이트(classify_spec_ref) 같은 순수 함수를 다른 스크립트에서
    재사용할 수 없다. 부작용을 main() 안으로 옮겨 재사용 가능하게 한다.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_DIR / "01_parse_cr_documents.log", mode="w"),
        ],
    )

# 대용량 처리 — 배치 크기 (Spec Step 7 §2 대용량 처리 전략, 값은 phase-4 step1_cr_parsing.md 「Stage 1-9」)
BATCH_SIZE = 2000
MAX_WORKERS = 8


# === 데이터 모델 ===
@dataclass
class CRDocumentData:
    tdoc_number: str
    cr_pack_id: str
    release: str
    spec_number: str | None = None
    cr_number: str | None = None
    rev: str | None = None
    title: str | None = None
    category: str | None = None
    work_item: str | None = None
    reason_for_change: str | None = None
    summary_of_change: str | None = None
    consequences_if_not_approved: str | None = None
    clauses_affected: str | None = None
    affects_core_spec: list = field(default_factory=list)
    affects_test_spec: list = field(default_factory=list)
    affects_om_spec: list = field(default_factory=list)
    rejected_spec_refs: list = field(default_factory=list)
    source_path: str = ""
    errors: list = field(default_factory=list)
    tsg_number: str | None = None
    tsg_revision_of: str | None = None


# === tdocNumber 추출 (R5-NNNNNN, 6자리) ===

# 근본 원칙: 이 CR 자신의 제출번호(TD#)는 파일명 또는
# 커버 헤더 문단에서만 추출한다. CR Form Table 셀(Reason/Summary/Other comments
# prose)에 등장하는 R5- 토큰은 *다른* CR 에 대한 *참조*이므로 자기 번호로 쓰면
# 오노드 MERGE → instantiation 통계 오염. python-docx 의 doc.paragraphs(본문 문단)
# 와 doc.tables(폼 셀)는 분리 스트림이라 문단만 보면 참조 오염이 구조적으로 차단됨.
# RAN5 고유: R5s 는 TTCN/test-suite 별도 제출 namespace(R5sNNNNNN, 별도 키 보존,
# 대시 변환 금지). 기존 R5-\d{6} 정규식이 R5s 를 못 잡아 132건 오키잉 + 다수 누락 →
# R5s 인식 + 언더스코어(R5_NNNNNN) 정규화로 복구.
# 근거: DROP 케이스는 전부 CR Form Table 단독 출현(=참조); R5s 는 파일명 namespace.
# 번호 뒤에 숫자가 이어지면 번호가 아니다(파일명 오타 `R5-2474883` 을 `R5-247488` 로 잘라 남의 번호를 받는다).
_TDOC_RE = re.compile(r"(R5s\s?\d{6}|R5[-_]\d{6})(?!\d)")
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
    """R5_190019 → R5-190019 정규화. R5s 는 별도 namespace 라 그대로 보존."""
    tok = tok.replace(" ", "")
    if "R5s" in tok:
        return tok
    return tok.replace("_", "-")


def extract_tdoc_from_filename(filename: str) -> str | None:
    """파일명에서 이 CR 자신의 TD#(R5-NNNNNN/R5sNNNNNN, 6자리) 추출. Spec §1.6

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


def extract_cr_number_from_filename(filename: str) -> tuple[str | None, str | None]:
    """파일명에서 CR 번호와 개정 추출 (예: CR0615 → ("0615", None), CR1532r1 → ("1532", "1")).

    CR 번호는 숫자만 둔다. Phase-1 이 Tdoc 목록에서 적재하는 `crNumber` 가 숫자만이고 개정은 `crRevision`
    으로 따로 두며, RAN1~4 의 CR 기록도 `cr_number` 와 `rev` 를 가른다. 개정을 번호에 붙이면 같은 CR 의 두
    출처가 문자열로 맞지 않는다.
    """
    m = re.search(r"_CR(\d+)(?:r(\d+))?", filename, re.IGNORECASE)
    if m:
        return m.group(1), m.group(2)
    return None, None


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


# === Spec 참조 유효성 게이트 ===
#
# 커버시트 "Other specs affected" 칸은 자유 서술이라 작성자 오타가 그대로 들어온다.
# 추출 정규식 \d{2}\.\d{3}(-\d+)? 는 모양만 보므로 39.903 / 58.521-2 처럼 존재하지
# 않는 번호도 통과했고, loader 가 그 토큰을 그대로 Spec 노드로 MERGE 해서 그래프에
# 유령 허브가 생겼다. 두 게이트로 거른다.
#
#   게이트 1 (구문) — 3GPP 명세 번호 체계에서 실제 할당된 시리즈만 통과.
#                     39·40·53·54·56·57·58 은 미할당이라 무조건 기각.
#   게이트 2 (실증) — 저장소가 실제로 아는 spec 집합에 대조. 코퍼스 디렉토리명,
#                     전 WG Phase-1 specs.jsonld, spec_titles.json 의 합집합.
#                     multi-part(X.YYY-N)가 하나라도 확증되면 커버시트 관행상
#                     part 를 뗀 family root X.YYY 도 유효로 인정한다.
#
# 실증 소스가 하나도 없는 환경(코퍼스 미전개)에서는 게이트 2 를 자동 비활성화한다.
# 모르는 것을 근거로 전부 기각하는 쪽이 더 나쁜 실패이기 때문이다.

_ALLOCATED_SPEC_SERIES = frozenset(
    [f"{n:02d}" for n in range(1, 14)]     # 01~13 GSM 계열
    + [f"{n:02d}" for n in range(21, 39)]  # 21~38 3G/LTE/NR
    + [f"{n:02d}" for n in range(41, 53)]  # 41~52
    + ["55"]                               # 55 보안 알고리즘 문서
)

_SPEC_NUM_RE = re.compile(r"^(\d{2})\.(\d{3})(?:-(\d+))?$")

_SPEC_UNIVERSE: frozenset | None = None


def _spec_universe() -> frozenset:
    """저장소가 실증하는 spec 번호 집합. 프로세스당 1회만 구성."""
    global _SPEC_UNIVERSE
    if _SPEC_UNIVERSE is not None:
        return _SPEC_UNIVERSE

    known: set[str] = set()

    # 슬롯은 WG 뒤에 오므로 spec 디렉토리는 `{doctype}/{WG}/{slot}/{spec}` 에 있다
    corpus_base = PROJECT_ROOT / "data" / "corpus" / "tsg" / "RAN" / "formal"
    for kind in ("TS", "TR"):
        kind_dir = corpus_base / kind
        if not kind_dir.is_dir():
            continue
        for wg_dir in kind_dir.iterdir():
            if not wg_dir.is_dir():
                continue
            for slot in ("source", "derived"):
                slot_dir = wg_dir / slot
                if not slot_dir.is_dir():
                    continue
                for spec_dir in slot_dir.iterdir():
                    if spec_dir.is_dir() and _SPEC_NUM_RE.match(spec_dir.name):
                        known.add(spec_dir.name)

    phase1_dir = PROJECT_ROOT / "ontology" / "output" / "tsg" / "RAN" / "formal" / "instances" / "phase-1"
    if phase1_dir.is_dir():
        for jsonld in sorted(phase1_dir.glob("*/specs.jsonld")):
            # 읽히지 않는 원본 자료를 건너뛰면 우주가 조용히 줄어 실재 번호가 unattested 로 기각된다.
            # 그 판정을 따르는 정리 스크립트는 실재 허브를 지우므로 여기서 멈춘다.
            try:
                payload = json.loads(jsonld.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise RuntimeError(f"규격 목록의 원본 자료를 읽지 못함: {jsonld.name}") from exc
            # 읽혔어도 목록 키가 없거나 형태가 다르면 기여가 0 으로 줄어드는 같은 실패다.
            graph = payload.get("@graph") if isinstance(payload, dict) else None
            if not isinstance(graph, list):
                raise RuntimeError(f"규격 목록 원본의 @graph 가 목록이 아님: {jsonld.name}")
            for item in graph:
                num = item.get("tdoc:specNumber")
                if isinstance(num, str) and _SPEC_NUM_RE.match(num):
                    known.add(num)

    titles_path = PROJECT_ROOT / "ontology" / "input" / "spec_titles.json"
    if titles_path.is_file():
        try:
            payload = json.loads(titles_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise RuntimeError(f"규격 목록의 원본 자료를 읽지 못함: {titles_path.name}") from exc
        specs = payload.get("specs") if isinstance(payload, dict) else None
        if not isinstance(specs, dict):
            raise RuntimeError(f"규격 목록 원본의 specs 가 사전이 아님: {titles_path.name}")
        for num in specs:
            if _SPEC_NUM_RE.match(num):
                known.add(num)

    # family root 확장: 38.101-1 이 확증되면 38.101 도 유효 참조로 받아들인다.
    known |= {n.split("-", 1)[0] for n in known if "-" in n}

    _SPEC_UNIVERSE = frozenset(known)
    return _SPEC_UNIVERSE


def classify_spec_ref(ref: str) -> str | None:
    """유효하면 None, 기각이면 사유 문자열('series' | 'unattested')."""
    m = _SPEC_NUM_RE.match(ref)
    if not m:
        return "malformed"
    if m.group(1) not in _ALLOCATED_SPEC_SERIES:
        return "series"
    universe = _spec_universe()
    if universe and ref not in universe:
        return "unattested"
    return None


def validate_spec_refs(refs: list, field_name: str) -> tuple[list, list]:
    """(통과 목록, 기각 기록 목록) 반환. 기각은 버리지 않고 사유와 함께 남긴다."""
    accepted, rejected = [], []
    for ref in refs:
        reason = classify_spec_ref(ref)
        if reason is None:
            accepted.append(ref)
        else:
            rejected.append({"ref": ref, "field": field_name, "reason": reason})
    return accepted, rejected


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
    """단일 CR 문서 파싱. Spec §1.4: Cover Sheet + CR 본문 단일 파일."""
    cr_pack_id = cr_other_wg.pack_id(cr_path) if source_pack_id is None else source_pack_id

    tdoc_number = extract_tdoc_from_filename(cr_path.name)
    spec_number = cr_form.filename_spec(cr_path.name)
    cr_number, cr_rev = extract_cr_number_from_filename(cr_path.name)
    fname_release = extract_release_from_filename(cr_path.name)

    result = CRDocumentData(
        tdoc_number=tdoc_number or "",
        cr_pack_id=cr_pack_id,
        release=fname_release or release,
        spec_number=spec_number,
        cr_number=cr_number,
        rev=cr_rev,
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

    # 파일명 `(Rel-N)` 토큰이 없으면 CR Form `Release:` 필드로 보정
    if not fname_release and cr_table is not None:
        form_release = extract_release_from_cr_form(cr_table)
        if form_release:
            result.release = form_release

    # 파일명에서 R5를 못 찾은 경우 문서 내부 검색
    if not result.tdoc_number:
        result.tdoc_number = extract_tdoc_from_document(
            doc, has_cr_form=cr_table is not None, filename=cr_path.name) or ""
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

    if not result.spec_number:
        result.spec_number = cr_form.header_spec(doc)

    # 주의: CR 번호는 파일 이름(`_CR0379r1`)을 먼저 쓰고, 이름에 번호가 없을 때만 서식 머리의 CR · rev 칸으로
    # 채운다. `R5-183717_NB_IOT_36.903_6.2.18.docx` 처럼 이름에 번호를 적지 않은 CR 이 있고, 그 CR 의 모든
    # 사본이 그런 이름이면 이 자리 말고는 번호를 얻지 못해 Phase-8 청크의 crNumber 가 빈다. 서식을 앞세우지
    # 않는 것은 서식 칸이 틀린 문서가 있어서다(`R5-197579` 는 이름이 CR0111r1, 서식 칸이 `01110267`).
    # 개정은 번호에 붙이지 않고 `rev` 에 둔다. 숫자이고 0 이 아닐 때만 적고, rev 칸이 비면 `correct_revision`
    # 이 시트 개정으로 채운다.
    form = cr_form.form_fields(doc)
    if not result.cr_number:
        if form.get("cr_number"):
            rev = form.get("rev", "")
            result.cr_number = form["cr_number"]
            result.rev = rev if rev.isdigit() and rev != "0" else None
    # 서식의 제목 · 분류 · 작업 항목. Phase-1 Tdoc List 가 다루지 않는 CR 은 Phase-4 적재기가 이 값으로
    # 제목과 MODIFIES · RELATED_TO 를 채운다(`cr_backfill_form`). 이 칸이 없으면 그 CR 은 spec · 작업
    # 항목으로 찾는 질의에서 빠지고, Phase-8 청크의 제목 · 작업 항목도 빈다.
    for key in ("title", "category", "work_item"):
        if form.get(key):
            setattr(result, key, form[key])
    # 주의: LibreOffice 변환본의 제목은 원본 .doc 이 보여 주는 Title 칸 글로 바로잡는다(`cr_word_title`).
    result.title = cr_word_title.form_title(result.title, cr_path)
    # 주의: 작업 항목 칸의 같은 잔재는 원본 칸에 결과가 빈 필드나 겹친 필드가 있는 경우에만 바로잡는다(`cr_word_title.form_work_item`).
    result.work_item = cr_word_title.form_work_item(result.work_item, cr_path)

    # 필드 추출
    result.reason_for_change = cr_form_slot.form_value(cr_table, "reason for change")
    result.summary_of_change = cr_form_slot.form_value(cr_table, "summary of change")
    result.consequences_if_not_approved = cr_form_slot.form_value(cr_table, "consequences if not approved")

    clauses = cr_form_slot.form_value(cr_table, "clauses affected")
    if clauses:
        result.clauses_affected = clauses

    # Cross-Spec 영향 (Spec §4.3)
    core, test, om = extract_other_specs(cr_table)
    rejected: list = []
    for raw_refs, field_name in ((core, "core"), (test, "test"), (om, "om")):
        accepted, bad = validate_spec_refs(raw_refs, field_name)
        raw_refs[:] = accepted
        rejected.extend(bad)
    result.affects_core_spec = core
    result.affects_test_spec = test
    result.affects_om_spec = om
    result.rejected_spec_refs = rejected

    return result


# === 파일 수집 ===

# 팩 커버. 원본 zip 에는 `.doc` 로 들어 있고 슬롯에 변환본 `.docx` 가 옆에 있다.
_PACK_COVER_RE = re.compile(r"^(RP-\d+)_cover\.docx$", re.IGNORECASE)
# 커버 첫 문단의 "3GPP TSG-RAN Meeting #101" → "RAN#101". RAN1~4 커버 파서와 같은 규칙이다.
_TSG_MEETING_RE = re.compile(r"(?:TSG[- ]?)?RAN\s*(?:Meeting\s*)?#(\d+)", re.IGNORECASE)


def cover_dir(pack_dir: Path) -> Path:
    """팩의 커버가 놓인 폴더.

    zip 이 내용 전체를 한 폴더로 감싼 채 풀린 팩은 팩 바로 아래에 파일이 없고 폴더가 하나뿐이고,
    커버는 그 폴더 안에 있다(RAN4 RP-201501 이 그 예다. RAN5 슬롯에는 현재 0건). 안쪽 zip 을 푼
    폴더는 그 zip 이 옆에 남으므로 이 경우에 걸리지 않는다. 압축 도구 잔재는 세지 않는다.
    """
    entries = [e for e in pack_dir.iterdir()
               if not os_residue.classify_path(e.relative_to(pack_dir))]
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return pack_dir


def collect_pack_covers() -> dict[str, list[Path]]:
    """crPackId → 팩 커버 경로들 (같은 팩이 여러 Release 폴더에 놓일 수 있다)."""
    covers: dict[str, list[Path]] = defaultdict(list)
    own = [p for p in sorted(INPUT_DIR.glob("Rel-*/TSG/*")) if p.is_dir()]
    for pack_dir in own + [p for p, _ in cr_other_wg.foreign_packs(WG)]:
        for f in sorted(cover_dir(pack_dir).iterdir()):
            m = _PACK_COVER_RE.match(f.name)
            if m and m.group(1) == pack_dir.name:
                covers[m.group(1)].append(f)
    return covers


def extract_tsg_meeting(cover_path: Path) -> str | None:
    """팩 커버 앞 다섯 문단에서 TSG 회의 번호를 읽는다. 못 읽으면 None."""
    doc = docx_text.open_document(str(cover_path))
    for p in doc.paragraphs[:5]:
        m = _TSG_MEETING_RE.search(docx_text.final_text(p))
        if m:
            return f"RAN#{m.group(1)}"
    return None


def collect_cr_documents() -> list[tuple[Path, str]]:
    """CR 문서 `(경로, 디렉토리 Release)` 목록. 모으는 규칙은 `cr_inputs` 이고 여기서는 팩 커버만 뺀다.

    팩 커버는 `_cover.docx` 접미로만 가른다(`Coverage` 가 든 CR 이름을 잘못 빼지 않게).
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
    파일이 놓인 슬롯을 기준으로 읽는다. 다른 슬롯의 팩 커버도 `collect_pack_covers` 가 읽는다.
    """
    files, unconverted, _ = cr_other_wg.collect(WG)
    cr_docs = [(f, release) for f, release in files if not f.name.lower().endswith("_cover.docx")]
    log.info(f"  CR 문서 {len(cr_docs)}개 · 팩 커버 제외 {len(files) - len(cr_docs)}개")
    if unconverted:
        log.warning(f"  읽을 수 없는 문서(변환본 없는 .doc · ZIP 아닌 .docx) {len(unconverted)}개 — 열기 실패 기록으로 남김(산출 메타데이터 `unconverted_doc`)")
    cr_docs += [(f, cr_other_wg.release(f)) for f in unconverted
                if not f.name.lower().endswith("_cover.docx")]
    return cr_docs


def cover_tdocs(cover_path: Path) -> set[str]:
    """팩 커버의 문단 · 표 칸이 적은 WG 번호."""
    doc = docx_text.open_document(str(cover_path))
    lines = [docx_text.final_text(p) for p in doc.paragraphs]
    for tbl in docx_text.iter_tables(doc):
        lines.extend(docx_text.table_line_rows(tbl))
    return {_norm_tdoc(m.group(1)) for text in lines for m in _TDOC_RE.finditer(text)}


def cover_listed(results: list[CRDocumentData]) -> set[tuple[str, str]]:
    """둘 이상의 팩 폴더에 놓인 tdoc 의 (팩, tdoc) 가운데 그 팩 커버가 적은 것.

    한 팩에만 놓인 tdoc 은 고를 것이 없어 커버를 열지 않는다.
    """
    packs: dict[str, set[str]] = defaultdict(set)
    for r in results:
        if r.tdoc_number and r.cr_pack_id:
            packs[r.tdoc_number].add(r.cr_pack_id)
    shared = {t: s for t, s in packs.items() if len(s) > 1}
    covers = collect_pack_covers()
    listed = set()
    for pack in sorted(set().union(*shared.values()) if shared else ()):
        named = set()
        for cover in covers.get(pack, []):
            try:
                named |= cover_tdocs(cover)
            except Exception as e:
                log.warning(f"  커버 읽기 실패 {cover.relative_to(PROJECT_ROOT)}: {e}")
        listed |= {(pack, t) for t in named if pack in shared.get(t, ())}
    return listed


def deduplicate_by_tdoc(results: list[CRDocumentData],
                        listed: set[tuple[str, str]] = frozenset()) -> list[CRDocumentData]:
    """tdocNumber 마다 기록 하나. 오류 없는 기록, TSG 회의 판정이 앞서는 팩의 기록, 팩 커버가 적은 기록,
    경로 순서의 첫 기록 차례로 고른다.

    같은 CR 이 여러 Release 폴더 · 팩에 다시 배포된다. 경로 순서만으로 고르면 열리지 않거나
    서식이 없는 사본이 먼저 와서 읽힌 사본을 가린다.

    주의: 같은 CR 이 두 팩 폴더에 놓이고 한 팩의 커버만 그 CR 을 적으면, 경로 순서로는 커버가
    적지 않은 팩이 이길 수 있다. RAN#87e 에서 승인된 RP-200065 · RP-200066 가운데 R5-201240 을
    적은 커버는 RP-200066 이고 그 파일은 두 폴더에 함께 있다. 커버가 적지 않은 팩을 고르면 CR 이
    다른 팩에 소속된다. 커버만으로는 가르지 못하는 곳도 있다. RAN#100 의 RP-230979 커버는 RP-230977 ·
    RP-230978 의 CR 들을 함께 적는다. 그래서 TSG 회의 TDoc 목록의 판정 순위(`tsg_cr_decision.rank`)가
    앞서는 팩의 사본을 먼저 고른다. 그 CR 시트는 R5-201240 을 RP-200066 에만, RAN#100 의 CR 들을
    RP-230977 · RP-230978 에만 `approved` 로 둔다. 순위가 같으면(TDoc 목록이 없는 RAN#111 · RAN#112)
    커버가 그 tdoc 을 적은 사본(`cover_listed`)을 고른다.
    """
    seen = {}
    for r in sorted(results, key=lambda r: (bool(r.errors), tsg_cr_decision.rank(r.tdoc_number, r.cr_pack_id),
                                            (r.cr_pack_id, r.tdoc_number) not in listed, r.source_path)):
        if r.tdoc_number and r.tdoc_number not in seen:
            seen[r.tdoc_number] = r
    return sorted(seen.values(), key=lambda r: r.source_path)


# === Resume 로직 ===

def input_fingerprint(cr_docs: list[tuple[Path, str]]) -> str:
    """재개 상태를 묶는 지문 — 배치 크기 · 파서와 저장소 안에서 import 한 모듈의 원문 · 입력 경로 · Release · 파일 내용.
    Spec 참조 판정에 쓰는 spec 번호 집합도 넣는다.

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
    h.update("\n".join(sorted(_spec_universe())).encode())
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
    write_text_atomic(partial_path, json.dumps(data, ensure_ascii=False, indent=2))
    return partial_path


def cleanup_partial_files():
    """부분 결과 파일 삭제."""
    for partial in OUTPUT_DIR.glob("cr_documents_batch_*.json"):
        partial.unlink()
    if RESUME_FILE.exists():
        RESUME_FILE.unlink()


# === CRPack 집계 ===

def build_crpacks(results: list[CRDocumentData]) -> tuple[list[dict], dict]:
    """CRPack 집계: crPackId → {tsgMeeting, tdocNumbers}.
    tsgMeeting 은 팩 커버에서 읽는다. 커버가 없거나 회의 번호를 못 읽은 팩은 None 으로 두고
    그 수를 통계로 돌려준다 — 빈칸을 추정값으로 메우지 않는다.
    """
    covers = collect_pack_covers()
    stats = {"with_cover": 0, "no_cover": [], "unreadable": [], "conflict": {}}
    packs = defaultdict(lambda: {"tdoc_numbers": [], "release_set": set()})
    for r in results:
        if not r.cr_pack_id or not r.tdoc_number:
            continue
        pack = packs[r.cr_pack_id]
        pack["tdoc_numbers"].append(r.tdoc_number)
        pack["release_set"].add(r.release)

    crpacks = []
    for pack_id, info in sorted(packs.items()):
        meetings = set()
        for cover in covers.get(pack_id, []):
            try:
                meeting = extract_tsg_meeting(cover)
            except Exception as e:
                log.warning(f"  커버 읽기 실패 {cover.relative_to(PROJECT_ROOT)}: {e}")
                meeting = None
            if meeting:
                meetings.add(meeting)
        if not covers.get(pack_id):
            stats["no_cover"].append(pack_id)
        elif not meetings:
            stats["unreadable"].append(pack_id)
        elif len(meetings) > 1:
            stats["conflict"][pack_id] = sorted(meetings)
        else:
            stats["with_cover"] += 1
        crpacks.append({
            "crPackId": pack_id,
            "tsgMeeting": meetings.pop() if len(meetings) == 1 else None,
            "tdocNumbers": sorted(info["tdoc_numbers"]),
            "releases": sorted(info["release_set"]),
            "crCount": len(info["tdoc_numbers"]),
        })
    return crpacks, stats


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


def correct_revision(results: list[CRDocumentData], identity_fixes: dict[str, dict[str, list]]) -> None:
    """CR 시트의 개정으로 `rev` 를 채우거나 고친다. 고친 쌍은 `identity_fixes[tdoc]["rev"]` 에 [읽은 값, 시트 값] 으로 적는다.

    규칙은 `tsg_cr_decision.correct_identity` 가 번호를 맞춘 뒤 개정에 적용한다.
    1. 번호를 시트 값으로 고친 CR 은 개정도 시트 값으로 둔다. 번호가 틀린 파일 이름은 개정도 믿을 수 없어서다
       (`tsg_cr_decision.sheet_cr_label` 의 개정 주의).
    2. 번호가 시트와 같고 기록에 개정이 없으며 시트 개정이 0 이 아닌 숫자면 시트 개정을 적는다. 문서가 개정을
       적지 않은 경우다. `R5-192504` · `R5-225616` 은 파일 이름에 번호가 없고 서식 머리의 rev 칸이 비며,
       `R5-237956` 은 파일 이름이 `CR0626` 이라 개정을 적지 않는다. 세 문서 모두 시트와 Phase-1 Tdoc 목록이
       개정 1 이다.
    3. 기록에 개정이 있으면 시트와 달라도 둔다. 문서가 적은 개정을 바꾸지 않는다.

    시트 개정은 숫자이고 0 이 아닐 때만 쓴다. 기록의 `rev` 도 같은 규칙으로 적어 두 값이 같은 표기를 쓴다.
    """
    for r in results:
        if not r.tdoc_number:
            continue
        reg = tsg_cr_decision.identity(r.tdoc_number, r.cr_pack_id or "")
        if reg is None or not reg["cr"]:
            continue
        sheet_rev = reg["rev"] if reg["rev"].isdigit() and reg["rev"] != "0" else None
        fixed = identity_fixes.get(r.tdoc_number, {})
        if "cr_number" in fixed:
            new = sheet_rev
        elif r.cr_number and not r.rev and sheet_rev:
            new = sheet_rev
        else:
            continue
        if new != r.rev:
            identity_fixes.setdefault(r.tdoc_number, {})["rev"] = [r.rev, new]
            r.rev = new


def cr_record(r: CRDocumentData) -> dict:
    """CR 기록. `tsg_*` 는 빠진 문서에만 쓰이므로 기록에 싣지 않는다."""
    d = asdict(r)
    d.pop("tsg_number")
    d.pop("tsg_revision_of")
    return d


# === 메인 ===

def main():
    setup_output_and_logging()
    log.info("=" * 60)
    log.info("RAN5 Phase-4 Step 1: CR 문서 파싱 시작")
    log.info("=" * 60)

    cr_docs = collect_cr_documents()
    _, unconverted_paths, other_wg = cr_other_wg.collect(WG)
    unconverted = [str(p.relative_to(PROJECT_ROOT)) for p in unconverted_paths]
    log.info(f"CR 문서 발견: {len(cr_docs)}개")

    if not cr_docs:
        log.error("CR 문서를 찾을 수 없습니다.")
        return 1

    # 배치 처리 (Resume 지원)
    all_results: list[CRDocumentData] = []
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
            # 이전 배치 결과 로드
            for bi in range(start_batch):
                partial_path = OUTPUT_DIR / f"cr_documents_batch_{bi:03d}.json"
                if not partial_path.exists():
                    raise FileNotFoundError(f"재개할 앞 배치 결과가 없음: {partial_path} — Resume 파일을 지우고 처음부터 돌릴 것")
                with open(partial_path, encoding="utf-8") as f:
                    all_results.extend(CRDocumentData(**d) for d in json.load(f))

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
    unique_results = deduplicate_by_tdoc(all_results, cover_listed(all_results))
    # 파일 이름 · 서식이 적은 Spec · CR 번호 · Release 를 TSG 회의 CR 시트 값으로 맞춘다(`tsg_cr_decision.correct_identity`).
    identity_fixes, identity_unlisted, identity_kept_spec = tsg_cr_decision.correct_identity(unique_results)
    correct_revision(unique_results, identity_fixes)
    identity_fixes = dict(sorted(identity_fixes.items()))
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

    rejected_refs = defaultdict(int)
    for r in unique_results:
        for bad in r.rejected_spec_refs:
            rejected_refs[(bad["ref"], bad["reason"])] += 1

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
    log.info(f"  기각된 Spec 참조: {sum(rejected_refs.values())}건 / 고유 {len(rejected_refs)}개")
    for (ref, reason), cnt in sorted(rejected_refs.items(), key=lambda kv: -kv[1]):
        log.info(f"    {ref} ({reason}): {cnt}")

    if no_tdoc:
        log.warning("\n  tdocNumber 추출 실패 파일:")
        for r in no_tdoc[:20]:
            log.warning(f"    {r.source_path}: {r.errors}")

    # --- 출력 1: cr_documents.json ---
    cr_output = {
        "metadata": {
            "total_cr_docs_found": len(cr_docs),
            "unique_crs": len(unique_results),
            "duplicates_removed": len(all_results) - len(no_tdoc) - len(unique_results),
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
            "unconverted_doc": unconverted,
            "rejected_spec_refs": {
                "occurrences": sum(rejected_refs.values()),
                "distinct": len(rejected_refs),
                "by_ref": {f"{ref} ({reason})": cnt
                           for (ref, reason), cnt in sorted(rejected_refs.items())},
            },
        },
        "documents": [cr_record(r) for r in unique_results],
    }

    cr_output_path = OUTPUT_DIR / "cr_documents.json"

    # --- 출력 2: crpacks.json ---
    crpacks, tsg_stats = build_crpacks(unique_results)
    crpacks_output = {
        "metadata": {
            "total_packs": len(crpacks),
            "total_crs_in_packs": sum(p["crCount"] for p in crpacks),
            "tsg_meeting": {
                "filled": tsg_stats["with_cover"],
                "no_cover": tsg_stats["no_cover"],
                "unreadable": tsg_stats["unreadable"],
                "conflict": tsg_stats["conflict"],
            },
        },
        "packs": crpacks,
    }

    crpacks_path = OUTPUT_DIR / "crpacks.json"

    # --- 출력 3: parse_summary.json ---
    # Release별 통계
    # errors 는 errors_count 와 같은 기준(목록 밖 오류)으로 세고, 열 수 없다고 확인해 둔 문서는 따로 센다.
    release_stats = defaultdict(lambda: {"total": 0, "with_reason": 0, "with_summary": 0, "errors": 0,
                                         "known_unopenable": 0})
    known_paths = {r.source_path for r in known_unopenable}
    for r in unique_results:
        rs = release_stats[r.release]
        rs["total"] += 1
        if r.reason_for_change:
            rs["with_reason"] += 1
        if r.summary_of_change:
            rs["with_summary"] += 1
        if r.source_path in known_paths:
            rs["known_unopenable"] += 1
        elif r.errors:
            rs["errors"] += 1

    summary = {
        "script": "01_parse_cr_documents.py",
        "wg": "RAN5",
        "input_dir": str(INPUT_DIR.relative_to(PROJECT_ROOT)),
        "total_files_found": len(cr_docs),
        "unique_crs": len(unique_results),
        "duplicates_removed": len(all_results) - len(no_tdoc) - len(unique_results),
        "tdoc_extraction_failed": len(no_tdoc),
        "field_coverage": {
            "reasonForChange": total_with_reason,
            "summaryOfChange": total_with_summary,
            "consequencesIfNotApproved": total_with_consequences,
            "clausesAffected": total_with_clauses,
            "crossSpecAffects": total_with_cross_spec,
        },
        "errors_count": total_with_errors,
        "known_unopenable_count": len(known_unopenable),
        "crpacks_count": len(crpacks),
        "release_stats": dict(release_stats),
    }

    summary_path = OUTPUT_DIR / "parse_summary.json"
    # 최종 결과 셋은 모두 직렬화한 뒤 함께 게시한다. 재개용 파일은 이전 단일 파일 저장 규칙을 유지한다.
    publish_text_set([(path, json.dumps(data, ensure_ascii=False, indent=2))
                      for path, data in ((cr_output_path, cr_output), (crpacks_path, crpacks_output),
                                         (summary_path, summary))])
    log.info(f"\n출력 1: {cr_output_path}")
    log.info(f"  파일 크기: {cr_output_path.stat().st_size / 1024 / 1024:.1f} MB")
    log.info(f"출력 2: {crpacks_path}")
    log.info(f"  CRPack 수: {len(crpacks)}, CR 총 수: {crpacks_output['metadata']['total_crs_in_packs']}")
    log.info(f"  tsgMeeting: 채움 {tsg_stats['with_cover']}, 커버 없음 {len(tsg_stats['no_cover'])}, "
             f"읽기 실패 {len(tsg_stats['unreadable'])}, 충돌 {len(tsg_stats['conflict'])}")
    log.info(f"출력 3: {summary_path}")

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
