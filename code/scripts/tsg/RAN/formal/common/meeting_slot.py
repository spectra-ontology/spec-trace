"""회의별 표·그림·차트 파일과 보고서 JSON의 저장 및 교체.

Spec: docs/tsg/RAN/formal/RAN1/phase-2/step1_parsing.md.
Ontology: 보고서 항목의 filePath와 moreFilePaths.
Cycle: 임시 디렉토리 추출 -> 전체 직렬화 -> 회의별 산출물 교체.
배경: 실패한 재파싱이 기존 JSON과 첨부 파일을 서로 다른 세대로 남기지 않도록 한다.
사용: WG별 ReportParser가 저장 경로와 직렬화한 보고서를 전달한다.
LLM 호출: 없음.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

#: 회의별 디렉토리의 조부모 이름. 이 밖의 경로는 reset에서 지우지 않는다.
KINDS = {"tables", "figures", "charts"}


class GenerationRecoveryError(RuntimeError):
    """복구 중에도 오류가 나면 원래 산출물을 임시 디렉토리에 보존한다."""


def save_bytes_atomic(path: Path, data: bytes) -> None:
    """추출한 파일 바이트를 교체한다. 실패·중단 시 기존 파일과 권한을 보존한다.

    부모 디렉토리는 호출자가 준비한다. 교체 단위는 파일 하나다.
    """
    path = Path(path)
    if path.is_symlink():
        raise ValueError(f"Artifact output must be a regular file: {path}")
    mode = path.stat().st_mode & 0o777 if path.exists() else None
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f'.{path.name}.',
                                         suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if mode is not None:
            temporary.chmod(mode)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def reset(slot: Path | None) -> None:
    """`{tables|figures|charts}/{WG}/{WG}_{회의}` 자리를 지운다. None 이거나 없으면 아무것도 하지 않는다."""
    if slot is None or not slot.exists():
        return
    wg = slot.parent.name
    if slot.parent.parent.name not in KINDS or not slot.name.startswith(f"{wg}_"):
        raise ValueError(f"회의 추출 자리가 아니다: {slot}")
    shutil.rmtree(slot)


def rewrite_artifact_paths(items, old_prefix: str, new_prefix: str) -> None:
    """모델의 기본 파일·추가 부품 경로를 임시 위치에서 최종 위치로 바꾼다."""
    def rewrite(value):
        if not value.startswith(old_prefix):
            raise ValueError(f"Artifact outside staged generation: {value}")
        return new_prefix + value[len(old_prefix):]

    for item in items:
        for field in ("file_path", "chart_path"):
            value = getattr(item, field, None)
            if value:
                setattr(item, field, rewrite(value))
        if getattr(item, "more_file_paths", None):
            item.more_file_paths = [rewrite(value) for value in item.more_file_paths]


def publish_generation(work: Path, pairs, *, report_path=None, report_bytes=None) -> None:
    """준비된 회의별 디렉토리와 JSON을 교체하고, 실행 중 오류에는 이전 상태를 복구한다.

    호출자가 각 디렉토리의 WG·회의 소유 범위를 확인한 뒤 (임시, 최종) 경로를 전달한다.
    개별 rename 사이에는 중간 상태가 보일 수 있으며 프로세스 강제 종료의 자동 복구를 보장하지 않는다.
    """
    work = Path(work)
    pairs = [(Path(staged), Path(target)) for staged, target in pairs]
    targets = set()
    for staged, target in pairs:
        if not staged.resolve().is_relative_to(work.resolve()):
            raise ValueError(f"Artifact outside staged generation: {staged}")
        if staged.is_symlink() or not staged.is_dir():
            raise ValueError(f"Staged artifact must be a directory: {staged}")
        if target.is_symlink() or (target.exists() and not target.is_dir()):
            raise ValueError(f"Artifact slot must be a directory: {target}")
        resolved = target.resolve()
        if any(resolved.is_relative_to(other) or other.is_relative_to(resolved) for other in targets):
            raise ValueError(f"Overlapping artifact slot: {target}")
        targets.add(resolved)
    if report_path is not None:
        report_path = Path(report_path)
        if report_path.is_symlink() or (report_path.exists() and not report_path.is_file()):
            raise ValueError(f"Report output must be a regular file: {report_path}")
        resolved_report = report_path.resolve()
        if resolved_report.is_relative_to(work.resolve()):
            raise ValueError(f"Report output is inside staged generation: {report_path}")
        if any(resolved_report.is_relative_to(target) or target.is_relative_to(resolved_report)
               for target in targets):
            raise ValueError(f"Report output overlaps an artifact slot: {report_path}")
        if report_bytes is None:
            raise ValueError("Report bytes are required with report_path")
        staged = work / "report.json"
        save_bytes_atomic(staged, report_bytes)
        if report_path.exists():
            staged.chmod(report_path.stat().st_mode & 0o777)
        pairs.append((staged, report_path))
    previous = work / ".previous"
    previous.mkdir()
    receipts = []
    try:
        for index, (staged, target) in enumerate(pairs):
            target.parent.mkdir(parents=True, exist_ok=True)
            backup = previous / str(index)
            receipts.append((staged, target, backup))
            if target.exists():
                os.replace(target, backup)
            os.replace(staged, target)
    except BaseException as error:
        failures = []
        for staged, target, backup in reversed(receipts):
            try:
                # os.replace가 교체 후 예외를 전달한 경우도 이전 상태로 복구한다.
                if backup.exists() or not staged.exists():
                    if target.is_dir() and not target.is_symlink():
                        shutil.rmtree(target)
                    else:
                        target.unlink(missing_ok=True)
                if backup.exists():
                    os.replace(backup, target)
            except BaseException as recovery_error:
                failures.append(f"{target}: {recovery_error}")
        if failures:
            raise GenerationRecoveryError(
                f"Generation recovery incomplete; retained originals at {work}: "
                + "; ".join(failures)
            ) from error
        raise
