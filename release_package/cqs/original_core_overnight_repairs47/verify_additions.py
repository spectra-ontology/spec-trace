#!/usr/bin/env python3
"""Replay the sealed original CR-count metadata contract offline."""
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
INVENTORY = 'f9ec65c2f19eb51c415eb8631591496e68a4b2662948acda07d612f7b3287817'
SEAL = 'a7e20360f61fcea2240732f7c4ce2ca0792036048fc705b4cf971bcdef66d4d3'
SOURCE_MANIFEST = '1361ac4846cc0d5c8dac53726bf2a8584ae6e46f9451f022cd03a0af379b72e1'
IDENTITY = 'RAN4_P1_CQ6-3'
REPAIR = 'fd4ae11928d21631419c20e19f089ca75130068fa8cc6816d419735f34c9f422'
REPAIR_FILE = '4da187460f900a526f5363631ef32194049cb99e841d8866807d28942ee4e496'
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

def native(source):
    prefix = 'native_preparation_v1/ROOT_actual_native_capture_v1/reference_outputs/' + IDENTITY + '/12f1bc8faab308b35c2c9a6863e710016120f2346f415ef7a8aedaec6a3d8949'
    meta = load(source / (prefix + '.json'))
    raw = safe(source / (prefix + '.jsonl')).read_bytes()
    positional = [parse(x) for x in raw.splitlines() if x.strip()]
    require(meta['status'] == 'OK' and meta['id'] == IDENTITY and meta['wg'] == 'RAN4', 'actual native identity/status')
    require(hashlib.sha256(raw).hexdigest() == meta['rows_sha256'] and len(raw) == meta['bytes_retained'], 'all retained native bytes')
    require(meta['query'].encode() == (source / 'reference_original_census_v2.cypher').read_bytes() and hashlib.sha256(meta['query'].encode()).hexdigest() == meta['query_sha256'], 'exact unchanged original capture')
    require(all(type(x) is list and len(x) == len(meta['columns']) for x in positional), 'native positional shape')
    require(meta['rows_retained'] == len(positional) == 1 and meta['full_rows_available'] is True and meta['truncated'] is False, 'full original scalar record')
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
            and definition['reference_query'] == definition['original_query'], 'original EN/query byte unchanged')
    require([(r['name'], r['type'], r['nullable']) for r in definition['required_fields']]
            == [('crs', 'integer', False)], 'one requested CR integer')
    require(definition['collection'] == {'kind': 'set'} and definition['cardinality_policy'] == {'mode': 'exact', 'value': 1}, 'unordered singleton count')
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
    require(replay['status'] == 'PASS_PORTABLE_ORIGINAL_CENSUS_SOURCE_NATIVE_SQL_AND_TYPED_CONTROLS' and replay['id'] == IDENTITY
            and replay['requested_fields'] == ['crs'] and replay['native_full_columns'] == ['total', 'crs']
            and replay['native_queries'] == 1 and replay['typed_controls'] == 21
            and replay['complete_frozen_memberships'] == 167442 and replay['independent_AI_reviews'] == 2
            and replay['source']['byte_exact_original_members'] == 5 and replay['human_expert_n'] == 0
            and replay['new_API_calls'] == replay['new_native'] == 0, 'complete original-census source-bound replay')
    meta, full_records = native(source)
    require(meta['columns'] == ['total', 'crs'] and meta['query'] == definition['reference_query'], 'full original two-column context')
    records = [{'crs': r['crs']} for r in full_records]
    require(exact(gold['records']) == exact(records) and 'order_groups' not in gold, 'one projected integer; no invented order groups')
    require(scorer.score(task, records, records, diagnostic=True)['exact'], 'requested CR count exact')
    generic = checks.checks(task, records)
    saved = load(gate / 'portable_typed_controls.json')
    require(len(generic) == 7 and all(row['pass'] for row in generic) and generic == saved['generic'], 'original typed controls')
    require(saved['generic_controls_n'] == 7 and saved['source_child_typed_controls_n'] == 21, 'control scopes')
    require(not scorer.score(task, records, [{'total': full_records[0]['total']}], diagnostic=True)['exact'], 'denominator-only is not the requested count')
    for name in ['scorer.py', 'typed_values.py', 'source_pins.json', 'original_scorer.py', 'contract_checks.py', 'review_schema.py']:
        require(sha(bundle / name) == sha(source / 'scoring' / name), 'unchanged scientific scoring:' + name)
    execution = load(source / 'native_preparation_v1/ROOT_actual_native_capture_v1/execution_RAN4.json')
    require(set(declaration['graph_sources']) == {'RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'}
            and exact(execution['source_before']) == exact(execution['source_after']) == exact(declaration['graph_sources']['RAN4']), 'all original graph sources')
    scope = declaration['source_certification_scope']
    require(scope['full_frozen_memberships'] == 167442 and scope['source_child_exact_file_n'] == 50
            and scope['original_source_members'] == 5 and scope['physical_document_universal_classification_claim'] is False, 'original census versus five diagnostic source witnesses')
    require(all(audit[key] == 0 for key in ['network_calls', 'SQL_calls', 'host_private_open_attempts', 'write_open_attempts', 'other_subprocess_calls'])
            and audit['expected_source_child_calls'] == 1, 'default no-host replay with only sealed source child')
    return {'status': 'PASS', 'candidate_n': 1, 'local_validated_n': 1, 'new_public_admissions': 0,
            'model_calls': 0, 'native_calls': 0, 'portable_controls_replayed': 28,
            'control_count_note': '7 outer generic plus21 child typed replayed; generic typed scopes overlap.',
            'items': [{'id': IDENTITY, 'repair_sha256': REPAIR, 'native_rows': 1, 'native_population_rows': 1,
                'native_full_columns': ['total', 'crs'], 'requested_fields': ['crs'], 'collection_kind': 'set',
                'generic_typed_controls': 7, 'source_child_typed_controls': 21, 'reference_order_groups_preserved': False,
                'independently_sealed_item_replay': replay}],
            'distinct_nonblind_AI_reviews_per_item': 2, 'human_expert_validation_n': 0, 'no_host_audit': audit,
            'scope': 'Original-authority CR census with full two-column native context and one requested count; complete frozen memberships and five source witnesses retained.'}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.bundle), ensure_ascii=False, sort_keys=True))
