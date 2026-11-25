#!/usr/bin/env python3
"""test_archive_head.py — `archive_head` 의 형식 판정을 합성 파일로 시험한다.

`.zip` 이름으로 받은 파일이 0바이트 · 웹 응답(HTML · XML) · 서명 없는 바이트일 때 받은 것으로
세지 않는지, ZIP(분할 표지 · 앞에 다른 바이트가 붙은 것 포함) · 7z · RAR 서명은 형식으로
통과시키는지, 이름이 `.zip` 이 아닌 파일은 아카이브를 약속하지 않는지 본다. RAR 를 읽을
도구가 없을 때 판정을 내리지 않는지(None)도 확인한다. 내용 검사(CRC · `7z t`)는 부르는 쪽의
일이라 여기서 보지 않는다.

사용:
    python3 scripts/common/common/test_archive_head.py
"""
from __future__ import annotations

import builtins
import io
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import archive_head  # noqa: E402


def check(cond: bool, what: str, fails: list[str]) -> None:
    print(("  ok   " if cond else "  FAIL ") + what)
    if not cond:
        fails.append(what)


def zip_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("a.txt", "hello" * 100)
    return buf.getvalue()


def main() -> int:
    fails: list[str] = []
    zb = zip_bytes()
    cases = {
        "empty.zip": (b"", "empty", True),
        "page.zip": (b"<!DOCTYPE html><html><body>404</body></html>", "markup", True),
        "bom.zip": (b"\xef\xbb\xbf\n  <html></html>", "markup", True),
        "xmlerr.zip": (b'<?xml version="1.0"?><Error/>', "markup", True),
        "ok.zip": (zb, "zip", False),
        "UPPER.ZIP": (zb, "zip", False),
        "span.zip": (b"PK00" + zb, "zip", False),
        "prefixed.zip": (b"\xd0\xcf\x11\xe0" + b"\0" * 60 + zb, "zip", False),
        "seven.zip": (archive_head.SEVEN_Z_MAGIC + b"\0" * 26, "7z", False),
        "rar.zip": (archive_head.RAR_MAGIC + b"\0" * 40, "rar", False),
        "drm.zip": (b"<## DRM FILE ##>" + b"\x01" * 200, "other", True),
        "filtered.zip": (b"[Content removed]\n", "other", True),
        "page.htm": (b"<html></html>", "markup", True),
    }
    with tempfile.TemporaryDirectory(prefix="archive-head-") as tmp:
        work = Path(tmp)
        for name, (data, want_kind, want_failure) in cases.items():
            path = work / name
            path.write_bytes(data)
            kind = archive_head.sniff(path)
            check(kind == want_kind, f"{name}: 부류 {kind} == {want_kind}", fails)
            failure = archive_head.download_failure(kind, path)
            check((failure is not None) == want_failure,
                  f"{name}: 받은 것으로 세지 않음 == {want_failure} ({failure})", fails)
        check(archive_head.expects_archive(work / "UPPER.ZIP"), "대문자 .ZIP 도 아카이브 약속", fails)
        check(not archive_head.expects_archive(work / "page.htm"), ".htm 은 아카이브 약속 아님", fails)
        check(not archive_head.expects_archive(work / "doc.docx"), ".docx 는 아카이브 약속 아님", fails)
        try:
            archive_head.sniff(work / "missing.zip")
            check(False, "없는 파일은 OSError", fails)
        except OSError:
            check(True, "없는 파일은 OSError", fails)

        rar = work / "rar.zip"
        real_import = builtins.__import__

        def no_libarchive(name, *args, **kwargs):
            if name == "libarchive":
                raise ImportError(name)
            return real_import(name, *args, **kwargs)

        with mock.patch.object(builtins, "__import__", no_libarchive):
            check(archive_head.rar_readable(rar) is None, "RAR 도구 없음 → 판정 안 함(None)", fails)
        with mock.patch.dict(sys.modules, {"libarchive": mock.MagicMock()}), \
                mock.patch.object(archive_head.rar_archive, "reads", return_value=False):
            check(archive_head.rar_readable(rar) is False, "RAR 도구 있음 · 읽기 실패 → False", fails)

    print(f"FAIL {len(fails)}" if fails else "PASS")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
