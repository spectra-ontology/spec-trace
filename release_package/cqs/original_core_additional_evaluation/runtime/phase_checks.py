#!/usr/bin/env python3
"""Replay retained predictions offline; never call models or execute answer queries.

The published scorer is invoked on freshly extracted, pinned inputs.  Retained
execution statuses independently gate failures to zero, including empty gold.
Hash checks establish artifact integrity, not semantic or expert validation.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import random
import shutil
import subprocess
import sys
import tarfile
import tempfile

sys.dont_write_bytecode = True
METHODS = ('text2cypher', 'text2sql', 'single_retrieval', 'iterative_retrieval')
PHASES = {
    'original_attempt': (350, 'main350_bundle'),
    'transport_recovered': (350, 'main350_bundle'),
    'additional_original_attempt': (21, 'additional21_bundle'),
    'additional_originals_recovered': (21, 'additional21_bundle'),
    'admitted_union': (371, None),
}
CONTENT = {'OK', 'PARTIAL'}
FINANCE_KEYS = {'limit_usd', 'spend_usd', 'balance_usd', 'balance', 'credits',
                'credits_remaining', 'remaining_credits', 'total_credits', 'total_usage',
                'limit_remaining', 'remaining_usd', 'resets_at', 'reset_at',
                'key_limit_usd', 'key_spend_usd', 'account_balance_usd', 'account_usage_usd'}
REDACTED = '[REDACTED_PRIVATE_ACCOUNT_FINANCE]'


def fail(message):
    raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def pairs_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail('duplicate JSON key: ' + str(key))
        result[key] = value
    return result


def decode(text):
    return json.loads(text, object_pairs_hook=pairs_no_duplicates,
                      parse_constant=lambda value: fail('nonfinite JSON number: ' + value))


def load(path):
    return decode(Path(path).read_text(encoding='utf-8'))


def rows(path):
    result = {}
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        value = decode(line)
        identity = value['id']
        if identity in result:
            fail('duplicate ID in ' + str(path) + ': ' + identity)
        result[identity] = value
    return result


def safe_relative(name):
    if not isinstance(name, str) or not name or '\\' in name or '\x00' in name:
        fail('invalid relative path')
    parts = name.split('/')
    if name.startswith('/') or any(p in ('', '.', '..') for p in parts):
        fail('unsafe relative path: ' + name)
    return PurePosixPath(name)


def under(root, name):
    relative = safe_relative(name)
    result = root.joinpath(*relative.parts)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            fail('symlink forbidden: ' + str(current))
    if not result.resolve().is_relative_to(root.resolve()):
        fail('path escapes root')
    return result


def check_pins(root, manifest_name, exact=False):
    manifest = load(root / manifest_name)
    pins = manifest['files']
    if not isinstance(pins, dict) or not pins:
        fail('empty or malformed hash manifest')
    if 'file_n' in manifest and manifest['file_n'] != len(pins):
        fail('manifest file_n mismatch')
    for name, expected in pins.items():
        path = under(root, name)
        if not path.is_file() or sha(path) != expected:
            fail('manifest hash mismatch: ' + name)
    if exact:
        actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
        if actual != set(pins) | {manifest_name}:
            fail('unlisted or missing evidence files')
    return manifest


def extract_checked(archive, inventory_path, destination):
    inventory = load(inventory_path)
    if sha(archive) != inventory['archive_sha256']:
        fail('archive SHA mismatch: ' + archive.name)
    if archive.stat().st_size != inventory['archive_bytes']:
        fail('archive byte-count mismatch')
    expected = inventory['files']
    if inventory['file_n'] != len(expected):
        fail('archive inventory denominator mismatch')
    for name in expected:
        safe_relative(name)
    actual = {}
    roots = set()
    seen = set()
    with tarfile.open(archive, 'r:gz') as source:
        for member in source:
            relative = safe_relative(member.name)
            if member.name in seen:
                fail('duplicate archive member: ' + member.name)
            seen.add(member.name)
            if not member.isfile():
                fail('nonregular archive member forbidden: ' + member.name)
            if len(relative.parts) < 2:
                fail('archive requires one enclosing directory')
            roots.add(relative.parts[0])
            name = PurePosixPath(*relative.parts[1:]).as_posix()
            if name in actual or name not in expected:
                fail('unexpected or duplicate archive file: ' + name)
            target = under(destination, member.name)
            target.parent.mkdir(parents=True, exist_ok=True)
            stream = source.extractfile(member)
            if stream is None:
                fail('archive file has no readable stream')
            h = hashlib.sha256()
            count = 0
            with stream, target.open('xb') as output:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    h.update(chunk)
                    count += len(chunk)
                    output.write(chunk)
            if count != member.size or h.hexdigest() != expected[name]:
                fail('contained-file hash mismatch: ' + name)
            actual[name] = h.hexdigest()
    if len(roots) != 1 or actual != expected:
        fail('archive inventory does not exactly enumerate all contained files')
    # Original hashes are retained provenance when public account-finance fields
    # were redacted.  They cannot be independently rehashed from redacted bytes.
    original = inventory.get('private_original_files', inventory.get('original_files'))
    if original is not None and set(original) != set(expected):
        fail('original/published archive inventories differ in membership')
    return destination / next(iter(roots)), {
        'archive_sha256': sha(archive), 'file_n': len(actual),
        'original_bytes_independently_verified': original is None or original == expected,
        'redaction_provenance_present': original is not None and original != expected,
    }


def pointer_value(value, pointer):
    if not isinstance(pointer, str) or not pointer.startswith('/'):
        fail('invalid redaction JSON pointer')
    for raw in pointer[1:].split('/'):
        key = raw.replace('~1', '/').replace('~0', '~')
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def verify_redactions(evidence, extracted):
    report = load(evidence / 'public_redactions.json')
    occurrences = report['files']
    if (report.get('private_originals_preserved') is not True
            or report.get('model_payloads_and_model_answer_content_redacted') is not False
            or report.get('redacted_file_occurrences') != len(occurrences)):
        fail('inconsistent public-redaction scope metadata')
    by_path = {}
    for record in occurrences:
        published = record['published_path']
        if published in by_path:
            fail('duplicate published-redaction path')
        by_path[published] = record
        if '::' in published:
            archive_name, member = published.split('::', 1)
            safe_relative(archive_name)
            member_parts = safe_relative(member).parts
            if archive_name not in extracted or len(member_parts) < 2:
                fail('redaction refers to unretained archive')
            path = under(extracted[archive_name], PurePosixPath(*member_parts[1:]).as_posix())
        else:
            path = under(evidence, published)
        if not path.is_file() or sha(path) != record['published_sha256']:
            fail('redaction published-byte pin mismatch')
        if record['private_original_sha256'] == record['published_sha256'] or not record['masked_locations']:
            fail('redaction must identify a changed source file and its locations')
        for location in record['masked_locations']:
            if 'line' in location:
                lines = path.read_text().splitlines()
                value = decode(lines[location['line'] - 1])
                location = location['location']
            else:
                value = load(path)
            pointer = location['json_pointer']
            reason = location['reason']
            masked = pointer_value(value, pointer)
            if reason == 'provider_account_key_finance_error_metadata':
                bits = pointer.split('/')
                if len(bits) < 4 or bits[-3:-1] != ['error', 'metadata'] or bits[-1] not in FINANCE_KEYS or masked != REDACTED:
                    fail('redaction exceeds account-finance metadata scope')
            elif reason == 'provider_account_key_finance_error_message':
                if not pointer.endswith('/error/message') or masked not in {
                        'Provider rejected the request before generation because the API key spend limit was reached.',
                        'Provider rejected the request before generation because of an in-flight budget limit.',
                        'Provider error message with private account financial details redacted.'}:
                    fail('redaction exceeds account-finance error-message scope')
            elif reason == 'private_provider_account_query':
                if pointer.split('/')[-1] not in {'data', 'response_data', 'account', 'key_info', 'credits_info'} or masked != REDACTED:
                    fail('redaction exceeds explicit account-query scope')
            else:
                fail('unknown redaction reason')
            if any('/' + key + '/' in pointer for key in ('records', 'choices', 'messages')):
                fail('prediction or model request/answer content redacted')
    changed_members = set()
    for archive_name, source in extracted.items():
        inventory = load(evidence / (archive_name + '.inventory.json'))
        original = inventory.get('private_original_files', inventory.get('original_files'))
        if original is None:
            continue
        for name, published_sha in inventory['files'].items():
            if original[name] == published_sha:
                continue
            published_path = archive_name + '::' + source.name + '/' + name
            if published_path not in by_path:
                fail('changed archive member has no explicit redaction provenance')
            record = by_path[published_path]
            if record['private_original_sha256'] != original[name] or record['published_sha256'] != published_sha:
                fail('archive original/public hashes disagree with redaction provenance')
            changed_members.add(published_path)
    if any('::' in name and name not in changed_members for name in by_path):
        fail('unmatched archive redaction record')
    return {'redacted_file_occurrences': len(occurrences),
            'changed_archive_members': len(changed_members),
            'public_bytes_verified': True,
            'private_original_bytes_independently_rehashed': False}


def equal(actual, expected, where):
    if isinstance(actual, dict) and isinstance(expected, dict):
        if set(actual) != set(expected):
            fail('object keys differ at ' + where)
        for key in actual:
            equal(actual[key], expected[key], where + '/' + str(key))
    elif isinstance(actual, list) and isinstance(expected, list):
        if len(actual) != len(expected):
            fail('array length differs at ' + where)
        for index, (left, right) in enumerate(zip(actual, expected)):
            equal(left, right, where + '/' + str(index))
    elif (isinstance(actual, (int, float)) and not isinstance(actual, bool)
          and isinstance(expected, (int, float)) and not isinstance(expected, bool)):
        if not math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12):
            fail('numeric replay mismatch at ' + where)
    elif type(actual) is not type(expected) or actual != expected:
        fail('replay mismatch at ' + where)


def summary(records):
    n = len(records)
    if n == 0:
        return {'n': 0}
    status_counts = Counter(r['execution_status'] for r in records)
    exact_n = sum(r['exact'] for r in records)
    return {
        'n': n,
        'requested_complete_record_macro_f1': sum(r['f1'] for r in records) / n,
        'exact_output_rate': exact_n / n,
        'exact_outputs': exact_n,
        'execution_status_counts': dict(status_counts),
        'failed_n': sum(status_counts[k] for k in status_counts if k not in CONTENT),
        'self_reported_partial_n': status_counts.get('PARTIAL', 0),
        'matched_requested_records': sum(r['matched_records'] for r in records),
        'gold_answer_records': sum(r['gold_records'] for r in records),
        'predicted_records': sum(r['predicted_records'] for r in records),
    }


def score(bundle, tasks_path, gold_path, predictions_path):
    command = [sys.executable, '-B', '-S', str(bundle / 'score_predictions.py'),
               '--tasks', str(tasks_path), '--gold', str(gold_path),
               '--predictions', str(predictions_path)]
    result = subprocess.run(command, cwd=bundle, text=True, capture_output=True,
                            check=False)
    if result.returncode != 0:
        fail('published scorer rejected retained predictions: ' + result.stderr[-1500:])
    return decode(result.stdout)


def replay_phase(label, folder, inputs, scorer_bundle, archived_run=None):
    expected_n = PHASES[label][0]
    tasks = rows(inputs / 'tasks.jsonl')
    gold = rows(inputs / 'reference_gold.jsonl')
    if len(tasks) != expected_n or set(tasks) != set(gold):
        fail(label + ': wrong task/gold denominator')
    public_tasks = rows(scorer_bundle / 'tasks.jsonl')
    public_gold = rows(scorer_bundle / 'reference_gold.jsonl')
    for identity, task in tasks.items():
        equal(task, public_tasks[identity], label + '/published-task/' + identity)
        equal(gold[identity], public_gold[identity], label + '/published-gold/' + identity)
    protocol = load(folder / 'protocol.json')
    for key, path in [('tasks_sha256', inputs / 'tasks.jsonl'),
                      ('gold_sha256', inputs / 'reference_gold.jsonl')]:
        if protocol.get(key) != sha(path):
            fail(label + ': protocol input pin mismatch: ' + key)
    if protocol.get('admitted_n') != expected_n:
        fail(label + ': protocol denominator mismatch')
    for key, filename in [('scorer_sha256', 'score_predictions.py'),
                          ('original_scorer_sha256', 'original_scorer.py'),
                          ('typed_scorer_sha256', 'scorer.py'),
                          ('typed_kernel_sha256', 'typed_values.py')]:
        if key not in protocol and label == 'admitted_union':
            continue
        if protocol.get(key) != sha(scorer_bundle / filename):
            fail(label + ': retained scoring implementation pin mismatch: ' + key)
    if protocol.get('cohort_ids') is not None:
        if len(protocol['cohort_ids']) != expected_n or set(protocol['cohort_ids']) != set(tasks):
            fail(label + ': protocol cohort IDs mismatch')
    completion = load(folder / 'generation_complete.json')
    if (completion.get('completed_method_items') != expected_n * 4
            or completion.get('required') != expected_n * 4):
        fail(label + ': incomplete method/item denominator')
    analysis = load(folder / 'analysis.json')
    if analysis.get('admitted_n') != expected_n:
        fail(label + ': analysis denominator mismatch')
    if set(analysis['tables']) != set(METHODS):
        fail(label + ': analysis lacks exact four-arm inventory')
    method_results = {}
    per_method = {}
    for method in METHODS:
        directory = folder / method
        predictions_path = directory / 'predictions.jsonl'
        statuses_path = directory / 'statuses.jsonl'
        predictions, statuses = rows(predictions_path), rows(statuses_path)
        if set(predictions) != set(tasks) or set(statuses) != set(tasks):
            fail(label + '/' + method + ': missing or extra IDs')
        for identity, task in tasks.items():
            prediction, status = predictions[identity], statuses[identity]
            if (prediction['repair_sha256'] != task['repair_sha256']
                    or status['repair_sha256'] != task['repair_sha256']):
                fail(label + '/' + method + ': stale repair SHA')
            if not isinstance(prediction['records'], list) or not isinstance(status['status'], str):
                fail('malformed prediction/status')
            if archived_run is not None:
                artifact = load(under(archived_run, status['artifact']))
                if (artifact['id'] != identity or artifact['repair_sha256'] != task['repair_sha256']
                        or artifact['status'].upper() != status['status']):
                    fail(label + ': status does not match retained execution artifact')
                equal(artifact['records'], prediction['records'], label + '/artifact-records/' + identity)
        raw = score(scorer_bundle, inputs / 'tasks.jsonl', inputs / 'reference_gold.jsonl', predictions_path)
        equal(raw, load(directory / 'raw_scores.json'), label + '/' + method + '/raw_scores')
        computed = {}
        for outcome in raw['outcomes']:
            result = dict(outcome)
            status = statuses[result['id']]['status']
            result['execution_status'] = status
            # A parsed partial empty answer cannot establish a true empty-gold
            # success.  Every other execution failure/abstention is also zero.
            allowed = status in CONTENT and not (status == 'PARTIAL' and result['gold_records'] == 0)
            result['failure_gated'] = not allowed
            if not allowed:
                result.update(precision=0.0, recall=0.0, f1=0.0, exact=False,
                              matched_records=0, raw_scorer_exact=outcome['exact'])
            computed[result['id']] = result
        saved = load(directory / 'failure_gated_scores.json')
        if not isinstance(saved, list) or len(saved) != expected_n:
            fail(label + ': missing complete gated score denominator')
        saved_by_id = {}
        for value in saved:
            if value['id'] in saved_by_id:
                fail('duplicate gated-score ID')
            saved_by_id[value['id']] = value
        equal(computed, saved_by_id, label + '/' + method + '/gated_scores')
        partitions = defaultdict(list)
        for identity, result in computed.items():
            task = tasks[identity]
            partitions['WG:' + identity.split('_')[0]].append(result)
            partitions['phase:' + identity.split('_')[1]].append(result)
            partitions['collection:' + task['collection']['kind']].append(result)
            partitions['asked_fields:' + ('multiple' if len(task['required_fields']) > 1 else 'single')].append(result)
            types = [f['type'] for f in task['required_fields']]
            if task['collection']['kind'] == 'top_k_boundary_ties':
                shape = 'ranked'
            elif types == ['boolean']:
                shape = 'boolean'
            elif len(types) == 1 and types[0] in {'integer', 'number'}:
                shape = 'scalar_numeric'
            elif any(t in {'integer', 'number'} for t in types):
                shape = 'grouped_numeric'
            else:
                shape = 'enumeration'
            partitions['contract_output_type:' + shape].append(result)
        replayed_table = {
            'overall': summary(list(computed.values())),
            'strata': {key: summary(value) for key, value in partitions.items()},
            'prediction_sha256': sha(predictions_path), 'statuses_sha256': sha(statuses_path),
        }
        equal(replayed_table, analysis['tables'][method], label + '/' + method + '/analysis')
        method_results[method] = computed
        per_method[method] = replayed_table['overall']
    if len(analysis.get('paired', [])) != 12:
        fail(label + ': incomplete paired comparison inventory')
    pair_keys = set()
    for pair in analysis['paired']:
        a, b, metric = pair['a'], pair['b'], pair['metric']
        if (a not in METHODS or b not in METHODS or METHODS.index(a) >= METHODS.index(b)
                or metric not in {'f1', 'exact'} or (a, b, metric) in pair_keys):
            fail('unexpected or duplicate paired comparison')
        pair_keys.add((a, b, metric))
        ids = sorted(tasks)
        differences = [float(method_results[a][i][metric]) - float(method_results[b][i][metric]) for i in ids]
        if pair['n'] != expected_n or pair['seed'] != 20261014 or pair['replicates'] != 2000:
            fail('paired uncertainty protocol changed')
        equal(sum(differences) / expected_n, pair['difference_a_minus_b'], label + '/paired/difference')
        rng = random.Random(pair['seed'])
        samples = sorted(sum(differences[rng.randrange(expected_n)] for _ in ids) / expected_n
                         for _ in range(pair['replicates']))
        equal([samples[50], samples[1950]], pair['paired_bootstrap_95_percentile_ci'], label + '/paired/CI')
    table_lines = ['| Method | N | Complete-record macro F1 | Exact output | Failures |',
                   '| --- | ---: | ---: | ---: | ---: |']
    for method in METHODS:
        value = per_method[method]
        table_lines.append(f"| {method} | {value['n']} | {value['requested_complete_record_macro_f1']:.4f} | {value['exact_outputs']}/{value['n']} | {value['failed_n']} |")
    if (folder / 'performance_table.md').read_text() != '\n'.join(table_lines) + '\n':
        fail(label + ': published performance table differs from exact replay')
    return {'admitted_n': expected_n, 'method_item_n': expected_n * 4,
            'protocol_sha256': sha(folder / 'protocol.json'), 'methods': per_method}, tasks


def verify(evidence, bundle):
    evidence, bundle = evidence.resolve(), bundle.resolve()
    manifest = check_pins(evidence, 'evidence_manifest.json', exact=True)
    bundle_manifest = check_pins(bundle, 'manifest.json')
    if bundle_manifest.get('admitted_n') != 371:
        fail('expected published union371 bundle')
    archives = sorted(evidence.rglob('*.tar.gz'))
    expected_archives = {'inputs/main350_bundle.tar.gz', 'inputs/additional21_bundle.tar.gz'} | {
        'retained_runs/' + label + '.tar.gz' for label in PHASES if label != 'admitted_union'}
    if {p.relative_to(evidence).as_posix() for p in archives} != expected_archives:
        fail('unexpected or missing retained/input archives')
    archive_proofs = {}
    phase_proofs = {}
    phase_tasks = {}
    with tempfile.TemporaryDirectory(prefix='spectra-offline-evidence-') as temporary:
        extraction = Path(temporary)
        extracted = {}
        for number, archive in enumerate(archives):
            rel = archive.relative_to(evidence).as_posix()
            extracted[rel], archive_proofs[rel] = extract_checked(
                archive, archive.with_suffix(archive.suffix + '.inventory.json'), extraction / str(number))
        redaction_proof = verify_redactions(evidence, extracted)
        inputs = {}
        for label in ('main350_bundle', 'additional21_bundle'):
            archive_name = 'main350' if label == 'main350_bundle' else 'additional21'
            path = extracted['inputs/' + archive_name + '_bundle.tar.gz']
            check_pins(path, 'manifest.json')
            inputs[label] = path
        if set(rows(inputs['main350_bundle'] / 'tasks.jsonl')) & set(rows(inputs['additional21_bundle'] / 'tasks.jsonl')):
            fail('main350 and additional21 overlap')
        for label, (_, input_label) in PHASES.items():
            folder = evidence / 'results' / label
            archived = None
            if input_label is not None:
                archived = extracted['retained_runs/' + label + '.tar.gz']
                # Published result copies must be the very same redacted bytes
                # retained in the archive, rather than a second score snapshot.
                for path in folder.rglob('*'):
                    if path.is_file():
                        rel = path.relative_to(folder).as_posix()
                        counterpart = under(archived, rel)
                        if not counterpart.is_file() or sha(counterpart) != sha(path):
                            fail(label + ': result copy/archive mismatch: ' + rel)
                protocol = load(folder / 'protocol.json')
                if protocol.get('bundle_manifest_sha256') != sha(inputs[input_label] / 'manifest.json'):
                    fail(label + ': frozen input manifest pin mismatch')
            phase_proofs[label], phase_tasks[label] = replay_phase(
                label, folder, inputs[input_label] if input_label else bundle, bundle, archived)
        equal(phase_tasks['original_attempt'], phase_tasks['transport_recovered'], '350/repair_identity')
        equal(phase_tasks['additional_original_attempt'], phase_tasks['additional_originals_recovered'], '21/repair_identity')
        union_tasks = {**phase_tasks['original_attempt'], **phase_tasks['additional_original_attempt']}
        equal(union_tasks, phase_tasks['admitted_union'], '371/exact_disjoint_task_union')
        union_folder = evidence / 'results/admitted_union'
        union_protocol = load(union_folder / 'protocol.json')
        if union_protocol.get('bundle_manifest_sha256') != sha(bundle / 'manifest.json'):
            fail('371 union protocol concerns a different published contract bundle')
        components = union_protocol.get('components', [])
        phase_by_run = {'original-core-transport-supplement': 'transport_recovered',
                        'additional-originals-transport-supplement': 'additional_originals_recovered'}
        if len(components) != 2 or {c['run_name'] for c in components} != set(phase_by_run):
            fail('371 union does not pin both source cohort protocols')
        for component in components:
            label = phase_by_run[component['run_name']]
            if component['n'] != PHASES[label][0]:
                fail('371 union source cohort denominator mismatch')
            for name in ('protocol', 'analysis', 'generation_complete'):
                if component[name + '_sha256'] != sha(evidence / 'results' / label / (name + '.json')):
                    fail('371 union component file pin mismatch: ' + name)
        prediction_pins = union_protocol.get('source_prediction_and_status_pins', {})
        if len(prediction_pins) != 16:
            fail('371 union must pin all16 source prediction/status files')
        seen_sources = set()
        for old_path, expected_hash in prediction_pins.items():
            bits = safe_relative(old_path).parts
            if len(bits) < 3:
                fail('invalid union source file path')
            run_name, method, filename = bits[-3:]
            if run_name not in phase_by_run or method not in METHODS or filename not in {'predictions.jsonl', 'statuses.jsonl'}:
                fail('unexpected union source file pin')
            identity = (run_name, method, filename)
            if identity in seen_sources:
                fail('duplicate union source file pin')
            seen_sources.add(identity)
            if sha(evidence / 'results' / phase_by_run[run_name] / method / filename) != expected_hash:
                fail('union source prediction/status SHA mismatch')
        for key in ('new_model_calls', 'new_query_executions', 'quality_retries'):
            if union_protocol.get(key) != 0:
                fail('371 aggregation must not invent additional model calls or executions')
        for method in METHODS:
            union_predictions = rows(union_folder / method / 'predictions.jsonl')
            union_statuses = rows(union_folder / method / 'statuses.jsonl')
            for label in ('transport_recovered', 'additional_originals_recovered'):
                source_folder = evidence / 'results' / label / method
                for identity, prediction in rows(source_folder / 'predictions.jsonl').items():
                    equal(prediction, union_predictions[identity], '371/copied_prediction/' + identity)
                for identity, status in rows(source_folder / 'statuses.jsonl').items():
                    for key in ('id', 'repair_sha256', 'status'):
                        equal(status[key], union_statuses[identity][key], '371/copied_status/' + identity)
        for recovered, original in [('transport_recovered', 'original_attempt'),
                                    ('additional_originals_recovered', 'additional_original_attempt')]:
            protocol = load(evidence / 'results' / recovered / 'protocol.json')
            if protocol['transport_recovery']['original_protocol_sha256'] != phase_proofs[original]['protocol_sha256']:
                fail('transport supplement source protocol pin mismatch')
            if load(evidence / 'results' / recovered / 'generation_complete.json').get('original_artifacts_unchanged') is not True:
                fail('transport supplement does not preserve original artifacts')
    # Recheck all files after replay; this includes untouched published scores.
    check_pins(evidence, 'evidence_manifest.json', exact=True)
    check_pins(bundle, 'manifest.json')
    return {
        'status': 'PASS', 'evidence_manifest_sha256': sha(evidence / 'evidence_manifest.json'),
        'bundle_manifest_sha256': sha(bundle / 'manifest.json'), 'evidence_file_n': len(manifest['files']),
        'archive_integrity': archive_proofs, 'phases': phase_proofs,
        'redaction_provenance': redaction_proof,
        'failure_zero_overrides_replayed': True, 'paired_intervals_replayed': True,
        'fresh_extraction': True, 'answer_queries_executed': 0, 'model_calls': 0,
        'expert_review_claimed': False,
        'limitations': ['Integrity and saved-prediction scoring do not establish graph factual completeness.',
                        'Original finance-redacted bytes cannot be reconstructed from published redacted bytes.',
                        'No fresh model generation, retrieval, database execution or expert review was performed.'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    output = args.out.resolve()
    if output.is_relative_to(args.evidence.resolve()) or output.is_relative_to(args.bundle.resolve()):
        parser.error('--out must be outside the immutable evidence and contract packages')
    if output.exists():
        parser.error('--out already exists; preserve prior verification evidence')
    report = verify(args.evidence, args.bundle)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status': report['status'], 'phases': list(report['phases']),
                      'evidence_file_n': report['evidence_file_n'], 'proof': str(output)}))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError, json.JSONDecodeError, tarfile.TarError) as error:
        print(json.dumps({'status': 'FAIL', 'reason': str(error)}), file=sys.stderr)
        sys.exit(1)
