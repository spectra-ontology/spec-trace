#!/usr/bin/env python3
"""Verify the captured full owner pool and replay actual requested-field controls."""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
RECHECK = BASE.parent
PREP = BASE.parents[2]
ORIG = PREP / 'original_repair'
PARENT = Path('/home/sihyeon/workspace/spectra-public/spec-trace/release_package/cqs/original_core_repair')
sys.path[:0] = [str(ORIG), str(PREP)]
import build
import contract_checks
import original_scorer
import review_schema
import scorer


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    return [scorer.get_kernel().loads_exact(line) for line in path.read_text().splitlines() if line.strip()]


def main():
    task = rows(BASE / 'proposals.jsonl')[0]
    second = rows(BASE / 'secondary.jsonl')[0]
    keys = ['id', 'question_en', 'original_query', 'reference_query', 'required_fields', 'collection',
            'cardinality_policy', 'repair_class', 'original_question_preserved']
    assert build.digest({key: task[key] for key in keys}) == task['repair_sha256'] == second['repair_sha256']
    original = next(row for row in rows(PARENT / 'provenance/original_benchmark.jsonl') if row['id'] == task['id'])
    assert task['question_en'] == original['question_en'] and task['original_query'] == original['cypher']
    criteria_sha = sha(PARENT / 'criteria.json')
    semantic_units = json.loads((PARENT / 'criteria.json').read_text())['semantic_units']
    for review in (task['primary_review'], second):
        review_schema.check_pass(review, task['question_en'], semantic_units, criteria_sha=criteria_sha,
                                 identity_key='repair_sha256', identity_sha=task['repair_sha256'])
    protocol = json.loads((BASE / 'execution_protocol.json').read_text())
    assert protocol['semantic_primary_file_sha256'] == sha(BASE / 'proposals.jsonl')
    assert protocol['semantic_secondary_file_sha256'] == sha(BASE / 'secondary.jsonl')
    assert protocol['full_owned_source_pool_witness_sha256'] == sha(BASE / 'source_pool_witness.json')
    source = RECHECK / 'ownership_common_source'
    assert protocol['common_ownership_source_manifest_sha256'] == task['common_source_manifest_sha256'] == sha(source / 'manifest.json')
    for row in json.loads((source / 'manifest.json').read_text())['files']:
        assert sha(source / row['path']) == row['sha256']
    execution = json.loads((BASE / 'execution_RAN4.json').read_text())
    parent_source = json.loads((PARENT / 'manifest.json').read_text())['graph_sources']['RAN4']
    assert execution['source_before'] == execution['source_after'] == parent_source
    assert execution['inventory_unchanged'] and execution['protocol_sha256'] == sha(BASE / 'execution_protocol.json')
    assert execution['input_sha256'] == sha(BASE / 'execution_inputs/RAN4.jsonl')
    assert execution['runner_sha256'] == protocol['original_runner_sha256'] == sha(PREP / 'execute_candidates.py')
    assert len(execution['items']) == 1
    item = execution['items'][0]
    assert item['id'] == task['id'] and item['status'] == 'OK'
    receipt_path = BASE / 'reference_outputs' / task['id'] / (task['reference_query_sha256'] + '.json')
    receipt = json.loads(receipt_path.read_text())
    native_path = BASE / receipt['rows_file']
    native = rows(native_path)
    assert receipt['query'] == task['reference_query']
    assert receipt['query_sha256'] == task['reference_query_sha256'] == item['query_sha256']
    assert receipt['rows_sha256'] == sha(native_path)
    assert receipt['rows_retained'] == len(native) == item['rows'] == 445
    assert native_path.stat().st_size == receipt['bytes_retained']
    assert (receipt['status'] == 'OK' and receipt['rollback_completed'] and receipt['full_rows_available']
            and not receipt['truncated'] and receipt['execution_summary_complete']
            and receipt['plan_query_type'] == receipt['execution_query_type'] == 'r')
    assert all(len(row) == len(receipt['columns']) for row in native)
    named = [dict(zip(receipt['columns'], row)) for row in native]
    witness = json.loads((BASE / 'source_pool_witness.json').read_text())
    actual = {(row['specNumber'], row['crCount']) for row in named}
    expected = {(row['specNumber'], row['crCount']) for row in witness['full_owned_pool']}
    assert actual == expected and len(actual) == len(native)
    assert all(type(row['specNumber']) is str and type(row['crCount']) is int for row in named)
    assert len({row['specNumber'] for row in named}) == len(named)
    assert [row['crCount'] for row in named] == sorted((row['crCount'] for row in named), reverse=True)
    projected = [{'specNumber': row['specNumber']} for row in named]
    _, projection_errors = scorer.project(projected, task['required_fields'], gold=True)
    assert not projection_errors
    groups = original_scorer.make_order_groups(task, named, projected)
    controls = contract_checks.checks(task, projected, groups)
    assert all(control['pass'] for control in controls)
    prediction = original_scorer.reference_prediction(task, projected)
    additional_controls = []
    for kind, answer, exact in [
        ('reverse_display_order_is_valid', list(reversed(prediction)), True),
        ('whole_eligible_pool_is_not_a_top10_answer', projected, False),
        ('eleven_answers_instead_of_ten', prediction + [projected[10]], False),
        ('lower_rank_replaces_higher_requested_member', prediction[1:] + [projected[10]], False),
    ]:
        outcome = original_scorer.score(task, projected, answer, diagnostic=True, order_groups=groups)
        assert outcome['exact'] is exact
        additional_controls.append({'check': kind, 'pass': True, 'expected_exact': exact, 'actual_exact': outcome['exact']})
    proof = {'status': 'PASS', 'id': task['id'], 'repair_sha256': task['repair_sha256'],
             'primary_sha256': sha(BASE / 'proposals.jsonl'), 'secondary_sha256': sha(BASE / 'secondary.jsonl'),
             'protocol_sha256': sha(BASE / 'execution_protocol.json'), 'receipt_sha256': sha(receipt_path),
             'rows_sha256': sha(native_path), 'full_native_rows_n': len(native), 'requested_k': 10,
             'full_pool_matches_independent_SQL_source': True, 'source_before_after_matches_preserved_parent': True,
             'official_common_source_sha256': sha(source / 'shared_source.txt'),
             'actual_scorer_controls': controls, 'actual_scorer_control_n': len(controls),
             'additional_boundary_and_order_controls': additional_controls,
             'all_controls_n': len(controls) + len(additional_controls), 'boundary_count': witness['boundary_count'],
             'observed_boundary_tie_n': witness['boundary_tie_n'], 'unclassified_spec_max_count': witness['unclassified_max_count'],
             'new_model_calls': 0, 'expert_validation_n': 0, 'admitted_by_this_capture': False,
             'scope': 'Original-question frozen graph-relative owner ranking repair; extra ownership source must be identically exposed to all new model arms; not full raw-archive truth'}
    out = BASE / 'native_capture_check.json'
    out.write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': proof['status'], 'rows': len(native), 'scorer_controls': len(controls),
                      'additional_boundary_controls': len(additional_controls), 'proof_sha256': sha(out)}))


if __name__ == '__main__':
    main()
