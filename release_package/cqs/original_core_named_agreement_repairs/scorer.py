#!/usr/bin/env python3
"""Local named-record scorer with explicit types and collection semantics.

Reuses the reviewed schema-first typed token kernel, without its 2,000-row
experimental adapter bound. No legacy value-set normalization is applied.
Gold is supplied separately. This scorer does not validate question meaning.
"""
from collections import Counter
import hashlib
import importlib.util
from pathlib import Path
import sys

KERNEL = Path(__file__).parent / 'typed_values.py'


def kernel():
    import json
    expected = json.loads((Path(__file__).parent / 'source_pins.json').read_text())['copied_kernel']['sha256']
    actual = hashlib.sha256(KERNEL.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError('typed scoring kernel changed')
    spec = importlib.util.spec_from_file_location('spectracq_contract_typed_kernel', KERNEL)
    module = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(module)
    return module


TYPED = None


def get_kernel():
    global TYPED
    if TYPED is None:
        TYPED = kernel()
    return TYPED


def record_token(row, fields):
    mod = get_kernel()
    if type(row) is not dict:
        raise ValueError('record must be a named JSON object')
    tokens = []
    for field in fields:
        name = field['name']
        if name not in row:
            raise ValueError('missing required field: ' + name)
        schema = mod.field_schema(field)
        token = mod.typed_token(row[name], schema, field.get('nested_array_semantics'), '$')
        tokens.append((name, token))
    return tuple(tokens)


def project(rows, fields, gold=False):
    tokens, errors = [], []
    if type(rows) is not list:
        raise ValueError('records must be a list')
    mod = get_kernel()
    for index, row in enumerate(rows):
        try:
            tokens.append(record_token(row, fields))
        except (ValueError, TypeError, KeyError) as exc:
            if gold:
                raise ValueError('invalid gold row ' + str(index) + ': ' + str(exc)) from exc
            # Distinct invalid records retain their identity. They cannot match
            # gold, and are never merged merely because their type error agrees.
            try:
                identity = mod.json_exact(row)
            except (ValueError, TypeError):
                identity = repr(row)
            tokens.append(('INVALID_RECORD', identity))
            errors.append({'row': index, 'reason': str(exc)})
    return tokens, errors


def compare_values(left, right, direction):
    # Cypher places null last ascending and first descending. Mixed incomparable
    # value types are prohibited by the declared field schema/order contract.
    if left is None or right is None:
        result = 0 if left is right else (1 if left is None else -1)
    else:
        result = (left > right) - (left < right)
    return result if direction == 'asc' else -result


def order_compare(left, right, keys):
    for key in keys:
        result = compare_values(left[key['field']], right[key['field']], key['direction'])
        if result:
            return result
    return 0


def ordered_groups(rows, tokens, keys):
    groups = []
    for index, row in enumerate(rows):
        if index and order_compare(rows[index - 1], row, keys) > 0:
            raise ValueError('records violate declared order')
        if not groups or order_compare(groups[-1][0], row, keys):
            groups.append((row, [tokens[index]]))
        else:
            groups[-1][1].append(tokens[index])
    return [Counter(group) for _, group in groups]


def validate_order_keys(collection, fields):
    keys = collection.get('order_keys')
    names = {field['name']: field for field in fields}
    if not isinstance(keys, list) or not keys:
        raise ValueError('ordered collection requires nonempty order keys')
    seen = set()
    for key in keys:
        if (type(key) is not dict or key.get('field') not in names
                or key.get('direction') not in {'asc', 'desc'}
                or key['field'] in seen or names[key['field']]['type'] == 'json'):
            raise ValueError('invalid, duplicate or nonprimitive order key')
        seen.add(key['field'])
    return keys


def require_sorted(rows, keys):
    if any(order_compare(left, right, keys) > 0 for left, right in zip(rows, rows[1:])):
        raise ValueError('records violate declared order')


def score(contract, gold_rows, predicted_rows, *, diagnostic=False):
    fields = contract['required_fields']
    if not fields or len({f['name'] for f in fields}) != len(fields):
        raise ValueError('required field names must be nonempty and unique')
    if not diagnostic and contract.get('validation_status') != 'validated':
        raise ValueError('unvalidated task cannot supply benchmark scores')
    gold, _ = project(gold_rows, fields, gold=True)
    pred, errors = project(predicted_rows, fields)
    kind = contract['collection']['kind']
    order_valid = not errors
    if kind == 'set':
        a, b = set(gold), set(pred)
        matched, ng, np = len(a & b), len(a), len(b)
        exact = a == b
    elif kind == 'multiset':
        a, b = Counter(gold), Counter(pred)
        matched, ng, np = sum((a & b).values()), len(gold), len(pred)
        exact = a == b
    elif kind == 'sequence':
        keys = validate_order_keys(contract['collection'], fields)
        require_sorted(gold_rows, keys)
        try:
            if errors:
                raise ValueError('invalid predicted fields')
            require_sorted(predicted_rows, keys)
        except (ValueError, TypeError, KeyError):
            order_valid = False
        matched = sum(a == b for a, b in zip(gold, pred))
        ng, np, exact = len(gold), len(pred), gold == pred
    elif kind == 'ordered_ties':
        keys = validate_order_keys(contract['collection'], fields)
        if contract['collection'].get('tie_policy') != 'any_order_within_equal_keys':
            raise ValueError('unsupported ordered-tie policy')
        a = ordered_groups(gold_rows, gold, keys)
        try:
            if errors:
                raise ValueError('invalid predicted fields')
            b = ordered_groups(predicted_rows, pred, keys)
            matched = sum(sum((x & y).values()) for x, y in zip(a, b))
            exact = a == b
        except (ValueError, TypeError, KeyError):
            matched, exact, order_valid = 0, False, False
        ng, np = len(gold), len(pred)
    else:
        raise ValueError('collection semantics absent or unsupported')
    cardinality = contract['cardinality_policy']
    mode = cardinality['mode']
    cardinality_ok = True
    if mode == 'exact':
        if ng != cardinality['value']:
            raise ValueError('gold violates declared exact cardinality')
        cardinality_ok = np == cardinality['value']
    elif mode in {'at_most', 'top_k'}:
        if ng > cardinality['value']:
            raise ValueError('gold violates declared upper cardinality')
        cardinality_ok = np == ng if mode == 'top_k' else np <= cardinality['value']
    elif mode != 'all':
        raise ValueError('cardinality policy absent or unsupported')
    exact = exact and cardinality_ok and order_valid
    precision = matched / np if np else (1.0 if not ng else 0.0)
    recall = matched / ng if ng else (1.0 if not np else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {'diagnostic_only': diagnostic, 'exact': exact, 'precision': precision,
            'recall': recall, 'f1': f1, 'matched_records': matched,
            'gold_records': ng, 'predicted_records': np, 'type_errors': errors,
            'cardinality_valid': cardinality_ok, 'order_valid': order_valid}
