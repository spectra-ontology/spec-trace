#!/usr/bin/env python3
"""test_chunker_identity.py — 청크 분할 후 문서 내 식별자의 유일성을 확인한다.

시험 목적
---------
적재 시 포인트 식별자는 `(tdocNumber, chunkIndex)`로 결정된다. 한 문서에서
chunkIndex가 중복되면 뒤에 적재한 청크가 앞의 청크를 덮어쓴다. 예외가 발생하지 않고
적재 개수도 맞지만 일부 본문은 검색되지 않는다. 기존 조사에서 컬렉션의 1,345개
포인트에 동일 식별자 충돌이 확인되었다(`_v2Split` 식별자 오염).

원인은 한도 초과 청크를 분할하면서 각 분할 청크에 1..k를 다시 부여한 것이다.
부모가 문서의 15번째 청크였다면 분할 청크의 번호 1,2,3은 기존 1,2,3번 청크와 겹친다.

검증 항목:
  · 수정 전 방식(분할 청크마다 1..k 부여)의 입력에서 중복을 검출하는지 확인한다.
    중복이 있는 입력에도 시험이 통과하는 문제를 방지하기 위한 반례다.
  · 수정한 함수의 산출에 중복이 없는지, 분할이 필요하지 않으면 기존 식별자를
    유지하는지 확인한다. 불필요하게 식별자를 변경하면 재적재가 필요하다.

Usage:
    python3 scripts/common/common/test_chunker_identity.py

Exit: 0 = 전부 통과 / 1 = 하나라도 실패
LLM 호출: 없음
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.chunker import (  # noqa: E402
    HARD_MAX_DEFAULT,
    count_tokens,
    enforce_hard_max,
    renumber_chunk_indices,
    split_existing_chunk,
)

FAILS: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"{'✅' if ok else '🔴'} {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        FAILS.append(name)


def _dup(chunks: list[dict]) -> list[int]:
    seen: dict[int, int] = {}
    for c in chunks:
        seen[c["chunkIndex"]] = seen.get(c["chunkIndex"], 0) + 1
    return sorted(i for i, n in seen.items() if n > 1)


def _doc(n_small: int, oversized_at: int) -> list[dict]:
    """작은 청크 n개 중 한 자리만 한도를 넘긴 문서."""
    big = "word " * (HARD_MAX_DEFAULT * 3)
    out = []
    for i in range(1, n_small + 1):
        out.append({
            "chunkId": f"R1-2400001-{i:03d}",
            "chunkIndex": i,
            "totalChunks": n_small,
            "tdocNumber": "R1-2400001",
            "content": big if i == oversized_at else f"body {i}",
        })
    return out


def main() -> int:
    doc = _doc(20, oversized_at=15)
    assert count_tokens(doc[14]["content"]) > HARD_MAX_DEFAULT

    # ① 중복 검출을 확인하기 위해 수정 전 번호 부여 방식으로 입력을 구성한다.
    naive = [dict(c) for c in doc[:14]]
    for idx, part in enumerate(split_existing_chunk(dict(doc[14])), 1):
        part["chunkIndex"] = idx          # 수정 전 방식: 분할 청크마다 1..k를 다시 부여
        naive.append(part)
    naive.extend(dict(c) for c in doc[15:])
    check("중복 검출(수정 전 방식)", bool(_dup(naive)),
          f"중복된 청크 번호 {_dup(naive)}")

    # ② 고친 enforce_hard_max 의 산출에는 겹침이 없다.
    fixed = enforce_hard_max([dict(c) for c in doc], hard_max=HARD_MAX_DEFAULT)
    check("분할 후 청크 번호 유일", not _dup(fixed),
          f"청크 {len(doc)}→{len(fixed)} · 겹침 {_dup(fixed)}")
    check("청크 번호 연속", [c["chunkIndex"] for c in fixed] == list(range(1, len(fixed) + 1)))
    check("totalChunks 갱신", all(c["totalChunks"] == len(fixed) for c in fixed))
    check("chunkId 유일", len({c["chunkId"] for c in fixed}) == len(fixed))
    check("토큰 한도 준수", all(count_tokens(c["content"]) <= HARD_MAX_DEFAULT for c in fixed))

    # ③ 분할이 필요하지 않으면 청크 번호를 유지한다.
    plain = _doc(5, oversized_at=0)
    before = [c["chunkIndex"] for c in plain]
    after = [c["chunkIndex"] for c in enforce_hard_max([dict(c) for c in plain])]
    check("미분할 문서는 청크 번호 유지", before == after, f"{before} → {after}")

    # ④ 0-기반 목록을 1-기반으로 옮기지 않는다(시작값은 입력을 따른다).
    zero = [{"chunkId": f"x-{i}", "chunkIndex": i, "totalChunks": 3,
             "tdocNumber": "R1-2400002", "content": "b"} for i in range(0, 3)]
    renumber_chunk_indices(zero)
    check("시작값 보존", [c["chunkIndex"] for c in zero] == [0, 1, 2],
          str([c["chunkIndex"] for c in zero]))

    # ⑤ 첫 청크가 쪼개져도 시작값은 쪼개기 전 목록을 따른다. 조각 번호 1 이 그 자리에 들어가므로
    #    쪼갠 뒤 목록에서 시작값을 읽으면 0-기반 목록이 1-기반으로 옮겨진다.
    for start in (0, 1):
        head = [dict(c, chunkIndex=c["chunkIndex"] - 1 + start) for c in _doc(4, oversized_at=1)]
        out = enforce_hard_max(head, hard_max=HARD_MAX_DEFAULT)
        check(f"첫 청크 분할 뒤 시작값 {start} 보존",
              len(out) > len(head) and [c["chunkIndex"] for c in out] == list(range(start, start + len(out))),
              str([c["chunkIndex"] for c in out]))

    if FAILS:
        print(f"\n🔴 실패 {len(FAILS)}: {', '.join(FAILS)}")
        return 1
    print("\n✅ 전부 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
