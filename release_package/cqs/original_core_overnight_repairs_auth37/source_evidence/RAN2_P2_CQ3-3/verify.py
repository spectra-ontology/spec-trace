"""Offline fixed-inventory source and declared partitioned-production replay."""
import sys
if sys.flags.optimize:
    raise RuntimeError('Optimized Python is not supported')
sys.dont_write_bytecode=True
import os
from pathlib import Path
ENTRY=Path(os.path.abspath(__file__))
for part in [ENTRY,*ENTRY.parents]:
    if part.is_symlink():raise ValueError('Symlink entry or ancestor is forbidden before metadata reads')
ROOT=ENTRY.parent
import argparse,collections,gzip,hashlib,importlib.util,json,math,sqlite3,stat
INVENTORY_SHA='cfb3ebd64b294b2b790b5ed8db3cca1e7224de80e943f307dfae22c4e383a865'
REPAIR='bdf997f06492063fce39de80bca72378d557151ff81f0b1df846c9a9ec0e9a07'
CRITERIA_SHA='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
IDENTITY='RAN2_P2_CQ3-3'
def need(test,message):
    if not test:raise ValueError(message)
def regular(path):
    for part in [path,*path.parents]:
        need(not part.is_symlink(),'Symlink input or ancestor')
    need(stat.S_ISREG(path.stat().st_mode),'Nonregular input')
    return path
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def exact(value):return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)
def pairs(entries):
    out={}
    for key,value in entries:
        need(key not in out,'Duplicate JSON key');out[key]=value
    return out
def loads(raw):return json.loads(raw,object_pairs_hook=pairs)
def load(path):return loads(regular(path).read_text())
SCOPED={'original560_pass_increment':0,'new_public_admissions':0,'API_calls':0,'human_expert_n':0,
 'nonblind_AI':True,'scope':'Original authored recorded literal REFERENCES contribution per WI; count distinct Resolution. Source-replayed complete first-five dependency; no causal leadership or approval inference.',
 'whole_host_graph_default_replayed':False,'limited_native_records':5,'native_eligibility_groups':1939,
 'lawful_nested_answers':5,'source_raw_full_contents':12,'source_Tdoc_roles':294,
 'source_all3773_raw_body_claimed':False,'historical_generator_binding_claimed':False,
 'canonical_scientific_modules_modified':False,'validated_task_envelope_is_local_control_fixture':True}
manifest=load(ROOT/'manifest.json')
need(set(manifest)=={'status','id','repair_sha256','criteria_sha256','scope_and_provenance','inventory','verifier_sha256','source_selected_records','dispatch'},'Manifest key set differs')
need(type(manifest['scope_and_provenance']) is dict and exact(manifest['scope_and_provenance'])==exact(SCOPED),'Scientific scope declarations differ')
need(manifest['status']=='local_portable_proposal' and manifest['id']==IDENTITY and manifest['repair_sha256']==REPAIR and manifest['criteria_sha256']==CRITERIA_SHA,'Manifest identity differs')
need(manifest['verifier_sha256']==sha(ENTRY.read_bytes()),'Running verifier differs')
need(manifest['inventory']=={'path':'immutable_inventory.json','sha256':INVENTORY_SHA},'Inventory pin differs')
invpath=regular(ROOT/'immutable_inventory.json');need(sha(invpath.read_bytes())==INVENTORY_SHA,'Fixed inventory bytes differ')
inventory=load(invpath)
expected=set(inventory['files'])|{'verify.py','manifest.json','immutable_inventory.json'}
observed=set()
for p in ROOT.rglob('*'):
    mode=p.lstat().st_mode
    need(not stat.S_ISLNK(mode),'Symlink in package tree')
    if stat.S_ISREG(mode):observed.add(str(p.relative_to(ROOT)))
    else:need(stat.S_ISDIR(mode),'Nonregular package entry')
need(observed==expected,'Closed file inventory differs')
for rel,entry in inventory['files'].items():
    q=Path(rel);need(not q.is_absolute() and '..' not in q.parts,'Nonrelative inventory path')
    raw=regular(ROOT/q).read_bytes()
    need(type(entry['bytes']) is int and type(entry['sha256']) is str and entry['bytes']==len(raw) and entry['sha256']==sha(raw),'Payload bytes differ: '+rel)
sys.path[:0]=[str(ROOT),str(ROOT/'canonical'),str(ROOT/'outer_WI_metrics')]
import scorer,original_scorer,verify_release,review_schema,bound_partition_adapter
import score_predictions_partitioned_dispatch as dispatcher
kernel=scorer.get_kernel()
definition=load(ROOT/'definition.json');criteria=load(ROOT/'criteria.json');original=load(ROOT/'original.json')
need(set(definition)==set(verify_release.DEFINITION_KEYS) and verify_release.digest(definition)==REPAIR,'Exact nine-key repair differs')
need(sha((ROOT/'criteria.json').read_bytes())==CRITERIA_SHA,'Criteria bytes differ')
need(definition['question_en']==original['question_en'] and definition['original_query']==original['cypher'] and definition['reference_query']==original['cypher'],'Original question/query differs')
reviews=[load(ROOT/name) for name in ['primary_exact_seven_unit_review.json','ROOT_secondary_exact_seven_unit_review_v1.json']]
for review in reviews:
    review_schema.check_pass(review,definition['question_en'],criteria['semantic_units'],criteria_sha=CRITERIA_SHA,identity_key='repair_sha256',identity_sha=REPAIR)
need(reviews[0]['reviewer_identity']!=reviews[1]['reviewer_identity'],'Two distinct reviewers required')
# Execute included raw XML/register/retained-reference replay only after fixed tree validation.
spec=importlib.util.spec_from_file_location('included_original_frontier',ROOT/'replay_included_original_frontier.py')
source_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(source_module)
source=source_module.replay(ROOT/'source_inputs')
need(source['full_source_contents']==12 and source['original_Tdoc_roles']==294 and source['source_role_failures']==0,'Complete selected source dependency failed')
fixture=loads(gzip.decompress((ROOT/'source_inputs/data/retained_resolution_and_path_projection.json.gz').read_bytes()))
groups=collections.defaultdict(set)
for row in fixture['paths']:groups[row['workItemCode'],row['companyName']].add(row['rn'])
flatSQL=[{'workItemCode':code,'company':company,'count':len(res)} for (code,company),res in groups.items()]
need(len(flatSQL)==1939 and len({r['workItemCode'] for r in flatSQL})==223,'Original recorded full population differs')
# Validate actual guarded capture, raw two-query output and limited/full separation.
execution=load(ROOT/'native/execution_RAN2.json')
need(execution['source_before']==execution['source_after'] and execution['inventory_unchanged'] is True,'Native inventory changed')
need(execution['source_before']['nodes']==156288 and execution['source_before']['relationships']==939037,'Native source shape differs')
need(execution['input_sha256']==sha((ROOT/'native_input_development_probe.jsonl').read_bytes()),'Native input bytes differ')
outer=load(ROOT/'native_guard/outer_receipt.json')
need(outer['status']=='PASS' and outer['child_exit']==0 and outer['failure'] is None,'Native outer guard failed')
need(outer['owned_cleanup']['owned_stopped'] is True and outer['owned_cleanup']['common_lock_held'] is True,'Owned cleanup/lock failed')
need(type(outer['prestart_available_minimum_bytes']) is int and outer['prestart_available_minimum_bytes']==26*1024**3 and outer['continuous_reserve_minimum_bytes']==16*1024**3,'Memory guard policy differs')
need(outer['scope_sha256']==sha((ROOT/'definition.json').read_bytes()) and outer['wrapper_sha256']==sha((ROOT/'native_guard/ROOT_outer_native_reserve_guard.py').read_bytes()),'Guard scientific input/wrapper pin differs')
coordinator=load(ROOT/'native_guard/coordinator_receipt.json')
need(coordinator['child_exit']==0 and coordinator['status']=='NATIVE_WRAPPER_PASS_PENDING_SCIENTIFIC_BINDING','Coordinator did not succeed')
native={}
for identity,query in [(IDENTITY,definition['reference_query']),(IDENTITY+'__full_partition_population',(ROOT/'full_partition_population_query.cypher').read_text())]:
    digest=sha(query.encode());base=ROOT/'native/reference_outputs'/identity
    meta=load(base/(digest+'.json'));rowpath=Path(meta['rows_file'])
    need(not rowpath.is_absolute() and '..' not in rowpath.parts,'Native row path escapes capture')
    raw=regular(ROOT/'native'/rowpath).read_bytes()
    need(meta['id']==identity and meta['query']==query and meta['query_sha256']==digest,'Native exact query differs')
    need(meta['status']=='OK' and meta['truncated'] is False and all(meta[k] is True for k in ['rollback_completed','execution_summary_complete','full_rows_available']),'Native output incomplete')
    need(meta['plan_query_type']==meta['execution_query_type']=='r','Native query was not READ')
    need(meta['rows_sha256']==sha(raw) and meta['bytes_retained']==len(raw),'Native raw bytes differ')
    rows=[kernel.loads_exact(s) for s in raw.decode().splitlines() if s.strip()]
    need(len(rows)==meta['rows_retained'] and len(set(meta['columns']))==len(meta['columns']),'Native columns/row count differ')
    need(all(type(row) is list and len(row)==len(meta['columns']) for row in rows),'Native row shape differs')
    aggregate=[item for item in execution['items'] if item['id']==identity]
    need(len(aggregate)==1 and aggregate[0]['status']=='OK' and aggregate[0]['query_sha256']==digest and aggregate[0]['rows']==len(rows),'Native execution item binding differs')
    native[identity]=([dict(zip(meta['columns'],row)) for row in rows],meta['columns'])
flat,_=native[IDENTITY+'__full_partition_population']
fields=[{'name':'workItemCode','type':'string','nullable':False},{'name':'company','type':'string','nullable':False},{'name':'count','type':'integer','nullable':False}]
left,le=scorer.project(flat,fields,gold=True);right,re=scorer.project(flatSQL,fields,gold=True)
need(not le and not re and collections.Counter(left)==collections.Counter(right) and len(flat)==1939,'Actual full native1939 != retained typed SQL projection')
population={}
for row in flat:population.setdefault(row['workItemCode'],[]).append({'company':row['company'],'count':row['count']})
# Reference presentation only: countDESC, never company tie-break or member selection.
population={code:sorted(rows,key=lambda row:-row['count']) for code,rows in population.items()}
limited,cols=native[IDENTITY];limited=verify_release.project(limited,definition['required_fields'],cols)
need(len(limited)==5,'Limited actual native cardinality differs')
selected=regular(ROOT/'actual_native_SQL_bridge_v1/actual_limited_native_projected_records.jsonl').read_bytes()
need([kernel.loads_exact(s) for s in selected.decode().splitlines()]==limited,'Actual native projection differs')
sel=manifest['source_selected_records']
need(set(sel)=={'path','records','bytes','sha256'} and sel['path']=='actual_native_SQL_bridge_v1/actual_limited_native_projected_records.jsonl' and type(sel['records']) is int and sel['records']==5 and type(sel['bytes']) is int and sel['bytes']==len(selected) and sel['sha256']==sha(selected),'Actual selected metadata differs')
need(exact(population)==exact(load(ROOT/'actual_native_SQL_bridge_v1/actual_native_full_partition_population.json')),'Normalized full reference population differs')
need(manifest['dispatch']=={'path':'outer_WI_metrics/score_predictions_partitioned_dispatch.py','declaration':'dispatch_declaration.json','limited_native_is_eligibility_population':False},'Explicit dispatch differs')
actual=dispatcher.read_run(ROOT,ROOT/'dispatch_declaration.json',ROOT/'actual_native_prediction_envelope.jsonl')
need(actual['exact'] is True and actual['diagnostic_only'] is False and actual['matched_records']==5,'Actual native production replay failed')
policy=load(ROOT/'nested_eligibility_policy.json');task=load(ROOT/'prospective_local_validated_task_envelope.json');declaration=load(ROOT/'dispatch_declaration.json')
controls=load(ROOT/'proofs/actual_original_five_tie_diagnostic_controls.json')
need(controls['lawful_combinations']==5 and controls['controls_n']==56,'Control inventory differs')
for test in controls['controls']:
    result=dispatcher.run(task,definition,policy,limited,population,{'id':IDENTITY,'repair_sha256':REPAIR,'records':test['input']},declaration)
    need(result['diagnostic_only'] is False and result['exact'] is test['expected']['exact'],'Production exact control differs: '+test['name'])
    for key in ['matched_records','precision','recall','f1']:
        if test['expected'].get(key) is not None:need(math.isclose(result[key],test['expected'][key],rel_tol=0,abs_tol=1e-12),'Complete WI metric control differs')
production=load(ROOT/'proofs/actual_production_dispatch_and_reader_controls.json')
need(production['production_reader_controls_n']==56 and production['production_rejections_n']==29 and production['production_internal_calls']['diagnostic_true_calls']==0,'Actual production audit failed')
# Optional explicit immutable source database. Default never opens a DB.
parser=argparse.ArgumentParser();parser.add_argument('--database',type=Path);args=parser.parse_args()
wholeSQL=False
if args.database is not None:
    dbp=regular(args.database.absolute());audit=load(ROOT/'source_inputs/data/actual_source_audit.json');expected=audit['database']
    def filehash(path):
        h=hashlib.sha256()
        with path.open('rb') as stream:
            for part in iter(lambda:stream.read(1024*1024),b''):h.update(part)
        return h.hexdigest()
    before=filehash(dbp);need(dbp.stat().st_size==expected['bytes'] and before==expected['sha256'],'Explicit immutable database pin differs')
    import sqlite3
    db=sqlite3.connect('file:'+str(dbp)+'?mode=ro&immutable=1',uri=True);db.row_factory=sqlite3.Row;db.execute('PRAGMA query_only=ON')
    query='SELECT r.node_id rn,r.resolutionId,t.node_id tn,t.tdocNumber,wi.node_id wn,wi.workItemCode,c.node_id cn,c.companyName FROM Resolution r JOIN rel_REFERENCES rf ON rf.src_id=r.node_id JOIN Tdoc t ON t.node_id=rf.dst_id JOIN rel_RELATED_TO rt ON rt.src_id=t.node_id JOIN WorkItem wi ON wi.node_id=rt.dst_id JOIN rel_SUBMITTED_BY sb ON sb.src_id=t.node_id JOIN Company c ON c.node_id=sb.dst_id'
    paths=[dict(row) for row in db.execute(query)]
    need(collections.Counter(map(exact,paths))==collections.Counter(map(exact,fixture['paths'])),'Explicit full13654 SQL paths differ')
    resolutions=[dict(row) for row in db.execute('SELECT node_id,resolutionId,content FROM Resolution')]
    references=[list(row) for row in db.execute('SELECT src_id,dst_id FROM rel_REFERENCES')]
    identities=[dict(row) for row in db.execute('SELECT node_id,tdocNumber FROM Tdoc')];db.close()
    for one,two in [(resolutions,fixture['Resolution']),(references,fixture['all_references']),(identities,fixture['Tdoc_identities'])]:
        need(collections.Counter(map(exact,one))==collections.Counter(map(exact,two)),'Explicit full retained source projection differs')
    need(filehash(dbp)==before,'Immutable database changed');wholeSQL=True
print(json.dumps({'status':'PASS','id':IDENTITY,'repair_sha256':REPAIR,'semantic_reviews':2,'full_retained_Resolution':3773,'literal_references':12995,'full_path_records':13654,'full_native_WI_company_groups':1939,'actual_limited_native_records':5,'lawful_nested_answers':5,'production_controls':56,'production_diagnostic_only':False,'source_raw_full_contents':12,'source_Tdoc_roles':294,'source_original_XML_documents':9,'source_original_XLSX':11,'source_role_failures':0,'explicit_full_SQL_replay':wholeSQL,'canonical9_modified_n':0,'original560_pass_increment':0,'new_public_admissions':0,'human_expert_n':0,'API_calls':0,'native_calls':0,'whole3773_raw_body_claimed':False}))
