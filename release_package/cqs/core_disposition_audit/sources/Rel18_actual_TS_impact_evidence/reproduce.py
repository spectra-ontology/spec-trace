"""Replay the sealed original Rel-18 study-to-TS source-role classification."""
import hashlib,json,subprocess,sys
from pathlib import Path
if sys.flags.optimize: raise SystemExit('Enabled checks required')
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
INVENTORY_SHA256='b7efc06aa50300efffb6ff4e53ac158c481cbd4f08bf332c59d9c003cb64d8b1'
SEAL_SHA256='b10a01a381271d8a49bc83555fbb73f51a7f222706450a693e41df5e0d40d402'
ID='RAN1_P5_CQ4-1'
def load(p): return json.loads(p.read_bytes())
def pin(p):
 b=p.read_bytes(); return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def main():
 assert pin(HERE/'immutable_inventory.json')['sha256']==INVENTORY_SHA256
 inv=load(HERE/'immutable_inventory.json')
 assert not any(p.is_symlink() for p in HERE.rglob('*'))
 for name,value in inv['files'].items():
  rel=Path(name); assert not rel.is_absolute() and '..' not in rel.parts
  assert pin(HERE/rel)==value,name
 actual={p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file()}
 assert actual==set(inv['files'])|{'immutable_inventory.json','manifest.json','reproduce.py'}
 seal=load(HERE/'ROOT_final_seal.json')
 assert pin(HERE/'ROOT_final_seal.json')['sha256']==SEAL_SHA256
 assert seal['id']==ID and seal['classification']=='unsupported_frozen_data'
 assert seal['subtype']=='Rel18_study_to_actual_TS_impact_type_role_requires_source_attribution'
 assert seal['criteria_sha256']=='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
 assert seal['two_nonblind_AI_semantic_judgments'] is True and seal['human_expert_n']==0
 assert seal['whole_original_question_verified_pass'] is False
 assert seal['source_grounded_partial_recovery'] is True and seal['complete_source_enriched_oracle_created'] is False
 case=HERE/'cases'/ID
 pairs=[
 ('contract/primary_seven_unit_review.json','primary_ROOT_review'),
 ('contract/secondary_seven_unit_review.json','independent_secondary_review'),
 ('provenance/secondary_actual_original_source_and_SQL_review_v1.json','independent_secondary_actual_source_and_SQL'),
 ('provenance/actual_ROOT_capture_receipt.json','ROOT_actual_source_capture'),
 ('provenance/actual_ROOT_Rel18_complete_roles_SQL_receipt_v2.json','ROOT_actual_original_SQL_replay'),
 ('source/actual_ROOT_original_release_covers_and_CR_source_role_v2.json','ROOT_actual_source_cover_roles'),
 ('provenance/actual_ROOT_generic_original_MATCH_OPTIONAL_replay_v1.json','ROOT_original_generic_optional_replay'),
 ('contract/bounded_source_role_contract.json','source_role_contract'),
 ('contract/counterauthority_and_alternate_recovery_decisions.json','counterauthority_and_alternate_recovery'),
 ('manifest.json','portable_manifest')]
 for name,key in pairs: assert pin(case/name)=={k:seal[key][k] for k in ['bytes','sha256']},key
 assert seal['primary_ROOT_review']['sha256']!=seal['independent_secondary_review']['sha256']
 assert pin(HERE/'actual_ROOT_final_portable_independent_relocated_replay.json')=={k:seal['ROOT_final_relocated_portable_replay'][k] for k in ['bytes','sha256']}
 controls_path=HERE/'actual_secondary_portable_relocation_and_controls_v1.json'
 assert pin(controls_path)=={k:seal['agent_actual_scientific_adverse_controls'][k] for k in ['bytes','sha256']}
 controls=load(controls_path)
 assert controls['status']=='PASS_ACTUAL_AGENT_LOCAL_RELOCATED_AND_NINE_SCIENTIFIC_ADVERSE_CONTROLS'
 assert controls['actual_scientific_control_n']==len(controls['scientific_adverse_controls'])==9
 assert controls['all_controls_reinventoried'] and controls['all_rejected_for_expected_semantic_invariant']
 assert controls['baseline_results_equal'] and controls['original_bundle_unchanged']
 assert controls['bundle']['manifest']==pin(case/'manifest.json')
 assert all(x['exit_code']!=0 and x['actual_rejection'] and x['reinventoried_payload'] and x['temporary_owned_tree_removed'] for x in controls['scientific_adverse_controls'])
 assert controls['actual_local_baseline']['exit_code']==controls['actual_relocated_baseline']['exit_code']==0
 assert controls['model_API_calls']==controls['native_calls']==controls['public_writes']==controls['queue_writes']==0
 proc=subprocess.run([sys.executable,'-B','-I','-S',str(case/'reproduce.py')],capture_output=True,text=True,stdin=subprocess.DEVNULL)
 assert proc.returncode==0,proc.stderr
 child=json.loads(proc.stdout)
 assert child['status']=='PASS' and child['id']==ID and child['classification']==seal['classification']
 assert child['retained_replay']['all_rows_and_fields_equal'] and child['source_grounded_positive_recovery_preserved']
 assert child['expert_validation_n']==child['human_review_n']==child['new_admissions']==child['model_API_calls']==child['new_native_calls']==child['public_writes']==0
 assert child['retained_replay']['complete_core_nodes']==367 and child['retained_replay']['records']==9634 and child['retained_replay']['edges']==12428
 print(json.dumps({'status':'PASS','cases':[{'id':ID,'classification':seal['classification'],'subtype':seal['subtype'],'child_result':child}],'new_admissions':0,'expert_validation_n':0,'model_API_calls':0,'new_native_calls':0},ensure_ascii=False))
if __name__=='__main__': main()

