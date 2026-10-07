#!/usr/bin/env python3
"""Inventory retained original-question logs and inspect source/key consistency.

Preparation only: this program has no semantic-label or model-scoring input.
It executes only the pinned historical canon/norm function ASTs, not the
baseline harness or any database, model, retrieval, or network function.
"""
from __future__ import annotations

import argparse
import ast
import collections
import gzip
import hashlib
import json
from pathlib import Path
import types

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
TRACK = Path('scripts/publication/paper/under-review/kdd-2027-datasets-benchmarks')
ANALYSIS = ROOT / TRACK / 'baseline/results/analysis/rebuttal'
OBSERVATION = ROOT / 'logs/publication/paper/under-review/kdd-2027-datasets-benchmarks/baseline-runs/_source_contract_expansion_v1'
ARMS = ('closed_book', 'rag', 'kg_grounded')
MODELS = ('claude-haiku-4.5', 'claude-opus-4.8', 'deepseek-v3.1',
          'gemini-2.5-flash', 'gemini-2.5-pro', 'gpt-5-mini', 'gpt-5.1',
          'llama-3.3-70b', 'qwen3-235b')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while data := stream.read(1024 * 1024):
            h.update(data)
    return h.hexdigest()


def text_sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()
            if line.strip() and '_header' not in json.loads(line)]


def historical_norm(baseline):
    environment = {'json': json}
    for name, function in (('bench_common.py', 'canon'), ('score.py', 'norm')):
        tree = ast.parse((baseline / name).read_text())
        nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == function]
        if len(nodes) != 1:
            raise ValueError('expected one historical normalization function')
        module = ast.Module(body=nodes, type_ignores=[])
        exec(compile(module, name, 'exec'), environment)
        if function == 'canon':
            environment['bc'] = types.SimpleNamespace(canon=environment['canon'])
    return environment['norm']


def log_id_inventory(path, all_ids, core_ids):
    opener = gzip.open if path.suffix == '.gz' else open
    seen, duplicates, invalid, no_id = set(), 0, 0, 0
    first_record_fields, lines, conditions, question_fields = set(), 0, set(), set()
    with opener(path, 'rt', encoding='utf-8') as stream:
        for line in stream:
            if not line.strip():
                continue
            lines += 1
            try:
                row = json.loads(line)
            except ValueError:
                invalid += 1
                continue
            if type(row) is not dict:
                raise ValueError('retained log row is not an object')
            cid = row.get('id')
            if cid is None:
                no_id += 1
                continue
            if type(cid) is not str:
                raise ValueError('retained log id is not a string')
            if cid in seen:
                duplicates += 1
                continue
            seen.add(cid)
            first_record_fields.update(row)
            conditions.add(row.get('condition'))
            question_fields.update(set(row) & {'question', 'question_en', 'prompt', 'messages'})
    return {'nonempty_lines': lines, 'unique_ids': len(seen),
            'first_record_rule': 'first valid JSON object for each id, as historical score_core.read_predictions',
            'duplicate_ids_ignored': duplicates, 'invalid_JSON_lines_skipped': invalid,
            'rows_without_id_skipped': no_id, 'Core_ids_present_n': len(seen & core_ids),
            'Core_ids_missing': sorted(core_ids - seen), 'IDs_outside_original624': sorted(seen - all_ids),
            'sorted_IDs_utf8_SHA256': text_sha('\n'.join(sorted(seen)) + '\n'),
            'first_record_field_names': sorted(first_record_fields),
            'recorded_conditions': sorted(conditions), 'stored_question_or_prompt_field_names': sorted(question_fields)}


def source_key_comparison(core_key, receipts, observation, norm):
    rows, counts = [], collections.Counter()
    for k in sorted(core_key):
        g, receipt = core_key[k], receipts[k]
        e = receipt['execution']
        item = {'id': k, 'receipt_sha256': sha(observation / 'receipts' / (k + '.json')),
                'status': e['status'], 'declared_original_answer_column': g['answer_column'],
                'old_key_has_scope_repaired_query': bool(g.get('repaired_cypher'))}
        if e['status'] != 'OK' or not e['full_json_rows_available']:
            item.update(comparable=False, blocker='native ordinary-read completion/full positional JSON unavailable')
            counts['native_unavailable'] += 1
        else:
            if e['columns'].count(g['answer_column']) != 1:
                raise ValueError('original answer column does not resolve uniquely in native columns')
            path = observation / e['rows_file']
            if sha(path) != e['rows_file_sha256']:
                raise ValueError('native rows hash mismatch')
            native = [json.loads(line) for line in path.read_text().splitlines()]
            if any(type(row) is not list or len(row) != len(e['columns']) for row in native):
                raise ValueError('native positional rows mismatch')
            position = e['columns'].index(g['answer_column'])
            declared_set = {norm(row[position]) for row in native}
            first_set = {norm(row[0]) for row in native}
            v2 = {norm(v) for v in g['gold_values']}
            v1 = {norm(v) for v in g.get('gold_values_released_query', g['gold_values'])}
            item.update(comparable=True, declared_column_position=position,
                        source_declared_matches_preserved_default_Core_V2=declared_set == v2,
                        source_declared_matches_preserved_released_V1=declared_set == v1,
                        source_first_column_matches_preserved_default_Core_V2=first_set == v2,
                        source_declared_normalized_set_n=len(declared_set),
                        preserved_default_Core_V2_normalized_set_n=len(v2),
                        preserved_released_V1_normalized_set_n=len(v1))
            counts['native_declared_matches_Core_V2' if declared_set == v2 else 'native_declared_mismatches_Core_V2'] += 1
            counts['native_declared_matches_released_V1' if declared_set == v1 else 'native_declared_mismatches_released_V1'] += 1
            counts['declared_column_position_' + str(position)] += 1
        rows.append(item)
    return {'primary_key': 'unchanged-query released/V1 key',
            'sensitivity_key': 'historical default Core/V2 key, on the entire identical cohort',
            'normalizer': 'unchanged historical score.norm: whitespace-collapsed casefolded bench_common.canon strings',
            'answer_values_exposed': False, 'model_scores_computed': False,
            'counts': dict(counts), 'items': rows,
            'mismatch_policy': 'Primary source/gold consistency uses released/V1. A source/V1 mismatch blocks analysis of the unchanged cohort. Preserve all default Core/V2 mismatches as transparency and same-entire-cohort sensitivity; a V2 mismatch does not block V1 analysis or remove an item. Never rewrite gold or select by scores.'}


def diagnostic_key_plan(consistency_items, cohort_ids):
    """Check a caller-frozen cohort without selecting or removing any members.

    No audit labels or model predictions are read here. Historical V2 mismatch
    affects only its disclosure; both keys must use the entire same cohort.
    """
    cohort = list(cohort_ids)
    if len(cohort) != len(set(cohort)):
        raise ValueError('duplicate frozen cohort identity')
    items = {item['id']: item for item in consistency_items}
    if len(items) != len(consistency_items) or not set(cohort) <= set(items):
        raise ValueError('unknown or duplicate source-consistency identity')
    blockers = [k for k in cohort if items[k].get('comparable') is not True
                or items[k].get('source_declared_matches_preserved_released_V1') is not True]
    changed_v2 = [k for k in cohort if items[k].get('comparable') is True
                  and items[k].get('source_declared_matches_preserved_default_Core_V2') is False]
    return {'frozen_cohort_ids': cohort, 'cohort_membership_changed': False,
            'primary_key': 'released/V1', 'primary_source_mismatch_blockers': blockers,
            'primary_source_consistency_passed': not blockers,
            'sensitivity_key': 'default Core/V2', 'sensitivity_cohort_ids': list(cohort),
            'source_V2_changed_key_ids_in_same_cohort': changed_v2,
            'V2_mismatches_block_primary_V1': False, 'model_scores_computed': False}


def build_inventory(public, observation):
    baseline = public / 'paper/baseline'
    cq = public / 'release_package/cqs/spectra_cq_v2.0'
    inputs = json.loads((observation / 'input_manifest.json').read_text())
    summary = json.loads((observation / 'source_contract_observation_summary_v1.json').read_text())
    key_rows = read_jsonl(cq / 'core_answer_gold.jsonl')
    core_key = {row['id']: row for row in key_rows}
    benchmark = read_jsonl(cq / 'benchmark.jsonl')
    all_ids = {row['id'] for row in benchmark}
    core_ids = set(core_key)
    if len(core_ids) != len(key_rows) or len(core_ids) != 560 or len(all_ids) != 624:
        raise ValueError('original input identities mismatch')
    if core_ids != {r['id'] for r in inputs['items']}:
        raise ValueError('source observation identity mismatch')
    if sha(observation / 'input_manifest.json') != summary['input_manifest_sha256']:
        raise ValueError('source input manifest hash mismatch')
    summary_items = {r['id']: r for r in summary['items']}
    receipts = {}
    for k in sorted(core_ids):
        path = observation / 'receipts' / (k + '.json')
        if sha(path) != summary_items[k]['receipt_sha256']:
            raise ValueError('source receipt hash mismatch')
        receipts[k] = json.loads(path.read_text())
    files = []
    for arm in ARMS:
        observed_models = {p.name for p in (baseline / 'results' / arm).iterdir() if p.is_dir()}
        if observed_models != set(MODELS):
            raise ValueError('historical nine-model condition matrix changed')
        for model in MODELS:
            directory = baseline / 'results' / arm / model
            path = next((directory / name for name in ('all.jsonl', 'all.jsonl.gz') if (directory / name).is_file()), None)
            if path is None:
                raise ValueError('historical model run missing')
            metadata = log_id_inventory(path, all_ids, core_ids)
            if metadata['IDs_outside_original624'] or metadata['recorded_conditions'] != [arm]:
                raise ValueError('retained original run identity/condition mismatch')
            files.append({'condition': arm, 'model_slug': model,
                          'relative_public_path': str(path.relative_to(public)),
                          'sha256': sha(path), 'bytes': path.stat().st_size, **metadata})
    pinned_code = ('bench_common.py', 'score.py', 'score_core.py', 'run_baseline.py')
    pins = [{'relative_public_path': 'paper/baseline/' + name, 'sha256': sha(baseline / name)} for name in pinned_code]
    pins += [{'relative_public_path': 'release_package/cqs/spectra_cq_v2.0/' + name, 'sha256': sha(cq / name)}
             for name in ('benchmark.jsonl', 'questions.json', 'answer_contract.jsonl', 'core_answer_gold.jsonl', 'splits/track_assignment.json')]
    return {'kind': 'pre-label retained original-question baseline hash inventory and source/key consistency only',
            'state': 'prepared; no semantic audit judgments loaded; no model performance computed',
            'code_sha256': sha(__file__), 'original_Core_n': 560, 'original624_n': 624,
            'retained_run_files_n': len(files), 'models_per_condition': len(MODELS), 'conditions': list(ARMS),
            'files': files, 'public_source_and_legacy_code_pins': pins,
            'source_observation_pins': {name: sha(observation / name) for name in ('input_manifest.json', 'frozen_manifest.json', 'source_contract_observation_summary_v1.json')},
            'source_key_consistency': source_key_comparison(core_key, receipts, observation, historical_norm(baseline)),
            'limits': ['Retained logs do not store the full original prompts/questions; pinned harness uses question_en, but per-trial exact prompt byte provenance is unavailable.',
                       'Original kg_grounded prediction is its saved first model-returned column; the Core key is its declared answer column, which may not be the first reference-query column.',
                       'Primary key is released/V1, matching the unchanged native source queries. Default Core/V2 preserves seven scope-repaired references and is a same-entire-cohort historical sensitivity, not a reason for membership changes.',
                       'A released/V1 diagnostic cannot be interpreted as recovering the old paper default Core/V2 performance.',
                       'Old normalization compares canonical strings, collapses whitespace/case and duplicate values, and does not preserve native typing, named roles, ordering or multiplicity.',
                       'These retained graph/text conditions have unequal evidence access and potentially unequal source cutoffs; future score differences cannot identify a causal effect.',
                       'Future dual AI alignment agreement is a source-evidenced diagnostic, not independent domain-expert or canonical-gold certification.'],
            'semantic_audit_labels_read': False, 'new_model_calls': 0, 'database_calls': 0,
            'model_scores_computed': False, 'original_questions_queries_gold_predictions_modified': False}


def self_test(public):
    import tempfile
    norm = historical_norm(public / 'paper/baseline')
    assert norm(' A  B ') == 'a b'
    assert norm({'b': 2, 'a': 1}) == norm({'a': 1, 'b': 2})
    assert norm(1) == norm('1') and norm(1.0) != norm(1)
    assert norm(True) == norm('true') and norm(True) != norm(1)
    assert len({norm('A'), norm(' a ')}) == 1
    with tempfile.TemporaryDirectory(prefix='original_retained_inventory_test_') as temporary:
        path = Path(temporary) / 'all.jsonl'
        path.write_text('{"id":"a","condition":"rag","predicted_values":[]}\ninvalid\n{"id":"a","condition":"rag","predicted_values":["later"]}\n{"id":"b","condition":"rag"}\n')
        r = log_id_inventory(path, {'a', 'b'}, {'a', 'b', 'c'})
        assert r['unique_ids'] == 2 and r['duplicate_ids_ignored'] == 1
        assert r['invalid_JSON_lines_skipped'] == 1 and r['Core_ids_missing'] == ['c']
        assert r['stored_question_or_prompt_field_names'] == []
    synthetic = [dict(id='a', comparable=True,
                      source_declared_matches_preserved_released_V1=True,
                      source_declared_matches_preserved_default_Core_V2=True),
                 dict(id='b', comparable=True,
                      source_declared_matches_preserved_released_V1=True,
                      source_declared_matches_preserved_default_Core_V2=False)]
    plan = diagnostic_key_plan(synthetic, ['b', 'a'])
    assert plan['frozen_cohort_ids'] == plan['sensitivity_cohort_ids'] == ['b', 'a']
    assert plan['primary_source_consistency_passed'] and plan['source_V2_changed_key_ids_in_same_cohort'] == ['b']
    synthetic[0]['source_declared_matches_preserved_released_V1'] = False
    blocked = diagnostic_key_plan(synthetic, ['a', 'b'])
    assert not blocked['primary_source_consistency_passed'] and blocked['primary_source_mismatch_blockers'] == ['a']
    assert blocked['frozen_cohort_ids'] == blocked['sensitivity_cohort_ids'] == ['a', 'b']
    print('PASS: 12 historical-normalization, first-record and fixed-cohort V1/V2 policy invariants; no model or DB calls')


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--public-directory', type=Path, default=ROOT.parent / 'spectra-public/spec-trace')
    parser.add_argument('--source-observation-directory', type=Path, default=OBSERVATION)
    parser.add_argument('--out', type=Path, default=ANALYSIS / 'original_retained_baseline_inventory_v1.json')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test(args.public_directory)
        return
    if args.out.exists():
        raise SystemExit('refusing to overwrite pre-label inventory')
    inventory = build_inventory(args.public_directory.resolve(), args.source_observation_directory.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8') as stream:
        json.dump(inventory, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'retained_runs': inventory['retained_run_files_n'], 'sha256': sha(args.out),
                      'source_key_counts': inventory['source_key_consistency']['counts'], 'performance_computed': False}))


if __name__ == '__main__':
    main()
