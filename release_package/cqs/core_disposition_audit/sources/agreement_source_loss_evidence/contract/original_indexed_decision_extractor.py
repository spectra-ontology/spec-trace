#!/usr/bin/env python3
"""
Decision Extractor - Extract Agreements, Conclusions, Working Assumptions

Uses regex to detect decision keywords and LLM for boundary/validation.
Integrates with AgendaMatcher for correct agenda assignment.
"""

import re
import zipfile
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from xml.etree import ElementTree as ET

from docx import Document

# Namespace for Word XML (body-level parsing)
_W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

from models import Decision, DecisionType, Section

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
    from equation_converter import build_text_with_latex, build_text_with_markers
except ImportError:
    build_text_with_latex = None
    build_text_with_markers = None


# Decision keyword patterns - Support both header-only and inline content
# Pattern 1: Header only (e.g., "Agreement:")
# Pattern 2: Inline content (e.g., "Agreement: The UE shall...")
# 결정 표지는 회의록마다 방언이 갈린다 — 맨 `Agreement:` 와 대괄호를 두른 `[Agreement]`.
# 소비자가 한 방언만 읽으면 다른 방언으로 적힌 결정은 오류가 아니라 부재로 나타나므로
# 두 방언을 함께 읽는다. 소괄호 `(Working assumption)` 은 일부러 받지 않는다 — 실측상
# 그것은 표지가 아니라 절차 목록 안의 한정 어구여서, 받으면 문장 조각이 결정이 된다.
DECISION_PATTERNS_HEADER = {
    DecisionType.AGREEMENT: re.compile(
        r'^(?:\[\s*agreements?\s*\]|agreements?)\s*:?\s*$',
        re.IGNORECASE
    ),
    DecisionType.CONCLUSION: re.compile(
        r'^(?:\[\s*conclusions?\s*\]|conclusions?)\s*:?\s*$',
        re.IGNORECASE
    ),
    DecisionType.WORKING_ASSUMPTION: re.compile(
        r'^(?:\[\s*working\s*assumptions?\s*\]|working\s*assumptions?)\s*:?\s*$',
        re.IGNORECASE
    ),
}

# Inline patterns - match "Agreement: [content]" where content exists
DECISION_PATTERNS_INLINE = {
    DecisionType.AGREEMENT: re.compile(
        r'^(?:\[\s*agreements?\s*\]\s*:?|agreements?\s*:)\s*(.+)',
        re.IGNORECASE | re.DOTALL
    ),
    DecisionType.CONCLUSION: re.compile(
        r'^(?:\[\s*conclusions?\s*\]\s*:?|conclusions?\s*:)\s*(.+)',
        re.IGNORECASE | re.DOTALL
    ),
    DecisionType.WORKING_ASSUMPTION: re.compile(
        r'^(?:\[\s*working\s*assumptions?\s*\]\s*:?|working\s*assumptions?\s*:)\s*(.+)',
        re.IGNORECASE | re.DOTALL
    ),
}

# Annex section pattern - skip these sections (Spec requirement)
ANNEX_PATTERN = re.compile(r'^Annex\s+[A-Z]', re.IGNORECASE)

# Pattern to extract Tdoc references
TDOC_PATTERN = re.compile(r'R\d-\d{7}')

# Pattern to detect FFS (For Further Study)
FFS_PATTERN = re.compile(r'\bFFS\b', re.IGNORECASE)

# Pattern to detect TBD (To Be Determined)
TBD_PATTERN = re.compile(r'\bTBD\b', re.IGNORECASE)

# Pattern to detect Note: block (Spec §3.1: note 속성)
# Note appears as a separate paragraph starting with "Note:" at the end of content
NOTE_PATTERN = re.compile(r'^Note\s*:', re.IGNORECASE)


@dataclass
class DecisionCandidate:
    """Candidate decision found by regex."""
    decision_type: DecisionType
    keyword_index: int  # Paragraph index of the keyword
    keyword_text: str  # The keyword text
    inline_content: Optional[str] = None  # Content on the same line as keyword


class DecisionExtractor:
    """
    Extract decisions from document paragraphs.

    Two-phase approach:
    1. Regex detection: Find decision keywords (high recall)
    2. Content extraction: Get content until next decision/heading
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

    def _build_section_index(self) -> None:
        """Build index for quick section lookup by paragraph index."""
        for section in self.sections:
            for idx in range(section.start_index, section.end_index):
                self._section_by_index[idx] = section

    @staticmethod
    def _build_body_map(docx_path: Path) -> tuple[dict[int, int], list]:
        """Build para_idx→body_idx mapping and body_children list.

        python-docx의 doc.paragraphs는 w:p만 반환하므로, body의 모든
        자식(w:p + w:tbl + etc)을 순회하여 paragraph 인덱스↔body 인덱스 매핑 생성.
        이를 통해 paragraph 범위 사이에 끼어있는 w:tbl도 추출 가능.
        """
        try:
            with zipfile.ZipFile(docx_path, 'r') as zf:
                xml_content = zf.read('word/document.xml')
        except Exception:
            return {}, []

        root = ET.fromstring(xml_content)
        body = root.find(f'{{{_W_NS}}}body')
        if body is None:
            return {}, []

        body_children = list(body)
        p_tag = f'{{{_W_NS}}}p'

        para_to_body: dict[int, int] = {}
        para_idx = 0
        for body_idx, child in enumerate(body_children):
            if child.tag == p_tag:
                para_to_body[para_idx] = body_idx
                para_idx += 1

        return para_to_body, body_children

    @staticmethod
    def _table_to_text(tbl_element) -> str:
        """Convert w:tbl XML element to pipe-delimited text.

        Each row becomes: | cell1 | cell2 | cell3 |
        Extracts all w:t text from each cell.
        """
        rows = []
        tr_tag = f'{{{_W_NS}}}tr'
        tc_tag = f'{{{_W_NS}}}tc'
        t_tag = f'{{{_W_NS}}}t'

        for tr in tbl_element:
            if tr.tag != tr_tag:
                continue
            cells = []
            for tc in tr:
                if tc.tag != tc_tag:
                    continue
                # Collect all text in the cell
                cell_texts = []
                for t_elem in tc.iter(t_tag):
                    if t_elem.text:
                        cell_texts.append(t_elem.text)
                cells.append(' '.join(cell_texts).strip())
            if cells:
                rows.append('| ' + ' | '.join(cells) + ' |')

        return '\n'.join(rows)

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
        candidates = self._find_candidates(paragraphs)

        # Extract content for each candidate
        agreements = []
        conclusions = []
        working_assumptions = []

        # Track decision counts per agenda for ID generation
        counters: dict[tuple[DecisionType, str], int] = {}

        for i, candidate in enumerate(candidates):
            # Handle inline content vs header-only
            if candidate.inline_content:
                # Inline: content is on the same line
                # But may continue to following paragraphs
                next_boundary = self._find_content_boundary(
                    candidate.keyword_index,
                    paragraphs,
                    candidates[i + 1].keyword_index if i + 1 < len(candidates) else len(paragraphs)
                )
                following_content = self._extract_content(
                    paragraphs,
                    candidate.keyword_index + 1,
                    next_boundary
                )

                # Re-extract inline content with [EQUATION] markers (Spec §3.1)
                inline_content = candidate.inline_content
                if build_text_with_markers:
                    full_text = build_text_with_markers(
                        paragraphs[candidate.keyword_index]._element
                    ).strip()
                    for pattern in DECISION_PATTERNS_INLINE.values():
                        m = pattern.match(full_text)
                        if m:
                            inline_content = m.group(1).strip()
                            break

                # Combine inline content with following content
                if following_content.strip():
                    content = inline_content + '\n' + following_content
                else:
                    content = inline_content
            else:
                # Header-only: content in following paragraphs
                next_boundary = self._find_content_boundary(
                    candidate.keyword_index,
                    paragraphs,
                    candidates[i + 1].keyword_index if i + 1 < len(candidates) else len(paragraphs)
                )
                content = self._extract_content(
                    paragraphs,
                    candidate.keyword_index + 1,  # Skip keyword paragraph
                    next_boundary
                )

            if not content.strip():
                continue

            # Split Note: block from content (Spec §3.1: note 속성)
            content, note = self._split_note(content)

            if not content.strip():
                continue

            # Get agenda for this decision
            agenda = self._get_agenda_for_index(candidate.keyword_index)

            # Generate decision ID
            counter_key = (candidate.decision_type, agenda)
            counters[counter_key] = counters.get(counter_key, 0) + 1
            count = counters[counter_key]

            prefix = self._get_decision_prefix(candidate.decision_type)
            meeting_num = meeting_id.replace("RAN1#", "")
            decision_id = f"{prefix}-{meeting_num}-{agenda}-{count:03d}"

            # Determine hasConsensus for Conclusion type
            # Spec §4.3: 부정 합의 패턴 미포함 시 true (6개 패턴)
            has_consensus = None
            if candidate.decision_type == DecisionType.CONCLUSION:
                has_consensus = not _NEG_CONSENSUS_RE.search(content)

            # Build content_with_equations (Spec: contentWithEquations §4.5)
            content_with_equations = None
            if self._eq_map:
                content_with_equations = self._build_content_with_equations(
                    paragraphs, candidate, next_boundary
                )
                # Also split note from content_with_equations
                if content_with_equations:
                    content_with_equations, _ = self._split_note(content_with_equations)

            # Create decision
            decision = Decision(
                decision_id=decision_id,
                decision_type=candidate.decision_type,
                meeting_id=meeting_id,
                agenda_item=agenda,
                content=content,
                paragraph_index=candidate.keyword_index,
                sequence=count,
                content_with_equations=content_with_equations,
                note=note,
                referenced_tdocs=TDOC_PATTERN.findall(content),
                has_ffs=bool(FFS_PATTERN.search(content)),
                has_tbd=bool(TBD_PATTERN.search(content)),
                has_consensus=has_consensus,
            )

            # Add to appropriate list
            if candidate.decision_type == DecisionType.AGREEMENT:
                agreements.append(decision)
            elif candidate.decision_type == DecisionType.CONCLUSION:
                conclusions.append(decision)
            else:
                working_assumptions.append(decision)

        return agreements, conclusions, working_assumptions

    def _find_candidates(self, paragraphs: list) -> list[DecisionCandidate]:
        """Find all decision keyword candidates.

        Supports:
        1. Header-only: "Agreement:" (content in following paragraphs)
        2. Inline: "Agreement: The UE shall..." (content on same line)

        Filters out:
        - Annex sections (per Spec requirement)
        - TOC entries (toc style paragraphs)
        """
        candidates = []
        in_annex = False

        for idx, para in enumerate(paragraphs):
            text = para.text.strip()
            style = para.style.name.lower() if para.style else ""

            # Skip TOC entries (they may contain Annex references)
            if style.startswith('toc'):
                continue

            # Check for Annex start - skip all content after this
            # Only trigger on actual headings, not TOC references
            if ANNEX_PATTERN.match(text) and style.startswith('heading'):
                in_annex = True
                continue

            # Skip if we're in Annex section
            if in_annex:
                continue

            # Try header-only patterns first
            for decision_type, pattern in DECISION_PATTERNS_HEADER.items():
                if pattern.match(text):
                    candidates.append(DecisionCandidate(
                        decision_type=decision_type,
                        keyword_index=idx,
                        keyword_text=text,
                        inline_content=None
                    ))
                    break
            else:
                # Try inline patterns (Agreement: [content])
                for decision_type, pattern in DECISION_PATTERNS_INLINE.items():
                    match = pattern.match(text)
                    if match:
                        inline_content = match.group(1).strip()
                        candidates.append(DecisionCandidate(
                            decision_type=decision_type,
                            keyword_index=idx,
                            keyword_text=text,
                            inline_content=inline_content
                        ))
                        break

        return candidates

    def _find_content_boundary(
        self,
        start_index: int,
        paragraphs: list,
        max_index: int
    ) -> int:
        """
        Find where the decision content ends.

        Ends at:
        - Next decision keyword (header or inline)
        - Heading paragraph
        - Annex section
        - Double blank lines
        """
        blank_count = 0

        for idx in range(start_index + 1, max_index):
            para = paragraphs[idx]
            text = para.text.strip()
            style = para.style.name.lower() if para.style else ""

            # Check for heading
            if style.startswith('heading'):
                return idx

            # Check for Annex (stop at Annex)
            if ANNEX_PATTERN.match(text):
                return idx

            # Check for decision keyword (header-only)
            for pattern in DECISION_PATTERNS_HEADER.values():
                if pattern.match(text):
                    return idx

            # Check for decision keyword (inline)
            for pattern in DECISION_PATTERNS_INLINE.values():
                if pattern.match(text):
                    return idx

            # Check for consecutive blanks
            if not text:
                blank_count += 1
                if blank_count >= 2:
                    return idx - 1
            else:
                blank_count = 0

        return max_index

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

        if self._body_children and start_index in self._para_to_body:
            # Body-aware: paragraph 범위에 대응하는 body 구간 순회
            body_start = self._para_to_body[start_index]
            body_end = self._para_to_body.get(end_index, len(self._body_children))

            # para_idx 매핑을 역산: body_idx → para_idx
            body_to_para: dict[int, int] = {}
            for pi, bi in self._para_to_body.items():
                body_to_para[bi] = pi

            for body_idx in range(body_start, body_end):
                child = self._body_children[body_idx]
                if child.tag == p_tag:
                    para_idx = body_to_para.get(body_idx)
                    if para_idx is not None and para_idx < len(paragraphs):
                        if build_text_with_markers:
                            text = build_text_with_markers(
                                paragraphs[para_idx]._element
                            ).strip()
                        else:
                            text = paragraphs[para_idx].text.strip()
                        if text:
                            content_parts.append(text)
                elif child.tag == tbl_tag:
                    table_text = self._table_to_text(child)
                    if table_text:
                        content_parts.append(table_text)
        else:
            # Fallback: 기존 paragraph-only 로직 (DOCM 또는 body_map 미지원)
            for idx in range(start_index, end_index):
                if build_text_with_markers:
                    text = build_text_with_markers(paragraphs[idx]._element).strip()
                else:
                    text = paragraphs[idx].text.strip()
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
        Embedded tables are included as pipe-delimited text (no LaTeX).

        Returns None if:
        - No equations found in the decision's paragraph range
        - build_text_with_latex is not available
        """
        if not build_text_with_latex:
            return None

        kw_idx = candidate.keyword_index
        content_start = kw_idx + 1

        # Check if any paragraph in content range has equations
        check_start = kw_idx if candidate.inline_content else content_start
        if not any(idx in self._eq_map for idx in range(check_start, content_end)):
            return None

        parts: list[str] = []
        tbl_tag = f'{{{_W_NS}}}tbl'
        p_tag = f'{{{_W_NS}}}p'

        # Handle inline: extract LaTeX-enriched inline portion from keyword paragraph
        if candidate.inline_content:
            para_text = build_text_with_latex(
                paragraphs[kw_idx]._element,
                self._eq_map.get(kw_idx, {})
            ).strip()
            # Extract inline content (after "Agreement:" or similar keyword)
            inline_extracted = None
            for pattern in DECISION_PATTERNS_INLINE.values():
                m = pattern.match(para_text)
                if m:
                    inline_extracted = m.group(1).strip()
                    break
            parts.append(inline_extracted if inline_extracted else candidate.inline_content)

        # Following content (body-aware if available)
        if self._body_children and content_start in self._para_to_body:
            body_start = self._para_to_body[content_start]
            body_end = self._para_to_body.get(content_end, len(self._body_children))

            body_to_para: dict[int, int] = {}
            for pi, bi in self._para_to_body.items():
                body_to_para[bi] = pi

            for body_idx in range(body_start, body_end):
                child = self._body_children[body_idx]
                if child.tag == p_tag:
                    para_idx = body_to_para.get(body_idx)
                    if para_idx is not None and para_idx < len(paragraphs):
                        text = build_text_with_latex(
                            paragraphs[para_idx]._element,
                            self._eq_map.get(para_idx, {})
                        ).strip()
                        if text:
                            parts.append(text)
                elif child.tag == tbl_tag:
                    table_text = self._table_to_text(child)
                    if table_text:
                        parts.append(table_text)
        else:
            # Fallback: paragraph-only
            for idx in range(content_start, content_end):
                text = build_text_with_latex(
                    paragraphs[idx]._element,
                    self._eq_map.get(idx, {})
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
    doc = Document(docx_path)
    extractor = DecisionExtractor(sections, equation_converter, docx_path=docx_path)
    return extractor.extract_decisions(doc.paragraphs, meeting_id)


if __name__ == "__main__":
    import sys
    from toc_parser import parse_toc_from_docx
    from agenda_matcher import AgendaMatcher, SectionBuilder

    if len(sys.argv) < 2:
        print("Usage: python decision_extractor.py <docx_path>")
        sys.exit(1)

    docx_path = Path(sys.argv[1])
    meeting_id = "RAN1#" + docx_path.stem.split('-')[-1].replace('_hybrid', '')

    # Parse TOC and build sections
    toc_entries = parse_toc_from_docx(docx_path)
    matcher = AgendaMatcher(toc_entries)
    builder = SectionBuilder(matcher)

    # Build sections from document
    doc = Document(docx_path)
    sections = []
    for idx, para in enumerate(doc.paragraphs):
        style = para.style.name.lower() if para.style else ""
        if style.startswith('heading'):
            level = int(style.split()[-1]) if style.split()[-1].isdigit() else 1
            section = builder.process_heading(para.text.strip(), level, idx)
            if sections:
                sections[-1].end_index = idx
            sections.append(section)

    if sections:
        sections[-1].end_index = len(doc.paragraphs)

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
