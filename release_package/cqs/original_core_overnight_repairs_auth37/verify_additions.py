"""Verify the one sealed original recorded-contribution addition offline."""
import argparse,hashlib,importlib.util,json,os,stat,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
if sys.flags.optimize:raise ValueError('Enabled checks required; -O/-OO forbidden')
INVENTORY_SHA='cc8b5e454315b1e2443be082e45cbef2e831aeae597f0f9efb3746adcc107d2a'
SEAL_SHA='4c9e3e578cda0fc4a4a222ae90b819450899bc5199d625b22a31356327ab11b0'
SOURCE_SHA='8f04a2a156a590bf845eb44f880eebcc5d7c6e97c13c49149ae2b365c8a57a06'
ID='RAN2_P2_CQ3-3'
REPAIR='bdf997f06492063fce39de80bca72378d557151ff81f0b1df846c9a9ec0e9a07'
CRITERIA='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
def need(ok,msg):
    if not ok:raise ValueError(msg)
def safe(path):
    path=Path(os.path.abspath(path))
    for p in [path,*path.parents]:need(not p.is_symlink(),'Symlink input or ancestor')
    mode=path.lstat().st_mode
    need(stat.S_ISREG(mode) or stat.S_ISDIR(mode),'Nonregular package input')
    return path
def sha(p):return hashlib.sha256(safe(p).read_bytes()).hexdigest()
def pairs(items):
    d={}
    for k,v in items:need(k not in d,'Duplicate JSON key');d[k]=v
    return d
def load(p):return json.loads(safe(p).read_text(),object_pairs_hook=pairs)
def exact(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)
def lines(p):return [json.loads(s,object_pairs_hook=pairs) for s in safe(p).read_text().splitlines() if s.strip()]
def verify(bundle):
    bundle=safe(bundle);need(safe(__file__)==bundle/'verify_additions.py','Use package own verifier')
    need(sha(bundle/'immutable_inventory.json')==INVENTORY_SHA,'Immutable inventory differs')
    inventory=load(bundle/'immutable_inventory.json')['files'];manifest=load(bundle/'manifest.json');declarations=load(bundle/'declarations.json')
    need(set(manifest)==set(declarations)|{'files','immutable_inventory_sha256','verifier_sha256'},'Manifest key set')
    need(exact({k:manifest[k] for k in declarations})==exact(declarations),'Scientific declarations differ')
    need(manifest['files']==inventory and manifest['immutable_inventory_sha256']==INVENTORY_SHA and manifest['verifier_sha256']==sha(bundle/'verify_additions.py'),'Manifest fixed identities')
    actual=set()
    for p in bundle.rglob('*'):
        safe(p)
        if p.is_file():actual.add(str(p.relative_to(bundle)))
    need(actual==set(inventory)|{'verify_additions.py','immutable_inventory.json','manifest.json'},'Closed package inventory differs')
    for name,pin in inventory.items():
        rel=Path(name);need(not rel.is_absolute() and '..' not in rel.parts,'Nonrelative inventory path')
        need(type(pin['bytes']) is int and (bundle/rel).stat().st_size==pin['bytes'] and sha(bundle/rel)==pin['sha256'],'Payload differs: '+name)
    need(exact(declarations['accounting'])==exact({'candidate_n':1,'local_validated_n':1,'new_public_admissions':0,'new_API_calls':0,'human_expert_n':0,'nonblind_AI':True}),'Accounting differs')
    seal=load(bundle/'gate_evidence/ROOT_final_disposition.json')
    need(sha(bundle/'gate_evidence/ROOT_final_disposition.json')==SEAL_SHA and seal['decision']=='pass_local' and seal['repair_sha256']==REPAIR and seal['criteria_sha256']==CRITERIA,'ROOT seal identity')
    source=bundle/'source_evidence'/ID
    need(sha(source/'manifest.json')==SOURCE_SHA==seal['portable_manifest']['sha256'],'Immutable V7 source differs')
    child=subprocess.run([sys.executable,'-B','-I','-S',str(source/'verify.py')],cwd=bundle,capture_output=True,text=True,timeout=180,env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'})
    need(child.returncode==0,'Source portable replay failed: '+child.stderr)
    replay=json.loads(child.stdout,object_pairs_hook=pairs)
    need(replay['status']=='PASS' and replay['repair_sha256']==REPAIR and replay['actual_limited_native_records']==5 and replay['full_native_WI_company_groups']==1939 and replay['source_role_failures']==0 and replay['production_controls']==56,'Source/native/production closure')
    sys.path[:0]=[str(bundle),str(bundle/'outer_WI_metrics')]
    import scorer,review_schema,verify_release
    definition=load(bundle/'definition.json');criteria=load(bundle/'criteria.json')
    need(set(definition)==set(verify_release.DEFINITION_KEYS) and verify_release.digest(definition)==REPAIR and sha(bundle/'criteria.json')==CRITERIA,'Exact definition/criteria')
    tasks=lines(bundle/'tasks.jsonl');gold=lines(bundle/'reference_gold.jsonl')
    need(len(tasks)==len(gold)==1,'One unchanged question')
    task=tasks[0]
    need(task['id']==ID and task['repair_sha256']==REPAIR and task['validation_status']=='validated' and task['admitted'] is False,'Local ROOT-validated envelope')
    need(exact({k:task[k] for k in verify_release.DEFINITION_KEYS})==exact(definition),'Task nine-key definition differs')
    need(task['ROOT_final_disposition_sha256']==SEAL_SHA and task['validation_provenance']=='ROOT sealed local pass; public and API registration remain separate','Task validation source')
    reviews=[load(bundle/'gate_evidence'/(role+'.json')) for role in ['primary','secondary']]
    for r in reviews:review_schema.check_pass(r,definition['question_en'],criteria['semantic_units'],criteria_sha=CRITERIA,identity_key='repair_sha256',identity_sha=REPAIR)
    need(reviews[0]['reviewer_identity']!=reviews[1]['reviewer_identity'],'Distinct independent reviewers')
    limited=lines(bundle/'actual_limited_native_records.jsonl')
    need(gold[0]=={'id':ID,'repair_sha256':REPAIR,'records':limited,'order_groups':None} and len(limited)==5,'Actual limited native exemplar')
    spec=importlib.util.spec_from_file_location('declared_partition_reader',bundle/'score_predictions_partitioned_reader.py')
    reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
    positive=reader.run(bundle/'tasks.jsonl',bundle/'reference_gold.jsonl',bundle/'actual_native_prediction_envelope.jsonl')['outcomes'][0]
    need(positive['exact'] is True and positive['diagnostic_only'] is False and positive['matched_records']==5,'Production native bridge')
    import score_predictions_partitioned_dispatch as dispatch
    policy=load(bundle/'nested_eligibility_policy.json');population=load(bundle/'full_native_partition_population.json');declaration=load(bundle/'dispatch_declaration.json')
    tests=load(bundle/'controls/actual_original_five_tie_diagnostic_controls.json')
    need(tests['lawful_combinations']==5 and len(tests['controls'])==56,'Five lawful tie choices/56 controls')
    for test in tests['controls']:
        result=dispatch.run(task,definition,policy,limited,population,{'id':ID,'repair_sha256':REPAIR,'records':test['input']},declaration)
        need(result['exact'] is test['expected']['exact'] and result['diagnostic_only'] is False,'Production answer control: '+test['name'])
        for key in ['matched_records','precision','recall','f1']:
            expected=test['expected'].get(key)
            if expected is not None:need(abs(result[key]-expected)<=1e-12,'Complete outer-WI metric: '+test['name'])
    return {'status':'PASS','candidate_n':1,'local_validated_n':1,'new_public_admissions':0,'new_API_calls':0,'human_expert_validation_n':0,'items':[{'id':ID,'repair_sha256':REPAIR,'native_limited_records':5,'full_eligibility_groups':1939,'lawful_nested_answers':5,'production_answer_controls':56,'diagnostic_only':False,'metric_unit':'one complete WI record'}],'graph_sources':declarations['graph_sources'],'explicit_analysis_reader':'score_predictions_partitioned_reader.py','source_replay':replay}
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--bundle',type=Path,required=True);args=parser.parse_args();print(json.dumps(verify(args.bundle),sort_keys=True))
