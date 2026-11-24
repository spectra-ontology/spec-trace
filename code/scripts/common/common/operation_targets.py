"""증분 갱신의 DB 대상 검사와 하위 적재기로의 설정 전달을 관리한다."""

from __future__ import annotations

import os
from ipaddress import ip_address
from pathlib import Path
import re
import sys

from . import axis, credentials


def explicit_meeting_folder(folder: str, *, meeting_id: str, wg: str,
                            normalize) -> str:
    """명시한 FTP 폴더가 한 경로 요소이며 대상 회의와 같은지 검사한다.

    전자회의·bis·개최지 접미사는 원문 폴더 이름 그대로 하위 수집기에 전달한다.
    회의 ID에서 폴더 이름을 다시 추측하지 않는다.
    """
    if (not isinstance(folder, str)
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", folder) is None
            or not any(folder.upper().startswith(prefix.upper())
                       for prefix in axis.meeting_folder_prefixes(wg))):
        raise ValueError("--ftp-folder에는 경로가 아닌 정확한 회의 폴더 이름을 지정하세요")
    if normalize(folder, wg=wg) != meeting_id:
        raise ValueError("--ftp-folder의 회의 식별자가 meeting_id와 다릅니다")
    return folder


def bounded_update_scope(root: Path | None = None) -> dict | None:
    """같은 소스의 제한 구축 계약을 읽고 갱신에도 같은 선택을 적용한다."""
    root = axis.PROJECT_ROOT if root is None else Path(root)
    path = root / "logs/common/bootstrap/scope.json"
    if not path.exists() and not path.is_symlink():
        return None
    bootstrap = root / "scripts/common/bootstrap"
    if str(bootstrap) not in sys.path:
        sys.path.insert(0, str(bootstrap))
    from bounded_scope import load_contract
    return load_contract(root)


def bounded_spec_targets(scope: dict, wg: str, family: str, targets=None) -> list[str]:
    """명시 대상 또는 저장된 규격 목록을 검증하며 WG 전체로 확대하지 않는다."""
    selection = scope["selection"]
    kind = family.upper()
    if wg not in scope["wgs"] or kind not in selection["data_kinds"]:
        raise ValueError(f"제한 구축 범위에 없는 갱신이다: {wg}/{kind}")
    allowed = selection["specs"].get(wg, [])
    selected = allowed if targets is None else list(targets)
    if any(number not in allowed for number in selected):
        raise ValueError("갱신할 규격이 저장된 제한 구축 범위를 벗어난다")
    return list(selected)


def canonical_neo4j_errors(config, wg: str) -> list[str]:
    """Phase-1~5 하위 적재기의 실제 Neo4j 대상과 설정을 대조한다.

    하위 적재기는 axis의 WG URI, 프로세스 계정·정본 비밀번호와 기본 DB를
    사용한다. 설정만 바꾸면 사전 조회·삭제와 하위 적재가 다른 DB에 수행된다.
    자격증명 값은 진단 메시지에 기록하지 않는다.
    """
    errors = []
    if os.environ.get("NEO4J_USER") == "":
        errors.append("NEO4J_USER는 비어 있지 않은 계정 이름을 사용하세요")
    expected = (
        ("neo4j_uri", axis.bolt_uri(wg)),
        ("neo4j_user", os.environ.get("NEO4J_USER", "neo4j")),
        ("neo4j_database", "neo4j"),
    )
    for name, value in expected:
        if getattr(config, name) != value:
            errors.append(f"{name}: 하위 적재기와 같은 기본 대상({value})을 사용하세요")
    try:
        password = credentials.neo4j_password()
    except credentials.MissingCredential:
        errors.append("NEO4J_PASSWORD 정본 자격증명을 설정하세요")
    else:
        if config.neo4j_password != password:
            errors.append("neo4j_password: 하위 적재기와 같은 NEO4J_PASSWORD를 사용하세요")
    return errors


def phase10_target_errors(config, tasks=(1, 2, 3, 4)) -> list[str]:
    """회의 증분 실행의 사전 조회와 실제 Task별 적재 대상을 일치시킨다.

    Task 2는 WG 기본 Neo4j, Task 3은 같은 대상과 NEO4J_URI 환경변수,
    Task 4는 localhost:6333을 쓴다. 컬렉션 이름은 Task 4의 CLI로 전달한다.
    Task 1 수집만 실행할 때는 DB 적재 대상을 제한하지 않는다.
    """
    try:
        scope = bounded_update_scope()
        if scope is not None and "meetings" not in scope["selection"]["data_kinds"]:
            return ["이 제한 구축에는 회의 자료가 포함되어 있지 않습니다. 회의 갱신 범위를 별도로 준비하세요"]
    except (OSError, ValueError, RuntimeError) as exc:
        return [f"구축 범위 계약을 확인하지 못했습니다: {exc}"]
    errors = canonical_neo4j_errors(config, config.wg) if {2, 3}.intersection(tasks) else []
    if 3 in tasks:
        expected = axis.bolt_uri(config.wg)
        if os.environ.get("NEO4J_URI", expected) != expected:
            errors.append("NEO4J_URI: Task 3도 WG 기본 Neo4j 주소를 사용하도록 설정하세요")
    if 4 in tasks and (config.qdrant_host != "localhost" or config.qdrant_port != 6333):
        errors.append("Qdrant: Task 4 적재기와 같은 localhost:6333을 사용하세요")
    return errors


def phase11_target_errors(config, pipeline: str, task_num: int | None, targets=None) -> list[str]:
    """설정된 대상의 형식과 임베딩 선언을 DB 연결 전에 확인한다.

    Phase-11은 검증한 설정을 하위 프로세스에도 전달한다. Neo4j 데이터베이스는
    기존 TS 보조 적재기가 사용하는 neo4j로 유지하고, URI·계정·비밀번호와
    Qdrant 호스트·포트·등록 컬렉션은 사용자 설정을 사용한다.
    """
    from urllib.parse import urlsplit
    from .embedding_registry import BUILTIN_COLLECTIONS, require_local

    if pipeline not in {"ts", "cr", "tr"}:
        return [f"알 수 없는 파이프라인: {pipeline}"]
    try:
        scope = bounded_update_scope()
        if scope is not None:
            if targets is None:
                return ["제한 구축의 갱신에는 규격 번호를 명시하세요. 저장된 규격·Release 범위에서 실행합니다"]
            bounded_spec_targets(scope, config.wg_name, pipeline, targets)
            # 최초 구축 manifest와 실행 checkpoint는 불변이다. Phase-11의
            # canonical source 교체·WG 전체 재파싱을 그 상태에 바로 반영하면
            # 검증 입력·KG·VDB가 서로 다른 generation을 가리키게 된다.
            # 이 사전 검사에는 dry_run 계약이 없으므로 상위 dry-run도 함께 거절한다.
            return ["제한 구축의 Phase-11 적재는 새 원문 generation·KG/VDB 검증 기록이 연결된 "
                    "갱신 경로가 필요합니다. 현재 자료와 최초 manifest를 보존합니다. "
                    "판본 목록은 TS-0 수집기의 명시 대상 dry-run으로 확인하고, 새 구축은 별도 빈 설치 위치에서 진행하세요"]
    except (OSError, ValueError, RuntimeError) as exc:
        return [f"구축 범위 계약을 확인하지 못했습니다: {exc}"]
    if task_num == 0:
        return []
    errors = []
    try:
        uri = urlsplit(config.neo4j_uri)
        valid_uri = (uri.scheme in {"bolt", "bolt+s", "bolt+ssc", "neo4j", "neo4j+s", "neo4j+ssc"}
                     and bool(uri.hostname) and uri.username is None and uri.password is None
                     and uri.path in {"", "/"} and not uri.query and not uri.fragment
                     and (uri.port is None or 1 <= uri.port <= 65535))
    except (TypeError, ValueError):
        valid_uri = False
    if not valid_uri:
        errors.append("neo4j_uri: 자격증명이 없는 Neo4j 주소를 지정하세요. 포트를 명시하면 1~65535 범위여야 합니다")
    if valid_uri:
        # bolt/neo4j 계열 스킴과 loopback 표기가 달라도 같은 로컬 DB에 연결된다.
        # 원격 사용자 지정 주소의 동일 포트는 별도 인스턴스일 수 있으므로 허용한다.
        local_host = uri.hostname.rstrip(".").lower() == "localhost"
        try:
            address = ip_address(uri.hostname)
            mapped = getattr(address, "ipv4_mapped", None)
            local_host = local_host or (mapped or address).is_loopback
        except ValueError:
            pass
        if local_host and any((uri.port if uri.port is not None else 7687) == axis.bolt_port(wg)
                              for wg in axis.wgs_of("RAN") if wg != config.wg_name):
            errors.append("neo4j_uri: 다른 WG의 기본 인스턴스 대신 현재 WG의 DB 주소를 지정하세요")
    if not isinstance(config.neo4j_user, str) or not config.neo4j_user.strip():
        errors.append("neo4j_user: 비어 있지 않은 계정 이름을 지정하세요")
    if not isinstance(config.neo4j_password, str) or not config.neo4j_password:
        errors.append("neo4j_password: 비어 있지 않은 비밀번호를 지정하세요")
    if config.neo4j_database != "neo4j":
        errors.append("neo4j_database: 하위 TS 적재기와 같은 neo4j 데이터베이스를 사용하세요")
    if (not isinstance(config.qdrant_host, str) or not config.qdrant_host.strip()
            or "://" in config.qdrant_host or "/" in config.qdrant_host):
        errors.append("qdrant_host: URL 대신 호스트 이름이나 IP 주소를 지정하세요")
    if type(config.qdrant_port) is not int or not 1 <= config.qdrant_port <= 65535:
        errors.append("qdrant_port: 1~65535 범위의 정수 포트를 지정하세요")
    collection = getattr(config, f"{pipeline}_collection")
    # 저장소 기본 컬렉션은 이메일·TDoc·보조 자료도 각자의 페이로드 계약을 갖는다.
    # 사용자 설정으로 추가한 새 이름은 허용하고 기존 기본 컬렉션의 재목적 사용은 막는다.
    expected = axis.qdrant_collection(config.wg_name, {
        "ts": "ts_sections", "cr": "cr_chunks", "tr": "tr_sections"}[pipeline])
    if collection != expected and isinstance(collection, str) and collection in BUILTIN_COLLECTIONS:
        errors.append("컬렉션: 다른 WG·자료 유형의 기본 컬렉션 대신 해당 파이프라인용 컬렉션을 지정하세요")
    try:
        require_local(collection)
    except (ValueError, TypeError):
        errors.append(f"{pipeline}_collection: 로컬 임베딩 레지스트리에 등록된 컬렉션을 지정하세요")
    return errors


def qdrant_http_url(host: str, port: int) -> str:
    """검증된 Qdrant 호스트·포트에서 HTTP 주소를 만든다. IPv6는 대괄호로 감싼다."""
    url_host = f"[{host}]" if ":" in host and not host.startswith("[") else host
    return f"http://{url_host}:{port}"


def child_environment(config) -> dict[str, str]:
    """검증된 Phase-11 설정을 자식 프로세스에 명시적으로 전달한다.

    현재 셸은 변경하지 않는다. WG 표식이 있어야 하위 적재기가 사용자 지정
    연결 주소를 사용하므로 다른 WG에 남은 NEO4J_URI가 유입되지 않는다.
    비밀번호는 명령 인자나 로그 대신 프로세스 환경으로 전달한다.
    """
    wg = getattr(config, "wg_name", None) or config.wg
    env = dict(os.environ)
    env.update({
        "SPECTRA_UPDATE_WG": wg,
        "NEO4J_URI": config.neo4j_uri,
        "NEO4J_USER": config.neo4j_user,
        "NEO4J_PASSWORD": config.neo4j_password,
        "NEO4J_DATABASE": config.neo4j_database,
        "QDRANT_HOST": config.qdrant_host,
        "QDRANT_PORT": str(config.qdrant_port),
        "QDRANT_URL": qdrant_http_url(config.qdrant_host, config.qdrant_port),
    })
    for family in ("ts", "cr", "tr"):
        value = getattr(config, f"{family}_collection", None)
        if value is not None:
            env[f"SPECTRA_{family.upper()}_COLLECTION"] = value
    return env


def child_neo4j_uri(wg: str, default: str) -> str:
    """같은 WG의 갱신 명령이 넘긴 주소만 사용하고, 일반 실행은 기본값을 쓴다."""
    return os.environ["NEO4J_URI"] if os.environ.get("SPECTRA_UPDATE_WG") == wg else default


def child_qdrant_settings(wg: str, default_collection: str) -> tuple[str, int, str]:
    """CR 하위 적재기의 기본 설정과 갱신 명령의 명시 설정을 구분한다."""
    if os.environ.get("SPECTRA_UPDATE_WG") != wg:
        return "localhost", 6333, default_collection
    return (os.environ["QDRANT_HOST"], int(os.environ["QDRANT_PORT"]),
            os.environ["SPECTRA_CR_COLLECTION"])
