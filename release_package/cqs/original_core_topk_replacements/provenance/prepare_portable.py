#!/usr/bin/env python3
"""Package separately reviewed replacements while preserving prior artifacts."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
PARENT = ROOT.parent / 'spectra-public/spec-trace/release_package/cqs/original_core_repair'
MECHANICAL = ROOT / 'logs/publication/paper/under-review/kdd-2027-datasets-benchmarks/gxmb-verification/mechanical'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    target = HERE / 'bundle'
    if target.exists():
        raise ValueError('Refuse to replace an existing prepared bundle')
    target.mkdir()
    parent_manifest_sha = sha(PARENT / 'manifest.json')
    parent_manifest = json.loads((PARENT / 'manifest.json').read_text())
    sys.path.insert(0, str(PARENT))
    import scorer
    import original_scorer
    import contract_checks
    import review_schema
    kernel = scorer.get_kernel()

    def load_rows(path):
        return [kernel.loads_exact(line) for line in path.read_text().splitlines() if line.strip()]

    def copy(source, name):
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        if sha(source) != sha(destination):
            raise ValueError('Copied artifact differs')
        return destination.relative_to(target).as_posix()

    for name in ('original_scorer.py', 'scorer.py', 'typed_values.py', 'source_pins.json',
                 'contract_checks.py', 'review_schema.py', 'score_predictions.py', 'test_native_order.py',
                 'test_boundary_ties.py', 'test_predictions.py', 'test_scorer.py', 'criteria.json',
                 'all_core_dispositions.jsonl'):
        copy(PARENT / name, name)
    copy(PARENT / 'tasks.jsonl', 'provenance/parent_tasks.jsonl')
    copy(PARENT / 'manifest.json', 'provenance/parent_manifest.json')
    copy(PARENT / 'provenance/original_benchmark.jsonl', 'provenance/original_benchmark.jsonl')
    for name in ('candidates.jsonl', 'secondary.jsonl', 'secondary_mechanical_checks.json', 'source_native_audit.json'):
        copy(HERE / name, 'provenance/' + name)
    for name in ('native_top_k_artifact_index.json', 'native_top_k_report.json', 'native_top_k_audit.py'):
        copy(MECHANICAL / name, 'provenance/' + name)
    for source, name in ((HERE.parent / 'audit_topk_replacement_sources.py', 'source_frozen_sql_audit.py'),
                         (HERE.parent / 'prepare_topk_replacements.py', 'prepare_semantic_reviews.py'),
                         (Path(__file__), 'prepare_portable.py')):
        copy(source, 'provenance/' + name)
    copy(HERE / 'verify_replacements.py', 'verify_replacements.py')
    candidates = load_rows(HERE / 'candidates.jsonl')
    secondary_rows = load_rows(HERE / 'secondary.jsonl')
    secondary = {row['id']: row for row in secondary_rows}
    if len(secondary) != len(secondary_rows) or set(secondary) != {row['id'] for row in candidates}:
        raise ValueError('Exact second-review scope differs')
    artifact_index = json.loads((MECHANICAL / 'native_top_k_artifact_index.json').read_text())
    artifacts = {row['id']: row for row in artifact_index['items']}
    units = json.loads((target / 'criteria.json').read_text())['semantic_units']
    tasks, gold, controls = [], [], []
    native_n = check_n = boundary_n = 0
    for candidate in candidates:
        identifier = candidate['id']
        task = dict(candidate, secondary_review=secondary[identifier], admitted=True,
                    validation_status='validated', human_author_review_completed=False, expert_validation_n=0)
        for review in (task['primary_review'], task['secondary_review']):
            review_schema.check_pass(review, task['question_en'], units, criteria_sha=sha(target / 'criteria.json'),
                                     identity_key='repair_sha256', identity_sha=task['repair_sha256'])
        portable = {}
        for kind in ('capped', 'uncapped'):
            source = artifacts[identifier]['runs'][kind]
            portable[kind] = {}
            for suffix in ('receipt', 'rows'):
                original = MECHANICAL / source[suffix + '_file']
                if sha(original) != source[suffix + '_sha256']:
                    raise ValueError('Historical native evidence differs')
                name = copy(original, 'provenance/' + source[suffix + '_file'])
                portable[kind][suffix + '_file'] = name
                portable[kind][suffix + '_sha256'] = source[suffix + '_sha256']
        task['portable_native_evidence'] = portable
        receipt = json.loads((target / portable['uncapped']['receipt_file']).read_text())
        native = load_rows(target / portable['uncapped']['rows_file'])
        named = [dict(zip(receipt['columns'], row)) for row in native]
        records = [{field['name']: row[field['source_column_or_expression']]
                    for field in task['required_fields']} for row in named]
        scorer.project(records, task['required_fields'], gold=True)
        groups = original_scorer.make_order_groups(task, named, records)
        task['projected_records_sha256'] = hashlib.sha256(kernel.json_exact(records).encode()).hexdigest()
        actual = contract_checks.checks(task, records, groups)
        selected = original_scorer.reference_prediction(task, records)
        actual.append({'check': 'selected_membership_reverse_display_order',
                       'pass': original_scorer.score(task, records, list(reversed(selected)), diagnostic=True,
                                                     order_groups=groups)['exact'] is True})
        if not all(row['pass'] for row in actual):
            raise ValueError('Actual replacement controls fail')
        tasks.append(task)
        gold.append({'id': identifier, 'repair_sha256': task['repair_sha256'], 'records': records, 'order_groups': groups})
        controls.append({'id': identifier, 'repair_sha256': task['repair_sha256'], 'checks': actual})
        native_n += len(records)
        check_n += len(actual)
        boundary_n += sum(row['check'] == 'alternative_boundary_subset' for row in actual)
    for name, values in (('tasks.jsonl', tasks), ('reference_gold.jsonl', gold), ('scorer_checks.jsonl', controls)):
        (target / name).write_text(''.join(kernel.json_exact(value) + '\n' for value in values))
    (target / 'README.md').write_text('''# Existing top-k contract replacements

These ten separately reviewed contracts preserve the original English questions,
original queries and required answer fields. Their reference queries remove only
the final cap and retain the full eligible ranking pool, so any valid selection
at the numeric boundary can be scored. Display order is not required.

This package replaces definitions for ten existing Core IDs. It adds no IDs;
the previous 371-item bundle and its complete 560-item disposition ledger are
preserved unchanged and pinned. The separately published seven-item and local
eight-item additions are not changed by these replacements. Original capped
and uncapped native receipts retain their original IDs and bytes.

The two new AI semantic reviews and retained frozen-source SQL witnesses are
included separately. The offline verifier checks identities, typed native
projections, source guards and actually replays all scorer controls. It does not
rerun SQL databases or certify raw-archive completeness, human review or expert
validation. No new model calls or native executions were used to build this
package. Existing frozen model results remain associated with their original
contracts; any rescoring must be labelled separately.

Run from a fresh copy, supplying the unchanged parent bundle:

```sh
python3 -B verify_replacements.py --bundle . --parent ../original_core_repair --out /tmp/replacement-proof.json
python3 -B -m unittest test_scorer test_native_order test_predictions test_boundary_ties
```
''')
    files = {path.relative_to(target).as_posix(): sha(path) for path in sorted(target.rglob('*')) if path.is_file()}
    manifest = {'kind': 'additive_existing_original_core_top_k_replacements',
                'parent_bundle_manifest_sha256': parent_manifest_sha,
                'graph_sources': parent_manifest['graph_sources'], 'files': files,
                'replacement_n': len(tasks), 'new_original_core_id_n': 0,
                'retained_uncapped_native_rows': native_n, 'actual_scorer_controls': check_n,
                'actual_boundary_alternative_controls': boundary_n,
                'human_expert_validation_n': 0, 'new_model_calls': 0, 'new_native_executions': 0,
                'prior_scientific_bytes_unchanged': True,
                'scope': 'Ten existing contract replacements only; zero additional confirmed Core IDs.'}
    (target / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    if sha(PARENT / 'manifest.json') != parent_manifest_sha:
        raise ValueError('Parent changed during packaging')
    report = {'status': 'PREPARED', 'bundle': str(target), 'manifest_sha256': sha(target / 'manifest.json'),
              'listed_files_n': len(files), 'replacement_n': len(tasks), 'new_original_core_id_n': 0,
              'retained_uncapped_native_rows': native_n, 'actual_scorer_controls': check_n,
              'actual_boundary_alternative_controls': boundary_n}
    (HERE / 'packaging_report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
