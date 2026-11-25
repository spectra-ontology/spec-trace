#!/usr/bin/env python3
"""
Phase-8 Step-1: CR-Form 구조화 청킹 (RAN5).

사전 스캔 기반 RAN5 전용 설계:
  - CR DOCX → header(Reason/Summary/Consequences) + body(Text Proposal) 분리 청킹
  - CR 서식 본문 표(`cr_form.is_form_table`)의 이름 칸으로 구조화 필드 추출
  - 4-Strategy 청킹: A(header only) / B(header+body) / C(섹션별) / D(문단 분할)
  - Phase-4 cr_documents.json 메타데이터 연동

RAN5 고유:
  - R5-\\d{6} (6자리 TDoc 패턴)
  - CR 85.9% 비중 (WG 중 최고)
  - 38.5xx Conformance Testing Spec
  - 평균 61 paragraphs / 8 tables per CR

Input:  data/corpus/tsg/RAN/formal/change-requests/RAN5/derived/Rel-*/TSG/{팩}/ — cr_inputs 가 모은다(팩 커버 제외)
        ontology/output/tsg/RAN/formal/parsed_cr/RAN5/cr_documents.json (Phase-4 메타)
Output: vectordb/parsed/cr/RAN5/ran5_cr_chunks.json
"""

import itertools
import json
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter

from docx import Document
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

# =============================================================================
# Configuration
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[7]
PHASE4_META = PROJECT_ROOT / "ontology" / "output" / "tsg" / "RAN" / "formal" / "parsed_cr" / "RAN5" / "cr_documents.json"
WG = 'RAN5'
# CR 폴더 이름의 WG 번호. Phase-4 `_TDOC_RE` 와 같은 꼴이다.
_FOLDER_TDOC_RE = re.compile(r"(R5s\s?\d{6}|R5[-_]\d{6})(?!\d)")
OUTPUT_DIR = PROJECT_ROOT / "vectordb" / "parsed" / "cr" / "RAN5"
LOG_DIR = PROJECT_ROOT / "logs" / "tsg" / "RAN" / "formal" / "RAN5" / "phase-8"

# === 정규 프로세스 hardening ===
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "common"))
from common.atomic_io import write_json_atomic
from common.chunker import (  # noqa: E402
    enforce_hard_max as _enforce_hard_max, HARD_MAX_DEFAULT as _HARD_MAX_TOK,
    count_tokens as _count_tokens_exact, renumber_chunk_indices as _renumber_chunk_indices, _index_base,
)
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "tsg" / "RAN" / "formal" / "common"))
import docx_text  # noqa: E402
import cr_revision_marks  # noqa: E402
import cr_split_pieces  # noqa: E402
import cr_del_state  # noqa: E402
import cr_text_encoding  # noqa: E402
import cr_cover_cell  # noqa: E402
import ts_section_number as tsn  # noqa: E402
from cr_clause import clause_candidates, placeholder_clauses, range_clauses  # noqa: E402
import cr_identity  # noqa: E402
import tsg_cr_decision  # noqa: E402
import cr_attachments  # noqa: E402
import cr_inputs  # noqa: E402
import cr_other_wg  # noqa: E402  (다른 WG 슬롯에 놓인 이 WG 의 CR · 이 슬롯에 놓인 다른 WG 의 CR)
import cr_form  # noqa: E402
import cr_word_title  # noqa: E402 — LibreOffice 변환본의 표지 제목을 원본 .doc 글로 읽는다
import cr_form_slot  # noqa: E402 — CR 서식 본문 네 칸을 이름 칸이 망가져도 서식 틀의 자리로 읽는다
INPUT_DIR = cr_inputs.derived_dir("RAN5")

# 번호 뒤에 숫자가 이어지면 번호가 아니다(파일명 오타 `R5-2474883` 을 `R5-247488` 로 잘라 남의 번호를 받는다).
_NAME_TDOC_RE = re.compile(r"(R5s\s?\d{6}|R5[-_]\d{6})(?!\d)")


def _name_tdoc(filename: str) -> tuple[str, str, str] | None:
    """파일명의 tdoc(Phase-4 와 같은 정규화). `CRIdentity` 가 기록을 tdoc 으로 찾을 때 쓴다."""
    m = _NAME_TDOC_RE.search(filename)
    if not m:
        return None
    tok = m.group(1).replace(" ", "")
    return "", "", tok if tok.startswith("R5s") else tok.replace("_", "-")

#: 부속서 스타일. 머리(`Annex A (normative): …`)와 하위 절이 같은 스타일로 적힌다.
ANNEX_STYLES = {"Heading 8", "Heading 9"}

# 청킹 파라미터
HEADER_MIN_TOKENS = 20      # Strategy A(헤더만 내는 CR)의 헤더 최소 — 명세 §3.2 A 칸
MAX_BODY_TOKENS = 2000      # Strategy B→D 전환 기준
SPLIT_TARGET = 1500          # 분할 시 목표
SPLIT_OVERLAP = 80           # 분할 오버랩
MIN_CHUNK_TOKENS = 50        # 분할 조각에 새로 든 글의 최소. 형제 WG Spec §3.3 최소 청크 크기와 같다

# === 변경 표지 문단 (Spec §2.7.3) ===
# 「<< End of changes >>」 · 「-------- Skipped unchanged clauses --------」 처럼 바뀐 자리의 시작 · 끝 · 생략을
# 알리는 문단이다. 검색 가치가 없고 전략을 가르는 본문 토큰 수만 부풀리므로 변경 본문에서 뺀다.
# 대시 머리 꼴(`MARKER_RE`)과 낱말 꼴(`_is_marker_words`) 두 규칙은 RAN1 Phase-8 파서와 같다.
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
    """변경 표지(Spec §2.7.3)인가. 문단 · 표 행(`| 칸 | 칸 |`) · 표 · 그림 제목 글을 받는다.

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

#: CR 서식 본문 표의 이름 칸 → CRFormData 필드. 이름 칸이 앞 두 칸에 있고 값은 이름 칸 뒤 첫 글 있는 칸이고, 이름 칸이 지워지거나 망가졌으면 서식 틀의 자리에서 읽는다(`cr_form_slot.form_value`).
FORM_FIELD_LABELS = {
    'reason': "reason for change",
    'summary': "summary of change",
    'consequences': "consequences if not approved",
    'clauses': "clauses affected",
}


# =============================================================================
# Data classes
# =============================================================================

@dataclass
class CRFormData:
    """CR-Form에서 추출한 구조화 필드."""
    tdoc_number: str = ""
    reason: str = ""
    summary: str = ""
    consequences: str = ""
    clauses: str = ""
    category: str = ""
    title: str = ""
    spec_number: str = ""
    release: str = ""
    _crDelProof: dict | None = field(default=None, repr=False)


@dataclass
class CRChunk:
    """Phase-8 청크.
    RAN1~4 schema 통일 — bodySnippet/crNumber/crPackId/meeting/sectionIds/
    source/title/totalChunks/tsgMeeting/workItem/chunkSectionId/chunkIndex 추가.
    """
    chunk_id: str = ""
    tdoc_number: str = ""
    chunk_type: str = ""  # "header" | "body" | "body_section"
    section_title: str = ""
    content: str = ""           # 본문 텍스트 (RAN1과 통일 시 'text' 키로 직렬화)
    token_count: int = 0
    strategy: str = ""  # A/B/C/D
    spec_number: str = ""
    release: str = ""
    category: str = ""
    clauses_affected: str = ""
    has_tables: bool = False
    has_figures: bool = False
    # 추가 (RAN1 schema 통일)
    cr_number: str = ""           # ex: "CR0123"
    cr_pack_id: str = ""          # Phase-4 cover_sheets cr_pack_id
    meeting: str = ""             # Phase-4 meeting (RAN5#NN)
    tsg_meeting: str = ""         # Phase-4 tsg_meeting (TSG#NN)
    source: str = ""              # Phase-4 source (회사명)
    title: str = ""               # CR title
    work_item: str = ""           # Phase-4 work_item
    section_ids: list = field(default_factory=list)
    chunk_section_id: str = ""   # body_section 시 section_id (Strategy C)
    chunk_index: int = 0          # 0-based
    total_chunks: int = 0
    body_snippet: str = ""        # header 청크에 포함되는 body 미리보기 (200자)
    _crDelProof: dict | None = field(default=None, repr=False)


# =============================================================================
# CR-Form 필드 추출
# =============================================================================

def _form_table(doc: Document):
    """CR 서식 본문 표 — 서식 본문 이름 칸을 자기 칸에 가진 첫 표(`cr_form.is_form_table`, 칸 안에 든 표까지).

    서식 표는 문서마다 자리가 다르다 — 앞에 표가 더 있거나 서식 전체를 겉 표 한 칸에 담은 문서가
    있어 `doc.tables[2]` 는 서식 표가 아닐 수 있다. 행 차례도 틀마다 달라 행은 이름 칸으로 찾는다.
    """
    for table in cr_form.form_tables(doc):
        if cr_form.is_form_table(table):
            return table
    return None


def _form_end(doc: Document) -> int | None:
    """CR 서식이 끝나는 본문 직계 요소의 자리 — 서식 본문 표와 이어 받은 표(`cr_form.form_block`) 가운데
    마지막 표를 담은 요소. 서식 본문 표가 없으면 None.

    서식 표 수는 문서마다 다르다 — 서식을 표 둘로 줄인 문서, 앞에 머리 표를 더 둔 문서, 서식 본문을
    빈 문단으로 끊어 표 넷으로 둔 문서가 있다. 그래서 앞 표 몇 개를 자리로 빼지 않고 서식이 끝나는
    자리까지의 표를 뺀다.

    서식 뒤로 이어 받는 표는 표지 안에서만 잇는다. `form_block` 은 보이는 글(w:t)이 있는 문단에서만
    멈추므로, 빈 문단에 든 구역 나눔 · 쪽 나눔 너머의 본문 표나, 지운 글(w:delText)만 남은 제목 ·
    표까지 서식으로 잇는다. 서식 표와 다음 표 사이에 그런 문단이 있으면(`_cover_ends`) 서식은 거기서 끝난다.
    """
    table = _form_table(doc)
    if table is None:
        return None
    body = doc.element.body
    kids = list(body.iterchildren())

    def top(el):
        while el is not None and el.getparent() is not body:
            el = el.getparent()
        return el

    form = top(table._tbl)
    if form is None:
        return None
    end = kids.index(form)

    def _proposal_heading(el):
        if el.tag != qn("w:p"):
            return False
        style = Paragraph(el, doc).style
        return (style is not None and style.name.startswith("Heading")
                and style.name != "Heading 1")

    for t in cr_form.form_block(table):
        el = top(t._tbl)
        at = kids.index(el) if el is not None else -1
        if at <= end:
            continue
        between = kids[end + 1:at]
        if any(_cover_ends(k) or _proposal_heading(k) for k in between):
            break
        if between and _body_table(t):
            break
        end = at
    return end


#: 서식 이름 칸(`cr_form.FORM_LABELS`) 없이 서식 꼬리에만 오는 행의 글귀. 형제 WG 파서의
#: `find_last_form_table_index` 가 서식 뒤 표를 서식으로 잇는 글귀와 같고, 그 표에 함께 오는 `Other comments` 를 더한다.
_FORM_TAIL_WORDS = ("other specs", "other comments", "change history", "revision history")


def _body_table(table) -> bool:
    """빈 문단 너머에 온 표가 서식을 이은 표가 아니라 변경 본문의 표인가 — 보이는 글이 있는데 서식 이름 칸도,
    서식 꼬리 글귀(`_FORM_TAIL_WORDS`)도 없다.

    `cr_form.form_block` 은 글 있는 문단에서만 멈추므로, 서식 바로 뒤 빈 문단 다음에 표로 시작하는 변경 본문은
    그 표까지 서식으로 이어져 본문에서 빠진다. 서식을 빈 문단으로 끊은 문서의 뒤 표는 이름 칸이나 꼬리 글귀를 가진다.
    """
    text = " ".join((t.text or "") for t in table._tbl.iter(qn("w:t"))).strip()
    if not text:
        return False
    if any(cr_form._row_label([c.strip() for c in cells]) for cells in docx_text.table_rows(table)):
        return False
    low = text.lower().replace("\u2019", "'")
    return not any(w in low for w in _FORM_TAIL_WORDS)


def _cover_ends(el) -> bool:
    """서식(표지)이 끝났다는 표지 — 구역 나눔 · 쪽 나눔이 있거나, 지운 글이 든 요소."""
    if el.find(".//" + qn("w:sectPr")) is not None or el.find(".//" + qn("w:pageBreakBefore")) is not None:
        return True
    if any(br.get(qn("w:type")) == "page" for br in el.iter(qn("w:br"))):
        return True
    return any((x.text or "").strip() for x in el.iter(qn("w:delText")))


def extract_cr_form(doc: Document, filename: str) -> CRFormData:
    """CR DOCX에서 CR-Form 필드 추출."""
    form = CRFormData()

    # TDoc 번호: 파일명에서 추출 (R5-NNNNNN)
    m = re.search(r'(R5-\d{6})', filename)
    if m:
        form.tdoc_number = m.group(1)

    # Spec 번호: 3GPP 표준 형식만 매치
    # R5-234614 TDoc 뒤 5자리가 spec으로 오인되는 버그 수정
    # sub-spec suffix를 1-2자리로 제한 + whitelist
    # underscore separator 제거. root cause = (?:[-_](\d{1,2}))?에서 _도 sub-spec separator로 오인.
    #   - 파일명 `38.521_6.5A.3.docx`의 `_6`이 sub-spec으로 잘못 매칭 → `38.521-6` (실제는 §6.5A.3 section)
    #   - 파일명 `R5-XXX_38.903_10.1.1.1.1.docx`의 `_10`이 sub-spec → `38.903-10` (실제는 §10.1.1.1.1)
    #   - hyphen `-`만 진짜 sub-spec separator (예: `38101-1_CR0029`)
    # 화이트리스트는 v4 fallback 용으로 보존 (defense in depth).
    LEGITIMATE_RAN5_SUBSPECS = {
        '38.508-1', '38.508-2',
        '38.521-1', '38.521-2', '38.521-3', '38.521-4', '38.521-5',
        '38.523-1', '38.523-2', '38.523-3',
    }
    # 처리 순서: 1) TDoc 제거 2) 점/언더스코어 3) CR 붙여쓰기
    clean = re.sub(r'R5-\d{6}', '', filename)
    # sub-spec separator는 hyphen `-`만. underscore `_`는 section number separator라 제외.
    m = re.search(r'(3[4-9])[._](\d{3})(?:-(\d{1,2}))?', clean)
    if m:
        base = f"{m.group(1)}.{m.group(2)}"
        if m.group(3):
            candidate = f"{base}-{m.group(3)}"
            # 정상 sub-spec 화이트리스트에 없으면 base spec으로 fallback (defense)
            form.spec_number = candidate if candidate in LEGITIMATE_RAN5_SUBSPECS else base
        else:
            form.spec_number = base
    else:
        m = re.search(r'(3[4-9]\d{3}(?:-\d{1,2})?)_CR', clean)
        if m:
            raw = m.group(1)
            candidate = f"{raw[:2]}.{raw[2:]}"
            base = candidate.split('-')[0] if '-' in candidate else candidate
            form.spec_number = candidate if (candidate in LEGITIMATE_RAN5_SUBSPECS or '-' not in candidate) else base

    # Release: 파일명에서 추출
    m = re.search(r'Rel-(\d+)', filename)
    if m:
        form.release = f"Rel-{m.group(1)}"

    table = _form_table(doc)
    if table is not None:
        for name, label in FORM_FIELD_LABELS.items():
            setattr(form, name, cr_form_slot.form_value(table, label) or "")
        # 제목 · 분류는 서식 틀의 자리표시(`<Title>` · `<Cat>`)를 뗀 값으로 받는다.
        fields = cr_form.form_fields(doc)
        form.title = fields.get("title", "")
        cat_raw = fields.get("category", "")
        if cat_raw:
            form.category = cat_raw[0] if cat_raw[0] in 'FABCD' else cat_raw[:10]

    return form


# =============================================================================
# Text Proposal 본문 추출
# =============================================================================

def _body_boxed(p_elem) -> str:
    """표 칸 문단 글 — `_body_paragraph_text` 다음 줄에 그 문단에 연결된 부동 텍스트 상자(`w:txbxContent`) 글을 붙인다
    (`docx_text.boxed_text`, 글상자 안 문단도 `_body_paragraph_text` 로 읽는다).

    `docx_text.chunk_text` 는 글상자를 읽지 않는다. 지운 변경 표시 안 글상자는 읽지 않고, `mc:AlternateContent` 는 한 벌만,
    도형 묶음 · 그리기 캔버스 안 글상자는 그림 안 라벨이라 넣지 않는다(`docx_text.box_text`).

    Text Proposal 시작 앞 문단(표지 · CR 양식)은 건너뛰므로, 그 문단의 글상자도 들지 않는다.
    """
    return docx_text.boxed_text(p_elem, read=_body_paragraph_text)


def _table_rows(tbl) -> list[str]:
    """본문 표 → 행마다 `| 칸 | 칸 |` 한 줄(다른 WG 파서의 `table_to_text` 와 같은 꼴). 빈칸만 있는 행은 뺀다.

    행 · 칸은 `docx_text.table_rows` 로 읽는다. 칸 안 문단은 `_body_boxed`(빠진 글 `[DEL]…[/DEL]`, 그 문단에 연결된 부동 텍스트 상자 글은 다음 줄)로 읽어
    빈칸으로 잇고, 행 지움 표시(`w:trPr/w:del`)가 있는 행은 칸 글 전체를 `[DEL]…[/DEL]` 로 감싼다(`docx_text.MARK`).
    칸 안 표는 같은 꼴의 행을 ` ; ` 로 이어 칸 글 한 줄로 넣는다.
    주의: 행 · 칸을 `w:tr` · `w:tc` 직접 자식으로 돌고 칸 글을 `findall(w:p)` 로 읽으면 칸 안 표의 글, 블록 래퍼
    (`w:sdt` · `w:customXml`) 속 행 · 칸 · 문단이 빠지고, 지운 행이 확정 글로 남으며, 세로로 합친 칸(`w:vMerge`)의
    이어지는 행에는 머리글 없는 값만 남는다.
    표본 CR 300 개의 표 6,514 개 가운데 1,821 개의 글이 옛 읽기와 다르다 — 칸 안 줄바꿈만 다른 표 642, 나머지는 세로 합침 686 · 지운 행
    510 · 칸 안 표 2 개가 든 표다(한 표에 여럿이 겹친다).
    주의: 빈 칸도 자리로 남긴다. 빈 칸을 버리고 글 있는 칸만 잇으면 값이 어느 열의 것인지 사라져, 시험 조건 표처럼 빈 칸이
    많은 표의 행이 머리글과 맞지 않는다. 같은 표가 WG 마다 다른 글로 임베딩되지 않도록 다른 WG 파서와 같은 꼴로 쓴다.
    """
    def lines(rows: list[list[str]]) -> list[str]:
        out = []
        for row in rows:
            cells = [" ".join(x for x in c.split("\n") if x).strip() for c in row]
            line = "| " + " | ".join(cells) + " |"
            # 모든 칸이 변경 표지인 행(「| Unchanged rows skipped |」)은 문단 표지처럼 뺀다(Spec §2.7.3).
            if any(cells) and not _is_change_marker(line):
                out.append(line)
        return out

    return lines(docx_text.table_rows(tbl, para=_body_boxed, deleted=docx_text.MARK,
                                      nested=lambda inner: [" ; ".join(lines(inner))]))


def _body_paragraph_text(p_elem) -> str:
    """변경 본문 문단 글. 들어간 글은 그대로, 빠진 글은 `[DEL]…[/DEL]` 로 함께 읽는다(RAN1 Phase-8 Spec §1.9.2).

    수식은 선형 표기로, 수식 개체는 읽은 글로 넣는다(`docx_text.chunk_text`).
    §1.9.2 는 RAN5 Phase-8 Spec 에 없고 RAN1 Phase-8 Spec
    (docs/tsg/RAN/formal/RAN1/phase-8/design-spec/tdoc_vectordb_specs(CR).md)에 있다.
    """
    return docx_text.chunk_text(cr_text_encoding.repaired_paragraph(p_elem), deleted=docx_text.MARK)


def _heading(p_elem, style: str) -> tuple[str, str]:
    """제목 문단 → (제목 글, 절 번호). 번호가 절 번호 문법이 아니면 번호는 빈 값.

    제목은 바뀐 뒤의 글로 읽는다. CR 이 통째로 지운 절이면 지워진 제목이 그 절을 가리킨다.
    """
    text = docx_text.paragraph_text(p_elem, math=False) or docx_text.paragraph_text(
        p_elem, deleted=docx_text.KEEP, math=False)
    split = tsn.split_annex_heading if style in ANNEX_STYLES else tsn.split_heading
    num, _ = split(text)
    return text, (num if tsn.is_section_number(num) else "")


#: 이름이 `Heading` 으로 시작하지 않는 3GPP 제목 스타일(형제 WG 파서의 `HEADING_LEVEL_MAP` 과 같은 몫).
H_STYLES = {"H6", "h60"}


def _is_heading(p_elem, style: str) -> bool:
    """제목 문단인가 — 이름이 `Heading` 으로 시작하는 스타일, 3GPP 제목 스타일(`H_STYLES`), 문단에 개요 수준
    (`w:outlineLvl` 0 부터 8)을 단 문단.

    주의: 이름만 보면 `H6` 스타일로 적은 시험 절 제목(`6.5.1.5.4.2 Test procedure` 따위)이 본문 글로 섞이고
    절이 나뉘지 않는다. 형제 WG 파서(`detect_headings`)는 스타일 표와 개요 수준으로 제목을 찾는다.
    """
    if not _heading_style(p_elem, style):
        return False
    # 표 · 그림 제목 · ASN.1 정의 줄 · 제목 아닌 3GPP 스타일 문단은 개요 수준이 붙어 있어도 절 경계가 아니다
    # (`docx_text.not_heading`). 변경 표지는 캡션 스타일이어도 바뀐 자리 사이의 경계라 제목으로 둔다.
    text = docx_text.paragraph_text(p_elem, math=False) or docx_text.paragraph_text(
        p_elem, deleted=docx_text.KEEP, math=False)
    return not docx_text.not_heading(style, text) or _is_change_marker(text)


def _heading_style(p_elem, style: str) -> bool:
    """스타일 이름이나 문단 개요 수준이 제목을 가리키는가."""
    if style.startswith("Heading") or style in H_STYLES:
        return True
    lvl = p_elem.find(f"{qn('w:pPr')}/{qn('w:outlineLvl')}")
    if lvl is None:
        return False
    try:
        return 0 <= int(lvl.get(qn("w:val"), "")) <= 8
    except ValueError:
        return False


#: 목차 내용 제어의 문서 조각 갤러리 값(`w:sdtPr/w:docPartObj/w:docPartGallery/@w:val`). 표지 래퍼는 `Cover Pages` 다.
_TOC_GALLERY = "Table of Contents"


def _is_toc_sdt(sdt) -> bool:
    sdt_pr = sdt.find(qn("w:sdtPr"))
    if sdt_pr is None:
        return False
    gallery = sdt_pr.find(".//" + qn("w:docPartGallery"))
    return gallery is not None and gallery.get(qn("w:val")) == _TOC_GALLERY


def _body_blocks(el):
    """본문 직계 요소 하나를 블록(`w:p` · `w:tbl`)들로. 블록 `w:sdt` · `w:customXml` 안으로 들어가되 목차 `w:sdt` 는 건너뛴다.

    변경 본문을 내용 제어 안에 적은 CR 이 있어 직계만 돌면 그 글이 빠진다. 래퍼 안 글의 대부분은 목차라서 그대로
    내려가면 청크에 목차 잡음이 들어오므로 목차 래퍼만 뺀다(형제 WG 파서의 `_body_blocks` 와 같은 규칙).
    블록이 아닌 요소(`w:sectPr` 등)는 그대로 돌려 호출부가 건너뛰게 한다.
    """
    if el.tag == qn("w:sdt"):
        if _is_toc_sdt(el):
            return
        content = el.find(qn("w:sdtContent"))
        for child in (content if content is not None else ()):
            yield from _body_blocks(child)
    elif el.tag == qn("w:customXml"):
        for child in el:
            yield from _body_blocks(child)
    else:
        yield el


def extract_text_proposal(doc: Document) -> tuple[str, list[tuple[str, str, str, bool]], bool, bool]:
    """CR DOCX에서 Text Proposal 본문 추출.

    본문 요소(문단 · 표)를 문서 순서대로 읽어, 표가 자기 절에 들어가게 한다.
    서식이 끝나는 자리(`_form_end`)까지의 표는 CR-Form 이라 본문에 넣지 않는다.

    Returns:
        full_text: 전체 본문 텍스트
        sections: [(heading_text, section_number, body_text, changed), ...] (Heading 기반 분할).
            changed 는 절 안에 변경 추적 표시나 손 표기(밑줄 · 취소선)가 있는가다. 본문에 변경 추적 표시가
            하나도 없으면 모든 절이 True 다(`cr_revision_marks`). 제목 앞 글(제목 "")도 True 다.
        has_tables: 본문 글에 표 행이나 표 제목(`TH`) 줄을 넣었는가
        has_figures: 본문 글에 그림 제목(`TF`) 줄을 넣었는가
    """
    paragraphs = []
    sections = []
    current_heading = ""
    current_number = ""
    current_body = []
    in_text_proposal = False
    has_tables = False
    has_figures = False
    form_end = _form_end(doc)

    current_line = ""
    current_marked = False  # 지금 절에 변경 추적 표시나 손 표기가 있는가
    any_revision = False  # 본문에 변경 추적 표시가 있는가

    carried: list[str] = []  # 글 없는 절의 제목 줄. 다음에 글이 있는 절의 첫머리에 붙인다

    def close_section():
        # 절 글은 제목 줄을 첫 줄로 둔다(형제 WG 파서가 제목 문단부터 절 끝까지를 읽는 것과 같다).
        # 제목 아래 글이 없는 절은 글을 비워 두어 Strategy C 청크를 내지 않는다.
        # 주의: 글 없는 절의 제목 줄은 버리지 않고 다음에 글이 있는 절의 첫머리에 붙인다. 버리면 시험 항목
        # 이름(`8.1.19 E-UTRAN FD - FDD Intra-frequency identification … for UE category 0`)이 Strategy C
        # 어느 청크에도 들지 않아, 그 아래 `Test procedure` 같은 짧은 절 청크가 어느 시험의 절인지 글로
        # 가려지지 않는다. 받는 절의 번호 · 제목 · 변경 판정은 그대로 둔다. 형제 WG 파서처럼 짧은 절을
        # 이웃 청크에 합치지는 않는다. 합치면 합쳐진 절의 `chunkSectionId` 가 사라진다.
        if current_body or current_heading:
            if current_body:
                lines = carried + ([current_line] if current_line else []) + current_body
                carried.clear()
            else:
                lines = []
                if current_line:
                    carried.append(current_line)
            sections.append((current_heading, current_number, "\n".join(lines),
                             current_marked or not (current_heading or current_number)))

    # 표지 표 칸 안에 이어 적은 변경 본문은 그 표 바로 뒤 자리(표 자리 + 0.5)의 본문 요소로 꺼낸다
    # (`cr_cover_cell.body_in_cells`). 그 표가 서식의 마지막 표면 서식 뒤라 본문이 되고, 뒤에 서식 표가 더 있으면
    # 서식 안이라 빠진다.
    children = list(doc.element.body.iterchildren())
    cover_at, cell_body = cr_cover_cell.body_in_cells(children)
    # 래퍼(`w:sdt` · `w:customXml`) 안 블록은 그 래퍼의 직계 자리를 함께 쓴다 — `_form_end` 가 래퍼 속 서식 표를
    # 그 래퍼의 직계 자리로 재므로 같은 자로 비교된다.
    placed = []
    for at, child in enumerate(children):
        placed.extend((at, block) for block in _body_blocks(child))
        if at == cover_at:
            placed.extend((at + 0.5, k) for k in cell_body)
    for at, child in placed:
        if child.tag == qn("w:tbl"):
            if form_end is not None and at <= form_end:
                continue
            rev = cr_revision_marks.has_revision(child)
            any_revision |= rev
            current_marked |= rev or cr_revision_marks.has_manual_mark(child)
            rows = _table_rows(child)
            # 주의: 판정은 글에 넣은 것으로 한다. 모든 행이 지워졌거나 변경 표지뿐인 표는 줄을 내지 않는다.
            has_tables |= bool(rows)
            current_body.extend(rows)
            paragraphs.extend(rows)
            continue
        if child.tag != qn("w:p"):
            continue
        style = Paragraph(child, doc).style
        style = style.name if style is not None else ""
        is_heading = _is_heading(child, style)

        # Text Proposal 시작: 서식 표가 있으면 서식이 끝난 자리 다음부터 본문이다(형제 WG 파서의
        # `find_last_form_table_index` 다음과 같은 자리). 서식 앞 문단은 표지라 뺀다.
        # 주의: 서식 뒤에서도 "=====" 표지나 Heading 2 이상 제목을 기다리면, 변경 본문이 `Heading 1` 절
        # (`2 References` 따위)이나 `H6` 제목, 표지 없는 문단으로 시작하는 CR 은 본문 문단이 통째로 빠지고
        # 서식 뒤 표만 남는다. 그 기다림은 서식 표를 찾지 못한 문서에만 쓴다.
        if form_end is not None:
            in_text_proposal = at > form_end
            if not in_text_proposal:
                continue
        if not in_text_proposal:
            if is_heading and style != 'Heading 1':
                in_text_proposal = True
            elif '=====' in _body_paragraph_text(child):
                in_text_proposal = True
                continue
            else:
                # CR Cover Page, CR-Form 관련 paragraphs는 skip
                continue

        # Text Proposal 내부
        # 문단에 연결된 부동 텍스트 상자 글. 제목 · 표 제목 · 그림 제목 글은 그대로 두고 본문 다음 줄로 넣는다.
        # 글상자에 든 변경 표지(`End of changes` 따위)는 문단 표지처럼 뺀다(Spec §2.7.3).
        box = docx_text.box_text(child, read=_body_paragraph_text)
        if box and _is_change_marker(box):
            box = ""
        rev = cr_revision_marks.has_revision(child)
        mark = rev or cr_revision_marks.has_manual_mark(child)
        any_revision |= rev
        if is_heading:
            close_section()
            current_marked = mark
            current_heading, current_number = _heading(child, style)
            # 주의: 제목 글은 절 이름(`section_title`)으로만 두면 임베딩 글(`text`)에 들지 않아, 시험 절 이름 ·
            # 절 번호로 찾는 질의가 그 CR 의 청크에 닿지 않는다. 본문과 같은 읽기(빠진 글 `[DEL]…[/DEL]`)로 본문 줄에도 넣는다.
            current_line = _body_paragraph_text(child)
            if current_line and _is_change_marker(current_line):
                current_line = ""
            current_body = [box] if box else []
            if current_line:
                paragraphs.append(current_line)
            if box:
                paragraphs.append(box)
            continue
        text = _body_paragraph_text(child)
        if style == 'TH':
            # 표 · 그림 제목 자리에 쓴 변경 표지(「<Unchanged tables omitted>」)도 뺀다.
            # 주의: 그림을 놓는 문단도 `TH` 서식을 쓴다(글이 없다). 그 문단은 표 판정을 세우지 않는다.
            if text and not _is_change_marker(text):
                has_tables = True
                current_body.append(f"[Table] {text}")
                paragraphs.append(f"[Table] {text}")
        elif style == 'TF':
            if text and not _is_change_marker(text):
                has_figures = True
                current_body.append(f"[Figure] {text}")
                paragraphs.append(f"[Figure] {text}")
        elif text and not _is_change_marker(text):
            current_body.append(text)
            paragraphs.append(text)
        current_marked |= mark
        if box:
            current_body.append(box)
            paragraphs.append(box)

    close_section()
    if not any_revision:
        sections = [(h, n, t, True) for h, n, t, _ in sections]

    full_text = "\n".join(paragraphs)
    return full_text, sections, has_tables, has_figures


# 문서 읽기는 자식 프로세스 하나가 한 벌씩 맡고, 이 수만큼 읽으면 새 자식으로 바뀐다.
# 한 프로세스가 3만여 벌을 읽으면 lxml 이 잡았다 놓는 메모리 사이에 오래 사는 청크 문자열이
# 끼어 힙이 조각난다 — 1,000 벌째 상주 4.1 GB 중 1.8 GB, 2,000 벌째 5.6 GB 중 4.7 GB 가
# `malloc_trim` 으로 돌아가는 빈 몫이었고, 6 GB 상한에서 OOM 으로 끊겼다. 문서만 여는 측정에서
# 750 벌이 1.2 GB 에 닿았으므로 자식은 그 몇 분의 일에서 바꾼다.
READER_TASKS = 100


class _Reader:
    """문서를 자식 프로세스 하나에서 읽고, READER_TASKS 벌마다 새 자식으로 바꾼다.

    주의: `multiprocessing.Pool.apply` 는 일을 맡은 자식이 죽으면(메모리 상한에 걸린 OOM 등) 새 자식을
    띄우지만 그 일의 결과는 끝내 오지 않아 부모가 멈춘다. 여기서는 자식이 죽으면 `BrokenProcessPool` 을
    받아 새 자식으로 그 문서를 한 번 더 읽고, 또 죽으면 그 문서를 오류로 올린다. 넘기는 것은 경로뿐이라
    죽은 자식의 파이프에 큰 항목을 쓰다 막히는 일도 없다.
    """

    def __init__(self) -> None:
        self._pool: ProcessPoolExecutor | None = None
        self._used = 0

    def _fresh(self) -> ProcessPoolExecutor:
        if self._pool is None or self._used >= READER_TASKS:
            self.close()
            self._pool = ProcessPoolExecutor(1, mp_context=multiprocessing.get_context("fork"))
        self._used += 1
        return self._pool

    def read(self, path: str):
        for _ in range(2):
            try:
                return self._fresh().submit(_read_cr, path).result()
            except BrokenProcessPool:
                self.close()
        raise RuntimeError("문서를 읽던 자식 프로세스가 두 번 죽음")

    def close(self) -> None:
        if self._pool is not None:
            self._pool.shutdown()
            self._pool = None
        self._used = 0


def _read_cr(path: str):
    """자식 프로세스에서 CR 한 벌을 읽는다 → (form, proposal, 오류, Strict 로 열었는가).

    판정(tdoc 없음 · 중복)은 부모가 이 순서대로 내린다. 그래서 본문 추출 오류는 바로 올리지
    않고 담아 보내, 부모가 판정을 마친 뒤에 오류로 센다 — 한 프로세스에서 읽던 때와 같은 순서다.
    """
    note: dict = {}
    try:
        doc = docx_text.open_document(path, note)
        form = extract_cr_form(doc, Path(path).name)
        # 주의: LibreOffice 변환본의 제목은 원본 .doc 이 보여 주는 Title 칸 글로 바로잡는다(`cr_word_title`).
        form.title = cr_word_title.form_title(form.title, path)
    except Exception as e:
        return None, None, str(e), bool(note)
    try:
        form._crDelProof = cr_del_state.prove_xml(
            [doc.element.body],
            lambda p: docx_text.chunk_text(p, deleted=docx_text.KEEP),
            raw_metadata=vars(form),
        )
        return form, extract_text_proposal(doc), None, bool(note)
    except Exception as e:
        return form, None, str(e), bool(note)


# =============================================================================
# 청킹 전략
# =============================================================================

def count_tokens(text: str) -> int:
    return len(text) // 4


def build_header_text(form: CRFormData) -> str:
    """CR-Form 구조화 필드를 검색용 텍스트로 결합."""
    parts = []
    if form.title:
        parts.append(f"Title: {form.title}")
    if form.reason:
        parts.append(f"Reason for change: {form.reason}")
    if form.summary:
        parts.append(f"Summary of change: {form.summary}")
    if form.consequences:
        parts.append(f"Consequences if not approved: {form.consequences}")
    if form.clauses:
        parts.append(f"Clauses affected: {form.clauses}")
    return "\n".join(parts)


def split_by_paragraphs(text: str, target: int = SPLIT_TARGET,
                         overlap: int = SPLIT_OVERLAP, del_proof=None) -> list[str]:
    """문단 경계 기반 분할."""
    if cr_del_state.is_proven(del_proof) and cr_del_state.MARK.search(text):
        return cr_del_state.split_paragraphs(
            text.split("\n"), target, overlap, MIN_CHUNK_TOKENS, count_tokens,
            del_proof, trim_word=True)
    paras = text.split("\n")
    chunks = []
    current = []
    current_tokens = 0
    carried_tokens = 0  # current 앞머리 가운데 앞 조각에서 넘겨받은 오버랩 토큰

    for p in paras:
        pt = count_tokens(p)
        # 주의: 앞 조각에 없던 글이 MIN_CHUNK_TOKENS 미만이면 끊지 않는다. 끊으면 넘겨받은 오버랩과 절 제목만
        # 든 조각이 생긴다. 커진 조각은 저장 직전의 HARD_MAX 강제가 자른다.
        if current_tokens + pt > target and current and current_tokens - carried_tokens >= MIN_CHUNK_TOKENS:
            chunks.append("\n".join(current))
            # 주의: 오버랩은 SPLIT_OVERLAP 안에 드는 끝 문단들만 넘긴다(형제 WG split_by_tokens 와 같은 규칙).
            # 마지막 문단을 통째로 넘기면 큰 표 · 긴 문단이 다음 조각에 한 번 더 실린다. 끝 문단 하나가 이미
            # 상한을 넘으면 그 끝 글자 SPLIT_OVERLAP * 4 자 안에서 낱말 경계부터 넘긴다.
            overlap_paras: list[str] = []
            overlap_tokens = 0
            for q in reversed(current):
                qt = count_tokens(q)
                if overlap_tokens + qt > overlap:
                    if not overlap_paras:
                        tail = q[-overlap * 4:]
                        # 주의: 자른 자리가 낱말 가운데면 첫 공백 뒤부터 넘긴다. 낱말 조각으로 시작하는 조각은
                        # 임베딩에 뜻 없는 글자를 싣는다. 공백이 없으면 그대로 둔다.
                        cut = tail.find(" ") if len(q) > len(tail) and not q[-len(tail) - 1].isspace() else -1
                        if 0 <= cut < len(tail) - 1:
                            tail = tail[cut + 1:]
                        overlap_paras = [tail]
                        overlap_tokens = count_tokens(tail)
                    break
                overlap_paras.insert(0, q)
                overlap_tokens += qt
            current = overlap_paras
            current_tokens = carried_tokens = overlap_tokens
        current.append(p)
        current_tokens += pt

    if current:
        chunks.append("\n".join(current))
    return chunks


def _parse_clauses_to_section_ids(clauses_str: str, spec_number: str) -> list[str]:
    """clausesAffected 문자열 → sectionIds 리스트.
    "5.1.2.1, 5.1.3.2" → ["38.508-1-5.1.2.1", "38.508-1-5.1.3.2"]

    칸은 Phase-4 가 CR → Section 간선을 만들 때 쓰는 `cr_clause.clause_candidates` 로 읽는다.
    두 단계가 같은 칸을 다르게 끊으면 이 청크의 sectionIds 와 그래프의 간선이 서로 다른 절을
    가리킨다. 이 함수가 따로 쉼표 조각을 통째로 받던 때는 아직 번호가 없는 새 절(`9.2.x`)과
    낱말(`New` · `RadioBearerConfig`)이 절로 들어가고, 머리말이나 주석이 붙은 조각
    (`Section 8.1` · `8.14.4 (new)` · `(New) A.3.18`)은 통째로 빠졌다.

    `clause_candidates` 는 절마다 철자 후보를 긴 것부터 낸다(`A.1-1` → `A.1-1`, `A.1`). Phase-4 는
    Section 색인에서 처음 걸리는 후보를 고르지만 이 단계에는 색인이 없다. 그래서 절 번호 꼴인
    후보 가운데 마지막 것, 곧 꼬리를 뗀 머리를 고른다. 칸에 적힌 꼬리 붙은 꼴은 TS 절 제목으로
    거의 서지 않고 머리 쪽이 절로 선다.

    ASN.1 정의명 후보는 넣지 않는다. 같은 꼴의 낱말(`New` · `General`)과 가르는 일은 Section
    색인만 할 수 있고, sectionIds 를 맞대는 Phase-7 TS 청크에는 이름으로 선 절이 없다.
    """
    if not clauses_str or not spec_number:
        return []
    clauses = []
    for candidates in clause_candidates(clauses_str):
        # 이름 후보는 절 번호 문법을 통과하지 못해 여기서 빠진다.
        numbers = [c for c in candidates if tsn.is_section_number(c)]
        if numbers:
            clauses.append(numbers[-1])
    return [f"{spec_number}-{c}" for c in dict.fromkeys(clauses)]


def generate_cr_chunks(form: CRFormData, body_text: str,
                        body_sections: list[tuple[str, str, str, bool]],
                        has_tables: bool, has_figures: bool,
                        phase4_meta: dict | None = None,
                        cr_number: str = "",
                        omitted: list[str] | None = None) -> list[CRChunk]:
    """4-Strategy 청킹.
    phase4_meta + cr_number 인자 추가 (RAN1 schema 통일).
    """
    chunks = []
    from tdoc_source_metadata import identity_fields, corrected_label
    source_fields = identity_fields(PROJECT_ROOT, 'RAN5').get(form.tdoc_number, {})
    if 'spec_number' in source_fields:
        form.spec_number = source_fields['spec_number']
    if 'release' in source_fields:
        form.release = source_fields['release']
    cr_number = corrected_label(cr_number, source_fields)
    del_proof = getattr(form, "_crDelProof", None)
    del_proof = cr_del_state.with_metadata(del_proof, phase4_meta or {})
    header_text = build_header_text(form)
    header_tokens = count_tokens(header_text)
    section_ids = _parse_clauses_to_section_ids(form.clauses, form.spec_number)

    # 주의: 변경 추적 표시가 있는 CR 에서 표시가 없는 절은 옮겨 적은 표준 글이라 청크로 만들지 않는다
    # (`cr_revision_marks`, 형제 WG 파서와 같은 규칙). 표지에 적힌 절은 남긴다. 이 판정은 전략을 고르기
    # 전에 하고, 전략은 남긴 본문으로 고른다. 판정을 C 안에서만 하면 옮겨 적은 글을 뺀 뒤 B · D 로 갈 CR 이
    # 옮겨 적은 글까지 센 길이로 C 에 머물거나, B · D 로 가는 CR 은 그 글을 그대로 청크에 싣는다. 뺀 절은
    # `omitted` 로 돌려 parse_stats.json 에 CR 별로 남긴다.
    # 자리표시 새 절(`8.7.X`)은 절 목록에 들지 않지만 표지 절로 넘겨 그 위 절 제목을 남긴다(`cr_clause.placeholder_clauses`).
    # 주의: 범위로 적힌 절(`2-11`)의 가운데 절도 보존 판정에만 넘긴다. 양 끝만 넘기면 표시 없는 가운데 절이 빠진다
    # (`cr_clause.range_clauses`).
    declared = ([sid[len(form.spec_number) + 1:] for sid in section_ids] + placeholder_clauses(form.clauses)
                + range_clauses(form.clauses, (number for _, number, _, _ in body_sections)))
    keep = [changed or cr_revision_marks.declared(number, declared)
            for _, number, _, changed in body_sections]
    if not all(keep):
        if omitted is not None:
            omitted.extend(number or heading
                           for (heading, number, _, _), k in zip(body_sections, keep) if not k)
        body_text = "\n".join(text for (_, _, text, _), k in zip(body_sections, keep) if k and text)
    body_tokens = count_tokens(body_text)

    # Strategy 결정
    if body_tokens < 100:
        # 헤더만 내는 자리라 헤더 최소는 여기에만 걸린다. 본문 청크를 내는 B · C · D 는 표지가
        # 짧거나 비어도 본문이 CR 의 변경 내용이므로 버리지 않는다.
        if header_tokens < HEADER_MIN_TOKENS:
            return chunks
        strategy = "A"
    elif body_tokens < MAX_BODY_TOKENS:
        strategy = "B"
    elif sum(keep) >= 2:
        strategy = "C"
    else:
        strategy = "D"

    # Phase-4 메타 추출 (없으면 빈 값)
    p4 = phase4_meta or {}

    base = {
        'spec_number': form.spec_number,
        'release': form.release,
        'category': form.category,
        'clauses_affected': form.clauses,
        'has_tables': has_tables,
        'has_figures': has_figures,
        # RAN1 schema 통일 메타
        'cr_number': cr_number or cr_identity.cr_label(p4),
        'cr_pack_id': p4.get('cr_pack_id', ''),
        'meeting': p4.get('meeting', ''),
        'tsg_meeting': p4.get('tsg_meeting', ''),
        'source': p4.get('source', ''),
        'title': form.title or p4.get('title', ''),
        'work_item': p4.get('work_item', ''),
        'section_ids': section_ids,
    }

    # 전략 A 는 본문 청크가 없어 본문이 bodySnippet 에만 남는다. 200자로 자르면 나머지가 어디에도 남지 않는다.
    body_snippet_text = (body_text if strategy == "A" else body_text[:200]) if body_text else ""
    # 전략 A 는 본문 청크가 없다. 본문(100 토큰 미만)을 머리 문장에 붙여야 변경 내용이 임베딩되어 검색된다.
    # 변경 표지 문단을 본문에서 빼면 B 였던 짧은 CR 이 A 로 내려오므로, 붙이지 않으면 그 본문이 검색에서 사라진다.
    # 헤더 최소(HEADER_MIN_TOKENS) 판정은 위에서 표지 글만으로 이미 끝났다.
    if strategy == "A" and body_text:
        header_text = f"{header_text}\nChange text: {body_text}"
        header_tokens = count_tokens(header_text)

    # Header 청크 (모든 Strategy에 포함) — chunk_index=0, body_snippet 포함
    chunks.append(CRChunk(
        chunk_id=f"{form.tdoc_number}-header",
        tdoc_number=form.tdoc_number,
        chunk_type="header",
        section_title="CR-Form Header",
        content=header_text,
        token_count=header_tokens,
        strategy=strategy,
        chunk_index=0,
        body_snippet=body_snippet_text,
        **base
    ))

    # Body 청크
    if strategy == "A":
        pass  # header only
    elif strategy == "B":
        chunks.append(CRChunk(
            chunk_id=f"{form.tdoc_number}-body-001",
            tdoc_number=form.tdoc_number,
            chunk_type="body",
            section_title="Text Proposal",
            content=body_text,
            token_count=body_tokens,
            strategy=strategy,
            chunk_index=1,
            **base
        ))
    elif strategy == "C":
        for idx, ((heading, number, text, _), k) in enumerate(zip(body_sections, keep), 1):
            if not k:
                continue
            if not text.strip():
                continue
            # 주의: 제목 스타일로 적은 변경 표지(「<Unchanged section skipped>」 · 「Change 2」)는 바뀐 자리 사이의
            # 경계라 절을 나누지만 절 이름이 아니다. 그 글을 `sectionTitle` 로, 그 앞 번호(「1 Change 1」 의 1)를
            # 절 번호로 쓰면 없는 절 이름과 엉뚱한 `chunkSectionId` 가 payload 에 남는다. 남길 절 판정(`keep`)과
            # 뺀 절 기록은 표지 글을 그대로 쓴다.
            if heading and _is_change_marker(heading):
                heading, number = "", ""
            chunks.append(CRChunk(
                chunk_id=f"{form.tdoc_number}-body-{idx:03d}",
                tdoc_number=form.tdoc_number,
                chunk_type="body_section",
                section_title=heading or f"Section {idx}",
                content=text,
                token_count=count_tokens(text),
                strategy=strategy,
                chunk_index=idx,
                chunk_section_id=f"{form.spec_number}-{number}" if number and form.spec_number else "",
                **base
            ))
    elif strategy == "D":
        split_texts = split_by_paragraphs(body_text, del_proof=del_proof)
        for idx, text in enumerate(split_texts, 1):
            if not text.strip():
                continue
            chunks.append(CRChunk(
                chunk_id=f"{form.tdoc_number}-body-{idx:03d}",
                tdoc_number=form.tdoc_number,
                chunk_type="body",
                section_title=f"Text Proposal (part {idx})",
                content=text,
                token_count=count_tokens(text),
                strategy=strategy,
                chunk_index=idx,
                **base
            ))

    # chunkIndex 는 이 CR 의 머리 · 본문 청크 목록 안의 순번(0..n-1)이고 totalChunks 는 그 개수다. C 는 뺀 절과
    # 빈 절을 건너뛰므로 절 순번(`idx`)을 그대로 쓰면 순번에 빈칸이 생긴다(머리 0, 본문 1, 3 · 개수 3). 형제 WG
    # 파서처럼 남긴 청크에 차례대로 다시 매긴다. 청크 ID 는 절 순번을 그대로 둔다 — 포인트 신원이 md5(chunkId)
    # 라 ID 를 바꾸면 같은 본문이 새 포인트로 다시 임베딩된다.
    total = len(chunks)
    for i, c in enumerate(chunks):
        c.chunk_index = i
        c.total_chunks = total
        c._crDelProof = del_proof

    return chunks


# =============================================================================
# Main
# =============================================================================

def _harden_per_cr(chunk_dicts: list[dict]) -> list[dict]:
    """HARD_MAX 강제를 CR 하나씩 건다.

    `generate_cr_chunks` 의 chunkIndex · totalChunks 는 그 CR 의 머리 · 본문 청크 전체 안의 순번과 개수다. 공통
    `enforce_hard_max` 는 하나라도 쪼개면 받은 목록 전체에 번호를 다시 매기므로(번호 단위는 호출자가 고른다),
    모든 CR 을 한 목록으로 넘기면 한 CR 만 쪼개져도 다른 CR 의 번호가 전체 목록 기준으로 바뀐다. CR 은 청크 ID 를
    만드는 `tdocNumber` 로 가른다. CR 마다 청크를 이어 붙이므로 이웃한 같은 키를 한 CR 로 묶는다.
    쪼갠 끝에 남은 작은 조각은 같은 청크의 이웃 조각에 원문 그대로 합친다(`cr_split_pieces`).
    """
    out: list[dict] = []
    for _, group in itertools.groupby(chunk_dicts, key=lambda c: c.get("tdocNumber")):
        group = [dict(c) for c in group]
        out.extend(cr_del_state.harden_group(
            group, _enforce_hard_max, cr_split_pieces.merge_small_hardened,
            _count_tokens_exact, _HARD_MAX_TOK, MIN_CHUNK_TOKENS,
            _renumber_chunk_indices, _index_base(group)))
    return out


def main():
    print("=" * 60)
    print("Phase-8 Step-1: CR-Form Structured Chunking (RAN5)")
    print("=" * 60)

    # 1. CR DOCX 파일 수집
    # 모으는 규칙은 cr_inputs(팩 안 하위 폴더 · 확장자 대소문자 포함). 같은 CR 의 사본 중
    # Phase-4 가 기록한 파일을 먼저 두어, 아래 tdoc 중복 건너뛰기가 그 사본을 남기게 한다.
    # 식별자(tdoc · spec · Release)도 그 기록에서 받는다 — 파일명만 읽으면 R5s · `R5_` 이름,
    # TSG 에 바로 낸 CR(RP 번호), 파일명에 spec 이 없는 CR, 서식에만 Release 가 있는 CR 을 잃는다.
    ident = cr_identity.CRIdentity("RAN5", PHASE4_META.parent, INPUT_DIR, _name_tdoc)
    # 주의: 파일 이름의 WG 번호가 다른 WG 인 CR 은 그 WG 가 읽고, 다른 WG 슬롯에 놓인 이 WG 의 CR 은
    # 여기서 읽는다(`cr_other_wg`). 슬롯만 보면 놓인 WG 는 식별자 없는 파일로, 만든 WG 는 빠진 CR 로 센다.
    files, unconverted, other_wg = cr_other_wg.collect("RAN5")
    if other_wg:
        print(f"  다른 WG 번호의 CR 제외(그 WG 가 읽음): {len(other_wg)}개")
    # Phase-4 가 팩 안 CR 폴더의 첨부 문서로 가린 파일은 CR 이 아니다(`cr_attachments`).
    attachments = cr_attachments.recorded_attachments(PHASE4_META)
    candidates = [f for f, _ in cr_inputs.without_covers(files)]
    cr_files = sorted(
        (f for f in candidates if str(f.relative_to(PROJECT_ROOT)) not in attachments),
        key=lambda f: (not ident.recorded(f), str(f)),
    )
    if attachments:
        print(f"  팩 CR 폴더의 첨부 문서 제외: {len(candidates) - len(cr_files)}")
    # 주의: Phase-4 가 CR 서식이 없어 CR 기록에서 뺀 문서(`cr_attachments.split_no_form`)는 팩 안에 놓였어도 CR 이
    # 아니므로 청크로 만들지 않는다. 번호가 아니라 경로로 가린다. RP-240954 의 `R5-244000/` 처럼 표지가 번호를
    # 두는 문서는 표지 행으로 식별되어, 가리지 않으면 CR 본문이 아닌 글이 그 CR 의 청크가 된다.
    no_form = cr_attachments.recorded_no_form(PHASE4_META)
    if no_form:
        before = len(cr_files)
        cr_files = [f for f in cr_files if str(f.relative_to(PROJECT_ROOT)) not in no_form]
        print(f"  CR 서식이 없는 문서 제외: {before - len(cr_files)}")
    unconverted = cr_inputs.selected_unconverted(files, unconverted, project_root=PROJECT_ROOT,
        excluded_paths=set(attachments) | set(no_form))
    if unconverted:
        print("  [ERROR] 선택한 CR 문서를 열 수 없어 기존 청크/통계 출력을 보존합니다: "
              + ", ".join(str(p.relative_to(PROJECT_ROOT)) for p in unconverted))
        return 1
    print(f"\n[1] CR DOCX 파일: {len(cr_files)} · 읽을 수 없는 문서(변환본 없는 .doc · ZIP 아닌 .docx) {len(unconverted)}")
    if not cr_files:
        print("  CR 파일 없음. 종료.")
        return 1

    # 2. Phase-4 메타데이터 로드 (선택)
    # cr_documents.json + crpacks.json 결합 (RAN1 schema 통일)
    phase4_meta = {}
    if PHASE4_META.exists():
        with open(PHASE4_META, encoding="utf-8") as f:
            p4 = json.load(f)
        for doc in p4.get('documents', []):
            tdoc = doc.get('tdoc_number', '')
            if tdoc:
                phase4_meta[tdoc] = {
                    # CR 번호(숫자)와 개정은 따로 받아 청크 머리에서 `cr_identity.cr_label` 로 합친다.
                    'cr_number': doc.get('cr_number', ''),
                    'rev': doc.get('rev', ''),
                    'cr_pack_id': doc.get('cr_pack_id', ''),
                    'meeting': '',          # RAN5 phase-4에 없음
                    'tsg_meeting': '',      # crpacks.json에서 보강
                    'source': '',           # RAN5 phase-4에 없음
                    # 제목은 아래 form 값이 우선이고 Phase-4 값은 form 이 비었을 때의 대체값이다.
                    'title': doc.get('title', '') or '',
                    # 작업 항목은 Phase-4 파서가 CR 서식에서 읽어 둔 값이다. 비워 두면 RAN5 청크만 workItem 이 빈다.
                    'work_item': doc.get('work_item', '') or '',
                }
        # crpacks.json에서 tsg_meeting 보강
        crpacks_path = PHASE4_META.parent / "crpacks.json"
        if crpacks_path.exists():
            with open(crpacks_path, encoding="utf-8") as f:
                cp = json.load(f)
            for pack in cp.get('packs', []):
                tsgm = pack.get('tsgMeeting', '')
                pack_id = pack.get('crPackId', '')
                for tdoc in pack.get('tdocNumbers', []):
                    if tdoc in phase4_meta:
                        phase4_meta[tdoc]['tsg_meeting'] = tsgm
                        if not phase4_meta[tdoc].get('cr_pack_id'):
                            phase4_meta[tdoc]['cr_pack_id'] = pack_id
        print(f"[2] Phase-4 메타: {len(phase4_meta)} CR")
    else:
        print("[2] Phase-4 메타: 파일 없음 (파일명 기반 추출)")

    # 3. 파싱
    print("\n[3] 파싱 시작...")
    all_chunks = []
    strategy_count = Counter()
    unchanged_omitted: list[dict] = []
    parse_errors = 0
    error_files = []  # 실패자 목록은 자르지 않는다 — 수만 남으면 어느 CR 이 빠졌는지 되짚을 길이 없다
    no_chunk_tdocs = []  # 표지도 본문도 비어 청크를 못 낸 CR
    skip_count = 0
    skipped: list[Path] = []  # tdoc 없는 파일. 루프 뒤에 CR 이 아닌 문서와 실패로 가른다.
    dup_skip = 0  # 중복 tdocNumber skip
    processed = 0
    seen_tdocs = set()  # 이미 처리한 tdocNumber
    strict_opened = 0  # Strict 이름공간이라 이름을 맞춰 연 벌

    reader = _Reader()
    try:
        for i, cr_path in enumerate(cr_files):
            try:
                # 문서를 열기 전에 tdocNumber 로 중복 체크 (DOCX open 비용 회피)
                rec = ident.record(cr_path)
                m = re.search(r'(R5-\d{6})', cr_path.name)
                pre_key = rec["tdoc_number"] if rec else (m.group(1) if m else None)
                if pre_key and pre_key in seen_tdocs:
                    dup_skip += 1
                    if (i + 1) % 1000 == 0:
                        print(f"  진행: {i+1}/{len(cr_files)} ({(i+1)*100//len(cr_files)}%) | "
                              f"chunks={len(all_chunks)} | errors={parse_errors} | dup_skip={dup_skip}")
                    continue

                form, proposal, error, strict = reader.read(str(cr_path))
                strict_opened += strict
                if form is None:
                    raise RuntimeError(error)
                if rec:
                    form.tdoc_number = rec["tdoc_number"]
                    form.spec_number = rec.get("spec_number") or form.spec_number
                    form.release = rec.get("release") or form.release

                if not form.tdoc_number:
                    skip_count += 1
                    skipped.append(cr_path)
                    continue

                from tdoc_body_source_metadata import validate_source_selection
                validate_source_selection(PROJECT_ROOT, WG, 'cr', form.tdoc_number, [cr_path])

                # 중복 체크 (파일명 외 Form에서 추출한 경우)
                if form.tdoc_number in seen_tdocs:
                    dup_skip += 1
                    continue
                seen_tdocs.add(form.tdoc_number)

                if proposal is None:
                    raise RuntimeError(error)
                body_text, body_sections, has_tables, has_figures = proposal
                # phase4_meta 주입 + cr_number 추출
                p4_for_tdoc = phase4_meta.get(form.tdoc_number, {})
                # 머리의 CR 번호는 RAN1~RAN4 와 같은 `CR0123r1` 꼴이다. Phase-4 기록의 번호와 개정을 공용 라벨로
                # 합치고, CR 시트가 그 쌍에 다른 번호를 두면 시트 값으로 적는다(형제 WG 파서와 같은 함수).
                cr_number_val = tsg_cr_decision.sheet_cr_label(
                    cr_identity.cr_label(p4_for_tdoc), form.tdoc_number, p4_for_tdoc.get('cr_pack_id', '')
                ) if p4_for_tdoc else ''
                omitted: list[str] = []
                chunks = generate_cr_chunks(
                    form, body_text, body_sections, has_tables, has_figures,
                    phase4_meta=p4_for_tdoc, cr_number=cr_number_val, omitted=omitted,
                )

                if chunks:
                    strategy_count[chunks[0].strategy] += 1
                    if omitted:
                        unchanged_omitted.append({"tdocNumber": form.tdoc_number,
                                                  "specNumber": form.spec_number, "sections": omitted})
                    all_chunks.extend(chunks)
                else:
                    # 청크가 없으면 이 tdoc 을 닫지 않는다 — 다른 Release 폴더의 사본이 읽힐 수 있다
                    seen_tdocs.discard(form.tdoc_number)
                    no_chunk_tdocs.append(f"{form.tdoc_number}: {cr_path.name}")
                    continue

                processed += 1
                if (i + 1) % 1000 == 0:
                    print(f"  진행: {i+1}/{len(cr_files)} ({(i+1)*100//len(cr_files)}%) | "
                          f"chunks={len(all_chunks)} | errors={parse_errors} | dup_skip={dup_skip}")

            except Exception as e:
                parse_errors += 1
                error_files.append(f"{cr_path.name}: {e}")
                if parse_errors <= 5:
                    print(f"  [ERROR] {cr_path.name[:50]}: {str(e)[:60]}")

    finally:
        reader.close()

    # Source-ledger CRs outside the CR-pack inventory use the same body parser.
    from tdoc_source_supplements import validated_records
    from tdoc_supplement_vectors import parse_cr_supplements
    supplements = parse_cr_supplements(sys.modules[__name__],
                                      validated_records(PROJECT_ROOT, 'RAN5'),
                                      {c.tdoc_number for c in all_chunks})
    if supplements:
        all_chunks.extend(supplements)
        added_tdocs = {c.tdoc_number for c in supplements}
        processed += len(added_tdocs)
        for target in added_tdocs:
            strategy_count[next(c.strategy for c in supplements if c.tdoc_number == target)] += 1

    # tdoc 없는 파일 가운데 TSG 직접 제출 문서와 청크를 낸 CR 폴더의 첨부는 CR 이 아니다(`cr_attachments`).
    # 이 둘은 성공률의 분모에서도 뺀다. 나머지는 번호를 못 읽은 CR 일 수 있어 실패로 남는다.
    not_cr, unidentified = cr_attachments.split_unidentified(
        [str(p.relative_to(PROJECT_ROOT)) for p in skipped], PHASE4_META,
        {c.tdoc_number for c in all_chunks}, _FOLDER_TDOC_RE)
    not_cr_count = sum(len(v) for v in not_cr.values())
    # 루프 앞에서 이미 뺀 문서라 성공률 분모에서 다시 빼지 않도록 `not_cr_count` 다음에 더한다.
    not_cr[cr_attachments.NO_FORM_KEY] = sorted(no_form)

    print(f"\n  처리 완료: {processed} / {len(cr_files)}")
    print(f"  Strict 이름공간으로 연 문서: {strict_opened}")
    print(f"  skip (no tdoc): {skip_count} · CR 이 아닌 문서 TSG 직접 제출 {len(not_cr['tsg_direct'])} · "
          f"CR 폴더 첨부 {len(not_cr['folder_attachment'])} · "
          f"CR 서식 없음 {len(not_cr[cr_attachments.NO_FORM_KEY])} · 식별 실패 {len(unidentified)}")
    print(f"  dup_skip (중복 tdoc): {dup_skip}")
    print(f"  errors: {parse_errors}")
    print(f"  총 청크: {len(all_chunks)}")
    print(f"  Strategy 분포: {dict(strategy_count)}")
    print(f"  변경 표시 없는 절 제외: CR {len(unchanged_omitted)}개 · "
          f"절 {sum(len(o['sections']) for o in unchanged_omitted)}개")

    if parse_errors or unconverted or unidentified:
        print("  [ERROR] 선택한 CR 입력을 모두 읽지 못해 기존 출력을 유지합니다.")
        return 1

    # 4. 출력 저장
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "metadata": {
            "wg": "RAN5",
            "phase": "phase-8",
            "parseDate": datetime.now().isoformat(),
            "totalFiles": len(cr_files) + len({c.tdoc_number for c in supplements}),
            "unconvertedDoc": [str(p.relative_to(PROJECT_ROOT)) for p in unconverted],
            "processed": processed,
            "errors": parse_errors,
            "errorFiles": error_files,
            "noChunkTdocs": no_chunk_tdocs,
            "skipped": skip_count,
            "notCr": {k: len(v) for k, v in not_cr.items()},
            "notCrFiles": not_cr,
            "unidentifiedFiles": unidentified,
            "dupSkipped": dup_skip,
            "strictNamespaceOpened": strict_opened,
            "totalChunks": len(all_chunks),
            "sourceSupplements": sorted({c.tdoc_number for c in supplements}),
            "strategyDistribution": dict(strategy_count),
            "unchangedSectionsOmitted": sum(len(o["sections"]) for o in unchanged_omitted),
        },
        "chunks": [
            {
                # RAN1~4 schema 통일 — text/bodySnippet/crNumber/crPackId/
                # meeting/sectionIds/source/title/totalChunks/tsgMeeting/workItem/
                # chunkSectionId/chunkIndex 추가
                "chunkId": c.chunk_id,
                "tdocNumber": c.tdoc_number,
                "chunkType": c.chunk_type,
                "sectionTitle": c.section_title,
                "text": c.content,                  # RAN1 통일: 'text' 키 사용
                "tokenCount": c.token_count,
                "strategy": c.strategy,
                "specNumber": c.spec_number,
                "release": c.release,
                "category": c.category,
                "clausesAffected": c.clauses_affected,
                "hasTables": c.has_tables,
                "hasFigures": c.has_figures,
                # RAN1 통일 메타
                "crNumber": c.cr_number,
                "crPackId": c.cr_pack_id,
                "meeting": c.meeting,
                "tsgMeeting": c.tsg_meeting,
                "source": c.source,
                "title": c.title,
                "workItem": c.work_item,
                "sectionIds": c.section_ids,
                "chunkSectionId": c.chunk_section_id,
                "chunkIndex": c.chunk_index,
                "totalChunks": c.total_chunks,
                "bodySnippet": c.body_snippet,
                "_crDelProof": c._crDelProof,
            }
            for c in all_chunks
        ],
    }

    # 4.5 HARD_MAX 강제 (정규 프로세스 hardening)
    output["metadata"]["delStateProof"] = cr_del_state.proof_summary(output["chunks"])
    _pre_count = len(output["chunks"])
    output["chunks"] = _harden_per_cr(output["chunks"])
    from tdoc_classification_views import phase8_classified_chunks, phase4_records, source_body_rows
    source_chunks = phase8_classified_chunks(sys.modules[__name__],
        source_body_rows(PROJECT_ROOT, WG), phase4_records(sys.modules[__name__]),
        existing_tdocs={c['tdocNumber'] for c in output['chunks']})
    output['chunks'].extend(source_chunks)
    source_targets = sorted({c['tdocNumber'] for c in source_chunks})
    processed += len(source_targets)
    output['metadata']['sourceClassifications'] = source_targets
    output['metadata']['totalFiles'] += len(source_targets)
    output['metadata']['processed'] += len(source_targets)
    for target in source_targets:
        strategy = next(c['strategy'] for c in source_chunks if c['tdocNumber'] == target)
        output['metadata']['strategyDistribution'][strategy] = output['metadata']['strategyDistribution'].get(strategy, 0) + 1
    if len(output["chunks"]) != _pre_count:
        print(f"  HARD_MAX hardening: {_pre_count} → {len(output['chunks'])} chunks (force-split 적용)")
    from tdoc_body_source_metadata import project as project_body_source_metadata
    output['chunks'] = [project_body_source_metadata(PROJECT_ROOT, WG, 'cr', c['tdocNumber'], c)
                        for c in output['chunks']]
    output["metadata"]["totalChunks"] = len(output["chunks"])

    # 입력이 있는데 청크가 하나도 없으면 이 실행은 실패다. 앞 세대 출력은 그대로 둔다.
    # 덮어쓰면 다음 적재와 Phase-11 CR-2 가 빈 세대를 정상 결과로 받는다.
    if not output["chunks"]:
        for e in error_files:
            print(f"    {e}")
        print(f"  CR 파일 {len(cr_files)}개에서 청크를 하나도 만들지 못함 "
              f"(오류 {parse_errors} · 청크 없음 {len(no_chunk_tdocs)} · tdoc 없음 {skip_count}). "
              f"앞 세대 출력을 두고 실패로 끝낸다.")
        return 1

    out_path = OUTPUT_DIR / "ran5_cr_chunks.json"
    # 다 쓴 뒤에 이름을 바꿔 넣는다. 쓰다가 멈춰도 앞 세대 파일은 온전히 남는다.
    write_json_atomic(out_path, output)
    print(f"\n[4] 저장: {out_path} ({len(output['chunks'])} chunks)")

    # 5. 통계 저장
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stats_path = LOG_DIR / "parse_stats.json"
    write_json_atomic(stats_path, dict(output["metadata"], unchangedSectionsOmitted=unchanged_omitted))
    print(f"  통계: {stats_path}")

    # 6. 성공률 검증
    # 분모는 연 CR 문서다. dup_skip 은 이미 파싱한 CR 의 다른 Release 폴더 사본이고, not_cr 은 CR 이 아닌
    # 문서(TSG 직접 제출 · CR 폴더 첨부)라 둘 다 실패가 아니다.
    attempted = output['metadata']['totalFiles'] - dup_skip - not_cr_count
    success_rate = processed / attempted * 100 if attempted else 0
    print(f"\n{'=' * 60}")
    print(f"성공률: {success_rate:.1f}% ({processed}/{attempted}, 중복 사본 {dup_skip} · CR 이 아닌 문서 {not_cr_count} 제외)")
    if success_rate >= 95:
        print("✅ 품질 검증 통과")
    else:
        print(f"⚠️ 품질 검증 실패: {success_rate:.1f}% < 95%")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
