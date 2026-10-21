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
assert hashlib.sha256(guard.read_bytes()).hexdigest() == '8d8ad1734ca5b88fd029f9da9284469934e97ab5abaaea6a9af3bb64d54ba503'
assert not (A / 'ROOT_actual_guarded_persistent_cim_execute_RAN1').exists()
assert not (A / 'ROOT_actual_native_capture_v1').exists()
input_file = A / 'requested_repaired_native_input.jsonl'
assert hashlib.sha256(input_file.read_bytes()).hexdigest() == '40c17c3359338036e621824eec2a2414b24121f862d5396ae3596666b1878d65'
sys.path.insert(0, str(B / 'authorized_incremental29_OpenRouter_release/operational_guards'))
from fresh_windows_memory import Broker
broker = Broker(HERE / 'actual_fresh_memory_session_v1')
receipt = {'paid_API_calls': 0, 'public_mutations': 0, 'guard_sha256': hashlib.sha256(guard.read_bytes()).hexdigest()}
code = None
try:
    broker.start()
    code = subprocess.run([sys.executable, '-B', str(guard), 'execute_RAN1']).returncode
    if code != 0:
        raise RuntimeError('Native guard failed; preserve its receipt')
    assert hashlib.sha256(input_file.read_bytes()).hexdigest() == '40c17c3359338036e621824eec2a2414b24121f862d5396ae3596666b1878d65'
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
