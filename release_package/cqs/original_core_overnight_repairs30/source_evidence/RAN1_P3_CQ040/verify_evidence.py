#!/usr/bin/env python3
"""CQ040 offline recorded-operation replay, with no host/native/API fallback."""
import sys
if sys.flags.optimize != 0:
    raise RuntimeError('Assertions require a nonoptimized interpreter')
sys.dont_write_bytecode = True
from pathlib import Path
import collections
import copy
import gzip
import hashlib
import json
import xml.etree.ElementTree as ET

INVENTORY_SHA256 = 'f262cfe3aa0487cf58323308b5132aedc6eebf5ddbac88f802f74e91be6071bd'
EXPECTED_METADATA = {'id': 'RAN1_P3_CQ040', 'artifact_type': 'two_AI_source_grounded_recorded_operation_actual_native8_pending_ROOT_seal', 'repair_sha256': '5190dbce5c32071f9074398d5f37c9f2038eb8690eb439431bbc6aaa476edead', 'final_admission_ready': False, 'ROOT_secondary_review_included': True, 'new_exact_eight_native_included': True, 'old_exact_native_rows': 5, 'independent_SQL_Python_rows': 8, 'whole_operand_rows': {'Agreement': 21058, 'CR': 10715, 'Spec': 127, 'REFERENCES': 19454, 'MODIFIES': 10671}, 'source_complete_citation_count_certified': False, 'new_original_core_admissions': 0, 'expert_validation_n': 0, 'independent_reviewer_count_in_this_preflight': 2, 'source_scope': 'Original RAN1 eight-family captured recorded-operation counts; original authored specific-five filter remains counterauthority.', 'scope_interpretation': 'Two separate nonblind AI judgments accept exact eight-family repair; not author or expert endorsement.', 'remaining_gate': 'ROOT independently verifies and seals this exact final packet. No paid evaluation or publication is included.', 'actual_native_rows': 8, 'native_values': 24}

def no_symlink(p):
    p = Path(p)
    for item in (p, *p.parents):
        if item.is_symlink():
            raise RuntimeError('Symlink boundary: '+str(item))
    return p

no_symlink(Path(__file__).absolute())
PACKAGE_ROOT = Path(__file__).resolve().parent

def read(name):
    p = no_symlink(PACKAGE_ROOT/name)
    if not p.is_file():
        raise RuntimeError('Missing file: '+name)
    return p.read_bytes()

def sha(b):
    return hashlib.sha256(b).hexdigest()

def load(name):
    return json.loads(read(name))

def main():
    if len(sys.argv) != 1:
        raise RuntimeError('No external source/native path accepted')
    invraw = read('immutable_inventory.json')
    assert sha(invraw) == INVENTORY_SHA256
    inv = json.loads(invraw)
    manifest = load('manifest.json')
    assert set(manifest) == {'metadata','inventory','verifier_sha256'}
    assert json.dumps(manifest['metadata'],sort_keys=True,separators=(',',':')) == json.dumps(EXPECTED_METADATA,sort_keys=True,separators=(',',':'))
    assert type(manifest['metadata']['expert_validation_n']) is int
    assert type(manifest['metadata']['new_original_core_admissions']) is int
    assert manifest['inventory'] == {'path':'immutable_inventory.json','sha256':INVENTORY_SHA256,'bytes':len(invraw)}
    assert manifest['verifier_sha256'] == sha(read('verify_evidence.py'))
    actual = set()
    for p in PACKAGE_ROOT.rglob('*'):
        no_symlink(p)
        if p.is_file():actual.add(p.relative_to(PACKAGE_ROOT).as_posix())
        elif not p.is_dir():raise RuntimeError('Unsupported filesystem entry')
    assert actual == set(inv['files']) | {'manifest.json','immutable_inventory.json','verify_evidence.py'}
    for name, meta in inv['files'].items():
        b = read(name)
        assert meta == {'bytes':len(b),'sha256':sha(b)}, name

    task = load('definition.json')
    fields = ('id','question_en','original_query','reference_query','required_fields',
              'collection','cardinality_policy','repair_class','original_question_preserved')
    sys.path.insert(0,str(PACKAGE_ROOT/'canonical'))
    import scorer
    import review_schema
    digest = sha(scorer.get_kernel().json_exact({k:task[k] for k in fields}).encode())
    assert digest == task['repair_sha256'] == EXPECTED_METADATA['repair_sha256']
    assert task['id'] == 'RAN1_P3_CQ040'
    assert task['question_en'] == 'Compare CR counts against agreement counts per TS (which spec changes most relative to consensus).'
    assert sha(task['original_query'].encode()) == '3b8c946b836267a3c183e2d3a2e4e01ba99e319b2e5b6386dba01c1846b8896d'
    assert read('proposed_full_eight_query.cypher').decode() == task['reference_query']
    assert [(x['name'],x['type']) for x in task['required_fields']] == [('ts','string'),('crCnt','integer'),('agrCnt','integer')]
    assert task['collection'] == {'kind':'set'} and task['cardinality_policy'] == {'mode':'all'}
    assert task['question_en'] in read('authority/original_CQ040.cypher').decode()
    assert task['original_query'] in read('authority/original_CQ040.cypher').decode()
    csv = read('authority/HEAD_cq_all_137.csv').decode().splitlines()
    assert csv[99].startswith('3,CQ040,통합분석,TS별 CR 건수와 Agreement 건수를 비교해줘.')
    own = load('authority/own_original_dataset_full.json')
    qs = {q['id']:q for q in own['questions']}
    assert qs['CQ040']['cypher'] == task['original_query']
    assert qs['CQ040']['question'] == 'TS별 CR 건수와 Agreement 건수를 비교해줘. 어떤 TS가 합의 대비 변경이 많은지 보고 싶어'
    assert qs['CQ040']['category'] == '통합분석'
    assert '8개 TS별' in qs['CQ019']['question']
    assert all(x in qs['CQ025']['cypher'] for x in ['38.201','38.202','38.291'])
    design = read('authority/original_phase3_TS_design.md').decode().splitlines()
    assert all(s in design[62] for s in ['38.201','38.202','38.211','38.212','38.213','38.214','38.215','38.291'])
    assert all(s in design[208] for s in ['38.201','38.202','38.211-215','38.291'])
    assert '모든 클래스, 관계, 인스턴스' in design[51]
    assert 'references하는 경우만' in design[206]
    assert '위 전체 조합' in design[290]
    p2 = read('authority/HEAD_phase2_FinalReport_design.md').decode().splitlines()
    assert 'content 내 참조' in p2[1309] and '기존 인스턴스에 references 관계 생성' in p2[1320]
    assert 'references 관계 생성 안 함' in p2[1321]
    criteria = load('canonical/criteria.json')
    review = load('primary_exact_eight_scope_recorded_count_seven_unit_review.json')
    review_schema.check_pass(review,task['question_en'],criteria['semantic_units'],criteria_sha=sha(read('canonical/criteria.json')),identity_key='repair_sha256',identity_sha=digest)
    assert review['reviewer_agent'] == '/root/verify_public467_readonly' and review['expert_validation_n'] == 0

    x = json.loads(gzip.decompress(read('unfiltered_identity_and_relation_operands.json.gz')))
    assert {k:len(v) for k,v in x.items()} == EXPECTED_METADATA['whole_operand_rows']
    agr = set(x['Agreement']); cr = set(x['CR']); sp = dict(x['Spec'])
    specs = ['38.201','38.202','38.211','38.212','38.213','38.214','38.215','38.291']
    assert set(specs) <= set(sp.values())
    target = collections.defaultdict(set); cm = {s:set() for s in specs}; am = {s:set() for s in specs}
    for a,b in x['MODIFIES']:
        if a in cr and b in sp:
            target[a].add(sp[b])
            if sp[b] in cm:cm[sp[b]].add(a)
    for a,b in x['REFERENCES']:
        if a in agr and b in cr:
            for s in target[b]:
                if s in am:am[s].add(a)
    records = sorted([{'ts':s,'crCnt':len(cm[s]),'agrCnt':len(am[s])} for s in specs],key=lambda r:(-r['crCnt'],r['ts']))
    assert records == [json.loads(x) for x in read('repaired_eight_reference_records.jsonl').decode().splitlines()]
    exact = load('actual_exact_repaired_query_SQL_equivalence.json')
    assert exact['rows'] == records and exact['all24typed_equal_independent_whole_operand_Python'] is True
    old = load('actual_original_SQL_saved_native_and_all8_counterpolicy.json')
    five = [r for r in records if r['ts'] in ['38.211','38.212','38.213','38.214','38.215']]
    assert old['original_five_records'] == five and old['saved_original_five_native']['full15_typed_values_equal'] is True
    assert load('old_original_native_rows.json') == [[r['ts'],r['crCnt'],r['agrCnt']] for r in five]
    oldreceipt = load('old_original_native_receipt.json')['execution']
    assert oldreceipt['query_utf8_sha256'] == sha(task['original_query'].encode())
    assert oldreceipt['row_count_retained'] == 5 and oldreceipt['columns'] == ['ts','crCnt','agrCnt']
    assert oldreceipt['rollback_completed'] and not oldreceipt['truncated']
    assert len(records) == 8 and len(five) == 5
    assert {r['ts'] for r in records if r['agrCnt'] == 0} == {'38.201','38.291'}

    # Preserve and replay the physical source counterexample, not merely a prose
    # assertion that this frozen operation is complete.
    raw = load('actual_raw_report_witnesses.json')
    W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    reports = {}
    for packet in raw['source_packets']:
        blocks = {}
        for block in packet['blocks']:
            assert sha(ET.tostring(ET.fromstring(block['XML']))) == block['ET_serialization_sha256']
            text = ''.join(t.text or '' for t in ET.fromstring(block['XML']).iter(W+'t'))
            assert text == block['text']; blocks[block['raw_body_child0']] = text
        reports[packet['report']] = blocks
    b = reports['123']
    assert b[486]=='Agreement' and '38.213' in b[487] and 'endorsed' in b[487]
    assert 'Final CRs capturing the above TPs' in b[494]
    assert b[495]=='R1-2509603CR for TS 38.213 on RACH-less handoverNEC, vivo, Samsung, Ericsson'
    assert b[497]=='R1-2509604CR for TS 38.213 on RACH-less handoverNEC, vivo, Samsung, Ericsson'
    retained = load('bounded_retained_witnesses.json')
    assert retained['source_reopen_receipt']['all_decoded_node_records_checked'] == 165418
    a = retained['own_Agreement_all_properties']
    assert a['node_id']==13604 and a['resolutionId']=='AGR-123-7-011'
    assert a['content']==b[487] and a['note'] is None and a['contentWithEquations'] is None
    assert not any(src==13604 for src,dst in x['REFERENCES'])
    assert target[157359] == target[157360] == {'38.213'}
    expanded = set(am['38.213']); expanded.add(13604)
    assert len(am['38.213'])==493 and len(expanded)==494
    tp = retained['generic_TS_body_counterpolicy']['actual_Agreement']
    assert tp['node_id']==10022 and 'Adopt the following TP' in reports['116'][2220]
    assert '38.213' in tp['content'] and not any(src==10022 for src,dst in x['REFERENCES'])

    controls=[]
    def check(name,pred,want):
        result=scorer.score(task,records,pred,diagnostic=True)
        assert result['exact'] is want,(name,result)
        controls.append((name,want))
    check('all8_typed_three_fields',records,True)
    check('unrequested_serialization_reverse',list(reversed(records)),True)
    check('unrequested_ratio_column_does_not_change_required_count_fields',[dict(r,ratio='not scored') for r in records],True)
    check('specific_five_filter_omits_three_in_scope_families',five,False)
    check('zero_Agreement_families_cannot_be_dropped',[r for r in records if r['agrCnt']],False)
    for i,r in enumerate(records):check('missing_family_'+r['ts'],records[:i]+records[i+1:],False)
    for key in ['ts','crCnt','agrCnt']:
        z=copy.deepcopy(records);del z[0][key];check('missing_required_'+key,z,False)
    for key in ['crCnt','agrCnt']:
        z=copy.deepcopy(records);z[0][key]+=1;check('wrong_'+key,z,False)
        for value in [str(records[0][key]),True,None,float(records[0][key])]:
            z=copy.deepcopy(records);z[0][key]=value;check('wrong_type_'+key+'_'+type(value).__name__,z,False)
    z=copy.deepcopy(records);z[0]['ts']='36.213';check('outside_family_substituted',z,False)
    z=copy.deepcopy(records);z[0]['crCnt'],z[1]['crCnt']=z[1]['crCnt'],z[0]['crCnt'];check('CR_counts_reassigned_to_wrong_TS',z,False)
    z=copy.deepcopy(records);z[0]['crCnt'],z[0]['agrCnt']=z[0]['agrCnt'],z[0]['crCnt'];check('CR_and_Agreement_roles_swapped',z,False)
    z=copy.deepcopy(records);z[0]['agrCnt']=494;check('source_enriched_count_not_frozen_recorded_count',z,False)
    check('all51_CR_target_scope_not_original_Phase3_domain',[{k:r[k] for k in ['ts','crCnt','agrCnt']} for r in old['all51_aggregate_count_vs_distinct']],False)
    archived=load('actual_typed_scorer_controls.json')
    assert len(controls)==archived['controls_n']==31
    assert controls==[(r['name'],r['expected_exact']) for r in archived['controls']]
    secondary = load('ROOT_secondary_exact_seven_unit_eight_scope_review.json')
    review_schema.check_pass(secondary,task['question_en'],criteria['semantic_units'],criteria_sha=sha(read('canonical/criteria.json')),identity_key='repair_sha256',identity_sha=digest)
    assert secondary['reviewer_agent']=='/root' and secondary['reviewer_agent']!=review['reviewer_agent']
    assert secondary['expert_validation_n']==0 and secondary['blind'] is False
    root_sql=load('ROOT_actual_independent_generic_SQL_eight.json')
    assert root_sql['status']=='PASS' and root_sql['rows']==records and root_sql['typed_values']==24
    assert root_sql['database']['sha256']=='aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
    assert EXPECTED_METADATA['ROOT_secondary_review_included'] is True
    assert EXPECTED_METADATA['new_exact_eight_native_included'] is True
    assert EXPECTED_METADATA['final_admission_ready'] is False

    # Only included actual native8 artifacts can close this gate. The original
    # five-row native result stays separately checked above, never substituted.
    assert EXPECTED_METADATA['new_exact_eight_native_included'] is True
    assert EXPECTED_METADATA['final_admission_ready'] is False
    assert EXPECTED_METADATA['actual_native_rows'] == 8
    nreceipt=load('native/repaired_query_receipt.json')
    raw_native=read('native/repaired_query_rows.jsonl')
    arrays=[json.loads(x)for x in raw_native.decode().splitlines()]
    assert nreceipt['query']==task['reference_query']
    assert nreceipt['query_sha256']==sha(task['reference_query'].encode())
    assert nreceipt['rows_sha256']==sha(raw_native)
    assert nreceipt['status']=='OK' and nreceipt['columns']==['ts','crCnt','agrCnt']
    assert nreceipt['rows_retained']==8 and nreceipt['bytes_retained']==len(raw_native)
    assert nreceipt['truncated'] is False and nreceipt['full_rows_available'] is True
    assert nreceipt['rollback_completed'] is True and nreceipt['execution_summary_complete'] is True
    assert nreceipt['plan_query_type']==nreceipt['execution_query_type']=='r'
    assert all(len(row)==3 and type(row[0])is str and type(row[1])is int and type(row[2])is int for row in arrays)
    native=[dict(zip(nreceipt['columns'],row))for row in arrays]
    assert len(native)==8 and [scorer.record_token(r,task['required_fields'])for r in native]==[scorer.record_token(r,task['required_fields'])for r in records]
    assert scorer.score(task,records,native,diagnostic=True)['exact'] is True
    execution=load('native/execution_RAN1.json')
    assert execution['source_before']==execution['source_after'] and execution['inventory_unchanged'] is True
    source=execution['source_before']
    assert source['nodes']==165418 and source['relationships']==848228
    assert source['source']['sha256']=='9540683df5407bb3f8978ad4d05ddc7f7880f10c94f21273f588d737f145e231'
    assert execution['input_sha256']==sha(read('native/exact_input.jsonl'))
    assert execution['protocol_sha256']==sha(read('native/execution_protocol.json'))
    assert execution['runner_sha256']==sha(read('native/execute_candidates_original.py'))
    assert execution['items']==[{'id':task['id'],'status':'OK','query_sha256':nreceipt['query_sha256'],'rows':8}]
    protocol=load('native/execution_protocol.json')
    assert protocol['container_memory_bytes']==2*1024**3 and protocol['container_cpu_cores']==1
    assert protocol['model_calls']==0 and protocol['same_count_external_property_changes_detected'] is False
    guard=load('native/outer_guard_receipt.json')
    assert guard['status']=='PASS' and guard['child_started'] is True and guard['child_exit']==0 and guard['failure'] is None
    assert guard['scope_sha256']==sha(read('definition.json'))
    assert guard['wrapper_sha256']==sha(read('native/ROOT_outer_native_reserve_guard.py'))
    assert guard['owned_cleanup']['owned_stopped'] is True and guard['owned_cleanup']['common_lock_held'] is True
    assert guard['quality_rerolls']==0
    assert guard['prestart_available_minimum_bytes']==26*1024**3
    assert guard['continuous_reserve_minimum_bytes']==16*1024**3
    assert min(guard['initial_memory'].values())>=26*1024**3
    assert all(min(s['Linux_available_bytes'],s['Windows_available_bytes'])>=16*1024**3 for s in guard['memory_samples'])
    observations=[json.loads(x)for x in read('native/fresh_CIM_observations.jsonl').decode().splitlines()]
    assert len(observations)==len({x['nonce']for x in observations})
    assert all(x['status']=='FRESH_NUMERIC_OBSERVATION' and x['cached_values_used']==0 and x['Get_CimInstance_calls_for_this_request']==1 and type(x['windows_available_bytes'])is int and x['windows_available_bytes']>0 for x in observations)
    fresh_values={x['windows_available_bytes']for x in observations}
    resources=[json.loads(x)for x in read('native/resource_checks.jsonl').decode().splitlines()]
    assert all(x['windows_available_bytes']in fresh_values and min(x['linux_available_bytes'],x['windows_available_bytes'])>=26*1024**3 for x in resources)
    coordinator=load('native/coordinator.json')
    assert coordinator['status']=='NATIVE_WRAPPER_PASS_PENDING_SCIENTIFIC_BINDING' and 'failure' not in coordinator
    assert type(coordinator['child_exit']) is int and coordinator['child_exit']==0
    assert coordinator['guard_sha256']==guard['wrapper_sha256']
    assert type(coordinator['paid_API_calls']) is int and coordinator['paid_API_calls']==0
    assert type(coordinator['public_mutations']) is int and coordinator['public_mutations']==0
    # Strict schema/type/nonvacuity checks; native execution is still required.
    assert type(guard['child_exit']) is int and guard['child_exit'] == 0
    assert type(guard['quality_rerolls']) is int and guard['quality_rerolls'] == 0
    assert set(guard['initial_memory']) == {'Linux_available_bytes','Windows_available_bytes'}
    assert all(type(v) is int and v >= 26*1024**3 for v in guard['initial_memory'].values())
    assert type(guard['memory_samples']) is list and len(guard['memory_samples']) > 0
    assert all(type(s[k]) is int and s[k] >= 16*1024**3 for s in guard['memory_samples'] for k in ('Linux_available_bytes','Windows_available_bytes'))
    assert all(type(s['elapsed_seconds']) in (int,float) and s['elapsed_seconds'] >= 0 for s in guard['memory_samples'])
    assert type(observations) is list and len(observations) > 0
    assert all(type(x['nonce']) is str and len(x['nonce']) == 32 and all(c in '0123456789abcdef' for c in x['nonce']) for x in observations)
    assert all(type(x['cached_values_used']) is int and x['cached_values_used'] == 0 and type(x['Get_CimInstance_calls_for_this_request']) is int and x['Get_CimInstance_calls_for_this_request'] == 1 for x in observations)
    assert guard['initial_memory']['Windows_available_bytes'] in fresh_values
    assert all(s['Windows_available_bytes'] in fresh_values for s in guard['memory_samples'])
    assert type(resources) is list and len(resources) > 0
    assert all(type(x[k]) is int for x in resources for k in ('linux_available_bytes','windows_available_bytes'))
    assert len({x['session'] for x in observations})==1
    capture=read('native/capture_native_original.py').decode()
    assert "fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)" in capture and "native_capture.lock" in capture
    assert load('actual_exact_eight_native_SQL_typed_binding.json')['all24typed_native_equals_independent_SQL_and_whole_operands'] is True
    adapted = load('native/exact_input.jsonl')
    original = load('preserved_first_input_schema_failure/original_input.jsonl')
    assert set(adapted)=={'id','wg','status','candidate_query'}
    assert adapted['id']==original['id']==task['id'] and adapted['wg']==original['wg']=='RAN1'
    assert adapted['status']=='development_probe' and adapted['candidate_query']==original['cypher']==task['reference_query']
    previous=load('preserved_first_input_schema_failure/outer_guard_receipt.json')
    assert previous['status']=='FAIL_PRESERVED' and previous['child_exit']==1
    assert "KeyError: 'status'" in read('preserved_first_input_schema_failure/stderr').decode()
    assert nreceipt['id']==task['id'] and nreceipt['wg']=='RAN1'
    assert execution['model_calls']==0 and execution['expert_validation'] is False
    assert sha(read('native/exact_input.jsonl'))=='777b06097fd48374ba64dfc1e7391872c2ad1a95b50ca69fef6238bdaead0039'

    print(json.dumps({'status':'PASS_CQ040_SOURCE_CONTEXT_COUNT_REPLAY','id':task['id'],
      'repair_sha256':digest,'complete_SQL_Python_rows':8,'old_original_native_rows':5,
      'controls':len(controls),'separate_AI_source_reviews':2,'exact_eight_native_included':True,'actual_native_rows':8,'actual_native_typed_values':24,'source_complete_count_certified':False,
      'counterfactual_source_Agreement_count':[493,494],'new_native_calls':0,'new_API_calls':0,
      'expert_validation_n':0,'new_original_core_admissions':0},ensure_ascii=False))

if __name__=='__main__':main()
