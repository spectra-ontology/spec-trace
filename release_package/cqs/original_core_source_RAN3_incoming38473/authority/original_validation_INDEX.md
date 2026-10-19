# Step-3: CQ Validation

## 개요

페르소나 시나리오 기반 15개 Competency Question(CQ)으로 RAN3 CR 확장 Knowledge Graph(Phase-4)를 검증한다. Direct Cypher 검증으로 데이터 정합성을 확인한다.

## Stage

| Stage | 내용 | 상태 |
|-------|------|------|
| 3-1 | CQ Cypher 검증 (15개) | ✅ 완료 (100%) |

## 기술 스택

| 구성 요소 | 선택 |
|-----------|------|
| Direct Cypher | Neo4j Python Driver |
| Neo4j Port | 7689 (RAN3 전용) |
| LLM SDK | OpenAI SDK (OpenRouter 호환) |
| LLM Model | Gemini 2.5 Flash (`google/gemini-2.5-flash`) |
| 답변 언어 | 한국어 |

## 검증 결과

| 지표 | 결과 |
|------|------|
| 성공 (PASS) | 15개 (100%) |
| 데이터 없음 (NO_DATA) | 0개 (0%) |
| 실패 (FAIL) | 0개 (0%) |
| **쿼리 성공률** | **100%** |

## CQ 카테고리별 결과

| 카테고리 | 설명 | CQ 수 | 결과 |
|----------|------|--------|------|
| CQ1_CR변경근거 | CR 변경 이유·요약·영향 분석 | 3 | 3/3 PASS |
| CQ2_CrossSpec영향 | Cross-Spec 영향 범위 분석 | 4 | 4/4 PASS |
| CQ3_CRPack분석 | CR Pack 구성·TSG 제출 분석 | 3 | 3/3 PASS |
| CQ4_연계분석 | Resolution→CR→TS 연계 추적 | 5 | 5/5 PASS |
| **합계** | | **15** | **15/15 (100%)** |

## CQ 데이터셋 설계

### 버전

v3.0 (최신 데이터 우선, 페르소나 시나리오 기반)

### 대상 페르소나

| 페르소나 | 핵심 니즈 |
|----------|----------|
| 표준 엔지니어 | CR 변경 근거·영향 분석 |
| WG 의장/라포르터 | CRPack 구성·회의 결과 종합 |
| 시스템 아키텍트 | Cross-Spec 연쇄 영향 파악 |
| 기업 대표 | 자사 기고문의 Cross-Spec 영향 추적 |

### 질문 설계 원칙

1. **최신 데이터 우선** - 최신 회의/CR 활용
2. **실제 시나리오 기반** - 특정 CR 번호(R3-XXXXXX 등) 지정
3. **Phase 1-3 연계** - Resolution→CR→TS 전체 추적 CQ
4. **Cross-Spec 분석** - 영향 유형(Core/Test/O&M) 구분

## 스크립트

| 스크립트 | 용도 |
|----------|------|
| `scripts/RAN/formal/RAN3/phase-4/validation/01_validate_cq_cypher.py` | CQ Cypher 검증 |

## 실행 방법

```bash
# CQ Cypher 검증
python scripts/RAN/formal/RAN3/phase-4/validation/01_validate_cq_cypher.py
```

## 로그 파일

| 파일 | 설명 |
|------|------|
| `logs/RAN/formal/RAN3/phase-4/cq_test_dataset.json` | 테스트 데이터셋 v3.0 (15개 CQ) |
| `logs/RAN/formal/RAN3/phase-4/cq_cypher_results.json` | Cypher 직접 검증 결과 |

## 관련 문서

- [Phase-4 README](README.md)
- [Step-1: CR Parsing](step1_cr_parsing.md)
- [Step-2: JSON-LD & Neo4j Loading](step2_neo4j_loading.md)
- [CR Ontology Spec](design-spec/tdoc_ontology_specs(CR).md)

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-04-06 | CQ 데이터셋 v3.0 설계 (4개 카테고리, 15개 CQ) |
| 2026-04-06 | Direct Cypher 검증 15/15 PASS (100%) |
