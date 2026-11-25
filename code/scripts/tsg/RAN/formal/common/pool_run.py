"""pool_run.py — 프로세스 풀로 항목을 모두 처리한다. 워커가 죽어도 항목을 잃지 않는다.

워커 하나가 죽으면(메모리 제한에 걸린 OOM 등) 풀 전체가 깨지고, 아직 끝나지 않은 future 는
전부 `BrokenProcessPool` 로 끝난다. 이것을 항목별 오류 한 줄로 흘려보내면 산출이 조용히 줄어든 채
정상 종료한다 — 실제로 RAN4 · RAN5 CR 문서 파싱이 12,313 → 5,056 · 26,328 → 14,240 건으로 줄어
들었지만 종료 코드는 0 이었다.

여기서는 끝나지 못한 항목만 워커 수를 반으로 줄인 새 풀에서 다시 돌린다. 워커 하나로도 풀이 깨지면
(항목 하나가 제한을 넘는다) 멈춘다. 항목 함수가 던진 예외도 모아 두었다가 끝에서 멈춘다.
어느 쪽이든 호출자는 부분 산출을 쓰지 않는다.

워커는 항목마다 순환 GC 를 돌린다. python-docx 문서는 부품끼리 서로 가리키는 순환 참조라 참조 수로는
풀리지 않고, 뒤에 붙은 lxml 트리(C 메모리)는 파이썬 객체 수로 도는 GC 기준에 잡히지 않는다. 그래서
워커 하나가 문서를 이어 받으면 트리가 쌓인다 — RAN4 CR 800건 연속 파싱 RSS 3.8GB, 항목마다 GC 면 1GB.

워커는 항목마다 `docx_reader.STATS` 가 늘어난 몫을 결과와 함께 돌려보내고, 부모가 자기 `STATS` 에
더한다. 워커 안에서 센 수는 부모로 건너가지 않아서, 부모가 기록에 싣는 Strict 계수가 문서를 맞춰
열고도 늘 0 이었다.
"""
from __future__ import annotations

import gc
import logging
import os
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from concurrent.futures.process import BrokenProcessPool
from pathlib import Path

_ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(_ROOT / "scripts" / "common" / "common"))
import docx_reader  # noqa: E402 — 워커가 센 몫을 부모의 계수에 더한다


class PoolRunError(RuntimeError):
    """처리하지 못한 항목이 남았다."""


def _run_one(fn, args):
    """항목 하나의 결과와, 그 항목을 도는 동안 워커의 `docx_reader.STATS` 가 늘어난 몫."""
    before = Counter(docx_reader.STATS)
    try:
        return fn(*args), docx_reader.STATS - before
    finally:
        gc.collect()


def run_all(fn, items, workers: int, log: logging.Logger) -> list:
    """항목을 처리한다. SPECTRA_PARSE_WORKERS 양수 설정은 호출자의 워커 수 상한이다."""
    worker_limit = os.environ.get("SPECTRA_PARSE_WORKERS")
    if worker_limit is not None:
        try:
            limit = int(worker_limit)
        except ValueError:
            raise ValueError("SPECTRA_PARSE_WORKERS must be a positive integer") from None
        if limit < 1:
            raise ValueError("SPECTRA_PARSE_WORKERS must be a positive integer")
        workers = min(workers, limit)
    pending = list(items)
    results: list = []
    failures: list = []
    while pending:
        broken = []
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {}
            for index, args in enumerate(pending):
                try:
                    futures[executor.submit(_run_one, fn, args)] = args
                except BrokenProcessPool:
                    # 제출 도중 풀이 깨지면 이 항목과 아직 제출하지 않은 항목도 재시도한다.
                    broken.extend(pending[index:])
                    break
            for future in as_completed(futures):
                args = futures[future]
                try:
                    result, counts = future.result()
                    results.append(result)
                    docx_reader.STATS.update(counts)
                except BrokenProcessPool:
                    broken.append(args)
                except Exception as e:  # noqa: BLE001 — 항목 함수의 예외는 끝에서 한꺼번에 멈춘다
                    failures.append((args, e))
                    log.error(f"  {args!r}: {e}")
        if not broken:
            break
        if workers == 1:
            raise PoolRunError(f"워커 1개로도 풀이 깨짐 — 끝나지 못한 항목 {len(broken)}건, 첫 항목 {broken[0]!r}")
        workers = max(1, workers // 2)
        log.warning(f"  워커가 죽어 풀이 깨짐 — 끝나지 못한 {len(broken)}건을 워커 {workers}개로 다시 돌린다")
        pending = broken
    if failures:
        raise PoolRunError(f"항목 함수 예외 {len(failures)}건, 첫 항목 {failures[0][0]!r}: {failures[0][1]}")
    return results
