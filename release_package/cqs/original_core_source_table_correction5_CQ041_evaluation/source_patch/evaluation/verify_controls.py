"""Offline exact two-question source5 contract/native/SQL/control replay."""
import argparse,hashlib,json,sys
from collections import Counter
from pathlib import Path
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE))
import scorer,original_scorer,review_schema
KEYS=('id','question_en','original_query','reference_query','required_fields','collection','cardinality_policy','repair_class','original_question_preserved')
def read(p):return json.loads(Path(p).read_text())
def rows(p):return [scorer.get_kernel().loads_exact(s) for s in Path(p).read_text().splitlines() if s.strip()]
def digest(x):return hashlib.sha256(scorer.get_kernel().json_exact(x).encode()).hexdigest()
def verify(package,sql_path=None):
 p=package.resolve();m=read(p/'manifest.json')
 for f in m['files']:
  q=p/f['path'];assert q.stat().st_size==f['bytes'] and hashlib.sha256(q.read_bytes()).hexdigest()==f['sha256'],q
 criteria=read(p/'contracts/criteria.json');csha=hashlib.sha256((p/'contracts/criteria.json').read_bytes()).hexdigest()
 tasks=rows(p/'evaluation/tasks.jsonl');gold={x['id']:x for x in rows(p/'evaluation/reference_gold.jsonl')}
 native=read(p/'evidence/full_native_three_queries.json');assert native['snapshot_sha256']==m['expected_rebuilt_RDF_sha256']
 assert native['db_sha256']==m['reference_rebuilt_SQL_sha256'] and native['owned_container_stopped'] is True
 assert native['inventory_before']==native['inventory_after']==dict(nodes=165423,relationships=848238)
 complete={q['name']:q for q in native['queries']}
 cases=[];total=0
 for t in tasks:
  cq=t['id'];rp=digest({k:t[k] for k in KEYS});assert rp==t['repair_sha256']==gold[cq]['repair_sha256']
  for role in ['primary','secondary']:
   review=read(p/'contracts'/cq/(role+'_AI_review.json'))
   review_schema.check_pass(review,t['question_en'],criteria['semantic_units'],criteria_sha=csha,identity_key='repair_sha256',identity_sha=rp)
  n=complete[cq];assert n['query']==t['reference_query']
  assert n['query_sha256']==hashlib.sha256(t['reference_query'].encode()).hexdigest()
  assert n['rollback_completed'] and n['read_plan_and_execution'] and n['full_rows_available'] and n['independent_SQL_full_multiset_equal']
  nr=rows(p/'evidence'/cq/'native_full_rows.jsonl');sr=rows(p/'evidence'/cq/'independent_SQL_full_rows.jsonl')
  assert len(nr)==len(sr)==n['rows_n']
  token=lambda r:scorer.get_kernel().json_exact(r)
  assert Counter(map(token,nr))==Counter(map(token,sr))
  required=[]
  for row in nr:
   required.append({f['name']:row[f['source_column_or_expression']] for f in t['required_fields']})
  assert Counter(map(token,required))==Counter(map(token,gold[cq]['records']))
  controls=read(p/'evidence'/cq/'actual_original_controls.json')
  for c in controls:
   diagnostic=original_scorer.score(t,gold[cq]['records'],c['predicted_records'],diagnostic=True,order_groups=gold[cq]['order_groups'])
   actual=original_scorer.score(t,gold[cq]['records'],c['predicted_records'],diagnostic=False,order_groups=gold[cq]['order_groups'])
   assert diagnostic==c['actual'] and diagnostic['exact'] is c['expected_exact'],(cq,c['name'])
   assert diagnostic['diagnostic_only'] is True and actual['diagnostic_only'] is False
   assert {k:v for k,v in diagnostic.items() if k!='diagnostic_only'}=={k:v for k,v in actual.items() if k!='diagnostic_only'},(cq,c['name'])
  total+=len(controls)
  case=dict(id=cq,repair_sha256=rp,native_rows_n=len(nr),requested_roles=[f['name'] for f in t['required_fields']],controls_n=len(controls),full_native_SQL_all_returned_fields_equal=True)
  if sql_path:
   import sqlite3
   c=sqlite3.connect(sql_path.resolve().as_uri()+'?mode=ro&immutable=1',uri=True);c.execute('PRAGMA query_only=ON');c.execute('PRAGMA cache_size=-8192');c.execute('PRAGMA threads=1')
   cur=c.execute((p/'evidence'/cq/'independent_SQL.sql').read_text());actual=[dict(zip([d[0] for d in cur.description],r)) for r in cur];c.close()
   assert Counter(map(token,actual))==Counter(map(token,sr));case['actual_fresh_SQL_full_result_equal']=True
  cases.append(case)
 assert len(cases)==2 and total==34
 return dict(status='PASS_SOURCE5_TWO_EXACT_CONTRACTS_FULL_NATIVE_SQL_AND_34_CONTROLS',all_pass=True,cases=cases,controls_n=total,model_API_calls_n=0,new_native_execution_n=0,frozen447_index_or_gold_changed=False)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--package',type=Path,default=BASE.parent);a.add_argument('--sql',type=Path);x=a.parse_args();print(json.dumps(verify(x.package,x.sql),ensure_ascii=False))
