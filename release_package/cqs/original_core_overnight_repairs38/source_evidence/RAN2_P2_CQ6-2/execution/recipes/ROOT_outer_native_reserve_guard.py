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
A = Path(__file__).resolve().parent
GIB = 1024 ** 3
SCOPE = '9081125b44f1cda5364890eaa9dd5b9f3338226b438c807a65e64bba1f66dc4a'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def memory():
    sys.path.insert(0,str(B/'authorized_incremental29_OpenRouter_release/operational_guards'))
    from fresh_windows_memory import observe
    return observe()


def ownership_helper():
    path = B / 'root_evidence/two_agent_unresolved_loop/root_CQ045_original_contract_source_review/run_guarded_exact_native_infrastructure_retry.py'
    spec = importlib.util.spec_from_file_location('cq045_exact_owned_cleanup', path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['execute_RAN2'])
    args = parser.parse_args()
    assert sha(A / 'definition.json') == SCOPE
    out = HERE / ('ROOT_actual_guarded_persistent_cim_' + args.stage)
    assert not out.exists(), 'Preserve previous attempts'
    out.mkdir()
    controller = HERE / 'ROOT_guarded_native_capture.py'
    native_wg = args.stage.split('_', 1)[1] if args.stage.startswith('execute_') else None
    if native_wg:
        cmd = ['/usr/bin/python3', '-B', str(controller)]
    else:
        controller = A / 'evaluation/runtime/execute_ready.py'
        cmd = ['/usr/bin/python3', '-B', str(controller), 'assemble',
               '--bundle', '/home/sihyeon/workspace/spectra/logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit/root_evidence/two_agent_unresolved_loop/adjudication62/resumed_deep_verification/sequential_two_main/portable_three_v1/release_package/cqs/original_core_overnight_repairs27',
               '--run-dir', str(A / 'evaluation/first_trial')]
    assert controller.is_file()
    initial_container_identity = None
    container_name = 'kdd-db-frozen-v1-' + native_wg.lower() if native_wg else None
    def checked_owned_container():
        info = json.loads(subprocess.check_output(['docker', 'inspect', container_name]))[0]
        manifest_path = Path('/home/sihyeon/workspace/spectra-public/spec-trace/release_package/cqs/contract_repair_v1/_frozen_ttl_v1') / native_wg.lower() / 'import_manifest.json'
        manifest = json.loads(manifest_path.read_text())
        labels = info['Config'].get('Labels') or {}
        assert info['Name'] == '/' + container_name and labels.get('spectra.frozen.owner') == 'contract_repair_v1'
        assert labels.get('spectra.frozen.run_uuid') == manifest['run_uuid']
        assert info['HostConfig']['Memory'] == 2 * GIB and info['HostConfig']['NanoCpus'] == 10**9
        if initial_container_identity is not None:
            assert info['Id'] == initial_container_identity, 'Container identity changed'
        return info
    began = time.monotonic()
    child, failure, code, initial, cleanup = None, None, None, None, None
    samples = []
    helper = None  # This guard controls generation/analysis only; native execution has its separate scheduler.
    try:
        linux, windows = memory()
        initial = {'Linux_available_bytes': linux, 'Windows_available_bytes': windows}
        assert min(linux, windows) >= 26 * GIB, initial
        if native_wg:
            initial_info = checked_owned_container()
            assert initial_info['State']['Running'] is False
            initial_container_identity = initial_info['Id']
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
        assert sha(A / 'definition.json') == SCOPE
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
        if native_wg and child is not None:
            try:
                with (B / 'native_capture.lock').open('a') as lock:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    final_info = checked_owned_container()
                    running = final_info['State']['Running']
                    if running:
                        subprocess.run(['docker', 'stop', '--time', '20', container_name], check=True, capture_output=True)
                    assert checked_owned_container()['State']['Running'] is False
                    cleanup = {'owned_stopped': True, 'fallback_stop': running, 'container': container_name,
                               'container_identity': initial_container_identity, 'common_lock_held': True}
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
