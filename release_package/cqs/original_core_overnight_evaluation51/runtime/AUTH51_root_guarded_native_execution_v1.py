#!/usr/bin/env python3
"""Spec: Execute saved generated queries for one ready authorized_incremental51 WG.
Ontology: Unmodified owned frozen graphs and immutable SQLite projections.
Cycle: Paid generation overlaps with separate read-only query execution.
배경: Finish ready methods without changing prompts, queries or score selection.
사용: .venv/bin/python execute_authorized_incremental51_ready_WG_guarded.py --wg RAN1
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

if sys.flags.optimize:
    raise SystemExit('Run without -O/-OO; native safety assertions must remain enabled.')

BASE = next(p for p in Path(__file__).resolve().parents if p.name == 'overnight_reaudit')
RUNTIME = BASE / 'authorized_incremental51_OpenRouter_release/evaluation/runtime'
RUN = BASE / 'authorized_incremental51_OpenRouter_release/evaluation/first_trial'
BUNDLE = Path('/home/sihyeon/workspace/spectra/logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit/root_evidence/two_agent_unresolved_loop/adjudication62/resumed_deep_verification/sequential_two_main/local_only41/main_C/RAN1_P5_CQ3-3/AUTH51_preparation/portable_addition_v1/release_package/cqs/original_core_overnight_repairs51')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wg', choices=['RAN1'], required=True)
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(RUNTIME), str(BASE)]
    import authorized_incremental51_evaluation
    import execute_ready
    import capture_native
    inherited_host_guard = capture_native.host_guard
    def host_guard_with_26GiB_admission(output):
        inherited_host_guard(output)
        row = json.loads((output/'resource_checks.jsonl').read_text().splitlines()[-1])
        assert min(row['linux_available_bytes'], row['windows_available_bytes']) >= 26*1024**3, 'Preserve 26GiB host admission for owned native execution'
    capture_native.host_guard = host_guard_with_26GiB_admission
    authorized_incremental51_evaluation.verify(BUNDLE, RUN)
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
