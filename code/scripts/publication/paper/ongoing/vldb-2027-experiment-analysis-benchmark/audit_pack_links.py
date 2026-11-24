"""CR 의 TSG 묶음 소속 기록(E4)을 묶음 표지에서 다시 읽어 맞대어 본다 (모델 호출 없음).

E4 는 CR 쪽 `belongsToCRPack` 과 묶음 쪽 `CRPack.hasCR` 이 함께 적는 (CR, 묶음) 짝이다. 이 검사는 빌드 코드도,
빌드가 남긴 표지 해석 결과도 쓰지 않고 표지 파일을 직접 연다. 표지는 두 곳에 있다.
- CR 수집본: `change-requests/<WG>/derived/Rel-*/TSG/<묶음>/` 아래(하위 폴더 포함)의 `<묶음>_cover.docx`. E4 를 만든
  입력과 같은 묶음이다.
- 총회 회의 문서: `meetings/TSG_RAN/source/TSGR_*/Docs/<묶음>.zip`. CR 수집 범위 밖 묶음도 여기에 있고, 표지는 대개
  Word 97 이진 형식(.doc)이다. 이 검사는 .doc 의 본문 글을 직접 읽는다(`word_text`). 같은 읽기로 CR 수집본 원본 zip 의
  .doc 표지를 읽어 변환된 docx 표지와 맞대어 보고 결과를 `docReaderCheck` 에 남긴다.
표지의 CR 표는 머리 행에 문서 번호 칸(대개 `TD#`, 표지에 따라 `WG TD#` · `Tdoc` · `WG Tdoc` · `RAN1 Tdoc` · `R3 #`)을
두고, 행마다 그 칸에 작업반 문서 번호를 적는다. 받는 표기와 그 근거는 `TD_HEADER` 에 적었다.

- 정확도: E4 짝마다 그 묶음 CR 수집본 표지의 CR 행 문서 번호 칸에 CR 번호가 있는지 본다. 표지를 모두 읽어도 몇 분이면
  끝나므로 표본을 뽑지 않고 모든 짝을 본다. 확인되지 않은 짝은 정해 둔 차례(`REASON_ORDER`)로 까닭을 가른다.
  CR 수집본 표지로 판정하지 못한 짝은 총회 회의 문서의 표지로 따로 본다. 이 작업반 CR 수집본에 묶음 폴더가 없는
  짝은 다른 작업반 CR 수집본에 있는 같은 묶음 표지도 따로 본다.
- 재현율: 문서 목록의 `tdoc:tsgCRPack` 이 묶음 P 를 적었는데 (문서, P) E4 짝이 없는 문서를 묶음 수집 여부와
  표지 내용으로 가른다. `measure_pack_source_agreement.py` 의 documentListOnly 와 differentPack 을 합친 집합이다.
  묶음이 CR 수집본에 없으면 CR 수집 범위(작업반 TS 목록, Rel-15~Rel-20, CR 목록)와 총회 회의 문서의 표지로 다시 가른다.
- 표지 기준 짝: 이 작업반 폴더에 수집된 표지의 CR 행 문서 번호 칸에 적힌, 이 작업반 접두의 번호마다 E4 짝이 있는지 본다.

docx 는 `w:t` 를 모으고, 줄 안 하이픈 요소(`w:noBreakHyphen`)는 "-" 로, 탭·줄바꿈·기호 요소는 공백으로 읽는다. 지운 글(`w:del` · `w:delText`), 옮겨 가기 전 글(`w:moveFrom`), 필드 코드(`w:instrText`),
호환용 대체 내용(`mc:Fallback`)은 읽지 않는다. 칸 위치는 `w:gridBefore` · `w:gridSpan` 으로 맞추고, 세로로 합친 칸
(`w:vMerge`)은 위 칸의 글을 이어 받는다. .doc 는 필드 코드를 빼고 필드 결과만 남긴다. 한 묶음 표지가 여러 사본으로
있으면 읽을 수 있는 사본을 합쳐 본다. 문서 번호는 기록과 같은 철자(`R1-1803551`, `R5s180525`)로 적힌 것과,
대시 종류·띄어쓰기·대소문자를 맞춰야 읽히는 것을 나누어 센다.

사용 (저장소 루트에서 실행):
  python3 -I audit_pack_links.py --wg RAN1 RAN2 RAN3 RAN4 RAN5 --phase4-root <RAN5 묶음 기록 폴더> \\
      --manifest <export_manifest.json> --agreement <json> [<json> ...] --out <json> --items <jsonl>
"""
from __future__ import annotations

import argparse
import collections
import csv
import gc
import hashlib
import io
import json
import random
import re
import struct
import zipfile
import zlib
from pathlib import Path
from xml.etree import ElementTree

INSTANCES = Path("ontology/output/tsg/RAN/formal/instances")
CORPUS = Path("data/corpus/tsg/RAN/formal/change-requests")
# TSG RAN 총회 회의 문서. 총회에 올라온 묶음 zip 이 회의별로 있다. CR 수집 범위 밖 묶음도 여기에는 있다.
MEETINGS = Path("data/corpus/tsg/RAN/formal/meetings/TSG_RAN/source")
# 작업반마다 CR 을 모은 TS 목록. CR 목록(`cr_list.csv`)은 이 목록의 `TS` 에 든 spec 하나·릴리스 하나씩 받았다
# (`docs/tsg/RAN/formal/RAN{N}/phase-0/step2_change-requests-download.md`).
SPEC_SCOPE = Path("data/inventory/RAN/wg_spec_mapping.json")
# 같은 문서가 받은 릴리스 범위. 위 문서의 Release 표가 Rel-15 부터 Rel-20 까지다.
RELEASES = range(15, 21)
# 3GPP Portal 의 CR 목록을 받아 둔 것. 38 · 37 계열 spec 의 Rel-15 이후 CR 만 있다. 작업반 문서마다 TSG 문서와 TSG 결정을 적는다.
PORTAL = Path("data/inventory/RAN/portal_data_all_ran.json")
WGS = ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5")
# 작업반 접두. RAN5 는 신호 시험 문서를 `R5s` 로 따로 번호 매긴다.
PREFIXES = {"RAN1": ("R1-",), "RAN2": ("R2-",), "RAN3": ("R3-",), "RAN4": ("R4-",), "RAN5": ("R5-", "R5s")}
PACK_NUMBER = re.compile(r"RP-\d+")
# 요청한 사례 수(유형마다 2~3건)를 채우는 수다. 통계에는 쓰지 않는다.
EXAMPLES = 3

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
SKIP = {W + "del", W + "moveFrom", W + "delText", W + "instrText",
        "{http://schemas.openxmlformats.org/markup-compatibility/2006}Fallback"}
# 탭·줄바꿈·기호 요소. 글자 사이를 띄우는 자리라 공백으로 읽는다(`w:sym` 은 기호 글꼴의 한 글자다).
BREAKS = {W + "tab", W + "ptab", W + "br", W + "cr", W + "sym"}
# 줄 바꿈하지 않는 하이픈. 글자로는 하이픈이고 `w:t` 밖에 따로 적힌다.
HYPHENS = {W + "noBreakHyphen"}
# 머리 행은 칸 글에서 공백을 빼고 소문자로 바꾼 값이 이 가운데 하나와 같은 행이다. 부분 일치는 쓰지 않는다
# (본문 행의 `tdd` · `ltd` 같은 낱말이 걸린다). 실제로 나온 머리 행 표기는 출력의 `headerSignatures` 에 모두 남긴다.
# 문서 목록이 적은 묶음의 총회 표지 4807건에서 `Spec`/`TS`/`CR` 칸이 든 행을 머리 행으로 보고 표지마다 서로 다른 머리
# 행을 세면 4805행이다. 그 문서 번호 칸은 `TD#` 4549 · `WG TD#` 105 · `Tdoc` 61 · `WG Tdoc` 41 · `RAN1 Tdoc` 38 ·
# `R3 #` 11 로 적혀 있고, 나머지 표지 2건은 머리 행 없는 표다. `RAN1 Tdoc` 과 `R3 #` 은 작업반 번호를 넣은 표기라
# 다른 작업반 번호를 넣은 같은 꼴도 받는다. spec 칸은 `TS` · `Spec`, CR 번호 칸은 `CR` 로만 적혀 있다. 묶음 번호 칸은
# CR 수집본 RAN5 표지의 `TSG CR Pack` 과 `R3 #` 표지의 `RP #` 이다. CR 수집본 표지의 머리 행도 모두 이 표기 안에 든다
# (`headerSignatures`). 두 표지 묶음 어디에도 나오지 않는 표기는 받지 않는다.
TD_HEADER = {"td#", "wgtd#", "tdoc", "wgtdoc"} | {f"ran{n}tdoc" for n in range(1, 6)} | {f"r{n}#" for n in range(1, 6)}
ROLE_HEADERS = {"ts": {"ts", "spec"}, "cr": {"cr"}, "pack": {"tsgcrpack", "rp#"}}
DASHES = re.compile("[‐‑‒–—―−﹣－]")
EXACT = re.compile(r"(?<![A-Za-z0-9])(?:(R[1-5])-(\d{6,7})|R5s(\d{6}))(?!\d)")
LOOSE = re.compile(r"(?<![A-Z0-9])R\s*(?:([1-5])\s*-?\s*(\d{6,7})|5\s*S\s*-?\s*(\d{6}))(?!\d)", re.I)
FILE_CR = re.compile(r"^(?P<spec>\d[\w.\-]*?)_CR(?P<cr>\d+)(?:r\d+)?_")
# 묶음 zip 안의 표지 파일 이름. `RP-192647_cover.doc` · `RP-182887 Cover.docx` 처럼 묶음 번호 뒤에 cover 를
# 붙이거나, 옛 묶음처럼 묶음 번호만 이름으로 쓴다(`RP-170606.doc`). 이름에 cover 가 들어 있기만 한 CR 파일
# (`… Fast MCG Recovery ….docx`)이나 다른 묶음의 표지는 걸리지 않는다. 대소문자는 가리지 않는다.
COVER_NAME = r"{pack}(?:[ _\-]*cover(?:sheet)?)?\.docx?"

# zip 을 열거나 풀 때 손상·미지원 압축 방식·잘린 파일로 나는 오류. 이 오류가 나면 그 파일을 읽지 못한 것으로 센다.
ZIP_ERRORS = (OSError, ValueError, EOFError, RuntimeError, NotImplementedError, zlib.error, zipfile.BadZipFile)
# Word 97 이진 문서(.doc)의 상자. 복합 문서(CFB) 서명과 섹터 사슬의 끝 표시 두 가지(끝 · 빈 섹터)다.
CFB_SIGNATURE = bytes.fromhex("D0CF11E0A1B11AE1")
CHAIN_END = (0xFFFFFFFE, 0xFFFFFFFF)
NO_ENTRY = 0xFFFFFFFF
WORD97 = 0xA5EC
# 압축 조각(한 글자 1바이트)은 cp1252 와 같되 0x81 · 0x8D · 0x8F · 0x90 · 0x9D 는 그 값 그대로다.
CP1252 = {byte: bytes([byte]).decode("cp1252") for byte in range(0x80, 0xA0)
          if byte not in (0x81, 0x8D, 0x8F, 0x90, 0x9D)}
# .doc 본문의 특수 글자. 칸·행 끝(0x07)과 문단 끝(\r)은 표를 나누는 데 쓰고, 칸 글을 모을 때는 아래처럼 바꾼다.
# 0x0B 줄 바꿈 · 0x0C 쪽 나눔은 띄어쓰기, 0x1E 줄 바꿈하지 않는 하이픈은 하이픈, 0x1F 선택 하이픈과 개체 자리(0x01 그림 ·
# 0x02 각주 · 0x05 메모 · 0x08 그림 개체)는 지운다.
DOC_CONTROLS = str.maketrans({"\r": " ", "\x07": " ", "\x0b": " ", "\x0c": " ", "\x1e": "-", "\x1f": None,
                              "\x01": None, "\x02": None, "\x05": None, "\x08": None})

# 표지 표가 문서 번호를 이 묶음 행의 문서 번호 칸에 들지 않을 때의 까닭. 확인되지 않은 E4 짝과, 문서 목록만 묶음을
# 적었고 표지가 그 문서를 들지 않는 문서에 함께 쓴다. 여럿이 맞으면 앞의 것으로 세고, 모든 표시는 항목 파일에 남긴다.
REASON_ORDER = ("listedForOtherPack", "digitsInNumberCellOtherSpelling", "inOtherCellOfCrRow", "elsewhereInCover",
                "sameSpecCrAsRevision", "sameSpecCrOtherNumber", "directoryFileOnly", "absent")
# 총회 회의 문서 표지로 본 결과. 앞의 것일수록 판정 전 단계에서 멈춘 것이다.
MEETING_ORDER = ("zipAbsent", "zipUnreadable", "noCoverInZip", "coverUnreadable", "coverWithoutCrTable",
                 "coverListsDocument", "coverDoesNotListDocument")
# CR 수집본에 없는 묶음을 문서가 적었을 때, 그 문서가 CR 수집 범위의 어느 조건에서 빠지는지. 앞 조건부터 본다.
SCOPE_ORDER = ("specUnknown", "specNotInThisWgList", "releaseUnknown", "releaseBeforeRel15", "releaseAfterRel20",
               "inScopeNotInCrList", "inScopeCrListNamesOtherPack", "inScopeCrListNamesThisPack")
# 재현율 추정 셋. 분모에 넣는 문서의 범위와 총회 표지로 확인한 짝을 분자에 넣는지가 다르다(각 추정의 `denominatorIs`).
ESTIMATES = ("recallEstimate", "recallEstimateWithMeetingCovers", "recallEstimateWithMeetingCoversInDeclaredScope")


def as_list(value) -> list:
    return [] if value is None else value if isinstance(value, list) else [value]


def available_gib() -> float:
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) / 1024 / 1024
    raise RuntimeError("MemAvailable 항목이 /proc/meminfo 에 없다")


def guard(floor: float, step: str) -> float:
    gc.collect()
    free = available_gib()
    if free < floor:
        raise SystemExit(f"가용 메모리 {free:.1f}GiB 가 하한 {floor}GiB 미만이어서 멈춘다: {step}")
    return free


def numbers(text: str) -> dict[str, bool]:
    """글 안의 작업반 문서 번호. 값은 기록과 같은 철자로 적혔으면 True, 철자를 맞춰야 읽혔으면 False."""
    found = {(f"{m[1]}-{m[2]}" if m[1] else f"R5s{m[3]}"): True for m in EXACT.finditer(text)}
    for m in LOOSE.finditer(DASHES.sub("-", text)):
        found.setdefault(f"R{m[1]}-{m[2]}" if m[1] else f"R5s{m[3]}", False)
    return found


def digits_of(number: str) -> str:
    return number.split("-", 1)[1] if "-" in number else number[3:]


def spec_key(text: str | None) -> str | None:
    if not text:
        return None
    value = re.sub(r"^(?:ts|tr)", "", re.sub(r"[\s._]", "", text.lower()))
    return value or None


def cr_key(text: str | None) -> int | None:
    found = re.search(r"\d+", text or "")
    return int(found[0]) if found else None


def release_number(text: str | None) -> int | None:
    found = re.fullmatch(r"Rel-(\d+)", text or "")
    return int(found[1]) if found else None


def member_name(name: str) -> str:
    """zip 안 파일의 이름 부분. 대시 종류를 맞춘다."""
    return DASHES.sub("-", name.replace("\\", "/").rsplit("/", 1)[-1])


def zip_index(paths) -> tuple[dict[str, list[Path]], collections.Counter]:
    """zip 파일을 묶음 번호로 찾는 색인. 확장자 대소문자를 가리지 않고, 이름은 대시 종류와 대소문자를 맞춘다."""
    index: dict[str, list[Path]] = collections.defaultdict(list)
    spelling = collections.Counter()
    for path in sorted(paths):
        if path.suffix.lower() != ".zip" or not path.is_file():
            continue
        stem = DASHES.sub("-", path.stem).upper()
        index[stem].append(path)
        spelling["asIs" if stem == path.stem else "respelled"] += 1
        spelling["packNumberName" if PACK_NUMBER.fullmatch(stem) else "otherName"] += 1
    return index, spelling


# ---- docx 표지 ----

def gridval(element, default: int) -> int:
    try:
        return int(element.get(W + "val", default)) if element is not None else default
    except ValueError:
        return default


def collect_text(element, parts: list[str], into_tables: bool) -> None:
    for child in element:
        if child.tag in SKIP or (child.tag == W + "tbl" and not into_tables):
            continue
        if child.tag == W + "t":
            parts.append(child.text or "")
        elif child.tag in BREAKS:
            parts.append(" ")
        elif child.tag in HYPHENS:
            parts.append("-")
        else:
            collect_text(child, parts, into_tables)
            if child.tag == W + "p":
                parts.append(" ")


def text_of(element, into_tables: bool = False) -> str:
    parts: list[str] = []
    collect_text(element, parts, into_tables)
    return " ".join("".join(parts).split())


def read_tables(root) -> list[list[list[dict]]]:
    """문서의 모든 표(안긴 표 포함). 표 → 행 → 칸(`col` 격자 시작 위치, `span`, `merge`, `text`)."""
    tables: list[list[list[dict]]] = []

    def walk(node) -> None:
        for child in node:
            if child.tag in SKIP:
                continue
            if child.tag == W + "tbl":
                rows: list[list[dict]] = []
                tables.append(rows)
                walk_table(child, rows)
            else:
                walk(child)

    def walk_table(node, rows) -> None:
        for child in node:
            if child.tag == W + "tr":
                rows.append(read_row(child))
            elif child.tag not in SKIP and child.tag not in (W + "tblPr", W + "tblGrid"):
                walk_table(child, rows)

    def read_row(row) -> list[dict]:
        cells: list[dict] = []
        properties = row.find(W + "trPr")
        position = [gridval(properties.find(W + "gridBefore") if properties is not None else None, 0)]

        def walk_cells(node) -> None:
            for child in node:
                if child.tag == W + "tc":
                    properties = child.find(W + "tcPr")
                    span = gridval(properties.find(W + "gridSpan") if properties is not None else None, 1)
                    merge = properties.find(W + "vMerge") if properties is not None else None
                    cells.append({"col": position[0], "span": max(span, 1), "text": text_of(child),
                                  "merge": None if merge is None else merge.get(W + "val", "continue")})
                    position[0] += max(span, 1)
                    walk(child)
                elif child.tag not in SKIP and child.tag not in (W + "trPr", W + "tblPrEx"):
                    walk_cells(child)

        walk_cells(row)
        return cells

    walk(root)
    return tables


def cover_row(td: str, ts: str, cr: str, pack: str, cells: list[str]) -> dict:
    found = PACK_NUMBER.search(pack)
    return {"td": td, "numbers": numbers(td), "spec": spec_key(ts), "cr": cr_key(cr),
            "pack": found[0] if found else None, "cells": set(numbers(" ".join(cells)))}


def read_cover(source) -> dict:
    """docx 표지 한 사본(경로나 파일 객체)을 읽어 CR 행과 문서 전체의 문서 번호를 낸다."""
    try:
        with zipfile.ZipFile(source) as archive:
            root = ElementTree.fromstring(archive.read("word/document.xml"))
        tables = read_tables(root)
        everything = text_of(root, into_tables=True)
    except ZIP_ERRORS + (KeyError, RecursionError, ElementTree.ParseError) as error:
        return {"readable": False, "format": "docx", "reason": type(error).__name__}
    headers, rows = [], []
    for table in tables:
        columns, previous = None, {}
        for cells in table:
            names = [re.sub(r"\s+", "", cell["text"]).lower() for cell in cells]
            if any(name in TD_HEADER for name in names):
                headers.append("|".join(names))
                columns = {"td": next(c["col"] for c, n in zip(cells, names) if n in TD_HEADER)}
                for role, accepted in ROLE_HEADERS.items():
                    columns[role] = next((c["col"] for c, n in zip(cells, names) if n in accepted), None)
                previous = {}
                continue
            if columns is None:
                continue
            placed = []
            for cell in cells:
                text = previous.get(cell["col"], "") if cell["merge"] == "continue" else cell["text"]
                previous[cell["col"]] = text
                placed.append((cell["col"], cell["span"], text))

            def at(column):
                return "" if column is None else next((t for c, s, t in placed if c <= column < c + s), "")

            rows.append(cover_row(at(columns["td"]), at(columns["ts"]), at(columns["cr"]), at(columns["pack"]),
                                  [t for _, _, t in placed]))
    return {"readable": True, "format": "docx", "headers": headers, "rows": rows, "brokenTables": 0,
            "numbers": set(numbers(everything))}


# ---- Word 97 .doc 표지 ----

class CompoundFile:
    """OLE 복합 문서(CFB). Word 97 .doc 는 이 안에 `WordDocument` 와 `0Table`/`1Table` 흐름을 둔다."""

    def __init__(self, data: bytes) -> None:
        if data[:8] != CFB_SIGNATURE:
            raise ValueError("CFB 서명이 없다")
        shift, mini_shift = struct.unpack_from("<HH", data, 0x1E)
        # 규격이 허용하는 섹터 크기는 512 바이트(9)와 4096 바이트(12), 작은 섹터는 64 바이트(6)뿐이다.
        if shift not in (9, 12) or mini_shift != 6:
            raise ValueError("CFB 섹터 크기가 규격 밖이다")
        self.data, self.size, self.mini_size = data, 1 << shift, 1 << mini_shift
        fat_sectors, directory_start = struct.unpack_from("<II", data, 0x2C)
        self.cutoff, mini_fat_start, mini_fat_sectors, difat_start, difat_sectors = struct.unpack_from("<IIIII", data, 0x38)
        difat = list(struct.unpack_from("<109I", data, 0x4C))
        sector, seen = difat_start, set()
        for _ in range(difat_sectors):
            if sector in CHAIN_END or sector in seen:
                break
            seen.add(sector)
            values = struct.unpack_from(f"<{self.size // 4}I", self.sector(sector))
            difat.extend(values[:-1])
            sector = values[-1]
        self.fat: list[int] = []
        for sector in difat[:fat_sectors]:
            self.fat.extend(struct.unpack_from(f"<{self.size // 4}I", self.sector(sector)))
        directory = self.chain(directory_start)
        entries = []
        for offset in range(0, len(directory) - 127, 128):
            entry = directory[offset:offset + 128]
            length = struct.unpack_from("<H", entry, 64)[0]
            left, right, child = struct.unpack_from("<III", entry, 68)
            start, size = struct.unpack_from("<IQ", entry, 116)
            entries.append({"name": entry[:max(min(length, 64) - 2, 0)].decode("utf-16-le", "replace"),
                            "kind": entry[66], "left": left, "right": right, "child": child, "start": start,
                            "size": size & 0xFFFFFFFF if self.size == 512 else size})
        if not entries or entries[0]["kind"] != 5:
            raise ValueError("CFB 뿌리 항목이 없다")
        root = entries[0]
        # 뿌리 바로 아래 흐름만 찾는다. 문서에 박힌 개체(`ObjectPool`)도 같은 이름의 흐름을 가질 수 있어서다.
        self.streams: dict[str, dict] = {}
        stack, visited = [root["child"]], set()
        while stack:
            index = stack.pop()
            if index == NO_ENTRY or index >= len(entries) or index in visited:
                continue
            visited.add(index)
            entry = entries[index]
            if entry["kind"] == 2:
                self.streams.setdefault(entry["name"], entry)
            stack.extend((entry["left"], entry["right"]))
        self.mini = self.chain(root["start"])[:root["size"]]
        mini_fat = self.chain(mini_fat_start) if mini_fat_sectors and mini_fat_start not in CHAIN_END else b""
        self.mini_fat = list(struct.unpack_from(f"<{len(mini_fat) // 4}I", mini_fat))

    def sector(self, number: int) -> bytes:
        offset = (number + 1) * self.size
        return self.data[offset:offset + self.size]

    def chain(self, start: int) -> bytes:
        parts, seen, number = [], set(), start
        while number not in CHAIN_END and number < len(self.fat) and number not in seen:
            seen.add(number)
            parts.append(self.sector(number))
            number = self.fat[number]
        return b"".join(parts)

    def stream(self, name: str) -> bytes:
        entry = self.streams[name]
        if entry["size"] < self.cutoff:
            parts, seen, number = [], set(), entry["start"]
            while number not in CHAIN_END and number < len(self.mini_fat) and number not in seen:
                seen.add(number)
                parts.append(self.mini[number * self.mini_size:(number + 1) * self.mini_size])
                number = self.mini_fat[number]
            return b"".join(parts)[:entry["size"]]
        return self.chain(entry["start"])[:entry["size"]]


def word_text(data: bytes) -> str:
    """Word 97 문서의 본문 글. 조각 표(`Clx` 의 `PlcPcd`)를 따라 이어 붙이고 본문 길이(`ccpText`)에서 자른다.
    머리글·각주·글상자는 본문 뒤에 이어 오므로 잘린다."""
    compound = CompoundFile(data)
    document = compound.stream("WordDocument")
    if struct.unpack_from("<H", document, 0)[0] != WORD97:
        raise ValueError("Word 97 문서가 아니다")
    flags = struct.unpack_from("<H", document, 0x0A)[0]
    if flags & 0x0100:
        raise ValueError("암호화된 문서다")
    table = compound.stream("1Table" if flags & 0x0200 else "0Table")
    # FIB: 고정부 32 바이트, 그다음 16비트 값 묶음, 32비트 값 묶음(4번째가 ccpText), (위치, 길이) 짝 묶음(34번째가 Clx).
    position = 32
    position += 2 + struct.unpack_from("<H", document, position)[0] * 2
    longs = struct.unpack_from("<H", document, position)[0]
    text_length = struct.unpack_from("<i", document, position + 2 + 3 * 4)[0]
    position += 2 + longs * 4 + 2
    clx_offset, clx_length = struct.unpack_from("<II", document, position + 33 * 8)
    clx = table[clx_offset:clx_offset + clx_length]
    index = 0
    while index < len(clx) and clx[index] == 1:
        size = struct.unpack_from("<h", clx, index + 1)[0]
        if size < 0:
            raise ValueError("Clx 서식 묶음 길이가 음수다")
        index += 3 + size
    if index >= len(clx) or clx[index] != 2:
        raise ValueError("조각 표가 없다")
    length = struct.unpack_from("<I", clx, index + 1)[0]
    pieces = clx[index + 5:index + 5 + length]
    count = (length - 4) // 12
    positions = struct.unpack_from(f"<{count + 1}I", pieces, 0)
    parts = []
    for k in range(count):
        location = struct.unpack_from("<I", pieces, (count + 1) * 4 + k * 8 + 2)[0]
        characters = max(positions[k + 1] - positions[k], 0)
        if location & 0x40000000:
            offset = (location & 0x3FFFFFFF) // 2
            parts.append(document[offset:offset + characters].decode("latin-1").translate(CP1252))
        else:
            offset = location & 0x3FFFFFFF
            parts.append(document[offset:offset + 2 * characters].decode("utf-16-le", "replace"))
    text = "".join(parts)
    return text[:text_length] if text_length > 0 else text


def visible(text: str) -> str:
    """필드 코드(0x13 과 0x14 사이)는 빼고 필드 결과(0x14 와 0x15 사이)는 남긴다. 필드는 겹칠 수 있다."""
    out, codes = [], []
    for character in text:
        if character == "\x13":
            codes.append(True)
        elif character == "\x14":
            if codes:
                codes[-1] = False
        elif character == "\x15":
            if codes:
                codes.pop()
        elif not any(codes):
            out.append(character)
    return "".join(out)


def header_name(piece: str) -> str:
    return re.sub(r"\s+", "", piece.rsplit("\r", 1)[-1]).lower()


def doc_tables(text: str) -> list[dict]:
    """.doc 본문에서 머리 행을 기준으로 CR 표를 찾는다.

    칸은 0x07 로 끝나고, 행은 마지막 칸 뒤에 0x07 을 하나 더 둔다. 그래서 0x07 로 나누면 행 끝이 빈 조각이 된다.
    빈 칸도 빈 조각이므로 칸 수는 머리 행에서 정한다. 문서 번호 머리 칸이 든 조각에서 앞으로는 문단 끝이나 빈 조각이
    나올 때까지, 뒤로는 빈 조각(행 끝)까지가 머리 행이다. 그 뒤로 칸 수 + 1 조각씩 끊어 마지막이 빈 조각이면 한 행으로
    읽고, 아니면 그 자리에서 표가 끝났거나 칸 수가 바뀐 것으로 보고 멈춘다(`brokenAt`)."""
    pieces = text.split("\x07")
    tables, index = [], 0
    while index < len(pieces):
        if header_name(pieces[index]) not in TD_HEADER:
            index += 1
            continue
        start = index
        while start > 0 and pieces[start - 1] != "" and "\r" not in pieces[start - 1]:
            start -= 1
        if start > 0 and pieces[start - 1] != "" and "\r" in pieces[start - 1]:
            start -= 1
        end = index
        while end < len(pieces) and pieces[end] != "":
            end += 1
        header = [header_name(pieces[start])] + [re.sub(r"\s+", "", piece).lower() for piece in pieces[start + 1:end]]
        width = len(header)
        rows, cursor, broken = [], end + 1, None
        while cursor + width < len(pieces) + 1:
            chunk = pieces[cursor:cursor + width + 1]
            if len(chunk) < width + 1 or chunk[width] != "":
                broken = cursor
                break
            rows.append(chunk[:width])
            cursor += width + 1
        tables.append({"header": header, "rows": rows, "brokenAt": broken})
        index = cursor if cursor > index else index + 1
    return tables


def doc_cell(text: str) -> str:
    return " ".join(text.translate(DOC_CONTROLS).split())


def read_doc_cover(data: bytes) -> dict:
    """.doc 표지를 읽어 docx 표지와 같은 모양(CR 행과 문서 전체의 문서 번호)으로 낸다."""
    text = visible(word_text(data))
    headers, rows, broken = [], [], 0
    for table in doc_tables(text):
        names = table["header"]
        headers.append("|".join(names))
        broken += table["brokenAt"] is not None
        columns = {"td": next(i for i, name in enumerate(names) if name in TD_HEADER)}
        for role, accepted in ROLE_HEADERS.items():
            columns[role] = next((i for i, name in enumerate(names) if name in accepted), None)
        for raw in table["rows"]:
            cells = [doc_cell(cell) for cell in raw]

            def at(column):
                return "" if column is None else cells[column]

            rows.append(cover_row(at(columns["td"]), at(columns["ts"]), at(columns["cr"]), at(columns["pack"]), cells))
    return {"readable": True, "format": "doc", "headers": headers, "rows": rows, "brokenTables": broken,
            "numbers": set(numbers(doc_cell(text)))}


def read_any_cover(data: bytes) -> dict:
    """표지 파일 내용을 서명으로 가려 읽는다. 확장자는 믿지 않는다."""
    if data[:8] == CFB_SIGNATURE:
        try:
            return read_doc_cover(data)
        except (ValueError, KeyError, IndexError, StopIteration, struct.error, RecursionError) as error:
            return {"readable": False, "format": "doc", "reason": f"{type(error).__name__}: {error}"}
    if data[:4] == b"PK\x03\x04":
        return read_cover(io.BytesIO(data))
    return {"readable": False, "format": "other", "reason": "unknownSignature", "signature": data[:8].hex()}


def own_numbers(cover: dict, pack: str) -> set[str]:
    """표지의 CR 행 가운데 다른 묶음을 적은 행을 뺀 행의 문서 번호."""
    return {number for row in cover["rows"] if not row["pack"] or row["pack"] == pack for number in row["numbers"]}


def combine(pack: str, parsed: list[dict], file_names: list[str], file_spec_cr: dict) -> dict:
    """한 묶음의 표지 사본들과 같은 묶음 파일 이름들을 합친 보기."""
    readable = [cover for cover in parsed if cover["readable"]]
    tabled = [cover for cover in readable if cover["headers"]]
    listed: dict[str, bool] = {}
    other_pack: dict[str, set[str]] = collections.defaultdict(set)
    cells, texts, spec_cr, per_copy = set(), [], collections.defaultdict(set), []
    for cover in tabled:
        mine = set()
        for row in cover["rows"]:
            cells |= row["cells"]
            if row["pack"] and row["pack"] != pack:
                for number in row["numbers"]:
                    other_pack[number].add(row["pack"])
                continue
            texts.append(row["td"])
            for number, exact in row["numbers"].items():
                listed[number] = listed.get(number, False) or exact
                mine.add(number)
            if row["spec"] and row["cr"] is not None:
                spec_cr[(row["spec"], row["cr"])] |= set(row["numbers"])
        per_copy.append(frozenset(mine))
    files = set()
    for name in file_names:
        found = set(numbers(name))
        files |= found
        parts = FILE_CR.match(name)
        if parts:
            for number in found:
                file_spec_cr.setdefault(number, (spec_key(parts["spec"]), int(parts["cr"])))
    return {"readable": len(readable), "tabled": len(tabled), "listed": listed, "otherPack": other_pack,
            "cells": cells, "tdTexts": texts, "specCr": spec_cr, "copiesDiffer": len(set(per_copy)) > 1,
            "perCopy": per_copy, "document": set().union(*(cover["numbers"] for cover in readable)), "files": files,
            "formats": sorted({cover["format"] for cover in parsed}),
            "brokenTables": sum(cover.get("brokenTables", 0) for cover in readable),
            "unreadableReasons": sorted({cover.get("reason", "") for cover in parsed if not cover["readable"]})}


def cover_copies(directory: Path, pack: str) -> list[Path]:
    """묶음 폴더 안의 `<묶음>_cover.docx`. 대개 폴더 바로 아래에 있지만, zip 을 같은 이름의 안쪽 폴더째 풀어 둔 묶음
    (`RP-201501/RP-201501/`)은 한 단계 아래에 있다. 그래서 하위 폴더까지 찾는다."""
    return sorted(path for path in directory.rglob(f"{pack}_cover.docx") if path.is_file())


class Corpus:
    """다섯 작업반 묶음 폴더, CR 수집본 원본 zip, 총회 회의 문서 zip 의 색인. 표지는 처음 볼 때 한 번만 읽는다."""

    def __init__(self, floor: float) -> None:
        self.floor = floor
        self.dirs = {wg: collections.defaultdict(list) for wg in WGS}
        for wg in WGS:
            for path in sorted(CORPUS.glob(f"{wg}/derived/Rel-*/TSG/*")):
                if path.is_dir():
                    self.dirs[wg][path.name].append(path)
        self.zips, self.zip_spelling = zip_index(CORPUS.glob("*/source/Rel-*/TSG/*"))
        self.meeting_zips, self.meeting_spelling = zip_index(MEETINGS.glob("TSGR_*/Docs/*"))
        self.covers: dict[Path, dict] = {}
        self.views: dict[tuple[str, str], dict] = {}
        self.meeting_views: dict[str, dict] = {}
        self.zip_names: dict[Path, set[str] | None] = {}
        self.file_spec_cr: dict[str, tuple[str, int]] = {}

    def cover(self, path: Path) -> dict:
        if path not in self.covers:
            self.covers[path] = read_cover(path)
        return self.covers[path]

    def view(self, wg: str, pack: str) -> dict:
        key = (wg, pack)
        if key in self.views:
            return self.views[key]
        directories = self.dirs[wg].get(pack, [])
        copies = [copy for d in directories for copy in cover_copies(d, pack)]
        # 묶음 폴더 안의 하위 폴더도 그 묶음의 파일이다. 작업반 문서 zip 을 풀어 둔 폴더(`R5-193543/`)에 CR 파일이
        # 들기도 한다.
        names = [path.name for d in directories for path in d.rglob("*")
                 if path.is_file() and path.name not in (f"{pack}_cover.docx", f"{pack}_cover.doc")]
        self.views[key] = {"directories": len(directories), "copies": [str(path) for path in copies],
                           **combine(pack, [self.cover(path) for path in copies], names, self.file_spec_cr)}
        return self.views[key]

    def cover_members(self, archive: zipfile.ZipFile, pack: str) -> tuple[list[zipfile.ZipInfo], list[str]]:
        matcher = re.compile(COVER_NAME.format(pack=re.escape(pack)), re.I)
        covers, others = [], []
        for info in archive.infolist():
            if info.is_dir():
                continue
            name = member_name(info.filename)
            (covers.append(info) if matcher.fullmatch(name) else others.append(name))
        return covers, others

    def read_member(self, archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> dict:
        # 압축을 푼 크기가 하한을 넘는 가용 메모리보다 크면 읽지 않는다. 이 검사가 지키는 메모리 하한에서 정한 값이다.
        headroom = (available_gib() - self.floor) * 2 ** 30
        if info.file_size > headroom:
            return {"readable": False, "format": None, "reason": f"largerThanMemoryHeadroom:{info.file_size}"}
        try:
            data = archive.read(info)
        except ZIP_ERRORS as error:
            return {"readable": False, "format": None, "reason": f"memberUnreadable:{type(error).__name__}"}
        return read_any_cover(data)

    def meeting_view(self, pack: str) -> dict:
        """총회 회의 문서에 있는 묶음 zip 의 표지와 파일 이름."""
        if pack in self.meeting_views:
            return self.meeting_views[pack]
        zips = self.meeting_zips.get(pack, [])
        parsed, names, members, problems = [], [], [], []
        for path in zips:
            try:
                with zipfile.ZipFile(path) as archive:
                    covers, others = self.cover_members(archive, pack)
                    names.extend(others)
                    for info in covers:
                        members.append(f"{path}::{info.filename}")
                        parsed.append(self.read_member(archive, info))
            except ZIP_ERRORS as error:
                problems.append(f"{path}: {type(error).__name__}")
        self.meeting_views[pack] = {"zips": [str(path) for path in zips], "members": members, "zipProblems": problems,
                                    "fileNames": len(names), **combine(pack, parsed, names, self.file_spec_cr)}
        return self.meeting_views[pack]

    def meeting_class(self, number: str, pack: str) -> tuple[str, dict]:
        view = self.meeting_view(pack)
        if not view["zips"]:
            return "zipAbsent", view
        if len(view["zipProblems"]) == len(view["zips"]):
            return "zipUnreadable", view
        if not view["members"]:
            return "noCoverInZip", view
        if not view["readable"]:
            return "coverUnreadable", view
        if not view["tabled"]:
            return "coverWithoutCrTable", view
        return ("coverListsDocument" if number in view["listed"] else "coverDoesNotListDocument"), view

    def zip_lists(self, path: Path, number: str) -> bool | None:
        """원본 zip 의 파일 이름에 문서 번호가 있는지. zip 을 열지 못하면 None."""
        if path not in self.zip_names:
            try:
                with zipfile.ZipFile(path) as archive:
                    self.zip_names[path] = {n for name in archive.namelist() for n in numbers(member_name(name))}
            except ZIP_ERRORS:
                self.zip_names[path] = None
        names = self.zip_names[path]
        return None if names is None else number in names


def read_cr_lists() -> dict[str, list[dict]]:
    """3GPP CR 목록(`source/Rel-*/metadata/cr_list.csv`)의 작업반 문서 번호별 행."""
    rows: dict[str, list[dict]] = collections.defaultdict(list)
    for path in sorted(CORPUS.glob("*/source/Rel-*/metadata/cr_list.csv")):
        with path.open(encoding="utf-8", errors="replace", newline="") as handle:
            for row in csv.DictReader(handle):
                number = (row.get("wg_tdoc") or "").strip()
                if number:
                    rows[number].append({"tsgTdoc": (row.get("tsg_tdoc") or "").strip(),
                                         "tsgStatus": (row.get("tsg_status") or "").strip(),
                                         "targetRelease": (row.get("target_release") or "").strip(),
                                         "list": str(path.relative_to(CORPUS))})
    return rows


def read_portal(inputs: "Inputs") -> dict[str, list[dict]]:
    """Portal CR 목록의 작업반 문서 번호별 (TSG 문서, TSG 결정, spec, 릴리스)."""
    rows: dict[str, list[dict]] = collections.defaultdict(list)
    loaded = inputs.json(PORTAL)
    for release, records in loaded.items():
        for record in records if isinstance(records, list) else []:
            number = str(record.get("wg_tdoc") or "").strip()
            if number:
                rows[number].append({"tsgTdoc": str(record.get("tsg_tdoc") or "").strip(),
                                     "tsgStatus": str(record.get("tsg_status") or "").strip(),
                                     "spec": str(record.get("spec_number") or ""), "release": release})
    return rows


def read_spec_scope(inputs: "Inputs") -> dict[str, set[str]]:
    return {group: {spec_key(spec) for spec in lists.get("TS", [])}
            for group, lists in inputs.json(SPEC_SCOPE).items()}


class Inputs:
    def __init__(self, floor: float, manifest: dict[str, str]) -> None:
        self.floor, self.manifest, self.read = floor, manifest, []

    def raw(self, path: Path) -> bytes:
        free = guard(self.floor, str(path))
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        self.read.append({"path": str(path), "bytes": len(data), "sha256": digest, "availableGibBeforeRead": round(free, 1),
                          "sameAsExportManifest": None if str(path) not in self.manifest else self.manifest[str(path)] == digest})
        return data

    def json(self, path: Path):
        return json.loads(self.raw(path))

    def graph(self, path: Path) -> list[dict]:
        return self.json(path)["@graph"]


class Revisions:
    """개정 관계(`isRevisionOf` · `revisedTo`)로 이어진 문서 묶음."""

    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, item: str) -> str:
        root = item
        while self.parent.get(root, root) != root:
            root = self.parent[root]
        while self.parent.get(item, item) != root:
            self.parent[item], item = root, self.parent[item]
        return root

    def join(self, a: str, b: str) -> None:
        self.parent.setdefault(a, a)
        self.parent.setdefault(b, b)
        self.parent[self.find(a)] = self.find(b)

    def related(self, a: str, b: str) -> bool:
        return a in self.parent and b in self.parent and self.find(a) == self.find(b)


def sample(items: list, name: str) -> list:
    ordered = sorted(items, key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False, default=sorted))
    return random.Random(name).sample(ordered, min(EXAMPLES, len(ordered)))


def flags_against(number: str, pack: str, view: dict, spec_cr: tuple | None, revisions: Revisions) -> dict:
    """표지 표가 문서 번호를 이 묶음의 행 번호 칸에 들지 않을 때 볼 수 있는 단서."""
    pattern = re.compile(rf"(?<!\d){digits_of(number)}(?!\d)")
    same = sorted(view["specCr"].get(spec_cr, set()) - {number}) if spec_cr else []
    return {
        "listedForOtherPack": sorted(view["otherPack"].get(number, ())),
        "digitsInNumberCellOtherSpelling": any(pattern.search(text) for text in view["tdTexts"]),
        "inOtherCellOfCrRow": number in view["cells"],
        "elsewhereInCover": number in view["document"] and number not in view["cells"],
        "sameSpecCrAsRevision": [n for n in same if revisions.related(number, n)],
        "sameSpecCrOtherNumber": [n for n in same if not revisions.related(number, n)],
        "directoryFileOnly": number in view["files"],
    }


def first_reason(flags: dict, order: tuple[str, ...]) -> str:
    return next((name for name in order[:-1] if flags[name]), order[-1])


def meeting_fields(corpus: Corpus, number: str, pack: str, spec_cr: tuple | None, revisions: Revisions) -> dict:
    """총회 회의 문서의 표지로 본 결과를 항목에 붙일 필드로 낸다."""
    name, view = corpus.meeting_class(number, pack)
    fields = {"meeting": name, "meetingZips": view["zips"], "meetingCoverMembers": view["members"],
              "meetingCoverFormats": view["formats"], "meetingZipFileNamesDocument": number in view["files"]}
    if name == "coverListsDocument":
        fields["meetingExactSpelling"] = view["listed"][number]
    if name == "coverDoesNotListDocument":
        flags = flags_against(number, pack, view, spec_cr, revisions)
        fields.update(meetingFlags=flags, meetingReason=first_reason(flags, REASON_ORDER),
                      meetingBrokenTables=view["brokenTables"])
    if name in ("coverUnreadable", "zipUnreadable"):
        fields["meetingProblems"] = view["unreadableReasons"] + view["zipProblems"]
    return fields


def collection_scope(wg: str, document: dict, listings: list[dict], pack: str, spec_lists: dict[str, set[str]]) -> dict:
    """문서가 CR 수집 범위(이 작업반 TS 목록, Rel-15~Rel-20, CR 목록)의 어느 조건에서 빠지는지."""
    spec, release = document["spec"], release_number(document["release"])
    owners = sorted(group for group, specs in spec_lists.items() if spec and spec in specs)
    cr_list = ("namesThisPack" if any(row["tsgTdoc"] == pack for row in listings)
               else "namesOtherPack" if listings else "absent")
    if spec is None:
        verdict = "specUnknown"
    elif wg not in owners:
        verdict = "specNotInThisWgList"
    elif release is None:
        verdict = "releaseUnknown"
    elif release < RELEASES.start:
        verdict = "releaseBeforeRel15"
    elif release >= RELEASES.stop:
        verdict = "releaseAfterRel20"
    else:
        verdict = {"absent": "inScopeNotInCrList", "namesOtherPack": "inScopeCrListNamesOtherPack",
                   "namesThisPack": "inScopeCrListNamesThisPack"}[cr_list]
    return {"verdict": verdict, "spec": spec, "specInTsListOf": owners, "release": document["release"], "crList": cr_list}


def doc_reader_check(wg: str, corpus: Corpus) -> dict:
    """CR 수집본 원본 zip 의 .doc 표지와 수집 때 변환된 docx 표지가 이 묶음 행에 드는 문서 번호 집합이 같은지 본다.
    총회 회의 문서의 .doc 표지를 같은 읽기로 판정하므로, 이 비교가 그 읽기의 근거다. 사본마다 모두 비교한다."""
    counts, examples = collections.Counter(), collections.defaultdict(list)
    for pack, directories in sorted(corpus.dirs[wg].items()):
        for directory, copy in ((d, c) for d in directories for c in cover_copies(d, pack)):
            counts["docxCopies"] += 1
            folder = CORPUS / wg / "source" / directory.parts[-3] / "TSG"
            source = next((path for path in corpus.zips.get(pack, []) if path.parent == folder), None)
            if source is None:
                counts["noSourceZip"] += 1
                continue
            try:
                with zipfile.ZipFile(source) as archive:
                    covers = [info for info in corpus.cover_members(archive, pack)[0]
                              if info.filename.lower().endswith(".doc")]
                    parsed = [corpus.read_member(archive, info) for info in covers]
            except ZIP_ERRORS:
                counts["sourceZipUnreadable"] += 1
                continue
            if not parsed:
                counts["noDocCoverInSourceZip"] += 1
                continue
            docx = corpus.cover(copy)
            if not docx["readable"]:
                counts["docxUnreadable"] += 1
                continue
            want = own_numbers(docx, pack)
            for cover in parsed:
                counts["compared"] += 1
                if not cover["readable"]:
                    counts["docUnreadable"] += 1
                    examples["docUnreadable"].append({"source": str(source), "reason": cover["reason"]})
                    continue
                counts["brokenTables"] += cover["brokenTables"] > 0
                got = own_numbers(cover, pack)
                if got == want:
                    counts["sameNumbers"] += 1
                else:
                    counts["differentNumbers"] += 1
                    examples["differentNumbers"].append({"source": str(source), "docx": str(copy),
                                                         "onlyDocx": sorted(want - got), "onlyDoc": sorted(got - want)})
    return {"unit": "CR 수집본 표지 사본과 같은 릴리스 폴더 원본 zip 의 .doc 표지 쌍",
            **{name: counts[name] for name in ("docxCopies", "noSourceZip", "sourceZipUnreadable",
                                               "noDocCoverInSourceZip", "docxUnreadable", "compared", "sameNumbers",
                                               "differentNumbers", "docUnreadable", "brokenTables")},
            "criterion": "다른 묶음을 적은 행을 뺀 CR 행 문서 번호 칸의 번호 집합이 같다",
            "examples": {name: sample(entries, f"{wg}/docReader/{name}") for name, entries in sorted(examples.items())}}


def audit(wg: str, corpus: Corpus, inputs: Inputs, phase4_root: Path | None, cr_lists: dict, portal: dict,
          spec_lists: dict, reported: dict, items: list[dict]) -> dict:
    def staged(name: str) -> Path:
        path = phase4_root / wg / name if phase4_root else None
        return path if path and path.exists() else INSTANCES / f"phase-4/{wg}/{name}"

    documents, revisions = {}, Revisions()
    for record in inputs.graph(INSTANCES / f"phase-1/{wg}/tdocs.jsonld"):
        if "tdoc:tdocNumber" not in record:
            continue
        number = record["@id"].removeprefix("tdoc:")
        modifies = record.get("modifies")
        documents[number] = {
            "type": record.get("@type") if isinstance(record.get("@type"), str) else None,
            "tdocType": record.get("tdoc:type"), "status": record.get("tdoc:status"),
            "spec": spec_key(modifies.rsplit("/", 1)[-1]) if isinstance(modifies, str) else None,
            "cr": cr_key(record.get("tdoc:crNumber")),
            "release": str(record["targetRelease"]).rsplit("/", 1)[-1].replace("_", "-") if "targetRelease" in record else None,
            "packField": str(record["tdoc:tsgCRPack"]).strip() if "tdoc:tsgCRPack" in record else None}
        for other in as_list(record.get("isRevisionOf")) + as_list(record.get("revisedTo")):
            revisions.join(number, str(other).removeprefix("tdoc:"))

    pack_records = inputs.graph(staged("crpacks.jsonld"))
    pack_id = {record["@id"]: record["tdoc:crPackId"] for record in pack_records}
    members = {(str(cr).removeprefix("tdoc:"), record["tdoc:crPackId"])
               for record in pack_records for cr in as_list(record.get("hasCR"))}
    cr_records = inputs.graph(staged("cr_extensions.jsonld"))
    parsed_crs = {record["@id"].removeprefix("tdoc:") for record in cr_records}
    links = set()
    for record in cr_records:
        for value in as_list(record.get("belongsToCRPack")):
            links.add((record["@id"].removeprefix("tdoc:"), pack_id.get(value, str(value).rsplit("/", 1)[-1])))
    del pack_records, cr_records
    packs_of = collections.defaultdict(set)
    for number, pack in links:
        packs_of[number].add(pack)

    guard(inputs.floor, f"{wg} 표지 읽기")
    collected = sorted(corpus.dirs[wg])
    for pack in collected:
        corpus.view(wg, pack)
    for pack in sorted({pack for _, pack in links} - set(collected)):
        corpus.view(wg, pack)

    def spec_cr_of(number: str) -> tuple | None:
        document = documents.get(number)
        if document and document["spec"] and document["cr"] is not None:
            return document["spec"], document["cr"]
        return corpus.file_spec_cr.get(number)

    def portal_of(number: str) -> list[dict]:
        return portal.get(number, [])

    # 정확도: E4 짝마다 표지를 본다.
    precision, meeting_precision, not_confirmed_meeting = collections.Counter(), collections.Counter(), collections.Counter()
    absent_elsewhere = collections.Counter()
    reasons, flag_counts, examples = collections.Counter(), collections.Counter(), collections.defaultdict(list)
    for number, pack in sorted(links):
        view = corpus.view(wg, pack)
        document = documents.get(number)
        entry = {"kind": "e4Link", "wg": wg, "number": number, "pack": pack,
                 "packField": document["packField"] if document else None, "copies": view["copies"]}
        if not view["directories"]:
            name = "packDirectoryAbsent"
            # 다른 작업반이 낸 묶음에 이 작업반 CR 이 실리면 그 묶음 폴더는 다른 작업반 CR 수집본에만 있다.
            elsewhere = [other for other in WGS if other != wg and pack in corpus.dirs[other]]
            entry.update(otherWgDirectories=elsewhere,
                         otherWgCoverLists={other: number in corpus.view(other, pack)["listed"] for other in elsewhere})
            absent_elsewhere["listed" if any(entry["otherWgCoverLists"].values()) else
                             "folderWithoutListing" if elsewhere else "noFolder"] += 1
        elif not view["copies"]:
            name = "coverMissing"
            entry["directoryFile"] = number in view["files"]
        elif not view["readable"]:
            name = "coverUnreadable"
        elif not view["tabled"]:
            name = "coverWithoutCrTable"
        elif number in view["listed"]:
            name = "confirmedExactSpelling" if view["listed"][number] else "confirmedAfterSpelling"
            if not view["listed"][number]:
                examples[name].append({**entry, "numberCells": [t for t in view["tdTexts"] if digits_of(number) in t]})
            if view["copiesDiffer"] and not all(number in copy for copy in view["perCopy"]):
                precision["confirmedInSomeCopiesOnly"] += 1
                examples["confirmedInSomeCopiesOnly"].append(entry)
        else:
            name = "notConfirmed"
            flags = flags_against(number, pack, view, spec_cr_of(number), revisions)
            reason = first_reason(flags, REASON_ORDER)
            reasons[reason] += 1
            flag_counts.update(flag for flag, value in flags.items() if value)
            entry.update(flags=flags, reason=reason, specCr=spec_cr_of(number), portal=portal_of(number),
                         **meeting_fields(corpus, number, pack, spec_cr_of(number), revisions))
            not_confirmed_meeting[entry["meeting"]] += 1
            examples[reason].append(entry)
        precision[name] += 1
        if name in ("packDirectoryAbsent", "coverMissing", "coverUnreadable", "coverWithoutCrTable"):
            entry.update(portal=portal_of(number), **meeting_fields(corpus, number, pack, spec_cr_of(number), revisions))
            meeting_precision[(name, entry["meeting"])] += 1
            examples[name].append(entry)
        if name not in ("confirmedExactSpelling", "confirmedAfterSpelling"):
            items.append({**entry, "class": name})
    confirmed = precision["confirmedExactSpelling"] + precision["confirmedAfterSpelling"]
    judged = confirmed + precision["notConfirmed"]
    # CR 수집본 표지로 판정하지 못한 짝 가운데 총회 표지로 판정한 것.
    meeting_confirmed = sum(n for (_, m), n in meeting_precision.items() if m == "coverListsDocument")
    meeting_unconfirmed = sum(n for (_, m), n in meeting_precision.items() if m == "coverDoesNotListDocument")
    record_packs = {pack for _, pack in members}

    # 재현율: 문서 목록만 묶음을 적은 문서.
    recall, recall_reasons = collections.Counter(), collections.Counter()
    by_status, by_type = collections.Counter(), collections.Counter()
    not_collected, scope_meeting = collections.Counter(), collections.Counter()
    meeting_reasons, meeting_fallback = collections.Counter(), collections.Counter()
    portal_status = collections.Counter()
    recall_examples = collections.defaultdict(list)
    missed_flags = collections.Counter()
    definition = collections.Counter()
    for number, document in sorted(documents.items()):
        pack = document["packField"]
        if pack is None or not PACK_NUMBER.fullmatch(pack) or (number, pack) in links:
            continue
        definition["differentPack" if packs_of.get(number) else "documentListOnly"] += 1
        view = corpus.view(wg, pack)
        entry = {"kind": "listFieldOnly", "wg": wg, "number": number, "pack": pack, "status": document["status"],
                 "tdocType": document["tdocType"], "release": document["release"],
                 "linkedTo": sorted(packs_of.get(number, ())), "copies": view["copies"],
                 "portal": portal_of(number)}
        if document["tdocType"] != "CR":
            name = "notAFormalCr"
            entry["crCorpusCoverLists"] = number in view["listed"] if view["tabled"] else None
            entry.update(meeting_fields(corpus, number, pack, spec_cr_of(number), revisions))
            entry["detail"] = str(document["tdocType"])
        elif not view["directories"]:
            name = "packNotCollected"
            elsewhere = [other for other in WGS if other != wg and pack in corpus.dirs[other]]
            zips = corpus.zips.get(pack, [])
            scope = collection_scope(wg, document, cr_lists.get(number, []), pack, spec_lists)
            entry.update(
                scope=scope, otherWgDirectories=elsewhere,
                otherWgCoverLists={other: number in corpus.view(other, pack)["listed"] for other in elsewhere},
                sourceZips={str(path): corpus.zip_lists(path, number) for path in zips},
                **meeting_fields(corpus, number, pack, spec_cr_of(number), revisions))
            detail = "inOtherWgCrCorpus" if elsewhere else "crCorpusSourceZipOnly" if zips else "notInCrCorpus"
            not_collected[(detail, scope["crList"], document["release"] or "none")] += 1
            scope_meeting[(scope["verdict"], entry["meeting"])] += 1
            if entry["meeting"] == "coverDoesNotListDocument":
                meeting_reasons[entry["meetingReason"]] += 1
            if scope["verdict"].startswith("inScope"):
                statuses = sorted({row["tsgStatus"] or "(빈 값)" for row in entry["portal"]
                                   if row["tsgTdoc"] == pack}) or ["portalHasNoRowForThisPack"]
                portal_status[(scope["verdict"], entry["meeting"], "|".join(statuses))] += 1
            entry["detail"] = f"{scope['verdict']}/{entry['meeting']}"
        elif not view["copies"] or not view["readable"] or not view["tabled"]:
            name = ("collectedCoverMissing" if not view["copies"] else "collectedCoverUnreadable"
                    if not view["readable"] else "collectedCoverWithoutCrTable")
            entry["directoryFile"] = number in view["files"]
            entry.update(meeting_fields(corpus, number, pack, spec_cr_of(number), revisions))
            meeting_fallback[(name, entry["meeting"])] += 1
            entry["detail"] = entry["meeting"]
        elif number in view["listed"]:
            name = "coverListsDocument"
            linked_elsewhere = sorted(packs_of.get(number, ()))
            entry.update(
                otherPackCoverLists={other: number in corpus.view(wg, other)["listed"] for other in linked_elsewhere},
                parsedCrRecord=number in parsed_crs, directoryFile=number in view["files"],
                packRecordHasMembers=pack in record_packs)
            if linked_elsewhere:
                key = "linkedToOtherPackWhoseCoverAlsoLists" if any(entry["otherPackCoverLists"].values()) \
                    else "linkedToOtherPackWhoseCoverDoesNotList"
            else:
                key = "noLinkWithParsedCrRecord" if entry["parsedCrRecord"] else "noLinkWithoutParsedCrRecord"
            missed_flags[key] += 1
            entry["detail"] = key
        else:
            name = "coverDoesNotListDocument"
            flags = flags_against(number, pack, view, spec_cr_of(number), revisions)
            entry.update(flags=flags, specCr=spec_cr_of(number))
            reason = first_reason(flags, REASON_ORDER)
            recall_reasons[reason] += 1
            entry["detail"] = reason
        recall[name] += 1
        by_status[(name, document["status"])] += 1
        by_type[(name, document["type"], document["tdocType"])] += 1
        recall_examples[f"{name}/{entry['detail']}"].append(entry)
        items.append({**entry, "class": name})

    # 표지 기준 짝: 수집된 표지가 드는 이 작업반 번호.
    listed_pairs = collections.Counter()
    listed_examples = collections.defaultdict(list)
    foreign = 0
    for pack in collected:
        view = corpus.view(wg, pack)
        for number in sorted(view["listed"]):
            if not number.startswith(PREFIXES[wg]):
                foreign += 1
                continue
            if (number, pack) in links:
                name = "linked"
            elif packs_of.get(number):
                name = "linkedToOtherPack"
            elif number in parsed_crs:
                name = "parsedCrWithoutLink"
            elif number in documents:
                name = "inDocumentListWithoutLink"
            else:
                name = "inNoRecord"
            listed_pairs[name] += 1
            if name != "linked":
                document = documents.get(number)
                entry = {"kind": "coverListed", "wg": wg, "number": number, "pack": pack, "class": name,
                         "linkedTo": sorted(packs_of.get(number, ())),
                         "linkedToCoverLists": {other: number in corpus.view(wg, other)["listed"]
                                                for other in sorted(packs_of.get(number, ()))},
                         "packField": document["packField"] if document else None,
                         "status": document["status"] if document else None,
                         "tdocType": document["tdocType"] if document else None, "portal": portal_of(number)}
                listed_examples[name].append(entry)
                items.append(entry)
    listed_total = sum(listed_pairs.values())
    missed = recall["coverListsDocument"]
    meeting_listed = sum(n for (verdict, meeting), n in scope_meeting.items() if meeting == "coverListsDocument")
    meeting_listed_in_scope = sum(n for (verdict, meeting), n in scope_meeting.items()
                                  if meeting == "coverListsDocument" and verdict.startswith("inScope"))
    fallback_listed = sum(n for (_, meeting), n in meeting_fallback.items() if meeting == "coverListsDocument")

    def estimate(found: int, added: int, statement: str, excluded: dict) -> dict:
        numerator = confirmed + found
        denominator = numerator + added
        return {"numerator": numerator, "denominator": denominator,
                "value": round(numerator / denominator, 6) if denominator else None,
                "denominatorIs": statement, "excluded": excluded}

    covers = [Path(path) for pack in collected for path in corpus.view(wg, pack)["copies"]]
    signatures = collections.Counter(header for path in covers if corpus.cover(path)["readable"]
                                     for header in corpus.cover(path)["headers"])
    unjudged = recall["packNotCollected"] + recall["collectedCoverMissing"] + recall["collectedCoverUnreadable"] \
        + recall["collectedCoverWithoutCrTable"]
    return {
        "wg": wg,
        "links": {"unit": "(CR, 묶음) 짝. CR 쪽 belongsToCRPack 기준", "n": len(links), "hasCrPairs": len(members),
                  "onlyBelongsToCrPack": len(links - members), "onlyHasCr": len(members - links),
                  "crsWithMoreThanOnePack": sum(len(v) > 1 for v in packs_of.values())},
        "corpus": {"unit": "묶음 폴더·표지 파일",
                   "packDirectories": sum(len(v) for v in corpus.dirs[wg].values()), "packsCollected": len(collected),
                   "coverFiles": len(covers), "packsWithoutCover": sum(not corpus.view(wg, p)["copies"] for p in collected),
                   "unreadableCoverFiles": sum(not corpus.cover(p)["readable"] for p in covers),
                   "coverFilesWithoutCrTable": sum(corpus.cover(p)["readable"] and not corpus.cover(p)["headers"]
                                                   for p in covers),
                   "packsWhoseCopiesListDifferentNumbers": sum(corpus.view(wg, p)["copiesDiffer"] for p in collected),
                   "collectedPacksWithoutPackRecord": len(set(collected) - record_packs),
                   "packRecordsWithoutCollectedPack": len(record_packs - set(collected)),
                   "headerSignatures": dict(signatures.most_common())},
        "docReaderCheck": doc_reader_check(wg, corpus),
        "precision": {
            "unit": "E4 짝. CR 수집본 표지의 CR 행 문서 번호 칸에 CR 번호가 있으면 확인",
            "links": len(links), "confirmed": confirmed, **{k: precision[k] for k in (
                "confirmedExactSpelling", "confirmedAfterSpelling", "confirmedInSomeCopiesOnly", "notConfirmed",
                "coverMissing", "coverUnreadable", "coverWithoutCrTable", "packDirectoryAbsent")},
            "notConfirmedReason": {name: reasons[name] for name in REASON_ORDER},
            "notConfirmedFlags": {name: flag_counts[name] for name in REASON_ORDER[:-1]},
            "rate": {"numerator": confirmed, "denominator": judged, "value": round(confirmed / judged, 6) if judged else None,
                     "denominatorIs": "CR 수집본 표지를 읽어 CR 표가 나온 묶음의 E4 짝"},
            "excluded": {"coverMissing": precision["coverMissing"], "coverUnreadable": precision["coverUnreadable"],
                         "coverWithoutCrTable": precision["coverWithoutCrTable"],
                         "packDirectoryAbsent": precision["packDirectoryAbsent"]},
            "packDirectoryAbsentCheckedAgainstOtherWgCover": {
                name: absent_elsewhere[name] for name in ("listed", "folderWithoutListing", "noFolder")},
            "excludedCheckedAgainstMeetingCover": [{"class": c, "meeting": m, "n": n}
                                                   for (c, m), n in sorted(meeting_precision.items())],
            "rateWithMeetingCoverForExcluded": {
                "numerator": confirmed + meeting_confirmed,
                "denominator": judged + meeting_confirmed + meeting_unconfirmed,
                "value": round((confirmed + meeting_confirmed) / (judged + meeting_confirmed + meeting_unconfirmed), 6)
                if judged + meeting_confirmed + meeting_unconfirmed else None,
                "denominatorIs": "위 분모 + CR 수집본 표지로 판정하지 못하고 총회 표지의 CR 표로 판정한 짝"},
            "notConfirmedByMeetingCover": dict(sorted(not_confirmed_meeting.items())),
            "examples": {name: sample(entries, f"{wg}/precision/{name}") for name, entries in sorted(examples.items())}},
        "recall": {
            "unit": "문서. tdoc:tsgCRPack 이 RP-숫자 하나를 적었는데 (문서, 그 묶음) E4 짝이 없는 문서",
            "set": sum(recall.values()), "documentListOnly": definition["documentListOnly"],
            "differentPack": definition["differentPack"], "reported": reported.get(wg),
            "classes": {name: recall[name] for name in (
                "notAFormalCr", "packNotCollected", "collectedCoverMissing", "collectedCoverUnreadable",
                "collectedCoverWithoutCrTable", "coverListsDocument", "coverDoesNotListDocument")},
            "packNotCollectedDetail": [{"crCorpus": w, "crList": c, "release": r, "n": n}
                                       for (w, c, r), n in sorted(not_collected.items())],
            "packNotCollectedByScopeAndMeetingCover": [
                {"scope": s, "meeting": m, "n": n} for (s, m), n in
                sorted(scope_meeting.items(), key=lambda kv: (SCOPE_ORDER.index(kv[0][0]), MEETING_ORDER.index(kv[0][1])))],
            "packNotCollectedMeetingCoverDoesNotListReason": {name: meeting_reasons[name] for name in REASON_ORDER},
            "packNotCollectedInScopePortalTsgStatus": [
                {"scope": s, "meeting": m, "portalTsgStatusForThisPack": p, "n": n}
                for (s, m, p), n in sorted(portal_status.items())],
            "collectedCoverNotJudgedMeetingCover": [{"class": c, "meeting": m, "n": n}
                                                    for (c, m), n in sorted(meeting_fallback.items())],
            "coverListsDocumentDetail": dict(sorted(missed_flags.items())),
            "coverDoesNotListDocumentReason": {name: recall_reasons[name] for name in REASON_ORDER},
            "byStatus": [{"class": c, "status": s, "n": n} for (c, s), n in sorted(by_status.items(), key=str)],
            "byType": [{"class": c, "type": t, "tdocType": d, "n": n} for (c, t, d), n in sorted(by_type.items(), key=str)],
            "excluded": {"tsgCRPackNotSingleRpNumber": "tdoc:tsgCRPack 이 없거나 RP-숫자 하나와 꼭 맞지 않는 문서는 넣지 않는다"},
            "examples": {name: sample(entries, f"{wg}/recall/{name}") for name, entries in sorted(recall_examples.items())}},
        "recallEstimate": estimate(
            0, missed, "CR 수집본 표지로 확인된 E4 짝 + 문서 목록이 묶음을 적었고 CR 수집본의 그 묶음 표지도 문서를 드는데 "
                       "E4 짝이 없는 문서",
            {"listFieldOnlyNotJudgedByCrCorpusCover": unjudged,
             "note": "묶음이 CR 수집본에 없거나 그 표지를 읽지 못한 문서는 CR 수집본 표지로 판정할 수 없어 분모에 넣지 않는다. "
                     "CR 이 아닌 문서(notAFormalCr)도 넣지 않는다"}),
        "recallEstimateWithMeetingCovers": estimate(
            meeting_confirmed, missed + meeting_listed + fallback_listed,
            "위 분모 + CR 수집본 표지로 판정하지 못한 E4 짝 가운데 총회 표지로 확인된 짝 + CR 수집본에 없는 묶음과 CR 수집본 "
            "표지로 판정하지 못한 묶음 가운데 총회 회의 문서의 표지가 문서를 드는 문서",
            {"listFieldOnlyNotJudgedByAnyCover": unjudged - meeting_listed - fallback_listed
             - sum(n for (_, m), n in scope_meeting.items() if m == "coverDoesNotListDocument")
             - sum(n for (_, m), n in meeting_fallback.items() if m == "coverDoesNotListDocument"),
             "note": "E4 는 CR 수집본만 입력으로 쓰므로, 이 값은 수집 범위 밖 묶음까지 포함한 표지 기록에 대한 E4 의 범위를 잰다"}),
        "recallEstimateWithMeetingCoversInDeclaredScope": estimate(
            meeting_confirmed, missed + meeting_listed_in_scope + fallback_listed,
            "첫 분모 + CR 수집본 표지로 판정하지 못한 E4 짝 가운데 총회 표지로 확인된 짝 + CR 수집본 표지로 판정하지 못한 "
            "묶음에서 총회 표지가 드는 문서 + CR 수집본에 없는 묶음의 문서 가운데 이 작업반 TS 목록·Rel-15~Rel-20 안이고 "
            "총회 표지가 문서를 드는 문서",
            {"meetingCoverListedOutsideDeclaredScope": meeting_listed - meeting_listed_in_scope}),
        "coverListedPairs": {
            "unit": "(문서 번호, 묶음) 짝. 이 작업반 폴더의 표지가 이 묶음 행의 문서 번호 칸에 든 이 작업반 접두 번호",
            "n": listed_total, **{name: listed_pairs[name] for name in (
                "linked", "linkedToOtherPack", "parsedCrWithoutLink", "inDocumentListWithoutLink", "inNoRecord")},
            "rate": {"numerator": listed_pairs["linked"], "denominator": listed_total,
                     "value": round(listed_pairs["linked"] / listed_total, 6) if listed_total else None},
            "rateExcludingLinkedToOtherPack": {
                "numerator": listed_pairs["linked"], "denominator": listed_total - listed_pairs["linkedToOtherPack"],
                "value": round(listed_pairs["linked"] / (listed_total - listed_pairs["linkedToOtherPack"]), 6)
                if listed_total - listed_pairs["linkedToOtherPack"] else None,
                "why": "belongsToCRPack 은 CR 마다 묶음 하나만 적으므로 두 묶음 표지에 든 CR 은 한 짝만 남는다"},
            "excluded": {"otherWgNumbers": foreign},
            "examples": {name: sample(entries, f"{wg}/listed/{name}") for name, entries in sorted(listed_examples.items())}},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--wg", nargs="+", choices=WGS, required=True)
    parser.add_argument("--phase4-root", type=Path, help="phase-4 묶음 기록을 따로 둔 폴더(<root>/<WG>/crpacks.jsonld)")
    parser.add_argument("--manifest", type=Path, help="입력 SHA-256 을 맞대어 볼 export_manifest.json")
    parser.add_argument("--agreement", type=Path, nargs="*", default=[],
                        help="같은 집합의 크기를 맞대어 볼 measure_pack_source_agreement.py 출력")
    parser.add_argument("--min-available-gib", type=float, default=8.0,
                        help="이 아래면 멈춘다. 저장소 작업 지침이 정한 하한이다")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--items", type=Path, required=True, help="확인되지 않은 짝과 분류한 문서를 한 줄씩 적는 jsonl")
    args = parser.parse_args()
    manifest = {}
    if args.manifest:
        for export in json.loads(args.manifest.read_text())["exports"].values():
            manifest.update({item["path"]: item["sha256"] for item in export["inputs"]})
    reported = {}
    for path in args.agreement:
        for row in json.loads(path.read_text())["byWg"]:
            reported[row["wg"]] = {"documentListOnly": row["documentListOnly"], "differentPack": row["differentPack"],
                                   "from": str(path)}
    inputs = Inputs(args.min_available_gib, manifest)
    guard(args.min_available_gib, "묶음 폴더 색인")
    corpus, cr_lists = Corpus(args.min_available_gib), read_cr_lists()
    portal, spec_lists = read_portal(inputs), read_spec_scope(inputs)
    items: list[dict] = []
    by_wg = [audit(wg, corpus, inputs, args.phase4_root, cr_lists, portal, spec_lists, reported, items) for wg in args.wg]
    total = collections.Counter()
    for row in by_wg:
        total.update({"links": row["links"]["n"], "confirmed": row["precision"]["confirmed"],
                      "judged": row["precision"]["rate"]["denominator"], "recallSet": row["recall"]["set"],
                      "coverListsDocument": row["recall"]["classes"]["coverListsDocument"]})
        # 세 추정은 분자가 서로 다르다(총회 표지로 확인한 짝을 분자에도 넣는다). 그래서 분자도 추정마다 따로 더한다.
        for name in ESTIMATES:
            total.update({f"{name}Numerator": row[name]["numerator"], f"{name}Denominator": row[name]["denominator"]})

    def ratio(numerator: str, denominator: str):
        return round(total[numerator] / total[denominator], 6) if total[denominator] else None

    meeting_packs = collections.Counter(len(paths) for paths in corpus.meeting_zips.values())
    report = {
        "unit": "작업반마다 따로 센다. total 은 고른 작업반의 합이다",
        "method": {
            "evidence": "묶음 표지 파일을 직접 연다. 빌드 코드와 빌드가 남긴 표지 해석 결과는 쓰지 않는다",
            "census": "표본 없이 모든 E4 짝과 모든 해당 문서를 본다",
            "coverSources": {"crCorpus": str(CORPUS), "meetings": str(MEETINGS),
                             "meetingCoverName": COVER_NAME, "doc": "Word 97 본문 글을 직접 읽는다(word_text · doc_tables)",
                             "docReaderCheck": "byWg[].docReaderCheck 가 CR 수집본의 .doc · docx 표지 쌍으로 이 읽기를 맞대어 본다"},
            "collectionScope": {"specList": f"{SPEC_SCOPE} 의 <WG>.TS", "releases": f"Rel-{RELEASES.start}~Rel-{RELEASES.stop - 1}",
                                "crList": "change-requests/*/source/Rel-*/metadata/cr_list.csv", "order": list(SCOPE_ORDER)},
            "portal": f"{PORTAL}. 38 · 37 계열 Rel-15 이후 CR 만 있어 그 밖의 문서는 빈 목록이다",
            "zipIndex": {"crCorpusSource": dict(corpus.zip_spelling), "meetings": dict(corpus.meeting_spelling),
                         "meetingPacksByZipCount": dict(sorted(meeting_packs.items()))},
            "numberHeader": sorted(TD_HEADER), "roleHeaders": {k: sorted(v) for k, v in ROLE_HEADERS.items()},
            "reasonOrder": list(REASON_ORDER), "meetingOrder": list(MEETING_ORDER),
            "examplesPerClass": EXAMPLES},
        "inputs": inputs.read,
        "total": dict(total) | {"precision": ratio("confirmed", "judged")}
                 | {name: ratio(f"{name}Numerator", f"{name}Denominator") for name in ESTIMATES},
        "byWg": by_wg,
    }
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=sorted) + "\n")
    with args.items.open("w") as handle:
        for item in items:
            handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True, default=sorted) + "\n")
    for row in by_wg:
        p, r, d = row["precision"], row["recall"], row["docReaderCheck"]
        print(row["wg"], "links", p["links"], "confirmed", p["confirmed"], "notConfirmed", p["notConfirmed"],
              "excluded", p["excluded"], "| docReader", d["compared"], d["sameNumbers"], d["differentNumbers"],
              d["docUnreadable"], "| recallSet", r["set"], r["classes"], "| estimate",
              row["recallEstimate"]["numerator"], "/", row["recallEstimate"]["denominator"],
              "| withMeeting", row["recallEstimateWithMeetingCovers"]["denominator"],
              "| inScope", row["recallEstimateWithMeetingCoversInDeclaredScope"]["denominator"])


if __name__ == "__main__":
    main()
