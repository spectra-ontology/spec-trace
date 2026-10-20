# Step-3: CQ Validation

## 개요

41개 Competency Question(CQ)으로 RAN3 TS 구조 Knowledge Graph(Phase-3)를 검증한다. Direct Cypher 검증으로 데이터 정합성을 확인한다.

## release-aware 검증 계층

| 검증 계층 | 시점/도구 | 상태 |
|------|------|------|
| **Release Integrity (R1~R6, JSON-LD)** | Stage 4 — `validate_ts_jsonld.py` §10.4 | ✅ PASS |
| ↳ R1 sectionId에 release 토큰 포함 / R2 belongsToSpec release == sectionId release(cross-release 오염 0) / R3 specNumber 일치 / R4 cross-release 참조 누수 0 / R5 Spec `specInRelease`/`specRelease` 정합 / R6 referencesSpec 동일-release Spec 노드 존재(RAN3 referencesSpec 보유) | | |
| **CQ 41개 Cypher (Neo4j)** | Stage 8 — release-키 그래프 재적재 후 재실행 | ⏸️ 보류 — 아래 결과는 **재적재 이전 latest-only 그래프** 기준 |

> R1~R6는 release-aware JSON-LD 산출물 자체의 무결성을 비파괴로 검증한다(전수 PASS; cross-release 오염 0, 참조 누수 0). 41개 CQ는 Neo4j 적재 그래프를 대상으로 하므로, release-키 재적재(Stage 5) 완료 후 동일 41개 + release-차원 신규 CQ로 재실행한다.

## Stage

| Stage | 내용 | 상태 |
|-------|------|------|
| 3-1 | CQ Cypher 검증 (41개) | ✅ 완료 (41/41 PASS) |

## 기술 스택

| 구성 요소 | 선택 |
|-----------|------|
| Direct Cypher | Neo4j Python Driver |
| Neo4j | bolt://localhost:7689 (RAN3 전용 DB) |

## 검증 결과

| 지표 | 결과 |
|------|------|
| 성공 (PASS) | 41개 (100%) |
| 데이터 없음 (NO_DATA) | 0개 (0%) |
| 실패 (FAIL) | 0개 (0%) |
| **쿼리 성공률** | **41/41 (100%)** |

## CQ 카테고리별 결과

| 카테고리 | 설명 | CQ 수 | 결과 |
|----------|------|--------|------|
| CQ1_TS구조탐색 | Section 계층 탐색, breadcrumb, Table/Figure | 16 | 16/16 PASS |
| CQ2_TS간참조 | 교차 TS 참조 분석 | 8 | 8/8 PASS |
| CQ3_CR연결 | CR->Spec, clausesAffected | 8 | 8/8 PASS |
| CQ4_Resolution연결 | Resolution->CR->Spec | 4 | 4/4 PASS |
| CQ5_통합분석 | CR 밀도, Table/Figure 분포, 회사 기여도 | 5 | 5/5 PASS |
| **합계** | | **41** | **41/41 (100%)** |

### RAN3 CQ 구성 (41 CQ)

| 카테고리 | RAN3 | 비고 |
|----------|------|------|
| TS구조탐색 | **16** | Void, 레벨 분포, Table/Figure Top 5 |
| TS간참조 | **8** | 전체 건수, 내부 참조 Top 5 |
| CR연결 | **8** | clausesAffected->Section 매칭 |
| Resolution연결 | **4** | Resolution->CR->Spec 경로 |
| 통합분석 | **5** | CR 밀도, Table/Figure 분포 |

## CQ 데이터셋 설계

### 대상 페르소나

| 페르소나 | 핵심 니즈 |
|----------|----------|
| HW/SW 엔지니어 | TS Section 구조 탐색, 관련 Table/Figure 조회 |
| 표준화 엔지니어 | CR->TS 변경 추적, 교차 TS 참조 분석 |
| 전략/기획 | 릴리스별 변경 트렌드, 회사 기여도 |
| IP/특허 | Resolution->CR->TS 의사결정 추적 |

### 질문 설계 원칙

1. **Section 계층 탐색** - breadcrumb, 부모/자식 탐색
2. **교차 참조 분석** - TS 간 참조 관계 추적
3. **Phase-1/2 연계** - CR->TS, Resolution->CR->TS 연계 쿼리
4. **내부 ID 사용 금지** - 자연어 기반 질문

### 질문 유형 예시

| 유형 | 예시 질문 |
|------|----------|
| 구조탐색 | "38.413에서 Section 레벨별 분포는?" |
| 구조탐색 | "TS별 Section 수 Top 5는?" |
| 구조탐색 | "Void Section 목록은?" |
| 참조분석 | "전체 교차 참조(REFERENCES_SECTION) 건수는?" |
| 참조분석 | "38.401 내부에서 가장 많이 참조되는 Section은?" |
| 변경추적 | "clausesAffected로 실제 Section과 매칭되는 CR은?" |
| 의사결정 | "Resolution->CR->Spec 경로에서 가장 많이 수정된 TS는?" |
| 통합분석 | "TS별 CR 밀도(CR수/Section수)는?" |

## 알려진 한계

| 항목 | 내용 |
|------|------|
| TSTable | 12개 (캡션 기반). ASN.1 IE 정의가 대부분이라 캡션 형식 Table이 극소 |
| 교차 참조 | 119건으로 적음. Interface별 독립 프로토콜 특성 |
| ASN.1 | 38.413/423/473 — PL 스타일이라 Section 미생성, 본문 미저장 |
| Warnings | 3건 (38.460, 38.462, 38.463 — 소형 TS의 Heading 스타일 이슈) |
| 소형 TS | 14개 (58%)가 섹션 수 3~12개. CQ 적용 범위가 대형 TS에 편중 |

## 주요 데이터 수치

> ⏸️ **재적재 이전 latest-only 그래프** 기준. release-aware baseline(Section 16,268 / TSTable 64 / TSFigure 1,924 / refsSection 485 / refsSpec 939, 115 spec-release)은 Spec Appendix A.1.3.

| 항목 | 수량 |
|------|------|
| 전체 Section | 4,044 |
| 전체 TSTable | 12 |
| 전체 TSFigure | 498 |
| REFERENCES_SECTION | 119 |
| REFERENCES_SPEC | 202 |
| TS별 최대 Section | 38.413 (1,049) |
| 계층 edges (HAS_SUB_SECTION) | 3,857 |
| hasSection | 187 |

## 로그 파일

| 파일 | 설명 |
|------|------|
| `logs/RAN/formal/RAN3/phase-3/cq_test_dataset.json` | 테스트 데이터셋 (41개 CQ) |
| `logs/RAN/formal/RAN3/phase-3/cq_cypher_results.json` | Cypher 직접 검증 결과 |

## 스크립트

| 스크립트 | 용도 |
|----------|------|
| `scripts/RAN/formal/RAN3/phase-3/validation/01_validate_cq_cypher.py` | CQ Cypher 검증 |

## 실행 방법

```bash
# CQ Cypher 검증
python scripts/RAN/formal/RAN3/phase-3/validation/01_validate_cq_cypher.py
```

## 관련 문서

- [Phase-3 Overview](README.md)
- [Step-1: TS Parsing](step1_ts_parsing.md)
- [Step-2: Neo4j Loading](step2_neo4j_loading.md)
- [TS Structure Ontology Spec](design-spec/tdoc_ontology_specs(TS).md)

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-04-06 | CQ 데이터셋 설계 (5개 카테고리, 41개 CQ) |
| 2026-04-06 | Cypher 직접 검증 41/41 PASS (100%) |
| 2026-06-10 | release-aware Release Integrity R1~R6 (JSON-LD 계층) 전수 PASS (cross-release 오염 0, 참조 누수 0). → Stage 5 Neo4j 파괴적 재적재 완료(release-키 Section 16,268, 게이트 6/6), CQ 49/49 PASS 재검증 완료. Qdrant 재적재는 §3.6 보류 |
