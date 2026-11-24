"""TS 제목의 절 번호를 판별하고 부모·자식 계층을 구성한다.

RAN1~RAN5의 TS 파서 10개 진입점(`RAN{1..5}/phase-3/ts-parser/parse_ts_docx.py`와
`RAN{1..5}/phase-7/ts-parser/01_parse_ts_sections.py`)이 공통으로 쓰는 문법과 구조 규칙이다.
TR 파서(`*/phase-9/tr-parser/`)는 번호 문법과 구조 규칙을 함께 쓰고, `cr_clause.py` · `ts_citation.py` 는 번호 문법만 쓴다.
ASN.1 정의명 제목(`– MIB`)처럼 한 WG 에만 있는 제목 꼴은 각 파서가 따로 판정한다.

구조 규칙:
    build_hierarchy        부모 = 존재하는 가장 가까운 번호상 조상 절
    HeadingSequence        문서 순서. 문법이 거절한 제목(`recover`)과 제목 스타일이 아닌 제목(`promote`)을
                            인접한 절 번호의 순서와 일치할 때만 절로 처리한다
    split_repeated_ids     분할 파트마다 반복되는 절 식별자를 `-dupN` 접미사로 구분한다
    split_glued            제목 문단에 공백 없이 붙은 본문 문장을 분리해 해당 절의 본문으로 사용한다

번호 문법이 거절한 제목은 별도 절로 생성되지 않고, 그 본문이 직전 절에 포함될 수 있다.
각 파서가 다른 문법을 사용하면 같은 제목이 KG에서는 독립 절로, VDB에서는 직전 절의
본문으로 처리될 수 있으므로 번호 문법과 계층 구성 규칙을 공유한다.

받아야 하는 번호 꼴:

    5.3B.1.2 · 5.2.3.1s.6      마디 뒤 글자 (글자 뒤 숫자까지)
    4A.1.1.0.1                 첫 마디 뒤 글자
    6.2.1.1_1.3.3_1            시험 규격(38.521-x · 38.508-1)의 변형 절 — 마디마다 `_N`
    A.4.3.2B.2.3.1 · G.1.5.0_1 부속서 번호 안의 글자 마디 · 변형 절
    A.1-1                      부속서 번호 뒤 붙임표 꼬리
"""
from __future__ import annotations

import logging
import re

import docx_text

logger = logging.getLogger(__name__)

#: 절 번호의 두 번째 이후 마디. 숫자·글자 하나·뒤따르는 숫자·변형 절 접미사(`_N`)를 허용한다.
#: 주의: 글자 뒤 숫자는 글자가 있을 때만 허용한다(`[0-9]+[a-zA-Z]?[0-9]*`로 쓰지 않는다). 허용 형식은 같지만,
#: 글자가 없으면 `11` 을 `1`+`1` 로도 `11`+`` 로도 가를 수 있어 매치가 실패할 때 마디마다 갈래가 두 배로
#: 늘어난다. 번호 나열 뒤에 문서가 오는지 보는 인용 문법(`ts_citation`)은 나열이 길고 문서가 없으면
#: 실패하므로, 두 자리 마디가 수십 개인 표 칸(RAN5 38.533 `G.2.6` 의 `All tests in clauses 4.4.3, 4.5,
#: …, 18.3 are delay tests`) 하나에서 파서가 끝나지 않는다.
SEG = r"[0-9]+(?:[a-zA-Z][0-9]*)?(?:_[0-9]+)*"
#: 본문 절 번호. 끝의 `.A` 꼴(부속서 안 본문 절)까지 받는다.
BODY_NUM = rf"[0-9]+[a-zA-Z]?(?:_[0-9]+)*(?:\.{SEG})*(?:\.[A-Z])?"
#: 부속서 절 번호.
ANNEX_NUM = rf"[A-Z][0-9]*(?:\.{SEG})*(?:-[0-9]+[a-zA-Z]?)?"

BODY_NUM_RE = re.compile(rf"^{BODY_NUM}$")
ANNEX_NUM_RE = re.compile(rf"^{ANNEX_NUM}$")
_BODY_HEAD_RE = re.compile(rf"^({BODY_NUM})\s+(.*)", re.DOTALL)
_ANNEX_HEAD_RE = re.compile(rf"^({ANNEX_NUM}):?\s+(.*)", re.DOTALL)
#: 범위 제목(`5 to 7 Void` · `9.2.3.96 - 9.2.3.99 Void`). 한 절이 아니라 비워 둔 번호 묶음이다.
_RANGE_HEAD_RE = re.compile(
    rf"^((?:{BODY_NUM}|{ANNEX_NUM})\s*(?:to|–|-)\s*(?:{BODY_NUM}|{ANNEX_NUM}))\s+(.*)", re.DOTALL)
#: 번호 앞에 「Clause」 가 붙어 들어온 제목(`ClauseA.4.3.2.2.1.2.7`).
_CLAUSE_PREFIX_RE = re.compile(r"^(?i:clause)(?=[0-9A-Z])")
#: 번호 앞에 붙어 들어온 쉼표(전각 포함).
_LEADING_COMMA_RE = re.compile(r"^[,，](?=[0-9A-Z])")
#: 번호 끝에 붙어 들어온 붙임표.
_TRAILING_HYPHEN_RE = re.compile(r"(?<=[0-9A-Za-z])-$")


def normalize(num: str) -> str:
    """제목에서 떼어 낸 번호의 조판 흔적을 지운다.

    번호 안 공백(`A. 6.3.2`) · 변형 꼬리 앞의 점(`6.4.2.1._1`) · 끝의 점 · 쌍점 · 붙임표(`4.` · `A.1:` ·
    `8.2.2.7.2.3.2-`) · 앞에 붙은 `Clause` 와 쉼표(`，7.6.1.4.2`) 는 조판이 남긴 것이지 번호의 일부가 아니다.
    번호 자체가 틀린 제목(`s13.4.1.1.5` · `7.6A.4,1.1`)은 여기서 고치지 않는다. 문서 순서가 번호를
    증명할 때만 `HeadingSequence.recover` 가 받아들인다.
    """
    num = re.sub(r"\s+", "", num).replace("._", "_")
    num = _CLAUSE_PREFIX_RE.sub("", num)
    num = _LEADING_COMMA_RE.sub("", num)
    # 붙임표는 번호 뒤에 붙었을 때만 벗긴다. 홀로 선 `-` 는 목록 문단이라 거절 경고로 남아야 한다.
    return _TRAILING_HYPHEN_RE.sub("", num).rstrip(".:")


def is_section_number(num: str) -> bool:
    return bool(BODY_NUM_RE.match(num) or ANNEX_NUM_RE.match(num))


#: 비운 절 표시. `Void`·`(void)`·`to H: Void`처럼 독립 단어인 경우와 앞 글자에 붙은
#: 대문자 `Void`(`eVoid`)를 인식한다. 부분 문자열로 찾으면 `avoidance`·`musim-AvoidedBandsList` 같은
#: 제목과 `should be avoided` 가 든 본문이 비운 절이 되어 KG 에서는 isVoid 로, VDB 에서는 청크 제외로 사라진다.
_VOID_RE = re.compile(r"\b[Vv][Oo][Ii][Dd]\b|(?<=[a-z])Void\b")


def is_void_text(text: str) -> bool:
    """제목이나 본문 문단에 비운 절 표시 `void` 가 낱말로 들어 있는가."""
    return bool(_VOID_RE.search(text))


def split_heading(text: str) -> tuple[str, str]:
    """번호가 붙은 제목을 (번호, 제목) 으로 나눈다. 번호가 없으면 ("", text).

    탭이 있으면 탭 앞을 번호로 반환하고, 호출자가 `is_section_number`로 유효성을 판정한다.
    이 방식으로 유효하지 않은 번호도 경고에 기록할 수 있다. 탭이 없으면 번호 문법과
    일치하는 접두부만 번호로 반환한다.
    """
    text = text.strip()
    if "\t" in text:
        num, _, title = text.partition("\t")
        return normalize(num), title.strip()
    m = _RANGE_HEAD_RE.match(text)
    if m:
        # 범위는 번호가 아니므로 판정에서 거절되도록 붙여서 돌려준다.
        return normalize(m.group(1)), m.group(2).strip()
    for pattern in (_BODY_HEAD_RE, _ANNEX_HEAD_RE):
        m = pattern.match(text)
        if m:
            return normalize(m.group(1)), m.group(2).strip()
    return "", text


#: 부속서 머리 문단: `Annex A (informative): Change history` → ("A", "Change history").
#: 쌍점이 괄호 앞에 오는 꼴(`Annex M:(normative)` · `Annex A: (normative):`)도 머리다. 괄호를 제목으로 남기면
#: 그 뒤 줄바꿈 너머의 제목(`Measurement grids`)이 잘린다.
ANNEX_HEADING_RE = re.compile(r"^Annex\s+([A-Z])\s*:?\s*(?:\([^)]*\))?\s*:?\s*(.*)")


def split_annex_heading(text: str) -> tuple[str, str]:
    """부속서 스타일(Heading 8/9) 문단 → (번호, 제목).

    부속서 스타일은 부속서 머리에만 쓰이지 않는다. 하위 절(`A.1\\tTitle`)과 번호 없는 제목 글도
    같은 스타일로 적힌다. 머리 꼴이 아니면 본문 제목과 같은 문법(`split_heading`)으로 판정한다 —
    머리 꼴이 아니라고 버리면 하위 절이 사라지고, 대문자 한 글자로 시작하는 글을 번호로 자르면
    `Expected …` 가 `Ex` 절이 된다.
    """
    text = text.strip()
    m = ANNEX_HEADING_RE.match(text)
    if m:
        return m.group(1), m.group(2).strip()
    return split_heading(text)


def ancestors(num: str) -> list[str]:
    """번호상 조상을 가까운 것부터. `6.2A.3.1` → `6.2A.3` · `6.2A` · `6`, `A.1.2` → `A.1` · `A`."""
    parts = num.split(".")
    return [".".join(parts[:k]) for k in range(len(parts) - 1, 0, -1)]


def build_hierarchy(sections, id_attr: str = "section_id", parent_attr: str = "parent_section_id") -> list[str]:
    """절의 부모를 정한다. 부모 = 존재하는 가장 가까운 번호상 조상 절.

    제목 스타일 수준은 부모의 증거가 아니다. 원문은 같은 깊이의 절에 다른 스타일을 쓰고
    (`4.9.15.2.2` 와 `4.9.15` 가 둘 다 Heading 6), 부속서 대제목(Heading 8)과 그 첫 절(Heading 1)을
    같은 수준으로 매긴다. 수준으로 쌓으면 `4.9.15.2.2` 가 `4.9.15` 아래로, `8.24.2` 가 `8.25` 아래로
    가고 `A.1` 은 부모를 잃는다. 번호 문법 밖의 제목(ASN.1 정의명)과 조상이 하나도 없는 절만
    제목 수준 스택으로 정한다.

    `sections` 의 원소는 식별자(`id_attr`) · `section_number` · `level` · 부모 식별자(`parent_attr`) ·
    `child_section_ids` 를 가진다. TR 파서의 절은 식별자를 `tr_section_id` · `parent_tr_section_id` 로 부른다. 같은 번호가 여럿이면(분할 파트마다 다시 나와 `-dupN` 으로 갈린 절)
    앞에서 가장 가까운 것이 조상 자리를 맡는다. 앞에 없으면 뒤에서 처음 나오는 것이 맡는다.

    부모를 정한 뒤 `level` 을 그 트리의 깊이로 다시 매긴다(부모 없음 = 1, 아니면 부모 + 1).
    스타일 수준을 남겨 두면 부모와 수준이 서로 다른 트리를 말한다 — `A.1`(Heading 1)은 부모 `A` 를 얻고도
    level 1 로 남아 Spec 직속 절로도 세어진다.

    번호가 스타일보다 앞선다. 제목 수준 스택은 번호상 자기 자손인 절을 부모로 고르지 않는다.
    `6.1`(Heading 1) 다음에 `6`(Heading 2)이 오면 `6.1` 은 번호로 `6` 을 부모로 갖는데, 스택이
    `6` 에게 `6.1` 을 주면 두 절이 서로의 부모가 된다. 그 밖에도 부모 사슬이 자기에게 돌아오는
    후보는 고르지 않고 다음 후보로 넘어간다. 그래서 결과는 언제나 숲(고리 없음)이다.

    돌려주는 값은 건너뛴 후보의 기록이다(건너뛴 것이 없으면 빈 목록). 같은 기록을 경고 로그로도 낸다.
    """
    first = {}
    for section in sections:
        first.setdefault(section.section_number, section)
    latest = {}
    stack = []
    parent_of = {}
    notes = []

    def closes_loop(candidate, section):
        node, seen = candidate, set()
        while node is not None and id(node) not in seen:
            if node is section:
                return True
            seen.add(id(node))
            node = parent_of.get(id(node))
        return False

    def skip(section, candidate, why):
        note = (f"Hierarchy: {getattr(section, id_attr)} skips parent candidate "
                f"{getattr(candidate, id_attr)} ({why})")
        notes.append(note)
        # 호출자가 돌려받은 기록을 쓰지 않아도 그 파서의 로그에 남도록 경고로도 낸다.
        logger.warning(note)

    for section in sections:
        while stack and stack[-1].level >= section.level:
            stack.pop()
        parent = None
        if is_section_number(section.section_number):
            for a in ancestors(section.section_number):
                if a not in first:
                    continue
                candidate = latest.get(a) or first[a]
                if closes_loop(candidate, section):
                    skip(section, candidate, "parent chain returns to the section")
                    continue
                parent = candidate
                break
        if parent is None:
            own = section.section_number if is_section_number(section.section_number) else None
            for candidate in reversed(stack):
                if own is not None and own in ancestors(candidate.section_number):
                    skip(section, candidate, "numeric descendant")
                    continue
                if closes_loop(candidate, section):
                    skip(section, candidate, "parent chain returns to the section")
                    continue
                parent = candidate
                break
        if parent is not None and parent is not section:
            setattr(section, parent_attr, getattr(parent, id_attr))
            parent.child_section_ids.append(getattr(section, id_attr))
            parent_of[id(section)] = parent
        stack.append(section)
        latest[section.section_number] = section
    depth_of = {}
    for section in sections:
        chain, seen, node = [], set(), section
        while node is not None and id(node) not in depth_of and id(node) not in seen:
            chain.append(node)
            seen.add(id(node))
            node = parent_of.get(id(node))
        base = depth_of.get(id(node), 0) if node is not None else 0
        for k, n in enumerate(reversed(chain), start=1):
            depth_of[id(n)] = base + k
    for section in sections:
        section.level = depth_of[id(section)]
    return notes


_LAST_SEG_RE = re.compile(r"^([0-9]+)([a-zA-Z]*)$")


def _typo_candidates(head: str, last: str | None) -> list[str]:
    """번호 한 토큰의 조판 오타를 지운 후보. 어느 후보도 여기서 채택되지 않는다 — 순서 판정이 고른다."""
    out = []
    compact = re.sub(r"\s+", "", head)
    for cand in (
        re.sub(r"^[a-z]+(?=[0-9])", "", compact),          # s13.4.1.1.5
        compact.replace(",", "."),                          # 7.6A.4,1.1
        re.sub(r"\.{2,}", ".", compact),                    # 5.3.3.1.3..3
        re.sub(r"(?<=[0-9])\.([A-Z])(?=\.)", r"\1", compact),  # 6.5.A.2.2.4
    ):
        if cand != compact:
            out.append(normalize(cand))
    if compact.startswith(".") and last:
        # `.6` — 앞 마디가 빠진 번호. 직전 절의 조상 가운데 하나에 붙는 자리만 후보가 된다.
        out.extend(f"{a}{compact}" for a in [last, *ancestors(last)])
    return out


def _tail_candidates(head: str) -> list[tuple[str, str]]:
    """앞 절의 본문 문장이 제목 문단에 붙어 들어온 꼴(`…apply to this test.A.6.5.1.17`)에서 (번호, 앞 문장) 후보.

    꼬리의 시작 자리를 좁히지 않는다 — `PC3.7.3.1.4.1` 처럼 문장 끝 앞이 숫자인 꼴도 있다. 어느 꼬리가
    번호인지는 순서 판정이 고른다.
    """
    head = head.strip()
    out = []
    for i in range(1, len(head)):
        lead, tail = head[:i].strip(), normalize(head[i:])
        if lead and tail[:1].isalnum() and is_section_number(tail):
            out.append((tail, lead))
    return out


#: 제목에 이어 붙은 노트. 편집자 노트는 앞 글자가 무엇이든 제목이 아니다(`CA_n5BEditor's note: …`).
_NOTE_GLUE_RE = re.compile(r"(?<=\S)(?=(?:Editor[’']s\s+[Nn]ote|NOTE)\s*\d*\s*:)")
#: 소문자 바로 뒤에 빈칸 없이 대문자 낱말이 이어지는 자리(`Test descriptionIf …`).
_WORD_GLUE_RE = re.compile(r"(?<=[a-z])(?=[A-Z][a-z]+\s)")


def split_glued(title: str) -> tuple[str, str]:
    """제목 문단 하나에 이어 붙은 본문 문장을 떼어 `(제목, 본문 문장)` 으로 돌려준다. 없으면 본문은 `""`.

    원문은 제목과 그 절의 첫 문장을 한 문단에 빈칸 없이 적기도 한다(38.521-3 `6.5L.1.3.4\tTest
    descriptionIf Standalone FR1 can be tested, …` · 38.521-4 `…predicted PMIEditor's Note: …`). 그대로
    두면 문장이 제목이 되고 본문에서는 빠진다 — 그 문장이 든 절 인용(`6.5G.1`)도 함께 빠진다.
    낱말이 붙은 자리는 `kHz` · `RedCap` · `AoAs` 같은 제목 낱말에도 있으므로, 뒤쪽이 마침표나
    쌍점으로 끝나는 네 낱말 이상의 문장일 때만 뗀다.
    """
    for rx in (_NOTE_GLUE_RE, _WORD_GLUE_RE):
        for m in rx.finditer(title):
            head, lead = title[:m.start()].rstrip(), title[m.start():].strip()
            if rx is _NOTE_GLUE_RE or (lead.endswith((".", ":")) and len(lead.split()) >= 4):
                return head, lead
    return title, ""


class Promotion(tuple):
    """`promote` 가 세운 `(번호, 제목)`. 제목 문단에 이어 붙어 있던 본문 문장은 `lead` 로 든다."""

    def __new__(cls, num: str, title: str, lead: str = ""):
        self = super().__new__(cls, (num, title))
        self.lead = lead
        return self


class HeadingSequence:
    """한 문서(또는 한 파트)의 제목 순서. 번호 문법이 거절한 제목을 순서가 증명할 때만 절로 되살린다.

    되살리는 조건 셋이 모두 성립해야 한다.
      1. 후보 번호의 번호상 부모가 이미 나왔고, 그 부모가 직전 절 자신이거나 직전 절의 조상이다.
      2. 후보 번호가 아직 나오지 않았다.
      3. 후보가 그 부모의 다음 자식 자리다 — 부모의 마지막 자식 끝 마디 + 1, 같은 끝 숫자에 뒤 글자,
         자식이 아직 없으면 끝 마디 0 또는 1.
    조건을 채우는 후보가 둘 이상이면 되살리지 않는다. 마디 하나짜리 번호의 조건은 `promote` 에 있다.
    """

    def __init__(self) -> None:
        self.seen: set[str] = set()
        self.last_child: dict[str, str] = {}
        self.last: str | None = None
        self._title_node = None

    def new_part(self) -> None:
        """분할 파트의 시작. 번호 집합은 이어 가고 직전 절만 끊는다."""
        self.last = None

    def accept(self, num: str) -> None:
        """절로 세운 제목을 기록한다. ASN.1 정의명처럼 번호가 아닌 제목은 번호 경로를 끊지 않는다."""
        if not is_section_number(num):
            return
        if num not in self.seen:
            anc = ancestors(num)
            if anc:
                self.last_child[anc[0]] = num
        self.seen.add(num)
        self.last = num

    def _is_next(self, cand: str) -> bool:
        if cand in self.seen or not is_section_number(cand) or self.last is None:
            return False
        anc = ancestors(cand)
        if not anc or anc[0] not in self.seen:
            return False
        parent = anc[0]
        if parent != self.last and parent not in ancestors(self.last):
            return False
        m = _LAST_SEG_RE.match(cand.rsplit(".", 1)[-1])
        if not m:
            return False
        n, suf = int(m.group(1)), m.group(2)
        prev = self.last_child.get(parent)
        if prev is None:
            return n in (0, 1) and not suf
        pm = _LAST_SEG_RE.match(prev.rsplit(".", 1)[-1])
        if not pm:
            return False
        p, psuf = int(pm.group(1)), pm.group(2)
        return (n == p + 1 and not suf) or (n == p and suf > psuf)

    def recover(self, text: str) -> tuple[str, str, str] | None:
        """거절된 제목 문단 → (번호, 제목, 앞 절 몫의 앞 문장) 또는 None."""
        head, sep, title = text.strip().partition("\t")
        if not sep:
            return None
        splits = [(head, title)]
        # 시험 조건의 목록 문장에도 탭이 있다. 끝에 붙은 번호와 제목의
        # 마지막 탭을 읽되, 기존과 같은 문서 순서 검사를 통과해야 한다.
        if text.count("\t") > 1:
            head, title = text.strip().rsplit("\t", 1)
            splits.append((head.replace("\t", " "), title))
        for head, title in splits:
            cands = [(c, "") for c in _typo_candidates(head, self.last)] + _tail_candidates(head)
            ok = {}
            for num, lead in cands:
                if self._is_next(num):
                    ok.setdefault(num, lead)
            if len(ok) == 1:
                num, lead = next(iter(ok.items()))
                return num, title.strip(), lead
        return None

    def _is_next_root(self, cand: str) -> bool:
        """마디 하나짜리 본문 번호가 직전 절이 속한 장의 다음 장 자리인가."""
        if cand in self.seen or not cand.isdigit() or self.last is None:
            return False
        root = self.last.split(".", 1)[0]
        return root.isdigit() and int(cand) == int(root) + 1

    def promote(self, text: str, following=None) -> Promotion | None:
        """제목 스타일이 아닌 문단 → `Promotion`(번호, 제목, 붙은 본문 문장 `lead`) 또는 None.

        원문은 절 제목을 Normal 같은 본문 스타일로 적기도 한다(38.314 의 `4.2.1.7\\tPRB Usage for MIMO`).
        스타일만 보면 그 절은 경고 없이 사라지고 본문과 표가 앞 절로 들어간다. 스타일은 증거가
        아니므로 `번호\\t제목` 꼴이고 문서 순서가 그 번호를 다음 자리로 증명할 때만 절로 세운다.

        마디가 하나뿐인 번호(`7\\t…`)는 순서만으로는 번호 목록 문단과 가를 수 없다. 그래서 다음 장
        자리이면서, 뒤따르는 문단 가운데 처음 나오는 번호 문단이 그 번호의 자식(`7.…`)일 때만 받는다.
        38.115-1 은 7장 머리부터 하위 절까지를 모두 Normal 로 적어, 이 증거 없이는 7장 전체가 6장
        마지막 절의 본문이 된다.

        번호와 제목을 탭이 아니라 빈칸으로 가른 문단(38.133 의 `A.10.3.3.1 SCell Activation …`)은
        번호로 시작하는 본문 문장과 모양이 같다. 그래서 순서 조건에 더해, 뒤따르는 첫 번호 문단이
        그 번호 뒤의 자리일 때만 받는다 — 그 번호의 자식이거나, 그 번호 또는 그 조상의 다음 형제
        (`11.3.1.7 …` 뒤의 `11.3.2`). 자식 증거만 보면 자식이 없는 잎 절(38.104 `11.3.1.7` ·
        38.101-3 `5.5B.4.0`)이 빠진다. 부모 절이 빠지면 탭으로 적힌 그 자식 절들까지 순서가 끊겨 사라진다.

        번호가 점으로 끝나는 문단(`7.\tOFF power sub test:` · `7.1.\tMeasure …`)은 절이 아니라 번호
        목록이다. 38.533 · 38.521-1 의 시험 절차 단계가 이 꼴이고, 앞 장 뒤라서 순서도 자식 증거도
        갖춘다. 절 제목의 번호는 점으로 끝나지 않으므로(`normalize` 가 벗기는 끝 점은 제목 스타일
        문단의 조판 흔적) 본문 스타일 문단에서는 이 꼴을 받지 않는다.

        `following` 은 뒤따르는 문단 글의 iterable 이고(`following_texts`), 주지 않으면 자식 증거가
        필요한 두 경우는 받지 않는다.
        """
        text = text.strip()
        head, sep, title = text.partition("\t")
        spaced = not sep
        if spaced:
            head, sep, title = text.partition(" ")
        if head.strip().endswith("."):
            return None
        num = normalize(head)
        if not sep or not title.strip():
            return None
        if "." not in num:
            if not self._is_next_root(num) or not _child_follows(num, following):
                return None
            return Promotion(num, *split_glued(title.strip()))
        if not self._is_next(num):
            return None
        if spaced and not _position_follows(num, following):
            return None
        return Promotion(num, *split_glued(title.strip()))

    def take_annex_title(self, head_text: str, para) -> str:
        """제목이 빈 부속서 머리(`Annex G (normative):`) → 다음 문단에 적힌 제목, 없으면 "".

        원문은 부속서 제목을 머리 문단의 쌍점 뒤가 아니라 다음 문단에 따로 적기도 한다
        (38.101-1 Rel-15/16 의 Annex G · 38.115-2 Rel-19 의 Annex J). 그 문단을 제목으로 읽지 않으면
        부속서는 제목 없이 서고 제목 글은 본문 첫 줄이나 버려진 제목 문단이 된다.
        머리가 쌍점으로 끝나고, 사이에 표 없이 처음 나오는 비어 있지 않은 문단에 절 번호가 없으며
        표 · 그림 캡션이나 목차 · 다른 부속서 머리가 아닐 때만 받는다(38.174 의 Annex F 는 바로
        F.1 이 이어지므로 제목이 빈 채로 남는다). 가져간 문단은 `is_annex_title` 로 본문에서 뺀다.
        """
        from docx.oxml.ns import qn
        from docx.text.paragraph import Paragraph
        self._title_node = None
        element = getattr(para, "_p", None)
        head = ANNEX_HEADING_RE.match(head_text.strip())
        if element is None or not head or head.group(2).strip() or not head_text.rstrip().endswith(":"):
            return ""
        node = element.getnext()
        while node is not None:
            if node.tag != qn("w:p"):
                return ""
            nxt = Paragraph(node, para._parent)
            text = docx_text.final_text(node)
            if text:
                style = nxt.style.name if nxt.style else ""
                if (style in ("TH", "TF") or style.lower().startswith("toc")
                        or ANNEX_HEADING_RE.match(text) or split_heading(text)[0]
                        or is_section_number(normalize(text.partition("\t")[0]))):
                    return ""
                self._title_node = node
                return text
            node = node.getnext()
        return ""

    def is_annex_title(self, para) -> bool:
        """`take_annex_title` 가 부속서 제목으로 가져간 문단인가."""
        return self._title_node is not None and getattr(para, "_p", None) is self._title_node


def _child_follows(num: str, following) -> bool:
    """뒤따르는 문단 가운데 처음 나오는 번호 문단이 `num` 의 자식인가."""
    if following is None:
        return False
    for nxt in following:
        nhead, nsep, _ = nxt.strip().partition("\t")
        nnum = normalize(nhead) if nsep else split_heading(nxt.strip())[0]
        if is_section_number(nnum):
            return nnum.startswith(num + ".")
    return False


def _seg_key(seg: str) -> tuple:
    """번호 마디의 순서 키. `2B` → (2, 'B') · `1_3` → (1, '_', 3)."""
    return tuple(int(t) if t.isdigit() else t for t in re.findall(r"[0-9]+|[A-Za-z]+|_", seg))


def _position_follows(num: str, following) -> bool:
    """뒤따르는 문단 가운데 처음 나오는 번호 문단이 `num` 뒤의 자리인가.

    `num` 의 자식이거나, `num` 또는 그 조상의 다음 형제(`11.3.1.7` 뒤의 `11.3.1.8` · `11.3.2` · `12.1`).
    장 번호만의 다음 자리(`12`)는 번호 목록 문단과 가를 수 없어 받지 않는다.
    """
    if following is None:
        return False
    for nxt in following:
        nhead, nsep, _ = nxt.strip().partition("\t")
        nnum = normalize(nhead) if nsep else split_heading(nxt.strip())[0]
        if not is_section_number(nnum):
            continue
        if nnum.startswith(num + "."):
            return True
        cs, ns = num.split("."), nnum.split(".")
        k = len(ns) - 1
        if not 1 <= k < len(cs) or ns[:k] != cs[:k]:
            return False
        try:
            return _seg_key(ns[k]) > _seg_key(cs[k])
        except TypeError:
            return False
    return False


def following_texts(para):
    """본문에서 이 문단 뒤에 오는 문단들의 글을 차례로 낸다. 표처럼 문단이 아닌 형제는 건너뛴다."""
    from docx.oxml.ns import qn
    element = getattr(para, "_p", None)
    node = element.getnext() if element is not None else None
    while node is not None:
        if node.tag == qn("w:p"):
            yield docx_text.final_text(node)
        node = node.getnext()


def depth(num: str) -> int:
    """번호의 마디 수 = 제목 수준. `4.2.1.7` → 4, `A.1` → 2."""
    return num.count(".") + 1


def split_repeated_ids(seen: set[str], sections) -> list[str]:
    """분할 파트마다 다시 나온 절 식별자를 버리지 않고 `-dupN` 접미사로 가른다.

    한 파트 안에서는 같은 번호의 제목이 다시 나오면 그 절로 돌아가지만, 파트가 다르면 같은
    `section_id` 가 두 번 선다. 하류의 point id 는 chunkId 를 해싱해 만들기 때문에 겹치는 순간
    뒤엣것이 앞엣것을 조용히 덮어쓴다. `section_number` 는 원문이 적은 그대로 두고 식별자만
    가른다. 계층(`build_hierarchy`)은 가른 뒤에 세운다. 돌려주는 값은 가른 자리의 기록이다.
    """
    notes = []
    for section in sections:
        old = section.section_id
        if old not in seen:
            seen.add(old)
            continue
        n = 2
        while f"{old}-dup{n}" in seen:
            n += 1
        section.section_id = f"{old}-dup{n}"
        seen.add(section.section_id)
        notes.append(f"Cross-part duplicate section ID: {old} -> {section.section_id}")
    return notes
