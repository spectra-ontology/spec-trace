"""Replay the pinned documentary trace, source roles, native rows and tie contract."""
import sys
if sys.flags.optimize != 0:
    raise SystemExit('Run without -O/-OO')
from pathlib import Path
import collections, contextlib, copy, gzip, hashlib, importlib.util, io, json, math, re

INVENTORY_SHA = '341f7ed3fe677191242b1825e4633c72171ae70a35a35e6a7e3163fe88c618ca'
FIXED = {'id': 'RAN4_P3_CQ4-1', 'artifact_type': 'source_grounded_local_contract_evidence', 'local_validation_status': 'completed_local_gates_ROOT_final_seal_pending', 'repair_sha256': '22c2820652aef63282405510d7e8b8bcaf6016e2b46e9c33d7fc0bc97901ffe7', 'criteria_sha256': 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4', 'immutable_inventory_sha256': '341f7ed3fe677191242b1825e4633c72171ae70a35a35e6a7e3163fe88c618ca', 'canonical_definition_keys': ['cardinality_policy', 'collection', 'id', 'original_query', 'original_question_preserved', 'question_en', 'reference_query', 'repair_class', 'required_fields'], 'frozen_TTL_sha256': '90c6bf7d4420949b7395e8a0b5700a07f8866ddd461699d4516fe4e4f5deec5d', 'new_admissions': 0, 'API_calls': 0, 'native_execution_by_replay': False}
ID = 'RAN4_P3_CQ4-1'
META = {'README.md','manifest.json','inventory.json','verify.py'}

def sha(b): return hashlib.sha256(b).hexdigest()
def canonical(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def pin(p): return {'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
def load_module(name,p):
    spec=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def tree(root):
    result={}
    for p in root.rglob('*'):
        assert not p.is_symlink(),'Symlink refused'
        if p.is_dir(): continue
        assert p.is_file(),'Nonregular entry refused'
        result[p.relative_to(root).as_posix()]=pin(p)
    return result
def main():
    entry=Path(__file__).absolute(); root=entry.parent
    for p in [entry,root,*root.parents]: assert not p.is_symlink(),'Entry/ancestor symlink refused'
    before=tree(root)
    inv_bytes=(root/'inventory.json').read_bytes(); assert sha(inv_bytes)==INVENTORY_SHA
    inventory=json.loads(inv_bytes)
    assert inventory=={'files':{k:v for k,v in before.items()if k not in META}},'Immutable inventory differs'
    manifest=json.loads((root/'manifest.json').read_text())
    expected=dict(FIXED,files={k:v for k,v in before.items()if k!='manifest.json'})
    assert canonical(manifest)==canonical(expected),'Manifest metadata or file map differs'
    expected_files=set(inventory['files'])|META
    assert set(before)==expected_files
    expected_dirs={str(Path(k).parent)for k in expected_files if str(Path(k).parent)!='.'}
    expected_dirs|={str(a)for k in expected_files for a in Path(k).parents if str(a)!='.'}
    assert {p.relative_to(root).as_posix()for p in root.rglob('*')if p.is_dir()}==expected_dirs,'Extra directory'
    read=lambda n:json.loads((root/n).read_text())
    contract=read('contract/definition.json'); original=read('authority/original.json')
    assert contract['id']==ID and set(contract)==set(FIXED['canonical_definition_keys'])
    repair=sha(canonical(contract).encode()); assert repair==FIXED['repair_sha256']
    assert original['id']==ID and contract['question_en']==original['question_en']
    assert sha(contract['question_en'].encode())==original['question_sha256']
    assert sha(contract['original_query'].encode())==original['original_query_sha256']
    assert contract['original_query']==original['original_query']
    assert contract['original_question_preserved'] is True
    assert [f['name']for f in contract['required_fields']]==['resolutionId','tdocNumber']
    criteria=read('authority/criteria.json')
    assert sha((root/'authority/criteria.json').read_bytes())=='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
    schema=load_module('review_schema',root/'authority/review_schema.py')
    primary=read('contract/primary.json');secondary=read('contract/secondary.json')
    for review in [primary,secondary]:
        schema.check_pass(review,contract['question_en'],criteria['semantic_units'],criteria_sha=sha((root/'authority/criteria.json').read_bytes()),identity_key='repair_sha256',identity_sha=repair)
    assert primary!=secondary,'Separate review evidence required'
    source=load_module('source_replay',root/'source/replay_source.py')
    with contextlib.redirect_stdout(io.StringIO()): source_result=source.main()
    assert source_result['status']=='PASS' and source_result['admissible_highest_ID_ties']==18
    f=json.loads(gzip.decompress((root/'source/frozen_dependency_projection.json.gz').read_bytes()))
    assert f['original_query']==contract['original_query'] and f['original_question']==contract['question_en']
    crs={r['node_id']:r for r in f['CR_properties']}
    projected=lambda rows:[{'resolutionId':r['r.resolutionId'],'tdocNumber':r['cr.tdocNumber']}for r in rows]
    counter=lambda rows:collections.Counter(canonical(r)for r in rows)
    full_query=contract['reference_query'].removesuffix(' LIMIT 10')
    native=[]
    for label,query,n in [('full',full_query,635),('limited',contract['reference_query'],10)]:
        case=read('native/'+label+'.json')
        raw=gzip.decompress((root/('native/'+label+'.jsonl.gz')).read_bytes())
        assert sha(raw)==case['rows_sha256']
        assert case['id']==ID and case['wg']=='RAN4' and case['status']=='OK'
        assert case['query']==query and case['query_sha256']==sha(query.encode())
        assert case['columns']==['r.resolutionId','cr.tdocNumber']
        assert case['rows_retained']==n and case['truncated']is False
        assert case['full_rows_available']is True and case['rollback_completed']is True
        assert case['execution_summary_complete']is True and case['plan_query_type']==case['execution_query_type']=='r'
        assert case['limits']=={'rows':100000,'bytes':268435456,'timeout_s':20}
        values=[json.loads(line)for line in raw.splitlines()]
        assert len(values)==n and all(type(v)is list and len(v)==2 and all(type(x)is str for x in v)for v in values)
        native.append([dict(zip(case['columns'],v))for v in values])
    full,limited=native
    sql=read('data/full_SQL_rows.json'); assert len(sql)==635 and counter(full)==counter(sql)
    expected_pairs=[{'resolutionId':p['resolutionId'],'tdocNumber':p['tdocNumber']}for p in f['paths']if(crs[p['cr_node']]['status']or'').strip().lower()in {'agreed','approved','endorsed'}]
    gold=projected(full); assert counter(gold)==counter(expected_pairs)
    assert len(set(canonical(r)for r in gold))==635
    assert [r['resolutionId']for r in gold]==sorted([r['resolutionId']for r in gold],reverse=True)
    execution=read('native/execution_RAN4.json');protocol=read('native/execution_protocol.json')
    assert execution['input_sha256']==sha((root/'native/input.jsonl').read_bytes())
    input_rows=[json.loads(x)for x in(root/'native/input.jsonl').read_text().splitlines()]
    assert [x['candidate_query']for x in input_rows]==[full_query,contract['reference_query']]
    assert execution['source_before']==execution['source_after'] and execution['inventory_unchanged']is True
    src=execution['source_before']; assert src['source']['sha256']==FIXED['frozen_TTL_sha256']
    assert (src['nodes'],src['relationships'])==(342161,1592845)
    assert [(x['status'],x['rows'],x['query_sha256'])for x in execution['items']]==[('OK',635,sha(full_query.encode())),('OK',10,sha(contract['reference_query'].encode()))]
    assert execution['model_calls']==0 and type(execution['model_calls'])is int
    assert protocol['container_memory_bytes']==2*1024**3 and protocol['container_cpu_cores']==1 and protocol['query_timeout_seconds']==20
    assert protocol['host_reserve_bytes']==16*1024**3 and protocol['model_calls']==0
    outer=read('native/outer_guard.json'); assert outer['status']=='PASS' and outer['child_started']is True and outer['child_exit']==0 and outer['failure']is None
    assert outer['prestart_available_minimum_bytes']==26*1024**3 and outer['continuous_reserve_minimum_bytes']==16*1024**3
    assert outer['owned_cleanup']['owned_stopped']is True and outer['owned_cleanup']['common_lock_held']is True
    assert all(type(outer['initial_memory'][h])is int and outer['initial_memory'][h]>=26*1024**3 for h in ['Linux_available_bytes','Windows_available_bytes'])
    assert all(type(s[h])is int and s[h]>=16*1024**3 for s in outer['memory_samples']for h in ['Linux_available_bytes','Windows_available_bytes'])
    obs=[json.loads(x)for x in(root/'native/fresh_observations.jsonl').read_text().splitlines()]
    assert obs and len({x['nonce']for x in obs})==len(obs)
    assert all(x['Get_CimInstance_calls_for_this_request']==1 and x['cached_values_used']==0 and type(x['windows_available_bytes'])is int for x in obs)
    sys.path.insert(0,str(root/'scoring'));scorer=load_module('original_scorer',root/'scoring/original_scorer.py')
    groups=scorer.make_order_groups(contract,full,gold); assert len(groups[0])==18
    def score(pred):return scorer.score(contract,gold,pred,diagnostic=True,order_groups=groups)
    assert score(projected(limited))['exact']is True
    assert score(projected(read('data/SQLite_selected10.json')))['exact']is True
    assert projected(limited)!=projected(read('data/SQLite_selected10.json'))
    a=gold[:10];b=list(reversed(gold[8:18]));tests=[]
    def check(name,pred,want):
        result=score(pred); assert result['exact']is want,(name,result)
        tests.append({'name':name,'expected_exact':want,'actual':result})
    check('first_valid_tied_subset',a,True);check('different_valid_tied_subset_with_free_within_tie_order',b,True)
    check('SQLite_selected10',projected(read('data/SQLite_selected10.json')),True);check('same_subset_reversed',list(reversed(a)),True)
    check('all18_is_not_finite10',gold[:18],False);check('missing_one',a[:-1],False);check('extra_one',gold[:11],False)
    bad=copy.deepcopy(a);bad[-1]=dict(bad[0]);check('duplicate_pair',bad,False)
    bad=copy.deepcopy(a);bad[-1]=dict(gold[18]);check('lower_id_replaces_cutoff_pair',bad,False)
    for field in ['resolutionId','tdocNumber']:
        for kind,value in [('null',None),('bool',True),('integer',1),('wrong_string','NOT_AN_ACTUAL_ID')]:
            bad=copy.deepcopy(a);bad[0][field]=value;check(field+'_'+kind,bad,False)
        bad=copy.deepcopy(a);del bad[0][field];check(field+'_missing',bad,False)
    top=max(p['resolutionId']for p in f['paths'])
    for p in f['paths']:
        if p['resolutionId']==top and(crs[p['cr_node']]['status']or'').strip().lower()not in {'agreed','approved','endorsed'}:
            bad=copy.deepcopy(a);bad[-1]={'resolutionId':p['resolutionId'],'tdocNumber':p['tdocNumber']};check('nonaffirmative_'+p['tdocNumber'],bad,False)
    stored=read('data/scoring_controls.json')
    # The scorer population order inside the top tie may differ; only per-control
    # outcomes and all public score fields are compared, never one arbitrary slice.
    assert tests==stored
    generic=[x for x in tests if any(x['name'].startswith(n+'_')for n in ['resolutionId','tdocNumber'])]
    assert len(generic)==10 and all(x['actual']['exact']is False for x in generic)
    assert sum(x['expected_exact']for x in tests)==4 and len(tests)==29
    assert tree(root)==before,'Replay modified package'
    result={'status':'PASS','id':ID,'cases':[{'id':ID,'repair_sha256':repair,'source_paths':1766,'eligible_unique_pairs':635,'native_full_rows':635,'native_limited_rows':10,'required_fields':2,'cutoff_tie_pairs':18,'valid_ten_subsets':math.comb(18,10),'source_current_outcomes':14,'source_earlier_endorsed':4,'excluded_cutoff_pairs':10,'generic_field_controls':10,'tie_role_controls_positive':4,'tie_role_controls_adverse':25,'native_and_SQL_different_valid_answers':True,'semantic_reviews':2}],'new_admissions':0,'API_calls':0,'native_executed_by_replay':False}
    print(json.dumps(result));return result
if __name__=='__main__':main()
