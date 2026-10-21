"""Replay the sealed TS38.423 approval-provenance contract and its original source proof."""
import argparse,gzip,hashlib,importlib.util,json,os,pathlib,stat,subprocess,sys
sys.dont_write_bytecode=True
if sys.flags.optimize:raise SystemExit('Enabled checks required; -O/-OO refused')
INVENTORY='a5b4625f7abff9e65220622fbbc0c998f377a8f7dd3944bea468fdea62849811'
SEAL='8f383089d7066797c68e25d1c8ec2a1441a70bc13ee7b18fadf396c027265199'
SOURCE_MANIFEST='c1ae18469665eaf2ba571319a90ba4c746da2e73308603ef1168f3c2b08c9268'
IDENTITY='RAN3_P3_CQ4-2'
REPAIR='85cc410326169fffd4fe5394c8428c934315c6ca9b3c2980ddff144e3b8fe318'
CRITERIA='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
def require(v,s):
 if not v:raise ValueError(s)
def safe(p):
 p=pathlib.Path(os.path.abspath(p))
 for a in (p,*p.parents):require(not a.is_symlink(),'symlink forbidden')
 if p.exists():require(stat.S_ISREG(p.lstat().st_mode)or stat.S_ISDIR(p.lstat().st_mode),'nonregular member')
 return p
def sha(p):return hashlib.sha256(safe(p).read_bytes()).hexdigest()
def pairs(xs):
 d={}
 for k,v in xs:require(k not in d,'duplicate JSON key');d[k]=v
 return d
def load(p):return json.loads(safe(p).read_text(),object_pairs_hook=pairs)
def lines(p):return [json.loads(s,object_pairs_hook=pairs)for s in safe(p).read_text().splitlines()if s.strip()]
def exact(o):return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def local(p,n):
 s=importlib.util.spec_from_file_location(n,safe(p/(n+'.py')));m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def verify(bundle):
 bundle=safe(bundle);require(safe(__file__)==bundle/'verify_additions.py','execute bundle verifier')
 require(sha(bundle/'immutable_inventory.json')==INVENTORY,'inventory pin')
 files=load(bundle/'immutable_inventory.json')['files'];m=load(bundle/'manifest.json');d=load(bundle/'declarations.json')
 require(exact(m)==exact(dict(d,files=files,immutable_inventory_sha256=INVENTORY,verifier_sha256=sha(bundle/'verify_additions.py'))),'exact declarations/manifest')
 expected=set(files)|{'manifest.json','immutable_inventory.json','verify_additions.py'};dirs={a.as_posix()for n in expected for a in pathlib.Path(n).parents if a.as_posix()!='.'};actual=set()
 for p in bundle.rglob('*'):
  safe(p)
  if p.is_file():actual.add(p.relative_to(bundle).as_posix())
  else:require(p.relative_to(bundle).as_posix()in dirs,'extra directory')
 require(actual==expected,'closed inventory')
 for n,pin in files.items():
  rel=pathlib.Path(n);require(not rel.is_absolute()and'..'not in rel.parts and'\\'not in n,'unsafe member')
  require((bundle/n).stat().st_size==pin['bytes']and sha(bundle/n)==pin['sha256'],'changed payload:'+n)
 require(d['cohort_ids']==[IDENTITY]and type(d['candidate_n'])is int and d['candidate_n']==1,'one candidate')
 for k in ['new_model_calls','new_public_admissions','human_expert_n']:require(type(d[k])is int and d[k]==0,'offline zero')
 require(sha(bundle/'criteria.json')==CRITERIA,'fixed7')
 typed=local(bundle,'typed_values');local(bundle,'scorer');scorer=local(bundle,'original_scorer');checks=local(bundle,'contract_checks');schema=local(bundle,'review_schema')
 tasks,golds,originals=[lines(bundle/n)for n in ['tasks.jsonl','reference_gold.jsonl','provenance/original_selected_rows.jsonl']]
 require(len(tasks)==len(golds)==len(originals)==1,'one complete row')
 task,gold,orig=tasks[0],golds[0],originals[0];definition=load(bundle/'definitions'/(IDENTITY+'.json'))
 keys=['id','question_en','original_query','reference_query','required_fields','collection','cardinality_policy','repair_class','original_question_preserved']
 require(set(definition)==set(keys)and hashlib.sha256(typed.json_exact(definition).encode()).hexdigest()==REPAIR,'canonical9')
 require(task['id']==gold['id']==orig['id']==IDENTITY and task['repair_sha256']==gold['repair_sha256']==REPAIR,'case identity')
 require(all(exact(task[k])==exact(definition[k])for k in keys),'exact canonical task')
 require(definition['question_en']==orig['question_en']and definition['original_query']==orig['cypher']and definition['reference_query']!=definition['original_query'],'original question and query; source-grounded query repair')
 require(definition['required_fields']==[{'name':'resolutionId','type':'string','nullable':False,'source_column_or_expression':'r.resolutionId'}]and definition['collection']=={'kind':'set'}and definition['cardinality_policy']=={'mode':'exact','value':6},'six requested Resolution identities')
 require(task['validation_status']=='validated'and task['admitted']is False and task['model_calls']==task['expert_validation_n']==0 and task['human_author_review_completed']is False,'local/model/public distinction')
 gate=bundle/'gate_evidence'/IDENTITY;seal=load(gate/'ROOT_final_disposition.json')
 require(sha(gate/'ROOT_final_disposition.json')==SEAL and seal['decision']=='pass_local'and seal['repair_sha256']==REPAIR,'ROOT seal')
 for item in load(gate/'sealed_gate_file_index.json'):
  require(sha(gate/item['local'])==item['sha256']==seal[item['seal_key']]['sha256']and (gate/item['local']).stat().st_size==item['bytes'],'sealed gate evidence')
 reviews=[load(gate/(n+'.json'))for n in ['primary','secondary']]
 for r in reviews:schema.check_pass(r,definition['question_en'],load(bundle/'criteria.json')['semantic_units'],criteria_sha=CRITERIA,identity_key='repair_sha256',identity_sha=REPAIR)
 require(reviews[0]['reviewer']!=reviews[1]['reviewer'],'distinct nonblind AI reviews')
 source=bundle/'source_evidence'/IDENTITY
 require(sha(source/'manifest.json')==SOURCE_MANIFEST==seal['portable_manifest']['sha256']and sha(source/'verify.py')==seal['portable_verifier']['sha256'],'sealed source bundle')
 child=subprocess.run([sys.executable,'-B','-I','-S',str(source/'verify.py')],cwd=bundle,capture_output=True,text=True,timeout=180,env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'})
 require(child.returncode==0,'source replay:'+child.stderr[-3000:]);replay=json.loads(child.stdout)
 require(replay['status']=='PASS'and replay['id']==IDENTITY and replay['native_counts']==[125,10]and replay['original_paths']==617 and replay['source_frontier_paths']==35 and replay['source_body_contexts']==10 and replay['source_header_bindings']==267 and replay['source_approved_selected_paths']==10 and replay['requested_identity_set_n']==6 and replay['controls_n']==24 and replay['distinct_nonblind_AI_reviewers']==2 and replay['human_n']==replay['model_calls']==0,'original-source/native/24controls replay')
 require(all(replay['no_host_audit'][k]==0 for k in ['network_calls','subprocess_calls','SQL_calls','host_private_open_attempts','write_open_attempts']),'source no-host access')
 meta=load(source/'native/limited.json');raw=gzip.decompress(safe(source/'native/limited.jsonl.gz').read_bytes());arrays=[json.loads(s)for s in raw.splitlines()if s.strip()]
 require(hashlib.sha256(raw).hexdigest()==meta['rows_sha256']and meta['query']==definition['reference_query']and meta['columns']==['r.resolutionId','cr.tdocNumber']and len(arrays)==10,'actual full two-field native')
 requested=[{'resolutionId':v}for v in sorted({r[0]for r in arrays})];require(len(requested)==6 and typed.json_exact(gold['records'])==typed.json_exact(requested),'six native-derived requested records')
 execution=load(source/'native/execution_RAN3.json');require(set(d['graph_sources'])=={'RAN1','RAN2','RAN3','RAN4','RAN5'}and exact(execution['source_before'])==exact(execution['source_after'])==exact(d['graph_sources']['RAN3']),'five original graphs and captured RAN3 inventory')
 require(scorer.score(task,requested,requested,diagnostic=True)['exact'],'positive requested record score')
 generic=checks.checks(task,requested);require(len(generic)==7 and all(x['pass']for x in generic)and generic==load(gate/'portable_typed_controls.json')['generic_controls'],'seven typed controls')
 controls=load(source/'data/scoring_controls.json');require(controls['repair_sha256']==REPAIR and len(controls['requested_role_controls'])==9,'nine requested-role controls')
 require(len(controls['source_event_controls'])==8 and controls['total_controls_n']==24,'eight source event controls')
 return {'status':'PASS','candidate_n':1,'local_validated_n':1,'new_public_admissions':0,'model_calls':0,'native_calls':0,'portable_controls_replayed':16,'items':[{'id':IDENTITY,'repair_sha256':REPAIR,'native_rows':10,'native_full_columns':2,'requested_fields':['resolutionId'],'collection_kind':'set','generic_typed_controls':7,'source_child_requested_role_controls':9,'source_child_event_predicate_controls':8,'independently_sealed_item_replay':replay}],'distinct_nonblind_AI_reviews_per_item':2,'human_expert_validation_n':0,'scope':'TS38.423 same-CR approval provenance: six Resolution identities from ten selected witness paths; all35 raw selection-frontier paths,10 complete retained bodies and four original reports; native125/10,24 unchanged source/scoring controls.'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',type=pathlib.Path,required=True);a=p.parse_args();print(json.dumps(verify(a.bundle),ensure_ascii=False,sort_keys=True))

