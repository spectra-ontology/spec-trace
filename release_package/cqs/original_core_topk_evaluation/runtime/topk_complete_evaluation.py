#!/usr/bin/env python3
"""Assemble fixed pre-answer recovery choices and execute/score all TOP10 arms."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE))
import run_evaluation as runtime
import structured_adapter as structured


def prepare(bundle,parent,original,recovery,run):
    import topk_current_evaluation,topk_operational_recovery
    first=topk_current_evaluation.verify(bundle,parent,original)
    recovered=topk_operational_recovery.verify(bundle,original,recovery)
    if run.exists() or not (recovery/'generation_complete.json').exists():
        raise ValueError('Combined phase exists or operational phase incomplete')
    selected={(r['id'],r['arm']) for r in recovered['operational_recovery']['selected_method_items']}
    run.mkdir(parents=True)
    for name in ['public_tasks.jsonl','retrieval_corpus_inventory.json','retrieval_protocol.json','schema_preflight.json','runtime_freeze_base.json']:
        if (original/name).exists():shutil.copy2(original/name,run/name)
    shutil.copytree(original/'schemas',run/'schemas')
    choices=[]
    for task in runtime.read(original/'public_tasks.jsonl'):
        for arm,name in runtime.ARMS.items():
            source=recovery if (task['id'],arm) in selected else original
            path=source/'arm_outputs'/name/(task['id']+'.json')
            output=json.loads(path.read_text())
            if output['id']!=task['id'] or output['repair_sha256']!=task['repair_sha256']:
                raise ValueError('Prediction identity differs')
            target=run/'arm_outputs'/name/path.name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(path,target)
            choices.append({'id':task['id'],'arm':arm,'method':name,
                            'selection':'registered_pre_answer_operational_recovery' if source==recovery else 'preserved_original_prediction',
                            'source_file':str(path),'source_sha256':runtime.sha(path),
                            'combined_file':str(target.relative_to(run)),'status':output['status']})
    if len(choices)!=40 or len(selected)!=15:
        raise ValueError('Complete four-arm fixed selection differs')
    runtime.write(run/'selection.json',choices)
    protocol=dict(first)
    protocol['frozen_utc']=datetime.now(timezone.utc).isoformat()
    protocol['code_pins']=dict(first['code_pins'],**{'topk_complete_evaluation.py':runtime.sha(__file__)})
    protocol['execution_workers']=1
    protocol['working_group_execution_workers']=2
    protocol['model_calls_from_this_combined_phase']=0
    protocol['phase_assembly']={
        'original_protocol_sha256':runtime.sha(original/'protocol.json'),
        'operational_protocol_sha256':runtime.sha(recovery/'protocol.json'),
        'operational_generation_complete_sha256':runtime.sha(recovery/'generation_complete.json'),
        'selection_sha256':runtime.sha(run/'selection.json'),
        'original_predictions_retained':25,'pre_registered_operational_predictions_retained':15,
        'complete_method_items':40,'performance_based_selection':False,
        'new_model_calls':0,'original_files_overwritten':False,
        'source_guard_limit':'Inventory counts/source pins do not detect same-count property mutation; frozen owned read-only archival containers are required.'}
    runtime.write(run/'protocol.json',protocol)
    usages=[json.loads((p/'usage.json').read_text()) for p in [original,recovery]]
    runtime.write(run/'combined_usage.json',{'known_actual_cost_usd':sum(u['known_actual_cost_usd'] for u in usages),
                    'unknown_cost_attempts':sum(u['unknown_cost_attempts'] for u in usages),
                    'received_response_calls':sum(u['received_response_calls'] for u in usages),
                    'original_usage_sha256':runtime.sha(original/'usage.json'),
                    'operational_usage_sha256':runtime.sha(recovery/'usage.json'),
                    'new_model_calls_in_combined_phase':0})
    print(json.dumps({'status':'PREPARED','method_items':40,'protocol_sha256':runtime.sha(run/'protocol.json')}),flush=True)


def verify(bundle,run):
    protocol=runtime.verify_pins(bundle,run)
    if runtime.sha(run/'selection.json')!=protocol['phase_assembly']['selection_sha256']:
        raise ValueError('Fixed prediction selection changed')
    for selected in json.loads((run/'selection.json').read_text()):
        if runtime.sha(run/selected['combined_file'])!=selected['source_sha256'] or runtime.sha(Path(selected['source_file']))!=selected['source_sha256']:
            raise ValueError('Copied prediction changed')
    return protocol


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
    with ThreadPoolExecutor(max_workers=2) as pool:
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
    runtime.write(run/'execution_complete.json',{'structured_method_items':len(items),'expected':20,
                   'all_four_method_items':40,'working_groups':groups,'max_parallel_working_groups':2,
                   'each_working_group_query_workers':1,'new_model_calls':0,'source_guards_unchanged':True})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','execute'])
    for name in ['bundle','parent','original','recovery','run-dir']:
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    if args.action=='prepare':prepare(args.bundle.resolve(),args.parent.resolve(),args.original.resolve(),args.recovery.resolve(),args.run_dir.resolve())
    else:execute(args.bundle.resolve(),args.run_dir.resolve())
