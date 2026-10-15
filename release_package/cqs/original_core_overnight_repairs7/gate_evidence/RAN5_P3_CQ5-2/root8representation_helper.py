"""Actual native-backed matrix representation controls through the pinned wrapper."""
import hashlib,json,sys
from pathlib import Path
B=Path(__file__).resolve().parent.parent
sys.dont_write_bytecode=True
S=B/'RAN2_RAN5/RAN5_matrix19_full_gate_preparation_v1/scoring_snapshot'
sys.path.insert(0,str(S))
import original_scorer
D=B/'RAN2_RAN5/RAN5_P3_CQ5-2_original_domain19_matrix_representations_source_only_v5/canonical_source_only_definition.json'
N=B/'root_evidence/RAN5_matrix19_original_recorded_full_native_v1/reference_outputs/RAN5_P3_CQ5-2/e0d635e8d7cca22df888d73b8a80770683b644f42c576f2755503ff2fffa725b.jsonl'
gold=[dict(zip(['companyName','specNumber','crCount'],json.loads(line))) for line in N.read_text().splitlines()]
task=json.loads(D.read_text());task['validation_status']='validated'
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
receipt={'status':'ROOT_ACTUAL_FULL3401_NATIVE_DENSE_SPARSE_EIGHT_CONTROLS_PASS','native_rows_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),'definition_sha256':hashlib.sha256(D.read_bytes()).hexdigest(),'repair_sha256':task['repair_sha256'],'controls_n':len(result),'controls':result,'diagnostic_and_validated_modes_equal':True,'same_prior_typed_kernel':True,'model_or_native_API_calls_n':0}
out=B/'root_evidence/RAN5_matrix19_root_actual_native_representation_controls_v1.json';out.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':receipt['status'],'controls_n':len(result),'receipt_sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
