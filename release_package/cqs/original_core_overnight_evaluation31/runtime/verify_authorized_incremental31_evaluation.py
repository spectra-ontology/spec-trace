"""Offline saved-output replay of every authorized_incremental31 method item."""
import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import importlib.util
import json
import re
from pathlib import Path, PurePosixPath
import sys
sys.dont_write_bytecode = True
if sys.flags.optimize != 0:
    raise RuntimeError('Optimized verifier execution unsupported')
EXPECTED_METADATA_SHA256 = '786a0a3108bdde6a4f96215f6ccfeff0934600c0e6593d5223d67e0b675e51b8'
EXPECTED_PAYLOAD_MAP_SHA256 = '43efbccee3bb801c277ac95061ec695453d10589647a4b9695c1efbc8c309cd3'
EXPECTED_BUNDLE_MANIFEST_SHA256 = '791d6c9c761408c7670d284acfe3b4fc6300b2dff5397befffb45f8620068211'

def _no_link(path):
    import os
    p = Path(os.path.abspath(path))
    for q in [*reversed(p.parents), p]:
        if q.is_symlink():
            raise ValueError('symlink refused before target read: ' + str(q))
    return p

def _canonical_boundary(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def _check_closed_tree(root, names):
    actual = set()
    directories = set()
    allowed_dirs = {x.as_posix() for name in names for x in PurePosixPath(name).parents if x.as_posix() != '.'}
    for p in root.rglob('*'):
        _no_link(p)
        if p.is_file():
            if p != root / 'manifest.json':
                actual.add(p.relative_to(root).as_posix())
        elif p.is_dir():
            directories.add(p.relative_to(root).as_posix())
        else:
            raise ValueError('nonregular entry refused before target read: ' + str(p))
    if not actual == names:
        raise ValueError('closed file inventory changed')
    if not directories == allowed_dirs:
        raise ValueError('closed directory inventory changed')

def _secure_evidence(path):
    root = _no_link(path)
    mp = _no_link(root / 'manifest.json')
    obj = json.loads(mp.read_text())
    if not (type(obj) is dict and type(obj.get('files')) is dict):
        raise ValueError('saved evidence invariant failed')
    meta = {k: v for (k, v) in obj.items() if k != 'files'}
    if not hashlib.sha256(_canonical_boundary(meta).encode()).hexdigest() == EXPECTED_METADATA_SHA256:
        raise ValueError('immutable metadata or JSON scalar type changed')
    pins = obj['files']
    payload = {k: v for (k, v) in pins.items() if k != 'runtime/verify_authorized_incremental31_evaluation.py'}
    if not hashlib.sha256(_canonical_boundary(payload).encode()).hexdigest() == EXPECTED_PAYLOAD_MAP_SHA256:
        raise ValueError('immutable scientific payload map changed')
    if not 'runtime/verify_authorized_incremental31_evaluation.py' in pins:
        raise ValueError('saved evidence invariant failed')
    for (name, pin) in pins.items():
        q = PurePosixPath(name)
        if not (type(name) is str and type(pin) is str and (not q.is_absolute()) and ('..' not in q.parts) and ('\\' not in name)):
            raise ValueError('saved evidence invariant failed')
    _check_closed_tree(root, set(pins))
    for (name, pin) in pins.items():
        if not hashlib.sha256(_no_link(root / name).read_bytes()).hexdigest() == pin:
            raise ValueError(name)
    return root

def _secure_bundle(path):
    root = _no_link(path)
    mp = _no_link(root / 'manifest.json')
    if not hashlib.sha256(mp.read_bytes()).hexdigest() == EXPECTED_BUNDLE_MANIFEST_SHA256:
        raise ValueError('repair bundle manifest changed')
    obj = json.loads(mp.read_text())
    pins = obj['files']
    expected = set(pins) | {'immutable_inventory.json', 'verify_additions.py'}
    _check_closed_tree(root, expected)
    for (name, pin) in pins.items():
        if not (type(pin) is dict and set(pin) == {'sha256', 'bytes'} and (type(pin['bytes']) is int)):
            raise ValueError('saved evidence invariant failed')
        raw = _no_link(root / name).read_bytes()
        if not (len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256']):
            raise ValueError(name)
    if not hashlib.sha256(_no_link(root / 'immutable_inventory.json').read_bytes()).hexdigest() == obj['immutable_inventory_sha256']:
        raise ValueError('saved evidence invariant failed')
    if not hashlib.sha256(_no_link(root / 'verify_additions.py').read_bytes()).hexdigest() == obj['verifier_sha256']:
        raise ValueError('saved evidence invariant failed')
    return root
ENTRY = _no_link(Path(__file__).absolute())

def sha(p):
    return hashlib.sha256(_no_link(p).read_bytes()).hexdigest()

def load(p):
    return json.loads(_no_link(p).read_text())

def rows(p):
    return [json.loads(s) for s in _no_link(p).read_text().splitlines() if s.strip()]

def unique(values):
    result = {r['id']: r for r in values}
    if not len(result) == len(values):
        raise ValueError('saved evidence invariant failed')
    return result

def verify(evidence, bundle):
    evidence = _secure_evidence(evidence)
    bundle = _secure_bundle(bundle)
    manifest = load(evidence / 'manifest.json')
    actual = {p.relative_to(evidence).as_posix(): sha(p) for p in evidence.rglob('*') if p.is_file() and p != evidence / 'manifest.json'}
    if not actual == manifest['files']:
        raise ValueError('saved evidence invariant failed')
    for name in actual:
        path = PurePosixPath(name)
        if not (not path.is_absolute() and '..' not in path.parts and ('\\' not in name)):
            raise ValueError('saved evidence invariant failed')
        if not not (evidence / name).is_symlink():
            raise ValueError('saved evidence invariant failed')
    if not sha(bundle / 'manifest.json') == manifest['bundle_manifest_sha256']:
        raise ValueError('saved evidence invariant failed')
    sys.path.insert(0, str(bundle))
    spec = importlib.util.spec_from_file_location('authorized_incremental31_public_contract_verify', bundle / 'verify_additions.py')
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    proof = validator.verify(bundle)
    if not (proof['status'] == 'PASS' and proof['local_validated_n'] == proof['candidate_n'] == 2 and (proof['new_public_admissions'] == 0)):
        raise ValueError('saved evidence invariant failed')
    tasks = unique(rows(bundle / 'tasks.jsonl'))
    current = evidence / 'current'
    protocol = load(current / 'protocol.json')
    if not sha(current / 'protocol.json') == manifest['protocol_sha256']:
        raise ValueError('saved evidence invariant failed')
    if not protocol['bundle_manifest_sha256'] == sha(bundle / 'manifest.json'):
        raise ValueError('saved evidence invariant failed')
    if not protocol['tasks_sha256'] == sha(bundle / 'tasks.jsonl'):
        raise ValueError('saved evidence invariant failed')
    if not protocol['gold_sha256'] == sha(bundle / 'reference_gold.jsonl'):
        raise ValueError('saved evidence invariant failed')
    if not protocol['public_tasks_sha256'] == sha(current / 'public_tasks.jsonl'):
        raise ValueError('saved evidence invariant failed')
    if not (protocol['admitted_n'] == 2 and set(protocol['cohort_ids']) == set(tasks) == {'RAN1_P2_CQ5-8', 'RAN1_P2_CQ5-2'}):
        raise ValueError('saved evidence invariant failed')
    if not (protocol['model'] == 'anthropic/claude-opus-4.8' and protocol['provider'] == 'Anthropic'):
        raise ValueError('saved evidence invariant failed')
    for (name, expected) in protocol['code_pins'].items():
        if not sha(evidence / 'runtime' / name) == expected:
            raise ValueError(name)
    for (name, expected) in protocol['schema_pins'].items():
        if not sha(current / name) == expected:
            raise ValueError(name)
    for (wg, item) in protocol['sql_manifests'].items():
        if not sha(evidence / 'source_manifests' / (wg + '.manifest.json')) == item['sha256']:
            raise ValueError('saved evidence invariant failed')
    scope = protocol['authorized_incremental31_extension']
    if not sha(evidence / 'authorization/scope.json') == manifest['scope_sha256'] == scope['scope_sha256']:
        raise ValueError('saved evidence invariant failed')
    if not sha(evidence / 'authorization/admission_inputs.json') == scope['admission_inputs_sha256']:
        raise ValueError('saved evidence invariant failed')
    if not sha(evidence / 'runtime/runtime_source_copy_receipt.json') == scope['source_copy_receipt_sha256']:
        raise ValueError('saved evidence invariant failed')
    early_path = evidence / 'runtime/early_execution_reader_copy_receipt.json'
    if early_path.exists():
        early = load(early_path)
        if not sha(evidence / 'runtime/execute_ready.py') == early['copy_sha256'] == early['source_sha256']:
            raise ValueError('saved evidence invariant failed')
        if not (early['generation_and_adapter_code_modified'] is False and early['execution_scheduling_only'] is True):
            raise ValueError('saved evidence invariant failed')
    if not sha(current / 'runtime_freeze_base.json') == scope['raw_runtime_freeze_sha256']:
        raise ValueError('saved evidence invariant failed')
    if not sha(current / 'schema_preflight.json') == protocol['schema_preflight_sha256']:
        raise ValueError('saved evidence invariant failed')
    if not sha(bundle / 'verify_additions.py') == scope['bundle_validator_sha256']:
        raise ValueError('saved evidence invariant failed')
    if not (scope['scope_n'] == 2 and scope['method_items_n'] == 8):
        raise ValueError('saved evidence invariant failed')
    if not (scope['baseline_public_original_n'] == 499 and scope['this_phase_original_union_n'] == 501 and (scope['this_phase_pending_n'] == 59)):
        raise ValueError('saved evidence invariant failed')
    if not scope['planned_calls_without_transport_retry'] == 10:
        raise ValueError('saved evidence invariant failed')
    if not (scope['selection_used_phase_predictions'] is False and scope['live_admission_registry_used'] is False):
        raise ValueError('saved evidence invariant failed')
    if not scope['common_supplemental_source_supplied'] is False:
        raise ValueError('saved evidence invariant failed')
    if not (scope['quality_regeneration_authorized'] is False and scope['human_expert_validation_n'] == 0):
        raise ValueError('saved evidence invariant failed')
    if not (type(protocol['generation_workers']) is int and protocol['generation_workers'] == 1):
        raise ValueError('Serial generation policy differs')
    if not protocol['credit_floor_guard_sha256'] == protocol['code_pins']['credit_floor_guard.py'] == 'c4193f523bec9d6b0282311850957530bd8b7ec237d8446a0e0c94cd18f0451e':
        raise ValueError('Pinned operational credit-floor guard differs')
    if not protocol['account_and_key_credit_floor_usd'] == 5.0:
        raise ValueError('Credit floor policy differs')
    omission=load(evidence / 'authorization/private_credit_floor_log_omission.json')
    if not (omission['private_account_observations_shipped'] is False and omission['scientific_calls_or_responses_omitted'] is False and omission['public_usage_and_raw_attempts_preserved'] is True):
        raise ValueError('Private ledger omission policy differs')
    omitted=omission['omitted_files']
    if not (len(omitted)==1 and omitted[0]['original_relative_path']=='credit_floor_guard.jsonl' and type(omitted[0]['bytes']) is int and omitted[0]['bytes']>0 and re.fullmatch('[0-9a-f]{64}',omitted[0]['sha256'])):
        raise ValueError('Private ledger hash/bytes omission record invalid')
    if (current/'credit_floor_guard.jsonl').exists():
        raise ValueError('Private account/key observations must not be shipped')
    generation = load(current / 'generation_complete.json')
    if not generation['completed_method_items'] == generation['required'] == 8:
        raise ValueError('saved evidence invariant failed')
    requests = sorted((current / 'calls').glob('*.request.json'))
    attempts = sorted((current / 'calls').glob('*.response.json'))
    outcomes = sorted((current / 'calls').glob('*.outcome.json'))
    if not {p.name[:-len('.request.json')] for p in requests} == {p.name[:-len('.outcome.json')] for p in outcomes}:
        raise ValueError('saved evidence invariant failed')
    if not len(requests) == len(outcomes) == 10:
        raise ValueError('saved evidence invariant failed')
    if not {load(p)['request_id'] for p in requests} == {ident + '_' + tag for ident in tasks for tag in ['Text2Cypher', 'Text2SQL', 'C_answer', 'D_followup', 'D_answer']}:
        raise ValueError('saved evidence invariant failed')
    referenced_attempts = []
    (responses, http_counts, known_cost, unknown) = (0, Counter(), Decimal(0), 0)
    raw_known_cost = Decimal(0)
    raw_unknown = 0
    for path in requests:
        request = load(path)
        payload = request['payload']
        if not request['authorization_header_omitted'] is True:
            raise ValueError('saved evidence invariant failed')
        if not request['payload_sha256'] == hashlib.sha256(json.dumps(payload, ensure_ascii=False).encode()).hexdigest():
            raise ValueError('saved evidence invariant failed')
        if not payload['model'] == 'anthropic/claude-opus-4.8':
            raise ValueError('saved evidence invariant failed')
        if not payload['provider'] == {'only': ['Anthropic'], 'allow_fallbacks': False, 'require_parameters': True}:
            raise ValueError('saved evidence invariant failed')
        if not (payload['reasoning'] == {'enabled': False} and payload['response_format'] == {'type': 'json_object'}):
            raise ValueError('saved evidence invariant failed')
        outcome = load(path.with_name(path.name[:-len('.request.json')] + '.outcome.json'))
        if not 1 <= len(outcome['attempts']) <= 2:
            raise ValueError('saved evidence invariant failed')
        if len(outcome['attempts']) == 2:
            if not outcome['attempts'][0]['retryable'] is True:
                raise ValueError('saved evidence invariant failed')
            if not (outcome['attempts'][0]['http_status'] is None or outcome['attempts'][0]['http_status'] == 429 or outcome['attempts'][0]['http_status'] >= 500):
                raise ValueError('saved evidence invariant failed')
        known_cost += Decimal(str(outcome['known_actual_cost_usd']))
        unknown += outcome['unknown_cost_attempts']
        for (index, attempt) in enumerate(outcome['attempts']):
            attempt_path = current / 'calls' / Path(attempt['response_path']).name
            referenced_attempts.append(attempt_path.name)
            raw = load(attempt_path)
            if not (raw['request_id'] == request['request_id'] and raw['attempt'] == index):
                raise ValueError('saved evidence invariant failed')
            http_counts[raw.get('http_status')] += 1
            response = raw.get('response') or {}
            if type(response) is not dict:
                raise ValueError('saved raw provider response shape invalid')
            cost = (response.get('usage') or {}).get('cost')
            if cost is None:
                # Replay the unchanged client: HTTPError status rows do not increment its unknown-cost counter.
                if raw.get('error_type') is not None or raw.get('http_status') == 200:
                    raw_unknown += 1
            else:
                if not (type(cost) in {int, float, str} and type(cost) is not bool):
                    raise ValueError('saved evidence invariant failed')
                actual_cost = Decimal(str(cost))
                if not (actual_cost.is_finite() and actual_cost >= 0):
                    raise ValueError('saved evidence invariant failed')
                raw_known_cost += actual_cost
            if raw.get('http_status') == 200:
                responses += 1
                if response.get('choices'):
                    if not (response.get('model') == 'anthropic/claude-opus-4.8' and response.get('provider') == 'Anthropic'):
                        raise ValueError('saved evidence invariant failed')
    if not len(referenced_attempts) == len(set(referenced_attempts)):
        raise ValueError('saved evidence invariant failed')
    if not set(referenced_attempts) == {p.name for p in attempts}:
        raise ValueError('every saved actual attempt is in the denominator')
    usage = load(current / 'usage.json')
    if not usage['received_response_calls'] == responses:
        raise ValueError('saved evidence invariant failed')
    if not abs(Decimal(str(usage['known_actual_cost_usd'])) - known_cost) < Decimal('0.000000001'):
        raise ValueError('saved evidence invariant failed')
    if not abs(raw_known_cost - known_cost) < Decimal('0.000000001'):
        raise ValueError('saved evidence invariant failed')
    if not raw_unknown == unknown:
        raise ValueError('saved evidence invariant failed')
    if not usage['unknown_cost_attempts'] == unknown:
        raise ValueError('saved evidence invariant failed')
    visible = unique(rows(current / 'public_tasks.jsonl'))
    if not set(visible) == set(tasks):
        raise ValueError('saved evidence invariant failed')
    allowed = {'id', 'wg', 'repair_sha256', 'question_en', 'required_fields', 'collection', 'cardinality_policy', 'identity_format', 'ordering_format'}
    for (ident, task) in tasks.items():
        public = visible[ident]
        if not set(public) <= allowed:
            raise ValueError('saved evidence invariant failed')
        if not (public['question_en'] == task['question_en'] and public['repair_sha256'] == task['repair_sha256']):
            raise ValueError('saved evidence invariant failed')
        # Replay the frozen run_evaluation.public_task field whitelist exactly.
        if not public['required_fields'] == [{k: v for (k, v) in f.items() if k in {'name', 'type', 'nullable', 'json_schema', 'nested_array_semantics'}} for f in task['required_fields']]:
            raise ValueError('saved evidence invariant failed')
    for wg in {i.split('_')[0] for i in tasks}:
        guard = load(current / 'source_guards' / (wg + '.json'))
        sql = load(evidence / 'source_manifests' / (wg + '.manifest.json'))
        expected = sql.get('sqlite_sha256', sql.get('db_sha256', sql.get('output_sha256')))
        if not guard['before'] == guard['after'] == protocol['graph_sources'][wg]:
            raise ValueError('saved evidence invariant failed')
        if not guard['sql_sha256'] == expected:
            raise ValueError('saved evidence invariant failed')
    sys.path.insert(0, str(evidence / 'runtime'))
    import analyze_predictions as analyze
    import score_predictions
    methods = {'A': 'text2cypher', 'B': 'text2sql', 'C': 'single_retrieval', 'D': 'iterative_retrieval'}
    analysis = load(current / 'analysis.json')
    (results, tables) = ({}, {})
    for (arm, method) in methods.items():
        predictions = unique(rows(current / method / 'predictions.jsonl'))
        statuses = unique(rows(current / method / 'statuses.jsonl'))
        if not (set(predictions) == set(statuses) == set(tasks) and len(predictions) == 2):
            raise ValueError('saved evidence invariant failed')
        for (ident, prediction) in predictions.items():
            status = statuses[ident]
            artifact = load(current / status['artifact'])
            if not prediction['repair_sha256'] == status['repair_sha256'] == tasks[ident]['repair_sha256']:
                raise ValueError('saved evidence invariant failed')
            if not (artifact['records'] == prediction['records'] and artifact['status'].upper() == status['status']):
                raise ValueError('saved evidence invariant failed')
            if arm in {'A', 'B'}:
                generated = load(current / 'arm_outputs' / method / (ident + '.json'))
                if not artifact.get('generated_query') == generated.get('generated_query'):
                    raise ValueError('saved evidence invariant failed')
        raw = score_predictions.run(bundle / 'tasks.jsonl', bundle / 'reference_gold.jsonl', current / method / 'predictions.jsonl')
        if not raw == load(current / method / 'raw_scores.json'):
            raise ValueError('saved evidence invariant failed')
        gated = {r['id']: analyze.gated(r, statuses[r['id']]['status']) for r in raw['outcomes']}
        if not list(gated.values()) == load(current / method / 'failure_gated_scores.json'):
            raise ValueError('saved evidence invariant failed')
        tables[method] = analyze.summary(list(gated.values()))
        if not tables[method] == analysis['tables'][method]['overall']:
            raise ValueError('saved evidence invariant failed')
        if not sha(current / method / 'predictions.jsonl') == analysis['tables'][method]['prediction_sha256']:
            raise ValueError('saved evidence invariant failed')
        if not sha(current / method / 'statuses.jsonl') == analysis['tables'][method]['statuses_sha256']:
            raise ValueError('saved evidence invariant failed')
        results[method] = gated
    pairs = []
    for (index, a) in enumerate(methods.values()):
        for b in list(methods.values())[index + 1:]:
            for metric in ('f1', 'exact'):
                pairs.append(dict(a=a, b=b, **analyze.paired(results[a], results[b], metric)))
    if not (pairs == analysis['paired'] and analysis['admitted_n'] == 2):
        raise ValueError('saved evidence invariant failed')
    if not (manifest['additional_n'] == 2 and manifest['method_items'] == 8):
        raise ValueError('saved evidence invariant failed')
    if not (manifest['new_unique_core_ids'] == 2 and set(manifest['cohort_ids']) == set(tasks)):
        raise ValueError('saved evidence invariant failed')
    if not manifest['planned_first_calls_without_transport_retry'] == 10:
        raise ValueError('saved evidence invariant failed')
    if not (manifest['baseline_public_original_n'], manifest['registered_union_n'], manifest['registered_pending_n']) == (499, 501, 59):
        raise ValueError('saved evidence invariant failed')
    guard_provenance = load(evidence / 'runtime/AUTH31_root_guarded_native_execution_v1.adaptation.json')
    old_guard = evidence / 'runtime/original_guard_scheduler.py'
    new_guard = evidence / 'runtime/AUTH31_root_guarded_native_execution_v1.py'
    if not sha(old_guard) == guard_provenance['source_sha256']:
        raise ValueError('saved evidence invariant failed')
    if not sha(new_guard) == guard_provenance['destination_sha256']:
        raise ValueError('saved evidence invariant failed')
    if not guard_provenance['native_lock_memory_cpu_readonly_protocol_unchanged'] is True:
        raise ValueError('saved evidence invariant failed')
    if not guard_provenance['API_calls'] == 0:
        raise ValueError('saved evidence invariant failed')
    if not manifest['guard_scheduler_source_sha256'] == sha(old_guard):
        raise ValueError('saved evidence invariant failed')
    if not manifest['guard_scheduler_destination_sha256'] == sha(new_guard):
        raise ValueError('saved evidence invariant failed')
    if not manifest['guard_scheduler_adaptation_sha256'] == sha(evidence / 'runtime/AUTH31_root_guarded_native_execution_v1.adaptation.json'):
        raise ValueError('saved evidence invariant failed')
    parser_path = evidence / 'runtime/verify_incremental31_exact_prompts_and_parsers.py'
    parser_spec = importlib.util.spec_from_file_location('auth31_exact_parser_replay', parser_path)
    parser_module = importlib.util.module_from_spec(parser_spec)
    parser_spec.loader.exec_module(parser_module)
    parser_proof = parser_module.verify(evidence)
    if not parser_proof['status'] == 'PASS':
        raise ValueError('saved evidence invariant failed')
    privacy = load(evidence / 'privacy_check.json')
    if not (privacy['exact_configured_credential_bytes_scanned'] is True and privacy['matches'] == 0):
        raise ValueError('saved evidence invariant failed')
    if not privacy['personal_credit_balance_files_included'] is False:
        raise ValueError('Private account observations included')
    if not privacy['private_credit_floor_log_omission_sha256'] == sha(evidence/'authorization/private_credit_floor_log_omission.json'):
        raise ValueError('Private ledger omission commitment differs')
    if not privacy['credential_bytes_exposed'] is False:
        raise ValueError('saved evidence invariant failed')
    if not manifest['all_actual_response_attempts_and_failures_preserved'] is True:
        raise ValueError('saved evidence invariant failed')
    return {'status': 'PASS', 'additional_n': 2, 'method_items': 8, 'model_request_n': len(requests), 'model_response_attempt_n': len(attempts), 'received_http200_response_n': responses, 'http_status_counts': {str(k): v for (k, v) in http_counts.items()}, 'known_actual_cost_usd': str(known_cost), 'raw_usage_decimal_cost_usd': str(raw_known_cost), 'unknown_cost_attempts': unknown, 'tables': tables, 'strict_scoring_and_failure_gates_replayed': True, 'evidence_manifest_sha256': sha(evidence / 'manifest.json'), 'human_expert_validation_n': 0, 'new_API_calls': 0, 'new_database_executions': 0, 'contract_verification': proof, 'exact_prompt_and_parser_replay': parser_proof}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = verify(args.evidence, args.bundle)
    if args.out:
        args.out = _no_link(args.out)
        if not not args.out.is_relative_to(_no_link(args.bundle)):
            raise ValueError('output may not write into repair bundle')
        if not not args.out.exists():
            raise ValueError('Preserve earlier replay receipts')
        if not not args.out.resolve().is_relative_to(args.evidence.resolve()):
            raise ValueError('saved evidence invariant failed')
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
