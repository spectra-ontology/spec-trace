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
assert hashlib.sha256(guard.read_bytes()).hexdigest() == '9f6d145ab4ddd48db20b496a6e829d4973dbeb7fa5207157cb25a155a823a5c6'
assert not (A / 'ROOT_actual_guarded_persistent_cim_execute_RAN2').exists()
assert not (A / 'ROOT_actual_native_capture_v1').exists()
input_file = A / 'requested_repaired_native_input.jsonl'
assert hashlib.sha256(input_file.read_bytes()).hexdigest() == 'b45d4183c9b7e80b3701796cdffa989a6ca6f67fd70a9f07c1ab344c9d2265f5'
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
    assert hashlib.sha256(input_file.read_bytes()).hexdigest() == 'b45d4183c9b7e80b3701796cdffa989a6ca6f67fd70a9f07c1ab344c9d2265f5'
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
