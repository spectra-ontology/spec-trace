"""OLE 수식 개체의 미리보기 그림(WMF · EMF)을 선형 수식 글로 읽는다 — `Equation Native` 가 없거나 비었거나
미리보기와 어긋날 때 쓰는 대체 판독. 표기는 `mtef_linear.linear` 와 같은 규약(`_grp` · `_base` · `_open`)을 따른다.

읽는 순서:
  1. 글 조각을 글자로 나눈다 — 글자 간격(Dx)이 있으면 x_i = x + sum(Dx[:i]), 없으면 조각 하나를 한 덩어리로 둔다.
     MT Extra 부호는 `MTX` 의 넷만 글로 읽고, `ACCENT_MTX` 는 꾸밈표로, 나머지(괄호 · 화살표를 그리는 조각)는 버린다.
     따로 그린 꾸밈표 글자는 그 아래 글자에 결합 꾸밈표로 붙인다(`_accents`).
  2. 같은 x 에 쌓인 괄호 조각(⎛⎜⎝ …)을 괄호 하나로 합친다.
  3. 선: 수평선은 구조(분수 막대 · 근호 윗줄 · 윗줄), 수직선은 `|`, 사선은 `/`.
     근호는 윗줄 왼끝에서 끝나는 사선과 그 앞 사선 둘(꺾임 · 내림)을 그리기 순서대로 그린 것이다
     (38.211 · 38.901 의 Equation Editor 3 과 MathType 미리보기 모두).
  4. 구조를 짧은 수평선부터 접는다 — 위아래에 다 글이 있으면 분수, 아래에만 있으면 윗줄, 위에만 있으면 밑줄.
     분자 · 분모는 막대에 맞닿은 세로 연결 덩어리(세로 범위가 이어지는 요소)만 든다.
  5. 줄 읽기: 짝 맞는 괄호의 안을 따로 읽어 묶고, 주 글자 크기(H)보다 작은 요소를 앞 주 요소의 첨자로 붙인다
     (기준선보다 아래면 아래첨자, 위면 위첨자). 주 크기 요소의 기준선이 H 이상 떨어지면 다른 줄(`; `)이다.
요소의 세로 범위는 글자면 [기준선 − 글꼴 높이, 기준선], 선이면 꼭짓점 범위, 묶음이면 내용의 합이다.

수식 개체 안에 수식이 아닌 그림이 든 경우가 있다 — 38.104 · 38.108 · 38.174 의 TH 문단 수식 개체(그림 「Transmission
Bandwidth Configuration」, 같은 그림이 CR 둘에도 있다)는 해독 글이 「Nominal channel spacing=…」 인데 미리보기는 그 그림이다.
수식 편집기는 글을 기울여 그리지 않는다: 말뭉치의 수식 개체 미리보기 29,244 개 가운데 기울인 글꼴(Escapement≠0)로 그린 것은
이 그림 다섯뿐이고(조각 38 개씩), 나머지는 0 이다. 그래서 기울인 글이 있으면 그림으로 보고 읽지 않는다(`figure`)."""
import unicodedata

import docx_text
import glyph_width
import metafile_text
import mtef_linear

_grp, _base, _open, _OPEN, _seq = docx_text._grp, docx_text._base, docx_text._open, docx_text._OPEN, docx_text._seq

#: MT Extra 에서 글자로 읽는 부호 — 38.214 · 38.104 미리보기에서 해독 글의 … · ⋯ · ⋮ · ∪ 자리에 그려진 것
MTX = {0x4B: "…", 0x4C: "⋯", 0x4D: "⋮", 0x55: "∪"}
#: 꾸밈표(악센트)를 따로 그린 글자 → 결합 꾸밈표(`mtef_linear.EMBELL` 과 같은 글자). same 개체 census: Times New Roman
#: `~` 600 개 · `ˆ` 351 개는 바로 앞 글자보다 기준선이 높고(글꼴 높이의 0.3~0.6 배) 크기가 같다. MT Extra 0x25(물결 · 38.211
#: `x̃^(0)(i)`) · 0x26(점 · 38.901 `ẏ`, 두 개면 `ẍ`) · 0x29(뒤집힌 반달 · 38.101-4 `Ȇ_s`) · 0x72(벡터 화살 · 38.901 `v⃗(t)`).
#: 같은 census 에서 Times New Roman `´` · `` ` `` 은 해독 글에도 그 글자로 있는 보통 글자(38.101-4 `N_oc´` · 38.211 `β_(`SSS)`)라 넣지 않는다.
ACCENT_GLYPH = {"ˆ": chr(0x302), "~": chr(0x303)}
ACCENT_MTX = {0x25: chr(0x303), 0x26: chr(0x307), 0x29: chr(0x311), 0x72: chr(0x20D7)}
#: 같은 글자 위 점 꾸밈표 수 → 결합 꾸밈표(점 둘 · 셋)
DOTS = {2: chr(0x308), 3: chr(0x20DB)}
#: Symbol 글꼴 괄호 조각 → 괄호. ⎪ 는 왼 · 오른 중괄호가 함께 쓰는 이음 조각이라 같은 x 의 다른 조각을 따른다.
PIECES = {"⎛": "(", "⎜": "(", "⎝": "(", "⎞": ")", "⎟": ")", "⎠": ")",
          "⎡": "[", "⎢": "[", "⎣": "[", "⎤": "]", "⎥": "]", "⎦": "]",
          "⎧": "{", "⎨": "{", "⎩": "{", "⎫": "}", "⎬": "}", "⎭": "}",
          "⌠": "∫", "⎮": "∫", "⌡": "∫", "⎪": ""}
#: 위 모서리 조각만 있는 각괄호 = 올림, 아래 모서리 조각만 = 내림(38.212 `A'=⌈A/C⌉⋅C` 는 Symbol 0xE9 · 0xF9 한 개씩,
#: `⌊(25N_cb)/(50Z_c)⌋` 는 0xEB · 0xFB).
CEIL = {"[": "⌈", "]": "⌉"}
FLOOR = {"[": "⌊", "]": "⌋"}
OPENERS = {"(": ")", "[": "]", "{": "}", "⟨": "⟩", "⌈": "⌉", "⌊": "⌋"}
CLOSERS = set(OPENERS.values())
BIGOP = set("∑∏∐∫∬∭∮⋃⋂")
PRIME = set("′″‴")
#: 사선 분수의 피연산자를 끊는 기호 — 관계 · 더하기 · 곱하기 · 구분 기호와 괄호.
BOUND = set("=<>≤≥≠≈≡∼∝+-−±∓·⋅×÷∗,;:→←↔⇒∈∉()[]{}⌈⌉⌊⌋⟨⟩")
#: 가장 좁은 글자 폭 ÷ 글꼴 높이 — 38.211 · 38.214 · 38.901 MathType 미리보기의 글자 간격(Dx, 조각 끝 글자 제외)
#: 10,575 개 중 최솟값(프라임 `′` 0.125, 다음이 `'` 0.149). 글자 기준점이 세로선보다 이만큼도 앞서지 않으면 그 글자는
#: 세로선과 겹칠 수 없으니 선 뒤에 그린 것이다(38.901 `|τ_n…|` 의 τ 는 기준점이 선보다 6 앞, 글꼴 높이 384).
NARROW = 0.125
#: 칸 사이로 보는 가장 좁은 간격 ÷ H. 짝 하네스 개체 29,170 개에서 잰 간격(앞 주 요소와 그 첨자의 오른끝 → 다음 주 요소
#: 왼끝, 사이에 빈칸 글자가 없고 앞뒤가 쉼표 · 쌍반점이 아닌 것)의 분포는 연산 기호 둘레 간격이 0.40 에 몰리고(exact
#: 개체 0.400~0.425 에 821) 행렬 칸 간격이 0.85~1.20 에 몰린다. 문턱을 0.025 씩 옮기며 「원본에 쉼표가 모자란 loose 개체
#: 가운데 문턱 넘는 간격 수가 모자란 쉼표 수와 같은 것」에서 「문턱 넘는 간격이 생기는 exact 개체」를 뺀 수가 0.725 · 0.75
#: 에서 가장 크다(358 − 60 = 298) — 둘 가운데 넣는 쪽이 적은 큰 값을 쓴다.
COLUMN = 0.75
#: 글자 · 숫자 사이 간격이 이 값 ÷ H 이상이고 사이에 그린 것이 없으면 사용자가 친 빈칸으로 본다 — 미리보기는 빈칸 글자를
#: 그리지 않거나(조각 끝 빈칸, 38.106 `N_(TA offset)` 의 조각 'TA ') 앞 글자 간격만 넓힌다(38.817-02 `P_(EIRP OFF)` 의 P 뒤
#: Dx 150 · P 폭 98). 짝 하네스에서 문턱별 등급 이동(칸 쉼표만 넣은 판 대비)은 0.10 고침 31 · 깨짐 60, 0.125 31 · 24,
#: 0.15 · 0.175 31 · 4, 0.20 29 · 4 — 평평한 구간의 큰 값을 쓴다. 남는 깨짐 4 는 숫자 뒤 기울임 글자(38.211 `6 j/L`)로 뜻은 같다.
SPACE = 0.175
#: 큰 연산자의 위 · 아래 한계 자리(÷ 연산자 크기). 짝 하네스 exact 개체에서 연산자 기준선 위로 잰 위 한계의 가장 가까운
#: 기준선은 0.77~1.0(170 개), 연산자 기준선 아래로 잰 아래 한계의 윗끝은 0.07~0.10(199 개)이다. 앞 요소의 위 · 아래
#: 첨자는 이보다 연산자 기준선에 가깝다(38.211 `y_(u,v)(n)=∑…` 의 아래 첨자 u 윗끝은 연산자 기준선보다 0.43 위). 문턱별 exact 는
#: UP 0.5 · 0.6 · 0.7 · 0.8 에서 28447 · 28448 · 28448 · 28435, LOW −0.2 · 0 · 0.05 에서 28417 · 28448 · 28448 — 평평한 구간에서
#: 첨자 쪽으로 가장 먼 값을 쓴다.
UP = 0.6
LOW = 0
#: 큰 연산자 글자의 아래끝(÷ 크기). 아래 한계 윗끝이 연산자 기준선보다 0.07~0.10 아래라(위 수) 아래끝을 기준선에 두면 분수
#: 막대 위 · 아래 덩어리를 이을 때 연산자와 아래 한계가 끊긴다 — 연산자가 분자에서 빠진다(38.101-1 `EVM=√((∑_(v∈T_m) …)/…)`).
#: Symbol ∑ 의 실제 아래끝은 0.0996(symbol.ttf 0xF0E5 의 yMin −204 / 2048). 0.10 · 0.125 · 0.15 · 0.2 의 exact 는 모두 28479,
#: miss 는 224 · 222 · 222 · 222 — 아래 한계 윗끝의 가장 큰 값보다 큰 첫 값을 쓴다.
OPDESC = 0.125
_WIDTH = {k: dict(zip(cs, ws)) for k, (cs, ws) in glyph_width.WIDTH.items()}


class El:
    """요소 하나. k = g 글자 · f 괄호 · op 큰 연산자 · pr 프라임 · s 선 글자(`|` `/`) · c 묶음.
    y = 기준선(선은 아래끝, 분수는 막대 높이), lv = 크기(글꼴 높이 · 선 길이 · 묶음 안 가장 큰 크기),
    top · bot = 세로 범위, lc · rc = 왼끝 · 오른끝 갈래(w 글 · 함수 글꼴 낱말, v 그 밖의 글자 · 숫자)."""
    __slots__ = ("x", "y", "lv", "t", "k", "top", "bot", "lc", "rc", "op", "r")

    def __init__(self, x, y, lv, t, k, top, bot, lc=None, rc=None, op=False, r=None):
        self.x, self.y, self.lv, self.t, self.k = x, y, lv, t, k
        self.top, self.bot, self.lc, self.rc, self.op = top, bot, lc, rc, op
        self.r = x if r is None else r

    def __repr__(self):
        return f"El({self.x},{self.y},{self.lv},{self.t!r},{self.k})"


def _cls(ch, font):
    if not ch.isalnum():
        return None
    if ch.isdigit():
        return "v"
    upright = font is not None and not font.italic and font.tab is None and font.charset != 2
    return "w" if upright and ch.isalpha() else "v"


def _width(t, font) -> float:
    """글 t 의 폭(글꼴 크기 단위). Symbol 은 Symbol 표, 그 밖의 글꼴은 Times New Roman 표(기울임 따라)를 쓴다 — 말뭉치
    미리보기에 그린 글자 343,818 개 가운데 Times New Roman 82.8% · Symbol 16.9% 다. 표에 없는 글자는 다른 표에서 찾고,
    어느 표에도 없으면 0.5 로 둔다(times.ttf · timesi.ttf 의 cmap 글자 3,678 · 2,983 개 폭의 가운데값이 둘 다 0.5)."""
    face = font.face if font is not None else ""
    first = "Symbol|0" if face == "Symbol" else f"Times New Roman|{int(bool(font is not None and font.italic))}"
    w = 0
    for ch in t:
        v = next((_WIDTH[k][ch] for k in (first, "Times New Roman|0", "Symbol|0") if ch in _WIDTH[k]), 500)
        w += v
    return w / 1000


def _glyph(x, y, h, t, font):
    k = ("f" if t in OPENERS or t in CLOSERS else "op" if t in BIGOP else "pr" if t in PRIME
         else "g")
    return El(x, y, h, t, k, y - h, y + (OPDESC * h if k == "op" else 0), _cls(t[:1], font), _cls(t[-1:], font),
              r=x + _width(t, font) * h)


def glyphs(runs, notes):
    out = []
    for x, y, t, odd, h, dx, _raw, font, _al in runs:
        if odd:
            pos = [x + sum(dx[:i]) for i in range(len(odd))] if dx and len(dx) == len(odd) else [x] * len(odd)
            for (face, c), xi in zip(odd, pos):
                s = MTX.get(c) if face == "MT Extra" else None
                acc = ACCENT_MTX.get(c) if face == "MT Extra" else None
                if s:
                    out.append(El(xi, y, h, s, "g", y - h, y, r=xi + _width(s, None) * h))
                elif acc:
                    out.append(El(xi, y, h, acc, "acc", y - h, y))
                else:
                    notes.append(f"drop:{face}:{c:#04x}")
            continue
        if not t.strip():
            # 빈칸만 그린 조각 — Equation Editor 3 은 빈칸 글자를 따로 그린다(38.101-4 R_high 행렬의 칸 사이)
            out.append(El(x, y, h, " ", "sp", y - h, y))
            continue
        if dx and len(dx) == len(t):
            ink = [i for i, ch in enumerate(t) if not ch.isspace()]
            for i, ch in enumerate(t):
                if not ch.isspace():
                    out.append(_glyph(x + sum(dx[:i]), y, h, ch, font))
                elif ink[0] < i < ink[-1] and not t[i - 1].isspace():
                    # 글자 사이에 그린 빈칸 — 해독 글의 빈칸 글자와 같은 자리(38.101-4 R_high 행렬의 칸 사이)
                    out.append(El(x + sum(dx[:i]), y, h, " ", "sp", y - h, y))
        else:
            if dx:
                notes.append("dxlen")
            out.append(_glyph(x, y, h, " ".join(t.split()), font))
    return _accents(_merge_pieces(out), notes)


def _accents(els, notes):
    """꾸밈표 글자를 그 아래 글자에 결합 꾸밈표로 붙인다. 아래 글자 = x 가 꾸밈표 기준점 이하인 글자 가운데 가장 오른쪽 것
    (꾸밈표는 글자 위 가운데 그려 기준점이 글자 기준점보다 오른쪽이다 — 38.133 `Ê` 의 E 58 · ˆ 112). 기울인 글자는 위쪽이
    오른쪽으로 쏠려 왼쪽 점이 기준점보다 조금 앞설 수 있어(38.901 `ẍ` 의 x 76 · 점 68 · 152) `NARROW` 만큼 왼쪽까지 본다.
    Times New Roman `ˆ` · `~` 는 그 글자보다 기준선이 높을 때만 꾸밈표다(같은 줄이면 보통 글자로 둔다). 아래 글자는 꾸밈표와
    세로 범위가 겹쳐야 한다 — 행렬은 칸마다 같은 x 에 여러 줄을 그려 다른 줄의 아래첨자가 꾸밈표 바로 왼쪽에 올 수 있다
    (38.214 `W^(3)` 의 첫 줄 ṽ 꾸밈표 x 3206 · v 3168 · 둘째 줄 아래첨자 p 3193)."""
    base_of = {}
    rest = []
    for e in els:
        mtx = e.k == "acc"
        if not mtx and not (e.k == "g" and e.t in ACCENT_GLYPH):
            rest.append(e)
            continue
        under = [b for b in els if b.k == "g" and b.t not in ACCENT_GLYPH and b.x - NARROW * b.lv < e.x
                 and (mtx or b.y > e.y) and _overlap(_span(b), _span(e))]
        if not under:
            if mtx:
                notes.append("acc:alone")
            else:
                rest.append(e)
            continue
        b = max(under, key=lambda u: u.x)
        base_of.setdefault(id(b), (b, []))[1].append(e.t if mtx else ACCENT_GLYPH[e.t])
    for b, marks in base_of.values():
        if len(b.t) > 1:
            notes.append("acc:multi")
        dots = marks.count(chr(0x307))
        marks = [m for m in marks if m != chr(0x307)] + ([DOTS.get(dots, chr(0x307) * dots)] if dots else [])
        b.t += "".join(marks)
    return rest


def _merge_pieces(els):
    cols: dict = {}
    rest = []
    for e in els:
        if e.t in PIECES:
            cols.setdefault(e.x, []).append(e)
        else:
            rest.append(e)
    for x, ps in cols.items():
        fam = next((PIECES[p.t] for p in ps if PIECES[p.t]), "")
        if not fam:
            continue
        top, bot = min(p.top for p in ps), max(p.bot for p in ps)
        k = "op" if fam == "∫" else "f"
        if fam in "[]":
            kinds = {p.t for p in ps}
            if not kinds & set("⎣⎦"):
                fam = CEIL[fam]
            elif not kinds & set("⎡⎤"):
                fam = FLOOR[fam]
        rest.append(El(x, bot, bot - top, fam, k, top, bot, r=max(p.r for p in ps)))
    return rest


def _span(e):
    return e.top, e.bot


def _overlap(a, b):
    return a[0] < b[1] and b[0] < a[1]


def _within(e, x0, x1):
    """요소가 가로 범위 [x0, x1] 의 선(막대 · 근호 윗줄)과 겹치는가. 글자 기준점은 글자 왼쪽 여백 때문에 선 왼끝보다
    조금 앞설 수 있다(38.901 `1/(1−p_0)` 의 분모 `1` 은 기준점 2125, 막대 왼끝 2136) — 왼쪽으로 가장 좁은 글자 폭
    (`NARROW`)보다 덜 앞서면 선과 겹친다. 선 요소(`|` `/`)는 여백이 없고 크기가 선 길이라 이 여유를 주지 않는다 — 주면
    38.212 `|Q̅_I^N|` 의 절댓값 세로선(x 72, 길이 558)이 윗줄(왼끝 113) 안으로 들어간다. 오른쪽은 요소 가운데가 선 안에
    있어야 한다 — 윗줄은 밑글자 오른끝을 조금 넘어 그려져(38.106 `q̅_0` 의 q 오른끝 219 · 윗줄 끝 237) 바로 뒤 첨자의
    기준점(222)이 선 안에 든다. 괄호는 가운데로만 잰다 — 쌓은 괄호의 크기는 글꼴 높이가 아니라 쌓은 높이라 여유가
    지나치게 커진다(RAN1-92 회의 보고서 `⌈(…)/(∑_(r=0)^(C_(UL−SCH)−1) K_r)⌉` 의 올림 괄호는 크기 2238 · 막대 왼끝 234 앞
    170 에 있어 여유로 재면 분모에 든다)."""
    if e.k == "f":
        return x0 <= (e.x + e.r) / 2 <= x1
    return x0 - (0 if e.k == "s" else NARROW * e.lv) < e.x and (e.x + e.r) / 2 <= x1


def _component(cands, edge, downward):
    """막대(높이 edge)에 맞닿은 세로 연결 덩어리 — 막대 쪽부터 세로 범위가 이어지는 요소만."""
    cands = sorted(cands, key=(lambda e: e.top) if downward else (lambda e: -e.bot))
    out, reach = [], None
    for e in cands:
        if reach is None:
            out.append(e)
            reach = e.bot if downward else e.top
        elif (e.top < reach) if downward else (e.bot > reach):
            out.append(e)
            reach = max(reach, e.bot) if downward else min(reach, e.top)
        else:
            break
    return out


def _compound(x, y, lv, t, members, extra=(), op=False, edge=None):
    """묶음 요소. 오른끝은 내용의 오른끝과 선 오른끝(edge) 가운데 큰 것."""
    tops = [m.top for m in members] + [v for v in extra]
    bots = [m.bot for m in members] + [v for v in extra]
    left = members and min(members, key=lambda m: m.x)
    right = members and max(members, key=lambda m: m.x)
    r = max([m.r for m in members] + ([edge] if edge is not None else []), default=x)
    return El(x, y, lv, t, "c", min(tops), max(bots),
              left.lc if left else None, right.rc if right else None, op, r)


def _level(members):
    lv = [m.lv for m in members if m.k in ("g", "c")]
    return max(lv) if lv else max((m.lv for m in members), default=0)


def structures(els, strokes, notes):
    """선을 요소로 바꾸고 수평선 구조를 접는다."""
    hs, used = [], set()
    for i, s in enumerate(strokes):
        if len(s) == 2:
            (x0, y0), (x1, y1) = s
            if y0 == y1 and x0 != x1:
                hs.append(i)
    for i in hs:
        # 근호: 윗줄 바로 앞 획이 윗줄 왼끝에서 끝나는 사선, 그 앞 둘이 사선(꺾임 · 내림)
        (a, b) = sorted(strokes[i])
        if i >= 1 and len(strokes[i - 1]) == 2 and strokes[i - 1][1] == a and strokes[i - 1][0][1] != a[1]:
            chain = [i - 1]
            for j in (i - 2, i - 3):
                if j >= 0 and len(strokes[j]) == 2 and strokes[j][0][0] != strokes[j][1][0] \
                        and strokes[j][0][1] != strokes[j][1][1]:
                    chain.append(j)
            used.update(chain)
    # DSMT4 는 근호를 선 넷 뒤에 같은 모양의 채운 다각형으로 한 번 더 그린다 — 선으로 이미 읽은 근호면 버린다
    for i, s in enumerate(strokes):
        if i in used or len(s) == 2:
            continue
        xs, ys = [p[0] for p in s], [p[1] for p in s]
        if min(ys) == max(ys) or min(xs) == max(xs):
            continue
        notes.append(f"poly{len(s)}")
        used.add(i)
    vert = {}
    for i, s in enumerate(strokes):
        if i in used or i in hs:
            continue
        xs, ys = [p[0] for p in s], [p[1] for p in s]
        if min(xs) == max(xs) and min(ys) != max(ys):
            vert.setdefault((min(ys), max(ys)), []).append(min(xs))
        elif min(ys) == max(ys):
            hs.append(i)
        else:
            els.append(El(min(xs), max(ys), max(ys) - min(ys), "/", "s", min(ys), max(ys), r=max(xs)))
    # 세로선 둘이 같은 세로 범위로 사이에 아무 글자 없이 붙으면 두 줄 세로 막대 `‖` 하나다(R1-166734 의 노름
    # `‖∑_(l=0)^(L−1) c_(l,k)b_l‖` 은 높이 1002 인 선 둘을 54 떨어뜨려 그린다). 짝 하네스 29,170 개에서 이 꼴은 이 두 식의
    # 네 쌍뿐이고, 원본 `‖` 가 든 식도 이 둘뿐이다.
    for (y0, y1), xs in vert.items():
        xs.sort()
        k = 0
        while k < len(xs):
            if k + 1 < len(xs) and not any(xs[k] < e.x < xs[k + 1] for e in els):
                els.append(El(xs[k], y1, y1 - y0, "‖", "s", y0, y1, r=xs[k + 1]))
                k += 2
                continue
            els.append(El(xs[k], y1, y1 - y0, "|", "s", y0, y1))
            k += 1
    for i in sorted(set(hs), key=lambda i: abs(strokes[i][0][0] - strokes[i][-1][0])):
        xs = [p[0] for p in strokes[i]]
        x0, x1, y = min(xs), max(xs), strokes[i][0][1]
        prev = strokes[i - 1] if i >= 1 else None
        if prev is not None and len(prev) == 2 and prev[1] == (x0, y) and prev[0][1] != y and i - 1 in used:
            lo = max(prev[0][1], prev[1][1])
            left = min(p[0] for j in range(max(0, i - 3), i) if j in used for p in strokes[j])
            inside = [e for e in els if _within(e, x0, x1) and _overlap(_span(e), (y, lo))]
            if not inside:
                notes.append("root:empty")
                continue
            for e in inside:
                els.remove(e)
            els.append(_compound(left, y + (lo - y), _level(inside), _open("√" + _grp(read_line(inside))),
                                 inside, (y, lo), edge=x1))
            continue
        # 위 · 아래는 기준선으로 가른다 — 글꼴 높이로 잡은 윗끝은 글자 위 여백까지 들어 막대를 넘는다
        # (38.901 의 윗줄 θ̅ 는 막대 y=97, 글꼴 높이 384 로 잡은 윗끝이 음수)
        above = [e for e in els if _within(e, x0, x1) and e.y < y and e.k != "sp"]
        below = [e for e in els if _within(e, x0, x1) and e.y > y and e.k != "sp"]
        num = _component(above, y, False)
        den = _component(below, y, True)
        if num and den:
            for e in num + den:
                els.remove(e)
            t = _open(f"{_grp(read_line(num))}/{_grp(read_line(den))}")
            els.append(_compound(x0, y, _level(num + den), t, num + den, (y,), edge=x1))
            continue
        if not den and not num:
            near = [e for e in els if e.x < x0 and e.y > y]
            if near:
                e = max(near, key=lambda e: e.x)
                den = _component([d for d in near if d.x == e.x], y, True)
        if den:
            for e in den:
                els.remove(e)
            g = read_line(den)
            els.append(_compound(min(e.x for e in den), max(e.y for e in den), _level(den), _grp(g) + "̅",
                                 den, edge=x1))
        elif num:
            for e in num:
                els.remove(e)
            g = read_line(num)
            els.append(_compound(min(e.x for e in num), max(e.y for e in num), _level(num), _grp(g) + "̲",
                                 num, edge=x1))
        else:
            notes.append("bar:alone")
    return els


def _fences(els):
    """짝 맞는 괄호의 안을 묶음 하나로. 짝 없는 큰 여는 괄호(쌓은 조각)는 오른쪽 전부를 안으로 둔다. 큰 괄호 = 어느
    글자보다도 키가 큰 괄호 — 괄호 위끝으로 재면 안 된다: 식 배열의 다른 줄 글자가 더 위에 있고(38.211 `k_ref^RB={…`
    는 둘째 줄), 조건 글이 괄호 위끝보다 조금 높이 그려지기도 한다(38.521-2 `n={30, for 60 kHz SCS` 의 글 위끝 6 · 괄호 34)."""
    work = sorted(els, key=lambda e: e.x)
    stack = []
    i = 0
    while i < len(work):
        e = work[i]
        if e.k == "f" and e.t in OPENERS:
            stack.append(e)
        elif e.k == "f" and e.t in CLOSERS:
            j = next((j for j in range(len(stack) - 1, -1, -1)
                      if OPENERS[stack[j].t] == e.t and _overlap(_span(stack[j]), _span(e))), None)
            if j is not None:
                o = stack[j]
                del stack[j:]
                box = (min(o.top, e.top), max(o.bot, e.bot))
                inner = [m for m in work if o.x < m.x < e.x and m is not o and _overlap(_span(m), box)
                         and (m.k != "op" or box[0] <= (m.top + m.bot) / 2 <= box[1])]
                for m in inner + [o, e]:
                    work.remove(m)
                g = _compound(o.x, o.y, _level(inner) if inner else max(o.lv, e.lv), o.t + read_line(inner, True) + e.t,
                              [o, e] + inner)
                g.lc, g.rc = None, None
                work.append(g)
                work.sort(key=lambda m: m.x)
                i = work.index(g)
        i += 1
    for o in reversed(stack):
        if o.lv > max((m.lv for m in work if m.k == "g"), default=o.lv):
            inner = [m for m in work if m.x > o.x and _overlap(_span(m), _span(o))]
            if inner:
                for m in inner + [o]:
                    work.remove(m)
                g = _compound(o.x, o.y, _level(inner), o.t + read_line(inner, True), [o] + inner)
                g.lc = None
                work.append(g)
                work.sort(key=lambda m: m.x)
    return work


def read_line(els, grid=False) -> str:
    if not els:
        return ""
    work = _fences(els)
    lv = [e.lv for e in work if e.k in ("g", "c")]
    H = max(lv) if lv else max(e.lv for e in work)
    base = sorted(e.y for e in work if e.k == "g" and e.lv >= H)
    rows = []
    for y in base:
        if rows and y - rows[-1][-1] < H:
            rows[-1].append(y)
        else:
            rows.append([y])
    if len(rows) <= 1:
        # 큰 글자가 묶음뿐이면 기준선은 큰 요소에서 잰다 — 첨자까지 넣어 재면 첨자 기준선이 잡혀 첨자가 주 요소가 된다
        # (38.101-1 `EVM̅_DMRS` 의 윗줄 묶음 y 448 · 첨자 DMRS y 472). 큰 연산자는 수식 축에 맞춰 기준선보다 아래로 그리므로
        # 다른 큰 요소가 있으면 빼고 잰다(같은 문서 `√(1/6∑_(j=1)^6 EVM̅_(DMRS,j)^2)` 의 ∑ 는 y 825, 윗줄 묶음 EVM̅ 은 736 이라
        # ∑ 로 재면 아래첨자 DMRS 760 이 위첨자가 된다).
        big = [e.y for e in work if e.lv >= H and e.k != "op"] or [e.y for e in work if e.lv >= H]
        b = max(set(base), key=base.count) if base else max(big)
        return _row(work, b, H, grid).strip()
    bs = [max(set(r), key=r.count) for r in rows]
    parts = [[] for _ in bs]
    for e in work:
        parts[min(range(len(bs)), key=lambda k: abs(e.y - bs[k]))].append(e)
    return _seq([r for r in (_row(p, bs[k], H, True).strip() for k, p in enumerate(parts)) if r], "; ")


def _key(e):
    return e.x if e.k == "s" else e.x + NARROW * e.lv


def _side(e, o):
    """e 가 큰 연산자 o 의 위 한계 자리면 1, 아래 한계 자리면 -1, 둘 다 아니면 0."""
    if e is o or e.k == "op" or e.lv >= o.lv:
        return 0
    return 1 if o.y - e.y >= UP * o.lv else -1 if e.y - e.lv >= o.y + LOW * o.lv else 0


def _limits(els):
    """큰 연산자의 위 · 아래 한계 글자 → {id(연산자): [요소]}. 한계 자리 글자는 연산자 둘레의 다른 글자(앞 · 뒤 요소와 그
    첨자) 사이에 있어야 하고, 한 줄에 큰 연산자가 여럿이면 같은 쪽 한계 글자를 x 차례로 이어진 토막으로 나눠 연산자마다
    한 토막씩 준다 — 토막 가운데와 연산자 가운데의 거리 합이 가장 작은 나눔이다. 넓은 한계는 이웃 연산자 위까지
    뻗는다(38.101-1 `∑_(t∈T_s) ∑_(f_l)^(f_l+(12⋅N_RB−1)Δf)` 의 위 한계 앞부분 `f_l+` 은 앞 ∑ 위에 있다)."""
    ops = sorted((o for o in els if o.k == "op"), key=lambda o: o.x)
    if not ops:
        return {}
    band = {id(e) for e in els for o in ops if _side(e, o)}
    ok = {}
    for o in ops:
        rest = [e for e in els if e is not o and id(e) not in band]
        left = max((e.r for e in rest if (e.x + e.r) / 2 < o.x), default=float("-inf"))
        # 오른쪽 경계는 연산자 다음 요소의 가운데다. 한계 글자는 다음 요소 머리 위로 넘어가 그려지기도 하므로(38.213 CR0070
        # `∑_(m=0)^(C(D_i)−1) δ_(PUSCH,b,f,c)(m,l)` 의 위 한계 끝 `1` 은 x 4145 로 δ 의 x 4095 보다 오른쪽) 글자 왼끝이 그
        # 가운데보다 앞이면 한계로 받는다. 다음 요소의 오른끝까지 받으면 괄호 묶음 뒤 위첨자가 한계로 빨려 든다(38.521-1
        # `√(1/m∑_(i=1)^m (EVM_(PRACH,i))^2)` 의 `2` 는 닫는 괄호 x 5160 뒤 x 5295). 짝 하네스 29,170 개에서 가운데 경계는
        # 예전 경계(글자 가운데 ≤ 다음 요소 왼끝) 대비 miss→exact 14 · miss→order 3 이고 나빠진 식은 없다.
        nxt = min((e for e in rest if (e.x + e.r) / 2 > o.r), key=lambda e: e.x, default=None)
        right = (nxt.x + nxt.r) / 2 if nxt is not None else float("inf")
        ok[id(o)] = {id(e): _side(e, o) for e in els if _side(e, o) and left <= (e.x + e.r) / 2 and e.x < right}
    out = {}
    for side in (1, -1):
        cand = sorted((e for e in els if any(ok[id(o)].get(id(e)) == side for o in ops)), key=lambda e: e.x)
        if not cand:
            continue

        def cost(o, seg):
            if not seg:
                return 0
            if any(ok[id(o)].get(id(e)) != side for e in seg):
                return float("inf")
            return abs((min(e.x for e in seg) + max(e.r for e in seg)) / 2 - (o.x + o.r) / 2) / o.lv

        # best[k][i] = 앞 연산자 k 개에 앞 글자 i 개를 나눠 준 가장 작은 비용
        n, best = len(cand), {(0, 0): (0, None)}
        for k, o in enumerate(ops):
            for i in range(n + 1):
                opts = [(best[(k, j)][0] + cost(o, cand[j:i]), j) for j in range(i + 1) if (k, j) in best]
                if opts:
                    best[(k + 1, i)] = min(opts)
        if best[(len(ops), n)][0] == float("inf"):
            continue
        i = n
        for k in range(len(ops), 0, -1):
            j = best[(k, i)][1]
            if j < i:
                out.setdefault(id(ops[k - 1]), []).extend(cand[j:i])
            i = j
    return out


def _row(els, b, H, grid=False) -> str:
    els = sorted(els, key=_key)
    mains, scripts, primes = [], {}, {}
    pre = []
    lims = _limits(els)
    held = {id(e) for v in lims.values() for e in v}
    for e in els:
        if id(e) in held:
            continue
        if id(e) in lims:
            mains.append(e)
            scripts[id(e)] = list(lims[id(e)])
            continue
        last = next((m for m in reversed(mains) if m.k != "sp"), None)
        if e.k == "pr":
            host = next((m for m in reversed(mains) if m.k != "sp" and m.lv >= e.lv), last)
            if host is not None:
                primes.setdefault(id(host), []).append(e)
                continue
        if e.lv >= H or e.k == "op" or (e.y == b and e.k != "c"):
            mains.append(e)
        elif last is not None:
            scripts.setdefault(id(last), []).append(e)
        else:
            pre.append(e)
    # 행렬 · 식 배열의 칸 사이: 미리보기에는 칸을 가르는 글자가 없고 간격만 있다(38.214 `i_(1,4)={i_(1,4,1), N_g=2; …` 의
    # 조건 칸 N 은 앞 칸 오른끝에서 글꼴 높이의 4.1 배 뒤). 사이에 빈칸 글자를 그린 것은 글에 빈칸이 이미 있다.
    cols, spaces = set(), set()
    ink = [i for i, m in enumerate(mains) if m.k != "sp"]
    for i, j in zip(ink, ink[1:]):
        a, c = mains[i], mains[j]
        edge = max([a.r] + [e.r for e in scripts.get(id(a), []) + primes.get(id(a), [])])
        # 큰 연산자는 한계 글자가 연산자보다 넓으면 그 왼끝에서 잰다(38.212 `⌈α⋅∑_(l=l_0)^(N_(symb,all)^PUSCH−1)` 의 ∑ 는
        # 아래 한계가 넓어 오른쪽으로 밀려 있다).
        gap = (min([c.x] + [e.x for e in lims.get(id(c), [])]) - edge) / H
        if grid and gap >= COLUMN and j == i + 1 and a.t[-1:] not in ",;" and c.t[:1] not in ",;":
            cols.add(j)
        elif gap >= SPACE and j == i + 1 and a.t[-1:].isalnum() and c.t[:1].isalnum():
            spaces.add(j)
    items = []
    lead = _head(pre, b)
    for j, m in enumerate(mains):
        if j in cols:
            items.append([", ", None, None, "|"])
        elif j in spaces:
            items.append([" ", None, None, ""])
        t = m.t + "".join(p.t for p in primes.get(id(m), []))
        # 첨자의 위 · 아래는 밑글자의 기준선으로 가른다 — 한 줄에 기준선이 다른 칸이 섞일 수 있다(38.901 τ_n 의 식 칸
        # τ 392 · 조건 칸 `,for NLOS` 614 를 따로 가운데 맞춘 세로 묶음 둘이라, 줄 기준선 614 로 재면 τ 의 아래첨자 n 488 이 위로 간다).
        head = _head(scripts.get(id(m), []), m.y if m.k in ("g", "op") else b)
        if head:
            item = [_open((t if m.k == "op" else _base(t)) + head), m.lc, None]
        else:
            item = [t, m.lc, m.rc]
        if lead:
            item[0] = f"{lead} {item[0]}"
            item[1] = None
            lead = ""
        if m.k == "op":
            item[0] += " "
            item[2] = None
        item.append("" if head or m.k == "c" else "/" if m.k == "s" and m.t == "/" else "|" if m.k == "op"
                    else "g" if m.k in ("g", "f") else "")
        items.append(item)
    if lead:
        items.append([lead, None, None, ""])
    return _join(_slashes(items))


def _slashes(items):
    """사선 획(`/` 하나로 그린 분수 — MTEF 틀 41)의 앞 · 뒤 피연산자를 분수의 분자 · 분모로 묶는다. 피연산자는 사선에서
    연산 기호 · 구분 기호 · 괄호(`BOUND`) · 다른 사선 · 줄 끝까지 이어진 항목이다 — UnicodeMath 의 `/` 피연산자와 같은
    범위다(38.211 `κ=T_s/T_c=64` 는 `κ=(T_s)/(T_c)=64`). 원본 해독이 분자 · 분모를 `_grp` 로 감싸는 것과 같은 글이 된다.
    한 글 조각에 끊는 기호와 글자가 함께 들면(38.211 `j=0,1,...,N/L−1` 의 `0,1,...,N`) 그 기호에서 조각을 가른다.
    피연산자 한쪽이 비면 사선을 그대로 둔다."""
    out = []
    i = 0
    while i < len(items):
        if items[i][3] != "/":
            out.append(items[i])
            i += 1
            continue
        left = []
        while out and out[-1][3] in ("", "g"):
            t = out[-1][0]
            p = max((q for q, c in enumerate(t) if c in BOUND), default=-1) if out[-1][3] == "g" else -1
            if p < 0:
                left.insert(0, out.pop())
                continue
            if t[p + 1:]:
                out[-1] = [t[:p + 1], out[-1][1], None, "|"]
                left.insert(0, [t[p + 1:], None, None, "g"])
            break
        right, j = [], i + 1
        while j < len(items) and items[j][3] in ("", "g"):
            t = items[j][0]
            p = min((q for q, c in enumerate(t) if c in BOUND), default=-1) if items[j][3] == "g" else -1
            if p < 0:
                right.append(items[j])
                j += 1
                continue
            if p:
                right.append([t[:p], None, None, "g"])
                items = items[:j] + [[t[p:], None, items[j][2], "|"]] + items[j + 1:]
            break
        num, den = _join(left), _join(right)
        if not num or not den:
            out += left + [items[i]] + right
            i = j
            continue
        out.append([_open(f"{_grp(num)}/{_grp(den)}"), None, None, ""])
        i = j
    return out


def _join(items) -> str:
    out, prev = [], None
    for t, lc, rc, _kind in items:
        if not t:
            continue
        if prev is not None and prev[2] and lc and prev[2] != lc and prev[0][-1:].isalnum() and t[:1].isalnum():
            out.append(_OPEN)
        out.append(t)
        prev = (t, lc, rc)
    return "".join(out)


def _head(scr, b) -> str:
    if not scr:
        return ""
    sub = [e for e in scr if e.y > b]
    sup = [e for e in scr if e.y <= b]
    s, p = read_line(sub), read_line(sup)
    return (f"_{_grp(s)}" if s else "") + (f"^{_grp(p)}" if p else "")


def figure(runs) -> bool:
    """기울인 글꼴로 그린 글 조각이 있는가 — 수식이 아니라 그림이다(모듈 설명)."""
    return any(r[7] is not None and r[7].esc for r in runs)


def read(blob: bytes, notes=None) -> str | None:
    """미리보기 그림 하나의 선형 수식 글. WMF · EMF 가 아니거나 그림(`figure`)이면 None — 그림이면 notes 에 "figure"."""
    notes = notes if notes is not None else []
    got = metafile_text._read(blob)
    if got is None:
        return None
    _texts, _odd, runs, strokes = got
    if figure(runs):
        notes.append("figure")
        return None
    els = glyphs(runs, notes)
    els = structures(els, strokes, notes)
    text = read_line(els)
    text = docx_text._OPEN_GAP.sub(" ", text).replace(_OPEN, "").translate(docx_text._INVISIBLE)
    return unicodedata.normalize("NFC", mtef_linear._SPACES.sub(" ", text).strip())
