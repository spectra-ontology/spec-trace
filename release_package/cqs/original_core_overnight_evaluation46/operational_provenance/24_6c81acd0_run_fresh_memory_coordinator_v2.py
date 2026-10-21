"""One owned fresh CIM broker; immutable first-attempt cohort29 evaluation."""
from datetime import datetime,timezone
import hashlib,json,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
A=HERE.parent
sys.path.insert(0,str(HERE))
from fresh_windows_memory import Broker
assert not sys.flags.optimize
assert hashlib.sha256((A/'scope.json').read_bytes()).hexdigest()=='e830fb1e9d061353a6a3b47fcd27dd9b5856d7eab049dbcc5e2cd951e6aac1c5'
assert not (A/'evaluation/first_trial').exists()
assert not (A/'actual_ROOT_fresh_memory_coordinator_v2.json').exists()
assert not list((A/'evaluation').glob('**/calls/*.request.json'))
os.environ['WSL_INTEROP']='/run/WSL/1_interop'
broker=Broker(HERE/'actual_fresh_cim_session_v2')
stages=[];failure=None
try:
    broker.start()
    print(json.dumps({'status':'FRESH_CIM_READY'}),flush=True)
    import time
    from fresh_windows_memory import observe
    while True:
        linux,windows=observe()
        with (A/'actual_v2_pre_freeze_memory_wait.jsonl').open('a') as record:
            record.write(json.dumps({'observed_utc':datetime.now(timezone.utc).isoformat(),'Linux_available_bytes':linux,'Windows_available_bytes':windows,'freeze_admission_minimum_bytes':int(27.25*1024**3)})+'\n')
        if min(linux,windows)>=int(27.25*1024**3):break
        print(json.dumps({'status':'WAITING_FRESH_FREEZE_RESERVE','Linux_available_GiB':round(linux/1024**3,2),'Windows_available_GiB':round(windows/1024**3,2),'calls':0}),flush=True)
        time.sleep(10)
    for stage,name in [('freeze','run_root_guarded_freeze_retry_v2.py'),
        ('generate','run_root_guarded_evaluation_stage_persistent_cim.py'),
        ('execute_RAN3','run_root_guarded_native_and_assembly_persistent_cim.py'),
        ('assemble','run_root_guarded_native_and_assembly_persistent_cim.py'),
        ('analyze','run_root_guarded_explicit_optional_analysis.py')]:
        with (A/('actual_ROOT_v2_'+stage+'_stdout')).open('x') as out,(A/('actual_ROOT_v2_'+stage+'_stderr')).open('x') as err:
            result=subprocess.run([sys.executable,'-B',str(HERE/name),stage],stdout=out,stderr=err)
        stages.append({'stage':stage,'returncode':result.returncode})
        print(json.dumps(stages[-1]),flush=True)
        if result.returncode:
            raise RuntimeError('Stage failed; preserve first outputs: '+stage)
except BaseException as exc:
    failure={'type':type(exc).__name__,'message':str(exc)[:1500]}
finally:
    broker.close()
    receipt={'status':'PASS' if failure is None else 'FAIL_PRESERVED','observed_utc':datetime.now(timezone.utc).isoformat(),
        'stages':stages,'failure':failure,'fresh_observations_file':str(broker.directory/'actual_observations.jsonl'),
        'cached_memory_values':0,'quality_rerolls':0,'transport_only':'Each nonce runs fresh Get-CimInstance'}
    with (A/'actual_ROOT_fresh_memory_coordinator_v2.json').open('x') as stream:
        stream.write(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'status':receipt['status'],'failure':failure}),flush=True)
if failure is not None:raise SystemExit(1)
