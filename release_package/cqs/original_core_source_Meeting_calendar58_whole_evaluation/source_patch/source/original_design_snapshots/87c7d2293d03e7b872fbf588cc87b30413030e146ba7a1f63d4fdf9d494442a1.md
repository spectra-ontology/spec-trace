- **phase-3: Ontology 101 기반 RF/EMC/RRM 엔지니어 타겟으로 확장 (TS)**
    
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
    
    **3GPP RAN4 Technical Specification(TS) 문서의 구조와 참조 관계**
    
    ### 1.2 For what are we going to use the ontology?
    
    **Phase-1~2 온톨로지를 확장**하여 다음을 지원:
    
    - TS 구조 탐색 — Section 계층 네비게이션
    - TS 간 참조 분석 — 문서 간 참조 관계 파악
    - CR → TS 연결 — CR이 어떤 TS/Section을 수정했는지 추적
    - Resolution → TS 연결 — Resolution이 승인한 CR의 TS 수정 추적
    
    ### 1.3 Who will use and maintain the ontology?
    
    | 사용자 | 핵심 니즈 |
    | --- | --- |
    | **HW/SW 엔지니어** | TS 구조 파악, RF/EMC 시험 스펙 위치 찾기 |
    | **표준화 엔지니어** | CR이 수정한 Section 확인, 시험 요구사항 변경 추적 |
    | **전략/기획** | 기술 트렌드, 특정 주파수 대역/기능 변경 현황 |
    | **IP/특허** | 기술 표준 반영 현황, RF 성능 요구사항 기여 증거 |
    
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
    
    ### 1.6 RAN4 TS 데이터 특성
    
    | 항목 | RAN4 | 비고 |
    | --- | --- | --- |
    | TS 수 | 38.1xx 계열 (Step 3 §1.1 목록 참조) | 파트 번호 TS 포함 |
    | DOCX 파일 수 | 분할 파일 포함 (Step 7 §1.1 목록 참조) | 분할 파일 병합 필수 |
    | 총 Section | Appendix A [P3-V01] 참조 | RF/EMC 시험 세분화 |
    | 최대 TS | **38.133** | RRM 요구사항 |
    | Heading depth | **1~9** | 비표준 추가 |
    | Table 캡션 | Appendix A [P3-V02] 참조 | |
    | Figure 캡션 | Appendix A [P3-V03] 참조 | |
    | Void Section | Appendix A [P3-V07] 참조 | |
    | ASN.1 | **없음** | RF/EMC 도메인 |
    | 분할 파일 | 38.101-1/3/4, 38.133 | Step 7 §1.2 |
    | 비표준 Heading | **Header 5/6/7, H6, Heading 3.xxx** | 소량 |
    | TR 혼재 | **38.173** (제외) | TR Skeleton |
    | 중복 파일 | **38.195** (_cl/_cm) | _cl 사용 |
    
    ---
    
    ## 2. Scope 정의
    
    ### 2.1 포함 (In Scope)
    
    | 구분 | 포함 대상 |
    | --- | --- |
    | **TS 문서** | 38.101-1~5, 38.104, 38.106, 38.108, 38.113, 38.114, 38.115-1/2, 38.124, 38.133, 38.141-1/2, 38.151, 38.161, 38.171, 38.174, 38.175, 38.176-1/2, 38.181, 38.191, 38.194, 38.195, 38.307 (**28 spec**) — release별 데이터 보유 spec도 동일 28 (38.173은 TR이라 제외, §2.2) |
    | **Release 차원 (release-aware)** | 각 TS의 **release별 final 버전** (Rel-15/16/17/18/19). 동일 spec번호라도 release마다 **별개 Spec 노드**이며, sectionId·Spec IRI가 release 키를 포함한다 (예: `38.133-Rel-15-...` ≠ `38.133-Rel-18-...`; 하이픈 spec `38.101-1-Rel-15-...`). spec×release = spec-release 단위로 적재 (모든 spec이 모든 release에 존재하지는 않음 — 다수 RF spec은 Rel-17+ 신규; baseline 수치는 Appendix A.1.3) |
    | **Section 구조** | 본문 + Annex, 9레벨까지 (Heading 8 = Annex) |
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
    | **38.173** (TR38.173 Skeleton) | **TR이므로 Phase-3 (TS) 범위 밖. Phase-5 TR에서 처리** — `data_raw`에 per-release TS 데이터도 없음(legacy `.doc` skeleton만, Phase-0 수집 공백). release-aware는 28 spec 기준 |
    | TS **intra-release** 버전 히스토리 (한 release 내 모든 draft/중간 버전) | 복잡도 증가, 향후 확장. release별 **final 버전 1개**만 적재 (release-aware). 각 release final의 버전값은 Spec 확장의 specVersion에 기록 (Step 5 §4 참조) |
    | **38.195 Presentation** | RP-260419 Presentation 파일. 본문 아님 |
    | **38.195 _cm 파일** | _cl과 동일 내용. _cl 하나만 사용 |
    | **Cover 파일** | 38.101-1/3/4, 38.133 cover 파일. Section 0건 |
    | TS 버전 히스토리 | 복잡도 증가. 단일 버전만 기록 |
    | RAN4 Scope 외 TS | Scope 한정 |
    
    ### 2.3 Graph DB vs Vector DB 경계
    
    | Graph DB (Phase-3) | Vector DB |
    | --- | --- |
    | Section ID, 번호, 제목, 레벨 | Section 본문 텍스트 |
    | Section 계층 관계 | 본문 임베딩 |
    | Table/Figure 메타데이터 | Table 셀 데이터 |
    | TS 간 참조 관계 | 수식 내용 |
    | CR/Resolution 연결 | |
    
    **연결 키**: sectionId (release-aware 예: `38.133-Rel-18-9.2.1`, 하이픈 spec `38.101-1-Rel-15-6.2.4`)
    
    ---
    
    ## 3. 용어 정의
    
    | 용어 | 정의 | 온톨로지 | 예시 |
    | --- | --- | --- | --- |
    | **TS** | Technical Specification 문서 | Spec (Phase-1) | 38.133 |
    | **Spec** | Phase-1 클래스명, TS와 동의어 | Spec | 38.133 |
    | **Section** | TS 내부 계층 구조 (본문 + Annex) | Section (Phase-3) | 5.1.3.2, A.1 |
    | **Clause** | Section의 3GPP 공식 용어 (동의어) | Section | 5.1.3.2 |
    | **Annex** | Section 중 알파벳으로 시작하는 것 | Section | A, A.1, B.2 |
    | **Table** | TS 내 표 | TSTable (Phase-3) | Table 5.1.3.2-1 |
    | **Figure** | TS 내 그림 | TSFigure (Phase-3) | Figure 5-1 |
    
    ### 3.1 용어 구분
    
    | 헷갈리는 것 | 구분 |
    | --- | --- |
    | Spec vs TS | 같음. Spec은 Phase-1 클래스명, TS는 3GPP 공식 용어 |
    | Section vs Clause | 같음. Section은 온톨로지 클래스명, Clause는 3GPP 공식 용어 |
    | Section vs Spec | 다름. Spec은 문서 전체, Section은 문서 내부 구조 |
    | Section vs Annex | Annex ⊂ Section. sectionNumber 패턴으로 구분 (`^[A-Z]` = Annex) |
    
    ### 3.2 RAN4 고유 용어
    
    | 용어 | 설명 | 영향 |
    | --- | --- | --- |
    | **분할 파일** | 대형 TS가 여러 DOCX로 분할 (Step 7 §1.1 참조) | 파싱 시 순서대로 병합 |
    | **파트 번호 TS** | 38.101-1~5 등 하이픈으로 구분된 독립 TS | 각각 별도 Spec 노드 |
    | **Cover 파일** | 표지만 포함된 DOCX (_cover 접미사) | 파싱에서 제외 |
    
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
    | **TS 버전** | release-aware: **release별 final 버전** (Rel-15~19) 각각 별개 Spec 노드. 각 release final 버전을 specVersion에 기록 | release 내 intra-release draft 히스토리는 미지원 |
    | **TS 범위** | RAN4 38.1xx 계열 (Step 3 §1.1 목록 참조) | 38.173 TR 제외 |
    | **분할 파일** | 파트별 순서대로 병합 파싱 | cover 파일 제외 |
    
    > **specVersion·release 추출 규칙 (release-aware)**: Phase-3는 각 spec-release DOCX 파일명/cover에서 release와 버전 코드를 추출하여 release별 Spec 노드의 specVersion 속성에 저장한다. release 자체는 입력 디렉토리 구조 `data/data_raw/RAN/formal/TS/RAN4/{spec}/{release}/`에서 산출하며, release 토큰(`Rel-NN`)은 `specRelease`에, release 노드 IRI는 `specInRelease`에 부착한다.
    >
    > - 파일명 패턴: `{specNumber}-{버전코드}.docx` 
    > - 버전 코드 → 시맨틱 버전 변환: 알파벳(a=10, b=11, ..., j=19, k=20) + 2자리 숫자 → `{major}.{minor}.0` (예: j30 → 19.3.0, j00 → 19.0.0)
    > - 분할 파일 대표 파일: 38.101-1(s00-0504→j40), 38.101-3(s00-05→j40), 38.101-4(s00-05→j10), 38.133(s0-7→j30)
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
    
    **R-J3 Phase-1~2 의존성 CQ별 세분화**:
    
    - CQ1 (Spec → Section 구조 조회), CQ2 (Section → TSTable/TSFigure): Phase-1~2 인스턴스 없어도 동작 가능. 내부적으로 Spec/Section 노드만 사용.
    - CQ3 (CR → modifiesSection → Section): Phase-1 Tdoc·CR 노드 필수, `modifiesSection` 관계는 Phase-4 이후에 생성됨. Phase-4 미적재 상태에서는 "관계 없음" 결과.
    - CQ4 (Resolution → references Tdoc → CR → modifiesSection → Section): Phase-1 Tdoc + Phase-2 Resolution + Phase-4 CR 관계가 모두 필요.
    - 따라서 "Phase-1~2 전체 유지"는 CQ3/CQ4 경로를 보장하기 위한 **최대 보수(safety) 규정**이며, CQ1/CQ2만 사용하는 재현 시나리오에서는 Phase-1~2 부분 적재 또는 skip도 기술적으로 가능하다. 단, 본 spec은 전체 유지를 기본 권장 범위로 유지한다.
    
    ### 1.2 Phase-1 온톨로지
    
    | 항목 | 내용 |
    | --- | --- |
    | 도메인 | 3GPP RAN4 Tdoc 메타데이터 |
    | 데이터 소스 | Tdoc_list (Excel) |
    
    ### 1.3 Phase-2 온톨로지
    
    | 항목 | 내용 |
    | --- | --- |
    | 도메인 | 3GPP RAN4 Final Report Resolution |
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
    | **Resolution** | ✅ CQ4 | |
    | Agreement | ⚪ (Resolution 하위) | 간접 사용 |
    | Conclusion | ⚪ (Resolution 하위) | 간접 사용 |
    | WorkingAssumption | ⚪ (Resolution 하위) | 간접 사용 |
    | Table | ⚪ | 기존 유지 (Phase-3와 별개) |
    
    *참고: RAN4 Phase-2에는 Summary/SessionNotes/Figure/Chart 클래스 없음 (Moderator/수식 0건 등으로 제외)*
    
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
    | **references** | Resolution → Tdoc | ✅ CQ4 | 핵심 경로 |
    | **madeAt** | Resolution → Meeting | ✅ CQ4 | |
    | resolutionBelongsTo | Resolution → AgendaItem | ⚪ | 기존 유지 |
    | hasResolutions | AgendaItem → Resolution | ⚪ | 기존 유지 |
    | hasTable | Resolution → Table | ⚪ | 기존 유지 |
    | containedIn | Table → Meeting | ⚪ | 기존 유지 |
    
    *참고: RAN4 Phase-2에는 moderatedBy 없음 (Summary 미포함)*
    
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
    
    [CQ4 경로: Resolution → CR → TS → Section]
    Resolution -[references]-> CR -[modifies]-> Spec -[hasSection]-> Section
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
    | **Phase-2 (전체 유지)** | Resolution, Agreement, Conclusion, WorkingAssumption, Table |
    | **Phase-3 CQ 직접 사용** | Spec, CR, Meeting, Company, WorkItem, Release, Resolution |
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
    | 문서 | 28개 TS (38.101-1~5, 38.104~38.307) |
    | 형식 | Word 문서 (단일 또는 분할) |
    | 범위 | 본문 + Annex |
    
    ### 1.1 TS 문서 목록
    
    | # | TS | DOCX | 규모 | 비고 |
    | --- | --- | --- | --- | --- |
    | 1 | 38.101-1 | 8파트 | 대형 | UE RF FR1. cover+7파트 |
    | 2 | 38.101-2 | 1 | 중형 | UE RF FR2 |
    | 3 | 38.101-3 | 4파트 | 대형 | UE RF Inter-band. cover+3파트 |
    | 4 | 38.101-4 | 4파트 | 대형 | UE RF Performance. cover+3파트 |
    | 5 | 38.101-5 | 1 | 소형 | UE RF DSS |
    | 6 | 38.104 | 1 | 대형 | BS RF |
    | 7 | 38.106 | 1 | 중형 | BS EMC |
    | 8 | 38.108 | 1 | 소형 | BS-MS System Simulator |
    | 9 | 38.113 | 1 | 소형 | BS EMC |
    | 10 | 38.114 | 1 | 소형 | UE EMC |
    | 11 | 38.115-1 | 1 | 중형 | NR repeater conformance (Part 1) |
    | 12 | 38.115-2 | 1 | 중형 | NR repeater conformance (Part 2) |
    | 13 | 38.124 | 1 | 소형 | EMC for MSR |
    | 14 | 38.133 | 22파트 | **초대형** | RRM Requirements. cover+21파트 |
    | 15 | 38.141-1 | 1 | 대형 | BS conformance FR1 |
    | 16 | 38.141-2 | 1 | 대형 | BS conformance FR2 |
    | 17 | 38.151 | 1 | 중형 | Repeater Requirements |
    | 18 | 38.161 | 1 | 소형 | Smart Repeater Requirements |
    | 19 | 38.171 | 1 | 중형 | UE-NTN Requirements |
    | 20 | 38.174 | 1 | 대형 | IAB Radio |
    | 21 | 38.175 | 1 | 소형 | UE-NTN High Power |
    | 22 | 38.176-1 | 1 | 대형 | BS WPT FR1 |
    | 23 | 38.176-2 | 1 | 대형 | BS WPT FR2 |
    | 24 | 38.181 | 1 | 대형 | RIS Requirements |
    | 25 | 38.191 | 1 | 중형 | Inter-frequency Measurements |
    | 26 | 38.194 | 1 | 소형 | Multi-Antenna Performance |
    | 27 | 38.195 | 1 (_cl만) | 중형 | UE Requirements (_cl/_cm 동일, _cl 사용) |
    | 28 | 38.307 | 1 | 중형 | Requirements on UEs |
    
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
    | **sectionNumber** | Section 번호 | 헤딩 파싱 (예: 5.1.3.2, A.1) | CQ1 |
    | **sectionTitle** | Section 제목 | 헤딩 파싱 | CQ1-9 |
    | **level** | Section 계층 레벨 | 헤딩 스타일에서 추출 | CQ1-4 |
    | **isVoid** | Void 여부 | 본문에 "Void" 텍스트 | CQ1 |
    
    ### 2.3 TSTable/TSFigure 속성 관련
    
    | 용어 | 설명 | 관련 CQ |
    | --- | --- | --- |
    | **tableId** | Table 고유 식별자 | CQ1 |
    | **tableNumber** | Table 번호 (예: 5.1.3.2-1) | CQ1-10 |
    | **tableCaption** | Table 캡션 | CQ1 |
    | **figureId** | Figure 고유 식별자 | CQ1 |
    | **figureNumber** | Figure 번호 (예: 5-1) | CQ1 |
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
    | **TSTable** | TS 내 표 (RF/EMC 측정 요구사항 표) |
    | **TSFigure** | TS 내 그림 (시험 구성도, 블록 다이어그램) |
    
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
    │                    RAN4 TS Ontology (Phase-3)                   │
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
    | Phase-2 | Resolution, Agreement, Conclusion, WorkingAssumption, Table |
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
    | sectionId | String | Section 고유 식별자 | 생성 (예: 38.133-Rel-18-9.2.1, 하이픈 spec 38.101-1-Rel-15-6.2.4) |
    | sectionNumber | String | Section 번호 | 헤딩 파싱 (예: 5.1.3.2, A.1) |
    | sectionTitle | String | Section 제목 | 헤딩 파싱 |
    | level | Integer | Section 계층 레벨 (1~9) | 헤딩 스타일에서 추출 (아래 매핑 참조). Heading 8 → level 1 (Annex 대제목) |
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
    | H6 | 6 | 커스텀 (38.106, 38.133 등) |
    | Heading 8 | 1 | Annex 대제목 |
    | Heading 9 | 2 | Annex 하위 (일부 TS) |
    | Heading 3.Underrubrik2.H3 | 3 | 비표준 (38.101-3, 38.115-2) |
    | Heading 2.Head2A.2 | 2 | 비표준 (38.101-3, 38.133) |
    | Header 5 | 5 | 비표준 (38.101-5) |
    | Header 6 | 6 | 비표준 (38.133) |
    | Header 7 | 7 | 비표준 (38.195) |
    
    **제외 스타일 (Section이 아닌 것):**
    
    | 스타일 | 용도 | 처리 |
    | --- | --- | --- |
    | TH | Table Header | 제외 |
    | TF | Table Footer | 제외 |
    | NO | NOTE 텍스트 | 제외 |
    | B1/B2/B3 | 불릿 리스트 | 제외 |
    | EW/EQ/EX | Equation/Example | 제외 |
    | FP | Figure 문단 | 제외 |
    | toc 1~8 | Table of Contents | 제외 (Heading과 중복) |
    | Normal | 일반 본문 | 제외 |
    | Guidance | TR 전용 | 제외 (38.173 TR 전체 제외) |
    
    ### 1.2 Object Property
    
    | Property | Range | Inverse | Description |
    | --- | --- | --- | --- |
    | belongsToSpec | Spec | hasSection | Section이 속한 TS |
    | hasSubSection | Section | parentSection | 하위 Section (부모→자식) |
    | parentSection | Section | hasSubSection | 상위 Section (자식→부모) |
    | referencesSection | Section | referencedBySection | 참조하는 다른 Section |
    | referencedBySection | Section | referencesSection | 이 Section을 참조하는 Section |
    | referencesSpec | Spec | - | TS-only 참조 (clause 없이 TS 번호만 언급) |
    | containsTable | TSTable | tableInSection | Section에 포함된 Table |
    | containsFigure | TSFigure | figureInSection | Section에 포함된 Figure |
    
    ---
    
    ## 2. TSTable 클래스 속성
    
    ### 2.1 Data Property
    
    | Property | Type | Description | 데이터 소스 |
    | --- | --- | --- | --- |
    | tableId | String | Table 고유 식별자 | 생성 (예: 38.133-Rel-18-T9.2-1) |
    | tableNumber | String | Table 번호 | 캡션 파싱 (예: 5.1.3.2-1) |
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
    | figureId | String | Figure 고유 식별자 | 생성 (예: 38.133-Rel-18-F9.2-1) |
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
    | specInRelease | Release | - | release별 Spec 노드 → 해당 Release 노드 (IRI `tdoc:release/Rel_NN`). cardinality 1, Functional |
    
    **Spec 추가 Data Property (release-aware):**
    
    | Property | Range | Cardinality | Functional | 특성 |
    | --- | --- | --- | --- | --- |
    | specRelease | String | 1 | ✅ | denormalized release 토큰 `Rel-NN` (하이픈, 예: `Rel-15`). `specInRelease`의 비정규화 캐시 |
    | specVersion | String | 0..1 | ❌ | 해당 release의 final 버전 (Phase-1 정의 속성, Phase-3가 채움; 예: Rel-18 → `18.10.0`) |
    
    *참고: release-aware에서 Phase-3는 (specNumber, release)별 Spec 노드를 생성하고, 각 spec-release에서 추출한 release 토큰을 specRelease/specInRelease에, final 버전을 specVersion에 설정한다. specNumber 등 나머지는 Phase-1 값을 유지한다 (추출 규칙: Step 1 §6 참조).*
    
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
    | 4 | level | Section | Integer | 계층 레벨 (1~9) |
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
    | sectionId | String | 1 | ✅ | PK | 패턴: `{specNumber}-{release}-{sectionNumber}` (release 토큰 `-Rel-NN-`. 예 `38.133-Rel-18-9.2.1`, 하이픈 spec `38.101-1-Rel-15-6.2.4`) |
    | sectionNumber | String | 1 | ✅ | 패턴 | 본문: `^[0-9]+(\\.[0-9]+[a-zA-Z]?)*(\\.[A-Z])?$`, Annex: `^[A-Z](\\.[0-9]+)*$` |
    | sectionTitle | String | 1 | ✅ | - | Section 제목 |
    | level | Integer | 1 | ✅ | 범위 | min=1, max=9 (Heading 8 → level 1) |
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
    | tableId | String | 1 | ✅ | PK. 패턴: `{specNumber}-{release}-T{tableNumber}` (예 `38.133-Rel-18-T9.2-1`) |
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
    | figureId | String | 1 | ✅ | PK. 패턴: `{specNumber}-{release}-F{figureNumber}` (예 `38.133-Rel-18-F9.2-1`) |
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
    | hasSection | Spec | Section | 1..* | ❌ | belongsToSpec |

    > **E-4 정책 (hasSection 1..* 제약의 경계 케이스)**:
    > - **Void-only TS 허용**: 모든 Section이 `isVoid=true`인 경우도 `hasSection ≥ 1` 충족(Section 노드가 존재하므로 cardinality 위반 아님). Phase-11 spec §5.5 E-1 엣지와 일관.
    > - **Section 0건 파일 처리**: 38.173(skeleton) 같이 Section을 전혀 파싱하지 못하는 파일은 **Phase-3 KG 적재 대상에서 제외**(Phase-3 README "38.173 제외" 규칙). 따라서 KG에 존재하는 Spec 인스턴스는 모두 `hasSection ≥ 1`을 만족하며, `1..*` 제약은 적재 단계에서 보장된다.
    > - **Presentation-only/단일 Cover 파일**: Section이 추출되지 않는 파일(예: 38.195 일부 변종)은 KG에 Spec 노드를 생성하지 않고 로그만 남긴다. Spec 노드 생성과 Section ≥ 1은 원자적으로 처리.
    
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
    | Section | `{specNumber}-{release}-{sectionNumber}` | 38.133-Rel-18-9.2.1 (하이픈 spec: 38.101-1-Rel-15-6.2.4) |
    | TSTable | `{specNumber}-{release}-T{tableNumber}` | 38.133-Rel-18-T9.2-1 |
    | TSFigure | `{specNumber}-{release}-F{figureNumber}` | 38.133-Rel-18-F9.2-1 |
    
    > 🔴 release-aware: ID에 release 토큰 `-Rel-NN-`이 들어간다. 하이픈 spec번호(`38.101-1`)는 `38.101-1-Rel-15-6.2.4`처럼 spec 하이픈과 release 토큰이 함께 나타나며, release는 `-Rel-NN-` 패턴으로 식별한다 (spec=`38.101-1`, release=`Rel-15`, sectionNumber=`6.2.4`).
    
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
    | 1 | 38.101-1 | 8파트 (38101-1-j40_*) | j40 | 분할. cover 제외 |
    | 2 | 38.101-2 | 38101-2-j30.docx | j30 | |
    | 3 | 38.101-3 | 4파트 (38101-3-j40_*) | j40 | 분할. cover 제외 |
    | 4 | 38.101-4 | 4파트 (38101-4-j10_*) | j10 | 분할. cover 제외 |
    | 5 | 38.101-5 | 38101-5-j30.docx | j30 | |
    | 6 | 38.104 | 38104-j20.docx | j20 | |
    | 7 | 38.106 | 38106-j30.docx | j30 | |
    | 8 | 38.108 | 38108-j30.docx | j30 | |
    | 9 | 38.113 | 38113-j10.docx | j10 | |
    | 10 | 38.114 | 38114-j00.docx | j00 | |
    | 11 | 38.115-1 | 38115-1-j30.docx | j30 | |
    | 12 | 38.115-2 | 38115-2-j10.docx | j10 | |
    | 13 | 38.124 | 38124-j00.docx | j00 | |
    | 14 | 38.133 | 22파트 (38133-j30_*) | j30 | 분할. cover 제외. 초대형 |
    | 15 | 38.141-1 | 38141-1-j30.docx | j30 | |
    | 16 | 38.141-2 | 38141-2-j30.docx | j30 | |
    | 17 | 38.151 | 38151-j00.docx | j00 | |
    | 18 | 38.161 | 38161-j20.docx | j20 | |
    | 19 | 38.171 | 38171-j10.docx | j10 | |
    | 20 | 38.174 | 38174-j20.docx | j20 | |
    | 21 | 38.175 | 38175-j00.docx | j00 | |
    | 22 | 38.176-1 | 38176-1-j20.docx | j20 | |
    | 23 | 38.176-2 | 38176-2-j30.docx | j30 | |
    | 24 | 38.181 | 38181-j20.docx | j20 | |
    | 25 | 38.191 | 38191-j10.docx | j10 | |
    | 26 | 38.194 | 38194-j10.docx | j10 | |
    | 27 | 38.195 | RP-260419 TS 38.195 v1.0.0_cl.docx | v1.0.0 | 특수 파일명. _cl만 사용 |
    | 28 | 38.307 | 38307-j30.docx | j30 | |
    
    **제외 파일:**
    
    | 파일 | 이유 |
    | --- | --- |
    | 38.173 (TR38.173 Skeleton) | TR. Phase-3 범위 밖 |
    | *_cover.docx | 표지만. Section 0건 |
    | 38.195 Presentation | 슬라이드 파일 |
    | 38.195 _cm.docx | _cl과 동일 내용 |
    
    ### 1.2 분할 파일 병합 순서
    
    **38.101-1** (cover 제외, 7파트):
    
    ```
    s00-0504 → s0505-0505A02 → s0505A03-0505A03 → s0505B-0505J → s06-06 → s07-XX → sAnnexes
    ```
    
    **38.101-3** (cover 제외, 3파트):
    
    ```
    s00-05 → s06-XX → sAnnexes
    ```
    
    **38.101-4** (cover 제외, 3파트):
    
    ```
    s00-05 → s06-XX → sAnnexes
    ```
    
    **38.133** (cover 제외, 21파트):
    
    ```
    s0-7 → s8-8 → s9-9 → s10-11 → s12-13
    → sA.1-A.3 → sA.4-A.406 → sA.407-A.5 → sA.6-A.605 → sA.606-A.611
    → sA.7-A.704 → sA.705-A.705 → sA.706-A.711 → sA.8-A.9
    → sA.10-A.10 → sA.11-A.12 → sA.13-A.14 → sA.15-A.16 → sA.17-A.18
    → sA.19-A.XX → sB.1-XX
    ```
    
    ---
    
    ## 2. ID 생성 규칙
    
    | 클래스 | ID 속성 | 패턴 | 예시 |
    | --- | --- | --- | --- |
    | Section | sectionId | `{specNumber}-{release}-{sectionNumber}` | 38.133-Rel-18-9.2.1 (하이픈 spec: 38.101-1-Rel-15-6.2.4) |
    | TSTable | tableId | `{specNumber}-{release}-T{tableNumber}` | 38.133-Rel-18-T9.2-1 |
    | TSFigure | figureId | `{specNumber}-{release}-F{figureNumber}` | 38.133-Rel-18-F9.2-1 |
    
    ---
    
    ## 3. 데이터 소스 매핑
    
    ### 3.1 Section 매핑
    
    | 속성 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | sectionId | 생성 | `{specNumber}-{release}-{sectionNumber}` (release 토큰 `-Rel-NN-`) |
    | release | 입력 디렉토리 | `data/data_raw/RAN/formal/TS/RAN4/{spec}/{release}/`의 release 토큰 (예 `Rel-15`) |
    | sectionNumber | 헤딩 텍스트 | 숫자/문자 패턴 추출 |
    | sectionTitle | 헤딩 텍스트 | sectionNumber 이후 텍스트 |
    | level | 헤딩 스타일 | Step 5 §1.1 매핑 참조 |
    | isVoid | 본문 내용 | "Void" 텍스트만 있으면 true |
    
    ### 3.2 TSTable/TSFigure 매핑
    
    | 속성 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | tableId / figureId | 생성 | `{specNumber}-{release}-T/F{number}` (release 토큰 `-Rel-NN-`) |
    | tableNumber / figureNumber | 캡션 텍스트 | "Table/Figure X.X.X-N:" 패턴에서 추출 |
    | tableCaption / figureCaption | 캡션 텍스트 | "Table/Figure X.X.X-N:" 이후 텍스트 |
    
    ### 3.3 tableNumber/figureNumber → sectionNumber 매핑
    
    | 입력 | 출력 | 규칙 |
    | --- | --- | --- |
    | 5.1.3.2-1 | 5.1.3.2 | 마지막 `-N` 제거 |
    | A.1-1 | A.1 | 마지막 `-N` 제거 |
    | `-` 없음 | 전체를 sectionNumber로 사용 | |
    | 매칭 Section 없음 | 상위 Section 탐색 → 없으면 null | 오류 로그 |
    
    ### 3.4 참조 패턴 (referencesSection)
    
    | 패턴 | 정규식 | 예시 |
    | --- | --- | --- |
    | clause X.X.X | `clause\s+(\d+(?:\.\d+)*)` | "clause 5.1.3" |
    | subclause X.X.X | `subclause\s+(\d+(?:\.\d+)*)` | "subclause 7.4.1.1" |
    | Section X.X.X | `Section\s+(\d+(?:\.\d+)*)` | "Section 5.1.3" |
    | Annex X | `Annex\s+([A-Z](?:\.\d+)*)` | "Annex A.1" |
    | TS 38.XXX clause X.X | `TS\s+38\.(\d{3}(?:-\d)?)\s+clause\s+(\d+(?:\.\d+)*)` | "TS 38.101-1 clause 5.4.3" |
    | TS 38.XXX (TS-only) | `TS\s+38\.(\d{3}(?:-\d)?)` (clause 없음) | "TS 38.104" → referencesSpec |
    
    **참조 대상 결정:**
    
    | 참조 유형 | 대상 결정 |
    | --- | --- |
    | 같은 TS 내 | 현재 specNumber + 추출된 sectionNumber |
    | 다른 TS (clause 있음) | 추출된 specNumber + sectionNumber → referencesSection |
    | 다른 TS (clause 없음) | 추출된 specNumber → referencesSpec. 자기 TS 제외, Scope 내 TS만 |
    | 대상 Section 없음 | 관계 생성 안 함 (로그 기록) |
    | 자기 자신 참조 | 무시 (Irreflexive) |
    
    ---
    
    ## 4. 계층 구조 생성 규칙
    
    ### 4.1 Section 계층 생성
    
    ```
    [파싱 순서]
    1. TS 문서에서 모든 헤딩 추출 (Heading 1~9 + 비표준)
    2. 분할 파일은 병합 순서대로 연결 (Section 번호 연속 보장)
    3. 각 헤딩에서 sectionNumber, sectionTitle, level 추출
    4. level 기반 스택 알고리즘으로 부모-자식 관계 설정
    
    [부모-자식 연결 규칙]
    - 현재 Section의 부모 = 가장 가까운 상위 레벨 Section
    - level 1 Section은 parentSection = null (최상위)
    - level 1 Section만 Spec과 hasSection으로 연결
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
      "specNumber": "38.133",
      "specRelease": "Rel-18",
      "specInRelease": { "@id": "release:Rel_18" },
      "specVersion": "18.10.0",
      "hasSection": [
        { "@id": "section:38.133-Rel-18-1" },
        { "@id": "section:38.133-Rel-18-2" },
        { "@id": "section:38.133-Rel-18-A" }
      ]
    }
    ```
    
    > release-aware: Spec 노드는 (specNumber, release) 단위이며, Phase-3가 release별 Spec 노드에 `specRelease`(`Rel-NN` 토큰)·`specInRelease`(release 노드 IRI `tdoc:release/Rel_NN`)·`specVersion`(해당 release final 버전)을 설정한다. specNumber 등 나머지는 Phase-1 값을 유지한다.
    
    ### 5.2 CR → Section 연결 (clausesAffected 활용)
    
    | clausesAffected | 파싱 결과 | 연결 Section |
    | --- | --- | --- |
    | "5.1.3.2" | [5.1.3.2] | 38.XXX-5.1.3.2 |
    | "5.1.3.2, 7.4" | [5.1.3.2, 7.4] | 38.XXX-5.1.3.2, 38.XXX-7.4 |
    
    ---
    
    ## 6. 예시 인스턴스
    
    ### 6.1 Section 예시 (38.133 Rel-18 — 최상위)
    
    > release-aware: 아래 예시의 sectionId·@id는 release 토큰 `-Rel-18-`을 포함한다. release마다 별개 Spec/Section 노드이다.
    
    ```json
    {
      "@type": "Section",
      "sectionId": "38.133-Rel-18-8",
      "sectionNumber": "8",
      "sectionTitle": "RRM Performance Requirements",
      "level": 1,
      "isVoid": false,
      "belongsToSpec": { "@id": "spec:38.133-Rel-18" },
      "parentSection": null,
      "hasSubSection": [
        { "@id": "section:38.133-Rel-18-8.1" },
        { "@id": "section:38.133-Rel-18-8.2" }
      ]
    }
    ```
    
    ### 6.2 TSTable 예시 (38.104 Rel-17 — BS RF 측정표)
    
    ```json
    {
      "@type": "TSTable",
      "tableId": "38.104-Rel-17-T6.2.1-1",
      "tableNumber": "6.2.1-1",
      "tableCaption": "BS type 1-C operating bands in FR1",
      "tableInSection": { "@id": "section:38.104-Rel-17-6.2.1" }
    }
    ```
    
    ### 6.3 TSFigure 예시 (38.141-2 Rel-18)
    
    ```json
    {
      "@type": "TSFigure",
      "figureId": "38.141-2-Rel-18-F6.2-1",
      "figureNumber": "6.2-1",
      "figureCaption": "Test setup for BS type 1-O",
      "figureInSection": { "@id": "section:38.141-2-Rel-18-6.2" }
    }
    ```
    
    ---
    
    ## 7. 생성 순서
    
    | 순서 | 클래스 | 의존 대상 |
    | --- | --- | --- |
    | 1 | Spec | 없음 (Phase-1 기존) |
    | 2 | Section (level 1) | Spec |
    | 3 | Section (level 2~9) | Section (상위) |
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
    | orphan Section 수 | Appendix A [P3-V04] 참조 (BELONGS_TO_SPEC 전수) |
    | referencesSection 수 | Appendix A [P3-V08] 참조 (Section → Section) |
    | referencesSpec 수 | Appendix A [P3-V09] 참조 (Section → Spec) |
    | 계층 edges | Appendix A [P3-V10] 참조 (PARENT_SECTION = HAS_SUB_SECTION) |
    | hasSection edges | Appendix A [P3-V11] 참조 (Spec → level-1 Section) |
    | BELONGS_TO_SPEC edges | Appendix A [P3-V12] 참조 (Section 전수) |
    | CONTAINS_TABLE edges | Appendix A [P3-V13] 참조 |
    | CONTAINS_FIGURE edges | Appendix A [P3-V14] 참조 |
    | 파서 warnings | Appendix A [P3-V15] 참조 |
    
    ### 8.4 Release Integrity 검증 (release-aware)
    
    release-키 무결성. RAN4는 중간 JSON-LD가 없으므로 `scripts/RAN/formal/RAN4/phase-3/ts-parser/validate_release_integrity.py`가 **파서 JSON**(`ts_{spec}_{release}.json`)에 대해 R1~R6을 전수 검사하며, 1건이라도 위반 시 FAIL(다음 단계 차단). 전수 PASS 실측은 Appendix A.1.3 참조.
    
    | 규칙 | 검증 항목 | 기대값 |
    | --- | --- | --- |
    | R1 | sectionId가 release 토큰(`-Rel-NN-`)을 포함 (형식 준수; 하이픈 spec `38.101-1-Rel-15-...` 포함) | 전수 PASS |
    | R2 | belongsToSpec의 release == sectionId의 release (cross-release 오염 0) | 0 위반 |
    | R3 | belongsToSpec의 specNumber == sectionId의 specNumber | 0 위반 |
    | R4 | cross-release 참조 누출 0 (referencesSection target release == source release) | 0 edge |
    | R5 | Spec 노드 specInRelease(`tdoc:release/Rel_NN`)·specRelease(`Rel-NN`) 정합 | 전수 일치 |
    | R6 (RAN4 referencesSpec 보유) | referencesSpec target은 **동일 release** Spec 노드로만 해소 + target Spec 노드 존재. cross-spec 참조 24건(예 38.101-1→38.101-3)도 전부 동일 release 내 해소 | 0 위반 |
    
    ---
    
    ## 9. RAN4 고유 파싱 규칙
    
    ### 9.1 분할 파일 병합
    
    | 규칙 | 설명 |
    | --- | --- |
    | 파일 정렬 | 파일명의 섹션 범위 접미사 기준 (s00→s06→s07→sAnnexes) |
    | cover 파일 | 무조건 스킵 (_cover 접미사) |
    | Section 연속성 | 파트 간 Section 번호가 연속되어야 함 |
    | 계층 유지 | 스택을 파트 간 유지하여 부모-자식 관계 연속 보장 |
    
    ### 9.2 비표준 Heading 처리
    
    | 스타일 | 처리 | 매핑 level |
    | --- | --- | --- |
    | Header N | Heading N과 동일 처리 | N |
    | H6 | Heading 6과 동일 | 6 |
    | Heading 3.Underrubrik2.H3 | Heading 3과 동일 | 3 |
    | Heading 2.Head2A.2 | Heading 2와 동일 | 2 |
    
    ### 9.3 38.195 특수 처리
    
    | 항목 | 처리 |
    | --- | --- |
    | _cl 파일만 사용 | _cm은 동일 내용이므로 제외 |
    | Presentation 파일 | 제외 (본문 아님) |
    | 버전 추출 | 파일명에서 v1.0.0 직접 추출 (j-코드 아님) |
    
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
    
    ## 2. Entity 클래스 적용 범위 (RAN4)
    
    | Entity 클래스 | 본 RAN item-level 적재 | granularity=section 기존 잔존 | 대표 예시 |
    | --- | --- | --- | --- |
    | `RRCParameter` | ❌ (RAN4 spec body는 perf/test req — IE 없음) | 0 | — |
    | `CapabilityItem` | ❌ | 0 | — |
    | `Procedure` | ❌ (perf req에는 protocol procedure 없음) | 0 | — |
    | `PerformanceRequirement` | ✅ item-level perf req extraction (38.133 §6/§8 등) | ✅ legacy section-level (Appendix A) | TEvaluate_BFD_SSB, DLTM |
    | `ConformanceTest` | ✅ BS conformance (38.141-1/2, 38.181) | ✅ legacy section-level (Appendix A) | BS RF test cases |
    | `Feature` | ✅ 22 catalog features (cross-RAN) | — | BFR perf timing, LTM delay budget |
    
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
    
    > 수치 변경 시 이 테이블만 수정한다.
    
    > **구현 완료 후 실측치로 작성한다.** (구현 전 미측정 껍데기 금지)
    
    > **🔴 release-aware 전환 중**: 아래 A.1.1 P3-V01~V15는 **재설계 이전 latest-only(spec당 최신 1버전) Neo4j 적재 상태** 수치이다. release-aware 파서가 산출한 신규 baseline(spec×release)은 **A.1.3**에 있으며, Neo4j 재적재(Stage 5)는 완료되었으며(A.1.1 latest-only는 historical 보존, 현 Neo4j 실측은 release-aware-migration/migration_report.json), Qdrant 재적재는 §3.6 게이트로 보류 중이다. RAN4는 중간 JSON-LD가 없으므로 현 시점 통계 검증은 `parse_summary_release.json`(파서 JSON 집계)을 권위로 사용한다.
    
    ### A.1.1 latest-only 적재 baseline (재설계 이전, 교체 예정)
    
    | ID | 항목 | 기준값 | 비고 |
    | --- | --- | --- | --- |
    | P3-V01 | Section 총 수 | **23,410** | 28 TS, 실측 (Phase-3~4 backfill 누적 반영) |
    | P3-V02 | TSTable 총 수 | **13,860** | RF/EMC 측정표 |
    | P3-V03 | TSFigure 총 수 | **861** | 시험 구성도 |
    | P3-V04 | orphan Section 수 | **0** | BELONGS_TO_SPEC 23,410 전수 |
    | P3-V05 | clausesAffected 커버리지 | **5,904 / 74,347** (7.94%) | CR 전체 중 clausesAffected 비어있지 않은 CR 수. 분모 74,347 = :CR 라벨 전수 (P1-V02). Phase-3 분석 초기 분모 64,689 → 재적재(+8,181) → backfill(+1,001) 누적 반영. 분자는 텍스트 속성 채워진 CR 한정으로 변동 적음. |
    | P3-V06 | Resolution→CR 커버리지 | **3,166** edges / 1,985 Resolution, 74,347 CR | Resolution REFERENCES CR. 분모 74,347 = P1-V02 갱신 후 수치. |
    | P3-V07 | Void Section 수 | **544** | 전체 Section의 2.32% (분모 갱신: 23,410) |
    | P3-V08 | referencesSection 수 | **10,882** | Section → Section |
    | P3-V09 | referencesSpec 수 | **1,775** | Section → Spec |
    | P3-V10 | 계층 edges | **22,446** | PARENT_SECTION = HAS_SUB_SECTION |
    | P3-V11 | hasSection edges | **964** | Spec → level-1 Section |
    | P3-V12 | BELONGS_TO_SPEC edges | **23,410** | Section 전수 |
    | P3-V13 | CONTAINS_TABLE edges | **13,860** | |
    | P3-V14 | CONTAINS_FIGURE edges | **861** | 전수 매핑 |
    | P3-V15 | 파서 warnings | **118** | 중복/경미, 전부 무해 |
    
    ### A.1.3 release-aware 파서 baseline (Stage 4 실측 — Neo4j 적재 전)
    
    > 출처: `scripts/RAN/formal/RAN4/phase-3/ts-parser/parse_ts_docx.py` 실행 산출 `ontology/output/RAN/formal/parsed_ts/RAN4/parse_summary_release.json` + `ts_*_Rel-*.json` 직접 집계, 무결성은 `validate_release_integrity.py`. RAN4는 중간 JSON-LD가 없어 파서 JSON이 SSoT이다. Neo4j/Qdrant 재적재(Stage 5+) 후 A.1.1을 이 값으로 교체.
    
    | ID | 항목 | 기준값 | 비고 |
    | --- | --- | --- | --- |
    | P3-R01 | spec-release 수 | 106 | 28 distinct spec 참여. release별 spec 수: Rel-15=12, Rel-16=16, Rel-17=25, Rel-18=25, Rel-19=28 (모든 spec이 모든 release에 존재하지는 않음 — 다수 RF spec은 Rel-17+ 신규) |
    | P3-R02 | distinct spec 수 | 28 | scope 29 spec 디렉토리 중 **38.173 제외** — 실제로는 TR이며 `data_raw`에 per-release TS 데이터 없음(legacy `.doc` skeleton만, Phase-0 데이터 수집 공백) |
    | P3-R03 | Section 총 수 | 76,704 | 106 spec-release 합산 (release별 Section 노드 분리) |
    | P3-R04 | TSTable 총 수 | 45,389 | 106 spec-release 합산 |
    | P3-R05 | TSFigure 총 수 | 3,042 | 106 spec-release 합산 |
    | P3-R06 | Void Section 수 | 2,030 | isVoid=true 합산 |
    | P3-R07 | referencesSection (Section→Section) | 34,265 | 동일 release 내 해소 (cross-release 누출 0, validate R4) |
    | P3-R08 | referencesSpec (Section→Spec, TS-only) | 6,376 | 동일 release Spec 노드로 매핑 (RAN4 referencesSpec 보유, validate R6; cross-spec 24건 전부 동일-release 해소) |
    | P3-R09 | Spec 노드 수 | 106 | (specNumber, release) 단위, specInRelease/specRelease 부착 |
    | P3-R10 | Release Integrity (R1~R6) | PASS | `validate_release_integrity.py` 전수 PASS (파서 JSON), cross-release 누출 0, 참조 누수 0 |
    | P3-R11 | 38.133 per-release Section | Rel-15 1,691 / Rel-16 3,960 / Rel-17 6,930 / Rel-18 9,371 / Rel-19 10,936 | Rel-18·Rel-19 각각 21 body docx 파트(+cover) 병합, ID 충돌 0 |
    | P3-R12 | parse warnings | 390 | advisory (비차단) |
    
    ### A.2 구현 CQ 검증 결과
    
    > Spec Step 1의 CQ는 온톨로지 **설계 근거**이다.
    아래는 구현에서 사용하는 **검증 CQ**로, 설계 CQ를 포함하되 구현 검증용으로 확장/재구성되었다.
    
    | 항목 | 설계 CQ (Spec) | 검증 CQ (구현) |
    | --- | --- | --- |
    | 개수 | 5그룹 (CQ1~CQ5) | **41개** |
    | 데이터셋 | - | Phase-3 CQ 데이터셋 |
    | 검증 결과 | - | **41 PASS / 0 WARN / 0 FAIL / 0 ERROR** |
    | 결과 파일 | - | Phase-3 CQ Cypher 결과 |


    ### A.1.2 v2.0 + v2.1 Ontology classType 분포 (update — Flywheel ⑦ 핵심)

    RAN4 phase-3은 v2.1 신규 클래스 **PerformanceRequirement** + **ConformanceTest**의 주력 영역.

    | classType | RAN4 분포 | 의미 |
    | --- | --- | --- |
    | **`PerformanceRequirement` (v2.1)** | **Qdrant 10,760 (`ran4_ts_sections`)** + **Neo4j 15,360** (BELONGS_TO_SPEC) | 38.133 RRM (7,331) + 38.101-1/2/3/4/5 UE RF/EMC (2,905) + 38.104 BS RF (524) |
    | **`ConformanceTest` (v2.1)** | **Qdrant 1,825** + **Neo4j 2,471** | 38.141-1 (599) + 38.141-2 (673) + 38.181 (553) BS conformance test |
    | `Feature` (v2.0) | 20 nodes in Neo4j RAN4 (cross-RAN, F-1.6) | Feature catalog instances |

    **v2.1 신규 클래스 정의**:
    - `tdoc:PerformanceRequirement` (subClassOf Section) — RRM/RF perf req body
    - `tdoc:ConformanceTest` (subClassOf Section) — UE/BS conformance test body (spec body 본질 기준, WG 무관)

    **관련 ontology TTL**: v2.0 + v2.1
    **관련 SHACL**: `ontology/tdoc-ontology-shapes.ttl` (pyshacl PASS)
    **관련 도구**: `scripts/cross-phase/ontology/classify_sections.py` / `audit_classtype_coverage.py` / `add_neo4j_section_labels.py` / `load_feature_instances_neo4j.py`
    **관련 Flywheel 표준**: `docs/autonomous-self-improvement-flywheel/flywheel-process.md`

    ### A.3 변경 이력

    | 날짜 | 변경 내용 |
    | --- | --- |
    | 2026-06-10 | release-aware 전환(비파괴 Stage 4). ID 포맷 `{specNumber}-{release}-{sectionNumber}` (예 `38.133-Rel-18-9.2.1`, 하이픈 spec `38.101-1-Rel-15-6.2.4`, release 토큰 `-Rel-NN-`), tableId/figureId 동일; Spec 노드 = (specNumber, release) + `specInRelease`/`specRelease` 부착 (§2.1, §2.2, Step 5 §4, Step 6 ID 패턴, Step 7 §2/§3.1). 신규 §8.4 Release Integrity R1~R6 — RAN4는 중간 JSON-LD가 없어 `validate_release_integrity.py`가 **파서 JSON**에 대해 검증(전수 PASS). Appendix A를 A.1.1(latest-only, 재설계 이전·교체 예정) + A.1.3(release-aware 파서 baseline)로 분리. scope 29 spec dir 중 38.173은 TR·per-release 데이터 부재로 release-aware에서 제외. Neo4j 재적재(Stage 5)는 완료(A.1.1 latest-only는 historical 보존, 현 실측은 migration_report.json), Qdrant는 §3.6 보류 |
