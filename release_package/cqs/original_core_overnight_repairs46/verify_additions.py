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
INVENTORY = 'bbb9bdb42996ad3fd7556a6f9a16bfbe6316ed6ea8ffc2058e8500ccf1de6567'
SEAL = '1cc1b293c5b65309c8d214538c9ac18d527141ab89f8898d971a0cdae2b998db'
SOURCE_MANIFEST = '94d4b2c301f901d1258fceb03f28f8066264e2ad36bac234b830185af6ef5673'
IDENTITY = 'RAN3_P4_CQ4-2'
REPAIR = '7309bfe374e2e3f9b2770ade378ba81311dcc28f01fc49d42e45445ce032869e'
REPAIR_FILE = '4ec33383dea542db63b212b9d70115a4794ca34b102a9bd3826624f01fc71b4f'
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
    require(meta['status'] == 'OK' and meta['id'] == IDENTITY and meta['wg'] == 'RAN3', 'actual native identity/status')
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
    require(safe(__file__) == bundle / 'verify_additions.py', 'execute own verifier')
    source = bundle / 'source_evidence' / IDENTITY
    command = [sys.executable, '-B', '-I', '-S', str(source / 'verify.py')]
    child_env = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1'}
    audit, state = no_host_audit(bundle, command, child_env)
    require(sha(bundle / 'immutable_inventory.json') == INVENTORY, 'immutable inventory')
    files = load(bundle / 'immutable_inventory.json')['files']
    declaration, manifest = load(bundle / 'declarations.json'), load(bundle / 'manifest.json')
    require(exact(manifest) == exact(dict(declaration, files=files, immutable_inventory_sha256=INVENTORY,
            verifier_sha256=sha(bundle / 'verify_additions.py'))), 'exact declarations and manifest')
    expected = set(files) | {'manifest.json', 'immutable_inventory.json', 'verify_additions.py'}
    directories = {p.as_posix() for item in expected for p in Path(item).parents if p.as_posix() != '.'}
    actual = set()
    for path in bundle.rglob('*'):
        safe(path)
        if path.is_file():
            actual.add(path.relative_to(bundle).as_posix())
        else:
            require(path.relative_to(bundle).as_posix() in directories, 'extra directory')
    require(actual == expected, 'closed file tree')
    for name, info in files.items():
        rel = Path(name)
        require(not rel.is_absolute() and '..' not in rel.parts and '\\' not in name, 'safe member')
        require((bundle / name).stat().st_size == info['bytes'] and sha(bundle / name) == info['sha256'], 'payload:' + name)
    require(declaration['cohort_ids'] == [IDENTITY] and declaration['candidate_n'] == 1, 'one item')
    for key in ['new_model_calls', 'new_public_admissions', 'human_expert_n']:
        require(type(declaration[key]) is int and declaration[key] == 0, 'offline zero')
    require(sha(bundle / 'criteria.json') == CRITERIA, 'unchanged seven criteria')
    typed = local(bundle, 'typed_values')
    local(bundle, 'scorer')
    scorer, checks, schema = local(bundle, 'original_scorer'), local(bundle, 'contract_checks'), local(bundle, 'review_schema')
    tasks, golds, originals = [lines(bundle / name) for name in ['tasks.jsonl', 'reference_gold.jsonl', 'provenance/original_selected_rows.jsonl']]
    require(len(tasks) == len(golds) == len(originals) == 1, 'one complete case')
    task, gold, authored = tasks[0], golds[0], originals[0]
    definition = load(bundle / 'definitions' / (IDENTITY + '.json'))
    keys = ['id', 'question_en', 'original_query', 'reference_query', 'required_fields', 'collection', 'cardinality_policy', 'repair_class', 'original_question_preserved']
    require(set(definition) == set(keys) and hashlib.sha256(typed.json_exact(definition).encode()).hexdigest() == REPAIR, 'canonical9')
    require(task['id'] == gold['id'] == authored['id'] == IDENTITY and task['repair_sha256'] == gold['repair_sha256'] == REPAIR, 'case identity')
    require(all(exact(task[key]) == exact(definition[key]) for key in keys), 'unchanged task definition')
    require(authored['question_en'] == definition['question_en'] and authored['cypher'] == definition['original_query']
            and definition['reference_query'] != definition['original_query'], 'original authority and approval-object repair')
    require([(r['name'], r['type'], r['nullable']) for r in definition['required_fields']]
            == [('tdocNumber', 'string', False), ('reason', 'string', False), ('summary', 'string', True)], 'three complete fields')
    require(definition['collection'] == {'kind': 'top_k_boundary_ties', 'value': 5,
            'source_order_keys': [{'source_column': 'tdocNumber', 'direction': 'asc'}],
            'tie_policy': 'any_subset_at_boundary', 'within_tie_order': 'any', 'require_rank_order': False}, 'original ASC5 membership with unordered serialization')
    require(task['validation_status'] == 'validated' and task['admitted'] is False and task['model_calls'] == 0
            and task['expert_validation_n'] == 0 and task['human_author_review_completed'] is False, 'local/model/public distinction')
    gate = bundle / 'gate_evidence' / IDENTITY
    seal = load(gate / 'ROOT_final_disposition.json')
    require(sha(gate / 'ROOT_final_disposition.json') == SEAL and seal['id'] == IDENTITY
            and seal['decision'] == 'pass_local' and seal['repair_sha256'] == REPAIR and seal['criteria_sha256'] == CRITERIA, 'actual ROOT seal')
    index = load(gate / 'sealed_gate_file_index.json')
    seal_pin_keys = {key for key, value in seal.items() if isinstance(value, dict) and {'path', 'bytes', 'sha256'} <= set(value)}
    require({item['seal_key'] for item in index} == seal_pin_keys, 'all explicit sealed gate artifacts')
    for item in index:
        require(sha(gate / item['local']) == item['sha256'] == seal[item['seal_key']]['sha256']
                and (gate / item['local']).stat().st_size == item['bytes'], 'sealed artifact bytes')
    reviews = [load(gate / (label + '.json')) for label in ['primary', 'secondary']]
    for review in reviews:
        schema.check_pass(review, definition['question_en'], load(bundle / 'criteria.json')['semantic_units'],
                          criteria_sha=CRITERIA, identity_key='repair_sha256', identity_sha=REPAIR)
    require(reviews[0]['reviewer'] != reviews[1]['reviewer'], 'two distinct AI judgments')
    source_pin = seal['portable_manifest'] if 'portable_manifest' in seal else seal['portable']['manifest']
    verifier_pin = seal['portable_verifier'] if 'portable_verifier' in seal else seal['portable']['verifier']
    require(sha(source / 'manifest.json') == SOURCE_MANIFEST == source_pin['sha256']
            and sha(source / 'verify.py') == verifier_pin['sha256'], 'actual sealed source child')
    state['source_child_window'] = True
    try:
        child = subprocess.run(command, cwd=bundle, capture_output=True, text=True, timeout=180, env=child_env)
    finally:
        state['source_child_window'] = False
    require(child.returncode == 0, 'source child:' + child.stderr[-3000:])
    replay = parse(child.stdout)
    require(replay['status'] == 'PASS' and replay['id'] == IDENTITY and replay['native_counts'] == [426, 8, 5]
            and replay['source_frontier'] == [142, 145, 37] and replay['source_members'] == 15
            and replay['requested_fields'] == 10 and replay['typed_role_controls'] == 30
            and replay['approval_grammar_controls'] == 25 and replay['literal_regex_comparisons'] == 2849
            and replay['distinct_nonblind_AI_reviews'] == 2 and replay['semantic_units'] == 7
            and replay['model_calls'] == replay['human_n'] == 0, 'complete source-bound replay')
    native_rows = {kind: native(source, kind) for kind in ['original_full', 'repaired_full', 'limited']}
    require([len(native_rows[kind][1]) for kind in ['original_full', 'repaired_full', 'limited']] == [426, 8, 5], 'all three captures')
    full_meta, records = native_rows['repaired_full']
    limited_meta, selected = native_rows['limited']
    require(full_meta['columns'] == limited_meta['columns'] == ['tdocNumber', 'reason', 'summary']
            and limited_meta['query'] == definition['reference_query'] and selected == records[:5], 'canonical exact ASC5 and three-field records')
    require(exact(gold['records']) == exact(records) and len(records) == 8, 'full repaired8 gold, original426 diagnostic preserved')
    groups = scorer.make_order_groups(task, records, records)
    require(len(groups) == 8 and all(len(group) == 1 for group in groups) and exact(gold['order_groups']) == exact(groups), 'all full-native order groups')
    require(scorer.score(task, records, selected, diagnostic=True, order_groups=groups)['exact']
            and scorer.score(task, records, list(reversed(selected)), diagnostic=True, order_groups=groups)['exact'], 'complete records and unordered serialization')
    generic = checks.checks(task, records, order_groups=groups)
    saved = load(gate / 'portable_typed_controls.json')
    require(len(generic) == 15 and all(row['pass'] for row in generic) and generic == saved['generic'], 'original typed controls')
    require(saved['generic_controls_n'] == 15 and saved['source_child_typed_controls_n'] == 30
            and saved['source_child_grammar_controls_n'] == 25 and saved['literal_regex_comparisons_n'] == 2849, 'control scopes')
    for name in ['scorer.py', 'typed_values.py', 'source_pins.json', 'original_scorer.py', 'contract_checks.py', 'review_schema.py']:
        require(sha(bundle / name) == sha(source / name), 'unchanged scientific scoring:' + name)
    execution = load(source / 'native/execution_RAN3.json')
    require(set(declaration['graph_sources']) == {'RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'}
            and exact(execution['source_before']) == exact(execution['source_after']) == exact(declaration['graph_sources']['RAN3']), 'all original graph sources')
    scope = declaration['source_certification_scope']
    require(scope['full426_global_source_classifier'] is False and scope['all8_global_source_classifier'] is False
            and scope['source_child_exact_file_n'] == 82 and scope['source_positive_paths'] == 5
            and scope['source_negative_paths'] == 140, 'bounded original-source frontier')
    require(all(audit[key] == 0 for key in ['network_calls', 'SQL_calls', 'host_private_open_attempts', 'write_open_attempts', 'other_subprocess_calls'])
            and audit['expected_source_child_calls'] == 1, 'default no-host replay with only sealed source child')
    return {'status': 'PASS', 'candidate_n': 1, 'local_validated_n': 1, 'new_public_admissions': 0,
            'model_calls': 0, 'native_calls': 0, 'portable_controls_replayed': 70,
            'control_count_note': '15 outer generic plus30 child typed plus25 child grammar replayed; generic typed scopes overlap.',
            'items': [{'id': IDENTITY, 'repair_sha256': REPAIR, 'native_rows': 5, 'native_population_rows': 8,
                'original_native_population_rows': 426, 'native_full_columns': 3,
                'requested_fields': ['tdocNumber', 'reason', 'summary'], 'collection_kind': 'top_k_boundary_ties',
                'generic_typed_controls': 15, 'source_child_typed_controls': 30, 'source_child_grammar_controls': 25,
                'reference_order_groups_preserved': True, 'independently_sealed_item_replay': replay}],
            'distinct_nonblind_AI_reviews_per_item': 2, 'human_expert_validation_n': 0, 'no_host_audit': audit,
            'scope': 'Technical Agreement approval-object metadata tracing, selected complete5 records and all142 earlier CRs/145paths/37technical objects; captured metadata and unchanged scoring.'}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.bundle), ensure_ascii=False, sort_keys=True))
