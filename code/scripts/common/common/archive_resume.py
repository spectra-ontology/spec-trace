"""완전히 해제한 임시 트리와 기존 결과를 대조해 누락 파일만 게시한다.

Spec: docs/tsg/RAN/formal/RAN1/phase-10/step1_data-collection.md
Ontology: 원본 아카이브와 파생 파일의 내용을 대조하며 기존 파일을 보존한다.
Cycle: Phase-10 회의 ZIP 최초 해제·부분 해제 재개·중첩 ZIP 처리.
배경: 내용이 있는 목적지를 완료로 간주하면 바뀐 원본과 누락 파일을 놓친다.
사용: WG 진입점이 해제·정리·잔재 판정 함수를 명시적으로 전달한다.
LLM 호출: 없음.
"""

from pathlib import Path
import tempfile


def _same_file_bytes(first: Path, second: Path) -> bool:
    if first.stat().st_size != second.stat().st_size:
        return False
    with first.open("rb") as left, second.open("rb") as right:
        while True:
            block = left.read(1 << 20)
            if block != right.read(1 << 20):
                return False
            if not block:
                return True


def resume_archive(archive: Path, destination: Path, downloaded: bool = True,
                   *, extract, cleanup) -> dict:
    """기존 전체 경로를 먼저 검사하고, 충돌이 없을 때 누락 파일만 추가한다.

    바이트·파일 종류·심볼릭 링크 충돌이면 기존 결과와 추가 파일을 보존한다.
    게시 중 중단으로 생긴 부분 결과는 다음 실행에서 같은 방식으로 대조한다.
    """
    failed = {"extracted": 0, "skipped": 0, "failed": 1}
    try:
        if destination.is_symlink() or (destination.exists() and not destination.is_dir()):
            raise ValueError(f"추출 목적지는 일반 디렉토리여야 합니다: {destination}")
        if any(parent.is_symlink() for parent in destination.parents):
            raise ValueError(f"추출 목적지 상위의 심볼릭 링크를 보존합니다: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".extract-", dir=destination.parent) as temporary:
            stage = Path(temporary)
            stats = extract(archive, stage, downloaded)
            if not stats["extracted"]:
                return stats
            cleanup(stage)
            entries = sorted(stage.rglob("*"))
            missing = []
            for item in entries:
                if item.is_symlink() or not (item.is_dir() or item.is_file()):
                    raise ValueError(f"일반 파일·폴더가 아닌 아카이브 항목: {item.relative_to(stage)}")
                relative = item.relative_to(stage)
                target = destination / relative
                current = destination
                for part in relative.parts:
                    current /= part
                    if current.is_symlink():
                        raise ValueError(f"추출 경로의 심볼릭 링크를 보존합니다: {current}")
                    if current != target and current.exists() and not current.is_dir():
                        raise ValueError(f"추출 경로를 차지한 파일을 보존합니다: {current}")
                if target.exists():
                    if (item.is_dir() != target.is_dir()
                            or (item.is_file() and (not target.is_file() or not _same_file_bytes(item, target)))):
                        raise ValueError(f"아카이브와 다른 기존 내용을 보존합니다: {target}")
                elif item.is_file():
                    missing.append((item, target))
            destination.mkdir(exist_ok=True)
            for item in entries:
                if item.is_dir():
                    (destination / item.relative_to(stage)).mkdir(parents=True, exist_ok=True)
            for item, target in missing:
                target.parent.mkdir(parents=True, exist_ok=True)
                # 경합 중 같은 경로가 생겨도 덮어쓰지 않는다.
                target.hardlink_to(item)
            if not missing:
                stats["extracted"], stats["skipped"] = 0, 1
            return stats
    except Exception as error:
        print(f"  [WARN] 추출 완료 대조 실패: {archive.name} — {error}")
        return failed


def extract_inner_archives(root: Path, depth: int = 0, max_depth: int = 10,
                           *, resume, cleanup, classify_path, causes) -> dict:
    """중첩 ZIP을 한 번씩 대조하고, 깊이 한도에 남은 ZIP은 실패로 집계한다."""
    stats = {"extracted": 0, "failed": 0}
    stats.update({cause: 0 for cause in causes})
    inner = sorted(
        path for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() == ".zip"
        and classify_path(path.relative_to(root)) is None
    )
    # 이미 해제된 중첩 트리는 해당 ZIP을 처리한 재귀 호출이 담당한다.
    destinations = {archive.parent / archive.stem for archive in inner}
    inner = [archive for archive in inner
             if not any(parent in destinations for parent in archive.parents if parent != root)]
    if depth >= max_depth:
        if inner:
            print(f"  [WARN] 안쪽 ZIP 해제 깊이 한도 {max_depth}: {root}")
            stats["failed"] = len(inner)
        return stats
    for archive in inner:
        destination = archive.parent / archive.stem
        result = resume(archive, destination, downloaded=False)
        complete = result["extracted"] or result["skipped"]
        result.pop("skipped", None)
        for key, value in result.items():
            stats[key] = stats.get(key, 0) + value
        if complete:
            cleanup(destination)
            nested = extract_inner_archives(
                destination, depth + 1, max_depth, resume=resume, cleanup=cleanup,
                classify_path=classify_path, causes=causes)
            for key, value in nested.items():
                stats[key] = stats.get(key, 0) + value
    return stats
