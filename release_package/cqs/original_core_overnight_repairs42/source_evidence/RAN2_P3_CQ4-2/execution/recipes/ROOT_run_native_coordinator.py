"""One local-only native attempt using the unchanged guarded capture."""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

if sys.flags.optimize:
    raise SystemExit('Assertions must remain enabled')
HERE = Path(__file__).resolve().parent
S = HERE.parent
B = next(p for p in HERE.parents if p.name == 'overnight_reaudit')
A = HERE
guard = A / 'ROOT_outer_native_reserve_guard.py'
assert hashlib.sha256(guard.read_bytes()).hexdigest() == 'af6c7945b7de529cfcf8c233f330d002ad5f44e70d819762a00905e3c52af736'
assert not (A / 'ROOT_actual_guarded_persistent_cim_execute_RAN2').exists()
assert not (A / 'ROOT_actual_native_capture_v1').exists()
input_file = A / 'requested_repaired_native_input.jsonl'
assert hashlib.sha256(input_file.read_bytes()).hexdigest() == '8a6e947bb5214bf6ec39e6ec9d5d160e0e4f18e1c55f524c8b1fa610d4a98071'
sys.path.insert(0, str(B / 'authorized_incremental29_OpenRouter_release/operational_guards'))
from fresh_windows_memory import Broker
broker = Broker(HERE / 'actual_fresh_memory_session_v1')
receipt = {'paid_API_calls': 0, 'public_mutations': 0, 'guard_sha256': hashlib.sha256(guard.read_bytes()).hexdigest()}
code = None
try:
    broker.start()
    code = subprocess.run([sys.executable, '-B', str(guard), 'execute_RAN2']).returncode
    if code != 0:
        raise RuntimeError('Native guard failed; preserve its receipt')
    assert hashlib.sha256(input_file.read_bytes()).hexdigest() == '8a6e947bb5214bf6ec39e6ec9d5d160e0e4f18e1c55f524c8b1fa610d4a98071'
    receipt['status'] = 'NATIVE_WRAPPER_PASS_PENDING_SCIENTIFIC_BINDING'
except BaseException as exc:
    receipt['status'] = 'FAIL_PRESERVED'
    receipt['failure'] = {'type': type(exc).__name__, 'message': str(exc)[:2000]}
finally:
    broker.close()
    receipt['child_exit'] = code
    receipt['observed_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with (HERE / 'actual_ROOT_native_coordinator_receipt.json').open('x') as f:
        json.dump(receipt, f, indent=2)
        f.write('\n')
    print(json.dumps(receipt), flush=True)
if receipt['status'] == 'FAIL_PRESERVED':
    raise SystemExit(1)
