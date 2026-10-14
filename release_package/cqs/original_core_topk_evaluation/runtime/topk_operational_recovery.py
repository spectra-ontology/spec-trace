#!/usr/bin/env python3
"""Recover only pre-answer HTTP402 stages; preserve the original TOP10 phase."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
sys.path.insert(0,str(BASE))
import run_evaluation as runtime
import structured_adapter as structured
import retrieval_adapter as retrieval
from openrouter_client import OpenRouterCaller, MODEL, PROVIDER


def outcome_path(request):
    return request.with_name(request.name.replace('.request.json','.outcome.json'))


def request_payload(messages, max_tokens):
    return {'model':MODEL,'messages':messages,'max_tokens':int(max_tokens),
            'provider':{'only':[PROVIDER],'allow_fallbacks':False,'require_parameters':True},
            'response_format':{'type':'json_object'},'reasoning':{'enabled':False},'stream':False}


def freeze(bundle, parent, original, run):
    import topk_current_evaluation
    protocol=topk_current_evaluation.verify(bundle,parent,original)
    if run.exists() or not (original/'generation_complete.json').exists():
        raise ValueError('Recovery exists or original generation is incomplete')
    selected=[]
    stages=[]
    for task in runtime.read(original/'public_tasks.jsonl'):
        for arm,name in runtime.ARMS.items():
            path=original/'arm_outputs'/name/(task['id']+'.json')
            record=json.loads(path.read_text())
            calls=[record['call']] if arm in {'A','B'} else record.get('calls',[])
            failed=[]
            for call in calls:
                if call.get('error')!='http_402':
                    continue
                request=Path(call['request_path']); response=Path(call['response_path'])
                raw=json.loads(response.read_text())
                saved=json.loads(outcome_path(request).read_text())
                error=raw.get('response',{}).get('error',{})
                if (raw.get('http_status')!=402 or raw.get('response',{}).get('choices')
                        or saved.get('content') is not None or saved.get('ok') is not False
                        or error.get('metadata',{}).get('reason')!='in_flight_budget_exhausted'):
                    raise ValueError('Stage is not a verified pre-answer in-flight 402')
                request_id=json.loads(request.read_text())['request_id']
                failed.append(request_id)
                stages.append({'request_id':request_id,'original_request_file':str(request.relative_to(original)),
                               'original_request_sha256':runtime.sha(request),
                               'original_response_file':str(response.relative_to(original)),
                               'original_response_sha256':runtime.sha(response),
                               'original_outcome_file':str(outcome_path(request).relative_to(original)),
                               'original_outcome_sha256':runtime.sha(outcome_path(request)),
                               'http_status':402,'actual_model_response_received':False})
            if failed:
                selected.append({'id':task['id'],'arm':arm,'method':name,
                                 'original_status':record['status'],'pre_answer_stages':failed,
                                 'original_prediction_sha256':runtime.sha(path)})
    if len(selected)!=15 or len(stages)!=15:
        raise ValueError('Unexpected original operational-failure scope')
    original_usage=json.loads((original/'usage.json').read_text())
    if original_usage['unknown_cost_attempts']!=0:
        raise ValueError('Original spend has unknown cost')
    budget=min(2.2,protocol['budget_guard_usd']-original_usage['known_actual_cost_usd'])
    if budget<=0:
        raise ValueError('No original spending guard remains')
    run.mkdir(parents=True)
    for name in ['public_tasks.jsonl','retrieval_corpus_inventory.json','retrieval_protocol.json']:
        if (original/name).exists():shutil.copy2(original/name,run/name)
    shutil.copytree(original/'schemas',run/'schemas')
    preserved={str(p.relative_to(original)):runtime.sha(p) for p in sorted(original.rglob('*'))
               if p.is_file() and not any(x in {'executed','source_guards','__pycache__'} for x in p.relative_to(original).parts)}
    new=dict(protocol)
    new['frozen_utc']=datetime.now(timezone.utc).isoformat()
    new['budget_guard_usd']=budget
    new['generation_workers']=1
    new['code_pins']=dict(protocol['code_pins'],topk_operational_recovery=runtime.sha(__file__))
    # Code-pins are interpreted as actual filenames by the shared verifier.
    new['code_pins']['topk_operational_recovery.py']=new['code_pins'].pop('topk_operational_recovery')
    new['schema_pins']={str(p.relative_to(run)):runtime.sha(p) for p in sorted((run/'schemas').glob('*.json'))}
    new['operational_recovery']={
        'kind':'Only original pre-answer in-flight-budget HTTP402 stages',
        'original_phase':str(original),'original_protocol_sha256':runtime.sha(original/'protocol.json'),
        'original_usage_sha256':runtime.sha(original/'usage.json'),
        'original_known_cost_usd':original_usage['known_actual_cost_usd'],
        'combined_spending_guard_usd':protocol['budget_guard_usd'],
        'original_artifact_pins':preserved,'selected_method_items':selected,'selected_stages':stages,
        'selected_n':len(selected),'pre_answer_http402_n':len(stages),
        'max_new_calls_without_transport_retry':18,
        'new_first_answer_stages_allowed':[row['id']+'_D_answer' for row in selected
                                          if row['arm']=='D' and row['pre_answer_stages']==[row['id']+'_D_followup']],
        'minimum_seconds_between_call_starts':5,'generation_workers':1,
        'already_received_model_responses_reissued':False,
        'identical_payload_on_pre_answer_retry':True,'same_model_provider_schemas_token_limits':True,
        'quality_retry':False,
        'retrieval_context_policy':'Reuse exact recorded pre-failure rounds and contexts; a first second retrieval after a newly recovered followup uses the same frozen index and limits.',
        'previous_successful_followup_policy':'Reuse exact recorded response without a paid request; record reuse separately.',
        'score_policy':'Preserve original phase; report operationally recovered predictions and any combined results separately.',
        'new_model_calls_before_registration':0}
    runtime.write(run/'protocol.json',new)
    print(json.dumps({'status':'FROZEN_OPERATIONAL_TOP10','selected_method_items':15,
                      'pre_answer_stages':15,'max_new_calls':18,'budget_guard_usd':budget,
                      'protocol_sha256':runtime.sha(run/'protocol.json')}),flush=True)


def verify(bundle,original,run):
    protocol=runtime.verify_pins(bundle,run)
    recovery=protocol['operational_recovery']
    for name,expected in recovery['original_artifact_pins'].items():
        if runtime.sha(original/name)!=expected:
            raise ValueError('Original phase artifact changed: '+name)
    return protocol


def generate(bundle,original,run):
    protocol=verify(bundle,original,run)
    recovery=protocol['operational_recovery']
    sys.path.insert(0,str(runtime.ROOT/'scripts/common/common'))
    import credentials
    native=OpenRouterCaller(run,credentials.secret('OPENROUTER_API_KEY'),protocol['budget_guard_usd'])
    permitted={row['request_id'] for row in recovery['selected_stages']}
    new_first=set(recovery['new_first_answer_stages_allowed'])
    routes=[]
    last_start=None

    class Caller:
        def call(self,request_id,messages,max_tokens=8192):
            nonlocal last_start
            payload=request_payload(messages,max_tokens)
            old_request=original/'calls'/(request_id+'.request.json')
            old_outcome=None
            if old_request.exists():
                old=json.loads(old_request.read_text())
                if old['payload']!=payload:
                    raise ValueError('Recovery payload changed: '+request_id)
                old_outcome=json.loads(outcome_path(old_request).read_text())
            if request_id not in permitted:
                if old_outcome is not None:
                    if old_outcome.get('content') is None or not old_outcome.get('ok'):
                        raise ValueError('Unselected failed stage cannot be retried')
                    result=copy.deepcopy(old_outcome)
                    result['original_known_actual_cost_usd']=result.get('known_actual_cost_usd')
                    result['known_actual_cost_usd']=0.0
                    result['unknown_cost_attempts']=0
                    result['operational_cached_response']=True
                    routes.append({'request_id':request_id,'route':'reuse_received_response','new_paid_request':False,
                                   'original_request_sha256':runtime.sha(old_request),
                                   'original_outcome_sha256':runtime.sha(outcome_path(old_request))})
                    runtime.write(run/'stage_routes.json',routes)
                    return result
                if request_id not in new_first:
                    raise ValueError('Unregistered new stage')
            elif old_outcome is None or old_outcome.get('content') is not None:
                raise ValueError('Permitted recovery stage already has a model response')
            if last_start is not None:
                time.sleep(max(0,5-(time.monotonic()-last_start)))
            last_start=time.monotonic()
            result=native.call(request_id,messages,max_tokens=max_tokens)
            routes.append({'request_id':request_id,'route':'identical_pre_answer_retry' if old_request.exists() else 'first_answer_after_recovered_followup',
                           'new_paid_request':bool(result.get('request_path')),
                           'old_payload_sha256':json.loads(old_request.read_text())['payload_sha256'] if old_request.exists() else None,
                           'new_request_file':str(Path(result['request_path']).relative_to(run)) if result.get('request_path') else None,
                           'actual_model_response_received':result.get('content') is not None,'error':result.get('error')})
            runtime.write(run/'stage_routes.json',routes)
            return result

    caller=Caller()
    tasks={task['id']:task for task in runtime.read(run/'public_tasks.jsonl')}
    counts={}
    for index,trial in enumerate(recovery['selected_method_items'],1):
        task=dict(tasks[trial['id']]);arm=trial['arm'];method=trial['method']
        target=run/'arm_outputs'/method/(trial['id']+'.json')
        if target.exists():raise ValueError('Existing recovery prediction; no quality rerun')
        try:
            if arm in {'A','B'}:
                kind='graph' if arm=='A' else 'sql'
                task[kind+'_schema']=json.loads((run/'schemas'/(task['wg']+'_'+kind+'.json')).read_text())
                result=structured.evaluate(task,arm,caller,run)
            else:
                # Avoid time-bounded FTS recomputation changing an already
                # serialized request. Only the not-yet-performed second round
                # after a recovered followup may conduct fresh retrieval.
                old_dir=original/'retrieval'/arm/task['id']
                old_retrieve,old_contexts=retrieval.retrieve,retrieval.contexts
                counters={'retrieve':0,'contexts':0}
                def cached_retrieve(*args,**kwargs):
                    counters['retrieve']+=1
                    saved=old_dir/('retrieval_round_'+str(counters['retrieve'])+'.json')
                    return json.loads(saved.read_text()) if saved.exists() else old_retrieve(*args,**kwargs)
                def cached_contexts(*args,**kwargs):
                    counters['contexts']+=1
                    saved=old_dir/('initial_context.json' if counters['contexts']==1 else 'final_context.json')
                    if saved.exists():
                        context=json.loads(saved.read_text())
                        return context['documents'],context['stats']
                    return old_contexts(*args,**kwargs)
                retrieval.retrieve,retrieval.contexts=cached_retrieve,cached_contexts
                try:
                    result=retrieval.evaluate(task,arm,caller,run)
                finally:
                    retrieval.retrieve,retrieval.contexts=old_retrieve,old_contexts
        except Exception as exc:
            result={'id':task['id'],'repair_sha256':task['repair_sha256'],'records':[],
                    'status':'ADAPTER_EXCEPTION','error_type':type(exc).__name__,'error':str(exc)[:1000]}
        runtime.write(target,result)
        counts[result['status']]=counts.get(result['status'],0)+1
        print(json.dumps({'completed_method_items':index,'required':len(recovery['selected_method_items']),
                          'id':task['id'],'arm':arm,'status':result['status']}),flush=True)
    verify(bundle,original,run)
    runtime.write(run/'generation_complete.json',{'completed_method_items':15,'required':15,
                   'status_counts':counts,'original_phase_unchanged':True,
                   'only_pre_answer_stages_reissued':True,'quality_retries':0})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['freeze','generate'])
    for name in ['bundle','parent','original','run-dir']:
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    values=[getattr(args,name).resolve() for name in ['bundle','parent','original','run_dir']]
    if args.action=='freeze':freeze(*values)
    else:generate(values[0],values[2],values[3])
