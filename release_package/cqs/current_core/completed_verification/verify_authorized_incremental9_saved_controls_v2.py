"""Replay heterogeneous saved controls for exactly six AUTH9 contracts, no DB/API."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
EXPECTED={'RAN2_P2_CQ2-1','RAN1_P3_CQ026','RAN3_P2_CQ1-6','RAN4_P2_CQ1-6','RAN2_P2_CQ2-5','RAN1_P2_CQ4-2'}
def read(p):return json.loads(Path(p).read_text())
def lines(p):return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
def without_flag(v):return {k:x for k,x in v.items() if k!='diagnostic_only'}
def verify(bundle):
    bundle=Path(bundle).resolve();sys.path.insert(0,str(bundle));import original_scorer
    tasks={x['id']:x for x in lines(bundle/'tasks.jsonl')};golds={x['id']:x for x in lines(bundle/'reference_gold.jsonl')}
    assert set(tasks)==set(golds)==EXPECTED
    cases=[];total=synthetic=0
    for ident,task in tasks.items():
        gold=golds[ident];root=bundle/'gate_evidence'/ident
        raw=read(root/'additional_saved_controls.json')
        controls=raw['additional_controls'] if isinstance(raw,dict) else raw
        synthetic_gold=synthetic_groups=None
        if ident.startswith('RAN2_'):
            witness=read(root/'additional_control_source_witness.json')
            fixture=witness['synthetic_fixture']
            assert len(fixture)==13 and all(x['resolutionId'].startswith('SYNTHETIC-ONLY-') for x in fixture)
            synthetic_gold=[{'resolutionId':x['resolutionId']} for x in fixture]
            synthetic_groups=original_scorer.make_order_groups(task,fixture,synthetic_gold)
        checks=[]
        for case in controls:
            source_free=case.get('synthetic_source_free_fixture',False)
            actual_gold=synthetic_gold if source_free else gold['records']
            groups=synthetic_groups if source_free else gold['order_groups']
            prediction=case.get('input_records',case.get('predictions',case.get('prediction')))
            assert prediction is not None
            diagnostic=original_scorer.score(task,actual_gold,prediction,diagnostic=True,order_groups=groups)
            validated=original_scorer.score(dict(task,validation_status='validated'),actual_gold,prediction,diagnostic=False,order_groups=groups)
            stored=case.get('diagnostic_score',case.get('actual_diagnostic',case.get('actual')))
            assert diagnostic==stored,(ident,case['name'],'saved diagnostic score changed')
            saved_validated=case.get('validated_score',case.get('actual_validated'))
            if saved_validated is not None:assert validated==saved_validated,(ident,case['name'],'saved validated score changed')
            assert without_flag(diagnostic)==without_flag(validated)
            assert diagnostic['exact'] is case['expected_exact'],(ident,case['name'])
            if 'pass' in case:assert case['pass'] is True
            checks.append({'name':case['name'],'pass':True,'expected_exact':case['expected_exact'],'synthetic_source_free_fixture':source_free})
            total+=1;synthetic+=int(source_free)
        assert checks
        if isinstance(raw,dict):
            assert raw['all_controls_pass'] is True
            assert raw['controls_n']==len(raw['basic_controls'])+len(checks)
            saved_gold=read(root/'additional_requested_reference_gold.json')
            assert saved_gold['rows']==gold['records']
            assert saved_gold['order_groups']==gold['order_groups']
        cases.append({'id':ident,'additional_controls_n':len(checks),'synthetic_source_free_controls_n':sum(c['synthetic_source_free_fixture'] for c in checks),'checks':checks})
    return {'status':'PASS','cases':cases,'additional_saved_controls_n':total,'synthetic_source_free_controls_n':synthetic,'actual_population_controls_n':total-synthetic,'diagnostic_and_validated_modes_equal':True,'database_queries_n':0,'API_calls_n':0,'limits':'Explicit synthetic tie-boundary fixtures are distinct from the actual native/gold population; optional auxiliary truth is not scored.'}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',type=Path,required=True);p.add_argument('--out',type=Path);a=p.parse_args();r=verify(a.bundle)
    if a.out:assert not a.out.exists();a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(r))
