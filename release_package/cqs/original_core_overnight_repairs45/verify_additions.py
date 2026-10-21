"""Replay the sealed TS38.133 Resolution/approved-CR trace contract and its original source proof."""
import argparse,gzip,hashlib,importlib.util,json,os,pathlib,stat,subprocess,sys
sys.dont_write_bytecode=True
if sys.flags.optimize:raise SystemExit('Enabled checks required; -O/-OO refused')
INVENTORY='2a586a945c4958a1ec48c41cad04bde99ff15aed22e1b97ae2c9b7ec82a5f4de'
SEAL='89b0a62a450ac307ded5acf903f1a639d685195f712e93b1822d2c3249ca38ae'
SOURCE_MANIFEST='4ae33b539382695888a4052689d050f2bdaebebf0616882abff71ecde94f18a6'
IDENTITY='RAN4_P3_CQ4-1'
REPAIR='22c2820652aef63282405510d7e8b8bcaf6016e2b46e9c33d7fc0bc97901ffe7'
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
 require(definition['question_en']==orig['question_en']and definition['original_query']==orig['original_query']and definition['reference_query']!=definition['original_query'],'original question and query; source-grounded status predicate')
 require(definition['required_fields']==[{'name':'resolutionId','type':'string','nullable':False,'source_column_or_expression':'r.resolutionId'},{'name':'tdocNumber','type':'string','nullable':False,'source_column_or_expression':'cr.tdocNumber'}],'two requested identities')
 require(definition['collection']=={'kind':'top_k_boundary_ties','value':10,'tie_policy':'any_subset_at_boundary','within_tie_order':'any','require_rank_order':True,'source_order_keys':[{'source_column':'r.resolutionId','direction':'desc'}]}and definition['cardinality_policy']=={'mode':'top_k','value':10,'tie_policy':'any_subset_at_boundary'},'complete top-ten boundary contract')
 require(task['validation_status']=='validated'and task['admitted']is False and type(task['model_calls'])is int and task['model_calls']==0 and type(task['expert_validation_n'])is int and task['expert_validation_n']==0 and task['human_author_review_completed']is False,'local/model/public distinction')
 require(type(task['native_rows'])is int and task['native_rows']==10 and type(task['reference_population_rows'])is int and task['reference_population_rows']==635,'limited versus complete population')
 gate=bundle/'gate_evidence'/IDENTITY;seal=load(gate/'ROOT_final_disposition.json')
 require(sha(gate/'ROOT_final_disposition.json')==SEAL and seal['decision']=='pass_local'and seal['repair_sha256']==REPAIR,'ROOT seal')
 index=load(gate/'sealed_gate_file_index.json')
 require({r['seal_key']for r in index}=={'primary_review','secondary_review','ROOT_direct_source_and_SQL_replay','actual_native_SQL_binding','ROOT_actual_portable_replay','agent_actual_portable_replay','final_packet','native_guard','ROOT_no_host_replay'},'complete sealed gate evidence')
 for item in index:
  require(sha(gate/item['local'])==item['sha256']==seal[item['seal_key']]['sha256']and(gate/item['local']).stat().st_size==item['bytes'],'sealed gate pin')
 reviews=[load(gate/(n+'.json'))for n in ['primary','secondary']]
 for r in reviews:schema.check_pass(r,definition['question_en'],load(bundle/'criteria.json')['semantic_units'],criteria_sha=CRITERIA,identity_key='repair_sha256',identity_sha=REPAIR)
 require(reviews[0]['reviewer']!=reviews[1]['reviewer'],'two distinct nonblind AI reviews')
 source=bundle/'source_evidence'/IDENTITY
 require(sha(source/'manifest.json')==SOURCE_MANIFEST==seal['portable_manifest']['sha256']and sha(source/'verify.py')==seal['portable_verifier']['sha256'],'sealed original source bundle')
 child=subprocess.run([sys.executable,'-B','-I','-S',str(source/'verify.py')],cwd=bundle,capture_output=True,text=True,timeout=180,env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'})
 require(child.returncode==0,'source replay:'+child.stderr[-3000:]);replay=json.loads(child.stdout)
 require(replay['status']=='PASS'and replay['id']==IDENTITY and replay['new_admissions']==0,'complete source replay')
 require(len(replay['cases'])==1,'one source case');case=replay['cases'][0]
 require(case['id']==IDENTITY and case['repair_sha256']==REPAIR and case['source_paths']==1766 and case['eligible_unique_pairs']==case['native_full_rows']==635 and case['native_limited_rows']==10 and case['required_fields']==2,'source and complete native dependency')
 require(case['cutoff_tie_pairs']==18 and case['valid_ten_subsets']==43758 and case['source_current_outcomes']==14 and case['source_earlier_endorsed']==4 and case['excluded_cutoff_pairs']==10,'source-certified cutoff roles')
 require(case['generic_field_controls']==10 and case['tie_role_controls_positive']==4 and case['tie_role_controls_adverse']==25 and case['native_and_SQL_different_valid_answers']is True and case['semantic_reviews']==2,'source controls and distinct valid tied answers')
 native={}
 for label,n in [('full',635),('limited',10)]:
  meta=load(source/'native'/(label+'.json'));raw=gzip.decompress(safe(source/'native'/(label+'.jsonl.gz')).read_bytes())
  arrays=[json.loads(s,object_pairs_hook=pairs)for s in raw.splitlines()if s.strip()]
  query=definition['reference_query'].removesuffix(' LIMIT 10')if label=='full'else definition['reference_query']
  require(hashlib.sha256(raw).hexdigest()==meta['rows_sha256']and meta['query']==query and meta['columns']==['r.resolutionId','cr.tdocNumber']and len(arrays)==n,'complete native two-field rows')
  native[label]=[dict(zip(meta['columns'],r))for r in arrays]
 full=native['full'];records=[{'resolutionId':r['r.resolutionId'],'tdocNumber':r['cr.tdocNumber']}for r in full]
 require(len(records)==635 and exact(gold['records'])==exact(records),'FULL635 requested gold; limited10 cannot replace population')
 groups=scorer.make_order_groups(task,full,records)
 require(len(groups[0])==18 and exact(gold['order_groups'])==exact(groups),'actual full-native-derived order groups')
 selected=[{'resolutionId':r['r.resolutionId'],'tdocNumber':r['cr.tdocNumber']}for r in native['limited']]
 sql=[{'resolutionId':r['r.resolutionId'],'tdocNumber':r['cr.tdocNumber']}for r in load(source/'data/SQLite_selected10.json')]
 require(selected!=sql,'different permissible native and SQL tied subsets')
 for answer in [selected,sql]:require(scorer.score(task,records,answer,diagnostic=True,order_groups=groups)['exact'],'different finite ten must both score exact')
 execution=load(source/'native/execution_RAN4.json')
 require(set(d['graph_sources'])=={'RAN1','RAN2','RAN3','RAN4','RAN5'}and exact(execution['source_before'])==exact(execution['source_after'])==exact(d['graph_sources']['RAN4']),'five original graphs and actual captured RAN4 source')
 for name in ['original_scorer.py','scorer.py','typed_values.py']:require(sha(bundle/name)==sha(source/'scoring'/name),'byte-exact original scoring kernel')
 generic=checks.checks(task,records,order_groups=groups);saved=load(gate/'portable_typed_controls.json')
 require(len(generic)==13 and all(x['pass']for x in generic)and generic==saved['generic_controls'],'original generic and top-k control replay')
 require(saved['generic_field_and_collection_controls_n']==10 and saved['additional_boundary_controls_n']==3 and saved['total_controls_n']==13,'generic10 plus boundary3')
 require([x['check']for x in generic[10:]]==['duplicate_requested_record','alternative_boundary_subset','lower_rank_displaces_boundary'],'existing boundary controls')
 controls=load(source/'data/scoring_controls.json')
 require(len(controls)==29 and sum(x['expected_exact']for x in controls)==4 and sum(not x['expected_exact']for x in controls)==25,'source child29 unchanged controls')
 return {'status':'PASS','candidate_n':1,'local_validated_n':1,'new_public_admissions':0,'model_calls':0,'native_calls':0,'portable_controls_replayed':42,'items':[{'id':IDENTITY,'repair_sha256':REPAIR,'native_rows':10,'native_population_rows':635,'native_full_columns':2,'requested_fields':['resolutionId','tdocNumber'],'collection_kind':'top_k_boundary_ties','generic_typed_controls':10,'additional_boundary_controls':3,'generic_controls_total':13,'source_child_positive_controls':4,'source_child_adverse_controls':25,'distinct_valid_tied_answers_tested':2,'reference_order_groups_preserved':True,'independently_sealed_item_replay':replay}],'distinct_nonblind_AI_reviews_per_item':2,'human_expert_validation_n':0,'scope':'TS38.133 documentary Resolution references and approved CR identities; full native635 and finite10 with all18 cutoff ties; source report/register roles, exact seven-unit reviews and unchanged typed scoring.'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',type=pathlib.Path,required=True);a=p.parse_args();print(json.dumps(verify(a.bundle),ensure_ascii=False,sort_keys=True))
