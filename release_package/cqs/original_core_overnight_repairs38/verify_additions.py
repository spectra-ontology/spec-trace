#!/usr/bin/env python3
"""Replay the sealed recorded contribution-rate addition offline."""
import argparse
import collections
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
if sys.flags.optimize:
    raise SystemExit('Enabled checks required; -O/-OO refused')
INVENTORY = '8972d0903fb46b1e0a0b29ce2bf19d9b9bc89126027311ea9b5a1f0e7876929f'
SEAL = 'b71c754bdd53c304398f178cc102028b3550f02ca6b28ce43d4312e1bf465b83'
SOURCE_MANIFEST = 'd6565fd3a473e2ceb1a6547b2f1942033e2280a60174570271b29f25a6617896'
IDENTITY = 'RAN2_P2_CQ6-2'
REPAIR = '2e686158064dfef7f6e830e55ef1e1c8f342a2b37f402a3165068be957e5ca35'
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

def load(p):
    return json.loads(safe(p).read_text(), object_pairs_hook=pairs)

def lines(p):
    return [json.loads(s, object_pairs_hook=pairs) for s in safe(p).read_text().splitlines() if s.strip()]

def exact(v):
    return json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(',', ':'))

def local(bundle, name):
    spec = importlib.util.spec_from_file_location(name, safe(bundle / (name + '.py')))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

def verify(bundle):
    bundle = safe(bundle)
    require(safe(__file__) == bundle / 'verify_additions.py', 'execute bundle own verifier')
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
        require((bundle / name).stat().st_size == info['bytes'] and sha(bundle / name) == info['sha256'], 'changed payload:' + name)
    require(declaration['cohort_ids'] == [IDENTITY] and type(declaration['candidate_n']) is int and declaration['candidate_n'] == 1, 'exact one item')
    for key in ['new_model_calls', 'new_public_admissions', 'human_expert_n']:
        require(type(declaration[key]) is int and declaration[key] == 0, 'offline zero:' + key)
    require(sha(bundle / 'criteria.json') == CRITERIA, 'fixed criteria')
    typed = local(bundle, 'typed_values')
    local(bundle, 'scorer')
    original = local(bundle, 'original_scorer')
    checks = local(bundle, 'contract_checks')
    schema = local(bundle, 'review_schema')
    tasks, golds, originals = [lines(bundle / x) for x in ['tasks.jsonl', 'reference_gold.jsonl', 'provenance/original_selected_rows.jsonl']]
    require(len(tasks) == len(golds) == len(originals) == 1, 'exact one row')
    task, gold, authored = tasks[0], golds[0], originals[0]
    definition = load(bundle / 'definitions' / (IDENTITY + '.json'))
    keys = ['id', 'question_en', 'original_query', 'reference_query', 'required_fields', 'collection', 'cardinality_policy', 'repair_class', 'original_question_preserved']
    require(set(definition) == set(keys) and hashlib.sha256(typed.json_exact(definition).encode()).hexdigest() == REPAIR, 'canonical9 identity')
    require(task['id'] == gold['id'] == authored['id'] == IDENTITY and task['repair_sha256'] == gold['repair_sha256'] == REPAIR, 'cohort identity')
    require(all(exact(task[k]) == exact(definition[k]) for k in keys), 'task exact definition')
    require(definition['question_en'] == authored['question_en'] and definition['reference_query'] == definition['original_query'] == authored['cypher'], 'original query unchanged')
    require(definition['required_fields'] == [{'name': 'canonicalMeetingNumber', 'type': 'string', 'nullable': False, 'source_column_or_expression': 'm.canonicalMeetingNumber'}, {'name': 'ratio', 'type': 'number', 'nullable': False, 'source_column_or_expression': 'ratio'}], 'exact two requested roles')
    require(definition['collection'] == {'kind': 'native_ordered_ties', 'source_order_keys': [{'source_column': 'm.meetingNumberInt', 'direction': 'asc'}], 'tie_policy': 'any_order_within_equal_keys'} and definition['cardinality_policy'] == {'mode': 'exact', 'value': 52}, 'original full trend/numeric ties')
    require(task['validation_status'] == 'validated' and task['admitted'] is False and task['model_calls'] == 0 and task['expert_validation_n'] == 0 and task['human_author_review_completed'] is False, 'local/public/model distinction')
    gate = bundle / 'gate_evidence' / IDENTITY
    seal = load(gate / 'ROOT_final_disposition.json')
    require(sha(gate / 'ROOT_final_disposition.json') == SEAL and seal['decision'] == 'pass_local' and seal['repair_sha256'] == REPAIR, 'ROOT seal')
    for item in load(gate / 'sealed_gate_file_index.json'):
        require(sha(gate / item['local']) == item['sha256'] == seal[item['seal_key']]['sha256'], 'sealed evidence')
    reviews = [load(gate / (s + '.json')) for s in ['primary', 'secondary']]
    for review in reviews:
        schema.check_pass(review, definition['question_en'], load(bundle / 'criteria.json')['semantic_units'], criteria_sha=CRITERIA, identity_key='repair_sha256', identity_sha=REPAIR)
    require(reviews[0]['reviewer'] != reviews[1]['reviewer_identity'], 'distinct AI reviewers')
    source = bundle / 'source_evidence' / IDENTITY
    require(sha(source / 'manifest.json') == SOURCE_MANIFEST == seal['portable_manifest']['sha256'] and sha(source / 'reproduce.py') == seal['portable_verifier']['sha256'], 'sealed source package')
    child = subprocess.run([sys.executable, '-B', '-I', '-S', str(source / 'reproduce.py')], cwd=bundle, text=True, capture_output=True, timeout=180, env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1'})
    require(child.returncode == 0, 'source replay:' + child.stderr)
    replay = json.loads(child.stdout)
    require(replay['status'] == 'PASS' and replay['repair_sha256'] == REPAIR and replay['recorded_source_markers'] == 3773 and replay['Huawei_positive_Resolution_n'] == 742 and replay['native_n'] == 52 and replay['all_full_five_columns_equal'] is True, 'complete recorded/source/native replay')
    metadata = load(source / 'execution/native_case.json')
    raw = source / 'execution/native_rows.jsonl'
    native = [dict(zip(metadata['columns'], x)) for x in lines(raw)]
    require(sha(raw) == metadata['rows_sha256'] and metadata['query'] == definition['reference_query'] and len(native) == 52, 'native identity/full output')
    requested = [{'canonicalMeetingNumber': x['m.canonicalMeetingNumber'], 'ratio': x['ratio']} for x in native]
    groups = original.make_order_groups(definition, native, requested)
    require(typed.json_exact(gold['records']) == typed.json_exact(requested) and typed.json_exact(gold['order_groups']) == typed.json_exact(groups), 'requested gold and native helper order groups')
    require(original.score(task, requested, requested, diagnostic=True, order_groups=groups)['exact'], 'native requested positive')
    generic = checks.checks(task, requested, order_groups=groups)
    require(len(generic) == 10 and all(x['pass'] for x in generic) and generic == load(gate / 'portable_typed_controls.json')['generic_controls'], 'two-role generic controls')
    with tempfile.TemporaryDirectory(prefix='rate27-') as tmp:
        diag = Path(tmp) / 'diagnostic_controls'
        shutil.copytree(bundle / 'diagnostic_controls', diag)
        p = subprocess.run([sys.executable, '-B', '-I', '-S', str(diag / 'current/replay_requested_two_field_scoring.py')], cwd=tmp, text=True, capture_output=True, timeout=30)
        require(p.returncode == 0, 'unchanged27 controls:' + p.stderr)
        typed_result = load(diag / 'current/actual_requested_two_field_scoring_controls.json')
        require(typed_result['status'] == 'PASS' and typed_result['checks_n'] == 27, 'all27 controls')
    return {'status': 'PASS', 'candidate_n': 1, 'local_validated_n': 1, 'new_public_admissions': 0, 'model_calls': 0, 'native_calls': 0,
            'portable_controls_replayed': 37, 'items': [{'id': IDENTITY, 'repair_sha256': REPAIR, 'native_rows': 52, 'native_full_columns': 5,
            'requested_fields': ['canonicalMeetingNumber', 'ratio'], 'collection_kind': 'native_ordered_ties', 'generic_typed_controls': 10,
            'source_child_requested_role_controls': 27, 'independently_sealed_item_replay': replay}], 'distinct_nonblind_AI_reviews_per_item': 2,
            'human_expert_validation_n': 0, 'scope': 'One original full52 meeting contribution-rate trend with3773 fixed recorded units,742 documentary Huawei units and explicit native numeric tie groups.'}

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bundle', type=Path, required=True)
    args = ap.parse_args()
    print(json.dumps(verify(args.bundle), ensure_ascii=False, sort_keys=True))
