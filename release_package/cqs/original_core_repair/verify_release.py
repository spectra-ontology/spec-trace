#!/usr/bin/env python3
"""Offline checks of captured original-question repair evidence.

This checks stored definitions, judgments, native output and scoring behavior.
It does not execute a database, certify domain meaning or measure a model.
"""
from collections import Counter
import hashlib
import json
import re
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import scorer
import original_scorer
import review_schema
import contract_checks
import maximum_pool_checks

BASE = Path(__file__).resolve().parent
DEFINITION_KEYS = ('id', 'question_en', 'original_query', 'reference_query',
                   'required_fields', 'collection', 'cardinality_policy',
                   'repair_class', 'original_question_preserved')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def digest(value):
    return text_sha(scorer.get_kernel().json_exact(value))


def read(path):
    return [scorer.get_kernel().loads_exact(s) for s in path.read_text().splitlines() if s.strip()]


def index(rows):
    result = {}
    for row in rows:
        if row['id'] in result:
            raise ValueError('duplicate evidence ID: ' + row['id'])
        result[row['id']] = row
    return result


def project(rows, fields, columns):
    for field in fields:
        if field['name'] not in columns and field.get('source_column_or_expression') not in columns:
            raise ValueError('asked field has no returned source column')
    records = []
    for row in rows:
        record = {}
        for field in fields:
            name, source = field['name'], field['source_column_or_expression']
            if name in row:
                value = row[name]
                if source != name and source in row:
                    schema = scorer.get_kernel().field_schema(field)
                    semantics = field.get('nested_array_semantics')
                    if scorer.get_kernel().typed_token(value, schema, semantics) != scorer.get_kernel().typed_token(row[source], schema, semantics):
                        raise ValueError('returned alias and source disagree')
            elif source in row:
                value = row[source]
            else:
                raise ValueError('asked field absent from a captured native row')
            record[name] = value
        records.append(record)
    return records


def verify_uncapped_witness(task, candidate, native_records, order_groups, manifest):
    if task['id'] in maximum_pool_checks.REQUIRED_IDS:
        maximum_pool_checks.verify(BASE, task, native_records, manifest)
        return
    population = task['primary_review'].get('whole_population_evidence')
    needs_witness = population or (task['repair_class'] == 'scorer_only' and task['cardinality_policy']['mode'] == 'all'
                                  and re.search(r'\bLIMIT\b', task['reference_query'], re.I))
    witness = task.get('completeness_witness')
    if not needs_witness:
        if witness is not None:
            raise ValueError('unexpected coverage witness outside its declared scope')
        return
    if (not witness or witness['query'] != candidate['candidate_query']
            or witness['query_sha256'] != text_sha(witness['query'])
            or re.search(r'\bLIMIT\b', witness['query'], re.I)):
        raise ValueError('complete-question capped query lacks its exact uncapped witness')
    evidence = witness['portable_native_evidence']
    if not {evidence['receipt_file'], evidence['rows_file'], evidence['run_report_file']} <= set(manifest['files']):
        raise ValueError('manifest omits full uncapped coverage evidence')
    receipt = json.loads((BASE / evidence['receipt_file']).read_text())
    if (sha(BASE / evidence['receipt_file']) != evidence['receipt_sha256']
            or sha(BASE / evidence['rows_file']) != evidence['rows_sha256']
            or receipt['id'] != task['id'] or receipt['query'] != witness['query']
            or receipt['query_sha256'] != witness['query_sha256']
            or receipt['rows_sha256'] != evidence['rows_sha256']
            or receipt.get('status') != 'OK' or receipt.get('full_rows_available') is not True
            or receipt.get('truncated') is not False or receipt.get('rollback_completed') is not True
            or receipt.get('execution_summary_complete') is not True
            or receipt.get('execution_query_type') != 'r' or receipt.get('plan_query_type') != 'r'):
        raise ValueError('uncapped coverage receipt identity/completeness differs')
    columns = receipt['columns']; positional = read(BASE / evidence['rows_file'])
    if (len(set(columns)) != len(columns) or len(positional) != receipt['rows_retained']
            or any(type(row) is not list or len(row) != len(columns) for row in positional)):
        raise ValueError('uncapped coverage output dimensions differ')
    rows = [dict(zip(columns, row)) for row in positional]
    records = project(rows, task['required_fields'], columns)
    if (digest(records) != witness['projected_records_sha256']
            or not original_scorer.score(task, native_records, records, order_groups=order_groups)['exact']):
        raise ValueError('original query cap omits asked records')
    run = json.loads((BASE / evidence['run_report_file']).read_text())
    matches = [row for row in run['items'] if row['id'] == task['id']]
    if (run.get('inventory_unchanged') is not True or run['source_before'] != run['source_after']
            or run['source_before'] != manifest['graph_sources'][task['id'].split('_')[0]]
            or len(matches) != 1 or matches[0]['status'] != 'OK'
            or matches[0]['query_sha256'] != witness['query_sha256'] or matches[0]['rows'] != len(rows)):
        raise ValueError('uncapped coverage witness uses a different recorded source run')
    if population:
        path = BASE / 'provenance/frozen_ttl_import_manifest.json'
        inventory = json.loads(path.read_text())
        entries = [e for e in inventory['entries'] if e['working_group'] == task['id'].split('_')[0]]
        if (sha(path) != population['manifest_sha256'] or len(entries) != 1
                or entries[0]['source']['sha256'] != manifest['graph_sources'][task['id'].split('_')[0]]['source']['sha256']
                or entries[0]['parsed_inventory']['class_subjects'][population['class']] != population['global_class_nodes']
                or entries[0]['parsed_inventory']['relationship_predicates'][population['containment_predicate']] != population['global_containment_edges']
                or population['global_containment_edges'] != population['original_count']
                or population['original_count'] != population['captured_distinct_count']
                or evidence['rows_sha256'] != population['captured_distinct_rows_sha256']):
            raise ValueError('population-completeness evidence differs from pinned inventory/capture')


def verify():
    manifest = json.loads((BASE / 'manifest.json').read_text())
    required = {'tasks.jsonl', 'reference_gold.jsonl', 'all_core_dispositions.jsonl',
                'criteria.json', 'source_pins.json', 'scorer.py', 'typed_values.py',
                'original_scorer.py', 'review_schema.py', 'verify_release.py', 'contract_checks.py',
                'provenance/original_benchmark.jsonl', 'provenance/original_answer_contract.jsonl',
                'provenance/candidate_definitions.jsonl', 'provenance/scorer_checks.jsonl',
                'provenance/validation.json', 'provenance/retained_frozen_manifest.json',
                'provenance/retained_input_manifest.json', 'provenance/retained_original_run.json',
                'provenance/historical_original_diagnostic_admission.json',
                'provenance/frozen_ttl_import_manifest.json',
                'provenance/ran12_source_semantics.py', 'provenance/ran12_source_semantics.json'}
    if not required <= set(manifest['files']):
        raise ValueError('manifest omits required repair evidence')
    for relative, expected in manifest['files'].items():
        path = (BASE / relative).resolve()
        if not path.is_relative_to(BASE.resolve()) or not path.is_file() or sha(path) != expected:
            raise ValueError('file integrity mismatch: ' + relative)
    source_scan = json.loads((BASE / 'provenance/ran12_source_semantics.json').read_text())
    if set(source_scan) != {'RAN1', 'RAN2'}:
        raise ValueError('source-population scan scope differs')
    for wg, row in source_scan.items():
        guard = manifest['graph_sources'][wg]
        if (row['scanner_sha256'] != sha(BASE / 'provenance/ran12_source_semantics.py')
                or row['graph_source_sha256'] != guard['source']['sha256']
                or row['loader_sha256'] != guard['shipped_loader_sha256']
                or row['nodes'] != guard['nodes'] or row['relationships'] != guard['relationships']):
            raise ValueError('source-population scan provenance differs: ' + wg)
    original_path = BASE / 'provenance/original_benchmark.jsonl'
    contract_path = BASE / 'provenance/original_answer_contract.jsonl'
    # These identify the unchanged original release, rather than a generated subset.
    if (sha(original_path) != '8fca9e16b39b387590e04d44d6e2bb6aa2189e5ab1745d7b7729c431e18af2ef'
            or sha(contract_path) != 'e0caeed9fb4203c4517977cc61f257eebd1da49b80bd53bcd6d8111a352a7d9b'):
        raise ValueError('original release source identity differs')
    originals = index(read(original_path))
    original_contracts = index([row for row in read(contract_path) if 'id' in row])
    candidates = index(read(BASE / 'provenance/candidate_definitions.jsonl'))
    additional_path = BASE / 'provenance/additional_definitions.jsonl'
    additional = index(read(additional_path)) if additional_path.exists() else {}
    tasks = index(read(BASE / 'tasks.jsonl'))
    gold = index(read(BASE / 'reference_gold.jsonl'))
    dispositions = index(read(BASE / 'all_core_dispositions.jsonl'))
    recorded_checks = index(read(BASE / 'provenance/scorer_checks.jsonl'))
    if (len(original_contracts) != 560 or set(dispositions) != set(original_contracts)
            or set(tasks) != set(gold) or set(tasks) != {id for id, row in dispositions.items() if row['status'] == 'pass'}
            or not set(tasks) <= set(original_contracts)):
        raise ValueError('original Core identity/disposition accounting failed')
    criteria = json.loads((BASE / 'criteria.json').read_text())
    criteria_sha = sha(BASE / 'criteria.json')
    if criteria_sha != 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4':
        raise ValueError('fixed original-question review criteria changed')
    native_rows, formal_empty, check_count = 0, 0, 0
    for id, task in tasks.items():
        original = originals[id]
        definition = {key: task[key] for key in DEFINITION_KEYS}
        repair_sha = digest(definition)
        query_sha = text_sha(task['reference_query'])
        if (task['question_en'] != original['question_en'] or task['original_query'] != original['cypher']
                or task['original_question_sha256'] != text_sha(original['question_en'])
                or task['original_query_sha256'] != text_sha(original['cypher'])
                or task['reference_query_sha256'] != query_sha
                or task['repair_sha256'] != repair_sha or gold[id]['repair_sha256'] != repair_sha
                or dispositions[id]['repair_sha256'] != repair_sha
                or task['criteria_sha256'] != criteria_sha
                or task.get('original_question_preserved') is not True
                or task['repair_class'] != ('scorer_only' if task['reference_query'] == original['cypher'] else 'query_and_scorer')):
            raise ValueError('original question or repair definition identity mismatch: ' + id)
        primary, secondary = task['primary_review'], task['secondary_review']
        if id in additional:
            proposed = additional[id]
            if digest({key: proposed[key] for key in DEFINITION_KEYS}) != repair_sha:
                raise ValueError('additional proposal differs from its admitted definition')
            candidate = {'candidate_query': proposed['reference_query']}
            review_schema.check_pass(primary, original['question_en'], criteria['semantic_units'],
                                     criteria_sha=criteria_sha, identity_key='repair_sha256', identity_sha=repair_sha)
        else:
            candidate = candidates[id]
            candidate_sha = text_sha(json.dumps(candidate, ensure_ascii=False, sort_keys=True, separators=(',', ':')))
            primary_fields = [dict(field) for field in primary['required_fields']]
            for field in primary_fields:
                if 'nested_semantics' in field and 'nested_array_semantics' not in field:
                    field['nested_array_semantics'] = field.pop('nested_semantics')
            primary_query = original['cypher'] if primary['query_choice'] == 'original' else candidate['candidate_query']
            if (primary_query != task['reference_query'] or primary['repair_class'] != task['repair_class']
                    or digest(primary_fields) != digest(task['required_fields'])
                    or digest(primary['collection']) != digest(task['collection'])
                    or digest(primary['cardinality_policy']) != digest(task['cardinality_policy'])):
                raise ValueError('primary judgment concerns a different repaired contract: ' + id)
            review_schema.check_pass(primary, original['question_en'], criteria['semantic_units'],
                                     criteria_sha=criteria_sha, identity_key='definition_sha256', identity_sha=candidate_sha)
        for review in (primary, secondary):
            if review.get('id') != id:
                raise ValueError('review attached to another task')
        review_schema.check_pass(secondary, original['question_en'], criteria['semantic_units'],
                                 criteria_sha=criteria_sha, identity_key='repair_sha256', identity_sha=repair_sha)
        if (task.get('validation_status') != 'validated' or task.get('human_author_review_completed') is not False
                or task.get('expert_validation_n') != 0 or task.get('model_calls') != 0):
            raise ValueError('unsupported validation scope: ' + id)
        evidence = task['portable_native_evidence']
        receipt_path, rows_path = evidence['receipt_file'], evidence['rows_file']
        if not {receipt_path, rows_path, evidence['run_report_file']} <= set(manifest['files']):
            raise ValueError('manifest omits complete native execution evidence: ' + id)
        receipt = json.loads((BASE / receipt_path).read_text())
        if sha(BASE / receipt_path) != evidence['receipt_sha256'] or sha(BASE / rows_path) != evidence['rows_sha256']:
            raise ValueError('native evidence differs from its actual captured bytes: ' + id)
        if evidence['source_kind'] == 'retained_original_query':
            execution = receipt['execution']
            if (receipt['id'] != id or receipt['reference_query_utf8_sha256'] != query_sha
                    or receipt['original_question'] != original['question_en']
                    or receipt['original_question_utf8_sha256'] != text_sha(original['question_en'])
                    or execution['query_utf8_sha256'] != query_sha or execution.get('full_json_rows_available') is not True
                    or execution.get('rows_file_sha256') != evidence['rows_sha256']):
                raise ValueError('original-query native capture identity differs: ' + id)
            columns = execution['columns']; retained = execution['row_count_retained']
            run = json.loads((BASE / evidence['run_report_file']).read_text())
            matches = [row for row in run['items'] if row['id'] == id]
            if (run.get('source_inventory_unchanged') is not True or len(matches) != 1
                    or matches[0].get('status') != 'OK' or matches[0]['receipt_sha256'] != evidence['receipt_sha256']):
                raise ValueError('original-query recorded run identity differs: ' + id)
            guards = [row for row in run['source_guards_before'] if row['wg'] == id.split('_')[0]]
            if (run['source_guards_before'] != run['source_guards_after'] or len(guards) != 1
                    or guards[0] != manifest['graph_sources'][id.split('_')[0]]
                    or run['frozen_manifest_sha256'] != sha(BASE / 'provenance/retained_frozen_manifest.json')
                    or run['input_manifest_sha256'] != sha(BASE / 'provenance/retained_input_manifest.json')
                    or type(run.get('new_model_calls')) is not int or run['new_model_calls'] != 0
                    or run.get('domain_expert_validation') is not False):
                raise ValueError('original run source guards differ')
        elif evidence['source_kind'] == 'captured_repaired_query':
            execution = receipt
            if (receipt.get('id') != id or receipt.get('query') != task['reference_query']
                    or receipt.get('query_sha256') != query_sha or receipt.get('full_rows_available') is not True
                    or receipt.get('rows_sha256') != evidence['rows_sha256']):
                raise ValueError('repaired-query native capture identity differs: ' + id)
            columns = receipt['columns']; retained = receipt['rows_retained']
            run = json.loads((BASE / evidence['run_report_file']).read_text())
            matches = [row for row in run['items'] if row['id'] == id]
            if (run.get('inventory_unchanged') is not True or run['source_before'] != run['source_after']
                    or run['source_before'] != manifest['graph_sources'][id.split('_')[0]]
                    or len(matches) != 1 or matches[0].get('status') != 'OK'
                    or matches[0]['query_sha256'] != query_sha or matches[0]['rows'] != retained):
                raise ValueError('repaired-query recorded run identity differs: ' + id)
        else:
            raise ValueError('unrecognized native evidence source')
        if (execution.get('status') != 'OK' or execution.get('truncated') is not False
                or execution.get('rollback_completed') is not True
                or execution.get('execution_summary_complete') is not True
                or execution.get('execution_query_type') != 'r' or execution.get('plan_query_type') != 'r'):
            raise ValueError('captured native execution is incomplete: ' + id)
        positional = read(BASE / rows_path)
        if (len(set(columns)) != len(columns) or len(positional) != retained
                or any(type(row) is not list or len(row) != len(columns) for row in positional)):
            raise ValueError('captured native dimensions differ: ' + id)
        rows = [dict(zip(columns, row)) for row in positional]
        records = project(rows, task['required_fields'], columns)
        groups = None
        if task['collection']['kind'] in {'native_ordered_ties', 'top_k_boundary_ties'}:
            if any(key['source_column'] not in columns for key in task['collection']['source_order_keys']):
                raise ValueError('native order key lacks a returned column')
            groups = original_scorer.make_order_groups(task, rows, records)
        if (digest(records) != task['projected_records_sha256']
                or scorer.get_kernel().json_exact(records) != scorer.get_kernel().json_exact(gold[id]['records'])
                or scorer.get_kernel().json_exact(groups) != scorer.get_kernel().json_exact(gold[id]['order_groups'])
                or not original_scorer.score(task, records, original_scorer.reference_prediction(task, records), order_groups=groups)['exact']):
            raise ValueError('gold or ordering differs from actual native projection: ' + id)
        verify_uncapped_witness(task, candidate, records, groups, manifest)
        outcome = recorded_checks[id]
        replayed = contract_checks.checks(task, records, groups)
        if (outcome.get('pass') is not True or outcome['repair_sha256'] != repair_sha
                or not outcome.get('checks') or any(row.get('pass') is not True for row in outcome['checks'])
                or digest(replayed) != digest(outcome['checks'])):
            raise ValueError('recorded per-item negative/control checks are incomplete')
        native_rows += len(rows); formal_empty += not records; check_count += len(outcome['checks'])
    report = json.loads((BASE / 'provenance/validation.json').read_text())
    historical = json.loads((BASE / 'provenance/historical_original_diagnostic_admission.json').read_text())
    historical_ids = set(historical['fixed_cohort_ids'])
    overlap = len(set(tasks) & historical_ids)
    outside = len(set(tasks) - historical_ids)
    classes = dict(Counter(task['repair_class'] for task in tasks.values()))
    if (manifest['registered_original_n'] != 560 or manifest['admitted_n'] != len(tasks)
            or manifest['native_rows'] != native_rows or manifest['repair_classes'] != classes
            or manifest['full_original_core_complete'] is not (len(tasks) == 560)
            or report['admitted_n'] != len(tasks) or report['repair_classes'] != classes
            or report['native_rows'] != native_rows or manifest['model_calls'] != 0
            or report['scorer_check_count'] != check_count
            or manifest['dispositions'] != dict(Counter(row['status'] for row in dispositions.values()))
            or report['dispositions'] != dict(Counter(row['status'] for row in dispositions.values()))
            or len(historical_ids) != 31 or not historical_ids <= set(dispositions)
            or report['historical_31_overlap_n'] != overlap or report['admitted_outside_historical_31_n'] != outside
            or manifest['historical_31_overlap_n'] != overlap or manifest['admitted_outside_historical_31_n'] != outside
            or manifest['expert_validation_n'] != 0 or manifest['human_author_review_completed'] is not False):
        raise ValueError('reported coverage or validation scope differs from actual evidence')
    result = {'pass': True, 'kind': 'Offline stored-evidence checks; two AI semantic judgments, no human/expert certification or model performance',
              'registered_original_n': 560, 'admitted_n': len(tasks), 'repair_classes': classes,
              'native_rows': native_rows, 'formal_empty_answers': formal_empty,
              'scorer_check_count': check_count, 'full_original_core_complete': len(tasks) == 560,
              'historical_31_overlap_n': overlap, 'admitted_outside_historical_31_n': outside,
              'model_calls': 0, 'expert_validation_n': 0, 'human_author_review_completed': False}
    print(json.dumps(result, ensure_ascii=False))
    return result


if __name__ == '__main__':
    verify()
