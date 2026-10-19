from pathlib import Path
import json,sys
B=next(p for p in Path(__file__).resolve().parents if p.name=='overnight_reaudit')
sys.path.insert(0,str(B))
import capture_native
original=capture_native.host_guard
def guarded(output):
    original(output)
    last=json.loads((output/'resource_checks.jsonl').read_text().splitlines()[-1])
    assert min(last['linux_available_bytes'],last['windows_available_bytes'])>=26*1024**3
capture_native.host_guard=guarded
capture_native.main()
