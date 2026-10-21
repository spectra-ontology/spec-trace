"""Bind actual original limited/full native output to typed SQL eligibility.

This reader never executes queries and never substitutes an exemplar for
native output. It requires exact captured query, raw rows and READ metadata.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import shutil
import sys

if sys.flags.optimize:
    raise RuntimeError('optimized Python is not supported')
sys.dont_write_bytecode = True
P = Path(__file__).absolute().parent
sys.path[:0] = [str(P),str(P/'canonical'),str(P/'outer_WI_metrics')]
import scorer
import original_scorer
import verify_release
import bound_partition_adapter
import partitioned_complete_record_score as metrics

def must(value, message):
    if not value:
        raise RuntimeError(message)

def pin(path):
    raw = path.read_bytes()
    return {'path':str(path.absolute()),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def dump(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--native-dir',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    must(not args.output.exists(),'preserve existing bridge')
    kernel=scorer.get_kernel()
    execution_path=args.native_dir/'execution_RAN2.json'
    execution=kernel.loads_exact(execution_path.read_text())
    must(execution['inventory_unchanged'] is True and execution['source_before']==execution['source_after'],
         'native inventory changed')
    definition=kernel.loads_exact((P/'definition.json').read_text())
    policy=kernel.loads_exact((P/'nested_eligibility_policy.json').read_text())
    sql=kernel.loads_exact((P/'full_SQL_partition_population.json').read_text())
    identity=verify_release.digest(definition)
    ids=[definition['id'],definition['id']+'__full_partition_population']
    queries=[definition['reference_query'],(P/'full_partition_population_query.cypher').read_text()]
    captured=[]
    for item_id,query in zip(ids,queries):
        query_sha=hashlib.sha256(query.encode()).hexdigest()
        meta_path=args.native_dir/'reference_outputs'/item_id/(query_sha+'.json')
        metadata=kernel.loads_exact(meta_path.read_text())
        raw_path=args.native_dir/metadata['rows_file']
        raw=raw_path.read_bytes()
        must(metadata['id']==item_id and metadata['query']==query and metadata['query_sha256']==query_sha,
             'exact query binding failed')
        must(metadata['status']=='OK' and metadata['rollback_completed'] is True
             and metadata['plan_query_type']=='r' and metadata['execution_query_type']=='r'
             and metadata['execution_summary_complete'] is True and metadata['full_rows_available'] is True
             and metadata['truncated'] is False,'native READ/full-output assertions failed')
        must(len(raw)==metadata['bytes_retained'] and hashlib.sha256(raw).hexdigest()==metadata['rows_sha256'],
             'native raw row identity')
        values=[kernel.loads_exact(line) for line in raw.decode().splitlines() if line.strip()]
        must(len(values)==metadata['rows_retained'],'native row cardinality metadata')
        rows=[dict(zip(metadata['columns'],row)) for row in values]
        must(all(len(row)==len(metadata['columns']) for row in values),'native column shape')
        capture_item=next(row for row in execution['items'] if row['id']==item_id)
        must(capture_item['status']=='OK' and capture_item['query_sha256']==query_sha
             and capture_item['rows']==len(rows),'native execution aggregate binding')
        captured.append({'metadata':metadata,'metadata_pin':pin(meta_path),'raw_pin':pin(raw_path),
            'metadata_path':meta_path,'raw_path':raw_path,'rows':rows})
    limited=verify_release.project(captured[0]['rows'],definition['required_fields'],captured[0]['metadata']['columns'])
    flat=captured[1]['rows']
    fields=[{'name':key,'type':kind,'nullable':False} for key,kind in
            [('workItemCode','string'),('company','string'),('count','integer')]]
    expected=[{'workItemCode':code,**row} for code,rows in sql.items() for row in rows]
    native_tokens,errors=kernel.project_typed(flat,fields)
    sql_tokens,sql_errors=kernel.project_typed(expected,fields,gold=True)
    must(not errors and not sql_errors and collections.Counter(native_tokens)==collections.Counter(sql_tokens),
         'full typed native/SQL population mismatch')
    must(len(limited)==5 and len(flat)==1939 and len(sql)==223,'new original population differs')
    full={}
    for row in flat:
        full.setdefault(row['workItemCode'],[]).append({'company':row['company'],'count':row['count']})
    # Canonical order-group construction requires the countDESC reference presentation.
    # This normalizes full reference rows only; no member is selected or removed,
    # and equal counts retain native encounter order (no company tie-breaker).
    full={code:sorted(rows,key=lambda row:-row['count']) for code,rows in full.items()}
    result=metrics.score(definition,policy,full,limited,scorer,original_scorer,
        verify_release,bound_partition_adapter,diagnostic=True)
    must(result['exact'] is True,'native limited output is not an eligible complete answer')
    args.output.mkdir()
    (args.output/'actual_limited_native_projected_records.jsonl').write_text(
        ''.join(kernel.json_exact(row)+'\n' for row in limited))
    dump(args.output/'actual_native_full_partition_population.json',full)
    evidence=args.output/'native_evidence';evidence.mkdir()
    shutil.copyfile(execution_path,evidence/'execution_RAN2.json')
    for index,row in enumerate(captured):
        shutil.copyfile(row['metadata_path'],evidence/('limited_metadata.json' if index==0 else 'full_metadata.json'))
        shutil.copyfile(row['raw_path'],evidence/('limited_rows.jsonl' if index==0 else 'full_rows.jsonl'))
    receipt={'status':'PASS_ACTUAL_NATIVE_TYPED_SQL_BRIDGE','id':definition['id'],'repair_sha256':identity,
        'actual_limited_native_records':len(limited),'actual_full_native_groups':len(flat),
        'full_partition_WIs':len(full),'full_typed_native_SQL_Counter_equal':True,
        'actual_limited_native_eligibility':result,'limited_native_is_full_eligibility_population':False,
        'reference_population_normalization':'Each complete WI population sorted by numeric count DESC only; equal-count native encounter order retained; raw full1939 output unchanged',
        'queries_original_unchanged':True,'source_inventory_unchanged':True,
        'READ_rollback_full_output_verified':True,'execution':pin(execution_path),
        'captures':[{key:row[key] for key in ['metadata_pin','raw_pin']} for row in captured],
        'inputs':[pin(P/'definition.json'),pin(P/'full_partition_population_query.cypher'),pin(P/'full_SQL_partition_population.json')],
        'root_guard_receipt_must_be_pinned_separately':True,'API_calls':0,'native_calls_by_this_reader':0,
        'new_public_admissions':0}
    dump(args.output/'actual_original_native_SQL_bridge.json',receipt)
    print(json.dumps({'status':receipt['status'],'limited':len(limited),'full':len(flat),
        'sha256':pin(args.output/'actual_original_native_SQL_bridge.json')['sha256']}))

if __name__=='__main__':
    main()
