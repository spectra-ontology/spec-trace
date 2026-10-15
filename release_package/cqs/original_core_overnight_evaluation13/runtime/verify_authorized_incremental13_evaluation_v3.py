#!/usr/bin/env python3
"""Spec: AUTH13 exact two original ordinary recorded-field contracts.
Ontology: original company/WorkItem contribution history and RAN4 NewTS recorded metadata.
Cycle: KDD2027 Datasets and Benchmarks Cycle1.
배경: reuse actual completed gates, preserve the actual committed464 baseline.
사용: root reviews/invokes private helpers; no inferred commit or index hash.
LLM 호출: no calls from preparation, package or saved replay helpers.
Offline saved-output replay of every authorized_incremental13 method item.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
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
    spec = importlib.util.spec_from_file_location('authorized_incremental13_public_contract_verify', bundle / 'verify_additions.py')
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    proof = validator.verify(bundle)
    assert proof['status'] == 'PASS' and proof['additional_admitted_n'] == 2
    assert proof['native_rows'] == 65 and proof['actual_scorer_controls'] == 16
    tasks = unique(validator.lines(bundle / 'tasks.jsonl'))
    assert set(tasks) == {'RAN2_P1_CQ4-1', 'RAN4_P5_CQ2-3'}
    gold_controls = unique(validator.lines(bundle / 'reference_gold.jsonl'))
    additional=proof['additional_saved_control_replay']
    assert additional['status']=='PASS'
    additional_n=additional['additional_saved_controls_n']
    assert additional_n == 37
    assert additional['actual_population_control_replays_n'] == 25
    assert additional['separate_synthetic_control_replays_n'] == 12
    current = evidence / 'current'
    protocol = load(current / 'protocol.json')
    assert sha(current / 'protocol.json') == manifest['protocol_sha256']
    assert protocol['bundle_manifest_sha256'] == sha(bundle / 'manifest.json')
    assert protocol['tasks_sha256'] == sha(bundle / 'tasks.jsonl')
    assert protocol['gold_sha256'] == sha(bundle / 'reference_gold.jsonl')
    assert protocol['public_tasks_sha256'] == sha(current / 'public_tasks.jsonl')
    assert protocol['admitted_n'] == 2 and set(protocol['cohort_ids']) == set(tasks)
    assert protocol['model'] == 'anthropic/claude-opus-4.8' and protocol['provider'] == 'Anthropic'
    for name, expected in protocol['code_pins'].items():
        assert sha(evidence / 'runtime' / name) == expected, name
    for name, expected in protocol['schema_pins'].items():
        assert sha(current / name) == expected, name
    for wg, item in protocol['sql_manifests'].items():
        assert sha(evidence / 'source_manifests' / (wg + '.manifest.json')) == item['sha256']
    scope = protocol['authorized_incremental13_extension']
    assert sha(evidence / 'authorization/scope.json') == manifest['scope_sha256'] == scope['scope_sha256']
    assert sha(evidence / 'authorization/admission_inputs.json') == scope['admission_inputs_sha256']
    assert sha(evidence / 'runtime/runtime_source_copy_receipt.json') == scope['source_copy_receipt_sha256']
    early_path = evidence / 'runtime/early_execution_reader_copy_receipt.json'
    if early_path.exists():
        early = load(early_path)
        assert sha(evidence / 'runtime/execute_ready.py') == early['copy_sha256'] == early['source_sha256']
        assert early['byte_identical'] is True and isinstance(early['purpose'], str) and early['purpose']
    guards=sorted((evidence/'runtime').glob('AUTH13_root_guarded_native_execution*.py'))
    assert len(guards)==1
    adaptation=load(guards[0].with_suffix('.adaptation.json'))
    assert sha(guards[0])==adaptation['copy_sha256']
    assert adaptation['generation_prompts_or_adapters_changed'] is False
    assert adaptation['native_resource_guards_unchanged'] is True
    assert adaptation['underlying_kernel_18GiB_guard_retained_without_edits'] is True
    assert adaptation['existing_additional_Linux_and_Windows_admission_bytes']==26*1024**3
    inherited=evidence/'runtime/inherited_scheduler/AUTH12_root_guarded_native_execution_v1.py'
    assert sha(inherited)==adaptation['source_sha256']=='3995ed7ffbe436b07880525769aab6d6f64ef4abc5b36275e7045f83cd39ce10'
    expected=inherited.read_text().replace('authorized_incremental12','authorized_incremental13').replace('AUTH12','AUTH13')
    assert guards[0].read_text()==expected
    assert sha(current / 'runtime_freeze_base.json') == scope['raw_runtime_freeze_sha256']
    assert sha(current / 'schema_preflight.json') == protocol['schema_preflight_sha256']
    assert sha(bundle / 'verify_additions.py') == scope['bundle_validator_sha256']
    assert scope['scope_n'] == 2 and scope['method_items_n'] == 8
    assert scope['planned_calls_without_transport_retry'] == 10
    assert scope['selection_used_phase_predictions'] is False and scope['live_admission_registry_used'] is False
    assert scope['quality_regeneration_authorized'] is False and scope['human_expert_validation_n'] == 0
    extension=protocol['authorized_incremental13_extension']
    assert extension['source_order_contract_exposed_to_all_methods'] is True
    assert extension['byte_identical_to_prior_prompt_protocol'] is False
    change=load(evidence/'runtime/source_order_contract_change_receipt.json')
    assert sha(evidence/'runtime/source_order_contract_change_receipt.json')==extension['source_order_contract_change_receipt_sha256']
    assert change['prior_runtime_or_outputs_modified'] is False and change['quality_regeneration_authorized'] is False
    assert sha(evidence/'runtime/exact_share_patch_manifest.json')==extension['exact_share_protocol']['patch_manifest_sha256']
    assert extension['exact_share_protocol']['public_task_prompt_parser_candidate_score_hooks'] is True
    assert extension['exact_share_protocol']['no_rounding_tolerance'] is True
    generation = load(current / 'generation_complete.json')
    assert generation['completed_method_items'] == generation['required'] == 8
    requests = sorted((current / 'calls').glob('*.request.json'))
    attempts = sorted((current / 'calls').glob('*.response.json'))
    outcomes = sorted((current / 'calls').glob('*.outcome.json'))
    assert {p.name[:-len('.request.json')] for p in requests} == {p.name[:-len('.outcome.json')] for p in outcomes}
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
            first = outcome['attempts'][0]
            first_raw = load(current / 'calls' / Path(first['response_path']).name)
            code = first.get('http_status')
            http_retry = code == 429 or (isinstance(code, int) and 500 <= code < 600)
            read_retry = first_raw.get('error_type') in {'TimeoutError', 'OSError', 'URLError', 'ConnectionResetError', 'ConnectionAbortedError', 'BrokenPipeError'} and 'response' not in first_raw
            assert http_retry or read_retry, 'only preserved declared transport failures may retry'
        known_cost += outcome['known_actual_cost_usd']
        unknown += outcome['unknown_cost_attempts']
        for index, attempt in enumerate(outcome['attempts']):
            attempt_path = current / 'calls' / Path(attempt['response_path']).name
            raw = load(attempt_path)
            assert raw['request_id'] == request['request_id'] and raw['attempt'] == index
            http_counts[raw.get('http_status')] += 1
            response = raw.get('response', {})
            if raw.get('http_status') == 200 and isinstance(raw.get('response'), dict):
                responses += 1
                if response.get('choices'):
                    assert response.get('model') == 'anthropic/claude-opus-4.8' and response.get('provider') == 'Anthropic'
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
        assert public['collection'].get('source_order_keys')==task['collection'].get('source_order_keys')
        fields=[{k:v for k,v in f.items() if k!='source_column_or_expression'} for f in task['required_fields']]
        descriptor=task['collection'].get('rational_share_representation')
        if descriptor:
            minimal={k:descriptor[k] for k in ['kind','unit','field']}
            assert public['collection']['rational_share_representation']==minimal
            fields=[dict(f,value_representation={'kind':'exact_rational_share','unit':'one'}) if f['name']==descriptor['field'] else f for f in fields]
        assert public['required_fields']==fields
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
        assert set(predictions) == set(statuses) == set(tasks) and len(predictions) == 2
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
    assert pairs == analysis['paired'] and analysis['admitted_n'] == 2
    assert manifest['additional_n'] == 2 and manifest['method_items'] == 8
    return {'status': 'PASS', 'additional_n': 2, 'method_items': 8, 'model_request_n': len(requests),
        'model_response_attempt_n': len(attempts), 'received_http200_response_n': responses,
        'http_status_counts': {str(k): v for k, v in http_counts.items()},
        'known_actual_cost_usd': known_cost, 'unknown_cost_attempts': unknown,
        'tables': tables, 'strict_scoring_and_failure_gates_replayed': True,
        'evidence_manifest_sha256': sha(evidence / 'manifest.json'),
        'human_expert_validation_n': 0, 'new_API_calls': 0, 'new_database_executions': 0,
        'contract_verification': proof, 'actual_additional_controls_n': additional_n,
        'actual_additional_controls_replayed': True, 'additional_control_proof': additional, 'http200_requires_complete_parsed_response_body': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = verify(args.evidence.resolve(), args.bundle.resolve())
    if args.out:
        assert not args.out.resolve().is_relative_to(args.evidence.resolve())
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
