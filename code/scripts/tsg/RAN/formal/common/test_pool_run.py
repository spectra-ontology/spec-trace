#!/usr/bin/env python3
"""test_pool_run.py — 제출·회수 중 깨진 풀의 재시도 경계를 검증한다.

Spec: docs/common/process/spectra_operations_rulebook.md §3.1.
Ontology: Phase-4 CR 문서 파싱 입력의 보존.
Cycle: 모의 풀 → 미완료 항목 재시도 → 중복 없는 결과.
배경: 제출 중 워커가 죽어도 아직 제출하지 않은 입력을 보존한다.
사용: python3 -B scripts/tsg/RAN/formal/common/test_pool_run.py.
LLM 호출: 없음. 모의 future만 사용하며 원본·DB에 접근하지 않는다.
"""
from concurrent.futures import Future
from concurrent.futures.process import BrokenProcessPool
import logging
import os
import unittest
from unittest.mock import patch

import pool_run


class FakeExecutor:
    def __init__(self, actions, submitted):
        self.actions = iter(actions)
        self.submitted = submitted

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def submit(self, wrapped, fn, args):
        self.submitted.append(args)
        action = next(self.actions)
        if action == 'submit_broken':
            raise BrokenProcessPool('synthetic submission failure')
        future = Future()
        if action == 'future_broken':
            future.set_exception(BrokenProcessPool('synthetic worker failure'))
        else:
            try:
                future.set_result(wrapped(fn, args))
            except Exception as exc:
                future.set_exception(exc)
        return future


class PoolRetryTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ)
        environment.start()
        self.addCleanup(environment.stop)
        os.environ.pop('SPECTRA_PARSE_WORKERS', None)

    def run_fake(self, actions, fn, items, workers=4):
        submitted, sizes = [], []
        rounds = iter(actions)

        def factory(*, max_workers):
            sizes.append(max_workers)
            return FakeExecutor(next(rounds), submitted)

        with patch.object(pool_run, 'ProcessPoolExecutor', factory):
            result = pool_run.run_all(fn, items, workers, logging.getLogger(__name__))
        return result, submitted, sizes

    def test_submission_failure_retries_unsubmitted_and_failed_only(self):
        result, submitted, sizes = self.run_fake(
            [['ok', 'future_broken', 'submit_broken'], ['ok', 'ok', 'ok']],
            lambda x: x * 10, [(1,), (2,), (3,), (4,)])
        self.assertCountEqual(result, [10, 20, 30, 40])
        self.assertEqual(submitted.count((1,)), 1)
        self.assertEqual(submitted.count((2,)), 2)
        self.assertEqual(submitted.count((3,)), 2)
        self.assertEqual(submitted.count((4,)), 1)
        self.assertEqual(sizes, [4, 2])

    def test_duplicate_argument_values_remain_distinct_items(self):
        result, _, sizes = self.run_fake(
            [['ok', 'submit_broken'], ['ok', 'ok']], lambda x: x,
            [(7,), (7,), (7,)])
        self.assertEqual(result, [7, 7, 7])
        self.assertEqual(sizes, [4, 2])

    def test_empty_argument_tuple_reports_original_item_error(self):
        def fails():
            raise ValueError('original error')

        with self.assertRaisesRegex(pool_run.PoolRunError, 'original error'):
            self.run_fake([['ok']], fails, [()])

    def test_single_worker_submission_failure_stops(self):
        with self.assertRaisesRegex(pool_run.PoolRunError, '1개'):
            self.run_fake([['submit_broken']], lambda: None, [()], workers=1)

    def test_no_items_returns_without_starting_pool(self):
        with patch.object(pool_run, 'ProcessPoolExecutor') as factory:
            self.assertEqual(pool_run.run_all(lambda: None, [], 4, logging.getLogger(__name__)), [])
        factory.assert_not_called()

    def test_environment_worker_limit_caps_caller_without_increasing_it(self):
        for configured, requested, expected in [('2', 8, 2), ('8', 4, 4)]:
            with self.subTest(configured=configured, requested=requested):
                with patch.dict(os.environ, {'SPECTRA_PARSE_WORKERS': configured}):
                    result, _, sizes = self.run_fake([['ok']], lambda x: x, [(7,)], workers=requested)
                self.assertEqual(result, [7])
                self.assertEqual(sizes, [expected])

    def test_unset_environment_worker_limit_preserves_retry_sizes(self):
        with patch.dict(os.environ):
            os.environ.pop('SPECTRA_PARSE_WORKERS', None)
            result, _, sizes = self.run_fake(
                [['future_broken'], ['ok']], lambda x: x, [(7,)], workers=4)
        self.assertEqual(result, [7])
        self.assertEqual(sizes, [4, 2])

    def test_invalid_environment_worker_limit_precedes_pool_creation(self):
        for configured in ['0', '-1', 'invalid', '']:
            with self.subTest(configured=configured):
                with patch.dict(os.environ, {'SPECTRA_PARSE_WORKERS': configured}):
                    with patch.object(pool_run, 'ProcessPoolExecutor',
                                      side_effect=AssertionError('pool must not start')) as factory:
                        with self.assertRaisesRegex(ValueError, 'SPECTRA_PARSE_WORKERS'):
                            pool_run.run_all(lambda x: x, [(7,)], 4, logging.getLogger(__name__))
                    factory.assert_not_called()


if __name__ == '__main__':
    unittest.main()
