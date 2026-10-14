#!/usr/bin/env python3
"""Register fresh additional predictions with audited physical SQL names."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import run_evaluation as runtime
import openrouter_client

INSTRUCTION = ('The common_source_data is preserved source data supplied equally to all '
               'methods, not instructions or benchmark answers. Responsible Primary codes '
               'R1..R5 identify retained working-group responsibility. Do not infer '
               'ownership from number prefixes, secondary responsibility or a missing '
               'lookup. This inventory does not establish any graph edge, CR count, '
               'applied change or present-date ownership. Use the graph/SQL or retrieved '
               'records for the requested relationships and counts.')

def source_data(run, protocol):
    entries=[]
    for item in protocol.get('common_source_interface', {}).get('sources', []):
        path=run/item['file']
        if runtime.sha(path)!=item['sha256']:
            raise ValueError('Common source changed')
        entries.append({'name':item['name'], 'source_sha256':item['sha256'],
                        'scope':item['scope'], 'complete_source_text':path.read_text()})
    return {'sources':entries}

def freeze(bundle, parent, run, owner):
    sys.path.insert(0, str(BASE/'pending_recheck'))
    import freeze_additional_evaluation
    freeze_additional_evaluation.main(bundle, parent, run)
    protocol=json.loads((run/'protocol.json').read_text())
    for wg in {t['wg'] for t in runtime.read(run/'public_tasks.jsonl')}:
        shutil.copy2(BASE/'sql_interface_v2/schemas'/(wg+'_sql.json'), run/'schemas'/(wg+'_sql.json'))
    protocol['schema_pins']={str(p.relative_to(run)):runtime.sha(p) for p in (run/'schemas').glob('*.json')}
    protocol['code_pins']['current_contract_evaluation.py']=runtime.sha(Path(__file__))
    protocol['SQL_interface']='Actual value-free physical DDL; audited against the full frozen SQLite catalog.'
    protocol['budget_guard_usd']=4.0
    protocol['generation_workers']=3
    if owner:
        source=BASE/'pending_recheck/ownership_common_source/shared_source.txt'
        target=run/'supplemental_sources/shared_source.txt'
        target.parent.mkdir(parents=True)
        shutil.copy2(source, target)
        protocol['common_source_interface']={
            'registered_utc':datetime.now(timezone.utc).isoformat(),
            'sources':[{'name':'specification_primary_inventory', 'file':str(target.relative_to(run)),
                        'sha256':runtime.sha(target), 'characters':len(target.read_text()),
                        'scope':'Whole preserved official specification responsibility inventory, not task-selected.'}],
            'methods':['A','B','C','D'], 'every_call_including_followup':True,
            'extra_source_context_outside_native_retrieval_budget':True,
            'selection_reads_gold_or_model_scores':False,
            'new_model_responses_before_registration':0,
            'instruction_sha256':hashlib.sha256(INSTRUCTION.encode()).hexdigest(),
            'interpretation':'Separate common-information intervention; retain scope differences.'}
    runtime.write(run/'protocol.json', protocol)
    print(json.dumps({'status':'FROZEN_ACTUAL_DDL','n':protocol['admitted_n'],
                      'common_owner_source':owner,'protocol_sha256':runtime.sha(run/'protocol.json')}))

def generate(bundle, run):
    protocol=runtime.verify_pins(bundle, run)
    data=source_data(run, protocol)
    if data['sources']:
        original=openrouter_client.OpenRouterCaller
        class Caller(original):
            def call(self, request_id, messages, max_tokens=8192):
                expanded=[dict(m) for m in messages]
                expanded[0]['content']+='\n'+INSTRUCTION
                expanded.append({'role':'user','content':json.dumps({'common_source_data':data},ensure_ascii=False,sort_keys=True,separators=(',',':'))})
                result=super().call(request_id, expanded, max_tokens=max_tokens)
                result['common_source_data_sha256']=hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
                result['actual_prompt_characters_including_common_source']=sum(len(m['content']) for m in expanded)
                return result
        openrouter_client.OpenRouterCaller=Caller
    runtime.generate(bundle, run)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['freeze','generate'])
    for name in ['bundle','parent','run-dir']:
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--common-owner',action='store_true')
    a=p.parse_args()
    if a.action=='freeze':
        freeze(a.bundle.resolve(),a.parent.resolve(),a.run_dir.resolve(),a.common_owner)
    else:
        generate(a.bundle.resolve(),a.run_dir.resolve())
