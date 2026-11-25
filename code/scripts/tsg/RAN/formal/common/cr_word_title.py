#!/usr/bin/env python3
"""cr_word_title.py: LibreOffice 로 바꾼 CR 의 표지 Title 칸을 원본 .doc 이 보여 주는 글로 읽는다.

> 주의: 표지 Title 칸에 `DOCPROPERTY "CrTitle"` 필드를 둔 CR 서식이 있다. 원본 Word 는 필드 결과를 비워 둔 채
> 앞 글(`Update NR SIB1`)만 보여 주는데, LibreOffice 는 변환할 때 결과를 문서 속성 값으로 다시 계산해 써서
> 서식 틀에 남은 낡은 제목이 붙는다(RAN5 `R5-195322` 는 `Update NR SIB1Introduction of TC 7.9A.1 …`). `doc_fields`
> 의 변환 복원은 Word 결과가 빈 필드를 되돌리지 않으므로 이 잔재가 양식 제목에 남는다. 필드가 겹친 칸은 바깥
> 결과 안에 안쪽 필드가 들어 있어 첫 글자만 남기도 한다(`R5-200647` 은 `C`). 그래서 같은 이름의 원본 .doc 이 있는
> LibreOffice 변환본은 .doc 본문 이야기에서 필드 명령문을 걷어 낸 Title 칸 글을 따로 읽는다.
>
> 주의: 원본 글이 양식 제목과 영숫자로 같으면 양식 제목을 그대로 쓴다. 원본 글은 공백을 하나로 접으므로, 공백만
> 다른 경우까지 바꾸면 TDoc 목록 제목과 글자로 맞던 제목이 어긋난다.
>
> 주의: Work item code 칸에도 `DOCPROPERTY "RelatedWis"` 필드를 둔 서식이 있어 같은 잔재가 붙는다(RAN5 `R5-192002`
> 는 `5GS_NR_LTE-UEConTest 5GS_NR_LTE-UEConTest`, `R5s190086` 은 원본이 보여 주지 않는 `NB_IOT-UEConTest` 가 앞에
> 붙는다). 작업 항목은 그 칸의 원본 필드 결과가 비었을 때만 원본 글로 바꾼다. .doc 이야기는 변경 추적으로 지운 글도
> 담고 있어서(`R4-2108257` 원본 글 `NR_HST-coreCore`), 빈 결과 필드가 없는 칸까지 원본 글을 쓰면 맞던 값이 틀어진다.
>
> 주의: 필드가 겹친 Work item code 칸도 원본 글로 바꾼다. 바깥 필드 결과가 안쪽 필드 끝 표지 뒤에 이어지는 칸은
> 변환본에서 그 뒤 글자가 빠진다(RAN5 `R5-205899` 는 원본 `TEI14_Test, LTE_V2X-UEConTest` 가 `…UEConTes` 로 남는다).
"""
from __future__ import annotations

import re
import struct
import os
from functools import lru_cache

import cr_form
import doc_fields

_SPACE = {"\x0b": " ", "\r": " ", "\n": " ", "\t": " ", "\x1e": "-", "\x1f": "", "\xa0": " ", "\x0c": " "}
_CONTROL = re.compile(r"[\x00-\x06\x08\x0e-\x1d﷐]")
# 표지는 본문 앞머리에 있다. 본문 전체를 걸러 내지 않도록 Title 칸을 찾는 범위를 앞머리로 둔다.
_HEAD = 60000


def _shown(s: str) -> str:
    """필드 명령문을 걷어 내고(겹친 필드 포함) 결과만 남긴다. 칸 끝 표지(\\x07)는 칸을 나누려고 남긴다."""
    out, stack = [], []
    for ch in s:
        if ch == "\x13":
            stack.append(False)
        elif ch == "\x14":
            if stack:
                stack[-1] = True
        elif ch == "\x15":
            if stack:
                stack.pop()
        elif all(stack):
            out.append(ch)
    return "".join(out)


def _clean(s: str) -> str:
    s = "".join(_SPACE.get(c, c) for c in s)
    return " ".join(_CONTROL.sub("", s).split())


def _key(s: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


@lru_cache(maxsize=4)
def _cached_head(doc_path: str, identity: tuple) -> str | None:
    try:
        with open(doc_path, "rb") as f:
            stories, _ = doc_fields._doc_read(f.read(), False)
    except (doc_fields.DocError, struct.error, OSError, IndexError, ValueError):
        return None
    return stories[0][:_HEAD]


def _head(doc_path: str) -> str | None:
    """한 원본의 제목·작업 항목을 함께 캐시하고, 원본 교체 후에는 다시 읽는다."""
    try:
        stat = os.stat(doc_path)
    except OSError:
        return None
    identity = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
    return _cached_head(doc_path, identity)


def doc_title(doc_path: str) -> str | None:
    """원본 .doc 표지의 Title 칸 다음 칸 글. 읽지 못하거나 Title 칸이 없으면 None."""
    head = _head(doc_path)
    if head is None:
        return None
    cells = _shown(head).split("\x07")
    for i, cell in enumerate(cells[:-1]):
        if re.sub(r"[^a-z]", "", _clean(cell).lower()) == "title":
            return _clean(cells[i + 1]) or None
    return None


def form_title(title: str, docx_path) -> str:
    """양식에서 읽은 제목을 원본 .doc 이 보여 주는 제목으로 바로잡는다. 변환본이 아니거나 양식 제목이 비었으면
    받은 제목 그대로다(제목이 빈 문서는 따로 견주어 보지 않았다)."""
    if not title:
        return title
    doc_path = doc_fields.lo_source(docx_path)
    if doc_path is None:
        return title
    shown = doc_title(doc_path)
    if shown is None or _key(shown) == _key(title):
        return title
    return shown


#: Word 결과가 비었거나 공백뿐인 필드(`\x13 명령문 \x14\x15`, 구분 표지 없는 `\x13 명령문 \x15`).
_BLANK_FIELD = re.compile(r"\x13[^\x13\x14\x15]*(?:\x14\s*)?\x15")


def _nested(s: str) -> bool:
    """필드 안에 다른 필드가 들어 있는가."""
    depth = 0
    for ch in s:
        if ch == "\x13":
            depth += 1
            if depth > 1:
                return True
        elif ch == "\x15" and depth:
            depth -= 1
    return False


def doc_cell(doc_path: str, label: str) -> tuple[str, bool] | None:
    """원본 .doc 표지에서 이름 칸이 `label`(영문자만 남긴 소문자)인 칸 다음 칸의 (보이는 글, 변환본이 원본과 다른 글을
    낼 수 있는 칸인가: 빈 결과 필드나 겹친 필드가 있다). 읽지 못하거나 이름 칸이 없으면 None."""
    head = _head(doc_path)
    if head is None:
        return None
    cells = head.split("\x07")
    for i, cell in enumerate(cells[:-1]):
        if re.sub(r"[^a-z]", "", _clean(_shown(cell)).lower()) == label:
            return _clean(_shown(cells[i + 1])), bool(_BLANK_FIELD.search(cells[i + 1])) or _nested(cells[i + 1])
    return None


def form_work_item(work_item: str | None, docx_path) -> str | None:
    """양식에서 읽은 작업 항목을, 원본 .doc 의 Work item code 칸에 Word 결과가 빈 필드나 겹친 필드가 있을 때만 원본이 보여 주는
    글로 바로잡는다. 원본 글도 양식 칸 값과 같이 서식 자리표시를 뗀다(`cr_form._field_value`)."""
    if not work_item:
        return work_item
    doc_path = doc_fields.lo_source(docx_path)
    if doc_path is None:
        return work_item
    hit = doc_cell(doc_path, "workitemcode")
    if hit is None or not hit[1]:
        return work_item
    shown = cr_form._field_value("work_item", hit[0])
    if _key(shown) == _key(work_item):
        return work_item
    return shown
