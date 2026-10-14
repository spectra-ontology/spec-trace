#!/usr/bin/env python3
"""Requested-field scoring with native-only ordering evidence.

Ordering columns may establish answer order without becoming requested answer
fields. This supplements the preserved typed scorer and never infers question
meaning, boundary top-k eligibility, or model performance.
"""
from collections import Counter
from decimal import Decimal
import scorer as typed


def make_order_groups(contract, native_rows, projected_rows):
    collection = contract['collection']
    keys = collection.get('source_order_keys')
    if (collection.get('kind') != 'native_ordered_ties'
            or collection.get('tie_policy') != 'any_order_within_equal_keys'
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
            seen[token] = index
    return groups


def score(contract, gold_rows, predicted_rows, *, diagnostic=False, order_groups=None):
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
