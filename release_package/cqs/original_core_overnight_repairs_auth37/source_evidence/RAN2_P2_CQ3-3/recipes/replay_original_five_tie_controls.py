"""Reproduce all original-query lawful nested answers and typed adverse cases.

SQL-derived eligibility is a witness, not limited native gold. Actual captures
can be attached later through the separate explicit production reader.
"""
import argparse
import copy
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError('optimized Python is not supported')
sys.dont_write_bytecode = True
D = Path(__file__).absolute().parent
P = D.parent
sys.path[:0] = [str(D), str(P), str(P / 'canonical')]
import scorer
import original_scorer
import verify_release
import bound_partition_adapter
import partitioned_complete_record_score as metrics

def must(value, message):
    if not value:
        raise RuntimeError(message)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    must(not args.output.exists(), 'preserve prior controls')
    definition = json.loads((P / 'definition.json').read_text())
    policy = json.loads((P / 'nested_eligibility_policy.json').read_text())
    population = json.loads((P / 'full_SQL_partition_population.json').read_text())
    identity = bound_partition_adapter.check_binding(definition, policy, verify_release)
    choices = []
    boundary_proof = []
    for code in sorted(population)[:5]:
        members = population[code]
        k = min(5, len(members))
        threshold = sorted((row['count'] for row in members), reverse=True)[k - 1]
        above = [row for row in members if row['count'] > threshold]
        tied = [row for row in members if row['count'] == threshold]
        alternatives = [above + list(part) for part in itertools.combinations(tied, k - len(above))]
        choices.append([{'workItemCode': code, 'topCompanies': copy.deepcopy(rows)} for rows in alternatives])
        boundary_proof.append({'workItemCode': code, 'population': len(members), 'required_members': k,
            'threshold': threshold, 'above': above, 'boundary': tied, 'choose': k - len(above),
            'lawful_subsets': len(alternatives)})
    alternatives = [list(rows) for rows in itertools.product(*choices)]
    must(len(alternatives) == 5, 'complete lawful combination count changed')
    controls = []
    def add(name, records, exact, f1=None, matched=None):
        result = metrics.score(definition, policy, population, records, scorer, original_scorer,
            verify_release, bound_partition_adapter, diagnostic=True)
        must(result['exact'] is exact, name + ': exact')
        if f1 is not None:
            must(math.isclose(result['f1'], f1, rel_tol=0, abs_tol=1e-12), name + ': F1')
        if matched is not None:
            must(result['matched_records'] == matched, name + ': matched outer WI records')
        controls.append({'name': name, 'input': records,
            'expected': {'exact': exact, 'f1': f1, 'matched_records': matched}, 'actual': result, 'PASS': True})
    for index, records in enumerate(alternatives):
        add('all_lawful_boundary_choice_' + str(index), records, True, 1, 5)
        permuted = copy.deepcopy(list(reversed(records)))
        for row in permuted:
            row['topCompanies'].reverse()
        add('outer_and_inner_permutation_' + str(index), permuted, True, 1, 5)
    base = copy.deepcopy(alternatives[0])
    # Every first5 WI participates in a value/cardinality/type/field test.
    for index in range(5):
        bad = copy.deepcopy(base); bad[index]['topCompanies'][0]['count'] += 1
        add('wrong_count_WI_' + str(index), bad, False, .8, 4)
        bad = copy.deepcopy(base); bad[index]['topCompanies'][0]['company'] = 'UNRECORDED_COMPANY'
        add('wrong_company_WI_' + str(index), bad, False, .8, 4)
        bad = copy.deepcopy(base); bad[index]['topCompanies'] = []
        add('empty_nested_members_WI_' + str(index), bad, False, .8, 4)
        bad = copy.deepcopy(base); del bad[index]['topCompanies'][0]['count']
        add('missing_count_field_WI_' + str(index), bad, False, .8, 4)
        bad = copy.deepcopy(base); bad[index]['topCompanies'].append(copy.deepcopy(bad[index]['topCompanies'][0]))
        add('duplicate_inner_member_WI_' + str(index), bad, False, .8, 4)
    for label, value in [('string', '1'), ('float', 1.0), ('bool', True), ('null', None), ('None_text', 'None')]:
        bad = copy.deepcopy(base); bad[0]['topCompanies'][0]['count'] = value
        add('wrong_count_type_' + label, bad, False, .8, 4)
    for label, value in [('null', None), ('number', 1), ('bool', False)]:
        bad = copy.deepcopy(base); bad[0]['topCompanies'][0]['company'] = value
        add('wrong_company_type_' + label, bad, False, .8, 4)
    bad = copy.deepcopy(base); bad[0]['topCompanies'][0]['approval'] = True
    add('surplus_nested_attribute', bad, False, .8, 4)
    bad = copy.deepcopy(base); bad[0]['extra'] = 'unrequested'
    add('surplus_outer_attribute', bad, False, .8, 4)
    bad = copy.deepcopy(base); del bad[0]['topCompanies']
    add('missing_outer_field', bad, False, .8, 4)
    bad = copy.deepcopy(base); bad[0]['topCompanies'] = 'None'
    add('nested_array_is_string', bad, False, .8, 4)
    bad = copy.deepcopy(base); bad[0]['topCompanies'] = None
    add('nested_array_is_null', bad, False, .8, 4)
    add('missing_WI', copy.deepcopy(base[1:]), False, 8 / 9, 4)
    bad = copy.deepcopy(base); bad.append({'workItemCode': 'OUTSIDE_FIRST5', 'topCompanies': []})
    add('extra_WI', bad, False, 10 / 11, 5)
    bad = copy.deepcopy(base); bad[0]['workItemCode'] = sorted(population)[5]
    add('wrong_outer_WI_boundary', bad, False, .8, 4)
    bad = copy.deepcopy(base); bad.append(copy.deepcopy(base[0]))
    add('duplicate_outer_WI_set_F1_but_not_exact', bad, False, 1, 5)
    bad = copy.deepcopy(base); bad[-1]['topCompanies'].pop()
    add('missing_inner_fifth_boundary_member', bad, False, .8, 4)
    lower = next(row for row in population[base[-1]['workItemCode']] if row['count'] < 4)
    bad = copy.deepcopy(base); bad[-1]['topCompanies'][-1] = copy.deepcopy(lower)
    add('below_boundary_company_count_pair', bad, False, .8, 4)
    bad = copy.deepcopy(base); bad[-1]['topCompanies'][0] = copy.deepcopy(bad[-1]['topCompanies'][-1])
    add('mandatory_count5_member_replaced_with_boundary_count4', bad, False, .8, 4)
    add('empty_answer', [], False, 0, 0)
    expected = json.loads((P / 'scientific_module_pins.json').read_text())['copied']
    must(all(sha(P / 'canonical' / name) == entry['sha256'] for name, entry in expected.items()),
         'canonical scientific module byte drift')
    out = {'status': 'PASS_DIAGNOSTIC_TYPED_CONTROLS_ONLY', 'id': definition['id'],
        'repair_sha256': identity, 'original_query_unchanged': True,
        'full_SQL_population_groups': sum(map(len, population.values())), 'full_SQL_WIs': len(population),
        'lawful_combinations': len(alternatives), 'all_lawful_variants': alternatives,
        'boundary_proof': boundary_proof, 'controls_n': len(controls), 'controls': controls,
        'canonical9_modified_n': 0, 'outer_complete_WI_record_scoring_unit': True,
        'limited_native_gold_observed': False, 'production_dispatch_actual_native_pending': True,
        'source_eligibility_is_native_gold': False, 'API_calls': 0, 'native_calls': 0,
        'public_admissions': 0,
        'inputs': {str(path.relative_to(P)): {'bytes': path.stat().st_size, 'sha256': sha(path)}
            for path in [P/'definition.json', P/'nested_eligibility_policy.json', P/'full_SQL_partition_population.json',
                D/'partitioned_complete_record_score.py', Path(__file__).absolute()]}}
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': out['status'], 'controls': len(controls),
        'all_lawful_alternatives': len(alternatives), 'sha256': sha(args.output)}))

if __name__ == '__main__':
    main()
