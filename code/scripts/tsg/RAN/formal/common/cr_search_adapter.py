#!/usr/bin/env python3
"""cr_search_adapter.py — connect shared CR search to native score provenance.

Spec: Phase-8 shared CR retrieval and unchanged CQ evaluation contracts.
Ontology: Existing canonical CR chunk payloads and same-chunk filters.
Cycle: Product search integration.
배경: Share ranking while preserving original query, payload and score units.
사용: Called through cr_tdoc_ranking by the WG wrappers.
LLM 호출: None; existing local encoder and native CE are supplied by the client.
"""
from __future__ import annotations

import importlib
import json
import math
from pathlib import Path
import weakref

from cr_hybrid_search import FILTER_FIELDS, SearchCache, resolve_cache_spec, rank_bm25f


def _finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('A finite actual native score is required')
    return float(value)


def _freeze(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def _source_path(config):
    path = Path(config.chunks_path).expanduser()
    if not path.is_absolute():
        root = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
        path = root / path
    return path.absolute()


def _cache(client):
    config = client.config
    key = (config.collection_name, str(_source_path(config)),
           str(getattr(config, 'search_cache_root', None)),
           str(getattr(config, 'search_manifest_path', None)),
           getattr(config, 'search_manifest_sha256', None))
    existing = getattr(client, '_cr_product_search_cache', None)
    if existing is not None:
        if existing[0] != key:
            raise ValueError('Search client cache configuration changed after activation')
        existing[1].check_current()
        return existing[1]
    spec = resolve_cache_spec(collection_name=config.collection_name, source_path=_source_path(config),
                              cache_root=getattr(config, 'search_cache_root', None),
                              manifest_path=getattr(config, 'search_manifest_path', None),
                              manifest_sha256=getattr(config, 'search_manifest_sha256', None))
    cache = SearchCache(spec)
    weakref.finalize(client, cache.close)
    client._cr_product_search_cache = (key, cache)
    return cache


def _policy():
    # A selected policy is a separate installed source, never a fallback weight.
    policy = importlib.import_module('cr_search_policy')
    if not callable(getattr(policy, 'rank_candidates', None)) or not hasattr(policy, 'TITLE_BOOST'):
        raise ValueError('An explicitly selected shared search policy must be installed')
    return policy


class _BatchEightPredict:
    """Keep native pair construction and prediction defaults with a small batch."""
    def __init__(self, model):
        self.model = model

    def predict(self, pairs, **kwargs):
        if kwargs != {'show_progress_bar': False}:
            raise ValueError('Native CE predict invocation changed')
        return self.model.predict(pairs, batch_size=8, show_progress_bar=False)


def _native_reranker(client):
    factory = getattr(client, 'cr_search_reranker_factory', None)
    if factory is not None:
        return factory()
    existing = getattr(client, '_cr_product_native_reranker', None)
    if existing is not None:
        return existing
    from llm_quality.reranker_module import Reranker
    shared = Reranker.shared()
    if shared.model_name != 'BAAI/bge-reranker-base':
        raise ValueError('The measured existing native CE model is required')
    model = shared._load()
    if model.max_length != 512 or str(next(model.model.parameters()).dtype) != 'torch.float32':
        raise ValueError('Native max512/fp32 CE identity differs')
    # The shared model stays unchanged; only this native wrapper owns the proxy.
    reranker = Reranker(model_name=shared.model_name)
    reranker._model = _BatchEightPredict(model)
    client._cr_product_native_reranker = reranker
    return reranker


def _point(hit, cache, filters):
    payload = dict(hit.payload or {})
    if not payload.get('chunkId') or not payload.get('tdocNumber'):
        raise ValueError('Actual Qdrant hit requires canonical chunk and TDoc identity')
    if 'bi_score' in payload or 'rerank_score' in payload:
        raise ValueError('Canonical payload collides with native score annotations')
    canonical = cache.check_dense_payload(payload, filters)
    if canonical is False:
        raise ValueError('Qdrant payload differs from the canonical source')
    point_id = getattr(hit, 'id', None)
    if point_id is None:
        raise ValueError('Actual Qdrant point identifier is required')
    point_id = point_id if type(point_id) in (str, int) else str(point_id)
    return {'id': point_id, 'point_id': point_id, 'score': _finite(hit.score), 'payload': payload}


def _ce(points, query, reranker):
    candidates = [dict(point['payload'], bi_score=point['score']) for point in points]
    if not candidates:
        return {}, {}, []
    original = {id(candidate): index for index, candidate in enumerate(candidates)}
    ranked = reranker.rerank(query, candidates, top_k=len(candidates), mode='rerank_only')
    if len(ranked) != len(points) or {id(x) for x in ranked} != set(original):
        raise ValueError('Native CE changed the complete candidate universe')
    scores = {original[id(x)]: _finite(x['rerank_score']) for x in ranked}
    order = [original[id(x)] for x in ranked]
    if order != sorted(range(len(points)), key=lambda index: (-scores[index], index)):
        raise ValueError('Native CE stable order differs')
    by_tdoc, representatives = {}, {}
    for candidate in ranked:
        index = original[id(candidate)]
        actual = {key: value for key, value in candidate.items() if key not in ['bi_score', 'rerank_score']}
        if _freeze(actual) != _freeze(points[index]['payload']):
            raise ValueError('Native CE changed canonical payload fields')
        tdoc = candidate['tdocNumber']
        if tdoc not in by_tdoc:
            by_tdoc[tdoc], representatives[tdoc] = scores[index], points[index]
    return by_tdoc, representatives, [points[index]['payload']['tdocNumber'] for index in order]


def _enrich(client, cache, query, vector, filters, tdoc, base_filter, reranker):
    from qdrant_client.http.models import Filter, FieldCondition, MatchValue
    conditions = [FieldCondition(key='tdocNumber', match=MatchValue(value=tdoc))]
    if base_filter is not None:
        conditions.insert(0, base_filter)
    points = client.qdrant.query_points(collection_name=client.config.collection_name, query=vector,
                                         query_filter=Filter(must=conditions), limit=1, with_payload=True).points
    if len(points) != 1:
        raise ValueError('Selected eligible TDoc has no actual filtered dense representative')
    point = _point(points[0], cache, filters)
    if point['payload']['tdocNumber'] != tdoc:
        raise ValueError('Output enrichment returned a different TDoc')
    score = None
    if reranker is not None:
        scores, _, _ = _ce([point], query, reranker)
        score = scores[tdoc]
    return point, score


def _unsupported_fields(filters):
    return sorted(str(key) for key in (filters or {}) if key not in FILTER_FIELDS)


def _fallback_trace(filters):
    return {'search_policy': 'legacy_native_unsupported_filter',
            'fallback_reason': 'cache_filter_scope',
            'unsupported_filter_fields': _unsupported_fields(filters)}


def rank_tdocs(client, query: str, filters=None, k: int = 10) -> dict:
    """Return selected TDocs with native output scores and distinct rank scores."""
    if not isinstance(query, str) or type(k) is not int or k < 0:
        raise ValueError('Original query string and nonnegative integer k required')
    filters = dict(filters or {})
    use_rerank = bool(client.config.use_rerank)
    empty = {'ranked_tdocs': [], 'scores': {}, 'payloads': {}, 'chunk_tdocs': [], 'pool_size': 0,
             'ranked_rows': [], 'score_kinds': {}, 'provenance': {'originalQuery': query, 'originalFilters': filters,
             'useRerank': use_rerank, 'search_policy': 'shared_selected_product_policy',
             'configuredNativeCeBatchSize': 8, 'frozenDiagnosticCeBatchSize': 1,
             'batch1BitwiseEqualityMeasured': False,
             'displayEnrichmentUsedForRanking': False}}
    if not k:
        return empty
    if _unsupported_fields(filters):
        from cr_search_legacy import rank_tdocs as native_rank
        result = native_rank(client, query, filters=filters, k=k)
        result['score_kinds'] = {tdoc: 'native_ce' if use_rerank else 'raw_dense_cosine'
                                 for tdoc in result['ranked_tdocs']}
        result['provenance'] = dict(_fallback_trace(filters), originalQuery=query,
                                     originalFilters=filters, useRerank=use_rerank)
        return result
    cache = _cache(client)
    empty['provenance']['cacheGeneration'] = {
        key: cache.generation[key] for key in ('sourceSha256', 'codeSha256', 'schema', 'collection')}
    empty['provenance']['cachePath'] = str(cache.path)
    features = cache.lexical_features(query, filters, include_body=True)
    if features['positiveEvidenceDocuments'] == 0:
        empty['provenance']['generalWholeEligibleSourceLexicalAbstention'] = True
        return empty
    policy = _policy()
    from cr_tdoc_ranking import build_filter
    query_filter = build_filter(filters)
    vector = client.embed_query(query)
    limit = client.config.rerank_retrieve_k
    if type(limit) is not int or limit <= 0:
        raise ValueError('Configured native dense candidate limit must be positive')
    raw = client.qdrant.query_points(collection_name=client.config.collection_name, query=vector,
                                      query_filter=query_filter, limit=limit, with_payload=True).points
    points = [_point(hit, cache, filters) for hit in raw]
    previous, chunk_ids, dense_scores, dense_representatives = math.inf, set(), {}, {}
    for point in points:
        payload, score = point['payload'], point['score']
        if score > previous or payload['chunkId'] in chunk_ids:
            raise ValueError('Original dense order or unique chunk universe differs')
        previous = score
        chunk_ids.add(payload['chunkId'])
        tdoc = payload['tdocNumber']
        if tdoc not in dense_scores:
            dense_scores[tdoc], dense_representatives[tdoc] = score, point
    reranker = _native_reranker(client) if use_rerank else None
    ce_scores, ce_representatives = None, {}
    chunk_tdocs = [point['payload']['tdocNumber'] for point in points]
    if use_rerank:
        ce_scores, ce_representatives, chunk_tdocs = _ce(points, query, reranker)
    lexical_rows = rank_bm25f(features, title_boost=policy.TITLE_BOOST, dense_scores=dense_scores)
    for row in lexical_rows:
        row['bm25f16'] = row['bm25f'] if policy.TITLE_BOOST == 16 else None
        row['tdoc'] = row['tdocNumber']
        row['titleTF'], row['headerTF'] = row['titleTf'], row['headerTf']
    frozen_points, frozen_ce = _freeze(points), _freeze(ce_scores)
    frozen_lexical = _freeze(lexical_rows)
    chosen = policy.rank_candidates(lexical_rows, points, ce_scores, k=k)
    if (_freeze(points) != frozen_points or _freeze(ce_scores) != frozen_ce
            or _freeze(lexical_rows) != frozen_lexical):
        raise ValueError('Ranking policy mutated frozen native feature inputs')
    if not isinstance(chosen, list) or len(chosen) > k:
        raise ValueError('Selected policy must return a bounded list of ranked feature rows')
    eligible = {row['tdocNumber'] for row in lexical_rows}
    selected = tuple(row['tdocNumber'] for row in chosen)
    if len(set(selected)) != len(selected) or not set(selected) <= eligible:
        raise ValueError('Policy selected duplicate or ineligible TDocs')
    result = dict(empty, ranked_tdocs=list(selected), scores={}, payloads={}, score_kinds={},
                  chunk_tdocs=chunk_tdocs[:k], pool_size=len(points), ranked_rows=[])
    enrichment_count = 0
    for row, tdoc in zip(chosen, selected):
        rank_score = _finite(row['rank_score'])
        rank_kind = row['rank_score_kind']
        if not isinstance(rank_kind, str) or not rank_kind:
            raise ValueError('Selected policy must identify rank score units')
        if use_rerank and tdoc in ce_representatives:
            point, ce_score = ce_representatives[tdoc], ce_scores[tdoc]
        elif not use_rerank and tdoc in dense_representatives:
            point, ce_score = dense_representatives[tdoc], None
        else:
            point, ce_score = _enrich(client, cache, query, vector, filters, tdoc, query_filter, reranker)
            enrichment_count += 1
        raw_dense = _finite(point['score'])
        native_score = _finite(ce_score) if use_rerank else raw_dense
        score_kind = 'native_ce' if use_rerank else 'raw_dense_cosine'
        payload = dict(point['payload'])
        augmented = dict(payload, bi_score=raw_dense)
        if use_rerank:
            augmented['rerank_score'] = ce_score
        # Keep the existing criteria payload projection and expose audit separately.
        result['payloads'][tdoc] = [{key: value for key, value in augmented.items() if key not in ['text', 'content']}]
        result['scores'][tdoc] = round(native_score, 4)
        result['score_kinds'][tdoc] = score_kind
        result['ranked_rows'].append({'tdocNumber': tdoc, 'score': native_score, 'score_kind': score_kind,
                                      'rank_score': rank_score, 'rank_score_kind': rank_kind,
                                      'raw_dense_cosine': raw_dense, 'ce_score': ce_score,
                                      'point_id': point['point_id'], 'payload': payload})
    if tuple(result['ranked_tdocs']) != selected or tuple(row['tdocNumber'] for row in result['ranked_rows']) != selected:
        raise ValueError('Display enrichment changed the frozen selected ranking')
    if _freeze(points) != frozen_points or _freeze(ce_scores) != frozen_ce:
        raise ValueError('Display enrichment changed original fusion feature inputs')
    cache.check_current()
    result['provenance'].update(nativeDensePoolLimit=limit, nativeDensePoolSize=len(points),
                                actualNativeCeUsed=bool(use_rerank and (len(points) + enrichment_count)),
                                nativeCeBatchSize=8 if use_rerank and (len(points) + enrichment_count) else None,
                                nativeCeScoredPairs=(len(points) + enrichment_count) if use_rerank else 0,
                                nativeCeRerankCalls=(int(bool(points)) + enrichment_count) if use_rerank else 0,
                                ceFeatureScope='original_native_dense_pool_only' if use_rerank else None,
                                displayEnrichedTdocs=enrichment_count, rankFeaturesFrozenBeforeDisplayEnrichment=True,
                                generalWholeEligibleSourceLexicalAbstention=False)
    return result


def search_formatted(client, query: str, top_k=None, filters=None, *, content_profile=False) -> list[dict]:
    """Keep the direct native chunk contract with whole-source evidence tracing."""
    if top_k is None:
        top_k = client.config.top_k
    from cr_search_legacy import search_content, search_text
    native_search = search_content if content_profile else search_text
    use_rerank = bool(client.config.use_rerank)
    if _unsupported_fields(filters):
        native_reranker = _native_reranker(client) if use_rerank else None
        output = native_search(client, query, top_k=top_k, filters=filters,
                               native_reranker=native_reranker)
        client.last_search_provenance = dict(_fallback_trace(filters), originalQuery=query,
                                             originalFilters=dict(filters or {}),
                                             useRerank=use_rerank, resultUnit='native_chunk',
                                             configuredNativeCeBatchSize=8,
                                             frozenDiagnosticCeBatchSize=1,
                                             batch1BitwiseEqualityMeasured=False)
        for value in output:
            value.update(_fallback_trace(filters),
                         score_kind='native_ce' if use_rerank else 'raw_dense_cosine',
                         native_ce_batch_size=8 if use_rerank else None,
                         batch1_bitwise_equality_measured=False)
        return output
    cache = _cache(client)
    features = cache.lexical_features(query, filters, include_body=True)
    provenance = {'originalQuery': query, 'originalFilters': dict(filters or {}),
                  'useRerank': use_rerank, 'resultUnit': 'native_chunk',
                  'search_policy': 'native_chunk_contract_with_source_evidence_guard',
                  'configuredNativeCeBatchSize': 8, 'frozenDiagnosticCeBatchSize': 1,
                  'batch1BitwiseEqualityMeasured': False,
                  'eligibleDocuments': features['eligibleDocuments'],
                  'positiveEvidenceDocuments': features['positiveEvidenceDocuments'],
                  'cacheGeneration': {key: cache.generation[key] for key in
                                      ('sourceSha256', 'codeSha256', 'schema', 'collection')},
                  'cachePath': str(cache.path),
                  'generalWholeEligibleSourceLexicalAbstention': features['positiveEvidenceDocuments'] == 0}
    del features
    client.last_search_provenance = dict(provenance)
    if provenance['generalWholeEligibleSourceLexicalAbstention']:
        cache.check_current()
        return []
    native_reranker = _native_reranker(client) if use_rerank else None
    output = native_search(client, query, top_k=top_k, filters=filters,
                           native_reranker=native_reranker)
    cache.check_current()
    for value in output:
        value.update(score_kind='native_ce' if use_rerank else 'raw_dense_cosine',
                     search_policy=provenance['search_policy'],
                     native_ce_batch_size=8 if use_rerank else None,
                     batch1_bitwise_equality_measured=False)
    return output
