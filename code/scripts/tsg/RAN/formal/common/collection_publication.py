"""Publish collected Word inputs while retaining any preimage that cannot be restored."""
import logging
import os
from pathlib import Path
import shutil
import tempfile

logger = logging.getLogger(__name__)


def publish_collected_documents(unpacked: Path, destination: Path, names: list[str]) -> None:
    """Replace a document set, restore on interruption, and retain failed recovery outside staging.

    The caller owns the temporary extraction directory. Recovery copies live beside
    the destination so its temporary-directory cleanup cannot remove the only old
    input after a failed restoration. A successful replacement or restoration
    removes the recovery directory.
    """
    if (not names or len(names) != len(set(names))
            or any(Path(name).name != name or name in ('', '.', '..')
                   or not (unpacked / name).is_file() for name in names)):
        raise ValueError('수집 산출물의 파일명·완전성을 확인할 수 없습니다')
    destination.mkdir(parents=True, exist_ok=True)
    old_files = [path for path in destination.iterdir()
                 if path.is_file() and path.suffix.lower() in ('.docx', '.doc')]
    previous = Path(tempfile.mkdtemp(prefix=f'.{destination.name}.recovery-', dir=destination.parent))
    attempted = []
    try:
        for old in old_files:
            os.replace(old, previous / old.name)
        for name in names:
            # Record the attempted placement before the syscall; a signal can be
            # delivered after the rename has happened and before Python returns.
            attempted.append(name)
            os.replace(unpacked / name, destination / name)
    except BaseException as original:
        failures = []
        for name in attempted:
            try:
                (destination / name).unlink(missing_ok=True)
            except BaseException as error:
                failures.append(f'{name}: {type(error).__name__}: {error}')
        for old in old_files:
            backup = previous / old.name
            if backup.exists() or backup.is_symlink():
                try:
                    os.replace(backup, old)
                except BaseException as error:
                    failures.append(f'{old.name}: {type(error).__name__}: {error}')
        if failures:
            message = f'수집 입력 복구를 마치지 못했습니다. 보존 위치: {previous}; ' + '; '.join(failures)
            logger.error(message)
            if isinstance(original, Exception):
                raise OSError(message) from original
            add_note = getattr(original, 'add_note', None)
            if callable(add_note):
                add_note(message)
            else:
                original.args = (*original.args, message)
        else:
            shutil.rmtree(previous)
        raise
    else:
        shutil.rmtree(previous)
