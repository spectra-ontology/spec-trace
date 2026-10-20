"""Keep one owned fresh CIM transport for registered evaluation stages."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
A = HERE.parent
sys.path.insert(0, str(HERE))
from fresh_windows_memory import Broker

assert not sys.flags.optimize
assert hashlib.sha256((A/'scope.json').read_bytes()).hexdigest() == '1dd87540f079fc4ef445c5a30d6f3f56c011a41e0dede21ec85d38e741372f99'
assert hashlib.sha256((A/'evaluation/first_trial/protocol.json').read_bytes()).hexdigest() == '2ac742adc6bfc5eff3758f8c9eef1a0a424b8d98f1434b7b5ec25f83f87781bc'
assert not (A/'actual_ROOT_compatibility_memory_coordinator_v2.json').exists()
os.environ['WSL_INTEROP'] = '/run/WSL/1_interop'
broker = Broker(HERE/'actual_compatibility_cim_session_v2')
stages=[]
failure=None
try:
    broker.start()
    print(json.dumps({'status':'FRESH_CIM_READY','socket':os.environ['WSL_INTEROP']}),flush=True)
    for stage,script in [
        ('generate','run_guarded_compatibility_stage.py'),
        
        ('assemble','run_compatibility_assembly.py'),
        ('analyze','run_guarded_compatibility_stage.py')]:
        cmd=[sys.executable,'-B',str(HERE/script),stage]
        with (A/('actual_ROOT_compatibility_'+stage+'_stdout')).open('x') as out, (A/('actual_ROOT_compatibility_'+stage+'_stderr')).open('x') as err:
            result=subprocess.run(cmd,stdout=out,stderr=err)
        stages.append({'stage':stage,'returncode':result.returncode})
        print(json.dumps(stages[-1]),flush=True)
        if result.returncode:
            raise RuntimeError('Stage failed; preserve first outputs: '+stage)
except BaseException as exc:
    failure={'type':type(exc).__name__,'message':str(exc)[:1500]}
finally:
    broker.close()
    receipt={'status':'PASS' if failure is None else 'FAIL_PRESERVED',
        'observed_utc':datetime.now(timezone.utc).isoformat(),'stages':stages,
        'failure':failure,'fresh_observations_file':str(broker.directory/'actual_observations.jsonl'),
        'cached_memory_values':0,'quality_rerolls':0,
        'transport_only':'Persistent PowerShell process; each nonce runs fresh Get-CimInstance'}
    with (A/'actual_ROOT_compatibility_memory_coordinator_v2.json').open('x') as stream:
        stream.write(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'status':receipt['status'],'failure':failure}),flush=True)
if failure is not None:
    raise SystemExit(1)
