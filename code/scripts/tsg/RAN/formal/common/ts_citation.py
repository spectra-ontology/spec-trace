"""TS 본문의 절 인용에서 대상 문서와 절 번호를 추출한다.

5 WG TS 파서(`RAN{1..5}/phase-3/ts-parser/parse_ts_docx.py`)의 `extract_references` 가
공통으로 사용하는 규칙이다. 같은 TS의 절은 현재 specNumber로, 다른 TS의 절은
인용에서 추출한 specNumber로 구분한다. 대상 결정 기준은 각 WG Phase-3 설계서의 참조 패턴 절이다.

`clause N`만으로는 대상 문서를 결정할 수 없다. 문서명과 절 번호가 다음처럼
여러 순서로 나타나므로, 다른 문서를 가리키는 인용부터 구분한다.

    TS 38.521-1 [8] clause 5.3        문서가 앞, 참고문헌 번호가 사이에 낀다
    [2, TS 38.211], clause 4.3        참고문헌 괄호 안에 문서
    clause 5.3 of TS 38.521-1 [8]     문서가 뒤
    clause 5.3 in [2, TS 38.211]
    clause 5.3 of [8]                 참고문헌 번호만 — 문서는 References 절이 정한다
    [8] clause 5.3
    clause 5.3 [8]                    참고문헌 번호가 절 번호 바로 뒤에 붙는다

문서명은 `TS 38.521-1` 형식 외에도 계열을 붙여 쓰거나(`TS38.133`) 계열 없이 번호만
적거나(`38.212 [27] clause 7.3.1.1.4`), 3GPP 밖 문서(`clause 3.3 of IETF RFC 5448 [31]`)일 수 있다.
일부 형식만 구분하면 다른 문서의 절을 현재 문서의 같은 번호 절로 잘못 연결할 수 있다.
따라서 다른 문서를 가리키는 인용을 먼저 분리하고, 남은 본문에서 현재 문서의 절을 추출한다.

절 번호 문법은 글자 접미사, 변형 절 접미사, 마지막 글자 마디를 포함한다(`5.3B.1.2` · `5.1.4a` · `A.2` ·
`6.2.2_1.3` · `9.A`).
숫자만 허용하면 `5.3B.1.2`를 `5.3`으로, `6.2.2_1.3`을 `6.2.2`로 잘라 다른 절에 연결할 수 있다.
제목과 같은 마디 문법(`ts_section_number.SEG`)을 사용해 이를 방지한다. 끝에 `\\b`를 두면
접미사를 포함한 매치가 실패한 뒤 더 짧은 번호로 되돌아갈 수 있다. 대신 번호 끝 경계(`_END`)로
뒤에 영숫자가 이어지는 매치를 거절한다. `5.3Bx`·`5.3B1x`처럼 허용하지 않는 토큰도 나열의
일부로 읽되 절 번호로 반환하지 않아, 뒤쪽 번호와 대상 문서의 연결을 유지한다.

번호 하나가 아니라 나열 전체가 한 문서를 가리킨다. 이음말(쉼표 뒤 `and` · 빗금 · 범위 대시 ·
`through`)을 하나라도 놓치면 나열이 거기서 끊겨 뒤쪽 `of TS X` 가 앞 번호에 닿지 않고, 앞 번호가
자기 문서 절로 읽힌다. 범위는 사이의 절까지 펴고, 표 · 그림 번호 꼬리(`4.2-1`)는 그 표가 실린 절로
해소한다. 복수 머리말(`clauses 5, 6 and 7`)도 자기 문서 절로 읽는다. 문서와 머리말 사이에는 쉼표나 여는 괄호가
낄 수 있다(`TS 38.213 [13] (clauses 9 and 10)`).

주의: 번호와 `of/in 문서` 사이에는 괄호 속 절 제목과 표 번호만 낄 수 있다. 그보다 긴 수식어가 끼면
(`clause 6.5.1 for BS type 1-H in TS 38.104`) 문서가 번호에 닿지 않아 자기 문서 절로 읽힌다. 수식어 끝의
문서가 번호를 가리키는지 수식어 안의 명사를 가리키는지(`clause 4.5.2.3) DL RSTD measurements, defined in
TS 38.215` 의 4.5.2.3 은 자기 문서 절이다) 글자만으로는 가려지지 않으므로 수식어를 건너뛰지 않는다.
주의: 정규식의 각 분기에서 공백·연결 표현을 중복 매치하지 않는다. 같은 공백을 여러 패턴이
나눠 매치하면, 긴 나열의 매치 실패 시 백트래킹이 급증할 수 있다(`_CONJ`·`_OF` 주석 참조).
"""
from __future__ import annotations

import re

from ts_section_number import SEG

#: 절 번호의 한 마디. 둘째 글자가 이어지면(`5.3Bx`) 번호가 아니다.
_SEG = rf"(?:{SEG})(?![A-Za-z])"
#: 자기 문서 절 번호. 첫 마디가 글자이면(`A.2`) 부속서 절이라 뒤에 마디가 반드시 온다.
#: 번호 뒤 대시 꼬리(`4.2-1` · `A.3.3.2-1`). 표 · 그림 번호(`clause 4.2-1 of TS 38.211` 은 표 4.2-1 이
#: 실린 절을 가리킨다)이거나 꼬리까지가 제목인 부속서 절(`A.3.3.2-1`)이다. 꼬리를 물지 않으면 `of TS X`
#: 가 번호에 닿지 않아 다른 문서 인용이 자기 문서의 `4.2` 로 읽힌다. 꼬리 뒤에 `.숫자` 가 오면 꼬리가
#: 아니라 범위(`6.3A.3.3.2-6.3A.3.3.5`)이므로 받지 않는다.
_TAIL = r"(?:-[0-9]+[a-zA-Z]?(?![0-9A-Za-z]|\.[0-9]))"
#: 끝 마디가 대문자 하나인 번호(`9.A`). 제목 쪽 문법(`ts_section_number.BODY_NUM`)이 이 꼴의 절을 세우므로
#: 인용 쪽도 받는다(TS 38.213 의 `9.A` 는 PUCCH cell switching 절이다).
#: 주의: 이 마디를 받지 않으면 `TS 38.213 [13], clause 9.A, clause 9.1.5` 의 사슬이 `9` 에서 끊겨
#: 뒤쪽 `clause 9.1.5` 가 자기 문서의 9.1.5 로 읽힌다. 문장 끝 마침표(`clause 9.A.`)는 막지 않는다.
_LETTER = r"(?:\.[A-Z](?![A-Za-z0-9]|\.(?![A-Z][a-z])[0-9A-Za-z]))"
#: 번호 끝의 토큰 경계. 번호 문법이 거절한 토큰(`5.3Bx` · `5.3B1x`)을 짧은 앞 마디(`5` · `5.3B`)로 되돌려
#: 읽지 않는다 — 매치 바로 뒤가 영숫자이면 매치를 버린다. 앞 마디로 되돌아가면 없는 절이 아니라 다른 절
#: (`5`)로 간선이 생긴다. 문장 끝 마침표(`clause 5.3.`)와 마침표 뒤에 띄어쓰기 없이 대문자 낱말이 붙은
#: 자리(`clause 5.2.1.The UE`)는 문장 끝이라 막지 않는다. 절 번호의 마디는 대문자 뒤에 소문자가 오지
#: 않으므로(`_LETTER`) 그 자리에서 번호가 끝난다.
_END = r"(?![0-9A-Za-z_]|\.(?![A-Z][a-z])[0-9A-Za-z_])"
CLAUSE_NUM = rf"(?:{_SEG}|[A-Z](?=\.\d))(?:\.{_SEG})*{_LETTER}?{_TAIL}?{_END}"
#: 부속서 번호. `Annex A` 처럼 글자 하나로도 선다.
ANNEX_NUM = rf"[A-Z](?![A-Za-z])(?:\.{_SEG})*{_TAIL}?{_END}"
#: 다른 문서를 가리킬 때의 번호. 문서가 함께 적혀 있으니 부속서 글자 하나도 받는다.
_XNUM = rf"(?:{_SEG}|[A-Z](?![A-Za-z]))(?:\.{_SEG})*{_LETTER}?{_TAIL}?{_END}"
#: 나열의 이음말. 쉼표 뒤 `and`/`or`(`6.2.1, 6.2A.1, and 6.2D.1`) · 빗금(`7.5.2/7.6.2`) · 범위
#: (`6.3A.3.3.2-6.3A.3.3.5` · `4 through 6` · `5.1 to 5.4`)도 나열을 잇는다. 이음말을 하나라도 놓치면
#: 나열이 거기서 끊겨 뒤쪽 `of TS X` 가 앞 번호에 닿지 않고, 앞 번호가 자기 문서 절로 읽힌다.
#: 주의: 이음말 앞뒤 공백을 갈래마다 한 자리에서만 문다. `\s*(?:,|and)\s*` 처럼 앞뒤 둘 다에 공백을
#: 두면 공백을 어느 쪽이 물지 갈래가 둘로 갈려, 나열이 길고 뒤에 문서가 없어 매치가 실패할 때 이음말마다
#: 갈래가 두 배로 늘어난다(`ts_section_number.SEG` 의 주의와 같은 결함이다).
_CONJ = r"(?:\s*,\s*(?:(?:and|or)\s+)?|\s*[/\-\u2013]\s*|\s+(?:and|or|to|through)\s+)"
#: 범위 이음말. 범위는 두 끝만이 아니라 사이의 절까지 가리킨다(`_numbers`).
_RANGE = re.compile(r"\s*(?:[-\u2013]|to|through)\s*")
_TAIL_END = re.compile(rf"{_TAIL}$")
_LETTER_END = re.compile(rf"{_LETTER}$")
#: 번호 나열(`clauses 5.1 and 5.2`, `clause 5.1, 5.3 or 5.4`). 나열 전체가 한 문서를 가리킨다.
#: 문서가 뒤에 오는 꼴은 `of TS X` 가 나열을 닫으므로 머리말을 되풀이한 나열(`clause 5.1 and
#: clause 5.2 of TS X`)까지 받는다. 문서가 앞에 오는 꼴(`TS X clause 5.1 and clause 5.2`)은 닫는
#: 자리가 없어 뒤쪽 `clause` 가 자기 문서로 돌아온 것인지 가릴 수 없으므로, 머리말 없는 나열만 받는다.
#: 나열 안의 거절 토큰(`5.3Bx`). 다른 문서 나열이 거기서 끊기지 않게 물기만 하고 번호로는 내지 않는다
#: (`_numbers` 는 `_END` 를 지키는 번호만 읽는다). 끊기면 `clauses 5.1 and 5.3Bx of TS X` 의 5.1 이 자기 문서
#: 절로 읽힌다. 나열의 한 자리에서 서는 갈래는 하나뿐이다. 번호는 꼬리(`-1`)를 물 수 있으면 반드시 물고,
#: 거절 토큰은 번호가 서지 않는 자리에서만 토큰 끝까지 문 꼴로 선다. 꼬리를 물지 않는 갈래를 남기면
#: `A.1-1` 이 `A.1` · `-` · `1` 로도 읽혀, 나열이 길고 뒤에 문서가 없어 매치가 실패할 때 그런 토큰마다
#: 갈래가 두 배로 늘어난다.
#: 주의: 원자 묶음(`(?>…)`)으로 같은 일을 하면 Python 3.10 의 `re` 가 컴파일하지 못해 이 모듈을 들여오는
#: 파서 다섯 벌이 모두 멈춘다(pyproject 의 requires-python 은 3.10 부터다).
_REJ = r"(?<![0-9A-Za-z_.])(?:[0-9]|[A-Z](?=[0-9.]))[0-9A-Za-z_]*(?:\.[0-9A-Za-z_]+)*(?![0-9A-Za-z_]|\.[0-9A-Za-z_])"
_XNUM_FIRST = (rf"(?:{_SEG}|[A-Z](?![A-Za-z]))(?:\.{_SEG})*{_LETTER}?"
               rf"(?:{_TAIL}{_END}|(?!{_TAIL}{_END}){_END})")
_XTOK = rf"(?:{_XNUM_FIRST}|(?!{_XNUM}){_REJ})"
_XLIST_HEAD = rf"{_XTOK}(?:{_CONJ}{_XTOK})*"
_XLIST = rf"{_XTOK}(?:{_CONJ}(?:(?i:(?:sub)?clauses?)\s+)?{_XTOK})*"
#: 문서 번호. 계열(`TS`/`TR`)과 파트 번호(`-1`)까지 문다 — 파트를 잃으면 서로 다른 규격이
#: 하나로 뭉쳐 다른 문서를 가리키게 된다. 계열 뒤를 붙여 쓴 표기(`TS38.133`)와 계열 없이 번호만
#: 적은 표기(`38.212 [27] clause 7.3.1.1.4` · `Derivation Path: 24.501 clause 8.2.1` ·
#: `Annex F in 38.521-2`)도 문서다. 계열 없는 번호는 3GPP 규격 계열 번호로 시작할 때만 문서로
#: 읽는다 — 값(`10.000`)이나 다른 번호의 꼬리(`5.38.212`)를 문서로 읽지 않게 하려는 것이다.
#: 끝의 부정 전방 탐색은 번호가 더 이어지는 자리(`38.2111` · `38.212.1`)를 문서로 끊지 않게 하고,
#: 문장 끝 마침표(`TS 38.211.`)는 막지 않는다.
_SERIES = r"(?:2[1-9]|3[0-8]|4[1-9]|5[0-5])"
_DOC = (rf"(?:3GPP\s+)?(?:T[SR]\s*|(?<![\w.])(?={_SERIES}\.))"
        r"(\d{2}\.\d{3}(?:-\d+)*)(?!\d|\.\d|-\d)")
#: 3GPP 밖 문서(IETF RFC · ITU · IEEE · ETSI · ISO). 범위 안 specNumber 가 아니니 그 절 인용은
#: 간선이 되지 않지만, 떼어 내지 않으면 `clause 3.3 of IETF RFC 5448 [31]` 의 `clause 3.3` 이
#: 자기 문서의 3.3 으로 읽힌다.
_FOREIGN = (r"(?:(?:IETF\s+)?RFC\s*\d+"
            r"|ITU-[TR]\s+(?:Recommendation\s+)?[A-Z]\.\d+(?:\.\d+)*"
            r"|IEEE\s+(?:Std\.?\s+)?\d+(?:\.\d+[a-z]*)*"
            r"|ETSI\s+(?:TS|EN|ES|TR|EG)\s+\d{3}\s+\d{3}(?:-\d+)*"
            r"|ISO(?:/IEC)?\s+\d+(?:-\d+)*)")
#: 인용 머리말. 대소문자를 가리지 않는다 — 떼어 내는 쪽은 넓게 물어야 남는 본문이 깨끗하다.
_KW = r"(?i:(?:sub)?clauses?|sections?|annex(?:es)?)"
#: 주의: 쉼표 뒤 공백과 `of` 앞 공백을 한 갈래로 문다(`_CONJ` 의 주의와 같은 까닭).
_OF = r"(?:\s*,)?\s+(?i:of|in)\s+"
#: 번호와 `of/in 문서` 사이에 끼는 것. 괄호 속 절 제목(`clause 5.3.2.1 (E-UTRAN Initial Attach) in TS
#: 23.401`)과 그 절의 표 번호(`clause 4.4A.2 Table 4.4A.2-3 of TS 38.508-1`)다. 이것을 건너지 못하면
#: 다른 문서의 절이 자기 문서의 같은 번호 절로 읽힌다. 번호를 감싼 대괄호(`clause [6.1.6] of TS 38.214`)는
#: 편집 중인 번호 표시라 번호로 읽는다.
_GAP = rf"(?:\s*\([^()\n]*\)|\s+(?i:table)\s+{_XNUM})?"
#: 문서와 머리말 사이. 쉼표(`[2, TS 38.211], clause 4.3`)나 여는 괄호(`TS 38.213 [13] (clauses 9 and 10)`)가
#: 낄 수 있다. 주의: 괄호를 건너지 못하면 괄호 속 번호가 자기 문서의 같은 번호 절로 읽힌다(TS 38.331 의
#: `ControlResourceSet` 이 자기 문서 9 · 10 절을 가리키게 된다). 공백은 `_CONJ` 의 주의대로 한 자리에서만 문다.
_LEAD = r"(?:\s*[,(])?\s*"
#: 문서가 앞에 오는 꼴의 인용 몸통. 쉼표로 이어 내려가는 사슬(`TS X [8] Annex A, clause A.2`)은
#: 한 문서 안에서 부속서 → 절로 좁혀 가는 표기라 사슬 전체가 그 문서를 가리킨다. 사슬을 끊으면
#: 뒤쪽 `clause A.2` 가 자기 문서의 A.2 로 읽힌다.
_HEAD_BODY = rf"{_KW}\s+({_XLIST_HEAD}(?:\s*,\s*{_KW}\s+{_XLIST_HEAD})*)"

#: 다른 문서를 가리키는 인용의 꼴들. 차례가 의미다 — 문서가 적힌 꼴을 먼저 떼어 내야
#: `[8] clause N` 꼴이 앞의 `TS X [8]` 를 두 번 읽지 않는다. (이름, 정규식, 문서 그룹, 번호 그룹,
#: 참고문헌 번호 그룹) — 문서 그룹이 없으면 참고문헌 번호로 문서를 찾고, 둘 다 없으면 3GPP 밖
#: 문서라 문서 번호가 None 이다.
EXTERNAL_FORMS: tuple[tuple[str, re.Pattern, int | None, int, int | None], ...] = (
    ("doc_then_clause",
     re.compile(rf"{_DOC}(?:\s*\[\d+\])?{_LEAD}{_HEAD_BODY}"), 1, 2, None),
    ("bibdoc_then_clause",
     re.compile(rf"\[\d+,\s*{_DOC}\]{_LEAD}{_HEAD_BODY}"), 1, 2, None),
    ("clause_of_doc",
     re.compile(rf"\b{_KW}\s+\[?({_XLIST})\]?{_GAP}{_OF}{_DOC}(?:\s*\[\d+\])?"), 2, 1, None),
    ("clause_of_bibdoc",
     re.compile(rf"\b{_KW}\s+\[?({_XLIST})\]?{_GAP}{_OF}\[\d+,\s*{_DOC}\]"), 2, 1, None),
    ("foreign_then_clause",
     re.compile(rf"{_FOREIGN}(?:\s*\[\d+\])?{_LEAD}{_HEAD_BODY}"), None, 1, None),
    ("clause_of_foreign",
     re.compile(rf"\b{_KW}\s+\[?({_XLIST})\]?{_GAP}{_OF}{_FOREIGN}(?:\s*\[\d+\])?"), None, 1, None),
    ("clause_of_bib",
     re.compile(rf"\b{_KW}\s+\[?({_XLIST})\]?{_GAP}{_OF}\[(\d+)\]"), None, 1, 2),
    ("bib_then_clause",
     re.compile(rf"\[(\d+)\]{_LEAD}{_HEAD_BODY}"), None, 2, 1),
    # 주의: 참고문헌 번호가 `of` 없이 절 번호 바로 뒤에 붙는 꼴(`Annex A.3.3 [15]` · `clause 6.2.3G [4]`)이다.
    # 이 꼴을 떼어 내지 않으면 [15] 문서의 A.3.3 이 자기 문서의 A.3.3 으로 읽힌다. 앞의 꼴들이 문서가 적힌
    # 인용(`TS 38.213 clause 7.7.1 [6]` · `clause 7.3.4 of TS 38.101-2 [19]`)을 먼저 떼어 내므로 맨 뒤에 둔다.
    ("clause_then_bib",
     re.compile(rf"\b{_KW}\s+\[?({_XLIST})\]?{_GAP}\s*\[(\d+)\]"), None, 1, 2),
)

#: 나열 → 번호. 거절 토큰의 중간(`5.3Bx` 의 `3`)에서 번호를 새로 세우지 않는다.
_XNUM_RE = re.compile(rf"(?<![0-9A-Za-z_.]){_XNUM}")

#: 자기 문서의 이어지는 번호. 머리말이 단수(`clause`)이면 마디가 둘 이상인 번호만 잇는다 — 단수
#: 머리말은 절 하나를 약속하므로, 뒤따르는 맨 숫자(`clause 5.1 and 10 dB`)는 절 번호가 아니라 값일 수 있다.
_DOTTED = rf"(?:{_SEG}|[A-Z])(?:(?:\.{_SEG})+{_LETTER}?|{_LETTER}){_TAIL}?{_END}"
#: 자기 문서 절 인용. `Section` 은 대문자만 받는다 — 소문자 `section` 은 일반 명사로도 쓰인다.
#: 복수 머리말(`clauses 5, 6 and 7` · `sub-clauses 6.3A.3.3.2-6.3A.3.3.5` · `Sections` · `annexes`)은
#: 나열을 약속하므로 맨 숫자도 잇는다. 단수 머리말만 읽으면 복수 머리말 인용 전체가 간선에서 빠진다.
#: 자기 문서 나열 안의 거절 토큰. 번호로 서는 토큰은 받지 않는다(`clause 5.1 and 10 dB` 의 `10` 을 단수
#: 머리말 나열에 넣지 않는다). 거절 토큰은 물기만 하고 번호로 내지 않으므로, 나열이 거기서 끊기지 않고 뒤쪽
#: 번호(`clauses 5.3Bx and 6` 의 6)를 계속 읽는다.
_REJ_OWN = rf"(?!{_XNUM}){_REJ}"
_SINGLE = rf"(?:{CLAUSE_NUM}|{_REJ_OWN})(?:{_CONJ}(?:{_DOTTED}|{_REJ_OWN}))*"
_PLURAL = rf"(?:{CLAUSE_NUM}|{_REJ_OWN})(?:{_CONJ}(?:{CLAUSE_NUM}|{_REJ_OWN}))*"
SAME_DOC_FORMS: tuple[re.Pattern, ...] = (
    re.compile(rf"\b(?i:clause)\s+({_SINGLE})"),
    re.compile(rf"\b(?i:subclause)\s+({_SINGLE})"),
    re.compile(rf"\bSection\s+({_SINGLE})"),
    re.compile(rf"\b(?i:(?:sub-?)?clauses)\s+({_PLURAL})"),
    re.compile(rf"\bSections\s+({_PLURAL})"),
    re.compile(rf"\bAnnex\s+({ANNEX_NUM})"),
    re.compile(rf"\b(?i:annexes)\s+({ANNEX_NUM}(?:{_CONJ}{ANNEX_NUM})*)"),
)

#: References 절의 한 항목. `[8]\t3GPP TS 38.521-1: "..."`.
_BIB_ENTRY = re.compile(rf"^\s*\[(\d+)\]\s*{_DOC}")


# Candidate only: keep the number grammar and external-document parser intact.
# A complete dotted number may be glued to a separate following English word.
# These patterns are anchored at a citation head or an already active list item;
# they never search inside a rejected token for a shorter numeric prefix.
_SPACE_NUMBER = rf"(?:{SEG}|[A-Z])(?:\.{SEG})+(?:\.[A-Z])?"
_SPACE_HEAD = re.compile(rf"\b{_KW}\s+\[?")
# Capture the complete token before choosing a word suffix. SEG permits a
# trailing letter: a greedy number-first pattern reads E.2.2for as E.2.2f + or.
# The longest explicit word is cut first; only then is the entire remaining
# number checked with the unchanged native grammar. Never retry a shorter word
# after a recognized longer word or fall back to a shorter numeric prefix.
_SPACE_ATTACHED = re.compile(
    r"(?P<token>[0-9A-Za-z_]+(?:\.[0-9A-Za-z_]+)*)"
    r"(?![0-9A-Za-z_]|\.[0-9A-Za-z_])")
_SPACE_WORDS = ('clauses', 'Clauses', 'clause', 'Clause',
                'with', 'does', 'and', 'for', 'or')
_SPACE_TOKEN = re.compile(_XTOK)
_SPACE_CONJ = re.compile(_CONJ)
_SPACE_SCOPE = re.compile(rf"(?:{_DOC}|{_FOREIGN}|\[\d+(?:\s*,\s*\d+)*\])")
_SPACE_DOC_LEAD = re.compile(
    rf"(?:{_DOC}(?:\s*\[\d+\])?|\[\d+,\s*{_DOC}\]|"
    rf"{_FOREIGN}(?:\s*\[\d+\])?|\[\d+\]){_LEAD}$")
_SPACE_SENTENCE_END = re.compile(r"[;\n]|\.(?=\s|$)")
# A comma followed by an explicit document AND a citation head starts a new
# citation. A bare document in a modifier is not such a boundary. This only
# bounds the spacing helper; the unchanged native parser still owns scope.
_SPACE_INDEPENDENT_CITATION = re.compile(
    rf",\s*(?:(?:and|or)\s+)?(?:{_DOC}(?:\s*\[\d+\])?|"
    rf"{_FOREIGN}(?:\s*\[\d+\])?){_LEAD}{_KW}\s+")
# Opt-in punctuation repair: a complete dotted number, an extra period, and
# the whole modifier word for. No target IDs or particular annex are consulted.
_SPACE_DOT_FOR = re.compile(
    r"(?P<number>[0-9A-Za-z_]+(?:\.[0-9A-Za-z_]+)*)\.for"
    r"(?![0-9A-Za-z_]|\.[0-9A-Za-z_])")
# Experimental, opt-in only. A timer subject and complete finite predicate are
# sentence evidence, unlike an arbitrary alphabetic clause suffix. The default
# split_external path never calls the repair helper. A consuming parser must
# explicitly opt in; all existing default callers retain their prior behavior.
_SPACE_TIMER = re.compile(
    rf"(?P<number>{_SPACE_NUMBER})\.(?P<timer>T[0-9]+)\s+"
    r"(?:starts|stops|expires)(?![0-9A-Za-z_])")


def repair_citation_spacing(text: str, *, timer_sentences: bool = False,
                            dot_for: bool = False,
                            lowercase_x: bool = False
                            ) -> tuple[str, list[dict[str, str | int]]]:
    """Return citation-only text and inspectable edits in original coordinates.

    This does not modify saved paragraph text, section identity or target IDs.
    Target existence is deliberately unavailable to the grammar. Dotted malformed
    numbers and arbitrary suffixes remain untouched. The extra-period-before-for
    rule requires its own opt-in and a complete dotted number. Repeated heads
    are repaired only in document-marker-free input: a whitespace repair must not
    make a second foreign head fall back to the own document. Timer sentence
    repair also requires explicit opt-in. A separate lowercase_x opt-in folds
    only a complete terminal .x placeholder to .X in active citation text; native
    exact-uppercase-then-parent resolution and document scope stay unchanged.
    An immediately attached hyphen tail is deferred. No section identity or
    saved body is rewritten. None changes default resolve.
    """
    edits: dict[tuple[int, int], dict[str, str | int]] = {}
    has_document_marker = bool(_SPACE_SCOPE.search(text))

    def add(start: int, end: int, replacement: str, rule: str,
            number: str, head: int) -> None:
        row = dict(start=start, end=end, original=text[start:end],
                   replacement=replacement, rule=rule, number=number,
                   citationHeadStart=head)
        key = (start, end)
        if key in edits:
            assert edits[key] == row
        else:
            edits[key] = row

    def modifier_scope_is_safe(head: int, rest: str) -> bool:
        end = _SPACE_SENTENCE_END.search(rest)
        tail = rest[:end.start()] if end else rest
        independent = _SPACE_INDEPENDENT_CITATION.search(tail)
        if independent:
            tail = tail[:independent.start()]
        next_head = _SPACE_HEAD.search(tail)
        if next_head:
            tail = tail[:next_head.start()]
        return not (_SPACE_SCOPE.search(tail)
                    and not _SPACE_DOC_LEAD.search(text[:head]))

    def placeholder_scope_is_safe(head: int, start: int, end: int) -> bool:
        # A modifier containing a later document is ambiguous under the native
        # _GAP contract. Permit it only when an unchanged external form already
        # consumes this whole normalized number. This does not choose a target:
        # split_external still resolves bibliography and in/out-of-scope specs.
        if modifier_scope_is_safe(head, text[end:]):
            return True
        normalized = text[:end - 1] + 'X' + text[end:]
        return any(m.start(num_g) <= start and end <= m.end(num_g)
                   for _, pattern, _, num_g, _ in EXTERNAL_FORMS
                   for m in pattern.finditer(normalized))

    for head in _SPACE_HEAD.finditer(text):
        pos = head.end()
        while pos < len(text):
            attached = _SPACE_ATTACHED.match(text, pos)
            if lowercase_x and attached and attached.group('token').endswith('.x'):
                normalized = attached.group('token')[:-1] + 'X'
                # Check the entire normalized token with the existing dotted
                # grammar. Never search inside a rejected base or accept an
                # interior wildcard, a compact annex, xx/x1 or another suffix.
                if (text[attached.end():attached.end() + 1] != '-'
                        and re.fullmatch(_DOTTED, normalized)
                        and placeholder_scope_is_safe(head.start(), pos,
                                                      attached.end())):
                    add(attached.end() - 1, attached.end(), 'X',
                        'terminal_lowercase_x_placeholder', normalized,
                        head.start())
                    # The approved token ends in .x: an attached hyphen tail
                    # was excluded above. Continue this list explicitly from
                    # the consumed original token end, without widening raw
                    # _XTOK or relying on its rejected-token alternative.
                    conj = _SPACE_CONJ.match(text, attached.end())
                    if not conj:
                        break
                    pos = conj.end()
                    continue
            number = word = None
            if attached:
                token = attached.group('token')
                for suffix in _SPACE_WORDS:
                    if token.endswith(suffix):
                        candidate = token[:-len(suffix)]
                        if re.fullmatch(_DOTTED, candidate):
                            number, word = candidate, suffix
                        break
            if number is not None:
                cut = attached.end() - len(word)
                rest = text[attached.end():]
                if word in ('and', 'or'):
                    following = re.match(
                        rf"\s+(?P<duplicate>{word}\s+)?(?={_XNUM})", rest)
                    if not following:
                        break
                    if following.group('duplicate'):
                        # Nand and M: remove only the glued duplicate word;
                        # the independent connective and document scope remain.
                        add(cut, attached.end(), '', 'duplicate_connective',
                            number, head.start())
                    else:
                        add(cut, cut, ' ', 'attached_connective',
                            number, head.start())
                    pos = attached.end() + following.end()
                    continue
                if word.lower().startswith('clause'):
                    following = re.match(rf"\s+(?={_XNUM})", rest)
                    if has_document_marker or not following:
                        break
                    add(cut, cut, ' ', 'attached_repeated_head',
                        number, head.start())
                    pos = attached.end() + following.end()
                    continue
                if not re.match(r"\s+[A-Za-z]", rest):
                    break
                # A trailing document behind a modifier is already outside the
                # native _GAP contract. Do not turn that ambiguous malformed
                # citation into a new own-document edge by repairing spacing.
                if not modifier_scope_is_safe(head.start(), rest):
                    break
                add(cut, cut, ' ', 'attached_following_word',
                    number, head.start())
                break
            if dot_for:
                dotted = _SPACE_DOT_FOR.match(text, pos)
                if dotted and re.fullmatch(_DOTTED, dotted.group('number')):
                    rest = text[dotted.end():]
                    if (re.match(r"\s+[A-Za-z]", rest)
                            and modifier_scope_is_safe(head.start(), rest)):
                        cut = dotted.end('number')
                        add(cut, cut + 1, ' ', 'period_before_for',
                            dotted.group('number'), head.start())
                    break
            if timer_sentences:
                timer = _SPACE_TIMER.match(text, pos)
                if timer and re.fullmatch(_DOTTED, timer.group('number')):
                    cut = timer.end('number') + 1
                    add(cut, cut, ' ', 'timer_sentence_hypothesis',
                        timer.group('number'), head.start())
                    break
            token = _SPACE_TOKEN.match(text, pos)
            if not token:
                break
            conj = _SPACE_CONJ.match(text, token.end())
            if not conj:
                break
            pos = conj.end()
    ordered = [edits[key] for key in sorted(edits)]
    previous_end = -1
    for row in ordered:
        assert row['start'] >= previous_end
        previous_end = row['end']
    repaired = text
    for row in reversed(ordered):
        repaired = (repaired[:row['start']] + row['replacement']
                    + repaired[row['end']:])
    return repaired, ordered


def is_references_section(title: str) -> bool:
    """References 절인가. 제목으로만 가린다 — 번호 `2` 는 규격마다 다른 절일 수 있다."""
    return title.strip().lower() == "references"


def is_change_history_section(title: str) -> bool:
    """변경 이력 절인가. 그 표의 칸은 CR 제목이다 — CR 이 고친 옛 판의 절 번호를 자유 서식으로 적어
    (`Update to TS 38.508-1 clause 4.6.3-200BB` 의 `4.6.3-200BB` 는 표 번호다) 지금 판의 절 인용이
    아니다. 파서는 이 절의 표 칸을 참조로 읽지 않는다."""
    return "change history" in title.lower()


def build_bibliography(paragraphs: list[str]) -> dict[str, str]:
    """References 절 문단 → {참고문헌 번호: 문서 번호}. 3GPP 문서가 아닌 항목은 싣지 않는다."""
    bib: dict[str, str] = {}
    for para in paragraphs:
        m = _BIB_ENTRY.match(para.replace("\xa0", " "))
        if m:
            bib.setdefault(m.group(1), m.group(2))
    return bib


def _numbers(listed: str) -> list[str]:
    """나열 → 번호 목록. 범위(`6.3A.3.3.2-6.3A.3.3.5` · `4 through 6`)는 사이 번호까지 편다 — 앞 마디가
    같고 끝 마디가 숫자인 범위만 편다. 깊이가 다른 범위(`5.1 to 5.3.2`)는 사이가 정해지지 않으므로 두 끝만
    남긴다."""
    nums: list[str] = []
    prev_end = None
    for m in _XNUM_RE.finditer(listed):
        num = m.group(0)
        if nums and _RANGE.fullmatch(listed[prev_end:m.start()]):
            lo_head, _, lo = nums[-1].rpartition(".")
            hi_head, _, hi = num.rpartition(".")
            if lo_head == hi_head and lo.isdigit() and hi.isdigit():
                nums += [f"{lo_head}.{k}" if lo_head else str(k) for k in range(int(lo) + 1, int(hi))]
        nums.append(num)
        prev_end = m.end()
    return nums


def split_external(text: str, bibliography: dict[str, str]
                   ) -> tuple[list[tuple[str | None, str]], str]:
    """다른 문서를 가리키는 인용을 떼어 낸다.

    Returns: (인용 목록, 남은 본문)
      - 인용 목록: (문서 번호, 절 번호). 참고문헌 번호가 3GPP 문서로 풀리지 않으면 문서 번호가
        None 이다 — 그 인용은 어느 절로도 해소하지 않지만, 자기 문서 절로 읽혀서도 안 되므로
        본문에서는 똑같이 떼어 낸다.
      - 남은 본문: 떼어 낸 자리를 공백으로 바꾼 본문. 자기 문서 절은 여기서만 읽는다.
    """
    text = text.replace("\xa0", " ")
    cited: list[tuple[str | None, str]] = []
    for _name, pattern, doc_g, num_g, bib_g in EXTERNAL_FORMS:
        def _take(m: re.Match) -> str:
            if doc_g is not None:
                doc = m.group(doc_g)
            elif bib_g is not None:
                doc = bibliography.get(m.group(bib_g))
            else:
                doc = None
            for num in _numbers(m.group(num_g)):
                cited.append((doc, num))
            return " "
        text = pattern.sub(_take, text)
    return cited, text


def same_doc_numbers(text: str) -> list[str]:
    """다른 문서 인용을 떼어 낸 본문에서 자기 문서 절 번호를 읽는다."""
    return [num for pattern in SAME_DOC_FORMS for m in pattern.finditer(text) for num in _numbers(m.group(1))]


def resolve(text: str, bibliography: dict[str, str], own_spec: str, release: str,
            own_section_id: str, scope_specs: set[str], section_ids: set[str]) -> set[str]:
    """본문의 절 인용 → 같은 release 안의 sectionId 집합(`{spec}-{release}-{num}`).

    다른 문서의 절은 그 문서가 범위(`scope_specs`) 안이고 그 절이 실재할 때만 간선이 된다.
    자기 자신은 싣지 않는다. 대시 꼬리가 붙은 번호는 그 번호의 절이 있으면(부속서 `A.3.3.2-1`) 그 절로,
    없으면(표 번호 `4.2-1`) 꼬리를 뗀 절로 해소한다 — 표 번호는 그 표가 실린 절을 가리킨다.
    끝 마디가 대문자 하나인 번호도 같다. 그 절이 있으면(`9.A`) 그 절로, 없으면 그 마디를 뗀 절로 해소한다.
    주의: 없는 쪽은 자리표시 번호(`clause 8.2.X` 는 아직 정하지 않은 8.2 의 아래 절)이거나 오타(`clause 9.2.A`)다.
    가리키는 절은 뗀 절 안에 있으므로 뗀 절로 잇는다. 오타를 고쳐 다른 번호(`9.2A`)로 짐작하지는 않는다.
    """
    cited, cleaned = split_external(text, bibliography)
    targets = [(doc, num) for doc, num in cited if doc is not None and doc in scope_specs]
    targets += [(own_spec, num) for num in same_doc_numbers(cleaned)]
    refs = set()
    for doc, num in targets:
        stem = _TAIL_END.sub("", num)
        for cand in (num, stem, _LETTER_END.sub("", stem)):
            ref_id = f"{doc}-{release}-{cand}"
            if ref_id in section_ids:
                if ref_id != own_section_id:
                    refs.add(ref_id)
                break
    return refs
