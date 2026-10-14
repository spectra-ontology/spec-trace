#!/usr/bin/env python3
"""Offline provenance gate for a pre-call sequence adapter correction.

This reads retained public artifacts only: no network, model call or database
execution. Actual archive coverage and unshipped corpus truth are not inferred.
"""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path

ID = 'RAN1_P3_CQ003'
METHODS = {'C':'single_retrieval','D':'iterative_retrieval'}
REQUESTS = [ID+suffix for suffix in ('_C_answer','_D_followup','_D_answer')]


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path): return json.loads(Path(path).read_text())
def inventory(path): return {str(p.relative_to(path)):sha(p) for p in sorted(path.rglob('*')) if p.is_file()}
def require(condition, message):
    if not condition: raise ValueError(message)


def verify(run):
    run = Path(run)
    proof = load(run/'adapter_pre_call_recovery.json')
    companion = run/'adapter_pre_call_recovery'
    original = companion/'original_run'
    recovery = companion/'recovery_run'
    p = load(recovery/'protocol.json')
    require(inventory(original)==proof['original_run_inventory'], 'Preserved original run bytes differ')
    require(inventory(recovery)==proof['recovery_run_inventory'], 'Retained recovery bytes differ')
    require(sha(recovery/'protocol.json')==proof['recovery_protocol_sha256'], 'Recovery registration pin differs')
    require(sha(original/'protocol.json')==p['original_protocol_sha256']==proof['original_protocol_sha256']==sha(run/'protocol.json'), 'Original frozen protocol changed')
    require(proof['original_run_unchanged'] is True and proof['used_source_before_after_equal'] is True, 'Source/original immutability not retained')
    require(p['selected_id']==ID and p['selected_arms']==['C','D'] and p['request_ids']==REQUESTS, 'First-call recovery scope differs')
    require(p['generation_workers']==1 and p['max_logical_calls']==3 and p['answer_quality_retry'] is False and p['new_model_responses_before_registration']==0, 'Recovery call policy differs')
    require(p['public_tasks_sha256']==sha(recovery/'public_tasks.jsonl'), 'Recovery public task pin differs')
    tasks=[json.loads(s) for s in (original/'public_tasks.jsonl').read_text().splitlines() if s.strip()]
    task=json.loads((recovery/'public_tasks.jsonl').read_text())
    require(task==next(t for t in tasks if t['id']==ID), 'Recovery changed the original model-visible task')
    require(task['repair_sha256']==p['repair_sha256'], 'Repair SHA differs')
    original_p=load(original/'protocol.json')
    for key in ['model','provider','reasoning','response_format','retry_policy','retrieval_protocol','common_source_interface']:
        require(p[key]==original_p[key], 'Frozen generation input or policy differs: '+key)
    require(sha(recovery/'retrieval_corpus_inventory.json')==p['retrieval_inventory_sha256']==sha(original/'retrieval_corpus_inventory.json'), 'Retained corpus inventory differs')
    require(sha(recovery/'retrieval_protocol.json')==p['retrieval_protocol_sha256']==sha(original/'retrieval_protocol.json'), 'Retrieval protocol differs')
    source=next(s for s in load(recovery/'retrieval_corpus_inventory.json')['shards'] if s['WG']=='RAN1')
    require(source['sha256']==p['fresh_used_source']['sha256'], 'Used corpus source differs from original inventory')
    completed=load(recovery/'generation_complete.json')
    require(completed['source_before_after_equal'] is True and completed['source_after_sha256']==source['sha256'] and completed['original_run_unchanged'] is True, 'Retained source hash guard differs')
    require(sha(recovery/'original_absence_proof.json')==p['original_absence_proof_sha256'], 'Absence proof pin differs')
    require(sha(recovery/'original_run_inventory.json')==p['original_inventory_sha256'] and load(recovery/'original_run_inventory.json')==inventory(original), 'Original inventory chain differs')
    absence=load(recovery/'original_absence_proof.json')
    require(inventory(original/'calls')==absence['original_call_file_inventory'], 'Original call inventory differs')
    for request_id in REQUESTS:
        require(not any(q.name.startswith(request_id+'.') for q in (original/'calls').iterdir()), 'An earlier request exists; recovery is not a first call')
    for path,digest in p['code_pins'].items():
        require(sha(run/proof['recovery_code_paths'][path])==digest, 'Frozen corrected execution code differs')
    old=(companion/'runtime/retrieval_adapter.py').read_bytes()
    new=(companion/'runtime/retrieval_adapter_sequence.py').read_bytes()
    token=b"mode not in {'set', 'list', 'ordered', 'multiset'}"
    replacement=b"mode not in {'set', 'list', 'ordered', 'multiset', 'sequence'}"
    require(old.count(token)==1 and new==old.replace(token,replacement), 'Correction changed more than the sequence whitelist')
    require(original_p['code_pins']['retrieval_adapter.py']==sha(companion/'runtime/retrieval_adapter.py') and original_p['code_pins']['owner_contract_evaluation.py']==sha(companion/'runtime/owner_contract_evaluation.py'), 'Original adapter or common-source wrapper changed')
    selected={(item['id'],item['arm']):item for item in proof['replaced_method_outcomes']}
    require(set(selected)=={(ID,'C'),(ID,'D')}, 'Replaced model outcomes differ')
    original_outcomes=[]
    for arm,method in {'A':'text2cypher','B':'text2sql',**METHODS}.items():
        for t in tasks:
            rel=Path('arm_outputs')/method/(t['id']+'.json')
            if (t['id'],arm) in selected:
                item=selected[(t['id'],arm)]
                require(sha(original/rel)==item['original_sha256'] and sha(recovery/rel)==item['recovery_sha256']==sha(run/rel), 'Selected outcome pin differs')
                old_output=load(original/rel)
                require(old_output['status']=='ADAPTER_EXCEPTION' and old_output['error']=='Invalid structural nested-array semantics', 'Prior outcome was not the specific pre-call error')
                # Git and file-only packaging omit empty directories. Validate
                # their recorded absence of files, not directory existence.
                trial_prefix=str(Path('retrieval')/arm/ID)+'/'
                require(absence['original_outcomes'][arm]['retrieval_directory_empty'] is True
                        and not any(name.startswith(trial_prefix) for name in inventory(original)),
                        'Prior retrieval trial contains retained files')
                require(inventory(run/'retrieval'/arm/ID)==inventory(recovery/'retrieval'/arm/ID), 'Actual recovered retrieval artifacts differ')
            else:
                require(sha(original/rel)==sha(run/rel), 'A previously received answer was changed')
                original_outcomes.append(str(rel))
    require(len(original_outcomes)==10 and proof['preserved_original_method_outcomes']==10, 'Original method/outcome preservation differs')
    old_calls=inventory(original/'calls'); new_calls=inventory(recovery/'calls')
    require(not (set(old_calls)&set(new_calls)), 'Recovery retries an earlier model request')
    require(inventory(run/'calls')=={**old_calls,**new_calls}, 'Merged model request inventory differs')
    require({q.name.removesuffix('.request.json') for q in (recovery/'calls').glob('*.request.json')}==set(REQUESTS), 'Recovery contains unexpected or missing logical requests')
    common=[]
    for member in p['common_source_interface']['sources']:
        require(sha(recovery/member['file'])==member['sha256']==sha(original/member['file']), 'Common source bytes differ')
        text=(recovery/member['file']).read_text()
        require(len(text)==member['characters'], 'Common source length differs')
        common.append({'name':member['name'],'source_sha256':member['sha256'],'scope':member['scope'],'complete_source_text':text})
    expected_common={'common_source_data':{'sources':common}}
    cost=0.0; response_n=0
    for request_id in REQUESTS:
        request=load(recovery/'calls'/(request_id+'.request.json'))
        payload=request['payload']
        require(datetime.fromisoformat(request['created_utc'])>=datetime.fromisoformat(p['frozen_utc']), 'Request predates its frozen recovery registration')
        require(payload['model']==p['model'] and payload['provider']['only']==[p['provider']] and payload['provider']['allow_fallbacks'] is False and payload['reasoning']==p['reasoning'] and payload['response_format']==p['response_format'], 'Actual model request policy differs')
        require(request['authorization_header_omitted'] is True and hashlib.sha256(json.dumps(payload,ensure_ascii=False).encode()).hexdigest()==request['payload_sha256'], 'Actual request payload pin differs')
        require(payload['max_tokens']==(1024 if request_id.endswith('_followup') else 8192), 'Original output budget changed')
        require(json.loads(payload['messages'][-1]['content'])==expected_common, 'Actual request omitted or changed common information')
        q=json.loads(payload['messages'][1]['content'].split('\nSOURCE PASSAGES:\n',1)[0])
        require(q['question']==task['question_en'] and q['contract']['required_fields']==task['required_fields'] and q['contract']['collection']==task['collection'], 'Actual prompt changed the original question or requested sequence contract')
        outcome=load(recovery/'calls'/(request_id+'.outcome.json'))
        require(1<=len(outcome['attempts'])<=2, 'Transport attempt limit differs')
        for attempt in outcome['attempts']:
            response=load(recovery/'calls'/(request_id+'.attempt'+str(attempt['attempt'])+'.response.json'))
            if 'response' in response and response.get('http_status')==200:
                response_n+=1
                value=response['response']['usage'].get('cost')
                require(isinstance(value,(int,float)), 'Unexpected unknown response cost')
                cost+=value
            if attempt['attempt']>0:
                previous=outcome['attempts'][attempt['attempt']-1]
                require(previous['retryable'] is True and (previous['http_status'] is None or previous['http_status']==429 or 500<=previous['http_status']<600), 'A received answer was retried')
    usage=load(recovery/'usage.json');original_usage=load(original/'usage.json');merged_usage=load(run/'usage.json')
    require(response_n==usage['received_response_calls']==3 and usage['unknown_cost_attempts']==0 and abs(cost-usage['known_actual_cost_usd'])<1e-12, 'Retained first response/cost totals differ')
    require(abs(original_usage['known_actual_cost_usd']+cost-merged_usage['known_actual_cost_usd'])<1e-12 and merged_usage['received_response_calls']==original_usage['received_response_calls']+3==15, 'Merged response/cost totals differ')
    require(p['remaining_budget_guard_usd']+p['prior_guard_spend_usd']==p['original_budget_guard_usd'] and merged_usage['guard_reserved_or_spent_usd']<=p['original_budget_guard_usd'], 'Original aggregate spending guard changed')
    return {'status':'PASS','kind':'First calls after pre-API sequence adapter correction', 'replaced_method_items':2,
        'preserved_method_items':10,'first_logical_requests':3,'first_received_response_calls':3,
        'original_received_response_calls':original_usage['received_response_calls'],'merged_received_response_calls':15,
        'first_known_actual_cost_usd':cost,'merged_known_actual_cost_usd':merged_usage['known_actual_cost_usd'],
        'original_protocol_sha256':sha(original/'protocol.json'),'recovery_protocol_sha256':sha(recovery/'protocol.json'),
        'answer_quality_retries':0,'new_api_calls_during_verification':0,'new_database_executions_during_verification':0,
        'original_artifacts_preserved':True,'scope':'Pinned artifact provenance; not raw archive factual completeness or expert validation.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.resolve().is_relative_to(a.run.resolve()): raise ValueError('Output must be outside retained run')
    result=verify(a.run)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result))
