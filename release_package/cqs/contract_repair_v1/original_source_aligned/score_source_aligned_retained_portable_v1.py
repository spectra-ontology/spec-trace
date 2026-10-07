#!/usr/bin/env python3
"""Replay the admitted original-question AI-agreement cohort, with V1 primary.

Preparation only until a root-approved public admission is supplied. This is a
separate entrypoint; historical score_core's 133/V2 default remains unchanged.
No model, database, network, publication or file-write operation is implemented.

Future offline command (the expected manifest SHA is an external trust anchor):
  python3 -B score_source_aligned_retained_portable_v1.py \
    --bundle BUNDLE --public-root RELEASE --expected-manifest-sha256 SHA

Bundle manifest.json: kind=source_aligned_retained_portable_admission_v1,
closed=true, original_Core_n=560, audit_checked_calls_n=112,
entrypoint_sha256=<this unchanged wrapper's SHA>,
files={admission,inventory,reference_report,legacy_analysis,legacy_preparation},
each {path:<bundle-relative>,sha256:<published bytes>}; source_commitments is
an allowlisted mapping of original source SHA digests. Admission is a safe
projection of the closed author report: all560_dispositions, fixed_cohort_ids,
fixed_cohort_ids_sha256, source_key_comparison_all560.items. Reference contains
only project_reference() fields. Inventory contains unchanged retained log and
legacy-code/key pins from the original pre-label inventory. Code/preparation
full-file hashes are fixed below; only their listed pure function ASTs execute.

Source commitments bind an author-admitted projection, not independently
revalidated unpublished audit traces, source rows, expert truth or question
accuracy. The prior full source admission remains a prerequisite outside this
offline replayer. Legacy canonical-string set scoring ignores named roles,
types, order and multiplicity; it is not strict named-record performance.
Both keys retain the exact same cohort, including all V2 changed-key cases.
An empty admitted cohort has undefined metrics (null), never a zero result.
"""
from __future__ import annotations

import argparse
import ast
import collections
import gzip
import hashlib
import json
from pathlib import Path
import random
import re
import sys
import types

sys.dont_write_bytecode = True
ANALYSIS_SHA = '259c7b699671cf4ee487b2a6780297b2d1177376d792f37c7797f9b96c295c45'
PREPARATION_SHA = '587508c7230d69b01c82ff7ef2dfec50be0d81d92187c7f7361647c3c6169c38'
ARMS = ('closed_book', 'rag', 'kg_grounded')
MODELS = ('claude-haiku-4.5', 'claude-opus-4.8', 'deepseek-v3.1',
          'gemini-2.5-flash', 'gemini-2.5-pro', 'gpt-5-mini', 'gpt-5.1',
          'llama-3.3-70b', 'qwen3-235b')
METRICS = ('f1', 'exact', 'precision', 'recall')
LEGACY_CODE_SHA = {
    'bench_common.py': '1ed9b9e4f68e1438ad1e7b724474ba74fd9db6329bce536bc678e00061e55787',
    'score.py': '83f3c4abfa7710f0db678b86063cd52338bcc76a1677a318303ec57ea161b5c2',
    'score_core.py': '2ef640bf09c72787365f4952c8620ffc6f040a89d4e55542fc771561f14f420a',
    'run_baseline.py': '6134e5ad0cac325ae9c51a218e6e6900f9998325ff9fbc406939d54da68db361'}
REFERENCE_FIELDS = ('status', 'model_scores_computed', 'primary_key',
                    'whole_identical_cohort_sensitivity_key', 'per_run',
                    'per_task_scores', 'retained_parser_inventory',
                    'paired_differences', 'bootstrap', 'pooled_by_condition')
SOURCE_COMMITMENTS = ('author_report_sha256', 'author_inventory_sha256',
                      'audit_manifest_sha256', 'closed_audit_index_sha256',
                      'source_observation_sha256', 'analysis_protocol_sha256')
PRIVATE_TOKEN_SHA256 = frozenset({
    '341d8fd36787bdf618f76867bff8eb5f002057c08a69ea06af98d6da16499acf',
    'd9633577fa456f680408e27803173c94e7e060987f0ea21f7e3a0443c1132663',
    'a373ccf98f8b53f24965680b61272a8a47aafb0d3b94b88936e4f8f59b71c4ad',
    '5918c8df11198cb50e76732942448b055e50186e9724bc209d5713d70f0e834f'})


class ReplayError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ReplayError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read_json(path):
    def pairs(entries):
        result = {}
        for k, v in entries:
            require(k not in result, 'duplicate metadata key')
            result[k] = v
        return result
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ReplayError('nonfinite metadata')))


def safe_child(directory, relative):
    require(type(relative) is str, 'relative path required')
    p = Path(relative)
    require(not p.is_absolute() and p.parts and '..' not in p.parts, 'unsafe artifact path')
    result = Path(directory) / p
    require(not any(x.is_symlink() for x in [result, *result.parents]), 'symlinked artifact')
    require(result.is_file(), 'missing artifact')
    return result


def pinned(path, expected):
    require(type(expected) is str and re.fullmatch('[a-f0-9]{64}', expected), 'invalid SHA')
    require(sha(path) == expected, 'artifact hash mismatch')


def safe_metadata(value):
    if isinstance(value, dict):
        for k, v in value.items():
            safe_metadata(k); safe_metadata(v)
    elif isinstance(value, list):
        for v in value:
            safe_metadata(v)
    elif isinstance(value, str):
        require(not re.search(r'/home/|/Users/|/root/|Authorization:|Bearer |OPENAI_API_KEY', value),
                'private metadata in public projection')
        require(not any(hashlib.sha256(token.encode()).hexdigest() in PRIVATE_TOKEN_SHA256
                        for token in re.findall(r'[A-Za-z0-9]+', value)),
                'private token in public projection')


def project_admission(report):
    """Pure projection helper; does not inspect or execute an actual audit."""
    rows = []
    for row in report['all560_dispositions']:
        value = {k: row[k] for k in ('id', 'native_status', 'native_complete',
                                    'both_host_full_contract_aligned', 'selected')}
        for rater in ('A', 'B'):
            pair = row[rater]
            value[rater] = {k: pair[k] for k in ('validity', 'host_original_full_contract')}
        value['original_disposition_sha256'] = digest(row)
        rows.append(value)
    fields = ('id', 'status', 'declared_original_answer_column', 'comparable',
              'declared_column_position', 'source_declared_matches_preserved_released_V1',
              'source_declared_matches_preserved_default_Core_V2',
              'source_declared_normalized_set_n', 'preserved_released_V1_normalized_set_n',
              'preserved_default_Core_V2_normalized_set_n')
    return {'all560_dispositions': rows, 'fixed_cohort_ids': report['fixed_cohort_ids'],
            'fixed_cohort_ids_sha256': report['fixed_cohort_ids_sha256'],
            'source_key_comparison_all560': {'items': [
                {k: row[k] for k in fields if k in row}
                for row in report['source_key_comparison_all560']['items']]}}


def project_reference(report):
    return {k: report[k] for k in REFERENCE_FIELDS if k in report}


def ast_functions(path, names, environment):
    tree = ast.parse(Path(path).read_text())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    require(len(nodes) == len(names) and {n.name for n in nodes} == set(names), 'pure functions missing')
    exec(compile(ast.Module(body=nodes, type_ignores=[]), 'fixed pure scientific functions', 'exec'), environment)


def pure_functions(analysis, preparation):
    pinned(analysis, ANALYSIS_SHA); pinned(preparation, PREPARATION_SHA)
    env = {'json': json, 'gzip': gzip, 'random': random, 'collections': collections,
           'Path': Path, 'types': types, 'ast': ast, 'METRICS': METRICS,
           'N_BOOT': 10000, 'SEED': 0, 'ProofError': ReplayError}
    ast_functions(analysis, ('require', 'frozen_cohort', 'mean', 'paired_bootstrap',
                            'read_predictions', 'score_fixed_cohort', 'build_contrasts'), env)
    ast_functions(preparation, ('text_sha', 'diagnostic_key_plan', 'log_id_inventory',
                               'historical_norm'), env)
    env['hashlib'] = hashlib
    return env


def validate_admission(admission, key, functions):
    require(set(admission) == {'all560_dispositions', 'fixed_cohort_ids',
                              'fixed_cohort_ids_sha256', 'source_key_comparison_all560'},
            'unsafe admission projection')
    rows = admission['all560_dispositions']
    require(type(rows) is list and len(rows) == 560, 'all560 dispositions required')
    require(len({r['id'] for r in rows}) == 560 and {r['id'] for r in rows} == set(key),
            'Core/disposition identity mismatch')
    labels, native = {}, {}
    for row in rows:
        fields = {'id', 'A', 'B', 'native_status', 'native_complete',
                  'both_host_full_contract_aligned', 'selected'}
        require(fields <= set(row) <= fields | {'original_disposition_sha256'},
                'unsafe disposition projection')
        if 'original_disposition_sha256' in row:
            require(type(row['original_disposition_sha256']) is str and
                    re.fullmatch('[a-f0-9]{64}', row['original_disposition_sha256']),
                    'invalid source disposition digest')
        k = row['id']
        for field in ('selected', 'native_complete', 'both_host_full_contract_aligned'):
            require(type(row[field]) is bool, 'disposition flag must be Boolean')
        pair = {}
        for rater in ('A', 'B'):
            p = row[rater]
            require(set(p) == {'validity', 'host_original_full_contract'}, 'unsafe rater projection')
            require(p['validity'] in ('valid', 'invalid'), 'pending rater admission')
            label = p['host_original_full_contract']
            require((p['validity'] == 'valid' and label in ('aligned', 'misaligned', 'unresolved')) or
                    (p['validity'] == 'invalid' and label is None), 'invalid rater label')
            pair[rater] = p
        require(not row['native_complete'] or row['native_status'] == 'OK', 'native completion/status mismatch')
        labels[k] = pair
        native[k] = {'execution': {'status': row['native_status'],
            'execution_summary_complete': row['native_complete'],
            'full_json_rows_available': row['native_complete'],
            'truncated': not row['native_complete'], 'unsupported_json_rows': 0}}
    cohort, checked = functions['frozen_cohort'](labels, native)
    observed = {r['id']: r for r in rows}
    require(all(r['selected'] == observed[r['id']]['selected'] and
                r['both_host_full_contract_aligned'] == observed[r['id']]['both_host_full_contract_aligned']
                for r in checked), 'admitted selection disagrees with both-valid/native-complete rule')
    require(admission['fixed_cohort_ids'] == cohort, 'fixed cohort identity/order mismatch')
    require(admission['fixed_cohort_ids_sha256'] == functions['text_sha']('\n'.join(cohort) + '\n'),
            'cohort SHA mismatch')
    consistency = admission['source_key_comparison_all560']['items']
    require(set(admission['source_key_comparison_all560']) == {'items'}, 'unsafe source projection')
    require(len(consistency) == 560 and len({r['id'] for r in consistency}) == 560 and
            {r['id'] for r in consistency} == set(key), 'all560 source/key comparisons required')
    for row in consistency:
        source_fields = {'id', 'status', 'declared_original_answer_column', 'comparable',
              'declared_column_position', 'source_declared_matches_preserved_released_V1',
              'source_declared_matches_preserved_default_Core_V2',
              'source_declared_normalized_set_n', 'preserved_released_V1_normalized_set_n',
              'preserved_default_Core_V2_normalized_set_n'}
        require(set(row) <= source_fields and type(row['comparable']) is bool,
                'unsafe source/key projection')
        if row['comparable']:
            require(type(row['source_declared_matches_preserved_released_V1']) is bool and
                    type(row['source_declared_matches_preserved_default_Core_V2']) is bool,
                    'explicit V1 and V2 source comparison required')
        require(row['declared_original_answer_column'] == key[row['id']]['answer_column'],
                'declared native field differs from preserved original key')
        require(row['status'] == observed[row['id']]['native_status'], 'native/source admission status mismatch')
    plan = functions['diagnostic_key_plan'](consistency, cohort)
    require(plan['primary_source_consistency_passed'], 'primary source/V1 admission mismatch')
    return cohort, plan


def calculate(cohort, key, predictions, inventory, tracks, functions, norm, score_row):
    if not cohort:
        return {'status': 'CLOSED_EMPTY_COHORT', 'model_scores_computed': False}
    wg = {k: row['wg'] for k, row in key.items()}
    per_task, aggregate = functions['score_fixed_cohort'](cohort, key, predictions, score_row, norm, wg, tracks)
    vectors = functions['build_contrasts'](per_task, cohort, sorted(MODELS))
    return {'status': 'COMPLETE', 'model_scores_computed': True, 'primary_key': 'released_V1',
        'whole_identical_cohort_sensitivity_key': 'default_Core_V2',
        'per_run': aggregate, 'per_task_scores': per_task,
        'retained_parser_inventory': [{'condition': r['condition'], 'model': r['model_slug'],
             'invalid_JSON_lines_skipped': r['invalid_JSON_lines_skipped'],
             'duplicate_ids_ignored': r['duplicate_ids_ignored']} for r in inventory['files']],
        'paired_differences': functions['paired_bootstrap'](vectors),
        'bootstrap': {'n': 10000, 'seed': 0, 'unit': 'task shared across27 runs and both keys',
                      'percentile_zero_based_indices': [250, 9749]},
        'pooled_by_condition': {label: {arm: {metric: functions['mean']([r[metric]
            for name, r in runs.items() if name.startswith(arm + '/')]) for metric in METRICS}
            for arm in ARMS} for label, runs in aggregate.items()}}


def replay(bundle, public, expected_manifest_sha256):
    bundle, public = Path(bundle), Path(public)
    manifest_path = safe_child(bundle, 'manifest.json')
    pinned(manifest_path, expected_manifest_sha256)
    manifest = read_json(manifest_path); safe_metadata(manifest)
    pinned(Path(__file__), manifest['entrypoint_sha256'])
    require(manifest['kind'] == 'source_aligned_retained_portable_admission_v1' and
            manifest['closed'] is True and type(manifest['original_Core_n']) is int and
            manifest['original_Core_n'] == 560 and type(manifest['audit_checked_calls_n']) is int and
            manifest['audit_checked_calls_n'] == 112, 'closed fixed admission required')
    commitments = manifest['source_commitments']
    require(set(commitments) == set(SOURCE_COMMITMENTS) and
            all(type(v) is str and re.fullmatch('[a-f0-9]{64}', v) for v in commitments.values()),
            'original-source commitments required')
    names = ('admission', 'inventory', 'reference_report', 'legacy_analysis', 'legacy_preparation')
    require(set(manifest['files']) == set(names), 'unexpected manifest files')
    paths = {k: safe_child(bundle, manifest['files'][k]['path']) for k in names}
    require(len(set(paths.values())) == len(names), 'overlapping bundle artifacts')
    for k, p in paths.items():
        pinned(p, manifest['files'][k]['sha256'])
    inventory = read_json(paths['inventory']); admission = read_json(paths['admission'])
    reference = read_json(paths['reference_report'])
    for v in (inventory, admission, reference):
        safe_metadata(v)
    require(type(inventory['original_Core_n']) is int and inventory['original_Core_n'] == 560 and
            type(inventory['original624_n']) is int and inventory['original624_n'] == 624,
            'original inventory cardinalities differ')
    rows = inventory['files']; runs = {(r['condition'], r['model_slug']) for r in rows}
    require(len(rows) == 27 and len(runs) == 27 and
            runs == {(a, m) for a in ARMS for m in MODELS}, 'fixed27 run matrix required')
    sourcepins = inventory['public_source_and_legacy_code_pins']
    expected_sources = {'paper/baseline/' + x for x in ('bench_common.py', 'score.py', 'score_core.py', 'run_baseline.py')}
    cq = 'release_package/cqs/spectra_cq_v2.0/'
    expected_sources |= {cq + x for x in ('benchmark.jsonl', 'questions.json', 'answer_contract.jsonl',
                                         'core_answer_gold.jsonl', 'splits/track_assignment.json')}
    require(len(sourcepins) == len(expected_sources) and
            {r['relative_public_path'] for r in sourcepins} == expected_sources, 'original source pin set differs')
    allpins = sourcepins + rows
    require(len({r['relative_public_path'] for r in allpins}) == len(allpins), 'duplicate public input path')
    # Validate every original key/code/log byte BEFORE parsing any prediction.
    public_paths = {r['relative_public_path']: safe_child(public, r['relative_public_path']) for r in allpins}
    for row in allpins:
        pinned(public_paths[row['relative_public_path']], row['sha256'])
    for name, expected in LEGACY_CODE_SHA.items():
        pinned(public_paths['paper/baseline/' + name], expected)
    functions = pure_functions(paths['legacy_analysis'], paths['legacy_preparation'])
    key_rows = [json.loads(s) for s in public_paths[cq + 'core_answer_gold.jsonl'].read_text().splitlines() if s.strip()]
    key_rows = [r for r in key_rows if '_header' not in r]
    key = {r['id']: r for r in key_rows}
    require(len(key_rows) == len(key) == 560, 'original Core key IDs differ')
    benchmark = [json.loads(s) for s in public_paths[cq + 'benchmark.jsonl'].read_text().splitlines() if s.strip()]
    all_ids = {r['id'] for r in benchmark if '_header' not in r}
    require(len(all_ids) == 624 and set(key) <= all_ids, 'original624 identities differ')
    cohort, plan = validate_admission(admission, key, functions)
    tracks = read_json(public_paths[cq + 'splits/track_assignment.json'])
    require(set(tracks) == all_ids and all(v in ('lookup', 'aggregation', 'relational', 'multihop')
                                          for v in tracks.values()), 'released track identities differ')
    norm = functions['historical_norm'](public / 'paper/baseline')
    score_env = {'norm': norm}
    ast_functions(public_paths['paper/baseline/score.py'], ('score_row',), score_env)
    predictions = {}
    if cohort:
        for row in rows:
            path = public_paths[row['relative_public_path']]
            observed = functions['log_id_inventory'](path, all_ids, set(key))
            require(all(observed[k] == v for k, v in row.items() if k in observed), 'retained parser/source inventory mismatch')
            require(not observed['IDs_outside_original624'] and observed['recorded_conditions'] == [row['condition']],
                    'original run condition/identity mismatch')
            values, parsed = functions['read_predictions'](path)
            require(all(parsed[k] == row[k] for k in parsed), 'legacy parser counts differ')
            predictions[(row['condition'], row['model_slug'])] = values
    result = calculate(cohort, key, predictions, inventory, tracks, functions, norm, score_env['score_row'])
    require(result == reference, 'retained arithmetic differs from admitted author report')
    for row in allpins:
        pinned(public_paths[row['relative_public_path']], row['sha256'])
    for k, p in paths.items():
        pinned(p, manifest['files'][k]['sha256'])
    pinned(manifest_path, expected_manifest_sha256)
    return {'kind': 'offline original-question conditional AI-cohort retained-output replay',
        'fixed_cohort_ids': cohort, 'fixed_cohort_n': len(cohort), 'original_Core_n': 560,
        'all560_dispositions': admission['all560_dispositions'], 'primary_and_sensitivity_key_plan': plan,
        'results': result if cohort else None, 'empty_cohort_metrics_defined': bool(cohort),
        'public_admission_manifest_sha256': expected_manifest_sha256, 'source_commitments': commitments,
        'legacy_analysis_sha256': ANALYSIS_SHA, 'legacy_preparation_sha256': PREPARATION_SHA,
        'domain_expert_validation_n': 0, 'new_model_calls': 0, 'database_calls': 0,
        'network_calls': 0, 'original_files_modified': False,
        'limits': ['Author-admitted source/AI agreement, not independent revalidation of unpublished raw audit/source traces.',
                   'Unchanged original prompts/retained value sets; no new named-record task or original-paper V2 performance recovery.',
                   'Legacy normalization/duplicate handling preserved; roles, native types, order and multiplicity are not graded.',
                   'Unequal historical graph/text evidence and unverified equal source cutoff; no causal access-effect claim.']}


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--bundle', type=Path, required=True)
    p.add_argument('--public-root', type=Path, default=Path('.'))
    p.add_argument('--expected-manifest-sha256', required=True)
    args = p.parse_args()
    try:
        result = replay(args.bundle, args.public_root, args.expected_manifest_sha256)
    except (ValueError, KeyError, TypeError, OSError, IndexError):
        print(json.dumps({'status': 'FAIL', 'error_category': 'portable_source_admission_or_replay_failure'}))
        return 2
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
