#!/usr/bin/env python3
"""Replay five saved matrix-scope requests and all four output parsers, offline."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True


def load(path): return json.loads(path.read_text())
def rows(path): return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main(evidence, out):
    current, runtime = evidence / 'current', evidence / 'runtime'
    public, = rows(current / 'public_tasks.jsonl')
    protocol = load(current / 'protocol.json')
    for name, pin in protocol['code_pins'].items():
        assert sha(runtime / name) == pin, name
    sys.path.insert(0, str(runtime))
    spec = importlib.util.spec_from_file_location('incremental7_pinned_structured', runtime / 'structured_adapter.py')
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    functions = {'canonical', 'structural_schema', 'public_contract', 'parse_answer', 'answer_instruction'}
    constants = {'QUERY_INSTRUCTION', 'ANSWER_INSTRUCTION'}
    selected = []
    for node in ast.parse((runtime / 'retrieval_adapter.py').read_text()).body:
        if isinstance(node, ast.FunctionDef) and node.name in functions:
            selected.append(node)
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in constants for t in node.targets):
            selected.append(node)
    retrieval = {'json': json}
    exec(compile(ast.Module(body=selected, type_ignores=[]), '<pinned retrieval projection>', 'exec'), retrieval)
    assert functions | constants <= set(retrieval)
    identifier, wg = public['id'], public['wg']
    assert public['collection']['matrix_representation']
    expected, structured_tasks = {}, {}
    for arm, kind, tag in [('A', 'graph', 'Text2Cypher'), ('B', 'sql', 'Text2SQL')]:
        task = dict(public)
        task[kind + '_schema'] = load(current / 'schemas' / (wg + '_' + kind + '.json'))
        structured_tasks[tag] = task
        expected[identifier + '_' + tag] = adapter.messages_for(task, arm)
    for arm in ('C', 'D'):
        base = current / 'retrieval' / arm / identifier
        initial, final = load(base / 'initial_context.json'), load(base / 'final_context.json')
        contract = retrieval['public_contract'](public)
        assert contract['collection']['matrix_representation']
        prefix = retrieval['canonical']({'question': public['question_en'], 'contract': contract}) + '\nSOURCE PASSAGES:\n'
        if arm == 'D':
            expected[identifier + '_D_followup'] = [
                {'role': 'system', 'content': retrieval['QUERY_INSTRUCTION']},
                {'role': 'user', 'content': prefix + '\n\n'.join(doc['formatted'] for doc in initial['documents'])}]
        expected[identifier + '_' + arm + '_answer'] = [
            {'role': 'system', 'content': retrieval['answer_instruction'](public)},
            {'role': 'user', 'content': prefix + '\n\n'.join(doc['formatted'] for doc in final['documents'])}]
    requests = {load(path)['request_id']: load(path) for path in (current / 'calls').glob('*.request.json')}
    assert set(requests) == set(expected) and len(requests) == 5
    outcomes = {}
    for request_id, request in requests.items():
        assert request['payload']['messages'] == expected[request_id], request_id
        outcomes[request_id] = load(current / 'calls' / (request_id + '.outcome.json'))

    class SavedCaller:
        def call(self, request_id, messages, **kwargs):
            assert messages == expected[request_id]
            return outcomes[request_id]

    statuses = {}
    for method, tag in [('text2cypher', 'Text2Cypher'), ('text2sql', 'Text2SQL')]:
        saved_generation = load(current / 'predictions' / tag / (identifier + '.json'))
        saved_execution = load(current / 'executed' / method / (identifier + '.json'))
        with tempfile.TemporaryDirectory(prefix='spectra-auth7-parser-') as directory:
            replay = adapter.evaluate(structured_tasks[tag], tag, SavedCaller(), Path(directory))
        assert replay == saved_generation, tag
        # Non-ready predictions are returned unchanged by the pinned execution path.
        if replay['status'] != 'QUERY_READY':
            executed_replay = adapter.execute_generated(replay, public)
            assert executed_replay == saved_execution
        else:
            assert saved_execution['generated_query'] == replay['generated_query']
            assert saved_execution['query_sha256'] == replay['query_sha256']
            execution = saved_execution['execution']
            assert execution is not None
            assert saved_execution['records'] == (execution['rows'] if execution['complete'] else [])
            if method == 'text2cypher' and execution['complete']:
                assert execution['plan_query_type'] == execution['execution_query_type'] == 'r'
                assert execution['rollback_completed'] and execution['execution_summary_complete']
        statuses[method] = saved_execution['status']
    parse_failures = 0
    for method, arm in [('single_retrieval', 'C'), ('iterative_retrieval', 'D')]:
        result = load(current / 'arm_outputs' / method / (identifier + '.json'))
        outcome = outcomes[identifier + '_' + arm + '_answer']
        assert outcome.get('ok') and outcome.get('finish_reason') == 'stop'
        try:
            parsed = retrieval['parse_answer'](outcome['content'])
        except (ValueError, TypeError, KeyError) as error:
            assert result['status'].upper() == 'ANSWER_PARSE_ERROR'
            assert result['records'] == [] and result['error'] == str(error)
            parse_failures += 1
        else:
            status = 'ABSTAINED' if parsed['abstain'] else ('OK' if parsed['complete'] else 'PARTIAL')
            assert result['status'].upper() == status and result['records'] == parsed['records']
        statuses[method] = result['status']
    record = {
        'status': 'EXACT5_MATRIX_PROMPTS_AND_ALL4_OUTPUT_PARSERS_REPLAY_PASS',
        'evaluation_manifest_sha256': sha(evidence / 'manifest.json'),
        'protocol_sha256': sha(current / 'protocol.json'),
        'prompt_reconstruction_n': 5, 'structured_generation_parser_replay_n': 2,
        'retrieval_answer_parser_replay_n': 2, 'retrieval_parse_failure_replay_n': parse_failures,
        'structured_nonready_execution_passthrough_replayed': True,
        'matrix_public_descriptor_visible_in_all_final_answer_requests': True,
        'actual_statuses': statuses, 'new_model_or_database_calls_n': 0,
        'limitations': 'Saved requests and outputs only. No API, new database execution, physical corpus coverage, or human/expert validity claim.'}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(record))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    main(args.evidence.resolve(), args.out.resolve())
