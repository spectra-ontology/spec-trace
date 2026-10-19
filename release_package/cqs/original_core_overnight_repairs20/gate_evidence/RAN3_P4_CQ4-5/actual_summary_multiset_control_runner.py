from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import json,hashlib,sys
B=next(p for p in Path(__file__).resolve().parents if p.name=='overnight_reaudit');T=Path(__file__).resolve().parent
P=Path('/home/sihyeon/workspace/spectra-public/spec-trace/release_package/cqs/original_core_repair');sys.dont_write_bytecode=True;sys.path[:0]=[str(B.parents[1]/'original_repair'),str(P)]
import original_scorer,scorer

def pin(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
d=json.loads((T/'definition.json').read_text());records=[scorer.get_kernel().loads_exact(l) for l in (T/'controls/projected_native_records.jsonl').read_text().splitlines()];assert len(records)==10
counts=Counter(r['summary'] for r in records);assert sorted(counts.values())==[1,1,1,1,1,2,3]
unique=[{'summary':s} for s in counts];one_replaced=[dict(r) for r in records];duplicate=next(s for s,c in counts.items() if c==3);other=next(s for s,c in counts.items() if c==1);idx=next(n for n,r in enumerate(one_replaced) if r['summary']==duplicate);one_replaced[idx]={'summary':other}
cases=[('permutation_preserves_requested_multiset',list(reversed(records)),True),('deduplicating_equal_summaries_loses_CR_occurrences',unique,False),('same_length_and_same_unique_summaries_wrong_multiplicity',one_replaced,False),('missing_one_duplicate_occurrence',records[:6]+records[7:],False),('extra_duplicate_occurrence',records+[records[6]],False)]
out=[]
for name,pred,exact in cases:
 r=original_scorer.score(d,records,pred,diagnostic=True);assert r['exact'] is exact,(name,r);out.append({'control':name,'expected_exact':exact,'pass':True,'actual_score':r})
a={'checked_utc':datetime.now(timezone.utc).isoformat(),'id':d['id'],'repair_sha256':d['repair_sha256'],'status':'PASS_ACTUAL_MULTIPLICITY_AND_UNORDERED_SUMMARY_CONTROLS','source_summary_occurrences':10,'distinct_summary_values':len(counts),'actual_controls':out,'inputs':[pin(T/'definition.json'),pin(T/'controls/projected_native_records.jsonl'),pin(Path(original_scorer.__file__)),pin(P/'scorer.py')],'new_model_API_calls':0,'expert_validation_n':0}
f=T/'actual_additional_summary_multiset_controls.json';assert not f.exists();f.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':a['status'],'controls':len(out),'receipt':pin(f)}))
