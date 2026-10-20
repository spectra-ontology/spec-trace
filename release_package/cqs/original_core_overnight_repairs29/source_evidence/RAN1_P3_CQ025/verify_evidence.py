#!/usr/bin/env python3
"""Offline CQ025 recorded-path evidence replay; no native/API/host fallback."""
import sys
if sys.flags.optimize != 0:
    raise RuntimeError('Assertions require a nonoptimized interpreter')
sys.dont_write_bytecode = True
from pathlib import Path
import collections
import gzip
import hashlib
import json
import xml.etree.ElementTree as ET

INVENTORY_SHA256 = 'ef344842fa8b6bc88b3744f01a82bde9e0ddcf0363220f74c0d9dedda85f7585'
EXPECTED_METADATA = {'id': 'RAN1_P3_CQ025', 'artifact_type': 'locally_verified_recorded_operation_source_evidence', 'repair_sha256': '1b34342bbca25d16847a744ff5f35b086ea87298262a7239d898ac5452584206', 'question_sha256': '5436ccbd126c32691ddf5d703ba9e70bdb01001414eb185c8439cf09eab89f9d', 'criteria_sha256': 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4', 'full_operand_rows': {'Agreement': 21058, 'CR': 10715, 'Spec': 127, 'REFERENCES': 19454, 'MODIFIES': 10671}, 'recorded_query_rows': 8, 'zero_TS_rows': 2, 'old_saved_native_rows': 6, 'repaired_native8_included': True, 'ROOT_secondary_review_included': True, 'native_binding_required_before_final_admission': False, 'source_reference_extension_count': [493, 494], 'source_complete_count_certified': False, 'new_original_core_admissions': 0, 'expert_validation_n': 0, 'blind': False, 'source_role': 'original recorded REFERENCES operation, distinct from source-enriched citation reconstruction', 'verifier_scope': 'closed included file inventory; source excerpts/complete operand count replay/canonical typed31 controls; no API/native/host DB or source fallback', 'final_status': 'two_AI_source_reviews_SQL_Python_actual_native8_and_typed_controls_pass_ROOT_seal_pending', 'source_completeness_certified': False, 'actual_native_rows': 8}

def no_symlink(p):
    p = Path(p)
    for x in (p, *p.parents):
        if x.is_symlink():
            raise RuntimeError('Symlink boundary: '+str(x))
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
        raise RuntimeError('No external source/native path accepted by this source-only verifier')
    inv_raw = read('immutable_inventory.json')
    assert sha(inv_raw) == INVENTORY_SHA256
    inv = json.loads(inv_raw)
    manifest = load('manifest.json')
    assert set(manifest) == {'metadata','inventory','verifier_sha256'}
    assert json.dumps(manifest['metadata'],sort_keys=True,separators=(',',':')) == json.dumps(EXPECTED_METADATA,sort_keys=True,separators=(',',':'))
    assert type(manifest['metadata']['expert_validation_n']) is int
    assert type(manifest['metadata']['new_original_core_admissions']) is int
    assert manifest['inventory'] == {'path':'immutable_inventory.json','sha256':INVENTORY_SHA256,'bytes':len(inv_raw)}
    assert manifest['verifier_sha256'] == sha(read('verify_evidence.py'))
    files = set()
    for p in PACKAGE_ROOT.rglob('*'):
        no_symlink(p)
        if not (p.is_file() or p.is_dir()):
            raise RuntimeError('Unsupported filesystem entry')
        if p.is_file():
            files.add(p.relative_to(PACKAGE_ROOT).as_posix())
    assert files == set(inv['files']) | {'manifest.json','immutable_inventory.json','verify_evidence.py'}
    for name, value in inv['files'].items():
        b = read(name)
        assert value == {'bytes':len(b),'sha256':sha(b)}, name

    task = load('definition.json')
    fields = ('id','question_en','original_query','reference_query','required_fields',
              'collection','cardinality_policy','repair_class','original_question_preserved')
    sys.path.insert(0, str(PACKAGE_ROOT/'canonical'))
    import scorer
    digest = sha(scorer.get_kernel().json_exact({k:task[k] for k in fields}).encode())
    assert digest == task['repair_sha256'] == EXPECTED_METADATA['repair_sha256']
    orig = load('original_authority_and_question.json')['original']
    assert task['question_en'] == orig['question_en'] and task['original_query'] == orig['original_query']
    assert sha(task['question_en'].encode()) == orig['question_sha256']
    assert sha(task['original_query'].encode()) == orig['original_query_sha256']
    cq = read('authority/original_CQ025.cypher').decode()
    assert task['question_en'] in cq and task['original_query'] in cq
    csv_lines = read('authority/HEAD_cq_all_137.csv').decode().splitlines()
    assert csv_lines[84].startswith('3,CQ025,Resolution_TS_의사결정,TS별로 관련된 Agreement 수를 요약해줘.')
    design = read('authority/original_phase3_TS_design.md').decode().splitlines()
    assert 'Resolution이 CR을 references하는 경우만' in design[165]
    assert all(s in design[208] for s in ['38.201','38.202','38.211-215','38.291'])
    p2 = read('authority/HEAD_phase2_FinalReport_design.md').decode().splitlines()
    assert 'content 내 참조' in p2[1309] and '패턴 추출' in p2[1309]
    assert '기존 인스턴스에 references 관계 생성' in p2[1320]
    assert 'references 관계 생성 안 함' in p2[1321]

    operands = json.loads(gzip.decompress(read('unfiltered_identity_and_relation_operands.json.gz')))
    assert {k:len(v) for k,v in operands.items()} == EXPECTED_METADATA['full_operand_rows']
    agreements = set(operands['Agreement'])
    crs = set(operands['CR'])
    specs = dict(operands['Spec'])
    domain = ['38.201','38.202','38.211','38.212','38.213','38.214','38.215','38.291']
    assert set(domain) <= set(specs.values())
    targets = collections.defaultdict(set)
    for src,dst in operands['MODIFIES']:
        if src in crs and dst in specs and specs[dst] in domain:
            targets[src].add(specs[dst])
    members = {s:set() for s in domain}
    for src,dst in operands['REFERENCES']:
        if src in agreements and dst in crs:
            for s in targets.get(dst, set()): members[s].add(src)
    records = sorted([{'specNumber':s,'agrCount':len(ids)} for s,ids in members.items()],
                     key=lambda r:(-r['agrCount'],r['specNumber']))
    sql_rows = [json.loads(x) for x in read('repaired_full_eight_SQL_records.jsonl').decode().splitlines()]
    assert records == sql_rows and len(records) == 8
    assert {r['specNumber'] for r in records if r['agrCount'] == 0} == {'38.201','38.291'}
    old = load('actual_original_SQL_and_saved_native_typed_agreement.json')
    assert old['saved_native_positional_records'] == [[r['specNumber'],r['agrCount']] for r in records if r['agrCount']]
    assert len(old['saved_native_positional_records']) == 6
    assert old['six_native_rows_are_not_eight_native_rows'] is True

    raw = load('actual_raw_report_witnesses.json')
    W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    by_report = {}
    for packet in raw['source_packets']:
        blocks={}
        for block in packet['blocks']:
            assert sha(ET.tostring(ET.fromstring(block['XML']))) == block['ET_serialization_sha256']
            e = ET.fromstring(block['XML'])
            assert ''.join(t.text or '' for t in e.iter(W+'t')) == block['text']
            blocks[block['raw_body_child0']] = block['text']
        by_report[packet['report']] = blocks
    b = by_report['123']
    assert b[486] == 'Agreement' and '38.213' in b[487] and 'endorsed' in b[487]
    assert 'Final CRs capturing the above TPs' in b[494]
    assert b[495] == 'R1-2509603CR for TS 38.213 on RACH-less handoverNEC, vivo, Samsung, Ericsson' and b[497] == 'R1-2509604CR for TS 38.213 on RACH-less handoverNEC, vivo, Samsung, Ericsson'
    assert 'Rel-18' in b[496] and 'Rel-19' in b[498]
    b = by_report['116']
    assert b[2219] == 'Agreement' and 'Adopt the following TP' in b[2220]
    assert '38.213' in b[2220] and 'beam application time for LTM' in b[2221]
    assert b[2231] == 'Agreement'
    retained = load('bounded_retained_witnesses.json')
    assert retained['source_reopen_receipt']['all_decoded_node_records_checked'] == 165418
    own = retained['own_Agreement_all_properties']
    assert own['node_id'] == 13604 and own['resolutionId'] == 'AGR-123-7-011'
    assert own['content'] == by_report['123'][487]
    assert own['contentWithEquations'] is None and own['note'] is None
    assert not any(src == 13604 for src,dst in operands['REFERENCES'])
    assert targets[157359] == targets[157360] == {'38.213'}
    ext = {s:set(v) for s,v in members.items()}
    for dst in [157359,157360]:
        for s in targets[dst]: ext[s].add(13604)
    assert len(members['38.213']) == 493 and len(ext['38.213']) == 494
    tp = retained['generic_TS_body_counterpolicy']['actual_Agreement']
    assert tp['node_id'] == 10022 and 'Adopt the following TP' in tp['content'] and '38.213' in tp['content']
    assert not any(src == 10022 for src,dst in operands['REFERENCES'])

    controls = load('actual_typed_scorer_controls.json')
    # Replay the meaningful alternatives from current records and canonical bytes.
    positive = [records,list(reversed(records)),records+[records[0]],
                [dict(r,extra_display_title='unrequested') for r in records]]
    negative = [[r for r in records if r['agrCount']],[]]
    for i in range(8):
        rows=[dict(r) for r in records]; rows[i]['agrCount']+=1; negative.append(rows)
        rows=[dict(r) for r in records]; rows[i]['specNumber']='38.999'; negative.append(rows)
    for value in ['493',493.0,True,None]:
        rows=[dict(r) for r in records]; rows[0]['agrCount']=value; negative.append(rows)
    for field in ['specNumber','agrCount']:
        rows=[dict(r) for r in records]; del rows[0][field]; negative.append(rows)
    rows=[dict(r) for r in records];rows[0]['agrCount'],rows[1]['agrCount']=rows[1]['agrCount'],rows[0]['agrCount'];negative.append(rows)
    negative.append(records+[{'specNumber':'38.999','agrCount':0}])
    rows=[dict(r) for r in records];rows[0]['agrCount']=494;negative.append(rows)
    assert len(positive)+len(negative)==controls['controls_n']==31
    for rows in positive: assert scorer.score(task,records,rows,diagnostic=True)['exact'] is True
    for rows in negative: assert scorer.score(task,records,rows,diagnostic=True)['exact'] is False
    import review_schema
    criteria=load('authority/criteria.json')
    primary=load('primary_exact_recorded_documentary_count_seven_unit_review.json')
    secondary=load('ROOT_secondary_exact_seven_unit_recorded_count_review.json')
    assert primary['reviewer_agent']=='/root/verify_public467_readonly'
    assert secondary['reviewer_agent']=='/root'
    for review in [primary,secondary]:
        review_schema.check_pass(review,task['question_en'],criteria['semantic_units'],
            criteria_sha=EXPECTED_METADATA['criteria_sha256'],identity_key='repair_sha256',identity_sha=digest)
        assert review['expert_validation_n']==0 and review['blind'] is False
    assert secondary['source_enrichment_for_native_or_gold'] is False
    root=load('ROOT_actual_source_SQL_native_replay.json')
    assert root['status']=='PASS' and root['repair_sha256']==digest
    assert root['all_eight_typed_rows']==records
    assert root['fresh_SQL_equals_exact_native_all8'] is True
    assert root['source_faithful_citation_completeness_certified'] is False
    for report in root['raw_own_source_reopens']:
        packet=next(x for x in raw['source_packets'] if x['DOCX']['sha256']==report['sha256'])
        assert report['own_blocks_compared']==len(packet['blocks'])==19
    nreceipt=load('native/repaired_query_receipt.json')
    raw_native=read('native/repaired_query_rows.jsonl')
    arrays=[json.loads(x)for x in raw_native.decode().splitlines()]
    assert nreceipt['query']==task['reference_query']
    assert nreceipt['query_sha256']==sha(task['reference_query'].encode())
    assert nreceipt['rows_sha256']==root['native_rows_file']['sha256']==sha(raw_native)
    assert nreceipt['status']=='OK' and nreceipt['columns']==['specNumber','agrCount']
    assert nreceipt['rows_retained']==8 and nreceipt['bytes_retained']==len(raw_native)
    assert nreceipt['truncated'] is False and nreceipt['full_rows_available'] is True
    assert nreceipt['rollback_completed'] is True and nreceipt['execution_summary_complete'] is True
    assert nreceipt['plan_query_type']==nreceipt['execution_query_type']=='r'
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
    assert coordinator['status']=='PASS' and coordinator['failure'] is None and coordinator['new_API_calls']==0
    capture=read('native/capture_native_original.py').decode()
    assert "fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)" in capture and "native_capture.lock" in capture
    assert root['native_receipt_file']['sha256']==sha(read('native/repaired_query_receipt.json'))
    for name in ['ROOT_preserved_native_shape_checker_failure.json','ROOT_preserved_independent_SQL_schema_failure.json']:
        assert load('native/'+name)['status']=='FAIL_PRESERVED'

    print(json.dumps({'status':'PASS_OFFLINE_RECORDED_COUNT_AND_PRESERVED_SOURCE_COUNTEREVIDENCE',
        'id':task['id'],'repair_sha256':digest,'full_operand_rows':EXPECTED_METADATA['full_operand_rows'],
        'SQL_Python_records':8,'old_saved_native_records':6,'repaired_native8_included':True,
        'actual_native_rows':8,'two_distinct_AI_reviews':2,'typed_controls':31,'source_reference_extension_count':[493,494],
        'source_completeness_certified':False,'new_native_calls':0,'new_API_calls':0,
        'new_original_core_admissions':0,'expert_validation_n':0},ensure_ascii=False))

if __name__ == '__main__':
    main()
