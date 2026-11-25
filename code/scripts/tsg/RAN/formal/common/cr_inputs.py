"""cr_inputs.py — Phase 4·8에서 사용할 CR 문서와 변환 누락 입력을 수집한다.

입력은 Phase 0의 변환 산출물인
`data/corpus/tsg/RAN/formal/change-requests/{WG}/derived/Rel-*/TSG/{팩}/`이다.
폴더 아래를 재귀 탐색하며 Release·팩·경로 순서로 반환한다.

ZIP 형식의 `.docx`를 본문 후보로 모은다. `.doc`와 ZIP 형식이 아닌 `.docx`는
인접한 변환본이 있으면 그 변환본을 사용하고, 없으면 `unconverted`로 반환한다.
같은 문서의 배포본·변환본은 공통 `docx_pick` 선택 규칙으로 중복을 제거한다.

Phase 8의 `without_covers`는 팩 표지를 제외한다. 개별 CR 표지는 같은 폴더의
같은 TDoc 번호에 본문 후보가 있을 때만 제외하여 유일한 문서를 보존한다.
`selected_unconverted`는 이 규칙과 명시된 첨부·서식 없음 제외를 적용하고,
선택적으로 호출 WG의 CR 식별 함수로 필수 입력을 판별한다. 호출자는 처리할 수
없는 필수 입력을 확인한 뒤 파싱·최종 결과 게시 여부를 결정한다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(_ROOT / "scripts" / "common" / "common"))
import axis  # noqa: E402
import docx_pick  # noqa: E402

#: 파서가 직접 읽는 Word 문서 확장자.
DOCUMENT_SUFFIX = ".docx"
#: Phase 0에서 DOCX로 변환하는 문서 확장자.
CONVERTED_SUFFIX = ".doc"
#: DOCX의 ZIP 파일 시그니처. 확장자가 같아도 이 형식인지 검사한다.
ZIP_MAGIC = b"PK"
#: 팩 전체의 표지 파일 이름 끝.
PACK_COVER_SUFFIX = "_cover.docx"
#: 파일 이름 안의 Tdoc 번호(`R4-2115878` · `RP-182887`). 같은 CR의 표지와 본문을 연결하는 기준이다.
_TDOC_IN_NAME = re.compile(r"(?<![A-Za-z0-9])(R[1-5P])[-_ ]?(\d{6,7})(?!\d)", re.I)


def derived_dir(wg: str) -> Path:
    """한 WG 의 Phase-0 CR 산출 디렉토리."""
    return axis.tree_path("corpus", wg=wg, doc_type="change-requests", slot="derived")


def _converted(doc: Path) -> bool:
    return ((doc.parent / (doc.stem + DOCUMENT_SUFFIX)).exists()
            or (doc.parent / (doc.name + DOCUMENT_SUFFIX)).exists())


def _zip_container(doc: Path) -> bool:
    """파일 시작 바이트가 ZIP 시그니처와 일치하는지 검사한다."""
    try:
        with doc.open("rb") as fh:
            return fh.read(len(ZIP_MAGIC)) == ZIP_MAGIC
    except OSError:
        return False


def collect(root: Path) -> tuple[list[tuple[Path, str]], list[Path]]:
    """`(파일, 디렉토리 Release)` 목록과 읽을 수 없는 문서(변환본 없는 `.doc` · 열리지 않는 `.docx`) 목록.

    순서는 Release → 팩 → 경로.
    """
    files: list[tuple[Path, str]] = []
    unconverted: list[Path] = []
    for rel_dir in sorted(root.glob("Rel-*")):
        tsg_dir = rel_dir / "TSG"
        if not rel_dir.is_dir() or not tsg_dir.is_dir():
            continue
        for pack_dir in sorted(p for p in tsg_dir.iterdir() if p.is_dir()):
            for f in sorted(pack_dir.rglob("*")):
                if not f.is_file():
                    continue
                suffix = f.suffix.lower()
                if suffix == DOCUMENT_SUFFIX:
                    if _zip_container(f):
                        files.append((f, rel_dir.name))
                    elif not (f.parent / (f.name + DOCUMENT_SUFFIX)).exists():
                        unconverted.append(f)
                elif suffix == CONVERTED_SUFFIX and not _converted(f):
                    unconverted.append(f)
    kept = set(docx_pick.drop_shipped_twins([f for f, _ in files]))
    return [(f, rel) for f, rel in files if f in kept], unconverted


def _cr_key(path: Path) -> tuple[Path, str]:
    """같은 본문 후보 파일을 묶는 기준: 폴더와 이름 안 Tdoc 번호. Tdoc 번호가 없으면 파일 이름 자체."""
    m = _TDOC_IN_NAME.search(path.name)
    return path.parent, (f"{m.group(1).upper()}-{m.group(2)}" if m else path.name)


def without_covers(files: list[tuple[Path, str]]) -> list[tuple[Path, str]]:
    """`collect` 의 `(파일, Release)` 목록에서 팩 표지와 CR 표지를 뺀 목록. 순서는 그대로다."""
    files = [(f, rel) for f, rel in files if not f.name.lower().endswith(PACK_COVER_SUFFIX)]
    groups: dict[tuple[Path, str], list[Path]] = {}
    for f, _ in files:
        groups.setdefault(_cr_key(f), []).append(f)
    keep = {f for group in groups.values() for f in docx_pick.drop_covers(group)}
    return [(f, rel) for f, rel in files if f in keep]


def selected_unconverted(files: list[tuple[Path, str]], unconverted: list[Path], *,
                         project_root: Path, excluded_paths=(), resolve=None) -> list[Path]:
    """본문 선택에 남는 변환 실패 문서. 명시한 표지·첨부·서식 없음 제외를 유지한다.

    정상 문서와 함께 같은 폴더·TDoc 번호별 표지를 판별한다. `.doc` 팩 표지도
    `.docx` 팩 표지와 같이 제외한다. `resolve`가 있으면 해당 WG 파서가 실제 CR로
    식별한 문서만 반환하고, 생략하면 식별 여부와 관계없이 남은 문서를 반환한다.
    """
    excluded = set(excluded_paths)
    candidates = [path for path in unconverted
                  if str(path.relative_to(project_root)) not in excluded
                  and not path.with_suffix(DOCUMENT_SUFFIX).name.lower().endswith(PACK_COVER_SUFFIX)]
    combined = [(path, rel) for path, rel in files
                if str(path.relative_to(project_root)) not in excluded]
    combined.extend((path, "") for path in candidates)
    selected = {path for path, _ in without_covers(combined)}
    return [path for path in candidates if path in selected
            and (resolve is None or resolve(path) is not None)]


def pack_id(path: Path, root: Path) -> str:
    """파일이 든 팩(`RP-NNNNNN`). 팩 안 하위 폴더에 든 파일도 팩 디렉토리 이름을 받는다."""
    return path.relative_to(root).parts[2]
