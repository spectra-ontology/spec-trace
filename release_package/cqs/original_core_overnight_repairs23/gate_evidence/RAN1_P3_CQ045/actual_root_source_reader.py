"""Compare all authored return columns and execute requested-identity controls."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
O = HERE.parent
B = next(p for p in HERE.parents if p.name == 'overnight_reaudit')
P = Path('/home/sihyeon/workspace/spectra-public/spec-trace')
K = P / 'release_package/cqs/original_core_repair'
sys.path.insert(0, str(K))
import scorer
import original_scorer
import contract_checks

ID = 'RAN1_P3_CQ045'
REPAIR = '3950eb7946e0b3ad47afed70818088159fea41320df0e91c8f0de8e28b426e80'
QUERY = '4c5cd385f33cb03b63815ecd3ad6e3dd590845011bda83f3ca85c3d217552c05'
KEYS = ['id', 'question_en', 'original_query', 'reference_query', 'required_fields', 'collection', 'cardinality_policy', 'repair_class', 'original_question_preserved']


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_text())


def save(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def lines(p):
    return [scorer.get_kernel().loads_exact(x) for x in p.read_text().splitlines() if x.strip()]


def main():
    definition = O / 'RAN1_RAN3_RAN4/loop174_CQ045_original_formal_Resolution_requested_TS_identity_semantic_proposal/prospective_original_query_TS_identity_definition.json'
    task = read(definition)
    kernel = scorer.get_kernel()
    assert sha(definition) == '010c24b19e334ec87289e0d7800c704f4986183a60622527e842a64482d68873'
    assert hashlib.sha256(kernel.json_exact({k: task[k] for k in KEYS}).encode()).hexdigest() == REPAIR
    assert task['id'] == ID and task['original_query'] == task['reference_query']
    assert hashlib.sha256(task['reference_query'].encode()).hexdigest() == QUERY
    assert task['collection'] == {'kind': 'set'} and task['cardinality_policy'] == {'mode': 'all'}
    task['repair_sha256'] = REPAIR
    originals = lines(K / 'provenance/original_benchmark.jsonl')
    original = next(x for x in originals if x['id'] == ID)
    assert original['question_en'] == task['question_en'] and original['cypher'] == task['original_query']
    native_base = HERE / 'native_exact_full3_infrastructure_retry'
    guard = HERE / 'actual_continuous_exact_native_guard_infrastructure_retry.json'
    assert read(guard)['status'] == 'PASS'
    rp = native_base / 'reference_outputs' / ID / (QUERY + '.json')
    rr = rp.with_suffix('.jsonl')
    receipt = read(rp)
    assert receipt['query'] == task['reference_query'] and receipt['status'] == 'OK'
    assert receipt['full_rows_available'] is True and receipt['truncated'] is False
    assert receipt['rollback_completed'] and receipt['execution_summary_complete']
    assert receipt['plan_query_type'] == receipt['execution_query_type'] == 'r'
    assert receipt['columns'] == ['spec', 'resolutionCount', 'crCount']
    assert sha(rr) == receipt['rows_sha256']
    native = lines(rr)
    assert len(native) == receipt['rows_retained'] == 3
    sql_file = HERE / 'actual_ROOT_independent_SQL_reference_and_finite_bound.json'
    sql = read(sql_file)
    sql_rows = [[r[k] for k in receipt['columns']] for r in sql['full_reference_rows']]
    assert kernel.json_exact(native) == kernel.json_exact(sql_rows)
    records = [{'spec': row[0]} for row in native]
    assert {row['spec'] for row in records} == {'38.212', '38.213', '38.214'}
    run = read(native_base / 'execution_RAN1.json')
    index = read(P / 'release_package/cqs/current_core/index_manifest.json')
    assert run['inventory_unchanged'] and run['model_calls'] == 0 and run['expert_validation'] is False
    assert run['source_before'] == run['source_after'] == index['source_snapshot']['RAN1']
    controls = contract_checks.checks(task, records)
    assert len(controls) == 7 and all(x['pass'] for x in controls)
    predictions = original_scorer.reference_prediction(task, records)
    extra_cases = [
        ('permuted_complete_identity_set', list(reversed(predictions)), True),
        ('missing_one_TS', predictions[:-1], False),
        ('duplicate_displaces_distinct_TS', predictions[:-1] + predictions[:1], False),
        ('extra_outside_target_38_211', predictions + [{'spec': '38.211'}], False),
        ('wrong_required_TS_identity', [{'spec': '38.211'}, *predictions[1:]], False),
        ('null_required_identity', [{'spec': None}, *predictions[1:]], False),
        ('numeric_required_identity', [{'spec': 38214}, *predictions[1:]], False),
        ('incidental_count_values_ignored', [dict(x, resolutionCount=-999, crCount=-999) for x in predictions], True),
        ('incidental_counts_do_not_replace_identity', [{'resolutionCount': 48, 'crCount': 99}], False),
    ]
    actual = list(controls)
    for name, prediction, expected in extra_cases:
        outcome = original_scorer.score(task, records, prediction, diagnostic=True)
        actual.append({'check': name, 'pass': outcome['exact'] is expected})
    assert len(actual) == 16 and all(x['pass'] for x in actual)
    save(HERE / 'definition.json', task)
    records_file = HERE / 'independent_SQL_requested_records.jsonl'
    sql_all = HERE / 'independent_SQL_all_return_columns.jsonl'
    with records_file.open('x') as stream:
        stream.write(''.join(kernel.json_exact({'spec': r['spec']}) + '\n' for r in sql['full_reference_rows']))
    with sql_all.open('x') as stream:
        stream.write(''.join(kernel.json_exact(row) + '\n' for row in sql_rows))
    pins = {str(p): sha(p) for p in [definition, HERE / 'definition.json', rp, rr, sql_file, records_file, sql_all, guard]}
    save(HERE / 'controls/controls.json', {'id': ID, 'repair_sha256': REPAIR, 'status': 'controls_pass', 'controls': controls, 'pins': pins, 'source_guard': run['source_before'], 'native_reference_population_n': 3})
    sqlcase = {'id': ID, 'independent_SQL_all_return_columns': str(sql_all.relative_to(B)), 'independent_SQL_all_return_columns_sha256': sha(sql_all),
               'independent_records': str(records_file.relative_to(B)), 'independent_records_sha256': sha(records_file),
               'compared_native_columns': receipt['columns'], 'all_return_fields_compared': True, 'uncapped_SQL': True,
               'native_receipt_sha256': sha(rp), 'native_rows_sha256': sha(rr), 'cap_meaning': 'Exact original query has no LIMIT; complete finite three-TS output.',
               'independent_SQL_file': str((HERE / 'prospective_independent_reference.sql').relative_to(B)), 'independent_SQL_sha256': sql['SQL_sha256'],
               'SQL_capture_receipt': str(sql_file.relative_to(B)), 'SQL_capture_receipt_sha256': sha(sql_file)}
    save(HERE / 'native_SQL_agreement.json', {'id': ID, 'repair_sha256': REPAIR, 'independent_native_sql_fullpool_equal': True, 'all_reference_query_return_columns_typed_equal': True, 'root_independent_SQL_case': sqlcase,
                                           'incidental_count_source_fidelity_certified': False, 'source_semantic_gate_is_separate': True, 'expert_validation_n': 0})
    result = {'status': 'PASS_ACTUAL_ROOT_ORIGINAL_FULL3_NATIVE_SQL_AND16_CONTROLS', 'observed_utc': datetime.now(timezone.utc).isoformat(), 'id': ID, 'repair_sha256': REPAIR,
              'native_rows': 3, 'all_three_authored_columns_typed_equal': True, 'actual_scorer_checks': actual, 'source_membership_closure_is_separate': True,
              'preserved_prior_guard_failure': 'actual_continuous_exact_native_guard.json', 'passed_guard': guard.name, 'new_API_calls': 0, 'new_admissions': 0, 'expert_validation_n': 0}
    output = HERE / 'actual_ROOT_native_SQL_and_controls.json'
    save(output, result)
    print(json.dumps({'status': result['status'], 'receipt_sha256': sha(output), 'native_rows': 3, 'checks': len(actual)}))


if __name__ == '__main__':
    main()
