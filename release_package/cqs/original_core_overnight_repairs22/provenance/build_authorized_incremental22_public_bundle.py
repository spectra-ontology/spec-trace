#!/usr/bin/env python3
"""Materialize the prospective immutable authorized 22, with preserved baseline evidence.

No model call, native execution, publication, or historical score is made here.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
B = next(p for p in OUT.parents if p.name=='overnight_reaudit')
AUTH = B / 'authorized_incremental22_OpenRouter_release'
PUBLIC = Path('/home/sihyeon/workspace/spectra-public/spec-trace')
WORKTREE = AUTH/'baseline_source'
PARENT = PUBLIC / 'release_package/cqs/original_core_repair'
DEST = AUTH/'public_bundle'
INPUT_INDEX = None
README_TEXT = '# Additional original-question repair: named RAN1#121 Conclusions\n\nThis one-question cohort extends the pinned 482-question release to 483 of 560; 77 remain nonadmitted (14 clarification-required and 63 evidence-pending). Original English and authored query are unchanged. The named historical meeting RAN1#121 is fixed. The original query selects fifteen Conclusion identities by sequence and resolutionId. The requested answer is their resolutionId set; output serialization order is unscored. The extra content column is compared in full typed native/SQL agreement but is not a required answer field.\n\nTwo nonblind seven-unit AI judgments, all 64 source candidates and frozen query operands, their 63 active source records, the unchanged first fifteen identities, read-only rollback native evidence, exact two-column independent SQL agreement, seven generic scorer controls and four identity-set controls are retained. Source label deletion/counterevidence and the first native prequery transport failure are preserved. The source candidate and active populations select the same original fifteen; this does not make the retained inactive item an active Conclusion. This is not a present-day latest-meeting or unresolved-status assertion, authentic optional-content rendering, or human/expert validation.\n\nsource_population is answer-bearing verification evidence and is not extra model or retrieval input. The portable command replays included data. Original ZIP/member and whole frozen SQLite replays are separately recorded; they are not silently rerun by the portable command. Historical quarantines, their single explicit RAN5 resolution, three conflicting-TR diagnostics and prior cohorts remain in the pinned baseline. This builder makes no model calls and does not publish.\n\nRun python3 -B -S verify_additions.py --bundle . for the offline check.\n'
KEYS = ['id', 'question_en', 'original_query', 'reference_query', 'required_fields',
        'collection', 'cardinality_policy', 'repair_class', 'original_question_preserved']
sys.path.insert(0, str(PARENT))
import scorer
import original_scorer
import review_schema
import contract_checks


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def canonical(v):
    return scorer.get_kernel().json_exact(v)


def digest(v):
    return hashlib.sha256(canonical(v).encode()).hexdigest()


def read(p):
    return json.loads(Path(p).read_text())


def lines(p):
    return [scorer.get_kernel().loads_exact(s) for s in Path(p).read_text().splitlines() if s.strip()]


def write_json(p, v):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n')


def write_lines(p, v):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(''.join(canonical(r) + '\n' for r in v))


def copy(source, relative, expected=None):
    source = Path(source)
    actual = sha(source)
    assert expected is None or actual == expected, (source, 'pin changed')
    target = DEST / relative
    assert target.resolve().is_relative_to(DEST.resolve())
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert sha(target) == actual
    else:
        shutil.copyfile(source, target)
    return {'file': str(relative), 'sha256': actual, 'bytes': source.stat().st_size}



EXPECTED_ID = 'RAN1_P2_CQ1-3'
EXPECTED_REPAIR = '02b71d66fce022602c3d30b9084aee57b12bc5495a45057b3db45bd7040277ba'
EXPECTED_BASELINE_INDEX = '556c58bea84a123435cf538a7722caa598c3f38b9fa2531269e6df05c85f3ca6'
EXPECTED_PARENT_COMMIT = 'ea149bb543b8acb90e800ff29a68a02006ae8fe7'
TR_IDS = {'RAN1_P5_CQ5-1','RAN1_P5_CQ5-2','RAN4_P5_CQ4-3'}
QUARANTINE_IDS = {'RAN1_P2_CQ1-1','RAN3_P4_CQ2-3','RAN4_P1_CQ6-3','RAN5_P1_CQ6-3'}


def check_Conclusion_identity_contract(task):
    assert task['id']==EXPECTED_ID and task['repair_sha256']==EXPECTED_REPAIR
    assert task['original_query']==task['reference_query'] and task['repair_class']=='scorer_only'
    assert digest({k:task[k] for k in KEYS})==EXPECTED_REPAIR
    assert task['required_fields']==[{'name':'resolutionId','type':'string','nullable':False,'source_column_or_expression':'c.resolutionId'}]
    assert task['collection']=={'kind':'set'} and task['cardinality_policy']=={'mode':'exact','value':15}


def preflight():
    """Read-only readiness check: no destination, native run, API or registry write."""
    import subprocess
    index_path=PUBLIC/'release_package/cqs/current_core/index_manifest.json'
    assert sha(index_path)==EXPECTED_BASELINE_INDEX, 'baseline index changed; independently review and version the preparer'
    index=read(index_path)
    assert set(index['source_factuality_quarantines']['ids'])==QUARANTINE_IDS
    assert set(index['source_factuality_resolutions'])=={'RAN5_P1_CQ6-3'}
    partition=PUBLIC/'release_package/cqs/core_disposition_audit/partition'
    overlay=lines(partition/'classification_overlay560.jsonl')
    tr=[r for r in overlay if r['id'] in TR_IDS]
    assert len(tr)==3 and all(r['classification']=='clarification_required' and r['diagnostic_subtype']=='conflicting_entity_description' for r in tr)
    scope=read(AUTH/'scope.json')
    assert scope['baseline_public_commit_observed']==EXPECTED_PARENT_COMMIT
    assert scope['authorized_original_frozen_repair_n']==1
    cases={r['id']:r for r in scope['cases']}
    assert set(cases)=={EXPECTED_ID}
    inputs=read(AUTH/'admission_inputs.json')
    assert len(inputs)==1
    entry=inputs[0]; case=cases[EXPECTED_ID]
    task=read(B/entry['definition']);check_Conclusion_identity_contract(task)
    assert sha(B/entry['definition'])==case['definition']['sha256']
    assert case['repair_sha256']==EXPECTED_REPAIR
    criteria=read(PARENT/'criteria.json')
    reviews=[read(B/entry[role]) for role in ('primary','secondary')]
    for review in reviews:
        review_schema.check_pass(review,task['question_en'],criteria['semantic_units'],criteria_sha=sha(PARENT/'criteria.json'),identity_key='repair_sha256',identity_sha=EXPECTED_REPAIR)
        assert review['human_author_review_completed'] is False and review['expert_validation_n']==0
    assert reviews[0]['reviewer_kind']!=reviews[1]['reviewer_kind']
    for role,pin in case['gate_files'].items():
        if pin.get('embedded_in_definition'):assert digest(task[pin['embedded_in_definition']])==pin['sha256']
        else:assert sha(Path(pin['path']))==pin['sha256'],role
    assert 'exact_native_input' in case['gate_files']
    controls=read(B/entry['controls'])
    assert controls['id']==EXPECTED_ID and controls['repair_sha256']==EXPECTED_REPAIR
    assert controls['status']=='controls_pass' and controls['controls'] and all(c['pass'] for c in controls['controls'])
    receipts=[Path(p) for p in controls['pins'] if '/reference_outputs/' in p and p.endswith('.json')]
    assert len(receipts)==1
    rp=receipts[0];receipt=read(rp);rows=rp.with_suffix('.jsonl')
    assert sha(rp)==controls['pins'][str(rp)] and sha(rows)==controls['pins'][str(rows)]==receipt['rows_sha256']
    assert receipt['status']=='OK' and receipt['full_rows_available'] is True and receipt['truncated'] is False
    assert receipt['rollback_completed'] is True and receipt['execution_summary_complete'] is True
    assert receipt['plan_query_type']==receipt['execution_query_type']=='r'
    assert receipt['query']==task['reference_query'] and receipt['columns']==['c.resolutionId','c.content']
    assert len(lines(rows))==receipt['rows_retained']==controls['native_reference_population_n']==15
    sql=read(AUTH/'gate_inputs/full_independent_sql_scope_bridge.json')
    assert {c['id'] for c in sql['cases']}=={EXPECTED_ID}
    sqlcase=sql['cases'][0]
    assert sqlcase['all_return_fields_compared'] is True and sqlcase['uncapped_SQL'] is True
    full_SQL=lines(B/sqlcase['independent_SQL_all_return_columns'])
    assert sha(B/sqlcase['independent_SQL_all_return_columns'])==sqlcase['independent_SQL_all_return_columns_sha256']
    assert canonical(full_SQL)==canonical(lines(rows))
    assert sqlcase['compared_native_columns']==receipt['columns'] and sqlcase['cap_meaning']
    assert sqlcase['native_receipt_sha256']==sha(rp) and sqlcase['native_rows_sha256']==sha(rows)
    assert sha(B/sqlcase['independent_records'])==sqlcase['independent_records_sha256']
    assert receipt['query_sha256']==hashlib.sha256(task['reference_query'].encode()).hexdigest()
    native=[dict(zip(receipt['columns'],r)) for r in lines(rows)]
    independent=lines(B/sqlcase['independent_records'])
    assert all(set(r)=={'resolutionId'} for r in independent)
    assert Counter(scorer.record_token(r,task['required_fields']) for r in project_requested(task,native))==Counter(scorer.record_token(r,task['required_fields']) for r in independent)
    assert contract_checks.checks(task,project_requested(task,native),None)==controls['controls'] and len(controls['controls'])==7
    native_base=rp.parents[2];run=read(native_base/'execution_RAN1.json')
    guard=read(PARENT/'manifest.json')['graph_sources']['RAN1']
    assert run['inventory_unchanged'] is True and run['model_calls']==0 and run['expert_validation'] is False
    assert controls['source_guard']==run['source_before']==run['source_after']==guard
    run_item=next(r for r in run['items'] if r['id']==EXPECTED_ID)
    assert run_item['status']=='OK' and run_item['query_sha256']==receipt['query_sha256'] and run_item['rows']==15
    native_input=native_base/'execution_inputs/RAN1.jsonl'
    if not native_input.is_file():native_input=Path(case['gate_files']['exact_native_input']['path'])
    assert sha(native_input)==run['input_sha256'] and sha(native_base/'execution_protocol.json')==run['protocol_sha256']
    assert next(r for r in lines(native_input) if r['id']==EXPECTED_ID)['candidate_query']==task['reference_query']
    admissions={r['id']:r for r in read(AUTH/'current_local_admissions.json')['admitted']}
    assert EXPECTED_ID in admissions and admissions[EXPECTED_ID]['source_witness_pins']
    for pin in admissions[EXPECTED_ID]['source_witness_pins']:assert sha(Path(pin['path']))==pin['sha256']
    extra_pin=case['gate_files']['actual_Conclusion_identity_set_controls']
    replay_identity_set_controls(task,project_requested(task,native),read(Path(extra_pin['path'])))
    full_pin=case['gate_files']['actual_full_source_portable_and_archives']
    check_full_source_replay(read(Path(full_pin['path'])))
    packs=read(OUT/'source_packs.json')
    assert len(packs)==1 and packs[0]['id']==EXPECTED_ID
    item=packs[0];source=Path(item['path'])
    assert len(item['manifest_sha256'])==64 and len(item['verifier_sha256'])==64, 'final sourcepack pins required'
    assert sha(source/'manifest.json')==item['manifest_sha256'] and sha(source/item['verifier'])==item['verifier_sha256']
    manifest=read(source/'manifest.json')
    assert manifest['scope_and_provenance']['repair_sha256']==EXPECTED_REPAIR
    selected=manifest['source_selected_records'];selected_path=source/selected['path']
    assert selected['path']=='source_selected_records.jsonl' and selected['records']==15
    assert sha(selected_path)==selected['sha256'] and selected_path.stat().st_size==selected['bytes']
    witnessed=lines(selected_path)
    assert Counter(scorer.record_token(r,task['required_fields']) for r in witnessed)==Counter(scorer.record_token(r,task['required_fields']) for r in project_requested(task,native))
    assert len(witnessed)==15 and all(set(r)=={'resolutionId'} and type(r['resolutionId']) is str for r in witnessed)
    result=subprocess.run([sys.executable,'-B','-I',str(source/item['verifier'])],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    proof=json.loads(result.stdout)
    assert proof['status']=='PASS',proof
    return {'status':'PREFLIGHT_PASS_NO_BUNDLE_CREATED','id':EXPECTED_ID,'repair_sha256':EXPECTED_REPAIR,'source_manifest_sha256':item['manifest_sha256'],'native_rows':15,'actual_model_calls':0,'actual_native_executions':0}



def check_full_source_replay(saved):
    assert saved['exit_code']==0
    proof=json.loads(saved['stdout'])
    assert proof['status']=='PASS' and proof['id']=='RAN1_P2_CQ1-3'
    assert proof['raw_candidates']==proof['source_records']==64
    assert proof['source_active']==63 and proof['selected_records']==15
    original=proof['optional_original_replay']
    assert original['original_archive_and_member_reopened'] is True
    assert original['frozen_SQLite_rehashed_and_all64_rows_recounted'] is True
    assert all(c['outcome']=='REJECTED' for c in proof['negative_controls'])


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
    """Recompute the actual four additional identity-set and order checks."""
    assert task['collection']=={'kind':'set'} and task['cardinality_policy']=={'mode':'exact','value':15}
    assert len(records)==15 and len({r['resolutionId'] for r in records})==15
    assert saved['id']==task['id'] and saved['repair_sha256']==task['repair_sha256']
    assert saved['status']=='PASS_ACTUAL_SOURCE_SQL_NATIVE_AND_CONTROLS'
    assert saved['native_SQL_all2_columns_exact_typed_agreement'] is True
    assert saved['native_rows']==saved['unique_selected_IDs']==15
    predictions=original_scorer.reference_prediction(task,records)
    cases=[('answer_order_permutation',list(reversed(predictions)),True),
           ('missing_one_distinct_ID',predictions[:-1],False),
           ('duplicate_replaces_distinct_ID',predictions[:-1]+predictions[:1],False),
           ('extra_distinct_ID',predictions+[{'resolutionId':'__EXTRA_CONCLUSION__'}],False)]
    actual=contract_checks.checks(task,records)
    assert len(actual)==7 and all(c['pass'] for c in actual)
    for name,prediction,expected in cases:
        result=original_scorer.score(task,records,prediction,diagnostic=True)
        actual.append({'check':name,'pass':result['exact'] is expected})
    assert len(actual)==11 and all(c['pass'] for c in actual)
    assert actual==saved['actual_scorer_checks']
    return 4


def main():
    assert not DEST.exists(), 'preserve existing bundle; choose a new version for changes'
    scope = read(AUTH / 'scope.json')
    assert scope['authorized_original_frozen_repair_n'] == 1
    inputs = read(AUTH / 'admission_inputs.json')
    cases = {r['id']: r for r in scope['cases']}
    assert len(cases) == len(inputs) == 1
    admissions = {r['id']: r for r in read(AUTH / 'current_local_admissions.json')['admitted']}
    originals = {r['id']: r for r in lines(PARENT / 'provenance/original_benchmark.jsonl')}
    baseline = lines(PUBLIC / 'release_package/cqs/current_core/all_core_dispositions.jsonl')
    assert len(baseline) == 560 and sum(r['status'] == 'pass' for r in baseline) == 482
    baseline_partition=read(PUBLIC/'release_package/cqs/core_disposition_audit/partition/summary.json')
    assert baseline_partition['partition_counts']=={'contract_verified':482,'clarification_required':14,'evidence_pending':64}
    assert not set(cases) & {r['id'] for r in baseline if r['status'] == 'pass'}
    full_sql_path = AUTH/'gate_inputs/full_independent_sql_scope_bridge.json'
    full_sql = read(full_sql_path)
    sql_cases = {r['id']: r for r in full_sql['cases']}
    criteria = read(PARENT / 'criteria.json')
    criteria_sha = sha(PARENT / 'criteria.json')
    parent_manifest = read(PARENT / 'manifest.json')
    preflight()
    DEST.mkdir(parents=True)
    for name in ('criteria.json', 'original_scorer.py', 'scorer.py',
                 'typed_values.py', 'contract_checks.py', 'review_schema.py', 'source_pins.json'):
        copy(PARENT / name, name)
    baseline_index=read(PUBLIC/'release_package/cqs/current_core/index_manifest.json')
    runtime=PUBLIC/baseline_index['latest_scope']['bundle']
    runtime_manifest=read(runtime/'manifest.json')
    for name in ('score_predictions.py','rational_share_records.py','share_runtime_adapter.py'):
        copy(runtime/name,name,runtime_manifest['files'][name])
    for name in ('scope.json', 'admission_inputs.json', 'current_local_admissions.json',
                 'new_answerable_questions.json'):
        copy(AUTH / name, 'authorization/' + name)
    copy(PUBLIC / 'release_package/cqs/current_core/index_manifest.json', 'baseline/index_manifest.json')
    copy(PUBLIC / 'release_package/cqs/current_core/all_core_dispositions.jsonl', 'baseline/all_core_dispositions.jsonl')
    copy(PUBLIC / 'release_package/cqs/current_core/current_tasks.jsonl', 'baseline/current_tasks.jsonl')
    for name in ('summary.json', 'classification_overlay560.jsonl'):
        copy(PUBLIC/'release_package/cqs/core_disposition_audit/partition'/name, 'baseline/partition/'+name)
    copy(OUT/'source_packs.json', 'authorization/source_packs.json')
    copy(PARENT / 'provenance/original_benchmark.jsonl', 'provenance/original_benchmark.jsonl')
    copy(full_sql_path, 'provenance/root_full_SQL_recheck_at_build.json')
    copy(Path(__file__), 'provenance/build_authorized_incremental22_public_bundle.py')
    tasks, gold, checks, source_projection = [], [], [], []
    for entry in inputs:
        source_def = B / entry['definition']
        task = read(source_def)
        ident, wg = task['id'], task['id'].split('_')[0]
        pinned = cases[ident]
        assert sha(source_def) == pinned['definition']['sha256']
        definition = {k: task[k] for k in KEYS}
        repair_sha = digest(definition)
        assert repair_sha == task['repair_sha256'] == pinned['repair_sha256']
        assert task['question_en'] == originals[ident]['question_en']
        assert task['original_query'] == originals[ident]['cypher']
        primary = read(B / entry['primary']) if entry.get('primary') else task['primary_review']
        secondary = read(B / entry['secondary'])
        for judgment in (primary, secondary):
            review_schema.check_pass(judgment, task['question_en'], criteria['semantic_units'],
                criteria_sha=criteria_sha, identity_key='repair_sha256', identity_sha=repair_sha)
            assert judgment['human_author_review_completed'] is False and judgment['expert_validation_n'] == 0
        assert primary['reviewer_kind'] != secondary['reviewer_kind']
        portable_gates = {}
        for role, pin in pinned['gate_files'].items():
            if pin.get('embedded_in_definition'):
                value = task[pin['embedded_in_definition']]
                assert digest(value) == pin['sha256']
                relative = 'gate_evidence/' + ident + '/' + role + '.json'
                write_json(DEST / relative, value)
                portable_gates[role] = {'file': relative, 'sha256': sha(DEST / relative),
                    'embedded_in_definition': pin['embedded_in_definition'], 'embedded_digest': pin['sha256']}
                continue
            path = Path(pin['path'])
            portable_gates[role] = copy(path, 'gate_evidence/' + ident + '/' + role + path.suffix, pin['sha256'])
        copy(source_def, 'definitions/' + ident + '.json', pinned['definition']['sha256'])
        controls = read(B / entry['controls'])
        assert controls['id'] == ident and controls['repair_sha256'] == repair_sha
        assert controls['status'] == 'controls_pass' and all(c['pass'] for c in controls['controls'])
        receipts = [Path(p) for p in controls['pins'] if '/reference_outputs/' in p and p.endswith('.json')]
        assert len(receipts) == 1
        rp = receipts[0]
        receipt = read(rp)
        qsha = hashlib.sha256(task['reference_query'].encode()).hexdigest()
        assert receipt['query'] == task['reference_query'] and receipt['query_sha256'] == qsha
        assert receipt['status'] == 'OK' and receipt['full_rows_available'] is True
        assert receipt['truncated'] is False and receipt['rollback_completed'] is True
        assert receipt['execution_summary_complete'] is True
        assert receipt['plan_query_type'] == receipt['execution_query_type'] == 'r'
        rows_path = rp.with_suffix('.jsonl')
        assert sha(rows_path) == receipt['rows_sha256'] == controls['pins'][str(rows_path)]
        assert sha(rp) == controls['pins'][str(rp)]
        positional = lines(rows_path)
        assert all(type(r) is list and len(r) == len(receipt['columns']) for r in positional)
        native = [dict(zip(receipt['columns'], r)) for r in positional]
        assert len(native) == receipt['rows_retained'] == controls['native_reference_population_n']
        root = 'reference_outputs/' + ident + '/' + qsha
        rp_pin = copy(rp, root + '.json')
        rows_pin = copy(rows_path, root + '.jsonl')
        native_base = rp.parents[2]
        run_path = native_base / ('execution_' + wg + '.json')
        run = read(run_path)
        assert run['inventory_unchanged'] is True and run['model_calls'] == 0 and run['expert_validation'] is False
        expected_guard = parent_manifest['graph_sources'][wg]
        assert controls['source_guard'] == expected_guard
        assert run['source_before'] == run['source_after'] == expected_guard
        run_item = next(r for r in run['items'] if r['id'] == ident)
        assert run_item['status'] == 'OK' and run_item['query_sha256'] == qsha and run_item['rows'] == len(native)
        run_pin = copy(run_path, 'provenance/native_run_' + sha(run_path) + '.json')
        input_path = native_base / 'execution_inputs' / (wg + '.jsonl')
        if not input_path.is_file():
            input_path=Path(pinned['gate_files']['exact_native_input']['path'])
            assert sha(input_path)==run['input_sha256']
        chain = {}
        for name, path in [('execution_inputs', input_path),
                           ('execution_protocol', native_base / 'execution_protocol.json')]:
            chain[name] = copy(path, 'provenance/' + sha(path) + path.suffix)
        assert chain['execution_inputs']['sha256'] == run['input_sha256']
        assert chain['execution_protocol']['sha256'] == run['protocol_sha256']
        input_task = next(r for r in lines(input_path) if r['id'] == ident)
        assert input_task['candidate_query'] == task['reference_query']
        sql_case = sql_cases[ident]
        assert sql_case['all_return_fields_compared'] is True and sql_case['uncapped_SQL'] is True
        full_SQL_path=B/sql_case['independent_SQL_all_return_columns']
        assert sha(full_SQL_path)==sql_case['independent_SQL_all_return_columns_sha256']
        assert canonical(lines(full_SQL_path))==canonical(positional)
        assert sql_case['compared_native_columns']==receipt['columns'] and sql_case['cap_meaning']
        full_SQL_pin=copy(full_SQL_path,'independent_SQL/'+ident+'_all_return_columns.jsonl',sql_case['independent_SQL_all_return_columns_sha256'])
        assert sql_case['native_receipt_sha256'] == rp_pin['sha256']
        assert sql_case['native_rows_sha256'] == rows_pin['sha256']
        independent_path = B / sql_case['independent_records']
        sql_pin = copy(independent_path, 'independent_SQL/' + ident + '.jsonl', sql_case['independent_records_sha256'])
        independent = lines(independent_path)
        assert Counter(scorer.record_token(r,task['required_fields']) for r in independent) == Counter(scorer.record_token(r,task['required_fields']) for r in project_requested(task,native))
        assert all(set(r)=={'resolutionId'} for r in independent)
        sql_case = dict(sql_case, portable_independent_records=sql_pin,portable_all_return_columns=full_SQL_pin)
        sql_case_pin = None
        write_json(DEST / ('independent_SQL/' + ident + '_evidence.json'), sql_case)
        sql_case_pin = {'file': 'independent_SQL/' + ident + '_evidence.json',
                        'sha256': sha(DEST / ('independent_SQL/' + ident + '_evidence.json'))}
        fields = task['required_fields']
        records = []
        for row in native:
            record = {}
            for field in fields:
                key = field['name'] if field['name'] in row else field['source_column_or_expression']
                assert key in row, (ident, field, receipt['columns'])
                record[field['name']] = row[key]
            records.append(record)
        scorer.project(records, fields, gold=True)
        groups = original_scorer.make_order_groups(task, native, records) if task['collection']['kind'] in {
            'native_ordered_ties', 'top_k_boundary_ties'} else None
        extra_pin=pinned['gate_files']['actual_Conclusion_identity_set_controls']
        assert replay_identity_set_controls(task,records,read(Path(extra_pin['path'])))==4
        actual_checks = contract_checks.checks(task, records, groups)
        assert actual_checks == controls['controls'] and all(r['pass'] for r in actual_checks), ident
        source_pins = []
        for pin in admissions[ident]['source_witness_pins']:
            path = Path(pin['path'])
            rel = 'source_evidence/' + pin['sha256'] + path.suffix
            copied = copy(path, rel, pin['sha256'])
            source_pins.append(dict(copied, original_path=pin['path']))
        source_projection.append({'id': ident, 'source_witnesses': source_pins})
        completed = dict(definition, repair_sha256=repair_sha, criteria_sha256=criteria_sha,
            original_question_sha256=hashlib.sha256(task['question_en'].encode()).hexdigest(),
            original_query_sha256=hashlib.sha256(task['original_query'].encode()).hexdigest(),
            reference_query_sha256=qsha, primary_review=primary, secondary_review=secondary,
            validation_status='validated', admitted=True, native_execution_completed=True,
            scorer_controls_completed=True, human_author_review_completed=False, expert_validation_n=0,
            model_calls=0, model_call_scope='No predictions in repair bundle; authorized fresh evaluation is separate.',
            native_rows=len(records), projected_records_sha256=digest(records),
            portable_native_evidence={'receipt_file': rp_pin['file'], 'receipt_sha256': rp_pin['sha256'],
                'rows_file': rows_pin['file'], 'rows_sha256': rows_pin['sha256'],
                'run_report_file': run_pin['file'], 'run_report_sha256': run_pin['sha256'], 'chain': chain},
            portable_gate_evidence=portable_gates, portable_source_evidence=source_pins,
            portable_independent_SQL_evidence=sql_case_pin,
            limitations='Named historical RAN1#121 Conclusions, original first fifteen identities and unchanged authored query; two nonblind AI judgments. Source candidates64 and active63 have identical first15. Not present-day latest/open status or authentic optional-content rendering. Preserved initial prequery native transport failure and identical-query successful retry.')
        tasks.append(completed)
        gold.append({'id': ident, 'repair_sha256': repair_sha, 'records': records, 'order_groups': groups})
        checks.append({'id': ident, 'repair_sha256': repair_sha, 'checks': actual_checks, 'pass': True})
    assert {t['id'] for t in tasks} == set(cases)
    write_lines(DEST / 'tasks.jsonl', tasks)
    write_lines(DEST / 'reference_gold.jsonl', gold)
    write_lines(DEST / 'scorer_checks.jsonl', checks)
    write_json(DEST / 'source_public_projection.json', source_projection)
    ledger = {r['id']: r for r in baseline}
    for t in tasks:
        ledger[t['id']] = {'id': t['id'], 'status': 'pass', 'repair_class': t['repair_class'],
                          'repair_sha256': t['repair_sha256'], 'question_preserved': True}
    write_lines(DEST / 'all_core_dispositions.jsonl', sorted(ledger.values(), key=lambda r: r['id']))
    assert sum(r['status'] == 'pass' for r in ledger.values()) == 483
    source_packs=read(OUT/'source_packs.json')
    source_pack_proofs=[]
    import subprocess
    for item in source_packs:
        source=Path(item['path'])
        prefix='source_population/'+item['id']
        for f in sorted(source.rglob('*')):
            if f.is_file() and '__pycache__' not in f.parts and f.suffix != '.pyc':
                copy(f,prefix+'/'+str(f.relative_to(source)))
        proof=subprocess.run([sys.executable,'-B','-I',str(DEST/prefix/item['verifier'])],capture_output=True,text=True)
        assert proof.returncode==0,proof.stderr
        task=next(t for t in tasks if t['id']==item['id'])
        expected=next(g['records'] for g in gold if g['id']==item['id'])
        pack_manifest=read(DEST/prefix/'manifest.json')
        assert sha(DEST/prefix/'manifest.json')==item['manifest_sha256']
        assert sha(DEST/prefix/item['verifier'])==item['verifier_sha256']
        selected=pack_manifest['source_selected_records']
        assert selected['path']=='source_selected_records.jsonl' and selected['records']==15
        selected_path=DEST/prefix/selected['path']
        assert sha(selected_path)==selected['sha256'] and selected_path.stat().st_size==selected['bytes']
        witnessed=lines(selected_path)
        assert len(witnessed)==15 and all(set(r)=={'resolutionId'} and type(r['resolutionId']) is str for r in witnessed)
        assert Counter(scorer.record_token(r,task['required_fields']) for r in witnessed)==Counter(scorer.record_token(r,task['required_fields']) for r in expected)
        source_pack_proofs.append({'id':item['id'],'directory':prefix,'verifier':item['verifier'],
            'manifest_sha256':item['manifest_sha256'],'verifier_sha256':item['verifier_sha256'],
            'source_selected_records':selected,'included_evidence_replay':json.loads(proof.stdout)})
    write_json(DEST/'source_population_replay.json',source_pack_proofs)
    copy(OUT / 'verify_authorized_incremental22_public_bundle.py', 'verify_additions.py')
    (DEST/'README.md').write_text(README_TEXT)
    manifest = {'kind': 'Immutable authorized additional1 original-question repairs; model evaluation separate',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'parent_public_commit': scope['baseline_public_commit_observed'],
        'parent_bundle_manifest_sha256': sha(PARENT / 'manifest.json'),
        'baseline_public_pass_n': 482, 'admitted_n': 1, 'cohort_ids': [t['id'] for t in tasks],
        'global_admitted_union_n': 483, 'global_unresolved_n': 77,
        'global_clarification_required_n':14,'global_evidence_pending_n':63,
        'authorization_scope_sha256': sha(AUTH / 'scope.json'),
        'authorization_admission_inputs_sha256': sha(AUTH / 'admission_inputs.json'),
        'native_rows': sum(t['native_rows'] for t in tasks),
        'actual_scorer_controls': sum(len(c['checks']) for c in checks),
        'actual_additional_Conclusion_identity_set_controls':4,
        'repair_classes': dict(Counter(t['repair_class'] for t in tasks)),
        'graph_sources': parent_manifest['graph_sources'],
        'model_predictions_n': 0, 'expert_validation_n': 0, 'human_author_review_completed': False,
        'source_public_projection': 'source_public_projection.json',
        'source_population_replay':'source_population_replay.json',
        'files': {str(p.relative_to(DEST)): sha(p) for p in DEST.rglob('*') if p.is_file()}}
    write_json(DEST / 'manifest.json', manifest)
    print(json.dumps({'status': 'BUNDLE_PREPARED_REQUIRE_OFFLINE_REPLAY', 'bundle': str(DEST),
        'manifest_sha256': sha(DEST / 'manifest.json'), 'admitted_n': 1,
        'native_rows': manifest['native_rows'], 'actual_scorer_controls': manifest['actual_scorer_controls']}))


if __name__ == '__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--preflight-only',action='store_true',help='verify completed pinned gates without creating a bundle')
    args=p.parse_args()
    if args.preflight_only:print(json.dumps(preflight()))
    else:main()
