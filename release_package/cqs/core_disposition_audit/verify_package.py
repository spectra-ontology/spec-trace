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
    rows,summary=build([HERE/'metric_classification_candidates.json',HERE/'missing_input_classification_candidates.json',HERE/'extent_classification_candidates.json'])
    stored=[json.loads(l) for l in (HERE/'partition/classification_overlay560.jsonl').open()]
    assert rows==stored
    assert summary==json.loads((HERE/'partition/summary.json').read_text())
    assert summary['partition_counts']=={'contract_verified':478,'clarification_required':11,'evidence_pending':71}
    print(json.dumps({'verification':'PASS','files_verified':len(manifest['files_SHA256']),
        'SQLite_and_independent_set_recounts':'MATCH','conditional_recent_meeting_extent':extent,'partition':summary,
        'new_admissions':0,'expert_validation_n':0},ensure_ascii=False))


if __name__=='__main__':main()
