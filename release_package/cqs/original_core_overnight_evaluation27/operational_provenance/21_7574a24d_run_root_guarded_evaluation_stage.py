"""Run one frozen evaluation stage with dual-host reserve and owned cleanup."""
import argparse
import sys
if sys.flags.optimize:
    raise SystemExit('Run with assertions enabled; -O/-OO refused')
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

HERE = Path(__file__).resolve().parent
B = next(p for p in HERE.parents if p.name == 'overnight_reaudit')
A = B / 'authorized_incremental27_OpenRouter_release'
GIB = 1024 ** 3
SCOPE = '21336cfc1353afa976746178c462385cafcb7a45a238757cb9a7b6c4530d4fd5'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def memory():
    linux = int(next(s.split()[1] for s in Path('/proc/meminfo').read_text().splitlines()
                     if s.startswith('MemAvailable:'))) * 1024
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
                             '(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory'],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0 and re.fullmatch(r'\d+', result.stdout.strip())
    return linux, int(result.stdout.strip()) * 1024


def ownership_helper():
    path = B / 'root_evidence/two_agent_unresolved_loop/root_CQ045_original_contract_source_review/run_guarded_exact_native_infrastructure_retry.py'
    spec = importlib.util.spec_from_file_location('cq045_exact_owned_cleanup', path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['generate', 'analyze'])
    args = parser.parse_args()
    assert sha(A / 'scope.json') == SCOPE
    out = HERE / ('actual_guarded_first_' + args.stage)
    assert not out.exists(), 'Preserve previous attempts'
    out.mkdir()
    controller = A / 'evaluation/runtime/authorized_incremental27_evaluation.py'
    cmd = ['/usr/bin/python3', '-B', str(controller), args.stage,
           '--bundle', '/home/sihyeon/workspace/spectra/logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit/root_evidence/two_agent_unresolved_loop/adjudication62/resumed_deep_verification/sequential_two_main/portable_three_v1/release_package/cqs/original_core_overnight_repairs27', '--run-dir', str(A / 'evaluation/first_trial')]
    assert controller.is_file(), 'Controller path must exist before child starts'
    began = time.monotonic()
    child, failure, code, initial, cleanup = None, None, None, None, None
    samples = []
    helper = None  # This guard controls generation/analysis only; native execution has its separate scheduler.
    try:
        linux, windows = memory()
        initial = {'Linux_available_bytes': linux, 'Windows_available_bytes': windows}
        assert min(linux, windows) >= 26 * GIB, initial
        if helper:
            helper.inspect_owned(False)
            assert not any(n.startswith('kdd-db-') for n in helper.command('docker', 'ps', '--format', '{{.Names}}').splitlines())
        with (out / 'stdout').open('x') as stdout, (out / 'stderr').open('x') as stderr:
            child = subprocess.Popen(cmd, stdout=stdout, stderr=stderr, start_new_session=True)
            last_windows = time.monotonic()
            print(json.dumps({'stage': args.stage, 'status': 'STARTED', 'pid': child.pid, 'initial_memory': initial}), flush=True)
            while child.poll() is None:
                linux = int(next(s.split()[1] for s in Path('/proc/meminfo').read_text().splitlines()
                                 if s.startswith('MemAvailable:'))) * 1024
                if time.monotonic() - last_windows >= 10:
                    _, windows = memory()
                    last_windows = time.monotonic()
                samples.append({'elapsed_seconds': time.monotonic() - began,
                                'Linux_available_bytes': linux, 'Windows_available_bytes': windows})
                assert min(linux, windows) >= 16 * GIB, 'Continuous host reserve violated'
                time.sleep(2)
            code = child.wait()
            assert code == 0, 'Preserve failed stage and outputs'
        assert sha(A / 'scope.json') == SCOPE
    except BaseException as exc:
        failure = {'type': type(exc).__name__, 'message': str(exc)[:2000]}
    finally:
        if child is not None and child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=30)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
        if child is not None:
            code = child.poll()
        if helper and child is not None:
            try:
                with (B / 'native_capture.lock').open('a') as lock:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    raw = json.loads(helper.command('docker', 'inspect', helper.NAME))[0]
                    running = raw['State']['Running']
                    assert type(running) is bool
                    helper.inspect_owned(running)
                    if running:
                        helper.command('docker', 'stop', '--time', '20', helper.NAME)
                    helper.inspect_owned(False)
                    cleanup = {'owned_stopped': True, 'fallback_stop': running, 'common_lock_held': True}
            except BaseException as exc:
                failure = failure or {'type': type(exc).__name__, 'message': str(exc)[:2000]}
                cleanup = {'status': 'OWNERSHIP_OR_CLEANUP_FAILURE_PRESERVED'}
        receipt = {'status': 'PASS' if failure is None else 'FAIL_PRESERVED',
                   'stage': args.stage, 'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   'argv': cmd, 'wrapper_sha256': sha(Path(__file__)), 'scope_sha256': SCOPE,
                   'child_started': child is not None, 'child_exit': code, 'failure': failure,
                   'prestart_available_minimum_bytes': 26 * GIB, 'continuous_reserve_minimum_bytes': 16 * GIB,
                   'Linux_check_seconds': 2, 'Windows_check_seconds': 10, 'Windows_probe_timeout_seconds': 20,
                   'sampling_limitation': 'Windows probe duration can extend its nominal sampling interval.',
                   'initial_memory': initial, 'memory_samples': samples, 'owned_cleanup': cleanup,
                   'quality_rerolls': 0, 'elapsed_seconds': time.monotonic() - began}
        with (out / 'receipt.json').open('x') as stream:
            stream.write(json.dumps(receipt, indent=2) + '\n')
        print(json.dumps({'stage': args.stage, 'status': receipt['status'], 'receipt_sha256': sha(out / 'receipt.json')}), flush=True)
    assert failure is None, failure


def interrupted(signum, frame):
    raise SystemExit('Guard interrupted by signal ' + str(signum))


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    main()
