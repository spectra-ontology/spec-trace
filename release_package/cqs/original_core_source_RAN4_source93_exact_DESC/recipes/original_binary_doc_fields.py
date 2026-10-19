"""docx 글 부품을 바로잡는다 — LibreOffice 틀 되돌리기 · LibreOffice 변환 복원 · 명령문 누출 지우기 · 필드 오류 글
지우기 · 숨김 글 비우기.

RAN 판독기는 모두 `docx_text.zip_part` · `docx_text.open_document` 로 부품을 읽고, 두 입구가 본문 · 각주 ·
미주 부품(`TEXT_PARTS`)을 여기로 넘긴다. 고치는 결함은 다섯이고 이 차례로 고친다.

LibreOffice 틀 되돌리기
    .doc 의 틀(위치를 지정한 문단 · 표)은 .doc 본문 이야기의 제자리에 있지만, LibreOffice 는 이것을 닻 문단에 묶인
    글상자(그림 자리 · 대체 자리 두 벌)로 내보낸다. 판독기는 글상자를 본문 글로 읽지 않으므로 틀 안의 표 · 문단이
    본문에서 빠지고, 아래 필드 복원의 앞 글 대조와 글상자 짝짓기도 어긋난다. 같은 폴더의 .doc 으로 틀을 가려 안의
    블록을 닻 문단 앞으로 옮기고 그 그림 요소를 지운다(`_unwrap_frames`). 본문 부품만 고친다.
LibreOffice 변환 복원
    수집 때 .doc 원본을 LibreOffice 로 바꾼 .docx 는 필드 결과를 LibreOffice 가 다시 계산해 쓴다. 원본 Word 가
    저장한 결과와 달리 참조(REF)가 'Error: Reference source not found' 로 깨지고 SEQ · REF · DOCPROPERTY 값이
    바뀐다. 같은 폴더에 같은 이름의 .doc 이 있고 docProps/app.xml 이 LibreOffice 를 적은 문서만 고친다. .doc 의
    같은 이야기(본문 · 각주 · 미주)에서 필드를 읽고, 양쪽 필드를 (종류, 첫 인자) 열로 정렬(difflib)해 짝짓는다.
    본문 부품의 글상자는 .doc 글상자 이야기와 따로 짝짓는다(`box_contents` 의 두 벌마다). 짝 가운데 필드 앞
    글의 마지막 낱말 `CTX_WORDS` 개가 (지운 글을 넣은 벌과 뺀 벌 가운데 어느 한 벌에서) 같고 스위치가 같은 것만
    Word 가 저장한 결과로 되돌리고, 결과 글이 없는 필드는 그 값으로 채운다(`judge`).
명령문 누출
    LibreOffice 는 옮기지 못한 필드(EMBED · SHAPE · INCLUDEPICTURE · PAGEREF · HYPERLINK 따위)의 명령문을 보이는
    글로 쓰기도 한다. .doc 같은 이야기에 있는 필드 명령문이 docx 글에 낱말 경계로 들었고, .doc 의 보이는 글에는
    없고, docx 같은 자리에서 그 필드가 .doc 보다 적은 수만큼 빠졌을 때만 지운다(`_strip_leaked_codes`).
필드 오류 글
    Word 가 결과를 못 만들 때 결과 자리에 남기는 'Error! Reference source not found.' 같은 글이다. 한 문단 안의
    필드 결과가 오류 머리글(`_RESULT_ERROR`)로 시작하거나 LibreOffice 오류 글과 같으면 비운다. 필드 밖에 굳은
    오류 글은 `_LOOSE_ERRORS` 의 문구만 지운다. 'WUS Timing Error:' 같은 콜론 꼴은 본문이라 건드리지 않는다.
    오류 글을 지운 문단에는 표지 속성(`ERROR_LINE`)을 단다 — 원본 화면에서는 오류 글이 보이던 줄이라, 빈 문단을
    경계로 쓰는 판독기가 이 줄을 빈 줄로 세면 뒤의 글을 잃는다(`docx_text.blank_line`).
숨김 글
    글자 속성으로 숨긴(vanish · specVanish) 글은 화면 · 인쇄에 나오지 않는다. 그 run 의 글을 뺀다. 필드 표지 ·
    명령문은 남겨 필드 구조를 지킨다. 문단 표지(pPr 안 rPr)의 숨김은 글을 숨기지 않으므로 보지 않는다.

부품을 엄격하게 파싱하지 못하면(부르는 쪽이 넘긴 `repair` 로 고친 뒤에도) 받은 바이트를 그대로 돌려준다.
여기서 recover 파싱을 하면 판독기의 시끄러운 실패가 조용한 절단으로 바뀌기 때문이다. 고칠 것이 없으면 받은
바이트를 그대로 돌려준다. 한 일은 `STATS` 에 센다.
"""
from __future__ import annotations

import bisect
import difflib
import functools
import os
import re
import struct
import zipfile
from collections import Counter, deque

from lxml import etree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
MC = "{http://schemas.openxmlformats.org/markup-compatibility/2006}"
M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
_XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"

# 고치는 부품 → .doc 이야기 번호(0 본문 · 1 각주 · 2 미주).
TEXT_PARTS = {"word/document.xml": 0, "word/footnotes.xml": 1, "word/endnotes.xml": 2}

# 짝의 앞 글 낱말 수. 두 손실을 함께 재어 고른 값이다 — 바른 짝이
# 앞 글 대조에서 떨어져 값을 쓰지 못하는 것과, 짝을 이웃 같은 키 필드로 한 칸 밀었을 때 틀린 값이 쓰이는 것.
# WG 마다 "Error: Reference source not found" 가 든 TDoc 전부와 나머지에서 고른 150건을 앞 글 두 벌로 견주면
# 낱말 수 1~200 어디서도 바른 짝을 잃지 않는다(복원하지 않는 글상자 묶음은 뺀다). 틀린 값은 낱말 수가 늘수록 줄기만
# 하고, 71 은 다섯 WG 가 모두 가장 적은 수(RAN1 45 · RAN4 1 · 나머지 0)에 닿는 가장 작은 값이다 — 200 까지 수가
# 같다. 남는 것은 앞 글 두 벌이 200 낱말까지 통째로 같은 같은 키 필드라 낱말 수로는 가를 수 없고, 그 짝은 정렬
# 차례가 정한다. 표본에서 양쪽 개수가 다른 무리는 RAN4 목차 하나뿐이었고 거기서는 차례가 바른 값을 골랐다.
CTX_WORDS = 71

# 정렬에 넣지 않는 종류 — LibreOffice 가 HYPERLINK 필드를 하이퍼링크 요소로 바꾸므로 양쪽 개수가 맞지 않고,
# 표시 글은 LibreOffice 도 그대로 둔다.
_NEVER_ALIGN = frozenset({"HYPERLINK"})
# 짝의 스위치를 견줄 때 빼는 스위치 — LibreOffice 가 `\h` 를 더하고 `\s` 를 뺀다.
_LO_SWITCHES = frozenset({"\\h", "\\s"})

LO_ERROR = "Error: Reference source not found"
# 필드 결과 첫머리의 Word 오류 머리글(여러 언어판). 느낌표 꼴만 — 콜론 꼴은 본문 글에도 흔하다. 끝 부호 앞
# 빈칸 하나는 허용한다('Error !').
_RESULT_HEADS = ("Error!", "¡Error!", "Fehler!", "Erreur!", "Fel!", "Virhe.", "Virhe!", "Errore.", "Errore!", "Fout!",
                 "Erro!", "Błąd!", "Chyba!", "Hata!", "错误!", "错误！", "錯誤!", "錯誤！", "エラー!", "エラー！", "오류!", "오류！")
# 오류 글을 지운 문단(w:p)에 다는 속성. 이름공간 없는 속성이라 수식 같은 하위 요소를 직렬화할 때 이름공간
# 선언이 따라붙지 않는다.
ERROR_LINE = "error-line"
_RESULT_ERROR = re.compile("|".join(re.escape(h[:-1]) + " ?" + re.escape(h[-1]) for h in _RESULT_HEADS))
# 필드 밖에 굳은 오류 글 — 그대로 맞는 문구만 지운다.
_LOOSE_ERRORS = ("Error! Objects cannot be created from editing field codes.",
                 "错误!不能通过编辑域代码创建对象。",
                 "Error! Reference source not found.",
                 LO_ERROR)
# 오류 손질을 할지 가르는 값싼 문턱. 두 손질이 지우는 글(오류 머리글 `_RESULT_HEADS` · 굳은 오류 문구
# `_LOOSE_ERRORS`)을 통째로 찾되, 글자 사이에 태그 · 공백 · 문자 참조 · 제어 글자 escape 가 끼어도 맞는다 —
# 오류 글이 여러 run 에 갈려 쓰여도 놓치지 않고, 'Block Error Rate' 같은 본문 낱말에는 걸리지 않는다(앞 토막
# 'Err' 만 보면 영어 문서 거의 전부가 걸려 큰 TS 마다 트리 전체를 헛걷는다). 부품 바이트(`settle_part`)와 이은
# w:t 글(`settle_tree`)에 같은 문턱을 쓴다.
_GAP = r"(?:<[^>]*>|\s|&#\w+;|_x00[01][0-9a-fA-F]_)*"
_ERROR_GATE_TEXT = re.compile("|".join(_GAP.join(re.escape(c) for c in h if not c.isspace())
                                       for h in _RESULT_HEADS + _LOOSE_ERRORS))
_ERROR_GATE = re.compile(_ERROR_GATE_TEXT.pattern.encode())

_FALSE = frozenset({"false", "0", "off"})
_CTRL = re.compile(r"[\x00-\x1f]|_x00[01][0-9a-fA-F]_")

STATS: Counter = Counter()


def norm(s: str | None) -> str:
    return " ".join(_CTRL.sub(" ", s or "").split())


def split_instr(instr: str) -> tuple[str, str, frozenset]:
    """(종류, 첫 인자, 서식 아닌 스위치 집합). 서식 스위치(`\\*` · `\\#` · `\\@`)는 인자째 뺀다."""
    toks = re.findall(r'"[^"]*"|\S+', norm(instr))
    if not toks:
        return "?", "", frozenset()
    kind, arg, sw, i = toks[0].upper(), "", set(), 1
    if i < len(toks) and not toks[i].startswith("\\"):
        arg = toks[i].strip('"')
        i += 1
    while i < len(toks):
        t = toks[i]
        if t.startswith("\\"):
            if t[:2] in ("\\*", "\\#", "\\@"):
                i += 2
                continue
            sw.add(t.lower())
        i += 1
    return kind, arg, frozenset(sw)


class _Words:
    """필드 앞 글의 마지막 낱말들. 띄어쓰기 · 문단 경계에서 낱말을 끊는다."""

    __slots__ = ("words", "cur", "log")

    def __init__(self, log: list | None = None):
        self.words: deque = deque(maxlen=CTX_WORDS)
        self.cur: list[str] = []
        self.log = log

    def feed(self, s: str) -> None:
        if not s:
            return
        parts = s.split()
        if not parts:
            self.space()
            return
        if s[0].isspace():
            self.space()
        self.cur.append(parts[0])
        for w in parts[1:]:
            self.space()
            self.cur.append(w)
        if s[-1].isspace():
            self.space()

    def space(self) -> None:
        if self.cur:
            self.words.append("".join(self.cur))
            if self.log is not None:
                self.log.append(self.words[-1])
            self.cur = []

    def tail(self) -> tuple:
        w = list(self.words)
        if self.cur:
            w.append("".join(self.cur))
        return tuple(w[-CTX_WORDS:])


class _Ctx:
    """앞 글 두 벌 — 변경 추적으로 지운 글을 넣은 벌(keep)과 뺀 벌(drop). LibreOffice 는 .doc 의 지운 글을 docx
    의 지운 글(w:del 안 w:delText)로 옮기기도 하고, 아예 버리기도 하고, 넣은 뒤 지운 글의 삭제 표시만 버려 보이는
    글로 남기기도 하고, 삭제 범위를 한 글자 앞으로 밀어 적기도 한다. 한 벌만 견주면 어느 벌을 골라도 다른 꼴의
    문서에서 바른 짝을 잃으므로 두 벌을 함께 쌓고, 어느 한 벌이 맞으면 같은 앞 글로 본다(`same_ctx`). 지운 글이
    없으면 두 벌은 같다. log · dlog 는 두 벌의 낱말을 모두 남길 목록이다."""

    __slots__ = ("keep", "drop")

    def __init__(self, log: list | None = None, dlog: list | None = None):
        self.keep, self.drop = _Words(log), _Words(dlog)

    def feed(self, s: str, gone: bool = False) -> None:
        self.keep.feed(s)
        if not gone:
            self.drop.feed(s)

    def space(self, gone: bool = False) -> None:
        self.keep.space()
        if not gone:
            self.drop.space()

    def tail(self) -> tuple:
        return self.keep.tail(), self.drop.tail()


# ---------------------------------------------------------------------------------------------------------------
# .doc (Word 97-2003) 판독 — 복합 파일(CFB)에서 WordDocument · 표 스트림을 꺼내고, FIB 의 Clx 조각표로
# 본문 · 각주 · 미주 글자열을 복원한다.

class DocError(Exception):
    pass


_SIG = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
_FREE, _END = 0xFFFFFFFF, 0xFFFFFFFE


class _Cfb:
    def __init__(self, data: bytes):
        if data[:8] != _SIG:
            raise DocError("복합 파일 서명 아님")
        self.d = data
        self.ss = 1 << struct.unpack_from("<H", data, 0x1E)[0]
        self.mss = 1 << struct.unpack_from("<H", data, 0x20)[0]
        self.cutoff = struct.unpack_from("<I", data, 0x38)[0]
        first_dir = struct.unpack_from("<I", data, 0x30)[0]
        first_mfat = struct.unpack_from("<I", data, 0x3C)[0]
        first_difat = struct.unpack_from("<I", data, 0x44)[0]
        difat = list(struct.unpack_from("<109I", data, 0x4C))
        per = self.ss // 4
        s, seen = first_difat, set()
        while s not in (_FREE, _END) and s not in seen:
            seen.add(s)
            ent = struct.unpack_from("<%dI" % per, self._sector(s), 0)
            difat.extend(ent[:-1])
            s = ent[-1]
        fat: list[int] = []
        for s in difat:
            if s not in (_FREE, _END):
                fat.extend(struct.unpack_from("<%dI" % per, self._sector(s), 0))
        self.fat = fat
        dirdata = self._chain(first_dir, self.fat, self._sector)
        ents = []
        for i in range(len(dirdata) // 128):
            e = dirdata[i * 128:(i + 1) * 128]
            nlen = struct.unpack_from("<H", e, 0x40)[0]
            name = e[:max(0, nlen - 2)].decode("utf-16-le", "replace")
            left, right, child = struct.unpack_from("<III", e, 0x44)
            start, size = struct.unpack_from("<II", e, 0x74)
            ents.append((e[0x42], name, left, right, child, start, size))
        if not ents or ents[0][0] != 5:
            raise DocError("루트 항목 없음")
        # 뿌리 저장소 바로 아래 항목만 모은다. 끼워 넣은 개체(OLE) 저장소 안에도 WordDocument · 1Table 같은
        # 이름의 흐름이 있어 이름만으로 고르면 남의 것을 읽는다.
        self.entries: dict[str, tuple[int, int]] = {}
        todo, seen = [ents[0][4]], set()
        while todo:
            k = todo.pop()
            if k >= len(ents) or k in seen:
                continue
            seen.add(k)
            typ, name, left, right, _child, start, size = ents[k]
            if typ == 2:
                self.entries[name] = (start, size)
            todo.extend((left, right))
        self.ministream = self._chain(ents[0][5], self.fat, self._sector)[:ents[0][6]]
        self.minifat: list[int] = []
        if first_mfat not in (_FREE, _END):
            raw = self._chain(first_mfat, self.fat, self._sector)
            self.minifat = list(struct.unpack_from("<%dI" % (len(raw) // 4), raw, 0))

    def _sector(self, s: int) -> bytes:
        # 마지막 섹터가 잘려 저장된 파일(크기가 섹터의 배수가 아님)이 있어 모자란 꼬리는 0 으로 채운다.
        o = (s + 1) * self.ss
        if o >= len(self.d):
            raise DocError("섹터가 파일 밖")
        return self.d[o:o + self.ss].ljust(self.ss, b"\0")

    def _mini(self, s: int) -> bytes:
        o = s * self.mss
        return self.ministream[o:o + self.mss]

    @staticmethod
    def _chain(start: int, fat: list[int], getter) -> bytes:
        out, s, seen = [], start, set()
        while s not in (_FREE, _END):
            if s in seen or s >= len(fat):
                raise DocError("섹터 사슬 손상")
            seen.add(s)
            out.append(getter(s))
            s = fat[s]
        return b"".join(out)

    def stream(self, name: str) -> bytes:
        if name not in self.entries:
            raise DocError("스트림 없음: " + name)
        start, size = self.entries[name]
        if size < self.cutoff:
            return self._chain(start, self.minifat, self._mini)[:size]
        return self._chain(start, self.fat, self._sector)[:size]


_SURROGATE = re.compile("[\ud800-\udfff]")


def _utf16_units(raw: bytes) -> str:
    """UTF-16LE 바이트를 코드 단위 하나에 글자 하나로 읽는다. 대리 쌍(BMP 밖 글자)을 한 글자로 합치는
    보통 해독은 글자 수가 CP 수보다 줄어 뒤쪽 이야기 경계가 밀린다."""
    n = len(raw) // 2
    return "".join(map(chr, struct.unpack("<%dH" % n, raw[:n * 2])))


def _join_surrogates(s: str) -> str:
    """이야기를 자른 뒤 대리 쌍을 한 글자로 합친다. 짝 없는 대리 글자는 U+FFFD 로 바꾼다(XML 에 못 쓴다)."""
    if not _SURROGATE.search(s):
        return s
    return s.encode("utf-16-le", "surrogatepass").decode("utf-16-le", "replace")


def _doc_read(data: bytes, props: bool):
    """(이야기 넷, 앞 글 이야기 넷).

    이야기는 (본문, 각주, 미주, 글상자) 글자열이다. 이야기 경계는 FIB 의 ccp 값 — 본문 [0, ccpText), 각주는 그 뒤
    ccpFtn, 미주는 머리말 · 매크로 · 메모 이야기 뒤 ccpEdn, 본문 글상자는 미주 바로 뒤 ccpTxbx 다.
    글상자 이야기는 FIB 가 ccpTxbx 를 싣고 조각표가 그 끝까지 닿을 때만 읽고, 아니면 빈 글이다.
    글자 위치(CP)는 UTF-16 코드 단위로 세므로 조각은 코드 단위로 읽고, 대리 쌍은 이야기를 자른 뒤 합친다.

    앞 글 이야기는 이야기마다 `_ctx_text` 의 두 벌이고, props 가 참일 때만 만들며 아니면 None 이다. 글자 속성에
    앞 글을 바꿀 것이 없으면 None 넷, 글자 속성을 못 읽으면 False 다."""
    cfb = _Cfb(data)
    wd = cfb.stream("WordDocument")
    ident, nfib = struct.unpack_from("<HH", wd, 0)
    if ident != 0xA5EC:
        raise DocError("FIB 표지 아님")
    if nfib < 101:
        raise DocError("Word 6/95 형식")
    flags = struct.unpack_from("<H", wd, 0x0A)[0]
    if flags & 0x0100:
        raise DocError("암호화 문서")
    pos = 32
    csw = struct.unpack_from("<H", wd, pos)[0]
    pos += 2 + csw * 2
    cslw = struct.unpack_from("<H", wd, pos)[0]
    if cslw < 9:
        raise DocError("FIB 길이 값 모자람")
    lw = struct.unpack_from("<%di" % cslw, wd, pos + 2)
    pos += 2 + cslw * 4
    ccp_text, ccp_ftn, ccp_hdd, ccp_mcr, ccp_atn, ccp_edn = lw[3:9]
    if min(ccp_text, ccp_ftn, ccp_hdd, ccp_mcr, ccp_atn, ccp_edn) < 0:
        raise DocError("ccp 값 손상")
    edn_start = ccp_text + ccp_ftn + ccp_hdd + ccp_mcr + ccp_atn
    total = edn_start + ccp_edn
    ccp_txbx = lw[9] if cslw > 9 and lw[9] > 0 else 0
    want = total + ccp_txbx
    cb = struct.unpack_from("<H", wd, pos)[0]
    if cb <= 33:
        raise DocError("fcClx 자리 없음")
    fc_clx, lcb_clx = struct.unpack_from("<II", wd, pos + 2 + 33 * 8)
    tbl = cfb.stream("1Table" if flags & 0x0200 else "0Table")
    clx = tbl[fc_clx:fc_clx + lcb_clx]
    i = 0
    while i < len(clx) and clx[i] == 0x01:
        i += 3 + struct.unpack_from("<h", clx, i + 1)[0]
    if i >= len(clx) or clx[i] != 0x02:
        raise DocError("Pcdt 없음")
    lcb = struct.unpack_from("<I", clx, i + 1)[0]
    plc = clx[i + 5:i + 5 + lcb]
    n = (lcb - 4) // 12
    cps = struct.unpack_from("<%dI" % (n + 1), plc, 0)
    parts, spans = [], []
    for k in range(n):
        a, b = cps[k], cps[k + 1]
        if a >= want:
            break
        b = min(b, want)
        fc, prm = struct.unpack_from("<IH", plc, (n + 1) * 4 + k * 8 + 2)
        if fc & 0x40000000:
            o = (fc & 0x3FFFFFFF) // 2
            parts.append(wd[o:o + (b - a)].decode("cp1252", "replace"))
            spans.append((a, b, o, 1, prm))
        else:
            raw = wd[fc:fc + 2 * (b - a)]
            s = raw.decode("utf-16-le", "replace")
            parts.append(s if len(s) == b - a else _utf16_units(raw))
            spans.append((a, b, fc, 2, prm))
    text = "".join(parts)
    if len(text) < total:
        raise DocError("조각표가 이야기 끝까지 닿지 않음")

    def cut(t: str) -> tuple:
        return tuple(_join_surrogates(s) for s in (t[:ccp_text], t[ccp_text:ccp_text + ccp_ftn], t[edn_start:total],
                                                   t[total:want] if len(t) >= want else ""))

    stories = cut(text)
    if not props:
        return stories, None
    try:
        ctext = _ctx_text(text, *_char_marks(wd, tbl, pos, clx[:i], spans, len(text)))
    except (DocError, struct.error, IndexError, ValueError):
        STATS["LO 복원/글자 속성 판독 실패"] += 1
        return stories, False
    return stories, ((None,) * 4 if ctext is None else tuple(zip(cut(ctext[0]), cut(ctext[1]))))


# 앞 글 대조에 쓰는 글자 속성(sprm) — 변경 추적 삭제 표시(sprmCFRMarkDel, ToggleOperand)와 기호 글자
# (sprmCSymbol, 글꼴 번호 2바이트 + 그 글꼴의 글자 번호 2바이트). 기호 삽입으로 넣은 글자는 글 흐름에 '(' 로 남고
# 실제 글자는 이 속성에만 있다.
_SPRM_DEL, _SPRM_SYM = 0x0800, 0x6A09
# sprm 위 3비트(spra) → 피연산자 바이트 수. 6 은 첫 바이트가 나머지 길이다(표 정의 · 탭 바꿈 sprm 은 따로 —
# `_sprms` 가 멈춘다).
_SPRA_LEN = (1, 1, 2, 4, 2, 2, None, 3)
_SPRM_ODD = frozenset({0xD608, 0xC615})
# 변경 추적으로 지운 글자의 자리 표시 — 앞 글 이야기의 지운 글을 뺀 벌(`_ctx_text`)에 쓴다.
_GONE = "\ufdd0"
_GONE_RUNS = re.compile("%s+|[^%s]+" % (_GONE, _GONE))
_NOT_SURROGATE = re.compile("[^\ud800-\udfff]")


def _sprms(g: bytes):
    """grpprl 의 (sprm, 피연산자) 열. 피연산자가 grpprl 을 넘으면 DocError."""
    j = 0
    while j + 2 <= len(g):
        sprm = struct.unpack_from("<H", g, j)[0]
        if sprm in _SPRM_ODD:
            STATS["LO 복원/글자 속성/길이 다른 sprm 에서 멈춤"] += 1
            return
        j += 2
        n = _SPRA_LEN[sprm >> 13]
        if n is None:
            if j >= len(g):
                raise DocError("sprm 잘림")
            n = 1 + g[j]
        if j + n > len(g):
            raise DocError("sprm 잘림")
        yield sprm, g[j:j + n]
        j += n


def _props(g: bytes) -> dict:
    """grpprl 에서 앞 글에 쓰는 속성 — {'del': 삭제 표시 여부, 'sym': 기호 글자 번호} 가운데 걸린 것. 삭제 표시
    0x81(스타일 값의 반대)은 켬으로 읽는다 — 스타일의 삭제 표시는 기본값(꺼짐)으로 본다."""
    out = {}
    for sprm, op in _sprms(g):
        if sprm == _SPRM_DEL:
            out["del"] = op[0] in (0x01, 0x81)
        elif sprm == _SPRM_SYM:
            out["sym"] = struct.unpack_from("<H", op, 2)[0]
    return out


def _char_marks(wd: bytes, tbl: bytes, fib: int, rgprc: bytes, spans: list, ncp: int):
    """CP 마다의 삭제 표시(bytearray, 1 = 지움 · 없으면 None)와 기호 글자(CP → 글자 번호).

    글자 속성은 FKP 의 CHPX(PlcBteChpx 가 가리키는 512바이트 쪽)에 FC 범위로 있고, 조각(Pcd)의 Prm 이 그 위를
    덮는다. FC 는 조각표로 CP 로 옮긴다 — 압축 조각은 한 글자 1바이트, 아니면 2바이트."""
    fc_bte, lcb_bte = struct.unpack_from("<II", wd, fib + 2 + 12 * 8)
    n = (lcb_bte - 4) // 8 if lcb_bte >= 12 else 0
    runs = []
    if n:
        plc = tbl[fc_bte:fc_bte + lcb_bte]
        for pn in struct.unpack_from("<%dI" % n, plc, (n + 1) * 4):
            o = (pn & 0x3FFFFF) * 512
            page = wd[o:o + 512]
            if len(page) < 512:
                raise DocError("CHPX 쪽이 스트림 밖")
            crun = page[511]
            rgfc = struct.unpack_from("<%dI" % (crun + 1), page, 0)
            for r in range(crun):
                off = page[(crun + 1) * 4 + r] * 2
                if off:
                    hit = _props(page[off + 1:off + 1 + page[off]])
                    if hit:
                        runs.append((rgfc[r], rgfc[r + 1], hit))
    gone, sym = bytearray(ncp), {}

    def apply(c1: int, c2: int, hit: dict) -> None:
        c2 = min(c2, ncp)
        if c1 >= c2:
            return
        if "del" in hit:
            gone[c1:c2] = (b"\x01" if hit["del"] else b"\x00") * (c2 - c1)
        if "sym" in hit:
            for c in range(c1, c2):
                sym[c] = hit["sym"]

    order = sorted((start, start + (b - a) * w, a, w) for a, b, start, w, _prm in spans)
    starts = [o[0] for o in order]
    for f1, f2, hit in runs:
        k = max(0, bisect.bisect_right(starts, f1) - 1)
        while k < len(order) and order[k][0] < f2:
            s, e, a, w = order[k]
            lo, hi = max(f1, s), min(f2, e)
            if lo < hi:
                apply(a + (lo - s) // w, a + (hi - s + w - 1) // w, hit)
            k += 1
    prcs, j = [], 0
    while j < len(rgprc) and rgprc[j] == 0x01:
        cb = struct.unpack_from("<h", rgprc, j + 1)[0]
        prcs.append(rgprc[j + 3:j + 3 + cb])
        j += 3 + cb
    for a, b, _start, _w, prm in spans:
        if prm & 1:
            if prm >> 1 >= len(prcs):
                raise DocError("Prm 이 가리키는 Prc 없음")
            hit = _props(prcs[prm >> 1])
            if hit:
                apply(a, b, hit)
        elif prm:
            STATS["LO 복원/글자 속성/Prm0"] += 1
    if gone.find(b"\x01") < 0:
        gone = None
    return gone, sym


def _ctx_text(text: str, gone, sym: dict) -> tuple[str, str] | None:
    """앞 글 대조용 글자열 두 벌(지운 글을 넣은 벌, 뺀 벌) — 둘 다 text 와 길이가 같다. 기호 자리 표시 '(' 는
    기호 글자(`_sym_char`)로 바꾸고, 뺀 벌에서는 지운 글자를 `_GONE` 으로 바꾼다. 대리 글자는 그대로 둬
    `_join_surrogates` 뒤에도 세 글의 길이가 같다. 바꿀 것이 없으면 None."""
    if gone is None and not sym:
        return None
    if sym:
        chars = list(text)
        for cp, code in sym.items():
            if chars[cp] == "(":
                chars[cp] = _sym_char(code)
        text = "".join(chars)
    if gone is None:
        return text, text
    out, last = [], 0
    for m in re.finditer(b"\x01+", gone):
        out.append(text[last:m.start()])
        out.append(_NOT_SURROGATE.sub(_GONE, text[m.start():m.end()]))
        last = m.end()
    out.append(text[last:])
    return text, "".join(out)


def _sym_char(code: int) -> str:
    """기호 글꼴 글자의 앞 글 꼴. LibreOffice 는 기호 글꼴 글자를 docx 에 사용자 정의 영역 글자(U+F020~U+F0FF)나
    그 아래 바이트의 보통 글자로 쓰므로 둘 다 아래 바이트 글자로 읽는다. U+F000~U+F01F 와 대리 글자 번호는 '('."""
    if 0xF020 <= code <= 0xF0FF:
        return chr(code - 0xF000)
    if 0xF000 <= code < 0xF020 or 0xD800 <= code <= 0xDFFF:
        return "("
    return chr(code)


# ---------------------------------------------------------------------------------------------------------------
# 필드 — 양쪽(.doc 글자열 · docx 트리)에서 같은 꼴로 모은다.
#   leaf         안에 다른 필드가 없다(짝짓기는 이 필드만 정렬에 넣는다)
#   ctx          필드 시작 앞 글의 마지막 낱말들 두 벌(`_Ctx.tail`). 앞 글 = 모든 바깥 필드가 결과 상태의
#                HYPERLINK 인 자리의 글.
#                HYPERLINK 가 아닌 필드의 구분 · 끝 표지는 낱말을 끊는다.
#   code         정규화한 명령문(안쪽 필드는 빼고)
#   gone         시작 표지가 변경 추적으로 지운 글 안에 있다

class _Field:
    __slots__ = ("kind", "arg", "sw", "leaf", "ctx", "state", "instr", "hyper", "code", "gone")

    def __init__(self, ctx: tuple):
        self.ctx = ctx
        self.leaf, self.hyper, self.gone = True, False, False
        self.state, self.instr = "instr", []
        self.kind, self.arg, self.sw, self.code = "?", "", frozenset(), ""

    def finish_instr(self) -> None:
        self.code = norm("".join(self.instr))
        self.kind, self.arg, self.sw = split_instr(self.code)
        self.hyper = self.kind == "HYPERLINK"
        self.instr = []

    @property
    def key(self) -> tuple[str, str]:
        return self.kind, self.arg.lower()


class DocField(_Field):
    __slots__ = ("text", "sep", "end", "ctext", "props")

    def raw_result(self) -> str | None:
        if self.sep is None or self.end is None:
            return None
        return _visible(self.text[self.sep + 1:self.end])

    def value(self) -> tuple[str | None, str]:
        """(되돌릴 값, 까닭). 값이 None 이면 까닭이 쓸 수 없는 이유다.

        결과 끝의 문단 표지는 필드 끝이 다음 문단에 있다는 뜻일 뿐이라 뗀다. 표 칸 표지가 든 결과는 표 구조를
        건너므로 쓰지 않는다. 안쪽의 문단 · 줄 · 쪽 · 단 나눔은 줄바꿈('\\n')으로 바꿔 `_set_result` 가 w:br 로
        쓴다 — 결과가 docx 에서 여러 문단에 걸치면 `judge` 가 따로 막는다. 결과에 변경 추적으로 지운 글이나 기호 글자
        (글 흐름에는 '(' 로만 남는다)가 들면 글 흐름만으로는 값을 알 수 없으므로 쓰지 않는다. 글자 속성을 못 읽은
        문서는 그 둘을 가릴 수 없어 쓰지 않는다."""
        raw = self.raw_result()
        if raw is None:
            return None, "doc결과없음"
        if not self.props:
            return None, "doc속성판독실패"
        if self.ctext is not None:
            keep, drop = self.ctext
            if _GONE in drop[self.sep + 1:self.end]:
                return None, "doc삭제글"
            if keep[self.sep + 1:self.end] != self.text[self.sep + 1:self.end]:
                return None, "doc기호"
        v = raw.translate(_VALUE_MAP).rstrip("\r")
        if "\x07" in v:
            return None, "doc표칸"
        v = v.translate(_VALUE_BREAKS)
        if any(ord(c) < 32 and c not in "\t\n" for c in v):
            return None, "doc제어문자"
        if not v.strip():
            return None, "doc빈결과"
        return v, ""


_MARK = re.compile("[\x13\x14\x15]")
_PUA = re.compile("[\uf000-\uf0ff]")
# 앞 글을 대조할 때 양쪽에 함께 쓰는 글자 바꿈. 기호 글꼴 글자(U+F000~U+F0FF)는 `_sym_char` 로 읽는다.
# 선택 하이픈(U+00AD)은 지우고 줄바꿈 없는 하이픈(U+2011)은 '-' — .doc 의 0x1F · 0x1E 와 같은 글자다.
_X_CTX = {c: _sym_char(c) for c in range(0xF000, 0xF100)}
_X_CTX.update({0xAD: None, 0x2011: "-"})
# .doc 앞 글 — 제어 문자는 낱말을 끊고, 선택 하이픈(0x1F)은 지우고, 줄바꿈 없는 하이픈(0x1E)은 '-'.
# 각주 · 미주 · 메모 참조 표지(0x02 · 0x05, docx 참조 요소)는 글 사이에 붙는 자리 표시라 낱말을 끊지 않는다.
# LibreOffice 가 글상자 안 메모를 버리는 등 한쪽에만 남는 일이 있어 양쪽 모두 폭 없이 읽는다. 떠 있는 그리기
# 개체의 닻(0x08)도 폭 없이 읽는다 — docx 의 떠 있는 그림(wp:anchor)과 같다.
_DOC_CTX = {c: " " for c in range(32)}
_DOC_CTX.update({0x1F: None, 0x1E: "-", 0x02: None, 0x05: None, 0x08: None})
_DOC_CTX.update(_X_CTX)
# 되돌릴 값 — 그림 · 각주 표지 · 메모 표지 · 그리기 개체 · 선택 하이픈은 지우고 0x1E 는 '-'.
_VALUE_MAP = {0x01: None, 0x02: None, 0x05: None, 0x08: None, 0x1F: None, 0x1E: "-"}
# 되돌릴 값 안의 나눔 — 문단 표지(0x0D) · 줄 나눔(0x0B) · 쪽 · 구역 나눔(0x0C) · 단 나눔(0x0E).
_VALUE_BREAKS = {0x0D: "\n", 0x0B: "\n", 0x0C: "\n", 0x0E: "\n"}


def _visible(s: str) -> str:
    """표지 섞인 결과 글에서 안쪽 필드의 명령문을 빼고 결과만 남긴다."""
    if "\x13" not in s:
        return s
    out, stack = [], []
    last = 0
    for m in _MARK.finditer(s):
        if not stack or all(x == "result" for x in stack):
            out.append(s[last:m.start()])
        ch = m.group()
        if ch == "\x13":
            stack.append("instr")
        elif ch == "\x14":
            if stack:
                stack[-1] = "result"
        elif stack:
            stack.pop()
        last = m.end()
    if not stack or all(x == "result" for x in stack):
        out.append(s[last:])
    return "".join(out)


def _symbol_char(f: _Field) -> str:
    """SYMBOL 필드가 그리는 글자의 앞 글 꼴. 글자 번호는 10진수나 0x 16진수다. \\u 는 유니코드 번호, \\j 는
    Shift-JIS 번호(읽지 않고 '('), 그 밖의 256 미만 번호는 cp1252 바이트로 읽는다. 못 읽으면 '('."""
    a = f.arg.strip('"')
    try:
        n = int(a, 16) if a[:2].lower() == "0x" else int(a)
    except ValueError:
        return "("
    if "\\j" in f.sw or not 0 < n < 0x110000:
        return "("
    if "\\u" in f.sw or n >= 256:
        return _sym_char(n)
    return bytes([n]).decode("cp1252", "replace")


def _breaks(f: _Field) -> bool:
    """필드의 구분 · 끝 표지가 앞 글의 낱말을 끊는가. HYPERLINK 결과는 본문이고, SYMBOL 필드는 글자 하나를
    그린다(`_symbol_char` 를 끝 표지에서 앞 글에 넣는다). 지운 필드의 표지는 지운 글을 뺀 벌에서 끊지 않는다."""
    return not (f.hyper or f.kind == "SYMBOL")


def doc_fields(text: str, log: list | None = None, ctext: tuple | None = None, props: bool = True,
               dlog: list | None = None) -> list[DocField]:
    """.doc 이야기 글자열의 필드를 시작 표지 차례로. log · dlog 를 주면 앞 글 두 벌로 읽은 낱말을 모두 거기에
    남긴다(`_Ctx`). ctext 는 같은 이야기의 앞 글 이야기 두 벌(`_doc_read`), props 는 글자 속성을 읽었는가다."""
    out: list[DocField] = []
    stack: list[DocField] = []
    ctx = _Ctx(log, dlog)
    keep, drop = ctext or (text, text)
    last = 0

    def in_ctx() -> bool:
        return all(f.state == "result" and f.hyper for f in stack)

    def segment(a: int, b: int) -> None:
        if a >= b:
            return
        if in_ctx():
            for m in _GONE_RUNS.finditer(drop, a, b):
                ctx.feed(keep[m.start():m.end()].translate(_DOC_CTX), m.group()[0] == _GONE)
        elif stack[-1].state == "instr":
            stack[-1].instr.append(text[a:b])

    for m in _MARK.finditer(text):
        segment(last, m.start())
        last = m.end()
        ch, i = m.group(), m.start()
        if ch == "\x13":
            for f in stack:
                f.leaf = False
            f = DocField(ctx.tail())
            f.text, f.sep, f.end, f.ctext, f.props = text, None, None, ctext, props
            f.gone = drop[i] == _GONE
            stack.append(f)
            out.append(f)
        elif ch == "\x14":
            if stack and stack[-1].state == "instr":
                f = stack[-1]
                f.state, f.sep = "result", i
                f.finish_instr()
                if _breaks(f):
                    ctx.space(f.gone)
        elif stack:
            f = stack.pop()
            f.end = i
            if f.state == "instr":
                f.finish_instr()
            if _breaks(f):
                ctx.space(f.gone)
            elif f.kind == "SYMBOL" and in_ctx():
                ctx.feed(_symbol_char(f), f.gone)
    segment(last, len(text))
    ctx.space()
    return out


class XField(_Field):
    """docx 필드. direct = 이 필드가 맨 안쪽인 결과 자리의 w:t, extra = 같은 자리의 탭 · 줄바꿈 따위 요소.
    sep_mark = 구분 표지(w:fldChar separate, 단순 필드면 w:fldSimple 자신), end_mark = 끝 표지(w:fldChar end)."""

    __slots__ = ("direct", "extra", "parts", "multi", "change", "other", "sep_para", "sep_run", "has_sep",
                 "sep_mark", "end_mark")

    def __init__(self, ctx: tuple):
        super().__init__(ctx)
        self.direct, self.extra, self.parts = [], [], []
        self.multi = self.change = self.other = self.has_sep = False
        self.sep_para, self.sep_run, self.sep_mark, self.end_mark = -1, None, None, None

    def text(self) -> str:
        return "".join(self.parts)


_X_BOX = frozenset({W + "drawing", W + "pict", W + "object", MC + "AlternateContent", W + "txbxContent"})
# LibreOffice 가 .doc 의 수식 개체(EMBED Equation 필드)를 바꾼 OMML 수식. .doc 에서는 필드라서 앞 글의 낱말을
# 끊으므로 docx 에서도 그림처럼 다른 내용으로 다룬다.
_X_MATH = frozenset({M + "oMath", M + "oMathPara"})
_X_PROPS = frozenset({W + t for t in ("pPr", "rPr", "sdtPr", "sdtEndPr", "tblPr", "trPr", "tcPr", "sectPr",
                                      "tblGrid", "bookmarkStart", "bookmarkEnd", "proofErr")})
_X_MARKS = frozenset({W + t for t in ("footnoteReference", "endnoteReference", "footnoteRef", "endnoteRef",
                                      "commentReference", "separator", "continuationSeparator", "sym")})
_X_ANCHORS = frozenset({W + t for t in ("footnoteReference", "endnoteReference", "footnoteRef", "endnoteRef",
                                        "commentReference")})
_X_BREAKS = {W + "tab": "\t", W + "ptab": "\t", W + "br": "\n", W + "cr": "\n", W + "noBreakHyphen": "-",
             W + "softHyphen": ""}
_X_CHANGES = frozenset({W + "ins", W + "del", W + "moveFrom", W + "moveTo"})
# 변경 추적으로 지운 글 — 옮겨 간 글의 원래 자리(moveFrom)는 w:delText 가 아니라 w:t 로 적힌다.
_X_GONE = frozenset({W + "del", W + "moveFrom"})
_WP = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"


def _floating(el) -> bool:
    """떠 있는 그림(wp:anchor) — 글 사이에 자리를 차지하지 않는다."""
    if el.tag == MC + "AlternateContent":
        el = el.find(MC + "Choice/" + W + "drawing")
        if el is None:
            return False
    return el.tag == W + "drawing" and el.find(_WP + "anchor") is not None


def _mark_gone(p) -> bool:
    """문단 표지가 변경 추적으로 지워졌는가 — 그러면 이 문단은 다음 문단과 이어진다."""
    rpr = p.find(W + "pPr/" + W + "rPr")
    return rpr is not None and (rpr.find(W + "del") is not None or rpr.find(W + "moveFrom") is not None)


def _sym_attr(el) -> str:
    try:
        return _sym_char(int(el.get(W + "char") or "", 16))
    except ValueError:
        return "("


class _XWalk:
    def __init__(self, log: list | None = None, dlog: list | None = None):
        self.fields: list[XField] = []
        self.stack: list[XField] = []
        self.ctx = _Ctx(log, dlog)
        self.para = 0
        self.gone = 0
        self.join = False

    def in_ctx(self) -> bool:
        return all(f.state == "result" and f.hyper for f in self.stack)

    def result_top(self) -> XField | None:
        return self.stack[-1] if self.stack and self.stack[-1].state == "result" else None

    def open(self) -> XField:
        for f in self.stack:
            f.leaf = False
        f = XField(self.ctx.tail())
        f.gone = self.gone > 0
        self.stack.append(f)
        self.fields.append(f)
        return f

    def separate(self, f: XField, run, mark) -> None:
        f.state, f.has_sep, f.sep_para, f.sep_run, f.sep_mark = "result", True, self.para, run, mark
        f.finish_instr()
        if _breaks(f):
            self.ctx.space(f.gone)

    def close(self, end_mark=None) -> None:
        f = self.stack.pop()
        f.end_mark = end_mark
        if f.state == "instr":
            f.finish_instr()
        elif self.para != f.sep_para:
            f.multi = True
        if _breaks(f):
            self.ctx.space(f.gone)
        elif f.kind == "SYMBOL" and self.in_ctx():
            self.ctx.feed(_symbol_char(f), f.gone)

    def mark_change(self) -> None:
        for f in self.stack:
            if f.state == "result":
                f.change = True

    def mark_other(self) -> None:
        for f in self.stack:
            if f.state == "result":
                f.other = True

    def walk(self, el) -> None:
        tag = el.tag
        if not isinstance(tag, str) or tag in _X_PROPS:
            return
        if tag in _X_BOX or tag in _X_MATH:
            self.mark_other()
            if not _floating(el):
                self.ctx.space(self.gone > 0)
            return
        if tag == W + "t" or tag == W + "delText":
            t = el.text or ""
            if self.in_ctx():
                self.ctx.feed(t.translate(_X_CTX), self.gone > 0 or tag == W + "delText")
            top = self.result_top()
            if top is not None:
                if tag == W + "delText":
                    self.mark_change()
                else:
                    if _PUA.search(t):
                        # 기호 글꼴 글자 — .doc 값에는 그 자리가 '(' 로만 남아 되돌리면 글자가 깨진다.
                        self.mark_other()
                    top.direct.append(el)
                    top.parts.append(t)
                    if self.para != top.sep_para:
                        top.multi = True
            return
        if tag in _X_BREAKS:
            ch = _X_BREAKS[tag]
            if self.in_ctx():
                self.ctx.feed(" " if ch in "\t\n" else ch, self.gone > 0)
            top = self.result_top()
            if top is not None:
                top.extra.append(el)
                top.parts.append(ch)
            return
        if tag in _X_MARKS:
            self.mark_other()
            if tag == W + "sym":
                if self.in_ctx():
                    self.ctx.feed(_sym_attr(el), self.gone > 0)
            elif tag not in _X_ANCHORS:
                self.ctx.space(self.gone > 0)
            return
        if tag == W + "fldChar":
            typ = el.get(W + "fldCharType")
            if typ == "begin":
                self.open()
            elif typ == "separate" and self.stack and self.stack[-1].state == "instr":
                self.separate(self.stack[-1], el.getparent(), el)
            elif typ == "end" and self.stack:
                self.close(el)
            return
        if tag == W + "instrText" or tag == W + "delInstrText":
            if self.stack and self.stack[-1].state == "instr":
                self.stack[-1].instr.append(el.text or "")
            return
        if tag == W + "fldSimple":
            f = self.open()
            f.instr.append(el.get(W + "instr") or "")
            self.separate(f, el, el)
            for ch in el:
                self.walk(ch)
            self.close()
            return
        if tag == W + "p":
            self.para += 1
            self.ctx.space(self.join)
            self.join = False
            for ch in el:
                self.walk(ch)
            self.join = _mark_gone(el)
            self.ctx.space(self.join)
            return
        if tag in _X_CHANGES:
            self.mark_change()
        if tag in _X_GONE:
            self.gone += 1
            for ch in el:
                self.walk(ch)
            self.gone -= 1
            return
        for ch in el:
            self.walk(ch)


def docx_fields(root) -> list[XField]:
    """docx 부품 트리의 필드를 시작 차례로. 글상자 안(.doc 에서는 다른 이야기)은 걷지 않는다."""
    w = _XWalk()
    w.walk(root)
    while w.stack:
        w.close()
    return w.fields


def box_contents(root) -> tuple[list, list]:
    """본문의 글상자(w:txbxContent)를 문서 차례로 두 벌 — 그림 자리(mc:Fallback 밖) · 대체 자리(mc:Fallback 안).
    LibreOffice 는 한 글상자를 두 자리에 모두 쓰므로 벌마다 따로 .doc 글상자 이야기와 짝짓는다. 다른 글상자 안의
    글상자는 바깥 글상자를 걸을 때 건너뛰므로 넣지 않는다."""
    main, fallback = [], []
    for tb in root.iter(W + "txbxContent"):
        a, in_fallback = tb.getparent(), False
        while a is not None and a.tag != W + "txbxContent":
            if a.tag == MC + "Fallback":
                in_fallback = True
            a = a.getparent()
        if a is None:
            (fallback if in_fallback else main).append(tb)
    return main, fallback


def box_fields(boxes: list, log: list | None = None, dlog: list | None = None) -> list[XField]:
    """글상자들의 필드를 한 이야기처럼 이어 걸어 시작 차례로. log · dlog 는 doc_fields 와 같다."""
    w = _XWalk(log, dlog)
    for tb in boxes:
        for ch in tb:
            w.walk(ch)
        while w.stack:
            w.close()
        w.ctx.space()
    return w.fields


def pairs(xfields: list[XField], dfields: list[DocField]):
    """양쪽의 leaf 필드를 (종류, 첫 인자) 열로 정렬해 맞는 덩어리 안의 짝을 낸다. 한쪽에만 있는 종류는
    정렬에서 뺀다(LibreOffice 가 지우거나 새로 만든 필드 — EMBED · PAGE · TOC 따위)."""
    xs, ds = [f for f in xfields if f.leaf], [f for f in dfields if f.leaf]
    kinds = ({f.kind for f in xs} & {f.kind for f in ds}) - _NEVER_ALIGN
    xs = [f for f in xs if f.kind in kinds]
    ds = [f for f in ds if f.kind in kinds]
    sm = difflib.SequenceMatcher(None, [f.key for f in xs], [f.key for f in ds], autojunk=False)
    for a, b, size in sm.get_matching_blocks():
        for t in range(size):
            yield xs[a + t], ds[b + t]


def hidden_run(r) -> bool:
    rpr = r.find(W + "rPr") if r is not None else None
    if rpr is None:
        return False
    for tag in ("vanish", "specVanish"):
        e = rpr.find(W + tag)
        if e is not None and (e.get(W + "val") or "true").lower() not in _FALSE:
            return True
    return False


def same_ctx(x: _Field, d: _Field) -> bool:
    """두 필드의 앞 글 마지막 낱말 `CTX_WORDS` 개가 두 벌(`_Ctx`) 가운데 어느 한 벌에서 같은가."""
    return any(a == b for a, b in zip(x.ctx, d.ctx))


def judge(x: XField, d: DocField) -> tuple[str, str | None]:
    """(판정, 되돌릴 값). 판정이 '되돌림' · '공백만다름' · '채움' · '채움구분더함' 일 때만 값을 쓴다.

    결과 글이 없는 필드는 채운다 — 구분 표지가 있으면 그 뒤에('채움'), 명령문만 있으면 끝 표지 앞에 구분
    표지와 함께('채움구분더함'). 그 표지의 run 이 숨김이면 채우지 않는다."""
    if not same_ctx(x, d):
        return "앞글다름", None
    if x.sw - _LO_SWITCHES != d.sw - _LO_SWITCHES:
        return "스위치다름", None
    value, why = d.value()
    if value is None:
        return why, None
    if not x.leaf:
        return "docx중첩", None
    if x.multi:
        return "docx여러문단", None
    if x.other:
        return "docx그림등", None
    if x.change:
        return "docx변경표시", None
    if not x.direct:
        if x.has_sep:
            if x.sep_mark.tag == W + "fldChar" and hidden_run(x.sep_run):
                return "docx숨김", None
            return "채움", value
        if x.end_mark is None:
            return "docx끝표지없음", None
        if hidden_run(x.end_mark.getparent()):
            return "docx숨김", None
        return "채움구분더함", value
    if all(hidden_run(t.getparent()) for t in x.direct):
        return "docx숨김", None
    cur = x.text()
    if cur == value:
        return "같음", None
    if norm(cur) == norm(value):
        return "공백만다름", value
    return "되돌림", value


def _write_lines(t, value: str) -> None:
    """w:t 하나에 값을 쓴다. 값의 줄바꿈마다 w:br 과 새 w:t 를 그 뒤에 잇는다."""
    lines = value.split("\n")
    t.text = lines[0]
    t.set(_XML_SPACE, "preserve")
    prev = t
    for line in lines[1:]:
        br = t.makeelement(W + "br", {})
        nt = t.makeelement(W + "t", {_XML_SPACE: "preserve"})
        nt.text = line
        prev.addnext(br)
        br.addnext(nt)
        prev = nt


def _set_result(x: XField, value: str) -> None:
    first = next(t for t in x.direct if not hidden_run(t.getparent()))
    for t in x.direct:
        if t is not first:
            t.text = ""
    for e in x.extra:
        parent = e.getparent()
        if parent is not None:
            parent.remove(e)
    _write_lines(first, value)


def _fill_result(x: XField, value: str, add_sep: bool) -> None:
    """결과 글이 없는 필드에 값을 쓴다(`judge` 의 '채움' · '채움구분더함')."""
    if add_sep:
        end = x.end_mark
        sep = end.makeelement(W + "fldChar", {W + "fldCharType": "separate"})
        t = end.makeelement(W + "t", {})
        end.addprevious(sep)
        end.addprevious(t)
    elif x.sep_mark.tag == W + "fldSimple":
        r = x.sep_mark.makeelement(W + "r", {})
        t = r.makeelement(W + "t", {})
        r.append(t)
        x.sep_mark.append(r)
    else:
        t = x.sep_mark.makeelement(W + "t", {})
        x.sep_mark.addnext(t)
    _write_lines(t, value)


def _blank_result(x: XField) -> None:
    for t in x.direct:
        t.text = ""
    for e in x.extra:
        parent = e.getparent()
        if parent is not None:
            parent.remove(e)


# ---------------------------------------------------------------------------------------------------------------
# LibreOffice 변환본 찾기와 .doc 읽기

@functools.lru_cache(maxsize=1024)
def _sibling_docs(folder: str) -> dict[str, str]:
    try:
        names = os.listdir(folder)
    except OSError:
        return {}
    return {n[:-4].lower(): n for n in names if n.lower().endswith(".doc")}


def _made_by_lo(path: str, zf) -> bool:
    try:
        if zf is not None:
            return b"LibreOffice" in zf.read("docProps/app.xml")
        with zipfile.ZipFile(path) as z:
            return b"LibreOffice" in z.read("docProps/app.xml")
    except (KeyError, OSError, zipfile.BadZipFile):
        return False


def lo_source(docx_path, zf=None) -> str | None:
    """LibreOffice 로 바꾼 .docx 이면 옆의 원본 .doc 경로, 아니면 None."""
    if docx_path is None:
        return None
    path = os.fspath(docx_path)
    folder, name = os.path.split(path)
    stem, ext = os.path.splitext(name)
    if ext.lower() != ".docx":
        return None
    doc = _sibling_docs(folder or ".").get(stem.lower())
    if doc is None or not _made_by_lo(path, zf):
        return None
    return os.path.join(folder, doc)


_SEP = "\x1f"


def _joined(words) -> str:
    """낱말 열을 구분자로 이어 감싼 글. 부분 열 검사(`in`)가 낱말 경계에서만 맞는다."""
    return _SEP + _SEP.join(words) + _SEP


@functools.lru_cache(maxsize=4)
def _doc_parsed(path: str, mtime: float, size: int):
    try:
        with open(path, "rb") as f:
            stories, cst = _doc_read(f.read(), True)
    except (DocError, struct.error, OSError, IndexError, ValueError) as e:
        STATS["LO 복원/원본 .doc 판독 실패"] += 1
        STATS["LO 복원/원본 .doc 판독 실패/" + (e.args[0] if isinstance(e, DocError) else type(e).__name__)] += 1
        return None
    props = cst is not False
    ctexts = cst or (None,) * 4
    main: list[str] = []
    dmain: list[str] = []
    words: list[str] = []
    dwords: list[str] = []
    logs = ((main, dmain), (None, None), (None, None), (words, dwords))
    fields = [doc_fields(s, log, c, props, dlog) for s, c, (log, dlog) in zip(stories, ctexts, logs)]
    return (*fields, (tuple(words), tuple(dwords)), (_joined(main), _joined(dmain)), (_joined(words), _joined(dwords)))


def doc_load(path: str):
    """원본 .doc 의 이야기별 필드 목록(본문 · 각주 · 미주 · 글상자), 글상자 이야기의 낱말, 본문 · 글상자 이야기의
    이은 낱말 열(`_joined`, 틀 판정용). 낱말과 이은 낱말 열은 앞 글 두 벌(`_Ctx`)의 짝이다. 못 읽으면 None."""
    try:
        st = os.stat(path)
    except OSError:
        return None
    return _doc_parsed(path, st.st_mtime, st.st_size)


# ---------------------------------------------------------------------------------------------------------------
# 손질

_FRAME_HOSTS = (MC + "AlternateContent", W + "drawing", W + "pict")


def _frame_host(tb):
    """글상자를 담은 가장 바깥 그림 요소와 그 닻 문단. 닻 문단이 없으면 (None, None)."""
    host, a = None, tb.getparent()
    while a is not None and a.tag != W + "p":
        if a.tag in _FRAME_HOSTS:
            host = a
        a = a.getparent()
    return (host, a) if a is not None else (None, None)


def _unwrap_frames(root, doc_path: str) -> int:
    """LibreOffice 가 .doc 의 틀을 글상자로 내보낸 것을 닻 문단 앞 본문 자리로 되돌린다.

    그림 자리 글상자(`box_contents` 첫 벌) 가운데 앞 글 두 벌(`_Ctx`)의 어느 한 벌에서 낱말 열이 비지 않고, .doc
    글상자 이야기에는 없고, .doc 본문 낱말 열에 이어서 나오는 것을 틀로 본다. 글상자 이름(wp:docPr)은 LibreOffice 가 틀과 글상자에 모두 'Frame N' 을
    붙여 가르지 못한다. 안의 블록(문단 · 표)을 닻 문단 앞에 차례대로 옮기고, 그림 요소(대체 자리 사본 포함)를
    지운 뒤 비게 된 run 도 지운다. 닻 문단 앞에 놓아야 docx 본문 낱말 열이 .doc 본문과 맞는다 — WG 별 오류 · 대조
    표본 여덟 무리에서 .doc 본문과 다른 낱말 수가 앞에 놓으면 모두 줄고(늘어난 TDoc 없음), 뒤에 놓으면 더 많이
    남았다(RAN4 오류 표본: 고치기 전 7,882 · 앞 107 · 뒤 1,765). 한 그림 요소에 그림 자리 글상자가 여럿이면(묶음
    도형) 지우면 다른 글상자도 사라지므로 두고 센다."""
    parsed = doc_load(doc_path)
    if parsed is None:
        return 0
    main, boxes = parsed[5], parsed[6]
    found = []
    for tb in box_contents(root)[0]:
        words: list[str] = []
        dwords: list[str] = []
        box_fields([tb], words, dwords)
        if any(w and _joined(w) not in b and _joined(w) in m for w, m, b in zip((words, dwords), main, boxes)):
            found.append((tb, *_frame_host(tb)))
    n = 0
    for tb, host, p in found:
        if host is None:
            STATS["틀 되돌림/그림 요소 없음"] += 1
            continue
        if len(box_contents(host)[0]) != 1:
            STATS["틀 되돌림/묶음 도형이라 둠"] += 1
            continue
        for ch in list(tb):
            p.addprevious(ch)
        run = host.getparent()
        run.remove(host)
        if run.tag == W + "r" and not any(isinstance(c.tag, str) and c.tag != W + "rPr" for c in run):
            run.getparent().remove(run)
        n += 1
    STATS["틀 되돌림"] += n
    return n


def _restore(root, story: int, doc_path: str) -> int:
    """본문 부품이면 글상자도 .doc 글상자 이야기(3)와 따로 짝지어 되돌린다.

    글상자는 docx 에서는 문서 안 고정 위치 차례로, .doc 에서는 글상자 이야기 차례로 이어 걸으므로 두 차례가 다르거나
    한쪽에만 있는 글상자가 있으면 필드가 다른 글상자의 필드와 짝지어진다(틀은 `_unwrap_frames` 가 먼저 본문으로
    되돌린다). 이야기 첫 필드는 앞 글이 짧아 앞 글 대조로 막히지 않으므로, 양쪽 낱말 열이 같을 때만 짝짓는다."""
    parsed = doc_load(doc_path)
    if parsed is None:
        return 0
    n = _restore_fields(docx_fields(root), parsed[story], "")
    if story == 0 and parsed[3]:
        for boxes in box_contents(root):
            if not boxes:
                continue
            words: list[str] = []
            dwords: list[str] = []
            xfields = box_fields(boxes, words, dwords)
            if tuple(words) != parsed[4][0] and tuple(dwords) != parsed[4][1]:
                STATS["LO 복원/글상자/글다름"] += sum(1 for _ in pairs(xfields, parsed[3]))
                continue
            n += _restore_fields(xfields, parsed[3], "글상자/")
    return n


def _restore_fields(xfields: list[XField], dfields: list[DocField], tag: str) -> int:
    n = 0
    for x, d in pairs(xfields, dfields):
        verdict, value = judge(x, d)
        STATS["LO 복원/" + tag + verdict] += 1
        if value is None:
            continue
        if verdict.startswith("채움"):
            _fill_result(x, value, verdict == "채움구분더함")
        else:
            _set_result(x, value)
        n += 1
    return n


def _flat(s: str) -> str:
    return "".join(s.split())


def _in_text(codes, flat: str) -> set:
    """명령문 가운데 빈칸을 뺀 꼴이 빈칸을 뺀 부품 글에 든 것. 첫 낱말이 나오는 자리에서만 견준다."""
    table: dict = {}
    for c in codes:
        f = _flat(c)
        table.setdefault(c.split()[0], {}).setdefault(len(f), {}).setdefault(f, []).append(c)
    found = set()
    for head, by_len in table.items():
        for m in re.finditer(re.escape(head), flat):
            i = m.start()
            for n, same in by_len.items():
                found.update(same.get(flat[i:i + n], ()))
    return found


@functools.lru_cache(maxsize=4096)
def _code_re(code: str):
    """명령문이 낱말 경계로 든 자리(뒤따르는 빈칸까지). 명령문 낱말 사이는 어떤 빈칸 · 다른 내용 자리라도 된다."""
    return re.compile(r"(?<!\S)" + r"\s+".join(re.escape(t) for t in code.split()) + r"(?!\S)\s*")


_LEAK_STOP = _X_BOX | _X_MATH | _X_MARKS | frozenset(_X_BREAKS) | frozenset(
    {W + "p", W + "fldChar", W + "instrText", W + "delText", W + "delInstrText"})


def _para_slots(p) -> list:
    """문단 p 의 보이는 글 조각 — (w:t, 글), 또는 탭 · 줄바꿈 · 그림 · 필드 표지 · 안쪽 문단 같은 다른 내용
    자리면 (None, ' '). 다른 내용 자리는 낱말을 끊기만 하고 지우지 않는다."""
    out = []

    def walk(el):
        for ch in el:
            tag = ch.tag
            if not isinstance(tag, str) or tag in _X_PROPS:
                continue
            if tag == W + "t":
                out.append((ch, ch.text or ""))
            elif tag in _LEAK_STOP:
                out.append((None, " "))
            else:
                walk(ch)

    walk(p)
    return out


def _cut_slots(slots: list, spans: list) -> None:
    pos = 0
    for t, s in slots:
        a0 = pos
        pos += len(s)
        if t is not None and any(a < pos and b > a0 for a, b in spans):
            t.text = "".join(ch for k, ch in enumerate(s) if not any(a <= a0 + k < b for a, b in spans))


def _box_of(p):
    a = p.getparent()
    while a is not None and a.tag != W + "txbxContent":
        a = a.getparent()
    return a


class _LeakGroup:
    """명령문 누출을 함께 세는 문단 묶음 — 한 .doc 이야기에 맞서는 docx 자리 하나(본문 · 각주 · 미주 부품의
    글상자 밖, 또는 글상자 한 벌). have = 이 자리에 필드로 남은 명령문 수, cut = 이 자리에서 지운 수."""

    __slots__ = ("paras", "have", "cut")

    def __init__(self, paras: list, fields: list):
        self.paras, self.have, self.cut = paras, Counter(f.code for f in fields), Counter()


def _leak_groups(root, story: int) -> dict:
    out = {story: [_LeakGroup([p for p in root.iter(W + "p") if _box_of(p) is None], docx_fields(root))]}
    if story == 0:
        out[3] = [_LeakGroup([p for tb in boxes for p in tb.iter(W + "p") if _box_of(p) is tb], box_fields(boxes))
                  for boxes in box_contents(root) if boxes]
    return out


def _strip_pass(g: _LeakGroup, codes: list, want: Counter, odd: Counter) -> int:
    """한 묶음에서 명령문 자리를 찾아, 자리 수가 잃은 필드 수 이하인 명령문만 지운다. 긴 명령문부터 자리를
    차지하고, 짧은 명령문은 이미 차지된 자리와 겹치는 곳을 세지 않는다."""
    texts = []
    for p in g.paras:
        sl = _para_slots(p)
        texts.append((sl, "".join(s for _, s in sl)))
    taken: list = [[] for _ in texts]
    cuts: list = [[] for _ in texts]
    n = 0
    for c in sorted(codes, key=len, reverse=True):
        pat = _code_re(c)
        hits = [(j, m.start(), m.end()) for j, (_, s) in enumerate(texts) for m in pat.finditer(s)]
        hits = [(j, a, b) for j, a, b in hits if not any(x < b and y > a for x, y in taken[j])]
        if not hits:
            continue
        for j, a, b in hits:
            taken[j].append((a, b))
        lost = want[c] - g.have[c] - g.cut[c]
        if len(hits) > lost:
            odd["docx 에 같은 필드가 남음" if lost <= 0 else "글 자리가 잃은 필드보다 많음"] += len(hits)
            continue
        for j, a, b in hits:
            cuts[j].append((a, b))
        g.cut[c] += len(hits)
        STATS["명령문 누출/지움/" + c.split()[0].upper()] += len(hits)
        n += len(hits)
    for (sl, _), spans in zip(texts, cuts):
        if spans:
            _cut_slots(sl, spans)
    return n


def _strip_leaked_codes(root, story: int, doc_path: str) -> int:
    """LibreOffice 가 필드 대신 보이는 글로 써 버린 .doc 필드 명령문을 지운다.

    명령문(code)이 지울 대상이 되려면 셋이 모두 맞아야 한다 — .doc 같은 이야기의 보이는 글(명령문을 뺀 결과
    글)에 낱말 경계로 나오지 않고, docx 의 같은 자리 묶음에 그 명령문의 필드가 .doc 보다 적고(잃은 필드),
    묶음 안 글 자리 수가 잃은 필드 수 이하다. 본문 글이 우연히 명령문과 같으면 .doc 보이는 글에도 있으므로
    지우지 않는다. 지운 뒤 안쪽 명령문이 빠져 바깥 명령문이 이어지면 다음 차례에 다시 찾는다. 남긴 자리는
    `STATS` 의 '명령문 누출/모호' 로 센다."""
    parsed = doc_load(doc_path)
    if parsed is None:
        return 0
    stories = (story, 3) if story == 0 else (story,)
    want = {s: Counter(f.code for f in parsed[s] if f.code) for s in stories}
    if not any(want.values()):
        return 0
    shown: dict = {}
    seen: dict = {}
    groups = None
    total = 0
    while True:
        flat = _flat("".join(t.text or "" for t in root.iter(W + "t")))
        cands = {}
        for s in stories:
            keep = []
            for c in _in_text(want[s], flat):
                if (s, c) not in seen:
                    if s not in shown:
                        shown[s] = norm(_visible(parsed[s][0].text))
                    seen[s, c] = _code_re(c).search(shown[s]) is not None
                if not seen[s, c]:
                    keep.append(c)
            if keep:
                cands[s] = keep
        if not cands:
            break
        if groups is None:
            groups = _leak_groups(root, story)
        odd: Counter = Counter()
        n = sum(_strip_pass(g, cs, want[s], odd) for s, cs in cands.items() for g in groups.get(s, ()))
        if not n:
            for why, k in odd.items():
                STATS["명령문 누출/모호/" + why] += k
            break
        total += n
    return total


def _strip_field_errors(root) -> int:
    n = 0
    fields = docx_fields(root)
    for boxes in box_contents(root):
        fields += box_fields(boxes)
    for x in fields:
        if x.state != "result" or not x.direct:
            continue
        txt = norm("".join(t.text or "" for t in x.direct))
        if not (txt == LO_ERROR or _RESULT_ERROR.match(txt)):
            continue
        if x.multi:
            STATS["오류 글/여러 문단 결과라 둠"] += 1
            continue
        _mark_line(x.direct[0])
        _blank_result(x)
        STATS["오류 글/필드 결과 비움/" + x.kind] += 1
        n += 1
    return n


def _mark_line(e) -> None:
    """요소 e 가 든 문단에 오류 글을 지운 표지(`ERROR_LINE`)를 단다."""
    while e is not None and e.tag != W + "p":
        e = e.getparent()
    if e is not None:
        e.set(ERROR_LINE, "1")


def _own_texts(p) -> list:
    """문단 p 의 w:t 가운데 안쪽 문단(글상자)에 들지 않은 것."""
    out = []
    for t in p.iter(W + "t"):
        a = t.getparent()
        while a is not None and a.tag != W + "p":
            a = a.getparent()
        if a is p:
            out.append(t)
    return out


def _strip_loose_errors(root) -> int:
    n = 0
    for p in root.iter(W + "p"):
        ts = _own_texts(p)
        if not ts:
            continue
        s = "".join(t.text or "" for t in ts)
        spans = [(m.start(), m.start() + len(e)) for e in _LOOSE_ERRORS for m in re.finditer(re.escape(e), s)]
        if not spans:
            continue
        pos = 0
        for t in ts:
            txt = t.text or ""
            a0 = pos
            pos += len(txt)
            if any(a < pos and b > a0 for a, b in spans):
                t.text = "".join(ch for k, ch in enumerate(txt) if not any(a <= a0 + k < b for a, b in spans))
        p.set(ERROR_LINE, "1")
        STATS["오류 글/필드 밖 문구 지움"] += len(spans)
        n += len(spans)
    return n


_HIDDEN_TEXT = frozenset({W + t for t in ("t", "delText", "tab", "ptab", "br", "cr", "noBreakHyphen",
                                          "softHyphen", "sym")})


def _blank_hidden(root) -> int:
    n = 0
    for r in root.iter(W + "r"):
        if not hidden_run(r):
            continue
        gone = [ch for ch in r if ch.tag in _HIDDEN_TEXT]
        for ch in gone:
            r.remove(ch)
        if gone:
            n += 1
    if n:
        STATS["숨김 글/비운 run"] += n
    return n


def _settle(root, story: int, doc_path: str | None, errors: bool, hidden: bool) -> bool:
    changed = 0
    if doc_path is not None:
        if story == 0:
            changed += _unwrap_frames(root, doc_path)
        changed += _restore(root, story, doc_path)
        changed += _strip_leaked_codes(root, story, doc_path)
    if errors:
        changed += _strip_field_errors(root)
        changed += _strip_loose_errors(root)
    if hidden:
        changed += _blank_hidden(root)
    return changed > 0


def _parse(data: bytes, repair):
    parser = etree.XMLParser(huge_tree=True, resolve_entities=False)
    try:
        return etree.fromstring(data, parser)
    except etree.XMLSyntaxError:
        pass
    if repair is None:
        return None
    fixed, n = repair(data)
    if not n:
        return None
    try:
        return etree.fromstring(fixed, parser)
    except etree.XMLSyntaxError:
        return None


def settle_part(data: bytes, part: str, docx_path=None, zf=None, repair=None) -> bytes:
    """글 부품 바이트를 고쳐 돌려준다. 고칠 것이 없거나 엄격 파싱이 안 되면 받은 바이트 그대로.

    `repair` 는 엄격 파싱이 거절한 바이트를 고쳐 (바이트, 고친 수)를 돌려주는 함수다
    (`docx_text.drop_orphan_end_tags`). 고친 뒤 엄격 파싱이 되는 부품만 손질한다.
    """
    story = TEXT_PARTS.get(part)
    if story is None or not data:
        return data
    doc_path = lo_source(docx_path, zf)
    errors = _ERROR_GATE.search(data) is not None
    hidden = b"vanish" in data or b"specVanish" in data
    if doc_path is None and not errors and not hidden:
        return data
    root = _parse(data, repair)
    if root is None:
        STATS["부품 파싱 실패로 건너뜀"] += 1
        return data
    if not _settle(root, story, doc_path, errors, hidden):
        return data
    STATS["고친 부품"] += 1
    return etree.tostring(root, encoding="UTF-8", xml_declaration=True, standalone=True)


def settle_tree(root, part: str, docx_path=None) -> bool:
    """이미 파싱된 글 부품 트리(python-docx 의 `doc.element` 등)를 제자리에서 고친다. 고쳤으면 True."""
    story = TEXT_PARTS.get(part)
    if story is None or root is None:
        return False
    doc_path = lo_source(docx_path)
    hidden = next(root.iter(W + "vanish", W + "specVanish"), None) is not None
    errors = _ERROR_GATE_TEXT.search("".join(t.text or "" for t in root.iter(W + "t"))) is not None
    if doc_path is None and not errors and not hidden:
        return False
    if not _settle(root, story, doc_path, errors, hidden):
        return False
    STATS["고친 트리"] += 1
    return True
