"""Verify package hashes, witness arithmetic, and the exhaustive partition."""
import hashlib
import json
from pathlib import Path
import sys

if sys.flags.optimize != 0:
    raise SystemExit("Verification requires assertions; Python -O and -OO are refused.")

sys.dont_write_bytecode=True
from reproduce import reproduce
from build_partition import build
from reproduce_extent import reproduce_extent

HERE=Path(__file__).resolve().parent


def main():
    manifest=json.loads((HERE/'manifest.json').read_text())
    for name,expected in manifest['files_SHA256'].items():
        assert '__pycache__' not in Path(name).parts and Path(name).suffix not in ('.pyc','.pyo'),name
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==expected,name
    actual=reproduce()
    assert actual==json.loads((HERE/'diagnostic_results.json').read_text())
    extent=reproduce_extent()
    rows,summary=build()
    stored=[json.loads(l) for l in (HERE/'partition/classification_overlay560.jsonl').open()]
    assert rows==stored
    assert summary==json.loads((HERE/'partition/summary.json').read_text())
    baseline=[json.loads(line) for line in (HERE/'baseline560_metadata.jsonl').open()]
    verified_n=sum(row['immutable_public_status']=='pass' for row in baseline)
    assert summary['partition_counts']=={'contract_verified':verified_n,'clarification_required':21,'unsupported_frozen_data':14,'evidence_pending':560-verified_n-21-14}
    description=__import__('subprocess').run([sys.executable,str(HERE/'sources/conflicting_TR_description_evidence/reproduce.py')],capture_output=True,text=True,check=True)
    description_result=json.loads(description.stdout)
    assert description_result['cases_verified_n']==3 and description_result['root_secondary_seven_unit_reviews_verified_n']==3
    assert description_result['root_secondary_review_attached'] is True
    agenda=__import__('subprocess').run([sys.executable,'-B','-I','-S',str(HERE/'sources/conflicting_agenda_description_evidence/verify_evidence.py')],capture_output=True,text=True,check=True)
    agenda_result=json.loads(agenda.stdout)
    assert agenda_result['status']=='PASS' and agenda_result['classification_is_conditional'] is True
    assert agenda_result['root_secondary_seven_unit_reviews_verified_n']==1 and agenda_result['new_admissions']==0
    pack=__import__('subprocess').run([sys.executable,'-B','-I','-S',str(HERE/'sources/conflicting_pack_scope_evidence/verify_evidence.py')],capture_output=True,text=True,check=True)
    pack_result=json.loads(pack.stdout)
    assert pack_result['status']=='PASS' and pack_result['classification']=='clarification_required' and pack_result['new_admissions']==0
    availability=__import__('subprocess').run([sys.executable,'-B','-I','-S',str(HERE/'sources/conflicting_source_availability_evidence/verify_evidence.py')],capture_output=True,text=True,check=True)
    availability_result=json.loads(availability.stdout)
    assert availability_result['status']=='PASS' and len(availability_result['cases'])==2 and availability_result['new_admissions']==0
    source_loss_results=[]
    for package in ['agreement_source_loss_evidence','structural_source_loss_evidence']:
        completed=__import__('subprocess').run([sys.executable,'-B','-I','-S',str(HERE/'sources'/package/'reproduce.py')],capture_output=True,text=True,check=True)
        evidence_result=json.loads(completed.stdout)
        assert evidence_result['status']=='PASS' and len(evidence_result['cases'])==2 and evidence_result['new_admissions']==0
        source_loss_results.append(evidence_result)
    additional=__import__('subprocess').run([sys.executable,'-B','-I','-S',str(HERE/'sources/additional_frozen_source_loss_evidence/reproduce.py')],capture_output=True,text=True,check=True)
    additional_result=json.loads(additional.stdout)
    assert additional_result['status']=='PASS' and len(additional_result['cases'])==4 and additional_result['new_admissions']==0
    source_loss_results.append(additional_result)
    expected_candidates=json.loads((HERE/'sources/additional_frozen_source_loss_evidence/classification_candidate_records.json').read_text())
    actual_candidates=json.loads((HERE/'unsupported_classification_candidates.json').read_text())['cases'][4:8]
    inventory_sha=hashlib.sha256((HERE/'sources/additional_frozen_source_loss_evidence/immutable_inventory.json').read_bytes()).hexdigest()
    for actual_candidate,expected_candidate in zip(actual_candidates,expected_candidates):
        candidate_copy=__import__('copy').deepcopy(actual_candidate)
        assert candidate_copy['evidence'].pop('inventory_sha256')==inventory_sha
        assert candidate_copy==expected_candidate
    assert len(actual_candidates)==len(expected_candidates)==4
    uci=__import__('subprocess').run([sys.executable,'-B','-I','-S',str(HERE/'sources/UCI_source_amendment_status_evidence/reproduce.py')],capture_output=True,text=True,check=True)
    uci_result=json.loads(uci.stdout)
    assert uci_result['status']=='PASS' and len(uci_result['cases'])==1 and uci_result['new_admissions']==0
    source_loss_results.append(uci_result)
    uci_expected=json.loads((HERE/'sources/UCI_source_amendment_status_evidence/classification_candidate_records.json').read_text())
    uci_actual=json.loads((HERE/'unsupported_classification_candidates.json').read_text())['cases'][8:9]
    assert len(uci_actual)==len(uci_expected)==1
    uci_candidate=__import__('copy').deepcopy(uci_actual[0])
    assert uci_candidate['evidence'].pop('inventory_sha256')==hashlib.sha256((HERE/'sources/UCI_source_amendment_status_evidence/immutable_inventory.json').read_bytes()).hexdigest()
    assert uci_candidate==uci_expected[0]
    completed_classifications=[]
    sealed=__import__('subprocess').run([sys.executable,'-B','-I','-S',str(HERE/'sources/DCI_source_amendment_status_evidence'/'reproduce.py')],capture_output=True,text=True,check=True)
    sealed_result=json.loads(sealed.stdout)
    assert sealed_result['status']=='PASS' and len(sealed_result['cases'])==1 and sealed_result['new_admissions']==0
    completed_classifications.append(sealed_result)
    expected_sealed=json.loads((HERE/'sources/DCI_source_amendment_status_evidence'/'classification_candidate_records.json').read_text())
    actual_sealed=json.loads((HERE/'unsupported_classification_candidates.json').read_text())['cases'][9:10]
    assert len(actual_sealed)==len(expected_sealed)==1
    candidate_copy=__import__('copy').deepcopy(actual_sealed[0])
    assert candidate_copy['evidence'].pop('inventory_sha256')==hashlib.sha256((HERE/'sources/DCI_source_amendment_status_evidence'/'immutable_inventory.json').read_bytes()).hexdigest()
    assert candidate_copy==expected_sealed[0]
    sealed=__import__('subprocess').run([sys.executable,'-B','-I','-S',str(HERE/'sources/cross_meeting_agenda_scope_evidence'/'reproduce.py')],capture_output=True,text=True,check=True)
    sealed_result=json.loads(sealed.stdout)
    assert sealed_result['status']=='PASS' and len(sealed_result['cases'])==1 and sealed_result['new_admissions']==0
    completed_classifications.append(sealed_result)
    expected_sealed=json.loads((HERE/'sources/cross_meeting_agenda_scope_evidence'/'classification_candidate_records.json').read_text())
    actual_sealed=json.loads((HERE/'completed_scope_classification_candidates.json').read_text())['cases'][3:4]
    assert len(actual_sealed)==len(expected_sealed)==1
    candidate_copy=__import__('copy').deepcopy(actual_sealed[0])
    assert candidate_copy['evidence'].pop('inventory_sha256')==hashlib.sha256((HERE/'sources/cross_meeting_agenda_scope_evidence'/'immutable_inventory.json').read_bytes()).hexdigest()
    assert candidate_copy==expected_sealed[0]
    sealed=__import__('subprocess').run([sys.executable,'-B','-I','-S',str(HERE/'sources/FL_summary_agenda_scope_evidence'/'reproduce.py')],capture_output=True,text=True,check=True)
    sealed_result=json.loads(sealed.stdout)
    assert sealed_result['status']=='PASS' and len(sealed_result['cases'])==1 and sealed_result['new_admissions']==0
    completed_classifications.append(sealed_result)
    expected_sealed=json.loads((HERE/'sources/FL_summary_agenda_scope_evidence'/'classification_candidate_records.json').read_text())
    actual_sealed=json.loads((HERE/'completed_scope_classification_candidates.json').read_text())['cases'][4:5]
    assert len(actual_sealed)==len(expected_sealed)==1
    candidate_copy=__import__('copy').deepcopy(actual_sealed[0])
    assert candidate_copy['evidence'].pop('inventory_sha256')==hashlib.sha256((HERE/'sources/FL_summary_agenda_scope_evidence'/'immutable_inventory.json').read_bytes()).hexdigest()
    assert candidate_copy==expected_sealed[0]
    sealed=__import__('subprocess').run([sys.executable,'-B','-I','-S',str(HERE/'sources/CSI_RS_amendment_status_evidence'/'reproduce.py')],capture_output=True,text=True,check=True)
    sealed_result=json.loads(sealed.stdout)
    assert sealed_result['status']=='PASS' and len(sealed_result['cases'])==1 and sealed_result['new_admissions']==0
    completed_classifications.append(sealed_result)
    expected_sealed=json.loads((HERE/'sources/CSI_RS_amendment_status_evidence'/'classification_candidate_records.json').read_text())
    actual_sealed=json.loads((HERE/'unsupported_classification_candidates.json').read_text())['cases'][10:11]
    assert len(actual_sealed)==len(expected_sealed)==1
    candidate_copy=__import__('copy').deepcopy(actual_sealed[0])
    assert candidate_copy['evidence'].pop('inventory_sha256')==hashlib.sha256((HERE/'sources/CSI_RS_amendment_status_evidence'/'immutable_inventory.json').read_bytes()).hexdigest()
    assert candidate_copy==expected_sealed[0]
    sealed=__import__('subprocess').run([sys.executable,'-B','-I','-S',str(HERE/'sources/work_item_Spec_selection_evidence'/'reproduce.py')],capture_output=True,text=True,check=True)
    sealed_result=json.loads(sealed.stdout)
    assert sealed_result['status']=='PASS' and len(sealed_result['cases'])==1 and sealed_result['new_admissions']==0
    completed_classifications.append(sealed_result)
    expected_sealed=json.loads((HERE/'sources/work_item_Spec_selection_evidence'/'classification_candidate_records.json').read_text())
    actual_sealed=json.loads((HERE/'completed_scope_classification_candidates.json').read_text())['cases'][5:6]
    assert len(actual_sealed)==len(expected_sealed)==1
    candidate_copy=__import__('copy').deepcopy(actual_sealed[0])
    assert candidate_copy['evidence'].pop('inventory_sha256')==hashlib.sha256((HERE/'sources/work_item_Spec_selection_evidence'/'immutable_inventory.json').read_bytes()).hexdigest()
    assert candidate_copy==expected_sealed[0]
    sealed=__import__('subprocess').run([sys.executable,'-B','-I','-S',str(HERE/'sources/RAN4_approval_target_binding_evidence'/'reproduce.py')],capture_output=True,text=True,check=True)
    sealed_result=json.loads(sealed.stdout)
    assert sealed_result['status']=='PASS' and len(sealed_result['cases'])==1 and sealed_result['new_admissions']==0
    completed_classifications.append(sealed_result)
    expected_sealed=json.loads((HERE/'sources/RAN4_approval_target_binding_evidence'/'classification_candidate_records.json').read_text())
    actual_sealed=json.loads((HERE/'unsupported_classification_candidates.json').read_text())['cases'][11:12]
    assert len(actual_sealed)==len(expected_sealed)==1
    candidate_copy=__import__('copy').deepcopy(actual_sealed[0])
    assert candidate_copy['evidence'].pop('inventory_sha256')==hashlib.sha256((HERE/'sources/RAN4_approval_target_binding_evidence'/'immutable_inventory.json').read_bytes()).hexdigest()
    assert candidate_copy==expected_sealed[0]
    sealed=__import__('subprocess').run([sys.executable,'-B','-I','-S',str(HERE/'sources/NRU_new_section_role_evidence'/'reproduce.py')],capture_output=True,text=True,check=True)
    sealed_result=json.loads(sealed.stdout)
    assert sealed_result['status']=='PASS' and len(sealed_result['cases'])==1 and sealed_result['new_admissions']==0
    completed_classifications.append(sealed_result)
    expected_sealed=json.loads((HERE/'sources/NRU_new_section_role_evidence'/'classification_candidate_records.json').read_text())
    actual_sealed=json.loads((HERE/'unsupported_classification_candidates.json').read_text())['cases'][12:13]
    assert len(actual_sealed)==len(expected_sealed)==1
    candidate_copy=__import__('copy').deepcopy(actual_sealed[0])
    assert candidate_copy['evidence'].pop('inventory_sha256')==hashlib.sha256((HERE/'sources/NRU_new_section_role_evidence'/'immutable_inventory.json').read_bytes()).hexdigest()
    assert candidate_copy==expected_sealed[0]
    sealed=__import__('subprocess').run([sys.executable,'-B','-I','-S',str(HERE/'sources/TR_inverse_impact_history_evidence'/'reproduce.py')],capture_output=True,text=True,check=True)
    sealed_result=json.loads(sealed.stdout)
    assert sealed_result['status']=='PASS' and len(sealed_result['cases'])==1 and sealed_result['new_admissions']==0
    completed_classifications.append(sealed_result)
    expected_sealed=json.loads((HERE/'sources/TR_inverse_impact_history_evidence'/'classification_candidate_records.json').read_text())
    actual_sealed=json.loads((HERE/'unsupported_classification_candidates.json').read_text())['cases'][13:14]
    assert len(actual_sealed)==len(expected_sealed)==1
    candidate_copy=__import__('copy').deepcopy(actual_sealed[0])
    assert candidate_copy['evidence'].pop('inventory_sha256')==hashlib.sha256((HERE/'sources/TR_inverse_impact_history_evidence'/'immutable_inventory.json').read_bytes()).hexdigest()
    assert candidate_copy==expected_sealed[0]
    print(json.dumps({'verification':'PASS','files_verified':len(manifest['files_SHA256']),
        'SQLite_and_independent_set_recounts':'MATCH','conflicting_TR_description_check':description_result,'conflicting_agenda_description_check':agenda_result,'conflicting_pack_scope_check':pack_result,'conflicting_source_availability_check':availability_result,'bounded_frozen_source_loss_checks':source_loss_results,'completed_sealed_classification_checks':completed_classifications,'conditional_recent_meeting_extent':extent,'partition':summary,
        'new_admissions':0,'expert_validation_n':0},ensure_ascii=False))


if __name__=='__main__':main()
