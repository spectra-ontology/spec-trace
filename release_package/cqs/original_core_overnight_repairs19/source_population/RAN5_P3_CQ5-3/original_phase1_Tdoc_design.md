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
    
    **3GPP RAN5 회의 문서(Tdoc) 메타데이터와 그 관계**
    
    RAN5 (Radio Access Network WG5)는 NR의 Conformance Testing을 담당한다.
    단말(UE)과 기지국(BS)의 적합성 시험 규격을 정의하는 WG이다.
    
    주요 Specification:
    - **38.508-1/2**: NR; UE conformance specification; Common test environments
    - **38.521-1~5**: NR; UE conformance specification; Radio transmit and receive (Part 1-5)
    - **38.522**: NR; UE conformance specification; Applicability of conformance tests
    - **38.523-1~3**: NR; UE conformance specification; Protocol (Part 1-3)
    - **38.533**: NR; UE conformance specification; Radio Resource Management (RRM)
    
    총 15개 TS (38.5xx 시리즈, 서브파트 포함 55 DOCX) — Conformance Testing 전문 WG.
    
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
    | **Phase-1** | **Tdoc_list (Excel)** | 35개 미팅, TDocs [P1-V01] (dedup 기준) |
    
    데이터 경로: TDoc List Excel 파일 (미팅별 `.xlsx`)
    
    ### 1.5 전제 조건
    
    - Phase-0 (데이터 수집, DOC→DOCX 변환) 완료 상태
    - TDoc List Excel 35개 파일 배치 완료
    - Final Report 35개 파일 배치 완료 (Phase-2에서 사용)
    
    ### 1.6 RAN5 주요 특성
    
    | 항목 | 값 |
    | --- | --- |
    | TDoc 접두사 | R5-NNNNNN (6자리) |
    | 미팅 폴더 | TSGR5__{N} (더블 언더스코어 #100+) |
    | 미팅 범위 | #76~#110 (35개) |
    | bis 접미사 | 없음 |
    | TDoc List 스키마 | 31/36/41 (3종, 41컬럼=다른 컬럼명) |
    | TDoc 총 수 | [P1-V01] |
    | CR 비중 | 다수 (Conformance Testing 특성) |
    | 핵심 TS | 38.5xx (Conformance Testing) |
    | Source 복합값 | 복수 회사 공동 제출 존재 |
    | CR revision | 일부 CR 보유 |
    
    **RAN5 고유 특성**:
    - **TDoc 번호 6자리**: `R5-\d{6}` 정규식 적용
    - **CR 다수**: Conformance Testing 특성상 CR 비중이 압도적. Type 분포에 WI status report, WID new, WID revised, WI summary, ToR, SID new/revised 포함
    - **41컬럼 파일 8개**: 완전히 다른 컬럼명(CRnbr, Doc-type, Decision 등) → 컬럼명 정규화 매핑 필수
    - **3GU 포맷 파일 2개**: 미팅번호 미포함 (#108, #110 하드코딩 매핑)
    - **3GU 파일 컬럼 차이**: `Tdoc`(소문자 d), `Rel`, `Specification`, `LS_To`, `LS_Cc`
    - **bis 미팅 없음**: 정규화 대상 없음
    - **CR category F 다수**: 거의 전부 F (Correction) 카테고리
    - **agreed 최다**: Status 최다값
    - **Agreement 최다**: For 최다값 (TDoc List 메타데이터 `For` 필드 라벨 기준. Final Report 본문의 `Agreement:` 헤딩 블록과는 별개 — Phase-2 §1.6에서는 Final Report 본문에 `Agreement:` 블록이 사실상 없어 제외 대상. 두 레이어가 서로 다르므로 혼동 금지)
    - **전자회의 접미사 `-e`**: #86~#96 (11개)
    
    ---
    
    ## 2. Scope 정의
    
    ### 2.1 포함 (In Scope)
    
    | 포함 | 제외 |
    | --- | --- |
    | Tdoc 메타데이터 | TS/TR 본문 |
    | Tdoc 간 관계 (revision, LS) | Final Report (Minutes) 본문 (Phase-2에서) |
    | 회의 정보 | RAN5 외 WG 데이터 |
    | 회사 정보 |  |
    | Work Item / Agenda Item |  |
    | Release 정보 |  |
    
    ### 2.2 데이터 품질 이슈
    
    | 이슈 | 영향 | 처리 방안 |
    | --- | --- | --- |
    | **TDoc 번호 6자리** | 7자리 정규식과 불일치 | `R5-\d{6}` 전용 패턴 사용 |
    | **41컬럼 파일 8개** | 컬럼명 완전 상이 (Tdoc, CRnbr, Decision 등) | 41→31 컬럼명 매핑 테이블 적용 |
    | **3GU 파일 2개** | 파일명에 미팅번호 없음 | #108, #110 하드코딩 매핑 |
    | **3GU 컬럼 차이** | Tdoc, Rel, Specification, LS_To, LS_Cc | 3GU→31 컬럼명 매핑 |
    | **컬럼 수 시기별 변화** | 31→36→41 (3가지 스키마 혼재) | 컬럼명 정규화 후 통합 처리 |
    | **Source 복합값** | Company 정규화 필요 | 쉼표 분리 + LLM 정규화 |
    | **Contact 빈값** | Contact 연결 불가 | hasContact 관계 0..* 처리 |
    | **Release 오염값** | "-", "R1997" 등 비정상 값 | Rel- 접두사 필터링 |
    | **For 대소문자 혼재** | "discussion" vs "Discussion" 혼재 | 대소문자 정규화 |
    
    ---
    
    ## 3. Competency Questions
    
    RAN5 TDoc List는 31개 기본 컬럼 구조를 기반으로 CQ 체계를 구성한다.
    
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
    
    *CQ2-5: CR category는 Phase-1 TDoc List에서 확보. Clauses Affected는 36컬럼 파일 7개에서 부분 확보 + 나머지는 Phase-4 CR 문서 파싱에서.*
    
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
    
    *참고: "Meeting 번호 DESC"는 `meetingNumberInt` 속성으로 정렬해야 숫자 기반 정렬이 보장됨 (문자열 정렬 시 #99 > #100 문제 발생)*
    
    // ★ 최신 우선 원칙: 명시적 요청 없으면 항상 DESC
    
    ### 4.2 결과 개수 (Default Limit)
    
    | CQ 유형 | 기본값 | 적용 CQ |
    | --- | --- | --- |
    | 목록 조회 | 10 | 1-1 ~ 1-5, 1-9, 2-1 ~ 2-3, 2-6 ~ 2-7, 3-1 ~ 3-2, 3-5, 4-1, 4-3 |
    | 단일 조회 | 1 | 1-6 ~ 1-8, 2-4 ~ 2-5 |
    | 집계/순위 | 10 | 3-3 ~ 3-4, 3-6, 4-2 |
    
    ---
    
    ## 5. CQ vs Tdoc 메타데이터 검증
    
    RAN5 TDoc List 컬럼 구조(31개 기본)를 기반으로 CQ 답변 가능성을 검증한다.
    
    | # | Competency Question | 필요한 데이터 | 컬럼 존재 | 답변 가능 | 비고 |
    | --- | --- | --- | --- | --- | --- |
    | **CQ1. Tdoc 기본 검색** | | | | | |
    | 1-1 | 특정 회의에서 특정 Work Item 관련 Tdoc 목록은? | Meeting, Related WIs | ✅ | ✅ | Meeting은 파일명에서 추출 |
    | 1-2 | 특정 회의에서 특정 Agenda Item 관련 Tdoc 목록은? | Meeting, Agenda item | ✅ | ✅ | 41컬럼: Agenda (번호만, 설명 없음) |
    | 1-3 | 특정 회의에서 특정 회사가 제출한 Tdoc 목록은? | Meeting, Source | ✅ | ✅ | |
    | 1-4 | 특정 Release에서 논의된 Tdoc 목록은? | Release | ✅ | ✅ | |
    | 1-5 | 특정 회의에서 승인/합의된 Tdoc 목록은? | Meeting, TDoc Status | ✅ | ✅ | |
    | 1-6 | 특정 Tdoc의 결정 결과(Status)는? | TDoc Status | ✅ | ✅ | |
    | 1-7 | 특정 Tdoc의 목적(For)은? | For | ✅ | ✅ | |
    | 1-8 | 특정 Tdoc의 담당자(Contact)는? | Contact | ✅ | ✅ | 빈값 일부 |
    | 1-9 | 이번 회의 전체 Agenda 목록과 설명은? | Agenda item, description | ✅ | △ | 41컬럼 파일: 설명 없음 |
    | **CQ2. Tdoc 관계 추적** | | | | | |
    | 2-1 | 특정 Tdoc의 이전/이후 revision은? | Is revision of, Revised to | ✅ | ✅ | 41컬럼: Replaces/Replaced-by |
    | 2-2 | 특정 LS가 어디서 왔고 어디로 갔나? | Original LS, To, Cc | ✅ | ✅ | |
    | 2-3 | 특정 Tdoc이 어떤 LS의 답변(Reply)인가? | Reply to, Reply in | ✅ | ✅ | |
    | 2-4 | 특정 Tdoc이 어떤 TS/Spec을 변경하나? | Spec | ✅ | ✅ | |
    | 2-5 | 특정 CR의 카테고리와 영향 범위는? | CR category, Clauses Affected | △ | △ | Clauses Affected: 36컬럼 7개만 |
    | 2-6 | 이번 회의에서 다음 회의로 연기된 Tdoc은? | TDoc Status (postponed) | ✅ | ✅ | |
    | 2-7 | 이번 회의에 들어온 LS 목록과 관련 Agenda Item은? | Type (LS in), Agenda item | ✅ | ✅ | |
    | **CQ3. 회사/경쟁사 분석** | | | | | |
    | 3-1 ~ 3-6 | 회사/경쟁사 분석 | Source, Related WIs, Agenda, Status | ✅ | ✅ | Source 복합값 → 정규화 필수 |
    | **CQ4. 히스토리/요약** | | | | | |
    | 4-1 ~ 4-3 | 히스토리/요약 | 여러 회의 데이터, Source, Status, Agenda | ✅ | ✅ | |
    
    ---
    
    ## 6. 검증 결과
    
    ### 6.1 발견된 문제와 해결
    
    | 문제 | 해당 CQ | 해결 방법 | 상태 |
    | --- | --- | --- | --- |
    | **Meeting 컬럼 없음** | 1-1, 1-2, 1-3, 1-5 | Meeting 클래스 추가. 파일명에서 회의 정보 추출 | ✅ 해결 |
    | **여러 회의 데이터 필요** | 4-1 | 온톨로지 구조는 지원. 전체 미팅 데이터 로드 시 답변 가능 | △ 구조 지원 |
    | **Clauses Affected 부분 확보** | 2-5 | 36컬럼 파일 7개에서 부분 확보. 나머지는 Phase-4 보완 | △ Phase-4 보완 |
    | **TDoc 번호 6자리** | 전체 | `R5-\d{6}` 정규식 적용. Step 7에서 상세 정의 | ✅ 해결 |
    | **41컬럼 파일 컬럼명** | 전체 | 컬럼명 매핑 테이블 (§7.1). Step 7에서 상세 정의 | ✅ 해결 |
    | **3GU 파일 미팅 매핑** | 전체 | TDoc 번호 범위로 확인: #108, #110. 하드코딩 | ✅ 해결 |
    | **41컬럼 Agenda 설명 누락** | 1-9 | agendaDescription null 허용 (0..1로 변경) | ✅ 해결 |
    
    ### 6.2 결론
    
    TDoc List 컬럼 구조가 3가지 스키마(31/36/41)로 분화되었으나, 핵심 컬럼은 모두 존재. 41컬럼 파일의 컬럼명 매핑만 처리하면 모든 CQ에 답변 가능.
    RAN5 특화 이슈(6자리 TDoc, 41컬럼 매핑, 3GU 파일, CR 다수)는 파싱 단계(Step 7)에서 처리.
    
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
    
    3GPP TDoc 도메인에 대해 재사용 가능한 기존 Ontology를 검토한다.
    
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
    | 파일 | Tdoc_list Excel (35개 미팅) |
    | 경로 | TDoc List Excel 입력 디렉토리 (미팅별 `.xlsx`) |
    | 스키마 | 31컬럼(20개), 36컬럼(7개), 41컬럼(8개) |
    | TDoc 총 수 | [P1-V01] (dedup) |
    
    ---
    
    ## 3. 용어 나열
    
    ### 3.1 클래스 후보
    
    | 용어 | 데이터 소스 | 채울 수 있나? | 비고 |
    | --- | --- | --- | --- |
    | Tdoc | TDoc 컬럼 | ✅ | 상위 클래스 |
    | CR | Type 컬럼 (CR, draftCR, pCR) | ✅ | Tdoc 하위 클래스. 다수 비중 |
    | LS | Type 컬럼 (LS in, LS out) | ✅ | Tdoc 하위 클래스. 소수 비중 |
    | Meeting | 파일명에서 추출 | ✅ | RAN5#{N} 패턴 |
    | Company | Source 컬럼 | ✅ | 파싱/정규화 필요 (복합값 존재) |
    | Contact | Contact 컬럼 | ✅ | 빈값 일부 |
    | WorkItem | Related WIs 컬럼 | ✅ | 파싱 필요 |
    | AgendaItem | Agenda item 컬럼 | ✅ | 41컬럼: Agenda (번호만) |
    | Release | Release 컬럼 | ✅ | Rel-8~19 범위 (오염값 제외) |
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
    | contactId | Contact ID | Contact | ✅ |
    | contactName | Contact | Contact | ✅ |
    | agendaNumber | Agenda item | AgendaItem | ✅ |
    | agendaDescription | Agenda item description | AgendaItem | ✅ (41컬럼 없음) |
    | specNumber | Spec | Spec | ✅ |
    | specVersion | Version | Spec | ✅ |
    | crNumber | CR | CR | ✅ |
    | crRevision | CR revision | CR | ✅ (일부 보유) |
    | crCategory | CR category | CR | ✅ (F 다수) |
    | clausesAffected | (36컬럼 파일 7개) | CR | △ 부분 확보 |
    | tsgCRPack | TSG CR Pack | CR | ✅ |
    | direction | Type에서 추출 | LS | ✅ |
    | specTitle | (외부 데이터/동적 생성) | Spec | ✅ |
    
    ### 3.4 CR 영향 범위 속성
    
    | 용어 | 데이터 소스 | 대상 클래스 | 채울 수 있나? |
    | --- | --- | --- | --- |
    | affectsUICC | UICC | CR | ✅ (36컬럼 파일 7개만) |
    | affectsME | ME | CR | ✅ (36컬럼 파일 7개만) |
    | affectsRAN | RAN | CR | ✅ (36컬럼 파일 7개만) |
    | affectsCN | CN | CR | ✅ (36컬럼 파일 7개만) |
    
    ### 3.5 Meeting 속성
    
    | 용어 | 데이터 소스 | 대상 클래스 | 채울 수 있나? |
    | --- | --- | --- | --- |
    | meetingNumber | 파일명 (RAN5#{N}) | Meeting | ✅ |
    | canonicalMeetingNumber | meetingNumber에서 정규화 | Meeting | ✅ |
    | meetingNumberInt | canonicalMeetingNumber에서 추출 | Meeting | ✅ |
    | workingGroup | "RAN5" 고정 | Meeting | ✅ |
    
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
    | 41컬럼 Flag1~4 | 내부 관리용 플래그, 의미 불명 |
    | 41컬럼 IsCurrent | 모든 값 null |
    | 41컬럼 Available | Boolean (접근가능 여부), Ontology 불필요 |
    | 41컬럼 Done | 내부 관리용, Ontology 불필요 |
    | 41컬럼 Withdrawn | status=withdrawn과 중복 |
    | 41컬럼 headerForInfo/footerForInfo | 표시용 필드 |
    | 41컬럼 ogLSattachments | 첨부파일 정보, Phase-1 범위 외 |
    
    ---
    
    ## 5. 파싱 필요 항목
    
    | 컬럼 | 이유 | 예시 |
    | --- | --- | --- |
    | Source | 복합 값 | "Huawei, HiSilicon" → 2개 Company |
    | Related WIs | 복합 값 | "NR_UEConTest_Perf-Core" → 1개 WorkItem |
    | To | 복합 값 | "SA2, CT1" → 2개 WorkingGroup |
    | Cc | 복합 값 | "RAN, SA2" → 2개 WorkingGroup |
    | Release | 방어 필터 | "Rel-" 접두사 없는 값("-", "R1997") 필터링 |
    
    ### 5.1 RAN5 Type 분포
    
    | Type | 처리 |
    | --- | --- |
    | **CR** | **CR (하위 클래스)** |
    | discussion | Tdoc (상위 클래스) |
    | pCR | CR (하위 클래스) |
    | Work Plan | Tdoc (상위 클래스) |
    | WI status report | Tdoc (상위 클래스) |
    | other | Tdoc (상위 클래스) |
    | WID new | Tdoc (상위 클래스) |
    | report | Tdoc (상위 클래스) |
    | LS in | LS (하위 클래스) |
    | WID revised | Tdoc (상위 클래스) |
    | LS out | LS (하위 클래스) |
    | agenda | Tdoc (상위 클래스) |
    | draft TS | Tdoc (상위 클래스) |
    | WI summary | Tdoc (상위 클래스) |
    | draftCR | CR (하위 클래스) |
    | draft TR | Tdoc (상위 클래스) |
    | ToR | Tdoc (상위 클래스) |
    | SID revised | Tdoc (상위 클래스) |
    | SID new | Tdoc (상위 클래스) |
    | TS or TR cover | Tdoc (상위 클래스) |
    
    총합 [P1-V01]. CR 클래스 총합(CR/pCR/draftCR 포함)은 [P1-V02] 참조. LS 클래스 총합(LS in·LS out 포함)은 [P1-V03] 참조.
    
    **RAN5 고유 Type**: WI status report, WID new, WID revised, WI summary, ToR, SID new, SID revised — 모두 Tdoc(상위 클래스)로 처리. 별도 하위 클래스 불필요 (고유 속성 없음).
    
    ### 5.2 RAN5 Status 분포
    
    | Status | 처리 |
    | --- | --- |
    | **agreed** | Data Property |
    | revised | Data Property |
    | withdrawn | Data Property |
    | noted | Data Property |
    | approved | Data Property |
    | available | Data Property |
    | reserved | Data Property |
    | endorsed | Data Property |
    | postponed | Data Property |
    | not pursued | Data Property |
    | for email approval | Data Property |
    | not concluded | Data Property |
    | not treated | Data Property |
    | for email agreement | Data Property |
    | rejected | Data Property |
    
    **RAN5 고유 Status**: `for email approval`, `for email agreement`, `rejected` 등 이메일 기반 상태값.
    
    ### 5.3 RAN5 For 분포
    
    | For | 처리 |
    | --- | --- |
    | **Agreement** | Data Property |
    | Information | Data Property |
    | Endorsement | Data Property |
    | Approval | Data Property |
    | Discussion | Data Property |
    | Action | Data Property |
    | Decision | Data Property |
    | Presentation | Data Property |
    | discussion | Data Property (**대소문자 혼재 → 정규화**) |
    
    **RAN5 고유 For**: Action, Presentation. 소문자 "discussion"은 "Discussion"으로 정규화.
    
    ---
    
    ---
    
    ## Step 4: 클래스와 클래스 계층 정의
    
    > Ontology 101 원칙
    >
    >
    > *"Developing a class hierarchy... Several possible approaches in developing a class hierarchy exist."*
    >
    > — Noy & McGuinness, Ontology Development 101
    >
    
    ---
    
    ## 1. Step 4 목적
    
    - Step 3에서 도출한 용어를 **클래스(Class)**로 구조화
    - **클래스 간 계층(hierarchy)** 정의: 상속(is-a) 관계
    - **인스턴스 판별 규칙** 정의: 어떤 Tdoc이 어떤 클래스에 속하는지
    
    ---
    
    ## 2. 클래스 계층
    
    ```
    owl:Thing
    ├── Tdoc                          # Tdoc 메타데이터 (일반)
    │   ├── CR                        # Change Request (type ∈ {CR, draftCR, pCR})
    │   └── LS                        # Liaison Statement (type ∈ {LS out, LS in})
    ├── Meeting                       # 3GPP 회의
    ├── Company                       # 참여 회사/조직
    ├── Contact                       # 문서 담당자
    ├── WorkItem                      # 작업 항목 (WI)
    ├── AgendaItem                    # 안건 항목
    ├── Release                       # 3GPP Release
    ├── Spec                          # 기술 규격 (TS/TR)
    └── WorkingGroup                  # 3GPP Working Group (LS 수/발신처)
    ```
    
    ### 2.1 클래스 설명
    
    | 클래스 | 설명 | 인스턴스 소스 |
    | --- | --- | --- |
    | **Tdoc** | 3GPP RAN5 회의 문서. CR/LS를 제외한 일반 Tdoc | Type ∉ {CR, draftCR, pCR, LS out, LS in} |
    | **CR** | Change Request. Tdoc의 하위 클래스 | Type ∈ {CR, draftCR, pCR} |
    | **LS** | Liaison Statement. Tdoc의 하위 클래스 | Type ∈ {LS out, LS in} |
    | **Meeting** | RAN5 회의 인스턴스 | 파일명에서 추출 (35개) |
    | **Company** | Tdoc을 제출한 회사/조직 | Source 컬럼 정규화 |
    | **Contact** | Tdoc 담당자 | Contact + Contact ID |
    | **WorkItem** | 3GPP Work Item | Related WIs 컬럼 |
    | **AgendaItem** | 회의 안건 | Agenda item + description |
    | **Release** | 3GPP Release | Release 컬럼 |
    | **Spec** | 기술 규격 (TS/TR) | Spec 컬럼 (CR의 modifies 대상) |
    | **WorkingGroup** | 3GPP Working Group | To, Cc 컬럼 (LS 수/발신처) |
    
    ### 2.2 클래스 판별
    
    | 조건 | 속성 | 값 | 클래스 |
    | --- | --- | --- | --- |
    | **Property** | type | 속성 | 설명 |
    | Data Property | type | CR, draftCR, pCR | **CR** |
    | Data Property | type | LS out, LS in | **LS** |
    | Data Property | type | 그 외 전부 | **Tdoc** |
    
    ---
    
    ## Step 5: 클래스의 속성(Property) 정의
    
    > Ontology 101 원칙
    >
    >
    > *"Define the properties of classes—slots."*
    >
    > — Noy & McGuinness, Ontology Development 101
    >
    
    ---
    
    ## 1. Property 종류
    
    | 종류 | 설명 | 예시 |
    | --- | --- | --- |
    | **Data Property** | 객체의 속성값 | tdocNumber, title, status |
    | **Object Property** | 다른 객체와의 관계 | submittedBy, relatedTo |
    
    ---
    
    ## 3. Tdoc 클래스 속성
    
    ### 3.1 Object Property
    
    | 속성명 | Range | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | submittedBy | Company | Source | Tdoc을 제출한 회사/조직. 복수 회사가 공동 제출 가능 (복합값) |
    | hasContact | Contact | Contact | Tdoc의 담당자 (빈값 가능) |
    | relatedTo | WorkItem | Related WIs | Tdoc이 관련된 Work Item. 다대다 |
    | belongsTo | AgendaItem | Agenda item | Tdoc이 논의되는 Agenda Item |
    | targetRelease | Release | Release | Tdoc이 대상으로 하는 3GPP Release (Rel-8~19) |
    | presentedAt | Meeting | 파일명 | Tdoc이 발표/논의된 3GPP 회의 |
    | isRevisionOf | Tdoc | Is revision of | 이 Tdoc이 수정한 이전 버전 Tdoc |
    | revisedTo | Tdoc | Revised to | 이 Tdoc을 수정한 이후 버전 Tdoc. isRevisionOf의 역관계 |
    | replyTo | Tdoc | Reply to | 이 Tdoc이 답변하는 대상 Tdoc |
    | replyIn | Tdoc | Reply in | 이 Tdoc에 대한 답변 Tdoc (replyTo의 역관계) |
    
    ### 3.2 Data Property
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | tdocNumber | String | TDoc | Tdoc의 고유 식별자. **형식: R5-NNNNNN (6자리)** |
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
    | modifies | Spec | Spec | CR이 변경을 요청하는 대상 기술 규격 (예: 38.521-1) |
    
    ### 4.2 추가 Data Property
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | crNumber | String | CR | CR의 공식 번호. draftCR/pCR은 이 값이 없음 |
    | crCategory | String (Enum) | CR category | CR의 카테고리 (F 다수, A/B/D 극소수) |
    | crRevision | String | CR revision | CR의 수정 횟수 (일부 CR만 보유) |
    | clausesAffected | String | Clauses Affected (36컬럼 7개) | 영향받는 조항 번호 |
    | tsgCRPack | String | TSG CR Pack | TSG에 제출되는 CR Pack 번호 |
    | affectsUICC | Boolean | UICC (36컬럼) | UICC 영향 여부 |
    | affectsME | Boolean | ME (36컬럼) | ME 영향 여부 |
    | affectsRAN | Boolean | RAN (36컬럼) | RAN 영향 여부 |
    | affectsCN | Boolean | CN (36컬럼) | CN 영향 여부 |
    
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
    | meetingNumber | String | 파일명 | 회의 번호 원본 (예: RAN5#109, RAN5#86-e) |
    | canonicalMeetingNumber | String | meetingNumber에서 정규화 | 정규화된 회의 번호. `-e` suffix 제거 |
    | meetingNumberInt | Integer | canonicalMeetingNumber에서 추출 | 정렬용 숫자값 |
    | workingGroup | String | "RAN5" 고정 | 회의를 주관하는 Working Group |
    
    **Meeting ID 정규화 규칙 (RAN5 — bis 없음, `-e`만 처리)**:
    
    | 원본 | canonicalMeetingNumber | meetingNumberInt | 설명 |
    | --- | --- | --- | --- |
    | RAN5#86-e | RAN5#86 | 86 | `-e` 제거 |
    | RAN5#109 | RAN5#109 | 109 | 변경 없음 |
    | RAN5#76 | RAN5#76 | 76 | 변경 없음 |
    
    **RAN5 정규화**: bis 변종 없음. `-e` 제거만으로 정규화 완료.
    
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
    | releaseName | String | Release | 3GPP Release 버전명 (Rel-8~19 범위) |
    
    ### 6.7 Spec
    
    | 속성명 | Type | 데이터 소스 | 설명 |
    | --- | --- | --- | --- |
    | specNumber | String | Spec | 기술 규격 번호 (예: 38.521-1, 38.533) |
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
    | 1 | tdocNumber | Tdoc | String | Tdoc 고유 식별자 (**R5-NNNNNN**) |
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
    | submittedBy | Tdoc | Company | 0..* | ❌ | 복수 회사 공동 제출 가능 |
    | hasContact | Tdoc | Contact | 0..* | ❌ | 빈값 존재 → 0..* |
    | relatedTo | Tdoc | WorkItem | 0..* | ❌ | 일부 Tdoc은 Related WIs 없음 |
    | belongsTo | Tdoc | AgendaItem | 0..1 | ❌ | 일부 빈값 존재 |
    | targetRelease | Tdoc | Release | 0..1 | ❌ | "-" 등 비정상값 포함, Release 없음 가능 |
    | presentedAt | Tdoc | Meeting | 1 | ✅ | 모든 Tdoc은 특정 회의에 속함 |
    | isRevisionOf | Tdoc | Tdoc | 0..1 | ❌ | 최초 버전은 없음 |
    | revisedTo | Tdoc | Tdoc | 0..* | ❌ | 분기 revision 가능 |
    | replyTo | Tdoc | Tdoc | 0..* | ❌ | 복수 답변 가능 |
    | replyIn | Tdoc | Tdoc | 0..* | ❌ | 복수 WG 답변 가능 |
    
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
    | crCategory | CR | String (Enum) | 0..1 | ❌ | 일부 미지정 (F/A/B/D) |
    | crRevision | CR | String | 0..1 | ❌ | 일부 CR만 보유 |
    | clausesAffected | CR | String | 0..1 | ❌ | 36컬럼 파일(7개)에서만 |
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
    | CR | 공식 Change Request |
    | discussion | 일반 기술 제안/논의 문서 |
    | pCR | Proposed CR |
    | Work Plan | 작업 계획 |
    | WI status report | Work Item 상태 보고 |
    | other | 기타 문서 |
    | WID new | 신규 Work Item 제안 |
    | report | 보고서 |
    | LS in | 수신 Liaison Statement |
    | WID revised | 수정된 Work Item |
    | LS out | 발신 Liaison Statement |
    | agenda | 회의 안건표 |
    | draft TS | Technical Specification 초안 |
    | WI summary | Work Item 요약 |
    | draftCR | Change Request 초안 |
    | draft TR | Technical Report 초안 |
    | ToR | Terms of Reference |
    | SID revised | 수정된 Study Item |
    | SID new | 신규 Study Item 제안 |
    | TS or TR cover | TS/TR 표지 |
    
    **RAN5 특성**: CR 라벨(CR+pCR+draftCR)이 압도적 다수, WI status report, WID new/revised, WI summary, ToR, SID new/revised 등 WI 관련 Type이 풍부하게 분포. (총 건수는 [P1-V01])
    
    ### 8.2 status (결정 상태)
    
    | 값 | 설명 |
    | --- | --- |
    | agreed | 합의됨 |
    | revised | 수정됨 |
    | withdrawn | 철회됨 |
    | noted | 참고로 접수됨 |
    | approved | 공식 승인됨 |
    | available | 접수됨 |
    | reserved | 예약됨 |
    | endorsed | 지지/승인됨 |
    | postponed | 연기됨 |
    | not pursued | 추진 중단 |
    | for email approval | 이메일 승인 대기 |
    | not concluded | 미결론 |
    | not treated | 미처리 |
    | for email agreement | 이메일 합의 대기 |
    | rejected | 거부됨 |
    
    **RAN5 특성**: agreed 최다, for email approval/agreement, rejected 등 이메일 기반 상태값 존재.
    
    ### 8.3 for (문서 목적)
    
    | 값 | 설명 |
    | --- | --- |
    | Agreement | 합의 요청 |
    | Information | 정보 공유 |
    | Endorsement | 지지 요청 |
    | Approval | 승인 요청 |
    | Discussion | 논의 요청 |
    | Action | 조치 요청 |
    | Decision | 결정 요청 |
    | Presentation | 발표 |
    
    **정규화**: 소문자 "discussion" → "Discussion"으로 정규화.
    
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
    
    **RAN5 특성**: F가 압도적. Conformance Testing WG 특성상 대부분이 테스트 사양 오류 수정.
    
    ### 8.6 releaseName (Release 값)
    
    | 값 |
    | --- |
    | Rel-16 |
    | Rel-17 |
    | Rel-18 |
    | Rel-15 |
    | Rel-14 |
    | Rel-19 |
    | Rel-13 |
    | Rel-12 |
    | Rel-11 |
    | Rel-10 |
    | Rel-8 |
    
    **Release 범위**: Rel-8~19. "-" 및 "R1997" 등 비정상값은 필터링 대상.
    
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
    
    ---
    
    ## 10. Functional Property 요약
    
    | 속성 | Domain | Range | 설명 |
    | --- | --- | --- | --- |
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
    | 파일 | TDoc_List Excel (35개 파일, 3가지 스키마) |
    | 경로 | TDoc List Excel 입력 디렉토리 (미팅별 `.xlsx`) |
    | 스키마 | 31컬럼(20개), 36컬럼(7개), 41컬럼(8개) |
    | TDoc 총 수 | [P1-V01] (dedup 기준) |
    
    ### 2.1 컬럼명 정규화 매핑 (41컬럼 → 31컬럼)
    
    41컬럼(마스터 로컬) 파일은 컬럼명이 완전히 다르므로 아래 매핑으로 정규화 후 처리:
    
    | 41컬럼 원본 | 31컬럼 표준 | 비고 |
    | --- | --- | --- |
    | Tdoc | TDoc | 대소문자 차이 |
    | Doc-type | Type | |
    | Decision | TDoc Status | |
    | Doc-for | For | |
    | Replaces | Is revision of | 의미 동일 (이전 버전) |
    | Replaced-by | Revised to | 의미 동일 (이후 버전) |
    | CRnbr | CR | |
    | CRrev | CR revision | |
    | CRcat | CR category | |
    | CRpack | TSG CR Pack | |
    | WorkItem | Related WIs | |
    | ReplyTo | Reply to | |
    | ReplyIn | Reply in | |
    | ContactID | Contact ID | |
    | ReservationDate | Reservation date | |
    | Available | Uploaded | Boolean→DateTime (Available=True → 날짜 없음, null 처리) |
    | Agenda | Agenda item | 숫자형 (5.2 등) |
    | originalLS | Original LS | |
    | Version-Current | Version | |
    
    **41컬럼 전용 컬럼 (무시)**:
    - Done, Flag1~4, IsCurrent, Order-within-agenda-item, Report, Withdrawn, headerForInfo, footerForInfo, ogLSattachments, AvailabilityDate
    
    **41컬럼에 없는 31컬럼 컬럼**:
    - Agenda item description, Agenda item sort order, TDoc sort order within agenda item → null 처리
    
    ### 2.2 컬럼명 정규화 매핑 (3GU → 31컬럼)
    
    3GU 포맷(2개 파일)도 일부 컬럼명이 다름:
    
    | 3GU 원본 | 31컬럼 표준 | 비고 |
    | --- | --- | --- |
    | Tdoc | TDoc | 대소문자 차이 |
    | Rel | Release | |
    | Specification | Spec | |
    | LS_To | To | |
    | LS_Cc | Cc | |
    
    ### 2.3 3GU 파일 미팅 매핑
    
    | 파일명 | TDoc 범위 | 매핑 미팅 | 근거 |
    | --- | --- | --- | --- |
    | tdocList_3GU_format_MMexport_2025-09-05_15h05.xlsx | R5-253700~255421 | **RAN5#108** | #107(~253653)과 #109(255500~) 사이 |
    | tdocList_3GU_format_MMexport_2026-02-23_13h40.xlsx | R5-260001~261681 | **RAN5#110** | #109(~256994) 이후 최신 |
    
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
    | Tdoc | tdocNumber | `R5-NNNNNN` | R5-253700 |
    | CR | tdocNumber | `R5-NNNNNN` | R5-240523 |
    | LS | tdocNumber | `R5-NNNNNN` | R5-230015 |
    | Meeting | meetingNumber | `RAN5#NNN` | RAN5#109 |
    | Company | companyName | (정규화된 이름) | Samsung |
    | Contact | contactId | (3GPP ID) | 12345 |
    | WorkItem | workItemCode | (코드) | NR_UEConTest-Perf |
    | AgendaItem | meetingNumber + agendaNumber | (복합키) | RAN5#109-5.2 |
    | Release | releaseName | `Rel-NN` | Rel-19 |
    | Spec | specNumber | `NN.NNN[-N]` | 38.521-1 |
    | WorkingGroup | wgName | (이름) | SA2 |
    
    **RAN5 핵심**: TDoc ID가 **R5-NNNNNN (6자리)**. 정규식: `R5-\d{6}`
    
    ---
    
    ## 6. 클래스별 인스턴스 생성 명세
    
    ### 6.1 Meeting
    
    | 속성 | 소스 | 변환 |
    | --- | --- | --- |
    | meetingNumber | 파일명 | `(?:RAN5\|R5)#(\d+)[-_]?(e)?` 패턴 + 3GU 하드코딩 |
    | canonicalMeetingNumber | meetingNumber | `-e` 제거 |
    | meetingNumberInt | canonicalMeetingNumber | 숫자 부분 추출 (`\d+`) |
    | workingGroup | 고정 | "RAN5" |
    
    **파일명 패턴 분기** (3가지):
    
    | 패턴 | 예시 | 파일 수 | 추출 방법 |
    | --- | --- | --- | --- |
    | `TDoc_List_Meeting_RAN5#N.xlsx` | 표준 | 25개 | `RAN5#(\d+)` |
    | `TdocList_master_local_R5#N[-_]...xlsx` | 마스터 로컬 | 8개 | `R5#(\d+)` |
    | `tdocList_3GU_format_MMexport_*.xlsx` | 3GU | 2개 | 하드코딩: 2025→#108, 2026→#110 |
    
    **정규화**: bis 변종 없음. `-e` suffix만 제거하면 완료.
    
    ### 6.2 Release
    
    | 속성 | 소스 | 변환 |
    | --- | --- | --- |
    | releaseName | Release 컬럼 | "Rel-" 접두사 필터. "-", "R1997" 등 비정상값 제외 |
    
    ### 6.3 Company
    
    | 속성 | 소스 | 변환 |
    | --- | --- | --- |
    | companyName | Source | 쉼표 분리 → 각각 trim → 정규화 사전 적용 |
    | aliases | 정규화 사전 | LLM 기반 정규화 (§9 참조) |
    
    ### 6.4 Contact
    
    | 속성 | 소스 | 변환 |
    | --- | --- | --- |
    | contactName | Contact | 그대로 사용 |
    | contactId | Contact ID (또는 41컬럼 ContactID) | 그대로 사용 |
    
    ### 6.5 WorkItem
    
    | 속성 | 소스 | 변환 |
    | --- | --- | --- |
    | workItemCode | Related WIs (또는 41컬럼 WorkItem) | 쉼표 분리 → 각각 trim |
    
    ### 6.6 AgendaItem
    
    | 속성 | 소스 | 변환 |
    | --- | --- | --- |
    | agendaNumber | Agenda item (또는 41컬럼 Agenda) | 그대로 사용 |
    | agendaDescription | Agenda item description | 그대로 (41컬럼은 null) |
    
    **복합키**: `{meetingNumber}-{agendaNumber}`
    
    ### 6.7 Spec
    
    | 속성 | 소스 | 변환 |
    | --- | --- | --- |
    | specNumber | Spec 컬럼 (또는 3GU Specification) | 그대로 사용 (예: 38.521-1, 38.533) |
    | specVersion | Version 컬럼 (또는 41컬럼 Version-Current) | 그대로 사용 |
    | specTitle | 외부/동적 | 38.5xx 시리즈 제목 매핑 |
    
    ### 6.8 WorkingGroup
    
    | 속성 | 소스 | 변환 |
    | --- | --- | --- |
    | wgName | To, Cc 컬럼 (또는 3GU LS_To, LS_Cc) | 쉼표 분리 → 표준 WG 이름 매핑 |
    
    ### 6.9 Tdoc (일반)
    
    **생성 조건**: Type이 CR/LS 이외인 경우
    
    | 속성 | 소스 | 변환 |
    | --- | --- | --- |
    | tdocNumber | TDoc (또는 41컬럼 Tdoc, 3GU Tdoc) | **`R5-\d{6}` 패턴 검증** |
    | title | Title | 그대로 |
    | abstract | Abstract | 그대로 (빈값 허용) |
    | type | Type (또는 41컬럼 Doc-type) | Enum 매핑 |
    | status | TDoc Status (또는 41컬럼 Decision) | Enum 매핑 |
    | for | For (또는 41컬럼 Doc-for) | Enum 매핑. "discussion"→"Discussion" 정규화 |
    | reservationDate | Reservation date (또는 41컬럼 ReservationDate) | DateTime 변환 |
    | uploadedDate | Uploaded | DateTime 변환 (41컬럼은 Available: Boolean→null) |
    | secretaryRemarks | Secretary Remarks | 그대로 (빈값 허용) |
    
    **Object Property**:
    
    | 관계 | 소스 | 대상 | 변환 |
    | --- | --- | --- | --- |
    | submittedBy | Source | Company | 쉼표 분리 → Company MERGE |
    | hasContact | Contact | Contact | Contact ID 매칭 |
    | relatedTo | Related WIs | WorkItem | 쉼표 분리 → WorkItem MERGE |
    | belongsTo | Agenda item | AgendaItem | agendaNumber 매칭 |
    | targetRelease | Release | Release | releaseName 매칭. "-"/null 제외 |
    | presentedAt | 파일명 | Meeting | meetingNumber 매칭 |
    | isRevisionOf | Is revision of (또는 41컬럼 Replaces) | Tdoc | tdocNumber 참조 |
    | revisedTo | Revised to (또는 41컬럼 Replaced-by) | Tdoc | tdocNumber 참조 |
    | replyTo | Reply to (또는 41컬럼 ReplyTo) | Tdoc | tdocNumber 참조 |
    | replyIn | Reply in (또는 41컬럼 ReplyIn) | Tdoc | tdocNumber 참조 |
    
    ### 6.10 CR (Tdoc 하위 클래스)
    
    **생성 조건**: Type이 'CR', 'draftCR', 'pCR' 중 하나
    
    **추가 속성** (Tdoc 속성 상속 + 아래 추가):
    
    | 속성 | 소스 | 변환 |
    | --- | --- | --- |
    | crNumber | CR (또는 41컬럼 CRnbr) | 그대로 (draftCR/pCR은 null) |
    | crCategory | CR category (또는 41컬럼 CRcat) | F/A/B/D 그대로 저장 |
    | crRevision | CR revision (또는 41컬럼 CRrev) | 문자열로 통일 (빈값 허용) |
    | clausesAffected | Clauses Affected (36컬럼만) | 그대로 (31/41컬럼은 null) |
    | tsgCRPack | TSG CR Pack (또는 41컬럼 CRpack) | 그대로 |
    | affectsUICC | UICC (36컬럼만) | Boolean 변환 |
    | affectsME | ME (36컬럼만) | Boolean 변환 |
    | affectsRAN | RAN (36컬럼만) | Boolean 변환 |
    | affectsCN | CN (36컬럼만) | Boolean 변환 |
    
    **추가 Object Property**:
    
    | 관계 | 소스 | 대상 | 변환 |
    | --- | --- | --- | --- |
    | modifies | Spec (또는 3GU Specification) | Spec | specNumber 매칭 |
    
    ### 6.11 LS (Tdoc 하위 클래스)
    
    **생성 조건**: Type이 'LS out' 또는 'LS in'
    
    **추가 속성** (Tdoc 속성 상속 + 아래 추가):
    
    | 속성 | 소스 | 변환 |
    | --- | --- | --- |
    | direction | Type에서 추출 | 'LS out' → 'out', 'LS in' → 'in' |
    
    **추가 Object Property**:
    
    | 관계 | 소스 | 대상 | 변환 |
    | --- | --- | --- | --- |
    | sentTo | To (또는 3GU LS_To) | WorkingGroup | 쉼표 분리 → WG MERGE |
    | ccTo | Cc (또는 3GU LS_Cc) | WorkingGroup | 쉼표 분리 → WG MERGE |
    | originalLS | Original LS (또는 41컬럼 originalLS) | Tdoc | tdocNumber 참조 |
    | originatedFrom | Original LS에서 WG prefix 추출 | WorkingGroup | prefix→WG 매핑 (예: S2-→SA2, C1-→CT1) |
    
    ---
    
    ## 7. 데이터 변환 규칙
    
    ### 7.1 복합 값 처리
    
    | 컬럼 | 구분자 | 처리 |
    | --- | --- | --- |
    | Source | `,` | 각각 별도 Company 참조 |
    | Related WIs | `,` | 각각 별도 WorkItem 참조 |
    | To / LS_To | `,` | 각각 별도 WorkingGroup 참조 |
    | Cc / LS_Cc | `,` | 각각 별도 WorkingGroup 참조 |
    
    ### 7.2 타입 변환
    
    | 컬럼 | 원본 타입 | 변환 타입 | 규칙 |
    | --- | --- | --- | --- |
    | Reservation date | String | DateTime | ISO 8601 파싱 |
    | Uploaded | String | DateTime | ISO 8601 파싱 |
    | UICC/ME/RAN/CN | String | Boolean | "Yes"/"True" → true, else false |
    | CR revision | String/Number | String | 문자열로 통일 |
    | 41컬럼 Available | Boolean | — | DateTime 대응 없음 → uploadedDate null |
    
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
    | isRevisionOf/revisedTo | `R5-\d{6}` 패턴으로 검증. 같은 데이터셋에 없으면 dangling reference → 관계 생성 안 함 |
    | replyTo/replyIn | 동일 |
    
    ### 8.2 외부 참조 (다른 WG 문서)
    
    | 관계 | 처리 |
    | --- | --- |
    | originalLS | 다른 WG 문서번호(S2-, C1- 등) → WorkingGroup prefix 추출만. Tdoc 인스턴스는 생성하지 않음 |
    
    ---
    
    ## 9. Company 정규화
    
    ### 9.1 정규화 이슈
    
    | 이슈 | 예시 | 빈도 |
    | --- | --- | --- |
    | 대소문자 | samsung / Samsung / SAMSUNG | 높음 |
    | 약어/정식명 | HW / Huawei | 높음 |
    | 복합값 | "Huawei, HiSilicon" | 존재 |
    | 역할 혼재 | "Moderator (Samsung)" | 존재 가능 |
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
    [4. LLM 기반 정규화] → 약어/변형 통합 (결정적 캐시 기반, 아래 규칙)
        │
        ▼
    [5. 빈도 필터] → 유의미한 Company만
        │
        ▼
    [Company 인스턴스]
    ```
    
    **[4] LLM 정규화 재현성 보장 규칙 (감사 이슈 H-1 대응):**
    
    | 규칙 | 내용 |
    | --- | --- |
    | 모델 고정 | LLM 모델 ID 운영 설정 고정. 모델 ID 변경 시 Minor 버전 업 + 재적재 필요. |
    | 호출 파라미터 | `temperature=0`, `top_p=1`, `seed=42` (모델이 지원하는 경우). LLM 비결정성 최소화. |
    | 결과 캐싱 | 입력 string → 정규화 결과를 운영 캐시 JSON에 저장. 이후 동일 입력은 캐시 조회만 수행 (LLM 재호출 없음). |
    | 1차 진실 소스 | 정규화 사전(intermediate)을 먼저 적용. 사전 미커버 string에만 LLM 호출 후 결과를 사전 또는 캐시에 축적. |
    | 멱등성 보장 | 동일 입력 Source 컬럼 값 집합 + 동일 캐시 상태 → 동일 companyName·aliases 산출. **Phase-10 멱등성(§A-2)은 본 캐시의 불변성에 의존** — 캐시를 지우고 재구축하는 경우 재실행마다 companyName 덮어쓰기가 발생할 수 있으므로 **캐시는 버전 관리 대상** (git-tracked). |
    | 모델 업스트림 변경 대응 | LLM 모델이 업스트림에서 업데이트되어 동일 캐시 키에 다른 결과를 내는 경우 → 캐시 우선이므로 *기존* 결과가 유지됨. 의도적 재정규화 시 캐시 무효화 + 변경 diff를 별도 로그로 기록. |
    
    ### 9.3 정규화 사전 형식
    
    ```json
    {
      "Samsung": ["Samsung", "Samsung Electronics", "SEC"],
      "Huawei": ["Huawei", "HW", "Huawei Technologies", "HiSilicon"],
      "ZTE": ["ZTE", "ZTE Corporation"],
      "Rohde & Schwarz": ["Rohde & Schwarz", "R&S"],
      "Keysight Technologies": ["Keysight Technologies", "Keysight"]
    }
    ```
    
    **RAN5 Source 특이사항**:
    - Source 복합값: 복수 회사 공동 제출 존재
    - Contact 빈값: 일부 존재
    
    ---
    
    ## 10. 예시 인스턴스
    
    ### 10.1 Meeting 예시
    
    ```json
    {
      "@type": "Meeting",
      "meetingNumber": "RAN5#109",
      "canonicalMeetingNumber": "RAN5#109",
      "meetingNumberInt": 109,
      "workingGroup": "RAN5"
    }
    ```
    
    ### 10.2 Tdoc 예시 (discussion)
    
    ```json
    {
      "@type": "Tdoc",
      "tdocNumber": "R5-253700",
      "title": "Discussion on UE conformance test case",
      "type": "discussion",
      "status": "noted",
      "for": "Discussion",
      "presentedAt": "RAN5#108",
      "submittedBy": ["Samsung"],
      "relatedTo": ["NR_UEConTest-Perf"],
      "belongsTo": "RAN5#108-5.2"
    }
    ```
    
    ### 10.3 CR 예시
    
    ```json
    {
      "@type": "CR",
      "tdocNumber": "R5-240523",
      "title": "Correction to NR RRM test case 8.1.4.1",
      "type": "CR",
      "status": "agreed",
      "crNumber": "0693",
      "crCategory": "F",
      "modifies": "38.533",
      "tsgCRPack": "RP-250401",
      "presentedAt": "RAN5#109"
    }
    ```
    
    ### 10.4 LS 예시
    
    ```json
    {
      "@type": "LS",
      "tdocNumber": "R5-230015",
      "title": "LS on NR conformance testing scope",
      "type": "LS out",
      "direction": "out",
      "sentTo": ["SA2", "CT1"],
      "ccTo": ["RAN"],
      "presentedAt": "RAN5#100"
    }
    ```
    
    ---
    
    ## 11. 검증 규칙
    
    ### 11.1 무결성 검증
    
    | 규칙 | 설명 |
    | --- | --- |
    | tdocNumber 유일성 | 동일 tdocNumber 중복 불가 |
    | ID 패턴 매칭 | R5-\d{6} (6자리) |
    | 참조 무결성 | isRevisionOf/revisedTo 대상이 존재 |
    | 타입 일관성 | CR은 반드시 type∈{CR, draftCR, pCR} |
    
    ### 11.2 통계 검증
    
    | 항목 | 기대 | 검증 방법 |
    | --- | --- | --- |
    | TDoc 총 수 | [P1-V01] | dedup 후 count |
    | CR 수 | [P1-V02] | type 필터 count |
    | LS 수 | [P1-V03] | type 필터 count |
    | Meeting 수 | [P1-V04] | 파일명 dedup count |
    | Neo4j 총 노드 | [P1-V12] | 적재 후 `MATCH (n) RETURN count(n)` |
    | Neo4j 총 관계 | [P1-V13] | 적재 후 `MATCH ()-[r]->() RETURN count(r)` |
    | CQ PASS | [P1-V14] | CQ 데이터셋 전수 실행 후 PASS 수 |
    
    ---
    
    ## 12. 요약
    
    ### 12.1 인스턴스 생성 명세
    
    | 클래스 | ID 속성 | 데이터 소스 | 주요 변환 |
    | --- | --- | --- | --- |
    | Meeting | meetingNumber | 파일명 (3패턴) | `-e` 제거, 3GU 하드코딩 |
    | Company | companyName | Source | 쉼표 분리 + LLM 정규화 |
    | Tdoc | tdocNumber | TDoc | **R5-\d{6}** 패턴 |
    | CR | tdocNumber | TDoc + CR 컬럼들 | CR 속성 추가 |
    | LS | tdocNumber | TDoc + To/Cc/Original LS | direction 추출, WG 매핑 |
    
    ### 12.2 RAN5 핵심 특성 요약
    
    | 항목 | 값 | 영향 |
    | --- | --- | --- |
    | TDoc ID | 6자리 | 정규식 `R5-\d{6}` |
    | 스키마 | 31/36/41 (3종) | 41컬럼 정규화 매핑 필수 |
    | 3GU 파일 | 2개 (#108, #110) | 미팅번호 하드코딩 |
    | bis 정규화 | 없음 | 단순화 |
    | CR 비중 | 다수 | CR 처리 성능 중요 |
    | Source 복합값 | 존재 | 쉼표 분리 + LLM 정규화 |
    | Contact 빈값 | 일부 | hasContact 0..* |
    | For 정규화 | discussion→Discussion | 대소문자 통일 |
    
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
    
    ## Appendix A: 기준 수치
    
    > **구현 완료 후 실측치로 작성한다.** 구현 전에는 작성하지 않는다.
    
    | ID | 항목 | 값 | 비고 |
    | --- | --- | --- | --- |
    | P1-V01 | 총 TDoc 수 (dedup) | 62,069 | Tdoc 8,252 + CR 53,288 + LS 529 |
    | P1-V02 | CR 수 | 53,288 | CR + draftCR + pCR |
    | P1-V03 | LS 수 | 529 | LS in + LS out |
    | P1-V04 | Meeting 수 | 35 | |
    | P1-V05 | Company 수 | 179 | 정규화 후 |
    | P1-V06 | Contact 수 | 471 | contactId dedup |
    | P1-V07 | WorkItem 수 | 398 | Related WIs dedup |
    | P1-V08 | AgendaItem 수 | 1,724 | DISTINCT agendaNumber 기준. AgendaItem 라벨 노드 수는 8,632건 (dedup 전, Phase-2 이후 보강 포함) |
    | P1-V09 | Release 수 | 11 | Rel-8~19 |
    | P1-V10 | Spec 수 | 73 | specNumber dedup. Phase-4 [P4-V04]에서 22개 동적 추가되어 누적 95 |
    | P1-V11 | WorkingGroup 수 | 142 | wgName dedup |
    | P1-V12 | Neo4j 총 노드 | 65,100 | Phase-1 시점. Phase-2~5 + Phase-7/11 incremental update 누적 후 134,196 (baseline_snapshot 정본) |
    | P1-V13 | Neo4j 총 관계 | 477,794 | Phase-1 시점. Phase-2~5 + Phase-7/11 incremental update 누적 후 855,701 (baseline_snapshot 정본) |
    | P1-V14 | CQ PASS 수 | 25/25 | |
    
    ### A.2 구현 CQ 검증 결과
    
    > Spec Step 1의 §3 CQ는 온톨로지 **설계 근거**이다.
    아래는 구현에서 사용하는 **검증 CQ**로, 설계 CQ를 포함하되 구현 검증용으로 확장/재구성되었다.
    > 
    
    | 항목 | 설계 CQ (Spec §3) | 검증 CQ (구현) |
    | --- | --- | --- |
    | 카테고리 수 | 4 (CQ1~CQ4) | 7 (CQ1~CQ7) |
    | 질문 수 | 25 | 25 |
    | 데이터셋 | - | Phase-1 CQ 데이터셋 |
    | 결과 파일 | - | Phase-1 CQ Cypher 결과 |
    | 검증 결과 | - | 25/25 PASS |
    
    검증 CQ 카테고리 매핑:
    
    | 구현 카테고리 | 질문 수 | 대응 설계 CQ |
    | --- | --- | --- |
    | CQ1 (TDoc/CR 기본 검색) | 5 | CQ1 (Tdoc 기본 검색) |
    | CQ2 (Release/Spec/WI 집계) | 3 | CQ1-4, CQ2-4 |
    | CQ3 (Agenda/Type/Company 분포) | 3 | CQ3 (회사/경쟁사 분석) |
    | CQ4 (Revision/LS 관계 추적) | 2 | CQ2 (관계 추적) |
    | CQ5 (노드/관계 통계·커버리지) | 5 | 설계 CQ 외 — 구현 건전성 검증 |
    | CQ6 (Meeting/CR/LS 집계) | 5 | CQ1-5, CQ4 |
    | CQ7 (Agenda/WorkItem 기본 집계) | 2 | CQ1-1, CQ1-2 |
    
    > CQ5는 Spec §3에 없는 **구현 건전성 검증 전용 CQ**(총 노드/관계 수, 커버리지 비율)로, 실측 데이터의 무결성 확인 목적이다. 설계 CQ에는 포함되지 않는다.
