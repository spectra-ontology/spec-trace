"""TDoc의 그림 개체, 그림과 캡션의 연결, 최상위 표의 캡션을 추출한다.

Phase-6 TDoc 파서(03)와 그림 보강기(04)가 같은 규칙으로 그림 목록·표 캡션·파일 색인을 만든다.
캡션 문법은 `caption.TDOC_FIGURE` · `caption.TDOC_TABLE` · `caption.tdoc_number` 다.

그림 개체
    본문 블록을 문서 순서로 순회한다. 표 셀·중첩 표·글상자 안 문단도 포함한다. 각 문단이 직접 담은 그림
    단위(`w:drawing` · `w:pict` · `w:object`)를 모은다. 단위 안으로 더 들어가 단위를 세지 않고, `mc:Fallback`
    대체 표현과 삭제된 변경 표시(`w:del` · `w:moveFrom`) 안의 단위는 제외한다.
    그림으로 치는 단위: 그림(`pic`), 그림을 채운 도형, VML 그림, 도형 묶음 · 그리기 캔버스(그림이 없어도 —
    도형으로 그린 그림이다), 차트 · SmartArt, 수식이 아닌 OLE 개체(Visio · Word.Picture · …).
    그림으로 치지 않는 단위: 낱 도형 · 글상자(화살표 · 테두리 · 설명 상자), ActiveX, 수식 OLE —
    ProgID 가 'Equation' 으로 시작하거나, 개체 부품이 수식 편집기 개체이거나(`docx_text.equation_ole`), ProgID 가
    비었어도 미리보기 그림이 모두 MathType 그림(`docx_text.equation_images`)이다. OLE 개체 없이 MathType 그림만
    그리는 그림 · VML 그림(`pic_eq`)도 수식이다 — 본문 글은 그 자리에 그림을 읽은 수식 글을 넣는다
    (`ole_equation.annotate_pictures`).

캡션 짝
    캡션은 `caption.tdoc_number('figure', …)` 가 받는 문단이다. 그림 단위 하나는 캡션 하나에만 붙고, 캡션 하나는
    여러 단위를 가질 수 있다(하위 그림 '(a)' · '(b)'). 캡션마다 먼저 볼 방향은 `_first_steps` 가 정한다 — 기본은
    앞(캡션이 그림 아래), 캡션과 그림이 번갈아 이어지는 줄이 캡션으로 시작하면 뒤.
    1차 — 캡션마다 문서 순서로 먼저 볼 방향의 바로 붙은 묶음(`_adjacent`: 빈 문단 · 그림 아닌 단위 · 캡션 아닌
    글상자 글만 건넌다. 다른 표의 칸 글에서 멈추면 그 표의 그림 전부).
    2차 — 아직 그림이 연결되지 않은 캡션마다 우선 방향의 범위를 검색한다(`_gap`: 본문 글 · 하위 그림 이름표를 건너 다른 캡션 ·
    절 제목 · 캡션 아닌 그림 머리말 문단 앞까지, 같은 표 자리의 그림), 그것이 비었을 때만 반대 방향의 바로 붙은
    묶음. 간격을 반대 방향 묶음보다 먼저 보는 까닭은 '그림 · (a) · 그림 · (b) · 캡션 · 그림 · (a) · …' 처럼 하위
    그림 이름표가 그림 아래 붙은 문서에서, 캡션 바로 뒤 그림이 다음 캡션의 첫 하위 그림이기 때문이다. 캡션마다
    차례로 정하므로 '캡션 · 그림 · 본문 · 캡션 · 그림' (캡션이 그림 위)에서는 앞 캡션이 뒤 그림을 먼저 갖는다.
    3차 — 여전히 그림이 연결되지 않은 캡션은 반대 방향의 범위를 검색한다.
    4차 — 캡션 문단 안에서 캡션 글 뒤에 놓인 그림 단위(`Event.after_text`)를 그 캡션이 가졌고, 문서 순서로 바로
    다음 캡션이 3차까지 아무 단위도 갖지 못했으면 그 단위들은 다음 캡션의 것으로 옮긴다('그림 A · [Figure 1 글 ·
    그림 B] · Figure 2' 에서 B 는 Figure 2 의 그림이다 — 그림을 캡션 문단 끝에 붙여 둔 문서). 옮기는 조건은 셋이
    모두 맞을 때다: 다음 캡션에 연결된 그림이 없음 · 앞 캡션에 캡션 글 뒤 단위 외의 그림도 있음(앞 캡션의 그림이 글 앞에
    따로 있는 '그림 아래 캡션' 문서다) · 두 캡션 사이에 글 있는 문단이 없음. 하나라도 어긋나면 옮기지 않는다 —
    '[Figure 1 글 · 그림 A] · Figure 2 · 그림 B'(다음 캡션이 그림을 가짐), '[Figure 1 글 · 그림 A] · Figure 2'(A 가
    Figure 1 의 하나뿐인 그림), '그림 A · [Figure 1 글 · 그림 B] · 본문 · Figure 2'(사이에 글) 는 모두 B(또는 A)가
    앞 캡션에 남는다.
    어느 캡션과도 짝짓지 못한 단위는 캡션 없는 항목이 된다. 짝을 못 정한 상태는 따로 두지 않는다.
    짝은 문서 순서만 본다 — 그림 부품 파일 이름 · 미디어 번호(`imageN`)는 쓰지 않는다. 1~3차의 문서 순서 단위는
    문단이다: 한 문단의 그림 단위는 그 문단 글보다 앞에 놓인 것으로 본다(`_Walker.paragraph`). 그래서 캡션 글
    뒤 같은 문단에 놓인 그림도 1~3차에서는 그 캡션의 앞 후보가 되고, 4차만 문단 안 순서를 본다.
    이 절이 짝 규칙의 정본이다. `scripts/tsg/RAN/formal/common/README.md#tdoc-figure-captions`는 요약과
    합성 배치 기대 표를 두고, 다섯 WG Spec의 「그림 캡션 짝 규칙」 소절이 이를 참조한다.
    그 표의 기대는 `test_docx_figures_caption_pairing.py` 가 검사한다.

표 캡션
    본문 최상위 표마다 바로 위 · 바로 아래의 글 있는 최상위 문단 중 `caption.tdoc_number('table', …)` 가 받는 것.
    기본은 위(3GPP 표 제목 TH 관례), 위가 캡션이 아니면 아래 — 단 아래 문단이 다음 표의 바로 위 문단이면 다음
    표의 몫이다. 이웃한 표들이 사이 문단 하나씩을 나눠 갖고 그 문단이 모두 캡션인 사슬은 사슬 첫 표의 위가
    캡션이 아니고 마지막 표의 아래가 캡션이면 모두 아래 캡션을 갖는다('본문 · 표 · Table 2-1 · 표 · Table 2-2' —
    위 규칙으로는 첫 표가 캡션을 잃고 'Table 2-2' 가 버려진다). 표지 표는 부르는 쪽이 거른다.

회의 보고서 그림
    Phase-2 회의 보고서 파서(RAN1 · RAN2 · RAN3 · RAN4 · RAN5 `figure_extractor`)의 캡션 없는 그림도 같은 단위 판정을
    쓴다(`report_units`). 단위마다 그 단위를 담은 본문 최상위 블록 번호(`docx_text.iter_blocks` 차례)가 붙고,
    표지 구간(`cover_end` 앞)은 부르는 쪽이 뺀다.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from lxml import etree

import caption
import docx_text

_W = docx_text.W_NS
_A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
_R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_V_NS = "urn:schemas-microsoft-com:vml"
_O_NS = "urn:schemas-microsoft-com:office:office"


def _w(name: str) -> str:
    return f"{{{_W}}}{name}"


_P = _w("p")
_T = _w("t")
_TR = _w("tr")
_TC = _w("tc")
_DRAWING, _PICT, _OBJECT = _w("drawing"), _w("pict"), _w("object")
_UNITS = (_DRAWING, _PICT, _OBJECT)
_TXBX = _w("txbxContent")
_FALLBACK = docx_text._MC_FALLBACK
_CHOICE = f"{{{docx_text.MC_NS}}}Choice"
_GONE = {_w("del"), _w("moveFrom")}
#: 단위가 이 문단의 것이 아닌 자리 — 다른 단위 안 · 글상자 안 · 대체본 · 지운 변경 표시.
_NOT_OWN = {*_UNITS, _TXBX, _FALLBACK, *_GONE}
_GRAPHIC_DATA = f"{{{_A_NS}}}graphicData"
_BLIP = f"{{{_A_NS}}}blip"
_IMAGEDATA = f"{{{_V_NS}}}imagedata"
_OLE = f"{{{_O_NS}}}OLEObject"
_OBJECT_EMBED = _w("objectEmbed")
_CONTROL = _w("control")
_V_GROUP = f"{{{_V_NS}}}group"
_P_STYLE = f"{_w('pPr')}/{_w('pStyle')}"
_VAL = _w("val")
_EMBED = f"{{{_R_NS}}}embed"
_LINK = f"{{{_R_NS}}}link"
_RID = f"{{{_R_NS}}}id"
_DM = f"{{{_R_NS}}}dm"

#: 그림으로 치지 않는 개체 종류.
_NOT_FIGURE = frozenset({"shape", "textbox", "vml_shape", "vml_textbox", "activex", "object_other", "ole_eq",
                         "pic_eq", "empty"})
#: Word 가 그림 파일을 두는 부품 자리. 그림 파일 경로(`filePath`)는 이 아래 이름에 'media/' 를 붙인 것이다.
_MEDIA_DIR = "/word/media/"
#: 내용 부품을 따로 두지 않고 문서 본문 안에 도형으로 그리는 그림 종류 — 그림 부품이 없으면 단위 XML 이 그림 파일이다.
_DRAWN = frozenset({"group", "canvas", "vml_group"})
#: 도형으로만 그린 단위의 XML 을 두는 그림 파일 폴더.
_DRAWINGS = "media/drawings/"
#: 내용을 따로 둔 부품을 가리키는 `a:graphicData` 종류(uri 끝) — 그림 · 도형 · 묶음 · 캔버스는 본문 안에 그린다.
_INLINE_URIS = ("/picture", "wordprocessingShape", "wordprocessingGroup", "wordprocessingCanvas", "lockedCanvas")


@dataclass
class Event:
    """문서 순회 중 기록한 그림 개체(obj) 또는 문단 텍스트(text).

    table은 가장 바깥 표의 문서 순서상 번호(표 밖이면 None), box는 글상자 안인지 여부다.
    heading 은 문단이 절 제목 스타일(`_heading_styles`)인가.
    para는 해당 개체나 텍스트를 담은 문단 번호다. after_text는 같은 문단의 글(`w:t`) 뒤에
    그림 개체가 놓였는지 나타내며, 캡션 연결의 4차 검사에서 사용한다.
    """
    obj: bool
    table: int | None
    box: bool
    kind: str = ""
    figure: bool = False
    rids: tuple = ()
    source_rids: tuple = ()
    fallback_rids: tuple = ()
    node: object = None
    text: str = ""
    style: str = ""
    heading: bool = False
    #: 본문 최상위 블록 번호(`docx_text.iter_blocks` 순서). 표·글상자 안에서는 바깥 블록을 가리킨다.
    block: int | None = None
    para: int | None = None
    after_text: bool = False


def _inside(el, top, tags) -> bool:
    """el 과 top 사이(둘 다 빼고) 조상 가운데 tags 태그가 있는가."""
    a = el.getparent()
    while a is not None and a is not top:
        if a.tag in tags:
            return True
        a = a.getparent()
    return False


def _find(unit, tags, stop):
    """unit 아래 tags 요소를 문서 순서로 — stop 태그 요소 안의 것은 뺀다."""
    for el in unit.iter(*tags):
        if el is not unit and not _inside(el, unit, stop):
            yield el


def _first(unit, tags, stop):
    return next(_find(unit, tags, stop), None)


def _image_rids(node, stop) -> tuple:
    rids = []
    for el in _find(node, (_BLIP, _IMAGEDATA), stop):
        rid = (el.get(_EMBED) or el.get(_LINK)) if el.tag == _BLIP else el.get(_RID)
        if rid:
            rids.append(rid)
    return tuple(rids)


def _fallback_rids(unit) -> tuple:
    """단위가 `mc:Choice` 안에 있으면 짝 `mc:Fallback` 이 담은 그림 관계 id."""
    choice = unit.getparent()
    if choice is None or choice.tag != _CHOICE:
        return ()
    alt = choice.getparent()
    fb = next((c for c in alt if c.tag == _FALLBACK), None) if alt is not None else None
    return _image_rids(fb, {_TXBX}) if fb is not None else ()


def _source_rids(unit, stop) -> tuple:
    """단위 안(글상자 안 · 대체본 안은 빼고) 차트 · SmartArt · 잉크처럼 내용을 따로 둔 부품의 관계 id, 문서 순서로.

    차트(`c:chart` · `cx:chart`) · 잉크(`w14:contentPart`)는 `a:graphicData` 의 자식이 `r:id` 로, SmartArt 는
    `dgm:relIds` 가 `r:dm`(도형의 텍스트를 담은 데이터 부품)으로 가리킨다. 배치 · 색 · 꾸밈 부품(`r:lo` · `r:qs` ·
    `r:cs`)은 내용이 아니라 뺀다. 묶음 · 캔버스 안에 든 차트도 같은 자리에서 얻는다.
    """
    out = []
    for gd in _find(unit, (_GRAPHIC_DATA,), stop):
        if gd.get("uri", "").endswith(_INLINE_URIS):
            continue
        for ch in gd:
            rid = ch.get(_DM) or ch.get(_RID)
            if rid and rid not in out:
                out.append(rid)
    return tuple(out)


def _classify(unit, is_equation_image) -> tuple[str, tuple, tuple]:
    """그림 단위의 종류, 그 단위가 그리는 그림 관계 id(글상자 안 · 대체본 안의 그림은 빼고), 내용 부품 관계 id.

    내용 부품은 그림 부품이 아닌 원본 — 차트 · SmartArt · 잉크의 부품(`_source_rids`)과, 미리보기 그림이 없는
    OLE 개체의 개체 부품(`o:OLEObject` · `w:objectEmbed` 의 `r:id`)이다. 미리보기 그림이 있는 OLE 개체는 그 그림이
    그림 파일이라 개체 부품을 더 두지 않는다.
    """
    rids = _image_rids(unit, {_TXBX, _FALLBACK})
    stop = {_TXBX, _FALLBACK}
    if unit.tag == _OBJECT or (unit.tag == _PICT and _first(unit, (_OLE,), stop) is not None):
        ole = _first(unit, (_OLE,), stop)
        emb = _first(unit, (_OBJECT_EMBED,), stop) if unit.tag == _OBJECT else None
        if ole is not None or emb is not None:
            prog = ((ole.get("ProgID") if ole is not None else None)
                    or (emb.get(_w("progId")) if emb is not None else None) or "")
            if prog.startswith("Equation") or (ole is not None and docx_text.equation_ole(ole)) \
                    or (rids and all(is_equation_image(r) for r in rids)):
                return "ole_eq", rids, ()
            own = tuple(r for r in ((ole.get(_RID) if ole is not None else None),
                                    (emb.get(_RID) if emb is not None else None)) if r)
            return "ole:" + (".".join(prog.split(".")[:2]) or "?"), rids, (() if rids else own[:1])
        if _first(unit, (_CONTROL,), stop) is not None:
            return "activex", rids, ()
        return ("object_pic" if rids else "object_other"), rids, ()
    if unit.tag == _PICT:
        if rids:
            return ("pic_eq" if all(is_equation_image(r) for r in rids) else "vml_pic"), rids, ()
        if _first(unit, (_V_GROUP,), stop) is not None:
            return "vml_group", rids, ()
        return ("vml_textbox" if _first(unit, (_TXBX,), {_FALLBACK}) is not None else "vml_shape"), rids, ()
    gd = _first(unit, (_GRAPHIC_DATA,), stop)
    if gd is None:
        return "empty", rids, ()
    uri = gd.get("uri", "")
    src = _source_rids(unit, stop)
    if uri.endswith("/picture"):
        return ("pic_eq" if rids and all(is_equation_image(r) for r in rids) else "pic"), rids, src
    if "chartex" in uri:
        return "chartex", rids, src
    if uri.endswith("/chart"):
        return "chart", rids, src
    if uri.endswith("/diagram"):
        return "diagram", rids, src
    if uri.endswith("wordprocessingGroup"):
        return "group", rids, src
    if uri.endswith("wordprocessingCanvas") or uri.endswith("lockedCanvas"):
        return "canvas", rids, src
    if uri.endswith("wordprocessingShape"):
        if rids:
            return "shape_pic", rids, src
        return ("textbox" if _first(unit, (_TXBX,), {_FALLBACK}) is not None else "shape"), rids, src
    return "other:" + uri.rsplit("/", 1)[-1], rids, src


def _heading_styles(doc) -> set[str]:
    """절 제목 문단 스타일의 styleId — 이름이 'Heading' 으로 시작하거나, 스타일이 개요 수준 0~8 을 선언한다.

    개요 수준은 스타일 자신의 `w:outlineLvl` 이고, 없으면 `w:basedOn` 을 따라 올라가며, 이름이 'heading N'
    이면 N-1 이다. 03 파서가 절 제목으로 받는 두 스타일 갈래(스타일 이름 · 스타일 개요 수준)와 같다.
    """
    own, based, out = {}, {}, set()
    for s in doc.styles:
        el = s.element
        if el.get(_w("type")) != "paragraph":
            continue
        sid, name = s.style_id, s.name or ""
        if name.startswith("Heading"):
            out.add(sid)
        lvl = el.find(f"{_w('pPr')}/{_w('outlineLvl')}")
        if lvl is not None and (lvl.get(_VAL) or "").isdigit():
            own[sid] = int(lvl.get(_VAL))
        elif name.lower().startswith("heading ") and name[8:].strip().isdigit():
            own[sid] = int(name[8:].strip()) - 1
        base = el.find(_w("basedOn"))
        if base is not None:
            based[sid] = base.get(_VAL)
    for sid in based.keys() | own.keys():
        cur, seen = sid, set()
        while cur is not None and cur not in own and cur not in seen:
            seen.add(cur)
            cur = based.get(cur)
        if cur in own and own[cur] < 9:
            out.add(sid)
    return out


class _Walker:
    def __init__(self, doc):
        self.events: list[Event] = []
        self.style_names = {s.style_id: s.name for s in doc.styles}
        self.headings = _heading_styles(doc)
        self.is_equation_image = docx_text.equation_images(doc.part)
        self.tables = 0
        self.paras = 0
        self.top = None
        self.block = None

    def blocks(self, container, table, box):
        for n, b in enumerate(docx_text.iter_blocks(container)):
            if container is self.top:
                self.block = n
            if b.tag == _P:
                self.paragraph(b, table, box)
                continue
            t = table
            if t is None:
                t = self.tables
                self.tables += 1
            for tr in docx_text._iter_wrapped(b, _TR):
                for tc in docx_text._iter_wrapped(tr, _TC):
                    self.blocks(tc, t, box)

    def paragraph(self, p, table, box):
        para = self.paras
        self.paras += 1
        for unit, after_text in _own_units(p):
            kind, rids, src = _classify(unit, self.is_equation_image)
            figure = kind not in _NOT_FIGURE
            self.events.append(Event(obj=True, table=table, box=box, kind=kind, figure=figure, rids=rids,
                                     source_rids=src, fallback_rids=_fallback_rids(unit),
                                     node=unit if figure and kind in _DRAWN else None, block=self.block,
                                     para=para, after_text=after_text))
            for tx in unit.iter(_TXBX):
                if not _inside(tx, unit, {_TXBX, _FALLBACK}):
                    self.blocks(tx, table, True)
        st = p.find(_P_STYLE)
        sid = st.get(_VAL) if st is not None else ""
        self.events.append(Event(obj=False, table=table, box=box, text=docx_text.final_text(p),
                                 style=self.style_names.get(sid, sid), heading=sid in self.headings,
                                 block=self.block, para=para))


def _own_units(p):
    """문단 p 가 직접 담은 그림 단위(`_NOT_OWN` 안의 것은 빼고)를 문서 순서로, 각각 그 앞에 이 문단의 빈칸 아닌
    글(`w:t`, `_NOT_OWN` 안의 것은 빼고)이 있었는가와 함께."""
    units = [u for u in p.iter(*_UNITS) if not _inside(u, p, _NOT_OWN)]
    if not units:
        return []
    want = set(map(id, units))
    out, seen_text = [], False
    for el in p.iter(_T, *_UNITS):
        if id(el) in want:
            out.append((el, seen_text))
        elif el.tag == _T and not seen_text and (el.text or "").strip() and not _inside(el, p, _NOT_OWN):
            seen_text = True
    return out


def events(doc) -> list[Event]:
    """그림 개체와 문단 텍스트를 문서 순서로 반환한다. 그림 개체가 없으면 빈 목록이다."""
    body = doc.element.body
    if next(body.iter(*_UNITS), None) is None:
        return []
    walker = _Walker(doc)
    walker.top = body
    walker.blocks(body, None, False)
    return walker.events


def figure_captions(evs: list[Event]) -> dict[int, str]:
    """그림 캡션의 Event 인덱스를 추출한 캡션 번호 문자열에 연결한다."""
    out = {}
    for i, e in enumerate(evs):
        if not e.obj and e.text:
            num = caption.tdoc_number("figure", e.text, e.style)
            if num is not None:
                out[i] = num
    return out


def _transparent(e: Event, caps: dict, i: int) -> bool:
    """캡션 연결 시 빈 문단·캡션이 아닌 글상자 텍스트·그림이 아닌 개체를 건너뛴다."""
    if e.obj:
        return not e.figure
    return not e.text or (e.box and i not in caps)


def _run(evs, caps, owner, c, step, end):
    """캡션 c에서 step 방향으로 연속한 미연결 그림과 검색이 멈춘 인덱스를 반환한다.

    _transparent가 허용하는 항목은 건너뛰고, 이미 연결된 그림이나 다른 본문에서 멈춘다.
    """
    run, j = [], c + step
    while j != end:
        e = evs[j]
        if e.obj and e.figure:
            if j in owner:
                break
            run.append(j)
        elif not _transparent(e, caps, j):
            break
        j += step
    return run, j


def _first_steps(evs: list[Event], caps: dict) -> dict[int, int]:
    """캡션마다 먼저 볼 방향(-1 앞 · +1 뒤).

    건너뛸 것(`_transparent`)만 사이에 둔 캡션 · 그림 단위의 최대 줄이 캡션으로 시작해 그림 단위로 끝나고 캡션을
    둘 이상 담으면 그 줄의 캡션은 모두 뒤를 먼저 본다('Figure 1 · 그림 · Figure 2 · 그림' — 캡션이 그림 위).
    나머지는 앞을 먼저 본다(캡션이 그림 아래 — 표본에서 더 흔한 관례).
    캡션이 하나뿐인 줄('캡션 · 그림')은 뒤를 먼저 보게 하지 않는다 — 표 안 하위 그림 이름표('Rank 1' 같은 글)가
    줄을 끊어, 앞 표의 그림 아래 붙은 캡션이 다음 표의 그림과 한 줄로 묶이는 문서가 표본에 있다.
    """
    first = {c: -1 for c in caps}
    line: list[int] = []

    def close():
        if line and line[0] in caps and line[-1] not in caps and sum(1 for i in line if i in caps) >= 2:
            for i in line:
                if i in caps:
                    first[i] = 1
        line.clear()

    for i, e in enumerate(evs):
        if i in caps or (e.obj and e.figure):
            line.append(i)
        elif not _transparent(e, caps, i):
            close()
    close()
    return first


def _gap(evs: list[Event], caps: dict, owner: dict, c: int, step: int) -> list[int]:
    """짝 없는 캡션 c 에서 step 방향으로 다른 그림 캡션 · 절 제목 문단 · 캡션이 아닌 그림 머리말 문단
    ('Figure 3 shows …' — 번호 뒤가 본문 문장이라(`caption.tdoc_sentence`) 캡션 문법이 받지 않은 문단) 앞까지 가며 c 와 같은 표 자리(같은
    가장 바깥 표, 또는 둘 다 표 밖)의 짝 없는 그림 단위 — 사이의 본문 글 · 하위 그림 이름표('(a)')는 건너뛴다."""
    out, j = [], c + step
    while 0 <= j < len(evs) and j not in caps and not evs[j].heading:
        e = evs[j]
        if not e.obj and e.text and caption.TDOC_FIGURE.match(e.text):
            break
        if e.obj and e.figure and j not in owner and e.table == evs[c].table:
            out.append(j)
        j += step
    return out


def _adjacent(evs: list[Event], caps: dict, owner: dict, c: int, step: int) -> list[int]:
    """캡션 c 에서 step 방향으로 바로 붙은 짝 없는 그림 단위 묶음(`_run`). 묶음이 다른 표의 칸 글에서 멈추고
    묶음이 모두 그 표 안이면(또는 비었으면) 그 표의 짝 없는 그림 단위 전부 — 표 밖 캡션이 표 안 그림을 이름 짓는다."""
    n = len(evs)
    run, stop = _run(evs, caps, owner, c, step, n if step > 0 else -1)
    if 0 <= stop < n and not evs[stop].obj and evs[stop].table is not None \
            and evs[stop].table != evs[c].table and all(evs[o].table == evs[stop].table for o in run):
        t = evs[stop].table
        run = [o for o in range(n) if evs[o].obj and evs[o].figure and evs[o].table == t and o not in owner]
    return run


def _pair(evs: list[Event], caps: dict) -> dict[int, int]:
    """그림 Event의 인덱스를 연결된 캡션 Event의 인덱스에 대응시킨다."""
    owner: dict[int, int] = {}
    order = sorted(caps)
    first = _first_steps(evs, caps)
    paired: set[int] = set()

    def take(c, run):
        for o in run:
            owner[o] = c
        if run:
            paired.add(c)

    # 1차: 캡션마다 문서 순서로 먼저 볼 방향의 바로 붙은 묶음.
    for c in order:
        take(c, _adjacent(evs, caps, owner, c, first[c]))
    # 2차: 미연결 캡션에서 우선 방향의 범위를 검색하고, 없을 때만 반대편 인접 묶음을 확인한다.
    for c in order:
        if c not in paired:
            take(c, _gap(evs, caps, owner, c, first[c]) or _adjacent(evs, caps, owner, c, -first[c]))
    # 3차: 여전히 미연결인 캡션에서 반대 방향의 범위를 검색한다.
    for c in order:
        if c not in paired:
            take(c, _gap(evs, caps, owner, c, -first[c]))
    # 4차: 다음 캡션이 미연결이고 두 캡션 사이에 본문이 없으면, 앞 캡션 문단의 글 뒤에 있는
    # 그림을 다음 캡션으로 옮긴다. 앞 캡션에도 별도의 그림이 남아야 한다.
    for c, nxt in zip(order, order[1:]):
        if nxt in paired:
            continue
        mine = [o for o, oc in owner.items() if oc == c]
        tail = [o for o in mine if evs[o].after_text and evs[o].para == evs[c].para]
        if not tail or len(tail) == len(mine):
            continue
        if any(not e.obj and e.text.strip() for e in evs[c + 1:nxt]):
            continue
        take(nxt, sorted(tail))
    return owner


@dataclass
class Figure:
    """그림 색인 항목 하나 — 그림 단위 하나."""
    figure_id: str
    figure_number: str
    caption: str
    file_path: str
    parts: tuple
    more_file_paths: tuple = ()
    #: 부품 없이 본문 안에 도형으로만 그린 단위의 XML(그 그림 파일 `media/drawings/drawing{n}.xml` 의 내용).
    drawing: bytes = b""


@dataclass(frozen=True)
class _Drawing:
    """부품이 아닌 그림 파일 — `media_parts` 가 부품과 같은 꼴(`blob` · `partname`)로 돌려준다."""
    partname: str
    blob: bytes


def _parts(doc, rids) -> tuple:
    """관계 id → 패키지 안 그림 부품 이름(외부 연결 · 없는 관계는 뺀다, 같은 부품은 한 번)."""
    rels = doc.part.rels
    out = []
    for rid in rids:
        rel = rels.get(rid)
        if rel is None or rel.is_external:
            continue
        name = str(rel.target_part.partname)
        if name not in out:
            out.append(name)
    return tuple(out)


def media_path(partname: str) -> str:
    """그림 부품 이름 → 색인의 그림 파일 경로('/word/media/image1.png' → 'media/image1.png')."""
    if partname.startswith(_MEDIA_DIR):
        return "media/" + partname[len(_MEDIA_DIR):]
    return "media/" + partname.rsplit("/", 1)[-1]


def _media_paths(partnames) -> dict:
    """그림 부품 이름 → 그림 파일 경로. 서로 다른 부품이 `media_path` 로 같은 경로에 모이면 `/word/media/` 밖
    부품은 부품 이름 전체를 경로로 쓴다('/media/image30.png' → 'media/media/image30.png').
    그 경로도 기존 부품과 겹치면 'media/'를 더 붙여 별도 경로를 만든다.

    > 주의: RAN3 R3-212128 은 같은 문서에 `/word/media/image30.png` 와 `/media/image30.png` 두 그림 부품을
    > 갖는다. 바깥 부품을 이름 끝 조각만으로 옮기면 두 그림이 한 파일을 덮는다. 모이지 않는 부품의 경로는
    > `media_path` 그대로라, 이미 쓴 색인과 그림 파일은 모인 문서만 달라진다.
    """
    out = {p: media_path(p) for p in partnames}
    users: dict = {}
    for p, path in out.items():
        users.setdefault(path, []).append(p)
    for path, ps in users.items():
        if len(ps) > 1:
            for p in ps:
                if not p.startswith(_MEDIA_DIR):
                    out[p] = "media/" + p.lstrip("/")
    occupied = {path for p, path in out.items() if p.startswith(_MEDIA_DIR)}
    for p in sorted(p for p in out if not p.startswith(_MEDIA_DIR)):
        path = out[p]
        while path in occupied:
            path = "media/" + path
        out[p] = path
        occupied.add(path)
    return out


def figures(doc, tdoc_number: str) -> list[Figure]:
    """문서의 그림 색인 — 그림 단위마다 한 항목, 문서 순서로 `FIG-{tdoc}-{순번:03d}`.

    캡션과 짝지은 단위는 그 캡션 문단 글 전체와 'Figure {번호}' 를, 짝 없는 단위는 빈 글을 갖는다.
    그림 파일 경로는 단위의 첫 부품 자리고, 둘째부터의 부품 자리는 차례대로 `more_file_paths` 에 둔다. 부품 차례는
    단위가 그리는 그림 부품(문서 순서) · 그것이 하나도 없을 때만 짝 `mc:Fallback` 의 대체 그림 · 내용 부품
    (`_classify` — 차트 · SmartArt 자료 · 잉크 · 미리보기 없는 OLE 개체)이다. 부품이 하나도 없는 묶음 · 캔버스 ·
    VML 묶음(`_DRAWN`)은 단위 XML 자체를 문서 차례대로 `media/drawings/drawing{n}.xml` 에 둔다.

    > 주의: 그림 부품만 파일로 두면 차트 · SmartArt · 잉크 · 미리보기 없는 OLE 개체와 도형으로만 그린 묶음 ·
    > 캔버스는 `filePath` 가 비어 그림의 내용이 Phase-6 산출물 어디에도 남지 않는다(RAN1 R1-2003968 의 차트 ·
    > RAN4 R4-2112336 의 도형 묶음). 그림 부품이 있던 단위는 그림 부품이 앞이라 `filePath` 가 그대로고, 내용 부품만
    > `more_file_paths` 뒤에 붙는다. 외부 연결 그림 · 관계 대상이 없는 그림(`NULL`)은 담을 내용이 없어 빈 채로 둔다.

    > 주의: 묶음(`wpg` · `v:group`) · 캔버스나 그림 여러 장을 담은 VML 개체는 한 단위가 그림 부품을 여럿
    > 그린다. 첫 부품만 경로로 두면 나머지 그림은 색인에도 파일에도 남지 않는다. 경로는 단위 전체의 부품을
    > 한꺼번에 `_media_paths` 에 넘겨 정한다 — 부품이 서로 다른 경로를 갖게 하는 판정이 문서 전체에서 한 번이다.
    """
    evs = events(doc)
    caps = figure_captions(evs)
    owner = _pair(evs, caps)
    units = []
    for i, e in enumerate(evs):
        if e.obj and e.figure:
            own = _parts(doc, e.rids)
            parts = own + (() if own else _parts(doc, e.fallback_rids)) + _parts(doc, e.source_rids)
            units.append((i, tuple(dict.fromkeys(parts))))
    paths = _media_paths({p for _, parts in units for p in parts})
    out, drawn = [], 0
    for i, parts in units:
        c, e = owner.get(i), evs[i]
        file_path, drawing = (paths[parts[0]] if parts else ""), b""
        if not parts and e.node is not None and not (e.rids or e.source_rids or e.fallback_rids):
            drawn += 1
            file_path = f"{_DRAWINGS}drawing{drawn}.xml"
            drawing = etree.tostring(e.node, xml_declaration=True, encoding="UTF-8", standalone=True)
        out.append(Figure(figure_id=f"FIG-{tdoc_number}-{len(out) + 1:03d}",
                          figure_number=f"Figure {caps[c]}" if c is not None else "",
                          caption=evs[c].text.strip() if c is not None else "",
                          file_path=file_path,
                          parts=parts,
                          more_file_paths=tuple(paths[p] for p in parts[1:]),
                          drawing=drawing))
    return out


def media_parts(doc, figs: list[Figure]) -> dict:
    """그림 색인이 가리키는 그림 파일 경로 → 그 부품(`blob` 이 파일 내용). 색인 항목이 가리키지 않는 부품은 없다.
    도형으로만 그린 단위의 XML(`Figure.drawing`)은 부품과 같은 꼴(`_Drawing`)로 담는다.

    서로 다른 부품이 같은 경로로 모이면 한 파일이 다른 그림을 덮으므로 ValueError 다.
    """
    by_name = {str(r.target_part.partname): r.target_part for r in doc.part.rels.values() if not r.is_external}
    out = {}
    for f in figs:
        pairs = [(path, by_name[name]) for path, name in zip((f.file_path,) + tuple(f.more_file_paths), f.parts)]
        if f.drawing:
            pairs.append((f.file_path, _Drawing(partname=f.figure_id, blob=f.drawing)))
        for path, part in pairs:
            if out.setdefault(path, part) is not part:
                raise ValueError(f"그림 파일 경로 {path} 에 부품 둘: {out[path].partname} · {part.partname}")
    return out


_CHART_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart"
_TOC_GALLERY = _w("docPartGallery")
_INSTR = _w("instrText")
_FLD_SIMPLE = _w("fldSimple")
_CONTENTS = frozenset({"contents", "table of contents"})


@dataclass
class ReportUnit:
    """회의 보고서의 그림 단위 하나 — 그 단위를 담은 최상위 블록 번호와 그림 파일로 둘 것."""
    block: int
    kind: str
    #: 단위가 그리는 그림 관계 id — 캡션 짝(offset -1)이 이미 가진 그림과 겹치는지 가리는 데 쓴다.
    rids: tuple
    #: 그림 파일로 둘 부품 이름, `figures` 와 같은 차례(그림 부품 · 없으면 대체 그림 · 내용 부품).
    parts: tuple
    #: 부품 없이 도형으로만 그린 단위의 XML.
    drawing: bytes
    #: 그림 없이 DrawingML 차트를 그린 단위 — 회의 보고서에서는 차트 추출기(`chart_extractor`)의 몫이다.
    chart: bool


def report_units(doc) -> list[ReportUnit]:
    """본문의 그림 단위(`_classify` 가 그림으로 치는 것) 전부를 문서 순서로, 담은 최상위 블록 번호와 함께.

    표 칸 · 글상자 안 단위도 들고, 크기 하한이 없다. 수식 단위(`ole_eq` · `pic_eq`)와 낱 도형 · 글상자는
    `figures` 와 같이 빠진다.
    """
    rels = doc.part.rels
    out = []
    for e in events(doc):
        if not (e.obj and e.figure):
            continue
        own = _parts(doc, e.rids)
        parts = tuple(dict.fromkeys(own + (() if own else _parts(doc, e.fallback_rids)) + _parts(doc, e.source_rids)))
        drawing = b""
        if not parts and e.node is not None and not (e.rids or e.source_rids or e.fallback_rids):
            drawing = etree.tostring(e.node, xml_declaration=True, encoding="UTF-8", standalone=True)
        chart = not e.rids and any(r in rels and rels[r].reltype == _CHART_REL for r in e.source_rids)
        out.append(ReportUnit(block=e.block, kind=e.kind, rids=e.rids, parts=parts, drawing=drawing, chart=chart))
    return out


def save_report_parts(unit: ReportUnit, package_parts: dict, output_dir,
                      figure_id: str, *, primary_part: str, write_bytes) -> list:
    """캡션 그림의 기본 파일은 유지하고 같은 단위의 추가 부품만 저장한다.

    P2의 기존 그림 ID와 파일명을 유지한다. 반복된 부품 이름은 한 번 저장하고,
    부품 이름의 SHA-256을 파일명에 넣어 같은 확장자·다른 그림 단위 사이의 충돌도 피한다.
    제공된 미디어·XML 보존은 차트나 도형의 독립 렌더링을 의미하지 않는다.
    """
    import hashlib
    from pathlib import Path

    if output_dir is None:
        return []
    if not figure_id or Path(figure_id).name != figure_id or "\\" in figure_id or figure_id in {".", ".."}:
        raise ValueError(f"Invalid report figure ID: {figure_id}")
    output_dir = Path(output_dir)
    parts = tuple(dict.fromkeys(unit.parts))
    files = []
    paths = set()
    for name in parts:
        if name == primary_part:
            continue
        part = package_parts[name]
        identity = hashlib.sha256(name.encode("utf-8")).hexdigest()
        path = output_dir / f"{figure_id}__part_{identity}{Path(name).suffix or '.bin'}"
        if path in paths:
            raise ValueError(f"Duplicate report figure part path: {path}")
        paths.add(path)
        files.append((path, part.blob))
    if unit.drawing:
        path = output_dir / f"{figure_id}__drawing.xml"
        if path in paths:
            raise ValueError(f"Duplicate report figure drawing path: {path}")
        files.append((path, unit.drawing))
    if files:
        output_dir.mkdir(parents=True, exist_ok=True)
    for path, blob in files:
        write_bytes(path, blob)
    return [path for path, _ in files]


def cover_end(doc) -> int:
    """표지(로고 · 회의 정보)가 끝나는 본문 최상위 블록 번호 — 목차의 시작과 첫 절 제목 가운데 앞선 것. 둘 다 없으면 0.

    목차 블록은 처음으로 목차 필드(`TOC` 필드 코드 · 단순 필드), 목차 문서 조각(`docPartGallery` 'Table of
    Contents'), 목차 문단 스타일('toc N' · 'TOC Heading'), 'Contents' · 'Table of contents' 한 줄 글 가운데
    하나를 가진 블록이다. 절 제목은 `_heading_styles` 스타일을 쓴 최상위 문단이다.

    > 주의: 목차가 있는 보고서에서 경계를 첫 절 제목만으로 잡으면 RAN1#88 이후 보고서의 목차 뒤 · 첫 절 앞에 놓인
    > 회의 주간 일정표 그림이 빠지므로 목차 시작이 먼저 온다. 목차가 없는 보고서(RAN4 · RAN5 의 다수)는 첫 절
    > 제목이 경계이고, 이를 0 으로 두면 RAN5 표지 로고가 그림으로 남는다. 로고처럼 여러 회의에 되풀이되는 그림을
    > 해시로 가리는 규칙은 회의마다 같은 그림을 다시 실은 RAN4 본문 그림까지 지운다. 이 경계 앞 그림은 측정한
    > RAN1 · RAN2 · RAN3 · RAN5 보고서 모두에서 3GPP 로고였고, RAN4 보고서에는 경계 앞 그림이 없었다.
    """
    names = {s.style_id: (s.name or "").lower() for s in doc.styles}
    heads = _heading_styles(doc)
    for n, b in enumerate(docx_text.iter_blocks(doc.element.body)):
        for el in b.iter(_w("pStyle")):
            sid = el.get(_VAL) or ""
            nm = names.get(sid, sid.lower())
            if nm == "toc heading" or (nm.startswith("toc ") and nm[4:].strip().isdigit()):
                return n
        if b.tag == _P:
            ps = b.find(_P_STYLE)
            if ps is not None and ps.get(_VAL) in heads:
                return n
        if any((it.text or "").strip().upper().startswith("TOC") for it in b.iter(_INSTR)):
            return n
        if any(f.get(_w("instr"), "").strip().upper().startswith("TOC") for f in b.iter(_FLD_SIMPLE)):
            return n
        if any("Contents" in (g.get(_VAL) or "") for g in b.iter(_TOC_GALLERY)):
            return n
        if b.tag == _P and docx_text.final_text(b).strip().lower() in _CONTENTS:
            return n
    return 0


def index_entry(f) -> dict:
    """그림 색인(`figures/index.json`)의 항목 하나 — Spec 「렌더링용 저장 구조」 절의 camelCase 키
    (RAN1 · RAN2 · RAN3 §3.6, RAN4 · RAN5 §3.4).

    03 이 쓰는 색인과 04 가 다시 얻어 대조하는 색인이 모두 이 함수로 만든다. 두 자리가 키를 따로 적으면
    한쪽만 바뀌어 04 가 모든 문서를 낡은 색인으로 거절한다. `moreFilePaths` 는 단위가 그림 부품을 둘 이상
    그릴 때만 둔다 — 그림 하나짜리 항목은 키 넷 그대로다.
    """
    entry = {
        'figureId': f.figure_id,
        'figureNumber': f.figure_number,
        'caption': f.caption,
        'filePath': f.file_path,
    }
    if f.more_file_paths:
        entry['moreFilePaths'] = list(f.more_file_paths)
    return entry


def bundle(groups, tdoc_number: str) -> list[list]:
    """문서 묶음의 그림 목록들 → 한 TDoc 의 그림 목록(문서마다 한 목록). 번호는 문서 차례로 이어
    `FIG-{tdoc}-{순번:03d}`, 둘째 문서의 그림 파일은 `media/cover/…`, 셋째부터는 `media/cover{k}/…` 로 옮긴다.

    항목은 `dataclasses.replace` 로 바꾸므로 `Figure` 와 파서의 `FigureInfo` 둘 다 받는다. 파싱(03)과 그림 보강(04)이
    같은 함수로 색인을 만든다 — 두 자리가 번호 · 경로를 따로 지으면 04 가 03 의 색인을 낡았다고 거절한다.

    > 주의: 묶음 문서는 저마다 `/word/media/image1.png` 를 가질 수 있다. 같은 경로로 두면 표지의 그림 파일이
    > 바탕 문서의 그림을 덮으므로 둘째 문서부터 하위 폴더로 옮긴다.
    """
    out, n = [], 0
    for k, figs in enumerate(groups):
        sub = "" if k == 0 else ("cover" if k == 1 else f"cover{k}")

        def move(p):
            if not sub or not p:
                return p
            if not p.startswith("media/"):
                raise ValueError(f"그림 파일 경로가 media/ 밖: {p}")
            return f"media/{sub}/" + p[len("media/"):]
        group = []
        for f in figs:
            n += 1
            group.append(replace(f, figure_id=f"FIG-{tdoc_number}-{n:03d}", file_path=move(f.file_path),
                                 more_file_paths=tuple(move(p) for p in f.more_file_paths)))
        out.append(group)
    return out


def table_captions(texts: list[str], styles: list[str], before: list[int], n_tables: int) -> list[tuple[str, str]]:
    """최상위 표마다 (캡션 번호 글, 캡션 문단 글) — 캡션이 없으면 ("", "").

    texts · styles · before 는 본문 최상위 문단마다의 확정 글 · 스타일 이름 · 그 앞 최상위 표 수다.
    표 바로 위(앞 표 뒤 · 이 표 앞의 마지막 글 있는 문단)가 표 캡션이면 그것을, 아니면 바로 아래(이 표 뒤 · 다음
    표 앞의 첫 글 있는 문단)가 표 캡션이면 그것을 고른다. 바로 아래 문단이 다음 표의 바로 위 문단이기도 하면
    다음 표의 캡션이다 — 위 캡션이 3GPP 표 제목(TH) 관례다. 예외는 사슬(모듈 설명 '표 캡션')이다.
    """
    above, below = {}, {}
    for i, t in enumerate(texts):
        if t:
            above[before[i]] = i
            below.setdefault(before[i] - 1, i)

    def read(i):
        if i is None:
            return None
        num = caption.tdoc_number("table", texts[i], styles[i])
        return None if num is None else (num, texts[i].strip())

    # 표 ti 와 ti+1 이 사이의 글 있는 문단 하나를 나눠 갖고 그것이 표 캡션이면 한 사슬로 잇는다.
    link = [ti + 1 < n_tables and below.get(ti) is not None and below.get(ti) == above.get(ti + 1)
            and read(below.get(ti)) is not None for ti in range(n_tables)]
    out: list[tuple[str, str]] = []
    ti = 0
    while ti < n_tables:
        tj = ti
        while link[tj]:
            tj += 1
        if tj > ti and read(above.get(ti)) is None and read(below.get(tj)) is not None:
            out += [read(below.get(k)) for k in range(ti, tj + 1)]
        else:
            for k in range(ti, tj + 1):
                got = read(above.get(k))
                if got is None:
                    b = below.get(k)
                    if b is not None and not (k + 1 < n_tables and above.get(k + 1) == b):
                        got = read(b)
                out.append(got or ("", ""))
        ti = tj + 1
    return out
