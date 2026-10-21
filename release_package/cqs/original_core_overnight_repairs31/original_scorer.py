#!/usr/bin/env python3
"""Requested-field scoring with native-only ordering evidence.

Ordering columns may establish answer order without becoming requested answer
fields. Ranking eligibility comes from a complete captured population and an
explicit boundary policy. The scorer never infers question meaning or performance.
"""
from collections import Counter
from decimal import Decimal
import scorer as typed


def make_order_groups(contract, native_rows, projected_rows):
    collection = contract['collection']
    keys = collection.get('source_order_keys')
    kind = collection.get('kind')
    expected_policy = ('any_subset_at_boundary' if kind == 'top_k_boundary_ties'
                       else 'any_order_within_equal_keys')
    if (kind not in {'native_ordered_ties', 'top_k_boundary_ties'}
            or collection.get('tie_policy') != expected_policy
            or not isinstance(keys, list) or not keys
            or len(native_rows) != len(projected_rows)):
        raise ValueError('incomplete native ordering contract')
    names = set()
    for key in keys:
        if (not isinstance(key, dict) or not isinstance(key.get('source_column'), str)
                or key['source_column'] in names or key.get('direction') not in {'asc', 'desc'}):
            raise ValueError('invalid native ordering key')
        names.add(key['source_column'])
    for row in native_rows:
        for key in keys:
            name = key['source_column']
            if name not in row or type(row[name]) not in {str, int, float, Decimal, bool, type(None)}:
                raise ValueError('native ordering source absent or nonprimitive')
            if type(row[name]) in {int, float, Decimal}:
                typed.get_kernel().numeric_fraction(row[name])

    def compare(left, right):
        for key in keys:
            result = typed.compare_values(left[key['source_column']], right[key['source_column']], key['direction'])
            if result:
                return result
        return 0

    groups, prior = [], None
    for native, projected in zip(native_rows, projected_rows):
        order = compare(prior, native) if prior is not None else -1
        if order > 0:
            raise ValueError('captured native rows violate requested ordering')
        if not groups or order:
            groups.append([])
        groups[-1].append(projected)
        prior = native
    # A visible answer record cannot belong to two distinct ordering groups.
    # Otherwise the visible answer lacks enough identity to assign its rank.
    seen = {}
    for index, group in enumerate(groups):
        for row in group:
            token = typed.record_token(row, contract['required_fields'])
            if token in seen and seen[token] != index:
                raise ValueError('requested record has ambiguous native rank')
            if token in seen and kind == 'top_k_boundary_ties':
                raise ValueError('top-k population contains duplicate requested records')
            seen[token] = index
    return groups


def reference_prediction(contract, gold_rows):
    """Choose one permissible answer; retain the complete population as evidence."""
    if contract['collection']['kind'] == 'top_k_boundary_ties':
        limit = contract['cardinality_policy'].get('value')
        if type(limit) is not int or limit <= 0:
            raise ValueError('top-k size must be an explicitly declared positive integer')
        return gold_rows[:limit]
    return gold_rows


def score_top_k(contract, gold_rows, predicted_rows, *, diagnostic, order_groups):
    collection, cardinality = contract['collection'], contract['cardinality_policy']
    limit = collection.get('value')
    if (type(limit) is not int or limit <= 0 or cardinality.get('mode') != 'top_k'
            or cardinality.get('value') != limit
            or collection.get('tie_policy') != 'any_subset_at_boundary'
            or cardinality.get('tie_policy') != 'any_subset_at_boundary'
            or collection.get('within_tie_order') != 'any'
            or type(collection.get('require_rank_order')) is not bool):
        raise ValueError('top-k boundary contract is incomplete or inconsistent')
    if not diagnostic and contract.get('validation_status') != 'validated':
        raise ValueError('unvalidated task cannot supply benchmark scores')
    if order_groups is None or [r for group in order_groups for r in group] != gold_rows:
        raise ValueError('full native ranking population absent or differs from projected reference')
    fields = contract['required_fields']
    if not fields or len({f['name'] for f in fields}) != len(fields):
        raise ValueError('required field names must be nonempty and unique')
    tokens, _ = typed.project(gold_rows, fields, gold=True)
    if len(tokens) != len(set(tokens)):
        raise ValueError('top-k population contains duplicate requested records')
    observed, errors = typed.project(predicted_rows, fields)
    counts = Counter(observed)
    ng, np = min(limit, len(tokens)), len(observed)
    quotas, rank_by_token, remaining = [], {}, ng
    for rank, group in enumerate(order_groups):
        group_tokens = {typed.record_token(row, fields) for row in group}
        quota = min(remaining, len(group_tokens))
        quotas.append((group_tokens, quota))
        remaining -= quota
        rank_by_token.update((token, rank) for token in group_tokens)
    matched = sum(min(quota, len(group & set(observed))) for group, quota in quotas)
    exact = not errors and np == ng and all(value == 1 for value in counts.values())
    exact = exact and all(sum(counts[t] for t in group) == quota for group, quota in quotas)
    exact = exact and all(token in rank_by_token for token in observed)
    order_valid = not errors
    if collection['require_rank_order']:
        ranks = [rank_by_token.get(token, -1) for token in observed]
        order_valid = order_valid and all(r >= 0 for r in ranks) and ranks == sorted(ranks)
    precision = matched / np if np else (1.0 if not ng else 0.0)
    recall = matched / ng if ng else (1.0 if not np else 0.0)
    return {'diagnostic_only': diagnostic, 'exact': exact and order_valid,
            'precision': precision, 'recall': recall,
            'f1': 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
            'matched_records': matched, 'gold_records': ng, 'predicted_records': np,
            'reference_population_records': len(tokens), 'type_errors': errors,
            'cardinality_valid': np == ng, 'order_valid': order_valid}


def score(contract, gold_rows, predicted_rows, *, diagnostic=False, order_groups=None):
    if contract['collection']['kind'] == 'top_k_boundary_ties':
        return score_top_k(contract, gold_rows, predicted_rows,
                           diagnostic=diagnostic, order_groups=order_groups)
    if contract['collection']['kind'] != 'native_ordered_ties':
        return typed.score(contract, gold_rows, predicted_rows, diagnostic=diagnostic)
    if order_groups is None or [r for group in order_groups for r in group] != gold_rows:
        raise ValueError('native order groups absent or differ from projected reference')
    plain = dict(contract, collection={'kind': 'multiset'})
    result = typed.score(plain, gold_rows, predicted_rows, diagnostic=diagnostic)
    predicted, errors = typed.project(predicted_rows, contract['required_fields'])
    matched, position, exact = 0, 0, not errors and len(predicted) == len(gold_rows)
    for group in order_groups:
        gold = Counter(typed.record_token(row, contract['required_fields']) for row in group)
        observed = Counter(predicted[position:position + len(group)])
        matched += sum((gold & observed).values())
        exact = exact and gold == observed
        position += len(group)
    ng, np = len(gold_rows), len(predicted)
    precision = matched / np if np else (1.0 if not ng else 0.0)
    recall = matched / ng if ng else (1.0 if not np else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    result.update(exact=exact and result['cardinality_valid'], precision=precision,
                  recall=recall, f1=f1, matched_records=matched, gold_records=ng,
                  predicted_records=np, order_valid=exact)
    return result
