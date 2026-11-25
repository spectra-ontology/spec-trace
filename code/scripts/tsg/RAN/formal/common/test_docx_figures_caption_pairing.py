#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_docx_figures_caption_pairing.py — 그림 캡션 짝 규칙(`docx_figures` 「캡션 짝」 절)의 합성 회귀 테스트.

Spec: scripts/tsg/RAN/formal/common/README.md#tdoc-figure-captions
정본: scripts/tsg/RAN/formal/common/docx_figures.py 모듈 docstring 「캡션 짝」 절

무엇을 하는가
  python-docx 로 배치 열두 개의 DOCX 를 임시 디렉토리에 만들고 `docx_figures.figures` 가 낸 캡션 번호별 그림을
  기대 표와 대조한다. 그림은 색이 다른 8x8 PNG(로고 · A · B)이고, 어느 그림이 어느 캡션에 붙었는지는 그림 부품
  바이트의 해시로 색을 읽어 판정한다 — 파일 이름이나 미디어 번호에 기대면 그것을 쓰지 않는다는 계약을 검사할 수
  없기 때문이다. 미디어 이름 교환 배치는 부품 이름 둘을 맞바꾼 사본에서도 같은 짝이 나와야 한다.

  배치(기대는 캡션 번호 → 그림, 짝 없는 그림):
    1 무로고                 그림A · 캡션1                              1→A
    2 분리 로고              로고 · 본문 · 그림A · 캡션1                 1→A, 로고 짝 없음
    3 인접(복합 그림)        그림A · 그림B · 캡션1                      1→A+B
    4 그림 · 본문 · 캡션 · 그림  그림A · 본문 · 캡션1 · 그림B            1→A, B 짝 없음
    5 그림 · 캡션 · 그림     그림A · 캡션1 · 그림B                      1→A, B 짝 없음
    6 미디어 이름 교환       로고 · 본문 · 그림A · 캡션1 · 그림B · 캡션2  1→A · 2→B, 로고 짝 없음, 이름 교환 사본도 같음
    X 캡션이 그림 위인 줄    캡션1 · 그림A · 캡션2 · 그림B               1→A · 2→B (`_first_steps` 의 예외)
    Y 캡션 글 뒤 그림 → 빈 다음 캡션
                             그림A · [캡션1 글 · 그림B] · 캡션2          1→A · 2→B (4차)
    Z 캡션 글 뒤 그림, 다음 캡션이 그림을 가짐
                             [캡션1 글 · 그림A] · 캡션2 · 그림B          1→A · 2→B (4차가 옮기지 않음)
    W 캡션 글 뒤 그림, 다음 캡션 없음
                             그림A · [캡션1 글 · 그림B]                  1→A+B (4차가 옮길 곳 없음)
    V 캡션 글 뒤 그림이 캡션의 하나뿐인 그림
                             [캡션1 글 · 그림A] · 캡션2                  1→A, 2 빈손 (4차가 옮기지 않음)
    U 캡션 글 뒤 그림, 다음 캡션 앞에 본문
                             그림A · [캡션1 글 · 그림B] · 본문 · 캡션2   1→A+B (4차가 옮기지 않음)
    ([…] 는 한 문단 — 캡션 글 다음 같은 문단에 그림 실행을 붙인다.)

사용:
    python3 -B scripts/tsg/RAN/formal/common/test_docx_figures_caption_pairing.py

exit 0 = 열두 배치가 모두 기대와 같음, exit 1 = 다른 배치가 있음(배치마다 실제 짝을 찍는다).
저장소 산출물 쓰기 0, 네트워크 0, LLM 호출 0.

## Changelog
- 1.0.0: 최초 — 배치 일곱 개(결정의 여섯 + 캡션이 그림 위인 줄).
- 1.1.0: 캡션 문단 안 캡션 글 뒤 그림 배치 셋(Y · Z · W) — 짝 4차.
- 1.2.0: 짝 4차의 옮기지 않는 조건 배치 둘(V · U).
"""
from __future__ import annotations

__version__ = "1.2.0"

import hashlib
import io
import struct
import sys
import tempfile
import zipfile
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import docx  # noqa: E402
from docx.shared import Inches  # noqa: E402

import docx_figures  # noqa: E402


def _png(rgb: tuple[int, int, int]) -> bytes:
    raw = b"".join(b"\x00" + bytes(rgb) * 8 for _ in range(8))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 8, 8, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


BLOBS = {name: _png(rgb) for name, rgb in {"logo": (255, 0, 0), "A": (0, 160, 0), "B": (0, 0, 255)}.items()}
BY_HASH = {hashlib.sha256(blob).hexdigest(): name for name, blob in BLOBS.items()}

# ('img', 그림) · ('cap', 캡션 문단) · ('text', 본문 문단) · ('cap_img', (캡션 글, 그림)) — 캡션 글 뒤 같은 문단에 그림
LAYOUTS = {
    "1_no_logo": [("img", "A"), ("cap", "Figure 1: Alpha")],
    "2_separate_logo": [("img", "logo"), ("text", "Introduction body text."), ("img", "A"),
                        ("cap", "Figure 1: Alpha")],
    "3_adjacent_composite": [("img", "A"), ("img", "B"), ("cap", "Figure 1: Alpha and beta")],
    "4_fig_text_cap_fig": [("img", "A"), ("text", "Some body text between."), ("cap", "Figure 1: Alpha"),
                           ("img", "B")],
    "5_fig_cap_fig": [("img", "A"), ("cap", "Figure 1: Alpha"), ("img", "B")],
    "6_media_name_swap": [("img", "logo"), ("text", "Introduction body text."), ("img", "A"),
                          ("cap", "Figure 1: Alpha"), ("img", "B"), ("cap", "Figure 2: Beta")],
    "X_caption_above_line": [("cap", "Figure 1: Alpha"), ("img", "A"), ("cap", "Figure 2: Beta"), ("img", "B")],
    "Y_tail_to_empty_next": [("img", "A"), ("cap_img", ("Figure 1: Alpha", "B")), ("cap", "Figure 2: Beta")],
    "Z_tail_next_has_figure": [("cap_img", ("Figure 1: Alpha", "A")), ("cap", "Figure 2: Beta"), ("img", "B")],
    "W_tail_no_next": [("img", "A"), ("cap_img", ("Figure 1: Alpha", "B"))],
    "V_tail_sole_figure": [("cap_img", ("Figure 1: Alpha", "A")), ("cap", "Figure 2: Beta")],
    "U_tail_text_before_next": [("img", "A"), ("cap_img", ("Figure 1: Alpha", "B")), ("text", "Some body text between."),
                                ("cap", "Figure 2: Beta")],
}

# 배치 → (캡션 번호 → 그림 목록, 짝 없는 그림 목록)
EXPECT = {
    "1_no_logo": ({"1": ["A"]}, []),
    "2_separate_logo": ({"1": ["A"]}, ["logo"]),
    "3_adjacent_composite": ({"1": ["A", "B"]}, []),
    "4_fig_text_cap_fig": ({"1": ["A"]}, ["B"]),
    "5_fig_cap_fig": ({"1": ["A"]}, ["B"]),
    "6_media_name_swap": ({"1": ["A"], "2": ["B"]}, ["logo"]),
    "X_caption_above_line": ({"1": ["A"], "2": ["B"]}, []),
    "Y_tail_to_empty_next": ({"1": ["A"], "2": ["B"]}, []),
    "Z_tail_next_has_figure": ({"1": ["A"], "2": ["B"]}, []),
    "W_tail_no_next": ({"1": ["A", "B"]}, []),
    "V_tail_sole_figure": ({"1": ["A"]}, []),
    "U_tail_text_before_next": ({"1": ["A", "B"]}, []),
}


def build(items, path: Path) -> None:
    d = docx.Document()
    for kind, value in items:
        if kind == "img":
            d.add_paragraph().add_run().add_picture(io.BytesIO(BLOBS[value]), width=Inches(0.5))
        elif kind == "cap_img":
            d.add_paragraph(value[0]).add_run().add_picture(io.BytesIO(BLOBS[value[1]]), width=Inches(0.5))
        else:
            d.add_paragraph(value)
    d.save(str(path))


def swap_media(src: Path, dst: Path) -> int:
    """미디어 부품 이름 둘을 맞바꾸고 관계 대상도 같이 바꾼다. 단위 · 관계 id · 부품 내용은 그대로."""
    with zipfile.ZipFile(src) as zin:
        media = sorted(n for n in zin.namelist() if n.startswith("word/media/"))
        a, b = media[0], media[1]
        rename = {a: b, b: a}
        ta, tb = a[len("word/"):], b[len("word/"):]
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
            for name in zin.namelist():
                data = zin.read(name)
                if name == "word/_rels/document.xml.rels":
                    data = data.decode().replace(ta, "\0").replace(tb, ta).replace("\0", tb).encode()
                zout.writestr(rename.get(name, name), data)
    return len(media)


def pairs(path: Path):
    doc = docx.Document(str(path))
    blob = {str(part.partname): part.blob for part in doc.part.package.iter_parts()}
    got: dict[str, list[str]] = {}
    uncaptioned: list[str] = []
    for f in docx_figures.figures(doc, "R0-0000000"):
        names = [BY_HASH.get(hashlib.sha256(blob[p]).hexdigest(), "?") for p in f.parts]
        if f.figure_number:
            got.setdefault(str(f.figure_number).removeprefix("Figure ").strip(), []).extend(names)
        else:
            uncaptioned.extend(names)
    return got, sorted(uncaptioned)


def main() -> int:
    failed = []
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for name, items in LAYOUTS.items():
            path = work / f"{name}.docx"
            build(items, path)
            got = pairs(path)
            want = (EXPECT[name][0], sorted(EXPECT[name][1]))
            ok = got == want
            line = f"{name}: got={got[0]} uncaptioned={got[1]}"
            if name == "6_media_name_swap":
                swapped = work / f"{name}__swapped.docx"
                if swap_media(path, swapped) < 2:
                    ok = False
                    line += " swap=부품이 둘 미만"
                else:
                    got_swapped = pairs(swapped)
                    ok = ok and got_swapped == got
                    line += f" swapped={got_swapped[0]} swapped_uncaptioned={got_swapped[1]}"
            print(("PASS " if ok else "FAIL ") + line)
            if not ok:
                failed.append(name)
    print(f"{len(LAYOUTS) - len(failed)}/{len(LAYOUTS)} PASS  docx_figures={Path(docx_figures.__file__).resolve().name}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
