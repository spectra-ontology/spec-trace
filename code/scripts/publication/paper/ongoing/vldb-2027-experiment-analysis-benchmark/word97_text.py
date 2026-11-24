"""Word 97-2003 이진 문서(.doc)의 본문 글을 LibreOffice 없이 바로 읽는다.

TSG 총회 문서 묶음의 옛 .doc 는 LibreOffice 변환이 문서 하나에 몇 분씩 걸리는 일이 잦다(변경 추적이 많은
큰 CR). 본문 글자는 문서 안 글 흐름(`WordDocument` 흐름의 조각표)에 그대로 들어 있으므로, 복합 파일(OLE)을
풀어 조각표를 따라 글자를 읽는다. 규칙은 MS-DOC 명세를 따르며 `raw_source_text.word_text`(OOXML 판독)와
같은 꼴로 내놓는다.

- 본문(주 문서 구간 CP 0 … ccpText)만 읽는다. 머리글 · 바닥글 · 각주 · 메모는 싣지 않는다(청크 파서와 같다).
- 변경 추적으로 지운 글(`sprmCFRMarkDel`)은 `[DEL]…[/DEL]` 로 감싸 함께 둔다.
- 표는 행마다 `| 칸 | 칸 |` 한 줄, 칸 안 문단은 빈칸으로 잇는다. 행 끝은 문단 속성 `sprmPFTtp` 로 가린다.
  OOXML 판독과 달리 세로로 합친 칸의 글을 아래 칸에 되풀이하지 않는다.
- 필드는 결과 글만 남기고 명령 글(`HYPERLINK …` 따위)은 뺀다. 그래서 CR 표지의 문서 속성 필드는 Word 가
  보여 주는 값(`R5-205879` 따위)으로 읽힌다(LibreOffice 변환본에는 `<TDoc#>` 같은 속성 이름이 남는 문서가 있다).
- 수식 개체(Equation.3 · MathType) · 그림 · 떠 있는 도형 · 글상자 글은 싣지 않고, 그 수를 `doc_text(…, stats)` 로
  센다.
- 기호 글꼴 글자는 OOXML 판독과 같은 규칙(`symbol_fonts`)으로 유니코드 글자로 바꾼다. 기호 넣기(`sprmCSymbol`,
  글 흐름에는 자리 표지 글자만 있다)는 그 글꼴 · 부호로, 기호 글꼴로 친 글은 run 에 바로 걸린 글꼴 칸
  (`sprmCRgFtc0/1/2` · `sprmCFtcBi`, 복합 문자 켬은 `sprmCFComplexScripts`)으로 읽는다. 스타일에서 물려받은 글꼴은
  OOXML 판독처럼 보지 않는다. 기호 글꼴 근거가 없는 사용자 영역 글자는 `symbol_fonts.settle_lost_fonts` 처럼 같은
  문서의 기호 근거가 한 대응표만 가리킬 때 그 글자로 읽고, 아니면 적힌 그대로 둔다.

읽지 못하면 `ExtractError(reason)` 를 올린다. Word 6/95 형식과 암호 걸린 문서는 이 판독기의 범위 밖이다.
"""

from __future__ import annotations

import bisect
import struct
import sys
from array import array

from raw_source_text import DEL_CLOSE, DEL_OPEN, ROOT, ExtractError

_COMMON = str(ROOT / "scripts/tsg/RAN/formal/common")
if _COMMON not in sys.path:
    sys.path.insert(0, _COMMON)
import symbol_fonts  # noqa: E402 — OOXML 판독과 같은 기호 글꼴 대응표

OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
FREE = 0xFFFFFFFA  # 이 값 이상은 사슬 끝 · 빈 칸 · FAT 칸 표지다
WORD_IDENT = 0xA5EC
MIN_NFIB = 0x00C1  # Word 97 의 nFib. 이보다 작으면 Word 6/95 형식이다
SPRM_DEL = 0x0800  # sprmCFRMarkDel
SPRM_IN_TABLE = 0x2416  # sprmPFInTable
SPRM_TTP = 0x2417  # sprmPFTtp — 표 행 끝 문단
SPRM_INNER_TTP = 0x244C  # sprmPFInnerTtp — 안쪽 표 행 끝 문단
SPRM_HUGE_PAPX = 0x6646  # sprmPHugePapx — 문단 속성이 Data 흐름에 있다
SPRM_DEF_TABLE = (0xD608, 0xD606)  # 길이를 2바이트로 적는 가변 sprm
SPRM_CHG_TABS = 0xC615
SPRM_FONTS = (0x4A4F, 0x4A51, 0x4A50, 0x4A5E)  # sprmCRgFtc0(ascii) · Ftc2(hAnsi) · Ftc1(eastAsia) · CFtcBi(cs)
SPRM_COMPLEX = 0x0882  # sprmCFComplexScripts — OOXML `w:cs`
SPRM_SYMBOL = 0x6A09  # sprmCSymbol — 글꼴 번호(2바이트) + 부호(2바이트)
CHAR_SPRMS = (SPRM_DEL, *SPRM_FONTS, SPRM_COMPLEX, SPRM_SYMBOL)
FONT_TABLE_PAIR = 15  # FibRgFcLcb97 의 fcSttbfFfn

# 글자 바꾸기: 문단 · 칸 끝 말고 글 흐름에 섞인 표지 글자.
CONTROL = {"\x0b": "\n", "\x0c": "\n", "\x0e": "\n", "\x1e": "-", "\x1f": "", "\t": "\t"}


def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


class Compound:
    """OLE 복합 파일(Compound File Binary). 이름으로 흐름 하나를 꺼낸다."""

    def __init__(self, data: bytes):
        if data[:8] != OLE_MAGIC:
            raise ExtractError("OLE 형식 아님")
        self.data = data
        self.size = 1 << u16(data, 30)
        mini_shift = u16(data, 32)
        self.mini_size = 1 << mini_shift
        fat_count, first_dir = u32(data, 44), u32(data, 48)
        self.cutoff = u32(data, 56)
        first_mini, mini_count = u32(data, 60), u32(data, 64)
        first_difat, difat_count = u32(data, 68), u32(data, 72)
        difat = list(struct.unpack_from("<109I", data, 76))
        sector, per = first_difat, self.size // 4
        for _ in range(difat_count):
            if sector >= FREE:
                break
            entries = struct.unpack_from(f"<{per}I", self._sector(sector))
            difat.extend(entries[:-1])
            sector = entries[-1]
        fat = array("I")
        for index in [s for s in difat[:fat_count] if s < FREE]:
            fat.frombytes(self._sector(index))
        self.fat = fat
        directory = self._chain(first_dir, self.fat, self._sector)
        # 디렉터리 항목: (이름, 종류, 왼쪽 · 오른쪽 형제, 첫 자식, 시작 섹터, 크기). 흐름 이름은 저장소마다 따로라서
        # 끼워 넣은 개체(ObjectPool 아래 Word 문서 따위)의 `WordDocument` 와 섞이지 않게 뿌리 바로 아래만 찾는다.
        nodes = []
        for offset in range(0, len(directory) - 127, 128):
            name_len = u16(directory, offset + 64)
            name = directory[offset:offset + max(name_len - 2, 0)].decode("utf-16-le", "replace") \
                if 2 <= name_len <= 64 else ""
            nodes.append((name, directory[offset + 66], u32(directory, offset + 68), u32(directory, offset + 72),
                          u32(directory, offset + 76), u32(directory, offset + 116), u32(directory, offset + 120)))
        self.stream_names = [node[0].lower() for node in nodes if node[1] == 2]
        self.entries = {}
        root_start = root_size = None
        if nodes and nodes[0][1] == 5:
            root_start, root_size = nodes[0][5], nodes[0][6]
            stack, visited = [nodes[0][4]], set()
            while stack:
                index = stack.pop()
                if index >= len(nodes) or index in visited:
                    continue
                visited.add(index)
                name, kind, left, right, _, start, size = nodes[index]
                stack.extend((left, right))
                if kind == 2:
                    self.entries.setdefault(name.lower(), (start, size))
        self.mini_stream = b""
        if root_start is not None and root_start < FREE:
            self.mini_stream = self._chain(root_start, self.fat, self._sector)[:root_size]
        minifat = array("I")
        if first_mini < FREE and mini_count:
            minifat.frombytes(self._chain(first_mini, self.fat, self._sector))
        self.minifat = minifat

    def _sector(self, index: int) -> bytes:
        start = (index + 1) * self.size
        return self.data[start:start + self.size]

    def _mini(self, index: int) -> bytes:
        start = index * self.mini_size
        return self.mini_stream[start:start + self.mini_size]

    @staticmethod
    def _chain(start: int, table: array, read) -> bytes:
        out, seen, sector = [], set(), start
        while sector < FREE and sector < len(table):
            if sector in seen:
                raise ExtractError("OLE 사슬 고리")
            seen.add(sector)
            out.append(read(sector))
            sector = table[sector]
        return b"".join(out)

    def stream(self, name: str) -> bytes:
        found = self.entries.get(name.lower())
        if found is None:
            raise ExtractError("OLE 흐름 없음", name)
        start, size = found
        if size < self.cutoff:
            return self._chain(start, self.minifat, self._mini)[:size]
        return self._chain(start, self.fat, self._sector)[:size]


def sprm_values(grpprl: bytes, wanted: tuple[int, ...]) -> dict[int, bytes]:
    """sprm 목록에서 찾는 sprm 의 피연산자. 길이 규칙(spra)은 MS-DOC 2.6.1 을 따른다."""
    found: dict[int, bytes] = {}
    pos, end = 0, len(grpprl)
    while pos + 2 <= end:
        sprm = u16(grpprl, pos)
        pos += 2
        spra = sprm >> 13
        if spra in (0, 1):
            size = 1
        elif spra in (2, 4, 5):
            size = 2
        elif spra == 3:
            size = 4
        elif spra == 7:
            size = 3
        elif sprm in SPRM_DEF_TABLE:
            if pos + 2 > end:
                break
            size = u16(grpprl, pos) + 1  # 길이 칸(2바이트) + 나머지(cb - 1)
        elif sprm == SPRM_CHG_TABS:
            if pos >= end:
                break
            if grpprl[pos] == 255:
                break  # 복잡한 탭 바꿈. 뒤의 sprm 은 읽지 않는다
            size = grpprl[pos] + 1
        else:
            if pos >= end:
                break
            size = grpprl[pos] + 1
        if sprm in wanted:
            found[sprm] = grpprl[pos:pos + size]
        pos += size
    return found


def _toggle_on(operand: bytes) -> bool:
    # 켬(1) · 스타일의 반대(0x81). 스타일 기본값은 꺼짐이다.
    return bool(operand) and operand[0] in (1, 0x81)


def _plc(data: bytes, offset: int, length: int, item: int) -> tuple[list[int], list[bytes]]:
    count = (length - 4) // (4 + item)
    if count <= 0:
        return [], []
    points = list(struct.unpack_from(f"<{count + 1}I", data, offset))
    base = offset + 4 * (count + 1)
    return points, [data[base + item * i:base + item * (i + 1)] for i in range(count)]


class Runs:
    """글 흐름 바이트 위치(FC) 구간마다의 값. 겹치지 않는 구간을 시작 위치로 찾는다."""

    def __init__(self, triples: list[tuple[int, int, object]]):
        triples.sort(key=lambda t: t[0])
        self.starts = [t[0] for t in triples]
        self.triples = triples
        self.bounds = sorted({t[0] for t in triples} | {t[1] for t in triples})

    def at(self, fc: int, default=None):
        i = bisect.bisect_right(self.starts, fc) - 1
        if i >= 0:
            start, end, value = self.triples[i]
            if start <= fc < end:
                return value
        return default

    def cuts(self, start: int, end: int) -> list[int]:
        """(start, end) 안에 있는 구간 경계."""
        return self.bounds[bisect.bisect_right(self.bounds, start):bisect.bisect_left(self.bounds, end)]


def _fkp_pages(table: bytes, fc: int, lcb: int) -> list[int]:
    _, items = _plc(table, fc, lcb, 4)
    return [u32(item, 0) & 0x3FFFFF for item in items]


def font_names(table: bytes, fc: int, lcb: int) -> list[str]:
    """글꼴 표(SttbfFfn). 항목은 길이 1바이트 + FFN 이고, FFN 39바이트 뒤가 글꼴 이름(UTF-16, 0 으로 끝남)이다."""
    names: list[str] = []
    if lcb < 4 or fc + lcb > len(table):
        return names
    block = table[fc:fc + lcb]
    count, extra, pos = u16(block, 0), u16(block, 2), 4
    for _ in range(count):
        if pos >= len(block):
            break
        size = block[pos]
        entry = block[pos + 1:pos + 1 + size]
        names.append(entry[39:].decode("utf-16-le", "replace").split("\x00")[0] if size > 39 else "")
        pos += 1 + size + extra
    return names


class CharProps:
    """글자 run 하나의 속성: 지운 글인가, 글꼴 칸 대응표(`symbol_fonts._slot_table` 꼴), 기호 넣기(대응표, 부호)."""

    __slots__ = ("deleted", "fonts", "sym_tab", "sym_code")

    def __init__(self, deleted: bool = False, fonts=None, sym_tab=None, sym_code: int | None = None):
        self.deleted = deleted
        self.fonts = fonts
        self.sym_tab = sym_tab
        self.sym_code = sym_code


PLAIN = CharProps()


def _char_props(values: dict[int, bytes], fonts: list[str]) -> CharProps:
    def font_of(operand: bytes) -> str | None:
        if len(operand) < 2:
            return None
        index = u16(operand, 0)
        return fonts[index] if index < len(fonts) else None

    deleted = _toggle_on(values.get(SPRM_DEL, b""))
    sym_tab = sym_code = None
    operand = values.get(SPRM_SYMBOL)
    if operand and len(operand) == 4:
        sym_tab, sym_code = symbol_fonts.table(font_of(operand)), u16(operand, 2)
    asc, han, ea, cs = (symbol_fonts.table(font_of(values[sprm])) if sprm in values else None
                        for sprm in SPRM_FONTS)
    slots = None
    if asc or han or ea or cs:
        forced = _toggle_on(values.get(SPRM_COMPLEX, b""))
        slots = (asc, han, cs, han or ea or cs or asc, forced)
    if not deleted and slots is None and sym_code is None:
        return PLAIN
    return CharProps(deleted, slots, sym_tab, sym_code)


def _is_pua(code: int) -> bool:
    return 0xF020 <= code <= 0xF0FF


class Lost:
    """글꼴 근거가 없는 사용자 영역 글자 자리. 문단을 맺을 때 문서 안 근거로 읽는다(`symbol_fonts.settle_lost_fonts`)."""

    __slots__ = ("code",)

    def __init__(self, code: int):
        self.code = code


def _symbol_evidence(segments) -> dict[int, set]:
    """문서 안 기호 근거: 아래 바이트 → 그 바이트를 그린 기호 글꼴 대응표 이름들(`settle_lost_fonts` 와 같은 모음)."""
    names = {id(tab): name for name, tab in symbol_fonts.TABLES.items()}
    seen: dict[int, set] = {}

    def note(tab, code: int) -> None:
        if tab is not None and symbol_fonts.glyph(tab, code) is not None:
            seen.setdefault(code & 0xFF, set()).add(names[id(tab)])

    for text, props, *_ in segments:
        if props.sym_code is not None:
            if _is_pua(props.sym_code) or props.sym_code <= 0xFF:
                note(props.sym_tab, props.sym_code)
        elif props.fonts is not None:
            for ch in set(text):
                note(symbol_fonts._slot_table(props.fonts, ch), ord(ch))
    return seen


def char_runs(word: bytes, table: bytes, fc: int, lcb: int, fonts: list[str]) -> Runs:
    """글자 바이트 위치 → `CharProps`(CHPX FKP)."""
    triples = []
    for page_number in _fkp_pages(table, fc, lcb):
        page = word[page_number * 512:page_number * 512 + 512]
        if len(page) < 512:
            continue
        count = page[511]
        points = struct.unpack_from(f"<{count + 1}I", page, 0)
        for j in range(count):
            offset = page[4 * (count + 1) + j] * 2
            props = PLAIN
            if offset:
                size = page[offset]
                props = _char_props(sprm_values(page[offset + 1:offset + 1 + size], CHAR_SPRMS), fonts)
            triples.append((points[j], points[j + 1], props))
    return Runs(triples)


def paragraph_runs(word: bytes, table: bytes, data_stream: bytes, fc: int, lcb: int) -> Runs:
    """문단 끝 바이트 위치 → (표 안인가, 표 행 끝인가)."""
    triples = []
    wanted = (SPRM_IN_TABLE, SPRM_TTP, SPRM_INNER_TTP, SPRM_HUGE_PAPX)
    for page_number in _fkp_pages(table, fc, lcb):
        page = word[page_number * 512:page_number * 512 + 512]
        if len(page) < 512:
            continue
        count = page[511]
        points = struct.unpack_from(f"<{count + 1}I", page, 0)
        for j in range(count):
            offset = page[4 * (count + 1) + 13 * j] * 2
            props = (False, False)
            if offset:
                size = page[offset]
                if size == 0:
                    size, start = 2 * page[offset + 1], offset + 2
                else:
                    size, start = 2 * size - 1, offset + 1
                grpprl = page[start + 2:start + size]  # 앞 2바이트는 스타일 번호(istd)
                values = sprm_values(grpprl, wanted)
                huge = values.get(SPRM_HUGE_PAPX)
                if huge and len(huge) == 4 and data_stream:
                    at = u32(huge, 0)
                    if at + 2 <= len(data_stream):
                        values = sprm_values(data_stream[at + 2:at + 2 + u16(data_stream, at)], wanted)
                in_table = _toggle_on(values.get(SPRM_IN_TABLE, b""))
                row_end = _toggle_on(values.get(SPRM_TTP, b"")) or _toggle_on(values.get(SPRM_INNER_TTP, b""))
                props = (in_table or row_end, row_end)
            triples.append((points[j], points[j + 1], props))
    return Runs(triples)


UNDEFINED_1252 = frozenset((0x81, 0x8D, 0x8F, 0x90, 0x9D))


def _decode(raw: bytes, compressed: bool) -> str:
    if not compressed:
        return raw.decode("utf-16-le", "replace")
    # 압축 조각은 한 글자 한 바이트(cp1252). cp1252 에 없는 다섯 바이트는 latin-1 로 둔다.
    try:
        return raw.decode("cp1252")
    except UnicodeDecodeError:
        return "".join(chr(b) if b in UNDEFINED_1252 else bytes((b,)).decode("cp1252") for b in raw)


def doc_text(data: bytes, stats: dict | None = None) -> str:
    """.doc 파일 바이트에서 본문 글. `raw_source_text.word_text` 와 같은 꼴(문단마다 한 줄).

    `stats` 를 주면 이 판독기가 글로 싣지 않은 것의 수를 센다 — `equationObjects`(복합 파일 안
    `Equation Native` 흐름 수: 수식 개체), `inlineObjectMarks`(본문의 `\x01` 자리 표지: 그림 · 개체 미리보기 ·
    양식 필드 자료), `floatingShapeAnchors`(본문의 `\x08` 떠 있는 도형 닻), `textboxChars`(글상자 구간 글자 수,
    FIB `ccpTxbx`).
    """
    compound = Compound(data)
    word = compound.stream("WordDocument")
    if len(word) < 0x22 or u16(word, 0) != WORD_IDENT:
        raise ExtractError("Word 문서 머리 아님")
    if u16(word, 2) < MIN_NFIB:
        raise ExtractError("Word 6/95 형식", f"nFib={u16(word, 2)}")
    flags = u16(word, 0x0A)
    if flags & 0x0100:
        raise ExtractError("암호 걸린 문서")
    table = compound.stream("1Table" if flags & 0x0200 else "0Table")
    try:
        data_stream = compound.stream("Data")
    except ExtractError:
        data_stream = b""
    # FIB: FibBase(32바이트) · csw + fibRgW · cslw + fibRgLw · cbRgFcLcb + fibRgFcLcbBlob 차례다.
    pos = 32
    pos += 2 + 2 * u16(word, pos)
    long_words = pos + 2
    pos = long_words + 4 * u16(word, pos)
    ccp_text = u32(word, long_words + 12)
    blob = pos + 2
    if stats is not None:
        stats["equationObjects"] = compound.stream_names.count("equation native")
        stats["textboxChars"] = u32(word, long_words + 36)
        stats["inlineObjectMarks"] = 0
        stats["floatingShapeAnchors"] = 0

    def pair(i: int) -> tuple[int, int]:
        return u32(word, blob + 8 * i), u32(word, blob + 8 * i + 4)

    fc_clx, lcb_clx = pair(33)
    if not lcb_clx or fc_clx + lcb_clx > len(table):
        raise ExtractError("조각표 없음")
    clx, i, grpprls = table[fc_clx:fc_clx + lcb_clx], 0, []
    while i < len(clx) and clx[i] == 1:
        size = u16(clx, i + 1)
        grpprls.append(clx[i + 3:i + 3 + size])
        i += 3 + size
    if i >= len(clx) or clx[i] != 2:
        raise ExtractError("조각표 읽기 실패")
    points, pieces = _plc(clx, i + 5, u32(clx, i + 1), 8)
    chars = char_runs(word, table, *pair(12), font_names(table, *pair(FONT_TABLE_PAIR)))
    paragraphs = paragraph_runs(word, table, data_stream, *pair(13))

    # 주 문서 구간을 글자 속성이 같은 조각으로 편다.
    segments: list[tuple[str, CharProps, bool, int, int]] = []  # (글, 글자 속성, 지움, 첫 글자 FC, 글자당 바이트)
    for k, pcd in enumerate(pieces):
        cp_start, cp_end = points[k], min(points[k + 1], ccp_text)
        if cp_start >= ccp_text:
            break
        if cp_end <= cp_start:
            continue
        raw_fc = u32(pcd, 2)
        compressed = bool(raw_fc & 0x40000000)
        fc = (raw_fc & 0x3FFFFFFF) // 2 if compressed else raw_fc & 0x3FFFFFFF
        width = 1 if compressed else 2
        prm = u16(pcd, 6)
        piece_deleted = False
        if prm & 1 and (prm >> 1) < len(grpprls):
            piece_deleted = _toggle_on(sprm_values(grpprls[prm >> 1], (SPRM_DEL,)).get(SPRM_DEL, b""))
        end_fc = fc + (cp_end - cp_start) * width
        cuts = [fc] + [c for c in chars.cuts(fc, end_fc) if (c - fc) % width == 0] + [end_fc]
        for a, b in zip(cuts, cuts[1:]):
            if b <= a:
                continue
            props = chars.at(a, PLAIN)
            segments.append((_decode(word[a:b], compressed), props, piece_deleted or props.deleted, a, width))

    seen = _symbol_evidence(segments)

    def symbol_text(props: CharProps):
        code = props.sym_code
        if props.sym_tab is not None:
            return symbol_fonts.glyph(props.sym_tab, code) or ""
        if _is_pua(code):
            return Lost(code)  # 기호 글꼴이 아닌 글꼴(Times New Roman 따위)에 적힌 사용자 영역 부호
        # 대응표 없는 글꼴의 사용자 영역 밖 부호는 그 유니코드 글자다.
        return chr(code) if code >= 0x20 and not 0xE000 <= code <= 0xF8FF else ""

    def settle(i: int, code: int) -> str:
        names = seen.get(code & 0xFF)
        g = symbol_fonts.glyph(symbol_fonts.TABLES[next(iter(names))], code) if names and len(names) == 1 else None
        if g is not None and g.isalpha():
            # 문단 첫 글자 뒤에 탭이 오면 목록 표지일 수 있어 알파벳으로는 읽지 않는다(`settle_lost_fonts` 와 같다).
            before = [x for x in buf[:i] if isinstance(x, str) and x not in (DEL_OPEN, DEL_CLOSE)]
            after = next((x for x in buf[i + 1:] if not (isinstance(x, str) and x in (DEL_OPEN, DEL_CLOSE))), "")
            if not "".join(before).strip() and after == "\t":
                g = None
        return g if g is not None else chr(code)

    lines: list[str] = []
    buf: list = []
    cell_parts: list[str] = []
    row: list[str] = []
    fields: list[bool] = []  # 필드마다 결과 구간에 들어섰는가
    open_del = False

    def cell(parts: list[str]) -> str:
        # 칸 안 줄바꿈은 빈칸으로 편다(`docx_text.table_line_rows` 와 같다).
        return " ".join(" ".join(p.split("\n")) for p in parts if p)

    def take() -> str:
        nonlocal open_del
        if open_del:
            buf.append(DEL_CLOSE)
            open_del = False
        text = "".join(x if isinstance(x, str) else settle(i, x.code) for i, x in enumerate(buf))
        text = text.replace(DEL_OPEN + DEL_CLOSE, "").strip()
        buf.clear()
        return text

    for text, props, is_deleted, fc, width in segments:
        for offset, ch in enumerate(text):
            if ch == "\x13":
                fields.append(False)
                continue
            if ch == "\x14":
                if fields:
                    fields[-1] = True
                continue
            if ch == "\x15":
                if fields:
                    fields.pop()
                continue
            if ch in ("\r", "\x07"):
                in_table, row_end = paragraphs.at(fc + offset * width, (False, False))
                paragraph = take()
                if ch == "\x07" and row_end:
                    if cell_parts:
                        row.append(cell(cell_parts))
                        cell_parts.clear()
                    if row:
                        lines.append("| " + " | ".join(row) + " |")
                    row.clear()
                elif ch == "\x07":
                    cell_parts.append(paragraph)
                    row.append(cell(cell_parts))
                    cell_parts.clear()
                elif in_table:
                    cell_parts.append(paragraph)
                else:
                    if row or cell_parts:  # 행 끝 표지 없이 표가 끝났다
                        if cell_parts:
                            row.append(cell(cell_parts))
                        lines.append("| " + " | ".join(row) + " |")
                        row.clear()
                        cell_parts.clear()
                    lines.append(paragraph)
                continue
            if any(not result for result in fields):
                continue  # 필드 명령 글
            if ch in CONTROL:
                ch = CONTROL[ch]
            elif ch < " ":
                if stats is not None and ch in ("\x01", "\x08"):
                    stats["inlineObjectMarks" if ch == "\x01" else "floatingShapeAnchors"] += 1
                continue
            elif props.sym_code is not None:
                ch = symbol_text(props)  # 기호 넣기: 글 흐름의 글자는 자리 표지다
            elif props.fonts is not None:
                tab = symbol_fonts._slot_table(props.fonts, ch)
                ch = (symbol_fonts.glyph(tab, ord(ch)) if tab else None) or ch
            elif _is_pua(ord(ch)):
                ch = Lost(ord(ch))
            if is_deleted != open_del:
                buf.append(DEL_OPEN if is_deleted else DEL_CLOSE)
                open_del = is_deleted
            buf.append(ch)
    tail = take()
    if cell_parts or row:
        if cell_parts:
            row.append(cell(cell_parts))
        lines.append("| " + " | ".join(row) + " |")
    if tail:
        lines.append(tail)
    return "\n".join(lines)
