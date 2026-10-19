#!/usr/bin/env python3
"""Relocatable stdlib audit of included saved source projections and proofs.

This is not a new raw-corpus parse, graph materialization, native service run,
full FTS rebuild, or model evaluation. External files are read only through
explicit optional CLI paths. Recorded private provenance paths are never used
as fallback inputs.
"""
from pathlib import Path
from collections import Counter,defaultdict
from decimal import Decimal,ROUND_HALF_UP
import argparse,copy,gzip,hashlib,importlib.util,json,re,sys,zipfile

sys.dont_write_bytecode=True
def reject_symlink_path(path):
    # Inspect the lexical route before resolve() can hide an entry or ancestor
    # symlink. Parent traversal is unnecessary in explicit portable input paths.
    path=Path(path).absolute()
    assert '..'not in path.parts,'Parent traversal prohibited in explicit path'
    for candidate in (path,*path.parents):
        assert not candidate.is_symlink(),'Symlink path component prohibited: '+str(candidate)
    return path

ROOT=reject_symlink_path(Path(__file__).absolute()).parent
INVENTORY_SHA='9831d2a5aa823e3b83a61f1f818a402170322a20365bb6839d4256b228abc630'
CRITERIA_SHA='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
REPAIR='bc739310bc8d3b131717dd95a7c873156822bc670009c83366e0aed88a69bc5c'
DEFINITION_SHA='01243921dd6086b8df22d01ffa9b5cd1fd4ad96bc6663d90253641a165d5df7c'
QUESTION='Return CR density (CRs per section) by spec (change-hotspot metric).'
QUESTION_SHA='17e2bd7058d434f51fcef2f6ae700f31b79ff4a792968de93d82e51f3c02f9de'
QUERY_SHA='8a353b2881c4fc96bed7c8c4db6cbb26a6acc50ce330f10ffce9e5fdc806ba28'
META={'README.md','manifest.json','verify_bundle.py','immutable_inventory.json'}

def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def load(p):return json.loads(Path(p).read_text())
def gz(p):
    with gzip.open(p,'rt')as f:return json.load(f)
def jsonl(p):
    opener=gzip.open if str(p).endswith('.gz')else open
    with opener(p,'rt')as f:return [json.loads(x)for x in f if x.strip()]
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def rel_file(root,relative):
    p=Path(relative)
    assert not p.is_absolute()and '..'not in p.parts and str(p)==relative,relative
    reject_symlink_path(root)
    result=reject_symlink_path(root/p)
    assert result.is_file()and not result.is_symlink(),relative
    return result

def verify_integrity(root=ROOT):
    root=Path(root).resolve()
    for p in root.rglob('*'):
        assert not p.is_symlink(),'Symlink prohibited: '+str(p.relative_to(root))
        assert p.is_file()or p.is_dir(),'Nonregular tree member'
    inventory=rel_file(root,'immutable_inventory.json')
    assert sha(inventory)==INVENTORY_SHA,'Immutable inventory pin mismatch'
    rows=load(inventory)['files']
    paths=[x['path']for x in rows]
    assert len(paths)==len(set(paths))and not(set(paths)&META)
    actual={str(p.relative_to(root))for p in root.rglob('*')if p.is_file()}
    assert actual==set(paths)|META,'Closed file population mismatch'
    for r in rows:
        p=rel_file(root,r['path'])
        assert p.stat().st_size==r['bytes']and sha(p)==r['sha256'],'Immutable file identity: '+r['path']
    manifest=load(rel_file(root,'manifest.json'))
    listed=manifest['files'];assert len({x['path']for x in listed})==len(listed)
    assert {x['path']for x in listed}==actual-{'manifest.json'}
    for r in listed:
        p=rel_file(root,r['path'])
        assert p.stat().st_size==r['bytes']and sha(p)==r['sha256'],'Outer file identity: '+r['path']
    assert manifest['original560_increment']==0 and manifest['expert_validation_n']==0
    assert manifest['default_replay_kind']=='saved_projections_and_recorded_proofs'
    assert manifest['default_raw14_or_raw64_reparse']is False
    return {'closed_files':len(actual),'immutable_nonmetadata_files':len(rows),'inventory_sha256':sha(inventory)}

def verify_contract():
    dpath=ROOT/'contract/prospective_finite_dependency_source_variant_definition.json'
    assert sha(dpath)==DEFINITION_SHA
    d=load(dpath);criteria=load(ROOT/'contract/criteria.json')
    assert sha(ROOT/'contract/criteria.json')==CRITERIA_SHA==d['criteria_sha256']
    assert d['question_en']==QUESTION and hashlib.sha256(QUESTION.encode()).hexdigest()==QUESTION_SHA==d['question_sha256']
    query=(ROOT/'contract/original_query.cypher').read_bytes()
    assert hashlib.sha256(query).hexdigest()==QUERY_SHA
    assert query.decode()==d['query']==d['original_query']and d['query_sha256']==d['original_query_sha256']==QUERY_SHA
    definition=copy.deepcopy(d);definition.pop('repair_sha256')
    assert hashlib.sha256(canon(definition).encode()).hexdigest()==REPAIR==d['repair_sha256']
    assert [x['name']for x in d['required_fields']]==['specNumber','crCnt','secCnt','density']
    assert d['collection']=={'kind':'set','cardinality':{'kind':'exact','value':5},'record_serialization_rank_required':False}
    assert d['preserved_unverified_graph_scope']['complete_source_graph_reconstruction_claim']is False
    assert d['fixed_population']['historical58_exact_file_versions_reconstructed']is False
    assert d['original560_increment']==0 and d['expert_validation_n']==0
    schema=module(ROOT/'contract/review_schema.py','portable_official_review_schema')
    p=ROOT/'contract/primary_exact_seven_unit_finite_dependency_source_policy_review.json'
    s=ROOT/'contract/independent_exact_seven_unit_finite_dependency_source_policy_review_v2.json'
    assert sha(p)!=sha(s),'Secondary cannot be replaced with primary bytes'
    for path in [p,s]:
        schema.check_pass(load(path),QUESTION,criteria['semantic_units'],criteria_sha=CRITERIA_SHA,
            identity_key='repair_sha256',identity_sha=REPAIR)
    return d

def replay_source_projections():
    recipe=module(ROOT/'recipes/materialize_graph.py','portable_finite_dependency_recipe')
    nodes,edges=recipe.derive()
    assert canon(nodes)==canon(load(ROOT/'contract/generic_derived_eight_Section_nodes.json'))
    assert edges==load(ROOT/'contract/generic_derived_all_131_additive_edges.json')
    assert len(nodes)==8 and Counter(x['relationship']for x in edges)=={'MODIFIES':107,'BELONGS_TO_SPEC':8,'PARENT_SECTION':8,'HAS_SUB_SECTION':8}
    t=ROOT/'source_projection/metadata'
    metadata=module(t/'replay_generic_modified_spec_delta.py','portable_metadata_rules')
    frozen=jsonl(t/'evidence/all_frozen_CR_to_MODIFIES_source_comparisons.jsonl.gz')
    source=jsonl(t/'evidence/all_retained_input_CR_MODIFIES_metadata_witnesses.jsonl.gz')
    specs=load(t/'evidence/all_original_Spec_nodes.json')
    assert len(frozen)==34622 and len(source)==35953 and len(specs)==187
    delta,absent=metadata.derive(frozen,source,specs)
    assert absent==2 and len(delta)==107
    assert Counter(metadata.canonical(x['source_meeting'])for x in delta)=={'RAN2#133':106,'RAN2#101bis':1}
    assert sum(x['resolution_route']!='original_production_exact_id'for x in delta)==6
    additions=defaultdict(list)
    for x in delta:additions[x['source_CR_iri']].append(x['target_source_iri'])
    byiri={x['source_iri']:x for x in specs};assert len(byiri)==187
    numerator=Counter();unknown=[]
    for row in frozen:
        old=[r['target_iri']for r in row['frozen_targets']if r['specRelease']is None and 'Spec'in r['target_labels']]
        after=old+additions[row['frozen_CR_iri']]
        expected=row['source_spec_numbers']
        if expected is not None:
            assert sorted(byiri[x]['specNumber']for x in after)==sorted(expected)
        else:
            assert not row['source_classified_CR_found']and not old and not after
            assert row['other_retained_source_rows_if_not_CR']
            assert all(r['named_values']['Type']=='LS in'for r in row['other_retained_source_rows_if_not_CR'])
            unknown.append(row['tdoc'])
        numerator.update(after)
    assert len(unknown)==2 and len(numerator)==72
    phase3=ROOT/'source_projection/phase3'
    products=gz(phase3/'all14_declared_parsed_source_products.json.gz')
    saved=gz(phase3/'complete_baseline_phase3_identity_projection.json.gz')
    identities={tuple(x['identity']):x['nodes'][0]for x in saved['records']}
    assert all(len(x['nodes'])==1for x in saved['records'])and len(identities)==len(saved['records'])
    all_sections=[(p,s)for p in products for s in p['sections']]
    source_sections={s['sectionId']:(p,s)for p,s in all_sections}
    assert len(products)==14 and len(all_sections)==len(source_sections)==3894
    headings=gz(ROOT/'source_projection/heading/all_latest14_source_Section_heading_raw_and_complete_owned_reference_inputs.json.gz')
    assert len(headings)==3894 and {h['sectionId']for h in headings}==set(source_sections)
    prefixes=tuple(p['spec_number']+'-'+p['release']+'-'for p in products)
    old_latest={k for k in identities if k[0]=='Section'and k[1].startswith(prefixes)}
    assert len(old_latest)==3886
    assert {k[1]for k in old_latest}|{x['identity'][1]for x in nodes}==set(source_sections)
    belongs=[x for x in saved['owned_scope_edges']if x[1]=='BELONGS_TO_SPEC']
    assert len(belongs)==3886
    denominator=Counter()
    for start,kind,target in belongs:
        assert tuple(start)in old_latest
        p,s=source_sections[start[1]]
        assert tuple(target)==('Spec',p['spec_number'],p['release'])
        denominator[identities[tuple(target)]['source_iri']]+=1
    for x in edges:
        if x['relationship']=='BELONGS_TO_SPEC':denominator[x['target_iri']]+=1
    assert sum(denominator.values())==3894
    release_edges=load(ROOT/'source_projection/all_original_IN_RELEASE_OF_edges.json')['edges']
    assert len(release_edges)==64 and len({(e['source_iri'],e['target_iri'])for e in release_edges})==64
    linked=defaultdict(list)
    for e in release_edges:
        child=byiri[e['source_iri']];hub=byiri[e['target_iri']]
        assert hub['specRelease']is None and child['specNumber']==hub['specNumber']
        assert re.fullmatch(r'Rel-\d+',child['specRelease'])
        linked[e['target_iri']].append(child)
    linked_positive=set(numerator)&set(linked)
    assert len(linked_positive)==15 and len(set(numerator)-set(linked))==57
    rows=[];zero=[]
    for hub in sorted(linked_positive):
        candidates=linked[hub];latest=max(int(x['specRelease'][4:])for x in candidates)
        choices=[x for x in candidates if int(x['specRelease'][4:])==latest]
        assert len(choices)==1 and latest==19
        rk=choices[0];sec=denominator[rk['source_iri']]
        if sec==0:zero.append(byiri[hub]['specNumber']);continue
        # Exact rational arithmetic to two decimal places, half up. No binary
        # float determines the independent expected density.
        count=numerator[hub]
        density=(Decimal(count)/Decimal(sec)).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP)
        rows.append({'specNumber':byiri[hub]['specNumber'],'crCnt':count,'secCnt':sec,'density':density})
    assert zero==['38.822']and len(rows)==14
    rows.sort(key=lambda x:x['density'],reverse=True)
    assert rows[4]['density']>rows[5]['density']
    return {'nodes':nodes,'edges':edges,'full_rows':rows,'selected':rows[:5],
        'counts':{'fixed_CR_nodes':len(frozen),'source_metadata_records':len(source),'Spec_nodes':len(specs),
        'source_covered_CR_nodes':34622-len(unknown),'unknown_CR_metadata_cases':unknown,
        'source_latest_Section_identities':len(source_sections),'frozen_latest_Section_identities':len(old_latest),
        'new_Section_nodes':len(nodes),'new_edges':len(edges),
        'positive_CR_hubs':len(numerator),'release_linked_positive_hubs':len(linked_positive),
        'excluded_no_retained_edition_hubs':len(set(numerator)-set(linked)),
        'excluded_zero_Section_spec':zero,'positive_Section_groups':len(rows)},
        'generic_metadata_boundary_controls':metadata.controls()}

def record_key(r):
    return (r['specNumber'],r['crCnt'],r['secCnt'],Decimal(str(r['density'])))

def compare_saved_proofs(result):
    m=load(ROOT/'saved_proof/materialization/actual_materialization_manifest.json')
    proof=load(ROOT/'saved_proof/materialization/actual_all79_tables_and_full_graph_fact_equivalence.json')
    assert m['whole_nodes']==proof['whole_nodes']==156296 and m['whole_edges']==proof['whole_edges']==939168
    assert m['old_tables']==79 and len(proof['all79_storage_tables'])==79
    assert all(x['typed_original_rows_preserved']for x in proof['all79_storage_tables'])
    assert proof['old_TTL_exact_byte_prefix']and proof['all_global_and_typed_edges_consistent']
    assert m['full_source_reconstruction_claim']is False
    assert sha(ROOT/'saved_proof/materialization/actual_all79_tables_and_full_graph_fact_equivalence.json')==m['full_fact_proof']['sha256']
    native=load(ROOT/'saved_proof/native/actual_native_manifest.json')
    capture=load(ROOT/'saved_proof/native/actual_native_four_column_source_capture.json')
    sql=load(ROOT/'saved_proof/native/actual_immutable_SQL_four_column_reference.json')
    assert native['owned_container_stopped']and native['question_admissions']==0
    assert native['source']['sha256']==m['source_TTL']['sha256']
    assert native['db']['sha256']==m['source_SQL']['sha256']
    assert native['measured_counts']['total_nodes']==156296
    assert sum(native['measured_counts']['rel_counts'].values())==939168
    assert sha(ROOT/'saved_proof/native/actual_native_four_column_source_capture.json')==native['capture']['sha256']
    names=['specNumber','crCnt','secCnt','density']
    for kind,expected in [('selected',result['selected']),('whole_matching_pool',result['full_rows'])]:
        c=capture[kind]
        assert c['columns']==names and c['actual_query_type']==c['EXPLAIN_query_type']=='r'
        assert c['contains_updates']is False and c['transaction_rolled_back']and c['complete']and not c['truncated']
        assert c['rows']==sql['rows'][kind]
        got=[dict(zip(names,r))for r in c['rows']]
        assert Counter(map(record_key,got))==Counter(map(record_key,expected))
        assert c['row_n']==len(expected)
        assert all(Decimal(str(got[i]['density']))>=Decimal(str(got[i+1]['density']))for i in range(len(got)-1))
    assert capture['selected']['literal_query']==(ROOT/'contract/original_query.cypher').read_text()
    assert capture['whole_matching_pool']['literal_query']==capture['selected']['literal_query'].removesuffix(' LIMIT 5')
    requested=jsonl(ROOT/'saved_proof/native/requested_records.jsonl')
    assert Counter(map(record_key,requested))==Counter(map(record_key,result['selected']))
    built=load(ROOT/'saved_proof/corpus/build_receipt.json')
    replay=load(ROOT/'saved_proof/corpus/all_fact_reconstruction_receipt.json')
    assert built['inventory']['nodes']==replay['nodes_reconstructed']==156296
    assert built['inventory']['edges']==replay['edges_reconstructed']==939168
    assert built['chunks']==replay['chunks_reconstructed']==279747
    assert built['database']['sha256']==replay['immutable_database_sha256']
    assert built['fact_source_sha256']==replay['fact_source_sha256']==m['source_TTL']['sha256']
    assert all(replay[k]for k in ['every_TTL_node_label_property_equal','every_directed_TTL_edge_equal',
        'all_chunk_overlaps_and_full_text_SHA_replayed','no_missing_or_added_node_or_edge','FTS_integrity_and_row_population_equal'])
    assert built['fact_selection_query_or_answer_inputs']==[]and built['raw_covers_or_prefix_fixtures_used']is False
    broadprops=load(ROOT/'counterpolicy/actual_existing_source_owned_property_differences.json')
    broadold=load(ROOT/'counterpolicy/actual_frozen_only_owned_edges_under_this_source_cohort.json')
    assert len(broadprops)==155 and len(broadold)==395
    return {'saved_native_SQL_full14_selected5_equal_independent_projection_math':True,
        'saved_whole_graph_nodes':156296,'saved_whole_graph_edges':939168,'saved_79_table_oldfact_preservation':True,
        'saved_corpus_full_fact_reconstruction':True,'fresh_native_or_large_graph_run':False}

def replay_scoring_controls():
    sys.path.insert(0,str(ROOT/'scoring'))
    scorer=module(ROOT/'scoring/original_scorer.py','portable_four_field_scorer')
    contract=load(ROOT/'scoring/evaluation_contract.json')
    gold=jsonl(ROOT/'saved_proof/native/requested_records.jsonl')
    cases=[]
    def check(name,pred,exact,zero=False):
        result=scorer.score(contract,gold,pred,diagnostic=True)
        assert result['exact']is exact,(name,result)
        if zero:assert result['f1']==0,(name,result)
        cases.append({'case':name,'pass':True})
    check('actual_native_reference',gold,True)
    check('set_reordering_preserved',list(reversed(gold)),True)
    x=copy.deepcopy(gold)
    for r in x:r['density']=Decimal(str(r['density']))
    check('exact_decimal_number_equivalence',x,True)
    for field in ['specNumber','crCnt','secCnt','density']:
        x=copy.deepcopy(gold)
        for r in x:del r[field]
        check('missing_required_'+field,x,False,True)
        x=copy.deepcopy(gold)
        for r in x:r[field]=None
        check('nonnull_'+field,x,False,True)
    for field in ['crCnt','secCnt']:
        for kind in ['wrong_count','string','boolean','floating_integral']:
            x=copy.deepcopy(gold)
            for r in x:r[field]={'wrong_count':r[field]+1,'string':str(r[field]),'boolean':True,'floating_integral':float(r[field])}[kind]
            check(field+'_'+kind,x,False,True)
    x=copy.deepcopy(gold)
    for r in x:r['specNumber']='WRONG-'+r['specNumber']
    check('wrong_spec_identity',x,False,True)
    for name,fn in [('density_wrong',lambda v:Decimal(str(v))+Decimal('0.01')),
                    ('density_high_precision_perturbation',lambda v:Decimal(str(v))+Decimal('0.000000000000000000000001')),
                    ('density_string',str),('density_boolean',lambda v:True),('density_nonfinite',lambda v:float('inf'))]:
        x=copy.deepcopy(gold)
        for r in x:r['density']=fn(r['density'])
        check(name,x,False,True)
    x=copy.deepcopy(gold)
    for r in x:r['crCnt'],r['secCnt']=r['secCnt'],r['crCnt']
    check('numerator_denominator_roles_swapped',x,False,True)
    check('empty_answer',[],False,True)
    check('missing_selected_record',gold[:-1],False)
    check('duplicate_replaces_record',gold[:-1]+[gold[0]],False)
    extra=copy.deepcopy(gold[0]);extra['specNumber']='EXTRA'
    check('extra_record',gold+[extra],False)
    token=str(gold[0]['density'])+'000000000000000000000001'
    assert float(token)==gold[0]['density']
    assert json.loads('{"density":'+token+'}',parse_float=Decimal)['density']!=Decimal(str(gold[0]['density']))
    saved=load(ROOT/'saved_proof/independent/actual_four_field_scoring_controls.json')
    assert len(cases)==len(saved['controls'])==30
    assert [x['case']for x in cases]==[x['case']for x in saved['controls']]
    return {'replayed_four_field_scoring_controls':len(cases),'raw_decimal_precision_counterexample_replayed':True}

def optional_hashes(args):
    checked=[]
    m=load(ROOT/'saved_proof/materialization/actual_materialization_manifest.json')
    fts=load(ROOT/'saved_proof/corpus/build_receipt.json')['database']
    for name,pin in [('base_sql',m['base_SQL']),('base_ttl',m['base_TTL']),
                     ('source_sql',m['source_SQL']),('source_ttl',m['source_TTL']),('fts',fts)]:
        value=getattr(args,name)
        if value is None:continue
        value=reject_symlink_path(value)
        assert value.is_file(),name
        assert value.stat().st_size==pin['bytes']and sha(value)==pin['sha256'],name
        checked.append({'kind':name,'actual_SHA_verified':True,'fresh_full_parse':False})
    if args.raw_source_root is not None:
        base=reject_symlink_path(args.raw_source_root);pins=load(ROOT/'provenance/optional_external_raw_input_inventory.json')
        for row in pins['TS14']+pins['metadata64']:
            p=rel_file(base,row['path']);assert p.stat().st_size==row['bytes']and sha(p)==row['sha256']
        for row in pins['actual_local_TS_archive_member_pins']:
            a=row['archive'];p=rel_file(base,a['path'])
            assert p.stat().st_size==a['bytes']and sha(p)==a['sha256']
            with zipfile.ZipFile(p)as z:data=z.read(row['member'])
            assert len(data)==row['member_bytes']and hashlib.sha256(data).hexdigest()==row['member_sha256']
        checked.append({'kind':'explicit_external_raw_inputs','raw_inputs_hashed':78,
            'TS_archive_member_pairs_hashed':len(pins['actual_local_TS_archive_member_pins']),
            'fresh_whole_raw14_or_raw64_reparse':False})
    return checked

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['raw-source-root','base-sql','base-ttl','source-sql','source-ttl','fts']:
        parser.add_argument('--'+name,type=Path)
    args=parser.parse_args()
    integrity=verify_integrity();verify_contract();source=replay_source_projections()
    proofs=compare_saved_proofs(source);scorer=replay_scoring_controls();external=optional_hashes(args)
    print(json.dumps({'status':'PASS_SAVED_SOURCE_PROJECTION_REPLAY_AND_RECORDED_PROOF_AUDIT',
        'integrity':integrity,'source_projection_replay':source['counts'],'saved_proof_checks':proofs,
        'scoring':scorer,'generic_metadata_boundary_controls':len(source['generic_metadata_boundary_controls']),
        'optional_explicit_external_checks':external,
        'raw14_or_raw64_reparse_performed':False,'new_native_or_API_calls':0,
        'original560_increment':0,'expert_validation_n':0},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
