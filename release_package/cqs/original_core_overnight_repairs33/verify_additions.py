#!/usr/bin/env python3
"""Replay the exact PUSCH original-question addition; no API/live database calls."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

sys.dont_write_bytecode=True
if sys.flags.optimize:
    raise SystemExit('Verification requires enabled checks; -O/-OO refused.')
INVENTORY_SHA256='f3c155b007f3a0a5772691409bfb64584bacba15854360a5bd16e8843a62f4de'
ID='RAN1_P2_CQ5-5'


def require(ok,message):
    if not ok:raise ValueError(message)


def safe(path):
    path=Path(os.path.abspath(path))
    for parent in (path,*path.parents):
        require(not parent.is_symlink(),'symlink forbidden: '+str(parent))
    if path.exists():
        require(stat.S_ISDIR(path.lstat().st_mode) or stat.S_ISREG(path.lstat().st_mode),'nonregular entry')
    return path


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(safe(path).read_text())
def lines(path):return [json.loads(s)for s in safe(path).read_text().splitlines()if s.strip()]


def local(bundle,name):
    spec=importlib.util.spec_from_file_location(name,safe(bundle/(name+'.py')))
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return module


def verify(bundle,release_root=None):
    bundle=safe(bundle)
    require(safe(__file__)==bundle/'verify_additions.py','execute bundle own verifier')
    require(sha(bundle/'immutable_inventory.json')==INVENTORY_SHA256,'fixed payload inventory changed')
    files=load(bundle/'immutable_inventory.json')['files']
    manifest=load(bundle/'manifest.json');declarations=load(bundle/'declarations.json')
    require(manifest['files']==files and manifest['immutable_inventory_sha256']==INVENTORY_SHA256,'manifest inventory differs')
    actual=set()
    for path in bundle.rglob('*'):
        safe(path)
        if path.is_file():actual.add(path.relative_to(bundle).as_posix())
    require(actual==set(files)|{'manifest.json','immutable_inventory.json','verify_additions.py'},'missing or extra payload file')
    for name,pin in files.items():
        relative=Path(name)
        require(not relative.is_absolute() and '..'not in relative.parts and '\\'not in name,'unsafe payload path')
        p=safe(bundle/relative)
        require(p.stat().st_size==pin['bytes'] and sha(p)==pin['sha256'],'payload changed: '+name)
    require(sha(bundle/'verify_additions.py')==manifest['verifier_sha256'],'verifier differs')
    require(set(manifest)==set(declarations)|{'files','immutable_inventory_sha256','verifier_sha256'},'unexpected manifest declaration')
    require(all(manifest[k]==v for k,v in declarations.items()),'scientific declaration differs')
    require(declarations['cohort_ids']==[ID] and declarations['candidate_n']==1,'single original question differs')
    scorer=local(bundle,'scorer');original=local(bundle,'original_scorer');review_schema=local(bundle,'review_schema');controls=local(bundle,'contract_checks')
    exact=scorer.get_kernel().json_exact
    task,=lines(bundle/'tasks.jsonl');gold,=lines(bundle/'reference_gold.jsonl');original_row,=lines(bundle/'provenance/original_selected_rows.jsonl')
    definition=load(bundle/'definitions'/(ID+'.json'))
    keys=['id','question_en','original_query','reference_query','required_fields','collection','cardinality_policy','repair_class','original_question_preserved']
    require(list(definition)==keys,'canonical nine-key order/shape differs')
    identity=hashlib.sha256(exact(definition).encode()).hexdigest()
    require(task['id']==gold['id']==definition['id']==ID and identity==task['repair_sha256']==gold['repair_sha256'],'repair identity differs')
    require(all(exact(task[k])==exact(definition[k])for k in keys),'task definition differs')
    require(definition['question_en']==original_row['question_en'] and definition['original_query']==original_row['cypher'] and definition['original_question_preserved'] is True,'original bytes differ')
    require(task['validation_status']=='validated' and task['admitted'] is False and task['expert_validation_n']==0 and task['human_author_review_completed'] is False,'offline AI/native versus admission declarations differ')
    criteria=load(bundle/'criteria.json')
    require(files['criteria.json']['sha256']=='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4','criteria differs')
    gate=bundle/'gate_evidence'/ID
    reviews=[load(gate/(side+'.json'))for side in ['primary','secondary']]
    for review in reviews:
        review_schema.check_pass(review,definition['question_en'],criteria['semantic_units'],criteria_sha=files['criteria.json']['sha256'],identity_key='repair_sha256',identity_sha=identity)
    require(reviews[0]['reviewer']!=reviews[1]['reviewer'],'same reviewer used twice')
    seal=load(gate/'ROOT_final_local_seal.json')
    require(seal['decision']=='pass_local' and seal['repair_sha256']==identity,'ROOT exact repair seal absent')
    source=bundle/'source_evidence'/ID
    replay=subprocess.run([sys.executable,'-B','-I','-S',str(source/'verify.py')],cwd=bundle,text=True,capture_output=True,timeout=180,
        env={'PATH':os.environ.get('PATH','/usr/bin:/bin'),'LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'})
    require(replay.returncode==0,'source/native portable replay failed: '+replay.stderr)
    replay_result=json.loads(replay.stdout)
    require(replay_result['full_SQL_rows']==532 and replay_result['boundary_rows']==16 and replay_result['operative_fragment_bindings']==83,'source/native dimensions differ')
    require(replay_result['pinned_native_receipt_checks']['distinct_nonblind_AI_review_records']==2 and replay_result['native_row_checks']['typed_full_multiset_and_rank_equal'] is True,'source/native typed binding incomplete')
    audit=replay_result['default_no_host_audit']
    require(all(audit[k]==0 for k in ['network_calls','subprocess_calls','SQL_calls','host_private_open_attempts','write_open_attempts']),'source replay used host-private capabilities')
    metadata=load(gate/'native_metadata.json');execution=load(gate/'native_execution.json');guard=load(gate/'native_guard.json')
    require(metadata['query']==definition['reference_query'] and metadata['query_sha256']==hashlib.sha256(definition['reference_query'].encode()).hexdigest(),'native query differs')
    require(metadata['status']=='OK' and metadata['plan_query_type']==metadata['execution_query_type']=='r' and metadata['rollback_completed'] is True and metadata['truncated'] is False,'native read-only/complete rollback gate')
    require(execution['inventory_unchanged'] is True and execution['source_before']==execution['source_after']==manifest['graph_sources']['RAN1'],'native source inventory differs')
    require(guard['status']=='PASS' and guard['child_exit']==0 and guard['quality_rerolls']==0 and guard['owned_cleanup']['owned_stopped'] is True,'native owned guard differs')
    raw_native=gate/'native_rows.jsonl'
    require(sha(raw_native)==metadata['rows_sha256'],'native row bytes differ')
    limited=[dict(zip(metadata['columns'],r))for r in lines(raw_native)]
    boundary=lines(gate/'complete_boundary16_with_source_rank.jsonl')
    projected=[{f['name']:r[f['source_column_or_expression']]for f in definition['required_fields']}for r in boundary]
    groups=original.make_order_groups(task,boundary,projected)
    require(len(boundary)==16 and projected==gold['records'] and groups==gold['order_groups'],'complete boundary/gold source rank differs')
    require(original.score(task,projected,limited,diagnostic=True,order_groups=groups)['exact'],'actual native10 not a legal full-record boundary answer')
    generic=controls.checks(task,projected,groups)
    require(all(x['pass']for x in generic),'typed corruption control failed')
    saved=load(gate/'portable_typed_controls.json')
    require(saved['generic_controls']==generic,'saved typed controls differ')
    require(replay_result['API_calls']==replay_result['native_calls_performed_here']==0,'source verifier made model/native calls')
    return {'status':'PASS','candidate_n':1,'local_validated_n':1,'new_public_admissions':0,'model_calls':0,'native_calls':0,
        'items':[{'id':ID,'repair_sha256':identity,'native_rows':10,'complete_tie_population':16,'full_native_rows':532}],
        'portable_controls_replayed':len(generic),'independently_sealed_item_replay':replay_result,'human_expert_validation_n':0}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--bundle',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(verify(args.bundle),ensure_ascii=False,sort_keys=True))
