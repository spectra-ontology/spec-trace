#!/usr/bin/env python3
"""
Phase-8 Step-1: CR 변경 본문 파싱 + 4-Strategy 청킹

Spec: docs/tsg/RAN/formal/RAN4/phase-8/design-spec/tdoc_vectordb_specs(CR).md

입력:
  - data/corpus/tsg/RAN/formal/change-requests/RAN4/derived/Rel-*/TSG/{팩}/ — cr_inputs 가 모은다(표지 제외)
  - ontology/output/tsg/RAN/formal/parsed_cr/RAN4/cover_sheets.json (Phase-4 메타데이터)
  - ontology/output/tsg/RAN/formal/parsed_cr/RAN4/cr_documents.json (Phase-4 메타데이터)

출력:
  - vectordb/parsed/cr/RAN4/ran4_cr_chunks.json (전체 청크)
  - vectordb/parsed/cr/RAN4/parse_stats.json (파싱 통계)

4전략:
  A: 헤더 전용 (body < 100 tok)
  B: 단일 청크 (body < 2K tok)
  C: Section 분할 (headings >= 2)
  D: 토큰 기반 분할 (headings 0-1 & body >= 2K)
"""

import itertools
import json
import re
import sys
import logging
import zipfile
from dataclasses import dataclass, field, asdict
from pathlib import Path
from xml.etree import ElementTree as ET

# === 경로 설정 ===
PROJECT_ROOT = Path(__file__).resolve().parents[7]
WG = 'RAN4'
OUTPUT_DIR = PROJECT_ROOT / "vectordb" / "parsed" / "cr" / "RAN4"
LOG_DIR = PROJECT_ROOT / "logs" / "tsg" / "RAN" / "formal" / "RAN4" / "phase-8"
PHASE4_DIR = PROJECT_ROOT / "ontology" / "output" / "tsg" / "RAN" / "formal" / "parsed_cr" / "RAN4"
# CR 폴더 이름의 WG 번호. Phase-4 `_TDOC_RE` 와 같은 꼴이다.
_FOLDER_TDOC_RE = re.compile(r"(R4[-_]\d{7})(?!\d)")

# === 정규 프로세스 hardening ===
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "common"))
from common.atomic_io import write_json_atomic
from common.chunker import (  # noqa: E402
    enforce_hard_max as _enforce_hard_max, HARD_MAX_DEFAULT as _HARD_MAX_TOK,
    count_tokens as _count_tokens_exact, renumber_chunk_indices as _renumber_chunk_indices,
    _index_base,
)
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "tsg" / "RAN" / "formal" / "common"))
import docx_text  # noqa: E402
import cr_split_pieces  # noqa: E402
import cr_cover_cell  # noqa: E402
import cr_revision_marks  # noqa: E402
import ts_section_number as tsn  # noqa: E402
from cr_clause import clause_candidates, placeholder_clauses, range_clauses  # noqa: E402
import cr_identity  # noqa: E402
import cr_attachments  # noqa: E402
import tsg_cr_decision  # noqa: E402
import cr_inputs  # noqa: E402
import cr_other_wg  # noqa: E402  (다른 WG 슬롯에 놓인 이 WG 의 CR · 이 슬롯에 놓인 다른 WG 의 CR)
INPUT_DIR = cr_inputs.derived_dir("RAN4")

def configure_logging():
    """실제 파싱 실행 때만 출력 디렉토리와 로그를 준비한다."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_DIR / "01_parse_cr_chunks.log", mode="w"),
        ],
    )


log = logging.getLogger(__name__)

# === XML Namespaces ===
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

# === Spec §3.2: 청킹 파라미터 ===
BODY_TOKEN_MIN = 100       # Strategy A 임계값
BODY_TOKEN_SINGLE = 2000   # Strategy B 임계값
HEADING_MIN_FOR_C = 2      # Strategy C 최소 heading 수
SPLIT_TARGET = 2000        # Spec §3.3: 조각 크기 목표
SPLIT_OVERLAP = 200        # README '청크를 나누는 전략': 오버랩 (Phase-7: 100 → Phase-8: 200)
MIN_CHUNK_TOKENS = 50      # README '청크를 나누는 전략': 최소 청크 크기

# === Heading 스타일 매핑 (Phase-7 패턴 + CR DOCX 공백 없는 형식) ===
HEADING_LEVEL_MAP = {
    # Phase-7 패턴 (공백 있음)
    "Heading 1": 1, "Heading 2": 2, "Heading 3": 3,
    "Heading 4": 4, "Heading 5": 5,
    "Heading 6": 6, "Heading 7": 7, "Heading 8": 1, "Heading 9": 1,
    # CR DOCX 스타일 (공백 없음)
    "Heading1": 1, "Heading2": 2, "Heading3": 3,
    "Heading4": 4, "Heading5": 5, "Heading6": 6, "Heading7": 7, "Heading8": 1, "Heading9": 1,
    # 기타 약어
    "H6": 6, "h60": 6,
}
#: 부속서 스타일. 머리(`Annex A (normative): …`)와 하위 절이 같은 스타일로 적힌다.
ANNEX_STYLES = {"Heading 8", "Heading 9", "Heading8", "Heading9"}

# === 파일명 패턴 ===
# 38133_CR0505_(Rel-16)_R4-2071640.docx
FILENAME_RE = re.compile(
    r"(\d{5}(?:-\d)?)_CR(\d+(?:r\d+)?)_\(Rel-\d+\)_\s*(R4-\d{7})",
    re.IGNORECASE,
)

# === unchanged/next change 마커 (Spec Step-2 상세 §2.6.4) ===
MARKER_RE = re.compile(
    r"^-{2,}\s*(?:next\s+change|unchanged|start of|end of|first change|last change|new clause)",
    re.IGNORECASE,
)

# 대시로 시작하지 않는 표지 문단(「Start of first change」 · 「<Unchanged parts omitted>」 등)도 표지로 본다.
# 장식 기호를 걷어 낸 낱말이 모두 표지 어휘이거나 숫자이고, 그 가운데 「바뀜 · 생략」을 뜻하는 기준 단어가
# 하나 이상 있을 때만 표지다. 표지 어휘 밖 낱말이 하나라도 있으면(절 제목 · 문장 · 표 이름) 표지가 아니다.
_ASN1_COMMENT_RE = re.compile(r"^--(?!-)")
# 지운 표지(「[DEL]<Start of modified section>[/DEL]」)도 표지다. 「[deleted …」 의 「[del」 은 남긴다.
_MARKER_DEL_RE = re.compile(r"\[/?del(?:\]|$)|(?<![a-z])/?del\]", re.IGNORECASE)

_MARKER_CORE_ANCHOR = {
    "change", "changes", "chagne", "chagnes", "modified", "modification", "modifications",
    "unchanged", "unaffected", "unmodified", "omitted", "ommited", "omited", "ommitted",
    "skipped", "skip", "tp", "proposal", "proposals",
}
_MARKER_CORE_VOCAB = _MARKER_CORE_ANCHOR | {
    "start", "starts", "strat", "end", "ends", "begin", "begins", "beginning", "the", "of", "a",
    "first", "second", "third", "fourth", "fifth", "sixth", "next", "last", "final", "set", "sets",
    "proposed", "proposal", "text", "texts", "section", "sections", "clause", "clauses",
    "subclause", "subclauses", "sub-clause", "sub-clauses", "part", "parts", "is", "are",
    "not", "shown", "copied", "removed", "this", "in", "and", "here", "irrelevant", "unrelated",
    "non-related", "non-relevant", "other", "rest", "remaining", "no", "more", "all", "for",
}

# 기준 단어의 변이형 · 오타(「unchaged」 · 「skiped」 · 「chnage」 등). 실제 CR 본문 표지에서 모은 꼴만 둔다.
_MARKER_VARIANT_ANCHOR = {
    "non-changed", "unchaged", "unchange", "unchanges", "unchangeed", "uncahnged", "unhanged",
    "uanchanged", "umodified", "unmoified", "omittd", "omiteed", "omiitted", "skiped", "sikpped",
    "sklipped", "skippted",
    "chnage", "chnages", "chang", "changess", "modificatcion", "kipped", "unchangedt",
    "unchanted", "3rdchange", "modifed", "omtitted", "uinchanged", "uncahned", "skippe",
    "chnaged", "unchnged", "unchnaged", "ommit",
    "skippped", "skippied", "skipppped", "skippled", "skpped", "skppped", "modifcations",
    "unchganged", "unchged", "uncchanged", "unhcnaged", "unvhanged", "un-changed", "omiited",
    "unskipped", "skipping", "skips",
}
# 「무관한 부분」을 뜻하는 낱말: 다른 낱말이 모두 어휘일 때만 표지가 되므로 본문 문장과는 겹치지 않는다.
_MARKER_VARIANT_ANCHOR |= {"irrelevant", "unrelated", "unreleated", "non-related", "non-relevant"}
_MARKER_ANCHOR = _MARKER_CORE_ANCHOR | _MARKER_VARIANT_ANCHOR
_MARKER_VOCAB = _MARKER_CORE_VOCAB | _MARKER_VARIANT_ANCHOR | {
    "omit", "omitting", "skipping", "skipp", "deleted", "partially", "partial",
    "operations", "portion", "portions", "content", "contents", "asn.1", "asn1", "ans1", "asn",
    "ies", "ie", "table", "tables", "message", "messages", "lines", "items", "codes", "rows",
    "definitions", "parameters", "configurations", "sessions", "partes",
    "to", "without", "same", "new", "included", "reproduced", "stop", "on", "oft", "nex",
    "netxt", "unnecessary", "affected", "impacted", "cr", "secondary", "fist", "change1",
    "frist", "srart", "thrid", "firth", "2nt", "thet", "nd", "xt", "emd", "begining", "of1st",
    "unreleated", "cut", "until", "go", "ignore", "intermediate", "previous", "has", "been",
    "was", "some", "obvious", "extract", "information", "reference", "only", "excluded",
    "context", "entries", "element", "elements", "partly", "short", "subsection",
    "subsections", "file", "document", "specification", "above", "capabilities", "timers",
    "ts", "tr", "pdu", "informative", "below", "provided", "just", "there", "continue",
    "continues", "started", "following", "were", "non", "tabular", "showing", "show",
    "corresponding", "place", "convenience", "against", "clarity", "need", "straight", "urnealted",
    "notes", "any", "avoid", "from", "fo", "propose", "annex", "endof", "endt", "enf", "srat",
    "star", "stare", "starr", "shipped", "wihtout", "un", "note", "editor", "made", "paragraphs",
    "remove", "including", "inlcuding", "includes", "have", "cells", "many",
    "lot", "several", "columns", "chapter", "chapters", "code", "none", "with", "off", "re",
    "line", "paragraph", "descriptions", "sub", "ship", "rext", "texk", "scetion", "scetions",
    "seciton", "sctions", "contenes", "cotents",
}
# 그 낱말만으로는 표지 뜻이 서지 않아, 짝 낱말이 함께 있을 때만 어휘로 친다.
_MARKER_NEEDS = {
    "changed": {"not", "no", "without", "section", "sections", "clause", "clauses",
                "subclause", "subclauses", "part", "parts",
                "start", "end", "begin", "beginning", "next"},  # 「text not changed」·「changed section」 / 표 IE 「>>>Changed」
    "request": {"start", "end", "begin", "beginning", "strat", "next"},  # 「Start of change request」 / CR 서식 「CHANGE REQUEST」
}
_MARKER_ORDINAL_RE = re.compile(
    r"^(?:first|second|third|fourth|forth|fifth|sixth|seventh|eighth|eigth|ninth|nineth|tenth|"
    r"eleventh|twelfth|twelth|thirteenth|fourteenth|fifteenth|fifthteenth|sixteenth|seventeenth|"
    r"eighteenth|nineteenth|twentieth|thirtieth|(?:twenty|thirty)-(?:first|second|third|fourth|fifth|"
    r"sixth|seventh|eighth|ninth)|secnd|seond|fithteenth|fitfthteenth|thirteeth|twelveth)"
    r"(?:-(?:bis|ter|quater))?$"
)
_MARKER_ORD_RE = re.compile(
    r"^\d+(?:st|nd|rd|th|h)?$|^[\d.]+$|^#?\d+$|^[ivx]+$|^r\d-\d{6,8}$|^\d+(?:-\d+)+$|^\d+\.?[a-z]$"
)
# 「A.4.1」·「7.3B.2.0.3.5」·「5.5A.3.2-1c」 같은 절·표 번호. 표지 괄호 안에서만 어휘로 친다
# (괄호 없는 「Clauses affected: 6.1C.2.2.2, …」 는 표지 서식의 영향 절 목록이라 본문이다).
_MARKER_SECID_RE = re.compile(r"^(?:[a-z]|\d+[a-z]?)(?:\.\d+[a-z]?)+(?:-\d+[a-z]?)*$")
# 「change1」·「2ndchange」 처럼 번호가 낱말에 붙어 쓰인 표지 낱말.
_MARKER_GLUED_RE = re.compile(r"^(?:\d+(?:st|nd|rd|th))?([a-z]+)\d*$")
_MARKER_WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9.'\-]*")
_MARKER_SECNUM_RE = re.compile(r"^\d+(?:\.\d+)+$")
_MARKER_MAX_WORDS = 16
_MARKER_DECOR_RE = re.compile(r"[\[\]<>()*/=~#{}…]|-{2,}|—")


def _marker_words(text: str) -> list[str]:
    words = [w.strip(".'-").lower() for w in _MARKER_WORD_RE.findall(text)]
    return [w for w in words if w]


def _is_marker_words(text: str) -> bool:
    words = _marker_words(text)
    if not words or len(words) > _MARKER_MAX_WORDS:
        return False
    # 절 번호로 시작하는 제목은 본문이지만, 「<6.6 skipped>」 처럼 괄호로 둘러싼 것은 표지다.
    if _MARKER_SECNUM_RE.match(words[0]) and not text.lstrip().startswith(("<", "[", "{", "(")):
        return False
    have = set(words)
    bracketed = text.lstrip().startswith(("<", "[", "{", "("))
    def ok(w):
        if w in _MARKER_VOCAB or _MARKER_ORD_RE.match(w) or _MARKER_ORDINAL_RE.match(w):
            return True
        if bracketed and _MARKER_SECID_RE.match(w):
            return True
        if w in _MARKER_NEEDS:
            # 「Eighth change request」 처럼 서수가 앞서도 차례를 가리키는 표지다.
            if _MARKER_NEEDS[w] & have or (w == "request" and any(_MARKER_ORDINAL_RE.match(x) for x in have)):
                return True
            # 「[Skip changed text]」 처럼 다른 표지 낱말과 함께 쓰인 「changed」.
            return w == "changed" and any(x != w and x in _MARKER_ANCHOR for x in have)
        g = _MARKER_GLUED_RE.match(w)
        # 「TP1」 은 시험 목적 번호(「[TS 24.501, clause 5.4.1.2.4.5 (TP1, TP2)]」)라 붙은 꼴로는 표지로 치지 않는다.
        if g and g.group(1) == "tp":
            return False
        if g and (g.group(1) in _MARKER_ANCHOR or (g.group(1) in _MARKER_VOCAB and g.group(1) not in _MARKER_NEEDS)):
            return True
        # 「change-1」 처럼 붙임표로 이은 낱말은 조각마다 따진다.
        return "-" in w and all(ok(x) for x in w.split("-") if x)
    def anchor(w):
        g = _MARKER_GLUED_RE.match(w)
        return w in _MARKER_ANCHOR or bool(g and g.group(1) in _MARKER_ANCHOR and g.group(1) != "tp") or (
            "-" in w and any(anchor(x) for x in w.split("-") if x))
    if not all(ok(w) for w in words):
        return False
    if any(anchor(w) for w in words) or ("changed" in have and ok("changed")):
        return True
    # 「omit」 은 TTCN 값·코드(「omit));」·「= omit;」)와 겹치므로, 낱말이 둘 이상이거나 괄호·기호로
    # 둘러싸였을 때만 표지로 보고, 코드 구두점(쉼표·쌍반점·등호)이나 짝이 안 맞는 괄호가 있으면 본문으로 둔다.
    if "omit" not in have or any(c in text for c in ",;="):
        return False
    if text.count("(") != text.count(")"):
        return False
    return len(words) > 1 or bool(_MARKER_DECOR_RE.search(text))


def _is_marker_cell(text: str) -> bool:
    text = _MARKER_DEL_RE.sub("", text).strip()
    if not text or text.endswith(","):
        return False
    # 쌍반점이나 짝이 안 맞는 중괄호는 코드 줄(「};<<SKIPPED CODE>>」)이라, 표지가 붙어 있어도 본문으로 둔다.
    if ";" in text or text.count("{") != text.count("}"):
        return False
    if _is_marker_words(text):
        return True
    return bool(MARKER_RE.match(text)) and not _ASN1_COMMENT_RE.match(text)


def _is_change_marker(text: str) -> bool:
    """변경 표지(Spec Step-2 상세 §2.6.4)인가. 문단 · 표 행(`| 칸 | 칸 |`) · 표 · 그림 제목 글을 받는다.

    표 행은 낱말 있는 칸이 모두 표지일 때만 표지다(「<ROWS SKIPPED> | pc_eTDD」 처럼 본문 칸이 섞이면 본문).
    ASN.1 주석(`-- Start of …`)은 낱말 규칙이 표지로 볼 때만 뺀다.
    """
    t = text.strip()
    if "|" in t:
        cells = [c.strip() for c in t.strip("|").split("|")]
        # 「…」·「⋮」 처럼 낱말이 없는 칸은 생략 기호이므로 빈 칸과 같이 본다.
        cells = [c for c in cells if _MARKER_WORD_RE.search(c)]
        return bool(cells) and all(_is_marker_cell(c) for c in cells)
    return _is_marker_cell(t)


# === 데이터 모델 ===

@dataclass
class CRChunk:
    """Spec §3.4: Qdrant 청크 데이터. camelCase = Qdrant/JSON-LD 스키마 일치."""
    chunkId: str
    chunkType: str               # "header" | "body"
    tdocNumber: str
    specNumber: str
    crNumber: str
    category: str = ""
    workItem: str = ""
    meeting: str = ""
    source: str = ""
    title: str = ""
    clausesAffected: list = field(default_factory=list)
    sectionIds: list = field(default_factory=list)
    # 본문 청크 전용
    chunkSectionId: str = ""    # Strategy C: 해당 Section ID
    chunkIndex: int = 0
    totalChunks: int = 0
    strategy: str = ""
    # 헤더 청크 전용
    bodySnippet: str = ""
    crPackId: str = ""
    tsgMeeting: str = ""
    # 공통
    text: str = ""
    tokenCount: int = 0


# =============================================================================
# Phase-4 메타데이터 로드
# =============================================================================

def load_phase4_metadata() -> tuple[dict, dict]:
    """Phase-4 cover_sheets.json + cr_documents.json 로드.

    Returns:
        (cover_map, cr_doc_map). cover_map 의 키는 (팩, tdoc) · (팩, "") · tdoc, cr_doc_map 은 tdoc
    """
    # Cover sheets: tdocNumber → cover data
    cover_map = {}
    cover_path = PHASE4_DIR / "cover_sheets.json"
    if cover_path.exists():
        with open(cover_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        packs = data.get("crpacks", data.get("cover_sheets")) if isinstance(data, dict) else None
        # 파일이 있는데 팩 목록 키가 없거나 목록이 아니면 빈 표지로 넘어가지 않는다. 그대로 가면 모든 청크의
        # 분류 · 작업 항목 · TSG 회의가 조용히 빈다.
        if not isinstance(packs, list):
            raise SystemExit(f"cover_sheets.json 의 crpacks 목록을 읽지 못함: {cover_path}")
        for pack in packs:
            pack_id = pack.get("cr_pack_id", "")
            # 키는 셋이다. (팩, tdoc) 은 그 팩 표지의 CR 칸, (팩, "") 은 팩 자체의 TSG 회의,
            # tdoc 하나는 Phase-4 기록이 없는 파일을 위한 것이다(두 팩 표지에 실리면 마지막 팩).
            cover_map[(pack_id, "")] = {"cr_pack_id": pack_id, "tsg_meeting": pack.get("tsg_meeting", "")}
            for cr in pack.get("cr_entries", []):
                tdoc = cr.get("tdoc_number", "")
                if tdoc:
                    entry = {
                        "category": cr.get("category", ""),
                        "work_item": cr.get("work_item", ""),
                        "meeting": cr.get("meeting", ""),
                        "source": cr.get("source", ""),
                        "title": cr.get("title", ""),
                        "cr_pack_id": pack_id,
                        "tsg_meeting": pack.get("tsg_meeting", ""),
                        "clauses_affected": cr.get("clauses_affected", ""),
                    }
                    cover_map[(pack_id, tdoc)] = entry
                    cover_map[tdoc] = entry
        log.info(f"  Cover sheets 로드: {sum(isinstance(k, str) for k in cover_map)}개 tdocNumber 매핑")

    # CR documents: tdocNumber → parsed CR data
    cr_doc_map = {}
    cr_doc_path = PHASE4_DIR / "cr_documents.json"
    if cr_doc_path.exists():
        with open(cr_doc_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        records = data.get("documents") if isinstance(data, dict) else None
        # 파일이 있는데 CR 문서 목록 키가 없거나 목록이 아니면 빈 사전으로 넘어가지 않는다. 그대로 가면 모든
        # 청크의 이유 · 요약 · 영향 절 · CR 팩이 조용히 빈다.
        if not isinstance(records, list):
            raise SystemExit(f"cr_documents.json 의 documents 목록을 읽지 못함: {cr_doc_path}")
        for cr in records:
            tdoc = cr.get("tdoc_number", "")
            if tdoc:
                cr_doc_map[tdoc] = cr
        log.info(f"  CR documents 로드: {len(cr_doc_map)}개 tdocNumber 매핑")

    return cover_map, cr_doc_map


# =============================================================================
# 토큰 & 텍스트 유틸리티 (Phase-7 패턴)
# =============================================================================

def count_tokens(text: str) -> int:
    """토큰 수 추정. Spec: len(text) // 4."""
    return len(text) // 4


def _body_paragraph_text(para_elem) -> str:
    """변경 본문 문단 글. 들어간 글은 그대로, 빠진 글은 `[DEL]…[/DEL]` 로 함께 읽는다(README '변경 표시 읽기').

    수식은 선형 표기로, 수식 개체는 읽은 글로 넣는다(`docx_text.chunk_text`).
    """
    return docx_text.chunk_text(para_elem, deleted=docx_text.MARK)


def _body_boxed(para_elem) -> str:
    """표 칸 문단 글 — `_body_paragraph_text` 다음 줄에 그 문단에 연결된 부동 텍스트 상자(`w:txbxContent`) 글을 붙인다
    (`docx_text.boxed_text`, 글상자 안 문단도 `_body_paragraph_text` 로 읽는다).

    `docx_text.chunk_text` 는 글상자를 읽지 않는다. 지운 변경 표시 안 글상자는 읽지 않고, `mc:AlternateContent` 는 한 벌만,
    도형 묶음 · 그리기 캔버스 안 글상자는 그림 안 라벨이라 넣지 않는다(`docx_text.box_text`).
    """
    return docx_text.boxed_text(para_elem, read=_body_paragraph_text)


def table_to_text(tbl_elem) -> str:
    """w:tbl → pipe-table 텍스트. 행마다 `| 칸 | 칸 |` 한 줄, 빈칸만 있는 행은 뺀다.

    행 · 칸은 `docx_text.table_rows` 로 읽는다. 칸 안 문단은 `_body_boxed`(빠진 글 `[DEL]…[/DEL]`, 그 문단에 연결된 부동 텍스트 상자 글은 다음 줄)로 읽어
    빈칸으로 잇고, 행 지움 표시(`w:trPr/w:del`)가 있는 행은 칸 글 전체를 `[DEL]…[/DEL]` 로 감싼다(`docx_text.MARK`).
    칸 안 표는 같은 꼴의 행을 ` ; ` 로 이어 칸 글 한 줄로 넣는다.
    주의: 행 · 칸을 `w:tr` · `w:tc` 직접 자식으로 돌고 칸 글을 `findall(w:p)` 로 읽으면 칸 안 표의 글, 블록 래퍼
    (`w:sdt` · `w:customXml`) 속 행 · 칸 · 문단이 빠지고, 지운 행이 확정 글로 남으며, 세로로 합친 칸(`w:vMerge`)의
    이어지는 행에는 머리글 없는 값만 남는다.
    표본 CR 300 개의 표 3,513 개 가운데 1,531 개의 글이 옛 읽기와 다르다 — 칸 안 줄바꿈만 다른 표 655, 나머지는 세로 합침 862 · 지운 행
    23 · 칸 안 표 24 개가 든 표다(한 표에 여럿이 겹친다).
    """
    def lines(rows: list[list[str]]) -> list[str]:
        out = []
        for row in rows:
            cells = [" ".join(x for x in c.split("\n") if x).strip() for c in row]
            line = "| " + " | ".join(cells) + " |"
            # 모든 칸이 변경 표지인 행(「| Unchanged rows skipped |」)은 문단 표지처럼 뺀다(Spec Step-2 상세 §2.6.4).
            if any(cells) and not _is_change_marker(line):
                out.append(line)
        return out

    rows = docx_text.table_rows(tbl_elem, para=_body_boxed, deleted=docx_text.MARK,
                                nested=lambda inner: [" ; ".join(lines(inner))])
    return "\n".join(lines(rows))


# =============================================================================
# XML-level body 파싱 (Phase-2 패턴)
# =============================================================================

_W_SDT = f"{{{W_NS}}}sdt"
_W_SDT_PR = f"{{{W_NS}}}sdtPr"
_W_SDT_CONTENT = f"{{{W_NS}}}sdtContent"
_W_CUSTOM_XML = f"{{{W_NS}}}customXml"
_W_DOC_PART_GALLERY = f"{{{W_NS}}}docPartGallery"
#: 목차 내용 제어의 `w:docPartGallery` 값. Word 가 목차를 넣을 때 다는 값이고, 수집 대상 RAN1~4 의 목차 래퍼 31개가
#: 모두 이 값을 가진다.
_TOC_GALLERY = "Table of Contents"


def _is_toc_sdt(sdt) -> bool:
    sdt_pr = sdt.find(_W_SDT_PR)
    if sdt_pr is None:
        return False
    gallery = sdt_pr.find(f".//{_W_DOC_PART_GALLERY}")
    return gallery is not None and gallery.get(f"{{{W_NS}}}val") == _TOC_GALLERY


def _body_blocks(container):
    """본문 블록(`w:p` · `w:tbl`)을 문서 순서로. 블록 `w:sdt` · `w:customXml` 안으로 들어가되 목차 `w:sdt` 는 건너뛴다.

    변경 본문을 내용 제어 안에 적은 CR 이 있어 직계만 돌면 그 글이 빠진다. 래퍼 안 글의 대부분은 목차라서 그대로
    내려가면 청크에 목차 잡음이 들어오므로 목차 래퍼만 뺀다. 표지(`Cover Pages`) 래퍼는 내려간다.
    """
    w_p = f"{{{W_NS}}}p"
    w_tbl = f"{{{W_NS}}}tbl"
    for child in container:
        if child.tag == w_p or child.tag == w_tbl:
            yield child
        elif child.tag == _W_SDT:
            if _is_toc_sdt(child):
                continue
            content = child.find(_W_SDT_CONTENT)
            if content is not None:
                yield from _body_blocks(content)
        elif child.tag == _W_CUSTOM_XML:
            yield from _body_blocks(child)


def parse_body_xml(docx_path: Path) -> list[tuple[str, ET.Element]]:
    """DOCX의 body-level 요소를 순서대로 반환.

    Returns:
        [(tag_type, element), ...] where tag_type is 'p' or 'tbl'
    """
    try:
        with zipfile.ZipFile(str(docx_path), "r") as zf:
            xml_content = docx_text.zip_part(zf, "word/document.xml")
            try:
                styles = docx_text.style_table(zf)
            except Exception as e:
                styles = ({}, {})
                log.warning(f"  스타일 표를 읽지 못해 styleId 로 제목을 찾음: {docx_path.name} ({e})")
    except Exception as e:
        log.error(f"  DOCX ZIP 열기 실패: {docx_path.name} — {e}")
        return []

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        xml_content, fixed = docx_text.repair_tag_balance(xml_content)
        root = ET.fromstring(xml_content)
        log.warning(f"  태그 짝 {fixed}곳을 고쳐 읽음: {docx_path.name} — {e}")
    body = root.find(f"{{{W_NS}}}body")
    if body is None:
        return []

    w_p = f"{{{W_NS}}}p"
    w_tbl = f"{{{W_NS}}}tbl"

    elements = [("p" if el.tag == w_p else "tbl", el) for el in _body_blocks(body)]
    # 표지 표 칸 안에 이어 적은 변경 본문은 표지 표 바로 뒤의 본문 요소로 꺼낸다(`cr_cover_cell`).
    elements = cr_cover_cell.unwrap(elements, tag_of=lambda el: "tbl" if el.tag == w_tbl else "p")
    docx_text.annotate_paragraph_styles(styles, [el for tag, el in elements if tag == "p"])
    return elements


def get_paragraph_style(p_elem) -> str:
    """w:p 요소의 스타일 이름. 이름을 풀지 못한 문단은 styleId.

    > 주의: `w:pStyle` 은 styleId 이고 제목 표(`HEADING_LEVEL_MAP`)는 이름이다. 다른 언어판 Word 로 저장한 CR 은
    > styleId 가 `2` · `40` · `Titre2` 처럼 바뀌어 styleId 로는 제목을 놓치고, 제목을 놓치면 절 나누기와 고치지 않은
    > 절 덜기(`cr_revision_marks`)가 함께 무너진다. 그래서 문서를 읽을 때 스타일 부품으로 이름을 풀어 문단에 달아
    > 두고(`docx_text.annotate_paragraph_styles`) 여기서 그 이름을 먼저 쓴다.
    """
    w_pPr = f"{{{W_NS}}}pPr"
    w_pStyle = f"{{{W_NS}}}pStyle"
    name = p_elem.get(docx_text.STYLE_NAME)
    if name:
        return name
    pPr = p_elem.find(w_pPr)
    if pPr is not None:
        pStyle = pPr.find(w_pStyle)
        if pStyle is not None:
            return pStyle.get(f"{{{W_NS}}}val", "")
    return ""


def get_outline_level(p_elem) -> int | None:
    """w:p 요소에서 outlineLvl 추출 (대안 heading 탐지)."""
    w_pPr = f"{{{W_NS}}}pPr"
    w_outlineLvl = f"{{{W_NS}}}outlineLvl"
    pPr = p_elem.find(w_pPr)
    if pPr is not None:
        olvl = pPr.find(w_outlineLvl)
        if olvl is not None:
            try:
                return int(olvl.get(f"{{{W_NS}}}val", ""))
            except (ValueError, TypeError):
                pass
    return None


# =============================================================================
# CR Form 분리 (Part 1 / Part 2)
# =============================================================================

FORM_START_WORDS = ("Reason for change", "Summary of change")
# 빈 문단으로 갈라진 서식 표(Consequences · Clauses 가 다음 표로 넘어간 꼴)와 꼬리 표도 서식으로 잇는다.
FORM_CONTINUE_WORDS = FORM_START_WORDS + ("Consequences if not", "Clauses affected", "Other specs", "Change history")
CR_COVER_WORD = "CHANGE REQUEST"


def _table_text(elem: ET.Element) -> str:
    return " ".join(t.text for t in elem.iter(f"{{{W_NS}}}t") if t.text)


def _form_chain_end(body_elements: list[tuple[str, ET.Element]], start: int) -> int:
    """`start` 서식 표에서 빈 문단만 건너 서식 글귀 표로 이어지는 마지막 인덱스."""
    end = start
    for idx in range(start + 1, len(body_elements)):
        tag, elem = body_elements[idx]
        if tag == "tbl":
            text = _table_text(elem)
            # 표지 하단 이력 표("This CR's revision history")도 Spec 이 임베딩에서 빼는 Change History 표다.
            if (any(w in text for w in FORM_CONTINUE_WORDS)
                    or "revision history" in text.lower().replace("\u2019", "'")):
                end = idx
            else:
                break
        elif tag == "p":
            # form 테이블 사이 빈 문단은 무시
            if docx_text.paragraph_text(elem, math=False):
                break
    return end


def find_last_form_table_index(body_elements: list[tuple[str, ET.Element]]) -> int:
    """CR form 테이블의 마지막 인덱스 반환.

    Spec §2.2: 3GPP CR form은 3~4개 테이블. "Reason for change" 포함 테이블이 핵심.
    마지막 form 테이블 다음이 Part 2 시작.

    Spec §2.8 은 본문 표를 청크에 넣으므로, 본문 글 뒤에서 서식 이름을 인용한 표는 서식이 아니다.
    그래서 첫 서식 표에서 이어지는 표들만 서식으로 잡고, 그 뒤 서식 표는 새 CHANGE REQUEST 표지가
    앞서거나 표 안에 있을 때만(한 파일에 CR 서식이 두 벌 이상인 꼴) 다음 서식으로 잡는다.
    """
    last_form_idx = -1
    cover_seen = False
    idx = 0
    while idx < len(body_elements):
        tag, elem = body_elements[idx]
        if tag == "tbl":
            text = _table_text(elem)
            if (any(w in text for w in FORM_START_WORDS)
                    and (last_form_idx < 0 or cover_seen or CR_COVER_WORD in text)):
                last_form_idx = _form_chain_end(body_elements, idx)
                cover_seen = False
                idx = last_form_idx + 1
                continue
            if last_form_idx >= 0 and CR_COVER_WORD in text:
                cover_seen = True
        idx += 1
    return last_form_idx


# =============================================================================
# Heading 탐지
# =============================================================================

@dataclass
class BodyHeading:
    """변경 본문 내 heading 정보."""
    index: int           # body_elements 내 인덱스
    level: int
    section_number: str
    section_title: str
    text: str            # 원문


def detect_headings(body_elements: list[tuple[str, ET.Element]], start_idx: int) -> list[BodyHeading]:
    """Part 2 body에서 heading 탐지.

    pStyle "Heading N" 매핑(Spec Step-2 상세 §2.4.1 의 Style 기반) + outlineLvl 대안.
    """
    headings = []

    for idx in range(start_idx, len(body_elements)):
        tag, elem = body_elements[idx]
        if tag != "p":
            continue

        style = get_paragraph_style(elem)
        level = HEADING_LEVEL_MAP.get(style)

        # outlineLvl 대안
        if level is None:
            olvl = get_outline_level(elem)
            if olvl is not None and 0 <= olvl <= 8:
                level = olvl + 1
        # 스타일이 선언한 개요 수준(바탕 스타일에서 물려받은 것 포함). 이름이 제목이 아닌 제목 스타일이다.
        if level is None and elem.get(docx_text.STYLE_OUTLINE) is not None:
            level = int(elem.get(docx_text.STYLE_OUTLINE)) + 1

        if level is None:
            continue

        # 제목은 바뀐 뒤의 글로 읽는다. CR 이 통째로 지운 절이면 지워진 제목이 그 절을 가리킨다.
        text = docx_text.paragraph_text(elem, math=False) or docx_text.paragraph_text(
            elem, deleted=docx_text.KEEP, math=False)
        if not text:
            continue
        # 표 · 그림 제목 · ASN.1 정의 줄 · 제목 아닌 3GPP 스타일 문단은 개요 수준이 붙어 있어도 절 경계가 아니다
        # (`docx_text.not_heading`). 변경 표지는 캡션 스타일이어도 바뀐 자리 사이의 경계라 제목으로 둔다.
        if docx_text.not_heading(style, text) and not _is_change_marker(text):
            continue

        split = tsn.split_annex_heading if style in ANNEX_STYLES else tsn.split_heading
        sec_num, sec_title = split(text)
        if not tsn.is_section_number(sec_num):
            sec_num, sec_title = "", text

        headings.append(BodyHeading(
            index=idx, level=level,
            section_number=sec_num, section_title=sec_title,
            text=text,
        ))

    return headings


# =============================================================================
# Body 텍스트 추출
# =============================================================================

def extract_body_text(
    body_elements: list[tuple[str, ET.Element]],
    start_idx: int,
    end_idx: int | None = None,
) -> list[str]:
    """body_elements 범위에서 텍스트 추출.

    - w:p → change marking 포함 텍스트, 그 문단에 연결된 부동 텍스트 상자 글은 다음 문단(제목 문단 포함)
    - w:tbl → pipe-table 텍스트
    - unchanged/next change 마커 제외 (Spec Step-2 상세 §2.6.4)
    """
    paragraphs = []
    end = end_idx if end_idx is not None else len(body_elements)

    for idx in range(start_idx, end):
        tag, elem = body_elements[idx]
        if tag == "p":
            text = _body_paragraph_text(elem)
            if text and not _is_change_marker(text):
                paragraphs.append(text)
            # 문단에 연결된 부동 텍스트 상자 글은 다음 문단으로. 글상자에 든 변경 표지(`Change start` 따위)는 문단 표지처럼 뺀다.
            box = docx_text.box_text(elem, read=_body_paragraph_text)
            if box and not _is_change_marker(box):
                paragraphs.append(box)
        elif tag == "tbl":
            tbl_text = table_to_text(elem)
            if tbl_text:
                paragraphs.append(tbl_text)

    return paragraphs


# =============================================================================
# 4-Strategy 분류 & 청킹
# =============================================================================

def classify_strategy(body_tokens: int, heading_count: int) -> str:
    """Spec Step-3 §3.2: 4전략 분류."""
    if body_tokens < BODY_TOKEN_MIN:
        return "A"
    if body_tokens < BODY_TOKEN_SINGLE:
        return "B"
    if heading_count >= HEADING_MIN_FOR_C:
        return "C"
    return "D"


def split_by_tokens(paragraphs: list[str], target: int = SPLIT_TARGET,
                    overlap: int = SPLIT_OVERLAP) -> list[str]:
    """문단 경계에서 토큰 기반 분할. Phase-7 split_giant_section 패턴.

    Spec Step-3 상세 §3.2 전략 D: target 2K. overlap 200 은 README '청크를 나누는 전략'.
    """
    if not paragraphs:
        return []

    chunks = []
    current_paras: list[str] = []
    current_tokens = 0
    carried_tokens = 0  # current_paras 앞머리 가운데 앞 조각에서 넘겨받은 오버랩 토큰

    for para in paragraphs:
        para_tokens = count_tokens(para)

        # 주의: 앞 조각에 없던 글이 MIN_CHUNK_TOKENS 미만이면 끊지 않는다. 끊으면 넘겨받은 오버랩과 절 제목만
        # 든 조각이 생겨 새 정보 없이 검색 자리만 차지한다. 그 제목은 다음 문단과 한 조각이 되고, 커진 조각은
        # 저장 직전의 HARD_MAX 강제가 자른다.
        if (current_tokens + para_tokens > target and current_paras
                and current_tokens - carried_tokens >= MIN_CHUNK_TOKENS):
            chunks.append("\n".join(current_paras))

            # 오버랩: 마지막 문단들을 다음 청크에 포함
            overlap_paras: list[str] = []
            overlap_tokens = 0
            for p in reversed(current_paras):
                pt = count_tokens(p)
                if overlap_tokens + pt > overlap:
                    if not overlap_paras:
                        char_limit = overlap * 4
                        overlap_paras = [p[-char_limit:]]
                        overlap_tokens = count_tokens(overlap_paras[0])
                    break
                overlap_paras.insert(0, p)
                overlap_tokens += pt

            current_paras = overlap_paras + [para]
            current_tokens = overlap_tokens + para_tokens
            carried_tokens = overlap_tokens
        else:
            current_paras.append(para)
            current_tokens += para_tokens

    if current_paras:
        chunks.append("\n".join(current_paras))

    return chunks


def _merge_small_chunks(section_texts: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """MIN_CHUNK_TOKENS 미만 청크를 인접 청크에 병합.

    README '청크를 나누는 전략': 최소 청크 크기 50 토큰.
    소규모 청크는 이전 청크 뒤에 병합. 첫 청크이면 다음 청크 앞부분으로 병합.
    section_id는 병합 대상(큰 쪽) 것을 유지.
    """
    if len(section_texts) <= 1:
        return section_texts

    merged = []
    pending_text = ""  # 병합 대기 중인 소규모 텍스트

    for text, sec_id in section_texts:
        if pending_text:
            # 이전 소규모 청크를 현재 청크 앞에 병합
            text = pending_text + "\n" + text
            pending_text = ""

        if count_tokens(text) < MIN_CHUNK_TOKENS:
            if merged:
                # 이전 청크에 뒤로 병합
                prev_text, prev_id = merged[-1]
                merged[-1] = (prev_text + "\n" + text, prev_id)
            else:
                # 첫 번째 청크이면 다음으로 넘김
                pending_text = text
        else:
            merged.append((text, sec_id))

    # 마지막까지 pending이 남아있으면 마지막 청크에 병합
    if pending_text:
        if merged:
            prev_text, prev_id = merged[-1]
            merged[-1] = (prev_text + "\n" + pending_text, prev_id)
        else:
            # 모든 청크가 소규모인 극단적 경우 — 전부 합침
            merged.append((pending_text, section_texts[0][1] if section_texts else ""))

    return merged


def build_header_chunk(
    tdoc_number: str, spec_number: str, cr_number: str,
    reason: str, summary: str, consequences: str,
    meta: dict,
    body_snippet: str = "",
) -> CRChunk:
    """헤더 청크 생성 (README 'header 청크와 body 청크')."""
    # 헤더 청크 텍스트 템플릿 (README 'header 청크와 body 청크' · Spec Step-3 상세 §3.1.1)
    text = (
        f"[CR {cr_number} for {spec_number}]\n"
        f"Reason for change: {reason}\n"
        f"Summary of change: {summary}\n"
        f"Consequences if not approved: {consequences}"
    )
    # 전략 A 는 본문 청크가 없다. 본문(100 토큰 미만)을 머리 문장에 붙여야 변경 내용이 임베딩되어 검색된다.
    # 변경 표지 문단을 본문에서 빼면 B 였던 짧은 CR 이 A 로 내려오므로, 붙이지 않으면 그 본문이 검색에서 사라진다.
    if meta.get("strategy") == "A" and body_snippet:
        text += f"\nChange text: {body_snippet}"

    chunk = CRChunk(
        chunkId=f"{tdoc_number}-header",
        chunkType="header",
        tdocNumber=tdoc_number,
        specNumber=spec_number,
        crNumber=cr_number,
        category=meta.get("category", ""),
        workItem=meta.get("work_item", ""),
        meeting=meta.get("meeting", ""),
        source=meta.get("source", ""),
        title=meta.get("title", ""),
        clausesAffected=meta.get("clauses_affected_list", []),
        sectionIds=meta.get("section_ids", []),
        bodySnippet=body_snippet,  # 자르기는 호출부가 전략별로 한다(전략 A 는 본문 전체).
        crPackId=meta.get("cr_pack_id", ""),
        tsgMeeting=meta.get("tsg_meeting", ""),
        strategy=meta.get("strategy", ""),
        text=text,
        tokenCount=count_tokens(text),
    )
    return chunk


def section_ranges_of(headings: list[BodyHeading], n_elements: int) -> list[tuple[BodyHeading, int, int]]:
    """절마다 (제목, 시작, 끝). 끝은 다음 제목의 자리, 마지막 절은 본문 끝."""
    return [(h, h.index, headings[i + 1].index if i + 1 < len(headings) else n_elements)
            for i, h in enumerate(headings)]


def kept_body(
    body_elements: list[tuple[str, ET.Element]],
    body_start_idx: int,
    headings: list[BodyHeading],
    clauses_affected: list[str],
) -> tuple[list[bool], list[str]]:
    """절마다 남길지(제목 순서대로)와 남긴 본문 문단.

    > 주의: 변경 추적 표시가 있는 CR 에서 표시가 없는 절은 옮겨 적은 표준 글이라 청크로 만들지 않는다
    > (`cr_revision_marks`). 이 판정은 전략을 고르기 **전에** 하고, 전략은 남긴 본문으로 고른다. 전략 C 에서만
    > 빼면 같은 CR 이 본문 길이에 따라 B · D 로 갈 때 바꾸지 않은 표준 글이 그대로 청크에 들어간다. 첫 제목 앞의
    > 글은 늘 남긴다. 제목이 없으면 가를 절이 없으므로 본문을 모두 남긴다.
    """
    if not headings:
        return [], extract_body_text(body_elements, body_start_idx)
    ranges = section_ranges_of(headings, len(body_elements))
    keep = cr_revision_marks.changed_sections(
        body_elements, body_start_idx,
        [(h.section_number, start, end) for h, start, end in ranges], clauses_affected)
    paragraphs = extract_body_text(body_elements, body_start_idx, headings[0].index)
    for (h, start, end), k in zip(ranges, keep):
        if k:
            paragraphs.extend(extract_body_text(body_elements, start, end))
    return keep, paragraphs


def build_body_chunks(
    tdoc_number: str, spec_number: str, cr_number: str,
    strategy: str,
    body_elements: list[tuple[str, ET.Element]],
    body_start_idx: int,
    headings: list[BodyHeading],
    meta: dict,
    keep: list[bool],
    paragraphs: list[str],
) -> list[CRChunk]:
    """전략별 본문 청크 생성. `keep` · `paragraphs` 는 `kept_body` 의 결과다."""
    chunks = []

    if strategy == "A":
        # Strategy A: 본문 청크 없음
        return []

    elif strategy == "B":
        # Strategy B: 남긴 본문 → 1 청크
        # title + clausesAffected를 본문 앞에 붙인다. 검색 품질 효과는 별도 측정이 필요하다.
        text_body = "\n".join(paragraphs)
        clauses_str = meta.get("clauses_affected_text", "")
        title = meta.get("title", "")
        prefix = f"[CR {cr_number} for {spec_number}] {title}\nClauses affected: {clauses_str}" if title else f"[CR {cr_number} | {spec_number} | Clauses: {clauses_str}]"
        full_text = f"{prefix}\n{text_body}" if text_body else prefix
        chunk = _make_body_chunk(
            tdoc_number, spec_number, cr_number, meta,
            chunk_index=0, total_chunks=1, strategy="B",
            text=full_text,
        )
        chunks.append(chunk)

    elif strategy == "C":
        # Strategy C: Heading별 Section 분할
        # Heading 경계로 body를 분할
        section_ranges = section_ranges_of(headings, len(body_elements))

        # Heading 이전의 텍스트 (첫 heading 전)
        pre_heading_paras = extract_body_text(body_elements, body_start_idx, headings[0].index)
        pre_heading_text = "\n".join(pre_heading_paras).strip()

        all_section_texts = []

        # 첫 heading 이전 텍스트가 있으면 별도 청크
        # 짧아도 넣는다. 최소 크기 미만은 아래 _merge_small_chunks 가 이웃 청크에 붙인다
        # (여기서 먼저 버리면 그 본문이 어느 청크에도 들어가지 않는다).
        if pre_heading_text:
            prefix = f"[CR {cr_number} | {spec_number} | Preamble]"
            all_section_texts.append((f"{prefix}\n{pre_heading_text}", ""))

        # title prefix 강화
        title = meta.get("title", "")
        for (h, start, end), k in zip(section_ranges, keep):
            if not k:
                continue
            paragraphs = extract_body_text(body_elements, start, end)
            section_text = "\n".join(paragraphs)
            section_id = f"{spec_number}-{h.section_number}" if h.section_number else ""
            if h.section_number:
                prefix = f"[CR {cr_number} for {spec_number}] {title}\nSection {h.section_number}" if title else f"[CR {cr_number} | {spec_number} | Section {h.section_number}]"
            else:
                prefix = f"[CR {cr_number} for {spec_number}] {title}" if title else f"[CR {cr_number} | {spec_number}]"
            full_text = f"{prefix}\n{section_text}" if section_text else prefix

            # Section 내 토큰 초과 시 추가 분할
            if count_tokens(full_text) > SPLIT_TARGET * 2:
                sub_chunks = split_by_tokens(paragraphs, SPLIT_TARGET, SPLIT_OVERLAP)
                for sc in sub_chunks:
                    all_section_texts.append((f"{prefix}\n{sc}", section_id))
            else:
                all_section_texts.append((full_text, section_id))

        # README '청크를 나누는 전략': MIN_CHUNK_TOKENS 미만 청크를 인접 청크에 병합
        all_section_texts = _merge_small_chunks(all_section_texts)

        total = len(all_section_texts)
        for i, (text, sec_id) in enumerate(all_section_texts):
            chunk = _make_body_chunk(
                tdoc_number, spec_number, cr_number, meta,
                chunk_index=i, total_chunks=total, strategy="C",
                text=text, chunkSectionId=sec_id,
            )
            chunks.append(chunk)

    elif strategy == "D":
        # Strategy D: 남긴 본문을 토큰 기반 분할
        # title prefix 강화
        sub_chunks = split_by_tokens(paragraphs, SPLIT_TARGET, SPLIT_OVERLAP)
        total = len(sub_chunks)
        title = meta.get("title", "")
        for i, sc in enumerate(sub_chunks):
            prefix = f"[CR {cr_number} for {spec_number}] {title}\nPart {i+1}/{total}" if title else f"[CR {cr_number} | {spec_number} | Part {i+1}/{total}]"
            full_text = f"{prefix}\n{sc}"
            chunk = _make_body_chunk(
                tdoc_number, spec_number, cr_number, meta,
                chunk_index=i, total_chunks=total, strategy="D",
                text=full_text,
            )
            chunks.append(chunk)

    return chunks


def _make_body_chunk(
    tdoc_number: str, spec_number: str, cr_number: str,
    meta: dict, chunk_index: int, total_chunks: int,
    strategy: str, text: str, chunkSectionId: str = "",
) -> CRChunk:
    """본문 청크 생성 헬퍼."""
    return CRChunk(
        chunkId=f"{tdoc_number}-body-{chunk_index:03d}",
        chunkType="body",
        tdocNumber=tdoc_number,
        specNumber=spec_number,
        crNumber=cr_number,
        category=meta.get("category", ""),
        workItem=meta.get("work_item", ""),
        meeting=meta.get("meeting", ""),
        source=meta.get("source", ""),
        clausesAffected=meta.get("clauses_affected_list", []),
        sectionIds=meta.get("section_ids", []),
        chunkSectionId=chunkSectionId,
        chunkIndex=chunk_index,
        totalChunks=total_chunks,
        strategy=strategy,
        text=text,
        tokenCount=count_tokens(text),
    )


# =============================================================================
# 파일명 파싱
# =============================================================================

def parse_filename(filename: str) -> tuple[str, str, str] | None:
    """파일명에서 (specNumber, crNumber, tdocNumber) 추출.

    예: 38133_CR0505_(Rel-16)_R4-2071640.docx → ("38.133", "CR0505", "R4-2071640")
    """
    m = FILENAME_RE.search(filename)
    if not m:
        return None
    raw_spec = m.group(1)  # "38133" or "38101-1"
    if "-" in raw_spec:
        parts = raw_spec.split("-")
        spec_number = f"{parts[0][:2]}.{parts[0][2:]}-{parts[1]}"
    else:
        spec_number = f"{raw_spec[:2]}.{raw_spec[2:]}"
    cr_number = f"CR{m.group(2)}"  # "CR0675"
    tdoc_number = m.group(3)  # "R4-2071640"
    return spec_number, cr_number, tdoc_number


_identity: cr_identity.CRIdentity | None = None


def identity() -> cr_identity.CRIdentity:
    """CR 식별자는 Phase-4 기록에서 받고, 기록이 없는 파일만 `parse_filename` 으로 읽는다."""
    global _identity
    if _identity is None:
        _identity = cr_identity.CRIdentity("RAN4", PHASE4_DIR, INPUT_DIR, parse_filename)
    return _identity


# =============================================================================
# clausesAffected → sectionIds 매핑
# =============================================================================

def clauses_to_section_ids(clauses_str: str, spec_number: str) -> tuple[list[str], list[str]]:
    """clausesAffected 문자열 → (clauses_list, sectionIds_list).

    Spec Step-3 상세 §3.7.1: "5.1.2.1, 5.1.3.2" → ["5.1.2.1", "5.1.3.2"], ["38.214-5.1.2.1", "38.214-5.1.3.2"]

    칸은 Phase-4 가 CR → Section 간선을 만들 때 쓰는 `cr_clause.clause_candidates` 로 읽는다.
    두 단계가 같은 칸을 다르게 끊으면 이 청크의 sectionIds 와 그래프의 간선이 서로 다른 절을
    가리킨다. 이 함수가 따로 정규식으로 읽을 때는 부속서 절(`A.3.18` · `Annex A`)과 머리말이
    붙은 번호(`Section 8.1` · `New (4.7)`)가 빠지고, 글자가 낀 번호가 잘리고(`5.5a.3.2` → `5.5a`),
    아직 번호가 없는 새 절이 부모 절로 바뀌었다(`9.2.x` → `9.2`).

    `clause_candidates` 는 절마다 철자 후보를 긴 것부터 낸다(`A.1-1` → `A.1-1`, `A.1`). Phase-4 는
    Section 색인에서 처음 걸리는 후보를 고르지만 이 단계에는 색인이 없다. 그래서 절 번호 꼴인
    후보 가운데 마지막 것, 곧 꼬리를 뗀 머리를 고른다. 칸에 적힌 `A.5.5.5.1.1-3` 같은 꼬리 붙은
    꼴은 TS 절 제목으로 거의 서지 않고 머리 쪽이 절로 선다.

    ASN.1 정의명 후보(`RadioBearerConfig`)는 넣지 않는다. 같은 꼴의 낱말(`New` · `General`)과
    가르는 일은 Section 색인만 할 수 있고, sectionIds 를 맞대는 Phase-7 TS 청크에는 이름으로 선
    절이 없다.
    """
    if not clauses_str:
        return [], []

    clauses = []
    for candidates in clause_candidates(clauses_str):
        # 이름 후보는 절 번호 문법을 통과하지 못해 여기서 빠진다.
        numbers = [c for c in candidates if tsn.is_section_number(c)]
        if numbers:
            clauses.append(numbers[-1])

    clauses = list(dict.fromkeys(clauses))  # 중복 제거 (순서 유지)
    section_ids = [f"{spec_number}-{c}" for c in clauses]
    return clauses, section_ids


# =============================================================================
# 단일 CR 파싱
# =============================================================================

def parse_single_cr(
    docx_path: Path,
    cover_map: dict,
    cr_doc_map: dict,
    extra: tuple[Path, ...] = (),
    omitted: list[str] | None = None,
    *, source_identity: tuple[str, str, str] | None = None,
) -> list[CRChunk]:
    """단일 CR DOCX 파싱 → 청크 리스트. `extra` 는 이 CR 본문이 이어지는 파일(`cr_attachments.continuations`)."""
    parsed = source_identity if source_identity is not None else identity().resolve(docx_path)
    if not parsed:
        log.warning(f"  식별자 없음 (Phase-4 기록 · 파일명 둘 다 없음): {docx_path.name}")
        return []

    spec_number, cr_number, tdoc_number = parsed
    from tdoc_body_source_metadata import validate_source_selection
    validate_source_selection(PROJECT_ROOT, WG, 'cr', tdoc_number, [docx_path])

    # Phase-4 메타데이터 조회. CR 팩은 Phase-4 기록이 고른 팩이고, 표지 칸과 TSG 회의도 그 팩에서 읽는다.
    # 주의: 한 CR 이 두 팩 표지에 실리면 tdoc 하나로 찾은 표지는 마지막에 읽은 팩의 것이다. RAN1 RAN#108 의
    # `R1-2504980` 은 RP-251576 과 RP-251836 표지에 함께 실리고, CR 시트는 앞 팩에 `reissued`, 뒤 팩에
    # `approved` 를 둔다. Phase-4 는 `tsg_cr_decision` 으로 팩을 고르므로 그 기록을 따른다.
    # tdoc 하나로 찾는 것은 Phase-4 기록이 없는 파일뿐이다.
    cr_doc = cr_doc_map.get(tdoc_number, {})
    pack_id = cr_doc.get("cr_pack_id", "")
    # 주의: CR 번호는 파일 이름에서 먼저 읽는데(`cr_identity`) 파일 이름의 번호가 틀린 CR 이 있다. RAN1
    # `R1-2207990` 의 파일 이름은 `38215_CR0296`, CR 서식과 CR 시트는 38.215 CR0045 다(CR0296 은 같은 회의
    # 38.214 CR `R1-2207996` 의 번호). 시트에 이 쌍이 있으면 시트 번호로 맞춘다(`tsg_cr_decision.sheet_cr_label`).
    # Phase-4 기록의 번호도 같은 시트 값이다.
    cr_number = tsg_cr_decision.sheet_cr_label(cr_number, tdoc_number, pack_id)
    if pack_id:
        cover = cover_map.get((pack_id, tdoc_number), {})
        pack_cover = cover_map.get((pack_id, ""), {})
    else:
        cover = pack_cover = cover_map.get(tdoc_number, {})

    # (reserved)/빈 title 필터링 (개선 2 — 검색 노이즈 제거)
    # Phase-4 메타데이터에서 title 가져와서 판단
    _title_check = cover.get("title", "") or cr_doc.get("title", "")
    if _title_check and any(skip in _title_check.lower() for skip in ["(reserved)", "(void)", "(spare)", "(withdrawn)"]):
        log.debug(f"  SKIP: {tdoc_number} title='{_title_check[:50]}' (reserved/void)")
        return []


    # 메타데이터 취합
    reason = cr_doc.get("reason_for_change", "") or ""
    summary = cr_doc.get("summary_of_change", "") or ""
    consequences = cr_doc.get("consequences_if_not_approved", "") or ""

    # 주의: 영향 절은 CR 양식 값을 먼저 쓰고, 양식 값이 비었을 때만 표지 값을 쓴다. 표지 docx 는 절 번호와
    # 제목이 붙은 글자(「5.3.5.2Initiation」)나 일부 절만 담는 경우가 있어 표지를 먼저 쓰면 절이 사라지거나
    # 틀어지고, KG(03_generate_cr_jsonld.py)는 양식 값만 쓰므로 Qdrant 와 KG 가 어긋난다.
    clauses_str = cr_doc.get("clauses_affected", "") or cover.get("clauses_affected", "") or ""
    clauses_list, section_ids = clauses_to_section_ids(clauses_str, spec_number)

    meta = {
        "category": cover.get("category", "") or cr_doc.get("category", ""),
        "work_item": cover.get("work_item", "") or cr_doc.get("work_item", ""),
        "meeting": cover.get("meeting", ""),
        "source": cover.get("source", "") or cr_doc.get("source", ""),
        "title": cover.get("title", "") or cr_doc.get("title", ""),
        "cr_pack_id": pack_id or cover.get("cr_pack_id", ""),
        "tsg_meeting": pack_cover.get("tsg_meeting", ""),
        "clauses_affected_list": clauses_list,
        # 머리 글에는 표지에 적힌 그대로를 싣는다. 절 목록은 절 번호 문법을 통과한 것만 남아 새 절(`9.2.x (new)`) ·
        # `ASN.1` · `All` 같은 칸이 빠지고, 그 글이 검색에서 사라진다. RAN5 는 처음부터 적힌 그대로를 싣는다.
        "clauses_affected_text": " ".join(clauses_str.split()),
        "section_ids": section_ids,
    }

    # XML-level body 파싱
    body_elements = parse_body_xml(docx_path)
    if not body_elements:
        log.warning(f"  Body 파싱 실패: {docx_path.name}")
        return []

    # Part 1/Part 2 분리
    last_form_idx = find_last_form_table_index(body_elements)
    body_start_idx = last_form_idx + 1 if last_form_idx >= 0 else 0
    # 주의: 이어지는 본문 파일은 서식이 든 파일의 본문 뒤에 읽을 차례대로 붙인다. 서식 표는 서식이 든 파일에만
    # 있으므로 서식 경계는 붙이기 전에 정한다. 붙인 파일의 표를 서식 표로 잘못 보면 앞 본문이 통째로 빠진다.
    for f in extra:
        body_elements.extend(parse_body_xml(f))

    # Heading 탐지
    headings = detect_headings(body_elements, body_start_idx)

    # 바꾸지 않은 절을 뺀 본문으로 토큰을 세고 전략을 고른다. 뺀 절은 `omitted` 로 돌려 parse_stats.json 에
    # CR 별로 남긴다.
    # 주의: 자리표시 새 절(`8.7.X`)은 절 목록에 들지 않지만 보존 판정에는 넘긴다. 새 절이 들어갈 자리의 위 절 제목이
    # 청크 글에 남는다(`cr_clause.placeholder_clauses`).
    # 주의: 범위로 적힌 절(`2-11`)의 가운데 절도 보존 판정에만 넘긴다. 양 끝만 넘기면 표시 없는 가운데 절이 빠진다
    # (`cr_clause.range_clauses`).
    keep, body_paragraphs = kept_body(body_elements, body_start_idx, headings,
                                      meta.get("clauses_affected_list", []) + placeholder_clauses(clauses_str)
                                      + range_clauses(clauses_str, (h.section_number for h in headings)))
    if omitted is not None:
        omitted.extend(h.section_number or h.text.strip() for h, k in zip(headings, keep) if not k)
    body_text = "\n".join(body_paragraphs)
    body_tokens = count_tokens(body_text)

    # 전략 분류
    strategy = classify_strategy(body_tokens, sum(keep))
    meta["strategy"] = strategy

    # 헤더 청크
    # 전략 A 는 본문 청크가 없어 본문이 bodySnippet 에만 남는다. 200자로 자르면 나머지가 어디에도 남지 않는다.
    body_snippet = (body_text if strategy == "A" else body_text[:200]) if body_text else ""
    header_chunk = build_header_chunk(
        tdoc_number, spec_number, cr_number,
        reason, summary, consequences,
        meta, body_snippet,
    )

    # 본문 청크
    body_chunks = build_body_chunks(
        tdoc_number, spec_number, cr_number,
        strategy, body_elements, body_start_idx,
        headings, meta, keep, body_paragraphs,
    )

    # 본문 청크 total_chunks 업데이트 (body_chunks가 확정된 후)
    total_body = len(body_chunks)
    for bc in body_chunks:
        bc.totalChunks = total_body

    return [header_chunk] + body_chunks


# =============================================================================
# 파일 수집
# =============================================================================

def collect_cr_files(cover_map: dict, cr_doc_map: dict) -> tuple[list[Path], dict[str, list[Path]]]:
    """CR DOCX 수집 — tdocNumber 기준 중복 제거.

    3GPP CRPack은 같은 CR DOCX를 여러 Release 폴더에 중복 배포한다.
    (예: 같은 R4 TDoc이 Rel-15/, Rel-18/ 양쪽에 존재)
    tdocNumber 기준으로 최초 발견 파일만 유지하여 중복 파싱을 방지한다.
    교훈 24 참조: docs/common/process/implementation_process.md

    돌려주는 값은 (청크를 만들 파일, {CR 번호: 그 CR 본문이 이어지는 파일})이다.
    """
    # 주의: 파일 이름의 WG 번호가 다른 WG 인 CR 은 그 WG 가 읽고, 다른 WG 슬롯에 놓인 이 WG 의 CR 은
    # 여기서 읽는다(`cr_other_wg`). 슬롯만 보면 놓인 WG 는 식별자 없는 파일로, 만든 WG 는 빠진 CR 로 센다.
    files, unconverted, other_wg = cr_other_wg.collect("RAN4")
    if other_wg:
        log.info(f"  다른 WG 번호의 CR 제외(그 WG 가 읽음): {len(other_wg)}개")
    all_files = [f for f, _ in cr_inputs.without_covers(files)]
    # Phase-4 가 팩 안 CR 폴더의 첨부 문서로 가린 파일은 CR 이 아니다(`cr_attachments`).
    attachments = cr_attachments.recorded_attachments(PHASE4_DIR / "cr_documents.json")
    if attachments:
        before = len(all_files)
        all_files = [f for f in all_files if str(f.relative_to(PROJECT_ROOT)) not in attachments]
        log.info(f"  팩 CR 폴더의 첨부 문서 제외: {before - len(all_files)}개")
    # 주의: Phase-4 가 CR 서식이 없어 CR 기록에서 뺀 문서(`cr_attachments.split_no_form`)는 팩 안에 놓였어도 CR 이
    # 아니므로 청크로 만들지 않는다. 번호가 아니라 경로로 가린다. 이름에 CR 번호가 없는 문서는 Phase-4 기록이 빠지면
    # 식별자를 얻지 못하고, 표지가 번호를 두는 문서는 표지 행으로 식별되어 CR 본문이 아닌 글이 청크가 되기 때문이다.
    no_form = cr_attachments.recorded_no_form(PHASE4_DIR / "cr_documents.json")
    if no_form:
        before = len(all_files)
        all_files = [f for f in all_files if str(f.relative_to(PROJECT_ROOT)) not in no_form]
        log.info(f"  CR 서식이 없는 문서 제외: {before - len(all_files)}개")
    if unconverted:
        log.warning(f"  읽을 수 없는 문서(변환본 없는 .doc · ZIP 아닌 .docx) {len(unconverted)}개 — 읽지 못한 CR")

    # tdocNumber 기준 dedup. 같은 CR 의 사본 중 Phase-4 가 기록한 파일을 남긴다.
    ident = identity()
    required = cr_inputs.selected_unconverted(files, unconverted, project_root=PROJECT_ROOT,
        excluded_paths=set(attachments) | set(no_form), resolve=ident.resolve)
    if required:
        raise ValueError("선택한 CR의 변환본이 없거나 문서를 열 수 없습니다: "
                         + ", ".join(str(p.relative_to(PROJECT_ROOT)) for p in required))
    seen_tdocs: dict[str, Path] = {}
    dir_tdocs: dict[Path, set[str]] = {}
    unresolved: list[Path] = []
    for f in all_files:
        parsed = ident.resolve(f)
        tdoc_key = parsed[2] if parsed else f.name
        if parsed:
            dir_tdocs.setdefault(f.parent, set()).add(tdoc_key)
        else:
            unresolved.append(f)
        kept = seen_tdocs.get(tdoc_key)
        if kept is None or (ident.recorded(f) and not ident.recorded(kept)):
            seen_tdocs[tdoc_key] = f

    dedup_count = len(all_files) - len(seen_tdocs)
    if dedup_count > 0:
        log.info(f"  DOCX dedup: {len(all_files)} → {len(seen_tdocs)} ({dedup_count}건 중복 제거)")

    # 주의: 큰 CR 은 본문을 한 CR 폴더의 여러 파일로 나눈다(`cr_attachments` 모듈 설명의 R4-1902690). 곁 파일은
    # 식별자를 얻지 못하므로 따로 읽으면 실패로 남고 CR 본문의 부속서 변경이 빠진다. 그 파일은 CR 하나의 본문으로
    # 붙여 읽고 입력 목록에서는 뺀다. 영향 절은 표지 칸, 없으면 Phase-4 기록의 칸이다(`parse_single_cr` 과 같은 차례).
    resolved = set().union(*dir_tdocs.values())
    kept = {t: f for t, f in seen_tdocs.items() if t in resolved}
    clauses = {t: (cr_doc_map.get(t, {}).get("clauses_affected") or cover_map.get(t, {}).get("clauses_affected") or "")
               for t in kept}
    cont = cr_attachments.continuations(kept, dir_tdocs, unresolved, clauses)
    joined = {f for fs in cont.values() for f in fs}
    if joined:
        log.info(f"  이어지는 CR 본문 파일: {len(joined)}개(CR {len(cont)}건)")

    return [f for f in seen_tdocs.values() if f not in joined], cont


# =============================================================================
# 메인
# =============================================================================

# 청크 글 첫머리의 CR 문맥 표지. `build_header_chunk` 는 `[CR x for spec]`, `build_body_chunks` 는
# `[CR x | spec | ...]` 를 붙이고, RAN4 는 제목이 있으면 `[CR x for spec] 제목` 다음 줄에 전략별 표지를 둔다.
_CR_TITLE_HEAD_RE = re.compile(r"\[CR [^\]\n]* for [^\]\n]*\] ")
_CR_PART_LINE_RE = re.compile(r"Part \d+/\d+")
_CR_PART_TAIL_RE = re.compile(r"\| Part \d+/\d+\]$")
_CR_SECOND_LINE = {
    "B": re.compile(r"Clauses affected: .*"),
    "C": re.compile(r"Section \S+"),
    "D": _CR_PART_LINE_RE,
}


def _cr_prefix(chunk: dict) -> str:
    """청크 글 맨 앞의 CR 문맥 표지. 표지가 없으면 빈 문자열."""
    text = chunk.get("text") or ""
    if not text.startswith("[CR "):
        return ""
    lines = text.split("\n", 2)
    head = lines[0]
    if chunk.get("chunkType") != "header" and len(lines) > 1 and _CR_TITLE_HEAD_RE.match(head):
        rule = _CR_SECOND_LINE.get(chunk.get("strategy", ""))
        if rule and rule.fullmatch(lines[1]):
            head = f"{head}\n{lines[1]}"
    if len(text) > len(head) and text[len(head)] != "\n":
        return ""
    return head


def _relabel_part(text: str, pos: int, total: int) -> str:
    """전략 D 표지의 `Part i/N` 을 최종 본문 순번 · 개수로 고쳐 쓴다. 표지가 없으면 그대로 둔다."""
    head, sep, rest = text.partition("\n")
    if _CR_PART_TAIL_RE.search(head):
        return _CR_PART_TAIL_RE.sub(f"| Part {pos}/{total}]", head) + sep + rest
    if _CR_TITLE_HEAD_RE.match(head):
        second, sep2, tail = rest.partition("\n")
        if _CR_PART_LINE_RE.fullmatch(second):
            return f"{head}\n{f'Part {pos}/{total}'}{sep2}{tail}"
    return text


def _harden_keep_prefix(group: list[dict]) -> list[dict]:
    """한 CR 의 머리 청크 또는 본문 청크 목록에 HARD_MAX 를 걸되, 쪼갠 조각마다 CR 문맥 표지를 다시 붙인다.

    공통 `enforce_hard_max` 는 글을 그대로 잘라 첫 조각만 표지를 지니고, 나머지 조각은 어느 CR · 어느 규격 ·
    어느 절의 글인지 모른 채 임베딩된다. 그래서 쪼갤 청크는 표지를 떼고, 표지 토큰만큼 줄인 한도로 나머지를
    쪼갠 뒤 조각마다 표지를 앞에 붙인다. 조각 ID · 자리표는 `enforce_hard_max` 와 같은 규칙으로 매긴다
    (부모 ID 에 `-NNN` 을 붙이고 겹치면 다음 번호, 목록 전체를 시작값부터 다시 매김). 전략 D 의 `Part i/N` 은
    다시 매긴 본문 순번 · 개수로 고친다. 고치지 않으면 표지의 순번이 chunkIndex · totalChunks 와 어긋난다.

    한도를 넘는 청크가 하나도 없는 목록은 `enforce_hard_max` 에 그대로 넘긴다(글 · ID · 자리표가 바뀌지
    않아야 다시 임베딩하지 않는다). 표지를 붙인 조각이나 순번을 고친 청크가 한도를 넘으면, 넘친 만큼
    그 청크의 한도를 줄여 다시 쪼갠다.
    """
    sizes = [_count_tokens_exact(c.get("text") or "") for c in group]
    if all(s <= _HARD_MAX_TOK for s in sizes):
        return _enforce_hard_max(group, hard_max=_HARD_MAX_TOK)

    base = _index_base(group)
    reserved = {c["chunkId"] for c in group if isinstance(c.get("chunkId"), str)}
    prefixes = [_cr_prefix(c) for c in group]
    limits = {i: _HARD_MAX_TOK - _count_tokens_exact(prefixes[i]) for i, s in enumerate(sizes) if s > _HARD_MAX_TOK}
    while True:
        final: list[dict] = []
        parents: list[int] = []
        generated: set[str] = set()
        for i, (chunk, tok) in enumerate(zip(group, sizes)):
            if i not in limits:
                kept = dict(chunk)
                kept["tokenCount"] = tok
                final.append(kept)
                parents.append(i)
                continue
            prefix = prefixes[i]
            text = chunk.get("text") or ""
            rest = text[len(prefix) + 1:] if prefix else text
            pieces = [p["text"] for p in _enforce_hard_max([dict(chunk, text=rest)], hard_max=limits[i])]
            # 끝에 남은 작은 조각은 이웃 조각에 원문 그대로 합친다(`cr_split_pieces`).
            pieces = cr_split_pieces.merge_small_pieces(rest, pieces, limits[i], MIN_CHUNK_TOKENS,
                                                        _count_tokens_exact)
            if prefix:
                pieces = [f"{prefix}\n{p}" for p in pieces]
            chunk_id = chunk.get("chunkId", "") or "chunk"
            for idx, piece in enumerate(pieces, 1):
                new_id = chunk_id
                if len(pieces) > 1:
                    suffix = idx
                    new_id = f"{chunk_id}-{suffix:03d}"
                    while new_id in reserved or new_id in generated:
                        suffix += 1
                        new_id = f"{chunk_id}-{suffix:03d}"
                generated.add(new_id)
                sub = dict(chunk)
                sub["text"] = piece
                sub["chunkId"] = new_id
                sub["chunkIndex"] = idx
                sub["totalChunks"] = len(pieces)
                sub["tokenCount"] = _count_tokens_exact(piece)
                sub["_hardMaxEnforced"] = True
                sub["_originalTokenCount"] = tok
                final.append(sub)
                parents.append(i)
        _renumber_chunk_indices(final, base=base)
        for c in final:
            if c.get("strategy") == "D" and c.get("chunkType") != "header":
                relabeled = _relabel_part(c["text"], c["chunkIndex"] - base + 1, c["totalChunks"])
                if relabeled != c["text"]:
                    c["text"] = relabeled
                    c["tokenCount"] = _count_tokens_exact(relabeled)
        over: dict[int, int] = {}
        for c, i in zip(final, parents):
            if c["tokenCount"] > _HARD_MAX_TOK:
                over[i] = max(over.get(i, 0), c["tokenCount"] - _HARD_MAX_TOK)
        if not over:
            return final
        for i, excess in over.items():
            limits[i] = limits.get(i, _HARD_MAX_TOK - _count_tokens_exact(prefixes[i])) - excess


def _harden_per_cr(chunk_dicts: list[dict]) -> list[dict]:
    """HARD_MAX 강제를 CR 하나씩, 머리 청크와 본문 청크에 따로 건다.

    Spec §3.4.2 의 본문 청크 순서 · 개수(이 파서가 chunkIndex · totalChunks 로 적는 값)는 그 CR 본문 안의
    것이다. 공통 `enforce_hard_max` 는 하나라도 쪼개면 받은 목록 전체에 번호를 다시 매기므로(번호 단위는
    호출자가 고른다), 모든 CR 을 한 목록으로 넘기면 한 CR 만 쪼개져도 다른 CR 의 번호가 전체 목록 기준으로
    바뀐다. CR 은 청크 ID 를 만드는 `tdocNumber` 로 가른다. 파서는 CR 마다 [머리] + 본문을 이어 붙이므로
    이웃한 같은 키를 한 CR 로 묶는다.
    쪼갤 청크의 조각마다 CR 문맥 표지를 다시 붙이는 일은 `_harden_keep_prefix` 가 맡는다.
    """
    out: list[dict] = []
    for _, group in itertools.groupby(chunk_dicts, key=lambda c: c.get("tdocNumber")):
        group = list(group)
        out.extend(_harden_keep_prefix([c for c in group if c.get("chunkType") == "header"]))
        out.extend(_harden_keep_prefix([c for c in group if c.get("chunkType") != "header"]))
    return out


def main():
    configure_logging()
    log.info("=" * 60)
    log.info("Phase-8 Step-1: CR 변경 본문 파싱 + 4-Strategy 청킹")
    log.info("=" * 60)

    # 1. Phase-4 메타데이터 로드
    log.info("\n[1] Phase-4 메타데이터 로드")
    cover_map, cr_doc_map = load_phase4_metadata()

    # 2. CR 파일 수집
    log.info("\n[2] CR 파일 수집")
    try:
        cr_files, continuations = collect_cr_files(cover_map, cr_doc_map)
    except ValueError as error:
        log.error("%s. 기존 청크/통계 출력을 보존합니다", error)
        return 1
    log.info(f"  CR DOCX 파일: {len(cr_files)}개")

    if not cr_files:
        log.error("  CR 파일 없음. 종료.")
        return 1

    # 3. 파싱
    log.info("\n[3] CR 파싱 시작")
    all_chunks: list[CRChunk] = []
    strategy_counts = {"A": 0, "B": 0, "C": 0, "D": 0}
    errors = []
    # 변경 표시 없는 절을 뺀 CR 과 뺀 절(`cr_revision_marks`). parse_stats.json 에 남긴다.
    unchanged_omitted: list[dict] = []
    unidentified: list[Path] = []  # CR 식별자를 얻지 못한 파일. 루프 뒤에 CR 이 아닌 문서와 실패로 가른다.

    for i, cr_path in enumerate(cr_files):
        try:
            parsed = identity().resolve(cr_path)
            extra = tuple(continuations.get(parsed[2], ())) if parsed else ()
            omitted: list[str] = []
            chunks = parse_single_cr(cr_path, cover_map, cr_doc_map, extra, omitted=omitted)
            if chunks:
                if omitted:
                    unchanged_omitted.append({"tdocNumber": chunks[0].tdocNumber, "specNumber": chunks[0].specNumber, "sections": omitted})
                # strategy 집계 (헤더 청크의 strategy)
                header = chunks[0]
                s = header.strategy
                if s in strategy_counts:
                    strategy_counts[s] += 1
                all_chunks.extend(chunks)
                body_count = len(chunks) - 1
                log.info(f"  [{i+1}/{len(cr_files)}] {cr_path.name}: "
                         f"strategy={s}, header=1, body={body_count}")
            elif identity().resolve(cr_path) is None:
                unidentified.append(cr_path)
            else:
                errors.append(cr_path.name)
                log.warning(f"  [{i+1}/{len(cr_files)}] {cr_path.name}: 파싱 실패")
        except Exception as e:
            errors.append(f"{cr_path.name}: {e}")
            log.error(f"  [{i+1}/{len(cr_files)}] {cr_path.name}: {e}")

    # 식별자 없는 파일 가운데 TSG 직접 제출 문서와 청크를 낸 CR 폴더의 첨부는 CR 이 아니다(`cr_attachments`).
    not_cr, unexplained = cr_attachments.split_unidentified(
        [str(p.relative_to(PROJECT_ROOT)) for p in unidentified], PHASE4_DIR / "cr_documents.json",
        {c.tdocNumber for c in all_chunks}, _FOLDER_TDOC_RE)
    errors.extend(f"{Path(p).name}: 식별자 없음" for p in unexplained)
    not_cr[cr_attachments.NO_FORM_KEY] = sorted(
        cr_attachments.recorded_no_form(PHASE4_DIR / "cr_documents.json"))
    log.info(f"  CR 이 아닌 문서: TSG 직접 제출 {len(not_cr['tsg_direct'])}개 · "
             f"CR 폴더 첨부 {len(not_cr['folder_attachment'])}개 · "
             f"CR 서식 없음 {len(not_cr[cr_attachments.NO_FORM_KEY])}개")

    if errors:
        log.error("선택한 CR 파싱 실패 %d건 — 기존 청크/통계 출력을 보존합니다", len(errors))
        return 1

    # 4. 통계
    header_chunks = [c for c in all_chunks if c.chunkType == "header"]
    body_chunks = [c for c in all_chunks if c.chunkType == "body"]

    log.info("\n" + "=" * 60)
    log.info("파싱 결과 요약")
    log.info("=" * 60)
    log.info(f"  CR 입력: {len(cr_files)}개")
    log.info(f"  총 청크: {len(all_chunks)}개 (헤더 {len(header_chunks)} + 본문 {len(body_chunks)})")
    log.info("  전략 분포:")
    for s, cnt in sorted(strategy_counts.items()):
        log.info(f"    {s}: {cnt}개")
    log.info(f"  에러: {len(errors)}개")
    log.info(f"  변경 표시 없는 절 제외: CR {len(unchanged_omitted)}개 · "
             f"절 {sum(len(e['sections']) for e in unchanged_omitted)}개")

    if body_chunks:
        body_tokens = sum(c.tokenCount for c in body_chunks)
        header_tokens = sum(c.tokenCount for c in header_chunks)
        log.info(f"  본문 토큰 합계: {body_tokens:,}")
        log.info(f"  헤더 토큰 합계: {header_tokens:,}")
        log.info(f"  본문 청크 평균: {body_tokens // len(body_chunks)} tok/chunk")

    # 4.5 HARD_MAX 강제 (정규 프로세스 hardening)
    _chunk_dicts = [asdict(c) for c in all_chunks]
    _pre_count = len(_chunk_dicts)
    _chunk_dicts = _harden_per_cr(_chunk_dicts)
    from tdoc_classification_views import (extra_phase8_sources, phase4_records,
                                           phase8_classified_chunks)
    source_rows = extra_phase8_sources(sys.modules[__name__], cr_files)
    source_chunks = phase8_classified_chunks(sys.modules[__name__], source_rows,
        phase4_records(sys.modules[__name__]), existing_tdocs={c['tdocNumber'] for c in _chunk_dicts})
    _chunk_dicts.extend(source_chunks)
    for target in {c['tdocNumber'] for c in source_chunks}:
        strategy_counts[next(c['strategy'] for c in source_chunks if c['tdocNumber'] == target)] += 1
    if len(_chunk_dicts) != _pre_count:
        log.info(f"  HARD_MAX hardening: {_pre_count} → {len(_chunk_dicts)} chunks (force-split 적용)")

    # 통계는 hardening 후 실제 산출 청크 기준으로 집계 → 파일 내용과 항상 일치.
    # (거대한 요약을 담은 헤더도 force-split 되므로 헤더 수도 바뀔 수 있다.)
    final_header = sum(1 for c in _chunk_dicts if c.get("chunkType") == "header")
    final_body = sum(1 for c in _chunk_dicts if c.get("chunkType") == "body")

    # 입력이 있는데 청크가 하나도 없으면 이 실행은 실패다. 앞 세대 출력은 그대로 둔다.
    # 덮어쓰면 다음 적재와 Phase-11 CR-2 가 빈 세대를 정상 결과로 받는다.
    if not _chunk_dicts:
        log.error(f"  CR 파일 {len(cr_files)}개에서 청크를 하나도 만들지 못함. 앞 세대 출력을 두고 실패로 끝낸다.")
        return 1

    from tdoc_body_source_metadata import project as project_body_source_metadata
    _chunk_dicts = [project_body_source_metadata(PROJECT_ROOT, WG, 'cr', c['tdocNumber'], c)
                    for c in _chunk_dicts]

    # 5. JSON 출력
    output = {
        "metadata": {
            "total_cr_files": len(cr_files) + len(source_rows),
            "total_chunks": len(_chunk_dicts),
            "header_chunks": final_header,
            "body_chunks": final_body,
            "strategy_distribution": strategy_counts,
            "errors": len(errors),
            "notCr": {k: len(v) for k, v in not_cr.items()},
            "continuations": sum(len(v) for v in continuations.values()),
            "strictPartsRead": docx_text.strict_parts_read(),
            "unchangedSectionsOmitted": sum(len(e["sections"]) for e in unchanged_omitted),
            "sourceClassifiedDocuments": sorted({c['tdocNumber'] for c in source_chunks}),
        },
        "chunks": _chunk_dicts,
    }

    output_path = OUTPUT_DIR / "ran4_cr_chunks.json"
    write_json_atomic(output_path, output)

    log.info(f"\n출력: {output_path}")
    log.info(f"파일 크기: {output_path.stat().st_size / 1024:.1f} KB")

    # 통계 JSON
    stats = {
        "total_cr_files": len(cr_files) + len(source_rows),
        "total_chunks": len(_chunk_dicts),
        "header_chunks": final_header,
        "body_chunks": final_body,
        "strategy_distribution": strategy_counts,
        "notCr": not_cr,
        "continuations": {t: [str(f.relative_to(PROJECT_ROOT)) for f in fs] for t, fs in sorted(continuations.items())},
        "errors": errors,
        "unchangedSectionsOmitted": unchanged_omitted,
    }
    stats_path = OUTPUT_DIR / "parse_stats.json"
    write_json_atomic(stats_path, stats)

    return 0


if __name__ == "__main__":
    sys.exit(main())
