#!/usr/bin/env python3
"""Spec: saved additional controls for the exact AUTH13 two original questions.
Ontology: history Tdoc identity and documentary NewTS TR identity.
Cycle: KDD2027 Datasets and Benchmarks Cycle1.
배경: preserve actual source-specific and separate synthetic controls.
사용: offline bundle replay; no SQL, native, network or provider execution.
LLM 호출: none.
"""
import argparse,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
def read(p):return json.loads(p.read_text())
def lines(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def verify(bundle):
 b=Path(bundle).resolve();sys.path.insert(0,str(b));import original_scorer
 tasks={x['id']:x for x in lines(b/'tasks.jsonl')};golds={x['id']:x for x in lines(b/'reference_gold.jsonl')}
 assert set(tasks)==set(golds)=={'RAN2_P1_CQ4-1','RAN4_P5_CQ2-3'};checks=[];actual_n=synthetic_n=0;per_case={}
 for ident in tasks:
  task=tasks[ident];gold=golds[ident];root=b/'gate_evidence'/ident
  if ident=='RAN2_P1_CQ4-1':
   saved=read(root/'additional_saved_controls.json');w=read(root/'saved_control_witness.json');fixture=w['synthetic_fixture'];proj=[{'tdocNumber':x['tdocNumber']} for x in fixture];groups=original_scorer.make_order_groups(task,fixture,proj);cases=[]
   for x in saved:
    syn=x['synthetic_source_free_fixture'];cases.append((x['name'],syn,proj if syn else gold['records'],groups if syn else gold['order_groups'],x['input_records'],x['expected_exact'],x['diagnostic_score'],x['validated_score']))
   expect=(14,6)
  else:
   saved=read(root/'additional_saved_controls.json');fixture=read(root/'synthetic_order_fixture.json');cases=[]
   for x in saved['controls']:cases.append((x['name'],False,gold['records'],gold['order_groups'],x['prediction'],x['expected_exact'],x['actual_score'],None))
   for x in fixture['cases']:cases.append((x['name'],True,fixture['full_records'],fixture['order_groups'],x['prediction'],x['expected_exact'],x['actual_score'],None))
   expect=(11,6)
  a_n=s_n=0
  for name,syn,records,groups,pred,expected,old_d,old_v in cases:
   d=original_scorer.score(task,records,pred,diagnostic=True,order_groups=groups);v=original_scorer.score(dict(task,validation_status='validated'),records,pred,diagnostic=False,order_groups=groups)
   assert d==old_d and (old_v is None or v==old_v) and d['exact'] is v['exact'] is expected,(ident,name)
   assert {k:x for k,x in d.items() if k!='diagnostic_only'}=={k:x for k,x in v.items() if k!='diagnostic_only'},(ident,name)
   a_n+=not syn;s_n+=syn;checks.append({'id':ident,'name':name,'synthetic_source_free_fixture':syn,'pass':True,'expected_exact':expected})
  assert (a_n,s_n)==expect;actual_n+=a_n;synthetic_n+=s_n;per_case[ident]={'actual_population_controls_n':a_n,'separate_synthetic_controls_n':s_n,'total_replays_n':a_n+s_n}
 assert (actual_n,synthetic_n,len(checks))==(25,12,37)
 return {'status':'PASS','additional_saved_controls_n':len(checks),'actual_population_control_replays_n':actual_n,'separate_synthetic_control_replays_n':synthetic_n,'per_case':per_case,'checks':checks,'diagnostic_and_validated_modes_equal':True,'database_queries_n':0,'API_calls_n':0,'limits':'Saved deterministic development controls, with synthetic source-free fixtures reported separately. No independent human/source truth evaluation.'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',type=Path,required=True);p.add_argument('--out',type=Path);a=p.parse_args();r=verify(a.bundle)
 if a.out:assert not a.out.exists();a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(r))
