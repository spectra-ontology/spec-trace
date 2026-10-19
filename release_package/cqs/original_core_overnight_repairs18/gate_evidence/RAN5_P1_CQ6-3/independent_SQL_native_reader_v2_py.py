from pathlib import Path
from datetime import datetime,timezone
import collections,hashlib,json,sqlite3,sys
R=next(p for p in Path(__file__).resolve().parents if (p/'CLAUDE.md').exists())
B=next(p for p in Path(__file__).resolve().parents if p.name=='overnight_reaudit');G=Path(__file__).resolve().parent
P=R/'logs/pending-tasks/spectracq-core-contract-2026-10-13/original_repair';sys.path.insert(0,str(P));sys.path.insert(0,'/home/sihyeon/workspace/spectra-public/spec-trace/release_package/cqs/original_core_repair')
import scorer
sys.dont_write_bytecode=True
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)
def save(p,d):
    assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def main():
    dp=B/'root_evidence/two_agent_unresolved_loop/RAN2_RAN5/loop50_CR_proportion_original_source_context_final_review/source_pinned_prospective_original_question_definition.json';d=json.loads(dp.read_text())
    qsha=hashlib.sha256(d['reference_query'].encode()).hexdigest();rp=G/'native/reference_outputs'/d['id']/(qsha+'.json');rr=rp.with_suffix('.jsonl');receipt=json.loads(rp.read_text())
    assert receipt['query']==d['reference_query'] and receipt['status']=='OK' and receipt['full_rows_available'] and not receipt['truncated'] and receipt['rollback_completed']
    assert receipt['rows_sha256']==sha(rr)
    native=[dict(zip(receipt['columns'],json.loads(l))) for l in rr.read_text().splitlines() if l.strip()]
    db=B.parent/'relational/RAN5.sqlite';mp=db.with_suffix('.manifest.json');manifest=json.loads(mp.read_text());assert sha(db)==manifest['db_sha256']
    con=sqlite3.connect(db.resolve().as_uri()+'?mode=ro&immutable=1',uri=True);con.execute('PRAGMA query_only=ON');con.row_factory=sqlite3.Row
    sql="SELECT COUNT(DISTINCT tdocNumber) AS total,COUNT(DISTINCT CASE WHEN type IN ('CR','draftCR','pCR') THEN tdocNumber END) AS crs FROM Tdoc"
    independent=[dict(r) for r in con.execute(sql)];assert all(type(v) is int for r in independent for v in r.values())
    key=lambda r:scorer.record_token(r,d['required_fields'])
    assert collections.Counter(map(key,independent))==collections.Counter(map(key,native))
    records=B/'root_evidence/independent_sql_recheck_records/RAN5_P1_CQ6-3.jsonl';assert not records.exists();records.write_text(''.join(scorer.get_kernel().json_exact(r)+'\n' for r in independent))
    before=json.loads((G/'native/execution_RAN5.json').read_text());assert before['inventory_unchanged']
    case=dict(id=d['id'],status='full_native_SQL_multiset_equal',sql=sql,parameters=[],columns=receipt['columns'],rows=len(independent),all_return_fields_compared=True,uncapped_SQL=True,independent_records=str(records.relative_to(B)),independent_records_sha256=sha(records),native_receipt=str(rp),native_receipt_sha256=sha(rp),native_rows=str(rr),native_rows_sha256=sha(rr),db=str(db),db_sha256=sha(db),relational_manifest=str(mp),relational_manifest_sha256=sha(mp),frozen_source_guard=before['source_before'],reader_pin=pin(Path(__file__)),full_record_comparison_policy='Declared integer roles, exact singleton multiset',declared_field_definitions=d['required_fields'],typed_kernel_pin=pin(Path(scorer.get_kernel().__file__)))
    result=dict(id=d['id'],independent_native_sql_fullpool_equal=True,rows=len(independent),source_sql=sql,parameters=[],root_independent_SQL_case=case,checked_utc=datetime.now(timezone.utc).isoformat(),new_model_API_calls=0,expert_validation_n=0)
    out=B/'root_evidence/RAN5_P1_CQ6-3_root_full_SQL_native_agreement.json';save(out,result);print(json.dumps(dict(status='PASS',agreement=pin(out),actual_records=independent)))
if __name__=='__main__':main()
