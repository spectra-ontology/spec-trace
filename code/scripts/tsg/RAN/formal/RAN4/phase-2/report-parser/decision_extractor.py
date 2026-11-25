#!/usr/bin/env python3
"""
Decision Extractor for RAN4 Final Reports

Spec: docs/tsg/RAN/formal/RAN4/phase-2/design-spec/tdoc_ontology_specs(Final_report).md

RAN3 대비 차이:
- TDoc 패턴: R4-\\d{7} (not R3-\\d{6})
- Summary 추출 없음 (Moderator 0건)
- meeting_id 접두사: RAN4#

RAN1 대비 차이:
- Body-aware extraction (w:tbl support) 유지
- contentWithEquations 복원 (RAN4 OMML 580건 실측 — m:oMath 510 + m:oMathPara 70)
- 결정 표지와 본문 끝은 RAN WG 다섯 곳이 함께 쓰는 `decision_marks` 가 읽는다
"""

import re
import sys
import zipfile
from pathlib import Path
from typing import Optional

from models import Decision, DecisionType, Section
from annex import element_style_name, is_annex_heading, outline_level, style_names

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "common"))
import docx_text  # noqa: E402
import decision_marks  # noqa: E402
import decision_boxes  # noqa: E402

# Equation support
try:
    from equation_converter import build_text_with_latex, table_text_with_latex
except ImportError:
    build_text_with_latex = table_text_with_latex = None

# Namespace for Word XML
_W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

# Spec §4.3: 부정 합의 패턴 — 하나라도 매칭 시 hasConsensus = false
_NEG_CONSENSUS_RE = re.compile(
    r'(?i)'
    r'(?:'
    r'no\s+\w*\s*consensus'
    r'|not\s+\w*\s*consensus'
    r'|did\s+not\s+reach\s+consensus'
    r'|could\s+not\s+reach\s+consensus'
    r'|has\s+not\s+reached?\s+consensus'
    r'|lack\s+of\s+consensus'
    r')'
)

# decision_marks 결정 종류 → DecisionType.
DECISION_TYPES = {
    "agreement": DecisionType.AGREEMENT,
    "conclusion": DecisionType.CONCLUSION,
    "working_assumption": DecisionType.WORKING_ASSUMPTION,
}


# Spec §4.1: RAN4 TDoc 참조 패턴 (7자리)
# 느슨한 꼴(`R1- 2004871` · `R12211014`)까지 읽고 `R1-2004871` 꼴로 바꾼다 — decision_marks.tdoc_number 참고.
TDOC_WG, TDOC_DIGITS = "4", "7"

# FFS / TBD patterns
FFS_PATTERN = re.compile(r'\bFFS\b', re.IGNORECASE)
TBD_PATTERN = re.compile(r'\bTBD\b', re.IGNORECASE)

# Note pattern (Spec §3.1)
NOTE_PATTERN = re.compile(r'^Note\s*:', re.IGNORECASE)


class DecisionExtractor:
    """Extract decisions from RAN4 document paragraphs.

    Two-phase: decision mark detection (`decision_marks`) -> content extraction.
    equation_map 지원으로 contentWithEquations 생성. equation_converter 는 본문 문단 번호가 없는 칸 문단(표 상자 결정 ·
    본문 표)의 수식을 따로 바꾸는 데 쓴다.
    """

    def __init__(self, sections: list[Section], docx_path: Optional[Path] = None,
                 equation_map: Optional[dict] = None, equation_converter=None):
        self.sections = sections
        self._section_by_index: dict[int, Section] = {}
        self._build_section_index()

        # Equation map (from EquationConverter.preprocess_paragraphs)
        self.equation_map = equation_map or {}
        self._equation_converter = equation_converter

        # Body-aware extraction for w:tbl support
        if docx_path:
            self._para_to_body, self._body_children = self._build_body_map(docx_path)
        else:
            self._para_to_body, self._body_children = {}, []
        # 회의록 파일 줄기(`RAN4-93`) — 꼬리표가 이 회의인 인용 꼴 표지를 decision_marks 가 가를 때 쓴다
        self._meeting_stem = docx_path.stem.removeprefix("Final_Report_") if docx_path else None

        # Cache inverse body→para map once (was O(D×P) when rebuilt per call)
        self._body_to_para: dict[int, int] = {
            bi: pi for pi, bi in self._para_to_body.items()
        }

    def _build_section_index(self) -> None:
        for section in self.sections:
            for idx in range(section.start_index, section.end_index):
                self._section_by_index[idx] = section

    @staticmethod
    def _build_body_map(docx_path: Path) -> tuple[dict[int, int], list]:
        """Build para_idx -> body_idx mapping for w:tbl support.

        본문 블록(w:p · w:tbl, 블록 w:sdt 안 포함)을 `docx_text.iter_blocks` 순서로 센다 —
        문단 목록(`docx_text.body_paragraphs`)과 같은 순서라 번호가 맞는다.
        """
        try:
            with zipfile.ZipFile(docx_path, 'r') as zf:
                xml_content = docx_text.zip_part(zf, 'word/document.xml')
        except Exception:
            return {}, []

        from xml.etree import ElementTree as ET
        root = ET.fromstring(xml_content)
        body = root.find(f'{{{_W_NS}}}body')
        if body is None:
            return {}, []

        body_children = list(docx_text.iter_blocks(body))
        p_tag = f'{{{_W_NS}}}p'
        para_to_body: dict[int, int] = {}
        para_idx = 0
        for body_idx, child in enumerate(body_children):
            if child.tag == p_tag:
                para_to_body[para_idx] = body_idx
                para_idx += 1

        return para_to_body, body_children

    def _table_to_text(self, tbl_element) -> str:
        """Convert w:tbl XML element to pipe-delimited text.

        Each row becomes: | cell1 | cell2 | cell3 |
        칸 글은 `docx_text.table_line_rows` 가 읽는다 — 칸 안 문단을 본문과 같은 `_marked` 로 읽은 글
        (변경 표시로 빠진 글 제외 · 수식 · 그림 자리는 표지), 가로 합친 칸은 한 번, 세로 합친 칸은
        합침을 시작한 칸의 글. `w:t` 를 빈칸으로 이으면 run 경계에서 낱말과 tdoc 번호(`R1-` `2001234`)가 갈라진다.
        """
        return '\n'.join(docx_text.table_line_rows(tbl_element, para=self._marked))

    def _marked(self, para) -> str:
        """본문 문단 글 — 확정 글에 수식(OMML)은 `[EQUATION]`, 그림은 `[FIGURE]`(MathType 그림 · OLE 수식은
        `[EQUATION]`)로 남기고 글상자 안 글을 넣는다(`docx_text.marked_text`)."""
        return docx_text.marked_text(para, is_equation_image=self._eq_image)

    def _table_with_equations(self, tbl_element) -> str:
        """contentWithEquations 의 표 글 — `_table_to_text` 와 같은 꼴에 칸 문단의 수식을 넣는다(`table_text_with_latex`)."""
        return table_text_with_latex(tbl_element, self._equation_converter, is_equation_image=self._eq_image)

    def extract_decisions(
        self, paragraphs: list, meeting_id: str
    ) -> tuple[list[Decision], list[Decision], list[Decision]]:
        """Extract all decisions from document paragraphs."""
        # 본문 판독기(_marked)가 그림 · OLE 개체를 수식 그림과 그 밖의 그림으로 가르는 데 쓴다
        self._eq_image = docx_text.equation_images(paragraphs[0].part) if paragraphs else None
        # (문서 자리, 결정 종류, Mark, 표지 줄 글, 본문, 의제를 정할 문단 번호, 본문 블록 범위, 문단 본문 끝 번호 또는 표 상자)
        candidates = [
            ((self._para_to_body.get(idx, idx), 0), decision_type, mark, self._marked(paragraphs[idx]),
             self._extract_content(paragraphs, idx + 1, boundary), idx, self._body_blocks(idx, boundary), boundary)
            for decision_type, idx, mark, boundary in self._find_candidates(paragraphs)
        ]
        candidates += self._box_candidates(paragraphs)
        # 이번 회의 결정을 다시 적는다고 밝힌 문단 표지의 글 줄이 모두 앞 표 상자 결정에 있으면 내지 않는다
        drop = decision_boxes.box_reprints(self._restated, self._boxes)
        candidates = [c for c in candidates if c[0][1] or c[5] not in drop]
        candidates.sort(key=lambda c: c[0])

        agreements = []
        conclusions = []
        working_assumptions = []
        counters: dict[tuple[DecisionType, str], int] = {}

        for _pos, decision_type, mark, line, following, keyword_idx, body_blocks, boundary in candidates:
            # 한정어 꼴 표지 줄(mark.lead)은 뒤 본문이 있거나 그 줄 혼자 결정 문장일 때만 결정이다
            if mark.lead is not None and not following.strip() and not decision_marks.lead_stands_alone(mark):
                continue
            # 표지 줄에 든 본문도 본문과 같은 판독기로 다시 읽는다 — 수식 · 그림 표지와 글상자 글이 든다
            head = decision_marks.mark_head(mark, line)
            if head:
                content = head + ('\n' + following if following.strip() else '')
            else:
                content = following

            if not content.strip():
                continue

            # Split Note: block (Spec §3.1)
            content, note = self._split_note(content)
            if not content.strip():
                continue

            # Get agenda — 본문 앞에 놓인 표 상자는 앞 문단이 없어 UNKNOWN 이다
            agenda = self._get_agenda_for_index(keyword_idx) if keyword_idx is not None else "UNKNOWN"

            # Generate ID — Spec §3.2: {TYPE}-{meeting}-{agenda}-{seq}
            counter_key = (decision_type, agenda)
            counters[counter_key] = counters.get(counter_key, 0) + 1
            count = counters[counter_key]

            prefix = self._get_decision_prefix(decision_type)
            meeting_num = meeting_id.replace("RAN4#", "")
            decision_id = f"{prefix}-{meeting_num}-{agenda}-{count:03d}"

            # hasConsensus for Conclusion (Spec §4.3)
            has_consensus = None
            if decision_type == DecisionType.CONCLUSION:
                has_consensus = not _NEG_CONSENSUS_RE.search(content)

            # Build content_with_equations (contentWithEquations Spec §3.1)
            content_with_equations = None
            # 표 상자 결정의 칸 문단은 equation_map 의 본문 문단 번호에 없어 칸 문단을 따로 바꾼다
            if isinstance(boundary, decision_boxes.BoxMark):
                content_with_equations = self._box_content_with_equations(boundary)
            else:
                content_with_equations = self._build_content_with_equations(
                    paragraphs, keyword_idx + 1, boundary, mark
                )
            if content_with_equations:
                content_with_equations, _ = self._split_note(content_with_equations)
            # 수식 자리가 모두 지운 변경 표시 안에 있으면 본문과 같다 — 같은 글을 두 번 싣지 않는다
            if content_with_equations == content:
                content_with_equations = None

            decision = Decision(
                decision_id=decision_id,
                decision_type=decision_type,
                meeting_id=meeting_id,
                agenda_item=agenda,
                content=content,
                content_with_equations=content_with_equations,
                paragraph_index=keyword_idx if keyword_idx is not None else 0,
                body_blocks=body_blocks,
                sequence=count,
                note=note,
                referenced_tdocs=list(dict.fromkeys(decision_marks.tdoc_ids(content, TDOC_WG, TDOC_DIGITS))),  # 같은 번호가 표 행마다 되풀이돼도 참조는 하나
                has_ffs=bool(FFS_PATTERN.search(content)),
                has_tbd=bool(TBD_PATTERN.search(content)),
                has_consensus=has_consensus,
            )

            if decision_type == DecisionType.AGREEMENT:
                agreements.append(decision)
            elif decision_type == DecisionType.CONCLUSION:
                conclusions.append(decision)
            else:
                working_assumptions.append(decision)

        return agreements, conclusions, working_assumptions

    def _find_candidates(self, paragraphs: list) -> list[tuple]:
        """Find all decision marks and where their content ends.

        Returns list of (DecisionType, keyword_idx, Mark, content_end) — 본문은 keyword_idx 다음 문단부터
        content_end 앞까지다.

        표지와 본문 끝은 `decision_marks.decision_spans` 가 읽는다.
        절 머리는 제목 꼴 문단 · 제목 꼴 `Annex X` 문단 · 절 인식(`report_parser._build_sections`)이 절을 연 문단이다.
        제목 꼴이 아닌 `Annex X` 줄은 절 머리가 아니다 — Abstract 글이나 결정 뒤 `Annex A.3: multiple CC configurations`
        같은 문단에서 본문이 끝나지 않게 한다.
        목차 문단과 제목 꼴 `Annex X` 문단부터 끝까지의 부록 문단은 표지로 읽지 않는다.
        문단마다 든 번호 매김 목록 자리(`docx_text.list_keys`)도 넘겨, 표지 뒤에 붙은 이름표 줄이 앞 줄의 목록 항목인지 가르게 한다.

        목차 밖 본문에서 목차 스타일로 쓴 제목은 절을 열므로 Heading 제목처럼 절 머리이고 목차 문단이 아니다.
        스타일만 보면 그 제목이 머리가 되지 못해, 앞 절의 결정 본문이 다음 절의 내용과 참조까지 읽는다.
        목차 스타일 문단 전부를 머리로 두지 않는 것은, 실제 목차 줄과 결정 본문 안의 목록 줄은 절을 열지 않기 때문이다.
        """
        texts: list[str] = []
        blank: list[bool] = []
        hard: list[bool] = []
        skip: list[int] = []
        in_annex = False
        self._annex_from = None
        section_heads = {section.start_index for section in self.sections}
        # 스타일 이름은 id → 이름 표로 읽는다 — 문단마다 `para.style` 을 풀면 큰 문서에서 느리다
        styles = style_names(paragraphs[0].part.styles.element) if paragraphs else ({}, "")
        for idx, para in enumerate(paragraphs):
            text = docx_text.final_text(para).strip()
            style = element_style_name(para._element, styles)
            texts.append(text)
            blank.append(not text and docx_text.blank_line(para))
            annex_head = is_annex_heading(text, style, outline_level(para._element))
            hard.append(style.startswith('heading') or annex_head or idx in section_heads)
            if annex_head and not in_annex:
                in_annex = True
                self._annex_from = idx
            if (style.startswith('toc') and idx not in section_heads) or in_annex:
                skip.append(idx)
        self._companies = decision_marks.report_companies(texts, entry_sources=False)
        self._spans, self._restated = [], {}
        self._texts, self._hard = texts, hard
        return [
            (DECISION_TYPES[mark.kind], idx, mark, end)
            for idx, mark, end in decision_marks.decision_spans(
                texts, blank, hard, self._after_block(), companies=self._companies, skip=skip,
                # RAN4 Tdoc 항목의 Abstract 칸에는 회의 결과를 옮긴 WF 문서 초록이 있어 그 칸 표지도 읽는다
                abstract_notes=True, meeting=self._meeting_stem, lists=docx_text.list_keys(paragraphs),
                spans=self._spans, restated=self._restated)
        ]

    def _box_candidates(self, paragraphs: list) -> list[tuple]:
        """어느 결정 본문에도 들지 않은 표의 칸 안 결정(`decision_boxes.box_marks`) — `extract_decisions` 의 후보 꼴로.

        의제를 정할 문단은 표 앞 마지막 본문 문단이고, 본문 블록 범위는 그 표 하나다. 문단 본문 끝 번호는 None 이다.
        부록 머리 뒤의 표는 문단 표지처럼 읽지 않고, 표 앞 본문 문맥(Abstract 칸 표지 규칙 ·
        출처 회의를 밝힌 앞 글 줄)도 문단 흐름과 같게 본다.
        """
        self._boxes = decision_boxes.box_marks(
            paragraphs, self._body_children, self._para_to_body, self._spans,
            companies=self._companies, meeting=self._meeting_stem, stop=self._annex_from,
            texts=self._texts, hard=self._hard, abstract_notes=True)
        return [((box.body_index, n), DECISION_TYPES[box.mark.kind], box.mark, self._marked(box.line),
                 box.following(self._marked, self._table_to_text), box.prev_para,
                 [box.body_index, box.body_index + 1], box)
                for n, box in enumerate(self._boxes, 1)]

    def _box_content_with_equations(self, box: decision_boxes.BoxMark) -> Optional[str]:
        """표 상자 결정의 contentWithEquations — 칸 문단을 따로 LaTeX 로 바꿔 읽는다(`box.paragraphs()` 의 0 번이 표지 줄).

        본문 문단의 수식 표(`equation_map`)는 본문 문단 번호로 매겨져 칸 문단을 담지 않는다. 칸 안 표는 문단 결정의 본문
        표와 같은 꼴에 칸 문단의 수식을 넣어 읽는다(`_table_with_equations`). 표지 줄 · 본문 블록(칸 안 표 포함)에 수식이
        없으면 None 이다.
        """
        if not (build_text_with_latex and self._equation_converter):
            return None
        has_head = bool(box.mark.inline or box.mark.lead)
        if not any(docx_text.has_math(b) for b in ([box.line] if has_head else []) + list(box.body)):
            return None
        eq_map = self._equation_converter.preprocess_paragraphs(box.paragraphs())
        parts: list[str] = []
        if has_head:
            parts.append(decision_marks.mark_head(box.mark, build_text_with_latex(
                box.line._element, eq_map.get(0, {}), is_equation_image=self._eq_image)))
        k = 0
        for block in box.body:
            if hasattr(block, '_element'):
                k += 1
                text = build_text_with_latex(block._element, eq_map.get(k, {}),
                                             is_equation_image=self._eq_image).strip()
            else:
                text = self._table_with_equations(block)
            if text:
                parts.append(text)
        return '\n'.join(parts) if parts else None

    def _after_block(self) -> set[int]:
        """바로 앞에 표(w:tbl)가 놓인 문단 번호 — 결정 본문 끝을 읽을 때 표를 본문 덩어리로 넘긴다."""
        p_tag = f'{{{_W_NS}}}p'
        tbl_tag = f'{{{_W_NS}}}tbl'
        after: set[int] = set()
        pending, para_idx = False, 0
        for child in self._body_children:
            if child.tag == p_tag:
                if pending:
                    after.add(para_idx)
                    pending = False
                para_idx += 1
            elif child.tag == tbl_tag:
                pending = True
        return after

    def _body_blocks(self, keyword_idx: int, end_index: int) -> Optional[list[int]]:
        """결정이 차지한 본문 블록 범위 [시작, 끝) — 표지 줄 블록부터 본문 끝 문단(end_index) 블록 앞까지.

        번호는 표 · 그림 · 차트의 `paragraph_index` 와 같은 `docx_text.iter_blocks` 블록 번호다. 본문 문단 사이에
        놓인 표(w:tbl)는 `_extract_content` 가 결정 본문으로 읽으므로, 이 범위 안에 놓인 표 · 그림 · 차트가 이 결정에
        딸린 것이다(JSON-LD 의 hasTable · hasFigure · hasChart). 블록 표를 만들지 못한 문서는 None 이다.
        """
        if keyword_idx not in self._para_to_body:
            return None
        return [self._para_to_body[keyword_idx],
                self._para_to_body.get(end_index, len(self._body_children))]

    def _extract_content(
        self, paragraphs: list, start_index: int, end_index: int
    ) -> str:
        """Extract and join content paragraphs + embedded tables (body-aware)."""
        content_parts = []
        tbl_tag = f'{{{_W_NS}}}tbl'
        p_tag = f'{{{_W_NS}}}p'

        # 표지 줄의 body 자리 바로 다음부터 읽는다 — 표지 줄과 다음 문단 사이에 놓인 표도 본문이다
        if self._body_children and start_index - 1 in self._para_to_body:
            body_start = self._para_to_body[start_index - 1] + 1
            body_end = self._para_to_body.get(end_index, len(self._body_children))

            body_to_para = self._body_to_para

            for body_idx in range(body_start, body_end):
                child = self._body_children[body_idx]
                if child.tag == p_tag:
                    para_idx = body_to_para.get(body_idx)
                    if para_idx is not None and para_idx < len(paragraphs):
                        text = self._marked(paragraphs[para_idx])
                        if text:
                            content_parts.append(text)
                elif child.tag == tbl_tag:
                    table_text = self._table_to_text(child)
                    if table_text:
                        content_parts.append(table_text)
        else:
            for idx in range(start_index, end_index):
                text = self._marked(paragraphs[idx])
                if text:
                    content_parts.append(text)

        return '\n'.join(content_parts)

    def _build_content_with_equations(
        self, paragraphs: list, start_index: int, end_index: int, mark: decision_marks.Mark
    ) -> Optional[str]:
        """Build content text with inline $LaTeX$ equations.

        RAN1 _build_content_with_equations를 RAN4 tuple candidate 형식에 맞게 포팅.
        start_index 는 표지 다음 문단, mark 는 그 앞 표지 줄을 읽은 `decision_marks.Mark` 다.
        """
        if not build_text_with_latex:
            return None

        # Check if any paragraph in content range has equations
        head = mark.inline or mark.lead
        check_start = start_index - 1 if head else start_index
        # 본문 블록(표지 줄에 든 본문 · 문단 · 표)에 수식(OMML · 글을 읽은 수식 OLE 개체 · 수식 그림, `docx_text.has_math`)이 있는
        # 결정만 — 표 칸의 수식도 든다
        if self._body_children and start_index - 1 in self._para_to_body:
            first = self._para_to_body[start_index - 1] + (0 if head else 1)
            blocks = self._body_children[first:self._para_to_body.get(end_index, len(self._body_children))]
        else:
            blocks = paragraphs[check_start:end_index]
        if not any(docx_text.has_math(b) for b in blocks):
            return None

        parts: list[str] = []
        tbl_tag = f'{{{_W_NS}}}tbl'
        p_tag = f'{{{_W_NS}}}p'

        # 표지 줄에 든 본문 — 수식을 LaTeX 로 넣은 글을 다시 표지로 읽어 같은 종류일 때 그 본문을 쓴다
        if head:
            kw_idx = start_index - 1
            if 0 <= kw_idx < len(paragraphs):
                parts.append(decision_marks.mark_head(mark, build_text_with_latex(
                    paragraphs[kw_idx]._element,
                    self.equation_map.get(kw_idx, {}),
                    is_equation_image=self._eq_image,
                )))

        # Body-aware following content
        # 표지 줄의 body 자리 바로 다음부터 읽는다 — 표지 줄과 다음 문단 사이에 놓인 표도 본문이다
        if self._body_children and start_index - 1 in self._para_to_body:
            body_start = self._para_to_body[start_index - 1] + 1
            body_end = self._para_to_body.get(end_index, len(self._body_children))

            body_to_para = self._body_to_para

            for body_idx in range(body_start, body_end):
                child = self._body_children[body_idx]
                if child.tag == p_tag:
                    para_idx = body_to_para.get(body_idx)
                    if para_idx is not None and para_idx < len(paragraphs):
                        text = build_text_with_latex(
                            paragraphs[para_idx]._element,
                            self.equation_map.get(para_idx, {}),
                            is_equation_image=self._eq_image,
                        ).strip()
                        if text:
                            parts.append(text)
                elif child.tag == tbl_tag:
                    table_text = self._table_with_equations(child)
                    if table_text:
                        parts.append(table_text)
        else:
            # Fallback: paragraph-only
            for idx in range(start_index, end_index):
                if idx < len(paragraphs):
                    text = build_text_with_latex(
                        paragraphs[idx]._element,
                        self.equation_map.get(idx, {}),
                        is_equation_image=self._eq_image,
                    ).strip()
                    if text:
                        parts.append(text)

        return '\n'.join(parts) if parts else None

    def _get_agenda_for_index(self, para_index: int) -> str:
        if para_index in self._section_by_index:
            return self._section_by_index[para_index].agenda_number

        closest_section = None
        for section in self.sections:
            if section.start_index <= para_index:
                closest_section = section
            else:
                break

        return closest_section.agenda_number if closest_section else "UNKNOWN"

    def _get_decision_prefix(self, decision_type: DecisionType) -> str:
        return {
            DecisionType.AGREEMENT: "AGR",
            DecisionType.CONCLUSION: "CON",
            DecisionType.WORKING_ASSUMPTION: "WA",
        }[decision_type]

    @staticmethod
    def _split_note(content: str) -> tuple[str, Optional[str]]:
        """Split Note: block from content (Spec §3.1)."""
        lines = content.split('\n')
        note_start = None
        for i, line in enumerate(lines):
            if NOTE_PATTERN.match(line.strip()):
                note_start = i
                break
        if note_start is None:
            return content, None
        main = '\n'.join(lines[:note_start]).strip()
        note_lines = lines[note_start:]
        note_lines[0] = re.sub(
            r'^Note\s*:\s*', '', note_lines[0].strip(), flags=re.IGNORECASE
        )
        note_text = '\n'.join(note_lines).strip()
        return main, note_text if note_text else None
