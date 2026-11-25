#!/usr/bin/env python3
"""
Decision Extractor for RAN3 Final Reports

Spec: tdoc_ontology_specs(Final_report).md

RAN1 대비 차이:
- TDoc 패턴: R3-\\d{6} (not R1-)
- 본문은 content에 저장하고 수식 위치는 [EQUATION]으로 표시
- equation_converter 미사용
- "Agreement" paragraph style은 키워드가 아님 — 텍스트 패턴만 매칭
- Body-aware extraction (w:tbl support) 유지
- 결정 표지와 본문 끝은 RAN WG 다섯 곳이 함께 쓰는 `decision_marks` 가 읽는다
"""

import re
import sys
import zipfile
from pathlib import Path
from typing import Optional

from models import Decision, DecisionType, Section
from annex import is_annex_heading, outline_level

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "common"))
import docx_text  # noqa: E402
import decision_marks  # noqa: E402
import decision_boxes  # noqa: E402

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


# Spec §4.1: RAN3 TDoc 참조 패턴
# R3 접두사 뒤 공백이나 구분자가 생략된 번호도 정규화한다: decision_marks.tdoc_number 참고.
TDOC_WG, TDOC_DIGITS = "3", "6"

# FFS / TBD patterns
FFS_PATTERN = re.compile(r'\bFFS\b', re.IGNORECASE)
TBD_PATTERN = re.compile(r'\bTBD\b', re.IGNORECASE)

# Note pattern (Spec §3.1)
NOTE_PATTERN = re.compile(r'^Note\s*:', re.IGNORECASE)


class DecisionExtractor:
    """Extract decisions from RAN3 document paragraphs.

    Two-phase: decision mark detection (`decision_marks`) -> content extraction.
    Equation positions use [EQUATION] markers rather than converted equations.
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
        self._body_to_para = {body_idx: para_idx
                              for para_idx, body_idx in self._para_to_body.items()}
        # 파일명에서 접두사를 제외한 회의 표기(`RAN3-126`)를 decision_marks의 인용 출처 대조에 사용한다.
        self._meeting_stem = docx_path.stem.removeprefix("Final_Report_") if docx_path else None

    def _build_section_index(self) -> None:
        for section in self.sections:
            for idx in range(section.start_index, section.end_index):
                self._section_by_index[idx] = section

    @staticmethod
    def _build_body_map(docx_path: Path) -> tuple[dict[int, int], list]:
        """Build para_idx -> body_idx mapping for w:tbl support.

        본문 블록(w:p · w:tbl, 블록 w:sdt 안 포함)을 `docx_text.iter_blocks` 순서로 센다.
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
        `docx_text.table_line_rows`가 셀의 문단을 본문과 같은 `_marked` 함수로 읽는다.
        삭제된 변경 내용은 제외하고 수식·그림 위치에는 표시 문자열을 남긴다. 가로 병합 셀은
        한 번 읽고 세로 병합 셀은 병합 시작 셀의 텍스트를 사용한다. `w:t` 사이에 임의로
        공백을 넣으면 run 경계에서 단어와 TDoc 번호가 분리될 수 있어 이 방식을 사용한다.
        """
        return '\n'.join(docx_text.table_line_rows(tbl_element, para=self._marked))

    def _marked(self, para) -> str:
        """확정된 문단 텍스트와 글상자 텍스트를 읽고 수식·그림 위치를 표시한다.

        `docx_text.marked_text`로 OMML 수식과 MathType 그림·OLE 수식을 `[EQUATION]`으로,
        그 밖의 그림을 `[FIGURE]`로 표시한다.
        """
        return docx_text.marked_text(para, is_equation_image=self._eq_image)

    def extract_decisions(
        self, paragraphs: list, meeting_id: str
    ) -> tuple[list[Decision], list[Decision], list[Decision]]:
        """Extract all decisions from document paragraphs."""
        # _marked에서 수식 이미지와 일반 이미지를 구분할 때 사용할 관계 정보를 읽는다.
        self._eq_image = docx_text.equation_images(paragraphs[0].part) if paragraphs else None
        # (본문 블록 위치, 결정 종류, Mark, 표지 문단 텍스트, 본문, 의제 판정 문단 번호, 본문 블록 범위)
        candidates = [
            ((self._para_to_body.get(idx, idx), 0), decision_type, mark, self._marked(paragraphs[idx]),
             self._extract_content(paragraphs, idx + 1, boundary), idx, self._body_blocks(idx, boundary))
            for decision_type, idx, mark, boundary in self._find_candidates(paragraphs)
        ]
        candidates += self._box_candidates(paragraphs)
        # 현재 회의의 결정을 반복한다고 명시한 문단의 모든 줄이 앞선 표 셀 결정과 같으면 중복 추출하지 않는다.
        drop = decision_boxes.box_reprints(self._restated, self._boxes)
        candidates = [c for c in candidates if c[0][1] or c[5] not in drop]
        candidates.sort(key=lambda c: c[0])

        agreements = []
        conclusions = []
        working_assumptions = []
        counters: dict[tuple[DecisionType, str], int] = {}

        for _pos, decision_type, mark, line, following, keyword_idx, body_blocks in candidates:
            # 한정어를 포함한 표지(mark.lead)는 뒤따르는 본문이 있거나 해당 줄이 독립된 결정 문장일 때만 추출한다.
            if mark.lead is not None and not following.strip() and not decision_marks.lead_stands_alone(mark):
                continue
            # 표지 문단에 포함된 본문도 수식·그림 표시와 글상자 텍스트를 포함해 읽는다.
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

            # 표 셀 결정 앞에 본문 문단이 없으면 의제 번호는 UNKNOWN으로 기록한다.
            agenda = self._get_agenda_for_index(keyword_idx) if keyword_idx is not None else "UNKNOWN"

            # Generate ID — Spec §3.2: {TYPE}-{meeting}-{agenda}-{seq}
            counter_key = (decision_type, agenda)
            counters[counter_key] = counters.get(counter_key, 0) + 1
            count = counters[counter_key]

            prefix = self._get_decision_prefix(decision_type)
            meeting_num = meeting_id.replace("RAN3#", "")
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

        Returns list of (DecisionType, keyword_idx, Mark, content_end): 본문은 keyword_idx 다음 문단부터
        content_end 앞까지다.

        표지와 본문 끝은 `decision_marks.decision_spans` 가 읽는다.
        절의 시작은 Heading·miniheading 스타일, 제목으로 판정된 `Annex X` 문단,
        또는 `report_parser._build_sections`가 절의 시작으로 선택한 문단이다.
        제목이 아닌 본문 속 `Annex X` 언급은 결정 본문의 종료 조건으로 사용하지 않는다.
        목차 문단과 부록 시작 이후의 문단은 결정 표지 후보에서 제외한다.
        번호 목록 정보(`docx_text.list_keys`)도 전달해 표지 다음 줄이 앞선 목록 항목에
        속하는지 판정한다.

        Heading이 없는 보고서에서는 의제 번호로 시작하는 굵은 Normal 문단을 절의
        시작으로 사용할 수 있다. 스타일뿐 아니라 실제 선택된 절의 시작 인덱스도
        전달해 앞 절의 결정에 다음 절의 본문과 참조가 포함되지 않게 한다.
        Heading이 있는 보고서의 모든 굵은 번호 문단을 종료 조건으로 삼지는 않는다.
        """
        section_heads = {section.start_index for section in self.sections}
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
            hard.append(style.startswith('heading') or style == 'miniheading' or annex_head
                        or idx in section_heads)
            if annex_head and not in_annex:
                in_annex = True
                self._annex_from = idx
            if style.startswith('toc') or in_annex:
                skip.append(idx)
        self._companies = decision_marks.report_companies(texts, entry_sources=False)
        self._spans, self._restated = [], {}
        self._texts, self._hard = texts, hard
        return [
            (DECISION_TYPES[mark.kind], idx, mark, end)
            for idx, mark, end in decision_marks.decision_spans(
                texts, blank, hard, self._after_block(), companies=self._companies, skip=skip,
                meeting=self._meeting_stem, lists=docx_text.list_keys(paragraphs), spans=self._spans,
                restated=self._restated)
        ]

    def _box_candidates(self, paragraphs: list) -> list[tuple]:
        """기존 결정 본문에 포함되지 않은 표 셀의 결정을 공통 후보 형식으로 반환한다.

        `decision_boxes.box_marks`가 표 셀의 표지를 판정한다. 의제는 표 앞 마지막 본문
        문단을 기준으로 정하고 본문 블록 범위는 해당 표 하나로 기록한다. 부록 이후의
        표는 제외한다. 앞선 TDoc 항목의 Abstract 셀이나 출처 회의 설명도 문맥으로 전달한다.
        """
        self._boxes = decision_boxes.box_marks(
            paragraphs, self._body_children, self._para_to_body, self._spans,
            companies=self._companies, meeting=self._meeting_stem, stop=self._annex_from,
            texts=self._texts, hard=self._hard)
        return [
            ((box.body_index, n), DECISION_TYPES[box.mark.kind], box.mark, self._marked(box.line),
             box.following(self._marked, self._table_to_text), box.prev_para,
             [box.body_index, box.body_index + 1])
            for n, box in enumerate(self._boxes, 1)
        ]

    def _after_block(self) -> set[int]:
        """표(w:tbl) 바로 다음 문단의 번호를 모아 결정 본문 경계 판정에 전달한다."""
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
        """결정이 차지한 본문 블록 범위 [시작, 끝): 표지 줄 블록부터 본문 끝 문단(end_index) 블록 앞까지.

        번호는 표·그림의 `paragraph_index`와 같은 `docx_text.iter_blocks` 기준이다.
        문단 사이의 표(w:tbl)도 `_extract_content`에서 본문으로 읽는다. JSON-LD의
        hasTable·hasFigure는 이 범위 안의 표·그림을 결정에 연결한다.
        본문 블록 인덱스를 만들지 못한 문서는 None을 반환한다.
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

        # 표지 문단의 본문 블록 바로 다음부터 읽어 다음 문단 앞에 있는 표도 본문에 포함한다.
        if self._body_children and start_index - 1 in self._para_to_body:
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
            for idx in range(start_index, end_index):
                text = self._marked(paragraphs[idx])
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
