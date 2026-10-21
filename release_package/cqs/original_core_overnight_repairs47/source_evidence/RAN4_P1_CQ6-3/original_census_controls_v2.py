"""Actual original scorer controls for the requested singleton CR count."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE / 'scoring'))
import original_scorer
import contract_checks


def controls(task, rows, counts):
    gold = [{'crs': rows[0]['crs']}]
    checks = contract_checks.checks(task, gold)
    n = gold[0]['crs']
    cases = [
        ('full_original_two_column_reference', rows, True),
        ('unrequested_total_does_not_become_mandatory', [{'crs': n}], True),
        ('unrequested_total_not_scored', [{'total': -1, 'crs': n}], True),
        ('denominator_only_not_requested_count', [{'total': rows[0]['total']}], False),
        ('ratio_alone_not_requested_count', [{'ratio': n / rows[0]['total']}], False),
        ('ratio_in_requested_integer_field', [{'crs': n / rows[0]['total']}], False),
        ('NULL_is_not_count', [{'crs': None}], False),
        ('boolean_is_not_integer', [{'crs': True}], False),
        ('numeric_string_is_not_integer', [{'crs': str(n)}], False),
        ('integral_float_is_not_integer', [{'crs': float(n)}], False),
        ('Type_formation_count_not_final_census', [{'crs': counts['Tdoc_Type_CR_set']}], False),
        ('explicit_Tdoc_intersection_not_final_census', [{'crs': counts['Tdoc_CR_intersection']}], False),
        ('Type_or_label_union_not_final_census', [{'crs': counts['Tdoc_CR_label_OR_Type_CR_set']}], False),
        ('two_distinct_counts_violates_singleton', [{'crs': n}, {'crs': n + 1}], False),
    ]
    for name, pred, expected in cases:
        got = original_scorer.score(task, gold, pred, diagnostic=True)
        checks.append({'check': name, 'expected_exact': expected, 'pass': got['exact'] is expected,
                       'prediction': pred, 'outcome': got})
    if not all(row['pass'] for row in checks):
        raise ValueError('requested-field scorer control failed')
    return checks


def main():
    task = json.loads((HERE / 'repair_original_census_v2.json').read_bytes())
    rows = json.loads((HERE / 'actual_immutable_SQL_original_census_v2.json').read_bytes())['rows']
    counts = json.loads((HERE / 'source_membership_diagnostics_v1/receipt.json').read_bytes())['counts']
    results = controls(task, rows, counts)
    p = HERE / 'actual_original_census_requested_field_controls_v2.json'
    with p.open('x') as f:
        json.dump({'status': 'PASS', 'id': task['id'], 'scorer_semantics_unchanged': True,
                   'control_count': len(results), 'controls': results,
                   'full_reference_columns': ['total', 'crs'], 'required_fields': ['crs'],
                   'new_API_calls': 0, 'new_native': 0}, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps({'status': 'PASS', 'controls': len(results)}))

if __name__ == '__main__':
    main()
