#!/usr/bin/env python3
"""archive_head.py — 파일 앞부분의 바이트로 압축 형식을 판별한다.

3GPP의 `.zip` 파일에는 ZIP 외에 RAR·7z 형식, 빈 파일, 오류 응답이 섞일 수 있다.
수집기와 추출기는 이 공통 판별기를 사용해 파일 형식을 같은 기준으로 확인한다.

반환하는 형식
-------------
    empty  : 0바이트
    zip    : ZIP 머리(`PK` 03 04 · 빈 ZIP 의 끝 기록 `PK` 05 06 · 분할 표지 `PK00` 뒤의
             `PK` 03 04), 또는 머리는 다르지만 zipfile 이 끝 기록을 찾는 파일(앞에 다른
             바이트가 붙은 ZIP)
    7z     : 7z 서명
    rar    : RAR 서명(`rar_archive.RAR_MAGIC`)
    markup : HTML · XML 문서 — 서버가 파일 대신 돌려준 웹 응답
    other  : 위 어느 것도 아님 — 암호화 머리, 걸러 낸 문구, 알 수 없는 바이트

`expects_archive`는 확장자가 `.zip`인지 확인한다(대소문자 무관).
HTML 자체가 정상 자료인 경우도 있으므로 호출자는 압축 파일로 기대한 자료에만
`download_failure`를 적용한다.

형식 판별은 파일 내용의 무결성 검사와 구분한다. 호출자는 ZIP CRC·`7z t`·libarchive
등으로 내용을 별도 검사한다. 이 모듈은 파일을 읽고 형식과 실패 사유만 반환한다.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import rar_archive

#: 지역 파일 머리, 항목 0개 ZIP 의 끝 기록, 분할 표지 뒤의 지역 파일 머리.
ZIP_HEADS = (b"PK\x03\x04", b"PK\x05\x06", b"PK00PK\x03\x04")
SEVEN_Z_MAGIC = b"7z\xbc\xaf\x27\x1c"
RAR_MAGIC = rar_archive.RAR_MAGIC

#: 웹 응답으로 읽는 머리. 앞의 BOM 과 공백을 걷어 낸 뒤 소문자로 비교한다.
_MARKUP_HEADS = (b"<!doctype html", b"<html", b"<?xml", b"<head", b"<body", b"<!--")
_HEAD_LEN = 512

KINDS = ("empty", "zip", "7z", "rar", "markup", "other")


def classify_head(head: bytes) -> str:
    """앞부분 바이트로 형식을 판별한다. 서명 앞에 다른 바이트가 붙은 ZIP은 `other`다."""
    if not head:
        return "empty"
    if head.startswith(ZIP_HEADS):
        return "zip"
    if head.startswith(SEVEN_Z_MAGIC):
        return "7z"
    if head.startswith(RAR_MAGIC):
        return "rar"
    if head.lstrip(b"\xef\xbb\xbf \t\r\n").lower().startswith(_MARKUP_HEADS):
        return "markup"
    return "other"


def read_head(path: Path) -> bytes:
    """앞 `_HEAD_LEN` 바이트. 읽지 못하면 OSError 를 그대로 올린다."""
    with open(path, "rb") as fh:
        return fh.read(_HEAD_LEN)


def sniff(path: Path) -> str:
    """파일 형식을 반환한다. 앞부분으로 식별하지 못한 ZIP은 끝 기록도 확인한다.

    파일 읽기 실패는 OSError로 전달한다.
    """
    kind = classify_head(read_head(path))
    if kind == "other" and zipfile.is_zipfile(path):
        return "zip"
    return kind


def expects_archive(path: Path) -> bool:
    """확장자가 `.zip`이면 True를 반환한다(대소문자 무관)."""
    return Path(path).suffix.lower() == ".zip"


def head_hex(path: Path, n: int = 4) -> str:
    """사유 문구에 붙일 앞 `n` 바이트의 16진 표기. 읽지 못하면 빈 문자열."""
    try:
        return read_head(path)[:n].hex()
    except OSError:
        return ""


def rar_readable(path: Path) -> bool | None:
    """libarchive로 RAR를 끝까지 읽어 검사한다. 라이브러리가 없으면 None을 반환한다.

    호출자는 None을 파일 손상과 구분해야 한다. 라이브러리가 준비된 경우에만
    `rar_archive.reads`의 내용 검사 결과를 반환한다.
    """
    try:
        import libarchive  # noqa: F401
    except (ImportError, OSError):
        return None
    return rar_archive.reads(path)


def download_failure(kind: str, path: Path) -> str | None:
    """압축 파일의 형식이 empty·markup·other이면 실패 사유를, 그 외에는 None을 반환한다.

    None은 형식 검사 통과를 뜻한다. 내용의 무결성 확인과 재수집 여부는 호출자가 처리한다.
    """
    if kind == "empty":
        return "빈 파일(0바이트)"
    if kind == "markup":
        return "아카이브 대신 웹 응답(HTML·XML)"
    if kind == "other":
        return f"ZIP·7z·RAR 서명 없음(머리 {head_hex(path)})"
    return None
