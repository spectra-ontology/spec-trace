#!/usr/bin/env python3
"""Offline source-tuple, complete membership and strict scoring verification."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(bundle, parent):
    sys.path.insert(0, str(bundle))
    import verify_additions
    import scorer
    import original_scorer
    from source_evidence.check_native import extra_controls
    basic = verify_additions.verify(bundle, parent)
    manifest = json.loads((bundle / 'manifest.json').read_text())
    read = lambda path: [scorer.get_kernel().loads_exact(line) for line in path.read_text().splitlines() if line.strip()]
    probe = json.loads((bundle / 'source_evidence/trend_scope_source_probe.json').read_text())
    tasks = read(bundle / 'tasks.jsonl')
    gold = {row['id']: row for row in read(bundle / 'reference_gold.jsonl')}
    root_counts = {row['id']: row for row in read(bundle / 'source_evidence/root_independent_count_reconstruction.jsonl')}
    proof = json.loads((bundle / 'source_evidence/native_capture_check.json').read_text())
    proofs = {row['id']: row for row in proof['items']}
    extra_n, diagnostic_n = 0, 0
    for task in tasks:
        identifier, wg = task['id'], task['id'].split('_')[0]
        source = probe[wg]
        witness_path = bundle / ('source_evidence/' + identifier + '_source_witness.json')
        witness = json.loads(witness_path.read_text())
        completeness = task['completeness_witness']
        if (completeness['source_tuple_file'] != 'source_evidence/trend_scope_source_probe.json'
                or completeness['source_tuple_sha256'] != sha(bundle / completeness['source_tuple_file'])
                or completeness['source_witness_sha256'] != sha(witness_path)
                or source['sqlite_sha256'] != witness['source_sqlite_sha256']):
            raise ValueError('source-tuple completeness pins differ')
        meetings = source['whole_meetings']
        if (len(meetings) != 58 or len({row['node_id'] for row in meetings}) != 58
                or len({row['canonicalMeetingNumber'] for row in meetings}) != 58):
            raise ValueError('source Meeting population is not complete and unique')
        meeting_by_node = {row['node_id']: row for row in meetings}
        members = {row['canonicalMeetingNumber']: {} for row in meetings}
        for row in source['resolution_agenda_MADE_AT_pairs']:
            meeting = meeting_by_node[row['meetingNode']]
            if (row['agendaNumber'] != witness['agendaNumber']
                    or row['canonicalMeetingNumber'] != meeting['canonicalMeetingNumber']
                    or row['meetingNumberInt'] != meeting['meetingNumberInt']):
                raise ValueError('source association meeting or exact agenda role differs')
            members[row['canonicalMeetingNumber']][row['resolutionNode']] = row['resolutionId']
        expected = {row['canonicalMeetingNumber']: {'meetingNumber': row['canonicalMeetingNumber'],
            'meetingOrdinal': row['meetingNumberInt'], 'resolutionCount': len(members[row['canonicalMeetingNumber']])}
            for row in meetings}
        if {row['canonicalMeetingNumber']: row['resolutionCount'] for row in witness['all_source_count_records']} != {
                key: row['resolutionCount'] for key, row in expected.items()}:
            raise ValueError('source count witness differs from full relation tuples')
        if (root_counts[identifier]['source_probe_sha256'] != sha(bundle / completeness['source_tuple_file'])
                or root_counts[identifier]['reconstructed_count_records'] != witness['all_source_count_records']):
            raise ValueError('separate AI source reconstruction differs from full count witness')
        native = task['portable_native_evidence']
        receipt = json.loads((bundle / native['receipt_file']).read_text())
        named = [dict(zip(receipt['columns'], row)) for row in read(bundle / native['rows_file'])]
        if len(named) != 58 or {row['meetingNumber']: row for row in named} != expected:
            raise ValueError('native count output differs from source population or node counts')
        evidence = completeness['membership_diagnostic']
        diagnostic_receipt = json.loads((bundle / evidence['receipt_file']).read_text())
        positional = read(bundle / evidence['rows_file'])
        input_rows = read(bundle / native['chain']['execution_inputs'])
        matching = [row for row in input_rows if row['id'] == identifier + '_FULL_MEMBERSHIP']
        expected_query = task['reference_query'].replace(
            'WITH m, count(DISTINCT r) AS resolutionCount\nRETURN m.canonicalMeetingNumber AS meetingNumber, m.meetingNumberInt AS meetingOrdinal, resolutionCount',
            'RETURN m.canonicalMeetingNumber AS meetingNumber, m.meetingNumberInt AS meetingOrdinal,\n       collect(DISTINCT r.resolutionId) AS resolutionIds')
        if (len(matching) != 1 or matching[0]['candidate_query'] != expected_query
                or diagnostic_receipt['query'] != expected_query
                or diagnostic_receipt['query_sha256'] != hashlib.sha256(expected_query.encode()).hexdigest()
                or sha(bundle / evidence['receipt_file']) != evidence['receipt_sha256']
                or sha(bundle / evidence['rows_file']) != evidence['rows_sha256']
                or diagnostic_receipt['rows_sha256'] != evidence['rows_sha256']
                or len(positional) != 58 or diagnostic_receipt['rows_retained'] != 58):
            raise ValueError('complete diagnostic query, files or row identity differ')
        for key, value in {'status': 'OK', 'full_rows_available': True, 'truncated': False,
                           'rollback_completed': True, 'execution_summary_complete': True,
                           'execution_query_type': 'r', 'plan_query_type': 'r'}.items():
            if diagnostic_receipt.get(key) != value:
                raise ValueError('complete read diagnostic status differs: ' + key)
        diagnostic = [dict(zip(diagnostic_receipt['columns'], row)) for row in positional]
        if len(diagnostic) != 58 or len({row['meetingNumber'] for row in diagnostic}) != 58:
            raise ValueError('diagnostic full Meeting population differs')
        for row in diagnostic:
            values = list(members[row['meetingNumber']].values())
            if (any(type(value) is not str for value in values) or len(set(values)) != len(values)
                    or len(row['resolutionIds']) != len(set(row['resolutionIds']))
                    or set(row['resolutionIds']) != set(values)
                    or row['meetingOrdinal'] != expected[row['meetingNumber']]['meetingOrdinal']):
                raise ValueError('native membership differs from exact source Resolution entities')
        actual = extra_controls(task, gold[identifier]['records'], gold[identifier]['order_groups'])
        if actual != proofs[identifier]['extra_scorer_controls'] or not all(row['pass'] for row in actual):
            raise ValueError('additional actual scorer controls differ or fail')
        if (task['admitted'] is not True or task['native_execution_completed'] is not True
                or task['scorer_controls_completed'] is not True):
            raise ValueError('completed task metadata does not reflect actual admission gates')
        extra_n += len(actual)
        diagnostic_n += len(diagnostic)
    if (basic['native_rows'] + diagnostic_n != proof['native_total_rows_n']
            or basic['scorer_controls'] + extra_n != manifest['total_actual_scorer_controls']
            or diagnostic_n != manifest['diagnostic_native_rows']):
        raise ValueError('complete source and control accounting differs')
    return dict(basic, full_native_rows_including_membership=basic['native_rows'] + diagnostic_n,
                additional_scorer_controls=extra_n,
                total_actual_scorer_controls=basic['scorer_controls'] + extra_n,
                source_scope='Graph-recorded exact agenda associations across all 58 source Meeting nodes per WG; no calendar activity, archive completeness or bis chronology claim.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--parent', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.bundle, args.parent), ensure_ascii=False, indent=2))
