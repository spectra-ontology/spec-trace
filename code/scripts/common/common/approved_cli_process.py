#!/usr/bin/env python3
"""approved_cli_process.py — 승인 CLI의 프로세스 실행과 자식 회수를 공유한다.

Spec: docs/common/process/internal_agent_guide.md 승인 CLI 실행.
Ontology: 승인 CLI의 입력·출력·중단·시간 제한 계약을 유지한다.
Cycle: 설치 진단·기능 작업·보고서 실행.
배경: bootstrap 어댑터와 런타임 보고서가 같은 프로세스 회수 계약을 사용한다.
사용: invoke(argv, input=task, timeout=seconds).
LLM 호출: 호출자가 전달한 argv만 실행하며 모델·인증·권한 정책은 호출자가 정한다.
"""
from __future__ import annotations

import os
import signal
import subprocess
import threading

__all__ = ["AgentInterrupted", "invoke"]


class AgentInterrupted(KeyboardInterrupt):
    """상위 실행기의 중단 요청을 자식 회수 후 전달한다."""


def invoke(argv: list[str], *, input: str | None = None, text: bool = True,
           capture_output: bool = True, timeout: float | None = None,
           cwd=None, env=None, check: bool = False) -> subprocess.CompletedProcess:
    """승인 CLI 프로세스 그룹을 시간 초과·중단·종료 시 회수한다.

    최종 응답을 먼저 반환한 CLI가 남긴 같은 그룹의 자식도 회수한다.
    중첩된 어댑터에는 더 짧은 회수 시간을 전달해 상위 종료 전에 자식을 정리한다.
    """
    if not text:
        raise ValueError("승인 CLI는 텍스트 표준입력·출력을 사용합니다")
    try:
        cleanup_grace = min(5.0, max(0.05, float(
            os.environ.get("_SPECTRA_AGENT_CLEANUP_GRACE", "5"))))
    except ValueError:
        cleanup_grace = 5.0
    child_environment = dict(os.environ if env is None else env)
    child_environment["_SPECTRA_AGENT_CLEANUP_GRACE"] = str(cleanup_grace / 2)
    process = subprocess.Popen(
        argv, stdin=subprocess.PIPE if input is not None else None,
        stdout=subprocess.PIPE if capture_output else None,
        stderr=subprocess.PIPE if capture_output else None,
        text=True, encoding="utf-8", cwd=cwd, env=child_environment,
        start_new_session=(os.name == "posix"),
    )

    def stop(sig: int) -> None:
        try:
            if os.name == "posix":
                os.killpg(process.pid, sig)
            elif sig == signal.SIGTERM:
                process.terminate()
            else:
                process.kill()
        except ProcessLookupError:
            pass

    cleaning = False

    def collect() -> None:
        nonlocal cleaning
        cleaning = True
        # 자식 어댑터의 회수 기한은 이 호출보다 짧다. 별도 세션의 CLI도 먼저 정리한다.
        stop(signal.SIGTERM)
        try:
            process.communicate(timeout=cleanup_grace)
        except subprocess.TimeoutExpired:
            pass
        finally:
            stop(signal.SIGKILL)
            process.communicate()

    previous_signals = {}
    if threading.current_thread() is threading.main_thread():
        def interrupted(signum, frame):
            if not cleaning:
                raise AgentInterrupted()

        for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
            previous_signals[sig] = signal.signal(sig, interrupted)
    try:
        stdout, stderr = process.communicate(input=input, timeout=timeout)
    except subprocess.TimeoutExpired:
        # 어댑터가 별도 CLI 그룹을 정리할 기회를 준 뒤 같은 그룹의 잔여 자식을 회수한다.
        collect()
        raise
    except BaseException:
        # 상위가 어댑터에 SIGTERM을 보낸 경우에도 여기서 별도 CLI 그룹을 회수한다.
        collect()
        raise
    finally:
        # 부모가 응답하고 pipe를 닫은 뒤에도 자손이 살아 있을 수 있다.
        try:
            stop(signal.SIGKILL)
        finally:
            for sig, previous in previous_signals.items():
                signal.signal(sig, previous)
    result = subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)
    if check:
        result.check_returncode()
    return result
