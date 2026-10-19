#!/usr/bin/env python3
"""Offline saved-output replay of every authorized_incremental21 method item."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import re
from pathlib import Path, PurePosixPath
import sys

sys.dont_write_bytecode = True


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(p):
    return json.loads(p.read_text())


def rows(p):
    return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]


def unique(values):
    result = {r['id']: r for r in values}
    assert len(result) == len(values)
    return result


def verify(evidence, bundle):
    manifest = load(evidence / 'manifest.json')
    actual = {p.relative_to(evidence).as_posix(): sha(p) for p in evidence.rglob('*')
              if p.is_file() and p != evidence / 'manifest.json'}
    assert actual == manifest['files']
    for name in actual:
        path = PurePosixPath(name)
        assert not path.is_absolute() and '..' not in path.parts and '\\' not in name
        assert not (evidence / name).is_symlink()
    assert sha(bundle / 'manifest.json') == manifest['bundle_manifest_sha256']
    sys.path.insert(0, str(bundle))
    spec = importlib.util.spec_from_file_location('authorized_incremental21_public_contract_verify', bundle / 'verify_additions.py')
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    proof = validator.verify(bundle)
    assert proof['status'] == 'PASS' and proof['additional_admitted_n'] == 1
    tasks = unique(rows(bundle / 'tasks.jsonl'))
    current = evidence / 'current'
    protocol = load(current / 'protocol.json')
    assert sha(current / 'protocol.json') == manifest['protocol_sha256']
    assert protocol['bundle_manifest_sha256'] == sha(bundle / 'manifest.json')
    assert protocol['tasks_sha256'] == sha(bundle / 'tasks.jsonl')
    assert protocol['gold_sha256'] == sha(bundle / 'reference_gold.jsonl')
    assert protocol['public_tasks_sha256'] == sha(current / 'public_tasks.jsonl')
    assert protocol['admitted_n'] == 1 and set(protocol['cohort_ids']) == set(tasks) == {'RAN1_P2_CQ1-5'}
    assert protocol['model'] == 'anthropic/claude-opus-4.8' and protocol['provider'] == 'Anthropic'
    for name, expected in protocol['code_pins'].items():
        assert sha(evidence / 'runtime' / name) == expected, name
    for name, expected in protocol['schema_pins'].items():
        assert sha(current / name) == expected, name
    for wg, item in protocol['sql_manifests'].items():
        assert sha(evidence / 'source_manifests' / (wg + '.manifest.json')) == item['sha256']
    scope = protocol['authorized_incremental21_extension']
    assert sha(evidence / 'authorization/scope.json') == manifest['scope_sha256'] == scope['scope_sha256']
    assert sha(evidence / 'authorization/admission_inputs.json') == scope['admission_inputs_sha256']
    assert sha(evidence / 'runtime/runtime_source_copy_receipt.json') == scope['source_copy_receipt_sha256']
    early_path = evidence / 'runtime/early_execution_reader_copy_receipt.json'
    if early_path.exists():
        early = load(early_path)
        assert sha(evidence / 'runtime/execute_ready.py') == early['copy_sha256'] == early['source_sha256']
        assert early['generation_and_adapter_code_modified'] is False and early['execution_scheduling_only'] is True
    assert sha(current / 'runtime_freeze_base.json') == scope['raw_runtime_freeze_sha256']
    assert sha(current / 'schema_preflight.json') == protocol['schema_preflight_sha256']
    assert sha(bundle / 'verify_additions.py') == scope['bundle_validator_sha256']
    assert scope['scope_n'] == 1 and scope['method_items_n'] == 4
    assert scope['baseline_public_original_n'] == 481 and scope['this_phase_original_union_n'] == 482 and scope['this_phase_pending_n'] == 78
    assert scope['planned_calls_without_transport_retry'] == 5
    assert scope['selection_used_phase_predictions'] is False and scope['live_admission_registry_used'] is False
    assert scope['common_supplemental_source_supplied'] is False
    assert scope['quality_regeneration_authorized'] is False and scope['human_expert_validation_n'] == 0
    generation = load(current / 'generation_complete.json')
    assert generation['completed_method_items'] == generation['required'] == 4
    requests = sorted((current / 'calls').glob('*.request.json'))
    attempts = sorted((current / 'calls').glob('*.response.json'))
    outcomes = sorted((current / 'calls').glob('*.outcome.json'))
    assert {p.name[:-len('.request.json')] for p in requests} == {p.name[:-len('.outcome.json')] for p in outcomes}
    assert len(requests) == len(outcomes) == 5
    assert {load(p)['request_id'] for p in requests} == {
        ident + '_' + tag for ident in tasks for tag in
        ['Text2Cypher', 'Text2SQL', 'C_answer', 'D_followup', 'D_answer']}
    referenced_attempts = []
    responses, http_counts, known_cost, unknown = 0, Counter(), 0.0, 0
    for path in requests:
        request = load(path)
        payload = request['payload']
        assert request['authorization_header_omitted'] is True
        assert request['payload_sha256'] == hashlib.sha256(json.dumps(payload, ensure_ascii=False).encode()).hexdigest()
        assert payload['model'] == 'anthropic/claude-opus-4.8'
        assert payload['provider'] == {'only': ['Anthropic'], 'allow_fallbacks': False, 'require_parameters': True}
        assert payload['reasoning'] == {'enabled': False} and payload['response_format'] == {'type': 'json_object'}
        outcome = load(path.with_name(path.name[:-len('.request.json')] + '.outcome.json'))
        assert 1 <= len(outcome['attempts']) <= 2
        if len(outcome['attempts']) == 2:
            assert outcome['attempts'][0]['retryable'] is True
            assert outcome['attempts'][0]['http_status'] is None or outcome['attempts'][0]['http_status'] == 429 or outcome['attempts'][0]['http_status'] >= 500
        known_cost += outcome['known_actual_cost_usd']
        unknown += outcome['unknown_cost_attempts']
        for index, attempt in enumerate(outcome['attempts']):
            attempt_path = current / 'calls' / Path(attempt['response_path']).name
            referenced_attempts.append(attempt_path.name)
            raw = load(attempt_path)
            assert raw['request_id'] == request['request_id'] and raw['attempt'] == index
            http_counts[raw.get('http_status')] += 1
            response = raw.get('response', {})
            if raw.get('http_status') == 200:
                responses += 1
                if response.get('choices'):
                    assert response.get('model') == 'anthropic/claude-opus-4.8' and response.get('provider') == 'Anthropic'
    assert len(referenced_attempts) == len(set(referenced_attempts))
    assert set(referenced_attempts) == {p.name for p in attempts}, 'every saved actual attempt is in the denominator'
    usage = load(current / 'usage.json')
    assert usage['received_response_calls'] == responses
    assert abs(usage['known_actual_cost_usd'] - known_cost) < 1e-9
    assert usage['unknown_cost_attempts'] == unknown
    visible = unique(rows(current / 'public_tasks.jsonl'))
    assert set(visible) == set(tasks)
    allowed = {'id', 'wg', 'repair_sha256', 'question_en', 'required_fields', 'collection',
               'cardinality_policy', 'identity_format', 'ordering_format'}
    for ident, task in tasks.items():
        public = visible[ident]
        assert set(public) <= allowed
        assert public['question_en'] == task['question_en'] and public['repair_sha256'] == task['repair_sha256']
        assert public['required_fields'] == [{k: v for k, v in f.items() if k != 'source_column_or_expression'} for f in task['required_fields']]
    for wg in {i.split('_')[0] for i in tasks}:
        guard = load(current / 'source_guards' / (wg + '.json'))
        sql = load(evidence / 'source_manifests' / (wg + '.manifest.json'))
        expected = sql.get('sqlite_sha256', sql.get('db_sha256', sql.get('output_sha256')))
        assert guard['before'] == guard['after'] == protocol['graph_sources'][wg]
        assert guard['sql_sha256'] == expected
    sys.path.insert(0, str(evidence / 'runtime'))
    import analyze_predictions as analyze
    import score_predictions
    methods = {'A': 'text2cypher', 'B': 'text2sql', 'C': 'single_retrieval', 'D': 'iterative_retrieval'}
    analysis = load(current / 'analysis.json')
    results, tables = {}, {}
    for arm, method in methods.items():
        predictions = unique(rows(current / method / 'predictions.jsonl'))
        statuses = unique(rows(current / method / 'statuses.jsonl'))
        assert set(predictions) == set(statuses) == set(tasks) and len(predictions) == 1
        for ident, prediction in predictions.items():
            status = statuses[ident]
            artifact = load(current / status['artifact'])
            assert prediction['repair_sha256'] == status['repair_sha256'] == tasks[ident]['repair_sha256']
            assert artifact['records'] == prediction['records'] and artifact['status'].upper() == status['status']
            if arm in {'A', 'B'}:
                generated = load(current / 'arm_outputs' / method / (ident + '.json'))
                assert artifact.get('generated_query') == generated.get('generated_query')
        raw = score_predictions.run(bundle / 'tasks.jsonl', bundle / 'reference_gold.jsonl', current / method / 'predictions.jsonl')
        assert raw == load(current / method / 'raw_scores.json')
        gated = {r['id']: analyze.gated(r, statuses[r['id']]['status']) for r in raw['outcomes']}
        assert list(gated.values()) == load(current / method / 'failure_gated_scores.json')
        tables[method] = analyze.summary(list(gated.values()))
        assert tables[method] == analysis['tables'][method]['overall']
        assert sha(current / method / 'predictions.jsonl') == analysis['tables'][method]['prediction_sha256']
        assert sha(current / method / 'statuses.jsonl') == analysis['tables'][method]['statuses_sha256']
        results[method] = gated
    pairs = []
    for index, a in enumerate(methods.values()):
        for b in list(methods.values())[index + 1:]:
            for metric in ('f1', 'exact'):
                pairs.append(dict(a=a, b=b, **analyze.paired(results[a], results[b], metric)))
    assert pairs == analysis['paired'] and analysis['admitted_n'] == 1
    assert manifest['additional_n'] == 1 and manifest['method_items'] == 4
    assert manifest['new_unique_core_ids'] == 1 and set(manifest['cohort_ids']) == set(tasks)
    assert manifest['planned_first_calls_without_transport_retry'] == 5
    assert (manifest['baseline_public_original_n'], manifest['registered_union_n'], manifest['registered_pending_n']) == (481, 482, 78)
    guard_provenance = load(evidence / 'runtime/AUTH21_root_guarded_native_execution_v1.adaptation.json')
    old_guard = evidence / 'runtime/original_guard_scheduler.py'
    new_guard = evidence / 'runtime/AUTH21_root_guarded_native_execution_v1.py'
    assert sha(old_guard) == guard_provenance['source_sha256']
    assert sha(new_guard) == guard_provenance['destination_sha256']
    previous = set(re.findall(r'authorized_incremental(\d+)_OpenRouter_release', old_guard.read_text()))
    assert len(previous) == 1
    old_increment = previous.pop()
    assert old_increment == manifest['guard_scheduler_source_increment']
    before_choices="choices=['RAN1','RAN2','RAN4','RAN5']"
    after_choices="choices=['RAN1']"
    assert guard_provenance['argument_choices_before']==['RAN1','RAN2','RAN4','RAN5']
    assert guard_provenance['argument_choices_after']==['RAN1']
    assert old_guard.read_text().count(before_choices)==1
    expected_guard=old_guard.read_text().replace('authorized_incremental' + old_increment, 'authorized_incremental21').replace(before_choices,after_choices).replace('--wg RAN3','--wg RAN1')
    assert expected_guard==new_guard.read_text(), 'Only seven AUTH19-to21 path substitutions, one WG restriction and the declared command-example correction are allowed'
    assert old_increment == '19'
    assert guard_provenance['replacement'] == {'authorized_incremental19': 'authorized_incremental21'}
    assert guard_provenance['native_lock_memory_cpu_readonly_protocol_unchanged'] is True and guard_provenance['API_calls'] == 0
    assert old_guard.read_text().count('authorized_incremental19') == manifest['guard_scheduler_replacement_n'] == 7
    parser_path = evidence / 'runtime/verify_incremental21_exact_prompts_and_parsers.py'
    parser_spec = importlib.util.spec_from_file_location('auth21_exact_parser_replay', parser_path)
    parser_module = importlib.util.module_from_spec(parser_spec)
    parser_spec.loader.exec_module(parser_module)
    parser_proof = parser_module.verify(evidence)
    assert parser_proof['status'] == 'PASS'
    privacy = load(evidence / 'privacy_check.json')
    assert privacy['exact_configured_credential_bytes_scanned'] is True and privacy['matches'] == 0
    assert privacy['credential_bytes_exposed'] is False
    assert manifest['all_actual_response_attempts_and_failures_preserved'] is True
    return {'status': 'PASS', 'additional_n': 1, 'method_items': 4, 'model_request_n': len(requests),
        'model_response_attempt_n': len(attempts), 'received_http200_response_n': responses,
        'http_status_counts': {str(k): v for k, v in http_counts.items()},
        'known_actual_cost_usd': known_cost, 'unknown_cost_attempts': unknown,
        'tables': tables, 'strict_scoring_and_failure_gates_replayed': True,
        'evidence_manifest_sha256': sha(evidence / 'manifest.json'),
        'human_expert_validation_n': 0, 'new_API_calls': 0, 'new_database_executions': 0,
        'contract_verification': proof, 'exact_prompt_and_parser_replay': parser_proof}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = verify(args.evidence.resolve(), args.bundle.resolve())
    if args.out:
        assert not args.out.exists(), 'Preserve earlier replay receipts'
        assert not args.out.resolve().is_relative_to(args.evidence.resolve())
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
