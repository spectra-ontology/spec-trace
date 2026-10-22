#!/usr/bin/env python3
"""Replay source-certified detailed URLLC study-to-specification impacts offline."""
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
INVENTORY='8e50f85072ecd8198dffecf4060190f2f5a647de8d43bc4df5b32aba6b8dbb1e'
SEAL='c823c417692e2c3d3764936bd0cfcdd95d5484dce9102280a3fbd1d135a7fa95'
SOURCE_MANIFEST='28d61b8f067ada570989f1029fdfbe7f77e3b0d41596397761049f0be95ba867'
SOURCE_VERIFIER='9ca33a40bce86c4e29c83255f87e4746f5fc2344e0652c724241c84441404e3d'
IDENTITY='RAN1_P5_CQ3-3'
REPAIR='889686436143c09726bc635cce77baff9616d7d9813ef204b471f155f5077e1b'
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

def all_sealed_pins(obj,prefix=''):
    if isinstance(obj,dict):
        if {'path','bytes','sha256'}<=set(obj):
            yield prefix,obj
        else:
            for key,value in obj.items():yield from all_sealed_pins(value,prefix+'.'+key if prefix else key)
    elif isinstance(obj,list):
        for i,value in enumerate(obj):yield from all_sealed_pins(value,prefix+'['+str(i)+']')


def native(source,kind):
    main=kind=='answer';version='v2'if main else'v3'
    query=(source/'retained/candidate.cypher').read_text()if main else(source/'native/v3/full_component_membership.cypher').read_text().strip()
    digest=hashlib.sha256(query.encode()).hexdigest();ident=IDENTITY if main else IDENTITY+'__full_components'
    prefix=source/'native'/version/'ROOT_actual_native_capture_v1/reference_outputs'/ident/digest
    meta=load(prefix.with_suffix('.json'));raw=safe(prefix.with_suffix('.jsonl')).read_bytes()
    require(meta['status']=='OK'and meta['id']==ident and meta['wg']=='RAN1','actual native identity/status')
    require(meta['query']==query and meta['query_sha256']==digest and meta['rows_sha256']==hashlib.sha256(raw).hexdigest(),'actual native exact query/rows')
    require(meta['full_rows_available']is True and meta['truncated']is False and meta['rollback_completed']is True and meta['execution_summary_complete']is True,'complete guarded READ rollback')
    require(meta['plan_query_type']==meta['execution_query_type']=='r','native read classification')
    rows=[parse(s)for s in raw.splitlines()if s];require(meta['rows_retained']==len(rows)and all(type(r)is list and len(r)==len(meta['columns'])for r in rows),'complete native rows and shape')
    return meta,[dict(zip(meta['columns'],row))for row in rows]


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
    requested=['tr.trNumber','sp.specNumber','ti.impactType','ti.affectedSection','ti.impactDescription']
    require([(r['name'],r['type'],r['nullable'])for r in definition['required_fields']]==[(f,'string',False)for f in requested],'original five requested roles')
    require(definition['collection']=={'kind':'sequence','order_keys':[{'field':'sp.specNumber','direction':'asc'}]}and definition['cardinality_policy']=={'mode':'exact','value':2},'original target-specification record unit and order')
    require(task['validation_status']=='validated'and task['admitted']is False and task['model_calls']==task['expert_validation_n']==0 and task['human_author_review_completed']is False,'local/model/public distinction')
    gate=bundle/'gate_evidence'/IDENTITY;seal=load(gate/'ROOT_final_disposition.json')
    require(sha(gate/'ROOT_final_disposition.json')==SEAL and seal['id']==IDENTITY and seal['decision']=='pass_local'and seal['repair_sha256']==REPAIR and seal['criteria_sha256']==CRITERIA,'actual ROOT final seal')
    index=load(gate/'sealed_gate_file_index.json');sealedpins=dict(all_sealed_pins(seal));sealkeys=set(sealedpins)
    require({row['seal_key']for row in index}==sealkeys,'all explicit sealed gate artifacts')
    for row in index:require(sha(gate/row['local'])==row['sha256']==sealedpins[row['seal_key']]['sha256']and(gate/row['local']).stat().st_size==row['bytes'],'sealed gate bytes')
    require(any(sealedpins[key]['sha256']==SOURCE_MANIFEST for key in sealkeys)and any(sealedpins[key]['sha256']==SOURCE_VERIFIER for key in sealkeys),'ROOT seals exact portable child')
    reviews=[load(gate/(kind+'.json'))for kind in ['primary','secondary']]
    for review in reviews:schema.check_pass(review,definition['question_en'],load(bundle/'criteria.json')['semantic_units'],criteria_sha=CRITERIA,identity_key='repair_sha256',identity_sha=REPAIR)
    require(reviews[0]['reviewer']!=reviews[1]['reviewer'],'two distinct actual AI semantic reviews')
    require(sha(source/'payload_manifest.json')==SOURCE_MANIFEST and sha(source/'verify_evidence.py')==SOURCE_VERIFIER,'source child identity')
    state['source_child_window']=True
    try:child=subprocess.run(command,cwd=bundle,capture_output=True,text=True,timeout=200,env=child_env)
    finally:state['source_child_window']=False
    require(child.returncode==0,'source child:'+child.stderr[-3000:]);replay=parse(child.stdout)
    require(replay['status']=='PASS_PORTABLE_ORIGINAL_SOURCE_FROZEN_SQL_GRAPH_NATIVE_AND_UNCHANGED_SCORER'and replay['original_source_archives']==41 and replay['original_source_body_children']==6778 and replay['candidate_CR_n']==72 and replay['selected_CR_n']==35 and replay['source_paragraphs_n']==74 and replay['native_component_records']==70 and replay['native_answer_rows']==2 and replay['new_native_calls']==replay['new_API_calls']==0,'complete authored source/frozen/native/scorer replay')
    answer_meta,answer=native(source,'answer');component_meta,components=native(source,'components')
    require(answer_meta['columns']==requested and component_meta['columns']==['specNumber','CRid','field','sections','pieces']and len(answer)==2 and len(components)==70 and sum(len(c['pieces'])for c in components)==74 and answer_meta['query']==definition['reference_query'],'actual complete requested records and component binding')
    require(exact(gold['records'])==exact(answer)and gold['order_groups']is None,'requested reference and original spec order semantics')
    require(scorer.score(task,answer,answer,diagnostic=True)['exact'],'requested five-field exact')
    generic=checks.checks(task,answer);saved=load(gate/'portable_typed_controls.json')
    require(all(row['pass']for row in generic)and generic==saved['generic']and len(generic)==saved['generic_controls_n']==19,'unchanged generic typed controls')
    require(replay['scorer_controls_n']==saved['source_child_total_controls_n']==29,'source-child generic19 and custom10 controls')
    for name in ['scorer.py','typed_values.py','source_pins.json','original_scorer.py']:require(sha(bundle/name)==sha(source/'scoring'/name),'unchanged released scientific scorer:'+name)
    execution=load(source/'native/v2/ROOT_actual_native_capture_v1/execution_RAN1.json')
    require(set(declaration['graph_sources'])=={'RAN1','RAN2','RAN3','RAN4','RAN5'}and exact(declaration['graph_sources']['RAN1'])==exact(execution['source_before'])==exact(execution['source_after']),'all original graph sources')
    require(all(audit[key]==0 for key in ['network_calls','SQL_calls','host_private_open_attempts','write_open_attempts','other_subprocess_calls'])and audit['expected_source_child_calls']==1,'default no-host parent and exact source child')
    return {'status':'PASS','candidate_n':1,'local_validated_n':1,'new_public_admissions':0,'model_calls':0,'native_calls':0,'portable_controls_replayed':29,'items':[{'id':IDENTITY,'repair_sha256':REPAIR,'native_rows':2,'native_population_rows':2,'native_membership_diagnostic_rows':70,'native_component_paragraphs':74,'native_full_columns':requested,'requested_fields':requested,'collection_kind':'sequence','generic_typed_controls':19,'source_child_typed_controls':29,'reference_order_groups_preserved':True,'independently_sealed_item_replay':replay}],'distinct_nonblind_AI_reviews_per_item':2,'human_expert_validation_n':0,'no_host_audit':audit,'scope':'Source-certified study-work-program lineage and detailed target specification impact records.'}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--bundle',type=Path,required=True);args=ap.parse_args();print(json.dumps(verify(args.bundle),ensure_ascii=False,sort_keys=True))
