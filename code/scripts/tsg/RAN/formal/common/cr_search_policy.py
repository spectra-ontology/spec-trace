"""Portable linear source-coverage rank fusion candidate.

The same pending global alpha applies to dense and native CE modes. Coverage is
computed once from the complete eligible source population for the query and
filters. This module performs no retrieval, model inference or evaluation.
Native output scores remain the responsibility of the search adapter.
"""
from __future__ import annotations

from collections.abc import Mapping
import math

TITLE_BOOST = 16
RRF_K = 60
ALPHA = 0.5
POLICY_STATUS = 'selected_engineering_candidate_pending_native226'
WEIGHT_RULE = 'alpha_times_unrepresented_query_terms_neural_only_if_none'
RANK_SCORE_KIND = 'weighted_rrf60_not_cosine'


def _number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(label + ' must be a finite native scalar')
    return float(value)


def _tdoc(row):
    value = row.get('tdocNumber', row.get('tdoc'))
    if not isinstance(value, str) or not value:
        raise ValueError('A canonical TDoc identifier is required')
    if 'tdocNumber' in row and 'tdoc' in row and row['tdocNumber'] != row['tdoc']:
        raise ValueError('TDoc aliases differ')
    return value


def _bm25f(row):
    if 'bm25f16' in row and row['bm25f16'] is not None:
        score = _number(row['bm25f16'], 'BM25F16')
        if 'bm25f' in row and _number(row['bm25f'], 'BM25F') != score:
            raise ValueError('BM25F and BM25F16 aliases differ')
    else:
        score = _number(row['bm25f'], 'BM25F16')
    if score < 0:
        raise ValueError('Canonical BM25F must be nonnegative')
    return score


def coverage(lexical_rows):
    """Query terms and their represented union over ALL eligible TDocs."""
    keys, represented = set(), set()
    for row in lexical_rows:
        for field in ('termScores', 'titleTf', 'headerTf'):
            if not isinstance(row[field], Mapping):
                raise ValueError('Whole eligible lexical feature mappings required')
        keys.update(row['termScores'])
        represented.update(row['titleTf'])
        represented.update(row['headerTf'])
    if not represented <= keys:
        raise ValueError('Represented source terms escaped complete query terms')
    return len(keys), len(represented)


def effective_weight(lexical_rows, alpha=ALPHA):
    """One source-derived neural weight shared by every candidate for a query."""
    alpha = _number(alpha, 'Global alpha')
    if alpha < 0:
        raise ValueError('Global alpha must be nonnegative')
    query_terms, represented_terms = coverage(lexical_rows)
    return alpha * (query_terms - represented_terms) if represented_terms else 1.0


def _dense_documents(dense_points):
    dense, previous = {}, math.inf
    for position, point in enumerate(dense_points):
        score = _number(point['score'], 'Original raw dense cosine')
        tdoc = _tdoc(point['payload'])
        if score > previous:
            raise ValueError('Original native dense pool order differs')
        previous = score
        if tdoc not in dense:
            dense[tdoc] = (score, position)
    return dense


def _ce_order(ce_tdoc_scores, dense):
    """Keep native stable insertion order, or use explicit native TDoc ranks.

    Scalar mappings must already be ordered by native stable chunk CE followed
    by first occurrence of each TDoc. Equal CE scores are never retied by dense
    score or identifier. Exporter mappings carry explicit rank and ceScore.
    """
    if not isinstance(ce_tdoc_scores, Mapping) or set(ce_tdoc_scores) != set(dense):
        raise ValueError('CE TDoc scores must cover exactly the original dense pool')
    values, explicit_ranks = {}, {}
    metadata_mode = None
    for tdoc, value in ce_tdoc_scores.items():
        is_metadata = isinstance(value, Mapping)
        if metadata_mode is None:
            metadata_mode = is_metadata
        elif metadata_mode != is_metadata:
            raise ValueError('CE scalar insertion order and rank metadata cannot be mixed')
        if is_metadata:
            rank = value.get('rank')
            if type(rank) is not int or rank <= 0:
                raise ValueError('Explicit native CE rank must be a positive integer')
            if 'ceScore' in value:
                score = _number(value['ceScore'], 'Actual native CE score')
                if 'ce_score' in value and _number(value['ce_score'], 'Actual native CE score') != score:
                    raise ValueError('CE score aliases differ')
            else:
                score = _number(value['ce_score'], 'Actual native CE score')
            explicit_ranks[tdoc] = rank
        else:
            score = _number(value, 'Actual native CE score')
        values[tdoc] = score
    if metadata_mode:
        if set(explicit_ranks.values()) != set(range(1, len(values) + 1)):
            raise ValueError('Explicit native CE TDoc ranks must be a complete permutation')
        order = sorted(values, key=explicit_ranks.__getitem__)
    else:
        order = list(values)
    if any(values[left] < values[right] for left, right in zip(order, order[1:])):
        raise ValueError('Native CE rank order disagrees with actual CE scores')
    return order, values


def rank_candidates(lexical_rows, dense_points, ce_tdoc_scores, k=10):
    """Pure shared policy candidate; None selects dense and a dict selects CE.

    lexical_rows must contain the COMPLETE eligible canonical source population,
    with BM25F16, titleTf/headerTf and all-query termScores. Dense points and CE
    scores describe only the original native candidate pool. Display enrichment
    occurs after selection and never enters these inputs.
    """
    if k is not None and (type(k) is not int or k < 0):
        raise ValueError('k must be a nonnegative integer or None')
    lexical_rows = list(lexical_rows)
    dense = _dense_documents(dense_points)
    documents, lexical_scores = {}, {}
    for row in lexical_rows:
        tdoc = _tdoc(row)
        if tdoc in documents:
            raise ValueError('Whole eligible lexical population contains duplicate TDocs')
        documents[tdoc], lexical_scores[tdoc] = row, _bm25f(row)
    if set(dense) - set(documents):
        raise ValueError('Native dense candidates escaped the eligible source population')
    query_terms, represented_terms = coverage(lexical_rows)
    beta = effective_weight(lexical_rows)
    lexical_order = sorted(documents, key=lambda tdoc: (
        -lexical_scores[tdoc], -(dense[tdoc][0] if tdoc in dense else -math.inf), tdoc))
    lexical_ranks = {tdoc: rank for rank, tdoc in enumerate(lexical_order, 1)}
    if ce_tdoc_scores is None:
        neural = sorted(dense, key=lambda tdoc: (-dense[tdoc][0], dense[tdoc][1]))
        ce_values = None
        lane = 'dense'
    else:
        neural, ce_values = _ce_order(ce_tdoc_scores, dense)
        lane = 'ce'
    neural_ranks = {tdoc: rank for rank, tdoc in enumerate(neural, 1)}
    answer = []
    for tdoc, row in documents.items():
        positive = lexical_scores[tdoc] > 0
        lexical_rank = lexical_ranks[tdoc] if positive else None
        neural_rank = neural_ranks.get(tdoc)
        lexical_rrf = 1.0 / (RRF_K + lexical_rank) if lexical_rank is not None else 0.0
        neural_rrf = beta / (RRF_K + neural_rank) if neural_rank is not None else 0.0
        rank_score = lexical_rrf + neural_rrf
        if rank_score <= 0:
            continue
        answer.append(dict(row, tdocNumber=tdoc, tdoc=tdoc,
            bm25f=lexical_scores[tdoc], bm25f16=lexical_scores[tdoc],
            rank_score=rank_score, rank_score_kind=RANK_SCORE_KIND,
            lexical_rank=lexical_rank, neural_rank=neural_rank,
            lexical_rrf=lexical_rrf, neural_rrf=neural_rrf,
            raw_dense_cosine=dense[tdoc][0] if tdoc in dense else None,
            ce_score=ce_values[tdoc] if ce_values is not None and tdoc in ce_values else None,
            query_term_count=query_terms, represented_query_terms=represented_terms,
            effective_neural_weight=beta, alpha=ALPHA, lane=lane,
            neural_weight_rule=WEIGHT_RULE, policy_status=POLICY_STATUS))
    answer.sort(key=lambda row: (-row['rank_score'], -row['bm25f16'],
                -(row['raw_dense_cosine'] if row['raw_dense_cosine'] is not None else -math.inf),
                row['tdocNumber']))
    return answer if k is None else answer[:k]
