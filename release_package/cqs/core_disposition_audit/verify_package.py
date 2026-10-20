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
    assert summary['partition_counts']=={'contract_verified':verified_n,'clarification_required':18,'unsupported_frozen_data':8,'evidence_pending':560-verified_n-18-8}
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
    actual_candidates=json.loads((HERE/'unsupported_classification_candidates.json').read_text())['cases'][4:]
    inventory_sha=hashlib.sha256((HERE/'sources/additional_frozen_source_loss_evidence/immutable_inventory.json').read_bytes()).hexdigest()
    for actual_candidate,expected_candidate in zip(actual_candidates,expected_candidates):
        candidate_copy=__import__('copy').deepcopy(actual_candidate)
        assert candidate_copy['evidence'].pop('inventory_sha256')==inventory_sha
        assert candidate_copy==expected_candidate
    assert len(actual_candidates)==len(expected_candidates)==4
    print(json.dumps({'verification':'PASS','files_verified':len(manifest['files_SHA256']),
        'SQLite_and_independent_set_recounts':'MATCH','conflicting_TR_description_check':description_result,'conflicting_agenda_description_check':agenda_result,'conflicting_pack_scope_check':pack_result,'conflicting_source_availability_check':availability_result,'bounded_frozen_source_loss_checks':source_loss_results,'conditional_recent_meeting_extent':extent,'partition':summary,
        'new_admissions':0,'expert_validation_n':0},ensure_ascii=False))


if __name__=='__main__':main()
