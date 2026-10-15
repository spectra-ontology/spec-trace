"""Replay three heterogeneous saved source controls and separate synthetic fixtures."""
import argparse,hashlib,json,sys,subprocess,tempfile
from decimal import Decimal
from pathlib import Path
sys.dont_write_bytecode=True
EXPECTED={'RAN1_P1_CQ2-6','RAN1_P2_CQ3-2','RAN2_P2_CQ3-1'}
def read(p):return json.loads(Path(p).read_text())
def lines(p):return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
def without_flag(v):return {k:x for k,x in v.items() if k!='diagnostic_only'}
def verify(bundle):
 bundle=Path(bundle).resolve();sys.path.insert(0,str(bundle))
 import original_scorer,share_runtime_adapter as adapter,rational_share_records as codec
 tasks={x['id']:x for x in lines(bundle/'tasks.jsonl')};golds={x['id']:x for x in lines(bundle/'reference_gold.jsonl')}
 assert set(tasks)==set(golds)==EXPECTED
 total=synthetic=0;cases=[]
 for ident,task in tasks.items():
  gold=golds[ident];root=bundle/'gate_evidence'/ident;raw=read(root/'additional_saved_controls.json')
  controls=raw['controls'] if isinstance(raw,dict) else raw
  assert len(controls)=={'RAN1_P1_CQ2-6':15,'RAN1_P2_CQ3-2':14,'RAN2_P2_CQ3-1':21}[ident]
  checked=[]
  for case in controls:
   prediction=case.get('raw_predictions',case.get('prediction'));assert prediction is not None
   diagnostic=adapter.score(task,gold['records'],prediction,original_scorer.score,diagnostic=True,order_groups=gold['order_groups'])
   validated=adapter.score(dict(task,validation_status='validated'),gold['records'],prediction,original_scorer.score,diagnostic=False,order_groups=gold['order_groups'])
   stored=case.get('diagnostic',case.get('actual_score',case.get('actual')))
   assert diagnostic==stored,(ident,case['name'],'saved diagnostic changed',diagnostic,stored)
   if 'validated' in case:assert validated==case['validated'],(ident,case['name'],'saved validated changed')
   assert without_flag(diagnostic)==without_flag(validated) and diagnostic['exact'] is case['expected_exact']
   if 'normalized_predictions' in case:assert codec.normalize_records(task,prediction)==case['normalized_predictions']
   checked.append({'name':case['name'],'pass':True,'expected_exact':case['expected_exact']});total+=1
  if ident=='RAN1_P1_CQ2-6':
   fixture=read(root/'source_free_boundary_fixture.json');assert len(fixture['full_records'])==22 and len(fixture['cases'])==6
   for c in fixture['cases']:
    assert c['source_free_synthetic'] is True and all(x['tdocNumber'].startswith('SYNTHETIC-') for x in fixture['full_records'])
    score=original_scorer.score(task,fixture['full_records'],c['prediction'],order_groups=fixture['order_groups'],diagnostic=True)
    validated=original_scorer.score(dict(task,validation_status='validated'),fixture['full_records'],c['prediction'],order_groups=fixture['order_groups'],diagnostic=False)
    assert score==c['actual_score'] and score['exact'] is c['expected_exact'] and without_flag(score)==without_flag(validated)
    synthetic+=1
  elif ident=='RAN2_P2_CQ3-1':
   assert raw['source_free_lexical_control']['pass_check'] is True
   field=task['collection']['rational_share_representation']['field']
   text='{"records":[{"'+field+'":0.100000000000000005}],"abstain":false,"complete":true}'
   parsed=codec.parse_retrieval_answer(task,text,json.loads)
   assert parsed['records'][0][field]==codec.rational(Decimal('0.100000000000000005')) and parsed['records'][0][field]!=codec.rational(Decimal('0.1'))
   synthetic+=1
  cases.append({'id':ident,'additional_actual_controls_n':len(checked),'checks':checked})
 assert total==50 and synthetic==7
 sidecar=bundle/'runtime_controls';manifest=read(sidecar/'manifest.json')
 for name,expected in manifest['files'].items():
  pin=expected.get('sha256') if isinstance(expected,dict) else expected
  rel=expected.get('file',name) if isinstance(expected,dict) else name
  assert hashlib.sha256((sidecar/rel).read_bytes()).hexdigest()==pin
 with tempfile.TemporaryDirectory(prefix='auth11-source-free-runtime-') as tmp:
  out=Path(tmp)/'receipt.json'
  run=subprocess.run([sys.executable,'-B','-S',str(sidecar/'replay_runtime.py'),'--out',str(out)],capture_output=True,text=True)
  assert run.returncode==0,run.stdout+run.stderr
  runtime=read(out);assert runtime['status'].startswith('PASS') and runtime['tests_n']>0
 return {'status':'PASS','cases':cases,'additional_saved_controls_n':total,'actual_population_control_replays_n':total,'synthetic_tie_and_source_free_runtime_controls_n':synthetic+runtime['tests_n'],'source_free_boundary_and_lexical_controls_n':synthetic,'source_free_runtime_controls_n':runtime['tests_n'],'runtime_protocol_proof':runtime,'diagnostic_and_validated_modes_equal':True,'database_queries_n':0,'API_calls_n':0,'limits':'The 50 saved source controls and seven explicit synthetic boundary/lexical controls are separate from the source-free synthetic runtime integration checks. These are development diagnostics, not independent population samples.'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',type=Path,required=True);p.add_argument('--out',type=Path);a=p.parse_args();r=verify(a.bundle)
 if a.out:assert not a.out.exists();a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(r))
