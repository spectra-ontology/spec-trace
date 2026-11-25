"""Preserved native search paths for filters outside the lexical cache scope.

The WG native chunk search and native TDoc grouping keep their original score
units and CE behavior. This explicit compatibility path is traced by the caller.
"""
from __future__ import annotations

import math
from typing import Mapping
import cr_tdoc_ranking
from cr_tdoc_ranking import build_filter, _finite, _slim, K

def search_text(self, query: str, top_k: int = None, filters: dict = None, *, native_reranker=None) -> list[dict]:
    """시맨틱 검색 + 필터 (+ optional cross-encoder rerank)."""
    if top_k is None:
        top_k = self.config.top_k

    query_vector = self.embed_query(query)

    # 필터: 다섯 WG 공용 `cr_tdoc_ranking.build_filter` 하나로 만든다(값 하나는 MatchValue, 배열 칸은
    # 원소 포함, 값이 목록이면 MatchAny). 정답 모집단도 같은 뜻으로 거르므로 검색과 판정의 필터가 갈라지지 않는다.
    query_filter = cr_tdoc_ranking.build_filter(filters)

    # Reranker 사용 시 더 많은 후보 retrieve, 아니면 top_k만
    retrieve_k = max(self.config.rerank_retrieve_k, top_k) if self.config.use_rerank else top_k
    results = self.qdrant.query_points(
        collection_name=self.config.collection_name,
        query=query_vector,
        query_filter=query_filter,
        limit=retrieve_k,
        with_payload=True,
    )

    # Reranker 적용
    candidates = []
    for hit in results.points:
        if isinstance(hit.score, bool) or not isinstance(hit.score, (int, float)) or not math.isfinite(hit.score):
            raise ValueError("Search score must be a finite number")
        p = hit.payload or {}
        c = dict(p)
        c["bi_score"] = round(hit.score, 4)
        candidates.append(c)

    if self.config.use_rerank and candidates:
        from llm_quality.reranker_module import Reranker
        rr = native_reranker if native_reranker is not None else Reranker.shared()
        candidates = rr.rerank(query, candidates, top_k=top_k, mode="rerank_only")
    else:
        candidates = candidates[:top_k]

    formatted = []
    for c in candidates:
        formatted.append({
            "score": round(c.get("rerank_score", c.get("bi_score", 0)), 4),
            "bi_score": c.get("bi_score", 0),
            "rerank_score": round(c.get("rerank_score", 0), 4) if "rerank_score" in c else None,
            "chunkId": c.get("chunkId", ""),
            "chunkType": c.get("chunkType", ""),
            "tdocNumber": c.get("tdocNumber", ""),
            "specNumber": c.get("specNumber", ""),
            "crNumber": c.get("crNumber", ""),
            "category": c.get("category", ""),
            "workItem": c.get("workItem", ""),
            "meeting": c.get("meeting", ""),
            "strategy": c.get("strategy", ""),
            "chunkIndex": c.get("chunkIndex", 0),
            "totalChunks": c.get("totalChunks", 0),
            "tokenCount": c.get("tokenCount", 0),
            "clausesAffected": c.get("clausesAffected", []),
            "sectionIds": c.get("sectionIds", []),
            "text_preview": (c.get("text", "") or "")[:200],
        })

    return formatted


def search_content(self, query: str, top_k: int = None, filters: dict = None, *, native_reranker=None) -> list[dict]:
    """시맨틱 검색 (+ optional cross-encoder rerank)."""
    if top_k is None:
        top_k = self.config.top_k

    query_vector = self.embed_query(query)

    # Reranker 사용 시 더 많은 후보 retrieve, 아니면 top_k만
    retrieve_k = max(self.config.rerank_retrieve_k, top_k) if self.config.use_rerank else top_k
    results = self.qdrant.query_points(
        collection_name=self.config.collection_name,
        query=query_vector,
        query_filter=build_filter(filters),
        limit=retrieve_k,
        with_payload=True,
    )

    # Reranker 적용
    candidates = []
    for hit in results.points:
        if isinstance(hit.score, bool) or not isinstance(hit.score, (int, float)) or not math.isfinite(hit.score):
            raise ValueError("Search score must be a finite number")
        p = hit.payload or {}
        c = dict(p)
        c["bi_score"] = round(hit.score, 4)
        candidates.append(c)

    if self.config.use_rerank and candidates:
        from llm_quality.reranker_module import Reranker
        rr = native_reranker if native_reranker is not None else Reranker.shared()
        # reranker_module._doc_text는 'text'/'content' 둘 다 지원
        candidates = rr.rerank(query, candidates, top_k=top_k, mode="rerank_only")
    else:
        candidates = candidates[:top_k]

    formatted = []
    for c in candidates:
        formatted.append({
            "score": round(c.get("rerank_score", c.get("bi_score", 0)), 4),
            "bi_score": c.get("bi_score", 0),
            "rerank_score": round(c.get("rerank_score", 0), 4) if "rerank_score" in c else None,
            "chunkId": c.get("chunkId", ""),
            "chunkType": c.get("chunkType", ""),
            "tdocNumber": c.get("tdocNumber", ""),
            "specNumber": c.get("specNumber", ""),
            "category": c.get("category", ""),
            "strategy": c.get("strategy", ""),
            "release": c.get("release", ""),
            "clausesAffected": c.get("clausesAffected", ""),
            "tokenCount": c.get("tokenCount", 0),
            "content_preview": (c.get("text") or c.get("content", ""))[:200],
        })

    return formatted


def rank_tdocs(client, query: str, filters: Mapping | None = None, k: int = K) -> dict:
    """서로 다른 TDoc 상위 k 개와 그 청크 payload, 청크 단위 상위 k 개의 TDoc.

    반환: ranked_tdocs(순위대로) · scores(TDoc 별 대표 청크 점수) · payloads(TDoc → 대표 청크 payload 목록) ·
    chunk_tdocs(청크 단위 상위 k 개의 TDoc, 중복 그대로) · pool_size(후보 청크 수).
    """
    cfg = client.config
    vec = client.embed_query(query)
    qf = build_filter(filters)
    if cfg.use_rerank:
        pool_k = max(cfg.rerank_retrieve_k, k)
        pts = client.qdrant.query_points(cfg.collection_name, query=vec, query_filter=qf, limit=pool_k,
                                         with_payload=True).points
        cands = [dict(h.payload or {}, bi_score=_finite(h.score)) for h in pts]
        if cands:
            from llm_quality.reranker_module import Reranker
            cands = Reranker.shared().rerank(query, cands, top_k=len(cands), mode="rerank_only")
        chunk_tdocs = [c.get("tdocNumber", "") for c in cands[:k]]
        ranked, scores, payloads = [], {}, {}
        for c in cands:
            t = c.get("tdocNumber", "")
            if t in scores:
                continue
            ranked.append(t)
            scores[t] = round(_finite(c.get("rerank_score", c["bi_score"])), 4)
            payloads[t] = [_slim(c)]
            if len(ranked) == k:
                break
        return dict(ranked_tdocs=ranked, scores=scores, payloads=payloads, chunk_tdocs=chunk_tdocs,
                    pool_size=len(cands))
    chunk_pts = client.qdrant.query_points(cfg.collection_name, query=vec, query_filter=qf, limit=k,
                                           with_payload=["tdocNumber"]).points
    groups = client.qdrant.query_points_groups(cfg.collection_name, query=vec, query_filter=qf,
                                               group_by="tdocNumber", limit=k, group_size=1,
                                               with_payload=True).groups
    ranked, scores, payloads = [], {}, {}
    for g in groups:
        t = str(g.id)
        ranked.append(t)
        scores[t] = round(_finite(g.hits[0].score), 4) if g.hits else None
        payloads[t] = [_slim(h.payload) for h in g.hits]
    return dict(ranked_tdocs=ranked, scores=scores, payloads=payloads,
                chunk_tdocs=[(p.payload or {}).get("tdocNumber", "") for p in chunk_pts], pool_size=None)
