"""Replay the frozen AUTH25 prompt families and parsers without API or DB calls.

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
if sys.flags.optimize != 0:
    raise RuntimeError('Optimized verifier execution unsupported')
IDS = {'RAN5_P3_CQ3-1', 'RAN1_P2_CQ5-11'}

def load(path):
    return json.loads(Path(path).read_text())

def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def verify(evidence):
    evidence = Path(evidence).resolve()
    (current, runtime) = (evidence / 'current', evidence / 'runtime')
    protocol = load(current / 'protocol.json')
    if not sha(current / 'protocol.json') == load(evidence / 'manifest.json')['protocol_sha256']:
        raise ValueError('saved evidence invariant failed')
    public_rows = rows(current / 'public_tasks.jsonl')
    public_by_id = {p['id']: p for p in public_rows}
    if not (len(public_rows) == len(public_by_id) == 2 and set(public_by_id) == IDS):
        raise ValueError('saved evidence invariant failed')
    for (ident, public) in public_by_id.items():
        if not public['wg'] == ident.split('_')[0]:
            raise ValueError('saved evidence invariant failed')
        expected_contracts = {'RAN5_P3_CQ3-1': {'collection': {'kind': 'multiset'}, 'cardinality_policy': {'mode': 'all'}, 'required_fields': [{'name': 'tdocNumber', 'nullable': False, 'type': 'string'}, {'name': 'specNumber', 'nullable': False, 'type': 'string'}]}, 'RAN1_P2_CQ5-11': {'collection': {'kind': 'top_k_boundary_ties', 'require_rank_order': False, 'tie_policy': 'any_subset_at_boundary', 'value': 10, 'within_tie_order': 'any'}, 'cardinality_policy': {'mode': 'top_k', 'tie_policy': 'any_subset_at_boundary', 'value': 10}, 'required_fields': [{'name': 'resolutionId', 'nullable': False, 'type': 'string'}]}}
        if {k:public[k] for k in ['collection','cardinality_policy','required_fields']} != expected_contracts[ident]:
            raise ValueError('Registered model-visible contract differs')
    for (name, expected_sha) in protocol['code_pins'].items():
        if not sha(runtime / name) == expected_sha:
            raise ValueError(name)
    adapter_spec = importlib.util.spec_from_file_location('auth25_frozen_structured_parser', runtime / 'structured_adapter.py')
    adapter = importlib.util.module_from_spec(adapter_spec)
    adapter_spec.loader.exec_module(adapter)
    functions = {'canonical', 'structural_schema', 'public_contract', 'parse_answer'}
    constants = {'QUERY_INSTRUCTION', 'ANSWER_INSTRUCTION'}
    selected = []
    for node in ast.parse((runtime / 'retrieval_adapter.py').read_text()).body:
        if isinstance(node, ast.FunctionDef) and node.name in functions:
            selected.append(node)
        elif isinstance(node, ast.Assign) and any((isinstance(t, ast.Name) and t.id in constants for t in node.targets)):
            selected.append(node)
    retrieval = {'json': json}
    exec(compile(ast.Module(body=selected, type_ignores=[]), '<pinned AUTH37 retrieval pure definitions>', 'exec'), retrieval)
    if not functions | constants <= set(retrieval):
        raise ValueError('saved evidence invariant failed')
    (expected, structured_tasks) = ({}, {})
    for (ident, public) in public_by_id.items():
        wg = public['wg']
        for (arm, kind, tag) in [('A', 'graph', 'Text2Cypher'), ('B', 'sql', 'Text2SQL')]:
            task = dict(public)
            task[kind + '_schema'] = load(current / 'schemas' / (wg + '_' + kind + '.json'))
            structured_tasks[ident, tag] = task
            expected[ident + '_' + tag] = adapter.messages_for(task, arm)
        for arm in ('C', 'D'):
            base = current / 'retrieval' / arm / ident
            (initial, final) = (load(base / 'initial_context.json'), load(base / 'final_context.json'))
            prefix = retrieval['canonical']({'question': public['question_en'], 'contract': retrieval['public_contract'](public)}) + '\nSOURCE PASSAGES:\n'
            if arm == 'D':
                expected[ident + '_D_followup'] = [{'role': 'system', 'content': retrieval['QUERY_INSTRUCTION']}, {'role': 'user', 'content': prefix + '\n\n'.join((d['formatted'] for d in initial['documents']))}]
            expected[ident + '_' + arm + '_answer'] = [{'role': 'system', 'content': retrieval['ANSWER_INSTRUCTION']}, {'role': 'user', 'content': prefix + '\n\n'.join((d['formatted'] for d in final['documents']))}]
    request_rows = [load(p) for p in (current / 'calls').glob('*.request.json')]
    requests = {r['request_id']: r for r in request_rows}
    if not (len(request_rows) == len(requests) == len(expected) == 10 and set(requests) == set(expected)):
        raise ValueError('saved evidence invariant failed')
    outcomes = {}
    for (identifier, request) in requests.items():
        if not request['payload']['messages'] == expected[identifier]:
            raise ValueError(identifier)
        outcomes[identifier] = load(current / 'calls' / (identifier + '.outcome.json'))

    class SavedCaller:

        def call(self, request_id, messages, **kwargs):
            if not messages == expected[request_id]:
                raise ValueError('saved evidence invariant failed')
            return outcomes[request_id]
    (read_guards, statuses, parse_failures) = ([], {}, 0)
    for (ident, public) in public_by_id.items():
        statuses[ident] = {}
        for (method, tag) in [('text2cypher', 'Text2Cypher'), ('text2sql', 'Text2SQL')]:
            saved = load(current / 'predictions' / tag / (ident + '.json'))
            executed = load(current / 'executed' / method / (ident + '.json'))
            with tempfile.TemporaryDirectory(prefix='spectra-auth25-offline-parser-') as temporary:
                replay = adapter.evaluate(structured_tasks[ident, tag], tag, SavedCaller(), Path(temporary))
            if not replay == saved:
                raise ValueError((ident, tag, 'generation parser'))
            if replay['status'] != 'QUERY_READY':
                if not adapter.execute_generated(replay, public) == executed:
                    raise ValueError('saved evidence invariant failed')
                read_guards.append({'id': ident, 'method': tag, 'status': executed['status'], 'nonready_passthrough': True})
            else:
                if not executed['generated_query'] == replay['generated_query']:
                    raise ValueError('saved evidence invariant failed')
                if not executed['query_sha256'] == replay['query_sha256']:
                    raise ValueError('saved evidence invariant failed')
                execution = executed['execution']
                if not execution is not None:
                    raise ValueError('saved evidence invariant failed')
                if not executed['records'] == (execution['rows'] if execution['complete'] else []):
                    raise ValueError('saved evidence invariant failed')
                if not executed['abstain'] == (not execution['complete']):
                    raise ValueError('saved evidence invariant failed')
                guard = {'id': ident, 'method': tag, 'status': executed['status'], 'complete': execution['complete'], 'truncated': execution['truncated']}
                if execution['complete']:
                    if not (executed['status'] == 'OK' and (not execution['truncated'])):
                        raise ValueError('saved evidence invariant failed')
                    if tag == 'Text2Cypher':
                        if not execution['plan_query_type'] == execution['execution_query_type'] == 'r':
                            raise ValueError('saved evidence invariant failed')
                        if not (execution['rollback_completed'] and execution['execution_summary_complete']):
                            raise ValueError('saved evidence invariant failed')
                        guard['actual_read_plan_summary_rollback'] = True
                    else:
                        if not execution['immutable_read_only'] is True:
                            raise ValueError('saved evidence invariant failed')
                        guard['actual_immutable_read_only'] = True
                else:
                    guard['partial_rows_not_scored'] = True
                read_guards.append(guard)
            statuses[ident][method] = executed['status']
        for (method, arm) in [('single_retrieval', 'C'), ('iterative_retrieval', 'D')]:
            result = load(current / 'arm_outputs' / method / (ident + '.json'))
            if not result == load(current / 'retrieval' / arm / ident / 'result.json'):
                raise ValueError('saved evidence invariant failed')
            outcome = outcomes[ident + '_' + arm + '_answer']
            if outcome.get('finish_reason') == 'length':
                if not (result['status'] == 'output_truncated' and result['records'] == []):
                    raise ValueError('saved evidence invariant failed')
            elif not outcome.get('ok') or outcome.get('finish_reason') != 'stop':
                if not (result['status'] == 'answer_failed' and result['records'] == []):
                    raise ValueError('saved evidence invariant failed')
            else:
                try:
                    parsed = retrieval['parse_answer'](outcome['content'])
                except (ValueError, TypeError, KeyError) as error:
                    if not result['status'] == 'answer_parse_error':
                        raise ValueError('saved evidence invariant failed')
                    if not (result['records'] == [] and result['error'] == str(error)):
                        raise ValueError('saved evidence invariant failed')
                    parse_failures += 1
                else:
                    if not result['status'] == ('abstained' if parsed['abstain'] else 'ok' if parsed['complete'] else 'partial'):
                        raise ValueError('saved evidence invariant failed')
                    if not (result['records'] == parsed['records'] and result['abstain'] == parsed['abstain']):
                        raise ValueError('saved evidence invariant failed')
                    if not result['self_reported_complete'] == parsed['complete']:
                        raise ValueError('saved evidence invariant failed')
            if not result['source_cutoff_relation_to_frozen_graph'] == 'UNKNOWN':
                raise ValueError('saved evidence invariant failed')
            if not result['requested_population_completeness_verified'] is False:
                raise ValueError('saved evidence invariant failed')
            statuses[ident][method] = result['status']
    for wg in {p['wg'] for p in public_by_id.values()}:
        guard = load(current / 'source_guards' / (wg + '.json'))
        if not guard['before'] == guard['after'] == protocol['graph_sources'][wg]:
            raise ValueError('saved evidence invariant failed')
    return {'status': 'PASS', 'question_n': 2, 'prompt_reconstruction_n': 10, 'output_parser_replay_n': 8, 'structured_generation_parser_replay_n': 4, 'retrieval_parse_failure_replay_n': parse_failures, 'saved_structured_read_guard_paths': read_guards, 'actual_statuses': statuses, 'new_model_or_database_calls_n': 0, 'source_order_or_exact_share_hooks_installed': False, 'retrieval_parser': 'Direct original parse_answer from registered AUTH37 bytes', 'portable_AST_retrieval_projection': True, 'limits': 'Saved parser and guard evidence replay; no live query/corpus execution or physical-source completeness claim.'}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = verify(args.evidence)
    if args.out:
        if not not args.out.exists():
            raise ValueError('Preserve earlier receipts')
        if not not args.out.resolve().is_relative_to(args.evidence.resolve()):
            raise ValueError('saved evidence invariant failed')
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
