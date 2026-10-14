#!/usr/bin/env python3
"""Typed snapshot scoring adapter; the original record scorer is unchanged.

All values are schema-validated before a hashable typed token is constructed.
Declared nested sets deduplicate/sort tokens, multisets sort preserving counts,
and sequences retain positions. Decimal JSON parsing preserves numeric literals.
No source queries/model calls are made. CLI scoring is a later authorized action.
"""
import argparse
from decimal import Decimal
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys


MAX_NUMERIC_DIGITS = 4096
MAX_DECIMAL_EXPONENT = 4096


class InvalidTypedValue(ValueError):
    pass


def fail(message):
    raise InvalidTypedValue(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_pinned_module(path, expected_sha, name):
    path = Path(path)
    if sha(path) != expected_sha:
        raise ValueError('module hash differs from reviewed pin: ' + path.name)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    before = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = before
    return module


def reject_constant(value):
    raise InvalidTypedValue('nonfinite JSON numeric literal: ' + value)


def unique_object_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail('duplicate JSON object key')
        result[key] = value
    return result


def loads_exact(text):
    return json.loads(text, parse_float=Decimal, parse_constant=reject_constant,
                      object_pairs_hook=unique_object_pairs)


exact_loads = loads_exact


def json_exact(value):
    """Serialize finite Decimal as a numeric token, never as an answer string."""
    if value is None:
        return 'null'
    if type(value) is bool:
        return 'true' if value else 'false'
    if type(value) is str:
        return json.dumps(value, ensure_ascii=False)
    if type(value) is int:
        if len(str(abs(value))) > MAX_NUMERIC_DIGITS:
            fail('numeric precision outside fixed supported bound')
        return str(value)
    if type(value) in {float, Decimal}:
        numeric_fraction(value)
        return str(value) if type(value) is Decimal else json.dumps(value, allow_nan=False)
    if type(value) is list:
        return '[' + ','.join(json_exact(child) for child in value) + ']'
    if type(value) is dict and all(type(key) is str for key in value):
        return '{' + ','.join(json.dumps(key, ensure_ascii=False) + ':' + json_exact(value[key])
                              for key in sorted(value)) + '}'
    fail('unsupported JSON object')


def numeric_fraction(value):
    if type(value) is bool or type(value) not in {int, float, Decimal}:
        fail('not a typed number')
    if type(value) is int:
        if len(str(abs(value))) > MAX_NUMERIC_DIGITS:
            fail('numeric precision outside fixed supported bound')
        return Fraction(value)
    if type(value) is float:
        if not math.isfinite(value):
            fail('nonfinite number')
        # A float supplied by an API is interpreted as its captured JSON repr.
        # Saved JSON files are parsed as Decimal before any float conversion.
        value = Decimal(str(value))
    if not value.is_finite():
        fail('nonfinite number')
    digits, exponent = value.as_tuple().digits, value.as_tuple().exponent
    if len(digits) > MAX_NUMERIC_DIGITS or abs(exponent) > MAX_DECIMAL_EXPONENT:
        fail('numeric precision outside fixed supported bound')
    return Fraction(value)


def value_kind(value):
    if value is None:
        return 'null'
    if type(value) is bool:
        return 'boolean'
    if type(value) is int:
        numeric_fraction(value)
        return 'integer'
    if type(value) in {float, Decimal}:
        numeric_fraction(value)
        return 'number'
    if type(value) is str:
        return 'string'
    if type(value) is list:
        return 'array'
    if type(value) is dict and all(type(key) is str for key in value):
        return 'object'
    fail('unsupported native value')


def field_schema(field):
    if 'snapshot_shape' in field:
        schema = field['snapshot_shape']
    elif field['type'] == 'json':
        schema = field['json_schema']
    else:
        typ = field['type']
        schema = {'type': [typ, 'null'] if field.get('nullable') and typ != 'null' else typ}
    validate_schema(schema)
    types = schema['type'] if type(schema['type']) is list else [schema['type']]
    active = set(types) - {'null'}
    declared = field['type']
    if declared == 'json':
        if not active <= {'array', 'object'} or len(active) != 1:
            fail('JSON field has contradictory snapshot shape')
        if 'json_schema' in field and schema != field['json_schema']:
            fail('JSON schema differs from snapshot shape')
    elif active != {declared} and not (declared == 'null' and not active):
        fail('declared primitive type differs from snapshot shape')
    if ('null' in types) != (field.get('nullable', False) or declared == 'null'):
        fail('declared nullable differs from snapshot shape')
    return schema


def validate_schema(schema):
    if type(schema) is not dict:
        fail('schema must be an object')
    kinds = schema.get('type')
    kinds = kinds if type(kinds) is list else [kinds]
    if not kinds or len(kinds) != len(set(kinds)) or not set(kinds) <= {
            'string', 'integer', 'number', 'boolean', 'null', 'array', 'object'}:
        fail('undefined schema kind')
    if 'array' in kinds:
        validate_schema(schema.get('items'))
    if 'object' in kinds:
        props, required = schema.get('properties'), schema.get('required')
        if (type(props) is not dict or type(required) is not list
                or set(required) != set(props) or len(required) != len(props)
                or schema.get('additionalProperties') is not False):
            fail('objects require exact source-defined structural properties')
        for name, child in props.items():
            if type(name) is not str:
                fail('invalid schema property name')
            validate_schema(child)
    if set(schema) - {'type', 'items', 'properties', 'required', 'additionalProperties'}:
        fail('value/cardinality hint or unsupported schema keyword')


def typed_token(value, schema, semantics=None, path='$'):
    """Validate first, then normalize only declared collection semantics."""
    actual = value_kind(value)
    allowed = schema['type'] if type(schema['type']) is list else [schema['type']]
    if actual not in allowed and not (actual == 'integer' and 'number' in allowed):
        fail('wrong JSON type at ' + path)
    if actual == 'null':
        return ('null', '')
    if actual in {'integer', 'number'}:
        if 'number' in allowed:
            fraction = numeric_fraction(value)
            return ('number', str(fraction.numerator) + '/' + str(fraction.denominator))
        return ('integer', str(value))
    if actual == 'string':
        return ('string', value)
    if actual == 'boolean':
        return ('boolean', value)
    if actual == 'object':
        if set(value) != set(schema['required']):
            fail('missing/extra structural property at ' + path)
        return ('object', tuple((name, typed_token(value[name], schema['properties'][name],
                                                  semantics, path + '.' + name))
                                for name in sorted(value)))
    collection = (semantics or {}).get(path)
    if collection not in {'set', 'multiset', 'sequence'}:
        fail('undefined nested array semantics at ' + path)
    members = [typed_token(child, schema['items'], semantics, path + '[]') for child in value]
    if collection == 'set':
        members = list(set(members))
    if collection in {'set', 'multiset'}:
        members.sort(key=lambda token: json.dumps(token, ensure_ascii=False, separators=(',', ':')))
    return ('array:' + collection, tuple(members))


def project_typed(records, fields, *, gold=False):
    if type(records) is not list or len(records) > 2000:
        fail('records must be a list within fixed2000 bound')
    result, errors = [], []
    for index, record in enumerate(records):
        cells = []
        for field in fields:
            name = field['name']
            if type(record) is not dict or name not in record:
                if gold:
                    fail('gold missing named field: ' + name)
                cells.append(('missing', ''))
                errors.append({'row': index, 'field': name, 'reason': 'missing named field'})
                continue
            try:
                schema = field_schema(field)
                token = typed_token(record[name], schema, field.get('nested_array_semantics', {}))
            except InvalidTypedValue as error:
                if gold:
                    raise InvalidTypedValue('gold invalid typed field ' + name + ': ' + str(error)) from error
                # Distinct wrong typed values must not collapse into a single
                # invalid marker during outer-set comparison and inflate precision.
                try:
                    raw_identity = json_exact(record[name])
                    token = ('invalid', name, raw_identity)
                except InvalidTypedValue:
                    token = ('invalid', name, 'unsupported_value', str(index))
                errors.append({'row': index, 'field': name, 'reason': str(error)})
            cells.append(token)
        result.append(tuple(cells))
    return result, errors


def score_contract(contract, gold_records, prediction, base_scorer):
    base_scorer.validate_contract(contract)
    if contract['constraints']:
        fail('external constraints require a separately reviewed adapter')
    fields, collection = contract['required_fields'], contract['collection']
    if collection['kind'] not in {'set', 'multiset', 'sequence'}:
        fail('expanded structured-signature protocol has no ordered_ties mode')
    # Fail a broken definition independently of any prediction values.
    for field in fields:
        field_schema(field)
    gold, _ = project_typed(gold_records, fields, gold=True)
    records = prediction.get('records') if type(prediction) is dict else prediction
    predicted, errors = project_typed(records, fields)
    exact, cells, rows, n_pred, n_gold = base_scorer.compare_rows(predicted, gold, fields, collection)
    precision = cells / (n_pred * len(fields)) if n_pred else float(not n_gold)
    recall = cells / (n_gold * len(fields)) if n_gold else float(not n_pred)
    row_precision = rows / n_pred if n_pred else float(not n_gold)
    row_recall = rows / n_gold if n_gold else float(not n_pred)
    harmonic = lambda p, r: 2 * p * r / (p + r) if p + r else 0.0
    return {'item_id': contract['item_id'], 'measurement_scope': 'supplied frozen snapshot records only',
            'semantic_validation': False, 'output_exact': exact,
            'exact': None if contract['status'] != 'ready' or contract['unresolved_reasons'] else exact,
            'output_full_records': {'precision': row_precision, 'recall': row_recall,
                                    'f1': harmonic(row_precision, row_recall),
                                    'correct_records': rows, 'predicted_records': n_pred, 'gold_records': n_gold},
            'partial_named_cells': {'precision': precision, 'recall': recall,
                                    'f1': harmonic(precision, recall), 'correct_cells': cells,
                                    'predicted_opportunities': n_pred * len(fields),
                                    'gold_opportunities': n_gold * len(fields)},
            'typed_prediction_errors': errors, 'prediction_rows_dropped': 0,
            'original_scorer_modified': False,
            'numeric_policy': 'integer strict; number exact finite rational value from Decimal JSON literals'}


def validate_prediction(value, fields):
    """Generation-side strict validation using the same exact numeric rules."""
    if type(value) is not dict or set(value) != {'records', 'abstain'} or type(value['abstain']) is not bool:
        fail('prediction envelope must contain records and boolean abstain only')
    names = {field['name'] for field in fields}
    if type(value['records']) is not list or len(value['records']) > 2000:
        fail('prediction record bound')
    for record in value['records']:
        if type(record) is not dict or set(record) != names:
            fail('prediction record named fields differ')
        for field in fields:
            typed_token(record[field['name']], field_schema(field), field.get('nested_array_semantics', {}))
    if value['abstain'] and value['records']:
        fail('abstain=true must have no records')
    return value


def self_test(base):
    passed = []
    anchor = {'question': 'SYNTHETIC', 'query': 'RETURN synthetic'}
    def contract(fields, kind='set'):
        return {'version': 1, 'item_id': 'SYNTHETIC_ONLY', 'status': 'ready',
                'required_fields': [{**field, 'source_anchor': anchor} for field in fields],
                'collection': {'kind': kind}, 'constraints': [], 'unresolved_reasons': []}
    def exact(c, gold, pred):
        return score_contract(c, gold, pred, base)['output_exact']
    scalar = contract([{'name': 'n', 'type': 'integer', 'role': 'count'}])
    assert exact(scalar, [{'n': 1}], [{'n': True}]) == exact(scalar, [{'n': 1}], [{'n': '1'}]) == 0
    assert exact(scalar, [{'n': 1}], [{'n': Decimal('1.0')}]) == 0
    passed.append('integer_boolean_string_decimal_strict')
    numeric = contract([{'name': 'n', 'type': 'number', 'role': 'value'}])
    assert exact(numeric, [{'n': 1}], [{'n': Decimal('1.000')}]) == 1
    assert exact(numeric, loads_exact('[{"n":1.00000000000000001}]'), loads_exact('[{"n":1.00000000000000002}]')) == 0
    assert exact(numeric, [{'n': Decimal('-0.0')}], [{'n': 0}]) == 1
    passed.append('number_exact_decimal_precision_and_signed_zero')
    for invalid in (True, '1', Decimal('NaN'), float('inf')):
        assert exact(numeric, [{'n': 1}], [{'n': invalid}]) == 0
    passed.append('number_boolean_string_nonfinite_rejected')
    nullable = contract([{'name': 'n', 'type': 'integer', 'role': 'value', 'nullable': True}])
    assert exact(nullable, [{'n': None}], [{'n': None}]) == 1
    assert exact(nullable, [{'n': None}], [{}]) == 0
    passed.append('null_distinct_from_missing')
    array = {'type': 'array', 'items': {'type': 'integer'}}
    f = {'name': 'a', 'type': 'json', 'role': 'identifiers', 'json_schema': array,
         'nested_array_semantics': {'$': 'set'}}
    sets = contract([f])
    assert exact(sets, [{'a': [1, 2]}], [{'a': [2, 1, 1]}]) == 1
    bags = contract([{**f, 'nested_array_semantics': {'$': 'multiset'}}])
    assert exact(bags, [{'a': [1, 1, 2]}], [{'a': [2, 1, 1]}]) == 1
    assert exact(bags, [{'a': [1, 2]}], [{'a': [2, 1, 1]}]) == 0
    sequence = contract([{**f, 'nested_array_semantics': {'$': 'sequence'}}])
    assert exact(sequence, [{'a': [1, 2]}], [{'a': [2, 1]}]) == 0
    passed.extend(['nested_set_permutation_and_duplicates', 'nested_bag_preserves_multiplicity', 'nested_sequence_preserves_positions'])
    for bad in ([True, 2], ['1', 2], [Decimal('1.0'), 2]):
        assert exact(sets, [{'a': [1, 2]}], [{'a': bad}]) == 0
    passed.append('nested_schema_checked_before_collection_normalization')
    nested_number = contract([{**f, 'json_schema': {'type': 'array', 'items': {'type': 'number'}}}])
    assert exact(nested_number, [{'a': [1, Decimal('2.00')]}], [{'a': [2, Decimal('1.0'), 1]}]) == 1
    passed.append('nested_numeric_equivalence_without_precision_loss')
    empty = score_contract(sets, [{'a': []}], [{'a': []}], base)
    assert empty['output_exact'] == 1
    passed.append('defined_schema_empty_prediction_array_supported')
    roles = contract([{'name': 'sender', 'type': 'string', 'role': 'sender'},
                      {'name': 'recipient', 'type': 'string', 'role': 'recipient'}])
    r = score_contract(roles, [{'sender': 'A', 'recipient': 'B'}], [{'sender': 'B', 'recipient': 'A'}], base)
    assert r['output_full_records']['f1'] == r['partial_named_cells']['f1'] == 0
    passed.append('sender_recipient_cross_role_no_credit')
    r = score_contract(roles, [{'sender': 'A', 'recipient': 'B'}], [{'sender': 'A', 'recipient': True}], base)
    assert r['output_full_records']['f1'] == 0 and r['partial_named_cells']['f1'] == .5
    assert r['prediction_rows_dropped'] == 0 and r['output_full_records']['predicted_records'] == 1
    passed.append('invalid_cell_opportunity_and_row_retained')
    r = score_contract(scalar, [{'n': 1}], [{'n': 1}, {'n': 'wrong_A'}, {'n': 'wrong_B'}], base)
    assert r['output_full_records']['predicted_records'] == 3 and r['output_full_records']['precision'] == 1/3
    passed.append('distinct_invalid_values_not_collapsed_to_inflate_precision')
    for ckind, expected in [('set', 1), ('multiset', 0), ('sequence', 0)]:
        c = contract([{'name': 'n', 'type': 'integer', 'role': 'count'}], ckind)
        assert exact(c, [{'n': 1}, {'n': 2}], [{'n': 2}, {'n': 1}, {'n': 1}]) == expected
    passed.append('outer_collection_same_record_concept')
    literal = '[{"n":1.2345678901234567890123456789}]'
    assert loads_exact(json_exact(loads_exact(literal))) == loads_exact(literal)
    passed.append('decimal_JSON_roundtrip_is_number_not_string')
    try:
        numeric_fraction(Decimal('1e5000'))
    except InvalidTypedValue:
        passed.append('complex_numeric_shape_explicitly_unsupported')
    else:
        raise AssertionError('unbounded exponent accepted')
    duplicate_cases = [
        ('duplicate_root_keys_rejected', '{"records":[],"records":[],"abstain":true}'),
        ('duplicate_nested_record_fields_rejected', '{"records":[{"count":1,"count":2}],"abstain":false}'),
        ('captured_raw_model_text_duplicate_escaped_key_rejected',
         '{"records":[{"value":1.00000000000000001,"va\\u006cue":1.00000000000000002}],"abstain":false}'),
    ]
    for name, raw_text in duplicate_cases:
        captured_sha = hashlib.sha256(raw_text.encode()).hexdigest()
        try:
            loads_exact(raw_text)
        except InvalidTypedValue:
            assert hashlib.sha256(raw_text.encode()).hexdigest() == captured_sha
            passed.append(name)
        else:
            raise AssertionError(name)
    return {'status': 'PASS', 'synthetic_tests_n': len(passed), 'tests': passed,
            'actual_gold_or_predictions_scored': 0, 'model_calls': 0, 'source_queries': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['self-test'])
    parser.add_argument('--base-scorer', type=Path, required=True)
    parser.add_argument('--base-sha256', required=True)
    args = parser.parse_args()
    base = load_pinned_module(args.base_scorer, args.base_sha256, 'expanded_unmodified_record_scorer')
    print(json.dumps(self_test(base), indent=2))


if __name__ == '__main__':
    main()
