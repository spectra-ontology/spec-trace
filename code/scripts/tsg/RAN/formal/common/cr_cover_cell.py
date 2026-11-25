#!/usr/bin/env python3
"""cr_cover_cell.py: CR 표지 표의 칸 안에 든 변경 본문을 꺼낸다.

3GPP CR 서식은 표지(CR-Form · Proposed change affects · Title … Reason for change · Summary of change …)를
표 몇 개로 두고 그 뒤에 변경 본문을 둔다. 본문 시작은 마지막 표지 표의 다음 자리다.

> 주의: 표지 전체를 겉 표 한 칸에 담고 같은 칸 안 표지 표들 뒤에 변경 본문까지 이어 적은 CR 이 있다
> (RAN1 `R1-2212972` · `R1-2603373` 은 1행 1칸 겉 표, `R1-2405624` 는 표지 행 하나의 칸). 본문 직계 요소만
> 보면 그 CR 은 표지 표 하나로 끝나 본문이 비고 헤더 청크만 남는다. 그래서 표지 표의 칸마다 마지막 표지 표
> 뒤에 오는 문단 · 표를 본문 요소로 꺼내 표지 표 바로 뒤 자리에 둔다. 칸 안에 표지 표가 없으면(보통의
> 표지 행) 아무것도 꺼내지 않는다. 표지 표 뒤에 빈 문단만 있는 칸도 꺼내지 않는다(빈 문단에 걸린 서식 변경
> 표시가 본문의 변경 추적 판정(`cr_revision_marks`)에 끼어들지 않게).
>
> 주의: 꺼내는 칸은 본문 직계 요소 가운데 마지막 표지 표의 칸이고, 그 표 뒤에 글이 든 요소가 하나도 없을
> 때만 꺼낸다. 표지 뒤에 본문이 따로 있는 CR 의 칸 안 표지 표 뒤 글은 표지의 나머지 칸이다(RAN2
> `R2-2411086` 은 칸 안 표지 표 뒤에 Consequences if not approved 칸을, RAN1 `R1-1907957` 은 개정 이력 머리말을
> 두었다). 그 글을 꺼내면 표지 글이 본문 청크에 섞인다.
>
> 주의: 꺼낸 자리에 글이 든 요소가 1행 1칸 상자 하나뿐이면 그 상자를 풀어 안의 문단 · 표를 본문으로 둔다
> (`R1-2405624` 는 본문 절을 상자 하나에 담았다). 상자를 풀지 않으면 제목 문단이 표 칸 글이 되어 절이 나뉘지
> 않는다. 다른 요소와 함께 있는 상자는 표 그대로 둔다(본문의 1칸 표일 수 있다).

ElementTree 요소와 lxml(python-docx) 요소를 모두 받는다.
"""
from __future__ import annotations

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_P, _TBL, _TR, _TC, _T = (f"{{{W_NS}}}{t}" for t in ("p", "tbl", "tr", "tc", "t"))

#: 표지 표에만 나오는 칸 이름(소문자로 견준다). `find_last_form_table_index` 가 표지로 보는 이름과
#: 표지 머리 표 이름이다.
COVER_KEYS = ("reason for change", "summary of change", "other specs", "change history", "revision history",
              "proposed change affects", "cr-form")


def _text(el) -> str:
    return " ".join(t.text for t in el.iter(_T) if t.text)


def is_cover_table(tbl) -> bool:
    """표 글에 표지 칸 이름이 있는가."""
    low = _text(tbl).lower().replace("’", "'")
    return any(k in low for k in COVER_KEYS)


def _box_children(el):
    """1행 1칸 표면 그 칸의 문단 · 표, 아니면 None."""
    if el.tag != _TBL:
        return None
    rows = [r for r in el if r.tag == _TR]
    if len(rows) != 1:
        return None
    cells = [c for c in rows[0] if c.tag == _TC]
    if len(cells) != 1:
        return None
    return [k for k in cells[0] if k.tag in (_P, _TBL)]


def cell_body(tbl) -> list:
    """표지 표의 칸 안에서 마지막 표지 표 뒤에 오는 문단 · 표(문서 차례). 없으면 빈 목록."""
    out = []
    for tr in tbl:
        if tr.tag != _TR:
            continue
        for tc in tr:
            if tc.tag != _TC:
                continue
            kids = [k for k in tc if k.tag in (_P, _TBL)]
            last = max((i for i, k in enumerate(kids) if k.tag == _TBL and is_cover_table(k)), default=-1)
            if last < 0:
                continue
            rest = kids[last + 1:]
            filled = [k for k in rest if _text(k).strip()]
            if not filled:
                continue
            if len(filled) == 1:
                inner = _box_children(filled[0])
                if inner is not None and not is_cover_table(filled[0]):
                    rest = inner
            out.extend(rest)
    return out


def body_in_cells(children: list) -> tuple[int, list]:
    """본문 직계 요소 목록에서 마지막 표지 표의 자리와 그 칸에서 꺼낼 본문 요소.

    표지 표가 없으면 (-1, []), 그 표 뒤에 글이 든 문단 · 표가 있으면 (자리, []) 이다.
    """
    last = max((i for i, k in enumerate(children) if k.tag == _TBL and is_cover_table(k)), default=-1)
    if last < 0:
        return -1, []
    if any(k.tag in (_P, _TBL) and _text(k).strip() for k in children[last + 1:]):
        return last, []
    return last, cell_body(children[last])


def unwrap(elements: list, tag_of=None) -> list:
    """본문 직계 요소 목록에서 마지막 표지 표의 칸 안 본문(`body_in_cells`)을 그 표 바로 뒤에 끼운 새 목록.

    `elements` 는 요소 목록이거나 `(꼴, 요소)` 짝 목록이다(`tag_of` 가 주어지면 짝 목록으로 보고 꺼낸
    요소도 `(tag_of(요소), 요소)` 짝으로 끼운다).
    """
    last, body = body_in_cells([item[1] if tag_of else item for item in elements])
    if not body:
        return list(elements)
    extra = [(tag_of(k), k) if tag_of else k for k in body]
    return list(elements[:last + 1]) + extra + list(elements[last + 1:])
