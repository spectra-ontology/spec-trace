#!/usr/bin/env python3
"""TSG·WG별 경로와 로컬 DB 인스턴스를 선언하는 공용 레지스트리.

폴더 접두, 포트, 컨테이너·볼륨 이름은 아래 표에서 읽는다. 경로 생성·해석은
TREE_LAYOUT을 공유하며 ScanLedger는 검사 기대 범위와 실제 관측 범위를 기록한다.
회의 식별자 정규화는 phase-10/core/config_loader.py, TS 시리즈 발견은 ts_series가 맡는다.
설계: docs/common/improvement-plans/tsg_axis_design.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# ──────────────────────────────────────────────────────────────
# 프로젝트 루트 (CLAUDE.md §5.6 규범 형태)
# ──────────────────────────────────────────────────────────────

PROJECT_ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())


# ──────────────────────────────────────────────────────────────
# TSG 레지스트리
# ──────────────────────────────────────────────────────────────

TSG_REGISTRY: dict[str, dict] = {
    "RAN": {"plenary": "TSG_RAN", "ftp_root": "tsg_ran",
            "wgs": ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5")},
}

VALID_TSGS: tuple[str, ...] = tuple(TSG_REGISTRY)

#: `docs/tsg/build`처럼 여러 TSG에 공통으로 적용되는 문서 디렉터리 이름.
#: TSG 등록과 구분하며 `tree_path(..., head="build")`로 경로를 만든다.
#: `tree_parse`는 이 디렉터리를 읽으면 `tsg` 대신 `head` 키를 반환한다.
TSG_HEADS: tuple[str, ...] = ("build",)


# ──────────────────────────────────────────────────────────────
# WG 레지스트리
# ──────────────────────────────────────────────────────────────
#
# `meeting_folder_prefixes`는 한 WG에서 사용하는 여러 폴더 접두사를 담는다.
# RAN5의 `TSGR5_`와 `TSGR5__`를 모두 인식하며 첫 원소를 기본 표기로 사용한다.

#: 인스턴스 레코드의 호스트 포트 필드. 포트 중복 검사는 이 목록을 사용한다.
_PORT_FIELDS: tuple[str, ...] = ("bolt", "http")


#: Neo4j 이미지의 기본 import 디렉터리. 새 인스턴스는 이 경로를 사용한다.
#: 다른 경로를 사용하려면 컨테이너 재생성 후에도 유지되는 설정과 마운트가 필요하다.
NEO4J_IMPORT_ROOT_DEFAULT = "/var/lib/neo4j/import"


def _neo4j(bolt: int, http: int, container: str, *,
           data_volume: str, logs_volume: str, import_root: str) -> dict:
    """한 파티션의 포트·컨테이너·볼륨·import 경로를 함께 반환한다.

    기존 인스턴스의 이름 규칙이 서로 달라 각 값을 명시적으로 선언한다.
    볼륨 이름이 달라지면 Docker가 새 빈 볼륨을 만들 수 있으므로 재생성 시에도
    같은 레코드를 사용한다. `provision_neo4j_instance.py`는 `import_root`를
    컨테이너 환경변수로 전달하고, `import_url`은 그 디렉터리 기준 URL을 만든다.
    """
    return {"bolt": bolt, "http": http, "container": container,
            "data_volume": data_volume, "logs_volume": logs_volume,
            "import_root": import_root}


def _wg(tsg: str, tdoc: str, folders: tuple[str, ...], ftp: str,
        neo4j: dict | None = None, *, qdrant_prefix: str | None = None) -> dict:
    """WG별 접두사·FTP 경로·DB 선언을 반환한다.

    `qdrant_prefix`는 컬렉션 이름의 접두사다. TSG_RAN은 `tsgran_*`를 사용하므로
    `wg.lower()`로 계산하지 않고 레지스트리에 명시한다.
    """
    return {"tsg": tsg, "tdoc_prefix": tdoc, "meeting_folder_prefixes": folders,
            "ftp_dir": ftp, "neo4j": neo4j, "qdrant_prefix": qdrant_prefix}


WG_REGISTRY: dict[str, dict] = {
    # TSG_RAN
    "RAN1":    _wg("RAN", "R1-", ("TSGR1_",), "WG1_RL1",
                   _neo4j(7687, 7474, "neo4j-tdoc",
                          data_volume="neo4j_neo4j-data", logs_volume="neo4j_neo4j-logs",
                          import_root="/import"),
                   qdrant_prefix="ran1"),
    "RAN2":    _wg("RAN", "R2-", ("TSGR2_",), "WG2_RL2",
                   _neo4j(7688, 7475, "neo4j-tdoc-ran2",
                          data_volume="neo4j-ran2_neo4j-data-ran2",
                          logs_volume="neo4j-ran2_neo4j-logs-ran2",
                          import_root="/import"),
                   qdrant_prefix="ran2"),
    "RAN3":    _wg("RAN", "R3-", ("TSGR3_",), "WG3_Iu",
                   _neo4j(7689, 7476, "neo4j-tdoc-ran3",
                          data_volume="neo4j-ran3_neo4j-data-ran3",
                          logs_volume="neo4j-ran3_neo4j-logs-ran3",
                          import_root="/import"),
                   qdrant_prefix="ran3"),
    "RAN4":    _wg("RAN", "R4-", ("TSGR4_",), "WG4_Radio",
                   _neo4j(7690, 7477, "neo4j-tdoc-ran4",
                          data_volume="neo4j-ran4_neo4j-ran4-data",
                          logs_volume="neo4j-ran4_neo4j-ran4-logs",
                          import_root=NEO4J_IMPORT_ROOT_DEFAULT),
                   qdrant_prefix="ran4"),
    "RAN5":    _wg("RAN", "R5-", ("TSGR5_", "TSGR5__"), "WG5_Test_ex-T1",
                   _neo4j(7691, 7478, "neo4j-tdoc-ran5",
                          data_volume="neo4j-ran5_neo4j-ran5-data",
                          logs_volume="neo4j-ran5_neo4j-ran5-logs",
                          import_root=NEO4J_IMPORT_ROOT_DEFAULT),
                   qdrant_prefix="ran5"),
    "TSG_RAN": _wg("RAN", "RP-", ("TSGR_",), "TSG_RAN",
                   _neo4j(7692, 7479, "neo4j-tdoc-tsgran",
                          data_volume="neo4j_neo4j-tsgran-data",
                          logs_volume="neo4j_neo4j-tsgran-logs",
                          import_root=NEO4J_IMPORT_ROOT_DEFAULT),
                   qdrant_prefix="tsgran"),
}

def _reject_shared_instance_ports(registry: dict[str, dict]) -> None:
    """서로 다른 인스턴스나 프로토콜이 같은 호스트 포트를 선언하면 거절한다.

    Bolt와 HTTP를 함께 검사해 두 필드 사이의 중복도 확인한다. 모듈을 읽을 때
    실행하므로 잘못된 포트 선언으로 다른 파티션에 접속하기 전에 실패한다.
    """
    claimed: dict[int, str] = {}
    for wg, rec in registry.items():
        inst = rec["neo4j"]
        if inst is None:
            continue
        for port_field in _PORT_FIELDS:
            port = inst[port_field]
            owner = f"{wg}.{port_field}"
            if port in claimed:
                raise ValueError(
                    f"Neo4j 포트 {port} 을 {claimed[port]} 와 {owner} 가 함께 선언했다 — "
                    f"겹친 포트는 연결에 실패하지 않고 남의 그래프 답을 돌려준다"
                )
            claimed[port] = owner


_reject_shared_instance_ports(WG_REGISTRY)


#: TSG 전체회의를 제외한 실무 WG 목록.
VALID_WGS: tuple[str, ...] = tuple(w for t in VALID_TSGS for w in TSG_REGISTRY[t]["wgs"])

#: TSG 전체회의를 포함한 전체 파티션. 경로 함수는 이 이름들을 사용한다.
ALL_PARTITIONS: tuple[str, ...] = tuple(WG_REGISTRY)

#: WG별 디렉터리와 같은 위치에 있는 공용 디렉터리 이름.
#: 예: `scripts/tsg/{TSG}/{track}/common`. 소속 TSG를 이름에서 정할 수 없으므로
#: 이 이름을 사용하는 `tree_path` 호출에는 `tsg`도 전달한다.
WG_SEGMENT_ALIASES: tuple[str, ...] = ("common",)

#: 파티션별 경로를 만드는 호출은 `tree_path(wg=...)`에 대상을 명시한다.
#: WG를 빠뜨린 실행이 특정 파티션의 파일을 읽거나 쓰는 기본값은 두지 않는다.


class UnassignedInstance(LookupError):
    """그 파티션에는 아직 인프라가 배정되지 않았다. 기본값으로 흡수하지 않는다."""


class UnknownPartition(KeyError):
    """레지스트리에 없는 WG/TSG. 조용히 빈 결과를 내지 않기 위해 예외로 낸다."""


def tsg_of(wg: str) -> str:
    """WG 레지스트리에 선언된 소속 TSG를 반환한다."""
    try:
        return WG_REGISTRY[wg]["tsg"]
    except KeyError:
        raise UnknownPartition(f"레지스트리에 없는 파티션: {wg!r}. 알려진 값 = {ALL_PARTITIONS}") from None


def wgs_of(tsg: str, *, include_plenary: bool = False) -> tuple[str, ...]:
    if tsg not in TSG_REGISTRY:
        raise UnknownPartition(f"레지스트리에 없는 TSG: {tsg!r}. 알려진 값 = {VALID_TSGS}")
    wgs = TSG_REGISTRY[tsg]["wgs"]
    return wgs + (TSG_REGISTRY[tsg]["plenary"],) if include_plenary else wgs


def wgs_in(tsgs, *, include_plenary: bool = False) -> tuple[str, ...]:
    """선택한 TSG에 속한 WG를 선언 순서대로 반환한다.

    `include_plenary=True`이면 각 TSG 전체회의도 포함한다.
    검사기는 적용할 TSG를 선언하고 WG 목록은 이 함수에서 얻는다.
    """
    return tuple(w for t in tsgs for w in wgs_of(t, include_plenary=include_plenary))


def plenary_of(tsg: str) -> str:
    if tsg not in TSG_REGISTRY:
        raise UnknownPartition(f"레지스트리에 없는 TSG: {tsg!r}")
    return TSG_REGISTRY[tsg]["plenary"]


# ──────────────────────────────────────────────────────────────
# 3GPP FTP 축
# ──────────────────────────────────────────────────────────────
#
# `ftp_dir`은 WG 번호로 계산하지 않고 서버의 디렉터리 이름을 선언한다.
# 예: `WG3_Iu`, `WG4_Radio`, `WG5_Test_ex-T1`.

#: 3GPP 문서 서버의 루트. 이 아래로만 URL 을 조립한다.
FTP_BASE = "https://www.3gpp.org/ftp"


def ftp_root(tsg: str) -> str:
    """`FTP_BASE` 바로 아래 TSG 세그먼트(`tsg_ran`)."""
    if tsg not in TSG_REGISTRY:
        raise UnknownPartition(f"레지스트리에 없는 TSG: {tsg!r}")
    return TSG_REGISTRY[tsg]["ftp_root"]


def ftp_dir(wg: str) -> str:
    """그 파티션의 FTP 디렉토리명. 이름에서 짓지 않는다 — 실측 선언이다."""
    if wg not in WG_REGISTRY:
        raise UnknownPartition(f"레지스트리에 없는 파티션: {wg!r}")
    return WG_REGISTRY[wg]["ftp_dir"]


def ftp_url(wg: str, *segments: str, trailing_slash: bool = False) -> str:
    """선택한 파티션의 FTP URL에 추가 경로를 연결한다.

        ftp_url("RAN1")                              → …/tsg_ran/WG1_RL1
        ftp_url("RAN2", "TSGR2_122", "Docs", trailing_slash=True)
                                                     → …/tsg_ran/WG2_RL2/TSGR2_122/Docs/

    각 세그먼트의 앞뒤 슬래시는 제거하고 `/` 하나로 연결한다.
    `trailing_slash=True`이면 마지막에도 `/`를 붙인다.
    """
    parts = [FTP_BASE, ftp_root(tsg_of(wg)), ftp_dir(wg)]
    parts += [seg.strip("/") for seg in segments if seg.strip("/")]
    url = "/".join(parts)
    return url + "/" if trailing_slash else url


def neo4j_instance(wg: str) -> dict:
    """WG에 배정된 Neo4j 인스턴스 레코드를 반환한다.

    등록되지 않은 WG는 `UnknownPartition`, DB가 배정되지 않은 WG는
    `UnassignedInstance`를 발생시킨다. 포트는 WG 이름으로 계산하지 않는다.
    """
    if wg not in WG_REGISTRY:
        raise UnknownPartition(f"레지스트리에 없는 파티션: {wg!r}")
    inst = WG_REGISTRY[wg]["neo4j"]
    if inst is None:
        raise UnassignedInstance(
            f"{wg} 에는 Neo4j 인스턴스가 아직 배정되지 않았다. "
            f"기본 포트로 넘어가면 남의 그래프에 붙어 부재를 0행으로 읽는다."
        )
    return inst


def bolt_port(wg: str) -> int:
    """드라이버(`neo4j.GraphDatabase`)가 붙는 포트."""
    return neo4j_instance(wg)["bolt"]


def http_port(wg: str) -> int:
    """트랜잭션 REST 엔드포인트(`/db/neo4j/tx/commit`)의 HTTP 포트를 반환한다."""
    return neo4j_instance(wg)["http"]


def _import_relpath(wg: str, phase: int | str) -> str:
    """마운트 대상과 `file:///` URL이 공유하는 import 디렉터리 기준 상대 경로."""
    seg = _phase_segment(phase)
    return f"output/instances/{seg}/{wg}"


def _phase_segment(phase: int | str) -> str:
    """확장 가능한 phase 이름을 경로 한 칸으로 검증한다."""
    if type(phase) is int and phase >= 0:
        return f'phase-{phase}'
    if (isinstance(phase, str) and phase.strip() and phase not in {'.', '..'}
            and '/' not in phase and '\\' not in phase and '\x00' not in phase):
        return phase
    raise TreeGrammarError('phase는 0 이상의 정수 또는 단일 디렉토리 이름이어야 한다')


def import_mount_source(wg: str, phase: int | str) -> Path:
    """WG·Phase별 JSON-LD 인스턴스 디렉터리를 호스트 마운트 원본으로 반환한다."""
    return tree_path("ontology_instances", wg=wg, phase=phase)


def import_mount_target(wg: str, phase: int | str) -> str:
    """컨테이너 쪽 마운트 지점. `import_mount_source` 가 붙을 자리다."""
    return f"{neo4j_instance(wg)['import_root']}/{_import_relpath(wg, phase)}"


def import_url(wg: str, phase: int | str, name: str = "") -> str:
    """`apoc.load.json`에 전달할 import 디렉터리 기준 파일 URL을 반환한다.

    `apoc.import.file.use_neo4j_config=true`에서는 Neo4j의 import 디렉터리를
    기준으로 경로를 해석한다. URL에는 컨테이너의 절대 import 경로를 넣는 대신
    마운트 대상과 공통으로 사용하는 상대 경로를 넣는다.
    """
    base = f"file:///{_import_relpath(wg, phase)}"
    return f"{base}/{name}" if name else base


def bolt_uri(wg: str, host: str = "localhost") -> str:
    return f"bolt://{host}:{bolt_port(wg)}"


def bolt_ports(tsgs=("RAN",), *, include_plenary: bool = False) -> dict[str, int]:
    """선언된 범위의 bolt 포트 지도. `BOLT_PORTS = {...}` 사본들을 대신한다."""
    return {w: bolt_port(w) for w in wgs_in(tsgs, include_plenary=include_plenary)}


def http_ports(tsgs=("RAN",), *, include_plenary: bool = False) -> dict[str, int]:
    """선언된 범위의 HTTP 포트 지도. `PORTS = {"RAN1": 7474, …}` 사본들을 대신한다."""
    return {w: http_port(w) for w in wgs_in(tsgs, include_plenary=include_plenary)}


def qdrant_collection(wg: str, family: str) -> str:
    """WG 접두사와 컬렉션 유형(`tr_sections` 등)에 해당하는 등록 이름을 반환한다.

    `embedding_registry.COLLECTION_ENCODER`에 없는 유형은 `UnknownPartition`으로
    거절한다. WG별 지원 유형은 `qdrant_collections`에서 확인한다.
    """
    built = qdrant_collections(wg)
    if family not in built:
        raise UnknownPartition(
            f"{wg} 에 지어진 Qdrant 컬렉션 가족이 아니다: {family!r}. "
            f"선언된 가족 = {tuple(sorted(built))}"
        )
    return built[family]


def qdrant_collections(wg: str) -> dict[str, str]:
    """WG의 등록 컬렉션을 `{컬렉션 유형: 전체 이름}` 형식으로 반환한다.

    목록을 중복 선언하지 않고 `embedding_registry.COLLECTION_ENCODER`에서
    WG 접두사가 일치하는 항목을 고른다. 해당 레지스트리는 호출 시 가져온다.
    """
    if wg not in WG_REGISTRY:
        raise UnknownPartition(f"레지스트리에 없는 파티션: {wg!r}")
    prefix = WG_REGISTRY[wg]["qdrant_prefix"]
    if prefix is None:
        raise UnassignedInstance(f"{wg} 에는 Qdrant 컬렉션 앞머리가 아직 선언되지 않았다.")
    if __package__:
        from .embedding_registry import COLLECTION_ENCODER
    else:
        from embedding_registry import COLLECTION_ENCODER
    head = f"{prefix}_"
    return {name[len(head):]: name for name in COLLECTION_ENCODER if name.startswith(head)}


def tdoc_prefix(wg: str) -> str:
    """`R1-` · `S2-` · `C1-` · `RP-`. 이름을 잘라 짓지 않는다 — 실측 선언이다."""
    if wg not in WG_REGISTRY:
        raise UnknownPartition(f"레지스트리에 없는 파티션: {wg!r}")
    return WG_REGISTRY[wg]["tdoc_prefix"]


def tdoc_pattern(wg: str) -> re.Pattern[str]:
    """그 WG 의 TDoc 번호 정규식. `rf"^R{wg[3:]}-…"` 를 대신한다."""
    return re.compile(rf"^{re.escape(tdoc_prefix(wg))}\d+$", re.IGNORECASE)


def meeting_folder_prefixes(wg: str) -> tuple[str, ...]:
    """WG의 회의 폴더 접두사들을 반환한다. 첫 원소는 기본 표기다."""
    if wg not in WG_REGISTRY:
        raise UnknownPartition(f"레지스트리에 없는 파티션: {wg!r}")
    return WG_REGISTRY[wg]["meeting_folder_prefixes"]


def strip_meeting_prefix(folder_name: str, wg: str) -> str | None:
    """WG 접두사를 제외한 회의 폴더 이름을 반환한다. 일치하는 접두사가 없으면 None.

    긴 접두사부터 비교해 `TSGR5__`가 `TSGR5_`로 부분 인식되는 것을 방지한다.
    """
    for pre in sorted(meeting_folder_prefixes(wg), key=len, reverse=True):
        if folder_name.upper().startswith(pre.upper()):
            return folder_name[len(pre):]
    return None


# ──────────────────────────────────────────────────────────────
# 트리 문법 — 트리마다 세그먼트 순서가 다르다는 사실을 여기 한 곳에 적는다
# ──────────────────────────────────────────────────────────────
#
# 값은 `(기준 디렉터리, 경로 세그먼트 순서)`다.
# 변수 세그먼트는 인자로 채우고, `=`로 시작하는 고정 세그먼트는 그대로 사용한다.
# 예를 들어 `=tsg`는 디렉터리 이름이고 `tsg`는 RAN 등의 인자다.
# `ontology_instances`는 phase가 wg보다 앞에 오며, `vectordb_parsed`는 TSG 층이 없다.
# 경로 생성과 해석이 모두 이 표를 사용해 같은 구조를 따른다.

TREE_LAYOUT: dict[str, tuple[str, tuple[str, ...]]] = {
    "corpus":               ("data/corpus",          ("=tsg", "tsg", "track", "doc_type", "wg", "slot")),
    "docs":                 ("docs",                 ("=tsg", "tsg", "track", "wg", "phase")),
    "scripts":              ("scripts",              ("=tsg", "tsg", "track", "wg", "phase")),
    "logs":                 ("logs",                 ("=tsg", "tsg", "track", "wg", "phase")),
    "logs_common":          ("logs/common",          ("wg",)),
    "ontology_config":      ("ontology/config",      ("=tsg", "tsg", "track", "wg")),
    "ontology_input":       ("ontology/input",       ("=tsg", "tsg", "track", "doc_type", "wg")),
    "ontology_intermediate": ("ontology/intermediate", ("=tsg", "tsg", "track", "wg")),
    "ontology_output":      ("ontology/output",      ("=tsg", "tsg", "track", "doc_type", "wg")),
    "ontology_instances":   ("ontology/output",      ("=tsg", "tsg", "track", "=instances", "phase", "wg")),
    "vectordb_parsed":      ("vectordb/parsed",      ("doc_type", "wg")),
}

#: `data/corpus` 의 마지막 층. 추출 전/후를 가른다.
SLOTS = ("source", "derived")

#: 축 트리의 두 번째 층. `domain-vocab` 은 WG 로 나뉘지 않는다 —
#: 그래서 `tree_path` 는 뒤 세그먼트 생략을 허용한다.
TRACKS = ("formal", "email", "domain-vocab")

#: 트리별 문서 유형 이름. 원본 코퍼스의 `change-requests`, 온톨로지 입력의 `CR`,
#: 파싱 결과의 `cr`을 구분하며 `tree_path`가 해당 트리의 허용값을 검사한다.
DOC_TYPES_BY_TREE: dict[str, tuple[str, ...]] = {
    "corpus":          ("meetings", "change-requests", "TS", "TR"),
    "ontology_input":  ("meetings", "TS", "TR", "CR"),
    # `instances` 는 디스크의 같은 층에 있지만 여기 넣지 않는다 — 그 아래는 WG 가 아니라
    # `phase-N` 이 먼저 온다(`ontology_instances` 문법). 층 이름이 같다고 어휘에 넣으면
    # `ontology_output` + `"instances"` 가 `…/instances/RAN1` 이라는 없는 경로를 만든다.
    "ontology_output": ("parsed_reports", "parsed_ts", "parsed_tr", "parsed_cr",
                        "charts", "figures", "tables"),
    "vectordb_parsed": ("tdocs", "ts", "tr", "cr"),
}

#: 트랙별 문서 유형 예외. 빈 튜플이면 해당 경로에 doc_type 층이 없다는 뜻이다.
#: 이메일 코퍼스는 `data/corpus/tsg/RAN/email/RAN2/source`처럼 바로 WG가 이어진다.
#: `tree_path`는 이 경우 doc_type을 생략하고, 호출자가 값을 주면 거절한다.
DOC_TYPES_BY_TRACK: dict[tuple[str, str], tuple[str, ...]] = {
    ("corpus", "email"): (),
}

# ---------------------------------------------------------------------------
# 기능 축 (`docs/` 최상위에서 파티션 축이 아닌 것)
# ---------------------------------------------------------------------------
#
# `check_directory_policy`가 사용하는 문서 분류 기준이다.
# TSG·WG별 구축 문서는 `tsg/`, 사용자 기능은 `capability/`, 공통 규약은 `common/`,
# 외부 독자를 위한 자료는 `publication/`에 둔다. 각 분류 아래의 종류는 별도로 선언한다.
# `docs/tsg/build`는 TSG 공통 구축 문서이며 `TSG_HEADS`와 `KINDS_BY_PATH`가 정의한다.

#: 기능별 문서의 적용 범위를 판별하는 질문.
FUNCTIONAL_AXES: dict[str, str] = {
    "capability":  "범위가 SPECTRA 가 사용자에게 하는 일 하나인가 (그 일의 부품을 자기 안에 갖는가)",
    "common":      "범위가 저장소 전체인가 (소비처가 두 일 이상에 걸치는가)",
    "publication": "범위가 저장소 밖 독자인가 (심사위원 · 특허청 · 사용자 · 평가자)",
}

#: `docs/` 기준 경로별 하위 종류 디렉터리 이름.
#: 검사기는 선언된 경로의 구조를 확인하고, 개별 문서·사례가 저장되는 내부까지는
#: 이 목록으로 제한하지 않는다. 새 종류 디렉터리를 추가할 때 이 선언도 갱신한다.
KINDS_BY_PATH: dict[str, tuple[str, ...]] = {
    # 축 뿌리
    "capability":  ("answer", "feature-planning"),
    "common":      ("baselines", "improvement-plans", "process", "standards"),
    "publication": ("paper", "patent", "performance-review", "release-notes"),
    # TSG 공통 구축 문서(`TSG_HEADS`)의 하위 종류.
    "tsg/build":   ("improvement-plans", "known-limitations", "phase-0", "process", "standards"),
    # 사용자 기능별 구성 요소.
    "capability/answer":           ("cases", "evaluation", "flywheel", "reports", "standards"),
    "capability/answer/cases":      ("CP_SW_team", "CP_modem_team", "sr_standards_board"),
    "capability/answer/evaluation": ("answers", "evaluations", "feedback", "questions"),
    "capability/answer/flywheel":   ("cycles", "lessons", "process", "system-architecture"),
    # 기능 기획의 사례·개선 기록·작업 단계.
    "capability/feature-planning":          ("cases", "flywheel", "steps"),
    "capability/feature-planning/cases":    ("LTM_probe",),
    "capability/feature-planning/flywheel": ("audits", "cycles", "lessons", "process"),
    # publication/ 안쪽
    # ongoing은 준비 중인 트랙, history는 제출이나 작업을 마치고 보존하는 트랙이다.
    "publication/paper":              ("ongoing", "history"),
    "publication/paper/ongoing":      ("vldb-2027-experiment-analysis-benchmark",),
    # WWW 정본은 소문자이며 대문자 항목은 동결 좌표용 호환 alias이다.
    "publication/paper/history":      ("kdd-2027-datasets-benchmarks", "kdd-2027-research",
                                      "www-2027-research", "WWW-2027-Research",
                                      "www-2027-research-kdd"),
    "publication/patent":             ("drafts", "filed"),
    "publication/performance-review": ("2026",),
}

#: 종류별 하위 폴더 대신 해당 디렉터리에 직접 둘 수 있는 예외 파일.
#: `README.md` 외 파일을 직접 둘 때 경로와 허용 사유를 함께 선언한다.
FLAT_EXEMPT_BY_PATH: dict[str, tuple[str, ...]] = {
    # 트랙별 문서로 라우팅하는 최소 제출 안내; 연구·평가는 각 트랙에 둔다.
    "publication/paper": ("publication_plan.md",),
    # 출원 단계별 문서와 구분되는 공통 작성 지침 및 후보 목록.
    "publication/patent": ("invention_disclosure_guide.md", "patent_idea.md"),
}


_VARIABLE_SEGMENTS = ("tsg", "track", "wg", "doc_type", "phase", "slot")


class TreeGrammarError(ValueError):
    """트리 문법이 요구하는 세그먼트가 빠졌다. 조용히 짧은 경로를 만들지 않는다."""


def tree_path(
    tree: str,
    *,
    wg: str | None = None,
    tsg: str | None = None,
    head: str | None = None,
    track: str | None = "formal",
    doc_type: str | None = None,
    phase: int | str | None = None,
    slot: str | None = None,
    root: Path | None = None,
) -> Path:
    """`TREE_LAYOUT` 이 선언한 문법대로 경로를 조립한다.

    WG를 주면 레지스트리에서 소속 TSG를 얻는다.

        tree_path("corpus", wg="RAN2", doc_type="meetings", slot="source")
        → data/corpus/tsg/RAN/formal/meetings/RAN2/source

        tree_path("ontology_instances", wg="RAN1", phase=1)
        → ontology/output/tsg/RAN/formal/instances/phase-1/RAN1

    `head`는 `build` 같은 TSG 공통 디렉터리를 선택한다. `tsg`·`wg`와 함께
    지정할 수 없으며, 그 아래의 종류는 `KINDS_BY_PATH`에서 정의한다.

        tree_path("docs", head="build")
        → docs/tsg/build

    뒤쪽 세그먼트를 생략해 상위 디렉토리를 얻는 것은 정상 용법이다. **중간만**
    비우는 것은 막는다 — 그러면 뒤 값이 앞자리로 밀려 다른 곳을 가리킨다.
    """
    if tree not in TREE_LAYOUT:
        raise TreeGrammarError(f"문법이 선언되지 않은 트리: {tree!r}. 알려진 값 = {tuple(TREE_LAYOUT)}")
    if head is not None:
        # TSG 공통 디렉터리는 파티션이 아니므로 전용 인자로 검사한다.
        if head not in TSG_HEADS:
            raise TreeGrammarError(f"알 수 없는 head: {head!r}. 알려진 값 = {TSG_HEADS}")
        if tsg is not None or wg is not None:
            raise TreeGrammarError(
                f"head={head!r} 는 파티션 자리에 서는 파티션-독립 머리라 tsg·wg 와 함께 올 수 없다"
            )
        if doc_type is not None or phase is not None or slot is not None:
            raise TreeGrammarError(
                f"head={head!r} 아래에는 doc_type·phase·slot 문법이 없다 — "
                f"머리의 종류 층은 `KINDS_BY_PATH` 가 선언한다"
            )
        base, segments = TREE_LAYOUT[tree]
        path = (root or PROJECT_ROOT).joinpath(*base.split("/"))
        for seg in segments:
            if seg.startswith("="):
                path = path / seg[1:]
                continue
            if seg != "tsg":
                raise TreeGrammarError(
                    f"{tree!r} 의 첫 변수 칸은 {seg!r} 이므로 TSG 머리를 세울 수 없다"
                )
            return path / head
        raise TreeGrammarError(f"{tree!r} 에는 파티션 층이 없어 머리를 세울 자리가 없다")
    if wg is not None:
        if wg in WG_SEGMENT_ALIASES:
            if tsg is None:
                raise TreeGrammarError(
                    f"{wg!r} 는 파티션이 아니라 WG 공용 자리 이름이라 TSG 를 유도할 수 없다"
                    f" — `tsg` 를 함께 준다"
                )
        else:
            wg_tsg = tsg_of(wg)  # 레지스트리에 없으면 UnknownPartition
            if tsg is None:
                tsg = wg_tsg
            elif tsg != wg_tsg:
                # 둘 다 받은 값을 검사 없이 이으면 `corpus/{다른 TSG}/formal/…/RAN1` 처럼
                # 구조는 멀쩡하고 실재하지 않는 교차 TSG 경로가 만들어진다.
                raise TreeGrammarError(
                    f"tsg={tsg!r} 와 wg={wg!r} 가 어긋난다 — {wg} 의 TSG 는 {wg_tsg!r} 다"
                )
    # 등록된 인자 값을 검사한다. phase는 고정 목록으로 제한하지 않고
    # _phase_segment에서 음이 아닌 정수 또는 단일 디렉터리 이름인지 확인한다.
    if track is not None and track not in TRACKS:
        raise TreeGrammarError(f"알 수 없는 track: {track!r}. 알려진 값 = {TRACKS}")
    if tsg is not None and tsg not in VALID_TSGS:
        raise TreeGrammarError(f"알 수 없는 tsg: {tsg!r}. 알려진 값 = {VALID_TSGS}")
    if slot is not None and slot not in SLOTS:
        raise TreeGrammarError(
            f"알 수 없는 slot: {slot!r}. 알려진 값 = {SLOTS} — 옛 이름 `work` 는 `derived` 로"
            f" 개명됐고, 개명 전 이름을 넣으면 지금은 없는 자리를 가리킨다"
        )
    if doc_type is not None:
        known = DOC_TYPES_BY_TRACK.get((tree, track), DOC_TYPES_BY_TREE.get(tree))
        if known is None:
            raise TreeGrammarError(
                f"{tree!r} 에는 doc_type 층이 없는데 {doc_type!r} 가 들어왔다 — "
                f"조용히 무시하면 호출부는 그 값이 경로에 박힌 줄 안다"
            )
        if not known:
            raise TreeGrammarError(
                f"{tree!r} 의 {track!r} 트랙에는 doc_type 층이 없는데 {doc_type!r} 가 "
                f"들어왔다 — 이 트랙의 경로는 지금 문법으로 표현되지 않는다. 그대로 "
                f"조립하면 없는 경로가 만들어진다"
            )
        if doc_type not in known:
            raise TreeGrammarError(
                f"{tree!r} 의 doc_type 어휘가 아니다: {doc_type!r}. 알려진 값 = {known}. "
                f"트리마다 어휘가 다르므로 다른 트리의 값을 넣으면 없는 경로가 만들어진다"
            )

    supplied = {
        "tsg": tsg,
        "track": track,
        "wg": wg,
        "doc_type": doc_type,
        "slot": slot,
        "phase": None if phase is None else _phase_segment(phase),
    }

    base, segments = TREE_LAYOUT[tree]
    path = (root or PROJECT_ROOT).joinpath(*base.split("/"))
    for idx, seg in enumerate(segments):
        if seg.startswith("="):
            path = path / seg[1:]
            continue
        if seg == "doc_type" and DOC_TYPES_BY_TRACK.get((tree, track)) == ():
            continue
        value = supplied[seg]
        if value is None:
            rest = [s for s in segments[idx:] if not s.startswith("=")]
            if any(supplied[s] is not None for s in rest):
                raise TreeGrammarError(
                    f"{tree!r} 문법 {segments} 에서 {seg!r} 가 비었는데 뒤 세그먼트가 "
                    f"채워져 있다 — 중간 생략은 뒤 값을 앞자리로 밀어 다른 곳을 가리킨다"
                )
            break
        path = path / str(value)
    return path


def tree_root(tree: str, *, root: Path | None = None) -> Path:
    """첫 변수 세그먼트 바로 위의 공통 경로를 반환한다.

    `TREE_LAYOUT` 의 base 와, 그 뒤에 잇달아 오는 리터럴 세그먼트(`"=tsg"` 처럼
    `=` 로 시작하는 것)까지를 합친다. 첫 변수 세그먼트를 만나면 멈춘다.

        tree_root("corpus")  → data/corpus/tsg
        tree_root("ontology_config") → ontology/config/tsg
        tree_root("vectordb_parsed") → vectordb/parsed      (앞에 리터럴이 없다)

    반환 경로에서 파티션 탐색을 시작할 수 있다. 저장 기준 경로와 탐색 시작
    경로가 다를 수 있으므로 `data/corpus` 같은 문자열을 호출부에 직접 쓰는 대신
    이 함수로 고정 세그먼트까지 포함한 경로를 얻는다.
    """
    if tree not in TREE_LAYOUT:
        raise TreeGrammarError(f"문법이 선언되지 않은 트리: {tree!r}. 알려진 값 = {tuple(TREE_LAYOUT)}")
    base, segments = TREE_LAYOUT[tree]
    path = (root or PROJECT_ROOT).joinpath(*base.split("/"))
    for seg in segments:
        if not seg.startswith("="):
            break
        path = path / seg[1:]
    return path


def tree_parse(
    tree: str,
    path: Path | str,
    *,
    root: Path | None = None,
) -> dict[str, object] | None:
    """`tree_path` 의 역 — 경로에서 그 트리가 선언한 세그먼트를 읽어 낸다.

    경로 생성과 동일한 `TREE_LAYOUT`을 사용해 각 디렉터리의 역할을 해석한다.

        tree_parse("corpus", "data/corpus/tsg/RAN/formal/meetings/RAN4/source/TSGR4_118/Docs/R4-2600913.zip")
        → {"tsg": "RAN", "track": "formal", "doc_type": "meetings", "wg": "RAN4",
           "slot": "source", "rest": ("TSGR4_118", "Docs", "R4-2600913.zip")}

    TSG 공통 디렉터리(`TSG_HEADS`)는 `head` 키로 반환하고 나머지는 `rest`에 담는다.

        tree_parse("docs", "docs/tsg/build/standards/extraction_policy.md")
        → {"head": "build", "rest": ("standards", "extraction_policy.md")}

    절대경로는 리포 루트 기준으로, 상대경로는 리포 루트에서 시작하는 것으로
    읽는다. 그 트리 밑이 아니면 `None` — 부재를 빈 값으로 흡수하지 않는다.
    문법보다 짧은 경로는 채워진 세그먼트까지만 담아 돌려준다(상위 디렉토리).
    """
    if tree not in TREE_LAYOUT:
        raise TreeGrammarError(f"문법이 선언되지 않은 트리: {tree!r}. 알려진 값 = {tuple(TREE_LAYOUT)}")

    root_path = root or PROJECT_ROOT
    candidate = Path(path)
    if candidate.is_absolute():
        try:
            parts = candidate.resolve().relative_to(Path(root_path).resolve()).parts
        except ValueError:
            return None
    else:
        parts = candidate.parts

    base, segments = TREE_LAYOUT[tree]
    base_parts = tuple(base.split("/"))
    if parts[: len(base_parts)] != base_parts:
        return None

    rest = parts[len(base_parts):]
    parsed: dict[str, object] = {}
    idx = 0
    for seg in segments:
        if seg == "doc_type" and DOC_TYPES_BY_TRACK.get((tree, parsed.get("track"))) == ():
            continue
        if idx >= len(rest):
            break
        if seg.startswith("="):
            if rest[idx] != seg[1:]:
                return None
            idx += 1
            continue
        if seg == "tsg" and rest[idx] in TSG_HEADS:
            # TSG 공통 디렉터리 아래 경로는 트랙·WG로 해석하지 않는다.
            parsed["head"] = rest[idx]
            idx += 1
            break
        parsed[seg] = rest[idx]
        idx += 1
    parsed["rest"] = rest[idx:]
    return parsed


def ts_series(wg: str, *, root: Path | None = None) -> tuple[str, ...] | None:
    """WG의 TS 원본 경로에서 두 자리 시리즈 번호를 찾아 정렬해 반환한다.

    직속 항목 이름이 두 자리 숫자와 '.' 또는 '_'로 시작하면 그 번호를 수집한다.
    경로가 없으면 None, 경로는 있지만 해당 이름이 없으면 빈 튜플을 반환한다.
    """
    d = tree_path("corpus", wg=wg, doc_type="TS", slot="source", root=root)
    if not d.is_dir():
        return None
    out = set()
    for p in d.iterdir():
        m = re.match(r"^(\d{2})[._]", p.name)
        if m:
            out.add(m.group(1))
    return tuple(sorted(out))


# ──────────────────────────────────────────────────────────────
# 대상 0 ≠ 위반 0
# ──────────────────────────────────────────────────────────────


@dataclass
class ScanLedger:
    """예상 검사 대상, 실제 검사 대상, 검사하지 못한 대상과 사유를 기록한다.

    결과 보고에서 검사 대상이 0개인 실행과 위반이 0개인 실행을 구분한다.
    """

    name: str
    expected: list[str] = field(default_factory=list)
    scanned: list[str] = field(default_factory=list)
    absences: dict[str, str] = field(default_factory=dict)

    def expect(self, key: str) -> None:
        self.expected.append(key)

    def scan(self, key: str) -> None:
        self.scanned.append(key)

    def absent(self, key: str, reason: str) -> None:
        """검사하지 못한 대상의 이름과 사유를 기록한다."""
        self.absences[key] = reason

    @property
    def vacuous(self) -> bool:
        """검사한 항목이 없고 예상 항목이나 대상 부재 기록이 있으면 True를 반환한다.

        예상 항목을 검사하지 못한 경우와 대상 디렉터리가 없어 예상 항목도
        구성하지 못한 경우를 포함한다. 둘 다 검사 통과와 구분해 보고한다.
        """
        return not self.scanned and bool(self.expected or self.absences)

    def report(self) -> str:
        lines = [
            f"[{self.name}] 기대 {len(self.expected)} · 훑음 {len(self.scanned)} · "
            f"부재 {len(self.absences)}"
        ]
        for k, why in sorted(self.absences.items()):
            lines.append(f"  판정 대상 아님: {k} — {why}")
        if self.vacuous:
            lines.append(
                "  🔴 공허: 이 실행은 하나도 훑지 못했다. "
                "이 실행의 '위반 0' 은 '대상 0' 이지 무결성의 증거가 아니다."
            )
        return "\n".join(lines)

    def exit_code(self) -> int:
        return 1 if self.vacuous else 0


# ──────────────────────────────────────────────────────────────
# argparse 헬퍼
# ──────────────────────────────────────────────────────────────


def add_wg_argument(parser, *, include_plenary: bool = False, tsg: str | None = None):
    """등록 파티션 중 하나를 선택하는 필수 `--wg` 인자를 추가한다.

    WG를 생략한 실행이 특정 파티션의 데이터를 처리하지 않도록 기본값을 두지 않는다.
    """
    choices = (wgs_of(tsg, include_plenary=include_plenary) if tsg else
               ALL_PARTITIONS if include_plenary else VALID_WGS)
    parser.add_argument("--wg", type=str, required=True, choices=choices,
                        help="파티션(필수 — 기본값을 두지 않는다)")
    return parser


def add_tsg_argument(parser, default: str | None = None):
    parser.add_argument("--tsg", type=str, default=default, choices=VALID_TSGS,
                        help="TSG 로 범위를 좁힌다 (기본: 전체)")
    return parser


def resolve_scope(tsg: str | None = None, wg: str | None = None, *,
                  include_plenary: bool = False) -> tuple[str, ...]:
    """`--tsg`/`--wg` 조합을 순회 대상으로 편다. 둘 다 없으면 전체."""
    if wg:
        return (wg,)
    if tsg:
        return wgs_of(tsg, include_plenary=include_plenary)
    return ALL_PARTITIONS if include_plenary else VALID_WGS
