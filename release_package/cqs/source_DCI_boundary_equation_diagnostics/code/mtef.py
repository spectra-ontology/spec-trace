"""MathType 수식 형식(MTEF) 읽기 — OLE 수식 개체 `Equation Native` 스트림을 레코드 나무로 푼다.

판 3(Equation Editor 3.x, `Equation.3`)과 판 5(MathType 4 이상, `Equation.DSMT4`)만 읽는다. 레코드 배치는
Design Science 의 MTEF 명세(판 3 · 판 5)를 따른다. 나무의 마디:
  ("line", [마디...])          줄. 빈 자리 줄(null line)은 ("line", None)
  ("char", 글꼴, 글자, 꾸밈[])   글꼴 = 판 3 은 typeface − 128, 판 5 는 부호 있는 typeface 값 − 128
                               글자 = 판 3 은 16비트 글자 값, 판 5 는 MTCode(없으면 None)
  ("tmpl", 선택자, 변형, [마디...])
  ("pile", [줄...])  ("matrix", 행 수, 열 수, [줄...])
크기 · 글꼴 정의 · 색 · 눈금자 · 수식 설정 레코드는 읽고 버린다. 판 3 의 FONT 레코드는 음수 글꼴 번호 →
글꼴 이름으로 `fonts` 에 모은다."""
import struct

EQ_HDR = 28  # EQNOLEFILEHDR 길이


class MTEFError(ValueError):
    pass


class _In:
    def __init__(self, b: bytes, i: int):
        self.b, self.i = b, i

    def u8(self) -> int:
        if self.i >= len(self.b):
            raise MTEFError("unexpected end")
        v = self.b[self.i]
        self.i += 1
        return v

    def u16(self) -> int:
        lo = self.u8()
        return lo | self.u8() << 8

    def uint(self) -> int:
        v = self.u8()
        return self.u16() if v == 255 else v

    def sint(self) -> int:
        v = self.u8()
        return self.u16() - 32768 if v == 255 else v - 128

    def cstr(self) -> str:
        j = self.b.find(b"\0", self.i)
        if j < 0:
            raise MTEFError("unterminated string")
        s = self.b[self.i:j].decode("latin-1")
        self.i = j + 1
        return s

    def skip(self, n: int):
        if self.i + n > len(self.b):
            raise MTEFError("unexpected end")
        self.i += n


END, LINE, CHAR, TMPL, PILE, MATRIX, EMBELL, RULER, FONT, SIZE = range(10)
NUDGE = 0x8


class Eqn:
    """풀린 수식 하나 — `version` · `product` · `inline`(판 5 만) · `fonts` · `body`(맨 위 마디 목록)."""

    def __init__(self, native: bytes):
        if len(native) < EQ_HDR:
            raise MTEFError("short native stream")
        hdr, = struct.unpack_from("<H", native, 0)
        size, = struct.unpack_from("<I", native, 8)
        data = native[hdr:hdr + size] if size else native[hdr:]
        r = _In(data, 0)
        self.version = r.u8()
        if self.version not in (3, 5):
            raise MTEFError(f"MTEF version {self.version}")
        self.platform, self.product, self.pver, self.psub = r.u8(), r.u8(), r.u8(), r.u8()
        self.inline = None
        if self.version == 5:
            self.app = r.cstr()
            self.inline = bool(r.u8() & 1)
        self.fonts: dict[int, str] = {}
        self.font_defs: list[tuple[int, str]] = []
        self.style_defs: list[int] = []
        self.rulers = {"tagged": 0, "untagged": 0}
        self._r = r
        self.body = self._list(top=True)
        self.tail = len(data) - r.i
        del self._r

    # 레코드 머리: (종류, 선택 비트). 판 3 은 한 바이트(아래 4비트 종류, 위 4비트 선택), 판 5 는 종류 바이트 +
    # 선택 바이트 — 단 END 와 선택 바이트가 없는 정의 레코드는 종류 바이트뿐이다.
    def _head(self):
        r = self._r
        t = r.u8()
        if self.version == 3:
            return t & 0x0F, t >> 4
        if t in (LINE, CHAR, TMPL, PILE, MATRIX, EMBELL, 16, 18):
            return t, r.u8()
        return t, 0

    def _nudge(self, opt):
        if opt & NUDGE:
            r = self._r
            if (r.u8(), r.u8()) == (128, 128):
                r.skip(4)

    def _list(self, top=False) -> list:
        out = []
        while True:
            if top and self._r.i >= len(self._r.b):
                return out
            t, opt = self._head()
            if t == END:
                return out
            node = self._record(t, opt)
            if node is not None:
                out.append(node)

    def _ruler(self):
        """LINE · PILE 의 선택 비트 0x2 뒤 눈금자. 명세는 종류 바이트(7)를 앞에 두지만, 38.104 의 판 5 경우 바이트
        `04 02 01 01 | 01 00 56 ff | 01 00 …`(PILE · 정렬 둘 · 칸 하나짜리 눈금자 · 다음 LINE)처럼 종류 바이트 없이
        칸 수부터 쓴 것이 있다. 첫 바이트가 7 이면 종류 바이트로, 아니면 칸 수로 읽는다."""
        r = self._r
        if r.b[r.i:r.i + 1] == bytes([RULER]):
            r.u8()
            self.rulers["tagged"] += 1
        else:
            self.rulers["untagged"] += 1
        r.skip(r.u8() * 3)

    def _record(self, t, opt):
        r, v5 = self._r, self.version == 5
        if t == LINE:
            self._nudge(opt)
            if opt & 0x4:
                r.skip(2)
            if opt & 0x2:
                self._ruler()
            return ("line", None if opt & 0x1 else self._list())
        if t == CHAR:
            self._nudge(opt)
            if v5:
                face = r.sint()
                code = None if opt & 0x20 else r.u16()
                if opt & 0x04:
                    r.skip(1)
                if opt & 0x10:
                    r.skip(2)
                emb = self._embells() if opt & 0x01 else []
            else:
                face = r.u8() - 128
                code = r.u16()
                emb = self._embells() if opt & 0x2 else []
            return ("char", face, code, emb)
        if t == TMPL:
            self._nudge(opt)
            sel = r.u8()
            var = r.u8()
            if v5 and var & 0x80:
                var = (var & 0x7F) | (r.u8() << 8)
            r.skip(1)
            return ("tmpl", sel, var, self._list())
        if t == PILE:
            self._nudge(opt)
            r.skip(2)
            if opt & 0x2:
                self._ruler()
            return ("pile", self._list())
        if t == MATRIX:
            self._nudge(opt)
            r.skip(3)
            rows, cols = r.u8(), r.u8()
            r.skip(((rows + 1) * 2 + 7) // 8 + ((cols + 1) * 2 + 7) // 8)
            return ("matrix", rows, cols, self._list())
        if t == EMBELL:
            self._nudge(opt)
            return ("embell", r.u8())
        if t == RULER:
            r.skip(r.u8() * 3)
            return None
        if t == FONT:
            if v5:  # FONT_STYLE_DEF
                self.style_defs.append(r.uint())
                r.skip(1)
            else:
                face = r.u8()
                r.skip(1)
                self.fonts[-face] = r.cstr()
            return None
        if t == SIZE:
            k = r.u8()
            r.skip({101: 2, 100: 3}.get(k, 1))
            return None
        if 10 <= t <= 14:
            return None
        if v5:
            if t == 15:  # COLOR
                r.uint()
                return None
            if t == 16:  # COLOR_DEF
                r.skip(8 if opt & 0x1 else 6)
                if opt & 0x4:
                    r.cstr()
                return None
            if t == 17:  # FONT_DEF
                self.font_defs.append((r.uint(), r.cstr()))
                return None
            if t == 18:  # EQN_PREFS
                self._dims()
                self._dims()
                for _ in range(r.u8()):
                    if r.uint():
                        r.skip(1)
                return None
            if t == 19:  # ENCODING_DEF
                r.cstr()
                return None
            if t >= 100:  # FUTURE
                r.skip(r.uint())
                return None
        raise MTEFError(f"record type {t} at {r.i - 1}")

    def _embells(self) -> list:
        out = []
        while True:
            t, opt = self._head()
            if t == END:
                return out
            if t != EMBELL:
                raise MTEFError(f"record type {t} in embellishment list")
            self._nudge(opt)
            out.append(self._r.u8())
            if self.version == 3:
                # Equation Editor 3 은 꾸밈 레코드마다 빈 개체 목록(END 하나)을 붙인다 — 명세에는 없고
                # 38.211 의 `06 11 00 06 11 00 00`(윗줄 꾸밈 둘 + 목록 끝) 같은 바이트로 확인했다.
                self._list()

    def _dims(self):
        r = self._r
        n = r.u8()
        nib, cur = 0, None

        def nibble():
            nonlocal nib, cur
            if nib % 2 == 0:
                cur = r.u8()
                v = cur >> 4
            else:
                v = cur & 0xF
            nib += 1
            return v

        for _ in range(n):
            nibble()  # 단위
            while nibble() != 0xF:
                pass
