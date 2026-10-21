# Step-2: Neo4j Loading

## 개요

`neo4j/01_load_tr_ontology.py` 가 Step-1 의 JSON-LD 를 RAN1 Neo4j(`bolt://localhost:7687`)에 적재한다. 입력은 `ontology/output/tsg/RAN/formal/instances/phase-5/RAN1/` 의 `technical_reports.jsonld` · `tr_impacts.jsonld` 이고, `spec_section_dynamic.jsonld` 는 생성기가 동적 Spec 을 만들었을 때만 있으므로 없어도 된다. TR 과 WorkItem 의 대응은 사람이 만든 `ontology/input/tsg/RAN/formal/TR/RAN1/tr_workitem_mapping.csv` 에서 읽는다.

## 적재 순서

관계가 걸릴 노드를 먼저 만든다.

| 순서 | 하는 일 | 방식 |
|------|---------|------|
| 1 | 인덱스 | `TechnicalReport.trNumber` · `TRImpact.trImpactId` 에 RANGE 인덱스(`IF NOT EXISTS`, 유일 제약 아님) |
| 2 | TechnicalReport | `trNumber` 로 MERGE. trTitle · trVersion · trStatus · scope · conclusions · studyItemRpNumber · workItemRpNumber 를 SET 하고, 빈 값은 null 로 둔다 |
| 3 | TRImpact | `trImpactId` 로 MERGE. impactType · affectedSection · impactDescription 을 SET |
| 4 | 동적 Spec | `spec_section_dynamic.jsonld` 의 Spec 가운데 대표 Spec(`specRelease` 없음)이 없는 번호만 Phase-1 과 같은 `id`(`tdoc:spec/38_291` 꼴)로 만들고 `_dynamicCreated` · `_createdBy='Phase-5'` 를 단다. Spec 이 아닌 항목은 경고만 찍고 적재하지 않는다 |
| 5 | Release | TR 의 targetRelease 가운데 `Rel-NN` 꼴인 값만 Phase-1 과 같은 `id`(`tdoc:release/Rel_18` 꼴)로 MERGE |
| 6 | HAS_TR_IMPACT · IMPACT_OF_TR | TechnicalReport ↔ TRImpact |
| 7 | IMPACTS_SPEC · SPEC_IMPACTED_BY | TRImpact ↔ 대표 Spec. 대표 Spec 이 없으면 간선이 생기지 않는다 |
| 8 | IMPACTS_SECTION · SECTION_IMPACTED_BY | TRImpact ↔ Section, `sectionId` 로 찾는다 |
| 9 | TARGET_RELEASE | TechnicalReport → Release, 5 의 `id` 로 찾는다 |
| 10 | RELATED_TO_WORK_ITEM · HAS_RELATED_TR | TechnicalReport ↔ WorkItem, CSV 의 `workItemCode` 로 찾는다. CSV 가 없으면 exit 1 로 멈추고, 찾지 못한 행은 진단으로 찍는다 |
| 11 | REFERENCES_TR · REFERENCED_BY_TR | TechnicalReport ↔ TechnicalReport. 자기 자신을 인용한 경우는 잇지 않는다 |

노드와 관계는 모두 MERGE 로 만들어 다시 돌려도 늘지 않는다. 적재기가 찍는 노드 수는 MERGE 가 찾은 노드와 만든 노드를 함께 센 값이고, 관계 수는 각 MERGE 가 실제로 잡은 행 수다. 결과는 화면에만 찍고 파일로 남기지 않는다.

`IMPACTS_SPEC` 의 대상을 대표 Spec 으로 한정하는 까닭은 Phase-3 이 같은 specNumber 로 release 별 Spec 노드를 먼저 만들어 두기 때문이다. specNumber 만으로 찾으면 그 노드들에도 간선이 걸린다.

## 적재 결과

RAN1 Neo4j 에서 센 값이다.

| 항목 | 수 |
|------|-----|
| TechnicalReport | 26 |
| TRImpact | 29 (ExtendSection 13 · NewSection 15 · NewTS 1) |
| HAS_TR_IMPACT · IMPACT_OF_TR | 29 · 29 |
| IMPACTS_SPEC · SPEC_IMPACTED_BY | 29 · 29 (대상 대표 Spec 5개, 모두 `id` 있음) |
| IMPACTS_SECTION · SECTION_IMPACTED_BY | 21 · 21 |
| TARGET_RELEASE | 26 |
| RELATED_TO_WORK_ITEM · HAS_RELATED_TR | 26 · 26 (WorkItem 25개) |
| REFERENCES_TR · REFERENCED_BY_TR | 25 · 25 (자기 참조 0) |
| 동적 Spec | 0 |
| 관계 합계 | 286 (11 종) |

- TRImpact 가 없는 TR 은 9개다. CSV 의 NoChange 8개(38.760-1 · 38.802 · 38.808 · 38.812 · 38.858 · 38.859 · 38.900 · 38.901)와 CSV 에 행이 없는 38.857 이다.
- TARGET_RELEASE 는 Rel-14 1 · Rel-15 1 · Rel-16 7 · Rel-17 5 · Rel-18 6 · Rel-19 2 · Rel-20 4 이고, 대상 Release 는 모두 `id` 가 있다.
- WorkItem 이 25개인 것은 38.900 과 38.901 이 같은 `FS_6GHz_CH_model` 에 이어지기 때문이다.
- conclusions 가 없는 TR 은 5개, studyItemRpNumber 가 없는 TR 은 2개, workItemRpNumber 가 없는 TR 은 25개다.

`IMPACTS_SECTION` 이 없는 TRImpact 8개는 NewTS 인 38.769 → 38.291 과, 아직 없는 절을 새로 만드는 NewSection 7개(38.889 §16 × 3 · 38.875 §8.9 · 38.869 §17 · 38.765 §18 · 38.867 §19)다. 이어진 21개는 모두 Rel-19 Section(`38.213-Rel-19-16` 꼴)에 걸려 있다.

주의: 절 번호는 사람이 적은 CSV 값을 번호만으로 Section 에 잇는 것이라, 이어진 절의 제목이 TR 주제와 맞지 않는 경우가 있다. 예를 들어 38.889 → 38.213 §16 은 「UE procedures for sidelink」 절에 이어진다. 다른 예와 원인은 [Step-1](step1_tr_parsing.md) 의 「생성 결과」 주의를 본다.

## 실행

```bash
python3 scripts/tsg/RAN/formal/RAN1/phase-5/neo4j/01_load_tr_ontology.py
```

접속 주소는 `NEO4J_URI`(기본 `bolt://localhost:7687`), 사용자는 `NEO4J_USER`(기본 `neo4j`), 비밀번호는 저장소 루트의 `.env` 에서 읽는다.

여러 release 에 걸쳐 갱신되는 TR 의 release 별 Spec 노드는 `neo4j/02_load_tr_release_specs.py` 가 따로 적재한다. [README](README.md) 의 「여러 release 에 걸쳐 갱신되는 TR 의 release 별 노드」를 본다.

## 관련 문서

- [README](README.md)
- [TR Ontology Spec](design-spec/tdoc_ontology_specs%28TR%29.md)
- [Step-1: TR Parsing & JSON-LD Generation](step1_tr_parsing.md)
- [Step-3: CQ Validation](step3_validation.md)
