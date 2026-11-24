#!/usr/bin/env python3
"""bootstrap_runtime.py — 구축 준비와 실행의 잠금·내용 식별·산출 계약.

Spec: docs/common/process/internal_deployment_readiness.md 작업 4
Ontology: 구축 파티션의 입력·산출 파일 신원 계약.
Cycle: 설치 준비 → 실행 → 재개
배경: 다른 범위·모델·산출물의 실행이 같은 상태를 이어받는 것을 방지한다.
사용: install.sh·prepare_scope.py·run_bootstrap.py에서 공유한다.
LLM 호출: 없음. Docker 접근 점검은 현재 context의 daemon 정보를 읽는다.

잠금은 설치기의 자식 프로세스에 같은 열린 파일로 전달한다. 마지막 프로세스가
닫힐 때 해제하므로 중단된 설치기의 자식이 쓰는 동안 새 실행이 시작되지 않는다.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import time

LOCK_ENV = "SPECTRA_BOOTSTRAP_LOCK_FD"
IGNORED_DIRS = {".git", ".venv", ".venv-cpu", "__pycache__", ".pytest_cache", "node_modules"}


class Refused(RuntimeError):
    """기존 산출물을 바꾸기 전에 재개 조건 불일치를 알린다."""


def check_docker_access() -> str:
    """Check read-only daemon access and return its identity before smoke setup."""
    try:
        result = subprocess.run(
            ["docker", "info", "--format", "{{.ID}}"],
            capture_output=True, text=True, timeout=15,
        )
    except FileNotFoundError as exc:
        raise Refused("docker 명령이 없다. 설치 안내 2.2절에서 Docker CLI와 실행 경로를 확인한다.") from exc
    except subprocess.TimeoutExpired as exc:
        raise Refused("Docker 접근 확인이 15초 안에 끝나지 않았다. 현재 Docker context와 daemon 상태를 확인한다.") from exc
    except OSError as exc:
        raise Refused("docker 명령을 실행하지 못했다. CLI 실행 권한과 설치 안내 2.2절을 확인한다.") from exc
    if result.returncode:
        error = result.stderr.lower()
        if "permission denied" in error or "access is denied" in error:
            raise Refused(
                "Docker 접근 권한이 없다. WSL2 Docker Engine에서는 id -nG에 docker가 보조 그룹으로 "
                "적용됐는지 확인하고, 그룹을 추가했다면 WSL 재로그인 후 다시 실행한다. "
                "sg/newgrp로 설치기를 우회하지 않는다. Desktop·rootless·원격 daemon은 해당 context와 "
                "소켓 접근 권한을 확인한다(설치 안내 2.2절)."
            )
        raise Refused(
            "docker info가 실패했다. 현재 Docker context와 daemon 기동 상태를 설치 안내 2.2절에서 "
            "확인한다. 수동 Engine은 WSL 재시작 후 daemon을 다시 기동해야 할 수 있다."
        )
    daemon_id = result.stdout.strip()
    if not daemon_id:
        raise Refused("Docker daemon ID를 확인하지 못했다. docker info와 현재 context를 확인한다.")
    return daemon_id


def lock_path(root: Path) -> Path:
    return root / "logs" / "common" / "bootstrap" / ".lock"


def inherited_lock_fd(root: Path) -> int | None:
    value = os.environ.get(LOCK_ENV)
    if value is None:
        return None
    try:
        fd = int(value)
        opened, expected = os.fstat(fd), lock_path(root).stat()
        if (opened.st_dev, opened.st_ino) != (expected.st_dev, expected.st_ino):
            raise ValueError("잠금 파일 식별 불일치")
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except (ValueError, OSError) as exc:
        raise Refused("상속된 구축 잠금을 확인하지 못했다") from exc


def lock_fds(root: Path) -> tuple[int, ...]:
    fd = inherited_lock_fd(root)
    return () if fd is None else (fd,)


@contextmanager
def bootstrap_lock(root: Path):
    relative_file(root, lock_path(root))
    inherited = inherited_lock_fd(root)
    if inherited is not None:
        yield inherited
        return
    path = lock_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise Refused("다른 설치·범위 준비·구축 실행이 진행 중이다") from exc
        os.set_inheritable(fd, True)
        os.environ[LOCK_ENV] = str(fd)
        yield fd
    finally:
        os.environ.pop(LOCK_ENV, None)
        os.close(fd)


def file_hash(path: Path) -> str:
    before = path.stat()
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (
            after.st_size, after.st_mtime_ns, after.st_ino):
        raise Refused("내용 식별 중 파일이 바뀌었다")
    return h.hexdigest()


def relative_file(root: Path, path: Path) -> str:
    try:
        relative = path.absolute().relative_to(root.absolute())
        name = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise Refused("입출력 계약 경로가 저장소 밖을 가리킨다") from exc
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise Refused(f"입출력 계약의 symlink는 지원하지 않는다: {relative.as_posix()}")
    return name


def file_manifest(root: Path, paths) -> dict[str, str]:
    out = {}
    for path in sorted(set(paths)):
        name = relative_file(root, path)
        if not path.is_file():
            raise Refused(f"계약 파일이 없다: {name}")
        out[name] = file_hash(path)
    return out


def contract_manifest(root: Path, specs: list, wg: str) -> dict[str, str]:
    """inputs/outputs의 파일을 상대경로 → SHA-256 대응표로 만든다.

    각 항목은 {path: 상대경로, glob: 선택 패턴}이다. 디렉터리에는 glob을 명시한다.
    빈 매치·경로 이탈·symlink는 오류로 처리한다.
    """
    paths = []
    for spec in specs:
        spec = {"path": spec} if isinstance(spec, str) else spec
        if not isinstance(spec, dict) or set(spec) - {"path", "glob"} or "path" not in spec:
            raise Refused("inputs/outputs 계약은 path와 선택 glob만 사용한다")
        rel = str(spec["path"]).replace("{WG}", wg).replace("{wg}", wg.lower())
        base = root / rel
        relative_file(root, base)
        if Path(rel).is_absolute() or ".." in Path(rel).parts:
            raise Refused("inputs/outputs 계약은 저장소 상대경로를 사용한다")
        pattern = spec.get("glob")
        if pattern is not None:
            if Path(str(pattern)).is_absolute() or ".." in Path(str(pattern)).parts:
                raise Refused("glob은 계약 디렉터리 안에서만 해석한다")
            matches = sorted(p for p in base.glob(str(pattern)) if p.is_file())
            if not matches:
                raise Refused(f"계약 glob의 산출 파일이 없다: {rel}")
            paths.extend(matches)
        else:
            paths.append(base)
    return file_manifest(root, paths)


def code_manifest(root: Path) -> dict[str, str]:
    """실행 코드·설정·규칙의 내용을 기록하며 생성 데이터·비밀·개인 환경은 읽지 않는다."""
    roots = ["scripts/common", "scripts/tsg", "scripts/capability",
             "ontology/schema", "ontology/shapes", "docs/capability/answer/flywheel/lessons",
             "docs/capability/feature-planning/steps"]
    paths = [root / name for name in ("pyproject.toml", ".env.example") if (root / name).is_file()]
    for name in roots:
        base = root / name
        if not base.exists():
            continue
        for parent, dirs, files in os.walk(base, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS)
            paths.extend(Path(parent) / f for f in files
                         if Path(f).suffix in {".py", ".sh", ".yaml", ".yml", ".json", ".toml",
                                               ".txt", ".md", ".ttl", ".cypher", ".rq", ".sparql"})
    return file_manifest(root, paths)


def generated_metadata(root: Path, roots: list[Path]) -> dict[str, tuple[int, int, int, int]]:
    """선택 파티션의 생성 파일만 순회한다. stat은 변경 탐지용이고 보존 신원은 SHA다."""
    out = {}
    def record(path):
        name = relative_file(root, path)
        st = path.stat()
        out[name] = (st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_ino)
    for base in roots:
        # Root aliases (including empty or dangling ones) never enter os.walk's
        # child-directory check, so validate their complete path first.
        relative_file(root, base)
        if not base.exists():
            continue
        if base.is_file():
            record(base)
            continue
        for parent, dirs, files in os.walk(base, followlinks=False):
            if any((Path(parent) / d).is_symlink() for d in dirs):
                raise Refused("생성 산출 디렉터리의 symlink는 지원하지 않는다")
            dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS)
            for filename in files:
                record(Path(parent) / filename)
    return out


def update_artifacts(root: Path, artifacts: dict[str, str], before: dict, after: dict,
                     started_ns: int | None = None) -> dict[str, str]:
    """뒤 단계가 고친 파일은 그 단계의 새 해시로 갱신하고 삭제한 파일은 제거한다."""
    out = {name: checksum for name, checksum in artifacts.items() if name in after}
    # 짧은 간격의 같은 크기 재쓰기는 파일시스템 timestamp tick 안에서 stat이 같을 수 있다.
    # 단계 시작과 겹치는 최근 ctime도 해시한다. 오래된 파일의 변조는 재개 전수 SHA가 잡는다.
    cutoff = (started_ns if started_ns is not None else time.time_ns()) - 2_000_000_000
    changed = [root / name for name, stats in after.items()
               if before.get(name) != stats or stats[2] >= cutoff]
    out.update(file_manifest(root, changed))
    return out


def validate_artifacts(root: Path, artifacts: dict[str, str], current: dict) -> None:
    if set(artifacts) != set(current):
        raise Refused("구축 산출 파일의 추가·삭제가 checkpoint와 다르다")
    if file_manifest(root, [root / name for name in artifacts]) != artifacts:
        raise Refused("구축 산출 파일의 내용이 checkpoint와 다르다")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lock-command", nargs=argparse.REMAINDER, required=True)
    args = ap.parse_args()
    if not args.lock_command:
        ap.error("실행할 명령이 필요하다")
    root = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
    try:
        with bootstrap_lock(root) as fd:
            return subprocess.call(args.lock_command, pass_fds=(fd,))
    except Refused as exc:
        print(f"거절: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
