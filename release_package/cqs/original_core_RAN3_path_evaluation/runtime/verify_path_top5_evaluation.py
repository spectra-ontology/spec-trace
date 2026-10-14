#!/usr/bin/env python3
"""Offline replay of one source-invariant original question and all four fresh methods."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys

sys.dont_write_bytecode=True


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text())
def rows(path):return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def verify(evidence,bundle,parent):
    manifest=load(evidence/'manifest.json')
    actual={p.relative_to(evidence).as_posix():sha(p) for p in evidence.rglob('*') if p.is_file() and p!=evidence/'manifest.json'}
    if actual!=manifest['files']:raise ValueError('Evidence membership or SHA differs')
    for name in actual:
        path=PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or '\\' in name or (evidence/name).is_symlink():
            raise ValueError('Unsafe evidence member')
    if sha(bundle/'manifest.json')!=manifest['bundle_manifest_sha256'] or sha(parent/'manifest.json')!=manifest['parent_manifest_sha256']:
        raise ValueError('Contract or parent differs')
    sys.path.insert(0,str(bundle))
    import verify_path_top5_bundle
    proof=verify_path_top5_bundle.verify(bundle,parent)
    if proof['additional_admitted_n']!=1:raise ValueError('Incomplete one-item phase')
    tasks={t['id']:t for t in rows(bundle/'tasks.jsonl')}
    current=evidence/'current'
    combined=load(current/'protocol.json')
    if (combined['bundle_manifest_sha256']!=sha(bundle/'manifest.json')
            or combined['tasks_sha256']!=sha(bundle/'tasks.jsonl')
            or combined['gold_sha256']!=sha(bundle/'reference_gold.jsonl')
            or combined['public_tasks_sha256']!=sha(current/'public_tasks.jsonl')):
        raise ValueError('Frozen cohort/task/gold pins differ')
    for name,expected in combined['code_pins'].items():
        if sha(evidence/'runtime'/name)!=expected:raise ValueError('Pinned runtime differs: '+name)
    for name,expected in combined['schema_pins'].items():
        if sha(current/name)!=expected:raise ValueError('Pinned schema differs')
    for wg,item in combined['sql_manifests'].items():
        if sha(evidence/'source_manifests'/(wg+'.manifest.json'))!=item['sha256']:
            raise ValueError('SQL source manifest differs')
    scope=combined['one_item_scope']
    if (sha(current/'runtime_freeze_base.json')!=scope['raw_runtime_freeze_sha256']
            or sha(current/'schema_preflight.json')!=combined['schema_preflight_sha256']
            or scope['method_items']!=4 or not scope['all_methods_fixed_before_prediction']
            or combined['generation_workers']!=1 or combined['budget_guard_usd']!=2.0):
        raise ValueError('Pre-call registration differs')
    received=0;http_counts=Counter();actual_cost=0.0
    for phase in [current]:
        for path in (phase/'calls').glob('*.request.json'):
            request=load(path);payload=request['payload']
            if (request['authorization_header_omitted'] is not True
                    or hashlib.sha256(json.dumps(payload,ensure_ascii=False).encode()).hexdigest()!=request['payload_sha256']
                    or payload['model']!='anthropic/claude-opus-4.8'
                    or payload['provider']!={'only':['Anthropic'],'allow_fallbacks':False,'require_parameters':True}
                    or payload['reasoning']!={'enabled':False}
                    or payload['response_format']!={'type':'json_object'}):
                raise ValueError('Request model/provider/payload differs')
        for path in (phase/'calls').glob('*.response.json'):
            response=load(path);http_counts[response.get('http_status')]+=1
            raw=response.get('response',{})
            if response.get('http_status')==200 and raw.get('choices'):
                if raw.get('provider')!='Anthropic' or raw.get('model')!='anthropic/claude-opus-4.8':raise ValueError('Provider/model fallback')
                received+=1
                cost=raw.get('usage',{}).get('cost')
                if type(cost) not in [int,float]:raise ValueError('Successful response cost unavailable')
                actual_cost+=cost
    if received!=5 or http_counts!={200:5}:raise ValueError('Actual full generation coverage differs')
    usage=load(current/'usage.json')
    if abs(usage['known_actual_cost_usd']-actual_cost)>1e-10 or usage['unknown_cost_attempts']!=0:
        raise ValueError('Reported cost differs from raw usage')
    methods={'A':'text2cypher','B':'text2sql','C':'single_retrieval','D':'iterative_retrieval'}
    public={t['id']:t for t in rows(current/'public_tasks.jsonl')}
    if set(public)!=set(tasks):raise ValueError('Public task cohort differs')
    for identifier,task in tasks.items():
        exposed=public[identifier]
        allowed={'id','wg','repair_sha256','question_en','required_fields','collection','cardinality_policy','identity_format'}
        if set(exposed)-allowed or exposed['question_en']!=task['question_en'] or exposed['repair_sha256']!=task['repair_sha256']:
            raise ValueError('Generator has altered questions or private evidence')
    for wg in {identifier.split('_')[0] for identifier in tasks}:
        guard=load(current/'source_guards'/(wg+'.json'))
        sql_manifest=load(evidence/'source_manifests'/(wg+'.manifest.json'))
        expected_sql=sql_manifest.get('sqlite_sha256',sql_manifest.get('db_sha256',sql_manifest.get('output_sha256')))
        if guard['before']!=guard['after'] or guard['before']!=combined['graph_sources'][wg] or guard['sql_sha256']!=expected_sql:
            raise ValueError('Source guards differ')
    sys.path.insert(0,str(evidence/'runtime'))
    import analyze_predictions as analyze
    import score_predictions
    analysis=load(current/'analysis.json');all_results={};tables={}
    for arm,method in methods.items():
        predictions=rows(current/method/'predictions.jsonl');statuses=rows(current/method/'statuses.jsonl')
        if (len(predictions)!=1 or len(statuses)!=1 or {p['id'] for p in predictions}!=set(tasks) or {p['id'] for p in statuses}!=set(tasks)):
            raise ValueError('Incomplete prediction/status denominator')
        status_index={s['id']:s for s in statuses}
        for prediction in predictions:
            identifier=prediction['id'];status=status_index[identifier]
            artifact=load(current/status['artifact'])
            if (prediction['repair_sha256']!=tasks[identifier]['repair_sha256'] or status['repair_sha256']!=prediction['repair_sha256']
                    or prediction['records']!=artifact['records'] or status['status']!=artifact['status'].upper()):
                raise ValueError('Prediction/status projection differs from actual output')
            if arm in ['A','B']:
                generated=load(current/'arm_outputs'/method/(identifier+'.json'))
                if artifact.get('generated_query')!=generated.get('generated_query'):
                    raise ValueError('Executed query differs from actual model query')
        raw=score_predictions.run(bundle/'tasks.jsonl',bundle/'reference_gold.jsonl',current/method/'predictions.jsonl')
        if raw!=load(current/method/'raw_scores.json'):raise ValueError('Raw strict score does not replay')
        gated={row['id']:analyze.gated(row,status_index[row['id']]['status']) for row in raw['outcomes']}
        if list(gated.values())!=load(current/method/'failure_gated_scores.json'):raise ValueError('Failure gate does not replay')
        tables[method]=analyze.summary(list(gated.values()));all_results[method]=gated
        if tables[method]!=analysis['tables'][method]['overall']:raise ValueError('Reported metrics differ')
    pairs=[]
    method_names=list(methods.values())
    for index,a in enumerate(method_names):
        for b in method_names[index+1:]:
            for metric in ['f1','exact']:
                pairs.append(dict(a=a,b=b,**analyze.paired(all_results[a],all_results[b],metric)))
    if analysis['paired']!=pairs or analysis['admitted_n']!=1:raise ValueError('Paired analysis or phase scope differs')
    return {'status':'PASS','additional_n':1,'new_original_core_ids':1,'method_items':4,
            'received_model_response_calls':received,'http_status_counts':dict(http_counts),
            'quality_retries':0,
            'known_actual_cost_usd':actual_cost,'unknown_cost_attempts':0,
            'tables':tables,'strict_scoring_and_failure_gates_replayed':True,
            'original_contracts_predictions_preserved':True,'human_expert_validation_n':0,
            'evidence_manifest_sha256':sha(evidence/'manifest.json'),
            'contract_verification':proof,'new_api_calls':0,'new_query_executions':0,
            'limits':'Stored raw execution/source guards and strict scorer replay; no live data replay or independent human/raw-source validation. Archive-text cutoff equivalence remains unverified.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['evidence','bundle','parent']:parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--out',type=Path)
    args=parser.parse_args();report=verify(args.evidence.resolve(),args.bundle.resolve(),args.parent.resolve())
    if args.out:
        if args.out.resolve().is_relative_to(args.evidence.resolve()):raise ValueError('Report must be outside frozen evidence')
        args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
