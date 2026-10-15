#!/usr/bin/env python3
"""Four-arm new evaluation. Freeze before calls; execute generated queries later."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

BASE=Path(__file__).resolve().parent
ROOT=next(p for p in BASE.parents if (p/'.git').exists())
DEFAULT_BUNDLE=BASE.parent/'original_repair/final_staging/release_package/cqs/original_core_repair'
DEFAULT_RUN=BASE/'runs/original-core-main'
HELPERS=Path('/home/sihyeon/workspace/spectra-public/spec-trace/release_package/cqs/contract_repair_v1')
ARMS={'A':'text2cypher','B':'text2sql','C':'single_retrieval','D':'iterative_retrieval'}


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def read(p):return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]


def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def public_task(t):
    allowed={'name','type','nullable','json_schema','nested_array_semantics'}
    collection={k:v for k,v in t['collection'].items() if k in
                {'kind','value','tie_policy','within_tie_order','require_rank_order','order_keys','source_order_keys'}}
    result={'id':t['id'],'wg':t['id'].split('_')[0],'repair_sha256':t['repair_sha256'],
            'question_en':t['question_en'],
            'required_fields':[{k:v for k,v in f.items() if k in allowed} for f in t['required_fields']],
            'collection':collection,'cardinality_policy':t['cardinality_policy']}
    if t['id'] in {'RAN1_P2_CQ2-4','RAN5_P1_CQ3-1','RAN5_P2_CQ1-6'}:
        result['identity_format']={'field':t['required_fields'][0]['name'],
            'rule':'Use the agenda item business ID when available; otherwise use its deterministic loader identity. Keep different agenda entities distinct.',
            'loader_identity_codec':'https://w3id.org/spectra/inst/_/{class}/{local_id}',
            'note':'This is an output-identity convention, not an answer value or a filter excluding anonymous items.'}
    return result


def freeze(bundle,run_dir):
    import structured_adapter as structured
    import retrieval_adapter as retrieval
    from openrouter_client import MODEL,PROVIDER
    if (run_dir/'protocol.json').exists():raise ValueError('protocol already frozen')
    tasks=read(bundle/'tasks.jsonl')
    ids=[t['id'] for t in tasks]
    if not tasks or len(ids)!=len(set(ids)):raise ValueError('empty or duplicate cohort')
    corpus=retrieval.prepare_corpus_inventory(run_dir)
    sql={wg:json.loads((BASE/'relational'/(wg+'.manifest.json')).read_text())
         for wg in ['RAN1','RAN2','RAN3','RAN4','RAN5']}
    source_schema=json.loads((HELPERS/'source_schema_frozen_v1.json').read_text())
    public=[public_task(t) for t in tasks]
    (run_dir/'public_tasks.jsonl').write_text(''.join(json.dumps(t,ensure_ascii=False)+'\n' for t in public))
    for wg in sql:
        write(run_dir/'schemas'/(wg+'_sql.json'),sql[wg]['schema'])
        write(run_dir/'schemas'/(wg+'_graph.json'),structured.graph_schema(source_schema['working_groups'][wg]))
    # Catalog prices verified before any benchmark predictions. This upper
    # bound assumes every arm uses its entire output budget, not actual spend.
    generation=structured.MAX_GENERATION_TOKENS
    answer=retrieval.PROTOCOL['answer_max_tokens']
    followup=retrieval.PROTOCOL['followup_max_tokens']
    calls=len(tasks)*5
    max_output=len(tasks)*(generation*2+answer*2+followup)
    configuration={'kind':'Frozen four-arm comparison on actual admitted original questions',
       'frozen_utc':datetime.now(timezone.utc).isoformat(),'model':MODEL,'provider':PROVIDER,
       'provider_fallbacks':False,'model_fallbacks':False,'temperature':'unsupported; omitted',
       'reasoning':{'enabled':False},'response_format':{'type':'json_object'},
       'original_total':560,'admitted_n':len(tasks),'unresolved_n':560-len(tasks),
       'cohort_ids':ids,'bundle_manifest_sha256':sha(bundle/'manifest.json'),
       'tasks_sha256':sha(bundle/'tasks.jsonl'),'gold_sha256':sha(bundle/'reference_gold.jsonl'),
       'public_tasks_sha256':sha(run_dir/'public_tasks.jsonl'),
       'scorer_sha256':sha(bundle/'score_predictions.py'),
       'original_scorer_sha256':sha(bundle/'original_scorer.py'),
       'typed_scorer_sha256':sha(bundle/'scorer.py'),
       'typed_kernel_sha256':sha(bundle/'typed_values.py'),
       'source_schema_sha256':sha(HELPERS/'source_schema_frozen_v1.json'),
       'code_pins':{n:sha(BASE/n) for n in ['openrouter_client.py','run_evaluation.py',
           'structured_adapter.py','retrieval_adapter.py','build_frozen_sqlite.py','add_loader_identity.py','analyze_predictions.py']},
       'schema_pins':{str(p.relative_to(run_dir)):sha(p) for p in (run_dir/'schemas').glob('*.json')},
       'graph_sources':json.loads((bundle/'manifest.json').read_text())['graph_sources'],
       'sql_manifests':{wg:{'path':str(BASE/'relational'/(wg+'.manifest.json')),
                           'sha256':sha(BASE/'relational'/(wg+'.manifest.json'))} for wg in sql},
       'retrieval_inventory_sha256':sha(run_dir/'retrieval_corpus_inventory.json'),
       'retrieval_protocol':retrieval.PROTOCOL,'generation_tokens':generation,
       'max_planned_calls_without_transport_retry':calls,
       'max_output_tokens_without_transport_retry':max_output,
       'max_output_cost_without_transport_retry_usd':max_output*.000025,
       'prompt_cost_estimate_note':'Estimated from actual frozen prompt characters using chars/3; authoritative tokens/cost are response usage. No claim that this is a tokenizer.',
       'budget_guard_usd':350.0,'generation_workers':8,'execution_workers':2,
       'retry_policy':{'transport_attempts':2,'retry_only':'429,5xx or network error',
                       'identical_payload':True,'delay_seconds':2,'answer_quality_retry':False},
       'execution_limits':{'rows':100000,'bytes':256*1024*1024,'timeout_s':60},
       'primary_metrics':['requested-field complete-record macro F1','exact output rate'],
       'failure_scoring':'All IDs retained; execution failure/abstention F1=0/exact=false even for empty gold. Parsed partial records receive matching credit; partial empty output cannot establish empty-gold success.',
       'information_access':'Graph and new SQL preserve the frozen record inventory; archive text cutoff/content equality is unverified and finite retrieved context is bounded.',
       'interpretation':'One model and a nonrepresentative admitted subset; no storage-medium causal advantage claimed.'}
    write(run_dir/'protocol.json',configuration)
    print(json.dumps({'frozen_n':len(tasks),'planned_calls':calls,
                      'max_output_cost_usd':configuration['max_output_cost_without_transport_retry_usd'],
                      'protocol_sha256':sha(run_dir/'protocol.json')}),flush=True)


def verify_pins(bundle,run_dir):
    p=json.loads((run_dir/'protocol.json').read_text())
    for n,h in p['code_pins'].items():
        if sha(BASE/n)!=h:raise ValueError('frozen implementation changed: '+n)
    for n,h in p['schema_pins'].items():
        if sha(run_dir/n)!=h:raise ValueError('frozen schema changed')
    if sha(bundle/'manifest.json')!=p['bundle_manifest_sha256'] or sha(run_dir/'public_tasks.jsonl')!=p['public_tasks_sha256']:
        raise ValueError('frozen cohort changed')
    return p


def generate(bundle,run_dir):
    p=verify_pins(bundle,run_dir)
    import structured_adapter as structured
    import retrieval_adapter as retrieval
    from openrouter_client import OpenRouterCaller
    sys.path.insert(0,str(ROOT/'scripts/common/common'))
    import credentials
    caller=OpenRouterCaller(run_dir,credentials.secret('OPENROUTER_API_KEY'),p['budget_guard_usd'])
    tasks=read(run_dir/'public_tasks.jsonl')
    def job(task,arm):
        path=run_dir/'arm_outputs'/ARMS[arm]/(task['id']+'.json')
        if path.exists():raise ValueError('existing prediction; no quality-based rerun allowed')
        try:
            public=dict(task)
            if arm in {'A','B'}:
                kind='graph' if arm=='A' else 'sql'
                public[kind+'_schema']=json.loads((run_dir/'schemas'/(task['wg']+'_'+kind+'.json')).read_text())
                outcome=structured.evaluate(public,arm,caller,run_dir)
            else:
                outcome=retrieval.evaluate(public,arm,caller,run_dir)
        except Exception as exc:
            outcome={'id':task['id'],'repair_sha256':task['repair_sha256'],'records':[],
                     'status':'ADAPTER_EXCEPTION','error_type':type(exc).__name__,'error':str(exc)[:1000]}
        write(path,outcome)
        return arm,outcome['status']
    completed=0
    with ThreadPoolExecutor(max_workers=p['generation_workers']) as executor:
        # Interleave all methods deterministically; do not pick easy IDs first.
        futures=[executor.submit(job,t,arm) for t in tasks for arm in ARMS]
        for future in as_completed(futures):
            arm,status=future.result();completed+=1
            if completed%40==0:print(json.dumps({'completed_method_items':completed,'total':len(futures),'last_arm':arm,'last_status':status}),flush=True)
    write(run_dir/'generation_complete.json',{'completed_method_items':completed,'required':len(tasks)*4})


def execute(bundle,run_dir):
    p=verify_pins(bundle,run_dir)
    import structured_adapter as structured
    sys.path.insert(0,str(HELPERS))
    import execute_frozen_reference_gold as source
    import replay_generated_read_queries as guard
    from neo4j import GraphDatabase
    tasks=read(run_dir/'public_tasks.jsonl')
    for wg in ['RAN1','RAN2','RAN3','RAN4','RAN5']:
        selected=[t for t in tasks if t['wg']==wg]
        container='kdd-db-frozen-v1-'+wg.lower()
        inspect=json.loads(subprocess.check_output(['docker','inspect',container]))[0]
        if inspect['State']['Running']:raise ValueError('expected idle owned archival container')
        subprocess.run(['docker','start',container],check=True,stdout=subprocess.DEVNULL)
        try:
            for _ in range(60):
                try:
                    with GraphDatabase.driver('bolt://127.0.0.1:'+str(source.PORTS[wg]),auth=None,connection_timeout=2) as driver:driver.verify_connectivity()
                    break
                except Exception:time.sleep(1)
            else:raise RuntimeError('archival database readiness failed')
            guard.owned_container_guard(wg)
            before=source.source_guard(wg)
            if before!=p['graph_sources'][wg]:raise ValueError('frozen graph source differs')
            manifest=json.loads((BASE/'relational'/(wg+'.manifest.json')).read_text())
            db=BASE/'relational'/(wg+'.sqlite')
            db_before=sha(db)
            db_stat=structured.file_identity(db)
            expected=manifest.get('sqlite_sha256',manifest.get('db_sha256',manifest.get('output_sha256')))
            if expected and db_before!=expected:raise ValueError('SQL source differs')
            receipts=[]
            def job(t,arm):
                public=dict(t);kind='graph' if arm=='A' else 'sql'
                public[kind+'_schema']=json.loads((run_dir/'schemas'/(wg+'_'+kind+'.json')).read_text())
                inp=run_dir/'arm_outputs'/ARMS[arm]/(t['id']+'.json')
                generated=json.loads(inp.read_text())
                kwargs=({'executor_directory':HELPERS,'source_guard_expected':before,
                         'source_guard_batch_verified':True} if arm=='A' else
                        {'sql_db':db,'expected_sql_sha':db_before,
                         'expected_sql_stat':db_stat,
                         'source_guard_batch_verified':True})
                outcome=structured.execute_generated(generated,public,**kwargs)
                write(run_dir/'executed'/ARMS[arm]/(t['id']+'.json'),outcome)
                return {'id':t['id'],'arm':arm,'status':outcome['status']}
            with ThreadPoolExecutor(max_workers=p['execution_workers']) as executor:
                receipts=[f.result() for f in as_completed([executor.submit(job,t,a) for t in selected for a in ['A','B']])]
            after=source.source_guard(wg)
            if after!=before or sha(db)!=db_before:raise ValueError('graph/SQL changed during method execution')
            write(run_dir/'source_guards'/(wg+'.json'),{'before':before,'after':after,'sql_sha256':db_before,'unchanged':True,'items':receipts})
            print(json.dumps({'wg_execution_complete':wg,'items':len(receipts)}),flush=True)
        finally:subprocess.run(['docker','stop','-t','10',container],check=True,stdout=subprocess.DEVNULL)
    for arm,name in ARMS.items():
        preds=[];statuses=[]
        for t in tasks:
            directory='executed' if arm in {'A','B'} else 'arm_outputs'
            o=json.loads((run_dir/directory/name/(t['id']+'.json')).read_text())
            status=o['status'].upper()
            preds.append({'id':t['id'],'repair_sha256':t['repair_sha256'],'records':o['records']})
            statuses.append({'id':t['id'],'repair_sha256':t['repair_sha256'],'status':status,'artifact':str((run_dir/directory/name/(t['id']+'.json')).relative_to(run_dir))})
        for n,rows in [('predictions.jsonl',preds),('statuses.jsonl',statuses)]:
            path=run_dir/name/n;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(''.join(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n' for r in rows))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('action',choices=['freeze','generate','execute']);a.add_argument('--bundle',type=Path,default=DEFAULT_BUNDLE);a.add_argument('--run-dir',type=Path,default=DEFAULT_RUN)
    args=a.parse_args();args.run_dir.mkdir(parents=True,exist_ok=True)
    globals()[args.action](args.bundle,args.run_dir)
