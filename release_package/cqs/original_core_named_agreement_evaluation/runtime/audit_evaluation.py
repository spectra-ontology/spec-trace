#!/usr/bin/env python3
"""Check actual serialized model inputs and name the source identity limitation."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(bundle,run):
    task=json.loads((bundle/'tasks.jsonl').read_text())
    public=json.loads((run/'public_tasks.jsonl').read_text())
    protocol=json.loads((run/'protocol.json').read_text())
    expected_fields=[{k:v for k,v in f.items() if k in {'name','type','nullable','json_schema','nested_array_semantics'}}
                     for f in task['required_fields']]
    assert public['question_en']==task['question_en'] and public['required_fields']==expected_fields
    forbidden={'reference_query','original_query','reference_evidence','primary_review','secondary_review',
               'source_context','gold','repair_reason','records'}
    assert not forbidden.intersection(public)
    request_checks=[]
    for path in sorted((run/'calls').glob('*.request.json')):
        item=json.loads(path.read_text());payload=item['payload']
        assert payload['model']==protocol['model'] and payload['provider']['only']==[protocol['provider']]
        assert payload['provider']['allow_fallbacks'] is False and item['authorization_header_omitted'] is True
        assert hashlib.sha256(json.dumps(payload,ensure_ascii=False).encode()).hexdigest()==item['payload_sha256']
        assert task['reference_query'] not in json.dumps(payload,ensure_ascii=False)
        user=payload['messages'][1]['content'];head=user.split('\nSOURCE PASSAGES:\n',1)[0]
        header=json.loads(head)
        assert set(header) <= {'output_format','contract','question','schema'} and header['question']==task['question_en']
        assert not forbidden.intersection(header)
        form=header.get('output_format',header.get('contract'))
        assert form['required_fields']==expected_fields
        assert not forbidden.intersection(form)
        request_checks.append({'file':str(path.relative_to(run)),'sha256':sha(path),
                               'payload_sha256':item['payload_sha256'],'status':'PASS',
                               'source_passages_present':'\nSOURCE PASSAGES:\n' in user})
    assert len(request_checks)==5
    model_outputs=[]
    for method in ['text2cypher','text2sql','single_retrieval','iterative_retrieval']:
        prediction=json.loads((run/method/'predictions.jsonl').read_text())
        status=json.loads((run/method/'statuses.jsonl').read_text())
        assert prediction['repair_sha256']==status['repair_sha256']==task['repair_sha256']
        model_outputs.append({'method':method,'status':status['status'],'records':prediction['records']})
    canonical='AGR-100-6.1-001'
    source_chunk='AGR-100-e-6.1-001#0'
    literal=task['source_context']['actual_original_decision']['literal_paragraphs'][2]['literal_text']
    access=[]
    for arm in ['C','D']:
        request_path=run/'calls'/('RAN1_P2_CQ2-2_'+arm+'_answer.request.json')
        user=json.loads(request_path.read_text())['payload']['messages'][1]['content']
        passages=user.split('\nSOURCE PASSAGES:\n',1)[1]
        access.append({'method':arm,'actual_answer_prompt_sha256':sha(request_path),
                       'explicit_named_draft_decision_present':literal in passages,
                       'canonical_graph_business_id_present':canonical in passages,
                       'source_alias_chunk_id_present':source_chunk in passages,
                       'whole_population_completeness_established':False})
    usage=json.loads((run/'usage.json').read_text())
    assert usage['known_actual_cost_usd']<=2 and usage['unknown_cost_attempts']==0
    guard=json.loads((run/'source_guards/RAN1.json').read_text())
    assert guard['unchanged'] and guard['before']==guard['after']==protocol['graph_sources']['RAN1']
    return {'status':'PASS','id':task['id'],'repair_sha256':task['repair_sha256'],
            'bundle_manifest_sha256':sha(bundle/'manifest.json'),'protocol_sha256':sha(run/'protocol.json'),
            'request_n':len(request_checks),'requests':request_checks,
            'full_denominator_method_items':4,'actual_outputs':model_outputs,
            'actual_text_context_access':access,'known_actual_cost_usd':usage['known_actual_cost_usd'],
            'unknown_cost_attempts':usage['unknown_cost_attempts'],'source_guards_unchanged':True,
            'quality_regeneration_n':0,'expert_validation_n':0,
            'interpretation':'Text methods retrieved the explicit named-draft agreement, but expose a source chunk identifier that differs from the pinned graph business identifier. Their strict ID scores must not be described as a failure to retrieve the decision or as a causal graph advantage. No post-output alias normalization, scorer changes, or response regeneration was performed.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    report=audit(args.bundle.resolve(),args.run.resolve())
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'request_n':report['request_n'],
                      'actual_method_items':4,'known_actual_cost_usd':report['known_actual_cost_usd']}))
