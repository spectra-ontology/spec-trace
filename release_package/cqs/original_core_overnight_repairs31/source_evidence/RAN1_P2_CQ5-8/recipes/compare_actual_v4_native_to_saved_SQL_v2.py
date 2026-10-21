"""Compare a future ROOT-owned exact native capture to the saved immutable SQL.

This program only reads existing capture files. It never starts a container,
queries a database, observes memory, or creates a model result.
"""
import sys
if sys.flags.optimize:
    raise SystemExit('Run without optimization')
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native-capture', type=Path, required=True)
    p.add_argument('--owned-outer-receipt', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    if args.out.exists():
        raise SystemExit('Preserve previous comparison')
    local = Path(__file__).absolute().parent / 'recorded_CR_recovery_v4'
    def load(path):
        return json.loads(path.read_text())
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()
    def pin(path):
        return {'path': str(path.absolute()), 'bytes': path.stat().st_size,
                'sha256': digest(path)}
    definition = load(local / 'definition.json')
    repair = hashlib.sha256(json.dumps(definition, ensure_ascii=False, sort_keys=True,
        separators=(',', ':')).encode()).hexdigest()
    assert repair == 'cc1ba3d9d67d1716ffdee8bb1e5c2d6353b22be4a13f410f5268dc633068a342'
    query_hash = hashlib.sha256(definition['reference_query'].encode()).hexdigest()
    native_file = args.native_capture / 'reference_outputs' / definition['id'] / (query_hash + '.json')
    native = load(native_file)
    assert native['id'] == definition['id'] and native['wg'] == 'RAN1'
    assert native['query'] == definition['reference_query'] and native['query_sha256'] == query_hash
    assert native['status'] == 'OK'
    assert all(native.get(k) is True for k in ['full_rows_available', 'rollback_completed', 'execution_summary_complete'])
    assert native['execution_query_type'] == native['plan_query_type'] == 'r'
    assert native['truncated'] is False and type(native['rows_retained']) is int and native['rows_retained'] == 10
    assert native['columns'] == ['m.meetingNumber', 'a.resolutionId', 'content']
    expected_relative_rows = 'reference_outputs/' + definition['id'] + '/' + query_hash + '.jsonl'
    assert native['rows_file'] == expected_relative_rows
    rows_file = args.native_capture / expected_relative_rows
    assert digest(rows_file) == native['rows_sha256']
    rows = [json.loads(line) for line in rows_file.read_text().splitlines()]
    assert len(rows) == 10 and all(type(r) is list and len(r) == 3 and all(type(v) is str for v in r) for r in rows)
    reference_file = local / 'expected_native_selected10_all3columns.jsonl'
    assert digest(reference_file) == '861886dd4d131851c693a63e54a5cd49876419a73c396290a331a91c88ba8dc6'
    reference = [json.loads(line) for line in reference_file.read_text().splitlines()]
    expected = [[row[k] for k in native['columns']] for row in reference]
    assert Counter(map(tuple, rows)) == Counter(map(tuple, expected)), 'Native full3-column values differ from SQL'
    execution_file = args.native_capture / 'execution_RAN1.json'
    execution = load(execution_file)
    assert execution['inventory_unchanged'] is True
    outer = load(args.owned_outer_receipt)
    assert outer['status'] == 'PASS' and outer['child_exit'] == 0
    assert outer['owned_cleanup']['owned_stopped'] is True
    result = {'status': 'PASS_ACTUAL_NATIVE10_FULL3_COLUMNS_EQUALS_SAVED_SQL',
        'id': definition['id'], 'repair_sha256': repair, 'native_rows': len(rows),
        'all3_columns_typed_equal': True, 'comparison': 'multiset, preserving join multiplicity; original meeting-only selection, not a new within-meeting serialization order',
        'native_read_rollback_and_untruncated': True, 'owned_stopped': True,
        'pins': [pin(q) for q in [Path(__file__), local / 'definition.json', reference_file,
            native_file, rows_file, execution_file, args.owned_outer_receipt]],
        'new_native_calls_by_this_checker': 0, 'API_calls': 0, 'new_admissions': 0}
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'receipt': pin(args.out)}))

if __name__ == '__main__':
    main()
