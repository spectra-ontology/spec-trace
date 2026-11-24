"""OLE 개체 미리보기 그림(WMF · EMF)에 그려진 글자를 뽑는다 — MTEF 해독 결과를 맞대 보는 독립 증거.

WMF: META_CREATEFONTINDIRECT(0x02FB)로 만든 글꼴을 개체 표 번호로 기억하고(META_DELETEOBJECT 0x01F0 은 비운다),
META_SELECTOBJECT(0x012D)로 고른 글꼴로 META_TEXTOUT(0x0521) · META_EXTTEXTOUT(0x0A32)의 바이트를 읽는다.
EMF: EMR_EXTCREATEFONTINDIRECTW(82) · EMR_SELECTOBJECT(37) · EMR_EXTTEXTOUTW(84, UTF-16) · EMR_EXTTEXTOUTA(83).
Symbol 글꼴 글자는 `symbol_fonts` 대응표로 바꾸고, 대응표가 없는 기호 글꼴(MT Extra …)은 (글꼴, 부호)로 남긴다.
MT Extra 는 문자 집합이 기호(2)가 아니어도 기호 글꼴이다 — 38.214 미리보기는 MT Extra(문자 집합 1)의 `K` 로 `…` 를 그린다.
"""
import struct

import symbol_fonts

#: 글 맞춤의 「현재 위치 사용」 비트 — 켜져 있으면 글 기록의 좌표 대신 펜 위치에 그리고 펜을 글 너비만큼 옮긴다.
#: MathType(Equation.DSMT4) 미리보기는 글 맞춤 25(기준선 24 + 이 비트), Equation Editor 3 은 24 다(38.211 · 38.214 · 38.104).
TA_UPDATECP = 1

#: 대응표 없이 기호를 그리는 글꼴 — 문자 집합 값과 상관없이 글로 읽지 않는다
SYMBOL_FACES = {"MT Extra"}

CODEPAGE = {0: "cp1252", 1: "cp1252", 161: "cp1253", 162: "cp1254", 177: "cp1255", 178: "cp1256",
            186: "cp1257", 204: "cp1251", 238: "cp1250", 128: "cp932", 129: "cp949", 134: "gbk", 136: "cp950",
            222: "cp874"}


class Font:
    def __init__(self, face: str, charset: int, height: int = 0, italic: bool = False):
        self.face, self.charset, self.height, self.italic = face, charset, abs(height), italic
        self.tab = symbol_fonts.table(face)
        self.esc = 0


def _plain(font) -> bool:
    """기호 글꼴이 아니라 부호를 글자 그대로 읽는 글꼴인가"""
    return font is None or (font.tab is None and not (font.charset == 2 or font.face in SYMBOL_FACES))


def _pair_dx(raw: bytes, dx):
    """UTF-16 대리 쌍(높은 반쪽 + 낮은 반쪽)은 글자 하나이므로 두 반쪽의 간격을 더해 글자 하나의 간격으로 합친다."""
    codes = struct.unpack(f"<{len(raw) // 2}H", raw[:len(raw) // 2 * 2])
    out, i = [], 0
    while i < len(dx):
        if i + 1 < len(dx) and 0xD800 <= codes[i] <= 0xDBFF and 0xDC00 <= codes[i + 1] <= 0xDFFF:
            out.append(dx[i] + dx[i + 1])
            i += 2
        else:
            out.append(dx[i])
            i += 1
    return out


def _decode(font, raw: bytes, wide: bool):
    """(글자열, 대응표 없는 기호 글꼴 부호 목록)"""
    codes = list(struct.unpack(f"<{len(raw) // 2}H", raw[:len(raw) // 2 * 2])) if wide else list(raw)
    if font is not None and font.tab is not None:
        out = []
        for c in codes:
            # 대응표 글꼴에 대리 반쪽이 오면 글자 하나로 묶을 수 없으므로 U+FFFD 로 둔다(부호 하나에 글자 하나는 지킨다)
            out.append(symbol_fonts.glyph(font.tab, c) or ("\ufffd" if 0xD800 <= c <= 0xDFFF else chr(c)))
        return "".join(out), []
    if font is not None and (font.charset == 2 or font.face in SYMBOL_FACES):
        return "", [(font.face, c) for c in codes]
    if wide:
        # 주의: 부호 단위(16비트)마다 chr() 로 바꾸면 수학 글자(𝑃 = D835 DC43 같은 기본 다국어 평면 밖 글자)가 대리 반쪽 둘로 갈라진다.
        # 갈라진 반쪽은 UTF-8 로 쓸 수 없어 기록이 멈추고, 글자 간격(dx)마다 따로 놓이면 서로 떨어져 다시 붙지 못한다.
        # 그래서 UTF-16 으로 한꺼번에 풀어 쌍을 한 글자로 묶고, 짝 없는 반쪽은 U+FFFD 로 둔다(간격은 _pair_dx 가 맞춘다).
        return raw[:len(raw) // 2 * 2].decode("utf-16-le", errors="replace"), []
    cp = CODEPAGE.get(font.charset if font else 0, "cp1252")
    return raw.decode(cp, errors="replace"), []


def _wmf(b: bytes):
    i = 22 if b[:4] == b"\xd7\xcd\xc6\x9a" else 0
    hdr_words, = struct.unpack_from("<H", b, i + 2)
    i += hdr_words * 2
    objs: list = []
    cur = None
    texts, odd, runs, strokes = [], [], [], []
    pen = (0, 0)
    align = 0
    while i + 6 <= len(b):
        size, func = struct.unpack_from("<IH", b, i)
        if size < 3:
            break
        prm = b[i + 6:i + size * 2]
        if func == 0x0000:
            break
        if func in (0x00F7, 0x01F9, 0x02FA, 0x02FB, 0x02FC, 0x06FF, 0x0142):
            obj = None
            if func == 0x02FB and len(prm) >= 18:
                face = prm[18:50].split(b"\0", 1)[0].decode("latin-1")
                # LogFont: Height(0) … Italic(10) … CharSet(13) · FaceName(18)
                obj = Font(face, prm[13], struct.unpack_from("<h", prm, 0)[0], bool(prm[10]))
                obj.esc = struct.unpack_from("<h", prm, 4)[0]  # LogFont Escapement(4): 글 줄의 기울기, 0.1도 단위
            slot = next((k for k, o in enumerate(objs) if o is False), None)
            if slot is None:
                objs.append(obj if obj is not None else True)
            else:
                objs[slot] = obj if obj is not None else True
        elif func == 0x01F0 and len(prm) >= 2:
            k, = struct.unpack_from("<H", prm, 0)
            if k < len(objs):
                if objs[k] is cur:
                    cur = None
                objs[k] = False
        elif func == 0x012D and len(prm) >= 2:
            k, = struct.unpack_from("<H", prm, 0)
            if k < len(objs) and isinstance(objs[k], Font):
                cur = objs[k]
        elif func == 0x012E and len(prm) >= 2:  # META_SETTEXTALIGN
            align, = struct.unpack_from("<H", prm, 0)
        elif func == 0x0214 and len(prm) >= 4:  # META_MOVETO
            y, x = struct.unpack_from("<hh", prm, 0)
            pen = (x, y)
        elif func == 0x0213 and len(prm) >= 4:  # META_LINETO
            y, x = struct.unpack_from("<hh", prm, 0)
            strokes.append([pen, (x, y)])
            pen = (x, y)
        elif func in (0x0325, 0x0324) and len(prm) >= 2:  # META_POLYLINE · META_POLYGON
            n, = struct.unpack_from("<h", prm, 0)
            v = struct.unpack_from(f"<{2 * n}h", prm, 2) if len(prm) >= 2 + 4 * n else ()
            strokes.append(list(zip(v[0::2], v[1::2])))
        elif func == 0x041B and len(prm) >= 8:  # META_RECTANGLE: bottom, right, top, left
            b_, r_, t_, l_ = struct.unpack_from("<hhhh", prm, 0)
            strokes.append([(l_, t_), (r_, t_), (r_, b_), (l_, b_)])
        elif func == 0x0538 and len(prm) >= 2:  # META_POLYPOLYGON
            n, = struct.unpack_from("<H", prm, 0)
            counts = struct.unpack_from(f"<{n}H", prm, 2)
            j = 2 + 2 * n
            for c in counts:
                v = struct.unpack_from(f"<{2 * c}h", prm, j)
                strokes.append(list(zip(v[0::2], v[1::2])))
                j += 4 * c
        elif func == 0x0521 and len(prm) >= 2:
            n, = struct.unpack_from("<H", prm, 0)
            t, o = _decode(cur, prm[2:2 + n], False)
            j = 2 + n + (n & 1)
            y, x = struct.unpack_from("<hh", prm, j) if len(prm) >= j + 4 else (0, 0)
            if align & TA_UPDATECP:
                x, y = pen
            texts.append(t)
            odd += o
            runs.append((x, y, t, o, cur.height if cur else 0, None, prm[2:2 + n], cur, align))
        elif func == 0x0A32 and len(prm) >= 8:
            y, x, n, opts = struct.unpack_from("<hhhH", prm, 0)
            j = 8 + (8 if opts & 0x6 else 0)
            t, o = _decode(cur, prm[j:j + max(n, 0)], False)
            texts.append(t)
            odd += o
            k = j + n + (n & 1)  # 글자 간격(Dx) 배열은 짝수로 채운 글 뒤에 있으면 있다
            dx = list(struct.unpack_from(f"<{n}h", prm, k)) if n > 0 and len(prm) >= k + 2 * n else None
            if align & TA_UPDATECP:
                x, y = pen
                if dx:
                    pen = (x + sum(dx), y)
            runs.append((x, y, t, o, cur.height if cur else 0, dx, prm[j:j + max(n, 0)], cur, align))
        i += size * 2
    return texts, odd, runs, strokes


def _emf(b: bytes):
    i = 0
    objs: dict = {}
    cur = None
    texts, odd, runs, strokes = [], [], [], []
    pen = (0, 0)
    align = 0
    while i + 8 <= len(b):
        typ, size = struct.unpack_from("<II", b, i)
        if size < 8:
            break
        rec = b[i:i + size]
        if typ == 14:  # EMR_EOF
            break
        if typ == 82 and len(rec) >= 104:
            ih, = struct.unpack_from("<I", rec, 8)
            charset = rec[12 + 23]
            face = rec[40:104].decode("utf-16-le", errors="replace").split("\0", 1)[0]
            objs[ih] = Font(face, charset, struct.unpack_from("<i", rec, 12)[0], bool(rec[12 + 20]))  # LogFontW: Italic(20)
            objs[ih].esc = struct.unpack_from("<i", rec, 12 + 8)[0]  # LogFontW Escapement(8)
        elif typ == 37:
            ih, = struct.unpack_from("<I", rec, 8)
            if ih in objs:
                cur = objs[ih]
        elif typ == 40:
            ih, = struct.unpack_from("<I", rec, 8)
            if objs.get(ih) is cur:
                cur = None
            objs.pop(ih, None)
        elif typ == 22:  # EMR_SETTEXTALIGN
            align, = struct.unpack_from("<I", rec, 8)
        elif typ == 27:  # EMR_MOVETOEX
            pen = struct.unpack_from("<ii", rec, 8)
        elif typ == 54:  # EMR_LINETO
            q = struct.unpack_from("<ii", rec, 8)
            strokes.append([pen, q])
            pen = q
        elif typ in (86, 87, 85, 88, 3, 4, 2, 5):  # POLYGON16 · POLYLINE16 · POLYBEZIER16 · POLYBEZIERTO16 · 32비트 꼴
            n, = struct.unpack_from("<I", rec, 24)
            fmt, w = ("h", 2) if typ >= 85 else ("i", 4)
            v = struct.unpack_from(f"<{2 * n}{fmt}", rec, 28) if len(rec) >= 28 + 2 * w * n else ()
            strokes.append(list(zip(v[0::2], v[1::2])))
        elif typ == 91:  # EMR_POLYPOLYGON16
            nn, _tot = struct.unpack_from("<II", rec, 24)
            counts = struct.unpack_from(f"<{nn}I", rec, 32)
            j = 32 + 4 * nn
            for c in counts:
                v = struct.unpack_from(f"<{2 * c}h", rec, j)
                strokes.append(list(zip(v[0::2], v[1::2])))
                j += 4 * c
        elif typ == 43:  # EMR_RECTANGLE
            l_, t_, r_, b_ = struct.unpack_from("<iiii", rec, 8)
            strokes.append([(l_, t_), (r_, t_), (r_, b_), (l_, b_)])
        elif typ in (83, 84) and len(rec) >= 76:
            x, y, n, off = struct.unpack_from("<iiII", rec, 36)
            raw = rec[off:off + n * (2 if typ == 84 else 1)]
            t, o = _decode(cur, raw, typ == 84)
            texts.append(t)
            odd += o
            opts, = struct.unpack_from("<I", rec, 52)
            offdx, = struct.unpack_from("<I", rec, 72)
            step = 2 if opts & 0x2000 else 1  # ETO_PDY: 간격마다 (x, y) 둘
            dx = (list(struct.unpack_from(f"<{n * step}i", rec, offdx))[::step]
                  if n > 0 and offdx and len(rec) >= offdx + 4 * n * step else None)
            if dx and typ == 84 and _plain(cur):
                dx = _pair_dx(raw, dx)
            if align & TA_UPDATECP:
                x, y = pen
                if dx:
                    pen = (x + sum(dx), y)
            runs.append((x, y, t, o, cur.height if cur else 0, dx, raw, cur, align))
        i += size
    return texts, odd, runs, strokes


def _read(blob: bytes):
    if blob[:4] == b"\x01\x00\x00\x00" and blob[40:44] == b" EMF":
        return _emf(blob)
    if blob[:4] == b"\xd7\xcd\xc6\x9a" or blob[:2] in (b"\x01\x00", b"\x02\x00"):
        return _wmf(blob)
    return None


def text(blob: bytes):
    """(그려진 글 조각 목록, 대응표 없는 기호 글꼴 (글꼴, 부호) 목록). WMF · EMF 가 아니면 None."""
    got = _read(blob)
    return None if got is None else got[:2]


def runs(blob: bytes):
    """그려진 글 조각마다 (x, y, 글, 대응표 없는 기호 글꼴 부호 목록, 글꼴 높이, 글자 간격 목록 또는 None, 원 바이트, 글꼴, 글 맞춤 TA_*)
    — 좌표는 그림 기록의 논리 좌표(글 기준점). 아니면 None."""
    got = _read(blob)
    return None if got is None else got[2]


def strokes(blob: bytes):
    """그려진 선 · 다각형마다 꼭짓점 목록(논리 좌표). 아니면 None."""
    got = _read(blob)
    return None if got is None else got[3]


#: EMF+ 레코드 종류(EMR_COMMENT 안, MS-EMFPLUS 2.1.1.1) — 개체 정의 · 그림 그리기 · 도형과 글 그리기
_PLUS_OBJECT = 0x4008
_PLUS_IMAGE_DRAW = {0x401A, 0x401B}
_PLUS_DRAW = set(range(0x400A, 0x401A)) | {0x401C, 0x4036}
#: EMF+ 개체 종류 가운데 그림(EmfPlusImage)
_PLUS_IMAGE_OBJECT = 5


def _plus_records(blob: bytes):
    """EMF 의 EMR_COMMENT(70) 안 EMF+ 레코드마다 (종류, 깃발, 자료)."""
    i = 0
    while i + 8 <= len(blob):
        typ, size = struct.unpack_from("<II", blob, i)
        if size < 8:
            return
        if typ == 70 and blob[i + 12:i + 16] == b"EMF+":
            j, end = i + 16, i + size
            while j + 12 <= end:
                ptyp, flags, psize, dsize = struct.unpack_from("<HHII", blob, j)
                if psize < 12:
                    break
                yield ptyp, flags, blob[j + 12:j + 12 + dsize]
                j += psize
        if typ == 14:
            return
        i += size


def _plus_images(blob: bytes):
    """EMF+ 그림 개체마다 안에 든 WMF · EMF 바이트(비트맵이면 None). 이어지는 개체(깃발 0x8000)는 이어 붙인다."""
    whole: dict = {}
    parts: dict = {}
    for ptyp, flags, data in _plus_records(blob):
        if ptyp != _PLUS_OBJECT or (flags >> 8) & 0x7F != _PLUS_IMAGE_OBJECT:
            continue
        oid = flags & 0xFF
        if flags & 0x8000:
            total, = struct.unpack_from("<I", data, 0)
            parts.setdefault(oid, bytearray()).extend(data[4:])
            if len(parts[oid]) >= total:
                whole[oid] = bytes(parts.pop(oid))
        else:
            whole[oid] = bytes(parts.pop(oid, b"")) + data
    out = []
    for data in whole.values():
        if len(data) < 16 or struct.unpack_from("<I", data, 4)[0] != 2:
            out.append(None)
            continue
        size, = struct.unpack_from("<I", data, 12)
        meta = data[16:16 + size]
        # 주의: GDI+ 는 그림 개체 안 WmfPlaceable 머리(22바이트) 뒤에 2바이트를 더 채우고 WMF 머리를 둔다
        # (RAN1#88 회의 보고서 image17). 그 자리에 WMF 머리가 있으면 머리를 떼고 넘긴다.
        if meta[:4] == b"\xd7\xcd\xc6\x9a" and meta[22:24] == b"\x00\x00" and meta[24:26] in (b"\x01\x00", b"\x02\x00"):
            meta = meta[24:]
        out.append(meta)
    return out


def _letters(blob: bytes) -> dict:
    got = runs(blob) or []
    counts: dict = {}
    for r in got:
        for ch in r[2]:
            if ch.isascii() and ch.isalnum():
                counts[ch] = counts.get(ch, 0) + 1
    return counts


def composite(blob: bytes) -> bool:
    """MathType 수식이 그림 전체가 아니라 일부인 EMF 인가 — 그러면 수식 그림이 아니라 그림(`[FIGURE]`)이다.

    MathType 수식을 다른 프로그램(GDI+)으로 옮긴 EMF 는 EMF+ 그림 개체 안에 MathType 이 그린 WMF 를 넣고, 바깥 GDI
    기록에 같은 글을 한 번 더 그린다. 문서 조각을 그림으로 붙인 것(본문 · 표 · 도식)도 그 안에 MathType 수식을 담으면
    서명이 같아 수식 그림으로 보였다. 그래서 EMF+ 가 도형 · 글을 직접 그리거나, 비트맵 그림을 담거나, 바깥에 그린
    영숫자가 안쪽 WMF · EMF 의 영숫자로 다 덮이지 않으면(글자별 개수로 견준다) 합친 그림으로 본다. 안쪽 EMF 가 다시
    합친 그림이어도 그렇다(표 그림을 EMF 로 한 번 더 싼 R1-1708725 image1).
    주의: 서명 있는 EMF 505개(회의 보고서 · TDoc · CR · TS · TR 의 본문 그림 수식 문서) 가운데 안쪽 그림이 하나이고
    바깥 영숫자가 다 덮이는 것은 126개였다. 나머지 EMF+ 그림은 덮인 몫이 0.96 이하였고, 본문 1,200자 조각
    (38.331 CR0388r3 image3)이나 비트 자리 도식(R1-1712526 image3)처럼 수식이 일부인 그림이었다.
    덮인 몫이 0.96 · 0.95 인 둘은 수식 옆에 바깥 글(`[dB]` · `IRR =`)을 더 쓴 그림이라 이 규칙으로는 그림이 된다.
    파서가 읽는 docx 687,963개(`ontology/input` 의 회의 보고서 · CR · TS · TR 과 코퍼스의 TDoc · TS 원본 · TR 원본 · CR 산출)
    전부를 다시 훑으면 서명 있는 EMF 부품은 708개(같은 파일이 여러 폴더에 있으면 따로 셈)이고 그 가운데 522개가 합친 그림이다.
    EMF+ 그림이 없는 서명 EMF(MathType 이 직접 그린 것)와 WMF 는 합친 그림이 아니다.
    """
    if blob[:4] != b"\x01\x00\x00\x00" or blob[40:44] != b" EMF":
        return False
    for ptyp, flags, data in _plus_records(blob):
        if ptyp in _PLUS_DRAW:
            return True
    images = _plus_images(blob)
    if not images:
        return False
    if any(m is None or composite(m) for m in images):
        return True
    inner: dict = {}
    for m in images:
        for ch, n in _letters(m).items():
            inner[ch] = inner.get(ch, 0) + n
    return any(inner.get(ch, 0) < n for ch, n in _letters(blob).items())
