#!/usr/bin/env python3
"""
Decision Extractor - Extract Agreements, Conclusions, Working Assumptions

결정 표지와 본문 끝은 RAN WG 다섯 곳이 함께 쓰는 `decision_marks` 가 읽는다.
Integrates with AgendaMatcher for correct agenda assignment.
"""

import re
import sys
import zipfile
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from xml.etree import ElementTree as ET


# Namespace for Word XML (body-level parsing)
_W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

from models import Decision, DecisionType, Section
from annex import is_annex_heading, outline_level

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "common"))
import docx_text  # noqa: E402
import decision_marks  # noqa: E402
import decision_boxes  # noqa: E402

# Spec §4.3: 부정 합의 패턴 — 하나라도 매칭 시 hasConsensus = false
_NEG_CONSENSUS_RE = re.compile(
    r'(?i)'
    r'(?:'
    r'no\s+\w*\s*consensus'           # 패턴 1: no [0~1단어] consensus
    r'|not\s+\w*\s*consensus'         # 패턴 2: not [0~1단어] consensus
    r'|did\s+not\s+reach\s+consensus' # 패턴 3
    r'|could\s+not\s+reach\s+consensus'  # 패턴 4
    r'|has\s+not\s+reached?\s+consensus'  # 패턴 5
    r'|lack\s+of\s+consensus'         # 패턴 6
    r')'
)

try:
    from equation_converter import build_text_with_latex, table_text_with_latex
except ImportError:
    build_text_with_latex = table_text_with_latex = None


# decision_marks 결정 종류 → DecisionType.
DECISION_TYPES = {
    "agreement": DecisionType.AGREEMENT,
    "conclusion": DecisionType.CONCLUSION,
    "working_assumption": DecisionType.WORKING_ASSUMPTION,
}


# Pattern to extract Tdoc references
# 느슨한 꼴(`R1- 2004871` · `R12211014`)까지 읽고 `R1-2004871` 꼴로 바꾼다 — decision_marks.tdoc_number 참고.
TDOC_WG, TDOC_DIGITS = r"\d", "7"

# Pattern to detect FFS (For Further Study)
FFS_PATTERN = re.compile(r'\bFFS\b', re.IGNORECASE)

# Pattern to detect TBD (To Be Determined)
TBD_PATTERN = re.compile(r'\bTBD\b', re.IGNORECASE)

# Pattern to detect Note: block (Spec §3.1: note 속성)
# Note appears as a separate paragraph starting with "Note:" at the end of content
NOTE_PATTERN = re.compile(r'^Note\s*:', re.IGNORECASE)


@dataclass
class DecisionCandidate:
    """Decision mark found by `decision_marks` and where its content ends."""
    decision_type: DecisionType
    keyword_index: int  # Paragraph index of the mark line
    mark: decision_marks.Mark  # 표지 줄을 읽은 결과 — 표지 줄에 든 본문(inline · lead)
    content_end: int  # 본문은 keyword_index 다음 문단부터 이 번호 앞까지


class DecisionExtractor:
    """
    Extract decisions from document paragraphs.

    Two-phase approach:
    1. Mark detection: `decision_marks.decision_spans` finds decision marks and where each content ends
    2. Content extraction: join the paragraphs and tables in that span
    """

    def __init__(self, sections: list[Section], equation_converter=None,
                 docx_path: Optional[Path] = None):
        """
        Initialize with document sections.

        Args:
            sections: List of sections with agenda numbers
            equation_converter: Optional EquationConverter for contentWithEquations
            docx_path: Path to DOCX file for body-aware extraction (w:tbl support)
        """
        self.sections = sections
        self._equation_converter = equation_converter
        self._eq_map: dict[int, dict[int, str]] = {}
        self._section_by_index: dict[int, Section] = {}
        self._build_section_index()

        # Body-aware extraction: map para_idx → body_idx for w:tbl support
        if docx_path:
            self._para_to_body, self._body_children = self._build_body_map(docx_path)
        else:
            self._para_to_body, self._body_children = {}, []
        self._body_to_para = {body: para for para, body in self._para_to_body.items()}
        # 회의록 파일 줄기(`RAN4-93`) — 꼬리표가 이 회의인 인용 꼴 표지를 decision_marks 가 가를 때 쓴다
        self._meeting_stem = docx_path.stem.removeprefix("Final_Report_") if docx_path else None

    def _build_section_index(self) -> None:
        """Build index for quick section lookup by paragraph index."""
        for section in self.sections:
            for idx in range(section.start_index, section.end_index):
                self._section_by_index[idx] = section

    @staticmethod
    def _build_body_map(docx_path: Path) -> tuple[dict[int, int], list]:
        """Build para_idx→body_idx mapping and body_children list.

        본문 블록(w:p · w:tbl, 블록 w:sdt 안 포함)을 `docx_text.iter_blocks` 순서로 순회하여
        paragraph 인덱스↔body 인덱스 매핑 생성. 문단 목록(`docx_text.body_paragraphs`)과 같은
        순서라 번호가 맞고, paragraph 범위 사이에 끼어있는 w:tbl도 추출 가능.
        """
        try:
            with zipfile.ZipFile(docx_path, 'r') as zf:
                xml_content = docx_text.zip_part(zf, 'word/document.xml')
        except Exception:
            return {}, []

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
        self,
        paragraphs: list,
        meeting_id: str
    ) -> tuple[list[Decision], list[Decision], list[Decision]]:
        """
        Extract all decisions from document paragraphs.

        Args:
            paragraphs: List of docx paragraphs
            meeting_id: Meeting ID for decision IDs

        Returns:
            Tuple of (agreements, conclusions, working_assumptions)
        """
        # Pre-process equations for contentWithEquations (Spec §4.5)
        if self._equation_converter:
            self._eq_map = self._equation_converter.preprocess_paragraphs(
                paragraphs
            )

        # Find candidates
        # 본문 판독기(_marked)가 그림 · OLE 개체를 수식 그림과 그 밖의 그림으로 가르는 데 쓴다
        self._eq_image = docx_text.equation_images(paragraphs[0].part) if paragraphs else None
        # (문서 자리, 결정 종류, Mark, 표지 줄 글, 본문, 의제를 정할 문단 번호, 본문 블록 범위, 문단 후보 또는 표 상자)
        # 문단 결정과 표 상자 결정을 문서 차례로 섞는다 — 의제마다 매기는 순번이 문서 차례를 따른다
        candidates = [
            ((self._para_to_body.get(c.keyword_index, c.keyword_index), 0), c.decision_type, c.mark,
             self._marked(paragraphs[c.keyword_index]),
             self._extract_content(paragraphs, c.keyword_index + 1, c.content_end),  # Skip keyword paragraph
             c.keyword_index, self._body_blocks(c.keyword_index, c.content_end), c)
            for c in self._find_candidates(paragraphs)
        ]
        candidates += self._box_candidates(paragraphs)
        # 이번 회의 결정을 다시 적는다고 밝힌 문단 표지의 글 줄이 모두 앞 표 상자 결정에 있으면 내지 않는다
        drop = decision_boxes.box_reprints(self._restated, self._boxes)
        candidates = [c for c in candidates if c[0][1] or c[5] not in drop]
        candidates.sort(key=lambda c: c[0])

        # Extract content for each candidate
        agreements = []
        conclusions = []
        working_assumptions = []

        # Track decision counts per agenda for ID generation
        counters: dict[tuple[DecisionType, str], int] = {}

        for _pos, decision_type, mark, line, following_content, keyword_idx, body_blocks, source in candidates:
            # 한정어 꼴 표지 줄(mark.lead)은 뒤 본문이 있거나 그 줄 혼자 결정 문장일 때만 결정이다
            if mark.lead is not None and not following_content.strip() and not decision_marks.lead_stands_alone(mark):
                continue

            # 표지 줄에 든 본문은 본문과 같은 판독기로 다시 읽는다 — 수식 · 그림 표지와 글상자 글이 든다 (Spec §3.1)
            head = decision_marks.mark_head(mark, line)
            if head:
                content = head + ('\n' + following_content if following_content.strip() else '')
            else:
                # Header-only: content in following paragraphs
                content = following_content

            if not content.strip():
                continue

            # Split Note: block from content (Spec §3.1: note 속성)
            content, note = self._split_note(content)

            if not content.strip():
                continue

            # Get agenda for this decision — 본문 앞에 놓인 표 상자는 앞 문단이 없어 UNKNOWN 이다
            agenda = self._get_agenda_for_index(keyword_idx) if keyword_idx is not None else "UNKNOWN"

            # Generate decision ID
            counter_key = (decision_type, agenda)
            counters[counter_key] = counters.get(counter_key, 0) + 1
            count = counters[counter_key]

            prefix = self._get_decision_prefix(decision_type)
            meeting_num = meeting_id.replace("RAN1#", "")
            decision_id = f"{prefix}-{meeting_num}-{agenda}-{count:03d}"

            # Determine hasConsensus for Conclusion type
            # Spec §4.3: 부정 합의 패턴 미포함 시 true (6개 패턴)
            has_consensus = None
            if decision_type == DecisionType.CONCLUSION:
                has_consensus = not _NEG_CONSENSUS_RE.search(content)

            # Build content_with_equations (Spec: contentWithEquations §4.5)
            content_with_equations = None
            if isinstance(source, decision_boxes.BoxMark):
                content_with_equations = self._box_content_with_equations(source)
            else:
                content_with_equations = self._build_content_with_equations(
                    paragraphs, source, source.content_end
                )
            if content_with_equations:
                # Also split note from content_with_equations
                content_with_equations, _ = self._split_note(content_with_equations)
            # 수식 자리가 모두 지운 변경 표시 안에 있으면 본문과 같다 — 같은 글을 두 번 싣지 않는다
            if content_with_equations == content:
                content_with_equations = None

            # Create decision
            decision = Decision(
                decision_id=decision_id,
                decision_type=decision_type,
                meeting_id=meeting_id,
                agenda_item=agenda,
                content=content,
                paragraph_index=keyword_idx if keyword_idx is not None else 0,
                body_blocks=body_blocks,
                sequence=count,
                content_with_equations=content_with_equations,
                note=note,
                referenced_tdocs=list(dict.fromkeys(decision_marks.tdoc_ids(content, TDOC_WG, TDOC_DIGITS))),  # 같은 번호가 표 행마다 되풀이돼도 참조는 하나
                has_ffs=bool(FFS_PATTERN.search(content)),
                has_tbd=bool(TBD_PATTERN.search(content)),
                has_consensus=has_consensus,
            )

            # Add to appropriate list
            if decision_type == DecisionType.AGREEMENT:
                agreements.append(decision)
            elif decision_type == DecisionType.CONCLUSION:
                conclusions.append(decision)
            else:
                working_assumptions.append(decision)

        return agreements, conclusions, working_assumptions

    def _find_candidates(self, paragraphs: list) -> list[DecisionCandidate]:
        """Find all decision marks and where their content ends.

        표지와 본문 끝은 `decision_marks.decision_spans` 가 읽는다. 절 머리는 제목 꼴 문단 · 제목 꼴 `Annex X` 문단이다.
        제목 꼴이 아닌 `Annex X` 줄은 절 머리가 아니다 — 결정 본문 안 TP 의 `Annex A.3: …` 문단에서 본문이 끝나지 않게 한다.
        문단마다 든 번호 매김 목록 자리(`docx_text.list_keys`)도 넘겨, 표지 뒤에 붙은 이름표 줄이 앞 줄의 목록 항목인지 가르게 한다.

        Filters out (표지로 읽지 않는다):
        - Annex sections (per Spec requirement) — 제목 꼴 `Annex X` 문단부터 끝까지
        - TOC entries (toc style paragraphs)
        """
        texts: list[str] = []
        blank: list[bool] = []
        hard: list[bool] = []
        skip: list[int] = []
        in_annex = False
        self._annex_from = None

        for idx, para in enumerate(paragraphs):
            text = docx_text.final_text(para).strip()
            style = para.style.name.lower() if para.style else ""
            texts.append(text)
            blank.append(not text and docx_text.blank_line(para))
            annex_head = is_annex_heading(text, style, outline_level(para._element))
            hard.append(style.startswith('heading') or annex_head)

            # Annex start — only on actual headings, not TOC references (TOC entries may contain Annex references)
            if annex_head and not in_annex:
                in_annex = True
                self._annex_from = idx
            if style.startswith('toc') or in_annex:
                skip.append(idx)

        self._companies = decision_marks.report_companies(texts, entry_sources=True)
        self._spans, self._restated = [], {}
        self._texts, self._hard = texts, hard
        return [
            DecisionCandidate(DECISION_TYPES[mark.kind], idx, mark, end)
            for idx, mark, end in decision_marks.decision_spans(
                texts, blank, hard, self._after_block(), companies=self._companies, skip=skip,
                meeting=self._meeting_stem, lists=docx_text.list_keys(paragraphs), spans=self._spans,
                restated=self._restated)
        ]

    def _box_candidates(self, paragraphs: list) -> list[tuple]:
        """어느 결정 본문에도 들지 않은 표의 칸 안 결정(`decision_boxes.box_marks`) — `extract_decisions` 의 후보 꼴로.

        의제를 정할 문단은 표 앞 마지막 본문 문단이고, 본문 블록 범위는 그 표 하나다. 부록 머리 뒤의 표는 문단 표지처럼
        읽지 않는다.
        표 앞 본문 문맥(Tdoc 항목의 Abstract 칸 · 출처 회의를 밝힌 앞 글 줄)은 문단 흐름과 같게 본다.
        """
        self._boxes = decision_boxes.box_marks(
            paragraphs, self._body_children, self._para_to_body, self._spans,
            companies=self._companies, meeting=self._meeting_stem, stop=self._annex_from,
            texts=self._texts, hard=self._hard)
        return [((box.body_index, n), DECISION_TYPES[box.mark.kind], box.mark, self._marked(box.line),
                 box.following(self._marked, self._table_to_text), box.prev_para,
                 [box.body_index, box.body_index + 1], box)
                for n, box in enumerate(self._boxes, 1)]

    def _box_content_with_equations(self, box: decision_boxes.BoxMark) -> Optional[str]:
        """표 상자 결정의 contentWithEquations — 칸 문단을 따로 LaTeX 로 바꿔 읽는다(`box.paragraphs()` 의 0 번이 표지 줄).

        본문 문단의 수식 표(`_eq_map`)는 본문 문단 번호로 매겨져 칸 문단을 담지 않는다. 칸 안 표는 문단 결정의 본문 표와
        같은 꼴에 칸 문단의 수식을 넣어 읽는다(`_table_with_equations`). 표지 줄 · 본문 블록(칸 안 표 포함)에 수식이
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
        self,
        paragraphs: list,
        start_index: int,
        end_index: int
    ) -> str:
        """Extract and join content paragraphs + embedded tables.

        Spec §3.1: content 필드 — 수식을 [EQUATION] 마커로 대체 (검색/쿼리용)

        Body-aware extraction: paragraph 범위 사이에 끼어있는 w:tbl도
        pipe-delimited 텍스트로 변환하여 포함. body_children이 없으면
        기존 paragraph-only 로직으로 fallback.
        """
        content_parts = []
        tbl_tag = f'{{{_W_NS}}}tbl'
        p_tag = f'{{{_W_NS}}}p'

        # 표지 줄의 body 자리 바로 다음부터 읽는다 — 표지 줄과 다음 문단 사이에 놓인 표도 본문이다
        if self._body_children and start_index - 1 in self._para_to_body:
            # Body-aware: paragraph 범위에 대응하는 body 구간 순회
            body_start = self._para_to_body[start_index - 1] + 1
            body_end = self._para_to_body.get(end_index, len(self._body_children))

            for body_idx in range(body_start, body_end):
                child = self._body_children[body_idx]
                if child.tag == p_tag:
                    para_idx = self._body_to_para.get(body_idx)
                    if para_idx is not None and para_idx < len(paragraphs):
                        text = self._marked(paragraphs[para_idx])
                        if text:
                            content_parts.append(text)
                elif child.tag == tbl_tag:
                    table_text = self._table_to_text(child)
                    if table_text:
                        content_parts.append(table_text)
        else:
            # Fallback: 기존 paragraph-only 로직 (DOCM 또는 body_map 미지원)
            for idx in range(start_index, end_index):
                text = self._marked(paragraphs[idx])
                if text:
                    content_parts.append(text)

        return '\n'.join(content_parts)

    def _build_content_with_equations(
        self,
        paragraphs: list,
        candidate: DecisionCandidate,
        content_end: int,
    ) -> Optional[str]:
        """
        Build content text with inline $LaTeX$ equations + embedded tables.

        Mirrors _extract_content logic but uses build_text_with_latex
        to replace OMML equations with $LaTeX$ markup.
        Embedded tables are included as pipe-delimited text — 칸 문단의 수식도 넣는다(`_table_with_equations`).

        Returns None if:
        - No equations in the decision's body blocks (OMML 도, 글을 읽은 수식 OLE 개체 · 수식 그림도 없다 — 표 칸 포함, `docx_text.has_math`)
        - build_text_with_latex is not available
        """
        if not build_text_with_latex:
            return None

        kw_idx = candidate.keyword_index
        content_start = kw_idx + 1
        has_head = bool(candidate.mark.inline or candidate.mark.lead)

        # Check if any paragraph in content range has equations
        # 본문 블록(표지 줄에 든 본문 · 문단 · 표)에 수식이 있는 결정만 — 표 칸의 수식도 든다
        if self._body_children and kw_idx in self._para_to_body:
            first = self._para_to_body[kw_idx] + (0 if has_head else 1)
            blocks = self._body_children[first:self._para_to_body.get(content_end, len(self._body_children))]
        else:
            blocks = paragraphs[kw_idx if has_head else content_start:content_end]
        if not any(docx_text.has_math(b) for b in blocks):
            return None

        parts: list[str] = []
        tbl_tag = f'{{{_W_NS}}}tbl'
        p_tag = f'{{{_W_NS}}}p'

        # 표지 줄에 든 본문 — LaTeX 를 넣은 글에서 다시 읽는다
        if has_head:
            parts.append(decision_marks.mark_head(
                candidate.mark,
                build_text_with_latex(paragraphs[kw_idx]._element, self._eq_map.get(kw_idx, {}),
                                      is_equation_image=self._eq_image),
            ))

        # Following content (body-aware if available)
        # 표지 줄의 body 자리 바로 다음부터 읽는다 — 표지 줄과 다음 문단 사이에 놓인 표도 본문이다
        if self._body_children and kw_idx in self._para_to_body:
            body_start = self._para_to_body[kw_idx] + 1
            body_end = self._para_to_body.get(content_end, len(self._body_children))

            for body_idx in range(body_start, body_end):
                child = self._body_children[body_idx]
                if child.tag == p_tag:
                    para_idx = self._body_to_para.get(body_idx)
                    if para_idx is not None and para_idx < len(paragraphs):
                        text = build_text_with_latex(
                            paragraphs[para_idx]._element,
                            self._eq_map.get(para_idx, {}),
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
            for idx in range(content_start, content_end):
                text = build_text_with_latex(
                    paragraphs[idx]._element,
                    self._eq_map.get(idx, {}),
                    is_equation_image=self._eq_image,
                ).strip()
                if text:
                    parts.append(text)

        return '\n'.join(parts) if parts else None

    def _get_agenda_for_index(self, para_index: int) -> str:
        """Get agenda number for a paragraph index."""
        # Find the section containing this index
        if para_index in self._section_by_index:
            return self._section_by_index[para_index].agenda_number

        # Fallback: find closest section before this index
        closest_section = None
        for section in self.sections:
            if section.start_index <= para_index:
                closest_section = section
            else:
                break

        if closest_section:
            return closest_section.agenda_number

        return "UNKNOWN"

    def _get_decision_prefix(self, decision_type: DecisionType) -> str:
        """Get prefix for decision ID."""
        prefixes = {
            DecisionType.AGREEMENT: "AGR",
            DecisionType.CONCLUSION: "CON",
            DecisionType.WORKING_ASSUMPTION: "WA",
        }
        return prefixes[decision_type]

    @staticmethod
    def _split_note(content: str) -> tuple[str, Optional[str]]:
        """Split Note: block from content. Spec §3.1: note 속성.

        Note appears as a separate paragraph (line) starting with "Note:"
        at the end of the decision content.

        Returns:
            (content_without_note, note_text_or_None)
        """
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
        # Remove "Note:" prefix from first line
        note_lines[0] = re.sub(r'^Note\s*:\s*', '', note_lines[0].strip(), flags=re.IGNORECASE)
        note_text = '\n'.join(note_lines).strip()
        return main, note_text if note_text else None


def extract_decisions_from_docx(
    docx_path: Path,
    sections: list[Section],
    meeting_id: str,
    equation_converter=None,
) -> tuple[list[Decision], list[Decision], list[Decision]]:
    """
    Extract decisions from a DOCX file.

    Args:
        docx_path: Path to DOCX file
        sections: List of sections with agenda numbers
        meeting_id: Meeting ID
        equation_converter: Optional EquationConverter for contentWithEquations

    Returns:
        Tuple of (agreements, conclusions, working_assumptions)
    """
    doc = docx_text.open_document(docx_path)
    extractor = DecisionExtractor(sections, equation_converter, docx_path=docx_path)
    return extractor.extract_decisions(docx_text.body_paragraphs(doc), meeting_id)


if __name__ == "__main__":
    import sys
    from toc_parser import parse_toc_from_docx
    from agenda_matcher import AgendaMatcher, SectionBuilder

    if len(sys.argv) < 2:
        print("Usage: python decision_extractor.py <docx_path>")
        sys.exit(1)

    docx_path = Path(sys.argv[1])
    # 회의는 파이프라인(report_parser)과 같은 규칙으로 읽는다 — 파일 이름의 마지막 `-` 뒤 토막을 떼면
    # `Final_Report_RAN1-100-e` 가 `RAN1#e` 가 되고, 정본 회의 ID 와 다른 ID · 파일 이름이 나온다
    from report_parser import ReportParser
    meeting_id = ReportParser._extract_meeting_id(docx_path)

    # Parse TOC and build sections
    toc_entries = parse_toc_from_docx(docx_path)
    matcher = AgendaMatcher(toc_entries)
    builder = SectionBuilder(matcher)

    # Build sections from document
    doc = docx_text.open_document(docx_path)
    sections = []
    for idx, para in enumerate(docx_text.body_paragraphs(doc)):
        style = para.style.name.lower() if para.style else ""
        if style.startswith('heading'):
            level = int(style.split()[-1]) if style.split()[-1].isdigit() else 1
            section = builder.process_heading(docx_text.final_text(para), level, idx)
            if sections:
                sections[-1].end_index = idx
            sections.append(section)

    if sections:
        sections[-1].end_index = len(docx_text.body_paragraphs(doc))

    # Extract decisions
    agreements, conclusions, was = extract_decisions_from_docx(docx_path, sections, meeting_id)

    print(f"Extracted from {docx_path.name}:")
    print(f"  Agreements: {len(agreements)}")
    print(f"  Conclusions: {len(conclusions)}")
    print(f"  Working Assumptions: {len(was)}")

    # Show first few
    print("\nSample Agreements:")
    for agr in agreements[:3]:
        print(f"  {agr.decision_id}: {agr.content[:80]}...")
