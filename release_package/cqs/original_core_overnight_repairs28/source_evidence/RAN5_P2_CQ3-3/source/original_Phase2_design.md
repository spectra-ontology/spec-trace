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
    
    **3GPP RAN5 Final Report 본문에 기록된 Resolution(결의) 정보**
    
    RAN5 Final Report는 **Resolution 텍스트 블록**(`Conclusion:`)과 **Decision 패턴**(`Decision:\tThe document was agreed.`)이 공존하는 구조를 가진다. 단, 다른 WG와 달리 `Agreement:` 헤딩이 사실상 존재하지 않으며, `Working Assumption:` 또한 없다.
    
    - Conclusion: 기술적 결론 원문 — Phase-2 핵심 추출 대상 ([P2-V01])
    - Decision: 문서 단위 처리 결과 — Phase-1 status와 중복이므로 Phase-2 Scope 밖
    - Agreement: 사실상 없음 → **제외**
    - Working Assumption: 없음 → **제외**
    - Discussion: TDoc 논의 맥락 텍스트 → Tdoc 속성 확장으로 처리 ([P2-V05])
    - Moderator: 없음 → **제외**
    
    ### 1.2 For what are we going to use the ontology?
    
    **Phase-1 Tdoc 중심 온톨로지를 확장**하여 다음을 지원:
    
    - 회의 결과 분석 — 무엇이 합의/결론되었는가
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
    
    - 대상: RAN5#76 ~ RAN5#110 Final Report
    - 파일: Final Report DOCX
    - bis/-e suffix 없음 (순번만)
    
    ### 1.5 전제 조건
    
    > 본 온톨로지는 Phase-1 Tdoc 온톨로지의 확장이다.
    >
    > Phase-1에서 정의된 클래스 및 관계를 재사용하며, 구체적인 재사용 범위는 Step 2에서 검토한다.
    >
    
    ### 1.6 RAN5 Final Report 구조 특성 (전수 스캔 결과)
    
    | 항목 | **RAN5** | 근거 |
    | --- | --- | --- |
    | **Resolution 구조** | **Conclusion만** (Agreement/WA 없음) | 전수 스캔 |
    | **Resolution 건수** | [P2-V01] | 실측치 |
    | **Decision 패턴** | 존재 | Phase-1 status 중복 → 제외 |
    | **Discussion 텍스트** | [P2-V05] (50자 초과) | Tdoc 속성 확장 |
    | **Moderator** | **없음 (제외)** | 전수 스캔 |
    | **FL Summary** | **없음** | |
    | **SessionNotes** | **없음 (제외)** | |
    | **Embedded Equation** | **없음** | |
    | **Embedded Figure** | **소량 (제외)** | Resolution 완결성 미기여 |
    | **Embedded Table** | 존재 | 포함 |
    | **Heading 스타일** | **Heading 1~8 + TOC1~8 (표준만, 커스텀 없음)** | 전수 스캔 확인 |
    | **TDoc 참조 패턴** | **R5-NNNNNN (6자리)** | |
    | **bis 미팅** | **없음** (-e suffix 없음) | |
    | **빈 파일** | **없음** | |
    | **Final Report 수** | RAN5#76~#110 (순번만) | |
    
    ### 1.7 RAN5 Phase-2 Discussion과 Conclusion의 관계
    
    RAN5 Final Report에서 **Discussion과 Conclusion은 서로 다른 레벨의 정보**이다:
    
    ```
    [TDoc] R5-241234 CB:#6_UEConTest (discussion)
      Decision:	The document was agreed.   ← TDoc 단위 처리 결과 (Phase-1 status)
      (Discussion text block)              ← 논의 맥락 텍스트 ([P2-V05])
      Conclusion: The test case for...     ← 기술적 결론 원문 ([P2-V01])
    ```
    
    - **Discussion**: TDoc 논의 맥락. 50자 초과 유의미 텍스트 ([P2-V05]). Tdoc 속성(`discussionText`)으로 확장
    - **Conclusion**: 기술적 결론. 독립 Resolution 객체로 모델링
    - **Decision**: Phase-1 status와 1:1 대응. Phase-2 추출 대상 아님
    - RAN5 Final Report는 Agreement 헤딩이 없는 구조 → Conclusion이 유일한 Resolution 하위 클래스
    
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
    | 1-1 | 특정 회의에서 도출된 Conclusion 목록은? |
    | 1-2 | 특정 Agenda Item에서의 Resolution(Conclusion) 목록은? |
    | 1-3 | 특정 Release 관련 Resolution 목록은? |
    | 1-4 | 특정 Spec을 변경하는 Resolution 목록은? |
    | 1-5 | 특정 Work Item의 Resolution 목록은? |
    | 1-6 | Resolution이 가장 많은 Agenda Item Top N은? |
    
    > Agreement 0건/Working Assumption 0건이므로 Agreement 조회, WA 조회 CQ는 **제외**. CQ 번호는 Conclusion 기준으로 정렬.
    
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
    | 목록 조회 | 10 | CQ1-1~1-5, CQ2 |
    | Top N 조회 | 10 | CQ1-6, CQ3 |
    | 트렌드 조회 | 전체 | CQ6 |
    
    ---
    
    ## 3. Scope 정의
    
    ### 3.1 포함 (In Scope)
    
    | 구분 | 포함 대상 | 비고 |
    | --- | --- | --- |
    | **Resolution** | Conclusion | CQ1~3, CQ6 |
    | **Discussion** | TDoc 논의 맥락 텍스트 | Tdoc 속성(`discussionText`)으로 확장 |
    | **Embedded Content** | Table | Resolution 완결성 위해 포함 |
    | **데이터 소스** | Final Report 본문 | Annex 제외 |
    
    ### 3.2 제외 (Out of Scope)
    
    | 제외 대상 | 이유 |
    | --- | --- |
    | `Agreement:` 텍스트 블록 | 사실상 없음. Resolution으로 취급 불가 |
    | `Working Assumption:` | 데이터 없음 |
    | `Decision:` 패턴 | Phase-1 status와 중복. Resolution이 아닌 문서 처리 결과 |
    | Summary (Moderator) | Moderator 없음. 구조화 패턴 없음 |
    | SessionNotes (Chair) | 없음 |
    | Rapporteur | 구조화 어려움 |
    | Annex (B, C, D, E, F) | 본문만 파싱 원칙 |
    | Figure | 소량. Resolution 완결성에 기여 미미 |
    | Chart/Equation | 없음 |
    | contentWithEquations | 수식 없음 |
    | CQ4 (역할) | Moderator 없음 |
    | CQ5 (후속 조치) | Annex 의존 |
    
    ### 3.3 용어 구분
    
    | 용어 | 정의 | 비고 |
    | --- | --- | --- |
    | **Conclusion** | `Conclusion:` 시작 텍스트 블록 | 온톨로지 추출 대상 ([P2-V01]) |
    | **Discussion** | TDoc 논의 블록의 텍스트 | Tdoc 속성 확장 대상 ([P2-V05]) |
    | **Decision** | `Decision:\tThe document was ...` 한 줄 패턴 | Phase-1 status 대응. 추출 대상 아님 |
    
    ---
    
    ## 4. CQ 요약
    
    | CQ 그룹 | 상태 |
    | --- | --- |
    | CQ1. Resolution 조회 | ✅ 포함 |
    | CQ2. Tdoc ↔ Resolution 추적 | ✅ 포함 |
    | CQ3. 회사별 기여도 | ✅ 포함 |
    | CQ4. 역할 (Moderator) | ❌ 제외 (Moderator 0건) |
    | CQ5. 후속 조치 | ❌ 제외 (Annex 의존) |
    | CQ6. 트렌드/비교 | ✅ 포함 |
    
    > CQ 개수 및 분포는 §3 CQ 목록 참조.
    
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
    | 도메인 | 3GPP RAN5 Tdoc 메타데이터 |
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
    | **AgendaItem** | CQ1-2 (Agenda별 Resolution) | ✅ 필수 |
    | **Company** | CQ3 (기여도) | ✅ 필수 |
    | **Release** | CQ1-3 (Release별 Resolution) | ✅ 필수 |
    | **Spec** | CQ1-4, CQ3-3 (Spec별 Resolution) | ✅ 필수 |
    | **WorkItem** | CQ1-5, CQ3-2 (WI별 Resolution) | ✅ 필수 |
    | CR | (Spec 연결 시 간접 사용) | ⚠️ 간접 |
    | LS | — | ❌ 불필요 |
    | Contact | — | ❌ 불필요 |
    | WorkingGroup | — | ❌ 불필요 |
    
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
    | 대상 | RAN5 Final Report |
    | 형식 | Word 문서 (.docx) |
    | 범위 | 본문만 (Annex 제외) |
    
    ---
    
    ## 3. 용어 나열
    
    ### 3.1 Resolution 관련
    
    | 용어 | 여러 인스턴스? | 독립 객체? | 클래스 여부 | RAN5 건수 |
    | --- | --- | --- | --- | --- |
    | **Conclusion** | ✅ | ✅ | ✅ 클래스 | [P2-V01] |
    
    **제외 대상 (전수 스캔 근거):**
    - Agreement: 사실상 없음 → **제외**
    - Working Assumption: 없음 → **제외**
    
    ### 3.2 Role 관련 — **제외**
    
    > RAN5 Final Report 전수 스캔 결과:
    >
    > - **Moderator**: 없음 — 구조화 패턴 없음
    > - Rapporteur: 구조화 어려움 → 제외
    > - FL Summary: 없음, Ad-hoc Chair: 없음 → 제외
    >
    > 위 항목 모두 없으므로 Role 관련 클래스/속성 전체 제외.
    
    ### 3.3 Discussion 관련 — **RAN5 고유**
    
    | 용어 | 여러 인스턴스? | 독립 객체? | 클래스 여부 | RAN5 건수 |
    | --- | --- | --- | --- | --- |
    | **Discussion** | ✅ | ❌ (Tdoc 속성) | ❌ 속성 | [P2-V05] |
    
    > Discussion 텍스트는 TDoc 논의 맥락으로, 독립 객체가 아니라 **Tdoc의 속성(`discussionText`)**으로 모델링.
    > 50자 초과 유의미 텍스트만 저장.
    
    ### 3.4 Relationship 관련
    
    | 용어 | 의미 | 관련 CQ |
    | --- | --- | --- |
    | **references** | Resolution이 Tdoc을 참조 | CQ2-1, CQ2-2 |
    | **madeAt** | Resolution이 Meeting에서 도출 | CQ1-1 |
    | **resolutionBelongsTo** | Resolution이 AgendaItem에 속함 | CQ1-2 |
    | **hasTable** | Resolution이 Table을 참조 | — |
    | **containedIn** | Table이 Meeting에 포함 | — |
    
    *hasFigure, hasChart 미정의: Figure/Chart는 Resolution 완결성에 기여하지 않아 클래스 미정의*
    
    ### 3.5 Property 관련
    
    | 용어 | 의미 | 관련 CQ |
    | --- | --- | --- |
    | **content** | Resolution 본문 텍스트 | CQ2-3 |
    | **resolutionId** | Resolution 고유 식별자 | 전체 |
    | **sequence** | 같은 Agenda 내 순서 | CQ1 |
    | **hasConsensus** | 합의 수준 표시 | — |
    | **note** | 부가 설명 | — |
    | **hasFFS** | "For Further Study" 포함 여부 | — |
    | **hasTBD** | "To Be Determined" 포함 여부 | — |
    | **discussionText** | TDoc 논의 맥락 텍스트 | — |
    
    *`discussionText`: RAN5 Final Report의 Discussion 텍스트(50자 초과, [P2-V05])를 TDoc 속성으로 확장*
    
    ### 3.6 Embedded Content 관련
    
    | 용어 | 패턴 | 비고 |
    | --- | --- | --- |
    | **Table** | 보고서 내 테이블 | [P2-V02] (캡션+구조 기반 식별) |
    
    *Figure (소량 — Resolution 완결성 미기여), Chart (없음), Equation (없음) → 모두 클래스 미정의*
    
    ---
    
    ## 4. CQ별 필요 용어 매핑
    
    | CQ | 필요 용어 |
    | --- | --- |
    | CQ1-1 | Conclusion, madeAt |
    | CQ1-2 | Resolution, resolutionBelongsTo |
    | CQ1-3~1-5 | Resolution, references → Phase-1 Tdoc/Release/Spec/WorkItem |
    | CQ1-6 | Resolution, resolutionBelongsTo |
    | CQ2-1~2-4 | Resolution, references, content |
    | CQ3-1~3-4 | Resolution, references → Phase-1 Tdoc/Company/WorkItem/Spec |
    | CQ6-1~6-2 | CQ1, CQ3 용어 + madeAt |
    
    ---
    
    ## 5. 요약
    
    ### 5.1 용어 목록
    
    | 카테고리 | 용어 |
    | --- | --- |
    | **Resolution** | Conclusion |
    | **Discussion** | discussionText (Tdoc 속성) |
    | **Relationship** | references, madeAt, resolutionBelongsTo, hasTable, containedIn |
    | **Property** | content, resolutionId, sequence, hasConsensus, note, hasFFS, hasTBD, discussionText |
    | **Embedded Content** | Table |
    
    ### 5.2 RAN5 포함/제외 결정 요약
    
    | 구분 | RAN5 | 근거 |
    | --- | --- | --- |
    | **Agreement** | ❌ **제외** | 사실상 없음 |
    | **Working Assumption** | ❌ **제외** | 없음 |
    | **discussionText** | ✅ **추가** | [P2-V05] |
    | CQ4 (역할) | ❌ 제외 | Moderator 없음 |
    | CQ5 (후속 조치) | ❌ 제외 | Annex 의존 |
    | Figure | ❌ 제외 | 소량, Resolution 완결성 미기여 |
    
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
    | **Conclusion** | ✅ | ✅ | ✅ 클래스 |
    
    → Conclusion만으로도 "회의에서 도출된 결의"라는 일반 개념 → **상위 클래스 Resolution** 유지 (WG 간 일관성)
    
    **제외 대상 (Step 1 §1.6 근거):**
    - Agreement: 사실상 없음 → **제외**
    - Working Assumption: 없음 → **제외**
    
    ### 3.2 Role 관련 용어 — **제외**
    
    > Moderator 없음. Summary 클래스 불필요.
    
    ### 3.3 Discussion 관련 — **속성 확장 (클래스 아님)**
    
    > Discussion 텍스트는 TDoc 논의 맥락으로, 독립 객체가 아니라 **Tdoc의 속성(`discussionText`)**으로 모델링.
    > 클래스가 아닌 Data Property로 처리 (Step 5에서 정의).
    
    ### 3.4 기타 용어
    
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
    | **└─ Conclusion** | 논의 결론 | [P2-V01] |
    
    **Resolution을 상위 클래스로 유지하는 이유**:
    
    - 상위 클래스 Resolution 유지 시 "Resolution" 통합 조회 쿼리 패턴 재사용 가능
    - RAN5에서 Conclusion만 존재하더라도 상위 클래스 유지가 cross-WG 쿼리에 유리
    
    > Agreement(사실상 없음→제외), WorkingAssumption(없음→제외)으로 Conclusion만 남음.
    
    ### 4.2 Tdoc 확장 클래스 — 해당 없음
    
    > Moderator 없음이므로 Summary 클래스 불필요.
    > 단, Tdoc에 `discussionText` 속성이 추가됨 (Step 5에서 정의).
    
    ### 4.3 Embedded Content 클래스
    
    | 클래스 | 정의 | Graph DB 저장 | 별도 저장소 |
    | --- | --- | --- | --- |
    | **Table** | 문서 내 삽입된 테이블 | ID, caption, filePath | 원본 HTML |
    
    **Table을 클래스로 정의하는 이유**:
    
    - 여러 인스턴스를 가지며 Resolution과 참조 관계를 가짐
    - 기술적 Table 대상 (포맷팅용 제외). RF 적합성 시험, 성능 검증 결과 등 기술적 테이블 ([P2-V02])
    - 캡션 유무와 무관하게 Resolution 본문에 포함된 실질적 콘텐츠를 추출하며, 식별 기준은 Step 7에서 정의
    
    > 미정의 클래스: Figure (소량 — Resolution 완결성 미기여), Chart (없음), Equation (없음)
    
    ---
    
    ## 5. 전체 클래스 계층 다이어그램
    
    ```
    ┌─────────────────────────────────────────────────────────────────┐
    │                    RAN5 Meeting Ontology                        │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                 │
    │  Tdoc (Phase-1)                   Resolution (Phase-2 신규)     │
    │  ├── CR (Phase-1)                 └── Conclusion ⭐             │
    │  └── LS (Phase-1)                                               │
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
    ├─────────────────────────────────────────────────────────────────┤
    │  속성 확장 (Phase-2 신규)                                        │
    │                                                                 │
    │  Tdoc.discussionText ⭐                                        │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘
    ```
    
    ⭐ = Phase-2 신규 클래스/속성
    
    **RAN5 특징**: Agreement, WorkingAssumption 미정의. discussionText 속성 확장 추가.
    
    ---
    
    ## 6. 요약
    
    ### 6.1 Phase-2 신규 클래스
    
    | 계층 | 클래스 |
    | --- | --- |
    | **Resolution 계층** | Resolution (abstract), Conclusion |
    | **Embedded Content** | Table |
    
    **총 신규: 3개**
    
    ### 6.2 클래스로 정의하지 않은 용어
    
    | 용어 | 이유 | 처리 |
    | --- | --- | --- |
    | references, madeAt 등 | 관계 | Step 5 |
    | content, note 등 | 속성 | Step 5 |
    | Discussion | Tdoc 속성 | Step 5 (discussionText DP) |
    
    ### 6.3 RAN5 미정의 클래스와 근거
    
    | 클래스 | **RAN5** | 근거 |
    | --- | --- | --- |
    | Agreement | **❌** | 사실상 없음 |
    | WorkingAssumption | **❌** | 없음 |
    | Summary | **❌** | Moderator 없음 |
    | SessionNotes | **❌** | 없음 |
    | Figure | **❌** | 소량, Resolution 완결성 미기여 (Step 1 §1.6) |
    | Chart | **❌** | 없음 |
    
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
    
    하위 클래스(Conclusion)가 **공통으로 상속**하는 속성
    
    **Data Property**
    
    | Property | Type | Description |
    | --- | --- | --- |
    | resolutionId | String | Resolution 고유 식별자 (예: CON-98-8.1-001) |
    | content | String | Resolution 본문 텍스트 |
    | sequence | Integer | 같은 Agenda 내 순서 |
    | sessionContext | String | 세션 정보 (예: "Thursday session", "Online") |
    | note | String | 부가 설명 (Note: ...) |
    
    > contentWithEquations 미정의: 수식 0건이므로 content만 사용 (Step 1 §1.6 근거)
    
    **Object Property**
    
    | Property | Range | Description |
    | --- | --- | --- |
    | references | Tdoc | Resolution이 참조하는 Tdoc |
    | madeAt | Meeting | Resolution이 도출된 회의. Phase-1 Meeting의 `canonicalMeetingNumber`와 매칭 |
    | resolutionBelongsTo | AgendaItem | Resolution이 속한 Agenda |
    | hasTable | Table | Resolution이 참조하는 Table |
    
    > hasFigure, hasChart 미정의: Figure/Chart 클래스 미정의

    > **🔴 Phase-1 ↔ Phase-2 정규화 일관성 (필수)**: Phase-2 loader는 `madeAt`/`containedIn`에서 추출한 canonical을 **Phase-1과 동일한 정규화 함수**로 처리한 후 `MERGE` 키로 사용해야 한다. Phase-1은 canonical에서 `-e` suffix 제거. Phase-2가 정규화를 생략하면 같은 미팅이 두 노드로 분기되어 NULL id placeholder 발생. `MERGE`의 `ON CREATE SET` 에 `m.id` 속성도 명시 부여 (Phase-1 id 패턴과 동일). 구현: Phase-2 loader의 canonical 정규화 헬퍼 함수 사용. RAN5는 e-meeting 폴더가 `_Electronic` 형태라 canonical 자체에 `-e` suffix는 거의 없으나, 안전을 위해 동일 정규화 적용.
    
    ### 3.2 Conclusion
    
    Resolution 속성 상속 + 추가 속성
    
    **추가 Data Property**
    
    | Property | Type | Description |
    | --- | --- | --- |
    | hasConsensus | Boolean | 합의 도달 여부 |
    | hasFFS | Boolean | "For Further Study" 포함 여부 |
    | hasTBD | Boolean | "To Be Determined" 포함 여부 |
    
    > RAN5는 Agreement 없이 Conclusion만 존재하므로, **hasConsensus/hasFFS/hasTBD 세 속성 모두 Conclusion에 통합 정의**.
    
    ---
    
    ## 4. Tdoc 속성 확장 (discussionText)
    
    > RAN5 Final Report는 TDoc별 논의 맥락 텍스트(Discussion)가 존재 ([P2-V05]).
    > 독립 클래스가 아닌 **Phase-1 Tdoc의 Data Property 확장**으로 처리.
    
    **추가 Data Property**
    
    | Property | Domain | Type | Description |
    | --- | --- | --- | --- |
    | discussionText | Tdoc | String | TDoc 논의 맥락 텍스트 (50자 초과 유의미, [P2-V05]) |
    
    > Phase-1 Tdoc 클래스의 Data Property 확장.
    > 빈 값/50자 이하는 저장하지 않음.
    
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
    
    > 미정의 OP: moderatedBy (Moderator 없음), chairedBy, hasFigure, hasChart, promotedTo — 해당 클래스/데이터 부재
    
    ---
    
    ## 7. 전체 Data Property 목록 (Phase-2 신규)
    
    | # | Property | Domain | Type | Description |
    | --- | --- | --- | --- | --- |
    | 1 | resolutionId | Resolution | String | Resolution 고유 식별자 |
    | 2 | content | Resolution | String | Resolution 본문 텍스트 |
    | 3 | sequence | Resolution | Integer | 같은 Agenda 내 순서 |
    | 4 | sessionContext | Resolution | String | 세션 정보 |
    | 5 | note | Resolution | String | 부가 설명 |
    | 6 | hasConsensus | Conclusion | Boolean | 합의 도달 여부 |
    | 7 | hasFFS | Conclusion | Boolean | FFS 포함 여부 |
    | 8 | hasTBD | Conclusion | Boolean | TBD 포함 여부 |
    | 9 | discussionText | Tdoc | String | TDoc 논의 맥락 텍스트 |
    | 10 | tableId | Table | String | Table 고유 식별자 |
    | 11 | caption | Table | String | 캡션 텍스트 |
    | 12 | filePath | Table | String | 원본 파일 경로 |
    | 13 | tableNumber | Table | String | 원본 Table 번호 |
    
    **총 신규 DP: 13개**
    
    > Conclusion에 hasFFS/hasTBD 통합, discussionText 추가.
    > 미정의 DP: contentWithEquations, roundNumber, summaryType, Figure/Chart/equation 관련 속성 — 해당 클래스/데이터 부재
    
    ---
    
    ## 8. CQ 답변 가능성 검증
    
    | CQ | 필요 속성 | 정의 여부 |
    | --- | --- | --- |
    | CQ1-1 | madeAt, Conclusion | ✅ |
    | CQ1-2 | resolutionBelongsTo | ✅ |
    | CQ1-3 | references → Tdoc → targetRelease (Phase-1) | ✅ |
    | CQ1-4 | references → Tdoc → modifies (Phase-1) | ✅ |
    | CQ1-5 | references → Tdoc → relatedTo (Phase-1) | ✅ |
    | CQ1-6 | resolutionBelongsTo | ✅ |
    | CQ2-1~2-2 | references | ✅ |
    | CQ2-3 | content | ✅ |
    | CQ2-4 | references → Tdoc → modifies (Phase-1) | ✅ |
    | CQ3-1~3-4 | references → Tdoc → submittedBy (Phase-1) | ✅ |
    | CQ6-1~6-2 | madeAt (시계열) + CQ1/CQ3 속성 | ✅ |
    
    **16개 CQ 전체 답변 가능** ✅
    
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
    | sequence | Integer | 1 | ✅ | 같은 Agenda 내 순서. *Note: resolutionId에서 추출 가능 (예: CON-98-8.1-001의 001)* |
    | sessionContext | String | 0..1 | ❌ | 세션 정보 (예: "Thursday session", "Online") |
    | note | String | 0..1 | ❌ | 부가 설명 |
    
    ### 3.2 Conclusion
    
    Resolution 상속 + 추가 속성
    
    | Property | Type | Cardinality | Required | Description |
    | --- | --- | --- | --- | --- |
    | hasConsensus | Boolean | 0..1 | ❌ | 합의 도달 여부 |
    | hasFFS | Boolean | 0..1 | ❌ | default: false |
    | hasTBD | Boolean | 0..1 | ❌ | default: false |
    
    > RAN5는 Agreement 없이 Conclusion만 존재하므로, **hasConsensus/hasFFS/hasTBD 세 속성 모두 Conclusion에 통합**.
    
    ### 3.3 Tdoc 속성 확장
    
    | Property | Domain | Type | Cardinality | Required | Description |
    | --- | --- | --- | --- | --- | --- |
    | discussionText | Tdoc | String | 0..1 | ❌ | TDoc 논의 맥락 텍스트. 50자 초과만 저장 |
    
    > Phase-1 Tdoc 클래스에 Data Property 추가.
    
    ### 3.4 Table
    
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
    
    > hasFigure, hasChart 미정의.
    > madeAt Cardinality: 1 (RAN5는 bis 미팅 없음, COVID-19 특수 케이스 없음)
    
    ### 4.2 AgendaItem 역관계 (Phase-1 확장)
    
    | Property | Domain | Range | Cardinality | Functional | Inverse |
    | --- | --- | --- | --- | --- | --- |
    | hasResolutions | AgendaItem | Resolution | 0..* | ❌ | resolutionBelongsTo |
    
    ### 4.3 Summary 관계 — 해당 없음
    
    > Moderator 없음. Summary 클래스 없음. moderatedBy 관계 없음.
    
    ### 4.4 Embedded Content 관계
    
    | Property | Domain | Range | Cardinality | Functional | Inverse |
    | --- | --- | --- | --- | --- | --- |
    | containedIn | Table | Meeting | 1 | ✅ | - |
    
    ---
    
    ## 5. 필수 속성 요약
    
    ### 5.1 필수 Data Property
    
    | Class | Required Properties |
    | --- | --- |
    | Resolution | resolutionId, content, sequence |
    | Conclusion | (상속) |
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
    | **Phase-2** | **Final Report (Word)** | ✅ 구현 완료 |
    
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
    | Conclusion | resolutionId | `CON-{meeting}-{agenda}-{seq}` | CON-98-8.1-001 |
    
    > Agreement(AGR-), WorkingAssumption(WA-) ID 패턴 미정의 — 해당 클래스 없음. Conclusion만 존재.
    > `{meeting}`은 Phase-1 `canonicalMeetingNumber`와 매칭되는 회의 번호.
    
    **ID 구성 요소**:
    
    - `{meeting}`: 회의 번호
    - `{agenda}`: Agenda Item 번호 (예: 8.1, 9.2.1)
    - `{seq}`: 해당 Agenda 내 순번 (001, 002, ...)
    
    > RAN5는 bis 미팅 없음. 순번만.
    > Phase-1 canonicalMeetingNumber와 일치.
    
    ### 3.3 Embedded Content ID
    
    | 클래스 | ID 속성 | 패턴 | 예시 |
    | --- | --- | --- | --- |
    | Table | tableId | `TBL-{meeting}-{seq}` | TBL-98-001 |
    
    **ID 구성 요소**:
    
    - `{meeting}`: 회의 번호
    - `{seq}`: 해당 회의 내 순번 (001, 002, ...)
    
    > Figure ID (FIG-), Chart ID (CHT-) 미정의 — 해당 클래스 없음
    
    ---
    
    ## 4. 데이터 소스 매핑
    
    ### 4.1 Resolution 매핑
    
    **소스**: Final Report 본문
    
    | 관계 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | references → Tdoc | content 내 참조 | `R5-\\d{6}` 패턴 추출 (6자리) |
    | madeAt → Meeting | 문서 메타 | 파일명에서 회의 번호 추출 후 Phase-1 Meeting의 `canonicalMeetingNumber`와 매칭 |
    | resolutionBelongsTo → AgendaItem | 섹션 헤더 | Agenda 번호 추출. **같은 미팅 내의 AgendaItem과 매칭** (madeAt으로 결정된 Meeting의 AgendaItem) |
    | hasTable → Table | content 내 참조 | `Table X.Y.Z-N` 패턴 → 같은 미팅 내 TBL 인스턴스 연결 |
    
    > RAN5 TDoc 참조 패턴: `R5-\\d{6}` (6자리)
    
    **references → Tdoc 매칭 규칙 (Tdoc / CR / LS 모두 대상):**
    
    > Phase-1은 `R5-\d{6}` TDoc 번호를 **Tdoc / CR / LS 세 클래스**로 분류 적재한다. Resolution의 references는 세 클래스 모두를 대상으로 하며, 매칭 우선순위는 아래와 같다.
    
    | 순서 | 매칭 대상 | 조건 | 처리 |
    | --- | --- | --- | --- |
    | 1 | Tdoc 클래스 | Phase-1 Tdoc 인스턴스에 `tdocNumber` 일치 | references 관계 생성 |
    | 2 | CR 클래스 (Tdoc 하위 클래스) | Phase-1 CR 인스턴스에 `tdocNumber` 일치 | references 관계 생성 |
    | 3 | LS 클래스 (Tdoc 하위 클래스) | Phase-1 LS 인스턴스에 `tdocNumber` 일치 | references 관계 생성 |
    | 4 | 세 클래스 중 어디에도 없음 | Phase-1에 미존재 | 관계 생성 안 함 + WARNING 로그 |
    
    *구현 상세: Phase-1의 `Tdoc`이 상위(추상) 클래스이고 CR/LS가 하위 클래스로 정의되어 있으므로, Cypher 상에서는 `MATCH (t:Tdoc {tdocNumber: $num})`만으로도 CR·LS 인스턴스가 매칭된다 (Neo4j의 라벨 상속). 따라서 references의 Range는 Tdoc이지만 실제 매칭 대상에는 CR·LS도 포함된다.*
    
    *참고: Resolution 본문에서 추출된 `R5-\d{6}` 패턴이 Phase-1 Tdoc/CR/LS 어디에도 존재하지 않을 수 있음. 이 경우 동적 생성하지 않고 관계를 생략함.*
    
    **Meeting 연결 규칙:**
    
    | Final Report 파일명 | 추출된 회의 번호 | 매칭 대상 (Phase-1) |
    | --- | --- | --- |
    | Final_Report_RAN5-76.docx | RAN5#76 | canonicalMeetingNumber = "RAN5#76" |
    | Final_Report_RAN5-98.docx | RAN5#98 | canonicalMeetingNumber = "RAN5#98" |
    | Final_Report_RAN5-110.docx | RAN5#110 | canonicalMeetingNumber = "RAN5#110" |
    
    **미팅 번호 추출:**
    
    > 파일명 기반으로 미팅 번호 추출. RAN5는 bis 미팅 없음 (순번만).
    
    ### 4.2 Conclusion 추가 매핑
    
    | 속성 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | hasConsensus | content | 부정 합의 패턴 미포함 시 true |
    | hasFFS | content | `FFS` 포함 여부 → Boolean |
    | hasTBD | content | `TBD` 포함 여부 → Boolean |
    
    > RAN5는 Agreement 없이 Conclusion만 존재하므로, **세 속성 모두 Conclusion에서 매핑**.
    
    **부정 합의 패턴** (아래 중 하나라도 content에 포함되면 `hasConsensus = false`):
    
    | # | 패턴 | 매칭 예시 |
    | --- | --- | --- |
    | 1 | `no [0~1단어] consensus` | "no consensus", "no RAN5 consensus" |
    | 2 | `not [0~1단어] consensus` | "not consensus", "currently not consensus" |
    | 3 | `did not reach consensus` |  |
    | 4 | `could not reach consensus` |  |
    | 5 | `has not reached consensus` |  |
    | 6 | `lack of consensus` |  |
    
    *참고: "not supported"는 합의 결과가 미지원인 것이며 합의 부재가 아니므로 false 대상이 아님*
    
    ### 4.3 Discussion 매핑 (discussionText)
    
    **소스**: Final Report 본문 내 TDoc 논의 블록
    
    | 속성 | Domain | 소스 | 변환 규칙 |
    | --- | --- | --- | --- |
    | discussionText | Tdoc | TDoc 논의 텍스트 블록 | 50자 초과 텍스트만 저장. 빈 값/50자 이하 스킵 |
    
    **매핑 규칙:**
    
    - TDoc 번호(`R5-\\d{6}`)가 Phase-1 인스턴스에 존재하는 경우에만 `discussionText` 속성 추가
    - Phase-1 인스턴스에 없는 TDoc은 속성 추가 안 함 + 로그 기록
    - 같은 TDoc이 여러 회의에서 논의된 경우: 가장 긴 텍스트 보존 (또는 회의별로 "\n---\n"으로 구분 연결)
    
    > RAN5 Final Report 고유 매핑. Phase-1 Tdoc의 Data Property로 저장.
    
    ### 4.4 Summary 매핑 — 해당 없음
    
    > Moderator 없음. Summary 클래스 없음.
    
    ### 4.5 Table 매핑
    
    **소스**: Final Report 본문 `<w:tbl>`
    
    **식별 기준**:
    
    1. 캡션 기반: `Table X.X.X-X:` 패턴이 있는 경우
    2. 구조 기반: 캡션 없는 `<w:tbl>` 중 다음 세 조건을 **모두** 만족
        - (행 수 ≥ 4) — 헤더 1행 + 데이터 3행 이상
        - (숫자/수식 포함) — 각 셀 텍스트 중 하나 이상이 `\d`, `=`, `>=`, `<=`, `<`, `>` 중 하나를 포함
        - (agenda/일정표 패턴 제외) — 헤더 셀 텍스트에 다음 한국어/영어 키워드가 모두 부재: `agenda`, `Agenda Item`, `Tdoc list`, `Tdoc number`, `일정`, `시간`
    
    *Note: 단순 포맷팅 테이블 (agenda, 일정표, Tdoc 목록 등)은 제외. 판별은 첫 행(헤더) 텍스트로만 결정 — 후행 행 내용에 따라 흔들리지 않음.*
    
    *실측 근거: 사전 스캔 raw `<w:tbl>` 532개 → 위 3조건 적용 후 49개. 구체적 축소 경로는 Appendix B에 기록 권고 (감사 이슈 E-4).*
    
    **tableId `{seq}` 결정성 규칙 (감사 이슈 H-5 대응):**
    
    | 규칙 | 내용 |
    | --- | --- |
    | 순서 정의 | `{seq}`는 동일 미팅 내 Final Report의 `<w:tbl>` 출현 순서 (문서 시작부터 1, 2, 3, ...). python-docx 기준 `document.tables` 순서. |
    | 식별 기준 우선순위 | 식별 기준 (1) 또는 (2)를 만족한 Table에만 `{seq}` 번호 부여. 판별에서 탈락한 `<w:tbl>`은 `{seq}`를 소비하지 않음(skip). |
    | 멱등성 보장 | 동일 Final Report DOCX에 대해 재파싱 시 동일 `{seq}` 산출. 식별 기준이 결정적(헤더 셀 고정)이므로 재실행마다 동일 집합을 선별. |
    | Phase-10 재실행 대응 | 재파싱에서 식별 기준 변경으로 `{seq}`가 달라지면 이전 TBL 노드가 orphan으로 남을 수 있음. 식별 기준 변경은 Minor 버전 업 + cleanup_stale 처리 필요 (Phase-10 §3.5 stale cleanup 범위에 Table 포함). |
    
    | 속성 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | tableId | 자동 생성 | `TBL-{meeting}-{seq:03d}` (3자리 zero-pad, 위 결정성 규칙 적용) |
    | caption | 본문 패턴 | `Table X.X.X-X:` 이후 텍스트 (있는 경우만) |
    | filePath | 변환 저장 | HTML 파일 경로 |
    | tableNumber | 캡션 패턴 | `Table X.X.X-X` 추출 |
    
    | 관계 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | containedIn → Meeting | 문서 메타 | 파일명에서 회의 번호 추출 |
    
    ### 4.6 Heading 스타일 매핑 규칙
    
    > Final Report 전수 스캔 결과.
    > RAN5는 **표준 Heading/TOC 스타일만 사용** (커스텀 스타일 없음).
    
    | Heading 스타일 | 매핑 | 비고 |
    | --- | --- | --- |
    | Heading 1 | **본문 텍스트로 처리 (Agenda 아님)** | 문서 제목 등 |
    | Heading 2 | Agenda Level 1 | 표준 |
    | Heading 3 | Agenda Level 2 | 표준 |
    | Heading 4 | Agenda Level 3 | 표준 |
    | Heading 5 | Agenda Level 4 | 표준 |
    | Heading 6 | Agenda Level 5 | 표준 |
    | Heading 7 | Agenda Level 6 | 표준 |
    | Heading 8 | Agenda Level 7 | 표준 |
    | TOC1~TOC8 | **Heading N과 동일 레벨로 매핑** | Heading과 1:1 대응 |
    
    > RAN5는 표준 Heading/TOC만 사용하여 매핑이 단순함.
    
    ### 4.7 Null 값 처리 규칙
    
    | 속성/관계 | 상황 | 처리 | 로그 레벨 |
    | --- | --- | --- | --- |
    | content | 파싱 실패 | Resolution 인스턴스 미생성 | ERROR |
    | references | Tdoc 번호가 Phase-1 인스턴스에 없음 | 해당 참조만 스킵 (§4.1 참조) | WARNING |
    | references | Tdoc 번호 파싱 실패 | 해당 참조만 스킵 | WARNING |
    | discussionText | 50자 이하 | 저장하지 않음 (정상) | - |
    | caption (Table) | 캡션 없음 | null 유지 (정상) | - |
    
    **처리 원칙:**
    
    - `content`(Resolution)은 필수 속성(Cardinality: 1)이므로 값을 채울 수 없으면 인스턴스 자체를 생성하지 않음
    - `caption`은 선택 속성(Cardinality: 0..1)이므로 null이 정상
    - `discussionText`는 선택 속성(Cardinality: 0..1)이므로 50자 이하 스킵이 정상
    
    ---
    
    ## 5. 예시 인스턴스
    
    ### 5.1 Conclusion 예시
    
    ```json
    {
      "@type": "Conclusion",
      "resolutionId": "CON-98-8.1-001",
      "content": "RAN5 concludes that the test case for NR CA band combination shall be updated to reflect the latest agreed requirements",
      "sequence": 1,
      "hasConsensus": true,
      "hasFFS": false,
      "hasTBD": false,
      "references": [
        { "@id": "tdoc:R5-241234" }
      ],
      "resolutionBelongsTo": { "@id": "agenda:8.1" },
      "madeAt": { "@id": "meeting:RAN5#98" }
    }
    ```
    
    ### 5.2 Table 예시
    
    ```json
    {
      "@type": "Table",
      "tableId": "TBL-98-001",
      "caption": "Test parameters for NR CA band combination",
      "filePath": "...",
      "tableNumber": "Table 7.8-1",
      "containedIn": { "@id": "meeting:RAN5#98" }
    }
    ```
    
    **캡션 없는 Table 예시**
    
    ```json
    {
      "@type": "Table",
      "tableId": "TBL-98-015",
      "filePath": "...",
      "containedIn": { "@id": "meeting:RAN5#98" }
    }
    ```
    
    ### 5.3 Tdoc discussionText 예시
    
    ```json
    {
      "@type": "Tdoc",
      "@id": "tdoc:R5-241234",
      "discussionText": "The proponent presented the CR to update the test case for NR CA band combination. Several companies supported the approach but requested clarification on the minimum requirements for band n78..."
    }
    ```
    
    > Phase-1에서 생성된 Tdoc 인스턴스에 `discussionText` 속성을 추가하는 형태.
    
    ---
    
    ## 6. 요약
    
    ### 6.1 Phase-2 인스턴스 생성 명세
    
    | 클래스 | ID 패턴 | 데이터 소스 | 예상 수 |
    | --- | --- | --- | --- |
    | Conclusion | CON-{m}-{a}-{s} | Final Report 본문 | [P2-V01] |
    | Table | TBL-{m}-{s} | 본문 `<w:tbl>` (캡션 + 구조 기반) | [P2-V02] |

    
    > Agreement(AGR-), WorkingAssumption(WA-) 인스턴스 없음 — 해당 클래스 미정의
    
    ### 6.1.1 Resolution 합계와 REFERENCES 관계
    
    | 항목 | 값 | 비고 |
    | --- | --- | --- |
    | Resolution 합계 (Conclusion 단일 타입) | [P2-V04] | Agreement/WorkingAssumption 없음 → [P2-V01] = [P2-V04] |
    | REFERENCES 관계 수 (Resolution → Tdoc) | [P2-V03] | Phase-1 tdocNumber 매칭 성공분만 생성 |
    
    > RAN5 Phase-2는 Conclusion 단일 타입이므로 Resolution 합계는 Conclusion 수와 동일([P2-V01] = [P2-V04]).
    
    ### 6.2 매핑 규칙 요약
    
    | 클래스 | 식별 패턴 | 주요 추출 |
    | --- | --- | --- |
    | Conclusion | `Conclusion:` 시작 텍스트 블록 | content, hasConsensus, hasFFS, hasTBD |
    | Table | 캡션 패턴 또는 구조 기반 | caption (Optional), filePath, tableNumber |
    
    ### 6.3 추가 매핑 (discussionText)
    
    | 대상 | 매핑 | 주요 추출 |
    | --- | --- | --- |
    | Tdoc.discussionText | TDoc 논의 블록 텍스트 | 50자 초과 유의미 텍스트 |
    
    ### 6.4 RAN5 인스턴스 생성 결정 요약
    
    | 항목 | **RAN5** |
    | --- | --- |
    | TDoc 참조 패턴 | **`R5-\\d{6}` (6자리)** |
    | 미팅 번호 소스 | **파일명** |
    | bis 미팅 | **없음** |
    | 빈 파일 | **없음** |
    | Heading 추가 스타일 | **TOC1~8 (표준만, 커스텀 없음)** |
    | Summary | **❌** (Moderator 없음) |
    | SessionNotes | **❌** (없음) |
    | Figure/Chart/Equation | **❌** (소량/없음) |
    | discussionText | **✅** (TDoc 속성 확장) |
    | Agreement | **❌** (사실상 없음→제외) |
    | WorkingAssumption | **❌** (없음) |
    
    ---
    
    ## 7. 전체 완료
    
    Phase-2 온톨로지 설계가 완료되었습니다.
    
    ### 7.1 Embedded Content 처리 요약
    
    | 대상 | Graph DB | 별도 저장소 | 변환 방식 |
    | --- | --- | --- | --- |
    | **Table** | 메타데이터 (ID, caption, filePath) | 원본 HTML | XML 파싱 + HTML 변환 |
    
    > Figure/Chart/Equation 미정의: Figure 소량(완결성 미기여), Chart/Equation 없음
    
    ---
    
    ## Appendix A: 기준 수치
    
    > 이 테이블이 Spec의 수치 권위 소스이다.
    >
    
    > 새 미팅 데이터 추가 시 이 테이블만 수정한다.
    >
    
    | ID | 항목 | 기준값 | 비고 |
    | --- | --- | --- | --- |
    | P2-V01 | Conclusion 수 | **83** | 35개 Report 파싱 결과 |
    | P2-V02 | Table 수 | **49** | 35개 Report 파싱 결과. 캡션+구조 기반 식별 |
    | P2-V03 | REFERENCES 관계 수 | **343** | Resolution → Tdoc (Phase-1 매칭 성공분) |
    | P2-V04 | Resolution 합계 | **83** | Conclusion = P2-V01 |
    | P2-V05 | discussionText 수 | **43,626** | 50자 초과 유의미 텍스트 (Neo4j 실측) |
    
    > **사전 스캔 대비 실측치 비교**:
    > - Conclusion: 사전 스캔 ~75 → 실측 83 (+10.7%)
    > - Table: 사전 스캔 ~532 (raw w:tbl) → 실측 49 (캡션+구조 기반)
    > - discussionText: 사전 스캔 ~23,311 → 실측 43,626 (파싱 방법론 차이)
    
    > Agreement 수, WorkingAssumption 수 항목 없음 — 해당 클래스 미정의
    > discussionText 수 (P2-V05) — Phase-1 Tdoc 속성 확장 실측치
    
    ### A.2 구현 CQ 검증 결과
    
    > Spec Step 1의 CQ는 온톨로지 **설계 근거**이다.
    아래는 구현에서 사용하는 **검증 CQ**로, 설계 CQ를 포함하되 구현 검증용으로 확장/재구성되었다.
    >
    
    | 항목 | 설계 CQ (Spec) | 검증 CQ (구현) |
    | --- | --- | --- |
    | 데이터셋 | 16개 (CQ1×6, CQ2×4, CQ3×4, CQ6×2) | Phase-2 CQ 데이터셋 |
    | 검증 결과 | - | **16/16 PASS** |
    | 결과 파일 | - | Phase-2 CQ Cypher 결과 |
    
    ---
