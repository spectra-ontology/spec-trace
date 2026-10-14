#!/usr/bin/env python3
"""First calls for two arms rejected by an adapter before their first request.

The original run is never edited. Freeze must precede generate. This does not
retry a received model answer, or change any question, contract or context cap.
"""
import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile

BASE = Path(__file__).resolve().parent
EMP = BASE.parent
ROOT = next(p for p in BASE.parents if (p / '.git').exists())
ORIGINAL = EMP / 'runs/final-three-additions'
RUN = EMP / 'runs/final-three-sequence-adapter-recovery'
IDENTIFIER = 'RAN1_P3_CQ003'
METHODS = {'C': 'single_retrieval', 'D': 'iterative_retrieval'}
REQUESTS = [IDENTIFIER + suffix for suffix in ('_C_answer', '_D_followup', '_D_answer')]
sys.path.insert(0, str(EMP))
import openrouter_client
import owner_contract_evaluation as owner


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write_new(path, value):
    path = Path(path)
    if path.exists():
        raise ValueError('Immutable artifact already exists: ' + path.name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def inventory(path):
    return {str(p.relative_to(path)): sha(p) for p in sorted(path.rglob('*')) if p.is_file()}


def adapter():
    spec = importlib.util.spec_from_file_location('sequence_retrieval', BASE / 'retrieval_adapter_sequence.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def gate_only_change():
    old = (EMP / 'retrieval_adapter.py').read_bytes()
    token = b"mode not in {'set', 'list', 'ordered', 'multiset'}"
    replacement = b"mode not in {'set', 'list', 'ordered', 'multiset', 'sequence'}"
    if old.count(token) != 1 or (BASE / 'retrieval_adapter_sequence.py').read_bytes() != old.replace(token, replacement):
        raise ValueError('Correction must only add the existing sequence contract mode')


def absent_before_call():
    calls = inventory(ORIGINAL / 'calls')
    for request_id in REQUESTS:
        if any(Path(name).name.startswith(request_id + '.') for name in calls):
            raise ValueError('Prior call exists; this is not a first-call recovery')
    outcomes = {}
    for arm, method in METHODS.items():
        p = ORIGINAL / 'arm_outputs' / method / (IDENTIFIER + '.json')
        outcome = read(p)
        if outcome.get('status') != 'ADAPTER_EXCEPTION' or outcome.get('error') != 'Invalid structural nested-array semantics':
            raise ValueError('Original terminal state is not the specific pre-call adapter error')
        directory = ORIGINAL / 'retrieval' / arm / IDENTIFIER
        if list(directory.iterdir()):
            raise ValueError('Original retrieval directory contains post-contract work')
        outcomes[arm] = {'file': str(p.relative_to(ORIGINAL)), 'sha256': sha(p), 'outcome': outcome,
                         'retrieval_directory_empty': True}
    return {'request_ids_absent': REQUESTS, 'original_call_file_inventory': calls,
            'original_outcomes': outcomes, 'original_received_response_calls': read(ORIGINAL / 'usage.json')['received_response_calls']}


def offline_tests(task):
    """Exercise the failing mode and the actual C/D entry points without calls."""
    module = adapter()
    old_spec = importlib.util.spec_from_file_location('old_retrieval_for_test', EMP / 'retrieval_adapter.py')
    old = importlib.util.module_from_spec(old_spec)
    old_spec.loader.exec_module(old)
    try:
        old.public_contract(task)
    except ValueError as exc:
        assert str(exc) == 'Invalid structural nested-array semantics'
    else:
        raise AssertionError('Original adapter did not exhibit the retained failure')
    assert module.public_contract(task)['required_fields'][0]['nested_array_semantics'] == {'$': 'sequence'}
    bad = json.loads(json.dumps(task))
    bad['required_fields'][0]['nested_array_semantics'] = {'$': 'invented_mode'}
    try:
        module.public_contract(bad)
    except ValueError:
        pass
    else:
        raise AssertionError('Unsupported mode accepted')
    with tempfile.TemporaryDirectory() as temp:
        class FakeCaller:
            def __init__(self): self.ids = []
            def call(self, request_id, messages, max_tokens=8192):
                self.ids.append(request_id)
                assert task['question_en'] in messages[1]['content']
                assert 'sequence' in messages[1]['content']
                content = json.dumps({'query': 'breadcrumb parent clause'}) if request_id.endswith('_followup') else json.dumps({'records': [], 'abstain': True, 'complete': False})
                return {'ok': True, 'finish_reason': 'stop', 'content': content}
        module.prepare_corpus_inventory = lambda run: {'shards': [{'WG': 'RAN1', 'path': 'unused', 'sha256': '0'*64}]}
        module.retrieve = lambda *args: {'status': 'ok', 'hits': []}
        module.contexts = lambda *args: ([], {'document_selection_truncated': False})
        for arm, expected in [('C', REQUESTS[:1]), ('D', REQUESTS[1:])]:
            caller = FakeCaller()
            output = module.evaluate(task, arm, caller, Path(temp))
            assert caller.ids == expected and output['status'] == 'abstained'
    return {'status': 'PASS', 'checks': ['original sequence rejection', 'sequence preserved in structural contract',
              'unsupported mode rejected', 'C first-answer path', 'D followup and answer path'], 'paid_calls': 0}


def freeze():
    if RUN.exists():
        raise ValueError('Recovery directory already exists')
    gate_only_change()
    proof = absent_before_call()
    tasks = [json.loads(line) for line in (ORIGINAL / 'public_tasks.jsonl').read_text().splitlines() if line.strip()]
    task = next(t for t in tasks if t['id'] == IDENTIFIER)
    tests = offline_tests(task)
    original_inventory = inventory(ORIGINAL)
    original_protocol = read(ORIGINAL / 'protocol.json')
    corpus = read(ORIGINAL / 'retrieval_corpus_inventory.json')
    shard = next(s for s in corpus['shards'] if s['WG'] == 'RAN1')
    source_path = ROOT / shard['path']
    before = source_path.stat()
    fresh_source_sha = sha(source_path)
    after = source_path.stat()
    if fresh_source_sha != shard['sha256'] or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('Retained retrieval shard differs from original source')
    remaining = Decimal(str(original_protocol['budget_guard_usd'])) - Decimal(str(read(ORIGINAL/'usage.json')['guard_reserved_or_spent_usd']))
    if remaining <= 0:
        raise ValueError('Original experimental spending guard exhausted')
    RUN.mkdir(parents=True)
    for name in ['retrieval_corpus_inventory.json', 'retrieval_protocol.json']:
        shutil.copy2(ORIGINAL/name, RUN/name)
    for entry in original_protocol['common_source_interface']['sources']:
        target = RUN / entry['file']; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ORIGINAL/entry['file'], target)
        if sha(target) != entry['sha256']:
            raise ValueError('Shared source changed')
    (RUN / 'public_tasks.jsonl').write_text(json.dumps(task, ensure_ascii=False)+'\n')
    write_new(RUN / 'original_absence_proof.json', proof)
    write_new(RUN / 'original_run_inventory.json', original_inventory)
    write_new(RUN / 'offline_tests.json', tests)
    protocol = {'kind': 'First-call recovery after a pre-API structural-contract adapter exception',
        'frozen_utc': datetime.now(timezone.utc).isoformat(), 'original_run': str(ORIGINAL.relative_to(ROOT)),
        'original_protocol_sha256': sha(ORIGINAL/'protocol.json'), 'original_inventory_sha256': sha(RUN/'original_run_inventory.json'),
        'original_absence_proof_sha256': sha(RUN/'original_absence_proof.json'),
        'selected_id': IDENTIFIER, 'selected_arms': list(METHODS), 'request_ids': REQUESTS,
        'repair_sha256': task['repair_sha256'], 'original_public_tasks_sha256': sha(ORIGINAL/'public_tasks.jsonl'),
        'public_tasks_sha256': sha(RUN/'public_tasks.jsonl'), 'retrieval_inventory_sha256': sha(RUN/'retrieval_corpus_inventory.json'),
        'retrieval_protocol_sha256': sha(RUN/'retrieval_protocol.json'), 'fresh_used_source': {'path': shard['path'], 'sha256': fresh_source_sha,
           'bytes': after.st_size, 'mtime_ns': after.st_mtime_ns, 'other_shards': 'Inherited inventory; not used by these two arms'},
        'model': original_protocol['model'], 'provider': original_protocol['provider'],
        'reasoning': original_protocol['reasoning'], 'response_format': original_protocol['response_format'],
        'retry_policy': original_protocol['retry_policy'], 'retrieval_protocol': original_protocol['retrieval_protocol'],
        'common_source_interface': original_protocol['common_source_interface'],
        'code_pins': {str(p.relative_to(ROOT)): sha(p) for p in [Path(__file__), BASE/'retrieval_adapter_sequence.py',
            EMP/'retrieval_adapter.py', EMP/'openrouter_client.py', EMP/'owner_contract_evaluation.py']},
        'only_code_change': 'Accept sequence as an existing nested-array structural output mode; all other adapter bytes identical.',
        'new_model_responses_before_registration': 0, 'generation_workers': 1, 'max_logical_calls': 3,
        'answer_quality_retry': False, 'other_received_answers_reused_unchanged': True,
        'original_budget_guard_usd': original_protocol['budget_guard_usd'],
        'prior_guard_spend_usd': read(ORIGINAL/'usage.json')['guard_reserved_or_spent_usd'],
        'remaining_budget_guard_usd': float(remaining), 'offline_tests_sha256': sha(RUN/'offline_tests.json')}
    write_new(RUN/'protocol.json', protocol)
    print(json.dumps({'status': 'FROZEN_FIRST_CALL_RECOVERY', 'protocol_sha256': sha(RUN/'protocol.json'),
                      'remaining_budget_guard_usd': float(remaining), 'new_calls': 0}), flush=True)


def generate():
    p = read(RUN/'protocol.json')
    for name, digest in p['code_pins'].items():
        if sha(ROOT/name) != digest: raise ValueError('Frozen recovery code changed')
    for name, digest in [('public_tasks.jsonl', p['public_tasks_sha256']), ('retrieval_corpus_inventory.json', p['retrieval_inventory_sha256']),
                         ('retrieval_protocol.json', p['retrieval_protocol_sha256']), ('original_run_inventory.json', p['original_inventory_sha256']),
                         ('original_absence_proof.json', p['original_absence_proof_sha256'])]:
        if sha(RUN/name) != digest: raise ValueError('Frozen recovery input changed')
    gate_only_change(); absent_before_call()
    if inventory(ORIGINAL) != read(RUN/'original_run_inventory.json'):
        raise ValueError('Original run changed after first-call recovery registration')
    if (RUN/'calls').exists() or (RUN/'arm_outputs').exists():
        raise ValueError('Recovery already started; no outcome-dependent rerun')
    source = ROOT/p['fresh_used_source']['path']
    if sha(source) != p['fresh_used_source']['sha256']:
        raise ValueError('Used retrieval corpus changed before first call')
    task = json.loads((RUN/'public_tasks.jsonl').read_text())
    data = owner.source_data(RUN, p)
    sys.path.insert(0, str(ROOT/'scripts/common/common'))
    import credentials
    class Caller(openrouter_client.OpenRouterCaller):
        def call(self, request_id, messages, max_tokens=8192):
            if request_id not in REQUESTS: raise ValueError('Unexpected recovery request')
            expanded=[dict(m) for m in messages]
            expanded[0]['content']=expanded[0]['content'].replace(
                'using only the original question, requested output format and supplied schema. ',
                'using only the original question, requested output format, supplied schema and common_source_data. ')
            expanded[0]['content']=expanded[0]['content'].replace(
                'No tools, files, internet, external facts, answer literals or unsupported assumptions. ',
                'No tools, files, internet, undisclosed facts, precomputed answer rows or unsupported assumptions. Literal identities and source membership lists in the original question or common_source_data are allowed as query predicates. ')
            expanded[0]['content']+='\n'+owner.INSTRUCTION+' Return only the method-requested JSON object without prose or Markdown.'
            expanded.append({'role':'user','content':json.dumps({'common_source_data':data},ensure_ascii=False,sort_keys=True,separators=(',',':'))})
            result=super().call(request_id, expanded, max_tokens=max_tokens)
            result['common_source_data_sha256']=hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            result['actual_prompt_characters_including_common_source']=sum(len(m['content']) for m in expanded)
            return result
    caller = Caller(RUN, credentials.secret('OPENROUTER_API_KEY'), p['remaining_budget_guard_usd'])
    module = adapter()
    for arm, method in METHODS.items():
        try:
            outcome = module.evaluate(task, arm, caller, RUN)
        except Exception as exc:
            outcome = {'id': IDENTIFIER, 'repair_sha256': task['repair_sha256'], 'records': [],
                       'status': 'ADAPTER_EXCEPTION', 'error_type': type(exc).__name__, 'error': str(exc)[:1000]}
        write_new(RUN/'arm_outputs'/method/(IDENTIFIER+'.json'), outcome)
        print(json.dumps({'arm': arm, 'status': outcome['status']}), flush=True)
    used_sha = sha(source)
    write_new(RUN/'generation_complete.json', {'required': 2, 'completed_method_items': 2, 'max_logical_calls': 3,
        'usage': read(RUN/'usage.json') if (RUN/'usage.json').exists() else None,
        'source_after_sha256': used_sha, 'source_before_after_equal': used_sha == p['fresh_used_source']['sha256'],
        'original_run_unchanged': inventory(ORIGINAL) == read(RUN/'original_run_inventory.json')})
    print(json.dumps({'status': 'RECOVERY_TERMINAL', 'usage': read(RUN/'usage.json')}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['freeze', 'generate'])
    args = parser.parse_args()
    {'freeze': freeze, 'generate': generate}[args.action]()
