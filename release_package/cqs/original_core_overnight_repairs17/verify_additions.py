#!/usr/bin/env python3
"""Offline verification of the exact authorized LTM recorded-baseline portable repair bundle.

Checks preserved baseline dispositions, question and repair identity, both AI
judgments, full typed native/SQL records, source guards and saved scorer controls.
No API, database, publication or central-registry operation is performed.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent

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
    global scorer, original_scorer, review_schema, contract_checks
    bundle = Path(bundle).resolve()
    sys.path.insert(0, str(bundle))
    import scorer
    import original_scorer
    import review_schema
    import contract_checks
    manifest = read(bundle / 'manifest.json')
    # Only the top-level manifest is excluded; similarly named witness files are covered.
    actual_files = {str(p.relative_to(bundle)) for p in bundle.rglob('*') if p.is_file() and p != bundle / 'manifest.json'}
    assert actual_files == set(manifest['files'])
    for rel, expected in manifest['files'].items():
        assert (bundle / rel).resolve().is_relative_to(bundle)
        assert sha(bundle / rel) == expected, rel
    scope = read(bundle / 'authorization/scope.json')
    assert sha(bundle / 'authorization/scope.json') == manifest['authorization_scope_sha256']
    assert sha(bundle / 'authorization/admission_inputs.json') == manifest['authorization_admission_inputs_sha256']
    assert scope['baseline_public_commit_observed'] == manifest['parent_public_commit'] == '307e9016f3968104e2d922a1ab13e9edf9709291'
    for name, expected in scope['source_registry_pins'].items():
        assert sha(bundle / 'authorization' / name) == expected
    assert sha(bundle / 'authorization' / scope['authorization_evidence_file']) == scope['authorization_evidence_sha256']
    baseline_n = scope['baseline_public_pass_n']
    target_n = scope['authorized_target_original_frozen_union_n']
    pending_n = scope['authorized_target_pending_n']
    assert baseline_n == 476 and target_n == baseline_n + 1 == 477 and pending_n == 83
    cases = unique(scope['cases'])
    assert set(cases) == {'RAN2_P3_P3-S8-CQ07'}
    tasks, gold, controls = [unique(lines(bundle / n)) for n in ('tasks.jsonl', 'reference_gold.jsonl', 'scorer_checks.jsonl')]
    assert set(tasks) == set(gold) == set(controls) == set(cases) and len(tasks) == 1
    assert set(manifest['cohort_ids']) == set(tasks)
    originals = unique(lines(bundle / 'provenance/original_benchmark.jsonl'))
    baseline = unique(lines(bundle / 'baseline/all_core_dispositions.jsonl'))
    ledger = unique(lines(bundle / 'all_core_dispositions.jsonl'))
    assert len(originals) == 624 and len(baseline) == len(ledger) == target_n + pending_n == 560
    index = read(bundle / 'baseline/index_manifest.json')
    assert index['repaired_n'] == baseline_n and index['pending_n'] == 560 - baseline_n
    for name, pin in scope['baseline_public_snapshot_pins'].items():
        assert sha(bundle / 'baseline' / name) == pin['sha256']
        assert (bundle / 'baseline' / name).stat().st_size == pin['bytes']
        assert manifest['baseline_public_snapshot_pins'][name] == {'file': 'baseline/' + name, 'sha256': pin['sha256']}
    assert manifest['graph_sources'] == index['source_snapshot']
    baseline_tasks = unique(lines(bundle / 'baseline/current_tasks.jsonl'))
    assert len(baseline_tasks) == baseline_n
    assert set(baseline_tasks) == {ident for ident, row in baseline.items() if row['status'] == 'pass'}
    assert set(baseline) <= set(originals)
    assert sum(r['status'] == 'pass' for r in baseline.values()) == baseline_n
    assert not set(tasks) & {i for i, r in baseline.items() if r['status'] == 'pass'}
    for ident in set(baseline) - set(tasks):
        assert baseline[ident] == ledger[ident]
    assert sum(r['status'] == 'pass' for r in ledger.values()) == target_n
    criteria = read(bundle / 'criteria.json')
    criteria_sha = sha(bundle / 'criteria.json')
    native_n, control_n = 0, 0
    for ident, task in tasks.items():
        original = originals[ident]
        assert task['question_en'] == original['question_en']
        assert task['original_query'] == original['cypher']
        assert task['original_question_preserved'] is True
        assert task['repair_sha256'] == '6da14fbf7af31ea1c132ab13dd4dde26c5af0479ea67fcd035f921baca5019ae'
        assert task['required_fields'] == cases[ident]['required_fields']
        assert [field['name'] for field in task['required_fields']] == ['all_loaded']
        assert task['collection'] == {'kind': 'multiset'}
        assert task['cardinality_policy'] == {'mode': 'exact', 'value': 1}
        assert task['required_fields'][0]['type'] == 'boolean' and task['required_fields'][0]['nullable'] is False
        assert ledger[ident] == {'id': ident, 'status': 'pass', 'repair_class': task['repair_class'], 'repair_sha256': task['repair_sha256'], 'question_preserved': True}
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
        assert receipt['columns'] == ['all_loaded']
        assert receipt['rows_sha256'] == evidence['rows_sha256']
        positional = lines(bundle / evidence['rows_file'])
        assert all(type(r) is list and len(r) == len(receipt['columns']) for r in positional)
        native = [dict(zip(receipt['columns'], r)) for r in positional]
        assert len(native) == receipt['rows_retained'] == task['native_rows'] == 1
        assert type(native[0]['all_loaded']) is bool and native[0]['all_loaded'] is False
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
        assert len(actual) == 7
        import verify_ltm_baseline_evidence as ltm
        source_recount = ltm.verify_source(bundle / 'source_baseline', task, native)
        assert source_recount == read(bundle / 'source_baseline/offline_source_recount.json')
        boolean_controls = ltm.strict_boolean_controls(task, projected, original_scorer)
        assert boolean_controls == read(bundle / 'source_baseline/strict_boolean_controls.json')
        assert len(boolean_controls) == manifest['strict_boolean_controls_n'] == 7
        assert manifest['recorded_baseline_items_n'] == 28
        saved_controls = read(bundle / task['portable_gate_evidence']['controls']['file'])
        assert saved_controls['controls'] == actual
        assert saved_controls['status'] == 'controls_pass'
        assert saved_controls['repair_sha256'] == task['repair_sha256']
        assert saved_controls['query_sha256'] == receipt['query_sha256']
        assert saved_controls['source_guard'] == manifest['graph_sources'][wg]
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
    assert manifest['global_admitted_union_n'] == target_n and manifest['global_unresolved_n'] == pending_n
    assert manifest['model_predictions_n'] == manifest['expert_validation_n'] == 0
    return {'status': 'PASS', 'check_scope': 'AUTHORIZED_INCREMENTAL17_ORIGINAL_NATIVE_SQL_SCORER', 'additional_admitted_n': 1,
        'global_admitted_union_n': target_n, 'global_unresolved_n': pending_n, 'native_rows': native_n,
        'actual_scorer_controls': control_n, 'strict_boolean_controls_n': len(boolean_controls),
        'recorded_baseline_source_recount': source_recount, 'model_predictions_n': 0, 'expert_validation_n': 0,
        'preserved_noncohort_dispositions_n': len(baseline) - len(tasks),
        'preserved_noncohort_nonpass_status_counts': dict(Counter(row['status'] for ident, row in baseline.items() if ident not in tasks and row['status'] != 'pass')),
        'database_queries_n': 0, 'API_calls_n': 0,
        'bundle_manifest_sha256': sha(bundle / 'manifest.json')}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle', type=Path, default=BASE)
    p.add_argument('--parent', type=Path, default=None)
    args = p.parse_args()
    print(json.dumps(verify(args.bundle, args.parent)))
