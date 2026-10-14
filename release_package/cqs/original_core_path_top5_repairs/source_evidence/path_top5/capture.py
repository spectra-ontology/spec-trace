#!/usr/bin/env python3
"""Two complete read-only source queries on one owned RAN3 archival container."""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
PREP = BASE.parents[3]
sys.path.insert(0, str(PREP))
import execute_candidates as execution


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    proposal = json.loads((BASE / 'proposals.jsonl').read_text())
    witness_path = BASE.parent / 'path_top5_count_unit_invariance.json'
    witness = json.loads(witness_path.read_text())
    run = BASE / 'native'
    run.mkdir(exist_ok=True)
    (run / 'execution_inputs').mkdir(exist_ok=True)
    selected = [{'id': proposal['id'], 'wg': 'RAN3', 'candidate_query': proposal['reference_query'], 'status': 'pending'},
                {'id': proposal['id'] + '_COUNT_UNIT_WITNESS', 'wg': 'RAN3',
                 'candidate_query': witness['native_diagnostic_query'], 'status': 'pending'}]
    inputs = run / 'execution_inputs/RAN3.jsonl'
    inputs.write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in selected))
    protocol = json.loads((PREP / 'execution_protocol.json').read_text())
    protocol.update(scope='One pending original-question top5 repair and one full count-unit source witness; neither is an admission or model prediction',
                    selected_original_n=1, source_diagnostic_queries_n=1, max_concurrent_owned_WG_containers=1,
                    query_timeout_s=20, reference_row_limit=10000,
                    candidate_sha256=sha(BASE / 'proposals.jsonl'), source_witness_sha256=sha(witness_path),
                    capture_code_sha256=sha(Path(__file__)), execution_helper_sha256=sha(Path(execution.__file__)),
                    expert_validation_n=0, human_author_review_completed=False, new_model_calls=0)
    (run / 'execution_protocol.json').write_text(json.dumps(protocol, ensure_ascii=False, indent=2) + '\n')
    execution.BASE = run
    execution.TIMEOUT_SECONDS = 20
    execution.ROW_LIMIT = 10000
    sys.argv = [str(PREP / 'execute_candidates.py'), '--wg', 'RAN3', '--input', str(inputs)]
    execution.main()
    print(json.dumps({'status': 'NATIVE_CAPTURE_COMPLETED_NOT_ADMITTED', 'run': str(run),
                      'execution_sha256': sha(run / 'execution_RAN3.json')}), flush=True)


if __name__ == '__main__':
    main()
