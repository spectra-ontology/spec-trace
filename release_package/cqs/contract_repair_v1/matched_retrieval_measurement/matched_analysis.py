#!/usr/bin/env python3
"""Replay public completed, frozen matched trials without changing any measurement.

No model/database calls or retries. A missing receipt is pending, not a scored
failure. Completed receipts with failed/missing predictions are empty under the
fixed protocol. Public output is constructed from an explicit allowlist.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import re
import sys

BASE = Path(__file__).resolve().parent
PUBLIC = BASE.parent
STUDY = BASE
ARMS = ('single', 'iterative', 'structured')
METRICS = ('complete_record_f1', 'output_exact', 'named_cell_f1')
CONTRASTS = (('iterative', 'single'), ('structured', 'single'), ('structured', 'iterative'))
TOKEN_KEYS = ('input_tokens', 'cached_input_tokens', 'output_tokens')
TRACKS = {'aggregation', 'lookup', 'relational', 'multihop'}


class AnalysisError(ValueError):
    """Only constant, public-safe messages are passed to the CLI."""


def require(condition, message):
    if not condition:
        raise AnalysisError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        raise AnalysisError('A required artifact is absent or not complete JSON') from None


def by_id(rows):
    require(isinstance(rows, list), 'Artifact items must be a list')
    result = {}
    for row in rows:
        require(isinstance(row, dict), 'Artifact item must be an object')
        item_id = row.get('id')
        require(isinstance(item_id, str) and re.fullmatch(r'[A-Za-z0-9_-]+', item_id), 'Unsafe task identity')
        require(item_id not in result, 'Duplicate task identity')
        result[item_id] = row
    return result


def load_scorer(directory):
    path = directory / 'score_contract.py'
    spec = importlib.util.spec_from_file_location('frozen_named_contract_scorer', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def contract_for(task):
    anchor = {'question': task['task_question'], 'query': task['reference_query']}
    fields = [{**{k: field[k] for k in ('name', 'type', 'role', 'nullable') if k in field},
               'source_anchor': anchor} for field in task['required_fields']]
    return {'version': 1, 'item_id': task['id'], 'status': 'ready',
            'required_fields': fields, 'collection': {'kind': task['collection_kind']},
            'constraints': [{'kind': 'scope', 'field': 'source_population',
                             'value': 'explicit reference query over restored deposited graph',
                             'verification': 'reference_query', 'source_anchor': anchor}],
            'unresolved_reasons': []}


def load_bundle(directory, protocol_path):
    definitions = directory / 'prospective_task_definitions_v2.json'
    gold_path = directory / 'prospective_reference_gold_frozen_v2.json'
    eligibility_path = directory / 'prospective_eligibility_v1.json'
    protocol = read_json(protocol_path)
    require(tuple(protocol['arms']) == ARMS, 'Fixed arm definitions differ')
    require(protocol['uncertainty']['replicates'] == 10000 and protocol['uncertainty']['seed'] == 0,
            'Fixed bootstrap specification differs')
    tasks = read_json(definitions)
    gold = read_json(gold_path)
    eligibility = read_json(eligibility_path)
    require(gold['taskset_sha256'] == sha(definitions), 'Gold/definition hash mismatch')
    require(eligibility['definition_sha256'] == sha(definitions), 'Eligibility/definition hash mismatch')
    require(eligibility['gold_execution_sha256'] == sha(gold_path), 'Eligibility/gold hash mismatch')
    require(eligibility['frozen_before_model_outcomes'] is True, 'Eligibility was not frozen before outcomes')
    task_rows, gold_rows, eligible_rows = map(by_id, (tasks['items'], gold['items'], eligibility['items']))
    require(len(task_rows) == 40 and set(task_rows) == set(gold_rows) == set(eligible_rows),
            'Fixed selected40 identities differ')
    require(set(tasks['selection']['selected_ids']) == set(task_rows), 'Source selection changed')
    ids = sorted(item_id for item_id, row in eligible_rows.items() if row['eligible'])
    require(len(ids) == eligibility['eligible_n'] == 36, 'Fixed eligible36 identities differ')
    # contract_repair_v1 and spectra_cq_v2.0 are siblings below cqs.
    track_path = directory.parent / 'spectra_cq_v2.0/splits/track_assignment.json'
    tracks = read_json(track_path)
    dispositions = []
    for item_id in sorted(task_rows):
        task, reference, disposition = task_rows[item_id], gold_rows[item_id], eligible_rows[item_id]
        require(disposition['eligible'] == reference['eligible'], 'Eligibility flag differs from reference execution')
        require(task['wg'] in {f'RAN{i}' for i in range(1, 6)}, 'Unknown working group')
        require(tracks.get(item_id) in TRACKS, 'Unknown original released track')
        query_hash = hashlib.sha256((task['reference_query'] or '').encode()).hexdigest()
        require(reference['reference_query_sha256'] == query_hash, 'Reference query hash mismatch')
        execution = reference['execution']
        if item_id in ids:
            require(execution['status'] == 'OK' and execution['truncated'] is False
                    and reference['required_types_match'] is True, 'Eligible reference execution is incomplete')
            require(execution['columns'] == [field['name'] for field in task['required_fields']],
                    'Eligible reference output columns differ')
        dispositions.append({'id': item_id, 'wg': task['wg'], 'eligible': bool(disposition['eligible']),
                             'reference_status': execution['status'] if execution['status'] in
                             {'OK', 'ERROR', 'ROW_CAP', 'UNRESOLVED_DEFINITION'} else 'other',
                             'reference_rows': len(execution['rows'])})
    hashes = {'definitions': sha(definitions), 'graph_relative_reference_gold': sha(gold_path),
              'eligibility': sha(eligibility_path), 'scientific_analysis_protocol': sha(protocol_path),
              'named_contract_scorer': sha(directory / 'score_contract.py'), 'original_track_labels': sha(track_path)}
    return {'ids': ids, 'tasks': task_rows, 'gold': gold_rows, 'tracks': tracks,
            'dispositions': dispositions, 'input_sha256': hashes, 'protocol': protocol}


def error_category(error):
    """No exception text, paths, headers, stderr or provider events are exported."""
    if not error:
        return None
    if error in {'timeout', 'tool_use', 'call_budget', 'query_execution', 'helper_failure',
                 'generation_or_prediction_failure', 'missing_prediction', 'invalid_prediction_structure'}:
        return error
    text = str(error).lower()
    if 'timeout' in text or 'timed out' in text:
        return 'timeout'
    if 'tool action' in text:
        return 'tool_use'
    if 'cap' in text or 'budget' in text:
        return 'call_budget'
    if 'query execution' in text:
        return 'query_execution'
    if 'helper' in text:
        return 'helper_failure'
    return 'generation_or_prediction_failure'


def call_numbers(receipt):
    if receipt['arm'] == 'structured':
        return [receipt['call_number']] if type(receipt.get('call_number')) is int else []
    return [row['number'] for row in receipt.get('calls', []) if type(row.get('number')) is int]


def evaluate_trial(scorer, task, gold, receipt, calls):
    categories = [error_category(receipt.get('error_category'))]
    for number in call_numbers(receipt):
        require(number in calls, 'Completed receipt refers to an absent caller record')
        call = calls[number]
        categories.append(error_category(call.get('error_category')))
        if call.get('tool_action_count', 0):
            categories.append('tool_use')
    prediction = receipt.get('prediction')
    missing = prediction is None
    malformed = not isinstance(prediction, dict) or not isinstance(prediction.get('records'), list)
    if not malformed:
        malformed = not all(isinstance(record, dict) for record in prediction['records'])
        malformed = malformed or type(prediction.get('abstain')) is not bool
    # Preserve independently observable specific failures even when the receipt
    # only says "reader failed". Never expose raw exception text.
    categories = {category for category in categories if category}
    if missing:
        categories.add('missing_prediction')
    elif malformed:
        categories.add('invalid_prediction_structure')
    priority = ('tool_use', 'timeout', 'call_budget', 'query_execution', 'helper_failure',
                'generation_or_prediction_failure', 'missing_prediction', 'invalid_prediction_structure')
    failure = next((category for category in priority if category in categories), None)
    observed_abstain = prediction.get('abstain') if isinstance(prediction, dict) else None
    observed_abstain = observed_abstain if type(observed_abstain) is bool else None
    observed_records = prediction.get('records', []) if isinstance(prediction, dict) else []
    inconsistent = observed_abstain is True and isinstance(observed_records, list) and bool(observed_records)
    scored = [] if failure else prediction['records']
    result = scorer.score_contract(contract_for(task), gold, scored)
    full, cells = result['output_full_records'], result['partial_named_cells']
    return {'id': task['id'], 'complete_record_f1': full['f1'], 'output_exact': result['output_exact'],
            'named_cell_f1': cells['f1'], 'complete_record_precision': full['precision'],
            'complete_record_recall': full['recall'], 'named_cell_precision': cells['precision'],
            'named_cell_recall': cells['recall'], 'gold_records': full['gold_records'],
            'scored_predicted_records': full['predicted_records'], 'failure_category': failure,
            'failure_flags': sorted(categories),
            'observed_abstain': observed_abstain, 'inconsistent_nonempty_record_abstain': inconsistent,
            'scorer_semantic_exact': result['exact'], 'semantic_validation': False}


def summarize(rows):
    require(bool(rows), 'Cannot summarize an empty task group')
    keys = (*METRICS, 'complete_record_precision', 'complete_record_recall',
            'named_cell_precision', 'named_cell_recall')
    return {'n': len(rows), **{key: sum(row[key] for row in rows) / len(rows) for key in keys},
            'failure_counts': dict(sorted(Counter(row['failure_category'] for row in rows if row['failure_category']).items())),
            'failure_flag_counts': dict(sorted(Counter(flag for row in rows for flag in row['failure_flags']).items())),
            'observed_abstain_true_including_runner_defaults': sum(row['observed_abstain'] is True for row in rows),
            'successful_output_abstain_true': sum(row['observed_abstain'] is True and not row['failure_category'] for row in rows),
            'inconsistent_nonempty_record_abstain': sum(row['inconsistent_nonempty_record_abstain'] for row in rows),
            'empty_gold_n': sum(row['gold_records'] == 0 for row in rows)}


def percentile(values, probability):
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    fraction = position - lower
    return ordered[lower] + fraction * (ordered[min(lower + 1, len(ordered) - 1)] - ordered[lower])


def paired_bootstrap(arm_rows, *, replicates=10000, seed=0):
    ids = [row['id'] for row in arm_rows['single']]
    require(all([row['id'] for row in arm_rows[arm]] == ids for arm in ARMS), 'Paired task identities/order differ')
    n = len(ids)
    require(n > 0, 'Bootstrap cohort is empty')
    differences = {(left, right, metric): [a[metric] - b[metric] for a, b in zip(arm_rows[left], arm_rows[right])]
                   for left, right in CONTRASTS for metric in METRICS[:2]}
    samples = {key: [] for key in differences}
    rng = random.Random(seed)
    for _ in range(replicates):
        indices = [rng.randrange(n) for _ in range(n)]
        for key, delta in differences.items():
            samples[key].append(sum(delta[index] for index in indices) / n)
    return [{'left': left, 'right': right, 'metric': metric,
             'mean_difference': sum(delta) / n,
             'percentile_95_ci': [percentile(samples[(left, right, metric)], .025),
                                  percentile(samples[(left, right, metric)], .975)],
             'paired_tasks': n, 'replicates': replicates, 'seed': seed,
             'interpretation': 'matched text retrieval contrast' if left == 'iterative' else
             'descriptive unequal-representation/source-cutoff contrast'}
            for (left, right, metric), delta in differences.items()]


def finite_nonnegative(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def summarize_calls(numbers, calls, reservations):
    numbers = set(numbers)
    completed = [calls[number] for number in sorted(numbers) if number in calls]
    reserved = [reservations[number] for number in sorted(numbers) if number in reservations]
    tokens = {key: 0 for key in TOKEN_KEYS}
    field_coverage = {key: 0 for key in TOKEN_KEYS}
    events_with_usage = 0
    missing_usage = 0
    for call in completed:
        captured = False
        captured_fields = set()
        for event in call.get('usage_events', []):
            usage = event.get('usage', {}) if isinstance(event, dict) else {}
            if not isinstance(usage, dict):
                continue
            if any(type(usage.get(key)) is int and usage[key] >= 0 for key in TOKEN_KEYS):
                captured = True
                events_with_usage += 1
                for key in TOKEN_KEYS:
                    if type(usage.get(key)) is int and usage[key] >= 0:
                        tokens[key] += usage[key]
                        captured_fields.add(key)
        for key in captured_fields:
            field_coverage[key] += 1
        missing_usage += not captured
    elapsed = [call['seconds'] for call in completed if finite_nonnegative(call.get('seconds'))]
    starts = [row['reserved_unix'] for row in reserved if finite_nonnegative(row.get('reserved_unix'))]
    finishes = [call['finished_unix'] for call in completed if finite_nonnegative(call.get('finished_unix'))]
    return {'durable_reservations': len(reserved), 'completed_caller_attempts': len(completed),
            'cli_invocations_with_process_returncode': sum(type(call.get('returncode')) is int for call in completed),
            'reservations_without_completed_caller_record': len((numbers & set(reservations)) - set(calls)),
            'captured_usage_events': events_with_usage, 'caller_records_without_captured_usage': missing_usage,
            'captured_tokens': tokens, 'caller_records_with_captured_token_field': field_coverage,
            'caller_records_without_captured_token_field': {key: len(completed) - field_coverage[key] for key in TOKEN_KEYS},
            'sum_cli_seconds': sum(elapsed),
            'caller_records_without_elapsed_seconds': len(completed) - len(elapsed),
            'span_first_reservation_to_last_call_finish_seconds': max(finishes) - min(starts) if starts and finishes else None,
            'monetary_cost': None, 'billing_limit': 'CLI does not capture verified monetary billing or provider-internal retry count.'}


def read_measurements(study, bundle):
    calls, reservations = {}, {}
    directory = study / 'calls'
    for path in sorted(directory.glob('*.json')):
        if not re.fullmatch(r'\d+(?:_[A-Za-z0-9_.:-]+)?(?:\.reservation)?\.json', path.name):
            continue
        row = read_json(path)
        number = row.get('number')
        require(type(number) is int and number > 0, 'Caller record has invalid identity')
        require(int(path.name.split('_', 1)[0].split('.', 1)[0]) == number,
                'Caller identity differs from its filename')
        target = reservations if path.name.endswith('.reservation.json') else calls
        require(number not in target, 'Duplicate caller or reservation identity')
        target[number] = row
    # Keep deposited text export bytes intact. This scalar-only sidecar carries
    # separately captured process return codes and tool-action counts, plus each
    # original raw caller file hash. Nothing here infers successful execution.
    proof_path = study / 'caller_returncodes_v1.json'
    proof_rows = read_json(proof_path)['calls']
    require(isinstance(proof_rows, list), 'Caller scalar attestation must be a list')
    proof = {}
    for row in proof_rows:
        number = row.get('number')
        require(type(number) is int and number > 0 and number not in proof,
                'Caller scalar attestation identity differs')
        require(type(row.get('returncode')) is int and
                type(row.get('tool_action_count')) is int and row['tool_action_count'] >= 0,
                'Caller scalar attestation has invalid captured values')
        require(isinstance(row.get('original_call_sha256'), str) and
                re.fullmatch(r'[0-9a-f]{64}', row['original_call_sha256']),
                'Caller scalar attestation has invalid source hash')
        proof[number] = row
    require(set(proof) == set(calls), 'Caller scalar attestation cohort differs')
    for number, row in proof.items():
        calls[number].update(returncode=row['returncode'], tool_action_count=row['tool_action_count'])
    bundle['input_sha256']['caller_scalar_attestation'] = sha(proof_path)
    receipts, pending, hashes = {}, [], []
    for arm in ARMS:
        for item_id in bundle['ids']:
            path = study / 'predictions' / arm / (item_id + '.json')
            if not path.exists():
                pending.append({'id': item_id, 'arm': arm})
                continue
            row = read_json(path)
            require(row.get('id') == item_id and row.get('arm') == arm, 'Prediction receipt identity differs')
            receipts[(arm, item_id)] = row
            hashes.append({'id': item_id, 'arm': arm, 'sha256': sha(path)})
    return receipts, calls, reservations, pending, hashes


def verify_run_manifests(study, bundle):
    """Pin frozen task prompts and source guards, exporting only their hashes."""
    retrieval_path = study / 'frozen_run_manifest.json'
    structured_path = study / 'frozen_structured_manifest.json'
    retrieval, structured = read_json(retrieval_path), read_json(structured_path)
    require(sorted(retrieval['task_ids']) == bundle['ids'], 'Frozen reader cohort differs')
    require(retrieval['gold_exposed_to_reader'] is False and
            structured['gold_read_by_generator'] is False and
            structured['reference_query_read_by_generator'] is False,
            'Gold or reference query was exposed to a generator')
    require(structured['retrieval_manifest_sha256'] == sha(retrieval_path),
            'Structured and retrieval task freezes differ')
    rows = by_id(retrieval['tasks'])
    require(sorted(rows) == bundle['ids'], 'Frozen reader tasks differ')
    for item_id in bundle['ids']:
        frozen, task = rows[item_id], bundle['tasks'][item_id]
        require(frozen['question'] == task['task_question'] and
                frozen['original_question'] == task['original_question'] and
                frozen['variant_id'] == task['variant_id'], 'Frozen task wording differs')
        expected = [{key: field[key] for key in ('name', 'type', 'role', 'nullable', 'json_schema') if key in field}
                    for field in task['required_fields']]
        require(frozen['contract']['required_fields'] == expected and
                frozen['contract']['collection']['kind'] == task['collection_kind'],
                'Frozen output contract differs')
    bundle['input_sha256'].update({'frozen_reader_manifest': sha(retrieval_path),
                                  'frozen_structured_manifest': sha(structured_path)})


def analyze(bundle, receipts, calls, reservations, scorer, prediction_hashes):
    require(all((arm, item_id) in receipts for arm in ARMS for item_id in bundle['ids']),
            'Measurement is incomplete; pending receipts are not completed missing predictions')
    arm_rows, groups, costs = {}, {}, {}
    for arm in ARMS:
        arm_rows[arm] = [evaluate_trial(scorer, bundle['tasks'][item_id],
                                      bundle['gold'][item_id]['execution']['rows'],
                                      receipts[(arm, item_id)], calls) for item_id in bundle['ids']]
        groups[arm] = {}
        for group_name, classifier in (
                ('working_group', lambda i: bundle['tasks'][i]['wg']),
                ('original_released_track', lambda i: bundle['tracks'][i]),
                ('required_named_field_count', lambda i: 'single' if len(bundle['tasks'][i]['required_fields']) == 1 else 'multiple')):
            buckets = {}
            for row in arm_rows[arm]:
                buckets.setdefault(classifier(row['id']), []).append(row)
            groups[arm][group_name] = {name: summarize(rows) for name, rows in sorted(buckets.items())}
        numbers = [number for item_id in bundle['ids'] for number in call_numbers(receipts[(arm, item_id)])]
        costs[arm] = summarize_calls(numbers, calls, reservations)
        costs[arm]['query_execution_seconds_sum'] = sum(
            row.get('execution', {}).get('elapsed_s', 0) for row in
            (receipts[(arm, item_id)] for item_id in bundle['ids'])
            if isinstance(row.get('execution'), dict) and finite_nonnegative(row['execution'].get('elapsed_s')))
    helper_numbers = [row['number'] for item_id in bundle['ids']
                      for row in receipts[('iterative', item_id)].get('calls', [])
                      if row.get('stage') == 'helper' and type(row.get('number')) is int]
    selected_numbers = {number for receipt in receipts.values() for number in call_numbers(receipt)}
    require(len(selected_numbers) == sum(len(set(call_numbers(receipt))) for receipt in receipts.values()),
            'Caller record is shared by distinct scientific trials')
    return {'kind': 'offline reproduction of completed matched measurement on explicit source-defined task variants',
            'analysis_state': 'complete', 'fixed_eligible_tasks': len(bundle['ids']), 'arms': list(ARMS),
            'input_sha256': bundle['input_sha256'], 'prediction_receipt_sha256': prediction_hashes,
            'all40_dispositions': bundle['dispositions'], 'metrics': {arm: summarize(rows) for arm, rows in arm_rows.items()},
            'per_task': arm_rows, 'subgroups': groups, 'paired_primary_contrasts': paired_bootstrap(arm_rows),
            'costs': {'by_arm': costs, 'iterative_helper': summarize_calls(helper_numbers, calls, reservations),
                      'overall_ledger': summarize_calls(set(calls) | set(reservations), calls, reservations),
                      'caller_records_not_linked_to_scored_tasks': len(set(calls) - selected_numbers)},
            'caller_input_sha256': {'completed_records': [
                {'number': number, 'sha256': hashlib.sha256(json.dumps(calls[number], sort_keys=True,
                 ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()} for number in sorted(calls)],
                'reservations': [{'number': number, 'sha256': hashlib.sha256(json.dumps(reservations[number],
                 sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()}
                 for number in sorted(reservations)],
                'hash_encoding': 'UTF-8 canonical JSON, sorted keys, compact separators, ensure_ascii=False'},
            'bootstrap_definition': {'replicates': 10000, 'seed': 0, 'rng': 'Python random.Random',
                                     'sampling': 'same task indices shared across arms/primary contrasts',
                                     'interval': '2.5/97.5 percentiles with linear interpolation; no significance gate'},
            'measurement_limits': [
                'Graph-relative reference answers for new explicit variants; not repaired-original-question performance or domain-expert truth.',
                'Supplemental fields are ignored. Required named roles/types and declared set/bag/sequence semantics use the public scorer.',
                'Nested JSON is a complete named cell; internal list order is preserved, not independently scored per nested member.',
                'Failed completed trials are empty on the fixed denominator. An empty failed prediction can match an empty reference under the unchanged scorer.',
                'Absent receipt files are pending and prevent publication of actual metrics.',
                'Iterative/helper cost is included; captured CLI token usage is incomplete when completion events are missing.',
                'Current retained text and deposited graph source cutoffs are not asserted equal; graph full access versus capped text is an input asymmetry.',
                'Structured/text contrasts are descriptive; no unique graph-storage benefit or causal graph-engine claim.',
                'Original track labels do not certify physical path depth. Unweighted selected small cohort is not a Core population estimate.',
                'Bootstrap ignores template clustering and does not supply acceptance probability, best-arm selection or population-generalization inference.',
                'No independent expert validation, outside-RAN transfer or missing-evidence abstention evaluation.',
                'Operational abstain flags include runner fallback defaults; successful flags and inconsistent nonempty-record flags are reported separately.'],
            'semantic_validation': False, 'domain_expert_validation': False,
            'abstention_validation': False, 'original_benchmark_repaired': False,
            'unequal_graph_text_context_and_source_cutoff': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--public-directory', type=Path, default=PUBLIC)
    parser.add_argument('--study-directory', type=Path, default=STUDY)
    parser.add_argument('--protocol', type=Path, default=BASE / 'scientific_analysis_protocol.json')
    parser.add_argument('--require-complete', action='store_true')
    parser.add_argument('--out', type=Path, help='New public-safe report; existing files are never overwritten.')
    args = parser.parse_args()
    try:
        bundle = load_bundle(args.public_directory, args.protocol)
        verify_run_manifests(args.study_directory, bundle)
        receipts, calls, reservations, pending, hashes = read_measurements(args.study_directory, bundle)
        if pending:
            require(not args.require_complete and args.out is None, 'Measurement is incomplete; no actual report written')
            print(json.dumps({'analysis_state': 'incomplete', 'fixed_eligible_tasks': len(bundle['ids']),
                              'completed_receipts': len(receipts), 'pending_receipts': len(pending)}))
            return
        if args.out is None:
            print(json.dumps({'analysis_state': 'ready_for_explicit_analysis', 'completed_receipts': len(receipts),
                              'fixed_eligible_tasks': len(bundle['ids'])}))
            return
        require(not args.out.exists(), 'Refusing to replace an existing analysis report')
        scorer = load_scorer(args.public_directory)
        report = analyze(bundle, receipts, calls, reservations, scorer, hashes)
        report['analysis_code_sha256'] = sha(__file__)
        with args.out.open('x') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
        print(json.dumps({'analysis_state': 'complete', 'fixed_eligible_tasks': len(bundle['ids']),
                          'report_sha256': sha(args.out)}))
    except (AnalysisError, ValueError, KeyError, TypeError, OSError):
        print('Analysis refused: incomplete or inconsistent frozen measurement artifacts.', file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
