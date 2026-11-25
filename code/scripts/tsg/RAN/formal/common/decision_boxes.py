"""decision_boxes.py — 회의록 표 상자 안의 결정 표지를 읽는 걸음.
RAN WG 다섯 곳의 Phase-2 결정 추출기가 함께 쓴다.

회의록은 결정을 1행 표 상자에 적기도 한다 — 칸 첫 줄이 `Agreements` 이고 그 아래 합의 항목이 이어진다. 결정
추출기의 문단 흐름은 본문 문단만 표지로 읽고 표는 앞 표지 문단의 본문으로만 들이므로, 상자 안 표지는 결정을
열지 못했다. 여기서는 어느 결정 본문에도 들지 않은 본문 표마다 칸 문단을 본문 문단과 같은
`decision_marks.decision_spans` 규칙으로 따로 읽는다.

- 문단 결정의 본문(내지 않은 인용 · 흡수 표지의 본문 포함 — `decision_spans` 의 spans) 안에 놓인 표는 그 결정이
  이미 읽었으므로 건너뛴다.
- 칸 결정의 본문은 칸 밖으로 잇지 않는다. 세로 합침이 이어지는 칸은 빈 칸이라 읽지 않는다. 칸 안 표는 칸 결정의
  본문이면 본문으로, 아니면 그 표의 칸을 다시 같은 규칙으로 읽는다.
- 칸 하나가 통째로 Tdoc 번호인 행은 Tdoc · LS 목록의 항목이라 읽지 않는다 — 제목 칸의 `Conclusion of …` ·
  `Agreements on Paging (R1-…; contact: …)` 는 기고문 · LS 이름이다(본문 문단의 항목 줄 `ENTRY_LINE` 과 같은 자리).
- 칸 하나가 통째로 회의 이름(뒤 붙은 달 · 해까지)인 행도 읽지 않는다 — 회의마다 할 일을 적은 작업 계획표의 행이라
  `Agreements on` 아래 줄은 그 회의에 이르려는 목표다(RAN4#90bis 기고 초록의 NR-U RRM 작업 계획표, 행 머리
  `RAN4#90bis April 2019`). 이번 회의 행이어도 계획이지 회의록이 적은 결정이 아니다.
- 칸 문단의 절 머리는 제목 꼴 · miniheading 꼴 문단이다.
- 상자는 앞 본문 문맥 안에 놓인다. 칸만 읽으면 그 문맥을 못 보므로 본문 문단(texts · hard)을 받아 문단 흐름과 같은
  두 규칙을 상자에도 건다(`outside_context`). 표가 Tdoc 항목의 `Abstract:` 칸 안에 놓였으면 Abstract 칸 표지 규칙을,
  표 바로 앞 글 줄이 상자 결정의 출처 회의를 밝히면(`decision_marks.lead_source`) 인용 규칙을 건다.

> 주의: 문단 번호는 절 · 의제 · 역할이 함께 쓰는 좌표라 칸 문단을 문단 흐름에 끼우지 않는다. 칸 문단은
> python-docx 문서 트리에서 읽고(`docx_text.list_keys` 가 스타일 표를 본다), 그 블록 차례가 추출기의 본문 블록
> (`zipfile` 로 읽은 document.xml)과 다르면 상자를 읽지 않고 알린다.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from typing import Callable, Container, Iterator, Optional, Sequence

import docx_text
import decision_marks

_W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
_P_TAG = f'{{{_W_NS}}}p'

# Tdoc 목록 표의 번호 칸 — 칸 글 전체가 Tdoc 번호(뒤 붙은 짧은 꼬리 `r1` 까지)인 칸
TDOC_CELL = re.compile(rf"{decision_marks.tdoc_number()}\w{{0,3}}")
# 계획표의 회의 칸 — 칸 글 전체가 회의 꼬리표(`-e` 꼬리, 뒤 붙은 달 · 해까지)인 칸
MEETING_CELL = re.compile(rf"{decision_marks.meeting_tag()}(?:-?e)?(?:[\s,]+(?:[A-Za-z]+\.?\s+)?\d{{4}})?",
                          re.IGNORECASE)


@dataclass
class BoxMark:
    """표 상자 안 결정 표지 하나 — 추출기가 표지 줄 글과 본문을 제 판독기로 읽는다."""
    body_index: int             # 상자 표의 본문 블록 번호
    prev_para: Optional[int]    # 표 앞 마지막 본문 문단 번호(의제를 정한다) — 본문 맨 앞 표면 None
    mark: decision_marks.Mark
    line: object                # 표지 칸 문단(python-docx Paragraph)
    body: list                  # 본문 블록 — 칸 문단은 Paragraph, 칸 안 표는 w:tbl 요소

    def paragraphs(self) -> list:
        """표지 줄과 본문의 칸 문단 — 수식 변환기에 넘길 문단 목록(번호 0 이 표지 줄)."""
        return [self.line] + [b for b in self.body if hasattr(b, '_element')]

    def following(self, marked: Callable[[object], str], table_text: Callable[[object], str]) -> str:
        """본문 글 — 칸 문단은 marked, 칸 안 표는 table_text 로 읽어 줄로 잇는다."""
        parts = (marked(b) if hasattr(b, '_element') else table_text(b) for b in self.body)
        return '\n'.join(t for t in parts if t)


def box_marks(paragraphs: Sequence, body_children: Sequence, para_to_body: dict, spans: Sequence[tuple[int, int]],
              *, companies: frozenset, meeting: Optional[str], stop: Optional[int] = None,
              outside: Container[int] = (),
              texts: Optional[Sequence[str]] = None, hard: Optional[Sequence[bool]] = None,
              kinds=tuple(decision_marks.KEYWORDS), **span_kw) -> list[BoxMark]:
    """어느 결정 본문에도 들지 않은 본문 표의 칸 안 결정 표지를 문서 차례로 낸다.

    paragraphs 는 본문 문단(`docx_text.body_paragraphs`), body_children 과 para_to_body 는 추출기의 본문 블록과
    문단 번호 → 블록 번호 표, spans 는 문단 흐름의 `decision_spans` 가 채운 (표지 문단 번호, 본문 끝 번호)다.
    stop 을 주면 그 문단 번호(부록 머리) 뒤에 놓인 표는 읽지 않는다 — 문단 흐름이 부록 표지를 읽지 않는 WG 의 규칙을
    상자에도 건다. outside 는 부록이 중간에 끝나고 본문이 다시 이어지는 WG(RAN2 브레이크아웃 세션 부록)가 주는 범위 밖
    문단 번호 집합이고, 바로 앞 문단이 그 안에 든 표는 읽지 않는다. texts · hard 는 추출기가 `decision_spans` 에 넘긴 본문 문단 글 · 절 머리이고, 주면 상자 표지마다
    `outside_context` 로 앞 본문 문맥을 본다. companies · meeting · kinds 와 나머지 인자는 `decision_spans` 에 그대로
    넘긴다.
    """
    if not paragraphs or not body_children:
        return []
    parent = paragraphs[0]._parent
    blocks = list(docx_text.iter_blocks(parent._element))
    if [b.tag for b in blocks] != [c.tag for c in body_children]:
        print(f"  [WARN] {meeting}: 본문 블록 차례가 달라 표 상자 결정을 읽지 않는다", file=sys.stderr)
        return []
    n_body = len(blocks)
    covered: set[int] = set()
    for idx, end in spans:
        if idx in para_to_body:
            covered.update(range(para_to_body[idx] + 1, para_to_body.get(end, n_body)))
    out: list[BoxMark] = []
    heads = [(decision_marks.template_head(t) or (None,))[0] if t else None for t in texts] if texts is not None else []
    prev, para_idx = None, 0
    for body_idx, block in enumerate(blocks):
        if block.tag == _P_TAG:
            prev, para_idx = para_idx, para_idx + 1
            continue
        if stop is not None and prev is not None and prev >= stop:
            break
        if prev in outside or body_idx in covered:
            continue
        for mark, line, body in table_marks(block, parent, companies=companies, meeting=meeting, kinds=kinds,
                                            **span_kw):
            box = BoxMark(body_idx, prev, mark, line, body)
            if texts is not None and prev is not None and outside_context(
                    box, texts, hard, heads, blocks, para_to_body, spans, out, companies=companies, meeting=meeting,
                    kinds=kinds, abstract_notes=span_kw.get("abstract_notes", False)):
                continue
            out.append(box)
    return out


def _lines(box: BoxMark) -> list[str]:
    """상자 결정의 글 줄 — 표지 줄 뒤 글과 본문 칸 문단(칸 안 표는 넣지 않는다)."""
    lines = [box.mark.inline or ""] + [docx_text.final_text(b).strip() for b in box.body if hasattr(b, '_element')]
    return [x for x in lines if x]


def outside_context(box: BoxMark, texts: Sequence[str], hard: Sequence[bool], heads: Sequence[Optional[str]],
                    blocks: Sequence, para_to_body: dict, spans: Sequence[tuple[int, int]], earlier: Sequence[BoxMark],
                    *, companies: frozenset, meeting: Optional[str], kinds=tuple(decision_marks.KEYWORDS),
                    abstract_notes: bool = False) -> bool:
    """상자 표지가 앞 본문 문맥 때문에 이번 회의 결정이 아닌가 — 문단 흐름(`decision_spans`)의 두 규칙을 상자에 건다.

    - 표 앞 마지막 문단까지 가장 가까운 칸 머리가 `Abstract:` 면 그 칸 안 표다. abstract_notes 가 아니면 내지 않고,
      abstract_notes 면 표지 줄을 표 자리에 끼운 문단 줄로 `abstract_quote` 를 본다(RAN4-88 의 WA 두 건은 초록 안
      `RAN4#AH1807 … agreed with the way forward [1]` 뒤 상자, RAN4-88bis · RAN4-90 은 `Regarding the RAN2 agreement`
      뒤 RAN2 합의 상자).
    - 표 바로 앞 글 줄(사이에 다른 표가 없을 때)의 `lead_source` 가 quote 면 내지 않는다(RAN1-124 의 `The following
      agreement was agreed in RAN1 #123 meeting.` 뒤 상자). restated 면 상자 글 줄이 모두 앞서 읽은 문단 결정 · 상자
      결정의 줄에 있을 때만 내지 않는다(RAN1-120 · RAN1-124 의 승인한 LS 안에 다시 적은 이번 회의 합의).
    - 앞 글 줄이 출처를 밝히지 않으면 표가 든 절 머리의 `head_form`(결정을 모아 다시 적은 요약 절)을 같은 규칙으로 본다.

    칸 안에서 표지 줄 앞에 놓인 칸 문단은 문맥으로 보지 않는다.
    """
    prev = box.prev_para
    own = decision_marks.meeting_key(meeting) if meeting else None
    j = prev
    while j >= 0 and not (heads[j] or hard[j] or decision_marks.ENTRY_LINE.match(texts[j])):
        j -= 1
    if j >= 0 and heads[j] == "abstract":
        if not abstract_notes:
            return True
        t2 = list(texts[:prev + 1]) + [docx_text.final_text(box.line).strip()] + list(texts[prev + 1:])
        h2 = list(hard[:prev + 1]) + [False] + list(hard[prev + 1:])
        k2 = list(heads[:prev + 1]) + [None] + list(heads[prev + 1:])
        if decision_marks.abstract_quote(t2, h2, k2, prev + 1, j, box.mark, kinds, companies,
                                         own[0] if own else None):
            return True
    form = None
    p = prev
    while p >= 0 and not texts[p]:
        p -= 1
    if (p >= 0 and p in para_to_body and decision_marks.classify(texts[p], kinds) is None
            and all(b.tag == _P_TAG for b in blocks[para_to_body[p] + 1:box.body_index])):
        form = decision_marks.lead_source(texts[p], own)
    h = prev
    while h >= 0 and not hard[h]:
        h -= 1
    form = form or (decision_marks.head_form(texts[h], own) if h >= 0 else None)
    if form == "quote":
        return True
    if form != "restated":
        return False
    seen: set[str] = set()
    for idx, end in spans:
        if idx <= prev:
            m = decision_marks.classify(texts[idx], kinds)
            seen.update(x for x in [m.inline if m else ""] + list(texts[idx + 1:end]) if x)
    for b in earlier:
        seen.update(_lines(b))
    return decision_marks.reprinted(_lines(box), seen)


def box_reprints(restated: dict, boxes: Sequence[BoxMark]) -> set[int]:
    """이번 회의 결정을 다시 적는다고 밝힌 문단 표지(`decision_spans` 의 restated 사전) 중 남은 글 줄이 모두 그보다
    앞에 놓인 상자 결정의 줄에 있는 것의 문단 번호 — 문단 흐름의 reprinted 는 앞 문단 결정만 보고, 상자의
    `outside_context` 는 앞 문단 결정과 앞 상자를 함께 본다. 이 함수가 남은 한쪽(문단 다시 적기 ↔ 앞 상자 원본)을
    본다. boxes 는 추출기가 결정으로 내는 상자다(내지 않는 상자는 원본 기록이 아니다).
    """
    out = set()
    for i, rest in restated.items():
        seen = [x for b in boxes if (b.prev_para if b.prev_para is not None else -1) < i for x in _lines(b)]
        if decision_marks.reprinted(rest, seen):
            out.add(i)
    return out


def table_marks(tbl, parent, *, companies: frozenset, meeting: Optional[str],
                kinds=tuple(decision_marks.KEYWORDS), **span_kw) -> Iterator[tuple]:
    """표 칸마다 칸 문단을 `decision_marks.decision_spans` 로 읽어 (Mark, 표지 칸 문단, 본문 블록)을 낸다."""
    from docx.text.paragraph import Paragraph

    for _gone, cells in docx_text.table_grid(tbl):
        if any(TDOC_CELL.fullmatch(t) or MEETING_CELL.fullmatch(t)
               for t in (docx_text.cell_text(cell.tc).strip() for cell in cells)):
            continue
        for cell in cells:
            if cell.vmerge == "continue":
                continue
            blocks = list(docx_text.iter_blocks(cell.tc))
            where = [b for b, block in enumerate(blocks) if block.tag == _P_TAG]
            paras = [Paragraph(blocks[b], parent) for b in where]
            texts = [docx_text.final_text(para).strip() for para in paras]
            read: set[int] = set()
            # 표지는 `classify` 가 읽는 줄에서만 열린다 — 표지 줄이 없는 칸은 스타일 · 목록을 읽지 않는다
            if any(t and decision_marks.classify(t, kinds) for t in texts):
                blank, hard, after = [], [], set()
                for k, para in enumerate(paras):
                    style = para.style.name.lower() if para.style else ""
                    blank.append(not texts[k] and docx_text.blank_line(para))
                    hard.append(style.startswith('heading') or style == 'miniheading')
                    if k and where[k] - where[k - 1] > 1:
                        after.add(k)
                for k, mark, end in decision_marks.decision_spans(
                        texts, blank, hard, after, kinds=kinds, companies=companies, meeting=meeting,
                        lists=docx_text.list_keys(paras), **span_kw):
                    stop = where[end] if end < len(where) else len(blocks)
                    read.update(range(where[k] + 1, stop))
                    body = [Paragraph(b, parent) if b.tag == _P_TAG else b for b in blocks[where[k] + 1:stop]]
                    yield mark, paras[k], body
            for b, block in enumerate(blocks):
                if block.tag != _P_TAG and b not in read:
                    yield from table_marks(block, parent, companies=companies, meeting=meeting, kinds=kinds,
                                           **span_kw)
