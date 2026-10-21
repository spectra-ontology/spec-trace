"""Reuse the pinned archival read-only capture kernel for development probes."""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import subprocess
import sys

BASE = Path(__file__).resolve().parent
TASK = BASE.parents[1]
GIB = 1024 ** 3


def host_guard(output):
    mem = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
    linux_available = int(mem['MemAvailable'].split()[0]) * 1024
    command = ['powershell.exe', '-NoLogo', '-NoProfile', '-NonInteractive',
               '-Command', '(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory']
    windows_available = int(subprocess.check_output(command, timeout=15).decode().strip()) * 1024
    evidence = {'utc': datetime.now(timezone.utc).isoformat(),
                'linux_available_bytes': linux_available, 'windows_available_bytes': windows_available,
                'reserve_bytes': 16 * GIB, 'new_container_budget_bytes': 2 * GIB}
    with (output / 'resource_checks.jsonl').open('a') as stream:
        stream.write(json.dumps(evidence) + '\n')
    if min(linux_available, windows_available) < 18 * GIB:
        raise RuntimeError('Resource reserve would not support the owned 2GiB container')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wg', required=True, choices=[f'RAN{i}' for i in range(1, 6)])
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(BASE.resolve()):
        raise ValueError('Capture output must remain inside the isolated re-audit directory')
    output.mkdir(parents=True, exist_ok=True)
    with (BASE / 'native_capture.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        host_guard(output)
        active = subprocess.check_output(['docker', 'ps', '--format', '{{.Names}}']).decode().splitlines()
        if any(name.startswith('kdd-db-frozen-v1-') for name in active):
            raise RuntimeError('Another archival capture is active; refusing parallel container admission')
        resource.setrlimit(resource.RLIMIT_AS, (2 * GIB, 2 * GIB))
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
        runner = TASK / 'execute_candidates.py'
        spec = importlib.util.spec_from_file_location('preserved_native_capture', runner)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.BASE = output
        module.TIMEOUT_SECONDS = 20
        protocol = json.loads((TASK / 'execution_protocol.json').read_text())
        protocol.update(query_timeout_seconds=20, scope='Direct Codex development probes, not model predictions',
                        host_reserve_bytes=16 * GIB, python_address_space_limit_bytes=2 * GIB,
                        inherited_kernel_sha256=hashlib.sha256(runner.read_bytes()).hexdigest())
        protocol_path = output / 'execution_protocol.json'
        if protocol_path.exists():
            assert json.loads(protocol_path.read_text()) == protocol
        else:
            protocol_path.write_text(json.dumps(protocol, indent=2) + '\n')
        original_execute = module.execute

        def guarded_execute(item, guard, native):
            host_guard(output)
            return original_execute(item, guard, native)

        module.execute = guarded_execute
        sys.argv = [str(runner), '--wg', args.wg, '--input', str(args.input.resolve())]
        module.main()
        host_guard(output)


if __name__ == '__main__':
    main()
