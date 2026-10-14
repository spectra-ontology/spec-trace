#!/usr/bin/env python3
"""Fresh four-arm evaluation of two observed-agenda-trend original Core questions.

Only this separately admitted question is predicted; previous phases remain frozen.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
sys.dont_write_bytecode = True
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE))
sys.path.insert(0,str(BASE/'observed_trend_runtime'))
import structured_adapter as structured
import retrieval_adapter as retrieval
import run_evaluation as runtime
from topk_current_evaluation import ddl_audit


def freeze(bundle,parent,run):
    if run.exists():raise ValueError('Refuse to overwrite a frozen phase')
    sys.path.insert(0,str(bundle))
    import verify_observed_trend
    proof=verify_observed_trend.verify(bundle,parent)
    if proof['status']!='PASS' or proof['additional_admitted_n']!=2:
        raise ValueError('Two complete admitted questions required')
    tasks=runtime.read(bundle/'tasks.jsonl')
    if [t['id'] for t in tasks]!=['RAN3_P2_CQ6-1','RAN4_P2_CQ6-1']:
        raise ValueError('Frozen all-method item scope differs')
    audits=[]
    for wg in ['RAN1','RAN2','RAN3','RAN4','RAN5']:
        audits.append(ddl_audit(wg,json.loads((BASE/'sql_interface_v2/schemas'/(wg+'_sql.json')).read_text())))
    run.mkdir(parents=True)
    runtime.freeze(bundle,run)
    shutil.copy2(run/'protocol.json',run/'runtime_freeze_base.json')
    p=json.loads((run/'protocol.json').read_text())
    for wg in ['RAN1','RAN2','RAN3','RAN4','RAN5']:
        shutil.copy2(BASE/'sql_interface_v2/schemas'/(wg+'_sql.json'),run/'schemas'/(wg+'_sql.json'))
    public=runtime.read(run/'public_tasks.jsonl')
    for task in public:
        task['ordering_format']={'rule':'Order records by the numeric Meeting.meetingNumberInt chronology ascending. Any order among equal numeric meeting ordinals is allowed. The auxiliary ordinal is not a requested answer field.'}
        structured.reject_private(task)
    (run/'public_tasks.jsonl').write_text(''.join(json.dumps(t,ensure_ascii=False)+'\n' for t in public))
    p['public_tasks_sha256']=runtime.sha(run/'public_tasks.jsonl')
    for name in ['structured_adapter.py','retrieval_adapter.py']:
        p['code_pins'].pop(name)
        p['code_pins']['observed_trend_runtime/'+name]=runtime.sha(BASE/'observed_trend_runtime'/name)
    p['schema_pins']={str(f.relative_to(run)):runtime.sha(f) for f in sorted((run/'schemas').glob('*.json'))}
    p['code_pins'].update({'observed_trend_evaluation.py':runtime.sha(__file__),
                           'topk_current_evaluation.py':runtime.sha(BASE/'topk_current_evaluation.py')})
    p['SQL_interface']='Complete value-free physical SQLite DDL; unchanged SQL-interface-v2 cards.'
    p['budget_guard_usd']=2.0
    p['generation_workers']=1
    p['execution_workers']=1
    p['working_group_execution_workers']=1
    p['observed_trend_scope']={'original_ids':['RAN3_P2_CQ6-1','RAN4_P2_CQ6-1'],'method_items':8,'all_methods_fixed_before_prediction':True,
        'parent_manifest_sha256':runtime.sha(parent/'manifest.json'),
        'parent_tasks_sha256':runtime.sha(parent/'tasks.jsonl'),
        'parent_relative_verification_union_n':373,
        'global_admission_count_owned_by_current_index':True,
        'no_common_source_appendix':True,'new_model_calls_before_registration':0,
        'model_quality_retry':False,'human_author_expert_validation_n':0,
        'source_validation_before_calls':proof,
        'raw_runtime_freeze_sha256':runtime.sha(run/'runtime_freeze_base.json'),
        'planned_calls_without_transport_retry':10,
        'estimated_cost_usd':2*91.705970/371,
        'cost_estimate_scope':'Historical four-method spend per item; actual usage is authoritative.',
        'legacy_admitted_n_field_scope':'Two-item phase size only.',
        'legacy_unresolved_n_field_scope':'Original Core IDs outside this phase, not the current global unresolved ledger.'}
    runtime.write(run/'schema_preflight.json',{'status':'PASS','groups':audits,'business_values_read':False})
    p['schema_preflight_sha256']=runtime.sha(run/'schema_preflight.json')
    runtime.write(run/'protocol.json',p)
    print(json.dumps({'status':'FROZEN','question_n':2,'method_items':8,
        'protocol_sha256':runtime.sha(run/'protocol.json'),'budget_guard_usd':2.0,'generation_workers':1,'new_model_calls':0}),flush=True)


def verify(bundle,run):
    p=runtime.verify_pins(bundle,run)
    scope=p['observed_trend_scope']
    for name,digest in [('tasks.jsonl',p['tasks_sha256']),('reference_gold.jsonl',p['gold_sha256'])]:
        if runtime.sha(bundle/name)!=digest:raise ValueError('Frozen question/gold changed')
    if runtime.sha(run/'runtime_freeze_base.json')!=scope['raw_runtime_freeze_sha256']:
        raise ValueError('Raw runtime freeze changed')
    if runtime.sha(run/'schema_preflight.json')!=p['schema_preflight_sha256']:
        raise ValueError('Actual DDL preflight changed')
    if [t['id'] for t in runtime.read(run/'public_tasks.jsonl')]!=scope['original_ids']:
        raise ValueError('Model-visible scope differs')
    return p


def execute(bundle,run):
    protocol=verify(bundle,run)
    if (run/'execution_complete.json').exists():raise ValueError('Execution already completed')
    sys.path.insert(0,str(runtime.HELPERS))
    import execute_frozen_reference_gold as source
    import replay_generated_read_queries as guard
    from neo4j import GraphDatabase
    tasks=runtime.read(run/'public_tasks.jsonl')
    groups=sorted({task['wg'] for task in tasks})
    def group(wg):
        selected=[task for task in tasks if task['wg']==wg]
        container='kdd-db-frozen-v1-'+wg.lower()
        inspected=json.loads(subprocess.check_output(['docker','inspect',container]))[0]
        if inspected['State']['Running']:raise ValueError('Owned container must be idle: '+wg)
        subprocess.run(['docker','start',container],check=True,stdout=subprocess.DEVNULL)
        try:
            for _ in range(60):
                try:
                    with GraphDatabase.driver('bolt://127.0.0.1:'+str(source.PORTS[wg]),auth=None,connection_timeout=2) as driver:
                        driver.verify_connectivity()
                    break
                except Exception:time.sleep(1)
            else:raise RuntimeError('Archival database readiness failed: '+wg)
            guard.owned_container_guard(wg)
            before=source.source_guard(wg)
            if before!=protocol['graph_sources'][wg]:raise ValueError('Frozen source differs: '+wg)
            db=BASE/'relational'/(wg+'.sqlite')
            manifest=json.loads((BASE/'relational'/(wg+'.manifest.json')).read_text())
            expected=manifest.get('sqlite_sha256',manifest.get('db_sha256',manifest.get('output_sha256')))
            db_sha=runtime.sha(db);db_stat=structured.file_identity(db)
            if db_sha!=expected:raise ValueError('Frozen SQL source differs: '+wg)
            items=[]
            for task in selected:
                for arm in ['A','B']:
                    name=runtime.ARMS[arm];kind='graph' if arm=='A' else 'sql'
                    public=dict(task)
                    public[kind+'_schema']=json.loads((run/'schemas'/(wg+'_'+kind+'.json')).read_text())
                    generated=json.loads((run/'arm_outputs'/name/(task['id']+'.json')).read_text())
                    kwargs=({'executor_directory':runtime.HELPERS,'source_guard_expected':before,'source_guard_batch_verified':True} if arm=='A' else
                            {'sql_db':db,'expected_sql_sha':db_sha,'expected_sql_stat':db_stat,'source_guard_batch_verified':True})
                    outcome=structured.execute_generated(generated,public,**kwargs)
                    runtime.write(run/'executed'/name/(task['id']+'.json'),outcome)
                    items.append({'id':task['id'],'arm':arm,'status':outcome['status']})
                    print(json.dumps({'wg':wg,'id':task['id'],'arm':arm,'status':outcome['status']}),flush=True)
            after=source.source_guard(wg)
            if after!=before or runtime.sha(db)!=db_sha:raise ValueError('Graph/SQL source changed: '+wg)
            runtime.write(run/'source_guards'/(wg+'.json'),{'before':before,'after':after,'sql_sha256':db_sha,'unchanged':True,'items':items})
            return items
        finally:
            subprocess.run(['docker','stop','-t','10',container],check=True,stdout=subprocess.DEVNULL)
    with ThreadPoolExecutor(max_workers=1) as pool:
        items=[item for future in as_completed([pool.submit(group,wg) for wg in groups]) for item in future.result()]
    for arm,name in runtime.ARMS.items():
        predictions=[];statuses=[]
        for task in tasks:
            directory='executed' if arm in ['A','B'] else 'arm_outputs'
            path=run/directory/name/(task['id']+'.json')
            outcome=json.loads(path.read_text())
            predictions.append({'id':task['id'],'repair_sha256':task['repair_sha256'],'records':outcome['records']})
            statuses.append({'id':task['id'],'repair_sha256':task['repair_sha256'],'status':outcome['status'].upper(),'artifact':str(path.relative_to(run))})
        for filename,records in [('predictions.jsonl',predictions),('statuses.jsonl',statuses)]:
            path=run/name/filename;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(''.join(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n' for row in records))
    verify(bundle,run)
    runtime.write(run/'execution_complete.json',{'structured_method_items':len(items),'expected':4,
                   'all_four_method_items':8,'working_groups':groups,'max_parallel_working_groups':1,
                   'each_working_group_query_workers':1,'new_model_calls':0,'source_guards_unchanged':True})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['freeze','generate','execute','analyze'])
    for name in ['bundle','parent','run-dir']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    bundle,parent,run=args.bundle.resolve(),args.parent.resolve(),args.run_dir.resolve()
    if args.action=='freeze':freeze(bundle,parent,run)
    elif args.action=='generate':
        verify(bundle,run)
        runtime.generate(bundle,run)
        print(json.dumps({'status':'GENERATION_COMPLETE','outputs':{
            name:{t['id']:json.loads((run/'arm_outputs'/name/(t['id']+'.json')).read_text())['status'] for t in runtime.read(run/'public_tasks.jsonl')}
            for name in runtime.ARMS.values()},'usage':json.loads((run/'usage.json').read_text())}),flush=True)
    elif args.action=='execute':execute(bundle,run)
    else:
        verify(bundle,run)
        import analyze_predictions
        analyze_predictions.run(bundle,run)
        print((run/'performance_table.md').read_text(),flush=True)
