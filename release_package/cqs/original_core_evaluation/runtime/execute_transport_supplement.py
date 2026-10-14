#!/usr/bin/env python3
"""Reuse pinned original executions; execute only newly recovered queries.

Separate wrapper; never alters the original scientific runtime or run.
No model/API calls. The CLI freeze records the policy and immutable inputs
before any supplemental query execution. CLI execute is run by the root.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

BASE=Path(__file__).resolve().parent
ORIGINAL=BASE/'runs/original-core-main'
SUPPLEMENT=BASE/'runs/original-core-transport-supplement'
BUNDLE=BASE.parent/'original_repair/final_staging/release_package/cqs/original_core_repair'
HELPERS=Path('/home/sihyeon/workspace/spectra-public/spec-trace/release_package/cqs/contract_repair_v1')
ARMS={'A':'text2cypher','B':'text2sql','C':'single_retrieval','D':'iterative_retrieval'}
WGS=['RAN1','RAN2','RAN3','RAN4','RAN5']
SIDECAR='execution_supplement_protocol.json'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text())


def rows(path):return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():raise ValueError('Existing supplemental artifact; uncontrolled execution rerun forbidden: '+str(path))
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def generation_identity(record):
    """Compare scientific generation inputs/result, excluding added provenance."""
    keys=['id','repair_sha256','method','wg','status','abstain','generated_query',
          'query_sha256','adapter_sha256','prompt_sha256']
    return {k:record.get(k) for k in keys}


def reusable(original_generation,new_generation,original_execution,task):
    if generation_identity(original_generation)!=generation_identity(new_generation):return False
    for record in [original_generation,new_generation,original_execution]:
        if record.get('id')!=task['id'] or record.get('repair_sha256')!=task['repair_sha256']:return False
    if original_execution.get('generated_query')!=original_generation.get('generated_query'):return False
    if original_execution.get('query_sha256')!=original_generation.get('query_sha256'):return False
    if original_execution.get('method')!=original_generation.get('method'):return False
    query=original_generation.get('generated_query')
    if query is not None and hashlib.sha256(query.encode()).hexdigest()!=original_generation.get('query_sha256'):return False
    # QUERY_READY must have a completed actual executor outcome, even if it was
    # an execution error. Never rerun a syntax/quality failure for improvement.
    if original_generation.get('status')=='QUERY_READY' and not isinstance(original_execution.get('execution'),dict):return False
    return True


def verify_original_guard(value,protocol,wg,db_hash):
    if (value.get('unchanged') is not True or value.get('before')!=protocol['graph_sources'][wg]
            or value.get('after')!=value['before'] or value.get('sql_sha256')!=db_hash):
        raise ValueError('Original execution source guard is absent or differs: '+wg)


def verify_inputs(original,supplement,bundle):
    import run_evaluation as runtime
    op=runtime.verify_pins(bundle,original);sp=runtime.verify_pins(bundle,supplement)
    if sp['transport_recovery']['original_protocol_sha256']!=sha(original/'protocol.json'):
        raise ValueError('Supplement is not linked to this original protocol')
    keys=['cohort_ids','bundle_manifest_sha256','tasks_sha256','gold_sha256','scorer_sha256',
          'original_scorer_sha256','typed_scorer_sha256','typed_kernel_sha256','graph_sources',
          'sql_manifests','public_tasks_sha256','schema_pins','execution_limits']
    if any(op[k]!=sp[k] for k in keys):raise ValueError('Supplement scientific inputs differ from original')
    for name,key in [('tasks.jsonl','tasks_sha256'),('reference_gold.jsonl','gold_sha256'),
                     ('score_predictions.py','scorer_sha256'),('original_scorer.py','original_scorer_sha256'),
                     ('scorer.py','typed_scorer_sha256'),('typed_values.py','typed_kernel_sha256')]:
        if sha(bundle/name)!=op[key]:raise ValueError('Frozen bundle component changed: '+name)
    for wg,pin in op['sql_manifests'].items():
        if sha(pin['path'])!=pin['sha256']:raise ValueError('Pinned SQL manifest changed')
    tasks=rows(original/'public_tasks.jsonl')
    if rows(supplement/'public_tasks.jsonl')!=tasks or [t['id'] for t in tasks]!=op['cohort_ids']:
        raise ValueError('Public task definition changed')
    return op,sp,tasks


def freeze(original,supplement,bundle):
    original=original.resolve();supplement=supplement.resolve();bundle=bundle.resolve()
    op,sp,tasks=verify_inputs(original,supplement,bundle)
    # Do not freeze an incomplete original source-execution inventory.
    inventory={}
    for task in tasks:
        for arm in ['A','B']:
            for directory in ['arm_outputs','executed']:
                path=original/directory/ARMS[arm]/(task['id']+'.json')
                value=read(path)
                if value.get('id')!=task['id'] or value.get('repair_sha256')!=task['repair_sha256']:
                    raise ValueError('Original execution identity changed')
                inventory[str(path.relative_to(original))]=sha(path)
    for wg in WGS:
        manifest=read(op['sql_manifests'][wg]['path'])
        db_hash=manifest.get('sqlite_sha256',manifest.get('db_sha256',manifest.get('output_sha256')))
        path=original/'source_guards'/(wg+'.json')
        verify_original_guard(read(path),op,wg,db_hash)
        inventory[str(path.relative_to(original))]=sha(path)
    policy={'frozen_utc':datetime.now(timezone.utc).isoformat(),'original_run':str(original),
        'original_protocol_sha256':sha(original/'protocol.json'),'supplement_protocol_sha256':sha(supplement/'protocol.json'),
        'wrapper_sha256':sha(__file__),'cohort_ids':op['cohort_ids'],'n':len(tasks),
        'original_execution_inputs':inventory,
        'reuse_rule':'Reuse original actual execution only when public task, repair, adapter, prompt, generated-query bytes/hash and full original unchanged source guards match. Preserve execution failures too; no quality rerun.',
        'new_query_rule':'Run only a QUERY_READY generation whose scientific generation identity differs from original. Unchanged read-only executor, caps, source guards and two workers. Nonready new outcomes need no database execution.',
        'guard_rule':'Original executions are backed by retained full pre/post graph and SQL guards. New graph/SQL executions require fresh pre/post guards; no claim of a fresh database read for reused results.',
        'models_called':0,'runtime_or_source_modified':False,'query_quality_retries':0}
    write(supplement/SIDECAR,policy)
    print(json.dumps({'execution_supplement_frozen':True,'n':len(tasks),'sidecar_sha256':sha(supplement/SIDECAR),'wrapper_sha256':sha(__file__)}),flush=True)


def execute(original,supplement,bundle):
    original=original.resolve();supplement=supplement.resolve();bundle=bundle.resolve()
    op,sp,tasks=verify_inputs(original,supplement,bundle);policy=read(supplement/SIDECAR)
    if (sha(__file__)!=policy['wrapper_sha256'] or sha(original/'protocol.json')!=policy['original_protocol_sha256']
            or sha(supplement/'protocol.json')!=policy['supplement_protocol_sha256']):raise ValueError('Frozen execution wrapper changed')
    for name,pin in policy['original_execution_inputs'].items():
        if sha(original/name)!=pin:raise ValueError('Original execution artifacts changed')
    completion=read(supplement/'generation_complete.json')
    if completion.get('completed_method_items')!=len(tasks)*4 or completion.get('required')!=len(tasks)*4:
        raise ValueError('Supplement generation incomplete')
    write(supplement/'execution_supplement_started.json',{'started_utc':datetime.now(timezone.utc).isoformat(),
          'sidecar_sha256':sha(supplement/SIDECAR),'generation_complete_sha256':sha(supplement/'generation_complete.json')})
    import structured_adapter as structured
    sys.path.insert(0,str(HELPERS));import execute_frozen_reference_gold as source
    import replay_generated_read_queries as guard
    all_receipts=[]
    for wg in WGS:
        selected=[t for t in tasks if t['wg']==wg];todo=[];receipts=[]
        for task in selected:
            for arm in ['A','B']:
                name=ARMS[arm];rel=Path('executed')/name/(task['id']+'.json')
                prior=read(original/rel);og=read(original/'arm_outputs'/name/(task['id']+'.json'))
                ng=read(supplement/'arm_outputs'/name/(task['id']+'.json'))
                if reusable(og,ng,prior,task):
                    result=dict(prior)
                    result['execution_transport_provenance']={'mode':'reused_original_actual_execution',
                         'original_execution_path':str(original/rel),'original_execution_sha256':sha(original/rel),
                         'original_generation_sha256':sha(original/'arm_outputs'/name/(task['id']+'.json')),
                         'supplement_generation_sha256':sha(supplement/'arm_outputs'/name/(task['id']+'.json')),
                         'original_source_guard_sha256':sha(original/'source_guards'/(wg+'.json')),'quality_retry':False}
                    write(supplement/rel,result)
                    receipts.append({'id':task['id'],'arm':arm,'status':result['status'],'mode':'reused_original_actual_execution'})
                elif ng['status']!='QUERY_READY':
                    result=dict(ng);result['execution_transport_provenance']={'mode':'new_nonready_outcome_no_database_execution','quality_retry':False}
                    write(supplement/rel,result)
                    receipts.append({'id':task['id'],'arm':arm,'status':result['status'],'mode':'new_nonready_outcome_no_database_execution'})
                else:todo.append((task,arm,ng))
        needs_graph=any(a=='A' for _,a,_ in todo);needs_sql=any(a=='B' for _,a,_ in todo)
        container='kdd-db-frozen-v1-'+wg.lower();graph_before=None;db_before=None;db_stat=None;started_container=False
        db=BASE/'relational'/(wg+'.sqlite')
        try:
            if needs_graph:
                from neo4j import GraphDatabase
                inspect=read_inspect(container)
                if inspect['State']['Running']:raise ValueError('Expected idle owned archival container')
                subprocess.run(['docker','start',container],check=True,stdout=subprocess.DEVNULL)
                started_container=True
                for _ in range(60):
                    try:
                        with GraphDatabase.driver('bolt://127.0.0.1:'+str(source.PORTS[wg]),auth=None,connection_timeout=2) as driver:driver.verify_connectivity()
                        break
                    except Exception:time.sleep(1)
                else:raise RuntimeError('Archival database readiness failed')
                guard.owned_container_guard(wg);graph_before=source.source_guard(wg)
                if graph_before!=op['graph_sources'][wg]:raise ValueError('Frozen graph source differs')
            if needs_sql:
                db_before=sha(db);db_stat=structured.file_identity(db)
                manifest=read(op['sql_manifests'][wg]['path'])
                expected=manifest.get('sqlite_sha256',manifest.get('db_sha256',manifest.get('output_sha256')))
                if db_before!=expected:raise ValueError('Frozen SQL source differs')
            def job(item):
                task,arm,generated=item;public=dict(task);kind='graph' if arm=='A' else 'sql'
                public[kind+'_schema']=read(supplement/'schemas'/(wg+'_'+kind+'.json'))
                kwargs=({'executor_directory':HELPERS,'source_guard_expected':graph_before,'source_guard_batch_verified':True}
                    if arm=='A' else {'sql_db':db,'expected_sql_sha':db_before,'expected_sql_stat':db_stat,'source_guard_batch_verified':True})
                result=structured.execute_generated(generated,public,**kwargs)
                result['execution_transport_provenance']={'mode':'first_execution_of_recovered_generated_query',
                    'supplement_generation_sha256':sha(supplement/'arm_outputs'/ARMS[arm]/(task['id']+'.json')),'quality_retry':False}
                write(supplement/'executed'/ARMS[arm]/(task['id']+'.json'),result)
                return {'id':task['id'],'arm':arm,'status':result['status'],'mode':'first_execution_of_recovered_generated_query'}
            with ThreadPoolExecutor(max_workers=sp['execution_workers']) as executor:
                receipts.extend(f.result() for f in as_completed([executor.submit(job,x) for x in todo]))
            graph_after=source.source_guard(wg) if needs_graph else None
            sql_after=sha(db) if needs_sql else None
            if graph_after!=graph_before or sql_after!=db_before:raise ValueError('Source changed during recovered-query execution')
            write(supplement/'source_guards'/(wg+'.json'),{'wg':wg,
                  'original_source_guard_sha256':sha(original/'source_guards'/(wg+'.json')),
                  'original_source_guard_used_for_reused_executions':True,
                  'fresh_graph_before':graph_before,'fresh_graph_after':graph_after,
                  'fresh_sql_before_sha256':db_before,'fresh_sql_after_sha256':sql_after,
                  'unchanged':True,'fresh_graph_checked':needs_graph,'fresh_sql_checked':needs_sql,'items':receipts})
            all_receipts.extend(receipts)
            print(json.dumps({'wg_execution_complete':wg,'method_items':len(receipts),
                             'reused':sum(x['mode']=='reused_original_actual_execution' for x in receipts),
                             'new_queries_executed':len(todo)}),flush=True)
        finally:
            if started_container:
                subprocess.run(['docker','stop','-t','10',container],check=True,stdout=subprocess.DEVNULL)
    for arm,name in ARMS.items():
        preds=[];statuses=[]
        for task in tasks:
            directory='executed' if arm in {'A','B'} else 'arm_outputs'
            path=supplement/directory/name/(task['id']+'.json');o=read(path)
            preds.append({'id':task['id'],'repair_sha256':task['repair_sha256'],'records':o['records']})
            statuses.append({'id':task['id'],'repair_sha256':task['repair_sha256'],'status':o['status'].upper(),'artifact':str(path.relative_to(supplement))})
        for name_,values in [('predictions.jsonl',preds),('statuses.jsonl',statuses)]:
            path=supplement/name/name_;path.parent.mkdir(parents=True,exist_ok=True)
            if path.exists():raise ValueError('Existing supplemental predictions')
            path.write_text(''.join(json.dumps(v,ensure_ascii=False,allow_nan=False)+'\n' for v in values))
    for name,pin in policy['original_execution_inputs'].items():
        if sha(original/name)!=pin:raise ValueError('Original executions changed during supplemental execution')
    write(supplement/'execution_complete.json',{'completed_method_items':len(all_receipts),'required':len(tasks)*2,
         'original_execution_artifacts_unchanged':True,'items':all_receipts,'models_called':0})


def read_inspect(container):return json.loads(subprocess.check_output(['docker','inspect',container]))[0]


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('action',choices=['freeze','execute'])
    a.add_argument('--original',type=Path,default=ORIGINAL);a.add_argument('--supplement',type=Path,default=SUPPLEMENT)
    a.add_argument('--bundle',type=Path,default=BUNDLE)
    args=a.parse_args();globals()[args.action](args.original,args.supplement,args.bundle)
