#!/usr/bin/env python3
"""Separately registered recovery of exact pre-provider OpenRouter 402 failures.

Never edits or reruns original artifacts. Model calls occur only in CLI `run`.
Real original model outputs, including malformed/truncated outputs, are reused.
Stored original retrieval rounds/context are reused; an originally rejected D
followup can conditionally produce its missing round2 and final answer.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request

BASE=Path(__file__).resolve().parent
ROOT=next(p for p in BASE.parents if (p/'.git').exists())
DEFAULT_ORIGINAL=BASE/'runs/additional-originals'
DEFAULT_SUPPLEMENT=BASE/'runs/additional-originals-transport-supplement'
DEFAULT_BUNDLE=BASE.parent/'original_repair/extension_bundle'
ARMS={'A':'text2cypher','B':'text2sql','C':'single_retrieval','D':'iterative_retrieval'}
OFFICIAL=['https://openrouter.ai/docs/api_reference/limits','https://openrouter.ai/docs/api_reference/errors-and-debugging']


def utc():return datetime.now(timezone.utc).isoformat()


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text())


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():raise ValueError('Recovery artifact already exists; no answer-quality rerun: '+str(path))
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def serialized(payload):return json.dumps(payload,ensure_ascii=False).encode()


def exact_budget_rejection(value):
    response=value.get('response') or {};error=response.get('error') or {};metadata=error.get('metadata') or {}
    code=value.get('http_status')
    exact=((code==402 and metadata.get('limit_source')=='openrouter_in_flight_budget')
           or (code==403 and metadata.get('limit_source')=='openrouter_key_limit'))
    return exact and error.get('code')==code and not response.get('choices')


def eligible(original,request_id):
    request=original/'calls'/(request_id+'.request.json')
    outcome=original/'calls'/(request_id+'.outcome.json')
    if not request.exists() or not outcome.exists():return False
    value=read(outcome);attempts=value.get('attempts') or []
    if not attempts or value.get('ok'):return False
    responses=[read(Path(a['response_path'])) for a in attempts]
    if any((r.get('response') or {}).get('choices') for r in responses):return False
    return exact_budget_rejection(responses[-1])


def freeze(original,supplement,bundle):
    original=original.resolve();supplement=supplement.resolve();bundle=bundle.resolve()
    if (supplement/'protocol.json').exists():raise ValueError('Supplement already frozen')
    p=read(original/'protocol.json')
    if p['admitted_n']!=21:raise ValueError('Expected fixed21 cohort; no silent denominator change')
    for name,pin in p['code_pins'].items():
        if sha(BASE/name)!=pin:raise ValueError('Original runtime changed')
    if sha(bundle/'manifest.json')!=p['bundle_manifest_sha256']:raise ValueError('Original21 bundle changed')
    supplement.mkdir(parents=True,exist_ok=True)
    for name in ['public_tasks.jsonl','retrieval_protocol.json','retrieval_corpus_inventory.json']:
        shutil.copyfile(original/name,supplement/name)
    shutil.copytree(original/'schemas',supplement/'schemas')
    policy={'registered_utc':utc(),'original_run':str(original),'original_protocol_sha256':sha(original/'protocol.json'),
            'recovery_implementation_sha256':sha(__file__),'official_primary_sources':OFFICIAL,
            'eligibility':'Original final HTTP402/error.code402/exact metadata.limit_source=openrouter_in_flight_budget OR HTTP403/error.code403/exact metadata.limit_source=openrouter_key_limit; no provider choices in any retained original attempt. No real model output, parse/quality failure, generic403 or other402 is eligible. Root must confirm key infrastructure unblocked and paid-start/cost cap before run.',
            'request_identity':'Use original retained payload and its exact serialized SHA. No changes to model/provider/messages/max_tokens/format/reasoning/tools/context.',
            'cached_output_policy':'Reuse all original noneligible outcomes unchanged; no model request for cached real outputs. Preserve all original failures and original21 denominator.',
            'retrieval_policy':'Never rerun initial retrieval or recompute an old final context. Replay C/D answer payload exactly from retained request. Only a rejected D followup may continue with saved original round1+initialcontext, one bounded new round2 and its first final-answer request.',
            'conditional_D_answer':'If the original D followup was eligible and the replay yields one valid query, run one second search under the unchanged frozen retrieval protocol, assemble context with the saved original round1, then make the previously nonexistent final answer call. Never retry malformed/truncated followup for quality.',
            'workers':1,'shared_backoff_seconds':120,'respect_Retry_After':True,
            'rejected_original_stage_max_new_attempts':4,'max_preprovider_402_replay_attempts':3,
            'transport_retry_extra_attempts':1,'transport_retry_statuses':[429,'5xx','network'],
            'new_conditional_answer_max_attempts':5,'new_conditional_answer_402_retries':3,
            'quality_retries':0,'aggregate_benchmark_budget_usd':6.0,
            'lower_run_cost_cap':'Root must pass a nonnegative new-cost-cap in USD and confirm-paid-start. The effective aggregate ceiling is min(6, original known experiment cost + that cap), recorded before any new API call; all21 tasks remain, without selection by difficulty or outcome.',
            'budget_scope':'Original known benchmark cost plus new cost/reservations; unknown new network cost stays conservatively reserved. No account balance or private finance information published.',
            'comparison_policy':'Report strict original-attempt21 results separately from infrastructure-recovered21 results. Recovery is a transport supplement, not a new benchmark or a replacement for original failures.',
            'performance_metrics_seen_for_registration':False,'models_called_by_freeze':0}
    configuration=dict(p);configuration.update({'kind':'Separate infrastructure-only recovery of original fixed21 experiment',
        'frozen_utc':policy['registered_utc'],'generation_workers':policy['workers'],
        'transport_recovery':policy,'retry_policy':{'original_unchanged':p['retry_policy'],'supplement_only':policy['eligibility']},
        'code_pins':dict(p['code_pins'],**{'transport_recovery_additional.py':sha(__file__)})})
    write(supplement/'protocol.json',configuration)
    print(json.dumps({'supplement_frozen':str(supplement),'protocol_sha256':sha(supplement/'protocol.json'),
                      'original_protocol_sha256':policy['original_protocol_sha256'],'n':21,'model_calls':0}),flush=True)


def retry_after(headers):
    value=headers.get('Retry-After') if headers else None
    try:return max(120.0,float(value))
    except (TypeError,ValueError):
        try:return max(120.0,parsedate_to_datetime(value).timestamp()-time.time())
        except (TypeError,ValueError,OverflowError):return 120.0


class RecoveryTransport:
    def __init__(self,original,supplement,api_key,old_cost,budget=6.0):
        self.original=original;self.supplement=supplement;self.key=api_key
        self.old_cost=old_cost;self.budget=budget;self.lock=threading.Lock()
        self.actual_cost=0.0;self.reserved=0.0;self.unknown_cost=0;self.attempts=0
        self.cooldown=0.0;self.request_lock=threading.Lock()

    def await_cooldown(self):
        while True:
            with self.lock:wait=self.cooldown-time.monotonic()
            if wait<=0:return
            time.sleep(min(wait,2))

    def cooldown_for(self,seconds):
        with self.lock:self.cooldown=max(self.cooldown,time.monotonic()+seconds)

    def call_payload(self,request_id,payload,*,original_request=None,new_conditional=False):
        raw=serialized(payload);pin=hashlib.sha256(raw).hexdigest()
        if original_request is not None:
            prior=read(original_request)
            if prior['payload_sha256']!=pin or serialized(prior['payload'])!=raw:
                raise ValueError('Original replay payload bytes changed')
        path=self.supplement/'calls'/request_id
        write(path.with_suffix('.request.json'),{'request_id':request_id,'created_utc':utc(),'payload':payload,'payload_sha256':pin,
             'authorization_header_omitted':True,'original_request':str(original_request) if original_request else None,
             'original_request_sha256':sha(original_request) if original_request else None,
             'identical_original_payload':original_request is not None,'conditional_predeclared_new_D_answer':new_conditional})
        maximum=5 if new_conditional else 4
        allowed_preprovider=4 if new_conditional else 3
        preprovider=0;network_extra=0;attempts=[];cost=0.0;unknown=0;began=time.monotonic();outcome=None
        for attempt in range(maximum):
            if preprovider>=allowed_preprovider:break
            self.await_cooldown();preprovider+=1
            estimate=sum(len(m['content']) for m in payload['messages'])/3*0.000005+payload['max_tokens']*0.000025
            with self.lock:
                if self.old_cost+self.actual_cost+self.reserved+estimate>self.budget:
                    outcome={'ok':False,'error':'aggregate_original_plus_recovery_budget_guard','content':None,'usage':{},'provider':None,'finish_reason':None}
                    break
                self.reserved+=estimate;self.attempts+=1
            response_path=path.with_suffix('.attempt'+str(attempt)+'.response.json')
            status=None;retry_kind=None;value=None;known=None;attempt_started=time.monotonic()
            try:
                request=urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',raw,
                    {'Authorization':'Bearer '+self.key,'Content-Type':'application/json'},method='POST')
                with urllib.request.urlopen(request,timeout=180) as response:
                    status=response.status;value=json.loads(response.read().decode('utf-8'))
                write(response_path,{'request_id':request_id,'attempt':attempt,'http_status':status,'received_utc':utc(),
                                    'elapsed_seconds':time.monotonic()-attempt_started,'response':value})
                usage=value.get('usage') or {};reported=usage.get('cost')
                if isinstance(reported,(int,float)):known=float(reported);cost+=known
                else:unknown+=1
                if value.get('choices'):
                    choice=value['choices'][0];valid=value.get('provider')==payload['provider']['only'][0] and value.get('model')==payload['model']
                    outcome={'ok':valid,'error':None if valid else 'pinned_model_or_provider_mismatch','content':choice.get('message',{}).get('content'),
                             'usage':usage,'provider':value.get('provider'),'model':value.get('model'),'finish_reason':choice.get('finish_reason'),'generation_id':value.get('id')}
                else:outcome={'ok':False,'error':'provider_error','content':None,'usage':usage,'provider':value.get('provider'),'finish_reason':None}
            except urllib.error.HTTPError as exc:
                status=exc.code;body=exc.read().decode('utf-8',errors='replace')
                try:value=json.loads(body)
                except ValueError:value={'non_json_body':body}
                envelope={'request_id':request_id,'attempt':attempt,'http_status':status,'received_utc':utc(),
                          'elapsed_seconds':time.monotonic()-attempt_started,'response':value,'retry_after':exc.headers.get('Retry-After')}
                write(response_path,envelope)
                outcome={'ok':False,'error':'http_'+str(status),'content':None,'usage':{},'provider':None,'finish_reason':None}
                if exact_budget_rejection(envelope) and status==402:retry_kind='exact_preprovider_402';self.cooldown_for(retry_after(exc.headers));known=0.0
                elif exact_budget_rejection(envelope) and status==403:known=0.0
                elif status==429 or 500<=status<600:retry_kind='original_transport_policy';self.cooldown_for(max(2,retry_after(exc.headers)) if exc.headers.get('Retry-After') else 2);known=0.0
                else:known=0.0
            except (OSError,TimeoutError,ValueError) as exc:
                retry_kind='original_transport_policy' if not isinstance(exc,ValueError) else None
                unknown+=1
                write(response_path,{'request_id':request_id,'attempt':attempt,'received_utc':utc(),'elapsed_seconds':time.monotonic()-attempt_started,
                                     'error_type':type(exc).__name__,'error':str(exc).replace(self.key,'[redacted]')})
                outcome={'ok':False,'error':'transport_or_response_error','content':None,'usage':{},'provider':None,'finish_reason':None}
            with self.lock:
                if known is not None:self.reserved-=estimate;self.actual_cost+=known
                else:self.unknown_cost+=1
            attempts.append({'attempt':attempt,'http_status':status,'response_path':str(response_path),'retry_kind':retry_kind,'payload_sha256':pin})
            if retry_kind=='exact_preprovider_402':continue
            if retry_kind=='original_transport_policy' and network_extra<1:
                network_extra+=1;preprovider-=1;self.cooldown_for(2);continue
            break
        if outcome is None:raise RuntimeError('Missing recovery outcome')
        outcome.update(request_path=str(path.with_suffix('.request.json')),response_path=attempts[-1]['response_path'] if attempts else None,
                       elapsed_seconds=time.monotonic()-began,attempts=attempts,known_actual_cost_usd=cost,unknown_cost_attempts=unknown,
                       original_payload_sha256=pin if original_request else None,recovery_is_quality_retry=False)
        write(path.with_suffix('.outcome.json'),outcome)
        with self.lock:
            usage={'known_original_benchmark_cost_usd':self.old_cost,'known_supplement_cost_usd':self.actual_cost,
                   'known_aggregate_cost_usd':self.old_cost+self.actual_cost,'unknown_new_cost_attempts':self.unknown_cost,
                   'reserved_or_unknown_cost_usd':self.reserved,'aggregate_budget_guard_usd':self.budget,'new_HTTP_attempts':self.attempts,
                   'model_output_quality_retry':False}
            usage_path=self.supplement/'usage.json';tmp=usage_path.with_suffix('.tmp')
            tmp.write_text(json.dumps(usage,ensure_ascii=False,indent=2)+'\n');tmp.replace(usage_path)
        return outcome

    def replay(self,request_id):
        if not eligible(self.original,request_id):raise ValueError('Noneligible request replay prohibited')
        prior=self.original/'calls'/(request_id+'.request.json')
        return self.call_payload(request_id,read(prior)['payload'],original_request=prior)

    def conditional_answer(self,request_id,messages,template):
        if (self.original/'calls'/(request_id+'.request.json')).exists():raise ValueError('Conditional answer already existed originally')
        payload=dict(template);payload['messages']=messages;payload['max_tokens']=8192
        return self.call_payload(request_id,payload,new_conditional=True)


class ReplayProxy:
    def __init__(self,transport):self.transport=transport
    def call(self,request_id,messages,max_tokens):
        prior=self.transport.original/'calls'/(request_id+'.request.json')
        payload=read(prior)['payload']
        if payload['messages']!=messages or payload['max_tokens']!=max_tokens:raise ValueError('Structured reconstruction changed original payload')
        return self.transport.replay(request_id)


def answer_result(base,outcome,retrieval):
    result=dict(base);result.update(records=[],calls=list(base.get('calls',[])))
    result['calls'].append(retrieval.call_summary(outcome,'transport_recovered_answer'))
    result['output_truncated']=outcome.get('finish_reason')=='length'
    if outcome.get('finish_reason')=='length':result['status']='output_truncated'
    elif not outcome.get('ok') or outcome.get('finish_reason')!='stop':result.update(status='answer_failed',error=outcome.get('error'))
    else:
        try:
            parsed=retrieval.parse_answer(outcome['content'])
            result.update(records=parsed['records'],abstain=parsed['abstain'],self_reported_complete=parsed['complete'],
                          status='abstained' if parsed['abstain'] else ('ok' if parsed['complete'] else 'partial'))
            result.pop('error',None)
        except (ValueError,TypeError,KeyError) as exc:result.update(status='answer_parse_error',error=str(exc))
    return result


def copy_original_context(original,supplement,arm,identifier):
    source=original/'retrieval'/arm/identifier;target=supplement/'retrieval'/arm/identifier
    if source.exists():shutil.copytree(source,target)
    return target


def recover_retrieval(task,arm,base,transport,retrieval):
    identifier=task['id'];folder=copy_original_context(transport.original,transport.supplement,arm,identifier)
    answer_id=identifier+'_'+arm+'_answer'
    if eligible(transport.original,answer_id):
        result=answer_result(base,transport.replay(answer_id),retrieval)
    elif arm=='D' and eligible(transport.original,identifier+'_D_followup'):
        helper=transport.replay(identifier+'_D_followup')
        result=dict(base);result['calls']=list(base.get('calls',[]))+[retrieval.call_summary(helper,'transport_recovered_followup')]
        if not helper.get('ok') or helper.get('finish_reason')!='stop':
            result.update(status='followup_output_truncated' if helper.get('finish_reason')=='length' else 'followup_failed',error=helper.get('error'))
        else:
            try:
                query=json.loads(helper['content'])
                if not isinstance(query,dict) or set(query)!={'query'} or not isinstance(query['query'],str) or not query['query'].strip():raise ValueError('Followup must be one nonempty query')
            except (ValueError,TypeError,KeyError) as exc:result.update(status='followup_parse_error',error=str(exc))
            else:
                inventory=read(transport.supplement/'retrieval_corpus_inventory.json')
                shard=next(s for s in inventory['shards'] if s['WG']==task['wg']);path=Path(shard['path']);path=path if path.is_absolute() else ROOT/path
                st=path.stat()
                if st.st_size!=shard['bytes'] or st.st_mtime_ns!=shard['mtime_ns']:raise ValueError('Pinned retrieval corpus changed')
                first=read(folder/'retrieval_round_1.json');second=retrieval.retrieve(path,query['query'],retrieval.PROTOCOL['followup_query_max_terms'])
                write(folder/'retrieval_round_2.json',second)
                docs,stats=retrieval.contexts(path,[first,second]);write(folder/'final_context.json',{'documents':docs,'stats':stats})
                messages=[{'role':'system','content':retrieval.ANSWER_INSTRUCTION},
                          {'role':'user','content':retrieval.canonical({'question':task['question_en'],'contract':retrieval.public_contract(task)})+'\nSOURCE PASSAGES:\n'+'\n\n'.join(d['formatted'] for d in docs)}]
                template=read(transport.original/'calls'/(identifier+'_D_followup.request.json'))['payload']
                outcome=transport.conditional_answer(answer_id,messages,template)
                result.update(context_stats=stats,context_docids=[{'collection':d['collection'],'point_id':d['point_id'],'chunk_id':d['chunk_id']} for d in docs],
                              retrieval_statuses=[first['status'],second['status']],retrieval_candidate_truncated=any(r.get('context_candidate_truncated') is True for r in [first,second]),
                              context_truncated=stats['document_selection_truncated'] or any(d['source_text_truncated'] or d['source_header_truncated'] for d in docs),
                              conditional_D_continuation=True,original_initial_retrieval_reused=True)
                result=answer_result(result,outcome,retrieval)
    else:result=dict(base)
    # The copied old result remains as original_result.json; a new result is a
    # separate infrastructure outcome, not a rewritten original failure.
    old_result=folder/'result.json'
    if old_result.exists():old_result.rename(folder/'original_result.json')
    write(folder/'result.json',result)
    return result


def run(original,supplement,bundle,new_cost_cap,confirm_paid_start):
    if not confirm_paid_start:raise ValueError('Root paid-start confirmation flag required; model calls are currently held')
    if new_cost_cap<0:raise ValueError('New experiment cost cap must be nonnegative')
    original=original.resolve();supplement=supplement.resolve();bundle=bundle.resolve()
    p=read(supplement/'protocol.json');policy=p['transport_recovery']
    if sha(original/'protocol.json')!=policy['original_protocol_sha256'] or sha(__file__)!=policy['recovery_implementation_sha256']:raise ValueError('Registered supplement changed')
    for name,pin in p['code_pins'].items():
        if sha(BASE/name)!=pin:raise ValueError('Frozen runtime changed')
    for name,pin in p['schema_pins'].items():
        if sha(supplement/name)!=pin:raise ValueError('Frozen schema changed')
    for folder,name,key in [(supplement,'public_tasks.jsonl','public_tasks_sha256'),
                            (supplement,'retrieval_corpus_inventory.json','retrieval_inventory_sha256'),
                            (bundle,'manifest.json','bundle_manifest_sha256'),(bundle,'tasks.jsonl','tasks_sha256'),
                            (bundle,'reference_gold.jsonl','gold_sha256')]:
        if sha(folder/name)!=p[key]:raise ValueError('Frozen source/cohort input changed: '+name)
    completion=read(original/'generation_complete.json')
    if completion['completed_method_items']!=21*4 or completion['required']!=21*4:raise ValueError('Original attempt run not complete')
    if (supplement/'recovery_started.json').exists():raise ValueError('Recovery already started; uncontrolled resume forbidden')
    tasks=[json.loads(s) for s in (supplement/'public_tasks.jsonl').read_text().splitlines() if s.strip()]
    if [t['id'] for t in tasks]!=p['cohort_ids']:raise ValueError('21 task identity changed')
    snapshot={str(path.relative_to(original)):sha(path) for parent in ['calls','arm_outputs','retrieval'] for path in (original/parent).rglob('*.json')}
    write(supplement/'original_artifact_inventory.json',{'original_protocol_sha256':policy['original_protocol_sha256'],'files':snapshot,'original_generation_complete_sha256':sha(original/'generation_complete.json')})
    old=read(original/'usage.json');old_cost=float(old['known_actual_cost_usd'])
    sys.path.insert(0,str(ROOT/'scripts/common/common'));import credentials
    effective_budget=min(float(policy['aggregate_benchmark_budget_usd']),old_cost+float(new_cost_cap))
    transport=RecoveryTransport(original,supplement,credentials.secret('OPENROUTER_API_KEY'),old_cost,effective_budget)
    import structured_adapter as structured
    import retrieval_adapter as retrieval
    write(supplement/'recovery_started.json',{'started_utc':utc(),'protocol_sha256':sha(supplement/'protocol.json'),'registered_before_API':True,
        'original_known_cost_usd':old_cost,'original_unknown_cost_attempts':old.get('unknown_cost_attempts',0),
        'root_new_cost_cap_usd':new_cost_cap,'effective_aggregate_known_plus_reserved_cost_cap_usd':effective_budget,
        'original_artifact_inventory_sha256':sha(supplement/'original_artifact_inventory.json')})
    def ordinary_job(task,arm):
        prior=original/'arm_outputs'/ARMS[arm]/(task['id']+'.json');base=read(prior)
        if arm in {'A','B'}:
            stage='Text2Cypher' if arm=='A' else 'Text2SQL';request_id=task['id']+'_'+stage
            if eligible(original,request_id):
                public=dict(task);kind='graph' if arm=='A' else 'sql';public[kind+'_schema']=read(supplement/'schemas'/(task['wg']+'_'+kind+'.json'))
                result=structured.evaluate(public,arm,ReplayProxy(transport),supplement)
                mode='identical_preprovider_replay'
            else:result=dict(base);mode='cached_original_outcome_no_model_call'
        else:
            had=eligible(original,task['id']+'_'+arm+'_answer') or arm=='D' and eligible(original,task['id']+'_D_followup')
            result=recover_retrieval(task,arm,base,transport,retrieval);mode='predeclared_transport_recovery' if had else 'cached_original_outcome_no_model_call'
        result['transport_provenance']={'original_arm_output':str(prior),'original_arm_output_sha256':sha(prior),
                                       'original_failure_preserved':True,'mode':mode,'quality_retry':False}
        write(supplement/'arm_outputs'/ARMS[arm]/(task['id']+'.json'),result)
        return {'id':task['id'],'arm':arm,'mode':mode,'status':result['status']}
    def job(task,arm):
        try:return ordinary_job(task,arm)
        except Exception as exc:
            path=supplement/'arm_outputs'/ARMS[arm]/(task['id']+'.json')
            if path.exists():raise
            result={'id':task['id'],'repair_sha256':task['repair_sha256'],'records':[],
                    'status':'RECOVERY_EXCEPTION','error_type':type(exc).__name__,
                    'error':str(exc).replace(transport.key,'[redacted]')[:1000],
                    'transport_provenance':{'original_failure_preserved':True,'quality_retry':False,'mode':'explicit_recovery_failure'}}
            write(path,result)
            return {'id':task['id'],'arm':arm,'mode':'explicit_recovery_failure','status':'RECOVERY_EXCEPTION'}
    results=[]
    with ThreadPoolExecutor(max_workers=policy['workers']) as executor:
        futures=[executor.submit(job,t,a) for t in tasks for a in ARMS]
        for future in as_completed(futures):
            results.append(future.result())
            if len(results)%40==0:print(json.dumps({'supplement_completed_method_items':len(results),'required':84}),flush=True)
    changed=[name for name,pin in snapshot.items() if sha(original/name)!=pin]
    if changed:raise ValueError('Original artifacts changed during separate recovery')
    write(supplement/'generation_complete.json',{'completed_method_items':len(results),'required':84,'original_artifacts_unchanged':True,
        'modes':{mode:sum(r['mode']==mode for r in results) for mode in sorted({r['mode'] for r in results})},'items':results})
    print(json.dumps({'recovery_complete':84,'original_artifacts_unchanged':True,'protocol_sha256':sha(supplement/'protocol.json')}),flush=True)


def estimate(original,output):
    """Retained usage and nonauthoritative future-cost estimates; no API call."""
    original=original.resolve();samples={};rows=[]
    for path in (original/'calls').glob('*.request.json'):
        request=read(path);request_id=request['request_id'];payload=request['payload']
        stage=next((s for s in ['Text2Cypher','Text2SQL','C_answer','D_followup','D_answer'] if request_id.endswith('_'+s)),None)
        wg=request_id.split('_')[0];chars=sum(len(m['content']) for m in payload['messages'])
        outcome_path=original/'calls'/(request_id+'.outcome.json')
        if not outcome_path.exists():continue
        outcome=read(outcome_path);usage=outcome.get('usage') or {}
        if outcome.get('ok') and isinstance(usage.get('prompt_tokens'),(int,float)):
            samples.setdefault((wg,stage),[]).append((usage['prompt_tokens']/max(1,chars),usage.get('completion_tokens',0)))
        if eligible(original,request_id):
            last=read(Path(outcome['attempts'][-1]['response_path']))
            rows.append({'request_id':request_id,'wg':wg,'stage':stage,'original_http_status':last['http_status'],
                         'exact_limit_source':last['response']['error']['metadata']['limit_source'],
                         'request_file_sha256':sha(path),'payload_sha256':request['payload_sha256'],
                         'prompt_characters':chars,'maximum_output_tokens':payload['max_tokens'],
                         'max_output_cost_usd_at_frozen_price':payload['max_tokens']*.000025,
                         'input_cost_chars_div3_estimate_usd':chars/3*.000005})
    for row in rows:
        sample=samples.get((row['wg'],row['stage'])) or [pair for (wg,stage),pairs in samples.items() if stage==row['stage'] for pair in pairs]
        row['observed_reference_sample_n']=len(sample)
        if sample:
            ratio=statistics.median(x[0] for x in sample);completion=statistics.median(x[1] for x in sample)
            row['observed_stage_median_input_estimate_usd']=row['prompt_characters']*ratio*.000005
            row['observed_stage_median_output_estimate_usd']=completion*.000025
    missing_D=[]
    for row in rows:
        if row['stage']=='D_followup':
            answer_id=row['request_id'].removesuffix('_D_followup')+'_D_answer'
            if not (original/'calls'/(answer_id+'.request.json')).exists():missing_D.append(answer_id)
    bystage={s:{'eligible_requests':sum(r['stage']==s for r in rows),
                'maximum_output_cost_usd':sum(r['max_output_cost_usd_at_frozen_price'] for r in rows if r['stage']==s),
                'median_usage_future_cost_estimate_usd':sum(r.get('observed_stage_median_input_estimate_usd',r['input_cost_chars_div3_estimate_usd'])+r.get('observed_stage_median_output_estimate_usd',r['max_output_cost_usd_at_frozen_price']) for r in rows if r['stage']==s)}
             for s in ['Text2Cypher','Text2SQL','C_answer','D_followup','D_answer']}
    result={'kind':'Offline remaining transport-recovery call inventory and nonauthoritative estimates',
            'created_utc':utc(),'original_protocol_sha256':sha(original/'protocol.json'),'original_known_usage':read(original/'usage.json'),
            'eligible_existing_stage_n':len(rows),'stages':bystage,'missing_conditional_D_answer_n':len(missing_D),
            'missing_conditional_D_answer_ids':missing_D,'maximum_conditional_D_answer_output_cost_usd':len(missing_D)*8192*.000025,
            'existing_stage_max_output_cost_usd':sum(r['max_output_cost_usd_at_frozen_price'] for r in rows),
            'all_existing_stage_median_usage_future_cost_estimate_usd':sum(v['median_usage_future_cost_estimate_usd'] for v in bystage.values()),
            'known_frozen_price_usd_per_token':{'input':.000005,'output':.000025},'new_model_calls':0,
            'limits':['Future output tokens/cost are unknown. Median usage estimates and chars/3 are not exact costs or a tokenizer.',
                      'Conditional D answer prompts/context do not yet exist, so their input cost is unestimated.',
                      'Retries, timeout cost, other account activity and account/key financing are separate. Preserve original unknown-cost attempts.',
                      'Model max-output cost is an upper component bound per completed request, not a promised final cost.'],
            'items':rows}
    write(output,result)
    print(json.dumps({k:result[k] for k in ['eligible_existing_stage_n','stages','missing_conditional_D_answer_n','all_existing_stage_median_usage_future_cost_estimate_usd','existing_stage_max_output_cost_usd']}),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('action',choices=['freeze','run','estimate'])
    a.add_argument('--original',type=Path,default=DEFAULT_ORIGINAL);a.add_argument('--supplement',type=Path,default=DEFAULT_SUPPLEMENT);a.add_argument('--bundle',type=Path,default=DEFAULT_BUNDLE)
    a.add_argument('--confirm-paid-start',action='store_true');a.add_argument('--new-cost-cap',type=float)
    a.add_argument('--output',type=Path,default=BASE/'audit/transport_recovery_cost_estimate.json')
    args=a.parse_args()
    if args.action=='run':
        if args.new_cost_cap is None:a.error('--new-cost-cap is required before paid run')
        run(args.original,args.supplement,args.bundle,args.new_cost_cap,args.confirm_paid_start)
    elif args.action=='estimate':estimate(args.original,args.output)
    else:freeze(args.original,args.supplement,args.bundle)
