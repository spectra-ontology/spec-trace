#!/usr/bin/env python3
"""Replay three named-lookup local gates without a database, model, or host fallback."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
if sys.flags.optimize != 0:
    raise RuntimeError('Optimized execution is unsupported: use python3 -B -I or -B -S')
INVENTORY_SHA256 = 'fadf0f280fd20f97a814a1db08d601ea57e0f261f2ea913585965398ae2c2cb0'
DECLARATIONS = {'kind': 'Three unchanged original named-lookup local publication candidates', 'state': 'LOCAL_PUBLICATION_PROPOSAL_NOT_ADMITTED', 'cohort_ids': ['RAN5_P1_CQ1-2', 'RAN4_P1_CQ1-2', 'RAN4_P1_CQ1-3'], 'candidate_n': 3, 'new_public_admissions': 0, 'model_predictions_n': 0, 'new_model_calls': 0, 'human_expert_n': 0, 'nonblind_AI': True, 'original560_pass_increment': 0, 'semantic_criteria_sha256': 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4', 'local_generic_controls': 45, 'local_extra_typed_controls': 156, 'stored_native_captures': {'new': 2, 'archived_reused': 1}, 'baseline_public_commit': '9c70ca34ed7e6e6359b7b71aad4f2481c0de578c', 'baseline_public_pass_n': 484, 'graph_sources': {'RAN1': {'wg': 'RAN1', 'import_manifest_sha256': 'c1fa8ecaf6cd21131f809a80c16f36c0a4ff32b385045c6465aa1358df6a2cf0', 'source': {'sha256': '9540683df5407bb3f8978ad4d05ddc7f7880f10c94f21273f588d737f145e231', 'md5': 'd0cd98857f936c6fbccaa190e1fc365c', 'bytes': 163305588, 'published_md5_verified': True}, 'nodes': 165418, 'relationships': 848228, 'shipped_loader_sha256': '9499ac120ea4fcf1c2707f6e3151e399530d9b4f43f5aec9d2d93040792d6e25', 'restoration_wrapper_sha256': '94ec3c9274ba2c62cd3bafc17e98225d174b9e7fef3f1a4a0bc9270101eae973'}, 'RAN2': {'wg': 'RAN2', 'import_manifest_sha256': '88e5529dafa528036cb37fd94dabd5e5f581d10eac7a1d454c851365f36c90d1', 'source': {'sha256': 'f0997bbfb5fd5844837514cd29cfe943b8cb2d0240f0ea5579c5e69b4e547d6c', 'md5': 'ec7dfb70a0822e47e78765172117d87f', 'bytes': 166688978, 'published_md5_verified': True}, 'nodes': 156288, 'relationships': 939037, 'shipped_loader_sha256': '9499ac120ea4fcf1c2707f6e3151e399530d9b4f43f5aec9d2d93040792d6e25', 'restoration_wrapper_sha256': '94ec3c9274ba2c62cd3bafc17e98225d174b9e7fef3f1a4a0bc9270101eae973'}, 'RAN3': {'wg': 'RAN3', 'import_manifest_sha256': '6a325f06f5c5fe903d6b382635e7096a107c4b620e3a9288cf5a18852e30c0a5', 'source': {'sha256': 'd9791c08773a0e38b89869b3882d3098d879a37ddd7109630c346200d6776e95', 'md5': 'ad73158bf9d80b1e3b875edaa9ea7ded', 'bytes': 81735967, 'published_md5_verified': True}, 'nodes': 87980, 'relationships': 481498, 'shipped_loader_sha256': '9499ac120ea4fcf1c2707f6e3151e399530d9b4f43f5aec9d2d93040792d6e25', 'restoration_wrapper_sha256': '94ec3c9274ba2c62cd3bafc17e98225d174b9e7fef3f1a4a0bc9270101eae973'}, 'RAN4': {'wg': 'RAN4', 'import_manifest_sha256': '79fdfaf2b47c96f5bd39ede7acb577f0da0e4d306463512cb0892cdb61d6386c', 'source': {'sha256': '90c6bf7d4420949b7395e8a0b5700a07f8866ddd461699d4516fe4e4f5deec5d', 'md5': '8c1b8f4b3d6b6368a491ba9dbc7a4399', 'bytes': 295732831, 'published_md5_verified': True}, 'nodes': 342161, 'relationships': 1592845, 'shipped_loader_sha256': '9499ac120ea4fcf1c2707f6e3151e399530d9b4f43f5aec9d2d93040792d6e25', 'restoration_wrapper_sha256': '94ec3c9274ba2c62cd3bafc17e98225d174b9e7fef3f1a4a0bc9270101eae973'}, 'RAN5': {'wg': 'RAN5', 'import_manifest_sha256': '10817e42ef9ea5fe4b6409ecc6f61cf1f8e09456c32a4e60db8d8918e6c8895d', 'source': {'sha256': '1ab414b785a155b58218a209be71ed9d1dacc1ea86ae13abbacfbaea27808f5e', 'md5': 'e60edcc16b3e96bbe0d70f54fb0adbc3', 'bytes': 195847852, 'published_md5_verified': True}, 'nodes': 215012, 'relationships': 1047242, 'shipped_loader_sha256': '9499ac120ea4fcf1c2707f6e3151e399530d9b4f43f5aec9d2d93040792d6e25', 'restoration_wrapper_sha256': '94ec3c9274ba2c62cd3bafc17e98225d174b9e7fef3f1a4a0bc9270101eae973'}}}
IDS = ['RAN5_P1_CQ1-2', 'RAN4_P1_CQ1-2', 'RAN4_P1_CQ1-3']
DEFINITION_KEYS = ['id','question_en','original_query','reference_query','required_fields',
                   'collection','cardinality_policy','repair_class','original_question_preserved']


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def no_symlink(path):
    p = Path(os.path.abspath(os.fspath(path)))
    for component in [p, *p.parents]:
        if component.is_symlink():
            raise ValueError('symlink path is unsupported: ' + str(component))
    return p


def digest(data):
    return hashlib.sha256(data).hexdigest()


def strict_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def child(bundle, relative):
    require(type(relative) is str and relative and '\\' not in relative, 'invalid relative path')
    rel = Path(relative)
    require(not rel.is_absolute() and '..' not in rel.parts and '.' not in rel.parts, 'unsafe relative path')
    target = no_symlink(bundle / rel)
    require(target.is_relative_to(bundle), 'path escaped bundle')
    return target


def load(bundle, relative):
    return json.loads(child(bundle, relative).read_text())


def rows(bundle, relative):
    return [json.loads(line) for line in child(bundle, relative).read_text().splitlines() if line.strip()]


def module(bundle, name):
    p = child(bundle, name + '.py')
    spec = importlib.util.spec_from_file_location(name, p)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def verify(bundle, release_root=None):
    # release_root is accepted for API compatibility only. Every replay input is included.
    # Do not resolve() before inspecting every ancestor of the original path.
    no_symlink(__file__)
    bundle = no_symlink(bundle)
    own = child(bundle, 'verify_additions.py')
    require(own.absolute() == Path(os.path.abspath(__file__)), 'execute the bundle own verifier')
    manifest = load(bundle, 'manifest.json')
    require(set(manifest) == set(DECLARATIONS) | {'verifier_sha256','immutable_inventory_sha256','files'},
            'manifest exact top-level field set changed')
    for key, expected in DECLARATIONS.items():
        require(strict_json(manifest[key]) == strict_json(expected), 'manifest scientific declaration changed: ' + key)
    require(manifest['immutable_inventory_sha256'] == INVENTORY_SHA256, 'inventory commitment changed')
    require(type(manifest['verifier_sha256']) is str and digest(own.read_bytes()) == manifest['verifier_sha256'],
            'executing verifier hash changed')
    invpath = child(bundle, 'immutable_inventory.json')
    require(digest(invpath.read_bytes()) == INVENTORY_SHA256, 'immutable inventory changed')
    inventory = json.loads(invpath.read_text())
    require(type(inventory) is dict and set(inventory) == {'kind','files'}, 'inventory schema changed')
    require(inventory['kind'] == 'Closed immutable named-lookup candidate payload inventory', 'inventory kind changed')
    files = inventory['files']
    require(type(files) is dict and strict_json(files) == strict_json(manifest['files']), 'manifest file inventory differs')
    actual_files = set()
    for p in bundle.rglob('*'):
        no_symlink(p)
        if p.is_file():
            actual_files.add(p.relative_to(bundle).as_posix())
        elif not p.is_dir():
            raise ValueError('nonregular package entry: ' + str(p))
    require(actual_files == set(files) | {'manifest.json','immutable_inventory.json','verify_additions.py'},
            'missing or extra package file')
    for relative, pin in files.items():
        require(type(pin) is dict and set(pin) == {'sha256','bytes'} and type(pin['bytes']) is int
                and type(pin['sha256']) is str, 'invalid inventory pin')
        raw = child(bundle, relative).read_bytes()
        require(len(raw) == pin['bytes'] and digest(raw) == pin['sha256'], 'payload changed: ' + relative)
    # Imports happen only after the complete closed payload tree has been checked.
    sys.path.insert(0, str(bundle))
    scorer = module(bundle, 'scorer')
    original_scorer = module(bundle, 'original_scorer')
    review_schema = module(bundle, 'review_schema')
    contract_checks = module(bundle, 'contract_checks')
    kernel = scorer.get_kernel()
    criteria = load(bundle, 'criteria.json')
    criteria_sha = files['criteria.json']['sha256']
    original_rows = {r['id']: r for r in rows(bundle, 'provenance/original_named_rows.jsonl')}
    tasks_list = rows(bundle, 'tasks.jsonl')
    gold_list = rows(bundle, 'reference_gold.jsonl')
    require(len(tasks_list) == len(gold_list) == len(IDS), 'cohort size changed')
    tasks = {r['id']:r for r in tasks_list}
    gold = {r['id']:r for r in gold_list}
    require(list(tasks) == list(gold) == IDS and set(original_rows) == set(IDS), 'cohort identity changed')
    validation = load(bundle, 'root_evidence/named_reference_validation.json')
    native_map = {r['id']:r for r in validation['items']}
    require(set(native_map) == set(IDS) and validation['new_native_queries'] == 2
            and validation['reused_exact_native_captures'] == 1
            and validation['new_API_calls'] == validation['new_admissions'] == validation['public_mutations'] == 0,
            'native evidence cohort declarations changed')
    generic_total = extra_total = 0
    results = []
    saved_generic = {r['id']:r for r in rows(bundle, 'scorer_checks.jsonl')}
    for id in IDS:
        task = tasks[id]
        definition = load(bundle, 'definitions/' + id + '.json')
        require(set(definition) == set(DEFINITION_KEYS), 'canonical definition keys differ: ' + id)
        require(all(strict_json(task[k]) == strict_json(definition[k]) for k in DEFINITION_KEYS), 'task definition differs')
        repair = digest(kernel.json_exact(definition).encode())
        require(repair == task['repair_sha256'] == gold[id]['repair_sha256'], 'exact repair identity differs')
        original = original_rows[id]
        require(definition['question_en'] == original['question_en'] and definition['original_query'] == original['cypher'],
                'original English or authored query changed')
        require(definition['reference_query'] == definition['original_query'] and definition['repair_class'] == 'scorer_only',
                'named lookup query changed')
        require(definition['collection'] == {'kind':'multiset'} and definition['cardinality_policy'] == {'mode':'all'},
                'collection completeness changed')
        require(task['validation_status'] == 'validated' and task['admitted'] is False
                and task['expert_validation_n'] == 0 and type(task['expert_validation_n']) is int
                and task['human_author_review_completed'] is False and task['nonblind_AI'] is True,
                'local validation versus public admission declarations differ')
        require(digest(definition['question_en'].encode()) == task['original_question_sha256']
                and digest(definition['original_query'].encode()) == task['original_query_sha256']
                and task['criteria_sha256'] == criteria_sha, 'question/query/criteria pins differ')
        reviews = []
        for name in ['primary','secondary']:
            review = load(bundle, 'reviews/' + id + '/' + name + '.json')
            review_schema.check_pass(review, definition['question_en'], criteria['semantic_units'], criteria_sha=criteria_sha,
                                     identity_key='repair_sha256', identity_sha=repair)
            reviews.append(review)
        require(reviews[0]['reviewer_kind'] != reviews[1]['reviewer_kind'] and
                strict_json(reviews[0]) != strict_json(reviews[1]), 'independent reviews cloned')
        capture = load(bundle, 'reference_outputs/' + id + '/receipt.json')
        native = native_map[id]
        require(strict_json(native['frozen_source_inventory']) == strict_json(manifest['graph_sources'][id[:4]]),
                'native source inventory differs from common frozen graph pin')
        require(capture['id'] == id and capture['query'] == definition['reference_query']
                and capture['query_sha256'] == task['original_query_sha256'], 'native query identity differs')
        require(capture['status'] == 'OK' and capture['full_rows_available'] is True
                and capture['truncated'] is False and capture['rollback_completed'] is True
                and capture['plan_query_type'] == capture['execution_query_type'] == 'r'
                and capture['execution_summary_complete'] is True, 'native read-only/full-output gate differs')
        source_rows_path = child(bundle, 'reference_outputs/' + id + '/rows.jsonl')
        require(digest(source_rows_path.read_bytes()) == capture['rows_sha256'] == native['native_rows_file']['sha256'],
                'native row bytes changed')
        source_rows = rows(bundle, 'reference_outputs/' + id + '/rows.jsonl')
        require(len(source_rows) == capture['rows_retained'] and capture['columns'] == native['exact_native_columns'],
                'native full field/row shape differs')
        projected = []
        for row in source_rows:
            require(type(row) is list and len(row) == len(capture['columns']), 'native positional shape differs')
            bound = dict(zip(capture['columns'], row))
            projected.append({f['name']:bound[f['source_column_or_expression']] for f in definition['required_fields']})
        sql = load(bundle, 'gate_evidence/' + id + '/immutable_SQL.json')
        require(all(sql[x] is True for x in ['query_only','mode_ro','immutable','database_stat_unchanged',
                                           'complete_native_equivalent_projection_not_native_execution']), 'saved immutable SQL flags differ')
        def counter(records):
            return Counter(scorer.record_token(r, definition['required_fields']) for r in records)
        require(counter(projected) == counter(sql['required_projected_records']) == counter(native['native_rows'])
                == counter(gold[id]['records']) == counter(rows(bundle, 'gate_evidence/' + id + '/SQL_records.jsonl')),
                'full requested native/SQL/gold typed multiset differs')
        require(gold[id]['order_groups'] is None, 'unordered named multiset has rank data')
        run = load(bundle, 'root_evidence/execution_' + id[:4] + '.json')
        require(run['inventory_unchanged'] is True and run['source_before'] == run['source_after'], 'native source inventory changed')
        require(any(r['id'] == id and r['status'] == 'OK' and r['query_sha256'] == capture['query_sha256'] for r in run['items']),
                'native execution inventory missing this query')
        controls = load(bundle, 'gate_evidence/' + id + '/typed_controls.json')
        generic = contract_checks.checks(task, projected)
        require(generic == controls['generic_production_checks'] == saved_generic[id]['checks']
                and all(r['pass'] is True for r in generic), 'production generic controls changed')
        generic_total += len(generic)
        for control in controls['extra_full_outcome_checks']:
            reference = control.get('synthetic_reference_records', projected)
            outcome = original_scorer.score(task, reference, control['predicted_records'], diagnostic=True, order_groups=None)
            require(outcome == control['actual'] and outcome['exact'] is control['expected_exact']
                    and control['pass'] is True, 'typed extra control replay failed: ' + control['name'])
            extra_total += 1
        results.append({'id':id,'repair_sha256':repair,'native_rows':len(projected),
                        'native_capture_reused':native['capture_reused'],
                        'full_requested_fields_native_SQL_equal':True})
    require(generic_total == 45 and extra_total == 156, 'actual scorer control count differs')
    return {'status':'PASS','candidate_n':3,'local_validated_n':3,'publication_state':'NOT_ADMITTED',
            'new_public_admissions':0,'new_model_calls':0,'new_native_executions':0,
            'human_expert_n':0,'nonblind_AI':True,'generic_controls':generic_total,
            'extra_typed_controls':extra_total,'items':results,
            'limitations':['Stored native and immutable SQL captures are replayed; databases and raw workbooks are not reexecuted.',
                           'Original frozen TTL/count guards do not certify arbitrary same-count external property mutations.',
                           'Contract validation and proposal packaging do not constitute publication or a model evaluation.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, default=Path(os.path.abspath(__file__)).parent)
    parser.add_argument('--release-root', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.bundle, args.release_root), ensure_ascii=False, sort_keys=True))
