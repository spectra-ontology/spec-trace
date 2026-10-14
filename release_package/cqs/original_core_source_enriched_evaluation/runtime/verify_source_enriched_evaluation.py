#!/usr/bin/env python3
"""Offline verification of retained source-enrichment prompts and strict scores.

No API, credentials, original database, live retrieval index or Neo4j is used.
Live graph/SQL and full-text retrieval execution are retained receipts, not rerun.
"""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

METHODS=('text2cypher','text2sql','single_retrieval','iterative_retrieval')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def load(p):return json.loads(Path(p).read_text())
def read(p):return [json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()]
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def require(ok,message):
 if not ok:raise ValueError(message)

def retrieval_functions(path):
 # Select the unchanged pure prompt/parse definitions, without executing the
 # original module's repository/SQLite setup or allowing any model call.
 funcs={'canonical','structural_schema','public_contract','parse_answer'}
 constants={'QUERY_INSTRUCTION','ANSWER_INSTRUCTION'}
 tree=ast.parse(path.read_text());selected=[]
 for node in tree.body:
  if isinstance(node,ast.FunctionDef) and node.name in funcs:selected.append(node)
  elif isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in constants for t in node.targets):selected.append(node)
 env={'json':json}
 exec(compile(ast.Module(body=selected,type_ignores=[]),str(path),'exec'),env)
 require(funcs|constants<=set(env),'incomplete frozen prompt definitions')
 return env

def verify(evidence):
 e=evidence.resolve();m=load(e/'evidence_manifest.json')
 actual={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='evidence_manifest.json'}
 require(actual==set(m['files']),'evidence file set differs')
 for n,h in m['files'].items():
  p=(e/n).resolve();require(p.is_relative_to(e) and sha(p)==h,'evidence file hash differs: '+n)
 run=e/'results';b=e/'inputs/enriched_source_bundle';p=load(run/'protocol.json');task,=read(b/'tasks.jsonl');public,=read(run/'public_tasks.jsonl')
 require(p['model']=='anthropic/claude-opus-4.8' and p['provider']=='Anthropic','model/provider differs')
 require(p['generation_workers']==1 and p['budget_guard_usd']==2 and p['retry_policy']['answer_quality_retry'] is False,'operational registration differs')
 require(p['cohort_ids']==[task['id']] and public['id']==task['id'] and public['repair_sha256']==task['repair_sha256'],'cohort identity differs')
 require(public['question_en']==task['question_en'] and sha(run/'public_tasks.jsonl')==p['public_tasks_sha256'],'original question/input differs')
 require(hashlib.sha256(task['question_en'].encode()).hexdigest()==p['question_sha256'],'question byte pin differs')
 require(sha(run/'source_config.json')==p['source_config_sha256'],'source config differs')
 reg=e/'runtime/registration'
 for n,h in p['code_pins'].items():require(sha(reg/n)==h,'frozen runtime differs: '+n)
 for n,h in p['schema_pins'].items():require(sha(run/n)==h,'frozen schema differs')
 require(sha(run/'retrieval_corpus_inventory.json')==p['retrieval_inventory_sha256'],'retrieval inventory differs')
 require(sha(e/'inputs/original_register_rows.jsonl')==p['source_pins']['raw_records_path']['sha256'],'240 original source rows differ')
 require(sha(e/'inputs/retrieval_augmentation_manifest.json')==p['source_pins']['retrieval_augmentation_manifest_path']['sha256'],'source augmentation manifest differs')
 require(sha(e/'inputs/retained_proposal.jsonl')==p['source_pins']['candidate_path']['sha256'],'retained proposal differs')
 spec=importlib.util.spec_from_file_location('offline_structured',reg/'runtime/structured_adapter.py');structured=importlib.util.module_from_spec(spec);spec.loader.exec_module(structured)
 ret=retrieval_functions(reg/'runtime/retrieval_adapter.py')
 identifier=task['id'];expected_ids={identifier+'_Text2Cypher',identifier+'_Text2SQL',identifier+'_C_answer',identifier+'_D_followup',identifier+'_D_answer'}
 requests={load(f)['request_id']:load(f) for f in (run/'calls').glob('*.request.json')}
 require(set(requests)==expected_ids and len(requests)==5,'not exactly five first-call requests')
 expected={}
 for arm,kind,name in [('A','graph','Text2Cypher'),('B','sql','Text2SQL')]:
  t=dict(public);t[kind+'_schema']=load(run/'schemas'/('RAN2_'+kind+'.json'))
  expected[identifier+'_'+name]=structured.messages_for(t,arm)
 contract=ret['public_contract'](public)
 for arm in ['C','D']:
  root=run/'retrieval'/arm/identifier
  final=load(root/'final_context.json');initial=load(root/'initial_context.json')
  require(len(final['documents'])<=p['retrieval_protocol']['final_context_documents'],'retained context doc cap differs')
  if arm=='D':expected[identifier+'_D_followup']=[{'role':'system','content':ret['QUERY_INSTRUCTION']},{'role':'user','content':ret['canonical']({'question':public['question_en'],'contract':contract})+'\nSOURCE PASSAGES:\n'+'\n\n'.join(d['formatted'] for d in initial['documents'])}]
  expected[identifier+'_'+arm+'_answer']=[{'role':'system','content':ret['ANSWER_INSTRUCTION']},{'role':'user','content':ret['canonical']({'question':public['question_en'],'contract':contract})+'\nSOURCE PASSAGES:\n'+'\n\n'.join(d['formatted'] for d in final['documents'])}]
 cost=0.0;unknown=0;responses_n=0;content={}
 for rid,request in requests.items():
  payload=request['payload']
  require(payload['messages']==expected[rid],'request is not reconstructed from frozen original inputs/context: '+rid)
  require(payload['model']==p['model'] and payload['provider']=={'only':['Anthropic'],'allow_fallbacks':False,'require_parameters':True},'request model/provider differs')
  require(request['payload_sha256']==hashlib.sha256(json.dumps(payload,ensure_ascii=False).encode()).hexdigest(),'request payload bytes differ')
  require(request['authorization_header_omitted'] is True,'request retains authorization')
  files=list((run/'calls').glob(rid+'.attempt*.response.json'));require(len(files)==1,'unexpected transport attempts')
  response=load(files[0]);require(response['http_status']==200 and response['request_id']==rid,'HTTP success receipt differs')
  raw=response['response'];require(raw['model']==p['model'] and raw['provider']==p['provider'],'actual response model/provider differs')
  require(raw['choices'][0]['finish_reason']=='stop','retained output truncated/nonterminal')
  outcome=load(run/'calls'/(rid+'.outcome.json'));content[rid]=raw['choices'][0]['message']['content']
  require(outcome['content']==content[rid] and outcome['ok'] is True,'actual response content/outcome differs')
  c=raw.get('usage',{}).get('cost')
  if type(c) in (int,float):cost+=c
  else:unknown+=1
  responses_n+=1
 guard=load(run/'source_guards/RAN2.json')
 require(guard['unchanged'] is True and guard['before']==guard['after'],'retained graph source changed')
 require(guard['before']['ttl_sha256']==p['source_pins']['graph_ttl_path']['sha256'] and guard['before']['import_manifest_sha256']==p['source_pins']['graph_import_manifest_path']['sha256'],'execution/source pin mismatch')
 require(guard['sql_sha256']==p['source_pins']['sql_db_path']['sha256'],'execution/SQL pin mismatch')
 require(load(run/'generation_complete.json')=={'completed_method_items':4,'required':4},'method denominator differs')
 for method in METHODS:
  prediction,=read(run/method/'predictions.jsonl');status,=read(run/method/'statuses.jsonl');require(prediction['id']==status['id']==identifier and prediction['repair_sha256']==status['repair_sha256']==task['repair_sha256'],'method identity differs')
  outcome=load(run/status['artifact']);require(prediction['records']==outcome['records'] and status['status']==outcome['status'].upper(),'published method projection/status differs')
  if method in {'text2cypher','text2sql'}:
   tag='Text2Cypher' if method=='text2cypher' else 'Text2SQL';generated=json.loads(content[identifier+'_'+tag]);receipt=outcome['execution']
   require(generated=={'query':outcome['generated_query'],'abstain':False},'saved model query differs')
   require(outcome['query_sha256']==hashlib.sha256(outcome['generated_query'].encode()).hexdigest(),'generated query hash differs')
   require(receipt['status']=='OK' and receipt['complete'] and not receipt['truncated'] and outcome['records']==receipt['rows'],'execution output incomplete/differs')
   if method=='text2cypher':require(receipt['plan_query_type']==receipt['execution_query_type']=='r' and receipt['execution_summary_complete'] and receipt['rollback_completed'],'Cypher execution not complete ordinary read/rollback')
  else:
   arm='C' if method=='single_retrieval' else 'D';parsed=ret['parse_answer'](content[identifier+'_'+arm+'_answer'])
   derived='abstained' if parsed['abstain'] else ('ok' if parsed['complete'] else 'partial')
   require(parsed['records']==outcome['records'] and derived==outcome['status'],'retrieval answer/status parse differs')
 usage=load(e/'actual_call_usage.json');require(usage['requests_n']==5 and usage['actual_http_responses_n']==responses_n and usage['unknown_cost_responses_n']==unknown and abs(usage['known_cost_usd']-cost)<1e-12 and usage['quality_regeneration_n']==0,'actual cost/call counts differ')
 sourceproof=json.loads(subprocess.check_output([sys.executable,'-B',str(b/'verify_enriched_bundle.py'),'--bundle',str(b)],text=True))
 require(sourceproof['status']=='PASS','source/semantic/scorer bundle does not verify')
 with tempfile.TemporaryDirectory(prefix='source-enriched-offline-') as td:
  fresh=Path(td)/'results';shutil.copytree(run,fresh)
  subprocess.run([sys.executable,'-B',str(e/'runtime/analyze_predictions.py'),'--bundle',str(b),'--run-dir',str(fresh)],check=True,stdout=subprocess.DEVNULL)
  for rel in ['analysis.json',*[str(Path(method)/n) for method in METHODS for n in ['raw_scores.json','failure_gated_scores.json']]]:
   require(load(fresh/rel)==load(run/rel),'offline score replay differs: '+rel)
 return {'status':'PASS','evidence_manifest_sha256':sha(e/'evidence_manifest.json'),'files_verified':len(actual),'cohort_n':1,'method_items':4,'requests':5,'actual_HTTP200':responses_n,'known_cost_usd':cost,'unknown_cost_responses_n':unknown,'quality_regeneration_n':0,'prompt_reconstruction_n':5,'strict_scoring_replay_n':4,'source_bundle':sourceproof,'limitations':'Replays retained prompts, response parsing, typed strict metrics and source bundle; does not rerun provider, Neo4j/SQLite or full-text retrieval, does not establish base graph/text cutoff equality or all-world submission completeness, and does not merge this separate enriched snapshot with prior cohorts.'}

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--evidence',type=Path,default=Path(__file__).resolve().parent.parent);a.add_argument('--out',type=Path);args=a.parse_args();result=verify(args.evidence)
 if args.out:args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,ensure_ascii=False))
