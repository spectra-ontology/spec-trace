"""Verify package hashes, witness arithmetic, and the exhaustive partition."""
import hashlib
import json
from pathlib import Path
import sys

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
    assert summary['partition_counts']=={'contract_verified':verified_n,'clarification_required':14,'evidence_pending':560-verified_n-14}
    description=__import__('subprocess').run([sys.executable,str(HERE/'sources/conflicting_TR_description_evidence/reproduce.py')],capture_output=True,text=True,check=True)
    description_result=json.loads(description.stdout)
    assert description_result['cases_verified_n']==3 and description_result['root_secondary_seven_unit_reviews_verified_n']==3
    assert description_result['root_secondary_review_attached'] is True
    print(json.dumps({'verification':'PASS','files_verified':len(manifest['files_SHA256']),
        'SQLite_and_independent_set_recounts':'MATCH','conflicting_TR_description_check':description_result,'conditional_recent_meeting_extent':extent,'partition':summary,
        'new_admissions':0,'expert_validation_n':0},ensure_ascii=False))


if __name__=='__main__':main()
