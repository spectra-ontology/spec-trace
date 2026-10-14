#!/usr/bin/env python3
"""Replay all retained additional model predictions offline, with full denominators."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(evidence, bundle, parent):
    sys.dont_write_bytecode = True
    manifest = json.loads((evidence/'evidence_manifest.json').read_text())
    actual = {str(p.relative_to(evidence)):sha(p) for p in evidence.rglob('*')
              if p.is_file() and p.name != 'evidence_manifest.json' and '__pycache__' not in p.parts}
    if actual != manifest['files']:
        raise ValueError('Additional evaluation membership or hashes differ')
    if sha(bundle/'manifest.json') != manifest['bundle_manifest_sha256']:
        raise ValueError('Additional repair contract differs')
    if sha(parent/'manifest.json') != manifest['parent_bundle_manifest_sha256']:
        raise ValueError('Preserved 371 cohort differs')
    repair = subprocess.run([sys.executable,'-B','-S',str(bundle/'verify_additions.py'),
                             '--bundle',str(bundle),'--parent',str(parent)],
                            text=True,capture_output=True,check=True)
    repair_proof = json.loads(repair.stdout)
    module_spec = importlib.util.spec_from_file_location('retained_phase_checks', evidence/'runtime/phase_checks.py')
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    n = repair_proof['additional_admitted_n']
    module.PHASES['additional_repairs'] = (n, None)
    phase_proof, tasks = module.replay_phase('additional_repairs', evidence/'run', bundle, bundle,
                                           archived_run=evidence/'run')
    protocol = json.loads((evidence/'run/protocol.json').read_text())
    if protocol['bundle_manifest_sha256'] != sha(bundle/'manifest.json'):
        raise ValueError('Frozen evaluation registration differs')
    for name, expected in protocol['code_pins'].items():
        if sha(evidence/'runtime'/name) != expected:
            raise ValueError('Actual frozen runtime differs: '+name)
    for name, expected in protocol['schema_pins'].items():
        if sha(evidence/'run'/name) != expected:
            raise ValueError('Actual frozen value-free schema differs')
    public_tasks = module.rows(evidence/'run/public_tasks.jsonl')
    if set(public_tasks) != set(tasks) or sha(evidence/'run/public_tasks.jsonl') != protocol['public_tasks_sha256']:
        raise ValueError('Model-visible original task scope differs')
    forbidden = {'reference_query','original_query','records','primary_review','secondary_review','reference_evidence'}
    for identifier, public in public_tasks.items():
        if forbidden & set(public) or public['question_en'] != tasks[identifier]['question_en']:
            raise ValueError('Private evaluation material in public model task')
        expected_fields=[{k:v for k,v in field.items() if k in
                         {'name','type','nullable','json_schema','nested_array_semantics'}}
                         for field in tasks[identifier]['required_fields']]
        if public['required_fields'] != expected_fields:
            raise ValueError('Model-visible requested fields differ')
    common = protocol.get('common_source_interface')
    common_data = None
    common_request_n = 0
    if common:
        if common['every_call_including_followup'] is not True or common['methods'] != ['A','B','C','D']:
            raise ValueError('Common sources are not registered for every method')
        sources=[]
        for member in common['sources']:
            path=evidence/'run'/member['file']
            if sha(path) != member['sha256'] or len(path.read_text()) != member['characters']:
                raise ValueError('Frozen full common source differs')
            sources.append({'name':member['name'],'source_sha256':member['sha256'],
                            'scope':member['scope'],'complete_source_text':path.read_text()})
        common_data={'common_source_data':{'sources':sources}}
    for request_path in (evidence/'run/calls').glob('*.request.json'):
        request=json.loads(request_path.read_text())
        payload=request['payload']
        if (payload['model'] != protocol['model']
                or payload['provider']['only'] != [protocol['provider']]
                or payload['provider']['allow_fallbacks'] is not False
                or request['authorization_header_omitted'] is not True
                or hashlib.sha256(json.dumps(payload,ensure_ascii=False).encode()).hexdigest()
                   != request['payload_sha256']):
            raise ValueError('Retained model request identity or provider differs')
        if common_data is not None:
            messages=payload['messages']
            if messages[-1]['role']!='user' or json.loads(messages[-1]['content'])!=common_data:
                raise ValueError('Actual request omitted or altered shared source data')
            common_request_n += 1
    for wg in {identifier.split('_')[0] for identifier in tasks}:
        guard=json.loads((evidence/'run/source_guards'/(wg+'.json')).read_text())
        if (guard['unchanged'] is not True or guard['before'] != guard['after']
                or guard['before'] != protocol['graph_sources'][wg]):
            raise ValueError('Frozen graph execution source differs')
    recovery_proof = None
    if (evidence/'run/adapter_pre_call_recovery.json').exists():
        recovery_spec = importlib.util.spec_from_file_location('sequence_first_call_checks', evidence/'runtime/verify_sequence_recovery.py')
        recovery_module = importlib.util.module_from_spec(recovery_spec)
        recovery_spec.loader.exec_module(recovery_module)
        recovery_proof = recovery_module.verify(evidence/'run')
    return {'status':'PASS','additional_admitted_n':n,
            'global_admitted_union_n':repair_proof['global_admitted_union_n'],
            'global_unresolved_n':repair_proof['global_unresolved_n'],
            'full_denominator_method_scores':n*4,'paired_uncertainty_comparisons':12,
            'phase':phase_proof,'repair_proof':repair_proof,
            'evidence_manifest_sha256':sha(evidence/'evidence_manifest.json'),
            'new_api_calls_during_replay':0,'new_database_executions_during_replay':0,
            'common_source_requests_verified':common_request_n,
            'expert_validation_n':0, 'adapter_pre_call_recovery':recovery_proof}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--parent',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    roots=[args.evidence.resolve(),args.bundle.resolve(),args.parent.resolve()]
    if any(args.out.resolve().is_relative_to(root) for root in roots):
        raise ValueError('Verification output must be outside frozen evidence')
    report=verify(*roots)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'additional_admitted_n':report['additional_admitted_n'],
                      'method_scores':report['full_denominator_method_scores']}))
