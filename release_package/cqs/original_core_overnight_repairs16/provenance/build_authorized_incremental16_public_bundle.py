#!/usr/bin/env python3
"""Prepare the authorized CQ001 portable repair bundle for root review.

Spec: original formal Section lookup across all retained release-final editions.
Ontology: unchanged frozen Spec/HAS_SECTION/Section source population.
Cycle: KDD Datasets and Benchmarks original-question contract repair.
This writes only the supplied new destination. No API, native graph, central
registry, scorer implementation, or public checkout is changed by this helper.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import subprocess

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--auth', type=Path, required=True)
parser.add_argument('--public-checkout', type=Path, required=True)
parser.add_argument('--dest', type=Path, required=True)
parser.add_argument('--scope-sha256', default='ddc3554078fa96b6828766dcfafbdf84689d3dc86b46a5748571d537de5e954a')
args = parser.parse_args()
AUTH = args.auth.resolve()
B = AUTH.parent
PUBLIC = args.public_checkout.resolve()
WORKTREE = AUTH / 'baseline_source'
PARENT = PUBLIC / 'release_package/cqs/original_core_repair'
DEST = args.dest.resolve()
KEYS = ['id', 'question_en', 'original_query', 'reference_query', 'required_fields',
        'collection', 'cardinality_policy', 'repair_class', 'original_question_preserved']
sys.path.insert(0, str(PARENT))
import scorer
import original_scorer
import review_schema
import contract_checks


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def canonical(v):
    return scorer.get_kernel().json_exact(v)


def digest(v):
    return hashlib.sha256(canonical(v).encode()).hexdigest()


def read(p):
    return json.loads(Path(p).read_text())


def lines(p):
    return [scorer.get_kernel().loads_exact(s) for s in Path(p).read_text().splitlines() if s.strip()]


def write_json(p, v):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n')


def write_lines(p, v):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(''.join(canonical(r) + '\n' for r in v))


def copy(source, relative, expected=None):
    source = Path(source)
    actual = sha(source)
    assert expected is None or actual == expected, (source, 'pin changed')
    target = DEST / relative
    assert target.resolve().is_relative_to(DEST.resolve())
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert sha(target) == actual
    else:
        shutil.copyfile(source, target)
    return {'file': str(relative), 'sha256': actual, 'bytes': source.stat().st_size}


def main():
    assert not DEST.exists(), 'preserve existing bundle; choose a new version for changes'
    assert sha(AUTH / 'scope.json') == args.scope_sha256, 'scope changed'
    scope = read(AUTH / 'scope.json')
    assert scope['baseline_public_commit_observed'] == '2e086b0ba3e6292d26920bc2ef3ba2e5f72bad9f'
    assert subprocess.check_output(['git', '-C', str(PUBLIC), 'rev-parse', 'HEAD'], text=True).strip() == scope['baseline_public_commit_observed']
    assert not DEST.is_relative_to(PUBLIC), 'public mutation belongs to root publication'
    for name, pin in scope['baseline_public_snapshot_pins'].items():
        source = WORKTREE / 'release_package/cqs/current_core' / name
        assert sha(source) == pin['sha256']
        assert source.stat().st_size == pin['bytes']
        assert sha(PUBLIC / 'release_package/cqs/current_core' / name) == pin['sha256']
    for name, expected in scope['source_registry_pins'].items():
        assert sha(AUTH / name) == expected
    assert sha(AUTH / scope['authorization_evidence_file']) == scope['authorization_evidence_sha256']
    baseline_index = read(WORKTREE / 'release_package/cqs/current_core/index_manifest.json')
    baseline_n = scope['baseline_public_pass_n']
    target_n = scope['authorized_target_original_frozen_union_n']
    pending_n = scope['authorized_target_pending_n']
    assert baseline_n == baseline_index['repaired_n'] == 475
    assert target_n == baseline_n + scope['authorized_original_frozen_repair_n'] == 476
    assert baseline_index['registered_n'] == target_n + pending_n == 560
    assert scope['authorized_original_frozen_repair_n'] == 1
    inputs = read(AUTH / 'admission_inputs.json')
    cases = {r['id']: r for r in scope['cases']}
    assert len(cases) == len(inputs) == 1
    assert set(cases) == {'RAN1_P3_CQ001'}
    admissions = {r['id']: r for r in read(AUTH / 'current_local_admissions.json')['admitted']}
    assert set(admissions) == set(cases)
    originals = {r['id']: r for r in lines(PARENT / 'provenance/original_benchmark.jsonl')}
    baseline = lines(WORKTREE / 'release_package/cqs/current_core/all_core_dispositions.jsonl')
    assert len(baseline) == 560 and sum(r['status'] == 'pass' for r in baseline) == baseline_n
    assert not set(cases) & {r['id'] for r in baseline if r['status'] == 'pass'}
    full_sql_path = AUTH / 'gate_inputs/full_independent_sql_scope_bridge.json'
    full_sql = read(full_sql_path)
    assert full_sql['status'] == 'PASS' and full_sql['scope_n'] == 1
    sql_cases = {r['id']: r for r in full_sql['cases']}
    assert set(sql_cases) == set(cases)
    criteria = read(PARENT / 'criteria.json')
    criteria_sha = sha(PARENT / 'criteria.json')
    parent_manifest = read(PARENT / 'manifest.json')
    assert parent_manifest['graph_sources'] == baseline_index['source_snapshot']
    DEST.mkdir(parents=True)
    for name in ('criteria.json', 'original_scorer.py', 'scorer.py',
                 'typed_values.py', 'contract_checks.py', 'review_schema.py', 'source_pins.json'):
        copy(PARENT / name, name, parent_manifest['files'][name])
    runtime = PUBLIC / baseline_index['latest_scope']['bundle']
    runtime_manifest = read(runtime / 'manifest.json')
    for name in ('score_predictions.py', 'rational_share_records.py', 'share_runtime_adapter.py'):
        assert sha(runtime / name) == runtime_manifest['files'][name]
        copy(runtime / name, name)
    copy(runtime / 'manifest.json', 'protocol_extensions/baseline_runtime_manifest.json')
    for name in ('scope.json', 'admission_inputs.json', 'current_local_admissions.json',
                 'new_answerable_questions.json', 'additional_budget_authorization.json'):
        copy(AUTH / name, 'authorization/' + name)
    copy(WORKTREE / 'release_package/cqs/current_core/index_manifest.json', 'baseline/index_manifest.json')
    copy(WORKTREE / 'release_package/cqs/current_core/all_core_dispositions.jsonl', 'baseline/all_core_dispositions.jsonl')
    copy(WORKTREE / 'release_package/cqs/current_core/current_tasks.jsonl', 'baseline/current_tasks.jsonl')
    copy(PARENT / 'provenance/original_benchmark.jsonl', 'provenance/original_benchmark.jsonl')
    copy(full_sql_path, 'provenance/root_full_SQL_recheck_at_build.json')
    copy(Path(__file__), 'provenance/build_authorized_incremental16_public_bundle.py')
    tasks, gold, checks, source_projection = [], [], [], []
    for entry in inputs:
        source_def = B / entry['definition']
        task = read(source_def)
        ident, wg = task['id'], task['id'].split('_')[0]
        pinned = cases[ident]
        assert sha(source_def) == pinned['definition']['sha256']
        definition = {k: task[k] for k in KEYS}
        repair_sha = digest(definition)
        assert repair_sha == task['repair_sha256'] == pinned['repair_sha256']
        assert repair_sha == '42b55e6702c348dad4d5faeaad61507ce1fe3e83aaf5de2f44485c44e0376039'
        assert task['required_fields'] == pinned['required_fields']
        assert [f['name'] for f in task['required_fields']] == ['specRelease', 'sectionNumber', 'sectionTitle']
        assert task['collection'] == {'kind': 'set'}
        assert task['question_en'] == originals[ident]['question_en']
        assert task['original_query'] == originals[ident]['cypher']
        primary = read(B / entry['primary']) if entry.get('primary') else task['primary_review']
        secondary = read(B / entry['secondary'])
        assert sha(B / entry['primary']) == pinned['gate_files']['primary']['sha256']
        assert sha(B / entry['secondary']) == pinned['gate_files']['secondary']['sha256']
        for judgment in (primary, secondary):
            review_schema.check_pass(judgment, task['question_en'], criteria['semantic_units'],
                criteria_sha=criteria_sha, identity_key='repair_sha256', identity_sha=repair_sha)
            assert judgment['human_author_review_completed'] is False and judgment['expert_validation_n'] == 0
        assert primary['reviewer_kind'] != secondary['reviewer_kind']
        portable_gates = {}
        for role, pin in pinned['gate_files'].items():
            if pin.get('embedded_in_definition'):
                value = task[pin['embedded_in_definition']]
                assert digest(value) == pin['sha256']
                relative = 'gate_evidence/' + ident + '/' + role + '.json'
                write_json(DEST / relative, value)
                portable_gates[role] = {'file': relative, 'sha256': sha(DEST / relative),
                    'embedded_in_definition': pin['embedded_in_definition'], 'embedded_digest': pin['sha256']}
                continue
            path = Path(pin['path'])
            portable_gates[role] = copy(path, 'gate_evidence/' + ident + '/' + role + path.suffix, pin['sha256'])
        copy(source_def, 'definitions/' + ident + '.json', pinned['definition']['sha256'])
        controls = read(B / entry['controls'])
        assert controls['id'] == ident and controls['repair_sha256'] == repair_sha
        assert controls['status'] == 'controls_pass' and all(c['pass'] for c in controls['controls'])
        receipts = [Path(p) for p in controls['pins'] if '/reference_outputs/' in p and p.endswith('.json')]
        assert len(receipts) == 1
        rp = receipts[0]
        receipt = read(rp)
        qsha = hashlib.sha256(task['reference_query'].encode()).hexdigest()
        assert receipt['query'] == task['reference_query'] and receipt['query_sha256'] == qsha
        assert receipt['status'] == 'OK' and receipt['full_rows_available'] is True
        assert receipt['truncated'] is False and receipt['rollback_completed'] is True
        assert receipt['execution_summary_complete'] is True
        assert receipt['plan_query_type'] == receipt['execution_query_type'] == 'r'
        assert receipt['id'] == ident
        assert receipt['columns'] == ['specRelease', 'sectionNumber', 'sectionTitle']
        rows_path = rp.with_suffix('.jsonl')
        assert sha(rows_path) == receipt['rows_sha256'] == controls['pins'][str(rows_path)]
        assert sha(rp) == controls['pins'][str(rp)]
        positional = lines(rows_path)
        assert all(type(r) is list and len(r) == len(receipt['columns']) for r in positional)
        native = [dict(zip(receipt['columns'], r)) for r in positional]
        assert len(native) == receipt['rows_retained'] == controls['native_reference_population_n'] == 46
        assert Counter(r['specRelease'] for r in native) == {'Rel-15': 7, 'Rel-16': 9, 'Rel-17': 10, 'Rel-18': 10, 'Rel-19': 10}
        root = 'reference_outputs/' + ident + '/' + qsha
        rp_pin = copy(rp, root + '.json')
        rows_pin = copy(rows_path, root + '.jsonl')
        native_base = rp.parents[2]
        run_path = native_base / ('execution_' + wg + '.json')
        run = read(run_path)
        assert run['inventory_unchanged'] is True and run['model_calls'] == 0 and run['expert_validation'] is False
        expected_guard = baseline_index['source_snapshot'][wg]
        assert controls['source_guard'] == expected_guard
        assert run['source_before'] == run['source_after'] == expected_guard
        run_item = next(r for r in run['items'] if r['id'] == ident)
        assert run_item['status'] == 'OK' and run_item['query_sha256'] == qsha and run_item['rows'] == len(native)
        run_pin = copy(run_path, 'provenance/native_run_' + sha(run_path) + '.json')
        input_path = native_base / 'execution_inputs' / (wg + '.jsonl')
        if not input_path.is_file():
            input_path = Path(pinned['gate_files']['exact_native_input']['path'])
            assert sha(input_path) == run['input_sha256'] == pinned['gate_files']['exact_native_input']['sha256']
        chain = {}
        for name, path in [('execution_inputs', input_path),
                           ('execution_protocol', native_base / 'execution_protocol.json')]:
            chain[name] = copy(path, 'provenance/' + sha(path) + path.suffix)
        assert chain['execution_inputs']['sha256'] == run['input_sha256']
        assert chain['execution_protocol']['sha256'] == run['protocol_sha256']
        input_task = next(r for r in lines(input_path) if r['id'] == ident)
        assert input_task['candidate_query'] == task['reference_query']
        sql_case = sql_cases[ident]
        assert sql_case['all_return_fields_compared'] is True and sql_case['uncapped_SQL'] is True
        assert sql_case['native_receipt_sha256'] == rp_pin['sha256']
        assert sql_case['native_rows_sha256'] == rows_pin['sha256']
        independent_path = B / sql_case['independent_records']
        sql_pin = copy(independent_path, 'independent_SQL/' + ident + '.jsonl', sql_case['independent_records_sha256'])
        independent = lines(independent_path)
        assert Counter(map(canonical, independent)) == Counter(map(canonical, native))
        assert all(set(r) == set(receipt['columns']) for r in independent)
        sql_case = dict(sql_case, portable_independent_records=sql_pin)
        sql_case_pin = None
        write_json(DEST / ('independent_SQL/' + ident + '_evidence.json'), sql_case)
        sql_case_pin = {'file': 'independent_SQL/' + ident + '_evidence.json',
                        'sha256': sha(DEST / ('independent_SQL/' + ident + '_evidence.json'))}
        fields = task['required_fields']
        records = []
        for row in native:
            record = {}
            for field in fields:
                key = field['name'] if field['name'] in row else field['source_column_or_expression']
                assert key in row, (ident, field, receipt['columns'])
                record[field['name']] = row[key]
            records.append(record)
        scorer.project(records, fields, gold=True)
        groups = original_scorer.make_order_groups(task, native, records) if task['collection']['kind'] in {
            'native_ordered_ties', 'top_k_boundary_ties'} else None
        actual_checks = contract_checks.checks(task, records, groups)
        assert actual_checks == controls['controls'] and all(r['pass'] for r in actual_checks), ident
        assert len(actual_checks) == 13
        source_pins = []
        for pin in admissions[ident]['source_witness_pins']:
            path = Path(pin['path'])
            rel = 'source_evidence/' + pin['sha256'] + path.suffix
            copied = copy(path, rel, pin['sha256'])
            source_pins.append(dict(copied, original_path=pin['path']))
        source_projection.append({'id': ident, 'source_witnesses': source_pins})
        completed = dict(definition, repair_sha256=repair_sha, criteria_sha256=criteria_sha,
            original_question_sha256=hashlib.sha256(task['question_en'].encode()).hexdigest(),
            original_query_sha256=hashlib.sha256(task['original_query'].encode()).hexdigest(),
            reference_query_sha256=qsha, primary_review=primary, secondary_review=secondary,
            validation_status='validated', admitted=True, native_execution_completed=True,
            scorer_controls_completed=True, human_author_review_completed=False, expert_validation_n=0,
            model_calls=0, model_call_scope='No predictions in repair bundle; authorized fresh evaluation is separate.',
            native_rows=len(records), projected_records_sha256=digest(records),
            portable_native_evidence={'receipt_file': rp_pin['file'], 'receipt_sha256': rp_pin['sha256'],
                'rows_file': rows_pin['file'], 'rows_sha256': rows_pin['sha256'],
                'run_report_file': run_pin['file'], 'run_report_sha256': run_pin['sha256'], 'chain': chain},
            portable_gate_evidence=portable_gates, portable_source_evidence=source_pins,
            portable_independent_SQL_evidence=sql_case_pin,
            limitations='Graph-relative original recorded metadata and operations; two nonblind AI judgments, not human/expert validation or complete physical-source coverage.')
        tasks.append(completed)
        gold.append({'id': ident, 'repair_sha256': repair_sha, 'records': records, 'order_groups': groups})
        checks.append({'id': ident, 'repair_sha256': repair_sha, 'checks': actual_checks, 'pass': True})
    assert {t['id'] for t in tasks} == set(cases)
    write_lines(DEST / 'tasks.jsonl', tasks)
    write_lines(DEST / 'reference_gold.jsonl', gold)
    write_lines(DEST / 'scorer_checks.jsonl', checks)
    write_json(DEST / 'source_public_projection.json', source_projection)
    ledger = {r['id']: r for r in baseline}
    for t in tasks:
        ledger[t['id']] = {'id': t['id'], 'status': 'pass', 'repair_class': t['repair_class'],
                          'repair_sha256': t['repair_sha256'], 'question_preserved': True}
    write_lines(DEST / 'all_core_dispositions.jsonl', sorted(ledger.values(), key=lambda r: r['id']))
    assert sum(r['status'] == 'pass' for r in ledger.values()) == target_n
    assert all(ledger[row['id']] == row for row in baseline if row['id'] not in cases)
    assert sum(row['status'] != 'pass' for row in ledger.values()) == pending_n
    copy(OUT / 'verify_authorized_incremental16_public_bundle.py', 'verify_additions.py')
    (DEST / 'README.md').write_text(
        '# Additional original-question formal Section repair\n\n'
        'This immutable one-question cohort preserves the exact original English question and its '
        'authorized contract. The pinned baseline contains 475 validated original questions; this '
        'cohort brings the union to 476 of 560, leaving 84 nonadmitted. Every other disposition, '
        'including existing source-factuality quarantines, is preserved byte-for-value.\n\n'
        'CQ001 returns the formal top-level body and Annex Section observations for all five '
        'retained release-final editions of TS 38.214, explicitly attributed by release. The complete '
        'reference has 46 observations, not a single mixed-edition outline. Unnumbered frontmatter '
        'is outside the preserved formal Section schema; the bare Spec reference node is not a sixth '
        'edition. This does not assert coverage of all minor versions or newer external standards.\n\n'
        'The portable evidence retains two separate nonblind AI judgments, rollback-only native '
        'execution, a full-field independent SQL comparison, five-source replay receipts and 13 '
        'replayable scorer controls. It contains no model predictions and no human/expert validation. '
        'Physical source observations and frozen graph-relative answer correctness remain distinct. '
        'A fresh evaluation belongs to its separately frozen protocol; prior scores are not transferred.\n\n'
        'Run `python3 -B -S verify_additions.py --bundle .` for an offline verification. No API or '
        'database is contacted by this verifier. Hashes authenticate the included execution evidence; '
        'offline replay is not a new execution of the original source archive or graph.\n')
    manifest = {'kind': 'Immutable authorized additional1 original-question repairs; model evaluation separate',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'parent_public_commit': scope['baseline_public_commit_observed'],
        'parent_bundle_manifest_sha256': sha(PARENT / 'manifest.json'),
        'baseline_public_pass_n': baseline_n, 'admitted_n': 1, 'cohort_ids': [t['id'] for t in tasks],
        'global_admitted_union_n': target_n, 'global_unresolved_n': pending_n,
        'authorization_scope_sha256': sha(AUTH / 'scope.json'),
        'authorization_admission_inputs_sha256': sha(AUTH / 'admission_inputs.json'),
        'native_rows': sum(t['native_rows'] for t in tasks),
        'actual_scorer_controls': sum(len(c['checks']) for c in checks),
        'repair_classes': dict(Counter(t['repair_class'] for t in tasks)),
        'graph_sources': baseline_index['source_snapshot'],
        'representation_protocol': 'Unchanged ordinary typed requested-field set matcher; exact-share hooks are inactive for this contract',
        'model_predictions_n': 0, 'expert_validation_n': 0, 'human_author_review_completed': False,
        'source_public_projection': 'source_public_projection.json',
        'baseline_public_snapshot_pins': {name: {'file': 'baseline/' + name, 'sha256': pin['sha256']} for name, pin in scope['baseline_public_snapshot_pins'].items()},
        'files': {str(p.relative_to(DEST)): sha(p) for p in DEST.rglob('*') if p.is_file()}}
    write_json(DEST / 'manifest.json', manifest)
    print(json.dumps({'status': 'BUNDLE_PREPARED_REQUIRE_OFFLINE_REPLAY', 'bundle': str(DEST),
        'manifest_sha256': sha(DEST / 'manifest.json'), 'admitted_n': 1,
        'native_rows': manifest['native_rows'], 'actual_scorer_controls': manifest['actual_scorer_controls']}))


if __name__ == '__main__':
    main()
