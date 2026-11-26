"""Collect observed local subject provenance and commit unscored first outputs.

Read only this study's fresh child transcripts; retain extracted tool calls for
independent scope review. Model fields describe recorded session configuration.
"""
import collections
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT_THREAD = '01a20f8a-39e9-7b21-96f6-08ef861324a6'
TRACE_ROOT = Path('/home/sihyeon/.codex/sessions/2026/11/26')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def save(p, v):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n')

def main():
    spec = importlib.util.spec_from_file_location('study_commit', HERE/'harness.py')
    harness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(harness)
    harness.check_lock()
    schedule = json.loads((HERE/'schedule.json').read_text())
    reports = []
    for trace in sorted(TRACE_ROOT.glob('*.jsonl')):
        with trace.open() as f:
            first = json.loads(next(f))
        meta = first.get('payload', {})
        child = meta.get('source', {}).get('subagent', {})
        spawn = child.get('thread_spawn', {}) if isinstance(child, dict) else {}
        if spawn.get('parent_thread_id') != ROOT_THREAD or not spawn.get('agent_path', '').startswith('/root/subject_'):
            continue
        records = [json.loads(x) for x in trace.read_text().splitlines() if x.strip()]
        calls, finals, contexts, usage = [], [], [], {}
        for record in records:
            payload = record.get('payload', {})
            if record.get('type') == 'turn_context':
                contexts.append({'model': payload.get('model'), 'effort': payload.get('effort')})
            if record.get('type') == 'response_item':
                if payload.get('type') in ['function_call', 'custom_tool_call']:
                    calls.append({'timestamp': record.get('timestamp'), 'name': payload.get('name'),
                                  'arguments': payload.get('arguments', payload.get('input', ''))})
                if payload.get('type') == 'message' and payload.get('role') == 'assistant' and (payload.get('channel') == 'final' or payload.get('phase') == 'final_answer'):
                    finals.append(payload.get('content'))
            if record.get('type') == 'token_usage_record':
                response = payload.get('response_id')
                if response:
                    assert response not in usage or usage[response] == payload.get('usage'), 'Conflicting response usage'
                    usage[response] = payload.get('usage', {})
        carrier = json.dumps(calls, ensure_ascii=False) + json.dumps(finals, ensure_ascii=False)
        matches = [r for r in schedule if r['runId']+'.json' in carrier]
        if len(matches) != 1:
            continue
        run = matches[0]
        raw = HERE/'incoming'/(run['runId']+'.json')
        if not raw.is_file() or not finals or raw.name not in json.dumps(finals[-1]):
            continue
        models = sorted({c['model'] for c in contexts})
        efforts = sorted({c['effort'] for c in contexts})
        assert models == [run['requestedModel']] and efforts == ['medium'], (run['runId'], contexts)
        totals = dict(collections.Counter())
        for u in usage.values():
            for k, v in u.items():
                if isinstance(v, int): totals[k] = totals.get(k, 0) + v
        packet = str(HERE/run['packet'])
        tools = sorted(set(re.findall(r'tools\.([A-Za-z_][A-Za-z_0-9]*)', carrier)))
        paths = sorted(set(re.findall(r'/home/sihyeon/[^\s"\'`\\\)\];,]+', carrier)))
        out_of_scope_paths = [p for p in paths if p not in {packet, str(raw)}]
        unexpected_tools = [t for t in tools if t not in {'exec_command', 'apply_patch'}]
        report = {'runId': run['runId'], 'subjectAgentPath': spawn['agent_path'],
                  'subjectThreadId': meta.get('id'), 'recordedSessionModels': models,
                  'recordedEfforts': efforts, 'identityEvidence': 'Local turn_context configuration, not a separate provider routing certificate',
                  'traceFile': str(trace), 'traceSha256': sha(trace), 'rawSha256': sha(raw),
                  'firstRecordAt': records[0].get('timestamp'), 'lastRecordAt': records[-1].get('timestamp'),
                  'deduplicatedResponseUsage': totals, 'responseIdsCount': len(usage),
                  'observedNestedTools': tools, 'observedAbsolutePaths': paths,
                  'outOfScopePathFlags': out_of_scope_paths, 'unexpectedToolFlags': unexpected_tools,
                  'semanticToolScopeReview': 'pending independent review of retained exact tool calls',
                  'toolCalls': calls, 'finalMessages': finals}
        save(HERE/'provenance'/(run['runId']+'.json'), report)
        destination = HERE/'submissions'/run['runId']
        if not (destination/'commitment.json').exists():
            receipt = {'requestedModel': run['requestedModel'], 'subjectSessionId': meta.get('id'),
                       'subjectAgentPath': spawn['agent_path'], 'forkTurns': 'none', 'reasoningEffort': 'medium',
                       'firstSubmission': True, 'feedbackBeforeSubmission': False, 'actualModels': models,
                       'identityEvidence': report['identityEvidence'], 'backendIdentityIndependentlyVerified': False,
                       'provenanceFile': str(HERE/'provenance'/(run['runId']+'.json')),
                       'traceSha256': report['traceSha256']}
            receipt_path = HERE/'incoming'/(run['runId']+'.receipt.json')
            assert not receipt_path.exists(), 'Existing receipt must remain unchanged'
            save(receipt_path, receipt)
            harness.commit(run['runId'], raw, receipt_path)
        reports.append({k:report[k] for k in ['runId', 'subjectAgentPath', 'subjectThreadId', 'recordedSessionModels', 'recordedEfforts', 'rawSha256', 'outOfScopePathFlags', 'unexpectedToolFlags']})
    save(HERE/'session_collection.json', {'collectedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'scope':'Observed session configuration and instruction-scope flags; scores remain withheld', 'runs':reports})
    print(json.dumps({'committed':len(reports), 'flagged':[r['runId'] for r in reports if r['outOfScopePathFlags'] or r['unexpectedToolFlags']]}))

if __name__ == '__main__':
    main()
