"""Stream a bootstrap child process and reap its group after interrupted output.

Shared by stage execution and package installation. The caller owns log files,
redaction and bootstrap lock descriptors. No network or model calls occur here.
"""
from __future__ import annotations

import codecs
import io
import os
import selectors
import signal
import subprocess
import threading
from collections.abc import Callable


def stop_process_group(process, *, grace_seconds: float = 3) -> None:
    """Stop and reap a child created with its own POSIX session.

    Callers must launch with start_new_session=True (or setsid on POSIX).
    The final kill also reaches descendants after the direct child exits.
    """
    previous_signals = {}
    try:
        if threading.current_thread() is threading.main_thread():
            for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
                previous_signals[sig] = signal.signal(sig, signal.SIG_IGN)

        def stop(sig):
            try:
                if os.name == "posix":
                    os.killpg(process.pid, sig)
                elif sig == signal.SIGTERM:
                    process.terminate()
                else:
                    process.kill()
            except ProcessLookupError:
                pass

        stop(signal.SIGTERM)
        try:
            process.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired:
            pass
        finally:
            stop(signal.SIGKILL)
            process.wait()
    finally:
        for sig, previous in previous_signals.items():
            signal.signal(sig, previous)


def stream_command(argv: list[str] | str, on_line: Callable[[str], None], *,
                   cwd=None, env=None, pass_fds=(), shell: bool = False,
                   resource_check: Callable[[], None] | None = None) -> int:
    """Return the child's exit code; propagate errors after group cleanup.

    Only the main thread temporarily handles termination signals. POSIX children
    use a separate session so a failed terminal or log write also stops their
    descendants. An optional resource check also runs once per second while the
    child is quiet. Its original exception propagates after process cleanup.
    Existing signal handlers are restored on every exit path.
    """
    process = None
    previous_signals = {}
    cleaning = False
    try:
        if threading.current_thread() is threading.main_thread():
            def interrupted(signum, frame):
                if not cleaning:
                    raise KeyboardInterrupt(f"구축 중단 신호: {signum}")
            for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
                previous_signals[sig] = signal.signal(sig, interrupted)
        if resource_check is not None:
            resource_check()
        process = subprocess.Popen(
            argv, cwd=cwd, env=env, shell=shell, pass_fds=pass_fds,
            start_new_session=(os.name == "posix"), stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, bufsize=1)
        with process.stdout:
            if resource_check is None:
                for line in process.stdout:
                    on_line(line)
            else:
                # Read available bytes directly: readline() could wait for a
                # newline while a quiet or partially writing pip allocates disk.
                decoder = io.IncrementalNewlineDecoder(
                    codecs.getincrementaldecoder(process.stdout.encoding)(errors=process.stdout.errors),
                    translate=True)
                pending = ""
                with selectors.DefaultSelector() as selector:
                    selector.register(process.stdout, selectors.EVENT_READ)
                    ended = False
                    while not ended:
                        resource_check()
                        for key, _ in selector.select(timeout=1):
                            data = os.read(key.fd, 64 * 1024)
                            pending += decoder.decode(data, final=not data)
                            while "\n" in pending:
                                line, pending = pending.split("\n", 1)
                                on_line(line + "\n")
                            if not data:
                                if pending:
                                    on_line(pending)
                                ended = True
        code = process.wait()
        if resource_check is not None:
            resource_check()
        return code
    except BaseException:
        if process is None:
            raise
        cleaning = True
        stop_process_group(process)
        raise
    finally:
        for sig, previous in previous_signals.items():
            signal.signal(sig, previous)
