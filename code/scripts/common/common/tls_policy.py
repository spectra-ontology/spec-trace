#!/usr/bin/env python3
"""증분 수집기의 TLS 인증서 검증 설정을 확인한다.

Spec: docs/common/process/internal_install_guide.md 회사 인증서 설정.
Ontology: 해당 없음 (전송 계층 설정).
Cycle: 설정 읽기 → 수집기 초기화 → HTTP 요청.
배경: 기본값과 호출 인자가 같은 TLS 검증 계약을 유지한다.
사용: require_tls_verification(configured_value).
LLM 호출·네트워크·DB·파일 쓰기: 없음.
"""
import os
from pathlib import Path


def require_tls_verification(value: object = True) -> bool:
    """검증 활성화만 수용한다. 회사 CA는 requests의 표준 환경변수로 지정한다."""
    if value is not True:
        raise ValueError(
            "TLS 인증서 검증은 True여야 합니다. 회사 CA는 "
            "REQUESTS_CA_BUNDLE 또는 CURL_CA_BUNDLE로 지정하세요."
        )
    return True


def aria2_tls_options(environ: dict | None = None) -> list[str]:
    """aria2도 검증을 켜고 requests 또는 SSL의 명시적인 CA 파일을 사용한다."""
    environment = os.environ if environ is None else environ
    options = ['--check-certificate=true']
    certificate = (environment.get('REQUESTS_CA_BUNDLE') or environment.get('CURL_CA_BUNDLE')
                   or environment.get('SSL_CERT_FILE'))
    if certificate:
        if not Path(certificate).is_file():
            raise ValueError('aria2에 지정한 회사 CA 파일이 없습니다')
        options.append('--ca-certificate=' + certificate)
    return options
