"""로컬 GPU 대량 임베딩의 배치 사이에 휴지시간을 추가한다.

대량 적재기의 `embed_local` 호출이 정상 반환하면, 실행 시간에 `REST`를 곱한 시간만큼
대기한다. 연속 적재 중 관찰한 GPU 온도와 호스트 중단 사례를 계기로 도입한 대기이며,
호스트 중단의 원인을 판정하거나 중단 방지를 보장하는 기능은 아니다.

배치 구성과 함수 반환값은 유지한다. 소수의 질의를 임베딩하는 검색·검증 경로에는
적용하지 않는다. 호출마다 대기 시간만큼 응답 시간이 늘어나기 때문이다.

`REST`는 환경 변수 `SPECTRA_GPU_REST`에서 모듈을 불러올 때 한 번 읽으며 기본값은 0.5다.
호출과 대기만 반복한다고 가정하면 호출 시간 비율은 1/(1+REST)이고, 0은 대기를 생략한다.
이미 실행 중인 프로세스에는 이후 환경 변수 변경이 반영되지 않는다."""

from __future__ import annotations

import os
import time
import math

REST = float(os.environ.get("SPECTRA_GPU_REST", "0.5"))
if not math.isfinite(REST) or REST < 0:
    raise ValueError("SPECTRA_GPU_REST는 0 이상의 유한한 수여야 합니다")


def rested(fn, *args, **kwargs):
    """`fn`이 정상 반환하면 실행 시간 × `REST`만큼 대기한 뒤 그 결과를 반환한다.

    `fn`의 예외는 그대로 전파하며, 이 경우 대기하지 않는다."""
    t = time.monotonic()
    out = fn(*args, **kwargs)
    if REST > 0:
        time.sleep((time.monotonic() - t) * REST)
    return out
