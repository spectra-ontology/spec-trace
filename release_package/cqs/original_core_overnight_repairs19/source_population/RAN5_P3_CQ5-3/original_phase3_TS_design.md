- **phase-3: Ontology 101 기반 적합성 시험 엔지니어 타겟으로 확장 (TS)**
    
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
    
    **3GPP RAN5 Technical Specification(TS) 문서의 구조와 참조 관계**
    
    ### 1.2 For what are we going to use the ontology?
    
    **Phase-1~2 온톨로지를 확장**하여 다음을 지원:
    
    - TS 구조 탐색 — Section 계층 네비게이션
    - TS 간 참조 분석 — 문서 간 참조 관계 파악
    - CR → TS 연결 — CR이 어떤 TS/Section을 수정했는지 추적
    - Resolution → TS 연결 — Resolution이 승인한 CR의 TS 수정 추적
    
    ### 1.3 Who will use and maintain the ontology?
    
    | 사용자 | 핵심 니즈 |
    | --- | --- |
    | **적합성 시험 엔지니어** | TS 구조 파악, 시험 절차/요구사항 위치 찾기 |
    | **표준화 엔지니어** | CR이 수정한 Section 확인, 시험 요구사항 변경 추적 |
    | **전략/기획** | 기술 트렌드, 적합성 시험 변경 현황 |
    | **IP/특허** | 기술 표준 반영 현황, 시험 요구사항 기여 증거 |
    
    ### 1.4 데이터 소스
    
    | Phase | 데이터 소스 | 상태 |
    | --- | --- | --- |
    | Phase-1 | Tdoc_list (Excel) | ✅ 구축 완료 |
    | Phase-2 | Final Report (Word) | ✅ 구축 완료 |
    | **Phase-3** | **TS 문서 (Word)** | 🔶 신규 |
    
    ### 1.5 전제 조건
    
    > 본 온톨로지는 Phase-1~2 온톨로지의 확장이다.
    >
    >
    > Phase-1~2에서 정의된 모든 클래스, 관계, 인스턴스를 사용할 수 있으며, Phase-3는 TS 구조를 추가하고 기존 데이터와 연결한다.
    >
    
    ### 1.6 RAN5 TS 데이터 특성
    
    TS 사전 스캔 결과:
    
    | 항목 | 값 | 비고 |
    | --- | --- | --- |
    | TS 범위 | 38.5xx | 적합성 시험 TS |
    | Heading 스타일 | Heading 1~8 + 비표준 2종 | Heading 3 Specs, Heading 2.Head2A.2 |
    | **TOC 이중 구조** | toc N + Heading N 쌍 | RAN5 고유, toc N 필터링 필수 |
    | Annex 스타일 | Heading 8 (Heading 9 없음) | Annex는 level 1로 재매핑 |
    | Max depth | 7 (Heading 7) | 적합성 시험 케이스 세부 단계 |
    | 분할 TS | 존재 | 38.508-1, 38.521-1, 38.521-2, 38.521-4, 38.523-1, 38.533 |
    | Table | [P3-V02] | 적합성 시험표 다수 |
    | Figure | [P3-V03] | 시험 구성도 |
    | 38.591 시리즈 | 입력 파일 없음 → 처리 대상 외 | |
    | Cover 파일 | `*_cover.docx` 패턴 → 파싱 제외 | |
    
    ---
    
    ## 2. Scope 정의
    
    ### 2.1 포함 (In Scope)
    
    | 구분 | 포함 대상 |
    | --- | --- |
    | **TS 문서** | 38.508-1/2, 38.509, 38.521-1~5, 38.522, 38.523-1~3, 38.533, 38.551, 38.561 |
    | **Release 차원 (release-aware)** | 각 TS의 **release별 final 버전** (Rel-15/16/17/18/19). 동일 spec번호라도 release마다 **별개 Spec 노드**이며 sectionId·Spec IRI가 release 키를 포함한다 (예: `38.521-1-Rel-15-...` ≠ `38.521-1-Rel-18-...`; RAN5 spec은 전부 하이픈 spec이라 `38.521-1-Rel-18-6.2.4`처럼 release 토큰이 `-1` 뒤에 위치). spec×release 단위로 적재하되, **UE 적합성 TS 특성상 다수 release final이 forward-redirect void shell**(본문이 "requirements in Release N [ref]"로 후방 참조, 실질 내용은 1~2 release에만 존재) — 이 void shell도 redirect 텍스트를 검색 가능한 Section 내용으로 **faithful 적재**한다 (§9.4). release별 참여 spec·void shell 분포는 Appendix A.1.3 |
    | **Section 구조** | 본문 + Annex, 7레벨까지 (Heading 8 = Annex 대제목 → level 1) |
    | **Table 메타데이터** | ID, 캡션, 번호, 위치 |
    | **Figure 메타데이터** | ID, 캡션, 번호, 위치 |
    | **TS 간 참조** | Section 간 내부/외부 참조 |
    | **기존 연결** | Spec(Phase-1) ↔ TS(Phase-3) 매핑 |
    
    ### 2.2 제외 (Out of Scope)
    
    | 제외 대상 | 이유 |
    | --- | --- |
    | Section 본문 텍스트 | Vector DB 영역 |
    | Table 셀 데이터 | Vector DB 영역 |
    | 수식 내용 | Vector DB 영역 |
    | **Cover 파일** | 분할 TS의 표지만 포함. Section 0건 |
    | **38.591-1~4** | DOCX 입력 없음, Tdoc 0건. 파싱 대상 아님 |
    | **toc N 스타일** | TOC 영역. 본문 Heading과 중복 |
    | TS **intra-release** 버전 히스토리 (한 release 내 모든 draft/중간 버전) | 복잡도 증가, 향후 확장. release별 **final 버전 1개**만 적재 (release-aware). 각 release final의 버전값은 Spec 확장의 specVersion에 기록 (Step 5 §4 참조) |
    | RAN5 외 TS | Scope 한정 |
    
    ### 2.3 Graph DB vs Vector DB 경계
    
    | Graph DB (Phase-3) | Vector DB |
    | --- | --- |
    | Section ID, 번호, 제목, 레벨 | Section 본문 텍스트 |
    | Section 계층 관계 | 본문 임베딩 |
    | Table/Figure 메타데이터 | Table 셀 데이터 |
    | TS 간 참조 관계 | 수식 내용 |
    | CR/Resolution 연결 | |
    
    **연결 키**: sectionId (예: `38.521-1-Rel-18-6.2`, release-aware 포맷 `{specNumber}-{release}-{sectionNumber}`)
    
    ---
    
    ## 3. 용어 정의
    
    | 용어 | 정의 | 온톨로지 | 예시 |
    | --- | --- | --- | --- |
    | **TS** | Technical Specification 문서 | Spec (Phase-1) | 38.521-1 |
    | **Spec** | Phase-1 클래스명, TS와 동의어 | Spec | 38.521-1 |
    | **Section** | TS 내부 계층 구조 (본문 + Annex) | Section (Phase-3) | 6.2.1, A.1 |
    | **Clause** | Section의 3GPP 공식 용어 (동의어) | Section | 6.2.1 |
    | **Annex** | Section 중 알파벳으로 시작하는 것 | Section | A, A.1, B.2 |
    | **Table** | TS 내 표 | TSTable (Phase-3) | Table 6.2.1-1 |
    | **Figure** | TS 내 그림 | TSFigure (Phase-3) | Figure 6-1 |
    
    ### 3.1 용어 구분
    
    | 헷갈리는 것 | 구분 |
    | --- | --- |
    | Spec vs TS | 같음. Spec은 Phase-1 클래스명, TS는 3GPP 공식 용어 |
    | Section vs Clause | 같음. Section은 온톨로지 클래스명, Clause는 3GPP 공식 용어 |
    | Section vs Spec | 다름. Spec은 문서 전체, Section은 문서 내부 구조 |
    | Section vs Annex | Annex ⊂ Section. sectionNumber 패턴으로 구분 (`^[A-Z]` = Annex) |
    
    ### 3.2 RAN5 고유 용어
    
    | 용어 | 설명 | 영향 |
    | --- | --- | --- |
    | **분할 파일** | 대형 TS가 여러 DOCX로 분할 (38.523-1: 12파트) | 파싱 시 순서대로 병합 |
    | **파트 번호 TS** | 38.508-1/2, 38.521-1~5, 38.523-1~3 등 하이픈으로 구분된 독립 TS | 각각 별도 Spec 노드 |
    | **Cover 파일** | 표지만 포함된 DOCX (_cover 접미사) | 파싱에서 제외 |
    | **toc N 스타일** | TOC 영역에서 사용되는 스타일. 본문 Heading N과 동일 텍스트 | 파싱에서 제외 |
    
    ---
    
    ## 4. Competency Questions
    
    ### CQ1. TS 구조 탐색
    
    | # | Competency Question |
    | --- | --- |
    | 1-1 | 특정 TS의 전체 Section 목록은? |
    | 1-2 | 특정 Section의 하위 Section 목록은? |
    | 1-3 | 특정 Section의 상위 계층 경로는? (breadcrumb) |
    | 1-4 | 특정 TS에서 레벨 N인 Section 목록은? |
    | 1-5 | 특정 Section에 포함된 Table 목록은? |
    | 1-6 | 특정 Section에 포함된 Figure 목록은? |
    | 1-7 | 특정 Table이 속한 Section은? |
    | 1-8 | 특정 TS의 Table 전체 목록은? |
    | 1-9 | 특정 키워드가 제목에 포함된 Section 목록은? |
    | 1-10 | 특정 Table 번호로 TS와 Section 찾기 |
    
    ### CQ2. TS 간 참조 분석
    
    | # | Competency Question |
    | --- | --- |
    | 2-1 | 특정 Section이 참조하는 다른 TS Section 목록은? |
    | 2-2 | 특정 Section을 참조하는 다른 TS Section 목록은? (역참조) |
    | 2-3 | 특정 TS가 가장 많이 참조하는 다른 TS는? |
    | 2-4 | 가장 많이 참조되는 Section Top N은? |
    | 2-5 | 두 TS 간 참조 관계 요약은? |
    
    ### CQ3. CR → TS 연결
    
    | # | Competency Question | 경로 |
    | --- | --- | --- |
    | 3-1 | 특정 CR이 수정한 TS는? | CR → Spec |
    | 3-2 | 특정 CR이 수정한 TS의 Section 구조는? | CR → Spec → Section |
    | 3-3 | 특정 TS를 수정한 CR 목록은? | Spec ← CR |
    | 3-4 | 특정 Section을 수정한 CR 목록은? | clausesAffected 기반 * |
    | 3-5 | 특정 Work Item 관련 CR이 수정한 TS 목록은? | WorkItem → CR → Spec |
    | 3-6 | 특정 회사가 수정한 TS 목록은? | Company → CR → Spec |
    
    *CQ 3-4 제약사항: clausesAffected 있는 CR만 (Appendix A [P3-V05] 참조)*
    
    ### CQ4. Resolution → TS 연결
    
    | # | Competency Question | 경로 |
    | --- | --- | --- |
    | 4-1 | 특정 Resolution이 승인한 CR이 수정한 TS는? | Resolution → CR → Spec |
    | 4-2 | 특정 TS를 수정한 CR을 승인한 Resolution 목록은? | Spec ← CR ← Resolution |
    | 4-3 | 특정 회의에서 승인된 CR이 수정한 TS 목록은? | Meeting → Resolution → CR → Spec |
    | 4-4 | 특정 Work Item의 Resolution이 반영된 TS 목록은? | WorkItem → CR ← Resolution, CR → Spec |
    
    *CQ4 제약사항: RAN5 Phase-2는 Conclusion만. Resolution이 CR을 references하는 경우만 (Appendix A [P3-V06] 참조)*
    
    ### CQ5. 통합 분석
    
    | # | Competency Question |
    | --- | --- |
    | 5-1 | 특정 TS의 전체 변경 관련 CR 목록은? |
    | 5-2 | 특정 회사의 TS별 CR 기여 현황은? |
    | 5-3 | 특정 Release에서 변경된 TS 목록은? |
    | 5-4 | 가장 많이 CR이 발생한 TS Top N은? |
    
    ---
    
    ## 5. CQ 결과 규칙
    
    ### 5.1 정렬 기준 (Default Sort Order)
    
    | CQ 그룹 | Primary Sort | Secondary Sort |
    | --- | --- | --- |
    | CQ1. 구조 탐색 | Section 번호 ASC | - |
    | CQ2. 참조 분석 | 참조 횟수 DESC | Section 번호 ASC |
    | CQ3. CR 연결 | Meeting 번호 DESC | CR 번호 ASC |
    | CQ4. Resolution 연결 | Meeting 번호 DESC | Resolution ID ASC |
    | CQ5. 통합 분석 | Count DESC | TS 번호 ASC |
    
    ### 5.2 결과 개수 (Default Limit)
    
    | CQ 유형 | 기본값 | 적용 CQ |
    | --- | --- | --- |
    | 목록 조회 | 10 | CQ1-1~1-10, CQ2-1~2-2, CQ3-1~3-6, CQ4, CQ5-1~5-3 |
    | Top N 조회 | 10 | CQ2-3~2-4, CQ5-4 |
    | 단일 조회 | 1 | CQ1-7 |
    | 전체 조회 | 전체 | CQ1-3 (breadcrumb) |
    
    ---
    
    ## 6. 제약사항
    
    | 항목 | 제약 | 비고 |
    | --- | --- | --- |
    | **CR → Section 직접 연결** | Appendix A [P3-V05] 참조 | clausesAffected 필드 있는 CR만 |
    | **Resolution → CR 연결** | Appendix A [P3-V06] 참조 | Conclusion이 CR을 references하는 경우만 |
    | **TS 버전** | 단일 버전 (최신). specVersion에 기록 | 버전 히스토리 미지원 |
    | **TS 범위** | RAN5 38.5xx | 38.591 시리즈 제외 |
    | **분할 파일** | 파트별 순서대로 병합 파싱 | cover 파일 제외 |
    
    > **specVersion 추출 규칙**: Phase-3는 TS DOCX 파일명에서 버전 코드를 추출하여 Spec 노드의 specVersion 속성에 저장한다.
    >
    > - 파일명 패턴: `{specNumber}-{버전코드}.docx` 
    > - 버전 코드 → 시맨틱 버전 변환: 알파벳(a=10, b=11, ..., i=18, j=19) + 2자리 숫자 → `{major}.{minor}.0` (예: i00 → 18.0.0, j20 → 19.2.0)
    > - 분할 파일 대표 파일: 첫 번째 본문 파일에서 버전 추출
    > - specVersion은 Phase-1에서 정의된 기존 속성(xsd:string, 0..1)이며, Phase-3에서 값을 채운다
    
    ---
    
    ## 7. CQ 요약
    
    | CQ 그룹 | 커버리지 |
    | --- | --- |
    | CQ1. TS 구조 탐색 | 100% |
    | CQ2. TS 간 참조 분석 | 100% |
    | CQ3. CR → TS 연결 | 100% (3-4만 [P3-V05] 참조) |
    | CQ4. Resolution → TS 연결 | [P3-V06] 참조 |
    | CQ5. 통합 분석 | 100% |
    
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
    
    ### 1.1 기본 전제
    
    > Phase-3는 Phase-1~2 온톨로지의 확장이다.
    >
    > - Phase-1~2의 모든 클래스, 관계, 인스턴스는 그대로 유지
    > - Phase-3는 TS 구조를 추가하고 기존 데이터와 연결
    > - 기존 CQ는 모두 답변 가능 유지
    
    ### 1.2 Phase-1 온톨로지
    
    | 항목 | 내용 |
    | --- | --- |
    | 도메인 | 3GPP RAN5 Tdoc 메타데이터 |
    | 데이터 소스 | Tdoc_list (Excel) |
    
    ### 1.3 Phase-2 온톨로지
    
    | 항목 | 내용 |
    | --- | --- |
    | 도메인 | 3GPP RAN5 Final Report Resolution |
    | 데이터 소스 | Final Report (Word) |
    
    ### 1.4 외부 표준 온톨로지
    
    | 온톨로지 | 용도 |
    | --- | --- |
    | Dublin Core | 문서 메타데이터 (title, identifier, date) |
    | FOAF | 조직/사람 (Organization, Person) |
    
    ---
    
    ## 2. Phase-3 CQ 기반 사용 분석
    
    ### 2.1 CQ별 사용 클래스
    
    | CQ | 사용 클래스 | 출처 |
    | --- | --- | --- |
    | **CQ1** (구조 탐색) | Spec | Phase-1 |
    |  | Section, TSTable, TSFigure | Phase-3 신규 |
    | **CQ2** (참조 분석) | Section | Phase-3 신규 |
    | **CQ3** (CR 연결) | CR, Spec, Company, WorkItem, Meeting | Phase-1 |
    |  | Section | Phase-3 신규 |
    | **CQ4** (Resolution 연결) | Conclusion | Phase-2 |
    |  | CR, Spec, Meeting | Phase-1 |
    |  | Section | Phase-3 신규 |
    | **CQ5** (통합 분석) | 위 전체 조합 | Phase-1~3 |
    
    ### 2.2 Phase-1 클래스 - 전체 유지
    
    | 클래스 | Phase-3 CQ 사용 | 비고 |
    | --- | --- | --- |
    | **Spec** | ✅ CQ1, CQ3, CQ4, CQ5 | Phase-3 Section과 연결 |
    | **CR** | ✅ CQ3, CQ4, CQ5 | |
    | **Meeting** | ✅ CQ3, CQ4, CQ5 | |
    | **Company** | ✅ CQ3, CQ5 | |
    | **WorkItem** | ✅ CQ3, CQ5 | |
    | **Release** | ✅ CQ5 | |
    | Tdoc | ⚪ (CR 상위 클래스) | 간접 사용 |
    | LS | ⚪ | 기존 유지 |
    | Contact | ⚪ | 기존 유지 |
    | WorkingGroup | ⚪ | 기존 유지 |
    | AgendaItem | ⚪ | 기존 유지 |
    
    ### 2.3 Phase-2 클래스 - 전체 유지
    
    | 클래스 | Phase-3 CQ 사용 | 비고 |
    | --- | --- | --- |
    | **Conclusion** | ✅ CQ4 | RAN5 유일 Resolution 하위 클래스 |
    | Table | ⚪ | 기존 유지 (Phase-3와 별개) |
    
    *참고: RAN5 Phase-2에는 Agreement/WorkingAssumption/Summary/SessionNotes/Figure/Chart 없음*
    
    ---
    
    ## 3. Phase-3 CQ 기반 관계 사용 분석
    
    ### 3.1 Phase-1 관계 - 전체 유지
    
    | 관계 | Domain → Range | Phase-3 CQ 사용 | 비고 |
    | --- | --- | --- | --- |
    | **modifies** | CR → Spec | ✅ CQ3, CQ4 | 핵심 경로 |
    | **submittedBy** | Tdoc → Company | ✅ CQ3, CQ5 | |
    | **relatedTo** | Tdoc → WorkItem | ✅ CQ3, CQ5 | |
    | **presentedAt** | Tdoc → Meeting | ✅ CQ3, CQ4 | |
    | **targetRelease** | Tdoc → Release | ✅ CQ5 | |
    | belongsTo | Tdoc → AgendaItem | ⚪ | 기존 유지 |
    | hasContact | Tdoc → Contact | ⚪ | 기존 유지 |
    | isRevisionOf | Tdoc → Tdoc | ⚪ | 기존 유지 |
    | revisedTo | Tdoc → Tdoc | ⚪ | 기존 유지 |
    | replyTo | Tdoc → Tdoc | ⚪ | 기존 유지 |
    | replyIn | Tdoc → Tdoc | ⚪ | 기존 유지 |
    | sentTo | LS → WorkingGroup | ⚪ | 기존 유지 |
    | ccTo | LS → WorkingGroup | ⚪ | 기존 유지 |
    | originalLS | LS → Tdoc | ⚪ | 기존 유지 |
    | originatedFrom | LS → WorkingGroup | ⚪ | 기존 유지 |
    
    ### 3.2 Phase-2 관계 - 전체 유지
    
    | 관계 | Domain → Range | Phase-3 CQ 사용 | 비고 |
    | --- | --- | --- | --- |
    | **references** | Conclusion → Tdoc | ✅ CQ4 | 핵심 경로 |
    | **madeAt** | Conclusion → Meeting | ✅ CQ4 | |
    | resolutionBelongsTo | Conclusion → AgendaItem | ⚪ | 기존 유지 |
    | containedIn | Table → Meeting | ⚪ | 기존 유지 |
    
    *참고: RAN5 Phase-2에는 moderatedBy, hasTable 없음*
    
    ---
    
    ## 4. 클래스명 충돌 해결
    
    | Phase-2 클래스 | Phase-3 클래스 | 용도 |
    | --- | --- | --- |
    | Table | **TSTable** | TS 문서 내 Table |
    | (없음) | **TSFigure** | TS 문서 내 Figure |
    
    **Phase-3에서는 `TSFigure`, `TSTable` 클래스명 사용하여 명시적 구분.**
    
    ---
    
    ## 5. 핵심 연결 경로
    
    ```
    [CQ3 경로: CR → TS → Section]
    CR -[modifies]-> Spec -[hasSection]-> Section
          ↑            ↑                     ↑
       Phase-1        Phase-1               Phase-3 신규
    
    [CQ4 경로: Conclusion → CR → TS → Section]
    Conclusion -[references]-> CR -[modifies]-> Spec -[hasSection]-> Section
         ↑              ↑           ↑             ↑                     ↑
      Phase-2          Phase-2       Phase-1         Phase-1            Phase-3 신규
    
    ```
    
    ---
    
    ## 6. Spec ↔ TS 연결
    
    | 옵션 | 설명 | 결정 |
    | --- | --- | --- |
    | A. TS 클래스 신규 | Spec과 별도 | ❌ |
    | B. Spec 클래스 재사용 | Section을 Spec에 연결 | ✅ |
    
    **Spec 클래스 재사용. Section은 Spec의 하위 구조로 연결.**
    
    ---
    
    ## 7. 요약
    
    ### 7.1 클래스 현황
    
    | 구분 | 클래스 |
    | --- | --- |
    | **Phase-1 (전체 유지)** | Tdoc, CR, LS, Meeting, Company, Contact, WorkItem, AgendaItem, Release, Spec, WorkingGroup |
    | **Phase-2 (전체 유지)** | Resolution, Conclusion, Table |
    | **Phase-3 CQ 직접 사용** | Spec, CR, Meeting, Company, WorkItem, Release, Conclusion |
    | **Phase-3 신규 (예상)** | Section, TSTable, TSFigure |
    
    ### 7.2 범례
    
    | 기호 | 의미 |
    | --- | --- |
    | ✅ | Phase-3 CQ에서 직접 사용 |
    | ⚪ | Phase-3 CQ 미사용 (기존 유지) |
    
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
    
    ## 1. 데이터 소스
    
    | 항목 | 내용 |
    | --- | --- |
    | 문서 | RAN5 TS (38.508-1~38.561) |
    | 형식 | Word 문서 (단일 또는 분할) |
    | 범위 | 본문 + Annex |
    
    ### 1.1 TS 문서 목록
    
    | # | TS | DOCX | 규모 | 비고 |
    | --- | --- | --- | --- | --- |
    | 1 | 38.508-1 | 6파트 (38508-1-j20_*) | 대형 | UE conformance test. cover+5파트 |
    | 2 | 38.508-2 | 38508-2-j31.docx | 중형 | UE test functions |
    | 3 | 38.509 | 38509-i00.docx | 중형 | UE special test functions |
    | 4 | 38.521-1 | 8파트 (38521-1-j30_*) | 대형 | UE conformance RF FR1. cover+7파트 |
    | 5 | 38.521-2 | 5파트 (38521-2-j20_*) | 대형 | UE conformance RF FR2. cover+4파트 |
    | 6 | 38.521-3 | 38521-3-j40.docx | 대형 | UE conformance interworking |
    | 7 | 38.521-4 | 4파트 (38521-4-i90_*) | 대형 | UE conformance performance. cover+3파트 |
    | 8 | 38.521-5 | 38521-5-j10.docx | 중형 | UE conformance DSS |
    | 9 | 38.522 | 38522-j11.docx | 소형 | Test case applicability |
    | 10 | 38.523-1 | 12파트 (38523-1-j30_*) | **초대형** | UE conformance Signalling. cover+11파트 |
    | 11 | 38.523-2 | 38523-2-j40.docx | 소형 | UE PICS |
    | 12 | 38.523-3 | 38523-3-i60.docx | 대형 | UE IXIT |
    | 13 | 38.533 | 11파트 (38533-j00_*) | **초대형** | UE conformance RRM. cover+10파트 |
    | 14 | 38.551 | 38551-i40.docx | 중형 | gNB conformance |
    | 15 | 38.561 | 38561-i30.docx | 중형 | NR Sidelink conformance |
    
    ---
    
    ## 2. 용어 나열
    
    ### 2.1 TS 구조 관련
    
    | 용어 | 설명 | 데이터 소스 | 관련 CQ |
    | --- | --- | --- | --- |
    | **TS (=Spec)** | Technical Specification 문서 | 문서 자체 | CQ1, CQ3, CQ4, CQ5 |
    | **Section** | TS 내부 계층 구조 (본문 + Annex) | 헤딩 파싱 | CQ1, CQ2, CQ3, CQ4 |
    | **TSTable** | TS 내 표 | 캡션 파싱 | CQ1 |
    | **TSFigure** | TS 내 그림 | 캡션 파싱 | CQ1 |
    
    ### 2.2 Section 속성 관련
    
    | 용어 | 설명 | 데이터 소스 | 관련 CQ |
    | --- | --- | --- | --- |
    | **sectionId** | Section 고유 식별자 | 생성 (TS번호-섹션번호) | 전체 |
    | **sectionNumber** | Section 번호 | 헤딩 파싱 (예: 6.2.1, A.1) | CQ1 |
    | **sectionTitle** | Section 제목 | 헤딩 파싱 | CQ1-9 |
    | **level** | Section 계층 레벨 | 헤딩 스타일에서 추출 | CQ1-4 |
    | **isVoid** | Void 여부 | 본문에 "Void" 텍스트 | CQ1 |
    
    ### 2.3 TSTable/TSFigure 속성 관련
    
    | 용어 | 설명 | 관련 CQ |
    | --- | --- | --- |
    | **tableId** | Table 고유 식별자 | CQ1 |
    | **tableNumber** | Table 번호 (예: 6.2.1-1) | CQ1-10 |
    | **tableCaption** | Table 캡션 | CQ1 |
    | **figureId** | Figure 고유 식별자 | CQ1 |
    | **figureNumber** | Figure 번호 (예: 6-1) | CQ1 |
    | **figureCaption** | Figure 캡션 | CQ1 |
    
    ### 2.4 관계 관련 (Phase-3 신규)
    
    | 용어 | 설명 | 관련 CQ |
    | --- | --- | --- |
    | **hasSection** | Spec → Section (최상위) | CQ1 |
    | **hasSubSection** | Section → Section (부모-자식) | CQ1-2, CQ1-3 |
    | **containsTable** | Section → TSTable | CQ1-5, CQ1-7 |
    | **containsFigure** | Section → TSFigure | CQ1-6 |
    | **referencesSection** | Section → Section (TS 간 참조) | CQ2 |
    
    ### 2.5 기존 연결 관련 (Phase-1~2 재사용)
    
    | 용어 | 출처 | 관련 CQ |
    | --- | --- | --- |
    | **modifies** | Phase-1 | CQ3 |
    | **references** | Phase-2 | CQ4 |
    | **clausesAffected** | Phase-1 CR 속성 | CQ3-4 |
    
    ---
    
    ## 3. 요약
    
    | 카테고리 | 용어 |
    | --- | --- |
    | **클래스 후보 (Phase-3 신규)** | Section, TSTable, TSFigure |
    | **클래스 (Phase-1 재사용)** | Spec (=TS) |
    | **Section 속성** | sectionId, sectionNumber, sectionTitle, level, isVoid |
    | **TSTable 속성** | tableId, tableNumber, tableCaption |
    | **TSFigure 속성** | figureId, figureNumber, figureCaption |
    | **관계 후보 (Phase-3 신규)** | hasSection, hasSubSection, containsTable, containsFigure, referencesSection |
    | **관계 (Phase-1~2 재사용)** | modifies, references |
    | **속성 (Phase-1 재사용)** | clausesAffected |
    
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
    
    ## 1. Phase-3 신규 클래스
    
    | 클래스 | 정의 |
    | --- | --- |
    | **Section** | TS 내부 계층 구조 (본문 + Annex) |
    | **TSTable** | TS 내 표 (적합성 시험 요구사항 표) |
    | **TSFigure** | TS 내 그림 (시험 구성도, 시그널링 다이어그램) |
    
    ### 1.1 계층 구조 검토
    
    **Section, TSTable, TSFigure 간 상속 관계 없음. 독립 클래스.**
    
    ### 1.2 Section 하위 클래스 검토
    
    | 후보 | 하위 클래스? | 이유 |
    | --- | --- | --- |
    | Annex | ❌ 불필요 | Section과 동일 구조. sectionNumber 패턴으로 구분 |
    | Void Section | ❌ 불필요 | Section과 동일 구조. isVoid 속성으로 구분 |
    
    ---
    
    ## 2. 전체 클래스 계층 다이어그램
    
    ```
    ┌─────────────────────────────────────────────────────────────────┐
    │                    RAN5 TS Ontology (Phase-3)                   │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                 │
    │  [Phase-1 기존 - 전체 유지]                                     │
    │                                                                 │
    │  Tdoc                                                           │
    │  ├── CR ──[modifies]──→ Spec ◄───────────────┐                  │
    │  └── LS                    │                  │                 │
    │                            │                  │                 │
    │  Meeting    Company    WorkItem    Release    │                 │
    │  Contact    AgendaItem WorkingGroup           │                 │
    │                                               │                 │
    ├───────────────────────────────────────────────┼─────────────────┤
    │  [Phase-2 기존 - 전체 유지]                   │                 │
    │                                               │                 │
    │  Conclusion ──[references]──→ Tdoc            │                 │
    │                                               │                 │
    │  Table                                        │                 │
    │                                               │                 │
    ├───────────────────────────────────────────────┼─────────────────┤
    │  [Phase-3 신규]                               │                 │
    │                                               │                 │
    │                            ┌──[hasSection]────┘                 │
    │                            ▼                                    │
    │                        Section ⭐ ←──────────────┐             │
    │                            │                     │              │
    │                   [hasSubSection]        [referencesSection]    │
    │                            │                     │              │
    │                            ▼                     │              │
    │                        Section ──────────────────┘              │
    │                        ╱      ╲                                 │
    │          [containsTable]      [containsFigure]                  │
    │                 ╱                    ╲                          │
    │                ▼                      ▼                         │
    │           TSTable ⭐              TSFigure ⭐                  │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘
    ```
    
    ⭐ = Phase-3 신규 클래스
    
    ---
    
    ## 3. Phase-1~2 클래스와의 연결
    
    | Phase-3 클래스 | 연결 대상 | 관계 | 방향 |
    | --- | --- | --- | --- |
    | Section | Spec (Phase-1) | hasSection | Spec → Section |
    | Section | Section | hasSubSection | Section → Section (부모→자식) |
    | Section | Section | referencesSection | Section → Section (참조) |
    | TSTable | Section | containsTable | Section → TSTable |
    | TSFigure | Section | containsFigure | Section → TSFigure |
    
    ---
    
    ## 4. 누적 클래스 현황
    
    | Phase | 클래스 |
    | --- | --- |
    | Phase-1 | Tdoc, CR, LS, Meeting, Company, Contact, WorkItem, AgendaItem, Release, Spec, WorkingGroup |
    | Phase-2 | Resolution, Conclusion, Table |
    | **Phase-3** | **Section, TSTable, TSFigure** |
    
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
    
    ## 1. Section 클래스 속성
    
    ### 1.1 Data Property
    
    | Property | Type | Description | 데이터 소스 |
    | --- | --- | --- | --- |
    | sectionId | String | Section 고유 식별자 | 생성 (예: 38.521-1-6.2) |
    | sectionNumber | String | Section 번호 | 헤딩 파싱 (예: 6.2.1, A.1) |
    | sectionTitle | String | Section 제목 | 헤딩 파싱 |
    | level | Integer | Section 계층 레벨 (1~7, Annex 대제목=1) | 헤딩 스타일에서 추출 (아래 매핑 참조). Heading 8 → level 1 (Annex 대제목) |
    | isVoid | Boolean | Void 여부 | 본문에 "Void" 텍스트 |
    
    **헤딩 스타일 → level 매핑:**
    
    | 스타일 | level | 비고 |
    | --- | --- | --- |
    | Heading 1 | 1 | 표준 |
    | Heading 2 | 2 | 표준 |
    | Heading 3 | 3 | 표준 |
    | Heading 4 | 4 | 표준 |
    | Heading 5 | 5 | 표준 |
    | Heading 6 | 6 | 표준 |
    | Heading 7 | 7 | 표준 |
    | Heading 8 | 1 | Annex 대제목 |
    | Heading 3 Specs | 3 | 비표준 (38.523-3 등) |
    | Heading 2.Head2A.2 | 2 | 비표준 |
    
    **제외 스타일 (Section이 아닌 것):**
    
    | 스타일 | 용도 | 처리 |
    | --- | --- | --- |
    | toc 1~8 | Table of Contents | 제외 (Heading과 중복되는 TOC 영역) |
    | Normal | 일반 본문 | 제외 |
    
    *RAN5는 Heading 9 없음. 비표준 2종 (Heading 3 Specs, Heading 2.Head2A.2).*
    
    ### 1.2 Object Property
    
    | Property | Range | Inverse | Description |
    | --- | --- | --- | --- |
    | belongsToSpec | Spec | hasSection | Section이 속한 TS |
    | hasSubSection | Section | parentSection | 하위 Section (부모→자식) |
    | parentSection | Section | hasSubSection | 상위 Section (자식→부모) |
    | referencesSection | Section | referencedBySection | 참조하는 다른 Section |
    | referencedBySection | Section | referencesSection | 이 Section을 참조하는 Section |
    | referencesSpec | Spec | - | TS-only 참조 (clause 없이 TS 번호만 언급). **도입 근거**: 아래 §1.X "referencesSpec 설계 결정" 참조 |
    | containsTable | TSTable | tableInSection | Section에 포함된 Table |
    | containsFigure | TSFigure | figureInSection | Section에 포함된 Figure |
    
    ---
    
    ## 2. TSTable 클래스 속성
    
    ### 2.1 Data Property
    
    | Property | Type | Description | 데이터 소스 |
    | --- | --- | --- | --- |
    | tableId | String | Table 고유 식별자 | 생성 (예: 38.521-1-T6.2.1-1) |
    | tableNumber | String | Table 번호 | 캡션 파싱 (예: 6.2.1-1) |
    | tableCaption | String | Table 캡션 | 캡션 파싱 |
    
    ### 2.2 Object Property
    
    | Property | Range | Inverse | Description |
    | --- | --- | --- | --- |
    | tableInSection | Section | containsTable | Table이 속한 Section |
    
    ---
    
    ## 3. TSFigure 클래스 속성
    
    ### 3.1 Data Property
    
    | Property | Type | Description | 데이터 소스 |
    | --- | --- | --- | --- |
    | figureId | String | Figure 고유 식별자 | 생성 (예: 38.509-F5-1) |
    | figureNumber | String | Figure 번호 | 캡션 파싱 (예: 5-1) |
    | figureCaption | String | Figure 캡션 | 캡션 파싱 |
    
    ### 3.2 Object Property
    
    | Property | Range | Inverse | Description |
    | --- | --- | --- | --- |
    | figureInSection | Section | containsFigure | Figure가 속한 Section |
    
    ---
    
    ## 4. Spec 클래스 확장 (Phase-1 기존 + Phase-3 추가)
    
    | Property | Range | Inverse | Description |
    | --- | --- | --- | --- |
    | hasSection | Section | belongsToSpec | Spec이 포함하는 최상위 Section |
    
    *참고: specVersion은 Phase-1에서 정의된 기존 속성이며, Phase-3에서 TS DOCX 파일명의 버전 코드에서 추출하여 값을 설정한다.*
    
    ---
    
    ## 5. 전체 Object Property 목록 (Phase-3 신규)
    
    | # | Property | Domain | Range | Inverse | Description |
    | --- | --- | --- | --- | --- | --- |
    | 1 | hasSection | Spec | Section | belongsToSpec | Spec의 최상위 Section |
    | 2 | belongsToSpec | Section | Spec | hasSection | Section이 속한 Spec |
    | 3 | hasSubSection | Section | Section | parentSection | 하위 Section |
    | 4 | parentSection | Section | Section | hasSubSection | 상위 Section |
    | 5 | referencesSection | Section | Section | referencedBySection | 참조하는 Section |
    | 6 | referencedBySection | Section | Section | referencesSection | 참조받는 Section |
    | 7 | containsTable | Section | TSTable | tableInSection | 포함된 Table |
    | 8 | containsFigure | Section | TSFigure | figureInSection | 포함된 Figure |
    | 9 | tableInSection | TSTable | Section | containsTable | Table이 속한 Section |
    | 10 | figureInSection | TSFigure | Section | containsFigure | Figure가 속한 Section |
    | 11 | referencesSpec | Section | Spec | - | TS-only 참조 |
    
    ---
    
    ## 6. 전체 Data Property 목록 (Phase-3 신규)
    
    | # | Property | Domain | Type | Description |
    | --- | --- | --- | --- | --- |
    | 1 | sectionId | Section | String | Section 고유 식별자 |
    | 2 | sectionNumber | Section | String | Section 번호 |
    | 3 | sectionTitle | Section | String | Section 제목 |
    | 4 | level | Section | Integer | 계층 레벨 (1~7) |
    | 5 | isVoid | Section | Boolean | Void 여부 |
    | 6 | tableId | TSTable | String | Table 고유 식별자 |
    | 7 | tableNumber | TSTable | String | Table 번호 |
    | 8 | tableCaption | TSTable | String | Table 캡션 |
    | 9 | figureId | TSFigure | String | Figure 고유 식별자 |
    | 10 | figureNumber | TSFigure | String | Figure 번호 |
    | 11 | figureCaption | TSFigure | String | Figure 캡션 |
    
    ---
    
    ## 7. Inverse Property 정리
    
    | 정방향 | 역방향 | 설명 |
    | --- | --- | --- |
    | hasSection | belongsToSpec | Spec ↔ 최상위 Section |
    | hasSubSection | parentSection | 부모 Section ↔ 자식 Section |
    | containsTable | tableInSection | Section ↔ TSTable |
    | containsFigure | figureInSection | Section ↔ TSFigure |
    | referencesSection | referencedBySection | 참조 ↔ 피참조 Section |
    
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
    
    ## 1. Section Data Property Facet
    
    | Property | Type | Cardinality | Required | 제약 | Description |
    | --- | --- | --- | --- | --- | --- |
    | sectionId | String | 1 | ✅ | PK | 패턴: `{specNumber}-{sectionNumber}` |
    | sectionNumber | String | 1 | ✅ | 패턴 | 본문: `^[0-9]+(\\.[0-9]+[a-zA-Z]?)*$`, Annex: `^[A-Z](\\.[0-9]+)*$` |
    | sectionTitle | String | 1 | ✅ | - | Section 제목 |
    | level | Integer | 1 | ✅ | 범위 | min=1, max=7 (Heading 8 → level 1, Heading 7 → level 7) |
    | isVoid | Boolean | 1 | ✅ | default | default: false |
    
    ---
    
    ## 2. Section Object Property Facet
    
    | Property | Domain | Range | Cardinality | Functional | Inverse | 특성 |
    | --- | --- | --- | --- | --- | --- | --- |
    | belongsToSpec | Section | Spec | 1 | ✅ | hasSection | - |
    | hasSubSection | Section | Section | 0..* | ❌ | parentSection | Irreflexive, Asymmetric |
    | parentSection | Section | Section | 0..1 | ✅ | hasSubSection | Irreflexive, Asymmetric |
    | referencesSection | Section | Section | 0..* | ❌ | referencedBySection | Irreflexive |
    | referencedBySection | Section | Section | 0..* | ❌ | referencesSection | Irreflexive |
    | containsTable | Section | TSTable | 0..* | ❌ | tableInSection | - |
    | containsFigure | Section | TSFigure | 0..* | ❌ | figureInSection | - |
    | referencesSpec | Section | Spec | 0..* | ❌ | - | TS-only 참조 |
    
    ---
    
    ## 3. TSTable Facet
    
    **Data Property:**
    
    | Property | Type | Cardinality | Required | 제약 |
    | --- | --- | --- | --- | --- |
    | tableId | String | 1 | ✅ | PK. 패턴: `{specNumber}-T{tableNumber}` |
    | tableNumber | String | 1 | ✅ | `^[0-9A-Z]+(\.[0-9]+)*-[0-9]+$` |
    | tableCaption | String | 0..1 | ❌ | 캡션 없는 Table 존재 가능 |
    
    **Object Property:**
    
    | Property | Domain | Range | Cardinality | Functional | Inverse |
    | --- | --- | --- | --- | --- | --- |
    | tableInSection | TSTable | Section | 1 | ✅ | containsTable |
    
    ---
    
    ## 4. TSFigure Facet
    
    **Data Property:**
    
    | Property | Type | Cardinality | Required | 제약 |
    | --- | --- | --- | --- | --- |
    | figureId | String | 1 | ✅ | PK. 패턴: `{specNumber}-F{figureNumber}` |
    | figureNumber | String | 1 | ✅ | `^[0-9A-Z]+(\.[0-9]+)*-[0-9]+$` |
    | figureCaption | String | 0..1 | ❌ | 캡션 없는 Figure 존재 가능 |
    
    **Object Property:**
    
    | Property | Domain | Range | Cardinality | Functional | Inverse |
    | --- | --- | --- | --- | --- | --- |
    | figureInSection | TSFigure | Section | 1 | ✅ | containsFigure |
    
    ---
    
    ## 5. Spec 추가 Object Property Facet
    
    | Property | Domain | Range | Cardinality | Functional | Inverse |
    | --- | --- | --- | --- | --- | --- |
    | hasSection | Spec | Section | 0..* | ❌ | belongsToSpec |
    
    > **Cardinality 설계 결정 (감사 이슈 E-7 대응)**: hasSection은 `0..*`로 완화. 근거:
    > - Phase-3 Step-6 파싱은 DOCX 본문을 가진 TS만 대상이므로 hasSection ≥ 1 보장되지만,
    > - Phase-4 §7.3에서 CR 본문 "Other Specs Affected"로부터 **동적 생성된 Spec** (실측 Phase-4 P4-V04=22건)은 Phase-3 파싱 범위 밖이라 Section 노드 없이 Spec 노드만 존재.
    > - 이전 `1..*` 제약에서는 동적 생성 Spec이 제약 위반이므로, 데이터 모델 정합성을 위해 `0..*`로 변경.
    > - 실제 Phase-3 파싱 결과 Spec은 여전히 P3-V11=527 hasSection edges(Spec → level-1 Section)를 유지. `hasSection` 없는 Spec은 Phase-4에서 동적 생성된 것으로 한정됨을 운영 가이드에 명시.
    
    ---
    
    ## 6. 특수 제약조건 요약
    
    ### 6.1 Object Property 특성
    
    | Property | Irreflexive | Asymmetric | Transitive |
    | --- | --- | --- | --- |
    | hasSubSection | ✅ | ✅ | ❌ |
    | parentSection | ✅ | ✅ | ❌ |
    | referencesSection | ✅ | ❌ | ❌ |
    | referencedBySection | ✅ | ❌ | ❌ |
    
    ### 6.2 계층 구조 제약
    
    | 제약 | 설명 |
    | --- | --- |
    | 최상위 Section | parentSection = null, level = 1 |
    | 말단 Section | hasSubSection = empty |
    | level 일관성 | 부모 level < 자식 level |
    
    ### 6.3 데이터 패턴
    
    **ID 패턴:**
    
    | 클래스 | 패턴 | 예시 |
    | --- | --- | --- |
    | Section | `{specNumber}-{sectionNumber}` | 38.521-1-6.2 |
    | TSTable | `{specNumber}-T{tableNumber}` | 38.521-1-T6.2.1-1 |
    | TSFigure | `{specNumber}-F{figureNumber}` | 38.509-F5-1 |
    
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
    
    ## 1. 데이터 소스
    
    ### 1.1 TS 문서 목록
    
    | # | TS 번호 | DOCX 파일 | 버전 코드 | 비고 |
    | --- | --- | --- | --- | --- |
    | 1 | 38.508-1 | 6파트 (38508-1-j20_*) | j20 | 분할. cover 제외 |
    | 2 | 38.508-2 | 38508-2-j31.docx | j31 | |
    | 3 | 38.509 | 38509-i00.docx | i00 | |
    | 4 | 38.521-1 | 8파트 (38521-1-j30_*) | j30 | 분할. cover 제외 |
    | 5 | 38.521-2 | 5파트 (38521-2-j20_*) | j20 | 분할. cover 제외 |
    | 6 | 38.521-3 | 38521-3-j40.docx | j40 | |
    | 7 | 38.521-4 | 4파트 (38521-4-i90_*) | i90 | 분할. cover 제외 |
    | 8 | 38.521-5 | 38521-5-j10.docx | j10 | |
    | 9 | 38.522 | 38522-j11.docx | j11 | |
    | 10 | 38.523-1 | 12파트 (38523-1-j30_*) | j30 | 분할. cover 제외. 초대형 |
    | 11 | 38.523-2 | 38523-2-j40.docx | j40 | |
    | 12 | 38.523-3 | 38523-3-i60.docx | i60 | |
    | 13 | 38.533 | 11파트 (38533-j00_*) | j00 | 분할. cover 제외. 초대형 |
    | 14 | 38.551 | 38551-i40.docx | i40 | |
    | 15 | 38.561 | 38561-i30.docx | i30 | |
    
    **제외 파일:**
    
    | 파일 | 이유 |
    | --- | --- |
    | *_cover.docx | 표지만. Section 0건 |
    | 38.591-1~4 | DOCX 입력 없음, Tdoc 0건 |
    
    ### 1.2 분할 파일 병합 순서
    
    **38.508-1** (cover 제외, 5파트):
    
    ```
    s00-s040311 → s040312-s0405 → s0406-s0414 → s05-s07 → sAnnexes
    ```
    
    **38.521-1** (cover 제외, 7파트):
    
    ```
    s00-s05 → s06-s0602C → s0602D-s060304 → s0603A-s0604L → s0605 → s0700 → sAnnexes
    ```
    
    **38.521-2** (cover 제외, 4파트):
    
    ```
    s00-s05 → s06-s0604D → s0605-s07 → sAnnexes
    ```
    
    **38.521-4** (cover 제외, 3파트):
    
    ```
    s00-s05 → s06-s11 → sAnnexes
    ```
    
    **38.523-1** (cover 제외, 11파트):
    
    ```
    s00-s06 → s0701-s070112 → s070113 → s070114 → s070115-s07014
    → s08-s0814 → s0815-s08161 → s08162-s0827 → s09-s103 → s104-s11 → s12-s14
    ```
    
    **38.533** (cover 제외, 10파트):
    
    ```
    s00-s04 → s05 → s0601_s0603 → s0604_s0605 → s0606_s0607
    → s07 → s08-s11 → s12-s15 → s16-s19 → sAnnexes
    ```
    
    ---
    
    ## 2. ID 생성 규칙
    
    | 클래스 | ID 속성 | 패턴 | 예시 |
    | --- | --- | --- | --- |
    | Section | sectionId | `{specNumber}-{sectionNumber}` | 38.521-1-6.2 |
    | TSTable | tableId | `{specNumber}-T{tableNumber}` | 38.521-1-T6.2.1-1 |
    | TSFigure | figureId | `{specNumber}-F{figureNumber}` | 38.509-F5-1 |
    
    ---
    
    ## 3. 데이터 소스 매핑
    
    ### 3.1 Section 매핑
    
    | 속성 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | sectionId | 생성 | `{specNumber}-{sectionNumber}` |
    | sectionNumber | 헤딩 텍스트 | 숫자/문자 패턴 추출 |
    | sectionTitle | 헤딩 텍스트 | sectionNumber 이후 텍스트 |
    | level | 헤딩 스타일 | Step 5 §1.1 매핑 참조 |
    | isVoid | 본문 내용 | "Void" 텍스트만 있으면 true |
    
    ### 3.2 TSTable/TSFigure 매핑
    
    | 속성 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | tableId / figureId | 생성 | `{specNumber}-T/F{number}` |
    | tableNumber / figureNumber | 캡션 텍스트 | "Table/Figure X.X.X-N:" 패턴에서 추출 |
    | tableCaption / figureCaption | 캡션 텍스트 | "Table/Figure X.X.X-N:" 이후 텍스트 |
    
    ### 3.3 tableNumber/figureNumber → sectionNumber 매핑
    
    | 입력 | 출력 | 규칙 |
    | --- | --- | --- |
    | 6.2.1-1 | 6.2.1 | 마지막 `-N` 제거 |
    | A.1-1 | A.1 | 마지막 `-N` 제거 |
    | `-` 없음 | 전체를 sectionNumber로 사용 | |
    | 매칭 Section 없음 | 상위 Section 탐색 → 없으면 null | 오류 로그 |
    
    ### 3.4 참조 패턴 (referencesSection)
    
    | 패턴 | 정규식 | 예시 |
    | --- | --- | --- |
    | clause X.X.X | `clause\s+(\d+(?:\.\d+)*)` | "clause 6.2.1" |
    | subclause X.X.X | `subclause\s+(\d+(?:\.\d+)*)` | "subclause 7.4.1.1" |
    | Section X.X.X | `Section\s+(\d+(?:\.\d+)*)` | "Section 6.2.1" |
    | Annex X | `Annex\s+([A-Z](?:\.\d+)*)` | "Annex A.1" |
    | TS 38.XXX clause X.X | `TS\s+38\.(\d{3}(?:-\d)?)\s+clause\s+(\d+(?:\.\d+)*)` | "TS 38.521-1 clause 6.2" |
    | TS 38.XXX (TS-only) | `TS\s+38\.(\d{3}(?:-\d)?)` (clause 없음) | "TS 38.533" → referencesSpec |
    
    **참조 대상 결정:**
    
    | 참조 유형 | 대상 결정 |
    | --- | --- |
    | 같은 TS 내 | 현재 specNumber + 추출된 sectionNumber |
    | 다른 TS (clause 있음) | 추출된 specNumber + sectionNumber → referencesSection |
    | 다른 TS (clause 없음) | 추출된 specNumber → referencesSpec. 자기 TS 제외, Scope 내 TS만 |
    | 대상 Section 없음 | 관계 생성 안 함 (로그 기록) |
    | 자기 자신 참조 | 무시 (Irreflexive) |
    
    ### 3.X referencesSpec 설계 결정 (감사 이슈 J-2 대응)
    
    **도입 이유:**
    RAN5 TS 본문에서 "TS 38.533", "TS 38.521-1" 등 clause 없이 TS 번호만 언급되는 패턴이 다수 발견됨 ([P3-V09] 검증; Spec ↔ Section edges). 이를 어떻게 모델링할지에 대해 아래 3가지 대안을 비교한 결과 현 설계(`referencesSpec: Section → Spec`)를 선택.
    
    **대안 비교:**
    
    | # | 대안 | 장점 | 단점 | 선택 여부 |
    | --- | --- | --- | --- | --- |
    | A | **`referencesSpec: Section → Spec` (현 채택)** | (1) Range가 Spec 단일 클래스로 명확 (2) clause 유무로 `referencesSection` / `referencesSpec`이 깔끔히 분리 (3) 동적 생성 Spec(Phase-4 §7)과도 자연스럽게 연동 | Object Property 1개 추가 부담 | ✅ |
    | B | `referencesSection`만 사용, sectionNumber nullable | 관계 수 단일화 | (1) Range가 Section이므로 clause 없는 경우에도 가짜 Section 노드(sectionNumber=null) 생성 필요 (2) Section 제약(sectionNumber 필수)과 충돌 (3) Neo4j 상 null 속성 필터링 오버헤드 | ❌ |
    | C | Spec 노드에 역방향 `referencedBySection`만 두고 정방향 property 생략 | 관계 수 최소 | (1) Section 중심 조회(CQ `이 Section이 참조하는 모든 Spec`)가 불가능 — Cypher에서 반대 방향 순회 필요 (2) 역관계만 있는 구조는 OWL 설계 안티패턴 | ❌ |
    
    **결론**: 대안 A가 Section 중심/Spec 중심 양방향 조회 모두를 지원하면서 Section 제약(sectionNumber 필수)을 유지. 해당 규모에서 OP 1개 추가 부담은 무시 가능.
    
    ---
    
    ## 4. 계층 구조 생성 규칙
    
    ### 4.1 Section 계층 생성
    
    ```
    [파싱 순서]
    1. TS 문서에서 Heading 1~8 + 비표준 2종 추출 (toc N 스타일 제외)
    2. 분할 파일은 병합 순서대로 연결 (Section 번호 연속 보장)
    3. 각 헤딩에서 sectionNumber, sectionTitle, level 추출
    4. level 기반 스택 알고리즘으로 부모-자식 관계 설정
    ```
    
    ### 4.2 역관계 자동 생성
    
    | 정방향 생성 시 | 역방향 자동 생성 |
    | --- | --- |
    | A -[hasSubSection]-> B | B -[parentSection]-> A |
    | A -[containsTable]-> B | B -[tableInSection]-> A |
    | A -[containsFigure]-> B | B -[figureInSection]-> A |
    | A -[referencesSection]-> B | B -[referencedBySection]-> A |
    | A -[hasSection]-> B | B -[belongsToSpec]-> A |
    | A -[referencesSpec]-> B | (역관계 없음) |
    
    ---
    
    ## 5. Spec 확장 (Phase-1 연결)
    
    ### 5.1 Spec → Section 연결
    
    Phase-1에서 생성된 Spec 인스턴스에 hasSection 관계 추가:
    
    ```json
    {
      "@type": "Spec",
      "specNumber": "38.521-1",
      "specVersion": "19.3.0",
      "hasSection": [
        { "@id": "section:38.521-1-1" },
        { "@id": "section:38.521-1-2" },
        { "@id": "section:38.521-1-A" }
      ]
    }
    ```
    
    > specVersion은 Phase-3가 Spec 노드에 새로 설정하는 유일한 Data Property이다.
    
    ### 5.2 CR → Section 연결 (clausesAffected 활용)
    
    | clausesAffected | 파싱 결과 | 연결 Section |
    | --- | --- | --- |
    | "6.2.1" | [6.2.1] | 38.XXX-6.2.1 |
    | "6.2.1, 7.4" | [6.2.1, 7.4] | 38.XXX-6.2.1, 38.XXX-7.4 |
    
    ---
    
    ## 6. 예시 인스턴스
    
    ### 6.1 Section 예시 (38.521-1 — 최상위)
    
    ```json
    {
      "@type": "Section",
      "sectionId": "38.521-1-6",
      "sectionNumber": "6",
      "sectionTitle": "Minimum conformance requirements",
      "level": 1,
      "isVoid": false,
      "belongsToSpec": { "@id": "spec:38.521-1" },
      "parentSection": null,
      "hasSubSection": [
        { "@id": "section:38.521-1-6.1" },
        { "@id": "section:38.521-1-6.2" }
      ]
    }
    ```
    
    ### 6.2 TSTable 예시 (38.521-1)
    
    ```json
    {
      "@type": "TSTable",
      "tableId": "38.521-1-T6.2.1-1",
      "tableNumber": "6.2.1-1",
      "tableCaption": "Test Parameters for UE Maximum Output Power for CA",
      "tableInSection": { "@id": "section:38.521-1-6.2.1" }
    }
    ```
    
    ### 6.3 TSFigure 예시 (38.509)
    
    ```json
    {
      "@type": "TSFigure",
      "figureId": "38.509-F5.3.4.1-1",
      "figureNumber": "5.3.4.1-1",
      "figureCaption": "UE test loop mode A",
      "figureInSection": { "@id": "section:38.509-5.3.4.1" }
    }
    ```
    
    ---
    
    ## 7. 생성 순서
    
    | 순서 | 클래스 | 의존 대상 |
    | --- | --- | --- |
    | 1 | Spec | 없음 (Phase-1 기존) |
    | 2 | Section (level 1) | Spec |
    | 3 | Section (level 2~7) | Section (상위) |
    | 4 | TSTable | Section |
    | 5 | TSFigure | Section |
    | 6 | referencesSection | Section (전체) |
    | 7 | referencesSpec | Section (전체), Spec (Phase-1) |
    
    ---
    
    ## 8. 검증 규칙
    
    | 검증 항목 | 규칙 |
    | --- | --- |
    | Section ID 중복 | sectionId 유일 |
    | 부모 없음 | level > 1이면 parentSection 필수 |
    | Spec 없음 | belongsToSpec 대상 존재 |
    | Table/Figure Section 없음 | tableInSection/figureInSection 대상 존재 |
    | 자기 참조 | referencesSection 대상 ≠ 자신 |
    | Section 총 수 | Appendix A [P3-V01] 참조 |
    | TSTable 총 수 | Appendix A [P3-V02] 참조 |
    | TSFigure 총 수 | Appendix A [P3-V03] 참조 |
    | Orphan Section (belongsToSpec 누락) | [P3-V04] (BELONGS_TO_SPEC 전수 일치) |
    | Void Section 수 | [P3-V07] |
    | referencesSection 관계 수 | [P3-V08] |
    | referencesSpec 관계 수 | [P3-V09] |
    | Section 계층 edges (hasSubSection=parentSection) | [P3-V10] |
    | hasSection edges (Spec → level-1 Section) | [P3-V11] |
    | BELONGS_TO_SPEC edges | [P3-V12] (= [P3-V01] Section 전수) |
    | CONTAINS_TABLE edges | [P3-V13] (매핑 성공분, unmapped는 로그) |
    | CONTAINS_FIGURE edges | [P3-V14] (매핑 성공분, unmapped는 로그) |
    | 파서 warnings | [P3-V15] (중복/경미 수준만 허용) |
    | CR → Section 커버리지 (clausesAffected 기반) | [P3-V05] |
    | Resolution → CR 커버리지 (Conclusion REFERENCES CR) | [P3-V06] |
    
    ### 8.1 Release Integrity 검증 (release-aware)
    
    release-키 무결성. RAN5는 중간 JSON-LD가 없으므로 `scripts/RAN/formal/RAN5/phase-3/ts-parser/validate_release_integrity.py`가 **파서 JSON**(`ts_{spec}_{release}.json`)에 대해 R1~R6을 전수 검사하며, 1건이라도 위반 시 FAIL(다음 단계 차단). void shell release(forward-redirect, §9.4)는 Section 수가 적어도 정상 적재이므로 R1~R6을 통과해야 한다(섹션 부족을 위반으로 오판 금지). 전수 PASS 실측은 Appendix A.1.3 참조.
    
    | 규칙 | 검증 항목 | 기대값 |
    | --- | --- | --- |
    | R1 | sectionId가 release 토큰(`-Rel-NN-`)을 포함 (형식 준수; 하이픈 spec `38.521-1-Rel-15-...` 포함) | 전수 PASS |
    | R2 | belongsToSpec의 release == sectionId의 release (cross-release 오염 0) | 0 위반 |
    | R3 | belongsToSpec의 specNumber == sectionId의 specNumber | 0 위반 |
    | R4 | cross-release 참조 누출 0 (referencesSection target release == source release) | 0 edge |
    | R5 | Spec 노드 specInRelease(`tdoc:release/Rel_NN`)·specRelease(`Rel-NN`) 정합 | 전수 일치 |
    | R6 (RAN5 referencesSpec 보유) | referencesSpec target은 **동일 release** Spec 노드로만 해소 + target Spec 노드 존재 | 0 위반 |
    
    ---
    
    ## 9. RAN5 고유 파싱 규칙
    
    ### 9.1 분할 파일 병합
    
    | 규칙 | 설명 |
    | --- | --- |
    | 파일 정렬 | 파일명의 섹션 범위 접미사 기준 (s00→s06→s07→sAnnexes) |
    | cover 파일 | 무조건 스킵 (_cover 접미사) |
    | Section 연속성 | 파트 간 Section 번호가 연속되어야 함 |
    | 계층 유지 | 스택을 파트 간 유지하여 부모-자식 관계 연속 보장 |
    
    ### 9.2 toc N 스타일 필터링 (RAN5 고유)
    
    | 규칙 | 설명 |
    | --- | --- |
    | toc 1~8 전부 제외 | TOC 영역에서 사용. Heading N과 동일 텍스트가 중복 존재 |
    | Heading 1~6, 8만 파싱 | 실제 본문 Section Heading |
    | 단일 DOCX | toc N (TOC) + Heading N (본문) 쌍으로 존재 |
    | 분할 DOCX | Heading N만 존재 (TOC는 cover에 별도) |
    
    ### 9.3 Heading 매핑 단순화
    
    RAN5는 비표준 2종(소량). Heading 9 없음.
    
    | 스타일 | level | 비고 |
    | --- | --- | --- |
    | Heading 1~7 | 1~7 | 표준 |
    | Heading 8 | 1 | Annex 대제목 |
    | Heading 3 Specs | 3 | 비표준 |
    | Heading 2.Head2A.2 | 2 | 비표준 |
    
    RAN5 TS는 H6, Header N, Heading 9 등 비표준 변형 없음. 위 표 외에 등장하는 스타일은 본문 단락으로 처리.
    
    ### 9.4 void shell / forward-redirect release (RAN5 고유, release-aware)
    
    UE 적합성 TS(38.5xx 계열)는 release별 "final" 버전 **다수가 void shell**이다. Heading 구조는 존재하나 본문이 `"5 to 7 Void"` + `"requirements ... provided in Release N [ref]"` 형태로 **다른 release를 후방 참조(forward-redirect)**하며, 실질 적합성 내용은 1~2개 release final에만 집중 게시된다 (예: 38.521-1은 Rel-15/16/17 final이 모두 shell이고 본문은 Rel-18 final에 존재). RF TS(RAN4)에는 이 패턴이 0건이며 RAN5 적합성 TS 고유.
    
    | 항목 | 처리 |
    | --- | --- |
    | 적재 방침 | **faithful 적재 (Option A)**. void shell release도 정상 spec-release로 적재하고, redirect 텍스트를 Section 본문으로 보존(Vector DB에서 검색 가능 → "Rel-15에서는 Rel-18을 보라"는 사실 자체가 답변 근거) |
    | 신규 relation | 추가 안 함. `redirectsTo` 등 명시 관계는 의미 변경(§3.1 사용자 결정 영역)이므로 도입하지 않고, redirect는 Section 본문 텍스트로만 표현 |
    | 무결성 | Section 수가 적은(sec≈5~8, tbl=fig=0) void shell release도 Release Integrity R1~R6 통과 대상. 섹션 부족을 파서 버그/적재 누락으로 오판 금지 (§8.1) |
    | 분포 | release별 실질-내용 spec vs void shell 분포 = Appendix A.1.3 census |
    
    ---
    
    ---
    
    ## Step 8: Entity Layer (v3.0 신규)
    
    > Ontology v3.0 changelog 참조: `ontology/tdoc-ontology.ttl`. v2.0/v2.1에서 `rdfs:subClassOf tdoc:Section`으로 정의되어 Section 노드 라벨링만 가능했던 5개 entity 클래스 (`RRCParameter`, `CapabilityItem`, `Procedure`, `PerformanceRequirement`, `ConformanceTest`)를 v3.0에서 **independent class**로 재정의. 본 Step에서 Phase-3 산출물에 entity-layer 노드 + 관계를 추가 적재한다. 사용자 허락 (세션) 하에 5 RAN spec 일관 갱신.
    
    ---
    
    ## 1. Step 8 목적
    
    v2.0/v2.1까지의 KG는 Section 노드에 `:RRCParameter`/`:CapabilityItem` 등 multi-label만 부여하여 *section-level mock entity*만 적재되었다 (예: RAN2 `:Section:CapabilityItem`는 38.306 §4.x section 단위이고, 개별 `ltm-MCG-IntraFreq-r18` 같은 item-level capability는 부재). v3.0은 item-level entity를 **독립 노드**로 적재하여 답변 파이프라인이 chunkId 외에 entity name으로도 Neo4j MATCH할 수 있도록 한다.
    
    4-tier 모델 (v3.0):
    
    ```
    Tdoc/Resolution layer  ── Phase-1/2 (메타데이터)
        │
    Section layer          ── Phase-3 Step 1~7 (TS 구조)
        │
    Entity layer (NEW)     ── Phase-3 Step 8 (이번 단계)
        │
    Feature layer          ── feature_catalog.yaml (cross-RAN curated)
    ```
    
    ## 2. Entity 클래스 적용 범위 (RAN5)
    
    | Entity 클래스 | 본 RAN item-level 적재 | granularity=section 기존 잔존 | 대표 예시 |
    | --- | --- | --- | --- |
    | `RRCParameter` | ❌ (UE conformance test spec — IE 정의 아님) | 0 | — |
    | `CapabilityItem` | ❌ | 0 | — |
    | `Procedure` | ❌ | 0 | — |
    | `PerformanceRequirement` | ❌ | 0 | — |
    | `ConformanceTest` | ✅ UE conformance test case item-level (38.508-x, 38.521-x, 38.523-1, 38.533) | ✅ legacy section-level (Appendix A) | Test case IDs §6.3.2.x, §6.3.3.x |
    | `Feature` | ✅ 22 catalog features (cross-RAN) | — | UE test for Rel-16 eType-II, LTM |
    
    → "❌"는 본 RAN의 spec body 본질상 해당 entity가 정의되지 않음. 일관성을 위해 entity-loader 스크립트는 5 RAN 모두 동일 디렉토리 구조로 배치하되, 적재 결과 0건이 정상.
    
    ## 3. ID 생성 규칙
    
    | Entity 클래스 | ID 패턴 | 예시 |
    | --- | --- | --- |
    | `RRCParameter` | `ie:{ieName}@spec:{specNumber}` | `ie:CodebookConfig-r16@spec:38.331` |
    | `CapabilityItem` | `cap:{capabilityItemName}@spec:{specNumber}` | `cap:ltm-MCG-IntraFreq-r18@spec:38.306` |
    | `Procedure` | `proc:{procedureName}@{specNumber}-§{section}` | `proc:BFR-Procedure@38.321-§5.17` |
    | `PerformanceRequirement` | `perfReq:{perfReqName}@spec:{specNumber}` | `perfReq:TEvaluate_BFD_SSB@spec:38.133` |
    | `ConformanceTest` | `test:{testCaseId}@spec:{specNumber}` | `test:38.521-4-§6.3.2.2.6@spec:38.521-4` |
    | `Feature` | `feature:{featureId}` (cross-RAN, single ID space) | `feature:rel18_ltm` |
    
    `granularity` property 값:
    - `"item"`: item-level entity node (v3.0 신규 적재). 본 Step의 주 대상.
    - `"section"`: v2.0/v2.1에서 적재된 section-level legacy node. 그대로 보존, granularity property만 backfill.
    
    ## 4. 입력/출력
    
    ### 입력 (read-only — 본 Step에서 재임베딩 없음)
    
    - **Qdrant**: `ran{N}_ts_sections`, `ran{N}_ts_asn1_chunks` (존재하는 RAN만)
    - **YAML**: `ontology/config/feature_catalog.yaml` (Feature 정의)
    - **Neo4j**: 기존 Phase-3 산출물 (`:Spec`, `:Section`, `:TSTable`, `:TSFigure`)
    
    ### 출력 (Neo4j 추가 적재)
    
    - 신규 노드: `:RRCParameter`, `:CapabilityItem`, `:Procedure`, `:PerformanceRequirement`, `:ConformanceTest`, `:Feature` (item-level)
    - 신규 관계: `:definedInSection`, `:hasEntity`(inverse), `:partOfFeature`, `:usesIE`, `:hasCapability`, `:hasProcedure`, `:hasPerfRequirement`, `:hasConformanceTest`, `:definedByIE`, `:disjointWith`(Feature⊥Feature)
    
    ### Property
    
    | Class | 의무 property | 선택 |
    | --- | --- | --- |
    | `RRCParameter` | `ieName`, `granularity`, `asn1ChunkId` (Qdrant FK) | `ieKind`, `isCapabilityComposite`, `release` |
    | `CapabilityItem` | `capabilityItemName`, `granularity` | `capabilityGranularity` (Per-UE/Band/BC), `release` |
    | `Procedure` | `procedureName`, `granularity` | `release` |
    | `PerformanceRequirement` | `perfReqName`, `granularity` | `release` |
    | `ConformanceTest` | `testCaseId`, `granularity` | `release` |
    | `Feature` | `featureName`, `introducedInRelease` | `featureDescription` |
    
    ## 5. 적재 절차
    
    ```
    scripts/RAN/formal/RAN{N}/phase-3/entity-loader/
      ├── 01_load_rrc_parameters.py       # RAN1/4/5는 0건, RAN2/3 실 적재
      ├── 02_load_capability_items.py     # RAN2만 실 적재
      ├── 03_load_procedures.py           # RAN1/2/3 실 적재
      ├── 04_load_performance_requirements.py  # RAN4만 실 적재
      ├── 05_load_conformance_tests.py    # RAN4/5만 실 적재
      ├── 06_load_features.py             # 5 RAN 공통 (cross-phase/ontology/load_feature_instances_neo4j.py 이관)
      └── 99_run_all.py                   # orchestration
    ```
    
    5 RAN 동일 디렉토리 구조 유지 — 적재할 entity가 없는 RAN에서도 스크립트 존재 (`if RAN not in scope: return early` 패턴). 일관성을 우선한 의도된 중복.
    
    ## 6. 검증 규칙
    
    | 규칙 ID | 검증 내용 |
    | --- | --- |
    | P3-S8-V01 | 모든 item-level 노드는 `granularity = "item"` property 필수 |
    | P3-S8-V02 | 모든 entity 노드는 `:definedInSection` 관계로 최소 1개 `:Section` 노드와 연결 |
    | P3-S8-V03 | 동일 `name` + `specNumber` 조합으로 중복 entity 노드 0건 (MERGE 의무) |
    | P3-S8-V04 | `:Feature`는 `feature_catalog.yaml` entry 수와 동일 (cross-RAN 22) |
    | P3-S8-V05 | `:Feature` ↔ `:RRCParameter`/`:CapabilityItem`/`:Procedure` 관계는 feature_catalog의 `ie_refs`/`capability_refs`/`procedure_refs` 와 1:1 매칭 |
    | P3-S8-V06 | `:Feature` `disjointWith` 관계는 feature_catalog `disjoint_feature_groups`와 정합 |
    | P3-S8-V07 | Qdrant ASN.1 chunk count ↔ Neo4j `:RRCParameter` item count drift < 5% (96.4% IE 추출 success rate 반영) |
    
    ## 7. CQ 의무
    
    본 Step의 CQ는 `logs/RAN/formal/RAN{N}/phase-3/cq_test_dataset.json` 에 P3-S8-CQ01~CQ08로 추가:
    
    - P3-S8-CQ01: 5 RAN entity 클래스별 노드 카운트 baseline
    - P3-S8-CQ02: 모든 entity는 `:definedInSection` 관계 존재
    - P3-S8-CQ03: Feature ↔ entity 관계 정합 (`USES_IE`, `HAS_CAPABILITY` 등)
    - P3-S8-CQ04: Feature disjointWith 정합
    - P3-S8-CQ05: granularity property 분포 (item vs section)
    - P3-S8-CQ06: RAN2 `CodebookConfig-r16` `LTM-Config-r18` 핵심 IE 존재 (cross-cycle baseline)
    - P3-S8-CQ07: 28 LTM capability items 모두 적재 (cycle-02 D-B baseline)
    - P3-S8-CQ08: feature_catalog disjoint_feature_groups (LTM ⊥ CHO ⊥ CPC ⊥ CPAC) 모두 적재
    
    ## 8. Phase-10/11 incremental hook
    
    신규 spec release 또는 미팅 적재 시 entity layer 자동 update:
    - Phase-10 (new meeting): TDoc 단위 적재이므로 entity layer 영향 없음
    - Phase-11 (TS/TR/CR update): TS 신규 release → 신규 Section 적재 후 `entity-loader/99_run_all.py` trigger 의무
      → `scripts/RAN/formal/RAN{N}/phase-11/` orchestration에 entity-loader hook 추가 (Phase F 작업)
    
    ## 9. Backward compatibility
    
    v3.0 entity 클래스가 `rdfs:subClassOf tdoc:Section` 제거되어 SPARQL query `?s a tdoc:Section`이 entity 노드 미포함 결과 반환. 본 변경은 **MAJOR bump 의도된 breaking change** (`ontology/tdoc-ontology.ttl` v3.0 changelog 참조). 외부 query 수정 필요한 경우:
    
    ```
    # v2.x 패턴:
    ?s a tdoc:Section .  # 모든 section + entity 매칭
    
    # v3.0 패턴:
    { ?s a tdoc:Section } UNION { ?s a tdoc:RRCParameter } UNION ...
    # 또는 새 super-property 활용:
    ?s tdoc:definedInSection|^tdoc:hasSubSection*/^tdoc:belongsToSpec ?spec .
    ```
    
    기존 v2.0/v2.1 적재된 multi-label 노드 (`:Section:CapabilityItem` RAN2, `:Section:PerformanceRequirement` RAN4, `:Section:ConformanceTest` RAN4+5; 적재 수는 Appendix A)는 `granularity = "section"` property 부여로 보존. v3.0 신규 적재는 pure entity 노드 (`granularity = "item"`).
    
    ---
    
    ## Phase-3 온톨로지 완료
    
    ## Appendix A: 기준 수치
    
    > 이 테이블이 Spec의 수치 권위 소스이다.
    >
    
    > 수치 변경 시 이 테이블만 수정한다.
    >
    
    > **구현 완료 후 실측치로 작성한다.** (구현 전 미측정 껍데기 금지)
    >
    
    > **🔴 release-aware 전환 중**: 아래 A.1.1 P3-V01~V15는 **재설계 이전 latest-only(spec당 최신 1버전) Neo4j 적재 상태** 수치이다. release-aware 파서가 산출한 신규 baseline(spec×release)은 **A.1.3**에 있으며, Neo4j 재적재(Stage 5)는 완료되었으며(A.1.1 latest-only는 historical 보존, 현 Neo4j 실측은 release-aware-migration/migration_report.json), Qdrant 재적재는 §3.6 게이트로 보류 중이다. RAN5는 중간 JSON-LD가 없으므로 현 시점 통계 검증은 `parse_summary_release.json`(파서 JSON 집계)을 권위로 사용한다.
    
    ### A.1.1 latest-only 적재 baseline (재설계 이전, 교체 예정)
    
    | ID | 항목 | 기준값 | 비고 |
    | --- | --- | --- | --- |
    | P3-V01 | Section 총 수 | **33,948** (재측정; Phase-3 baseline = 10,349) | 15 TS 파싱 결과. Phase-3 ts-parser 재실행으로 sub-section 분해 깊어짐 (`docs/cross-phase/baselines/baseline_snapshot_2026-04-25.md` §10) |
    | P3-V02 | TSTable 총 수 | **25,911** | 적합성 시험표 |
    | P3-V03 | TSFigure 총 수 | **924** | 시험 구성도 |
    | P3-V04 | orphan Section 수 | **0** | BELONGS_TO_SPEC = Section 전수 (Phase-3 baseline 10,349; 재측정 33,948) |
    | P3-V05 | clausesAffected 커버리지 | **4,430 / 34,586** (12.8%) | 분모 34,586 = **Phase-4 초기 CR 파서(`01_parse_cr_documents.py` v0, 감사 리포트 E-6 대응 산출)가 CR-Form Table 2에서 "Clauses affected" 컬럼 자체가 *존재했던* CR subset**. Phase-1 CR 전체(P1-V02=53,288) 중 CR-Form이 없거나 "Clauses affected" 컬럼 자체가 누락된 CR은 분모에서 제외. 비어있지 않은 CR 4,430(분자). 분모·분자 모두 최초 파싱 시점(2026-02~03) 스냅샷이며, 이후 Phase-4 파서 개선(교훈 32, specNumber 교정 등)으로 실측치는 갱신됨 — 최신 실측은 Phase-4 Appendix A P4-V05(MODIFIES_SECTION=26,813) 및 CR-with-clausesAffected 분포를 참조. 본 V-ID는 Spec 설계 근거 보존용 상수로 고정 |
    | P3-V06 | Resolution→CR 커버리지 | **25 res → 135 CR** | Conclusion REFERENCES CR |
    | P3-V07 | Void Section 수 | **223** | 전체 Section의 2.2% |
    | P3-V08 | referencesSection 수 | **14,709** | Section → Section |
    | P3-V09 | referencesSpec 수 | **3,531** | Section → Spec |
    | P3-V10 | 계층 edges | **9,822** | PARENT_SECTION = HAS_SUB_SECTION |
    | P3-V11 | hasSection edges | **527** | Spec → level-1 Section |
    | P3-V12 | BELONGS_TO_SPEC edges | **33,948** (재측정; Phase-3 baseline = 10,349) | Section 전수 (Section 수와 동수) |
    | P3-V13 | CONTAINS_TABLE edges | **25,893** | 매핑 성공분 (18 unmapped) |
    | P3-V14 | CONTAINS_FIGURE edges | **916** | 매핑 성공분 (8 unmapped) |
    | P3-V15 | 파서 warnings | **2,117** | 중복/경미 |
    
    ### A.1.3 release-aware 파서 baseline (spec×release) + void shell census

    > release-aware 파서(`scripts/RAN/formal/RAN5/phase-3/ts-parser/parse_ts_docx.py`)가 산출한 **파서 JSON**(`ontology/output/RAN/formal/parsed_ts/RAN5/ts_{spec}_{release}.json`) 집계. 권위 출처 = `parse_summary_release.json`. Release Integrity R1~R6 전수 PASS(`validate_release_integrity.py`). Neo4j/Qdrant 재적재(Stage 5+, 파괴적·보류)는 이 수치를 입력으로 하며, 완료 후 A.1.1을 release-aware 실측으로 교체한다. 측정 시점·산출 출처는 A.3 변경 이력. RAN5는 중간 JSON-LD가 없어 현 시점 통계는 파서 JSON 집계가 권위이다.

    **(a) 전체 집계 (15 spec · 66 spec-release · excluded 0 · skipped 0)**

    | 항목 | 값 | 비고 |
    | --- | --- | --- |
    | spec-release 총 수 | **66** | 15 spec × 참여 release (release-미존재 spec-release 제외) |
    | substantive | **38** | 실질 내용 보유 release |
    | void shell (forward-redirect) | **28** | tbl=0 ∧ fig=0 ∧ sec≤10, 본문이 후방 release 참조 (§9.4) |
    | Section 총 수 | **76,749** | 전 spec-release 합 |
    | TSTable 총 수 | **59,471** | 적합성 시험표 |
    | TSFigure 총 수 | **2,151** | 시험 구성도 |
    | Void Section 수 | **694** | `isVoid=true` Section |
    | referencesSection 수 | **42,706** | Section → Section (동일 release 내, cross-release leak 0) |
    | referencesSpec 수 | **12,786** | Section → Spec (same-release 12,760 + nearest≤source 26) |
    | 파서 warnings | **10,854** | 중복/경미 |

    **(b) release별 참여 분포**

    | Release | 참여 spec | Section | TSTable | TSFigure | 비고 |
    | --- | --- | --- | --- | --- | --- |
    | Rel-15 | 12 | 1,971 | 1,026 | 44 | 다수 void shell |
    | Rel-16 | 12 | 193 | 1 | 26 | 대부분 void shell |
    | Rel-17 | 15 | 7,482 | 6,945 | 381 | |
    | Rel-18 | 15 | 33,255 | 25,099 | 894 | 실질 내용 집중 |
    | Rel-19 | 12 | 33,848 | 26,400 | 806 | 실질 내용 집중 |

    **(c) spec별 substantive vs void shell** — UE 적합성 TS(38.5xx)는 release별 final 다수가 forward-redirect void shell이며 실질 내용은 1~2 release에 집중 (§9.4). void shell도 redirect 텍스트를 검색 가능한 Section 내용으로 faithful 적재:

    | Spec | substantive release | void shell release |
    | --- | --- | --- |
    | 38.508-1 | Rel-15, 18, 19 | Rel-16, 17 |
    | 38.508-2 | Rel-15, 18, 19 | Rel-16, 17 |
    | 38.509 | Rel-15~18 (전부) | — |
    | 38.521-1 | Rel-18, 19 | Rel-15, 16, 17 |
    | 38.521-2 | Rel-18, 19 | Rel-15, 16, 17 |
    | 38.521-3 | Rel-15, 18, 19 | Rel-16, 17 |
    | 38.521-4 | Rel-18, 19 | Rel-15, 16, 17 |
    | 38.521-5 | Rel-18, 19 | Rel-17 |
    | 38.522 | Rel-18, 19 | Rel-15, 16, 17 |
    | 38.523-1 | Rel-17, 18, 19 | Rel-15, 16 |
    | 38.523-2 | Rel-17, 18, 19 | Rel-15, 16 |
    | 38.523-3 | Rel-17, 18 | Rel-15, 16 |
    | 38.533 | Rel-18, 19 | Rel-15, 16, 17 |
    | 38.551 | Rel-17, 18 (전부) | — |
    | 38.561 | Rel-17, 18, 19 (전부) | — |

    **(d) Release Integrity (R1~R6) — `validate_release_integrity.py` 전수 PASS**

    | Rule | 검사 | 결과 |
    | --- | --- | --- |
    | R1 | 모든 sectionId가 `-Rel-NN-` 토큰 보유 | PASS (76,749) |
    | R2 | sectionId release == 파일 release | PASS |
    | R3 | sectionId spec == 파일 spec (하이픈 안전) | PASS |
    | R4 | cross-release referencesSection leak = 0 | PASS |
    | R5 | specVersion 존재 + release/count == summary | PASS |
    | R6 | referencesSpec가 대상 spec의 현재 버전으로 해소 (same-release, 없으면 ≤source 최신) | PASS (12,760 same + 26 nearest≤source) |

    ### A.2 구현 CQ 검증 결과
    
    > Spec Step 1의 CQ는 온톨로지 **설계 근거**이다.
    아래는 구현에서 사용하는 **검증 CQ**로, 설계 CQ를 포함하되 구현 검증용으로 확장/재구성되었다.
    >
    
    | 항목 | 설계 CQ (Spec) | 검증 CQ (구현) |
    | --- | --- | --- |
    | 개수 | 5그룹 (CQ1~CQ5) | Phase-3 CQ 데이터셋 |
    | 검증 결과 | - | **41 PASS / 0 WARN / 0 FAIL / 0 ERROR** |
    | 결과 파일 | - | Phase-3 CQ Cypher 결과 |
    
    ---


    ### A.1.2 v2.0 + v2.1 Ontology classType 분포 (update — Flywheel ⑦ 핵심)

    RAN5 phase-3은 v2.1 신규 클래스 **ConformanceTest**의 주력 영역.

    | classType | RAN5 분포 | 의미 |
    | --- | --- | --- |
    | **`ConformanceTest` (v2.1)** | **Qdrant 9,268 (`ran5_ts_sections`)** + **18,268 (`ran5_ts_sections_p12`)** + **Neo4j 33,047** (BELONGS_TO_SPEC) | 38.508-1/2 (721) + 38.509 (99) + 38.521-1/2/3/4 (3,202) + 38.523-1/3 (3,025) + 38.533 (2,221) |
    | `Feature` (v2.0) | 20 nodes in Neo4j RAN5 (cross-RAN, F-1.6) | Feature catalog instances |

    **v2.1 신규 클래스**: `tdoc:ConformanceTest` (subClassOf Section) — RAN5 UE test + RAN4 BS test 본질 기준.

    **관련 도구**: `scripts/cross-phase/ontology/classify_sections.py` / `audit_classtype_coverage.py` / `add_neo4j_section_labels.py` / `load_feature_instances_neo4j.py`
    **관련 Flywheel 표준**: `docs/autonomous-self-improvement-flywheel/flywheel-process.md`
    
    ### A.3 변경 이력
    
    | 날짜 | 변경 내용 |
    | --- | --- |
    | 2026-06-10 | release-aware 전환(비파괴 Stage 4). ID 포맷 `{specNumber}-{release}-{sectionNumber}` (예 `38.521-1-Rel-18-6.2.4`, RAN5는 전부 하이픈 spec이라 release 토큰이 `-1` 뒤에 위치, release 토큰 `-Rel-NN-`), tableId/figureId 동일; Spec 노드 = (specNumber, release) + `specInRelease`/`specRelease` 부착 (§2.1, §2.2, 연결 키 예시). 신규 §8.1 Release Integrity R1~R6 — RAN5는 중간 JSON-LD가 없어 `validate_release_integrity.py`가 **파서 JSON**에 대해 검증(RAN5 referencesSpec 보유 → R6 적용). 신규 §9.4 void shell / forward-redirect — UE 적합성 TS(38.5xx)는 release별 final 다수가 void shell(본문이 후방 release 참조)이며 faithful 적재(redirect 텍스트=검색 가능 Section 내용, 신규 relation 미도입). Appendix A를 A.1.1(latest-only, 재설계 이전·교체 예정) + A.1.3(release-aware 파서 baseline + void shell census)로 분리. 38.591-1~4는 DOCX 입력 부재로 release-aware에서도 제외. Neo4j 재적재(Stage 5)는 완료(A.1.1 latest-only는 historical 보존, 현 실측은 migration_report.json), Qdrant는 §3.6 보류 |
