#!/usr/bin/env python3
"""Offline portable check of immutable additional1; makes no API calls."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
# Strict immutable package boundary, before importing any package code.
EXPECTED_METADATA_SHA256='4a0c3e70dbf1ffb33ef760c6e8947a334891a75e10aba0a92a0b83b4af4f6324'
EXPECTED_PAYLOAD_MAP_SHA256='06dd0c81ab91b5ee0e0a541071b1662ae230a36495d07a7cdedf4274ec0a38f6'
def _no_link(path):
    import os
    p=Path(os.path.abspath(path))
    for q in [*reversed(p.parents),p]:
        if q.is_symlink():
            raise ValueError('symlink refused before target content read: '+str(q))
    return p

def _canonical_metadata(v):
    return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))

def _secure_bundle(path):
    root=_no_link(path)
    mp=_no_link(root/'manifest.json')
    obj=json.loads(mp.read_text())
    assert type(obj) is dict and type(obj.get('files')) is dict
    meta={k:v for k,v in obj.items() if k!='files'}
    assert hashlib.sha256(_canonical_metadata(meta).encode()).hexdigest()==EXPECTED_METADATA_SHA256,'immutable manifest metadata or JSON scalar type changed'
    pins=obj['files'];payload={k:v for k,v in pins.items() if k!='verify_additions.py'}
    assert hashlib.sha256(_canonical_metadata(payload).encode()).hexdigest()==EXPECTED_PAYLOAD_MAP_SHA256,'immutable scientific payload map changed'
    assert 'verify_additions.py' in pins
    names=set(pins)
    for rel,pin in pins.items():
        assert type(rel) is str and type(pin) is str
        q=Path(rel);assert not q.is_absolute() and '..' not in q.parts
    actual=set()
    # Refuse every tree link, including dangling links and directory links,
    # before opening any scientific payload or imported helper target.
    for p in root.rglob('*'):
        _no_link(p)
        if p.is_file() and p!=mp:actual.add(p.relative_to(root).as_posix())
    assert actual==names,'closed package file inventory changed'
    for rel,pin in pins.items():
        raw=_no_link(root/rel).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==pin,'file pin differs: '+rel
    return root

BASE=_no_link(Path(__file__).absolute()).parent
_secure_bundle(BASE)

sys.path.insert(0, str(BASE))
import scorer
import original_scorer
import review_schema
import contract_checks

KEYS = ['id', 'question_en', 'original_query', 'reference_query', 'required_fields',
        'collection', 'cardinality_policy', 'repair_class', 'original_question_preserved']


def sha(p):
    return hashlib.sha256(_no_link(p).read_bytes()).hexdigest()


def read(p):
    return json.loads(_no_link(p).read_text())


def lines(p):
    return [scorer.get_kernel().loads_exact(s) for s in _no_link(p).read_text().splitlines() if s.strip()]


def canonical(v):
    return scorer.get_kernel().json_exact(v)


def digest(v):
    return hashlib.sha256(canonical(v).encode()).hexdigest()


def unique(rows):
    result = {r['id']: r for r in rows}
    assert len(result) == len(rows)
    return result



def check_full_source_replay(saved):
    assert saved['status']=='PASS_ACTUAL_RELOCATION_ORIGINAL_REPLAY_AND_FOURTEEN_NEGATIVE_CONTROLS'
    assert saved['manifest_sha256']=='0eaf619daac55992a0db1ceea3b17b25a0469e1f8c1ba6c5e6d5f0289158120d'
    checks=saved['checks']; assert len(checks)==16 and all(c['pass'] for c in checks)
    original=next(c for c in checks if c['check']=='explicit_original62_workbooks61_DOCX_source_root')
    proof=json.loads(original['stdout'])
    assert original['exit_code']==0 and proof['status']=='PASS' and proof['id']=='RAN1_P3_CQ045'
    assert proof['source_candidate_CR_rows']==482 and proof['source_target_TSs']==4
    assert proof['report_literal_streams']==61 and proof['outside_occurrence_blocks']==8
    assert proof['own_normative_TS_witnesses']==proof['source_selected_records']==3
    assert proof['whole_38212_final_CR_table_exact'] is False
    assert proof['optional_original_replay']['all62_original_workbooks_rehashed'] is True
    assert proof['optional_original_replay']['all61_original_DOCX_rehashed_and_literal_streams_reextracted'] is True
    assert proof['original560_pass_increment']==proof['human_expert_n']==proof['native_calls']==proof['API_calls']==0


def project_requested(task, rows):
    records=[]
    for row in rows:
        record={}
        for field in task['required_fields']:
            key=field['name'] if field['name'] in row else field['source_column_or_expression']
            record[field['name']]=row[key]
        records.append(record)
    scorer.project(records,task['required_fields'],gold=True)
    return records


def replay_identity_set_controls(task, records, saved):
    """Replay the actual seven generic and nine bounded identity-set controls."""
    assert task['collection']=={'kind':'set'} and task['cardinality_policy']=={'mode':'all'}
    assert len(records)==3 and {r['spec'] for r in records}=={'38.212','38.213','38.214'}
    assert saved['id']==task['id'] and saved['repair_sha256']==task['repair_sha256']
    assert saved['status']=='PASS_ACTUAL_ROOT_ORIGINAL_FULL3_NATIVE_SQL_AND16_CONTROLS'
    assert saved['all_three_authored_columns_typed_equal'] is True and saved['native_rows']==3
    predictions=original_scorer.reference_prediction(task,records)
    cases=[
      ('permuted_complete_identity_set',list(reversed(predictions)),True),
      ('missing_one_TS',predictions[:-1],False),
      ('duplicate_displaces_distinct_TS',predictions[:-1]+predictions[:1],False),
      ('extra_outside_target_38_211',predictions+[{'spec':'38.211'}],False),
      ('wrong_required_TS_identity',[{'spec':'38.211'},*predictions[1:]],False),
      ('null_required_identity',[{'spec':None},*predictions[1:]],False),
      ('numeric_required_identity',[{'spec':38214},*predictions[1:]],False),
      ('incidental_count_values_ignored',[dict(x,resolutionCount=-999,crCount=-999) for x in predictions],True),
      ('incidental_counts_do_not_replace_identity',[{'resolutionCount':48,'crCount':99}],False)]
    actual=contract_checks.checks(task,records)
    assert len(actual)==7 and all(c['pass'] for c in actual)
    for name,prediction,expected in cases:
        outcome=original_scorer.score(task,records,prediction,diagnostic=True)
        actual.append({'check':name,'pass':outcome['exact'] is expected})
    assert len(actual)==16 and all(c['pass'] for c in actual) and actual==saved['actual_scorer_checks']
    return 9


def verify(bundle, parent=None):
    bundle = _secure_bundle(bundle)
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
    assert sha(bundle/'baseline/index_manifest.json')=='2f8006cb09b650b294a06d196a20efcf39031eab4722e4e5759ab045466d932e'
    index=read(bundle/'baseline/index_manifest.json')
    assert set(index['source_factuality_quarantines']['ids'])=={'RAN1_P2_CQ1-1','RAN3_P4_CQ2-3','RAN4_P1_CQ6-3','RAN5_P1_CQ6-3'}
    assert set(index['source_factuality_resolutions'])=={'RAN5_P1_CQ6-3'}
    tr=[r for r in lines(bundle/'baseline/partition/classification_overlay560.jsonl') if r['id'] in {'RAN1_P5_CQ5-1','RAN1_P5_CQ5-2','RAN4_P5_CQ4-3'}]
    assert len(tr)==3 and all(r['classification']=='clarification_required' and r['diagnostic_subtype']=='conflicting_entity_description' for r in tr)
    assert scope['baseline_public_commit_observed']=='f4d747ce97d1424755d10795ec1cacec04323d72'
    assert scope['authorized_original_frozen_repair_n']==1
    cases = unique(scope['cases'])
    assert set(cases)=={'RAN1_P3_CQ045'} and cases['RAN1_P3_CQ045']['repair_sha256']=='3950eb7946e0b3ad47afed70818088159fea41320df0e91c8f0de8e28b426e80'
    tasks, gold, controls = [unique(lines(bundle / n)) for n in ('tasks.jsonl', 'reference_gold.jsonl', 'scorer_checks.jsonl')]
    assert set(tasks) == set(gold) == set(controls) == set(cases) and len(tasks) == 1
    assert set(manifest['cohort_ids']) == set(tasks)
    originals = unique(lines(bundle / 'provenance/original_benchmark.jsonl'))
    baseline = unique(lines(bundle / 'baseline/all_core_dispositions.jsonl'))
    ledger = unique(lines(bundle / 'all_core_dispositions.jsonl'))
    assert len(originals) == 624 and len(baseline) == len(ledger) == 560
    assert set(baseline) <= set(originals)
    assert sum(r['status'] == 'pass' for r in baseline.values()) == 483
    assert not set(tasks) & {i for i, r in baseline.items() if r['status'] == 'pass'}
    for ident in set(baseline) - set(tasks):
        assert baseline[ident] == ledger[ident]
    assert sum(r['status'] == 'pass' for r in ledger.values()) == 484
    criteria = read(bundle / 'criteria.json')
    criteria_sha = sha(bundle / 'criteria.json')
    native_n, control_n = 0, 0
    for ident, task in tasks.items():
        assert task['original_query']==task['reference_query'] and task['repair_class']=='scorer_only'
        assert task['required_fields']==[{'name':'spec','type':'string','nullable':False,'source_column_or_expression':'sp.specNumber'}]
        assert task['collection']=={'kind':'set'} and task['cardinality_policy']=={'mode':'all'}
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
            assert review['exposure']['nonblind_AI'] is True and review['exposure']['human_expert_n']==0
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
        full_SQL_pin=sql['portable_all_return_columns']
        assert sha(bundle/full_SQL_pin['file'])==full_SQL_pin['sha256']==sql['independent_SQL_all_return_columns_sha256']
        assert canonical(lines(bundle/full_SQL_pin['file']))==canonical(positional)
        assert sql['compared_native_columns']==receipt['columns']==['spec','resolutionCount','crCount']
        assert sql['cap_meaning']
        assert sql['all_return_fields_compared'] is True and sql['uncapped_SQL'] is True
        assert sql['native_receipt_sha256'] == evidence['receipt_sha256']
        assert sql['native_rows_sha256'] == evidence['rows_sha256']
        assert Counter(scorer.record_token(r,task['required_fields']) for r in project_requested(task,native)) == Counter(scorer.record_token(r,task['required_fields']) for r in independent)
        assert all(set(r)=={'spec'} for r in independent)
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
        full_pin=task['portable_gate_evidence']['actual_full_source_portable_and_originals']
        check_full_source_replay(read(bundle/full_pin['file']))
        extra_pin=task['portable_gate_evidence']['actual_CQ045_TS_identity_set_controls']
        assert replay_identity_set_controls(task,projected,read(bundle/extra_pin['file']))==9
        native_n += len(native)
        control_n += len(actual)
    assert native_n == manifest['native_rows'] == 3 and control_n == manifest['actual_scorer_controls'] == 7
    assert manifest['global_admitted_union_n'] == 484 and manifest['global_unresolved_n'] == 76
    assert manifest['global_clarification_required_n']==14 and manifest['global_evidence_pending_n']==62
    assert read(bundle/'baseline/partition/summary.json')['partition_counts']=={'contract_verified':483,'clarification_required':14,'evidence_pending':63}
    import subprocess
    for item in read(bundle/'source_population_replay.json'):
        result=subprocess.run([sys.executable,'-B','-I',str(bundle/item['directory']/item['verifier'])],capture_output=True,text=True)
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
        assert selected==item['source_selected_records'] and selected['path']=='source_selected_records.jsonl' and selected['records']==3
        assert sha(source/selected['path'])==selected['sha256'] and (source/selected['path']).stat().st_size==selected['bytes']
        witnessed=lines(source/selected['path'])
        assert len(witnessed)==3 and all(set(r)=={'spec'} and type(r['spec']) is str for r in witnessed)
        assert Counter(scorer.record_token(r,task['required_fields']) for r in witnessed)==Counter(scorer.record_token(r,task['required_fields']) for r in expected)
    assert manifest['actual_additional_TS_identity_set_controls']==9
    assert manifest['model_predictions_n'] == manifest['expert_validation_n'] == 0
    return {'status': 'PASS', 'check_scope': 'AUTHORIZED_INCREMENTAL23_ORIGINAL_NATIVE_SQL_SCORER', 'additional_admitted_n': 1,
        'global_admitted_union_n': 484, 'global_unresolved_n': 76, 'native_rows': native_n,
        'actual_scorer_controls': control_n, 'actual_additional_TS_identity_set_controls':9, 'model_predictions_n': 0, 'expert_validation_n': 0,
        'bundle_manifest_sha256': sha(bundle / 'manifest.json')}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle', type=Path, default=BASE)
    p.add_argument('--parent', type=Path, default=None)
    args = p.parse_args()
    print(json.dumps(verify(args.bundle, args.parent)))
