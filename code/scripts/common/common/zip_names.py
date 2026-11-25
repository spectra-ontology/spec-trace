"""zip 항목 이름을 원래 문자로 디코딩하는 공용 모듈.

zip 은 항목 이름의 인코딩을 플래그 한 비트(0x800, 「이름이 UTF-8」)로만 알린다. 비트가 꺼져 있으면
표준 라이브러리는 이름을 CP437 로 푼다. 3GPP 배포 zip 에는 UTF-8 이름을 해당 비트 설정 없이 저장한 파일이 섞여
있어서, `–` 가 `ΓÇô` 로 풀린 파일이 생긴다. 같은 zip 을 다른 도구(7z)로 푼 사본 옆에 깨진 이름의
사본이 겹쳐 쌓이거나, 깨진 이름이 유일한 사본이 된다. 파일 이름에서 제목을 읽는 쪽은 깨진 글자를
그대로 싣는다.

비트가 꺼진 이름은 CP437 바이트로 되돌린 뒤 UTF-8로 엄격하게 디코딩한다. 변환에 성공하면
그 이름을 사용한다. UTF-8로 디코딩되지 않는 이름은 유지하고 경고를 남긴다.
인코딩 정보가 명시된 경우에는 아래 확장 필드의 값을 우선한다.

다만 항목의 중앙 목록 확장 필드가 원래 이름을 밝히면 짐작이 아니므로 그것을 먼저 쓴다.
- 0x7075(Info-ZIP 유니코드 경로): 버전 1 · 원래 이름 바이트의 CRC32 · UTF-8 이름. CRC 가 지금
  이름 바이트와 맞을 때만 쓴다(다른 도구가 이름만 바꾸고 이 필드를 남긴 경우를 거른다).
- 0xE57A(ALZip 이 붙이는 코드 페이지): 4바이트 리틀엔디언 코드 페이지 번호. 이름 바이트가 그
  코드 페이지로 엄격히 풀릴 때만 쓴다.
RAN 회의 zip 에서 한국어(949) · 중국어 이름이 이 두 필드로만 원래 글자를 되찾는다(예: R1-164568 의
「최종본」, R4-1902191 의 「名称」). 두 필드가 없는 비-UTF-8 이름은 위와 같이 그대로 둔다.

바꾸는 것은 `ZipInfo.filename`(풀어 쓸 경로)뿐이다. 표준 라이브러리는 항목을 열 때
`orig_filename` 을 로컬 헤더와 대조하므로 읽기는 그대로 맞는다.

중앙 디렉토리와 로컬 헤더의 이름이 다른 항목
-----------------------------------------
한 항목의 이름이 중앙 디렉터리와 로컬 파일 헤더(항목 바로 앞의 헤더)에 다른 바이트로 적힌 zip이 있다.
표준 라이브러리는 항목을 열 때 두 이름을 비교해 다르면 `BadZipFile` 로 멈추고, 7z 은 그 항목을
0바이트 파일로 만들고 오류로 끝낸다. 이 사례에서는 헤더 뒤의 데이터를 풀면 중앙 디렉터리의
CRC와 크기가 맞는다. `members()`는 로컬 파일 헤더를 읽어 이름이 다르면 `orig_filename`을 그 헤더의
이름으로 맞춘다. 그러면 표준 라이브러리가 파일을 열고 CRC까지 확인한다. 추출할 파일 이름은 중앙
디렉터리의 이름을 디코딩할 수 있으면(UTF-8 비트·ASCII·위 복원 규칙) 그 값을 쓴다. 그렇지 않으면 로컬 파일
헤더의 이름을 디코딩해 사용하고, 양쪽 모두 디코딩되지 않으면 중앙 디렉터리의 이름을 유지한다. 해당 위치에 로컬 파일 헤더가 없는 항목은
변경하지 않는다 — 열 때 표준 라이브러리가 멈추고, 호출부에서 실패를 처리한다.

`members()` 는 같은 `ZipFile` 에 두 번 불려도 첫 번째 결과를 그대로 돌려준다. `orig_filename` 을
바꾼 뒤 이름을 다시 판정하면 다른 이름을 고를 수 있어서다. 이름을 바꾼 항목은
`zf.open(info.filename)` 으로 찾을 수 없으므로(표준 라이브러리의 이름 색인은 처음 읽은 이름이다)
`ZipInfo` 를 그대로 넘긴다. 표준 `ZipFile.testzip()` 은 이름으로 열기 때문에 이름이 다른 항목에서
멈춘다. 내용 검사는 이 모듈의 `testzip()` 을 쓴다.

파일 앞머리와 다른 zip 을 읽는 경우
-----------------------------------
표준 라이브러리는 파일 끝 64 KiB 안의 마지막 종료 레코드(`PK` 05 06)를 이 zip의 종료 레코드로 읽는다.
받다 만 묶음 zip 이 압축하지 않고 담은 안쪽 zip 뒤에서 잘렸으면 마지막 끝 기록은 그 안쪽 zip 의
것이고, 표준 라이브러리는 안쪽 zip을 묶음 전체로 읽어 그 항목만 오류 없이 푼다. CRC도 맞는다.
그때 항목 위치는 모두 안쪽 zip이 놓인 자리 뒤를 가리키고, 파일 0 위치의 로컬 파일 헤더(묶음의 첫
항목)는 어느 항목에도 속하지 않는다. `members()`는 파일이 로컬 파일 헤더로 시작하는데 0 위치에서
시작하는 항목이 없으면 `BadZipFile` 로 멈춘다. 부르는 쪽은 열지 못한 zip 의 실패 경로를 타고,
7z 은 그런 파일을 잘린 것으로 읽어 오류로 끝낸다. 앞에 다른 바이트를 붙인 zip(자동 실행 묶음)은
로컬 파일 헤더로 시작하지 않아 이 검사에서 제외된다.

3GPP 원격에는 같은 zip 을 두 번이나 세 번 그대로 이어 붙인 파일도 있다(원격 크기가 그 길이이고,
처음부터 다시 받아도 바이트가 같다). 표준 라이브러리는 마지막 사본을 읽으므로 0 위치에서 시작하는
항목이 없지만, 앞의 사본들과 바이트가 같아 같은 내용을 읽는다. 파일 크기가 읽은 사본의 길이로
나누어떨어지고 모든 사본의 바이트가 같을 때만 통과시킨다. 앞에 다른 zip이 붙은 파일은 거절한다.
마지막 사본만 읽으면 앞의 zip 내용이 누락되기 때문이다.
"""

from __future__ import annotations

import hashlib
import logging
import shutil
import os
import struct
import zipfile
import zlib

_UTF8_FLAG = 0x800
_UNICODE_PATH = 0x7075
_ALZIP_CODEPAGE = 0xE57A
_LOCAL_MAGIC = b"PK\x03\x04"
_DONE_ATTR = "_zip_names_members"

log = logging.getLogger(__name__)


def _extra_fields(extra: bytes) -> dict[int, bytes]:
    """확장 필드를 {필드 ID: 내용}으로 나눈다. 같은 ID가 두 번 있으면 앞의 값을 쓴다."""
    fields: dict[int, bytes] = {}
    k = 0
    while k + 4 <= len(extra):
        hid, size = struct.unpack("<HH", extra[k:k + 4])
        fields.setdefault(hid, extra[k + 4:k + 4 + size])
        k += 4 + size
    return fields


def _declared(raw: bytes, extra: bytes) -> str | None:
    """확장 필드가 밝힌 원래 이름(모듈 설명). 밝히지 않았거나 검증에 걸리면 None."""
    fields = _extra_fields(extra)
    up = fields.get(_UNICODE_PATH)
    if up is not None and len(up) > 5 and up[0] == 1 and struct.unpack("<I", up[1:5])[0] == zlib.crc32(raw):
        try:
            return up[5:].decode("utf-8")
        except UnicodeDecodeError:
            pass
    cp = fields.get(_ALZIP_CODEPAGE)
    if cp is not None and len(cp) >= 4:
        page = struct.unpack("<I", cp[:4])[0]
        try:
            return raw.decode("utf-8" if page == 65001 else f"cp{page}")
        except (LookupError, UnicodeDecodeError):
            pass
    return None


def _recover(name: str, flag_bits: int, extra: bytes = b"") -> tuple[str, bool]:
    """(되찾은 이름, 원래 글자로 읽혔는가). UTF-8 비트가 켜지면 그 이름을 유지한다.

    `extra`는 그 이름과 함께 적힌 확장 필드다(중앙 디렉터리 이름이면 `ZipInfo.extra`).
    """
    if flag_bits & _UTF8_FLAG:
        return name, True
    try:
        raw = name.encode("cp437")
    except UnicodeEncodeError:
        return name, False
    fixed = _declared(raw, extra)
    if fixed is None:
        try:
            fixed = raw.decode("utf-8")
        except UnicodeDecodeError:
            return name, False
    return fixed.replace(os.sep, "/"), True


def recovered_name(info: zipfile.ZipInfo) -> str:
    """항목의 원래 이름. UTF-8 플래그를 유지하고 검증된 확장 필드의 선언을 적용한다."""
    # 판정은 라이브러리가 처음 푼 이름(`orig_filename`)에서 한다 — `members()` 가 `filename` 을
    # 바꿔 두므로, 거기서 다시 판정하면 되찾은 이름을 한 번 더 CP437 로 되돌리려다 실패한다.
    name, readable = _recover(info.orig_filename, info.flag_bits, info.extra)
    if not readable or name == info.orig_filename:
        return info.filename
    return name


def local_name(zf: zipfile.ZipFile, info: zipfile.ZipInfo) -> tuple[str, int] | None:
    """로컬 파일 헤더에 적힌 (이름, 플래그)를 표준 라이브러리와 같은 규칙으로 디코딩한다.

    그 위치에 로컬 파일 헤더가 없거나 플래그에 따라 디코딩할 수 없으면 None을 반환한다.
    """
    fp = zf.fp
    if fp is None:
        return None
    pos = fp.tell()
    try:
        fp.seek(info.header_offset)
        head = fp.read(30)
        if len(head) < 30 or head[:4] != _LOCAL_MAGIC:
            return None
        flag = struct.unpack("<H", head[6:8])[0]
        raw = fp.read(struct.unpack("<H", head[26:28])[0])
    finally:
        fp.seek(pos)
    try:
        return raw.decode("utf-8" if flag & _UTF8_FLAG else "cp437"), flag
    except UnicodeDecodeError:
        return None


def _same_copies(fp, start: int) -> bool:
    """파일 전체가 `start`부터 끝까지의 바이트를 동일하게 반복한 사본들로 구성되었는지 검사한다."""
    fp.seek(0, os.SEEK_END)
    size = fp.tell()
    period = size - start
    if start <= 0 or period <= 0 or size % period:
        return False
    step = 1 << 20
    for off in range(0, period, step):
        n = min(step, period - off)
        fp.seek(start + off)
        last = fp.read(n)
        for k in range(start // period):
            fp.seek(k * period + off)
            if fp.read(n) != last:
                return False
    return True


def reads_file_start(zf: zipfile.ZipFile) -> bool:
    """표준 라이브러리가 읽은 항목이 파일 앞머리의 zip 에 속하는가.

    파일이 로컬 파일 헤더로 시작하면 0 위치에서 시작하는 항목이 있어야 한다. 없더라도 파일이 읽은 사본을
    그대로 반복한 것이면 참이다(모듈 설명). 로컬 파일 헤더로 시작하지 않거나 파일을 읽을 수 없으면
    참으로 둔다.
    """
    fp = zf.fp
    if fp is None or not fp.seekable():
        return True
    infos = zf.infolist()
    pos = fp.tell()
    try:
        fp.seek(0)
        head = fp.read(4)
        if head != _LOCAL_MAGIC or any(info.header_offset == 0 for info in infos):
            return True
        return bool(infos) and _same_copies(fp, min(info.header_offset for info in infos))
    finally:
        fp.seek(pos)


def members(zf: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    """이름을 되찾은 항목 목록 — `zf.extract(info, …)` · `zf.extractall(dest, members=…)` 에 그대로 넘긴다.

    표준 라이브러리가 파일 앞머리와 다른 zip 을 읽었으면 `BadZipFile` (모듈 설명의 「파일 앞머리와
    다른 zip 을 읽는 경우」).
    """
    done = getattr(zf, _DONE_ATTR, None)
    if done is not None:
        return done
    if not reads_file_start(zf):
        raise zipfile.BadZipFile(f"파일 시작의 로컬 파일 헤더에 해당하는 항목이 없습니다. 잘린 ZIP 안의 다른 ZIP 종료 레코드를 읽었을 수 있습니다 ({zf.filename})")
    infos = zf.infolist()
    for info in infos:
        name = recovered_name(info)
        central_readable = _recover(info.orig_filename, info.flag_bits, info.extra)[1]
        local = local_name(zf, info)
        if local is not None and local[0] != info.orig_filename:
            local_str, local_flag = local
            fixed, local_readable = _recover(local_str, local_flag)
            if not central_readable and local_readable:
                name = zipfile.ZipInfo(fixed).filename
            log.warning("ZIP 항목 이름이 중앙 디렉터리(%r)와 로컬 파일 헤더(%r)에서 다릅니다. 로컬 파일 헤더의 이름으로 열고 %s 이름으로 저장합니다 (%s)",
                        info.orig_filename, local_str, name, zf.filename)
            info.orig_filename = local_str
        if name != info.filename:
            log.info("zip 항목 이름을 원래 글자로 되찾음: %s → %s", info.filename, name)
            info.filename = name
        elif not central_readable:
            log.warning("zip 항목 이름이 UTF-8 로 풀리지 않아 CP437 로 둠: %s (%s)", name, zf.filename)
    setattr(zf, _DONE_ATTR, infos)
    return infos


def extractall(zf: zipfile.ZipFile, dest) -> None:
    """`zf.extractall(dest)` 와 같되 항목 이름을 되찾아 푼다."""
    zf.extractall(dest, members=members(zf))


def testzip(zf: zipfile.ZipFile) -> str | None:
    """`zf.testzip()` 과 같되 `members()` 의 항목으로 연다. CRC 가 맞지 않는 첫 항목의 이름, 없으면 None."""
    for info in members(zf):
        try:
            with zf.open(info) as fh:
                while fh.read(1 << 20):
                    pass
        except zipfile.BadZipFile:
            return info.filename
    return None


def sha256_member(zf: zipfile.ZipFile, info: zipfile.ZipInfo) -> bytes:
    """Return a member's SHA-256 digest using bounded reads."""
    digest = hashlib.sha256()
    with zf.open(info) as source:
        while chunk := source.read(64 * 1024):
            digest.update(chunk)
    return digest.digest()


def copy_member(zf: zipfile.ZipFile, info: zipfile.ZipInfo, destination) -> None:
    """Stream a member into a caller-owned destination; close only the source."""
    with zf.open(info) as source:
        shutil.copyfileobj(source, destination, length=64 * 1024)
