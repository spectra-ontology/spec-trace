"""docx_pick.py — 한 폴더 안 여러 docx 가운데 표지와, 정리판 짝이 있는 수정 표시판을 본문 후보에서 빼는 규칙.

TS · TR · CR 묶음은 본문 docx 곁에 표지 한 쪽(`R4-1816258 … Cover page.docx` · `RP-182887 Cover.docx` ·
`RP-190747 …_Cover_draft.docx` · `38101-1-j40_cover.docx`)을 함께 싣는다. 표지 이름에도 spec 번호 · Tdoc 번호가
들어가므로, 이름 차례나 「마지막 판」 같은 선택 규칙만으로는 표지가 본문 대신 뽑힐 수 있다. 표지는 "첨부를 보라"는
한 쪽이고 그 묶음이 가리키는 내용은 본문이다.

표지 이름 문법(`COVER_NAME`)은 Phase-6 Tdoc 파서가 표지를 본문 뒤로 미는 규칙과 같다. 낱말 `cover` 와 그 뒤의
`page` · `sheet` · `letter` · `note` 를 받고, 앞뒤가 영문자인 `coverage` · `covering` · `discovery` · `recovery` 는
받지 않는다. 이름 판정은 파일 이름(디렉토리를 뺀 끝 이름)만 본다.

이 문법은 진짜 CR 본문 이름(`… evolution cover RAN4#110bis.docx` 처럼 제목에 낱말 cover 가 든 것)에도 맞는다.
그래서 `prefer_body` 는 표지를 빼고 하나도 남지 않으면 원래 목록을 그대로 돌려준다 — 본문 후보를 없애지 않는다.
여러 파일이 섞인 묶음 전체에 한 번에 걸지 말고, 같은 본문을 두고 다투는 후보끼리(한 폴더 · 한 팩)에 건다.

같은 판을 수정 표시판(`rm`, 변경 추적이 든 판)과 정리판(`cl`)으로 함께 싣는 폴더도 있다(`38.475-030 rm.docx` ·
`38.475-030 cl.docx`, `38760-1-010_rm.docx` · `38760-1-010_cl.docx`). 이름 차례로는 `rm` 이 뒤에 와서 「마지막 판」
규칙이 수정 표시판을 고른다. 수정 표시판은 지운 글을 `w:del` 로 품고 있어 읽는 쪽에 따라 지운 글이 섞이거나
넣은 글이 빠진다. 그래서 `prefer_body` 는 이름 끝 낱말만 `rm` ↔ `cl` 로 다른 정리판이 후보에 있으면 수정 표시판을
뺀다. 짝이 없는 `rm` 판은 그대로 둔다.

한 문서를 같은 이름으로 `.doc` 와 `.docx` 두 형식에 담아 보낸 zip 도 있다. 그 쌍은 `drop_shipped_twins` 가
글이 많은 판 하나로 줄인다. 이 규칙만 이름이 아니라 내용(본문 글자 수)을 본다.
"""
from __future__ import annotations

import os
import re
import zipfile
from collections.abc import Iterable
from typing import TypeVar

#: 묶음의 표지 문서 이름. `coverage` · `covering` · `discovery` · `recovery` 는 아니다.
COVER_NAME = re.compile(r"(?<![a-z])cover(?:[ _-]?(?:page|sheet|letter|note))?(?![a-z])", re.I)

#: 이름 끝(확장자 앞)의 수정 표시판 · 정리판 낱말. 앞은 공백 · `_` · `-` 다.
_EDITION = re.compile(r"(?<=[ _-])(rm|cl)$", re.I)

#: 배포 `X.docx` 곁에서 배포 `X.doc` 의 변환본이 받는 이름 끝(Phase-0 변환기 `conversion_target`).
SHIPPED_TWIN_SUFFIX = ".doc.docx"

#: 본문 XML 의 글 조각(`w:t`). `w:tbl` · `w:tab` · 지운 글 `w:delText` 는 맞지 않는다.
_W_T = re.compile(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>")

P = TypeVar("P", str, os.PathLike)


def is_cover(path_or_stem: str | os.PathLike) -> bool:
    """파일 이름(디렉토리를 뺀 끝 이름)이 표지 이름인가."""
    return COVER_NAME.search(os.path.basename(os.fspath(path_or_stem))) is not None


def _clean_twin(path: str | os.PathLike) -> str | None:
    """수정 표시판(`… rm.docx`)이면 짝이 될 정리판의 끝 이름(`… cl.docx`), 아니면 None."""
    stem, ext = os.path.splitext(os.path.basename(os.fspath(path)))
    m = _EDITION.search(stem)
    if m is None or m.group(1).lower() != "rm":
        return None
    return (stem[:m.start()] + "cl" + ext).lower()


def drop_covers(paths: Iterable[P]) -> list[P]:
    """표지가 아닌 후보만, 들어온 순서대로. 모두 표지면 원래 목록 전부(본문 후보를 없애지 않는다).

    CR 묶음은 이것만 쓴다. CR 에서는 수정 표시판이 바뀐 내용 자체라 정리판을 앞세우면 안 된다.
    """
    paths = list(paths)
    return [p for p in paths if not is_cover(p)] or paths


def text_chars(path: str | os.PathLike) -> int:
    """docx 본문(`word/document.xml`)의 글자 수. 지운 글은 세지 않는다. 열리지 않으면 -1."""
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8", "replace")
    except (OSError, KeyError, zipfile.BadZipFile):
        return -1
    return sum(len(t) for t in _W_T.findall(xml))


def drop_shipped_twins(paths: Iterable[P]) -> list[P]:
    """같은 폴더에 배포 `X.docx` 와 배포 `X.doc` 의 변환본 `X.doc.docx` 가 함께 있으면 글이 많은 쪽만 남긴다.

    순서는 그대로다. 글자 수가 같으면 배포 `.docx` 를 남긴다(변환을 거치지 않은 바이트다).

    Phase-0 변환기는 배포 `X.docx` 를 덮지 않으려고 같은 zip 의 `X.doc` 변환본을 `X.doc.docx` 로 적는다. 두 파일은
    한 문서의 두 판이라 둘 다 읽으면 같은 글이 두 번 들어간다. 이름 차례(`X` < `X.doc`)로 하나를 고르면 판의
    내용과 무관하게 언제나 `.docx` 가 뽑힌다.

    주의: 두 판이 같다고 볼 수 없다. RAN5 meetings 의 이런 쌍 11 곳(R5-195901~195906 · R5-195931 · R5-195932 ·
    R5-195934 · R5-195935 · R5-201325)은 모두 배포 `.docx` 가 글 1,235~1,346 자의 빈 CR 양식(문단 107 · 표 3)이고
    `.doc` 이 6,394~97,486 자의 채운 CR 이다. 이름 차례로 고르면 이 11 CR 은 빈 양식만 읽혀 바꾸는 이유와 바뀐
    절이 통째로 빠진다. 다른 쌍(CR 슬롯 R5-252974 의 `38.533 12.4.1.1 TT`)은 두 판이 23,698 · 23,707 자로 같은 문서다.

    주의: 배포되지 않은 `X.docx`(옛 변환본) 곁에는 지금 변환기가 `X.doc.docx` 를 만들지 않는다. 그런 쌍은 옛 규칙이
    남긴 중복 변환본이므로 이 함수로 고를 일이 아니라 코퍼스에서 지운다.
    """
    paths = list(paths)
    by_name = {(os.path.dirname(os.fspath(p)), os.path.basename(os.fspath(p)).lower()): p for p in paths}
    drop = set()
    for (folder, name), conv in by_name.items():
        if not name.endswith(SHIPPED_TWIN_SUFFIX):
            continue
        shipped = by_name.get((folder, name[:-len(SHIPPED_TWIN_SUFFIX)] + ".docx"))
        if shipped is not None:
            drop.add(conv if text_chars(shipped) >= text_chars(conv) else shipped)
    return [p for p in paths if p not in drop]


def prefer_body(paths: Iterable[P]) -> list[P]:
    """TS · TR 본문 후보: 표지를 뺀 뒤(`drop_covers`) 정리판 짝이 후보에 있는 수정 표시판을 뺀다. 순서는 그대로다."""
    body = drop_covers(paths)
    names = {os.path.basename(os.fspath(p)).lower() for p in body}
    return [p for p in body if _clean_twin(p) not in names]
