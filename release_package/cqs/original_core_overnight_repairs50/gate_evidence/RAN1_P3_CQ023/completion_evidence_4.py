"""Replay the original-source, retained-field, native and scorer evidence offline."""
import gzip,hashlib,importlib.util,json,os,sqlite3,stat,sys,time,xml.etree.ElementTree as E
from pathlib import Path
sys.dont_write_bytecode=True
if sys.flags.optimize:raise SystemExit('Enabled checks required')
MANIFEST='885a7bbcaeb23edf3bb6225490189577091389b3e9d472ced1f9232522abc75c'
HERE=Path(__file__).resolve().parent
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
def need(ok,why):
 if not ok:raise ValueError(why)
def safe(p):
 p=Path(os.path.abspath(p))
 for q in (p,*p.parents):need(not q.is_symlink(),'symlink forbidden')
 need(not p.exists()or stat.S_ISREG(p.stat().st_mode)or stat.S_ISDIR(p.stat().st_mode),'regular files only')
 return p
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(safe(p).read_bytes())
def gzload(name):return json.loads(gzip.decompress((HERE/'source/evidence'/(name+'.gz')).read_bytes()))
def module(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def txt(e,tabs=False):
 if e.tag in(W+'del',W+'moveFrom'):return ''
 if e.tag==W+'t':return e.text or ''
 if tabs and e.tag==W+'tab':return '\t'
 if tabs and e.tag in(W+'br',W+'cr'):return '\n'
 return ''.join(txt(c,tabs)for c in e)
def audit():
 stdlib=Path(os.__file__).resolve().parent;db=HERE/'retained/frozen_retained_dependency_projection.sqlite';allowed=db.as_uri()+'?mode=ro&immutable=1'
 counts=dict(network_calls=0,write_attempts=0,external_read_attempts=0,unexpected_SQL_connections=0,expected_immutable_SQL_connections=0,subprocess_calls=0)
 def hook(event,args):
  if event.startswith(('socket.','http.client.','urllib.')):counts['network_calls']+=1;raise RuntimeError('Offline evidence replay')
  if event=='sqlite3.connect':
   if os.fsdecode(args[0])!=allowed:counts['unexpected_SQL_connections']+=1;raise RuntimeError('Only the pinned immutable retained projection')
   counts['expected_immutable_SQL_connections']+=1
  if event in ['subprocess.Popen','os.system','os.posix_spawn','os.posix_spawnp','os.fork','os.exec']:counts['subprocess_calls']+=1;raise RuntimeError('No external execution')
  if event=='open':
   p,mode,flags=args
   if isinstance(p,int):counts['external_read_attempts']+=1;raise RuntimeError('No outside descriptors')
   if (isinstance(mode,str)and any(x in mode for x in 'wax+'))or(isinstance(flags,int)and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_APPEND|os.O_TRUNC)):counts['write_attempts']+=1;raise RuntimeError('No writes')
   target=safe(os.fsdecode(p))
   if not(target.is_relative_to(HERE)or target.is_relative_to(stdlib)):counts['external_read_attempts']+=1;raise RuntimeError('No host-private input')
 sys.addaudithook(hook);return counts

def native(ident,query):
 rawquery=query.read_bytes();digest=sha(rawquery);prefix=HERE/'native/ROOT_actual_native_capture_v1/reference_outputs'/ident/digest
 meta=load(prefix.with_suffix('.json'));raw=prefix.with_suffix('.jsonl').read_bytes()
 need(meta['status']=='OK'and meta['id']==ident and meta['wg']=='RAN1','native identity')
 need(meta['query'].encode()==rawquery and meta['query_sha256']==digest and meta['rows_sha256']==sha(raw),'native exact query and rows')
 need(not meta['truncated']and meta['full_rows_available']and meta['rollback_completed']and meta['execution_summary_complete'],'complete native capture and rollback')
 need(meta['plan_query_type']==meta['execution_query_type']=='r','native read classification')
 positional=[json.loads(s)for s in raw.splitlines()if s];need(len(positional)==meta['rows_retained'],'full native row count')
 need(all(type(r)is list and len(r)==len(meta['columns'])for r in positional),'native positional shapes')
 return meta,[dict(zip(meta['columns'],r))for r in positional]

def main():
 started=time.monotonic();counts=audit();manifestpath=HERE/'payload_manifest.json';need(sha(manifestpath.read_bytes())==MANIFEST,'manifest pin');manifest=load(manifestpath)
 for rel,info in manifest['files'].items():
  p=safe(HERE/rel);need(p.is_relative_to(HERE)and p.stat().st_size==info['bytes']and sha(p.read_bytes())==info['sha256'],'payload pin:'+rel)
 # Selection executes before source judgments or membership lists are parsed.
 module('declarative_grammar',HERE/'retained/declarative_grammar.py');lexical=module('core_sql',HERE/'retained/core_sql.py')
 projection=HERE/'retained/frozen_retained_dependency_projection.sqlite';db=sqlite3.connect(projection.as_uri()+'?mode=ro&immutable=1',uri=True);db.execute('PRAGMA query_only=ON');lexical.register_lexical(db)
 try:
  query=(HERE/'retained/independent_candidate_members.sql').read_text();cur=db.execute(query);cols=[c[0]for c in cur.description];selected=[dict(zip(cols,r))for r in cur]
  rawscope=db.execute("SELECT count(*),count(DISTINCT a.resolutionId) FROM Agreement a JOIN rel_REFERENCES r ON r.src_id=a.node_id JOIN CR c ON c.node_id=r.dst_id JOIN rel_MODIFIES m ON m.src_id=c.node_id JOIN Spec s ON s.node_id=m.dst_id WHERE s.specNumber='38.214'").fetchone()
 finally:db.close()
 definition=load(HERE/'contract/definition.json');ledger=load(HERE/'contract/primary_all407_same_direct_current_object_membership_NOT_gold.json');scope=load(HERE/'scope.json')
 source=sorted(r['resolutionId']for r in ledger['rows']if r['current_same_direct_referenced_CR_approved']);allids=[r['resolutionId']for r in ledger['rows']]
 need(len(allids)==len(set(allids))==407 and rawscope==(772,407),'whole original REFERENCES carrier/path population')
 smeta,scalar=native('RAN1_P3_CQ023',HERE/'retained/candidate_scalar.cypher');mmeta,members=native('RAN1_P3_CQ023__full_membership',HERE/'retained/candidate_members.cypher')
 need(cols==mmeta['columns']==['resolutionId']and selected==members and[r['resolutionId']for r in members]==source,'source/SQL/native complete membership')
 need(smeta['columns']==['agrCount']and scalar==[{'agrCount':len(members)}]and type(scalar[0]['agrCount'])is int,'requested native scalar')
 need(definition['reference_query']==smeta['query'],'exact contract scalar query')
 execution=load(HERE/'native/ROOT_actual_native_capture_v1/execution_RAN1.json');need(execution['source_before']==execution['source_after']and execution['inventory_unchanged'],'unchanged graph inventory')
 outer=load(HERE/'native/ROOT_actual_guarded_persistent_cim_execute_RAN1/receipt.json');need(outer['status']=='PASS'and outer['child_exit']==0and outer['owned_cleanup']['owned_stopped']and outer['owned_cleanup']['common_lock_held'],'complete owned cleanup and guarded capture')
 # Reopen the actual original source XML and every recorded Agreement interval.
 fresh=gzload('actual_original407_explicit357_negative31_fresh_source_binding_v79_NOT_gold.json');index=load(HERE/'source/XML_index.json');reportcount=0;children=0
 for item in index['report_files']:
  xml=gzip.decompress((HERE/'source/XML'/(item['stem']+'_document.xml.gz')).read_bytes());styles=gzip.decompress((HERE/'source/XML'/(item['stem']+'_styles.xml.gz')).read_bytes());need(sha(xml)==item['XML']['document_xml_sha256']and sha(styles)==item['XML']['styles_xml_sha256'],'original report XML/styles')
  body=E.fromstring(xml).find(W+'body');rows=[r for r in fresh['records']if r['original_source']['sha256']==item['original']['sha256']]
  for row in rows:
   need(row['source_XML']==item['XML'],'original report identity');lo,hi=row['original_own_interval0'];need([r['body_child0']for r in row['actual_current_own_body']]==list(range(lo,hi)),'whole own interval')
   for rec in row['actual_current_own_body']:
    e=body[rec['body_child0']];need(txt(e,True)==rec['current_text']and sha(E.tostring(e))==rec['xml_sha256'],'actual own XML/current text');children+=1
  reportcount+=1
 need(reportcount==35 and len(fresh['records'])==407,'whole original report source coverage')
 # Original current CR/selected TP objects carry current/deleted text separately.
 source72=gzload('actual_ROOT_direct_CR_objects_and_own_context_v72_NOT_gold.json');source77=gzload('actual_ROOT_2403626_selected_TP_current_object_supplement_v77_NOT_gold.json');source80=gzload('actual_historical2_and_cross_target2_original_component_review_v80_NOT_gold.json');objectcount=0;objectchildren=0
 for item in index['CR_and_selected_TP_files']:
  xml=gzip.decompress((HERE/'source/XML'/(item['stem']+'_document.xml.gz')).read_bytes());styles=gzip.decompress((HERE/'source/XML'/(item['stem']+'_styles.xml.gz')).read_bytes());need(sha(xml)==item['XML']['document_xml_sha256']and sha(styles)==item['XML']['styles_xml_sha256'],'original CR/TP XML/styles')
  body=E.fromstring(xml).find(W+'body');receipts=[]
  for row in source72['sources']:
   if row['member']['sha256']==item['member']['sha256']:receipts+=row['all_current_body_children']
  if source77['member']['sha256']==item['member']['sha256']:receipts+=source77['body_children']
  for row in source80['records']:
   if row['member']['sha256']==item['member']['sha256']:receipts+=row['original_CR_body']
  need(bool(receipts),'original object receipt')
  for rec in receipts:
   e=body[rec['body_child0']];expected=rec.get('active_text',rec.get('current_text'));need(sha(E.tostring(e))==rec['xml_sha256']and txt(e)==expected,'original current CR/TP body');objectchildren+=1
  objectcount+=1
 # The original seven unit judgments and unchanged released scorer stay distinct.
 sys.path.insert(0,str(HERE/'scoring'));typed=module('typed_values',HERE/'scoring/typed_values.py');module('scorer',HERE/'scoring/scorer.py');scorer=module('original_scorer',HERE/'scoring/original_scorer.py');checks=module('contract_checks',HERE/'scoring/contract_checks.py');schema=module('review_schema',HERE/'scoring/review_schema.py')
 repair=sha(typed.json_exact(definition).encode());criteria=load(HERE/'contract/criteria.json');criteria_sha=sha((HERE/'contract/criteria.json').read_bytes())
 for kind in ['primary','secondary']:schema.check_pass(load(HERE/'contract'/(kind+'.json')),definition['question_en'],criteria['semantic_units'],criteria_sha=criteria_sha,identity_key='repair_sha256',identity_sha=repair)
 generic=checks.checks(definition,scalar);need(all(c['pass']for c in generic),'unchanged generic typed controls')
 cases=[('exact_scalar',scalar,True),('string_count',[{'agrCount':str(len(members))}],False),('boolean_count',[{'agrCount':True}],False),('null_count',[{'agrCount':None}],False),('missing_count',[{}],False),('empty_answer',[],False),('duplicated_scalar',scalar*2,False),('wrong_aggregate',[{'agrCount':len(allids)}],False),('wrong_count',[{'agrCount':len(members)+1}],False),('unasked_context',[dict(scalar[0],context='original records')],True)]
 for name,pred,expected in cases:need(scorer.score(definition,scalar,pred,diagnostic=True)['exact']is expected,'scalar control:'+name)
 print(json.dumps(dict(status='PASS_PORTABLE_ORIGINAL_SOURCE_FROZEN_SQL_NATIVE_AND_UNCHANGED_SCORER',id=scope['id'],repair_sha256=repair,source_original_reports=reportcount,source_own_intervals=len(fresh['records']),source_own_body_children=children,source_current_objects=objectcount,source_object_body_children=objectchildren,source_positive=len(source),source_other=len(allids)-len(source),native_scalar_rows=len(scalar),native_full_members=len(members),full_ordered_membership_equal=True,generic_typed_controls=len(generic),scalar_controls=len(cases),distinct_nonblind_AI_reviews=2,human_expert_n=0,model_calls=0,new_native_calls=0,source_labels_or_XML_in_selection=False,no_host_audit=counts,elapsed_seconds=time.monotonic()-started),ensure_ascii=False))
if __name__=='__main__':main()
