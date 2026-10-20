# RAN5 Phase-4 Step-3: CQ Validation

## 개요

15개 Competency Question을 Cypher로 직접 검증한다.

## CQ 데이터셋

`logs/RAN/formal/RAN5/phase-4/cq_test_dataset.json`

## CQ 결과

| CQ | 카테고리 | 질문 | 결과 | rows |
|----|---------|------|------|------|
| CQ1-1 | 변경 근거 | 특정 CR의 변경 이유는? | ✅ PASS | 1 |
| CQ1-2 | 변경 근거 | 특정 CR의 변경 요약은? | ✅ PASS | 1 |
| CQ1-3 | 변경 근거 | 특정 CR의 미승인 영향은? | ✅ PASS | 1 |
| CQ2-1 | Cross-Spec | 특정 CR이 영향주는 다른 Spec 목록은? | ✅ PASS | 2 |
| CQ2-2 | Cross-Spec | 특정 Spec의 CR 중 Cross-Spec 있는 것은? | ✅ PASS | 10 |
| CQ2-3 | Cross-Spec | 특정 Spec을 영향 대상으로 참조하는 CR은? | ✅ PASS | 10 |
| CQ2-4 | Cross-Spec | Cross-Spec 영향이 가장 많은 CR Top 10은? | ✅ PASS | 10 |
| CQ3-1 | CR Pack | 특정 CR Pack의 CR 목록과 변경 요약은? | ✅ PASS | 10 |
| CQ3-2 | CR Pack | 특정 Work Item 관련 CR이 속한 Pack은? | ✅ PASS | 10 |
| CQ3-3 | CR Pack | 특정 TSG 회의에 제출된 CR Pack은? | ✅ PASS | 10 |
| CQ4-1 | 연계 분석 | 특정 Section을 수정하는 CR의 변경 이유는? | ✅ PASS | 10 |
| CQ4-2 | 연계 분석 | 특정 Resolution이 승인한 CR 정보는? | ✅ PASS | 5 |
| CQ4-3 | 연계 분석 | 특정 Work Item CR이 수정하는 Section은? | ✅ PASS | 10 |
| CQ4-4 | 연계 분석 | 특정 회사 CR이 영향주는 다른 Spec은? | ✅ PASS | 10 |
| CQ4-5 | 연계 분석 | 특정 회의 승인 CR의 변경 요약은? | ✅ PASS | 10 |

**합계: 15/15 PASS (100%)**

## Neo4j 검증 (port 7691)

| 항목 | 수치 |
|------|------|
| CRPack 노드 | 1,220 |
| CR with reasonForChange | 23,192 |
| BELONGS_TO_CR_PACK | 23,109 |
| HAS_CR | 23,109 |
| AFFECTS_CORE_SPEC | 77 |
| AFFECTS_TEST_SPEC | 4,990 |
| AFFECTS_OM_SPEC | 1 |
| MODIFIES_SECTION | 31,846 |
| MODIFIED_BY_CR | 31,846 |
| Spec 총 수 | 95 |
