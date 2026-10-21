#!/usr/bin/env python3
"""Replay the one sealed original decision-to-section trace addition offline."""
import argparse
import collections
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

sys.dont_write_bytecode=True
if sys.flags.optimize:raise SystemExit('Enabled checks required; -O/-OO refused')
INVENTORY_SHA256='b4a792d62d80785c35dd8663fbebf4f7f75121301b1fa541905e07248544d71a'
SEAL_SHA256='11d85d9df18a8376ec3b46a0daa7e3858b785367e22b84796d50a3de9f8c3571'
SOURCE_MANIFEST_SHA256='dd44a37bf137454e16f84094aff33112e1d692d88d9fe5756e2642cc53e84f25'
IDENTITY='RAN2_P3_CQ4-3'
REPAIR='01a561b7ff2c33ff5191531d37c0e231d81f8434dd10aff461bdaa653407ac63'
CRITERIA='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
FIELDS=['r.resolutionId','cr.tdocNumber','cr.clausesAffected','sp.specNumber']


def require(ok,why):
    if not ok:raise ValueError(why)


def safe(path):
    path=Path(os.path.abspath(path))
    for p in (path,*path.parents):require(not p.is_symlink(),'symlink forbidden')
    if path.exists():require(stat.S_ISDIR(path.lstat().st_mode) or stat.S_ISREG(path.lstat().st_mode),'nonregular file forbidden')
    return path


def sha(path):return hashlib.sha256(safe(path).read_bytes()).hexdigest()


def pairs(values):
    result={}
    for k,v in values:
        require(k not in result,'duplicate JSON key');result[k]=v
    return result


def load(path):return json.loads(safe(path).read_text(),object_pairs_hook=pairs)


def lines(path):return [json.loads(s,object_pairs_hook=pairs) for s in safe(path).read_text().splitlines() if s.strip()]


def local(bundle,name):
    spec=importlib.util.spec_from_file_location(name,safe(bundle/(name+'.py')))
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module


def verify(bundle):
    bundle=safe(bundle)
    require(safe(__file__)==bundle/'verify_additions.py','execute the bundle own verifier')
    require(sha(bundle/'immutable_inventory.json')==INVENTORY_SHA256,'immutable inventory changed')
    files=load(bundle/'immutable_inventory.json')['files'];manifest=load(bundle/'manifest.json');declarations=load(bundle/'declarations.json')
    require(manifest['files']==files and manifest['immutable_inventory_sha256']==INVENTORY_SHA256,'manifest inventory differs')
    actual=set()
    for p in bundle.rglob('*'):
        safe(p)
        if p.is_file():actual.add(p.relative_to(bundle).as_posix())
    require(actual==set(files)|{'manifest.json','immutable_inventory.json','verify_additions.py'},'missing or extra file')
    for name,pin in files.items():
        relative=Path(name)
        require(type(name) is str and name and not relative.is_absolute() and '..' not in relative.parts and '\\' not in name,'unsafe inventory path')
        require((bundle/relative).stat().st_size==pin['bytes'] and sha(bundle/relative)==pin['sha256'],'payload changed: '+name)
    require(sha(bundle/'verify_additions.py')==manifest['verifier_sha256'],'verifier changed')
    require(set(manifest)==set(declarations)|{'files','immutable_inventory_sha256','verifier_sha256'} and all(manifest[k]==v for k,v in declarations.items()),'scientific declarations changed')
    require(declarations['cohort_ids']==[IDENTITY] and declarations['candidate_n']==1 and declarations['new_model_calls']==declarations['new_public_admissions']==declarations['human_expert_n']==0,'offline cohort accounting')
    require(sha(bundle/'criteria.json')==CRITERIA,'fixed seven criteria changed')
    typed=local(bundle,'typed_values');local(bundle,'scorer');original=local(bundle,'original_scorer');checks=local(bundle,'contract_checks');schema=local(bundle,'review_schema')
    tasks=lines(bundle/'tasks.jsonl');golds=lines(bundle/'reference_gold.jsonl');originals=lines(bundle/'provenance/original_selected_rows.jsonl')
    require(len(tasks)==len(golds)==len(originals)==1,'one original question required')
    task,gold,authored=tasks[0],golds[0],originals[0]
    require(task['id']==gold['id']==authored['id']==IDENTITY,'cohort original ID')
    definition=load(bundle/'definitions'/(IDENTITY+'.json'));criteria=load(bundle/'criteria.json')
    keys=['id','question_en','original_query','reference_query','required_fields','collection','cardinality_policy','repair_class','original_question_preserved']
    require(set(definition)==set(keys) and len(definition)==9,'canonical nine-key shape')
    require(hashlib.sha256(typed.json_exact(definition).encode()).hexdigest()==task['repair_sha256']==gold['repair_sha256']==REPAIR,'canonical identity')
    require(all(typed.json_exact(task[k])==typed.json_exact(definition[k]) for k in keys),'task definition')
    require(definition['question_en']==authored['question_en'] and definition['original_query']==authored['cypher'] and definition['original_question_preserved'] is True,'original authored bytes')
    require([f['name'] for f in definition['required_fields']]==FIELDS and all(f['type']=='string' and f['nullable'] is False for f in definition['required_fields']),'four requested trace roles')
    require(definition['collection']=={'kind':'multiset'} and definition['cardinality_policy']=={'mode':'top_k','value':10},'original pathbag cap10')
    require(task['validation_status']=='validated' and task['admitted'] is False and task['expert_validation_n']==0 and task['human_author_review_completed'] is False and task['model_calls']==0,'local/source versus public/model accounting')
    gate=bundle/'gate_evidence'/IDENTITY
    reviews=[load(gate/(s+'.json')) for s in ('primary','secondary')]
    for review in reviews:schema.check_pass(review,definition['question_en'],criteria['semantic_units'],criteria_sha=CRITERIA,identity_key='repair_sha256',identity_sha=REPAIR)
    require(reviews[0]['reviewer']!=reviews[1]['reviewer'] and all(r['nonblind'] is True and r['human_n']==0 for r in reviews),'two distinct nonblind AI human0')
    seal=load(gate/'ROOT_final_disposition.json')
    require(sha(gate/'ROOT_final_disposition.json')==SEAL_SHA256 and seal['decision']=='pass_local' and seal['repair_sha256']==REPAIR and seal['criteria_sha256']==CRITERIA,'exact final ROOT seal')
    for record in load(gate/'sealed_gate_file_index.json'):
        require(sha(gate/record['local'])==record['sha256'] and (gate/record['local']).stat().st_size==record['bytes'],'ROOT gate file pin: '+record['local'])
        require(seal[record['seal_key']]['sha256']==record['sha256'],'ROOT gate file declaration')
    source=bundle/'source_evidence'/IDENTITY
    require(sha(source/'manifest.json')==SOURCE_MANIFEST_SHA256==seal['portable_manifest']['sha256'],'sealed source package')
    require(sha(source/'verify.py')==seal['portable_verifier']['sha256'],'sealed source verifier')
    child=subprocess.run([sys.executable,'-B','-I','-S',str(source/'verify.py')],cwd=bundle,text=True,capture_output=True,timeout=180,env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'})
    require(child.returncode==0,'isolated original/native source replay: '+child.stderr)
    replay=json.loads(child.stdout,object_pairs_hook=pairs)
    require(replay['status']=='PASS' and replay['canonical_repair_sha256']==REPAIR and replay['native_counts']==[185,49,10,10] and replay['actual_guards_preserved_and_verified']==2,'complete source and exact-canonical native replay')
    require(replay['source_closure']=={'original54':54,'original_raw_prefix52':52,'own_positive':10,'foreign':42,'unknown_in_prefix':0},'complete original prefix source closure')
    require(replay['requested_role_controls']==21 and replay['distinct_nonblind_AI_reviews']==2,'source controls/reviews')
    require(all(replay['no_host_audit'][k]==0 for k in ('network_calls','subprocess_calls','SQL_calls','host_private_open_attempts','write_open_attempts')),'source child accessed live/private capabilities')
    metadata=load(gate/'native_metadata.json');raw=gate/'native_rows.jsonl'
    require(metadata['query']==definition['reference_query'] and metadata['query_sha256']==hashlib.sha256(definition['reference_query'].encode()).hexdigest(),'exact canonical/native query bytes including LF policy')
    require(metadata['status']=='OK' and metadata['plan_query_type']==metadata['execution_query_type']=='r' and metadata['rollback_completed'] is True and metadata['full_rows_available'] is True and metadata['truncated'] is False,'actual read-only complete native')
    require(sha(raw)==metadata['rows_sha256'],'actual native row bytes')
    limited=[dict(zip(metadata['columns'],r)) for r in lines(raw)]
    require(metadata['columns']==FIELDS and len(limited)==metadata['rows_retained']==10 and limited==gold['records'],'actual native4/10 reference')
    require(gold.get('order_groups') is None,'unrequested output sequence not required')
    require(original.score(task,gold['records'],limited,diagnostic=True,order_groups=None)['exact'] and original.score(task,gold['records'],list(reversed(limited)),diagnostic=True,order_groups=None)['exact'],'complete typed answer/pathbag serialization freedom')
    generic=checks.checks(task,gold['records'])
    require(len(generic)==16 and all(c['pass'] for c in generic) and generic==load(gate/'portable_typed_controls.json')['generic_controls'],'four-role scorer controls')
    return {'status':'PASS','candidate_n':1,'local_validated_n':1,'new_public_admissions':0,'model_calls':0,'native_calls':0,'portable_controls_replayed':16,'items':[{'id':IDENTITY,'repair_sha256':REPAIR,'native_rows':10,'native_full_columns':4,'requested_fields':FIELDS,'collection_kind':'multiset','generic_typed_controls':16,'source_child_requested_role_controls':21,'independently_sealed_item_replay':replay}],'distinct_nonblind_AI_reviews_per_item':2,'human_expert_validation_n':0,'scope':'One unchanged original decision-to-section trace with exact canonical/native bytes, complete raw source prefix and typed four-role path records.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--bundle',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(verify(args.bundle),ensure_ascii=False,sort_keys=True))
