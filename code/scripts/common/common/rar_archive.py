#!/usr/bin/env python3
"""rar_archive.py — 7z 가 풀지 못한 RAR 아카이브를 libarchive 로 푼다.

무엇인가
--------
3GPP 기고 가운데 RAR 로 압축해 `.zip` 이름으로 올린 것이 있다. 추출기는 zipfile 이 열지
못하면 7z 로 한 번 더 여는데, 이 저장소의 p7zip(16.02+dfsg)은 RAR 형식을 알아보아 항목
이름까지 보여 주지만 RAR 압축 해제 코덱이 빠진 배포판이다(`7z i` 의 코덱 목록에 Rar 가
없다). RAN 의 회의 · CR 입력에서 RAR 서명으로 시작하는 파일 57개를 `7z t` 로 시험하면 모두
`Unsupported Method` 로 끝난다.
그런 파일은 어떤 재실행으로도 풀리지 않고 그 TDoc 의 문서가 통째로 빠진다.

OS 의 libarchive(3.6.0)는 57개를 모두 오류 없이 읽는다. 회의 TDoc 으로 `.zip` 이름을 단 RAN
RAR 41개 가운데 예전에 다른 도구로 풀어 산출에 이미 있던 33개는 libarchive 산출이 항목마다 그
산출과 바이트가 같았다. 7z 가 실패한 뒤에만 이 경로를 쓴다.

무엇을 하지 않는가
------------------
- 첫 바이트가 RAR 서명(`Rar!` 1A 07)이 아닌 파일은 열지 않는다. libarchive 는 zip 도
  읽지만, 끝이 잘린 zip 이나 두 판이 이어 붙은 zip 은 7z 가 거부한 판정을 그대로 둔다.
- 일반 파일과 디렉토리가 아닌 항목(링크 · 장치), 절대 경로, `..` 이 든 경로를 만나면
  그 아카이브 전체를 실패로 돌린다.
- 암호가 걸린 항목, 읽다 난 오류, 머리에 적힌 크기와 읽은 바이트 수가 다른 항목도
  전체 실패다. 부분 산출을 남기지 않는다.

목적지와 같은 부모의 고유한 임시 폴더(`.<이름>.rar_tmp-*`)에 모두 추출한 뒤 목적지를 교체한다.
해독 실패는 목적지를 건드리지 않는다. 교체할 때는 기존 목적지를 고유한 형제 폴더(`.<이름>.rar_old-*`)에 먼저
보관하고, 새 폴더 이동이 실패하면 되돌린다. 복원도 실패하면 원본을 그 보관 폴더에 남긴다.

`reads` 는 `extract` 와 같은 판정으로 끝까지 읽기만 하고 쓰지 않는다. 풀리지 않은 입력을
세는 검사기도 실제 추출과 같은 기준으로 추출 가능 여부를 확인한다.

파이썬 쪽 바인딩은 `libarchive-c` 이고 OS 공유 라이브러리 `libarchive.so.13` 을 불러 쓴다.
둘 중 하나라도 없으면 `extract`는 False를 반환하고 호출자가 기존 실패 처리를 수행한다.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path, PurePosixPath

#: RAR 1.5~4.x(`Rar!` 1A 07 00)와 RAR5(`Rar!` 1A 07 01 00)가 함께 갖는 앞머리.
RAR_MAGIC = b"Rar!\x1a\x07"


def is_rar(path: Path) -> bool:
    """첫 바이트가 RAR 서명인가."""
    try:
        with open(path, "rb") as fh:
            return fh.read(len(RAR_MAGIC)) == RAR_MAGIC
    except OSError:
        return False


def safe_relpath(name: str) -> PurePosixPath | None:
    """아카이브 항목 이름을 목적지 아래 상대 경로로 바꾼다. 밖으로 나가는 이름이면 None.

    RAR 는 경로 구분자로 `/` 와 `\\` 를 모두 쓴 판이 있어 둘 다 나눈다. 빈 조각과 `.` 은 버린다.
    """
    parts = [p for p in name.replace("\\", "/").split("/") if p not in ("", ".")]
    if not parts or name.startswith(("/", "\\")) or any(p == ".." for p in parts):
        return None
    if ":" in parts[0]:  # 드라이브 문자
        return None
    return PurePosixPath(*parts)


def _extract_into(archive: Path, staging: Path | None) -> bool:
    """항목을 모두 읽어 `staging` 아래에 쓴다. `staging` 이 None 이면 읽기만 하고 쓰지 않는다."""
    import libarchive  # 바인딩이나 OS 라이브러리가 없으면 ImportError · OSError

    written = 0
    files, directories = set(), set()
    with libarchive.file_reader(str(archive)) as entries:
        for entry in entries:
            rel = safe_relpath(entry.pathname or "")
            if rel is None:
                return False
            parents = set(rel.parents) - {PurePosixPath('.')}
            if parents & files:
                return False
            if entry.isdir:
                if rel in files:
                    return False
                directories.update(parents | {rel})
                if staging is not None:
                    (staging / rel).mkdir(parents=True, exist_ok=True)
                continue
            if not entry.isreg or entry.islnk or entry.issym:
                return False
            if rel in directories:
                return False
            files.add(rel)
            directories.update(parents)
            n = 0
            if staging is None:
                for block in entry.get_blocks():
                    n += len(block)
            else:
                target = staging / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                with open(target, "wb") as out:
                    for block in entry.get_blocks():
                        out.write(block)
                        n += len(block)
            if entry.size is not None and n != entry.size:
                return False
            written += 1
    return written > 0


def reads(archive: Path) -> bool:
    """RAR 이고 `extract` 가 풀 수 있는가 — 같은 판정으로 끝까지 읽되 아무것도 쓰지 않는다."""
    archive = Path(archive)
    if not is_rar(archive):
        return False
    try:
        return _extract_into(archive, None)
    except Exception:
        return False


def extract(archive: Path, dest: Path) -> bool:
    """RAR 이면 libarchive 로 `dest` 에 푼다. 모든 항목을 온전히 풀었을 때만 참이다."""
    archive, dest = Path(archive), Path(dest)
    if not is_rar(archive):
        return False
    staging = None
    backup = None
    committed = False
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f".{dest.name}.rar_tmp-", dir=dest.parent))
        if not _extract_into(archive, staging):
            return False
        if dest.exists():
            backup = Path(tempfile.mkdtemp(prefix=f".{dest.name}.rar_old-", dir=dest.parent))
            dest.rename(backup / "original")
        try:
            staging.rename(dest)
        except Exception:
            if backup is not None:
                (backup / "original").rename(dest)
            raise
        committed = True
        return True
    except Exception:  # libarchive 의 ArchiveError · 바인딩 부재 · 쓰기 오류는 모두 실패다
        return False
    finally:
        if staging is not None:
            shutil.rmtree(staging, ignore_errors=True)
        if backup is not None:
            original = backup / "original"
            if committed or not (original.exists() or original.is_symlink()):
                shutil.rmtree(backup, ignore_errors=True)
