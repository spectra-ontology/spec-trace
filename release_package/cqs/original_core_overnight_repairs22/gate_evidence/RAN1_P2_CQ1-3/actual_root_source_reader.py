"""Reopen original Conclusion source and compare the exact original native query."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sqlite3
import subprocess
import sys

sys.dont_write_bytecode = True
C = Path(__file__).resolve().parent
B = next(p for p in C.parents if p.name == 'overnight_reaudit')
ROOT = next(p for p in C.parents if (p / 'CLAUDE.md').is_file())
P = ROOT.parent / 'spectra-public/spec-trace/release_package/cqs/original_core_repair'
S = C.parent / 'RAN1_RAN3_RAN4/loop91_RAN1_Conclusion121_original15_portable_source_packet'
N = C / 'native_guard_transport_retry'
sys.path.insert(0,str(P))
import scorer
import contract_checks
import original_scorer

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()

def read(p): return json.loads(p.read_text())
def lines(p): return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def write(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f: json.dump(obj,f,ensure_ascii=False,indent=2); f.write('\n')
def rel(p): return str(p.relative_to(B))

def main():
    d = read(C/'definition.json'); k = scorer.get_kernel()
    assert d['repair_sha256'] == '02b71d66fce022602c3d30b9084aee57b12bc5495a45057b3db45bd7040277ba'
    assert sha(S/'manifest.json') == 'c873e809ab60da7d22a9ffc63b34b18812c13a577bf8bc0ed29f9719049770a4'
    source_run = subprocess.run(['python3','-B','-I',str(S/'verify_source_evidence.py'),'--source-root',str(ROOT)],capture_output=True,text=True)
    write(C/'actual_root_original_source_replay_after_projection_fix.json',{'argv':['python3','-B','-I',str(S/'verify_source_evidence.py'),'--source-root',str(ROOT)],
        'exit_code':source_run.returncode,'stdout':source_run.stdout,'stderr':source_run.stderr,
        'root_previous_direct_actual_replay_also_passed':True})
    assert source_run.returncode == 0
    source_result = json.loads(source_run.stdout)
    assert source_result['status'] == 'PASS' and source_result['source_records'] == 64 and source_result['selected_records'] == 15
    assert source_result['optional_original_replay']['frozen_SQLite_rehashed_and_all64_rows_recounted'] is True
    source_ids = lines(S/'source_selected_records.jsonl')
    dbpath = B.parent/'relational/RAN1.sqlite'
    assert sha(dbpath) == 'aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
    sql = ('SELECT c.resolutionId,c.content FROM Conclusion c JOIN rel_MADE_AT e ON e.src_id=c.node_id '
           'JOIN Meeting m ON m.node_id=e.dst_id WHERE m.meetingNumber=\'RAN1#121\' '
           'ORDER BY c.sequence,c.resolutionId LIMIT 15')
    sqlpath = C/'RAN1_P2_CQ1-3.sql'; sqlpath.write_text(sql+';\n')
    with sqlite3.connect(dbpath.as_uri()+'?mode=ro&immutable=1',uri=True) as db:
        db.execute('PRAGMA query_only=ON')
        sqlrows = [list(r) for r in db.execute(sql)]
        population = [list(r) for r in db.execute('SELECT c.resolutionId,c.sequence FROM Conclusion c JOIN rel_MADE_AT e ON e.src_id=c.node_id JOIN Meeting m ON m.node_id=e.dst_id WHERE m.meetingNumber=\'RAN1#121\' ORDER BY c.sequence,c.resolutionId')]
    assert len(population) == len({r[0] for r in population}) == 64
    frozen_operands = lines(S/'frozen/all64_query_operands.jsonl')
    assert [dict(resolutionId=r[0],sequence=r[1]) for r in population] == [{key:r[key] for key in ['resolutionId','sequence']} for r in frozen_operands]
    query_sha = hashlib.sha256(d['reference_query'].encode()).hexdigest()
    receipt_path = N/'reference_outputs'/d['id']/(query_sha+'.json')
    rows_path = receipt_path.with_suffix('.jsonl')
    receipt = read(receipt_path); native = lines(rows_path)
    assert receipt['status'] == 'OK' and receipt['query'] == d['original_query'] == d['reference_query']
    assert receipt['columns'] == ['c.resolutionId','c.content']
    assert receipt['full_rows_available'] and receipt['rollback_completed'] and receipt['execution_summary_complete']
    assert receipt['plan_query_type'] == receipt['execution_query_type'] == 'r' and not receipt['truncated']
    assert receipt['rows_retained'] == len(native) == len(sqlrows) == 15
    assert sha(rows_path) == receipt['rows_sha256']
    assert k.json_exact(native) == k.json_exact(sqlrows)
    records = [{'resolutionId':r[0]} for r in native]
    assert records == source_ids and len({r['resolutionId'] for r in records}) == 15
    checks = contract_checks.checks(d,records)
    prediction = original_scorer.reference_prediction(d,records)
    additions = [('answer_order_permutation',list(reversed(prediction)),True),
        ('missing_one_distinct_ID',prediction[:-1],False),
        ('duplicate_replaces_distinct_ID',prediction[:-1]+prediction[:1],False),
        ('extra_distinct_ID',prediction+[{'resolutionId':'__EXTRA_CONCLUSION__'}],False)]
    for name,value,expected in additions:
        scored = original_scorer.score(d,records,value,diagnostic=True)
        checks.append({'check':name,'pass':scored['exact'] is expected})
    assert len(checks) == 11 and all(r['pass'] for r in checks)
    run = read(N/'execution_RAN1.json')
    assert run['source_before'] == run['source_after'] and run['inventory_unchanged'] and run['model_calls'] == 0
    index = read(ROOT.parent/'spectra-public/spec-trace/release_package/cqs/current_core/index_manifest.json')
    assert run['source_before'] == index['source_snapshot']['RAN1']
    full = C/'independent_SQL_all_return_columns.jsonl'
    projected = C/'independent_SQL_requested_records.jsonl'
    full.write_text(''.join(k.json_exact(r)+'\n' for r in sqlrows))
    projected.write_text(''.join(k.json_exact(r)+'\n' for r in records))
    proof = C/'actual_root_source_SQL_native_and_controls.json'
    write(proof,{'status':'PASS_ACTUAL_SOURCE_SQL_NATIVE_AND_CONTROLS','checked_utc':datetime.now(timezone.utc).isoformat(),
        'id':d['id'],'repair_sha256':d['repair_sha256'],'native_rows':15,'unique_selected_IDs':15,
        'all64_join_rows_and_distinct_IDs':64,'native_SQL_all2_columns_exact_typed_agreement':True,
        'native_receipt_sha256':sha(receipt_path),'native_rows_sha256':sha(rows_path),
        'SQL':sql,'database_sha256':sha(dbpath),'source_manifest_sha256':sha(S/'manifest.json'),
        'source_replay_sha256':sha(C/'actual_root_original_source_replay_after_projection_fix.json'),
        'actual_scorer_checks':checks,'new_API_calls':0,'admitted':False,
        'limits':['Source candidate population64 and active63 have the same exact original first15.',
            'Full typed content agreement across engines does not certify authentic content rendering or complete optional prose.',
            'The named historical meeting121 is fixed; no current-latest or present-day-open status is claimed.',
            'First native attempt failed Windows interop at the second host guard before query; identical-query guarded retry preserved separately.']})
    write(C/'controls/controls.json',{'id':d['id'],'status':'controls_pass','query_sha256':query_sha,'repair_sha256':d['repair_sha256'],
        'required_fields':d['required_fields'],'native_reference_population_n':15,'permissible_answer_n':15,
        'controls':checks[:7],'pins':{str(p):sha(p) for p in [C/'definition.json',receipt_path,rows_path,N/'execution_RAN1.json',proof,C/'actual_root_original_source_replay_after_projection_fix.json',P/'contract_checks.py',P/'original_scorer.py',P/'scorer.py',P/'typed_values.py']},
        'source_guard':run['source_before'],'new_model_api_calls':0,'semantic_admission':False,'human_expert_validation_n':0})
    case = {'id':d['id'],'all_return_fields_compared':True,'uncapped_SQL':True,
        'cap_meaning':'No added execution cap beyond original LIMIT15; both original columns compared.',
        'native_receipt_sha256':sha(receipt_path),'native_rows_sha256':sha(rows_path),
        'independent_records':rel(projected),'independent_records_sha256':sha(projected),
        'independent_SQL_all_return_columns':rel(full),'independent_SQL_all_return_columns_sha256':sha(full),
        'compared_native_columns':receipt['columns'],'SQL':sql,'database_sha256':sha(dbpath),
        'sql_file':rel(sqlpath),'sql_sha256':sha(sqlpath),'rows':15}
    write(C/'native_SQL_agreement.json',{'id':d['id'],'repair_sha256':d['repair_sha256'],
        'independent_native_sql_fullpool_equal':True,'all_reference_query_return_columns_typed_equal':True,
        'root_independent_SQL_case':case,'rows':15,'new_API_calls':0})
    print(json.dumps({'status':'PASS_ROOT_CONCLUSION_SOURCE64_NATIVE15_SQL_BOTH_COLUMNS_SCORER11',
        'proof_sha256':sha(proof),'source_active':63,'new_API_calls':0}))

if __name__ == '__main__': main()
