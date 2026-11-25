#!/usr/bin/env python3
"""cr_revision_marks.py: CR 변경 본문에서 고친 절과 고치지 않은 절을 변경 추적 표시로 가른다.

3GPP CR 서식은 바뀐 글을 변경 추적 표시(삽입 · 삭제 · 이동 · 서식 변경)로 적게 한다. 표시가 하나라도 있는
CR 에서 표시가 없는 절은 바꾼 자리를 찾기 쉽게 옮겨 적은 표준 글이고, 그 CR 이 바꾼 글이 아니다.

> 주의: 표준 전체나 큰 절 묶음을 옮겨 적고 몇 절만 고친 CR 이 있다(RAN2 `R2-2314072` 는 38.322 102절 가운데
> 3.1 한 절만 고쳤다). 표시 없는 절까지 청크로 만들면 그 CR 이 바꾸지 않은 표준 글이 CR 검색에서 그 CR 의
> 변경으로 잡힌다. Phase-8 Spec §1.5 의 본문은 TS 변경 글이다.
>
> 주의: 표시를 쓰지 않고 색이나 강조로만 바뀐 글을 보이는 CR 도 있을 수 있다. 그래서 다음 경우는 표시가 없어도
> 남긴다. ① 본문에 표시가 하나도 없는 CR 은 모든 절을 남긴다(무엇이 바뀌었는지 표시로 알 수 없다).
> ② 표지의 Clauses affected 에 적힌 절과 그 위 · 아래 절은 남긴다(제출자가 바꿨다고 밝힌 자리다).
> ③ 글자에 밑줄이나 취소선을 직접 건 절은 남긴다. 변경 추적 없이 밑줄(넣은 글) · 취소선(뺀 글)으로 고친 자리를
> 적는 손 표기 관례가 있고, 표시 있는 CR 안에서도 일부 절을 그렇게 적은 사례가 있다(RAN2 `R2-2008286` 의
> 5.5.3.3 은 밑줄 친 구절만 있다). 색과 형광 강조는 쓰지 않는다. 색은 ASN.1 · 참조 글에 늘 붙어 있고, 형광 강조는
> `<UNNECESSARY PARTS OMITTED>` 같은 생략 표지에 붙는다.
>
> 주의: 번호 없는 제목 절(RRC IE 이름 `– CellGroupConfig`, ASN.1 묶음 `-- …`, 시험 단계 `(1)` 따위)은 앞의
> 번호 있는 절이 표지에 적혀 있어도 그 번호를 물려받지 않고 제 표시로만 판정한다. 표준 한 장을 통째로 옮겨
> 적은 CR 은 표지에 큰 절(`6.3.2` 따위)을 적고 그 아래 IE 몇 개만 고치는데, 번호를 물려주면 고치지 않은 IE
> 글이 모두 다시 남는다(RAN2 `R2-2501448` 은 그 몫이 본문의 절반에 이른다). 표시 있는 CR 에서는 표시가 더
> 잘게 바뀐 자리를 가리키므로 번호 없는 절에는 표시를 따른다.
"""
from __future__ import annotations

from typing import Iterable, Sequence
from xml.etree import ElementTree as ET

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

#: 변경 추적 표시 요소. 글의 삽입 · 삭제 · 이동과 문단 · 글자 · 표 · 칸 서식 변경을 모두 바뀐 자리로 본다.
REVISION_TAGS = frozenset(f"{{{W_NS}}}{t}" for t in (
    "ins", "del", "moveTo", "moveFrom",
    "rPrChange", "pPrChange", "tblPrChange", "trPrChange", "tcPrChange", "tblGridChange",
    "sectPrChange", "numberingChange", "cellIns", "cellDel", "cellMerge",
))


_R, _RPR, _T = (f"{{{W_NS}}}{t}" for t in ("r", "rPr", "t"))
_ON_OFF_OFF = ("0", "false", "off")


def has_revision(elem: ET.Element) -> bool:
    """요소 안에 변경 추적 표시가 있는가."""
    return any(e.tag in REVISION_TAGS for e in elem.iter())


def has_manual_mark(elem: ET.Element) -> bool:
    """글이 든 글자 묶음에 밑줄이나 취소선을 직접 걸었는가(스타일로 물려받은 것은 보지 않는다)."""
    for r in elem.iter(_R):
        rpr = r.find(_RPR)
        if rpr is None or not "".join(t.text or "" for t in r.iter(_T)).strip():
            continue
        for c in rpr:
            tag = c.tag[len(W_NS) + 2:]
            val = c.get(f"{{{W_NS}}}val")
            if tag in ("strike", "dstrike") and (val or "1") not in _ON_OFF_OFF:
                return True
            if tag == "u" and val not in (None, "none"):
                return True
    return False


def range_has_revision(body_elements: Sequence[tuple[str, ET.Element]], start: int, end: int) -> bool:
    """`body_elements[start:end]` 안에 변경 추적 표시가 있는가."""
    return any(has_revision(el) for _, el in body_elements[start:end])


def declared(section_number: str, clauses: Iterable[str]) -> bool:
    """절 번호가 표지에 적힌 절이거나 그 위 · 아래 절인가."""
    if not section_number:
        return False
    for c in clauses:
        if c and (section_number == c or section_number.startswith(c + ".") or c.startswith(section_number + ".")):
            return True
    return False


def changed_sections(
    body_elements: Sequence[tuple[str, ET.Element]],
    body_start_idx: int,
    section_ranges: Sequence[tuple[str, int, int]],
    clauses_affected: Iterable[str] = (),
) -> list[bool]:
    """절마다 청크로 남길지(True) 고르는 표.

    `section_ranges` 는 (절 번호, 시작, 끝) 목록이고 시작은 제목 문단의 자리다. 본문(`body_start_idx` 부터)에
    표시가 하나도 없으면 모두 남긴다. 표시가 있으면 표시가 든 절, 표지에 적힌 절, 손 표기가 든 절만 남긴다.
    """
    if not range_has_revision(body_elements, body_start_idx, len(body_elements)):
        return [True] * len(section_ranges)
    clauses = [c for c in clauses_affected if c]
    return [range_has_revision(body_elements, s, e) or declared(num, clauses)
            or any(has_manual_mark(el) for _, el in body_elements[s:e])
            for num, s, e in section_ranges]
