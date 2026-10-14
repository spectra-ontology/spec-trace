#!/usr/bin/env python3
"""Offline native/SQL full-pool equality and strict requested-field controls."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
PREP = BASE.parents[3]
ORIG = PREP / 'original_repair'
sys.path[:0] = [str(ORIG), str(PREP)]
import build
import contract_checks
import original_scorer
import scorer


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    proposal_path = BASE / 'proposals.jsonl'
    proposal = json.loads(proposal_path.read_text())
    witness_path = BASE.parent / 'path_top5_count_unit_invariance.json'
    witness = json.loads(witness_path.read_text())
    run = BASE / 'native'
    execution_path = run / 'execution_RAN3.json'
    execution = json.loads(execution_path.read_text())
    assert execution['source_before'] == execution['source_after'] and execution['inventory_unchanged']
    assert execution['input_sha256'] == sha(run / 'execution_inputs/RAN3.jsonl')
    assert execution['protocol_sha256'] == sha(run / 'execution_protocol.json')
    assert execution['source_before']['source']['sha256'] == witness['source_graph_sha256']
    receipts = []
    captured = {}
    for item in execution['items']:
        assert item['status'] == 'OK' and item['rows'] == len(witness['full_pool']) == 139
        receipt_path = run / 'reference_outputs' / item['id'] / (item['query_sha256'] + '.json')
        receipt = json.loads(receipt_path.read_text())
        rows_path = run / receipt['rows_file']
        positional = [json.loads(line) for line in rows_path.read_text().splitlines()]
        assert receipt['rows_sha256'] == sha(rows_path) and receipt['rows_retained'] == len(positional)
        assert receipt['status'] == 'OK' and receipt['full_rows_available'] and not receipt['truncated']
        assert receipt['rollback_completed'] and receipt['execution_summary_complete']
        assert receipt['execution_query_type'] == receipt['plan_query_type'] == 'r'
        assert hashlib.sha256(receipt['query'].encode()).hexdigest() == item['query_sha256']
        named = [dict(zip(receipt['columns'], row)) for row in positional]
        captured[item['id']] = named
        receipts.append({'id': item['id'], 'rows_n': len(named), 'query_sha256': item['query_sha256'],
                         'receipt_file': str(receipt_path.relative_to(BASE)), 'receipt_sha256': sha(receipt_path),
                         'rows_file': str(rows_path.relative_to(BASE)), 'rows_sha256': sha(rows_path)})
    diagnostic_id = proposal['id'] + '_COUNT_UNIT_WITNESS'
    assert sorted(captured[diagnostic_id], key=lambda row: row['specNumber']) == witness['full_pool']
    named = captured[proposal['id']]
    expected = [{'specNumber': row['specNumber'], 'crCount': row['crEntityCount']} for row in witness['full_pool']]
    assert sorted(named, key=lambda row: row['specNumber']) == expected
    records = [{'specNumber': row['specNumber']} for row in named]
    _, field_errors = scorer.project(records, proposal['required_fields'], gold=True)
    assert not field_errors
    groups = original_scorer.make_order_groups(proposal, named, records)
    controls = contract_checks.checks(proposal, records, groups)
    assert all(control['pass'] for control in controls)
    requested = original_scorer.reference_prediction(proposal, records)
    assert sorted(row['specNumber'] for row in requested) == witness['requested_identity_set']
    state = subprocess.check_output(['docker', 'inspect', '--format', '{{.State.Running}}',
                                     'kdd-db-frozen-v1-ran3'], text=True).strip()
    assert state == 'false'
    proof = {'status': 'NATIVE_FULL_POOL_AND_SCORER_PASS_NOT_ADMITTED', 'id': proposal['id'],
             'repair_sha256': proposal['repair_sha256'], 'criteria_sha256': proposal['criteria_sha256'],
             'proposal_sha256': sha(proposal_path), 'source_witness_sha256': sha(witness_path),
             'execution_report_sha256': sha(execution_path), 'capture_protocol_sha256': sha(run / 'execution_protocol.json'),
             'native_receipts': receipts, 'native_total_rows_n': 278, 'requested_reference_answer_n': 5,
             'complete_native_four_metrics_equal_full_SQL_source': True,
             'complete_native_reference_equal_full_SQL_CR_unit': True,
             'source_before_after_unchanged': True, 'owned_container_stopped': True,
             'requested_field_errors': field_errors, 'actual_scorer_controls': controls,
             'actual_scorer_controls_n': len(controls), 'new_model_calls': 0,
             'human_author_validation_n': 0, 'expert_validation_n': 0,
             'secondary_review_gate': 'Root independent second original-question judgment remains separate; this technical proof is not semantic approval or admission.',
             'scope_limit': witness['scope_limit']}
    (BASE / 'native_capture_check.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n')
    (BASE / 'candidate_gold.jsonl').write_text(scorer.get_kernel().json_exact({'id': proposal['id'],
        'repair_sha256': proposal['repair_sha256'], 'records': records, 'order_groups': groups}) + '\n')
    print(json.dumps({'status': proof['status'], 'native_rows': 278, 'controls': len(controls),
                      'proof_sha256': sha(BASE / 'native_capture_check.json')}))


if __name__ == '__main__':
    main()
