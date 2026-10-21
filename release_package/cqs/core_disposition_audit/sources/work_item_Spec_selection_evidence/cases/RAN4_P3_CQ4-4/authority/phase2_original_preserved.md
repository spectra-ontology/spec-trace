- **phase-2: Ontology 101 기반 전략/기획, IP/특허 담당 타겟으로 확장 (Final Report)**
    
    ## Step 1: Domain과 Scope 정의
    
    > Ontology 101 원칙
    >
    >
    > *"We suggest starting the development of an ontology by defining its domain and scope."*
    >
    > — Noy & McGuinness, Ontology Development 101
    >
    
    ---
    
    ## 1. 기본 질문에 대한 답변
    
    ### 1.1 What is the domain?
    
    **3GPP RAN4 Final Report 본문에 기록된 Resolution(결의) 정보**
    
    RAN4 Final Report는 **Resolution 텍스트 블록**(`Agreement:`, `Conclusion:`, `Working Assumption:`)과 **Decision 패턴**(`Decision: The document was agreed.`)이 공존하는 구조를 가진다.
    
    - Resolution: 기술적 합의 내용 원문 (Agreement + Conclusion + Working Assumption)
    - Decision: 문서 단위 처리 결과 — Phase-1 status와 중복이므로 Phase-2 Scope 밖
    - Moderator: 0건 → **제외**
    
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
    
    - 대상: RAN4#78 ~ RAN4#117 Final Report
    - 파일: Final Report DOCX
    - **RAN4-99: 빈 파일** → 스킵 대상
    
    ### 1.5 전제 조건
    
    > 본 온톨로지는 Phase-1 Tdoc 온톨로지의 확장이다.
    >
    > Phase-1에서 정의된 클래스 및 관계를 재사용하며, 구체적인 재사용 범위는 Step 2에서 검토한다.
    >
    
    **R-J2 Phase-1 의존성 범위 구체화**:
    
    - **JSON-LD 생성 단계**: Phase-1 JSON-LD 산출물(Tdoc 인스턴스)만 있으면 충분하다. Phase-1 Neo4j **적재 완료**를 요구하지 않는다. Phase-2 파서는 JSON-LD 레벨에서 tdocNumber 매칭을 수행하며, 매칭 실패 시 §4의 규칙에 따라 관계 생략 + 로그 경고로 처리한다.
    - **Neo4j 병합(JSON-LD → Neo4j) 단계에서의 의존성**: Resolution → Tdoc `references` 관계를 Neo4j에 생성하려면 Phase-1 Neo4j 인스턴스가 존재해야 한다. 이 단계에서만 Phase-1 Neo4j 적재가 **실질 의존**이며, JSON-LD 생성 단계는 의존하지 않는다.
    - 따라서 재현 시: Phase-1 JSON-LD만 있으면 Phase-2 파싱은 실행 가능, Phase-2 Neo4j 통합은 Phase-1 Neo4j 적재 이후 실행해야 한다.
    
    ### 1.6 RAN4 데이터 특성
    
    | 항목 | RAN4 | 근거 |
    | --- | --- | --- |
    | **Resolution 구조** | `Agreement:`/`Conclusion:`/`WA:` + `Decision:` 공존 | 전수 스캔 |
    | **Resolution 건수** | Agreement/Conclusion/WA — Appendix A [P2-V01]/[P2-V02]/[P2-V03] 참조 | 파서 실측 |
    | **Decision 패턴** | Phase-1 status와 중복 → 제외 | 전수 스캔 |
    | **Moderator** | 0건 (제외) | 전수 스캔 |
    | **FL Summary** | 0건 | |
    | **SessionNotes (Chair)** | 0건 (제외) | |
    | **Embedded Equation** | OMML → LaTeX 변환 (RAN4-78~96에 집중) | 파서 실측 v2 |
    | **Embedded Figure** | 캡션 기반 + 50KB+ 구조적 — Appendix A [P2-V05] 참조 | 파서 실측 v2 |
    | **Embedded Chart** | c:chart XML — Appendix A [P2-V06] 참조 | 파서 실측 v2 |
    | **Embedded Table** | RF 측정 등 기술적 테이블 — Appendix A [P2-V04] 참조 | 파서 실측 v2 |
    | **Heading 스타일** | Heading 1~7 + toc 1~7 + TOC 1~3(대문자) | 전수 스캔 |
    | **TDoc 참조 패턴** | R4-NNNNNNN (7자리) | |
    | **bis 미팅** | Bis/bis/bis-e/bis_e/-bis-e/_eBis 6변종 | Phase-1 canonical과 일치 |
    | **빈 파일** | RAN4-99 | 스킵 대상 |
    
    ### 1.7 RAN4 Phase-2 Resolution과 Decision의 관계
    
    RAN4 Final Report에서 **Resolution과 Decision은 서로 다른 레벨의 정보**이다:
    
    ```
    [TDoc] R4-2401234 CB:#6_RRM (discussion)
      Decision: The document was noted.     ← TDoc 단위 처리 결과 (Phase-1 status)
      Agreement: The test tolerance...      ← 기술적 합의 내용 (Resolution 원문)
      Agreement: For band n104, the...      ← 기술적 합의 내용 (Resolution 원문)
    ```
    
    - **하나의 TDoc 논의에서 여러 Resolution이 도출**될 수 있음
    - Decision이 `noted`여도 그 안에서 기술적 Agreement가 도출됨
    - Phase-2는 **Resolution 텍스트 블록만 추출** (Decision은 Phase-1 status로 커버)
    
    ---
    
    ## 2. Competency Questions
    
    > Ontology 101 원칙
    >
    > *"One of the ways to determine the scope of the ontology is to sketch a list of questions that a knowledge base based on the ontology should be able to answer."*
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
    
    ### CQ4. 역할 (Moderator) — **제외**
    
    | # | Competency Question | 제외 이유 |
    | --- | --- | --- |
    | 4-1 | 특정 Agenda Item의 Moderator는 누구(어느 회사)인가? | Moderator 0건 |
    | 4-2 | 특정 회사가 Moderator를 맡은 Agenda Item 목록은? | Moderator 0건 |
    | 4-3 | 특정 회사의 Moderator 담당 비율은? | Moderator 0건 |
    
    **RAN4 설계**: Moderator 0건으로 **CQ4 전체 제외**.
    
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
    
    **RAN4 설계**: Moderator 0건으로 CQ6-3(Moderator 추이) **제외**.
    
    ---
    
    ### CQ 결과 규칙
    
    ### 정렬 기준 (Default Sort Order)
    
    | CQ 그룹 | Primary Sort | Secondary Sort | 구현 속성 |
    | --- | --- | --- | --- |
    | CQ1. Resolution 조회 | Meeting 번호 DESC | Agenda 번호 ASC, Sequence ASC | `meetingNumberInt DESC` |
    | CQ2. Tdoc ↔ Resolution | Meeting 번호 DESC | Sequence ASC | `meetingNumberInt DESC` |
    | CQ3. 회사별 기여도 | Count DESC | Company 이름 ASC | `count DESC` |
    | CQ6. 트렌드/비교 | Meeting 번호 ASC (시계열) | — | `meetingNumberInt ASC` |
    
    // ★ 최신 우선 원칙: 명시적 요청 없으면 항상 DESC (CQ6 제외 — 시계열)
    
    ### 결과 개수 (Default Limit)
    
    | CQ 유형 | 기본값 | 적용 CQ |
    | --- | --- | --- |
    | 목록 조회 | 10 | CQ1-1~1-7, CQ2 |
    | Top N 조회 | 10 | CQ1-8, CQ3 |
    | 트렌드 조회 | 전체 | CQ6 |
    
    ---
    
    ## 3. Scope 정의
    
    ### 3.1 포함 (In Scope)
    
    | 구분 | 포함 대상 | 비고 |
    | --- | --- | --- |
    | **Resolution** | Agreement, Conclusion, Working Assumption | CQ1~3, CQ6 |
    | **Embedded Content** | Table | Resolution 완결성 위해 포함. RF 측정 테이블 다수 |
    | **데이터 소스** | Final Report 본문 | Annex 제외 |
    
    ### 3.2 제외 (Out of Scope)
    
    | 제외 대상 | 이유 |
    | --- | --- |
    | `Decision:` 패턴 | Phase-1 status와 중복. Resolution이 아닌 문서 처리 결과 |
    | Summary (Moderator) | Moderator 0건. 구조화 패턴 없음 |
    | SessionNotes (Chair) | 0건 |
    | Rapporteur | 구조화 어려움 |
    | Annex (B, C, D, E, F) | 본문만 파싱 원칙 |
    | ~~Figure~~ | **v2**: 50KB+ 구조적 필터 기반 포함으로 변경 — Appendix A [P2-V05] 참조 |
    | ~~Chart/Equation~~ | **v2**: Chart/Equation(OMML) 포함으로 변경 — Chart 수는 Appendix A [P2-V06] 참조 |
    | ~~contentWithEquations~~ | **v2**: 수식 포함 Resolution에 한하여 생성 |
    | CQ4 (역할) | Moderator 0건 |
    | CQ5 (후속 조치) | Annex 의존 |
    
    ### 3.3 용어 구분
    
    | 용어 | 정의 | 비고 |
    | --- | --- | --- |
    | **Resolution** | `Agreement:`/`Conclusion:`/`WA:` 시작 텍스트 블록 | 온톨로지 추출 대상 |
    | **Decision** | `Decision: The document was ...` 한 줄 패턴 | Phase-1 status 대응. 추출 대상 아님 |
    
    ---
    
    ## 4. CQ 요약
    
    | CQ 그룹 | 상태 |
    | --- | --- |
    | CQ1. Resolution 조회 | ✅ 포함 |
    | CQ2. Tdoc ↔ Resolution 추적 | ✅ 포함 |
    | CQ3. 회사별 기여도 | ✅ 포함 |
    | CQ4. 역할 (Moderator) | ❌ 제외 (Moderator 0건) |
    | CQ5. 후속 조치 | ❌ 제외 (Annex 의존) |
    | CQ6. 트렌드/비교 | ✅ 포함 — CQ6-3 제외 |
    
    ---
    
    ## Step 2: 기존 온톨로지 재사용 검토
    
    > Ontology 101 원칙
    >
    >
    > *"It is almost always worth considering what someone else has done and checking if we can refine and extend existing sources for our particular domain and task."*
    >
    > — Noy & McGuinness, Ontology Development 101
    >
    
    ---
    
    ## 1. 재사용 검토 대상
    
    ### 1.1 Phase-1 온톨로지
    
    | 항목 | 내용 |
    | --- | --- |
    | 도메인 | 3GPP RAN4 Tdoc 메타데이터 |
    | 데이터 소스 | Tdoc_list (Excel) |
    
    ### 1.2 외부 표준 온톨로지
    
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
    | **Company** | CQ3 (기여도) | ✅ 필수 |
    | **Release** | CQ1-5 (Release별 Resolution) | ✅ 필수 |
    | **Spec** | CQ1-6, CQ3-3 (Spec별 Resolution) | ✅ 필수 |
    | **WorkItem** | CQ1-7, CQ3-2 (WI별 Resolution) | ✅ 필수 |
    | CR | (Spec 연결 시 간접 사용) | ⚠️ 간접 |
    | LS | — | ❌ 불필요 |
    | Contact | — | ❌ 불필요 |
    | WorkingGroup | — | ❌ 불필요 |
    
    **Company 사용처**: RAN4는 CQ4 제외로 CQ3(회사별 기여도)에서만 Company를 사용.
    
    ### 2.2 재사용 클래스 결정
    
    | 구분 | 클래스 |
    | --- | --- |
    | **필수** | Tdoc, Meeting, AgendaItem, Company, Release, Spec, WorkItem |
    | **간접** | CR (Tdoc 하위 클래스 유지) |
    | **불필요** | LS, Contact, WorkingGroup |
    
    ---
    
    ## 3. Phase-1 관계 재사용 검토
    
    | 구분 | 관계 | 관련 CQ |
    | --- | --- | --- |
    | **필수** | submittedBy, belongsTo, presentedAt, targetRelease, relatedTo, modifies | CQ1~3, CQ6 |
    | **간접** | isRevisionOf, revisedTo | 유지 |
    | **불필요** | hasContact, sentTo, ccTo, originalLS, originatedFrom, replyTo, replyIn | Phase-2에서 직접 사용 안 함 |
    
    ---
    
    ## 4. 외부 온톨로지 재사용
    
    | 온톨로지 | Phase-1 용도 | Phase-2 결정 |
    | --- | --- | --- |
    | Dublin Core | Tdoc title, identifier | ✅ 유지 |
    | FOAF | Company, Contact | ✅ 유지 |
    | 추가 온톨로지 | — | ❌ 불필요 |
    
    ---
    
    ## 5. 요약
    
    | 구분 | 대상 |
    | --- | --- |
    | **Phase-1 클래스** | Tdoc, Meeting, AgendaItem, Company, Release, Spec, WorkItem |
    | **Phase-1 관계** | submittedBy, belongsTo, presentedAt, targetRelease, relatedTo, modifies |
    | **외부 온톨로지** | Dublin Core, FOAF |
    
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
    
    - 도메인에서 나오는 **명사, 동사를 나열**
    - 아직 **클래스/속성 구분 없이** 후보 용어로 정리
    - Final Report 본문에서 **실제로 추출 가능한지** 확인
    
    ---
    
    ## 2. 데이터 소스
    
    | 항목 | 내용 |
    | --- | --- |
    | 대상 | RAN4 Final Report (RAN4-99 빈 파일 스킵) |
    | 형식 | Word 문서 (.docx) |
    | 범위 | 본문만 (Annex 제외) |
    
    ---
    
    ## 3. 용어 나열
    
    ### 3.1 Resolution 관련
    
    | 용어 | 여러 인스턴스? | 독립 객체? | 클래스 여부 |
    | --- | --- | --- | --- |
    | **Agreement** | ✅ | ✅ | ✅ 클래스 |
    | **Conclusion** | ✅ | ✅ | ✅ 클래스 |
    | **Working Assumption** | ✅ | ✅ | ✅ 클래스 |
    
    ### 3.2 Role 관련 — **제외**
    
    > RAN4 Final Report 56개 전수 스캔 결과:
    >
    > - **Moderator: 0건** — 구조화 패턴 없음
    > - Rapporteur: 구조화 어려움 → 제외
    > - FL Summary: 0건, Ad-hoc Chair: 0건 → 제외
    >
    > **RAN4 설계**: Moderator 0건으로 Summary 클래스 및 관련 CQ를 **전체 제외**.
    
    ### 3.3 Relationship 관련
    
    | 용어 | 의미 | 관련 CQ |
    | --- | --- | --- |
    | **references** | Resolution이 Tdoc을 참조 | CQ2-1, CQ2-2 |
    | **madeAt** | Resolution이 Meeting에서 도출 | CQ1-1~1-3 |
    | **resolutionBelongsTo** | Resolution이 AgendaItem에 속함 | CQ1-4 |
    | **hasTable** | Resolution이 Table을 참조 | — |
    | **containedIn** | Table이 Meeting에 포함 | — |
    
    *제외: `moderatedBy` (Moderator 0건). **v2**: `hasFigure`/`hasChart` 포함 (Figure/Chart 수는 Appendix A [P2-V05]/[P2-V06] 참조).*
    
    ### 3.4 Property 관련
    
    | 용어 | 의미 | 관련 CQ |
    | --- | --- | --- |
    | **content** | Resolution 본문 텍스트 | CQ2-3 |
    | **contentWithEquations** (v2) | 수식 포함 Resolution의 LaTeX 치환 본문 | — |
    | **resolutionId** | Resolution 고유 식별자 | 전체 |
    | **sequence** | 같은 Agenda 내 순서 | CQ1 |
    | **hasConsensus** | 합의 수준 표시 | — |
    | **note** | 부가 설명 | — |
    | **hasFFS** | "For Further Study" 포함 여부 | — |
    | **hasTBD** | "To Be Determined" 포함 여부 | — |
    
    *제외: `summaryType` (Summary 클래스 없음), `roundNumber` (Summary 없음). **v2**: `contentWithEquations` 포함 (Equation OMML → LaTeX).*
    
    ### 3.5 Embedded Content 관련
    
    | 용어 | 패턴 | 비고 |
    | --- | --- | --- |
    | **Table** | 보고서 내 테이블 | RF 측정 등 기술적 테이블 다수 — Appendix A [P2-V04] 참조 |
    | **Figure** (v2) | 보고서 내 이미지 | 캡션 기반 + 50KB+ 구조적 필터 — Appendix A [P2-V05] 참조 |
    | **Chart** (v2) | 보고서 내 차트 (c:chart XML) | Appendix A [P2-V06] 참조 |
    | **Equation** (v2) | OMML 수식 → LaTeX 변환 | RAN4-78~96 집중 |
    
    ---
    
    ## 4. CQ별 필요 용어 매핑
    
    | CQ | 필요 용어 |
    | --- | --- |
    | CQ1-1~1-3 | Agreement, Conclusion, WA, madeAt |
    | CQ1-4 | Resolution, resolutionBelongsTo |
    | CQ1-5~1-7 | Resolution, references → Phase-1 Tdoc/Release/Spec/WorkItem |
    | CQ1-8 | Resolution, resolutionBelongsTo |
    | CQ2-1~2-4 | Resolution, references, content |
    | CQ3-1~3-4 | Resolution, references → Phase-1 Tdoc/Company/WorkItem/Spec |
    | CQ6-1~6-2 | CQ1, CQ3 용어 + madeAt |
    
    ---
    
    ## 5. 요약
    
    ### 5.1 용어 목록
    
    | 카테고리 | 용어 |
    | --- | --- |
    | **Resolution** | Agreement, Conclusion, Working Assumption |
    | **Relationship** | references, madeAt, resolutionBelongsTo, hasTable, containedIn |
    | **Property** | content, resolutionId, sequence, hasConsensus, note, hasFFS, hasTBD |
    | **Embedded Content** | Table |
    
    ### 5.2 RAN4 제외 항목
    
    | 구분 | RAN4 | 근거 |
    | --- | --- | --- |
    | **Summary 클래스** | ❌ **제외** | Moderator 0건 |
    | **moderatedBy** | ❌ **제외** | Moderator 0건 |
    | **summaryType** | ❌ **제외** | Summary 없음 |
    | **CQ4 (역할)** | ❌ **제외** | Moderator 0건 |
    | **CQ6-3** | ❌ **제외** | Moderator 0건 |
    | SessionNotes | ❌ 제외 | 0건 |
    | ~~Figure/Chart/Equation~~ | **✅ 포함 (v2)** | Figure/Chart 클래스 + contentWithEquations 속성 활성화 (수치는 Appendix A [P2-V05]/[P2-V06] 참조) |
    
    ### 5.3 검증
    
    | 검증 항목 | 결과 |
    | --- | --- |
    | 모든 CQ가 나열된 용어로 답변 가능? | ✅ |
    | 모든 용어가 Step 1 Scope 내? | ✅ |
    | Final Report에서 추출 가능? | ✅ |
    | Step 2 직접 정의 목록과 일치? | ✅ |
    
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
    
    ### 3.2 Role 관련 용어 — **제외**
    
    > Moderator 0건. Summary 클래스 불필요.
    
    ### 3.3 기타 용어
    
    | 용어 | 판단 |
    | --- | --- |
    | references, madeAt, resolutionBelongsTo, hasTable, containedIn | ❌ 관계 (Step 5) |
    | content, resolutionId, sequence, sessionContext, note, hasFFS, hasTBD, hasConsensus | ❌ 속성 (Step 5) |
    
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
    
    ### 4.2 Tdoc 확장 클래스 — 해당 없음
    
    > RAN4는 Moderator 0건으로 Summary(Moderator 기반) 클래스 **해당 없음**.
    
    ### 4.3 Embedded Content 클래스
    
    | 클래스 | 정의 | Graph DB 저장 | 별도 저장소 |
    | --- | --- | --- | --- |
    | **Table** | 문서 내 삽입된 테이블 | ID, caption, filePath | 원본 HTML |
    | **Figure** (v2) | 문서 내 삽입된 그림 (캡션 기반 + 50KB+ 구조적) | ID, caption, filePath, figureNumber | 원본 이미지 |
    | **Chart** (v2) | 문서 내 삽입된 차트 (c:chart XML) | ID, caption, filePath, chartNumber | 원본 XML |
    
    **Table을 클래스로 정의하는 이유**:
    
    - 여러 인스턴스를 가지며 Resolution과 참조 관계를 가짐
    - 기술적 Table 대상 (포맷팅용 제외). RF 측정, EMC 시험 결과 등 기술적 테이블이 다수 (수량은 Appendix A [P2-V04] 참조)
    - 캡션 유무와 무관하게 Resolution 본문에 포함된 실질적 콘텐츠를 추출하며, 식별 기준은 Step 7에서 정의
    
    **Figure/Chart v2 복원**:
    
    - 초기 Spec은 "Figure/Chart/Equation → 제외"로 기록했으나, 전수 스캔 결과 실제 존재가 확인됨 (수량은 Appendix A [P2-V05]/[P2-V06] 참조).
    - 원시 미디어 파일 대부분이 수식 이미지 PNG이며, 50KB+ 필터로 실제 figure를 추출.
    - Chart는 c:chart XML 직접 식별.
    - Equation(OMML)은 Pandoc으로 LaTeX 변환 → `contentWithEquations` 속성에 저장 (RAN4-78~96 집중).
    - 따라서 Figure/Chart/contentWithEquations는 이제 **포함**. 본 Spec 이후 섹션의 "제외" 표기는 v1 기록 (Appendix A v2 override 참조).
    
    ---
    
    ## 5. 전체 클래스 계층 다이어그램
    
    ```
    ┌─────────────────────────────────────────────────────────────────┐
    │                    RAN4 Meeting Ontology                        │
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
    │  Table ⭐       Figure ⭐ (v2)       Chart ⭐ (v2)              │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘
    ```
    
    ⭐ = Phase-2 신규 클래스
    
    **RAN4 설계**: Summary 클래스 없음 (Moderator 0건).
    
    ---
    
    ## 6. 요약
    
    ### 6.1 Phase-2 신규 클래스
    
    | 계층 | 클래스 |
    | --- | --- |
    | **Resolution 계층** | Resolution (abstract), Agreement, Conclusion, WorkingAssumption |
    | **Embedded Content** | Table |
    
    **총 신규: 5개**
    
    ### 6.2 클래스로 정의하지 않은 용어
    
    | 용어 | 이유 | 처리 |
    | --- | --- | --- |
    | references, madeAt 등 | 관계 | Step 5 |
    | content, note 등 | 속성 | Step 5 |
    
    ### 6.3 RAN4 제외 클래스
    
    | 클래스 | RAN4 | 근거 |
    | --- | --- | --- |
    | Summary | **❌** | Moderator 0건 |
    | SessionNotes | **❌** | 0건 |
    | ~~Figure~~ | **✅ 포함 (v2)** | 50KB+ 구조적 필터 — Appendix A [P2-V05] 참조 |
    | ~~Chart~~ | **✅ 포함 (v2)** | c:chart XML — Appendix A [P2-V06] 참조 |
    
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
    | resolutionId | String | Resolution 고유 식별자 (예: AGR-98-8.1-001) |
    | content | String | Resolution 본문 텍스트 |
    | sequence | Integer | 같은 Agenda 내 순서 |
    | sessionContext | String | 세션 정보 (예: "Thursday session", "Online") |
    | note | String | 부가 설명 (Note: ...) |
    
    > ~~제외: contentWithEquations (수식 0건이므로 content만 사용. Step 1 §1.6 근거)~~ → **v2**: contentWithEquations 포함 (Equation OMML, RAN4-78~96 집중)
    
    **Object Property**
    
    | Property | Range | Description |
    | --- | --- | --- |
    | references | Tdoc | Resolution이 참조하는 Tdoc |
    | madeAt | Meeting | Resolution이 도출된 회의. Phase-1 Meeting의 `canonicalMeetingNumber`와 매칭 |
    | resolutionBelongsTo | AgendaItem | Resolution이 속한 Agenda |
    | hasTable | Table | Resolution이 참조하는 Table |
    
    > **v2**: Figure/Chart 클래스 복원에 따라 `hasFigure`/`hasChart` Object Property도 구현 가능. 현재는 `containedIn` (Figure/Chart → Meeting)만 생성하고 Resolution과의 직접 관계는 구현 미정 (Step 4 §4.3 Embedded Content 참조).

    > **🔴 Phase-1 ↔ Phase-2 정규화 일관성 (필수)**: Phase-2 loader는 `madeAt`/`containedIn`에서 추출한 canonical을 **Phase-1과 동일한 정규화 함수**로 처리한 후 `MERGE` 키로 사용해야 한다. Phase-1은 canonical에서 `-e` suffix 제거. Phase-2가 정규화를 생략하면 같은 미팅이 두 노드로 분기되어 NULL id placeholder 발생. `MERGE`의 `ON CREATE SET` 에 `m.id` 속성도 명시 부여 (Phase-1 id 패턴과 동일). 구현: Phase-2 loader의 canonical 정규화 헬퍼 함수 사용.
    
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
    
    > RAN4는 WA 3건으로 `promotedTo` (WA → Agreement) 관계의 자동 추출이 어려워 제외.
    
    ---
    
    ## 4. Tdoc 확장 클래스 속성 — 해당 없음
    
    > RAN4는 Moderator 0건으로 Summary 클래스 없음. **해당 없음**.
    
    ---
    
    ## 5. Embedded Content 클래스 속성
    
    ### 5.1 Table
    
    **Data Property**
    
    | Property | Type | Description |
    | --- | --- | --- |
    | tableId | String | Table 고유 식별자 (예: TBL-98-001) |
    | caption | String | Table 캡션 텍스트 |
    | filePath | String | 원본 테이블 파일 경로 (HTML) |
    | tableNumber | String | 원본 Table 번호 (예: "Table 7.8-1") |
    
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
    
    **총 신규 OP: 6개**
    
    > 제외: moderatedBy (Moderator 0건), chairedBy, promotedTo. **v2**: hasFigure/hasChart 복원 (수치는 Appendix A [P2-V05]/[P2-V06] 참조)
    
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
    
    **총 신규 DP: 12개**
    
    > 제외: summaryType (Summary 없음), roundNumber. **v2**: contentWithEquations + Figure/Chart 관련 속성 복원
    
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
    
    **모든 CQ 답변 가능** ✅ (Step 1 CQ 설계 참조)
    
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
    | sequence | Integer | 1 | ✅ | 같은 Agenda 내 순서. *Note: resolutionId에서 추출 가능 (예: AGR-98-8.1-001의 001)* |
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
    
    ---
    
    ## 4. Object Property Facet
    
    ### 4.1 Resolution 관계
    
    | Property | Domain | Range | Cardinality | Functional | Inverse |
    | --- | --- | --- | --- | --- | --- |
    | references | Resolution | Tdoc | 0..* | ❌ | - |
    | madeAt | Resolution | Meeting | 1 | ✅ | - |
    | resolutionBelongsTo | Resolution | AgendaItem | 1 | ✅ | hasResolutions |
    | hasTable | Resolution | Table | 0..* | ❌ | - |
    
    > ~~제외: hasFigure, hasChart~~ → **v2**: 포함 (수치는 Appendix A [P2-V05]/[P2-V06] 참조)
    > madeAt Cardinality: 1 (RAN4는 Resolution이 단일 회의에 귀속)
    
    ### 4.2 WorkingAssumption 추가 관계 — 해당 없음
    
    > `promotedTo` (WA → Agreement) 제외. RAN4는 WA 3건으로 자동 추출 어려움.
    
    ### 4.3 AgendaItem 역관계 (Phase-1 확장)
    
    | Property | Domain | Range | Cardinality | Functional | Inverse |
    | --- | --- | --- | --- | --- | --- |
    | hasResolutions | AgendaItem | Resolution | 0..* | ❌ | resolutionBelongsTo |
    
    ### 4.4 Summary 관계 — 해당 없음
    
    > Moderator 0건. Summary 클래스 없음. moderatedBy 관계 없음.
    
    ### 4.5 Embedded Content 관계
    
    | Property | Domain | Range | Cardinality | Functional | Inverse |
    | --- | --- | --- | --- | --- | --- |
    | containedIn | Table | Meeting | 1 | ✅ | - |
    
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
    | **Phase-2** | **Final Report (Word)** | 🔲 구현 예정 |
    
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
    | Agreement | resolutionId | `AGR-{meeting}-{agenda}-{seq}` | AGR-98-8.1-001 |
    | Conclusion | resolutionId | `CON-{meeting}-{agenda}-{seq}` | CON-98-9.2-001 |
    | WorkingAssumption | resolutionId | `WA-{meeting}-{agenda}-{seq}` | WA-98-8.1-001 |
    
    **ID 구성 요소**:
    
    - `{meeting}`: **정규화된** 회의 번호 (예: `78`, `98`, `117`, `101bis`) — 하이픈 없는 `{숫자}[bis]` 형식
    - `{agenda}`: Agenda Item 번호 (예: 8.1, 9.2.1)
    - `{seq}`: 해당 Agenda 내 순번 (001, 002, ...)

    > **E-3 Resolution ID `{meeting}` 정규화 규칙 (엣지 케이스 해소)**:
    > - **최종 형식**: `{숫자}[bis]` 단일 형식만 사용. 하이픈/밑줄·`-e`/`-bis-e`/`_eBis` 잔존 금지. (예: 정규화 결과 `101bis`, 금지 형식 `101-bis`, `101-bis-e`, `101_bis-e`).
    > - **정규화 함수** (`str.lower` 선행): `Bis`→`bis`, `-bis-e`→`bis`, `_eBis`→`bis`, `bis_e`→`bis`, 접두 하이픈(`-bis`)→`bis`, `-e`/`_e` 말미 제거. Phase-1 `canonicalMeetingNumber`와 1:1 대응.
    > - **예시 ID**: `AGR-101bis-8.1-001`, `AGR-98bis-8.1-001`. `AGR-101-bis-8.1-001` 같은 중간 형태는 생성 금지(orphan 원인).
    > - **bis 파일명 변종**: Phase-1은 TDoc List 파일명 기준 **6변종**, Phase-2는 Final Report 파일명 기준 **3변종**(대상 파일 집합 차이, v14 라운드 F-1 문서화). 정규화된 `{meeting}` 값은 두 Phase에서 동일.
    
    ### 3.3 Embedded Content ID
    
    | 클래스 | ID 속성 | 패턴 | 예시 |
    | --- | --- | --- | --- |
    | Table | tableId | `TBL-{meeting}-{seq}` | TBL-98-001 |
    
    **ID 구성 요소**:
    
    - `{meeting}`: 회의 번호 (예: 78, 98, 117, 101-bis)
    - `{seq}`: 해당 회의 내 순번 (001, 002, ...)
    
    > ~~제외: Figure ID (FIG-), Chart ID (CHT-)~~ → **v2**: 포함 (FIG-{meeting}-{seq:03d}, CHT-{meeting}-{seq:03d})
    
    ---
    
    ## 4. 데이터 소스 매핑
    
    ### 4.1 Resolution 매핑
    
    **소스**: Final Report 본문
    
    | 관계 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | references → Tdoc | content 내 참조 | `R4-\\d{7}` 패턴 추출 (7자리). 실측 매칭 수: [P2-V07] |
    | madeAt → Meeting | 문서 메타 | 파일명에서 회의 번호 추출 후 Phase-1 Meeting의 `canonicalMeetingNumber`와 매칭 |
    | resolutionBelongsTo → AgendaItem | 섹션 헤더 | Agenda 번호 추출. **같은 미팅 내의 AgendaItem과 매칭** (madeAt으로 결정된 Meeting의 AgendaItem) |
    | hasTable → Table | content 내 참조 | `Table X.Y.Z-N` 패턴 → 같은 미팅 내 TBL 인스턴스 연결. 실측 매칭 수: [P2-V08] |
    
    > RAN4 TDoc 패턴: `R4-\\d{7}` (7자리)
    
    **references → Tdoc 매칭 실패 시 처리 규칙:**
    
    | 조건 | 처리 |
    | --- | --- |
    | 추출된 Tdoc 번호가 Phase-1 인스턴스에 존재 | 기존 인스턴스에 references 관계 생성 |
    | 추출된 Tdoc 번호가 Phase-1 인스턴스에 없음 (다른 WG 문서 등) | references 관계 생성 안 함 + 로그 기록 |
    
    *참고: Resolution 본문에서 추출된 `R4-\\d{7}` 패턴이 Phase-1 Tdoc 인스턴스에 존재하지 않을 수 있음. 이 경우 동적 생성하지 않고 관계를 생략함*
    
    **Meeting 연결 규칙:**
    
    | Final Report 파일명 | 추출된 회의 번호 (정규화 후) | 매칭 대상 (Phase-1) |
    | --- | --- | --- |
    | Final_Report_RAN4-98.docx | RAN4#98 | canonicalMeetingNumber = "RAN4#98" |
    | Final_Report_RAN4-78Bis.docx | RAN4#78bis (Bis→bis) | canonicalMeetingNumber = "RAN4#78bis" |
    | Final_Report_RAN4-108bis.docx | RAN4#108bis | canonicalMeetingNumber = "RAN4#108bis" |
    | Final_Report_RAN4-104bis-e.docx | RAN4#104bis (`-e` 제거) | canonicalMeetingNumber = "RAN4#104bis" |
    | Final_Report_RAN4-98bis_e.docx | RAN4#98bis (`_e` 제거) | canonicalMeetingNumber = "RAN4#98bis" |
    | Final_Report_RAN4-101-bis-e.docx | RAN4#101bis (`-bis-e`→`bis`) | canonicalMeetingNumber = "RAN4#101bis" |
    | Final_Report_RAN4-94_eBis.docx | RAN4#94bis (`_eBis`→`bis`) | canonicalMeetingNumber = "RAN4#94bis" |
    
    **미팅 번호 추출:**
    
    > 파일명 기반으로 미팅 번호 추출. bis 6변종(Bis/bis/bis-e/bis_e/-bis-e/_eBis) 정규화 처리 (Bis→bis, `-e`/`_e` 제거, `-bis-e`/`_eBis`→`bis`). Phase-1 canonicalMeetingNumber 규칙과 일치.
    
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
    | 1 | `no [0~1단어] consensus` | "no consensus", "no RAN4 consensus" |
    | 2 | `not [0~1단어] consensus` | "not consensus", "currently not consensus" |
    | 3 | `did not reach consensus` |  |
    | 4 | `could not reach consensus` |  |
    | 5 | `has not reached consensus` |  |
    | 6 | `lack of consensus` |  |
    
    *참고: "not supported"는 합의 결과가 미지원인 것이며 합의 부재가 아니므로 false 대상이 아님*
    
    ### 4.4 WorkingAssumption 추가 매핑
    
    > `promotedTo` 매핑 제외. RAN4는 WA 3건으로 자동 추출 어려움.
    
    ### 4.5 Summary 매핑 — 해당 없음
    
    > RAN4는 Moderator 0건. Summary 클래스 없음.
    
    ### 4.6 Table 매핑
    
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
    
    ### 4.7 Heading 스타일 매핑 규칙
    
    > RAN4 Final Report에는 다양한 Heading 스타일이 존재.
    > Agenda Item 추출 시 이들도 매핑해야 함.
    
    | Heading 스타일 | 매핑 | 비고 |
    | --- | --- | --- |
    | Heading 2 | Agenda Level 1 | 표준 |
    | Heading 3 | Agenda Level 2 | 표준 |
    | Heading 4 | Agenda Level 3 | 표준 (최다 빈도) |
    | Heading 5 | Agenda Level 4 | 표준 |
    | Heading 6 | Agenda Level 5 | 표준 |
    | Heading 7 | Agenda Level 6 | 표준 |
    | toc 1~7 | **Heading N과 동일 레벨로 매핑** | RAN4 고유: Heading 스타일 대신 toc 사용 |
    | TOC 1~3 (대문자) | **toc N과 동일 레벨로 매핑** | RAN4 고유: 대문자 TOC 변종 |
    | **R4_Topic** | **본문 텍스트로 처리 (Agenda 아님)** | RAN4 고유 커스텀 스타일 |
    | **FP** | 본문 텍스트로 처리 | 커스텀 소수 |
    | **TH** | 본문 텍스트로 처리 | 커스텀 소수 |
    
    ### 4.8 Null 값 처리 규칙
    
    | 속성/관계 | 상황 | 처리 | 로그 레벨 |
    | --- | --- | --- | --- |
    | content | 파싱 실패 | Resolution 인스턴스 미생성 | ERROR |
    | references | Tdoc 번호가 Phase-1 인스턴스에 없음 | 해당 참조만 스킵 (§4.1 참조) | WARNING |
    | references | Tdoc 번호 파싱 실패 | 해당 참조만 스킵 | WARNING |
    | caption (Table) | 캡션 없음 | null 유지 (정상) | - |
    
    **처리 원칙:**
    
    - `content`(Resolution)은 필수 속성(Cardinality: 1)이므로 값을 채울 수 없으면 인스턴스 자체를 생성하지 않음
    - `caption`은 선택 속성(Cardinality: 0..1)이므로 null이 정상
    
    ### 4.9 RAN4-99 빈 파일 처리
    
    > RAN4-99는 빈 파일. Heading/Resolution/Table 모두 0건.
    > **파서에서 자동 스킵** 처리. 로그에 SKIP 기록.
    
    ---
    
    ## 5. 예시 인스턴스
    
    ### 5.1 Agreement 예시
    
    ```json
    {
      "@type": "Agreement",
      "resolutionId": "AGR-98-8.1-001",
      "content": "The test tolerance for band n104 BS conducted emission is defined as...",
      "sequence": 1,
      "note": null,
      "hasFFS": false,
      "hasTBD": false,
      "references": [
        { "@id": "tdoc:R4-2401234" },
        { "@id": "tdoc:R4-2401235" }
      ],
      "resolutionBelongsTo": { "@id": "agenda:8.1" },
      "madeAt": { "@id": "meeting:RAN4#98" }
    }
    ```
    
    ### 5.2 Conclusion 예시
    
    ```json
    {
      "@type": "Conclusion",
      "resolutionId": "CON-98-9.2-001",
      "content": "RAN4 concludes that the current requirement is sufficient for the specified frequency range",
      "sequence": 1,
      "hasConsensus": true,
      "resolutionBelongsTo": { "@id": "agenda:9.2" },
      "madeAt": { "@id": "meeting:RAN4#98" }
    }
    ```
    
    ### 5.3 WorkingAssumption 예시
    
    ```json
    {
      "@type": "WorkingAssumption",
      "resolutionId": "WA-98-8.1-001",
      "content": "For FR2 UE, the minimum peak EIRP requirement shall apply...",
      "sequence": 1,
      "resolutionBelongsTo": { "@id": "agenda:8.1" },
      "madeAt": { "@id": "meeting:RAN4#98" }
    }
    ```
    
    ### 5.4 Table 예시
    
    ```json
    {
      "@type": "Table",
      "tableId": "TBL-98-001",
      "caption": "Test parameters for BS conducted emission measurement",
      "filePath": "...",
      "tableNumber": "Table 7.8-1",
      "containedIn": { "@id": "meeting:RAN4#98" }
    }
    ```
    
    **캡션 없는 Table 예시**
    
    ```json
    {
      "@type": "Table",
      "tableId": "TBL-98-015",
      "filePath": "...",
      "containedIn": { "@id": "meeting:RAN4#98" }
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
    | Agreement | `Agreement:` 시작 텍스트 블록 | content, references, hasFFS, hasTBD |
    | Conclusion | `Conclusion:` 시작 텍스트 블록 | content, hasConsensus |
    | WorkingAssumption | `Working Assumption:`/`WA:` 시작 텍스트 블록 | content |
    | Table | 캡션 패턴 또는 구조 기반 | caption (Optional), filePath, tableNumber |
    
    ### 6.3 RAN4 파싱/설계 특성
    
    | 항목 | RAN4 |
    | --- | --- |
    | TDoc 참조 패턴 | **`R4-\\d{7}` (7자리)** |
    | 미팅 번호 소스 | **파일명** |
    | bis 미팅 | **Bis/bis/bis-e/bis_e/-bis-e/_eBis 6변종** (Phase-1 canonical과 일치) |
    | 빈 파일 | **RAN4-99 (스킵)** |
    | Heading 추가 스타일 | **toc 1~7, TOC 1~3, R4_Topic, FP, TH** |
    | Summary | **❌** (Moderator 0건) |
    | SessionNotes | **❌** (0건) |
    | ~~Figure/Chart/Equation~~ | **✅ 포함 (v2)** — 수치는 Appendix A [P2-V05]/[P2-V06]/[P2-V09] 참조 |
    | ~~contentWithEquations~~ | **✅ 포함 (v2)** — 580 OMML 태그 실측 (Appendix A [P2-V09]) |
    | roundNumber | **❌** (Summary 없음) |
    
    ---
    
    ## 7. 전체 완료
    
    Phase-2 온톨로지 설계가 완료되었습니다.
    
    ### 7.1 Embedded Content 처리 요약
    
    | 대상 | Graph DB | 별도 저장소 | 변환 방식 |
    | --- | --- | --- | --- |
    | **Table** | 메타데이터 (ID, caption, filePath) | 원본 HTML | XML 파싱 + HTML 변환 |
    | **Figure** (v2) | 메타데이터 (ID, caption, filePath) | 원본 이미지 | 캡션 기반 + 50KB+ 구조적 |
    | **Chart** (v2) | 메타데이터 (ID, caption, filePath) | 원본 XML | c:chart XML 직접 식별 |
    
    > **v2**: Figure/Chart/Equation 포함으로 변경. Equation은 contentWithEquations 속성으로 LaTeX 변환.
    
    ---
    
    ## Appendix A: 기준 수치
    
    > 이 테이블이 Spec의 수치 권위 소스이다.
    >
    
    > 새 미팅 데이터 추가 시 이 테이블만 수정한다.
    >
    
    | ID | 항목 | 기준값 | 비고 |
    | --- | --- | --- | --- |
    | P2-V01 | Agreement 수 | 1,905 | 55개 Report 파싱 결과 (v2 실측) |
    | P2-V02 | Conclusion 수 | 77 | 55개 Report 파싱 결과 |
    | P2-V03 | WorkingAssumption 수 | 3 | 55개 Report 파싱 결과 |
    | P2-V04 | Table 수 | 1,388 | 55개 Report 파싱 결과. 캡션+구조 기반 식별 |
    | P2-V05 | Figure 수 | 28 | v2 — 캡션 기반 + 구조적(50KB+) |
    | P2-V06 | Chart 수 | 13 | v2 — c:chart XML 직접 식별 |
    | P2-V07 | REFERENCES 관계 수 | 8,111 | Resolution → Tdoc (Phase-1 매칭 성공분) |
    | P2-V08 | HAS_TABLE 관계 수 | 236 | Resolution → Table 참조 |
    | P2-V09 | OMML 수식 태그 수 | 580 | DOCX 본문 실측 (m:oMath 510 + m:oMathPara 70). 19개 미팅(RAN4-78~96 구간) 374 paragraph 분포. Pandoc OMML→LaTeX 변환 → contentWithEquations 속성. 재파싱 후 실제 contentWithEquations 보유 Resolution 수는 변환 성공률에 따라 별도 측정 (검증 명령은 본 Spec 부록 참조). |
    
    > **사전 스캔 vs 실측 차이** (Step 1 §1.6 비교):
    > - 사전 스캔 예상(~1,566): Agreement 1,488 + Conclusion 75 + WA 3
    > - 실측(1,985): Agreement 1,905 + Conclusion 77 + WA 3
    > - Agreement 28% 증가(파싱 방법론 차이), Conclusion/WA 거의 일치
    > - Table: 사전 스캔 ~1,113 → 실측 1,388 (24% 증가, 구조 기반 식별 기여)
    > - **v2 추가**: Figure/Chart 복원. 사전 Spec은 "21/0 제외"로 기록했으나 실측은 28/13. 원시 미디어 파일 592개 대부분이 수식 이미지 PNG이며, 50KB+ 필터로 실제 figure 28개 추출.
    > - **v2 추가**: Equation 수치 정정. 초기 Spec "22"는 단위 불명확(과소 기재). DOCX 원본 OMML 태그 수 실측 = 580 (m:oMath 510 + m:oMathPara 70). 분포: RAN4-78~96 19개 미팅, 374 paragraph (전체 RAN4 56개 미팅 중 RAN4-97~117 30개는 0건). 의사결정 컨텍스트(Proposal/Agreement 직전 3 paras) 인접 비율: 50.8% (190/374 paragraph). [P2-V09] 참조.
    
    > 제외: Summary 수, MODERATED_BY 관계 수 (Moderator 0건), SessionNotes (Chair 0건)
    
    ### A.1.1 v1 → v2 변경 사항 (단일 참조 표)
    
    > 본 Spec은 v1 초판에서 v2로 개정되었다. 본문에 v1 취소선(`~~…~~`)과 v2 주석이 분산되어 있으므로, **현재 유효한 설계 결정은 반드시 아래 표 기준**으로 판단한다.
    
    | 항목 | v1 (초판) | v2 | 위치(참고) |
    | --- | --- | --- | --- |
    | Embedded Equation (OMML→LaTeX) | 제외 | **포함** (580 OMML, [P2-V09]) | §3.2, §3.5, §6.3, §10.1 |
    | Embedded Figure | 제외 | **포함** (28건, [P2-V05]) | §3.2 |
    | Embedded Chart | 제외 | **포함** (13건, [P2-V06]) | §3.2 |
    | contentWithEquations 속성 | 없음 | **추가** (수식 있는 Resolution 한정) | §4 Resolution |
    | Summary / SessionNotes / Moderator | 포함 후보 | **최종 제외** (RAN4 실측 0건) | §1.6, §3.2, §6.2 |
    | roundNumber 속성 | 포함 | **제외** | §4 |
    
    **독자 규칙**: v1 시점의 "제외" 기술이 본문에 남아 있더라도, 위 표의 v2 값이 현재 유효한 최종 결정이다. Implementation/Implement CQ는 전부 v2 기준 18/18 PASS.
    
    ### A.2 구현 CQ 검증 결과
    
    > Spec Step 1의 CQ는 온톨로지 **설계 근거**이다.
    아래는 구현에서 사용하는 **검증 CQ**로, 설계 CQ를 포함하되 구현 검증용으로 확장/재구성되었다.
    >
    
    | 항목 | 설계 CQ (Spec) | 검증 CQ (구현) |
    | --- | --- | --- |
    | 데이터셋 | 18개 (CQ1×8, CQ2×4, CQ3×4, CQ6×2) | Phase-2 CQ 데이터셋 |
    | 검증 결과 | - | **18/18 PASS** (v2) |
    | 결과 파일 | - | Phase-2 CQ Cypher 결과 |
    
    ---
