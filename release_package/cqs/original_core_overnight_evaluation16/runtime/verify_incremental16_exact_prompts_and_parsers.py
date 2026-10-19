#!/usr/bin/env python3
"""Replay the exact frozen CQ001 requests and output parsers without API or DB calls.

The registered AUTH37 generation adapters are used directly. No source-order or
declared-share prompt/parser hooks are installed for this ordinary typed CQ.
"""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True
IDENT = 'RAN1_P3_CQ001'


def load(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(evidence):
    evidence = Path(evidence).resolve()
    current, runtime = evidence / 'current', evidence / 'runtime'
    protocol = load(current / 'protocol.json')
    assert sha(current / 'protocol.json') == '6a7e1b7c37170342f6377fdec2f026937c173f3a5b3246d1c3d54253eca12ec6'
    public_rows = rows(current / 'public_tasks.jsonl')
    assert len(public_rows) == 1
    public = public_rows[0]
    assert public['id'] == IDENT and public['wg'] == 'RAN1'
    assert [field['name'] for field in public['required_fields']] == [
        'specRelease', 'sectionNumber', 'sectionTitle']
    assert public['collection'] == {'kind': 'set'}
    for name, expected in protocol['code_pins'].items():
        assert sha(runtime / name) == expected, name
    adapter_spec = importlib.util.spec_from_file_location(
        'auth16_frozen_structured_parser', runtime / 'structured_adapter.py')
    adapter = importlib.util.module_from_spec(adapter_spec)
    adapter_spec.loader.exec_module(adapter)

    # Load only the actual pure prompt/JSON parser definitions, avoiding corpus
    # initialization and unrelated environment dependencies during offline replay.
    functions = {'canonical', 'structural_schema', 'public_contract', 'parse_answer'}
    constants = {'QUERY_INSTRUCTION', 'ANSWER_INSTRUCTION'}
    selected = []
    for node in ast.parse((runtime / 'retrieval_adapter.py').read_text()).body:
        if isinstance(node, ast.FunctionDef) and node.name in functions:
            selected.append(node)
        elif isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id in constants for target in node.targets):
            selected.append(node)
    retrieval = {'json': json}
    exec(compile(ast.Module(body=selected, type_ignores=[]),
                 '<pinned AUTH37 retrieval pure definitions>', 'exec'), retrieval)
    assert functions | constants <= set(retrieval)
    expected, structured_tasks = {}, {}
    for arm, kind, tag in [('A', 'graph', 'Text2Cypher'), ('B', 'sql', 'Text2SQL')]:
        task = dict(public)
        task[kind + '_schema'] = load(current / 'schemas' / ('RAN1_' + kind + '.json'))
        structured_tasks[tag] = task
        expected[IDENT + '_' + tag] = adapter.messages_for(task, arm)
    for arm in ('C', 'D'):
        base = current / 'retrieval' / arm / IDENT
        initial, final = load(base / 'initial_context.json'), load(base / 'final_context.json')
        prefix = retrieval['canonical']({'question': public['question_en'],
                  'contract': retrieval['public_contract'](public)}) + '\nSOURCE PASSAGES:\n'
        if arm == 'D':
            expected[IDENT + '_D_followup'] = [
                {'role': 'system', 'content': retrieval['QUERY_INSTRUCTION']},
                {'role': 'user', 'content': prefix + '\n\n'.join(
                    document['formatted'] for document in initial['documents'])}]
        expected[IDENT + '_' + arm + '_answer'] = [
            {'role': 'system', 'content': retrieval['ANSWER_INSTRUCTION']},
            {'role': 'user', 'content': prefix + '\n\n'.join(
                document['formatted'] for document in final['documents'])}]
    request_rows = [load(path) for path in (current / 'calls').glob('*.request.json')]
    requests = {request['request_id']: request for request in request_rows}
    assert len(request_rows) == len(requests) == len(expected) == 5
    assert set(requests) == set(expected)
    outcomes = {}
    for identifier, request in requests.items():
        assert request['payload']['messages'] == expected[identifier], identifier
        outcomes[identifier] = load(current / 'calls' / (identifier + '.outcome.json'))

    class SavedCaller:
        def call(self, request_id, messages, **kwargs):
            assert messages == expected[request_id]
            return outcomes[request_id]

    read_guards, statuses = [], {}
    for method, tag in [('text2cypher', 'Text2Cypher'), ('text2sql', 'Text2SQL')]:
        saved = load(current / 'predictions' / tag / (IDENT + '.json'))
        executed = load(current / 'executed' / method / (IDENT + '.json'))
        with tempfile.TemporaryDirectory(prefix='spectra-auth16-offline-parser-') as temporary:
            replay = adapter.evaluate(structured_tasks[tag], tag, SavedCaller(), Path(temporary))
        assert replay == saved, (tag, 'generation parser')
        if replay['status'] != 'QUERY_READY':
            # This documented branch returns before any database access.
            assert adapter.execute_generated(replay, public) == executed
            read_guards.append({'method': tag, 'status': executed['status'],
                                'nonready_passthrough': True})
        else:
            assert executed['generated_query'] == replay['generated_query']
            assert executed['query_sha256'] == replay['query_sha256']
            execution = executed['execution']
            assert execution is not None
            assert executed['records'] == (execution['rows'] if execution['complete'] else [])
            assert executed['abstain'] == (not execution['complete'])
            guard = {'method': tag, 'status': executed['status'],
                     'complete': execution['complete'], 'truncated': execution['truncated']}
            if execution['complete']:
                assert executed['status'] == 'OK' and not execution['truncated']
                if tag == 'Text2Cypher':
                    assert execution['plan_query_type'] == execution['execution_query_type'] == 'r'
                    assert execution['rollback_completed'] and execution['execution_summary_complete']
                    guard['actual_read_plan_summary_rollback'] = True
                else:
                    assert execution['immutable_read_only'] is True
                    guard['actual_immutable_read_only'] = True
            else:
                guard['partial_rows_not_scored'] = True
            read_guards.append(guard)
        statuses[method] = executed['status']

    parse_failures = 0
    for method, arm in [('single_retrieval', 'C'), ('iterative_retrieval', 'D')]:
        result = load(current / 'arm_outputs' / method / (IDENT + '.json'))
        assert result == load(current / 'retrieval' / arm / IDENT / 'result.json')
        outcome = outcomes[IDENT + '_' + arm + '_answer']
        if outcome.get('finish_reason') == 'length':
            assert result['status'] == 'output_truncated' and result['records'] == []
        elif not outcome.get('ok') or outcome.get('finish_reason') != 'stop':
            assert result['status'] == 'answer_failed' and result['records'] == []
        else:
            try:
                parsed = retrieval['parse_answer'](outcome['content'])
            except (ValueError, TypeError, KeyError) as error:
                assert result['status'] == 'answer_parse_error'
                assert result['records'] == [] and result['error'] == str(error)
                parse_failures += 1
            else:
                assert result['status'] == ('abstained' if parsed['abstain'] else
                                            ('ok' if parsed['complete'] else 'partial'))
                assert result['records'] == parsed['records']
                assert result['abstain'] == parsed['abstain']
                assert result['self_reported_complete'] == parsed['complete']
        assert result['source_cutoff_relation_to_frozen_graph'] == 'UNKNOWN'
        assert result['requested_population_completeness_verified'] is False
        statuses[method] = result['status']
    guard = load(current / 'source_guards/RAN1.json')
    assert guard['before'] == guard['after'] == protocol['graph_sources']['RAN1']
    return {'status': 'PASS', 'question_n': 1, 'prompt_reconstruction_n': 5,
            'output_parser_replay_n': 4, 'structured_generation_parser_replay_n': 2,
            'retrieval_parse_failure_replay_n': parse_failures,
            'saved_structured_read_guard_paths': read_guards, 'actual_statuses': statuses,
            'new_model_or_database_calls_n': 0,
            'source_order_or_exact_share_hooks_installed': False,
            'retrieval_parser': 'Direct original parse_answer from registered AUTH37 bytes',
            'portable_AST_retrieval_projection': True,
            'limits': 'Saved parser and guard evidence replay; no live query/corpus execution or physical-source completeness claim.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    arguments = parser.parse_args()
    result = verify(arguments.evidence)
    if arguments.out:
        assert not arguments.out.exists(), 'Preserve previous receipts'
        assert not arguments.out.resolve().is_relative_to(arguments.evidence.resolve())
        arguments.out.parent.mkdir(parents=True, exist_ok=True)
        arguments.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
