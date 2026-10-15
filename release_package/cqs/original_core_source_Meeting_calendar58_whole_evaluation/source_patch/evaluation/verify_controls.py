"""Offline replay of the source58 task's23 actual-data scorer controls."""
import json
from pathlib import Path
import original_scorer
from contract_checks import checks


def main():
    here=Path(__file__).resolve().parent
    task=json.loads((here/'tasks.jsonl').read_text())
    gold=json.loads((here/'reference_gold.jsonl').read_text())
    observed=[json.loads(l)for l in (here.parent/'evidence/actual_query_native_full16017_records.jsonl').read_text().splitlines()]
    rows,groups=gold['records'],gold['order_groups']
    assert task['repair_sha256']==gold['repair_sha256']=='c4f534fda848bfac16ce25f5634c28fb7e7ec56a8b453d20ba2be34c2a0ec338'
    assert len(rows)==16017 and rows==[{'tdocNumber':r['tdocNumber']}for r in observed]
    assert groups==original_scorer.make_order_groups(task,observed,rows)
    base=checks(task,rows,groups);assert len(base)==10 and all(c['pass']for c in base)
    ref=original_scorer.reference_prediction(task,rows);assert len(ref)==10
    remaining,above=10,[]
    for i,g in enumerate(groups):
        if len(g)<remaining:above+=g;remaining-=len(g)
        else:boundary,boundary_i=g,i;break
    assert len(above)==0 and len(boundary)==563 and remaining==10
    extra=[]
    def check(name,predicted,expected):
        result=original_scorer.score(task,rows,predicted,diagnostic=True,order_groups=groups)
        assert result['exact'] is expected,(name,result)
        extra.append({'name':name,'expected_exact':expected,'actual':result,'pass':True})
    check('reverse_display_order_preserves_recent_top10',ref[::-1],True)
    check('rotated_display_order_preserves_recent_top10',ref[3:]+ref[:3],True)
    check('last_actual_boundary_subset_display_reversed',(above+boundary[-remaining:])[::-1],True)
    check('rotated_actual_boundary_subset',above+(boundary[remaining:]+boundary[:remaining])[:remaining],True)
    check('all16017_documents_are_not_requested_top10',rows,False)
    check('nine_entries_are_incomplete',ref[:-1],False)
    check('eleven_entries_exceed_top10',ref+groups[boundary_i+1][:1],False)
    check('duplicate_displaces_valid_CR',ref[:-1]+ref[:1],False)
    check('meeting_date_without_CR_identity',[{'meetingPeriodEndDate':r['meetingPeriodEndDate']}for r in observed[:10]],False)
    check('older_actual_meeting_CR_displaces_boundary',ref[:-1]+groups[boundary_i+1][:1],False)
    check('invented_CR_identity_displaces_actual',ref[:-1]+[{'tdocNumber':'R4-SOURCE58-NOT-A-RECORDED-CR'}],False)
    check('nonrequired_calendar_and_title_context_do_not_add_answer_roles',[{**r,'meetingPeriodEndDate':'auxiliary','title':'auxiliary'}for r in ref],True)
    coarse=json.loads((here/'actual_coarse_numeric_top10_control.json').read_text())
    assert coarse['repair_sha256']==task['repair_sha256']
    check('actual_coarse_integer_top10_membership_diagnostic',coarse['records'],coarse['expected_exact'])
    assert len(extra)==13
    print(json.dumps({'base_controls':base,'additional_controls':extra,'controls_n':23,'all_pass':True,
        'actual_native_population_n':16017,'model_performance_claimed':False},ensure_ascii=False,sort_keys=True))


if __name__=='__main__':main()
