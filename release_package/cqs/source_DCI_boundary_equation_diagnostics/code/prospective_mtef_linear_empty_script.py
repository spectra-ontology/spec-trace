"""MTEF 나무(`mtef.Eqn.body`)를 선형 표기 글로 — `docx_text.math_linear` 와 같은 적기.

첨자 틀은 줄에서 바로 앞 항목을 밑글로 삼고(MTEF 에는 밑글 칸이 없다), 앞첨자 틀은 바로 뒤 항목 앞에 붙는다.
큰 연산자 · 극한 틀의 아래 · 위 칸은 빈 자리 줄인지로 가른다 — 판 5 의 변형 비트는 명세와 다르게 쓰인다(38.211 의
합 기호 틀 변형 0x30).

틀의 칸은 줄만이 아니다 — Equation Editor 3 은 괄호 틀 칸에 세로 묶음(pile)을 줄로 싸지 않고 바로 넣는다(38.901 의
`ρ̂ = (x; y; z)`). 그래서 글자 개체가 아닌 아랫 마디를 모두 칸으로 센다.
"""
import re

import docx_text

_grp, _base, _open, _OPEN, _seq = docx_text._grp, docx_text._base, docx_text._open, docx_text._OPEN, docx_text._seq

#: 판 3 · 판 5 공통 꾸밈 번호 → (앞에 붙일 글, 뒤에 붙일 글)
EMBELL = {
    2: ("", "̇"), 3: ("", "̈"), 4: ("", "⃛"),
    5: ("", "′"), 6: ("", "″"), 7: ("‵", ""), 18: ("", "‴"),
    8: ("", "̃"), 9: ("", "̂"), 10: ("", "̸"),
    11: ("", "⃗"), 12: ("", "⃖"), 13: ("", "⃡"), 14: ("", "⃑"), 15: ("", "⃐"),
    16: ("", "̵"), 17: ("", "̅"), 19: ("", "̑"), 20: ("", "̆"),
}

#: Symbol 글꼴의 괄호 조각(Adobe Symbol PUA) → 괄호. 바닥 · 천장 괄호는 아래 · 위 조각으로 그린다.
PIECE = {0xF8F0: "⌊", 0xF8FB: "⌋", 0xF8EE: "⌈", 0xF8F9: "⌉"}
PIECE.update({c: "(" for c in (0xF8EB, 0xF8EC, 0xF8ED)})
PIECE.update({c: ")" for c in (0xF8F6, 0xF8F7, 0xF8F8)})
PIECE.update({0xF8EF: "[", 0xF8FA: "]"})
PIECE.update({c: "{" for c in (0xF8F1, 0xF8F2, 0xF8F3, 0xF8F4)})
PIECE.update({c: "}" for c in (0xF8FC, 0xF8FD, 0xF8FE)})

SPACE_FACE = 24
WORD_FACES = (1, 2)  # 글 · 함수 글꼴 — 낱말로 적힌다

#: 괄호 틀의 기본 괄호 — 괄호 글자 개체가 없을 때만 쓴다
FENCE3 = {0: "⟨⟩", 1: "()", 2: "{}", 3: "[]", 4: "||", 5: "‖‖", 6: "⌊⌋",
          7: "⌈⌉", 8: "{{", 9: "}}", 10: "}{", 11: "{)", 12: "(}"}
FENCE5 = {0: "⟨⟩", 1: "()", 2: "{}", 3: "[]", 4: "||", 5: "‖‖", 6: "⌊⌋",
          7: "⌈⌉", 8: "⟦⟧"}
BIGOP3 = {21: "∫", 22: "∬", 23: "∭", 24: "∫", 25: "∬", 26: "∭", 29: "∑",
          30: "∑", 31: "∏", 32: "∏", 33: "∐", 34: "∐", 35: "⋃", 36: "⋃",
          37: "⋂", 38: "⋂", 42: "∫", 43: "∑"}
BIGOP5 = {15: "∫", 16: "∑", 17: "∏", 18: "∐", 19: "⋃", 20: "⋂", 21: "∫",
          22: "∑"}


def char_text(code, face) -> str:
    if code is None:
        return ""
    if face == SPACE_FACE:
        return " "
    return PIECE.get(code) or chr(code)


class Render:
    def __init__(self, eqn, notes=None):
        self.v = eqn.version
        self.unknown: list[str] = []
        self.notes = notes if notes is not None else []

    # 줄 하나 — 항목(글, 왼끝 갈래, 오른끝 갈래)을 모아 잇는다. 갈래 'w' = 글 · 함수 글꼴 글자, 'v' = 그 밖의 글자.
    # 서로 다른 갈래의 글자 · 숫자가 맞닿으면 한 칸 띄운다(`n mod 2`).
    def line(self, nodes) -> str:
        items: list[list] = []
        pre = None  # 앞첨자 — 다음 항목 앞에 붙는다
        for n in nodes or []:
            k = n[0]
            scr = self.script(n) if k == "tmpl" else None
            if scr is not None:
                sub, sup, lead = scr
                # Prospective diagnostic only: an empty script contributes no
                # drawn content; do not regroup a preceding space as `( )`.
                if not sub and not sup:
                    continue
                head = (f"_{_grp(sub)}" if sub else "") + (f"^{_grp(sup)}" if sup else "")
                if lead:
                    pre = head
                    continue
                if items and items[-1][3] is not None and _joins(items[-1][3][1], sub) and _joins(items[-1][3][2], sup):
                    base, sub0, sup0 = items[-1][3]
                    sub, sup = sub0 + sub, sup0 + sup
                    head = (f"_{_grp(sub)}" if sub else "") + (f"^{_grp(sup)}" if sup else "")
                    items[-1][0], items[-1][3] = _open(_base(base) + head), (base, sub, sup)
                    continue
                if items:
                    base, lc, _rc, _s = items.pop()
                    base = base.removesuffix(_OPEN)
                elif not (sub and sup):
                    # 줄 첫머리의 첨자 틀은 밑글이 없어 한 칸만 차 있으면 그 칸 글만 한 단 낮춰 · 높여 그린 것이다.
                    # 수식 개체가 든 683 문서에서 MTEF 가 풀린 개체 29,241 개에 179 건이고 모두 아래첨자 칸만 찼다
                    # (38.214 `2^(μ_PDSCH)` 의 위첨자 칸 첫머리
                    # 아래첨자 틀이 μ_PDSCH 전체를 담는다). 빈 밑글에 첨자 표지를 달면 `2^(_(μ_PDSCH))` 처럼 밑글 없는
                    # 첨자로 읽히므로 칸 글만 적는다.
                    items.append([sub or sup, None, None, None])
                    continue
                else:
                    base, lc = "", None
                items.append([_open(_base(base) + head), lc, None, (base, sub, sup)])
                continue
            if k == "char":
                face, code, emb = n[1], n[2], n[3]
                t = char_text(code, face)
                for e in emb:
                    before, after = EMBELL.get(e, ("", ""))
                    t = before + t + after
                cls = ("w" if face in WORD_FACES else "v") if t[:1].isalnum() or t[-1:].isalnum() else None
                item = [t, cls, cls, None]
            else:
                item = [self.node(n), None, None, None]
            if pre is not None:
                item[0] = f"{pre} {item[0]}" if item[0] else pre
                item[1] = None
                pre = None
            items.append(item)
        if pre is not None:
            items.append([pre, None, None, None])
        out = []
        prev = None
        for t, lc, rc, _s in items:
            if not t:
                continue
            if prev is not None and prev[2] and lc and prev[2] != lc and prev[0][-1:].isalnum() and t[:1].isalnum():
                out.append(_OPEN)
            out.append(t)
            prev = (t, lc, rc)
        return "".join(out)

    def node(self, n) -> str:
        k = n[0]
        if k == "line":
            return self.line(n[1])
        if k == "char":
            return self.line([n])
        if k == "pile":
            return _seq([r for r in (self.node(x) for x in n[1]) if r], "; ")
        if k == "matrix":
            rows, cols = n[1], n[2]
            rs = []
            for i in range(rows):
                row = n[3][i * cols:(i + 1) * cols]
                stacks = [_stack(x) for x in row]
                if cols > 1 and all(stacks) and len({len(st) for st in stacks}) == 1:
                    # 칸마다 세로 묶음을 둔 한 줄 행렬은 줄끼리 맞춰 읽는다(38.901 τ_n 의 식 칸 · 조건 칸)
                    rs += [_seq([self.node(x) for x in sub], ", ") for sub in zip(*stacks)]
                else:
                    rs.append(_seq([self.node(x) for x in row], ", "))
            return _seq([r for r in rs if r.strip(", ")], "; ")
        if k == "tmpl":
            return self.tmpl(n)
        return ""

    def script(self, n):
        """첨자 틀이면 (아래첨자, 위첨자, 앞첨자인가), 아니면 None."""
        sel, var, subs = n[1], n[2], n[3]
        if self.v == 3 and sel in (15, 44):
            lead = sel == 44
        elif self.v == 5 and sel in (27, 28, 29):
            lead = bool(var & 0x1)
        else:
            return None
        lines = self.slots(sel, subs)
        sub = self.node(lines[0]) if lines else ""
        sup = self.node(lines[1]) if len(lines) > 1 else ""
        return sub, sup, lead

    def slots(self, sel, subs) -> list:
        """틀의 칸 — 글자 개체(틀이 그리는 괄호 · 연산자 글자)가 아닌 아랫 마디 전부."""
        out = [s for s in subs if s[0] != "char"]
        for s in out:
            if s[0] != "line":
                self.notes.append(f"slot:{s[0]}|v{self.v}|{sel}")
        return out

    def tmpl(self, n) -> str:
        sel, var, subs = n[1], n[2], n[3]
        lines = self.slots(sel, subs)
        chars = [self.tmpl_char(sel, s) for s in subs if s[0] == "char"]
        txt = [self.node(x) for x in lines]
        main = txt[0] if txt else ""
        v3 = self.v == 3
        kind = self.kind(sel, var)
        if kind == "fence":
            return self.fence(sel, var, main, chars)
        if kind == "root":
            idx = txt[1] if len(txt) > 1 else ""
            return f"√({idx}&{main})" if idx else _open("√" + _grp(main))
        if kind == "frac":
            den = txt[1] if len(txt) > 1 else ""
            return _open(f"{_grp(main)}/{_grp(den)}")
        if kind == "bigop":
            lo = txt[1] if len(txt) > 1 else ""
            hi = txt[2] if len(txt) > 2 else ""
            # 연산자 글자가 글자 개체가 아니라 넷째 칸 줄로 오기도 한다 — 38.214 의 판 5 틀 21 은 빈 본 칸 ·
            # 아래 칸 p · 빈 위 칸 · 넷째 칸 θ 로 `θ_p` 를 적고, 미리보기도 θ 와 p 만 그린다.
            if chars and chars[-1]:
                op = chars[-1]
            elif len(txt) > 3 and txt[3]:
                op = txt[3]
            else:
                op = (BIGOP3 if v3 else BIGOP5).get(sel, "∫")
            head = op + (f"_{_grp(lo)}" if lo else "") + (f"^{_grp(hi)}" if hi else "")
            return f"{head} {main}" if main else _open(head)
        if kind == "lim":
            lo = txt[1] if len(txt) > 1 else ""
            hi = txt[2] if len(txt) > 2 else ""
            if not lo and not hi:
                return main
            return _open(_base(main) + (f"_{_grp(lo)}" if lo else "") + (f"^{_grp(hi)}" if hi else ""))
        if kind == "bar":
            under = (sel == 16) if v3 else (sel == 12)
            mark = "̲" if under else "̅"
            return _grp(main) + mark * (2 if var & 0x1 else 1)
        if kind == "hbrace":
            top = (sel == 27) if v3 else bool(var & 0x1)
            brace = (chars[-1] if chars else "") or ("⏞" if top else "⏟")
            small = txt[1] if len(txt) > 1 else ""
            body = _grp(main) + brace
            return _open(body + ("^" if top else "_") + _grp(small)) if small else body
        if kind == "arrow":
            arrow = (chars[-1] if chars else "") or "→"
            rest = [t for t in txt if t]
            if not rest:
                return arrow
            if v3:
                mark = "_" if var & 0x1 else "^"
                return _open(arrow + mark + _grp(rest[0]))
            top = txt[0] if var & 0x4 else ""
            bot = (txt[1] if var & 0x4 else txt[0]) if var & 0x8 and txt else ""
            return _open(arrow + (f"_{_grp(bot)}" if bot else "") + (f"^{_grp(top)}" if top else ""))
        if kind == "vec":
            return _grp(main) + self.vec_mark(sel, var)
        if kind == "accent":
            return _grp(main) + {32: "̃", 33: "̂", 34: "̑", 48: "̑"}.get(sel, "")
        if kind == "dirac":
            left = txt[0] if txt else ""
            right = txt[1] if len(txt) > 1 else ""
            return "⟨" + "|".join(t for t in (left, right) if t) + "⟩"
        self.unknown.append(f"v{self.v}|{sel}|{var:#x}")
        return " ".join(t for t in txt if t)

    def tmpl_char(self, sel, s) -> str:
        """틀 글자 개체의 글. 괄호 조각 표에 없는 사용 영역(PUA) 글자는 빈 글 — 틀의 기본 괄호를 쓴다.
        Equation Editor 3 은 절댓값 틀(선택자 4)의 세로 막대를 U+EC07 · U+EC08 로 적는다(38.901 의 `|Δx|`)."""
        t = char_text(s[2], s[1])
        if len(t) == 1 and 0xE000 <= ord(t) <= 0xF8FF:
            self.notes.append(f"tmplpua|v{self.v}|{sel}|{ord(t):#x}")
            return ""
        return t

    def kind(self, sel, var) -> str:
        if self.v == 3:
            if sel <= 12:
                return "fence"
            return {13: "root", 14: "frac", 41: "frac", 16: "bar", 17: "bar", 18: "arrow", 19: "arrow",
                    20: "arrow", 27: "hbrace", 28: "hbrace", 39: "lim", 45: "dirac", 46: "vec", 47: "vec",
                    48: "accent"}.get(sel) or ("bigop" if 21 <= sel <= 38 or sel in (42, 43) else "other")
        if sel <= 9:
            return "fence"
        return {10: "root", 11: "frac", 12: "bar", 13: "bar", 14: "arrow", 23: "lim", 24: "hbrace",
                25: "hbrace", 30: "dirac", 31: "vec", 32: "accent", 33: "accent", 34: "accent"}.get(sel) or (
            "bigop" if 15 <= sel <= 22 else "other")

    def fence(self, sel, var, main, chars) -> str:
        if self.v == 3:
            pair = FENCE3.get(sel, "()")
            left_on, right_on = (True, True) if sel > 5 else (var != 2, var != 1)
        elif sel == 9:  # 짝이 맞지 않는 구간 괄호 — 변형의 아래 · 위 4비트가 왼 · 오른 괄호
            pick = "()[]"
            pair = pick[var & 0x3] + pick[(var >> 4) & 0x3]
            left_on = right_on = True
        else:
            pair = FENCE5.get(sel, "()")
            left_on, right_on = bool(var & 0x1), bool(var & 0x2)
        left = pair[0] if left_on else ""
        right = pair[1] if right_on else ""
        it = iter(chars)
        if left_on:
            left = next(it, left) or left
        if right_on:
            right = next(it, right) or right
        return left + main + right

    def vec_mark(self, sel, var) -> str:
        if self.v == 3:
            under = sel == 46
            way = {0: "l", 1: "r", 2: "b"}.get(var, "r")
            harpoon = False
        else:
            under = bool(var & 0x4)
            harpoon = bool(var & 0x8)
            way = "b" if var & 0x3 == 0x3 else ("l" if var & 0x1 else "r")
        if under:
            return {"l": "⃮", "r": "⃯", "b": "͍"}[way] if not harpoon else (
                "⃭" if way == "l" else "⃬")
        return {"l": "⃖", "r": "⃗", "b": "⃡"}[way] if not harpoon else (
            "⃐" if way == "l" else "⃑")


def _stack(n):
    """세로 묶음(pile · 한 열 행렬)이면 그 줄 목록 — 칸 하나만 든 줄은 벗긴다. 아니면 None."""
    while n and n[0] == "line" and n[1] and len([x for x in n[1] if x is not None]) == 1:
        n = next(x for x in n[1] if x is not None)
    if n and n[0] == "pile":
        return n[1]
    if n and n[0] == "matrix" and n[2] == 1:
        return n[3]
    return None


def _joins(a, b) -> bool:
    """앞 첨자 틀의 한 칸 글 a 뒤에 바로 이은 첨자 틀의 같은 칸 글 b 를 한 칸으로 합쳐 읽는가. MathType 은 첨자 틀
    뒤의 첨자 틀을 같은 높이에 이어 그린다. 수식 개체가 든 683 문서에서 MTEF 가 풀린 개체 29,241 개에 첨자 틀이 첨자 틀
    뒤에 바로 이은 자리는 608 곳이다. 겹치는 칸이 없으면 합친다(105 곳: 38.212 `Q_m` 뒤의 빈 첨자 틀, 38.101-4 `α_i` 뒤
    위첨자 틀 `^∗` → `α_i^∗`). 둘 다 차 있으면 쉼표로 이어질 때만 합친다 — 아래첨자가 겹치는 57 곳은 모두 쉼표로 이어지는
    첨자 목록이고(38.214 `p_l^(1)` 뒤 `_,` → `p_(l,)^(1)`, 38.521-2 · 38.810 `R_z` 뒤 `_(,pol)` → `R_(z,pol)`), 위첨자가 겹치는 446 곳은 모두
    켤레 `*` 다(38.101-4 `(α^(1/9))^*`). 켤레는 앞 첨자 붙은 글 전체에 걸리므로 묶어 둔다."""
    return not a or not b or a.removesuffix(_OPEN).endswith(",") or b.startswith(",")


_SPACES = re.compile(r" {2,}")


def linear(eqn, notes=None) -> tuple[str, list[str]]:
    """수식 하나의 선형 표기 글과 읽는 규칙이 없는 틀 목록. `notes` 목록을 주면 줄 아닌 칸 · 사용 영역 틀 글자를 적는다."""
    r = Render(eqn, notes)
    text = r.line(eqn.body)
    text = docx_text._OPEN_GAP.sub(" ", text).replace(_OPEN, "").translate(docx_text._INVISIBLE)
    return _SPACES.sub(" ", text).strip(), r.unknown
