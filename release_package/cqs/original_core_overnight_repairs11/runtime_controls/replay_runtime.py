"""Replay three source-free contract shapes through unchanged runtime code.

Only a temporary synthetic SQLite file is queried. Native execution, passage
retrieval and model responses are explicit test doubles. An empty temporary
.git marker satisfies the unchanged modules' repository-root initializer; it
does not access a real repository, research source, credential or network.
"""
from pathlib import Path
from decimal import Decimal
import argparse
import hashlib
import importlib
import json
import shutil
import sqlite3
import sys
import tempfile

sys.dont_write_bytecode = True


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    assert not args.out.exists(), 'receipt must be new'
    base = Path(__file__).resolve().parent
    manifest = json.loads((base / 'manifest.json').read_text())
    for relative, pin in manifest['files'].items():
        expected = pin if isinstance(pin, str) else pin['sha256']
        assert digest(base / relative) == expected, relative
    tests = []

    def check(name, condition):
        assert condition, name
        tests.append({'name': name, 'pass': True})

    with tempfile.TemporaryDirectory(prefix='auth11-source-free-three-case-') as name:
        temporary = Path(name)
        workspace = temporary / 'synthetic_workspace'
        workspace.mkdir()
        (workspace / '.git').mkdir()
        for folder in ('runtime', 'bundle_scorer'):
            shutil.copytree(base / folder, workspace / folder)
        sys.path[:0] = [str(workspace / 'runtime'), str(workspace / 'bundle_scorer')]
        runtime = importlib.import_module('run_evaluation')
        structured = importlib.import_module('structured_adapter')
        retrieval = importlib.import_module('retrieval_adapter')
        share = importlib.import_module('share_runtime_adapter')
        codec = importlib.import_module('rational_share_records')
        score_predictions = importlib.import_module('score_predictions')
        check('unchanged_runtime_imported_from_temporary_synthetic_workspace', runtime.ROOT == workspace)
        check('V8_hooks_installed_automatically', runtime._cohort_exact_share_hooks_installed is True)
        lexical = '0.100000000000000005'
        expected_pair = codec.rational(Decimal(lexical))
        expected_count = expected_pair['numerator']
        samsung_id, huawei_id, ordinary_id = ('RAN1_P2_CQ3-2', 'RAN2_P2_CQ3-1', 'RAN1_P1_CQ2-6')

        def share_task(identifier, field, count=False):
            fields = ([{'name': 'agreementLinkedTdocCount', 'type': 'integer', 'nullable': False}] if count else [])
            fields += [{'name': field, 'type': 'json', 'nullable': False, 'json_schema': codec.PAIR_SCHEMA}]
            return {'id': identifier, 'repair_sha256': 'source-free-synthetic-' + identifier,
                    'validation_status': 'validated', 'question_en': 'Return synthetic required roles only.',
                    'required_fields': fields,
                    'collection': {'kind': 'set', 'rational_share_representation': {
                        'kind': 'exact_rational_share', 'unit': 'one', 'field': field}},
                    'cardinality_policy': {'mode': 'all'}}

        samsung = share_task(samsung_id, 'agreementLinkedTdocShare', True)
        huawei = share_task(huawei_id, 'resolutionLinkedTdocShare')
        ordinary = {'id': ordinary_id, 'repair_sha256': 'source-free-synthetic-' + ordinary_id,
            'validation_status': 'validated', 'question_en': 'List ten synthetic identities in recorded order.',
            'required_fields': [{'name': 'tdocNumber', 'type': 'string', 'nullable': False}],
            'collection': {'kind': 'top_k_boundary_ties', 'value': 10,
                'tie_policy': 'any_subset_at_boundary', 'within_tie_order': 'any', 'require_rank_order': True,
                'source_order_keys': [{'source_column': 'tdocNumber', 'direction': 'asc'}]},
            'cardinality_policy': {'mode': 'top_k', 'value': 10, 'tie_policy': 'any_subset_at_boundary'}}
        definitions = [samsung, huawei, ordinary]
        publics = {t['id']: runtime.public_task(t) for t in definitions}
        samsung_row = {'agreementLinkedTdocCount': expected_count, 'agreementLinkedTdocShare': expected_pair}
        huawei_row = {'resolutionLinkedTdocShare': expected_pair}
        ordinary_full = [{'tdocNumber': 'SYNTHETIC-%03d' % i} for i in range(1, 13)]
        ordinary_top10 = ordinary_full[:10]
        gold_rows = {samsung_id: [samsung_row], huawei_id: [huawei_row], ordinary_id: ordinary_full}
        expected_rows = {samsung_id: [samsung_row], huawei_id: [huawei_row], ordinary_id: ordinary_top10}

        for task in definitions:
            identifier, public = task['id'], publics[task['id']]
            check(identifier + '_required_roles_survive_real_public_task',
                  [f['name'] for f in public['required_fields']] == [f['name'] for f in task['required_fields']])
            check(identifier + '_private_query_and_hashes_not_disclosed',
                  'reference_query' not in public and 'normalizer_sha256' not in json.dumps(public))
            if identifier == ordinary_id:
                check('ordinary_recorded_source_order_keys_unchanged', public['collection']['source_order_keys'] == ordinary['collection']['source_order_keys'])
                check('ordinary_default_top10_cardinality_unchanged', public['cardinality_policy'] == ordinary['cardinality_policy'])
                check('ordinary_has_no_share_descriptor_or_field_marker', 'rational_share_representation' not in public['collection'] and all('value_representation' not in f for f in public['required_fields']))
            else:
                descriptor = task['collection']['rational_share_representation']
                check(identifier + '_sanitized_public_descriptor', public['collection']['rational_share_representation'] == descriptor)
                markers = [f['name'] for f in public['required_fields'] if 'value_representation' in f]
                check(identifier + '_only_share_field_has_decoder_marker', markers == [descriptor['field']])
                if identifier == samsung_id:
                    check('Samsung_mandatory_count_integer_and_nullable_contract_unchanged', public['required_fields'][0] == samsung['required_fields'][0])
            for method, schema in [('A', 'graph_schema'), ('B', 'sql_schema')]:
                messages = structured.messages_for(dict(public, **{schema: {'synthetic': 'no-source-values'}}), method)
                visible = json.loads(messages[1]['content'])['output_format']
                check(identifier + '_' + method + '_actual_prompt_required_roles', [f['name'] for f in visible['required_fields']] == [f['name'] for f in public['required_fields']])
                if identifier != ordinary_id:
                    check(identifier + '_' + method + '_actual_prompt_share_units', visible['value_representations'] == [codec.public_representation(public)])
            contract = retrieval.public_contract(public)
            check(identifier + '_C_D_actual_contract_required_roles', [f['name'] for f in contract['required_fields']] == [f['name'] for f in public['required_fields']])
            if identifier != ordinary_id:
                check(identifier + '_C_D_actual_contract_share_units', contract['value_representations'] == [codec.public_representation(public)])

        db = temporary / 'synthetic.sqlite3'
        connection = sqlite3.connect(db)
        connection.execute('CREATE TABLE synthetic_share(n INTEGER, value TEXT)')
        connection.execute('INSERT INTO synthetic_share VALUES (?,?)', (expected_count, lexical))
        connection.execute('CREATE TABLE synthetic_docs(tdocNumber TEXT)')
        connection.executemany('INSERT INTO synthetic_docs VALUES (?)', [(r['tdocNumber'],) for r in ordinary_full])
        connection.commit(); connection.close()
        before_db = digest(db)
        queries = {
            samsung_id: 'SELECT n AS agreementLinkedTdocCount, value AS agreementLinkedTdocShare FROM synthetic_share',
            huawei_id: 'SELECT value AS resolutionLinkedTdocShare FROM synthetic_share',
            ordinary_id: 'SELECT tdocNumber FROM synthetic_docs ORDER BY tdocNumber ASC LIMIT 10'}
        results = {method: {} for method in 'ABCD'}
        for task in definitions:
            identifier, public = task['id'], publics[task['id']]
            query = queries[identifier]
            record = {'id': identifier, 'repair_sha256': public['repair_sha256'], 'method': 'Text2SQL',
                'status': 'QUERY_READY', 'generated_query': query, 'query_sha256': hashlib.sha256(query.encode()).hexdigest(), 'wg': public['wg']}
            executed = structured.execute_generated(record, public, sql_db=db)
            check(identifier + '_B_actual_immutable_SQLite_assembly', executed['status'] == 'OK' and executed['records'] == expected_rows[identifier])
            check(identifier + '_B_actual_SQLite_read_guard', executed['execution']['immutable_read_only'] is True)
            results['B'][identifier] = executed['records']
            if identifier == samsung_id:
                check('Samsung_B_assembly_preserves_large_exact_integer_count', executed['records'][0]['agreementLinkedTdocCount'] == expected_count and type(executed['records'][0]['agreementLinkedTdocCount']) is int)
            raw_native = [dict(row) for row in expected_rows[identifier]]
            if identifier != ordinary_id:
                field = task['collection']['rational_share_representation']['field']
                raw_native[0][field] = {k: v * 2 for k, v in expected_pair.items()}
            structured.run_cypher_query = lambda *a, _rows=raw_native, **k: {'status': 'OK', 'rows': _rows, 'complete': True}
            native_record = dict(record, method='Text2Cypher', generated_query='synthetic-native-stub', query_sha256=hashlib.sha256(b'synthetic-native-stub').hexdigest())
            executed_a = structured.execute_generated(native_record, public)
            check(identifier + '_A_actual_assembly_stub_no_native_call', executed_a['status'] == 'OK' and executed_a['records'] == expected_rows[identifier])
            results['A'][identifier] = executed_a['records']
            if identifier == samsung_id:
                check('Samsung_A_pair_reduction_does_not_change_required_count', executed_a['records'][0]['agreementLinkedTdocCount'] == expected_count)

        check('temporary_SQLite_bytes_preserved_by_all_actual_reads', digest(db) == before_db)
        retrieval.prepare_corpus_inventory = lambda *a, **k: {'shards': [{'WG': 'RAN1', 'path': 'synthetic-unused', 'sha256': 'synthetic'}, {'WG': 'RAN2', 'path': 'synthetic-unused', 'sha256': 'synthetic'}]}
        retrieval.retrieve = lambda *a, **k: {'status': 'ok', 'context_candidate_truncated': False}
        retrieval.contexts = lambda *a, **k: ([], {'document_selection_truncated': False})

        class Caller:
            def __init__(self, content):
                self.content, self.messages = content, []

            def call(self, key, messages, **kwargs):
                self.messages.append((key, messages))
                content = '{"query":"synthetic"}' if key.endswith('followup') else self.content
                return {'ok': True, 'finish_reason': 'stop', 'content': content}

        for task in definitions:
            identifier, public = task['id'], publics[task['id']]
            if identifier == ordinary_id:
                content = json.dumps({'records': ordinary_top10, 'abstain': False, 'complete': True})
            elif identifier == samsung_id:
                content = '{"records":[{"agreementLinkedTdocCount":%d,"agreementLinkedTdocShare":%s},{"agreementLinkedTdocCount":%d,"agreementLinkedTdocShare":"invalid"}],"abstain":false,"complete":true}' % (expected_count, lexical, expected_count)
            else:
                content = '{"records":[{"resolutionLinkedTdocShare":%s},{"resolutionLinkedTdocShare":"invalid"}],"abstain":false,"complete":true}' % lexical
            for method in 'CD':
                caller = Caller(content)
                outcome = retrieval.evaluate(public, method, caller, temporary)
                check(identifier + '_' + method + '_actual_evaluate_valid_first_record', outcome['status'] == 'ok' and outcome['records'][0] == expected_rows[identifier][0])
                if identifier != ordinary_id:
                    check(identifier + '_' + method + '_invalid_extra_row_preserves_valid_partial_record', len(outcome['records']) == 2)
                else:
                    check(identifier + '_' + method + '_ordinary_default10_records_unchanged', outcome['records'] == ordinary_top10)
                prompt = json.loads(caller.messages[-1][1][1]['content'].split('\nSOURCE PASSAGES:', 1)[0])['contract']
                check(identifier + '_' + method + '_actual_answer_prompt_required_roles', [f['name'] for f in prompt['required_fields']] == [f['name'] for f in public['required_fields']])
                if identifier != ordinary_id:
                    check(identifier + '_' + method + '_actual_answer_prompt_same_share_units', prompt['value_representations'] == [codec.public_representation(public)])
                results[method][identifier] = outcome['records']

        task_file, gold_file, pred_file = [temporary / filename for filename in ('tasks.jsonl', 'gold.jsonl', 'predictions.jsonl')]
        task_file.write_text(''.join(json.dumps(task) + '\n' for task in definitions))
        gold_file.write_text(''.join(json.dumps({'id': t['id'], 'repair_sha256': t['repair_sha256'], 'records': gold_rows[t['id']], 'order_groups': [[r] for r in ordinary_full] if t['id'] == ordinary_id else []}) + '\n' for t in definitions))

        def actual_score(rows):
            pred_file.write_text(''.join(json.dumps({'id': task['id'], 'repair_sha256': task['repair_sha256'], 'records': rows[task['id']]}) + '\n' for task in definitions))
            return {row['id']: row for row in score_predictions.run(task_file, gold_file, pred_file)['outcomes']}

        for method in 'ABCD':
            scored = actual_score(results[method])
            for identifier in (samsung_id, huawei_id):
                exact = method in 'AB'
                check(identifier + '_' + method + '_actual_declared_codec_and_original_scorer', scored[identifier]['exact'] is exact and scored[identifier]['f1'] == (1.0 if exact else 2 / 3))
            check(method + '_ordinary_task_exact_same_original_scorer', scored[ordinary_id]['exact'] is True and scored[ordinary_id]['f1'] == 1.0)
        pristine = {identifier: list(rows) for identifier, rows in expected_rows.items()}
        for label, changed in [('missing_count', {'agreementLinkedTdocShare': expected_pair}),
                               ('wrong_count', dict(samsung_row, agreementLinkedTdocCount=expected_count + 1)),
                               ('missing_share', {'agreementLinkedTdocCount': expected_count})]:
            mutated = dict(pristine, **{samsung_id: [changed]})
            scored = actual_score(mutated)
            check('Samsung_' + label + '_cannot_receive_complete_record_match', scored[samsung_id]['exact'] is False and scored[samsung_id]['f1'] == 0.0)
            check(label + '_does_not_change_Huawei_or_ordinary', scored[huawei_id]['exact'] is True and scored[ordinary_id]['exact'] is True)
        mutated = dict(pristine, **{huawei_id: [dict(huawei_row, auxiliaryCount=7)]})
        check('Huawei_share_only_does_not_force_auxiliary_count_role', actual_score(mutated)[huawei_id]['exact'] is True)
        for label, rows in [('missing_identity', ordinary_top10[:-1]), ('extra_identity', ordinary_top10 + ordinary_full[10:11]), ('wrong_order', list(reversed(ordinary_top10)))]:
            mutated = dict(pristine, **{ordinary_id: rows})
            check('ordinary_' + label + '_remains_rejected', actual_score(mutated)[ordinary_id]['exact'] is False)
        check('ordinary_scorer_identity_was_not_replaced', score_predictions.original_scorer.__file__.startswith(str(workspace / 'bundle_scorer')))
    receipt = {'status': 'PASS_AUTH11_THREE_SOURCE_FREE_ACTUAL_RUNTIME_CONTRACT_SHAPES',
        'tests_n': len(tests), 'tests': tests, 'manifest_sha256': digest(base / 'manifest.json'),
        'actual_research_answer_or_gold_read': False, 'research_SQLite_read': False,
        'temporary_synthetic_SQLite_only': True, 'empty_synthetic_repository_marker_for_unchanged_module_initializer': True,
        'native_execution_is_explicit_stub': True, 'retrieval_and_model_responses_are_explicit_stubs': True,
        'API_calls': 0, 'native_calls': 0, 'original_scorer_and_V8_runtime_bytes_unchanged': True}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        json.dump(receipt, stream, indent=2); stream.write('\n')
    print(json.dumps({'status': receipt['status'], 'tests_n': len(tests), 'receipt_sha256': digest(args.out)}))


if __name__ == '__main__':
    main()
