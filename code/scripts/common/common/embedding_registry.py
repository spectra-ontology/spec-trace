#!/usr/bin/env python3
"""컬렉션별 임베딩 인코더 설정을 조회하고 로컬 모델로 인코딩한다.

COLLECTION_ENCODER는 컬렉션 이름을 ENCODERS의 모델 설정에 연결한다.
본문과 질의에는 같은 모델 판본과 등록된 문서·질의 처리 규칙을 적용한다. 차원이 같아도 서로 다른
모델로 생성한 벡터는 같은 컬렉션의 검색에 함께 사용하지 않는다.
기본 모델은 로컬 bge-m3이며, SPECTRA_EMBEDDING_CONFIG의 JSON으로
추가 인코더와 새 컬렉션을 등록할 수 있다. 기존 선언은 유지한다.

사용:
    from common.embedding_registry import encoder_for
    enc = encoder_for("ran5_tdoc_chunks")

등록·차원 검사:
    scripts/common/data-integrity/check_embedding_space_declaration.py
    Qdrant 컬렉션의 등록 여부와 단일 벡터 차원을 선언과 대조한다.
    실제 적재에 사용한 모델과 입력 처리의 일치는 구축 기록으로 별도 확인한다."""

from __future__ import annotations

import os
import sys
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

try:
    from .local_model import BGE_M3_REPO, BGE_M3_REVISION
except ImportError:  # flat import를 쓰는 기존 Phase 실행기
    from local_model import BGE_M3_REPO, BGE_M3_REVISION

__all__ = [
    "Encoder",
    "TextPrefixAdapter",
    "ENCODERS",
    "COLLECTION_ENCODER",
    "BUILTIN_COLLECTIONS",
    "encoder_for",
    "local_encoder_for",
    "embed_query_local",
    "load_local_encoder",
    "load_local_tokenizer",
    "local_snapshot_path",
    "force_hf_offline",
    "truncate_to_encoder_budget",
    "embed_local",
    "TRUNCATED",
    "load_registry_config",
]


@dataclass(frozen=True)
class TextPrefixAdapter:
    """동일한 dense 인코더에 전달할 문서·질의 접두사를 명시한다."""

    type: str
    document_prefix: str
    query_prefix: str


@dataclass(frozen=True)
class Encoder:
    """컬렉션에 연결할 모델·판본·차원·토큰 한도와 선택적 문서·질의 접두사를 보관한다."""
    key: str
    provider: str      # "local"
    model: str
    dim: int
    max_tokens: int
    revision: str | None = None
    adapter: TextPrefixAdapter | None = None


ENCODERS: dict[str, Encoder] = {
    # 기본 로컬 모델 설정. 가중치는 각 PC의 Hugging Face 캐시에 준비한다.
    "bge-m3": Encoder(
        key="bge-m3",
        provider="local",
        model=BGE_M3_REPO,
        dim=1024,
        max_tokens=8_192,
        revision=BGE_M3_REVISION,
    ),
}

# 컬렉션 이름별 인코더 키. encoder_for는 여기에 등록되지 않은 이름을 거절한다.
# 추가 모델은 별도 컬렉션으로 등록하고, 사용하는 검색·적재 경로에 연결한다.
COLLECTION_ENCODER: dict[str, str] = {
    "ran5_tdoc_chunks": "bge-m3",
    # RAN1~RAN5 및 Plenary의 TR 절 컬렉션.
    "ran1_tr_sections": "bge-m3",
    "ran2_tr_sections": "bge-m3",
    "ran3_tr_sections": "bge-m3",
    "ran4_tr_sections": "bge-m3",
    "ran5_tr_sections": "bge-m3",
    "tsgran_tr_sections": "bge-m3",
    # TS에서 파생한 ASN.1·capability·IE 및 추가 절 컬렉션.
    "ran2_ts_asn1_chunks": "bge-m3",
    "ran3_ts_asn1_chunks": "bge-m3",
    "ran2_ts_capabilities": "bge-m3",
    "ran2_ts_ie_descriptions": "bge-m3",
    # p1_1b_extract_ie_descriptions가 WG·기본 suffix로 구성하는 RAN5 컬렉션.
    "ran5_ts_ie_descriptions": "bge-m3",
    # apply_p1_to_wg.reindex_main_collection의 별도 P1.2 적재 대상.
    "ran3_ts_sections_p12": "bge-m3",
    "ran5_ts_sections_p12": "bge-m3",
    # WG별 Neo4j의 Resolution으로 생성하는 검색 컬렉션.
    "ran1_resolution_chunks": "bge-m3",
    "ran2_resolution_chunks": "bge-m3",
    "ran3_resolution_chunks": "bge-m3",
    "ran4_resolution_chunks": "bge-m3",
    "ran5_resolution_chunks": "bge-m3",
    # WG별 TS 절 컬렉션. 기본 적재기와 릴리스별 적재기가 같은 선언을 조회한다.
    "ran1_ts_sections": "bge-m3",
    "ran2_ts_sections": "bge-m3",
    "ran3_ts_sections": "bge-m3",
    "ran4_ts_sections": "bge-m3",
    "ran5_ts_sections": "bge-m3",
    # WG별 CR 컬렉션. Phase-11의 CR 적재기에서도 컬렉션별 인코더를 확인한다.
    "ran1_cr_chunks": "bge-m3",
    "ran2_cr_chunks": "bge-m3",
    "ran3_cr_chunks": "bge-m3",
    "ran4_cr_chunks": "bge-m3",
    "ran5_cr_chunks": "bge-m3",
    # WG별 이메일 청크 컬렉션. 적재기와 의미 분석 도구가 같은 선언을 사용한다.
    "ran1_email_chunks": "bge-m3",
    "ran2_email_chunks": "bge-m3",
    "ran3_email_chunks": "bge-m3",
    "ran4_email_chunks": "bge-m3",
    "ran5_email_chunks": "bge-m3",
    # WG별 정형 TDoc 컬렉션. ran5_tdoc_chunks는 위쪽에 함께 등록돼 있다.
    "ran1_tdoc_chunks": "bge-m3",
    "ran2_tdoc_chunks": "bge-m3",
    "ran3_tdoc_chunks": "bge-m3",
    "ran4_tdoc_chunks": "bge-m3",
}

# 사용자 설정으로 추가한 이름과 구분하여 기존 자료별 컬렉션의 교차 덮어쓰기를 막는다.
BUILTIN_COLLECTIONS = frozenset(COLLECTION_ENCODER)


def load_registry_config(path: str | Path, *, encoders=None, collections=None) -> dict:
    """JSON의 추가 인코더·컬렉션 선언을 검증한 뒤 두 설정 사전에 반영한다.

    기존 키의 덮어쓰기를 거절하고, 모델명·고정 commit·양의 정수 차원/토큰 한도를
    확인한다. 모든 항목을 검증한 뒤에만 사전을 갱신하고 읽은 config를 반환한다.
    실제 가중치·차원·인코딩 방식의 확인은 모델 로드와 소량 인코딩 단계에서 수행한다."""
    encoders = ENCODERS if encoders is None else encoders
    collections = COLLECTION_ENCODER if collections is None else collections
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if (not isinstance(config, dict) or set(config) != {"encoders", "collections"}
            or not isinstance(config["encoders"], dict) or not config["encoders"]
            or not isinstance(config["collections"], dict) or not config["collections"]):
        raise ValueError("embedding config requires encoders and collections objects")
    added = {}
    for key, value in config["encoders"].items():
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", key):
            raise ValueError("invalid encoder key")
        if key in encoders:
            raise ValueError(f"existing encoder declaration is immutable: {key}")
        required = {"model", "revision", "dim", "max_tokens"}
        if (not isinstance(value, dict) or not required <= set(value)
                or set(value) - required - {"adapter"}):
            raise ValueError(f"invalid encoder fields (optional adapter is supported): {key}")
        model_id = value["model"]
        if (not isinstance(model_id, str)
                or not re.fullmatch(r"\b[\w.-]+\b/\b[\w.-]{1,96}\b", model_id)
                or ".." in model_id or "--" in model_id or model_id.endswith(".git")):
            raise ValueError(f"model must be a Hugging Face repository id: {key}")
        if not isinstance(value["revision"], str) or not re.fullmatch(r"[0-9a-f]{40}", value["revision"]):
            raise ValueError(f"revision must be an immutable commit: {key}")
        if any(type(value[field]) is not int or value[field] <= 0 for field in ("dim", "max_tokens")):
            raise ValueError(f"dimensions and token budget must be positive integers: {key}")
        adapter = None
        if "adapter" in value:
            declaration = value["adapter"]
            if (not isinstance(declaration, dict)
                    or set(declaration) != {"type", "document_prefix", "query_prefix"}
                    or declaration.get("type") != "text_prefix"):
                raise ValueError(f"{key}: adapter requires text_prefix with document_prefix/query_prefix")
            for field in ("document_prefix", "query_prefix"):
                prefix = declaration[field]
                if (not isinstance(prefix, str) or not prefix.strip() or len(prefix) > 256
                        or not prefix.isprintable()):
                    raise ValueError(f"{key}: {field} requires 1..256 printable prefix characters")
            adapter = TextPrefixAdapter(**declaration)
        added[key] = Encoder(key=key, provider="local",
                             **{field: value[field] for field in required}, adapter=adapter)
    names = {}
    for name, key in config["collections"].items():
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name):
            raise ValueError("invalid collection name")
        if name in collections:
            raise ValueError(f"existing collection declaration is immutable: {name}")
        if not isinstance(key, str) or key not in added:
            raise ValueError(f"collection requires an encoder from this config: {name}")
        names[name] = key
    encoders.update(added)
    collections.update(names)
    return config


def _load_configured_registry() -> None:
    configured = os.environ.get("SPECTRA_EMBEDDING_CONFIG")
    if not configured:
        try:
            from .credentials import env_file_values, PROJECT_ROOT
        except ImportError:
            from credentials import env_file_values, PROJECT_ROOT
        configured = env_file_values().get("SPECTRA_EMBEDDING_CONFIG")
    else:
        PROJECT_ROOT = Path(__file__).resolve().parents[3]
    if configured:
        path = Path(configured).expanduser()
        load_registry_config(path if path.is_absolute() else PROJECT_ROOT / path)


_load_configured_registry()


def encoder_for(collection: str) -> Encoder:
    """컬렉션에 등록된 Encoder를 반환한다. 미등록 이름은 ValueError로 거절한다.

    이 함수는 설정만 조회하며 모델 가중치를 로드하지 않는다."""
    key = COLLECTION_ENCODER.get(collection)
    if key is None:
        raise ValueError(
            f"{collection}은 COLLECTION_ENCODER에 등록되어 있지 않습니다. "
            "사용 전에 컬렉션 이름과 인코더를 등록하세요."
        )
    return ENCODERS[key]


def require_local(collection: str) -> Encoder:
    """컬렉션 선언에 대응하는 Encoder를 반환하며 provider가 local이 아니면 ValueError를 낸다.

    encoder_for에서 컬렉션과 인코더 선언을 읽는다. 이 함수는 모델 가중치를 적재하지
    않으므로 토큰 수 계산 등 가중치가 필요 없는 호출에서도 같은 선언 검사를 쓸 수 있다."""
    enc = encoder_for(collection)
    if enc.provider != "local":
        raise ValueError(
            f"{collection}은 원격 인코더({enc.key})로 선언되어 있습니다. "
            "COLLECTION_ENCODER에 로컬 모델을 등록하고 해당 모델로 생성한 "
            "컬렉션을 연결하세요."
        )
    return enc


def local_encoder_for(collection: str) -> Encoder:
    """컬렉션이 로컬 인코더에 연결됐는지 확인하고 모델을 로드한 뒤 Encoder를 반환한다.

    모델은 load_local_encoder의 캐시를 재사용한다. 원격 provider는 require_local에서 거절한다."""
    enc = require_local(collection)
    load_local_encoder(enc)
    return enc


def embed_query_local(collection: str, query: str) -> list[float]:
    """컬렉션에 등록된 로컬 인코더로 질의 하나를 인코딩해 벡터를 반환한다.

    등록된 질의 접두사와 embed_local의 토큰 한도·정규화 처리를 사용한다.
    질의용 모델을 별도로 선택하지 않는다."""
    return embed_local(local_encoder_for(collection), [query], batch_size=1, input_kind="query")[0]


# ---------------------------------------------------------------------------
# 로컬 인코더
# ---------------------------------------------------------------------------

_LOCAL_CACHE: dict[str, object] = {}


# import 시점에 오프라인 설정을 저장하는 모듈 속성.
# 환경변수 변경 뒤에도 이전 값이 남을 수 있어, 이미 로드된 모듈의 속성도 갱신한다.
_OFFLINE_MIRRORS = (
    ("huggingface_hub.constants", "HF_HUB_OFFLINE"),
    ("transformers.utils.hub", "_is_offline_mode"),
)


def force_hf_offline() -> dict[str, bool]:
    """Hugging Face의 오프라인 환경변수와 이미 import된 모듈의 설정값을 갱신한다.

    HF_HUB_OFFLINE·TRANSFORMERS_OFFLINE을 1로 설정한다. _OFFLINE_MIRRORS에
    등록된 모듈이 이미 로드됐다면 해당 속성도 True로 설정하며, 모듈에 속성이 없으면
    RuntimeError를 낸다. 아직 로드되지 않은 모듈은 import할 때 환경변수를 읽는다.
    반환 사전에는 이번 호출에서 실제로 갱신한 모듈.속성 이름만 포함한다."""
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

    stood: dict[str, bool] = {}
    for mod_name, attr in _OFFLINE_MIRRORS:
        mod = sys.modules.get(mod_name)
        if mod is None:
            continue
        if not hasattr(mod, attr):
            raise RuntimeError(
                f"오프라인 설정 속성이 없습니다: {mod_name}.{attr} — "
                "설치된 패키지 판본의 속성 이름을 확인하세요(§1.2)"
            )
        setattr(mod, attr, True)
        stood[f"{mod_name}.{attr}"] = True
    return stood


# 모듈 import 시 환경변수와 이미 로드된 Hugging Face 모듈의 오프라인 설정을 갱신한다.
force_hf_offline()


_TOKENIZER_CACHE: dict[str, object] = {}


def local_snapshot_path(enc: Encoder) -> str:
    """고정 repository/commit의 로컬 캐시 경로를 해석한다. 네트워크는 사용하지 않는다.

    모델 ID를 라이브러리에 직접 넘기면 같은 이름의 상대 디렉터리가 먼저 선택될 수 있다.
    토크나이저·모델·파일 기록은 이 스냅샷 경로를 함께 사용한다.
    """
    force_hf_offline()
    from huggingface_hub import snapshot_download

    snapshot = Path(snapshot_download(enc.model, revision=enc.revision,
                                      local_files_only=True)).resolve(strict=True)
    modules_path = snapshot / "modules.json"
    if modules_path.exists():
        modules = json.loads(modules_path.read_text(encoding="utf-8"))
        if not isinstance(modules, list) or not modules:
            raise ValueError(f"{enc.key}: modules.json requires a nonempty module list")
        for module in modules:
            # SentenceTransformer treats local paths as trusted when resolving custom
            # classes. Permit installed modules only, even though this cache is local.
            module_type = module.get("type") if isinstance(module, dict) else None
            if (not isinstance(module_type, str)
                    or not re.fullmatch(r"sentence_transformers(?:\.[A-Za-z_]\w*)+", module_type)):
                raise ValueError(f"{enc.key}: custom SentenceTransformer module code is unsupported")
            relative = module.get("path")
            if (not isinstance(relative, str) or "\\" in relative or Path(relative).is_absolute()
                    or not (snapshot / relative).resolve().is_relative_to(snapshot)):
                raise ValueError(f"{enc.key}: SentenceTransformer module path must stay within snapshot")
    return str(snapshot)


def load_local_tokenizer(enc: Encoder):
    """인코더의 모델명과 revision으로 로컬 캐시의 토크나이저를 로드하고 재사용한다.

    AutoTokenizer만 로드하며 모델 가중치는 로드하지 않는다."""
    cached = _TOKENIZER_CACHE.get(enc.key)
    if cached is not None:
        return cached

    force_hf_offline()
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(local_snapshot_path(enc), revision=enc.revision,
                                        local_files_only=True, trust_remote_code=False)
    _TOKENIZER_CACHE[enc.key] = tok
    return tok


def load_local_encoder(enc: Encoder, device: str | None = None):
    """로컬 캐시의 SentenceTransformer 모델을 로드해 반환하고 인코더 키별로 재사용한다.

    신규 로드에는 오프라인 설정과 local_files_only=True를 적용한다. device가 없으면
    CUDA 사용 가능 여부에 따라 장치를 고른다. 기본 prompt, 차원, 토큰 한도를 검사한 뒤
    캐시한다. 이미 캐시된 키는 최초 로드한 모델과 장치를 그대로 재사용한다."""
    if enc.provider != "local":
        raise ValueError(f"local 인코더가 아니다: {enc.key} (provider={enc.provider})")

    cached = _LOCAL_CACHE.get(enc.key)
    if cached is not None:
        return cached

    force_hf_offline()

    from sentence_transformers import SentenceTransformer

    if device is None:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"

    model = SentenceTransformer(local_snapshot_path(enc), revision=enc.revision, device=device,
                                local_files_only=True, trust_remote_code=False)
    if getattr(model, "default_prompt_name", None):
        raise ValueError(
            f"{enc.key}: implicit default prompt is unsupported; text_prefix uses plain encode only"
        )
    dimension = getattr(model, "get_embedding_dimension", None)
    actual_dim = dimension() if dimension else model.get_sentence_embedding_dimension()
    if actual_dim != enc.dim:
        raise ValueError(f"{enc.key}: model dimension {actual_dim} differs from declaration {enc.dim}")
    if enc.max_tokens > model.max_seq_length:
        raise ValueError(f"{enc.key}: token budget {enc.max_tokens} exceeds model capacity {model.max_seq_length}")
    model.max_seq_length = enc.max_tokens
    _LOCAL_CACHE[enc.key] = model
    return model


# 현재 프로세스에서 인코더 키별로 누적한 입력 절단 건수.
TRUNCATED: dict[str, int] = {}


def _input_prefix(enc: Encoder, input_kind: str) -> str:
    if input_kind not in ("document", "query"):
        raise ValueError("input_kind must be document or query")
    adapter = getattr(enc, "adapter", None)
    if adapter is None:
        return ""
    if adapter.type != "text_prefix":
        raise ValueError(f"{enc.key}: unsupported embedding adapter {adapter.type!r}")
    return adapter.document_prefix if input_kind == "document" else adapter.query_prefix


def truncate_to_encoder_budget(enc: Encoder, texts: list[str], *,
                               input_kind: str = "document") -> tuple[list[str], int]:
    """접두사를 적용한 인코딩 입력과 본문이 잘린 건수를 돌려준다.

    청커와 같은 로컬 인코더의 토크나이저를 사용한다. 청커를 거치지 않은 입력도
    sentence_transformers 의 `max_seq_length` 에서 잘릴 수 있으므로, 적재 직전에
    같은 토크나이저로 미리 자르고 절단된 입력 수를 반환한다.

    원래 본문을 받으며 문서·질의용 접두사는 여기서 한 번 붙인다. 특수 토큰과 접두사를
    포함해 한도를 검사하고, 초과하면 본문만 줄여 접두사를 보존한다. 디코드한 문자열은
    접두사와 합친 뒤 다시 토큰화해 확인한다.
    """
    input_prefix = _input_prefix(enc, input_kind)
    if not texts:
        return [], 0

    model = load_local_encoder(enc)
    tok = model.tokenizer
    keep = enc.max_tokens - tok.num_special_tokens_to_add()
    if keep <= 0:
        raise ValueError(f'{enc.key}: token budget leaves no room after special tokens')
    prefix_length = (len(tok(input_prefix, add_special_tokens=False, truncation=False)["input_ids"])
                     if input_prefix else 0)
    if prefix_length >= keep:
        raise ValueError(f'{enc.key}: token budget leaves no room after input prefix and special tokens')
    seqs = tok(texts, add_special_tokens=False, truncation=False)["input_ids"]
    if len(seqs) != len(texts):
        raise ValueError(f'{enc.key}: tokenizer returned {len(seqs)} rows for {len(texts)} texts')

    out: list[str] = []
    n_cut = 0
    for text, seq in zip(texts, seqs):
        prepared = input_prefix + text
        input_length = (len(tok(prepared, add_special_tokens=False, truncation=False)["input_ids"])
                        if input_prefix else len(seq))
        if input_length <= keep:
            out.append(prepared)
            continue
        n_cut += 1
        prefix = min(len(seq), keep - prefix_length)
        while True:
            candidate = input_prefix + tok.decode(seq[:prefix], skip_special_tokens=True)
            actual = len(tok(candidate, add_special_tokens=False, truncation=False)["input_ids"])
            if actual <= keep:
                out.append(candidate)
                break
            if prefix == 0:
                raise ValueError(f'{enc.key}: decoded text cannot fit the token budget')
            prefix = max(0, prefix - (actual - keep))
    return out, n_cut


def embed_local(enc: Encoder, texts: list[str], batch_size: int = 4, *,
                input_kind: str = "document") -> list[list[float]]:
    """텍스트를 로컬 인코더로 인코딩해 정규화한 벡터 목록을 반환한다.

    기본 입력 유형은 문서이고, 질의는 embed_query_local 또는 input_kind="query"로 지정한다.
    토큰 한도를 넘은 입력은 자르고 인코더별 절단 건수를 누적한다. 빈 입력에는 빈 목록을
    반환한다. 출력 수·차원·유한수 여부·영벡터 여부를 확인하고 잘못된 출력은 ValueError로 거절한다."""
    if not texts:
        return []

    texts, n_cut = truncate_to_encoder_budget(enc, texts, input_kind=input_kind)
    if n_cut:
        TRUNCATED[enc.key] = TRUNCATED.get(enc.key, 0) + n_cut
        print(
            f"  [WARN] {enc.key} 한도({enc.max_tokens:,} 토큰) 초과 {n_cut} 건 절단"
            f" — 누적 {TRUNCATED[enc.key]}",
            file=sys.stderr,
        )

    model = load_local_encoder(enc)
    vecs = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    if len(vecs) != len(texts):
        raise ValueError(f'{enc.key}: encoder returned {len(vecs)} vectors for {len(texts)} texts')
    result = [v.tolist() for v in vecs]
    for vector in result:
        if ((hasattr(enc, "dim") and len(vector) != enc.dim)
                or any(not math.isfinite(value) for value in vector)
                or not any(vector)):
            raise ValueError(f"{enc.key}: invalid vector dimension or non-finite/zero vector")
    return result
