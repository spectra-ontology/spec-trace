- **phase-2: Ontology 101 기반 전략/기획, IP/특허 담당 타겟으로 확장 (Tdoc)**
    
    ## Step 1: Domain과 Scope 정의
    
    > Ontology 101 원칙
    > 
    > 
    > *"We suggest starting the development of an ontology by defining its domain and scope. That is, answer several basic questions: What is the domain that the ontology will cover? For what we are going to use the ontology? For what types of questions the information in the ontology should provide answers? Who will use and maintain the ontology?"*
    > 
    > — Noy & McGuinness, Ontology Development 101
    > 
    
    ---
    
    ## 1. 기본 질문에 대한 답변
    
    ### 1.1 What is the domain?
    
    **3GPP RAN1 Final Report 본문에 기록된 Resolution(결의)과 Role(역할) 정보**
    
    ### 1.2 For what are we going to use the ontology?
    
    **Phase-1 Tdoc 중심 온톨로지를 확장**하여 다음을 지원:
    
    - 회의 결과 분석 — 무엇이 합의되었는가
    - 기술 채택 현황 추적 — 어떤 기술이 표준에 반영되었는가
    - 회사별 기여도 파악 — 누가 표준화에 기여했는가
    - 논의 진행 역할 분석 — 누가 논의를 이끌었는가
    
    ### 1.3 Who will use and maintain the ontology?
    
    | 사용자 | 핵심 니즈 |
    | --- | --- |
    | **전략/기획** | 회의 결과 파악, 기술 트렌드 분석, 경쟁사 동향 |
    | **IP/특허** | 기고의 표준 반영 여부, 기여 증거 확보 |
    
    ### 1.4 데이터 소스
    
    | Phase | 데이터 소스 | 비고 |
    | --- | --- | --- |
    | Phase-1 | Tdoc_list (Excel) | 구축 완료 |
    | **Phase-2** | **Final Report 본문 (Word)** | Annex 제외 |
    
    ### 1.5 전제 조건
    
    > 본 온톨로지는 Phase-1 Tdoc 온톨로지의 확장이다.
    > 
    > 
    > Phase-1에서 정의된 클래스 및 관계를 재사용하며, 구체적인 재사용 범위는 Step 2에서 검토한다.
    > 
    
    ---
    
    ## 2. Competency Questions
    
    > Ontology 101 원칙
    > 
    > 
    > *"One of the ways to determine the scope of the ontology is to sketch a list of questions that a knowledge base based on the ontology should be able to answer. These questions will serve as the litmus test later: Does the ontology contain enough information to answer these types of questions?"*
    > 
    
    ---
    
    ### CQ1. Resolution 조회
    
    | # | Competency Question |
    | --- | --- |
    | 1-1 | 특정 회의에서 합의된 Agreement 목록은? |
    | 1-2 | 특정 회의에서 도출된 Conclusion 목록은? |
    | 1-3 | 특정 회의의 Working Assumption 목록은? |
    | 1-4 | 특정 Agenda Item에서의 Resolution 목록은? |
    | 1-5 | 특정 Release 관련 Resolution 목록은? |
    | 1-6 | 특정 Spec을 변경하는 Resolution 목록은? |
    | 1-7 | 특정 Work Item의 Resolution 목록은? |
    | 1-8 | Resolution이 가장 많은 Agenda Item Top N은? |
    
    ---
    
    ### CQ2. Tdoc ↔ Resolution 추적
    
    | # | Competency Question |
    | --- | --- |
    | 2-1 | 특정 Tdoc이 어떤 Resolution으로 이어졌나? |
    | 2-2 | 특정 Resolution이 참조한 Tdoc 목록은? |
    | 2-3 | Comeback 결정된 Tdoc 목록은? |
    | 2-4 | 특정 Tdoc이 어떤 Spec에 반영됐나? |
    
    ---
    
    ### CQ3. 회사별 기여도
    
    | # | Competency Question |
    | --- | --- |
    | 3-1 | 특정 회사 Tdoc이 Resolution으로 이어진 비율은? |
    | 3-2 | 특정 기술(Work Item)에서 회사별 Resolution 기여도는? |
    | 3-3 | 특정 Spec의 주요 contributor 순위는? |
    | 3-4 | 두 회사 간 기여도 비교는? |
    
    ---
    
    ### CQ4. 역할 (Moderator/Chair)
    
    | # | Competency Question |
    | --- | --- |
    | 4-1 | 특정 Agenda Item의 Moderator는 누구(어떤 회사)인가? |
    | 4-2 | 특정 회사가 Moderator를 맡은 Agenda Item 목록은? |
    | 4-3 | 특정 회사의 Moderator 담당 비율은? |
    | 4-4 | 특정 Agenda Item의 Ad-hoc Chair는 누구(어떤 회사)인가? |
    | 4-5 | 특정 회사가 Ad-hoc Chair를 맡은 Agenda Item 목록은? |
    
    ---
    
    ### CQ5. 후속 조치 — 제외
    
    | # | Competency Question | 제외 이유 |
    | --- | --- | --- |
    | 5-1 | 특정 회의의 Action Item 목록은? | Annex 필요 |
    | 5-2 | 특정 회의에서 승인된 CR 목록은? | Annex 필요 |
    | 5-3 | 특정 회의에서 처리된 LS 목록은? | Annex 필요 |
    
    ---
    
    ### CQ6. 트렌드/비교
    
    | # | Competency Question |
    | --- | --- |
    | 6-1 | 특정 기술(Work Item)의 Resolution 수 추이는? |
    | 6-2 | 특정 회사의 기여율 변화는? |
    | 6-3 | 특정 회사의 Moderator 담당 추이는? |
    
    ---
    
    ### CQ 결과 규칙
    
    ### 정렬 기준 (Default Sort Order)
    
    | CQ 그룹 | Primary Sort | Secondary Sort | 구현 속성 |
    | --- | --- | --- | --- |
    | CQ1. Resolution 조회 | Meeting 번호 DESC (최신 먼저) | Agenda 번호 ASC, Sequence ASC | `meetingNumberInt DESC` |
    | CQ2. Tdoc ↔ Resolution | Meeting 번호 DESC | Sequence ASC | `meetingNumberInt DESC` |
    | CQ3. 회사별 기여도 | Count DESC (많은 순) | Company 이름 ASC | `count DESC` |
    | CQ4. 역할 조회 | Meeting 번호 DESC | Agenda 번호 ASC | `meetingNumberInt DESC` |
    | CQ6. 트렌드/비교 | Meeting 번호 ASC (시계열) | - | `meetingNumberInt ASC` |
    
    *참고: "Meeting 번호" 정렬은 Phase-1 Meeting 클래스의 `meetingNumberInt` 속성 사용 (숫자 기반 정렬 보장)*
    
    ### 결과 개수 (Default Limit)
    
    | CQ 유형 | 기본값 | 적용 CQ |
    | --- | --- | --- |
    | 목록 조회 | 10 | CQ1-1~1-7, CQ2, CQ4 |
    | Top N 조회 | 10 | CQ1-8, CQ3 |
    | 트렌드 조회 | 전체 | CQ6 |
    
    *참고: Limit은 쿼리 시 파라미터로 조정 가능*
    
    ---
    
    ## 3. Scope 정의
    
    ### 3.1 포함 (In Scope)
    
    | 구분 | 포함 대상 | 비고 |
    | --- | --- | --- |
    | **Resolution** | Agreement, Conclusion, Working Assumption | CQ1~3, CQ6 |
    | **Role** | Moderator, Ad-hoc Chair | CQ4 |
    | **Embedded Content** | Figure, Table, Chart, Equation | CQ 대상 아님, Resolution 완결성 위해 포함 |
    | **데이터 소스** | Final Report 본문 | Annex 제외 |
    
    ### 3.2 제외 (Out of Scope)
    
    | 제외 대상 | 이유 |
    | --- | --- |
    | 본문의 `**Decision:**` 패턴 | Resolution과 용어 혼동 방지 |
    | Annex (B, C, D, E, F) | 본문만 파싱 원칙 |
    | Resolution 의미/내용 검색 | Vector DB 영역 (향후 확장) |
    | CQ5 (후속 조치) | Annex 의존 |
    | RAN1 Chair | 고정 역할 |
    | Figure 이미지 콘텐츠 | 별도 저장소에서 관리, Graph DB는 메타데이터만 |
    | Table 셀 데이터 | 별도 저장소에서 관리, Graph DB는 메타데이터와 수식만 |
    
    ### 3.3 용어 구분
    
    | 용어 | 정의 | 비고 |
    | --- | --- | --- |
    | **Resolution** | 회의에서 도출된 기술적 결의 | 온톨로지 용어 |
    | **Decision** | Final Report의 `**Decision:**` 패턴 | 추출 대상 아님 |
    
    ---
    
    ## 4. CQ 요약
    
    | CQ 그룹 | 상태 |
    | --- | --- |
    | CQ1. Resolution 조회 | ✅ 포함 |
    | CQ2. Tdoc ↔ Resolution 추적 | ✅ 포함 |
    | CQ3. 회사별 기여도 | ✅ 포함 |
    | CQ4. 역할 (Moderator/Chair) | ✅ 포함 |
    | CQ5. 후속 조치 | ❌ 제외 |
    | CQ6. 트렌드/비교 | ✅ 포함 |
    
    ---
    
    ## Step 2: 기존 온톨로지 재사용 검토
    
    > Ontology 101 원칙
    > 
    > 
    > *"It is almost always worth considering what someone else has done and checking if we can refine and extend existing sources for our particular domain and task. Reusing existing ontologies may be a requirement if our system needs to interact with other applications that have already committed to particular ontologies or controlled vocabularies."*
    > 
    > — Noy & McGuinness, Ontology Development 101
    > 
    
    ---
    
    ## 1. 재사용 검토 대상
    
    ### 1.1 Phase-1 온톨로지
    
    | 항목 | 내용 |
    | --- | --- |
    | 도메인 | 3GPP RAN1 Tdoc 메타데이터 |
    | 데이터 소스 | Tdoc_list (Excel) |
    
    ### 1.2 외부 표준 온톨로지
    
    Phase-1에서 참조한 외부 온톨로지:
    
    | 온톨로지 | 용도 |
    | --- | --- |
    | Dublin Core | 문서 메타데이터 (title, identifier, date) |
    | FOAF | 조직/사람 (Organization, Person) |
    
    ---
    
    ## 2. Phase-1 클래스 재사용 검토
    
    ### 2.1 CQ 기반 필요성 분석
    
    | Phase-1 클래스 | 관련 CQ | 필요성 |
    | --- | --- | --- |
    | **Tdoc** | CQ2 (Tdoc ↔ Resolution 추적) | ✅ 필수 |
    | **Meeting** | CQ1 (특정 회의의 Resolution) | ✅ 필수 |
    | **AgendaItem** | CQ1-4, CQ4 (Agenda별 Resolution, Moderator) | ✅ 필수 |
    | **Company** | CQ3, CQ4 (회사별 기여도, Moderator 회사) | ✅ 필수 |
    | **Release** | CQ1-5 (특정 Release 관련 Resolution) | ✅ 필수 |
    | **Spec** | CQ1-6, CQ3-3 (Spec별 Resolution) | ✅ 필수 |
    | **WorkItem** | CQ1-7, CQ3-2 (WorkItem별 Resolution) | ✅ 필수 |
    | CR | (Spec 연결 시 간접 사용) | ⚠️ 간접 |
    | LS | - | ❌ 불필요 |
    | Contact | - | ❌ 불필요 |
    | WorkingGroup | - | ❌ 불필요 |
    
    ### 2.2 재사용 클래스 결정
    
    | 구분 | 클래스 | 재사용 방식 |
    | --- | --- | --- |
    | **필수** | Tdoc, Meeting, AgendaItem, Company, Release, Spec, WorkItem | 그대로 사용 |
    | **간접** | CR | Tdoc 하위 클래스로 유지 |
    | **불필요** | LS, Contact, WorkingGroup | Phase-2에서 직접 사용 안 함 |
    
    *참고: "불필요"는 삭제가 아니라 Phase-2 CQ 답변에 직접 사용되지 않음을 의미*
    
    ### 2.3 Phase-1 클래스 연결 시 주의사항
    
    | 클래스 | 연결 속성 | 설명 |
    | --- | --- | --- |
    | **Meeting** | canonicalMeetingNumber | Phase-2 Resolution의 `madeAt` 관계는 Phase-1 Meeting의 `canonicalMeetingNumber`와 매칭 |
    
    *참고: Phase-1 Meeting은 `-e` suffix가 포함된 원본(`meetingNumber`)과 정규화된 값(`canonicalMeetingNumber`)을 모두 가짐*

    **🔴 RAN1 Phase-2 매칭 정책 (RAN2~5와 의도적으로 다름)**:
    - **현재 정책**: RAN1 phase-2 loader는 `MATCH (m:Meeting {canonicalMeetingNumber: ...})` 사용. **`MERGE` 아님**.
    - **사유 1: COVID-19 특수 케이스 보존**: RAN1#100과 RAN1#100-e 두 미팅이 동일 `canonicalMeetingNumber=RAN1#100`을 갖는다 (§Step 5 / 본 spec L1325 참조). 현재 `MATCH` 패턴은 두 노드 모두 매칭하여 Resolution이 양쪽에 연결됨. `MERGE`로 변경 시 첫 매칭 노드만 처리되어 두 번째 노드 silent skip → COVID 의도 동작 깨짐.
    - **사유 2: Phase-1 권위 우선**: Phase-1에 없는 미팅을 Phase-2가 신규 생성하지 않는 정책. 현재 RAN1 데이터에서는 silent skip 발생 케이스 없음 (정상).
    - **현황**: RAN1 NULL id Meeting 0건, orphan Resolution 0건, orphan Table 0건 → MATCH 정책 정상 작동.
    - **RAN2~5 차이 (의도적)**: RAN2~5 phase-2는 `MERGE + _normalize_canonical_meeting + ON CREATE SET m.id` 패턴 사용. 사유: RAN2~5는 Phase-1에 없는 미팅이 Phase-2 입력에 등장하는 케이스 다수 (예: RAN3#103/103bis/97, RAN2#101bis) → 신규 노드 생성 필요. RAN1과 데이터 특성 차이로 정책 분리.
    - **회귀 감지 보강**: Phase-1 DQ Tier4 dataset에 `CQ-RAN1-P1-DQ-T4-05` (NULL id Meeting 0건 검증) 추가됨. 미래 코드 변경/incremental update에서 회귀 발생 즉시 감지.
    - **변경 결정 시 영향**: RAN1 phase-2 패턴 변경 (MATCH → MERGE 등)은 COVID 케이스 동작 + RAN1 production 데이터 영향. 변경 전 사용자 결정 필수.
    
    ---
    
    ## 3. Phase-1 관계 재사용 검토
    
    ### 3.1 CQ 기반 필요성 분석
    
    | Phase-1 관계 | 관련 CQ | 필요성 |
    | --- | --- | --- |
    | **submittedBy** (Tdoc → Company) | CQ3 (회사별 기여도) | ✅ 필수 |
    | **belongsTo** (Tdoc → AgendaItem) | CQ1-4 (Agenda별 조회) | ✅ 필수 |
    | **presentedAt** (Tdoc → Meeting) | CQ1 (회의별 조회) | ✅ 필수 |
    | **targetRelease** (Tdoc → Release) | CQ1-5 (Release별 조회) | ✅ 필수 |
    | **relatedTo** (Tdoc → WorkItem) | CQ1-7, CQ3-2 (WI별 조회) | ✅ 필수 |
    | **modifies** (CR → Spec) | CQ1-6, CQ3-3 (Spec별 조회) | ✅ 필수 |
    | isRevisionOf (Tdoc → Tdoc) | - | ⚠️ 간접 |
    | revisedTo (Tdoc → Tdoc) | - | ⚠️ 간접 |
    | hasContact (Tdoc → Contact) | - | ❌ 불필요 |
    | sentTo (LS → WorkingGroup) | - | ❌ 불필요 |
    | ccTo (LS → WorkingGroup) | - | ❌ 불필요 |
    | originalLS (LS → Tdoc) | - | ❌ 불필요 |
    | originatedFrom (LS → WorkingGroup) | - | ❌ 불필요 |
    | replyTo (LS → Tdoc) | - | ❌ 불필요 |
    | replyIn (LS → Tdoc) | - | ❌ 불필요 |
    
    ### 3.2 재사용 관계 결정
    
    | 구분 | 관계 | 재사용 방식 |
    | --- | --- | --- |
    | **필수** | submittedBy, belongsTo, presentedAt, targetRelease, relatedTo, modifies | 그대로 사용 |
    | **간접** | isRevisionOf, revisedTo | 유지 |
    | **불필요** | hasContact, sentTo, ccTo, originalLS, originatedFrom, replyTo, replyIn | Phase-2에서 직접 사용 안 함 |
    
    ---
    
    ## 4. 외부 온톨로지 재사용 검토
    
    ### 4.1 기존 참조 온톨로지
    
    | 온톨로지 | Phase-1 용도 | Phase-2 필요성 | 결정 |
    | --- | --- | --- | --- |
    | Dublin Core | Tdoc의 title, identifier | Phase-2 개념에도 적용 가능 | ✅ 유지 |
    | FOAF | Company, Contact | Company 재사용 | ✅ 유지 |
    
    ### 4.2 추가 온톨로지 검토
    
    | 온톨로지 | 검토 내용 | 결정 |
    | --- | --- | --- |
    | PROV-O | 출처/유래 표현 | ❌ 불필요 |
    | SKOS | 계층적 분류 | ❌ 불필요 |
    | ORG | 조직 구조 | ❌ 불필요 |
    
    ### 4.3 결론
    
    - 기존 참조 온톨로지 (Dublin Core, FOAF) 유지
    - 추가 외부 온톨로지 불필요
    
    ---
    
    ## 5. 요약
    
    ### 5.1 재사용 결정
    
    | 구분 | 대상 |
    | --- | --- |
    | **Phase-1 클래스** | Tdoc, Meeting, AgendaItem, Company, Release, Spec, WorkItem |
    | **Phase-1 관계** | submittedBy, belongsTo, presentedAt, targetRelease, relatedTo, modifies |
    | **외부 온톨로지** | Dublin Core, FOAF |
    
    ### 5.2 비고
    
    - 신규 클래스 및 관계는 Step 3~5에서 정의
    - 재사용 클래스/관계와 신규 개념의 연결 방식은 Step 5에서 정의
    
    ---
    
    ## Step 3: 중요 용어 나열
    
    > Ontology 101 원칙
    > 
    > 
    > *"It is useful to write down a list of all terms we would like either to make statements about or to explain to a user. What are the terms we would like to talk about? What properties do those terms have? What would we like to say about those terms?"*
    > 
    > — Noy & McGuinness, Ontology Development 101
    > 
    
    ---
    
    ## 1. Step 3 목적
    
    - 도메인에서 나오는 **명사, 동사를 나열**
    - 아직 **클래스/속성 구분 없이** 후보 용어로 정리
    - Final Report 본문에서 **실제로 추출 가능한지** 확인
    
    ---
    
    ## 2. 데이터 소스
    
    | 항목 | 내용 |
    | --- | --- |
    | 샘플 | RAN1#112, #120, #122 |
    | 형식 | Word 문서 (영어) |
    | 범위 | 본문만 (Annex 제외) |
    
    ---
    
    ## 3. 용어 나열
    
    ### 3.1 Resolution 관련
    
    | 용어 | 여러 인스턴스? | 독립 객체? | 클래스 여부 |
    | --- | --- | --- | --- |
    | **Agreement** | ✅ (Step 3 §2 샘플 참조) | ✅ | ✅ 클래스 |
    | **Conclusion** | ✅ (Step 3 §2 샘플 참조) | ✅ | ✅ 클래스 |
    | **Working Assumption** | ✅ (Step 3 §2 샘플 참조) | ✅ | ✅ 클래스 |
    
    ### 3.2 Role 정보 출처
    
    | Term | Final Report Pattern | Related CQ |
    | --- | --- | --- |
    | **Summary** | `[R1-XXX] Moderator Summary ... Moderator (Company)` | CQ4-1, CQ4-2, CQ4-3 |
    |  | `[R1-XXX] FL summary ... Moderator (Company)` |  |
    |  | `[R1-XXX] FL Summary #N ... Feature Lead (Company)` |  |
    | **Session Notes** | `[R1-XXX] Session notes for X.X Ad-hoc Chair (Company)` | CQ4-4, CQ4-5 |
    
    ### 3.3 Role 관련
    
    | Term | Description | Source | Related CQ |
    | --- | --- | --- | --- |
    | **Moderator** | Discussion facilitator | Summary | CQ4-1, CQ4-2, CQ4-3 |
    | **Ad-hoc Chair** | Session manager | Session Notes | CQ4-4, CQ4-5 |
    
    **Moderator 표현 통합**
    
    Final Report에서 동일한 역할을 두 가지 표현으로 사용:
    
    | Final Report 표현 | 패턴 예시 |
    | --- | --- |
    | **Moderator** | `Moderator (Ericsson)`, `Moderator Summary` |
    | **Feature Lead (FL)** | `FL summary`, `FL Summary #1`, `Feature Lead (ZTE)` |
    
    → 두 표현은 **동일한 역할**을 의미하며, 온톨로지에서는 **Moderator**로 통합
    
    ### 3.4 Relationship 관련
    
    | Term | Meaning | Related CQ |
    | --- | --- | --- |
    | **references** | Resolution이 Tdoc을 참조 | CQ2-1, CQ2-2 |
    | **madeAt** | Resolution이 Meeting에서 도출 | CQ1-1, CQ1-2, CQ1-3 |
    | **resolutionBelongsTo** | Resolution이 AgendaItem에 속함 | CQ1-4 |
    | **promotedTo** | WorkingAssumption이 Agreement로 전환 | - |
    | **moderatedBy** | Summary의 Moderator 회사 | CQ4-1, CQ4-2 |
    | **chairedBy** | Session Notes의 Chair 회사 | CQ4-4, CQ4-5 |
    | **hasFigure** | Resolution이 Figure를 참조 | - |
    | **hasTable** | Resolution이 Table을 참조 | - |
    | **hasChart** | Resolution이 Chart를 참조 | - |
    | **containedIn** | Figure/Table이 Meeting에 포함 | - |
    
    *참고: Phase-1 `belongsTo`(Tdoc → AgendaItem)와 구분하기 위해 `resolutionBelongsTo` 사용*
    
    ### 3.5 Property 관련
    
    | Term | Meaning | Related CQ |
    | --- | --- | --- |
    | **content** | Resolution 본문 텍스트 | CQ2-3 (comeback 패턴) |
    | **contentWithEquations** | Resolution 본문 (수식 LaTeX 포함) | - |
    | **resolutionId** | Resolution 고유 식별자 | 전체 |
    | **sequence** | 같은 Agenda 내 순서 | CQ1 |
    | **sessionContext** | 세션 정보 | - |
    | **note** | Resolution 부가 설명 | - |
    | **hasFFS** | "For Further Study" 포함 여부 | - |
    | **hasTBD** | "To Be Determined" 포함 여부 | - |
    | **roundNumber** | Summary 라운드 번호 (#1, #2) | - |
    
    ### 3.6 Embedded Content 관련
    
    | Term | Final Report Pattern | Related CQ |
    | --- | --- | --- |
    | **Figure** | `Figure X:` 캡션 패턴 | - |
    | **Table** | `Table X.X.X-X:` 캡션 패턴 | - |
    | **Chart** | `<c:chart>` XML 객체 | - |
    | **Equation** | OMML (`<m:oMath>`) 수식 객체 | - |
    
    **처리 방향**:
    
    | 대상 | Graph DB 저장 | 별도 저장소 |
    | --- | --- | --- |
    | Figure | ID, caption, filePath | 원본 이미지 파일 |
    | Table | ID, caption, filePath, 내부 수식(LaTeX) | 원본 구조 (HTML) |
    | Chart | ID, caption, chartPath, chartType | 원본 XML 파일 |
    | Equation | LaTeX 텍스트 (Resolution content에 인라인) | 없음 |
    
    ---
    
    ## 4. CQ별 필요 용어 매핑
    
    ### CQ1: Resolution 조회
    
    | CQ | Required Terms |
    | --- | --- |
    | 1-1 ~ 1-3 | Agreement, Conclusion, Working Assumption, madeAt |
    | 1-4 | Resolution, resolutionBelongsTo |
    | 1-5 ~ 1-7 | Resolution, references (→ Phase-1 Tdoc, Release, Spec, WorkItem) |
    | 1-8 | Resolution, resolutionBelongsTo |
    
    ### CQ2: Tdoc ↔ Resolution 추적
    
    | CQ | Required Terms |
    | --- | --- |
    | 2-1, 2-2 | Resolution, references |
    | 2-3 | Resolution, content |
    | 2-4 | Resolution, references (→ Phase-1 Tdoc, Spec) |
    
    ### CQ3: 회사별 기여도
    
    | CQ | Required Terms |
    | --- | --- |
    | 3-1 ~ 3-4 | Resolution, references (→ Phase-1 Tdoc, Company, WorkItem, Spec) |
    
    ### CQ4: 역할
    
    | CQ | Required Terms |
    | --- | --- |
    | 4-1 ~ 4-3 | Summary, Moderator, moderatedBy |
    | 4-4 ~ 4-5 | Session Notes, Ad-hoc Chair, chairedBy |
    
    ### CQ6: 트렌드/비교
    
    | CQ | Required Terms |
    | --- | --- |
    | 6-1 ~ 6-3 | CQ1, CQ3, CQ4 용어 + madeAt (시계열) |
    
    ---
    
    ## 5. 요약
    
    ### 5.1 용어 목록
    
    | Category | Terms |
    | --- | --- |
    | **Resolution** | Agreement, Conclusion, Working Assumption |
    | **Role Source** | Summary, Session Notes |
    | **Role** | Moderator, Ad-hoc Chair |
    | **Relationship** | references, madeAt, resolutionBelongsTo, promotedTo, moderatedBy, chairedBy, hasFigure, hasTable, hasChart, containedIn |
    | **Property** | content, contentWithEquations, resolutionId, sequence, sessionContext, note, hasFFS, hasTBD, roundNumber  |
    | **Embedded Content** | Figure, Table, Chart, Equation |
    
    ### 5.2 검증
    
    | 검증 항목 | 결과 |
    | --- | --- |
    | 모든 용어가 Step 1 Scope 내? | ✅ |
    | 모든 용어가 CQ 답변에 필요? | ✅ |
    | Final Report에서 추출 가능? | ✅ |
    
    ---
    
    ## Step 4: 클래스와 계층 구조 정의
    
    > Ontology 101 원칙
    > 
    > 
    > *"Define the classes and the class hierarchy... A class can have subclasses that represent concepts that are more specific than the superclass."*
    > 
    > — Noy & McGuinness, Ontology Development 101
    > 
    
    ---
    
    ## 1. Step 4 목적
    
    - Step 3에서 나열한 용어 중 **클래스를 확정**
    - **is-a (상속) 관계**로 계층 구조 정의
    - 속성(Property) 정의는 Step 5에서 진행
    
    ---
    
    ## 2. 클래스 판단 기준
    
    > Ontology 101 판단 기준
    > 
    > 
    > *"A class is a concept in the domain. If a concept has individual instances, it should be a class."*
    > 
    
    | 질문 | 클래스 여부 |
    | --- | --- |
    | 여러 개의 인스턴스를 가질 수 있는가? | ✅ 클래스 |
    | 독립적으로 존재하는 객체인가? | ✅ 클래스 |
    | 다른 객체의 속성/값인가? | ❌ Property |
    
    ### 하위 클래스 조건
    
    | 조건 | 설명 |
    | --- | --- |
    | 추가 속성 | 상위 클래스에 없는 속성이 있음 |
    | 다른 관계 | 다른 관계에 참여함 |
    | 다른 제약조건 | 속성의 제약이 다름 |
    
    ---
    
    ## 3. Step 3 용어 → 클래스 판단
    
    ### 3.1 Resolution 관련 용어
    
    | 용어 | 여러 인스턴스? | 독립 객체? | 클래스 여부 |
    | --- | --- | --- | --- |
    | **Agreement** | ✅  | ✅ | ✅ 클래스 |
    | **Conclusion** | ✅ | ✅ | ✅ 클래스 |
    | **Working Assumption** | ✅  | ✅ | ✅ 클래스 |
    
    → 세 유형 모두 "회의에서 도출된 결의"라는 공통 개념 → **상위 클래스 Resolution** 필요
    
    ### 3.2 Role 정보 출처 용어
    
    | 용어 | 여러 인스턴스? | 독립 객체? | 클래스 여부 |
    | --- | --- | --- | --- |
    | **Summary** | ✅  | ✅ (Tdoc) | ✅ 클래스 (Tdoc 하위) |
    | **Session Notes** | ✅  | ✅ (Tdoc) | ✅ 클래스 (Tdoc 하위) |
    
    → 둘 다 Tdoc이지만 **추가 관계**(moderatedBy, chairedBy)가 있음 → **Tdoc 하위 클래스**
    
    ### 3.3 Role 관련 용어
    
    | 용어 | 여러 인스턴스? | 독립 객체? | 클래스 여부 |
    | --- | --- | --- | --- |
    | Moderator | ? | ? | ❌ 클래스 아님 |
    | Ad-hoc Chair | ? | ? | ❌ 클래스 아님 |
    
    **판단 근거**:
    
    - Moderator, Ad-hoc Chair는 독립 객체가 아님
    - "Summary가 특정 Company에 의해 moderate됨" → **관계(moderatedBy)**로 표현
    - "Session Notes가 특정 Company에 의해 chair됨" → **관계(chairedBy)**로 표현
    
    → Role은 클래스가 아니라 **Step 5에서 관계로 정의**
    
    ### 3.4 기타 용어
    
    | 용어 | 판단 |
    | --- | --- |
    | references, madeAt, resolutionBelongsTo, moderatedBy, chairedBy | ❌ 관계 (Step 5) |
    | content, resolutionId, sequence, note, hasFFS, hasTBD, roundNumber | ❌ 속성 (Step 5) |
    
    ---
    
    ## 4. Phase-2 신규 클래스
    
    ### 4.1 Resolution 계층
    
    | 클래스 | 정의 | 인스턴스 수 (샘플) |
    | --- | --- | --- |
    | **Resolution** (abstract) | 회의에서 도출된 기술적 결의 | - |
    | **├─ Agreement** | 기술적 합의 사항 | Appendix A [P2-V01] 참조 |
    | **├─ Conclusion** | 논의 결론 | Appendix A [P2-V02] 참조 |
    | **└─ WorkingAssumption** | 잠정 가정 (추후 Agreement로 확정 가능) | Appendix A [P2-V03] 참조 |
    
    **Resolution을 상위 클래스로 만드는 이유**:
    
    - 세 하위 클래스가 공통 속성(content, note 등)과 공통 관계(references, madeAt, resolutionBelongsTo)를 가짐
    - CQ에서 "특정 조건의 Resolution"을 조회할 때 세 유형을 통합 조회 가능
    
    ### 4.2 Tdoc 확장
    
    | 클래스 | 정의 | 상위 클래스 | 인스턴스 수 (샘플) |
    | --- | --- | --- | --- |
    | **Summary** | 논의 요약 문서 (Moderator/FL Summary) | Tdoc | Appendix A [P2-V04] 참조 |
    | **SessionNotes** | 세션별 논의 기록 | Tdoc | Appendix A [P2-V05] 참조 |
    
    **Tdoc 하위 클래스로 만드는 이유**:
    
    - 이미 Phase-1에서 CR, LS가 Tdoc의 하위 클래스로 정의됨
    - Summary, SessionNotes도 Tdoc의 공통 속성(tdocNumber, title 등)을 상속
    - 추가 관계(moderatedBy, chairedBy)로 하위 클래스 조건 충족
    
    ### 4.3 Embedded Content 클래스
    
    | 클래스 | 정의 | Graph DB 저장 | 별도 저장소 |
    | --- | --- | --- | --- |
    | **Figure** | 문서 내 삽입된 이미지 | ID, caption, filePath | 원본 이미지 파일 |
    | **Table** | 문서 내 삽입된 테이블 | ID, caption, filePath, equations | 원본 HTML |
    | **Chart** | 문서 내 삽입된 차트 | ID, caption, chartPath, chartType | 원본 XML 파일 |
    
    **클래스 정의 이유**:
    
    - Figure, Table, Chart 모두 여러 인스턴스를 가지며 Resolution과 참조 관계를 가짐
    - 기술적 Figure/Table/Chart 대상 (포맷팅용 제외). 캡션 유무와 무관하게 Resolution 본문에 포함된 실질적 콘텐츠를 추출하며, 식별 기준은 Step 7에서 정의.
    - Chart는 Figure와 달리 이미지가 아닌 데이터 XML로 저장되므로 별도 클래스로 정의
    
    **Equation은 클래스가 아닌 이유**:
    
    - 독립 객체가 아님, Resolution content의 일부
    - LaTeX 텍스트로 content 속성에 인라인 포함 (`$...$` 형식)
    
    ---
    
    ## 5. 전체 클래스 계층 다이어그램
    
    ```
    ┌─────────────────────────────────────────────────────────────────┐
    │                    RAN1 Meeting Ontology                        │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                 │
    │  Tdoc (Phase-1)                   Resolution (Phase-2 신규)     │
    │  ├── CR (Phase-1)                 ├── Agreement ⭐              │
    │  ├── LS (Phase-1)                 ├── Conclusion ⭐             │
    │  ├── Summary ⭐                 └── WorkingAssumption ⭐       │
    │  └── SessionNotes ⭐                                            │
    │                                                                 │
    ├─────────────────────────────────────────────────────────────────┤
    │  독립 클래스 (Phase-1 재사용)                                    │
    │                                                                 │
    │  Meeting    Company    WorkItem    AgendaItem                   │
    │  Release    Spec       Contact     WorkingGroup                 │
    │                                                                 │
    ├─────────────────────────────────────────────────────────────────┤
    │  독립 클래스 (Phase-2 신규)                                      │
    │                                                                 │
    │  Figure ⭐    Table ⭐    Chart ⭐                             │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘
    ```
    
    ⭐ = Phase-2 신규 클래스
    
    *참고: Figure, Table, Chart는 공통 상위 클래스 없이 독립 클래스로 정의. 공통 속성(caption, containedIn)은 각 클래스에서 개별 정의.*
    
    ---
    
    ## 6. 요약
    
    ### 6.1 Phase-2 신규 클래스
    
    | 계층 | 클래스 |
    | --- | --- |
    | **Resolution 계층** | Resolution (abstract), Agreement, Conclusion, WorkingAssumption |
    | **Tdoc 확장** | Summary, SessionNotes |
    | **Embedded Content** | Figure, Table, Chart |
    
    ### 6.2 클래스로 정의하지 않은 용어
    
    | 용어 | 이유 | 처리 |
    | --- | --- | --- |
    | Moderator, Ad-hoc Chair | 독립 객체 아님 | Step 5에서 관계로 정의 |
    | references, madeAt 등 | 관계 | Step 5 |
    | content, note 등 | 속성 | Step 5 |
    
    ---
    
    ## Step 5: 속성(Slot) 정의
    
    > Ontology 101 원칙
    > 
    > 
    > *"Define the properties of classes—slots... Properties describe attributes of instances of a class and relations to other instances."*
    > 
    > — Noy & McGuinness, Ontology Development 101
    > 
    
    ---
    
    ## 1. Step 5 목적
    
    - Step 4에서 정의한 클래스의 **속성(Slot)** 정의
    - **Data Property**: 클래스 인스턴스의 값 (String, Integer, Boolean 등)
    - **Object Property**: 클래스 인스턴스 간의 관계
    - 제약조건(Cardinality 등)은 Step 6에서 정의
    
    ---
    
    ## 2. 속성의 종류
    
    | 종류 | 설명 | 예시 |
    | --- | --- | --- |
    | **Data Property** | 객체의 속성값 | content, hasFFS |
    | **Object Property** | 다른 객체와의 관계 | references, madeAt |
    
    ---
    
    ## 3. Resolution 계층 속성
    
    ### 3.1 Resolution (추상 클래스)
    
    하위 클래스(Agreement, Conclusion, WorkingAssumption)가 **공통으로 상속**하는 속성
    
    **Data Property**
    
    | Property | Type | Description |
    | --- | --- | --- |
    | resolutionId | String | Resolution 고유 식별자 (예: AGR-112-8.1-001) |
    | content | String | Resolution 본문 텍스트 (수식을 `[EQUATION]` 마커로 대체). **Text-to-Cypher 검색용**. |
    | contentWithEquations | String | Resolution 본문 텍스트 (수식 LaTeX 인라인 포함). **LLM 답변 생성 및 UI 렌더링용**. |
    | sequence | Integer | 같은 Agenda 내 순서 |
    | sessionContext | String | 세션 정보 (예: "Thursday session", "Online") |
    | note | String | 부가 설명 (Note: ...) |
    
    **Object Property**
    
    | Property | Range | Description |
    | --- | --- | --- |
    | references | Tdoc | Resolution이 참조하는 Tdoc |
    | madeAt | Meeting | Resolution이 도출된 회의. Phase-1 Meeting의 `canonicalMeetingNumber`와 매칭 |
    | resolutionBelongsTo | AgendaItem | Resolution이 속한 Agenda |
    | hasFigure | Figure | Resolution이 참조하는 Figure |
    | hasTable | Table | Resolution이 참조하는 Table |
    | hasChart | Chart | Resolution이 참조하는 Chart |
    
    ### 3.2 Agreement
    
    Resolution 속성 상속 + 추가 속성
    
    **추가 Data Property**
    
    | Property | Type | Description |
    | --- | --- | --- |
    | hasFFS | Boolean | "For Further Study" 포함 여부 |
    | hasTBD | Boolean | "To Be Determined" 포함 여부 |
    
    ### 3.3 Conclusion
    
    Resolution 속성 상속 + 추가 속성
    
    **추가 Data Property**
    
    | Property | Type | Description |
    | --- | --- | --- |
    | hasConsensus | Boolean | 합의 도달 여부 |
    
    ### 3.4 WorkingAssumption
    
    Resolution 속성 상속 + 추가 속성
    
    **추가 Object Property**
    
    | Property | Range | Description |
    | --- | --- | --- |
    | promotedTo | Agreement | Agreement로 확정 시 연결 |
    
    ---
    
    ## 4. Tdoc 확장 클래스 속성
    
    ### 4.1 Summary
    
    Tdoc 속성 상속 (Phase-1 정의) + 추가 속성
    
    **추가 Data Property**
    
    | Property | Type | Description |
    | --- | --- | --- |
    | summaryType | Enum (FL, Moderator) | Summary 유형 |
    | roundNumber | Integer | 라운드 번호 (0, 1, 2, ...) |
    
    **추가 Object Property**
    
    | Property | Range | Description |
    | --- | --- | --- |
    | moderatedBy | Company | Moderator 소속 회사 |
    
    ### 4.2 SessionNotes
    
    Tdoc 속성 상속 (Phase-1 정의) + 추가 속성
    
    **추가 Data Property**: 없음
    
    **추가 Object Property**
    
    | Property | Range | Description |
    | --- | --- | --- |
    | chairedBy | Company | Ad-hoc Chair 소속 회사 |
    
    ---
    
    ## 5. Embedded Content 클래스 속성
    
    ### 5.1 Figure
    
    **Data Property**
    
    | Property | Type | Description |
    | --- | --- | --- |
    | figureId | String | Figure 고유 식별자 (예: FIG-112-001) |
    | caption | String | Figure 캡션 텍스트 |
    | filePath | String | 원본 이미지 파일 경로 |
    | figureNumber | String | 원본 Figure 번호 (예: "Figure 1") |
    
    **Object Property**
    
    | Property | Range | Description |
    | --- | --- | --- |
    | containedIn | Meeting | Figure가 포함된 회의 |
    
    ### 5.2 Table
    
    **Data Property**
    
    | Property | Type | Description |
    | --- | --- | --- |
    | tableId | String | Table 고유 식별자 (예: TBL-112-001) |
    | caption | String | Table 캡션 텍스트 |
    | filePath | String | 원본 테이블 파일 경로 (HTML) |
    | tableNumber | String | 원본 Table 번호 (예: "Table 7.8-1") |
    | equations | String (multi-valued) | 테이블 내 수식 목록 (LaTeX) |
    
    **Object Property**
    
    | Property | Range | Description |
    | --- | --- | --- |
    | containedIn | Meeting | Table이 포함된 회의 |
    
    ### 5.3 Chart
    
    **Data Property**
    
    | Property | Type | Description |
    | --- | --- | --- |
    | chartId | String | Chart 고유 식별자 (예: CHT-112-001) |
    | caption | String | Chart 캡션 텍스트 |
    | chartPath | String | 차트 XML 파일 경로 |
    | chartType | String | 차트 타입 (scatterChart, lineChart, barChart, pieChart 등) |
    | chartNumber | String | 원본 번호 (예: "6.3.2-1") |
    
    **Object Property**
    
    | Property | Range | Description |
    | --- | --- | --- |
    | containedIn | Meeting | Chart가 포함된 회의 |
    
    ### 5.4 Equation 처리 (클래스 아님)
    
    | 항목 | 내용 |
    | --- | --- |
    | 원본 형식 | OMML (`<m:oMath>`) |
    | 저장 형식 | LaTeX (`$...$`) |
    | 변환 방법 | OMML → 임시 DOCX → Pandoc → LaTeX |
    | 저장 위치 | Resolution `contentWithEquations`, Table `equations`에 인라인 |
    
    ---
    
    ## 6. 전체 Object Property 목록 (Phase-2 신규)
    
    | # | Property | Domain | Range | Description |
    | --- | --- | --- | --- | --- |
    | 1 | references | Resolution | Tdoc | Resolution이 참조하는 Tdoc |
    | 2 | madeAt | Resolution | Meeting | Resolution이 도출된 회의 |
    | 3 | resolutionBelongsTo | Resolution | AgendaItem | Resolution이 속한 Agenda |
    | 4 | hasResolutions | AgendaItem | Resolution | Agenda에 속한 Resolution (역관계) |
    | 5 | promotedTo | WorkingAssumption | Agreement | WA → Agreement 전환 |
    | 6 | moderatedBy | Summary | Company | Moderator 소속 회사 |
    | 7 | chairedBy | SessionNotes | Company | Ad-hoc Chair 소속 회사 |
    | 8 | hasFigure | Resolution | Figure | Resolution이 참조하는 Figure |
    | 9 | hasTable | Resolution | Table | Resolution이 참조하는 Table |
    | 10 | hasChart | Resolution | Chart | Resolution이 참조하는 Chart |
    | 11 | containedIn | Figure, Table, Chart | Meeting | Figure/Table/Chart가 포함된 회의 |
    
    ---
    
    ## 7. 전체 Data Property 목록 (Phase-2 신규)
    
    | # | Property | Domain | Type | Description |
    | --- | --- | --- | --- | --- |
    | 1 | resolutionId | Resolution | String | Resolution 고유 식별자 |
    | 2 | content | Resolution | String | Resolution 본문 텍스트 (수식을 `[EQUATION]` 마커로 대체). **Text-to-Cypher 검색용**. |
    | 3 | contentWithEquations | Resolution | String | Resolution 본문 텍스트 (수식 LaTeX 인라인 포함). **LLM 답변 생성 및 UI 렌더링용**. |
    | 4 | sequence | Resolution | Integer | 같은 Agenda 내 순서 |
    | 5 | sessionContext | Resolution | String | 세션 정보 |
    | 6 | note | Resolution | String | 부가 설명 |
    | 7 | hasFFS | Agreement | Boolean | FFS 포함 여부 |
    | 8 | hasTBD | Agreement | Boolean | TBD 포함 여부 |
    | 9 | hasConsensus | Conclusion | Boolean | 합의 도달 여부 |
    | 10 | summaryType | Summary | Enum | Summary 유형 (FL/Moderator) |
    | 11 | roundNumber | Summary | Integer | 라운드 번호 |
    | 12 | figureId | Figure | String | Figure 고유 식별자 |
    | 13 | caption | Figure, Table, Chart | String | 캡션 텍스트 |
    | 14 | filePath | Figure, Table | String | 원본 파일 경로 |
    | 15 | figureNumber | Figure | String | 원본 Figure 번호 |
    | 16 | tableId | Table | String | Table 고유 식별자 |
    | 17 | tableNumber | Table | String | 원본 Table 번호 |
    | 18 | equations | Table | String (multi-valued) | 테이블 내 수식 (LaTeX) |
    | 19 | chartId | Chart | String | Chart 고유 식별자 |
    | 20 | chartPath | Chart | String | 차트 XML 파일 경로 |
    | 21 | chartType | Chart | String | 차트 타입 |
    | 22 | chartNumber | Chart | String | 원본 번호 |
    
    참고: caption, containedIn은 Figure/Table/Chart와 공유하므로 별도 추가 불필요
    
    ---
    
    ## 8. content vs contentWithEquations 사용 규칙
    
    Resolution 검색 및 답변 생성 시 두 필드의 역할이 다름.
    
    ### 8.1 필드별 용도
    
    | Phase | 사용 필드 | 이유 |
    | --- | --- | --- |
    | **검색 (Text-to-Cypher)** | content | `[EQUATION]` 마커로 노이즈 제거, 텍스트 매칭 정확도 향상 |
    | **답변 생성 (LLM context)** | contentWithEquations | 수식 포함 완전한 정보로 정확한 답변 |
    | **UI 렌더링** | contentWithEquations | LaTeX 수식 렌더링 |
    
    ### 8.2 처리 흐름
    
    ```
    1. 사용자 질문 → Text-to-Cypher 생성
    2. Cypher 쿼리에서 content 필드로 Resolution 검색
    3. 검색된 Resolution의 contentWithEquations를 LLM context로 전달
    4. LLM이 contentWithEquations 기반으로 답변 생성
    5. UI에서 contentWithEquations의 LaTeX 렌더링
    
    ```
    
    ### 8.3 예시
    
    **검색 Cypher**:
    
    ```
    MATCH (r:Agreement)
    WHERE r.content CONTAINS 'processing time'
    RETURN r.resolutionId, r.contentWithEquations
    LIMIT 5
    
    ```
    
    *Note: WHERE 조건은 `content`, RETURN은 `contentWithEquations`*
    
    ---
    
    ## Step 6: 제약조건(Facet) 정의
    
    > Ontology 101 원칙
    > 
    > 
    > *"Define the facets of the slots... Slots can have different facets describing the value type, allowed values, the number of the values (cardinality), and other features of the values the slot can take."*
    > 
    > — Noy & McGuinness, Ontology Development 101
    > 
    
    ---
    
    ## 1. Step 6 목적
    
    - Step 5에서 정의한 속성의 **제약조건(Facet)** 정의
    - **Cardinality**: 속성값 개수 (0..1, 1, 0..*, 1..*)
    - **필수 여부**: 인스턴스 생성 시 반드시 값이 필요한지
    - **Functional**: 단일값만 허용하는지
    - **Inverse**: 역관계가 있는지
    
    ---
    
    ## 2. Facet 종류
    
    | Facet | 설명 | 예시 |
    | --- | --- | --- |
    | **Cardinality** | 속성값 개수 | 0..1, 1, 0..*, 1..* |
    | **Required** | 필수 여부 | ✅ / ❌ |
    | **Functional** | 단일값만 허용 | ✅ (최대 1개) |
    | **Inverse** | 역관계 | resolutionBelongsTo ↔ hasResolutions |
    
    ### Cardinality 표기법
    
    | 표기 | 의미 | Required | Functional |
    | --- | --- | --- | --- |
    | 1 | 정확히 1개 | ✅ | ✅ |
    | 0..1 | 0개 또는 1개 | ❌ | ✅ |
    | 1..* | 1개 이상 | ✅ | ❌ |
    | 0..* | 0개 이상 | ❌ | ❌ |
    
    ---
    
    ## 3. Data Property Facet
    
    ### 3.1 Resolution (추상 클래스)
    
    | Property | Type | Cardinality | Required | Description |
    | --- | --- | --- | --- | --- |
    | resolutionId | String | 1 | ✅ | PK, 패턴: `{TYPE}-{meeting}-{agenda}-{seq}` |
    | content | String | 1 | ✅ | Resolution 본문 (수식을 `[EQUATION]` 마커로 대체, 검색/쿼리용) |
    | contentWithEquations | String | 0..1 | ❌ | Resolution 본문 (수식 LaTeX 포함, 렌더링용). 수식이 없는 Resolution에서는 null. 수식 포함 비율은 Appendix A [P2-V09] 참조 |
    | sequence | Integer | 1 | ✅ | 같은 Agenda 내 순서. *Note: resolutionId에서 추출 가능 (예: AGR-112-8.1-001의 001)* |
    | sessionContext | String | 0..1 | ❌ | 세션 정보 (예: "Thursday session", "Online") |
    | note | String | 0..1 | ❌ | 부가 설명 |
    
    ### 3.2 Agreement
    
    Resolution 상속 + 추가 속성
    
    | Property | Type | Cardinality | Required | Description |
    | --- | --- | --- | --- | --- |
    | hasFFS | Boolean | 0..1 | ❌ | default: false |
    | hasTBD | Boolean | 0..1 | ❌ | default: false |
    
    ### 3.3 Conclusion
    
    Resolution 상속 + 추가 속성
    
    | Property | Type | Cardinality | Required | Description |
    | --- | --- | --- | --- | --- |
    | hasConsensus | Boolean | 0..1 | ❌ | 합의 도달 여부. 커버리지는 Appendix A [P2-V10] 참조 |
    
    ### 3.4 WorkingAssumption
    
    Resolution 상속, 추가 Data Property 없음
    
    ### 3.5 Summary
    
    Tdoc 상속 (Phase-1) + 추가 속성
    
    | Property | Type | Cardinality | Required | Description |
    | --- | --- | --- | --- | --- |
    | summaryType | Enum | 1 | ✅ | 값: FL, Moderator |
    | roundNumber | Integer | 0..1 | ❌ | min: 0 |
    
    ### 3.6 SessionNotes
    
    Tdoc 상속 (Phase-1), 추가 Data Property 없음
    
    ### 3.7 Figure
    
    | Property | Type | Cardinality | Required | Description |
    | --- | --- | --- | --- | --- |
    | figureId | String | 1 | ✅ | PK, 패턴: `FIG-{meeting}-{seq}` |
    | caption | String | 0..1 | ❌ | Figure 캡션 (있는 경우만) |
    | filePath | String | 0..1 | ❌ | 원본 이미지 파일 경로 (이미지 누락 시 없음) |
    | figureNumber | String | 0..1 | ❌ | 원본 Figure 번호 |
    
    ### 3.8 Table
    
    | Property | Type | Cardinality | Required | Description |
    | --- | --- | --- | --- | --- |
    | tableId | String | 1 | ✅ | PK, 패턴: `TBL-{meeting}-{seq}` |
    | caption | String | 0..1 | ❌ | Table 캡션 (있는 경우만) |
    | filePath | String | 1 | ✅ | 원본 HTML 파일 경로 |
    | tableNumber | String | 0..1 | ❌ | 원본 Table 번호 |
    | equations | String (multi-valued) | 0..* | ❌ | 테이블 내 수식 (LaTeX) |
    
    ### 3.9 Chart
    
    | Property | Type | Cardinality | Required | Description |
    | --- | --- | --- | --- | --- |
    | chartId | String | 1 | ✅ | PK, 패턴: `CHT-{meeting}-{seq}` |
    | caption | String | 1 | ✅ | Chart 캡션 |
    | chartPath | String | 1 | ✅ | 차트 XML 파일 경로 |
    | chartType | String | 1 | ✅ | 차트 타입 |
    | chartNumber | String | 0..1 | ❌ | 원본 번호 |
    
    ---
    
    ## 4. Object Property Facet
    
    ### 4.1 Resolution 관계
    
    | Property | Domain | Range | Cardinality | Functional | Inverse |
    | --- | --- | --- | --- | --- | --- |
    | references | Resolution | Tdoc | 0..* | ❌ | - |
    | madeAt | Resolution | Meeting | 1..* | ❌ | - |
    | resolutionBelongsTo | Resolution | AgendaItem | 1 | ✅ | hasResolutions |
    | hasFigure | Resolution | Figure | 0..* | ❌ | - |
    | hasTable | Resolution | Table | 0..* | ❌ | - |
    | hasChart | Resolution | Chart | 0..* | ❌ | - |
    
    ### 4.2 WorkingAssumption 추가 관계
    
    | Property | Domain | Range | Cardinality | Functional | Inverse |
    | --- | --- | --- | --- | --- | --- |
    | promotedTo | WorkingAssumption | Agreement | 0..1 | ✅ | - |
    
    ### 4.3 Summary 관계
    
    | Property | Domain | Range | Cardinality | Functional | Inverse |
    | --- | --- | --- | --- | --- | --- |
    | moderatedBy | Summary | Company | 1 | ✅ | - |
    
    ### 4.4 SessionNotes 관계
    
    | Property | Domain | Range | Cardinality | Functional | Inverse |
    | --- | --- | --- | --- | --- | --- |
    | chairedBy | SessionNotes | Company | 1 | ✅ | - |
    
    ### 4.5 AgendaItem 역관계 (Phase-1 확장)
    
    | Property | Domain | Range | Cardinality | Functional | Inverse |
    | --- | --- | --- | --- | --- | --- |
    | hasResolutions | AgendaItem | Resolution | 0..* | ❌ | resolutionBelongsTo |
    
    ### 4.6 Embedded Content 관계
    
    | Property | Domain | Range | Cardinality | Functional | Inverse |
    | --- | --- | --- | --- | --- | --- |
    | containedIn | Figure, Table, Chart | Meeting | 1 | ✅ | - |
    
    ---
    
    ## 5. 필수 속성 요약
    
    ### 5.1 필수 Data Property
    
    | Class | Required Properties |
    | --- | --- |
    | Resolution | resolutionId, content, sequence |
    | Agreement | (상속) |
    | Conclusion | (상속) |
    | WorkingAssumption | (상속) |
    | Summary | summaryType |
    | SessionNotes | - |
    | Figure | figureId |
    | Table | tableId, filePath |
    | Chart | chartId, caption, chartPath, chartType |
    
    ### 5.2 필수 Object Property
    
    | Class | Required Properties |
    | --- | --- |
    | Resolution | madeAt, resolutionBelongsTo |
    | Summary | moderatedBy |
    | SessionNotes | chairedBy |
    | Figure | containedIn |
    | Table | containedIn |
    | Chart | containedIn |
    
    ---
    
    ## 6. Functional Property 요약
    
    단일값만 허용하는 Object Property:
    
    | Property | Domain | Range | Description |
    | --- | --- | --- | --- |
    | resolutionBelongsTo | Resolution | AgendaItem | Resolution은 하나의 Agenda에만 |
    | promotedTo | WorkingAssumption | Agreement | WA → Agreement는 1:1 |
    | moderatedBy | Summary | Company | Moderator는 한 회사 |
    | chairedBy | SessionNotes | Company | Chair는 한 회사 |
    | containedIn | Figure, Table, Chart | Meeting | Figure/Table/Chart는 하나의 회의에만 |
    
    ---
    
    ## 7. Inverse Property 요약
    
    | Forward | Inverse | Description |
    | --- | --- | --- |
    | resolutionBelongsTo | hasResolutions | Resolution ↔ AgendaItem |
    
    ---
    
    ## Step 7: 인스턴스 생성 명세
    
    > Ontology 101 원칙
    > 
    > 
    > *"The last step is creating individual instances of classes in the hierarchy. Defining an individual instance of a class requires (1) choosing a class, (2) creating an individual instance of that class, and (3) filling in the slot values."*
    > 
    > — Noy & McGuinness, Ontology Development 101
    > 
    
    ---
    
    ## 1. Step 7 목적
    
    - Step 4에서 정의한 클래스의 **인스턴스 생성 규칙** 정의
    - **ID 생성 규칙**: 인스턴스 식별자 패턴
    - **데이터 소스 매핑**: Final Report → 속성값
    - **예시 인스턴스**: 실제 데이터 기반 예시
    
    ---
    
    ## 2. 인스턴스 현황
    
    | Phase | 데이터 소스 | 상태 |
    | --- | --- | --- |
    | Phase-1 | Tdoc_list (Excel) | ✅ 구현 완료 |
    | **Phase-2** | **Final Report (Word)** | ✅ 완료 |
    
    ---
    
    ## 3. ID 생성 규칙
    
    ### 3.1 ID 생성 원칙
    
    | 원칙 | 설명 |
    | --- | --- |
    | 유일성 | 클래스 내에서 고유한 값 |
    | 불변성 | 한 번 생성되면 변경 불가 |
    | 의미성 | 도메인 의미 반영 |
    | 추적성 | 데이터 소스와 매핑 가능 |
    
    ### 3.2 Resolution 계층 ID
    
    | 클래스 | ID 속성 | 패턴 | 예시 |
    | --- | --- | --- | --- |
    | Agreement | resolutionId | `AGR-{meeting}-{agenda}-{seq}` | AGR-112-8.1-001 |
    | Conclusion | resolutionId | `CON-{meeting}-{agenda}-{seq}` | CON-112-9.2-001 |
    | WorkingAssumption | resolutionId | `WA-{meeting}-{agenda}-{seq}` | WA-112-8.1-001 |
    
    **ID 구성 요소**:
    
    - `{meeting}`: 회의 번호 (예: 112, 120, 122)
    - `{agenda}`: Agenda Item 번호 (예: 8.1, 9.2.1)
    - `{seq}`: 해당 Agenda 내 순번 (001, 002, ...)
    
    ### 3.3 Tdoc 확장 클래스 ID
    
    | 클래스 | ID 속성 | 패턴 | 예시 | 소스 |
    | --- | --- | --- | --- | --- |
    | Summary | tdocNumber | `R1-\d{7}` | R1-2302021 | Final Report Tdoc 참조 |
    | SessionNotes | tdocNumber | `R1-\d{7}` | R1-2302051 | Final Report Tdoc 참조 |
    
    *Note: Summary, SessionNotes는 Tdoc 하위 클래스이므로 기존 tdocNumber를 ID로 사용*
    
    ### 3.4 Embedded Content ID
    
    | 클래스 | ID 속성 | 패턴 | 예시 |
    | --- | --- | --- | --- |
    | Figure | figureId | `FIG-{meeting}-{seq}` | FIG-112-001 |
    | Table | tableId | `TBL-{meeting}-{seq}` | TBL-112-001 |
    | Chart | chartId | `CHT-{meeting}-{seq}` | CHT-114b-001 |
    
    **ID 구성 요소**:
    
    - `{meeting}`: 회의 번호 (예: 112, 120, 122)
    - `{seq}`: 해당 회의 내 순번 (001, 002, ...)
    
    ---
    
    ## 4. 데이터 소스 매핑
    
    ### 4.1 Resolution 매핑
    
    **소스**: Final Report 본문
    
    | 관계 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | references → Tdoc | content 내 참조 | `R1-\\d{7}` 패턴 추출 |
    | madeAt → Meeting | 문서 메타 | 파일명에서 회의 번호 추출 후 Phase-1 Meeting의 `canonicalMeetingNumber`와 매칭 |
    | resolutionBelongsTo → AgendaItem | 섹션 헤더 | Agenda 번호 추출 |
    | hasFigure → Figure | content 내 참조 | `Figure N` 패턴 → 같은 미팅 내 FIG 인스턴스 연결 |
    | hasTable → Table | content 내 참조 | `Table X.Y.Z-N` 패턴 → 같은 미팅 내 TBL 인스턴스 연결 |
    | hasChart → Chart | content 내 참조 | Chart의 Figure 번호 매칭 → 같은 미팅 내 CHT 인스턴스 연결 |
    
    **references → Tdoc 매칭 실패 시 처리 규칙:**
    
    | 조건 | 처리 |
    | --- | --- |
    | 추출된 Tdoc 번호가 Phase-1 인스턴스에 존재 | 기존 인스턴스에 references 관계 생성 |
    | 추출된 Tdoc 번호가 Phase-1 인스턴스에 없음 (다른 WG 문서 등) | references 관계 생성 안 함 + 로그 기록 |
    
    *참고: Resolution 본문에서 추출된 `R1-\\d{7}` 패턴이 RAN1 이외 WG 문서를 참조하는 경우, Phase-1 Tdoc 인스턴스에 존재하지 않을 수 있음. 이 경우 동적 생성하지 않고 관계를 생략함 (Phase-4 Spec 동적 생성과 다른 정책)*
    
    **Meeting 연결 규칙:**
    
    | Final Report 파일명 | 추출된 회의 번호 | 매칭 대상 (Phase-1) | 연결되는 Meeting |
    | --- | --- | --- | --- |
    | Final_Minutes_report_RAN1_112_v100.docx | RAN1#112 | canonicalMeetingNumber = "RAN1#112" | RAN1#112 |
    | Final_Minutes_report_RAN1_120_v100.docx | RAN1#120 | canonicalMeetingNumber = "RAN1#120" | RAN1#120 |
    | Final_Minutes_report_RAN1_100-e_v100.docx | RAN1#100 | canonicalMeetingNumber = "RAN1#100" | RAN1#100, RAN1#100-e |
    
    *참고: RAN1#100-e의 Final Report는 RAN1#100 + RAN1#100-e 내용을 모두 포함하므로, canonicalMeetingNumber가 동일한 두 Meeting 모두에 Resolution이 연결됨 (COVID-19 특수 케이스, Phase-1 Step 5 참조)*
    
    ### 4.2 Agreement 추가 매핑
    
    | 속성 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | hasFFS | content | `FFS` 포함 여부 → Boolean |
    | hasTBD | content | `TBD` 포함 여부 → Boolean |
    
    ### 4.3 Conclusion 추가 매핑
    
    | 속성 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | hasConsensus | content | 부정 합의 패턴 미포함 시 true |
    
    **부정 합의 패턴** (아래 중 하나라도 content에 포함되면 `false`):
    
    | # | 패턴 | 매칭 예시 |
    | --- | --- | --- |
    | 1 | `no [0~1단어] consensus` | "no consensus", "no RAN1 consensus" |
    | 2 | `not [0~1단어] consensus` | "not consensus", "currently not consensus" |
    | 3 | `did not reach consensus` |  |
    | 4 | `could not reach consensus` |  |
    | 5 | `has not reached consensus` |  |
    | 6 | `lack of consensus` |  |
    
    *참고: "not supported"는 합의 결과가 미지원인 것이며 합의 부재가 아니므로 false 대상이 아님*
    
    ### 4.4 WorkingAssumption 추가 매핑
    
    | 관계 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | promotedTo → Agreement | content | `changed to an agreement` 패턴 시 해당 Agreement 연결 |
    
    ### 4.5 Summary 매핑
    
    **소스**: Final Report 본문 내 Tdoc 참조
    
    **식별 패턴**:
    
    ```
    Title contains: "FL summary" OR "Moderator summary" OR "Moderator Summary"
    Source pattern: "Moderator (Company)" OR "Feature Lead (Company)"
    
    ```
    
    | 속성 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | tdocNumber | Tdoc 참조 | `R1-\d{7}` 패턴 |
    | summaryType | Title 패턴 | `FL summary` → FL, `Moderator` → Moderator |
    | roundNumber | Title 패턴 | `#N`, `Round N` → N 추출 |
    
    | 관계 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | moderatedBy → Company | Source 패턴 | `Moderator (Company)` → Company 추출 |
    
    ### 4.6 SessionNotes 매핑
    
    **소스**: Final Report 본문 내 Tdoc 참조
    
    **식별 패턴**:
    
    ```
    Title contains: "Session notes"
    Source pattern: "Ad-hoc Chair (Company)" OR "Ad-Hoc Chair (Company)"
    
    ```
    
    | 속성 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | tdocNumber | Tdoc 참조 | `R1-\d{7}` 패턴 |
    
    | 관계 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | chairedBy → Company | Source 패턴 | `Ad-hoc Chair (Company)` → Company 추출 |
    
    ### 4.7 Figure 매핑
    
    **소스**: Final Report word/media/ 폴더 + 본문
    
    **식별 기준**:
    
    1. 캡션 기반: `Figure X:` 패턴이 있는 경우
    2. 구조 기반: 캡션 없는 `<w:drawing>` 중 이미지 크기 > 50KB이고 본문 내 위치 (Header/Footer 제외)
    
    *Note: word/media/ 내 로고, 인라인 수식 이미지 등 포맷팅용은 제외*
    
    | 속성 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | figureId | 자동 생성 | `FIG-{meeting}-{seq}` |
    | caption | 본문 패턴 | `Figure X:` 이후 텍스트 (있는 경우만) |
    | filePath | word/media/ | 이미지 파일 경로 |
    | figureNumber | 캡션 패턴 | `Figure X` 추출 (있는 경우만) |
    
    | 관계 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | containedIn → Meeting | 문서 메타 | 파일명에서 회의 번호 추출 |
    
    ### 4.8 Table 매핑
    
    **소스**: Final Report 본문 `<w:tbl>`
    
    **식별 기준**:
    
    1. 캡션 기반: `Table X.X.X-X:` 패턴이 있는 경우
    2. 구조 기반: 캡션 없는 `<w:tbl>` 중 (행 수 > 3) AND (숫자/수식 포함) AND (agenda/일정표 패턴 제외)
    
    *Note: 단순 포맷팅 테이블 (agenda, 일정표, Tdoc 목록 등)은 제외*
    
    | 속성 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | tableId | 자동 생성 | `TBL-{meeting}-{seq}` |
    | caption | 본문 패턴 | `Table X.X.X-X:` 이후 텍스트 (있는 경우만) |
    | filePath | 변환 저장 | HTML 파일 경로 |
    | tableNumber | 캡션 패턴 | `Table X.X.X-X` 추출 |
    | equations | 테이블 내 OMML | LaTeX 변환 후 리스트 |
    
    | 관계 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | containedIn → Meeting | 문서 메타 | 파일명에서 회의 번호 추출 |
    
    ### 4.9 Chart 매핑
    
    **소스**: Final Report 본문 `<w:drawing>` → `<c:chart>`
    
    **식별 기준**: `<a:blip>` 없이 `<c:chart>` 만 있는 drawing 객체
    
    | 속성 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | chartId | 자동 생성 | `CHT-{meeting}-{seq}` |
    | caption | 본문 패턴 | drawing 다음 paragraph에서 캡션 추출 |
    | chartPath | word/charts/ | 차트 XML 파일 경로 |
    | chartType | chart XML | `<c:scatterChart>`, `<c:lineChart>` 등 태그에서 추출 |
    | chartNumber | 캡션 패턴 | 숫자 패턴 추출 (예: "6.3.2-1") |
    
    | 관계 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | containedIn → Meeting | 문서 메타 | 파일명에서 회의 번호 추출 |
    
    ### 4.10 Equation 처리 규칙
    
    | 항목 | 내용 |
    | --- | --- |
    | 원본 형식 | OMML (`<m:oMath>`) |
    | 저장 형식 | LaTeX (`$...$`) |
    | 변환 방법 | OMML → 임시 DOCX → Pandoc → LaTeX |
    | 저장 위치 | Resolution `contentWithEquations`, Table `equations`에 인라인 |
    
    ### 4.11 Null 값 처리 규칙
    
    | 속성/관계 | 상황 | 처리 | 로그 레벨 |
    | --- | --- | --- | --- |
    | content | 파싱 실패 | Resolution 인스턴스 미생성 | ERROR |
    | contentWithEquations | 수식 없음 | null 유지 (정상) | - |
    | contentWithEquations | 수식 변환 실패 | null + 로그 기록 | WARNING |
    | references | Tdoc 번호가 Phase-1 인스턴스에 없음 | 해당 참조만 스킵 (§4.1 참조) | WARNING |
    | references | Tdoc 번호 파싱 실패 | 해당 참조만 스킵 | WARNING |
    | caption (Figure/Table) | 캡션 없음 | null 유지 (정상) | - |
    | moderatedBy | Company 매칭 실패 | Summary 인스턴스 미생성 | ERROR |
    | chairedBy | Company 매칭 실패 | SessionNotes 인스턴스 미생성 | ERROR |
    
    **처리 원칙:**
    
    - `content`(Resolution), `moderatedBy`(Summary), `chairedBy`(SessionNotes)는 필수 속성(Cardinality: 1)이므로 값을 채울 수 없으면 인스턴스 자체를 생성하지 않음
    - `contentWithEquations`, `caption`은 선택 속성(Cardinality: 0..1)이므로 null이 정상
    - moderatedBy/chairedBy는 필수 속성(Cardinality: 1)이므로 매칭 실패 시 Summary/SessionNotes 인스턴스 자체가 생성되지 않는다. 즉 생성된 인스턴스는 정의상 매칭 성공 상태다. 매칭 실패는 파싱 오류로 간주하며, 실측 통계는 파싱 로그에서 확인한다.
    
    ---
    
    ## 5. 예시 인스턴스
    
    ### 5.1 Agreement 예시
    
    ```json
    {
      "@type": "Agreement",
      "resolutionId": "AGR-112-8.1-001",
      "content": "Adopt the following TP to Section 5.2.2.6, TS38.212 for R18 NR positioning enhancements",
      "contentWithEquations": "Adopt the following TP to Section 5.2.2.6, TS38.212 for R18 NR positioning enhancements",
      "sequence": 1,
      "note": "No specification impact is expected",
      "hasFFS": false,
      "hasTBD": false,
      "references": [
        { "@id": "tdoc:R1-2302088" },
        { "@id": "tdoc:R1-2302089" }
      ],
      "resolutionBelongsTo": { "@id": "agenda:8.1" },
      "madeAt": { "@id": "meeting:RAN1#112" },
      "hasFigure": [
        { "@id": "figure:FIG-112-001" }
      ],
      "hasTable": [
        { "@id": "table:TBL-112-001" }
      ]
    }
    
    ```
    
    ### 5.2 Conclusion 예시
    
    ```json
    {
      "@type": "Conclusion",
      "resolutionId": "CON-112-9.2-001",
      "content": "It is RAN1 understanding that any combination of TCI states is allowed for the configured TCI states",
      "contentWithEquations": "It is RAN1 understanding that any combination of TCI states is allowed for the configured TCI states",
      "sequence": 1,
      "hasConsensus": true,
      "resolutionBelongsTo": { "@id": "agenda:9.2" },
      "madeAt": { "@id": "meeting:RAN1#112" }
    }
    
    ```
    
    ### 5.3 WorkingAssumption 예시
    
    ```json
    {
      "@type": "WorkingAssumption",
      "resolutionId": "WA-112-8.1-001",
      "content": "For RAN1#111 agreement of the antenna ports indication, the UE behavior is defined as follows...",
      "contentWithEquations": "For RAN1#111 agreement of the antenna ports indication, the UE behavior is defined as follows...",
      "sequence": 1,
      "resolutionBelongsTo": { "@id": "agenda:8.1" },
      "madeAt": { "@id": "meeting:RAN1#112" },
      "promotedTo": { "@id": "resolution:AGR-113-8.1-005" }
    }
    
    ```
    
    ### 5.4 Summary 예시
    
    ```json
    {
      "@type": "Summary",
      "tdocNumber": "R1-2302021",
      "title": "FL summary #2 of SPS PDSCH dropping",
      "summaryType": "FL",
      "roundNumber": 2,
      "moderatedBy": { "@id": "company:ericsson" },
      "belongsTo": { "@id": "agenda:8.1" },
      "presentedAt": { "@id": "meeting:RAN1#112" }
    }
    
    ```
    
    ### 5.5 SessionNotes 예시
    
    ```json
    {
      "@type": "SessionNotes",
      "tdocNumber": "R1-2302051",
      "title": "Session notes for AI 6.2.1.1 – AI/ML for CSI",
      "chairedBy": { "@id": "company:qualcomm" },
      "belongsTo": { "@id": "agenda:6.2.1.1" },
      "presentedAt": { "@id": "meeting:RAN1#112" }
    }
    
    ```
    
    ### 5.6 Figure 예시
    
    ```json
    {
      "@type": "Figure",
      "figureId": "FIG-112-001",
      "caption": "UE processing timeline for PUSCH preparation",
      "filePath": "/data/figures/RAN1_112/image1.png",
      "figureNumber": "Figure 1",
      "containedIn": { "@id": "meeting:RAN1#112" }
    }
    
    ```
    
    **캡션 없는 Figure 예시**
    
    ```json
    {
      "@type": "Figure",
      "figureId": "FIG-100-003",
      "filePath": "/data/figures/RAN1_100/image5.emf",
      "containedIn": { "@id": "meeting:RAN1#100" }
    }
    
    ```
    
    ### 5.7 Table 예시
    
    ```json
    {
      "@type": "Table",
      "tableId": "TBL-112-001",
      "caption": "Simulation assumptions for large scale calibration",
      "filePath": "/data/tables/RAN1_112/table_7.8-1.html",
      "tableNumber": "Table 7.8-1",
      "equations": [
        "$T_{proc,2} = \\max(...)$",
        "$N_{2} + d_{2,1}$"
      ],
      "containedIn": { "@id": "meeting:RAN1#112" }
    }
    
    ```
    
    **캡션 없는 Table 예시**
    
    ```json
    {
      "@type": "Table",
      "tableId": "TBL-112-015",
      "filePath": "/data/tables/RAN1_112/table_inline_001.html",
      "equations": ["$N_{2} + d_{2,1}$"],
      "containedIn": { "@id": "meeting:RAN1#112" }
    }
    
    ```
    
    ### 5.8 Chart 예시
    
    ```json
    {
      "@type": "Chart",
      "chartId": "CHT-114b-001",
      "caption": "Figure 6.3.2-1",
      "chartPath": "/data/charts/RAN1_114b/chart1.xml",
      "chartType": "scatterChart",
      "chartNumber": "6.3.2-1",
      "containedIn": { "@id": "meeting:RAN1#114b" }
    }
    
    ```
    
    ### 5.9 Equation 인라인 예시
    
    Resolution contentWithEquations 내 수식 포함 (content는 수식 제외):
    
    ```json
    {
      "@type": "Agreement",
      "resolutionId": "AGR-112-8.1-001",
      "content": "The UE processing time is defined as [EQUATION] after the end of reception...",
      "contentWithEquations": "The UE processing time is defined as $T_{proc,2} = \\max\\left( (N_{2} + d_{2,1} + d_{2} + d_{3})(2048 + 144) \\cdot \\kappa 2^{- \\mu} \\cdot T_{C} + T_{ext} + T_{switch},d_{2,2} \\right)$ after the end of reception...",
      "sequence": 1,
      "resolutionBelongsTo": { "@id": "agenda:8.1" },
      "madeAt": { "@id": "meeting:RAN1#112" }
    }
    ```
    
    ---
    
    ## 6. 요약
    
    ### 6.1 Phase-2 인스턴스 생성 명세
    
    | 클래스 | ID 패턴 | 데이터 소스 | 예상 수 |
    | --- | --- | --- | --- |
    | Agreement | AGR-{m}-{a}-{s} | Final Report 본문 | [P2-V01] |
    | Conclusion | CON-{m}-{a}-{s} | Final Report 본문 | [P2-V02] |
    | WorkingAssumption | WA-{m}-{a}-{s} | Final Report 본문 | [P2-V03] |
    | Summary | R1-XXXXXXX | Final Report Tdoc 참조 | [P2-V04] |
    | SessionNotes | R1-XXXXXXX | Final Report Tdoc 참조 | [P2-V05] |
    | Figure | FIG-{m}-{s} | word/media/ (캡션 + 구조 기반) | [P2-V06] |
    | Table | TBL-{m}-{s} | 본문 `<w:tbl>` (캡션 + 구조 기반) | [P2-V07] |
    | Chart | CHT-{m}-{s} | `<w:drawing>` → `<c:chart>` | [P2-V08] |
    
    ### 6.2 매핑 규칙 요약
    
    | 클래스 | 식별 패턴 | 주요 추출 |
    | --- | --- | --- |
    | Agreement | `[Agreement]` | content + contentWithEquations, references, hasFFS, hasTBD |
    | Conclusion | `[Conclusion]` | content + contentWithEquations, hasConsensus |
    | WorkingAssumption | `[Working Assumption]` | content + contentWithEquations, promotedTo |
    | Summary | `FL summary`, `Moderator summary` | summaryType, roundNumber, moderatedBy |
    | SessionNotes | `Session notes` | chairedBy |
    | Figure | 캡션 패턴 또는 구조 기반 | caption (Optional), filePath, figureNumber |
    | Table | 캡션 패턴 또는 구조 기반 | caption (Optional), filePath, tableNumber, equations |
    | Chart | `<c:chart>` XML | caption, chartPath, chartType, chartNumber |
    
    ---
    
    ## 7. 전체 완료
    
    Phase-2 온톨로지 설계가 완료되었습니다.
    
    ### 7.1 Embedded Content 처리 요약
    
    | 대상 | Graph DB | 별도 저장소 | 변환 방식 |
    | --- | --- | --- | --- |
    | **Figure** | 메타데이터 (ID, caption, filePath) | 원본 이미지 | word/media/ 추출 |
    | **Table** | 메타데이터 + 수식(LaTeX) | 원본 HTML | XML 파싱 + HTML 변환 |
    | **Chart** | 메타데이터 (ID, caption, chartPath, chartType) | Chart XML | word/charts/ 추출 |
    | **Equation** | contentWithEquations에 인라인 (LaTeX) | 없음 | OMML → Pandoc → LaTeX |
    
    ---
    
    ## Appendix A: 기준 수치
    
    > 이 테이블이 Spec의 수치 권위 소스이다.
    > 
    
    > 새 미팅 데이터 추가 시 이 테이블만 수정한다.
    > 
    
    | ID | 항목 | 기준값 | 비고 |
    | --- | --- | --- | --- |
    | P2-V01 | Agreement 수 | 21,058 | stale cleanup 반영 |
    | P2-V02 | Conclusion 수 | 2,703 | stale cleanup 반영 |
    | P2-V03 | WorkingAssumption 수 | 949 | stale cleanup 반영 |
    | P2-V04 | Summary 수 | 3,468 |  |
    | P2-V05 | SessionNotes 수 | 678 |  |
    | P2-V06 | Figure 수 | 120 |  |
    | P2-V07 | Table 수 | 1,441 |  |
    | P2-V08 | Chart 수 | 1 |  |
    | P2-V09 | 수식 포함 Resolution 수 | 998 (4.0%) | AGR 895, CON 48, WA 55 |
    | P2-V10 | hasConsensus 커버리지 | 2,617/2,703 (96.8%) | Conclusion 중 합의 판별 성공 비율 |
    
    ### A.2 구현 CQ 검증 결과
    
    > Spec Step 1의 CQ는 온톨로지 **설계 근거**이다.
    아래는 구현에서 사용하는 **검증 CQ**로, 설계 CQ를 포함하되 구현 검증용으로 확장/재구성되었다.
    > 
    
    | 항목 | 설계 CQ (Spec) | 검증 CQ (구현) |
    | --- | --- | --- |
    | 데이터셋 | - | cq_test_dataset.json v3.0 |
    | 검증 결과 | - | PASS |
    
    검증 CQ 카테고리 매핑:
    
    | 구현 카테고리 | 대응 Spec CQ |
    | --- | --- |
    | CQ1 (Resolution 조회) | CQ1 |
    | CQ2 (Tdoc-Resolution 추적) | CQ2 |
    | CQ3 (회사별 기여도) | CQ3 |
    | CQ4 (기술주도권분석) | CQ4 (역할) |
    | CQ5 (기술트렌드) | CQ6 (트렌드/비교) |
    
    ### A.3 Optional 속성 구현 현황
    
    | 속성 | Cardinality | 구현 상태 | 비고 |
    | --- | --- | --- | --- |
    | note | 0..1 | 미구현 (원본 미마킹) | 실측 0%. Spec 유지, 향후 구현 대상 |
    | sessionContext | 0..1 | 미구현 (원본 미마킹) | 실측 0%. Spec 유지, 향후 구현 대상 |
    | hasConsensus | 0..1 | ✅ 구현 완료 | 커버리지 [P2-V10] |
    | promotedTo | 0..1 | 미구현 (자동 판별 불가) | Spec 유지, 향후 구현 대상 |