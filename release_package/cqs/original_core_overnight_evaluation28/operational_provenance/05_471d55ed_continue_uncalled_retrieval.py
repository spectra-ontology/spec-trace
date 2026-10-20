"""Run only the two retrieval arms that failed before any model request."""
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import shutil
import sys

HERE=Path(__file__).resolve().parent
A=HERE.parent
BASE=A/'evaluation/compatibility_runtime'
RUN=A/'evaluation/compatibility_trial'
FIRST=A/'evaluation/first_trial'
sys.path.insert(0,str(BASE))
import run_evaluation as runtime
import retrieval_adapter as retrieval
from openrouter_client import OpenRouterCaller

assert not sys.flags.optimize
registration=A/'sequence_compatibility_recovery_registration.json'
assert runtime.sha(registration)=='cc2f4f8d25a5ef887361a729e6b417afd31af08ae55b22c415c0c52560664000'
protocol=runtime.verify_pins(Path(json.loads((A/'scope.json').read_text())['offline_bundle_before_calls']['path']).parent,RUN)
assert protocol['authorized_incremental28_compatibility_recovery']['registration_sha256']==runtime.sha(registration)
assert not list((RUN/'calls').glob('*_C_*')) and not list((RUN/'calls').glob('*_D_*'))
for path in (FIRST/'calls').glob('*'):
    assert runtime.sha(path)==runtime.sha(RUN/'calls'/path.name)
root=next(p for p in HERE.parents if (p/'CLAUDE.md').exists())
sys.path.insert(0,str(root/'scripts/common/common'))
import credentials
caller=OpenRouterCaller(RUN,credentials.secret('OPENROUTER_API_KEY'),protocol['budget_guard_usd'])
tasks=runtime.read(RUN/'public_tasks.jsonl');assert len(tasks)==1
task=tasks[0]
def job(arm):
    method=runtime.ARMS[arm]
    target=RUN/'arm_outputs'/method/(task['id']+'.json')
    assert not target.exists()
    try:out=retrieval.evaluate(task,arm,caller,RUN)
    except Exception as exc:
        out={'id':task['id'],'repair_sha256':task['repair_sha256'],'records':[],
            'status':'ADAPTER_EXCEPTION','error_type':type(exc).__name__,'error':str(exc)[:1000]}
    runtime.write(target,out)
    return {'arm':arm,'status':out['status']}
with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(job,['C','D']))
runtime.write(RUN/'generation_complete.json',{'completed_method_items':4,'required':4,
    'first_two_structured_items_reused':2,'first_retrieval_items':2,'quality_rerolls':0})
shutil.copyfile(RUN/'usage.json',RUN/'usage_new_retrieval_calls.json')
responses=[json.loads(p.read_text()) for p in (RUN/'calls').glob('*.response.json')]
cost=sum((Decimal(str(r['response']['usage']['cost'])) for r in responses),Decimal(0))
assert len(responses)==5 and all(r['http_status']==200 and r['attempt']==0 for r in responses)
assert cost<=Decimal('1')
usage=json.loads((RUN/'usage.json').read_text())
usage.update(received_response_calls=5,known_actual_cost_usd=float(cost),guard_reserved_or_spent_usd=float(cost),
    budget_guard_usd=1.0,aggregation='Exact raw usage from original2 plus first3 retrieval calls; source client receipts retained')
runtime.write(RUN/'usage.json',usage)
runtime.write(RUN/'usage_aggregation_receipt.json',{'status':'PASS','original_calls':2,
    'new_first_retrieval_calls':3,'exact_total_cost_usd_decimal':str(cost),
    'new_retrieval_client_summary_sha256':runtime.sha(RUN/'usage_new_retrieval_calls.json'),
    'original_client_summary_sha256':runtime.sha(FIRST/'usage.json'),
    'all_original_request_response_bytes_unchanged':True,'quality_rerolls':0})
print(json.dumps({'status':'COMPLETE_FIRST_RETRIEVAL_CALLS','arms':results,'all_calls':5,'cost':str(cost)}))
