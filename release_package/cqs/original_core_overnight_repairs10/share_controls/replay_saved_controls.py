"""Portable replay: no research database, graph, credentials, network or model."""
from decimal import Decimal
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    assert not args.out.exists(), 'preserve previous receipts'
    base = Path(__file__).resolve().parent
    manifest = json.loads((base / 'manifest.json').read_text())
    for relative, expected in manifest['files'].items():
        path = base / relative
        assert path.is_file() and sha(path) == expected['sha256'] and path.stat().st_size == expected['bytes'], relative
    sys.path[:0] = [str(base / 'proposal/bundle_scorer'), str(base / 'proposal/runtime')]
    import original_scorer
    import share_runtime_adapter as adapter
    import rational_share_records as codec
    task = json.loads((base / 'task.json').read_text())
    gold = json.loads((base / 'gold.json').read_text())
    assert task['repair_sha256'] == manifest['repair_sha256']
    field = task['required_fields'][0]['name']
    results = []
    for filename, expected_n in [('source_actual20.json', 20), ('root_actual24.json', 24)]:
        saved = json.loads((base / filename).read_text())
        assert saved['repair_sha256'] == task['repair_sha256']
        assert saved['canonical_reference_records'] == gold
        assert saved['controls_n'] == len(saved['controls']) == expected_n
        replayed = []
        for control in saved['controls']:
            if 'prediction' in control:
                actual = adapter.score(task, gold, control['prediction'], original_scorer.score, diagnostic=True)
                assert actual == control['actual'], (control['name'], actual, control['actual'])
                assert actual['exact'] is control['expected_exact']
            else:
                assert control['name'] == 'actual_task_raw_decimal_lexical_information_preserved'
                text = '{"records":[{"' + field + '":0.100000000000000005}],"abstain":false,"complete":true}'
                parsed = codec.parse_retrieval_answer(task, text, json.loads)
                assert parsed['records'][0][field] == codec.rational(Decimal('0.100000000000000005'))
                assert parsed['records'][0][field] != codec.rational(Decimal('0.1'))
            replayed.append({'name': control['name'], 'pass': True})
        results.append({'source': filename, 'controls_n': len(replayed), 'controls': replayed})
    with tempfile.TemporaryDirectory(prefix='auth10-portable-source-free-') as temporary:
        fixture = Path(temporary)
        # Root-discovery fixture only: no Git command, repository or credentials.
        (fixture / '.git').mkdir()
        proposal = fixture / 'proposal'
        shutil.copytree(base / 'proposal', proposal)
        out = fixture / 'source_free25.json'
        execution = subprocess.run([sys.executable, '-B', '-S', str(base / 'verify_source_free_runtime25.py'),
            '--proposal', str(proposal), '--out', str(out)], capture_output=True, text=True,
            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        assert execution.returncode == 0, execution.stdout + execution.stderr
        source_free = json.loads(out.read_text())
        original = json.loads((base / 'source_free_actual25.json').read_text())
        assert source_free == original
        assert source_free['tests_n'] == len(source_free['tests']) == 25
    result = {'status': 'PASS_PORTABLE_EXACT_SHARE_SAVED20_SAVED24_AND_SOURCE_FREE25',
        'manifest_sha256': sha(base / 'manifest.json'),
        'id': task['id'], 'repair_sha256': task['repair_sha256'],
        'saved_control_replays': results, 'source_free_runtime': source_free,
        'overlapping_control_sets_not_independent': True,
        'research_database_native_API_network_operations': 0,
        'temporary_synthetic_SQLite_only': True}
    with args.out.open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')
    print(json.dumps({'status': result['status'], 'receipt_sha256': sha(args.out),
        'saved_counts': [item['controls_n'] for item in results], 'source_free_n': source_free['tests_n']}))


if __name__ == '__main__':
    main()
