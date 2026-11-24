"""파일 교체와 저장소 공용 writer 잠금을 제공합니다."""

from contextlib import contextmanager
import fcntl
import json
import os
import shutil
import tempfile
from pathlib import Path


@contextmanager
def repository_writer_lock(root: Path, name: str):
    """모든 실행 세대가 같은 inode의 비차단 배타 잠금을 공유합니다.

    잠금은 실행 기록의 공용 상태 경로에 두고 해제 후에도 inode를 유지합니다.
    실행별 출력 폴더나 잠금 파일 삭제를 사용하면 동시 writer가 갈라집니다.
    """
    if not name or name in {".", ".."} or Path(name).name != name:
        raise ValueError("Writer lock name must be one path component")
    root = Path(root).resolve()
    path = root / "logs/common/verification/writer-locks" / (name + ".lock")
    current = root
    for part in path.relative_to(root).parts:
        current /= part
        if current.is_symlink():
            raise ValueError("Writer lock paths must use regular directories and files")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "a") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


@contextmanager
def _atomic_writer(path: Path, *, permissions: int | None, overwrite: bool,
                   **file_options):
    """텍스트와 바이트 writer의 임시 저장·동기화·게시를 공유합니다."""
    if type(overwrite) is not bool:
        raise ValueError("overwrite must be a boolean")
    path = Path(path)
    old_mode = permissions if permissions is not None else (
        path.stat().st_mode & 0o777 if overwrite and path.exists() else None)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, **file_options,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            yield stream
            stream.flush()
            os.fsync(stream.fileno())
        if old_mode is not None:
            temporary.chmod(old_mode)
        if overwrite:
            os.replace(temporary, path)
        else:
            os.link(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def write_text_atomic(path: Path, text: str, *, encoding: str = "utf-8",
                      mode: int | None = None, overwrite: bool = True) -> None:
    """쓰기나 교체가 실패하면 원본을 유지하고 임시 파일을 정리합니다.

    부모 디렉토리는 호출자가 준비합니다. 기존 파일의 권한을 보존하며,
    새 파일은 tempfile의 기본 권한을 사용합니다. mode가 있으면 그 권한으로 저장합니다.
    overwrite=False는 완성된 임시 파일을 hard link로 게시하며, 기존 경로와
    경합한 writer의 결과는 FileExistsError로 보존합니다. 부모 디렉토리의
    fsync와 여러 파일의 일괄 교체는 호출자의 별도 계약입니다.
    """
    with _atomic_writer(path, permissions=mode, overwrite=overwrite,
                        mode="w", encoding=encoding) as stream:
        stream.write(text)


def write_bytes_atomic(path: Path, data: bytes, *, mode: int | None = None,
                       overwrite: bool = True) -> None:
    """완성된 바이트를 write_text_atomic과 같은 권한·게시 계약으로 저장합니다."""
    with _atomic_writer(path, permissions=mode, overwrite=overwrite, mode="wb") as stream:
        stream.write(data)


def write_json_atomic(path: Path, value, *, mode: int | None = None,
                      overwrite: bool = True) -> None:
    """유효한 JSON을 모두 준비한 뒤 한 파일을 교체합니다.

    부모 디렉토리는 호출자가 준비합니다. 비유한 수와 직렬화할 수 없는 값은
    쓰기 전에 거절하며, 심볼릭 링크를 출력 파일로 사용하지 않습니다.
    """
    text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    path = Path(path)
    if path.is_symlink():
        raise ValueError(f"JSON 출력은 심볼릭 링크를 사용할 수 없습니다: {path}")
    write_text_atomic(path, text, mode=mode, overwrite=overwrite)


def publish_json_set(results) -> None:
    """같은 디렉토리의 JSON 묶음을 준비하고 교체 실패 시 이전 파일들을 복원합니다.

    각 경로의 교체는 순차적으로 일어납니다. 복원까지 실패하면 남은 사전 이미지와
    준비 파일을 보존하고 복구 경로를 오류에 포함합니다. 다른 writer와의 직렬화와
    전원 장애에 대한 디렉토리 동기화는 호출자의 별도 계약입니다.
    """
    results = [(path, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))
               for path, value in results]
    _publish_text_set(results, label="JSON", prefix='.json-set-')


def publish_text_set(results) -> None:
    """같은 디렉토리의 텍스트 묶음을 교체하며 None인 경로는 삭제합니다.

    모든 텍스트를 먼저 준비합니다. 교체와 명시적 삭제 중 오류나 중단이 생기면
    이전 파일들을 복원합니다. 순차 가시성·writer 조율·전원 장애 계약은
    publish_json_set과 같습니다.
    """
    _publish_text_set(list(results), label="텍스트", prefix='.text-set-')


def _publish_text_set(results, *, label: str, prefix: str) -> None:
    paths = [Path(path) for path, _ in results]
    if not paths or len(set(paths)) != len(paths) or len({p.parent for p in paths}) != 1:
        raise ValueError(f"{label} 묶음은 같은 디렉토리의 서로 다른 파일이어야 합니다.")
    texts = [text for _, text in results]
    if any(text is not None and not isinstance(text, str) for text in texts):
        raise ValueError("텍스트 묶음의 값은 문자열 또는 명시적 삭제(None)여야 합니다.")
    for path in paths:
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ValueError(f"{label} 출력은 일반 파일이어야 합니다: {path}")
    parent = paths[0].parent
    parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=prefix, dir=parent))
    attempted = []
    previous = {}
    retain = False
    try:
        (work / 'new').mkdir()
        (work / 'previous').mkdir()
        for path, text in zip(paths, texts):
            mode = path.stat().st_mode & 0o777 if path.exists() else None
            if text is not None:
                write_text_atomic(work / 'new' / path.name, text, mode=mode)
            if path.exists():
                backup = work / 'previous' / path.name
                os.link(path, backup)
                previous[path] = backup
        try:
            for path, text in zip(paths, texts):
                # 교체 직후 중단되어도 이 경로는 복원 대상에 포함합니다.
                attempted.append(path)
                if text is None:
                    path.unlink(missing_ok=True)
                else:
                    os.replace(work / 'new' / path.name, path)
        except BaseException as error:
            failures = []
            for path in reversed(attempted):
                try:
                    if path in previous:
                        os.replace(previous[path], path)
                    else:
                        path.unlink(missing_ok=True)
                except BaseException as restore_error:
                    failures.append(f"{path}: {restore_error}")
            if failures:
                retain = True
                raise RuntimeError(
                    f"{label} 묶음 복원 실패. 복구 파일 보존: {work}; "
                    + '; '.join(failures)) from error
            raise
    finally:
        if not retain:
            shutil.rmtree(work)


def copy_file_atomic(source: Path, destination: Path) -> None:
    """Copy one file with copy2 metadata, then atomically replace its destination.

    The caller prepares the parent directory. Destination symlinks are rejected,
    and an identical source/destination retains shutil.copy2's SameFileError.
    A failed or interrupted copy preserves the previous file and removes its temp.
    """
    source, destination = Path(source), Path(destination)
    if destination.is_symlink():
        raise ValueError(f"파일 복사 출력은 심볼릭 링크를 사용할 수 없습니다: {destination}")
    if destination.exists() and source.samefile(destination):
        raise shutil.SameFileError(f"{source} and {destination} are the same file")
    if destination.is_dir():
        raise IsADirectoryError(destination)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=f".{destination.name}.",
                                         suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
        shutil.copy2(source, temporary)
        with temporary.open("rb") as stream:
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
