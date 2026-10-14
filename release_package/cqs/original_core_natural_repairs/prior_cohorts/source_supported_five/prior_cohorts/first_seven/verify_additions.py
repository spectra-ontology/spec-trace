#!/usr/bin/env python3
"""Check retained additional repairs without changing the published cohort.

This verifies recorded AI judgments, captured outputs and scoring controls.
It is not human/expert validation or a new model evaluation.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import zipfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(bundle, parent):
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(bundle))
    import scorer
    import original_scorer
    import review_schema
    import contract_checks

    kernel = scorer.get_kernel()
    read = lambda path: [kernel.loads_exact(line) for line in path.read_text().splitlines() if line.strip()]
    digest = lambda value: hashlib.sha256(kernel.json_exact(value).encode()).hexdigest()

    def index(rows):
        output = {row['id']: row for row in rows}
        if len(output) != len(rows):
            raise ValueError('duplicate retained ID')
        return output

    manifest = json.loads((bundle / 'manifest.json').read_text())
    if sha(parent / 'manifest.json') != manifest['parent_bundle_manifest_sha256']:
        raise ValueError('parent repair cohort changed')
    parent_manifest = json.loads((parent/'manifest.json').read_text())
    for name in ('tasks.jsonl','all_core_dispositions.jsonl','provenance/original_benchmark.jsonl','criteria.json'):
        if sha(parent/name) != parent_manifest['files'][name]:
            raise ValueError('Consumed parent file differs: '+name)
    if manifest['graph_sources'] != parent_manifest['graph_sources']:
        raise ValueError('Additional source snapshot differs from preserved parent')
    files = {str(path.relative_to(bundle)): sha(path) for path in bundle.rglob('*')
             if path.is_file() and path.name != 'manifest.json' and not path.name.startswith('.')}
    if files != manifest['files']:
        raise ValueError('additional package membership or SHA differs')
    def member(name):
        path = bundle/name
        if name not in manifest['files'] or path.is_symlink() or not path.resolve().is_relative_to(bundle.resolve()):
            raise ValueError('Evidence path is not an internal manifest member')
        return path
    criteria = json.loads((bundle / 'criteria.json').read_text())
    tasks = index(read(bundle / 'tasks.jsonl'))
    gold = index(read(bundle / 'reference_gold.jsonl'))
    checks = index(read(bundle / 'scorer_checks.jsonl'))
    originals = index(read(parent / 'provenance/original_benchmark.jsonl'))
    previous = index(read(parent / 'tasks.jsonl'))
    if not tasks or set(tasks) != set(gold) or set(tasks) != set(checks) or set(tasks) & set(previous):
        raise ValueError('additional tasks/gold/controls scope differs')
    definition_keys = ('id', 'question_en', 'original_query', 'reference_query', 'required_fields',
                       'collection', 'cardinality_policy', 'repair_class', 'original_question_preserved')
    native_n = 0
    controls_n = 0
    for identifier, task in tasks.items():
        original = originals[identifier]
        if (task['question_en'] != original['question_en'] or task['original_query'] != original['cypher']
                or task['original_question_preserved'] is not True
                or task['repair_sha256'] != digest({key: task[key] for key in definition_keys})
                or task['criteria_sha256'] != sha(bundle / 'criteria.json')
                or task['original_question_sha256'] != hashlib.sha256(original['question_en'].encode()).hexdigest()
                or task['original_query_sha256'] != hashlib.sha256(original['cypher'].encode()).hexdigest()
                or task['reference_query_sha256'] != hashlib.sha256(task['reference_query'].encode()).hexdigest()
                or task['validation_status'] != 'validated'
                or task['human_author_review_completed'] is not False or task['expert_validation_n'] != 0):
            raise ValueError('original question, definition or validation scope differs: ' + identifier)
        for review in (task['primary_review'], task['secondary_review']):
            review_schema.check_pass(review, task['question_en'], criteria['semantic_units'],
                                     criteria_sha=task['criteria_sha256'], identity_key='repair_sha256',
                                     identity_sha=task['repair_sha256'])
        if (task['repair_class'] != ('scorer_only' if task['reference_query'] == original['cypher']
                                    else 'query_and_scorer')):
            raise ValueError('repair class differs')
        native = task['portable_native_evidence']
        receipt_path = member(native['receipt_file'])
        rows_path = member(native['rows_file'])
        if sha(receipt_path) != native['receipt_sha256'] or sha(rows_path) != native['rows_sha256']:
            raise ValueError('native output SHA differs')
        receipt = json.loads(receipt_path.read_text())
        execution = receipt.get('execution', receipt)
        query_sha = hashlib.sha256(task['reference_query'].encode()).hexdigest()
        if (receipt.get('id') != identifier or execution['status'] != 'OK'
                or execution.get('rollback_completed') is not True
                or execution.get('execution_summary_complete') is not True
                or execution.get('execution_query_type') != 'r' or execution.get('plan_query_type') != 'r'
                or execution.get('truncated') is not False
                or execution.get('query_sha256', execution.get('query_utf8_sha256')) != query_sha):
            raise ValueError('native query identity or complete read execution differs')
        if 'execution' in receipt:
            if (receipt.get('reference_query_utf8_sha256') != query_sha
                    or execution.get('full_json_rows_available') is not True
                    or execution.get('unsupported_json_rows') != 0
                    or execution.get('rows_file_sha256') != sha(rows_path)):
                raise ValueError('Retained exact-query complete output identity differs')
        elif (receipt.get('query') != task['reference_query']
                or receipt.get('full_rows_available') is not True
                or receipt.get('rows_sha256') != sha(rows_path)):
            raise ValueError('Captured exact-query complete output identity differs')
        positional = read(rows_path)
        columns = execution['columns']
        if (len(positional) != execution.get('rows_retained', execution.get('row_count_retained'))
                or len(set(columns)) != len(columns)
                or any(type(row) is not list or len(row) != len(columns) for row in positional)):
            raise ValueError('native row dimensions differ')
        run = json.loads(member(native['run_report_file']).read_text())
        run_items = [row for row in run['items'] if row['id'] == identifier]
        if len(run_items) != 1 or run_items[0].get('status') != 'OK':
            raise ValueError('Captured receipt not uniquely in successful native run')
        chain = native['chain']
        for name in chain.values():
            member(name)
        if 'execution' in receipt:
            if (run_items[0].get('receipt_sha256') != sha(receipt_path)
                    or run.get('source_inventory_unchanged') is not True
                    or run.get('frozen_manifest_sha256') != sha(bundle/chain['frozen_manifest.json'])
                    or run.get('input_manifest_sha256') != sha(bundle/chain['input_manifest.json'])
                    or run.get('new_model_calls') != 0 or run.get('domain_expert_validation') is not False):
                raise ValueError('Retained native provenance differs')
        else:
            inputs = read(bundle/chain['execution_inputs'])
            matching = [row for row in inputs if row['id'] == identifier]
            if (len(matching) != 1 or matching[0]['candidate_query'] != task['reference_query']
                    or run.get('input_sha256') != sha(bundle/chain['execution_inputs'])
                    or run.get('protocol_sha256') != sha(bundle/chain['execution_protocol'])
                    or run.get('inventory_unchanged') is not True
                    or run.get('model_calls') != 0 or run.get('expert_validation') is not False
                    or run_items[0].get('query_sha256') != query_sha
                    or run_items[0].get('rows') != len(positional)):
                raise ValueError('New native provenance differs')
        wg = identifier.split('_')[0]
        if 'source_before' in run:
            before, after = run['source_before'], run['source_after']
        else:
            before = next(row for row in run['source_guards_before'] if row['wg'] == wg)
            after = next(row for row in run['source_guards_after'] if row['wg'] == wg)
        if before != after or before != manifest['graph_sources'][wg]:
            raise ValueError('captured frozen source differs')
        source = task.get('portable_source_evidence')
        if source:
            archive = member(source['archive_file'])
            if sha(archive) != source['archive_sha256']:
                raise ValueError('Original source archive differs')
            with zipfile.ZipFile(archive) as zipped:
                source_member_bytes = zipped.read(source['member'])
            if hashlib.sha256(source_member_bytes).hexdigest() != source['member_sha256']:
                raise ValueError('Original source member differs')
        native_rows = [dict(zip(columns, row)) for row in positional]
        projected = []
        for row in native_rows:
            projected.append({field['name']: row[field['name']] if field['name'] in row
                              else row[field['source_column_or_expression']]
                              for field in task['required_fields']})
        g = gold[identifier]
        if (g['repair_sha256'] != task['repair_sha256'] or projected != g['records']
                or digest(projected) != task['projected_records_sha256']):
            raise ValueError('gold differs from actual requested-field projection')
        groups = original_scorer.make_order_groups(task, native_rows, projected) if task['collection']['kind'] in {
            'native_ordered_ties', 'top_k_boundary_ties'} else None
        if groups != g['order_groups']:
            raise ValueError('gold ordering/tie groups differ')
        actual_checks = contract_checks.checks(task, projected, groups)
        if checks[identifier]['checks'] != actual_checks or not all(c['pass'] for c in actual_checks):
            raise ValueError('actual scorer controls differ or fail')
        native_n += len(positional)
        controls_n += len(actual_checks)
    ledger = index(read(bundle/'all_core_dispositions.jsonl'))
    prior_ledger = index(read(parent/'all_core_dispositions.jsonl'))
    if len(ledger) != 560 or not set(ledger) <= set(originals) or set(ledger) != set(prior_ledger):
        raise ValueError('Full original 560 disposition scope differs')
    for identifier, disposition in ledger.items():
        if identifier in tasks:
            if (disposition['status'] != 'pass' or disposition['repair_sha256'] != tasks[identifier]['repair_sha256']
                    or prior_ledger[identifier]['status'] == 'pass'):
                raise ValueError('Additional ID disposition differs')
        elif disposition != prior_ledger[identifier]:
            raise ValueError('Prior disposition changed')
    if (set(manifest['cohort_ids']) != set(tasks) or len(manifest['cohort_ids']) != len(tasks)
            or len(tasks) != manifest['admitted_n'] or native_n != manifest['native_rows']
            or controls_n != manifest['actual_scorer_controls']
            or manifest['global_admitted_union_n'] != len(tasks) + len(previous)
            or manifest['global_unresolved_n'] != 560-len(tasks)-len(previous)):
        raise ValueError('additional accounting differs')
    return {'status': 'PASS', 'additional_admitted_n': len(tasks),
            'global_admitted_union_n': len(tasks) + len(previous), 'global_unresolved_n': 560-len(tasks)-len(previous),
            'repair_classes': dict(Counter(t['repair_class'] for t in tasks.values())),
            'native_rows': native_n, 'scorer_controls': controls_n,
            'model_prediction_scope': 'This repair bundle contains no model predictions; separately frozen model evidence is not counted by this verifier.',
            'human_author_review_completed': False, 'expert_validation_n': 0,
            'manifest_sha256': sha(bundle / 'manifest.json')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--parent', type=Path)
    args = parser.parse_args()
    parent = args.parent or args.bundle.parent / 'original_core_repair'
    print(json.dumps(verify(args.bundle, parent), ensure_ascii=False, indent=2))
