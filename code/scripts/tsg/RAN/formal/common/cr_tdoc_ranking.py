#!/usr/bin/env python3
"""cr_tdoc_ranking.py: Phase-8 CR 검색 CQ 를 TDoc 단위 순위로 재고 `cr_cq_gold` 정답으로 판정한다.

검증기(`RAN{n}/phase-8/validation/01_validate_search.py`)의 `SearchClient` 를 그대로 받아 쓴다. 질의 임베딩 ·
컬렉션 · rerank 여부는 그 클라이언트의 설정을 따른다. 필터는 이 모듈의 `build_filter` 하나가 만들고 검증기
`search()` 도 같은 함수를 부른다: 칸 값이 하나면 `MatchValue`(배열 칸은 원소 포함), 값이 목록이면 `MatchAny`
(목록 값 중 하나와 같으면 통과)다.

> 주의: CR 하나는 헤더 청크와 본문 청크 여럿으로 나뉜다. 청크 상위 10 개를 그대로 세면 한 CR 의 청크가
> 여러 자리를 차지해 서로 다른 CR 이 몇 건만 남는다. CQ 는 「어느 CR 이 답인가」를 묻으므로 순위는 TDoc
> 단위로 매긴다: 같은 TDoc 은 가장 높은 청크 한 자리만 차지하고, 서로 다른 TDoc 10 개를 돌려준다.
> 비교를 위해 청크 단위 상위 10 개의 TDoc 과 그 적중 수도 함께 남긴다.
>
> 주의: 실제 밀집검색 점수와 cross-encoder 점수는 공통 검색기가 원형 청크에서 구한다.
> TDoc 순위를 정한 결합 점수는 별도 칸으로 보존하고, 출력의 score 는 rerank 모드의 실제
> cross-encoder 점수 또는 일반 모드의 실제 밀집검색 점수로 유지한다.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Mapping

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import cr_cq_gold  # noqa: E402

K = cr_cq_gold.K
#: 판정에 쓰지 않는 큰 칸. 결과 파일에 본문 글을 싣지 않는다.
_DROP = ("text", "content")


def build_filter(filters: Mapping | None):
    """CQ 필터를 Qdrant 필터로 바꾼다. 필터가 없으면 None.

    값이 목록이면 `MatchAny`(여러 spec 중 하나처럼 「이 중 하나」 조건), 아니면 `MatchValue` 다. 칸끼리는
    모두 만족해야 한다(must). 정답 쪽 `cr_cq_gold.satisfies_filters` 가 같은 뜻으로 모집단을 거른다.
    """
    from qdrant_client.http.models import FieldCondition, Filter, MatchAny, MatchValue
    conds = [FieldCondition(key=k, match=MatchAny(any=list(v)) if isinstance(v, (list, tuple)) else MatchValue(value=v))
             for k, v in (filters or {}).items()]
    return Filter(must=conds) if conds else None


def _slim(payload: Mapping | None) -> dict:
    return {k: v for k, v in (payload or {}).items() if k not in _DROP}


def _finite(score) -> float:
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score):
        raise ValueError("Search score must be a finite number")
    return float(score)


def search_formatted(client, query: str, top_k=None, filters: Mapping | None = None,
                     *, content_profile: bool = False) -> list[dict]:
    """WG search() direct path and criteria ranking share one product facade."""
    from cr_search_adapter import search_formatted as shared_search
    return shared_search(client, query, top_k=top_k, filters=filters,
                         content_profile=content_profile)


def rank_tdocs(client, query: str, filters: Mapping | None = None, k: int = K) -> dict:
    """Return shared TDoc ranking with distinct native and fusion score units."""
    from cr_search_adapter import rank_tdocs as shared_rank
    return shared_rank(client, query, filters=filters, k=k)


def evaluate_with_gold(client, cq: Mapping, gold: Mapping[str, Mapping]) -> dict:
    """CQ 하나를 TDoc 단위로 검색하고 `cr_cq_gold.evaluate` 로 판정한 결과(검증기 evaluation 칸 꼴)."""
    cq_id = cq["cq_id"]
    entry = gold.get(cq_id)
    if entry is None:
        raise KeyError(f"{cq_id}: cr_cq_gold 에 기준이 없다")
    # 주의: 기준은 질의 글과 필터를 보고 정했다. 데이터셋의 질의나 필터가 바뀌었는데 기준이 그대로면
    # 다른 질문을 옛 기준으로 재게 되므로 둘이 다르면 판정하지 않고 멈춘다.
    if entry["query"] != cq["query"] or dict(entry["filters"]) != dict(cq.get("filters") or {}):
        raise ValueError(f"{cq_id}: 데이터셋 질의·필터와 cr_cq_gold 기준의 질의·필터가 다르다")
    r = rank_tdocs(client, cq["query"], cq.get("filters") or {})
    res = cr_cq_gold.evaluate(entry, r["ranked_tdocs"], r["payloads"])
    lenient, strict = set(entry["lenient_tdocs"]), set(entry["strict_tdocs"])
    chunk_distinct = list(dict.fromkeys(r["chunk_tdocs"]))
    if res["status"] == "NOT_TESTABLE":
        res["status"], res["skip_reason"] = "SKIP", "not_testable"
    ranked = r["ranked_tdocs"][:K]
    res.update({
        "top_score": r["scores"].get(ranked[0], 0.0) if ranked else 0.0,
        "ranked_tdocs": ranked,
        "hit_tdocs_lenient": [t for t in ranked if t in lenient],
        "hit_tdocs_strict": [t for t in ranked if t in strict],
        "universe_size": entry["universe_size"], "n_lenient": entry["n_lenient"], "n_strict": entry["n_strict"],
        "p0": entry["p0"], "draws": entry["draws"], "alpha": entry["alpha"],
        "criteria": entry["criteria"], "amended_post_hoc": entry["amended_post_hoc"],
        "chunk_unit": {"distinct_tdocs": len(chunk_distinct),
                       "hits_lenient": sum(t in lenient for t in chunk_distinct)},
        "rerank_pool_size": r["pool_size"],
        "search_provenance": r.get("provenance", {}),
        "score_kind": r.get("score_kinds", {}).get(ranked[0]) if ranked else None,
    })
    return res
