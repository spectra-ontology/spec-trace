#!/usr/bin/env python3
"""Verify retained-score portability using copied public inputs and no network.

This replays existing predictions, not model generation or full-corpus ranking.
It checks reproduction against the retained primary report, not semantic truth.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

BASE = Path(__file__).resolve().parent
FIXTURES = ('prospective_task_definitions_v2.json',
            'prospective_reference_gold_frozen_v2.json',
            'prospective_eligibility_v1.json', 'score_contract.py')
PRIMARY_SECTIONS = ('metrics', 'per_task', 'subgroups',
                    'paired_primary_contrasts', 'costs', 'all40_dispositions')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True,
                        help='New verification report; existing files are refused.')
    args = parser.parse_args()
    if args.out.exists():
        parser.error('Refusing to overwrite a verification report')
    original = json.loads((BASE / 'matched_measurement_report_v1.json').read_text())
    original_inputs = {name: sha(BASE.parent / name) for name in FIXTURES}
    track = BASE.parent.parent / 'spectra_cq_v2.0/splits/track_assignment.json'
    original_inputs['original_track_assignment'] = sha(track)
    with tempfile.TemporaryDirectory(prefix='spectra-public-replay-') as temp:
        root = Path(temp)
        public = root / 'cqs/contract_repair_v1'
        copied = public / BASE.name
        public.mkdir(parents=True)
        shutil.copytree(BASE, copied,
                        ignore=shutil.ignore_patterns('__pycache__', '.git', 'local_run'))
        for name in FIXTURES:
            shutil.copy2(BASE.parent / name, public / name)
        track_copy = root / 'cqs/spectra_cq_v2.0/splits/track_assignment.json'
        track_copy.parent.mkdir(parents=True)
        shutil.copy2(track, track_copy)
        assert not list(root.rglob('.git'))
        replay = root / 'replayed_primary.json'
        # Python isolation removes user/site and PYTHONPATH dependencies. A socket
        # guard prevents the replay from contacting any model/database service.
        wrapper = ('import runpy,socket,sys; '
                   'deny=lambda *a,**k: (_ for _ in ()).throw(RuntimeError("Network disabled for retained replay")); '
                   'socket.socket=deny; socket.create_connection=deny; socket.getaddrinfo=deny; '
                   'sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0],run_name="__main__")')
        command = [sys.executable, '-I', '-B', '-c', wrapper,
                   str(copied / 'matched_analysis.py'), '--require-complete', '--out', str(replay)]
        environment = {key: os.environ[key] for key in ('PATH', 'LANG', 'LC_ALL', 'TMPDIR')
                       if key in os.environ}
        process = subprocess.run(command, cwd=root, env=environment,
                                 capture_output=True, text=True, timeout=120)
        if process.returncode != 0:
            raise SystemExit('Isolated retained replay failed; no verification report written')
        reproduced = json.loads(replay.read_text())
        checks = {section: reproduced[section] == original[section]
                  for section in PRIMARY_SECTIONS}
        checks.update(fixed_36_tasks=reproduced['fixed_eligible_tasks'] == 36,
                      three_arms=reproduced['arms'] == ['single', 'iterative', 'structured'],
                      retained_108_predictions=sum(len(rows) for rows in reproduced['per_task'].values()) == 108,
                      retained_144_calls=reproduced['costs']['overall_ledger']['completed_caller_attempts'] == 144,
                      paired_6_intervals=len(reproduced['paired_primary_contrasts']) == 6,
                      no_git_directory=not list(root.rglob('.git')))
        if not all(checks.values()):
            raise SystemExit('Retained primary reproduction differed; no verification report written')
        proof = {'kind': 'isolated no-model retained public replay verification',
                 'status': 'PASS', 'checks': checks,
                 'process_returncode': process.returncode,
                 'python_version': sys.version.split()[0],
                 'input_sha256': original_inputs,
                 'analysis_code_sha256': sha(BASE / 'matched_analysis.py'),
                 'verification_code_sha256': sha(__file__),
                 'retained_primary_report_sha256': sha(BASE / 'matched_measurement_report_v1.json'),
                 'reproduced_report_sha256': sha(replay),
                 'execution': {'copied_public_inputs_only': True, 'python_isolation_flag': '-I',
                               'git_metadata_present': False, 'network_socket_calls_blocked': True,
                               'model_generation': False, 'corpus_ranking': False,
                               'database_calls': False},
                 'limits': ['Checks retained numerical reproduction, not task semantics or expert truth.',
                            'Does not reproduce generation, provider backend, or unpublished full-corpus rankings.',
                            'Published path and metadata transformations cause input/report hashes to differ from private originals.']}
        with args.out.open('x') as stream:
            json.dump(proof, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
        print(json.dumps({'status': 'PASS', 'verification_report_sha256': sha(args.out)}))


if __name__ == '__main__':
    main()
