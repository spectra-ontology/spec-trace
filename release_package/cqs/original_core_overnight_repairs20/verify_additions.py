#!/usr/bin/env python3
"""Offline portable check of immutable additional1; makes no API calls."""
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



def replay_summary_multiset_controls(task, records, saved):
    """Recompute five multiplicity/order controls using included scorer bytes."""
    counts=Counter(r['summary'] for r in records)
    assert len(records)==10 and sorted(counts.values())==[1,1,1,1,1,2,3]
    assert saved['id']==task['id'] and saved['repair_sha256']==task['repair_sha256']
    assert saved['status']=='PASS_ACTUAL_MULTIPLICITY_AND_UNORDERED_SUMMARY_CONTROLS'
    assert saved['source_summary_occurrences']==10 and saved['distinct_summary_values']==7
    unique=[{'summary':s} for s in counts]
    replaced=[dict(r) for r in records]
    duplicate=next(s for s,c in counts.items() if c==3)
    other=next(s for s,c in counts.items() if c==1)
    replaced[next(n for n,r in enumerate(replaced) if r['summary']==duplicate)]={'summary':other}
    cases=[('permutation_preserves_requested_multiset',list(reversed(records)),True),
      ('deduplicating_equal_summaries_loses_CR_occurrences',unique,False),
      ('same_length_and_same_unique_summaries_wrong_multiplicity',replaced,False),
      ('missing_one_duplicate_occurrence',records[:6]+records[7:],False),
      ('extra_duplicate_occurrence',records+[records[6]],False)]
    actual=[]
    for name,pred,exact in cases:
        score=original_scorer.score(task,records,pred,diagnostic=True)
        assert score['exact'] is exact,(name,score)
        actual.append({'control':name,'expected_exact':exact,'pass':True,'actual_score':score})
    assert actual==saved['actual_controls']
    return len(actual)


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
    assert sha(bundle/'baseline/index_manifest.json')=='e8dde572c2d662e9ff52e705ad74435261ead4e2cc8a233ca9988721248ffe6b'
    index=read(bundle/'baseline/index_manifest.json')
    assert set(index['source_factuality_quarantines']['ids'])=={'RAN1_P2_CQ1-1','RAN3_P4_CQ2-3','RAN4_P1_CQ6-3','RAN5_P1_CQ6-3'}
    assert set(index['source_factuality_resolutions'])=={'RAN5_P1_CQ6-3'}
    tr=[r for r in lines(bundle/'baseline/partition/classification_overlay560.jsonl') if r['id'] in {'RAN1_P5_CQ5-1','RAN1_P5_CQ5-2','RAN4_P5_CQ4-3'}]
    assert len(tr)==3 and all(r['classification']=='clarification_required' and r['diagnostic_subtype']=='conflicting_entity_description' for r in tr)
    assert scope['baseline_public_commit_observed']=='c4529319154e1685c0db26c444a02f559b9036ba'
    assert scope['authorized_original_frozen_repair_n']==1
    cases = unique(scope['cases'])
    assert set(cases)=={'RAN3_P4_CQ4-5'} and cases['RAN3_P4_CQ4-5']['repair_sha256']=='403ffd325d157916c9ef13d4df6523bf30868b0ce4d5f1e1a3ca30cfb323eb63'
    tasks, gold, controls = [unique(lines(bundle / n)) for n in ('tasks.jsonl', 'reference_gold.jsonl', 'scorer_checks.jsonl')]
    assert set(tasks) == set(gold) == set(controls) == set(cases) and len(tasks) == 1
    assert set(manifest['cohort_ids']) == set(tasks)
    originals = unique(lines(bundle / 'provenance/original_benchmark.jsonl'))
    baseline = unique(lines(bundle / 'baseline/all_core_dispositions.jsonl'))
    ledger = unique(lines(bundle / 'all_core_dispositions.jsonl'))
    assert len(originals) == 624 and len(baseline) == len(ledger) == 560
    assert set(baseline) <= set(originals)
    assert sum(r['status'] == 'pass' for r in baseline.values()) == 480
    assert not set(tasks) & {i for i, r in baseline.items() if r['status'] == 'pass'}
    for ident in set(baseline) - set(tasks):
        assert baseline[ident] == ledger[ident]
    assert sum(r['status'] == 'pass' for r in ledger.values()) == 481
    criteria = read(bundle / 'criteria.json')
    criteria_sha = sha(bundle / 'criteria.json')
    native_n, control_n = 0, 0
    for ident, task in tasks.items():
        assert task['required_fields']==[{'name':'summary','type':'string','nullable':False,'source_column_or_expression':'c.summaryOfChange'}]
        assert task['collection']=={'kind':'multiset'} and task['cardinality_policy']=={'mode':'exact','value':10}
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
        assert Counter(scorer.record_token(r,task['required_fields']) for r in native) == Counter(scorer.record_token(r,task['required_fields']) for r in independent)
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
        extra_pin=task['portable_gate_evidence']['actual_summary_multiset_controls']
        assert replay_summary_multiset_controls(task,projected,read(bundle/extra_pin['file']))==5
        native_n += len(native)
        control_n += len(actual)
    assert native_n == manifest['native_rows'] and control_n == manifest['actual_scorer_controls']
    assert manifest['global_admitted_union_n'] == 481 and manifest['global_unresolved_n'] == 79
    import subprocess
    for item in read(bundle/'source_population_replay.json'):
        result=subprocess.run([sys.executable,'-I',str(bundle/item['directory']/item['verifier'])],capture_output=True,text=True)
        assert result.returncode==0,result.stderr
        assert json.loads(result.stdout)==item['included_evidence_replay']
        expected=gold[item['id']]['records']
        task=tasks[item['id']]
        source=bundle/item['directory']
        assert sha(source/'manifest.json')==item['manifest_sha256']
        assert sha(source/item['verifier'])==item['verifier_sha256']
        source_manifest=read(source/'manifest.json')
        assert source_manifest['scope_and_provenance']['repair_sha256']==task['repair_sha256']
        selected=source_manifest['source_selected_records']
        assert selected==item['source_selected_records'] and selected['path']=='source_selected_records.jsonl' and selected['records']==10
        assert sha(source/selected['path'])==selected['sha256'] and (source/selected['path']).stat().st_size==selected['bytes']
        witnessed=lines(source/selected['path'])
        assert len(witnessed)==10 and all(set(r)=={'summary'} and type(r['summary']) is str for r in witnessed)
        assert Counter(scorer.record_token(r,task['required_fields']) for r in witnessed)==Counter(scorer.record_token(r,task['required_fields']) for r in expected)
    assert manifest['actual_additional_summary_multiset_controls']==5
    assert manifest['model_predictions_n'] == manifest['expert_validation_n'] == 0
    return {'status': 'PASS', 'check_scope': 'AUTHORIZED_INCREMENTAL20_ORIGINAL_NATIVE_SQL_SCORER', 'additional_admitted_n': 1,
        'global_admitted_union_n': 481, 'global_unresolved_n': 79, 'native_rows': native_n,
        'actual_scorer_controls': control_n, 'actual_additional_summary_multiset_controls':5, 'model_predictions_n': 0, 'expert_validation_n': 0,
        'bundle_manifest_sha256': sha(bundle / 'manifest.json')}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle', type=Path, default=BASE)
    p.add_argument('--parent', type=Path, default=None)
    args = p.parse_args()
    print(json.dumps(verify(args.bundle, args.parent)))
