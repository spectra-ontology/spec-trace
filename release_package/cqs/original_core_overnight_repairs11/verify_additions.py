#!/usr/bin/env python3
"""Offline portable check of immutable additional3; makes no API calls."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import scorer
import original_scorer
import review_schema
import contract_checks

KEYS = ['id', 'question_en', 'original_query', 'reference_query', 'required_fields',
        'collection', 'cardinality_policy', 'repair_class', 'original_question_preserved']


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):
    return json.loads(Path(p).read_text())


def lines(p):
    return [scorer.get_kernel().loads_exact(s) for s in Path(p).read_text().splitlines() if s.strip()]


def canonical(v):
    return scorer.get_kernel().json_exact(v)


def digest(v):
    return hashlib.sha256(canonical(v).encode()).hexdigest()


def unique(rows):
    result = {r['id']: r for r in rows}
    assert len(result) == len(rows)
    return result


def verify(bundle, parent=None):
    bundle = Path(bundle).resolve()
    manifest = read(bundle / 'manifest.json')
    actual_files = {str(p.relative_to(bundle)) for p in bundle.rglob('*') if p.is_file() and p.name != 'manifest.json'}
    # Only the top-level manifest is excluded; similarly named witness files are covered.
    actual_files = {str(p.relative_to(bundle)) for p in bundle.rglob('*') if p.is_file() and p != bundle / 'manifest.json'}
    assert actual_files == set(manifest['files'])
    for rel, expected in manifest['files'].items():
        assert (bundle / rel).resolve().is_relative_to(bundle)
        assert sha(bundle / rel) == expected, rel
    scope = read(bundle / 'authorization/scope.json')
    assert sha(bundle / 'authorization/scope.json') == manifest['authorization_scope_sha256']
    assert sha(bundle / 'authorization/admission_inputs.json') == manifest['authorization_admission_inputs_sha256']
    cases = unique(scope['cases'])
    tasks, gold, controls = [unique(lines(bundle / n)) for n in ('tasks.jsonl', 'reference_gold.jsonl', 'scorer_checks.jsonl')]
    assert set(tasks) == set(gold) == set(controls) == set(cases) and len(tasks) == 3
    assert set(manifest['cohort_ids']) == set(tasks)
    originals = unique(lines(bundle / 'provenance/original_benchmark.jsonl'))
    baseline = unique(lines(bundle / 'baseline460/all_core_dispositions.jsonl'))
    ledger = unique(lines(bundle / 'all_core_dispositions.jsonl'))
    assert len(originals) == 624 and len(baseline) == len(ledger) == 560
    assert set(baseline) <= set(originals)
    assert sum(r['status'] == 'pass' for r in baseline.values()) == 460
    assert not set(tasks) & {i for i, r in baseline.items() if r['status'] == 'pass'}
    for ident in set(baseline) - set(tasks):
        assert baseline[ident] == ledger[ident]
    assert sum(r['status'] == 'pass' for r in ledger.values()) == 463
    criteria = read(bundle / 'criteria.json')
    criteria_sha = sha(bundle / 'criteria.json')
    native_n, control_n = 0, 0
    for ident, task in tasks.items():
        original = originals[ident]
        assert task['question_en'] == original['question_en']
        assert task['original_query'] == original['cypher']
        assert task['original_question_preserved'] is True
        assert task['repair_sha256'] == digest({k: task[k] for k in KEYS}) == cases[ident]['repair_sha256']
        assert task['validation_status'] == 'validated'
        assert task['human_author_review_completed'] is False and task['expert_validation_n'] == 0
        for role in ('primary_review', 'secondary_review'):
            review = task[role]
            review_schema.check_pass(review, task['question_en'], criteria['semantic_units'],
                criteria_sha=criteria_sha, identity_key='repair_sha256', identity_sha=task['repair_sha256'])
            assert review['human_author_review_completed'] is False and review['expert_validation_n'] == 0
        assert task['primary_review']['reviewer_kind'] != task['secondary_review']['reviewer_kind']
        assert sha(bundle / ('definitions/' + ident + '.json')) == cases[ident]['definition']['sha256']
        evidence = task['portable_native_evidence']
        for key in ('receipt', 'rows', 'run_report'):
            assert sha(bundle / evidence[key + '_file']) == evidence[key + '_sha256']
        receipt = read(bundle / evidence['receipt_file'])
        assert receipt['id'] == ident and receipt['query'] == task['reference_query']
        assert receipt['query_sha256'] == hashlib.sha256(task['reference_query'].encode()).hexdigest()
        assert receipt['status'] == 'OK' and receipt['full_rows_available'] is True
        assert receipt['truncated'] is False and receipt['rollback_completed'] is True
        assert receipt['execution_summary_complete'] is True
        assert receipt['plan_query_type'] == receipt['execution_query_type'] == 'r'
        assert receipt['rows_sha256'] == evidence['rows_sha256']
        positional = lines(bundle / evidence['rows_file'])
        assert all(type(r) is list and len(r) == len(receipt['columns']) for r in positional)
        native = [dict(zip(receipt['columns'], r)) for r in positional]
        assert len(native) == receipt['rows_retained'] == task['native_rows']
        run = read(bundle / evidence['run_report_file'])
        assert run['inventory_unchanged'] is True and run['model_calls'] == 0 and run['expert_validation'] is False
        wg = ident.split('_')[0]
        assert run['source_before'] == run['source_after'] == manifest['graph_sources'][wg]
        item = next(r for r in run['items'] if r['id'] == ident)
        assert item['status'] == 'OK' and item['query_sha256'] == receipt['query_sha256'] and item['rows'] == len(native)
        for key, pin in evidence['chain'].items():
            assert sha(bundle / pin['file']) == pin['sha256']
        assert evidence['chain']['execution_inputs']['sha256'] == run['input_sha256']
        assert evidence['chain']['execution_protocol']['sha256'] == run['protocol_sha256']
        input_task = next(r for r in lines(bundle / evidence['chain']['execution_inputs']['file']) if r['id'] == ident)
        assert input_task['candidate_query'] == task['reference_query']
        sql_pin = task['portable_independent_SQL_evidence']
        assert sha(bundle / sql_pin['file']) == sql_pin['sha256']
        sql = read(bundle / sql_pin['file'])
        records_pin = sql['portable_independent_records']
        assert sha(bundle / records_pin['file']) == records_pin['sha256'] == sql['independent_records_sha256']
        independent = lines(bundle / records_pin['file'])
        assert sql['all_return_fields_compared'] is True and sql['uncapped_SQL'] is True
        assert sql['native_receipt_sha256'] == evidence['receipt_sha256']
        assert sql['native_rows_sha256'] == evidence['rows_sha256']
        assert Counter(map(canonical, native)) == Counter(map(canonical, independent))
        assert all(set(r) == set(receipt['columns']) for r in independent)
        projected = [{f['name']: r[f['name'] if f['name'] in r else f['source_column_or_expression']]
                      for f in task['required_fields']} for r in native]
        assert gold[ident]['repair_sha256'] == task['repair_sha256']
        assert gold[ident]['records'] == projected
        assert task['projected_records_sha256'] == digest(projected)
        groups = original_scorer.make_order_groups(task, native, projected) if task['collection']['kind'] in {
            'native_ordered_ties', 'top_k_boundary_ties'} else None
        assert groups == gold[ident]['order_groups']
        actual = contract_checks.checks(task, projected, groups)
        assert actual == controls[ident]['checks'] and all(c['pass'] for c in actual)
        assert controls[ident]['repair_sha256'] == task['repair_sha256']
        for role, pin in task['portable_gate_evidence'].items():
            if pin.get('embedded_in_definition'):
                assert digest(read(bundle / pin['file'])) == pin['embedded_digest'] == cases[ident]['gate_files'][role]['sha256']
            else:
                assert pin['sha256'] == cases[ident]['gate_files'][role]['sha256']
            assert sha(bundle / pin['file']) == pin['sha256']
        assert task['portable_source_evidence']
        for pin in task['portable_source_evidence']:
            assert sha(bundle / pin['file']) == pin['sha256']
        native_n += len(native)
        control_n += len(actual)
    assert native_n == manifest['native_rows'] and control_n == manifest['actual_scorer_controls']
    assert manifest['global_admitted_union_n'] == 463 and manifest['global_unresolved_n'] == 97
    assert manifest['model_predictions_n'] == manifest['expert_validation_n'] == 0
    import importlib.util
    spec=importlib.util.spec_from_file_location('authorized11_saved_controls',bundle/'verify_saved_controls.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    additional=module.verify(bundle)
    assert additional['status']=='PASS'
    return {'status': 'PASS', 'check_scope': 'AUTHORIZED_INCREMENTAL11_ORIGINAL_NATIVE_SQL_SCORER', 'additional_admitted_n': 3,
        'global_admitted_union_n': 463, 'global_unresolved_n': 97, 'native_rows': native_n,
        'actual_scorer_controls': control_n, 'model_predictions_n': 0, 'expert_validation_n': 0,
        'additional_saved_control_replay': additional,
        'bundle_manifest_sha256': sha(bundle / 'manifest.json')}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle', type=Path, default=BASE)
    p.add_argument('--parent', type=Path, default=None)
    args = p.parse_args()
    print(json.dumps(verify(args.bundle, args.parent)))
