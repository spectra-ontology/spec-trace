#!/usr/bin/env python3
"""Replay the sealed original CR-proposal approval trace addition offline."""
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
INVENTORY = '09f954527c0584537f6d593bc93f1504d832456f6101c4e5ecdddf147a3c2625'
SEAL = '1ffe5c3af63e94dd85773b10595a45b3c704f00f9c4c56cf817adf316b312573'
SOURCE_MANIFEST = 'd9f6aacad8f821395d029ff2f59e4920f45eb3cc759bf5e645e91e51e2cb8bcf'
IDENTITY = 'RAN1_P2_CQ2-3'
REPAIR = '2ac61068644d56f1be7dc443ecf295dd1e53f04a2a019a78dc6bfad9f44461fb'
REPAIR_FILE = 'c4b8b596e2de6243f0da74f66587266314e5a1d20dc4ed501c88801049793192'
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
    require(meta['status'] == 'OK' and meta['id'] == IDENTITY and meta['wg'] == 'RAN1', 'actual native identity/status')
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
    require(len(definition['required_fields']) == 1 and definition['required_fields'][0]['name'] == 'a.resolutionId' and definition['required_fields'][0]['type'] == 'string' and definition['required_fields'][0]['nullable'] is False, 'requested typed Agreement identity')
    expected_collection = {'kind':'top_k_boundary_ties','value':15,'source_order_keys':[{'source_column':'__source_order_sequence','direction':'asc'},{'source_column':'a.resolutionId','direction':'asc'}],'tie_policy':'any_subset_at_boundary','within_tie_order':'any','require_rank_order':False}
    require(exact(definition['collection']) == exact(expected_collection) and exact(definition['cardinality_policy']) == exact({'mode':'top_k','value':15,'tie_policy':'any_subset_at_boundary'}), 'original membership and unrequested serialization')
    require(task['validation_status'] == 'validated' and task['admitted'] is False and task['model_calls'] == task['expert_validation_n'] == 0 and task['human_author_review_completed'] is False, 'local/public/model distinction')
    gate = bundle/'gate_evidence'/IDENTITY
    seal = load(gate/'ROOT_final_disposition.json')
    require(sha(gate/'ROOT_final_disposition.json') == SEAL and seal['decision'] == 'pass_local' and seal['repair_sha256'] == REPAIR, 'ROOT seal')
    for item in load(gate/'sealed_gate_file_index.json'):
        require(sha(gate/item['local']) == item['sha256'] == seal[item['seal_key']]['sha256'] and (gate/item['local']).stat().st_size == item['bytes'] == seal[item['seal_key']]['bytes'], 'sealed evidence')
    require(seal['canonical_repair']['sha256'] == REPAIR_FILE, 'actual canonical file seal')
    reviews = [load(gate/(s+'.json')) for s in ['primary','secondary']]
    for review in reviews:
        schema.check_pass(review, definition['question_en'], load(bundle/'criteria.json')['semantic_units'], criteria_sha=CRITERIA, identity_key='repair_sha256', identity_sha=REPAIR)
    require(reviews[0]['reviewer'] != reviews[1]['reviewer'] and reviews[1]['reviewer'] == '/root', 'distinct AI reviewers')
    require(sha(source/'manifest.json') == SOURCE_MANIFEST == seal['portable_manifest']['sha256'] and sha(source/'verify.py') == seal['portable_verifier']['sha256'] and sha(source/'immutable_inventory.json') == seal['portable_inventory']['sha256'], 'sealed immutable source package')
    require(sum(p.is_file() for p in source.rglob('*')) == 59, 'all59 immutable source files')
    for name in ['scorer.py','typed_values.py','source_pins.json','original_scorer.py','contract_checks.py','review_schema.py']:
        require((bundle/name).read_bytes() == (source/name).read_bytes(), 'unchanged kernel and review schema:' + name)
    audit_state['source_child_window'] = True
    try:
        child = subprocess.run(command, cwd=bundle, text=True, capture_output=True, timeout=180, env=child_env)
    finally:
        audit_state['source_child_window'] = False
    require(child.returncode == 0, 'source replay:' + child.stderr)
    replay = parse(child.stdout)
    require(replay['status'] == 'PASS' and replay['id'] == IDENTITY and replay['native_counts'] == [156,156,15] and replay['source_reopened'] == {'own16':16,'external6':6,'all55':55}, 'actual source/native replay scope')
    require(replay['requested_role_controls'] == 14 and replay['distinct_nonblind_AI_reviews'] == 2 and replay['semantic_units'] == 7 and replay['human_n'] == replay['model_calls'] == 0, 'actual child14 controls and original7 reviews')
    require(all(replay['no_host_audit'][k] == 0 for k in ['network_calls','subprocess_calls','SQL_calls','host_private_open_attempts','write_open_attempts']), 'child no-host audit')
    scope = {'original_meeting_Agreements':357,'source_certified_selected_Agreement_identities':15,'complete_unfiltered_selection_prefix':44,'selection_prefix_CR_proposals':15,'selection_prefix_other':29,'additional_original_source_role_comparisons':55,'all55_CR_proposals':17,'all55_other':38,'retained_lexical_rank_rows':156,'lexical156_global_CR_role_certified':False,'native_counts_rank_full_limited':[156,156,15],'selected_cutoff_unique':True,'source_child_unchanged_file_n':59}
    require(exact(declaration['source_certification_scope']) == exact(scope), 'exact bounded source certification')
    authority = seal['counterauthority_preserved']
    require(authority['original_population'] == 357 and authority['unfiltered_prefix'] == 44 and authority['source_positive'] == 15 and authority['source_other'] == 29 and authority['all55_positive'] == 17 and authority['all55_other'] == 38 and authority['full156_lexical_rows_are_order_evidence_not_global_role_gold'] is True, 'ROOT-certified finite frontier')
    captured = {kind:native(source,kind) for kind in ['rank','full','limited']}
    rank_meta, rank = captured['rank']
    full_meta, full = captured['full']
    meta, limited = captured['limited']
    require([len(rank),len(full),len(limited)] == [156,156,15] and meta['columns'] == full_meta['columns'] == ['a.resolutionId','a.content'] and rank_meta['columns'] == ['a.resolutionId','a.content','__source_order_sequence'], 'all three native outputs')
    require(meta['query'] == definition['reference_query'] and task['reference_query_sha256'] == meta['query_sha256'], 'canonical exact native query')
    execution = load(source/'native/execution_RAN1.json')
    require(set(declaration['graph_sources']) == {'RAN1','RAN2','RAN3','RAN4','RAN5'} and exact(execution['source_before']) == exact(execution['source_after']) == exact(declaration['graph_sources']['RAN1']), 'frozen graph binding')
    records = [{'a.resolutionId':x['a.resolutionId']} for x in full]
    requested = [{'a.resolutionId':x['a.resolutionId']} for x in limited]
    groups = original.make_order_groups(task, rank, records)
    require(typed.json_exact(gold['records']) == typed.json_exact(records) and typed.json_exact(gold['order_groups']) == typed.json_exact(groups) and len(groups) == 156 and all(len(g) == 1 for g in groups), 'all original ranking groups')
    require(original.score(task, records, requested, diagnostic=True, order_groups=groups)['exact'], 'native requested positive')
    generic = checks.checks(task, records, groups)
    controls = load(gate/'portable_typed_controls.json')
    require(len(generic) == 9 and all(x['pass'] for x in generic) and generic == controls['generic_controls'], 'actual nine generic controls')
    prior = load(source/'data/actual_SQL_requested_controls.json')
    require(prior['controls_n'] == len(prior['checks']) == controls['total_controls_n'] == 14 and prior['reference'] == requested, 'same original14 controls')
    expected_names = ['reversed_identity_serialization','excluded_bare_TP1_displaces_selected_CR','actual_CR_form_named_TP_raw44_omitted','selected_CR_form_raw44_replaced_with_later_CR','unrequested_content_not_mandatory']
    require([x['check'] for x in controls['source_role_controls']] == expected_names, 'exact five source-role controls')
    for test in controls['source_role_controls']:
        result = original.score(task, records, test['prediction'], diagnostic=True, order_groups=groups)
        old = next(x for x in prior['checks'] if x['check'] == test['check'])
        require(typed.json_exact(result) == typed.json_exact(test['actual']) == typed.json_exact(old['result']) and result['exact'] is test['expected_exact'], 'actual source-role scoring:' + test['check'])
    require(audit['expected_source_child_calls'] == 1 and all(audit[k] == 0 for k in ['network_calls','SQL_calls','host_private_open_attempts','write_open_attempts','other_subprocess_calls']), 'offline outer audit')
    return {
        'status':'PASS','candidate_n':1,'local_validated_n':1,'new_public_admissions':0,
        'model_calls':0,'native_calls':0,'portable_controls_replayed':14,
        'items':[{'id':IDENTITY,'repair_sha256':REPAIR,'native_rows':15,'native_full_columns':2,
                  'native_reference_population_rows':156,'requested_fields':['a.resolutionId'],
                  'collection_kind':'top_k_boundary_ties','generic_typed_controls':9,
                  'source_child_requested_role_controls':14,'source_role_controls':5,
                  'independently_sealed_item_replay':replay}],
        'source_certification_scope':scope,'distinct_nonblind_AI_reviews_per_item':2,
        'human_expert_validation_n':0,'no_host_audit':audit,
        'scope':'Source-certified first15 CR-proposal approval Agreement identities, complete unfiltered prefix44 and additional55-role review; native full156 retains lexical order evidence.'}

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bundle', type=Path, required=True)
    args = ap.parse_args()
    print(json.dumps(verify(args.bundle), ensure_ascii=False, sort_keys=True))

