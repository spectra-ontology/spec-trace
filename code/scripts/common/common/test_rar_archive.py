#!/usr/bin/env python3
"""test_rar_archive.py — `rar_archive` 의 거절 규칙을 시험한다.

이 저장소에는 RAR 를 만드는 도구가 없어 정상 RAR 를 합성하지 못한다. 그래서 여기서는
RAR 서명이 아닌 파일(zip 포함), 서명 뒤가 망가진 파일, 목적지 밖으로 나가는 항목 이름을
거절하는지 본다. 해독을 가짜로 바꾼 시험은 실제 임시 폴더에서 교체 성공, 이동 실패와
복원 실패를 검사한다. libarchive 부재를 강제하고 외부 호출을 차단하여 합성 파일로 실행한다.
합성 항목 스트림으로 정상 파일 바이트와 읽기·추출의 경로 충돌 판정을 함께 검사한다.

사용:
    python3 scripts/common/common/test_rar_archive.py
"""
from __future__ import annotations

import builtins
import contextlib
import socket
import subprocess
import sys
import tempfile
import types
import zipfile
from pathlib import Path, PurePosixPath
from unittest import mock

with mock.patch.object(sys, "path", [str(Path(__file__).resolve().parent), *sys.path]):
    import rar_archive


def check(cond: bool, what: str, fails: list[str]) -> None:
    print(("  ok   " if cond else "  FAIL ") + what)
    if not cond:
        fails.append(what)


def swap_cases(fails: list[str]) -> None:
    cases = (
        ("교체 성공", True, False, False, False, True),
        ("새 폴더 이동 실패", True, True, False, False, True),
        ("복원도 실패", True, True, True, False, True),
        ("기존 폴더 보관 실패", True, False, False, True, True),
        ("해독 실패", True, False, False, False, False),
        ("새 목적지 이동 실패", False, True, False, False, True),
    )
    for label, existed, fail_stage, fail_restore, fail_backup, decoded in cases:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            archive, dest = root / "input.rar", root / "output"
            archive.write_bytes(rar_archive.RAR_MAGIC + b"synthetic")
            staging = None
            if existed:
                dest.mkdir()
                (dest / "keep.txt").write_bytes(b"original")

            def decode(_archive, target):
                nonlocal staging
                staging = target
                (target / "new.txt").write_bytes(b"replacement")
                return decoded

            original_rename = Path.rename

            def rename(path, target):
                if fail_stage and path == staging:
                    raise OSError("synthetic staging rename failure")
                if fail_restore and path.name == "original":
                    raise OSError("synthetic rollback failure")
                if fail_backup and path == dest:
                    raise OSError("synthetic backup rename failure")
                return original_rename(path, target)

            with mock.patch.object(rar_archive, "_extract_into", decode), \
                    mock.patch.object(Path, "rename", rename):
                result = rar_archive.extract(archive, dest)
            success = decoded and not (fail_stage or fail_backup)
            check(result == success, f"{label}: 반환값", fails)
            backups = list(root.glob(".output.rar_old-*"))
            if success:
                preserved = (dest / "new.txt").read_bytes() == b"replacement" and not (dest / "keep.txt").exists()
            elif fail_restore:
                preserved = (not dest.exists() and len(backups) == 1
                             and (backups[0] / "original" / "keep.txt").read_bytes() == b"original")
            elif existed:
                preserved = (dest / "keep.txt").is_file() and (dest / "keep.txt").read_bytes() == b"original"
            else:
                preserved = not dest.exists()
            check(preserved, f"{label}: 새 산출 또는 원본 보존", fails)
            check(staging is None or not staging.exists(), f"{label}: 임시 자리 정리", fails)
            check(len(backups) == (1 if fail_restore else 0), f"{label}: 복원 실패 원본만 보관", fails)


def rejection_cases(fails: list[str]) -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)

        z = root / "R9-9990001.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("R9-9990001.docx", b"x" * 100)
        check(not rar_archive.is_rar(z), "zip 은 RAR 로 보지 않는다", fails)
        d = root / "out_zip"
        check(not rar_archive.extract(z, d) and not d.exists(), "zip 은 풀지 않고 목적지를 만들지 않는다", fails)
        check(not rar_archive.reads(z), "zip 은 읽힌다고 하지 않는다", fails)

        broken = root / "R9-9990002.zip"
        broken.write_bytes(rar_archive.RAR_MAGIC + b"\x01\x00" + b"\x00" * 64)
        check(rar_archive.is_rar(broken), "RAR 서명을 알아본다", fails)
        d = root / "out_broken"
        d.mkdir()
        (d / "keep.txt").write_bytes(b"k")
        ok = rar_archive.extract(broken, d)
        check(not ok, "서명 뒤가 망가진 RAR 는 실패다", fails)
        check(not rar_archive.reads(broken), "망가진 RAR 는 읽힌다고 하지 않는다", fails)
        check((d / "keep.txt").read_bytes() == b"k", "실패하면 목적지를 건드리지 않는다", fails)
        check(not list(root.glob(".out_broken.rar_tmp-*")), "실패하면 임시 자리를 남기지 않는다", fails)

        empty = root / "R9-9990003.zip"
        empty.write_bytes(b"")
        check(not rar_archive.is_rar(empty), "빈 파일은 RAR 가 아니다", fails)

    cases = {
        "a.docx": PurePosixPath("a.docx"),
        "dir\\b.doc": PurePosixPath("dir/b.doc"),
        "./c/./d.doc": PurePosixPath("c/d.doc"),
        "../e.doc": None,
        "f/../../g.doc": None,
        "/abs.doc": None,
        "\\abs.doc": None,
        "C:\\x.doc": None,
        "": None,
    }
    for name, want in cases.items():
        check(rar_archive.safe_relpath(name) == want, f"safe_relpath({name!r}) == {want}", fails)


def entry_cases(fails: list[str]) -> None:
    """Read-only and extracting paths apply the same entry and size rules."""
    def entry(name, *, directory=False, size=1, link=False):
        return types.SimpleNamespace(pathname=name, isdir=directory,
            isreg=not directory, islnk=link, issym=False, size=size,
            get_blocks=lambda: iter([b'x']))

    cases = (
        ('regular file', [entry('a/b')], True),
        ('explicit directory', [entry('a', directory=True), entry('a/b')], True),
        ('file parent', [entry('a'), entry('a/b')], False),
        ('implicit directory as file', [entry('a/b'), entry('a')], False),
        ('explicit directory as file', [entry('a', directory=True), entry('a')], False),
        ('file as explicit directory', [entry('a'), entry('a', directory=True)], False),
        ('size mismatch', [entry('a', size=2)], False),
        ('link', [entry('a', link=True)], False),
        ('parent escape', [entry('../a')], False),
    )
    for label, entries, expected in cases:
        codec = types.SimpleNamespace(file_reader=lambda _path: contextlib.nullcontext(entries))
        with tempfile.TemporaryDirectory() as td, mock.patch.dict(sys.modules, {'libarchive': codec}):
            root = Path(td); archive = root / 'input.rar'; dest = root / 'output'
            archive.write_bytes(rar_archive.RAR_MAGIC + b'synthetic entries')
            dest.mkdir(); (dest / 'original').write_bytes(b'keep')
            check(rar_archive.reads(archive) == expected, label + ': read-only verdict', fails)
            check(rar_archive.extract(archive, dest) == expected, label + ': extraction verdict', fails)
            if expected:
                check((dest / 'a/b').read_bytes() == b'x', label + ': exact extracted bytes', fails)
            else:
                check((dest / 'original').read_bytes() == b'keep', label + ': original preserved', fails)
            check(not list(root.glob('.output.rar_tmp-*')), label + ': staging cleaned', fails)


def main() -> int:
    fails: list[str] = []
    original_import = builtins.__import__
    codec_attempts = []
    external_calls = []

    def without_codec(name, *args, **kwargs):
        if name == "libarchive":
            codec_attempts.append(name)
            raise ImportError("synthetic unavailable RAR codec")
        return original_import(name, *args, **kwargs)

    def denied(*args, **kwargs):
        external_calls.append((args, kwargs))
        raise AssertionError("합성 RAR 시험의 외부 프로세스·네트워크 호출")

    with contextlib.ExitStack() as stack:
        for target in ((subprocess, "run"), (subprocess, "Popen"),
                       (socket, "socket"), (socket, "create_connection")):
            stack.enter_context(mock.patch.object(*target, side_effect=denied))
        entry_cases(fails)
        stack.enter_context(mock.patch.object(builtins, "__import__", without_codec))
        rejection_cases(fails)
        check(codec_attempts == ["libarchive", "libarchive"],
              "코덱 부재: extract·reads가 실제 해독 경로를 시도", fails)
        swap_cases(fails)
    check(not external_calls, "외부 프로세스·네트워크 호출 0건", fails)

    print(f"\n{'PASS' if not fails else 'FAIL'} ({len(fails)} 실패)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
