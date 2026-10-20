- **phase-3: Ontology 101 기반 HW/SW 엔지니어 타겟으로 확장 (TS)**
    
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
    
    **3GPP RAN2 Technical Specification(TS) 문서의 구조와 참조 관계**
    
    ### 1.2 For what are we going to use the ontology?
    
    **Phase-1~2 온톨로지를 확장**하여 다음을 지원:
    
    - TS 구조 탐색 — Section 계층 네비게이션
    - TS 간 참조 분석 — 문서 간 참조 관계 파악
    - CR → TS 연결 — CR이 어떤 TS/Section을 수정했는지 추적
    - Resolution → TS 연결 — Resolution이 승인한 CR의 TS 수정 추적
    
    ### 1.3 Who will use and maintain the ontology?
    
    | 사용자 | 핵심 니즈 |
    | --- | --- |
    | **HW/SW 엔지니어** | TS 구조 파악, 특정 기능 스펙 위치 찾기 |
    | **표준화 엔지니어** | CR이 수정한 Section 확인 |
    | **전략/기획** | 기술 트렌드, 특정 영역 변경 현황 |
    | **IP/특허** | 기술 표준 반영 현황, 기여 증거 |
    
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
    
    ### 1.6 RAN2 데이터 특성
    
    | 항목 | RAN2 | 비고 |
    | --- | --- | --- |
    | TS 범위 | 38.3xx + 37.324 | L2/L3 프로토콜 시리즈 |
    | 총 Section | [P3-V01] | Heading 1~8 |
    | 최대 TS | 38.331 (RRC 프로토콜) | 섹션 수 최다 |
    | Heading depth | 1~8 | Heading 7/8 사용 |
    | TSTable | [P3-V02] | |
    | TSFigure | [P3-V03] | |
    | Void Section | Appendix A (§2.5 분류 정의 참조) | |
    | ASN.1 | 38.331 중심 | |
    | 제외 스타일 | TH, NO, ZA/ZB/ZT/ZU | 커스텀 스타일 포함 |
    
    ---
    
    ## 2. Scope 정의
    
    ### 2.1 포함 (In Scope)
    
    | 구분 | 포함 대상 |
    | --- | --- |
    | **TS 문서** | 37.324, 38.300, 38.304, 38.305, 38.306, 38.314, 38.321, 38.322, 38.323, 38.331, 38.340, 38.351, 38.355, 38.391 |
    | **Release 차원 (release-aware)** | 각 TS의 **release별 final 버전** (Rel-15/16/17/18/19). 동일 spec번호라도 release마다 **별개 Spec 노드**이며, sectionId·Spec IRI가 release 키를 포함한다 (예: `38.331-Rel-15-...` ≠ `38.331-Rel-17-...`). spec×release = spec-release 단위로 적재 |
    | **Section 구조** | 본문 + Annex, 8레벨까지 |
    | **Table 메타데이터** | ID, 캡션, 번호, 위치 |
    | **Figure 메타데이터** | ID, 캡션, 번호, 위치 |
    | **TS 간 참조** | Section 간 내부/외부 참조 |
    | **기존 연결** | Spec(Phase-1) ↔ TS(Phase-3) 매핑 |
    
    ### 2.2 제외 (Out of Scope)
    
    | 제외 대상 | 이유 |
    | --- | --- |
    | Section 본문 텍스트 | Vector DB 영역 |
    | Table 셀 데이터 | Vector DB 영역 |
    | 수식 내용 | Vector DB 영역 (LaTeX) |
    | **ASN.1 본문 텍스트** | Vector DB 영역. Section 노드(sectionId, sectionNumber, title, level)는 포함하되, ASN.1 코드 본문은 Graph DB에 저장하지 않음 |
    | TS **intra-release** 버전 히스토리 (한 release 내 모든 draft/중간 버전) | 복잡도 증가, 향후 확장. release별 **final 버전 1개**만 적재 (release-aware). 각 release final의 버전값은 Spec 확장의 specVersion에 기록 (Step 4 §6 참조) |
    | RAN2 외 TS (36.xxx 등) | Scope 한정 |
    
    ### 2.3 Graph DB vs Vector DB 경계
    
    | Graph DB (Phase-3) | Vector DB |
    | --- | --- |
    | Section ID, 번호, 제목, 레벨 | Section 본문 텍스트 |
    | Section 계층 관계 | 본문 임베딩 |
    | Table/Figure 메타데이터 | Table 셀 데이터 |
    | TS 간 참조 관계 | 수식 내용 |
    | CR/Resolution 연결 | **ASN.1 본문 텍스트** |
    
    **연결 키**: sectionId (예: `38.331-Rel-15-5.1.3.2` — release 키 포함)
    
    ---
    
    ## 3. 용어 정의
    
    | 용어 | 정의 | 온톨로지 | 예시 |
    | --- | --- | --- | --- |
    | **TS** | Technical Specification 문서 | Spec (Phase-1) | 38.331 |
    | **Spec** | Phase-1 클래스명, TS와 동의어 | Spec | 38.331 |
    | **Section** | TS 내부 계층 구조 (본문 + Annex) | Section (Phase-3) | 5.1.3.2, A.1 |
    | **Clause** | Section의 3GPP 공식 용어 (동의어) | Section | 5.1.3.2 |
    | **Annex** | Section 중 알파벳으로 시작하는 것 | Section | A, A.1, B.2 |
    | **Table** | TS 내 표 | TSTable (Phase-3) | Table 5.1.3.2-1 |
    | **Figure** | TS 내 그림 | TSFigure (Phase-3) | Figure 5-1 |
    
    ### 3.1 용어 구분
    
    | 헷갈리는 것 | 구분 |
    | --- | --- |
    | Spec vs TS | 같음. Spec은 Phase-1 클래스명, TS는 3GPP 공식 용어. 교차 참조 시 "TS(=Spec)" / "Spec(=TS)" 모두 허용 |
    | Section vs Clause | 같음. Section은 온톨로지 클래스명, Clause는 3GPP 공식 용어 |
    | Section vs Spec | 다름. Spec은 문서 전체, Section은 문서 내부 구조 |
    | Section vs Annex | Annex ⊂ Section. sectionNumber 패턴으로 구분 (`^[A-Z]` = Annex) |
    | "Section" (영문) vs "섹션" (한글) | 동일 개념. 클래스명 참조 시 "Section 노드", 일반 서술 시 "섹션" 혼용 허용. 수치 단위는 "Section 수" (예: P3-V01) |
    | Working Group vs WG vs 작업 그룹 | 동일 개념. 첫 도입부에서 "Working Group (WG)" 정의 후 본문은 약어 "WG" 사용 권장 |
    
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
    
    *CQ4 제약사항: Resolution이 CR을 references하는 경우만 (Appendix A [P3-V06] 참조)*
    
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
    | **Resolution → CR 연결** | Appendix A [P3-V06] 참조 | Resolution이 CR을 references하는 경우만 |
    | **TS 버전** | release별 final 버전 (Rel-15~19 각 1개). 각 release final 버전을 specVersion에 기록 | intra-release draft 히스토리(한 release 내 중간 버전)는 미지원. specVersion은 Phase-1에서 정의된 기존 속성이며, Phase-3에서 release별 Spec 노드마다 값을 채운다 |
    | **TS 범위** | RAN2 관련 | 37.324, 38.300, 38.304~306, 38.314, 38.321~323, 38.331, 38.340, 38.351, 38.355, 38.391 |
    
    > **specVersion·release 추출 규칙 (release-aware)**: Phase-3는 각 spec-release의 **cover page**에서 release와 버전을 추출하여 release별 Spec 노드의 specVersion에 저장한다. release 자체는 입력 디렉토리 구조 `data/data_raw/RAN/formal/TS/RAN2/{spec}/{release}/`에서 산출한다.
    >
    > - 정본 추출기: `scripts/RAN/formal/common/phase-0/ts_cover_metadata.py` (`_find_doc()` cover 우선 탐색 → `cover_version()` / `cover_release()`)
    > - cover page는 해당 release의 **final 버전**(예: Rel-15 → V15.30.0)을 명시하므로, 파일명 휴리스틱보다 권위 있다 (멀티파트 split spec은 `_cover.docx`가 별도 존재)
    > - 버전 코드 참고: 3자리 base-36 `{major}{minor}{patch}`, 첫 글자 major=release (f=15, g=16, h=17, i=18, j=19)
    > - specVersion은 Phase-1에서 정의된 기존 속성(xsd:string, 0..1)이며, Phase-3에서 **release별 Spec 노드마다** 값을 채운다
    
    ---
    
    ## 7. CQ 요약
    
    | CQ 그룹 | 커버리지 |
    | --- | --- |
    | CQ1. TS 구조 탐색 | 100% |
    | CQ2. TS 간 참조 분석 | 100% |
    | CQ3. CR → TS 연결 | 100% (3-4만 [P3-V05] 참조) |
    | CQ4. Resolution → TS 연결 | [P3-V06] 참조  |
    | CQ5. 통합 분석 | 100% |
    
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
    
    ### 1.1 기본 전제
    
    > Phase-3는 Phase-1~2 온톨로지의 확장이다.
    >
    > - Phase-1~2의 모든 클래스, 관계, 인스턴스는 그대로 유지
    > - Phase-3는 TS 구조를 추가하고 기존 데이터와 연결
    > - 기존 CQ는 모두 답변 가능 유지
    
    ### 1.2 Phase-1 온톨로지
    
    | 항목 | 내용 |
    | --- | --- |
    | 도메인 | 3GPP RAN2 Tdoc 메타데이터 |
    | 데이터 소스 | Tdoc_list (Excel) |
    
    ### 1.3 Phase-2 온톨로지
    
    | 항목 | 내용 |
    | --- | --- |
    | 도메인 | 3GPP RAN2 Final Report Resolution/Role |
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
    | **CQ4** (Resolution 연결) | Resolution | Phase-2 |
    |  | CR, Spec, Meeting | Phase-1 |
    |  | Section | Phase-3 신규 |
    | **CQ5** (통합 분석) | 위 전체 조합 | Phase-1~3 |
    
    ### 2.2 Phase-1 클래스 - 전체 유지
    
    | 클래스 | Phase-3 CQ 사용 | 비고 |
    | --- | --- | --- |
    | **Spec** | ✅ CQ1, CQ3, CQ4, CQ5 | Phase-3 Section과 연결 |
    | **CR** | ✅ CQ3, CQ4, CQ5 |  |
    | **Meeting** | ✅ CQ3, CQ4, CQ5 |  |
    | **Company** | ✅ CQ3, CQ5 |  |
    | **WorkItem** | ✅ CQ3, CQ5 |  |
    | **Release** | ✅ CQ5 |  |
    | Tdoc | ⚪ (CR 상위 클래스) | 간접 사용 |
    | LS | ⚪ | 기존 유지 |
    | Contact | ⚪ | 기존 유지 |
    | WorkingGroup | ⚪ | 기존 유지 |
    | AgendaItem | ⚪ | 기존 유지 |
    
    ### 2.3 Phase-2 클래스 - 전체 유지
    
    | 클래스 | Phase-3 CQ 사용 | 비고 |
    | --- | --- | --- |
    | **Resolution** | ✅ CQ4 |  |
    | Agreement | ⚪ (Resolution 하위) | 간접 사용 |
    | Conclusion | ⚪ (Resolution 하위) | 간접 사용 |
    | WorkingAssumption | ⚪ (Resolution 하위) | 간접 사용 |
    | Table | ⚪ | 기존 유지 (Phase-3와 별개) |
    
    *참고: RAN2 Phase-2에는 Summary, SessionNotes, Figure, Chart 클래스가 없음*
    
    ---
    
    ## 3. Phase-3 CQ 기반 관계 사용 분석
    
    ### 3.1 Phase-1 관계 - 전체 유지
    
    | 관계 | Domain → Range | Phase-3 CQ 사용 | 비고 |
    | --- | --- | --- | --- |
    | **modifies** | CR → Spec | ✅ CQ3, CQ4 | 핵심 경로 |
    | **submittedBy** | Tdoc → Company | ✅ CQ3, CQ5 |  |
    | **relatedTo** | Tdoc → WorkItem | ✅ CQ3, CQ5 |  |
    | **presentedAt** | Tdoc → Meeting | ✅ CQ3, CQ4 |  |
    | **targetRelease** | Tdoc → Release | ✅ CQ5 |  |
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
    | **references** | Resolution → Tdoc | ✅ CQ4 | 핵심 경로 |
    | **madeAt** | Resolution → Meeting | ✅ CQ4 |  |
    | resolutionBelongsTo | Resolution → AgendaItem | ⚪ | 기존 유지 |
    | hasResolutions | AgendaItem → Resolution | ⚪ | 기존 유지 |
    | hasTable | Resolution → Table | ⚪ | 기존 유지 |
    | containedIn | Table → Meeting | ⚪ | 기존 유지 |
    
    *참고: RAN2 Phase-2에는 hasFigure, hasChart, moderatedBy, chairedBy, contentWithEquations, promotedTo 관계가 없음 (Phase-2 §3.4 참조 — "changed to an agreement" 패턴이 RAN2 데이터에서 자동 추출 불가하여 promotedTo 미정의)*
    
    ---
    
    ## 4. 클래스명 충돌 해결
    
    ### 4.1 문제
    
    | Phase | 클래스 | 용도 |
    | --- | --- | --- |
    | Phase-2 | Table | Final Report 내 embedded content |
    | Phase-3 | (신규) | TS 문서 내 embedded content |
    
    **같은 개념이지만 다른 문서 소스.**
    
    ### 4.2 해결
    
    | Phase-2 클래스 | Phase-3 클래스 | 용도 |
    | --- | --- | --- |
    | Table | **TSTable** | TS 문서 내 Table |
    | (없음) | **TSFigure** | TS 문서 내 Figure |
    
    **Phase-3에서는 `TSFigure`, `TSTable` 클래스명 사용하여 명시적 구분.**
    
    *참고: RAN2 Phase-2에는 Figure 클래스가 없으므로 TSFigure와의 충돌 없음. 일관성을 위해 TS 접두사 사용.*
    
    ---
    
    ## 5. 핵심 연결 경로
    
    Phase-3 CQ를 답변하기 위한 핵심 경로:
    
    ```
    [CQ3 경로: CR → TS → Section]
    CR -[modifies]-> Spec -[hasSection]-> Section
          ↑            ↑                     ↑
       Phase-1        Phase-1               Phase-3 신규
    
    [CQ4 경로: Resolution → CR → TS → Section]
    Resolution -[references]-> CR -[modifies]-> Spec -[hasSection]-> Section
         ↑              ↑           ↑             ↑                     ↑
      Phase-2          Phase-2       Phase-1         Phase-1            Phase-3 신규
    
    ```
    
    ---
    
    ## 6. Spec ↔ TS 연결
    
    ### 6.1 분석
    
    - Phase-1 `Spec` 클래스: specNumber = "38.331"
    - Phase-3 TS 데이터: 38.331 문서 파싱
    
    **같은 것을 가리킴.**
    
    ### 6.2 결정
    
    | 옵션 | 설명 | 결정 |
    | --- | --- | --- |
    | A. TS 클래스 신규 | Spec과 별도 | ❌ |
    | B. Spec 클래스 재사용 | Section을 Spec에 연결 | ✅ |
    
    **Spec 클래스 재사용. Section은 Spec의 하위 구조로 연결.**
    
    ```
    Spec (Phase-1 기존)
    └─[hasSection]→ Section (Phase-3 신규)
    
    ```
    
    ---
    
    ## 7. 외부 온톨로지 재사용
    
    | 온톨로지 | Phase-1~2 용도 | Phase-3 | 결정 |
    | --- | --- | --- | --- |
    | Dublin Core | title, identifier | Section 제목에 적용 | ✅ 유지 |
    | FOAF | Organization | 간접 사용 | ✅ 유지 |
    
    추가 외부 온톨로지 불필요.
    
    ---
    
    ## 8. 요약
    
    ### 8.1 클래스 현황
    
    | 구분 | 클래스 |
    | --- | --- |
    | **Phase-1 (전체 유지)** | Tdoc, CR, LS, Meeting, Company, Contact, WorkItem, AgendaItem, Release, Spec, WorkingGroup |
    | **Phase-2 (전체 유지)** | Resolution, Agreement, Conclusion, WorkingAssumption, Table |
    | **Phase-3 CQ 직접 사용** | Spec, CR, Meeting, Company, WorkItem, Release, Resolution |
    | **Phase-3 신규 (예상)** | Section, TSTable, TSFigure |
    
    ### 8.2 관계 현황
    
    | 구분 | 관계 |
    | --- | --- |
    | **Phase-1 (전체 유지)** | submittedBy, hasContact, relatedTo, belongsTo, targetRelease, presentedAt, isRevisionOf, revisedTo, replyTo, replyIn, modifies, sentTo, ccTo, originalLS, originatedFrom |
    | **Phase-2 (전체 유지)** | references, madeAt, resolutionBelongsTo, hasResolutions, hasTable, containedIn (RAN2 Phase-2는 promotedTo 미정의) |
    | **Phase-3 CQ 직접 사용** | modifies, submittedBy, relatedTo, presentedAt, targetRelease, references, madeAt |
    | **Phase-3 신규 (예상)** | hasSection, hasSubSection, containsTable, containsFigure, referencesSection 등 |
    
    ### 8.3 범례
    
    | 기호 | 의미 |
    | --- | --- |
    | ✅ | Phase-3 CQ에서 직접 사용 |
    | ⚪ | Phase-3 CQ 미사용 (기존 유지, Phase-1~2 CQ 답변 가능) |
    
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
    - TS 문서에서 **실제로 추출 가능한지** 확인
    
    ---
    
    ## 2. 데이터 소스
    
    | 항목 | 내용 |
    | --- | --- |
    | 문서 | 37.324, 38.300, 38.304, 38.305, 38.306, 38.314, 38.321, 38.322, 38.323, 38.331, 38.340, 38.351, 38.355, 38.391 |
    | 형식 | Word 문서 |
    | 범위 | 본문 + Annex |
    
    ### 2.1 TS 문서 목록
    
    | TS | 제목 |
    | --- | --- |
    | 37.324 | SDAP specification |
    | 38.300 | NR and NG-RAN Overall Description; Stage 2 |
    | 38.304 | User Equipment (UE) procedures in Idle mode and RRC Inactive state |
    | 38.305 | Stage 2 functional specification of UE positioning in NG-RAN |
    | 38.306 | User Equipment (UE) radio access capabilities |
    | 38.314 | Layer 2 Measurements |
    | 38.321 | Medium Access Control (MAC) protocol specification |
    | 38.322 | Radio Link Control (RLC) protocol specification |
    | 38.323 | Packet Data Convergence Protocol (PDCP) specification |
    | 38.331 | Radio Resource Control (RRC) protocol specification |
    | 38.340 | Backhaul Adaptation Protocol (BAP) specification |
    | 38.351 | Sidelink relay adaptation protocol specification |
    | 38.355 | Sidelink Relay Adaptation Protocol (SRAP) specification |
    | 38.391 | NR positioning protocol specification |
    
    ---
    
    ## 3. 용어 나열
    
    ### 3.1 TS 구조 관련
    
    | 용어 | 설명 | 데이터 소스 | 관련 CQ |
    | --- | --- | --- | --- |
    | **TS (=Spec)** | Technical Specification 문서 | 문서 자체 | CQ1, CQ3, CQ4, CQ5 |
    | **Section** | TS 내부 계층 구조 (본문 + Annex) | 헤딩 파싱 | CQ1, CQ2, CQ3, CQ4 |
    | **TSTable** | TS 내 표 | `<w:tbl>` 파싱 | CQ1 |
    | **TSFigure** | TS 내 그림 | `<w:drawing>` 파싱 | CQ1 |
    
    *참고: TS는 Phase-1 Spec 클래스 재사용 (Step 2 결정)*
    
    ### 3.2 Section 속성 관련
    
    | 용어 | 설명 | 데이터 소스 | 관련 CQ |
    | --- | --- | --- | --- |
    | **sectionId** | Section 고유 식별자 | 생성 (TS번호-섹션번호) | 전체 |
    | **sectionNumber** | Section 번호 | 헤딩 파싱 (예: 5.1.3.2, A.1) | CQ1 |
    | **sectionTitle** | Section 제목 | 헤딩 파싱 | CQ1-9 |
    | **level** | Section 계층 레벨 | 번호에서 추출 (1~7) | CQ1-4 |
    | **isVoid** | Void 여부 | 본문에 "Void" 텍스트 | CQ1 |
    
    ### 3.3 TSTable 속성 관련
    
    | 용어 | 설명 | 데이터 소스 | 관련 CQ |
    | --- | --- | --- | --- |
    | **tableId** | Table 고유 식별자 | 생성 | CQ1 |
    | **tableNumber** | Table 번호 | 캡션 파싱 (예: 5.1.3.2-1) | CQ1-10 |
    | **tableCaption** | Table 캡션 | 캡션 파싱 | CQ1 |
    
    ### 3.4 TSFigure 속성 관련
    
    | 용어 | 설명 | 데이터 소스 | 관련 CQ |
    | --- | --- | --- | --- |
    | **figureId** | Figure 고유 식별자 | 생성 | CQ1 |
    | **figureNumber** | Figure 번호 | 캡션 파싱 (예: 5-1) | CQ1 |
    | **figureCaption** | Figure 캡션 | 캡션 파싱 | CQ1 |
    
    ### 3.5 관계 관련 (Phase-3 신규)
    
    | 용어 | 설명 | 관련 CQ |
    | --- | --- | --- |
    | **hasSection** | Spec → Section (최상위) | CQ1 |
    | **hasSubSection** | Section → Section (부모-자식) | CQ1-2, CQ1-3 |
    | **containsTable** | Section → TSTable | CQ1-5, CQ1-7 |
    | **containsFigure** | Section → TSFigure | CQ1-6 |
    | **referencesSection** | Section → Section (TS 간 참조) | CQ2 |
    
    ### 3.6 기존 연결 관련 (Phase-1~2 재사용)
    
    | 용어 | 설명 | 출처 | 관련 CQ |
    | --- | --- | --- | --- |
    | **modifies** | CR → Spec | Phase-1 | CQ3 |
    | **references** | Resolution → Tdoc | Phase-2 | CQ4 |
    | **clausesAffected** | CR이 수정한 Section 번호 | Phase-1 CR 속성 | CQ3-4 |
    
    ---
    
    ## 4. CQ별 필요 용어 매핑
    
    ### CQ1: TS 구조 탐색
    
    | CQ | 필요 용어 |
    | --- | --- |
    | 1-1 | Spec, Section, hasSection |
    | 1-2 | Section, hasSubSection |
    | 1-3 | Section, hasSubSection (역방향) |
    | 1-4 | Section, level |
    | 1-5 | Section, TSTable, containsTable |
    | 1-6 | Section, TSFigure, containsFigure |
    | 1-7 | TSTable, containsTable (역방향) |
    | 1-8 | Spec, TSTable |
    | 1-9 | Section, sectionTitle |
    | 1-10 | TSTable, tableNumber, Section |
    
    ### CQ2: TS 간 참조 분석
    
    | CQ | 필요 용어 |
    | --- | --- |
    | 2-1 | Section, referencesSection |
    | 2-2 | Section, referencesSection (역방향) |
    | 2-3 | Spec, referencesSection |
    | 2-4 | Section, referencesSection |
    | 2-5 | Spec, referencesSection |
    
    ### CQ3: CR → TS 연결
    
    | CQ | 필요 용어 |
    | --- | --- |
    | 3-1 | CR, modifies, Spec |
    | 3-2 | CR, modifies, Spec, hasSection, Section |
    | 3-3 | Spec, modifies (역방향), CR |
    | 3-4 | Section, clausesAffected, CR |
    | 3-5 | WorkItem, CR, modifies, Spec |
    | 3-6 | Company, CR, modifies, Spec |
    
    ### CQ4: Resolution → TS 연결
    
    | CQ | 필요 용어 |
    | --- | --- |
    | 4-1 | Resolution, references, CR, modifies, Spec |
    | 4-2 | Spec, modifies, CR, references, Resolution |
    | 4-3 | Meeting, Resolution, references, CR, modifies, Spec |
    | 4-4 | WorkItem, CR, references, Resolution, modifies, Spec |
    
    ### CQ5: 통합 분석
    
    | CQ | 필요 용어 |
    | --- | --- |
    | 5-1 | Spec, CR, modifies |
    | 5-2 | Company, CR, modifies, Spec |
    | 5-3 | Release, CR, modifies, Spec |
    | 5-4 | Spec, CR, modifies |
    
    ---
    
    ## 5. 요약
    
    ### 5.1 용어 목록
    
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
    
    ### 5.2 신규 vs 재사용 구분
    
    | 구분 | 용어 |
    | --- | --- |
    | **Phase-3 신규** | Section, TSTable, TSFigure, hasSection, hasSubSection, containsTable, containsFigure, referencesSection |
    | **Phase-1~2 재사용** | Spec, modifies, references, clausesAffected |
    
    ### 5.3 검증
    
    | 검증 항목 | 결과 |
    | --- | --- |
    | 모든 용어가 Step 1 Scope 내? | ✅ |
    | 모든 용어가 CQ 답변에 필요? | ✅ |
    | TS 문서에서 추출 가능? | ✅ |
    | Step 2 결정과 일관성? | ✅ |
    
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
    
    ---
    
    ## 3. Step 3 용어 → 클래스 판단
    
    ### 3.1 TS 구조 관련 용어
    
    | 용어 | 여러 인스턴스? | 독립 객체? | 클래스 여부 | 비고 |
    | --- | --- | --- | --- | --- |
    | **TS (=Spec)** | ✅ | ✅ | ✅ 클래스 | Phase-1 Spec 재사용 |
    | **Section** | ✅ | ✅ | ✅ 클래스 | Phase-3 신규 |
    | **TSTable** | ✅ | ✅ | ✅ 클래스 | Phase-3 신규 |
    | **TSFigure** | ✅ | ✅ | ✅ 클래스 | Phase-3 신규 |
    
    ### 3.2 속성 관련 용어
    
    | 용어 | 클래스 여부 | 처리 |
    | --- | --- | --- |
    | sectionId, sectionNumber, sectionTitle, level, isVoid | ❌ | Step 5 Data Property |
    | tableId, tableNumber, tableCaption | ❌ | Step 5 Data Property |
    | figureId, figureNumber, figureCaption | ❌ | Step 5 Data Property |
    
    ### 3.3 관계 관련 용어
    
    | 용어 | 클래스 여부 | 처리 |
    | --- | --- | --- |
    | hasSection, hasSubSection, containsTable, containsFigure, referencesSection | ❌ | Step 5 Object Property |
    | modifies, references, clausesAffected | ❌ | Phase-1~2 재사용 |
    
    ---
    
    ## 4. Phase-3 신규 클래스
    
    ### 4.1 클래스 목록
    
    | 클래스 | 정의 |
    | --- | --- |
    | **Section** | TS 내부 계층 구조 (본문 + Annex) |
    | **TSTable** | TS 내 표 |
    | **TSFigure** | TS 내 그림 |
    
    ### 4.2 계층 구조 검토
    
    **질문: Section, TSTable, TSFigure 간에 상속 관계가 있는가?**
    
    | 기준 | Section vs TSTable | Section vs TSFigure | TSTable vs TSFigure |
    | --- | --- | --- | --- |
    | 추가 속성? | 다름 | 다름 | 비슷 |
    | 다른 제약조건? | 다름 | 다름 | 비슷 |
    | 다른 관계? | 다름 | 다름 | 비슷 |
    
    **결론: 서로 상속 관계 없음. 독립 클래스.**
    
    ### 4.3 TSTable vs TSFigure 공통 상위 클래스 검토
    
    | 속성 | TSTable | TSFigure |
    | --- | --- | --- |
    | ID | tableId | figureId |
    | Number | tableNumber | figureNumber |
    | Caption | tableCaption | figureCaption |
    
    | 기준 | 판단 |
    | --- | --- |
    | 인스턴스 수 | TSTable [P3-V02]개 vs TSFigure [P3-V03]개 (불균형) |
    | CQ에서 함께 조회? | ❌ 없음 |
    | Ontology 101 | "불필요한 클래스 만들지 말라" |
    
    **결론: 공통 상위 클래스 불필요. 독립 클래스 유지.**
    
    ### 4.4 Section 하위 클래스 검토
    
    | 후보 | 추가 속성? | 다른 제약? | 다른 관계? | 하위 클래스? |
    | --- | --- | --- | --- | --- |
    | Annex | ❌ 동일 | ❌ 동일 | ❌ 동일 | ❌ 불필요 |
    | Void Section | ❌ 동일 | ❌ 동일 | ❌ 동일 | ❌ 불필요 |
    
    **결론: Section 하위 클래스 불필요. sectionNumber 패턴과 isVoid 속성으로 구분.**
    
    ---
    
    ## 5. 전체 클래스 계층 다이어그램
    
    ```
    ┌─────────────────────────────────────────────────────────────────┐
    │                    RAN2 TS Ontology (Phase-3)                   │
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
    │  Resolution ──[references]──→ Tdoc            │                 │
    │  ├── Agreement                                │                 │
    │  ├── Conclusion                               │                 │
    │  └── WorkingAssumption                        │                 │
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
    
    ## 6. 클래스별 상세
    
    ### 6.1 Section
    
    | 항목 | 내용 |
    | --- | --- |
    | 정의 | TS 문서의 내부 계층 구조 단위 (본문 + Annex) |
    | 상위 클래스 | 없음 (독립) |
    | 하위 클래스 | 없음 |
    | 구분 | sectionNumber 패턴 (`^[0-9]` = 본문, `^[A-Z]` = Annex) |
    | 특수 케이스 | isVoid = true인 경우 Void Section |
    
    ### 6.2 TSTable
    
    | 항목 | 내용 |
    | --- | --- |
    | 정의 | TS 문서 내 표 |
    | 상위 클래스 | 없음 (독립) |
    | 하위 클래스 | 없음 |
    | Phase-2 Table과 구분 | 클래스명으로 구분 (TSTable vs Table) |
    
    ### 6.3 TSFigure
    
    | 항목 | 내용 |
    | --- | --- |
    | 정의 | TS 문서 내 그림 |
    | 상위 클래스 | 없음 (독립) |
    | 하위 클래스 | 없음 |
    | Phase-2 Figure과 구분 | RAN2 Phase-2에는 Figure 클래스 없음. 일관성을 위해 TS 접두사 사용 |
    
    ---
    
    ## 7. Phase-1~2 클래스와의 연결
    
    | Phase-3 클래스 | 연결 대상 | 관계 | 방향 |
    | --- | --- | --- | --- |
    | Section | Spec (Phase-1) | hasSection | Spec → Section |
    | Section | Section | hasSubSection | Section → Section (부모→자식) |
    | Section | Section | referencesSection | Section → Section (참조) |
    | TSTable | Section | containsTable | Section → TSTable |
    | TSFigure | Section | containsFigure | Section → TSFigure |
    
    ---
    
    ## 8. 요약
    
    ### 8.1 Phase-3 신규 클래스
    
    | 클래스 | 상속 |
    | --- | --- |
    | Section | 없음 |
    | TSTable | 없음 |
    | TSFigure | 없음 |
    
    ### 8.2 클래스로 정의하지 않은 용어
    
    | 용어 | 이유 | 처리 |
    | --- | --- | --- |
    | sectionId, sectionNumber 등 | 속성값 | Step 5 Data Property |
    | hasSection, containsTable 등 | 관계 | Step 5 Object Property |
    | TS | Phase-1 Spec 재사용 | Step 2에서 결정 |
    | Annex | Section과 동일 구조 | sectionNumber 패턴으로 구분 |
    | Void Section | Section과 동일 구조 | isVoid 속성으로 구분 |
    
    ### 8.3 누적 클래스 현황
    
    | Phase | 클래스 |
    | --- | --- |
    | Phase-1 | Tdoc, CR, LS, Meeting, Company, Contact, WorkItem, AgendaItem, Release, Spec, WorkingGroup |
    | Phase-2 | Resolution, Agreement, Conclusion, WorkingAssumption, Table |
    | **Phase-3** | **Section, TSTable, TSFigure** |
    
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
    - **Inverse Property**: 역관계 명시
    - 제약조건(Cardinality 등)은 Step 6에서 정의
    
    ---
    
    ## 2. 속성의 종류
    
    | 종류 | 설명 | 예시 |
    | --- | --- | --- |
    | **Data Property** | 객체의 속성값 | sectionNumber, tableCaption |
    | **Object Property** | 다른 객체와의 관계 | hasSection, containsTable |
    | **Inverse Property** | 역방향 관계 | hasSection ↔ belongsToSpec |
    
    ---
    
    ## 3. Section 클래스 속성
    
    ### 3.1 Data Property
    
    | Property | Type | Description | 데이터 소스 |
    | --- | --- | --- | --- |
    | sectionId | String | Section 고유 식별자 | 생성 (예: 38.331-Rel-15-5.1.3.2) |
    | sectionNumber | String | Section 번호 | 헤딩 파싱 (예: 5.1.3.2, A.1) |
    | sectionTitle | String | Section 제목 | 헤딩 파싱 |
    | level | Integer | Section 계층 레벨 (1~7) | 헤딩 스타일에서 추출 (아래 매핑 참조). Heading 8 → level 1 (Annex 대제목) |
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
    | Heading 7 | 7 | 38.305, 38.306 |
    | Heading 8 | 1 | Annex 대제목 |
    
    **제외 스타일 (Section이 아닌 것):**

    > 제외 스타일은 Section 계층에서 빠진다(실측 건수는 본문에 고정하지 않음).

    | 스타일 | 용도 | 처리 |
    | --- | --- | --- |
    | TH | Table/메시지 캡션 | 제외 |
    | NO | NOTE 텍스트 | 제외 |
    | ZA | 표지 (버전 정보) | 제외 |
    | ZB | 표지 (문서 유형) | 제외 |
    | ZT | 표지 (제목) | 제외 |
    | ZU | 표지 (빈 줄) | 제외 |
    
    ### 3.2 Object Property
    
    | Property | Range | Inverse | Description |
    | --- | --- | --- | --- |
    | belongsToSpec | Spec | hasSection | Section이 속한 TS |
    | hasSubSection | Section | parentSection | 하위 Section (부모→자식) |
    | parentSection | Section | hasSubSection | 상위 Section (자식→부모) |
    | referencesSection | Section | referencedBySection | 참조하는 다른 Section |
    | referencedBySection | Section | referencesSection | 이 Section을 참조하는 Section |
    | referencesSpec | Spec | - | TS-only 참조 (clause 없이 TS 번호만 언급, Section→Spec) |
    | containsTable | TSTable | tableInSection | Section에 포함된 Table |
    | containsFigure | TSFigure | figureInSection | Section에 포함된 Figure |
    
    ---
    
    ## 4. TSTable 클래스 속성
    
    ### 4.1 Data Property
    
    | Property | Type | Description | 데이터 소스 |
    | --- | --- | --- | --- |
    | tableId | String | Table 고유 식별자 | 생성 (예: 38.331-Rel-15-T5.1.3.2-1) |
    | tableNumber | String | Table 번호 | 캡션 파싱 (예: 5.1.3.2-1) |
    | tableCaption | String | Table 캡션 | 캡션 파싱 |
    
    ### 4.2 Object Property
    
    | Property | Range | Inverse | Description |
    | --- | --- | --- | --- |
    | tableInSection | Section | containsTable | Table이 속한 Section |
    
    ---
    
    ## 5. TSFigure 클래스 속성
    
    ### 5.1 Data Property
    
    | Property | Type | Description | 데이터 소스 |
    | --- | --- | --- | --- |
    | figureId | String | Figure 고유 식별자 | 생성 (예: 38.300-Rel-15-F5-1) |
    | figureNumber | String | Figure 번호 | 캡션 파싱 (예: 5-1) |
    | figureCaption | String | Figure 캡션 | 캡션 파싱 |
    
    ### 5.2 Object Property
    
    | Property | Range | Inverse | Description |
    | --- | --- | --- | --- |
    | figureInSection | Section | containsFigure | Figure가 속한 Section |
    
    ---
    
    ## 6. Spec 클래스 확장 (Phase-1 기존 + Phase-3 추가)
    
    ### 6.1 추가 Object Property
    
    | Property | Range | Inverse | Description |
    | --- | --- | --- | --- |
    | hasSection | Section | belongsToSpec | Spec이 포함하는 최상위 Section |
    
    *참고: Spec의 기존 속성(specNumber 등)은 Phase-1에서 정의됨. release-aware 설계에서 Phase-3는 (specNumber, release)별 Spec 노드를 생성하고, 각 spec-release의 cover page에서 추출한 final 버전을 specVersion에, release 토큰을 specRelease/specInRelease에 설정한다 (추출 규칙: Step 1 §6 참조).*
    
    ---
    
    ## 7. 전체 Object Property 목록 (Phase-3 신규)
    
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
    | 11 | referencesSpec | Section | Spec | - | TS-only 참조 (Section→Spec) |
    
    ---
    
    ## 8. 전체 Data Property 목록 (Phase-3 신규)
    
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
    
    ## 9. Inverse Property 정리
    
    | 정방향 | 역방향 | 설명 |
    | --- | --- | --- |
    | hasSection | belongsToSpec | Spec ↔ 최상위 Section |
    | hasSubSection | parentSection | 부모 Section ↔ 자식 Section |
    | containsTable | tableInSection | Section ↔ TSTable |
    | containsFigure | figureInSection  | Section ↔ TSFigure |
    | referencesSection | referencedBySection | 참조 ↔ 피참조 Section |
    
    ---
    
    ## 10. Phase-1~2 재사용 관계 (CQ 답변에 필요)
    
    | Property | Domain | Range | 출처 | 관련 CQ |
    | --- | --- | --- | --- | --- |
    | modifies | CR | Spec | Phase-1 | CQ3 |
    | references | Resolution | Tdoc | Phase-2 | CQ4 |
    | submittedBy | Tdoc | Company | Phase-1 | CQ3, CQ5 |
    | relatedTo | Tdoc | WorkItem | Phase-1 | CQ3, CQ5 |
    | presentedAt | Tdoc | Meeting | Phase-1 | CQ3, CQ4 |
    | targetRelease | Tdoc | Release | Phase-1 | CQ5 |
    | madeAt | Resolution | Meeting | Phase-2 | CQ4 |
    
    *참고: Phase-1 CR의 clausesAffected 속성은 Section 연결에 사용 (CQ3-4)*
    
    ---
    
    ## 11. 계층 구조 예시
    
    ```
    38.331 (Spec)
      │
      ├─[hasSection]─→ Section "5" (level 1)
      │                   │
      │                   ├─[hasSubSection]─→ Section "5.1" (level 2)
      │                   │                      │
      │                   │                      ├─[hasSubSection]─→ Section "5.1.3" (level 3)
      │                   │                      │                      │
      │                   │                      │                      └─[containsTable]─→ TSTable "5.1.3-1"
      │                   │                      │
      │                   │                      └─[hasSubSection]─→ Section "5.1.4" (level 3)
      │                   │
      │                   └─[hasSubSection]─→ Section "5.2" (level 2)
      │                                          │
      │                                          └─[referencesSection]─→ Section "5.1.3"
      │
      └─[hasSection]─→ Section "A" (level 1, Annex)
                          │
                          └─[containsFigure]─→ TSFigure "A-1"
    
    ```
    
    ---
    
    ## 12. 요약
    
    **Section:**
    
    - DP: sectionId, sectionNumber, sectionTitle, level, isVoid
    - OP: belongsToSpec, hasSubSection, parentSection, referencesSection, referencedBySection, referencesSpec, containsTable, containsFigure
    
    **TSTable:**
    
    - DP: tableId, tableNumber, tableCaption
    - OP: tableInSection
    
    **TSFigure:**
    
    - DP: figureId, figureNumber, figureCaption
    - OP: figureInSection
    
    **Spec (확장):**
    
    - OP: hasSection
    
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
    - **Inverse**: 역관계 명시
    - **기타 특성**: Irreflexive, Asymmetric, Transitive 등
    
    ---
    
    ## 2. Facet 종류
    
    | Facet | 설명 | 예시 |
    | --- | --- | --- |
    | **Cardinality** | 속성값 개수 | 0..1, 1, 0..*, 1..* |
    | **Required** | 필수 여부 | ✅ / ❌ |
    | **Functional** | 단일값만 허용 | ✅ (최대 1개) |
    | **Inverse** | 역관계 | hasSubSection ↔ parentSection |
    | **Irreflexive** | 자기참조 불허 | A-R-A 불가능 |
    | **Asymmetric** | 비대칭 관계 | A-R-B ⟹ B-R-A 불가 |
    | **Transitive** | 전이 관계 | A-R-B, B-R-C ⟹ A-R-C |
    
    ### Cardinality 표기법
    
    | 표기 | 의미 | Required | Functional |
    | --- | --- | --- | --- |
    | 1 | 정확히 1개 | ✅ | ✅ |
    | 0..1 | 0개 또는 1개 | ❌ | ✅ |
    | 1..* | 1개 이상 | ✅ | ❌ |
    | 0..* | 0개 이상 | ❌ | ❌ |
    
    ---
    
    ## 3. Section Data Property Facet
    
    | Property | Type | Cardinality | Required | 제약 | Description |
    | --- | --- | --- | --- | --- | --- |
    | sectionId | String | 1 | ✅ | PK | 패턴: `{specNumber}-{release}-{sectionNumber}` (release 키 포함, 예: `38.331-Rel-15-5.1.3.2`) |
    | sectionNumber | String | 1 | ✅ | 패턴 | 본문: `^[0-9]+(\\.[0-9]+[a-zA-Z]?)*(\\.[A-Z])?$`, Annex: `^[A-Z](\\.[0-9]+)*$` |
    | sectionTitle | String | 1 | ✅ | - | Section 제목 |
    | level | Integer | 1 | ✅ | 범위 | min=1, max=7 (Heading 8 → level 1) |
    | isVoid | Boolean | 1 | ✅ | default | default: false |
    
    ---
    
    ## 4. Section Object Property Facet
    
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
    
    ### 특성 설명
    
    | Property | 특성 | 이유 |
    | --- | --- | --- |
    | hasSubSection | Irreflexive | Section이 자기 자신의 하위가 될 수 없음 |
    | hasSubSection | Asymmetric | A가 B의 부모면 B는 A의 부모가 아님 |
    | parentSection | Irreflexive | Section이 자기 자신의 상위가 될 수 없음 |
    | parentSection | Asymmetric | A가 B의 자식이면 B는 A의 자식이 아님 |
    | referencesSection | Irreflexive | Section이 자기 자신을 참조하는 것은 무의미 |
    | referencesSection | NOT Asymmetric | 두 Section이 서로 참조 가능 (상호 참조) |
    | hasSubSection | NOT Transitive | 직접 하위만 연결 (손자는 체인으로) |
    
    ---
    
    ## 5. TSTable Data Property Facet
    
    | Property | Type | Cardinality | Required | 제약 | Description |
    | --- | --- | --- | --- | --- | --- |
    | tableId | String | 1 | ✅ | PK | 패턴: `{specNumber}-{release}-T{tableNumber}` (예: `38.331-Rel-15-T6.1.2-1`) |
    | tableNumber | String | 1 | ✅ | 패턴 | `^[0-9A-Z]+(\.[0-9]+)*-[0-9]+$` |
    | tableCaption | String | 0..1 | ❌ | - | 캡션 없는 Table 존재 가능 |
    
    ---
    
    ## 6. TSTable Object Property Facet
    
    | Property | Domain | Range | Cardinality | Functional | Inverse | 특성 |
    | --- | --- | --- | --- | --- | --- | --- |
    | tableInSection | TSTable | Section | 1 | ✅ | containsTable | - |
    
    ---
    
    ## 7. TSFigure Data Property Facet
    
    | Property | Type | Cardinality | Required | 제약 | Description |
    | --- | --- | --- | --- | --- | --- |
    | figureId | String | 1 | ✅ | PK | 패턴: `{specNumber}-{release}-F{figureNumber}` (예: `38.331-Rel-15-F4.2.1-1`) |
    | figureNumber | String | 1 | ✅ | 패턴 | `^[0-9A-Z]+(\.[0-9]+)*-[0-9]+$` |
    | figureCaption | String | 0..1 | ❌ | - | 캡션 없는 Figure 존재 가능 |
    
    ---
    
    ## 8. TSFigure Object Property Facet
    
    | Property | Domain | Range | Cardinality | Functional | Inverse | 특성 |
    | --- | --- | --- | --- | --- | --- | --- |
    | figureInSection | TSFigure | Section | 1 | ✅ | containsFigure | - |
    
    ---
    
    ## 9. Spec 추가 Object Property Facet
    
    | Property | Domain | Range | Cardinality | Functional | Inverse | 특성 |
    | --- | --- | --- | --- | --- | --- | --- |
    | hasSection | Spec | Section | 1..* | ❌ | belongsToSpec | - |
    | specInRelease | Spec | Release | 1 | ✅ | - | release별 Spec 노드 → 해당 Release 노드 (IRI `tdoc:release/Rel_NN`) |
    
    **설명:** 모든 TS는 최소 1개 이상의 최상위 Section을 가짐. release-aware 설계에서 Spec 노드는 (specNumber, release) 단위이며 `specInRelease`로 자신의 Release에 연결된다.

    ### 9.1 Spec 추가 Data Property (release-aware)

    | Property | Type | Cardinality | Required | 제약 | Description |
    | --- | --- | --- | --- | --- | --- |
    | specRelease | String | 1 | ✅ | enum | denormalized release 토큰 `Rel-NN` (하이픈, 예: `Rel-15`). `specInRelease`의 비정규화 캐시 |
    | specVersion | String | 0..1 | ❌ | - | 해당 release의 final 버전 (Phase-1 정의 속성, Phase-3가 cover page에서 채움; 예: Rel-15 → `15.30.0`) |
    
    ---
    
    ## 10. 필수 속성 요약
    
    ### 10.1 필수 Data Property
    
    | Class | Required Properties |
    | --- | --- |
    | Section | sectionId, sectionNumber, sectionTitle, level, isVoid |
    | TSTable | tableId, tableNumber |
    | TSFigure | figureId, figureNumber |
    | Spec (release-aware) | specRelease |
    
    ### 10.2 필수 Object Property
    
    | Class | Required Properties |
    | --- | --- |
    | Section | belongsToSpec (1) |
    | TSTable | tableInSection (1) |
    | TSFigure | figureInSection (1) |
    | Spec | hasSection (1..*) |
    
    ---
    
    ## 11. Functional Property 요약
    
    단일값만 허용하는 Property:
    
    | Property | Domain | Range | Description |
    | --- | --- | --- | --- |
    | belongsToSpec | Section | Spec | Section은 하나의 Spec에만 속함 |
    | parentSection | Section | Section | Section은 하나의 부모만 가짐 |
    | tableInSection | TSTable | Section | Table은 하나의 Section에만 속함 |
    | figureInSection | TSFigure | Section | Figure는 하나의 Section에만 속함 |
    
    ---
    
    ## 12. Inverse Property 요약
    
    | Property | Inverse | Domain → Range |
    | --- | --- | --- |
    | hasSection | belongsToSpec | Spec → Section |
    | belongsToSpec | hasSection | Section → Spec |
    | hasSubSection | parentSection | Section → Section |
    | parentSection | hasSubSection | Section → Section |
    | containsTable | tableInSection | Section → TSTable |
    | containsFigure | figureInSection | Section → TSFigure |
    | tableInSection | containsTable | TSTable → Section |
    | figureInSection | containsFigure | TSFigure → Section |
    | referencesSection | referencedBySection | Section → Section |
    | referencedBySection | referencesSection | Section → Section |
    
    ---
    
    ## 13. 특수 제약조건 요약
    
    ### 13.1 Object Property 특성
    
    | Property | Irreflexive | Asymmetric | Transitive |
    | --- | --- | --- | --- |
    | hasSubSection | ✅ | ✅ | ❌ |
    | parentSection | ✅ | ✅ | ❌ |
    | referencesSection | ✅ | ❌ | ❌ |
    | referencedBySection | ✅ | ❌ | ❌ |
    | containsTable | - | - | - |
    | containsFigure | - | - | - |
    | tableInSection | - | - | - |
    | figureInSection | - | - | - |
    | hasSection | - | - | - |
    | belongsToSpec | - | - | - |
    
    ### 13.2 계층 구조 제약
    
    | 제약 | 설명 | 구현 |
    | --- | --- | --- |
    | 최상위 Section | parentSection = null | level = 1인 Section |
    | 말단 Section | hasSubSection = empty | 하위 Section 없음 |
    | level 일관성 | 부모 level + 1 = 자식 level | 검증 규칙 |
    
    ### 13.3 데이터 패턴
    
    **sectionNumber 패턴:**
    
    | 유형 | 패턴 | 예시 |
    | --- | --- | --- |
    | 본문 | `^[0-9]+(\\.[0-9]+[a-zA-Z]?)*(\\.[A-Z])?$` | 5, 5.1, 5.1.3.2, 5.1.2.1a, 8.1.4A |
    | Annex | `^[A-Z](\\.[0-9]+)*$` | A, A.1, A.1.2 |
    
    **ID 패턴:**
    
    | 클래스 | 패턴 | 예시 |
    | --- | --- | --- |
    | Section | `{specNumber}-{release}-{sectionNumber}` | 38.331-Rel-15-5.1.3.2 |
    | TSTable | `{specNumber}-{release}-T{tableNumber}` | 38.331-Rel-15-T5.1.3.2-1 |
    | TSFigure | `{specNumber}-{release}-F{figureNumber}` | 38.300-Rel-15-F5-1 |
    
    ---
    
    ## 14. 요약
    
    | 제약 유형 | 적용 Property |
    | --- | --- |
    | Irreflexive | hasSubSection, parentSection, referencesSection, referencedBySection |
    | Asymmetric | hasSubSection, parentSection |
    | level 범위 | min=1, max=7 (Heading 8 → level 1) |
    
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
    - **데이터 소스 매핑**: TS 문서 → 속성값
    - **예시 인스턴스**: 실제 데이터 기반 예시
    
    ---
    
    ## 2. 데이터 소스
    
    ### 2.1 TS 문서 목록
    
    | # | TS 번호 | 제목 | 버전 |
    | --- | --- | --- | --- |
    | 1 | 37.324 | SDAP specification | j00 |
    | 2 | 38.300 | NR and NG-RAN Overall Description; Stage 2 | j00 |
    | 3 | 38.304 | UE procedures in Idle mode and RRC Inactive state | j00 |
    | 4 | 38.305 | Stage 2 functional spec of UE positioning in NG-RAN | j00 |
    | 5 | 38.306 | User Equipment (UE) radio access capabilities | j00 |
    | 6 | 38.314 | Layer 2 Measurements | j00 |
    | 7 | 38.321 | Medium Access Control (MAC) protocol specification | j00 |
    | 8 | 38.322 | Radio Link Control (RLC) protocol specification | j00 |
    | 9 | 38.323 | Packet Data Convergence Protocol (PDCP) specification | j00 |
    | 10 | 38.331 | Radio Resource Control (RRC) protocol specification | j00 |
    | 11 | 38.340 | Backhaul Adaptation Protocol (BAP) specification | j00 |
    | 12 | 38.351 | Sidelink relay adaptation protocol specification | j10 |
    | 13 | 38.355 | Sidelink Relay Adaptation Protocol (SRAP) specification | j00 |
    | 14 | 38.391 | NR positioning protocol specification | j00 |
    
    ### 2.2 인스턴스 소스
    
    | 클래스 | 데이터 소스 |
    | --- | --- |
    | Section | TS 문서 헤딩 |
    | TSTable | TS 문서 테이블 캡션 |
    | TSFigure | TS 문서 그림 캡션 |
    
    ---
    
    ## 3. ID 생성 규칙
    
    ### 3.1 ID 생성 원칙
    
    | 원칙 | 설명 |
    | --- | --- |
    | 유일성 | 클래스 내에서 고유한 값 |
    | 불변성 | 한 번 생성되면 변경 불가 |
    | 의미성 | 도메인 의미 반영 |
    | 추적성 | 데이터 소스와 매핑 가능 |
    
    ### 3.2 클래스별 ID 패턴
    
    | 클래스 | ID 속성 | 패턴 | 예시 |
    | --- | --- | --- | --- |
    | Section | sectionId | `{specNumber}-{release}-{sectionNumber}` | 38.331-Rel-15-5.1.3.2 |
    | TSTable | tableId | `{specNumber}-{release}-T{tableNumber}` | 38.331-Rel-15-T5.1.3.2-1 |
    | TSFigure | figureId | `{specNumber}-{release}-F{figureNumber}` | 38.300-Rel-15-F5-1 |
    
    ### 3.3 ID 구성 요소
    
    | 구성 요소 | 설명 | 예시 |
    | --- | --- | --- |
    | specNumber | TS 규격 번호 | 38.331 |
    | release | 3GPP Release 토큰 | Rel-15, Rel-16, Rel-17, Rel-18, Rel-19 |
    | sectionNumber | Section 번호 | 5.1.3.2, A.1 |
    | tableNumber | Table 번호 | 5.1.3.2-1 |
    | figureNumber | Figure 번호 | 5-1 |
    | T prefix | Table 구분자 | T |
    | F prefix | Figure 구분자 | F |
    
    ---
    
    ## 4. 데이터 소스 매핑
    
    ### 4.1 Section 매핑

    > 이하 건수(ASN.1 줄 수, ASN.1 Section 수량 등)는 설계 시점 데이터 기준이며, 데이터 변경 시 갱신 대상이 아니다.

    **소스**: TS 문서 헤딩 (Heading 1~8 스타일)
    
    | 속성 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | sectionId | 생성 | `{specNumber}-{release}-{sectionNumber}` |
    | sectionNumber | 헤딩 텍스트 | 숫자/문자 패턴 추출 (예: "5.1.3.2") |
    | sectionTitle | 헤딩 텍스트 | sectionNumber 이후 텍스트 |
    | level | 헤딩 스타일 | 아래 매핑 참조 |
    | isVoid | 본문 내용 | 본문이 "Void" 텍스트만 있으면 true |
    
    **헤딩 스타일 → level 매핑:**
    
    | 스타일 | level | 비고 |
    | --- | --- | --- |
    | Heading 1~7 | 1~7 | 표준 |
    | Heading 8 | 1 | Annex 대제목 |
    
    **Section 관계 매핑**
    
    | 관계 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | belongsToSpec → Spec | 디렉토리 | specNumber + release 추출 (`{spec}/{release}/`) → 동일 release Spec 노드 매칭 |
    | hasSubSection → Section | 헤딩 계층 | 다음 레벨 헤딩들 연결 |
    | parentSection → Section | 헤딩 계층 | 이전 레벨 헤딩 연결 |
    | referencesSection → Section | 본문 패턴 | 참조 패턴 추출 (섹션 4.4 참조) |
    
    **ASN.1 포함 Section 처리:**
    
    | 항목 | 처리 |
    | --- | --- |
    | Section 노드 | 정상 생성 (sectionId, sectionNumber, sectionTitle, level, isVoid) |
    | ASN.1 본문 텍스트 | Graph DB에 저장하지 않음 (Vector DB 영역) |
    | 해당 TS | 38.331, 38.355, 38.305 |
    
    **ASN.1 정의명 sectionNumber (RAN2 고유):**
    
    38.331에서 ASN.1 정의 헤딩(`–\tBCCH-BCH-Message` 형태)이 Section으로 파싱됨. 이 경우 sectionNumber는 일반 숫자 패턴(`5.1.3.2`)이 아닌 ASN.1 정의명(`BCCH-BCH-Message`)이 됨.
    
    | 항목 | 일반 Section | ASN.1 정의 Section |
    | --- | --- | --- |
    | sectionNumber 패턴 | `^[0-9]+(\.[0-9]+)*$` 또는 `^[A-Z](\.[0-9]+)*$` | `^[A-Z][A-Za-z0-9-]+$` (예: `BCCH-BCH-Message`) |
    | sectionTitle | 별도 제목 | sectionNumber와 동일 |
    | sectionId | `38.331-Rel-15-5.1.3.2` | `38.331-Rel-15-BCCH-BCH-Message` |
    | 수량 | 대다수 | 38.331에 집중 (구체 건수 — Appendix A) |
    
    ### 4.2 TSTable 매핑
    
    **소스**: TS 문서 테이블 캡션
    
    | 속성 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | tableId | 생성 | `{specNumber}-{release}-T{tableNumber}` |
    | tableNumber | 캡션 텍스트 | "Table X.X.X-N:" 패턴에서 추출 |
    | tableCaption | 캡션 텍스트 | "Table X.X.X-N:" 이후 텍스트 |
    
    **TSTable 관계 매핑**
    
    | 관계 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | tableInSection → Section | tableNumber | tableNumber → sectionNumber 매핑 (섹션 4.5 참조) |
    
    ### 4.3 TSFigure 매핑
    
    **소스**: TS 문서 그림 캡션
    
    | 속성 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | figureId | 생성 | `{specNumber}-{release}-F{figureNumber}` |
    | figureNumber | 캡션 텍스트 | "Figure X.X.X-N:" 패턴에서 추출 |
    | figureCaption | 캡션 텍스트 | "Figure X.X.X-N:" 이후 텍스트 |
    
    **TSFigure 관계 매핑**
    
    | 관계 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | figureInSection → Section | figureNumber | figureNumber → sectionNumber 매핑 (섹션 4.5 참조) |
    
    ### 4.4 참조 패턴 (referencesSection)
    
    **본문 패턴**:
    
    | 패턴 | 정규식 | 예시 | 추출 결과 |
    | --- | --- | --- | --- |
    | clause X.X.X | `clause\s+(\d+(?:\.\d+)*)` | "clause 5.1.3" | 5.1.3 |
    | subclause X.X.X | `subclause\s+(\d+(?:\.\d+)*)` | "subclause 7.4.1.1" | 7.4.1.1 |
    | Section X.X.X | `Section\s+(\d+(?:\.\d+)*)` | "Section 5.1.3" | 5.1.3 |
    | Annex X | `Annex\s+([A-Z](?:\.\d+)*)` | "Annex A.1" | A.1 |
    | TS 38.XXX clause X.X | `TS\s+38\.(\d{3})\s+clause\s+(\d+(?:\.\d+)*)` | "TS 38.321 clause 5.4.3" | 38.321-{release}-5.4.3 (source와 동일 release) |
    | TS 37.XXX clause X.X | `TS\s+37\.(\d{3})\s+clause\s+(\d+(?:\.\d+)*)` | "TS 37.324 clause 5.1" | 37.324-{release}-5.1 (source와 동일 release) |
    | TS 38.XXX (TS-only) | `TS\s+(38\|37)\.(\d{3})` (clause 없음) | "TS 38.331" | → referencesSpec (Section→Spec) |
    
    **참조 대상 결정**:
    
    | 참조 유형 | 대상 결정 |
    | --- | --- |
    | 같은 TS 내 | 현재 specNumber + 현재 release + 추출된 sectionNumber |
    | 다른 TS (clause 있음) | 추출된 specNumber + **source와 동일 release** + 추출된 sectionNumber → referencesSection (cross-release 누출 0, validate R4) |
    | 다른 TS (clause 없음, TS-only) | 추출된 specNumber + **source와 동일 release** Spec 노드 → referencesSpec (Section→Spec). 자기 TS 제외, Scope 내 TS만 대상 (validate R6) |
    
    **참조 생성 시 주의사항**:
    
    | 주의사항 | 처리 |
    | --- | --- |
    | 대상 Section 없음 | 관계 생성 안 함 (로그 기록) |
    | 자기 자신 참조 | 무시 (Irreflexive) |
    | Scope 외 TS 참조 | 관계 생성 안 함 (Scope 내 TS만 대상) |
    
    ### 4.5 tableNumber/figureNumber → sectionNumber 매핑
    
    **정상 케이스 (X.X.X-N)**:
    
    | 입력 | 출력 | 규칙 |
    | --- | --- | --- |
    | 5.1.3.2-1 | 5.1.3.2 | 마지막 `-N` 제거 |
    | 5.1.3.2-10 | 5.1.3.2 | 마지막 `-N` 제거 |
    | A.1-1 | A.1 | 마지막 `-N` 제거 |
    
    **예외 처리**:
    
    | 케이스 | 처리 |
    | --- | --- |
    | `-` 없음 (X.X.X) | 전체를 sectionNumber로 사용 |
    | 매칭 Section 없음 | 오류 로그, 상위 Section 탐색 |
    | 상위도 없음 | 오류 로그, tableInSection/figureInSection = null |
    
    ---
    
    ## 5. 계층 구조 생성 규칙
    
    ### 5.1 Section 계층 생성
    
    ```
    [파싱 순서]
    1. TS 문서에서 모든 헤딩 추출 (Heading 1~8)
    2. 각 헤딩에서 sectionNumber, sectionTitle, level 추출
    3. level 기반으로 부모-자식 관계 설정
    
    [부모-자식 연결 규칙]
    - 현재 Section의 부모 = 가장 가까운 상위 레벨 Section
    - level 1 Section은 parentSection = null (최상위)
    - level 1 Section만 Spec과 hasSection으로 연결
    
    ```
    
    ### 5.2 계층 생성 예시
    
    **입력 (헤딩 순서)**:
    
    ```
    Heading 1: 5 RRC procedures
    Heading 2: 5.1 RRC connection control
    Heading 3: 5.1.1 RRC connection establishment
    Heading 3: 5.1.2 RRC connection reconfiguration
    Heading 2: 5.2 Measurement configuration
    Heading 1: 6 Protocol data units
    
    ```
    
    **출력 (관계)**:
    
    ```
    38.331 Rel-15 (Spec)
      │
      ├─[hasSection]─→ 38.331-Rel-15-5 (level 1)
      │                   │
      │                   ├─[hasSubSection]─→ 38.331-Rel-15-5.1 (level 2)
      │                   │                      │
      │                   │                      ├─[hasSubSection]─→ 38.331-Rel-15-5.1.1 (level 3)
      │                   │                      │
      │                   │                      └─[hasSubSection]─→ 38.331-Rel-15-5.1.2 (level 3)
      │                   │
      │                   └─[hasSubSection]─→ 38.331-Rel-15-5.2 (level 2)
      │
      └─[hasSection]─→ 38.331-Rel-15-6 (level 1)
    
    ```
    
    ---
    
    ## 6. 역관계 자동 생성
    
    ### 6.1 Inverse 관계 생성 규칙
    
    | 정방향 생성 시 | 역방향 자동 생성 |
    | --- | --- |
    | A -[hasSubSection]-> B | B -[parentSection]-> A |
    | A -[containsTable]-> B | B -[tableInSection]-> A |
    | A -[containsFigure]-> B | B -[figureInSection]-> A |
    | A -[referencesSection]-> B | B -[referencedBySection]-> A |
    | A -[referencesSpec]-> B | (역관계 없음) |
    | A -[hasSection]-> B | B -[belongsToSpec]-> A |
    
    ### 6.2 Neo4j 구현
    
    ```
    // referencesSection 생성 시 referencedBySection 자동 생성
    MATCH (a:Section)-[r:referencesSection]->(b:Section)
    MERGE (b)-[:referencedBySection]->(a)
    
    ```
    
    ---
    
    ## 7. Spec 확장 (Phase-1 연결)
    
    ### 7.1 Spec → Section 연결
    
    Phase-1에서 생성된 Spec 인스턴스에 hasSection 관계 추가:
    
    ```json
    {
      "@id": "spec:38.331-Rel-15",
      "@type": "Spec",
      "specNumber": "38.331",
      "specRelease": "Rel-15",
      "specInRelease": { "@id": "release:Rel_15" },
      "specVersion": "15.30.0",
      "hasSection": [
        { "@id": "section:38.331-Rel-15-1" },
        { "@id": "section:38.331-Rel-15-2" },
        { "@id": "section:38.331-Rel-15-3" },
        { "@id": "section:38.331-Rel-15-4" },
        { "@id": "section:38.331-Rel-15-5" },
        { "@id": "section:38.331-Rel-15-6" },
        { "@id": "section:38.331-Rel-15-7" },
        { "@id": "section:38.331-Rel-15-A" },
        { "@id": "section:38.331-Rel-15-B" }
      ]
    }
    
    ```
    
    > **Spec 노드 속성 소스 매핑**:
    >
    >
    >
    > | 속성 | 소스 | 예시 |
    > | --- | --- | --- |
    > | specNumber | Phase-1에서 생성됨 (기존값 유지) | "38.331" |
    > | specRelease | 디렉토리 release 토큰 | "Rel-15" |
    > | specInRelease | release 노드 IRI (`tdoc:release/Rel_NN`) | release:Rel_15 |
    > | specVersion | cover page에서 추출 (해당 release final, Step 1 §6 규칙) | "15.30.0" |
    > | hasSection | Phase-3 파싱 결과 (본 Step) | section:38.331-Rel-15-1, ... |
    >
    > release-aware 설계에서 Spec 노드는 (specNumber, release) 단위이다. specRelease·specInRelease·specVersion이 Phase-3가 release별 Spec 노드에 설정하는 Data/Object Property이며, specNumber 등 나머지는 Phase-1 값을 유지한다.
    >
    
    ### 7.2 CR → Section 연결 (clausesAffected 활용)
    
    Phase-1 CR의 clausesAffected 속성을 파싱하여 Section 식별:
    
    | clausesAffected | 파싱 결과 | 연결 Section |
    | --- | --- | --- |
    | "5.1.3.2" | [5.1.3.2] | 38.XXX-{release}-5.1.3.2 |
    | "5.1.3.2, 7.4" | [5.1.3.2, 7.4] | 38.XXX-{release}-5.1.3.2, 38.XXX-{release}-7.4 |
    | "10.4C (new)" | [10.4C] | 38.XXX-{release}-10.4C |
    
    **연결 방법**:
    
    - CR의 modifies → Spec에서 specNumber 확인 + CR의 대상 release 확인
    - clausesAffected 파싱하여 sectionNumber 추출
    - sectionId = `{specNumber}-{release}-{sectionNumber}`로 동일 release Section 매칭
    
    **제약사항** (Step 1 참조):
    
    - clausesAffected 커버리지: Appendix A [P3-V05] 참조
    - 나머지 CR은 Spec 레벨까지만 연결 (CR → Spec)
    
    ---
    
    ## 8. 예시 인스턴스
    
    ### 8.1 Section 예시
    
    **최상위 Section (level 1)**:
    
    ```json
    {
      "@type": "Section",
      "sectionId": "38.331-Rel-15-5",
      "sectionNumber": "5",
      "sectionTitle": "RRC procedures",
      "level": 1,
      "isVoid": false,
      "belongsToSpec": { "@id": "spec:38.331-Rel-15" },
      "parentSection": null,
      "hasSubSection": [
        { "@id": "section:38.331-Rel-15-5.1" },
        { "@id": "section:38.331-Rel-15-5.2" }
      ]
    }
    
    ```
    
    **중간 Section (level 3)**:
    
    ```json
    {
      "@type": "Section",
      "sectionId": "38.331-Rel-15-5.3.5",
      "sectionNumber": "5.3.5",
      "sectionTitle": "RRC connection reconfiguration",
      "level": 3,
      "isVoid": false,
      "belongsToSpec": { "@id": "spec:38.331-Rel-15" },
      "parentSection": { "@id": "section:38.331-Rel-15-5.3" },
      "hasSubSection": [
        { "@id": "section:38.331-Rel-15-5.3.5.1" },
        { "@id": "section:38.331-Rel-15-5.3.5.2" }
      ],
      "referencesSection": [
        { "@id": "section:38.321-Rel-15-5.4.3" }
      ],
      "referencedBySection": [
        { "@id": "section:38.331-Rel-15-5.3.6" }
      ],
      "containsTable": [
        { "@id": "table:38.331-Rel-15-T5.3.5-1" }
      ]
    }
    
    ```
    
    **Void Section**:
    
    ```json
    {
      "@type": "Section",
      "sectionId": "38.331-Rel-15-5.1.4",
      "sectionNumber": "5.1.4",
      "sectionTitle": "Reserved",
      "level": 3,
      "isVoid": true,
      "belongsToSpec": { "@id": "spec:38.331-Rel-15" },
      "parentSection": { "@id": "section:38.331-Rel-15-5.1" },
      "hasSubSection": []
    }
    
    ```
    
    **Annex Section**:
    
    ```json
    {
      "@type": "Section",
      "sectionId": "38.331-Rel-15-A",
      "sectionNumber": "A",
      "sectionTitle": "ASN.1 definitions",
      "level": 1,
      "isVoid": false,
      "belongsToSpec": { "@id": "spec:38.331-Rel-15" },
      "parentSection": null,
      "hasSubSection": [
        { "@id": "section:38.331-Rel-15-A.1" },
        { "@id": "section:38.331-Rel-15-A.2" }
      ]
    }
    
    ```
    
    ### 8.2 TSTable 예시
    
    **캡션 있는 Table**:
    
    ```json
    {
      "@type": "TSTable",
      "tableId": "38.331-Rel-15-T5.3.5-1",
      "tableNumber": "5.3.5-1",
      "tableCaption": "RRCReconfiguration message",
      "tableInSection": { "@id": "section:38.331-Rel-15-5.3.5" }
    }
    
    ```
    
    **캡션 없는 Table**:
    
    ```json
    {
      "@type": "TSTable",
      "tableId": "38.321-Rel-15-T5.2.1-3",
      "tableNumber": "5.2.1-3",
      "tableCaption": null,
      "tableInSection": { "@id": "section:38.321-Rel-15-5.2.1" }
    }
    ```
    
    ### 8.3 TSFigure 예시
    
    ```json
    {
      "@type": "TSFigure",
      "figureId": "38.300-Rel-15-F5-1",
      "figureNumber": "5-1",
      "figureCaption": "Overall architecture",
      "figureInSection": { "@id": "section:38.300-Rel-15-5" }
    }
    
    ```
    
    ---
    
    ## 9. 생성 순서
    
    ### 9.1 인스턴스 생성 순서
    
    ```
    [1단계 - 기존 확인]
    Spec 인스턴스 확인 (Phase-1에서 생성됨)
        │
        ▼
    [2단계 - Section 생성]
    최상위 Section 생성 (level 1)
        │
        ├─ belongsToSpec 연결
        │
        ▼
    하위 Section 생성 (level 2~8)
        │
        ├─ parentSection 연결
        ├─ hasSubSection 연결 (역관계)
        │
        ▼
    [3단계 - TSTable/TSFigure 생성]
    TSTable 생성
        │
        ├─ tableInSection 연결
        ├─ containsTable 연결 (역관계)
        │
    TSFigure 생성
        │
        ├─ figureInSection 연결
        ├─ containsFigure 연결 (역관계)
        │
        ▼
    [4단계 - 참조 관계 생성]
    referencesSection 연결
        │
        ├─ referencedBySection 연결 (역관계)
        │
    referencesSpec 연결 (Section→Spec, TS-only 참조)
        │
        ▼
    [5단계 - Spec 확장]
    Spec.hasSection 연결 (level 1 Section만)
    
    ```
    
    ### 9.2 의존성 순서
    
    | 순서 | 클래스 | 의존 대상 |
    | --- | --- | --- |
    | 1 | Spec | 없음 (Phase-1 기존) |
    | 2 | Section (level 1) | Spec |
    | 3 | Section (level 2~8) | Section (상위) |
    | 4 | TSTable | Section |
    | 5 | TSFigure | Section |
    | 6 | referencesSection | Section (전체) |
    | 7 | referencesSpec | Section (전체), Spec (Phase-1) |
    
    ---
    
    ## 10. 검증 규칙
    
    ### 10.1 무결성 검증
    
    | 검증 항목 | 규칙 | 오류 처리 |
    | --- | --- | --- |
    | Section ID 중복 | sectionId 유일 | 오류 로그 + 스킵 |
    | 부모 없음 | level > 1이면 parentSection 필수 | 오류 로그 |
    | Spec 없음 | belongsToSpec 대상 존재 | 오류 로그 |
    | Table/Figure Section 없음 | tableInSection/figureInSection 대상 존재 | 오류 로그 |
    | 자기 참조 | referencesSection 대상 ≠ 자신 | 무시 |
    
    ### 10.2 통계 검증
    
    | 검증 항목 | 기대값 |
    | --- | --- |
    | Section 총 수 | Appendix A [P3-V01] 참조 |
    | TSTable 총 수 | Appendix A [P3-V02] 참조 |
    | TSFigure 총 수 | Appendix A [P3-V03] 참조 |
    | level 1 Section | hasSection 수와 일치 |
    | orphan Section | Appendix A [P3-V04] 참조 |
    
    ### 10.3 계층 일관성 검증
    
    | 규칙 | 검증 방법 |
    | --- | --- |
    | 자식 level = 부모 level + 1 | hasSubSection 관계에서 검증 |
    | level 1 → parentSection = null | level 1 Section 검증 |
    | level 1만 Spec에 연결 | hasSection 대상 검증 |

    ### 10.4 Release Integrity 검증 (release-aware)

    release-키 무결성. `validate_ts_jsonld.py` §10.1b가 R1~R6 전수 검사하며, 1건이라도 위반 시 FAIL(다음 단계 차단).

    | 규칙 | 검증 항목 | 기대값 |
    | --- | --- | --- |
    | R1 | sectionId가 release 토큰(`-Rel-NN-`)을 포함 (형식 준수) | 전수 PASS |
    | R2 | belongsToSpec의 release == sectionId의 release (cross-release 오염 0) | 0 위반 |
    | R3 | belongsToSpec의 specNumber == sectionId의 specNumber | 0 위반 |
    | R4 | cross-release 참조 누출 0 (referencesSection target release == source release) | 0 edge |
    | R5 | Spec 노드 specInRelease(`tdoc:release/Rel_NN`)·specRelease(`Rel-NN`) 정합 | 전수 일치 |
    | R6 (RAN2 고유) | referencesSpec target은 **동일 release** Spec 노드로만 해소 + target Spec 노드 존재 | 0 위반 |
    
    ---
    
    ## 11. 요약
    
    ### 11.1 인스턴스 생성 명세
    
    | 클래스 | ID 패턴 | 데이터 소스 |
    | --- | --- | --- |
    | Section | `{specNumber}-{release}-{sectionNumber}` | TS 헤딩 |
    | TSTable | `{specNumber}-{release}-T{tableNumber}` | TS 테이블 캡션 |
    | TSFigure | `{specNumber}-{release}-F{figureNumber}` | TS 그림 캡션 |
    
    ### 11.2 관계 생성 요약
    
    | 관계 | 소스 | 대상 | 역관계 |
    | --- | --- | --- | --- |
    | belongsToSpec | Section | Spec (Phase-1) | hasSection |
    | hasSection | Spec (Phase-1) | Section | belongsToSpec |
    | hasSubSection | Section | Section | parentSection |
    | parentSection | Section | Section | hasSubSection |
    | referencesSection | Section | Section | referencedBySection |
    | referencedBySection | Section | Section | referencesSection |
    | referencesSpec | Section | Spec | - |
    | containsTable | Section | TSTable | tableInSection |
    | containsFigure | Section | TSFigure | figureInSection |
    | tableInSection | TSTable | Section | containsTable |
    | figureInSection | TSFigure | Section | containsFigure |
    
    ### 11.3 누적 인스턴스 현황
    
    | Phase | 클래스 |
    | --- | --- |
    | Phase-1 | Tdoc, CR, LS, Meeting, Company, Contact, WorkItem, AgendaItem, Release, Spec, WorkingGroup |
    | Phase-2 | Resolution, Agreement, Conclusion, WorkingAssumption, Table |
    | **Phase-3** | **Section, TSTable, TSFigure** |
    
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
    
    ## 2. Entity 클래스 적용 범위 (RAN2)
    
    | Entity 클래스 | 본 RAN item-level 적재 | granularity=section 기존 잔존 | 대표 예시 |
    | --- | --- | --- | --- |
    | `RRCParameter` | ✅ 38.331 RRC ASN.1 IE (≈ 2,280 unique IE from 2,365 chunks) | 0 | CodebookConfig-r16, LTM-Config-r18, BeamFailureRecoveryConfig |
    | `CapabilityItem` | ✅ 38.306 §4.x capability items (≈ 600~1,000 items) | ✅ legacy section-level (Appendix A) | ltm-MCG-IntraFreq-r18, codebookParametersAddition-r16 |
    | `Procedure` | ✅ MAC/RRC procedure (38.321 §5.x, 38.331 §5.3.x) | 0 | BFR Procedure §5.17, LTM Cell Switch §5.18.35 |
    | `PerformanceRequirement` | ❌ | 0 | — |
    | `ConformanceTest` | ❌ | 0 | — |
    | `Feature` | ✅ 22 catalog features (cross-RAN) | — | Rel-18 LTM, TCI Unified |
    
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
    
    ## 12. Phase-3 온톨로지 완료
    
    ## Appendix A: 기준 수치
    
    > 이 테이블이 Spec의 수치 권위 소스이다.
    >
    
    > 수치 변경 시 이 테이블만 수정한다.
    >

    > **🔴 release-aware 전환 중**: 아래 A.1.1 P3-V01~V06은 **재설계 이전 latest-only(spec당 최신 1버전) Neo4j 적재 상태** 수치이다. release-aware 파서가 산출한 신규 baseline(spec×release)은 **A.1.3**에 있으며, Neo4j 재적재(Stage 5)는 완료되었으며(A.1.1 latest-only는 historical 보존, 현 Neo4j 실측은 release-aware-migration/migration_report.json), Qdrant 재적재는 §3.6 게이트로 보류 중이다. 현 시점 §10.2 통계 검증은 `parse_summary_release.json`을 권위로 사용한다.

    ### A.1.1 latest-only 적재 baseline (재설계 이전, 교체 예정)

    | ID | 항목 | 기준값 | 비고 |
    | --- | --- | --- | --- |
    | P3-V01 | Section 총 수 | 3,835 | 14 TS 파싱 결과 (latest-only). Phase 10/11 증분 적재 반영 (이전 3,834, +1) |
    | P3-V02 | TSTable 총 수 | 254 | 14 TS 파싱 결과 |
    | P3-V03 | TSFigure 총 수 | 545 | 14 TS 파싱 결과 |
    | P3-V04 | orphan Section 수 (Section 기준) | 0 | BELONGS_TO_SPEC 누락 0건. **정의**: Spec 노드에 연결되지 않은 Section. CR의 clausesAffected 매칭 실패 건(MODIFIES_SECTION 미생성)은 P3-V05 커버리지로 별도 추적하며 "orphan"에 포함하지 않음. |
    | P3-V05 | clausesAffected 커버리지 | 4,219 / 5,663 (74.5%) | Phase-1 매칭 확장 CR(P4-V04=5,663) 중 MODIFIES_SECTION 관계 있는 CR. Phase-4 구현 후 역측정 (Neo4j 실측, RAN2 전체 CR 34,622 중에서는 12.2%. 이전 4,135 / 5,545 = 74.6%는 집계, P4-V04 분모 변동 반영) |
    | P3-V06 | Resolution→CR 커버리지 | 474 / 3,773 (12.6%) | Resolution 전체(P2 AGR+CON+WA = 3,773) 중 (:Resolution)-[:REFERENCES]->(:CR) 관계 있는 Resolution. Tdoc 전반 참조는 1,643건 (43.5%). Neo4j 재실측 (값 동일) |

    ### A.1.2 v2.0 + v2.1 Ontology classType 분포 (update — Flywheel ⑦)

    Phase-3 TS Structure ontology에 v2.0 + v2.1 6 신규 클래스 추가. RAN2 phase-3 영향 영역:

    | classType | RAN2 분포 | 의미 |
    | --- | --- | --- |
    | `RRCParameter` (v2.0) | 2,255 (`ran2_ts_asn1_chunks`) + 19 capability composite + 727 (`ran2_ts_ie_descriptions`) | 38.331 RRC IE body. Despite name, ontology comment에서 NGAP/XnAP/F1AP/E1AP IE도 포함 (RAN3 적용). |
    | `CapabilityItem` (v2.0) | 1,716 (`ran2_ts_capabilities`) + 210 (38.306 §4.x in `ran2_ts_sections`) | 38.306 UE capability item. Granularity: Per-UE / Per-Band / Per-BC / Per-FeatureSet |
    | `Procedure` (v2.0) | 141 (v1 keyword 116 + v2 pseudo-code 25) | 38.300/305/321/322/323/331/355 procedure sections |
    | `Feature` (v2.0, independent) | 20 nodes in Neo4j RAN2 (cross-RAN, F-1.6 적재) | 3GPP 표준 feature catalog 인스턴스 (Q1-Q4 핵심 17 + 추가 3) |
    | Neo4j RAN2 `:CapabilityItem` label | 97 (BELONGS_TO_SPEC 38.306) | RAN2 Neo4j v2 label 적재 |
    | Neo4j RAN2 `:Feature` nodes | 20 | F-1.6 적재 |

    **관련 ontology TTL**: `ontology/tdoc-ontology.ttl` v2.0 + v2.1
    **관련 SHACL**: `ontology/tdoc-ontology-shapes.ttl` (pyshacl PASS)
    **관련 Feature catalog**: `ontology/config/feature_catalog.yaml` `catalog_version: 1.2-2026-05-19` (20 verified features, Claude self-curation + 100% retrieval cross-check per `validate_feature_catalog.py`)
    **관련 도구**: `scripts/cross-phase/ontology/classify_sections.py` / `classify_procedures.py` / `add_neo4j_section_labels.py` / `load_feature_instances_neo4j.py` / `audit_classtype_coverage.py`

    ### A.1.3 release-aware 파서 baseline (Stage 4 실측 — Neo4j 적재 전)

    > 출처: `scripts/RAN/formal/RAN2/phase-3/ts-parser/parse_ts_docx.py` 실행 산출 `ontology/output/RAN/formal/parsed_ts/RAN2/parse_summary_release.json` + `ts_*_Rel-*.json` 직접 집계. Neo4j/Qdrant 재적재(Stage 5+) 후 A.1.1을 이 값으로 교체.

    | ID | 항목 | 기준값 | 비고 |
    | --- | --- | --- | --- |
    | P3-R01 | spec-release 수 | 59 | 14 distinct spec × release. 분포: Rel-15=9, Rel-16=11, Rel-17=12, Rel-18=13, Rel-19=14 |
    | P3-R02 | distinct spec 수 | 14 | 37.324, 38.300, 38.304~306, 38.314, 38.321~323, 38.331, 38.340, 38.351, 38.355, 38.391 (release별 등장 시점 상이) |
    | P3-R03 | Section 총 수 | 14,397 | 59 spec-release 합산 (release별 Section 노드 분리) |
    | P3-R04 | TSTable 총 수 | 900 | 59 spec-release 합산 |
    | P3-R05 | TSFigure 총 수 | 1,969 | 59 spec-release 합산 |
    | P3-R06 | Void Section 수 | 172 | isVoid=true 합산 |
    | P3-R07 | referencesSection (Section→Section) | 3,747 | 동일 release 내 해소 (cross-release 누출 0, validate R4) |
    | P3-R08 | referencesSpec (Section→Spec, TS-only) | 1,868 | 동일 release Spec 노드로 매핑 (RAN2 고유, validate R6) |
    | P3-R09 | Release Integrity (R1~R6) | PASS | `validate_ts_jsonld.py` §10.1b 전수 PASS, cross-release 누출 0 |

    ### A.2 구현 CQ 검증 결과
    
    > Spec Step 1의 CQ는 온톨로지 **설계 근거**이다.
    아래는 구현에서 사용하는 **검증 CQ**로, 설계 CQ를 포함하되 구현 검증용으로 확장/재구성되었다.
    >
    
    | 항목 | 설계 CQ (Spec) | 검증 CQ (구현) |
    | --- | --- | --- |
    | 개수 | (5그룹) | 41 CQ |
    | 데이터셋 | - | `logs/RAN/formal/RAN2/phase-3/cq_test_dataset.json` |
    | 검증 결과 | - | **41/41 PASS (100%)** — `logs/RAN/formal/RAN2/phase-3/cq_cypher_results.json` 권위 |
