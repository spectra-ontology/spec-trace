"""OOXML 문서를 여는 공통 함수와 Strict 이름공간 변환을 제공한다.

`python-docx`로 파일을 먼저 열고, 실패한 파일이 ISO/IEC 29500 Strict 형식인지
패키지 관계 파일(`_rels/.rels`)에서 확인한다. Strict 문서는 XML의 이름공간 선언과
관련 URI 속성을 Transitional URI로 변환한 메모리 사본으로 다시 연다. 본문 텍스트,
관계 대상 경로와 요소 순서는 보존한다. 이 처리는 이름공간 호환을 위한 변환이다.

Strict 여부는 예외 문구 대신 파일 내용으로 판단한다. 다른 형식이나 손상된 파일의
오류는 호출자에게 전달한다. 변환한 문서·부품 수는 `STATS`와 선택적인 `note`에 남겨
호출자가 파싱 결과와 함께 기록할 수 있게 한다.
"""

from __future__ import annotations

import io
import posixpath
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

STRICT_PREFIX = b"http://purl.oclc.org/ooxml/"

#: WordprocessingML 이름공간. `open_document` 가 Strict 를 Transitional 이름으로 바꿔 열므로
#: 본문을 읽을 때는 이 이름공간을 사용한다.
W_MAIN = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_P = W_MAIN + "p"
_TBL = W_MAIN + "tbl"
_SDT = W_MAIN + "sdt"
_SDT_CONTENT = W_MAIN + "sdtContent"
_SECT_PR = W_MAIN + "sectPr"
_TR = W_MAIN + "tr"
_TC = W_MAIN + "tc"
_CUSTOM_XML = W_MAIN + "customXml"
_CUSTOM_XML_PR = W_MAIN + "customXmlPr"
#: 추적 변경으로 삭제된 내용. 안의 블록은 변경 후 문서에 없다.
_DELETED_BLOCK = frozenset((W_MAIN + "del", W_MAIN + "moveFrom"))
#: 목차 콘텐츠 컨트롤의 문서 부품 갤러리 값.
_TOC_GALLERY = re.compile(r"table of contents", re.I)

# 이름공간 변환은 XML과 관계 파일에 적용한다. 그림·글꼴·삽입 개체 바이트는 보존한다.
_NAMED_PARTS = (".xml", ".rels")

_STRICT_URI = re.compile(rb"http://purl\.oclc\.org/ooxml/[A-Za-z0-9/_.\-]*")
#: 시작 태그(빈 요소 태그 포함). 문자 노드·주석에 적힌 URI는 본문 내용으로 보존한다.
_START_TAG = re.compile(rb'''<!--.*?-->|<!\[CDATA\[.*?\]\]>|<[A-Za-z_](?:[^<>"']+|"[^"]*"|'[^']*')*>''', re.S)
#: 시작 태그 안에서 값 전체가 Strict URI 인 속성(이름공간 선언 · 관계 Type · `a:graphicData/@uri` 따위).
_URI_ATTR = re.compile(rb"""(\s)([A-Za-z_][\w:.\-]*)(\s*=\s*)(["'])(.*?)\4""", re.S)


def _rename_attr(m: "re.Match[bytes]") -> bytes:
    # 관계 Target 은 가리키는 곳(외부 링크 주소)이라 이름이 아니다.
    if m.group(2).rsplit(b":", 1)[-1] == b"Target":
        return m.group(0)
    strict = _STRICT_URI.fullmatch(m.group(5))
    if strict is None:
        return m.group(0)
    uri = _to_transitional(strict)
    return m.group(1) + m.group(2) + m.group(3) + m.group(4) + uri + m.group(4)


def _to_transitional_names(data: bytes) -> bytes:
    """부품 XML 의 Strict 이름만 Transitional 로 바꾼다 — 시작 태그 안의 이름공간 선언과 값 전체가 Strict URI 인
    속성 값. 문자 노드(w:t · w:instrText 따위) · 주석 · 관계 Target · 값 일부에 URI 를 적은 속성은 그대로 둔다.
    바이트 전체에 치환을 걸면 본문에 적힌 Strict URI 글까지 Transitional URI 로 바뀐다."""
    return _START_TAG.sub(lambda t: t.group(0) if t.group(0).startswith(b'<!')
                          else _URI_ATTR.sub(_rename_attr, t.group(0)), data)

# 호출자가 진단 기록에 포함할 수 있도록 변환 건수를 집계한다.
STATS: Counter = Counter()

# 워커는 이 키로 변환 여부를 반환하고, 부모 프로세스는 반환값을 집계한다.
STRICT_NOTE_KEY = "strict_namespace"


def _to_transitional(match: "re.Match[bytes]") -> bytes:
    """Strict URI 하나를 Transitional URI 로 옮긴다.

    첫 경로 요소 뒤에 `/2006`을 추가한다(`drawingml/main` → `drawingml/2006/main`).
    확장 속성 URI는 `extendedProperties`를 `extended-properties`로 바꿔
    `python-docx`의 `RELATIONSHIP_TYPE.EXTENDED_PROPERTIES`와 일치시킨다.
    """
    tail = match.group(0)[len(STRICT_PREFIX):]
    head, _, rest = tail.partition(b"/")
    rest = rest.replace(b"extendedProperties", b"extended-properties")
    base = b"http://schemas.openxmlformats.org/" + head + b"/2006"
    return base + (b"/" + rest if rest else b"")


def is_strict(path: Path | str) -> bool:
    """패키지 관계 파일에 Strict 이름공간 URI가 있는지 확인한다."""
    try:
        with zipfile.ZipFile(str(path)) as z:
            return STRICT_PREFIX in z.read("_rels/.rels")
    except Exception:
        return False


def as_transitional(path: Path | str) -> io.BytesIO:
    """Strict URI를 변환한 ZIP 사본을 메모리에서 만들고 읽기 위치를 처음으로 돌린다."""
    buf = io.BytesIO()
    with zipfile.ZipFile(str(path)) as src:
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as dst:
            for item in src.infolist():
                data = src.read(item.filename)
                if item.filename.endswith(_NAMED_PARTS):
                    data = _to_transitional_names(data)
                dst.writestr(item, data)
    buf.seek(0)
    return buf


#: 본문 부품의 관례 이름과 그 관계 파일 이름. 읽는 쪽은 이 이름으로 본문을 부른다.
MAIN_PART = "word/document.xml"
_MAIN_RELS = "word/_rels/document.xml.rels"


def main_part(z: zipfile.ZipFile) -> str | None:
    """패키지 관계(`_rels/.rels` 의 officeDocument)가 가리키는 본문 부품 이름. 관계가 없거나 대상이 패키지에 없으면 None.

    Word 는 본문을 `word/document2.xml` 같은 다른 이름으로 저장하기도 한다. `python-docx` 는 관계를 따라 열지만,
    관례 이름으로만 읽는 코드는 본문을 찾지 못할 수 있다. 이 함수는 관계에 기록된 실제 경로를 반환한다.
    """
    from xml.etree import ElementTree

    try:
        rels = ElementTree.fromstring(z.read("_rels/.rels"))
    except (KeyError, ElementTree.ParseError):
        return None
    names = set(z.namelist())
    for rel in rels:
        if (rel.get("Type") or "").endswith("/officeDocument") and rel.get("TargetMode") != "External":
            part = posixpath.normpath(unquote(rel.get("Target") or "").lstrip("/"))
            return part if part in names else None
    return None


def _part_name(z: zipfile.ZipFile, name: str) -> str:
    """본문과 본문 관계 파일의 관례 이름을 실제 패키지 관계가 가리키는 경로로 바꾼다.

    관계로도 찾지 못하면 이름을 그대로 돌려줘 `KeyError` 가 올라가게 한다. 본문이 없는 패키지는 「열지 못함」으로 세어져야 한다.
    """
    if name not in (MAIN_PART, _MAIN_RELS):
        return name
    main = main_part(z)
    if main is None or main == MAIN_PART:
        return name
    if name == MAIN_PART:
        STATS["관계로 찾아 읽은 본문 부품"] += 1
        return main
    head, base = posixpath.split(main)
    return f"{head}/_rels/{base}.rels"


def resolve_relationship_part(
    z: zipfile.ZipFile, target: str, *, source_part: str = MAIN_PART,
    target_mode: str | None = None,
) -> str | None:
    """Resolve an internal OPC relationship against its actual source part.

    The result is an existing ZIP member name. External URLs, fragments and
    paths escaping the package have no internal member and return None.
    """
    if target_mode == "External" or not target:
        return None
    uri = urlsplit(target)
    if uri.scheme or uri.netloc or uri.query or uri.fragment:
        return None
    path = unquote(uri.path)
    if "\\" in path or "\x00" in path:
        return None
    if source_part == MAIN_PART:
        source_part = main_part(z) or MAIN_PART
    member = posixpath.normpath(
        path.lstrip("/") if path.startswith("/")
        else posixpath.join(posixpath.dirname(source_part), path)
    )
    if member == ".." or member.startswith("../"):
        return None
    try:
        return None if z.getinfo(member).is_dir() else member
    except KeyError:
        return None


def read_zip_part(z: zipfile.ZipFile, name: str) -> bytes:
    """이미 연 패키지에서 부품 XML(본문 · 관계 · 차트 따위) 하나를 Transitional 이름으로 읽는다.

    본문 부품과 그 관계 파일은 관례 이름으로 부르면 된다. 다른 이름으로 저장된 본문은 패키지 관계로 찾는다(`_part_name`).
    """
    data = z.read(_part_name(z, name))
    try:
        strict = STRICT_PREFIX in z.read("_rels/.rels")
    except KeyError:
        strict = False
    if strict:
        STATS["이름을 맞춰 읽은 Strict 부품"] += 1
        data = _to_transitional_names(data)
    return data


def open_document(path: Path | str, note: dict | None = None) -> Any:
    """원본을 먼저 열고, 실패한 문서가 Strict이면 이름공간을 변환한 메모리 사본을 연다.

    Strict 변환이 성공하면 `STATS`에 집계하고, `note`가 있으면 변환 여부를 기록한다.
    `STATS`는 프로세스별로 관리되므로 워커의 처리 결과를 부모에서 집계하려면
    워커가 `note`를 반환해야 한다. 입력 파일은 수정하지 않는다.
    """
    from docx import Document  # 무거운 의존이라 호출 시점에 연다

    try:
        return Document(str(path))
    except Exception:
        if not is_strict(path):
            raise
        document = Document(as_transitional(path))
        STATS["이름을 맞춰 연 Strict 문서"] += 1
        if note is not None:
            note[STRICT_NOTE_KEY] = True
        return document


def is_toc_control(sdt) -> bool:
    """이 콘텐츠 컨트롤(`w:sdt`)이 목차인가. 문서 부품 갤러리 값으로 판정한다."""
    g = sdt.find(f"{W_MAIN}sdtPr/{W_MAIN}docPartObj/{W_MAIN}docPartGallery")
    return g is not None and bool(_TOC_GALLERY.search(g.get(W_MAIN + "val") or ""))


def body_blocks(container, note: dict | None = None):
    """문서 본문의 블록 요소(`w:p` · `w:tbl`)를 문서 순서대로 반환한다.

    python-docx 의 `Document.paragraphs` 와 `Document.tables` 는 본문의 **직계** 자식만 준다.
    본문 수준의 콘텐츠 컨트롤(`w:sdt`)이나 사용자 정의 XML(`w:customXml`) 안에 든 문단과 표는
    어느 쪽에도 나오지 않고, 예외 없이 글자만 빠진다. 이 함수는 감싸는 요소 안으로 들어가
    그 안의 블록을 같은 순서로 낸다.

    감싸는 요소의 이름을 열거하지 않는다. 문단과 표가 아닌 요소는 모두 안으로 들어가 본다
    (책갈피 같은 표지는 자식이 없어 아무것도 내지 않는다). 예외는 둘이다.

    - 추적 변경으로 삭제된 내용(`w:del` · `w:moveFrom`)은 건너뛴다.
    - 목차 콘텐츠 컨트롤은 건너뛴다. 목차는 본문과 같은 글자를 담으므로 각 Phase 가 읽지 않기로
      정한 영역이다. 이 함수를 쓰기 전에도 본문 수준 목차 컨트롤 안의 문단은 읽히지 않았다.

    `note` 를 주면 들어가 읽은 콘텐츠 컨트롤과 건너뛴 목차 컨트롤의 수를 더한다.
    """
    for child in container.iterchildren():
        tag = child.tag
        if tag == _P or tag == _TBL:
            yield child
        elif tag == _SECT_PR or tag in _DELETED_BLOCK or not isinstance(tag, str):
            continue
        elif tag == _SDT:
            if is_toc_control(child):
                if note is not None:
                    note["건너뛴 목차 콘텐츠 컨트롤"] = note.get("건너뛴 목차 콘텐츠 컨트롤", 0) + 1
                continue
            content = child.find(_SDT_CONTENT)
            if content is not None:
                if note is not None:
                    note["읽은 몸통 콘텐츠 컨트롤"] = note.get("읽은 몸통 콘텐츠 컨트롤", 0) + 1
                yield from body_blocks(content, note)
        else:
            yield from body_blocks(child, note)


def _lift_wrappers(parent, where: str, got: Counter) -> None:
    """`parent` 의 직계 자식 가운데 감싸는 요소를 그 내용으로 바꾼다. 표 · 행 · 칸 수준에 쓴다."""
    i = 0
    while i < len(parent):
        child = parent[i]
        tag = child.tag
        if tag == _SDT or tag == _CUSTOM_XML:
            if tag == _SDT and is_toc_control(child):
                got["건너뛴 목차 콘텐츠 컨트롤"] += 1
                i += 1
                continue
            if tag == _SDT:
                content = child.find(_SDT_CONTENT)
                inner = [] if content is None else list(content)
                got[f"{where} 안의 콘텐츠 컨트롤"] += 1
            else:
                inner = [c for c in child if c.tag != _CUSTOM_XML_PR]
                got[f"{where} 안의 사용자 XML"] += 1
            for k, el in enumerate(inner):
                parent.insert(i + k, el)
            parent.remove(child)
            # 꺼낸 첫 요소가 다시 감싸는 요소일 수 있으므로 같은 위치를 다시 본다.
            continue
        i += 1


def lift_table_wrappers(doc) -> Counter:
    """표 안의 콘텐츠 컨트롤과 사용자 XML 을 풀어, 그 안의 행 · 칸 · 블록을 제자리에 둔다.

    python-docx 의 `Table.rows` 는 표의 직계 `w:tr` 만, `_Row.cells` 는 행의 직계 `w:tc` 만,
    `_Cell.paragraphs` 는 칸의 직계 `w:p` 만 준다. 행이나 칸을 콘텐츠 컨트롤이 감싸면 그 행과
    칸의 글자가 예외 없이 빠진다. 행과 칸은 병합(`gridSpan` · `vMerge`) 계산이 python-docx 안에
    있어서 읽는 함수를 따로 만들지 않고, 메모리에 올린 문서 트리에서 감싸는 요소를 그 내용으로
    바꾼다. 파일은 바꾸지 않는다.

    규칙은 `body_blocks` 와 같다. 목차 콘텐츠 컨트롤은 그대로 두어 읽지 않는다. 문단 안(런
    수준)의 감싸는 요소는 여기서 다루지 않는다 — 문단 글자를 읽는 함수가 이미 그 안까지 읽는다.

    한 문서에 한 번만 푼다. 푼 수는 문서 객체에 남기고 두 번째 호출부터는 그 수를 돌려준다.
    """
    got = getattr(doc, "_lifted_table_wrappers", None)
    if got is not None:
        return got
    got = Counter()
    level = {_TBL: "표", _TR: "행", _TC: "칸"}
    for tbl in list(doc.element.body.iter(_TBL)):
        stack = [tbl]
        while stack:
            el = stack.pop()
            _lift_wrappers(el, level[el.tag], got)
            stack.extend(c for c in el if c.tag in (_TR, _TC))
    doc._lifted_table_wrappers = got
    return got


def body_items(doc, note: dict | None = None):
    """`body_blocks` 를 python-docx 객체로 낸다 — `("para", Paragraph)` 와 `("table", Table)`.

    먼저 `lift_table_wrappers` 로 표 안의 감싸는 요소를 푼다. 그래서 여기서 받은 표는
    `rows` · `cells` · `paragraphs` 가 감싼 행 · 칸 · 문단까지 준다. 푼 수는 `note` 에 더한다.
    """
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    lifted = lift_table_wrappers(doc)
    if note is not None:
        for k, v in lifted.items():
            note[k] = note.get(k, 0) + v
    parent = doc._body
    for el in body_blocks(doc.element.body, note):
        if el.tag == _P:
            yield ("para", Paragraph(el, parent))
        else:
            yield ("table", Table(el, parent))


def body_paragraphs(doc, note: dict | None = None) -> list:
    """본문 문단을 문서 순서대로 반환한다. 감싸는 요소 안의 문단도 포함한다."""
    return [o for k, o in body_items(doc, note) if k == "para"]
