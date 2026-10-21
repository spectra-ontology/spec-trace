- **phase-1: Ontology 101 기반 표준화 엔지니어 타겟 Tdoc 관계 모델링 (Tdoc_list)**
    
    ## Step 1: Domain과 Scope 결정
    
    > Ontology 101 원칙
    >
    >
    > *"We suggest starting the development of an ontology by defining its domain and scope. That is, answer several basic questions: What is the domain that the ontology will cover? For what we are going to use the ontology? For what types of questions the information in the ontology should provide answers? Who will use and maintain the ontology?"*
    >
    > — Noy & McGuinness, Ontology Development 101
    >
    
    > **용어 번역 가교**: 본 Spec의 영문 인용문에 등장하는 "Domain and Scope", "Class/Slot/Facet" 등은 아래 본문에서 한국어로 대응 설명한다.
    > - Domain and Scope → 1.1/1.2 "도메인"과 "범위"
    > - Class → 4. "클래스" (온톨로지의 개체 유형)
    > - Slot → 5. "속성(Slot)" (클래스가 가지는 속성·관계)
    > - Facet → "제약"(값 타입, 카디널리티 등 속성의 제약 조건)
    
    ---
    
    ## 1. 기본 질문에 대한 답변
    
    ### 1.1 What is the domain?
    
    **3GPP RAN2 회의 문서(Tdoc) 메타데이터와 그 관계**
    
    RAN2 (Radio Layer 2/3)는 NR의 MAC, RLC, PDCP, SDAP, RRC 프로토콜을 담당한다.
    RAN1이 물리계층(Physical Layer)을 다루는 반면, RAN2는 물리계층 위의 프로토콜 스택을 설계한다.
    
    주요 Specification:
    - **38.321**: MAC (Medium Access Control)
    - **38.322**: RLC (Radio Link Control)
    - **38.323**: PDCP (Packet Data Convergence Protocol)
    - **38.331**: RRC (Radio Resource Control) — RAN2 최대 규모 Spec
    - **38.300**: NR/NG-RAN Overall description
    - **38.304**: UE procedures in Idle/Inactive
    - **38.306**: UE Radio Access Capabilities
    - **37.324**: SRAP (Sidelink Relay Adaptation Protocol)
    - 기타: 38.305, 38.314, 38.340, 38.351, 38.355, 38.391
    
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
    | **Phase-1** | **Tdoc_list (Excel)** | [P1-V02] 파일 ([P1-V05] 범위), [P1-V01] TDocs (dedup 기준) |
    
    데이터 경로: TDoc List Excel 파일 (미팅별 `.xlsx`)
    
    > **[P1-V01] 같은 표기는 무엇인가요?** — Spec 본문에 등장하는 `[P{n}-V{번호}]`는 "Versioned 수치 참조" 약식 표기이다. 실제 수치(파일 수·TDoc 수 등)는 본 Spec 하단 **[Appendix A: 기준 수치](#appendix-a-기준-수치)** 표에 모여 있다. 본문에서 수치를 직접 쓰지 않는 이유와 명명 규칙은 **§14 Appendix ID 네이밍 규칙** 참조. 데이터 변경 시 Appendix A의 해당 행만 수정하면 본문 전체가 갱신된다.
    
    ---
    
    ## 2. Scope 정의
    
    ### 2.1 포함 (In Scope)
    
    | 포함 | 제외 |
    | --- | --- |
    | Tdoc 메타데이터 | TS/TR 본문 |
    | Tdoc 간 관계 (revision, LS) | Final Report (Minutes) 본문 (Phase-2에서) |
    | 회의 정보 | 다른 WG 데이터 |
    | 회사 정보 |  |
    | Work Item / Agenda Item |  |
    | Release 정보 |  |
    
    ### 2.2 RAN2 데이터 특성
    
    | 항목 | RAN2 |
    | --- | --- |
    | TDoc 접두사 | R2-NNNNNNN |
    | 미팅 폴더 | TSGR2_{N} |
    | 미팅 범위 | [P1-V05] ([P1-V02] 파일, bis 포함) |
    | bis 접미사 | bis (93bis) |
    | TDoc List 컬럼 | 시기별 변동 (표준 분포 + 비표준 변종 일부; 분포는 [P1-V06] 참조) |
    | TDoc 총 수 | [P1-V01] (dedup) |
    | 핵심 TS | 38.3xx (L2/3 Protocol) + 37.324 |
    
    ### 2.3 데이터 품질 이슈
    
    | 이슈 | 영향 | 처리 방안 |
    | --- | --- | --- |
    | Release 컬럼 방어 필터 | Release 값에 비정상 값 혼입 가능성 (전수 스캔 시 현재 0건이나 방어적 처리) | 파싱 시 "Rel-" 접두사 없는 값 필터링 |
    | 전자회의 접미사 혼재 | `-e`, `_e`, `bis-e` 등 | 미팅 번호 추출 시 정규화 필요. **정규화 정책 주 정의는 본 Phase-1 §5.1 Meeting 노드 `canonicalMeetingNumber` 규칙** — Phase-6/10은 이 규칙을 참조한다 (B-04 중앙집중화). |
    | TDoc List 컬럼 수 시기별 차이 | 초기 3개: 32개 (컬럼명에 `#` 접미사 + `Type supplement`), 중간 37개: 31개 (기본), 최신 18개: 36개 (`Clauses Affected`, `UICC`, `ME`, `RAN`, `CN` 추가) | 파싱 시 컬럼명 정규화 필요. 최신 미팅에서는 Clauses Affected/영향범위 확보 가능 |
    | TDoc List 중복 파일 | #93-BIS, #95-BIS에 .xlsm(32컬럼) + .xlsx(31컬럼) 동시 존재. 동일 미팅의 구/신 버전으로 행 수 동일 | 파일 수 [P1-V02] 유지. 파서에서 동일 미팅 중복 감지 시 tdocNumber 기준 dedup 처리 |
    
    ---
    
    ## 3. Competency Questions
    
    RAN2 데이터에 맞춘 CQ 체계를 사용한다.
    
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
    | 2-5 | 특정 CR의 카테고리와 영향 범위는? | *CR category: Phase-1 (TDoc List). Clauses Affected: 최신 미팅(#120~) TDoc List + 나머지는 Phase-4 (CR 문서 파싱)* |
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
    
    *참고: "Meeting 번호 DESC"는 `meetingNumberInt` 속성으로 정렬해야 숫자 기반 정렬이 보장됨 (문자열 정렬 시 #99 > #132 문제 발생)*
    
    ### 4.2 결과 개수 (Default Limit)
    
    | CQ 유형 | 기본값 | 적용 CQ |
    | --- | --- | --- |
    | 목록 조회 | 10 | 1-1 ~ 1-5, 1-9, 2-1 ~ 2-3, 2-6 ~ 2-7, 3-1 ~ 3-2, 3-5, 4-1, 4-3 |
    | 단일 조회 | 1 | 1-6 ~ 1-8, 2-4 ~ 2-5 |
    | 집계/순위 | 10 | 3-3 ~ 3-4, 3-6, 4-2 |
    
    *참고: Limit은 쿼리 시 파라미터로 조정 가능*
    
    ---
    
    ## 5. CQ vs Tdoc 메타데이터 검증
    
    TDoc List 컬럼 구조가 RAN1과 동일하므로 (시기별 변동, §1.4/§2.3 [P1-V06] 참조), RAN1에서 확인된 CQ 답변 가능성이 RAN2에도 그대로 적용된다.
    
    | # | Competency Question | 필요한 데이터 | 컬럼 존재 | 답변 가능 | 해결 방법 |
    | --- | --- | --- | --- | --- | --- |
    | **CQ1. Tdoc 기본 검색** |  |  |  |  |  |
    | 1-1 | 특정 회의에서 특정 Work Item 관련 Tdoc 목록은? | Meeting, Related WIs | ✅ | ✅ | Meeting 클래스 추가 (Step 4). 파일명에서 추출 |
    | 1-2 | 특정 회의에서 특정 Agenda Item 관련 Tdoc 목록은? | Meeting, Agenda item | ✅ | ✅ | Meeting 클래스 추가 (Step 4). 파일명에서 추출 |
    | 1-3 | 특정 회의에서 특정 회사가 제출한 Tdoc 목록은? | Meeting, Source | ✅ | ✅ | Meeting 클래스 추가 (Step 4). 파일명에서 추출 |
    | 1-4 | 특정 Release에서 논의된 Tdoc 목록은? | Release | ✅ | ✅ | 초기 미팅 Release 오염 필터 적용 |
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
    | 2-5 | 특정 CR의 카테고리와 영향 범위는? | CR category, Clauses Affected | △ | △ | CR category는 TDoc List [24]에 있음. Clauses Affected는 최신 미팅(#120~, 18개 파일)의 TDoc List에 포함. 초기/중간 미팅에서는 Phase-4에서 확보 |
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
    | **Release 컬럼 방어 필터** | 1-4 | Release 값에 비정상 값 혼입 가능성. "Rel-" 접두사 필터로 방어적 처리 (현재 전수 스캔 오염 0건) | ✅ 해결 |
    
    ### 6.2 결론
    
    모든 CQ에 대해 TDoc List 컬럼에서 데이터 소스가 확인됨.
    RAN2 특화 이슈(Release 컬럼 오염, bis 미팅 패턴)는 파싱 단계에서 처리.
    
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
    
    3GPP TDoc 도메인의 기존 Ontology 조사 결과:
    
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
    | CR 관련 | CR, CR category (Clauses Affected는 Phase-4) |
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
    | 파일 | Tdoc_list Excel (58개 미팅) |
    | 경로 | TDoc List Excel 입력 디렉토리 (미팅별 `.xlsx`) |
    | 컬럼 | 시기별 변동 (분포는 [P1-V06], 아래 §2.3 참조) |
    | TDoc 총 수 | [P1-V01] (dedup 기준) |
    
    ---
    
    ## 3. 용어 나열
    
    ### 3.1 클래스 후보
    
    | 용어 | 데이터 소스 | 채울 수 있나? | 비고 |
    | --- | --- | --- | --- |
    | Tdoc | TDoc 컬럼 | ✅ | 상위 클래스 |
    | CR | Type 컬럼 (CR, draftCR, pCR) | ✅ | Tdoc 하위 클래스 |
    | LS | Type 컬럼 (LS in, LS out) | ✅ | Tdoc 하위 클래스 |
    | Meeting | 파일명에서 추출 | ✅ | TSGR2_{N} 패턴 |
    | Company | Source 컬럼 | ✅ | 파싱/정규화 필요 (31.4% 복합 값) |
    | Contact | Contact 컬럼 | ✅ |  |
    | WorkItem | Related WIs 컬럼 | ✅ | 파싱 필요 |
    | AgendaItem | Agenda item 컬럼 | ✅ |  |
    | Release | Release 컬럼 | ✅ | 초기 미팅 오염 주의 (Step 1 §2.3) |
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
    | crRevision | CR revision | CR | ✅ |
    | crCategory | CR category | CR | ✅ |
    | clausesAffected | (Phase-4에서 CR 문서 파싱) | CR | △ Phase-4 |
    | tsgCRPack | TSG CR Pack | CR | ✅ |
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
    | meetingNumber | 파일명 (TSGR2_{N}) | Meeting | ✅ |
    | canonicalMeetingNumber | meetingNumber에서 정규화 | Meeting | ✅ |
    | meetingNumberInt | canonicalMeetingNumber에서 추출 | Meeting | ✅ |
    | workingGroup | "RAN2" 고정 | Meeting | ✅ |
    
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
    
    **RAN2 처리**: CR revision은 11,213건(CR 대비 32.7%)으로 유의미하므로 §3.3에 `crRevision` 속성으로 포함.
    
    ---
    
    ## 5. 파싱 필요 항목
    
    | 컬럼 | 이유 | 예시 |
    | --- | --- | --- |
    | Source | 복합 값 (31.4%) | "Samsung, Huawei" → 2개 Company |
    | Related WIs | 복합 값 | "NR_MIMO_Ph5-Core, NR_duplex" → 2개 WorkItem |
    | To | 복합 값 | 복수 WG 문자열 → 2개 이상 WorkingGroup |
    | Cc | 복합 값 | 복수 WG 문자열 → 2개 이상 WorkingGroup |
    | Release | 방어 필터 | "Rel-" 접두사 없는 값 필터링 (현재 오염 0건, 방어적 처리) |
    
    ### 5.1 RAN2 Type 값
    
    RAN2에서 관측되는 Type 중 특수 처리가 필요한 항목:
    
    | Type | 처리 |
    | --- | --- |
    | draft TS | Tdoc (상위 클래스) |
    | draft TR | Tdoc (상위 클래스) |
    | response | Tdoc (상위 클래스) |
    
    ### 5.2 RAN2 Status 값
    
    RAN2에서 관측되는 Status 중 별도 처리가 필요한 항목:
    
    | Status | 처리 |
    | --- | --- |
    | merged | Data Property로 저장 |
    | reserved | Data Property로 저장 |
    | treated | Data Property로 저장 |
    
    ---
    
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
    
    RAN1과 동일한 11개 클래스. TDoc List 컬럼 구조가 동일하므로 클래스 구조도 동일.
    
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
    
    > §5/§6 본문은 정성 표현 위주이며, 구체 건수·비율은 Appendix A의 V-ID 테이블을 권위로 한다.

    ### 5.1 CR (Change Request)

    
    | 기준 | 충족 여부 | 내용 |
    | --- | --- | --- |
    | 추가 속성 | ✅ | crNumber, crCategory, crRevision, clausesAffected, tsgCRPack, affectsUICC, affectsME, affectsRAN, affectsCN |
    | 다른 관계 | ✅ | modifies → Spec |
    | 해당 Type | - | 'CR', 'draftCR', 'pCR' |
    
    **RAN1과의 차이**: crRevision이 RAN2에서는 유의미한 비중을 가진다 (RAN1은 미미). 정량 비중은 Appendix A.
    
    ### 5.2 LS (Liaison Statement)
    
    | 기준 | 충족 여부 | 내용 |
    | --- | --- | --- |
    | 추가 속성 | ✅ | direction ('in' / 'out') |
    | 다른 관계 | ✅ | sentTo → WorkingGroup, ccTo → WorkingGroup, originalLS → Tdoc |
    | 해당 Type | - | 'LS out', 'LS in' |
    
    ---
    
    ## 6. Type별 클래스 매핑
    | Type 값 | 건수 | 클래스 | 구분 속성 |
    | --- | --- | --- | --- |
    | discussion | 70,223 | Tdoc | type = 'discussion' |
    | CR | 28,688 | CR | - |
    | draftCR | 5,179 | CR | crNumber가 null |
    | pCR | 380 | CR | crNumber가 null |
    | LS out | 4,728 | LS | direction = 'out' |
    | LS in | 4,565 | LS | direction = 'in' |
    | other | 1,229 | Tdoc | type = 'other' |
    | report | 1,114 | Tdoc | type = 'report' |
    | Work Plan | 192 | Tdoc | type = 'Work Plan' |
    | draft TS | 117 | Tdoc | type = 'draft TS' |
    | draft TR | 114 | Tdoc | type = 'draft TR' |
    | agenda | 71 | Tdoc | type = 'agenda' |
    | WI summary | 7 | Tdoc | type = 'WI summary' |
    | response | 5 | Tdoc | type = 'response' |
    | CR pack | 1 | Tdoc | type = 'CR pack' |
    | TS or TR cover | 1 | Tdoc | type = 'TS or TR cover' |
    
    *tdocNumber 기준 dedup 후 수치. 파일 58개 중 2건 중복 존재.*
    
    **RAN2 추가 Type** (RAN1에 없음): `CR pack` (1건), `TS or TR cover` (1건). 극소수이므로 Tdoc 상위 클래스로 분류.
    
    ### 인스턴스 분포 요약
    
    클래스별 건수/비율은 §7 "클래스별 인스턴스 분포" 참조. 합계는 [P1-V01].
    
    *파일 58개 중 2건(#93-BIS, #95-BIS)에 .xlsm/.xlsx 중복 존재. 수치는 tdocNumber 기준 dedup 후.*
    
    ---
    
    ## 7. 클래스별 인스턴스 분포
    
    | 클래스 | 분류 기준 |
    | --- | --- |
    | Tdoc (직접) | Type이 discussion, other, report, agenda, Work Plan, draft TS, draft TR, response, WI summary, CR pack, TS or TR cover |
    | CR | Type이 CR, draftCR, pCR |
    | LS | Type이 LS out, LS in |
    
    ---
    
    ## 8. 클래스로 정의하지 않은 용어
    
    | 용어 | 이유 | 처리 |
    | --- | --- | --- |
    | tdocNumber, title, status 등 | 속성값 | Step 5 Data Property |
    | submittedBy, relatedTo 등 | 관계 | Step 5 Object Property |
    | draftCR, pCR | CR과 동일 구조 | type 속성으로 구분 |
    | CR pack, TS or TR cover | 극소수 (각 1건) | type 속성으로 구분 |
    
    ---
    
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
    | tdocNumber | String | TDoc | Tdoc의 고유 식별자 (예: R2-2500001). 형식: R2-YYNNNNN |
    | title | String | Title | Tdoc의 제목. 문서 내용을 요약하는 짧은 설명 |
    | abstract | String | Abstract | Tdoc의 요약. 문서 내용의 상세 설명 (대부분 비어있음) |
    | type | String (Enum) | Type | Tdoc의 유형 |
    | status | String (Enum) | TDoc Status | 회의에서의 결정 결과 |
    | for | String (Enum) | For | Tdoc의 목적/용도 |
    | reservationDate | DateTime | Reservation date | Tdoc 번호 예약 일시 |
    | uploadedDate | DateTime | Uploaded | Tdoc 파일 업로드 일시 |
    | secretaryRemarks | String | Secretary Remarks | 회의 비서의 메모 (예: "Late contribution", "Revised in session") |
    
    **RAN2 차이**: tdocNumber 형식이 R2-YYNNNNN (RAN1은 R1-YYNNNNN)
    
    ---
    
    ## 4. CR 클래스 속성 (Tdoc 상속 + 추가)
    ### 4.1 추가 Object Property
    
    | 속성명 | Range | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | modifies | Spec | Spec | CR이 변경을 요청하는 대상 기술 규격 (예: 38.331) |
    
    ### 4.2 추가 Data Property
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | crNumber | String | CR | CR의 공식 번호 (예: 0693). draftCR은 이 값이 없음 |
    | crCategory | String (Enum) | CR category | CR의 카테고리 |
    | crRevision | String | CR revision | CR의 수정 횟수 (1~9). RAN2: 11,213건 (CR 대비 32.7%) |
    | clausesAffected | String | TDoc List (최신 #120~) 또는 Phase-4 | CR로 인해 영향받는 규격의 조항 번호. 최신 18개 미팅에서는 TDoc List에 포함 |
    | tsgCRPack | String | TSG CR Pack | TSG에 제출되는 CR Pack 번호 (예: RP-250233) |
    | affectsUICC | Boolean | UICC | CR이 UICC에 영향을 미치는지 여부 |
    | affectsME | Boolean | ME | CR이 ME에 영향을 미치는지 여부 |
    | affectsRAN | Boolean | RAN | CR이 RAN에 영향을 미치는지 여부 |
    | affectsCN | Boolean | CN | CR이 CN에 영향을 미치는지 여부 |
    
    **RAN1과의 차이**: crRevision이 RAN2에서 유의미 (CR 대비 32.2%, 11,214건). clausesAffected는 최신 미팅(#120~)에서 TDoc List에 포함. 나머지는 Phase-4에서 확보.
    
    ---
    
    ## 5. LS 클래스 속성 (Tdoc 상속 + 추가)
    
    ### 5.1 추가 Object Property
    
    | 속성명 | Range | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | sentTo | WorkingGroup | To | LS의 수신 대상 Working Group. 복수 가능 |
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
    | meetingNumber | String | 파일명 | 회의 번호 원본 (예: RAN2#120, RAN2#101bis-e) |
    | canonicalMeetingNumber | String | meetingNumber에서 정규화 | 정규화된 회의 번호. `-e` suffix 제거 |
    | meetingNumberInt | Integer | canonicalMeetingNumber에서 추출 | 정렬용 숫자값. CQ 결과 정렬에 사용 |
    | workingGroup | String | "RAN2" 고정 | 회의를 주관하는 Working Group |
    
    **Meeting ID 정규화 규칙:**
    
    | 원본 | canonicalMeetingNumber | meetingNumberInt | 설명 |
    | --- | --- | --- | --- |
    | RAN2#101bis-e | RAN2#101bis | 101 | e-meeting suffix 제거 |
    | RAN2#113bis-e | RAN2#113bis | 113 | e-meeting suffix만 제거, bis 유지 |
    | RAN2#120 | RAN2#120 | 120 | 변경 없음 |
    
    **RAN1과의 차이**: RAN1은 `b` (84b), RAN2는 `bis` (93bis). 정규화 시 bis 유지.
    
    ### 6.2 Company
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | companyName | String | Source 파싱 | 회사/조직의 정규화된 대표 이름 (예: Samsung, Huawei, Ericsson) |
    | aliases | List<String> | company_aliases.json | 회사의 다른 이름/변형 목록. 정규화 사전에서 추출 |
    
    ### 6.3 Contact
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | contactName | String | Contact | 담당자의 이름 |
    | contactId | String | Contact ID | 3GPP 시스템에서의 담당자 고유 ID |
    
    ### 6.4 WorkItem
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | workItemCode | String | Related WIs 파싱 | Work Item의 코드명 (예: NR_RRC_inactive-Core) |
    
    ### 6.5 AgendaItem
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | agendaNumber | String | Agenda item | Agenda Item의 번호 (예: 9.1, 9.1.1). 계층 구조를 가짐 |
    | agendaDescription | String | Agenda item description | Agenda Item의 설명 |
    
    ### 6.6 Release
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | releaseName | String | Release | 3GPP Release 버전명 (예: Rel-18, Rel-19). 초기 미팅 오염 필터 적용 (Step 1 §2.3) |
    
    ### 6.7 Spec
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | specNumber | String | Spec | 기술 규격 번호 (예: 38.331, 38.321) |
    | specVersion | String | Version | 규격의 버전 (예: 18.5.0) |
    | specTitle | String | (외부 데이터/동적 생성) | 기술 규격 제목 (예: "RRC protocol specification") |
    
    ### 6.8 WorkingGroup
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | wgName | String | To, Cc 파싱 | Working Group 이름 (예: RAN2, SA2) |
    
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
    | 12 | clausesAffected | CR | String | 영향받는 조항 (최신 #120~ TDoc List + Phase-4) |
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
    | submittedBy | Tdoc | Company | 0..* | ❌ | 복수 회사 공동 제출 가능. Source 누락 건수 — [P1-V03] |
    | hasContact | Tdoc | Contact | 1 | ✅ | 모든 Tdoc에 Contact 존재 |
    | relatedTo | Tdoc | WorkItem | 0..* | ❌ | 일부 Tdoc은 Related WIs 없음 |
    | belongsTo | Tdoc | AgendaItem | 1 | ✅ | 모든 Tdoc에 Agenda item 존재 |
    | targetRelease | Tdoc | Release | 0..1 | ❌ | 일부 Tdoc은 Release 없음. 초기 미팅 오염 필터 적용 |
    | presentedAt | Tdoc | Meeting | 1 | ✅ | 모든 Tdoc은 특정 회의에 속함 |
    | isRevisionOf | Tdoc | Tdoc | 0..1 | ❌ | 최초 버전은 없음 |
    | revisedTo | Tdoc | Tdoc | 0..* | ❌ | 하나의 TDoc이 여러 버전으로 분기 가능 |
    | replyTo | Tdoc | Tdoc | 0..* | ❌ | 하나의 TDoc이 여러 문서에 답변 가능 |
    | replyIn | Tdoc | Tdoc | 0..* | ❌ | 복수 WG 답변 가능 |
    
    ### 3.2 Data Property
    
    | 속성명 | Domain | Type | Cardinality | 필수 | 근거 |
    | --- | --- | --- | --- | --- | --- |
    | tdocNumber | Tdoc | String | 1 | ✅ | 모든 Tdoc의 고유 식별자 |
    | title | Tdoc | String | 1 | ✅ | 모든 Tdoc에 제목 존재 |
    | abstract | Tdoc | String | 0..1 | ❌ | 대부분 비어있음 |
    | type | Tdoc | String (Enum) | 1 | ✅ | 모든 Tdoc에 유형 존재 |
    | status | Tdoc | String (Enum) | 1 | ✅ | 모든 Tdoc에 상태 존재 |
    | for | Tdoc | String (Enum) | 0..1 | ❌ | 일부 Tdoc은 For 없음 |
    | reservationDate | Tdoc | DateTime | 1 | ✅ | 모든 Tdoc에 예약일 존재 |
    | uploadedDate | Tdoc | DateTime | 0..1 | ❌ | 미업로드 문서 가능 |
    | secretaryRemarks | Tdoc | String | 0..1 | ❌ | 일부만 비서 메모 존재 |
    
    ---
    
    ## 4. CR 클래스 추가 속성 제약조건
    ### 4.1 Object Property
    
    | 속성명 | Domain | Range | Cardinality | 필수 | 근거 |
    | --- | --- | --- | --- | --- | --- |
    | modifies | CR | Spec | 0..* | ❌ | 거의 모든 CR에 Spec 존재 (34,852/34,853). 초기 미팅 pCR 1건(R2-161663, #93) Spec null. 모델상 한 CR이 복수 Spec 병기 가능 (ontology tdoc:modifies 다중값) |
    
    ### 4.2 Data Property
    
    | 속성명 | Domain | Type | Cardinality | 필수 | 근거 |
    | --- | --- | --- | --- | --- | --- |
    | crNumber | CR | String | 0..1 | ❌ | draftCR은 CR 번호 미부여 |
    | crCategory | CR | String (Enum) | 0..1 | ❌ | 일부 CR은 카테고리 미지정 |
    | crRevision | CR | String | 0..1 | ❌ | 일부 CR만 revision 번호 보유 (RAN2: CR 대비 32.2%, 11,214건) |
    | clausesAffected | CR | String | 0..1 | ❌ | 최신 미팅(#120~)은 TDoc List에 포함, 나머지 Phase-4 |
    | tsgCRPack | CR | String | 0..1 | ❌ | 승인된 CR만 존재 |
    | affectsUICC | CR | Boolean | 0..1 | ❌ | 일부만 명시 |
    | affectsME | CR | Boolean | 0..1 | ❌ | 일부만 명시 |
    | affectsRAN | CR | Boolean | 0..1 | ❌ | 일부만 명시 |
    | affectsCN | CR | Boolean | 0..1 | ❌ | 일부만 명시 |
    
    ---
    
    ## 5. LS 클래스 추가 속성 제약조건
    
    ### 5.1 Object Property
    
    | 속성명 | Domain | Range | Cardinality | 필수 | 근거 |
    | --- | --- | --- | --- | --- | --- |
    | sentTo | LS | WorkingGroup | 0..* | ❌ | 수신처 없이 발신된 LS out 존재 ([P1-V04]) |
    | ccTo | LS | WorkingGroup | 0..* | ❌ | 참조는 선택사항 |
    | originalLS | LS | Tdoc | 0..1 | ❌ | LS in만 존재 |
    | originatedFrom | LS | WorkingGroup | 0..1 | ❌ | LS in만 존재 |
    
    ### 5.2 Data Property
    
    | 속성명 | Domain | Type | Cardinality | 필수 | 근거 |
    | --- | --- | --- | --- | --- | --- |
    | direction | LS | String (Enum) | 1 | ✅ | 모든 LS는 방향 있음 (in/out) |
    
    ---
    
    ## 6. 기타 클래스 속성 제약조건
    
    ### 6.1 Meeting
    
    | 속성명 | Domain | Type | Cardinality | 필수 | 설명 |
    | --- | --- | --- | --- | --- | --- |
    | meetingNumber | Meeting | String | 1 | ✅ | 회의 번호 원본 |
    | canonicalMeetingNumber | Meeting | String | 1 | ✅ | 정규화된 회의 번호 |
    | meetingNumberInt | Meeting | Integer | 1 | ✅ | 정렬용 숫자값 |
    | workingGroup | Meeting | String | 1 | ✅ | 주관 WG |
    
    ### 6.2 Company
    
    | 속성명 | Domain | Type | Cardinality | 필수 | 설명 |
    | --- | --- | --- | --- | --- | --- |
    | companyName | Company | String | 1 | ✅ | 회사/조직의 고유 이름 |
    | aliases | Company | List<String> | 0..* | ❌ | 회사의 다른 이름/변형 목록 |
    
    ### 6.3 Contact
    
    | 속성명 | Domain | Type | Cardinality | 필수 | 설명 |
    | --- | --- | --- | --- | --- | --- |
    | contactName | Contact | String | 1 | ✅ | 담당자의 이름 |
    | contactId | Contact | String | 1 | ✅ | 담당자 고유 ID |
    
    ### 6.4 WorkItem
    
    | 속성명 | Domain | Type | Cardinality | 필수 | 설명 |
    | --- | --- | --- | --- | --- | --- |
    | workItemCode | WorkItem | String | 1 | ✅ | Work Item의 고유 코드명 |
    
    ### 6.5 AgendaItem
    
    | 속성명 | Domain | Type | Cardinality | 필수 | 설명 |
    | --- | --- | --- | --- | --- | --- |
    | agendaNumber | AgendaItem | String | 1 | ✅ | Agenda 번호 |
    | agendaDescription | AgendaItem | String | 1 | ✅ | Agenda 설명 |
    
    ### 6.6 Release
    
    | 속성명 | Domain | Type | Cardinality | 필수 | 설명 |
    | --- | --- | --- | --- | --- | --- |
    | releaseName | Release | String | 1 | ✅ | Release 버전명 |
    
    ### 6.7 Spec
    
    | 속성명 | Domain | Type | Cardinality | 필수 | 설명 |
    | --- | --- | --- | --- | --- | --- |
    | specNumber | Spec | String | 1 | ✅ | 기술 규격 번호 |
    | specVersion | Spec | String | 0..1 | ❌ | 규격의 버전 |
    | specTitle | Spec | String | 0..1 | ❌ | 기술 규격 제목 |
    
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
    | CR | 공식 Change Request |
    | draftCR | Change Request 초안 |
    | pCR | Proposed CR |
    | LS out | 발신 Liaison Statement |
    | LS in | 수신 Liaison Statement |
    | other | 기타 문서 |
    | report | 보고서 |
    | Work Plan | 작업 계획 |
    | draft TR | Technical Report 초안 |
    | draft TS | Technical Specification 초안 |
    | agenda | 회의 안건표 |
    | WI summary | Work Item 요약 |
    | response | 응답 문서 |
    | CR pack | CR 번들 |
    | TS or TR cover | TS/TR 표지 |
    
    **RAN2 관측**: `CR pack` (1건), `TS or TR cover` (1건) 등 소수 유형 포함. `WID new`, `SID new`는 RAN2 전수 스캔 0건이므로 미정의.
    
    ### 8.2 status (결정 상태)
    
    | 값 | 설명 |
    | --- | --- |
    | available | 접수됨 (회의 전 상태) |
    | noted | 참고로 접수됨 |
    | not treated | 회의에서 다루지 않음 |
    | revised | 수정되어 새 버전으로 대체됨 |
    | agreed | 합의됨 |
    | endorsed | 지지/승인됨 |
    | postponed | 다음 회의로 연기됨 |
    | withdrawn | 제출자가 철회함 |
    | reserved | 예약됨 (번호만 할당) |
    | not pursued | 더 이상 추진하지 않음 |
    | approved | 공식 승인됨 |
    | merged | 다른 문서와 병합됨 |
    | treated | 처리됨 |
    | not concluded | 결론 미도출 |
    | conditionally agreed | 조건부 합의 |
    | reissued | 재발행됨 (RAN2 추가) |
    | rejected | 거부됨 (RAN2 추가) |
    
    **RAN2 대비 추가**: `reissued`, `rejected`
    
    ### 8.3 for (문서 목적)
    
    | 값 | 설명 |
    | --- | --- |
    | Decision | 결정 요청 |
    | Agreement | 합의 요청 |
    | Discussion | 논의 요청 |
    | Approval | 승인 요청 |
    | Action | 조치 요청 |
    | Endorsement | 지지 요청 |
    | Information | 정보 공유 |
    | Presentation | 발표용 |
    
    RAN1과 동일.
    
    ### 8.4 direction (LS 방향)
    
    | 값 | 설명 |
    | --- | --- |
    | out | 이 WG에서 다른 WG로 발신 |
    | in | 다른 WG에서 이 WG로 수신 |
    
    ### 8.5 crCategory (CR 카테고리)
    
    | 값 | 설명 |
    | --- | --- |
    | F | Correction (오류 수정) |
    | B | Addition of feature (기능 추가) |
    | A | Mirror CR (다른 Release에 동일 적용) |
    | D | Editorial change (편집상 변경) |
    | C | Functional modification of feature (기능 수정) |
    | E | Early implementation (조기 구현) |
    
    RAN1과 동일한 6개 값. (초기 Spec 작성 시 숫자 레거시 코드 1,2,3을 기재했으나, 전수 스캔 결과 0건으로 삭제함.)
    
    ### 8.6 releaseName (Release 값)
    
    | 값 |
    | --- |
    | Rel-20 |
    | Rel-19 |
    | Rel-18 |
    | Rel-17 |
    | Rel-16 |
    | Rel-15 |
    | Rel-14 |
    | Rel-13 |
    | Rel-12 |
    | Rel-11 |
    | Rel-10 |
    | Rel-9 |
    | Rel-8 |
    | Rel-5 |
    
    **RAN2 특이**: `Rel-5`는 RAN2 초기 미팅에서 레거시 Release 참조로 관측됨.
    
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
    | CR | (modifies는 0..* — pCR Spec null로 하한 0, 복수 Spec 병기로 상한 *) |
    
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
    - **예시 인스턴스**: RAN2 실제 데이터 기반 예시
    
    ---
    
    ## 2. 데이터 소스
    
    | 항목 | 내용 |
    | --- | --- |
    | 파일 | TDoc_List Excel (58개 미팅) |
    | 경로 | TDoc List Excel 입력 디렉토리 (미팅별 `.xlsx`) |
    | TDoc 총 수 | [P1-V01] (dedup 기준) |
    
    ---
    
    ## 3. 인스턴스 현황
    
    | 클래스 | 소스 |
    | --- | --- |
    | Meeting | 파일명 (RAN2#{N} 패턴) |
    | Release | Release 컬럼 (오염 필터 적용) |
    | Company | Source 컬럼 (정규화 후) |
    | Contact | Contact, Contact ID 컬럼 |
    | WorkItem | Related WIs 컬럼 |
    | AgendaItem | Agenda item 컬럼 |
    | Spec | Spec 컬럼 |
    | WorkingGroup | To, Cc 컬럼 |
    | Tdoc (일반) | Type이 discussion, other, report 등 |
    | CR | Type이 CR, draftCR, pCR |
    | LS | Type이 LS out 또는 LS in |
    
    ---
    
    ## 4. 생성 순서
    
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
    | Meeting | meetingNumber | `{WG}#{회차}[-e]` | RAN2#120, RAN2#101bis-e |
    | Release | releaseName | `Rel-{번호}` | Rel-18, Rel-19 |
    | Company | companyName | 정규화된 회사명 | Samsung, Huawei |
    | Contact | contactId | 3GPP 시스템 ID | 52292 |
    | WorkItem | workItemCode | Work Item 코드 | NR_RRC_inactive-Core |
    | AgendaItem | meetingNumber + agendaNumber | (복합키) | RAN2#120-9.1 |
    | Spec | specNumber | Spec 번호 | 38.331, 38.321 |
    | WorkingGroup | wgName | WG 이름 | SA2 |
    | Tdoc, CR, LS | tdocNumber | `R2-{YYNNNNN}` | R2-2500001 |
    
    **RAN2 식별자 체계**: TDoc은 `R2-`, Meeting은 `RAN2#`, bis 접미사는 소문자 `bis`
    
    ---
    
    ## 6. 클래스별 인스턴스 생성 명세
    
    ### 6.1 Meeting
    
    | 항목 | 내용 |
    | --- | --- |
    | 소스 | 파일명 (TDoc_List_Meeting_RAN2#{N}.xlsx) |
    | ID | meetingNumber 원본 값 |
    
    | 속성 | 소스 | 변환 규칙 | 예시 |
    | --- | --- | --- | --- |
    | meetingNumber | 파일명에서 추출 | 원본 그대로 | "RAN2#101bis-e" |
    | canonicalMeetingNumber | meetingNumber | `-e` suffix 제거 | "RAN2#101bis" |
    | meetingNumberInt | canonicalMeetingNumber | `#` 뒤 숫자만 추출 (bis 제거) | 101 |
    | workingGroup | "RAN2" 고정 | - | "RAN2" |
    
    **RAN2 파일명 패턴**:
    - `TDoc_List_Meeting_RAN2#100.xlsx` → RAN2#100
    - `TDoc_List_Meeting_RAN2#101-Bis.xlsx` → RAN2#101bis (bis 소문자 정규화)
    - `TDoc_List_Meeting_RAN2#113-bis-e.xlsx` → RAN2#113bis-e → canonical: RAN2#113bis
    - `TDoc_List_RAN2#96_110217.xlsm` → RAN2#96 (날짜 suffix 무시)
    - `TDoc_List_Meeting_ RAN2#132.xlsx` → RAN2#132 (파일명 내 공백 trim)
    
    **bis 대소문자 정규화**: 파일명에 BIS, Bis, bis 3가지 변형 존재. 모두 소문자 `bis`로 통일.
    
    | 원본 | 정규화 |
    | --- | --- |
    | `-BIS` | `bis` |
    | `-Bis` | `bis` |
    | `-bis` | `bis` |
    
    ### 6.2 Release
    
    | 속성 | 소스 | 예시 |
    | --- | --- | --- |
    | releaseName | Release 컬럼 | "Rel-19" |
    
    **오염 필터**: Release 값이 "Rel-"로 시작하지 않으면 무시 (Step 1 §2.3 참조)
    **실제 값**: Rel-5, Rel-8, Rel-9, Rel-10, Rel-11, Rel-12, Rel-13, Rel-14, Rel-15, Rel-16, Rel-17, Rel-18, Rel-19, Rel-20
    
    ### 6.3 Company
    
    | 속성 | 소스 | 예시 |
    | --- | --- | --- |
    | companyName | Source에서 추출/정규화 | "Samsung" |
    
    **Source 특수 케이스 처리**:
    
    | Source 값 | 처리 | 근거 |
    | --- | --- | --- |
    | "Chairman" | 역할만 → Company 아님. 건너뜀 또는 역할로 분리 | 3건 확인 |
    | "MCC" | ETSI MCC (사무국) → Company로 처리 | 관례적 처리 |
    | "Moderator (Samsung)" | 역할 분리 → Company: Samsung | §9.2 파이프라인 |
    | "Rapporteur (Huawei, HiSilicon)" | 역할 분리 → Company: Huawei, HiSilicon | 괄호 내 쉼표 처리 |
    
    ### 6.4 Contact
    
    | 속성 | 소스 | 예시 |
    | --- | --- | --- |
    | contactName | Contact 컬럼 | "John Smith" |
    | contactId | Contact ID 컬럼 | "52292" |
    
    ### 6.5 WorkItem
    
    | 속성 | 소스 | 예시 |
    | --- | --- | --- |
    | workItemCode | Related WIs에서 추출 | "NR_RRC_inactive-Core" |
    
    ### 6.6 AgendaItem
    
    | 속성 | 소스 | 예시 |
    | --- | --- | --- |
    | agendaNumber | Agenda item 컬럼 | "9.1" |
    | agendaDescription | Agenda item description 컬럼 | "NR RRC" |
    
    **복합키**: `{meetingNumber}-{agendaNumber}` (같은 agendaNumber가 다른 미팅에서 다른 description을 가질 수 있음)
    
    ### 6.7 Spec
    
    | 속성 | 소스 | 예시 |
    | --- | --- | --- |
    | specNumber | Spec 컬럼 | "38.331" |
    | specVersion | Version 컬럼 (optional) | "18.5.0" |
    
    ### 6.8 WorkingGroup
    
    | 속성 | 소스 | 예시 |
    | --- | --- | --- |
    | wgName | To, Cc에서 추출 | "SA2" |
    
    ### 6.9 Tdoc (일반)
    
    | 항목 | 내용 |
    | --- | --- |
    | 조건 | Type이 discussion, other, report, agenda, Work Plan, draft TR, draft TS, response, WI summary, CR pack, TS or TR cover |
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
    | crRevision | CR revision | ❌ |
    | clausesAffected | Clauses Affected (최신 #120~) 또는 Phase-4 | ❌ |
    | tsgCRPack | TSG CR Pack | ❌ |
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
    
    ## 명명 규칙 (Naming Convention) — RAN2 Phase 1~11 공통
    
    | 레이어 | 규칙 | 예시 |
    | --- | --- | --- |
    | Spec 문서 (온톨로지 속성명) | camelCase | `tdocNumber`, `crNumber`, `presentedAt`, `belongsTo`, `clausesAffected` |
    | Neo4j 구현 (속성키) | snake_case 또는 camelCase (Phase별) | `presented_at`, `belongs_to` (Phase-1 초기). Phase-2 이후 속성은 camelCase 유지 |
    | JSON 중간 산출물 (파서 출력) | snake_case | `cr_number`, `reason_for_change`, `clauses_affected` (Phase-4/8 파서 raw) |
    | Qdrant payload | camelCase | `tdocNumber`, `sectionId`, `specNumber` (Phase-6~9) |
    | 외부 컬럼/원본 인용 | 원본 표기 유지 | "Clauses Affected" (TDoc_list 컬럼 헤더), "Source" (CR Form) |
    
    변환 규칙: Spec 속성(camelCase) ↔ JSON/DB 저장(스펙별 표기) 간 변환은 파서 레이어에서 담당.
    
    ### 공통 식별자 표기 (F-04/F-05/F-10 통일)
    
    | 개념 | 공식 용어 (Spec) | 동의 표기 (docs/본문) |
    | --- | --- | --- |
    | TDoc 번호 | `tdocNumber` (속성) | TDoc 번호 (사람 읽기) / Tdoc 번호 (오타, 지양) |
    | CR 번호 | `crNumber` (속성) | CR 번호 (사람 읽기) / `cr_number` (JSON 중간 산출물 키) |
    | 회의 식별자 | `canonicalMeetingNumber` (정규화 값, 예: RAN2#131bis) | `meetingNumber` (원본) / `meetingId` (Qdrant payload의 정규화된 값) |
    | Clauses Affected | `clausesAffected` (Spec 속성) | "Clauses Affected" (TDoc_list 원본 컬럼 인용 시) / `clauses_affected` (JSON 키) |
    
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
    | Spec | float (38.331) | 문자열 "38.331" |
    | CR | float (693.0) | 문자열 "693" |
    | Reservation date | 문자열 | ISO 8601 |
    | Uploaded | Timestamp | ISO 8601 |
    | CR revision | float (1.0) 또는 String ("2") | 문자열 "1", "2" (소수점 제거) |
    | UICC, ME, RAN, CN | Boolean | 그대로 |
    
    ### 7.3 클래스 판별
    
    | Type 값 | 클래스 |
    | --- | --- |
    | CR, draftCR, pCR | CR |
    | LS out, LS in | LS |
    | 그 외 | Tdoc |
    
    ### 7.4 Release 오염 필터 (RAN2 고유)
    
    | 조건 | 처리 |
    | --- | --- |
    | Release 값이 "Rel-"로 시작 | 정상 처리 |
    | Release 값이 "R2-"로 시작 | 무시 (TDoc 번호 혼입) |
    | Release 값이 빈 문자열 | targetRelease 관계 생성 안 함 |
    
    전수 스캔 결과 현재 오염 0건. 향후 새 데이터 대비 방어적 필터 유지.
    
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
    
    RAN1과 동일한 파이프라인. 동일한 3GPP 참여사이므로 정규화 사전도 대부분 공유 가능.
    
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
    
    **RAN2 Source 특이사항**:

    > 이하 건수·비율(37,383건, 31.4%)은 설계 시점 데이터 기준이며, 데이터 변경 시 갱신 대상이 아니다.
    > 현재 실측값은 구현 결과(파싱 로그)를 확인한다.

    - Source 빈값: 0건 (전수 스캔 확인, RAN1과 동일하게 모든 TDoc에 Source 존재)
    - Source 복합값: 37,383건 (31.4%) — 복수 회사 공동 제출
    - submittedBy Cardinality 0..*는 복합값 처리를 위한 것 (빈값 때문이 아님)
    
    ---
    
    ## 10. 예시 인스턴스
    
    ### 10.1 Meeting 예시
    
    ```json
    {
      "@type": "Meeting",
      "meetingNumber": "RAN2#120",
      "canonicalMeetingNumber": "RAN2#120",
      "meetingNumberInt": 120,
      "workingGroup": "RAN2"
    }
    ```
    
    ### 10.2 Tdoc 예시
    
    ```json
    {
      "@type": "Tdoc",
      "tdocNumber": "R2-2300001",
      "title": "Discussion on NR RRC enhancements",
      "type": "discussion",
      "status": "noted",
      "for": "Discussion",
      "submittedBy": [{ "@id": "company:Samsung" }],
      "hasContact": { "@id": "contact:52292" },
      "belongsTo": { "@id": "agenda:9.1" },
      "presentedAt": { "@id": "meeting:RAN2#120" },
      "relatedTo": [{ "@id": "workitem:NR_RRC_inactive-Core" }],
      "targetRelease": { "@id": "release:Rel-19" }
    }
    ```
    
    ### 10.3 CR 예시
    
    ```json
    {
      "@type": "CR",
      "tdocNumber": "R2-2300088",
      "title": "CR to 38.331 on RRC connection setup",
      "type": "CR",
      "status": "agreed",
      "for": "Agreement",
      "crNumber": "0693",
      "crCategory": "F",
      "crRevision": "2",
      "modifies": { "@id": "spec:38.331" },
      "submittedBy": [{ "@id": "company:Ericsson" }],
      "hasContact": { "@id": "contact:12345" },
      "belongsTo": { "@id": "agenda:8.1" },
      "presentedAt": { "@id": "meeting:RAN2#120" }
    }
    ```
    
    ### 10.4 LS 예시
    
    ```json
    {
      "@type": "LS",
      "tdocNumber": "R2-2300150",
      "title": "LS on RRC protocol enhancements",
      "type": "LS out",
      "status": "approved",
      "direction": "out",
      "sentTo": [{ "@id": "wg:SA2" }, { "@id": "wg:CT1" }],
      "ccTo": [{ "@id": "wg:SA2" }],
      "submittedBy": [{ "@id": "company:Qualcomm" }],
      "hasContact": { "@id": "contact:67890" },
      "belongsTo": { "@id": "agenda:8.5" },
      "presentedAt": { "@id": "meeting:RAN2#120" }
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
    | 총 Tdoc 수 | Appendix A [P1-V01] 참조 (dedup 기준, Tdoc·CR·LS 분류 합산) |
    
    ---
    
    ## 12. 요약
    
    ### 12.1 인스턴스 생성 명세
    
    | 클래스 | ID 패턴 | 데이터 소스 |
    | --- | --- | --- |
    | Meeting | `RAN2#{회차}[-e]` | 파일명 |
    | Release | `Rel-{번호}` | Release 컬럼 (오염 필터) |
    | Company | 정규화된 회사명 | Source 컬럼 |
    | Contact | 3GPP ID | Contact ID 컬럼 |
    | WorkItem | WI 코드 | Related WIs 컬럼 |
    | AgendaItem | Agenda 번호 | Agenda item 컬럼 |
    | Spec | Spec 번호 | Spec 컬럼 |
    | WorkingGroup | WG 이름 | To, Cc 컬럼 |
    | Tdoc | `R2-{YYNNNNN}` | TDoc 컬럼 |
    | CR | `R2-{YYNNNNN}` | TDoc 컬럼 (Type=CR/draftCR/pCR) |
    | LS | `R2-{YYNNNNN}` | TDoc 컬럼 (Type=LS in/out) |
    
    ### 12.2 변환 규칙 요약
    
    | 항목 | 규칙 |
    | --- | --- |
    | 복합 값 | 쉼표 분리 → 복수 관계 |
    | 타입 변환 | float → String, DateTime → ISO 8601 |
    | 클래스 판별 | Type 값 기반 (CR/LS/Tdoc) |
    | 정규화 | Company 정규화 사전 적용 |
    | Release 필터 | "Rel-" 접두사 없는 값 무시 (초기 미팅 오염) |
    | 컬럼명 정규화 | 초기 미팅 `TDoc #` → `TDoc` 매핑 |
    
    ---
    
    ## 13. 전체 완료
    
    Phase-1 온톨로지 설계가 완료되었습니다.
    Appendix A (기준 수치)는 Phase-G 회귀 전수 검증 시점 실측 완료. 시점은 각 V-ID 비고 참조.
    
    ---
    
    ## 14. Appendix ID 네이밍 규칙
    
    `P{n}-V{번호}` 형식. Phase 간 수치 참조 시 원본 Phase의 V-ID를 직접 참조한다.
    
    **V-ID 부여 조건** (3가지 모두 충족 시):
    - **가변성**: 데이터 추가/삭제에 따라 값이 변할 수 있는 수치
    - **필수성**: Spec 본문 또는 검증에서 참조하는 수치
    - **비자명성**: 코드에서 즉시 계산할 수 없어 명시적 기록이 필요한 수치
    
    **Phase별 V-ID 정책** (F-12 일관화):
    - Phase 1~11 모두 위 3조건을 동일 기준으로 적용한다
    - 파싱 커버리지 100%(예: P4-V09 tsgMeeting 추출률 100%)와 같이 "비자명성"이 약한 수치도, 구현 회귀 감지와 docs 자동 대조의 재현성을 위해 V-ID를 부여할 수 있다. 단, 비고에 "회귀 감지용" 명시.
    - 성능/소요시간 V-ID(예: P10-V07 E2E 소요시간)는 "환경 변화 시 재측정"이라는 조건부 참조 용도임을 비고에 명시한다.
    - Phase-11과 같이 자체 V-ID를 부여하지 않고 다른 Phase의 V-ID를 외부 참조(예: P4-V04)로 사용하는 경우에는 Appendix A에 "외부 참조 전용" 헤더를 둔다.
    
    ---
    
    ## Appendix A: 기준 수치
    
    > Phase-G 회귀 전수 검증 시점 실측치. 시점/근거는 비고 컬럼 참조.
    
    | ID | 항목 | 실측값 | 비고 |
    | --- | --- | --- | --- |
    | P1-V01 | 총 TDoc 수 (dedup) | 120,000 | 58개 파일, tdocNumber dedup 기준. Neo4j 실측 (Phase-G 회귀 전수 검증 시점, 이전 ~117,756 / 집계, +2,244) |
    | P1-V02 | TDoc List 파일 수 | 58 | #93-BIS, #95-BIS에 .xlsm/.xlsx 중복 포함 |
    | P1-V03 | Source 누락 건수 (submittedBy 없음) | 9,404 | 전체 120,000 중 7.84%. Neo4j 실측 (관계 SUBMITTED_BY 미생성 기준, 이전 7,160 / 117,756 = 6.08%는 집계, 분모 변동 반영) |
    | P1-V04 | sentTo 누락 건수 (LS out) | 388 | LS out 4,799 중 8.09%. Neo4j 실측 (Tdoc.type="LS out" 중 SENT_TO 미생성, 이전 363 / 4,774 = 7.6%는 집계) |
    | P1-V05 | 미팅 범위 | RAN2#93 ~ RAN2#132 | 58개 미팅 (bis 포함) |
    | P1-V06 | TDoc List 컬럼 분포 | 31~36개 (시기별: 초기 32, 중간 31, 최신 36; 비표준 변종 일부) | 파서 컬럼 인덱스 결정 근거 |
