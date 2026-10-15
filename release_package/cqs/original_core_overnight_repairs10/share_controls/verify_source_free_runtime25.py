"""Source-free actual runtime/public/scorer integration; temporary SQLite only."""
from pathlib import Path
from decimal import Decimal
import argparse
import hashlib
import importlib
import importlib.util
import json
import sqlite3
import sys
import tempfile


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--proposal', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    assert not args.out.exists()
    base = args.proposal.resolve()
    sys.path[:0] = [str(base / 'runtime'), str(base / 'bundle_scorer')]
    runtime = importlib.import_module('run_evaluation')
    structured = importlib.import_module('structured_adapter')
    retrieval = importlib.import_module('retrieval_adapter')
    share = importlib.import_module('share_runtime_adapter')
    codec = importlib.import_module('rational_share_records')
    score_predictions = importlib.import_module('score_predictions')
    tests = []
    def check(name, condition):
        assert condition, name
        tests.append({'name': name, 'pass': True})
    definition = {
        'id': 'RAN4_SYNTHETIC_SHARE', 'repair_sha256': 'synthetic-not-source-or-gold',
        'validation_status': 'validated', 'question_en': 'Return this synthetic exact share.',
        'required_fields': [{'name': 'share', 'type': 'json', 'nullable': False, 'json_schema': codec.PAIR_SCHEMA}],
        'collection': {'kind': 'set', 'rational_share_representation': {'kind': 'exact_rational_share', 'unit': 'one', 'field': 'share'}},
        'cardinality_policy': {'mode': 'all'}}
    public = runtime.public_task(definition)
    check('fresh_runtime_automatically_installed_before_freeze', runtime._cohort_exact_share_hooks_installed is True)
    check('real_public_task_sanitized_descriptor', public['collection']['rational_share_representation'] == {'kind': 'exact_rational_share', 'unit': 'one', 'field': 'share'})
    check('real_public_task_decoder_marker', public['required_fields'][0]['value_representation'] == {'kind': 'exact_rational_share', 'unit': 'one'})
    check('private_paths_and_hashes_not_in_public', 'normalizer_sha256' not in json.dumps(public) and 'reference_query' not in public)
    plain = {'id': 'RAN2_SYNTHETIC_ORDINARY', 'repair_sha256': 'ordinary-synthetic',
        'validation_status': 'validated', 'question_en': 'Return a synthetic ID.',
        'required_fields': [{'name': 'identity', 'type': 'string', 'nullable': False}],
        'collection': {'kind': 'set', 'source_order_keys': [{'field': 'meetingNumberInt', 'direction': 'desc'}]},
        'cardinality_policy': {'mode': 'all'}}
    plain_public = runtime.public_task(plain)
    check('prior_source_order_keys_disclosure_preserved', plain_public['collection']['source_order_keys'] == plain['collection']['source_order_keys'])
    check('ordinary_public_contract_not_given_share_marker', 'rational_share_representation' not in plain_public['collection'] and 'value_representation' not in plain_public['required_fields'][0])
    for method, schema in [('A', 'graph_schema'), ('B', 'sql_schema')]:
        messages = structured.messages_for(dict(public, **{schema: {'synthetic': 'no-source-values'}}), method)
        visible = json.loads(messages[1]['content'])
        check(method + '_actual_messages_same_public_representation', visible['output_format']['value_representations'] == [codec.public_representation(public)])
    check('C_D_actual_contract_same_public_representation', retrieval.public_contract(public)['value_representations'] == [codec.public_representation(public)])
    expected = codec.rational(Decimal('0.100000000000000005'))
    with tempfile.TemporaryDirectory(prefix='auth10-source-free-runtime-') as temporary:
        temporary = Path(temporary)
        db = temporary / 'synthetic.sqlite3'
        con = sqlite3.connect(db)
        con.execute('CREATE TABLE synthetic(value TEXT)')
        con.execute('INSERT INTO synthetic VALUES (?)', ('0.100000000000000005',))
        con.commit(); con.close()
        query = 'SELECT value AS share FROM synthetic'
        record = {'id': public['id'], 'repair_sha256': public['repair_sha256'], 'method': 'Text2SQL',
            'status': 'QUERY_READY', 'generated_query': query, 'query_sha256': hashlib.sha256(query.encode()).hexdigest(), 'wg': 'RAN4'}
        executed = structured.execute_generated(record, public, sql_db=db)
        check('B_actual_immutable_SQLite_execution_assembly', executed['status'] == 'OK' and executed['records'] == [{'share': expected}])
        check('B_actual_SQLite_read_guard', executed['execution']['immutable_read_only'] is True)
        check('B_direct_custom_task_fields_decode', structured.run_sql_query(db, query, public['required_fields'])['rows'] == executed['records'])
        raw_query = 'SELECT value AS share FROM synthetic'
        # A custom root executor can use the same hook explicitly after its own
        # immutable SQL read; synthetic raw JSON text demonstrates that route.
        check('custom_SQL_path_explicit_hook', share.candidate_records(public, 'B', [{'share': '0.100000000000000005'}]) == executed['records'])
        # Native execution is simulated, without contacting a graph or driver.
        structured.run_cypher_query = lambda *a, **k: {'status': 'OK', 'rows': [{'share': {'numerator': 2, 'denominator': 10}}], 'complete': True}
        native_record = dict(record, method='Text2Cypher', generated_query='synthetic', query_sha256=hashlib.sha256(b'synthetic').hexdigest())
        native = structured.execute_generated(native_record, public)
        check('A_native_assembly_same_canonical_pair_no_native_call', native['records'] == [{'share': {'numerator': 1, 'denominator': 5}}])
        retrieval.prepare_corpus_inventory = lambda *a, **k: {'shards': [{'WG': 'RAN4', 'path': 'synthetic-unused', 'sha256': 'synthetic'}]}
        retrieval.retrieve = lambda *a, **k: {'status': 'ok', 'context_candidate_truncated': False}
        retrieval.contexts = lambda *a, **k: ([], {'document_selection_truncated': False})
        class Caller:
            def __init__(self): self.messages = []
            def call(self, key, messages, **kwargs):
                self.messages.append((key, messages))
                content = '{"query":"synthetic"}' if key.endswith('followup') else '{"records":[{"share":0.100000000000000005},{"share":"invalid"}],"abstain":false,"complete":true}'
                return {'ok': True, 'finish_reason': 'stop', 'content': content}
        results = {'B': executed['records']}
        for method in ['C', 'D']:
            caller = Caller()
            outcome = retrieval.evaluate(public, method, caller, temporary)
            check(method + '_actual_evaluate_exact_lexical_and_invalid_partial', outcome['status'] == 'ok' and outcome['records'][0]['share'] == expected and len(outcome['records']) == 2)
            user = caller.messages[-1][1][1]['content'].split('\nSOURCE PASSAGES:', 1)[0]
            check(method + '_actual_evaluate_public_representation', json.loads(user)['contract']['value_representations'] == [codec.public_representation(public)])
            results[method] = outcome['records']
        task_file, gold_file, pred_file = [temporary / name for name in ['tasks.jsonl', 'gold.jsonl', 'prediction.jsonl']]
        task_file.write_text(json.dumps(definition) + '\n' + json.dumps(plain) + '\n')
        gold = [{'id': definition['id'], 'repair_sha256': definition['repair_sha256'], 'records': [{'share': expected}], 'order_groups': []},
                {'id': plain['id'], 'repair_sha256': plain['repair_sha256'], 'records': [{'identity': 'source-free-ID'}], 'order_groups': []}]
        gold_file.write_text(''.join(json.dumps(row) + '\n' for row in gold))
        for method, rows in results.items():
            predictions = [{'id': definition['id'], 'repair_sha256': definition['repair_sha256'], 'records': rows},
                {'id': plain['id'], 'repair_sha256': plain['repair_sha256'], 'records': [{'identity': 'source-free-ID'}]}]
            pred_file.write_text(''.join(json.dumps(row) + '\n' for row in predictions))
            scored = score_predictions.run(task_file, gold_file, pred_file)
            outcomes = {row['id']: row for row in scored['outcomes']}
            share_score = outcomes[definition['id']]
            check(method + '_actual_public_scorer_end_to_end', share_score['exact'] is (method == 'B') and share_score['f1'] == (1.0 if method == 'B' else 2/3))
            check(method + '_ordinary_task_same_scorer_unchanged', outcomes[plain['id']]['exact'] is True)
        source = (base / 'runtime/run_evaluation.py').read_text()
        check('freeze_pins_new_codec_and_hooks', all("'" + name + "'" in source.split("'code_pins':", 1)[1].split("'schema_pins':", 1)[0] for name in ['rational_share_records.py', 'share_runtime_adapter.py', 'share_cohort_hooks.py']))
    receipt = {'status': 'PASS_SOURCE_FREE_AUTH10_ACTUAL_PUBLIC_RUNTIME_SQLITE_PARSERS_ASSEMBLY_AND_SCORER',
        'tests_n': len(tests), 'tests': tests, 'source_or_actual_answer_or_model_read': False,
        'temporary_synthetic_SQLite_only': True, 'native_or_API_calls': 0,
        'proposal_manifest_sha256': hashlib.sha256((base / 'manifest.json').read_bytes()).hexdigest()}
    with args.out.open('x') as stream:
        json.dump(receipt, stream, indent=2); stream.write('\n')
    print(json.dumps({'status': receipt['status'], 'tests_n': len(tests), 'receipt_sha256': hashlib.sha256(args.out.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
