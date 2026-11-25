#!/usr/bin/env python3
"""test_approved_cli_process.py — 공유 실행부의 결과·신호·회수를 검증한다.

Spec: docs/common/process/internal_agent_guide.md 승인 CLI 실행.
Ontology: CLI 어댑터·보고서의 실행 계약을 유지한다.
Cycle: 로컬 자식 실행 → 종료 또는 중단 → 잔여 자식 회수.
배경: 기능 실행이 설치 어댑터를 import하지 않고 같은 회수 계약을 사용한다.
사용: python3 -B scripts/common/common/test_approved_cli_process.py
LLM 호출·DB·모델·네트워크: 없음. 합성 로컬 Python 프로세스만 실행한다.
"""
from __future__ import annotations

import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import approved_cli_process as process


class ProcessTests(unittest.TestCase):
    def test_output_exit_and_text_contract(self):
        result = process.invoke([sys.executable, "-c", "import sys; print('result'); print('diagnostic',file=sys.stderr)"])
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "result\n", "diagnostic\n"))
        with self.assertRaises(subprocess.CalledProcessError) as caught:
            process.invoke([sys.executable, "-c", "raise SystemExit(7)"], check=True)
        self.assertEqual(caught.exception.returncode, 7)
        with self.assertRaises(ValueError):
            process.invoke([sys.executable, "-c", "pass"], text=False)

    @unittest.skipUnless(os.name == "posix", "POSIX 신호 계약")
    def test_signal_handlers_restored_after_success_and_timeout(self):
        before = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT)}
        process.invoke([sys.executable, "-c", "pass"], timeout=3)
        self.assertEqual({sig: signal.getsignal(sig) for sig in before}, before)
        with patch.dict(os.environ, {"_SPECTRA_AGENT_CLEANUP_GRACE": "0.05"}):
            with self.assertRaises(subprocess.TimeoutExpired):
                process.invoke([sys.executable, "-c", "import time; time.sleep(60)"], timeout=0.1)
        self.assertEqual({sig: signal.getsignal(sig) for sig in before}, before)

    @unittest.skipUnless(os.name == "posix", "POSIX 프로세스 그룹 계약")
    def test_term_cancels_invocation_reaps_child_and_restores_handler(self):
        with tempfile.TemporaryDirectory(prefix="spectra-process-cancel-") as temporary:
            marker = Path(temporary) / "child.pid"
            child = ("import os,signal,time; from pathlib import Path; "
                     "signal.signal(signal.SIGTERM,signal.SIG_IGN); "
                     f"Path({str(marker)!r}).write_text(str(os.getpid())); time.sleep(60)")
            driver = ("import sys,signal\n"
                      f"sys.path.insert(0,{str(Path(process.__file__).parent)!r})\n"
                      "from approved_cli_process import invoke,AgentInterrupted\n"
                      "before=signal.getsignal(signal.SIGTERM)\n"
                      "try:\n"
                      f" invoke([sys.executable,'-c',{child!r}])\n"
                      "except AgentInterrupted:\n"
                      " assert signal.getsignal(signal.SIGTERM)==before\n"
                      " raise SystemExit(130)\n")
            environment = {"PATH": os.defpath, "PYTHONDONTWRITEBYTECODE": "1", "_SPECTRA_AGENT_CLEANUP_GRACE": "0.05"}
            parent = subprocess.Popen([sys.executable, "-B", "-c", driver], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=environment)
            try:
                deadline = time.monotonic() + 5
                while not marker.exists() and parent.poll() is None and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(marker.exists(), "합성 자식이 시작되지 않았습니다")
                parent.terminate()
                stdout, stderr = parent.communicate(timeout=5)
                self.assertEqual(parent.returncode, 130, stdout + stderr)
                pid = int(marker.read_text())
                deadline = time.monotonic() + 3
                while time.monotonic() < deadline:
                    stat = Path(f"/proc/{pid}/stat")
                    if not stat.exists() or stat.read_text().split(") ", 1)[1].split()[0] == "Z":
                        break
                    time.sleep(0.01)
                else:
                    self.fail("중단 후 합성 자식이 실행 중입니다")
            finally:
                if parent.poll() is None:
                    parent.kill()
                parent.communicate(timeout=5)
                if marker.exists():
                    try:
                        os.kill(int(marker.read_text()), signal.SIGKILL)
                    except ProcessLookupError:
                        pass


if __name__ == "__main__":
    unittest.main()
