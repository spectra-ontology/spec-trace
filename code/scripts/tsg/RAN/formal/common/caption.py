"""caption.py — 회의록의 표 · 그림 제목(`Table 8.1-1: …` · `Figure 5-2: …`) 문법. 표 · 그림 추출기가 함께 쓴다.

제목 문단 안의 줄바꿈(`w:br`)은 제목의 일부다.

    Table 6.3.1.1.2-13: Mapping order of CSI reports to UCI bit sequence , ⏎with two-part CSI report(s)

`docx_text.final_text` 는 줄바꿈을 `\\n` 으로 살리므로, 제목 글을 한 줄로 가정한 `(.*)` 은 줄바꿈 앞에서
제목을 자른다. 여기서는 줄바꿈을 넘어 읽고 공백을 한 칸으로 편다.

제목은 제목 문단 자신의 글로 읽는다. 문단 안 글상자의 글은 제목이 아니다. 문단 자신의 글이 비어 있고
글상자 안에만 글이 있을 때만 첫 글상자 문단을 제목 후보로 본다.

`TDOC_*` · `tdoc_*` 는 Tdoc(기고 문서)의 그림 · 표 캡션 문법이다. 번호의 단 문법(부록 글자 · 글자 꼬리 · 자리표 ·
로마 숫자)은 회의록 제목 문법(`TABLE` · `FIGURE`)과 같다. 다른 것은 머리말 꼴, 줄표 이음 앞뒤의 빈칸, 번호 뒤
글로 본문 문장을 가르는 일이다.
"""
from __future__ import annotations

import re

import docx_text

def caption_text(p) -> str:
    """제목 후보 글 — 문단 자신의 확정 글, 비어 있으면 첫 글상자 문단의 확정 글."""
    for part in (p, *docx_text.iter_all_paragraphs(p)):
        text = docx_text.final_text(part).strip()
        if text:
            return text
    return ""


def read(pattern: re.Pattern, p) -> tuple[str, str] | None:
    """문단이 제목이면 `(번호, 공백을 편 제목 글)`, 아니면 None."""
    m = pattern.match(caption_text(p))
    if not m:
        return None
    return m.group(1), " ".join(m.group(2).split())


# Tdoc 그림 · 표 캡션 — 머리말('Figure' · 'Fig' · 'Fig.' / 'Table', 대소문자 무관) + 번호 + 나머지 글.
# 아래 꼴은 RAN1~5 표본(WG 마다 300 문서)의 캡션 후보 문단에서 잰 것이다.

#: 번호 한 단 — 숫자(글자 하나가 꼬리로 붙을 수 있다: '5a' · '3A'), 또는 자리표 'x' · 'xx' · 'x1'('Fig. x:' ·
#: 'Figure xx:' · 'Fig. x1:'). 글자가 둘 이상 이어지면 바로 뒤가 ':' 이거나 '.' · 줄표 다음 숫자일 때만
#: 꼬리다('Table 6.2.2EA-1:' · 'Table 6.2.2EA.4.1-1:' · 'Table 4.6.3-25AAA:' · 'Table 7.3.2-2aa:').
#: 그 밖에는 붙여 쓴 낱말이다('Table 1summarizes …' 의 번호는 '1', 'Figure 6.1.3.2-1is …' 의 번호는 '6.1.3.2-1').
#: RAN1~5 문서(WG 마다 표본 300 + 표본 밖 300)에서 번호 뒤에 글자 둘 이상이 빈칸 없이 붙은 문단은 23 개다.
#: 뒤가 ':' · '-' 숫자 · '.' 숫자인 18 개는 모두 표 캡션 번호였고(TH 스타일 15), 뒤가 빈칸인 5 개는 붙여 쓴
#: 낱말 2 개와 표 칸 안의 표 참조 3 개('Table H.3.1-4AB with condition RSRP')였다.
_TDOC_SEG = r"(?:\d+(?:[A-Za-z]{2,}(?=:|[.\-‑–]\d)|[A-Za-z](?![A-Za-z]))?|[xX]{1,2}\d*(?![A-Za-z]))"
#: 단 이음 — '.' · '_' 는 붙여 쓰고('Table 7.3A.1_1.4.1-1'), 줄표 꼴은 앞뒤 빈칸 하나를 허용한다('3.2.1- 1' ·
#: '6.2.2.2 – 1'). '.' 뒤 빈칸은 이음이 아니다 — 'Fig. 2. 16QAM' · 'Figure 1. 10MHz' 의 번호는 '2' · '1' 이다.
#: 줄표는 '-' · '‑' · '–' 셋이다. '—'(U+2014)로 숫자를 이은 캡션 후보 문단은 RAN1~5 문서(WG 마다 표본 300 +
#: 표본 밖 300)에 하나도 없었다.
_TDOC_JOIN = r"(?:[._]|\s?[-‑–]\s?)"


def _number(join: str) -> str:
    """번호 문법 — 단(`_TDOC_SEG`)을 join 으로 잇는다.

    부록 글자 머리('A.1-1' · 'B-2')가 붙을 수 있다. 로마 숫자도 번호다('Table I.' · 'Table II:').
    첫 단 뒤에는 '.' 다음 소문자 하나도 단이다 — 절 번호 자리표('Table 4.2.1.7.a-1' · 'Table 8.2.y.2-1' ·
    'Figure 8.z.1.2.1'). 이 단이 없으면 번호가 '4.2.1.7' · '8' 에서 잘린다.
    """
    return (rf"(?:(?:[A-Z][.\-‑–]?)?{_TDOC_SEG}(?:{join}{_TDOC_SEG}|\.[a-z](?![A-Za-z]))*"
            rf"|[IVX]+(?![A-Za-z]))")


#: Tdoc 번호.
_TDOC_NUM = _number(_TDOC_JOIN)
#: 머리말과 번호 사이 — 빈칸과 부호 하나('Table: 8.2.2.1.1-1' · 'Table.1' · 'Figure-1.' · 'Figure. 1:').
_TDOC_LEAD = r"\s*[.:\-‑–]?\s*"

#: 그림 캡션 후보. 그룹 num = 번호, rest = 번호 뒤 글.
TDOC_FIGURE = re.compile(rf"^\s*(?i:figure|fig\.?){_TDOC_LEAD}(?P<num>{_TDOC_NUM})(?P<rest>.*)$", re.S)
#: 표 캡션 후보. 그룹 num = 번호, rest = 번호 뒤 글.
TDOC_TABLE = re.compile(rf"^\s*(?i:table){_TDOC_LEAD}(?P<num>{_TDOC_NUM})(?P<rest>.*)$", re.S)

# 회의록 표 · 그림 제목 — 머리말 'Table' · 'Figure'(대소문자 무관) + 빈칸 + 번호 + 구분 부호 + 제목 글.
# 숫자와 '.' · '-' 만 받는 번호는 자리표 · 글자 꼬리 · 부록 글자 앞에서 끊겨 나머지를 제목으로 넘겼다
# ('Table 6.1.1-x: BS energy savings …' 의 번호 '6.1.1', 제목 'x: BS energy savings …').
# RAN1~5 Final Report 280 개에서 'Table' · 'Figure' 로 시작하는 문단 1,846 개 가운데 Tdoc 과 같은 단 문법으로
# 번호가 달라지는 문단은 292 개다(RAN1 227 · RAN2 4 · RAN3 4 · RAN4 47 · RAN5 10). 'Table 7.3.1.1.2-5E' ·
# 'Table 6.1.1.x-1' · 'Table A.3-1' · 'Table X.12' · 'Table II' · 'Figure E-1' · 'Table 7.3A.1_1.5-1' 같은 꼴이다.

#: 회의록 번호의 단 이음 — 줄표 앞뒤에 빈칸을 두지 않는다. 같은 문단들에서 번호 뒤 빈칸 낀 줄표 4 개는 모두
#: 번호와 제목을 가르는 부호였다('Table 2 - Modulation and code rate table …' · 'Table 1 – Pm-dsg metric …').
#: 빈칸 낀 줄표를 이음으로 받으면 'Table 1 - 4-bit CQI Table for 256 - QAM' 의 번호가 '1 - 4' 가 된다.
_REPORT_JOIN = r"(?:[._]|[-‑–])"
_REPORT_NUM = _number(_REPORT_JOIN)

#: 표 제목. 그룹 1 = 번호, 2 = 제목 글. 번호 뒤 구분 부호(`:` · 줄표 · `.`)는 없어도 된다.
TABLE = re.compile(rf"(?i:table)\s+({_REPORT_NUM})\s*[:\-‑–.]?\s*(.*)", re.S)

#: 그림 제목. 그룹 1 = 번호, 2 = 제목 글. 번호 뒤 `:` 또는 줄표가 있어야 한다.
FIGURE = re.compile(rf"^(?i:figure)\s+({_REPORT_NUM})\s*[:\-‑–]\s*(.*)", re.S)

#: 지역화된 캡션 스타일 이름. RAN1~5 문서(WG 마다 표본 300 + 표본 밖 300)에서 이 세 스타일의 문단 가운데
#: `TDOC_FIGURE` · `TDOC_TABLE` 에 맞는 156 개(RAN1 · RAN2 · RAN4 의 34 문서)는 모두 그림 · 표 캡션이었다.
#: 문법에 맞지 않는 207 개는 제안 · 관찰 줄 50 개, 표 칸 글 153 개, 절 제목 꼴 글 3 개, 본문 문장 1 개였으므로
#: 스타일만으로는 캡션을 가르지 않는다.
#: 156 개 가운데 번호 뒤가 소문자인 6 개도 첫 낱말이 `_TDOC_SENTENCE_WORDS` 에 없어, 이 이름 때문에 판정이
#: 바뀐 문단은 없었다.
_TDOC_CAPTION_STYLES = frozenset({"题注", "標號", "캡션"})


def tdoc_caption_style(style: str, kind: str) -> bool:
    """캡션 스타일인가 — 이름에 'caption' 이 든 스타일('Caption' · 'WW-Caption'), 지역화된 캡션 스타일,
    3GPP 그림 제목 'TF'(kind 'figure') · 표 제목 'TH'(kind 'table')."""
    return ("caption" in style.lower() or style in _TDOC_CAPTION_STYLES
            or (kind == "figure" and style == "TF") or (kind == "table" and style == "TH"))


#: 본문 문장을 잇는 첫 낱말 — 번호 뒤가 소문자 · '&' 이고 첫 낱말이 이 목록에 들면 본문 문장이다.
#: 잰 모집단은 `TDOC_FIGURE` · `TDOC_TABLE` 에 맞고, 번호 뒤가 소문자 · '&' 이며, 캡션 스타일이 아닌 글 문단이다
#: (표 칸 · 글상자 포함, 표 칸 안의 'Table …' 문단은 표 캡션 후보가 아니므로 뺀다).
#: 목록은 RAN1~5 표본(WG 마다 300 문서)의 이 문단 286 개 가운데 본문 문장 267 개의 첫 낱말이다. 나머지 19 개 중
#: 18 개는 소문자로 시작하는 캡션이고('Figure 2 joint work of …' · 'Table 5.2.3.4-1 simulation results for …'),
#: 1 개는 캡션이 아닌 본문 글('Figure A.59 without faders for UE …')로 캡션 판정을 받지만 그 문서의 어느 그림
#: 개체와도 짝지어지지 않는다.
#: 표본 밖 문서(WG 마다 300)에서 같은 꼴의 문단은 305 개다. 첫 낱말이 목록에 든 276 개는 모두 본문 문장이었다.
#: 목록에 없는 29 개 가운데 21 개는 캡션이었고, 8 개는 본문 문장이었다('elaborates' · 'outlines' · 'exhibit' ·
#: 'clearly' · 'of TS 38.211'). 첫 글자만 보는 규칙은 이 21 개를 버린다.
_TDOC_SENTENCE_WORDS = frozenset("""shows defines illustrates lists provides summarizes includes compares describes
is gives depicts define presents indicates contains demonstrates show suggest represents implements reflects also
replaces specifies and for below to not &""".split())
_TDOC_WORD = re.compile(r"[A-Za-z]+|&")


def tdoc_sentence(rest: str) -> bool:
    """번호 뒤 글이 본문 문장을 잇는가 — 빈칸을 건너 첫 글자가 소문자이거나 '&' 이고, 첫 낱말(소문자로 바꾼 것)이
    `_TDOC_SENTENCE_WORDS` 에 든다('Figure 3 shows …' · 'Table 2 and 3 …'). 끝 · 부호 · 대문자 · 숫자로
    이어지거나 첫 낱말이 목록에 없으면 캡션이다('Figure 7 multiple CG PUSCHs …')."""
    r = rest.lstrip()
    if not r or not (r[0].islower() or r[0] == "&"):
        return False
    m = _TDOC_WORD.match(r)
    return bool(m) and m.group(0).lower() in _TDOC_SENTENCE_WORDS


def tdoc_number(kind: str, text: str, style: str) -> str | None:
    """Tdoc 문단이 kind('figure' · 'table') 캡션이면 번호 글(맞은 그대로), 아니면 None.

    번호 뒤가 본문 문장이면(`tdoc_sentence`) 캡션이 아니다. 문단이 캡션 스타일이면(`tdoc_caption_style`)
    문장 꼴이어도 캡션이다. RAN1~5 문서(WG 마다 표본 300 + 표본 밖 300)에서 이 예외로 캡션이 된 문단은 2 개다
    ('Caption' 스타일의 'Table 2 presents the SINR floor …', 'TH' 스타일의 'Table 15.3.12.5-1 defines the primary
    level settings …').
    """
    m = (TDOC_FIGURE if kind == "figure" else TDOC_TABLE).match(text)
    if not m:
        return None
    if tdoc_sentence(m.group("rest")) and not tdoc_caption_style(style, kind):
        return None
    return m.group("num")
