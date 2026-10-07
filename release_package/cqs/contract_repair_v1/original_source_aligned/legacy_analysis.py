#!/usr/bin/env python3
"""Authorized, no-model diagnostic of retained original-question predictions.

Actual audit labels and model scores are never read by self-tests. A real run
requires separately pinned root authorization and a closed audit file index.
"""
from __future__ import annotations

import argparse
import ast
import collections
import gzip
import importlib.util
import json
from pathlib import Path
import random
import sys

sys.dont_write_bytecode = True

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
HERE = Path(__file__).resolve().parent
TRACK = Path('scripts/publication/paper/under-review/kdd-2027-datasets-benchmarks')
ANALYSIS = ROOT / TRACK / 'baseline/results/analysis/rebuttal'
RUNS = ROOT / 'logs/publication/paper/under-review/kdd-2027-datasets-benchmarks/baseline-runs'
AUDIT_OUT = RUNS / '_semantic_alignment_audit_v1/native_signature_v1'
SOURCE_OUT = RUNS / '_source_contract_expansion_v1'
N_BOOT, SEED = 10000, 0
METRICS = ('f1', 'exact', 'precision', 'recall')


class ProofError(ValueError):
    pass


class IntegrityError(ProofError):
    pass


class ScientificEvidenceUnavailable(ProofError):
    """Captured bytes are bound, but strict final JSON cannot support labels."""


def strict_source_json(text):
    def pairs(entries):
        value = {}
        for key, item in entries:
            if key in value:
                raise ScientificEvidenceUnavailable('duplicate key in captured final JSON')
            value[key] = item
        return value
    try:
        return json.loads(text, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(
                              ScientificEvidenceUnavailable('nonfinite captured final JSON')))
    except (json.JSONDecodeError, TypeError) as exc:
        raise ScientificEvidenceUnavailable('captured final JSON is not strictly parseable') from exc


def closure_status_agrees(scientific_status, terminal_status, strict_unavailable=False):
    # A strict parser may withhold scientific evidence from an unchanged VALID
    # terminal receipt. It never changes its preserved technical closure status.
    return scientific_status.upper() == terminal_status or (
        strict_unavailable and scientific_status == 'invalid' and terminal_status == 'VALID')


def module_from_path(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PREP = module_from_path(HERE / 'prepare_original_aligned_retained_diagnostic_v1.py', 'retained_diagnostic_preparation')
sha = PREP.sha


def require(condition, message):
    if not condition:
        raise ProofError(message)


def read_json(path):
    def pairs(entries):
        value = {}
        for key, item in entries:
            require(key not in value, 'duplicate JSON object key')
            value[key] = item
        return value
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ProofError('nonfinite JSON number')))


def pinned(path, expected):
    require(type(expected) is str and Path(path).is_file() and sha(path) == expected,
            'file pin mismatch: ' + Path(path).name)


def safe_child(directory, relative):
    require(type(relative) is str, 'relative path is not a string')
    p = Path(relative)
    require(not p.is_absolute() and '..' not in p.parts, 'unsafe relative artifact path')
    return Path(directory) / p


def legacy_scorer(baseline):
    env = {'norm': PREP.historical_norm(baseline)}
    tree = ast.parse((baseline / 'score.py').read_text())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'score_row']
    require(len(nodes) == 1, 'historical score_row missing or duplicated')
    exec(compile(ast.Module(body=nodes, type_ignores=[]), 'pinned historical score_row', 'exec'), env)
    return env['norm'], env['score_row']


def validate_command(command, reservation, protocol):
    require(type(command) is list and all(type(v) is str for v in command), 'CLI command not an argv list')
    cpus = reservation.get('cpu_affinity')
    require(type(cpus) is list and len(cpus) == 2 and len(set(cpus)) == 2 and
            all(type(v) is int and v >= 0 for v in cpus), 'CPU reservation invalid')
    require(command.count('--cd') == 1, 'CLI scratch directory missing or duplicated')
    scratch = command[command.index('--cd') + 1]
    expected = ['taskset', '-c', ','.join(map(str, cpus)), 'codex', 'exec',
                '--ignore-user-config', '--ignore-rules', '--ephemeral', '--skip-git-repo-check',
                '--sandbox', 'read-only', '--cd', scratch, '--json', '--model', protocol['model_requested'],
                '-c', 'model_reasoning_effort=' + json.dumps(protocol['reasoning_effort']),
                '-c', 'web_search="disabled"', '--output-schema', str(Path(scratch) / 'schema.json'),
                '-o', str(Path(scratch) / 'answer.json'), '-']
    require(command == expected, 'CLI command differs from fixed model/effort/tool-scope recipe')


def validate_call(receipt, batch, rater, items, audit, stdout_text, stderr_text, reservation):
    require(receipt['rater'] == rater and receipt['batch_id'] == batch['id'] and
            receipt['item_ids'] == batch['item_ids'], 'call identity mismatch')
    require(receipt['prompt_sha256'] == batch['prompts'][rater]['sha256'], 'call prompt mismatch')
    require(reservation.get('rater') == rater and reservation.get('batch_id') == batch['id'] and
            type(reservation.get('attempt')) is int and reservation['attempt'] == 1 and
            reservation.get('new_model_attempt') is True, 'reservation mismatch')
    require(receipt.get('stdout') == stdout_text and receipt.get('stderr') == stderr_text,
            'captured raw source mismatch')
    parsed, invalid_lines = [], 0
    for line in stdout_text.splitlines():
        try:
            parsed.append(json.loads(line))
        except json.JSONDecodeError:
            invalid_lines += 1
    require(receipt.get('events') == parsed, 'receipt event projection mismatch')
    require(all(type(e) is dict for e in parsed), 'CLI event must be an object')
    require(all('item' not in e or type(e['item']) is dict for e in parsed),
            'CLI event item must be an object')
    actions = [e for e in parsed if e.get('item', {}).get('type') not in (None, 'reasoning', 'agent_message')]
    require(receipt.get('tool_actions') == actions, 'tool action projection mismatch')
    messages = [e['item'].get('text') for e in parsed if e.get('type') == 'item.completed' and
                e.get('item', {}).get('type') == 'agent_message']
    if 'raw_output' in receipt:
        require(messages and json.loads(messages[-1]) == receipt['raw_output'],
                'last raw agent output differs from saved structured output')
    require(receipt.get('error') is None and type(receipt.get('returncode')) is int and
            receipt['returncode'] == 0, 'audit call invalid or nonzero')
    require(not actions and receipt.get('tool_actions') == [], 'tool action invalidates audit')
    require(invalid_lines == 0, 'valid audit call contains unparseable stdout lines')
    require(all(sum(e.get('type') == kind for e in parsed) == 1
                for kind in ('thread.started', 'turn.started', 'turn.completed')) and
            not any(e.get('type') in ('error', 'turn.failed') for e in parsed), 'CLI turn not complete')
    require(receipt.get('usage_events') == [e for e in parsed if e.get('type') == 'turn.completed'],
            'usage event projection mismatch')
    raw = receipt['raw_output']
    require(messages and json.loads(messages[-1]) == raw, 'last raw agent output differs from saved structured output')
    require(strict_source_json(messages[-1]) == raw,
            'strict captured final JSON differs from preserved output')
    validated = audit.validate_response(raw, items)
    require(receipt.get('output') == validated, 'validated output changed')
    require(receipt.get('resolved_evidence') == audit.resolved_evidence(raw, items), 'resolved source evidence changed')
    derived = [{'id': row['id'], 'status': audit.derived_contract_status(row)} for row in raw['items']]
    require(receipt.get('host_derived_original_full_contract') == derived, 'host-derived full-contract status changed')
    return {row['id']: {'validity': 'valid', 'host_original_full_contract': entry['status'],
                       'original_question_determinacy': row['original_question_determinacy'],
                       'reference_query_alignment': row['reference_query_alignment'],
                       'original_scored_field_coverage': row['original_scored_field_coverage'],
                       'native_output_support': row['native_output_support'],
                       'contract_signature': row['contract_signature']}
            for row, entry in zip(raw['items'], derived)}, invalid_lines


def validate_closed_index(closed, manifest_sha, code_sha, protocol_sha, expected_calls):
    """The index pins closure; independent validation still supplies each label."""
    for key, expected in (('audit_manifest_sha256', manifest_sha),
                          ('code_sha256', code_sha), ('protocol_sha256', protocol_sha)):
        require(closed.get(key) == expected, 'closed audit provenance changed: ' + key)
    require(closed.get('closed') is True, 'audit index is not closed')
    items = closed['calls']
    require(type(items) is list, 'closed audit calls must be a list')
    index = {row['call_id']: row for row in items}
    require(len(index) == len(items) and set(index) == expected_calls,
            'closed audit call index is duplicate, unexpected or incomplete')
    for row in items:
        if 'rater' in row or 'batch_id' in row:
            require(row.get('rater') in ('A', 'B') and type(row.get('batch_id')) is str and
                    row['call_id'] == row['rater'] + '_' + row['batch_id'],
                    'closed audit rater/batch identity contradicts call_id')
        require(row.get('valid_status') in ('VALID', 'INVALID'), 'closed audit status not final')
        require((row['valid_status'] == 'VALID' and row.get('error_category') is None) or
                (row['valid_status'] == 'INVALID' and type(row.get('error_category')) is str
                 and bool(row['error_category'])), 'closed audit error category contradicts status')
    return index


def verify_runtime_sources(receipt, files, pin):
    """Contradictions are global proof errors; absent setup capture earns no label."""
    def integral(condition, message):
        if not condition:
            raise IntegrityError(message)
    if receipt.get('error') is None and 'raw_output' in receipt:
        integral('output' in receipt and receipt['output'] == receipt['raw_output'],
                 'saved successful output differs from preserved raw_output')
    unavailable, texts = [], {}
    for name in ('stdout', 'stderr'):
        expected, path = pin[name + '_sha256'], files[name]
        if expected is None:
            integral(pin['valid_status'] == 'INVALID' and (receipt.get('error') is not None or
                     pin.get('closure_derived_technical_status') == 'INVALID'),
                     'missing runtime capture claimed by nonterminal-invalid receipt')
            integral(not path.exists() and name not in receipt,
                     'null runtime pin contradicts existing file or recorded text')
            texts[name] = None
            unavailable.append(name + '_file_not_created')
        else:
            pinned(path, expected)
            texts[name] = path.read_text()
        if name in receipt:
            integral(texts[name] is not None and receipt[name] == texts[name],
                     'recorded runtime text differs from captured file')
        else:
            unavailable.append(name + '_metadata_not_created')
    events = []
    for line in (texts['stdout'] or '').splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    if 'events' in receipt:
        integral(receipt['events'] == events, 'recorded events differ from captured stdout')
    else:
        unavailable.append('event_metadata_not_created')
    def event_item(e):
        value = e.get('item', {}) if type(e) is dict else {}
        return value if type(value) is dict else {}
    actions = [e for e in events if type(e) is dict and
               event_item(e).get('type') not in (None, 'reasoning', 'agent_message')]
    if 'tool_actions' in receipt:
        integral(receipt['tool_actions'] == actions, 'recorded tool actions differ from captured stdout')
    else:
        unavailable.append('tool_action_metadata_not_created')
    if 'raw_output' in receipt:
        messages = [event_item(e).get('text') for e in events if type(e) is dict and
                    e.get('type') == 'item.completed' and event_item(e).get('type') == 'agent_message']
        try:
            integral(bool(messages) and json.loads(messages[-1]) == receipt['raw_output'],
                     'preserved raw_output is not the final captured agent JSON')
        except (json.JSONDecodeError, TypeError) as exc:
            raise IntegrityError('preserved raw_output lacks captured final JSON') from exc
    if unavailable:
        integral(pin['valid_status'] == 'INVALID' and (receipt.get('error') is not None or
                 pin.get('closure_derived_technical_status') == 'INVALID'),
                 'unavailable runtime metadata claimed by nonterminal-invalid receipt')
    return {'binding_availability': 'UNAVAILABLE_BINDING' if unavailable else 'AVAILABLE',
            'unavailable_fields': unavailable}


def load_audit(audit_out, audit_protocol, audit_code, expected_manifest_sha, closed_pins, source_out, public):
    audit = module_from_path(audit_code, 'pinned_semantic_alignment_audit')
    pinned(audit_out / 'frozen_input_manifest.json', expected_manifest_sha)
    protocol, manifest = audit.verify_preparation(audit_out, audit_protocol)
    require(len(manifest['batches']) == 56 and manifest['planned_cli_invocations'] == 112 and
            manifest['raters'] == ['A', 'B'] and len(set(manifest['fixed_ids'])) == 560,
            'audit population or rater plan changed')
    expected_calls = {r + '_' + b['id'] for b in manifest['batches'] for r in ('A', 'B')}
    pins = validate_closed_index(closed_pins, expected_manifest_sha, sha(audit_code), sha(audit_protocol), expected_calls)
    cq = public / 'release_package/cqs/spectra_cq_v2.0'
    paths = {'benchmark': cq / 'benchmark.jsonl', 'contract': cq / 'answer_contract.jsonl',
             'scorer': public / 'paper/baseline/score.py', 'executor': public / 'paper/baseline/bench_common.py'}
    for key, path in paths.items():
        pinned(path, manifest['original_input_sha256'][key])
    benchmark, contracts = audit.read_lines(paths['benchmark']), audit.read_lines(paths['contract'])
    fixture = read_json(audit_out / 'fixture_items.json')['items']
    pointers = read_json(audit_out / 'source_pointers.json')['items']
    require(len(pointers) == 560 and {p['id'] for p in pointers} == set(manifest['fixed_ids']), 'source pointers IDs changed')
    pointer_index = {p['id']: p for p in pointers}
    native_pins = {p['id']: p['sha256'] for p in manifest['native_receipts_sha256']['receipt_sha256']}
    require(len(native_pins) == 560 and set(native_pins) == set(manifest['fixed_ids']), 'native receipt IDs changed')
    native = {}
    for item in fixture:
        k = item['id']; path = source_out / 'receipts' / (k + '.json')
        pinned(path, native_pins[k]); receipt = read_json(path); native[k] = receipt
        require(audit.project_item(benchmark[k][1], contracts[k][1], receipt) == item,
                'audit source fixture differs from exact original source projection')
        p = pointer_index[k]
        require(p['benchmark_line'] == benchmark[k][0] and p['contract_line'] == contracts[k][0] and
                p['question_utf8_sha256'] == audit.digest(item['question']) and
                p['reference_query_utf8_sha256'] == audit.digest(item['reference_query']) and
                p['fixture_sha256'] == audit.digest(audit.canonical(item)), 'raw source pointer mismatch')
    labels = {k: {r: {'validity': 'pending', 'host_original_full_contract': None} for r in ('A', 'B')}
              for k in manifest['fixed_ids']}
    blockers, checked, invalid_calls, invalid_stdout_lines = [], [], [], 0
    actual_dirs = {p.name for p in (audit_out / 'calls').iterdir() if p.is_dir()} if (audit_out / 'calls').is_dir() else set()
    require(actual_dirs <= expected_calls, 'unexpected audit call directory')
    # Receipt/reservation closure is checked for all112 before any audit
    # output JSON is read. Terminal INVALID may lack original runtime capture.
    for call_id in sorted(expected_calls):
        directory = audit_out / 'calls' / call_id
        if not all((directory / name).is_file() for name in ('receipt.json', 'reservation.json')):
            blockers.append({'call_id': call_id, 'reason': 'pending_or_missing_required_call_artifact'})
    if blockers:
        return {'manifest': manifest, 'labels': labels, 'native': native, 'blockers': blockers,
                'checked_calls': [], 'invalid_calls': [], 'valid_calls_n': 0,
                'invalid_raw_stdout_lines_skipped_like_audit': 0}
    for batch in manifest['batches']:
        items = read_json(audit_out / 'batches' / batch['id'] / 'items.json')['items']
        for rater in ('A', 'B'):
            call_id = rater + '_' + batch['id']; directory = audit_out / 'calls' / call_id
            files = {'receipt': directory / 'receipt.json', 'reservation': directory / 'reservation.json',
                     'stdout': directory / 'stdout.jsonl', 'stderr': directory / 'stderr.txt'}
            if call_id not in pins or not all(files[key].is_file() for key in ('receipt', 'reservation')):
                blockers.append({'call_id': call_id, 'reason': 'pending_or_unpinned_call'})
                continue
            # A byte/provenance mismatch is an integrity failure, not an
            # operationally invalid audit that can simply be excluded.
            for key in ('receipt', 'reservation'):
                path = files[key]
                pinned(path, pins[call_id][key + '_sha256'])
            receipt = read_json(files['receipt'])
            runtime = verify_runtime_sources(receipt, files, pins[call_id])
            checked.append({'call_id': call_id, **runtime, **{key + '_sha256': pins[call_id][key + '_sha256']
                                                             for key in files}})
            strict_unavailable = False
            try:
                require(runtime['binding_availability'] == 'AVAILABLE', 'terminal invalid setup has unavailable runtime binding')
                require(receipt.get('model_requested') == protocol['model_requested'], 'requested audit model changed')
                reservation = read_json(files['reservation'])
                validate_command(receipt.get('command'), reservation, protocol)
                valid, bad_lines = validate_call(receipt, batch, rater, items, audit,
                    files['stdout'].read_text(), files['stderr'].read_text(), reservation)
                invalid_stdout_lines += bad_lines
                for k, label in valid.items():
                    labels[k][rater] = label
            except (ValueError, KeyError, TypeError, IndexError) as exc:
                strict_unavailable = isinstance(exc, ScientificEvidenceUnavailable)
                invalid_calls.append({'call_id': call_id, 'reason': type(exc).__name__,
                                      'validation_failure': str(exc).split(':', 1)[0],
                                      'preserved_terminal_valid_status': pins[call_id]['valid_status'],
                                      'scientific_evidence_availability': 'UNAVAILABLE' if strict_unavailable else 'INVALID'})
                for k in batch['item_ids']:
                    labels[k][rater] = {'validity': 'invalid', 'host_original_full_contract': None,
                                       'retained_receipt_sha256': sha(files['receipt']),
                                       'preserved_terminal_valid_status': pins[call_id]['valid_status'],
                                       'scientific_evidence_availability': 'UNAVAILABLE' if strict_unavailable else 'INVALID'}
            independent_status = labels[batch['item_ids'][0]][rater]['validity']
            require(closure_status_agrees(independent_status, pins[call_id]['valid_status'], strict_unavailable),
                    'independent audit validity differs from pinned closure index')
    return {'manifest': manifest, 'labels': labels, 'native': native, 'blockers': blockers,
            'checked_calls': checked, 'invalid_calls': invalid_calls,
            'valid_calls_n': len(checked) - len(invalid_calls),
            'invalid_raw_stdout_lines_skipped_like_audit': invalid_stdout_lines}


def closure_ready(checked_calls, pending_calls, expected_calls_n=112):
    """Closed invalid receipts count as attempts, never as valid judgments."""
    return not pending_calls and len(checked_calls) == expected_calls_n


def frozen_cohort(labels, native):
    require(set(labels) == set(native), 'native/audit identity mismatch')
    dispositions, selected = [], []
    for k in sorted(labels):
        pair = labels[k]; e = native[k]['execution']
        ready = (e['status'] == 'OK' and e['execution_summary_complete'] is True and
                 e['full_json_rows_available'] is True and e['truncated'] is False and
                 type(e['unsupported_json_rows']) is int and e['unsupported_json_rows'] == 0)
        agreement = all(pair[r]['validity'] == 'valid' and
                        pair[r]['host_original_full_contract'] == 'aligned' for r in ('A', 'B'))
        include = agreement and ready
        if include:
            selected.append(k)
        dispositions.append({'id': k, 'A': pair['A'], 'B': pair['B'],
                             'native_status': e['status'], 'native_complete': ready,
                             'both_host_full_contract_aligned': agreement, 'selected': include})
    return selected, dispositions


def mean(values):
    return sum(values) / len(values) if values else None


def paired_bootstrap(vectors):
    """One Random(0) randrange draw per task shared by every fixed contrast."""
    if not vectors:
        return {}
    n = len(next(iter(vectors.values())))
    require(n > 0 and all(len(v) == n for v in vectors.values()), 'bootstrap task vectors misaligned')
    rng, boot = random.Random(SEED), {k: [] for k in vectors}
    for _ in range(N_BOOT):
        draw = [rng.randrange(n) for _ in range(n)]
        for k, v in vectors.items():
            boot[k].append(sum(map(v.__getitem__, draw)) / n)
    return {k: {'mean': mean(vectors[k]), 'ci95': [sorted(v)[250], sorted(v)[9749]]} for k, v in boot.items()}


def read_predictions(path):
    opener = gzip.open if path.suffix == '.gz' else open
    predictions, invalid, duplicates = {}, 0, 0
    with opener(path, 'rt') as stream:
        for line in stream:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError:
                invalid += 1
                continue
            require(type(row) is dict, 'retained prediction row must be object')
            cid = row.get('id')
            if cid is not None:
                if cid in predictions:
                    duplicates += 1
                else:
                    predictions[cid] = row.get('predicted_values')
    return predictions, {'invalid_JSON_lines_skipped': invalid, 'duplicate_ids_ignored': duplicates}


def score_fixed_cohort(cohort, key_rows, run_predictions, score_row, norm, wg, tracks):
    """Legacy value-set scoring only, with identical V1/V2 denominators."""
    keys = {label: {k: {norm(v) for v in (g.get('gold_values_released_query', g['gold_values'])
                  if label == 'released_V1' else g['gold_values'])} for k, g in key_rows.items()}
            for label in ('released_V1', 'default_Core_V2')}
    per_task, aggregate = {}, {}
    for label, gold in keys.items():
        per_task[label], aggregate[label] = {}, {}
        for (arm, model), predictions in sorted(run_predictions.items()):
            scores = {k: score_row(predictions[k], gold[k]) if k in predictions else dict.fromkeys(METRICS, 0.0)
                      for k in cohort}
            name = arm + '/' + model
            per_task[label][name] = scores
            def summary(ids):
                return {'n': len(ids), 'attempted_n': sum(k in predictions for k in ids),
                        'missing_n': sum(k not in predictions for k in ids),
                        **{m: mean([scores[k][m] for k in ids]) for m in METRICS}}
            aggregate[label][name] = {**summary(cohort),
                'by_wg': {group: summary([k for k in cohort if wg[k] == group]) for group in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5')},
                'by_original_track': {group: summary([k for k in cohort if tracks[k] == group])
                                      for group in ('lookup', 'aggregation', 'relational', 'multihop')}}
    return per_task, aggregate


def build_contrasts(per_task, cohort, models):
    vectors = {}
    for key_label, runs in per_task.items():
        for metric in ('f1', 'exact'):
            for text in ('rag', 'closed_book'):
                differences = []
                for model in models:
                    v = [runs['kg_grounded/' + model][k][metric] - runs[text + '/' + model][k][metric] for k in cohort]
                    vectors[key_label + '/' + metric + '/kg_minus_' + text + '/' + model] = v
                    differences.append(v)
                vectors[key_label + '/' + metric + '/kg_minus_' + text + '/nine_model_task_mean'] = [
                    mean([v[j] for v in differences]) for j in range(len(cohort))]
    return vectors


def exclusive_json(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def authorize(args, protocol):
    require(args.authorization is not None and args.closed_audit_pins is not None,
            'separate root authorization and closed audit file pins are required before labels or predictions are read')
    auth = read_json(args.authorization)
    expected = {'authorization': 'root_reviewed_original_retained_diagnostic_v2',
                'analysis_code_sha256': sha(__file__), 'analysis_protocol_sha256': sha(args.protocol),
                'baseline_inventory_sha256': protocol['prepared_files']['baseline_inventory_sha256'],
                'audit_protocol_sha256': protocol['final_audit_pins']['protocol_sha256'],
                'audit_code_sha256': protocol['final_audit_pins']['code_sha256'],
                'audit_manifest_sha256': protocol['final_audit_pins']['manifest_sha256'],
                'closed_audit_receipts_manifest_sha256': sha(args.closed_audit_pins),
                'model_calls': 0, 'database_calls': 0}
    for key, value in expected.items():
        require(type(auth.get(key)) is type(value) and auth[key] == value, 'analysis authorization mismatch: ' + key)
    return auth


def run(args):
    protocol = read_json(args.protocol)
    require(protocol['analysis_code_sha256'] == sha(__file__), 'analysis code changed after protocol freeze')
    authorize(args, protocol)  # This gate runs before opening any actual audit labels or predictions.
    preparation_pins = [(ROOT / protocol['prepared_files']['source_independent_check'],
                         protocol['prepared_files']['source_independent_check_sha256']),
                        (HERE / 'test_analyze_original_aligned_retained_v1.py', protocol['analysis_test_sha256']),
                        (args.protocol, sha(args.protocol)), (args.authorization, sha(args.authorization)),
                        (args.closed_audit_pins, sha(args.closed_audit_pins))]
    for path, expected in preparation_pins:
        pinned(path, expected)
    require(not args.out.exists() and not args.cohort_out.exists(), 'refusing to overwrite diagnostic outputs')
    inventory_path = ROOT / protocol['prepared_files']['baseline_inventory']
    pinned(inventory_path, protocol['prepared_files']['baseline_inventory_sha256']); inventory = read_json(inventory_path)
    pinned(HERE / 'prepare_original_aligned_retained_diagnostic_v1.py', inventory['code_sha256'])
    public = args.public_directory
    for row in inventory['public_source_and_legacy_code_pins'] + inventory['files']:
        pinned(safe_child(public, row['relative_public_path']), row['sha256'])
    for name, expected in inventory['source_observation_pins'].items():
        pinned(args.source_out / name, expected)
    final = protocol['final_audit_pins']; audit_code = HERE / 'semantic_alignment_audit_v1.py'
    audit_protocol = HERE / 'semantic_alignment_audit_protocol_v1.json'
    pinned(audit_code, final['code_sha256']); pinned(audit_protocol, final['protocol_sha256'])
    audited = load_audit(args.audit_out, audit_protocol, audit_code, final['manifest_sha256'],
                        read_json(args.closed_audit_pins), args.source_out, public)
    cohort, dispositions = frozen_cohort(audited['labels'], audited['native'])
    report = {'kind': 'retained original-question answer-column diagnostic; source-aligned AI-agreement cohort',
              'analysis_code_sha256': sha(__file__), 'analysis_protocol_sha256': sha(args.protocol),
              'baseline_inventory_sha256': sha(inventory_path), 'final_audit_pins': final,
              'closed_audit_file_index_sha256': sha(args.closed_audit_pins),
              'original_Core_n': 560, 'audit_checked_calls_n': len(audited['checked_calls']),
              'audit_valid_calls_n': audited['valid_calls_n'],
              'audit_invalid_closed_calls': audited['invalid_calls'],
              'audit_file_checks': audited['checked_calls'], 'all560_dispositions': dispositions,
              'fixed_cohort_ids': cohort, 'fixed_cohort_n': len(cohort),
              'fixed_cohort_ids_sha256': PREP.text_sha('\n'.join(cohort) + '\n'),
              'audit_blockers': audited['blockers'], 'model_scores_computed': False,
              'source_V2_mismatches_affect_cohort_membership': False,
              'limits': protocol['report_language_limits'],
              'domain_expert_validation_n': 0, 'canonical_gold_certification': False,
              'new_model_calls': 0, 'database_calls': 0, 'original_files_modified': False}
    if not closure_ready(audited['checked_calls'], audited['blockers']):
        report['status'] = 'BLOCKED_PENDING_AUDIT_CLOSURE'
        exclusive_json(args.out, report)
        return 2
    baseline = public / 'paper/baseline'; cq = public / 'release_package/cqs/spectra_cq_v2.0'
    key_rows = {g['id']: g for g in PREP.read_jsonl(cq / 'core_answer_gold.jsonl')}
    norm, score_row = legacy_scorer(baseline)
    comparison = PREP.source_key_comparison(key_rows, audited['native'], args.source_out, norm)
    plan = PREP.diagnostic_key_plan(comparison['items'], cohort)
    report['primary_and_sensitivity_key_plan'] = plan
    report['source_key_comparison_all560'] = comparison
    if not plan['primary_source_consistency_passed']:
        report['status'] = 'BLOCKED_SOURCE_V1_MISMATCH'
        exclusive_json(args.out, report)
        return 2
    snapshot = {'kind': 'immutable cohort snapshot before retained model performance join',
                'analysis_protocol_sha256': sha(args.protocol), 'audit_manifest_sha256': final['manifest_sha256'],
                'closed_audit_file_index_sha256': sha(args.closed_audit_pins),
                'baseline_inventory_sha256': sha(inventory_path), 'cohort_ids': cohort,
                'cohort_ids_sha256': report['fixed_cohort_ids_sha256'], 'primary_key': 'released/V1',
                'sensitivity_key': 'default Core/V2, identical entire cohort',
                'membership_uses_model_predictions_or_gold_key_mismatches': False}
    exclusive_json(args.cohort_out, snapshot)
    report['cohort_snapshot_sha256'] = sha(args.cohort_out)
    if not cohort:
        report.update(status='CLOSED_EMPTY_COHORT', results=None)
        exclusive_json(args.out, report)
        return 0
    predictions, parse_inventory = {}, []
    for row in inventory['files']:
        path = safe_child(public, row['relative_public_path'])
        values, parsed = read_predictions(path)
        require(parsed['invalid_JSON_lines_skipped'] == row['invalid_JSON_lines_skipped'] and
                parsed['duplicate_ids_ignored'] == row['duplicate_ids_ignored'], 'legacy prediction parser inventory changed')
        predictions[(row['condition'], row['model_slug'])] = values
        parse_inventory.append({'condition': row['condition'], 'model': row['model_slug'], **parsed})
    wg = {k: g['wg'] for k, g in key_rows.items()}; tracks = read_json(cq / 'splits/track_assignment.json')
    per_task, aggregate = score_fixed_cohort(cohort, key_rows, predictions, score_row, norm, wg, tracks)
    contrasts = build_contrasts(per_task, cohort, sorted({r['model_slug'] for r in inventory['files']}))
    report.update(status='COMPLETE', model_scores_computed=True, primary_key='released_V1',
                  whole_identical_cohort_sensitivity_key='default_Core_V2', per_run=aggregate,
                  per_task_scores=per_task, retained_parser_inventory=parse_inventory,
                  paired_differences=paired_bootstrap(contrasts), bootstrap={'n': N_BOOT, 'seed': SEED,
                  'unit': 'task shared across27 runs and both keys', 'percentile_zero_based_indices': [250, 9749]})
    report['pooled_by_condition'] = {label: {arm: {metric: mean([r[metric] for name, r in runs.items()
        if name.startswith(arm + '/')]) for metric in METRICS} for arm in PREP.ARMS} for label, runs in aggregate.items()}
    # Recheck immutable predictions and source keys after arithmetic.
    for row in inventory['files'] + inventory['public_source_and_legacy_code_pins']:
        pinned(safe_child(public, row['relative_public_path']), row['sha256'])
    pinned(args.audit_out / 'frozen_input_manifest.json', final['manifest_sha256'])
    pinned(audit_code, final['code_sha256']); pinned(audit_protocol, final['protocol_sha256'])
    module_from_path(audit_code, 'post_arithmetic_audit_preparation_check').verify_preparation(args.audit_out, audit_protocol)
    for path, expected in preparation_pins + [(inventory_path, protocol['prepared_files']['baseline_inventory_sha256'])]:
        pinned(path, expected)
    for name, expected in inventory['source_observation_pins'].items():
        pinned(args.source_out / name, expected)
    for call in audited['checked_calls']:
        directory = args.audit_out / 'calls' / call['call_id']
        for key, name in (('receipt', 'receipt.json'), ('reservation', 'reservation.json'),
                          ('stdout', 'stdout.jsonl'), ('stderr', 'stderr.txt')):
            expected = call[key + '_sha256']
            if expected is None:
                require(not (directory / name).exists(), 'previously absent runtime capture appeared after arithmetic')
            else:
                pinned(directory / name, expected)
    for k, receipt in audited['native'].items():
        pinned(args.source_out / 'receipts' / (k + '.json'), next(
            row['sha256'] for row in audited['manifest']['native_receipts_sha256']['receipt_sha256'] if row['id'] == k))
        pinned(args.source_out / receipt['execution']['rows_file'], receipt['execution']['rows_file_sha256'])
    report['all_input_bytes_unchanged_after_arithmetic'] = True
    exclusive_json(args.out, report)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--protocol', type=Path, default=ANALYSIS / 'original_aligned_retained_diagnostic_protocol_v2.json')
    parser.add_argument('--authorization', type=Path)
    parser.add_argument('--closed-audit-pins', type=Path)
    parser.add_argument('--public-directory', type=Path, default=ROOT.parent / 'spectra-public/spec-trace')
    parser.add_argument('--audit-out', type=Path, default=AUDIT_OUT)
    parser.add_argument('--source-out', type=Path, default=SOURCE_OUT)
    parser.add_argument('--out', type=Path, default=ANALYSIS / 'original_aligned_retained_diagnostic_report_v1.json')
    parser.add_argument('--cohort-out', type=Path, default=ANALYSIS / 'original_aligned_retained_cohort_v1.json')
    args = parser.parse_args()
    raise SystemExit(run(args))


if __name__ == '__main__':
    main()
