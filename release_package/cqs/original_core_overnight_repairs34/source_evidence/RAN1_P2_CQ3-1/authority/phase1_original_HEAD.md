- **phase-1: Ontology 101 기반 표준화 엔지니어 타겟 Tdoc 관계 모델링 (Tdoc_list)**
    
    ## Step 1: Domain과 Scope 결정
    
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
    
    **3GPP RAN1 회의 문서(Tdoc) 메타데이터와 그 관계**
    
    ### 1.2 For what are we going to use the ontology?
    
    **표준화 엔지니어의 업무 지원**:
    
    - Tdoc 검색 및 필터링
    - Tdoc 간 관계 추적 (revision, LS)
    - 회사별/기술별 기고 분석
    - 회의 결과 요약
    
    ### 1.3 Who will use and maintain the ontology?
    
    | 사용자 | 핵심 니즈 |
    | --- | --- |
    | **표준화 엔지니어** | Tdoc 검색, 관계 추적, 경쟁사 분석 |
    
    ### 1.4 데이터 소스
    
    | Phase | 데이터 소스 | 범위 |
    | --- | --- | --- |
    | **Phase-1** | **Tdoc_list (Excel)** | [P1-V05] |
    
    ---
    
    ## 2. Scope 정의
    
    ### 2.1 포함 (In Scope)
    
    | 포함 | 제외 |
    | --- | --- |
    | Tdoc 메타데이터 | TS/TR 본문 |
    | Tdoc 간 관계 (revision, LS) | Final Minutes 본문 (Phase-2에서) |
    | 회의 정보 | RAN4/5 데이터 |
    | 회사 정보 |  |
    | Work Item / Agenda Item |  |
    | Release 정보 |  |
    
    ---
    
    ## 3. Competency Questions
    
    ### CQ1. Tdoc 기본 검색
    
    | # | Competency Question |
    | --- | --- |
    | 1-1 | 특정 회의에서 특정 Work Item 관련 Tdoc 목록은? |
    | 1-2 | 특정 회의에서 특정 Agenda Item 관련 Tdoc 목록은? |
    | 1-3 | 특정 회의에서 특정 회사가 제출한 Tdoc 목록은? |
    | 1-4 | 특정 Release에서 논의된 Tdoc 목록은? |
    | 1-5 | 특정 회의에서 승인/합의된 Tdoc 목록은? |
    | 1-6 | 특정 Tdoc의 결정 결과(Status)는? |
    | 1-7 | 특정 Tdoc의 목적(For)은? |
    | 1-8 | 특정 Tdoc의 담당자(Contact)는? |
    | 1-9 | 이번 회의 전체 Agenda 목록과 설명은? |
    
    ### CQ2. Tdoc 관계 추적
    
    | # | Competency Question |
    | --- | --- |
    | 2-1 | 특정 Tdoc의 이전/이후 revision은? |
    | 2-2 | 특정 LS가 어디서 왔고 어디로 갔나? |
    | 2-3 | 특정 Tdoc이 어떤 LS의 답변(Reply)인가? |
    | 2-4 | 특정 Tdoc이 어떤 TS/Spec을 변경하나? |
    | 2-5 | 특정 CR의 카테고리와 영향 범위는? |
    | 2-6 | 이번 회의에서 다음 회의로 연기된 Tdoc은? |
    | 2-7 | 이번 회의에 들어온 LS 목록과 관련 Agenda Item은? |
    
    ### CQ3. 회사/경쟁사 분석
    
    | # | Competency Question |
    | --- | --- |
    | 3-1 | 특정 회사가 특정 Work Item에서 낸 기고 목록은? |
    | 3-2 | 특정 Agenda Item 관련 다른 회사 기고 목록은? |
    | 3-3 | 특정 Work Item에서 회사별 기고 수는? |
    | 3-4 | 특정 회사의 Tdoc 중 채택된 비율은? |
    | 3-5 | 특정 Tdoc과 같은 Agenda Item에서 다른 회사가 낸 Tdoc 목록은? |
    | 3-6 | 특정 회사의 주력 기술 영역(Work Item별 기고 분포)은? |
    
    ### CQ4. 히스토리/요약
    
    | # | Competency Question |
    | --- | --- |
    | 4-1 | 특정 기술에서 우리 회사가 이전 회의들에서 낸 기고 목록은? |
    | 4-2 | 이번 회의에서 우리 회사 기고 결과 요약은? |
    | 4-3 | 특정 Agenda Item에서 아직 미결(not treated)인 Tdoc은? |
    
    ---
    
    ## 4. CQ 결과 규칙
    
    ### 4.1 정렬 기준 (Default Sort Order)
    
    | CQ 그룹 | Primary Sort | Secondary Sort | 구현 속성 |
    | --- | --- | --- | --- |
    | CQ1. Tdoc 기본 검색 | Meeting 번호 DESC | Agenda 번호 ASC, TDoc 번호 ASC | `meetingNumberInt DESC` |
    | CQ2. Tdoc 관계 추적 | TDoc 번호 ASC | - | `tdocNumber ASC` |
    | CQ3. 회사/경쟁사 분석 | Count DESC (많은 순) | Company 이름 ASC | `count DESC` |
    | CQ4. 히스토리/요약 | Meeting 번호 DESC | TDoc 번호 ASC | `meetingNumberInt DESC` |
    
    *참고: "Meeting 번호 DESC"는 `meetingNumberInt` 속성으로 정렬해야 숫자 기반 정렬이 보장됨 (문자열 정렬 시 #99 > #122 문제 발생)*
    
    ### 4.2 결과 개수 (Default Limit)
    
    | CQ 유형 | 기본값 | 적용 CQ |
    | --- | --- | --- |
    | 목록 조회 | 10 | 1-1 ~ 1-5, 1-9, 2-1 ~ 2-3, 2-6 ~ 2-7, 3-1 ~ 3-2, 3-5, 4-1, 4-3 |
    | 단일 조회 | 1 | 1-6 ~ 1-8, 2-4 ~ 2-5 |
    | 집계/순위 | 10 | 3-3 ~ 3-4, 3-6, 4-2 |
    
    *참고: Limit은 쿼리 시 파라미터로 조정 가능*
    
    ---
    
    ## 5. CQ vs Tdoc 메타데이터 검증
    
    | # | Competency Question | 필요한 데이터 | 컬럼 존재 | 답변 가능 | 해결 방법 |
    | --- | --- | --- | --- | --- | --- |
    | **CQ1. Tdoc 기본 검색** |  |  |  |  |  |
    | 1-1 | 특정 회의에서 특정 Work Item 관련 Tdoc 목록은? | Meeting, Related WIs | ✅ | ✅ | Meeting 클래스 추가 (Step 4). 파일명에서 추출 |
    | 1-2 | 특정 회의에서 특정 Agenda Item 관련 Tdoc 목록은? | Meeting, Agenda item | ✅ | ✅ | Meeting 클래스 추가 (Step 4). 파일명에서 추출 |
    | 1-3 | 특정 회의에서 특정 회사가 제출한 Tdoc 목록은? | Meeting, Source | ✅ | ✅ | Meeting 클래스 추가 (Step 4). 파일명에서 추출 |
    | 1-4 | 특정 Release에서 논의된 Tdoc 목록은? | Release | ✅ | ✅ | - |
    | 1-5 | 특정 회의에서 승인/합의된 Tdoc 목록은? | Meeting, TDoc Status | ✅ | ✅ | Meeting 클래스 추가 (Step 4). 파일명에서 추출 |
    | 1-6 | 특정 Tdoc의 결정 결과(Status)는? | TDoc Status | ✅ | ✅ | - |
    | 1-7 | 특정 Tdoc의 목적(For)은? | For | ✅ | ✅ | - |
    | 1-8 | 특정 Tdoc의 담당자(Contact)는? | Contact | ✅ | ✅ | - |
    | 1-9 | 이번 회의 전체 Agenda 목록과 설명은? | Agenda item, description | ✅ | ✅ | - |
    | **CQ2. Tdoc 관계 추적** |  |  |  |  |  |
    | 2-1 | 특정 Tdoc의 이전/이후 revision은? | Is revision of, Revised to | ✅ | ✅ | - |
    | 2-2 | 특정 LS가 어디서 왔고 어디로 갔나? | Original LS, To, Cc | ✅ | ✅ | - |
    | 2-3 | 특정 Tdoc이 어떤 LS의 답변(Reply)인가? | Reply to, Reply in | ✅ | ✅ | - |
    | 2-4 | 특정 Tdoc이 어떤 TS/Spec을 변경하나? | Spec | ✅ | ✅ | - |
    | 2-5 | 특정 CR의 카테고리와 영향 범위는? | CR category, Clauses Affected | ✅ | ✅ | - |
    | 2-6 | 이번 회의에서 다음 회의로 연기된 Tdoc은? | TDoc Status (postponed) | ✅ | ✅ | - |
    | 2-7 | 이번 회의에 들어온 LS 목록과 관련 Agenda Item은? | Type (LS in), Agenda item | ✅ | ✅ | - |
    | **CQ3. 회사/경쟁사 분석** |  |  |  |  |  |
    | 3-1 | 특정 회사가 특정 Work Item에서 낸 기고 목록은? | Source, Related WIs | ✅ | ✅ | - |
    | 3-2 | 특정 Agenda Item 관련 다른 회사 기고 목록은? | Agenda item, Source | ✅ | ✅ | - |
    | 3-3 | 특정 Work Item에서 회사별 기고 수는? | Related WIs, Source | ✅ | ✅ | - |
    | 3-4 | 특정 회사의 Tdoc 중 채택된 비율은? | Source, TDoc Status | ✅ | ✅ | - |
    | 3-5 | 특정 Tdoc과 같은 Agenda Item에서 다른 회사가 낸 Tdoc 목록은? | Agenda item, Source | ✅ | ✅ | - |
    | 3-6 | 특정 회사의 주력 기술 영역(Work Item별 기고 분포)은? | Source, Related WIs | ✅ | ✅ | - |
    | **CQ4. 히스토리/요약** |  |  |  |  |  |
    | 4-1 | 특정 기술에서 우리 회사가 이전 회의들에서 낸 기고 목록은? | 여러 회의 데이터 | ✅ 구조 지원 | △ | 온톨로지 구조는 지원. 전체 미팅 데이터 로드 시 ✅ |
    | 4-2 | 이번 회의에서 우리 회사 기고 결과 요약은? | Source, TDoc Status | ✅ | ✅ | - |
    | 4-3 | 특정 Agenda Item에서 아직 미결(not treated)인 Tdoc은? | Agenda item, TDoc Status | ✅ | ✅ | - |
    
    ---
    
    ## 6. 검증 결과
    
    ### 6.1 발견된 문제와 해결
    
    | 문제 | 해당 CQ | 해결 방법 | 상태 |
    | --- | --- | --- | --- |
    | **Meeting 컬럼 없음** | 1-1, 1-2, 1-3, 1-5 | Meeting 클래스 추가 (Step 4). 파일명에서 회의 정보 추출 | ✅ 해결 |
    | **여러 회의 데이터 필요** | 4-1 | 온톨로지 구조는 지원. 전체 미팅 데이터 로드 시 답변 가능 | △ 구조 지원 |
    
    ### 6.2 결론
    
    모든 CQ에 대해 데이터 소스가 확인됨. CQ 4-1만 여러 회의 데이터 로드가 필요하며, 온톨로지 구조는 지원한다.
    
    ---
    
    ## Step 2: 기존 Ontology 재사용 검토
    
    > Ontology 101 원칙
    > 
    > 
    > *"It is almost always worth considering what someone else has done and checking if we can refine and extend existing sources for our particular domain and task. Reusing existing ontologies may be a requirement if our system needs to interact with other applications that have already committed to particular ontologies or controlled vocabularies."*
    > 
    > — Noy & McGuinness, Ontology Development 101
    > 
    
    ---
    
    ## 1. 검토 결과
    
    | 검토 대상 | 결과 |
    | --- | --- |
    | 3GPP Tdoc 전용 Ontology | ❌ 없음 |
    | 통신 표준 문서 Ontology | ❌ 없음 |
    
    **→ 3GPP 특화 Ontology는 직접 설계해야 함**
    
    ---
    
    ## 2. 재사용 가능한 기존 Ontology
    
    | Ontology | 정의 | 우리 용도 |
    | --- | --- | --- |
    | **Dublin Core (DC)** | 문서 메타데이터 표준 (제목, 작성자, 날짜 등 15개 요소) | Tdoc 기본 속성 |
    | **FOAF** | 사람/조직 표현 표준 | Company, Contact |
    | **SKOS** | 계층적 분류 체계 표현 표준 (상위-하위 관계) | Agenda Item 계층 (참고) |
    
    ---
    
    ## 3. 재사용 매핑
    
    | 우리 개념 | 기존 Ontology | 매핑 |
    | --- | --- | --- |
    | Tdoc 제목 | Dublin Core | dc:title |
    | Tdoc 번호 | Dublin Core | dc:identifier |
    | Tdoc 유형 | Dublin Core | dc:type |
    | Tdoc 날짜 | Dublin Core | dc:date |
    | Company | FOAF | foaf:Organization |
    | Contact | FOAF | foaf:Person |
    | Agenda 계층 | SKOS | skos:broader, skos:narrower (참고) |
    
    ---
    
    ## 4. 직접 정의해야 할 것 (3GPP 특화)
    
    | 개념 | 데이터 소스 (Tdoc_list 컬럼) |
    | --- | --- |
    | Tdoc | TDoc, Title, Abstract |
    | Meeting | 파일명/TDoc 번호에서 추출 |
    | Work Item | Related WIs |
    | Agenda Item | Agenda item, Agenda item description |
    | Release | Release |
    | Spec (TS/TR) | Spec, Version |
    | Company | Source |
    | Contact | Contact, Contact ID |
    | LS 관계 | Reply to, To, Cc, Original LS, Reply in |
    | Revision 관계 | Is revision of, Revised to |
    | CR 관련 | CR, CR category, Clauses Affected |
    | TDoc Status | TDoc Status |
    | For (목적) | For |
    | Type | Type |
    
    ---
    
    ## 5. 결론
    
    | 구분 | 내용 |
    | --- | --- |
    | **재사용** | Dublin Core, FOAF, SKOS 개념 참조 |
    | **신규 정의** | 3GPP 특화 클래스 및 관계 |
    | **데이터 소스** | 모두 Tdoc_list 메타데이터로 커버 가능 ✅ |
    
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
    
    - 도메인에서 나오는 **명사, 동사를 전부 나열**
    - 아직 **클래스/속성 구분 없이** 후보 용어로 정리
    - Tdoc_list로 **실제로 채울 수 있는지** 검증
    
    ---
    
    ## 2. 데이터 소스
    
    | 항목 | 내용 |
    | --- | --- |
    | 파일 | Tdoc_list Excel ([P1-V02] 참조) |
    | 범위 | [P1-V05] |
    
    ---
    
    ## 3. 용어 나열
    
    ### 3.1 클래스 후보
    
    | 용어 | 데이터 소스 | 채울 수 있나? | 비고 |
    | --- | --- | --- | --- |
    | Tdoc | TDoc 컬럼 | ✅ | 상위 클래스 |
    | CR | Type 컬럼 (CR, draftCR, pCR) | ✅ | Tdoc 하위 클래스 |
    | LS | Type 컬럼 (LS in, LS out) | ✅ | Tdoc 하위 클래스 |
    | Meeting | 파일명에서 추출 | ✅ | [P1-V02] 참조 |
    | Company | Source 컬럼 | ✅ | 파싱/정규화 필요 |
    | Contact | Contact 컬럼 | ✅ |  |
    | WorkItem | Related WIs 컬럼 | ✅ | 파싱 필요 |
    | AgendaItem | Agenda item 컬럼 | ✅ |  |
    | Release | Release 컬럼 | ✅ |  |
    | Spec | Spec 컬럼 | ✅ |  |
    | WorkingGroup | To, Cc에서 추출 | ✅ | 파싱 필요 |
    
    ### 3.2 Object Property 후보
    
    | 용어 | 데이터 소스 | 설명 | 채울 수 있나? |
    | --- | --- | --- | --- |
    | submittedBy | Source | Tdoc → Company | ✅ |
    | hasContact | Contact | Tdoc → Contact | ✅ |
    | relatedTo | Related WIs | Tdoc → WorkItem (다대다) | ✅ |
    | belongsTo | Agenda item | Tdoc → AgendaItem | ✅ |
    | targetRelease | Release | Tdoc → Release | ✅ |
    | modifies | Spec | CR → Spec | ✅ |
    | presentedAt | 파일명 | Tdoc → Meeting | ✅ |
    | isRevisionOf | Is revision of | Tdoc → Tdoc | ✅ |
    | revisedTo | Revised to | Tdoc → Tdoc | ✅ |
    | replyTo | Reply to | Tdoc → Tdoc | ✅ |
    | originalLS | Original LS | LS → Tdoc | ✅ |
    | replyIn | Reply in | Tdoc → Tdoc | ✅ |
    | sentTo | To | LS → WorkingGroup (다대다) | ✅ |
    | ccTo | Cc | LS → WorkingGroup (다대다) | ✅ |
    | originatedFrom | Original LS에서 추출 | Original LS에서 추출 | ✅ |
    
    ### 3.3 Data Property 후보
    
    | 용어 | 데이터 소스 | 대상 클래스 | 채울 수 있나? |
    | --- | --- | --- | --- |
    | tdocNumber | TDoc | Tdoc | ✅ |
    | title | Title | Tdoc | ✅ |
    | abstract | Abstract | Tdoc | ✅ |
    | type | Type | Tdoc | ✅ |
    | status | TDoc Status | Tdoc | ✅ |
    | for | For | Tdoc | ✅ |
    | reservationDate | Reservation date | Tdoc | ✅ |
    | uploadedDate | Uploaded | Tdoc | ✅ |
    | secretaryRemarks | Secretary Remarks | Tdoc | ✅ |
    | contactId | Contact ID | Contact | ✅ |
    | contactName | Contact | Contact | ✅ |
    | agendaNumber | Agenda item | AgendaItem | ✅ |
    | agendaDescription | Agenda item description | AgendaItem | ✅ |
    | specNumber | Spec | Spec | ✅ |
    | specVersion | Version | Spec | ✅ |
    | crNumber | CR | CR | ✅ |
    | crCategory | CR category | CR | ✅ |
    | clausesAffected | Clauses Affected | CR | ✅ |
    | tsgCRPack | TSG CR Pack | CR | ✅ |
    | crRevision | CR revision | CR | ✅ |
    | direction | Type에서 추출 | LS | ✅ |
    | specTitle | (외부 데이터/동적 생성) | Spec | ✅ |
    
    ### 3.4 CR 영향 범위 속성
    
    | 용어 | 데이터 소스 | 대상 클래스 | 채울 수 있나? |
    | --- | --- | --- | --- |
    | affectsUICC | UICC | CR | ✅ |
    | affectsME | ME | CR | ✅ |
    | affectsRAN | RAN | CR | ✅ |
    | affectsCN | CN | CR | ✅ |
    
    ### 3.5 Meeting 속성
    
    | 용어 | 데이터 소스 | 대상 클래스 | 채울 수 있나? |
    | --- | --- | --- | --- |
    | meetingNumber | 파일명 | Meeting | ✅ |
    | canonicalMeetingNumber | meetingNumber에서 정규화 | Meeting | ✅ |
    | meetingNumberInt | canonicalMeetingNumber에서 추출 | Meeting | ✅ |
    | workingGroup | 파일명 | Meeting | ✅ |
    
    ### 3.6 기타 클래스 속성
    
    | 용어 | 데이터 소스 | 대상 클래스 | 채울 수 있나? |
    | --- | --- | --- | --- |
    | companyName | Source 파싱 | Company | ✅ |
    | workItemCode | Related WIs 파싱 | WorkItem | ✅ |
    | releaseName | Release | Release | ✅ |
    | wgName | To, Cc 파싱 | WorkingGroup | ✅ |
    
    ---
    
    ## 4. 제외 항목
    
    | 컬럼 | 제외 이유 |
    | --- | --- |
    | Agenda item sort order | 정렬용, Ontology 불필요 |
    | TDoc sort order within agenda item | 정렬용, Ontology 불필요 |
    
    ---
    
    ## 5. 파싱 필요 항목
    
    | 컬럼 | 이유 | 예시 |
    | --- | --- | --- |
    | Source | 복합 값 | "Samsung, Huawei" → 2개 Company |
    | Related WIs | 복합 값 | "NR_MIMO_Ph5-Core, NR_duplex" → 2개 WorkItem |
    | To | 복합 값 | "RAN1, RAN4" → 2개 WorkingGroup |
    | Cc | 복합 값 | "RAN, RAN1, SA2" → 3개 WorkingGroup |
    
    ---
    
    ## Step 4: 클래스와 계층 구조 정의
    
    > Ontology 101 원칙
    > 
    > 
    > *"Define the classes and the class hierarchy... A class can have subclasses that represent concepts that are more specific than the superclass."*
    > 
    > *"Subclasses of a class usually (1) have additional properties that the superclass does not have, or (2) restrictions different from those of the superclass, or (3) participate in different relationships than the superclasses"*
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
    
    ## 3. 클래스 확정
    
    | 클래스 | 설명 |
    | --- | --- |
    | **Tdoc** | 3GPP 회의 문서 |
    | **CR** | Change Request (Tdoc 하위) |
    | **LS** | Liaison Statement (Tdoc 하위) |
    | **Meeting** | 3GPP 회의 |
    | **Company** | 기고 회사/조직 |
    | **Contact** | 담당자 |
    | **WorkItem** | 작업 항목 |
    | **AgendaItem** | 회의 안건 |
    | **Release** | 3GPP 릴리즈 |
    | **Spec** | 기술 규격 (TS/TR) |
    | **WorkingGroup** | 3GPP 작업 그룹 |
    
    ---
    
    ## 4. 클래스 계층 구조
    
    ```
    Tdoc
    ├── CR
    └── LS
    
    Meeting
    Company
    Contact
    WorkItem
    AgendaItem
    Release
    Spec
    WorkingGroup
    
    ```
    
    ---
    
    ## 5. 하위 클래스 판단 근거
    
    ### 5.1 CR (Change Request)
    
    | 기준 | 충족 여부 | 내용 |
    | --- | --- | --- |
    | 추가 속성 | ✅ | crNumber, crCategory, clausesAffected, tsgCRPack, crRevision, affectsUICC, affectsME, affectsRAN, affectsCN |
    | 다른 관계 | ✅ | modifies → Spec |
    | 해당 Type | - | 'CR', 'draftCR', 'pCR' |
    
    ### 5.2 LS (Liaison Statement)
    
    | 기준 | 충족 여부 | 내용 |
    | --- | --- | --- |
    | 추가 속성 | ✅ | direction ('in' / 'out') |
    | 다른 관계 | ✅ | sentTo → WorkingGroup, ccTo → WorkingGroup, originalLS → Tdoc |
    | 해당 Type | - | 'LS out', 'LS in' |
    
    ---
    
    ## 6. Type별 클래스 매핑
    
    | Type 값 | 클래스 | 구분 속성 |
    | --- | --- | --- |
    | CR | CR | - |
    | draftCR | CR | crNumber가 null |
    | pCR | CR | crNumber가 null |
    | LS out | LS | direction = 'out' |
    | LS in | LS | direction = 'in' |
    | discussion | Tdoc | type = 'discussion' |
    | other | Tdoc | type = 'other' |
    | report | Tdoc | type = 'report' |
    | agenda | Tdoc | type = 'agenda' |
    | Work Plan | Tdoc | type = 'Work Plan' |
    | draft TR | Tdoc | type = 'draft TR' |
    | draft TS | Tdoc | type = 'draft TS' |
    | response | Tdoc | type = 'response' |
    | WID new | Tdoc | type = 'WID new' |
    | SID new | Tdoc | type = 'SID new' |
    | WI summary | Tdoc | type = 'WI summary' |
    
    ---
    
    ## 7. 클래스별 인스턴스 분포
    
    총 Tdoc 수는 [P1-V01] 참조.
    
    | 클래스 | 분류 기준 |
    | --- | --- |
    | Tdoc (직접) | Type이 discussion, other 등 |
    | CR | Type이 CR, draftCR, pCR |
    | LS | Type이 LS out, LS in |
    
    ---
    
    ## 8. 클래스로 정의하지 않은 용어
    
    | 용어 | 이유 | 처리 |
    | --- | --- | --- |
    | tdocNumber, title, status 등 | 속성값 | Step 5 Data Property |
    | submittedBy, relatedTo 등 | 관계 | Step 5 Object Property |
    | draftCR, pCR | CR과 동일 구조 | type 속성으로 구분 |
    
    ---
    
    ## Step 5: 속성(Slot) 정의
    
    > Ontology 101 원칙
    > 
    > 
    > *"Define the properties of classes—slots... Properties describe attributes of instances of a class and relations to other instances."*
    > 
    > *"A slot should be attached at the most general class that can have that property."*
    > 
    > — Noy & McGuinness, Ontology Development 101
    > 
    
    ---
    
    ## 1. Step 5 목적
    
    - Step 4에서 정의한 클래스의 **속성(Slot)** 정의
    - **Data Property**: 클래스 인스턴스의 값 (String, Integer, Boolean 등)
    - **Object Property**: 클래스 인스턴스 간의 관계
    - 각 속성의 **의미와 용도**를 명확히 기술
    - 제약조건(Cardinality 등)은 Step 6에서 정의
    
    ---
    
    ## 2. 속성의 종류
    
    | 종류 | 설명 | 예시 |
    | --- | --- | --- |
    | **Data Property** | 객체의 속성값 | tdocNumber, title, status |
    | **Object Property** | 다른 객체와의 관계 | submittedBy, relatedTo |
    
    ---
    
    ## 3. Tdoc 클래스 속성
    
    ### 3.1 Object Property
    
    | 속성명 | Range | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | submittedBy | Company | Source | Tdoc을 제출한 회사/조직. 복수 회사가 공동 제출 가능 |
    | hasContact | Contact | Contact | Tdoc의 담당자 (연락 가능한 사람) |
    | relatedTo | WorkItem | Related WIs | Tdoc이 관련된 Work Item. 하나의 Tdoc이 여러 WI에 관련될 수 있음 |
    | belongsTo | AgendaItem | Agenda item | Tdoc이 논의되는 Agenda Item |
    | targetRelease | Release | Release | Tdoc이 대상으로 하는 3GPP Release 버전 |
    | presentedAt | Meeting | 파일명 | Tdoc이 발표/논의된 3GPP 회의 |
    | isRevisionOf | Tdoc | Is revision of | 이 Tdoc이 수정한 이전 버전 Tdoc |
    | revisedTo | Tdoc | Revised to | 이 Tdoc을 수정한 이후 버전 Tdoc. 복수 가능 (분기 revision). isRevisionOf의 역관계 |
    | replyTo | Tdoc | Reply to | 이 Tdoc이 답변하는 대상 Tdoc. 복수 가능. 주로 LS에 대한 답변 |
    | replyIn | Tdoc | Reply in | 이 Tdoc에 대한 답변 Tdoc (replyTo의 역관계) |
    
    ### 3.2 Data Property
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | tdocNumber | String | TDoc | Tdoc의 고유 식별자 (예: R1-2500001). 형식: R1-YYNNNNN |
    | title | String | Title | Tdoc의 제목. 문서 내용을 요약하는 짧은 설명 |
    | abstract | String | Abstract | Tdoc의 요약. 문서 내용의 상세 설명 (대부분 비어있음) |
    | type | String (Enum) | Type | Tdoc의 유형 |
    | status | String (Enum) | TDoc Status | 회의에서의 결정 결과 |
    | for | String (Enum) | For | Tdoc의 목적/용도 |
    | reservationDate | DateTime | Reservation date | Tdoc 번호 예약 일시 |
    | uploadedDate | DateTime | Uploaded | Tdoc 파일 업로드 일시 |
    | secretaryRemarks | String | Secretary Remarks | 회의 비서의 메모 (예: "Late contribution", "Revised in session") |
    
    ---
    
    ## 4. CR 클래스 속성 (Tdoc 상속 + 추가)
    
    ### 4.1 추가 Object Property
    
    | 속성명 | Range | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | modifies | Spec | Spec | CR이 변경을 요청하는 대상 기술 규격 (예: 38.212) |
    
    ### 4.2 추가 Data Property
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | crNumber | String | CR | CR의 공식 번호 (예: 0693). draftCR은 이 값이 없음 |
    | crCategory | String (Enum) | CR category | CR의 카테고리 |
    | clausesAffected | String | Clauses Affected | CR로 인해 영향받는 규격의 조항 번호 (예: "5.3.1, 5.3.2") |
    | tsgCRPack | String | TSG CR Pack | TSG에 제출되는 CR Pack 번호 (예: RP-250233) |
    | crRevision | String | CR revision | CR의 수정 횟수 (1~9). 일부 CR만 보유 |
    | affectsUICC | Boolean | UICC | CR이 UICC(Universal Integrated Circuit Card)에 영향을 미치는지 여부 |
    | affectsME | Boolean | ME | CR이 ME(Mobile Equipment)에 영향을 미치는지 여부 |
    | affectsRAN | Boolean | RAN | CR이 RAN(Radio Access Network)에 영향을 미치는지 여부 |
    | affectsCN | Boolean | CN | CR이 CN(Core Network)에 영향을 미치는지 여부 |
    
    ---
    
    ## 5. LS 클래스 속성 (Tdoc 상속 + 추가)
    
    ### 5.1 추가 Object Property
    
    | 속성명 | Range | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | sentTo | WorkingGroup | To | LS의 수신 대상 Working Group (예: RAN1, RAN4). 복수 가능 |
    | ccTo | WorkingGroup | Cc | LS의 참조 대상 Working Group. 복수 가능 |
    | originalLS | Tdoc | Original LS | LS in의 경우, 다른 WG에서 보낸 원본 LS 문서 번호 |
    | originatedFrom | WorkingGroup | Original LS에서 WG 추출 | LS in의 발신 Working Group. Original LS 번호의 prefix에서 추출 (예: S2-xxx → SA2) |
    
    ### 5.2 추가 Data Property
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | direction | String (Enum) | Type에서 추출 | LS의 방향. in(수신), out(발신) |
    
    ---
    
    ## 6. 기타 클래스 속성
    
    ### 6.1 Meeting
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | meetingNumber | String | 파일명 | 회의 번호 원본 (예: RAN1#120, RAN1#101-e) |
    | canonicalMeetingNumber | String | meetingNumber에서 정규화 | 정규화된 회의 번호. `-e` suffix 제거 |
    | meetingNumberInt | Integer | canonicalMeetingNumber에서 추출 | 정렬용 숫자값. CQ 결과 정렬에 사용 |
    | workingGroup | String | 파일명 | 회의를 주관하는 Working Group (예: RAN1) |
    
    **Meeting ID 정규화 규칙:**
    
    | 원본 | canonicalMeetingNumber | meetingNumberInt | 설명 |
    | --- | --- | --- | --- |
    | RAN1#101-e | RAN1#101 | 101 | e-meeting suffix 제거 |
    | RAN1#112bis-e | RAN1#112bis | 112 | e-meeting suffix만 제거, bis 유지 |
    | RAN1#120 | RAN1#120 | 120 | 변경 없음 |
    
    ### 6.2 Company
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | companyName | String | Source 파싱 | 회사/조직의 정규화된 대표 이름 (예: Samsung, Huawei, Ericsson) |
    | aliases | List<String> | company_aliases.json | 회사의 다른 이름/변형 목록 (예: ["Samsung Electronics", "SEC"]). 정규화 사전에서 추출 |
    
    ### 6.3 Contact
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | contactName | String | Contact | 담당자의 이름 (예: Patrick Merias) |
    | contactId | String | Contact ID | 3GPP 시스템에서의 담당자 고유 ID (예: 52292) |
    
    ### 6.4 WorkItem
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | workItemCode | String | Related WIs 파싱 | Work Item의 코드명 (예: NR_MIMO_Ph5-Core) |
    
    ### 6.5 AgendaItem
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | agendaNumber | String | Agenda item | Agenda Item의 번호 (예: 9.1, 9.1.1). 계층 구조를 가짐 |
    | agendaDescription | String | Agenda item description | Agenda Item의 설명 (예: "AI/ML for NR Air Interface") |
    
    ### 6.6 Release
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | releaseName | String | Release | 3GPP Release 버전명 (예: Rel-18, Rel-19) |
    
    ### 6.7 Spec
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | specNumber | String | Spec | 기술 규격 번호 (예: 38.212, 38.214) |
    | specVersion | String | Version | 규격의 버전 (예: 18.5.0) |
    | specTitle | String | (외부 데이터/동적 생성) | 기술 규격 제목 (예: "Physical channels and modulation") |
    
    ### 6.8 WorkingGroup
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | wgName | String | To, Cc 파싱 | Working Group 이름 (예: RAN1, RAN2, SA2) |
    
    ---
    
    ## 7. 전체 Object Property 목록
    
    | # | 속성명 | Domain | Range | 설명 |
    | --- | --- | --- | --- | --- |
    | 1 | submittedBy | Tdoc | Company | Tdoc을 제출한 회사 |
    | 2 | hasContact | Tdoc | Contact | Tdoc의 담당자 |
    | 3 | relatedTo | Tdoc | WorkItem | Tdoc이 관련된 Work Item |
    | 4 | belongsTo | Tdoc | AgendaItem | Tdoc이 속한 Agenda Item |
    | 5 | targetRelease | Tdoc | Release | Tdoc의 대상 Release |
    | 6 | presentedAt | Tdoc | Meeting | Tdoc이 발표된 회의 |
    | 7 | isRevisionOf | Tdoc | Tdoc | 이전 버전 Tdoc |
    | 8 | revisedTo | Tdoc | Tdoc | 이후 버전 Tdoc |
    | 9 | replyTo | Tdoc | Tdoc | 답변 대상 Tdoc |
    | 10 | replyIn | Tdoc | Tdoc | 답변 Tdoc |
    | 11 | modifies | CR | Spec | CR이 수정하는 Spec |
    | 12 | sentTo | LS | WorkingGroup | LS 수신처 |
    | 13 | ccTo | LS | WorkingGroup | LS 참조처 |
    | 14 | originalLS | LS | Tdoc | 원본 LS |
    | 15 | originatedFrom | LS | WorkingGroup | LS 발신 WG |
    
    ---
    
    ## 8. 전체 Data Property 목록
    
    | # | 속성명 | Domain | Type | 설명 |
    | --- | --- | --- | --- | --- |
    | 1 | tdocNumber | Tdoc | String | Tdoc 고유 식별자 |
    | 2 | title | Tdoc | String | Tdoc 제목 |
    | 3 | abstract | Tdoc | String | Tdoc 요약 |
    | 4 | type | Tdoc | String (Enum) | Tdoc 유형 |
    | 5 | status | Tdoc | String (Enum) | 결정 결과 |
    | 6 | for | Tdoc | String (Enum) | 목적 |
    | 7 | reservationDate | Tdoc | DateTime | 예약 일시 |
    | 8 | uploadedDate | Tdoc | DateTime | 업로드 일시 |
    | 9 | secretaryRemarks | Tdoc | String | 비서 메모 |
    | 10 | crNumber | CR | String | CR 번호 |
    | 11 | crCategory | CR | String (Enum) | CR 카테고리 |
    | 12 | clausesAffected | CR | String | 영향받는 조항 |
    | 13 | tsgCRPack | CR | String | TSG CR Pack |
    | 14 | crRevision | CR | String | CR 수정 횟수 |
    | 15 | affectsUICC | CR | Boolean | UICC 영향 |
    | 16 | affectsME | CR | Boolean | ME 영향 |
    | 17 | affectsRAN | CR | Boolean | RAN 영향 |
    | 18 | affectsCN | CR | Boolean | CN 영향 |
    | 19 | direction | LS | String (Enum) | LS 방향 |
    | 20 | meetingNumber | Meeting | String | 회의 번호 원본 |
    | 21 | canonicalMeetingNumber | Meeting | String | 정규화된 회의 번호 |
    | 22 | meetingNumberInt | Meeting | Integer | 정렬용 숫자값 |
    | 23 | workingGroup | Meeting | String | 주관 WG |
    | 24 | companyName | Company | String | 회사명 |
    | 25 | contactName | Contact | String | 담당자 이름 |
    | 26 | contactId | Contact | String | 담당자 ID |
    | 27 | workItemCode | WorkItem | String | Work Item 코드 |
    | 28 | agendaNumber | AgendaItem | String | Agenda 번호 |
    | 29 | agendaDescription | AgendaItem | String | Agenda 설명 |
    | 30 | releaseName | Release | String | Release 버전명 |
    | 31 | specNumber | Spec | String | Spec 번호 |
    | 32 | specVersion | Spec | String | Spec 버전 |
    | 33 | specTitle | Spec | String | Spec 제목 |
    | 34 | wgName | WorkingGroup | String | WG 이름 |
    | 35 | aliases | Company | List<String> | 회사 별칭 목록 |
    
    ---
    
    ## 9. Inverse Property (역관계)
    
    | 속성 | 역속성 | 설명 |
    | --- | --- | --- |
    | isRevisionOf | revisedTo | A가 B의 revision이면, B는 A로 revised됨 |
    | replyTo | replyIn | A가 B에 대한 답변이면, B는 A에서 답변됨 |
    
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
    - **Enumeration**: 허용되는 값 목록
    
    ---
    
    ## 2. Facet 종류
    
    | Facet | 설명 | 예시 |
    | --- | --- | --- |
    | **Cardinality** | 속성값 개수 | 0..1, 1, 0..*, 1..* |
    | **Required** | 필수 여부 | ✅ / ❌ |
    | **Functional** | 단일값만 허용 | ✅ (최대 1개) |
    | **Inverse** | 역관계 | isRevisionOf ↔ revisedTo |
    
    ### Cardinality 표기법
    
    | 표기 | 의미 | Required | Functional |
    | --- | --- | --- | --- |
    | 1 | 정확히 1개 | ✅ | ✅ |
    | 0..1 | 0개 또는 1개 | ❌ | ✅ |
    | 1..* | 1개 이상 | ✅ | ❌ |
    | 0..* | 0개 이상 | ❌ | ❌ |
    
    ---
    
    ## 3. Tdoc 클래스 속성 제약조건
    
    ### 3.1 Object Property
    
    | 속성명 | Domain | Range | Cardinality | 필수 | 근거 |
    | --- | --- | --- | --- | --- | --- |
    | submittedBy | Tdoc | Company | 0..* | ❌ | Source 누락 [P1-V03]. 전 기간 분산, 데이터 소스 자체 누락. |
    | hasContact | Tdoc | Contact | 1 | ✅ | 모든 Tdoc에 Contact 존재. 담당자는 1명 |
    | relatedTo | Tdoc | WorkItem | 0..* | ❌ | 일부 Tdoc은 Related WIs 없음. 복수 WI 관련 가능 |
    | belongsTo | Tdoc | AgendaItem | 1 | ✅ | 모든 Tdoc에 Agenda item 존재 |
    | targetRelease | Tdoc | Release | 0..1 | ❌ | 일부 Tdoc은 Release 없음. 하나의 Release만 대상 |
    | presentedAt | Tdoc | Meeting | 1 | ✅ | 모든 Tdoc은 특정 회의에 속함 |
    | isRevisionOf | Tdoc | Tdoc | 0..1 | ❌ | 최초 버전은 없음 |
    | revisedTo | Tdoc | Tdoc | 0..* | ❌ | 하나의 TDoc이 여러 버전으로 분기 가능 |
    | replyTo | Tdoc | Tdoc | 0..* | ❌ | 하나의 TDoc이 여러 문서에 답변 가능 |
    | replyIn | Tdoc | Tdoc | 0..* | ❌ | 복수 WG 답변 가능 |
    
    ---
    
    ### 3.2 Data Property
    
    | 속성명 | Domain | Type | Cardinality | 필수 | 근거 |
    | --- | --- | --- | --- | --- | --- |
    | tdocNumber | Tdoc | String | 1 | ✅ | 모든 Tdoc의 고유 식별자 |
    | title | Tdoc | String | 1 | ✅ | 모든 Tdoc에 제목 존재 |
    | abstract | Tdoc | String | 0..1 | ❌ | 대부분 비어있음 |
    | type | Tdoc | String (Enum) | 1 | ✅ | 모든 Tdoc에 유형 존재 |
    | status | Tdoc | String (Enum) | 1 | ✅ | 모든 Tdoc에 상태 존재 |
    | for | Tdoc | String (Enum) | 0..1 | ❌ | 일부 Tdoc은 For 없음 (주로 LS) |
    | reservationDate | Tdoc | DateTime | 1 | ✅ | 모든 Tdoc에 예약일 존재 |
    | uploadedDate | Tdoc | DateTime | 0..1 | ❌ | 미업로드 문서는 없음 |
    | secretaryRemarks | Tdoc | String | 0..1 | ❌ | 일부만 비서 메모 존재 |
    
    ---
    
    ## 4. CR 클래스 추가 속성 제약조건
    
    ### 4.1 Object Property
    
    | 속성명 | Domain | Range | Cardinality | 필수 | 근거 |
    | --- | --- | --- | --- | --- | --- |
    | modifies | CR | Spec | 0..* | ✅ | 모든 RAN1 CR/draftCR에 Spec 존재(관측상 단일). 모델상 한 CR이 복수 Spec 병기 가능 (ontology tdoc:modifies 다중값) |
    
    ### 4.2 Data Property
    
    | 속성명 | Domain | Type | Cardinality | 필수 | 근거 |
    | --- | --- | --- | --- | --- | --- |
    | crNumber | CR | String | 0..1 | ❌ | draftCR은 CR 번호 미부여 |
    | crCategory | CR | String (Enum) | 0..1 | ❌ | 일부 CR은 카테고리 미지정 |
    | clausesAffected | CR | String | 0..1 | ❌ | 일부만 영향 조항 명시 |
    | tsgCRPack | CR | String | 0..1 | ❌ | 승인된 CR만 존재 |
    | crRevision | CR  | String |  0..1 | ❌ | 일부 CR만 revision 번호 보유 |
    | affectsUICC | CR | Boolean | 0..1 | ❌ | 일부만 명시 |
    | affectsME | CR | Boolean | 0..1 | ❌ | 일부만 명시 |
    | affectsRAN | CR | Boolean | 0..1 | ❌ | 일부만 명시 |
    | affectsCN | CR | Boolean | 0..1 | ❌ | 일부만 명시 |
    
    ---
    
    ## 5. LS 클래스 추가 속성 제약조건
    
    ### 5.1 Object Property
    
    | 속성명 | Domain | Range | Cardinality | 필수 | 근거 |
    | --- | --- | --- | --- | --- | --- |
    | sentTo | LS | WorkingGroup | 0..* | ❌ | 누락 [P1-V04]. 수신처 없이 발신된 케이스 존재. |
    | ccTo | LS | WorkingGroup | 0..* | ❌ | 참조는 선택사항 |
    | originalLS | LS | Tdoc | 0..1 | ❌ | LS in만 존재. LS out은 원본 LS 없음 |
    | originatedFrom | LS | WorkingGroup | 0..1 | ❌ | LS in만 존재. Original LS 번호에서 WG 추출 |
    
    ---
    
    ### 5.2 Data Property
    
    | 속성명 | Domain | Type | Cardinality | 필수 | 근거 |
    | --- | --- | --- | --- | --- | --- |
    | direction | LS | String (Enum) | 1 | ✅ | 모든 LS는 방향 있음. Type에서 추출 (in 또는 out) |
    
    ---
    
    ## 6. 기타 클래스 속성 제약조건
    
    ### 6.1 Meeting
    
    | 속성명 | Domain | Type | Cardinality | 필수 | 설명 |
    | --- | --- | --- | --- | --- | --- |
    | meetingNumber | Meeting | String | 1 | ✅ | 회의 번호 원본 |
    | canonicalMeetingNumber | Meeting | String | 1 | ✅ | 정규화된 회의 번호 (자동 생성) |
    | meetingNumberInt | Meeting | Integer | 1 | ✅ | 정렬용 숫자값 (자동 생성) |
    | workingGroup | Meeting | String | 1 | ✅ | 주관 Working Group |
    
    ### 6.2 Company
    
    | 속성명 | Domain | Type | Cardinality | 필수 | 설명 |
    | --- | --- | --- | --- | --- | --- |
    | companyName | Company | String | 1 | ✅ | 회사/조직의 고유 이름 |
    | aliases | Company | List<String> | 0..* | ❌ | 회사의 다른 이름/변형 목록. company_aliases.json에서 추출 |
    
    ### 6.3 Contact
    
    | 속성명 | Domain | Type | Cardinality | 필수 | 설명 |
    | --- | --- | --- | --- | --- | --- |
    | contactName | Contact | String | 1 | ✅ | 담당자의 이름 |
    | contactId | Contact | String | 1 | ✅ | 3GPP 시스템의 담당자 고유 ID |
    
    ### 6.4 WorkItem
    
    | 속성명 | Domain | Type | Cardinality | 필수 | 설명 |
    | --- | --- | --- | --- | --- | --- |
    | workItemCode | WorkItem | String | 1 | ✅ | Work Item의 고유 코드명 |
    
    ### 6.5 AgendaItem
    
    | 속성명 | Domain | Type | Cardinality | 필수 | 설명 |
    | --- | --- | --- | --- | --- | --- |
    | agendaNumber | AgendaItem | String | 1 | ✅ | Agenda 번호 (계층 구조) |
    | agendaDescription | AgendaItem | String | 1 | ✅ | Agenda 설명/제목 |
    
    ### 6.6 Release
    
    | 속성명 | Domain | Type | Cardinality | 필수 | 설명 |
    | --- | --- | --- | --- | --- | --- |
    | releaseName | Release | String | 1 | ✅ | Release 버전명 |
    
    ### 6.7 Spec
    
    | 속성명 | Domain | Type | Cardinality | 필수 | 설명 |
    | --- | --- | --- | --- | --- | --- |
    | specNumber | Spec | String | 1 | ✅ | 기술 규격 번호 (예: 38.212, 38.214) |
    | specVersion | Spec | String | 0..1 | ❌ | 규격의 버전 (예: 18.5.0). CR마다 다를 수 있으므로 Spec 인스턴스에는 대표값 |
    | specTitle | Spec | String | 0..1 | ❌ | 기술 규격 제목 (예: "Physical channels and modulation"). 외부 데이터/동적 생성 |
    
    ### 6.8 WorkingGroup
    
    | 속성명 | Domain | Type | Cardinality | 필수 | 설명 |
    | --- | --- | --- | --- | --- | --- |
    | wgName | WorkingGroup | String | 1 | ✅ | Working Group 고유 이름 |
    
    ---
    
    ## 7. Inverse Property (역관계)
    
    | 속성 | 역속성 | 설명 |
    | --- | --- | --- |
    | isRevisionOf | revisedTo | A가 B의 revision이면, B는 A로 revised됨 |
    | replyTo | replyIn | A가 B에 대한 답변이면, B는 A에서 답변됨 |
    
    ---
    
    ## 8. Enumeration (열거형)
    
    ### 8.1 type (Tdoc 유형)
    
    | 값 | 설명 |
    | --- | --- |
    | discussion | 일반 기술 제안/논의 문서 |
    | other | 기타 문서 |
    | draftCR | Change Request 초안 |
    | LS out | 발신 Liaison Statement |
    | CR | 공식 Change Request |
    | LS in | 수신 Liaison Statement |
    | draft TR | Technical Report 초안 |
    | report | 보고서 |
    | agenda | 회의 안건표 |
    | draft TS | Technical Specification 초안 |
    | Work Plan | 작업 계획 |
    | pCR | Proposed CR |
    | response | 응답 문서 |
    | WID new | 새 Work Item Description |
    | SID new | 새 Study Item Description |
    | WI summary | Work Item 요약 |
    
    ### 8.2 status (결정 상태)
    
    | 값 | 설명 |
    | --- | --- |
    | not treated | 회의에서 다루지 않음 |
    | available | 접수됨 (회의 전 상태) |
    | noted | 참고로 접수됨 |
    | revised | 수정되어 새 버전으로 대체됨 |
    | agreed | 합의됨 |
    | withdrawn | 제출자가 철회함 |
    | not pursued | 더 이상 추진하지 않음 |
    | endorsed | 지지/승인됨 |
    | approved | 공식 승인됨 |
    | treated | 처리됨 |
    | postponed | 다음 회의로 연기됨 |
    | reserved | 예약됨 (번호만 할당) |
    | merged | 다른 문서와 병합됨 |
    | not concluded | 결론 미도출 |
    | conditionally agreed | 조건부 합의 |
    
    ### 8.3 for (문서 목적)
    
    | 값 | 설명 |
    | --- | --- |
    | Decision | 결정 요청 |
    | Discussion | 논의 요청 |
    | Agreement | 합의 요청 |
    | Approval | 승인 요청 |
    | Endorsement | 지지 요청 |
    | Information | 정보 공유 |
    | Presentation | 발표용 |
    | Action | 조치 요청 |
    
    ### 8.4 direction (LS 방향)
    
    | 값 | 설명 |
    | --- | --- |
    | out | 이 WG에서 다른 WG로 발신 |
    | in | 다른 WG에서 이 WG로 수신 |
    
    ### 8.5 crCategory (CR 카테고리)
    
    | 값 | 설명 |
    | --- | --- |
    | F | Correction (오류 수정) |
    | B | Addition of feature (기능 추가, 하위 호환) |
    | A | Mirror CR (다른 Release에 동일 적용) |
    | D | Editorial change (편집상 변경) |
    | C | Functional modification of feature (기능 수정) |
    | E | Early implementation (조기 구현) |
    
    ### 8.6 releaseName (Release 값)
    
    | 값 |
    | --- |
    | Rel-17 |
    | Rel-18 |
    | Rel-19 |
    | Rel-16 |
    | Rel-15 |
    | Rel-14 |
    | Rel-13 |
    | Rel-20 |
    | Rel-12 |
    | Rel-9 |
    | Rel-11 |
    | Rel-10 |
    | Rel-8 |
    
    ---
    
    ## 9. 필수 속성 요약
    
    ### 9.1 필수 Data Property
    
    | 클래스 | 필수 속성 |
    | --- | --- |
    | Tdoc | tdocNumber, title, type, status, reservationDate |
    | CR | (상속) |
    | LS | direction |
    | Meeting | meetingNumber, canonicalMeetingNumber, meetingNumberInt, workingGroup |
    | Company | companyName |
    | Contact | contactName, contactId |
    | WorkItem | workItemCode |
    | AgendaItem | agendaNumber, agendaDescription |
    | Release | releaseName |
    | Spec | specNumber |
    | WorkingGroup | wgName |
    
    ### 9.2 필수 Object Property
    
    | 클래스 | 필수 속성 |
    | --- | --- |
    | Tdoc | hasContact, belongsTo, presentedAt |
    | CR | modifies |
    
    *submittedBy는 Source 누락 [P1-V03]으로 비필수 (Section 3.1 참조). sentTo는 To 누락 [P1-V04]으로 비필수 (Section 5.1 참조).*
    
    ---
    
    ## 10. Functional Property 요약
    
    단일값만 허용하는 Object Property:
    
    | 속성 | Domain | Range | 설명 |
    | --- | --- | --- | --- |
    | hasContact | Tdoc | Contact | 담당자는 1명 |
    | belongsTo | Tdoc | AgendaItem | 하나의 Agenda에만 속함 |
    | targetRelease | Tdoc | Release | 하나의 Release만 대상 |
    | presentedAt | Tdoc | Meeting | 하나의 회의에만 발표 |
    | isRevisionOf | Tdoc | Tdoc | 이전 버전은 1개 |
    | originalLS | LS | Tdoc | 원본 LS는 1개 |
    | originatedFrom | LS | WorkingGroup | 발신 WG는 1개 |
    
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
    
    - Step 4~6에서 정의한 클래스, 속성, 제약조건을 바탕으로 **인스턴스 생성 규칙** 정의
    - **ID 생성 규칙**: 인스턴스 식별자 패턴
    - **데이터 소스 매핑**: Tdoc_list → 속성값
    - **예시 인스턴스**: 실제 데이터 기반 예시
    
    ---
    
    ## 2. 데이터 소스
    
    | 항목 | 내용 |
    | --- | --- |
    | 파일 | Tdoc_list Excel ([P1-V02] 참조) |
    | 범위 | [P1-V05] |
    
    ---
    
    ## 3. 인스턴스 현황
    
    | 클래스 | 소스 |
    | --- | --- |
    | Meeting | 파일명 |
    | Release | Release 컬럼 |
    | Company | Source 컬럼 (정규화 후) |
    | Contact | Contact, Contact ID 컬럼 |
    | WorkItem | Related WIs 컬럼 |
    | AgendaItem | Agenda item 컬럼 |
    | Spec | Spec 컬럼 |
    | WorkingGroup | To, Cc 컬럼 |
    | Tdoc (일반) | Type이 discussion, other 등 |
    | CR | Type이 CR, draftCR, pCR |
    | LS | Type이 LS out 또는 LS in |
    
    ---
    
    ## 4. 생성 순서
    
    인스턴스 간 참조 관계로 인해 순서가 중요합니다.
    
    | 순서 | 클래스 | 이유 |
    | --- | --- | --- |
    | 1 | Meeting, Release, Company, Contact, WorkItem, AgendaItem, Spec, WorkingGroup | 참조 대상 (의존성 없음) |
    | 2 | Tdoc, CR, LS | 위 클래스들을 참조 |
    
    ---
    
    ## 5. ID 생성 규칙
    
    ### 5.1 ID 생성 원칙
    
    | 원칙 | 설명 |
    | --- | --- |
    | 유일성 | 클래스 내에서 고유한 값 |
    | 불변성 | 한 번 생성되면 변경 불가 |
    | 의미성 | 도메인 의미 반영 |
    | 추적성 | 데이터 소스와 매핑 가능 |
    
    ### 5.2 클래스별 ID 패턴
    
    | 클래스 | ID 속성 | 패턴 | 예시 |
    | --- | --- | --- | --- |
    | Meeting | meetingNumber | `{WG}#{회차}[-e]` | RAN1#120, RAN1#101-e |
    | Release | releaseName | `Rel-{번호}` | Rel-18, Rel-19 |
    | Company | companyName | 정규화된 회사명 | Samsung, Huawei |
    | Contact | contactId | 3GPP 시스템 ID | 52292 |
    | WorkItem | workItemCode | Work Item 코드 | NR_MIMO_Ph5-Core |
    | AgendaItem | meetingNumber + agendaNumber | (복합키) | RAN1#120-9.1 |
    | Spec | specNumber | Spec 번호 | 38.212, 38.214 |
    | WorkingGroup | wgName | WG 이름 | RAN1, SA2 |
    | Tdoc, CR, LS | tdocNumber | `R1-{YYNNNNN}` | R1-2500001 |
    
    ---
    
    ## 6. 클래스별 인스턴스 생성 명세
    
    ### 6.1 Meeting
    
    | 항목 | 내용 |
    | --- | --- |
    | 소스 | 파일명 |
    | ID | meetingNumber 원본 값 |
    
    | 속성 | 소스 | 변환 규칙 | 예시 |
    | --- | --- | --- | --- |
    | meetingNumber | 파일명에서 추출 | 원본 그대로 | "RAN1#101-e" |
    | canonicalMeetingNumber | meetingNumber | `-e` suffix 제거 | "RAN1#101" |
    | meetingNumberInt | canonicalMeetingNumber | `#` 뒤 숫자만 추출 | 101 |
    | workingGroup | 파일명에서 추출 | `#` 앞부분 | "RAN1" |
    
    ### 6.2 Release
    
    | 항목 | 내용 |
    | --- | --- |
    | 소스 | Release 컬럼 (고유 값) |
    | ID | releaseName 값 |
    
    | 속성 | 소스 | 예시 |
    | --- | --- | --- |
    | releaseName | Release 컬럼 | "Rel-19" |
    
    **실제 값**: Rel-8, Rel-9, Rel-10, Rel-11, Rel-12, Rel-13, Rel-14, Rel-15, Rel-16, Rel-17, Rel-18, Rel-19, Rel-20
    
    ### 6.3 Company
    
    | 항목 | 내용 |
    | --- | --- |
    | 소스 | Source 컬럼 (쉼표 분리 후 고유 값) |
    | ID | companyName |
    
    | 속성 | 소스 | 예시 |
    | --- | --- | --- |
    | companyName | Source에서 추출/정규화 | "Samsung" |
    
    ### 6.4 Contact
    
    | 항목 | 내용 |
    | --- | --- |
    | 소스 | Contact, Contact ID 컬럼 |
    | ID | contactId 값 |
    
    | 속성 | 소스 | 예시 |
    | --- | --- | --- |
    | contactName | Contact 컬럼 | "Patrick Merias" |
    | contactId | Contact ID 컬럼 | "52292" |
    
    ### 6.5 WorkItem
    
    | 항목 | 내용 |
    | --- | --- |
    | 소스 | Related WIs 컬럼 (쉼표 분리 후 고유 값) |
    | ID | workItemCode |
    
    | 속성 | 소스 | 예시 |
    | --- | --- | --- |
    | workItemCode | Related WIs에서 추출 | "NR_MIMO_Ph5-Core" |
    
    ### 6.6 AgendaItem
    
    | 항목 | 내용 |
    | --- | --- |
    | 소스 | Agenda item, Agenda item description 컬럼 |
    | ID | meetingNumber + agendaNumber (복합키) |
    
    | 속성 | 소스 | 예시 |
    | --- | --- | --- |
    | agendaNumber | Agenda item 컬럼 | "9.1" |
    | agendaDescription | Agenda item description 컬럼 | "AI/ML for NR Air Interface" |
    
    **복합키**: `{meetingNumber}-{agendaNumber}` (같은 agendaNumber가 다른 미팅에서 다른 description을 가질 수 있음)
    
    ### 6.7 Spec
    
    | 항목 | 내용 |
    | --- | --- |
    | 소스 | Spec, Version 컬럼 |
    | ID | specNumber |
    
    | 속성 | 소스 | 예시 |
    | --- | --- | --- |
    | specNumber | Spec 컬럼 | "38.212" |
    | specVersion | Version 컬럼 (optional) | "18.5.0" |
    
    ### 6.8 WorkingGroup
    
    | 항목 | 내용 |
    | --- | --- |
    | 소스 | To, Cc 컬럼 (쉼표 분리 후 고유 값) |
    | ID | wgName |
    
    | 속성 | 소스 | 예시 |
    | --- | --- | --- |
    | wgName | To, Cc에서 추출 | "RAN1" |
    
    ### 6.9 Tdoc (일반)
    
    | 항목 | 내용 |
    | --- | --- |
    | 조건 | Type이 discussion, other, report, agenda, Work Plan, draft TR, draft TS, response, WID new, SID new, WI summary |
    | ID | tdocNumber |
    
    **Data Property 매핑**
    
    | 속성 | 소스 컬럼 | 필수 |
    | --- | --- | --- |
    | tdocNumber | TDoc | ✅ |
    | title | Title | ✅ |
    | abstract | Abstract | ❌ |
    | type | Type | ✅ |
    | status | TDoc Status | ✅ |
    | for | For | ❌ |
    | reservationDate | Reservation date | ✅ |
    | uploadedDate | Uploaded | ❌ |
    | secretaryRemarks | Secretary Remarks | ❌ |
    
    **Object Property 매핑**
    
    | 속성 | 소스 컬럼 | 대상 클래스 | 필수 |
    | --- | --- | --- | --- |
    | submittedBy | Source | Company | ❌ |
    | hasContact | Contact ID | Contact | ✅ |
    | relatedTo | Related WIs | WorkItem | ❌ |
    | belongsTo | Agenda item | AgendaItem | ✅ |
    | targetRelease | Release | Release | ❌ |
    | presentedAt | (파일명) | Meeting | ✅ |
    | isRevisionOf | Is revision of | Tdoc | ❌ |
    | revisedTo | Revised to | Tdoc | ❌ |
    | replyTo | Reply to | Tdoc | ❌ |
    | replyIn | Reply in | Tdoc | ❌ |
    
    **submittedBy 누락 시 처리 규칙:**
    
    | 조건 | 처리 |
    | --- | --- |
    | Source 컬럼이 비어있음 | SUBMITTED_BY 관계 생성 안 함 |
    | 영향 범위 | [P1-V03] 참조 |
    | 원인 | 데이터 소스(Tdoc_list.xlsx) 자체의 Source 컬럼 누락 |
    
    ### 6.10 CR (Tdoc 하위 클래스)
    
    | 항목 | 내용 |
    | --- | --- |
    | 조건 | Type이 CR, draftCR, pCR |
    | ID | tdocNumber |
    | 상속 | Tdoc의 모든 속성/관계 |
    
    **추가 Data Property 매핑**
    
    | 속성 | 소스 컬럼 | 필수 |
    | --- | --- | --- |
    | crNumber | CR | ❌ |
    | crCategory | CR category | ❌ |
    | clausesAffected | Clauses Affected | ❌ |
    | tsgCRPack | TSG CR Pack | ❌ |
    | crRevision | CR revision | ❌ |
    | affectsUICC | UICC | ❌ |
    | affectsME | ME | ❌ |
    | affectsRAN | RAN | ❌ |
    | affectsCN | CN | ❌ |
    
    **추가 Object Property 매핑**
    
    | 속성 | 소스 컬럼 | 대상 클래스 | 필수 |
    | --- | --- | --- | --- |
    | modifies | Spec | Spec | ✅ |
    
    ### 6.11 LS (Tdoc 하위 클래스)
    
    | 항목 | 내용 |
    | --- | --- |
    | 조건 | Type이 LS out 또는 LS in |
    | ID | tdocNumber |
    | 상속 | Tdoc의 모든 속성/관계 |
    
    **추가 Data Property 매핑**
    
    | 속성 | 소스 컬럼 | 필수 |
    | --- | --- | --- |
    | direction | Type에서 추출 ("in" 또는 "out") | ✅ |
    
    **추가 Object Property 매핑**
    
    | 속성 | 소스 컬럼 | 대상 클래스 | 필수 |
    | --- | --- | --- | --- |
    | sentTo | To | WorkingGroup | ❌ |
    | ccTo | Cc | WorkingGroup | ❌ |
    | originalLS | Original LS | Tdoc (외부) | ❌ |
    | originatedFrom | Original LS에서 추출 | WorkingGroup | ❌ |
    
    **sentTo 누락 시 처리 규칙:**
    
    | 조건 | 처리 |
    | --- | --- |
    | To 컬럼이 비어있음 | SENT_TO 관계 생성 안 함 |
    | 영향 범위 | [P1-V04] 참조 |
    | 원인 | 수신처 정보 없이 발신된 케이스 |
    
    ## 명명 규칙 (Naming Convention)
    
    | 레이어 | 규칙 | 예시 |
    | --- | --- | --- |
    | 스펙 문서 | camelCase | presentedAt, belongsTo |
    | Neo4j 구현 | snake_case | presented_at, belongs_to |
    
    변환 규칙: camelCase → snake_case 자동 변환
    예: `presentedAt` → `presented_at`
    
    ---
    
    ## 7. 데이터 변환 규칙
    
    ### 7.1 복합 값 처리
    
    | 컬럼 | 처리 | 결과 |
    | --- | --- | --- |
    | Source | 쉼표(,) 분리, trim | 복수 Company 참조 |
    | Related WIs | 쉼표(,) 분리, trim | 복수 WorkItem 참조 |
    | To | 쉼표(,) 분리, trim | 복수 WorkingGroup 참조 |
    | Cc | 쉼표(,) 분리, trim | 복수 WorkingGroup 참조 |
    
    ### 7.2 타입 변환
    
    | 컬럼 | 원본 타입 | 변환 |
    | --- | --- | --- |
    | Spec | float (38.212) | 문자열 "38.212" |
    | CR | float (693.0) | 문자열 "693" |
    | Reservation date | 문자열 "M/D/YYYY H:MM:SS AM/PM" | ISO 8601 |
    | Uploaded | Timestamp | ISO 8601 |
    | UICC, ME, RAN, CN | Boolean | 그대로 |
    
    ### 7.3 클래스 판별
    
    | Type 값 | 클래스 |
    | --- | --- |
    | CR, draftCR, pCR | CR |
    | LS out, LS in | LS |
    | 그 외 | Tdoc |
    
    ---
    
    ## 8. 참조 무결성 처리
    
    ### 8.1 내부 참조 (같은 데이터셋 내)
    
    | 속성 | 설명 |
    | --- | --- |
    | isRevisionOf | 대부분 내부 참조 |
    | revisedTo | 대부분 내부 참조 |
    | replyIn | 일부 내부 참조 |
    
    ### 8.2 외부 참조 (다른 회의/WG 문서)
    
    | 속성 | 설명 | 처리 |
    | --- | --- | --- |
    | replyTo | 이전 회의 문서 참조 가능 | 문자열로 저장, 향후 연결 |
    | originalLS | 다른 WG 문서 참조 | 문자열로 저장, 향후 연결 |
    
    ---
    
    ## 9. Company 정규화
    
    ### 9.1 정규화 이슈
    
    | 이슈 유형 | 예시 |
    | --- | --- |
    | 대소문자 불일치 | vivo, Vivo, VIVO |
    | 회사명 변형 | ZTE, ZTE Corporation |
    | 약어 | LG Electronics, LGE |
    | 역할 포함 | Moderator (Samsung), Rapporteur (Huawei) |
    | 괄호 내 쉼표 | "Moderator (NTT DOCOMO, INC.)" |
    | 오타/마침표 | CAICT., CATT) |
    
    ### 9.2 정규화 파이프라인
    
    ```
    [1단계] 괄호 내 쉼표 처리 (정규식)
               │
               ▼
    [2단계] 역할 분리 (정규식)
            "Moderator (Samsung)" → 회사: Samsung
               │
               ▼
    [3단계] 고유 회사명 추출
               │
               ▼
    [4단계] 정규화 사전 적용
               │
               ▼
    [5단계] company_aliases.json 저장
    
    ```
    
    ### 9.3 정규화 사전 형식
    
    ```json
    {
      "Samsung": ["Samsung", "Samsung Electronics", "SEC"],
      "Huawei": ["Huawei", "HW", "Huawei Technologies", "HiSilicon"],
      "ZTE": ["ZTE", "ZTE Corporation"],
      "vivo": ["vivo", "Vivo", "VIVO"],
      "LG": ["LG Electronics", "LGE"],
      "NTT DOCOMO": ["NTT DOCOMO", "NTT DOCOMO, INC."]
    }
    
    ```
    
    ---
    
    ## 10. 예시 인스턴스
    
    ### 10.1 Meeting 예시
    
    ```json
    {
      "@type": "Meeting",
      "meetingNumber": "RAN1#120",
      "canonicalMeetingNumber": "RAN1#120",
      "meetingNumberInt": 120,
      "workingGroup": "RAN1"
    }
    
    ```
    
    ### 10.2 Tdoc 예시
    
    ```json
    {
      "@type": "Tdoc",
      "tdocNumber": "R1-2500001",
      "title": "Discussion on NR MIMO enhancements",
      "type": "discussion",
      "status": "noted",
      "for": "Discussion",
      "reservationDate": "2025-01-15T09:30:00Z",
      "submittedBy": [
        { "@id": "company:Samsung" }
      ],
      "hasContact": { "@id": "contact:52292" },
      "belongsTo": { "@id": "agenda:9.1" },
      "presentedAt": { "@id": "meeting:RAN1#120" },
      "relatedTo": [
        { "@id": "workitem:NR_MIMO_Ph5-Core" }
      ],
      "targetRelease": { "@id": "release:Rel-19" }
    }
    
    ```
    
    ### 10.3 CR 예시
    
    ```json
    {
      "@type": "CR",
      "tdocNumber": "R1-2500088",
      "title": "CR to 38.212 on PDCCH monitoring",
      "type": "CR",
      "status": "agreed",
      "for": "Agreement",
      "crNumber": "0693",
      "crCategory": "F",
      "clausesAffected": "5.3.1, 5.3.2",
      "crRevision": "2",
      "modifies": { "@id": "spec:38.212" },
      "submittedBy": [
        { "@id": "company:Ericsson" }
      ],
      "hasContact": { "@id": "contact:12345" },
      "belongsTo": { "@id": "agenda:8.1" },
      "presentedAt": { "@id": "meeting:RAN1#120" }
    }
    
    ```
    
    ### 10.4 LS 예시
    
    ```json
    {
      "@type": "LS",
      "tdocNumber": "R1-2500150",
      "title": "LS on positioning enhancements",
      "type": "LS out",
      "status": "approved",
      "direction": "out",
      "sentTo": [
        { "@id": "wg:RAN2" },
        { "@id": "wg:RAN4" }
      ],
      "ccTo": [
        { "@id": "wg:SA2" }
      ],
      "submittedBy": [
        { "@id": "company:Qualcomm" }
      ],
      "hasContact": { "@id": "contact:67890" },
      "belongsTo": { "@id": "agenda:8.5" },
      "presentedAt": { "@id": "meeting:RAN1#120" }
    }
    
    ```
    
    ---
    
    ## 11. 검증 규칙
    
    ### 11.1 무결성 검증
    
    | 검증 항목 | 규칙 |
    | --- | --- |
    | ID 중복 | 클래스 내 고유 |
    | 필수 속성 | 모두 값 존재 |
    | 참조 무결성 | 참조 대상 존재 |
    | Enum 유효성 | 정의된 값만 허용 |
    
    ### 11.2 통계 검증
    
    | 검증 항목 | 기대 결과 |
    | --- | --- |
    | 총 Tdoc 수 | Tdoc + CR + LS = [P1-V01] |
    | 필수 속성 | 모두 존재 |
    
    ---
    
    ## 12. 요약
    
    ### 12.1 인스턴스 생성 명세
    
    | 클래스 | ID 패턴 | 데이터 소스 |
    | --- | --- | --- |
    | Meeting | `{WG}#{회차}[-e]` | 파일명 |
    | Release | `Rel-{번호}` | Release 컬럼 |
    | Company | 정규화된 회사명 | Source 컬럼 |
    | Contact | 3GPP ID | Contact ID 컬럼 |
    | WorkItem | WI 코드 | Related WIs 컬럼 |
    | AgendaItem | Agenda 번호 | Agenda item 컬럼 |
    | Spec | Spec 번호 | Spec 컬럼 |
    | WorkingGroup | WG 이름 | To, Cc 컬럼 |
    | Tdoc | `R1-{YYNNNNN}` | TDoc 컬럼 |
    | CR | `R1-{YYNNNNN}` | TDoc 컬럼 (Type=CR/draftCR/pCR) |
    | LS | `R1-{YYNNNNN}` | TDoc 컬럼 (Type=LS in/out) |
    
    ### 12.2 변환 규칙 요약
    
    | 항목 | 규칙 |
    | --- | --- |
    | 복합 값 | 쉼표 분리 → 복수 관계 |
    | 타입 변환 | float → String, DateTime → ISO 8601 |
    | 클래스 판별 | Type 값 기반 |
    | 정규화 | Company 정규화 사전 적용 |
    
    ---
    
    ## 13. 전체 완료
    
    Phase-1 온톨로지 설계가 완료되었습니다.
    
    ---
    
    ## 14. Appendix ID 네이밍 규칙
    
    본 프로젝트는 Phase 1~11에 걸쳐 Spec 문서를 관리한다. Phase 간 수치 참조 시 충돌과 이중 관리를 방지하기 위해 다음 규칙을 적용한다.
    
    ### 14.1 ID 형식
    
    `P{n}-V{번호}`
    
    | 구성 요소 | 설명 | 예시 |
    | --- | --- | --- |
    | P{n} | Phase 번호 | P1, P2, ... P11 |
    | V | 변수 (Variable) | V |
    | 번호 | 01부터 순차 (빈번호 없음) | 01, 02, ... |
    
    ### 14.2 V-ID 부여 조건
    
    V-ID는 다음 3조건을 모두 충족하는 수치에만 부여한다:
    
    | 조건 | 설명 |
    | --- | --- |
    | 가변성 | 새 데이터 추가 시 값이 바뀜 |
    | 필수성 | Spec↔구현 대조에 필수 |
    | 비자명성 | 본문 목록/테이블에서 직접 세어 확인 불가 |
    
    3조건을 모두 충족하지 않는 수치는 본문에서 제거한다. 설계 확정값(클래스 수, OP 수 등)은 독자가 본문 목록/테이블에서 직접 세거나 구현 코드에서 확인한다.
    
    ### 14.3 Cross-Phase 참조 원칙
    
    - 각 Phase Appendix는 자기 Phase가 "소유"하는 수치만 V-ID를 가진다.
    - 다른 Phase 수치의 복사본을 자기 Appendix에 두지 않는다.
    - 다른 Phase 수치가 필요하면 원본 Phase의 V-ID를 직접 참조한다.
    예: Phase-6에서 Phase-1 총 Tdoc 수 참조 시 → [P1-V01]
    
    ---
    
    ## Appendix A: 기준 수치
    
    > 이 테이블이 Spec의 수치 권위 소스이다.
    > 
    
    > 새 미팅 데이터 추가 시 이 테이블만 수정한다.
    > 
    
    | ID | 항목 | 기준값 | 비고 |
    | --- | --- | --- | --- |
    | P1-V01 | 총 Tdoc 수 (Tdoc+CR+LS) | 123,676 | 전체 미팅 Tdoc 합계 (Tdoc_list 기준) |
    | P1-V02 | Meeting 수 | 60 | 파일명 기준 |
    | P1-V03 | submittedBy 누락 건수 | 999 | Source 컬럼 자체 누락. 전 기간 분산 |
    | P1-V04 | sentTo 누락 건수 | 0 | RAN1#123 추가 후 재측정 |
    | P1-V05 | 데이터 범위 | RAN1#84 ~ RAN1#123 (60개 미팅) | 전체 Phase 공통 데이터 범위 |