#!/usr/bin/env python3
"""Require rejection of internally repinned corruptions in temporary copies."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    assert not args.receipt.exists()
    cases = [
        ('wrong_original_question_hash', 'contract/definition.json',
         lambda value: value.__setitem__('original_question_sha256', '0' * 64)),
        ('wrong_own_source_identity', 'source/actual_all38_original_own_cover_observations.json',
         lambda value: value['observations'][0].__setitem__('own_header_ids', ['R3-000000'])),
        ('missing_required_own_role', 'source/actual_all38_original_own_cover_observations.json',
         lambda value: value['observations'][0]['affected_roles'].pop()),
        ('wrong_actual_source_delta', 'proof/all_role_edge_diff.json',
         lambda value: value['added'][0].__setitem__('specNumber', '00.000')),
    ]
    results = []
    with tempfile.TemporaryDirectory(prefix='source-bundle-negative-') as temp:
        for name, relative, mutate in cases:
            directory = Path(temp) / name
            shutil.copytree(ROOT, directory)
            path = directory / relative
            value = json.loads(path.read_text())
            mutate(value)
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
            # Updating this internal manifest ensures semantic/binding gates,
            # rather than only checksum mismatch, are challenged.
            manifest_path = directory / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['artifacts'][relative] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                               'bytes': path.stat().st_size}
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
            completed = subprocess.run([sys.executable, '-B', '-I', str(directory / 'verify_portable.py')],
                                       text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            assert completed.returncode != 0, name
            results.append({'name': name, 'mutation_file': relative, 'internal_manifest_repinned': True,
                            'exit_code': completed.returncode, 'rejected': True,
                            'stdout': completed.stdout, 'stderr': completed.stderr})
    receipt = {'status': 'PASS', 'controls': results, 'original_bundle_unchanged': True,
               'human_expert_validation_n': 0, 'model_native_SQL_calls': 0, 'original_560_admissions': 0}
    args.receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': 'PASS', 'internally_repinned_corruptions_rejected': len(results)}))


if __name__ == '__main__':
    main()
