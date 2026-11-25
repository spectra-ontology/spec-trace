#!/usr/bin/env python3
"""
Decision Extractor for RAN5 Final Reports

Spec: docs/tsg/RAN/formal/RAN5/phase-2/design-spec/tdoc_ontology_specs(Final_report).md

RAN4 대비 차이:
- Conclusion만 저장한다. Agreement와 Working assumption 표지는 Conclusion 본문의 종료 경계를 판정하는 데 사용한다.
- hasFFS/hasTBD/hasConsensus 모두 Conclusion에 통합 (Spec §3.2)
- TDoc 패턴: R5-\\d{6} (6자리, RAN3과 동일)
- Discussion 텍스트 추출 (RAN5 고유, Spec §4.3)
- meeting_id 접두사: RAN5#
- 결정 표지와 본문 끝은 RAN WG 다섯 곳이 함께 쓰는 `decision_marks` 가 읽는다
"""

import re
import sys
import zipfile
from pathlib import Path
from typing import Optional

from models import Decision, DecisionType, DiscussionInfo, Section
from annex import is_annex_heading, outline_level, paragraph_annex_start

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "common"))
import docx_text  # noqa: E402
import decision_marks  # noqa: E402
import decision_boxes  # noqa: E402

# Namespace for Word XML
_W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

# Spec §4.2: 부정 합의 패턴 — 하나라도 매칭 시 hasConsensus = false
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


# Spec §4.1: RAN5 TDoc 참조 패턴 (6자리)
# 번호 내부의 공백과 하이픈 생략을 허용하고 RAN5의 6자리 TDoc 번호로 정규화한다.
TDOC_WG, TDOC_DIGITS = "5", "6"

# FFS / TBD patterns — Spec §3.2: Conclusion에 통합
FFS_PATTERN = re.compile(r'\bFFS\b', re.IGNORECASE)
TBD_PATTERN = re.compile(r'\bTBD\b', re.IGNORECASE)

# Note pattern (Spec §3.1)
NOTE_PATTERN = re.compile(r'^Note\s*:', re.IGNORECASE)

# Discussion: TDoc reference line pattern (RAN5 고유)
# 문단 시작에서 RAN5 TDoc 번호를 찾아 해당 문서의 논의 구간을 시작한다.
TDOC_LINE_PATTERN = re.compile(rf'^({decision_marks.tdoc_number(TDOC_WG, TDOC_DIGITS)})\b')

# Minimum discussion text length (Spec §4.3)
MIN_DISCUSSION_LENGTH = 50


class DecisionExtractor:
    """Extract Conclusions and Discussion texts from RAN5 document paragraphs.

    RAN4 대비: Agreement/WA 추출 제거, Discussion 추출 추가.
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
        self._body_to_para = {bi: pi for pi, bi in self._para_to_body.items()}
        # 파일명에서 추출한 회의 식별자로 현재 회의의 결정과 인용된 과거 결정을 구분한다.
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
        칸 글은 `docx_text.table_line_rows` 가 읽는다: 칸 안 문단을 본문과 같은 `_marked` 로 읽은 글
        (변경 표시로 빠진 글 제외 · 수식 · 그림 자리는 표지), 가로 합친 칸은 한 번, 세로 합친 칸은
        합침을 시작한 칸의 글. `w:t` 를 빈칸으로 이으면 run 경계에서 낱말과 tdoc 번호(`R1-` `2001234`)가 갈라진다.
        """
        return '\n'.join(docx_text.table_line_rows(tbl_element, para=self._marked))

    def _marked(self, para) -> str:
        """본문 문단 글: 확정 글에 수식(OMML)은 `[EQUATION]`, 그림은 `[FIGURE]`(MathType 그림 · OLE 수식은
        `[EQUATION]`)로 남기고 글상자 안 글을 넣는다(`docx_text.marked_text`)."""
        return docx_text.marked_text(para, is_equation_image=self._eq_image)

    def extract_decisions(
        self, paragraphs: list, meeting_id: str
    ) -> list[Decision]:
        """Extract Conclusions from document paragraphs.

        RAN5: Conclusion만 추출 (Agreement/WA 제외)
        """
        # 본문 판독기(_marked)가 그림 · OLE 개체를 수식 그림과 그 밖의 그림으로 가르는 데 쓴다
        self._eq_image = docx_text.equation_images(paragraphs[0].part) if paragraphs else None
        # (문서 자리, Mark, 표지 줄 글, 본문, 의제를 정할 문단 번호, 본문 블록 범위, Tdoc 머리 줄을 찾기 시작할 문단 번호)
        candidates = [
            ((self._para_to_body.get(idx, idx), 0), mark, self._marked(paragraphs[idx]),
             self._extract_content(paragraphs, idx + 1, boundary), idx, self._body_blocks(idx, boundary), idx)
            for idx, mark, boundary in self._find_candidates(paragraphs)
        ]
        candidates += self._box_candidates(paragraphs)
        # 이번 회의 결정을 다시 적는다고 밝힌 문단 표지의 글 줄이 모두 앞 표 상자 결정에 있으면 내지 않는다
        drop = decision_boxes.box_reprints(self._restated, self._boxes)
        candidates = [c for c in candidates if c[0][1] or c[4] not in drop]
        candidates.sort(key=lambda c: c[0])

        conclusions = []
        counters: dict[str, int] = {}

        for _pos, mark, line, following, keyword_idx, body_blocks, subject_at in candidates:
            # 한정어 꼴 표지 줄(mark.lead)은 뒤 본문이 있거나 그 줄 혼자 결정 문장일 때만 결정이다
            if mark.lead is not None and not following.strip() and not decision_marks.lead_stands_alone(mark):
                continue
            # 표지 줄에 든 본문도 본문과 같은 판독기로 다시 읽는다: 수식 · 그림 표지와 글상자 글이 든다
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

            # Get agenda: 본문 앞에 놓인 표 상자는 앞 문단이 없어 UNKNOWN 이다
            agenda = self._get_agenda_for_index(keyword_idx) if keyword_idx is not None else "UNKNOWN"

            # Generate ID — Spec §3.2: CON-{meeting}-{agenda}-{seq}
            counters[agenda] = counters.get(agenda, 0) + 1
            count = counters[agenda]

            meeting_num = meeting_id.replace("RAN5#", "")
            decision_id = f"CON-{meeting_num}-{agenda}-{count:03d}"

            # Spec §4.2: hasConsensus, hasFFS, hasTBD 모두 Conclusion에 통합
            has_consensus = not _NEG_CONSENSUS_RE.search(content)

            decision = Decision(
                decision_id=decision_id,
                decision_type=DecisionType.CONCLUSION,
                meeting_id=meeting_id,
                agenda_item=agenda,
                content=content,
                paragraph_index=keyword_idx if keyword_idx is not None else 0,
                body_blocks=body_blocks,
                sequence=count,
                note=note,
                referenced_tdocs=list(dict.fromkeys(decision_marks.tdoc_ids(content, TDOC_WG, TDOC_DIGITS))),  # 같은 번호가 표 행마다 되풀이돼도 참조는 하나
                subject_tdoc=self._subject_tdoc(paragraphs, subject_at),
                has_ffs=bool(FFS_PATTERN.search(content)),
                has_tbd=bool(TBD_PATTERN.search(content)),
                has_consensus=has_consensus,
            )
            conclusions.append(decision)

        return conclusions

    def extract_discussions(
        self, paragraphs: list, meeting_id: str
    ) -> list[DiscussionInfo]:
        """Extract Discussion texts from document paragraphs (RAN5 고유).

        Spec §4.3: TDoc 논의 텍스트 블록, 50자 초과만 저장. 제목 꼴 `Annex X` 문단부터 끝까지의 부록은 읽지 않는다.
        """
        discussions = []
        paragraphs = paragraphs[:paragraph_annex_start(paragraphs)]
        # 논의 본문도 결정 본문과 같은 판독기(_marked)로 읽는다. 끝 판정(Tdoc 줄 · 표지 · 틀 머리)은 확정 글로 한다
        self._eq_image = docx_text.equation_images(paragraphs[0].part) if paragraphs else None

        for idx, para in enumerate(paragraphs):
            text = docx_text.final_text(para)
            style = para.style.name.lower() if para.style else ""

            # Skip headings and TOC
            if style.startswith('heading') or style.startswith('toc'):
                continue

            # Find TDoc reference lines
            tdoc_match = TDOC_LINE_PATTERN.search(text)
            if not tdoc_match:
                continue

            tdoc_number = decision_marks.canonical_tdoc(tdoc_match.group(1))

            # Collect discussion text: paragraphs after TDoc ref until next boundary
            # Skip metadata lines (Type:, Source:, For:) — not discussion content
            discussion_parts = []
            for j in range(idx + 1, len(paragraphs)):
                p_text = docx_text.final_text(paragraphs[j])
                p_style = paragraphs[j].style.name.lower() if paragraphs[j].style else ""

                # Stop at headings
                if p_style.startswith('heading'):
                    break

                # Stop at next TDoc reference line
                if TDOC_LINE_PATTERN.match(p_text) and j != idx:
                    break

                # Stop at a decision mark (Conclusion · Agreement · Working assumption)
                if decision_marks.classify(p_text.strip()) is not None:
                    break

                # 회의록 틀의 칸 머리(decision_marks.template_head: 철자 틀린 꼴 · 전각 쌍점 포함).
                # Decision 칸은 그 TDoc 의 처리 결과라 논의가 끝난 자리다. 처분이 머리 줄에 함께 적혔든
                # 다음 문단에 적혔든 여기서 모으기를 끝낸다(README 「논의 글」의 결정 표시).
                # Discussion · Abstract 칸은 머리 낱말만 떼고
                # 같은 줄 글을 남긴다(머리 낱말만 남기면 본문 없는 항목이 50자 문턱을 넘는다).
                head = decision_marks.template_head(p_text.strip())
                if head is not None:
                    if head[0] == "decision":
                        break
                    # 머리 낱말 뒤 글은 본문 판독기로 다시 읽은 줄에서 뗀다: 그 줄도 같은 머리로 읽힐 때
                    line = self._marked(paragraphs[j]).strip()
                    again = decision_marks.template_head(line)
                    if again is None or again[0] != head[0]:
                        line, again = p_text.strip(), head
                    inline = line[again[1]:].strip()
                    if inline:
                        discussion_parts.append(inline)
                    continue

                # Skip TDoc metadata lines
                if re.match(r'^(Type|Source|For)\s*:', p_text, re.IGNORECASE):
                    continue

                marked = self._marked(paragraphs[j])
                if marked:
                    discussion_parts.append(marked)

            discussion_text = '\n'.join(discussion_parts).strip()

            # Spec §4.3: 50자 초과만 저장
            if len(discussion_text) > MIN_DISCUSSION_LENGTH:
                discussions.append(DiscussionInfo(
                    tdoc_number=tdoc_number,
                    meeting_id=meeting_id,
                    text=discussion_text,
                    paragraph_index=idx,
                ))

        # Deduplicate: 같은 TDoc이 여러 번 → 가장 긴 텍스트 보존 (Spec §4.3)
        best_by_tdoc: dict[str, DiscussionInfo] = {}
        for d in discussions:
            if d.tdoc_number not in best_by_tdoc or len(d.text) > len(best_by_tdoc[d.tdoc_number].text):
                best_by_tdoc[d.tdoc_number] = d

        return list(best_by_tdoc.values())

    @staticmethod
    def _subject_tdoc(paragraphs: list, keyword_idx: int) -> Optional[str]:
        """Conclusion이 속한 TDoc 번호를 앞쪽의 가장 가까운 TDoc 시작 문단에서 찾는다.

        결론 본문에 문서 번호가 없어도 해당 TDoc에 ABOUT_TDOC 관계를 연결할 수 있도록 한다.
        표지 줄 앞에서부터 역순으로 검사하며, TDoc 번호보다 절 제목이나 이전 항목의
        `Decision` 필드를 먼저 만나면 현재 문서 항목의 범위를 벗어난 것으로 보고 None을 반환한다.
        """
        for i in range(keyword_idx - 1, -1, -1):
            para = paragraphs[i]
            style = para.style.name.lower() if para.style else ""
            if style.startswith('heading') or style.startswith('toc'):
                return None
            text = docx_text.final_text(para).strip()
            head = decision_marks.template_head(text)
            if head is not None and head[0] == "decision":
                return None
            m = TDOC_LINE_PATTERN.match(text)
            if m:
                return decision_marks.canonical_tdoc(m.group(1))
        return None

    def _find_candidates(self, paragraphs: list) -> list[tuple]:
        """Find all Conclusion marks and where their content ends.

        Returns list of (keyword_idx, Mark, content_end): 본문은 keyword_idx 다음 문단부터 content_end 앞까지다.

        표지와 본문 끝은 `decision_marks.decision_spans` 가 결정 세 종류 표지를 모두 읽어 낸다: Agreement ·
        Working assumption 표지도 앞 Conclusion 본문을 끝낸다. 그중 Conclusion 표지만 돌려준다.
        절 머리는 제목 꼴 문단 · 제목 꼴 `Annex X` 문단이다. 제목 꼴이 아닌 `Annex X` 줄은 절 머리가 아니다.
        목차 문단과 제목 꼴 `Annex X` 문단부터 끝까지의 부록 문단은 표지로 읽지 않는다.
        문단마다 든 번호 매김 목록 자리(`docx_text.list_keys`)도 넘겨, 표지 뒤에 붙은 이름표 줄이 앞 줄의 목록 항목인지 가르게 한다.
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
            if annex_head and not in_annex:
                in_annex = True
                self._annex_from = idx
            if style.startswith('toc') or in_annex:
                skip.append(idx)
        self._companies = decision_marks.report_companies(texts, entry_sources=False)
        self._spans, self._restated = [], {}
        self._texts, self._hard = texts, hard
        return [
            (idx, mark, end)
            for idx, mark, end in decision_marks.decision_spans(
                texts, blank, hard, self._after_block(), companies=self._companies, skip=skip,
                meeting=self._meeting_stem, lists=docx_text.list_keys(paragraphs), spans=self._spans,
                restated=self._restated)
            if mark.kind == "conclusion"
        ]

    def _box_candidates(self, paragraphs: list) -> list[tuple]:
        """어느 결정 본문에도 들지 않은 표의 칸 안 결론(`decision_boxes.box_marks`): `extract_decisions` 의 후보 꼴로.

        의제를 정할 문단은 표 앞 마지막 본문 문단이고, 본문 블록 범위는 그 표 하나다. Tdoc 머리 줄은 표 앞 문단부터
        앞쪽으로 찾는다. 부록 머리 뒤의 표는 문단 표지처럼 읽지 않는다.
        표 앞 본문 문맥(Tdoc 항목의 Abstract 칸 · 출처 회의를 밝힌 앞 글 줄)은 문단 흐름과 같게 본다.
        """
        out, self._boxes = [], []
        for n, box in enumerate(decision_boxes.box_marks(
                paragraphs, self._body_children, self._para_to_body, self._spans,
                companies=self._companies, meeting=self._meeting_stem, stop=self._annex_from,
                texts=self._texts, hard=self._hard), 1):
            if box.mark.kind != "conclusion":
                continue
            self._boxes.append(box)
            out.append(((box.body_index, n), box.mark, self._marked(box.line),
                        box.following(self._marked, self._table_to_text), box.prev_para,
                        [box.body_index, box.body_index + 1],
                        box.prev_para + 1 if box.prev_para is not None else 0))
        return out

    def _after_block(self) -> set[int]:
        """바로 앞에 표(w:tbl)가 놓인 문단 번호: 결정 본문 끝을 읽을 때 표를 본문 덩어리로 넘긴다."""
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

        # 표지 줄의 body 자리 바로 다음부터 읽는다: 표지 줄과 다음 문단 사이에 놓인 표도 본문이다
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
