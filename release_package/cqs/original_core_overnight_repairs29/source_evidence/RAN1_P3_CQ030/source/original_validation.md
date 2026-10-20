# Step-3: CQ Validation

## 개요

페르소나 기반 45개 Competency Question(CQ, v3.0)으로 RAN1 TS 구조 Knowledge Graph(Phase-3)를 검증한다. Direct Cypher 검증으로 데이터 정합성을 확인하고, LLM 기반 자연어 답변 리포트를 생성한다.

## release-aware 검증 계층

| 검증 계층 | 시점/도구 | 상태 |
|------|------|------|
| **Release Integrity (R1~R5, JSON-LD)** | Stage 4 — `validate_ts_jsonld.py` §10.1b | ✅ PASS |
| ↳ R1 sectionId에 release 토큰 포함 / R2 belongsToSpec release == sectionId release(cross-release 오염 0) / R3 specNumber 일치 / R4 cross-release 참조 누수 0 / R5 Spec `specInRelease`/`specRelease` 정합 | | |
| **CQ 45개 Cypher (Neo4j)** | Stage 8 — release-키 그래프 재적재 후 재실행 | ⏸️ 보류 — 아래 결과는 **재적재 이전 latest-only 그래프** 기준 |

> R1~R5는 release-aware JSON-LD 산출물 자체의 무결성을 비파괴로 검증한다(통과). R6(referencesSpec)은 RAN1 generate가 `referencesSpec`를 산출하지 않아 RAN1 미적용. 45개 CQ는 Neo4j 적재 그래프를 대상으로 하므로 release-키 재적재(Stage 5) 완료 후 동일 45개 + release-차원 신규 CQ로 재실행한다.

## Stage

| Stage | 내용 | 상태 |
|-------|------|------|
| 3-1 | CQ Cypher 검증 (45개, v3.0) | ✅ 완료 (100%) |
| 3-2 | LLM 답변 리포트 생성 | ✅ 완료 |

## 출처 테이블 개선 (v3.1)

LLM 답변 리포트의 출처 정보 품질 향상을 위해 `source_extractor.py`를 개선:

| 항목 | 개선 전 | 개선 후 |
|------|---------|---------|
| Section 타입 | ❌ 미포함 | ✅ TDoc/Section 유형 구분 표시 |
| Section 출처 | 기본 정보만 | ✅ sectionId, sectionTitle 표시 |

### 출처 테이블 포맷

```markdown
| ID | 타입 | TS | Section | 본문 미리보기 |
| sec-38211-5.1.3 | Section | 38.211 | 5.1.3 PDSCH resource mapping | Reference point... |
```

**수정 파일**: `scripts/cross-phase/llm_quality/source_extractor.py` (v3.1)

## 기술 스택

| 구성 요소 | 선택 |
|-----------|------|
| Direct Cypher | Neo4j Python Driver |
| LLM SDK | OpenAI SDK (OpenRouter 호환) |
| LLM Provider | OpenRouter |
| LLM Model | Gemini 2.5 Flash (`google/gemini-2.5-flash`) |
| 답변 언어 | 한국어 |

## 검증 결과

| 지표 | 결과 |
|------|------|
| 성공 (PASS) | 45개 (100%) |
| 데이터 없음 (NO_DATA) | 0개 (0%) |
| 실패 (FAIL) | 0개 (0%) |
| **쿼리 성공률** | **100%** |

## CQ 카테고리별 결과

| 카테고리 | 설명 | CQ 수 | 결과 |
|----------|------|--------|------|
| TS_구조탐색 | Section 계층 탐색, breadcrumb | 8 | 8/8 PASS |
| TS_참조분석 | 교차 TS 참조 분석 | 7 | 7/7 PASS |
| CR_TS_변경추적 | CR→Spec, clausesAffected | 8 | 8/8 PASS |
| Resolution_TS_의사결정 | Resolution→CR→Spec | 7 | 7/7 PASS |
| 기술_키워드검색 | Section 제목 키워드 검색 | 7 | 7/7 PASS |
| 통합분석 | 회사 기여도, 릴리스 변경, 트렌드 | 8 | 8/8 PASS |
| **합계** | | **45** | **45/45 (100%)** |

## CQ 데이터셋 설계

### 버전

v3.0 (페르소나 중심 재설계)

### 대상 페르소나

| 페르소나 | 핵심 니즈 |
|----------|----------|
| HW/SW 엔지니어 | TS Section 구조 탐색, 관련 Table/Figure 조회 |
| 표준화 엔지니어 | CR→TS 변경 추적, 교차 TS 참조 분석 |
| 전략/기획 | 릴리스별 변경 트렌드, 회사 기여도 |
| IP/특허 | Resolution→CR→TS 의사결정 추적 |

### 질문 설계 원칙

1. **Section 계층 탐색** - breadcrumb, 부모/자식 탐색
2. **교차 참조 분석** - TS 간 참조 관계 추적
3. **Phase-1/2 연계** - CR→TS, Resolution→CR→TS 연계 쿼리
4. **키워드 검색** - Section 제목 기반 기술 키워드 검색
5. **내부 ID 사용 금지** - 자연어 기반 질문

### 질문 유형 예시

| 유형 | 예시 질문 |
|------|----------|
| 구조탐색 | "38.214의 Section 5.1.3은 어떤 하위 Section을 가지나?" |
| 참조분석 | "38.213이 가장 많이 참조하는 다른 TS Section은?" |
| 변경추적 | "38.211 Section 6.3.1을 수정하는 CR 목록은?" |
| 의사결정 | "MIMO 관련 Resolution이 참조하는 TS Section은?" |
| 키워드 | "positioning 키워드가 포함된 Section 목록은?" |

## LLM 답변 리포트

45개 CQ에 대해 Cypher 쿼리 결과를 기반으로 자연어 한국어 답변을 생성한다.

- **LLM**: Gemini 2.5 Flash (`google/gemini-2.5-flash`, OpenRouter 경유, OpenAI SDK)
- **입력**: CQ 질문 + Cypher 쿼리 + 쿼리 결과 테이블
- **출력**: `logs/RAN/formal/RAN1/phase-3/cq_answers_report_llm.md` (3,041행)

### 답변 형식

각 CQ마다:
1. 질문 (한국어)
2. Cypher 쿼리 (코드 블록)
3. 쿼리 결과 (테이블)
4. 자연어 답변 (Gemini 2.5 Flash 생성, OpenRouter 경유)

## 스크립트

| 스크립트 | 용도 | 실행 순서 |
|----------|------|-----------|
| `scripts/RAN/formal/RAN1/phase-3/validation/01_validate_cq_cypher.py` | CQ Cypher 검증 | 1번째 |
| `scripts/RAN/formal/RAN1/phase-3/validation/02_generate_llm_answers.py` | LLM 답변 생성 | 2번째 |

## 실행 방법

```bash
# 1. CQ Cypher 검증
python scripts/RAN/formal/RAN1/phase-3/validation/01_validate_cq_cypher.py

# 2. LLM 답변 리포트 생성
python scripts/RAN/formal/RAN1/phase-3/validation/02_generate_llm_answers.py
```

## 로그 파일

| 파일 | 설명 |
|------|------|
| `logs/RAN/formal/RAN1/phase-3/cq_test_dataset.json` | 테스트 데이터셋 v3.0 (45개 CQ) |
| `logs/RAN/formal/RAN1/phase-3/cq_cypher_results.json` | Cypher 직접 검증 결과 |
| `logs/RAN/formal/RAN1/phase-3/cq_answers_report_llm.md` | LLM 자연어 답변 리포트 (3,041행) |

## 관련 문서

- [Phase-3 README](README.md)
- [Step-1: TS Parsing](step1_ts_parsing.md)
- [Step-2: Neo4j Loading](step2_neo4j_loading.md)
- [TS Structure Ontology Spec](design-spec/tdoc_ontology_specs(TS).md)

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-01-31 | CQ 데이터셋 v3.0 설계 (6개 카테고리, 45개 CQ) |
| 2026-01-31 | Direct Cypher 검증 45/45 PASS (100%) |
| 2026-01-31 | LLM 자연어 답변 리포트 생성 완료 (3,041행) |
| 2026-02-03 | **LLM 호출 패턴 통일**: Google Gemini API 직접 호출 → OpenAI SDK + OpenRouter (`google/gemini-2.5-flash`) |
| 2026-02-04 | **출처 테이블 개선 (v3.1)**: Section 유형/정보 표시 개선 |
| 2026-06-10 | release-aware Release Integrity R1~R5(JSON-LD 계층) PASS. R6는 RAN1 미적용(referencesSpec 미산출). → Stage 5 Neo4j 파괴적 재적재 완료(release-키 Section 3,942, 게이트 5/5), CQ 53/53 PASS 재검증 완료. Qdrant 재적재는 §3.6 보류 |
