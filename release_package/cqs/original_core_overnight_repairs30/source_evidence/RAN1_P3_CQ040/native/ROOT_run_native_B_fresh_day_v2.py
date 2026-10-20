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
A = S / 'local_only41/main_B/RAN1_P3_CQ040/native_attempt_v2'
guard = A / 'ROOT_outer_native_reserve_guard.py'
assert hashlib.sha256(guard.read_bytes()).hexdigest() == 'd06ac4d38f04e3423661300bd3bd22fc5e7eb3d2c212cd07611ddeeb8c220138'
assert not (A / 'ROOT_actual_guarded_persistent_cim_execute_RAN1').exists()
assert not (A / 'ROOT_actual_native_capture_v1').exists()
input_file = A / 'requested_repaired_native_input.jsonl'
assert hashlib.sha256(input_file.read_bytes()).hexdigest() == '777b06097fd48374ba64dfc1e7391872c2ad1a95b50ca69fef6238bdaead0039'
sys.path.insert(0, str(B / 'authorized_incremental29_OpenRouter_release/operational_guards'))
from fresh_windows_memory import Broker
broker = Broker(HERE / 'ROOT_native_B_fresh_day_v2_memory')
receipt = {'paid_API_calls': 0, 'public_mutations': 0, 'guard_sha256': hashlib.sha256(guard.read_bytes()).hexdigest()}
code = None
try:
    broker.start()
    code = subprocess.run([sys.executable, '-B', str(guard), 'execute_RAN1']).returncode
    if code != 0:
        raise RuntimeError('Native guard failed; preserve its receipt')
    assert hashlib.sha256(input_file.read_bytes()).hexdigest() == '777b06097fd48374ba64dfc1e7391872c2ad1a95b50ca69fef6238bdaead0039'
    receipt['status'] = 'NATIVE_WRAPPER_PASS_PENDING_SCIENTIFIC_BINDING'
except BaseException as exc:
    receipt['status'] = 'FAIL_PRESERVED'
    receipt['failure'] = {'type': type(exc).__name__, 'message': str(exc)[:2000]}
finally:
    broker.close()
    receipt['child_exit'] = code
    receipt['observed_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with (HERE / 'ROOT_native_B_fresh_day_v2_coordinator_receipt.json').open('x') as f:
        json.dump(receipt, f, indent=2)
        f.write('\n')
    print(json.dumps(receipt), flush=True)
if receipt['status'] == 'FAIL_PRESERVED':
    raise SystemExit(1)
