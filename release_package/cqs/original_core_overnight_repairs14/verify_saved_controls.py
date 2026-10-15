#!/usr/bin/env python3
"""Spec: exact AUTH14 canonical Meeting Agreement trend saved12 controls.
Ontology: logical Meeting identity and distinct Agreement count, two required roles.
Cycle: KDD2027 Datasets and Benchmarks Cycle1.
배경: reuse actual complete32 native/independent SQL, preserve original controls.
사용: standalone no-DB bundle replay of saved actual dual-mode controls.
LLM 호출: none; no network, native or SQL execution.
"""
import argparse,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
def read(p):return json.loads(p.read_text())
def lines(p):return [json.loads(x)for x in p.read_text().splitlines()if x.strip()]
def verify(bundle):
 b=Path(bundle).resolve();sys.path.insert(0,str(b));import original_scorer
 tasks={x['id']:x for x in lines(b/'tasks.jsonl')};golds={x['id']:x for x in lines(b/'reference_gold.jsonl')}
 ident='RAN1_P2_CQ5-6';assert set(tasks)==set(golds)=={ident};task=tasks[ident];gold=golds[ident]
 assert [f['name']for f in task['required_fields']]==['meetingNumber','agreementCount']
 assert len(gold['records'])==32 and task['collection']['kind']=='native_ordered_ties'
 saved=read(b/'gate_evidence'/ident/'additional_saved_controls.json');assert saved['id']==ident and saved['repair_sha256']==task['repair_sha256'];checks=[]
 assert len(saved['controls'])==12
 for x in saved['controls']:
  d=original_scorer.score(task,gold['records'],x['predictions'],diagnostic=True,order_groups=gold['order_groups'])
  v=original_scorer.score(dict(task,validation_status='validated'),gold['records'],x['predictions'],diagnostic=False,order_groups=gold['order_groups'])
  assert d==x['score'] and v==x['validated_score'] and d['exact']is v['exact']is x['expected_exact'],x['name']
  assert {k:y for k,y in d.items()if k!='diagnostic_only'}=={k:y for k,y in v.items()if k!='diagnostic_only'},x['name']
  checks.append({'id':ident,'name':x['name'],'pass':True,'expected_exact':x['expected_exact'],'synthetic_source_free_fixture':False})
 return {'status':'PASS','additional_saved_controls_n':12,'actual_population_control_replays_n':12,'separate_synthetic_control_replays_n':0,'per_case':{ident:{'actual_population_controls_n':12,'separate_synthetic_controls_n':0,'total_replays_n':12}},'checks':checks,'diagnostic_and_validated_modes_equal':True,'database_queries_n':0,'API_calls_n':0,'limits':'Saved deterministic development controls; nonblind AI development diagnosis, no human/expert or complete physical archive validation.'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',type=Path,required=True);p.add_argument('--out',type=Path);a=p.parse_args();r=verify(a.bundle)
 if a.out:assert not a.out.exists();a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(r))
