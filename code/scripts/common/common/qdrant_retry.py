#!/usr/bin/env python3
"""qdrant_retry.py — Qdrant 호출의 일시 전송 오류를 제한된 대기로 재시도한다.

Spec: docs/common/standards/directory_structure_guide.md — 공통 알고리즘 재사용
Ontology: 컬렉션·포인트·payload는 호출자가 전달한 값을 그대로 사용한다.
Cycle: 정형 자료·이메일의 벡터 적재 및 갱신
배경: 각 적재기의 동일한 HTTP 상태 판정과 대기 한도를 공유한다.
사용: call_with_retry(fn, args, kwargs, max_wait=120, sleep=time.sleep)
LLM 호출: 없음
"""

from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse


def call_with_retry(fn, args, kwargs, *, max_wait, sleep):
    """전송 오류와 HTTP 408·429·503을 대기 합계 한도 안에서 재시도한다.

    다른 HTTP 상태와 다른 예외는 즉시 전달한다. 한도는 요청 실행 시간과
    별개인 대기 시간의 합계다. 인자 묶음을 따로 받아 원래 호출의 키워드와
    재시도 설정이 충돌하지 않게 한다. sleep은 호출자가 사용하는 함수를
    전달하므로 기존 적재기의 시간 제어·테스트 대체 경로를 유지한다.

    서버가 요청을 적용한 뒤 응답 전송만 실패할 수도 있다. 호출자는 같은 요청을
    반복해도 결과가 유지되는지 확인해야 한다. 예를 들어 create_snapshot은
    재시도할 때 스냅샷을 추가로 만들 수 있다.
    """
    waited, delay = 0.0, 1.0
    while True:
        try:
            return fn(*args, **kwargs)
        except (ResponseHandlingException, UnexpectedResponse) as exc:
            if isinstance(exc, UnexpectedResponse) and exc.status_code not in (408, 429, 503):
                raise
            if waited + delay > max_wait:
                raise
            print(f"    ⚠️ Qdrant 전송 오류({exc}) — {delay:.0f}초 후 재시도"
                  f" (누적 대기 {waited:.0f}/{max_wait}초)", flush=True)
            sleep(delay)
            waited += delay
            delay *= 2
