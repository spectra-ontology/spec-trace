#!/usr/bin/env python3
"""로컬 임베딩 모델의 배포 revision과 파일 내용 계약.

Spec: docs/common/process/internal_deployment_readiness.md 작업 2
Ontology: 임베딩 공간과 tokenizer의 동일 모델 계약.
Cycle: 모델 준비 → 로컬 임베딩 실행
배경: 설치 점검과 실제 encoder가 같은 스냅샷을 사용하게 한다.
사용: doctor.py와 embedding_registry.py에서 상수를 import한다.
LLM 호출: 없음. 네트워크 접근: 없음.

모델을 내려받는 doctor와 실제 tokenizer/encoder가 같은 스냅샷을 사용한다.
이 모듈은 모델·HuggingFace 라이브러리를 import하거나 망에 접속하지 않는다.
"""
from pathlib import Path


def validate_snapshot_layout(snapshot: Path) -> None:
    """Keep alternate weight formats from taking precedence over pinned bin bytes."""
    if any(snapshot.glob("*.safetensors")) or any(snapshot.glob("*.index.json")):
        raise ValueError("unpinned_preferred_model_weights")


BGE_M3_REPO = "BAAI/bge-m3"
BGE_M3_REVISION = "5617a9f61b028005a4858fdac845db406aefb181"
BGE_M3_FILES = {
    "pytorch_model.bin": "b5e0ce3470abf5ef3831aa1bd5553b486803e83251590ab7ff35a117cf6aad38",
    "tokenizer.json": "21106b6d7dab2952c1d496fb21d5dc9db75c28ed361a05f5020bbba27810dd08",
    "sentencepiece.bpe.model": "cfc8146abe2a0488e9e2a0c56de7952f7c11ab059eca145a0a727afce0db2865",
    "config.json": "e6eda1c72da8f9dc30fdd9b69c73d35af3b7a7ad",
    "modules.json": "952a9b81c0bfd99800fabf352f69c7ccd46c5e43",
    "1_Pooling/config.json": "9bd85925f325e25246d94c4918dc02ab98f2a1b7",
    "sentence_bert_config.json": "0140ba1eac83a3c9b857d64baba91969d988624b",
    "config_sentence_transformers.json": "1fba91c78a6c8e17227058ab6d4d3acb5d8630a9",
    "special_tokens_map.json": "b1879d702821e753ffe4245048eee415d54a9385",
    "tokenizer_config.json": "dc69ac559dcba2694012009aaa108c614541789a",
}
