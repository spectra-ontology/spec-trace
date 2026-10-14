#!/usr/bin/env python3
"""Spec: Execute saved generated queries for one ready authorized37 WG.
Ontology: Unmodified owned frozen graphs and immutable SQLite projections.
Cycle: Paid generation overlaps with separate read-only query execution.
배경: Finish ready methods without changing prompts, queries or score selection.
사용: .venv/bin/python execute_authorized37_ready_WG_guarded.py --wg RAN3
LLM 호출: None; executes saved model queries, no regeneration.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys

BASE = Path(__file__).resolve().parent
RUNTIME = BASE / 'authorized37_OpenRouter_release/evaluation/runtime'
RUN = BASE / 'authorized37_OpenRouter_release/evaluation/run'
BUNDLE = Path('/home/sihyeon/workspace/spectra-public/spec-trace-authorized37-20261015/release_package/cqs/original_core_overnight_repairs37')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wg', choices=['RAN1','RAN2','RAN3','RAN4','RAN5'], required=True)
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(RUNTIME))
    import authorized37_evaluation
    import execute_ready
    import capture_native
    authorized37_evaluation.verify(BUNDLE, RUN)
    copy = json.loads((RUNTIME/'early_execution_reader_copy_receipt.json').read_text())
    assert hashlib.sha256((RUNTIME/'execute_ready.py').read_bytes()).hexdigest() == copy['copy_sha256']
    with (BASE/'native_capture.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        capture_native.host_guard(RUN)
        active = subprocess.check_output(['docker','ps','--format','{{.Names}}'], text=True).splitlines()
        assert not any(name.startswith('kdd-db-') for name in active), 'Another owned audit container is active'
        resource.setrlimit(resource.RLIMIT_AS, (2*1024**3, 2*1024**3))
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
        execute_ready.execute_wg(BUNDLE, RUN, args.wg)
        capture_native.host_guard(RUN)


if __name__ == '__main__':
    main()
