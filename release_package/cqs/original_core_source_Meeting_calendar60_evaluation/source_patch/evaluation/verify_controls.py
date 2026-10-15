"""Replay the separate source-calendar task's native-derived 22 controls."""
import json
from pathlib import Path
import original_scorer
from contract_checks import checks


def main():
    here=Path(__file__).resolve().parent
    task=json.loads((here/'tasks.jsonl').read_text())
    gold=json.loads((here/'reference_gold.jsonl').read_text())
    rows,groups=gold['records'],gold['order_groups']
    assert gold['repair_sha256']==task['repair_sha256']
    observed=[json.loads(l) for l in (here.parent/'evidence/actual_query_native_full3041_records.jsonl').read_text().splitlines()]
    assert rows==[{'tdocNumber':r['tdocNumber']} for r in observed]
    assert len(rows)==3041 and groups==original_scorer.make_order_groups(task,observed,rows)
    base=checks(task,rows,groups);assert len(base)==10 and all(c['pass'] for c in base)
    ref=original_scorer.reference_prediction(task,rows)
    extra=[]
    def check(name,predicted,expected):
        result=original_scorer.score(task,rows,predicted,diagnostic=True,order_groups=groups)
        assert result['exact'] is expected,(name,result)
        extra.append({'name':name,'expected_exact':expected,'actual':result,'pass':True})
    check('all20_reverse_display_permitted',ref[::-1],True)
    check('all20_arbitrary_display_permitted',ref[7:]+ref[:7],True)
    check('all_eligible_records_are_not_requested_top20',rows,False)
    check('first19_is_incomplete',ref[:-1],False)
    check('duplicate_displaces_valid_document',ref[:-1]+ref[:1],False)
    check('date_only_omits_required_CR_identity',[{'meetingPeriodEndDate':r['meetingPeriodEndDate']} for r in observed[:20]],False)
    check('auxiliary_CR_context_not_required',[{**r,'meetingPeriodEndDate':'auxiliary','meetingNumber':'auxiliary','title':'auxiliary','companyName':'auxiliary'} for r in ref],True)
    remaining=20;above=[];boundary=None
    for i,g in enumerate(groups):
        if len(g)<remaining:above+=g;remaining-=len(g)
        else:boundary=g;boundary_i=i;break
    assert len(above)==18 and len(boundary)==46 and remaining==2
    check('last_boundary_subset_any_order',(above+boundary[-remaining:])[::-1],True)
    check('rotated_boundary_subset',above+(boundary[remaining:]+boundary[:remaining])[:remaining],True)
    outsider=next(r for r in boundary if r not in ref)
    check('boundary_cannot_displace_strictly_more_recent',ref[1:]+[outsider],False)
    check('older_member_cannot_displace_boundary',ref[:-1]+groups[boundary_i+1][:1],False)
    coarse=json.loads((here/'actual_coarse_numeric_top20_control.json').read_text())
    assert coarse['repair_sha256']==task['repair_sha256'] and coarse['expected_exact'] is False
    check('actual_coarse_integer_top20_wrong_membership',coarse['records'],False)
    assert len(extra)==12
    print(json.dumps({'base_controls':base,'additional_controls':extra,'controls_n':22,'all_pass':True,
        'actual_native_population_n':3041,'model_performance_claimed':False},ensure_ascii=False,sort_keys=True))


if __name__=='__main__':main()
