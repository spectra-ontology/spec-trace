"""증분 갱신의 WG 실행 잠금과 상태 파일의 변경 충돌을 관리한다."""

from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


class UpdateInProgress(RuntimeError):
    """같은 저장소·WG의 다른 갱신이 실행 중이다."""


class StaleStateError(RuntimeError):
    """읽은 뒤 변경된 실행 이력을 덮어쓰려 했다."""


@contextmanager
def _exclusive_lock(identity: str, *, blocking: bool):
    # 파일을 지우면 대기 중인 프로세스와 새 프로세스가 다른 inode를 잠글 수 있다.
    # 작은 잠금 파일은 OS 임시 디렉터리에 유지하고 프로세스 종료로 잠금을 해제한다.
    digest = hashlib.sha256(identity.encode()).hexdigest()
    path = Path(tempfile.gettempdir()) / f"spectra-update-{os.getuid()}-{digest}.lock"
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        flags = fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB)
        try:
            fcntl.flock(fd, flags)
        except BlockingIOError as exc:
            raise UpdateInProgress("같은 WG의 증분 갱신이 실행 중입니다. 해당 실행 종료 후 다시 실행하세요.") from exc
        yield
    finally:
        os.close(fd)


@contextmanager
def update_execution_lock(root: Path, wg: str):
    """상태 조회 전부터 Phase-10/11의 모든 쓰기 완료까지 같은 WG를 잠근다."""
    if not isinstance(wg, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", wg):
        raise ValueError("갱신 잠금에 사용할 WG 이름이 올바르지 않습니다")
    with _exclusive_lock(f"execution:{Path(root).resolve()}:{wg}", blocking=False):
        yield


def state_revision(path: Path) -> str | None:
    """파일 원본의 SHA를 반환한다. 파일이 아직 없으면 None이다."""
    try:
        content = Path(path).read_bytes()
    except FileNotFoundError:
        return None
    return hashlib.sha256(content).hexdigest()


def read_state_document(path: Path):
    """JSON과 revision을 동일한 원본 바이트에서 읽는다."""
    content = Path(path).read_bytes()
    return json.loads(content), hashlib.sha256(content).hexdigest()


def save_state_checked(path: Path, data, expected_revision: str | None, writer) -> str:
    """상태의 읽기 이후 변경을 검사하고 검사·원자 교체를 한 잠금에서 수행한다."""
    path = Path(path)
    with _exclusive_lock(f"state:{path.resolve()}", blocking=True):
        if state_revision(path) != expected_revision:
            raise StaleStateError("실행 이력이 다른 실행에서 변경됐습니다. 상태를 다시 읽은 뒤 재실행하세요.")
        writer(path, data)
        return state_revision(path)


def validate_auto_arguments(parser, args, explicit_targets) -> None:
    """자동 대상 선택과 명시 대상·Task 선택의 모호한 조합을 거절한다."""
    if args.auto and (explicit_targets or args.task is not None):
        parser.error("--auto는 특정 대상이나 --task와 함께 사용할 수 없습니다.")
    if args.auto and getattr(args, "validate_only", False):
        parser.error("--auto와 --validate-only는 함께 사용할 수 없습니다.")
