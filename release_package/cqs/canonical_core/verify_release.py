#!/usr/bin/env python3
"""Offline integrity/contract verification of the revised canonical Core.

No model calls, graph access, author endorsement or independent expert review.
The manifest is an integrity inventory, not a cryptographic attestation.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import scorer

BASE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def read_lines(path):
    return [scorer.get_kernel().loads_exact(x) for x in path.read_text().splitlines() if x.strip()]


def unique(rows):
    result = {}
    for row in rows:
        if row['id'] in result:
            raise ValueError('duplicate ID: '+row['id'])
        result[row['id']] = row
    return result


def project(rows, fields, columns):
    for field in fields:
        if field['name'] not in columns and field.get('source_column_or_expression') not in columns:
            raise ValueError('declared role absent from native columns')
    records = []
    for row in rows:
        record = {}
        for field in fields:
            name = field['name']; source = field.get('source_column_or_expression')
            if name in row:
                value = row[name]
                if source != name and source in row:
                    schema = scorer.get_kernel().field_schema(field)
                    semantics = field.get('nested_array_semantics')
                    if scorer.get_kernel().typed_token(value, schema, semantics) != scorer.get_kernel().typed_token(row[source], schema, semantics):
                        raise ValueError('native alias/source collision')
            elif source in row:
                value = row[source]
            else:
                raise ValueError('required role missing from native row')
            record[name] = value
        records.append(record)
    return records


def verify():
    manifest = json.loads((BASE/'manifest.json').read_text())
    required = {'canonical_tasks.jsonl','canonical_reference_gold.jsonl','scorer.py','typed_values.py',
                'source_pins.json','criteria.json','provenance/definitions.jsonl','provenance/reviews.jsonl',
                'provenance/original_benchmark.jsonl','provenance/original_answer_contract.jsonl','migration.jsonl'}
    if not required <= set(manifest['files']):
        raise ValueError('manifest omits required contract inputs')
    for relative, expected in manifest['files'].items():
        path = (BASE/relative).resolve()
        if not path.is_relative_to(BASE.resolve()) or not path.is_file() or sha(path) != expected:
            raise ValueError('file integrity mismatch: '+relative)
    tasks = unique(read_lines(BASE/'canonical_tasks.jsonl'))
    gold = unique(read_lines(BASE/'canonical_reference_gold.jsonl'))
    definitions = unique(read_lines(BASE/'provenance/definitions.jsonl'))
    reviews = unique(read_lines(BASE/'provenance/reviews.jsonl'))
    original = unique(read_lines(BASE/'provenance/original_benchmark.jsonl'))
    original_contracts = unique([r for r in read_lines(BASE/'provenance/original_answer_contract.jsonl') if 'id' in r])
    migrations = unique(read_lines(BASE/'migration.jsonl'))
    if not (len(tasks)==560 and set(tasks)==set(gold)==set(definitions)==set(reviews)==set(original_contracts)==set(migrations)):
        raise ValueError('complete Core identity accounting failed')
    semantic_keys = ['id','candidate_question','candidate_query','required_fields','collection',
                     'cardinality_policy','original_intent_change','status','original_question','original_query']
    native_rows = 0
    empty_answers = 0
    gates = json.loads((BASE/'criteria.json').read_text())['completion_gates']
    for id, task in tasks.items():
        definition = definitions[id]
        definition_sha = text_sha(json.dumps(definition, ensure_ascii=False, sort_keys=True, separators=(',',':')))
        if task['definition_sha256'] != definition_sha or gold[id]['definition_sha256'] != definition_sha:
            raise ValueError('definition hash mismatch: '+id)
        migration=migrations[id]
        if (migration['definition_sha256'] != definition_sha
                or migration['historical_question_sha256'] != text_sha(original[id]['question_en'])
                or migration['historical_query_sha256'] != text_sha(original[id]['cypher'])
                or migration['original_intent_change'] != task['original_intent_change']
                or migration['substantive_original_intent_unresolved'] is not (task['original_intent_change']=='substantive_variant')
                or migration['remaining_author_semantic_review'] is not True
                or migration['requires_fresh_predictions'] is not True):
            raise ValueError('migration scope mismatch: '+id)
        for key in semantic_keys:
            left, right = task[key], definition[key]
            if key == 'required_fields':
                right = [dict(f) for f in right]
                for field in right:
                    if 'nested_semantics' in field and 'nested_array_semantics' not in field:
                        field['nested_array_semantics'] = field.pop('nested_semantics')
            if scorer.get_kernel().json_exact(left) != scorer.get_kernel().json_exact(right):
                raise ValueError('canonical definition changed: '+id+'/'+key)
        if (task['original_question'] != original[id]['question_en']
                or task['original_query'] != original[id]['cypher']):
            raise ValueError('historical identity changed: '+id)
        if (task['wg'] != id.split('_')[0] or task['wg'] != original[id]['wg']
                or definition.get('wg',task['wg']) != task['wg']):
            raise ValueError('working-group identity mismatch: '+id)
        review = reviews[id]
        if (review['definition_sha256'] != definition_sha or review['decision'] != 'pass'
                or not review.get('reasoning') or not review.get('review_scope')
                or review.get('remaining_author_semantic_review') is not True):
            raise ValueError('current scoped AI cross-review missing: '+id)
        if task.get('validation_status') != 'validated' or gold[id].get('validation_status') != 'validated':
            raise ValueError('technical validation incomplete: '+id)
        if (task['status'] not in {'retain','repair'} or task.get('blockers') != []
                or task.get('unresolved_reasons') != []
                or any(task.get('gates',{}).get(gate)!='pass' for gate in gates)):
            raise ValueError('technical admission gates incomplete: '+id)
        if task.get('remaining_author_semantic_review') is not True or task.get('expert_validation') is not False:
            raise ValueError('author/expert scope changed: '+id)
        query_sha = text_sha(task['candidate_query'])
        if gold[id]['query_sha256'] != query_sha:
            raise ValueError('gold query mismatch: '+id)
        relative = Path('reference_outputs')/id/(query_sha+'.json')
        receipt = json.loads((BASE/relative).read_text())
        expected_rows = str(relative.with_suffix('.jsonl'))
        execution_relative = 'provenance/execution_'+task['wg']+'.json'
        if not {str(relative),expected_rows,execution_relative} <= set(manifest['files']):
            raise ValueError('manifest omits native execution evidence: '+id)
        if (receipt['id'] != id or receipt['wg'] != task['wg']
                or receipt['query'] != task['candidate_query'] or receipt['query_sha256'] != query_sha
                or receipt['rows_file'] != expected_rows or receipt['rows_sha256'] != sha(BASE/expected_rows)
                or receipt.get('status') != 'OK' or receipt.get('full_rows_available') is not True
                or receipt.get('truncated') is not False or receipt.get('rollback_completed') is not True
                or receipt.get('execution_summary_complete') is not True
                or receipt.get('execution_query_type') != 'r' or receipt.get('plan_query_type') != 'r'):
            raise ValueError('complete read-only native receipt mismatch: '+id)
        positional = read_lines(BASE/expected_rows)
        columns = receipt['columns']
        if len(set(columns)) != len(columns) or len(positional) != receipt['rows_retained']:
            raise ValueError('native output dimensions invalid: '+id)
        if any(type(row) is not list or len(row) != len(columns) for row in positional):
            raise ValueError('native row dimension invalid: '+id)
        rows = [dict(zip(columns,row)) for row in positional]
        projected = project(rows,task['required_fields'],columns)
        if scorer.get_kernel().json_exact(projected) != scorer.get_kernel().json_exact(gold[id]['records']):
            raise ValueError('gold differs from native projection: '+id)
        if not scorer.score(task,projected,projected)['exact']:
            raise ValueError('reference violates declared contract: '+id)
        execution = json.loads((BASE/execution_relative).read_text())
        if (execution.get('inventory_unchanged') is not True
                or execution['source_before'] != execution['source_after']
                or execution['source_before'] != manifest['graph_sources'][task['wg']]):
            raise ValueError('graph source guard mismatch: '+id)
        matches = [r for r in execution['items'] if r['id']==id]
        if len(matches)!=1 or matches[0]['query_sha256'] != query_sha or matches[0]['status']!='OK' or matches[0]['rows']!=len(rows):
            raise ValueError('execution report/reference mismatch: '+id)
        native_rows += len(rows)
        empty_answers += not projected
    changes = dict(Counter(r['original_intent_change'] for r in tasks.values()))
    if (manifest['n'] != len(tasks) or manifest['native_rows'] != native_rows
            or manifest['intent_change'] != changes or manifest['model_calls'] != 0
            or manifest['expert_validation_n'] != 0 or manifest['actual_author_review_completed'] is not False
            or manifest['full_original_core_complete'] is not False):
        raise ValueError('unsupported scope claim')
    report = {'kind':'offline integrity and technical contract verification; not model performance',
              'pass':True,'n':len(tasks),'native_rows':native_rows,'formal_empty_answers':empty_answers,
              'intent_change':changes,'model_calls':0,'expert_validation_n':0,
              'actual_author_review_completed':False,'full_original_core_complete':False}
    print(json.dumps(report,ensure_ascii=False))
    return report


if __name__=='__main__':
    verify()
