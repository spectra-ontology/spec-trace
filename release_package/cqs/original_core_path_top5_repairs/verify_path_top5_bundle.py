#!/usr/bin/env python3
"""Portable structural count-unit invariance gate; no model/SQL/Neo4j calls."""
import argparse
from collections import Counter, defaultdict
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
    standard = verify_additions.verify(bundle, parent)
    assert standard['status'] == 'PASS' and standard['additional_admitted_n'] == 1
    manifest = json.loads((bundle / 'manifest.json').read_text())
    for relative, expected in manifest['files'].items():
        assert sha(bundle / relative) == expected
    task = json.loads((bundle / 'tasks.jsonl').read_text())
    assert task['id'] == 'RAN3_P3_CQ4-4'
    assert [f['name'] for f in task['required_fields']] == ['specNumber']
    assert task['collection']['value'] == 5 and task['collection']['require_rank_order'] is False
    context = bundle / 'source_evidence/path_top5'
    witness = json.loads((context / 'path_top5_count_unit_invariance.json').read_text())
    independent = json.loads((context / 'root_source_checks.json').read_text())
    assert independent['repair_sha256'] == task['repair_sha256']
    counts = defaultdict(lambda: {'paths': 0, 'resolutions': set(), 'crs': set(), 'documents': set()})
    for specification, resolution, cr, document in independent['actual_path_records']:
        v = counts[specification]
        v['paths'] += 1
        v['resolutions'].add(resolution)
        v['crs'].add(cr)
        v['documents'].add(document)
    whole = [{'specNumber': number, 'pathCount': counts[number]['paths'],
              'resolutionCount': len(counts[number]['resolutions']),
              'crEntityCount': len(counts[number]['crs']),
              'crDocumentCount': len(counts[number]['documents'])}
             for number in sorted(independent['all_spec_numbers'])]
    assert whole == witness['full_pool'] and len(whole) == 139
    requested = witness['requested_identity_set']
    for metric in ('pathCount', 'resolutionCount', 'crEntityCount', 'crDocumentCount'):
        ranked = sorted(whole, key=lambda r: -r[metric])
        boundary = ranked[4][metric]
        eligible = sorted(row['specNumber'] for row in ranked if row[metric] >= boundary)
        assert eligible == requested and len(eligible) == 5 and ranked[5][metric] < boundary
    capture = json.loads((context / 'native_capture_check.json').read_text())
    assert capture['repair_sha256'] == task['repair_sha256'] and capture['actual_scorer_controls_n'] == 9
    assert all(test['pass'] for test in capture['actual_scorer_controls'])
    diagnostic = json.loads((context / 'count_unit_receipt.json').read_text())
    diagnostic_rows = [json.loads(line) for line in (context / 'count_unit_rows.jsonl').read_text().splitlines()]
    assert diagnostic['rows_sha256'] == sha(context / 'count_unit_rows.jsonl')
    assert diagnostic['status'] == 'OK' and diagnostic['full_rows_available'] and not diagnostic['truncated']
    assert diagnostic['execution_summary_complete'] and diagnostic['rollback_completed']
    assert diagnostic['plan_query_type'] == diagnostic['execution_query_type'] == 'r'
    assert diagnostic['query'] == witness['native_diagnostic_query']
    named = [dict(zip(diagnostic['columns'], row)) for row in diagnostic_rows]
    assert sorted(named, key=lambda r: r['specNumber']) == whole
    assert task['completeness_witness']['source_witness_sha256'] == sha(context / 'path_top5_count_unit_invariance.json')
    return {'status': 'PASS', 'additional_admitted_n': 1, 'full_specification_pool_n': 139,
            'independent_source_path_records_n': len(independent['actual_path_records']),
            'native_pool_rows_n': 139, 'native_diagnostic_rows_n': 139,
            'four_count_units_requested_identity_set_equal': True, 'boundary_eligibility_unambiguous': True,
            'actual_scorer_controls_n': 9, 'standard_addition_validation': standard,
            'new_model_or_database_calls': 0, 'human_expert_validation_n': 0,
            'complete_raw_archive_truth_certified': False, 'equal_counts_or_orders_claimed': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle', type=Path, default=Path(__file__).resolve().parent)
    p.add_argument('--parent', type=Path, required=True)
    p.add_argument('--out', type=Path)
    args = p.parse_args()
    result = verify(args.bundle.resolve(), args.parent.resolve())
    if args.out:
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
