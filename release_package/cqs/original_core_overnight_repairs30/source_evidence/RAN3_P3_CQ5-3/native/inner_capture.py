"""Run the original archival capture with fresh host-memory observations."""
import hashlib,importlib.util,sys
if sys.flags.optimize: raise SystemExit("Run without -O/-OO")
from pathlib import Path
D=Path(__file__).resolve().parent
B=next(p for p in D.parents if p.name=='overnight_reaudit')
G=B/'authorized_incremental29_OpenRouter_release/operational_guards'
sys.path[:0]=[str(G),str(B)]
import capture_native
from fresh_windows_memory import host_guard
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def exact_input_guard():
 assert sha(D/'definition_each_spec_recorded_density_v2.json')=='cd785fed54451a447e35e09b81fb1109b72c8eddfe6c42e68e1db24f825e1839'
 assert sha(D/'native_input_each_spec_development_probe.jsonl')=='4a2e863e365dbee62096abb7781ab424da02fc5bd54b541f45492ed2516b1094'
 assert sha(B/'capture_native.py')=='3dfb502a86cec163a5fa5bc3b944129b0464ece27e8b02f865f52b603fbcc51b'
exact_input_guard()
def observed_26GiB(output):
 host_guard(output)
 import json
 x=json.loads((output/'resource_checks.jsonl').read_text().splitlines()[-1])
 assert min(x['linux_available_bytes'],x['windows_available_bytes'])>=26*1024**3
capture_native.host_guard=observed_26GiB
sys.argv=[str(B/'capture_native.py'),'--wg','RAN3','--input',str(D/'native_input_each_spec_development_probe.jsonl'),'--output',str(D/'ROOT_actual_guarded_persistent_cim_execute_RAN3/capture')]
capture_native.main()
exact_input_guard()
