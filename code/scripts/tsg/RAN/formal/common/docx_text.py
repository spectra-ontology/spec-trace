#!/usr/bin/env python3
"""docx_text.py — Word 문단·표·수식을 용도에 맞는 텍스트로 읽는다.

Spec: docs/tsg/build/standards/reembedding_policy.md.
Ontology: 원문 인용과 검색 본문의 출처·표현을 구별한다.
Cycle: 공통 Word 판독 및 검색 표현 보존.
배경: 확정 글·변경 표시·수식·검색용 첨자 표기를 각 호출 계약에 맞게 읽는다.
사용: final_text / chunk_text / search_text 및 문서 블록 판독 API.
LLM 호출: 없음.

다섯 WG의 TS·CR·TR·TDoc 파서가 사용하는 공통 판독 규칙이다. 호출자는 용도에
맞는 함수를 선택한다.

- `final_text`: 변경을 반영한 문단 텍스트. 수식을 제외하며 제목·캡션 판정에 사용한다.
- `chunk_text`: 같은 문단에 수식의 선형 표기를 포함한다. CR은 `deleted=MARK`로
  삭제된 부분을 `[DEL]…[/DEL]`과 함께 읽을 수 있다.
- `search_text`: 기본 청크의 문자·공백을 보존하면서 명시적 위·아래첨자를 표시한다.
- `marked_text`: 그림·수식 위치에 표지를 남긴다. 호출자가 수식 변환 함수를 줄 수 있다.
- `boxed_text`, `iter_blocks`, `table_rows`: 글상자, 블록 래퍼 안의 문단·표,
  중첩 표와 병합 셀까지 해당 함수의 계약에 따라 읽는다.

문단 판독은 삽입·삭제 표시(`w:ins`·`w:del`), 하이퍼링크·콘텐츠 컨트롤 등의
래퍼와 탭·줄바꿈을 처리한다. 직접 자식 `w:r/w:t`만 읽으면 이 안의 글이 누락되고
제목 번호와 본문이 붙을 수 있다. DrawingML/VML 대체 표현은 같은 내용을 중복해
읽지 않도록 선택하며, 일반 그림과 글상자는 호출자가 지정한 판독 방식으로 처리한다.

`symbol_fonts`는 Symbol·Wingdings 등 기호 글꼴의 문자를 표시되는 유니코드 문자로
변환한다. Pandoc에 전달할 수식은 `drawn_math` 복사본에서 같은 기호 변환과 변경 표시
정리를 적용한다. 원본 수식 요소는 유지한다.

`open_document`와 `zip_part`는 `docx_reader`의 Strict 이름공간 호환 처리를 사용한다.
`doc_fields`는 필드 결과·명령문·숨김 텍스트를 처리하고, `ole_equation`은 판독 가능한
Equation Editor·MathType OLE 개체와 수식 미리보기의 텍스트를 `EQUATION_TEXT`로
기록한다. `chunk_text`는 이 주석이 있는 트리에서 해당 수식을 본문에 포함한다.
이 선형 텍스트 판독은 완전한 LaTeX 변환이나 일반 이미지 OCR과 구분한다.
"""
from __future__ import annotations

import copy
import re
import sys
import unicodedata
from pathlib import Path
from typing import Callable, NamedTuple

_ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(_ROOT / "scripts" / "common" / "common"))
import docx_reader  # noqa: E402 — Transitional·Strict 문서의 공통 열기 함수
import doc_fields  # noqa: E402 — 필드 결과 · 숨김 글 손질
import symbol_fonts  # noqa: E402 — 기호 글꼴 글자 읽기
import metafile_text  # noqa: E402 — 합친 EMF 가리기(`equation_image_data`)


def zip_part(z, name: str) -> bytes:
    """이미 연 패키지에서 부품 XML 하나를 Transitional 이름으로 읽는다. 글 부품(본문 · 각주 · 미주)은
    `doc_fields` 가 손질한 바이트다.

    주의: 수식 개체 · 수식 그림 판독(`_equation_part`)은 부품에 OLE 개체가 있을 때만이 아니라 그림 단위
    (`w:drawing` · `w:pict`)가 있을 때도 건다. MathType 수식 그림은 OLE 개체 없이 그림으로만 오기도 해서, 본문에
    OLE 개체가 하나도 없고 MathType 서명 그림만 든 문서가 코퍼스 CR 산출에 RAN1 177 · RAN2 27 · RAN4 1,255 ·
    RAN5 1,433개, `ontology/input` 회의 보고서 · TR 에 12개(RAN2 3 · RAN3 1 · RAN4 8) · 4개(RAN1 1 · RAN4 3) 있다. 개체가 있을
    때만 판독하면 이 문서들의 수식 그림은 글 없이 빠진다(`open_document` 는 늘 판독하므로 두 입구가 갈렸다)."""
    data = docx_reader.read_zip_part(z, name)
    if name in doc_fields.TEXT_PARTS:
        data = doc_fields.settle_part(data, name, getattr(z, "filename", None), z, repair=repair_tag_balance)
        if b"OLEObject" in data or b":drawing" in data or b":pict" in data:
            data = _equation_part(z, name, data)
        aliases = _font_aliases(z)
        if aliases:
            data = _alias_part(data, aliases)
        if symbol_fonts.has_private_use(data):
            data = _lost_font_part(z, name, data)
    return data


def _lxml_part(data: bytes):
    """부품 바이트를 lxml 로 읽는다. 엄격한 해석기가 거절하면 태그 짝만 고쳐 다시 읽고, 그래도 안 되면 None."""
    from lxml import etree

    parser = etree.XMLParser(huge_tree=True, resolve_entities=False)
    try:
        return etree.fromstring(data, parser)
    except etree.XMLSyntaxError:
        fixed, n = repair_tag_balance(data)
        try:
            return etree.fromstring(fixed, parser) if n else None
        except etree.XMLSyntaxError:
            return None


def _font_aliases(z) -> dict:
    """패키지 글꼴 표의 대체 기호 글꼴(`symbol_fonts.font_aliases`). 글꼴 표가 없거나 파싱되지 않으면 빈 사전."""
    try:
        data = docx_reader.read_zip_part(z, "word/fontTable.xml")
    except KeyError:
        return {}
    if b"altName" not in data:
        return {}
    return symbol_fonts.font_aliases(_lxml_part(data))


def _alias_part(data: bytes, aliases: dict) -> bytes:
    """글 부품에서 대응표 없는 글꼴 이름을 글꼴 표의 대체 기호 글꼴 이름으로 바꿔 적는다
    (`symbol_fonts.settle_font_aliases`). 바꾼 자리가 없거나 부품이 파싱되지 않으면 받은 바이트 그대로.

    > 주의: 글꼴 잃은 사용자 영역 글자의 문서 근거(`_lost_font_part`)보다 먼저 바꾼다. 대체 글꼴로 읽힌 run 도
    > 그 근거가 된다.
    """
    from lxml import etree

    low = data.lower()
    if not any(k.encode("utf-8") in low for k in aliases):
        return data
    root = _lxml_part(data)
    if root is None or not symbol_fonts.settle_font_aliases(root, aliases):
        return data
    return etree.tostring(root, encoding="UTF-8", xml_declaration=True, standalone=True)


def _document_font_aliases(doc) -> dict:
    """python-docx 로 연 문서의 글꼴 표 대체 기호 글꼴(`symbol_fonts.font_aliases`)."""
    for rel in doc.part.rels.values():
        if not rel.is_external and rel.reltype.endswith("/fontTable"):
            data = rel.target_part.blob
            return symbol_fonts.font_aliases(_lxml_part(data)) if b"altName" in data else {}
    return {}


def _lost_font_part(z, name: str, data: bytes) -> bytes:
    """글 부품의 글꼴 잃은 사용자 영역 글자를 문서 안 근거로 바꿔 적는다(`symbol_fonts.settle_lost_fonts`).
    각주 · 미주 부품은 본문 부품의 근거도 함께 본다. 바꾼 글자가 없거나 부품이 파싱되지 않으면 받은 바이트 그대로.

    > 주의: 이 자리는 `zip_part` 로 부품 바이트를 받아 각자 해석하는 호출자(표준 ElementTree 를 쓰는 Phase-2
    > 표 · 결정 추출기, Phase-6 TDoc 파서 등)를 위한 것이다. 표준 ElementTree 요소는 부모 · 뿌리에 닿지 못해
    > 글을 읽는 자리(`paragraph_text`)에서 문서 근거를 모을 수 없으므로, 부품을 넘기기 전에 글자를 바꿔 둔다.
    """
    from lxml import etree

    root = _lxml_part(data)
    if root is None:
        return data
    evidence = ()
    if name != "word/document.xml":
        body = _lxml_part(zip_part(z, "word/document.xml"))
        evidence = (body,) if body is not None else ()
    if not symbol_fonts.settle_lost_fonts(root, evidence):
        return data
    return etree.tostring(root, encoding="UTF-8", xml_declaration=True, standalone=True)


#: 수식 개체(`w:object`) · 수식 그림 단위(`w:drawing` · `w:pict`)에 단 읽은 글의 속성 이름(`ole_equation.annotate`).
#: 접두 없는 이름은 `doc_fields.ERROR_LINE` 과 같은 관례다.
EQUATION_TEXT = "equation-text"
#: 수식 편집기 개체인데 ProgID 가 `Equation.` 이 아닌 `o:OLEObject` 에 다는 속성 이름(`ole_equation.annotate`) —
#: 개체 부품을 열어 보아야 알 수 있어 문서를 여는 자리가 단다(`equation_ole`).
EQUATION_OBJECT = "equation-object"
#: 문단 요소에 다는 스타일 이름 · 스타일 개요 수준 속성 이름(`annotate_paragraph_styles`).
STYLE_NAME = "style-name"
STYLE_OUTLINE = "style-outline"
#: 3GPP TS · TR 서식에서 제목이 아닌 문단 스타일(표 · 그림 제목, 표 칸, 주석, 예, 수식, 코드 줄, 그림 자리, 글머리)과
#: Word 내장 캡션 스타일. 이름(`STYLE_NAME`)으로 대 본다.
#:
#: > 주의: 문단에 직접 단 `w:outlineLvl` 이나 스타일이 물려받은 개요 수준만 보고 제목을 찾으면 이 스타일 문단도
#: > 제목이 된다. CR 작성자가 표 제목(`TH`) · ASN.1 줄(`PL`) · 글머리(`B1`) 문단에 개요 수준을 단 채 옮겨 적은
#: > 문서가 있고, 그 문단이 절 경계가 되면 한 절이 여러 조각으로 갈려 조각마다 고친 절인지 따로 판정된다
#: > (`cr_revision_marks`). 번호 없는 조각은 제 표시로만 판정되므로 표시 없는 조각에 든 그 절의 글이 빠진다.
NON_HEADING_STYLES = frozenset((
    "TH", "TF", "TAH", "TAC", "TAL", "TAR", "TAN", "NO", "EX", "EW", "EQ", "PL", "FP",
    "B1", "B2", "B3", "B4", "B5", "caption",
))


def non_heading_style(name: str | None) -> bool:
    """제목이 될 수 없는 문단 스타일 이름인가(`NON_HEADING_STYLES`, 캡션은 대소문자 무관)."""
    n = (name or "").strip()
    return n in NON_HEADING_STYLES or n.lower() == "caption"


#: 표 · 그림 제목 글(`Table 6.6.1.3.1-2: …`, `Figure 8.3.1.2-1: …`). 스타일이 `Normal` 이어도 제목이 아니다.
_CAPTION_TEXT_RE = re.compile(r"^(?:Table|Figure)\s*[0-9A-Z][0-9A-Za-z._\-]*\s*[:.\-–]")


def not_heading(name: str | None, text: str) -> bool:
    """개요 수준이나 제목 스타일이 붙었어도 제목으로 보지 않을 문단인가.

    제목이 아닌 스타일(`non_heading_style`), 표 · 그림 제목 글, ASN.1 정의 줄(`::=`)이다.

    > 주의: CR 작성자는 TS 의 표 제목 · ASN.1 정의 줄을 `Normal` 이나 스타일 없는 문단으로 옮기고 개요 수준을
    > 달아 두기도 한다. 그래서 스타일만으로는 다 거르지 못하고 글 꼴도 본다. ASN.1 주석 줄(`-- …`)은 TS 의
    > ASN.1 묶음을 가르는 자리라 제목으로 둔다(`cr_revision_marks`).
    """
    t = (text or "").strip()
    return non_heading_style(name) or bool(_CAPTION_TEXT_RE.match(t)) or "::=" in t


#: 번호 바로 뒤에 쌍점이 오는 표 · 그림 제목 글(`Table 6.6.5.5.2-1: …`).
_CAPTION_COLON_RE = re.compile(r"^(Table|Figure)\s*[0-9A-Z][0-9A-Za-z._\-]*\s*:")


def heading_styled_role(name: str | None, text: str) -> str | None:
    """제목 스타일 문단 가운데 절이 아닌 문단(`not_heading`)을 무엇으로 받을지. 절이면 None.

    쌍점 꼴 표 제목은 `TH`, 그림 제목은 `TF`, 나머지는 본문 `Normal` 이다. 제목이 될 수 없는 스타일(`TH` ·
    `Normal` 따위, `non_heading_style`)의 문단은 이미 제 자리로 읽히므로 None 이다.

    > 주의: TS · TR 파서는 제목 스타일 문단을 모두 절 제목으로 읽고, 번호를 읽지 못하면 글째 버린다. 그래서
    > 제목 스타일에 적은 표 제목(RAN4 38.176-1 Rel-19 `Table 6.6.5.5.2-1: …`)은 표가 되지 못하고, 표 목록 줄
    > (38.101-1 `Table 5.5A.3.2-1a`)과 문장(RAN5 38.521-4 `Table 5.2.2.1.23.5-1 defines …`)은 절 본문에서 빠진다.
    > 쌍점 없는 줄을 표 제목으로 받지 않는 까닭은 그 표의 제목이 `TH` 문단으로 따로 있어서다(38.101-1 Rel-19 의
    > `5.5A.3.2-1a` 표가 그렇다). 표 제목으로 받으면 같은 번호의 표가 둘이 된다.
    >
    > 주의: 파서는 제목 스타일(`HEADING_LEVEL_MAP`) 문단에만 이 판정을 건다. 모든 문단에 걸면 쌍점 없이 번호만
    > 적은 `TH` 문단(RAN1 38.212 `Table 4.1-1`)이 본문으로 바뀌어 그 표가 사라진다.
    """
    if (name or "").strip() == "" or non_heading_style(name) or not not_heading(name, text):
        return None
    m = _CAPTION_COLON_RE.match((text or "").strip())
    if m:
        return "TH" if m.group(1) == "Table" else "TF"
    return "Normal"


def style_table(z) -> tuple[dict[str, str], dict[str, int]]:
    """이미 연 패키지의 문단 스타일 styleId → 이름, styleId → 개요 수준(0 부터 8).

    주의: 문단의 `w:pStyle` 은 이름이 아니라 styleId 다. 영어판 Word 는 둘이 같은 꼴(`Heading2` · `Heading 2`)이라
    styleId 를 이름 표에 대 보아도 맞지만, 다른 언어판 Word 로 저장한 문서는 styleId 가 `2` · `40` · `Titre2` 따위로
    바뀌고 이름만 `heading 2` 로 남는다(내장 스타일 이름은 어느 언어판에서도 영어로 적힌다). styleId 로 제목을 찾으면
    그런 문서의 제목을 하나도 못 찾는다. 이름은 python-docx `style.name` 과 같은 표기(`Heading 2`)로 둔다.
    개요 수준은 스타일이 선언한 `w:outlineLvl` 이고, 없으면 `w:basedOn` 을 따라 올라가며, 이름이 `heading N` 이면
    N-1 이다. 9 이상은 OOXML 의 본문 수준이라 뺀다. 스타일 부품이 없거나 읽을 수 없으면 빈 표다.
    """
    from xml.etree import ElementTree as ET
    from docx.styles import BabelFish
    try:
        data = zip_part(z, "word/styles.xml")
    except KeyError:
        return {}, {}
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        root = ET.fromstring(repair_tag_balance(data)[0])
    names, own, based = {}, {}, {}
    for s in root.iter(_w("style")):
        if s.get(_w("type")) != "paragraph":
            continue
        sid = s.get(_w("styleId"), "")
        name = s.find(_w("name"))
        raw = name.get(_w("val"), "") if name is not None else ""
        if raw:
            names[sid] = BabelFish.internal2ui(raw)
        lvl = s.find(f"{_w('pPr')}/{_w('outlineLvl')}")
        if lvl is not None and (lvl.get(_w("val")) or "").isdigit():
            own[sid] = int(lvl.get(_w("val")))
        else:
            m = re.match(r"^heading\s*(\d)$", raw, re.IGNORECASE)
            if m:
                own[sid] = int(m.group(1)) - 1
        base = s.find(_w("basedOn"))
        if base is not None:
            based[sid] = base.get(_w("val"))
    outline = {}
    for sid in names.keys() | own.keys():
        cur, seen = sid, set()
        while cur is not None and cur not in own and cur not in seen:
            seen.add(cur)
            cur = based.get(cur)
        if cur in own and own[cur] < 9:
            outline[sid] = own[cur]
    return names, outline


def annotate_paragraph_styles(table: tuple[dict[str, str], dict[str, int]], paragraphs) -> None:
    """문단 요소(`w:p`)마다 제 스타일 이름(`STYLE_NAME`)과 스타일 개요 수준(`STYLE_OUTLINE`)을 단다.

    `table` 은 그 문단이 든 문서의 `style_table`. styleId 를 이름으로 푸는 일을 문서마다 한 번 하고, 문단을 읽는
    자리는 속성만 본다. 여러 파일의
    문단을 한 목록으로 이어 붙여도 문단마다 제 문서의 스타일 표로 풀린 이름이 남는다. 스타일 표에 없는
    styleId 는 이름을 달지 않는다.
    """
    names, outline = table
    for p in paragraphs:
        ppr = p.find(_w("pPr"))
        ps = ppr.find(_w("pStyle")) if ppr is not None else None
        sid = ps.get(_w("val"), "") if ps is not None else ""
        if sid in names:
            p.set(STYLE_NAME, names[sid])
        if sid in outline:
            p.set(STYLE_OUTLINE, str(outline[sid]))


def _equation_part(z, name: str, data: bytes) -> bytes:
    """글 부품 바이트의 수식 개체 · 수식 그림에 읽은 글을 단다. 단 곳이 없거나 부품이 파싱되지 않으면 받은 바이트 그대로."""
    import posixpath
    from urllib.parse import unquote
    from lxml import etree
    import ole_equation  # ole_equation 이 고르는 판독기들이 이 모듈을 쓰므로 부를 때 연다

    parser = etree.XMLParser(huge_tree=True, resolve_entities=False)
    root = _lxml_part(data)
    if root is None:
        return data
    head, base = posixpath.split(name)
    try:
        rels = etree.fromstring(docx_reader.read_zip_part(z, f"{head}/_rels/{base}.rels"), parser)
    except (KeyError, etree.XMLSyntaxError):
        return data
    names = set(z.namelist())
    targets = {r.get("Id"): r.get("Target") for r in rels if r.get("TargetMode") != "External" and r.get("Target")}

    def blob(rid):
        target = targets.get(rid)
        if target is None:
            return None
        target = unquote(target)
        part = target[1:] if target.startswith("/") else posixpath.normpath(posixpath.join(head, target))
        return z.read(part) if part in names else None

    if not ole_equation.annotate(root, blob):
        return data
    return etree.tostring(root, encoding="UTF-8", xml_declaration=True, standalone=True)


REPAIRED_OPENED = 0  # 부품을 고쳐서야 연 문서 수(이 프로세스 몫)


def open_document(path, note: dict | None = None):
    """문서를 열고 본문 트리를 `doc_fields` 로 손질하고, 대응표 없는 글꼴을 글꼴 표의 대체 기호 글꼴로 바꿔
    적고(`symbol_fonts.settle_font_aliases`), 글꼴 잃은 기호 글자를 문서 안 근거로 바꿔 적은
    뒤(`symbol_fonts.settle_lost_fonts`) 수식 개체에 읽은 글을 단다(python-docx 는 각주 · 미주 부품을 읽지 않는다)."""
    import ole_equation  # `_equation_part` 와 같은 까닭으로 부를 때 연다

    doc = _open_package(path, note)
    doc_fields.settle_tree(doc.element, "word/document.xml", path)
    symbol_fonts.settle_font_aliases(doc.element, _document_font_aliases(doc))
    symbol_fonts.settle_lost_fonts(doc.element)
    parts = doc.part.related_parts
    ole_equation.annotate(doc.element, lambda rid: parts[rid].blob if rid in parts else None)
    return doc


def _open_package(path, note: dict | None = None):
    """문서를 연다. 패키지가 아래 다섯 가지로 거절당하면 그 자리만 고쳐 다시 연다.

    짝 없는 닫는 태그   `.doc` 을 변환한 문서 중에 `w:pPr/w:rPr` 안에 짝 없는 `</w:ins>` 가 낀 것이
                        있다. 그 태그만 뺀다(`repair_tag_balance`).
    닫히지 않은 요소    RAN4 R4-162613 · R4-164414 · R4-164695 는 `w:hyperlink` 안에서 연 `w:del` 을
                        닫지 않은 채 `</w:hyperlink>` 가 온다. 바깥 요소의 닫는 태그 바로 앞에서 그 요소를
                        닫는다(`repair_tag_balance`).
    없는 부품 관계      관계 파일(`*.rels`)이 패키지에 없는 내부 부품(`word/NULL` · `word/#this`)을
                        가리킨다. python-docx 는 관계를 따라 부품을 모두 읽으므로 그 관계만 뺀다.
    본문 부품의 형식 표시  매크로 문서(`.docm`)와 서식 파일의 본문 부품은 같은 WordprocessingML 인데
                        `[Content_Types].xml` 이 다른 형식 이름을 단다. 이름이 `.docx` 인 RAN5 CR
                        (R5-220204 등)도 매크로 문서 형식을 단 채 온다. python-docx 는 형식 이름만 보고
                        거절하므로 그 이름만 일반 문서 형식으로 바꾼다.
    한도를 넘는 속성값    VML 도형의 `o:gfxdata` 는 같은 도형을 DrawingML 패키지로 base64 에 담은 사본이다.
                        RAN1 R1-2410334 · R1-2410655 는 그룹 도형 두 개에 그림을 품은 채 44~50MB 짜리
                        `o:gfxdata` 를 달고 있어, 한도(10MB)를 둔 python-docx 의 XML 해석기가
                        `AttValue length too long` 으로 문서를 거절한다. 파서는 이 속성을 읽지 않으므로
                        (도형의 글은 `v:textbox` 에, 그림은 관계로 따로 온다) 그 속성만 뺀다.

    python-docx 는 다섯 다 문서를 통째로 거절해 CR · TS · TR 한 벌이 결과에서 소리 없이 빠진다.
    고친 뒤에도 열리지 않으면 처음의 거절을 그대로 올린다.
    """
    global REPAIRED_OPENED
    try:
        return docx_reader.open_document(path, note)
    except Exception as first:
        from lxml import etree
        broken_xml = isinstance(first, etree.XMLSyntaxError)
        missing_part = isinstance(first, KeyError) and "There is no item named" in str(first)
        other_main = isinstance(first, ValueError) and any(ct in str(first) for ct in _WORD_MAIN_VARIANTS)
        if not (broken_xml or missing_part or other_main):
            reason = _unreadable_reason(path)
            if reason:
                raise ValueError(reason) from first
            raise
        package = _repaired_package(path)
        if package is None:
            raise
        from docx import Document
        doc = Document(package)
        REPAIRED_OPENED += 1
        print(f"  [수선] 부품을 고쳐 읽음: {Path(path).name} — {first}", file=sys.stderr)
        return doc


_OLE_MAGIC = bytes.fromhex("d0cf11e0a1b11ae1")
_WORD_MAIN = "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
# 본문 부품이 같은 WordprocessingML 인데 형식 이름만 다른 것 — 매크로 문서 · 서식 파일 · 매크로 서식 파일
_WORD_MAIN_VARIANTS = (
    "application/vnd.ms-word.document.macroEnabled.main+xml",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.template.main+xml",
    "application/vnd.ms-word.template.macroEnabledTemplate.main+xml",
)


def _unreadable_reason(path) -> str | None:
    """ZIP 패키지로 열리지 않는 파일이 왜 열리지 않는가. ZIP 으로 열리거나 파일을 읽을 수 없으면 None.

    python-docx 는 이 자리를 모두 `Package not found` 로만 알려 경로가 틀린 것처럼 읽히고, 실패 목록에서
    읽을 수 없는 원본과 고칠 수 있는 결함이 갈리지 않는다. 내용으로 가른다.

    빈 파일             0바이트.
    OLE 컨테이너        Word 97-2003 문서(변환본 없는 `.doc` 이거나 `.docx` 이름을 단 것, 변환 대상)와, 암호화(IRM) 된 OOXML 을
                        담은 것(`EncryptedPackage` 스트림). 3GPP 배포 ZIP 에 IRM 문서가 그대로 든 CR 이
                        있다(RAN5 R5-241785~241788).
    DRM 머리            기고자가 사내 DRM 으로 감싸 올린 파일. 머리가 `%TSD-Header-###%`(RAN4 R4-2014798 ·
                        R4-2017021) 이거나 앞 16바이트에 `NASCA` 가 있다. 라이선스 없이는 열리지 않는다.
    잘린 ZIP            `PK` 로 시작하나 ZIP 목록(중앙 디렉토리)이 없다. 배포 ZIP 안의 파일 자체가 중간에서
                        끊긴 것이 있다(RAN4 R4-2419829 · R4-167063 · R4-1714534).
    그 밖               첫 바이트를 함께 적는다.
    """
    import io
    import zipfile

    try:
        with open(path, "rb") as fh:
            head = fh.read(16)
            encrypted = False
            if head[:8] == _OLE_MAGIC:
                marker = "EncryptedPackage".encode("utf-16-le")
                tail = head
                while block := fh.read(io.DEFAULT_BUFFER_SIZE):
                    window = tail + block
                    if marker in window:
                        encrypted = True
                        break
                    tail = window[-(len(marker) - 1):]
    except OSError:
        return None
    if not head:
        return "빈 파일(0바이트)"
    if head[:8] == _OLE_MAGIC:
        if encrypted:
            return "암호화(IRM)된 OOXML 을 담은 OLE 컨테이너 — 라이선스 없이는 읽을 수 없음"
        # 변환본 없는 `.doc` 도 이 자리로 온다(CR 파서가 열기 실패 기록으로 남긴다). 이름을 따라 사유를 가른다.
        if Path(path).suffix.lower() == ".doc":
            return "변환본 없는 Word 97-2003 문서(.doc) — 변환 대상"
        return "OLE 컨테이너(Word 97-2003 형식)가 .docx 이름을 달고 있음 — 변환 대상"
    if head.startswith(b"%TSD-") or b"NASCA" in head:
        return "사내 DRM 으로 감싼 파일 — 라이선스 없이는 읽을 수 없음"
    if zipfile.is_zipfile(path):
        return None
    if head.startswith(b"PK"):
        return "PK 로 시작하나 ZIP 목록(중앙 디렉토리)이 없음 — 중간에서 끊긴 파일"
    return f"Word 문서 형식이 아님(첫 바이트 {head[:8]!r})"


def _repaired_package(path):
    """깨진 부품을 고친 패키지(메모리) — 고칠 것이 없거나 고쳐도 해석되지 않으면 None."""
    import io
    import zipfile
    from lxml import etree

    out = io.BytesIO()
    fixed = 0
    with zipfile.ZipFile(str(path)) as src, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        names = set(src.namelist())
        for info in src.infolist():
            data = src.read(info.filename)
            if info.filename == "[Content_Types].xml":
                data, n = _word_main_content_type(data)
                fixed += n
            elif info.filename.endswith(".rels"):
                data, n = _drop_missing_part_rels(data, info.filename, names)
                fixed += n
            elif info.filename.startswith("word/") and info.filename.endswith(".xml"):
                try:
                    etree.fromstring(data)
                except etree.XMLSyntaxError:
                    data, _ = repair_tag_balance(data)
                    data, _ = _drop_vml_gfxdata(data)
                    try:
                        etree.fromstring(data)
                    except etree.XMLSyntaxError:
                        return None
                    fixed += 1
            dst.writestr(info, data)
    if not fixed:
        return None
    out.seek(0)
    return out


_O_GFXDATA = "{urn:schemas-microsoft-com:office:office}gfxdata"


def _drop_vml_gfxdata(data: bytes) -> tuple[bytes, int]:
    """기본 한도로는 해석되지 않고 한도를 풀면 해석되는 부품에서 VML `o:gfxdata` 속성을 뺀다 → (내용, 뺀 수).

    주의: 한도를 풀어도 해석되지 않는 부품(태그가 깨진 것)은 그대로 돌려준다 — 이 손질은 크기 한도만 다룬다.
    """
    from lxml import etree

    try:
        root = etree.fromstring(data, etree.XMLParser(huge_tree=True, resolve_entities=False))
    except etree.XMLSyntaxError:
        return data, 0
    dropped = 0
    for el in root.iter():
        if _O_GFXDATA in el.attrib:
            del el.attrib[_O_GFXDATA]
            dropped += 1
    if not dropped:
        return data, 0
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True), dropped


def _word_main_content_type(data: bytes) -> tuple[bytes, int]:
    """`[Content_Types].xml` 에서 본문 부품(`/word/document.xml`)의 형식 이름이 매크로 문서 · 서식 파일
    것이면 일반 문서 형식으로 바꾼다 → (내용, 바꾼 수)."""
    from lxml import etree

    try:
        root = etree.fromstring(data)
    except etree.XMLSyntaxError:
        return data, 0
    changed = 0
    for o in root:
        if o.get("PartName") == "/word/document.xml" and o.get("ContentType") in _WORD_MAIN_VARIANTS:
            o.set("ContentType", _WORD_MAIN)
            changed += 1
    if not changed:
        return data, 0
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True), changed


def _drop_missing_part_rels(data: bytes, rels_name: str, names: set) -> tuple[bytes, int]:
    """관계 파일에서 패키지에 없는 내부 부품을 가리키는 관계를 뺀다 → (관계 파일, 뺀 수)."""
    import posixpath
    from urllib.parse import unquote
    from lxml import etree

    try:
        root = etree.fromstring(data)
    except etree.XMLSyntaxError:
        return data, 0
    # `word/_rels/document.xml.rels` 의 관계 대상은 `word/` 기준이고, 패키지 관계는 뿌리 기준이다
    base = posixpath.dirname(posixpath.dirname(rels_name))
    dropped = 0
    for rel in list(root):
        if rel.get("TargetMode") == "External":
            continue
        target = unquote(rel.get("Target") or "")
        part = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join(base, target))
        if part not in names:
            root.remove(rel)
            dropped += 1
    if not dropped:
        return data, 0
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True), dropped


def strict_opened() -> int:
    """이 프로세스가 Strict 이름공간이라 이름을 맞춰 연 문서 수 — 부르는 쪽이 자기 기록에 싣는다."""
    return docx_reader.STATS["이름을 맞춰 연 Strict 문서"]


def strict_parts_read() -> int:
    """이 프로세스가 Strict 이름공간이라 이름을 맞춰 읽은 부품 XML 수(워커 프로세스의 몫은 들지 않는다)."""
    return docx_reader.STATS["이름을 맞춰 읽은 Strict 부품"]


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"


def _w(name: str) -> str:
    return f"{{{W_NS}}}{name}"


_P = _w("p")
_TBL = _w("tbl")
_TR = _w("tr")
_TC = _w("tc")
_R = _w("r")
_T = _w("t")
_DEL_TEXT = _w("delText")
_TAB = _w("tab")
_PTAB = _w("ptab")
_BR = _w("br")
_CR = _w("cr")
_NB_HYPHEN = _w("noBreakHyphen")
_SYM = _w("sym")
_INSERTED = {_w("ins"), _w("moveTo")}
_DELETED = {_w("del"), _w("moveFrom")}
#: 글을 감싸기만 하는 틀. 안으로 들어가 읽는다.
_WRAPPERS = {_w("hyperlink"), _w("smartTag"), _w("sdt"), _w("sdtContent"), _w("fldSimple"),
             _w("customXml"), _w("dir"), _w("bdo")}
#: 문단 글이 아닌 것. 속성 · 글상자 · 그림 · 필드 명령.
_SKIP = {_w("pPr"), _w("rPr"), _w("sdtPr"), _w("sdtEndPr"), _w("drawing"), _w("pict"), _w("object"),
         _w("instrText"), _w("delInstrText"), f"{{{MC_NS}}}AlternateContent"}
_OMATH = f"{{{M_NS}}}oMath"
_MATH = {_OMATH, f"{{{M_NS}}}oMathPara"}
_MATH_T = f"{{{M_NS}}}t"
#: 블록(문단 · 표 · 표의 행 · 칸)을 감싸기만 하는 틀. 안으로 들어가 읽는다.
_BLOCK_WRAPPERS = {_w("sdt"), _w("sdtContent"), _w("customXml")}
_MC_FALLBACK = f"{{{MC_NS}}}Fallback"
_MC_CHOICE = f"{{{MC_NS}}}Choice"
#: 그려지는 것(그림 · 개체 · 도형 · 글상자)을 담는 요소. `paragraph_text(drawn=…)` 가 이 자리마다 부른다.
_DRAWN_ANY = {_w("drawing"), _w("pict"), _w("object"), f"{{{MC_NS}}}AlternateContent"}
_OBJECT = _w("object")
#: 읽은 수식 글(`EQUATION_TEXT`)을 다는 자리 — 수식 개체와, MathType 수식 그림만 그리는 그림 단위.
_EQUATION_HOLDERS = {_w("drawing"), _w("pict"), _OBJECT}

#: 삭제된 글을 어떻게 다루는가.
DROP = "drop"          # 바뀐 뒤의 문서만 읽는다 — 제목 번호 판정
MARK = "mark"          # `[DEL]…[/DEL]` 로 감싸 함께 읽는다 — CR 변경 본문
KEEP = "keep"          # 표시 없이 함께 읽는다 — 바뀌기 전 글이 필요할 때

#: `paragraph_text(math=LINEAR)` — 수식 자리에 선형 표기(`math_linear`)를 넣는다. 청크 본문(`chunk_text`)의 읽기.
LINEAR = "linear"


_TAG = re.compile(rb"<(/?)([A-Za-z_][\w.:-]*)(?:\s[^>]*?)?(/?)>")


def repair_tag_balance(raw: bytes) -> tuple[bytes, int]:
    """태그 짝을 고친 XML 과 고친 수. 엄격한 해석기가 거절한 부품에만 쓴다.

    짝 없는 닫는 태그   Word 가 복구해서 여는 문서 중에 문단 기호 속성(`w:pPr/w:rPr`) 안에 짝 없는
                        `</w:ins>` 가 낀 것이 있다(RAN1 38.213 · 38.214 의 첫 CR). 어떤 요소도 닫지 않으므로
                        그 태그만 뺀다.
    닫히지 않은 요소    RAN4 R4-162613 · R4-164414 · R4-164695 는 `w:hyperlink` 안에서 연 `w:del` 을 닫지 않은
                        채 `</w:hyperlink>` 가 온다. 건너뛴 요소는 바깥 요소 안에서 열렸으므로 늦어도 바깥 요소가
                        닫히기 전에 닫혀야 한다. 그 가장 늦은 자리(바깥 요소의 닫는 태그 바로 앞)에서 닫는다.

    둘 다 글 · 차례를 바꾸지 않는다. 판정할 근거가 없는 것은 건너뛴 요소가 원래 어디서 닫혔는가 하나다 —
    `w:del` · `w:ins` 이면 변경 표시가 덮는 글의 끝이 늘 수 있다. 해석기의 복구 모드는 그 자리에서 열린
    요소를 닫아 버려 짝 없는 닫는 태그 뒤의 글을 대부분 잃고, 고장 자리 뒤에 엔티티로 적은 글자(`&amp;` ·
    `&lt;` · `&quot;` 등)를 빼고 읽는다(R4-162613 의 `AT&T` → `ATT` 등 14자).
    """
    out: list[bytes] = []
    stack: list[bytes] = []
    last = 0
    fixed = 0
    for m in _TAG.finditer(raw):
        closing, name, empty = m.group(1), m.group(2), m.group(3)
        if empty:
            continue
        if not closing:
            stack.append(name)
            continue
        if stack and stack[-1] == name:
            stack.pop()
        elif name not in stack:
            out.append(raw[last:m.start()])
            last = m.end()
            fixed += 1
        else:
            skipped = []
            while stack[-1] != name:
                skipped.append(stack.pop())
            stack.pop()
            out.append(raw[last:m.start()])
            out.append(b"".join(b"</" + t + b">" for t in skipped))
            last = m.start()
            fixed += len(skipped)
    out.append(raw[last:])
    return b"".join(out), fixed


def _math_pieces(node, deleted: bool = False):
    """`node` 아래 수식 글 조각(`m:t`)을 문서 순서로 `(m:t, 읽기 함수)` 짝으로 낸다.

    `deleted` 가 거짓이면 변경 표시로 빠진 자리(`w:del` · `w:moveFrom`) 안 조각은 내지 않는다 — 수식 안에서
    지운 글자는 수식 run(`m:r`) 안의 글 조각을 그 표시로 감싸 적는다.
    읽기 함수는 그 조각을 직접 감싼 요소(수식 run `m:r`)의 `w:rPr` 에서 찾고, 기호 글꼴이 없으면 None 이다.
    감싼 요소를 위로 거슬러 찾지 않고 내려가며 넘겨 준다 — 회의록 · TR · CR 파서 몇은 문서를 ElementTree 로
    읽어 넘기는데, ElementTree 요소에는 부모를 찾는 길(`getparent`)이 없다.
    """
    read = False
    for child in node:
        if child.tag == _MATH_T:
            if read is False:
                read = symbol_fonts.run_reader(node)
            yield child, read
        elif deleted or child.tag not in _DELETED:
            yield from _math_pieces(child, deleted)


def _m(name: str) -> str:
    return f"{{{M_NS}}}{name}"


_M_VAL = _m("val")
_M_E = _m("e")
_M_SUB = _m("sub")
_M_SUP = _m("sup")
_M_DEG = _m("deg")
_M_NUM = _m("num")
_M_DEN = _m("den")
_M_CTRL = _m("ctrlPr")
_OFF = {"off", "0", "false"}


def _pr(node):
    """수식 구조 `node`의 속성 요소를 반환한다(`m:d`이면 `m:dPr`). 없으면 None."""
    return node.find(node.tag + "Pr")


def _prop_char(pr, name: str, default: str) -> str:
    """속성 묶음 `pr` 의 기호 글자(`m:chr` · `m:begChr` · `m:pos` …의 `m:val`).

    요소가 없거나 `m:val` 을 적지 않았으면 `default`(ECMA-376 의 기본 글자), `m:val=""` 이면 빈 글이다.
    """
    el = pr.find(_m(name)) if pr is not None else None
    if el is None:
        return default
    val = el.get(_M_VAL)
    return default if val is None else val


def _prop_on(pr, name: str, absent: bool) -> bool:
    """속성 묶음 `pr` 의 켜고 끄는 값(`m:show` · `m:degHide` …). 요소가 없으면 `absent`, 값을 적지 않았으면 켜짐."""
    el = pr.find(_m(name)) if pr is not None else None
    if el is None:
        return absent
    return el.get(_M_VAL, "on").lower() not in _OFF


def _glyph_shown(node, deleted: bool) -> bool:
    """수식 구조의 기호를 출력할지 판단한다. 구조의 삭제 표시는 `m:ctrlPr` 안의 `w:del`로 확인한다.

    넣었다가 지운 짜임은 `m:ctrlPr` > `w:ins` > `w:del` 로 적으므로 바로 아래만 보지 않고 안을 모두 본다.
    """
    if deleted:
        return True
    pr = _pr(node)
    ctrl = pr.find(_M_CTRL) if pr is not None else None
    return ctrl is None or not any(c.tag in _DELETED for c in ctrl.iter())


def _read_d(node, deleted: bool, out: list) -> None:
    """괄호(`m:d`): 여는 글자 · 칸(`m:e`)마다 구분 글자 · 닫는 글자. 기본은 `(` · `|` · `)`."""
    pr, shown = _pr(node), _glyph_shown(node, deleted)
    if shown:
        out.append(_prop_char(pr, "begChr", "("))
    sep = _prop_char(pr, "sepChr", "|") if shown else ""
    for i, e in enumerate(c for c in node if c.tag == _M_E):
        if i:
            out.append(sep)
        _math_glyphs(e, deleted, out)
    if shown:
        out.append(_prop_char(pr, "endChr", ")"))


def _read_nary(node, deleted: bool, out: list) -> None:
    """큰 연산자(`m:nary`): 연산자 글자(기본 `∫`) · 아래 · 위 범위(숨기지 않은 것) · 밑글."""
    pr = _pr(node)
    if _glyph_shown(node, deleted):
        out.append(_prop_char(pr, "chr", "\u222b"))
    hidden = {_M_SUB: _prop_on(pr, "subHide", False), _M_SUP: _prop_on(pr, "supHide", False)}
    for c in node:
        if c.tag == _M_E or (c.tag in hidden and not hidden[c.tag]):
            _math_glyphs(c, deleted, out)


def _read_rad(node, deleted: bool, out: list) -> None:
    """근호(`m:rad`): 차수(숨기지 않았으면) · `√` · 밑글."""
    if not _prop_on(_pr(node), "degHide", False):
        for c in node:
            if c.tag == _M_DEG:
                _math_glyphs(c, deleted, out)
    if _glyph_shown(node, deleted):
        out.append("\u221a")
    for c in node:
        if c.tag == _M_E:
            _math_glyphs(c, deleted, out)


#: 띄움 꼴 악센트 중 NFKD 가 「빈칸 + 결합 부호」로 풀리지 않는 것 — 같은 자리에 쓰는 결합 부호.
_SPACING_ACCENT = {"^": "\u0302", "~": "\u0303"}


def _accent(ch: str) -> str:
    """악센트(`m:acc`)의 `m:chr` 를 결합 부호로 맞춘다. 띄움 꼴(`^` · `~` 와 NFKD 가 「빈칸 + 결합 부호」인
    `¯` · `˙` · `¨` 따위)은 그 결합 부호로, 나머지는 그대로 돌려준다.

    주의: 같은 수식이 문서마다 두 꼴로 적힌다. 38.901 은 결합 부호(`n̂` · `ẏ` · `ẍ`)로, 38.900 은 같은 수식을
    띄움 꼴(`n^` · `y˙` · `x¨`)로 적었다. TS · TR 347 문서의 `m:acc` 에서 결합 부호가 대부분이고 띄움 꼴은
    38.811 · 38.900 · 38.742 세 문서의 180 개(`^` 126 · `¯` 42 · `˙` 5 · `¨` 4 · `~` 3)다. MTEF 수식
    (`mtef_linear`)도 꾸밈표를 결합 부호로 쓴다. 맞추지 않으면 같은 수식이 문서마다 다른 글이 되고, 선형 표기에서
    띄움 꼴 `^` 는 위첨자 표지와 구별되지 않는다(`n^` 다음 글이 위첨자로 읽힌다)."""
    if len(ch) != 1:
        return ch
    mark = _SPACING_ACCENT.get(ch)
    if mark:
        return mark
    nfkd = unicodedata.normalize("NFKD", ch)
    if len(nfkd) == 2 and nfkd[0] == " " and unicodedata.category(nfkd[1]) == "Mn":
        return nfkd[1]
    return ch


def _after_base(default: str, fold: "Callable[[str], str]" = str):
    """밑글 뒤에 `m:chr` 기호 하나를 붙이는 짜임 — 악센트(`m:acc`, 기본 U+0302, `fold=_accent`) · 묶음 기호
    (`m:groupChr`, 기본 U+23DF)."""
    def read(node, deleted: bool, out: list) -> None:
        for c in node:
            if c.tag == _M_E:
                _math_glyphs(c, deleted, out)
        if _glyph_shown(node, deleted):
            out.append(fold(_prop_char(_pr(node), "chr", default)))
    return read


def _read_bar(node, deleted: bool, out: list) -> None:
    """윗줄 · 밑줄(`m:bar`): 밑글 뒤에 결합 윗줄 U+0305(`m:pos` top, 기본) 또는 결합 밑줄 U+0332(bot)."""
    for c in node:
        if c.tag == _M_E:
            _math_glyphs(c, deleted, out)
    if _glyph_shown(node, deleted):
        out.append("\u0332" if _prop_char(_pr(node), "pos", "top") == "bot" else "\u0305")


def _read_f(node, deleted: bool, out: list) -> None:
    """분수(`m:f`): 분자 · `/` · 분모. 막대를 그리지 않는 `noBar`(쌓기)는 `/` 없이 잇는다."""
    for c in node:
        if c.tag == _M_DEN and _glyph_shown(node, deleted) and _prop_char(_pr(node), "type", "bar") != "noBar":
            out.append("/")
        if c.tag in (_M_NUM, _M_DEN):
            _math_glyphs(c, deleted, out)


def _read_phant(node, deleted: bool, out: list) -> None:
    """팬텀(`m:phant`): `m:show` 가 꺼져 있으면 밑글을 그리지 않는다(자리만 차지한다)."""
    if _prop_on(_pr(node), "show", True):
        for c in node:
            if c.tag == _M_E:
                _math_glyphs(c, deleted, out)


#: 글 조각 밖에서 기호를 그리거나 밑글을 숨기는 짜임 — 기호 글자 · 기본값은 ECMA-376 Part 1 §22.1 을 따른다.
_GLYPH_READERS = {
    _m("d"): _read_d,
    _m("nary"): _read_nary,
    _m("rad"): _read_rad,
    _m("acc"): _after_base("\u0302", _accent),
    _m("groupChr"): _after_base("\u23df"),
    _m("bar"): _read_bar,
    _m("f"): _read_f,
    _m("phant"): _read_phant,
}


def _math_glyphs(node, deleted: bool, out: list) -> None:
    """`node` 아래 수식의 문자를 문서 순서대로 `out`에 추가한다(`math_text`의 재귀 처리).

    글 조각(`m:t`)은 그 조각을 직접 감싼 수식 run(`m:r`)의 `w:rPr` 기호 글꼴로 읽는다(`_math_pieces` 와 같은 길 —
    ElementTree 요소도 받으려고 위로 거슬러 찾지 않는다). 수식 run 안의 `w:sym` 은 그 기호 글자다. 속성 묶음
    (`…Pr`)에는 글이 없다. 줄바꿈 없는 하이픈(`w:noBreakHyphen`)은 문단 글과 같이 `-` 다.
    """
    read = False
    for child in node:
        tag = child.tag
        if tag == _MATH_T:
            if child.text:
                if read is False:
                    read = symbol_fonts.run_reader(node)
                out.append(read(child.text) if read else child.text)
        elif tag == _SYM:
            out.append(symbol_fonts.sym_text(child))
        elif tag == _NB_HYPHEN:
            out.append("-")
        elif tag in _DELETED:
            if deleted:
                _math_glyphs(child, deleted, out)
        elif tag in _GLYPH_READERS:
            _GLYPH_READERS[tag](child, deleted, out)
        elif isinstance(tag, str) and not tag.endswith("Pr"):
            _math_glyphs(child, deleted, out)


def math_text(elem, deleted: bool = False) -> str:
    """OMML 수식이 그리는 글자를 읽는 차례로 잇는다. 완전한 LaTeX 가 아니라 기호 글이다.

    글 조각(`m:t`)에 더해 짜임이 그리는 기호도 넣는다 — 괄호(`m:d`), 큰 연산자(`m:nary`), 근호(`m:rad` → `√`, 차수는
    그 앞), 악센트(`m:acc`) · 묶음 기호(`m:groupChr`)는 밑글 뒤에 그 글자, 윗줄 · 밑줄(`m:bar`)은 결합 글자, 분수
    막대(`m:f`)는 `/`. 기호 글자를 적지 않은 짜임은 ECMA-376 의 기본 글자로 읽는다. 위 · 아래 첨자처럼 자리만
    옮기고 기호를 그리지 않는 짜임은 글자를 넣지 않는다 — `x_i` 와 `xi` 가 같은 글이 된다(짜임은 LaTeX 판독기
    몫이다). 꺼 둔 팬텀 · 숨긴 차수 · 숨긴 큰 연산자 범위는 그리지 않으므로 넣지 않는다.
    변경 표시로 빠진 글자와 지운 짜임의 기호는 `deleted` 가 참일 때만 넣는다.
    """
    out: list[str] = []
    _math_glyphs(elem, deleted, out)
    return "".join(out).strip()


#: 첨자 · 분자 · 분모를 괄호 없이 적어도 되는 글 — 글자 · 숫자 · 결합 부호 · 프라임 · `*` · `∞` · 소수점만.
_ATOM = re.compile(r"(?:[^\W_]|[\u0300-\u036f\u20d0-\u20ff′″‴'*∗∞.])+")
_PAIRS = {"(": ")", "[": "]", "{": "}", "⌊": "⌋", "⌈": "⌉", "〈": "〉", "⟨": "⟩", "|": "|", "‖": "‖"}
#: 밑글을 괄호로 묶어야 하는 글 — 공백 · 연산 기호가 들면 첨자가 어디에 붙는지 흐려진다.
_BASE_BREAK = re.compile(r"[\s+\-−=<>≤≥≠±·×÷/,;:→←↔⇒∈∉∑∏\u222b]")
#: 보이지 않는 연산자(함수 적용 · 보이지 않는 곱 · 구분 · 더하기) — 그려지지 않는다.
_INVISIBLE = str.maketrans("", "", "\u2061\u2062\u2063\u2064")
#: 괄호 없이 글자 · 숫자로 끝난 첨자 · 분모 · 근호 밑글 뒤 자리. 바로 뒤에 글자 · 숫자가 오면 `_linear` 가 한 칸으로
#: 바꾸고 아니면 지운다 — 붙여 적으면 뒤 글자가 첨자 · 분모로 읽힌다(38.211 `N_symb^slot N_slot^(subframe,μ)`).
_OPEN = "\x01"
_OPEN_GAP = re.compile(_OPEN + r"(?=[^\W_])")
#: MARK 읽기에서 수식 안 지운 자리를 여닫는 표지. 지운 글 조각과, 지운 짜임(제어 속성 안 `w:del`)이 그리는 기호
#: (`_` · `^` · `/` · 괄호 · 연산자 글자 · 칸 구분 · 짜임이 넣는 묶음 괄호와 빈칸)를 이 둘로 감싼다. `_linear` 가
#: 맞닿은 지운 자리를 하나로 합친 뒤 `[DEL]` · `[/DEL]` 로 바꾼다 — 짜임을 통째로 지운 자리는 기호까지 한 덩어리로
#: 표지 안에 들고, 지우지 않은 짜임의 기호는 표지 밖에 남는다. 짜임의 괄호 묶기 판정(`_grp` · `_base` · `_open` ·
#: `_seq` · `_lin_func`)은 표지를 뺀 글로 한다.
#: 주의: 표지를 `[DEL]` 글로 바로 넣으면 짜임 기호가 지운 자리 밖에 남고(38.214 `[DEL]n+[/DEL]([DEL]3N[/DEL])_…`),
#: `[` · `]` 가 글로 읽혀 한 덩어리 첨자에도 괄호가 붙으며, 보이지 않는 연산자만 지운 자리는 빈 `[DEL][/DEL]` 이 된다.
_DEL_ON = "\x04"
_DEL_OFF = "\x05"
_UNMARK = str.maketrans("", "", _DEL_ON + _DEL_OFF)
_WORD = re.compile(r"[^\W_]")
#: 수식과 둘레 글의 경계 — `paragraph_text(math=LINEAR)` 가 수식 글 앞에 `_EDGE_IN`, 뒤에 `_EDGE_OUT` 을 둔다.
#: 둘레 글의 글자 · 숫자와 수식 끝의 낱말 글자가 맞닿으면 한 칸, 아니면 지운다. 수식은 둘레 글과 따로 놓인 개체라
#: 낱말이 그 경계를 넘지 않는다(38.201 `for all ` · 수식 `a` · `and `).
#: 수식 뒤 경계에서는 결합 부호와 프라임도 낱말 글자로 친다 — 앞 글자에 붙어 한 글자를 이루므로, 띄우지 않으면
#: 둘레 낱말이 그 글자에 붙는다(38.901 `ẏ` · `and`, 38.900 `θ'` · `given`).
#: 주의: 괄호 · 연산 기호가 경계에 오면 띄우지 않는다 — 기호가 이미 낱말을 가른다(38.812 `R_(n_k n_k)` · `is`,
#: 38.211 `Δf_RA∈{15,30,60,120,480,960}` · `kHz`). TS · TR 347 문서에서 글자 · 숫자끼리 맞닿은 경계가 3,248 곳,
#: 기호와 글자 · 숫자가 맞닿은 경계가 약 1,100 곳이다. 이웃한 두 수식 사이(`_EDGE_OUT` 바로 뒤 `_EDGE_IN`)는
#: 띄우지 않는다 — Word 는 줄바꿈 없이 이웃한 수식을 하나로 그린다.
_EDGE_IN = "\x02"
_EDGE_OUT = "\x03"
_EDGE_GAP = re.compile(r"(?<=[^\W_])" + _EDGE_IN + r"(?=[^\W_])"
                       r"|(?:(?<=[^\W_])|(?<=[\u0300-\u036f\u20d0-\u20ff′″‴']))" + _EDGE_OUT + r"(?=[^\W_])")
#: MARK 읽기에서 경계 표지에 `[DEL]` · `[/DEL]` 이 맞닿은 자리 — `_EDGE_GAP` 은 표지 글의 `]` · `[` 를 이웃 글자로 보아
#: 빈칸을 놓친다(`… where Xµ [DEL]Z'_m[/DEL]is …`). 표지를 건너뛴 두 이웃 글자로 같은 판정을 하고, 빈칸은 지운
#: 쪽 자리 안에 둔다 — 표지를 빼면 KEEP 글과 같고, 지운 자리를 빼면 빈칸이 지운 쪽과 함께 빠진다.
_EDGE_GAP_MARKED = re.compile(r"(?<=(.))((?:\[/?DEL\])*)([" + _EDGE_IN + _EDGE_OUT + r"])((?:\[/?DEL\])*)(?=[^\W_])",
                              re.S)
_EDGE_PRIME = re.compile(r"[\u0300-\u036f\u20d0-\u20ff′″‴']")


def _edge_gap_marked(m: "re.Match[str]") -> str:
    left, before, edge, after = m.group(1), m.group(2), m.group(3), m.group(4)
    if not (before or after) or not (_WORD.match(left) or (edge == _EDGE_OUT and _EDGE_PRIME.match(left))):
        return before + edge + after
    text = m.string[:m.start(2)]
    if text.count("[DEL]") > text.count("[/DEL]"):
        return " " + before + edge + after
    return before + edge + after + " "


def _bracketed(s: str) -> bool:
    """`s` 전체가 한 쌍의 괄호로 감싸였는가 — `(a,b)` 는 참, `(a)(b)` 는 거짓."""
    close = _PAIRS.get(s[:1])
    if close is None or len(s) < 2 or s[-1] != close:
        return False
    if close == s[0]:
        return s.count(close) == 2
    depth = 0
    for i, ch in enumerate(s):
        if ch == s[0]:
            depth += 1
        elif ch == close:
            depth -= 1
            if depth == 0:
                return i == len(s) - 1
    return False


_DEL_SPAN = re.compile(_DEL_ON + "[^" + _DEL_ON + _DEL_OFF + "]*" + _DEL_OFF)


def _plain(s: str) -> str:
    """지운 자리 표지(`_DEL_ON` · `_DEL_OFF`)를 뺀 글 — 묶기 판정은 이 글로 한다."""
    return s.translate(_UNMARK)


def _kept(s: str) -> str:
    """지운 자리를 통째로 뺀 글 — 같은 칸을 DROP 으로 읽은 글이다. 짜임이 넣는 기호가 DROP 에서도 나오는지 이 글로
    가린다: 내용을 다 지운 칸의 첨자 기호 · 칸 구분, 지운 글이 빠지면 필요 없어지는 묶음 괄호는 지운 자리에 든다."""
    while _DEL_ON in s:
        s, n = _DEL_SPAN.subn("", s)
        if not n:
            break
    return s


def _gone(node, deleted: str) -> bool:
    """MARK 읽기에서 짜임 `node` 를 지웠는가 — 그 짜임이 그리는 기호를 지운 자리 표지 안에 둔다."""
    return deleted == MARK and not _glyph_shown(node, False)


def _sym(s: str, gone: bool) -> str:
    """짜임이 넣는 기호 글 `s`. 지운 짜임(`gone`)이면 지운 자리 표지로 감싼다."""
    return f"{_DEL_ON}{s}{_DEL_OFF}" if gone and s else s


def _open(s: str) -> str:
    """짜임 글이 글자 · 숫자로 끝나면(괄호로 묶지 않은 끝 조각) `_OPEN` 을 붙인다. 지운 글을 빼면 그렇게 끝나지 않는
    짜임의 `_OPEN` 은 지운 자리에 둔다(DROP 에는 없는 자리)."""
    if not _plain(s)[-1:].isalnum():
        return s
    return s + (_OPEN if _plain(_kept(s))[-1:].isalnum() else _sym(_OPEN, True))


def _grp_needed(s: str) -> bool:
    return bool(s) and not _ATOM.fullmatch(s) and not _bracketed(s)


def _base_needed(s: str) -> bool:
    return bool(_BASE_BREAK.search(s)) and not _bracketed(s)


def _wrap(s: str, needed: "Callable[[str], bool]", gone: bool) -> str:
    """`needed` 가 참이면 `s` 를 `( )` 로 묶는다. 판정은 표지를 뺀 글로 하고, 지운 글을 빼면(`_kept`) 묶을 필요가
    없어지는 괄호는 지운 자리에 둔다."""
    if not needed(_plain(s)):
        return s
    g = gone or not needed(_plain(_kept(s)))
    return _sym("(", g) + s + _sym(")", g)


def _grp(s: str, gone: bool = False) -> str:
    """첨자 · 분자 · 분모 글 — 한 덩어리(`_ATOM`)이거나 이미 괄호로 감싼 글이 아니면 `( )` 로 묶는다."""
    return _wrap(s, _grp_needed, gone)


def _base(s: str, gone: bool = False) -> str:
    """첨자가 붙는 밑글 — 공백 · 연산 기호가 들고 괄호로 감싸지 않았으면 `( )` 로 묶는다."""
    return _wrap(s, _base_needed, gone)


def _lin(node, deleted: str) -> str:
    """`node` 아래 수식을 재귀적으로 선형 텍스트로 읽는다. 문자·기호·삭제 표시는 `_math_glyphs`와
    같은 규칙으로 읽고, 짜임은 `_LINEAR` 의 읽기로 넘긴다. 수식 run 안 줄바꿈(`w:br` · `w:cr`)은 `\\n` 이다."""
    parts: list[str] = []
    read = False
    for child in node:
        tag = child.tag
        if tag == _MATH_T:
            if child.text:
                if read is False:
                    read = symbol_fonts.run_reader(node)
                parts.append(read(child.text) if read else child.text)
        elif tag == _SYM:
            parts.append(symbol_fonts.sym_text(child))
        elif tag == _NB_HYPHEN:
            parts.append("-")
        elif tag == _BR or tag == _CR:
            parts.append("\n")
        elif tag in _DELETED:
            if deleted != DROP:
                gone = _lin(child, deleted)
                if gone:
                    parts.append(f"{_DEL_ON}{gone}{_DEL_OFF}" if deleted == MARK else gone)
        elif tag in _LINEAR:
            parts.append(_LINEAR[tag](child, deleted))
        elif isinstance(tag, str) and not tag.endswith("Pr"):
            parts.append(_lin(child, deleted))
    return "".join(parts)


def _part(node, tag: str, deleted: str) -> str:
    return "".join(_lin(c, deleted) for c in node if c.tag == tag)


def _parts(node, tag: str, deleted: str) -> list[str]:
    return [_lin(c, deleted) for c in node if c.tag == tag]


def _scripted(node, deleted: str, base: str, sub: str, sup: str) -> str:
    """밑글 뒤에 아래첨자 `_` · 위첨자 `^`. 지운 짜임(`_glyph_shown` 거짓)은 표지 없이 잇는다."""
    if not _glyph_shown(node, deleted != DROP):
        return base + sub + sup
    g = _gone(node, deleted)
    return _open(_base(base, g) + (_sym("_", g or not _kept(sub)) + _grp(sub, g) if sub else "")
                 + (_sym("^", g or not _kept(sup)) + _grp(sup, g) if sup else ""))


def _lin_ssub(node, deleted: str) -> str:
    return _scripted(node, deleted, _part(node, _M_E, deleted), _part(node, _M_SUB, deleted), "")


def _lin_ssup(node, deleted: str) -> str:
    return _scripted(node, deleted, _part(node, _M_E, deleted), "", _part(node, _M_SUP, deleted))


def _lin_ssubsup(node, deleted: str) -> str:
    return _scripted(node, deleted, _part(node, _M_E, deleted), _part(node, _M_SUB, deleted),
                     _part(node, _M_SUP, deleted))


def _lin_spre(node, deleted: str) -> str:
    """앞첨자(`m:sPre`): `_아래^위` 를 밑글 앞에, 밑글과는 한 칸 띄운다."""
    sub, sup, base = _part(node, _M_SUB, deleted), _part(node, _M_SUP, deleted), _part(node, _M_E, deleted)
    if not _glyph_shown(node, deleted != DROP):
        return sub + sup + base
    g = _gone(node, deleted)
    pre = ((_sym("_", g or not _kept(sub)) + _grp(sub, g) if sub else "")
           + (_sym("^", g or not _kept(sup)) + _grp(sup, g) if sup else ""))
    return pre + _sym(" ", g or not _kept(pre) or not _kept(base)) + base if pre and base else pre + base


def _limit(mark: str):
    """밑글 아래 · 위 범위(`m:limLow` · `m:limUpp`) — 아래는 `_`, 위는 `^` 로 붙인다(`lim_(n→∞)`)."""
    def read(node, deleted: str) -> str:
        base, lim = _part(node, _M_E, deleted), _part(node, _M_LIM, deleted)
        if not lim or not _glyph_shown(node, deleted != DROP):
            return base + lim
        g = _gone(node, deleted)
        return _open(_base(base, g) + _sym(mark, g or not _kept(lim)) + _grp(lim, g))
    return read


def _lin_nary(node, deleted: str) -> str:
    """큰 연산자(`m:nary`): 연산자 글자 · 숨기지 않은 범위 `_아래^위` · 한 칸 · 밑글(`∑_(i=1)^j L_i`)."""
    pr, shown = _pr(node), _glyph_shown(node, deleted != DROP)
    sub = "" if _prop_on(pr, "subHide", False) else _part(node, _M_SUB, deleted)
    sup = "" if _prop_on(pr, "supHide", False) else _part(node, _M_SUP, deleted)
    body = _part(node, _M_E, deleted)
    if not shown:
        return sub + sup + body
    g = _gone(node, deleted)
    head = (_sym(_prop_char(pr, "chr", "\u222b"), g) + (_sym("_", g or not _kept(sub)) + _grp(sub, g) if sub else "")
            + (_sym("^", g or not _kept(sup)) + _grp(sup, g) if sup else ""))
    return head + _sym(" ", g or not _kept(body)) + body if body else _open(head)


def _lin_f(node, deleted: str) -> str:
    """분수(`m:f`): `분자/분모`, 막대 없는 쌓기(`noBar`)는 `분자¦분모`. 한 덩어리가 아닌 쪽은 괄호로 묶는다."""
    num, den = _part(node, _M_NUM, deleted), _part(node, _M_DEN, deleted)
    if not _glyph_shown(node, deleted != DROP):
        return num + den
    g = _gone(node, deleted)
    bar = "¦" if _prop_char(_pr(node), "type", "bar") == "noBar" else "/"
    return _open(_grp(num, g) + _sym(bar, g) + _grp(den, g))


def _lin_rad(node, deleted: str) -> str:
    """근호(`m:rad`): `√밑글`, 차수가 있으면 `√(차수&밑글)`(UnicodeMath 의 적기)."""
    deg = "" if _prop_on(_pr(node), "degHide", False) else _part(node, _M_DEG, deleted)
    body = _part(node, _M_E, deleted)
    if not _glyph_shown(node, deleted != DROP):
        return deg + body
    g = _gone(node, deleted)
    return (_sym("\u221a(", g) + deg + _sym("&", g) + body + _sym(")", g) if deg
            else _open(_sym("\u221a", g) + _grp(body, g)))


def _lin_d(node, deleted: str) -> str:
    """괄호(`m:d`): 여는 글자 · 칸(`m:e`)마다 구분 글자 · 닫는 글자. 기본은 `(` · `|` · `)`."""
    pr, items = _pr(node), _parts(node, _M_E, deleted)
    if not _glyph_shown(node, deleted != DROP):
        return "".join(items)
    g = _gone(node, deleted)
    return (_sym(_prop_char(pr, "begChr", "("), g) + _sym(_prop_char(pr, "sepChr", "|"), g).join(items)
            + _sym(_prop_char(pr, "endChr", ")"), g))


def _lin_func(node, deleted: str) -> str:
    """함수(`m:func`): 함수 이름 · 인자. 인자가 괄호로 열리지 않으면 한 칸 띄운다(`log_2 x` · `max(a,b)`)."""
    name, arg = _part(node, _M_FNAME, deleted), _part(node, _M_E, deleted)
    return (name + _sym(" ", _gone(node, deleted) or not _kept(name) or not _kept(arg)) + arg
            if name and arg and _plain(arg)[:1] not in _PAIRS else name + arg)


def _lin_after(default: str, fold: "Callable[[str], str]" = str):
    """밑글 뒤에 `m:chr` 기호 하나 — 악센트(`m:acc`, `fold=_accent`) · 묶음 기호(`m:groupChr`). 밑글이 한 덩어리가
    아니면 괄호로 묶는다."""
    def read(node, deleted: str) -> str:
        body = _part(node, _M_E, deleted)
        if not _glyph_shown(node, deleted != DROP):
            return body
        g = _gone(node, deleted)
        return _grp(body, g) + _sym(fold(_prop_char(_pr(node), "chr", default)), g)
    return read


def _lin_bar(node, deleted: str) -> str:
    """윗줄 · 밑줄(`m:bar`): 밑글 뒤에 결합 윗줄 U+0305(`m:pos` top, 기본) 또는 결합 밑줄 U+0332(bot)."""
    body = _part(node, _M_E, deleted)
    if not _glyph_shown(node, deleted != DROP):
        return body
    g = _gone(node, deleted)
    return _grp(body, g) + _sym("\u0332" if _prop_char(_pr(node), "pos", "top") == "bot" else "\u0305", g)


def _seq(parts: list[str], sep: str, gone: bool = False, drop_void: bool = True) -> str:
    """칸 · 줄을 `sep` 로 잇는다. 앞 조각이 이미 `,` · `;` 로 끝나면 한 칸만 띄우고, 뒤 조각이 `,` · `;` 로 시작하면
    그대로 붙인다 — 식과 조건을 칸으로 나눈 자리(38.211 `e^jαn r̅_(u,v)(n),` · `0≤n<M_ZC`, 38.901 τ_n 의 조건 칸
    `,for NLOS`)에서 구분 글자가 겹치지 않게 한다. 끝 · 시작의 빈칸은 건너 보고 잰다(38.521-2 `v_(n,m)=…),` 줄은 쉼표
    뒤에 빈칸 글자를 하나 더 둔다)."""
    out: list[str] = []
    for i, s in enumerate(parts):
        if i:
            void = drop_void and (not _kept(s) or not any(_kept(x) for x in parts[:i]))
            out.append(_sym(" " if _plain(parts[i - 1]).rstrip()[-1:] in (",", ";")
                            else "" if _plain(s).lstrip()[:1] in (",", ";") else sep, gone or void))
        out.append(s)
    return "".join(out)


def _lin_rows(node, deleted: str) -> str:
    """식 배열(`m:eqArr`)의 줄을 `; ` 로 잇는다(`_seq`)."""
    return _seq([r for r in _parts(node, _M_E, deleted) if r], "; ", _gone(node, deleted))


def _lin_matrix(node, deleted: str) -> str:
    """행렬(`m:m`): 칸은 `, `, 행은 `; ` 로 잇는다(`_seq`). 둘러싼 괄호는 바깥 `m:d` 가 그린다."""
    g = _gone(node, deleted)
    rows = [_seq(_parts(mr, _M_E, deleted), ", ", g, drop_void=False) for mr in node if mr.tag == _M_MR]
    return _seq([r for r in rows if _plain(r).strip(", ")], "; ", g)


def _lin_phant(node, deleted: str) -> str:
    """팬텀(`m:phant`): `m:show` 가 꺼져 있으면 그리지 않는다."""
    return _part(node, _M_E, deleted) if _prop_on(_pr(node), "show", True) else ""


_M_LIM = _m("lim")
_M_FNAME = _m("fName")
_M_MR = _m("mr")
#: 선형 표기에서 짜임마다 읽는 규칙. 여기 없는 짜임(`m:box` · `m:borderBox` …)은 안의 글을 차례로 잇는다.
_LINEAR = {
    _m("sSub"): _lin_ssub,
    _m("sSup"): _lin_ssup,
    _m("sSubSup"): _lin_ssubsup,
    _m("sPre"): _lin_spre,
    _m("limLow"): _limit("_"),
    _m("limUpp"): _limit("^"),
    _m("nary"): _lin_nary,
    _m("f"): _lin_f,
    _m("rad"): _lin_rad,
    _m("d"): _lin_d,
    _m("func"): _lin_func,
    _m("acc"): _lin_after("\u0302", _accent),
    _m("groupChr"): _lin_after("\u23df"),
    _m("bar"): _lin_bar,
    _m("eqArr"): _lin_rows,
    _m("m"): _lin_matrix,
    _m("phant"): _lin_phant,
}


def math_linear(elem, deleted: str = DROP) -> str:
    """OMML 수식을 선형 표기로 — 위 · 아래첨자와 분수 · 근호 · 큰 연산자의 짜임을 글로 남긴다.

    `math_text` 는 짜임이 그리는 기호만 넣어 38.211 의 `N_symb^slot` 이 `Nsymbslot` 으로 붙는다. 청크 본문처럼
    수식을 글로 읽어야 하는 자리는 이것을 쓴다. 적기는 UnicodeMath(Unicode Technical Note #28)의 선형 표기를 따른다.
        아래 · 위첨자          `x_i` · `x^2` · `N_(RB,c)^j`   앞첨자 `_아래^위 밑글`
        범위(`limLow`)         `lim_(n→∞)`                   큰 연산자 `∑_(i=1)^j L_i`
        분수                   `a/b` · `(x+1)/2` · 쌓기 `n¦k`  근호 `√x` · `√(n&x)`
        괄호 · 함수            `(a|b)` · `max(a,b)` · `log_2 x`
        악센트 · 윗줄          밑글 뒤 결합 글자              식 배열 · 행렬  줄 `; ` · 칸 `, `
    첨자 · 분자 · 분모는 글자 · 숫자 한 덩어리이거나 이미 괄호로 감싼 글이 아니면 `( )` 로 묶는다. 밑글은 공백 ·
    연산 기호가 들 때만 묶는다(첨자가 겹친 밑글은 그대로). 괄호 없이 끝난 첨자 · 분모 바로 뒤에 글자 · 숫자가
    이어지면 한 칸 띄운다(`_OPEN`). 기호 글꼴 · 지운 짜임 · 꺼 둔 팬텀 ·
    숨긴 차수 · 숨긴 범위는 `math_text` 와 같게 읽는다. 보이지 않는 연산자(U+2061~2064)는 뺀다.
    `deleted` 는 수식 안에서 지운 글자의 처리 — DROP 은 빼고, KEEP 은 표지 없이, MARK 는 `[DEL]…[/DEL]` 로 감싸
    넣는다(`paragraph_text` 와 같은 값).
    수식 run 안 줄바꿈(`w:br`)은 `\\n` 으로 남긴다. Word 는 수식 문단(`m:oMathPara`) 안 수식(`m:oMath`)마다 끝 run
    에 줄바꿈을 두어 줄을 나눈다 — 줄바꿈 없이 이웃한 수식은 하나로 합쳐 그린다(MS-OI29500 Part 1 §22.1.2.77 a).
    """
    return _linear(elem, deleted).strip()


def _linear(elem, deleted: str) -> str:
    """`math_linear` 의 글 — 양끝을 벗기지 않는다. 끝 줄바꿈은 다음 수식과 줄을 나누는 자리이고, 양끝 공백은
    수식 안에 적힌 둘레 글과의 띄어쓰기다(38.201 ` where` 뒤 수식 ` q=⌊a/N⌋`)."""
    text = _lin(elem, deleted).translate(_INVISIBLE)
    if _DEL_ON not in text:
        return _OPEN_GAP.sub(" ", text).replace(_OPEN, "")
    return _del_marked(text)


def _del_marked(text: str) -> str:
    """지운 자리 표지(`_DEL_ON` · `_DEL_OFF`)가 든 선형 글을 `[DEL]…[/DEL]` 글로. 표지가 겹치거나 맞닿은 지운 자리는
    한 자리로 합치고, 표지 안에 글자가 없는 자리(보이지 않는 연산자만 지운 자리)는 남기지 않는다.

    `_OPEN` 의 빈칸은 두 읽기를 함께 맞춘다 — 표지를 빼면 KEEP 글(다음 글자가 낱말 글자일 때 빈칸), 지운 자리를
    빼면 DROP 글(지우지 않은 `_OPEN` 이고 다음 남은 글자가 낱말 글자일 때 빈칸). KEEP 에만 있는 빈칸은 지운 자리에
    든다. 지우지 않은 글자는 표지 안에 들지 않는다."""
    chars: list[tuple[str, bool]] = []
    depth = 0
    for ch in text:
        if ch == _DEL_ON:
            depth += 1
        elif ch == _DEL_OFF:
            depth -= 1
        else:
            chars.append((ch, depth > 0))
    out: list[str] = []
    inside = False
    for i, (ch, gone) in enumerate(chars):
        if ch == _OPEN:
            if not _WORD.match(chars[i + 1][0] if i + 1 < len(chars) else ""):
                continue
            kept_next = next((c for c, g in chars[i + 1:] if not g), "")
            ch, gone = " ", gone or not _WORD.match(kept_next)
        if gone != inside:
            out.append("[DEL]" if gone else "[/DEL]")
            inside = gone
        out.append(ch)
    if inside:
        out.append("[/DEL]")
    return "".join(out)


def _drop_deleted(node) -> None:
    """`node` 아래 변경 표시로 빠진 자리(`w:del` · `w:moveFrom`)를 지운다."""
    for child in list(node):
        if child.tag in _DELETED:
            node.remove(child)
        else:
            _drop_deleted(child)


def _unwrap_inserted(node) -> None:
    """`node` 아래 변경 표시로 넣은 자리(`w:ins` · `w:moveTo`)를 풀어 그 자식을 제자리에 둔다."""
    for child in list(node):
        _unwrap_inserted(child)
        if child.tag in _INSERTED:
            at = list(node).index(child)
            for offset, grand in enumerate(list(child)):
                node.insert(at + offset, grand)
            node.remove(child)


def drawn_math(elem):
    """수식 요소의 복사본. 변경 표시로 빠진 자리를 지우고 넣은 자리는 풀며, `m:t` 글을 `math_text` 와 같이 그려지는 글자로 바꿔 적는다.

    주의: 수식 run 안의 `w:ins`(`<m:r><w:ins><m:t>…`)는 Pandoc 이 읽지 않아 그 수식이 빈 LaTeX 가 된다
    (RAN1#118 표 칸 `2∙N`). `math_text` 는 넣은 글을 읽으므로 같은 글이 Pandoc 에도 보이도록 푼다.
    """
    out = copy.deepcopy(elem)
    _drop_deleted(out)
    _unwrap_inserted(out)
    for t, read in list(_math_pieces(out)):
        if t.text and read:
            t.text = read(t.text)
    return out


_FLD_CHAR = _w("fldChar")
_FLD_TYPE = _w("fldCharType")
_INSTR_TEXT = _w("instrText")
#: 필드 명령 자리에서 숨는 것 — 문단 글을 내는 요소. 명령문(`w:instrText`)은 `_SKIP` 이 이미 뺀다.
_SHOWN_LEAF = {_T, _DEL_TEXT, _SYM, _TAB, _PTAB, _BR, _CR, _NB_HYPHEN}


def _one_picture(elem) -> bool:
    """그려지는 것 하나가 그림 한 장(수식 개체 하나 또는 그림 하나)인가 — 글상자 · 묶음 그림이 아닌 것."""
    if elem.tag == f"{{{MC_NS}}}AlternateContent":
        pick = elem.find(_MC_CHOICE)
        elem = pick if pick is not None else elem.find(_MC_FALLBACK)
        if elem is None:
            return False
    boxes: list = []
    oles: list[bool] = []
    images: list[str] = []
    if _drawn_parts(elem, boxes, oles, images) or boxes:
        return False
    if oles:
        return len(oles) == 1 and oles[0]
    return len(images) == 1


def _field_view(p) -> "tuple[set, dict]":
    """문단 안 필드가 화면에 내지 않는 요소와, 수식 그림 → 그 그림을 대신 읽을 필드 명령 수식.

    Word 는 필드의 명령 자리(`begin` 에서 `separate` 까지, `separate` 가 없으면 `end` 까지)를 그리지 않고 결과
    자리만 그린다. 명령 자리에 든 수식 · 글 · 그림은 숨는 것이다 — 필드 안 필드(명령 자리에 든 필드)의 결과도 그렇다.

    수식을 담은 `QUOTE` 필드는 .doc 호환 꼴이다. .doc 은 Office 수식(OMML)을 담지 못해 수식을 그림(수식 개체 ·
    그림)으로 그리고 고칠 수 있는 수식을 `QUOTE` 명령 자리에 둔다. 그 그림은 결과 자리에 들거나, 결과 자리가 비고
    필드 바로 앞이나 뒤에 놓인다(공백 글만 사이에 둔다). 그 그림 한 장이 정해지면 그림 자리에서 명령 수식을 읽는다
    — 같은 수식이고 LaTeX · 선형 표기로 읽을 수 있다. 다음이면 짝을 짓지 않고 그림만 그대로 둔다.

    - 결과 자리가 비고 앞뒤가 모두 그림이다(어느 쪽이 그 수식인지 문서가 말하지 않는다).
    - 한 그림을 두 필드가 짝으로 고른다.
    - 그림이 한 장이 아니다(글상자 · 묶음 그림 · 수식 아닌 OLE 개체).

    결과 자리에 글이나 보이는 수식이 있거나, 바로 앞 · 뒤가 글 · 보이는 수식이면 명령 수식은 숨기기만 한다 —
    고친 뒤 결과를 다시 계산하지 않아 명령 수식과 보이는 수식이 다른 문서가 있다.

    주의: `separate` 가 없는 필드는 결과가 없어 Word 가 아무것도 그리지 않는다. 그 명령 자리에 든 그림(`QUOTE`
    뒤 그림)은 화면에 없는 사본이고, 보이는 꼴은 필드 앞 · 뒤에 따로 있다 — 수식 개체 · OMML 수식 · 글 `N2` ·
    `n+m` 처럼(RAN1 · RAN4 회의록과 TS · TR 의 이 꼴 113곳에서 앞뒤가 모두 빈 자리는 없었고, 원문으로 본 자리는 이웃이
    같은 수식이었다). 보이는 꼴이 없는 자리도 있다 — R2-1712871 의 `monitor { QUOTE M≥1 } multiple BPLs` 는 이웃이
    글이라 화면에는 `monitor multiple BPLs` 만 그려진다.
    어느 쪽이든 화면에 없는 사본이므로 숨긴다.

    주의: 상태는 문단마다 새로 연다. 결과 자리가 여러 문단에 걸친 필드(목차 따위)의 뒷 문단은 `begin` 을 보지
    않으므로 그대로 읽힌다. 짝은 같은 문단 안에서만 찾는다.
    """
    hide: set = set()
    if next(p.iter(_FLD_CHAR), None) is None:
        return hide, {}
    stack: list[dict] = []       # 열린 필드 — instr: 명령 자리인가, quiet: 명령 자리 안에서 열린 필드인가
    fields: list[dict] = []      # 닫힌 QUOTE 수식 필드
    tokens: list = []            # 보이는 토큰 (종류, 요소) — 'P' 그림 · 'T' 글 · 'M' 수식 · 'F' 닫힌 필드
    waiting: list[dict] = []     # 결과 자리가 비어 뒤 토큰을 기다리는 필드
    skip: set = set()

    def visible(kind: str, elem) -> None:
        tokens.append((kind, elem))
        if stack:
            stack[-1]["shown"].append((kind, elem))
        while waiting:
            waiting.pop()["after"] = (kind, elem)

    def instr_field():
        for f in reversed(stack):
            if f["instr"]:
                return f
        return None

    for el in p.iter():
        if el in skip:
            continue
        tag = el.tag
        if not isinstance(tag, str):
            continue
        owner = instr_field()
        if tag == _FLD_CHAR:
            kind = el.get(_FLD_TYPE)
            if kind == "begin":
                stack.append({"instr": True, "quiet": owner is not None, "words": [], "maths": [], "shown": [],
                              "before": tokens[-1] if tokens else None, "after": None})
            elif kind == "separate" and stack:
                stack[-1]["instr"] = False
            elif kind == "end" and stack:
                fld = stack.pop()
                if not fld["quiet"]:
                    visible("F", None)
                    if fld["maths"] and "".join(fld["words"]).split()[:1] == ["QUOTE"]:
                        fields.append(fld)
                        if not fld["shown"]:
                            waiting.append(fld)
            continue
        if tag in _MATH or tag in _DRAWN_ANY:
            skip.update(el.iter())
            if owner is None:
                visible("M" if tag in _MATH else "P", el)
                continue
            hide.add(el)
            if tag in _MATH and not owner["quiet"]:
                owner["maths"].append(el)
            continue
        if tag == _INSTR_TEXT:
            if owner is not None and not owner["quiet"]:
                owner["words"].append(el.text or "")
            continue
        if tag in _SHOWN_LEAF:
            if owner is not None:
                hide.add(el)
            elif tag in (_T, _SYM, _NB_HYPHEN) and (tag != _T or (el.text or "").strip()):
                visible("T", el)

    claims: dict = {}
    for fld in fields:
        if fld["shown"]:
            pick = fld["shown"][0] if len(fld["shown"]) == 1 else None
        else:
            sides = [t for t in (fld["before"], fld["after"]) if t is not None and t[0] == "P"]
            pick = sides[0] if len(sides) == 1 else None
        if pick is not None and pick[0] == "P" and _one_picture(pick[1]):
            claims.setdefault(pick[1], []).append(fld)
    swap = {pic: flds[0]["maths"] for pic, flds in claims.items() if len(flds) == 1}
    return hide, swap


def paragraph_text(p, *, deleted: str = DROP, math: "bool | str | Callable[[object], str]" = True,
                   drawn: "Callable[[object], str] | None" = None, equation_objects: "bool | None" = None,
                   _script_tokens: bool = False) -> str:
    """문단 글. `deleted` 는 변경 표시로 빠진 글의 처리, `math` 는 수식 자리에 넣을 글.

    `math` 가 참이면 수식 글(`math_text`), 거짓이면 아무것도 넣지 않는다. 함수를 주면 수식(`m:oMath`)마다
    불러 돌려준 글을 넣는다 — `m:oMathPara` 는 안의 `m:oMath` 마다 한 번씩 부른다. 회의록 파서가
    수식 자리를 `[EQUATION]` 표지나 LaTeX 로 바꾸는 자리다. 글을 읽는 순서와 부르는 순서가 같으므로
    수식 목록을 모을 때도 같은 함수를 쓴다.
    `math` 가 `LINEAR` 이면 수식마다 선형 표기(`math_linear`)를 넣는다. 수식 run 안 줄바꿈은 `\\n` 으로 남아 수식
    문단(`m:oMathPara`) 안 수식이 줄마다 나뉜다. 지운 변경 표시 안 수식은 KEEP 으로 읽는다 — MARK 이면 바깥
    `[DEL]…[/DEL]` 이 이미 감싼다. 수식과 둘레 글의 낱말 글자가 맞닿으면 한 칸 띄운다(`_EDGE_GAP`).
    함수는 그리는 것이 있는 수식(`math_text` 가 빈 글이 아닌 것)에만 부른다 — 빈 수식(`<m:oMath/>`, 줄바꿈 ·
    공백만 든 것)과, `deleted` 가 DROP 일 때 글자 · 짜임이 모두 지워진 수식은 부르지 않는다.
    `deleted` 가 DROP 이면 수식 안에서 지운 글자 · 짜임 기호도 빼고, KEEP · MARK 이면 표지 없이 넣는다.
    `math` 가 `LINEAR` 이면 수식 개체(`w:object`)와 수식 그림 단위(`w:drawing` · `w:pict`)에 단 읽은 글
    (`EQUATION_TEXT`)도 수식처럼 넣는다 — 지운 변경 표시 안 개체는 수식과 같이 다룬다. `mc:AlternateContent` 안의
    것은 넣지 않는다(두 벌 가운데 어느 쪽을 읽을지 고르는 것은 `drawn` 의 몫이다).
    `drawn` 을 주면 그려지는 것(`w:drawing` · `w:pict` · `w:object` · `mc:AlternateContent`)마다 불러 돌려준
    글을 넣는다(`drawn_marker`) — 수식 개체 자리도 `drawn` 이 읽는다. 주지 않으면 그 자리는 읽지 않는다(위
    `LINEAR` 의 수식 개체만 빼고).
    양끝 공백은 벗긴다. 탭은 `\\t`, 줄바꿈(`w:br` · `w:cr`)은 `\\n` 으로 남긴다.
    필드는 Word 가 그리는 결과 자리만 읽는다 — 명령 자리에 든 수식 · 글 · 그림은 읽지 않고, .doc 호환 꼴의 수식
    그림은 짝지은 `QUOTE` 명령 수식으로 읽는다(`_field_view`). 단 그 그림이 글을 단 수식 개체(`EQUATION_TEXT`)이고
    이 읽기가 수식 개체를 직접 읽으면(`equation_objects`) 개체 자리로 읽는다. `equation_objects` 를 주지 않으면
    `math` 가 `LINEAR`(개체 글을 넣는다)이거나 `drawn` 을 준(개체를 받는다) 읽기를 개체를 읽는 읽기로 본다.
    """
    out: list[str] = []
    hide, swap = _field_view(p)
    if equation_objects is None:
        equation_objects = math == LINEAR or drawn is not None
    if swap and equation_objects:
        # 개체를 읽는 읽기에서는 그려진 수식 개체(글 `EQUATION_TEXT` 를 단 것)가 명령 수식보다 앞선다 — 화면에
        # 그려지는 원본이고, 명령 수식은 그 사본이라 글자가 빠지거나 바뀐 문서가 있다(RAN1#92 회의록의
        # `O_P=N_max−N_reported` 개체 옆 명령 수식은 `=N_max-N_reported`). 개체 글이 없으면 명령 수식으로 읽는다.
        # 수식 자리 목록(`paragraph_equations` · 기고문 파서의 수식 자리)도 같은 기본값으로 세어 청크 글과 맞는다.
        # 주의: 앞서는 것은 수식 개체만이다. 그림을 읽은 글(수식 그림 단위)은 미리보기를 글자 모양으로 읽은 것이라
        # 명령 수식보다 덜 정확해, 그림 자리는 명령 수식으로 읽는다.
        swap = {pic: eqs for pic, eqs in swap.items()
                if not any(o.get(EQUATION_TEXT) for o in ([pic] if pic.tag == _OBJECT else pic.iter(_OBJECT)))}

    def emit_math(elem, in_del: bool) -> None:
        if not math or (in_del and deleted == DROP):
            return
        if math == LINEAR:
            for eq in ([elem] if elem.tag == _OMATH else [m for m in elem if m.tag == _OMATH]):
                shown = _linear(eq, KEEP if in_del else deleted)
                if shown.strip():
                    out.append(_EDGE_IN + shown + _EDGE_OUT)
            return
        if callable(math):
            eqs = [elem] if elem.tag == _OMATH else [m for m in elem if m.tag == _OMATH]
            out.extend(math(eq) for eq in eqs if math_text(eq, deleted != DROP))
            return
        inline = math_text(elem, deleted != DROP)
        if inline:
            out.append(inline)

    def emit_drawn(elem, in_del: bool) -> None:
        if in_del and deleted == DROP:
            return
        shown = drawn(elem)
        if shown:
            out.append(shown)

    def emit_object(elem, in_del: bool) -> None:
        if in_del and deleted == DROP:
            return
        shown = elem.get(EQUATION_TEXT)
        if shown:
            out.append(_EDGE_IN + shown + _EDGE_OUT)

    def walk(node, in_del: bool) -> None:
        for child in node:
            if hide and child in hide:
                continue
            if swap and child in swap:
                for eq in swap[child]:
                    emit_math(eq, in_del)
                continue
            tag = child.tag
            if tag in _SKIP:
                if drawn is not None and tag in _DRAWN_ANY:
                    emit_drawn(child, in_del)
                elif tag in _EQUATION_HOLDERS and math == LINEAR:
                    emit_object(child, in_del)
                continue
            if tag in _MATH:
                emit_math(child, in_del)
                continue
            if tag in _DELETED:
                if deleted == DROP:
                    continue
                if deleted == MARK and not in_del:
                    start = len(out)
                    walk(child, True)
                    if "".join(out[start:]):
                        out.insert(start, "[DEL]")
                        out.append("[/DEL]")
                    else:
                        del out[start:]
                else:
                    walk(child, True)
                continue
            if tag == _R:
                run(child, in_del)
                continue
            if tag in _INSERTED or tag in _WRAPPERS:
                walk(child, in_del)

    def run(r, in_del: bool) -> None:
        read = False  # 기호 글꼴 글자 읽기 — 글 조각을 처음 만날 때 run 마다 한 번 찾는다
        role = None
        if _script_tokens:
            va = r.find(f"{_w('rPr')}/{_w('vertAlign')}")
            role = _SCRIPT_TOKENS.get(va.get(_w("val"))) if va is not None else None

        def emit_text(shown: str) -> None:
            # 기호 글꼴을 해석한 다음 표지한다. XML 글에 ASCII 태그를 먼저 넣으면 Symbol 글꼴이
            # <sup> 자체를 <συπ> 로 바꾼다. 이 내부 표지는 search_text 만 소비한다.
            out.append(role[0] + shown + role[1] if role and shown else shown)

        for sub in r:
            if hide and sub in hide:
                continue
            if swap and sub in swap:
                for eq in swap[sub]:
                    emit_math(eq, in_del)
                continue
            tag = sub.tag
            if tag == _T or tag == _DEL_TEXT:
                if sub.text:
                    if read is False:
                        read = symbol_fonts.run_reader(r)
                    emit_text(read(sub.text) if read else sub.text)
            elif tag == _SYM:
                emit_text(symbol_fonts.sym_text(sub))
            elif tag == _TAB or tag == _PTAB:
                out.append("\t")
            elif tag == _BR or tag == _CR:
                out.append("\n")
            elif tag == _NB_HYPHEN:
                emit_text("-")
            elif tag in _MATH:
                emit_math(sub, in_del)
            elif drawn is not None and tag in _DRAWN_ANY:
                emit_drawn(sub, in_del)
            elif tag in _EQUATION_HOLDERS and math == LINEAR:
                emit_object(sub, in_del)

    walk(p, False)
    text = "".join(out)
    # 경계 표지는 LINEAR 수식만이 아니라 `drawn` 이 넣은 수식 개체 글(`marked_text(objects=True)`)에도 붙는다.
    # XML 글에는 이 두 제어 글자가 올 수 없으므로 표지가 있으면 언제나 풀어 준다.
    if _EDGE_IN in text or _EDGE_OUT in text:
        if deleted == MARK and "[DEL]" in text:
            text = _EDGE_GAP_MARKED.sub(_edge_gap_marked, text)
        text = _EDGE_GAP.sub(" ", text).replace(_EDGE_IN, "").replace(_EDGE_OUT, "")
    return text.strip()


def final_text(p) -> str:
    """문단의 확정 글 — 바뀐 뒤의 글만 읽고 수식은 뺀다.

    TS · TR 파서가 제목 판정 · 캡션에 쓰는 규칙이다. 수식은 뺀다 — 청크 본문은 수식 자리에 선형 표기를 넣는
    `chunk_text` 로 읽는다.
    CR 표지 · 회의 보고서 · 기고문처럼 변경 표시가 있어도 바뀐 뒤의 글이 문서의 뜻인 자리도 이것을 쓴다.
    python-docx `Paragraph` 도 받는다(`Paragraph.text` 는 직계 `w:r` · `w:hyperlink` 만 읽어
    변경 표시 · `w:smartTag` · `w:sdt` · `w:fldSimple` 안의 글을 잃는다).
    """
    return paragraph_text(getattr(p, "_p", p), deleted=DROP, math=False)


def chunk_text(p, deleted: str = DROP) -> str:
    """청크 본문 글 — `final_text` 와 같이 읽되 수식 자리에 선형 표기(`math_linear`)를, 수식 개체 · 수식 그림 자리에
    읽은 글(`EQUATION_TEXT`)을 넣는다. 개체 · 그림 글은 `open_document` · `zip_part` 로 연 트리에만 달려 있다.

    TS · TR · CR · 기고문 청크 파서가 본문 · 표 칸 문단을 읽는 규칙이다. `deleted` 는 `paragraph_text` 와 같은 값 —
    TS · TR · 기고문은 DROP, CR 변경 본문은 MARK. python-docx `Paragraph` 도 받는다.

    주의: 일반 그림의 자리 표지(`[FIGURE]`)는 넣지 않는다. 수식 개체 · 수식 그림에서
    읽은 글만 넣으며, 그림 자리 표지는 `drawn_marker` 를 부르는 판독기에만 있다.
    """
    return paragraph_text(getattr(p, "_p", p), deleted=deleted, math=LINEAR)


# XML 1.0 본문에 들어올 수 없는 내부 표지. 수식 경계(02/03)·삭제(04/05)와 겹치지 않고,
# str.strip 이 공백으로 지우는 0B/0C/1C~1F 도 쓰지 않는다. 기본 판독에는 들어가지 않는다.
_SCRIPT_TOKENS = {"superscript": ("\x06", "\x07"), "subscript": ("\x08", "\x0e")}
_SCRIPT_OPEN = {"\x06": "sup", "\x08": "sub"}
_SCRIPT_CLOSE = {"\x07": "sup", "\x0e": "sub"}


def search_text(p, deleted: str = DROP) -> str:
    """검색 본문에서 일반 Word run 의 명시적 위·아래첨자를 <sup>/<sub> 로 구별한다.

    원문 인용용 final_text 와 기본 chunk_text 는 그대로다. 수식·기호 글꼴·변경 표시는
    chunk_text 의 글을 바탕으로 하고, 일반 run 의 w:rPr/w:vertAlign 만 역할로 덧붙인다.
    footnote / 지수 같은 의미를 모양만으로 추정하지 않는다. 상속 스타일과 w:position 은
    이 계약의 대상이 아니다. 첨자 태그를 빼면 기본 본문의 모든 글자·공백이 그대로 남는다.

    수식 경계에서 생성되는 공백은 기존 판독으로 확정한 뒤 역할을 입힌다. 내부 표지로 인한
    공백 차이를 따라가지 않으며, 비공백 문자 순서가 기본 판독과 다르면 오류로 중단한다.
    원본 XML 을 변경하지 않는다. python-docx Paragraph 도 받는다.
    """
    p = getattr(p, "_p", p)
    baseline = paragraph_text(p, deleted=deleted, math=LINEAR)
    if not any(v.get(_w("val")) in _SCRIPT_TOKENS for v in p.iter(_w("vertAlign"))):
        return baseline
    marked = paragraph_text(p, deleted=deleted, math=LINEAR, _script_tokens=True)
    symbols, roles = [], []
    active = None
    for ch in marked:
        if ch in _SCRIPT_OPEN:
            if active is not None:
                raise ValueError("nested search script annotation")
            active = _SCRIPT_OPEN[ch]
        elif ch in _SCRIPT_CLOSE:
            if active != _SCRIPT_CLOSE[ch]:
                raise ValueError("unbalanced search script annotation")
            active = None
        elif not ch.isspace():
            symbols.append(ch)
            roles.append(active)
    if active is not None or "".join(symbols) != "".join(c for c in baseline if not c.isspace()):
        raise ValueError("search script annotation changed source character sequence")
    at = 0
    character_roles = []
    for ch in baseline:
        if ch.isspace():
            character_roles.append(None)
        else:
            character_roles.append(roles[at])
            at += 1
    # 둘 다 같은 첨자인 글자 사이 공백만 같은 역할로 둔다. run 경계의 원래 공백 수는 보존한다.
    following = None
    next_roles = [None] * len(baseline)
    for i in range(len(baseline) - 1, -1, -1):
        next_roles[i] = following
        if not baseline[i].isspace():
            following = character_roles[i]
    previous = None
    for i, ch in enumerate(baseline):
        if ch.isspace():
            character_roles[i] = previous if previous == next_roles[i] else None
        else:
            previous = character_roles[i]
    out = []
    active = None
    for ch, role in zip(baseline, character_roles):
        if active != role:
            if active:
                out.append(f"</{active}>")
            if role:
                out.append(f"<{role}>")
            active = role
        out.append(ch)
    if active:
        out.append(f"</{active}>")
    return "".join(out)


#: 글 밖에 화면에 그려지는 것 — 그림 · 개체 · VML 도형. 지운 변경 표시 안의 것은 그려지지 않는다.
_DRAWN = (_w("drawing"), _w("pict"), _w("object"))


def blank_line(p) -> bool:
    """문단이 화면에 아무것도 그리지 않는 빈 줄인가.

    글(수식 포함)이 있거나, 그림 · 개체를 담았거나, `doc_fields` 가 필드 오류 글을 지운 문단(원본 화면에는 오류
    글이 보이던 줄 — `doc_fields.ERROR_LINE` 표지)은 빈 줄이 아니다. `final_text` 는 수식을 빼므로 수식만 있는
    문단도 빈 글로 읽힌다 — 빈 문단을 경계로 쓰는 판독기(회의 보고서 결정 본문의 끝)는 이것으로 가른다.
    python-docx `Paragraph` 도 받는다.
    """
    el = getattr(p, "_p", p)
    if el.get(doc_fields.ERROR_LINE) is not None or paragraph_text(el, deleted=DROP, math=True):
        return False
    for d in el.iter(*_DRAWN):
        a = d.getparent()
        while a is not el and a.tag not in _DELETED:
            a = a.getparent()
        if a is el:
            return False
    return True


def _iter_wrapped(container, wanted: str):
    for child in container:
        if child.tag == wanted:
            yield child
        elif child.tag in _BLOCK_WRAPPERS:
            yield from _iter_wrapped(child, wanted)


def iter_blocks(container):
    """본문 · 표 칸의 블록(`w:p` · `w:tbl`)을 문서 순서로. 블록 `w:sdt` · `w:customXml` 안으로 들어간다.

    python-docx 요소도 ElementTree 요소도 받는다.
    """
    for child in container:
        if child.tag == _P or child.tag == _TBL:
            yield child
        elif child.tag in _BLOCK_WRAPPERS:
            yield from iter_blocks(child)


def body_paragraphs(doc) -> list:
    """본문 문단 전부를 문서 순서로 python-docx `Paragraph` 로 — 블록 `w:sdt` · `w:customXml` 안 문단 포함.

    `Document.paragraphs` 는 본문 직계 `w:p` 만 돌려준다. 회의록 파서는 절 · 결정 · 역할의 범위를
    이 목록의 번호로 잡으므로 목차 · 절 · 결정 · 역할 · 수식이 모두 같은 목록을 써야 번호가 맞는다.
    """
    from docx.text.paragraph import Paragraph

    return [Paragraph(b, doc._body) for b in iter_blocks(doc.element.body) if b.tag == _P]


def body_blocks(doc):
    """본문 블록을 문서 순서로 — 문단은 python-docx `Paragraph`, 표는 `Table` 로. 블록 `w:sdt` · `w:customXml`
    안으로 들어간다(`body_paragraphs` 와 같은 문단 목록에 표가 제자리에 끼인 것).

    표 안 문단은 따로 나오지 않는다 — 칸 글은 `table_rows` 로 읽는다.
    """
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    for b in iter_blocks(doc.element.body):
        yield Paragraph(b, doc._body) if b.tag == _P else Table(b, doc._body)


def is_table(block) -> bool:
    """`body_blocks` 가 돌려준 블록이 표인가. python-docx 개체도 요소도 받는다."""
    return getattr(block, "_element", block).tag == _TBL


def _num_pr(ppr) -> tuple:
    """`w:pPr` 의 번호 매김 칸 (numId, ilvl) — 없는 칸은 None."""
    n = ppr.find(_w("numPr")) if ppr is not None else None
    if n is None:
        return None, None
    ni, il = n.find(_w("numId")), n.find(_w("ilvl"))
    return (ni.get(_w("val")) if ni is not None else None), (il.get(_w("val")) if il is not None else None)


def list_keys(paragraphs) -> list:
    """python-docx `Paragraph` 마다 든 번호 매김 목록 자리 `numId.ilvl`(목록 밖이면 None)을 같은 차례로.

    numId 와 ilvl 은 칸마다 따로 정한다. 문단의 `w:pPr/w:numPr` 이 먼저이고, 빈 칸은 문단 스타일(`w:pStyle` 이
    없으면 기본 문단 스타일)과 그 `w:basedOn` 사슬에서 가까운 것부터 채운다 — 제목 스타일이 ilvl 만 적고 numId 는
    바탕 스타일에서 받는 꼴(`Heading 4` 가 ilvl 3 을, numId 는 바탕의 `Heading 3` 에서)이 있다. 스타일 표에 없는
    스타일은 아무 칸도 주지 않는다. numId 0 은 목록 밖이고, ilvl 이 끝내 없으면 0 이다. 같은 목록의 항목은 numId 가
    같고, 깊은 수준일수록 ilvl 이 크다.
    """
    if not paragraphs:
        return []
    styles, default = {}, None
    for s in paragraphs[0].part.styles.element.findall(_w("style")):
        if s.get(_w("type")) != "paragraph":
            continue
        sid = s.get(_w("styleId"))
        b = s.find(_w("basedOn"))
        styles[sid] = (_num_pr(s.find(_w("pPr"))), b.get(_w("val")) if b is not None else None)
        if s.get(_w("default")) in ("1", "true", "on"):
            default = sid
    out = []
    for p in paragraphs:
        ppr = p._p.find(_w("pPr"))
        v, lv = _num_pr(ppr)
        ps = ppr.find(_w("pStyle")) if ppr is not None else None
        sid = ps.get(_w("val")) if ps is not None else default
        seen = set()
        while (v is None or lv is None) and sid in styles and sid not in seen:
            seen.add(sid)
            (sv, sl), sid = styles[sid]
            v = sv if v is None else v
            lv = sl if lv is None else lv
        out.append(None if v in (None, "0") else f"{v}.{lv or 0}")
    return out


def iter_tables(doc):
    """문서의 모든 표를 문서 순서로 python-docx `Table` 로 — 블록 `w:sdt` 안 표와 칸 안에 든 표까지.

    바깥 표가 먼저 나오고 그 칸 안의 표가 뒤따른다. `Document.tables` 는 본문 직계 표만 돌려주므로
    CR 서식 전체를 한 칸짜리 겉 표에 담은 문서(RAN1 35 · RAN4 8)에서 서식 표를 찾지 못한다.
    """
    from docx.table import Table

    def walk(container):
        for block in iter_blocks(container):
            if block.tag != _TBL:
                continue
            yield Table(block, doc._body)
            for tr in _iter_wrapped(block, _TR):
                for tc in _iter_wrapped(tr, _TC):
                    yield from walk(tc)

    yield from walk(doc.element.body)


def table_line_rows(tbl, *, para: "Callable[[object], str] | None" = None, deleted: str = DROP) -> list[str]:
    """표를 행마다 `| 칸 | 칸 |` 한 줄로. 칸 안 줄바꿈은 빈칸으로 편다(`table_rows` 를 따른다)."""
    lines = []
    for row in table_rows(tbl, para=para, deleted=deleted):
        if row:
            lines.append("| " + " | ".join(" ".join(c.split("\n")) for c in row) + " |")
    return lines


def table_rows(tbl, *, para: "Callable[[object], str] | None" = None, deleted: str = DROP,
               nested: "Callable[[list[list[str]]], list[str]] | None" = None) -> list[list[str]]:
    """표의 행마다 칸 글(`cell_text`) 목록. `para` 는 칸 안 문단을 읽는 함수, `nested` 는 칸 안 표를 칸 글 줄로
    바꾸는 함수(둘 다 `cell_text` 를 따른다). 행 · 칸은 `table_grid` 에서 얻는다.

    `deleted` 는 행 지움 표시(`w:trPr/w:del`)가 있는 행의 처리 — `para` 와 같은 방식을 준다. DROP 이면 행을 빼고,
    MARK 이면 칸 글 전체를 `[DEL]…[/DEL]` 로 감싸며(칸 안 표지는 걷어 한 겹으로), KEEP 이면 그대로 읽는다.
    주의: 행을 지워도 칸 안 글 조각이 `w:del` 로 감싸이지 않는 행이 있다 — RAN2 CR 표본에서 한 행(45 낱말)이
    지운 행인데도 확정 글로 읽혔다. 글 조각이 모두 `w:del` 인 지운 행도 DROP 으로 읽으면 빈 칸만 남은 행이 된다.
    행 표시를 보지 않으면 두 경우 모두 지운 행이 표 글에 남는다.

    가로로 합친 칸(`w:gridSpan`)은 한 번만 나온다 — python-docx `Table.rows[i].cells` 는 격자
    칸마다 같은 칸을 되풀이한다. 세로로 합친 칸(`w:vMerge`)의 이어지는 칸은 비어 있으므로 합침을
    시작한 칸의 글을 받는다 — 행을 한 줄로 펼 때 그 행의 머리글이 빠지지 않게 한다. 위에 합침이 없는 이어지는
    칸(지운 행 뒤 등)은 제 글을 읽고 그 아래로 이어지는 칸에 넘긴다.
    주의: 받은 글은 행마다 되풀이되므로 표 글이 길어진다 — 표본 TS 표 글 낱말이 `w:tr` · `w:tc` 를 직접 돌던 읽기보다
    RAN4 5.6% · RAN5 4.9% 늘었다. 받지 않으면 둘째 행부터 머리글 없는 값만 남아 행 하나만으로는 무엇의 값인지
    읽을 수 없다.
    python-docx `Table` 도 받는다.
    """
    rows: list[list[str]] = []
    above: dict[int, str] = {}  # 격자 열 → 세로 합침을 시작한 칸의 글
    for gone, cells in table_grid(tbl, deleted=deleted):
        row: list[str] = []
        next_above: dict[int, str] = {}
        for c in cells:
            if c.vmerge == "continue" and c.col in above:
                text = above[c.col]
            else:
                text = cell_text(c.tc, para=para, deleted=deleted, nested=nested)
                if gone:
                    pass  # 지운 행의 글은 아래 남은 행에 넘기지 않는다 — DROP 으로 읽을 때와 같은 글이 되게
                elif c.vmerge:
                    next_above[c.col] = text
                else:
                    above.pop(c.col, None)
            if not gone and c.vmerge:
                next_above[c.col] = text
            if gone and deleted == MARK and text:
                text = "[DEL]" + text.replace("[DEL]", "").replace("[/DEL]", "") + "[/DEL]"
            row.append(text)
        if not gone:
            above = next_above
        rows.append(row)
    return rows


class GridCell(NamedTuple):
    """표 격자의 칸 하나(`table_grid`)."""
    tc: object   # `w:tc` 요소
    col: int     # 칸이 시작하는 격자 열 — 행 앞에 비운 열(`w:gridBefore`)을 센다
    span: int    # 가로로 차지하는 격자 칸 수(`w:gridSpan`)
    vmerge: str  # 세로 합침 — "" · "restart"(합침 시작) · "continue"(이어지는 칸, 글이 비어 있다)


def table_grid(tbl, *, deleted: str = DROP) -> list[tuple[bool, list[GridCell]]]:
    """표의 행마다 `(지운 행인가, 칸 목록)` — 블록 `w:sdt` · `w:customXml` 안의 행 · 칸까지 문서 순서로.

    `deleted` 가 DROP 이면 지운 행(`row_deleted`)을 뺀다. 칸 글을 스스로 짜는 파서(HTML 렌더링 등)도 행 · 칸은
    여기서 얻는다. 주의: 행 · 칸을 `findall(w:tr)` · `findall(w:tc)` 로 돌면 래퍼 안의 행 · 칸과 행 지움 표시를
    놓친다. python-docx `Table` 도 받는다.
    """
    tbl = getattr(tbl, "_tbl", tbl)
    grid: list[tuple[bool, list[GridCell]]] = []
    for tr in _iter_wrapped(tbl, _TR):
        gone = row_deleted(tr)
        if gone and deleted == DROP:
            continue
        cells: list[GridCell] = []
        col = _grid_before(tr)
        for tc in _iter_wrapped(tr, _TC):
            span, vmerge = _tc_merge(tc)
            cells.append(GridCell(tc, col, span, vmerge))
            col += span
        grid.append((gone, cells))
    return grid


def merged_rows(grid: list[tuple[bool, list[GridCell]]], r: int, col: int) -> int:
    """`table_grid` 의 r 번째 행 col 열에서 세로 합침을 시작한 칸이 차지하는 행 수(제 행 포함) — HTML `rowspan`."""
    n = 1
    for _gone, cells in grid[r + 1:]:
        if not any(c.col == col and c.vmerge == "continue" for c in cells):
            break
        n += 1
    return n


def shown_cells(grid: list[tuple[bool, list[GridCell]]]):
    """`table_grid` 의 칸 가운데 HTML 표에 내는 칸을 `(행 번호, 칸, rowspan)` 으로 문서 차례로.

    위 행에서 세로 합침이 이어지는 칸(`vmerge == "continue"`)은 합침을 시작한 칸의 `rowspan` 이 덮으므로 내지 않는다.
    위에 합침이 없는 이어지는 칸은 합침을 시작한 칸처럼 낸다(`table_rows` 와 같다) — 내지 않으면 그 행의 열이 하나
    모자라고 그 칸의 글이 빠진다.
    """
    merging: set[int] = set()  # 위 행에서 세로 합침이 이어지는 격자 열
    for r, (_gone, cells) in enumerate(grid):
        still: set[int] = set()
        for c in cells:
            if c.vmerge == "continue" and c.col in merging:
                still.add(c.col)
                continue
            rowspan = 1
            if c.vmerge:
                still.add(c.col)
                rowspan = merged_rows(grid, r, c.col)
            yield r, c, rowspan
        merging = still


def html_cells(grid: list[tuple[bool, list[GridCell]]]):
    """HTML 표의 `<td>` 를 `(행 번호, 칸 또는 None, colspan, rowspan)` 으로 문서 차례로 — `shown_cells` 의 칸 앞에
    비어 있는 격자 열(행 앞 `w:gridBefore`)이 있으면 그 자리에 빈 칸(None)을 먼저 낸다. 위 행의 `rowspan` 이 덮는
    열은 비어 있는 열로 세지 않는다.
    주의: `shown_cells` 의 칸만 내면 `w:gridBefore` 가 있는 행의 칸이 왼쪽으로 당겨져 위아래 행과 열이 어긋난다.
    """
    covered: dict[int, set[int]] = {}  # 행 → 위 행의 rowspan 이 덮는 격자 열
    row, at = -1, 0
    for r, c, rowspan in shown_cells(grid):
        if r != row:
            row, at = r, 0
        free = [k for k in range(at, c.col) if k not in covered.get(r, ())]
        start = 0
        for i in range(1, len(free) + 1):
            if i == len(free) or free[i] != free[i - 1] + 1:
                yield r, None, i - start, 1
                start = i
        yield r, c, c.span, rowspan
        for rr in range(r + 1, r + rowspan):
            covered.setdefault(rr, set()).update(range(c.col, c.col + c.span))
        at = max(at, c.col + c.span)


def row_deleted(tr) -> bool:
    """행 지움 표시(`w:trPr/w:del`)가 있는 행인가."""
    pr = tr.find(_TR_PR)
    return pr is not None and pr.find(_DEL) is not None


_TC_PR = _w("tcPr")
_TR_PR = _w("trPr")
_DEL = _w("del")
_GRID_SPAN = _w("gridSpan")
_GRID_BEFORE = _w("gridBefore")
_VMERGE = _w("vMerge")
_VAL = _w("val")


def _int_val(elem, default: int) -> int:
    try:
        return int(elem.get(_VAL))
    except (TypeError, ValueError):
        return default


def _grid_before(tr) -> int:
    pr = tr.find(_TR_PR)
    gb = pr.find(_GRID_BEFORE) if pr is not None else None
    return _int_val(gb, 0) if gb is not None else 0


def _tc_merge(tc) -> tuple[int, str]:
    """`(가로로 차지하는 격자 칸 수, 세로 합침: "" · "restart" · "continue")`."""
    pr = tc.find(_TC_PR)
    if pr is None:
        return 1, ""
    gs = pr.find(_GRID_SPAN)
    vm = pr.find(_VMERGE)
    vmerge = "" if vm is None else ("restart" if vm.get(_VAL) == "restart" else "continue")
    return (_int_val(gs, 1) if gs is not None else 1), vmerge


def cell_text(cell, *, para: "Callable[[object], str] | None" = None, deleted: str = DROP,
              nested: "Callable[[list[list[str]]], list[str]] | None" = None) -> str:
    """표 칸(`w:tc`)의 확정 글 — 칸 안 문단마다 `final_text`(`para` 를 주면 그 함수), 줄바꿈으로 잇는다.

    칸 안 표는 행마다 칸 글을 ` | ` 로 이은 줄로 넣는다(행 지움 표시는 `deleted` 로 `table_rows` 를 따른다).
    `nested` 를 주면 칸 안 표의 행 목록(`table_rows`)을 그 함수가 돌려준 줄로 넣는다.
    python-docx `_Cell` 도 받는다.
    `_Cell.text` 와 모양(`\n` 으로 잇기)은 같고 읽는 자리가 다르다 — CR 표지의 제목 · spec ·
    CR 번호 칸은 `w:fldSimple`(문서 속성 필드)로 채워져 있어 `_Cell.text` 로는 빈 칸이 되고,
    칸 안 표와 블록 `w:sdt` 안 문단은 `_Cell.text` 에 들어오지 않는다.
    """
    tc = getattr(cell, "_tc", cell)
    parts: list[str] = []
    for block in iter_blocks(tc):
        if block.tag == _P:
            parts.append((para or final_text)(block))
        else:
            rows = table_rows(block, para=para, deleted=deleted, nested=nested)
            parts.extend(nested(rows) if nested else (" | ".join(c for c in row if c) for row in rows))
    return "\n".join(parts).strip()


def iter_all_paragraphs(elem):
    """요소 아래 모든 문단(글상자 안 문단 포함)을 문서 순서로. `mc:Fallback` 대체본은 건너뛴다.

    글상자 안 문단은 바깥 문단의 글(`final_text`)에 들어가지 않으므로, 바깥 문단과 글상자
    문단을 함께 읽어도 같은 글이 두 번 나오지 않는다.
    """
    for child in elem:
        if child.tag == _MC_FALLBACK:
            continue
        if child.tag == _P:
            yield child
        yield from iter_all_paragraphs(child)


EQUATION = "[EQUATION]"
FIGURE = "[FIGURE]"
_A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
_V_NS = "urn:schemas-microsoft-com:vml"
_O_NS = "urn:schemas-microsoft-com:office:office"
_R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_TXBX_CONTENT = _w("txbxContent")
_OLE = f"{{{_O_NS}}}OLEObject"
_BLIP = f"{{{_A_NS}}}blip"
_IMAGEDATA = f"{{{_V_NS}}}imagedata"
#: 하나의 그림으로 그려지는 것 — 차트 · SmartArt · 그리기 캔버스 · 도형 묶음.
_WHOLE_FIGURE = {
    "{http://schemas.openxmlformats.org/drawingml/2006/chart}chart",
    "{http://schemas.openxmlformats.org/drawingml/2006/diagram}relIds",
    "{http://schemas.openxmlformats.org/drawingml/2006/lockedCanvas}lockedCanvas",
    "{http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas}wpc",
    "{http://schemas.microsoft.com/office/word/2010/wordprocessingGroup}wgp",
    f"{{{_V_NS}}}group",
}
#: MathType 이 그린 WMF · EMF 그림은 주석 레코드에 이 글을 남긴다.
_EQUATION_IMAGE_SIGNS = (b"MathType", b"Design Science")
_VECTOR_IMAGE = (".wmf", ".emf")


def equation_image_data(data: bytes) -> bool:
    """그림 바이트가 MathType 수식 그림인가 — 서명(`_EQUATION_IMAGE_SIGNS`)이 있고, 수식이 그림의 일부일 뿐인 합친 EMF
    (`metafile_text.composite`)가 아니다.
    주의: 서명만 보면 문서 조각(본문 · 표 · 도식)을 붙인 EMF 도 그 안에 MathType 수식이 있으면 수식 그림이 된다 — 서명 있는
    EMF 505개 가운데 350개가 그랬다(파서가 읽는 docx 전부로는 서명 있는 EMF 부품 708개 가운데 522개). 그 그림은 `[EQUATION]` 이 아니라 `[FIGURE]` 이고 그림 글을 수식으로 읽지 않는다.
    """
    return any(sign in data for sign in _EQUATION_IMAGE_SIGNS) and not metafile_text.composite(data)


def equation_images(source) -> "Callable[[str], bool]":
    """관계 id → 그 그림이 MathType 수식 그림인가(`drawn_marker` 의 `is_equation_image`).

    `source` 는 python-docx 문서 파트(`Paragraph.part` · `Document.part`) 또는 .docx 경로다. 본문 부품의
    관계 가운데 WMF · EMF 그림만 열어 MathType 수식 그림(`equation_image_data`)인지 본다. 회의 보고서 결정 본문
    안 그림에서 잰 바로는 WMF 그림은 모두 이 서명을 가졌고 PNG · GIF · JPEG 는 수식 편집기가 남긴 서명이 없다.
    """
    found: set[str] = set()
    rels = getattr(source, "rels", None)
    if rels is not None:
        for rid, rel in rels.items():
            if rel.is_external or not str(rel.reltype).endswith("/image"):
                continue
            part = rel.target_part
            if str(part.partname).lower().endswith(_VECTOR_IMAGE) and equation_image_data(part.blob):
                found.add(rid)
        return found.__contains__
    import posixpath
    import zipfile
    from urllib.parse import unquote
    from lxml import etree
    with zipfile.ZipFile(str(source)) as z:
        names = set(z.namelist())
        try:
            rels_xml = etree.fromstring(z.read("word/_rels/document.xml.rels"))
        except KeyError:
            return found.__contains__
        for rel in rels_xml:
            target = unquote(rel.get("Target") or "")
            if rel.get("TargetMode") == "External" or not (rel.get("Type") or "").endswith("/image"):
                continue
            name = posixpath.normpath(target.lstrip("/") if target.startswith("/") else posixpath.join("word", target))
            if name.lower().endswith(_VECTOR_IMAGE) and name in names:
                if equation_image_data(z.read(name)):
                    found.add(rel.get("Id"))
    return found.__contains__


def equation_ole(ole) -> bool:
    """OLE 개체(`o:OLEObject`)가 수식 편집기(3.0 · MathType) 개체인가 — ProgID 가 `Equation.` 으로 시작하거나,
    문서를 열 때 개체 부품을 보고 단 속성(`EQUATION_OBJECT`)이 있다. 주의: 변환을 거친 문서는 수식 개체의 ProgID 를
    비워 두거나 `Unknown` 으로 적는다(`ole_equation.annotate`). `open_document` · `zip_part` 로 열지 않은 트리에서는
    그런 개체를 알아보지 못한다."""
    return (ole.get("ProgID") or "").startswith("Equation.") or bool(ole.get(EQUATION_OBJECT))


def _drawn_parts(elem, boxes: list, oles: list, images: list) -> bool:
    """elem 아래(글상자 안은 빼고) 글상자 · OLE 개체가 수식인가(`equation_ole`) · 그림 관계 id 를 모은다. 하나의 그림
    꼴이 있으면 참."""
    whole = False
    for child in elem:
        tag = child.tag
        if not isinstance(tag, str):
            continue
        if tag == _TXBX_CONTENT:
            boxes.append(child)
            continue
        if tag in _WHOLE_FIGURE:
            whole = True
        elif tag == _OLE:
            oles.append(equation_ole(child))
        elif tag == _BLIP:
            images.append(child.get(f"{{{_R_NS}}}embed") or "")
        elif tag == _IMAGEDATA:
            images.append(child.get(f"{{{_R_NS}}}id") or "")
        whole = _drawn_parts(child, boxes, oles, images) or whole
    return whole


def drawn_marker(elem, *, text: "Callable[[object], str] | None" = None,
                 is_equation_image: "Callable[[str], bool] | None" = None) -> str:
    """그려지는 것 하나(`w:drawing` · `w:pict` · `w:object` · `mc:AlternateContent`)를 본문 글로 적는다.

    - `mc:AlternateContent` 는 `mc:Choice`(없으면 `mc:Fallback`) 한 벌만 읽는다 — 두 벌은 같은 것을 그린다.
    - OLE 개체: 수식 편집기 3.0 · MathType 개체(`equation_ole`)면 `[EQUATION]`, 그 밖(Visio · Excel …)은 `[FIGURE]`.
    - 차트 · SmartArt · 그리기 캔버스 · 도형 묶음: `[FIGURE]` 하나(안에 든 그림도 그 그림의 일부다).
    - 그림(`a:blip` · `v:imagedata`): `is_equation_image` 가 관계 id 를 수식 그림으로 판정하면 `[EQUATION]`,
      아니면 `[FIGURE]`. 그림마다 하나씩 빈칸으로 잇는다.
    - 글상자(`w:txbxContent`): 표지가 있어도 함께 적는다 — 글상자 글은 그림 위에 놓인 본문 글이다. 안 문단 ·
      표를 `text`(주지 않으면 `final_text`)로 읽고 앞뒤에 줄바꿈을 두어 둘레 글과 따로 놓인 덩이로 적는다.
      글상자 안 그림은 `text` 가 읽는다. 따로 놓인 글상자는 줄마다 줄바꿈으로 잇는다. 캔버스 · 도형 묶음 안
      글상자는 자리를 잡아 놓은 조각이라 문서 순서에 줄 차례가 없으므로(결정 본문에서 잰 두 캔버스는 글상자
      대부분이 기호 한두 자였다) 한 줄로 빈칸 이음한다.
    - 그 밖(글 없는 도형 · 선 · 빈 글상자): 빈 글. 보이는 글도 그림도 없다.
    """
    if elem.tag == f"{{{MC_NS}}}AlternateContent":
        pick = elem.find(_MC_CHOICE)
        if pick is None:
            pick = elem.find(_MC_FALLBACK)
        if pick is None:
            return ""
        elem = pick
    boxes: list = []
    oles: list[bool] = []
    images: list[str] = []
    whole = _drawn_parts(elem, boxes, oles, images)
    if oles:
        mark = EQUATION if oles[0] else FIGURE
    elif whole:
        mark = FIGURE
    else:
        mark = " ".join(EQUATION if is_equation_image is not None and is_equation_image(rid) else FIGURE
                        for rid in images)
    read = text or final_text
    lines: list[str] = []
    for box in boxes:
        for block in iter_blocks(box):
            if block.tag == _P:
                lines.append(read(block))
            else:
                lines.extend(table_line_rows(block, para=read))
    kept = [line.strip() if whole else line for line in lines if line.strip()]
    body = (" " if whole else "\n").join(kept)
    return f"{mark}\n{body}\n" if body else mark


def _box_lines(elem, read: "Callable[[object], str]") -> list[str]:
    """그려지는 것 하나 안 따로 놓인 글상자의 줄 — 안 문단 · 표를 `read` 로 읽는다. 그림 하나로 그려지는 것
    (차트 · SmartArt · 그리기 캔버스 · 도형 묶음) 안 글상자는 그 그림의 라벨이라 빈 목록이다."""
    if elem.tag == f"{{{MC_NS}}}AlternateContent":
        pick = elem.find(_MC_CHOICE)
        if pick is None:
            pick = elem.find(_MC_FALLBACK)
        if pick is None:
            return []
        elem = pick
    boxes: list = []
    if _drawn_parts(elem, boxes, [], []):
        return []
    lines: list[str] = []
    for box in boxes:
        for block in iter_blocks(box):
            if block.tag == _P:
                lines.append(read(block))
            else:
                lines.extend(table_line_rows(block, para=read))
    return [line for line in lines if line.strip()]


def box_text(p, *, read: "Callable[[object], str] | None" = None) -> str:
    """문단에 연결된 부동 텍스트 상자의 글 — 줄마다 줄바꿈으로 잇는다. 글상자가 없으면 빈 글.

    `final_text`는 그리기 요소 내부의 텍스트를 읽지 않아 글상자 글이 빠진다. 기고문은 규격 인용 · 제안을 글상자에 담기도 한다
    (R2-1712177 은 규격 절 하나 '5.7.5.3 Reflective QoS Control' 을 글상자에 옮겨 적었다).
    - 지운 변경 표시 안 글상자는 읽지 않는다(`final_text` 와 같은 확정본). `mc:AlternateContent` 는 한 벌만 읽는다.
    - 도형 묶음 · 그리기 캔버스 안 글상자는 그림 안 라벨이라 읽지 않는다(R2-1712207 의 'IP Packet' 처럼
      몇 글자짜리 조각이고 문서 순서에 줄 차례가 없다).
    - 글상자 안 문단은 `boxed_text` 로 읽어, 그 문단에 연결된 부동 텍스트 상자도 함께 읽는다. `read` 는 글상자 안 문단
      하나의 글을 읽는 함수다(기본 `final_text`, 청크 본문은 `chunk_text`).
    python-docx `Paragraph` 도 받는다.
    """
    p = getattr(p, "_p", p)
    if next(p.iter(_TXBX_CONTENT), None) is None:
        return ""
    lines: list[str] = []

    def drawn(d) -> str:
        lines.extend(_box_lines(d, lambda q: boxed_text(q, read=read)))
        return ""

    paragraph_text(p, deleted=DROP, math=False, drawn=drawn)
    return "\n".join(lines)


def boxed_text(p, *, read: "Callable[[object], str] | None" = None) -> str:
    """문단의 확정 글(`final_text`) 뒤에 그 문단에 연결된 부동 텍스트 상자의 글(`box_text`)을 줄을 바꿔 잇는다.

    기고문 표 칸 · 글상자 안 문단을 읽는 규칙이다. `read` 를 주면 문단 글과 글상자 안 문단을 그 함수로 읽는다
    (청크 본문은 `chunk_text`). python-docx `Paragraph` 도 받는다.
    """
    own, box = (read or final_text)(p), box_text(p, read=read)
    return f"{own}\n{box}" if own and box else (own or box)


def paragraph_equations(p) -> list:
    """문단이 보여 주는 수식(`m:oMath`)을 읽는 차례로 `(수식, 그 수식을 담은 문단)` 짝 목록으로.

    글을 읽는 자리(`boxed_text`)에 든 수식만 센다 — 지운 변경 표시 안 수식 · 글자와 짜임이 모두 지워진 수식 ·
    아무것도 그리지 않는 빈 수식은 빼고, `mc:AlternateContent` 는 한 벌만 보고, 따로 놓인 글상자 안 수식(안
    문단 · 표까지)은 넣고, 도형 묶음 · 그리기 캔버스 안 라벨의 수식은 뺀다. `m:oMathPara` 는 안의 `m:oMath`
    마다 하나다. 글상자 안 수식의 짝은 그 수식을 담은 글상자 안 문단이다.
    python-docx `Paragraph` 도 받는다.
    """
    p = getattr(p, "_p", p)
    found: list = []
    if next(p.iter(_OMATH), None) is None:
        return found

    def math(eq) -> str:
        found.append((eq, p))
        return ""

    def take(q) -> str:
        found.extend(paragraph_equations(q))
        return ""

    def drawn(d) -> str:
        _box_lines(d, take)
        return ""

    paragraph_text(p, deleted=DROP, math=math, drawn=drawn)
    return found


def table_equations(tbl) -> list:
    """표 칸이 보여 주는 수식을 칸 글을 읽는 차례(`table_rows`)대로 `(수식, 그 수식을 담은 문단)` 짝 목록으로.

    칸 안 문단마다 `paragraph_equations` 로 센다. 칸 안 표도 읽고, 세로로 합친 칸의 이어지는 칸은 `table_rows` 가
    읽지 않으므로 세지 않는다. python-docx `Table` 도 받는다.
    """
    tbl = getattr(tbl, "_tbl", tbl)
    found: list = []
    if next(tbl.iter(_OMATH), None) is None:
        return found

    def take(q) -> str:
        found.extend(paragraph_equations(q))
        return ""

    table_rows(tbl, para=take)
    return found


def _equation_texts(elem):
    if not isinstance(elem.tag, str) or elem.tag == _TXBX_CONTENT:
        return
    if elem.tag == f"{{{MC_NS}}}AlternateContent":
        pick = elem.find(_MC_CHOICE)
        if pick is None:
            pick = elem.find(_MC_FALLBACK)
        if pick is not None:
            yield from _equation_texts(pick)
        return
    shown = elem.get(EQUATION_TEXT) if elem.tag in _EQUATION_HOLDERS else None
    if shown:
        yield shown
        return
    for child in elem:
        yield from _equation_texts(child)


def drawn_equation_text(elem) -> str:
    """그려지는 것 하나(`drawn_marker` 가 받는 것)에 든 수식 개체 · 수식 그림 단위의 읽은 글(`EQUATION_TEXT`). 없으면
    빈 글이다.

    `mc:AlternateContent` 는 `drawn_marker` 와 같이 한 벌만 본다. 여럿이면 빈칸으로 잇는다. 글상자
    (`w:txbxContent`) 안의 것은 넣지 않는다 — 글상자는 `drawn_marker` 가 안 문단째 읽으므로, 여기서 글을 돌려주면
    글상자 글이 통째로 빠진다.
    """
    return " ".join(_equation_texts(elem))


def has_math(elem) -> bool:
    """요소(문단 · 표) 안에 수식이 있는가 — OMML 이나, 읽은 글(`EQUATION_TEXT`)을 단 수식 개체 · 수식 그림 단위.

    수식을 글로 싣는 읽기(`marked_text(objects=True)` 와 OMML 을 LaTeX · `math_text` 로 넣는 `math` 함수)가 표지
    `[EQUATION]` 대신 글을 넣을 자리가 있는지 미리 보는 데 쓴다. LaTeX 로 바꾸지 못한 OMML 도 `math_text` 로 실리므로
    든다. 지운 변경 표시 안의 수식도 세므로, 쓰는 쪽은 읽은 글이 표지 글과 같은지 다시 본다.
    python-docx `Paragraph` · `Table` 도, 표준 라이브러리 `xml.etree` 요소도 받는다(그 `iter` 는 태그 하나만 받는다)."""
    e = getattr(elem, "_element", elem)
    return any(x.tag in _MATH or (x.tag in _EQUATION_HOLDERS and x.get(EQUATION_TEXT)) for x in e.iter())


def marked_text(p, *, math: "Callable[[object], str] | None" = None,
                is_equation_image: "Callable[[str], bool] | None" = None, objects: bool = False) -> str:
    """문단의 확정 글에 수식 · 그림 자리를 표지로 남긴다 — 회의 보고서 결정 본문 · 표 칸을 읽는 규칙.

    수식(`m:oMath`)은 `math`(주지 않으면 `[EQUATION]`)가 돌려준 글, 그려지는 것은 `drawn_marker` 로 적는다.
    .doc 호환 꼴 필드의 수식 그림은 수식 개체여도 짝지은 `QUOTE` 명령 수식으로 읽는다(`equation_objects=False`) —
    `drawn_marker` 는 수식 개체를 `[EQUATION]` 으로만 적으므로 명령 수식이 LaTeX 를 얻는 유일한 자리다.
    > 주의: 명령 수식은 그려진 개체의 사본이라 드물게 글자가 다르다(RAN1#92 회의록 `O_P` 가 빠진 자리).
    > 수식 목록을 따로 모으는 판독기(회의 보고서 `equation_converter`)는 같은 차례를 얻도록 `math` 함수만 주고
    > `drawn` 을 주지 않는다 — 그러면 기본값이 이 읽기와 같다.
    글상자 안 문단도 같은 규칙으로 읽되 수식은 늘 `[EQUATION]` 이다 — `math` 가 본문 수식을 차례로 세는
    함수일 때(LaTeX 를 넣는 판독기) 글상자 안 수식이 그 차례를 밀지 않게 한다.
    `objects` 가 참이면 읽은 글을 단 수식 개체 · 수식 그림 단위(`EQUATION_TEXT`)는 `[EQUATION]` 대신 그 글을 넣는다 — 수식을 글로
    싣는 판독기(회의 보고서 `contentWithEquations`)의 읽기다. 짝지은 `QUOTE` 명령 수식으로 읽는 그림 자리는 그대로
    명령 수식이다(`math` 가 세는 차례가 `objects` 와 무관하게 같다).
    python-docx `Paragraph` 도 받는다.
    """
    def inner(q) -> str:
        return marked_text(q, is_equation_image=is_equation_image, objects=objects)

    def drawn(d) -> str:
        if objects:
            shown = drawn_equation_text(d)
            if shown:
                return _EDGE_IN + shown + _EDGE_OUT
        return drawn_marker(d, text=inner, is_equation_image=is_equation_image)

    return paragraph_text(getattr(p, "_p", p), deleted=DROP,
                          math=math if math is not None else (lambda _m: EQUATION), drawn=drawn,
                          equation_objects=False)
