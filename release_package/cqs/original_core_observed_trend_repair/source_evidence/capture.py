"""Complete read-only counts and source membership on one owned WG at a time."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
PREP = BASE.parents[3]
sys.path.insert(0, str(PREP))
import execute_candidates as execution


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--wg', choices=['RAN3', 'RAN4'], required=True)
    args = parser.parse_args()
    proposals = [json.loads(line) for line in (BASE / 'proposals.jsonl').read_text().splitlines()]
    proposal = next(r for r in proposals if r['id'].startswith(args.wg + '_'))
    agenda = '8.1' if args.wg == 'RAN3' else '6.6.3'
    diagnostic = f"""MATCH (m:Meeting)
OPTIONAL MATCH (r:Resolution)-[:MADE_AT]->(m)
WHERE EXISTS {{ MATCH (r)-[:RESOLUTION_BELONGS_TO]->(:AgendaItem {{agendaNumber: '{agenda}'}}) }}
RETURN m.canonicalMeetingNumber AS meetingNumber, m.meetingNumberInt AS meetingOrdinal,
       collect(DISTINCT r.resolutionId) AS resolutionIds
ORDER BY meetingOrdinal ASC"""
    run = BASE / 'native'
    run.mkdir(exist_ok=True)
    (run / 'execution_inputs').mkdir(exist_ok=True)
    rows = [{'id': proposal['id'], 'wg': args.wg, 'candidate_query': proposal['reference_query'], 'status': 'pending'},
            {'id': proposal['id'] + '_FULL_MEMBERSHIP', 'wg': args.wg, 'candidate_query': diagnostic, 'status': 'pending'}]
    inputs = run / 'execution_inputs' / (args.wg + '.jsonl')
    inputs.write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in rows))
    protocol_path = run / 'execution_protocol.json'
    protocol = json.loads((PREP / 'execution_protocol.json').read_text())
    protocol.update(scope='Two pending original count-trend candidates; complete native counts and complete Resolution identity membership; no model output or admission',
                    selected_original_n=2, source_diagnostic_queries_n=2, max_concurrent_owned_WG_containers=1,
                    owned_container_memory_bytes=2 * 1024 ** 3, owned_container_cpus=1,
                    query_timeout_s=20, reference_row_limit=10000,
                    candidate_sha256=sha(BASE / 'proposals.jsonl'),
                    source_witness_sha256=sha(BASE.parent / 'trend_scope_source_probe.json'),
                    capture_code_sha256=sha(Path(__file__)), execution_helper_sha256=sha(Path(execution.__file__)),
                    expert_validation_n=0, human_author_review_completed=False, new_model_calls=0)
    payload = json.dumps(protocol, ensure_ascii=False, indent=2) + '\n'
    if protocol_path.exists():
        assert protocol_path.read_text() == payload
    else:
        protocol_path.write_text(payload)
    execution.BASE = run
    execution.TIMEOUT_SECONDS = 20
    execution.ROW_LIMIT = 10000
    sys.argv = [str(PREP / 'execute_candidates.py'), '--wg', args.wg, '--input', str(inputs)]
    execution.main()
    print(json.dumps({'status': 'NATIVE_CAPTURE_COMPLETE_NOT_ADMITTED', 'wg': args.wg,
                      'run': str(run), 'execution_sha256': sha(run / ('execution_' + args.wg + '.json'))}), flush=True)


if __name__ == '__main__':
    main()
