"""Portable actual native-bound dense/sparse control replay; no API or native calls."""
import hashlib,json
from pathlib import Path
import original_scorer
from matrix_actual_controls import actual_controls
def root8_actual_controls(task,gold):
 companies=sorted({r['companyName'] for r in gold});families=sorted({r['specNumber'] for r in gold})
 nonzero=[r for r in gold if r['crCount']]
 assert len(companies)==179 and len(families)==19 and len(gold)==3401 and len(nonzero)<len(gold)
 matrix={'rowField':'companyName','columnField':'specNumber','valueField':'crCount','rowValues':companies,'columnValues':families,'default':0,'cells':nonzero}
 missing_axis=dict(matrix,rowValues=companies[1:],cells=[r for r in nonzero if r['companyName']!=companies[0]])
 bad_type=[dict(r) for r in gold];bad_type[0]['crCount']=bool(bad_type[0]['crCount'])
 aux=[dict(r) for r in gold];aux[0]['matrix']={'auxiliary':'not a sparse wrapper'}
 controls=[('complete_native_dense',gold,True),('complete_explicit_axes_sparse',[{'matrix':matrix}],True),
  ('omitted_company_axis_not_inferred',[{'matrix':missing_axis}],False),('positive_cells_without_axes_not_complete',nonzero,False),
  ('boolean_count_is_not_integer',bad_type,False),('repeated_dense_members_idempotent',gold+gold,True),
  ('auxiliary_matrix_field_does_not_trigger_sparse',aux,True),('reversed_axis_roles_rejected',[{'matrix':dict(matrix,rowField='specNumber',columnField='companyName')}],False)]
 result=[]
 for name,predicted,expected in controls:
  diagnostic=original_scorer.score(task,gold,predicted,diagnostic=True)
  validated=original_scorer.score(task,gold,predicted)
  assert diagnostic['exact'] is expected and validated['exact'] is expected,name
  assert {k:v for k,v in diagnostic.items() if k!='diagnostic_only'}=={k:v for k,v in validated.items() if k!='diagnostic_only'}
  result.append({'name':name,'expected_exact':expected,'actual_validated':validated,'pass':True})
 return result

def replay(bundle,tasks,golds):
 task=tasks['RAN5_P3_CQ5-2'];records=golds[task['id']]['records']
 gates=task['portable_gate_evidence']
 a=json.loads((bundle/gates['additional_controls']['file']).read_text())
 got=actual_controls(task,records)
 assert got==a['controls'] and len(got)==23
 root=json.loads((bundle/gates['root8representation_controls']['file']).read_text())
 got8=root8_actual_controls(task,records)
 assert got8==root['controls'] and len(got8)==8
 return {'status':'PASS','actual_matrix_controls_n':len(got)+len(got8)}
