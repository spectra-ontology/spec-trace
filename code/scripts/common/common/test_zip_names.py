"""ZIP 항목 이름 복원과 잘린 파일·중복 압축 파일 처리를 검사한다.

확장 필드 0x7075·0xE57A, 중앙 디렉터리와 로컬 파일 헤더의 이름 차이도 검사한다.
합성 ZIP만 사용하며, 시험 파일은 임시 디렉터리에 만들고 종료 시 삭제한다.

사용:
    python3 scripts/common/common/test_zip_names.py
    python3 .../test_zip_names.py --source FILE   # FILE(작업본)을 zip_names 로 읽는다
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import logging
import struct
import sys
import tempfile
import zipfile
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
logging.disable(logging.CRITICAL)


def load(path: Path):
    spec = importlib.util.spec_from_file_location("zip_names_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build(entries: list[tuple[bytes, bytes, bytes]], method=zipfile.ZIP_DEFLATED) -> bytes:
    """[(중앙 디렉터리 이름 바이트, 로컬 파일 헤더 이름 바이트, 내용)] — UTF-8 비트 없이 쓴다. 두 이름은 길이가 같아야 한다.

    표준 라이브러리는 ASCII 밖 이름을 UTF-8 비트와 함께 쓰므로, 같은 길이의 ASCII 자리 이름으로 쓴
    뒤 로컬 파일 헤더(앞)와 중앙 디렉터리(뒤)의 바이트를 바꿔 넣는다.
    """
    buf = io.BytesIO()
    marks = []
    with zipfile.ZipFile(buf, "w", method) as z:
        for k, (central, local, data) in enumerate(entries):
            assert len(central) == len(local) >= 4
            mark = (f"{k:02d}" + "#" * (len(central) - 2)).encode()
            marks.append(mark)
            z.writestr(zipfile.ZipInfo(mark.decode()), data, compress_type=method)
    raw = buf.getvalue()
    for mark, (central, local, _) in zip(marks, entries):
        assert raw.count(mark) == 2
        i = raw.index(mark)
        raw = raw[:i] + local + raw[i + len(mark):]
        j = raw.index(mark)
        raw = raw[:j] + central + raw[j + len(mark):]
    return raw


def build_extra(name: bytes, extra: bytes, data: bytes) -> bytes:
    """이름 바이트 `name` 을 UTF-8 비트 없이, 확장 필드 `extra` 를 로컬 파일 헤더와 중앙 디렉터리에 함께 담은 zip."""
    mark = b"#" * len(name)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        info = zipfile.ZipInfo(mark.decode())
        info.extra = extra
        z.writestr(info, data)
    raw = buf.getvalue()
    assert raw.count(mark) == 2
    return raw.replace(mark, name)


def unicode_path(raw_name: bytes, utf8: str, crc: int | None = None) -> bytes:
    body = b"\x01" + struct.pack("<I", zlib.crc32(raw_name) if crc is None else crc) + utf8.encode("utf-8")
    return struct.pack("<HH", 0x7075, len(body)) + body


def alzip_codepage(page: int) -> bytes:
    return struct.pack("<HHI", 0xE57A, 4, page)


NBSP_C = b"R9-9990001-\xa02-step.docx"      # 중앙 디렉터리: 라틴-1 NBSP — UTF-8 로 풀리지 않는다
NBSP_L = b"R9-9990001\xc2\xa02-step.docx"   # 로컬 파일 헤더: UTF-8 NBSP
BODY = b"synthetic body " * 400


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=HERE / "zip_names.py")
    zn = load(ap.parse_args().source)
    results: list[tuple[str, bool]] = []

    def check(why: str, ok: bool) -> None:
        results.append((why, ok))

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        # 1. 플래그 없이 담긴 UTF-8 이름을 되찾는다.
        p = tmp / "utf8.zip"
        p.write_bytes(build([("R9-9990002 \u2013 a.docx".encode("utf-8"),) * 2 + (BODY,)]))
        with zipfile.ZipFile(p) as z:
            names = [i.filename for i in zn.members(z)]
        check("플래그 없는 UTF-8 이름을 되찾는다", names == ["R9-9990002 \u2013 a.docx"])

        # 2. 중앙 디렉터리 · 로컬 파일 헤더 이름이 다른 항목을 풀고, 로컬 파일 헤더 쪽이 원래 글자로 읽히면 그 이름으로 쓴다.
        p = tmp / "mismatch.zip"
        p.write_bytes(build([(b"a.docx", b"a.docx", b"first"), (NBSP_C, NBSP_L, BODY)]))
        with zipfile.ZipFile(p) as z:
            try:
                z.extractall(tmp / "plain")
                plain_fails = False
            except zipfile.BadZipFile:
                plain_fails = True
        check("표준 해제는 이름이 다른 항목에서 멈춘다(시험 zip 이 그 결함을 갖는다)", plain_fails)
        out = tmp / "fixed"
        try:
            with zipfile.ZipFile(p) as z:
                zn.extractall(z, out)
        except zipfile.BadZipFile:
            pass
        got = sorted(x.name for x in out.iterdir()) if out.is_dir() else []
        check("두 항목 모두 풀린다", got == sorted(["a.docx", "R9-9990001\u00a02-step.docx"]))
        fixed = out / "R9-9990001\u00a02-step.docx"
        check("이름이 다른 항목의 내용이 그대로다", fixed.is_file() and fixed.read_bytes() == BODY)

        # 3. 같은 ZipFile 에 두 번 불러도 같은 이름이다.
        with zipfile.ZipFile(p) as z:
            first = [i.filename for i in zn.members(z)]
            second = [i.filename for i in zn.members(z)]
        check("members() 를 두 번 불러도 같다", first == second)

        # 4. 중앙 디렉터리 쪽이 원래 글자로 읽히면 그 이름을 쓴다.
        p = tmp / "central_ok.zip"
        p.write_bytes(build([(b"R9-9990003-a.docx", b"R9-9990003_a.docx", b"x" * 50)]))
        with zipfile.ZipFile(p) as z:
            names = [i.filename for i in zn.members(z)]
            try:
                data = z.read(zn.members(z)[0])
            except zipfile.BadZipFile:
                data = None
        check("중앙 디렉터리 이름이 읽히면 그대로 쓴다", names == ["R9-9990003-a.docx"] and data == b"x" * 50)

        if not hasattr(zn, "testzip"):
            check("testzip 이 있다", False)
            return report(results)

        # 5. testzip — 이름이 다른 항목은 온전하고, 내용이 깨진 항목은 잡는다.
        with zipfile.ZipFile(tmp / "mismatch.zip") as z:
            check("testzip 은 이름만 다른 항목을 온전하다고 본다", zn.testzip(z) is None)
        raw = bytearray(build([(b"b.txt", b"b.txt", BODY)], zipfile.ZIP_STORED))
        raw[30 + 5 + 10] ^= 0xFF
        (tmp / "crc.zip").write_bytes(bytes(raw))
        with zipfile.ZipFile(tmp / "crc.zip") as z:
            check("testzip 은 CRC 가 맞지 않는 항목을 돌려준다", zn.testzip(z) == "b.txt")
        bad = bytearray(build([(NBSP_C, NBSP_L, BODY)], zipfile.ZIP_STORED))
        start = 30 + len(NBSP_L)
        bad[start + 3] ^= 0xFF
        (tmp / "crc_mismatch.zip").write_bytes(bytes(bad))
        with zipfile.ZipFile(tmp / "crc_mismatch.zip") as z:
            check("이름이 달라도 내용 검사는 그대로 한다", zn.testzip(z) is not None)

        # 6. 로컬 파일 헤더가 그 자리에 없으면 손대지 않는다 — 열 때 멈춘다.
        raw = bytearray(build([(b"c.txt", b"c.txt", BODY)]))
        raw[0:4] = b"XXXX"
        (tmp / "nohead.zip").write_bytes(bytes(raw))
        with zipfile.ZipFile(tmp / "nohead.zip") as z:
            infos = zn.members(z)
            try:
                z.read(infos[0])
                stopped = False
            except zipfile.BadZipFile:
                stopped = True
        check("로컬 파일 헤더가 없는 항목은 열 때 멈춘다", stopped and infos[0].orig_filename == "c.txt")

        # 7. 안쪽 ZIP 뒤에서 잘린 외부 ZIP은 마지막 종료 레코드가 안쪽 ZIP의 것이다.
        #    안쪽 ZIP 끝에서 잘린 경우와 다음 항목 헤더 일부까지 남은 경우를 검사한다.
        inner = io.BytesIO()
        with zipfile.ZipFile(inner, "w") as z:
            z.writestr("R9-9990004.docx", BODY)
        outer = io.BytesIO()
        with zipfile.ZipFile(outer, "w", zipfile.ZIP_STORED) as z:
            z.writestr("R9-9990004.zip", inner.getvalue())
            z.writestr("R9-9990005.zip", b"y" * 4096)
        raw = outer.getvalue()
        end = raw.index(inner.getvalue()) + len(inner.getvalue())
        for label, cut in (("안쪽 zip 끝에서 잘린", raw[:end]), ("다음 항목 머리까지 남은", raw[:end + 20])):
            with zipfile.ZipFile(io.BytesIO(cut)) as z:
                plain = z.namelist() == ["R9-9990004.docx"] and z.testzip() is None
            check(f"표준 라이브러리는 {label} 묶음을 안쪽 zip 으로 읽는다(시험 zip 이 그 결함을 갖는다)", plain)
            for fn in ("members", "testzip"):
                with zipfile.ZipFile(io.BytesIO(cut)) as z:
                    try:
                        getattr(zn, fn)(z)
                        refused = False
                    except zipfile.BadZipFile:
                        refused = True
                check(f"{label} 묶음은 {fn}() 에서 멈춘다", refused)

        # 8. 온전한 zip 은 주석이 있어도 · 메모리 안에서도 그대로 읽는다.
        with_comment = io.BytesIO()
        with zipfile.ZipFile(with_comment, "w") as z:
            z.writestr("d.txt", BODY)
            z.comment = b"meeting pack"
        for label, data in (("주석 있는 zip", with_comment.getvalue()), ("온전한 묶음", raw)):
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                try:
                    ok = bool(zn.members(z)) and zn.testzip(z) is None
                except zipfile.BadZipFile:
                    ok = False
            check(f"{label}은 그대로 읽는다", ok)
        (tmp / "whole.zip").write_bytes(raw)
        with zipfile.ZipFile(tmp / "whole.zip") as z:
            check("파일에서 연 온전한 zip 도 그대로 읽는다", len(zn.members(z)) == 2)

        # 9. 앞에 다른 바이트를 붙인 zip(자동 실행 묶음)은 로컬 파일 헤더로 시작하지 않아 그대로 읽는다.
        with zipfile.ZipFile(io.BytesIO(b"MZ" + b"\0" * 98 + raw)) as z:
            try:
                ok = len(zn.members(z)) == 2
            except zipfile.BadZipFile:
                ok = False
        check("앞에 바이트를 붙인 zip 은 그대로 읽는다", ok)

        # 10. 같은 zip 을 두세 번 그대로 이어 붙인 파일은 읽고, 앞에 다른 zip 이 붙은 파일은 멈춘다.
        one = with_comment.getvalue()
        other = io.BytesIO()
        with zipfile.ZipFile(other, "w") as z:
            z.writestr("R9-9990006.docx", BODY + b"!")
        for label, data, want in (("두 번 이어 붙인 같은 zip", one * 2, True),
                                  ("세 번 이어 붙인 같은 zip", one * 3, True),
                                  ("앞에 다른 zip 이 붙은 파일", other.getvalue() + one, False),
                                  ("앞 사본의 한 바이트가 다른 파일", one[:-1] + b"x" + one, False)):
            (tmp / "dup.zip").write_bytes(data)
            with zipfile.ZipFile(tmp / "dup.zip") as z:
                plain = z.namelist() == ["d.txt"] and z.infolist()[0].header_offset > 0
                try:
                    got = bool(zn.members(z)) and zn.testzip(z) is None and z.read(zn.members(z)[0]) == BODY
                except zipfile.BadZipFile:
                    got = False
            check(f"표준 라이브러리는 {label}의 마지막 사본을 읽는다(시험 zip 이 그 모양을 갖는다)", plain)
            check(f"{label}은 {'읽는다' if want else 'members() 에서 멈춘다'}", got is want)

        # 11. 확장 필드가 밝힌 원래 이름을 쓴다 — 0x7075 는 CRC 가 맞을 때만, 0xE57A 는 그 코드 페이지로 풀릴 때만.
        ko = "R9-9990007 최종본.docx"
        gbk = "R9-9990008 名称.docx"
        cases = (
            ("ASCII 대체 이름에도 CRC 가 맞는 Unicode 선언을 적용한다", b"R9-9990010.docx",
             unicode_path(b"R9-9990010.docx", ko), ko),
            ("ASCII 대체 이름의 CRC 가 틀리면 원래 이름을 유지한다", b"R9-9990010.docx",
             unicode_path(b"R9-9990010.docx", ko, crc=0), "R9-9990010.docx"),
            ("0xE57A 949 이름을 한국어로 되찾는다", ko.encode("cp949"), alzip_codepage(949), ko),
            ("0x7075 CRC 가 맞으면 그 UTF-8 이름을 쓴다", gbk.encode("gbk"), unicode_path(gbk.encode("gbk"), gbk), gbk),
            ("0x7075 CRC 가 틀리면 쓰지 않고 이름을 그대로 둔다", gbk.encode("gbk"),
             unicode_path(gbk.encode("gbk"), gbk, crc=0), gbk.encode("gbk").decode("cp437")),
            ("0xE57A 코드 페이지로 풀리지 않으면 이름을 그대로 둔다", b"R9-9990009 \x80\xff.docx", alzip_codepage(949),
             b"R9-9990009 \x80\xff.docx".decode("cp437")),
            ("0xE57A 가 모르는 코드 페이지면 이름을 그대로 둔다", ko.encode("cp949"), alzip_codepage(99999),
             ko.encode("cp949").decode("cp437")),
        )
        for label, name, extra, want in cases:
            with zipfile.ZipFile(io.BytesIO(build_extra(name, extra, BODY))) as z:
                got = [i.filename for i in zn.members(z)]
                body_ok = z.read(zn.members(z)[0]) == BODY
            check(label, got == [want] and body_ok)

    return report(results)


def report(results: list[tuple[str, bool]]) -> int:
    fails = 0
    for why, ok in results:
        fails += not ok
        print(f"{'PASS' if ok else 'FAIL'} {why}")
    print(f"{len(results) - fails}/{len(results)} 통과")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
