"""Exact extracted helper definitions; this is NOT the full DOCX parser."""
import re

_ATOM = re.compile(r"(?:[^\W_]|[\u0300-\u036f\u20d0-\u20ff′″‴'*∗∞.])+")

_PAIRS = {"(": ")", "[": "]", "{": "}", "⌊": "⌋", "⌈": "⌉", "〈": "〉", "⟨": "⟩", "|": "|", "‖": "‖"}

_BASE_BREAK = re.compile(r"[\s+\-−=<>≤≥≠±·×÷/,;:→←↔⇒∈∉∑∏\u222b]")

_INVISIBLE = str.maketrans("", "", "\u2061\u2062\u2063\u2064")

_OPEN = "\x01"

_OPEN_GAP = re.compile(_OPEN + r"(?=[^\W_])")

def _bracketed(s: str) -> bool:
    """`s` 전체가 한 쌍의 괄호로 감싸였는가 — `(a,b)` 는 참, `(a)(b)` 는 거짓."""
    close = _PAIRS.get(s[:1])
    if close is None or len(s) < 2 or s[-1] != close:
        return False
    if close == s[0]:
        return s.count(close) == 2
    depth = 0
    for i, ch in enumerate(s):
        if ch == s[0]:
            depth += 1
        elif ch == close:
            depth -= 1
            if depth == 0:
                return i == len(s) - 1
    return False

def _open(s: str) -> str:
    """짜임 글이 글자 · 숫자로 끝나면(괄호로 묶지 않은 끝 조각) `_OPEN` 을 붙인다."""
    return s + _OPEN if s[-1:].isalnum() else s

def _grp(s: str) -> str:
    """첨자 · 분자 · 분모 글 — 한 덩어리(`_ATOM`)이거나 이미 괄호로 감싼 글이 아니면 `( )` 로 묶는다."""
    return s if not s or _ATOM.fullmatch(s) or _bracketed(s) else f"({s})"

def _base(s: str) -> str:
    """첨자가 붙는 밑글 — 공백 · 연산 기호가 들고 괄호로 감싸지 않았으면 `( )` 로 묶는다."""
    return f"({s})" if _BASE_BREAK.search(s) and not _bracketed(s) else s

def _seq(parts: list[str], sep: str) -> str:
    """칸 · 줄을 `sep` 로 잇는다. 앞 조각이 이미 `,` · `;` 로 끝나면 한 칸만 띄우고, 뒤 조각이 `,` · `;` 로 시작하면
    그대로 붙인다 — 식과 조건을 칸으로 나눈 자리(38.211 `e^jαn r̅_(u,v)(n),` · `0≤n<M_ZC`, 38.901 τ_n 의 조건 칸
    `,for NLOS`)에서 구분 글자가 겹치지 않게 한다. 끝 · 시작의 빈칸은 건너 보고 잰다(38.521-2 `v_(n,m)=…),` 줄은 쉼표
    뒤에 빈칸 글자를 하나 더 둔다)."""
    out: list[str] = []
    for i, s in enumerate(parts):
        if i:
            out.append(" " if parts[i - 1].rstrip()[-1:] in (",", ";") else "" if s.lstrip()[:1] in (",", ";")
                       else sep)
        out.append(s)
    return "".join(out)
