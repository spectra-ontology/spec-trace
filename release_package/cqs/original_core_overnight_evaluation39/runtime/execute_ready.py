#!/usr/bin/env python3
"""Execute completed WG generations while other WG requests are in flight.

Generation, queries, source snapshots, adapter and limits remain unchanged.
Each saved execution is used once. This changes scheduling, not answer selection.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import subprocess
import sys
import time

import run_evaluation as original
import structured_adapter as adapter


def execute_wg(bundle,run_dir,wg):
    protocol=original.verify_pins(bundle,run_dir)
    sys.path.insert(0,str(original.HELPERS))
    import execute_frozen_reference_gold as source
    import replay_generated_read_queries as guard
    from neo4j import GraphDatabase
    tasks=[t for t in original.read(run_dir/'public_tasks.jsonl') if t['wg']==wg]
    names=['text2cypher','text2sql']
    if not all((run_dir/'arm_outputs'/n/(t['id']+'.json')).exists() for t in tasks for n in names):
        raise ValueError('WG generation incomplete: '+wg)
    receipt_path=run_dir/'source_guards'/(wg+'.json')
    if receipt_path.exists():
        receipt=json.loads(receipt_path.read_text())
        if receipt.get('unchanged') is not True or not all((run_dir/'executed'/n/(t['id']+'.json')).exists() for t in tasks for n in names):
            raise ValueError('Incomplete or changed prior execution batch')
        print(json.dumps({'wg':wg,'used_existing_execution':True}),flush=True);return
    name='kdd-db-frozen-v1-'+wg.lower()
    info=json.loads(subprocess.check_output(['docker','inspect',name]))[0]
    manifest=json.loads((original.HELPERS/'_frozen_ttl_v1'/wg.lower()/'import_manifest.json').read_text())
    labels=info['Config'].get('Labels') or {}
    if info['State']['Running'] or labels.get('spectra.frozen.owner')!='contract_repair_v1' or labels.get('spectra.frozen.run_uuid')!=manifest['run_uuid']:
        raise ValueError('Expected idle owned archival container')
    if info['HostConfig']['Memory']!=2*1024**3 or info['HostConfig']['NanoCpus']!=10**9:
        raise ValueError('Container budget differs from freeze')
    subprocess.run(['docker','start',name],check=True,stdout=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                with GraphDatabase.driver('bolt://127.0.0.1:'+str(source.PORTS[wg]),auth=None,connection_timeout=2) as driver:driver.verify_connectivity()
                break
            except Exception:time.sleep(1)
        else:raise RuntimeError('Database readiness failed')
        guard.owned_container_guard(wg)
        before=source.source_guard(wg)
        if before!=protocol['graph_sources'][wg]:raise ValueError('Frozen graph differs')
        db=original.BASE/'relational'/(wg+'.sqlite')
        sql_manifest=json.loads((original.BASE/'relational'/(wg+'.manifest.json')).read_text())
        db_before=original.sha(db);db_stat=adapter.file_identity(db)
        if db_before!=sql_manifest['db_sha256']:raise ValueError('Frozen SQL differs')
        def job(t,arm):
            n=original.ARMS[arm];out=run_dir/'executed'/n/(t['id']+'.json')
            if out.exists():
                result=json.loads(out.read_text())
                if result['repair_sha256']!=t['repair_sha256']:raise ValueError('Stale execution')
            else:
                public=dict(t);kind='graph' if arm=='A' else 'sql'
                public[kind+'_schema']=json.loads((run_dir/'schemas'/(wg+'_'+kind+'.json')).read_text())
                generated=json.loads((run_dir/'arm_outputs'/n/(t['id']+'.json')).read_text())
                kw={'executor_directory':original.HELPERS,'source_guard_expected':before,'source_guard_batch_verified':True} if arm=='A' else {'sql_db':db,'expected_sql_sha':db_before,'expected_sql_stat':db_stat,'source_guard_batch_verified':True}
                result=adapter.execute_generated(generated,public,**kw)
                original.write(out,result)
            return {'id':t['id'],'arm':arm,'status':result['status']}
        results=[]
        with ThreadPoolExecutor(max_workers=protocol['execution_workers']) as executor:
            futures=[executor.submit(job,t,a) for t in tasks for a in ['A','B']]
            for f in as_completed(futures):
                results.append(f.result())
                if len(results)%20==0:print(json.dumps({'wg':wg,'executions':len(results),'total':len(futures)}),flush=True)
        after=source.source_guard(wg)
        if after!=before or original.sha(db)!=db_before:raise ValueError('Sources changed during execution')
        original.write(receipt_path,{'before':before,'after':after,'sql_sha256':db_before,'unchanged':True,'items':results,'execution_schedule':'WG-ready overlap; generated queries and adapter unchanged'})
        print(json.dumps({'wg_execution_complete':wg,'items':len(results)}),flush=True)
    finally:subprocess.run(['docker','stop','-t','10',name],check=True,stdout=subprocess.DEVNULL)


def assemble(bundle,run_dir):
    original.verify_pins(bundle,run_dir)
    tasks=original.read(run_dir/'public_tasks.jsonl')
    for arm,name in original.ARMS.items():
        predictions=[];statuses=[]
        for t in tasks:
            directory='executed' if arm in {'A','B'} else 'arm_outputs'
            p=run_dir/directory/name/(t['id']+'.json')
            o=json.loads(p.read_text())
            if o['repair_sha256']!=t['repair_sha256']:raise ValueError('Repair changed')
            predictions.append({'id':t['id'],'repair_sha256':t['repair_sha256'],'records':o['records']})
            statuses.append({'id':t['id'],'repair_sha256':t['repair_sha256'],'status':o['status'].upper(),'artifact':str(p.relative_to(run_dir))})
        for n,rows in [('predictions.jsonl',predictions),('statuses.jsonl',statuses)]:
            p=run_dir/name/n;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(''.join(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n' for r in rows))
    print(json.dumps({'assembled_ids_per_method':len(tasks),'methods':4}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['wg','assemble']);p.add_argument('--wg');p.add_argument('--bundle',type=Path,default=original.DEFAULT_BUNDLE);p.add_argument('--run-dir',type=Path,default=original.DEFAULT_RUN)
    a=p.parse_args()
    if a.action=='wg':
        if a.wg not in {'RAN1','RAN2','RAN3','RAN4','RAN5'}:p.error('supported WG required')
        execute_wg(a.bundle,a.run_dir,a.wg)
    else:assemble(a.bundle,a.run_dir)
