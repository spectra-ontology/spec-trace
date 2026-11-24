#!/usr/bin/env python3
"""ts_release_slots.py — TS Release의 원본 문서와 변환 문서를 함께 선택한다.

`source`에는 3GPP 배포 문서를, `derived`에는 DOC를 DOCX로 변환한 결과를 저장한다.
이 모듈은 source의 규격·Release 폴더를 기준으로 두 디렉토리의 본문 후보를 모은다.
같은 문서의 배포본과 변환본이 함께 있으면 배포본을 우선한다.
WG별 파서가 이 선택 규칙을 공통으로 사용한다.

Spec 참조: docs/common/standards/directory_structure_guide.md (source|derived 슬롯 불변식)
LLM 호출: 없음
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

# 표지와 정리판이 함께 배포된 수정 표시판은 공통 docx_pick 규칙으로 선별한다.
_FORMAL_COMMON = str(Path(__file__).resolve().parents[1])
if _FORMAL_COMMON not in sys.path:
    sys.path.insert(0, _FORMAL_COMMON)
import docx_pick  # noqa: E402

SLOTS = ("source", "derived")


def twin_slot(path: Path) -> Path | None:
    """경로 끝에서 찾은 마지막 source/derived 구성요소를 서로 바꿔 반환한다.

    호출자는 WG 뒤에 source 또는 derived가 있는 코퍼스 경로를 전달한다.
    예를 들어 `TS/RAN3/source/38.401/Rel-16`은 해당 derived 경로가 된다.
    두 이름 중 어느 것도 없는 경로는 None을 반환한다.
    """
    parts = list(path.parts)
    for i in range(len(parts) - 1, -1, -1):
        if parts[i] in SLOTS:
            parts[i] = SLOTS[1] if parts[i] == SLOTS[0] else SLOTS[0]
            return Path(*parts)
    return None


def release_docx(rel_dir: Path) -> list[Path]:
    """source의 Release 폴더와 대응하는 derived에서 DOCX 후보를 모은다.

    확장자의 대소문자와 관계없이 일반 파일만 고른다. 확장자를 뺀 파일명이 같고
    확장자의 대소문자만 다른
    후보가 한 슬롯에 있으면 기존 소문자 `.docx`를 우선하고, 두 슬롯에 있으면
    source 파일을 우선한다. 선택한 실제 파일명은 바꾸지 않으며 결과는 이름순이다.
    """
    by_name: dict[str, Path] = {}
    twin = twin_slot(rel_dir)
    if twin is not None and twin.is_dir():
        for f in sorted(twin.iterdir()):
            if f.is_file() and f.suffix.lower() == ".docx":
                by_name[f.stem + ".docx"] = f
    if rel_dir.is_dir():
        for f in sorted(rel_dir.iterdir()):
            if f.is_file() and f.suffix.lower() == ".docx":
                by_name[f.stem + ".docx"] = f
    return sorted(by_name.values())


def orphan_conversions(rel_dir: Path, removing: set[str] = frozenset()) -> list[Path]:
    """대응하는 원본 DOC가 남지 않는 derived의 DOCX 경로를 반환한다.

    source의 판본을 교체하는 호출자가 이전 변환본을 함께 정리할 수 있도록 돕는다.
    이 함수는 목록만 반환하며 파일을 삭제하지 않는다. `removing`은 호출자가 삭제할
    source 파일의 실제 이름이다. 삭제 전에 같은 목록을 계산할 수 있어 dry-run에도 쓴다.
    """
    twin = twin_slot(rel_dir)
    if twin is None or not twin.is_dir():
        return []
    kept = {f.stem for f in rel_dir.iterdir()
            if f.is_file() and f.suffix.lower() == ".doc" and f.name not in removing} if rel_dir.is_dir() else set()
    return [f for f in sorted(twin.iterdir())
            if f.is_file() and f.suffix.lower() == ".docx" and f.stem not in kept]


def body_parts(rel_dir: Path) -> list[Path]:
    """Release의 본문 DOCX 후보를 선택한다. 후보가 없으면 빈 목록을 반환한다.

    `_cover`가 있으면 표지를 제외한 나머지 파트를 선택한다. 그 외의 표지와 정리판이
    함께 있는 수정 표시판은 `docx_pick.prefer_body`로 제외한다. `_cover`가 없고 여러
    후보에 `_s` 파트가 있으면 해당 파트를 모두 선택한다. 이 조건에도 해당하지 않으면
    이름에 `_`가 없는 마지막 파일을, 그런 파일도 없으면 첫 후보를 선택한다.

    Phase-3·7·11이 이 함수를 함께 사용해 KG 절과 Vector DB 청크의 문서 선택을 맞춘다.
    """
    docx = release_docx(rel_dir)
    if not docx:
        return []
    covers = [d for d in docx if d.stem.lower().endswith("_cover")]
    if covers:
        return docx_pick.prefer_body([d for d in docx if not d.stem.lower().endswith("_cover")])
    docx = docx_pick.prefer_body(docx)
    s_parts = [d for d in docx if "_s" in d.stem]
    if len(docx) > 1 and s_parts:
        return s_parts
    singles = [d for d in docx if "_" not in d.stem]
    return [singles[-1]] if singles else [docx[0]]


def rel_key(name: str) -> int:
    """Rel-숫자 형식에서 정수 Release 번호를 반환한다. 다른 형식은 -1을 반환한다."""
    m = re.fullmatch(r"Rel-(\d+)", name)
    return int(m.group(1)) if m else -1


def release_dirs(spec_dir: Path) -> list[Path]:
    """규격 폴더 아래 본문 후보가 있는 Rel-* 디렉토리를 Release 번호순으로 반환한다.

    규격 폴더 바로 아래의 파일은 Release별 입력에 포함하지 않는다.
    """
    if not spec_dir.is_dir():
        return []
    rels = [c for c in spec_dir.iterdir() if c.is_dir() and rel_key(c.name) >= 0]
    return [c for c in sorted(rels, key=lambda c: rel_key(c.name)) if body_parts(c)]


def latest_release(spec_dir: Path) -> tuple[str, list[Path]] | None:
    """본문 후보가 있는 가장 높은 Release 번호의 이름과 파트 목록을 반환한다.

    선택 기준은 source의 Release 폴더이며, 본문 파일은 대응하는 derived에서도 찾는다.
    본문 후보가 있는 Release가 없으면 None을 반환한다.
    """
    rels = release_dirs(spec_dir)
    if not rels:
        return None
    return rels[-1].name, body_parts(rels[-1])


@dataclass
class ReleaseScope:
    """WG의 TS에서 본문 후보를 찾은 범위와 건너뛴 범위·이유를 기록한다."""
    pairs: list[tuple[str, str, Path]] = field(default_factory=list)    # (spec, release, rel_dir)
    skipped: list[tuple[str, str, str]] = field(default_factory=list)   # (spec, release, reason)
    excluded_specs: list[tuple[str, str]] = field(default_factory=list)  # (spec, reason)
    scope_specs: set[str] = field(default_factory=set)


def release_scope(wg_source: Path, has_body: Callable[[Path], list]) -> ReleaseScope:
    """source의 규격·Release 폴더를 본문 후보 유무에 따라 분류한다.

    본문 후보가 있는 Release는 pairs에, 후보가 없는 Release는 skipped에 기록한다.
    Rel-* 폴더가 없는 규격은 excluded_specs에 기록한다. scope_specs는 교차 인용을
    해석할 대상 규격 목록이며, 본문 후보가 있는 Release를 하나 이상 가진 규격만 포함한다.
    문서 파싱의 성공 여부는 이 분류 이후 각 파서에서 검사한다.

    `has_body`는 WG 파서가 사용하는 본문 파트 선택 함수다.
    """
    scope = ReleaseScope()
    for p in sorted(wg_source.iterdir()):
        if not p.is_dir() or p.name == "metadata":
            continue
        rel_dirs = sorted((c for c in p.iterdir() if c.is_dir() and rel_key(c.name) >= 0),
                          key=lambda c: rel_key(c.name))
        if not rel_dirs:
            scope.excluded_specs.append((p.name, "no Rel-* subdir (legacy/Phase-0 gap)"))
            continue
        for rel_dir in rel_dirs:
            if has_body(rel_dir):
                scope.pairs.append((p.name, rel_dir.name, rel_dir))
                scope.scope_specs.add(p.name)
            else:
                scope.skipped.append((p.name, rel_dir.name, "no body docx (not extracted)"))
    return scope
