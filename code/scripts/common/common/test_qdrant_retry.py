#!/usr/bin/env python3
"""Qdrant 재시도의 상태 코드·대기 한도·호출 인자와 WG별 대체 경로를 검사한다.

Spec: docs/common/process/internal_components.md — 구축 순서와 회귀 검사.
Ontology: 컬렉션·포인트는 생성하지 않고 호출 인자 보존만 확인한다.
Cycle: 합성 전송 오류 → 재시도 또는 즉시 예외 전달 → WG 연결 함수 대조.
배경: 공통화 이후에도 각 적재기의 대기 설정과 호출 인자가 유지되는지 확인한다.
사용: python3 -B scripts/common/common/test_qdrant_retry.py
LLM 호출: 없음. DB·모델·네트워크를 사용하지 않는다.
"""

import ast
from contextlib import redirect_stdout
import io
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(ROOT / "scripts/common"))
from common.qdrant_retry import call_with_retry
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse


def http_failure(code):
    return UnexpectedResponse(code, "fixture", b"fixture", {})


class QdrantRetryTests(unittest.TestCase):
    def retry(self, fn, *, args=(), kwargs=None, budget=120):
        sleep = Mock()
        with redirect_stdout(io.StringIO()):
            result = call_with_retry(fn, args, kwargs or {}, max_wait=budget, sleep=sleep)
        return result, sleep

    def test_success_preserves_return_value_and_all_arguments(self):
        expected = object()
        fn = Mock(return_value=expected)
        result, sleep = self.retry(fn, args=("collection",), kwargs={"timeout": 9, "sleep": "payload"})
        self.assertIs(result, expected)
        fn.assert_called_once_with("collection", timeout=9, sleep="payload")
        sleep.assert_not_called()

    def test_transient_http_statuses_retry_without_real_sleep(self):
        for code in (408, 429, 503):
            with self.subTest(code=code):
                fn = Mock(side_effect=[http_failure(code), "ok"])
                result, sleep = self.retry(fn)
                self.assertEqual(result, "ok")
                sleep.assert_called_once_with(1.0)
                self.assertEqual(fn.call_count, 2)

    def test_other_http_failures_are_propagated_immediately(self):
        for code in (400, 401, 403, 404, 409, 422, 500):
            with self.subTest(code=code):
                error = http_failure(code)
                fn, sleep = Mock(side_effect=error), Mock()
                with self.assertRaises(UnexpectedResponse) as caught:
                    call_with_retry(fn, (), {}, max_wait=120, sleep=sleep)
                self.assertIs(caught.exception, error)
                self.assertEqual(fn.call_count, 1)
                sleep.assert_not_called()

    def test_retry_wait_sum_includes_boundary_but_stops_before_exceeding_it(self):
        error = ResponseHandlingException(ConnectionError("fixture"))
        fn, sleep = Mock(side_effect=error), Mock()
        with redirect_stdout(io.StringIO()), self.assertRaises(ResponseHandlingException) as caught:
            call_with_retry(fn, (), {}, max_wait=3, sleep=sleep)
        self.assertIs(caught.exception, error)
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [1.0, 2.0])
        self.assertEqual(fn.call_count, 3)

    def test_zero_wait_budget_never_sleeps(self):
        sleep = Mock()
        with self.assertRaises(ResponseHandlingException):
            call_with_retry(Mock(side_effect=ResponseHandlingException(TimeoutError())),
                            (), {}, max_wait=0, sleep=sleep)
        sleep.assert_not_called()

    def test_unrelated_exception_is_not_retried(self):
        error = ValueError("invalid payload")
        fn, sleep = Mock(side_effect=error), Mock()
        with self.assertRaises(ValueError) as caught:
            call_with_retry(fn, (), {}, max_wait=120, sleep=sleep)
        self.assertIs(caught.exception, error)
        self.assertEqual(fn.call_count, 1)
        sleep.assert_not_called()

    def test_formal_adapters_keep_module_timeout_and_sleep_override(self):
        checked = []
        for path in sorted((ROOT / "scripts/tsg/RAN/formal").rglob("*.py")):
            text = path.read_text()
            if "def _with_retry(" not in text:
                continue
            for node in ast.parse(text).body:
                if not isinstance(node, ast.FunctionDef) or node.name != "_with_retry":
                    continue
                with self.subTest(path=str(path.relative_to(ROOT))):
                    sleep = Mock()
                    namespace = {"QDRANT_TIMEOUT": 0, "time": SimpleNamespace(sleep=sleep)}
                    tree = ast.Module(body=[node], type_ignores=[])
                    exec(compile(tree, str(path), "exec"), namespace)
                    fn = Mock(side_effect=ResponseHandlingException(TimeoutError()))
                    with self.assertRaises(ResponseHandlingException):
                        namespace["_with_retry"](fn)
                    sleep.assert_not_called()
                    namespace["QDRANT_TIMEOUT"] = 1
                    fn.side_effect = [http_failure(503), "ok"]
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(namespace["_with_retry"](fn, "fixture", wait=True), "ok")
                    sleep.assert_called_once_with(1.0)
                    self.assertEqual(fn.call_args.args, ("fixture",))
                    self.assertEqual(fn.call_args.kwargs, {"wait": True})
                    checked.append(path)
        self.assertTrue(checked, "No formal Qdrant retry adapters were exercised")


if __name__ == "__main__":
    unittest.main()
