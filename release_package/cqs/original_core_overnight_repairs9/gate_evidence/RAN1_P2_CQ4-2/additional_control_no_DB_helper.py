#!/usr/bin/env python3
"""Spec: Replay saved CQ026 or FL controls without executing queries.
Ontology: Exact requested record identities, cardinality and ordering contract.
Cycle: AUTH9 preservation helper; original scorer/kernel stay unchanged.
배경: Reuse completed native/SQL proofs instead of rerunning source queries.
사용: --task JSON --records JSONL --controls JSON --kernel-dir DIR [--groups JSON].
LLM 호출: None; no database, native engine, network or provider calls.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def pin(path):
    return {'path': str(path.resolve()), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('task', 'records', 'controls', 'kernel-dir'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--groups', type=Path)
    args = parser.parse_args()
    sys.path[:0] = [str(args.kernel_dir), str(args.kernel_dir.parent)]
    spec = importlib.util.spec_from_file_location('saved_control_original_scorer', args.kernel_dir / 'original_scorer.py')
    scorer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scorer)
    task = json.loads(args.task.read_text())
    rows = [json.loads(line) for line in args.records.read_text().splitlines() if line.strip()]
    fields = task['required_fields']
    for field in fields:
        scorer.typed.get_kernel().field_schema(field)
    records = [{field['name']: row.get(field['name']) for field in fields} for row in rows]
    groups = []
    if args.groups:
        value = json.loads(args.groups.read_text())
        groups = value.get('order_groups') if isinstance(value, dict) else value
    elif task['collection']['kind'] in {'top_k_boundary_ties', 'native_ordered_ties'}:
        groups = scorer.make_order_groups(task, rows, records)
    controls = json.loads(args.controls.read_text())
    outcomes = []
    for control in controls:
        checks = {}
        for diagnostic, label in ((True, 'actual_diagnostic'), (False, 'actual_validated')):
            contract = task if diagnostic else dict(task, validation_status='validated')
            result = scorer.score(contract, records, control['predictions'], order_groups=groups, diagnostic=diagnostic)
            assert result['exact'] is control['expected_exact'], (control['name'], result)
            assert result == control[label], (control['name'], label, result, control[label])
            checks[label] = True
        outcomes.append({'name': control['name'], 'saved_dual_mode_result_byte_semantics_equal': checks})
    print(json.dumps({'status': 'PASS', 'id': task['id'], 'repair_sha256': task['repair_sha256'],
                      'records_n': len(records), 'controls_n': len(controls), 'checks': outcomes,
                      'input_pins': [pin(p) for p in [args.task, args.records, args.controls] + ([args.groups] if args.groups else [])],
                      'query_execution_n': 0, 'API_calls_n': 0,
                      'limitation': 'Offline saved-control replay only; does not replace actual native/independent SQL or semantic source proof.'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
