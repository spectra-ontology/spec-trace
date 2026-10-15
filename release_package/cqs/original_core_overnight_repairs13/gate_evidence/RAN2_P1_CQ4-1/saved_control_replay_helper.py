#!/usr/bin/env python3
"""Replay saved14 actual +6 separate synthetic history controls; no DB/network."""
import argparse,hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(task_path,full_path,controls_path,witness_path,kernel_dir,out):
 assert not out.exists()
 sys.path[:0]=[str(kernel_dir)]
 import original_scorer
 task=read(task_path);assert task['id']=='RAN2_P1_CQ4-1'
 full=[json.loads(x) for x in full_path.read_text().splitlines() if x.strip()];assert len(full)==64
 proj=[{'tdocNumber':x['tdocNumber']} for x in full];groups=original_scorer.make_order_groups(task,full,proj)
 fixture=read(witness_path)['synthetic_fixture'];fproj=[{'tdocNumber':x['tdocNumber']} for x in fixture];fgroups=original_scorer.make_order_groups(task,fixture,fproj)
 controls=read(controls_path);assert len(controls)==20
 actual_n=synthetic_n=0;results=[]
 for c in controls:
  synthetic=c['synthetic_source_free_fixture'];gold,order=(fproj,fgroups) if synthetic else (proj,groups)
  a=original_scorer.score(task,gold,c['input_records'],diagnostic=True,order_groups=order)
  b=original_scorer.score(dict(task,validation_status='validated'),gold,c['input_records'],diagnostic=False,order_groups=order)
  assert a==c['diagnostic_score'] and b==c['validated_score'] and a['exact']==b['exact']==c['expected_exact'],c['name']
  assert {k:v for k,v in a.items() if k!='diagnostic_only'}=={k:v for k,v in b.items() if k!='diagnostic_only'}
  actual_n+=not synthetic;synthetic_n+=synthetic
  results.append({'name':c['name'],'synthetic':synthetic,'exact':a['exact']})
 assert actual_n==14 and synthetic_n==6
 receipt={'status':'PASS_SAVED14_ACTUAL_PLUS_SEPARATE6_SYNTHETIC_CONTROLS_NO_DB','id':task['id'],'repair_sha256':task['repair_sha256'],'full_reference_records_n':64,'actual_controls_n':actual_n,'synthetic_controls_n':synthetic_n,'diagnostic_and_validated_modes_equal':True,'inputs':{str(p):sha(p) for p in [task_path,full_path,controls_path,witness_path]},'kernel_pins':{p.name:sha(p) for p in kernel_dir.iterdir() if p.is_file() and p.name in ['original_scorer.py','scorer.py','typed_values.py','source_pins.json','contract_checks.py']},'results':results,'database_model_network_calls':0}
 out.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['task','full','controls','witness','kernel-dir','out']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();main(a.task,a.full,a.controls,a.witness,a.kernel_dir,a.out)
