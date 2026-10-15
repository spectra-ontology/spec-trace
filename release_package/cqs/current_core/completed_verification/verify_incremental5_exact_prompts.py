#!/usr/bin/env python3
"""Reconstruct each first prompt and output parser from frozen runtime bytes."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True


def load(path): return json.loads(path.read_text())
def rows(path): return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worktree', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    cqs = args.worktree / 'release_package/cqs'
    evidence = cqs / 'original_core_overnight_evaluation5'
    current, runtime = evidence / 'current', evidence / 'runtime'
    public, = rows(current / 'public_tasks.jsonl')
    protocol = load(current / 'protocol.json')
    for name, pin in protocol['code_pins'].items(): assert sha(runtime / name) == pin
    spec = importlib.util.spec_from_file_location('incremental5_root_structured', runtime / 'structured_adapter.py')
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    functions = {'canonical', 'structural_schema', 'public_contract', 'parse_answer'}
    constants = {'QUERY_INSTRUCTION', 'ANSWER_INSTRUCTION'}
    selected = []
    for node in ast.parse((runtime / 'retrieval_adapter.py').read_text()).body:
        if isinstance(node, ast.FunctionDef) and node.name in functions: selected.append(node)
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in constants for t in node.targets): selected.append(node)
    retrieval = {'json': json}
    exec(compile(ast.Module(body=selected, type_ignores=[]), '<pinned retrieval projection>', 'exec'), retrieval)
    assert functions | constants <= set(retrieval)
    identifier, wg = public['id'], public['wg']
    expected = {}
    for arm, kind, tag in [('A', 'graph', 'Text2Cypher'), ('B', 'sql', 'Text2SQL')]:
        task = dict(public)
        task[kind + '_schema'] = load(current / 'schemas' / (wg + '_' + kind + '.json'))
        expected[identifier + '_' + tag] = adapter.messages_for(task, arm)
    for arm in ['C', 'D']:
        base = current / 'retrieval' / arm / identifier
        initial, final = load(base / 'initial_context.json'), load(base / 'final_context.json')
        prefix = retrieval['canonical']({'question': public['question_en'], 'contract': retrieval['public_contract'](public)}) + '\nSOURCE PASSAGES:\n'
        if arm == 'D': expected[identifier + '_D_followup'] = [{'role': 'system', 'content': retrieval['QUERY_INSTRUCTION']}, {'role': 'user', 'content': prefix + '\n\n'.join(doc['formatted'] for doc in initial['documents'])}]
        expected[identifier + '_' + arm + '_answer'] = [{'role': 'system', 'content': retrieval['ANSWER_INSTRUCTION']}, {'role': 'user', 'content': prefix + '\n\n'.join(doc['formatted'] for doc in final['documents'])}]
    requests = {load(path)['request_id']: load(path) for path in (current / 'calls').glob('*.request.json')}
    assert set(requests) == set(expected) and len(requests) == 5
    content = {}
    for identifier_request, request in requests.items():
        assert request['payload']['messages'] == expected[identifier_request]
        content[identifier_request] = load(current / 'calls' / (identifier_request + '.outcome.json'))['content']
    parse_failures = 0
    for method, tag in [('text2cypher', 'Text2Cypher'), ('text2sql', 'Text2SQL')]:
        result = load(current / 'executed' / method / (identifier + '.json'))
        assert json.loads(content[identifier + '_' + tag]) == {'query': result['generated_query'], 'abstain': False}
        execution = result['execution']
        assert result['records'] == execution['rows'] and execution['complete'] and not execution['truncated']
        if method == 'text2cypher': assert execution['plan_query_type'] == execution['execution_query_type'] == 'r' and execution['rollback_completed'] and execution['execution_summary_complete']
    for method, arm in [('single_retrieval', 'C'), ('iterative_retrieval', 'D')]:
        result = load(current / 'arm_outputs' / method / (identifier + '.json'))
        try: parsed = retrieval['parse_answer'](content[identifier + '_' + arm + '_answer'])
        except (ValueError, TypeError, KeyError) as error:
            assert result['status'].upper() == 'ANSWER_PARSE_ERROR' and result['records'] == [] and result['error'] == str(error)
            parse_failures += 1
        else:
            status = 'ABSTAINED' if parsed['abstain'] else ('OK' if parsed['complete'] else 'PARTIAL')
            assert result['status'].upper() == status and result['records'] == parsed['records']
    record = {'status': 'ROOT_EXACT5_PROMPTS_AND_ALL4_OUTPUT_PARSERS_REPLAY_PASS',
        'evaluation_manifest_sha256': sha(evidence / 'manifest.json'), 'protocol_sha256': sha(current / 'protocol.json'),
        'prompt_reconstruction_n': 5, 'retrieval_parse_failure_replay_n': parse_failures,
        'native_read_summary_and_rollback_verified': True, 'new_model_or_database_calls_n': 0,
        'limitations': 'Saved request/response/complete execution/scorer evidence. Does not establish physical corpus coverage or human/expert validity.'}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record))


if __name__ == '__main__': main()
