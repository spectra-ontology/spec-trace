#!/usr/bin/env python3
"""Verify the exact approval capture and nested requested-field controls."""
import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import time

HERE = Path(__file__).resolve().parent
PREP = HERE.parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(PREP / 'original_repair'))
import build


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    target = HERE / 'native_capture_check.json'
    if target.exists():
        raise ValueError('Refuse to replace a completed capture check')
    task = build.read(HERE / 'candidates_scope_reviewed.jsonl')[0]
    second = build.read(HERE / 'secondary.jsonl')[0]
    criteria = json.loads((PREP / 'original_repair/criteria.json').read_text())
    for judgment in [task['primary_review'], second]:
        build.review_schema.check_pass(judgment, task['question_en'], criteria['semantic_units'],
            criteria_sha=task['criteria_sha256'], identity_key='repair_sha256',
            identity_sha=task['repair_sha256'])
    before_base = build.native.BASE
    try:
        build.native.BASE = HERE
        rows, receipt = build.native.references({'id': task['id'], 'candidate_query': task['reference_query']})
    finally:
        build.native.BASE = before_base
    if rows is None:
        raise ValueError('No complete exact-query native output')
    records = build.native.answer_projection(rows, task['required_fields'], receipt['columns'])
    if len(records) != 35 or len({r['meeting'] for r in records}) != 35:
        raise ValueError('Incomplete or duplicate meeting mapping')
    control_results = build.checks(task, records)
    predictions = build.original_scorer.reference_prediction(task, records)

    def require(name, predicted, expected):
        result = build.original_scorer.score(task, records, predicted, diagnostic=True)
        control_results.append({'check': name, 'pass': result['exact'] is expected})

    reversed_all = [dict(r, specNumbers=list(reversed(r['specNumbers']))) for r in reversed(predictions)]
    require('outer_and_nested_set_order_is_irrelevant', reversed_all, True)
    nonempty_index = next(i for i, r in enumerate(predictions) if r['specNumbers'])
    empty_index = next(i for i, r in enumerate(predictions) if not r['specNumbers'])
    duplicated = copy.deepcopy(predictions)
    duplicated[nonempty_index]['specNumbers'].append(duplicated[nonempty_index]['specNumbers'][0])
    require('nested_set_duplicate_does_not_change_answer', duplicated, True)
    missing_nested = copy.deepcopy(predictions)
    missing_nested[nonempty_index]['specNumbers'].pop()
    require('missing_requested_spec_within_meeting_rejected', missing_nested, False)
    extra_nested = copy.deepcopy(predictions)
    extra_nested[nonempty_index]['specNumbers'].append('__WRONG_SPEC_NUMBER__')
    require('extra_wrong_spec_within_meeting_rejected', extra_nested, False)
    wrong_nested_type = copy.deepcopy(predictions)
    wrong_nested_type[nonempty_index]['specNumbers'][0] = 123
    require('nested_non_string_spec_rejected', wrong_nested_type, False)
    missing_zero_meeting = predictions[:empty_index] + predictions[empty_index + 1:]
    require('zero_result_meeting_omission_rejected', missing_zero_meeting, False)
    altered_empty = copy.deepcopy(predictions)
    altered_empty[empty_index]['specNumbers'] = ['__WRONG_SPEC_NUMBER__']
    require('invented_spec_for_empty_meeting_rejected', altered_empty, False)
    if not all(r['pass'] for r in control_results):
        raise ValueError('Requested-field/nested-set control failed')

    db = HERE.parents[1] / 'relational/RAN5.sqlite'
    db_before = sha(db)
    if db_before != task['source_context']['SQL_source_sha256']:
        raise ValueError('Frozen SQL source mismatch')
    identity_before = (db.stat().st_size, db.stat().st_mtime_ns)
    codes = task['source_context']['source_owned_spec_numbers']
    sql = ('SELECT m.canonicalMeetingNumber, found.specNumber FROM Meeting m LEFT JOIN '
           '(SELECT DISTINCT p.dst_id AS meeting_node, s.specNumber FROM CR cr '
           'JOIN rel_PRESENTED_AT p ON p.src_id=cr.node_id '
           'JOIN rel_MODIFIES x ON x.src_id=cr.node_id JOIN Spec s ON s.node_id=x.dst_id '
           "WHERE cr.status='approved' AND s.specNumber IN (" + ','.join('?' for _ in codes) + ')) found '
           'ON found.meeting_node=m.node_id ORDER BY m.canonicalMeetingNumber, found.specNumber')
    con = sqlite3.connect(db.as_uri() + '?mode=ro&immutable=1', uri=True)
    con.execute('PRAGMA query_only=ON')
    con.execute('PRAGMA cache_size=-32768')
    started = time.monotonic()
    con.set_progress_handler(lambda: int(time.monotonic() - started > 20), 10000)
    expected = {}
    for meeting, number in con.execute(sql, codes):
        expected.setdefault(meeting, set())
        if number is not None:
            expected[meeting].add(number)
    con.close()
    if identity_before != (db.stat().st_size, db.stat().st_mtime_ns) or sha(db) != db_before:
        raise ValueError('Read-only SQL source changed')
    captured = {r['meeting']: set(r['specNumbers']) for r in records}
    if captured != expected:
        raise ValueError('Captured native mapping disagrees with full read-only SQL projection')
    run = json.loads((HERE / 'execution_RAN5.json').read_text())
    if not run['inventory_unchanged'] or run['source_before'] != run['source_after']:
        raise ValueError('Frozen source inventory changed')
    rows_path = Path(receipt['rows_file'])
    if not rows_path.is_absolute():
        rows_path = HERE / rows_path
    report = {
        'id': task['id'], 'repair_sha256': task['repair_sha256'],
        'active_proposals_sha256': sha(HERE / 'candidates_scope_reviewed.jsonl'),
        'secondary_sha256': sha(HERE / 'secondary.jsonl'), 'tool_sha256': sha(__file__),
        'input_sha256': sha(HERE / 'execution_inputs/RAN5.jsonl'),
        'protocol_sha256': sha(HERE / 'execution_protocol.json'),
        'native_run_sha256': sha(HERE / 'execution_RAN5.json'),
        'receipt_path': receipt['receipt_path'], 'receipt_sha256': sha(receipt['receipt_path']),
        'rows_path': str(rows_path), 'rows_sha256': sha(rows_path),
        'native_rows': len(rows), 'requested_records': len(records),
        'nonempty_meetings': sum(bool(r['specNumbers']) for r in records),
        'empty_meetings': sum(not r['specNumbers'] for r in records),
        'asked_positive_meeting_spec_pairs': sum(len(r['specNumbers']) for r in records),
        'all35_meetings_complete': True, 'nested_spec_sets_complete': True,
        'projected_records_sha256': build.digest(records),
        'full_exact_native_receipt_validated': True, 'frozen_source_before_after': run['source_before'],
        'read_only_SQL_crosscheck': {'query': sql, 'parameters': codes,
            'db_sha256_before_after': db_before, 'actual_complete_mapping_equal': True},
        'checks': control_results, 'all_checks_pass': True,
        'new_model_calls': 0, 'human_author_review_completed': False, 'expert_validation_n': 0,
        'public_repository_mutated': False,
        'scope': 'New exact reference capture and requested-field tests; portable bundle integration/admission is separate.'}
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'path': str(target), 'sha256': sha(target),
        'native_rows': len(rows), 'empty_meetings': report['empty_meetings'],
        'nonempty_meetings': report['nonempty_meetings'], 'scorer_controls': len(control_results),
        'all_checks_pass': True}))


if __name__ == '__main__':
    main()
