#!/usr/bin/env python3
"""cr_split_pieces.py: HARD_MAX 강제로 쪼갠 조각 가운데 너무 작은 조각을 이웃 조각에 원문 그대로 합친다.

> 주의: 공통 `enforce_hard_max` 는 한도를 넘는 청크를 행 · 글자 단위로 목표 크기만큼 잘라 나가고 남은
> 끝을 그대로 조각 하나로 둔다. 그래서 제목 줄과 표 두 행만 든 조각(RAN1 `R1-1810018` 의 6.3.3.1)이나
> 단어 중간에서 잘린 몇 글자짜리 조각(`gured for this serving cell. |`)이 따로 임베딩된다. 그런 조각은
> 검색에서 뜻을 갖지 못하고 앞 조각은 끝 글을 잃는다. 파서의 작은 청크 합치기(`MIN_CHUNK_TOKENS`)는 강제
> 분할 전에 돌아 이 조각을 보지 못한다.
>
> 그래서 쪼갠 뒤 글 토큰이 최소 크기보다 작은 조각은 앞 조각에, 앞 조각과 합쳐 한도를 넘으면 뒤 조각에
> 합친다. 합친 글은 원문에서 두 조각이 차지하던 구간 그대로라(사이 줄바꿈 · 단어 이음 포함) 글이 더해지거나
> 빠지지 않는다. 어느 쪽과 합쳐도 한도를 넘거나 조각을 원문에서 찾지 못하면 그대로 둔다.
>
> 주의: `enforce_hard_max` 의 조각은 원문을 빈틈없이 이어 자른 것이 아니다. 표 글은 행 단위로 자르며 원문
> 첫 줄을 조각마다 다시 붙이고(RAN4 `R4-1815668` 의 `Section 6.6.1.3.1`), 표 아닌 글은 앞 조각과 겹치게
> 자른다. 앞 조각 끝에서부터 찾으면 이런 조각은 원문에서 찾지 못해 합치기 전체가 빠진다. 그래서 겹친 조각은
> 앞 조각 시작 뒤에서 찾고, 첫 줄을 다시 붙인 조각은 그 줄을 뗀 나머지를 찾은 뒤 합친 글 앞에 그 줄을 다시
> 붙인다. 겹친 두 조각을 합치면 겹친 글은 한 번만 남는다.
"""
from __future__ import annotations

from typing import Callable, Sequence


def _spans(text: str, pieces: Sequence[str]) -> list[list] | None:
    """조각마다 [원문 시작, 원문 끝, 앞에 다시 붙인 첫 줄]. 하나라도 찾지 못하면 None."""
    head = text.split("\n", 1)[0] + "\n"
    out, cur, after = [], 0, 0
    for p in pieces:
        lead = ""
        at = text.find(p, cur)
        if at < 0:
            at = text.find(p, after)
        if at < 0 and out and head.strip() and p.startswith(head):
            lead = head
            at = text.find(p[len(head):], cur)
        if at < 0:
            return None
        end = at + len(p) - len(lead)
        out.append([at, end, lead])
        after, cur = at + 1, max(cur, end)
    return out


def merge_small_pieces(text: str, pieces: Sequence[str], limit: int, min_tokens: int,
                       count: Callable[[str], int]) -> list[str]:
    """`text` 를 쪼갠 `pieces` 에서 `min_tokens` 보다 작은 조각을 이웃에 합친 조각 목록(합친 조각도 `limit` 이하)."""
    pieces = list(pieces)
    if len(pieces) < 2:
        return pieces
    spans = _spans(text, pieces)
    if spans is None:
        return pieces
    stuck: set[int] = set()  # 합칠 수 없는 조각의 시작 자리
    while len(spans) > 1:
        small = next((i for i, (s, e, lead) in enumerate(spans)
                      if s not in stuck and count(lead + text[s:e]) < min_tokens), None)
        if small is None:
            break
        for j in (small - 1, small + 1):
            if 0 <= j < len(spans):
                lo, hi = min(small, j), max(small, j)
                joined = [spans[lo][0], max(spans[lo][1], spans[hi][1]), spans[lo][2]]
                if count(joined[2] + text[joined[0]:joined[1]]) <= limit:
                    spans[lo:hi + 1] = [joined]
                    break
        else:
            stuck.add(spans[small][0])
    return [lead + text[s:e] for s, e, lead in spans]


def merge_small_hardened(before: Sequence[dict], hardened: list[dict], limit: int, min_tokens: int,
                         count: Callable[[str], int], renumber: Callable[..., list[dict]],
                         base: int, text_key: str = "text") -> list[dict]:
    """`enforce_hard_max(before)` 의 결과 `hardened` 에서 같은 부모 조각끼리 작은 조각을 합친 목록.

    조각 ID 는 부모마다 앞에서부터 남은 조각 수만큼 쓰던 ID 를 그대로 쓰고, 조각 차례 · 개수와 목록 전체의
    자리표(`renumber`, 시작값 `base`)를 다시 매긴다. 합친 조각이 없으면 `hardened` 를 그대로 돌려준다.
    """
    parents = {c.get("chunkId"): c for c in before if isinstance(c.get("chunkId"), str)}
    out: list[dict] = []
    changed = False
    i = 0
    while i < len(hardened):
        c = hardened[i]
        pid = c.get("chunkId", "").rsplit("-", 1)[0] if c.get("_hardMaxEnforced") else None
        if pid not in parents:
            out.append(c)
            i += 1
            continue
        j = i
        while (j < len(hardened) and hardened[j].get("_hardMaxEnforced")
               and hardened[j].get("chunkId", "").rsplit("-", 1)[0] == pid):
            j += 1
        run = hardened[i:j]
        texts = [r.get(text_key) or "" for r in run]
        merged = merge_small_pieces(parents[pid].get(text_key) or "", texts, limit, min_tokens, count)
        if merged != texts:
            changed = True
            run = [dict(r) for r in run[:len(merged)]]
            for idx, (r, t) in enumerate(zip(run, merged), 1):
                r[text_key] = t
                r["tokenCount"] = count(t)
                r["chunkIndex"] = idx
                r["totalChunks"] = len(merged)
        out.extend(run)
        i = j
    if not changed:
        return hardened
    return renumber(out, base=base)
