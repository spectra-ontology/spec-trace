"""회의록의 결정 표지와 결정 본문 범위를 판별한다.

RAN 다섯 WG의 Phase-2 결정 추출기가 사용하는 문법이다. 아래 예시는 처리
조건을 설명하기 위한 합성 문자열이며 특정 회의의 결정이나 추출 결과를 나타내지 않는다.

표지 분류
---------
`Agreement:`, `Conclusion:`, `Working assumption:` 같은 기본 표지 외에 괄호,
번호, 글머리표, 한정어, 같은 줄에 적힌 본문을 구분한다. 예를 들어
`Agreement on option A:`는 다음 문단을 소개하고,
`Agreement: Use option A.`는 같은 줄에 본문을 포함한다.

한정어는 괄호, 번호, 쉼표, 대시 또는 _LINKER의 연결어로 시작한다. 한정어가
주제와 본문을 함께 설명하면 표지 줄 전체를 본문에 포함한다. 문장형 표지와
따옴표로 감싼 결정도 같은 줄의 본문으로 읽는다. 글머리표가 있는 한정어 표지는
쌍점으로 끝날 때 결정 표지로 분류한다. 일반 번호가 붙은 conclusion은 별도
논의 목록으로, # 번호가 붙은 conclusion은 결정 표지로 구분한다.

조동사 판정은 괄호, 종속절, `to be`, 확정·수정 표현의 위치를 고려한다.
확정·수정 표현이 다음 본문을 소개하면 표지를 유지하고 단순 처리 상태나
향후 논의를 설명하면 결정 표지와 구분한다. 작업 가정의 합의 승격 여부는
WA_CONFIRMED, CONFIRMED_AS_AGREEMENT와 _confirmed_agreement가 판정한다.
호출자의 kinds에 agreement가 포함된 경우에만 종류를 바꾼다.

이메일 논의 산출물 목록의 항목, 기고문 초록의 인용·제안, 문서 처리 상태는
앞뒤 문맥까지 확인한다. 한 줄의 문법 판정은 classify가, 문단 사이의 판정은
최종 진입점 decision_spans가 담당한다.

본문 범위
---------
호출자는 표지 다음 문단을 `(번호, 글, 빈 줄 여부, 절 제목 여부)`로 전달한다.
표·그림 같은 비문자 본문은 그 뒤 문단 앞에 `(번호, "", False, False)`를
전달한다. 이 입력은 본문이 시작됐음을 표시하며 연속 빈 줄 집계를 끊는다.
`enclosed`는 현재 표지가 앞 결정의 본문 안에 있는지 나타낸다.

본문이 시작된 뒤 절 제목, 연속 빈 줄 두 개, 다음 결정, 발언, 문서 항목,
새 논의·제안·선택지 등이 나타나면 본문 종료 조건을 평가한다. 빈 줄로
분리된 문단 묶음의 첫 줄에서 새 주제가 시작되면 그 묶음 앞에서 끝낸다.
종료 직전의 한 줄짜리 제목 묶음은 _title_back이 함께 제외한다.

다음 조건에서는 해당 문단을 현재 결정 본문에 유지한다.

- 본문 시작 전 의장 발언이 포함된 발언 묶음, 또는 결정 내용을 적은 Decision 줄
- 문서 목록을 소개하는 문장 다음의 문서 항목과 빈 줄 전까지 이어지는 목록
- 본문이 명시적으로 소개한 쟁점·제안·선택지·질문 목록
- 빈 줄을 사이에 두고 같은 글머리표나 번호 매김 목록이 이어지는 경우
- 인용 본문이나 첨부할 변경 문구 안에 연속해서 등장하는 하위 결정 표지

가로줄은 본문에 삽입한 문구의 테두리와 주제 구분선을 구분한다. 본문에서
뒤의 변경 문구를 소개한 경우에는 테두리로 처리하고 그 외 구분선은 본문을
종료한다. 회사 발언은 출처 필드의 이름과 등록 약어를 대조한다.

인용·재기재
-----------
앞 회의의 결정을 인용한 표지는 이번 회의의 새 결정과 구분한다. 회의 식별자가
현재 회의와 같은지, 확정·수정 동작을 적었는지, 현재 회의의 추가 설명이 있는지
함께 확인한다. 요약 절에서 다시 적은 결정은 공백을 정규화한 본문이 앞서
추출한 결정에 모두 포함될 때 중복으로 제외한다.

앞 결정이 소개한 후속 표지는 _introduced가 종류·개수·인접성을 확인하여
앞 결정 본문에 포함한다. spans에는 제외된 인용·포함 표지의 범위도 기록한다.

출력 해석
---------
이 모듈은 문장과 문단 배치에 따른 추출 경계를 반환한다. 회의록에 합의 여부가
명시되지 않은 후속 제안 묶음은 기존 제안 목록에 포함될 수 있다. 하위 목록의
결정 표지는 상위 결정 본문과 개별 결정 본문 양쪽에 포함될 수 있다. 원문의
추출 범위를 점검할 때에는 표지 위치, 반환된 끝 위치와 종료 사유를 함께 본다."""
from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from functools import lru_cache
from typing import Iterable, Iterator, Optional, Sequence

#: 결정 종류 이름 → 표지 낱말.
KEYWORDS = {
    "agreement": r"agreements?",
    "conclusion": r"conclusions?",
    "working_assumption": r"(?:working\s*assumptions?|(?-i:WAs?))",
}

#: 닫힌 대괄호 표지(`[Agreement]` · `[Agreement:]`), 닫히지 않은 대괄호 표지(`[Agreement: 본문`), 맨 낱말.
_KEYWORD_RE = {
    kind: (
        re.compile(rf"^\[\s*{kw}\s*[:：]?\s*\]", re.IGNORECASE),
        re.compile(rf"^\[\s*{kw}\s*[:：]", re.IGNORECASE),
        re.compile(rf"^{kw}(?!\w)", re.IGNORECASE),
    )
    for kind, kw in KEYWORDS.items()
}
_BULLET = re.compile(r"^[-–•·▪]\s+")
#: 글머리표 글자.
_GLYPH = re.compile(r"^([-–•·▪])\s")
#: 번호 붙은 목록 항목 줄의 번호와 번호 뒤 글자(`2<TAB>…` · `2 <TAB>…` · `6) …` · `(3) …` · `3. …`). 절 번호
#: (`4.1.1.2<TAB>…`)와 숫자로 시작하는 글(`2 potential approaches …`)은 항목 줄이 아니다.
_NUM_ITEM = re.compile(r"^\(?(\d{1,2})(\t|\)\s*|\.\s+|\s{2,})(?=\S)")


def _num_item(t: str) -> Optional[tuple[str, int]]:
    """번호 붙은 목록 항목 줄이면 (번호 꼴, 번호) — 꼴은 번호 뒤 `)` · `.` 이고 빈칸 · 탭이면 빈 글이다."""
    m = _NUM_ITEM.match(t)
    return (m.group(2).strip(), int(m.group(1))) if m else None


_COLON = re.compile(r"[:：]")
_LEADING_COLON = re.compile(r"^\s*[:：]\s*", re.S)
_LEADING_SEP = re.compile(r"^\s*[:：;]\s*", re.S)
_ONLY_PUNCT = re.compile(r"^\s*[:：;.]\s*$")
_DASH = re.compile(r"^[-–—]\s*")
_QUOTE = re.compile(r"^(?:[“\"‘]|'(?!s\b))")
_NUMBER = re.compile(r"^(?:#\s*\d+[a-z]?|\d{1,3}(?:\s*[-–]\s*\d{1,3})?)(?![\w.])", re.IGNORECASE)
_PIN = re.compile(r"^P\d")
#: 결정을 확정 · 고친다는 말.
_REVISION = (r"(?:further\s+)?(?:re-?)?(?:confirmed|modified|updated|revised|amended|changed|replaced|superseded"
             r"|converted)")
_REVISION_PHRASE = re.compile(rf"\b(?:is|are|was|were|has\s+been|have\s+been)\s+{_REVISION}\b", re.IGNORECASE)
#: 확정 · 고친다는 말 뒤에 오면 뒤 문단이 그 결정 본문인 꼴.
_REVISION_TAIL = re.compile(
    r"^\s*,?\s*(?:\([^)]*\)\s*)*(?:[:：;]?\s*$|as\s+(?:follows|shown|below)\b|below\b|with\b)", re.IGNORECASE)
_REVISION_THAT = re.compile(r"^\s*,?\s*that\b", re.IGNORECASE)
#: 확정한다는 말 뒤 쉼표에 결정 글이 이어지는 꼴.
_REVISION_COMMA = re.compile(r"^\s*,\s*(?!(?:with|as|pending)\b|i\.e\.|e\.g\.)\S", re.IGNORECASE)
#: 처리 상태만 적은 줄의 표지 뒤 글.
_STATUS = re.compile(
    r"^\s*[:：]?\s*(?:re-?)?(?:confirmed|modified|updated|revised|amended|changed|agreed|endorsed)"
    r"(?:\s+(?:online|offline|(?:by|via)\s+e-?mail))?\s*\.?\s*$",
    re.IGNORECASE,
)
_LINKER = re.compile(
    r"^(?:(?:on|for|via|vie|in|within|with|from|of|regarding|during|pending|after|at|by|reached|drawn|made"
    r"|online|offline|e-?mail|related|relating|based|about|according|again|copied|and\s+FFS\w*|P\d+"
    r"|which|where|when|whose|who"
    rf"|{_REVISION}|(?:is|are|was|were|has\s+been|have\s+been)\s+{_REVISION})\b|[-–—/,])",
    re.IGNORECASE,
)
_AUXILIARY = re.compile(
    r"\b(?:is|are|was|were|be|been|being|will|would|can|could|should|shall|may|might|must"
    r"|has|have|had|do|does|did|not|needs)\b",
    re.IGNORECASE,
)
_TO_BE = re.compile(r"\bto\s+be\b", re.IGNORECASE)
_SENTENCE = re.compile(r"^(?:to|that)\b", re.IGNORECASE)
_COPULA_THAT = re.compile(r"\b(?:is|are|was|were)\s+that\b", re.IGNORECASE)
_INFINITIVE = re.compile(r"^to\s+(?:be\s+)?\w+", re.IGNORECASE)
_PARENS = re.compile(r"\([^()]*\)")
_UNCLOSED_PAREN = re.compile(r"\([^)]*$")
#: 종속절 — 이끄는 낱말부터 마침표까지.
_SUBORDINATE = re.compile(
    r"\b(?:that|which|where|when|while|if|whether|before|after|until|unless|once|who|whose|what)\b[^.]*",
    re.IGNORECASE,
)
#: 논의할 거리를 여는 한정어.
_PENDING = re.compile(
    r"\b(?:to\s+(?:be\s+)?(?:discuss|attempt)\w*|down-?prioriti[sz]\w*|requiring\s+more|proposed\s+to\s+be"
    r"|can\s+be\s+agreed)\b",
    re.IGNORECASE,
)
#: 쌍점 빠짐 꼴 가운데 본문이 아닌 것.
_NOT_INLINE = re.compile(r"^(?:summary\b|TP\s*[:：]|RAN\d\s*#)", re.IGNORECASE)
#: 출처 방식만 적은 한정어는 본문 문장과 구분한다.
#: 같은 위치의 대문자 전치사가 실제 결정 문장을 시작하는 경우는 본문으로 읽는다.
_SOURCE_QUALIFIER = re.compile(r"^(?:(?:by|via)\s+)?(?:e-?mail|off-?line|on-?line|copied\s+from)\b", re.IGNORECASE)

#: Tdoc 번호의 하이픈 자리 글자 — ASCII 하이픈과 유니코드 하이픈 · 대시(U+2010 · U+2011 · U+2012 · U+2013 · U+2212).
_TDOC_DASH = "[-\u2010\u2011\u2012\u2013\u2212]"


def tdoc_number(wg: str = r"\d", digits: str = "6,7") -> str:
    """TDoc 번호를 찾는 캡처 그룹 없는 정규식 조각을 반환한다.

    wg는 WG 숫자 위치의 정규식이고 digits는 문서번호의 숫자 개수다.
    하이픈 앞뒤 공백과 하이픈 생략형을 지원한다. 하이픈이 있는 번호는
    앞뒤 단어 경계를 요구하지 않으며 숫자가 더 이어져도 지정한 자리까지만 읽는다.
    하이픈이 없는 번호는 앞에 영숫자가 없고 뒤에 숫자가 이어지지 않아야 한다.
    읽은 문자열은 canonical_tdoc으로 표준 형식으로 바꾼다."""
    return (rf"(?:R{wg}\s?{_TDOC_DASH}\s?\d{{{digits}}}"
            rf"|(?<![A-Za-z0-9])R{wg}\d{{{digits}}}(?!\d))")


def canonical_tdoc(raw: str) -> str:
    """tdoc_number로 읽은 번호에서 공백·하이픈 차이를 정리해 `R{WG}-{숫자}`로 반환한다."""
    d = re.sub(r"\D", "", raw)
    return f"R{d[0]}-{d[1:]}"


@lru_cache(maxsize=None)
def _tdoc_finder(wg: str, digits: str) -> re.Pattern:
    return re.compile(tdoc_number(wg, digits))


def tdoc_ids(text: str, wg: str = r"\d", digits: str = "6,7") -> list[str]:
    """본문의 TDoc 번호를 등장 순서대로 반환한다. 중복 번호도 유지한다."""
    return [canonical_tdoc(m.group(0)) for m in _tdoc_finder(wg, digits).finditer(text)]


#: Tdoc 항목 줄 — 번호(번호 뒤 하이픈 하나까지) 뒤에 탭이 오는 줄.
ENTRY_LINE = re.compile(rf"^{tdoc_number()}-?\s*\t")
#: 이메일 배정 줄은 회의·논의 식별자가 든 대괄호로 시작한다.
#: 여러 대괄호를 연속해서 쓰거나 하나의 대괄호에 회의 번호와 논의 이름을 함께 쓸 수 있다.
#: 회의 번호에 Post, bis, 전자회의 접미사가 붙은 형식도 구분한다.
#: 단순 수치 범위·소수·거듭제곱·단위 표기와 전자회의 접미사만 있는 표기는 배정 줄에서 제외한다.
EMAIL_ASSIGNMENT = re.compile(r"^\[(?:(?:AT|POST|PRE)?\d+[\w-]*\]\s*\[\d+\]|\d+[a-z]*(?:-e)?#\w+\]\s*\["
                              r"|(?:AT|POST|PRE)?\d{2,3}(?:b|bis)?(?:-?e)?-(?:\d{1,3}[a-z]?(?:-\d{1,3}[a-z]?)*"
                              r"|\d[\d.]*[A-Za-z][\w.#/]*-[^\]\[]+|(?!e\])[A-Za-z][^\]\[]*)\])",
                              re.IGNORECASE)
#: 같은 문자를 반복한 가로줄이다. 본문이 첨부 문구를 소개한 뒤이면 테두리로,
#: 그 외에는 다음 주제를 나누는 구분선으로 처리한다.
RULE_LINE = re.compile(r"^([-=_*~#])\1+$")
#: 가로줄 바로 앞 줄이 이어 붙일 글을 예고하는 말.
FRAME_LEAD = re.compile(r"[:：]\s*$|\bfollow(?:ing|s)\b|\bTPs?\b|\btext\s+proposals?\b|\bbelow\b", re.IGNORECASE)
#: 본문 앞부분이 뒤의 변경 문구를 소개했으면 중간에 필드 설명이 끼어도 가로줄을 테두리로 읽는다.
FRAME_ANNOUNCE = re.compile(r"\bTPs?\b|\btext\s+proposals?\b", re.IGNORECASE)
#: 붙인 글의 테두리 글 줄 — 가로줄 글자 묶음에 말을 끼운 줄(`-----<Omitted text>-----` · `*** Unchanged text is omitted ***`).
FRAME_MARK = re.compile(r"([-=_*~#])\1{2,}")
#: 이메일 논의 결과 줄. RAN1 회의록은 이메일 논의 배정 줄 뒤에 그 결과를 `Done: …` 으로 적는다. 쌍점 없는
#: `Done` 은 알고리즘 단계 글(`Step 3: … Done`)에도 오므로 결과 줄이 아니다.
EMAIL_DONE = re.compile(r"^Done\s*[:：]\s*(?=\S)", re.IGNORECASE)
#: 결과 줄이 무엇이 합의 · 결론됐다고 적는 말 — 수동형 `… is agreed` · `… is considered as agreed` ·
#: `… is modified and agreed` 와 `RAN1 agreed …`, 결론 꼴 `… is concluded` · `the conclusions are:` ·
#: `RAN1 reached the following conclusion:` · `the following is taken as conclusion:`.
_DONE_PASSIVE = re.compile(r"\b(?:is|are|was|were|been)\s+(?:also\s+|later\s+|considered\s+(?:as\s+)?|\w+\s+and\s+)?"
                           r"agreed\b", re.IGNORECASE)
_DONE_ACTIVE = re.compile(r"\bRAN\s?1\s+(?:has\s+|have\s+)?agreed\b", re.IGNORECASE)
_DONE_CONCLUDED = re.compile(r"\b(?:is|are|was|were)\s+concluded\b", re.IGNORECASE)
_DONE_CONCLUSION_LEAD = re.compile(
    r"\b(?:the\s+conclusions?\s+(?:is|are)(?:\s+as\s+follows)?|reached\s+the\s+following\s+conclusions?"
    r"|taken\s+as\s+(?:an?\s+)?conclusions?)\s*[:：]\s*$", re.IGNORECASE)
#: 문서·판본·목록·양식 자체의 승인은 문서 처리 상태로 구분한다.
#: 결정이 실린 위치를 나타내는 전치사 뒤의 TDoc 번호와 승인 대상을 구분한다.
_DONE_DOCUMENT = re.compile(r"\b(?:p?CRs?|CR\d+\w*|draft\s?CRs?|LSs?|TPs?|TRs?|TSs?|TR\s?\d{2}\.\d+|TS\s?\d{2}\.\d+"
                            rf"|versions?|v\d+\.\d+(?:\.\d+)?|{tdoc_number(digits='5,7')}|(?:features?|parameters?)\s+lists?"
                            r"|templates?)\b", re.IGNORECASE)
_DONE_LOCATIVE = re.compile(rf"\b(?:of|in|from)\s+(?:\S+\s+){{0,3}}?{tdoc_number(digits='5,7')}\b", re.IGNORECASE)
#: 이메일 결과를 설명하기 전에 붙은 근거·출처 부사절.
_DONE_SOURCE = re.compile(r"^\s*(?:according|as\s+per|further\s+to|following|per|as\s+stated)\b[^,]*,\s*",
                          re.IGNORECASE)
#: 합의된 것이 뒤 문단을 가리키는 말(`the following …` · `Below updates` · `Table 1 and Table 2 below`).
_DONE_FORWARD = re.compile(r"^\s*(?:the\s+)?following\b|\bbelow\b", re.IGNORECASE)
#: 결과 줄 뒤 문단부터 본문이 온다는 꼴 — 줄이 쌍점으로 끝나거나 동사 뒤가 `as follows` · `below` 다.
_DONE_LEAD_TAIL = re.compile(r"[:：]\s*$|^\s*,?\s*(?:as\s+follows|below)\b", re.IGNORECASE)
_DONE_AS_WA = re.compile(r"^\s*as\s+(?:an?\s+)?working\s+assumptions?\b", re.IGNORECASE)
_SENTENCE_START = re.compile(r"[.;]\s+(?=[A-Z])")
#: 다음 줄의 Tdoc 을 가리키는 머리말. `Relevant Tdocs:` 꼴은 머리말이 아니라 입력 기고 목록 머리다(INPUT_HEAD).
POINTER_LEAD = re.compile(r"(?:\bin|\b(?:is|are|was|were)\s+(?:agreed|endorsed|approved|concluded)"
                          r"|^(?:final|corresponding|the\s+following)\b.*)\s*[:：]\s*$",
                          re.IGNORECASE | re.S)
#: 주제를 정리한 요약 문서의 위치를 가리키는 줄이다.
#: summary 뒤나 줄 끝의 in 구문이 TDoc 번호 또는 다음 문단을 가리켜야 한다.
#: summary로 시작해도 결정 내용 자체를 설명하거나 처분 동사가 있으면 요약 문서 위치로 분류하지 않는다.
TOPIC_TAIL = re.compile(
    r"^(?!.*\b(?:agreed|endorsed|approved|adopted|supported|noted|concluded|confirmed)\b)"
    r"(?:see\s+|(?:mon|tues|wednes|thurs|fri|satur|sun)day\s*[-–]\s*from\s+)?"
    r"(?:(?:final|detail+ed|e-?mail|thread|discussion|fl|feature\s+lead|moderator|offline|\(\w+\))\s+){0,3}"
    r"summar(?:y|ies)(?:(?:\s*#\s*\d+\w*|\s+is|\s+and\s+(?:updated\s+)?(?:TP|template))?"
    rf"\s+in(?:\s+in)?\s*(?:[:：]?\s*$|{tdoc_number()})"
    rf"|\b(?:[^.;:：]|\.(?=\S)){{0,80}}?\bin\s*(?:{tdoc_number()}(?![\w-])\s*(?:[.,(]|$)|[:：]?\s*$))", re.IGNORECASE)
#: Relevant로 시작하고 쌍점으로 끝나는 입력 기고문 목록 제목.
INPUT_HEAD = re.compile(r"^relevant\b[^:：]*[:：]\s*$", re.IGNORECASE)
#: 쟁점·주제 제목은 Issue, Topic, Sub-topic과 번호로 시작한다.
#: 쌍점 외에 대문자 제목·대시·줄 끝으로 바로 이어지는 형식도 허용한다.
ISSUE_HEAD = re.compile(r"^(?:(?:sub[-\s]?)?topic\s*#?\s*\d+(?:\s*[-.,]\s*\d+)*[a-z]?"
                        r"(?:\s*[:：]|\s+[-–]\s|\s+(?=(?-i:[A-Z(\[]))|\s*$)"
                        r"|issue\s*#?\s*\d+(?:[-.]\d+)*[a-z]?\s*[:：])", re.IGNORECASE)
#: 회의 진행 단계나 이메일 논의 회차가 바뀌는 제목이다.
#: 온라인 회의의 Web Conf 형식과 RAN3의 CB 오프라인 묶음 제목을 함께 처리한다.
#: CB 제목은 번호·밑줄로 시작하거나 대문자로 시작하는 한 단어인 경우로 한정한다.
SESSION_LINE = re.compile(r"^(?:(?:GTW|on-?line|off-?line)\s+session\b[^.:]{0,40}$"
                          r"|(?:\d+(?:st|nd|rd|th)|first|second|third|final)\s+round\s+(?:of\s+)?(?:e-?mail\s+)?"
                          r"discussion\s+conclusions?\s*:?\s*$"
                          r"|web\s*conf\b"
                          r"|(?:CB\s*#\s*\S.{0,80}|#\s*\d+_\s*\S.{0,80}|#\s*(?-i:[A-Z])[\w/-]*)\s*$)", re.IGNORECASE)
#: RAN3 오프라인 묶음의 진행자 표기는 새 결정 본문이 아닌 논의 묶음의 끝으로 처리한다.
MODERATOR_LINE = re.compile(r"^\(\s*(?:moderators?\s*[-–:]\s*[^()]{1,60}|[^()]{1,60}?\s*[-–:]\s*moderators?)\s*\)\s*$",
                            re.IGNORECASE)
#: 바로 뒤 쟁점 머리 줄들을 목록으로 소개하는 말(`Continue to discuss the following issues …` · `Remaining issues:`).
ISSUE_INTRO = re.compile(r"\bfollowing\b|\bissues?\b", re.IGNORECASE)
#: intended outcome이 쌍점으로 끝나면 후속 목록을 소개한다.
#: 같은 표현 뒤에 결과 내용이 이미 적힌 줄은 목록 제목으로 분류하지 않는다.
OUTCOME_HEAD = re.compile(r"^\W*(?:(?:initial|updated|final)\s+)?(?:intended|expected)\s+outcomes?\b.*[:：]\s*$",
                          re.IGNORECASE)
#: 회의록 틀의 칸 머리 낱말(`Abstract:` · `Discussion:` · `Decision:`) — 쌍점 앞 영문 낱말 하나.
_TEMPLATE_WORD = re.compile(r"^([A-Za-z]+)\s*[:：]")
#: 회의록 필드명의 오탈자를 허용하는 편집 거리 상한이다.
#: abstract는 1, discussion은 2, decision은 1까지 허용한다.
#: Revision이나 Discuss처럼 의미가 다른 필드명은 이 상한 밖에 둔다.
TEMPLATE_HEADS = {"abstract": 2, "discussion": 2, "decision": 1}


def _edit_distance(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def template_head(text: str) -> Optional[tuple[str, int]]:
    """줄이 회의록 틀의 칸 머리(TEMPLATE_HEADS)로 열면 (칸 이름, 머리 끝 위치), 아니면 None."""
    m = _TEMPLATE_WORD.match(text)
    if not m:
        return None
    w = m.group(1).lower()
    for name, bound in TEMPLATE_HEADS.items():
        if abs(len(w) - len(name)) <= bound and _edit_distance(w, name) <= bound:
            return name, m.end()
    return None


def _is_head(text: str, name: str) -> bool:
    h = template_head(text)
    return h is not None and h[0] == name


#: Abstract 필드의 결정 표지가 기고문 인용·제안인지 구분하는 신호다.
#: 출처 전치사·that절·직전 회의 식별자·앞 문장의 외부 출처를 확인한다.
#: Discussion 필드로 이어지는 conclusion은 기고문의 결론으로 구분한다.
#: WF 문서 초록에 현재 회의 결과를 적은 경우는 abstract_notes 정책에 따라 별도로 판정한다.
ABSTRACT_SOURCE = re.compile(r"^(?:agreements?|conclusions?|working\s+assumptions?)\s+(?:in|from|at|during|made|reached)\b",
                             re.IGNORECASE)
ABSTRACT_PROSE = re.compile(r"^(?:agreements?|conclusions?)\s+(?:(?:is|was|are|were)\s+)?that\b", re.IGNORECASE)
MEETING_TAG_LINE = re.compile(r"^(?:TSG\s*)?RAN\s*\d?\s*#\s*\d+[\w-]*$", re.IGNORECASE)
_DECISION_WORD = re.compile(r"agree|conclu|working\s+assum", re.IGNORECASE)
EXTERNAL_LOCUS = re.compile(r"RAN\s*\d?\s*#\s*\d+|\bAH-\d+|\bad[\s-]?hoc\b|\[\d+\]|(?-i:\bLS\b)"
                            r"|\bchair(?:man)?['’]?s?\s+notes?\b|\b(?:previous|last)\s+meetings?\b|\bRAN\d['’]s\b",
                            re.IGNORECASE)


#: Decision 머리말 없이 문서 처분만 적은 줄이다.
#: 발표자·게시·제출·정보 제공·회신 설명은 처분으로 취급하지 않는다.
BARE_DISPOSITION = re.compile(r"^(?:the\s+)?document\s+(?:was|is)\s+(?:noted|revised|agreed|endorsed|approved|merged|withdrawn"
                              r"|postponed|rejected|replied\s+to|deferred|reserved|(?:not|already)\s+treated|not\s+pursued"
                              r"|not\s+(?:made\s+)?available)\b", re.IGNORECASE)
#: Decision 머리말 뒤의 문서 처분 형식이다.
#: 문서 주어가 있는 형식과 처분 동사로 바로 시작하는 형식을 지원한다.
#: 등록한 오탈자와 주어·동사 사이 공백 생략형도 포함한다.
STATUS_REST = re.compile(
    r"^(?:t?he\s+document\b|document\s+(?:was|is)\b"
    r"|(?:this\s+(?:was|is)\s+)?(?:not\s+|technically\s+|for\s+)?(?:e-?\s*mail\s+)?"
    r"(?:noted|revised|agreed|endorsed|approved|merged|withd\w*|postpone\w*|treated|pursued|available|concluded"
    r"|rejected|replied|deferred|reserved|approval)\b)",
    re.IGNORECASE)
#: 대괄호 발언은 쌍점 뒤에 본문이 있어야 한다. 본문이 없으면 단순 식별자로 구분한다.
COMPANY_COMMENT = re.compile(r"^\[[^\]\[]{2,40}\]\s*[:：]\s*\S")
#: 긴 대괄호 이름 목록은 각 이름이 회사 이름에 해당하는지도 확인한다.
_BRACKET_SPEAKERS = re.compile(r"^\[([^\]\[]{41,})\]\s*[:：]\s*\S")
#: 대괄호 없는 발언 줄의 머리 — 글머리표 뒤 이름 묶음, 쌍점, 글.
_SPEAKER = re.compile(r"^(?:[-–•·▪]\s*)?([^:：\[\]()]{1,60}?)\s*[:：]\s*\S")
_SPEAKER_SPLIT = re.compile(r"\s*(?:,|/|;|\s&\s|\band\b|\+)\s*", re.IGNORECASE)
_SPEAKER_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9&'’\-]*")
_NAME_WORD = re.compile(r"[a-z0-9&'’]+")
#: 회사 이름 외의 발언자 역할과 등록 약어.
SPEAKER_ALIASES = re.compile(
    r"^(?:(?:RAN\d\s+)?(?:session\s+|vice[\s-]*|ad-?hoc\s+)?chair(?:man|person|woman)?|moderator|rapporteur"
    r"|e///|hw|ss|nok|qc|mtk|at&t|r&s)$",
    re.IGNORECASE,
)
#: 의장 · 진행자 · 보고자의 발언 줄 — 표지 줄 바로 뒤 발언 줄 묶음에 이 줄이 있으면 그 묶음이 결정의 내용이다.
CHAIR_LINE = re.compile(
    r"^(?:[-–•·▪]\s*)?(?:RAN\d\s+)?(?:(?:session\s+|vice[\s-]*|ad-?hoc\s+)?chair(?:man|person|woman)?|moderator"
    r"|rapporteur)\s*[:：]\s*\S",
    re.IGNORECASE,
)
#: TDoc의 Source 필드.
SOURCE_FIELD = re.compile(r"Source\s*:\s*([^\t\n]+)", re.IGNORECASE)
#: 출처 칸에 이름이 있어도 발언자로 치지 않는 쪽 — 회의 지원단(MCC)의 줄은 합의한 CR 에 다는 편집 지시다.
NOT_SPEAKER = frozenset({"mcc", "etsi", "etsi mcc"})
#: 본문이 시작된 뒤 빈 줄 건너 놓인 묶음 안의 제안 줄(`Proposal 5: …` · `[Easy] Proposal 7: …`).
PROPOSAL_LINE = re.compile(r"^(?:[-–•·▪]\s*)?(?:[\[(][^\])]{1,40}[\])]\s*)*proposals?\s*[-–#]?\s*\d", re.IGNORECASE)
#: 번호 없는 제안 머리(`Proposal:` · `Proposals: For option 6,`) — 결정 본문 뒤에 오면 다음에 논의할 제안을 연다.
PROPOSALS_HEAD = re.compile(r"^(?:[-–•·▪]\s*)?proposals?\s*[:：]", re.IGNORECASE)
#: 후속 제안이 결정 본문에 속한다고 명시하는 소개 문장.
PROPOSAL_INTRO = re.compile(r"\bfollowing\b|\bagreed\b", re.IGNORECASE)
#: 결정어 뒤의 괄호·대괄호가 본문 대신 논의 출처만 적었는지 확인한다.
NOTE_ONLY = re.compile(r"\s*[(\[].*[)\]]\s*[:：]?\s*")
#: 줄 앞 목록 글머리표.
LEAD_GLYPH = re.compile(r"^[-–•·▪]")
#: 묶음 첫 줄이 그 묶음의 제안이 이미 합의됐다고 적는 꼴(`Email agreed proposal in first round`).
AGREED_HEAD = re.compile(r"^(?:[-–•·▪]\s*)?(?:\S+\s+){0,3}agreed\b", re.IGNORECASE)
#: 아직 합의가 아니라는 말(`for further discussion` · `need discussion` · `potentially to agree` · `without clear majority`).
_NOT_AGREED = (r"for\s+(?:further\s+)?discussion|need(?:s|ed)?\s+(?:further\s+)?discussion"
               r"|potential(?:ly)?\s+(?:to\s+(?:be\s+)?)?agree|without\s+(?:a\s+)?clear\s+majority")
#: 그 말 · 미룬다는 말로 여는 묶음 머리(`For further discussion:` · `[Need discussion]` · `Potentially to agree:` ·
#: `To be revisited: …` · `Proposed offline consensus:` · `For future meetings:`).
NOT_AGREED_HEAD = re.compile(
    rf"^(?:[-–•·▪]\s*)?[\[(]?\s*(?:{_NOT_AGREED}|to\s+be\s+revisited|proposed\s+(?:offline\s+)?consensus"
    r"|for\s+(?:future|next)\s+meetings?)\b",
    re.IGNORECASE)
_NOT_AGREED_PHRASE = re.compile(rf"\b(?:{_NOT_AGREED})", re.IGNORECASE)
#: 소개하는 후속 항목이 아직 논의 대상이라고 밝히는 표현.
_PENDING_ANNOUNCE = re.compile(rf"\b(?:{_NOT_AGREED}|further\s+discussion)", re.IGNORECASE)
#: 뒤 항목들이 합의되지 않았다고 미리 밝히는 줄(`The following issues are not agreed, but …` ·
#: `The following bullets are not agreed:`). 빈 줄이 없어도 그 줄에서 앞 결정의 본문이 끝난다.
NOT_AGREED_FOLLOWING = re.compile(
    r"^(?:[-–•·▪]\s*)?(?:the\s+)?following\s+(?:[\w-]+\s+){0,3}(?:is|are|was|were)\s+not\s+(?:yet\s+)?agreed\b",
    re.IGNORECASE)
#: 뒤따르는 선택지 · 질문을 결정의 대상으로 끌어들이는 말(`the following` · `below` · `down-select` · `as follows`).
FORWARD = re.compile(
    r"\bdown[-\s]?select|\bas\s+follows\b|\b(?:options?|alternatives?)\s+below\b"
    r"|\bfollowing\s+(?:\S+\s+){0,2}?(?:options?|alternatives?|alts?|questions?|proposals?|cases?|aspects?|observations?)\b"
    r"|\bfollowing\b[^.;]*\bas\s+(?:an?\s+)?examples?\b",
    re.IGNORECASE)
#: 결정 본문 안에서 더 볼 거리를 여는 `FFS:` · `FFS details:` 줄.
FFS_LEAD = re.compile(r"^(?:[-–•·▪]\s*)?FFS\b[^.:：]{0,40}[:：]\s*$")
#: 내용 없이 기술 이름만 적은 쌍점 제목.
HEAD_LABEL = re.compile(r"^(?:[-–•·▪]\s*)?([^\s:：][^:：]{0,38}?)\s*[:：]\s*$")
#: 뒤에 나열한 선택지를 현재 결정의 검토 대상으로 명시하는 표현.
_FORWARD_NOUN = r"(?:options?|alt(?:ernative)?s?|schemes?|examples?)"
OWN_FORWARD = re.compile(rf"\b{_FORWARD_NOUN}(?:\s*[-#]?\s*\d+[a-z]?)?\b(?:[^.;]|\.(?=\d))*\bbelow\b"
                         rf"|\bbelow\s+(?:\S+\s+){{0,2}}?{_FORWARD_NOUN}\b", re.IGNORECASE)
#: 결정 본문이 보낼 LS 를 적는 말. 뒤 묶음의 질문 줄은 그 LS 의 내용이다(선택지 줄은 아니다).
OWN_LS = re.compile(r"\bLS\b")
#: 질문 꼴의 결정 밖 줄(`Q1: …` · `… ?`).
QUESTION_ITEM = re.compile(r"^(?:[-–•·▪]\s*)?Q\d+\s*[:：.]|\?\s*(?:\([^()]*\)\s*)?$", re.IGNORECASE)
#: 결정 밖의 선택지·질문 후보 줄. 번호·출처 괄호가 붙은 질문도 포함한다.
OPEN_ITEM = re.compile(
    r"^(?:[-–•·▪]\s*)?(?:(?:option|alt(?:ernative)?)(?:\s*[-#]?\s*\d+[a-z]?|\s+[A-Za-z])\b|Q\d+\s*[:：.])"
    r"|\?\s*(?:\([^()]*\)\s*)?$", re.IGNORECASE)
#: 여는 줄이 다른 논의 묶음의 시작인 꼴(본문이 시작된 뒤 빈 줄 건너 놓인 묶음의 첫 줄).
GROUP_OPENER = re.compile(
    r"^(?:[-–•·▪]\s*)?(?:"
    r"(?:\[[^\]]{1,40}\]\s*[-–:]?\s*)*(?:proposals?|observations?)\b"
    r"|(?:mon|tues|wednes|thurs|fri|satur|sun)day\b"
    r"|final\s+(?:\w+\s+){0,2}summary\b"
    r"|e-?mail\s+(?:discussion|approval)\b"
    r"|(?:possible|proposed|tentative|potential|candidate|suggested)\s+(?:agreements?|conclusions?|way\s*forward|WF"
    r"|working\s+assumptions?)\b"
    r"|suggestion\b|for\s+(?:further\s+study|potential\s+agreement|discussion)\b|for\s+RAN\d\s*#"
    r"|(?:low|medium|high)(?:er)?\s+priority\b|easily\s+agreeable\b|agreeable\b"
    r"|(?:\(online\)\s*)?(?:sub-?\s*)?(?:issue|topic)\s*#?\s*\d|open\s*[:：]"
    r"|to\s+be\s+continued\b|continue\s+(?:the\s+)?discussion\b|will\s+revisit\b|come\s*back\b"
    r"|to\s+be\s+(?:further\s+)?discussed\b|(?:the\s+)?following\s+proposals?\s+(?:\w+\s+){0,2}(?:further\s+)?discuss"
    r"|CB\s*#|#\s*\d+_|discuss(?:ions?)?\b|whether\b|how\b"
    r"|P\d+(?:\.\d+)?[a-z]?\b|\d{3,5}\s*\(|\d+-\d+(?:-\d+)*\s*[:：]"
    r")",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Mark:
    """결정 표지 한 줄.

    inline: 표지 줄에 함께 적힌 본문(기본 꼴은 표지 낱말 뒤 글, 한정어 · 문장 꼴은 줄 전체). 없으면 None.
    lead:   본문이 다음 문단부터인 한정어 꼴의 표지 줄 전체. 뒤 본문이 비면 `lead_stands_alone` 이 참일 때만
            결정을 만든다.
    bullet: 표지 줄이 글머리표로 열면 그 글자(`-` · `•` …). 같은 표지인지 견줄 때는 보지 않는다.
    """
    kind: str
    inline: Optional[str] = None
    lead: Optional[str] = None
    bullet: Optional[str] = field(default=None, compare=False)


#: 표지 낱말 뒤 한정어가 `of` 로 여는 꼴(`Agreement of the CR for …`).
_LEAD_OF = re.compile(r"of\b", re.IGNORECASE)


def lead_stands_alone(mark: Mark) -> bool:
    """다음 본문이 없는 한정어 표지를 독립 결정으로 읽을지 판단한다.

    마침표로 끝나고 FRAME_LEAD로 뒤 본문을 소개하지 않으며 결정어 뒤가
    of로 시작하는 명사구가 아닐 때 참이다. for/on 주제 설명과 of 명사구를
    구분하는 문법 규칙이며 개별 문장의 실제 합의 여부를 평가하는 함수는 아니다."""
    lead = mark.lead
    if lead is None or not lead.rstrip().endswith(".") or FRAME_LEAD.search(lead):
        return False
    line = _BULLET.sub("", lead.strip(), count=1)
    for _closed, _unclosed, plain in _KEYWORD_RE.values():
        m = plain.match(line)
        if m:
            rest = _DASH.sub("", line[m.end():].lstrip(), count=1)
            rest, _had = _skip_brackets(rest)
            return not _LEAD_OF.match(rest)
    return True


def mark_head(mark: Mark, line_text: Optional[str]) -> Optional[str]:
    """표지 줄에 든 본문(mark.inline · mark.lead)을 다른 판독기로 다시 읽은 줄에서 꺼낸다.

    mark 는 확정 글(`docx_text.final_text`)로 읽은 표지다. line_text 는 같은 표지 줄을 수식 · 그림 표지나
    LaTeX 를 넣어 다시 읽은 글이다. 그 글이 같은 종류의 표지로 읽히면 그 본문을, 아니면 mark 의 본문을 돌려준다.
    확정 글로는 머리만 있는 표지 줄(`Agreement:`)도 다시 읽은 글에 그림 · 수식 표지나 글상자 글이 들면 그것을 돌려준다.
    """
    head = mark.inline or mark.lead
    if line_text:
        again = classify(line_text)
        if again is not None and again.kind == mark.kind:
            return again.inline or again.lead or head
    return head


def _skip_brackets(s: str) -> tuple[str, bool]:
    """줄 머리의 괄호 묶음들을 건너뛴 나머지와 건너뛴 묶음이 있었는지. 짝이 안 닫힌 괄호는 줄 끝까지 묶음이다."""
    had = False
    while s[:1] in ("(", "["):
        depth = 0
        end = -1
        for i, ch in enumerate(s):
            if ch in "([":
                depth += 1
            elif ch in ")]":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end < 0:
            return "", True
        s = s[end:].lstrip()
        had = True
    return s, had


def _has_auxiliary(s: str) -> bool:
    """한정어 글에 조동사가 있는가. 괄호 안, 확정 · 고친다는 말(뒤가 본문을 가리키는 꼴), `to be`, 종속절,
    전부 대문자인 낱말은 세지 않는다."""
    while True:
        t = _PARENS.sub(" ", s)
        if t == s:
            break
        s = t
    s = _UNCLOSED_PAREN.sub(" ", s)
    m = _REVISION_PHRASE.search(s)
    if m and _REVISION_TAIL.match(s[m.end():]):
        s = s[:m.start()] + " " + s[m.end():]
    s = _SUBORDINATE.sub(" ", _TO_BE.sub(" ", s))
    return any(not a.group().isupper() for a in _AUXILIARY.finditer(s))


def _email_outcome(body: str, kinds) -> Optional[Mark]:
    """이메일 논의 결과 줄(`Done:` 뒤 글)이 결정의 합의 · 결론을 적으면 그 표지, 합의된 것이 문서면 None.
    수동형은 동사 앞 문장에서 근거 부사절을 뺀 나머지가, `RAN1 agreed` 는 동사 뒤 절이 합의된 것이다.
    합의된 것이 뒤 문단을 가리키거나 줄이 쌍점 · `as follows` 로 끝나면 한정어 줄(본문은 다음 문단부터)이다."""
    kind = "agreement"
    m = _DONE_PASSIVE.search(body)
    if m:
        what = _SENTENCE_START.split(_PARENS.sub(" ", body[:m.start()]))[-1]
        what = _DONE_SOURCE.sub("", what, count=1)
    elif _DONE_ACTIVE.search(body):
        m = _DONE_ACTIVE.search(body)
        what = re.split(r"[;.]\s|[:：]", body[m.end():])[0]
    else:
        m = _DONE_CONCLUDED.search(body)
        if m:
            what = _DONE_SOURCE.sub("", _SENTENCE_START.split(_PARENS.sub(" ", body[:m.start()]))[-1], count=1)
        elif _DONE_CONCLUSION_LEAD.search(body):
            return Mark("conclusion", lead=body) if "conclusion" in kinds else None
        else:
            return None
        kind = "conclusion"
    if _DONE_DOCUMENT.search(_DONE_LOCATIVE.sub(" ", what)):
        return None
    tail = body[m.end():]
    if kind == "agreement" and _DONE_AS_WA.match(tail):
        kind = "working_assumption"
    if kind not in kinds:
        return None
    if _DONE_FORWARD.search(what) or _DONE_LEAD_TAIL.search(tail):
        return Mark(kind, lead=body)
    return Mark(kind, inline=body)


#: 작업 가정이 확정됐다는 줄 머리. `if` · `unless` 로 건 조건부 확정은 뺀다.
WA_CONFIRMED = re.compile(
    r"^(?:\[\s*)?(?:working\s*assumptions?|(?-i:WAs?))\b(?:\s+from\s+[^,:：;]{1,40}?)?\s+"
    r"(?:is|are|was|were|has\s+been|have\s+been)\s+confirmed\b(?!\s+(?:if|unless)\b)",
    re.IGNORECASE)
#: 작업 가정 줄이 합의로 확정됐다는 말. 확정된 합의를 `below` 로 뒤에 따로 적은 줄은 뺀다.
CONFIRMED_AS_AGREEMENT = re.compile(
    r"\bconfirmed\b[^.;:]{0,40}?\bas\s+(?:an?\s+)?(?:formal\s+|RAN\d\s+)?agreements?\b(?![^.;]*\bbelow\b)",
    re.IGNORECASE)
_NEGATED_CONFIRMATION = re.compile(
    r"\b(?:not|never)\s+(?:(?:yet|be|been|being|to|fully|formally|explicitly|finally|previously)\s+)*$",
    re.IGNORECASE)
_CONDITIONAL_CONFIRMATION = re.compile(r"\b(?:if|unless)\b", re.IGNORECASE)


def _confirmed_agreement(line: str) -> bool:
    """확정 표현의 부정어와 같은 문장·괄호 구간 앞뒤의 조건어를 검사한다."""
    for match in (WA_CONFIRMED.match(line), CONFIRMED_AS_AGREEMENT.search(line)):
        if match is None:
            continue
        confirmed = re.search(r"\bconfirmed\b", match.group(), re.IGNORECASE)
        start = match.start() + confirmed.start()
        if _NEGATED_CONFIRMATION.search(line[:start]):
            continue
        head = re.split(r"[.;:：()\[\]]", line[:start])[-1]
        tail = re.split(r"[.;:：()\[\]]", line[start + len("confirmed"):], maxsplit=1)[0]
        if not (_CONDITIONAL_CONFIRMATION.search(head) or _CONDITIONAL_CONFIRMATION.search(tail)):
            return True
    return False


def _read(text: str, kinds) -> tuple[Optional[Mark], bool]:
    """결정 표지와 새 논의 묶음을 여는지 여부를 반환한다.

    글머리표가 있는 한정어 표지가 쌍점으로 끝나지 않으면 목록 항목으로 처리한다.
    작업 가정의 확정 표현이 있고 kinds에 agreement가 있으면 합의로 분류한다."""
    raw = text.strip()
    line = _BULLET.sub("", raw, count=1)
    mark, opens = _read_line(line, kinds)
    if (mark is not None and mark.kind == "working_assumption" and "agreement" in kinds
            and _confirmed_agreement(line)):
        mark = replace(mark, kind="agreement")
    if mark is not None and mark.lead is not None and line != raw and not line.endswith((":", "：")):
        return None, False
    g = _GLYPH.match(raw)
    if mark is not None and line != raw and g:
        mark = replace(mark, bullet=g.group(1))
    return mark, opens


def _read_line(line: str, kinds) -> tuple[Optional[Mark], bool]:
    """글머리표를 뗀 줄의 (결정 표지, 다른 묶음을 여는 줄인가)."""
    d = EMAIL_DONE.match(line)
    if d:
        return _email_outcome(line[d.end():], kinds), False
    for kind in kinds:
        closed, unclosed, plain = _KEYWORD_RE[kind]
        m = closed.match(line) or unclosed.match(line)
        if m:
            body = _LEADING_COLON.sub("", line[m.end():], count=1).strip()
            if m.re is unclosed and body.endswith("]") and "[" not in body:
                body = body[:-1].rstrip()
            return (Mark(kind, inline=body) if body else Mark(kind)), False
        m = plain.match(line)
        if m:
            break
    else:
        return None, False
    rest = line[m.end():]
    if not rest.strip() or _ONLY_PUNCT.match(rest):
        return Mark(kind), False
    if _STATUS.match(rest):
        return None, False
    c = _LEADING_SEP.match(rest)
    if c:
        body = rest[c.end():].strip()
        return (Mark(kind, inline=body) if body else Mark(kind)), False

    s = rest.lstrip()
    if _QUOTE.match(s):
        return Mark(kind, inline=line), False
    qualified = False
    d = _DASH.match(s)
    if d:
        after = s[d.end():].strip()
        if after and not _LINKER.match(after) and not after.endswith((":", "：")):
            return Mark(kind, inline=after), False
        s, qualified = after, True
    s, had_brackets = _skip_brackets(s)
    qualified = qualified or had_brackets
    bracketed = qualified
    numbered = False
    n = _NUMBER.match(s)
    if n:
        if kind == "conclusion" and not s.startswith("#"):
            return None, True
        s, had_brackets = _skip_brackets(s[n.end():].lstrip())
        qualified = qualified or had_brackets
        numbered = True
    if not s or _ONLY_PUNCT.match(s):
        return (Mark(kind, lead=line) if qualified else Mark(kind)), False
    c = _LEADING_COLON.match(s)
    if c:
        body = s[c.end():].strip()
        if not qualified:
            return (Mark(kind, inline=body) if body else Mark(kind)), False
        return (Mark(kind, inline=line) if body else Mark(kind, lead=line)), False
    qualified = qualified or numbered
    if _PENDING.search(s):
        return None, True
    colon_end = s.rstrip().endswith((":", "："))
    if _SENTENCE.match(s):
        if colon_end:
            return Mark(kind, lead=line), False
        if _TO_BE.match(s):
            return None, False
        if s[:2].lower() == "to" and _has_auxiliary(_INFINITIVE.sub("", s, count=1)):
            return None, False
        return Mark(kind, inline=line), False
    cp = _COPULA_THAT.search(s)
    if cp and not _has_auxiliary(s[:cp.start()]):
        after = s[cp.end():]
        return (Mark(kind, lead=line) if not after.strip() or _ONLY_PUNCT.match(after)
                else Mark(kind, inline=line)), False
    if (not bracketed and (s[:1].isupper() or s[:1].isdigit()) and not _NOT_INLINE.match(s)
            and not _PIN.match(s) and not _SOURCE_QUALIFIER.match(s)
            and (not colon_end or not (numbered or _LINKER.match(s)))):
        return Mark(kind, inline=s), False
    if not qualified and not _LINKER.match(s):
        return None, False
    r = _REVISION_PHRASE.search(s)
    if r and (_REVISION_THAT.match(s[r.end():]) or _REVISION_COMMA.match(s[r.end():])):
        return Mark(kind, inline=line), False
    c = _COLON.search(s)
    if c:
        if not s[c.end():].strip():
            return Mark(kind, lead=line), False
        return (None if _has_auxiliary(s[:c.start()]) else Mark(kind, inline=line)), False
    if _has_auxiliary(s):
        return None, False
    return Mark(kind, lead=line), False


def classify(text: str, kinds=tuple(KEYWORDS)) -> Optional[Mark]:
    """문단 글이 결정 표지면 Mark, 아니면 None. kinds 는 읽을 결정 종류(KEYWORDS 의 키)."""
    return _read(text, kinds)[0]


def opens_block(text: str, kinds=tuple(KEYWORDS)) -> bool:
    """결정 표지는 아니지만 결정 낱말로 다른 묶음(번호 붙은 회사 결론 · 논의할 거리)을 여는 줄인가."""
    return _read(text, kinds)[1]


def ends_content(text: str, prev_text: str) -> bool:
    """현재 문단에서 앞 결정의 본문이 끝나는지 판단한다.

    문서 처리 상태, 이메일 결과·배정, TDoc 항목을 확인한다. prev_text는
    앞선 비어 있지 않은 본문 문단이며 첫 문단이면 표지의 inline 또는 lead다.
    TDoc 목록을 소개한 문장 바로 뒤의 항목과 그 목록을 잇는 항목은 본문에 둔다.
    이메일 배정 줄은 새 논의로 구분한다. 쌍점으로 끝나는 TDoc 항목은 뒤 본문을
    소개하므로 유지한다. 제목에 summary가 있는 항목은 소개 문장 바로 뒤에서만
    유지하며 앞 TDoc 항목의 목록을 자동으로 이어받지 않는다."""
    t = text.strip()
    if _is_head(t, "decision") or BARE_DISPOSITION.match(t) or EMAIL_DONE.match(t) or EMAIL_ASSIGNMENT.match(t):
        return True
    if ENTRY_LINE.match(t):
        if t.endswith((":", "：")):
            return False
        p = prev_text.strip()
        if summary_entry(t):
            return not POINTER_LEAD.search(p)
        return not (POINTER_LEAD.search(p) or ENTRY_LINE.match(p))
    return False


#: Tdoc 항목 줄 제목 칸의 요약 문서 낱말.
_SUMMARY_TITLE = re.compile(r"\bsummar(?:y|ies)\b", re.IGNORECASE)


def summary_entry(text: str) -> bool:
    """TDoc 항목의 제목 필드에 summary라는 단어가 있는지 반환한다."""
    f = text.split("\t") if ENTRY_LINE.match(text) else []
    return len(f) > 1 and bool(_SUMMARY_TITLE.search(f[1]))


def _decision_note(text: str) -> bool:
    """`Decision:` 머리 뒤에 처분 틀(STATUS_REST)이 아닌 결정 글이 오는 줄인가."""
    h = template_head(text)
    if h is None or h[0] != "decision":
        return False
    rest = text[h[1]:].strip()
    return bool(rest) and not STATUS_REST.match(rest)


def _name_key(name: str) -> str:
    return " ".join(_NAME_WORD.findall(name.lower().replace("-", " ").replace("_", " ")))


def speaker_words(sources: Iterable[str]) -> frozenset:
    """출처 필드의 이름으로 발언자 비교 문자열 집합을 만든다.

    괄호 안 텍스트를 제외하고 이름의 앞 단어 조합을 모두 추가한다.
    비교 문자열은 소문자로 바꾸고 하이픈을 공백으로 정규화한다.
    앞 단어 조합을 구할 때는 원래의 공백을 사용하므로 하이픈 안에서 이름을 자르지 않는다."""
    keys = set()
    for src in sources:
        for name in _SPEAKER_SPLIT.split(_PARENS.sub(" ", src)):
            words = name.split()
            for k in range(1, len(words) + 1):
                keys.add(_name_key(" ".join(words[:k])))
    return frozenset(keys - NOT_SPEAKER - {""})


def speaker_comment(text: str, companies: frozenset = frozenset()) -> bool:
    """대괄호 발언 또는 쌍점 앞 발언자 목록을 검사한다.

    발언자마다 출처 이름의 앞 단어 조합, 등록 약어 또는 의장 이름과 일치해야 한다."""
    t = text.strip()
    if COMPANY_COMMENT.match(t):
        return True
    m = _BRACKET_SPEAKERS.match(t) or _SPEAKER.match(t)
    if not m:
        return False
    names = [x.strip() for x in _SPEAKER_SPLIT.split(m.group(1).strip()) if x.strip()]
    if not names:
        return False
    for name in names:
        if SPEAKER_ALIASES.match(name):
            continue
        tokens = name.split()
        if len(tokens) > 4 or not all(_SPEAKER_TOKEN.fullmatch(x) for x in tokens):
            return False
        key = _name_key(name)
        if key in NOT_SPEAKER or key not in companies:
            return False
    return True


def not_agreed_head(t: str) -> bool:
    """아직 합의가 아니라고 적는 묶음 머리인가. 그 말로 줄을 열거나, 줄 안에 그 말이 있되 줄이 이름표 꼴(그 말을 뺀
    나머지에 조동사가 없고 마침표로 끝나지 않는다)이다."""
    if NOT_AGREED_HEAD.match(t):
        return True
    m = _NOT_AGREED_PHRASE.search(t)
    if m is None or t.rstrip().endswith("."):
        return False
    return not _has_auxiliary(t[:m.start()] + " " + t[m.end():])


#: 권고 줄(`Recommendation 2: …`) — 제안 줄처럼 다음 논의가 다룰 거리를 적는다.
RECOMMENDATION_LINE = re.compile(r"^(?:[-–•·▪]\s*)?recommendations?\s*[-–#]?\s*\d", re.IGNORECASE)
#: 뒤 묶음을 자기 내용으로 끌어들이는 줄 끝 · 말.
_LEAD_IN = re.compile(r"[:：]\s*$|\bfollow(?:ing|s)\b|\bbelow\b|\bas\s+follows\b", re.IGNORECASE)
#: 대괄호만 있는 제목이다. 괄호 안에 발언이나 note가 있으면 본문에 붙은 메모로 구분한다.
BRACKET_TAG = re.compile(r"^\[(?=[^\]]*[A-Za-z])(?![^\]]*[:：]\s*[^\]\s])(?![^\]]*\bnotes?\b)[^\[\]\s][^\[\]]*\]\s*[:：]?$",
                         re.IGNORECASE)
#: 줄 끝 괄호에 적힌 출처·발언 참조.
CITATION_TAIL = re.compile(r"\([^()]*[:：]\s*\d{4,5}\b[^()]*\)\s*$")
#: 목록·문서 번호·표·그림·처분·지시 표현은 제목 후보에서 제외한다.
#: 지시 동사 뒤가 for/of/on이면 명사구 제목일 수 있다.
_NOT_TITLE_HEAD = re.compile(
    rf"^(?:[-–•·▪*…]|\d+(?:\.\d+)*[.)]?\s|\(?[a-z0-9]{{1,3}}\)\s|=>|->|{tdoc_number(digits='5,7')}|(?:Tables?|Figures?|Fig\.)(?!\w)"
    r"|(?:FFS|TBD|Notes?|Noted|Not|No|treated|Agreed|Endorsed|Approved|Revised|Update[ds]?|Offline|Online|CBF?"
    r"|Continued?|Postponed|Withdrawn|Merged)\b"
    r"|(?:Ask|Send|Check|Discuss|Provide|Confirm|Capture|Keep|Use|Support|Introduce|Define|Specify|Adopt|Agree|Wait"
    r"|Inform|Remove|Add|Allow|Study|Consider|Clarify|Reply|Prepare|Editors?|Companies|Further|Come\s*back)\b"
    r"(?!\s+(?:for|of|on)\b))",
    re.IGNORECASE)
#: 할 일을 적는 말 — 이 말이 든 줄은 제목이 아니라 다음 논의의 처리 지시다.
_ACTION_PHRASE = re.compile(r"\be-?mail\s+(?:discussion|approval)\b|\bLS\s+(?:out|to|in)\b|=>|->|\boff-?line\b"
                            r"|\bon-?line\b", re.IGNORECASE)
#: 제목 묶음을 거슬러 찾는 끝.
_TITLE_ENDS = frozenset({"mark", "markgroup", "disc", "speaker", "entry", "email", "notagreed", "opener", "proposal",
                         "open", "trailer", "issue", "session", "2blank"})


def _colon_title(t: str) -> bool:
    """쌍점으로 끝나는 이름표 줄인가 — 뒤를 끌어들이는 말 · `FFS:` 머리가 없고 쌍점 앞에 조동사가 없다."""
    t = t.rstrip()
    return (t.endswith((":", "：")) and not _LEAD_IN.search(t[:-1]) and not FFS_LEAD.match(t)
            and not _has_auxiliary(t[:-1]))


def _noun_title(t: str) -> bool:
    """명사구 제목 줄인가 — 대문자로 열고, 문장 · 목록 끝 부호와 `이름: 글` 꼴이 없고, 조동사가 없다."""
    return (t[:1].isupper() and not t.rstrip().endswith((".", ":", "：", ";", ",", "?"))
            and not _NOT_TITLE_HEAD.match(t) and not _ACTION_PHRASE.search(t)
            and not re.search(r"[:：]\s*\S", t) and not _has_auxiliary(t))


def _title_rule(lines: list[str], kind: str) -> Optional[str]:
    """종료 위치 앞 문단 묶음이 다음 주제의 제목이면 규칙 문자를 반환한다.

    a: 한 줄짜리 쌍점 제목. b: 한 줄짜리 대괄호 제목.
    c: 출처를 적은 괄호로 끝나는 제목이며 다음 줄이 논의·항목인 경우.
    d: 명사구 제목이며 다음 줄이 문서·이메일 배정·제안인 경우.
    e: 쌍점으로 끝나 뒤 목록을 소개하는 제목. FFS 머리는 제외한다.
    g: 쌍점·대괄호 제목만 여러 줄 나열한 묶음.
    제안·권고 본문이 들어 있는 여러 줄 묶음은 제목으로 분류하지 않는다.
    kind는 종료 사유이며 앞 제목을 계속 검사할 때에는 title이다."""
    if any(PROPOSAL_LINE.match(x) or RECOMMENDATION_LINE.match(x) or OPEN_ITEM.search(x) for x in lines):
        return None
    if len(lines) != 1:
        return "g" if all(_colon_title(x) or BRACKET_TAG.match(x) for x in lines) else None
    head = lines[0]
    if _colon_title(head):
        return "a"
    if BRACKET_TAG.match(head):
        return "b"
    if head.rstrip().endswith((":", "：")) and not FFS_LEAD.match(head):
        return "e"
    if kind in ("disc", "speaker", "proposal", "opener", "entry", "email") and CITATION_TAIL.search(head):
        return "c"
    if kind in ("entry", "email", "proposal") and _noun_title(head):
        return "d"
    return None


def _title_back(groups: list, kind: str) -> tuple[Optional[int], str]:
    """빈 줄에서 끝날 때 끝 바로 앞의 제목 묶음들을 거슬러 찾는다. 찾은 첫 묶음 앞 빈 줄과 규칙 글자들을, 없으면
    (None, "") 를 돌려준다. 묶음은 [앞 빈 줄, 글 줄들, 표 · 그림 · 테두리가 있는가, 앞 본문의 이름표를 잇는가, 끝 글 줄]
    이고 마지막 묶음이 끝을 낸 묶음이다. 첫 본문 묶음은 거스르지 않는다."""
    k, letters = len(groups) - 1, ""
    while k >= 2:
        _, lines, nontext, cont, _ = groups[k - 1]
        if nontext or cont or not lines:
            break
        rule = _title_rule(lines, kind)
        if rule is None:
            break
        letters += rule
        k -= 1
        kind = "title"
    if not letters:
        return None, ""
    return groups[k][0], letters


def _list_cont(before: Optional[str], line: Optional[str]) -> bool:
    """번호 매김 목록 자리(`numId.ilvl`) line 이 바로 앞 줄 before 의 목록을 같은 수준이나 더 깊은 수준으로 잇는가."""
    if before is None or line is None:
        return False
    (bn, bl), (ln, ll) = before.split("."), line.split(".")
    return bn == ln and int(ll) >= int(bl)


def _introducer(t: str) -> bool:
    """뒤 표지를 소개하는 줄인가 — _introduced 가 소개하는 줄로 읽는 꼴(_intro_form · BARE_ACTION 과 표지 낱말)."""
    return _intro_form(t) is not None or bool(BARE_ACTION.match(t) and _KW_ANY.search(t))


#: 번호 붙은 항목 줄의 번호 앞 머리 낱말(`Observation 1: …` 의 `Observation` · `Proposed Conclusion 12:` 의
#: `Proposed Conclusion`).
_ITEM_HEAD = re.compile(r"^(?:[-–•·▪]\s*)?([A-Za-z]+(?:\s+[A-Za-z]+)?)\s*#?\s*\d")


def _item_head(t: str) -> Optional[str]:
    h = _ITEM_HEAD.match(t)
    return h.group(1).lower() if h else None


def _announced_head(prev: str, t: str) -> Optional[str]:
    """t 가 바로 앞 글 줄 prev 가 결정의 내용으로 알린 항목이면 그 머리 낱말 — prev 가 쌍점으로 끝나고 `following` 뒤에
    t 의 번호 앞 머리 낱말을 적으며, 알린 항목이 아직 논의할 거리라는 말(_PENDING_ANNOUNCE)이 없다."""
    head = _item_head(t)
    if head is None or not prev.rstrip().endswith((":", "：")) or _PENDING_ANNOUNCE.search(prev):
        return None
    return head if re.search(rf"\bfollowing\b[^.;]*?\b{re.escape(head)}", prev, re.IGNORECASE) else None


def content_end_reason(rows: Iterable[tuple[int, str, bool, bool]], mark: Mark, stop: int, kinds=tuple(KEYWORDS),
                       companies: frozenset = frozenset(), enclosed: bool = False, quoted: bool = False,
                       own: Optional[tuple[str, int, bool]] = None,
                       lists: Optional[Sequence[Optional[str]]] = None) -> tuple[int, str]:
    """본문의 끝 위치와 그 위치를 선택한 사유를 반환한다.

    hard, 2blank, mark, markgroup, disc, speaker, decision, done, email,
    entry, notagreed, opener, proposal, open, rule, item, trailer, issue,
    session, numsib, stop으로 종료 조건을 구분한다. 제목 묶음을 함께 제외하면
    사유에 +와 제목 규칙 문자를, 바로 앞에 붙은 제목을 제외하면 ~와 규칙 문자를 붙인다.

    enclosed는 표지가 앞 결정 본문 안에 있는지, quoted는 다음 문단부터 시작하는
    인용 본문인지 나타낸다. 인용 본문 안에 빈 줄·표 없이 붙은 하위 표지는 본문에 둔다.
    변경 문구를 소개한 뒤 인용한 앞 결정도 같은 방식으로 유지한다.

    새 쟁점·진행 단계·진행자 줄은 본문 종료 후보다. 본문이 쟁점 목록으로
    시작했거나 앞 문장이 해당 목록을 소개하면 같은 목록의 후속 쟁점은 유지한다.
    제안도 본문 자체의 목록, 명시적으로 소개한 목록, 같은 글머리표의 연속 항목,
    합의됐다고 적힌 항목이면 유지한다. 표지에 출처 덧말만 붙은 경우는 본문이
    같은 줄에서 시작한 것으로 보지 않는다.

    own은 현재 회의의 meeting_key이고 lists는 문단별 번호 매김 식별자
    `numId.ilvl` 또는 None이다. 세부 종료 규칙은 모듈 설명과 각 판정 함수를 따른다."""
    prev = mark.inline or mark.lead or ""
    blanks = 0
    started = mark.inline is not None
    last_blank = None
    group_head = False
    own_proposal = bool(mark.inline and PROPOSAL_LINE.match(mark.inline))
    own_recommendation = bool(mark.inline and RECOMMENDATION_LINE.match(mark.inline))
    own_open = bool(mark.inline and OPEN_ITEM.search(mark.inline))
    own_forward = False
    group_own = bool(OWN_FORWARD.search(prev) or FORWARD.search(prev))
    own_ls = False
    group_ls = bool(OWN_LS.search(prev))
    group_forward = False
    colon = prev.rstrip().endswith((":", "："))
    head_line = ""
    group_cont = False
    said = (mark.inline or mark.lead or "").lower()
    framed = bool(FRAME_ANNOUNCE.search(prev))
    #: 지금 이어지는 빈 줄 · 가로줄 묶음의 첫 줄과 그 안에 가로줄이 있는가 · 빈 줄마다 그 앞에 붙은 가로줄 묶음의 첫 줄.
    run, ruled, ruled_before = None, False, {}
    #: 빈 줄로 나뉜 묶음들 — _title_back 의 꼴. 첫 묶음은 표지 줄의 본문부터다.
    groups = [[None, [mark.inline] if mark.inline else [], False, False, mark.inline or mark.lead]]
    #: 빈 줄 뒤 묶음 첫 줄이 바로 앞 글 줄과 같은 글머리표로 열면 그 글자(같은 목록이 빈 줄을 사이에 두고 이어진다),
    #: 그 묶음에서 그 글머리표가 처음 끊긴 줄.
    sib_glyph, sib_stop = None, None
    #: 앞 결정 목록 안의 글머리표 항목 표지면 그 글머리표 — 같은 글머리표를 단 다음 항목이나 번호 붙은 제안 · 권고 줄
    #: (목록 위 층의 다음 항목)에서 끝난다(쌍점으로 끝나는 표지 줄은 그 항목들이 본문이다).
    item_glyph = (mark.bullet if enclosed and not (mark.inline or "").rstrip().endswith((":", "：")) else None)
    #: 목록 안 항목 표지를 건너 읽을 때 — 첫 항목 표지에서 끝냈을 자리, 항목 표지 밖의 제 본문이 있었는가, 지금 읽는 줄이
    #: 든 항목 표지의 글머리표. 제 본문 없이 항목 표지뿐이면 첫 항목 표지에서 끝낸다.
    item_fallback, own_seen, in_item = None, mark.inline is not None, None
    #: 본문 시작 전 발언 줄 묶음을 읽는 중인가, 아직 의장 줄이 없으면 그 묶음 첫 줄에서 끝낸 자리.
    spk_run, spk_hold = False, None
    #: 본문 시작 전 Tdoc 항목 줄을 읽었을 때 그 줄에서 끝낸 자리 — 다음 줄이 결정 글 `Decision:` 줄이 아니면 돌려준다.
    entry_hold = None
    #: 바로 앞 줄이 내용으로 읽은 결정 글 `Decision:` 줄인가 — 그 뒤 Tdoc 항목 줄도 다음 결정 글 줄을 기다려 읽는다.
    #: 머리말이 가리켜 받은 Tdoc 항목 목록을 읽는 중인가 — 빈 줄 전까지 항목 사이 주석 줄 뒤의 항목 줄도 목록이다.
    pair_run, entry_list = False, False
    #: 바로 앞 덩어리가 표인가 — 머리말이 가리킨 것은 그 표라 표 뒤 Tdoc 항목 줄은 머리말을 이어 받지 않는다.
    tabled = False
    #: 바로 앞 줄이 글 줄인가(빈 줄 · 표 · 가로줄이 아니다).
    joined = False
    #: 쟁점 머리 줄을 본문으로 받았는가 — 받은 뒤의 쟁점 머리 줄도 같은 목록이다.
    issue_ok = bool(mark.inline and ISSUE_HEAD.match(mark.inline))
    #: 본문으로 읽은 번호 붙은 항목 줄의 번호들(번호 꼴마다 읽은 차례), 지금 묶음이 본문의 번호 목록을 잇는가,
    #: 빈 줄이 둘 이어져 끝낼 자리 — 그 뒤 첫 글 줄이 본문의 번호 목록을 이으면 끝내지 않는다.
    nums: dict[str, list[int]] = {}
    num_run, held2 = False, None
    #: 빈 줄 · 표 · 가로줄 없이 바로 앞 글 줄에 붙어 이어진 이름표 줄(_title_rule 의 a · b) 묶음의 첫 줄, 그 규칙 글자들,
    #: 그 묶음 앞에 본문이 있었는가. 바로 앞 줄이 글 줄(표지 줄 포함)인가와 그 줄의 번호 매김 목록 자리.
    tail_at, tail_letters, tail_body = None, "", False
    stuck, prev_list, first = True, None, True
    #: 표지 줄에 마침표로 끝나는 본문이 함께 적혔는가(그 본문이 번호 항목이 아니다) — 본문이 열지 않은 번호 꼴의 2 이상
    #: 번호 항목은 바깥 목록의 다음 항목이다. 바로 앞 글 줄이 결정의 내용으로 알린 항목의 머리 낱말(_announced_head).
    closed = bool(mark.inline and mark.inline.rstrip().endswith((".", "。")) and not _num_item(mark.inline))
    announced = None
    if mark.inline and _num_item(mark.inline):
        k, v = _num_item(mark.inline)
        nums[k] = [v]

    def num_cont(t: str) -> bool:
        """t 가 본문의 번호 목록을 잇는 항목 줄인가 — 같은 꼴의 번호가 본문의 첫 번호보다 크고 아직 읽지 않은 번호다
        (1 로 다시 열면 새 목록이다)."""
        n = _num_item(t)
        return n is not None and n[0] in nums and n[1] > nums[n[0]][0] and n[1] not in nums[n[0]]

    def end(at: int, why: str) -> tuple[int, str]:
        if spk_hold is not None:
            return spk_hold
        if entry_hold is not None:
            return entry_hold
        if item_fallback is not None and not own_seen:
            return item_fallback
        if at in ruled_before:
            return ruled_before[at], why
        return (run if ruled and run < at else at), why

    def group_cut(at: int) -> int:
        """at 줄에서 끝낼 때 끝 자리 — 첫 묶음이면 그 줄, 빈 줄 뒤 묶음이면 그 묶음 앞 빈 줄, 앞 목록을 잇는 묶음이면
        목록 항목 뒤(글머리표가 끊긴 줄, 끊기지 않았으면 그 줄)."""
        if last_blank is None or num_run:
            return at
        if sib_glyph is None:
            return last_blank
        return at if sib_stop is None else sib_stop

    def back(at: int, why: str) -> tuple[int, str]:
        """종료 위치 앞의 제목 묶음을 찾아 본문에서 제외한다.

        뒤 문서·표지·발언의 제목인 줄들이 빈 줄 없이 이어지면 그 첫 줄을 반환하고
        사유에 ~와 제목 규칙 문자를 붙인다. 같은 번호 매김 목록의 항목이거나,
        앞 문장이 쌍점으로 뒤 목록을 소개하거나 후속 표지를 소개하는 줄이면
        현재 결정 본문으로 유지한다."""
        if why in _TITLE_ENDS and tail_at is not None and tail_body and at > tail_at:
            return end(tail_at, f"{why}~{tail_letters}")
        if why in _TITLE_ENDS and last_blank is not None and (group_head or at == last_blank):
            title, letters = _title_back(groups, why if group_head else "title")
            if letters:
                return end(title, f"{why}+{letters}")
        return end(at, why)

    for idx, text, blank, hard in rows:
        t = text.strip()
        if first:
            first = False
            prev_list = lists[idx - 1] if lists is not None and 0 < idx <= len(lists) else None
        if entry_hold is not None and (hard or not _decision_note(t)):
            return entry_hold
        if spk_run and (hard or not t or not speaker_comment(t, companies)):
            if spk_hold is not None:
                return spk_hold
            spk_run = False
        if held2 is not None:
            if t and num_cont(t):
                held2 = None
            elif t or hard or not blank:
                return held2
        if hard:
            return end(idx, "hard")
        if not t:
            pair_run = entry_list = joined = stuck = False
            tail_at = None
            if blank:
                if ruled:
                    ruled_before[idx] = run
                if run is None:
                    run = idx
                blanks += 1
                if blanks >= 2:
                    if not nums:
                        return back(idx - 1, "2blank")
                    if held2 is None:
                        held2 = back(idx - 1, "2blank")
                    continue
                if started:
                    last_blank = idx
                    group_head = True
                    groups.append([idx, [], False, False, None])
                    sib_glyph, sib_stop, num_run = None, None, False
            else:
                tabled = True
                groups[-1][2], groups[-1][4] = True, None
                run, ruled = None, False
                blanks = 0
                started = True
                own_seen = own_seen or in_item is None
                group_head = False
                colon = False
            continue
        blanks = 0
        if RULE_LINE.match(t):
            joined = stuck = False
            tail_at = None
            if run is None:
                run = idx
            ruled = True
            if started and not framed and not FRAME_LEAD.search(prev):
                return end(group_cut(idx), "rule")
            framed = True
            groups[-1][2], groups[-1][4] = True, None
            continue
        g = _GLYPH.match(t)
        glyph = g.group(1) if g else None
        if group_head:
            pg = _GLYPH.match(prev)
            sib_glyph = glyph if glyph is not None and pg is not None and pg.group(1) == glyph else None
            sib_stop = None
            num_run = num_cont(t)
        elif sib_glyph is not None and sib_stop is None and glyph != sib_glyph:
            sib_stop = idx
        in_run = (sib_glyph is not None and sib_stop is None) or num_run
        if item_glyph is not None and (glyph == item_glyph or PROPOSAL_LINE.match(t) or RECOMMENDATION_LINE.match(t)):
            return end(idx if last_blank is None else last_blank, "item")
        if group_head:
            head_line = t
            lab = HEAD_LABEL.match(t)
            group_cont = bool(lab and re.search(rf"(?<!\w){re.escape(lab.group(1).lower())}(?!\w)", said))
            groups[-1][3] = group_cont
            group_forward = colon
            own_forward = own_forward or group_own
            own_ls = own_ls or group_ls
            group_own = group_ls = False
        group_forward = group_forward or bool(FORWARD.search(t) or OWN_FORWARD.search(t))
        m = classify(t, kinds)
        item = (m is not None and mark.bullet is None and m.bullet is not None and m.inline is not None
                and (not group_head or in_run))
        if item:
            if item_fallback is None and not own_seen:
                item_fallback = (back(idx, "mark") if last_blank is None or group_head
                                 else back(group_cut(idx), "markgroup"))
        elif m is not None and (
                (quoted and m.inline is not None and joined and quote_form(t, own) is None)
                or (not quoted and framed and joined and quote_form(t, own) == "quote")
                or (not quoted and not started and mark.inline is None and m.inline is None
                    and quote_form(t, own) == "quote")):
            pass
        elif m is not None or opens_block(t, kinds):
            if last_blank is None or group_head:
                return back(idx, "mark")
            return back(group_cut(idx), "markgroup")
        cut = group_cut(idx)
        n_item = _num_item(t)
        if closed and n_item is not None and n_item[1] >= 2 and n_item[0] not in nums:
            return end(cut, "numsib")
        if ISSUE_HEAD.match(t):
            if started and not issue_ok and (group_head or tabled or not (colon or ISSUE_INTRO.search(prev))):
                return back(cut, "issue")
            issue_ok = True
        if started and SESSION_LINE.match(t):
            return back(cut, "session")
        if _is_head(t, "discussion"):
            return back(cut, "disc")
        if TOPIC_TAIL.match(t) or INPUT_HEAD.match(t) or MODERATOR_LINE.match(t):
            return back(last_blank if group_head and last_blank is not None else idx, "trailer")
        paired, listed = False, False
        if speaker_comment(t, companies):
            chair = CHAIR_LINE.match(t)
            if not started and not spk_run:
                spk_run, spk_hold = True, (None if chair else back(cut, "speaker"))
            elif not spk_run or (not chair and spk_hold is None):
                return back(cut, "speaker")
            elif chair:
                spk_hold = None
        elif entry_list and ENTRY_LINE.match(t) and not summary_entry(t):
            listed = True
        elif ends_content(t, "" if tabled else prev):
            why = ("decision" if _is_head(t, "decision") or BARE_DISPOSITION.match(t)
                   else "done" if EMAIL_DONE.match(t)
                   else "email" if EMAIL_ASSIGNMENT.match(t) else "entry")
            if why == "decision" and _decision_note(t) and (not started or entry_hold is not None):
                entry_hold, paired = None, True
            elif why == "entry" and (not started or pair_run):
                entry_hold = back(cut, "entry")
            else:
                return back(cut, why)
        elif ENTRY_LINE.match(t) and not t.endswith((":", "：")):
            listed = True
        if NOT_AGREED_FOLLOWING.match(t):
            return back((last_blank if group_head and last_blank is not None and sib_glyph is None and not num_run
                         else idx), "notagreed")
        if last_blank is not None and group_head and not in_run and GROUP_OPENER.match(t):
            if announced is None or _item_head(t) != announced:
                announced = _announced_head(prev, t)
                if announced is None:
                    return back(last_blank, "opener")
        if last_blank is not None and group_head and not in_run and not_agreed_head(t):
            return back(last_blank, "notagreed")
        lead_glyph = LEAD_GLYPH.match(t)
        if started and not own_proposal and not PROPOSAL_INTRO.search(prev) and not re.search(r"\bagreed\b", t, re.I) \
                and not (lead_glyph and prev.startswith(lead_glyph.group())) and (
                (PROPOSALS_HEAD.match(t) and not (last_blank is not None and AGREED_HEAD.match(head_line)))
                or (mark.inline is not None and not NOTE_ONLY.fullmatch(mark.inline) and last_blank is None
                    and PROPOSAL_LINE.match(t))):
            return back(group_cut(idx), "proposal")
        if PROPOSAL_LINE.match(t):
            if (last_blank is not None and not in_run and not own_proposal and not AGREED_HEAD.match(head_line)
                    and not (group_head and announced is not None)):
                return back(group_cut(idx), "proposal")
            own_proposal = True
        elif RECOMMENDATION_LINE.match(t):
            if last_blank is not None and not in_run and not own_recommendation and not AGREED_HEAD.match(head_line):
                return back(group_cut(idx), "proposal")
            own_recommendation = True
        elif OPEN_ITEM.search(t):
            if (last_blank is not None and not in_run and not own_open and not own_forward and not group_forward
                    and not (not group_head and FFS_LEAD.match(prev))
                    and not (own_ls and QUESTION_ITEM.search(t)) and not AGREED_HEAD.match(head_line)
                    and not group_cont):
                return back(group_cut(idx), "open")
            own_open = True
        if item:
            in_item = m.bullet
        elif in_item is None or glyph == in_item:
            own_seen, in_item = True, None
        said += "\n" + t.lower()
        group_own = group_own or bool(OWN_FORWARD.search(t) or FORWARD.search(t))
        group_ls = group_ls or bool(OWN_LS.search(t))
        cur_list = lists[idx] if lists is not None and idx < len(lists) else None
        rule = _title_rule([t], "title")
        if rule in ("a", "b") and (tail_at is not None or not (
                stuck and (colon or _list_cont(prev_list, cur_list)) or _introducer(t))):
            if tail_at is None:
                tail_at, tail_letters, tail_body = idx, "", started
            tail_letters += rule
        else:
            tail_at = None
        prev_list = cur_list
        colon = t.endswith((":", "："))
        group_head = False
        started = True
        prev = t
        tabled = False
        framed = framed or bool(FRAME_MARK.search(t) or FRAME_ANNOUNCE.search(t))
        run, ruled = None, False
        joined = stuck = True
        groups[-1][1].append(t)
        groups[-1][4] = t
        if entry_hold is None:
            pair_run = paired
        entry_list = entry_list or listed
        n = _num_item(t)
        if n is not None:
            nums.setdefault(n[0], []).append(n[1])
    return held2 if held2 is not None else end(stop, "stop")


def content_end(rows: Iterable[tuple[int, str, bool, bool]], mark: Mark, stop: int, kinds=tuple(KEYWORDS),
                companies: frozenset = frozenset(), enclosed: bool = False, quoted: bool = False,
                own: Optional[tuple[str, int, bool]] = None, lists: Optional[Sequence[Optional[str]]] = None) -> int:
    return content_end_reason(rows, mark, stop, kinds, companies, enclosed, quoted, own, lists)[0]


def report_companies(texts: Iterable[str], entry_sources: bool) -> frozenset:
    """문단의 Source 필드에서 발언자 비교 이름을 수집한다.

    entry_sources가 참이면 TDoc 항목의 세 번째 탭 필드도 출처로 읽는다.
    이 옵션은 항목의 세 번째 필드를 출처로 사용하는 WG 진입점에서 지정한다.
    번호·제목만 있거나 표에서 변환한 항목에는 같은 열 의미를 가정하지 않는다."""
    sources = []
    for t in texts:
        if entry_sources and ENTRY_LINE.match(t):
            fields = t.split("\t")
            if len(fields) > 2:
                sources.append(fields[2])
        sources += SOURCE_FIELD.findall(t)
    return speaker_words(sources)


def outcome_item(texts: Sequence[str], i: int, after_block: frozenset) -> bool:
    """문단 i 가 이메일 논의의 산출 목록 머리(OUTCOME_HEAD) 아래, 빈 줄 · 표 없이 이어진 목록 줄인가."""
    j = i
    while j > 0 and j not in after_block:
        j -= 1
        if not texts[j]:
            return False
        if OUTCOME_HEAD.match(texts[j]):
            return True
    return False


_KWC = r"(?:agreements?|conclusions?|working\s*assumptions?|(?-i:WAs?))"
#: WG 이름, 회의 번호, bis 및 전자회의 접미사를 포함하는 회의 식별자.
_TAG = r"(?:TSG[\s-]*)?RAN\s*(?P<wg>\d)?\s*[#-]?\s*(?P<num>\d{2,3})(?![\d.])\s*(?P<bis>bis|b(?![a-z]))?"
_QPREV = r"(?P<prev>(?:previous|last|prior|earlier)\s+(?:RAN\d?\s*)?meetings?)"


def meeting_tag() -> str:
    """회의 식별자의 정규식 조각을 반환한다. wg·num·bis 이름의 그룹을 갖는다."""
    return _TAG


_SRC_VERB = (r"(?:(?:made|reached|achieved|agreed|copied|excerpted|extracted|taken|quoted)\s+)?"
             r"(?:in|from|at|during|of|@)?")
#: 결정어 뒤에 번호·괄호·출처 동사·전치사와 앞 회의 식별자가 이어지는 인용 표지.
QUOTE_HEAD = re.compile(rf"^\W*{_KWC}\s*(?:#?\s*\d+[a-z]?\s*)?(?:\(\s*)?{_SRC_VERB}\s*(?:the\s+)?(?:{_QPREV}\s*)?"
                        rf"(?:{_TAG})?", re.IGNORECASE)
#: 다른 위치에 이미 있는 결정을 참고용으로 다시 적었음을 명시하는 표지.
#: 앞 회의뿐 아니라 현재 회의의 다른 세션에서 나온 결정도 포함한다.
REF_HEAD = re.compile(rf"^\W*{_KWC}\b.*\bfor\s+(?:your\s+)?reference\b", re.IGNORECASE)
#: 앞 결정을 이번 회의에서 확정·수정한다고 적으면 현재 회의의 결정으로 분류한다.
QUOTE_ACTION = re.compile(r"\b(?:re)?confirm|\bupdat|\brevis|\bmodif|\bamend|\bsupersed|\breplac|\bcorrect|\bclarif"
                          r"|\bchang|\bremov|\bdelet|\brevert|\boverrid", re.IGNORECASE)
#: 회의록 파일명 줄기에서 WG·회의 번호·bis 여부를 찾는다.
MEETING_STEM = re.compile(r"^RAN(\d)-(\d+)[-_]?(b|bis)?", re.IGNORECASE)
#: 인용한 앞 결정을 현재 회의에서 추가 설명하는 문장이 있으면 인용 표지도 결과에 포함한다.
CLARIFY_LINE = re.compile(r"^(?:clarifications?|updates?|corrections?|modifications?)\b"
                          r"(?:\s+(?:of|to|on)\s+(?:the\s+)?(?:above|this|that)\b[^:：]*)?\s*[:：]", re.IGNORECASE)


def meeting_key(stem: str) -> Optional[tuple[str, int, bool]]:
    """회의록 파일 줄기의 (WG 숫자, 회의 번호, bis 인가). 읽지 못하면 None."""
    m = MEETING_STEM.match(stem)
    return (m.group(1), int(m.group(2)), bool(m.group(3))) if m else None


def quote_form(text: str, own: Optional[tuple[str, int, bool]] = None) -> Optional[str]:
    """인용 표지의 분류를 반환한다. 쌍점 앞 텍스트만 검사한다.

    action은 앞 결정을 이번 회의에서 확정·수정하는 경우다. same은 표지의
    회의 식별자가 own과 같은 경우다. quote는 앞 결정의 인용 또는 참고용 재기재다."""
    h = re.split(r"[:：]", text, maxsplit=1)[0]
    m = QUOTE_HEAD.match(h)
    if not (m and (m.group("prev") or m.group("num"))) and not REF_HEAD.match(h):
        return None
    if QUOTE_ACTION.search(h):
        return "action"
    if m and m.group("num") and m.group("wg") and own and (m.group("wg"), int(m.group("num")), bool(m.group("bis"))) == own:
        return "same"
    return "quote"


#: 앞 결정 본문이 뒤 표지를 소개하는 꼴 — 뒤를 가리키는 말과 표지 낱말. following 과 표지 낱말 사이에는 전치사 ·
#: 접속사 · 관계사가 아닌 꾸밈말을 다섯까지 둔다.
_INTRO_MODS = (r"(?:(?![(\[]?(?:to|of|in|from|at|on|for|by|with|into|onto|regarding|about|between|under|and|or|that"
               r"|which)\b)[\w\-/#().,’'\[\]]+\s+){0,5}?")
INTRO_FORMS = (
    ("following", re.compile(rf"\bfollowing\s+{_INTRO_MODS}(?P<kw>{_KWC})\b", re.IGNORECASE)),
    ("below", re.compile(rf"\bbelow\s+(?P<kw>{_KWC})\b", re.IGNORECASE)),
    ("kw-below", re.compile(rf"\b(?P<kw>{_KWC})\s+\(?(?:(?:is|are|was|were)\s+)?(?:(?:copied|listed|shown|captured|given"
                            rf"|quoted|provided|repeated|included|pasted)\s+)?below\b", re.IGNORECASE)),
    ("as-follows", re.compile(rf"\b(?P<kw>{_KWC})\b(?:[^.;:]|\.(?=\d))*?\bas\s+(?:(?:shown|listed|captured|copied|given"
                              rf"|indicated|described|quoted|provided)\s+)?(?:follows|below|per\s+below|followings?)\b",
                              re.IGNORECASE)),
    ("with-following", re.compile(rf"\b(?P<kw>{_KWC})\b(?:[^.;:]|\.(?=\d))*?\bwith\s+(?:the\s+)?following\s+(?:\w+\s+)?"
                                  rf"(?:modifications?|updates?|changes?|revisions?|corrections?|clarifications?)"
                                  rf"\s*[:：]?\s*$", re.IGNORECASE)),
)
_COLON_END = re.compile(r"[:：]\s*$")
_KW_ANY = re.compile(rf"\b{_KWC}\b", re.IGNORECASE)
#: 뒤를 가리키는 말 없이 확정만 적은 줄(`Confirm the WA.` · `To confirm the working assumption`).
BARE_ACTION = re.compile(r"^\W*(?:to\s+)?(?:re)?confirm(?:ation\s+of|ing|s|ed)?\b", re.IGNORECASE)
#: 앞 결정을 이르는 말 — 앞 회의 · 회의 꼬리표.
PREV_REF = re.compile(r"\b(?:previous(?:ly)?|earlier|prior|last|existing|past|original)\b|RAN\s*\d?\s*#\s*\d+"
                      r"|\bRAN\d?[\s-]*\d{2,3}(?:bis|b)?(?:-e)?\b", re.IGNORECASE)
#: 소개하는 문장이 결정에 가하는 일 — 표지 낱말 앞 동작 말, 뒤 수동 꼴, 뒤 명사 꼴.
_ACTIVE = re.compile(r"\b(?:re)?confirm\w*|\bupdat\w*|\brevis\w*|\bmodif\w*|\bclarif\w*|\breplac\w*|\brevert\w*"
                     r"|\bremov\w*|\bamend\w*|\bcorrect\w*|\bturn\w*|\badopt\w*|\bre-?us\w*|\bfollow(?:s|ed)?\b"
                     r"|\bkeep\w*|\bmaintain\w*|\bretain\w*|\bnot\s+chang\w*|\btak(?:e|en|ing)\b"
                     r"|\bappl(?:y|ies|ied|ying)\b", re.IGNORECASE)
_PASSIVE = re.compile(r"\b(?:is|are|was|were|be|been|being|gets?|got)\s+(?:\w+\s+){0,2}?(?:re)?(?:confirmed|updated"
                      r"|revised|modified|clarified|replaced|reverted|removed|amended|corrected|adopted|re-?used|taken"
                      r"|kept|maintained|changed|superseded|overridden|followed|applied)\b", re.IGNORECASE)
_POST = re.compile(r"\b(?:re)?confirm\w*|\bappl(?:y|ies)\b|\b(?:update|revision|modification|clarification|correction)s?\b",
                   re.IGNORECASE)
_SENT = re.compile(r"[.;]\s+(?=[A-Z])")
#: 후속 작업 가정을 확정할 필요가 없다는 표현은 확정·수정 동작으로 취급하지 않는다.
_NO_NEED = re.compile(r"(?:\b(?:not|n['’]t)\s+(?:\w+\s+)?(?:need|necessar\w*|requir\w*)|\bno\s+need)\s+(?:to\s+)?(?:be\s+)?"
                      r"(?:re)?confirm", re.IGNORECASE)
#: 마침표가 문장을 끝내지 않는 앞 낱말 — 줄임말(`Fig.` · `etc.` · `e.g.`).
_ABBR = re.compile(r"^[A-Z][a-z]{1,3}$|^(?:etc|vs|cf|al|approx|incl|resp)$|\.")
_NUMW = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
         "both": 2}
_DET = {"the", "a", "an", "this", "that", "these", "those", "its", "their", "our", "such"}
_INTRO_BEFORE = _DET | {"all", "with", "of", "in", "on", "for", "to", "by", "per", "as", "into", "under", "at"} | set(_NUMW)
_REPLACE_NEW = re.compile(r"\breplac\w*\b[^.;]*\b(?:with|by)\s+(?:the\s+)?following\b", re.IGNORECASE)
_MOD_COLON = re.compile(r"(?:modifications?|updates?|changes?|revisions?|corrections?|clarifications?)\s*[:：]\s*\S",
                        re.IGNORECASE)
_GEN_FWD = re.compile(r"\bas\s+follows\b|\bbelow\b|\bfollowing\b", re.IGNORECASE)
_SECOND = re.compile(r"\bfollowing\s+(?P<noun>[A-Za-z]+)", re.IGNORECASE)


def _prepositional(line: str, m: re.Match) -> bool:
    """following 이 전치사(…에 따라)로 쓰였는가: 뒤 낱말이 한정사이거나, 앞 낱말이 한정사 · 수 · 전치사 · 동작 말이
    아니고 줄머리나 문장부호 뒤도 아니다."""
    after = line[m.start() + len("following"):].split()
    if after and after[0].lower() in _DET:
        return True
    before = line[:m.start()].rstrip()
    if not before or before[-1] in ",:;(\u201c\"'":
        return False
    w = before.split()[-1].lower().strip("(\"'\u201c")
    return not (w in _INTRO_BEFORE or _ACTIVE.fullmatch(w))


def _sentence(line: str, pos: int) -> tuple[str, int]:
    """pos 가 든 문장과 그 시작 자리. 줄임말 뒤 마침표에서는 나누지 않는다."""
    a = 0
    for m in _SENT.finditer(line):
        if line[m.start()] == ".":
            tok = line[:m.start()].split()[-1:] or [""]
            if _ABBR.search(tok[0].lstrip("([\"'")):
                continue
        if m.end() <= pos:
            a = m.end()
        else:
            return line[a:m.start()], a
    return line[a:], a


def _kind_of(word: str) -> str:
    w = word.lower()
    return "agreement" if w.startswith("agree") else "conclusion" if w.startswith("concl") else "working_assumption"


def _budget(sent: str) -> dict:
    """문장의 표지 낱말마다 종류별로 소개하는 표지 수: 단수 1, 앞 세 낱말 안에 수 낱말이 있으면 그 수, 수 없는 복수는
    끝없음. 수 없는 복수 agreements 는 결정 전체를 두루 이르는 말이라 결론 · 작업 가정도 끝없이 받는다."""
    out, umbrella = {}, False
    for k in _KW_ANY.finditer(sent):
        w = k.group()
        n = None
        for tok in sent[:k.start()].split()[-3:]:
            t = tok.lower().strip("(),")
            if t in _NUMW:
                n = _NUMW[t]
            elif t.isdigit():
                n = int(t)
        if n is None:
            n = float("inf") if w.lower().endswith("s") else 1
            umbrella = umbrella or (w.lower().startswith("agree") and n == float("inf"))
        kd = _kind_of(w)
        out[kd] = max(out.get(kd, 0), n)
    if umbrella:
        for kd in ("conclusion", "working_assumption"):
            out[kd] = float("inf")
    return out


def _intro_form(line: str):
    """줄이 뒤 표지를 소개하는 꼴이면 (꼴, 문장, 문장 안 표지 낱말 끝 자리, 문장의 표지 종류들, 꼴 뒤 글), 아니면 None.
    INTRO_FORMS 가운데 줄에서 가장 앞에 걸린 꼴을 쓰고, 없으면 표지 낱말을 품고 쌍점으로 끝나는 줄을 `colon` 꼴로 읽는다."""
    hits = []
    for name, rx in INTRO_FORMS:
        for m in rx.finditer(line):
            if name == "following" and _prepositional(line, m):
                continue
            hits.append((m.start(), name, m))
            break
    if hits:
        _, name, m = min(hits, key=lambda h: h[0])
        sent, a = _sentence(line, m.start("kw"))
        return name, sent, m.end("kw") - a, {_kind_of(x) for x in _KW_ANY.findall(sent)}, line[m.end():]
    if _COLON_END.search(line) and _KW_ANY.search(line):
        kws = list(_KW_ANY.finditer(line))
        sent, a = _sentence(line, kws[-1].start())
        return "colon", sent, kws[-1].end() - a, {_kind_of(x) for x in _KW_ANY.findall(sent)}, ""
    return None


def _relation(sent: str, kw_end: int) -> Optional[str]:
    """소개하는 문장이 결정과 맺는 관계 — 앞 결정을 이른다(prev), 표지 낱말 앞 동작 말(active), 뒤 수동 꼴(passive),
    뒤 명사 꼴(post). 앞 결정을 이르지 않고 확정이 필요 없다고만 적으면(_NO_NEED) 뒤 표지는 이번 회의의 새 결정이라 None."""
    if PREV_REF.search(sent):
        return "prev"
    if _NO_NEED.search(sent):
        return None
    if _ACTIVE.search(sent[:kw_end]):
        return "active"
    if kw_end and _PASSIVE.search(sent[kw_end - 1:]):
        return "passive"
    if _POST.search(sent[kw_end:]):
        return "post"
    return None


def _open_end(line: str) -> bool:
    """줄의 마지막 문장이 뒤를 가리키는 말(as follows · below · 전치사가 아닌 following)을 품고, 그 뒤에 쌍점 다음 글이
    없다."""
    sent, _ = _sentence(line, len(line))
    for m in _GEN_FWD.finditer(sent):
        if m.group().lower() == "following" and _prepositional(sent, m):
            continue
        if not re.search(r"[:：]\s*\S", sent[m.end():]):
            return True
    return False


def _second_nouns(line: str) -> set:
    """소개하는 줄이 표지 낱말 밖에 따로 예고한 이름들(`… with the following note` → note)."""
    out = set()
    for m in _SECOND.finditer(line):
        w = m.group("noun").lower()
        if _prepositional(line, m) or _KW_ANY.fullmatch(w) or w in _DET:
            continue
        out.add(w.rstrip("s"))
    return out


def _introduced(ys: Sequence[tuple[int, Mark, int, Optional[str]]], texts: Sequence[str],
                after_block: frozenset) -> tuple[set, dict]:
    """앞 결정이 소개한 후속 표지 인덱스와 확장된 본문 끝 위치를 반환한다.

    ys 항목은 (문단 번호, Mark, 본문 끝, quote_form)이다. 인접한 표지 가운데
    앞 본문이 해당 종류·개수를 소개하고 확정·수정 동작 또는 앞 결정의 참조를
    설명한 경우를 포함한다. 사이 문장이 소개된 내용을 설명할 때에도 포함할 수 있다.
    인용 표지는 사이 문장이 있어도 앞 결정에 포함한다. 이미 포함된 표지나
    앞 줄의 쉼표 뒤에 이어지는 표지는 소개 개수를 추가로 사용하지 않는다."""
    absorbed, ext = set(), {}

    def span_lines(k):
        j, mj, je = ys[k][:3]
        nxt = ys[k + 1][0] if k + 1 < len(ys) else len(texts)
        return ([(j, mj.inline)] if mj.inline else []) + [(x, texts[x]) for x in range(j + 1, min(je, nxt)) if texts[x]]

    #: [대표 표지의 ys 인덱스, 본문 끝, 본문 줄, 남은 소개 개수, 소개 문단, 포함된 표지의 문단 집합]
    E = None
    k = 0
    while k < len(ys):
        i, m, e, qf = ys[k]
        if E is None or E[1] > i or any(texts[x] for x in range(E[1], i)) or not E[2]:
            E = [k, e, span_lines(k), None, None, set()]
            k += 1
            continue
        content = E[2]
        last = content[-1][0]
        lstar, fw = None, None
        for x, t in reversed(content):
            fw = _intro_form(t)
            if fw:
                lstar = x
                break
        lt = dict(content).get(lstar, content[-1][1])
        gap = any(not texts[x] for x in range(last + 1, i))
        take, carry, bud, lk, left, run = False, None, {}, set(), {}, []
        if fw is None:
            kw = _KW_ANY.search(content[-1][1])
            if (BARE_ACTION.match(lt) and kw and not re.search(r"[:：]\s*\S", lt) and not gap and last + 1 == i
                    and _kind_of(kw.group()) == m.kind):
                take, lstar, bud = True, last, _budget(lt)
        else:
            form, sent, kw_end, lk, rest = fw
            rel = _relation(sent, kw_end) or ("quote" if qf == "quote" else None)
            bud = _budget(sent)
            take = not (any(x in after_block for x in range(lstar + 1, i + 1))
                        or (re.search(r"[:：]\s*\S", rest) and not _MOD_COLON.search(rest))
                        or (re.search(r"\babove\b", lt, re.IGNORECASE) and not PREV_REF.search(lt) and len(content) > 1)
                        or (form == "following" and _REPLACE_NEW.search(sent))
                        or not rel
                        or not (m.kind in lk or bud.get(m.kind, 0) > 0
                                or ("working_assumption" in lk and m.kind == "agreement")))
            if lstar != last and qf != "quote":
                mid = [x for x in range(lstar + 1, i) if texts[x]]
                nouns = _second_nouns(lt) if form != "colon" else set()
                heads = {re.match(r"\W*(\w*)", texts[x]).group(1).lower().rstrip("s") for x in mid}
                if (E[4] == lstar and i not in after_block and all(x in E[5] for x in mid) and E[3]
                        and E[3].get(m.kind, 0) > 0 and nouns - heads):
                    take, carry = True, dict(E[3])
                elif not (take and ((nouns and heads <= nouns) or (not gap and _open_end(texts[mid[-1]])))):
                    take = False
        if take:
            left = carry if carry is not None else dict(bud)
            if carry is None and m.kind not in left and m.kind == "agreement" and "working_assumption" in left:
                left["agreement"] = 1
            prev_end, kk = e, k
            while kk < len(ys):
                j, mj, je = ys[kk][:3]
                if kk > k:
                    if j > prev_end or j in after_block or not texts[j - 1]:
                        break
                    if j < prev_end or texts[j - 1].endswith(","):
                        run.append(kk)
                        kk += 1
                        continue
                    if left.get(mj.kind, 0) <= 0:
                        break
                left[mj.kind] = left.get(mj.kind, 0) - 1
                run.append(kk)
                prev_end = max(prev_end, je)
                kk += 1
            if (carry is None and "working_assumption" in lk and "agreement" not in lk and m.kind == "agreement"
                    and "working_assumption" not in {ys[x][1].kind for x in run}):
                run = []
        if run:
            for x in run:
                j, mj, je = ys[x][:3]
                E[2] = E[2] + span_lines(x)
                E[1] = max(E[1], je)
                E[5].update(range(j, max(je, j + 1)))
                absorbed.add(x)
            ext[E[0]] = E[1]
            E[3], E[4] = left, lstar
            k = run[-1] + 1
        else:
            E = [k, e, span_lines(k), None, None, set()]
            k += 1
    return absorbed, ext


#: 소개하는 줄이 뒤 결정을 가리키는 말 — `following … 표지 낱말`(전치사 꼴 `in the following agreement` 도) ·
#: `below 표지 낱말` · `표지 낱말 … below / as follows`.
_LEAD_FWD = re.compile(rf"\bfollowing\s+(?:[\w\-/#().,’'\[\]]+\s+){{0,5}}?{_KWC}\b|\bbelow\s+{_KWC}\b"
                       rf"|\b{_KWC}\b[^.;:]*?\b(?:below|as\s+follows)\b", re.IGNORECASE)
#: 후속 결정을 문서에 포함하거나 전달하도록 지시하는 소개 문장.
_LEAD_ORDER = re.compile(r"^\W*(?:to\s+)?(?:include|send|provide|attach|inform|reply|respond|answer)\b", re.IGNORECASE)


def lead_source(line: str, own: Optional[tuple[str, int, bool]]) -> Optional[str]:
    """표지 앞 문장이 후속 결정의 출처를 설명하면 quote 또는 restated를 반환한다.

    후속 결정을 가리키는 마지막 문장에 회의 식별자가 있고 확정·수정·전달 지시가
    없어야 한다. 현재 회의 외의 식별자가 있으면 quote, 모두 현재 회의면 restated다.
    표지 자체의 출처를 검사하는 quote_form을 앞 문장에도 적용하는 판정이다."""
    for sent in reversed([x for x in _SENT.split(line) if x.strip()]):
        if not _LEAD_FWD.search(sent):
            continue
        tags = [m for m in re.finditer(_TAG, sent, re.IGNORECASE) if m.group("num")]
        if not tags or _ACTIVE.search(sent) or QUOTE_ACTION.search(sent) or _LEAD_ORDER.match(sent):
            return None
        if own and any((m.group("wg") or own[0], int(m.group("num")), bool(m.group("bis"))) != own for m in tags):
            return "quote"
        return "restated"
    return None


def lead_form(texts: Sequence[str], i: int, own: Optional[tuple[str, int, bool]], after_block: frozenset = frozenset(),
              kinds=tuple(KEYWORDS)) -> Optional[str]:
    """표지 직전의 비어 있지 않은 문장에 lead_source를 적용한다.

    사이에 표 같은 비문자 본문이 있거나 직전 문장도 결정 표지이면 None이다.
    앞 문장이 가리키는 표와 그 다음의 새 결정 표지를 분리하기 위한 조건이다."""
    p = i - 1
    while p >= 0 and not texts[p]:
        p -= 1
    if p < 0 or any(x in after_block for x in range(p + 1, i + 1)) or classify(texts[p], kinds) is not None:
        return None
    return lead_source(texts[p], own)


#: Summary of로 시작하는 결정 요약 절 제목.
SUMMARY_HEAD = re.compile(r"^\W*summary\s+of\b", re.IGNORECASE)


def head_form(head: str, own: Optional[tuple[str, int, bool]]) -> Optional[str]:
    """현재 절이 결정 요약 절인지 확인해 출처 분류를 반환한다.

    요약 제목에 현재 회의 외의 식별자가 있으면 quote, 그 외에는 restated다.
    요약 절이 아니면 None이다. 앞 문장을 검사하는 lead_source와 달리 절 제목을 검사한다."""
    if not SUMMARY_HEAD.match(head):
        return None
    tags = [m for m in re.finditer(_TAG, head, re.IGNORECASE) if m.group("num")]
    if own and any((m.group("wg") or own[0], int(m.group("num")), bool(m.group("bis"))) != own for m in tags):
        return "quote"
    return "restated"


def unseen_lines(lines: Sequence[str], earlier: Iterable[str]) -> list[str]:
    """공백을 한 칸으로 정규화한 뒤 earlier에 없는 lines의 줄들을 반환한다."""
    seen = {" ".join(x.split()) for x in earlier}
    return [y for y in (" ".join(x.split()) for x in lines) if y not in seen]


def reprinted(lines: Sequence[str], earlier: Iterable[str]) -> bool:
    """다시 적은 결정의 글 줄이 모두 앞서 읽은 결정 본문 줄에 있는가 — `restated` 표지는 그때만 내지 않는다(원본이
    따로 읽히지 않았으면 그 표지가 유일한 기록이다)."""
    return bool(lines) and not unseen_lines(lines, earlier)


#: WG 이름이 결정어와 직접 연결되면 그 WG의 결정을 가리킨다.
#: 같은 문장의 다른 위치에 수신 대상 WG만 등장하는 경우와 구분한다.
#: #가 붙은 회의 식별자는 EXTERNAL_LOCUS가 처리한다.
_WG_DECISION = re.compile(r"\bRAN\s*(\d)\s+(?:agree|conclu|working\s+assum)"
                          r"|(?:agree|conclu)\w*\s+(?:in|by|at)\s+(?:the\s+)?RAN\s*(\d)\b(?!\s*#)", re.IGNORECASE)


def abstract_quote(texts: Sequence[str], hard: Sequence[bool], heads: Sequence[Optional[str]], i: int, j: int,
                   mark: Mark, kinds=tuple(KEYWORDS), companies: frozenset = frozenset(),
                   own_wg: Optional[str] = None) -> bool:
    """초록 필드 안의 표지가 인용·제안·기고자의 결론인지 검사한다.

    heads는 문단별 template_head 필드명이다. 앞선 결정 표지·발언·의장 줄은
    출처 설명으로 사용하지 않는다. own_wg가 주어지면 결정어에 직접 붙은
    다른 WG 이름도 외부 출처로 판정한다."""
    t = texts[i]
    if ABSTRACT_SOURCE.match(t) or ABSTRACT_PROSE.match(t):
        return True
    if MEETING_TAG_LINE.match(next((texts[x] for x in range(i - 1, j, -1) if texts[x]), "")):
        return True
    for x in range(j + 1, i):
        s = texts[x]
        if (s and _DECISION_WORD.search(s)
                and (EXTERNAL_LOCUS.search(s)
                     or (own_wg and any((m.group(1) or m.group(2)) != own_wg for m in _WG_DECISION.finditer(s))))
                and classify(s, kinds) is None
                and not speaker_comment(s, companies) and not CHAIR_LINE.match(s)):
            return True
    if mark.kind != "conclusion":
        return False
    k = next((x for x in range(i + 1, len(texts))
              if heads[x] in ("discussion", "decision") or hard[x] or ENTRY_LINE.match(texts[x])), None)
    return k is not None and heads[k] == "discussion"


def decision_spans(texts: Sequence[str], blank: Sequence[bool], hard: Sequence[bool], after_block: Iterable[int],
                   kinds=tuple(KEYWORDS), companies: frozenset = frozenset(),
                   skip: Iterable[int] = (), abstract_notes: bool = False,
                   meeting: Optional[str] = None,
                   lists: Optional[Sequence[Optional[str]]] = None,
                   spans: Optional[list] = None,
                   restated: Optional[dict] = None) -> Iterator[tuple[int, Mark, int]]:
    """문단 순서대로 (표지 문단 번호, Mark, 본문 끝 번호)를 반환한다.

    texts는 앞뒤 공백을 제거한 문단, blank는 시각적으로 비어 있는 문단 여부,
    hard는 절 제목 여부다. after_block은 직전에 표 같은 비문자 본문이 있는
    문단 번호다. skip의 문단은 표지로 읽지 않지만 앞 결정의 본문에는 포함할 수 있다.

    abstract_notes가 참이면 초록 필드의 모든 표지를 제외하는 대신
    abstract_quote가 인용·제안·맺음말로 분류한 표지만 제외한다.
    제외한 표지도 다른 결정의 본문 경계 판정에 사용한다.

    앞 회의의 인용 표지와 그 안의 하위 표지는 새 결정에서 제외한다.
    현재 회의의 추가 설명(CLARIFY_LINE)이 있으면 그 인용 표지도 반환한다.
    요약에 다시 적은 결정은 앞서 나온 본문과 정규화 후 완전히 겹칠 때 제외한다.
    _introduced가 앞 결정에 포함한 후속 표지는 개별 결과에서 제외하고
    앞 결정의 끝 위치를 확장한다. meeting은 회의록 파일명 줄기이며
    lists는 docx_text.list_keys로 구한 문단별 번호 매김 식별자다.

    spans가 주어지면 제외된 인용·포함 표지까지 모든 표지의 범위를 추가한다.
    문단 사이의 표가 어느 결정 본문에 속하는지 판정할 때 사용한다.
    restated가 주어지면 반환하는 재기재 표지마다 앞서 없었던 정규화 줄들을 기록한다.
    표 안의 재기재 결정은 추출기가 decision_boxes.box_reprints로 추가 검사한다."""
    n = len(texts)
    after_block, skip = frozenset(after_block), frozenset(skip)
    own = meeting_key(meeting) if meeting else None
    heads = [(template_head(t) or (None,))[0] if t else None for t in texts]
    opened, last, section, sec = [], None, [], None
    for x, t in enumerate(texts):
        opened.append(last)
        section.append(sec)
        if heads[x] or hard[x] or ENTRY_LINE.match(t):
            last = x
        if hard[x]:
            sec = x

    def rows(i: int) -> Iterator[tuple[int, str, bool, bool]]:
        for j in range(i + 1, n):
            if j in after_block:
                yield (j, "", False, False)
            yield (j, texts[j], blank[j], hard[j])

    cover, ys = 0, []
    for i, t in enumerate(texts):
        if not t or i in skip:
            continue
        mark = classify(t, kinds)
        if mark is None:
            continue
        if mark.lead is not None and not re.search(r"[:：]", t) and outcome_item(texts, i, after_block):
            continue
        j = opened[i]
        if j is not None and heads[j] == "abstract" and (
                not abstract_notes or abstract_quote(texts, hard, heads, i, j, mark, kinds, companies,
                                                     own[0] if own else None)):
            continue
        qf = (quote_form(t, own) or lead_form(texts, i, own, after_block, kinds)
              or (head_form(texts[section[i]], own) if section[i] is not None else None))
        end = content_end(rows(i), mark, n, kinds, companies, i < cover, qf == "quote" and mark.inline is None, own,
                          lists)
        cover = max(cover, end)
        ys.append((i, mark, end, qf))
    inner = set()
    prior_end = quote_end = 0
    for i, mark, end, qf in ys:
        # Indices increase strictly; prior ends cover [start, end).
        if i < quote_end or (qf == "quote" and i < prior_end):
            inner.add(i)
        prior_end = max(prior_end, end)
        if qf == "quote" and mark.inline is None:
            quote_end = max(quote_end, end)
    ys0 = ys
    ys = [y for y in ys if y[0] not in inner]
    absorbed, ext = _introduced(ys, texts, after_block)
    if spans is not None:
        spans.extend((i, end) for i, _m, end, _q in ys0)
        spans.extend((ys[k][0], end) for k, end in ext.items())
    for k, (i, mark, end, qf) in enumerate(ys):
        if k in absorbed:
            continue
        end = ext.get(k, end)
        if qf == "quote" and not any(CLARIFY_LINE.match(texts[x]) for x in range(i + 1, end)):
            continue
        if qf == "restated":
            lines = [x for x in [mark.inline or ""] + [texts[x] for x in range(i + 1, end)] if x]
            earlier = {x for j, m, je, _q in ys0 if j < i
                       for x in [m.inline or ""] + [texts[y] for y in range(j + 1, min(je, n))] if x}
            if reprinted(lines, earlier):
                continue
            if restated is not None and lines:
                restated[i] = unseen_lines(lines, earlier)
        yield i, mark, end
