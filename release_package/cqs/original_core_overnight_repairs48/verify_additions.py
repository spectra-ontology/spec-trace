#!/usr/bin/env python3
"""Replay the sealed source-certified joint impact contract offline."""
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
INVENTORY = '2f95553d5e5ab26bf9e11dbcc263767294dc08e1d16a7e785d2b33263a4384b8'
SEAL = '69d8951e12106050bb9de2b5aa9a03eedf44da0e8f500b398b85bf85278a42ad'
SOURCE_MANIFEST = '58010df9a0aac57bb1a8b1b6c389c855cd507b7700dd0459f6dc288c371ba9eb'
IDENTITY = 'RAN1_P4_CQ2-3'
REPAIR = '032c4939f0b9e2640d29f874fbf53b725533a261545e12400cce6e9f9abeb541'
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


def leaf(value, keys):
    for key in keys:
        value = value[key]
    return value


def pin_paths(value, prefix=()):
    if isinstance(value, dict) and {'path', 'bytes', 'sha256'} <= set(value):
        yield prefix
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from pin_paths(item, prefix + (key,))


def captured(source, name):
    meta = load(source / ('native/' + name + '.json'))
    raw = gzip.decompress(safe(source / ('native/' + name + '.jsonl.gz')).read_bytes())
    require(hashlib.sha256(raw).hexdigest() == meta['rows_sha256'], 'Actual saved native rows')
    positional = [parse(line) for line in raw.splitlines() if line.strip()]
    require(meta['status'] == 'OK' and meta['rows_retained'] == len(positional) == 1
            and meta['columns'] == ['sp.specNumber', 'crCount', 'sampleCRs'], 'One full three-column native record')
    require(meta['truncated'] is False and meta['full_rows_available'] is True
            and meta['query_sha256'] == hashlib.sha256(meta['query'].encode()).hexdigest(), 'Full native and exact query')
    require(all(type(row) is list and len(row) == 3 for row in positional), 'Native positional shape')
    return meta, [dict(zip(['specNumber', 'crCount', 'sampleCRs'], row)) for row in positional]


def verify(bundle):
    bundle = safe(bundle)
    require(safe(__file__) == bundle / 'verify_additions.py', 'Execute own verifier')
    source = bundle / 'source_evidence' / IDENTITY
    command = [sys.executable, '-B', '-I', '-S', str(source / 'reproduce.py')]
    child_env = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1'}
    audit, state = no_host_audit(bundle, command, child_env)
    require(sha(bundle / 'immutable_inventory.json') == INVENTORY, 'Immutable inventory')
    files = load(bundle / 'immutable_inventory.json')['files']
    declaration, manifest = load(bundle / 'declarations.json'), load(bundle / 'manifest.json')
    require(exact(manifest) == exact(dict(declaration, files=files, immutable_inventory_sha256=INVENTORY,
            verifier_sha256=sha(bundle / 'verify_additions.py'))), 'Exact declarations and manifest')
    expected = set(files) | {'manifest.json', 'immutable_inventory.json', 'verify_additions.py'}
    directories = {p.as_posix() for item in expected for p in Path(item).parents if p.as_posix() != '.'}
    actual = set()
    for path in bundle.rglob('*'):
        safe(path)
        if path.is_file():
            actual.add(path.relative_to(bundle).as_posix())
        else:
            require(path.relative_to(bundle).as_posix() in directories, 'Extra directory')
    require(actual == expected, 'Closed file tree')
    for name, info in files.items():
        rel = Path(name)
        require(not rel.is_absolute() and '..' not in rel.parts and '\\' not in name, 'Safe member')
        require(type(info['bytes']) is int and (bundle / name).stat().st_size == info['bytes']
                and sha(bundle / name) == info['sha256'], 'Payload:' + name)
    require(declaration['cohort_ids'] == [IDENTITY] and type(declaration['candidate_n']) is int
            and declaration['candidate_n'] == 1, 'One item')
    for key in ['new_model_calls', 'new_public_admissions', 'human_expert_n']:
        require(type(declaration[key]) is int and declaration[key] == 0, 'Offline zero')
    require(sha(bundle / 'criteria.json') == CRITERIA, 'Original seven criteria')
    typed = local(bundle, 'typed_values')
    local(bundle, 'scorer')
    local(bundle, 'original_scorer')
    schema = local(bundle, 'review_schema')
    local(bundle, 'one_record_sample_scorer')
    dispatch = local(bundle, 'item_scorer_dispatch')
    entrypoint = local(bundle, 'score_predictions_joint_sample')
    tasks, golds, originals = [lines(bundle / name) for name in ['tasks.jsonl', 'reference_gold.jsonl', 'provenance/original_selected_rows.jsonl']]
    require(len(tasks) == len(golds) == len(originals) == 1, 'One original complete case')
    task, gold, authored = tasks[0], golds[0], originals[0]
    definition = load(bundle / 'definitions' / (IDENTITY + '.json'))
    keys = ['id','question_en','original_query','reference_query','required_fields','collection','cardinality_policy','repair_class','original_question_preserved']
    require(set(definition) == set(keys) and hashlib.sha256(typed.json_exact(definition).encode()).hexdigest() == REPAIR, 'Canonical9 binding')
    require(task['id'] == gold['id'] == authored['id'] == IDENTITY and task['repair_sha256'] == gold['repair_sha256'] == REPAIR, 'Exact task/gold/original identity')
    require(all(exact(task[key]) == exact(definition[key]) for key in keys), 'Unchanged canonical definition')
    require(authored['question_en'] == definition['question_en'] and authored['cypher'] == definition['original_query'], 'Original English/query')
    require(definition == load(source / 'contract/definition.json'), 'Source-certified exact repaired field query')
    require(task['validation_status'] == 'validated' and task['admitted'] is False and type(task['model_calls']) is int
            and task['model_calls'] == 0 and task['expert_validation_n'] == 0 and task['human_author_review_completed'] is False, 'Local versus public/model state')
    gate = bundle / 'gate_evidence' / IDENTITY
    seal = load(gate / 'ROOT_final_disposition.json')
    require(sha(gate / 'ROOT_final_disposition.json') == SEAL and seal['id'] == IDENTITY
            and seal['decision'] == 'pass_local' and seal['repair_sha256'] == REPAIR and seal['criteria_sha256'] == CRITERIA, 'ROOT seal')
    index = load(gate / 'sealed_gate_file_index.json')
    require({tuple(item['seal_key_path']) for item in index} == set(pin_paths(seal)), 'All direct and nested sealed gate pins')
    for item in index:
        original = leaf(seal, item['seal_key_path'])
        require(sha(gate / item['local']) == item['sha256'] == original['sha256']
                and (gate / item['local']).stat().st_size == item['bytes'] == original['bytes'], 'Actual sealed artifact bytes')
    reviews = [load(gate / (label + '.json')) for label in ['primary','secondary']]
    for review in reviews:
        schema.check_pass(review, definition['question_en'], load(bundle / 'criteria.json')['semantic_units'],
            criteria_sha=CRITERIA, identity_key='repair_sha256', identity_sha=REPAIR)
    require(reviews[0]['reviewer'] != reviews[1]['reviewer'], 'Two distinct nonblind AI reviews')
    require(sha(source / 'manifest.json') == SOURCE_MANIFEST == seal['completion_evidence']['portable_manifest']['sha256']
            and sha(source / 'reproduce.py') == seal['completion_evidence']['portable_verifier']['sha256'], 'Actual sealed source package')
    state['source_child_window'] = True
    try:
        child = subprocess.run(command, cwd=bundle, capture_output=True, text=True, timeout=180, env=child_env)
    finally:
        state['source_child_window'] = False
    require(child.returncode == 0, 'Source replay:' + child.stderr[-3000:])
    replay = parse(child.stdout)
    require(replay['status'] == 'PASS' and replay['new_admissions'] == 0
            and len(replay['cases']) == 1 and replay['cases'][0]['id'] == IDENTITY, 'Complete source-bound replay')
    limited_meta, records = captured(source, 'limited')
    _, full = captured(source, 'full')
    require(limited_meta['query'] == definition['reference_query'], 'Exact native repaired query')
    pool = load(bundle / 'sample_pools' / (IDENTITY + '.json'))
    require(pool == gold['sample_pool'] == load(source / 'data/complete_eligible_sample_pool.json')
            and type(pool) is list and len(pool) == len(set(pool)) == 129
            and sorted(pool) == sorted(full[0]['sampleCRs']) and full[0]['crCount'] == 129, 'Complete eligible129 population')
    require(gold['sample_pool_source'] == {'path': 'sample_pools/' + IDENTITY + '.json',
            'sha256': sha(bundle / 'sample_pools' / (IDENTITY + '.json'))}, 'Explicit original gold-sidecar pool')
    require(exact(gold['records']) == exact(records) and 'order_groups' not in gold, 'Actual native complete one-row gold')
    require(dispatch.score(task, records, records, sample_pool=pool)['exact'], 'Actual native joint complete match')
    controls = load(source / 'data/scoring_controls.json')
    require(controls['positive_n'] == 4 and controls['negative_n'] == 26 and len(controls['tests']) == 30, 'Frozen typed control coverage')
    for item in controls['tests']:
        result = dispatch.score(task, records, item['records'], sample_pool=pool)
        require(result['exact'] is item['expected_exact'] and result['gold_records'] == 1
                and result['f1'] in (0.0,1.0), 'Joint complete-record control:' + item['name'])
    original_reader = safe(bundle / 'score_predictions.py').read_text()
    prepared = load(bundle / 'scoring_extension.json')
    for before, after in prepared['exact_replacements']:
        require(original_reader.count(before) == 1, 'Explicit reader exact source substitution')
        original_reader = original_reader.replace(before, after)
    require(original_reader == safe(bundle / 'score_predictions_joint_sample.py').read_text(), 'Historical original reader preserved; explicit prospective entrypoint')
    # Read the supplied tasks/gold through the real scoring entrypoint with an in-memory path interface.
    class MemoryLines:
        def __init__(self, rows):
            self.raw = ''.join(json.dumps(row) + '\n' for row in rows)
        def read_text(self):
            return self.raw
        def read_bytes(self):
            return self.raw.encode()
    alternative = [dict(records[0], sampleCRs=list(reversed(pool[-10:])))]
    pred = [{'id': IDENTITY, 'repair_sha256': REPAIR, 'records': alternative}]
    result = entrypoint.run(MemoryLines(tasks), MemoryLines(golds), MemoryLines(pred))['outcomes'][0]
    require(result['exact'] and result['gold_records'] == result['matched_records'] == 1, 'Production reader accepts a different lawful10 as one complete record')
    for name, info in prepared['original_public_seven_files'].items():
        require(sha(bundle / name) == info['sha256'], 'Original shared file bytes:' + name)
    for name in ['scorer.py','typed_values.py','source_pins.json','original_scorer.py','review_schema.py']:
        require(sha(bundle / name) == sha(source / 'scoring' / name), 'Source/shared original identity')
    require(sha(bundle / 'one_record_sample_scorer.py') == sha(source / 'scoring/one_record_sample_scorer.py')
            and sha(bundle / 'item_scorer_dispatch.py') == sha(source / 'scoring/item_scorer_dispatch.py'), 'Exact prospective wrapper/dispatch binding')
    execution = load(source / 'native/execution_RAN1.json')
    require(set(declaration['graph_sources']) == {'RAN1','RAN2','RAN3','RAN4','RAN5'} and
            exact(execution['source_before']) == exact(execution['source_after']) == exact(declaration['graph_sources']['RAN1']), 'Five canonical graph sources')
    require(declaration['prospective_scoring']['cohort'] == 'AUTH48' and declaration['prospective_scoring']['id'] == IDENTITY
            and declaration['prospective_scoring']['entrypoint'] == 'score_predictions_joint_sample.py'
            and declaration['prospective_scoring']['historical_scores_changed'] is False, 'Explicit current-only dispatch registration')
    require(all(audit[k] == 0 for k in ['network_calls','SQL_calls','host_private_open_attempts','write_open_attempts','other_subprocess_calls'])
            and audit['expected_source_child_calls'] == 1, 'Immutable offline source-child replay only')
    return {'status':'PASS','candidate_n':1,'local_validated_n':1,'new_public_admissions':0,
        'model_calls':0,'native_calls':0,'portable_controls_replayed':30,
        'items':[{'id':IDENTITY,'repair_sha256':REPAIR,'native_rows':1,'native_full_columns':limited_meta['columns'],
            'native_queries':2,'requested_complete_records':1,'eligible_sample_pool_n':129,
            'required_fields':['specNumber','crCount','sampleCRs'],'collection_kind':definition['collection']['kind'],
            'scoring_entrypoint':'score_predictions_joint_sample.py','independently_sealed_item_replay':replay}],
        'distinct_nonblind_AI_reviews_per_item':2,'human_expert_validation_n':0,'no_host_audit':audit}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.bundle), ensure_ascii=False, sort_keys=True))
