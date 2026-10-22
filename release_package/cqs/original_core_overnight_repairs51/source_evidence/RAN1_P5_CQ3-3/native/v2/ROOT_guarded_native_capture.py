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
assert sha(D/'definition.json')=='cd69532a9c04ad4e8e516b636f4a04d247fc6bcf8b0b921d7fbb311114cb5241'
assert sha(D/'requested_repaired_native_input.jsonl')=='d5bcb52f3053b01ea697d7570c4510a570126162b27f3ff65659532f35f88c23'
def observed_26GiB(output):
 host_guard(output)
 import json
 x=json.loads((output/'resource_checks.jsonl').read_text().splitlines()[-1])
 assert min(x['linux_available_bytes'],x['windows_available_bytes'])>=26*1024**3
capture_native.host_guard=observed_26GiB
sys.argv=[str(B/'capture_native.py'),'--wg','RAN1','--input',str(D/'requested_repaired_native_input.jsonl'),'--output',str(D/'ROOT_actual_native_capture_v1')]
capture_native.main()
