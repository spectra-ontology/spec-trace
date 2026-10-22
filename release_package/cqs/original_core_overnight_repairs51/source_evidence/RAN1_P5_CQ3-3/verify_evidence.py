"""Replay source-certified impact records, native captures and typed contracts offline."""
import hashlib,importlib.util,json,os,sqlite3,stat,sys
from pathlib import Path
sys.dont_write_bytecode=True
if sys.flags.optimize:raise SystemExit('Enabled checks required')
HERE=Path(__file__).resolve().parent
MANIFEST='28d61b8f067ada570989f1029fdfbe7f77e3b0d41596397761049f0be95ba867'
def need(ok,why):
 if not ok:raise ValueError(why)
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_bytes())
def safe(p):
 p=Path(os.path.abspath(p))
 for q in (p,*p.parents):need(not q.is_symlink(),'Symlinks forbidden')
 need(not p.exists() or stat.S_ISREG(p.stat().st_mode) or stat.S_ISDIR(p.stat().st_mode),'Regular files only')
 return p
def module(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def audit():
 stdlib=Path(os.__file__).resolve().parent
 allowed=(HERE/'retained/frozen_dependency_projection.sqlite').as_uri()+'?mode=ro&immutable=1'
 counts=dict(network_calls=0,write_attempts=0,external_read_attempts=0,unexpected_SQL_connections=0,expected_immutable_SQL_connections=0,subprocess_calls=0)
 def hook(event,args):
  if event.startswith(('socket.','http.client.','urllib.')):counts['network_calls']+=1;raise RuntimeError('Offline evidence replay')
  if event=='sqlite3.connect':
   if os.fsdecode(args[0])!=allowed:counts['unexpected_SQL_connections']+=1;raise RuntimeError('Only pinned immutable retained projection')
   counts['expected_immutable_SQL_connections']+=1
  if event in ['subprocess.Popen','os.system','os.posix_spawn','os.posix_spawnp','os.fork','os.exec']:counts['subprocess_calls']+=1;raise RuntimeError('No external execution')
  if event=='open':
   p,mode,flags=args
   if isinstance(p,int):counts['external_read_attempts']+=1;raise RuntimeError('No outside descriptors')
   if (isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_APPEND|os.O_TRUNC)):counts['write_attempts']+=1;raise RuntimeError('No writes')
   p=safe(os.fsdecode(p))
   if not(p.is_relative_to(HERE) or p.is_relative_to(stdlib)):counts['external_read_attempts']+=1;raise RuntimeError('No host-private input')
 sys.addaudithook(hook);return counts

def native(version,ident,query_path,strip_final=False):
 query=query_path.read_text();query=query.strip() if strip_final else query;digest=sha(query.encode())
 prefix=HERE/'native'/version/'ROOT_actual_native_capture_v1/reference_outputs'/ident/digest
 meta=load(prefix.with_suffix('.json'));data=prefix.with_suffix('.jsonl').read_bytes()
 need(meta['status']=='OK' and meta['id']==ident and meta['wg']=='RAN1','Native identity and status')
 need(meta['query']==query and meta['query_sha256']==digest and meta['rows_sha256']==sha(data),'Exact actual native query and rows')
 need(not meta['truncated'] and meta['full_rows_available'] and meta['rollback_completed'] and meta['execution_summary_complete'],'Full native capture and rollback')
 need(meta['plan_query_type']==meta['execution_query_type']=='r','Native read-only EXPLAIN and execution')
 rows=[json.loads(s) for s in data.splitlines() if s]
 need(len(rows)==meta['rows_retained'] and all(type(r) is list and len(r)==len(meta['columns']) for r in rows),'Full positional result shape')
 inv=load(HERE/'native'/version/'ROOT_actual_native_capture_v1/execution_RAN1.json')
 need(inv['source_before']==inv['source_after'] and inv['inventory_unchanged'],'Actual source inventory unchanged')
 outer=load(HERE/'native'/version/'ROOT_actual_guarded_persistent_cim_execute_RAN1/receipt.json')
 need(outer['status']=='PASS' and outer['child_exit']==0 and outer['owned_cleanup']['owned_stopped'] and outer['owned_cleanup']['common_lock_held'],'Owned native cleanup and guarded capture')
 return meta,[dict(zip(meta['columns'],r)) for r in rows]

def main():
 counts=audit();mp=HERE/'payload_manifest.json';need(sha(mp.read_bytes())==MANIFEST,'Manifest pin');manifest=load(mp)
 for name,pin in manifest['files'].items():
  p=safe(HERE/name);need(p.is_relative_to(HERE) and p.stat().st_size==pin['bytes'] and sha(p.read_bytes())==pin['sha256'],'Payload pin:'+name)
 # Frozen role interpreters execute before source labels are checked.
 replay_module=module('source_replay',HERE/'verify_source_replay.py');replay=replay_module.replay()
 need(replay==load(HERE/'proof/actual_source_replay_v1.json'),'Recorded complete source, frozen-role and scorer replay')
 from repair_interpreter import graph_components,sql_components,aggregate
 components,types,n=graph_components(HERE);rows=aggregate(components,types)
 smeta,native_rows=native('v2','RAN1_P5_CQ3-3',HERE/'retained/candidate.cypher')
 mmeta,native_components=native('v3','RAN1_P5_CQ3-3__full_components',HERE/'native/v3/full_component_membership.cypher',True)
 need(native_rows==rows and native_components==components,'Native, graph, SQL full requested values and all components')
 definition=load(HERE/'definition.json');need(smeta['query']==definition['reference_query'],'Original requested-query contract')
 sys.path.insert(0,str(HERE/'scoring'));typed=module('typed_values',HERE/'scoring/typed_values.py');schema=module('review_schema',HERE/'scoring/review_schema.py')
 repair=sha(typed.json_exact(definition).encode());criteria=load(HERE/'contract/criteria.json');criteria_sha=sha((HERE/'contract/criteria.json').read_bytes())
 primary=load(HERE/'contract/primary_raw.json');secondary=load(HERE/'contract/secondary_raw.json')
 for kind,raw in [('primary',primary),('secondary',secondary)]:
  review=load(HERE/'contract'/(kind+'.json'));schema.check_pass(review,definition['question_en'],criteria['semantic_units'],criteria_sha=criteria_sha,identity_key='repair_sha256',identity_sha=repair)
  need([r['finding'] for r in review['semantic_evidence']]==[r['independent_original_question_derivation' if kind=='primary' else 'independent_assessment'] for r in raw['semantic_units']],'All seven original raw unit findings remain byte-exact')
 need(primary['reviewer']!=secondary['reviewer'],'Two distinct AI semantic judgments')
 original=json.loads((HERE/'authority/original_benchmark_record.jsonl').read_text());need(original['question_en']==definition['question_en'] and original['cypher']==definition['original_query'],'Original question/query preserved')
 result=dict(status='PASS_PORTABLE_ORIGINAL_SOURCE_FROZEN_SQL_GRAPH_NATIVE_AND_UNCHANGED_SCORER',id=definition['id'],repair_sha256=repair,original_source_archives=replay['original_source_archives'],original_source_body_children=replay['original_source_body_children'],candidate_CR_n=n,selected_CR_n=replay['selected_CR_n'],source_paragraphs_n=replay['selected_paragraphs_n'],native_answer_rows=len(native_rows),native_component_records=len(native_components),all_requested_fields_and_components_equal=True,answer_rows_sha256=replay['rows_sha256'],component_records_sha256=replay['components_sha256'],scorer_controls_n=replay['scorer_controls_n'],distinct_nonblind_AI_reviews=2,human_expert_n=0,new_API_calls=0,new_native_calls=0,source_labels_or_XML_in_selection=False,no_host_audit=counts)
 print(json.dumps(result,ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
