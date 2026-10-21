# Phase-5 Step-3: CQ Validation

## 개요

`validation/01_validate_cq_cypher.py` 가 `logs/tsg/RAN/formal/RAN1/phase-5/cq_test_dataset.json` 의 CQ 18개를 RAN1 Neo4j 에 돌려 판정하고, 결과를 같은 디렉토리의 `cq_cypher_results.json` 에 남긴다.

## 판정 규칙

CQ 마다 아래 순서로 판정한다.

| 판정 | 조건 |
|------|------|
| FAIL | CQ 에 명시한 식별자나 참조하는 스키마가 KG 에 없다(`scripts/tsg/RAN/formal/common/cq_anchor_guard.py` 의 검사). 행 수와 상관없이 FAIL 이다 |
| PASS | 위 검사를 통과하고 결과 행이 1개 이상이다 |
| NO_DATA | 위 검사를 통과했지만 결과 행이 0개다 |
| ERROR | 쿼리 실행 중 예외가 났다 |

PASS 가 전체 CQ 수보다 적으면 종료 코드 1 로 끝난다. NO_DATA 도 게이트를 닫지 못한다.

## CQ 검증 결과

`cq_cypher_results.json` 에 남은 마지막 실행 결과다. 18개 모두 PASS 이고 가드 결함은 0건이다.

| 카테고리 | CQ 수 | PASS | CQ 별 결과 행 수 |
|----------|-------|------|------------------|
| CQ1: TR 연구현황 분석 | 4 | 4 | CQ1-1 1 · CQ1-2 1 · CQ1-3 1 · CQ1-4 1 |
| CQ2: TS 반영영향 추적 | 5 | 5 | CQ2-1 1 · CQ2-2 1 · CQ2-3 11 · CQ2-4 1 · CQ2-5 1 |
| CQ3: 기술별 영향범위 | 3 | 3 | CQ3-1 2 · CQ3-2 1 · CQ3-3 2 |
| CQ4: 릴리스별 연구영향 | 3 | 3 | CQ4-1 7 · CQ4-2 1 · CQ4-3 1 |
| CQ5: TR 간 참조관계 | 3 | 3 | CQ5-1 6 · CQ5-2 4 · CQ5-3 5 |
| 합계 | 18 | 18 | |

CQ2-4 는 38.885 → 38.211 §8(`38.211-Rel-19-8`, Sidelink)에 걸린 TRImpact 를 찾는다. 데이터셋의 `rewrite_notes` 에 Section 키가 release-aware 꼴로 바뀌면서 대상을 옮긴 내력이 있다.

## 실행

```bash
python3 scripts/tsg/RAN/formal/RAN1/phase-5/validation/01_validate_cq_cypher.py
```

접속 주소는 `NEO4J_URI`(기본 `bolt://localhost:7687`), 사용자는 `NEO4J_USER`(기본 `neo4j`), 비밀번호는 저장소 루트의 `.env` 에서 읽는다.

## 관련 문서

- [README](README.md)
- [TR Ontology Spec](design-spec/tdoc_ontology_specs%28TR%29.md)
- [Step-2: Neo4j Loading](step2_neo4j_loading.md)
