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
assert sha(D/'definition.json')=='46fff937de4ea5873225b98d3d48b5997ca94b7385ad5c7249ffd530b94aa20f'
assert sha(D/'requested_repaired_native_input.jsonl')=='785a302cd95f8164362331e7bb673f8d874d2d5595d91a3fb7f0852374529a3e'
def observed_26GiB(output):
 host_guard(output)
 import json
 x=json.loads((output/'resource_checks.jsonl').read_text().splitlines()[-1])
 assert min(x['linux_available_bytes'],x['windows_available_bytes'])>=26*1024**3
capture_native.host_guard=observed_26GiB
sys.argv=[str(B/'capture_native.py'),'--wg','RAN1','--input',str(D/'requested_repaired_native_input.jsonl'),'--output',str(D/'ROOT_actual_native_capture_v1')]
capture_native.main()
