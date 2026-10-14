#!/usr/bin/env python3
"""Offline audit of already completed exact-payload transport recovery.

No key/account/API access; no gold, reference queries, scores or quality-based
selection. Packaged original and supplemental runs can be replayed side by side.
"""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

ARMS={'A':'text2cypher','B':'text2sql','C':'single_retrieval','D':'iterative_retrieval'}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text())


def serial(payload):return json.dumps(payload,ensure_ascii=False).encode()


def original_eligible(original,request_id):
    request=original/'calls'/(request_id+'.request.json');outcome=original/'calls'/(request_id+'.outcome.json')
    if not request.exists() or not outcome.exists():return False
    o=read(outcome);attempts=o.get('attempts',[])
    if o.get('ok') or not attempts:return False
    raw=[read(original/'calls'/Path(a['response_path']).name) for a in attempts]
    if any((r.get('response') or {}).get('choices') for r in raw):return False
    last=raw[-1];error=(last.get('response') or {}).get('error') or {};meta=error.get('metadata') or {}
    code=last.get('http_status')
    return error.get('code')==code and ((code==402 and meta.get('limit_source')=='openrouter_in_flight_budget')
                                  or (code==403 and meta.get('limit_source')=='openrouter_key_limit'))


def payload_identity(original_request,new_request):
    old=read(original_request);new=read(new_request)
    raw=serial(new['payload']);h=hashlib.sha256(raw).hexdigest()
    return {'same_payload_bytes':raw==serial(old['payload']),
            'new_recorded_payload_pin_matches':new['payload_sha256']==h,
            'original_recorded_payload_pin_matches':old['payload_sha256']==h,
            'original_request_file_pin_matches':new.get('original_request_sha256')==sha(original_request),
            'same_request_id':old['request_id']==new['request_id']}


def validate(original,supplement,output,expected_n=350):
    original=original.resolve();supplement=supplement.resolve()
    op=read(original/'protocol.json');sp=read(supplement/'protocol.json');policy=sp['transport_recovery']
    complete=read(supplement/'generation_complete.json')
    if expected_n not in {350,21}:raise ValueError('Explicitly select the preregistered350 or separate21 cohort')
    if complete['required']!=expected_n*4 or complete['completed_method_items']!=expected_n*4:raise ValueError('Only audit a completed fixed cohort supplement')
    if op['admitted_n']!=expected_n or sp['cohort_ids']!=op['cohort_ids'] or policy['original_protocol_sha256']!=sha(original/'protocol.json'):
        raise ValueError('Fixed original cohort linkage differs')
    errors=[];request_records=[];modes=Counter();statuses={a:Counter() for a in ARMS}
    inventory=read(supplement/'original_artifact_inventory.json')
    changed=[name for name,pin in inventory['files'].items() if sha(original/name)!=pin]
    if changed:errors.append({'original_artifacts_changed':changed})
    for path in sorted((supplement/'calls').glob('*.request.json')):
        req=read(path);rid=req['request_id'];checks={};kind='unsupported'
        if req.get('identical_original_payload'):
            kind='exact_preprovider_replay';old=original/'calls'/path.name
            checks=payload_identity(old,path)
            checks['original_recovery_eligible']=original_eligible(original,rid)
            checks['original_request_basename_matches']=Path(req.get('original_request','')).name==path.name
        elif req.get('conditional_predeclared_new_D_answer'):
            kind='first_conditional_D_answer';identifier=rid.removesuffix('_D_answer')
            checks={'D_answer_stage':rid.endswith('_D_answer'),
                    'no_original_D_answer_request':not (original/'calls'/path.name).exists(),
                    'original_D_followup_eligible':original_eligible(original,identifier+'_D_followup'),
                    'payload_pin_matches':hashlib.sha256(serial(req['payload'])).hexdigest()==req['payload_sha256'],
                    'round1_byte_identical':sha(original/'retrieval/D'/identifier/'retrieval_round_1.json')==sha(supplement/'retrieval/D'/identifier/'retrieval_round_1.json'),
                    'initial_context_byte_identical':sha(original/'retrieval/D'/identifier/'initial_context.json')==sha(supplement/'retrieval/D'/identifier/'initial_context.json')}
        else:checks={'registered_request_kind':False}
        payload=req['payload'];checks['pinned_model']=payload.get('model')==op['model']
        checks['pinned_provider_only']=payload.get('provider',{}).get('only')==[op['provider']]
        checks['provider_fallbacks_disabled']=payload.get('provider',{}).get('allow_fallbacks') is False
        checks['key_not_logged']=req.get('authorization_header_omitted') is True and 'Authorization' not in req
        outcome=read(supplement/'calls'/(rid+'.outcome.json'));attempts=outcome.get('attempts',[])
        checks['no_quality_retry_outcome_flag']=outcome.get('recovery_is_quality_retry') is False
        checks['attempt_count_within_registered_cap']=len(attempts)<=(5 if kind=='first_conditional_D_answer' else 4)
        checks['every_attempt_payload_pin_matches']=all(a.get('payload_sha256')==req['payload_sha256'] for a in attempts)
        raw=[read(supplement/'calls'/Path(a['response_path']).name) for a in attempts]
        checks['no_retry_after_provider_choices']=not any((r.get('response') or {}).get('choices') for r in raw[:-1])
        checks['no_retry_after_real403_key_rejection']=not any(r.get('http_status')==403 for r in raw[:-1])
        modes[kind]+=1
        record={'request_id':rid,'request_sha256':sha(path),'kind':kind,'checks':checks,
                'status':'PASS' if all(checks.values()) else 'FAIL','new_HTTP_attempts':len(attempts),
                'outcome_ok':outcome.get('ok'),'outcome_error':outcome.get('error')}
        request_records.append(record)
        if record['status']=='FAIL':errors.append({'request_id':rid,'failed_checks':[k for k,v in checks.items() if not v]})
    cache_records=[]
    for identifier in op['cohort_ids']:
        for arm,name in ARMS.items():
            prior=original/'arm_outputs'/name/(identifier+'.json');current=supplement/'arm_outputs'/name/(identifier+'.json')
            old=read(prior);new=read(current);provenance=new.get('transport_provenance',{})
            checks={'id_preserved':old['id']==new['id']==identifier,'repair_sha_preserved':old['repair_sha256']==new['repair_sha256'],
                    'quality_retry_prohibited':provenance.get('quality_retry') is False,
                    'original_failure_preserved':provenance.get('original_failure_preserved') is True}
            mode=provenance.get('mode');statuses[arm][new['status']]+=1
            if mode=='cached_original_outcome_no_model_call':
                checks['cached_outcome_exact']=old=={k:v for k,v in new.items() if k!='transport_provenance'}
                checks['cached_original_file_pin']=provenance.get('original_arm_output_sha256')==sha(prior)
                stages=['Text2Cypher'] if arm=='A' else ['Text2SQL'] if arm=='B' else [arm+'_answer'] if arm=='C' else ['D_followup','D_answer']
                checks['no_new_cached_request']=not any((supplement/'calls'/(identifier+'_'+stage+'.request.json')).exists() for stage in stages)
            modekey='arm_'+str(mode);modes[modekey]+=1
            if not all(checks.values()):errors.append({'id':identifier,'arm':arm,'failed_checks':[k for k,v in checks.items() if not v]})
            cache_records.append({'id':identifier,'arm':arm,'mode':mode,'checks':checks,'status':'PASS' if all(checks.values()) else 'FAIL'})
    usage=read(supplement/'usage.json');start=read(supplement/'recovery_started.json')
    cost_check=usage['known_supplement_cost_usd']<=start['root_new_cost_cap_usd']+1e-8
    if not cost_check:errors.append({'new_known_cost_exceeds_registered_root_cap':True})
    report={'kind':'Completed fixed'+str(expected_n)+' transport supplement offline integrity audit','snapshot_utc':datetime.now(timezone.utc).isoformat(),
        'tool_sha256':sha(__file__),'original_protocol_sha256':sha(original/'protocol.json'),'supplement_protocol_sha256':sha(supplement/'protocol.json'),
        'task_denominator_per_arm':expected_n,'arm_record_denominator':expected_n*4,'original_artifact_inventory_files':len(inventory['files']),
        'original_artifacts_unchanged':not changed,'new_request_count':len(request_records),'modes':dict(modes),
        'recovered_outcome_statuses':{a:dict(c) for a,c in statuses.items()},'new_known_cost_within_registered_cap':cost_check,
        'known_supplement_benchmark_cost_usd':usage['known_supplement_cost_usd'],
        'unknown_new_cost_attempts':usage['unknown_new_cost_attempts'],'request_check_failures':sum(r['status']=='FAIL' for r in request_records),
        'arm_check_failures':sum(r['status']=='FAIL' for r in cache_records),'status':'PASS' if not errors else 'FAIL','errors':errors,
        'models_or_account_calls_by_this_tool':0,'original_metrics_replaced':False,
        'limits':['Integrity checks do not establish answer correctness or score improvement.',
                  'Original failed attempts remain separate; output parsing or execution failures are not retried for quality.',
                  'Known experimental usage is distinct from account finances. Unknown provider cost remains unknown.',
                  'Exact prompt reconstruction and information-access diagnostics are recorded separately.'],
        'requests':request_records,'arm_records':cache_records}
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['task_denominator_per_arm','new_request_count','status','request_check_failures','arm_check_failures','known_supplement_benchmark_cost_usd']}))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--original',type=Path,required=True);a.add_argument('--supplement',type=Path,required=True);a.add_argument('--output',type=Path,required=True)
    a.add_argument('--expected-n',type=int,choices=[350,21],default=350)
    args=a.parse_args();validate(args.original,args.supplement,args.output,args.expected_n)
