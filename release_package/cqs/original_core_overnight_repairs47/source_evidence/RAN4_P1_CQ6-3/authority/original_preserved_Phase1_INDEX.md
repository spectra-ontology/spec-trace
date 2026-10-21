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
    
    **3GPP RAN4 회의 문서(Tdoc) 메타데이터와 그 관계**
    
    RAN4 (Radio Access Network WG4)은 NR의 RF 성능 요구사항, 전자파 적합성(EMC), 적합성 시험(Conformance Testing)을 정의한다.
    
    주요 Specification:
    - **38.101-1~5**: NR UE radio transmit and receive (Part 1-5)
    - **38.104**: NR Base Station radio transmit and receive
    - **38.113**: NR Base Station EMC
    - **38.141-1/2**: NR Base Station conformance testing
    - **38.133**: NR Requirements for support of radio resource management
    
    총 29개 TS (38.1xx 시리즈) — RF/EMC/Conformance 전담.
    
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
    | **Phase-1** | **Tdoc_list (Excel)** | Meeting [P1-V04]개, TDoc [P1-V01] (dedup 기준) |
    
    데이터 경로: TDoc List Excel 파일 (미팅별 `.xlsx`)
    
    ### 1.5 전제 조건
    
    - **R-J1**: Phase-1은 **TDoc List Excel 파일만** 입력으로 사용한다. Phase-0 Step-6의 DOC→DOCX 변환(Phase-6 TDoc 본문 대상)은 Phase-1의 선행 조건이 아니다. 따라서 Phase-1 재현 시 Phase-0 Step-6 완료를 기다릴 필요 없이 Excel 파일 배치만 확인하면 된다.
    - Phase-0 Step 중 Phase-1 필수 선행: **TDoc List Excel 수집(Step-2 Excel 다운로드) 완료 상태**
    - TDoc List Excel 파일 배치 완료 (대상 Meeting 수: [P1-V04])
    - Final Report 파일 배치 완료 (Phase-2에서 사용 — Phase-1은 해당 파일을 읽지 않음)
    
    ### 1.6 RAN4 데이터 특성
    
    | 항목 | **RAN4** |
    | --- | --- |
    | TDoc 접두사 | **R4-NNNNNNN (7자리)** |
    | 미팅 폴더 | **TSGR4_{N}** |
    | 미팅 범위 | **#78~#117 + bis 변종 (TDoc List 및 Final Report 파일, 총 58 미팅 [P1-V04])** |
    | bis 접미사 | **bis 6변종: Bis, bis, bis-e, bis_e, -bis-e, _eBis** |
    | TDoc List 컬럼 | **시기별 변동 (표준 분포 + 비표준 변종 일부; 분포는 [P1-V18] 참조)** |
    | TDoc 총 수 | [P1-V01] (dedup) |
    | CR 비중 | CR 수([P1-V02]) / TDoc 수([P1-V01]) 비율 |
    | 핵심 TS | **38.1xx (RF, EMC, Conformance)** |
    | Source 복합값 | 비중 높음 (Company 정규화 필요) |
    | CR revision | 부분 보유 (CR 대비 일부) |
    
    **RAN4 고유 특성**:
    - **TDoc 번호 7자리**: `R4-\d{7}` 전용 패턴 사용
    - **discussion 비중 높음**: 논의 중심 문서 비중이 다른 WG 대비 크다
    - **Status 값 풍부**: noted, available, revised, agreed, endorsed 등 다수 값 공존
    - **For: Endorsement/Decision**: RAN4에서 유의미한 Enum 값
    - **bis 6변종**: Bis, bis, bis-e, bis_e, -bis-e, _eBis → 정규화 필수 (소문자 통일 + 구분자 제거)
    - **비표준 컬럼 파일 2개**: 8컬럼(#107Bis-e), 12컬럼 → 파서에서 <10컬럼 스킵
    - **Backfill 이력**: Phase-1 backfill [P1-V17] (신규 미팅 + 누락 Tdoc 보완), Phase-4 backfill [P1-V16] (Phase-1 Tdoc List 미존재 CR 추가) — Phase-4 [P4-V09]에서 backfill 별건 명시
    
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
    
    ### 2.2 데이터 품질 이슈
    
    | 이슈 | 영향 | 처리 방안 |
    | --- | --- | --- |
    | **TDoc 번호 7자리** | `R4-\d{7}` 전용 패턴 사용 필요 | `R4-\d{7}` 전용 패턴 사용 |
    | **bis 접미사 6변종** | 미팅 번호 추출 실패 가능 | 정규화: Bis, bis, bis-e, bis_e, -bis-e, _eBis → 표준 bis로 통일 (소문자 + 구분자/`_e` 제거) |
    | **비표준 컬럼 파일 2개** | 8컬럼(#107Bis-e), 12컬럼 | <10컬럼 파일 스킵 (122행 손실 허용) |
    | **컬럼 수 시기별 변화** | 31→32→36 (초기 1개: 32, 주류 33개: 31, 최신 22개: 36) | 컬럼명 정규화, 36컬럼 파일에서 Clauses Affected 확보 |
    | **Source 복합값 비중 높음** | Company 정규화 필요 | 쉼표 분리 + LLM 정규화 |
    | **crCategory 레거시 숫자** | 1/2/3 코드 소수 잔존 | F/A/B/C/D 표준 + 1/2/3 레거시 허용 |
    | **전자회의 접미사 혼재** | `-e`, `_e`, `bis-e`, `bis_e` | 미팅 번호 추출 시 접미사 정규화 |
    | **파일명 비표준 8개** | 미팅 번호 추출 실패 가능 | 파일명 패턴 분기 (TDoc_List_Meeting_RAN4#N / RAN4#N_TDoc / R4-NNNNNNN / 3GPPRAN4#N) |
    | **Contact 빈값 존재** | Contact 연결 불가 | hasContact 관계 0..* 처리 |
    
    ---
    
    ## 3. Competency Questions
    
    RAN4 TDoc List 컬럼 구조(31개 기본)를 기반으로 다음 CQ 체계를 사용한다.
    
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
    
    *CQ2-5: CR category는 Phase-1 TDoc List에서 확보. Clauses Affected는 최신 미팅(36컬럼 파일 22개)의 TDoc List에서 확보 + 나머지는 Phase-4 CR 문서 파싱에서.*
    
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
    
    *참고: "Meeting 번호 DESC"는 `meetingNumberInt` 속성으로 정렬해야 숫자 기반 정렬이 보장됨 (문자열 정렬 시 #99 > #130 문제 발생)*
    
    // ★ 최신 우선 원칙: 명시적 요청 없으면 항상 DESC
    
    ### 4.2 결과 개수 (Default Limit)
    
    | CQ 유형 | 기본값 | 적용 CQ |
    | --- | --- | --- |
    | 목록 조회 | 10 | 1-1 ~ 1-5, 1-9, 2-1 ~ 2-3, 2-6 ~ 2-7, 3-1 ~ 3-2, 3-5, 4-1, 4-3 |
    | 단일 조회 | 1 | 1-6 ~ 1-8, 2-4 ~ 2-5 |
    | 집계/순위 | 10 | 3-3 ~ 3-4, 3-6, 4-2 |
    
    ---
    
    ## 5. CQ vs Tdoc 메타데이터 검증
    
    RAN4 TDoc List 컬럼 구조(31개 기본)를 기준으로 각 CQ의 데이터 소스를 검증한다.
    
    | # | Competency Question | 필요한 데이터 | 컬럼 존재 | 답변 가능 | 비고 |
    | --- | --- | --- | --- | --- | --- |
    | **CQ1. Tdoc 기본 검색** | | | | | |
    | 1-1 | 특정 회의에서 특정 Work Item 관련 Tdoc 목록은? | Meeting, Related WIs | ✅ | ✅ | Meeting은 파일명에서 추출 |
    | 1-2 | 특정 회의에서 특정 Agenda Item 관련 Tdoc 목록은? | Meeting, Agenda item | ✅ | ✅ | |
    | 1-3 | 특정 회의에서 특정 회사가 제출한 Tdoc 목록은? | Meeting, Source | ✅ | ✅ | |
    | 1-4 | 특정 Release에서 논의된 Tdoc 목록은? | Release | ✅ | ✅ | |
    | 1-5 | 특정 회의에서 승인/합의된 Tdoc 목록은? | Meeting, TDoc Status | ✅ | ✅ | |
    | 1-6 | 특정 Tdoc의 결정 결과(Status)는? | TDoc Status | ✅ | ✅ | |
    | 1-7 | 특정 Tdoc의 목적(For)은? | For | ✅ | ✅ | |
    | 1-8 | 특정 Tdoc의 담당자(Contact)는? | Contact | ✅ | ✅ | 빈값 존재 |
    | 1-9 | 이번 회의 전체 Agenda 목록과 설명은? | Agenda item, description | ✅ | ✅ | |
    | **CQ2. Tdoc 관계 추적** | | | | | |
    | 2-1 | 특정 Tdoc의 이전/이후 revision은? | Is revision of, Revised to | ✅ | ✅ | |
    | 2-2 | 특정 LS가 어디서 왔고 어디로 갔나? | Original LS, To, Cc | ✅ | ✅ | |
    | 2-3 | 특정 Tdoc이 어떤 LS의 답변(Reply)인가? | Reply to, Reply in | ✅ | ✅ | |
    | 2-4 | 특정 Tdoc이 어떤 TS/Spec을 변경하나? | Spec | ✅ | ✅ | |
    | 2-5 | 특정 CR의 카테고리와 영향 범위는? | CR category, Clauses Affected | △ | △ | CR category: TDoc List. Clauses Affected: 36컬럼 파일(22개) + Phase-4 |
    | 2-6 | 이번 회의에서 다음 회의로 연기된 Tdoc은? | TDoc Status (postponed) | ✅ | ✅ | |
    | 2-7 | 이번 회의에 들어온 LS 목록과 관련 Agenda Item은? | Type (LS in), Agenda item | ✅ | ✅ | |
    | **CQ3. 회사/경쟁사 분석** | | | | | |
    | 3-1 ~ 3-6 | 회사/경쟁사 분석 | Source, Related WIs, Agenda, Status | ✅ | ✅ | Source 복합값 비중 높음 → 정규화 필수 |
    | **CQ4. 히스토리/요약** | | | | | |
    | 4-1 ~ 4-3 | 히스토리/요약 | 여러 회의 데이터, Source, Status, Agenda | ✅ | ✅ | |
    
    ---
    
    ## 6. 검증 결과
    
    ### 6.1 발견된 문제와 해결
    
    | 문제 | 해당 CQ | 해결 방법 | 상태 |
    | --- | --- | --- | --- |
    | **Meeting 컬럼 없음** | 1-1, 1-2, 1-3, 1-5 | Meeting 클래스 추가 (Step 4). 파일명에서 회의 정보 추출 | ✅ 해결 |
    | **여러 회의 데이터 필요** | 4-1 | 온톨로지 구조는 지원. 전체 미팅 데이터 로드 시 답변 가능 | △ 구조 지원 |
    | **Clauses Affected 부분 확보** | 2-5 | 36컬럼 파일 22개에서 확보. 나머지는 Phase-4에서 보완 | △ Phase-4 보완 |
    | **TDoc 번호 7자리** | 전체 | `R4-\d{7}` 정규식 적용. Step 7에서 상세 정의 | ✅ 해결 |
    | **비표준 컬럼 파일** | 전체 | <10컬럼 스킵 (2개 파일, 122행) | ✅ 해결 |
    
    ### 6.2 결론
    
    RAN4 TDoc List 컬럼 구조(기본 31개)를 기준으로 모든 CQ에 대해 데이터 소스가 확인됨.
    RAN4 특화 이슈(7자리 TDoc, bis 6변종, 비표준 파일, Source 37% 복합값)는 파싱 단계(Step 7)에서 처리.
    
    ---
    
    ## Step 2: 기존 Ontology 재사용 검토
    
    > Ontology 101 원칙
    >
    >
    > *"It is almost always worth considering what someone else has done and checking if we can refine and extend existing sources for our particular domain and task."*
    >
    > — Noy & McGuinness, Ontology Development 101
    >
    
    ---
    
    ## 1. 검토 결과
    
    3GPP TDoc 도메인 전용 Ontology 존재 여부 조사 결과:
    
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
    
    ## Step 3: 중요 용어 나열
    
    > Ontology 101 원칙
    >
    >
    > *"It is useful to write down a list of all terms we would like either to make statements about or to explain to a user."*
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
    | 파일 | Tdoc_list Excel (Meeting [P1-V04]개, 비표준 파일 일부 제외) |
    | 경로 | TDoc List Excel 입력 디렉토리 (미팅별 `.xlsx`) |
    | 컬럼 | 시기별 변동 (표준 분포 + 비표준 변종 일부; 분포 — [P1-V18]) |
    | TDoc 총 수 | [P1-V01] (dedup 기준) |
    
    ---
    
    ## 3. 용어 나열
    
    ### 3.1 클래스 후보
    
    | 용어 | 데이터 소스 | 채울 수 있나? | 비고 |
    | --- | --- | --- | --- |
    | Tdoc | TDoc 컬럼 | ✅ | 상위 클래스 |
    | CR | Type 컬럼 (CR, draftCR, pCR) | ✅ | Tdoc 하위 클래스 |
    | LS | Type 컬럼 (LS in, LS out) | ✅ | Tdoc 하위 클래스 |
    | Meeting | 파일명에서 추출 | ✅ | RAN4#{N} 패턴 |
    | Company | Source 컬럼 | ✅ | 파싱/정규화 필요 (**복합 값 비중 높음**) |
    | Contact | Contact 컬럼 | ✅ | 빈값 존재 |
    | WorkItem | Related WIs 컬럼 | ✅ | 파싱 필요 |
    | AgendaItem | Agenda item 컬럼 | ✅ | 빈값 소수 존재 |
    | Release | Release 컬럼 | ✅ | Rel-12~20 범위 |
    | Spec | Spec 컬럼 | ✅ | |
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
    | originatedFrom | Original LS에서 추출 | LS → WorkingGroup | ✅ |
    
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
    | ~~note~~ | ~~Secretary Remarks~~ | ~~Tdoc~~ | Step 3 후보에서 제거 (E-1) |
    | contactId | Contact ID | Contact | ✅ |
    | contactName | Contact | Contact | ✅ |
    | agendaNumber | Agenda item | AgendaItem | ✅ |
    | agendaDescription | Agenda item description | AgendaItem | ✅ |
    | specNumber | Spec | Spec | ✅ |
    | specVersion | Version | Spec | ✅ |
    | crNumber | CR | CR | ✅ |
    | crRevision | CR revision | CR | ✅ (일부 보유) |
    | crCategory | CR category | CR | ✅ (F/A/B/C/D + 레거시 1/2/3) |
    | clausesAffected | (36컬럼 파일 22개 + Phase-4) | CR | △ 부분 확보 |
    | tsgCRPack | TSG CR Pack | CR | ✅ |
    | direction | Type에서 추출 | LS | ✅ |
    | specTitle | (외부 데이터/동적 생성) | Spec | ✅ |
    
    ### 3.4 CR 영향 범위 속성
    
    | 용어 | 데이터 소스 | 대상 클래스 | 채울 수 있나? |
    | --- | --- | --- | --- |
    | affectsUICC | UICC | CR | ✅ (36컬럼 파일 22개) |
    | affectsME | ME | CR | ✅ (36컬럼 파일 22개) |
    | affectsRAN | RAN | CR | ✅ (36컬럼 파일 22개) |
    | affectsCN | CN | CR | ✅ (36컬럼 파일 22개) |
    
    ### 3.5 Meeting 속성
    
    | 용어 | 데이터 소스 | 대상 클래스 | 채울 수 있나? |
    | --- | --- | --- | --- |
    | meetingNumber | 파일명 (RAN4#{N}) | Meeting | ✅ |
    | canonicalMeetingNumber | meetingNumber에서 정규화 | Meeting | ✅ |
    | meetingNumberInt | canonicalMeetingNumber에서 추출 | Meeting | ✅ |
    | workingGroup | "RAN4" 고정 | Meeting | ✅ |
    
    ### 3.6 기타 클래스 속성
    
    | 용어 | 데이터 소스 | 대상 클래스 | 채울 수 있나? |
    | --- | --- | --- | --- |
    | companyName | Source 파싱 | Company | ✅ |
    | aliases | Company 정규화 | Company | ✅ |
    | workItemCode | Related WIs 파싱 | WorkItem | ✅ |
    | releaseName | Release | Release | ✅ |
    | wgName | To, Cc 파싱 | WorkingGroup | ✅ |
    
    ---
    
    ## 4. 제외 항목
    
    | 컬럼 | 제외 이유 |
    | --- | --- |
    | Agenda item sort order | 정렬용, Ontology 불필요 |
    | TDoc sort order within agenda item | 정렬용, Ontology 불필요 |
    
    **CR revision**: RAN4에서 CR 대비 유의미한 비중으로 존재. **제외하지 않음**. §3.3에 `crRevision` 속성으로 포함.
    
    ---
    
    ## 5. 파싱 필요 항목
    
    | 컬럼 | 이유 | 예시 |
    | --- | --- | --- |
    | Source | 복합 값 (비중 높음) | "Huawei, HiSilicon" → 2개 Company |
    | Related WIs | 복합 값 | "NR_RF_FR2_req_Ph3, NR_BS_RF_Part2_EIRP_OTA" → 2개 WorkItem |
    | To | 복합 값 | 쉼표로 구분된 다중 WorkingGroup |
    | Cc | 복합 값 | 쉼표로 구분된 다중 WorkingGroup |
    | Release | 방어 필터 | "Rel-" 접두사 없는 값 필터링 |
    
    ### 5.1 RAN4 Type 분포
    
    | Type | 처리 |
    | --- | --- |
    | discussion | Tdoc (상위 클래스) |
    | CR | CR (하위 클래스) |
    | other | Tdoc (상위 클래스) |
    | draftCR | CR (하위 클래스) |
    | pCR | CR (하위 클래스) |
    | LS out | LS (하위 클래스) |
    | LS in | LS (하위 클래스) |
    | response | Tdoc (상위 클래스) |
    | Work Plan | Tdoc (상위 클래스) |
    | draft TR | Tdoc (상위 클래스) |
    | report | Tdoc (상위 클래스) |
    | draft TS | Tdoc (상위 클래스) |
    | agenda | Tdoc (상위 클래스) |
    | WID new | Tdoc (상위 클래스) |
    
    ### 5.2 RAN4 Status 분포
    
    | Status | 처리 |
    | --- | --- |
    | noted | Data Property |
    | available | Data Property |
    | revised | Data Property |
    | agreed | Data Property |
    | endorsed | Data Property |
    | reserved | Data Property |
    | withdrawn | Data Property |
    | endorsed (BL) | Data Property |
    | not pursued | Data Property |
    | approved | Data Property |
    
    ### 5.3 RAN4 For 분포
    
    | For | 처리 |
    | --- | --- |
    | Agreement | Data Property |
    | Discussion | Data Property |
    | Approval | Data Property |
    | **Endorsement** | Data Property **(RAN4에서 유의미)** |
    | **Decision** | Data Property **(RAN4에서 유의미)** |
    | Information | Data Property |
    
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
    
    총 11개 클래스.
    
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
    | 추가 속성 | ✅ | crNumber, crCategory, crRevision, clausesAffected, tsgCRPack, affectsUICC, affectsME, affectsRAN, affectsCN |
    | 다른 관계 | ✅ | modifies → Spec |
    | 해당 Type | - | 'CR', 'draftCR', 'pCR' |
    
    **RAN4 특성**: crRevision은 CR 대비 일부 보유. CR 비중은 타 WG 대비 높은 편. crCategory는 F/A/B/C/D + 레거시 1/2/3 소수 잔존.
    
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
    | discussion | Tdoc | type = 'discussion' |
    | **CR** | **CR** | — |
    | other | Tdoc | type = 'other' |
    | draftCR | CR | crNumber가 null |
    | pCR | CR | crNumber가 null |
    | LS out | LS | direction = 'out' |
    | LS in | LS | direction = 'in' |
    | response | Tdoc | type = 'response' |
    | Work Plan | Tdoc | type = 'Work Plan' |
    | draft TR | Tdoc | type = 'draft TR' |
    | report | Tdoc | type = 'report' |
    | draft TS | Tdoc | type = 'draft TS' |
    | agenda | Tdoc | type = 'agenda' |
    | WID new | Tdoc | type = 'WID new' |
    
    ### 인스턴스 분포 요약
    
    | 클래스 | 기준 수치 |
    | --- | --- |
    | Tdoc (직접) | Appendix A 참조 ([P1-V01]에서 CR·LS 제외한 나머지) |
    | CR | [P1-V02] |
    | LS | [P1-V03] |
    
    *CR = CR + draftCR + pCR. LS = LS out + LS in. 총합은 [P1-V01].*
    
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
    | submittedBy | Company | Source | Tdoc을 제출한 회사/조직. 복수 회사가 공동 제출 가능 (복합값 비중 높음) |
    | hasContact | Contact | Contact | Tdoc의 담당자 (빈값 존재) |
    | relatedTo | WorkItem | Related WIs | Tdoc이 관련된 Work Item. 다대다 |
    | belongsTo | AgendaItem | Agenda item | Tdoc이 논의되는 Agenda Item (빈값 소수 존재) |
    | targetRelease | Release | Release | Tdoc이 대상으로 하는 3GPP Release (Rel-12~20) |
    | presentedAt | Meeting | 파일명 | Tdoc이 발표/논의된 3GPP 회의 |
    | isRevisionOf | Tdoc | Is revision of | 이 Tdoc이 수정한 이전 버전 Tdoc |
    | revisedTo | Tdoc | Revised to | 이 Tdoc을 수정한 이후 버전 Tdoc. isRevisionOf의 역관계 |
    | replyTo | Tdoc | Reply to | 이 Tdoc이 답변하는 대상 Tdoc |
    | replyIn | Tdoc | Reply in | 이 Tdoc에 대한 답변 Tdoc (replyTo의 역관계) |
    
    ### 3.2 Data Property
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | tdocNumber | String | TDoc | Tdoc의 고유 식별자. **형식: R4-NNNNNNN (7자리)** |
    | title | String | Title | Tdoc의 제목 |
    | abstract | String | Abstract | Tdoc의 요약 |
    | type | String (Enum) | Type | Tdoc의 유형 (§5.1 분포 참조) |
    | status | String (Enum) | TDoc Status | 회의에서의 결정 결과 (§5.2 분포 참조) |
    | for | String (Enum) | For | Tdoc의 목적/용도 (§5.3 분포 참조) |
    | reservationDate | DateTime | Reservation date | Tdoc 번호 예약 일시 |
    | uploadedDate | DateTime | Uploaded | Tdoc 파일 업로드 일시 |
    | secretaryRemarks | String | Secretary Remarks | 회의 비서의 메모 |
    
    ---
    
    ## 4. CR 클래스 속성 (Tdoc 상속 + 추가)
    
    ### 4.1 추가 Object Property
    
    | 속성명 | Range | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | modifies | Spec | Spec | CR이 변경을 요청하는 대상 기술 규격 (예: 38.101-1) |
    
    ### 4.2 추가 Data Property
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | crNumber | String | CR | CR의 공식 번호. draftCR/pCR은 이 값이 없음 |
    | crCategory | String (Enum) | CR category | CR의 카테고리 (F/A/B/C/D + 레거시 1/2/3) |
    | crRevision | String | CR revision | CR의 수정 횟수 (일부 보유) |
    | clausesAffected | String | TDoc List (36컬럼 22개) 또는 Phase-4 | 영향받는 조항 번호 |
    | tsgCRPack | String | TSG CR Pack | TSG에 제출되는 CR Pack 번호 |
    | affectsUICC | Boolean | UICC | UICC 영향 여부 (36컬럼 파일만) |
    | affectsME | Boolean | ME | ME 영향 여부 (36컬럼 파일만) |
    | affectsRAN | Boolean | RAN | RAN 영향 여부 (36컬럼 파일만) |
    | affectsCN | Boolean | CN | CN 영향 여부 (36컬럼 파일만) |
    
    ---
    
    ## 5. LS 클래스 속성 (Tdoc 상속 + 추가)
    
    ### 5.1 추가 Object Property
    
    | 속성명 | Range | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | sentTo | WorkingGroup | To | LS의 수신 대상 Working Group. 복수 가능 |
    | ccTo | WorkingGroup | Cc | LS의 참조 대상 Working Group. 복수 가능 |
    | originalLS | Tdoc | Original LS | LS in의 경우, 다른 WG에서 보낸 원본 LS 문서 번호 |
    | originatedFrom | WorkingGroup | Original LS에서 WG 추출 | LS in의 발신 Working Group |
    
    ### 5.2 추가 Data Property
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | direction | String (Enum) | Type에서 추출 | LS의 방향. in(수신), out(발신) |
    
    ---
    
    ## 6. 기타 클래스 속성
    
    ### 6.1 Meeting
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | meetingNumber | String | 파일명 | 회의 번호 원본 (예: RAN4#120, RAN4#107Bis-e) |
    | canonicalMeetingNumber | String | meetingNumber에서 정규화 | 정규화된 회의 번호. `-e` suffix 제거, bis 소문자 통일 |
    | meetingNumberInt | Integer | canonicalMeetingNumber에서 추출 | 정렬용 숫자값 |
    | workingGroup | String | "RAN4" 고정 | 회의를 주관하는 Working Group |
    
    **Meeting ID 정규화 규칙 (RAN4 bis 6변종)**:
    
    | 원본 | canonicalMeetingNumber | meetingNumberInt | 설명 |
    | --- | --- | --- | --- |
    | RAN4#78Bis | RAN4#78bis | 78 | Bis→bis 정규화 (대문자→소문자) |
    | RAN4#108bis | RAN4#108bis | 108 | 변경 없음 |
    | RAN4#104bis-e | RAN4#104bis | 104 | -e 제거 |
    | RAN4#98bis_e | RAN4#98bis | 98 | _e 제거 |
    | RAN4#101-bis-e | RAN4#101bis | 101 | -bis-e → bis 정규화 |
    | RAN4#94_eBis | RAN4#94bis | 94 | _e 제거 + Bis→bis 정규화 |
    | RAN4#130 | RAN4#130 | 130 | 변경 없음 |
    
    ### 6.2 Company
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | companyName | String | Source 파싱 | 회사/조직의 정규화된 대표 이름 |
    | aliases | List<String> | company_aliases.json | 회사의 다른 이름/변형 목록 |
    
    ### 6.3 Contact
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | contactName | String | Contact | 담당자의 이름 |
    | contactId | String | Contact ID | 3GPP 시스템에서의 담당자 고유 ID |
    
    ### 6.4 WorkItem
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | workItemCode | String | Related WIs 파싱 | Work Item의 코드명 |
    
    ### 6.5 AgendaItem
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | agendaNumber | String | Agenda item | Agenda Item의 번호 |
    | agendaDescription | String | Agenda item description | Agenda Item의 설명 |
    
    ### 6.6 Release
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | releaseName | String | Release | 3GPP Release 버전명 (Rel-12~20 범위) |
    
    ### 6.7 Spec
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | specNumber | String | Spec | 기술 규격 번호 (예: 38.101-1, 38.104, 38.133) |
    | specVersion | String | Version | 규격의 버전 |
    | specTitle | String | (외부 데이터/동적 생성) | 기술 규격 제목 |
    
    ### 6.8 WorkingGroup
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | wgName | String | To, Cc 파싱 | Working Group 이름 |
    
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
    | 1 | tdocNumber | Tdoc | String | Tdoc 고유 식별자 (**R4-NNNNNNN**) |
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
    | submittedBy | Tdoc | Company | 0..* | ❌ | 복수 회사 공동 제출 가능 (복합값 비중 높음) |
    | hasContact | Tdoc | Contact | 0..* | ❌ | 빈값 존재 → 0..* |
    | relatedTo | Tdoc | WorkItem | 0..* | ❌ | 일부 Tdoc은 Related WIs 없음 |
    | belongsTo | Tdoc | AgendaItem | 0..1 | ❌ | 빈값 소수 존재 → 0..1 |
    | targetRelease | Tdoc | Release | 0..1 | ❌ | 일부 Tdoc은 Release 없음 |
    | presentedAt | Tdoc | Meeting | 1 | ✅ | 모든 Tdoc은 특정 회의에 속함 |
    | isRevisionOf | Tdoc | Tdoc | 0..1 | ❌ | 최초 버전은 없음 |
    | revisedTo | Tdoc | Tdoc | 0..* | ❌ | 분기 revision 가능 |
    | replyTo | Tdoc | Tdoc | 0..* | ❌ | 복수 답변 가능 |
    | replyIn | Tdoc | Tdoc | 0..* | ❌ | 복수 WG 답변 가능 |
    
    **RAN4 특이사항**: hasContact는 **0..*** (빈값 존재). belongsTo도 0..1 (빈값 소수 존재).
    
    ### 3.2 Data Property
    
    | 속성명 | Domain | Type | Cardinality | 필수 | 근거 |
    | --- | --- | --- | --- | --- | --- |
    | tdocNumber | Tdoc | String | 1 | ✅ | 고유 식별자 |
    | title | Tdoc | String | 1 | ✅ | 모든 Tdoc에 제목 존재 |
    | abstract | Tdoc | String | 0..1 | ❌ | 대부분 비어있음 |
    | type | Tdoc | String (Enum) | 1 | ✅ | 모든 Tdoc에 유형 존재 |
    | status | Tdoc | String (Enum) | 1 | ✅ | 모든 Tdoc에 상태 존재 |
    | for | Tdoc | String (Enum) | 0..1 | ❌ | 일부 Tdoc은 For 없음 |
    | reservationDate | Tdoc | DateTime | 0..1 | ❌ | 일부 없음 |
    | uploadedDate | Tdoc | DateTime | 0..1 | ❌ | 미업로드 문서 가능 |
    | secretaryRemarks | Tdoc | String | 0..1 | ❌ | 일부만 존재 |
    
    ---
    
    ## 4. CR 클래스 추가 속성 제약조건
    
    ### 4.1 Object Property
    
    | 속성명 | Domain | Range | Cardinality | 필수 | 근거 |
    | --- | --- | --- | --- | --- | --- |
    | modifies | CR | Spec | 0..* | ❌ | draftCR/pCR 일부 Spec null(하한 0). 관측상 단일 Spec이나 모델상 복수 Spec 병기 가능 (ontology tdoc:modifies 다중값) |
    
    ### 4.2 Data Property
    
    | 속성명 | Domain | Type | Cardinality | 필수 | 근거 |
    | --- | --- | --- | --- | --- | --- |
    | crNumber | CR | String | 0..1 | ❌ | draftCR은 CR 번호 미부여 |
    | crCategory | CR | String (Enum) | 0..1 | ❌ | 일부 미지정 (F/A/B/C/D + 레거시 1/2/3) |
    | crRevision | CR | String | 0..1 | ❌ | 일부 보유 |
    | clausesAffected | CR | String | 0..1 | ❌ | 36컬럼 파일(22개) + Phase-4 |
    | tsgCRPack | CR | String | 0..1 | ❌ | 승인된 CR만 |
    | affectsUICC | CR | Boolean | 0..1 | ❌ | 36컬럼 파일만 |
    | affectsME | CR | Boolean | 0..1 | ❌ | 36컬럼 파일만 |
    | affectsRAN | CR | Boolean | 0..1 | ❌ | 36컬럼 파일만 |
    | affectsCN | CR | Boolean | 0..1 | ❌ | 36컬럼 파일만 |
    
    ---
    
    ## 5. LS 클래스 추가 속성 제약조건
    
    ### 5.1 Object Property
    
    | 속성명 | Domain | Range | Cardinality | 필수 | 근거 |
    | --- | --- | --- | --- | --- | --- |
    | sentTo | LS | WorkingGroup | 0..* | ❌ | 수신처 없이 발신 케이스 존재 |
    | ccTo | LS | WorkingGroup | 0..* | ❌ | 참조는 선택사항 |
    | originalLS | LS | Tdoc | 0..1 | ❌ | LS in만 |
    | originatedFrom | LS | WorkingGroup | 0..1 | ❌ | LS in만 |
    
    ### 5.2 Data Property
    
    | 속성명 | Domain | Type | Cardinality | 필수 | 근거 |
    | --- | --- | --- | --- | --- | --- |
    | direction | LS | String (Enum) | 1 | ✅ | 모든 LS는 방향 있음 |
    
    ---
    
    ## 6. 기타 클래스 속성 제약조건
    
    ### 6.1 Meeting
    
    | 속성명 | Type | Cardinality | 필수 |
    | --- | --- | --- | --- |
    | meetingNumber | String | 1 | ✅ |
    | canonicalMeetingNumber | String | 1 | ✅ |
    | meetingNumberInt | Integer | 1 | ✅ |
    | workingGroup | String | 1 | ✅ |
    
    ### 6.2 Company
    
    | 속성명 | Type | Cardinality | 필수 |
    | --- | --- | --- | --- |
    | companyName | String | 1 | ✅ |
    | aliases | List<String> | 0..* | ❌ |
    
    ### 6.3 Contact
    
    | 속성명 | Type | Cardinality | 필수 |
    | --- | --- | --- | --- |
    | contactName | String | 1 | ✅ |
    | contactId | String | 1 | ✅ |
    
    ### 6.4~6.8: WorkItem, AgendaItem, Release, Spec, WorkingGroup
    
    | 클래스 | 속성 | Type | Cardinality | 필수 |
    | --- | --- | --- | --- | --- |
    | WorkItem | workItemCode | String | 1 | ✅ |
    | AgendaItem | agendaNumber | String | 1 | ✅ |
    | AgendaItem | agendaDescription | String | 1 | ✅ |
    | Release | releaseName | String | 1 | ✅ |
    | Spec | specNumber | String | 1 | ✅ |
    | Spec | specVersion | String | 0..1 | ❌ |
    | Spec | specTitle | String | 0..1 | ❌ |
    | WorkingGroup | wgName | String | 1 | ✅ |
    
    ---
    
    ## 7. Inverse Property (역관계)
    
    | 속성 | 역속성 | 설명 |
    | --- | --- | --- |
    | isRevisionOf | revisedTo | revision 관계 |
    | replyTo | replyIn | LS 답변 관계 |
    
    ---
    
    ## 8. Enumeration (열거형)
    
    ### 8.1 type (Tdoc 유형)
    
    | 값 | 설명 |
    | --- | --- |
    | discussion | 일반 기술 제안/논의 문서 |
    | CR | 공식 Change Request |
    | other | 기타 문서 |
    | draftCR | Change Request 초안 |
    | pCR | Proposed CR |
    | LS out | 발신 Liaison Statement |
    | LS in | 수신 Liaison Statement |
    | response | 응답 문서 |
    | Work Plan | 작업 계획 |
    | draft TR | Technical Report 초안 |
    | report | 보고서 |
    | draft TS | Technical Specification 초안 |
    | agenda | 회의 안건표 |
    | WID new | 신규 Work Item 제안 |
    
    ### 8.2 status (결정 상태)
    
    | 값 | 설명 |
    | --- | --- |
    | noted | 참고로 접수됨 |
    | available | 접수됨 |
    | revised | 수정됨 |
    | agreed | 합의됨 |
    | endorsed | 지지/승인됨 |
    | reserved | 예약됨 |
    | withdrawn | 철회됨 |
    | **endorsed (BL)** | **Baseline 승인** |
    | **not pursued** | **추진 중단** |
    | approved | 공식 승인됨 |
    
    **공통 Status (RAN3/RAN4 등에서 사용)**: `endorsed (BL)`, `not pursued`.
    
    ### 8.3 for (문서 목적)
    
    | 값 | 설명 |
    | --- | --- |
    | Agreement | 합의 요청 |
    | Discussion | 논의 요청 |
    | Approval | 승인 요청 |
    | **Endorsement** | **지지 요청** |
    | **Decision** | **결정 요청** |
    | Information | 정보 공유 |
    
    **RAN4 고유**: Endorsement와 Decision이 유의미한 비중.
    
    ### 8.4 direction (LS 방향)
    
    | 값 | 설명 |
    | --- | --- |
    | out | 발신 |
    | in | 수신 |
    
    ### 8.5 crCategory (CR 카테고리)
    
    | 값 | 설명 |
    | --- | --- |
    | F | Correction (오류 수정) |
    | B | Addition of feature (기능 추가) |
    | A | Mirror CR |
    | D | Editorial change |
    | C | Functional modification |
    | 1 | 레거시 코드 |
    | 2 | 레거시 코드 |
    | 3 | 레거시 코드 |
    
    **레거시 코드(1/2/3)**: 극소수 잔존. Data Property로 그대로 저장 (변환하지 않음).
    
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
    | Rel-8 |
    
    **RAN4 Release 범위**: Rel-8~20. Rel-8 이하는 레거시 극소수.
    
    ---
    
    ## 9. 필수 속성 요약
    
    ### 9.1 필수 Data Property
    
    | 클래스 | 필수 속성 |
    | --- | --- |
    | Tdoc | tdocNumber, title, type, status |
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
    | Tdoc | presentedAt |
    | CR | — (modifies는 0..* — pCR Spec null로 하한 0, 복수 Spec 병기로 상한 *) |
    
    **RAN4 특이사항**: hasContact와 belongsTo는 빈값이 있어 Cardinality 0..*/0..1로 정의.
    
    ---
    
    ## 10. Functional Property 요약
    
    | 속성 | Domain | Range | 설명 |
    | --- | --- | --- | --- |
    | targetRelease | Tdoc | Release | 하나의 Release만 대상 |
    | presentedAt | Tdoc | Meeting | 하나의 회의에만 발표 |
    | isRevisionOf | Tdoc | Tdoc | 이전 버전은 1개 |
    | originalLS | LS | Tdoc | 원본 LS는 1개 |
    | originatedFrom | LS | WorkingGroup | 발신 WG는 1개 |
    
    **RAN4 특이사항**: hasContact와 belongsTo는 Functional에서 제외됨 (빈값 존재로 0..*/0..1).
    
    ---
    
    ## Step 7: 인스턴스 생성 명세
    
    > Ontology 101 원칙
    >
    >
    > *"The last step is creating individual instances of classes in the hierarchy."*
    >
    > — Noy & McGuinness, Ontology Development 101
    >
    
    ---
    
    ## 1. Step 7 목적
    
    - Step 4~6에서 정의한 클래스, 속성, 제약조건을 기반으로 **인스턴스 생성 규칙** 정의
    - **ID 생성 규칙**, **데이터 소스 매핑**, **변환 규칙**, **예시 인스턴스**
    - 이 문서만으로 구현자가 파서를 작성할 수 있어야 함
    
    ---
    
    ## 2. 데이터 소스
    
    | 항목 | 내용 |
    | --- | --- |
    | 파일 | TDoc_List Excel (Meeting [P1-V04]개, 비표준 파일 일부 제외) |
    | 경로 | TDoc List Excel 입력 디렉토리 (미팅별 `.xlsx`) |
    | 컬럼 | 시기별 변동 ([P1-V18] 참조) |
    | TDoc 총 수 | [P1-V01] (dedup 기준) |
    
    ---
    
    ## 3. 인스턴스 현황
    
    | 클래스 | 인스턴스 수 (추정) | 비고 |
    | --- | --- | --- |
    | Tdoc (직접) | [P1-V01] | dedup 기준 |
    | CR | [P1-V02] | CR + draftCR + pCR |
    | LS | [P1-V03] | LS in + LS out |
    | Meeting | [P1-V04] | 파일명 기준 |
    | Company | [P1-V05] | 정규화 후 |
    | Contact | [P1-V06] | contactId dedup |
    | WorkItem | [P1-V07] | Related WIs dedup |
    | AgendaItem | [P1-V08] | meeting + agendaNumber dedup |
    | Release | [P1-V09] | Rel-N dedup |
    | Spec | [P1-V10] | specNumber dedup |
    | WorkingGroup | [P1-V11] | wgName dedup |
    
    ---
    
    ## 4. 생성 순서
    
    | 순서 | 클래스 | 이유 |
    | --- | --- | --- |
    | 1 | Meeting, Release, Company, Contact, WorkItem, AgendaItem, Spec, WorkingGroup | 참조 대상 (의존성 없음) |
    | 2 | Tdoc, CR, LS | 참조 클래스 의존 |
    
    ---
    
    ## 5. ID 생성 규칙
    
    ### 5.1 ID 생성 원칙
    
    | 원칙 | 설명 |
    | --- | --- |
    | **유일성** | 동일 클래스 내에서 중복 불가 |
    | **불변성** | 한번 생성된 ID는 변경 불가 |
    | **의미성** | ID에서 의미 추론 가능 |
    | **추적성** | 원본 데이터로 역추적 가능 |
    
    ### 5.2 클래스별 ID 패턴
    
    | 클래스 | ID 속성 | 패턴 | 예시 |
    | --- | --- | --- | --- |
    | Tdoc | tdocNumber | `R4-NNNNNNN` | R4-2520000 |
    | CR | tdocNumber | `R4-NNNNNNN` | R4-2522758 |
    | LS | tdocNumber | `R4-NNNNNNN` | R4-2521699 |
    | Meeting | meetingNumber | `RAN4#NNN[bis]` | RAN4#130 |
    | Company | companyName | (정규화된 이름) | Samsung |
    | Contact | contactId | (3GPP ID) | 12345 |
    | WorkItem | workItemCode | (코드) | NR_RF_FR2_req_Ph3 |
    | AgendaItem | meetingNumber + agendaNumber | (복합키) | RAN4#130-8.1 |
    | Release | releaseName | `Rel-NN` | Rel-19 |
    | Spec | specNumber | `NN.NNN` | 38.101-1 |
    | WorkingGroup | wgName | (이름) | RAN4 |
    
    **RAN4 핵심**: TDoc ID가 **R4-NNNNNNN (7자리)**. 정규식: `R4-\d{7}`
    
    ---
    
    ## 6. 클래스별 인스턴스 생성 명세
    
    ### 6.1 Meeting
    
    | 속성 | 소스 | 변환 |
    | --- | --- | --- |
    | meetingNumber | 파일명 | `RAN4#(\d+)((?:[-_]?(?:bis|Bis)(?:[-_]e)?)|(?:_e[-]?[Bb]is)|(?:[-_]e))?` 패턴 (6변종 + `-e`/`_e` 단순 후미 모두 캡처) |
    | canonicalMeetingNumber | meetingNumber | `-e`/`_e` 제거, Bis→bis 정규화, `-bis`/`_eBis`/`-bis-e`→`bis` 정규화 |
    | meetingNumberInt | canonicalMeetingNumber | 숫자 부분 추출 (`\d+`) |
    | workingGroup | 고정 | "RAN4" |
    
    **파일명 패턴 분기** (4가지):
    
    | 패턴 | 예시 | 추출 방법 |
    | --- | --- | --- |
    | `TDoc_List_Meeting_RAN4#N.xlsx` | 주류 | `RAN4#(\d+)` |
    | `RAN4#N_TDoc_List_...xlsx` | 소수 | `RAN4#(\d+)` |
    | `R4-NNNNNNN_attachment_...xlsx` | 소수 | 파일명에 미팅 번호 없음 → 폴더명 또는 내부 데이터에서 추출 |
    | `3GPPRAN4#N_...xlsx` | 단건 | `RAN4#(\d+)` |
    
    **bis 6변종 정규화**:
    
    | 원본 | 정규화 | 규칙 |
    | --- | --- | --- |
    | `78Bis` | `78bis` | Bis→bis (대문자→소문자) |
    | `108bis` | `108bis` | 변경 없음 |
    | `104bis-e` | `104bis` | `-e` 제거 |
    | `98bis_e` | `98bis` | `_e` 제거 |
    | `101-bis-e` | `101bis` | `-` 제거 + `-e` 제거 |
    | `94_eBis` | `94bis` | `_e` 제거 + Bis→bis |
    
    ### 6.2 Release
    
    | 속성 | 소스 | 변환 |
    | --- | --- | --- |
    | releaseName | Release 컬럼 | "Rel-" 접두사 필터. Rel-8~20 범위 |
    
    ### 6.3 Company
    
    | 속성 | 소스 | 변환 |
    | --- | --- | --- |
    | companyName | Source | 쉼표 분리 → 각각 trim → 정규화 사전 적용 |
    | aliases | 정규화 사전 | LLM 기반 정규화 (§9 참조) |
    
    ### 6.4 Contact
    
    | 속성 | 소스 | 변환 |
    | --- | --- | --- |
    | contactName | Contact | 그대로 사용 |
    | contactId | Contact ID | 그대로 사용 |
    
    ### 6.5 WorkItem
    
    | 속성 | 소스 | 변환 |
    | --- | --- | --- |
    | workItemCode | Related WIs | 쉼표 분리 → 각각 trim |
    
    ### 6.6 AgendaItem
    
    | 속성 | 소스 | 변환 |
    | --- | --- | --- |
    | agendaNumber | Agenda item | 그대로 사용 |
    | agendaDescription | Agenda item description | 그대로 사용 |
    
    **복합키**: `{meetingNumber}-{agendaNumber}` (같은 agendaNumber가 다른 미팅에서 다른 description을 가질 수 있음)

    > **E-2 정책 (belongsTo 복합키 참조 규칙)**:
    > - **인스턴스 IRI**: `agendaitem/{meetingNumber}-{agendaNumber}` (예: `agendaitem/RAN4#130-8.1`)
    > - **Tdoc.belongsTo 참조값**: 상기 IRI의 **복합키 문자열**(`{meetingNumber}-{agendaNumber}`)을 사용한다. `agendaNumber` 단독 참조는 금지(미팅 간 동일 번호의 description 충돌 방지).
    > - **실측 카운트 차이 주의**: Spec Appendix A `[P1-V08]=6,539`(최초 적재)와 재적재 이후 Phase-1 README L24 `7,518`은 **분모/집계 시점이 다른 동일 클래스의 두 스냅샷**이다. 권위는 해당 스냅샷의 Neo4j 실측치이며, Spec Appendix A 값은 최초 적재 기준으로 유지한다(Phase-11 재적재 시 Appendix A는 일괄 갱신 대상 — 프로젝트 `active_completion_plan`에 따라 전체 재적재 후 일괄 반영).
    
    ### 6.7 Spec
    
    | 속성 | 소스 | 변환 |
    | --- | --- | --- |
    | specNumber | Spec 컬럼 | 그대로 사용 (예: 38.101-1, 38.104, 38.133) |
    | specVersion | Version 컬럼 | 그대로 사용 |
    | specTitle | 외부/동적 | 38.1xx 시리즈 제목 매핑 |
    
    ### 6.8 WorkingGroup
    
    | 속성 | 소스 | 변환 |
    | --- | --- | --- |
    | wgName | To, Cc 컬럼 | 쉼표 분리 → 표준 WG 이름 매핑 |
    
    ### 6.9 Tdoc (일반)
    
    **생성 조건**: Type이 CR/LS 이외인 경우 (discussion, other, report, draft TS/TR, Work Plan 등)
    
    | 속성 | 소스 | 변환 |
    | --- | --- | --- |
    | tdocNumber | TDoc | **`R4-\d{7}` 패턴 검증** |
    | title | Title | 그대로 |
    | abstract | Abstract | 그대로 (빈값 허용) |
    | type | Type | Enum 매핑 |
    | status | TDoc Status | Enum 매핑 |
    | for | For | Enum 매핑 (빈값 허용) |
    | reservationDate | Reservation date | DateTime 변환 |
    | uploadedDate | Uploaded | DateTime 변환 (빈값 허용) |
    | secretaryRemarks | Secretary Remarks | 그대로 (빈값 허용) |

    > **E-1 정책 (중복 속성 제거)**: Step 3 후보 단계의 `note`는 Step 5 정규화 시 **폐기**한다. 파서는 동일 원본 컬럼(Secretary Remarks)을 `secretaryRemarks` 단일 속성에만 기록하며, `note` 속성은 생성하지 않는다. 이는 §8 Data Property 최종 목록과 일치한다(§8에 `note` 부재 = 의도된 결과).
    
    **Object Property**:
    
    | 관계 | 소스 | 대상 | 변환 |
    | --- | --- | --- | --- |
    | submittedBy | Source | Company | 쉼표 분리 → Company MERGE |
    | hasContact | Contact | Contact | Contact ID 매칭 |
    | relatedTo | Related WIs | WorkItem | 쉼표 분리 → WorkItem MERGE |
    | belongsTo | Agenda item | AgendaItem | agendaNumber 매칭 |
    | targetRelease | Release | Release | releaseName 매칭 |
    | presentedAt | 파일명 | Meeting | meetingNumber 매칭 |
    | isRevisionOf | Is revision of | Tdoc | tdocNumber 참조 |
    | revisedTo | Revised to | Tdoc | tdocNumber 참조 |
    | replyTo | Reply to | Tdoc | tdocNumber 참조 |
    | replyIn | Reply in | Tdoc | tdocNumber 참조 |
    
    ### 6.10 CR (Tdoc 하위 클래스)
    
    **생성 조건**: Type이 'CR', 'draftCR', 'pCR' 중 하나
    
    **추가 속성** (Tdoc 속성 상속 + 아래 추가):
    
    | 속성 | 소스 | 변환 |
    | --- | --- | --- |
    | crNumber | CR | 그대로 (draftCR/pCR은 null) |
    | crCategory | CR category | F/A/B/C/D + 레거시 1/2/3 그대로 저장 |
    | crRevision | CR revision | 그대로 (빈값 허용) |
    | clausesAffected | Clauses Affected (36컬럼) | 그대로 (31컬럼 파일은 null) |
    | tsgCRPack | TSG CR Pack | 그대로 |
    | affectsUICC | UICC (36컬럼) | Boolean 변환 |
    | affectsME | ME (36컬럼) | Boolean 변환 |
    | affectsRAN | RAN (36컬럼) | Boolean 변환 |
    | affectsCN | CN (36컬럼) | Boolean 변환 |
    
    **추가 Object Property**:
    
    | 관계 | 소스 | 대상 | 변환 |
    | --- | --- | --- | --- |
    | modifies | Spec | Spec | specNumber 매칭 |
    
    ### 6.11 LS (Tdoc 하위 클래스)
    
    **생성 조건**: Type이 'LS out' 또는 'LS in'
    
    **추가 속성** (Tdoc 속성 상속 + 아래 추가):
    
    | 속성 | 소스 | 변환 |
    | --- | --- | --- |
    | direction | Type에서 추출 | 'LS out' → 'out', 'LS in' → 'in' |
    
    **추가 Object Property**:
    
    | 관계 | 소스 | 대상 | 변환 |
    | --- | --- | --- | --- |
    | sentTo | To | WorkingGroup | 쉼표 분리 → WG MERGE |
    | ccTo | Cc | WorkingGroup | 쉼표 분리 → WG MERGE |
    | originalLS | Original LS | Tdoc | tdocNumber 참조 |
    | originatedFrom | Original LS에서 WG prefix 추출 | WorkingGroup | TDoc 번호 접두사(`Xn-`)를 3GPP WG 이름으로 매핑 |
    
    ---
    
    ## 7. 데이터 변환 규칙
    
    ### 7.1 복합 값 처리
    
    | 컬럼 | 구분자 | 처리 |
    | --- | --- | --- |
    | Source | `,` | 각각 별도 Company 참조 |
    | Related WIs | `,` | 각각 별도 WorkItem 참조 |
    | To | `,` | 각각 별도 WorkingGroup 참조 |
    | Cc | `,` | 각각 별도 WorkingGroup 참조 |
    
    ### 7.2 타입 변환
    
    | 컬럼 | 원본 타입 | 변환 타입 | 규칙 |
    | --- | --- | --- | --- |
    | Reservation date | String | DateTime | ISO 8601 파싱 |
    | Uploaded | String | DateTime | ISO 8601 파싱 |
    | UICC/ME/RAN/CN | String | Boolean | "Yes"/"True" → true, else false |
    | CR revision | String/Number | String | 문자열로 통일 |
    
    ### 7.3 클래스 판별
    
    | Type 값 | 클래스 | 판별 규칙 |
    | --- | --- | --- |
    | CR, draftCR, pCR | CR | `type in ('CR', 'draftCR', 'pCR')` |
    | LS out, LS in | LS | `type in ('LS out', 'LS in')` |
    | 기타 | Tdoc | 위 조건에 해당하지 않는 모든 Type |
    
    ---
    
    ## 8. 참조 무결성 처리
    
    ### 8.1 내부 참조 (같은 데이터셋 내)
    
    | 관계 | 처리 |
    | --- | --- |
    | isRevisionOf/revisedTo | `R4-\d{7}` 패턴으로 검증. 같은 데이터셋에 없으면 dangling reference → 관계 생성 안 함 |
    | replyTo/replyIn | 동일 |
    
    ### 8.2 외부 참조 (다른 WG 문서)
    
    | 관계 | 처리 |
    | --- | --- |
    | originalLS | 다른 WG 문서번호(접두사 패턴) → WorkingGroup prefix 추출만. Tdoc 인스턴스는 생성하지 않음 |
    
    ---
    
    ## 9. Company 정규화
    
    ### 9.1 정규화 이슈
    
    | 이슈 | 예시 | 빈도 |
    | --- | --- | --- |
    | 대소문자 | samsung / Samsung / SAMSUNG | 높음 |
    | 약어/정식명 | HW / Huawei | 높음 |
    | 복합값 | "Huawei, HiSilicon" | 비중 높음 |
    | 역할 혼재 | "Moderator (Samsung)" | 존재 |
    | 사무국 | MCC | 관례적 처리 |
    
    ### 9.2 정규화 파이프라인
    
    ```
    Source 컬럼
        │
        ▼
    [1. 쉼표 분리]
        │
        ▼
    [2. trim + 대소문자 정규화]
        │
        ▼
    [3. 역할 패턴 제거] → "Moderator (Samsung)" → "Samsung"
        │
        ▼
    [4. LLM 기반 정규화] → 약어/변형 통합
        │
        ▼
    [5. 빈도 필터] → 유의미한 Company만
        │
        ▼
    [Company 인스턴스]
    ```
    
    위 파이프라인을 통해 Source 컬럼을 Company 인스턴스로 변환한다.
    
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
    
    **RAN4 Source 특이사항**:
    - Source 빈값: 소수 존재
    - Source 복합값: 비중 높음 — 복수 회사 공동 제출
    - Contact 빈값: 존재
    
    ---
    
    ## 10. 예시 인스턴스
    
    ### 10.1 Meeting 예시
    
    ```json
    {
      "@type": "Meeting",
      "meetingNumber": "RAN4#130",
      "canonicalMeetingNumber": "RAN4#130",
      "meetingNumberInt": 130,
      "workingGroup": "RAN4"
    }
    ```
    
    ### 10.2 Tdoc 예시 (discussion)
    
    ```json
    {
      "@type": "Tdoc",
      "tdocNumber": "R4-2520001",
      "title": "Discussion on XYZ feature",
      "type": "discussion",
      "status": "noted",
      "for": "Discussion",
      "presentedAt": "RAN4#130",
      "submittedBy": ["Samsung"],
      "relatedTo": ["NR_RF_FR2_req_Ph3"],
      "belongsTo": "RAN4#130-8.1"
    }
    ```
    
    ### 10.3 CR 예시
    
    ```json
    {
      "@type": "CR",
      "tdocNumber": "R4-2522758",
      "title": "Correction to NR UE transmitter requirements",
      "type": "CR",
      "status": "agreed",
      "crNumber": "0693",
      "crCategory": "F",
      "modifies": "38.101-1",
      "tsgCRPack": "RP-250401",
      "presentedAt": "RAN4#125bis"
    }
    ```
    
    ### 10.4 LS 예시
    
    ```json
    {
      "@type": "LS",
      "tdocNumber": "R4-2521699",
      "title": "LS on NR RF conformance testing",
      "type": "LS out",
      "direction": "out",
      "sentTo": ["<WG A>", "<WG B>"],
      "ccTo": ["<WG C>"],
      "presentedAt": "RAN4#120"
    }
    ```
    
    ---
    
    ## 11. 검증 규칙
    
    ### 11.1 무결성 검증
    
    | 규칙 | 설명 |
    | --- | --- |
    | tdocNumber 유일성 | 동일 tdocNumber 중복 불가 |
    | ID 패턴 매칭 | R4-\d{7} (7자리) |
    | 참조 무결성 | isRevisionOf/revisedTo 대상이 존재 |
    | 타입 일관성 | CR은 반드시 type∈{CR, draftCR, pCR} |
    
    ### 11.2 통계 검증
    
    | 항목 | 기대 | 검증 방법 |
    | --- | --- | --- |
    | TDoc 총 수 | [P1-V01] | dedup 후 count |
    | CR 수 | [P1-V02] | type 필터 count |
    | LS 수 | [P1-V03] | type 필터 count |
    | Meeting 수 | [P1-V04] | 파일명 dedup count |
    | Neo4j 총 노드 | [P1-V12] | Phase-1~5 적재 후 `MATCH (n) RETURN count(n)` |
    | Neo4j 총 관계 | [P1-V13] | Phase-1~5 적재 후 `MATCH ()-[r]->() RETURN count(r)` |
    | CQ PASS 수 | [P1-V14] | `01_validate_cq_cypher.py` 실행 |
    | TDoc 연결 Meeting 커버리지 | [P1-V15] | `presentedAt` 관계 수 / Meeting 수 |
    
    ---
    
    ## 12. 요약
    
    ### 12.1 인스턴스 생성 명세
    
    | 클래스 | ID 속성 | 데이터 소스 | 주요 변환 |
    | --- | --- | --- | --- |
    | Meeting | meetingNumber | 파일명 | bis 6변종 정규화 |
    | Company | companyName | Source | 쉼표 분리 + LLM 정규화 |
    | Tdoc | tdocNumber | TDoc | **R4-\d{7}** 패턴 |
    | CR | tdocNumber | TDoc + CR 컬럼들 | CR 속성 추가 |
    | LS | tdocNumber | TDoc + To/Cc/Original LS | direction 추출, WG 매핑 |
    
    ### 12.2 RAN4 핵심 요약
    
    | 항목 | RAN4 | 영향 |
    | --- | --- | --- |
    | TDoc ID | **7자리** (`R4-\d{7}`) | 정규식 적용 |
    | bis 정규화 | **6변종** (Bis, bis, bis-e, bis_e, -bis-e, _eBis) | 정규화 로직 |
    | Source 복합값 | **비중 높음** | Company 정규화 부하 |
    | hasContact | **선택 (0..*)** | 빈값 존재 |
    | belongsTo | **선택 (0..1)** | 빈값 소수 존재 |
    | crCategory | **F/A/B/C/D + 1/2/3** | 레거시 허용 |
    
    ---
    
    ## Phase-1 온톨로지 설계 완료
    
    | 단계 | 내용 | 상태 |
    | --- | --- | --- |
    | Step 1 | Domain & Scope | ✅ |
    | Step 2 | Ontology 재사용 | ✅ |
    | Step 3 | 중요 용어 | ✅ |
    | Step 4 | 클래스/계층 | ✅ |
    | Step 5 | 속성 정의 | ✅ |
    | Step 6 | 제약조건 | ✅ |
    | Step 7 | 인스턴스 생성 | ✅ |
    
    ---
    
    ## 13. Appendix ID 네이밍 규칙
    
    본 프로젝트는 Phase 0~11에 걸쳐 Spec 문서를 관리한다. Phase 간 수치 참조 시 충돌과 이중 관리를 방지하기 위해 다음 규칙을 적용한다.
    
    ### 13.1 ID 형식
    
    `P{n}-V{번호}`
    
    | 구성 요소 | 설명 | 예시 |
    | --- | --- | --- |
    | P{n} | Phase 번호 | P1, P2, ... P11 |
    | V | 변수 (Variable) | V |
    | 번호 | 01부터 순차 (빈번호 없음) | 01, 02, ... |
    
    ### 13.2 V-ID 부여 조건
    
    V-ID는 다음 3조건을 모두 충족하는 수치에만 부여한다:
    
    | 조건 | 설명 |
    | --- | --- |
    | 가변성 | 새 데이터 추가 시 값이 바뀜 |
    | 필수성 | Spec↔구현 대조에 필수 |
    | 비자명성 | 본문 목록/테이블에서 직접 세어 확인 불가 |
    
    설계 확정값(클래스 수, OP 수 등)은 하드코딩으로 본문에 직접 기재한다.
    
    ### 13.3 Cross-Phase 참조 원칙
    
    - 각 Phase Appendix는 자기 Phase가 "소유"하는 수치만 V-ID를 가진다.
    - 다른 Phase 수치의 복사본을 자기 Appendix에 두지 않는다.
    - 다른 Phase 수치가 필요하면 원본 Phase의 V-ID를 직접 참조한다.
    예: Phase-6에서 Phase-1 총 Tdoc 수 참조 시 → [P1-V01]
    
    ### 13.4 RAN4 Phase-1 V-ID 소유 수치
    
    Phase-1이 소유하는 V-ID는 Appendix A에 기재. 다른 Phase에서 RAN4 TDoc 수치 참조 시 [P1-V01] 등으로 참조.
    
    ---
    
    ## Appendix A: 기준 수치
    
    > **구현 완료 후 실측치로 작성한다.** 구현 전에는 작성하지 않는다.
    
    | ID | 항목 | 값 | 비고 |
    | --- | --- | --- | --- |
    | P1-V01 | 총 TDoc 수 (dedup) | 167,017 | Tdoc(only) 88,665 + Tdoc:CR(dual) 73,346 + Tdoc:LS(dual) 5,006. Phase-1 backfill +3,527 반영 (165,490 → 167,017) |
    | P1-V02 | CR 수 | 74,929 | :CR 라벨 전수. CR ZIP recovery 후 정본. 직전 74,347 (backfill 반영: 73,346 Tdoc:CR dual + 1,001 Phase-4 backfill). +582 (282 zip 안 docx 본문 복원, recovery 상세 `docs/cross-phase/baselines/recovery_2026-05-05_cr_zip.md`) |
    | P1-V03 | LS 수 | 5,006 | LS in + LS out (Tdoc:LS dual) |
    | P1-V04 | Meeting 수 | 58 | 입력 디렉토리 기준 |
    | P1-V05 | Company 수 | 287 | 정규화 후 |
    | P1-V06 | Contact 수 | 1,133 | contactId dedup |
    | P1-V07 | WorkItem 수 | 1,248 | Related WIs dedup |
    | P1-V08 | AgendaItem 수 | 19,763 | agendaNumber dedup (재적재 후 미팅 단위 누적) |
    | P1-V09 | Release 수 | 14 | |
    | P1-V10 | Spec 수 | 360 | specNumber dedup (Phase-4 backfill +3 반영) |
    | P1-V11 | WorkingGroup 수 | 258 | wgName dedup |
    | P1-V12 | Neo4j 총 노드 | 234,011 | Phase-1~5 누적 |
    | P1-V13 | Neo4j 총 관계 | 1,290,837 | Phase-1~5 누적 |
    | P1-V14 | CQ PASS 수 | 25/25 | RAN4 DB (7690) 재검증 |
    | P1-V15 | TDoc 연결 Meeting | 58/59 | 99%. 분모 59 = 58 (P1-V04 공식 Meeting 노드) + 1 (RAN4#101-bis 고아 — TDoc이 참조하나 Meeting 노드로 생성되지 않은 정규화 이슈). 분자 58 = 실제 TDoc↔Meeting 연결 성공 미팅 수. Meeting 총수 공식 값은 [P1-V04]=58. |
    | P1-V16 | Phase-4 backfill (CR) | +1,001 | Phase-4 CR 파싱 결과 중 Phase-1 Tdoc List에 없던 CR 1,001건 추가. CR 정의는 :CR 라벨 (74,347 - 73,346 = 1,001). Phase-1 출처(Tdoc:CR dual) 73,346과 별건 명시 |
    | P1-V17 | Phase-1 backfill (Tdoc) | +3,527 | RAN4#118 등 신규 미팅 + 누락 Tdoc 보완 |
    | P1-V18 | TDoc List 컬럼 분포 | 31~36개 (시기별: 31컬럼 주류, 36컬럼 최신, 32컬럼 소수, 비표준 8/12컬럼 2개) | 파서 <10컬럼 스킵 임계값 결정 근거 |
    
    ### Phase-1 재적재 이력
    
    - 발견: RAN4#95/96/97/98-e TDoc List 부분 파일로 14,026건 TDoc 누락
    - 복구: 미팅 원시 데이터 디렉토리의 `TDoc_List_Meeting_RAN4#*-e.xlsx` 원본 복사
    - 버그 수정: `COLUMN_NAME_MAP`에 `"Tdoc": "TDoc"` 추가 (RAN4#82bis 컬럼명 호환)
    - 결과: +15,739 Tdoc / +8,181 CR / +421 LS 복원
