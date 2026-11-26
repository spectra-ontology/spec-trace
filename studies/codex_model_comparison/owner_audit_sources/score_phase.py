"""Run each committed native-query batch once; retain process receipts."""
import datetime
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
phase = sys.argv[1]
assert phase in {'A', 'B'}
schedule = json.loads((HERE / 'schedule.json').read_text())
deviations = {r['runId']: r for r in json.loads((HERE / 'first_write_deviations.json').read_text())['runs']} if (HERE / 'first_write_deviations.json').exists() else {}
runs = [r for r in schedule if r['repetition'] == phase]
assert len(runs) == 16
assert all((HERE / 'submissions' / r['runId'] / 'commitment.json').is_file() for r in runs)
receipts = HERE / 'execution_receipts'
receipts.mkdir(exist_ok=True)
for run in runs:
    run_id = run['runId']
    receipt_path = receipts / (run_id + '.json')
    if receipt_path.exists():
        prior = json.loads(receipt_path.read_text())
        assert prior['exitCode'] == 0, 'Inspect a failed execution before any continuation'
        continue
    assert not (HERE / 'execution' / run_id).exists(), 'Preserve an existing execution'
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    commitment = json.loads((HERE / 'submissions' / run_id / 'commitment.json').read_text())
    if commitment['status'] == 'invalid_first_submission' or run_id in deviations:
        # The frozen protocol already assigns unanswered credit to missing
        # queries. Preserve the invalid raw batch; never invent executable text.
        if run_id in deviations:
            deviation = deviations[run_id]
            assert deviation['firstWriteJsonValid'] is False
            try:
                json.loads((HERE / deviation['firstWritePath']).read_text())
            except json.JSONDecodeError:
                pass
            else:
                raise AssertionError('Expected the independently recovered malformed first batch')
        else:
            raw = json.loads((HERE / 'submissions' / run_id / 'response.raw').read_text())
            assert raw == {'queries': []}, 'Partial batches require an explicit item-level audit'
        receipt_path.write_text(json.dumps({'runId': run_id, 'startedAtUtc': started,
            'exitCode': 0, 'status': 'missing_first_queries', 'nativeQueriesExecuted': 0,
            'unansweredItems': 50, 'source': 'Frozen protocol generation.firstSubmission; no query replacements.'}, indent=2)+'\n')
        print(json.dumps({'runId': run_id, 'status': 'missing_first_queries', 'nativeQueriesExecuted': 0}), flush=True)
        continue
    command = [sys.executable, '-B', str(HERE / 'harness.py'), 'score', '--run-id', run_id]
    result = subprocess.run(command, capture_output=True, text=True)
    receipt = {'runId': run_id, 'startedAtUtc': started,
               'endedAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'command': command, 'exitCode': result.returncode,
               'stdout': result.stdout, 'stderr': result.stderr}
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'runId': run_id, 'exitCode': result.returncode}), flush=True)
    assert result.returncode == 0, 'Native execution failed; retain receipt and investigate'
