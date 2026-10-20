#!/usr/bin/env python3
"""Replay saved candidate evidence; no model calls or live databases.

The RAN1 eligibility supplement is explicit: saved native selected10 is one
legal answer, whereas the raw-source eligibility11 records all legal ties.
No equality between those two different artifacts is asserted.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
if sys.flags.optimize:
    raise SystemExit('Verification requires enabled checks; -O/-OO refused.')

INVENTORY_SHA256 = '7d96a4528c9ea8fbdbbba0c88a9ded6be0d89ba2e910fcdae058b2be504b7c8c'
def require(ok, message):
    if not ok:
        raise ValueError(message)
def digest(raw):
    return hashlib.sha256(raw).hexdigest()
def exact(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
def safe(p):
    p = Path(os.path.abspath(p))
    for ancestor in (p, *p.parents):
        require(not ancestor.is_symlink(), 'symlink forbidden: ' + str(ancestor))
    return p
def member(bundle, name):
    rel = Path(name)
    require(type(name) is str and name and '\\' not in name and
            not rel.is_absolute() and '..' not in rel.parts, 'unsafe bundle path')
    return safe(bundle / rel)
def load(bundle, name):
    return json.loads(member(bundle, name).read_text())
def lines(bundle, name):
    return [json.loads(s) for s in member(bundle, name).read_text().splitlines() if s.strip()]
def module(bundle, name):
    spec = importlib.util.spec_from_file_location(name, member(bundle, name + '.py'))
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result

def verify(bundle, release_root=None):
    bundle = safe(bundle)
    require(member(bundle, 'verify_additions.py') == safe(__file__), 'execute bundle own verifier')
    inv = member(bundle, 'immutable_inventory.json')
    require(digest(inv.read_bytes()) == INVENTORY_SHA256, 'fixed payload inventory changed')
    files = json.loads(inv.read_text())['files']
    manifest = load(bundle, 'manifest.json')
    require(files == manifest['files'], 'manifest inventory differs')
    actual = set()
    for p in bundle.rglob('*'):
        safe(p)
        require(p.is_file() or p.is_dir(), 'nonregular entry')
        if p.is_file():
            actual.add(p.relative_to(bundle).as_posix())
    require(actual == set(files) | {'manifest.json', 'immutable_inventory.json', 'verify_additions.py'},
            'missing or extra payload file')
    for name, pin in files.items():
        raw = member(bundle, name).read_bytes()
        require(len(raw) == pin['bytes'] and digest(raw) == pin['sha256'], 'payload changed: ' + name)
    require(digest(member(bundle, 'verify_additions.py').read_bytes()) == manifest['verifier_sha256'],
            'verifier differs')
    declarations = load(bundle, 'declarations.json')
    for key, value in declarations.items():
        require(exact(manifest.get(key)) == exact(value), 'scientific declaration differs: ' + key)
    source_replay = None
    if 'RAN1_P2_CQ5-11' in declarations['cohort_ids']:
        dependency = safe(bundle.parent / 'original_core_source_RAN1_common3176')
        dep = declarations['RAN1_raw_source_dependency']
        for name, pin in dep['files'].items():
            raw = member(dependency, name).read_bytes()
            require(len(raw) == pin['bytes'] and digest(raw) == pin['sha256'], 'source dependency changed: ' + name)
        replay = subprocess.run([sys.executable, '-B', '-S',
            str(dependency / 'raw_extraction/verify_source_evidence.py'),
            '--bundle', str(dependency / 'raw_extraction')], capture_output=True, text=True, timeout=120)
        require(replay.returncode == 0, 'included raw-source dependency replay failed: ' + replay.stderr)
        source_replay = json.loads(replay.stdout)
        require(source_replay['status'] == 'PASS' and source_replay['source_own_literal_matches'] == 11 and
                source_replay['required_above_boundary'] == 8 and source_replay['boundary_candidates'] == 3,
                'raw-source eligibility dimensions differ')
    sys.path.insert(0, str(bundle))
    scorer = module(bundle, 'scorer')
    original = module(bundle, 'original_scorer')
    review_schema = module(bundle, 'review_schema')
    contract_checks = module(bundle, 'contract_checks')
    criteria = load(bundle, 'criteria.json')
    require(files['criteria.json']['sha256'] ==
            'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4', 'criteria changed')
    tasks_list = lines(bundle, 'tasks.jsonl')
    gold_list = lines(bundle, 'reference_gold.jsonl')
    ids = declarations['cohort_ids']
    require([t['id'] for t in tasks_list] == [g['id'] for g in gold_list] == ids, 'cohort changed')
    originals = {r['id']: r for r in lines(bundle, 'provenance/original_selected_rows.jsonl')}
    require(set(originals) == set(ids), 'original cohort differs')
    definition_keys = ['id', 'question_en', 'original_query', 'reference_query', 'required_fields',
                       'collection', 'cardinality_policy', 'repair_class', 'original_question_preserved']
    results = []
    total_controls = 0
    for task, gold in zip(tasks_list, gold_list):
        ident = task['id']
        prefix = 'gate_evidence/' + ident + '/'
        definition = load(bundle, 'definitions/' + ident + '.json')
        require(set(definition) == set(definition_keys), 'noncanonical definition keys')
        require(all(exact(task[k]) == exact(definition[k]) for k in definition_keys), 'task differs')
        identity = digest(scorer.get_kernel().json_exact(definition).encode())
        require(identity == task['repair_sha256'] == gold['repair_sha256'], 'repair identity changed')
        require(definition['question_en'] == originals[ident]['question_en'] and
                definition['original_query'] == originals[ident]['cypher'] and
                definition['original_question_preserved'] is True, 'original meaning bytes changed')
        require((definition['original_query'] == definition['reference_query']) ==
                (definition['repair_class'] == 'scorer_only'), 'repair class differs')
        require(task['validation_status'] == 'validated' and task['admitted'] is False and
                task['nonblind_AI'] is True and type(task['expert_validation_n']) is int and
                task['expert_validation_n'] == 0 and task['human_author_review_completed'] is False,
                'AI/local validation versus admission declaration differs')
        reviews = [load(bundle, prefix + side + '.json') for side in ['primary', 'secondary']]
        for review in reviews:
            review_schema.check_pass(review, definition['question_en'], criteria['semantic_units'],
                criteria_sha=files['criteria.json']['sha256'], identity_key='repair_sha256', identity_sha=identity)
        reviewers = [r.get('reviewer_kind') or r.get('reviewer') or r.get('review_role') for r in reviews]
        require(all(type(r) is str and r.strip() for r in reviewers) and reviewers[0] != reviewers[1] and
                exact(reviews[0]) != exact(reviews[1]), 'two judgments cloned')
        src = 'source_evidence/' + ident + '/'
        density = ident == 'RAN3_P3_CQ5-3'
        command = 'verify_source_evidence.py' if density else 'verify_evidence.py'
        replay = subprocess.run([sys.executable, '-B', '-I', str(member(bundle, src + command))],
            cwd=bundle, capture_output=True, text=True, timeout=180,
            env={'PATH':os.environ.get('PATH','/usr/bin:/bin'),'LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'})
        require(replay.returncode == 0, 'item source/native/operand replay failed: '+replay.stderr)
        result = json.loads(replay.stdout)
        require(result['id']==ident and result['repair_sha256']==identity and
                result['API_calls' if density else 'new_API_calls']==0 and
                result['native_rows' if density else 'actual_native_rows']==(23 if density else 8),
                'item source/native replay scope differs')
        native = load(bundle, prefix + 'native_metadata.json')
        inventory = load(bundle, prefix + 'native_execution.json')
        guarded = load(bundle, prefix + 'native_guard.json')
        require(guarded['status'] == 'PASS' and inventory['inventory_unchanged'] is True and
                inventory['source_before'] == inventory['source_after'] == manifest['graph_sources'][ident[:4]],
                'owned native/source gate differs')
        native_input = lines(bundle, prefix + 'native_input.jsonl')
        require(len(native_input) == 1 and native_input[0]['id'] == ident and
                native_input[0]['candidate_query'] == definition['reference_query'] and
                digest(member(bundle, prefix + 'native_input.jsonl').read_bytes()) ==
                inventory['input_sha256'], 'native input binding differs')
        require(native['id'] == ident and native['query'] == definition['reference_query'] and
                native['query_sha256'] == digest(definition['reference_query'].encode()) and
                any(r['id'] == ident and r['status'] == 'OK' and
                    r['query_sha256'] == native['query_sha256'] for r in inventory['items']), 'native query differs')
        require(native['status'] == 'OK' and native['full_rows_available'] is True and
                native['truncated'] is False and native['rollback_completed'] is True and
                native['plan_query_type'] == native['execution_query_type'] == 'r' and
                native['execution_summary_complete'] is True, 'native incomplete/nonreadonly')
        native_raw = member(bundle, prefix + 'native_rows.jsonl').read_bytes()
        require(digest(native_raw) == native['rows_sha256'], 'native row hash differs')
        raw_rows = lines(bundle, prefix + 'native_rows.jsonl')
        require(len(raw_rows) == native['rows_retained'], 'native rows lost')
        require(all(type(row) is list and len(row) == len(native['columns']) for row in raw_rows), 'native shape')
        named = [dict(zip(native['columns'], row)) for row in raw_rows]
        sql = lines(bundle, prefix + 'SQL_full_records.jsonl')
        # json_exact retains every field, type and duplicate of full original execution output.
        require(Counter(exact(r) for r in named) == Counter(exact(r) for r in sql), 'full native/SQL differs')
        projected = [{f['name']: r[f['source_column_or_expression']] for f in definition['required_fields']}
                     for r in named]
        gold_records = gold['records']
        groups = gold.get('order_groups')
        if ident == 'RAN1_P2_CQ5-11':
            witness = load(bundle, prefix + 'source_eligibility_witness.json')
            dependency_prefix = json.loads((dependency / 'source_only_prefix_selection.json').read_text())[ident]
            require(witness == dependency_prefix, 'supplement witness differs from raw-source package')
            eligible = witness['source_only_full_matching_records']
            eligible_records = [{'resolutionId': r['resolutionId']} for r in eligible]
            require(len(raw_rows) == 10 and len(eligible) == 11 and
                    eligible_records == gold_records, 'separate native10/source11 changed')
            require(groups == original.make_order_groups(task, eligible, eligible_records), 'source order witness differs')
            mandatory = [{'resolutionId': r['resolutionId']} for r in witness['mandatory_above_boundary']]
            boundary = [{'resolutionId': r['resolutionId']} for r in witness['boundary_candidates']]
            require(len(mandatory) == 8 and len(boundary) == 3 and witness['choose_at_boundary'] == 2,
                    'source tie dimensions differ')
            require(original.score(task, gold_records, projected, diagnostic=True, order_groups=groups)['exact'],
                    'actual native selected10 is not source-admissible')
            for pair in itertools.combinations(boundary, 2):
                require(original.score(task, gold_records, mandatory + list(pair), diagnostic=True,
                    order_groups=groups)['exact'], 'legal source boundary answer rejected')
            require(task['eligibility_origin'] == 'raw_source_validation_not_native_output' and
                    gold['native_selected_records'] == projected and gold['records_are_full_native_output'] is False,
                    'source eligibility falsely presented as native gold')
        else:
            token = lambda rs: Counter(scorer.record_token(r, definition['required_fields']) for r in rs)
            require(token(projected) == token(gold_records), 'requested native/SQL/gold differs')
            if definition['collection']['kind'] == 'top_k_boundary_ties':
                require(groups == original.make_order_groups(task, named, projected),
                        'complete native ranking evidence differs')
        checks = contract_checks.checks(task, gold_records, order_groups=groups)
        require(all(row['pass'] for row in checks), 'generic typed control failed')
        controls = load(bundle, prefix + 'portable_typed_controls.json')
        require(checks == controls['generic_controls'], 'saved generic controls differ')
        for control in controls['extra_controls']:
            result = original.score(task, gold_records, control['predicted_records'],
                                    diagnostic=True, order_groups=groups)
            require(result == control['actual'] and result['exact'] is control['expected_exact'],
                    'portable typed control failed: ' + control['name'])
        total_controls += len(checks) + len(controls['extra_controls'])
        results.append({'id': ident, 'repair_sha256': identity, 'native_rows': len(raw_rows),
                        'scoring_eligibility_records': len(gold_records),
                        'source_eligibility_is_native_output': ident != 'RAN1_P2_CQ5-11'})
    return {'status': 'PASS', 'candidate_n': len(ids), 'local_validated_n': len(ids),
            'new_public_admissions': 0, 'model_calls': 0, 'native_calls': 0,
            'portable_controls_replayed': total_controls, 'items': results,
            'RAN1_separate_raw_source_replay': source_replay,
            'scope': 'Saved exact-definition/two-AI/native/SQL/typed evidence. Source raw reopens remain separately evidenced; no whole-graph factuality certification.',
            'human_expert_validation_n': 0}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.bundle), ensure_ascii=False, sort_keys=True))
