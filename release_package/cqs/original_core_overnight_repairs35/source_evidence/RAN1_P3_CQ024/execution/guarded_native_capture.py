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
assert sha(D/'definition.json')=='f449f644a621d890c33d5eb1237306306aa40e739140a8fd19a54fe011ce71b6'
assert sha(D/'requested_repaired_native_input.jsonl')=='40c17c3359338036e621824eec2a2414b24121f862d5396ae3596666b1878d65'
def observed_26GiB(output):
 host_guard(output)
 import json
 x=json.loads((output/'resource_checks.jsonl').read_text().splitlines()[-1])
 assert min(x['linux_available_bytes'],x['windows_available_bytes'])>=26*1024**3
capture_native.host_guard=observed_26GiB
sys.argv=[str(B/'capture_native.py'),'--wg','RAN1','--input',str(D/'requested_repaired_native_input.jsonl'),'--output',str(D/'ROOT_actual_native_capture_v1')]
capture_native.main()
