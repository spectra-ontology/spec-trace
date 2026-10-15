#!/usr/bin/env python3
"""Spec: separately registered Source10/Source17 original-question evaluation.
Ontology: additive graph snapshots, original old facts preserved.
Cycle: KDD2027 Datasets/Benchmarks Cycle1.
배경: preserve four methods and no answer-dependent regeneration.
사용: root freezes and invokes generation/execution; child API/native zero.
LLM 호출: root-authorized OpenRouter only in generate action.

Isolated source-enrichment experiment. Freeze inputs before first generation.

Generator input is original English plus structural schema/output shape only.
The complete unfiltered authored raw-source records enter C/D solely through
the unchanged retrieval adapter. No reference query, answer list, scorer output or review enters prompts.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import fcntl
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = Path(__file__).resolve().parent
ROOT = next(p for p in BASE.parents if (p/'.git').exists())
RUNTIME = BASE/'runtime'
sys.path.insert(0, str(RUNTIME))
ARMS = {'A':'text2cypher','B':'text2sql','C':'single_retrieval','D':'iterative_retrieval'}

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False); f.write('\n')

def load(path): return json.loads(Path(path).read_text())
def read(path): return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]
def canonical(v): return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',',':'), allow_nan=False)

def public_task(t):
    allowed = {'name','type','nullable','json_schema','nested_array_semantics'}
    result = {'id':t['id'],'wg':t['id'].split('_',1)[0],'question_en':t['question_en'],'repair_sha256':t['repair_sha256'],
              'required_fields':[{k:v for k,v in f.items() if k in allowed} for f in t['required_fields']],
              'collection':{k:v for k,v in t['collection'].items() if k in
                 {'kind','value','tie_policy','within_tie_order','require_rank_order','order_keys'}},
              'cardinality_policy':{k:v for k,v in t['cardinality_policy'].items() if k in {'mode','value','tie_policy'}}}
    import structured_adapter as structured
    structured.reject_private(result)
    return result

def source_pins(config):
    pins = {}
    for name in ['candidate_path','raw_records_path','snapshot_manifest_path','graph_ttl_path',
                 'graph_import_manifest_path','sql_db_path','sql_manifest_path','graph_schema_path',
                 'sql_schema_path','retrieval_augmentation_manifest_path']:
        p = Path(config[name]).resolve(strict=True)
        pins[name] = {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
    return pins

def freeze(config_path, run_dir):
    import structured_adapter as structured
    import retrieval_adapter as retrieval
    from openrouter_client import MODEL, PROVIDER
    if (run_dir/'protocol.json').exists() or (run_dir/'calls').exists():
        raise ValueError('existing registration or calls; no overwrite')
    config = load(config_path)
    gate=config['actual_gate_pin']
    if sha(gate['path'])!=gate['sha256']: raise ValueError('Completed source gate bytes differ')
    imported=load(config['graph_import_manifest_path'])
    if imported['status']!='restored_inventory_match' or imported['source']['sha256']!=sha(config['graph_ttl_path']):
        raise ValueError('enriched import is incomplete or uses a different source')
    if imported['measured_counts']['total_nodes']!=config['expected_node_n'] or sum(imported['measured_counts']['rel_counts'].values())!=config['expected_relationship_n']:
        raise ValueError('enriched import inventory differs')
    sql_manifest=load(config['sql_manifest_path'])
    if sql_manifest['db']['sha256']!=sha(config['sql_db_path']) or sql_manifest['RDF_snapshot']['sha256']!=sha(config['graph_ttl_path']):
        raise ValueError('SQL and source graph pins differ')
    tasks=read(config['candidate_path'])
    if len(tasks)!=1 or tasks[0]['id']!=config['expected_id']: raise ValueError('Unexpected source cohort')
    task=public_task(tasks[0])
    if task['question_en']!=config['unchanged_question_en'] or task['repair_sha256']!=config['expected_repair_sha256']:
        raise ValueError('Original question or exact repair differs')
    raw=read(config['raw_records_path'])
    if len(raw)!=config['expected_raw_rows_n'] or len({r['source_row'] for r in raw})!=len(raw):
        raise ValueError('Unfiltered raw source population differs')
    if any(set(r)!={'source_row','fields','source_cell_coordinates'} for r in raw):
        raise ValueError('Only raw authored fields and coordinates allowed')
    augmentation = load(config['retrieval_augmentation_manifest_path'])
    if augmentation['raw_source_sha256']!=sha(config['raw_records_path']) or augmentation['raw_rows_n']!=config['expected_raw_rows_n']:
        raise ValueError('retrieval augmentation source mismatch')
    if config['graph_container'].startswith('kdd-db-frozen-v1-'): raise ValueError('must use separate enriched graph')
    retrieval.CORPUS_DIR = Path(config['retrieval_corpus_dir'])
    inventory = retrieval.prepare_corpus_inventory(run_dir, retrieval.CORPUS_DIR, [task['wg']])
    (run_dir/'public_tasks.jsonl').write_text(canonical(task)+'\n')
    for kind in ['graph','sql']:
        schema = load(config[kind+'_schema_path'])
        structured.reject_private(schema)
        write(run_dir/'schemas'/(task['wg']+'_'+kind+'.json'),schema)
    write(run_dir/'source_config.json',config)
    pins = source_pins(config)
    protocol = {
      'kind':'Separate source-enriched original-question four-arm comparison',
      'frozen_utc':datetime.now(timezone.utc).isoformat(), 'model':MODEL,'provider':PROVIDER,
      'provider_fallbacks':False,'model_fallbacks':False,'reasoning':{'enabled':False},
      'response_format':{'type':'json_object'},'temperature':'unsupported; omitted',
      'cohort_ids':[task['id']],'admitted_n':1,'cohort_n':1,'original_total':560,
      'question_sha256':hashlib.sha256(task['question_en'].encode()).hexdigest(),
      'repair_sha256':task['repair_sha256'],'public_tasks_sha256':sha(run_dir/'public_tasks.jsonl'),
      'source_config_sha256':sha(run_dir/'source_config.json'),'source_pins':pins,
      'code_pins':{str(p.relative_to(BASE)):sha(p) for p in [Path(__file__),*sorted(RUNTIME.glob('*.py')),BASE/'build_retrieval_snapshot.py']},
      'schema_pins':{str(p.relative_to(run_dir)):sha(p) for p in sorted((run_dir/'schemas').glob('*.json'))},
      'retrieval_inventory_sha256':sha(run_dir/'retrieval_corpus_inventory.json'),
      'retrieval_protocol':retrieval.PROTOCOL,'generation_tokens':structured.MAX_GENERATION_TOKENS,
      'generation_workers':8,'execution_workers':2,'budget_guard_usd':config['budget_guard_usd'],
      'max_planned_calls_without_transport_retry':5,
      'max_output_tokens_without_transport_retry':2*structured.MAX_GENERATION_TOKENS+2*retrieval.PROTOCOL['answer_max_tokens']+retrieval.PROTOCOL['followup_max_tokens'],
      'retry_policy':{'transport_attempts':2,'retry_only':'429,5xx or network error','identical_payload':True,'delay_seconds':2,'answer_quality_retry':False},
      'execution_limits':{'rows':structured.ROW_CAP,'bytes':structured.BYTE_CAP,'timeout_s':structured.TIMEOUT_SECONDS},
      'information_access':{'A_B':'Separate pinned additive source graph and exact graph-equivalent SQL snapshot.',
         'C_D':config['retrieval_source_disclosure'],
         'appendix_answer_list_provided':False,'gold_reference_query_review_provided':False,
         'paired_source_augmentation':config['paired_source_disclosure'],
         'whole_snapshot_graph_text_date_or_coverage_equality':'Not established; prior base text/graph cutoffs differ and retrieved context remains bounded.'},
      'existing_frozen_cohorts_modified_or_merged':False,'model_scores_in_candidate_selection':False,
      'human_expert_validation_n':0,
      'failure_scoring':'Execution failure/abstention F1=0/exact=false; all method items retained. No quality retries.',
      'new_data_snapshot':True,'not_original_frozen_graph':True}
    write(run_dir/'protocol.json',protocol)
    print(canonical({'status':'FROZEN','protocol_sha256':sha(run_dir/'protocol.json'),'planned_calls':5,'model_calls':0}),flush=True)

def verify(run_dir, *, large_sources=True):
    p = load(run_dir/'protocol.json'); config = load(run_dir/'source_config.json')
    if sha(run_dir/'source_config.json')!=p['source_config_sha256'] or sha(run_dir/'public_tasks.jsonl')!=p['public_tasks_sha256']:
        raise ValueError('frozen public input/config changed')
    for name,expected in p['code_pins'].items():
        if sha(BASE/name)!=expected: raise ValueError('frozen code changed: '+name)
    for name,expected in p['schema_pins'].items():
        if sha(run_dir/name)!=expected: raise ValueError('frozen schema changed')
    if sha(run_dir/'retrieval_corpus_inventory.json')!=p['retrieval_inventory_sha256']:
        raise ValueError('frozen text inventory changed')
    for name,pin in p['source_pins'].items():
        if not large_sources and name=='sql_db_path': continue
        if sha(pin['path'])!=pin['sha256']: raise ValueError('frozen source changed: '+name)
    return p,config

def generate(run_dir):
    p,config = verify(run_dir)
    import structured_adapter as structured
    import retrieval_adapter as retrieval
    from openrouter_client import OpenRouterCaller
    retrieval.CORPUS_DIR = Path(config['retrieval_corpus_dir'])
    sys.path.insert(0,str(ROOT/'scripts/common/common'))
    import credentials
    caller = OpenRouterCaller(run_dir,credentials.secret('OPENROUTER_API_KEY'),p['budget_guard_usd'])
    tasks = read(run_dir/'public_tasks.jsonl'); completed = 0
    def one(task,arm,name):
        path=run_dir/'arm_outputs'/name/(task['id']+'.json')
        if path.exists(): raise ValueError('Existing outcome; no quality retry')
        public=dict(task)
        try:
            if arm in {'A','B'}:
                kind='graph' if arm=='A' else 'sql'
                public[kind+'_schema']=load(run_dir/'schemas'/(task['wg']+'_'+kind+'.json'))
                outcome=structured.evaluate(public,arm,caller,run_dir)
            else: outcome=retrieval.evaluate(public,arm,caller,run_dir)
        except Exception as exc:
            outcome={'id':task['id'],'repair_sha256':task['repair_sha256'],'records':[],
                     'status':'ADAPTER_EXCEPTION','error_type':type(exc).__name__,'error':str(exc)[:1000]}
        write(path,outcome)
        return name,outcome['status']
    with ThreadPoolExecutor(max_workers=p['generation_workers']) as pool:
        futures=[pool.submit(one,t,a,n) for t in tasks for a,n in ARMS.items()]
        for future in as_completed(futures):
            name,status=future.result();completed+=1
            print(canonical({'method':name,'status':status,'completed':completed}),flush=True)
    write(run_dir/'generation_complete.json',{'completed_method_items':completed,'required':4})

def graph_guard(config):
    from neo4j import GraphDatabase, READ_ACCESS
    obj=json.loads(subprocess.check_output(['docker','inspect',config['graph_container']]))[0]
    if not obj['State']['Running']: raise ValueError('expected running owned enriched graph')
    if obj['Image']!=config['graph_image_id'] or any(obj['Config'].get('Labels',{}).get(k)!=v for k,v in config['graph_owner_labels'].items()):
        raise ValueError('owned graph image or ownership labels changed')
    host=obj['HostConfig']
    if host['NanoCpus']>1000000000 or host['Memory']>2*1024**3 or not host['Memory'] or not host['NanoCpus']:
        raise ValueError('container resource bounds absent or exceeded')
    port=str(config['graph_uri'].rsplit(':',1)[1])
    mapping=obj['NetworkSettings']['Ports'].get('7687/tcp',[])
    if not any(e['HostIp']=='127.0.0.1' and e['HostPort']==port for e in mapping):
        raise ValueError('owned graph is not loopback-bound on pinned port')
    counts={}
    with GraphDatabase.driver(config['graph_uri'],auth=None,connection_timeout=5,max_transaction_retry_time=0) as driver:
        with driver.session(database='neo4j',default_access_mode=READ_ACCESS) as session:
            for key,q in [('nodes','MATCH(n) RETURN count(n) AS n'),('relationships','MATCH()-[r]->() RETURN count(r) AS n')]:
                counts[key]=session.run(q).single()['n']
    if counts!={'nodes':config['expected_node_n'],'relationships':config['expected_relationship_n']}:
        raise ValueError('enriched graph inventory differs')
    return {'container':config['graph_container'],'uri':config['graph_uri'],
            'ttl_sha256':sha(config['graph_ttl_path']),'import_manifest_sha256':sha(config['graph_import_manifest_path']),
            'nodes':counts['nodes'],'relationships':counts['relationships']}

def run_cypher(config,query):
    from neo4j import GraphDatabase, READ_ACCESS
    import structured_adapter as structured
    import read_query_guard as guard
    start=time.monotonic(); rows=[]; columns=[]; size=0; rolled=False; complete=False; plan_type=None; execution_type=None
    status='ERROR'; error=None
    try:
        clean=guard.screen_query(query)
        with GraphDatabase.driver(config['graph_uri'],auth=None,connection_timeout=5,max_transaction_retry_time=0) as driver:
            with driver.session(database='neo4j',default_access_mode=READ_ACCESS,fetch_size=100) as session:
                tx=session.begin_transaction(timeout=structured.TIMEOUT_SECONDS)
                try:
                    plan=tx.run('EXPLAIN '+clean).consume(); guard.require_read_plan(plan); plan_type=plan.query_type
                    cur=tx.run(clean); columns=list(cur.keys()); status='OK'
                    if len(columns)!=len(set(columns)): raise ValueError('duplicate aliases')
                    for row in cur:
                        item=row.data(); n=len(canonical(item).encode())+1
                        if len(rows)==structured.ROW_CAP: status='ROW_CAP'; break
                        if size+n>structured.BYTE_CAP: status='BYTE_CAP'; break
                        rows.append(item); size+=n
                    if status=='OK':
                        summary=cur.consume(); execution_type=summary.query_type
                        if execution_type!='r' or summary.counters.contains_updates or summary.counters.contains_system_updates:
                            raise ValueError('query was not ordinary read')
                        complete=True
                finally: tx.rollback(); rolled=True
    except Exception as exc: status='ERROR'; error=type(exc).__name__
    result=structured._result(status,rows,columns,start,size,error)
    result.update(plan_query_type=plan_type,execution_query_type=execution_type,
                  execution_summary_complete=complete,rollback_completed=rolled,source_guard_batch_verified=True)
    return result

def execute_unlocked(run_dir):
    p,config = verify(run_dir)
    import structured_adapter as structured
    from neo4j import GraphDatabase
    obj=json.loads(subprocess.check_output(['docker','inspect',config['graph_container']]))[0]
    if obj['State']['Running']: raise ValueError('owned enriched graph must be idle before execution')
    subprocess.run(['docker','start',config['graph_container']],check=True,stdout=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                with GraphDatabase.driver(config['graph_uri'],auth=None,connection_timeout=2) as d: d.verify_connectivity()
                break
            except Exception: time.sleep(1)
        else: raise RuntimeError('enriched graph not ready')
        before=graph_guard(config); db_sha=sha(config['sql_db_path']); db_stat=structured.file_identity(config['sql_db_path'])
        if db_sha!=p['source_pins']['sql_db_path']['sha256']: raise ValueError('SQL source changed')
        for task in read(run_dir/'public_tasks.jsonl'):
            for arm in ['A','B']:
                name=ARMS[arm]; inp=run_dir/'arm_outputs'/name/(task['id']+'.json'); outcome=load(inp)
                if outcome['status']=='QUERY_READY':
                    if hashlib.sha256(outcome['generated_query'].encode()).hexdigest()!=outcome['query_sha256']:
                        raise ValueError('generated query bytes changed')
                    if outcome['id']!=task['id'] or outcome['repair_sha256']!=task['repair_sha256']:
                        raise ValueError('generated task identity mismatch')
                    if arm=='A':
                        receipt=run_cypher(config,outcome['generated_query']); outcome=dict(outcome)
                        outcome.update(execution=receipt,status=receipt['status'],records=receipt['rows'] if receipt['complete'] else [],abstain=not receipt['complete'])
                    else:
                        outcome=structured.execute_generated(outcome,task,sql_db=config['sql_db_path'],expected_sql_sha=db_sha,
                            source_guard_batch_verified=True,expected_sql_stat=db_stat)
                write(run_dir/'executed'/name/(task['id']+'.json'),outcome)
        after=graph_guard(config)
        if after!=before or sha(config['sql_db_path'])!=db_sha: raise ValueError('sources changed during method execution')
        write(run_dir/'source_guards'/(config['wg']+'.json'),{'before':before,'after':after,'sql_sha256':db_sha,'unchanged':True})
    finally: subprocess.run(['docker','stop','-t','10',config['graph_container']],check=True,stdout=subprocess.DEVNULL)
    assemble(run_dir)


def execute(run_dir):
    _,config=verify(run_dir)
    with Path(config['native_lock_path']).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        linux=next(int(s.split()[1])*1024 for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:'))
        windows=int(subprocess.check_output(['powershell.exe','-NoProfile','-Command','(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory'],text=True).strip())*1024
        if min(linux,windows)<26*1024**3: raise ValueError('Preserve 26-GiB host reserve')
        info=json.loads(subprocess.check_output(['docker','inspect',config['graph_container']]))[0]
        if info['Image']!=config['graph_image_id'] or any(info['Config'].get('Labels',{}).get(k)!=v for k,v in config['graph_owner_labels'].items()):
            raise ValueError('Ownership/image mismatch before any container start')
        execute_unlocked(run_dir)
        fcntl.flock(lock,fcntl.LOCK_UN)

def assemble(run_dir):
    verify(run_dir,large_sources=False)
    tasks=read(run_dir/'public_tasks.jsonl')
    for arm,name in ARMS.items():
        predictions=[]; statuses=[]
        for task in tasks:
            path=run_dir/('executed' if arm in {'A','B'} else 'arm_outputs')/name/(task['id']+'.json')
            outcome=load(path)
            predictions.append({'id':task['id'],'repair_sha256':task['repair_sha256'],'records':outcome['records']})
            statuses.append({'id':task['id'],'repair_sha256':task['repair_sha256'],'status':outcome['status'].upper(),'artifact':str(path.relative_to(run_dir))})
        for filename,rows in [('predictions.jsonl',predictions),('statuses.jsonl',statuses)]:
            target=run_dir/name/filename; target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('x') as f: f.write(''.join(canonical(v)+'\n' for v in rows))
    print(canonical({'status':'FOUR_ARM_COMPLETE','method_items':4,'new_snapshot':True}),flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser(); a.add_argument('action',choices=['freeze','verify','generate','execute','assemble']); a.add_argument('--run-dir',type=Path,required=True); a.add_argument('--source-config',type=Path)
    args=a.parse_args(); args.run_dir.mkdir(parents=True,exist_ok=True)
    if args.action=='freeze': freeze(args.source_config,args.run_dir)
    elif args.action=='verify': verify(args.run_dir); print('{"status":"PINS_PASS"}')
    else: globals()[args.action](args.run_dir)
