#!/usr/bin/env python3
"""os_residue.py — 추출 잔재 분류 규칙의 공통 선언과 제거.

대상
----
3GPP 기고자가 작업 폴더 전체를 압축하면 문서 외에 OS·워드가 생성한 파일도 포함될 수 있다.
macOS 의 AppleDouble 리소스 포크(`__MACOSX/._X.docx`, 평면 추출 시 `._X.docx`),
워드의 소유자 파일(`~$X.docx`), `.DS_Store` 류가 해당한다. 이 파일들은 문서가 아니지만
문서 확장자를 사용하므로 첫 `.docx` 를 선택하는 파서에서 문서로 처리될 수 있다.

공통 선언의 이유
----------------
분류 규칙은 저장소 게이트와 RAN 추출기 10벌의 `CLEANUP_PATTERNS` 에 따로 선언되어 있었다.
게이트는 잔재 0을 요구하므로 추출기가 다른 규칙을 사용하면 제거되지 않은 파일로 인해
해당 파티션의 검사가 계속 실패할 수 있다. 분류 규칙을 이 모듈에 통합하고
검사기와 제거기가 같은 선언을 참조하도록 한다.

이름에 따른 판정
----------------
코퍼스 규모에서 처리할 수 있도록 파일 내용을 열지 않고 이름으로 판정한다.
`classify()` 는 분류를, `purge()` 는 제거를 담당한다.

정리 대상 선택
--------------
호출자는 수집 원본 `source/` 를 배포된 바이트 그대로 보존하고, 재생성 가능한 파생 추출
트리를 `purge(tree)` 에 전달한다. `derived/` 와 대체 추출 목적지의 선택은 호출자가 맡는다.
`purge()` 는 전달받은 트리 아래에 이름 규칙을 적용한다. 원본·파생 경로의 구분과
원본 보존은 호출자의 대상 경로 선택으로 집행한다.
남아 있는 아카이브(`leftover_archive`)는 추출 미완료의 증거이며 이 분류에 포함하지 않는다.
별도 성격의 문제이므로 다른 검사에서 다룬다.
"""
from __future__ import annotations

import shutil
from pathlib import Path

#: macOS 가 아카이브 안에 만드는 부속 디렉토리. 디렉토리 전체를 제거한다.
FORK_DIR = "__MACOSX"

#: 포크 디렉토리 밖으로 평면으로 풀린 리소스 포크의 접두.
FORK_PREFIX = "._"

#: 워드가 문서를 열어 둔 동안 만드는 소유자 파일의 접두.
WORD_LOCK_PREFIX = "~$"

#: OS 가 디렉토리마다 생성하는 부속 파일. 이름이 정확히 일치할 때만이다.
JUNK_NAMES = (".DS_Store", "Thumbs.db", "desktop.ini")

#: 접두로 판정하는 갈래. 갈래 이름은 `classify()` 가 돌려주는 값이다.
_PREFIXES = ((FORK_PREFIX, "fork_file"), (WORD_LOCK_PREFIX, "word_lock_file"))

#: macOS 잔재의 분류 목록. 분류별 집계를 수행하는 사용 코드는 이 선언을 참조한다.
#: 호출부에서 이름을 하드코딩하면 분류 추가 후 새 항목이 집계에서 누락될 수 있다.
FORK_LANES = ("fork_dir", "fork_member", "fork_file")

# 분류 규칙이 비면 검사와 제거가 수행되지 않아도 통과할 수 있다.
# 미검사와 잔재 0을 구분하기 위해 import 시점에 빈 선언을 거부한다.
assert FORK_DIR and JUNK_NAMES and all(p for p, _ in _PREFIXES), "잔재 어휘가 비었다"


def classify(name: str) -> str | None:
    """파일·디렉토리 이름 하나가 어느 갈래의 잔재인가. 잔재가 아니면 None.

    이름만 본다. 경로 안에 포크 디렉토리가 있는지까지 보려면 `classify_path()` 를 쓴다.
    """
    if name == FORK_DIR:
        return "fork_dir"
    if name in JUNK_NAMES:
        return name
    for prefix, lane in _PREFIXES:
        if name.startswith(prefix):
            return lane
    return None


def classify_path(rel: Path | str) -> str | None:
    """경로 하나의 잔재 분류. 포크 디렉토리 **안**의 파일은 포크 멤버로 분류한다.

    한 파일이 두 분류에 해당할 수 있으므로 우선순위를 정한다. 포크 디렉토리 안의 `._`
    파일은 `fork_member` 이며 `fork_file` 이 아니다. 중복 집계하면 합이 분모를 넘는다.
    """
    parts = Path(rel).parts
    if FORK_DIR in parts[:-1]:
        return "fork_member"
    return classify(parts[-1]) if parts else None


def purge(tree: Path) -> int:
    """추출한 트리에서 잔재를 제거하고 삭제한 항목 수를 반환한다.

    호출자는 수집 원본을 보존하고 정리할 파생 추출 트리를 `tree` 로 전달한다.
    이 함수는 전달받은 트리 아래의 이름으로 잔재를 판정한다. 원본·파생 경로의 구분은
    호출자의 대상 경로 선택으로 집행한다.

    분류는 `classify_path()` 를 사용한다. 분류와 집계에 다른 규칙을 적용하면 포크 멤버가
    독립 잔재로 중복 집계되어 합이 분모를 넘을 수 있다.
    포크 디렉토리는 전체를 1건으로 세고 내부 항목은 따로 세지 않는다.

    부모 디렉토리를 먼저 삭제해 자식 경로가 사라지지 않도록 깊은 경로부터 처리한다.
    삭제에 실패한 항목은 집계하지 않고 계속한다. 제거는 최선 노력 방식이며,
    남은 잔재는 게이트(`scripts/common/data-integrity/check_corpus_extraction_residue.py`)에서 검사한다.
    """
    tree = Path(tree)
    if not tree.exists():
        return 0
    removed = 0
    for path in sorted(tree.rglob("*"), key=lambda q: len(q.parts), reverse=True):
        lane = classify_path(path.relative_to(tree))
        if lane is None or lane == "fork_member":
            continue
        try:
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink()
        except OSError:
            continue
        removed += 1
    return removed

# 수동으로 선언한 `FORK_LANES` 와 실제 판정 결과가 달라지지 않도록
# import 시점에 두 집합의 일치를 확인한다.
assert set(FORK_LANES) == {
    classify(FORK_DIR),
    classify(FORK_PREFIX + "x"),
    classify_path(f"{FORK_DIR}/x"),
}, "포크 갈래 열거가 판정이 내는 값과 다르다"
