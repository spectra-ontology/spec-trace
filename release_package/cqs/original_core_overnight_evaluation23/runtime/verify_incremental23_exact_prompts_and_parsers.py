#!/usr/bin/env python3
"""Replay the frozen AUTH23 prompt families and parsers without API or DB calls.

The registered AUTH37 adapter bytes are loaded directly. No extra prompt or
parser hooks and no source evidence fixtures are installed as model inputs.
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
IDS = {'RAN1_P3_CQ045'}


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
    assert sha(current / 'protocol.json') == load(evidence / 'manifest.json')['protocol_sha256']
    public_rows = rows(current / 'public_tasks.jsonl')
    public_by_id = {p['id']: p for p in public_rows}
    assert len(public_rows) == len(public_by_id) == 1 and set(public_by_id) == IDS
    for ident, public in public_by_id.items():
        assert public['wg'] == ident.split('_')[0]
        assert public['collection']=={'kind':'set'}
        assert public['cardinality_policy']=={'mode':'all'}
        assert public['required_fields']==[{'name':'spec','type':'string','nullable':False}]
    for name, expected_sha in protocol['code_pins'].items():
        assert sha(runtime / name) == expected_sha, name
    adapter_spec = importlib.util.spec_from_file_location('auth23_frozen_structured_parser', runtime / 'structured_adapter.py')
    adapter = importlib.util.module_from_spec(adapter_spec)
    adapter_spec.loader.exec_module(adapter)
    functions = {'canonical', 'structural_schema', 'public_contract', 'parse_answer'}
    constants = {'QUERY_INSTRUCTION', 'ANSWER_INSTRUCTION'}
    selected = []
    for node in ast.parse((runtime / 'retrieval_adapter.py').read_text()).body:
        if isinstance(node, ast.FunctionDef) and node.name in functions:
            selected.append(node)
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in constants for t in node.targets):
            selected.append(node)
    retrieval = {'json': json}
    exec(compile(ast.Module(body=selected, type_ignores=[]), '<pinned AUTH37 retrieval pure definitions>', 'exec'), retrieval)
    assert functions | constants <= set(retrieval)
    expected, structured_tasks = {}, {}
    for ident, public in public_by_id.items():
        wg = public['wg']
        for arm, kind, tag in [('A', 'graph', 'Text2Cypher'), ('B', 'sql', 'Text2SQL')]:
            task = dict(public)
            task[kind + '_schema'] = load(current / 'schemas' / (wg + '_' + kind + '.json'))
            structured_tasks[(ident, tag)] = task
            expected[ident + '_' + tag] = adapter.messages_for(task, arm)
        for arm in ('C', 'D'):
            base = current / 'retrieval' / arm / ident
            initial, final = load(base / 'initial_context.json'), load(base / 'final_context.json')
            prefix = retrieval['canonical']({'question': public['question_en'], 'contract': retrieval['public_contract'](public)}) + '\nSOURCE PASSAGES:\n'
            if arm == 'D':
                expected[ident + '_D_followup'] = [
                    {'role': 'system', 'content': retrieval['QUERY_INSTRUCTION']},
                    {'role': 'user', 'content': prefix + '\n\n'.join(d['formatted'] for d in initial['documents'])}]
            expected[ident + '_' + arm + '_answer'] = [
                {'role': 'system', 'content': retrieval['ANSWER_INSTRUCTION']},
                {'role': 'user', 'content': prefix + '\n\n'.join(d['formatted'] for d in final['documents'])}]
    request_rows = [load(p) for p in (current / 'calls').glob('*.request.json')]
    requests = {r['request_id']: r for r in request_rows}
    assert len(request_rows) == len(requests) == len(expected) == 5 and set(requests) == set(expected)
    outcomes = {}
    for identifier, request in requests.items():
        assert request['payload']['messages'] == expected[identifier], identifier
        outcomes[identifier] = load(current / 'calls' / (identifier + '.outcome.json'))

    class SavedCaller:
        def call(self, request_id, messages, **kwargs):
            assert messages == expected[request_id]
            return outcomes[request_id]

    read_guards, statuses, parse_failures = [], {}, 0
    for ident, public in public_by_id.items():
        statuses[ident] = {}
        for method, tag in [('text2cypher', 'Text2Cypher'), ('text2sql', 'Text2SQL')]:
            saved = load(current / 'predictions' / tag / (ident + '.json'))
            executed = load(current / 'executed' / method / (ident + '.json'))
            with tempfile.TemporaryDirectory(prefix='spectra-auth23-offline-parser-') as temporary:
                replay = adapter.evaluate(structured_tasks[(ident, tag)], tag, SavedCaller(), Path(temporary))
            assert replay == saved, (ident, tag, 'generation parser')
            if replay['status'] != 'QUERY_READY':
                assert adapter.execute_generated(replay, public) == executed
                read_guards.append({'id': ident, 'method': tag, 'status': executed['status'], 'nonready_passthrough': True})
            else:
                assert executed['generated_query'] == replay['generated_query']
                assert executed['query_sha256'] == replay['query_sha256']
                execution = executed['execution']
                assert execution is not None
                assert executed['records'] == (execution['rows'] if execution['complete'] else [])
                assert executed['abstain'] == (not execution['complete'])
                guard = {'id': ident, 'method': tag, 'status': executed['status'], 'complete': execution['complete'], 'truncated': execution['truncated']}
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
            statuses[ident][method] = executed['status']
        for method, arm in [('single_retrieval', 'C'), ('iterative_retrieval', 'D')]:
            result = load(current / 'arm_outputs' / method / (ident + '.json'))
            assert result == load(current / 'retrieval' / arm / ident / 'result.json')
            outcome = outcomes[ident + '_' + arm + '_answer']
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
                    assert result['status'] == ('abstained' if parsed['abstain'] else ('ok' if parsed['complete'] else 'partial'))
                    assert result['records'] == parsed['records'] and result['abstain'] == parsed['abstain']
                    assert result['self_reported_complete'] == parsed['complete']
            assert result['source_cutoff_relation_to_frozen_graph'] == 'UNKNOWN'
            assert result['requested_population_completeness_verified'] is False
            statuses[ident][method] = result['status']
    for wg in {p['wg'] for p in public_by_id.values()}:
        guard = load(current / 'source_guards' / (wg + '.json'))
        assert guard['before'] == guard['after'] == protocol['graph_sources'][wg]
    return {'status': 'PASS', 'question_n': 1, 'prompt_reconstruction_n': 5,
        'output_parser_replay_n': 4, 'structured_generation_parser_replay_n': 2,
        'retrieval_parse_failure_replay_n': parse_failures, 'saved_structured_read_guard_paths': read_guards,
        'actual_statuses': statuses, 'new_model_or_database_calls_n': 0,
        'source_order_or_exact_share_hooks_installed': False,
        'retrieval_parser': 'Direct original parse_answer from registered AUTH37 bytes',
        'portable_AST_retrieval_projection': True,
        'limits': 'Saved parser and guard evidence replay; no live query/corpus execution or physical-source completeness claim.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = verify(args.evidence)
    if args.out:
        assert not args.out.exists(), 'Preserve earlier receipts'
        assert not args.out.resolve().is_relative_to(args.evidence.resolve())
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
