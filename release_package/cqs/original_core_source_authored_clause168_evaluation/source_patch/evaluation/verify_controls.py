"""Replay exact source168 reviews, native434 records and 24 typed tuple controls."""
from pathlib import Path
import argparse,hashlib,json,sys
sys.dont_write_bytecode=True;HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import scorer,original_scorer,review_schema
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify(p):
 m=read(p/'manifest.json')
 for f in m['files']:x=p/f['path'];assert x.stat().st_size==f['bytes'] and sha(x)==f['sha256']
 task=read(p/'evaluation/tasks.jsonl');gold=read(p/'evaluation/reference_gold.jsonl');keys=['id','question_en','original_query','reference_query','required_fields','collection','cardinality_policy','repair_class','original_question_preserved']
 rp=hashlib.sha256(scorer.get_kernel().json_exact({k:task[k] for k in keys}).encode()).hexdigest();assert rp==task['repair_sha256']==gold['repair_sha256']==m['repair_sha256']
 criteria=read(p/'contracts/criteria.json')
 for name in ['primary','secondary']:review_schema.check_pass(read(p/'contracts'/(name+'_AI_review.json')),task['question_en'],criteria['semantic_units'],criteria_sha=sha(p/'contracts/criteria.json'),identity_key='repair_sha256',identity_sha=rp)
 native=read(p/'evidence/full_native_two_queries.json');assert native['snapshot_sha256']==m['expected_rebuilt_RDF_sha256'] and native['db_sha256']==m['reference_rebuilt_SQL_sha256'] and native['owned_container_stopped']
 assert native['inventory_before']==native['inventory_after']==dict(nodes=156288,relationships=939037)
 q=next(q for q in native['queries'] if q['name']==task['id']);assert q['query']==task['reference_query'] and q['query_sha256']==hashlib.sha256(task['reference_query'].encode()).hexdigest()
 assert q['full_rows_available'] and q['rollback_completed'] and q['read_plan_and_execution'] and q['independent_SQL_full_multiset_equal'] and q['rows_n']==434
 actual=[json.loads(s) for s in (p/'evidence/native_full434_rows.jsonl').read_text().splitlines()];assert sha(p/'evidence/native_full434_rows.jsonl')==q['records_sha256'] and actual==gold['records']
 proof=read(p/'evidence/root_independent_inverse_SQL434_agreement.json');assert proof['full_native_rows_n']==434 and proof['full_multiset_equal'] and proof['SQL_immutable_hash_preserved'] and proof['native_capture_SHA256']==sha(p/'evidence/full_native_two_queries.json')
 bridge=read(p/'contracts/old_invalid_scorer_schema_and_new_identity_bridge.json');assert bridge['new_repair_sha256']==rp and proof['repair_sha256']==bridge['old_repair_sha256'] and bridge['native_query_sha256']==q['query_sha256'] and bridge['query_bytes_changed'] is False and bridge['source_snapshot_changed'] is False
 controls=read(p/'evidence/actual_three_role_controls.json');assert len(controls)==24
 for c in controls:
  result=original_scorer.score(task,gold['records'],c['predicted_records'],order_groups=[]);assert result==c['actual'] and result['exact'] is c['expected_exact'],c['name']
 return dict(status='PASS_SOURCE168_EXACT_TWO_AI_FULL434_NATIVE_SQL_AND24_TYPED_CONTROLS',repair_sha256=rp,full_required_trace_rows_n=434,controls_n=24,frozen_original_index_changed=False,remaining1996_unknown=True,model_API_calls_n=0,new_native_calls_n=0)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--package',type=Path,default=HERE.parent);x=a.parse_args();print(json.dumps(verify(x.package.resolve()),ensure_ascii=False))
