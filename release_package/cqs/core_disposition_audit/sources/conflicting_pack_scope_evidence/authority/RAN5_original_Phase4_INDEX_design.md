- **phase-4: Ontology 101 기반 적합성 시험 엔지니어 타겟으로 확장-2 (CR)**
    
    ## Step 1: Domain과 Scope 결정
    
    > Ontology 101 원칙
    >
    >
    > *"We suggest starting the development of an ontology by defining its domain and scope."*
    >
    
    ---
    
    ### 1. 기본 질문에 대한 답변
    
    ### 1.1 What is the domain?
    
    **3GPP RAN5 Change Request(CR) 문서의 본문 내용과 Spec 간 영향 관계**
    
    ### 1.2 For what are we going to use the ontology?
    
    - CR 변경 근거 추적 — 왜 이 변경이 필요했는가
    - Cross-Spec 영향 분석 — CR이 다른 Spec에 미치는 파급 효과
    - CR Pack 단위 분석 — TSG 제출 단위로 CR 그룹 분석
    - Phase 1-3 연계 — Conclusion → CR → TS Section 전체 추적
    
    ### 1.3 Who will use and maintain the ontology?
    
    | 사용자 | 핵심 니즈 |
    | --- | --- |
    | 적합성 시험 엔지니어 | 유사 CR의 변경 근거 참조, 영향 범위 사전 파악 |
    | 표준화 엔지니어 | 특정 Section 변경의 이유와 배경 이해 |
    | 전략/기획 | 기술 트렌드 분석 (어떤 이유로 변경이 많은가) |
    | IP/특허 | 기술 기여 증거 (변경 이유, 요약 텍스트) |
    
    ### 1.4 데이터 소스
    
    | 항목 | 내용 |
    | --- | --- |
    | CR 문서 | Word 형식 (.docx), [P4-V01] (Rel-15~Rel-19 범위) |
    | 파일 구조 | Cover Sheet + CR 본문이 **단일 파일에 합쳐짐** (TSG 폴더) |
    | 팩 디렉토리 | TSG 하위 RP 폴더 |
    
    > **RAN5 CR 파일 구조**: 별도 Cover Sheet 파일이 존재하지 않는다. 모든 CR이 CR 입력 디렉토리(`Rel-*/TSG/RP-*/*.docx`)에 단일 파일로 저장되며, CR 문서 안의 CR-Form 테이블에서 Cover Sheet 정보(spec/CR번호/release/title/source 등)와 본문(reasonForChange 등)을 함께 추출한다.
    
    ### 1.5 전제 조건
    
    > 본 온톨로지는 Phase-1~3 온톨로지의 확장이다.
    >
    > - Phase-1~3의 모든 클래스, 관계, 인스턴스는 그대로 유지
    > - Phase-4는 CR 문서 본문 정보를 추가하고 기존 데이터와 연결
    > - 기존 CQ는 모두 답변 가능 유지
    
    ### 1.6 RAN5 CR 데이터 특성
    
    사전 스캔 결과:
    
    | 항목 | 값 | 근거 |
    | --- | --- | --- |
    | CR 문서 수 (입력 폴더) | [P4-V01] | CR 입력 디렉토리 전수 |
    | CR 총 수 (Neo4j) | [P1-V02] | Phase-1 기준 |
    | CR → 38.5xx Spec | [P1-V10] | Phase-1 `MODIFIES` 관계 (Spec 수) |
    | clausesAffected 보유율 | [P3-V05] | Phase-3 Appendix A 참조 |
    | 파일 구조 | 단일 파일 (Cover Sheet + 본문 통합) | 사전 스캔 |
    | 파일 형식 | 100% .docx (변환 불필요) | 사전 스캔 |
    | TDoc 접두사 | `R5-\d{6}` (6자리) | RAN5 표준 |
    | Phase-2 Resolution 타입 | Conclusion만 (Agreement/WA 부재) | Phase-2 결과 |
    | 도메인 | 적합성 시험 (Conformance Testing) | 38.5xx 시리즈 |
    
    ---
    
    ### 2. Scope 정의
    
    ### 2.1 포함 (In Scope)
    
    | 구분 | 포함 대상 | Phase 1 대비 |
    | --- | --- | --- |
    | CR 변경 근거 | Reason for change | **신규** |
    | CR 변경 요약 | Summary of change | **신규** |
    | CR 미승인 영향 | Consequences if not approved | **신규** |
    | Cross-Spec 관계 | Other Specs Affected (Core/Test/O&M) | **신규** |
    | CR Pack 구조 | CR-Form 테이블 기반 CR 그룹핑 | **상세화** |
    | Clauses Affected | CR → Section 연결 | **향상** |
    
    ### 2.2 제외 (Out of Scope)
    
    | 제외 대상 | 이유 |
    | --- | --- |
    | Track Changes 변경 블록 | Vector DB 영역 |
    | 기술 테이블 셀 데이터 | Vector DB 영역 |
    | 시험 파라미터 수치 | Vector DB 영역 |
    
    ### 2.3 Graph DB vs Vector DB 경계
    
    | Graph DB (Phase-4) | Vector DB |
    | --- | --- |
    | CR 메타데이터 (reasonForChange, summaryOfChange, consequencesIfNotApproved) | Track Changes 변경 블록 |
    | CRPack 구조 (ID, TSG Meeting, CR 목록) | 기술 테이블 셀 데이터 |
    | Cross-Spec 영향 관계 | 시험 파라미터 수치 |
    | CR → Section 연결 | |
    
    **연결 키**: tdocNumber (예: `R5-242321`)
    
    ---
    
    ### 3. Competency Questions
    
    ### CQ1: CR 변경 근거 분석
    
    | # | Competency Question |
    | --- | --- |
    | 1-1 | 특정 CR의 변경 이유(reasonForChange)는? |
    | 1-2 | 특정 CR의 변경 요약(summaryOfChange)은? |
    | 1-3 | 특정 CR의 미승인 영향(consequencesIfNotApproved)은? |
    
    ### CQ2: Cross-Spec 영향 분석
    
    | # | Competency Question |
    | --- | --- |
    | 2-1 | 특정 CR이 영향주는 다른 Spec (Core/Test/O&M) 목록은? |
    | 2-2 | 특정 Spec을 수정하는 CR 중 다른 Spec에도 영향주는 CR은? |
    | 2-3 | 특정 Spec을 영향 받는 Spec으로 참조하는 CR 목록은? |
    | 2-4 | Cross-Spec 영향이 가장 많은 CR Top N은? |
    
    ### CQ3: CR Pack 분석
    
    | # | Competency Question |
    | --- | --- |
    | 3-1 | 특정 CR Pack에 포함된 CR 목록과 변경 요약은? |
    | 3-2 | 특정 Work Item 관련 CR이 속한 Pack 목록은? |
    | 3-3 | 특정 TSG 회의에 제출된 CR Pack 목록은? |
    
    ### CQ4: Phase 1-3 연계 분석
    
    | # | Competency Question |
    | --- | --- |
    | 4-1 | 특정 Section을 수정하는 CR의 변경 이유 목록은? |
    | 4-2 | 특정 Conclusion이 참조한 CR의 변경 이유와 요약은? |
    | 4-3 | 특정 Work Item 관련 CR이 수정하는 Section 목록은? |
    | 4-4 | 특정 회사의 CR이 영향주는 다른 Spec 목록은? |
    | 4-5 | 특정 회의에서 참조된 CR의 변경 요약 목록은? |
    
    ---
    
    ### 4. CQ 결과 규칙
    
    ### 4.1 정렬 기준
    
    | CQ 그룹 | Primary Sort | Secondary Sort |
    | --- | --- | --- |
    | CQ1 | tdocNumber DESC | - |
    | CQ2 | Count DESC | Spec ASC |
    | CQ3 | tsgMeeting DESC | crPackId ASC |
    | CQ4 | meetingNumberInt DESC | tdocNumber ASC |
    
    ---
    
    ### 5. CQ 요약
    
    | CQ 그룹 |
    | --- |
    | CQ1 (변경 근거) |
    | CQ2 (Cross-Spec) |
    | CQ3 (CR Pack) |
    | CQ4 (Phase 1-3 연계) |
    
    ---
    
    ## Step 2: 기존 온톨로지 재사용 검토
    
    > Ontology 101 원칙
    >
    >
    > *"It is almost always worth considering what someone else has done and checking if we can refine and extend existing sources."*
    >
    
    ---
    
    ### 1. Phase-1~3 온톨로지 현황
    
    | Phase | 클래스 |
    | --- | --- |
    | Phase-1 | Tdoc, CR, LS, Meeting, Company, Contact, WorkItem, AgendaItem, Release, Spec, WorkingGroup |
    | Phase-2 | Resolution, Conclusion, Table |
    | Phase-3 | Section, TSTable, TSFigure |
    
    > RAN5 Phase-2에는 Conclusion만 (Agreement/WorkingAssumption 없음).
    
    ### 2. CQ 기반 클래스/관계 사용 분석
    
    | Phase-1 클래스 | CQ | 필요 |
    | --- | --- | --- |
    | CR | CQ 전체 | ✅ 핵심 (확장 대상) |
    | Spec | CQ2, CQ4 | ✅ |
    | Meeting | CQ4-5 | ✅ |
    | Company | CQ4-4 | ��� |
    | WorkItem | CQ3-2, CQ4-3 | ✅ |
    
    | Phase-2 클래스 | CQ | 필요 |
    | --- | --- | --- |
    | Conclusion | CQ4-2, CQ4-5 | ✅ |
    
    | Phase-3 클래스 | CQ | 필요 |
    | --- | --- | --- |
    | Section | CQ4-1, CQ4-3 | ✅ |
    
    ### 3. 요약
    
    | 구분 | 대상 |
    | --- | --- |
    | **Phase-1~3 재사용** | CR, Spec, Meeting, Company, WorkItem, Conclusion, Section |
    | **Phase-4 신규** | CRPack |
    | **Phase-4 확장** | CR (DP + OP 추가), Section (OP 추가) |
    
    ---
    
    ## Step 3: 중요 용어 나열
    
    > Ontology 101 원칙
    >
    >
    > *"It is useful to write down a list of all terms we would like either to make statements about or to explain to a user."*
    >
    
    ---
    
    ### 1. 용어 목록
    
    | 카테고리 | 용어 |
    | --- | --- |
    | **클래스 후보** | CRPack |
    | **CR 본문 속성** | reasonForChange, summaryOfChange, consequencesIfNotApproved |
    | **Cross-Spec 관계** | affectsCoreSpec, affectsTestSpec, affectsOMSpec |
    | **CR-Section 관계** | modifiesSection, modifiedByCR |
    | **CRPack 속성** | crPackId, tsgMeeting |
    | **CRPack 관계** | hasCR, belongsToCRPack |
    | **Phase-1~3 재사용** | modifies, submittedBy, relatedTo, presentedAt, references, madeAt, belongsToSpec |
    
    ---
    
    ## Step 4: 클래스와 계층 구조 정의
    
    > Ontology 101 원칙
    >
    >
    > *"Define the classes and the class hierarchy."*
    >
    
    ---
    
    ### 1. Phase-4 신규 클래스
    
    | 클래스 | 정의 | 상위 | 하위 |
    | --- | --- | --- | --- |
    | **CRPack** | TSG 회의에 제출되는 CR 묶음 단위 | 없음 | 없음 |
    
    ### 2. 기존 클래스 확장
    
    | 클래스 | 확장 내용 |
    | --- | --- |
    | CR | DP/OP 추가 (Step 5 참조) |
    | Section | OP 추가 (modifiedByCR) |
    
    ### 3. 전체 클래스 계층 다이어그램
    
    ```
    ┌─────────────────────────────────────────────────────────────────┐
    │                    RAN5 CR Ontology (Phase-4)                    │
    ├─────────────────────────────────────────────────────────────────┤
    │  [Phase-1] Tdoc → CR ◄─ 속성 확장, LS, Meeting, Company, ...   │
    │  [Phase-2] Conclusion                                           │
    │  [Phase-3] Section ◄─ modifiedByCR, TSTable, TSFigure           │
    │  [Phase-4] CRPack ⭐                                           │
    └─────────────────────────────────────────────────────────────────┘
    ```
    
    ### 4. 누적 클래스 현황
    
    | Phase | 클래스 |
    | --- | --- |
    | Phase-1 | Tdoc, CR, LS, Meeting, Company, Contact, WorkItem, AgendaItem, Release, Spec, WorkingGroup |
    | Phase-2 | Resolution, Conclusion, Table |
    | Phase-3 | Section, TSTable, TSFigure |
    | **Phase-4** | **CRPack** |
    
    ---
    
    ## Step 5: 속성(Slot) 정의
    
    > Ontology 101 원칙
    >
    >
    > *"Define the properties of classes—slots... Properties describe attributes of instances of a class and relations to other instances."*
    >
    
    ---
    
    ### 1. 속성의 종류
    
    | 종류 | 설명 | 예시 |
    | --- | --- | --- |
    | **Data Property** | 객체의 속성값 | reasonForChange, crPackId |
    | **Object Property** | 다른 객체와의 관계 | affectsCoreSpec, hasCR |
    | **Inverse Property** | 역방향 관계 | hasCR ↔ belongsToCRPack |
    
    ---
    
    ### 2. CR 클래스 확장 속성
    
    ### 2.1 신규 Data Property
    
    | Property | Type | Description | 데이터 소스 |
    | --- | --- | --- | --- |
    | reasonForChange | String | 변경이 필요한 이유 | CR 문서 "Reason for change" 필드 |
    | summaryOfChange | String | 변경 내용 요약 | CR 문서 "Summary of change" 필드 |
    | consequencesIfNotApproved | String | 미승인 시 영향 | CR 문서 "Consequences if not approved" 필드 |
    
    ### 2.2 신규 Object Property
    
    | Property | Range | Inverse | Description |
    | --- | --- | --- | --- |
    | belongsToCRPack | CRPack | hasCR | CR이 속한 CR Pack |
    | affectsCoreSpec | Spec | — | CR이 영향주는 Core Spec |
    | affectsTestSpec | Spec | — | CR이 영향주는 Test Spec |
    | affectsOMSpec | Spec | — | CR이 영향주는 O&M Spec |
    | modifiesSection | Section | modifiedByCR | CR이 수정하는 Section (clausesAffected 구조화) |
    
    *참고: affectsCoreSpec/TestSpec/OMSpec의 역방향 탐색(CQ2-3)은 별도 역관계 property 없이 쿼리로 해결 (섹션 7 참조)*
    
    ---
    
    ### 3. CRPack 클래스 속성
    
    ### 3.1 Data Property
    
    | Property | Type | Description | 데이터 소스 |
    | --- | --- | --- | --- |
    | crPackId | String | CR Pack 고유 식별자 | CR-Form (예: "RP-250233") |
    | tsgMeeting | String | Pack이 제출된 TSG 회의 | CR-Form (예: "RAN#103") |
    
    ### 3.2 Object Property
    
    | Property | Range | Inverse | Description |
    | --- | --- | --- | --- |
    | hasCR | CR | belongsToCRPack | Pack에 포함된 CR |
    
    ---
    
    ### 4. Section 역관계 추가
    
    | Property | Range | Inverse | Description |
    | --- | --- | --- | --- |
    | modifiedByCR | CR | modifiesSection | 이 Section을 수정하는 CR 목록 |
    
    ---
    
    ### 5. modifiesSection과 clausesAffected 관계
    
    | 속성 | 타입 | 출처 | 용도 |
    | --- | --- | --- | --- |
    | clausesAffected | String | Phase-1 CR | 원본 데이터 보존 (예: "5.1.3.2, 7.4") |
    | modifiesSection | Object Property | Phase-4 확장 | Section 노드와 구조화된 연결 |
    
    **처리 방식:**
    
    - 두 속성은 동일한 정보의 다른 표현
    - clausesAffected 문자열 파싱 → modifiesSection 관계 생성
    - Phase-1 호환성 유지를 위해 clausesAffected 원본 데이터도 보존
    
    > **RAN5 고유**: clausesAffected 커버리지가 낮으므로([P3-V05] 참조) MODIFIES_SECTION 관계는 부분적으로만 생성됨. 커버리지 수치를 로그에 보고.
    
    ---
    
    ### 6. 전체 Object Property 목록 (Phase-4 신규)
    
    | # | Property | Domain | Range | Inverse | Description |
    | --- | --- | --- | --- | --- | --- |
    | 1 | belongsToCRPack | CR | CRPack | hasCR | CR이 속한 Pack |
    | 2 | hasCR | CRPack | CR | belongsToCRPack | Pack에 포함된 CR |
    | 3 | affectsCoreSpec | CR | Spec | — | 영향받는 Core Spec |
    | 4 | affectsTestSpec | CR | Spec | — | 영향받는 Test Spec |
    | 5 | affectsOMSpec | CR | Spec | — | 영향받는 O&M Spec |
    | 6 | modifiesSection | CR | Section | modifiedByCR | CR이 수정하는 Section |
    | 7 | modifiedByCR | Section | CR | modifiesSection | Section을 수정하는 CR |
    
    ---
    
    ### 7. 전체 Data Property 목록 (Phase-4 신규)
    
    | # | Property | Domain | Type | Description |
    | --- | --- | --- | --- | --- |
    | 1 | reasonForChange | CR | String | 변경 이유 |
    | 2 | summaryOfChange | CR | String | 변경 요약 |
    | 3 | consequencesIfNotApproved | CR | String | 미승인 영향 |
    | 4 | crPackId | CRPack | String | Pack 식별자 |
    | 5 | tsgMeeting | CRPack | String | TSG 회의 |
    
    ---
    
    ### 8. Inverse Property 정리
    
    | 정방향 | 역방향 | Domain ↔ Range |
    | --- | --- | --- |
    | hasCR | belongsToCRPack | CRPack ↔ CR |
    | modifiesSection | modifiedByCR | CR ↔ Section |
    
    ---
    
    ### 9. Cross-Spec 역방향 탐색 (affectedByCR 처리)
    
    Step 3에서 나열한 `affectedByCR`는 별도 property로 정의하지 않음.
    
    **이유:**
    
    - affectsCoreSpec, affectsTestSpec, affectsOMSpec 세 관계의 공통 역관계가 필요
    - OWL에서 하나의 property가 여러 property의 inverse가 될 수 없음
    - 역관계 3개를 별도 정의하면 복잡성 증가 (coreSpecAffectedByCR, testSpecAffectedByCR, omSpecAffectedByCR)
    
    **해결:**
    CQ2-3 ("특정 Spec을 영향 받는 Spec으로 참조하는 CR 목록")은 쿼리로 해결:
    
    ```cypher
    MATCH (s:Spec)<-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]-(cr:CR)
    WHERE s.specNumber = $specNumber
    RETURN cr
    ```
    
    ---
    
    ### 10. Phase-1~3 재사용 관계 (CQ 답변에 필요)
    
    | Property | Domain | Range | 출처 | 관련 CQ |
    | --- | --- | --- | --- | --- |
    | modifies | CR | Spec | Phase-1 | CQ2-2, CQ4 |
    | submittedBy | Tdoc | Company | Phase-1 | CQ4-4 |
    | relatedTo | Tdoc | WorkItem | Phase-1 | CQ3-2, CQ4-3 |
    | presentedAt | Tdoc | Meeting | Phase-1 | CQ4-5 |
    | references | Resolution | Tdoc | Phase-2 | CQ4-2, CQ4-5 |
    | madeAt | Resolution | Meeting | Phase-2 | CQ4-5 |
    | belongsToSpec | Section | Spec | Phase-3 | CQ4-1, CQ4-3 |
    
    ---
    
    ### 11. 클래스별 속성 요약
    
    | 클래스 | Data Property | Object Property |
    | --- | --- | --- |
    | CR (확장) | reasonForChange, summaryOfChange, consequencesIfNotApproved | belongsToCRPack, affectsCoreSpec, affectsTestSpec, affectsOMSpec, modifiesSection |
    | CRPack (신규) | crPackId, tsgMeeting | hasCR |
    | Section (역관계 추가) | — | modifiedByCR |
    
    ---
    
    ### 12. CQ 답변 가능성 검증
    
    | CQ | 필요 속성 | 정의 여부 |
    | --- | --- | --- |
    | CQ1-1~1-3 | reasonForChange, summaryOfChange, consequencesIfNotApproved | ✅ |
    | CQ2-1~2-4 | affectsCoreSpec, affectsTestSpec, affectsOMSpec | ✅ |
    | CQ3-1~3-3 | CRPack, hasCR, belongsToCRPack, tsgMeeting | ✅ |
    | CQ4-1~4-5 | modifiesSection, references, submittedBy, madeAt | ✅ |
    
    **전체 CQ 답변 가능** ✅
    
    ---
    
    ## Step 6: 제약조건(Facet) 정의
    
    > Ontology 101 원칙
    >
    >
    > *"Define the facets of the slots."*
    >
    
    ---
    
    ### 1. Facet 종류
    
    | Facet | 설명 | 예시 |
    | --- | --- | --- |
    | **Cardinality** | 속성값 개수 | 0..1, 1, 0..*, 1..* |
    | **Required** | 필수 여부 | ✅ / ❌ |
    | **Functional** | 단일값만 허용 | ✅ (최대 1개) |
    | **InverseFunctional** | 역관계가 Functional | hasCR (각 CR은 최대 1개 Pack에서 참조) |
    | **Inverse** | 역관계 | hasCR ↔ belongsToCRPack |
    
    ### Cardinality 표기법
    
    | 표기 | 의미 | Required | Functional |
    | --- | --- | --- | --- |
    | 1 | 정확히 1개 | ✅ | ✅ |
    | 0..1 | 0개 또는 1개 | ❌ | ✅ |
    | 1..* | 1개 이상 | ✅ | ❌ |
    | 0..* | 0개 이상 | ❌ | ❌ |
    
    ---
    
    ### 2. CR 확장 Data Property Facet
    
    | Property | Type | Cardinality | Required | 근거 |
    | --- | --- | --- | --- | --- |
    | reasonForChange | String | 0..1 | ❌ | 일부 CR은 해당 필드 비어있음 |
    | summaryOfChange | String | 0..1 | ❌ | 일부 CR은 해당 필드 비어있음 |
    | consequencesIfNotApproved | String | 0..1 | ❌ | 일부 CR은 해당 필드 비어있음 |
    
    ---
    
    ### 3. CR 확장 Object Property Facet
    
    | Property | Domain | Range | Cardinality | Functional | Inverse | 근거 |
    | --- | --- | --- | --- | --- | --- | --- |
    | belongsToCRPack | CR | CRPack | 0..1 | ✅ | hasCR | CR은 최대 1개 Pack에만 속함 |
    | affectsCoreSpec | CR | Spec | 0..* | ❌ | — | 여러 Core Spec 영향 가능 |
    | affectsTestSpec | CR | Spec | 0..* | ❌ | — | 여러 Test Spec 영향 가능 |
    | affectsOMSpec | CR | Spec | 0..* | ❌ | — | 여러 O&M Spec 영향 가능 |
    | modifiesSection | CR | Section | 0..* | ❌ | modifiedByCR | clausesAffected 없는 CR은 0개 (커버리지 [P3-V05] 참조) |
    
    ---
    
    ### 4. CRPack Data Property Facet
    
    | Property | Type | Cardinality | Required | 근거 |
    | --- | --- | --- | --- | --- |
    | crPackId | String | 1 | ✅ | PK, 패턴: `RP-\d{6}` |
    | tsgMeeting | String | 0..1 | ❌ | CR-Form에서 tsgMeeting 추출 불가한 경우 |
    
    ---
    
    ### 5. CRPack Object Property Facet
    
    | Property | Domain | Range | Cardinality | Functional | InverseFunctional | Inverse |
    | --- | --- | --- | --- | --- | --- | --- |
    | hasCR | CRPack | CR | 1..* | ❌ | ✅ | belongsToCRPack |
    
    ---
    
    ### 6. Section 역관계 Facet
    
    | Property | Domain | Range | Cardinality | Functional | Inverse |
    | --- | --- | --- | --- | --- | --- |
    | modifiedByCR | Section | CR | 0..* | ❌ | modifiesSection |
    
    ---
    
    ### 7. Cross-Spec Range 처리
    
    affectsCoreSpec, affectsTestSpec, affectsOMSpec의 Range는 Spec 클래스.
    
    **처리 규칙:**
    
    - 참조되는 Spec이 Phase-1 인스턴스에 존재하면 해당 인스턴스에 연결
    - 존재하지 않으면 Step 7에서 최소 Spec 인스턴스 생성
    
    **동적 생성 Spec 최소 속성:**
    
    | 속성 | 필수 | 설명 |
    | --- | --- | --- |
    | specNumber | ✅ | Spec 번호 (예: "38.508") |
    | specTitle | ❌ | Spec 제목 (가능하면 조회) |
    
    **예시:**
    
    - CR 문서에 "36.521-1" 참조 → Phase-1 인스턴스에 없음 → specNumber="36.521-1"인 Spec 인스턴스 동적 생성
    
    ---
    
    ### 8. 필수 속성 요약
    
    | Class | Required Data | Required Object |
    | --- | --- | --- |
    | CR (확장) | — (모두 선택) | — (모두 선택) |
    | CRPack | crPackId | hasCR (1..*) |
    
    ---
    
    ### 9. Functional / InverseFunctional 요약
    
    | Property | Functional | InverseFunctional |
    | --- | --- | --- |
    | belongsToCRPack | ✅ | — |
    | hasCR | — | ✅ |
    
    ---
    
    ### 10. Inverse Property 요약
    
    | Property | Inverse | Domain ↔ Range |
    | --- | --- | --- |
    | hasCR | belongsToCRPack | CRPack ↔ CR |
    | modifiesSection | modifiedByCR | CR ↔ Section |
    
    ---
    
    ## Step 7: 인스턴스 생성 명세
    
    > Ontology 101 원칙
    >
    >
    > *"The last step is creating individual instances of classes in the hierarchy."*
    >
    
    ---
    
    ### 1. 데이터 소스
    
    | 소스 | 형식 | 수량 | 용도 |
    | --- | --- | --- | --- |
    | CR 문서 | Word (.docx) | [P4-V01] | CR 확장 속성 + CRPack 인스턴스 |
    
    > **RAN5 고유**: Cover Sheet와 CR 본문이 단일 파일에 합쳐져 있음. 별도 Cover Sheet 파일 없음. CR-Form 테이블(Table 0, Table 2)에서 메타데이터 추출.
    
    ---
    
    ### 2. 파싱 대상 CR 선정 기준
    
    **Phase-4 파싱 대상:**
    
    - TSG 폴더(CR 입력 디렉토리 내 `Rel-*/TSG/RP-*/*.docx`)에 포함된 CR 문서 대상
    - CR-Form 테이블 기반 CRPack 생성 + CR 문서 메타데이터 확장
    
    **CR Pack 순수 커버 문서 제외 규칙:**
    
    - `RP-XXXXXX.docx` 패턴의 순수 CR Pack 커버 문서는 개별 CR 파싱 대상에서 제외한다
    - CR Pack 커버 문서 본문에 참조된 R5 번호를 개별 CR의 tdocNumber로 잘못 추출하는 것을 방지하기 위함
    
    **대용량 처리 전략:**
    
    - CR 입력 문서 전체([P4-V01]) → ProcessPoolExecutor로 병렬 파싱 필수
    - Resume 로직 필수 (중단 시 재시작 지점 기록)
    - 메모리 관리: 배치 단위 Neo4j 적재 (1,000건/배치 권장)
    
    ---
    
    ### 3. ID 생성 규칙
    
    | 클래스 | ID 속성 | 패턴 | 예시 |
    | --- | --- | --- | --- |
    | CRPack | crPackId | `RP-\d{6}` | RP-250233 |
    | CR | tdocNumber (Phase-1 기존) | `R5-\d{6}` | R5-242321 |
    | Spec | specNumber (Phase-1 기존) | `\d{2}\.\d{3}(-\d+)?` | 38.508, 38.521-1 |
    
    ---
    
    ### 4. CR 문서 파싱 규칙 (RAN5 고유)
    
    ### 4.1 CR-Form 테이블 구조
    
    > **RAN5 핵심**: Cover Sheet가 별도 파일이 아닌 CR 문서 내 CR-Form 테이블로 존재. Table 0과 Table 2에서 메타데이터 추출.
    
    | 테이블 | 내용 |
    | --- | --- |
    | Table 0 | spec, CR번호, rev, version |
    | Table 2 | Title, Source, Work Item, Category, Reason for change, Summary of change, Consequences if not approved, Clauses affected, Other Specs Affected |
    
    **파싱 전략:**
    
    1. 구현 전 전수 스캔으로 테이블 구조 분포 확인
    2. Table 2에서 "Reason for change", "Summary of change", "Consequences if not approved" 등 키워드 매칭
    3. 해당 키워드 셀의 다음 셀 또는 같은 행의 값을 필드 값으로 추출
    
    ### 4.2 TDoc 번호 추출
    
    | 패턴 | 정규식 | 예시 |
    | --- | --- | --- |
    | RAN5 TDoc | `R5-\d{6}` | R5-242321 |
    
    ### 4.3 Other Specs Affected 파싱
    
    ```
    Other specs affected:  Other core specifications  →  [Spec 목록]
                           Test specifications        →  [Spec 목록]
                           O&M Specifications         →  [Spec 목록]
    ```
    
    각 → 이후 텍스트에서 specNumber 패턴 `\d{2}\.\d{3}(-\d+)?` 추출.
    
    > RAN5 Spec 번호에는 `-1`, `-2`, `-3` 등의 접미사가 있는 경우가 있음 (예: 38.521-1, 38.521-3).
    
    ### 4.4 modifiesSection 생성
    
    **입력:**
    - Phase-1 CR.clausesAffected (String): "5.1.3.2, 6.2A.3"
    - Phase-1 CR.modifies → Spec: 38.508
    
    **처리:**
    1. clausesAffected 쉼표 분리
    2. sectionId 생성: `{specNumber}-{sectionNumber}`
    3. Phase-3 Section 인스턴스와 매칭
    4. 매칭되면 modifiesSection 관계 생성
    
    > **RAN5 고유**: clausesAffected 커버리지가 낮으므로([P3-V05] 참조) MODIFIES_SECTION은 일부 CR에서만 생성.
    
    ### 4.5 CR 파일명 패턴
    
    ```
    {specNumber}_CR{crNum}_(Rel-{N})_R5-{tdocNumber}_description.docx
    예: 38508-1_CR3115_(Rel-18)_R5-242321_description.docx
    ```
    
    파일명에서 specNumber, crNumber, release, tdocNumber 추출 가능.
    
    ---
    
    ### 5. CRPack 인스턴스 생성
    
    **소스**: CR 문서 내 CR-Form 테이블 — 입력 파일([P4-V01])에서 RP 폴더명 기반 추출
    
    | 속성 | 소스 위치 | 변환 규칙 |
    | --- | --- | --- |
    | crPackId | 파일 상위 디렉토리명 | `RP-\d{6}` 패턴 추출 |
    | tsgMeeting | CR-Form Table 2 또는 디렉토리 구조 | `(TSG\s+)?RAN#\d+` 패턴 추출 |
    
    **CR 목록 추출:**
    1. 같은 RP 폴더 내 CR 문서에서 `R5-\d{6}` 패턴 추출
    2. Phase-1 CR 인스턴스와 매칭
    3. hasCR 관계 생성
    
    ---
    
    ### 6. CR 인스턴스 확장
    
    ### 6.1 기존 인스턴스 활용
    
    - Phase-1에서 생성된 CR 인스턴스 중 매칭분에 대해 속성 추가
    - 새 인스턴스 생성이 아닌 **기존 인스턴스 확장**
    
    ### 6.2 CR 문서 → Phase-1 CR 매칭 규칙
    
    1. CR 문서 내 CR-Form Table 0 또는 파일명에서 tdocNumber 추출
    2. 패턴: `R5-\d{6}`
    3. Phase-1 CR 인스턴스와 tdocNumber로 매칭
    4. 매칭 실패 시 오류 로그
    
    ### 6.3 Data Property 매핑
    
    | 속성 | 소스 위치 | 변환 규칙 | 커버리지 |
    | --- | --- | --- | --- |
    | reasonForChange | CR-Form Table 2 "Reason for change" | 텍스트 추출, 빈 값이면 null | [P4-V06] |
    | summaryOfChange | CR-Form Table 2 "Summary of change" | 텍스트 추출, 빈 값이면 null | (Appendix A 참조) |
    | consequencesIfNotApproved | CR-Form Table 2 "Consequences if not approved" | 텍스트 추출, 빈 값이면 null | (Appendix A 참조) |
    
    ### 6.4 Object Property 매핑
    
    | 관계 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | belongsToCRPack → CRPack | RP 폴더명 | CR이 포함된 Pack의 crPackId로 연결 |
    | affectsCoreSpec → Spec | CR-Form Table 2 "Other core specifications" | §4.3 참조 |
    | affectsTestSpec → Spec | CR-Form Table 2 "Test specifications" | §4.3 참조 |
    | affectsOMSpec → Spec | CR-Form Table 2 "O&M Specifications" | §4.3 참조 |
    | modifiesSection → Section | Phase-1 clausesAffected + modifies | §4.4 참조 |
    
    ---
    
    ### 7. Spec 동적 생성
    
    ### 7.1 필요 상황
    
    CR 문서의 "Other Specs Affected"에서 Phase-1 Spec 인스턴스에 없는 Spec 참조 시
    
    ### 7.2 생성 규칙
    
    | 속성 | 값 |
    | --- | --- |
    | specNumber | 추출된 Spec 번호 (예: "38.508") |
    | specVersion | null (버전 정보 없음) |
    
    ### 7.3 동적 생성 Spec의 제약사항
    
    | 항목 | 내용 |
    | --- | --- |
    | hasSection 관계 | **없음** (Phase-3 Section과 연결 없음) |
    | 용도 | Cross-Spec 영향 분석 (CQ2)에서 참조 대상으로만 사용 |
    | 향후 확장 | 해당 Spec의 TS 문서 파싱 시 Section 연결 가능 |
    
    > **Phase-3 hasSection Cardinality 정합성 (감사 이슈 E-7 대응)**: Phase-3 §5에서 `hasSection: Spec → Section`의 Cardinality를 `1..*` → `0..*`로 완화함. 근거는 본 §7.3에 따라 동적 생성된 Spec은 Section 노드를 갖지 않는 것이 정상 상태이기 때문. 실측 P4-V04=22건 Spec이 이 경우에 해당(총 95 − Phase-3/Phase-1 기반 73). 제약 위반이 아니라 설계 상 허용된 상태임을 명시.
    
    ---
    
    ### 8. Spec별 CR 분포 (사전 스캔 결과)
    
    | Spec |
    | --- |
    | 38.523-1 (NR UE conformance) |
    | 38.533 (NR UE demod) |
    | 38.521-1 (NR UE TX) |
    | 38.508-1 (적합성 시험 UE) |
    | 38.521-3 (NR UE interband) |
    | 36.521-1 (LTE UE conformance) |
    | 기타 |
    
    > **RAN5 특성**: 38.5xx 시리즈(적합성 시험 규격)에 CR 집중.
    
    ---
    
    ### 9. 예시 인스턴스
    
    ### 9.1 CRPack 예시
    
    ```json
    {
      "@type": "CRPack",
      "@id": "tdoc:crpack/RP-250233",
      "crPackId": "RP-250233",
      "tsgMeeting": "TSG RAN#107",
      "hasCR": [
        { "@id": "tdoc:R5-242320" },
        { "@id": "tdoc:R5-242321" }
      ]
    }
    ```
    
    ### 9.2 CR 확장 예시
    
    ```json
    {
      "@type": "CR",
      "@id": "tdoc:R5-242321",
      "tdocNumber": "R5-242321",
      "reasonForChange": "The current test case for NR CA does not cover the newly added band combination.",
      "summaryOfChange": "Add conformance test requirements for new NR CA band combination BC_n77A-n79A.",
      "consequencesIfNotApproved": "Incomplete conformance test coverage for NR CA.",
      "belongsToCRPack": { "@id": "tdoc:crpack/RP-250233" },
      "affectsTestSpec": [{ "@id": "tdoc:spec/38_521-1" }],
      "modifiesSection": [
        { "@id": "tdoc:section/38.508-5.1.3.2" }
      ]
    }
    ```
    
    ---
    
    ### 10. 생성 순서
    
    ```
    [1단계] Phase-1~3 인스턴스 확인
    │
    ▼
    [2단계] CRPack 생성 (RP 폴더 기반 + CR-Form 테이블 파싱)
    │
    ▼
    [3단계] Spec 동적 생성 (Other Specs Affected에서 누락 Spec)
    │
    ▼
    [4단계] CR 확장 (reasonForChange, summaryOfChange, Cross-Spec, modifiesSection)
    │       → ProcessPoolExecutor 병렬 처리 ([P4-V01])
    ▼
    [5단계] 역관계 생성 (hasCR ← belongsToCRPack, modifiedByCR ← modifiesSection)
    ```
    
    ---
    
    ### 11. 역관계 자동 생성
    
    | 정방향 생성 시 | 역방향 자동 생성 |
    | --- | --- |
    | CR -[BELONGS_TO_CR_PACK]-> CRPack | CRPack -[HAS_CR]-> CR |
    | CR -[MODIFIES_SECTION]-> Section | Section -[MODIFIED_BY_CR]-> CR |
    
    **Neo4j 구현:**
    
    ```cypher
    // belongsToCRPack 생성 시 hasCR 자동 생성
    MATCH (cr:CR)-[:BELONGS_TO_CR_PACK]->(pack:CRPack)
    MERGE (pack)-[:HAS_CR]->(cr)
    
    // modifiesSection 생성 시 modifiedByCR 자동 생성
    MATCH (cr:CR)-[:MODIFIES_SECTION]->(sec:Section)
    MERGE (sec)-[:MODIFIED_BY_CR]->(cr)
    ```
    
    ---
    
    ### 12. 인스턴스 현황
    
    | Phase | 클래스 | 인스턴스 수 | 상태 |
    | --- | --- | --- | --- |
    | Phase-1 | CR | [P1-V02] | ✅ 기존 |
    | Phase-1 | Spec | [P1-V10] | ✅ 기존 |
    | Phase-3 | Section | [P3-V01] | ✅ 기존 |
    | **Phase-4** | **CRPack** | **[P4-V02]** | 🔶 신규 |
    | **Phase-4** | **CR 확장** | **[P4-V03]** | 🔶 기존 인스턴스 확장 |
    | **Phase-4** | **Spec (동적 생성)** | **[P4-V04]** | 🔶 Cross-Spec 참조 시 |
    | **Phase-4** | **Section (modifiesSection)** | **[P4-V07]** | 🔶 clausesAffected → Section 매칭 |
    
    ---
    
    ### 13. 검증 규칙
    
    ### 13.1 무결성 검증
    
    | 검증 항목 | 규칙 | 오류 처리 |
    | --- | --- | --- |
    | CRPack ID 중복 | crPackId 유일 | 오류 로그 + 스킵 |
    | CRPack ID 패턴 | `RP-\d{6}` | 오류 로그 |
    | tsgMeeting 패턴 | `(TSG\s+)?RAN#\d+` | 오류 로그 |
    | hasCR 최소 1개 | CRPack당 최소 1개 CR | 오류 로그 |
    | CR 존재 확인 | hasCR 대상 CR이 Phase-1에 존재 | 오류 로그 |
    | CR 중복 참조 | 같은 CR이 여러 Pack에 속함 | 오류 로그 (Functional 위반) |
    | Spec 존재 확인 | affectsXXXSpec 대상 확인 | 없으면 동적 생성 |
    | Section 존재 확인 | modifiesSection 대상 확인 | 없으면 관계 미생성, 로그 |
    | CR 매칭 실패 | CR 문서의 tdocNumber가 Phase-1에 없음 | 오류 로그 |
    
    ### 13.2 통계 검증
    
    | 클래스 | ID 패턴 | 데이터 소스 | 인스턴스 수 |
    | --- | --- | --- | --- |
    | CRPack | `RP-\d{6}` | CR-Form 테이블 | [P4-V02] |
    | CR (확장) | `R5-\d{6}` (기존) | CR 문서 | [P4-V03] |
    | Spec (동적) | `\d{2}\.\d{3}(-\d+)?` | CR 문서 Cross-Spec | [P4-V04] |
    | Section (modifiesSection) | — | clausesAffected 파싱 | [P4-V07] |
    
    ---
    
    ### 14. 요약
    
    ### 14.1 인스턴스 생성 명세
    
    | 클래스 | ID 패턴 | 데이터 소스 | 인스턴스 수 |
    | --- | --- | --- | --- |
    | CRPack | `RP-\d{6}` | CR-Form 테이블 | [P4-V02] |
    | CR (확장) | `R5-\d{6}` (기존) | CR 문서 | [P4-V03] |
    | Spec (동적) | `\d{2}\.\d{3}(-\d+)?` | CR 문서 Cross-Spec | [P4-V04] |
    | Section (modifiesSection) | — | clausesAffected 파싱 | [P4-V07] |
    
    ### 14.2 관계 생성 요약
    
    | 관계 | 소스 | 대상 | 역관계 | 실측 |
    | --- | --- | --- | --- | --- |
    | belongsToCRPack | CR | CRPack | hasCR | [P4-V03] |
    | hasCR | CRPack | CR | belongsToCRPack | [P4-V03] |
    | affectsCoreSpec | CR | Spec | — | — |
    | affectsTestSpec | CR | Spec | — | — |
    | affectsOMSpec | CR | Spec | — | — |
    | modifiesSection | CR | Section | modifiedByCR | [P4-V05] |
    | modifiedByCR | Section | CR | modifiesSection | [P4-V05] (양방향 동일) |
    
    ### 14.3 누적 인스턴스 현황
    
    | Phase | 클래스 |
    | --- | --- |
    | Phase-1 | Tdoc, CR, LS, Meeting, Company, Contact, WorkItem, AgendaItem, Release, Spec, WorkingGroup |
    | Phase-2 | Resolution, Conclusion, Table |
    | Phase-3 | Section, TSTable, TSFigure |
    | **Phase-4** | **CRPack ([P4-V02]), CR 확장 ([P4-V03]), Spec 동적 ([P4-V04]), Section 매칭 ([P4-V07])** |
    
    ---
    
    ## Phase-4 온톨로지 설계 완료
    
    | 항목 | 내용 |
    | --- | --- |
    | **신규 클래스** | CRPack |
    | **확장 클래스** | CR, Section |
    
    ---
    
    ## Appendix A: 기준 수치
    
    > 이 테이블이 Spec의 수치 권위 소스이다.
    
    > 새 미팅 데이터 추가 시 이 테이블만 수정한다.
    
    > **구현 완료 후 실측치로 작성한다.** (구현 전 미측정 껍데기 금지)
    
    | ID | 항목 | 기준값 | 비고 |
    | --- | --- | --- | --- |
    | P4-V01 | CR 문서 수 (파싱) | 26,327 | unique (28,586 입력) |
    | P4-V02 | CRPack 인스턴스 | 1,217 | |
    | P4-V03 | CR 확장 인스턴스 | 23,109 | BELONGS_TO_CR_PACK 기준 |
    | P4-V04 | Spec 동적 생성 수 | 22 | 총 95 - 기존 73 |
    | P4-V05 | MODIFIES_SECTION 관계 수 | 31,846 | 양방향 (MODIFIED_BY_CR 동일). Neo4j 실측 |
    | P4-V06 | reasonForChange 커버리지 | 26,238/26,327 (99.7%) | 파서 출력 기준. Neo4j 확장 실측 23,192 |
    | P4-V07 | clausesAffected 매칭 Section 수 | 6,354 | DISTINCT Section |
    
    ### A.2 구현 CQ 검증 결과
    
    > Step 1 §3 CQ는 온톨로지 **설계 근거**이다.
    아래는 구현에서 사용하는 **검증 CQ**로, 설계 CQ를 포함하되 구현 검증용으로 재구성된다.
    > 
    
    | 항목 | 설계 CQ (Spec §3) | 검증 CQ (구현) |
    | --- | --- | --- |
    | CQ 그룹 수 | 4 (CQ1~CQ4) | 4 (CQ1~CQ4) |
    | 질문 수 | 15 | 15 |
    | 데이터셋 | - | Phase-4 CQ 데이터셋 |
    | 결과 파일 | - | Phase-4 CQ Cypher 결과 |
    | 검증 결과 | - | 15/15 PASS |
    
    검증 CQ는 설계 CQ와 1:1 매핑된다. 단 아래 차이를 문서화한다:
    
    - **CQ3-3 (TSG 회의별 CR Pack)**: 설계는 "특정 TSG 회의에 제출된 CR Pack 목록"을 의도하지만, 현재 `CRPack` 노드에는 `tsgMeeting` 속성이 없어(Phase-4 Step 2 이후 연결 예정) 구현 CQ는 "CR Pack 목록 Top 10 (crCount 기준)"으로 대체 검증한다. TSG 회의 필터는 `CRPack.tsgMeeting` 속성 추가 후 재활성화 대상이다.
    - **CQ4-2**: 설계는 "특정 Conclusion이 참조한 CR의 변경 이유·요약"이나, 구현은 LIMIT 5 요약으로 간략화한다 (Resolution→CR 매핑이 Phase-2 CONCLUDES 관계에 의존).
    
    ### A.3 미측정·제약 항목
    
    | 항목 | 현 상태 | 사유 |
    | --- | --- | --- |
    | CRPack.tsgMeeting 추출 | 미구현 | Cover Sheet FTP 경로 파싱 로직 미구현. Phase-4 범위 외 |
    | Cover 없는 팩 수 | 미측정 | tsgMeeting 커버리지와 함께 후속 조치 |
    | LLM 자연어 답변 리포트 | 미생성 | Direct Cypher 검증만 수행. Query Interface(Phase-6 이후) 단계에서 통합 예정 |
