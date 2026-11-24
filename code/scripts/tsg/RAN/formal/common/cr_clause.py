"""cr_clause.py — CR Cover 의 「Clauses affected」 칸에서 절 번호를 읽는다.

5 WG Phase-4 의 clausesAffected → Section 해소(`RAN{1..4}/phase-4/cr-parser/03_generate_cr_jsonld.py`
와 `RAN5/phase-4/neo4j/01_load_cr_ontology.py`)가 공통으로 쓰는 읽기 규칙이다.

왜 한 자리에 두는가: 이 칸은 사람이 손으로 적는 자유 문자열이라 번호 앞뒤에 말이 붙는다.

    8.14.4 (new) · 4.3(new) · (New) A.3.18      주석
    Section 8.1.2.10 · Sub-clause 5.6 · Annex B  머리말
    New (4.7) · ASN.1 (9.3.4)                   번호가 괄호 안에 있다
    5.4.6 and 6.1.3.9 · 6.2.2 6.3.1             한 칸에 여러 절
    7.1/2/3 · Table 6.2.2.1-2                   앞 번호에 이어 붙인 약식 꼬리
    9.2.x (new) · 20.2.2.y                      아직 번호가 없는 새 절

영숫자와 점만 남기고 나머지를 지우는 정리는 말과 번호를 한 덩어리로 붙인다(`8.14.4new` ·
`Section8.1.2.10` · `5.4.66.1.3.9`). 그런 키는 어떤 절과도 맞지 않아 간선이 조용히 빠지고,
드물게는 붙은 덩어리가 다른 실재 절과 맞아 **다른 절**로 이어진다. 괄호만 떼는 정리는 번호가
괄호 안에 있는 꼴을 잃는다. 그래서 칸을 지우지 않고, 칸에서 절 번호 꼴을 **찾아 읽는다**.

번호 문법은 TS 제목 쪽과 같은 것(`ts_section_number.BODY_NUM` · `ANNEX_NUM`)을 쓴다 — 제목이
세운 절 번호를 이 칸이 다르게 끊으면 해소되지 않는다. 번호 대신 ASN.1 정의명으로 선 절
(38.331 `RadioBearerConfig`)은 이름이 곧 절 번호라 이름도 후보로 낸다.

받지 않는 것:
- 앞 번호에 이어 붙은 꼬리를 맨 정수로 읽은 번호(`7.1/2` 의 `2` · `8.3.1~5` 의 `5` · `#89` · `:3`) — 독립한 절이
  아니라, 맨 정수로 읽으면 1장 · 2장 같은 최상위 절로 이어진다. 빗금 정수 꼬리는 형제 절로 펼쳐 받는다(아래 주의).
- 산문 속 번호 나열의 뒤 항목(`bands 50, 51, 75, 76` 의 `51` · `Table 4-3a, 4-4` 의 `4`) — 쉼표로 나눈 조각은 번호만
  남아 홀로 선 것처럼 보이지만, 같은 줄의 앞 항목 끝 번호가 서지 못했으면 같은 나열이다. 머리말(`Annex C`)로 시작하는
  조각과 줄바꿈 · 쌍반점 뒤의 조각은 새 항목이다. 거꾸로 머리말 꼬리표 뒤의 번호(`RAN4#89: 3` · `New section 8`)는 선다.
- 자리표시 마디(`9.2.x`) — 짧은 쪽으로 끊어 부모 절(`9.2`)로 읽으면 CR 이 고치지 않은 절이 된다.
- 단어 안의 글자(`ASN.1` 의 `N.1`) — 부속서 글자는 앞뒤가 글자가 아닐 때만 번호다.
- TDoc 번호(`R4-2219736`) — 묶음 CR 표지는 칸에 하위 CR 의 TDoc 번호를 줄마다 적는다. 부속서 문법이
  글자 하나와 숫자 꼬리를 받으므로 그대로 두면 `R4` 라는 부속서 절로 읽힌다.
- 규격 인용(`TS 38.133` · `Draft CR to 37.941`) — 하위 CR 제목 줄과 「of TS …」 꼴의 규격 번호는 절이 아니다.
  앞에 그런 말이 없어도(`Draft CR Rel-16 for 38.101-2` · `All 34.123-3 TTCN-3 ATSs`) 3GPP 규격 번호 꼴
  (21 부터 38 까지의 계열, 점, 세 자리)은 절로 읽지 않는다. 그 꼴로 선 TS 절은 다섯 WG 색인에 없다.
- 첨부 파일 이름(`38.521-1_TPanalysis_7.4A.zip`) — 이름 속 번호는 그 칸의 규격 절이 아니다.
- `N/A` — 부속서 `N` 이 아니다(RAN5 38.903 칸의 `N/A (only zip file attachment)`).
- 단위가 붙은 물리량(`3.45-3.55 GHz` · `43.5 GHz`) · 규격 판 번호(`V18.1.0`) · 홀로 선 릴리스 표기(`R17` · `Rel-16` · `Release 15`).
- 대문자 자리표시 마디(`20.2.2.X` · `.Y` · `.Z`)와 새 부속서 자리표시(`Annex X` · `X.1`) — 소문자 `x` 와 같은
  자리표시다. 다섯 WG 색인에 부속서 `X` · `Y` · `Z` 는 없다. 다른 대문자 마디는 받는다(38.213 에 `9.A` 절이 실재한다).
- 지운 글 옆에 남은 낱말(`Adding ‘….zip’` 의 `Adding` · `In R18` 의 `In`) — 홀로 선 이름처럼 보이지만 절 이름이 아니다.
- 절 제목 · 괄호 주석 · 산문의 낱말(`5.5.4.1 General` · `4.4 (New)` · `Second`) — 안쪽 대문자 · 숫자 · 붙임표가 없는
  낱말 하나는 ASN.1 정의 머리 줄(`– Paging`)이나 정의 묶음 제목 뒤 괄호(`Message definitions (Paging)`)에 설 때만 이름이다.

> 주의: 칸을 나누는 쉼표 · 쌍반점에는 전각(`，` · `；` · `、`)도 있다(RAN4 `R4-2312186` 의 `1，2`). 반각만 나누면
> 두 번호가 한 조각에 붙어 어느 번호도 서지 않는다.
>
> 주의: 구분 기호 `/` · `~` · `-` 로 앞 번호에 이어진 번호는 묶음의 일부다. 뒤 번호의 마디 수가 묶음 머리 번호보다
> 적지 않을 때만 독립한 절이다 — `4.2.7.1/4.2.7.2` · `9.1.1.1-9.1.1.6` 의 뒤 번호는 받고, `8.3.1~5` 의
> 꼬리는 절 목록에서 버린다. 머리가 부속서 번호이고 뒤가 숫자로 시작하면(`A.6.5.2/3.1` · `A1/2/3`) 마디 수와 상관없이 꼬리다.
>
> 주의: 점 있는 번호 뒤에 빗금으로 정수만 이어 적은 꼬리(`7.1/2/3` · `8.1.2.4.23/24` · `A.6.5.2/3`)는 머리 번호의 마지막
> 마디만 바꾼 형제 절(`7.2` · `7.3`)을 줄여 적은 것이라 형제 절로 펼쳐 절 목록에 넣는다. 꼬리가 하나라도 점 있는
> 번호이거나 글자가 붙으면(`1/2/3.1` · `A.6.5.2/3.1` · `4.2.2.9/9a`) 펼치지 않고 위 묶음 규칙을 따른다. 머리 번호의
> 마지막 마디가 정수가 아니거나(`6.4A/2`) 머리가 점 없는 번호이면(`A1/2/3`) 펼치지 않는다.
> 물결표 정수 꼬리(`8.3.1~5`)는 범위라서 Phase-8 보존 판정의 `range_clauses` 가 실제 제목 가운데
> 범위 안에 있는 절과 그 하위 절을 남긴다. 붙임표 꼬리는 표 번호(`Table 5.2-1`)와 꼴이 같아 펼치지 않는다.
> 점 없는 번호끼리는 앞보다 뒤 차례일 때만 범위 · 나열이다(`2-11` · `Annex A - C` 는 받고 표 번호 `Table 4-1` 은
> 버린다). 절 목록에는 범위의 가운데 절을 채우지 않는다(Phase-8 보존 판정만 `range_clauses` 로 채운다). 붙임표 바로 뒤의 번호인데 앞이 번호가 아니면(`G-FR1-A4` · `Rel-15`)
> 식별자의 일부다. 붙임표 뒤에 공백을 둔 번호(줄머리 `- 7.1.1.3`)는 홀로 선 번호다. 구분 기호 둘레에 공백을 두고
> 점 있는 번호가 이어지면(`5.5.3.1 / 6.3.6`) 묶음이 아니라 새 항목이다.
>
> 주의: TDoc 번호는 붙임표 둘레 공백(`R4- 2114028`)과 여덟 자리 오타(`R4-42109410`)까지 지운다. 남기면 `R4` 가
> 부속서 절로 읽힌다.
>
> 주의: 부속서 글자 뒤에 점 없이 숫자가 붙은 번호(`A5.5.5.5` · `Annex G2`)는 TS 제목에서는 거의 늘 점이 있는
> 꼴(`A.5.5.5.5`)로 선다. 칸에 적힌 꼴을 먼저 내고 점을 넣은 꼴을 뒤에 낸다. Section 색인이 있는 Phase-4 는 적힌
> 꼴이 실제 절이면 그쪽을 고르고, 색인이 없는 Phase-8 은 마지막 후보인 점 넣은 꼴을 쓴다. 점 없는 꼴로 선 절
> (RAN4 `F10.1`)이 있는 규격을 그런 칸이 가리키면 두 단계가 갈린다.
"""
from __future__ import annotations

import re
from collections.abc import Iterable

from ts_section_number import ANNEX_NUM, BODY_NUM

#: 번호 앞이 이것이면 더 긴 식별자 · 약식 꼬리(`#89` · `:3`)의 일부다. 구분 기호(`/` · `~` · `-`) 뒤의 번호는
#: `_numbers` 가 앞 번호와의 묶음으로 따로 가른다.
_BEFORE = r"(?<![0-9A-Za-z._#:])"
#: 묶음을 잇는 구분 기호.
_JOIN_RE = re.compile(r"\s*[/~\-–]\s*")
#: 번호 뒤에 마디가 더 이어지면(`9.2.x`) 번호의 앞부분만 문 것이다. 탐욕 매치가 짧은 쪽으로
#: 되돌아가도 같은 검사에 걸린다.
_AFTER = r"(?![0-9A-Za-z_]|\.[0-9A-Za-z])"
_NUM_RE = re.compile(rf"{_BEFORE}({BODY_NUM}|{ANNEX_NUM}){_AFTER}")
#: 부속서 글자와 번호 사이의 조판 공백(`A. 16.6.7.1.2` · `B 2.8.2.1`) — 제목 쪽 `normalize` 와 같이 붙인다.
_ANNEX_GAP_RE = re.compile(r"(?<![0-9A-Za-z.])([A-Z])\.?[ \t]+(?=[0-9])")
#: 본문 번호 첫 마디 뒤의 조판 공백(`8. 3.13`). 뒤가 점 있는 번호일 때만 — `1. Scope` 는 제목이다.
_BODY_GAP_RE = re.compile(r"(?<![0-9A-Za-z.])([0-9]+)\.[ \t]+(?=[0-9]+\.[0-9])")
#: 점 있는 번호의 마지막 마디 뒤 조판 공백(`8.1.2.4. 23` · `4.3.1.4.1. 3`). 뒤가 점 없는 정수일 때만 — 뒤가 점 있는
#: 번호이면(`9.2.54. 9.2.58`) 쉼표 대신 찍은 마침표라 새 항목이다. 떼어 읽으면 정수 마디가 최상위 절로 선다.
_LAST_GAP_RE = re.compile(r"(?<![0-9A-Za-z.])([0-9]+(?:\.[0-9]+)+)\.[ \t]+(?=[0-9]+(?![0-9]|\.[0-9]))")
#: 머리말에 붙은 번호(`Clause10` · `AnnexB` · `Annex-A`). 붙임표째 떼지 않으면 `_BEFORE` 가
#: 붙임표 뒤 번호를 더 긴 식별자의 일부로 보고 버린다.
_GLUED_KEYWORD_RE = re.compile(r"\b((?i:sub-?clause|clause|section|annex))-?(?=[0-9A-Z])")
#: 부속서 번호 뒤 붙임표 꼬리(`A.1-1`). 제목 문법이 절 번호로 받는 꼴이지만 칸에서는 범위
#: (`A.5.5.1.1-4`)이기도 해서, 꼬리째 한 번 · 꼬리 없이 한 번 찾는다.
_TAIL_RE = re.compile(r"-[0-9]+[a-zA-Z]?$")
#: ASN.1 정의명으로 선 절(38.331 `– RadioBearerConfig`)은 번호 대신 이름이 절 번호다.
#: ASN.1 형 이름은 대문자로 시작한다(필드 이름 · 주석 낱말 `new` 는 소문자).
_NAME_RE = re.compile(r"(?<![0-9A-Za-z._\-])([A-Z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*)(?![0-9A-Za-z_.\-])")
#: ASN.1 형 이름다운 꼴 — 첫 글자 뒤의 대문자(`RRCSetup` · `SIB`), 숫자(`SIB1`), 붙임표(`PDCP-Config`).
_NAME_SHAPE_RE = re.compile(r".[A-Z]|[0-9]|-")
#: ASN.1 정의를 묶는 절 제목의 끝 낱말(`Message definitions` · `information elements` · `General message structure`
#: · `UE variables` · `System Information Blocks`).
_ASN1_GROUP = r"(?i:definitions|elements|structure|variables|blocks)"
#: 칸 안의 항목 경계.
_PIECE_SPLIT_RE = re.compile(r"[,;\n&，；、]")
#: 항목 경계 가운데 같은 줄의 나열을 잇는 것. 줄바꿈 · 쌍반점은 새 목록을 연다.
_LIST_JOIN = ",&，、"
_PAREN_RE = re.compile(r"\([^()]*\)")
_KEYWORD_RE = re.compile(r"^(?i:sub-?clauses?|clauses?|sections?|annex(?:es)?|chapters?)\b\.?\s*")
#: 번호 하나 또는 번호에서 시작하는 약식 묶음(`2-11` · `1/2/3.1` · `8.3.1~5`).
_NUM_WORD_RE = re.compile(
    rf"(?:{BODY_NUM}|{ANNEX_NUM})(?:\s*[/~\-–]\s*(?:{BODY_NUM}|{ANNEX_NUM}))*[.:]?|and|to")
#: 점 있는 번호 뒤에 빗금으로 이어 적은 정수 꼬리 전체(`7.1/2/3` 의 `/2/3`). 빗금 묶음 안의 꼬리가 하나라도 점 있는
#: 번호이거나 글자가 붙으면(`1/2/3.1` · `4.2.2.9/9a` · `7.1.1.4.1.3/4/7.1.1.4.2.3/4`) 이 꼴이 아니다.
_SLASH_SIBLINGS_RE = re.compile(r"(?:\s*/\s*[0-9]+)+(?!\s*/|[0-9A-Za-z_]|\.[0-9A-Za-z])")
#: 범위의 끝(`2-11` 의 `-11` · `A - C` 의 `- C`). 끝도 번호여야 한다 — `G-FR1-A4` 는 식별자다.
_RANGE_END = rf"\s*[-–~]\s*(?:{BODY_NUM}|{ANNEX_NUM})(?![0-9A-Za-z_\-])"


def _numbers(text: str) -> list[tuple[str, str]]:
    """`text` 에 선 (번호, 묶음 머리 번호). 묶음에 들지 않은 번호는 머리가 자기 자신이다. 구분 기호 뒤의 번호는
    묶음 규칙(모듈 설명의 주의)으로 거른다."""
    out: list[tuple[str, str]] = []
    prev = None  # (끝 자리, 묶음 머리, 바로 앞 번호, 형제 절의 줄기)
    for m in _NUM_RE.finditer(text):
        num, start = m.group(1), m.start(1)
        sep = text[prev[0]:start] if prev is not None else ""
        if prev is not None and _JOIN_RE.fullmatch(sep) and (sep == sep.strip() or _is_weak(num)):
            chain_head, before, stem = prev[1], prev[2], prev[3]
            sibling = stem is not None and sep.strip() == "/" and num.isdigit()
            prev = (m.end(1), chain_head, num, stem if sibling else None)
            if sibling:
                # 빗금 정수 꼬리는 머리 번호의 마지막 마디만 바꾼 형제 절이다(`7.1/2/3` → `7.2` · `7.3`).
                out.append((stem + num, stem + num))
                continue
            if not _joins(chain_head, before, num):
                continue
        elif start > 0 and text[start - 1] in "/~-–":
            # 앞이 번호가 아닌 붙임표(`G-FR1-A4` · `Rel-15`)는 식별자의 일부다.
            prev = None
            continue
        else:
            stem = None
            if "." in num and num.rsplit(".", 1)[1].isdigit() and _SLASH_SIBLINGS_RE.match(text, m.end(1)):
                stem = num.rsplit(".", 1)[0] + "."
            prev = (m.end(1), num, num, stem)
        if _PLACEHOLDER_RE.search(num):
            continue
        out.append((num, prev[1]))
    return out


def _order_key(num: str) -> tuple[int, str] | None:
    """점 없는 번호의 차례 값(`11` → 11, `C` → 글자). 견줄 수 없는 꼴이면 None."""
    if num.isdigit():
        return (int(num), "")
    if len(num) == 1 and num.isalpha():
        return (0, num)
    return None


def _joins(chain_head: str, before: str, num: str) -> bool:
    """묶음의 뒤 번호가 독립한 절인가 — 약식 꼬리(`7.1/2` · `A.6.5.2/3.1` · `A1/2`)와 표 번호(`Table 4-1`)가
    아닌가. 머리가 부속서이고 뒤가 숫자로 시작하면 부속서 번호의 꼬리다. 점 없는 번호는 머리와 앞 번호도 점 없는 번호이고
    앞 번호보다 뒤 차례일 때만 범위 · 나열이다(`2-11` · `A - C`). 그 밖에는 마디 수가 머리 번호보다 적지 않아야 한다."""
    if chain_head[0].isalpha() and num[0].isdigit():
        return False
    if _is_weak(num):
        if not (_is_weak(chain_head) and _is_weak(before)):
            return False
        a, b = _order_key(before), _order_key(num)
        return a is not None and b is not None and a[1].isalpha() == b[1].isalpha() and a < b
    return num.count(".") >= chain_head.count(".")


def _is_weak(num: str) -> bool:
    """점이 없는 번호(`8` · `10A` · 부속서 글자 `C`). 산문 속 숫자 · 글자와 모양이 같다."""
    return "." not in num


def _item_core(piece: str) -> str:
    """항목에서 주석 괄호와 머리말(`Subclause` · `Annex`)을 뗀 몸."""
    return _KEYWORD_RE.sub("", _PAREN_RE.sub(" ", piece).strip()).strip()


#: 항목 가운데의 머리말(`New section 8` · `New section Annex B`). 그 뒤가 항목의 몸이다.
_MID_KEYWORD_RE = re.compile(r"\b(?i:sub-?clauses?|clauses?|sections?|annex(?:es)?|chapters?)\b\.?\s*")


def _lead_in_rests(core: str) -> list[str]:
    """머리말 꼬리표 뒤의 몸 — 마지막 쌍점 뒤(`RAN4#89: 3` · `New clauses introduced to specification: 3`)와
    마지막 머리말 낱말 뒤(`New section 8`). 꼬리표의 낱말은 절 제목이 아니라 그 뒤 번호를 소개하는 말이다."""
    rests = []
    colon = core.rfind(":")
    if colon >= 0:
        rests.append(_item_core(core[colon + 1:]))
    keywords = list(_MID_KEYWORD_RE.finditer(core))
    if keywords and keywords[-1].start() > 0:
        rests.append(core[keywords[-1].end():].strip())
    return [r for r in rests if r]


def _weak_number_stands(num: str, core: str) -> bool:
    """점 없는 번호가 항목 자리에 섰는가. 머리말 꼬리표(`_lead_in_rests`) 뒤의 몸이 그런 꼴이어도 선다.
    """
    return any(_weak_number_heads(num, c) for c in [core, *_lead_in_rests(core)])


def _weak_number_heads(num: str, core: str) -> bool:
    """점 없는 번호가 항목 자리에 섰는가.

    번호만 늘어선 항목(`6.2.2 16` · `2-11` · `3.3 and 9`)이거나, 항목 첫머리의 번호 뒤에 제목
    · 범위 끝 · `and` 가 오는 꼴(`3 Definitions` · `1.    Scope` · `8 and subsequent …`)일 때만
    절 번호다. 제목 · 괄호 주석 · 산문 속의 숫자와 글자(`(Bullet 1.)` · `format 0 and 1` ·
    `G-FR1-A4-29A`)는 받지 않는다.
    """
    words = core.split()
    if words and all(_NUM_WORD_RE.fullmatch(w) for w in words):
        return num in (n for n, _ in _numbers(core))
    m = re.match(rf"({re.escape(num)})(?:\.?\s+[A-Z]|{_RANGE_END}|\s+and\b|\.?$)", core)
    return bool(m)


def _name_stands(name: str, piece: str) -> bool:
    """이름이 항목 자리에 섰는가 — 항목 전체이거나 번호 · 구분 기호 뒤에 홀로 올 때.

    제목 속 이름(`Reception of RRCSetup by the UE`)은 그 절이 다루는 메시지를 말할 뿐,
    메시지 정의 절을 고친다는 뜻이 아니다.

    안쪽 대문자 · 숫자 · 붙임표가 없는 낱말 하나(`General` · `New` · `Second`)는 절 제목 · 주석 · 산문의
    낱말과 모양이 같다. 그런 이름은 ASN.1 정의 머리 줄 꼴(`– Paging` · `6.3.2 – Paging`)이거나, ASN.1 정의를 묶는
    절 제목 뒤 괄호(`6.2.2 Message definitions (Paging)`)에 설 때만 받는다.
    """
    if not _NAME_SHAPE_RE.search(name):
        return bool(re.fullmatch(
            rf"\s*(?:(?:{BODY_NUM}|{ANNEX_NUM})(?![0-9A-Za-z_\-])\.?\s*)?[–-]\s*{re.escape(name)}\s*", piece)
            or re.search(rf"{_ASN1_GROUP}\s*\(\s*{re.escape(name)}\s*\)?\s*$", piece))
    rest = re.sub(rf"^(?:{BODY_NUM}|{ANNEX_NUM})(?![0-9A-Za-z_\-])\.?\s*", "", piece.strip())
    rest = rest.strip(" \t–-:()'\"")
    if rest == name:
        return True
    return bool(re.search(rf"(?:\s[–-]|[:(])\s*{re.escape(name)}\s*\)?\s*$", piece))


#: TDoc 번호. 부속서 문법(`R4` + 꼬리 `-2219736`)으로 읽히지 않도록 칸에서 먼저 지운다. 뒤에 붙은 쌍점도
#: 함께 지운다(`R4-1902067: 7`). 남기면 조각에 번호 아닌 말이 생겨 맨 정수 절(`7`)이 서지 못한다.
_TDOC_RE = re.compile(r"(?<![0-9A-Za-z])(?:R[1-5P]|RP|S[1-6P]|SP|C[1-6P]|CP)\s*-\s*[0-9]{5,8}(?![0-9])(?:\s*:)?")
#: 규격 인용(`TS 38.133` · `CR to 37.941`). 규격 번호는 두 자리 · 세 자리 마디이고 앞에 규격을 가리키는 말이 온다.
_SPEC_REF_RE = re.compile(r"\b(?i:TS|TR|to|CR)\s*[0-9]{2}\.[0-9]{3}(?:-[0-9]+)*(?![0-9A-Za-z]|\.[0-9])")
#: 앞에 규격을 가리키는 말이 없는 규격 번호(`for 38.101-2`). 3GPP 규격 계열(21 부터 38)과 세 자리 마디.
_BARE_SPEC_RE = re.compile(r"(?<![0-9A-Za-z.])(?:2[1-9]|3[0-8])\.[0-9]{3}(?:-[0-9]+)*(?![0-9A-Za-z]|\.[0-9])")
#: 첨부 파일 이름 — 따옴표로 묶이고 밑줄이나 `.zip` 을 담은 이름(공백이 든 `‘38.521-2_TP analysis_6.3.1_MinOP’`),
#: 파일 확장자로 끝나는 토막, 규격 번호에 밑줄로 이어 붙은 토막. 밑줄 식별자(`f_EUTRA38_508_…`)는 지우지 않는다 —
#: 지우면 앞 낱말(`Function`)이 홀로 남아 이름 후보가 된다.
_FILENAME_RE = re.compile(
    r"[‘’“”\"'][^‘’“”\"'\n]*?(?:_|\.(?i:zip))[^‘’“”\"'\n]*?[‘’“”\"']"
    r"|[^\s,;，；、]*\.(?i:zip|docx?|xlsx?|pptx?)(?![0-9A-Za-z])"
    r"|(?<![0-9A-Za-z.])(?:2[1-9]|3[0-8])\.[0-9]{3}(?:-[0-9]+)*_[^\s,;，；、]*")
_NOT_APPLICABLE_RE = re.compile(r"(?<![0-9A-Za-z])(?i:n/a)(?![0-9A-Za-z])")
#: 단위가 붙은 물리량(`3.45-3.55 GHz` · `43.5 GHz` · `-10 dBm`).
_QUANTITY_RE = re.compile(
    r"(?<![0-9A-Za-z.])[0-9]+(?:\.[0-9]+)?(?:\s*[-–~]\s*[0-9]+(?:\.[0-9]+)?)?\s*(?:[kMGT]Hz|dBm?|dBc|ms|μs)(?![0-9A-Za-z])")
#: 규격 판 번호(`V18.1.0` · `v.16.3.0`).
_VERSION_RE = re.compile(r"(?<![0-9A-Za-z.])[Vv]\.?\s?[0-9]+\.[0-9]+\.[0-9]+(?![0-9A-Za-z]|\.[0-9])")
#: 홀로 선 릴리스 표기(`R17` · `Rel-16` · `Release 15`). 약칭은 부속서 문법이 `R` 과 숫자 꼬리로 받고(RAN5 의
#: 부속서 `R` 절은 `R.3` 까지다), 긴 꼴은 붙임표 · 숫자가 있어 이름 꼴로 받는다.
_RELEASE_RE = re.compile(
    r"(?<![0-9A-Za-z._\-])(?:R|(?i:rel)(?:-|\.\s?|\s)?|(?i:release)\s?-?)(?:[89]|1[0-9])(?![0-9A-Za-z_.\-])")
#: 대문자 자리표시 마디(`20.2.2.X` · `X.1`). 규격에 부속서 `X` · `Y` · `Z` 는 없다.
_PLACEHOLDER_RE = re.compile(r"\.[XYZ]$|^[XYZ](?:\.|$)")
#: 절 번호 뒤에 점으로 붙은 망 · 시스템 한정어(`7.1.1.2.3.NR5GC` · `7.1.1.1.1a.ENDC` · `A.4.3.2.MCPTT`). 시험 사례 절이
#: 어느 망 설정의 사본인지 적은 꼬리이고, 고치는 절은 머리 번호다. 대문자로 시작하고 서로 다른 글자가 둘 이상인
#: 낱말만 한정어로 본다 — 자리표시 마디(`.x` · `.xx` · `.YY` · `.AA` · `.x1` · `.X2A`)는 소문자 · 같은 글자 되풀이 ·
#: `X`·`Y`·`Z` 머리라서 걸리지 않고, 그대로 남아 `_AFTER` 가 앞 번호째 버린다.
_QUALIFIER_TAIL_RE = re.compile(
    rf"{_BEFORE}((?:{BODY_NUM}|{ANNEX_NUM}))\.((?![XYZ])[A-Z][0-9A-Za-z]*)(?![0-9A-Za-z_]|\.[0-9A-Za-z])")
#: 칸에서 지운 자리. 번호는 공백으로 읽고, 이름은 지운 글 옆에 홀로 선 것으로 보지 않는다(`Adding ‘….zip’` 의 `Adding`).
_GONE = "\x01"
#: 부속서 글자 바로 뒤에 숫자가 붙은 번호(`A5.5.5.5`).
_GLUED_ANNEX_RE = re.compile(r"^([A-Z])(?=[0-9])")


def _drop_qualifier_tail(m: re.Match) -> str:
    """한정어 꼬리를 지운 머리 번호. 한정어가 아니면 그대로 둔다."""
    if len({ch.lower() for ch in m.group(2) if ch.isalpha()}) < 2:
        return m.group(0)
    return m.group(1) + _GONE


def _prepared(cell: str) -> str:
    """칸에서 절 번호가 아닌 번호 꼴(파일 이름 · TDoc 번호 · 규격 인용 · 물리량 · 판 번호 · 릴리스)을 지우고 조판 공백을 붙인 글."""
    text = _FILENAME_RE.sub(_GONE, cell)
    text = _SPEC_REF_RE.sub(_GONE, _TDOC_RE.sub(_GONE, text))
    for strip in (_BARE_SPEC_RE, _NOT_APPLICABLE_RE, _QUANTITY_RE, _VERSION_RE, _RELEASE_RE):
        text = strip.sub(_GONE, text)
    text = _GLUED_KEYWORD_RE.sub(r"\1 ", text)
    text = _BODY_GAP_RE.sub(r"\1.", _ANNEX_GAP_RE.sub(r"\1.", text))
    text = _LAST_GAP_RE.sub(r"\1.", text)
    return _QUALIFIER_TAIL_RE.sub(_drop_qualifier_tail, text)


#: 자리표시 마디로 끝나는 새 절 번호(`8.7.X` · `9.2.x` · `5.3.xx`). 앞 무리가 부모 절이다.
_NEW_CLAUSE_RE = re.compile(rf"{_BEFORE}(?:{BODY_NUM}|{ANNEX_NUM})\.[XYZxyz][0-9A-Za-z]*(?![0-9A-Za-z_])")


def placeholder_clauses(cell: str | None) -> list[str]:
    """칸에 적힌 자리표시 새 절 번호를 적힌 꼴 그대로(`8.7.X`). 절 목록(`clause_candidates`)에는 들지 않는다.

    > 주의: Phase-8 청크가 바꾸지 않은 절을 뺄 때(`cr_revision_marks.changed_sections`)만 쓴다. 새 절을 넣는 CR 은 본문에
    > 새 절이 들어갈 자리의 위 절 제목(`8.7 Procedures for E-UTRAN-NR Dual Connectivity`)을 표시 없이 옮겨 적는다. 자리표시
    > 번호를 보존 판정의 표지 절로 넘기면 `declared` 가 그 위 절들을 남겨 새 절의 자리가 청크 글에 남는다. KG 의
    > clausesAffected 에 넣으면 CR 이 고치지 않은 부모 절로 간선이 서므로 넣지 않는다.
    """
    if not cell:
        return []
    out = [m.group(0) for piece in _PIECE_SPLIT_RE.split(_prepared(cell))
           for m in _NEW_CLAUSE_RE.finditer(piece.replace(_GONE, " "))]
    return list(dict.fromkeys(out))


#: 범위의 약식 꼬리를 잇는 물결표. 붙임표 꼬리는 표 번호(`Table 5.2-1`)와 꼴이 같아 받지 않는다.
_TILDE = ("~", "～", "〜")
#: 범위를 잇는 구분(`2-11` · `A - C` · `1~6` · `5.1 to 5.4`). 나열 구분 `/` 는 범위가 아니다.
_RANGE_SEP_RE = re.compile(r"\s*[-–~]\s*|\s+to\s+")


def _in_range(candidate: str, a: str, b: str, include_end: bool) -> bool:
    """같은 부모의 정수·부속서 번호 범위에 후보가 있는지 숫자 간격을 생성하지 않고 검사한다."""
    pa, pb, pc = a.split("."), b.split("."), candidate.split(".")
    if len(pa) != len(pb) or len(pa) != len(pc) or pa[:-1] != pb[:-1] or pa[:-1] != pc[:-1]:
        return False
    x, y, z = pa[-1], pb[-1], pc[-1]
    if x.isdigit() and y.isdigit() and z.isdigit():
        # 기존 정수 범위는 선행 0이 없는 번호를 생성했다. 숫자는 길이·문자열로 비교하여
        # 끝점의 자릿수가 커져도 거대 정수나 범위 목록을 만들지 않는다.
        canonical = lambda value: value.lstrip("0") or "0"
        if z != canonical(z):
            return False
        x, y, z = ((len(v), v) for v in map(canonical, (x, y, z)))
    elif not (len(x) == len(y) == len(z) == 1 and x.isupper() and y.isupper() and z.isupper()):
        return False
    return x < z and (z <= y if include_end else z < y)


def range_clauses(cell: str | None, section_numbers: Iterable[str]) -> list[str]:
    """표지 범위 안에 있는 실제 제목 번호와 그 부모 번호를 Phase-8 보존 판정에 돌려준다.

    `section_numbers`는 현재 CR에서 읽은 제목 번호다. 그 번호와 유한한 부모 번호만 검사하므로
    `2-1000000000`처럼 큰 끝점도 숫자 사이를 전개하지 않는다. 실제 절을 임의 개수로 자르지 않는다.
    상하위 절의 보존은 `cr_revision_marks.declared`의 점 구분 prefix 규칙을 그대로 쓴다.

    양 끝이 `clause_candidates`에서 절로 인정된 범위만 받는다. 양 끝은 호출자가 별도로 전달하고,
    물결표 정수 꼬리(`8.3.1~5`)만 끝 번호까지 검사한다. 붙임표 꼬리(`5.2-1`)는 표 번호와
    구별할 수 없어 추가 범위를 만들지 않는다. 이 결과는 KG의 `clausesAffected`에 넣지 않는다.
    """
    if not cell:
        return []
    stood = {spellings[0] for spellings in clause_candidates(cell)}
    ranges: list[tuple[str, str, bool]] = []
    for marked in _PIECE_SPLIT_RE.split(_prepared(cell)):
        piece = marked.replace(_GONE, " ")
        prev = None
        for m in _NUM_RE.finditer(piece):
            num = m.group(1)
            sep = piece[prev.end(1):m.start(1)] if prev is not None else ""
            if prev is not None and _RANGE_SEP_RE.fullmatch(sep) \
                    and prev.group(1) in stood and num in stood:
                ranges.append((prev.group(1), num, False))
            elif prev is not None and sep.strip() in _TILDE and prev.group(1) in stood and num.isdigit():
                # 물결표 정수 꼬리(`8.3.1~5`)는 머리 번호의 마지막 마디부터 그 정수까지의 범위다.
                head = prev.group(1)
                stem, last = (head.rsplit(".", 1) + [""])[:2] if "." in head else ("", "")
                if last.isdigit():
                    ranges.append((head, f"{stem}.{num}", True))
            prev = m
    out: list[str] = []
    checked: set[str] = set()
    for number in section_numbers:
        candidate = number
        while candidate:
            if candidate not in checked:
                checked.add(candidate)
                if candidate not in stood and any(_in_range(candidate, a, b, end) for a, b, end in ranges):
                    out.append(candidate)
            candidate = candidate.rpartition(".")[0]
    return out


def clause_candidates(cell: str | None) -> list[tuple[str, ...]]:
    """「Clauses affected」 칸이 가리키는 절들. 절마다 찾아볼 번호를 앞선 차례로 담는다.

    호출자는 절마다 후보를 차례로 찾아 처음 걸린 것 하나만 잇는다. 이름 후보는 이름으로 선
    절이 있는 규격에서만 걸린다.
    """
    if not cell:
        return []
    out: list[tuple[str, ...]] = []
    parts = re.split(f"({_PIECE_SPLIT_RE.pattern})", _prepared(cell))
    #: 앞 항목의 마지막 번호가 섰는가. 쉼표로 이어진 항목만 잇는다.
    last_stood: bool | None = None
    for i in range(0, len(parts), 2):
        marked = parts[i]
        piece = marked.replace(_GONE, " ")
        inherited = last_stood if i and parts[i - 1] in _LIST_JOIN else None
        last_stood = None
        if not piece.strip():
            continue
        core = _item_core(piece)
        # 산문 속 번호 나열(`bands 50, 51, 75, 76` · `Table 4-3a, 4-4`)의 뒤 항목은 번호만 남아 홀로 선 것처럼
        # 보인다. 앞 항목의 마지막 번호가 서지 못했고 이 항목에 머리말이 없으면 같은 나열로 보고 받지 않는다.
        in_prose_list = inherited is False and not _KEYWORD_RE.match(_PAREN_RE.sub(" ", piece).strip())
        stood: set[str] = set()
        for num, chain_head in _numbers(piece):
            # 묶음 끝의 점 없는 번호(`A - C` 의 `C`)는 머리 번호가 섰으면 선다.
            if _is_weak(num) and (in_prose_list
                                  or not (chain_head in stood or _weak_number_stands(num, core))):
                last_stood = False
                continue
            last_stood = True
            head = _TAIL_RE.sub("", num) if num[0].isalpha() else num
            spellings = (num, head)
            if _GLUED_ANNEX_RE.match(num):
                spellings += tuple(_GLUED_ANNEX_RE.sub(r"\1.", x) for x in spellings)
            stood.add(num)
            out.append(tuple(dict.fromkeys(spellings)))
        for name in _NAME_RE.findall(piece):
            if not _NUM_RE.fullmatch(name) and _name_stands(name, marked):
                out.append((name,))
    return list(dict.fromkeys(out))
