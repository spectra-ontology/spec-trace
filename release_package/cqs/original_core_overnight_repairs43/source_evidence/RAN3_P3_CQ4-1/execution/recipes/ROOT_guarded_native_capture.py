"""Run the original archival capture with fresh host-memory observations."""
import hashlib,importlib.util,sys
from pathlib import Path
D=Path(__file__).resolve().parent
B=next(p for p in D.parents if p.name=='overnight_reaudit')
G=B/'authorized_incremental29_OpenRouter_release/operational_guards'
sys.path[:0]=[str(G),str(B)]
import capture_native
from fresh_windows_memory import host_guard
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(D/'definition.json')=='18ea2b11a0f0eb3e8e30c7897179b5b94e637a257b0ef087ea7aa2b1787675e7'
assert sha(D/'requested_repaired_native_input.jsonl')=='d99826f6e031cc0c6c917afd429114bd0df60db0802837ac95869b4d33a836f9'
def observed_26GiB(output):
 host_guard(output)
 import json
 x=json.loads((output/'resource_checks.jsonl').read_text().splitlines()[-1])
 assert min(x['linux_available_bytes'],x['windows_available_bytes'])>=26*1024**3
capture_native.host_guard=observed_26GiB
sys.argv=[str(B/'capture_native.py'),'--wg','RAN3','--input',str(D/'requested_repaired_native_input.jsonl'),'--output',str(D/'ROOT_actual_native_capture_v1')]
capture_native.main()
