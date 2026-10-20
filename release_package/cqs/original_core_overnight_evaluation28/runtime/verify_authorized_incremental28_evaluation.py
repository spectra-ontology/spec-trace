"""Offline saved-output replay of every authorized_incremental28 method item."""
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
EXPECTED_METADATA_SHA256 = 'f806d9cb8b6b87ec056baa012d0a21c83cd29b1339594ca154cefe5bf711bdd9'
EXPECTED_PAYLOAD_MAP_SHA256 = '7151f3ebe82661c6a558b3052d1575430f7f71d8e284b926ee2171c642019259'
EXPECTED_BUNDLE_MANIFEST_SHA256 = 'c6fde49d7d02d2d060abdbb4420e430674e9bcca40f2f6cc6dda79d66a815e56'

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
    payload = {k: v for (k, v) in pins.items() if k != 'runtime/verify_authorized_incremental28_evaluation.py'}
    if not hashlib.sha256(_canonical_boundary(payload).encode()).hexdigest() == EXPECTED_PAYLOAD_MAP_SHA256:
        raise ValueError('immutable scientific payload map changed')
    if not 'runtime/verify_authorized_incremental28_evaluation.py' in pins:
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


def _verify_compatibility_recovery(evidence,protocol):
    r=evidence/'compatibility_recovery'
    registration=load(r/'registration.json')
    check=protocol['authorized_incremental28_compatibility_recovery']
    if sha(r/'registration.json') != check['registration_sha256']:
        raise ValueError('Recovery registration changed')
    if check['quality_rerolls'] != 0 or check['first_two_structured_responses_reused'] != 2 or check['additional_first_retrieval_calls_planned'] != 3:
        raise ValueError('Recovery scope changed')
    old=r/'original_retrieval_adapter.py'
    new=evidence/'runtime/retrieval_adapter.py'
    before=registration['exact_patch']['before'];after=registration['exact_patch']['after']
    if old.read_text().count(before)!=1 or old.read_text().replace(before,after)!=new.read_text():
        raise ValueError('Adapter changed beyond single allowed nested mode')
    if sha(old)!=registration['original_retrieval_adapter']['sha256'] or sha(new)!=registration['compatible_retrieval_adapter']['sha256']:
        raise ValueError('Adapter lineage changed')
    oldp=load(r/'original_protocol.json')
    if sha(r/'original_protocol.json')!=registration['original_protocol']['sha256'] or sha(r/'original_analysis.json')!=registration['original_analysis']['sha256']:
        raise ValueError('Original failed evaluation omitted or modified')
    for k in ['bundle_manifest_sha256','tasks_sha256','gold_sha256','public_tasks_sha256','model','provider','cohort_ids','schema_pins','sql_manifests','graph_sources']:
        if oldp[k]!=protocol[k]:raise ValueError('Scientific scope changed during compatibility recovery: '+k)
    for k,pin in oldp['code_pins'].items():
        if k!='retrieval_adapter.py' and protocol['code_pins'][k]!=pin:raise ValueError('Unrelated method changed')
    original_calls=load(r/'original_call_inventory.json')
    if len(original_calls)!=6 or any('_C_' in f or '_D_' in f for f in original_calls):
        raise ValueError('Retrieval call existed before recovery or original two omitted')
    for name,pin in original_calls.items():
        if sha(evidence/'current/calls'/name)!=pin:raise ValueError('Original structured response/request/outcome changed')
    for m in ['single_retrieval','iterative_retrieval']:
        fail=load(r/(m+'_precall_failure.json'))
        if fail['status']!='ADAPTER_EXCEPTION' or fail['error']!='Invalid structural nested-array semantics':
            raise ValueError('Original adapter failure not preserved')
    copied=load(r/'late_original_prediction_copy.json')
    for item in copied['files']:
        if sha(evidence/'current'/item['file'])!=item['sha256']:raise ValueError('Original structured prediction changed')
    if copied['new_model_calls']!=0:raise ValueError('Unregistered late model call')
    usage=load(evidence/'current/usage_aggregation_receipt.json')
    if usage['original_calls']!=2 or usage['new_first_retrieval_calls']!=3 or usage['quality_rerolls']!=0 or usage['all_original_request_response_bytes_unchanged'] is not True:
        raise ValueError('Response reuse or cost aggregation changed')
    oa=load(r/'original_analysis.json')
    if any(oa['tables'][m]['overall']['execution_status_counts']!={'ADAPTER_EXCEPTION':1} for m in ['single_retrieval','iterative_retrieval']):
        raise ValueError('Original failed metrics omitted')

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
    spec = importlib.util.spec_from_file_location('authorized_incremental28_public_contract_verify', bundle / 'verify_additions.py')
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    proof = validator.verify(bundle)
    if not (proof['status'] == 'PASS' and proof['local_validated_n'] == proof['candidate_n'] == 1 and (proof['new_public_admissions'] == 0)):
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
    if not (protocol['admitted_n'] == 1 and set(protocol['cohort_ids']) == set(tasks) == {'RAN5_P2_CQ3-3'}):
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
    _verify_compatibility_recovery(evidence, protocol)
    scope = protocol['authorized_incremental28_extension']
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
    if not (scope['scope_n'] == 1 and scope['method_items_n'] == 4):
        raise ValueError('saved evidence invariant failed')
    if not (scope['baseline_public_original_n'] == 494 and scope['this_phase_original_union_n'] == 495 and (scope['this_phase_pending_n'] == 65)):
        raise ValueError('saved evidence invariant failed')
    if not scope['planned_calls_without_transport_retry'] == 5:
        raise ValueError('saved evidence invariant failed')
    if not (scope['selection_used_phase_predictions'] is False and scope['live_admission_registry_used'] is False):
        raise ValueError('saved evidence invariant failed')
    if not scope['common_supplemental_source_supplied'] is False:
        raise ValueError('saved evidence invariant failed')
    if not (scope['quality_regeneration_authorized'] is False and scope['human_expert_validation_n'] == 0):
        raise ValueError('saved evidence invariant failed')
    generation = load(current / 'generation_complete.json')
    if not generation['completed_method_items'] == generation['required'] == 4:
        raise ValueError('saved evidence invariant failed')
    requests = sorted((current / 'calls').glob('*.request.json'))
    attempts = sorted((current / 'calls').glob('*.response.json'))
    outcomes = sorted((current / 'calls').glob('*.outcome.json'))
    if not {p.name[:-len('.request.json')] for p in requests} == {p.name[:-len('.outcome.json')] for p in outcomes}:
        raise ValueError('saved evidence invariant failed')
    if not len(requests) == len(outcomes) == 5:
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
        if not (set(predictions) == set(statuses) == set(tasks) and len(predictions) == 1):
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
    if not (pairs == analysis['paired'] and analysis['admitted_n'] == 1):
        raise ValueError('saved evidence invariant failed')
    if not (manifest['additional_n'] == 1 and manifest['method_items'] == 4):
        raise ValueError('saved evidence invariant failed')
    if not (manifest['new_unique_core_ids'] == 1 and set(manifest['cohort_ids']) == set(tasks)):
        raise ValueError('saved evidence invariant failed')
    if not manifest['planned_first_calls_without_transport_retry'] == 5:
        raise ValueError('saved evidence invariant failed')
    if not (manifest['baseline_public_original_n'], manifest['registered_union_n'], manifest['registered_pending_n']) == (494, 495, 65):
        raise ValueError('saved evidence invariant failed')
    guard_provenance = load(evidence / 'runtime/AUTH28_root_guarded_native_execution_v1.adaptation.json')
    old_guard = evidence / 'runtime/original_guard_scheduler.py'
    new_guard = evidence / 'runtime/AUTH28_root_guarded_native_execution_v1.py'
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
    if not manifest['guard_scheduler_adaptation_sha256'] == sha(evidence / 'runtime/AUTH28_root_guarded_native_execution_v1.adaptation.json'):
        raise ValueError('saved evidence invariant failed')
    parser_path = evidence / 'runtime/verify_incremental28_exact_prompts_and_parsers.py'
    parser_spec = importlib.util.spec_from_file_location('auth28_exact_parser_replay', parser_path)
    parser_module = importlib.util.module_from_spec(parser_spec)
    parser_spec.loader.exec_module(parser_module)
    parser_proof = parser_module.verify(evidence)
    if not parser_proof['status'] == 'PASS':
        raise ValueError('saved evidence invariant failed')
    privacy = load(evidence / 'privacy_check.json')
    if not (privacy['exact_configured_credential_bytes_scanned'] is True and privacy['matches'] == 0):
        raise ValueError('saved evidence invariant failed')
    if not privacy['credential_bytes_exposed'] is False:
        raise ValueError('saved evidence invariant failed')
    if not manifest['all_actual_response_attempts_and_failures_preserved'] is True:
        raise ValueError('saved evidence invariant failed')
    return {'status': 'PASS', 'additional_n': 1, 'method_items': 4, 'model_request_n': len(requests), 'model_response_attempt_n': len(attempts), 'received_http200_response_n': responses, 'http_status_counts': {str(k): v for (k, v) in http_counts.items()}, 'known_actual_cost_usd': str(known_cost), 'raw_usage_decimal_cost_usd': str(raw_known_cost), 'unknown_cost_attempts': unknown, 'tables': tables, 'strict_scoring_and_failure_gates_replayed': True, 'evidence_manifest_sha256': sha(evidence / 'manifest.json'), 'human_expert_validation_n': 0, 'new_API_calls': 0, 'new_database_executions': 0, 'contract_verification': proof, 'exact_prompt_and_parser_replay': parser_proof}
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
