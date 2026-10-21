#!/usr/bin/env python3
"""
Decision Extractor for RAN2 Final Reports

Spec: tdoc_ontology_specs(Final_report).md

RAN1 대비 차이:
- TDoc 패턴: R2-\\d{7} (not R1-)
- contentWithEquations 제거 (수식 0건)
- equation_converter 미사용
- "Agreement" paragraph style은 키워드가 아님 — 텍스트 패턴만 매칭
- Body-aware extraction (w:tbl support) 유지
"""

import re
import zipfile
from pathlib import Path
from typing import Optional

from models import Decision, DecisionType, Section

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

# Decision keyword patterns — 텍스트 기준 매칭 (paragraph style "Agreement"와 혼동 금지)
# Pattern 1: Header only (e.g., "Agreement:")
# 결정 표지는 회의록마다 방언이 갈린다 — 맨 `Agreement:` 와 대괄호를 두른 `[Agreement]`.
# 소비자가 한 방언만 읽으면 다른 방언으로 적힌 결정은 오류가 아니라 부재로 나타나므로
# 두 방언을 함께 읽는다. 소괄호 `(Working assumption)` 은 일부러 받지 않는다 — 실측상
# 그것은 표지가 아니라 절차 목록 안의 한정 어구여서, 받으면 문장 조각이 결정이 된다.
DECISION_PATTERNS_HEADER = {
    DecisionType.AGREEMENT: re.compile(
        r'^(?:\[\s*agreements?\s*\]|agreements?)\s*:?\s*$', re.IGNORECASE
    ),
    DecisionType.CONCLUSION: re.compile(
        r'^(?:\[\s*conclusions?\s*\]|conclusions?)\s*:?\s*$', re.IGNORECASE
    ),
    DecisionType.WORKING_ASSUMPTION: re.compile(
        r'^(?:\[\s*working\s*assumptions?\s*\]|working\s*assumptions?)\s*:?\s*$', re.IGNORECASE
    ),
}

# Inline patterns — "Agreement: [content]"
DECISION_PATTERNS_INLINE = {
    DecisionType.AGREEMENT: re.compile(
        r'^(?:\[\s*agreements?\s*\]\s*:?|agreements?\s*:)\s*(.+)', re.IGNORECASE | re.DOTALL
    ),
    DecisionType.CONCLUSION: re.compile(
        r'^(?:\[\s*conclusions?\s*\]\s*:?|conclusions?\s*:)\s*(.+)', re.IGNORECASE | re.DOTALL
    ),
    DecisionType.WORKING_ASSUMPTION: re.compile(
        r'^(?:\[\s*working\s*assumptions?\s*\]\s*:?|working\s*assumptions?\s*:)\s*(.+)', re.IGNORECASE | re.DOTALL
    ),
}

# Annex section pattern
ANNEX_PATTERN = re.compile(r'^Annex\s+[A-Z]', re.IGNORECASE)

# Spec §4.1: RAN2 TDoc 참조 패턴
TDOC_PATTERN = re.compile(r'R2-\d{7}')

# FFS / TBD patterns
FFS_PATTERN = re.compile(r'\bFFS\b', re.IGNORECASE)
TBD_PATTERN = re.compile(r'\bTBD\b', re.IGNORECASE)

# Note pattern (Spec §3.1)
NOTE_PATTERN = re.compile(r'^Note\s*:', re.IGNORECASE)


class DecisionExtractor:
    """Extract decisions from RAN2 document paragraphs.

    Two-phase: regex detection -> content extraction.
    No equation conversion (수식 0건).
    """

    def __init__(self, sections: list[Section], docx_path: Optional[Path] = None):
        self.sections = sections
        self._section_by_index: dict[int, Section] = {}
        self._build_section_index()

        # Body-aware extraction for w:tbl support
        if docx_path:
            self._para_to_body, self._body_children = self._build_body_map(docx_path)
        else:
            self._para_to_body, self._body_children = {}, []

    def _build_section_index(self) -> None:
        for section in self.sections:
            for idx in range(section.start_index, section.end_index):
                self._section_by_index[idx] = section

    @staticmethod
    def _build_body_map(docx_path: Path) -> tuple[dict[int, int], list]:
        """Build para_idx -> body_idx mapping for w:tbl support."""
        try:
            with zipfile.ZipFile(docx_path, 'r') as zf:
                xml_content = zf.read('word/document.xml')
        except Exception:
            return {}, []

        from xml.etree import ElementTree as ET
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
        """Convert w:tbl XML element to pipe-delimited text."""
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
                cell_texts = []
                for t_elem in tc.iter(t_tag):
                    if t_elem.text:
                        cell_texts.append(t_elem.text)
                cells.append(' '.join(cell_texts).strip())
            if cells:
                rows.append('| ' + ' | '.join(cells) + ' |')

        return '\n'.join(rows)

    def extract_decisions(
        self, paragraphs: list, meeting_id: str
    ) -> tuple[list[Decision], list[Decision], list[Decision]]:
        """Extract all decisions from document paragraphs."""
        candidates = self._find_candidates(paragraphs)

        agreements = []
        conclusions = []
        working_assumptions = []
        counters: dict[tuple[DecisionType, str], int] = {}

        for i, candidate in enumerate(candidates):
            next_boundary_max = (
                candidates[i + 1][1] if i + 1 < len(candidates) else len(paragraphs)
            )
            decision_type, keyword_idx, keyword_text, inline_content = candidate

            # Find content boundary
            boundary = self._find_content_boundary(
                keyword_idx, paragraphs, next_boundary_max
            )

            # Extract content
            if inline_content:
                following = self._extract_content(paragraphs, keyword_idx + 1, boundary)
                content = inline_content + ('\n' + following if following.strip() else '')
            else:
                content = self._extract_content(paragraphs, keyword_idx + 1, boundary)

            if not content.strip():
                continue

            # Split Note: block (Spec §3.1)
            content, note = self._split_note(content)
            if not content.strip():
                continue

            # Get agenda
            agenda = self._get_agenda_for_index(keyword_idx)

            # Generate ID — Spec §3.2: {TYPE}-{meeting}-{agenda}-{seq}
            counter_key = (decision_type, agenda)
            counters[counter_key] = counters.get(counter_key, 0) + 1
            count = counters[counter_key]

            prefix = self._get_decision_prefix(decision_type)
            meeting_num = meeting_id.replace("RAN2#", "")
            decision_id = f"{prefix}-{meeting_num}-{agenda}-{count:03d}"

            # hasConsensus for Conclusion (Spec §4.3)
            has_consensus = None
            if decision_type == DecisionType.CONCLUSION:
                has_consensus = not _NEG_CONSENSUS_RE.search(content)

            decision = Decision(
                decision_id=decision_id,
                decision_type=decision_type,
                meeting_id=meeting_id,
                agenda_item=agenda,
                content=content,
                paragraph_index=keyword_idx,
                sequence=count,
                note=note,
                referenced_tdocs=TDOC_PATTERN.findall(content),
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
        """Find all decision keyword candidates.

        Returns list of (DecisionType, keyword_idx, keyword_text, inline_content_or_None).

        IMPORTANT: paragraph style "Agreement" (33,136건) 은 키워드가 아님.
        텍스트 패턴만 매칭한다.
        """
        candidates = []

        for idx, para in enumerate(paragraphs):
            text = para.text.strip()
            style = para.style.name.lower() if para.style else ""

            # Skip TOC entries
            if style.startswith('toc'):
                continue

            # Annex heading 자체는 스킵 (Resolution 키워드가 아니므로)
            # RAN2: Annex 이후에도 Email discussion Resolution 존재 → 이후 문단은 계속 처리
            if ANNEX_PATTERN.match(text) and (
                style.startswith('heading') or style in ('miniheading', 'subheading')
            ):
                continue

            # Try header-only patterns first
            found = False
            for decision_type, pattern in DECISION_PATTERNS_HEADER.items():
                if pattern.match(text):
                    candidates.append((decision_type, idx, text, None))
                    found = True
                    break

            # Try inline patterns
            if not found:
                for decision_type, pattern in DECISION_PATTERNS_INLINE.items():
                    match = pattern.match(text)
                    if match:
                        inline_content = match.group(1).strip()
                        candidates.append((decision_type, idx, text, inline_content))
                        break

        return candidates

    def _find_content_boundary(
        self, start_index: int, paragraphs: list, max_index: int
    ) -> int:
        """Find where decision content ends."""
        blank_count = 0

        for idx in range(start_index + 1, max_index):
            para = paragraphs[idx]
            text = para.text.strip()
            style = para.style.name.lower() if para.style else ""

            # Heading stops content (including RAN2 extra headings)
            if style.startswith('heading') or style == 'miniheading':
                return idx

            if ANNEX_PATTERN.match(text):
                return idx

            for pattern in DECISION_PATTERNS_HEADER.values():
                if pattern.match(text):
                    return idx

            for pattern in DECISION_PATTERNS_INLINE.values():
                if pattern.match(text):
                    return idx

            if not text:
                blank_count += 1
                if blank_count >= 2:
                    return idx - 1
            else:
                blank_count = 0

        return max_index

    def _extract_content(
        self, paragraphs: list, start_index: int, end_index: int
    ) -> str:
        """Extract and join content paragraphs + embedded tables (body-aware)."""
        content_parts = []
        tbl_tag = f'{{{_W_NS}}}tbl'
        p_tag = f'{{{_W_NS}}}p'

        if self._body_children and start_index in self._para_to_body:
            body_start = self._para_to_body[start_index]
            body_end = self._para_to_body.get(end_index, len(self._body_children))

            body_to_para: dict[int, int] = {}
            for pi, bi in self._para_to_body.items():
                body_to_para[bi] = pi

            for body_idx in range(body_start, body_end):
                child = self._body_children[body_idx]
                if child.tag == p_tag:
                    para_idx = body_to_para.get(body_idx)
                    if para_idx is not None and para_idx < len(paragraphs):
                        text = paragraphs[para_idx].text.strip()
                        if text:
                            content_parts.append(text)
                elif child.tag == tbl_tag:
                    table_text = self._table_to_text(child)
                    if table_text:
                        content_parts.append(table_text)
        else:
            for idx in range(start_index, end_index):
                text = paragraphs[idx].text.strip()
                if text:
                    content_parts.append(text)

        return '\n'.join(content_parts)

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
