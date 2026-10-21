#!/usr/bin/env python3
"""Replay the sealed original top-five current-decision change review offline."""
import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

sys.dont_write_bytecode=True
if sys.flags.optimize:raise SystemExit('Enabled checks required')
INVENTORY='09b194304bb8755a5becf84b9840185cdc0a4671545c06d4b7fe50794e4bb149'
SEAL='d926ab7d1cfe98c669bedfdd88c99649bcc165127c0a6c2a567a21683f52d653'
SOURCE_MANIFEST='e82347b27a7142c5458e5483260a84f2d61fdd052e97a30c89dd54fcf2209461'
SOURCE_VERIFIER='81dc6ea275360a94080494f17deea46c108b45d9767046b807b8ac6d6b53d104'
IDENTITY='RAN4_P4_CQ4-2'
REPAIR='eeec74a4949588ed3649d73cfe310fe10e9e46a4675c2923fc87740bf710c0d2'
CRITERIA='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'

def require(ok, why):
    if not ok:
        raise ValueError(why)

def safe(path):
    p = Path(os.path.abspath(path))
    for q in (p, *p.parents):
        require(not q.is_symlink(), 'symlink forbidden')
    if p.exists():
        require(stat.S_ISDIR(p.lstat().st_mode) or stat.S_ISREG(p.lstat().st_mode), 'nonregular entry forbidden')
    return p

def sha(p):
    return hashlib.sha256(safe(p).read_bytes()).hexdigest()

def pairs(values):
    out = {}
    for k, v in values:
        require(k not in out, 'duplicate JSON key')
        out[k] = v
    return out

def parse(raw):
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON')))

def load(p):
    return parse(safe(p).read_bytes())

def lines(p):
    return [parse(s) for s in safe(p).read_bytes().splitlines() if s.strip()]

def exact(v):
    return json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(',', ':'))

def local(bundle, name):
    spec = importlib.util.spec_from_file_location(name, safe(bundle / (name + '.py')))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def no_host_audit(bundle, source_command, child_env):
    counts = {'network_calls':0, 'SQL_calls':0, 'host_private_open_attempts':0, 'write_open_attempts':0,
              'expected_source_child_calls':0, 'other_subprocess_calls':0, 'packet_read_opens':0,
              'stdlib_read_opens':0, 'subprocess_pipe_descriptor_opens':0}
    stdlib = Path(os.__file__).resolve().parent
    state = {'source_child_window':False}
    def hook(event, args):
        if event.startswith(('socket.', 'http.client.', 'urllib.')):
            counts['network_calls'] += 1
            raise RuntimeError('Offline addition forbids network')
        if event.startswith('sqlite3.'):
            counts['SQL_calls'] += 1
            raise RuntimeError('Offline addition forbids SQL')
        if event == 'subprocess.Popen':
            executable, argv, cwd, env = args
            if state['source_child_window'] and list(argv) == source_command and Path(cwd) == bundle and env == child_env and counts['expected_source_child_calls'] == 0:
                counts['expected_source_child_calls'] += 1
            else:
                counts['other_subprocess_calls'] += 1
                raise RuntimeError('Only the exact immutable source verifier child is permitted')
        if event in {'os.system','os.posix_spawn','os.posix_spawnp','os.fork','os.exec','os.spawn'}:
            counts['other_subprocess_calls'] += 1
            raise RuntimeError('Offline addition forbids external execution')
        if event == 'open':
            path, mode, flags = args
            if isinstance(path, int):
                if state['source_child_window']:
                    counts['subprocess_pipe_descriptor_opens'] += 1
                    return
                counts['host_private_open_attempts'] += 1
                raise RuntimeError('Offline addition forbids host descriptors')
            if (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (isinstance(flags, int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_APPEND|os.O_TRUNC)):
                counts['write_open_attempts'] += 1
                raise RuntimeError('Offline addition forbids writes')
            target = Path(os.path.abspath(os.fsdecode(path)))
            if target.is_relative_to(bundle):
                safe(target)
                counts['packet_read_opens'] += 1
            elif target.is_relative_to(stdlib):
                counts['stdlib_read_opens'] += 1
            else:
                counts['host_private_open_attempts'] += 1
                raise RuntimeError('Offline addition forbids host-private open')
    sys.addaudithook(hook)
    return counts, state

def native(source,kind):
    query=safe(source/'native'/(kind+'_reference.cypher')).read_bytes();digest=hashlib.sha256(query).hexdigest()
    prefix=source/'native/actual/reference_outputs'/IDENTITY/digest
    meta=load(prefix.with_suffix('.json'));raw=safe(prefix.with_suffix('.jsonl')).read_bytes()
    positional=[parse(line)for line in raw.splitlines()if line]
    require(meta['status']=='OK'and meta['id']==IDENTITY and meta['wg']=='RAN4','actual native identity/status')
    require(meta['query'].encode()==query and meta['query_sha256']==digest and meta['rows_sha256']==hashlib.sha256(raw).hexdigest(),'actual native exact query/rows')
    require(meta['full_rows_available']is True and meta['truncated']is False and meta['rollback_completed']is True,'complete guarded READ rollback')
    require(meta['columns']==['tdocNumber','reason','summary']and meta['rows_retained']==len(positional),'three named native fields')
    require(all(type(row)is list and len(row)==3 for row in positional),'native positional shape')
    return meta,[dict(zip(meta['columns'],row))for row in positional]


def replay43(scorer,definition,full,selected,groups):
    cases=[('selected_native5',selected,True),('selected_permutation',list(reversed(selected)),True),('missing_row',selected[:-1],False),('duplicate_row',selected+[selected[0]],False),('later_rank_substitution',selected[:-1]+[full[5]],False),('full_population_as_answer',full,False)]
    for index in range(len(selected)):
        for field in ['tdocNumber','reason','summary']:
            bad=copy.deepcopy(selected);bad[index][field]=(bad[index][field]or'')+'__different_exact_value__';cases.append((f'row{index}_{field}_wrong_value',bad,False))
            bad=copy.deepcopy(selected);del bad[index][field];cases.append((f'row{index}_{field}_omitted',bad,False))
        bad=copy.deepcopy(selected);bad[index]['reason'],bad[index]['summary']=bad[index]['summary'],bad[index]['reason'];cases.append((f'row{index}_reason_summary_role_swap',bad,selected[index]['reason']==selected[index]['summary']))
    bad=copy.deepcopy(selected);bad[0]['reason']=None;cases.append(('nonnull_reason_null',bad,False))
    bad=copy.deepcopy(selected);bad[0]['tdocNumber']=123;cases.append(('identity_wrong_type',bad,False))
    observations=[]
    for name,predicted,expected in cases:
        outcome=scorer.score(definition,full,predicted,diagnostic=True,order_groups=groups)
        require(outcome['exact']is expected,'source diagnostic control:'+name)
        observations.append({'case':name,'expected_exact':expected,'observed':outcome})
    require(len(observations)==43,'exact43 diagnostic controls')
    return observations


def verify(bundle):
    bundle=safe(bundle);require(safe(__file__)==bundle/'verify_additions.py','execute own verifier')
    source=bundle/'source_evidence'/IDENTITY
    command=[sys.executable,'-B','-I','-S',str(source/'verify_evidence.py')]
    child_env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'}
    audit,state=no_host_audit(bundle,command,child_env)
    require(sha(bundle/'immutable_inventory.json')==INVENTORY,'immutable inventory')
    files=load(bundle/'immutable_inventory.json')['files'];declaration=load(bundle/'declarations.json');manifest=load(bundle/'manifest.json')
    require(exact(manifest)==exact(dict(declaration,files=files,immutable_inventory_sha256=INVENTORY,verifier_sha256=sha(bundle/'verify_additions.py'))),'exact declarations and manifest')
    expected=set(files)|{'manifest.json','immutable_inventory.json','verify_additions.py'}
    directories={p.as_posix()for name in expected for p in Path(name).parents if p.as_posix()!='.'};actual=set()
    for path in bundle.rglob('*'):
        safe(path)
        if path.is_file():actual.add(path.relative_to(bundle).as_posix())
        else:require(path.relative_to(bundle).as_posix()in directories,'extra directory')
    require(actual==expected,'closed file tree')
    for name,info in files.items():
        rel=Path(name);require(not rel.is_absolute()and'..'not in rel.parts and'\\'not in name,'safe member')
        require((bundle/name).stat().st_size==info['bytes']and sha(bundle/name)==info['sha256'],'payload:'+name)
    require(declaration['cohort_ids']==[IDENTITY]and declaration['candidate_n']==1,'one original item')
    for key in ['new_model_calls','new_public_admissions','human_expert_n']:require(type(declaration[key])is int and declaration[key]==0,'offline zero')
    require(sha(bundle/'criteria.json')==CRITERIA,'unchanged original7 criteria')
    typed=local(bundle,'typed_values');local(bundle,'scorer');scorer=local(bundle,'original_scorer');checks=local(bundle,'contract_checks');schema=local(bundle,'review_schema')
    tasks,golds,originals=[lines(bundle/name)for name in ['tasks.jsonl','reference_gold.jsonl','provenance/original_selected_rows.jsonl']]
    require(len(tasks)==len(golds)==len(originals)==1,'one complete case');task,gold,authored=tasks[0],golds[0],originals[0]
    definition=load(bundle/'definitions'/(IDENTITY+'.json'))
    keys=['id','question_en','original_query','reference_query','required_fields','collection','cardinality_policy','repair_class','original_question_preserved']
    require(set(definition)==set(keys)and hashlib.sha256(typed.json_exact(definition).encode()).hexdigest()==REPAIR,'canonical9')
    require(task['id']==gold['id']==authored['id']==IDENTITY and task['repair_sha256']==gold['repair_sha256']==REPAIR,'case identity')
    require(all(exact(task[key])==exact(definition[key])for key in keys),'unchanged task definition')
    require(authored['question_en']==definition['question_en']and authored['cypher']==definition['original_query'],'unchanged original EN/query authority')
    require([(r['name'],r['type'],r['nullable'])for r in definition['required_fields']]==[('tdocNumber','string',False),('reason','string',False),('summary','string',True)],'original named record roles')
    require(definition['collection']=={'kind':'top_k_boundary_ties','value':5,'source_order_keys':[{'source_column':'tdocNumber','direction':'asc'}],'tie_policy':'any_subset_at_boundary','within_tie_order':'any','require_rank_order':False},'original top-five membership')
    require(definition['cardinality_policy']=={'mode':'top_k','value':5,'tie_policy':'any_subset_at_boundary'},'original top-five cardinality')
    require(task['validation_status']=='validated'and task['admitted']is False and task['model_calls']==task['expert_validation_n']==0 and task['human_author_review_completed']is False,'local/model/public distinction')
    gate=bundle/'gate_evidence'/IDENTITY;seal=load(gate/'ROOT_final_disposition.json')
    require(sha(gate/'ROOT_final_disposition.json')==SEAL and seal['id']==IDENTITY and seal['decision']=='pass_local'and seal['repair_sha256']==REPAIR and seal['criteria_sha256']==CRITERIA,'actual ROOT final seal')
    index=load(gate/'sealed_gate_file_index.json');sealkeys={key for key,value in seal.items()if isinstance(value,dict)and{'path','bytes','sha256'}<=set(value)}
    require({row['seal_key']for row in index}==sealkeys,'all explicit sealed gate artifacts')
    for row in index:require(sha(gate/row['local'])==row['sha256']==seal[row['seal_key']]['sha256']and(gate/row['local']).stat().st_size==row['bytes'],'sealed gate bytes')
    require(any(seal[key]['sha256']==SOURCE_MANIFEST for key in sealkeys)and any(seal[key]['sha256']==SOURCE_VERIFIER for key in sealkeys),'ROOT seals exact portable child')
    reviews=[load(gate/(kind+'.json'))for kind in ['primary','secondary']]
    for review in reviews:schema.check_pass(review,definition['question_en'],load(bundle/'criteria.json')['semantic_units'],criteria_sha=CRITERIA,identity_key='repair_sha256',identity_sha=REPAIR)
    require(reviews[0]['reviewer']!=reviews[1]['reviewer'],'two distinct actual AI semantic reviews')
    require(sha(source/'payload_manifest.json')==SOURCE_MANIFEST and sha(source/'verify_evidence.py')==SOURCE_VERIFIER,'source child identity')
    state['source_child_window']=True
    try:child=subprocess.run(command,cwd=bundle,capture_output=True,text=True,timeout=200,env=child_env)
    finally:state['source_child_window']=False
    require(child.returncode==0,'source child:'+child.stderr[-3000:]);replay=parse(child.stdout)
    require(replay['status']=='PASS_PORTABLE_SOURCE_FROZEN_NATIVE_AND_UNCHANGED_SCORER_BINDING'and replay['Agreement']==1905 and replay['eligible_CR']==12300 and replay['source_frontier']==34 and replay['prefix_source_positive']==8 and replay['prefix_source_negative']==26 and replay['source_cover_fields']==68 and replay['source_original_acts']==110 and replay['source_original_CP_slices']==18940 and replay['native_full']==15 and replay['native_selected']==5 and replay['native_calls']==replay['model_API_calls']==0,'complete original-source/frozen/native/scorer child replay')
    fullmeta,full=native(source,'full');limitedmeta,selected=native(source,'limited')
    require(len(full)==15 and selected==full[:5]and len(selected)==5 and limitedmeta['query']==definition['reference_query'],'actual original top-five native binding')
    groups=scorer.make_order_groups(definition,full,full)
    require(exact(gold['records'])==exact(full)and exact(gold['order_groups'])==exact(groups),'full reference and original order groups')
    require(scorer.score(task,full,selected,diagnostic=True,order_groups=groups)['exact'],'original requested-record exact')
    generic=checks.checks(task,full,order_groups=groups);saved=load(gate/'portable_typed_controls.json')
    require(all(row['pass']for row in generic)and generic==saved['generic']and len(generic)==saved['generic_controls_n'],'unchanged generic typed controls')
    controls43=replay43(scorer,definition,full,selected,groups)
    prior=parse(gzip.decompress((source/'source/evidence/actual_v6_unchanged_scorer_diagnostic_controls_v2.json.gz').read_bytes()))
    require(exact(controls43)==exact(prior['controls'])and prior['cases']==43,'actual prior43 control result equality')
    for name in ['scorer.py','typed_values.py','source_pins.json','original_scorer.py']:require(sha(bundle/name)==sha(source/'scoring'/name),'unchanged released scientific scorer:'+name)
    execution=load(source/'native/actual/execution_RAN4.json')
    require(set(declaration['graph_sources'])=={'RAN1','RAN2','RAN3','RAN4','RAN5'}and exact(declaration['graph_sources']['RAN4'])==exact(execution['source_before'])==exact(execution['source_after']),'all original graph sources')
    require(all(audit[key]==0 for key in ['network_calls','SQL_calls','host_private_open_attempts','write_open_attempts','other_subprocess_calls'])and audit['expected_source_child_calls']==1,'default no-host replay with only sealed source child')
    return {'status':'PASS','candidate_n':1,'local_validated_n':1,'new_public_admissions':0,'model_calls':0,'native_calls':0,'portable_controls_replayed':len(generic)+43,'items':[{'id':IDENTITY,'repair_sha256':REPAIR,'native_rows':5,'native_population_rows':15,'native_full_columns':['tdocNumber','reason','summary'],'requested_fields':['tdocNumber','reason','summary'],'collection_kind':'top_k_boundary_ties','generic_typed_controls':len(generic),'source_child_typed_controls':43,'reference_order_groups_preserved':True,'independently_sealed_item_replay':replay}],'distinct_nonblind_AI_reviews_per_item':2,'human_expert_validation_n':0,'no_host_audit':audit,'scope':'Current technical Agreement adoption, complete earlier source frontier and original top-five CR reason/summary records.'}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--bundle',type=Path,required=True);args=ap.parse_args();print(json.dumps(verify(args.bundle),ensure_ascii=False,sort_keys=True))
