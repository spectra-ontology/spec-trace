#!/usr/bin/env python3
"""qdrant_generation.py — `--recreate`의 적재·삭제·교체 순서를 관리한다.

무엇인가
--------
적재기의 `--recreate` 는 "컬렉션을 새 세대로 바꾼다"는 뜻이다. 컬렉션을 먼저 지우고 새로
만들면, 그 뒤 임베딩 · 조회 · 업서트 가운데 하나만 실패해도 기존 세대가 사라진 채 실행이
끝난다. 이 모듈은 벡터 설정에 따라 적재 후 기존 포인트를 정리하거나 임시 컬렉션을 사용한다.

    absent   : 컬렉션이 없다. 새로 만들고 바로 적재한다(지울 기존 세대가 없다).
    in_place : 컬렉션이 있고 벡터 설정(차원 · 거리)이 같다. 기존 컬렉션에 새 세대를
               업서트한다. 모두 적재한 뒤 `prune_outside`가 이번 실행에서 유지할 ID에
               없는 포인트를 지운다. point ID는 청크 신원에서 결정되므로 같은 청크의
               포인트는 같은 ID로 덮어쓴다.
    staging  : 컬렉션이 있고 벡터 설정이 다르다. 임시 컬렉션(`staging_name`)에 모두
               적재하고 개수를 확인한 뒤 `promote_staging`이 원래 이름의 컬렉션으로
               복사한다. 복사 도중 실패하면 임시 컬렉션은 남는다.

무엇을 하지 않는가
------------------
- 대량 적재 전체를 하나의 원자 연산으로 만들지 않는다. 업서트 도중 실패하면 이미 처리한
  ID에는 새 값이, 나머지에는 이전 값이 남고 예외가 발생한다. 같은 명령을 다시 실행하면
  같은 ID를 덮어써 적재를 마칠 수 있다.
- 빈 새 세대로 교체하지 않는다. `prune_outside` 는 남길 id 가 0 이면 지우지 않고 예외를
  올린다. 빈 입력을 정상 교체로 받을지는 부르는 쪽이 그 전에 판정한다.
- 별칭(alias)을 쓰지 않는다. 적재기와 질의기는 컬렉션 이름을 직접 부르므로, 이름을 별칭으로
  바꾸면 목록 조회에서 실제 이름과 별칭이 갈린다.
"""
from __future__ import annotations

from typing import Callable, Iterable

STAGING_SUFFIX = "__replace_staging"

ABSENT = "absent"
IN_PLACE = "in_place"
STAGING = "staging"


def _direct(fn, *a, **kw):
    return fn(*a, **kw)


def check_scroll_progress(offset, seen: set) -> None:
    """계속 조회할 offset이 반복되면 종료하여 같은 페이지의 무한 조회를 막는다."""
    if offset is not None:
        if offset in seen:
            raise ValueError("Qdrant scroll의 continuation offset이 반복되었습니다")
        seen.add(offset)


def staging_name(name: str) -> str:
    """교체용 임시 컬렉션 이름을 반환한다."""
    return name + STAGING_SUFFIX


def _distance_name(distance) -> str:
    return str(getattr(distance, "value", distance)).lower()


def plan_replace(client, name: str, size: int, distance) -> str:
    """교체 방식을 고른다. 컬렉션을 바꾸지 않고 읽기만 한다.

    단일 벡터의 차원과 거리 척도가 모두 같으면 IN_PLACE를 반환한다. 이름 붙은
    다중 벡터(dict)이거나 차원·거리 값이 없거나 다르면 STAGING을 반환한다. 실제 모델과
    입력 처리 방식의 일치는 호출자가 임베딩 선언·구축 기록으로 확인한다.
    """
    names = {c.name for c in client.get_collections().collections}
    if name not in names:
        return ABSENT
    vectors = client.get_collection(name).config.params.vectors
    cur_size = getattr(vectors, "size", None)
    cur_dist = getattr(vectors, "distance", None)
    if cur_size == size and cur_dist is not None and _distance_name(cur_dist) == _distance_name(distance):
        return IN_PLACE
    return STAGING


def prepare_staging(client, name: str, create: Callable[[str], None], call=_direct) -> str:
    """임시 컬렉션을 새로 만든다. 이전 실행의 같은 임시 컬렉션은 먼저 지운다."""
    stage = staging_name(name)
    names = {c.name for c in client.get_collections().collections}
    if stage in names:
        call(client.delete_collection, stage)
    create(stage)
    return stage


def prune_outside(client, name: str, keep_ids: Iterable, scroll_filter=None,
                  call=_direct, scroll_batch: int = 10000, delete_batch: int = 1000) -> int:
    """`name`에서 `keep_ids`에 없는 포인트를 지우고 삭제한 수를 반환한다.

    `scroll_filter` 를 주면 그 필터에 걸리는 점만 후보로 본다(chunkType 부분 교체처럼 교체
    범위가 컬렉션 일부일 때). 조회 중에는 삭제할 ID만 모으고, 전체 조회가 끝난 뒤 삭제한다.
    """
    from qdrant_client.http import models

    keep = {int(i) if isinstance(i, int) or str(i).isdigit() else str(i) for i in keep_ids}
    if not keep:
        raise ValueError(f"{name}: 남길 새 세대 id 가 0 이라 기존 점을 지우지 않는다")
    stale: list = []
    offset = None
    seen_offsets = set()
    while True:
        got, offset = call(client.scroll, collection_name=name, scroll_filter=scroll_filter,
                           limit=scroll_batch, offset=offset,
                           with_payload=False, with_vectors=False)
        check_scroll_progress(offset, seen_offsets)
        for p in got:
            pid = int(p.id) if isinstance(p.id, int) else str(p.id)
            if pid not in keep:
                stale.append(pid)
        if offset is None:
            break
    for i in range(0, len(stale), delete_batch):
        call(client.delete, collection_name=name,
             points_selector=models.PointIdsList(points=stale[i:i + delete_batch]))
    return len(stale)


def _count(client, name: str, call=_direct) -> int:
    return call(client.count, collection_name=name, exact=True).count


def promote_staging(client, stage: str, name: str, create: Callable[[str], None],
                    expected: int, call=_direct, batch: int = 256) -> int:
    """임시 컬렉션의 포인트를 원래 이름의 컬렉션으로 복사하고 복사한 수를 반환한다.

    1. 임시 컬렉션의 포인트 수가 `expected`와 다르면 기존 컬렉션을 유지하고 멈춘다.
    2. 기존 컬렉션을 지우고 `create`로 다시 만든 뒤, 임시 컬렉션의 벡터와 payload를
       그대로 복사한다. 임베딩은 다시 계산하지 않는다.
    3. 두 컬렉션의 포인트 수가 같을 때만 임시 컬렉션을 지운다. 다르면 임시 컬렉션을 남긴다.
    """
    from qdrant_client.http.models import PointStruct

    staged = _count(client, stage, call)
    if staged != expected or expected == 0:
        raise RuntimeError(f"{stage}: 옆 컬렉션 점 {staged} ≠ 이번 실행이 올린 점 {expected}"
                           " — 원 컬렉션을 바꾸지 않는다")
    names = {c.name for c in client.get_collections().collections}
    if name in names:
        call(client.delete_collection, name)
    create(name)
    moved = 0
    offset = None
    seen_offsets = set()
    while True:
        got, offset = call(client.scroll, collection_name=stage, limit=batch, offset=offset,
                           with_payload=True, with_vectors=True)
        check_scroll_progress(offset, seen_offsets)
        if got:
            call(client.upsert, collection_name=name,
                 points=[PointStruct(id=p.id, vector=p.vector, payload=p.payload) for p in got])
            moved += len(got)
        if offset is None:
            break
    final = _count(client, name, call)
    if final != staged:
        raise RuntimeError(f"{name}: 옮긴 뒤 점 {final} ≠ 옆 컬렉션 점 {staged}"
                           f" — 옆 컬렉션 {stage} 를 남긴다")
    call(client.delete_collection, stage)
    return moved
