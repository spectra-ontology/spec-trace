"""공용 Qdrant 주소와 WG별 Neo4j 접속 대상의 정본.

Neo4j의 포트는 axis 레지스트리를 따른다. 현재 프로세스에 다른 WG용
NEO4J_URI/NEO4J_BOLT가 남았으면 접속 전에 거절한다. 자격증명은 별도
credentials 모듈에서 읽으며 오류 메시지에 URI 값을 출력하지 않는다.
"""
from __future__ import annotations

import os
from urllib.parse import urlsplit

from . import axis

QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_GRPC_PORT = 6334
QDRANT_URL = f"http://{QDRANT_HOST}:{QDRANT_PORT}"


def neo4j_uri(wg: str, *, override: str | None = None) -> str:
    """선택 WG의 등록 포트를 확인한 URI를 반환한다. 네트워크는 사용하지 않는다.

    명시적 인자, NEO4J_URI, NEO4J_BOLT, axis 기본값 순서로 선택한다.
    사용자 지정 호스트와 TLS scheme은 허용하며 포트는 선택 WG와 일치해야 한다.
    다른 포트가 필요한 설치는 axis 레지스트리와 인프라 설정을 함께 수정한다.
    """
    expected_port = axis.bolt_port(wg)
    value = override if override is not None else (os.environ.get("NEO4J_URI") or os.environ.get("NEO4J_BOLT"))
    if not value:
        return axis.bolt_uri(wg)
    try:
        parsed = urlsplit(value)
        if (parsed.scheme not in {"bolt", "bolt+s", "bolt+ssc", "neo4j", "neo4j+s", "neo4j+ssc"}
                or not parsed.hostname or parsed.username is not None or parsed.password is not None
                or parsed.fragment or any(char.isspace() for char in value)):
            raise ValueError("invalid endpoint")
        parsed_port = parsed.port
        port = parsed_port if parsed_port is not None else 7687
        if port == 0:
            raise ValueError("invalid endpoint port")
    except (TypeError, ValueError) as exc:
        raise ValueError("Neo4j 주소 형식을 확인하세요. 인증정보는 URI 대신 자격증명 설정을 사용합니다.") from exc
    if port != expected_port:
        raise ValueError(f"Neo4j 대상 포트가 {wg} 레지스트리({expected_port})와 다릅니다. 이전 WG의 NEO4J_URI/NEO4J_BOLT를 확인하세요.")
    return value
