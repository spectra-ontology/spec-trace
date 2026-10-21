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
    
    ### 1.0 용어 통일 (본 Spec 전체에 적용)
    
    | 공식 용어 | 동의어 (혼용 금지, 아래 이름으로 통일) |
    | --- | --- |
    | **Resolution** | 결의사항 / 결정 / Decision (본문에서 논의되는 Agreement/Conclusion/WorkingAssumption의 상위 개념) |
    | **Spec** | TS (3GPP 공식 용어 "TS"는 본문 인용 시에만 사용) |
    
    RAN2 Phase-2 Spec은 "Resolution"을 공식 용어로 사용한다. docs/README/본문에서 "결의사항" 표기를 본 경우 "Resolution"과 동일 개념.
    
    ### 1.1 What is the domain?
    
    **3GPP RAN2 Final Report 본문에 기록된 Resolution(결의) 정보**
    
    ### 1.2 For what are we going to use the ontology?
    
    **Phase-1 Tdoc 중심 온톨로지를 확장**하여 다음을 지원:
    
    - 회의 결과 분석 — 무엇이 합의되었는가
    - 기술 채택 현황 추적 — 어떤 기술이 표준에 반영되었는가
    - 회사별 기여도 파악 — 누가 표준화에 기여했는가
    
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
    
    - 대상: RAN2#93 ~ RAN2#132 (58개 회의)
    - 파일: Final Report DOCX (58개)
    
    ### 1.5 전제 조건
    
    > 본 온톨로지는 Phase-1 Tdoc 온톨로지의 확장이다.
    >
    >
    > Phase-1에서 정의된 클래스 및 관계를 재사용하며, 구체적인 재사용 범위는 Step 2에서 검토한다.
    >
    
    ### 1.6 RAN2 데이터 특성
    
    > **읽기 안내**: 아래 표의 "RAN1 대비" 서술은 RAN1과 비교하여 RAN2가 데이터 부재/축소된 항목을 설명한다. RAN1 Spec을 읽지 않은 독자는 본 Spec만으로도 이해 가능하도록 "근거" 열에 "Final Report 전수 스캔" 등 실측 근거를 함께 기재했다. RAN1 관련 상세는 `docs/RAN/formal/RAN1/phase-2/design-spec/tdoc_ontology_specs(Final_report).md` 참조.
    
    | 항목 | RAN2 | 근거 |
    | --- | --- | --- |
    | Moderator/Chair 데이터 | **없음** (CQ4 미정의. RAN1은 있음) | Final Report 전수 스캔 결과 실질적 인스턴스 없음 |
    | Embedded Figure | **거의 없음** | Final Report 전수 스캔 결과 무시 가능 수준 |
    | Embedded Chart | **없음** | Final Report 전수 스캔 결과 |
    | Embedded Equation | **없음** | Final Report 전수 스캔 결과 |
    | contentWithEquations | **불필요** | 수식 없음 |
    | TDoc 참조 패턴 | **R2-NNNNNNN** | |
    | 미팅 번호 체계 | **RAN2#N** (bis 미팅 포함) | 파일명 기준 추출 |
    | Heading 스타일 | Heading 1~6 + MiniHeading, SubHeading, Heading 9 | 추가 스타일 3종 |
    
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
    
    ### CQ4. 역할 (Moderator/Chair) — 제외
    
    | # | Competency Question | 제외 이유 |
    | --- | --- | --- |
    | 4-1 | 특정 Agenda Item의 Moderator는 누구인가? | 데이터 없음 |
    | 4-2 | 특정 회사가 Moderator를 맡은 Agenda Item 목록은? | 데이터 없음 |
    | 4-3 | 특정 회사의 Moderator 담당 비율은? | 데이터 없음 |
    | 4-4 | 특정 Agenda Item의 Ad-hoc Chair는 누구인가? | 데이터 없음 |
    | 4-5 | 특정 회사가 Ad-hoc Chair를 맡은 Agenda Item 목록은? | 데이터 없음 |
    
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
    
    > Moderator 담당 추이 관련 CQ는 CQ4 미정의에 따라 함께 제외.
    >
    
    ---
    
    ### CQ 결과 규칙
    
    ### 정렬 기준 (Default Sort Order)
    
    | CQ 그룹 | Primary Sort | Secondary Sort | 구현 속성 |
    | --- | --- | --- | --- |
    | CQ1. Resolution 조회 | Meeting 번호 DESC (최신 먼저) | Agenda 번호 ASC, Sequence ASC | `meetingNumberInt DESC` |
    | CQ2. Tdoc ↔ Resolution | Meeting 번호 DESC | Sequence ASC | `meetingNumberInt DESC` |
    | CQ3. 회사별 기여도 | Count DESC (많은 순) | Company 이름 ASC | `count DESC` |
    | CQ6. 트렌드/비교 | Meeting 번호 ASC (시계열) | - | `meetingNumberInt ASC` |
    
    *참고: "Meeting 번호" 정렬은 Phase-1 Meeting 클래스의 `meetingNumberInt` 속성 사용 (숫자 기반 정렬 보장)*
    
    ### 결과 개수 (Default Limit)
    
    | CQ 유형 | 기본값 | 적용 CQ |
    | --- | --- | --- |
    | 목록 조회 | 10 | CQ1-1~1-7, CQ2 |
    | Top N 조회 | 10 | CQ1-8, CQ3 |
    | 트렌드 조회 | 전체 | CQ6 |
    
    *참고: Limit은 쿼리 시 파라미터로 조정 가능*
    
    ---
    
    ## 3. Scope 정의
    
    ### 3.1 포함 (In Scope)
    
    | 구분 | 포함 대상 | 비고 |
    | --- | --- | --- |
    | **Resolution** | Agreement, Conclusion, Working Assumption | CQ1~3, CQ6 |
    | **Embedded Content** | Table | CQ 대상 아님, Resolution 완결성 위해 포함 |
    | **데이터 소스** | Final Report 본문 | Annex 제외 |
    
    ### 3.2 제외 (Out of Scope)
    
    | 제외 대상 | 이유 |
    | --- | --- |
    | 본문의 `**Decision:**` 패턴 | Resolution과 용어 혼동 방지 |
    | Annex (B, C, D, E, F) | 본문만 파싱 원칙 |
    | Resolution 의미/내용 검색 | Vector DB 영역 (향후 확장) |
    | CQ4 (역할) | Moderator/Chair 데이터 없음 |
    | CQ5 (후속 조치) | Annex 의존 |
    | Figure/Chart/Equation 클래스 | 데이터 거의 없음 |
    | Figure 이미지 콘텐츠 | 별도 저장소에서 관리, Graph DB는 메타데이터만 |
    | Table 셀 데이터 | 별도 저장소에서 관리, Graph DB는 메타데이터만 |
    | contentWithEquations 속성 | 수식 0건이므로 불필요 |
    
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
    | CQ4. 역할 (Moderator/Chair) | ❌ 제외 (데이터 없음) |
    | CQ5. 후속 조치 | ❌ 제외 (Annex 의존) |
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
    | 도메인 | 3GPP RAN2 Tdoc 메타데이터 |
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
    | **AgendaItem** | CQ1-4 (Agenda별 Resolution) | ✅ 필수 |
    | **Company** | CQ3 (회사별 기여도) | ✅ 필수 |
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

    **🔴 Phase-1 ↔ Phase-2 정규화 일관성 (필수)**:
    - Phase-2 loader는 `madeAt`/`containedIn`에서 추출한 canonical을 **Phase-1과 동일한 정규화 함수**로 처리한 후 `MERGE` 키로 사용해야 한다.
    - 이유: Phase-1은 canonical에서 `-e` suffix를 제거 (Phase-1 reference classes 모듈 정규화 함수). Phase-2가 정규화를 생략하면 같은 미팅이 두 노드로 분기되어 NULL id placeholder 발생.
    - Phase-2 `MERGE`의 `ON CREATE SET` 에 `m.id` 속성을 명시 부여 (Phase-1 id 패턴 `tdoc:meeting/<canonical>.replace('#', '_')` 동일).
    - 구현: Phase-2 loader의 canonical 정규화 헬퍼 함수 사용.
    
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
    
    ### 5.2 재사용 범위 주의

    CQ4(역할 분석)가 RAN2에 미정의이므로 Company는 CQ3에서만, AgendaItem은 CQ1-4에서만 사용한다.
    
    ### 5.3 비고
    
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
    | 샘플 | RAN2#130, #131, #132 (최신 3개 회의) |
    | 형식 | Word 문서 (영어) |
    | 범위 | 본문만 (Annex 제외) |
    
    ---
    
    ## 3. 용어 나열
    
    ### 3.1 Resolution 관련
    
    | 용어 | 여러 인스턴스? | 독립 객체? | 클래스 여부 |
    | --- | --- | --- | --- |
    | **Agreement** | ✅ | ✅ | ✅ 클래스 |
    | **Conclusion** | ✅ | ✅ | ✅ 클래스 |
    | **Working Assumption** | ✅ | ✅ | ✅ 클래스 |
    
    ### 3.2 Role 관련 — 제외
    
    > RAN2 Final Report 전수 스캔 결과:
    >
    > - Moderator, FL summary, Ad-hoc Chair, Session Notes 인스턴스가 실질적으로 없음
    > - Role 관련 용어(Summary, Session Notes, Moderator, Ad-hoc Chair) 전체 제외
    > - Step 1 §1.6 및 CQ4 제외 결정과 일치
    
    ### 3.3 Relationship 관련
    
    | Term | Meaning | Related CQ |
    | --- | --- | --- |
    | **references** | Resolution이 Tdoc을 참조 | CQ2-1, CQ2-2 |
    | **madeAt** | Resolution이 Meeting에서 도출 | CQ1-1, CQ1-2, CQ1-3 |
    | **resolutionBelongsTo** | Resolution이 AgendaItem에 속함 | CQ1-4 |
    | **hasTable** | Resolution이 Table을 참조 | - |
    | **containedIn** | Table이 Meeting에 포함 | - |
    
    *참고: Phase-1 `belongsTo`(Tdoc → AgendaItem)와 구분하기 위해 `resolutionBelongsTo` 사용*
    
    > RAN2 미정의: moderatedBy, chairedBy (CQ4 미정의), hasFigure, hasChart (데이터 없음)
    
    ### 3.4 Property 관련
    
    | Term | Meaning | Related CQ |
    | --- | --- | --- |
    | **content** | Resolution 본문 텍스트 | CQ2-3 (comeback 패턴) |
    | **resolutionId** | Resolution 고유 식별자 | 전체 |
    | **sequence** | 같은 Agenda 내 순서 | CQ1 |
    | **sessionContext** | 세션 정보 | - |
    | **note** | Resolution 부가 설명 | - |
    | **hasFFS** | "For Further Study" 포함 여부 | - |
    | **hasTBD** | "To Be Determined" 포함 여부 | - |
    
    > RAN2 미정의: contentWithEquations (수식 없음), roundNumber (Summary 없음)
    
    ### 3.5 Embedded Content 관련
    
    | Term | Final Report Pattern | Related CQ |
    | --- | --- | --- |
    | **Table** | `Table X.X.X-X:` 캡션 패턴 | - |
    
    **처리 방향**:
    
    | 대상 | Graph DB 저장 | 별도 저장소 |
    | --- | --- | --- |
    | Table | ID, caption, filePath | 원본 구조 (HTML) |
    
    > RAN2 미정의: Figure (전수 스캔 결과 무시 가능), Chart, Equation (데이터 없음)
    
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
    
    ### CQ6: 트렌드/비교
    
    | CQ | Required Terms |
    | --- | --- |
    | 6-1 ~ 6-2 | CQ1, CQ3 용어 + madeAt (시계열) |
    
    ---
    
    ## 5. 요약
    
    ### 5.1 용어 목록
    
    | Category | Terms |
    | --- | --- |
    | **Resolution** | Agreement, Conclusion, Working Assumption |
    | **Relationship** | references, madeAt, resolutionBelongsTo, hasTable, containedIn |
    | **Property** | content, resolutionId, sequence, sessionContext, note, hasFFS, hasTBD |
    | **Embedded Content** | Table |
    
    ### 5.2 RAN2 미정의 용어
    
    | 카테고리 | 미정의 용어 | 이유 |
    | --- | --- | --- |
    | Role Source | Summary, Session Notes | 데이터 없음 |
    | Role | Moderator, Ad-hoc Chair | 데이터 없음 |
    | Relationship | moderatedBy, chairedBy | CQ4 미정의 |
    | Relationship | hasFigure, hasChart | 데이터 없음 |
    | Property | contentWithEquations | 수식 없음 |
    | Property | roundNumber | Summary 없음 |
    | Embedded Content | Figure, Chart, Equation | 데이터 거의 없음 |
    
    ### 5.3 검증
    
    | 검증 항목 | 결과 |
    | --- | --- |
    | 모든 용어가 Step 1 Scope 내? | ✅ |
    | 모든 용어가 CQ 답변에 필요? | ✅ |
    | Final Report에서 추출 가능? | ✅ |
    | Step 2 직접 정의 목록과 일치? | ✅ (재사용 7 클래스 + 6 관계는 Step 2에서 확정) |
    
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
    | **Agreement** | ✅ | ✅ | ✅ 클래스 |
    | **Conclusion** | ✅ | ✅ | ✅ 클래스 |
    | **Working Assumption** | ✅ | ✅ | ✅ 클래스 |
    
    → 세 유형 모두 "회의에서 도출된 결의"라는 공통 개념 → **상위 클래스 Resolution** 필요
    
    ### 3.2 Role 관련 용어 — 해당 없음
    
    > Step 3 §3.2에서 Role 전체 제외 결정. Summary, Session Notes, Moderator, Ad-hoc Chair 용어는 클래스 판단 대상에서 제외.
    
    ### 3.3 기타 용어
    
    | 용어 | 판단 |
    | --- | --- |
    | references, madeAt, resolutionBelongsTo, hasTable, containedIn | ❌ 관계 (Step 5) |
    | content, resolutionId, sequence, sessionContext, note, hasFFS, hasTBD | ❌ 속성 (Step 5) |
    
    ---
    
    ## 4. Phase-2 신규 클래스
    
    ### 4.1 Resolution 계층
    
    | 클래스 | 정의 | 인스턴스 수 |
    | --- | --- | --- |
    | **Resolution** (abstract) | 회의에서 도출된 기술적 결의 | - |
    | **├─ Agreement** | 기술적 합의 사항 | Appendix A [P2-V01] 참조 |
    | **├─ Conclusion** | 논의 결론 | Appendix A [P2-V02] 참조 |
    | **└─ WorkingAssumption** | 잠정 가정 (추후 Agreement로 확정 가능) | Appendix A [P2-V03] 참조 |
    
    **Resolution을 상위 클래스로 만드는 이유**:
    
    - 세 하위 클래스가 공통 속성(content, note 등)과 공통 관계(references, madeAt, resolutionBelongsTo)를 가짐
    - CQ에서 "특정 조건의 Resolution"을 조회할 때 세 유형을 통합 조회 가능
    
    ### 4.2 Embedded Content 클래스
    
    | 클래스 | 정의 | Graph DB 저장 | 별도 저장소 |
    | --- | --- | --- | --- |
    | **Table** | 문서 내 삽입된 테이블 | ID, caption, filePath | 원본 HTML |
    
    **Table을 클래스로 정의하는 이유**:
    
    - 여러 인스턴스를 가지며 Resolution과 참조 관계를 가짐
    - 기술적 Table 대상 (포맷팅용 제외). 캡션 유무와 무관하게 Resolution 본문에 포함된 실질적 콘텐츠를 추출하며, 식별 기준은 Step 7에서 정의.
    
    > RAN2 미정의: Figure (전수 스캔 결과 무시 가능), Chart (데이터 없음). Step 1 §1.6 및 Step 3 §3.5 근거.
    
    ---
    
    ## 5. 전체 클래스 계층 다이어그램
    
    ```
    ┌─────────────────────────────────────────────────────────────────┐
    │                    RAN2 Meeting Ontology                        │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                 │
    │  Tdoc (Phase-1)                   Resolution (Phase-2 신규)     │
    │  ├── CR (Phase-1)                 ├── Agreement ⭐              │
    │  └── LS (Phase-1)                 ├── Conclusion ⭐             │
    │                                   └── WorkingAssumption ⭐      │
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
    │  Table ⭐                                                       │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘
    ```
    
    ⭐ = Phase-2 신규 클래스
    
    *참고: RAN2는 Summary, SessionNotes (Tdoc 확장), Figure, Chart 클래스를 정의하지 않음*
    
    ---
    
    ## 6. 요약
    
    ### 6.1 Phase-2 신규 클래스
    
    | 계층 | 클래스 |
    | --- | --- |
    | **Resolution 계층** | Resolution (abstract), Agreement, Conclusion, WorkingAssumption |
    | **Embedded Content** | Table |
    
    (신규 클래스 목록은 위 표 참조)
    
    ### 6.2 클래스로 정의하지 않은 용어
    
    | 용어 | 이유 | 처리 |
    | --- | --- | --- |
    | references, madeAt 등 | 관계 | Step 5 |
    | content, note 등 | 속성 | Step 5 |
    
    ### 6.3 RAN2 미정의 클래스
    
    | 클래스 | 이유 |
    | --- | --- |
    | Summary | Moderator/FL 데이터 없음 (Step 1 §1.6) |
    | SessionNotes | Ad-hoc Chair 데이터 없음 (Step 1 §1.6) |
    | Figure | 전수 스캔 결과 무시 가능 (Step 3 §3.5) |
    | Chart | 데이터 없음 (Step 3 §3.5) |
    
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
    | resolutionId | String | Resolution 고유 식별자 (예: AGR-100-8.1-001) |
    | content | String | Resolution 본문 텍스트 |
    | sequence | Integer | 같은 Agenda 내 순서 |
    | sessionContext | String | 세션 정보 (예: "Thursday session", "Online") |
    | note | String | 부가 설명 (Note: ...) |
    
    > RAN2 미정의: contentWithEquations (수식 0건이므로 content만 사용. Step 1 §1.6 근거)
    
    **Object Property**
    
    | Property | Range | Description |
    | --- | --- | --- |
    | references | Tdoc | Resolution이 참조하는 Tdoc |
    | madeAt | Meeting | Resolution이 도출된 회의. Phase-1 Meeting의 `canonicalMeetingNumber`와 매칭 |
    | resolutionBelongsTo | AgendaItem | Resolution이 속한 Agenda |
    | hasTable | Table | Resolution이 참조하는 Table |
    
    > RAN2 미정의: hasFigure (Figure 클래스 없음), hasChart (Chart 클래스 없음)
    
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
    
    Resolution 속성 상속, 추가 속성 없음
    
    > RAN2에서는 "changed to an agreement" 패턴(WA → Agreement 전환)이 Resolution 인스턴스가 아닌 일반 본문에만 존재하여 자동 추출 불가. `promotedTo` 관계는 정의하지 않는다.
    
    ---
    
    ## 4. Tdoc 확장 클래스 속성 — 해당 없음
    
    > RAN2는 Summary, SessionNotes 클래스를 정의하지 않으므로 moderatedBy, chairedBy 관계도 없다 (Step 4 §6.3).
    
    ---
    
    ## 5. Embedded Content 클래스 속성
    
    ### 5.1 Table
    
    **Data Property**
    
    | Property | Type | Description |
    | --- | --- | --- |
    | tableId | String | Table 고유 식별자 (예: TBL-100-001) |
    | caption | String | Table 캡션 텍스트 |
    | filePath | String | 원본 테이블 파일 경로 (HTML) |
    | tableNumber | String | 원본 Table 번호 (예: "Table 7.8-1") |
    
    > RAN2 미정의: equations (수식 0건이므로 Table 내 수식 LaTeX 변환 불필요)
    
    **Object Property**
    
    | Property | Range | Description |
    | --- | --- | --- |
    | containedIn | Meeting | Table이 포함된 회의 |
    
    ---
    
    ## 6. 전체 Object Property 목록 (Phase-2 신규)
    
    | # | Property | Domain | Range | Description |
    | --- | --- | --- | --- | --- |
    | 1 | references | Resolution | Tdoc | Resolution이 참조하는 Tdoc |
    | 2 | madeAt | Resolution | Meeting | Resolution이 도출된 회의 |
    | 3 | resolutionBelongsTo | Resolution | AgendaItem | Resolution이 속한 Agenda |
    | 4 | hasResolutions | AgendaItem | Resolution | Agenda에 속한 Resolution (역관계) |
    | 5 | hasTable | Resolution | Table | Resolution이 참조하는 Table |
    | 6 | containedIn | Table | Meeting | Table이 포함된 회의 |
    
    (moderatedBy, chairedBy, hasFigure, hasChart, promotedTo는 RAN2에서 정의하지 않음)
    
    ---
    
    ## 7. 전체 Data Property 목록 (Phase-2 신규)
    
    | # | Property | Domain | Type | Description |
    | --- | --- | --- | --- | --- |
    | 1 | resolutionId | Resolution | String | Resolution 고유 식별자 |
    | 2 | content | Resolution | String | Resolution 본문 텍스트 |
    | 3 | sequence | Resolution | Integer | 같은 Agenda 내 순서 |
    | 4 | sessionContext | Resolution | String | 세션 정보 |
    | 5 | note | Resolution | String | 부가 설명 |
    | 6 | hasFFS | Agreement | Boolean | FFS 포함 여부 |
    | 7 | hasTBD | Agreement | Boolean | TBD 포함 여부 |
    | 8 | hasConsensus | Conclusion | Boolean | 합의 도달 여부 |
    | 9 | tableId | Table | String | Table 고유 식별자 |
    | 10 | caption | Table | String | 캡션 텍스트 |
    | 11 | filePath | Table | String | 원본 파일 경로 |
    | 12 | tableNumber | Table | String | 원본 Table 번호 |
    
    (contentWithEquations, summaryType, roundNumber, Figure/Chart 관련 속성, equations는 RAN2에서 정의하지 않음)
    
    ---
    
    ## 8. CQ 답변 가능성 검증
    
    | CQ | 필요 속성 | 정의 여부 |
    | --- | --- | --- |
    | CQ1-1~1-3 | madeAt, Resolution 하위 타입 | ✅ |
    | CQ1-4 | resolutionBelongsTo | ✅ |
    | CQ1-5 | references → Tdoc → targetRelease (Phase-1) | ✅ |
    | CQ1-6 | references → Tdoc → modifies (Phase-1) | ✅ |
    | CQ1-7 | references → Tdoc → relatedTo (Phase-1) | ✅ |
    | CQ1-8 | resolutionBelongsTo | ✅ |
    | CQ2-1~2-2 | references | ✅ |
    | CQ2-3 | content | ✅ |
    | CQ2-4 | references → Tdoc → modifies (Phase-1) | ✅ |
    | CQ3-1~3-4 | references → Tdoc → submittedBy (Phase-1) | ✅ |
    | CQ6-1~6-2 | madeAt (시계열) + CQ1/CQ3 속성 | ✅ |
    
    **§2 포함 CQ 전체 답변 가능** ✅
    
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
    | content | String | 1 | ✅ | Resolution 본문 텍스트 |
    | sequence | Integer | 1 | ✅ | 같은 Agenda 내 순서. *Note: resolutionId에서 추출 가능 (예: AGR-100-8.1-001의 001)* |
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
    | hasConsensus | Boolean | 0..1 | ❌ | - |
    
    ### 3.4 WorkingAssumption
    
    Resolution 상속, 추가 Data Property 없음
    
    ### 3.5 Table
    
    | Property | Type | Cardinality | Required | Description |
    | --- | --- | --- | --- | --- |
    | tableId | String | 1 | ✅ | PK, 패턴: `TBL-{meeting}-{seq}` |
    | caption | String | 0..1 | ❌ | Table 캡션 (있는 경우만) |
    | filePath | String | 1 | ✅ | 원본 HTML 파일 경로 |
    | tableNumber | String | 0..1 | ❌ | 원본 Table 번호 |
    
    > RAN2 미정의: Summary (§3.5), SessionNotes (§3.6), Figure (§3.7), Chart (§3.9), equations (수식 0건)
    
    ---
    
    ## 4. Object Property Facet
    
    ### 4.1 Resolution 관계
    
    | Property | Domain | Range | Cardinality | Functional | Inverse |
    | --- | --- | --- | --- | --- | --- |
    | references | Resolution | Tdoc | 0..* | ❌ | - |
    | madeAt | Resolution | Meeting | 1 | ✅ | - |
    | resolutionBelongsTo | Resolution | AgendaItem | 1 | ✅ | hasResolutions |
    | hasTable | Resolution | Table | 0..* | ❌ | - |
    
    > RAN2 미정의: hasFigure, hasChart
    > madeAt Cardinality는 1 (RAN2에서는 1개 Report가 2개 Meeting에 연결되는 케이스 없음)
    
    ### 4.2 WorkingAssumption 추가 관계 — 해당 없음
    
    > `promotedTo` (WA → Agreement)는 RAN2에서 정의하지 않음. §3.4 참조.
    
    ### 4.3 AgendaItem 역관계 (Phase-1 확장)
    
    | Property | Domain | Range | Cardinality | Functional | Inverse |
    | --- | --- | --- | --- | --- | --- |
    | hasResolutions | AgendaItem | Resolution | 0..* | ❌ | resolutionBelongsTo |
    
    ### 4.4 Embedded Content 관계
    
    | Property | Domain | Range | Cardinality | Functional | Inverse |
    | --- | --- | --- | --- | --- | --- |
    | containedIn | Table | Meeting | 1 | ✅ | - |
    
    > RAN2 미정의: moderatedBy (§4.3), chairedBy (§4.4)
    
    ---
    
    ## 5. 필수 속성 요약
    
    ### 5.1 필수 Data Property
    
    | Class | Required Properties |
    | --- | --- |
    | Resolution | resolutionId, content, sequence |
    | Agreement | (상속) |
    | Conclusion | (상속) |
    | WorkingAssumption | (상속) |
    | Table | tableId, filePath |
    
    ### 5.2 필수 Object Property
    
    | Class | Required Properties |
    | --- | --- |
    | Resolution | madeAt, resolutionBelongsTo |
    | Table | containedIn |
    
    ---
    
    ## 6. Functional Property 요약
    
    단일값만 허용하는 Object Property:
    
    | Property | Domain | Range | Description |
    | --- | --- | --- | --- |
    | madeAt | Resolution | Meeting | Resolution은 하나의 회의에서만 도출 |
    | resolutionBelongsTo | Resolution | AgendaItem | Resolution은 하나의 Agenda에만 |
    | containedIn | Table | Meeting | Table은 하나의 회의에만 |
    
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
    | **Phase-2** | **Final Report (Word)** | ✅ 구현 완료 (RAN2 Phase-2: Final Report 58건 파싱·KG 적재 완료) |
    
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
    | Agreement | resolutionId | `AGR-{meeting}-{agenda}-{seq}` | AGR-132-8.1-001 |
    | Conclusion | resolutionId | `CON-{meeting}-{agenda}-{seq}` | CON-132-9.2-001 |
    | WorkingAssumption | resolutionId | `WA-{meeting}-{agenda}-{seq}` | WA-132-8.1-001 |
    
    **ID 구성 요소**:
    
    - `{meeting}`: 회의 번호 (예: 93, 100, 132, 101bis)
    - `{agenda}`: Agenda Item 번호 (예: 8.1, 9.2.1)
    - `{seq}`: 해당 Agenda 내 순번 (001, 002, ...)
    
    > RAN2 특성: bis 미팅 포함 (예: AGR-101bis-8.1-001)
    
    ### 3.3 Embedded Content ID
    
    | 클래스 | ID 속성 | 패턴 | 예시 |
    | --- | --- | --- | --- |
    | Table | tableId | `TBL-{meeting}-{seq}` | TBL-132-001 |
    
    **ID 구성 요소**:
    
    - `{meeting}`: 회의 번호 (예: 93, 100, 132, 101bis)
    - `{seq}`: 해당 회의 내 순번 (001, 002, ...)
    
    > RAN2 미정의: Figure ID (FIG-), Chart ID (CHT-)
    
    ---
    
    ## 4. 데이터 소스 매핑
    
    ### 4.1 Resolution 매핑
    
    **소스**: Final Report 본문
    
    | 관계 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | references → Tdoc | content 내 참조 | `R2-\\d{7}` 패턴 추출 |
    | madeAt → Meeting | 문서 메타 | 파일명에서 회의 번호 추출 후 Phase-1 Meeting의 `canonicalMeetingNumber`와 매칭 |
    | resolutionBelongsTo → AgendaItem | 섹션 헤더 | Agenda 번호 추출. **같은 미팅 내의 AgendaItem과 매칭** (madeAt으로 결정된 Meeting의 AgendaItem) |
    | hasTable → Table | content 내 참조 | `Table X.Y.Z-N` 패턴 → 같은 미팅 내 TBL 인스턴스 연결 |
    
    > TDoc 패턴: `R2-\\d{7}`
    
    **references → Tdoc 매칭 실패 시 처리 규칙:**
    
    | 조건 | 처리 |
    | --- | --- |
    | 추출된 Tdoc 번호가 Phase-1 인스턴스에 존재 | 기존 인스턴스에 references 관계 생성 |
    | 추출된 Tdoc 번호가 Phase-1 인스턴스에 없음 (다른 WG 문서 등) | references 관계 생성 안 함 + 로그 기록 |
    
    *참고: Resolution 본문에서 추출된 `R2-\\d{7}` 패턴이 Phase-1 Tdoc 인스턴스에 존재하지 않을 수 있음. 이 경우 동적 생성하지 않고 관계를 생략함*
    
    **Meeting 연결 규칙:**
    
    | Final Report 파일명 | 추출된 회의 번호 | 매칭 대상 (Phase-1) |
    | --- | --- | --- |
    | Final_Report_RAN2-132.docx | RAN2#132 | canonicalMeetingNumber = "RAN2#132" |
    | Final_Report_RAN2-101bis.docx | RAN2#101bis | canonicalMeetingNumber = "RAN2#101bis" |
    | Final_Report_RAN2-109_e.docx | RAN2#109 | canonicalMeetingNumber = "RAN2#109" |
    
    **미팅 번호 추출:**
    
    > 파일명 기반으로 미팅 번호 추출. (파일명 정합성 검증 완료)
    
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
    | 1 | `no [0~1단어] consensus` | "no consensus", "no RAN2 consensus" |
    | 2 | `not [0~1단어] consensus` | "not consensus", "currently not consensus" |
    | 3 | `did not reach consensus` |  |
    | 4 | `could not reach consensus` |  |
    | 5 | `has not reached consensus` |  |
    | 6 | `lack of consensus` |  |
    
    *참고: "not supported"는 합의 결과가 미지원인 것이며 합의 부재가 아니므로 false 대상이 아님*
    
    ### 4.4 WorkingAssumption 추가 매핑
    
    > RAN1의 `promotedTo` 매핑 제외 — §3.4 참조.
    
    ### 4.5 Table 매핑
    
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
    
    | 관계 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | containedIn → Meeting | 문서 메타 | 파일명에서 회의 번호 추출 |
    
    > RAN2 미정의: Summary 매핑 (§4.5), SessionNotes 매핑 (§4.6), Figure 매핑 (§4.7), Chart 매핑 (§4.9), Equation 처리 (§4.10), equations 속성
    
    ### 4.6 Heading 스타일 매핑 규칙
    
    > RAN2 Final Report에는 표준 Heading 1~6 외에 추가 Heading 스타일이 존재.
    > Agenda Item 추출 시 이들도 매핑해야 함.
    
    | Heading 스타일 | 매핑 |
    | --- | --- |
    | Heading 1 | Agenda Level 1 |
    | Heading 2 | Agenda Level 2 |
    | Heading 3 | Agenda Level 3 |
    | Heading 4 | Agenda Level 4 |
    | Heading 5 | Agenda Level 5 |
    | Heading 6 | Agenda Level 6 |
    | Heading 8 | 무시 (구조적 의미 없음) |
    | **Heading 9** | **Agenda 하위 레벨로 매핑** |
    | **MiniHeading** | **Agenda 하위 레벨로 매핑** |
    | **SubHeading** | **본문 텍스트로 처리 (Agenda 아님)** |
    
    ### 4.7 Null 값 처리 규칙
    
    | 속성/관계 | 상황 | 처리 | 로그 레벨 |
    | --- | --- | --- | --- |
    | content | 파싱 실패 | Resolution 인스턴스 미생성 | ERROR |
    | references | Tdoc 번호가 Phase-1 인스턴스에 없음 | 해당 참조만 스킵 (§4.1 참조) | WARNING |
    | references | Tdoc 번호 파싱 실패 | 해당 참조만 스킵 | WARNING |
    | caption (Table) | 캡션 없음 | null 유지 (정상) | - |
    
    **처리 원칙:**
    
    - `content`(Resolution)은 필수 속성(Cardinality: 1)이므로 값을 채울 수 없으면 인스턴스 자체를 생성하지 않음
    - `caption`은 선택 속성(Cardinality: 0..1)이므로 null이 정상
    
    ---
    
    ## 5. 예시 인스턴스
    
    ### 5.1 Agreement 예시
    
    ```json
    {
      "@type": "Agreement",
      "resolutionId": "AGR-132-8.1-001",
      "content": "Adopt the following TP to Section 5.2, TS38.331 for R19 NR sidelink enhancements",
      "sequence": 1,
      "note": null,
      "hasFFS": false,
      "hasTBD": false,
      "references": [
        { "@id": "tdoc:R2-2401234" },
        { "@id": "tdoc:R2-2401235" }
      ],
      "resolutionBelongsTo": { "@id": "agenda:8.1" },
      "madeAt": { "@id": "meeting:RAN2#132" }
    }
    
    ```
    
    ### 5.2 Conclusion 예시
    
    ```json
    {
      "@type": "Conclusion",
      "resolutionId": "CON-132-9.2-001",
      "content": "It is RAN2 understanding that the UE shall apply the new configuration after receiving the RRC reconfiguration",
      "sequence": 1,
      "hasConsensus": true,
      "resolutionBelongsTo": { "@id": "agenda:9.2" },
      "madeAt": { "@id": "meeting:RAN2#132" }
    }
    
    ```
    
    ### 5.3 WorkingAssumption 예시
    
    ```json
    {
      "@type": "WorkingAssumption",
      "resolutionId": "WA-132-8.1-001",
      "content": "For the MAC CE based activation, the UE behavior is defined as follows...",
      "sequence": 1,
      "resolutionBelongsTo": { "@id": "agenda:8.1" },
      "madeAt": { "@id": "meeting:RAN2#132" }
    }
    
    ```
    
    ### 5.4 Table 예시
    
    ```json
    {
      "@type": "Table",
      "tableId": "TBL-132-001",
      "caption": "Simulation assumptions for RLC performance evaluation",
      "filePath": "...",
      "tableNumber": "Table 7.8-1",
      "containedIn": { "@id": "meeting:RAN2#132" }
    }
    
    ```
    
    **캡션 없는 Table 예시**
    
    ```json
    {
      "@type": "Table",
      "tableId": "TBL-132-015",
      "filePath": "...",
      "containedIn": { "@id": "meeting:RAN2#132" }
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
    | Table | TBL-{m}-{s} | 본문 `<w:tbl>` (캡션 + 구조 기반) | [P2-V04] |
    
    ### 6.2 매핑 규칙 요약
    
    | 클래스 | 식별 패턴 | 주요 추출 |
    | --- | --- | --- |
    | Agreement | `[Agreement]` | content, references, hasFFS, hasTBD |
    | Conclusion | `[Conclusion]` | content, hasConsensus |
    | WorkingAssumption | `[Working Assumption]` | content |
    | Table | 캡션 패턴 또는 구조 기반 | caption (Optional), filePath, tableNumber |
    
    ### 6.3 RAN2 구현 요약

    | 항목 | RAN2 |
    | --- | --- |
    | TDoc 참조 패턴 | `R2-\\d{7}` |
    | 미팅 번호 소스 | 파일명 기준 추출 |
    | bis 미팅 | 존재 (93bis, 95bis, ...) |
    | Heading 추가 스타일 | MiniHeading, SubHeading, Heading 9 |
    | Summary/SessionNotes | 미정의 |
    | Figure/Chart/Equation | 미정의 |
    | contentWithEquations | 미정의 |
    
    ---
    
    ## 7. 전체 완료
    
    Phase-2 온톨로지 설계가 완료되었습니다.
    
    ### 7.1 Embedded Content 처리 요약
    
    | 대상 | Graph DB | 별도 저장소 | 변환 방식 |
    | --- | --- | --- | --- |
    | **Table** | 메타데이터 (ID, caption, filePath) | 원본 HTML | XML 파싱 + HTML 변환 |
    
    > RAN2 미정의: Figure (이미지 추출), Chart (XML 추출), Equation (OMML → LaTeX 변환)
    
    ---
    
    ## Appendix A: 기준 수치
    
    > 이 테이블이 Spec의 수치 권위 소스이다.
    >
    
    > 새 미팅 데이터 추가 시 이 테이블만 수정한다.
    >
    
    | ID | 항목 | 기준값 | 비고 |
    | --- | --- | --- | --- |
    | P2-V01 | Agreement 수 | 3,413 | 58개 Report 파싱 결과 (Annex 이후 Email discussion 포함) |
    | P2-V02 | Conclusion 수 | 171 | 58개 Report 파싱 결과 (초기 미팅 #93~#95bis inline 163건 포함) |
    | P2-V03 | WorkingAssumption 수 | 189 | 58개 Report 파싱 결과 |
    | P2-V04 | Table 수 | 138 | 58개 Report 파싱 결과 |
    
    > RAN2 미정의: Summary 수, SessionNotes 수, Figure 수, Chart 수, 수식 포함 Resolution 수, hasConsensus 커버리지
    
    ### A.2 구현 CQ 검증 결과
    
    > Spec Step 1의 CQ는 온톨로지 **설계 근거**이다.
    아래는 구현에서 사용하는 **검증 CQ**로, 설계 CQ를 포함하되 구현 검증용으로 확장/재구성되었다.
    >
    
    | 항목 | 설계 CQ (Spec) | 검증 CQ (구현) |
    | --- | --- | --- |
    | 데이터셋 | - | `logs/RAN/formal/RAN2/phase-2/cq_test_dataset.json` (25 CQ: CQ1 Resolution조회, CQ2 Tdoc-Resolution추적, CQ3 회사기여도, CQ6 트렌드비교) |
    | 검증 결과 | - | **24/25 PASS + 1 NO_DATA** — 재실행 (이전 실측 25/25). NO_DATA 1건(CQ1-4)은 데이터셋 Cypher의 `meetingNumber: '117'`가 실 Neo4j 데이터 포맷 `'117-e'`와 불일치한 **CQ 데이터셋 버그**이며 구현 회귀 아님. `logs/RAN/formal/RAN2/phase-2/cq_cypher_results.json` 권위 |
    
    ### A.3 Optional 속성 구현 현황
    
    | 속성 | Cardinality | 구현 상태 | 비고 |
    | --- | --- | --- | --- |
    | note | 0..1 | **의도적 미구현** (원본 Report에 해당 필드 마킹 없음) | Spec 유지. 원본 데이터에 마킹이 추가되면 구현 예정. 현 단계에서는 Phase-2 완료 게이트 차단 요인 아님 |
    | sessionContext | 0..1 | **의도적 미구현** (원본 Report에 해당 필드 마킹 없음) | Spec 유지. 원본 데이터에 마킹이 추가되면 구현 예정. 현 단계에서는 Phase-2 완료 게이트 차단 요인 아님 |
    | hasConsensus | 0..1 | ✅ 구현 완료 | 부정 합의 패턴 기반 (6가지 패턴) |
    | ~~promotedTo~~ | — | **제외** | RAN2 데이터에서 "changed to an agreement" 패턴이 Resolution 인스턴스가 아닌 일반 본문에만 존재 (2건). 대응 WA/AGR 인스턴스 자동 식별 불가하여 Spec에서 제외 (§3.4 참조) |
