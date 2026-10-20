# Step-3: CQ Validation

## 개요

페르소나 시나리오 기반 34개 Competency Question(CQ, v3.0)으로 Knowledge Graph를 검증한다. 두 가지 검증 방식을 사용:

1. **Direct Cypher 검증** (`01_validate_cq_cypher.py`): CQ 데이터셋의 Cypher 쿼리를 Neo4j에 직접 실행하여 데이터 정합성 검증
2. **Text2Cypher 검증** (`02_validate_cq_llamaindex.py`): 자연어 질문을 LLM(OpenAI SDK + OpenRouter)이 Cypher로 변환하여 실행, End-to-End QA 파이프라인 검증

## Stage

| Stage | 내용 | 상태 |
|----------|------|------|
| 3-1 | Cypher 직접 검증 (34개, v3.0) | ✅ 완료 (100%) |
| 3-2 | Text2Cypher 검증 (OpenAI SDK + OpenRouter) | ✅ 완료 |
| 3-3 | LLM 답변 리포트 생성 | ✅ 완료 |

## 출처 테이블 개선 (v3.1)

LLM 답변 리포트의 출처 정보 품질 향상을 위해 `source_extractor.py`를 개선:

| 항목 | 개선 전 | 개선 후 |
|------|---------|---------|
| Resolution 타입 | ❌ 미포함 | ✅ AGR/CON/WA 구분 표시 |

### 출처 테이블 포맷

```markdown
| ID | 타입 | 회의 | 관련 TDoc | 본문 미리보기 |
| AGR-115-7.1-001 | AGR | RAN1#115 | R1-2312484, ... | The following TPs... |
| CON-121-6-001 | CON | RAN1#121 | R1-2504573 | For the issue... |
| WA-115-8.1.1.2-001 | WA | RAN1#115 | R1-2312473 | A UE may report... |
```

**수정 파일**: `scripts/cross-phase/llm_quality/source_extractor.py` (v3.1)

## 기술 스택

| 구성 요소 | 선택 |
|-----------|------|
| Direct Cypher | Neo4j Python Driver |
| LLM SDK | OpenAI SDK (OpenRouter 호환) |
| LLM Provider | OpenRouter |
| LLM Model | Gemini 2.5 Flash (`google/gemini-2.5-flash`) |

## 검증 결과 (v3.0)

| 지표 | 결과 |
|------|------|
| 성공 (PASS) | 34개 (100%) |
| 데이터 없음 (NO_DATA) | 0개 (0%) |
| 실패 (FAIL) | 0개 (0%) |
| **쿼리 성공률** | **100%** |

**최종 결과**: 34개 CQ 전체 PASS (v3.0)

## CQ 카테고리별 결과 (v3.0)

| 카테고리 | 쿼리 수 | 성공 | 성공률 |
|----------|---------|------|--------|
| CQ1_Resolution조회 | 7 | 7 | 100% |
| CQ2_Tdoc-Resolution추적 | 5 | 5 | 100% |
| CQ3_회사기여도 | 6 | 6 | 100% |
| CQ4_기술주도권분석 | 3 | 3 | 100% |
| CQ5_기술트렌드 | 13 | 13 | 100% |
| **총계** | **34** | **34** | **100%** |

## Spec §8: content vs contentWithEquations 사용 규칙

CQ 쿼리에서 Resolution 본문을 다룰 때 Spec §8 규칙을 준수:

| 단계 | 필드 | 이유 |
|------|------|------|
| **검색 (WHERE)** | `content` | `[EQUATION]` 마커로 노이즈 제거, 텍스트 매칭 정확도 향상 |
| **답변/렌더링 (RETURN)** | `contentWithEquations` | 수식 LaTeX 인라인 포함, 완전한 정보 |

### COALESCE 패턴

`contentWithEquations`가 NULL인 Resolution(수식 미포함)을 안전하게 처리:

```cypher
-- Spec §8 준수: WHERE=content, RETURN=COALESCE(contentWithEquations, content)
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting)
WHERE m.meetingNumber = 'RAN1#112'
  AND a.content CONTAINS 'MIMO'
RETURN a.resolutionId, COALESCE(a.contentWithEquations, a.content)
```

CQ 데이터셋 v3.0 34개 쿼리 중 24개가 Resolution 본문(`content`)을 RETURN하며, 나머지 10개는 집계/카운트 쿼리. Text2Cypher에서는 COALESCE 패턴을 Few-shot 예시로 제공하여 LLM이 적절히 사용하도록 유도.

### Text2Cypher Schema 반영

`02_validate_cq_llamaindex.py`의 SCHEMA_INFO와 CYPHER_EXAMPLES에 Spec §8 규칙 명시:

- `SCHEMA_INFO`: `content` vs `contentWithEquations` 용도 설명 및 예시
- `CYPHER_EXAMPLES`: 30개 Few-shot 예시 모두 COALESCE 패턴 사용

## 테스트 데이터셋 v3.0 설계

### 페르소나

3가지 업무 페르소나 기반 시나리오:
- **전략/기획팀**: 회의 결과 파악, 기술 트렌드 분석, 경쟁사 동향
- **IP/특허팀**: 기고의 표준 반영 여부, 기여 증거 확보
- **표준화 엔지니어**: 특정 기술 결정사항 추적, 후속 작업 파악

### 질문 카테고리 (5종, 34개)

| 카테고리 | 수 | 주요 검증 포인트 |
|----------|-----|-----------------|
| CQ1_Resolution조회 | 7 | 회의별/Agenda별 Resolution 조회, 타입별 필터링 |
| CQ2_Tdoc-Resolution추적 | 5 | Tdoc↔Resolution 관계 추적, 참조 검색 |
| CQ3_회사기여도 | 6 | 회사별 기여 집계, Resolution 참여 분석 |
| CQ4_기술주도권분석 | 3 | 기술 영역별 주도 회사 식별 |
| CQ5_기술트렌드 | 13 | 시계열 기술 변화, 키워드 기반 추세 분석 |

## 교훈 (초기 버전 v1.0~v2.0에서 학습)

초기 CQ 설계(v1.0~v2.0) 과정에서 관계명·속성명 버그를 다수 경험. v3.0에서 전면 재설계하여 해결.

- Neo4j 관계명은 UPPER_SNAKE_CASE 사용 (Spec의 camelCase와 별개)
- JSON-LD의 데이터 속성(`tdoc:`)과 관계 속성(접두사 없음) 구분 필요
- CQ 쿼리 작성 시 실제 DB 스키마와 일치 여부 검증 필수

## 스크립트

| 스크립트 | 용도 | 실행 순서 |
|----------|------|-----------|
| `scripts/RAN/formal/RAN1/phase-2/validation/01_validate_cq_cypher.py` | Cypher 직접 검증 (데이터 정합성) | 1번째 |
| `scripts/RAN/formal/RAN1/phase-2/validation/02_validate_cq_llamaindex.py` | Text2Cypher 검증 (E2E QA, OpenAI SDK) | 2번째 |
| `scripts/RAN/formal/RAN1/phase-2/validation/03_generate_llm_answers.py` | LLM 기반 자연어 답변 리포트 생성 | 3번째 |

## 실행 방법

```bash
# 1. Cypher 직접 검증 (데이터 정합성)
python scripts/RAN/formal/RAN1/phase-2/validation/01_validate_cq_cypher.py

# 2. Text2Cypher 검증 (E2E QA)
python scripts/RAN/formal/RAN1/phase-2/validation/02_validate_cq_llamaindex.py

# 3. LLM 답변 리포트 생성
python scripts/RAN/formal/RAN1/phase-2/validation/03_generate_llm_answers.py
```

## 로그 파일

| 파일 | 설명 |
|------|------|
| `logs/RAN/formal/RAN1/phase-2/cq_test_dataset.json` | 테스트 데이터셋 v3.0 (34개 CQ) |
| `logs/RAN/formal/RAN1/phase-2/cq_cypher_results.json` | Cypher 직접 검증 결과 |
| `logs/RAN/formal/RAN1/phase-2/cq_validation_results.json` | Text2Cypher 검증 결과 |
| `logs/RAN/formal/RAN1/phase-2/cq_answers_report_llm.md` | LLM 자연어 답변 리포트 (Cypher 직접 답변 리포트는 deprecated — `cq_cypher_results.json` JSON 그대로 사용) |

## 핵심 설계 결정

### Two-tier 검증 전략

1. **Direct Cypher** (`01_validate_cq_cypher.py`): CQ 데이터셋에 미리 작성된 Cypher를 직접 실행. 데이터 적재 정확성과 관계 연결을 검증. 100% PASS가 필수.
2. **Text2Cypher** (`02_validate_cq_llamaindex.py`): 자연어 질문을 LLM(OpenAI SDK + OpenRouter)이 Cypher로 변환. End-to-End QA 파이프라인 품질 검증. LLM의 Cypher 생성 능력도 평가.

이 방식으로 "데이터가 맞는지" (Tier 1)와 "QA 시스템이 작동하는지" (Tier 2)를 분리 검증.

### Text2Cypher Schema 설계

`02_validate_cq_llamaindex.py`에 상세한 SCHEMA_INFO를 LLM에 제공:

- **노드/관계 구조**: Phase-1 + Phase-2 전체 스키마
- **속성 타입 주의사항**: `meetingNumber`는 STRING, `tdocNumber`는 Array 등
- **회사 검색 패턴**: `[:SUBMITTED_BY]` 관계 사용 (Tdoc 속성에 회사명 없음)
- **언어 규칙**: DB 데이터는 영어, 한국어 키워드 사용 금지
- **Spec §8 규칙**: content vs contentWithEquations 용도 구분
- **Few-shot Examples**: 30개 복잡한 쿼리 패턴 (모두 COALESCE 패턴 사용)

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-01-22 | 초기 검증 (55% → 스키마 충돌 해결 후 99%) |
| 2026-01-23 | DB 포트 수정 (7688→7687), NO_DATA 상태 추가 |
| 2026-01-23 | 테스트 데이터셋 v1.0~v2.0 초기 설계 및 반복 개선 |
| 2026-02-03 | **테스트 데이터셋 v3.0** — 페르소나 시나리오 기반 34개 CQ 재설계, 34/34 PASS |
| 2026-02-03 | **LLM 호출 패턴 통일**: OpenAI SDK + OpenRouter (`google/gemini-2.5-flash`) |
| 2026-02-03 | 01_validate_cq_cypher.py 추가 (Direct Cypher 검증, Two-tier 전략) |
| 2026-02-03 | Spec §8 반영: Text2Cypher SCHEMA_INFO + CYPHER_EXAMPLES에 COALESCE 패턴 명시 |
| 2026-02-12 | **Spec 정비**: v8.0 잔여 정리, v3.0 기준 문서 통일 |
| 2026-02-12 | **파서 임베딩 테이블 수정 후 재검증**: Cypher 34/34 PASS, LlamaIndex 30/34 PASS (4 NO_DATA는 LLM Cypher 생성 이슈) |
| 2026-02-13 | **Text2Cypher LLM 품질 개선**: SCHEMA_INFO 규칙 3개 + Few-Shot 3개 + CRITICAL NOTES 3개 추가, Cypher 스키마 검증 + 자동 재시도 로직 구현 → **34/34 PASS (100%)** |
