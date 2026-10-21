#!/usr/bin/env python3
"""Replay the sealed AUTH35 two-question addition without models/live databases."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

sys.dont_write_bytecode=True
if sys.flags.optimize:
 raise SystemExit('Verification requires enabled checks; -O/-OO refused.')
INVENTORY_SHA256='9e3d9325aacd308ee25b46da1118711bd27ab41653202ce0e782a0aefa8341e7'
IDS=['RAN1_P3_CQ024','RAN1_P2_CQ3-4']
CRITERIA='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
REPAIRS={'RAN1_P3_CQ024':'3481219419b45416eec1c8f694b09ea7810150caf0295432c4a9bac3f359aa66','RAN1_P2_CQ3-4':'0f1f3dca03cce9b51315e9de58619ad39fbb79d9ae37ba2cf4744129c4c8d273'}
SEALS={'RAN1_P3_CQ024':'75a15946daae28a5a70b629a549666b07f0f772cfabcafcfd57df0ad2bc79f93','RAN1_P2_CQ3-4':'ac3b4fbe8c7551980d17ce0cafe6caab8fff347cf878f61bfa180d49798e7113'}
SOURCE_MANIFESTS={'RAN1_P3_CQ024':'ab40cb943d14774fa38dfede40d752e9d692b2973a31e24f618d066541331f0e','RAN1_P2_CQ3-4':'b738ede9f92d22f2f615c5cc94a1f32bdefc28cd8e0670f55e68f71d5242c318'}

def require(ok,why):
 if not ok:raise ValueError(why)
def safe(path):
 path=Path(os.path.abspath(path))
 for p in (path,*path.parents):require(not p.is_symlink(),'symlink forbidden: '+str(p))
 if path.exists():require(stat.S_ISDIR(path.lstat().st_mode)or stat.S_ISREG(path.lstat().st_mode),'nonregular entry: '+str(path))
 return path
def sha(path):return hashlib.sha256(safe(path).read_bytes()).hexdigest()
def load(path):return json.loads(safe(path).read_text())
def lines(path):return [json.loads(s)for s in safe(path).read_text().splitlines()if s.strip()]
def local(bundle,name):
 spec=importlib.util.spec_from_file_location(name,safe(bundle/(name+'.py')))
 m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def verify(bundle):
 bundle=safe(bundle)
 require(safe(__file__)==bundle/'verify_additions.py','Execute the bundle own verifier')
 require(sha(bundle/'immutable_inventory.json')==INVENTORY_SHA256,'Fixed inventory changed')
 files=load(bundle/'immutable_inventory.json')['files']
 manifest=load(bundle/'manifest.json');declarations=load(bundle/'declarations.json')
 require(manifest['files']==files and manifest['immutable_inventory_sha256']==INVENTORY_SHA256,'Manifest/inventory differ')
 actual=set()
 for p in bundle.rglob('*'):
  safe(p)
  if p.is_file():actual.add(p.relative_to(bundle).as_posix())
 require(actual==set(files)|{'manifest.json','immutable_inventory.json','verify_additions.py'},'Missing or extra file')
 for name,pin in files.items():
  p=Path(name)
  require(type(name)is str and name and not p.is_absolute()and '..'not in p.parts and '\\'not in name,'Unsafe inventory path')
  require((bundle/p).stat().st_size==pin['bytes'] and sha(bundle/p)==pin['sha256'],'Payload changed: '+name)
 require(sha(bundle/'verify_additions.py')==manifest['verifier_sha256'],'Verifier changed')
 require(set(manifest)==set(declarations)|{'files','immutable_inventory_sha256','verifier_sha256'},'Unexpected manifest declaration')
 require(all(manifest[k]==v for k,v in declarations.items()),'Scientific declaration changed')
 require(declarations['cohort_ids']==IDS and declarations['candidate_n']==2 and declarations['new_public_admissions']==declarations['new_model_calls']==declarations['human_expert_n']==0,'Cohort/accounting changed')
 require(files['criteria.json']['sha256']==CRITERIA,'Fixed seven criteria changed')
 scorer=local(bundle,'scorer');original=local(bundle,'original_scorer')
 schema=local(bundle,'review_schema');checks=local(bundle,'contract_checks')
 exact=scorer.get_kernel().json_exact
 tasks=lines(bundle/'tasks.jsonl');golds=lines(bundle/'reference_gold.jsonl');originals=lines(bundle/'provenance/original_selected_rows.jsonl')
 require([x['id']for x in tasks]==[x['id']for x in golds]==[x['id']for x in originals]==IDS,'Cohort rows changed')
 criteria=load(bundle/'criteria.json')
 cases={x['id']:x for x in declarations['cases']}
 results=[];control_n=0
 keys=['id','question_en','original_query','reference_query','required_fields','collection','cardinality_policy','repair_class','original_question_preserved']
 for task,gold,authored in zip(tasks,golds,originals):
  identity=task['id'];case=cases[identity]
  definition=load(bundle/'definitions'/(identity+'.json'))
  require(list(definition)==keys,'Canonical nine-key shape/order changed')
  repair=hashlib.sha256(exact(definition).encode()).hexdigest()
  require(repair==task['repair_sha256']==gold['repair_sha256']==case['repair_sha256']==REPAIRS[identity],'Canonical repair changed')
  require(all(exact(task[k])==exact(definition[k])for k in keys),'Task definition changed')
  require(definition['question_en']==authored['question_en'] and definition['original_query']==authored['cypher'] and definition['original_question_preserved']is True,'Original authored bytes changed')
  require(task['validation_status']=='validated' and task['admitted']is False and task['expert_validation_n']==0 and task['human_author_review_completed']is False,'Offline local/native versus public state changed')
  require(task['model_calls']==0 and task['native_execution_completed']is True,'Evaluation stages changed')
  gate=bundle/'gate_evidence'/identity
  reviews=[load(gate/(x+'.json'))for x in ['primary','secondary']]
  for review in reviews:schema.check_pass(review,definition['question_en'],criteria['semantic_units'],criteria_sha=CRITERIA,identity_key='repair_sha256',identity_sha=repair)
  require(reviews[0]['reviewer']!=reviews[1]['reviewer'],'Distinct AI reviewers required')
  seal=load(gate/'ROOT_final_disposition.json')
  require(sha(gate/'ROOT_final_disposition.json')==SEALS[identity]==case['seal_sha256'],'Exact final ROOT seal changed')
  require(seal['decision']=='pass_local' and seal['repair_sha256']==repair and seal['criteria_sha256']==CRITERIA,'ROOT exact definition seal absent')
  for sourcekey,target in [('primary_review','primary.json'),('secondary_review','secondary.json'),('final_packet','preserved_final_local_packet.json'),('actual_ROOT_source_native_SQL_binding','ROOT_native_SQL_source_binding.json'),('actual_ROOT_portable_replay','ROOT_source_portable_replay.json'),('native_guard','native_guard.json'),('actual_native_SQL_binding','primary_native_SQL_binding.json'),('actual_adverse_controls','primary_adverse_controls.json')]:
   require(sha(gate/target)==seal[sourcekey]['sha256'] and (gate/target).stat().st_size==seal[sourcekey]['bytes'],'ROOT sealed file differs: '+target)
  source=bundle/'source_evidence'/identity
  require(sha(source/'manifest.json')==SOURCE_MANIFESTS[identity]==case['source_manifest_sha256'],'Sealed source packet changed')
  child_verifier=source/case['source_verifier']
  require(sha(child_verifier)==seal['portable_verifier']['sha256'],'Source verifier changed')
  child=subprocess.run([sys.executable,'-B','-I','-S',str(child_verifier)],cwd=bundle,text=True,capture_output=True,timeout=180,
      env={'PATH':os.environ.get('PATH','/usr/bin:/bin'),'LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'})
  require(child.returncode==0,'Isolated source/native replay failed: '+child.stderr)
  replay=json.loads(child.stdout)
  metadata=load(gate/'native_metadata.json');execution=load(gate/'native_execution.json');guard=load(gate/'native_guard.json')
  require(metadata['query']==definition['reference_query'] and metadata['query_sha256']==hashlib.sha256(definition['reference_query'].encode()).hexdigest(),'Exact native query changed')
  require(metadata['status']=='OK' and metadata['plan_query_type']==metadata['execution_query_type']=='r' and metadata['rollback_completed']is True and metadata['truncated']is False and metadata['full_rows_available']is True,'Actual native read-only/complete gates')
  require(execution['inventory_unchanged']is True and execution['source_before']==execution['source_after']==manifest['graph_sources']['RAN1'],'Native source inventory differs')
  require(guard['status']=='PASS' and guard['child_exit']==0 and guard['quality_rerolls']==0 and guard['owned_cleanup']['owned_stopped']is True,'Operational guard/cleanup failed')
  raw=gate/'native_rows.jsonl'
  require(sha(raw)==metadata['rows_sha256'],'Actual native row bytes changed')
  limited=[dict(zip(metadata['columns'],row))for row in lines(raw)]
  require(len(limited)==metadata['rows_retained']==10 and len(metadata['columns'])==4,'Both native4/10 evidence required')
  required=definition['required_fields'][0]
  predicted=[{required['name']:r[required['source_column_or_expression']]}for r in limited]
  groups=gold.get('order_groups')
  if identity=='RAN1_P3_CQ024':
   require(required=={'name':'resolutionId','type':'string','nullable':False,'source_column_or_expression':'agr.resolutionId'} and definition['collection']=={'kind':'set'} and definition['cardinality_policy']=={'mode':'exact','value':10},'CQ024 exact identity-set contract changed')
   require(groups is None and predicted==gold['records'] and len(gold['records'])==10,'CQ024 gold changed')
   require(replay['status']=='PASS' and replay['repair_sha256']==repair and replay['model_calls']==replay['new_admissions']==0,'CQ024 source replay incomplete')
   rc=replay['cases'][0]
   require(rc['distinct_own_full4_rows']==322 and rc['execution']['saved_native_rows']==10 and rc['execution']['all_four_typed_native_SQL_columns_equal']is True,'CQ024 full4 SQL/native binding incomplete')
  else:
   require(required['name']=='a.resolutionId' and definition['collection']['kind']=='top_k_boundary_ties' and definition['collection']['require_rank_order']is False and definition['cardinality_policy']['mode']=='top_k' and definition['cardinality_policy']['value']==10,'CQ3-4 identity top-k contract changed')
   rankmeta=load(gate/'full_ranked_native_metadata.json')
   require(sha(gate/'full_ranked_native_rows.jsonl')==rankmeta['rows_sha256'],'Full ranked native row bytes changed')
   ranked=[dict(zip(rankmeta['columns'],row))for row in lines(gate/'full_ranked_native_rows.jsonl')]
   projected=[{'a.resolutionId':r['a.resolutionId']}for r in ranked]
   require(len(ranked)==534 and len({r['a.resolutionId']for r in ranked})==534 and projected==gold['records'] and groups==original.make_order_groups(task,ranked,projected),'Complete534 ranked identity reference changed')
   require(len(groups)==534 and all(len(g)==1 for g in groups),'Actual original boundary groups changed')
   require(replay['full534_native_and_fresh_SQL_typed_equal']is True and replay['qualified_Tdocs']==9079 and replay['original_source_records']==869 and replay['latest10_operative_role_bindings']==32,'CQ3-4 source/native dimensions changed')
   require({k:v['rows']for k,v in replay['actual_native'].items()}=={'rank':534,'full':534,'limited':10},'CQ3-4 native3 incomplete')
   audit=replay['default_no_host_audit']
   require(all(audit[k]==0 for k in ['network_calls','subprocess_calls','SQL_calls','host_private_open_attempts','write_open_attempts']),'Source replay used private/live capabilities')
   require(replay['API_calls']==replay['native_calls_performed_here']==0,'Source replay made live calls')
  require(original.score(task,gold['records'],predicted,diagnostic=True,order_groups=groups)['exact'],'Actual native10 identity answer failed')
  require(original.score(task,gold['records'],list(reversed(predicted)),diagnostic=True,order_groups=groups)['exact'],'Unrequested output order imposed')
  generic=checks.checks(task,gold['records'],groups)
  require(all(x['pass']for x in generic) and generic==load(gate/'portable_typed_controls.json')['generic_controls'],'Actual requested-field corruptions failed')
  require(len(generic)==case['generic_typed_controls'],'Generic control count changed')
  control_n+=len(generic)
  results.append({'id':identity,'repair_sha256':repair,'native_rows':10,'native_full_columns':4,'scoring_eligibility_records':len(gold['records']),'required_identity':required['name'],'collection_kind':definition['collection']['kind'],'generic_typed_controls':len(generic),'independently_sealed_item_replay':replay})
 return {'status':'PASS','candidate_n':2,'local_validated_n':2,'new_public_admissions':0,'model_calls':0,'native_calls':0,'items':results,'portable_controls_replayed':control_n,'distinct_nonblind_AI_reviews_per_item':2,'human_expert_validation_n':0,'scope':'Two fixed original questions; per-item sealed requested-identity contracts, exact full4 native/source/SQL portable replays, unchanged typed scoring.'}

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--bundle',type=Path,required=True)
 args=parser.parse_args();print(json.dumps(verify(args.bundle),ensure_ascii=False,sort_keys=True))

