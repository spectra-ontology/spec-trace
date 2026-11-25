#!/usr/bin/env python3
"""
Phase-6 Tdoc Parser - Vector DB용 파싱 파이프라인
Spec: docs/tsg/RAN/formal/RAN4/phase-6/design-spec/tdoc_vectordb_specs(Tdoc).md

구조:
- 1-1: 공통 기반 (문서 로더, 문단 · 표 읽기, 헤더/푸터 제외, 제외 영역 감지)
- 1-2: 문서 유형 분류 (CR-Form, LS, report, discussion)
- 1-3: 유형별 파서 (분기 처리)
- 1-4: 섹션 추출기 (헤딩 + 정규식 폴백)
- 1-5: 콘텐츠 추출 (본문, 테이블, 캡션, 수식 주변, 각주, Agreement 박스)
- 1-6: 청킹 엔진 (100-2000 토큰, 오버랩 100)
- 1-7: 메타데이터 연동 (meeting_id 변환, Neo4j 조회)
- 1-8: 출력 생성 (vectordb/parsed/tdocs/{wg}/)
"""

import json
import os
from html import escape as html_escape
import re
import zipfile
import functools
import hashlib
from pathlib import Path
from dataclasses import dataclass, field, asdict
from xml.etree import ElementTree as ET

from docx.oxml.ns import qn
from docx.styles import BabelFish
from docx.table import Table
from docx.text.paragraph import Paragraph

# === 정규 프로세스 hardening ===
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[7] / "scripts" / "common"))
from common.chunker import enforce_hard_max as _enforce_hard_max, HARD_MAX_DEFAULT as _HARD_MAX_TOK

# 자격증명의 정본은 저장소 루트의 `.env` 한 벌이고, 그것을 읽는 자리도 한 곳이다.
# 자리마다 평문 대신값을 두면 그 대신값이 곧 두 번째 정본이 되어 정본이 갈린다.
_SCRIPTS_COMMON = Path(__file__).resolve().parents[7] / "scripts" / "common"
if str(_SCRIPTS_COMMON) not in _sys.path:
    _sys.path.insert(0, str(_SCRIPTS_COMMON))
from common import credentials, service_endpoints as endpoints  # noqa: E402
from common.atomic_io import write_json_atomic, write_text_atomic

# TDoc 폴더 이름 → 번호 규칙의 정본. 파생 식별자 게이트(check_tdoc_identifier_hygiene)가 같은 규칙으로 잰다.
from common.tdoc_number import parent_tdoc_number, tdoc_number_of  # noqa: E402

# 문단 · 표 칸을 읽는 규칙(변경 표시는 바뀐 뒤의 글 · 틀 안의 글 · 블록 sdt · 칸 안 표)의 정본.
# 제목 · 영역 판정은 수식을 뺀 `final_text`, 청크 본문은 수식 자리에 선형 표기를 넣는 `chunk_text` 로 읽는다.
_sys.path.insert(0, str(_SCRIPTS_COMMON.parent / "tsg" / "RAN" / "formal" / "common"))
import docx_text  # noqa: E402
# 그림 개체 · 그림 캡션 짝 · 표 캡션 규칙의 정본 — 그림 보강(04)과 같은 규칙을 쓴다.
import docx_figures  # noqa: E402
# 같은 이름의 `.docx` · `.doc` 변환본 쌍을 한 판으로 줄이는 규칙의 정본 — CR 입력(`cr_inputs`)과 같은 규칙을 쓴다.
import docx_pick  # noqa: E402


# XML 네임스페이스 (zipfile+ET fast path용)
_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

# 목차 항목 문단의 스타일(이름 'toc 1' · id 'TOC1' · 현지화 id 'Contents1'). 목차는 제외 영역이다(Spec §1.3).
_TOC_ENTRY_STYLE = re.compile(r'^(toc|contents)\s*\d', re.IGNORECASE)
# 목차 항목의 꼬리 — 탭 뒤 쪽 번호. 목차 스타일을 쓰지 않은 손 목차도 번호 제목으로 읽히지 않게 한다.
_TOC_PAGE_TAIL = re.compile(r'\t\s*\d+\s*$')
_W_P = f"{{{_W_NS}}}p"

# 대체 제목(Spec §3.1 청크 단위의 제목 판정 3)의 번호 줄 꼴 — 번호 · 구분(빈칸 또는 탭) · 제목 글. 번호 뒤에는 구분 다음 바로 글이
# 와야 한다 — 공백 뒤 탭(`2. \tThe …`)은 들여 쓴 번호 목록이고, 탭 둘(`30.04.2024\t\t…`)은 변경 이력 줄이다.
_HEADING_SPACE = re.compile(r'^(\d+(?:\.\d+)*\.?) +(\S.*)$')
_HEADING_TAB = re.compile(r'^(\d+(?:\.\d+)*\.?)\t(\S.*)$')
# 개요 수준을 선언해도 절 제목이 아닌 스타일 — 문서 제목(표지) 자리다.
_DOC_TITLE_STYLES = frozenset({"Title", "Subtitle"})
# 3GPP 문서 양식의 목록 스타일(B1~B5, 들여쓰기 단계). 번호로 시작해도 목록 항목이라 대체 제목에서 뺀다.
_LIST_STYLE = re.compile(r'^B\d\+?$')
# 번호 자리의 규격 번호('36.508 CRs') — 절 번호가 아니다.
_SPEC_NUMBER = re.compile(r'^\d{2}\.\d{3}$')
# 여러 단 번호 + 빈칸 줄에서 번호가 값이고 뒤 낱말이 단위인 꼴('0.5 dB …' · '0.5 Mbps …'). '/' 로 이은 복합
# 단위는 앞뒤를 따로 맞추고, 뒤쪽의 앞자리 수는 떼고 본다('49.3 dBm/3MHz …').
_UNIT_WORDS = frozenset({"db", "dbm", "dbi", "dbc", "hz", "khz", "mhz", "ghz", "ms", "us", "µs", "ns", "s", "km", "m",
                         "bps", "kbps", "mbps", "gbps", "%"})
# 제목 첫 낱말이 부호 붙은 수인 꼴('5.25 –3.75A\t\t; 0.2< A ≤0.6') — 번호가 아니라 값 · 수식 줄이다.
_SIGNED_TERM = re.compile(r'^[−–+±-]\d')
# 한 단 번호 제목의 낱말 수 상한. 스타일 제목(Heading 1)은 거의 모두 이 안에 들고, 이보다 긴 한 단 번호 줄은
# 대부분 번호 목록 항목 · 제안 문장이다(실측은 Spec §3.1).
_ONE_LEVEL_MAX_WORDS = 10


def _number_line(text: str, style: str) -> tuple[str, str, str] | None:
    """번호 줄이면 (번호, 구분, 제목 글). 목차 꼬리가 있거나 목록 스타일이면 None."""
    if not text or _TOC_PAGE_TAIL.search(text) or _LIST_STYLE.match(style):
        return None
    m = _HEADING_SPACE.match(text)
    if m:
        return m.group(1), ' ', m.group(2)
    m = _HEADING_TAB.match(text)
    if m:
        return m.group(1), '\t', m.group(2)
    return None


def _one_level_line(text: str, style: str, outline: int | None) -> bool:
    """스타일 제목 · 개요 · 목차 문단이 아닌 한 단 번호 줄인가 — 이웃 줄지음을 볼 때 쓴다."""
    if style.startswith('Heading') or outline is not None or _TOC_ENTRY_STYLE.match(style):
        return False
    line = _number_line(text, style)
    return line is not None and '.' not in line[0].rstrip('.')


def _fallback_reject(number: str, sep: str, title: str, lined_up: bool) -> str | None:
    """번호 줄을 대체 제목으로 받지 않는 까닭, 받으면 None.

    번호 단 수와 상관없이 제목 첫 낱말이 부호 붙은 수면('5.25 –3.75A') 값 줄이다.
    여러 단 번호: 번호가 규격 번호('36.508 CRs') · 제목 첫 낱말에 글자가 없음('1.96 * UC.' 의 '*'). 빈칸
    구분이면 첫 낱말이 단위('0.5 dB' · '0.5 Mbps' · '49.3 dBm/3MHz') · 소문자 낱말('9.2 deg for FR1')일 때도. 탭 구분은 소문자 낱말을 막지
    않는다 — 탭 꼴은 값 줄에 드물고 '5.2\tvoid' 같은 진짜 제목이 있다. 첫 낱말에 글자가 하나라도 있으면
    글자로 시작하지 않아도 받는다('∆TIB' · '(Void)' · '[Reserved]' · '2RX TDD …').
    한 단 번호: 빈칸 구분은 번호 뒤 점이 있어야 한다('2 Tx in CC2 …' 는 값이다). 탭 구분은 점이 없어야
    한다('1.\tThe UE …' 는 B1 · Doc-text2 같은 번호 목록이다). 앞뒤 글 있는 문단이 한 단 번호 줄이면
    번호 목록이다. 마침표로 끝나면 문장이다. 첫 낱말에 글자가 없으면('; \t5.4 ≤ B') 수식 조각이다. 낱말이
    `_ONE_LEVEL_MAX_WORDS` 보다 많으면 목록 항목 · 제안 문장이다.
    """
    words = title.split()
    if not any(ch.isalpha() for ch in words[0]):
        return "no-letter"
    if _SIGNED_TERM.match(words[0]):
        return "signed-term"
    if '.' in number.rstrip('.'):
        if _SPEC_NUMBER.match(number.rstrip('.')):
            return "spec-number"
        if sep == ' ':
            first = words[0].rstrip(',.;:')
            unit, _, per = first.lower().partition('/')
            if unit in _UNIT_WORDS and (not per or per.lstrip('0123456789.') in _UNIT_WORDS):
                return "unit"
            if re.fullmatch(r'[a-z]+', first):
                return "lowercase"
        return None
    if number.endswith('.') != (sep == ' '):
        return "form"
    if lined_up:
        return "lined-up"
    if title.rstrip().endswith('.'):
        return "period"
    if len(words) > _ONE_LEVEL_MAX_WORDS:
        return "too-long"
    return None


def _headings(texts: list[str], styles: list[str], outlines: list) -> list[tuple[str, int] | None]:
    """문단마다 절 제목이면 (제목, 수준), 아니면 None — Spec §3.1 의 차례대로 Heading 스타일 이름 ·
    스타일이 선언한 개요 수준 · 번호 줄. 목차 스타일 문단은 어느 규칙으로도 제목이 아니다. 번호 줄은
    앞뒤 글 있는 문단을 함께 본다(`_fallback_reject`)."""
    filled = [i for i, t in enumerate(texts) if t]
    one = {i for i in filled if _one_level_line(texts[i], styles[i], outlines[i])}
    out: list[tuple[str, int] | None] = [None] * len(texts)
    for pos, i in enumerate(filled):
        text, style, outline = texts[i], styles[i], outlines[i]
        if _TOC_ENTRY_STYLE.match(style):
            continue
        if style.startswith('Heading'):
            try:
                out[i] = text, int(style.replace('Heading', '').strip())
            except ValueError:
                out[i] = text, 1
            continue
        if outline is not None:
            out[i] = text, outline + 1
            continue
        line = _number_line(text, style)
        if line is None:
            continue
        number, sep, title = line
        lined_up = (pos > 0 and filled[pos - 1] in one) or (pos + 1 < len(filled) and filled[pos + 1] in one)
        if _fallback_reject(number, sep, title, lined_up) is None:
            out[i] = f"{number} {title}", len(re.findall(r'\d+', number))
    return out


# 표지(Spec §1.3 · §2.2 — TDoc 번호 · 회의 · Source · Title 등)는 문서 첫 줄에서 시작하는 한 덩어리다.
# 머리줄은 회의 이름 줄이고 양식이 WG · 회의마다 갈린다('3GPP TSG RAN WG<n> #<번호>bis' · 'TSG-RAN WG<n> #<번호>' ·
# '3GPP RAN<n>#<번호>' · '3GPP RAN WG<n> Meeting #<번호>' · 'TSG-RAN Working Group <n> (Radio) meeting' 꼴, 다른 TSG
# 에서 온 LS 의 '3GPP SA WG<n> Meeting #<번호>' 꼴). 그래서 줄 머리에서 3GPP · TSG 뒤에 TSG · RAN · SA · CT · WG 가 오는지로
# 본다. 머리의 낱자 하나('F3GPP …')와 '3' 이 빠진 'GPP TSG …' 는 입력 잡티다.
_COVER_HEADER = re.compile(r'^[\W_]*\w?(3?GPP|TSG)[\s_-]*(TSG|RAN|SA|CT|WG|R\d)', re.IGNORECASE)
# 줄 끝의 TDoc 번호도 머리줄이다 — 회의 이름 앞에 다른 글이 붙고 탭 뒤에 번호가 오는 줄, 번호만 따로 둔
# 줄('R4-2112145'). 번호를 아직 받지 않은 자리표(끝자리를 X 로 채운 번호)와 개정 전 번호를 괄호로 덧붙인
# 줄도 있다.
_COVER_TDOC = re.compile(r'(^|\t| {2,})[A-Z][A-Z0-9]{0,2}-[\dXx]{4,8}\w*(\s*\([^()]*\))?\s*$')
# 표지 이름표 줄 — 다섯 WG 표본에서 머리줄과 본문 사이에 나온 이름표(오타 'Souce' 포함). 이름표와 값은 쌍점이나
# 탭으로 가른다('Source:\tHuawei' · 'Title\t\tUE behaviour …').
_COVER_LABEL = re.compile(
    r'^[\W_]*(agenda(\s*item)?(\(s\))?|source|souce|title|document\s*(for|type)|meeting|release|work\s*item|'
    r'wi(\s*code)?(\(s\))?|wi/si|wid/sid|study\s*item|response\s*to|reply\s*to|type|moderator)\s*[:\t]',
    re.IGNORECASE)
# 머리줄 뒤 회의 장소 · 날짜 줄 — 연도, 날과 달 이름('16th – 20th April' · 'Oct 14th' · 'Nov.27'), 양식 자리표
# ('<Location>, <Country>'), 비대면 회의 이름('Online' · 'Electronic Meeting'), 도시와 나라만 쓴 줄('Incheon, South Korea').
_MONTH = (r'(Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|June?|July?|Aug(ust)?|Sep(t(ember)?)?|Oct(ober)?'
          r'|Nov(ember)?|Dec(ember)?)\b')
_COVER_WHEN_WHERE = re.compile(
    r'\b(19|20)\d\d\b'
    rf'|\b\d{{1,2}}(st|nd|rd|th)?[\s.\-–—]*{_MONTH}'
    rf'|\b{_MONTH}\.?\s*\d{{1,2}}(st|nd|rd|th)?\b'
    r'|<\s*(?i:location|country|city|start_?date|end_?date|date)\s*>'
    r'|^\W*(?i:(online|virtual|electronic)(\s+meeting)?|e-?meeting)\W*$'
    r"|^[A-Z][\w.'’\- ]{1,30}(,\s*[A-Z][\w.'’\- ]{1,30}){1,3},?\s*$")
# Work Item 값이 여러 줄로 이어진 표지 — 이름표 줄 뒤에 밑줄을 담은 WI 코드만 늘어놓은 줄('NR_channel_raster_enh').
_COVER_WI = re.compile(r'^[\W_]*(work\s*item|wi(\s*code)?(\(s\))?|wi/si|wid/sid)\s*[:\t]', re.IGNORECASE)
_WI_CODE_LINE = re.compile(r'^\s*[\w.\-]*_[\w.\-]*(\s*[,;/]\s*[\w.\-]+)*[,;]?\s*$')


def _cover_head(text: str) -> bool:
    """회의 이름 줄이나 TDoc 번호로 끝나는 줄."""
    return bool(_COVER_HEADER.match(text) or _COVER_TDOC.search(text))


def _cover_anchor(text: str, labels_seen: bool) -> bool:
    """사이 줄 바로 뒤에 와서 그 줄을 표지로 묶어 주는 줄 — 이름표 줄, 이름표 앞이면 머리줄과 장소 · 날짜 줄."""
    return bool(_COVER_LABEL.match(text)
                or (not labels_seen and (_cover_head(text) or _COVER_WHEN_WHERE.search(text))))


def _cover_lines(lead: list[tuple[int, str]]) -> set[int]:
    """표지 줄의 문단 번호. lead = 첫 표 앞 본문 문단의 (문단 번호, 글).

    덩어리는 첫 글 줄이 머리줄이나 이름표 줄일 때만 있다. 머리줄 · 장소와 날짜 줄이 먼저 오고
    이름표 줄(Agenda item · Source · Title · Document for …)이 뒤따른다. Work Item 이름표 뒤에 WI 코드만
    늘어놓은 줄은 그 값이다. 두 표지 줄 사이에 낀 한 줄(두 줄로 넘친 제목 · 개정 번호)도 표지다. 그 밖의
    줄을 만나면 덩어리가 끝나고 뒤는 모두 본문이다 — 본문 안에서 이름표처럼 보이는 줄은 지우지 않는다.
    """
    lines = [(i, t) for i, t in lead if t]
    cover = set()
    labels_seen = wi_value = False
    for k, (i, t) in enumerate(lines):
        wi_codes = wi_value and bool(_WI_CODE_LINE.match(t))
        if _COVER_LABEL.match(t):
            labels_seen = True
        elif wi_codes or (not labels_seen and (_cover_head(t) or (k > 0 and _COVER_WHEN_WHERE.search(t)))):
            pass
        elif not (k > 0 and k + 1 < len(lines) and _cover_anchor(lines[k + 1][1], labels_seen)):
            break
        cover.add(i)
        wi_value = bool(_COVER_WI.match(t)) or wi_codes
    return cover


def _cover_table_count(tables, texts: list[str], before: list[int], keywords) -> int:
    """문서 맨 앞의 회의 머리 표 수(0 · 1) — 이 표는 표지다(Spec §1.3).

    머리줄을 표 칸에 넣은 문서는 첫 표 앞에 글이 없고 이름표 줄(Agenda item · Source …)이 그 표
    뒤 문단으로 온다. 첫 표 앞만 표지 자리로 보면 이 문서의 표지는 통째로 본문에 남는다.
    첫 칸이 CR 양식 키워드를 담은 표는 양식이므로 머리 표로 치지 않는다.
    """
    if not tables or any(t for t, b in zip(texts, before) if b == 0):
        return 0
    rows = docx_text.table_rows(tables[0])
    cell = rows[0][0].strip() if rows and rows[0] else ""
    return int(bool(_COVER_HEADER.match(cell)) and not any(k in cell for k in keywords))


def _tables_before(body) -> list[int]:
    """본문 문단마다 그 앞에 놓인 최상위 표 수 — 문단 번호는 `_paragraphs` · `_fast_load_blocks` 와 같다."""
    counts, n = [], 0
    for b in docx_text.iter_blocks(body):
        if b.tag == _W_P:
            counts.append(n)
        else:
            n += 1
    return counts


# 목차 항목과 제목을 맞대는 꼴 — 'N\t제목\t쪽' 처럼 번호와 제목을 탭으로 가르거나, 제목 쪽 번호가 자동
# 번호라 글에 없을 수 있어서 첫 탭 앞 머리를 뗀 꼴과 '3.' · '4.2 ' · 'Proposal 2:' 같은 번호 머리를 뗀 꼴도 본다.
_TOC_NUM_HEAD = re.compile(r'^(\w+\s+)?\d+(\.\d+)*[a-z]?[:.)]?\s+')


def _toc_forms(text: str) -> set[str]:
    """목차 항목 · 제목 글을 맞대 보는 꼴 — 쪽 번호 꼬리를 떼고 공백을 하나로, 소문자로. 그대로 · 첫 탭 앞
    머리를 뗀 꼴 · 번호 머리를 뗀 꼴."""
    t = _TOC_PAGE_TAIL.sub('', text).strip()
    whole = re.sub(r'\s+', ' ', t).lower()
    forms = {whole, _TOC_NUM_HEAD.sub('', whole)}
    if '\t' in t:
        forms.add(re.sub(r'\s+', ' ', t.split('\t', 1)[1]).strip().lower())
    return {f for f in forms if f}


def _toc_entries(texts: list[str], styles: list[str], heading_at: list) -> set[int]:
    """목차 항목 문단 번호(Spec §1.3 의 목차).

    목차 스타일(`toc N` · `Contents N`) 문단 가운데 쪽 번호 꼬리가 있거나 문서 안 제목과 같은 글인 것.
    Word 목차 필드가 만든 결론의 'Observation N' · 'Proposal N' 목록은 목차 스타일이 달려 줄지어 있어도
    쪽 번호가 없고 제목이 아니라 본문 문단을 되풀이하므로 본문에 남는다. 스타일만 잘못 단 본문 줄도 그렇다.
    """
    toc = [i for i, t in enumerate(texts) if t and _TOC_ENTRY_STYLE.match(styles[i])]
    if not toc:
        return set()
    entries = {i for i in toc if _TOC_PAGE_TAIL.search(texts[i])}
    rest = [i for i in toc if i not in entries]
    if rest:
        tocset, heads = set(toc), set()
        for i, t in enumerate(texts):
            if t and i not in tocset and heading_at[i] is not None:
                heads |= _toc_forms(t)
        entries.update(i for i in rest if _toc_forms(texts[i]) & heads)
    return entries


# 참고문헌 목록 줄 — 번호를 달아도 절 제목이 아니다('[1] …' · TDoc 번호로 시작하는 줄 · '3GPP TS 38.213 …').
_REF_ENTRY = re.compile(r'^(\d+(\.\d+)*\.?\s+)?(\[\d+\]|[RS]\d\w*-\d|RP-\d|3GPP\s+T[SR]\b|T[SR]\s*\d)', re.IGNORECASE)
# 목록 줄의 줄 머리 표지 — '[3GPP-1]' · '1)' · '2.' · '3 ' · '• ' · '- '.
_REF_LISTED = re.compile(r'^\s*(\[\s*[\w.\-]+\s*\]|\(?\d+[\].):]|\d+\s|[•\-–·▪●○]\s?)')
# 참고문헌 목록 뒤에 붙는 새 부분의 첫 줄 — 부록('Annex 1' · 'Appendix:') · Text Proposal · 변경 표시
# ('NEXT CHANGE' · '<<< Start of Next Change>>>' · '/*** skip unchanged ***/').
_PART_START = re.compile(r'^\W*(annex\b|appendix\b|text\s+proposals?\b|tp\b.*\bfor\b)|'
                         r'\b(start|end|beginning|begin|first|next|last|\d+(st|nd|rd|th))\b.{0,24}\bchanges?\b|'
                         r'\bunchanged\b', re.IGNORECASE)


def _ref_entry(text: str) -> bool:
    """참고문헌 목록 줄 — 문서 · 규격 번호(`_REF_ENTRY`)나 줄 머리 표지(`_REF_LISTED`)로 시작한다."""
    return bool(_REF_ENTRY.match(text) or _REF_LISTED.match(text))


def _opens_part(text: str) -> bool:
    """참고문헌 목록을 끝내는 새 부분의 첫 줄 — 부록 · Text Proposal · 변경 표시(`_PART_START`), 뒤에 붙인 다른
    문서의 표지 첫 줄(회의 머리줄 + 문서 번호), LS 머리글 줄(`TdocParser.LS_HEADER_LINE`).

    변경 표시는 꾸밈 부호로 길어지기도 한다('////…skip unchanged…////'). 문서 · 규격
    번호로 시작하는 줄은 낱말이 맞아도 목록 줄이다.
    """
    if _REF_ENTRY.match(text):
        return False
    return bool(_PART_START.search(text) or (_COVER_HEADER.match(text) and _COVER_TDOC.search(text))
                or TdocParser.LS_HEADER_LINE.match(text))


_W_TEXT = f"{{{_W_NS}}}t"
_W_INSERTED = {f"{{{_W_NS}}}ins", f"{{{_W_NS}}}moveTo"}
_W_DELETED = {f"{{{_W_NS}}}del", f"{{{_W_NS}}}moveFrom"}


def _inserted_only(p) -> bool:
    """문단의 지워지지 않은 글(`w:t`)이 모두 변경 삽입(`w:ins` · `w:moveTo`) 안에 있는가. 글이 없으면 거짓.

    주의: 빠른 경로(`_fast_layout`)는 ElementTree 요소를 넘겨 `getparent` 가 없다. 그래서 조상을 거슬러
    오르지 않고 문단에서 아래로 내려가며 삽입 · 삭제 안인지를 들고 간다.
    """
    seen = False
    stack = [(p, False, False)]
    while stack:
        e, inserted, deleted = stack.pop()
        inserted = inserted or e.tag in _W_INSERTED
        deleted = deleted or e.tag in _W_DELETED
        if e.tag == _W_TEXT and e.text and not deleted:
            if not inserted:
                return False
            seen = True
        stack.extend((c, inserted, deleted) for c in e)
    return seen


#: Spec 2절(References)의 머리 문장. 기고 자신의 참고문헌 목록에는 오지 않는다.
_SPEC_REFS_PREAMBLE = re.compile(r"constitute provisions of the present document", re.IGNORECASE)


def _keep_inserted_references(marks: dict[int, str], texts: list[str], elems: list, patterns: dict) -> None:
    """참고문헌 영역 가운데 변경 삽입만으로 된 문단이 있는 영역에서 그 문단과 영역 제목 줄의 표시를 푼다.

    영역은 제목 줄(`patterns['references']`)에서 시작해 다음 제목 줄 앞까지의 'references' 문단이다.
    그 영역의 나머지 줄은 'references_unchanged' 로 바꾼다 — 싣지 않되 `_sections_from` 이 그 앞 절을
    닫지 않아, 실은 줄이 제목 줄의 절에 함께 든다.

    주의: Spec 2절의 머리 문장(`_SPEC_REFS_PREAMBLE`)이 든 영역은 기고 자신의 참고문헌이 아니라 옮겨
    적은 Spec 본문이라 영역 전체의 표시를 푼다. 변경 표시 없이 2절을 새로 써 넣은 기고가 있다
    (R3-174308: 37.340 2절의 [1]~[5] 를 고치자는 제안인데 변경 추적이 없다).
    """
    regions: list[list[int]] = []
    for i in sorted(i for i, r in marks.items() if r == "references"):
        if not regions or any(re.match(p, texts[i], re.IGNORECASE) for p in patterns['references']):
            regions.append([i])
        else:
            regions[-1].append(i)
    for region in regions:
        if any(_SPEC_REFS_PREAMBLE.search(texts[i]) for i in region):
            for i in region:
                del marks[i]
            continue
        kept = [i for i in region if _inserted_only(elems[i])]
        if not kept:
            continue
        for i in region:
            marks[i] = "references_unchanged"
        for i in {region[0], *kept}:
            del marks[i]


def _region_marks(texts: list[str], styles: list[str], outlines: list, lead_n: int,
                  patterns: dict, elems: list | None = None) -> dict[int, str]:
    """제외 영역(Spec §1.3)에 든 문단 번호 → 영역 이름('cover' · 'toc' · 'references').

    texts · styles · outlines 는 본문 문단 순서의 글 · 스타일 이름 · 개요 수준, lead_n 은 표지 자리
    문단 수(첫 표 앞, 머리 표가 있으면 둘째 표 앞).
    참고문헌은 제목 줄에서 시작한다. 영역 안 글 있는 문단을 차례로 보며
    - 목록 줄(`_REF_ENTRY`)이 아닌 절 제목이나 새 부분의 첫 줄(`_opens_part`)에서 끝난다 — 뒤의 부록 · 규격
      절 · 붙인 Text Proposal · 변경 본문은 본문이다. 목록 줄은 제목 스타일이나 번호 꼴이어도 영역에 든다.
    - 목록 줄(`_ref_entry`)이거나 영역 첫 줄과 스타일이 같으면 잇는다. 둘 다 아니어도 바로 다음 글 있는
      문단이 목록 줄이면 잇는다 — 작업 계획 목록의 묶음 이름 줄('General Papers' · 'TS 38.508-1 CRs').
    - 그 밖의 줄에서 끝난다 — 목록 뒤 스타일이 다른 본문 줄(양식 개정 이력 'v04.64 …').
    제목에서만 끝내면 제목 스타일 없이 이어지는 부록 · Text Proposal · 변경 본문이 영역에 묻혀 실리지 않는다
    (R4-2204624).

    > 주의: 변경 · TP 표지 뒤의 참고문헌 제목도 영역을 연다. 변경 본문에 실린 규격 2절(R3-182573 의
    > '2References' 와 그 아래 목록)과 끝 표지 없이 TP 뒤에 붙은 기고 자신의 참고문헌(R3-182619 의
    > 'References' 와 'RP-180536, …')은 앞의 표지로 갈리지 않는다. 둘 다 문헌 목록이라 함께 뺀다.
    > 다만 `elems`(문단 요소)가 주어지면 영역 안에서 변경 삽입(`w:ins` · `w:moveTo`)만으로 된 문단은 싣는다
    > (`_keep_inserted_references`). 그 줄은 기고가 제안하는 변경 자체라서다 — R3-182576 은 규격 2절에
    > '[x1] 3GPP TS 23.501' · '[x2] 3GPP TS 38.472' 를 넣는 변경이고, R3-182672 는 2절 전체를 새로 넣는다.
    > 그런 영역은 제목 줄도 싣고(삽입 줄이 어느 목록인지 알게), 바뀌지 않은 목록 줄은 'references_unchanged'
    > 로 표시해 빼되 열린 절을 닫지 않는다. 문서 전체를 변경 표시로 쓴 기고는 자기 참고문헌도 실린다.
    """
    marks = {i: "cover" for i in _cover_lines([(i, texts[i]) for i in range(lead_n)])}
    heading_at = _headings(texts, styles, outlines)
    for i in _toc_entries(texts, styles, heading_at):
        marks.setdefault(i, "toc")
    nonempty = [i for i, t in enumerate(texts) if t]
    next_text = dict(zip(nonempty, nonempty[1:]))

    def ends(i: int) -> bool:
        return (heading_at[i] is not None and not _REF_ENTRY.match(texts[i])) or _opens_part(texts[i])

    in_refs, entry_style = False, None
    for i, text in enumerate(texts):
        if not text or i in marks:
            continue
        if any(re.match(p, text, re.IGNORECASE) for p in patterns['toc']):
            marks[i] = "toc"
            continue
        if any(re.match(p, text, re.IGNORECASE) for p in patterns['references']):
            marks[i] = "references"
            in_refs, entry_style = True, None
            continue
        if in_refs:
            if entry_style is None:
                entry_style = styles[i]
            j = next_text.get(i)
            if ends(i):
                in_refs = False
            elif (_ref_entry(text) or styles[i] == entry_style
                  or (j is not None and not ends(j) and _ref_entry(texts[j]))):
                marks[i] = "references"
            else:
                in_refs = False
    if elems is not None:
        _keep_inserted_references(marks, texts, elems, patterns)
    return marks


# CR 양식(Spec §2.4.1 의 표 1~3 — Cover Sheet · Proposed change affects · 메타데이터) 표 2 · 3 의 줄 머리.
# 낱말 사이 빈칸은 없어도 맞춘다 — LibreOffice 변환본은 이름표의 빈칸을 잃기도 한다('Proposed changeaffects:').
_CR_FORM_ROW = re.compile(
    r'^(proposed\s*change\s*affects|title|source\s*to\s*(wg|tsg)|work\s*item\s*code|date|category|release|'
    r'reason\s*for\s*change|summary\s*of\s*change|consequences\s*if|clauses\s*affected|other\s*specs|'
    r'other\s*comments|this\s*cr)\b', re.IGNORECASE)


def _cr_form_count(tables) -> int:
    """CR 양식 표 수 — 표 1 과, 그 뒤 표 2 · 3 가운데 양식 줄을 담아 이어지는 것까지(많아야 셋).

    양식 표 수는 문서마다 다르다 — 표 둘을 하나로 합친 양식도, 양식 바로 뒤에 변경 본문 표가 오는
    문서도 있다. 자리(처음 셋)로 세면 본문 표를 지우거나 양식 표를 본문에 싣는다."""
    n = 1
    for tbl in tables[1:3]:
        rows = docx_text.table_rows(tbl)
        if not any(_CR_FORM_ROW.match(next((c.strip() for c in r if c.strip()), "")) for r in rows):
            break
        n += 1
    return n


# Spec §1.3 이 포함 대상으로 정한 CR 양식의 기술 설명 칸. 이름표는 글자만 남겨 맞춘다 — 변환본은 낱말 사이
# 빈칸을 잃기도 하고, 옛 양식(CR-Form-v9.6)은 이름표 칸에 도움말 기호를 함께 담고 줄을 바꾼다
# ('Consequences if \t⌘\nnot approved:').
_CR_FORM_FIELDS = {"reasonforchange": "Reason for change", "summaryofchange": "Summary of change",
                   "consequencesifnotapproved": "Consequences if not approved"}


def _cr_form_fields(tables) -> str:
    """CR 양식 표에서 기술 설명 칸(`_CR_FORM_FIELDS`)을 `이름: 값` 줄로 꺼낸다. 값이 빈 칸은 뺀다.

    값은 이름표 칸과 같은 줄의 뒤 칸 글에, 그 아래 줄 가운데 이름표 칸과 그 앞 칸이 빈 줄의 뒤 칸 글을
    더한 것이다. 이름표 칸에 다른 글이 있는 줄에서 멈추고, 세로 병합으로 같은 이름표가 되풀이된 줄에서는
    멈추지 않는다. 값을 이름표 아래 줄에 쓴 양식과 이름표 글이 빠진 줄의 글이 앞 이름표의 값에
    붙는 양식('Summary of change' 이름표 글이 문서에 없어 그 줄 글이 'Reason for change' 에 든다)이
    이 꼴이다. 서식 전체를 한 칸짜리 겉 표에 담은 초안 CR 은 이름표가 칸 안 표에 있어 칸 안 표까지 본다.
    같은 이름표가 값과 함께 다시 나오면 처음 것만 쓴다.
    """
    found: dict[str, str] = {}
    for tbl in tables:
        for t in getattr(tbl, "_tbl", tbl).iter(_W_TBL):
            rows = [[c.strip() for c in cells] for cells in docx_text.table_rows(t)]
            for i, cells in enumerate(rows):
                k = next((j for j, c in enumerate(cells) if c), None)
                if k is None:
                    continue
                name = _CR_FORM_FIELDS.get(re.sub(r'[^a-z]', '', cells[k].lower()))
                if name is None or name in found:
                    continue
                values = [c for c in cells[k + 1:] if c and c != cells[k]]
                for below in rows[i + 1:]:
                    if any(below[:k]) or (len(below) > k and below[k] and below[k] != cells[k]):
                        break
                    values += [c for c in below[k + 1:] if c]
                values = list(dict.fromkeys(values))
                if values:
                    found[name] = "\n".join(values)
    return "\n".join(f"{name}: {value}" for name, value in found.items())
_W_TBL = f"{{{_W_NS}}}tbl"

# Fast path 임계값: 이 문단 수 초과 시 zipfile+ET로 전환
_FAST_PATH_THRESHOLD = 10000


# =============================================================================
# 1-1: 공통 기반
# =============================================================================

@dataclass
class ParsedContent:
    """파싱된 콘텐츠 컨테이너"""
    tdoc_number: str
    doc_type: str  # discussion, CR, draftCR, LS_in, LS_out, report
    sections: list = field(default_factory=list)
    tables: list = field(default_factory=list)
    figures: list = field(default_factory=list)
    equations: list = field(default_factory=list)
    paragraph_count: int = 0


@dataclass
class Section:
    """섹션 데이터"""
    title: str
    level: int  # 1=Heading1, 2=Heading2, etc.
    content: str
    start_idx: int
    end_idx: int


@dataclass
class TableInfo:
    """테이블 정보"""
    table_id: str
    table_number: str
    caption: str
    html: str
    text: str
    equations: list = field(default_factory=list)
    is_agreement_box: bool = False


@dataclass
class FigureInfo:
    """그림 정보"""
    figure_id: str
    figure_number: str
    caption: str
    file_path: str
    more_file_paths: tuple = ()


@dataclass
class EquationInfo:
    """수식 정보"""
    equationId: str
    index: int
    latex: str  # 설계 결정: OMML→LaTeX 변환은 05_enhance_equations.py에서 처리
    context: str
    source: str = "omml"  # "omml" = OMML 수식(`m:oMath`) · "ole" = 수식 개체(`w:object`, ProgID `Equation.`)
    text: str = ""  # 청크 본문이 이 수식 자리에 넣는 선형 글 — OMML 은 `math_linear`, 수식 개체는 `EQUATION_TEXT`


# =============================================================================
# Fast path: zipfile+ElementTree 로 본문 XML 을 한 번에 읽는다 (>10K 문단 문서 · XML 손상 문서)
# 글 읽기 규칙은 python-docx 경로와 같은 docx_text 한 벌이다 — 변경 표시는 바뀐 뒤의 글로 읽는다(Spec §1.3 · §3.6.3).
# 제목 · 영역 판정 글은 수식을 빼고(`final_text`), 청크 본문 글은 수식 자리에 선형 표기를 넣는다(`chunk_text`).
# =============================================================================

def _load_body(docx_path):
    """본문(`w:body`) 요소. 읽을 수 없으면 None."""
    root = _load_part(docx_path, "word/document.xml")
    return None if root is None else root.find(f"{{{_W_NS}}}body")


def _load_part(docx_path, part: str):
    """docx 안 XML 부분의 뿌리 요소. 없거나 읽을 수 없으면 None.

    엄격한 해석기가 거절하면 태그 짝만 고쳐(`docx_text.repair_tag_balance` — 짝 없는 닫는 태그를 빼고,
    바깥 요소의 닫는 태그가 건너뛴 요소를 닫는다) 다시 읽는다. 그래도 거절하면
    lxml 복구 모드로 읽는다(DOC→DOCX 변환 손상 대응). 복구 모드는 망가진 자리에서 열린
    요소를 닫아 뒤의 글을 잃을 수 있고 망가진 자리 뒤에 엔티티로 적은 글자(`&amp;` 등)를 빼고
    읽으므로 마지막 수단이다.
    """
    try:
        with zipfile.ZipFile(str(docx_path), "r") as zf:
            xml_content = docx_text.zip_part(zf, part)
    except Exception:
        return None
    root = None
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        repaired, fixed = docx_text.repair_tag_balance(xml_content)
        if fixed:
            try:
                root = ET.fromstring(repaired)
            except ET.ParseError:
                root = None
        if root is None:
            try:
                from lxml import etree
                root = etree.fromstring(xml_content, etree.XMLParser(recover=True, huge_tree=True))
            except Exception:
                return None
    return root


#: 각주 · 미주 부분과 그 안의 note 요소.
_NOTE_PARTS = (("word/footnotes.xml", f"{{{_W_NS}}}footnote"),
               ("word/endnotes.xml", f"{{{_W_NS}}}endnote"))
_W_TYPE = f"{{{_W_NS}}}type"


def _fast_load_notes(docx_path) -> list[str]:
    """각주 · 미주 글을 note 하나당 한 줄로 (Spec §1.3 포함 대상).

    각주는 본문과 다른 부분(`word/footnotes.xml`)에 있어 본문 문단 목록에 들어오지 않는다.
    `w:type` 이 붙은 note 는 구분선 자리(separator · continuationSeparator)라 뺀다.
    """
    notes = []
    for part, tag in _NOTE_PARTS:
        root = _load_part(docx_path, part)
        if root is None:
            continue
        for note in root.iter(tag):
            if note.get(_W_TYPE):
                continue
            text = " ".join(t for t in (docx_text.chunk_text(p)
                                        for p in docx_text.iter_all_paragraphs(note)) if t)
            if text:
                notes.append(text)
    return notes


def _fast_get_style(p_elem) -> str:
    """w:p 요소에서 스타일명 추출."""
    w_pPr = f"{{{_W_NS}}}pPr"
    w_pStyle = f"{{{_W_NS}}}pStyle"
    pPr = p_elem.find(w_pPr)
    if pPr is not None:
        pStyle = pPr.find(w_pStyle)
        if pStyle is not None:
            return pStyle.get(f"{{{_W_NS}}}val", "")
    return ""


def _style_table(docx_path) -> tuple[dict[str, str], dict[str, int]]:
    """문단 스타일 styleId → 이름, styleId → 개요 수준(0~8).

    이름은 python-docx `style.name` 과 같은 표기로 둔다. styleId 는 현지화된 Word 에서 '30' · '1' ·
    'Titre3' 처럼 바뀌지만 이름은 'heading 3' 으로 남는다. 개요 수준은 스타일이 선언한
    `w:outlineLvl` 이고, 없으면 `w:basedOn` 을 따라 올라가며, 이름이 'heading N' 이면 N-1 이다.
    9 이상은 OOXML 의 본문 수준이라 뺀다.
    """
    root = _load_part(docx_path, "word/styles.xml")
    if root is None:
        return {}, {}
    names, own, based = {}, {}, {}
    for s in root.iter(f"{{{_W_NS}}}style"):
        if s.get(f"{{{_W_NS}}}type") != "paragraph":
            continue
        sid = s.get(f"{{{_W_NS}}}styleId", "")
        name = s.find(f"{{{_W_NS}}}name")
        raw = name.get(f"{{{_W_NS}}}val", "") if name is not None else ""
        if raw:
            names[sid] = BabelFish.internal2ui(raw)
        lvl = s.find(f"{{{_W_NS}}}pPr/{{{_W_NS}}}outlineLvl")
        if lvl is not None and (lvl.get(f"{{{_W_NS}}}val") or "").isdigit():
            own[sid] = int(lvl.get(f"{{{_W_NS}}}val"))
        else:
            m = re.match(r'^heading\s*(\d)$', raw, re.IGNORECASE)
            if m:
                own[sid] = int(m.group(1)) - 1
        base = s.find(f"{{{_W_NS}}}basedOn")
        if base is not None:
            based[sid] = base.get(f"{{{_W_NS}}}val")
    outline = {}
    for sid in names.keys() | own.keys():
        cur, seen = sid, set()
        while cur is not None and cur not in own and cur not in seen:
            seen.add(cur)
            cur = based.get(cur)
        if cur in own and own[cur] < 9:
            outline[sid] = own[cur]
    return names, outline


def _chunk_boxed(p) -> str:
    """청크로 가는 문단 하나의 글 — 문단 글과 그 문단에 연결된 부동 텍스트 상자의 글을 `docx_text.chunk_text` 로 읽는다."""
    return docx_text.boxed_text(p, read=docx_text.chunk_text)


def _table_lines(tbl) -> list[str]:
    """표 하나를 `칸1 | 칸2 …` 줄 목록으로. 칸 안의 줄바꿈 · 탭은 공백으로 편다.

    칸 글은 칸 안 문단에 연결된 부동 텍스트 상자의 글까지 `_chunk_boxed` 로 읽는다.
    """
    lines = []
    for row in docx_text.table_rows(tbl, para=_chunk_boxed):
        cells = [c.replace("\n", " ").replace("\t", " ") for c in row if c]
        if cells:
            lines.append(" | ".join(cells))
    return lines


_W_OBJECT = f"{{{_W_NS}}}object"
_M_OMATH = f"{{{docx_text.M_NS}}}oMath"


def _has_equation(elem) -> bool:
    """`elem` 아래에 OMML 수식이나 읽은 글이 달린 수식 개체가 있는가."""
    return (next(elem.iter(_M_OMATH), None) is not None
            or any(o.get(docx_text.EQUATION_TEXT) for o in elem.iter(_W_OBJECT)))


def _shown_equations(p) -> list:
    """문단이 보여 주는 수식을 읽는 차례로 `(수식, 그 수식을 담은 문단, 종류)` 목록으로.

    종류는 OMML 수식(`m:oMath`)이면 "omml", 문서를 열 때 읽은 글(`docx_text.EQUATION_TEXT`)이 달린 수식 개체
    (`w:object`)면 "ole" 이다. OMML 수식은 `docx_text.paragraph_equations` 와 같은 수식을 같은 차례로 센다. 수식
    개체는 청크 본문(`docx_text.chunk_text` 와 글상자 글 `box_text(read=chunk_text)`)이 그 글을 넣는 자리만 센다 —
    지운 변경 표시 안 개체 · `mc:AlternateContent` 안 개체 · 도형 묶음 · 그리기 캔버스 안 개체는 빼고, 따로 놓인
    글상자 안 문단의 개체는 넣는다. 글상자 안 수식의 짝은 그 수식을 담은 글상자 안 문단이다.
    python-docx `Paragraph` 도 받는다.
    """
    p = getattr(p, "_p", p)
    found: list = []
    if not _has_equation(p):
        return found

    def math(eq) -> str:
        found.append((eq, p, "omml"))
        return ""

    def take(q) -> str:
        found.extend(_shown_equations(q))
        return ""

    def drawn(d) -> str:
        if d.tag == _W_OBJECT and d.get(docx_text.EQUATION_TEXT):
            found.append((d, p, "ole"))
        docx_text._box_lines(d, take)
        return ""

    docx_text.paragraph_text(p, deleted=docx_text.DROP, math=math, drawn=drawn)
    return found


def _table_shown_equations(tbl) -> list:
    """표 칸이 보여 주는 수식을 칸 글을 읽는 차례(`docx_text.table_rows`)대로 `(수식, 그 수식을 담은 문단, 종류)`
    목록으로 — 칸 안 문단마다 `_shown_equations` 로 센다. 세로로 합친 칸의 이어지는 칸은 세지 않는다.
    python-docx `Table` 도 받는다.
    """
    tbl = getattr(tbl, "_tbl", tbl)
    found: list = []
    if not _has_equation(tbl):
        return found

    def take(q) -> str:
        found.extend(_shown_equations(q))
        return ""

    docx_text.table_rows(tbl, para=take)
    return found


def equation_sites(paragraphs, tables) -> list[tuple]:
    """문서가 보여 주는 수식을 `(수식, 그 수식을 담은 문단, 본문 문단 번호, 종류)` 목록으로 — 본문 문단 차례로, 다음
    최상위 표 차례로, 한 문단 안에서는 읽는 차례로. 표 안 수식의 문단 번호는 -1 이다. 종류는 OMML 수식이면
    "omml", 수식 개체(`w:object`, ProgID `Equation.`)면 "ole" 이다.

    OMML 수식은 문단 · 표 칸 글을 읽는 규칙(`docx_text.paragraph_equations` · `table_equations`)이 읽는 수식만
    센다 — 지운 변경 표시 안 수식 · 글자와 짜임이 모두 지워진 수식 · 아무것도 그리지 않는 빈 수식 ·
    `mc:AlternateContent` 의 대체본 · 도형 묶음 · 그리기 캔버스 안 라벨 · 세로로 합친 칸의 이어지는 칸은 빼고, 따로
    놓인 글상자 안 수식은 넣는다. 수식 개체는 읽은 글이 달려 청크 본문에 그 글이 들어가는 것만 센다
    (`_shown_equations`). 읽은 글이 없는 수식 개체(그림만 있거나 판독하지 못한 것)는 세지 않는다.
    파서(03)의 equations.json 과 수식 보강(05)은 이 목록을 `TdocParser.document_equation_sites` 로 함께 쓴다.
    python-docx `Paragraph` · `Table` 도 받는다.
    """
    sites = [(eq, owner, i, kind) for i, p in enumerate(paragraphs) for eq, owner, kind in _shown_equations(p)]
    sites += [(eq, owner, -1, kind) for t in tables for eq, owner, kind in _table_shown_equations(t)]
    return sites


def _equation_text(eq, kind: str) -> str:
    """청크 본문이 수식 자리에 넣는 선형 글 — OMML 은 `docx_text.math_linear`, 수식 개체는 단 글 그대로."""
    return docx_text.math_linear(eq) if kind == "omml" else eq.get(docx_text.EQUATION_TEXT)


def _equation_infos(tdoc_number: str, sites) -> list["EquationInfo"]:
    """`equation_sites` 의 수식마다 `EquationInfo` 하나 — 주변 글은 그 수식을 담은 문단의 확정 글 앞 200자."""
    return [EquationInfo(equationId=f"EQ-{tdoc_number}-{i:03d}", index=i,
                         latex="",  # 설계 결정: 05_enhance_equations.py에서 후처리
                         context=docx_text.final_text(owner)[:200],
                         source=kind, text=_equation_text(eq, kind))
            for i, (eq, owner, _at, kind) in enumerate(sites, 1)]


def _table_texts(tables) -> list[str]:
    """표마다 `칸1 | 칸2 …` 줄을 이은 글 (빈 표는 뺀다).

    초안 CR 은 변경 본문을 표 칸 안에 담는 일이 많다. 칸 글은 docx_text 규칙으로 읽는다 —
    `_Cell.text` 는 변경 표시로 들어간 글 · 칸 안 표 · 블록 `w:sdt` 안 문단을 읽지 않는다.
    """
    results = []
    for tbl in tables:
        lines = _table_lines(tbl)
        if lines:
            results.append("\n".join(lines))
    return results


def _table_items(tables, start: int = 0, stop: int | None = None) -> list[tuple[int, str]]:
    """`tables[start:stop]` 의 (최상위 표 번호, 글) — 글은 `_table_texts` 와 같고 빈 표는 뺀다."""
    items = []
    for j in range(start, len(tables) if stop is None else stop):
        lines = _table_lines(tables[j])
        if lines:
            items.append((j, "\n".join(lines)))
    return items


def _table_spots(before: list[int], items) -> list[tuple[int, str]]:
    """표마다 (그 표 바로 뒤 본문 문단 번호, 글) — 표 번호 차례인 `items` 를 문단 사이 자리에 놓는다.

    `before[i]` 는 문단 i 앞의 최상위 표 수라서 표 j 바로 뒤 문단은 `before[i] > j` 인 첫 i 다. 표 뒤에 문단이
    없으면 문단 수를 쓴다. 자리가 i 인 표는 문단 i 앞에 싣는다.
    """
    spots, i = [], 0
    for j, text in items:
        while i < len(before) and before[i] <= j:
            i += 1
        spots.append((i, text))
    return spots


def _interleave(indices, lines_at, spots) -> list[str]:
    """`indices` 차례의 문단 글(`lines_at(i)` 가 내는 글 목록)과 `_table_spots` 의 표 글을 문서 차례로 잇는다.

    자리가 i 인 표는 문단 i 앞에, 마지막 문단보다 뒤 자리의 표는 끝에 놓는다.
    """
    parts, k = [], 0
    for i in indices:
        while k < len(spots) and spots[k][0] <= i:
            parts.append(spots[k][1])
            k += 1
        parts.extend(lines_at(i))
    parts.extend(text for _, text in spots[k:])
    return parts


def _fast_load_all_text(docx_path) -> str:
    """본문의 모든 문단 — 표 칸 · 글상자 안 문단까지 — 을 문서 순서로 잇는다.

    `_fast_load_blocks` 와 달리 문단이 어느 자리에 있는지 묻지 않는다. 산출이 빈 문서를
    되찾는 마지막 수단이므로 읽히지 않는 자리를 남기지 않는 쪽을 택한다. 글상자 안 문단은
    대체본(`mc:Fallback`)을 건너뛰어 한 번만 읽는다.
    """
    body = _load_body(docx_path)
    if body is None:
        return ""
    parts = [docx_text.chunk_text(p) for p in docx_text.iter_all_paragraphs(body)]
    return "\n".join(t for t in parts if t)


def _fast_load_blocks(docx_path) -> tuple[list[tuple[str, str]], list[int], list, dict[int, str], list]:
    """본문을 한 번 읽어 문단 (text, styleId) · 문단마다 앞선 최상위 표 수 · 최상위 표 요소 · 문단에 연결된
    부동 텍스트 상자의 글(문단 번호 → `docx_text.box_text`) · 문단 요소(수식을 셀 때 `equation_sites` 에 넘긴다)를
    함께 낸다.

    문단은 블록 `w:sdt` 안 것을 포함하고 표 안 것은 뺀다. python-docx 를 거치지 않는다.

    초대형 문서는 본문 XML 을 읽는 데만 수십 초가 걸리므로, 문단과 표 자리를 따로 읽지 않는다.
    """
    body = _load_body(docx_path)
    if body is None:
        return [], [], [], {}, []
    paragraphs, before, tables, boxes, elems = [], [], [], {}, []
    for b in docx_text.iter_blocks(body):
        if b.tag == _W_P:
            box = docx_text.box_text(b, read=docx_text.chunk_text)
            if box:
                boxes[len(paragraphs)] = box
            paragraphs.append((docx_text.final_text(b), _fast_get_style(b)))
            before.append(len(tables))
            elems.append(b)
        else:
            tables.append(b)
    return paragraphs, before, tables, boxes, elems


def _sections_from(texts: list[str], styles: list[str], outlines: list, marks: dict[int, str],
                   indices, end_idx: int, untitled: str = "Full Document",
                   boxes: dict[int, str] | None = None,
                   bodies: list[str] | None = None,
                   tables: list[tuple[int, str]] | None = None) -> list["Section"]:
    """문단 목록을 절로 나눈다 (Spec §3.1) — python-docx 경로와 fast path 가 같은 규칙을 쓴다.

    `texts` 는 제목 · 영역 판정에 쓰는 문단 글이고, `bodies` 는 절 내용에 싣는 문단 글이다(없으면 `texts`).

    `indices` 의 문단만 본다. 제외 영역(표지 · 목차 제목 · 참고문헌, `_region_marks`)과 목차 스타일
    문단은 싣지 않고, 참고문헌 영역에 들어서면 그 앞 절을 닫는다 — 영역 뒤의 절(Annex 등)은 다음
    제목에서 새로 시작하므로 읽힌다. 영역 뒤에 제목 없이 이어지는 글(붙인 Text Proposal · 변경 본문)은 그
    첫 줄을 제목으로 하는 1수준 절이 된다. 첫 제목 앞의 글은 버리지 않고 'Preamble' 절로 싣는다.
    제목도 참고문헌 영역 뒤 글도 없으면 그 글 전체가 `untitled` 절 하나가 된다.

    `boxes` 는 문단 번호마다 그 문단에 연결된 부동 텍스트 상자의 글이다. 제목 · 영역 판정은 문단 글만 보고,
    글상자 글은 그 문단 다음 줄로 싣는다 — 제목 문단에 연결된 부동 텍스트 상자도 제목이 아니라 그 절의 내용이다.
    제외 영역 문단의 글상자는 싣지 않는다.

    제목 문단의 글은 그 절 내용의 첫 줄로도 싣는다 — 임베딩은 내용만 읽으므로 제목으로 읽힌 글이 내용에
    없으면 검색에서 사라지고, 작은 청크를 앞 청크에 합치면 뒤 청크의 제목은 메타데이터에서도 사라진다.

    `tables` 는 `_table_spots` 의 (자리, 표 글) 목록이다. 표 글은 자리 문단 바로 앞에서 그때 열린 절에 싣는다 —
    첫 제목 앞이면 'Preamble' 에, 참고문헌 영역 뒤 제목 없는 자리면 'Tables' 절에 든다. 제외 영역 사이의
    표도 싣는다 — 제외는 문단 글의 규칙이다.
    주의: 표 글을 모든 문단 뒤 'Tables' 절에 모으면 표가 제 절의 제목 · 캡션 · 앞 문단과 다른 청크에 들어간다.
    Agreement · Proposal 박스(1x1 표)는 그 결론을 낸 절과 떨어지고, 결과 표는 그 표를 설명하는 글과 떨어진다.
    """
    sections: list[Section] = []
    lead: list[str] = []
    lead_span = [None, None]
    current, buf = None, []
    after_refs = False
    heading_at = _headings(texts, styles, outlines)
    spots, k = tables or [], 0
    orphan = None

    def place(at, text):
        nonlocal orphan
        if current is not None:
            buf.append(text)
        elif after_refs:
            if orphan is None or sections[-1] is not orphan:
                orphan = Section(title="Tables", level=1, content="", start_idx=at, end_idx=at)
                sections.append(orphan)
            orphan.content = f"{orphan.content}\n{text}" if orphan.content else text
            orphan.end_idx = at
        else:
            lead.append(text)
            lead_span[0] = at if lead_span[0] is None else lead_span[0]
            lead_span[1] = at if lead_span[1] is None else max(lead_span[1], at)

    for i in indices:
        while k < len(spots) and spots[k][0] <= i:
            place(*spots[k])
            k += 1
        text = texts[i]
        body = bodies[i] if bodies is not None else text
        region = marks.get(i, "")
        if region == "references":
            after_refs = True
            if current is not None:
                current.content = "\n".join(buf)
                current.end_idx = i
                sections.append(current)
                current, buf = None, []
        if region:
            continue
        heading = heading_at[i]
        lines = [(body, text)]  # (싣는 글, 참고문헌 영역 뒤 새 절의 제목)
        if heading is not None:
            if current is not None:
                current.content = "\n".join(buf)
                current.end_idx = i
                sections.append(current)
            current = Section(title=heading[0], level=heading[1], content="", start_idx=i, end_idx=i)
            buf = [body]
            lines = []
        box = boxes.get(i, "") if boxes else ""
        if box:
            lines.append((box, box.split("\n", 1)[0]))
        for line, title in lines:
            if not line:
                continue
            if current is not None:
                buf.append(line)
            elif after_refs:
                current = Section(title=title, level=1, content="", start_idx=i, end_idx=i)
                buf = [line]
            elif not sections:
                lead.append(line)
                lead_span[0] = i if lead_span[0] is None else lead_span[0]
                lead_span[1] = i + 1
    for at, text in spots[k:]:
        place(at, text)
    if current is not None:
        current.content = "\n".join(buf)
        current.end_idx = end_idx
        sections.append(current)
    if not sections:
        start = lead_span[0] if lead_span[0] is not None else 0
        return [Section(title=untitled, level=1, content="\n".join(lead), start_idx=start, end_idx=end_idx)]
    if lead:
        sections.insert(0, Section(title="Preamble", level=1, content="\n".join(lead),
                                   start_idx=lead_span[0], end_idx=lead_span[1]))
    return sections


def _cr_sections(texts: list[str], styles: list[str], outlines: list, before: list[int],
                 marks: dict[int, str], form: range, tables, head: int,
                 boxes: dict[int, str] | None = None,
                 bodies: list[str] | None = None) -> list["Section"]:
    """CR 의 절 (Spec §2.4.1 · §3.1) — python-docx 경로와 fast path 가 같은 규칙을 쓴다.

    `texts` 는 제목 · 영역 판정에 쓰는 문단 글이고, `bodies` 는 절 내용에 싣는 문단 글이다(없으면 `texts`).

    `before[i]` 는 문단 i 앞의 최상위 표 수, `head` 는 맨 앞 머리 표 수다. 양식 표에서는 기술 설명
    칸(`_cr_form_fields`)만 'CR-Form' 절로 Text Proposal 앞에 싣고, 양식 표 사이의 문단은
    양식의 일부라 싣지 않는다. 양식 뒤의 문단(목차 · 빈 문단 빼고)과 양식 뒤 표의 글을 문서 차례대로
    이은 것이 Text Proposal 이다. 양식 뒤 본문은 규격 절을 옮겨 적은 변경 글이라, 규격의 'References' 절도 변경 대상으로
    싣는다. 양식 앞의 글(토론 본문 뒤에 CR 을 붙인 문서)은 표지 줄 · 참고문헌을 뺀 나머지가 있을
    때만 제목대로 나눠 앞에 싣고 양식 앞 표(머리 표 빼고)는 그 자리의 절에 넣는다. 그런 글이 없으면 양식
    앞 표만 'Tables' 절 하나로 싣는다.

    Text Proposal 이 통째로 비면 양식 표를 다시 읽는다. 초안 CR 은 양식과 변경 본문을 한 표
    안에 함께 담기도 해서, 그때 양식을 빼면 본문이 통째로 사라진다 — 배제가 산출을 통째로
    비우면 그것은 배제가 아니라 소실이다. 이때는 기술 설명 칸도 그 안에 있어 'CR-Form' 절을 두지 않는다.
    """
    boxes = boxes or {}
    bodies = texts if bodies is None else bodies

    def body(i, kept=("",)):
        return (bodies[i] or i in boxes) and marks.get(i, "") in kept

    n = len(texts)
    pre = [i for i in range(n) if before[i] <= form.start]
    post = [i for i in range(n) if before[i] >= form.stop]
    sections = []
    pre_spots = _table_spots(before, _table_items(tables, head, form.start))
    if any(body(i) for i in pre):
        sections = _sections_from(texts, styles, outlines, marks, pre, pre[-1] + 1, untitled="Preamble",
                                  boxes=boxes, bodies=bodies, tables=pre_spots)
    elif pre_spots:
        at = pre[-1] + 1 if pre else 0
        sections.append(Section(title="Tables", level=1, content="\n\n".join(t for _, t in pre_spots),
                                start_idx=at, end_idx=at))

    def lines_at(i):
        return [t for t in (bodies[i], boxes.get(i, "")) if t] if body(i, ("", "references", "references_unchanged")) else []

    text_parts = _interleave(post, lines_at, _table_spots(before, _table_items(tables, form.stop)))
    if not text_parts:
        text_parts = ["\n\n".join(_table_texts(tables[form.start:form.stop]))]
    else:
        fields = _cr_form_fields(tables[form.start:form.stop])
        if fields:
            at = pre[-1] + 1 if pre else 0
            sections.append(Section(title="CR-Form", level=1, content=fields, start_idx=at, end_idx=at))
    sections.append(Section(title="Text Proposal", level=1, content="\n".join(text_parts),
                            start_idx=post[0] if post else n, end_idx=n))
    return sections


class TdocParser:
    """Tdoc 파서 메인 클래스"""

    # 제외 영역 패턴 (Spec §1.3)
    EXCLUDE_PATTERNS = {
        'toc': [
            r'^Contents$',
            r'^Table of Contents$',
            r'^목차$',
        ],
        'references': [
            r'^References$',
            r'^\d+\.?\s*References$',
            r'^참고문헌$',
        ],
    }

    # CR-Form 감지 키워드 (Spec §2.4.1 — 표 1 첫 칸). 회의 머리줄('3GPP TSG-RAN WG4')은 CR 이 아닌
    # 문서의 첫 표에도 흔해서 키워드가 될 수 없다.
    CR_FORM_KEYWORDS = ['CR-Form', 'CHANGE REQUEST']

    # LS 머리글 칸 (Spec §2.3) — 3GPP LS 양식이 줄 머리에 다는 이름표 가운데 LS 에만 있는 것. 'Title:' ·
    # 'Source:' 는 LS 가 아닌 문서의 표지에도 있어 LS 를 가르지 못한다.
    LS_HEADER_FIELD = re.compile(
        r'^[ \t]*(to|cc|contact[ \t]+person|send[ \t]+any[ \t]+reply[ \t]+ls[ \t]+to|response[ \t]+to|attachments?)'
        r'[ \t]*:', re.IGNORECASE | re.MULTILINE)
    # LS 머리글 줄 — 위 칸에 LS 양식의 나머지 이름표를 더한 것. LS 양식은 이 줄에 Heading 스타일을 달기도
    # 한다('Name:' · 'E-mail Address:').
    LS_HEADER_LINE = re.compile(
        r'^[ \t]*(title|response[ \t]+to|release|work[ \t]+items?|source|to|cc|contact[ \t]+person|name|'
        r'e-?mail([ \t]+address)?|send[ \t]+any[ \t]+reply[ \t]+ls[ \t]+to|attachments?)[ \t]*:', re.IGNORECASE)

    def __init__(self, docx_path: Path, tdoc_number: str):
        self.docx_path = docx_path
        # 폴더 이름이 곧 tdoc 번호다. 다만 3GPP 아카이브 쪽 이름이 뒤에 공백을
        # 달고 오는 경우가 있어 그대로 쓰면 'R4-2405197 ' 같은
        # 값이 tdocNumber·chunkId·출력 폴더 이름에 그대로 박힌다. 그 값은 어떤
        # tdoc 번호와도 같지 않으므로 KG 와의 결합이 조용히 실패한다. 공백이 `%20` 으로
        # 인코딩된 채 풀린 이름도 같다. 03 의 이어 받기·04·05 가 같은 이름을 보도록 번호는
        # tdoc_number_of 한 규칙에서만 얻는다.
        # 문서가 TDoc 폴더의 하위 폴더에 있을 수 있으므로(`find_docx_file`) 번호는 문서 경로가
        # 아니라 부르는 쪽이 TDoc 폴더 이름에서 얻어 넘긴다.
        self.tdoc_number = tdoc_number
        self._xml_damaged = False
        self._para_cache: list[Paragraph] | None = None
        self._table_cache: list[Table] | None = None
        self._para_text_cache: list[str] | None = None
        self._para_chunk_cache: list[str] | None = None
        self._box_cache: dict[int, str] | None = None
        self._style_outline: dict[str, int] | None = None
        self._layout_cache = None
        self._before_cache: list[int] | None = None
        self._head_cache: int | None = None
        try:
            self.doc = docx_text.open_document(docx_path)
        except Exception:
            # 주의: ZIP 이 아닌 파일(0바이트 · 이름만 .docx 인 OLE 문서 · IRM 암호화 · 깨진 내려받기)은
            # lxml 로도 읽을 것이 없다. 손상 경로로 보내면 빈 'Full Document' 한 절이 나와 읽지 못한
            # 문서가 본문 없는 문서로 셈된다(RAN4 R4-1814144 · R4-2404168 등). 거절을 그대로 올린다.
            if not zipfile.is_zipfile(docx_path):
                raise
            # 주의: ZIP 이어도 본문 부품이 없거나 복구 모드로도 본문(`w:body`)을 얻지 못하면 같은 까닭으로 거절한다.
            # 손상 경로는 본문을 zipfile 로 다시 읽는데(`_load_body`), 읽을 본문이 없으면 빈 'Full Document' 한 절과
            # 수식 0개가 성공으로 남고, 수식 보강(05)은 03 이 쓴 수식 목록을 빈 목록으로 덮는다.
            if _load_body(docx_path) is None:
                raise
            # XML 손상 등으로 python-docx 로딩 실패 → fast path only 모드
            # lxml recover로 텍스트 추출은 가능 (LibreOffice 변환본의 XML 이 손상된 경우)
            self._xml_damaged = True
            self.doc = None
            return

    # 읽기 규칙 (Spec §1.3 · §3.6.3). 변경 표시는 최종본 기준 — 삽입(`w:ins`)은 읽고
    # 삭제(`w:del`)는 뺀다. 제목 · 영역 판정 글(`_paragraph_texts`)은 수식을 빼고, 절 내용 글
    # (`_paragraph_chunk_texts`)은 수식 자리에 선형 표기를 넣는다. python-docx 의
    # `Paragraph.text` · `_Cell.text` 는 삽입된 글 · `w:sdt` · `w:smartTag` · `w:fldSimple`
    # 안의 글 · 칸 안 표를 읽지 않고, `Document.paragraphs` · `Document.tables` 는 블록
    # `w:sdt` 안의 문단 · 표를 건너뛴다. 그래서 문단 · 표 목록과 글은 아래 세 자리에서만 얻는다.
    # 문단에 연결된 부동 텍스트 상자의 글은 문단 글과 따로 읽어(`_paragraph_boxes`) 절 내용 · 표 칸 글에만
    # 싣는다 — 제목 · 영역 판정은 문단 글만 본다.

    def _paragraphs(self) -> list[Paragraph]:
        """본문 문단 — 블록 `w:sdt` · `w:customXml` 안의 문단까지 문서 순서로(표 안 문단은 뺀다)."""
        if self._para_cache is None:
            self._para_cache = [Paragraph(b, self.doc._body)
                                for b in docx_text.iter_blocks(self.doc.element.body) if b.tag == _W_P]
        return self._para_cache

    def _outline_of(self, style_id: str, style_name: str) -> int | None:
        """문단 스타일이 선언한 개요 수준(0~8). 문서 제목 스타일 · 선언 없음은 None."""
        if style_name in _DOC_TITLE_STYLES:
            return None
        if self._style_outline is None:
            self._style_outline = _style_table(self.docx_path)[1]
        return self._style_outline.get(style_id)

    def _tables(self) -> list[Table]:
        """본문 최상위 표 — 블록 `w:sdt` · `w:customXml` 안의 표까지 문서 순서로."""
        if self._table_cache is None:
            self._table_cache = [Table(b, self.doc._body)
                                 for b in docx_text.iter_blocks(self.doc.element.body) if b.tag == _W_TBL]
        return self._table_cache

    def _is_header_footer(self, para: Paragraph) -> bool:
        """헤더/푸터 여부 확인 (Spec §1.3 제외 대상)"""
        # python-docx에서 헤더/푸터는 별도 섹션으로 분리됨
        # 본문 paragraphs에는 포함되지 않음
        return False

    def _layout(self):
        """문단의 스타일 이름 · 개요 수준 · 앞선 최상위 표 수 · 제외 영역 · 머리 표 수를 문서당 한 번 만든다."""
        if self._layout_cache is None:
            paras = self._paragraphs()
            texts = self._paragraph_texts()
            # 주의: python-docx `Paragraph.style` 은 부를 때마다 스타일 목록을 다시 훑는다 — 지정이 없거나
            # 없는 styleId 면 기본 스타일을 찾으려고 목록 전체를 돈다. 문단 수 × 스타일 수라 큰 문서에서
            # 이 두 줄이 파싱 시간을 다 먹는다. 결과는 문단의 styleId(`w:pStyle`, 없으면 None) 하나로
            # 정해지므로 styleId 마다 한 번만 묻는다.
            asked: dict = {}

            def style_of(p):
                sid = p._p.style
                if sid not in asked:
                    asked[sid] = p.style
                return asked[sid]

            found = [style_of(p) for p in paras]
            styles = [st.name if st is not None and st.name else "" for st in found]
            outlines = [self._outline_of(st.style_id if st is not None else "", s)
                        for st, s in zip(found, styles)]
            before = self._tables_before()
            head = len(self._cover_tables())
            marks = _region_marks(texts, styles, outlines, sum(1 for b in before if b <= head),
                                  self.EXCLUDE_PATTERNS, elems=[p._p for p in paras])
            self._layout_cache = (styles, outlines, before, marks, head)
        return self._layout_cache

    def _tables_before(self) -> list[int]:
        if self._before_cache is None:
            self._before_cache = _tables_before(self.doc.element.body)
        return self._before_cache

    def _cover_tables(self) -> range:
        """표지로 빼는 최상위 표 자리 — 맨 앞 회의 머리 표(`_cover_table_count`). 스타일을 읽지 않아
        초대형 문서에서도 싸다."""
        if self._head_cache is None:
            self._head_cache = _cover_table_count(self._tables(), self._paragraph_texts(),
                                                  self._tables_before(), self.CR_FORM_KEYWORDS)
        return range(self._head_cache)

    def _is_exclude_region(self, para_idx: int) -> tuple[bool, str]:
        """
        제외 영역 감지 (Spec §1.3) — 표지 · 목차(제목과 항목) · 참고문헌 영역. 빈 문단은 제외하지 않는다.
        Returns: (is_excluded, region_type)
        """
        region = self._layout()[3].get(para_idx, "")
        return bool(region), region

    def _fast_layout(self, paragraphs: list[tuple[str, str]], before: list[int], tables, elems: list | None = None):
        """fast path 문단의 글 · 스타일 이름 · 개요 수준 · 제외 영역 · 머리 표 수 — `_layout` 과 같은 규칙.

        스타일 이름은 python-docx `style.name` 과 같은 표기라 두 경로의 제목 판정이 같다.
        """
        style_names, style_outline = _style_table(self.docx_path)
        texts = [t for t, _ in paragraphs]
        styles = [style_names.get(sid, sid) for _, sid in paragraphs]
        outlines = [None if s in _DOC_TITLE_STYLES else style_outline.get(sid)
                    for (_, sid), s in zip(paragraphs, styles)]
        head = _cover_table_count(tables, texts, before, self.CR_FORM_KEYWORDS)
        marks = _region_marks(texts, styles, outlines, sum(1 for b in before if b <= head),
                              self.EXCLUDE_PATTERNS, elems=elems)
        return texts, styles, outlines, marks, head


# =============================================================================
# 1-2: 문서 유형 분류
# =============================================================================

    def classify_document_type(self) -> str:
        """
        문서 유형 분류 (Spec §2.3)
        Returns: discussion, CR, draftCR, LS_in, LS_out, report
        """
        # CR-Form 감지 (테이블 기반)
        if self._detect_cr_form():
            # Track Changes 여부로 CR vs draftCR 구분
            if self._has_track_changes():
                return "CR"
            return "draftCR"

        # LS 감지
        if self._detect_ls_structure():
            # 파일명으로 in/out 구분
            filename = self.docx_path.name.lower()
            if 'reply' in filename or 'draft' in filename:
                return "LS_out"
            return "LS_in"

        # Report 감지 (Final Minutes)
        if self._detect_report():
            return "report"

        # 기본값
        return "discussion"

    def _detect_cr_form(self) -> bool:
        """CR-Form 감지 (Spec §2.4.1)"""
        return self._cr_form_start() is not None

    def _cr_form_start(self) -> int | None:
        """CR 양식이 시작하는 최상위 표의 자리 — 첫 칸에 규격 키워드(`CR_FORM_KEYWORDS`)가 있는 표.

        규격의 양식은 표 1 에서 시작하지만, 토론 본문 뒤에 CR 을 붙인 문서는 앞에 본문 표가 있어
        양식이 둘째 · 셋째 표에서 시작한다. 그래서 처음 세 표를 본다.
        """
        for idx, table in enumerate(self._tables()[:3]):
            rows = docx_text.table_rows(table)
            if rows and rows[0] and any(kw in rows[0][0] for kw in self.CR_FORM_KEYWORDS):
                return idx
        return None

    def _cr_form_tables(self) -> range:
        """CR 양식(Spec §2.4.1 의 Cover Sheet · Proposed change affects · 메타데이터 표)이 차지하는 표 자리.

        양식은 시작 표 뒤로 양식 행 이름표(`_CR_FORM_ROW`)를 단 표가 이어지는 데까지다(셋까지).
        자리 셋을 무조건 빼면 양식이 표 하나 · 둘뿐인 CR 의 본문 표가 사라진다.
        """
        start = self._cr_form_start()
        if start is None:
            return range(0)
        return range(start, start + _cr_form_count(self._tables()[start:]))

    def _detect_ls_structure(self) -> bool:
        """LS 구조 감지 (Spec §2.3) — 글 있는 첫 20문단의 줄 머리에 서로 다른 LS 머리글 칸(`LS_HEADER_FIELD`)이
        둘 이상.

        LS 낱말('LS on' · 'Reply LS' 등)을 글 어디서나 부분 문자열로 세면 'Reply LS on …' 한 줄이 두 번 세이고,
        토론 · Text Proposal · 회의 보고 문서의 제목 · 장 목록 · 참고문헌 줄도 세인다. 그러면 제목 구조를 가진
        긴 문서가 LS 길로 가서 제목을 잃고 길이로만 잘린다(Heading 문단이 많은 문서가 그랬다). 3GPP LS 양식은
        To · Cc · Contact Person · Send any reply LS to · Response to · Attachments 가운데 여럿을 줄 머리에 단다.
        """
        text = "\n".join([t for t in self._paragraph_texts() if t][:20])
        fields = {re.sub(r'\s+', ' ', m.group(1).lower()).removesuffix('s')
                  for m in self.LS_HEADER_FIELD.finditer(text)}
        return len(fields) >= 2

    def _detect_report(self) -> bool:
        """Report (Final Minutes) 감지"""
        # 파일명 또는 제목에서 감지
        filename = self.docx_path.name.lower()
        if 'final' in filename and ('minute' in filename or 'report' in filename):
            return True

        # 문단 수로 추정 (3000 문단 초과)
        if len(self._paragraphs()) > 3000:
            # 추가 확인: Agenda Item 패턴
            text = "\n".join(t for t in self._paragraph_texts()[:50] if t)
            if 'Agenda Item' in text or 'AI ' in text:
                return True

        return False

    def _has_track_changes(self) -> bool:
        """Track Changes 존재 여부 확인"""
        body = self.doc._element.body
        insertions = body.findall('.//' + qn('w:ins'))
        deletions = body.findall('.//' + qn('w:del'))
        return bool(insertions or deletions)


# =============================================================================
# 1-3: 유형별 파서
# =============================================================================

    def parse(self) -> ParsedContent:
        """메인 파싱 함수 - 유형별 분기"""
        # XML 손상 문서: lxml recover fast path로 직접 섹션 추출
        if self._xml_damaged:
            content = self._parse_xml_damaged()
        else:
            doc_type = self.classify_document_type()

            if doc_type in ("CR", "draftCR"):
                content = self._parse_cr()
            elif doc_type in ("LS_in", "LS_out"):
                content = self._parse_ls(doc_type)
            elif doc_type == "report":
                content = self._parse_report()
            else:
                content = self._parse_discussion()

        content = self._recover_if_empty(content)
        return self._append_footnotes(content)

    def _append_footnotes(self, content: "ParsedContent") -> "ParsedContent":
        """각주 · 미주를 마지막 섹션으로 싣는다 (Spec §1.3 포함 대상). 유형과 상관없이 같다."""
        notes = _fast_load_notes(self.docx_path)
        if notes:
            content.sections.append(Section(
                title="Footnotes",
                level=1,
                content="\n".join(notes),
                start_idx=content.paragraph_count,
                end_idx=content.paragraph_count
            ))
        return content

    def _recover_if_empty(self, content: "ParsedContent") -> "ParsedContent":
        """산출이 통째로 비었을 때만 본문의 모든 문단을 읽어 되찾는다.

        유형별 경로는 본문 문단과 표를 읽는다. 글이 글상자 안에만 있는 문서는 두 자리
        어디에도 글이 없어 산출이 빈 채로 남고, 빈 산출은 본문이 없는 문서와 구별되지
        않는다. 되찾기는 글상자 안 문단까지 문서 순서로 잇는다.

        되찾기는 남은 글자가 하나도 없을 때만 돈다 — 이미 글자가 나온 문서의
        읽기 규칙은 그대로 두어 되찾기가 파싱 의미를 바꾸지 않게 한다.
        """
        if any(s.content.strip() for s in content.sections):
            return content
        recovered = _fast_load_all_text(self.docx_path)
        if not recovered:
            return content
        content.sections = [Section(
            title="Full Document",
            level=1,
            content=recovered,
            start_idx=0,
            end_idx=content.paragraph_count,
        )]
        return content

    def _parse_xml_damaged(self) -> ParsedContent:
        """XML 손상 문서 파싱 — lxml recover + fast path"""
        paragraphs, before, tables, boxes, elems = _fast_load_blocks(self.docx_path)
        para_count = len(paragraphs)
        content = ParsedContent(
            tdoc_number=self.tdoc_number,
            doc_type="discussion",  # 유형 판별 불가 → discussion 기본값
            paragraph_count=para_count
        )
        content.equations = _equation_infos(self.tdoc_number, equation_sites(elems, tables))

        if not paragraphs:
            content.sections.append(Section(
                title="Full Document", level=1, content="",
                start_idx=0, end_idx=0
            ))
            return content

        # 섹션 추출 (fast path 와 같은 규칙)
        texts, styles, outlines, marks, head = self._fast_layout(paragraphs, before, tables, elems)
        # 테이블 텍스트도 그 자리의 절에 싣는다 (Spec §2.4) — 머리 표는 표지라 뺀다
        content.sections = _sections_from(texts, styles, outlines, marks, range(para_count), para_count,
                                          boxes=boxes, bodies=[docx_text.chunk_text(e) for e in elems],
                                          tables=_table_spots(before, _table_items(tables, head)))
        content.tables = []
        content.figures = []
        return content

    def _parse_cr(self) -> ParsedContent:
        """
        CR/draftCR 파싱 (Spec §2.4.1 · §3.1)
        - CR 양식 표(`_cr_form_tables`)는 기술 설명 칸만 'CR-Form' 절로 싣고 나머지 칸 · 양식 표 사이 문단 · 표지 줄은 뺀다
        - 양식 뒤의 문단과 양식이 아닌 표가 Text Proposal 이다
        - 양식 앞의 글(토론 본문 뒤에 CR 을 붙인 문서)은 제목대로 나눠 앞에 싣는다
        - >10K 문단: fast path (zipfile+ET)로 전환
        """
        para_count = len(self._paragraphs())
        content = ParsedContent(
            tdoc_number=self.tdoc_number,
            doc_type="CR" if self._has_track_changes() else "draftCR",
            paragraph_count=para_count
        )
        form = self._cr_form_tables()

        # >10K 문단: fast path — zipfile+ET로 텍스트 추출
        if para_count > _FAST_PATH_THRESHOLD:
            return self._parse_cr_fast(content, form)

        styles, outlines, before, marks, head = self._layout()
        content.sections = _cr_sections(self._paragraph_texts(), styles, outlines, before, marks,
                                        form, self._tables(), head, boxes=self._paragraph_boxes(),
                                        bodies=self._paragraph_chunk_texts())

        # 수식, 테이블 추출 (머리 표 · 양식 표 제외)
        content.equations = self._extract_equations()
        content.tables = self._extract_tables(skip=set(form) | set(range(head)))
        content.figures = self._extract_figures()

        return content

    def _parse_cr_fast(self, content: ParsedContent, form: range) -> ParsedContent:
        """
        CR/draftCR fast path (>10K 문단용) — `_parse_cr` 와 같은 규칙.
        절 글은 zipfile+ET 로 읽는다 — python-docx 문단 순회 병목 회피. 표 · 그림 목록은 python-docx 로 읽는다.
        """
        paragraphs, before, tables, boxes, elems = _fast_load_blocks(self.docx_path)
        if not paragraphs:
            return content
        texts, styles, outlines, marks, head = self._fast_layout(paragraphs, before, tables, elems)
        content.sections = _cr_sections(texts, styles, outlines, before, marks, form, tables, head,
                                        boxes=boxes, bodies=[docx_text.chunk_text(e) for e in elems])

        # 수식은 위에서 읽은 본문 요소에서 `_extract_equations` 와 같은 규칙(`equation_sites`)으로 센다.
        # 표 · 그림 목록은 `_parse_cr` 와 같이 python-docx 로 만든다(머리 표 · 양식 표 제외).
        # 주의: 표 · 그림 목록을 비우면 이 문서들의 표 번호 · 캡션 · HTML 과 그림 항목만 빠지고, 표 글은
        #   절 내용에 남아 빠진 것이 드러나지 않는다. 문단 순회만 느리고 표 · 그림 읽기는 오래 걸리지 않는다.
        content.equations = _equation_infos(self.tdoc_number, equation_sites(elems, tables))
        content.tables = self._extract_tables(skip=set(form) | set(self._cover_tables()))
        content.figures = self._extract_figures()

        return content

    def _parse_ls(self, doc_type: str) -> ParsedContent:
        """
        LS 파싱 (Spec §3.1) — 표지 · 머리글(Title · Source · To · Cc · Contact Person 등)까지 싣고 목차 ·
        참고문헌 영역만 뺀다. 표 글은 그 표가 놓인 자리에 싣는다(Spec §2.4: 테이블 본문 · Agreement 박스 포함).
        - 글 전체가 한 청크(`ChunkEngine.MAX_TOKENS`)에 들면 'Full Document' 절 하나로 싣는다.
        - 넘으면 청크 엔진이 어차피 자르므로 제목대로 나눈다(`_sections_from`, 표지도 싣는다). 표 글은
          그 자리의 절에 든다. LS 머리글 줄(`LS_HEADER_LINE`)은 Heading 스타일을 달았어도 제목으로 보지 않는다
          — 머리글은 첫 제목 앞 'Preamble' 에 든다. 제목이 하나도 없으면 'Full Document' 절 하나다.
        """
        paras = self._paragraphs()
        texts = self._paragraph_texts()
        bodies = self._paragraph_chunk_texts()
        n = len(paras)
        content = ParsedContent(tdoc_number=self.tdoc_number, doc_type=doc_type, paragraph_count=n)
        styles, outlines, _before, marks, _head = self._layout()
        kept = {i: r for i, r in marks.items() if r != "cover"}
        boxes = self._paragraph_boxes()

        def lines_at(i):
            return [] if i in kept else [t for t in (bodies[i], boxes.get(i, "")) if t]

        spots = self._placed_tables()
        whole = _interleave(range(n), lines_at, spots)

        sections = None
        if ChunkEngine().count_tokens("\n".join(whole)) > ChunkEngine.MAX_TOKENS:
            plain, flat = list(styles), list(outlines)
            for i in range(n):
                if texts[i] and self.LS_HEADER_LINE.match(texts[i]):
                    plain[i], flat[i] = "", None
            found = _sections_from(texts, plain, flat, kept, range(n), n, boxes=boxes, bodies=bodies,
                                   tables=spots)
            if len(found) > 1 or found[0].title != "Full Document":
                sections = found
        if sections is None:
            sections = [Section(title="Full Document", level=1, content="\n".join(whole), start_idx=0, end_idx=n)]
        content.sections = sections
        content.equations = self._extract_equations()
        content.tables = self._extract_tables(skip=self._cover_tables())
        content.figures = self._extract_figures()
        return content

    def _parse_report(self) -> ParsedContent:
        """
        Report 파싱 (Spec §3.1)
        - 섹션 단위로 분할
        - Agenda Item 기준
        """
        content = ParsedContent(
            tdoc_number=self.tdoc_number,
            doc_type="report",
            paragraph_count=len(self._paragraphs())
        )

        # 섹션 추출
        # 테이블 텍스트도 그 자리의 절에 싣는다 (Spec §2.4) — 머리 표는 표지라 뺀다
        content.sections = self._extract_sections(tables=True)
        content.equations = self._extract_equations()
        content.tables = self._extract_tables(skip=self._cover_tables())
        content.figures = self._extract_figures()

        return content

    def _parse_discussion(self) -> ParsedContent:
        """
        Discussion 파싱 (Spec §3.1)
        - 섹션 단위 분할
        - 문서 길이에 따른 전략 적용
        - 테이블 텍스트도 그 자리에 싣는다 (Spec §2.4) — 머리 표는 표지라 뺀다
        """
        content = ParsedContent(
            tdoc_number=self.tdoc_number,
            doc_type="discussion",
            paragraph_count=len(self._paragraphs())
        )

        para_count = len(self._paragraphs())

        # 짧은 문서 (<30 문단): 전체를 1청크 (Spec §3.1)
        if para_count < 30:
            bodies, boxes = self._paragraph_chunk_texts(), self._paragraph_boxes()

            def lines_at(i):
                return [] if self._is_exclude_region(i)[0] else [t for t in (bodies[i], boxes.get(i, "")) if t]

            text_parts = _interleave(range(para_count), lines_at, self._placed_tables(skip=self._cover_tables()))

            content.sections.append(Section(
                title="Full Document",
                level=1,
                content="\n".join(text_parts),
                start_idx=0,
                end_idx=para_count
            ))
        else:
            # 일반/긴/초대형 문서: 섹션 단위
            content.sections = self._extract_sections(tables=True)

        content.equations = self._extract_equations()
        content.tables = self._extract_tables(skip=self._cover_tables())
        content.figures = self._extract_figures()

        return content

    def _placed_tables(self, skip=()) -> list[tuple[int, str]]:
        """
        테이블 텍스트와 그 자리(`_table_spots`, Vector DB 청크용) — 자리가 `skip` 에 든 표는 뺀다
        테이블 내용을 검색 가능한 텍스트로 변환

        Agreement · Proposal 박스(1x1 표, §2.6.1)도 같이 싣는다 — Spec §2.4 는 이 박스를
        "텍스트 추출 (검색 중요도 높음)" 으로 정했고, 박스 글은 본문 문단 목록에 들어오지 않는다.

        주의: 표 글 앞에 'Table N:' 같은 번호를 붙이지 않는다. 그 번호는 표지 표까지 센 문서 안 표 차례라서
        문서가 캡션에 쓴 표 번호와 어긋나고, 캡션 번호로 읽히면 다른 표의 설명과 이어 붙는다. 표 글은 제
        캡션 문단 옆 자리에 놓이므로 캡션이 그 표를 가리킨다.
        """
        items = [(j, t) for j, t in _table_items(self._tables()) if j not in skip]
        return _table_spots(self._tables_before(), items)


# =============================================================================
# 1-4: 섹션 추출기
# =============================================================================

    def _extract_sections(self, tables: bool = False) -> list[Section]:
        """
        섹션 추출 (Spec §3.1) — 규칙은 `_sections_from` 한 벌
        - >10K 문단: fast path (zipfile+ET)
        - `tables` 면 머리 표를 뺀 최상위 표의 글을 그 자리의 절에 싣는다(`_sections_from`)
        """
        # Fast path for huge documents
        if len(self._paragraphs()) > _FAST_PATH_THRESHOLD:
            return self._extract_sections_fast(tables)

        styles, outlines, _before, marks, _head = self._layout()
        n = len(self._paragraphs())
        spots = self._placed_tables(skip=self._cover_tables()) if tables else None
        return _sections_from(self._paragraph_texts(), styles, outlines, marks, range(n), n,
                              boxes=self._paragraph_boxes(), bodies=self._paragraph_chunk_texts(), tables=spots)

    def _extract_sections_fast(self, with_tables: bool = False) -> list[Section]:
        """
        섹션 추출 fast path (>10K 문단용) — zipfile+ET로 텍스트+스타일 한 번에 읽고 같은 규칙으로 나눈다.

        Running CR 은 3GPP Spec 전체를 담으므로 참고문헌 영역만 건너뛰고 그 뒤의 절은 읽는다.
        """
        paragraphs, before, tables, boxes, elems = _fast_load_blocks(self.docx_path)
        if not paragraphs:
            return [Section(title="Full Document", level=1, content="", start_idx=0, end_idx=0)]
        texts, styles, outlines, marks, head = self._fast_layout(paragraphs, before, tables, elems)
        spots = _table_spots(before, _table_items(tables, head)) if with_tables else None
        return _sections_from(texts, styles, outlines, marks, range(len(paragraphs)), len(paragraphs),
                              boxes=boxes, bodies=[docx_text.chunk_text(e) for e in elems], tables=spots)


# =============================================================================
# 1-5: 콘텐츠 추출
# =============================================================================

    def document_equation_sites(self) -> list[tuple]:
        """이 문서의 `equation_sites` — 수식 보강(05)이 03 의 equations.json 과 같은 목록을 얻는 자리.

        XML 손상 문서(`_xml_damaged`)는 `_parse_xml_damaged` 와 같이 zipfile 로 읽은 본문 요소에서, 나머지는
        `_extract_equations` 와 같이 python-docx 문단 · 표에서 센다. 문단 1만 개를 넘는 CR 은 03 이 zipfile 로 읽은
        본문 요소에서 세지만(`_parse_cr_fast`) 같은 본문 XML 의 같은 블록 차례이므로 목록이 같다.
        """
        if self._xml_damaged:
            body = _load_body(self.docx_path)
            blocks = [] if body is None else list(docx_text.iter_blocks(body))
            return equation_sites([b for b in blocks if b.tag == _W_P], [b for b in blocks if b.tag != _W_P])
        return equation_sites(self._paragraphs(), self._tables())

    def paragraph_total(self) -> int:
        """본문 문단 수 — 파싱 산출의 paragraph_count 와 같다(모든 경로가 블록 차례의 `w:p` 수를 센다).

        수식 보강(05)이 묶음 문서의 문단 번호를 이을 때 쓴다(`bundle_equation_sites`).
        """
        if self._xml_damaged:
            body = _load_body(self.docx_path)
            return 0 if body is None else sum(1 for b in docx_text.iter_blocks(body) if b.tag == _W_P)
        return len(self._paragraphs())

    def _extract_equations(self) -> list[EquationInfo]:
        """
        수식 추출 (Spec §2.4) — 본문 문단 · 최상위 표의 수식(OMML · 수식 개체)마다 하나(`equation_sites`)
        - 주변 텍스트(context): 그 수식을 담은 문단의 글
        - LaTeX 변환 (05_enhance_equations.py에서 후처리)
        """
        return _equation_infos(self.tdoc_number, equation_sites(self._paragraphs(), self._tables()))

    def _extract_tables(self, skip=()) -> list[TableInfo]:
        """
        테이블 추출 (Spec §2.4, §2.6.1)
        - HTML 변환
        - 텍스트 추출
        - Agreement 박스 감지 (1x1 Table Grid)
        """
        tables = []
        styles, _outlines, before, _marks, _head = self._layout()
        captions = docx_figures.table_captions(self._paragraph_texts(), styles, before, len(self._tables()))

        for i, table in enumerate(self._tables()):
            if i in skip:
                continue

            table_id = f"TBL-{self.tdoc_number}-{i+1:03d}"

            # Agreement 박스 감지 (Spec §2.6.1)
            is_agreement = self._is_agreement_box(table)

            rows = docx_text.table_rows(table, para=docx_text.boxed_text)

            # 텍스트 추출
            text_parts = []
            for row in rows:
                row_text = [c for c in row if c]
                if row_text:
                    text_parts.append(" | ".join(row_text))

            # HTML 변환
            html = self._table_to_html(rows)

            # 캡션 — 표 바로 위, 없으면 바로 아래 문단의 표 캡션. 번호는 캡션의 번호 그대로, 캡션이 없으면 빈 글.
            number, caption = captions[i]

            # 테이블 내 수식
            table_equations = [docx_text.final_text(owner)[:100] for _eq, owner, _kind in _table_shown_equations(table)]

            tables.append(TableInfo(
                table_id=table_id,
                table_number=f"Table {number}" if number else "",
                caption=caption,
                html=html,
                text="\n".join(text_parts),
                equations=table_equations,
                is_agreement_box=is_agreement
            ))

        return tables

    def _is_agreement_box(self, table: Table) -> bool:
        """Agreement 박스 감지 (Spec §2.6.1): 1x1 Table Grid"""
        rows = docx_text.table_rows(table, para=docx_text.boxed_text)
        if len(rows) == 1 and len(rows[0]) == 1:
            # 스타일 확인 (table.style.name이 None일 수 있음)
            style = table.style.name if table.style and table.style.name else ""
            if "Grid" in style or "Table Grid" in style:
                # 내용 확인: Proposal, Agreement, Observation 등
                text = rows[0][0].lower()
                keywords = ['proposal', 'agreement', 'observation', 'conclusion', 'working assumption']
                if any(kw in text for kw in keywords):
                    return True
        return False

    def _table_to_html(self, rows: list[list[str]]) -> str:
        """테이블(`docx_text.table_rows` 의 행 목록)을 HTML로 변환. 칸 글은 이스케이프한다."""
        html_parts = ['<table border="1">']

        for row in rows:
            html_parts.append('  <tr>')
            for cell in row:
                cell_text = html_escape(cell).replace('\n', '<br>')
                html_parts.append(f'    <td>{cell_text}</td>')
            html_parts.append('  </tr>')

        html_parts.append('</table>')
        return '\n'.join(html_parts)

    def _paragraph_texts(self) -> list[str]:
        """본문 문단 텍스트를 문서당 한 번만 만들어 재사용한다.

        `Document.paragraphs` 는 접근할 때마다 문단 목록을 새로 만들고,
        `Paragraph.text` 는 접근할 때마다 run 을 xpath 로 다시 모은다. 표마다
        캡션을 찾으려고 문서 전체를 다시 훑으면 비용이 표×문단으로 불어난다.
        문단 글을 캐시하면 각 표의 캡션을 찾을 때 같은 문단을 다시 읽는 비용을 줄인다.

        글은 `docx_text.final_text` 로 읽는다(읽기 규칙은 `_paragraphs` 위 설명).
        """
        if self._para_text_cache is None:
            self._para_text_cache = [docx_text.final_text(p) for p in self._paragraphs()]
        return self._para_text_cache

    def _paragraph_chunk_texts(self) -> list[str]:
        """본문 문단의 청크 본문 글(`docx_text.chunk_text`) — `_paragraph_texts` 와 같은 차례. 문서당 한 번 만든다."""
        if self._para_chunk_cache is None:
            self._para_chunk_cache = [docx_text.chunk_text(p) for p in self._paragraphs()]
        return self._para_chunk_cache

    def _paragraph_boxes(self) -> dict[int, str]:
        """본문 문단에 연결된 부동 텍스트 상자의 글 — 문단 번호 → `docx_text.box_text`. 문서당 한 번 만든다."""
        if self._box_cache is None:
            self._box_cache = {}
            for i, p in enumerate(self._paragraphs()):
                box = docx_text.box_text(p, read=docx_text.chunk_text)
                if box:
                    self._box_cache[i] = box
        return self._box_cache

    def _extract_figures(self) -> list[FigureInfo]:
        """
        그림 추출 (Spec §2.4) — 그림 개체마다 한 항목(`docx_figures.figures`).
        - 캡션만 Vector DB용 — 개체와 짝지은 캡션 문단 글, 짝이 없으면 빈 글
        - 이미지 파일은 렌더링용 저장 — 경로는 'media/…', 파일 복사는 그림 보강(04)이 한다
        """
        return [FigureInfo(figure_id=f.figure_id, figure_number=f.figure_number, caption=f.caption,
                           file_path=f.file_path, more_file_paths=f.more_file_paths)
                for f in docx_figures.figures(self.doc, self.tdoc_number)]


# =============================================================================
# 1-6: 청킹 엔진
# =============================================================================

class ChunkEngine:
    """
    청킹 엔진 (Spec §3.1.1)
    - 최소 청크: 100 토큰 (미만 시 병합)
    - 최대 청크: 2,000 토큰 (초과 시 분할)
    - 오버랩: 100 토큰

    v2.0 개선사항:
    - 작은 청크: 이전 청크와 병합 (마지막 청크 포함)
    - 큰 청크: 문장 단위 분할
    - chunkId 생성 지원
    """

    MIN_TOKENS = 100
    MAX_TOKENS = 2000
    OVERLAP_TOKENS = 100

    def __init__(self):
        pass

    def count_tokens(self, text: str) -> int:
        """토큰 수 추정 (공백 기준, 대략적)"""
        # 대략 1 토큰 = 4 글자 (영어 기준)
        return len(text) // 4

    def chunk_sections(self, sections: list[Section], tdoc_number: str = None) -> list[dict]:
        """섹션들을 청크로 분할"""
        chunks = []
        chunk_idx = 0

        for section in sections:
            section_chunks = self._chunk_text(
                section.content,
                section.title
            )

            for chunk_text in section_chunks:
                chunk_idx += 1
                chunks.append({
                    'chunkIndex': chunk_idx,
                    'sectionTitle': section.title,
                    'content': chunk_text,
                    'tokenCount': self.count_tokens(chunk_text)
                })

        # 1단계: 큰 청크 분할 (> 2000 토큰)
        chunks = self._split_oversized_chunks(chunks)

        # 2단계: 작은 청크 병합 (< 100 토큰)
        chunks = self._merge_small_chunks(chunks)

        # 3단계: chunkId 생성 (tdoc_number가 제공된 경우)
        if tdoc_number:
            for i, chunk in enumerate(chunks):
                chunk['chunkId'] = f"{tdoc_number}-{i+1:03d}"

        return chunks

    def _chunk_text(self, text: str, section_title: str) -> list[str]:
        """텍스트를 청크로 분할 (문단 단위)"""
        tokens = self.count_tokens(text)

        # 최대 크기 이하면 그대로 반환
        if tokens <= self.MAX_TOKENS:
            return [text]

        # 분할 필요
        chunks = []
        paragraphs = text.split('\n')
        current_chunk = []
        current_tokens = 0

        for para in paragraphs:
            para_tokens = self.count_tokens(para)

            if current_tokens + para_tokens > self.MAX_TOKENS:
                # 현재 청크 저장
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))

                # 오버랩 처리
                overlap_text = current_chunk[-1] if current_chunk else ""
                current_chunk = [overlap_text, para] if overlap_text else [para]
                current_tokens = self.count_tokens('\n'.join(current_chunk))
            else:
                current_chunk.append(para)
                current_tokens += para_tokens

        # 마지막 청크
        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks

    def _split_oversized_chunks(self, chunks: list[dict]) -> list[dict]:
        """큰 청크 분할 (> MAX_TOKENS)"""
        result = []

        for chunk in chunks:
            if chunk['tokenCount'] <= self.MAX_TOKENS:
                result.append(chunk)
                continue

            # 문장 단위로 분할
            text = chunk['content']
            sentences = self._split_into_sentences(text)

            current_text = []
            current_tokens = 0

            for sentence in sentences:
                sent_tokens = self.count_tokens(sentence)

                if current_tokens + sent_tokens > self.MAX_TOKENS and current_text:
                    # 현재까지 저장
                    result.append({
                        'chunkIndex': len(result) + 1,
                        'sectionTitle': chunk['sectionTitle'],
                        'content': ' '.join(current_text),
                        'tokenCount': current_tokens
                    })
                    current_text = [sentence]
                    current_tokens = sent_tokens
                else:
                    current_text.append(sentence)
                    current_tokens += sent_tokens

            # 마지막 부분
            if current_text:
                result.append({
                    'chunkIndex': len(result) + 1,
                    'sectionTitle': chunk['sectionTitle'],
                    'content': ' '.join(current_text),
                    'tokenCount': current_tokens
                })

        return result

    def _split_into_sentences(self, text: str) -> list[str]:
        """텍스트를 문장으로 분할"""
        import re
        # 문장 종결 패턴: '. ', '? ', '! ' (단, 소수점/약어 제외)
        # 간단한 휴리스틱: 공백 뒤에 대문자가 오는 경우
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        return [s.strip() for s in sentences if s.strip()]

    def _merge_small_chunks(self, chunks: list[dict]) -> list[dict]:
        """작은 청크 병합 (< MIN_TOKENS) - 개선된 버전"""
        if not chunks:
            return chunks

        merged = []

        for chunk in chunks:
            # 이전 청크가 있고, 현재 청크가 작으면 병합
            if merged and chunk['tokenCount'] < self.MIN_TOKENS:
                prev = merged[-1]
                merged_content = prev['content'] + '\n' + chunk['content']
                merged_tokens = self.count_tokens(merged_content)

                # 병합해도 MAX_TOKENS 이하면 병합
                if merged_tokens <= self.MAX_TOKENS:
                    merged[-1] = {
                        'chunkIndex': prev['chunkIndex'],
                        'sectionTitle': ' / '.join(dict.fromkeys(
                            title for title in (prev.get('sectionTitle', ''), chunk.get('sectionTitle', ''))
                            if title)),
                        'content': merged_content,
                        'tokenCount': merged_tokens
                    }
                    continue

            # 이전 청크가 작으면 현재 청크와 병합
            if merged and merged[-1]['tokenCount'] < self.MIN_TOKENS:
                prev = merged[-1]
                merged_content = prev['content'] + '\n' + chunk['content']
                merged_tokens = self.count_tokens(merged_content)

                if merged_tokens <= self.MAX_TOKENS:
                    merged[-1] = {
                        'chunkIndex': prev['chunkIndex'],
                        'sectionTitle': ' / '.join(dict.fromkeys(
                            title for title in (prev.get('sectionTitle', ''), chunk.get('sectionTitle', ''))
                            if title)),
                        'content': merged_content,
                        'tokenCount': merged_tokens
                    }
                    continue

            # 병합하지 않고 추가
            chunk['chunkIndex'] = len(merged) + 1
            merged.append(chunk)

        return merged


# =============================================================================
# WG (Working Group) 설정 — WG-agnostic 확장 지원
# =============================================================================

# 3GPP WG별 회의 폴더 접두사 매핑
WG_FOLDER_PREFIX = {
    "RAN1": "TSGR1_",
    "RAN2": "TSGR2_",
    "RAN3": "TSGR3_",
    "RAN4": "TSGR4_",
    "RAN5": "TSGR5_",
    "SA1":  "S1_",
    "SA2":  "S2_",
    "SA3":  "S3_",
    "SA4":  "S4_",
    "SA5":  "S5_",
    "SA6":  "S6_",
    "CT1":  "C1_",
    "CT3":  "C3_",
    "CT4":  "C4_",
    "CT6":  "C6_",
}

DEFAULT_WG = "RAN4"

# WG별 TDoc 번호 접두사 (Neo4j 쿼리용)
WG_TDOC_PREFIX = {
    "RAN1": "R1-",
    "RAN2": "R2-",
    "RAN3": "R3-",
    "RAN4": "R4-",
    "RAN5": "R5-",
    "SA1":  "S1-",
    "SA2":  "S2-",
    "SA3":  "S3-",
    "SA4":  "S4-",
    "SA5":  "S5-",
    "SA6":  "S6-",
    "CT1":  "C1-",
    "CT3":  "C3-",
    "CT4":  "C4-",
    "CT6":  "C6-",
}



def _zip_container(f: Path) -> bool:
    """앞 두 바이트가 ZIP 서명(`PK`)인가. 이름이 아니라 내용으로 읽을 수 있는 문서를 가린다."""
    try:
        with open(f, "rb") as fh:
            return fh.read(2) == b"PK"
    except OSError:
        return False


def _own_name(tdoc_number: str) -> re.Pattern:
    """이름이 그 TDoc 번호로 시작하는가. 번호 안 구분자는 `-` · `_` · 공백 · 없음을 같게 본다."""
    return re.compile(re.escape(tdoc_number).replace(r"\-", "[-_ ]?") + r"(?!\d)", re.I)


def _residue(name: str) -> bool:
    """`._X`(AppleDouble) · `~$X`(Word 소유자 파일). 문서의 확장자를 달고 있을 뿐 문서가 아니다."""
    return name.startswith("._") or name.startswith("~$")


def _doc_candidate(f: Path) -> bool:
    return f.is_file() and f.suffix.lower() in (".docx", ".docm") and not _residue(f.name)


#: 묶음의 표지 문서 이름(`R3-183592 38.413-090 cover page.docx` · `R3-170744_Cover sheet.docx` ·
#: `R3-183594_coverpage38.415_v020.docx` · `R3-183598_Cover.docx`). `coverage` · `covering` · `discovery` 는 아니다.
_COVER_NAME = re.compile(r"(?<![a-z])cover(?:[ _-]?(?:page|sheet|letter|note))?(?![a-z])", re.I)

#: 규격 초안 표지 서신의 Title 필드 값 — 규격 번호와 판 번호로 시작한다(`find_docx_file` 참고).
_SPEC_VERSION_TITLE = re.compile(
    r"^\W*(?:draft\s+)?(?:3GPP\s+)?T[SR]\s*(\d{2})\s*\.?\s*(\d{3})(?:-\d+)?\b[\s,:]*(?:v|version\s*)?\s*\d+\.\d+\.\d+",
    re.I)
_TITLE_FIELD = re.compile(r"Title\s*:\s*(.*)", re.I | re.S)


def _cover_letter_spec(f: Path) -> tuple[str, str] | None:
    """문서의 첫 Title 필드가 규격 번호 · 판 번호로 시작하면 규격 번호 두 조각(`('30', '531')`), 아니면 None.

    값이 같은 문단에 없으면(표 칸이 나뉜 양식) 다음 문단을 값으로 본다. 읽지 못하는 파일은 None 이다.
    """
    try:
        with zipfile.ZipFile(f) as z:
            xml = z.read("word/document.xml").decode("utf-8", "replace")
    except (OSError, KeyError, zipfile.BadZipFile):
        return None
    paras = [t for t in (re.sub(r"<[^>]+>", "", p).strip() for p in re.findall(r"<w:p[ >].*?</w:p>", xml, re.S)) if t]
    for i, p in enumerate(paras):
        m = _TITLE_FIELD.match(p)
        if m:
            value = m.group(1).strip() or (paras[i + 1] if i + 1 < len(paras) else "")
            s = _SPEC_VERSION_TITLE.match(value)
            return (s.group(1), s.group(2)) if s else None
    return None


def find_docx_file(tdoc_folder: Path) -> Path | None:
    """Tdoc 폴더에서 읽을 docx/docm 파일 하나를 고른다 (case-insensitive).

    .docm = Macro-Enabled Word Document. 내부 구조는 .docx와 동일 (OOXML).
    python-docx는 거부하지만 zipfile+lxml로 파싱 가능 (_xml_damaged 폴백).

    xlsx/pptx는 Spec §1.3에서 제외 대상이므로 포함하지 않음.

    후보가 여럿이면 다음 차례로 하나를 고른다.

    1. ZIP 컨테이너인 것. 이름만 .docx 인 옛 Word 문서는 phase-0 변환이 `X.docx.docx` 로
       곁에 두므로 원본과 변환본이 함께 후보가 된다. 읽을 수 있는 쪽은 변환본이다.
    2. 이름이 표지(cover page · cover sheet)가 아닌 것. TS · TR 초안 묶음은 제 번호를 단 표지 한 쪽과
       번호 없는 본문(`38413-090_cl.docx` · `38413-090_rm.docx`)으로 오고, 제 번호 파일끼리라도 이름
       차례로는 `R3-170744_Cover sheet.docx` 가 `R3-170744_TR 38 801 v120 (clean).docx` 보다 먼저 온다.
       표지는 "첨부를 보라"는 한 쪽이고 Tdoc 제목(`TS 38.413 v0.9.0 covering agreements of RAN3#100`)이
       가리키는 내용은 본문이다. 표지는 버리지 않고 `tdoc_documents` 가 본문 뒤에 붙여 읽는다.
    3. 이름이 폴더의 TDoc 번호로 시작하는 것 (`R4_2104965_TR37.717-11-21 v0.4.0_changed_marks.docx`). 3GPP 기고는 본문 + 초안 CR +
       부속서가 한 폴더에 오는 묶음이고, Neo4j 의 Tdoc 제목 · 제출처가 가리키는 문서는
       제 번호를 단 파일이다.
    4. 이름 줄기(stem) 차례. 한 줄기가 다른 줄기의 앞머리이면 짧은 쪽이 바탕 문서다
       (`R4-2111700_MeetingReport.docx` 가 `R4-2111700_MeetingReport Annexes.docx` 보다 먼저).
    5. 줄기가 같으면 .docx 를 .docm 보다 먼저 (`R4-2313118`).
    6. 마지막은 이름 전체 차례 — 같은 폴더면 늘 같은 문서를 고른다.

    이 차례로 고른 문서가 제 번호 파일이고 그 Title 필드가 규격 번호와 판 번호로 시작하면
    (`TR 30.531 v1.64.0 Work Plan …` · `TS 36.465, v1.4.0` · `TS 37.579-5, Version 0.1.0`), 그 문서는
    규격 초안을 넘기는 표지 서신이다. 이때는 같은 폴더에서 이름에 그 규격 번호가 든 다른 후보
    (`draft_30531-016400_cl.docx` · `36465-140-clean.docx` · `TR36.898-180-clean.docx`)를 위 차례로 골라 대신 쓴다.

    > 주의: 표지 서신은 이름에 cover 가 없어 2 로 걸러지지 않고, 제 번호를 달아 3 에서 오히려 앞선다.
    > 표지 서신만 읽으면 그 TDoc이 다루는 규격 본문이 빠진다. `pCR to TS …`처럼 다른 말로
    > 시작하는 제목은 표지 서신으로 분류하지 않는다. `tdoc_documents`는 본문 뒤에 표지 서신도 붙여 읽는다.

    주의: `iterdir()` 의 첫 후보를 그대로 돌려주면 고르는 문서를 파일시스템 순서가 정한다.
    같은 코퍼스를 다시 파싱할 때도 문서를 일관되게 고르려면 위의 정렬 규칙을 사용한다.
    제 번호 파일이 있으면 후보 우선순위에서 이를 고려한다.

    폴더 직속에 후보가 없으면 하위 폴더로 내려간다. 단, 직속 파일이 전부 `.zip` 이거나
    찌꺼기(`._*` · `~$*`)일 때만이다. 3GPP 기고 zip 가운데 문서를 제 번호 폴더에 한 겹 더
    싸 둔 것(`R1-…/R1-… title.docx`)이 있어 풀어 놓으면 폴더 직속에는 문서가 없다.
    직속에 pptx · xlsx · pdf 같은 다른 형식이 있으면 그것이 바탕 문서이고 하위 폴더의
    docx 는 딸린 자료이므로 내려가지 않는다. 내려간 자리에서도 위 차례를 쓰되, 3 다음에
    얕은 쪽을 먼저 본다. `__MACOSX` 아래는 AppleDouble 사본이므로 보지 않는다.

    하위 폴더 검색은 직속 후보가 없는 묶음에만 적용한다. 직속 후보가 있는 폴더는
    앞서 설명한 선택 규칙을 그대로 따른다.
    문서가 하위 폴더에 있으면 문서의 부모 폴더는 TDoc 폴더가 아니므로, TDoc 번호는
    문서 경로가 아니라 이 함수에 넘긴 폴더에서 얻어야 한다(`TdocParser(tdoc_number=…)`).

    이 함수는 바탕 문서 하나를 고른다. 파싱이 실제로 읽는 묶음(바탕 문서 + 표지)은 `tdoc_documents` 다.
    """
    return _bundle(tdoc_folder)[0]


def _digest(f: Path) -> str:
    """문서 비교용 SHA1을 64 KiB씩 읽어 계산한다."""
    digest = hashlib.sha1()
    with f.open('rb') as stream:
        for block in iter(lambda: stream.read(64 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _bundle(tdoc_folder: Path) -> tuple[Path | None, list[Path]]:
    """(바탕 문서, 함께 읽을 표지 목록) — 바탕 문서는 `find_docx_file` 의 규칙, 표지는 `tdoc_documents` 의 규칙.

    후보를 고르기 전에 같은 이름의 배포 `X.docx` 와 변환본 `X.doc.docx` 쌍을 글이 많은 판 하나로 줄인다
    (`docx_pick.drop_shipped_twins`). 주의: 줄이지 않으면 이름 차례가 `X.docx` 를 고르는데, RAN5 의 이런 쌍
    11 곳은 그 `X.docx` 가 빈 CR 양식이고 채운 CR 은 `.doc` 쪽에만 있다.
    """
    cands = [f for f in tdoc_folder.iterdir() if _doc_candidate(f)]
    if not cands and all(f.suffix.lower() == ".zip" or _residue(f.name)
                         for f in tdoc_folder.iterdir() if f.is_file()):
        cands = [f for f in tdoc_folder.rglob("*")
                 if _doc_candidate(f) and "__MACOSX" not in f.relative_to(tdoc_folder).parts]
    cands = docx_pick.drop_shipped_twins(cands)
    if len(cands) < 2:
        return (cands[0] if cands else None), []
    own = _own_name(tdoc_number_of(tdoc_folder.name))

    def key(f: Path):
        rel = f.relative_to(tdoc_folder)
        return (not _zip_container(f), _COVER_NAME.search(f.stem) is not None,
                own.match(f.name) is None, len(rel.parts),
                f.stem, f.suffix.lower() != ".docx", str(rel))
    pick = min(cands, key=key)
    body, covers = pick, []
    spec = _cover_letter_spec(pick) if own.match(pick.name) else None
    if spec:
        named = re.compile(rf"(?<!\d){spec[0]}[ .]?{spec[1]}(?!\d)")
        bodies = [f for f in cands if f != pick and named.search(f.stem)]
        if bodies:
            body, covers = min(bodies, key=key), [pick]
    if not _COVER_NAME.search(body.stem):
        covers += sorted((f for f in cands if f != body and f not in covers
                          and _zip_container(f) and _COVER_NAME.search(f.stem)), key=key)
    if not covers:
        return body, []
    seen, kept = {_digest(body)}, []
    for f in covers:
        d = _digest(f)
        if d not in seen:
            seen.add(d)
            kept.append(f)
    return body, kept


def tdoc_documents(tdoc_folder: Path) -> list[Path]:
    """TDoc 폴더에서 파싱이 읽는 문서 묶음 — 바탕 문서(`find_docx_file`) 다음에 표지를 붙인 목록. 문서가 없으면 빈 목록.

    표지는 두 가지다.
    1. 바탕 문서가 표지 서신을 제치고 고른 규격 본문이면 그 표지 서신(`find_docx_file` 의 표지 서신 규칙).
    2. 이름이 표지(`_COVER_NAME`)인 ZIP 문서. 바탕 문서의 이름도 표지이면(후보가 모두 표지) 더하지 않는다.
    표지끼리는 `find_docx_file` 의 차례를 따른다. 바탕 문서나 앞선 표지와 바이트가 같은 사본은 한 번만 읽는다.

    표지에도 CR 양식의 변경 이유·영향 절, 규격 앞머리, 표·그림이 포함될 수 있어 본문 뒤에 함께 읽는다.
    본문과 겹치는 글이 있는 표지도 이 단계에서는 그대로 읽어 표지의 고유 내용을 보존한다.

    다른 형제 문서(부속서 · 초안 CR · 비교본)는 이 목록에 들지 않는다. 그 손실은 수로 센다 —
    `scripts/common/data-integrity/check_corpus_bundle_loss.py`.
    """
    body, covers = _bundle(tdoc_folder)
    return [body, *covers] if body else []


def _table_seq(table_id: str) -> int:
    return int(table_id.rsplit("-", 1)[1])


def parse_documents(paths: list[Path], tdoc_number: str) -> ParsedContent:
    """문서 묶음(`tdoc_documents`)을 차례로 파싱해 한 TDoc 의 산출로 잇는다.

    첫 문서(바탕 문서)의 산출 뒤에 다음 문서의 산출을 붙인다. 문서 유형은 바탕 문서의 것이다.
    - 절: 문단 번호(start_idx · end_idx)를 앞 문서들의 문단 수만큼 민다. paragraph_count 는 합이다.
    - 표: 번호(`TBL-{tdoc}-{n:03d}`)를 앞 문서들이 쓴 가장 큰 번호 뒤로 민다.
    - 수식: 문서 차례로 1 부터 다시 매긴다. 수식 보강(05)은 `bundle_equation_sites` 로 같은 목록을 얻는다.
    - 그림: `docx_figures.bundle` 이 번호를 문서 차례로 잇고 둘째 문서부터의 그림 파일을 `media/cover…/` 로
      옮긴다. 그림 보강(04)도 같은 함수로 색인을 얻어 대조한다.
    문서 하나만 넘기면 `TdocParser(path, tdoc_number).parse()` 와 같다.
    """
    from tdoc_body_source_metadata import validate_source_selection
    validate_source_selection(_SCRIPTS_COMMON.parent.parent, Path(__file__).parents[2].name,
                              'tdoc', tdoc_number, paths)
    out = None
    groups = []
    for p in paths:
        c = TdocParser(p, tdoc_number).parse()
        groups.append(c.figures)
        if out is None:
            out = c
            continue
        for s in c.sections:
            s.start_idx += out.paragraph_count
            s.end_idx += out.paragraph_count
        out.sections += c.sections
        used = max((_table_seq(t.table_id) for t in out.tables), default=0)
        for t in c.tables:
            t.table_id = f"TBL-{tdoc_number}-{_table_seq(t.table_id) + used:03d}"
        out.tables += c.tables
        out.equations += c.equations
        out.paragraph_count += c.paragraph_count
    if out is None:
        raise ValueError(f"{tdoc_number}: 읽을 문서가 없다")
    for k, e in enumerate(out.equations, 1):
        e.equationId, e.index = f"EQ-{tdoc_number}-{k:03d}", k
    out.figures = [f for g in docx_figures.bundle(groups, tdoc_number) for f in g]
    return out


def bundle_equation_sites(paths: list[Path], tdoc_number: str) -> list[tuple]:
    """문서 묶음의 `equation_sites` — 문서 차례로 잇고, 본문 문단 번호를 앞 문서들의 문단 수만큼 민다(표 안 -1 은 그대로).

    `parse_documents` 가 equations.json 에 쓰는 목록과 같은 차례이고, 민 문단 번호는 그 절의 start_idx 와 같은 자다.
    """
    out, base = [], 0
    for p in paths:
        parser = TdocParser(p, tdoc_number)
        out += [(eq, owner, at + base if at >= 0 else at, kind)
                for eq, owner, at, kind in parser.document_equation_sites()]
        base += parser.paragraph_total()
    return out


def document_figures(path: Path, tdoc_number: str) -> tuple:
    """(열린 문서, 그림 목록) — 파싱(03)이 그 문서에서 얻는 그림 목록과 같은 규칙.

    python-docx 로 열리지 않는 ZIP(XML 손상)은 03 의 손상 경로가 그림을 비우므로 (None, []) 이다.
    ZIP 이 아니면 03 처럼 거절을 올린다.
    """
    try:
        doc = docx_text.open_document(path)
    except Exception:
        if not zipfile.is_zipfile(path):
            raise
        return None, []
    return doc, docx_figures.figures(doc, tdoc_number)


@functools.lru_cache(maxsize=None)
def _docs_index(docs_dir: str) -> dict[str, str]:
    """회의 Docs 폴더의 {TDoc 번호: 폴더 이름}. 파싱(03 `collect_tasks`)이 번호 자리를 주는
    규칙을 그대로 따른다 — 정렬 순서로 먼저 온, `.docx` 가 있는 폴더가 번호를 갖는다.
    `.docx` 없는 폴더는 03 에서 자리를 얻지 못하므로 여기서도 건너뛴다. 03 이 같은 회의 다른 번호의
    문서 사본이라 빼는 번호(`meeting_slots`)는 KG 를 물어야 가려지므로 여기서 가리지 않는다 — 이 색인은
    파싱 산출이 있는 번호의 원본 폴더를 찾는 데 쓰이고, 그 번호들에서는 두 규칙이 같은 폴더를 준다."""
    idx: dict[str, str] = {}
    for p in sorted(Path(docs_dir).iterdir()):
        if p.is_dir() and find_docx_file(p) is not None:
            idx.setdefault(tdoc_number_of(p.name), p.name)
    return idx


def tdoc_dir_for(docs_dir: Path, tdoc_number: str) -> Path | None:
    """TDoc 번호 → 03 이 그 번호로 파싱한 원본 폴더. 이름이 번호와 그대로 같지 않은
    폴더(앞뒤 공백 · `%20` · 끝 마침표 등)도, 번호가 겹친 폴더 중 03 이 고른 쪽도 같은 규칙으로 찾는다."""
    if not docs_dir.is_dir():
        return None
    name = _docs_index(str(docs_dir)).get(tdoc_number)
    return docs_dir / name if name else None


@functools.lru_cache(maxsize=None)
def _meeting_folder_index(base_dir: str, wg: str) -> dict[str, str]:
    """실제 회의 폴더들의 meetingId → 폴더 이름 (파싱 03 이 폴더에서 meetingId 를 만드는 사상의 역)."""
    prefix = WG_FOLDER_PREFIX.get(wg, "")
    idx = {}
    for p in sorted(Path(base_dir).iterdir()):
        if p.is_dir() and p.name.startswith(prefix):
            idx.setdefault(convert_meeting_id(p.name, wg), p.name)
    return idx


def meeting_id_to_folder(meeting_id: str, wg: str = DEFAULT_WG, base_dir: Path = None) -> str:
    """
    Meeting ID를 폴더명으로 변환 (convert_meeting_id의 역변환)

    예: RAN4#120 → TSGR4_120, RAN4#100-e → TSGR4_100-e (하이픈 유지)
    예: RAN4#92Bis → TSGR4_92Bis

    REV 9.2: RAN4 폴더는 `_e` 아닌 `-e` 사용 (mismatch root cause).
    base_dir 인자 제공 시 fs glob으로 실제 폴더명 매칭.
    """
    prefix = WG_FOLDER_PREFIX.get(wg, "")
    suffix = meeting_id.replace(f"{wg}#", "")

    # 1차 후보: 하이픈 유지 (RAN4 실제 패턴)
    canonical = f"{prefix}{suffix}"

    # base_dir 제공 시 실제 폴더명 검증 + fallback
    if base_dir is not None:
        try:
            base = Path(base_dir)
            if base.exists():
                # 03 이 실제 폴더 이름에서 만든 meetingId 라면 그 폴더로 정확히 되돌린다.
                # 아래 규칙 추정은 그 폴더가 없을 때만 쓴다(예: TSGR4_94_eBis ↔ RAN4#94bis-e).
                exact = _meeting_folder_index(str(base), wg).get(meeting_id)
                if exact:
                    return exact
                # exact match
                if (base / canonical).is_dir():
                    return canonical
                # _e 변환 시도 (legacy 패턴)
                alt = canonical.replace("-e", "_e")
                if (base / alt).is_dir():
                    return alt
                # location/bis suffix glob (TSGR4_94 → TSGR4_94_*, TSGR4_92Bis 등)
                for cand in sorted(base.glob(f"{canonical}_*")):
                    if cand.is_dir():
                        return cand.name
        except Exception:
            pass
    return canonical


def convert_meeting_id(folder_name: str, wg: str = DEFAULT_WG) -> str:
    """
    Meeting ID 변환 (Spec §3.2)
    WG-agnostic: WG 파라미터에 따라 접두사 자동 판별

    예시:
        TSGR4_120     → RAN4#120
        TSGR4_94_eBis → RAN4#94bis-e
    """
    prefix = WG_FOLDER_PREFIX.get(wg, "")
    if prefix and folder_name.startswith(prefix):
        suffix = folder_name[len(prefix):]
        # RAN5 회의 폴더 꼴(위치 접미사가 붙고 101 이상은 이중 밑줄)을 읽는 갈래다. 이 사본의 기본 WG 로는 타지 않는다.
        if wg == "RAN5":
            # Fix (Cause 5): "Electronic" 키워드 → -e suffix 추가
            m = re.match(r'_?(\d+[a-z]*(?:bis)?)(.*)$', suffix)
            if m:
                meeting_num = m.group(1)
                location = m.group(2) or ""
                if 'electronic' in location.lower():
                    return f"{wg}#{meeting_num}-e"
                return f"{wg}#{meeting_num}"
        # 접미사 정규화: 100_e → 100-e, 100b_e → 100b-e
        # e-meeting 표시가 꼬리에 없고 bis 앞에 끼어드는 폴더가 있다(`TSGR4_94_eBis`).
        # 꼬리만 보는 치환은 그것을 그대로 통과시켜 `RAN4#94_eBis` 같은 반쯤 바뀐
        # 식별자를 트리와 VDB 에 박아 넣는다 — 어느 정규화로도 회의에 닿지 못한다.
        suffix = re.sub(r'[-_][eE]([Bb][Ii][Ss])$', lambda m: m.group(1).lower() + '-e', suffix)
        suffix = re.sub(r'_e$', '-e', suffix)
        suffix = re.sub(r'(\d[a-z])_e$', r'\1-e', suffix)
        return f"{wg}#{suffix}"
    # 접두사가 맞지 않으면 일반 패턴으로 시도
    for wg_name, wg_prefix in WG_FOLDER_PREFIX.items():
        if folder_name.startswith(wg_prefix):
            suffix = folder_name[len(wg_prefix):]
            suffix = re.sub(r'_e$', '-e', suffix)
            suffix = re.sub(r'(\d[a-z])_e$', r'\1-e', suffix)
            return f"{wg_name}#{suffix}"
    return folder_name


@functools.lru_cache(maxsize=None)
def _canonical_meeting_id():
    """이 WG 의 KG 가 `Meeting.canonicalMeetingNumber` 를 짓는 정본화 규칙(phase-1 `meeting_id.canonical_meeting_id`).

    옮겨 적지 않고 그 자리에서 읽는다 — 두 벌이면 정본형이 갈라져 같은 회의가 서로 없는 회의로 보인다.
    """
    import importlib.util
    src = Path(__file__).resolve().parents[2] / "phase-1" / "jsonld" / "meeting_id.py"
    spec = importlib.util.spec_from_file_location(f"_meeting_id_{src.parents[2].name}", src)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.canonical_meeting_id


def kg_titles_in_meeting(driver, tdoc_numbers, meeting_id: str) -> dict[str, str]:
    """`meeting_id` 회의에 올라온 TDoc 의 KG 제목 {번호: 제목}. 제목이 빈 번호는 뺀다.

    회의로 좁혀 묻는다. 번호만으로 물으면 다른 회의 폴더에 잘못 놓인 번호가 제 회의의 제목을 얻어
    남의 문서 사본 판정(`tdoc_copy_owner`)에서 주인으로 읽힌다. 파싱 트리의 회의 id 는 보유형
    (`…-bis` · `…Bis` · `…-e`)이고 KG `Meeting.meetingNumber` 는 다른 표기를 쓰는 회의가 있어 글자로
    견주면 같은 회의가 어긋나므로, 정본형으로 접어 `canonicalMeetingNumber` 와 견준다
    (`docs/tsg/build/standards/meeting_id_normalization.md` §3.3).
    """
    nums = sorted(set(tdoc_numbers))
    if not nums:
        return {}
    with driver.session() as session:
        rows = session.run(
            "MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber: $mid}) "
            "WHERE t.tdocNumber IN $nums RETURN t.tdocNumber AS n, t.title AS title",
            mid=_canonical_meeting_id()(meeting_id), nums=nums)
        return {r["n"]: r["title"] for r in rows if r["title"]}


# =============================================================================
# 1-7: 메타데이터 연동
# =============================================================================

class MetadataResolver:
    """
    메타데이터 연동 (Spec §3.2)
    - meeting_id 변환 (WG-agnostic)
    - Neo4j 조회 (tdocNumber 기준)
    """

    # Neo4j 연결 설정 (Phase-1과 동일)
    DEFAULT_AUTH = credentials.neo4j_auth()

    def __init__(self, neo4j_uri: str = None, neo4j_auth: tuple = None,
                 wg: str = DEFAULT_WG):
        self.neo4j_uri = endpoints.neo4j_uri(wg, override=neo4j_uri)
        self.neo4j_auth = neo4j_auth or self.DEFAULT_AUTH
        self.wg = wg
        self._driver = None
        self._connected = False

    def connect(self):
        """Neo4j 연결"""
        if self._driver is None:
            try:
                from neo4j import GraphDatabase
                self._driver = GraphDatabase.driver(self.neo4j_uri, auth=self.neo4j_auth)
                # 연결 테스트
                with self._driver.session() as session:
                    session.run("RETURN 1")
                self._connected = True
            except Exception as e:
                print(f"[WARN] Neo4j 연결 실패: {e}")
                self._connected = False

    def close(self):
        """Neo4j 연결 종료"""
        if self._driver:
            self._driver.close()
            self._driver = None

    def convert_meeting_id(self, folder_name: str) -> str:
        """Meeting ID 변환 — 모듈 함수 convert_meeting_id() 위임"""
        return convert_meeting_id(folder_name, self.wg)

    def is_kg_placeholder(self, tdoc_number: str) -> bool:
        """Phase-1 목록에 없어 phase-6-backfill 이 KG 에 등록한 Tdoc 노드인가.

        그런 노드는 제목 · 제출사가 비어 있어도 KG 가 아는 문서다(`docs/tsg/build/process/orphan_detection_guide.md`
        패턴 A — 회의 문서에는 있고 TDoc 목록에는 없는 문서). 03 은 이 문서를 빈 메타데이터로 남기고, KG 에 노드가
        아예 없는 문서만 Phase-1 적재 문제로 실패시킨다.
        """
        if not self._connected:
            return False
        with self._driver.session() as session:
            record = session.run(
                "MATCH (t:Tdoc {tdocNumber: $tdocNumber}) "
                "RETURN any(x IN collect(t._createdBy) WHERE x = 'phase-6-backfill') AS placeholder",
                tdocNumber=tdoc_number).single()
        return bool(record and record['placeholder'])

    def resolve_metadata(self, tdoc_number: str, meeting_id: str) -> dict:
        """
        Neo4j에서 메타데이터 조회 (Spec §3.2)
        Phase-1 KG와 연결: Tdoc, Company, Release, AgendaItem
        """
        # 기본 메타데이터
        metadata = {
            'tdocNumber': tdoc_number,
            'meetingId': meeting_id,
            'source': [],
            'type': '',
            'release': '',
            'agendaItem': '',
            'title': ''
        }

        # Neo4j 연결이 없으면 기본값 반환
        if not self._connected:
            return metadata

        try:
            with self._driver.session() as session:
                # Phase-1 KG 스키마 기반 쿼리
                # Company: companyName 속성 사용
                # AgendaItem: agendaNumber 속성 사용
                query = """
                MATCH (t:Tdoc {tdocNumber: $tdocNumber})
                OPTIONAL MATCH (t)-[:SUBMITTED_BY]->(c:Company)
                OPTIONAL MATCH (t)-[:TARGET_RELEASE]->(r:Release)
                OPTIONAL MATCH (t)-[:BELONGS_TO]->(a:AgendaItem)
                RETURN t.title as title,
                       t.type as type,
                       collect(DISTINCT c.companyName) as sources,
                       r.releaseName as release,
                       a.agendaNumber as agendaItem
                """
                result = session.run(query, tdocNumber=tdoc_number)
                record = result.single()
                # 꼬리 이름(첨부 `R3-237153_attach_S2-2311681` · 변형 `R4-2103133x`)은 Phase-1 목록에 제 행이 없다.
                # 그 이름의 Tdoc 노드는 없거나 phase-6-backfill 이 만든 빈 노드(제목 · 제출사 없음)뿐이라, 그대로 두면
                # 03 이 메타데이터 조회 실패로 문서를 버린다. 그 파일을 실어 온 앞머리 번호의 행을 쓴다.
                # tdocNumber 는 폴더 이름 그대로 둔다.
                parent = parent_tdoc_number(tdoc_number)
                if parent and not (record and (record['title'] or record['sources'])):
                    record = session.run(query, tdocNumber=parent).single() or record

                if record:
                    metadata['title'] = record['title'] or ''
                    metadata['type'] = record['type'] or ''
                    metadata['source'] = [s for s in (record['sources'] or []) if s]
                    metadata['release'] = record['release'] or ''
                    metadata['agendaItem'] = record['agendaItem'] or ''

        except Exception as e:
            print(f"[WARN] 메타데이터 조회 실패 ({tdoc_number}): {e}")

        return metadata


# =============================================================================
# 1-8: 출력 생성
# =============================================================================

class OutputGenerator:
    """
    출력 생성 (Spec §3.4)
    vectordb/parsed/tdocs/{wg}/{meeting_id}/{tdoc_number}/
    ├── chunks.json
    ├── figures/
    │   ├── index.json
    │   └── media/
    ├── tables/
    │   ├── index.json
    │   └── html/
    └── equations.json
    """

    def __init__(self, base_path: Path):
        self.base_path = base_path

    def generate(self, content: ParsedContent, chunks: list[dict],
                 metadata: dict, meeting_id: str) -> Path:
        """출력 파일 생성"""
        # 출력 디렉토리 생성
        output_dir = self.base_path / meeting_id / content.tdoc_number
        output_dir.mkdir(parents=True, exist_ok=True)

        # 0.5 HARD_MAX 강제 (정규 프로세스 hardening)
        chunks = _enforce_hard_max(chunks, hard_max=_HARD_MAX_TOK)

        # 1. figures/
        if content.figures or (output_dir / 'figures/index.json').exists():
            figures_dir = output_dir / 'figures'
            figures_dir.mkdir(exist_ok=True)
            (figures_dir / 'media').mkdir(exist_ok=True)

            # Spec §3.4 항목 — 04 가 대조하는 색인과 같은 함수(`docx_figures.index_entry`)로 만든다
            figures_index = {
                'tdocNumber': content.tdoc_number,
                'figures': [docx_figures.index_entry(fig) for fig in content.figures]
            }

            write_json_atomic(figures_dir / 'index.json', figures_index)

        # 2. tables/
        if content.tables or (output_dir / 'tables/index.json').exists():
            tables_dir = output_dir / 'tables'
            tables_dir.mkdir(exist_ok=True)
            html_dir = tables_dir / 'html'
            html_dir.mkdir(exist_ok=True)

            tables_index = {
                'tdocNumber': content.tdoc_number,
                'tables': []
            }

            for table in content.tables:
                # HTML 파일 저장
                html_filename = f"{table.table_id}.html"
                write_text_atomic(html_dir / html_filename, table.html)

                tables_index['tables'].append({
                    'tableId': table.table_id,
                    'tableNumber': table.table_number,
                    'caption': table.caption,
                    'filePath': f"html/{html_filename}",
                    'equations': table.equations,
                    'isAgreementBox': table.is_agreement_box
                })

            write_json_atomic(tables_dir / 'index.json', tables_index)

        # 3. equations.json
        if content.equations or (output_dir / 'equations.json').exists():
            equations_data = {
                'tdocNumber': content.tdoc_number,
                'equations': [asdict(eq) for eq in content.equations],
                'total_count': len(content.equations),
                'omml_count': sum(1 for eq in content.equations if eq.source == "omml"),
                'ole_count': sum(1 for eq in content.equations if eq.source == "ole"),
            }

            write_json_atomic(output_dir / 'equations.json', equations_data)

        # 4. chunks.json — 맨 마지막에 임시 파일로 다 쓴 뒤 제자리로 옮긴다. 이 파일이 있으면
        # --resume 와 뒤 단계가 문서를 다 된 것으로 읽으므로, 쓰는 도중 워커가 죽으면 표시가 남지 않아야
        # 다음 실행이 그 문서를 처음부터 다시 쓴다.
        from tdoc_body_source_metadata import project as project_body_source_metadata
        metadata = project_body_source_metadata(_SCRIPTS_COMMON.parent.parent, Path(__file__).parents[2].name,
                                                'tdoc', content.tdoc_number, metadata)
        chunks_data = {
            'tdocNumber': content.tdoc_number,
            'meetingId': meeting_id,
            'type': content.doc_type,
            'paragraphCount': content.paragraph_count,
            'metadata': metadata,
            'chunks': chunks
        }
        write_json_atomic(output_dir / 'chunks.json', chunks_data)

        return output_dir


# Library exports
__all__ = [
    'ParsedContent', 'Section', 'TableInfo', 'FigureInfo', 'EquationInfo',
    'TdocParser', 'ChunkEngine', 'MetadataResolver', 'OutputGenerator',
]
