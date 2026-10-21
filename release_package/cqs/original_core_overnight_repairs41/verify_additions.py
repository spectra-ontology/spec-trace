#!/usr/bin/env python3
"""Replay the sealed approved-change reason-and-summary metadata trace offline."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

sys.dont_write_bytecode = True
if sys.flags.optimize:
    raise SystemExit('Enabled checks required; -O/-OO refused')
INVENTORY = '6ee92f76d017529ef8e7e47d66e53dcffe5c3764baf67dc123c7eeff20c45463'
SEAL = '866796a37035561bf8342e4327e9d421f02733ed008f1f10cd678b511959e985'
SOURCE_MANIFEST = 'b7a2436c96de2c3973bf2c6a105864c6c49680ab14527c8934edeccfee82c72b'
IDENTITY = 'RAN2_P4_CQ4-2'
REPAIR = 'ea553590c21a113107322044a7c6bbc7647a9f16a638b5923767316feb5b10b8'
REPAIR_FILE = '93481c1e6c35041350a49c5f4bc09edd08c072e7ecc40c414968a00768a8940e'
CRITERIA = 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'

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

def native(source, kind):
    meta = load(source / ('native/' + kind + '.json'))
    raw = gzip.decompress(safe(source / ('native/' + kind + '.jsonl.gz')).read_bytes())
    positional = [parse(x) for x in raw.splitlines() if x.strip()]
    require(meta['status'] == 'OK' and meta['id'] == IDENTITY and meta['wg'] == 'RAN2', 'actual native identity/status')
    require(hashlib.sha256(raw).hexdigest() == meta['rows_sha256'] and len(raw) == meta['bytes_retained'], 'all retained native bytes')
    require(meta['query'].encode() == (source / ('queries/' + kind + '.cypher')).read_bytes() and hashlib.sha256(meta['query'].encode()).hexdigest() == meta['query_sha256'], 'exact canonical capture')
    require(all(type(x) is list and len(x) == len(meta['columns']) for x in positional), 'native positional shape')
    require(meta['rows_retained'] == len(positional) and meta['full_rows_available'] is True and meta['truncated'] is False, 'full rows available')
    return meta, [dict(zip(meta['columns'], x)) for x in positional]

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

def verify(bundle):
    bundle = safe(bundle)
    require(safe(__file__) == bundle / 'verify_additions.py', 'execute bundle own verifier')
    source = bundle / 'source_evidence' / IDENTITY
    command = [sys.executable, '-B', '-I', '-S', str(source / 'verify.py')]
    child_env = {'PATH':'/usr/bin:/bin', 'LANG':'C.UTF-8', 'PYTHONDONTWRITEBYTECODE':'1'}
    audit, audit_state = no_host_audit(bundle, command, child_env)
    require(sha(bundle / 'immutable_inventory.json') == INVENTORY, 'immutable inventory')
    files = load(bundle / 'immutable_inventory.json')['files']
    manifest = load(bundle / 'manifest.json')
    declaration = load(bundle / 'declarations.json')
    expected_manifest = dict(declaration, files=files, immutable_inventory_sha256=INVENTORY, verifier_sha256=sha(bundle / 'verify_additions.py'))
    require(exact(manifest) == exact(expected_manifest), 'exact manifest types/accounting')
    expected = set(files) | {'manifest.json', 'immutable_inventory.json', 'verify_additions.py'}
    directories = {p.as_posix() for x in expected for p in Path(x).parents if p.as_posix() != '.'}
    actual = set()
    for p in bundle.rglob('*'):
        safe(p)
        if p.is_file():
            actual.add(p.relative_to(bundle).as_posix())
        else:
            require(p.relative_to(bundle).as_posix() in directories, 'extra directory')
    require(actual == expected, 'closed file tree')
    for name, info in files.items():
        rel = Path(name)
        require(not rel.is_absolute() and '..' not in rel.parts and '\\' not in name, 'unsafe path')
        require((bundle/name).stat().st_size == info['bytes'] and sha(bundle/name) == info['sha256'], 'changed payload:' + name)
    require(declaration['cohort_ids'] == [IDENTITY] and type(declaration['candidate_n']) is int and declaration['candidate_n'] == 1, 'exact one item')
    for key in ['new_model_calls','new_public_admissions','human_expert_n']:
        require(type(declaration[key]) is int and declaration[key] == 0, 'offline zero:' + key)
    require(declaration['scientific_query_requested_fields_and_criteria_changed_by_packaging'] is False and declaration['evaluation_runtime_configuration_changed_by_packaging'] is False, 'packaging only')
    require(sha(bundle/'criteria.json') == CRITERIA, 'fixed criteria')
    typed = local(bundle, 'typed_values')
    local(bundle, 'scorer')
    original = local(bundle, 'original_scorer')
    checks = local(bundle, 'contract_checks')
    schema = local(bundle, 'review_schema')
    tasks, golds, originals = [lines(bundle/x) for x in ['tasks.jsonl','reference_gold.jsonl','provenance/original_selected_rows.jsonl']]
    require(len(tasks) == len(golds) == len(originals) == 1, 'exact one row')
    task, gold, authored = tasks[0], golds[0], originals[0]
    definition_path = bundle/'definitions'/(IDENTITY+'.json')
    definition = load(definition_path)
    keys = ['id','question_en','original_query','reference_query','required_fields','collection','cardinality_policy','repair_class','original_question_preserved']
    require(set(definition) == set(keys) and sha(definition_path) == REPAIR_FILE and hashlib.sha256(typed.json_exact(definition).encode()).hexdigest() == REPAIR, 'canonical9 file/object identities')
    require(task['id'] == gold['id'] == authored['id'] == IDENTITY and task['repair_sha256'] == gold['repair_sha256'] == REPAIR, 'cohort identity')
    require(all(exact(task[k]) == exact(definition[k]) for k in keys), 'task exact definition')
    require(definition['question_en'] == authored['question_en'] and definition['original_query'] == authored['cypher'], 'original EN/query unchanged')
    require(sha(source/'data/repair.json') == REPAIR_FILE and load(source/'data/repair.json') == definition, 'source exact canonical9')
    fields = definition['required_fields']
    require([x['name'] for x in fields] == ['tdocNumber','reason','summary'] and all(x['type'] == 'string' and x['nullable'] is False for x in fields), 'three requested typed CR fields')
    expected_collection = {'kind':'top_k_boundary_ties','value':5,'source_order_keys':[{'source_column':'tdocNumber','direction':'asc'}],'tie_policy':'any_subset_at_boundary','within_tie_order':'any','require_rank_order':False}
    require(exact(definition['collection']) == exact(expected_collection) and exact(definition['cardinality_policy']) == exact({'mode':'top_k','value':5,'tie_policy':'any_subset_at_boundary'}), 'original ASC5 membership and unrequested serialization')
    require(task['validation_status'] == 'validated' and task['admitted'] is False and task['model_calls'] == task['expert_validation_n'] == 0 and task['human_author_review_completed'] is False, 'local/public/model distinction')
    gate = bundle/'gate_evidence'/IDENTITY
    seal = load(gate/'ROOT_final_disposition.json')
    require(sha(gate/'ROOT_final_disposition.json') == SEAL and seal['decision'] == 'pass_local' and seal['repair_sha256'] == REPAIR and seal['criteria_sha256'] == CRITERIA, 'ROOT seal')
    for item in load(gate/'sealed_gate_file_index.json'):
        require(sha(gate/item['local']) == item['sha256'] == seal[item['seal_key']]['sha256'] and (gate/item['local']).stat().st_size == item['bytes'] == seal[item['seal_key']]['bytes'], 'sealed evidence')
    require(seal['canonical_repair']['sha256'] == REPAIR_FILE, 'actual canonical file seal')
    reviews = [load(gate/(s+'.json')) for s in ['primary','secondary']]
    for review in reviews:
        schema.check_pass(review, definition['question_en'], load(bundle/'criteria.json')['semantic_units'], criteria_sha=CRITERIA, identity_key='repair_sha256', identity_sha=REPAIR)
    require(reviews[0]['reviewer'] != reviews[1]['reviewer'] and reviews[1]['reviewer'] == '/root', 'distinct AI reviewers')
    require(sha(source/'manifest.json') == SOURCE_MANIFEST == seal['portable_manifest']['sha256'] and sha(source/'verify.py') == seal['portable_verifier']['sha256'] and sha(source/'immutable_inventory.json') == seal['portable_inventory']['sha256'], 'sealed immutable source package')
    require(sum(p.is_file() for p in source.rglob('*')) == 56, 'all56 immutable source files')
    for name in ['scorer.py','typed_values.py','source_pins.json','original_scorer.py','contract_checks.py','review_schema.py']:
        require((bundle/name).read_bytes() == (source/name).read_bytes(), 'unchanged kernel and review schema:' + name)
    require((bundle/'requested_controls.py').read_bytes() == (source/'requested_controls.py').read_bytes(), 'unchanged requested-role controls')
    audit_state['source_child_window'] = True
    try:
        child = subprocess.run(command, cwd=bundle, text=True, capture_output=True, timeout=180, env=child_env)
    finally:
        audit_state['source_child_window'] = False
    require(child.returncode == 0, 'source replay:' + child.stderr)
    replay = parse(child.stdout)
    source_counts = {'original_archives':8,'original_binary_members':7,'original_OOXML_members':1,'requested_source_fields':10,'active_approval_roles':5,'report_target_windows':18,'retained_struck_literal_characters':17}
    require(replay['status'] == 'PASS' and replay['id'] == IDENTITY and replay['native_counts'] == [162,5] and exact(replay['source_reopened']) == exact(source_counts), 'actual source/native replay scope')
    require(replay['captured_input_counts'] == [34622,3413,2192] and replay['frontier_counts'] == [7127,104,374,5], 'complete captured input and original ASC frontier')
    require(replay['requested_role_controls'] == 27 and replay['distinct_nonblind_AI_reviews'] == 2 and replay['semantic_units'] == 7 and replay['human_n'] == replay['model_calls'] == 0, 'actual27 controls and original7 reviews')
    require(all(replay['no_host_audit'][k] == 0 for k in ['network_calls','subprocess_calls','SQL_calls','host_private_open_attempts','write_open_attempts']), 'child no-host audit')
    require(exact(seal['counts']) == exact(replay), 'ROOT seal exact actual child replay')
    scope = {'frozen_CR_records':34622,'frozen_Agreements':3413,'captured_Agreement_REFERENCE_CR_paths':2192,'full_native_CR_population':162,'raw_metadata_REFERENCE_paths':165,'unfiltered_pre_cutoff_CR':7127,'captured_metadata_prefix':104,'captured_reference_prefix':374,'source_certified_selected_CR':5,'requested_source_fields':10,'original_source_archives':8,'active_approval_roles':5,'all_report_target_windows':18,'retained_struck_literal_characters':17,'full162_global_approval_classifier':False,'native_counts_full_limited':[162,5],'source_child_unchanged_file_n':56}
    require(exact(declaration['source_certification_scope']) == exact(scope), 'exact bounded source certification')
    authority = seal['counterauthority_preserved']
    expected_authority = {'full_frozen_CR':34622,'full_frozen_Agreement':3413,'original_REFERENCES_to_CR_paths':2192,'unfiltered_pre_cutoff_CR':7127,'captured_metadata_prefix':104,'captured_reference_prefix':374,'selected_CR':5,'actual_original_archives':8,'requested_source_fields':10,'active_original_approval_roles':5,'report_target_windows':18,'struck_summary_literal_characters_preserved':17,'full162_global_approval_classifier':False,'source_null_asserted_empty':False,'specific_authored_ASC5_selection_preserved':True,'unrequested_serialization_order_required':False}
    require(exact(authority) == exact(expected_authority), 'ROOT-certified original captured-field frontier and literal source interpretation')
    captured = {kind:native(source,kind) for kind in ['full','limited']}
    full_meta, records = captured['full']
    meta, requested = captured['limited']
    require([len(records),len(requested)] == [162,5] and meta['columns'] == full_meta['columns'] == ['tdocNumber','reason','summary'], 'both complete three-column native outputs')
    require(meta['query'] == definition['reference_query'] == definition['original_query'] and task['reference_query_sha256'] == meta['query_sha256'], 'canonical exact original native query')
    require(requested == records[:5] and all(type(v) is str for r in records for v in r.values()), 'original selected5 typed complete records')
    require(len({r['tdocNumber'] for r in records}) == 162 and [r['tdocNumber'] for r in records] == sorted(r['tdocNumber'] for r in records), 'DISTINCT CR and original tdoc order')
    execution = load(source/'native/execution_RAN2.json')
    require(set(declaration['graph_sources']) == {'RAN1','RAN2','RAN3','RAN4','RAN5'} and exact(execution['source_before']) == exact(execution['source_after']) == exact(declaration['graph_sources']['RAN2']), 'frozen graph binding')
    groups = original.make_order_groups(task, records, records)
    require(typed.json_exact(gold['records']) == typed.json_exact(records) and typed.json_exact(gold['order_groups']) == typed.json_exact(groups) and len(groups) == 162 and all(len(g) == 1 for g in groups), 'all original162 ranking groups')
    require(original.score(task, records, requested, diagnostic=True, order_groups=groups)['exact'], 'native requested positive')
    controls = load(gate/'portable_typed_controls.json')
    actual = local(bundle,'requested_controls').run(task, records, original, checks)
    require(actual['n'] == controls['total_controls_n'] == 27 and len(actual['generic']) == 15 and len(actual['requested']) == 12, 'actual15 generic and12 requested-role controls')
    require(exact(actual['generic']) == exact(controls['generic_controls']) and exact(actual['requested']) == exact(controls['requested_role_controls']), 'outer controls independently replayed')
    prior = load(source/'data/actual_requested_controls.json')
    require(prior['actual_controls_n'] == 27 and prior['generic_controls_n'] == 15 and prior['requested_role_controls_n'] == 12 and exact(prior['reference']) == exact(requested), 'original source controls and requested records')
    normalized = [dict(check=x['check'], pass_=x['pass'], expected_exact=x['expected_exact'], result=x['result']) for x in prior['requested_role_controls']]
    require(exact(prior['generic_controls']) == exact(actual['generic']) and exact(normalized) == exact(actual['requested']), 'same original27 scientific controls')
    require(audit['expected_source_child_calls'] == 1 and all(audit[k] == 0 for k in ['network_calls','SQL_calls','host_private_open_attempts','write_open_attempts','other_subprocess_calls']), 'offline outer audit')
    return {
        'status':'PASS','candidate_n':1,'local_validated_n':1,'new_public_admissions':0,
        'model_calls':0,'native_calls':0,'portable_controls_replayed':27,
        'items':[{'id':IDENTITY,'repair_sha256':REPAIR,'native_rows':5,'native_full_columns':3,
                  'native_reference_population_rows':162,'requested_fields':['tdocNumber','reason','summary'],
                  'collection_kind':'top_k_boundary_ties','generic_typed_controls':15,
                  'source_child_requested_role_controls':27,'requested_role_controls':12,
                  'independently_sealed_item_replay':replay}],
        'source_certification_scope':scope,'distinct_nonblind_AI_reviews_per_item':2,
        'human_expert_validation_n':0,'no_host_audit':audit,
        'scope':'Source-verified approved-change metadata: five complete CR reason-and-summary records from the original captured-field gate and tdoc ASC5; original fields10, active approval roles5 and full162 selection population are reproduced.'}

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bundle', type=Path, required=True)
    args = ap.parse_args()
    print(json.dumps(verify(args.bundle), ensure_ascii=False, sort_keys=True))
