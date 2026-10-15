"""Spec: AUTH12 original CQ2-2 single-question ordinary typed contract.
Ontology: recorded MODIFIES plus three AFFECTS roles; affectedSpec and CR count.
Cycle: KDD2027 Datasets and Benchmarks Cycle1.
배경: reuse actual completed gates, preserve the actual committed463 baseline.
사용: root reviews/invokes private helpers; no inferred commit or index hash.
LLM 호출: no calls from preparation, package or saved replay helpers.
Replay all thirteen saved CQ2-2 two-role controls without API or DB execution.
"""
import argparse,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
def read(p):return json.loads(p.read_text())
def lines(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def verify(bundle):
 bundle=Path(bundle).resolve();sys.path.insert(0,str(bundle));import original_scorer
 tasks=lines(bundle/'tasks.jsonl');golds=lines(bundle/'reference_gold.jsonl')
 assert len(tasks)==len(golds)==1 and tasks[0]['id']==golds[0]['id']=='RAN1_P4_CQ2-2'
 task,gold=tasks[0],golds[0];raw=read(bundle/'gate_evidence/RAN1_P4_CQ2-2/additional_saved_controls.json')
 assert isinstance(raw,list) and len(raw)==13;checked=[]
 for c in raw:
  pred=c['predictions'];d=original_scorer.score(task,gold['records'],pred,diagnostic=True,order_groups=gold['order_groups'])
  v=original_scorer.score(dict(task,validation_status='validated'),gold['records'],pred,diagnostic=False,order_groups=gold['order_groups'])
  assert d==c['diagnostic'] and v==c['validated'] and d['exact'] is c['expected_exact'],c['name']
  assert {k:x for k,x in d.items() if k!='diagnostic_only'}=={k:x for k,x in v.items() if k!='diagnostic_only'}
  checked.append({'name':c['name'],'pass':True,'expected_exact':c['expected_exact']})
 return {'status':'PASS','additional_saved_controls_n':13,'actual_population_control_replays_n':13,'checks':checked,'diagnostic_and_validated_modes_equal':True,'database_queries_n':0,'API_calls_n':0,'limits':'Thirteen deterministic saved development controls, not independent population samples or normative-source truth validation.'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',type=Path,required=True);p.add_argument('--out',type=Path);a=p.parse_args();r=verify(a.bundle)
 if a.out:assert not a.out.exists();a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(r))
