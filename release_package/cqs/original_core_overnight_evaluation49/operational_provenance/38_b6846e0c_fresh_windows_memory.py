"""Fresh Windows memory queries over one retained PowerShell connection.

Each request has a new nonce and runs Get-CimInstance anew. Transport failure,
malformed values, nonce mismatch and timeouts fail closed; no cached value is
returned. This changes host observation transport, not scientific methods.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import select
import socket
import socketserver
import subprocess
import threading
import time
import uuid

SOCKET_ENV = 'SPECTRA_AUTH49_MEMORY_SOCKET'
SESSION_ENV = 'SPECTRA_AUTH49_MEMORY_SESSION'
COMMAND = ("$ErrorActionPreference='Stop'; "
           "while($null -ne ($n=[Console]::ReadLine())) { "
           "if($n -notmatch '^[a-f0-9]{32}$') { exit 2 }; "
           "$m=(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory; "
           "[Console]::WriteLine($n+' '+[string]$m); [Console]::Out.Flush() }")


def now():
    return datetime.now(timezone.utc).isoformat()


def observe():
    """Require a fresh nonce-bound observation, returning available bytes."""
    started = time.monotonic()
    nonce = uuid.uuid4().hex
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(15)
        connection.connect(os.environ[SOCKET_ENV])
        request = {'nonce': nonce, 'session': os.environ[SESSION_ENV]}
        connection.sendall((json.dumps(request) + '\n').encode())
        stream = connection.makefile('rb')
        raw = stream.readline(4097)
    if len(raw) > 4096 or not raw.endswith(b'\n'):
        raise RuntimeError('Invalid memory response framing')
    response = json.loads(raw)
    if response.get('nonce') != nonce or response.get('session') != request['session']:
        raise RuntimeError('Memory observation identity mismatch')
    if response.get('status') != 'FRESH_NUMERIC_OBSERVATION':
        raise RuntimeError('Windows memory unavailable: ' + str(response.get('failure')))
    value = response.get('windows_available_bytes')
    if type(value) is not int or value <= 0 or time.monotonic() - started > 15:
        raise RuntimeError('Nonpositive, nonnumeric or expired memory observation')
    linux = int(next(s.split()[1] for s in Path('/proc/meminfo').read_text().splitlines()
                     if s.startswith('MemAvailable:'))) * 1024
    return linux, value


def host_guard(output):
    """Preserve the original capture helper's 18GiB admission and record."""
    linux, windows = observe()
    gib = 1024 ** 3
    row = {'utc': now(), 'linux_available_bytes': linux,
           'windows_available_bytes': windows, 'reserve_bytes': 16 * gib,
           'new_container_budget_bytes': 2 * gib,
           'observation_transport': 'Fresh nonce-bound persistent PowerShell CIM query'}
    with (output / 'resource_checks.jsonl').open('a') as stream:
        stream.write(json.dumps(row) + '\n')
    if min(linux, windows) < 18 * gib:
        raise RuntimeError('Resource reserve would not support the owned 2GiB container')


class Broker:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(exist_ok=False)
        self.session = uuid.uuid4().hex
        self.path = '/run/user/' + str(os.getuid()) + '/spectra-auth27-' + self.session[:10] + '.sock'
        self.lock = threading.Lock()
        self.process = None
        self.server = None
        self.stderr = None
        self.thread = None

    def query(self, nonce):
        if not re.fullmatch(r'[a-f0-9]{32}', nonce):
            raise ValueError('Invalid nonce')
        with self.lock:
            began = time.monotonic()
            if self.process.poll() is not None:
                raise RuntimeError('PowerShell observation connection closed')
            self.process.stdin.write((nonce + '\n').encode())
            self.process.stdin.flush()
            ready, _, _ = select.select([self.process.stdout], [], [], 12)
            if not ready:
                raise TimeoutError('Fresh Windows CIM observation timed out')
            raw = self.process.stdout.readline(4097)
            match = re.fullmatch(rb'([a-f0-9]{32}) (\d+)\r?\n', raw)
            if match is None or match.group(1).decode() != nonce:
                raise RuntimeError('PowerShell returned a nonnumeric or mismatched observation')
            value = int(match.group(2)) * 1024
            if value <= 0:
                raise RuntimeError('Nonpositive Windows free memory')
            row = {'status': 'FRESH_NUMERIC_OBSERVATION', 'session': self.session,
                   'nonce': nonce, 'windows_available_bytes': value,
                   'observed_utc': now(), 'elapsed_seconds': time.monotonic() - began,
                   'Get_CimInstance_calls_for_this_request': 1, 'cached_values_used': 0}
            with (self.directory / 'actual_observations.jsonl').open('a') as stream:
                stream.write(json.dumps(row) + '\n')
            return row

    def start(self):
        self.stderr = (self.directory / 'powershell_stderr').open('xb')
        self.process = subprocess.Popen(
            ['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe',
             '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', COMMAND],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr, bufsize=0)
        # Admission itself is a fresh numeric query; no service exists on failure.
        self.query(uuid.uuid4().hex)
        broker = self

        class Handler(socketserver.StreamRequestHandler):
            def handle(self):
                request = json.loads(self.rfile.readline(4097))
                if request.get('session') != broker.session:
                    raise RuntimeError('Unexpected memory session')
                nonce = request.get('nonce', '')
                try:
                    response = broker.query(nonce)
                except Exception as exc:
                    response = {'status': 'UNAVAILABLE', 'session': broker.session,
                                'nonce': nonce, 'failure': type(exc).__name__}
                self.wfile.write((json.dumps(response) + '\n').encode())

        self.server = socketserver.ThreadingUnixStreamServer(self.path, Handler)
        self.server.daemon_threads = True
        os.chmod(self.path, 0o600)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        os.environ[SOCKET_ENV] = self.path
        os.environ[SESSION_ENV] = self.session

    def close(self):
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
        if self.process is not None:
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
        if self.stderr is not None:
            self.stderr.close()
        Path(self.path).unlink(missing_ok=True)
        for name in [SOCKET_ENV, SESSION_ENV]:
            os.environ.pop(name, None)
