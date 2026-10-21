#!/usr/bin/env python3
"""Replay unchanged requested-field scoring; SQL fixture is not native evidence."""
import copy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys

if sys.flags.optimize:
    raise SystemExit('Optimization unsupported')
HERE = Path(__file__).absolute().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE / 'unchanged_scoring'))
import original_scorer as scorer


def load(path):
    return json.loads(path.read_text(), parse_float=Decimal)


def pin(path):
    return {'path': str(path), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


definition = load(HERE / 'definition.json')
sql_path = HERE.parent / 'actual_authored_original_full_five_column_SQL_rows_v18.json'
sql = load(sql_path)
native_shape = [{'m.canonicalMeetingNumber': x['canonicalMeetingNumber'],
                 'm.meetingNumberInt': x['meetingNumberInt'],
                 'huaweiCount': x['huaweiCount'], 'total': x['total'],
                 'ratio': x['ratio']} for x in sql]
gold = [{'canonicalMeetingNumber': x['m.canonicalMeetingNumber'], 'ratio': x['ratio']}
        for x in native_shape]
assert len(gold) == 52
assert all(type(x['m.meetingNumberInt']) is int for x in native_shape)
groups = scorer.make_order_groups(definition, native_shape, gold)
checks = []


def check(name, prediction, expected):
    result = scorer.score(definition, gold, prediction, diagnostic=True,
                          order_groups=groups)
    assert result['exact'] is expected, (name, result)
    checks.append({'name': name, 'expected_exact': expected, 'actual': result})


def rejected(name, function):
    try:
        function()
    except (ValueError, TypeError, KeyError) as error:
        checks.append({'name': name, 'actual_rejected': True,
                       'error_type': type(error).__name__, 'error': str(error)})
        return
    raise AssertionError((name, 'unexpected acceptance'))


check('all52_requested_records_no_helper_fields', gold, True)
check('all52_extra_unrequested_projection_does_not_become_required',
      [dict(x, meetingNumberInt=y['m.meetingNumberInt'], huaweiCount=y['huaweiCount'],
            total=y['total']) for x, y in zip(gold, native_shape)], True)
ties = copy.deepcopy(gold)
offset = 0
tie_n = 0
for group in groups:
    if len(group) > 1:
        ties[offset:offset + len(group)] = reversed(ties[offset:offset + len(group)])
        tie_n += 1
    offset += len(group)
assert tie_n > 0
check('reverse_every_same_integer_meeting_group', ties, True)
cross = copy.deepcopy(gold)
first_next = len(groups[0])
cross[0], cross[first_next] = cross[first_next], cross[0]
check('swap_records_across_numeric_meeting_groups', cross, False)
check('missing_final_meeting', gold[:-1], False)
check('extra_duplicate_meeting', gold + [gold[-1]], False)
duplicated = copy.deepcopy(gold)
duplicated[-1] = duplicated[-2]
check('substitute_one_meeting_with_duplicate', duplicated, False)
for field in ['canonicalMeetingNumber', 'ratio']:
    prediction = copy.deepcopy(gold)
    del prediction[0][field]
    check('missing_requested_' + field, prediction, False)
for label, value in [('string', '25.0'), ('bool', True), ('null', None),
                     ('nonfinite_nan', Decimal('NaN')), ('nonfinite_inf', Decimal('Infinity')),
                     ('wrong_value', Decimal('25.1'))]:
    prediction = copy.deepcopy(gold)
    prediction[0]['ratio'] = value
    check('ratio_' + label, prediction, False)
for label, value in [('int', 97), ('null', None), ('wrong_value', 'RAN2#97bis')]:
    prediction = copy.deepcopy(gold)
    prediction[0]['canonicalMeetingNumber'] = value
    check('meeting_' + label, prediction, False)
prediction = copy.deepcopy(gold)
prediction[0]['ratio'] = 25
check('mathematically_equal_integer_ratio', prediction, True)
prediction = copy.deepcopy(gold)
prediction[0] = {'meeting': gold[0]['canonicalMeetingNumber'], 'rate': gold[0]['ratio']}
check('wrong_named_fields', prediction, False)
rejected('native_order_groups_absent', lambda: scorer.score(
    definition, gold, gold, diagnostic=True))
rejected('native_order_groups_differ_from_gold', lambda: scorer.score(
    definition, gold, gold, diagnostic=True, order_groups=groups[:-1]))
bad_native = copy.deepcopy(native_shape)
del bad_native[0]['m.meetingNumberInt']
rejected('native_helper_absent', lambda: scorer.make_order_groups(definition, bad_native, gold))
bad_native = copy.deepcopy(native_shape)
bad_native[0]['m.meetingNumberInt'] = Decimal('NaN')
rejected('native_helper_nonfinite', lambda: scorer.make_order_groups(definition, bad_native, gold))
bad_native = copy.deepcopy(native_shape)
bad_native[0], bad_native[first_next] = bad_native[first_next], bad_native[0]
rejected('native_rows_not_sorted_by_numeric_helper',
         lambda: scorer.make_order_groups(definition, bad_native, gold))
bad_projected = copy.deepcopy(gold)
bad_projected[first_next] = bad_projected[0]
rejected('same_visible_record_in_two_distinct_native_groups',
         lambda: scorer.make_order_groups(definition, native_shape, bad_projected))
rejected('unvalidated_contract_cannot_supply_benchmark_score', lambda: scorer.score(
    definition, gold, gold, diagnostic=False, order_groups=groups))
result = {'status': 'PASS', 'scope': 'Actual execution of unchanged scoring modules on the saved '
          'five-column SQL fixture projected to the two requested fields. This is diagnostic '
          'scoring evidence, not a native capture or a benchmark performance measurement.',
          'id': definition['id'], 'requested_fields': ['canonicalMeetingNumber', 'ratio'],
          'reference_n': len(gold), 'order_group_n': len(groups), 'tied_group_n': tie_n,
          'checks_n': len(checks), 'checks': checks,
          'inputs': [pin(HERE / 'definition.json'), pin(sql_path)],
          'unchanged_modules': [pin(HERE / 'unchanged_scoring' / x)
              for x in ['original_scorer.py', 'scorer.py', 'typed_values.py', 'source_pins.json']],
          'native_calls': 0, 'API_calls': 0, 'new_admissions': 0}
destination = HERE / 'actual_requested_two_field_scoring_controls.json'
with destination.open('x') as stream:
    json.dump(result, stream, indent=2, ensure_ascii=False)
    stream.write('\n')
print(json.dumps({'status': result['status'], 'checks_n': len(checks),
                  'receipt': pin(destination)}))
