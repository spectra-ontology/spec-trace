#!/usr/bin/env python3
"""Check complete native counts and memberships against retained source tuples."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
PREP = BASE.parents[3]
sys.path[:0] = [str(PREP / 'original_repair'), str(PREP)]
import contract_checks
import original_scorer
import scorer


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extra_controls(task, records, groups):
    results = []

    def require(name, predictions, expected):
        outcome = original_scorer.score(task, records, predictions, diagnostic=True, order_groups=groups)
        results.append({'check': name, 'pass': outcome['exact'] is expected})

    require('omit_graph_zero_meetings', [r for r in records if r['resolutionCount']], False)
    require('duplicate_meeting_displaces_required_meeting', records[:-1] + records[:1], False)
    wrong = [dict(r) for r in records]
    zero = next(i for i, row in enumerate(wrong) if not row['resolutionCount'])
    wrong[zero]['resolutionCount'] = 1
    require('invent_resolution_at_observed_zero', wrong, False)
    within = [r for group in groups for r in reversed(group)]
    assert any(len(group) > 1 for group in groups)
    require('any_order_within_source_ordinal_ties', within, True)
    across = list(records)
    left = 0
    right = len(groups[0])
    across[left], across[right] = across[right], across[left]
    require('incorrect_order_across_source_ordinals', across, False)
    return results


def main():
    proposals = [json.loads(line) for line in (BASE / 'proposals.jsonl').read_text().splitlines()]
    probe_path = BASE.parent / 'trend_scope_source_probe.json'
    probe = json.loads(probe_path.read_text())
    run = BASE / 'native'
    proofs, gold = [], []
    for task in proposals:
        identifier, wg = task['id'], task['id'].split('_')[0]
        witness_path = BASE / (identifier + '_source_witness.json')
        witness = json.loads(witness_path.read_text())
        source = probe[wg]
        assert source['sqlite_sha256'] == witness['source_sqlite_sha256']
        assert witness['source_probe']['sha256'] == sha(probe_path)
        meetings = source['whole_meetings']
        assert len(meetings) == len({m['node_id'] for m in meetings}) == 58
        assert len({m['canonicalMeetingNumber'] for m in meetings}) == 58
        memberships = {m['canonicalMeetingNumber']: {} for m in meetings}
        for row in source['resolution_agenda_MADE_AT_pairs']:
            assert row['agendaNumber'] == witness['agendaNumber']
            memberships[row['canonicalMeetingNumber']][row['resolutionNode']] = row['resolutionId']
        expected = {m['canonicalMeetingNumber']: {'meetingNumber': m['canonicalMeetingNumber'],
                    'meetingOrdinal': m['meetingNumberInt'],
                    'resolutionCount': len(memberships[m['canonicalMeetingNumber']])} for m in meetings}
        assert {row['canonicalMeetingNumber']: row['resolutionCount'] for row in witness['all_source_count_records']} == {
            key: row['resolutionCount'] for key, row in expected.items()}
        execution_path = run / ('execution_' + wg + '.json')
        execution = json.loads(execution_path.read_text())
        assert execution['source_before'] == execution['source_after'] and execution['inventory_unchanged']
        assert execution['input_sha256'] == sha(run / 'execution_inputs' / (wg + '.jsonl'))
        assert execution['protocol_sha256'] == sha(run / 'execution_protocol.json')
        assert execution['source_before']['source']['sha256'] == task['source_context']['graph_source_sha256']
        captured, receipts = {}, []
        for item in execution['items']:
            assert item['status'] == 'OK' and item['rows'] == 58
            receipt_path = run / 'reference_outputs' / item['id'] / (item['query_sha256'] + '.json')
            receipt = json.loads(receipt_path.read_text())
            rows_path = run / receipt['rows_file']
            positional = [json.loads(line) for line in rows_path.read_text().splitlines()]
            assert receipt['rows_sha256'] == sha(rows_path) and receipt['rows_retained'] == len(positional) == 58
            assert receipt['status'] == 'OK' and receipt['full_rows_available'] and not receipt['truncated']
            assert receipt['rollback_completed'] and receipt['execution_summary_complete']
            assert receipt['execution_query_type'] == receipt['plan_query_type'] == 'r'
            assert hashlib.sha256(receipt['query'].encode()).hexdigest() == item['query_sha256']
            captured[item['id']] = [dict(zip(receipt['columns'], row)) for row in positional]
            receipts.append({'id': item['id'], 'rows_n': 58, 'query_sha256': item['query_sha256'],
                'receipt_file': str(receipt_path.relative_to(BASE)), 'receipt_sha256': sha(receipt_path),
                'rows_file': str(rows_path.relative_to(BASE)), 'rows_sha256': sha(rows_path)})
        named = captured[identifier]
        assert {r['meetingNumber']: r for r in named} == expected
        diagnostic = captured[identifier + '_FULL_MEMBERSHIP']
        assert len({r['meetingNumber'] for r in diagnostic}) == 58
        for row in diagnostic:
            values = list(memberships[row['meetingNumber']].values())
            assert all(type(value) is str for value in values) and len(set(values)) == len(values)
            assert len(row['resolutionIds']) == len(set(row['resolutionIds'])) == len(values)
            assert set(row['resolutionIds']) == set(values)
            assert row['meetingOrdinal'] == expected[row['meetingNumber']]['meetingOrdinal']
        records = [{field['name']: row[field['source_column_or_expression']] for field in task['required_fields']} for row in named]
        _, errors = scorer.project(records, task['required_fields'], gold=True)
        assert not errors
        groups = original_scorer.make_order_groups(task, named, records)
        controls = contract_checks.checks(task, records, groups)
        extra = extra_controls(task, records, groups)
        assert all(row['pass'] for row in controls + extra)
        running = subprocess.check_output(['docker', 'inspect', '--format', '{{.State.Running}}',
                                          'kdd-db-frozen-v1-' + wg.lower()], text=True).strip()
        assert running == 'false'
        proofs.append({'id': identifier, 'repair_sha256': task['repair_sha256'],
            'criteria_sha256': task['criteria_sha256'], 'source_probe_sha256': sha(probe_path),
            'source_witness_sha256': sha(witness_path), 'execution_report_sha256': sha(execution_path),
            'native_receipts': receipts, 'requested_records_n': 58,
            'source_node_count_native_count_and_ID_membership_all_equal': True,
            'source_before_after_unchanged': True, 'owned_container_stopped': True,
            'requested_field_errors': errors, 'scorer_controls': controls, 'extra_scorer_controls': extra,
            'scope': witness['scope']})
        gold.append({'id': identifier, 'repair_sha256': task['repair_sha256'], 'records': records, 'order_groups': groups})
    proof = {'status': 'NATIVE_FULL_SOURCE_AND_SCORER_PASS', 'candidate_ids': [p['id'] for p in proofs],
        'items': proofs, 'native_total_rows_n': 232, 'requested_gold_records_n': 116,
        'standard_scorer_controls_n': sum(len(p['scorer_controls']) for p in proofs),
        'additional_scorer_controls_n': sum(len(p['extra_scorer_controls']) for p in proofs),
        'new_model_calls': 0, 'human_author_validation_n': 0, 'expert_validation_n': 0,
        'admission': 'Separate bundle construction requires both exact-pinned semantic judgments.'}
    (BASE / 'native_capture_check.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n')
    (BASE / 'candidate_gold.jsonl').write_text(''.join(scorer.get_kernel().json_exact(row) + '\n' for row in gold))
    print(json.dumps({'status': proof['status'], 'native_rows': 232, 'requested_records': 116,
        'controls': proof['standard_scorer_controls_n'] + proof['additional_scorer_controls_n'],
        'proof_sha256': sha(BASE / 'native_capture_check.json')}))


if __name__ == '__main__':
    main()
