"""OLE 수식 개체를 선형 수식 글로 읽는다 — 청크 본문(`docx_text.chunk_text`)이 수식 개체 자리에 넣는 글.

Equation Editor 3(`Equation.3`) · MathType(`Equation.DSMT4`)으로 넣은 수식은 OMML(`m:oMath`)이 아니라 OLE 개체
(`w:object` 안 `o:OLEObject`)다. 개체 부품은 복합 파일(MS-CFB)이고 그 안 `Equation Native` 스트림에 수식이
MTEF 로 들어 있다. 화면에 보이는 것은 `v:imagedata` 가 가리키는 미리보기 그림(WMF · EMF)이다. 문단 글로 읽으면
수식이 통째로 빠진다.

어느 쪽을 읽는가(`STATS` 의 이름):
    native    MTEF 를 풀어(`mtef_linear`) 빈 글이 아니고, 그 글자 · 숫자가 미리보기 그림에 그린 글자 · 숫자와 같다
              (`same_letters`). 미리보기가 WMF · EMF 가 아니거나 없으면 견줄 것이 없어 해독 글을 쓴다.
    preview   `Equation Native` 가 없거나 비었거나 풀리지 않거나, 해독 글이 그림과 다르면 그림을 읽는다(`preview_math`).
              그림이 화면에 보이는 수식이다 — 해독 글이 다른 개체는 MTEF 가 고치기 전 수식을 들고 있는 것이다.
    figure    미리보기가 수식이 아니라 그림이다(`preview_math.figure`). 글을 넣지 않는다.
    empty     MTEF 가 오류 없이 풀려 빈 글이고 미리보기에도 그린 글자가 없는 빈 수식이다. 글을 넣지 않는다.
    unread    둘 다 읽지 못했다. 글을 넣지 않는다.

수식은 OLE 개체 없이 MathType 이 그린 그림(WMF · EMF)으로만 들기도 한다 — `w:drawing` 의 `a:blip` 이나 `w:pict` 의
`v:imagedata` 가 가리키는 그림에 MathType 서명(`docx_text._EQUATION_IMAGE_SIGNS`)이 있다. 수식 개체의 미리보기와 같은
그림이므로 같은 판독기(`preview_math`)로 읽어 그 그림 단위에 글을 단다(`annotate_pictures`, `STATS` 의 이름 앞에
`picture_` 를 붙여 센다). 그림에는 `Equation Native` 가 없어 견줄 해독 글이 없다.
주의: 서명만으로는 모자란다. 문서 조각(본문 · 표 · 도식)을 EMF 로 붙인 그림도 그 안에 MathType 수식을 품으면 서명이
같다. 그런 합친 EMF(`metafile_text.composite`)는 수식 그림이 아니라 그림이다(`docx_text.equation_image_data`).

수식 개체가 든 683 문서의 개체 29,299 개(글상자의 DrawingML · VML 두 벌 194 개 포함)에서 native 29,224 ·
preview 68 · figure 5(38.104 · 38.108 · 38.174 와 38.104 CR 둘의 TH 문단에 수식 편집기로 그린 그림) ·
empty 1(38.211 의 35 바이트 MTEF) · unread 1(RAN1-93 회의 보고서의 `Equation.Ribbit` 개체 — `Equation Native` 가 없고
미리보기에 글자가 없다)이다. MTEF 를 풀다 예외가 난 개체는 없다.

주의: 해독 글에 U+FFFD 가 남는 것은 판독 실패가 아니다. 판 5 글자 레코드의 MTCode 자체가 0xFFFD 이고, MathType 이
그 글리프에 유니코드를 주지 않았다는 뜻이다. p6 수식 3,186,656 개(다섯 WG 전체) 가운데 한 개체에 둘이 있다 —
R1-160342 의 `M_(RB�1)^PUCCH4` 로 MT Extra 0x6E 이고, 미리보기 그림도 같은 MT Extra 0x6E 를 그린다. LibreOffice
`unotools/source/misc/fontcvt.cxx` 의 MT Extra 표도 U+F06E 를 0xFFFD 로 둔다. 근거 없이 다른 글자로 바꾸지 않는다.
"""
from __future__ import annotations

import collections
import re
import struct
import unicodedata

import docx_text
import metafile_text
import mtef
import mtef_linear
import ole_cfb
import preview_math


_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_O = "{urn:schemas-microsoft-com:office:office}"
_V = "{urn:schemas-microsoft-com:vml}"
_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

#: 읽은 개체 수(이 프로세스 몫) — 위 설명의 이름별.
STATS: collections.Counter = collections.Counter()

_FOLD = str.maketrans("ϕϑϵϖϱςϰ", "φθεπρσκ")

#: XML 1.0 의 Char 가 아닌 글자 — 제어 문자(탭 · 줄바꿈 · 복귀 말고), 짝 없는 대리 쌍, U+FFFE · U+FFFF. 읽은 글을
#: 속성으로 달 때 lxml 이 이런 글자를 거부해(`ValueError`) 문서 전체가 열리지 않는다.
#: 주의: 이런 글자는 수식의 글자가 아니라 선형 표기 도우미(`docx_text._seq` 등)의 내부 표지가 걸러지지 않고 남은
#: 것이다 — 38.523-1 의 MTEF 행렬 한 개(Rel-17 · 18 · 19 세 판)가 빈 칸 앞 쉼표를 지운 자리 표지 `\x04` · `\x05` 로
#: 감싼 채 나왔다. 걷어 낸 글은 표지를 뺀 글(`docx_text._plain`)과 같다 — OMML 행렬이 빈 칸 앞 쉼표를 그대로 두는 것과
#: 같은 읽기다.
_XML_BAD = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]")


def xml_text(s: str) -> str:
    """속성 값으로 달 수 있게 XML 1.0 이 받지 않는 글자(`_XML_BAD`)를 걷는다. 걷은 자리 수는 `STATS["xml_stripped"]`."""
    out, n = _XML_BAD.subn("", s)
    if n:
        STATS["xml_stripped"] += n
    return out


def _letters(s: str) -> collections.Counter:
    s = unicodedata.normalize("NFD", s).translate(_FOLD)
    return collections.Counter(c for c in s
                               if c.isalnum() and unicodedata.category(c) not in ("Lm", "Mn", "Mc", "Me"))


def same_letters(native: str, drawn: str) -> bool:
    """해독 글과 그린 글의 글자 · 숫자 다중집합이 같은가. 꾸밈표 · 수식 기호 · 괄호 · 빈칸은 견주지 않는다 — 미리보기는
    꾸밈표를 따로 그리고 괄호를 조각으로 그린다. 그리스 글자의 변형 꼴(ϕ · ϑ · ϵ · ϖ · ϱ · ς · ϰ)은 기본 꼴로 맞춘다 —
    맞추지 않으면 해독 글과 그림이 같은 개체 68 개가 다르다고 갈린다."""
    return _letters(native) == _letters(drawn)


def equation_text(ole: bytes | None, picture: bytes | None) -> tuple[str, str]:
    """개체 부품 바이트와 미리보기 그림 바이트(없으면 None)로 (글, 읽은 쪽)."""
    native = ""
    blank = False
    if ole:
        try:
            stream = ole_cfb.streams(ole).get("Equation Native")
            if stream:
                native = mtef_linear.linear(mtef.Eqn(stream))[0]
                blank = not native
        except (ole_cfb.CFBError, ValueError, struct.error, IndexError, KeyError):
            native = ""
    drawn = metafile_text.text(picture) if picture else None
    if native and (drawn is None or same_letters(native, "".join(drawn[0]))):
        return native, "native"
    if picture is None:
        return "", "unread"
    notes: list[str] = []
    shown = preview_math.read(picture, notes)
    if shown:
        return shown, "preview"
    if shown is None:
        return "", "figure" if "figure" in notes else "unread"
    return "", "empty" if blank else "unread"


def _native_part(data: bytes | None) -> bool:
    """개체 부품이 `Equation Native`(MTEF) 스트림을 가진 복합 파일인가."""
    if not data or data[:8] != ole_cfb.SIG:
        return False
    try:
        return "Equation Native" in ole_cfb.streams(data)
    except (ole_cfb.CFBError, struct.error, IndexError):
        return False


#: 수식 그림을 달 그림 단위 — 그림 · VML 그림. 수식 개체(`w:object`) 안 미리보기는 개체 쪽이 읽는다.
_PICTURE_UNITS = (_W + "drawing", _W + "pict")


def _metafile(data: bytes) -> bool:
    """WMF(자리 머리 있음 · 없음) · EMF 바이트인가 — `metafile_text` 가 읽는 두 꼴."""
    return (data[:4] == b"\xd7\xcd\xc6\x9a" or data[:2] in (b"\x01\x00", b"\x02\x00")
            or (data[:4] == b"\x01\x00\x00\x00" and data[40:44] == b" EMF"))


def annotate_pictures(root, blob) -> int:
    """트리 안 그림 단위(`w:drawing` · `w:pict`) 가운데 그리는 그림이 모두 MathType 수식 그림인 것마다 그림을 읽은
    글을 `docx_text.EQUATION_TEXT` 속성으로 단다. 속성을 단 단위 수를 돌려준다.

    단위 안 그림은 `docx_text._drawn_parts` 가 모으는 것(글상자 안은 빼고)이다. 하나의 그림 꼴(차트 · 캔버스 · 도형
    묶음)이거나 OLE 개체 · 글상자를 담은 단위는 달지 않는다 — 그 안 수식 그림은 그림의 일부거나 글상자 문단이 읽는다.
    그림이 여럿이면(드물다) 모두 읽혀야 빈칸으로 이어 단다. 읽은 쪽은 `STATS` 에 `picture_text` · `picture_figure`
    (기울인 글이 있는 그림) · `picture_empty` · `picture_unread` 로 센다.
    주의: 그림 바이트에 MathType 서명이 있어야 한다. 서명은 MathType 이 그린 그림의 주석 레코드(`MathType`)에 있고,
    PNG · GIF · JPEG 그림은 서명이 있어도 metafile 이 아니라 읽지 않는다. 서명이 있어도 수식이 그림의 일부인 합친 EMF
    (`docx_text.equation_image_data`)는 그림이다 — 바깥 글이 본문 조각 · 표 · 도식이라 수식으로 읽으면 엉뚱한 글이 된다.
    """
    verdict: dict = {}

    def equation_picture(rid):
        if rid not in verdict:
            data = blob(rid) if rid else None
            verdict[rid] = data if data and _metafile(data) and docx_text.equation_image_data(data) else None
        return verdict[rid]

    marked = 0
    for unit in root.iter(*_PICTURE_UNITS):
        boxes: list = []
        oles: list = []
        images: list = []
        if docx_text._drawn_parts(unit, boxes, oles, images) or oles or boxes or not images:
            continue
        datas = [equation_picture(rid) for rid in images]
        if not all(datas):
            continue
        shown = []
        for data in datas:
            notes: list[str] = []
            text = preview_math.read(data, notes)
            kind = ("text" if text else "empty" if text == "" else "figure" if "figure" in notes else "unread")
            STATS["picture_" + kind] += 1
            shown.append(text)
        if all(shown):
            unit.set(docx_text.EQUATION_TEXT, xml_text(" ".join(shown)))
            marked += 1
    return marked


def annotate(root, blob) -> int:
    """트리 안 수식 개체마다 읽은 글을 `docx_text.EQUATION_TEXT` 속성으로 단다. `blob(rid)` 은 관계 번호의 부품
    바이트(없으면 None). 속성을 단 개체 수(수식 그림 단위 `annotate_pictures` 포함)를 돌려준다.

    수식 개체는 `o:OLEObject` 의 ProgID 가 `Equation.` 으로 시작하는 개체와, ProgID 가 그렇지 않아도 개체 부품에
    `Equation Native` 스트림이 있는 개체다. 뒤쪽에는 `docx_text.EQUATION_OBJECT` 도 달아 그림 표지가 `[EQUATION]` 이
    되게 한다(`docx_text.equation_ole`).
    주의: ProgID 만 보면 안 된다. 변환을 거친 문서는 수식 개체의 ProgID 를 비워 두거나 `Unknown` 으로 적는다.
    회의 보고서 280개 가운데 10개의 수식 개체 71개(빈 ProgID 69 · `Unknown` 2), TS · TR 347개 가운데 TR 4개의
    58개, CR 13개(RAN1 6 · RAN5 6 · RAN4 1)의 1,269개, TDoc docx 4,699개(RAN1 2,076 · RAN4 1,847 · RAN5 560 ·
    RAN2 201 · RAN3 15)의 73,490개가 그랬다. ProgID 가 다른 종류 이름인 수식 개체도 있다
    (`Msxml2.SAXXMLReader.6.0` · `Visio.Drawing.11` · `Word.Picture.8` 안의 수식 스트림, 점 없는 `Equation`).
    이 개체들은 `[FIGURE]` 로 적히고 청크 본문에서 수식 글이 빠졌다. 부품 안 `\x01CompObj` 의
    이름은 대부분 `Equation.DSMT4` 지만 그 이름을 읽지 못하는 개체도 있어(TS · TR 21개) 수식 스트림으로 가린다.
    """
    marked = annotate_pictures(root, blob)
    for obj in root.iter(_W + "object"):
        ole = next(obj.iter(_O + "OLEObject"), None)
        if ole is None:
            continue
        part = blob(ole.get(_R + "id"))
        named = (ole.get("ProgID") or "").startswith("Equation.")
        if not named:
            if not _native_part(part):
                continue
            ole.set(docx_text.EQUATION_OBJECT, "1")
        img = next(obj.iter(_V + "imagedata"), None)
        text, kind = equation_text(part, blob(img.get(_R + "id")) if img is not None and img.get(_R + "id") else None)
        text = xml_text(text)
        STATS[kind] += 1
        if text:
            obj.set(docx_text.EQUATION_TEXT, text)
        marked += bool(text) or not named
    return marked
