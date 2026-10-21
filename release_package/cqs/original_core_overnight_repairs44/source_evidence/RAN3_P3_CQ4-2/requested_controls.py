"""Replay unchanged scoring and same-document event counterexamples."""
import copy,re

def run(task,gold,source_rows,regex_prefix,regex_suffix,scorer,contract_checks):
 generic=contract_checks.checks(task,gold)
 assert all(c['pass'] for c in generic)
 specific=[]
 def check(name,rows,expected):
  result=scorer.score(task,gold,rows,diagnostic=True)
  assert result['exact'] is expected,(name,result)
  specific.append({'check':name,'expected_exact':expected,'pass':True,'result':result})
 check('unordered_serialization_same_six_requested_identities',list(reversed(gold)),True)
 check('unrequested_CR_field_can_be_absent_or_null',[dict(r,tdocNumber=None) for r in gold],True)
 for name,bad in [('withdrawn_CR_Resolution_displaces_approved','WA-97bis-10.5.5-001'),('revised_then_noted_is_not_approval','WA-118-12.2.2.1-001'),('reference_only_old_endorsed_CR_is_not_current_event','CON-121bis-26.3-001')]:
  assert any(r['resolutionId']==bad and not r['source_role_positive'] for r in source_rows)
  p=copy.deepcopy(gold);p[0]['resolutionId']=bad;check(name,p,False)
 check('missing_selected_cutoff_Resolution',gold[1:],False)
 check('duplicate_identity_displaces_distinct_selected_Resolution',gold[:-1]+gold[:1],False)
 p=copy.deepcopy(gold);p[0]['resolutionId']=None;check('null_requested_identity',p,False)
 p=copy.deepcopy(gold);p[0]['resolutionId']=121;check('integer_requested_identity',p,False)
 td='R3-123456'
 samples=[('same_CR_endorsed',td+'\tCR title\nThe document was endorsed.',True),('same_CR_revised',td+'\tCR title\nThe document was revised to R3-654321.',False),('different_CR_endorsed',td+'\tCR title\nThe document was noted.\nR3-654321\tOther CR\nThe document was endorsed.',False),('Replaces_reference_not_header','R3-654321\tOther CR\nReplaces\n'+td+'\nThe document was endorsed.',False),('same_CR_approved_Decision_prefix',td+'\tCR title\nDecision:\tThe document was approved.',True),('same_CR_not_endorsed',td+'\tCR title\nThe document was not endorsed.',False),('same_CR_conditional_agreement',td+'\tCR title\nThe document was conditionally agreed.',True),('near_word_not_approval',td+'\tCR title\nThe document was approvedPending.',False)]
 events=[]
 for name,body,expected in samples:
  actual=bool(re.fullmatch(regex_prefix+td+regex_suffix,body));assert actual is expected,(name,actual)
  events.append({'check':name,'body':body,'expected':expected,'actual':actual,'pass':True})
 return {'generic_controls':generic,'requested_role_controls':specific,'source_event_controls':events,'total_controls_n':len(generic)+len(specific)+len(events)}
