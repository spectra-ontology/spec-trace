#!/usr/bin/env python3
"""Replay retained top-k replacements without changing previous scientific inputs."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

sys.dont_write_bytecode = True


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(bundle, parent):
    manifest = json.loads((bundle / 'manifest.json').read_text())
    actual = {p.relative_to(bundle).as_posix(): sha(p) for p in bundle.rglob('*')
              if p.is_file() and p != bundle / 'manifest.json'}
    if actual != manifest['files']:
        raise ValueError('Replacement package membership or hashes differ')

    def member(name):
        parts = PurePosixPath(name).parts
        if (not name or '\\' in name or name.startswith('/') or '..' in parts
                or name not in manifest['files']):
            raise ValueError('Unlisted or unsafe replacement evidence path')
        path = bundle / name
        if path.is_symlink() or not path.resolve().is_relative_to(bundle.resolve()):
            raise ValueError('Replacement evidence path escapes package')
        return path

    for name in manifest['files']:
        member(name)
    if sha(parent / 'manifest.json') != manifest['parent_bundle_manifest_sha256']:
        raise ValueError('Preserved parent cohort differs')
    old_manifest = json.loads((parent / 'manifest.json').read_text())
    for name in ('tasks.jsonl', 'all_core_dispositions.jsonl', 'criteria.json', 'provenance/original_benchmark.jsonl'):
        if sha(parent / name) != old_manifest['files'][name]:
            raise ValueError('Consumed parent file differs')
    if manifest['graph_sources'] != old_manifest['graph_sources'] or sha(bundle / 'criteria.json') != sha(parent / 'criteria.json'):
        raise ValueError('Replacement source or fixed semantic criteria differs')
    for name in ('scorer.py', 'original_scorer.py', 'contract_checks.py', 'review_schema.py',
                 'typed_values.py', 'source_pins.json', 'score_predictions.py'):
        if sha(member(name)) != old_manifest['files'][name] or sha(parent / name) != old_manifest['files'][name]:
            raise ValueError('Replacement silently changes inherited scoring implementation')
    sys.path.insert(0, str(bundle))
    import scorer
    import original_scorer
    import contract_checks
    import review_schema
    kernel = scorer.get_kernel()

    def rows(path):
        return [kernel.loads_exact(line) for line in path.read_text().splitlines() if line.strip()]

    def index(values):
        output = {row['id']: row for row in values}
        if len(output) != len(values):
            raise ValueError('Duplicate retained replacement ID')
        return output

    digest = lambda value: hashlib.sha256(kernel.json_exact(value).encode()).hexdigest()
    old_tasks = index(rows(parent / 'tasks.jsonl'))
    originals = index(rows(parent / 'provenance/original_benchmark.jsonl'))
    tasks = index(rows(bundle / 'tasks.jsonl'))
    gold = index(rows(bundle / 'reference_gold.jsonl'))
    checks = index(rows(bundle / 'scorer_checks.jsonl'))
    if set(tasks) != set(gold) or set(tasks) != set(checks) or not set(tasks) <= set(old_tasks):
        raise ValueError('Replacement scope differs or invents new Core IDs')
    if sha(bundle / 'provenance/parent_tasks.jsonl') != sha(parent / 'tasks.jsonl'):
        raise ValueError('Prior contract bytes were not preserved')
    if sha(bundle / 'all_core_dispositions.jsonl') != sha(parent / 'all_core_dispositions.jsonl'):
        raise ValueError('Replacement silently changes original 560 disposition counts')
    criteria = json.loads((bundle / 'criteria.json').read_text())
    artifact_index = json.loads((bundle / 'provenance/native_top_k_artifact_index.json').read_text())
    artifacts = {row['id']: row for row in artifact_index['items']}
    native_report = json.loads((bundle / 'provenance/native_top_k_report.json').read_text())
    if (artifact_index['executed_report_sha256'] != sha(member('provenance/native_top_k_report.json'))
            or artifact_index['executed_script_sha256'] != sha(member('provenance/native_top_k_audit.py'))
            or native_report['script_sha256'] != artifact_index['executed_script_sha256']):
        raise ValueError('Retained capture producer/report chain differs')
    guards = {row['wg']: row for row in native_report['groups']}
    definition_keys = ('id', 'question_en', 'original_query', 'reference_query', 'required_fields',
                       'collection', 'cardinality_policy', 'repair_class', 'original_question_preserved')
    native_n = controls_n = boundary_alternatives = 0
    for identifier, task in tasks.items():
        old = old_tasks[identifier]
        original = originals[identifier]
        if (task['question_en'] != original['question_en'] or task['original_query'] != original['cypher']
                or task['original_question_preserved'] is not True
                or task['repair_sha256'] != digest({key: task[key] for key in definition_keys})
                or task['replaces_public371_repair_sha256'] != old['repair_sha256']
                or task['required_fields'] != old['required_fields']
                or task['original_question_sha256'] != hashlib.sha256(original['question_en'].encode()).hexdigest()
                or task['original_query_sha256'] != hashlib.sha256(original['cypher'].encode()).hexdigest()
                or task['reference_query_sha256'] != hashlib.sha256(task['reference_query'].encode()).hexdigest()
                or task['criteria_sha256'] != sha(bundle / 'criteria.json')
                or task['validation_status'] != 'validated' or task['new_unique_core_id'] is not False
                or task['human_author_review_completed'] is not False or task['expert_validation_n'] != 0):
            raise ValueError('Replacement definition or scope differs: ' + identifier)
        if (re.sub(r'\s+LIMIT\s+\d+\s*$', '', old['reference_query'], flags=re.I).strip()
                != task['reference_query'].strip()):
            raise ValueError('Replacement changes more than old terminal ranking cap')
        for review in (task['primary_review'], task['secondary_review']):
            review_schema.check_pass(review, original['question_en'], criteria['semantic_units'],
                                     criteria_sha=task['criteria_sha256'], identity_key='repair_sha256',
                                     identity_sha=task['repair_sha256'])
        wg = identifier.split('_')[0]
        guard = guards[wg]
        if (guard['source_before'] != guard['source_after'] or guard['source_before'] != manifest['graph_sources'][wg]
                or guard['inventory_and_source_pins_unchanged'] is not True):
            raise ValueError('Retained source guard differs')
        native = task['portable_native_evidence']
        captured = []
        for kind in ('capped', 'uncapped'):
            evidence = native[kind]
            receipt_path = member(evidence['receipt_file'])
            rows_path = member(evidence['rows_file'])
            receipt = json.loads(receipt_path.read_text())
            original_index = artifacts[identifier]['runs'][kind]
            if (sha(receipt_path) != original_index['receipt_sha256']
                    or sha(rows_path) != original_index['rows_sha256']
                    or sha(receipt_path) != evidence['receipt_sha256'] or sha(rows_path) != evidence['rows_sha256']
                    or receipt['id'] != identifier + '__' + kind
                    or receipt['query'] != (old['reference_query'] if kind == 'capped' else task['reference_query'])
                    or receipt['query_sha256'] != hashlib.sha256(receipt['query'].encode()).hexdigest()
                    or receipt['rows_sha256'] != sha(rows_path)
                    or receipt['status'] != 'OK' or receipt['rollback_completed'] is not True
                    or receipt['full_rows_available'] is not True or receipt['truncated'] is not False
                    or receipt['execution_summary_complete'] is not True
                    or receipt['execution_query_type'] != 'r' or receipt['plan_query_type'] != 'r'):
                raise ValueError('Preserved original native receipt identity or bytes differ')
            positional = rows(rows_path)
            if (len(positional) != receipt['rows_retained'] or rows_path.stat().st_size != receipt['bytes_retained']
                    or len(set(receipt['columns'])) != len(receipt['columns'])
                    or any(type(row) is not list or len(row) != len(receipt['columns']) for row in positional)):
                raise ValueError('Retained native row dimensions differ')
            named = [dict(zip(receipt['columns'], row)) for row in positional]
            projected = [{field['name']: row[field['source_column_or_expression']]
                          for field in task['required_fields']} for row in named]
            scorer.project(projected, task['required_fields'], gold=True)
            captured.append((named, projected))
        named, projected = captured[1]
        groups = original_scorer.make_order_groups(task, named, projected)
        item_gold = gold[identifier]
        if (item_gold['repair_sha256'] != task['repair_sha256'] or item_gold['records'] != projected
                or item_gold['order_groups'] != groups or digest(projected) != task['projected_records_sha256']):
            raise ValueError('Replacement gold is not exact retained requested-field projection')
        actual_checks = contract_checks.checks(task, projected, groups)
        selected = original_scorer.reference_prediction(task, projected)
        reverse_score = original_scorer.score(task, projected, list(reversed(selected)), diagnostic=True, order_groups=groups)
        actual_checks.append({'check': 'selected_membership_reverse_display_order', 'pass': reverse_score['exact'] is True})
        if (checks[identifier]['repair_sha256'] != task['repair_sha256']
                or checks[identifier]['checks'] != actual_checks or not all(control['pass'] for control in actual_checks)):
            raise ValueError('Replacement scorer controls fail or were not actually replayed')
        boundary_alternatives += sum(control['check'] == 'alternative_boundary_subset' for control in actual_checks)
        source_audit = task['source_native_audit']
        audit = json.loads(member('provenance/source_native_audit.json').read_text())
        recorded = next(row for row in audit['items'] if row['id'] == identifier)
        if source_audit != recorded or sha(bundle / 'provenance/source_native_audit.json') != task['source_native_audit_sha256']:
            raise ValueError('Independent source audit identity differs')
        if (recorded['independent_sql_all_pool_exact'] is not True or recorded['count_multiplicity_difference_n'] != 0
                or recorded['retained_n'] != len(projected) or recorded['null_requested_identity_n'] != 0
                or recorded['distinct_requested_identity_n'] != len(projected)
                or recorded['repair_sha256'] != task['repair_sha256']
                or recorded['native_query_sha256'] != task['reference_query_sha256']
                or recorded['source_guards_match_published_parent'] is not True):
            raise ValueError('Independent source/completeness evidence differs')
        complete = recorded['complete_zero_inclusive_source_witness']
        if complete and (complete['all_positive_identity_and_count_exact'] is not True
                         or complete['omitted_zero_cannot_reach_positive_boundary'] is not True
                         or recorded['positive_boundary_value'] <= 0):
            raise ValueError('Positive-pool completeness witness incomplete')
        native_n += len(projected)
        controls_n += len(actual_checks)
    if (len(tasks) != manifest['replacement_n'] or manifest['new_original_core_id_n'] != 0
            or native_n != manifest['retained_uncapped_native_rows'] or controls_n != manifest['actual_scorer_controls']
            or boundary_alternatives != manifest['actual_boundary_alternative_controls']
            or manifest['new_model_calls'] != 0 or manifest['new_native_executions'] != 0):
        raise ValueError('Replacement accounting differs')
    return {'status': 'PASS', 'replacement_n': len(tasks), 'new_original_core_id_n': 0,
            'retained_uncapped_native_rows': native_n, 'actual_scorer_controls': controls_n,
            'actual_boundary_alternative_controls': boundary_alternatives,
            'manifest_sha256': sha(bundle / 'manifest.json'), 'original_560_ledger_unchanged': True,
            'new_model_calls': 0, 'new_native_executions': 0, 'human_expert_validation_n': 0,
            'scope': 'Recorded separate AI judgments, retained source witnesses and actually replayed scorer controls. No full raw-archive truth or new model performance.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True, type=Path)
    parser.add_argument('--parent', required=True, type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    report = verify(args.bundle.resolve(), args.parent.resolve())
    if args.out:
        if args.out.resolve().is_relative_to(args.bundle.resolve()) or args.out.resolve().is_relative_to(args.parent.resolve()):
            raise ValueError('Report must be outside frozen packages')
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
