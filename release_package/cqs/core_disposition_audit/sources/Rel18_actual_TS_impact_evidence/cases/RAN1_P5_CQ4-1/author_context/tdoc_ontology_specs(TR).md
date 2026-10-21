- **phase-5: Ontology 101 기반 HW/SW 엔지니어 타겟으로 확장-3 (TR)**
    
    ## Step 1: Domain과 Scope 결정
    
    > Ontology 101 원칙
    > 
    > 
    > *"We suggest starting the development of an ontology by defining its domain and scope. That is, answer several basic questions: What is the domain that the ontology will cover? For what we are going to use the ontology? For what types of questions the information in the ontology should provide answers? Who will use and maintain the ontology?"*
    > 
    > — Noy & McGuinness, Ontology Development 101
    > 
    
    ---
    
    ### 1. 기본 질문에 대한 답변
    
    ### 1.1 What is the domain?
    
    **3GPP RAN1 Technical Report(TR) 문서의 구조와 TS(Technical Specification)와의 관계**
    
    ### 1.2 For what are we going to use the ontology?
    
    **Phase-1~4 온톨로지를 확장**하여 다음을 지원:
    
    - TR-TS 추적성 — TR 연구 결과가 어떤 TS에 반영되었는가
    - TR 영향 유형 분석 — NewTS, NewSection, ExtendSection 별 분석
    - TR 내용 검색 — Scope, Conclusions 검색
    - Phase 1-4 연계 — Work Item, Company와 TR 연결
    
    ### 1.3 Who will use and maintain the ontology?
    
    | 사용자 | 핵심 니즈 |
    | --- | --- |
    | **표준화 엔지니어** | TR 연구 결과 참조, TS 반영 추적 |
    | **HW/SW 엔지니어** | 특정 기술의 연구 배경 이해 |
    | **전략/기획** | 기술 트렌드 분석, 미래 TS 변경 예측 |
    | **IP/특허** | 기술 기여 증거 (TR Conclusions) |
    
    ### 1.4 데이터 소스
    
    | Phase | 데이터 소스 | 상태 |
    | --- | --- | --- |
    | Phase-1 | Tdoc_list (Excel) | ✅ 구축 완료 |
    | Phase-2 | Final Report (Word) | ✅ 구축 완료 |
    | Phase-3 | TS 문서 (Word, Phase-3 §2 대상 TS 참조) | ✅ 구축 완료 |
    | Phase-4 | CR 문서 본문 (Word) | ✅ 구축 완료 |
    | **Phase-5** | **TR 문서 [P5-V01]개 (Word)** | 🔶 신규 |
    
    ### 1.5 전제 조건
    
    > 본 온톨로지는 Phase-1~4 온톨로지의 확장이다.
    > 
    > - Phase-1~4의 모든 클래스, 관계, 인스턴스는 그대로 유지
    > - Phase-5는 TR 문서 정보를 추가하고 기존 TS/CR 데이터와 연결
    > - 기존 CQ는 모두 답변 가능 유지
    
    ---
    
    ### 2. Scope 정의
    
    ### 2.1 포함 (In Scope)
    
    | 구분 | 포함 대상 | Phase 1-4 대비 |
    | --- | --- | --- |
    | **TR 메타데이터** | TR 번호, 버전, 릴리스, 상태 | **신규** |
    | **TR 핵심 섹션** | Scope 요약, Conclusions 요약 | **신규** |
    | **TR-TS 영향 관계** | ImpactType, 대상 TS/Section | **신규** |
    | **TR 간 참조** | TR이 참조하는 다른 TR | **신규** |
    | **Work Item 연결** | TR ↔ WorkItem | **확장** |
    
    ### 2.2 제외 (Out of Scope)
    
    | 제외 대상 | 이유 |
    | --- | --- |
    | TR 본문 전체 텍스트 | Vector DB 영역 |
    | Evaluation methodology 상세 | Vector DB 영역 |
    | Performance 테이블/수치 | Vector DB 영역 |
    | Annex 상세 내용 | Vector DB 영역 |
    
    ### 2.3 Graph DB vs Vector DB 경계
    
    | Graph DB (Phase-5) | Vector DB |
    | --- | --- |
    | TR 메타데이터 (번호, 버전, 릴리스, 상태) | TR 본문 전체 텍스트 |
    | TR Scope/Conclusions 요약 (1-10문장) | Evaluation/Performance 상세 |
    | TR-TS 영향 관계 | Simulation 결과 수치 |
    | TR 간 참조 관계 | Annex 상세 내용 |
    
    **연결 키**: `trNumber` (예: `38.769`), `specNumber` (예: `38.211`)
    
    **Graph DB 저장 근거:**
    
    - Scope/Conclusions는 1-10문장의 짧은 요약 메타데이터
    - CQ 답변에 직접 노출되는 속성 (Text-to-Cypher 조회 대상)
    - Phase-4 summaryOfChange와 동일한 성격
    
    ---
    
    ### 3. 용어 정의
    
    | 용어 | 정의 | 온톨로지 | 예시 |
    | --- | --- | --- | --- |
    | **TR** | Technical Report (연구 보고서) | TechnicalReport (Phase-5) | 38.769 |
    | **TS** | Technical Specification (기술 사양) | Spec (Phase-1) | 38.211 |
    | **ImpactType** | TR이 TS에 미친 영향 유형 | Enum (Phase-5) | NewTS, NewSection 등 |
    | **TRStatus** | TR의 현재 상태 | Enum (Phase-5) | Draft, Completed, Living |
    
    ### 3.1 용어 구분
    
    | 헷갈리는 것 | 구분 |
    | --- | --- |
    | TR vs TS | TR은 연구 보고서(Informative), TS는 기술 사양(Normative) |
    | Spec vs TS | 같음. Spec은 Phase-1 클래스명, TS는 3GPP 공식 용어  |
    | TR vs Tdoc | 다름. TR은 문서 유형, Tdoc은 회의 기고문 |
    
    ### 3.2 ImpactType 정의
    
    | ImpactType | 설명 | 예시 |
    | --- | --- | --- |
    | **NewTS** | 완전히 새로운 TS 생성 | TR 38.769 → TS 38.291 |
    | **NewSection** | 기존 TS에 새 섹션 추가 | TR 38.885 → Section 8 (Sidelink) |
    | **ExtendSection** | 기존 TS 섹션 확장 | TR 38.843 → Section 5.2 (CSI) |
    | **NoChange** | TS 변경 없음 (참조용/연구만) | TR 38.901 (Channel Model) |
    
    ### 3.3 TRStatus 정의
    
    | TRStatus | 설명 | 예시 |
    | --- | --- | --- |
    | **Draft** | 연구 진행 중 | TR 38.765 (ISAC) |
    | **Completed** | 연구 완료, TS 반영됨 | TR 38.769 (Ambient IoT) |
    | **Living** | 지속 업데이트 (평가용) | TR 38.901 (Channel Model) |
    
    ---
    
    ### 4. Competency Questions
    
    ### CQ1: TR 연구현황분석
    
    | # | Question |
    | --- | --- |
    | 1-1 | 특정 릴리스에서 완료된 TR 목록은? |
    | 1-2 | 특정 TR의 Scope(연구 범위)는? |
    | 1-3 | 특정 TR의 Conclusions(연구 결론)은? |
    | 1-4 | 현재 진행 중(Draft)인 TR 목록은? |
    
    ### CQ2: TS 반영영향추적 ⭐ 핵심
    
    | # | Question |
    | --- | --- |
    | 2-1 | 특정 TR이 영향 준 TS 목록은? |
    | 2-2 | 특정 TR의 ImpactType은? |
    | 2-3 | 새로운 TS를 만든 TR 목록은? (ImpactType = NewTS) |
    | 2-4 | 새 섹션을 추가한 TR 목록은? (ImpactType = NewSection) |
    | 2-5 | 특정 TS에 영향 준 TR 목록은? (역방향) |
    
    > CQ2-6 (특정 TS Section이 어떤 TR에서 유래했는가), CQ2-7 (TS에 반영되지 않은 TR 목록)은 설계 시 후보였으나, impactsSection 커버리지 제약으로 미구현. 향후 확장 대상.
    > 
    
    ### CQ3: 기술별 영향범위
    
    | # | Question |
    | --- | --- |
    | 3-1 | RedCap(Reduced Capability) 연구 TR 38.875가 어떤 TS의 어떤 Section에 영향을 미쳤는가? |
    | 3-2 | LP-WUS(Low-Power Wake-Up Signal) 연구 TR 38.869가 TS 38.211과 38.213에 미친 영향은? |
    | 3-3 | URLLC 연구 TR 38.824가 TS 38.211과 38.214에 미친 영향과 상세 내용은? |
    
    > CQ2의 TR→TS 영향 분석을 **기술 단위로 묶은 시나리오**. 특정 기술 TR이 여러 TS/Section에 미친 영향을 종합 추적한다.
    > 
    
    ### CQ4: 릴리스별 연구영향
    
    | # | Question |
    | --- | --- |
    | 4-1 | Rel-18을 타겟으로 하는 TR 연구 목록과 각 연구가 TS에 미친 영향 유형은? |
    | 4-2 | 6G Radio 연구(TR 38.760-1)의 현재 진행 상태와 연구 범위는? |
    | 4-3 | 52.6GHz~71GHz 주파수 대역 연구 TR 38.808의 연구 결론과 TS 반영 현황은? |
    
    ### CQ5: TR 간 참조관계
    
    | # | Question |
    | --- | --- |
    | 5-1 | 특정 TR이 참조하는 다른 TR 목록은? |
    | 5-2 | 특정 TR을 참조하는 다른 TR 목록은? (역참조) |
    | 5-3 | 가장 많이 참조되는 TR Top N은? |
    
    > referencesTR/referencedByTR 기반. Phase-5.1에서 구현 완료 (Appendix A.3 참조).
    > 
    
    ---
    
    ### 5. CQ 결과 규칙
    
    ### 5.1 정렬 기준 (Default Sort Order)
    
    | CQ 그룹 | Primary Sort | Secondary Sort |
    | --- | --- | --- |
    | CQ1. TR 연구현황분석 | Release DESC | TR 번호 ASC |
    | CQ2. TS 반영영향추적 | ImpactType ASC | TR 번호 ASC |
    | CQ3. 기술별 영향범위 | TR 번호 ASC | Section 번호 ASC |
    | CQ4. 릴리스별 연구영향 | Release DESC | TR 번호 ASC |
    | CQ5. TR 간 참조관계 | 참조 횟수 DESC | TR 번호 ASC |
    
    ### 5.2 결과 개수 (Default Limit)
    
    | CQ 유형 | 기본값 | 적용 CQ |
    | --- | --- | --- |
    | 단일 조회 | 1 | 1-2, 1-3, 2-2 |
    | 목록 조회 | 10 | 1-1, 1-4, 2-1, 2-3, 2-4, 2-5, 3-1, 3-2, 3-3, 4-1, 4-2, 4-3, 5-1, 5-2 |
    | Top N 조회 | 10 | 5-3 |
    
    ---
    
    ### 6. 제약사항
    
    | 항목 | 제약 | 비고 |
    | --- | --- | --- |
    | **TR-TS 영향 관계** | 입력 = legacy hand-curated CSV stopgap (no-human-hand 불변식 이전; SPECTRA-native = LLM corpus-grounded, TSG_RAN 구현) | 주요 TR 매핑 (목록 참조) |
    | **TR 간 참조 관계** | TR References 절에서 파싱 추출 (자동) | referencesTR / referencedByTR |
    | **TR 범위** | RAN1 관련 TR (38.7xx, 38.8xx, 38.9xx) |  |
    | **TR 버전** | 단일 버전 (최신) | 버전 히스토리 미지원 |
    | **TR-WorkItem 연결** | TR Scope에서 추출 | RP-xxxxxx 패턴 |
    
    ---
    
    ### 7. CQ 요약
    
    | CQ 그룹 | 핵심 가치 |
    | --- | --- |
    | CQ1. TR 연구현황분석 | TR 메타데이터 |
    | CQ2. TS 반영영향추적 | **핵심: 연구→사양 추적** |
    | CQ3. 기술별 영향범위 | 특정 기술 TR의 TS/Section 영향 종합 |
    | CQ4. 릴리스별 연구영향 | 릴리스·기술 단위 연구 현황 |
    | CQ5. TR 간 참조관계 | TR 참조 네트워크 |
    
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
    
    ### 1. 재사용 검토 대상
    
    ### 1.1 내부 온톨로지 (Phase 1-4)
    
    | Phase | 핵심 클래스 | Phase-5 연결 가능성 |
    | --- | --- | --- |
    | **Phase-1** | Spec, Meeting, Tdoc, CRPack, CR | ✅ Spec과 연결 (TR→TS) |
    | **Phase-2** | WorkItem, Company | ✅ WorkItem과 연결 (TR↔WI) |
    | **Phase-3** | TSVersion, Section, Paragraph, Table | ✅ Section과 연결 (TR→Section) |
    | **Phase-4** | CRDocument, ChangedSection | △ 간접 연결 (TR→TS→CR) |
    
    ### 1.2 외부 온톨로지
    
    | 온톨로지 | 도메인 | 검토 결과 |
    | --- | --- | --- |
    | Dublin Core | 문서 메타데이터 | △ 일부 참고 가능 (title, identifier, references) |
    | FOAF | 사람/조직 | ✗ Phase-2에서 이미 자체 정의 |
    | SKOS | 용어/개념 체계 | ✗ Phase-5 범위 아님 |
    | BIBO | 서지 정보 | △ 일부 참고 가능 (report, status) |
    
    ---
    
    ### 2. 핵심 검토: Spec vs TechnicalReport
    
    ### 2.1 Phase-1 Spec 클래스 현황
    
    ```
    Spec (Phase-1 정의)
    ├── specNumber: String (예: "38.212")
    └── specVersion: String (선택)
    
    ```
    
    **Phase-1 Spec 특징:**
    
    - 인스턴스 수: (Phase-1 Spec 참조)
    - 용도: CR의 `modifies` 대상 (CR이 수정하는 TS)
    - **specType 속성 없음** (TS/TR 구분 없음)
    
    ### 2.2 TR 전용 속성 분석
    
    | 속성 | TR 필요 | TS 필요 | 설명 |
    | --- | --- | --- | --- |
    | scope | ✅ | ❌ | 연구 범위 요약 |
    | conclusions | ✅ | ❌ | 연구 결론 요약 |
    | trStatus | ✅ | ❌ | Draft, Completed, Living |
    | impactType | ✅ | ❌ | NewTS, NewSection 등 |
    | referencedTRs | ✅ | ❌ | 참조하는 다른 TR |
    
    ### 2.3 결정 옵션 비교
    
    | 옵션 | 설명 | 장점 | 단점 |
    | --- | --- | --- | --- |
    | **A. Spec 확장** | specType 추가, TR 속성도 Spec에 | 단일 클래스 | Spec 비대화, TS에 불필요 속성 |
    | **B. TechnicalReport 신규** | TR 전용 클래스, Spec과 별도 | 관심사 분리 | 클래스 증가 |
    | **C. Spec 상속** | TechnicalReport extends Spec | 공통 속성 재사용 | 복잡성 증가 |
    
    ### 2.4 Ontology 101 원칙 적용
    
    > "Subclasses of a class usually (1) have additional properties that the superclass does not have, or (2) restrictions different from those of the superclass, or (3) participate in different relationships than the superclasses"
    > 
    
    **TR vs TS 비교:**
    
    | 기준 | TR | TS | 다른가? |
    | --- | --- | --- | --- |
    | 추가 속성 | scope, conclusions, trStatus | (없음) | ✅ 다름 |
    | 다른 제약 | Draft/Completed/Living | 버전 기반 | ✅ 다름 |
    | 다른 관계 | IMPACTS→TS, REFERENCES→TR | (CR로부터 수정됨) | ✅ 다름 |
    
    **결론: 옵션 B (TechnicalReport 신규 클래스) 선택**
    
    ### 2.5 specType 추가 여부
    
    **분석:**
    
    - Phase-1 Spec 인스턴스는 CR의 `modifies` 대상
    - CR은 **TS만 수정**함 (TR은 CR로 수정하지 않음)
    - 따라서 Phase-1 Spec = **사실상 TS만 포함**
    
    **결론: specType 추가 불필요**
    
    ---
    
    ### 3. Phase 1-4 재사용 분석
    
    ### 3.1 Spec 클래스 (Phase-1)
    
    ```
    현재 정의:
    ├── specNumber: String (예: "38.211")
    └── specVersion: String
    
    ```
    
    **재사용 결정:**
    
    - Phase-1 Spec 클래스는 **TS 역할 유지**
    - Phase-5 TR은 **별도 TechnicalReport 클래스**로 생성
    - TR→TS 영향 관계는 `TechnicalReport --IMPACTS--> Spec`
    
    ### 3.2 WorkItem 클래스 (Phase-2)
    
    ```
    현재 정의:
    ├── workItemId: String (예: "NR_pos_enh2")
    ├── workItemTitle: String
    └── release: String
    
    ```
    
    **재사용 결정:**
    
    - TR은 Study Item(SI) 또는 Work Item(WI)과 연결됨
    - TR Scope에서 RP-xxxxxx 패턴으로 SI/WI 식별 가능
    - **결정: 기존 WorkItem 클래스 재사용, TR→WorkItem 관계 추가**
    
    ### 3.3 Section 클래스 (Phase-3)
    
    ```
    현재 정의:
    ├── sectionNumber: String (예: "8.1")
    ├── sectionTitle: String
    └── belongs to Spec (via belongsToSpec; hasSection 은 최상위 절만)
    
    ```
    
    **재사용 결정:**
    
    - TR이 특정 TS Section에 영향을 줌 (예: TR 38.885 → Section 8)
    - **결정: 기존 Section 클래스 재사용, TR Impact에서 Section 참조 가능**
    
    ---
    
    ### 4. 재사용 vs 신규 생성 결정
    
    | 요소 | 결정 | 근거 |
    | --- | --- | --- |
    | **TechnicalReport** | 🆕 신규 | TR 전용 속성 필요 (scope, conclusions 등) |
    | **TRStatus** | 🆕 신규 Enum | Draft, Completed, Living |
    | **ImpactType** | 🆕 신규 Enum | NewTS, NewSection, ExtendSection, NoChange |
    | **IMPACTS 관계** | 🆕 신규 | TR→TS 영향 관계 (속성 포함) |
    | **Spec** | ♻️ 재사용 | TR이 영향 주는 TS 대상 (Phase-1 그대로)  |
    | **Section** | ♻️ 재사용 | TR이 영향 주는 Section 대상 |
    | **WorkItem** | ♻️ 재사용 | TR과 연결되는 SI/WI |
    
    ---
    
    ### 5. 클래스 간 관계 설계 (초안)
    
    ```
    [TechnicalReport] --IMPACTS--> [Spec]
                      --IMPACTS_SECTION--> [Section]
                      --REFERENCES_TR--> [TechnicalReport]
                      --RELATED_TO--> [WorkItem]
    
    [Spec] <--IMPACTS-- [TechnicalReport]  (역방향 탐색)
    
    ```
    
    ### 5.1 IMPACTS 관계 속성
    
    | 속성 | 타입 | 설명 |
    | --- | --- | --- |
    | impactType | ImpactType | NewTS, NewSection, ExtendSection, NoChange |
    | affectedSection | String? | 영향받은 섹션 번호 (예: "8", "17") |
    | description | String? | 영향 설명 |
    
    ---
    
    ### 6. 외부 온톨로지 참고 사항
    
    ### 6.1 Dublin Core 참고
    
    | DC 속성 | Phase-5 대응 | 채택 여부 |
    | --- | --- | --- |
    | dc:title | trTitle | ✅ 개념 차용 |
    | dc:identifier | trNumber | ✅ 개념 차용 |
    | dc:date | (version에 포함) | △ |
    | dc:references | referencedTRs | ✅ 개념 차용 |
    
    ### 6.2 BIBO 참고
    
    | BIBO 속성 | Phase-5 대응 | 채택 여부 |
    | --- | --- | --- |
    | bibo:Report | TechnicalReport | ✅ 개념 차용 |
    | bibo:status | trStatus | ✅ 개념 차용 |
    
    **참고만 하고 직접 import하지 않음** — 3GPP 도메인 특화 용어 유지
    
    ---
    
    ### 7. 재사용 요약
    
    | 구분 | 항목 | 출처 |
    | --- | --- | --- |
    | **재사용** | Spec, Section, WorkItem | Phase 1-3 |
    | **신규 생성** | TechnicalReport, TRStatus, ImpactType, IMPACTS | Phase 5 |
    | **개념 차용** | title, identifier, references, status | Dublin Core, BIBO |
    
    ---
    
    ### 8. 핵심 결정 요약
    
    | 질문 | 결정 | 근거 |
    | --- | --- | --- |
    | Spec 클래스를 TR에도 사용? | ❌ 별도 TechnicalReport 클래스 | TR 전용 속성/관계 필요 |
    | specType 속성 추가? | ❌ 불필요 |  Phase-1 Spec = 사실상 TS만 |
    | Spec 클래스 수정? | ❌ 그대로 유지 | Phase-1 정의 유지 |
    
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
    
    ### 1. Step 3 목적
    
    - 도메인에서 나오는 **명사, 동사를 나열**
    - 아직 **클래스/속성 구분 없이** 후보 용어로 정리
    - TR 문서에서 **실제로 추출 가능한지** 확인
    
    ---
    
    ### 2. 데이터 소스
    
    | 항목 | 내용 |
    | --- | --- |
    | 문서 | TR [P5-V01]개 (38.7xx, 38.8xx, 38.9xx) |
    | 형식 | Word 문서 |
    | 범위 | Rel-15 ~ Rel-20 |
    
    ### 2.1 주요 TR 문서 (분석 완료)
    
    | TR | 제목 | Release | ImpactType |
    | --- | --- | --- | --- |
    | 38.769 | Study on Ambient IoT | Rel-19 | NewTS |
    | 38.889 | Study on NR-based access to unlicensed spectrum | Rel-16 | NewTS |
    | 38.885 | Study on NR Vehicle-to-Everything (V2X) | Rel-16 | NewSection |
    | 38.875 | Study on support of reduced capability NR devices | Rel-17 | NewSection |
    | 38.869 | Study on low-power Wake Up Signal and Receiver | Rel-18 | NewSection |
    | 38.843 | Study on Artificial Intelligence (AI)/Machine Learning (ML) | Rel-18 | ExtendSection |
    | 38.857 | Study on NR positioning enhancements | Rel-17 | ExtendSection |
    | 38.840 | Study on UE power saving in NR | Rel-16 | ExtendSection |
    | 38.901 | Study on channel model for frequencies from 0.5 to 100 GHz | Rel-14+ | NoChange |
    | 38.812 | Study on Non-Orthogonal Multiple Access (NOMA) | Rel-16 | NoChange |
    
    > *위 테이블은 주요 10개 예시. 전체 목록은 구현 데이터 참조.*
    
    ---
    
    ### 3. 용어 나열
    
    ### 3.1 클래스 후보
    
    | 용어 | 데이터 소스 | 채울 수 있나? | 비고 |
    | --- | --- | --- | --- |
    | **TechnicalReport** | TR 문서 전체 | ✅ | Phase-5 신규, TR 문서 자체 |
    | **TRImpact** | 분석 결과 | ✅ | Phase-5 신규, TR→TS 영향 관계 (Reification) |
    
    **TRImpact 설명:**
    
    - TR이 TS에 미치는 영향을 표현하는 중간 클래스
    - 관계에 속성(impactType 등)을 붙이기 위한 Reification 패턴
    - Phase 1-4와 일관성 유지 (관계에 직접 속성 붙이지 않음)
    
    ### 3.2 TechnicalReport Data Property 후보
    
    | 용어 | 타입 | 대상 클래스 | 채울 수 있나? | 필수 | 비고 |
    | --- | --- | --- | --- | --- | --- |
    | trNumber | String | TechnicalReport | ✅ | ✅ | 예: "38.769" |
    | trVersion | String | TechnicalReport | ✅ | ✅ | 예: "19.0.0" |
    | trTitle | String | TechnicalReport | ✅ | ✅ | 예: "Study on Ambient IoT" |
    | trStatus | TRStatus | TechnicalReport | ✅ | ✅ | Draft, Completed, Living |
    | scope | String | TechnicalReport | ✅ | ❌ | Scope 섹션 요약 (1~10문장) |
    | conclusions | String | TechnicalReport | ✅ | ❌ | Conclusions 섹션 요약 (1~10문장) |
    | studyItemRpNumber | String | TechnicalReport | △ | ❌ | RP-xxxxxx 패턴 (Study Item RP 번호) |
    | workItemRpNumber | String | TechnicalReport | △ | ❌ | RP-xxxxxx 패턴 (Work Item RP 번호) |
    
    ### 3.3 TRImpact Data Property 후보
    
    | 용어 | 타입 | 대상 클래스 | 채울 수 있나? | 필수 | 비고 |
    | --- | --- | --- | --- | --- | --- |
    | trImpactId | String | TRImpact | ✅ | ✅ | TRImpact 고유 식별자 |
    | impactType | ImpactType | TRImpact | ✅ | ✅ | NewTS, NewSection, ExtendSection, NoChange |
    | affectedSection | String | TRImpact | ✅ | ❌ | 영향받은 섹션 번호 텍스트 (예: "8", "17") |
    | impactDescription | String | TRImpact | ✅ | ❌ | 영향 설명 |
    
    ### 3.4 Object Property 후보
    
    **TechnicalReport 관련:**
    
    | 용어 | Domain | Range | Inverse | 채울 수 있나? | 비고 |
    | --- | --- | --- | --- | --- | --- |
    | hasTRImpact | TR | TRImpact | impactOfTR | ✅ | TR이 가진 영향 관계 |
    | referencesTR | TR | TR | referencedByTR | ✅ | 참조하는 다른 TR |
    | referencedByTR | TR | TR | referencesTR | ✅ | 참조받는 TR (역관계) |
    | relatedToWorkItem | TR | WorkItem | hasRelatedTR | △ | TR과 연결된 WI |
    | targetRelease | TR | Release | - | ✅ | Phase-1 최초 선언, Phase-5 도메인 확장 (TR 추가) |
    
    **TRImpact 관련:**
    
    | 용어 | Domain | Range | Inverse | 채울 수 있나? | 비고 |
    | --- | --- | --- | --- | --- | --- |
    | impactOfTR | TRImpact | TR | hasTRImpact | ✅ | 이 Impact의 소스 TR (역관계) |
    | impactsSpec | TRImpact | Spec | specImpactedBy | ✅ | 영향받는 TS |
    | specImpactedBy | Spec | TRImpact | impactsSpec | ✅ | TS가 받은 영향 (역관계) |
    | impactsSection | TRImpact | Section | sectionImpactedBy | ✅ | 영향받는 Section (선택) |
    
    **WorkItem 역관계:**
    
    | 용어 | Domain | Range | Inverse | 채울 수 있나? | 비고 |
    | --- | --- | --- | --- | --- | --- |
    | hasRelatedTR | WorkItem | TR | relatedToWorkItem | △ | WI와 연결된 TR (역관계) |
    
    **Section 역관계:**
    
    | 용어 | Domain | Range | Inverse | 채울 수 있나? | 비고 |
    | --- | --- | --- | --- | --- | --- |
    | sectionImpactedBy | Section | TRImpact | impactsSection | ✅ | Section이 받은 영향 (역관계) |
    
    ### 3.5 Enum 후보
    
    **TRStatus:**
    
    | 값 | 정의 | 예시 TR |
    | --- | --- | --- |
    | Draft | 연구 진행 중 | 38.765 (ISAC) |
    | Completed | 연구 완료, TS 반영됨 | 38.769 (Ambient IoT) |
    | Living | 지속 업데이트 (평가용) | 38.901 (Channel Model) |
    
    **ImpactType:**
    
    | 값 | 정의 | 예시 TR |
    | --- | --- | --- |
    | NewTS | 완전히 새로운 TS 생성 | 38.769 → 38.291 |
    | NewSection | 기존 TS에 새 섹션 추가 | 38.885 → Section 8 |
    | ExtendSection | 기존 TS 섹션 확장 | 38.843 → Section 5.2 |
    | NoChange | TS 변경 없음 (참조용) | 38.901, 38.812 |
    
    ---
    
    ### 4. 재사용 클래스 (Phase 1-3)
    
    | 용어 | 출처 | Phase-5 용도 | 연결 관계 |
    | --- | --- | --- | --- |
    | Spec | Phase-1 | impactsSpec 대상 (TS) | TRImpact --impactsSpec--> Spec |
    | Section | Phase-3 | impactsSection 대상 | TRImpact --impactsSection--> Section |
    | WorkItem | Phase-2 | relatedToWorkItem 대상 | TR --relatedToWorkItem--> WorkItem |
    | Release | Phase-1 | targetRelease 대상 | TR --targetRelease--> Release |
    
    ---
    
    ### 5. CQ별 필요 용어 매핑
    
    ### CQ1: TR 기본 검색
    
    | CQ | Question | 필요 용어 |
    | --- | --- | --- |
    | 1-1 | 특정 릴리스에서 완료된 TR 목록은? | TechnicalReport, targetRelease, trStatus |
    | 1-2 | 특정 TR의 Scope는? | TechnicalReport, trNumber, scope |
    | 1-3 | 특정 TR의 Conclusions는? | TechnicalReport, trNumber, conclusions |
    | 1-4 | 현재 진행 중(Draft)인 TR 목록은? | TechnicalReport, trStatus |
    
    ### CQ2: TR-TS 영향 분석
    
    | CQ | Question | 필요 용어 |
    | --- | --- | --- |
    | 2-1 | 특정 TR이 영향 준 TS 목록은? | TR, **hasTRImpact**, **TRImpact**, **impactsSpec**, Spec |
    | 2-2 | 특정 TR의 ImpactType은? | TR, hasTRImpact, TRImpact, **impactType** |
    | 2-3 | 새로운 TS를 만든 TR 목록은? | TR, hasTRImpact, TRImpact, impactType (=NewTS) |
    | 2-4 | 새 섹션을 추가한 TR 목록은? | TR, hasTRImpact, TRImpact, impactType (=NewSection) |
    | 2-5 | 특정 TS에 영향 준 TR 목록은? | Spec, **specImpactedBy**, TRImpact, **impactOfTR**, TR |
    | 2-6 | 특정 Section이 어떤 TR에서 유래? | Section, **sectionImpactedBy**, TRImpact, impactOfTR, TR |
    | 2-7 | TS에 반영되지 않은 TR 목록은? | TR, trStatus, hasTRImpact, TRImpact, impactType |
    
    ### CQ3: 기술별 영향범위
    
    | CQ | Question | 필요 용어 |
    | --- | --- | --- |
    | 3-1 | RedCap 연구 TR 38.875가 어떤 TS의 어떤 Section에 영향을 미쳤는가? | TechnicalReport, **hasTRImpact**, TRImpact, **impactsSpec**, Spec, **impactsSection**, Section |
    | 3-2 | LP-WUS 연구 TR 38.869가 TS 38.211과 38.213에 미친 영향은? | TechnicalReport, hasTRImpact, TRImpact, impactsSpec, Spec, **impactType** |
    | 3-3 | URLLC 연구 TR 38.824가 TS 38.211과 38.214에 미친 영향과 상세 내용은? | TechnicalReport, hasTRImpact, TRImpact, impactsSpec, Spec, impactsSection, Section, **impactDescription** |
    
    ### CQ4: 릴리스별 연구영향
    
    | CQ | Question | 필요 용어 |
    | --- | --- | --- |
    | 4-1 | Rel-18을 타겟으로 하는 TR 연구 목록과 각 연구가 TS에 미친 영향 유형은? | TechnicalReport, **targetRelease**, Release, hasTRImpact, TRImpact, impactType |
    | 4-2 | 6G Radio 연구(TR 38.760-1)의 현재 진행 상태와 연구 범위는? | TechnicalReport, trNumber, **trStatus**, **scope** |
    | 4-3 | 52.6GHz~71GHz 주파수 대역 연구 TR 38.808의 연구 결론과 TS 반영 현황은? | TechnicalReport, trNumber, **conclusions**, hasTRImpact, TRImpact, impactsSpec, Spec |
    
    ### CQ5: TR 간 참조관계
    
    | CQ | Question | 필요 용어 |
    | --- | --- | --- |
    | 5-1 | 특정 TR이 참조하는 다른 TR 목록은? | TechnicalReport, **referencesTR** |
    | 5-2 | 특정 TR을 참조하는 다른 TR 목록은? | TechnicalReport, **referencedByTR** |
    | 5-3 | 가장 많이 참조되는 TR Top N은? | TechnicalReport, referencedByTR (count) |
    
    ---
    
    ### 6. 용어 목록 요약
    
    | 구분 | 내용 |
    | --- | --- |
    | 클래스 후보 (신규) | TechnicalReport, TRImpact |
    | Data Property 후보 | §3.2 (TR), §3.3 (TRImpact) 목록 참조 |
    | Object Property 후보 | §3.4 (신규·도메인 확장·역관계) 목록 참조 |
    | Enum 후보 | TRStatus, ImpactType (§3.5 값 목록 참조) |
    | 재사용 클래스 | Spec, Section, WorkItem, Release |
    
    ---
    
    ### 7. Inverse Property 정리
    
    | 정방향 | 역방향 | Domain ↔ Range |
    | --- | --- | --- |
    | hasTRImpact | impactOfTR | TR ↔ TRImpact |
    | impactsSpec | specImpactedBy | TRImpact ↔ Spec |
    | impactsSection | sectionImpactedBy | TRImpact ↔ Section |
    | referencesTR | referencedByTR | TR ↔ TR |
    | relatedToWorkItem | hasRelatedTR | TR ↔ WorkItem |
    
    ---
    
    ### 8. 검증
    
    | 검증 항목 | 결과 | 비고 |
    | --- | --- | --- |
    | 모든 CQ가 나열된 용어로 답변 가능? | ✅ | CQ 모두 커버 |
    | 역관계가 필요한 CQ에 역관계 존재? | ✅ | CQ 2-5, 2-6, 3-2, 4-1 |
    | TR 문서에서 추출 가능? | ✅ | 영향관계 입력은 현재 legacy CSV stopgap |
    | Step 1 Scope 내? | ✅ | Out of Scope 용어 없음 |
    | Step 2 결정과 일관성? | ✅ | TechnicalReport 신규, Spec 재사용 |
    | Phase 1-4와 일관성? | ✅ | 관계에 속성 직접 붙이지 않음 (Reification) |
    
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
    
    ### 1. Step 4 목적
    
    - Step 3에서 나열한 용어 중 **클래스를 확정**
    - **is-a (상속) 관계**로 계층 구조 정의
    - 속성(Property) 정의는 Step 5에서 진행
    
    ---
    
    ### 2. 클래스 판단 기준
    
    | 질문 | 클래스 여부 |
    | --- | --- |
    | 여러 개의 인스턴스를 가질 수 있는가? | ✅ 클래스 |
    | 독립적으로 존재하는 객체인가? | ✅ 클래스 |
    | 다른 객체의 속성/값인가? | ❌ Property |
    
    ---
    
    ### 3. Step 3 용어 → 클래스 판단
    
    ### 3.1 클래스 후보 판단
    
    | 용어 | 여러 인스턴스? | 독립 객체? | 클래스 여부 | 비고 |
    | --- | --- | --- | --- | --- |
    | **TechnicalReport** | ✅ ([P5-V01]개) | ✅ | ✅ 클래스 | Phase-5 신규 |
    | **TRImpact** | ✅ ([P5-V02]) | ✅ | ✅ 클래스 | Phase-5 신규 (Reification) |
    
    ### 3.2 Data Property 후보 판단
    
    | 용어 | 클래스 여부 | 처리 |
    | --- | --- | --- |
    | trNumber, trVersion, trTitle | ❌ | Step 5 Data Property (TR) |
    | trStatus | ❌ | Step 5 Data Property (TR, Enum 값) |
    | scope, conclusions | ❌ | Step 5 Data Property (TR) |
    | studyItemRpNumber, workItemRpNumber | ❌ | Step 5 Data Property (TR) |
    | impactType | ❌ | Step 5 Data Property (TRImpact, Enum 값) |
    | affectedSection, impactDescription | ❌ | Step 5 Data Property (TRImpact) |
    
    ### 3.3 Object Property 후보 판단
    
    | 용어 | 클래스 여부 | 처리 |
    | --- | --- | --- |
    | hasTRImpact, impactOfTR | ❌ | Step 5 Object Property |
    | impactsSpec, specImpactedBy | ❌ | Step 5 Object Property |
    | impactsSection, sectionImpactedBy | ❌ | Step 5 Object Property |
    | referencesTR, referencedByTR | ❌ | Step 5 Object Property |
    | relatedToWorkItem, hasRelatedTR | ❌ | Step 5 Object Property |
    | targetRelease | ❌ | Step 5 Object Property |
    
    ### 3.4 Enum 후보 판단
    
    | 용어 | 클래스 여부 | 처리 |
    | --- | --- | --- |
    | TRStatus | ❌ | Step 6 Enum 정의 |
    | ImpactType | ❌ | Step 6 Enum 정의 |
    
    ### 3.5 재사용 클래스 (Phase 1-3)
    
    | 용어 | 출처 | Phase-5 역할 |
    | --- | --- | --- |
    | Spec | Phase-1 | impactsSpec 대상 (TS) |
    | Section | Phase-3 | impactsSection 대상 |
    | WorkItem | Phase-2 | relatedToWorkItem 대상 |
    | Release | Phase-1 | targetRelease 대상 |
    
    ---
    
    ### 4. Phase-5 신규 클래스
    
    ### 4.1 TechnicalReport 클래스
    
    | 항목 | 내용 |
    | --- | --- |
    | **정의** | 3GPP Technical Report (연구 보고서) |
    | **상위 클래스** | 없음 (독립) |
    | **하위 클래스** | 없음 |
    | **인스턴스 수** | [P5-V01]개 (38.7xx, 38.8xx, 38.9xx) |
    | **식별자** | trNumber (예: "38.769") |
    
    ### 4.2 TRImpact 클래스
    
    | 항목 | 내용 |
    | --- | --- |
    | **정의** | TR이 TS/Section에 미치는 영향 관계 (Reification) |
    | **상위 클래스** | 없음 (독립) |
    | **하위 클래스** | 없음 |
    | **인스턴스 수** | [P5-V02] (TR당 다수 가능, 미생성 가능) |
    | **식별자** | 복합키 (trNumber + specNumber) 또는 자동 생성 |
    
    **TRImpact 도입 이유:**
    
    1. **Phase 1-4 일관성**: 관계에 직접 속성을 붙이지 않음
    2. **OWL/RDF 호환성**: Reification 패턴 적용
    3. **확장성**: 향후 속성 추가 용이
    
    ---
    
    ### 5. 계층 구조 검토
    
    ### 5.1 TechnicalReport 하위 클래스 필요성 검토
    
    | 후보 | 추가 속성? | 다른 제약? | 다른 관계? | 하위 클래스? |
    | --- | --- | --- | --- | --- |
    | StudyItem TR | ❌ 동일 | ❌ 동일 | ❌ 동일 | ❌ 불필요 |
    | WorkItem TR | ❌ 동일 | ❌ 동일 | ❌ 동일 | ❌ 불필요 |
    | Channel Model TR | ❌ 동일 | ❌ 동일 | ❌ 동일 | ❌ 불필요 |
    
    **결론:** TechnicalReport 하위 클래스 불필요. `trStatus`와 `impactType`으로 구분 가능.
    
    ### 5.2 TRImpact 하위 클래스 필요성 검토
    
    | 후보 | 추가 속성? | 다른 제약? | 다른 관계? | 하위 클래스? |
    | --- | --- | --- | --- | --- |
    | NewTSImpact | ❌ 동일 | ❌ 동일 | ❌ 동일 | ❌ 불필요 |
    | NewSectionImpact | ❌ 동일 | ❌ 동일 | ❌ 동일 | ❌ 불필요 |
    
    **결론:** TRImpact 하위 클래스 불필요. `impactType` Enum으로 구분.
    
    ### 5.3 TechnicalReport vs Spec 관계 재확인
    
    **Step 2 결정:**
    
    | 기준 | TechnicalReport | Spec (TS) |
    | --- | --- | --- |
    | 추가 속성 | scope, conclusions, trStatus | (없음) |
    | 다른 제약 | Draft/Completed/Living | 버전 기반 |
    | 다른 관계 | hasTRImpact, referencesTR | CR로부터 수정됨 |
    
    **결론:** TechnicalReport는 Spec의 하위 클래스가 **아님** (별도 독립 클래스)
    
    ### 5.4 공통 상위 클래스 검토
    
    | 후보 | TR 속성 | Spec 속성 | 공통? | 상위 클래스? |
    | --- | --- | --- | --- | --- |
    | Document | trNumber, trVersion | specNumber, specVersion | △ 유사 | ❌ 불필요 |
    
    **Ontology 101 원칙:**
    
    > "불필요한 클래스를 만들지 말라"
    > 
    
    **결론:** 공통 상위 클래스(Document) 불필요. 독립 클래스 유지.
    
    ---
    
    ### 6. 클래스 다이어그램
    
    ```
    ┌─────────────────────────────────────────────────────────────────┐
    │                        Phase-5 신규 클래스                        │
    └─────────────────────────────────────────────────────────────────┘
    
    [TechnicalReport]                              [TRImpact]
    │                                              │
    │ hasTRImpact (1..*)                          │ impactOfTR (1)
    └──────────────────────▶◀──────────────────────┘
                            │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        │ impactsSpec (1)      │ impactsSection (0..1)│
        ▼                      ▼                      │
      [Spec]               [Section]                      │
      (Phase-1)              (Phase-3)                     │
                            │
    Data Properties:       │
    ├── impactType         │
    ├── affectedSection    │
    └── impactDescription  │
    
    ┌─────────────────────────────────────────────────────────────────┐
    │                     TR 간 참조 관계                              │
    └─────────────────────────────────────────────────────────────────┘
    
    [TechnicalReport] ──referencesTR──▶ [TechnicalReport]
                      ◀──referencedByTR──
    
    ┌─────────────────────────────────────────────────────────────────┐
    │                   Phase 1-2 클래스 연결                          │
    └─────────────────────────────────────────────────────────────────┘
    
    [TechnicalReport] ──relatedToWorkItem──▶ [WorkItem]
                      ◀──hasRelatedTR────────  (Phase-2)
    
    [TechnicalReport] ──targetRelease──▶ [Release]
                                          (Phase-1)
    ```
    
    ---
    
    ### 7. 클래스 상세 정의
    
    ### 7.1 TechnicalReport
    
    | 항목 | 내용 |
    | --- | --- |
    | **클래스명** | TechnicalReport |
    | **정의** | 3GPP RAN1 Technical Report (연구 보고서) |
    | **상위 클래스** | 없음 |
    | **하위 클래스** | 없음 |
    | **식별자** | trNumber |
    | **인스턴스 예시** | TR 38.769, TR 38.885, TR 38.901 |
    
    ### 7.2 TRImpact
    
    | 항목 | 내용 |
    | --- | --- |
    | **클래스명** | TRImpact |
    | **정의** | TR이 TS/Section에 미치는 영향 관계 |
    | **상위 클래스** | 없음 |
    | **하위 클래스** | 없음 |
    | **식별자** | trImpactId (자동 생성 또는 복합키) |
    | **인스턴스 예시** | "38.769→38.291 (NewTS)", "38.885→38.211-Section8 (NewSection)" |
    
    ---
    
    ### 8. 클래스 요약
    
    ### 8.1 Phase-5 신규 클래스
    
    | 클래스 | 상속 | 인스턴스 수 | 설명 |
    | --- | --- | --- | --- |
    | **TechnicalReport** | 없음 (독립) | [P5-V01]개 | 3GPP TR 문서 |
    | **TRImpact** | 없음 (독립) | [P5-V02] | TR→TS 영향 관계 (Reification) |
    
    ### 8.2 클래스로 정의하지 않은 용어
    
    | 용어 | 이유 | 처리 |
    | --- | --- | --- |
    | trNumber, trVersion, trTitle 등 | 속성값 | Step 5 Data Property |
    | impactType, affectedSection 등 | 속성값 | Step 5 Data Property |
    | TRStatus, ImpactType | Enum 값 | Step 6 Enum 정의 |
    | hasTRImpact, referencesTR 등 | 관계 | Step 5 Object Property |
    
    ### 8.3 누적 클래스 현황
    
    | Phase | 클래스 |
    | --- | --- |
    | Phase-1 | Tdoc, CR, LS, Meeting, Company, Contact, WorkItem, AgendaItem, Release, Spec, WorkingGroup |
    | Phase-2 | Resolution, Agreement, Conclusion, WorkingAssumption, Summary, SessionNotes, Figure, Table, Chart |
    | Phase-3 | Section, TSTable, TSFigure |
    | Phase-4 | CRPack |
    | **Phase-5** | **TechnicalReport, TRImpact** |
    
    ---
    
    ### 9. 검증
    
    | 검증 항목 | 결과 | 비고 |
    | --- | --- | --- |
    | 모든 CQ가 정의된 클래스로 답변 가능? | ✅ | TR, TRImpact + 재사용 4개 |
    | 불필요한 클래스 생성 안 함? | ✅ | 하위 클래스/공통 상위 클래스 불필요 |
    | Step 2 결정과 일관성? | ✅ | TechnicalReport 신규, Spec 재사용 |
    | Step 3 용어 모두 처리? | ✅ | 클래스, 나머지 Property/Enum |
    | Phase 1-4 패턴과 일관성? | ✅ | Reification으로 관계 속성 처리 |
    
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
    
    ### 1. Step 5 목적
    
    - Step 4에서 정의한 클래스의 **속성(Slot)** 정의
    - **Data Property**: 클래스 인스턴스의 값 (String, Integer, Boolean 등)
    - **Object Property**: 클래스 인스턴스 간의 관계
    - **Inverse Property**: 역관계 명시
    - 제약조건(Cardinality 등)은 Step 6에서 정의
    
    ---
    
    ### 2. 속성의 종류
    
    | 종류 | 설명 | 예시 |
    | --- | --- | --- |
    | **Data Property** | 객체의 속성값 | trNumber, impactType |
    | **Object Property** | 다른 객체와의 관계 | hasTRImpact, impactsSpec |
    | **Inverse Property** | 역방향 관계 | hasTRImpact ↔ impactOfTR |
    
    ---
    
    ### 3. TechnicalReport 클래스 속성
    
    ### 3.1 Data Property
    
    | Property | Type | Description | 데이터 소스 |
    | --- | --- | --- | --- |
    | trNumber | String | TR 고유 번호 | TR 문서 번호 (예: "38.769") |
    | trVersion | String | TR 버전 | TR 문서 버전 (예: "19.0.0") |
    | trTitle | String | TR 제목 | TR 문서 제목 |
    | trStatus | TRStatus | TR 상태 | Draft, Completed, Living |
    | scope | String | 연구 범위 요약 | Scope 섹션 (1~10문장) |
    | conclusions | String | 연구 결론 요약 | Conclusions 섹션 (1~10문장) |
    | studyItemRpNumber | String | Study Item RP 번호 | RP-xxxxxx 패턴 |
    | workItemRpNumber | String | Work Item RP 번호 | RP-xxxxxx 패턴 |
    
    ### 3.2 Object Property (신규 + 도메인 확장)
    
    | Property | Range | Inverse | Description |
    | --- | --- | --- | --- |
    | hasTRImpact | TRImpact | impactOfTR | TR이 가진 영향 관계 |
    | referencesTR | TechnicalReport | referencedByTR | 참조하는 다른 TR |
    | referencedByTR | TechnicalReport | referencesTR | 이 TR을 참조하는 TR (역관계) |
    | relatedToWorkItem | WorkItem | hasRelatedTR | TR과 연결된 Work Item |
    | targetRelease | Release | - | Phase-1 최초 선언, Phase-5 도메인 확장 (TR 추가) |
    
    ---
    
    ### 4. TRImpact 클래스 속성
    
    ### 4.1 Data Property
    
    | Property | Type | Description | 데이터 소스 |
    | --- | --- | --- | --- |
    | trImpactId | String | TRImpact 고유 식별자 | 생성 (예: "38.769-38.291") |
    | impactType | ImpactType | 영향 유형 | NewTS, NewSection, ExtendSection, NoChange |
    | affectedSection | String | 영향받은 섹션 번호 텍스트 | 예: "8", "17", "5.2" |
    | impactDescription | String | 영향 설명 | 분석 결과 |
    
    **trImpactId 생성 규칙:**
    
    - 기본: `{trNumber}-{specNumber}` (예: "38.769-38.291")
    - Section 포함: `{trNumber}-{specNumber}-S{sectionNumber}` (예: "38.885-38.211-S8")
    
    ### 4.2 Object Property (신규 + 역관계)
    
    | Property | Range | Inverse | Description |
    | --- | --- | --- | --- |
    | impactOfTR | TechnicalReport | hasTRImpact | 이 Impact의 소스 TR (역관계) |
    | impactsSpec | Spec | specImpactedBy | 영향받는 TS |
    | specImpactedBy | Spec | impactsSpec | TS가 받은 영향 (역관계, Spec 측) |
    | impactsSection | Section | sectionImpactedBy | 영향받는 Section (선택) |
    
    ---
    
    ### 5. 재사용 클래스 확장 속성
    
    Phase-5에서 기존 클래스에 추가되는 **역관계 속성**:
    
    ### 5.1 Spec 클래스 (Phase-1) - 역관계 추가
    
    | Property | Range | Inverse | Description |
    | --- | --- | --- | --- |
    | specImpactedBy | TRImpact | impactsSpec | 이 TS가 받은 TR 영향 (역관계) |
    
    ### 5.2 Section 클래스 (Phase-3) - 역관계 추가
    
    | Property | Range | Inverse | Description |
    | --- | --- | --- | --- |
    | sectionImpactedBy | TRImpact | impactsSection | 이 Section이 받은 TR 영향 (역관계) |
    
    ### 5.3 WorkItem 클래스 (Phase-2) - 역관계 추가
    
    | Property | Range | Inverse | Description |
    | --- | --- | --- | --- |
    | hasRelatedTR | TechnicalReport | relatedToWorkItem | 이 WI와 연결된 TR (역관계) |
    
    ---
    
    ### 6. 전체 Data Property 목록 (Phase-5)
    
    | # | Property | Domain | Type | Description |
    | --- | --- | --- | --- | --- |
    | 1 | trNumber | TechnicalReport | String | TR 고유 번호 |
    | 2 | trVersion | TechnicalReport | String | TR 버전 |
    | 3 | trTitle | TechnicalReport | String | TR 제목 |
    | 4 | trStatus | TechnicalReport | TRStatus | TR 상태 |
    | 5 | scope | TechnicalReport | String | 연구 범위 요약 |
    | 6 | conclusions | TechnicalReport | String | 연구 결론 요약 |
    | 7 | studyItemRpNumber | TechnicalReport | String | Study Item RP 번호 |
    | 8 | workItemRpNumber | TechnicalReport | String | Work Item RP 번호 |
    | 9 | trImpactId | TRImpact | String | TRImpact 고유 식별자 |
    | 10 | impactType | TRImpact | ImpactType | 영향 유형 |
    | 11 | affectedSection | TRImpact | String | 영향받은 섹션 번호 텍스트 |
    | 12 | impactDescription | TRImpact | String | 영향 설명 |
    
    ---
    
    ### 7. 전체 Object Property 목록 (Phase-5)
    
    | # | Property | Domain | Range | Inverse | Description |
    | --- | --- | --- | --- | --- | --- |
    | 1 | hasTRImpact | TechnicalReport | TRImpact | impactOfTR | TR → Impact |
    | 2 | impactOfTR | TRImpact | TechnicalReport | hasTRImpact | Impact → TR (역) |
    | 3 | impactsSpec | TRImpact | Spec | specImpactedBy | Impact → TS |
    | 4 | specImpactedBy | Spec | TRImpact | impactsSpec | TS → Impact (역) |
    | 5 | impactsSection | TRImpact | Section | sectionImpactedBy | Impact → Section |
    | 6 | sectionImpactedBy | Section | TRImpact | impactsSection | Section → Impact (역) |
    | 7 | referencesTR | TechnicalReport | TechnicalReport | referencedByTR | TR → TR 참조 |
    | 8 | referencedByTR | TechnicalReport | TechnicalReport | referencesTR | TR → TR 참조 (역) |
    | 9 | relatedToWorkItem | TechnicalReport | WorkItem | hasRelatedTR | TR → WI |
    | 10 | hasRelatedTR | WorkItem | TechnicalReport | relatedToWorkItem | WI → TR (역) |
    | * | targetRelease | TechnicalReport | Release | - | Phase-1 최초 선언, Phase-5 도메인 확장. 신규 카운트 제외 |
    
    ---
    
    ### 8. Inverse Property 정리
    
    | 정방향 | 역방향 | Domain ↔ Range |
    | --- | --- | --- |
    | hasTRImpact | impactOfTR | TechnicalReport ↔ TRImpact |
    | impactsSpec | specImpactedBy | TRImpact ↔ Spec |
    | impactsSection | sectionImpactedBy | TRImpact ↔ Section |
    | referencesTR | referencedByTR | TechnicalReport ↔ TechnicalReport |
    | relatedToWorkItem | hasRelatedTR | TechnicalReport ↔ WorkItem |
    
    *참고: targetRelease는 CQ에서 역방향 질의가 없으므로 역관계 미정의*
    
    ---
    
    ### 9. 설계 결정 노트
    
    ### 9.1 targetRelease 역관계 미정의
    
    | 항목 | 내용 |
    | --- | --- |
    | **결정** | targetRelease의 역관계를 정의하지 않음 |
    | **근거** | CQ에 "특정 Release를 타겟으로 하는 TR 목록" 질의 없음 |
    | **대안** | 필요시 Cypher 쿼리로 역방향 탐색 가능 |
    
    ### 9.2 targetRelease Property 재사용
    
    | 항목 | 내용 |
    | --- | --- |
    | **결정** | 기존 Phase-1 `targetRelease`와 동일 Property 사용 |
    | **근거** | Ontology 101 원칙 - "가장 일반적인 클래스에 Property 부착" |
    | **효과** | Tdoc, CR, TechnicalReport 모두 동일 Property로 Release 참조 |
    
    ### 9.3 trStatus 추론 규칙 (선택적)
    
    | 항목 | 내용 |
    | --- | --- |
    | **결정** | trStatus는 version 패턴에서 추론 |
    | **규칙** | v0.x.x → Draft, vX.0.0 (X>0) → Completed, vX.Y.Z (Y|Z>0, Living 대상 TR) → Living |
    | **근거** | TR 분석 결과 version 패턴이 status와 일치 |
    
    ---
    
    ### 10. 요약
    
    ### 10.1 Phase-5 속성 정의
    
    §3 (TechnicalReport 신규 속성), §4 (TRImpact 속성), §5 (재사용 클래스 확장) 목록 참조.
    
    ### 10.2 클래스별 속성 요약
    
    | 클래스 | Data Property | Object Property |
    | --- | --- | --- |
    | TechnicalReport | §3.1 목록 | §3.2 목록 |
    | TRImpact | §4.1 목록 | §4.2 목록 |
    | Spec (확장) | - | §5.1 (역관계) |
    | Section (확장) | - | §5.2 (역관계) |
    | WorkItem (확장) | - | §5.3 (역관계) |
    
    ---
    
    ### 11. 검증
    
    | 검증 항목 | 결과 | 비고 |
    | --- | --- | --- |
    | CQ 모두 커버? | ✅ | 모든 CQ 답변 가능 |
    | Step 3 용어 모두 정의? | ✅ | 용어 + trImpactId |
    | 모든 클래스에 식별자 존재? | ✅ | trNumber, trImpactId |
    | 역관계 완전성? | ✅ | (목록 참조) |
    | Domain/Range 유효성? | ✅ | 모든 클래스 존재 |
    | 명명 규칙 일관성? | ✅ | camelCase 통일 |
    
    ---
    
    ## Step 6: 제약조건(Facet) 정의
    
    > Ontology 101 원칙
    > 
    > 
    > *"Slots can have different facets describing the value type, allowed values, the number of the values (cardinality), and other features of the values the slot can take."*
    > 
    > — Noy & McGuinness, Ontology Development 101
    > 
    
    ---
    
    ### 1. Step 6 목적
    
    - Step 5에서 정의한 속성의 **제약조건(Facet)** 정의
    - **Cardinality**: 속성값 개수 제한 (0..1, 1, 0..*, 1..*)
    - **Required**: 필수 여부
    - **Functional**: 단일값 여부
    - **InverseFunctional**: 역관계가 Functional인지
    - **특성**: Irreflexive, Asymmetric 등
    - **Enum 값**: 허용되는 값 목록
    - **패턴**: 값의 형식 제약
    
    ---
    
    ### 2. Facet 종류
    
    | Facet | 설명 | 예시 |
    | --- | --- | --- |
    | **Cardinality** | 속성값 개수 | 0..1, 1, 0..*, 1..* |
    | **Required** | 필수 여부 | ✅ / ❌ |
    | **Functional** | 단일값만 허용 | ✅ (최대 1개) |
    | **InverseFunctional** | 역관계가 Functional | hasTRImpact |
    | **Inverse** | 역관계 | hasTRImpact ↔ impactOfTR |
    | **Irreflexive** | 자기참조 불허 | A-R-A 불가 |
    | **Asymmetric** | 비대칭 관계 | A-R-B ⟹ B-R-A 불가 |
    
    ### Cardinality 표기법
    
    | 표기 | 의미 | Required | Functional |
    | --- | --- | --- | --- |
    | 1 | 정확히 1개 | ✅ | ✅ |
    | 0..1 | 0개 또는 1개 | ❌ | ✅ |
    | 1..* | 1개 이상 | ✅ | ❌ |
    | 0..* | 0개 이상 | ❌ | ❌ |
    
    ---
    
    ### 3. Enum 정의
    
    ### 3.1 TRStatus
    
    | 값 | 정의 | 예시 TR |
    | --- | --- | --- |
    | **Draft** | 연구 진행 중 | 38.765 (ISAC) |
    | **Completed** | 연구 완료, TS 반영됨 | 38.769 (Ambient IoT) |
    | **Living** | 지속 업데이트 (평가용) | 38.901 (Channel Model) |
    
    ### 3.2 ImpactType
    
    | 값 | 정의 | 예시 |
    | --- | --- | --- |
    | **NewTS** | 완전히 새로운 TS 생성 | 38.769 → 38.291 |
    | **NewSection** | 기존 TS에 새 섹션 추가 | 38.885 → Section 8 |
    | **ExtendSection** | 기존 TS 섹션 확장 | 38.843 → Section 5.2 |
    | **NoChange** | TS 변경 없음 (참조용) | 38.901, 38.812 |
    
    ---
    
    ### 4. TechnicalReport Data Property Facet
    
    | Property | Type | Cardinality | Required | 제약 | Description |
    | --- | --- | --- | --- | --- | --- |
    | trNumber | String | 1 | ✅ | PK, 패턴 | `^\\d{2}\\.\\d{3}(-\\d+)?$` (예: 38.769, 38.760-1) |
    | trVersion | String | 1 | ✅ | 패턴 | `^\d+\.\d+\.\d+$` (예: 19.0.0) |
    | trTitle | String | 1 | ✅ | - | 빈 문자열 불가 |
    | trStatus | TRStatus | 1 | ✅ | Enum | Draft, Completed, Living |
    | scope | String | 0..1 | ❌ | - | 1~10문장 요약 |
    | conclusions | String | 0..1 | ❌ | - | 1~10문장 요약 |
    | studyItemRpNumber | String | 0..1 | ❌ | 패턴 | `^RP-\d{6}$` (예: RP-213599) |
    | workItemRpNumber | String | 0..1 | ❌ | 패턴 | `^RP-\d{6}$` (예: RP-213599) |
    
    ---
    
    ### 5. TechnicalReport Object Property Facet
    
    | Property | Domain | Range | Cardinality | Functional | InverseFunctional | Inverse | 특성 |
    | --- | --- | --- | --- | --- | --- | --- | --- |
    | hasTRImpact | TR | TRImpact | 0..* | ❌ | ✅ | impactOfTR | - |
    | referencesTR | TR | TR | 0..* | ❌ | ❌ | referencedByTR | Irreflexive |
    | referencedByTR | TR | TR | 0..* | ❌ | ❌ | referencesTR | Irreflexive |
    | relatedToWorkItem | TR | WorkItem | 0..* | ❌ | ❌ | hasRelatedTR | - |
    | targetRelease | TR | Release | 1 | ✅ | ❌ | - | Phase-1 최초 선언, 도메인 확장 |
    
    ### 특성 설명
    
    | Property | 특성 | 이유 |
    | --- | --- | --- |
    | referencesTR | Irreflexive | TR이 자기 자신을 참조하는 것은 무의미 |
    | referencesTR | NOT Asymmetric | 두 TR이 서로 참조 가능 (상호 참조) |
    | referencesTR | NOT Transitive | A→B→C일 때 A→C 자동 추론 불필요 |
    
    ---
    
    ### 6. TRImpact Data Property Facet
    
    | Property | Type | Cardinality | Required | 제약 | Description |
    | --- | --- | --- | --- | --- | --- |
    | trImpactId | String | 1 | ✅ | PK | 고유 식별자 |
    | impactType | ImpactType | 1 | ✅ | Enum | NewTS, NewSection, ExtendSection, NoChange |
    | affectedSection | String | 0..1 | ❌ | - | 섹션 번호 텍스트 (예: "8", "17") |
    | impactDescription | String | 0..1 | ❌ | - | 영향 설명 |
    
    ---
    
    ### 7. TRImpact Object Property Facet
    
    | Property | Domain | Range | Cardinality | Functional | InverseFunctional | Inverse | 특성 |
    | --- | --- | --- | --- | --- | --- | --- | --- |
    | impactOfTR | TRImpact | TR | 1 | ✅ | ❌ | hasTRImpact | - |
    | impactsSpec | TRImpact | Spec | 1 | ✅ | ❌ | specImpactedBy | - |
    | impactsSection | TRImpact | Section | 0..1 | ✅ | ❌ | sectionImpactedBy | - |
    
    ---
    
    ### 8. 재사용 클래스 확장 Object Property Facet
    
    ### 8.1 Spec (Phase-1) 확장
    
    | Property | Domain | Range | Cardinality | Functional | Inverse |
    | --- | --- | --- | --- | --- | --- |
    | specImpactedBy | Spec | TRImpact | 0..* | ❌ | impactsSpec |
    
    ### 8.2 Section (Phase-3) 확장
    
    | Property | Domain | Range | Cardinality | Functional | Inverse |
    | --- | --- | --- | --- | --- | --- |
    | sectionImpactedBy | Section | TRImpact | 0..* | ❌ | impactsSection |
    
    ### 8.3 WorkItem (Phase-2) 확장
    
    | Property | Domain | Range | Cardinality | Functional | Inverse |
    | --- | --- | --- | --- | --- | --- |
    | hasRelatedTR | WorkItem | TR | 0..* | ❌ | relatedToWorkItem |
    
    ---
    
    ### 9. 필수 속성 요약
    
    ### 9.1 필수 Data Property
    
    | Class | Required Properties |
    | --- | --- |
    | TechnicalReport | trNumber, trVersion, trTitle, trStatus |
    | TRImpact | trImpactId, impactType |
    
    ### 9.2 필수 Object Property
    
    | Class | Required Properties |
    | --- | --- |
    | TechnicalReport | targetRelease (1) |
    | TRImpact | impactOfTR (1), impactsSpec (1) |
    
    ---
    
    ### 10. Functional / InverseFunctional Property 요약
    
    | Property | Functional | InverseFunctional | 설명 |
    | --- | --- | --- | --- |
    | targetRelease | ✅ | - | TR은 하나의 Release만 타겟 |
    | impactOfTR | ✅ | - | TRImpact는 하나의 TR에서만 유래 |
    | impactsSpec | ✅ | - | TRImpact는 하나의 TS에만 영향 |
    | impactsSection | ✅ | - | TRImpact는 최대 하나의 Section에 영향 |
    | hasTRImpact | - | ✅ | 각 TRImpact는 하나의 TR에서만 참조됨 |
    
    ---
    
    ### 11. Inverse Property 요약
    
    | Property | Inverse | Domain ↔ Range |
    | --- | --- | --- |
    | hasTRImpact | impactOfTR | TR ↔ TRImpact |
    | impactsSpec | specImpactedBy | TRImpact ↔ Spec |
    | impactsSection | sectionImpactedBy | TRImpact ↔ Section |
    | referencesTR | referencedByTR | TR ↔ TR |
    | relatedToWorkItem | hasRelatedTR | TR ↔ WorkItem |
    
    *참고: targetRelease는 CQ에서 역방향 질의가 없으므로 역관계 미정의 (쿼리로 해결)*
    
    ---
    
    ### 12. 데이터 패턴
    
    ### 12.1 ID 패턴
    
    | 클래스 | 속성 | 패턴 | 예시 |
    | --- | --- | --- | --- |
    | TechnicalReport | trNumber | `^\d{2}\.\d{3}(-\d+)?$` | 38.769, 38.901, 38.760-1 |
    | TRImpact | trImpactId | `{trNumber}-{specNumber}[-S{section}]` | 38.769-38.291, 38.885-38.211-S8 |
    
    ### 12.2 버전 패턴
    
    | 클래스 | 속성 | 패턴 | 예시 |
    | --- | --- | --- | --- |
    | TechnicalReport | trVersion | `^\d+\.\d+\.\d+$` | 19.0.0, 16.2.0 |
    
    ### 12.3 참조 ID 패턴
    
    | 클래스 | 속성 | 패턴 | 예시 |
    | --- | --- | --- | --- |
    | TechnicalReport | studyItemRpNumber | `^RP-\d{6}$` | RP-213599 |
    | TechnicalReport | workItemRpNumber | `^RP-\d{6}$` | RP-213599 |
    
    ---
    
    ### 13. 요약
    
    ### 13.1 Phase-5 Facet 정의
    
    §4 (TechnicalReport Facet), §5~§7 (TRImpact Facet), §8 (재사용 클래스 확장 Facet), §9 (필수 속성), §10 (Functional/InverseFunctional) 참조.
    
    ### 13.2 클래스별 제약조건 요약
    
    (Step 6 §3~§8 참조)
    
    ### 13.3 Enum 정의
    
    | Enum | 값 목록 |
    | --- | --- |
    | TRStatus | Draft, Completed, Living |
    | ImpactType | NewTS, NewSection, ExtendSection, NoChange |
    
    ### 13.4 특성 정의
    
    | Property | Irreflexive | Asymmetric | Transitive |
    | --- | --- | --- | --- |
    | referencesTR | ✅ | ❌ | ❌ |
    | referencedByTR | ✅ | ❌ | ❌ |
    
    ---
    
    ### 14. 검증
    
    | 검증 항목 | 결과 | 비고 |
    | --- | --- | --- |
    | Phase 1-4 패턴과 일관성? | ✅ | Cardinality, Functional, InverseFunctional, 특성 |
    | 모든 CQ 답변 가능? | ✅ | CQ 커버 |
    | Enum 완전성? | ✅ | TRStatus, ImpactType (§3.1, §3.2 값 목록 참조) |
    | 패턴 정확성? | ✅ | 정규식 검증 완료 |
    | 필수 속성 적절성? | ✅ | 데이터 소스 기반 검증 |
    
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
    
    ### 1. Step 7 목적
    
    - Step 4~6에서 정의한 클래스, 속성, 제약조건을 바탕으로 **인스턴스 생성 규칙** 정의
    - **ID 생성 규칙**: 인스턴스 식별자 패턴
    - **데이터 소스 매핑**: TR 문서 → 속성값
    - **예시 인스턴스**: 실제 데이터 기반 예시
    
    ---
    
    ### 2. 데이터 소스
    
    | 소스 | 형식 | 수량 | 용도 |
    | --- | --- | --- | --- |
    | TR 문서 | Word (.docx) | [P5-V01]개 | TechnicalReport 인스턴스 |
    | TR-TS 영향 매핑 | legacy CSV stopgap (SPECTRA-native = grounded LLM, TSG_RAN) | 주요 TR (목록 참조) | TRImpact 인스턴스 |
    
    ### 2.1 TR 문서 목록
    
    | TR | 제목 | Release | Status | ImpactType |
    | --- | --- | --- | --- | --- |
    | 38.769 | Study on Ambient IoT | Rel-19 | Completed | NewTS |
    | 38.889 | Study on NR-based access to unlicensed spectrum | Rel-16 | Completed | NewTS |
    | 38.885 | Study on NR Vehicle-to-Everything (V2X) | Rel-16 | Completed | NewSection |
    | 38.875 | Study on support of reduced capability NR devices | Rel-17 | Completed | NewSection |
    | 38.869 | Study on low-power Wake Up Signal and Receiver | Rel-18 | Completed | NewSection |
    | 38.843 | Study on AI/ML for NR air interface | Rel-18 | Completed | ExtendSection |
    | 38.857 | Study on NR positioning enhancements | Rel-17 | Completed | ExtendSection |
    | 38.840 | Study on UE power saving in NR | Rel-16 | Completed | ExtendSection |
    | 38.901 | Study on channel model | Rel-14+ | Living | NoChange |
    | 38.812 | Study on NOMA for NR | Rel-16 | Completed | NoChange |
    
    ---
    
    ### 3. 인스턴스 현황
    
    | Phase | 클래스 | 인스턴스 수 | 상태 |
    | --- | --- | --- | --- |
    | **Phase-5** | **TechnicalReport** | **[P5-V01]개** | 🔶 신규 |
    | **Phase-5** | **TRImpact** | **[P5-V02]** | 🔶 신규 |
    
    ### 3.1 TRImpact 인스턴스 생성 규칙
    
    **NoChange 처리:**
    
    - NoChange = TS에 직접 영향 없음 (참조/평가 용도)
    - NoChange인 TR은 **TRImpact를 생성하지 않음**
    - 예: 38.901 (Channel Model), 38.812 (NOMA)
    
    ---
    
    ### 4. ID 생성 규칙
    
    ### 4.1 ID 생성 원칙
    
    | 원칙 | 설명 |
    | --- | --- |
    | 유일성 | 클래스 내에서 고유한 값 |
    | 불변성 | 한 번 생성되면 변경 불가 |
    | 의미성 | 도메인 의미 반영 |
    | 추적성 | 데이터 소스와 매핑 가능 |
    
    ### 4.2 클래스별 ID 패턴
    
    | 클래스 | ID 속성 | 패턴 | 예시 |
    | --- | --- | --- | --- |
    | TechnicalReport | trNumber | `\d{2}\.\d{3}(-\d+)?` | 38.769, 38.901, 38.760-1 |
    | TRImpact | trImpactId | `{trNumber}-{specNumber}[-S{section}]` | 38.769-38.291, 38.885-38.211-S8 |
    
    ### 4.3 ID 참조 형식 (URI Prefix)
    
    | 클래스 | Prefix | 예시 |
    | --- | --- | --- |
    | TechnicalReport | `tr:` | `tr:38.769` |
    | TRImpact | `impact:` | `impact:38.769-38.291` |
    | Spec (Phase-1) | `spec:` | `spec:38.211` |
    | Section (Phase-3) | `section:` | `section:38.211-8` |
    | WorkItem (Phase-2) | `wi:` | `wi:NR_AIoT` |
    | Release (Phase-1) | `rel:` | `rel:Rel-19` |
    
    ---
    
    ### 5. Cross-Reference 동적 생성 규칙
    
    ### 5.1 Cross-Spec 처리 규칙
    
    `impactsSpec`이 참조하는 Spec 처리:
    
    | 조건 | 처리 |
    | --- | --- |
    | Phase-1 Spec 인스턴스에 존재 | 기존 인스턴스 사용 |
    | Phase-1 Spec 인스턴스에 없음 | 최소 Spec 인스턴스 생성 (specNumber만 포함) |
    
    **예시:**
    
    - TR 38.769 → TS 38.291 참조
    - 38.291이 Phase-1에 없음 → specNumber="38.291"인 Spec 인스턴스 생성
    
    ### 5.2 Cross-Section 처리 규칙
    
    `impactsSection`이 참조하는 Section 처리:
    
    | 조건 | 처리 |
    | --- | --- |
    | Phase-3 Section 인스턴스에 존재 | 기존 인스턴스 사용 |
    | Phase-3 Section 인스턴스에 없음 | 최소 Section 인스턴스 생성 (sectionId, sectionNumber만 포함) |
    
    **예시:**
    
    - TR 38.885 → TS 38.211 Section 8 참조
    - Section 38.211-8이 Phase-3에 없음 → sectionId="38.211-8", sectionNumber="8"인 Section 인스턴스 생성
    
    ### 5.3 동적 생성 인스턴스 최소 속성
    
    | 클래스 | 필수 속성 | 선택 속성 (null 허용) |
    | --- | --- | --- |
    | Spec | specNumber | specVersion, specTitle |
    | Section | sectionId, sectionNumber | sectionTitle |
    
    ---
    
    ### 6. TechnicalReport 인스턴스 생성
    
    ### 6.1 데이터 소스 매핑
    
    | 속성 | 소스 위치 | 변환 규칙 |
    | --- | --- | --- |
    | trNumber | 문서 번호 | `\d{2}\.\d{3}` 추출 |
    | trVersion | 문서 버전 | 표지에서 추출 (예: "V19.0.0") |
    | trTitle | 문서 제목 | 표지에서 추출 |
    | trStatus | 문서 상태 | Draft/Completed/Living 판단 |
    | scope | Scope 섹션 | 1~10문장 요약 |
    | conclusions | Conclusions 섹션 | 1~10문장 요약 |
    | studyItemRpNumber | Scope 섹션 | `RP-\d{6}` 패턴 추출 |
    | workItemRpNumber | Scope 섹션 | `RP-\d{6}` 패턴 추출 |
    
    ### 6.2 Object Property 매핑
    
    | 속성 | 소스 | 대상 클래스 | 매핑 규칙 |
    | --- | --- | --- | --- |
    | targetRelease | 문서 버전/표지 | Release | Release 이름으로 매칭 |
    | relatedToWorkItem | Scope 섹션 | WorkItem | WI 코드로 매칭 |
    | referencesTR | References 섹션 | TechnicalReport | TR 번호로 매칭 |
    | hasTRImpact | 분석 결과 | TRImpact | Impact 인스턴스 연결 |
    
    ### 6.3 예시 인스턴스
    
    **TR 38.769 (Ambient IoT) - Completed, NewTS:**
    
    ```json
    {
      "@type": "TechnicalReport",
      "@id": "tr:38.769",
      "trNumber": "38.769",
      "trVersion": "19.0.0",
      "trTitle": "Study on Ambient IoT (Internet of Things) for NR",
      "trStatus": "Completed",
      "scope": "This document captures the results of the study item on Ambient IoT for NR. The study covers device categories, deployment scenarios, and physical layer design aspects.",
      "conclusions": "The study concludes that Ambient IoT can be supported in NR with new physical layer procedures defined in TS 38.291.",
      "studyItemRpNumber": "RP-213599",
      "targetRelease": { "@id": "rel:Rel-19" },
      "relatedToWorkItem": [
        { "@id": "wi:NR_AIoT" }
      ],
      "referencesTR": [
        { "@id": "tr:38.901" }
      ],
      "hasTRImpact": [
        { "@id": "impact:38.769-38.291" }
      ]
    }
    
    ```
    
    **TR 38.901 (Channel Model) - Living, NoChange:**
    
    ```json
    {
      "@type": "TechnicalReport",
      "@id": "tr:38.901",
      "trNumber": "38.901",
      "trVersion": "17.1.0",
      "trTitle": "Study on channel model for frequencies from 0.5 to 100 GHz",
      "trStatus": "Living",
      "scope": "This document provides channel models for link-level and system-level simulations.",
      "conclusions": "The channel models defined in this TR serve as evaluation methodology for various NR studies.",
      "targetRelease": { "@id": "rel:Rel-14" },
      "referencesTR": [],
      "hasTRImpact": []
    }
    
    ```
    
    *Note: Living/NoChange TR은 hasTRImpact가 빈 배열*
    
    ---
    
    ### 7. TRImpact 인스턴스 생성
    
    ### 7.1 생성 조건
    
    | 조건 | TRImpact 생성 |
    | --- | --- |
    | impactType = NewTS | ✅ 생성 |
    | impactType = NewSection | ✅ 생성 |
    | impactType = ExtendSection | ✅ 생성 |
    | impactType = NoChange | ❌ 생성 안 함 |
    
    ### 7.2 데이터 소스 매핑
    
    | 속성 | 소스 | 변환 규칙 |
    | --- | --- | --- |
    | trImpactId | 생성 | `{trNumber}-{specNumber}[-S{section}]` |
    | impactType | 분석 결과 | NewTS, NewSection, ExtendSection |
    | affectedSection | 분석 결과 | 영향받은 섹션 번호 텍스트 |
    | impactDescription | 분석 결과 | 영향 설명 |
    
    ### 7.3 Object Property 매핑
    
    | 속성 | 소스 | 대상 클래스 | 매핑 규칙 |
    | --- | --- | --- | --- |
    | impactOfTR | 분석 결과 | TechnicalReport | TR 번호로 매칭 |
    | impactsSpec | 분석 결과 | Spec | Spec 번호로 매칭 (동적 생성 가능) |
    | impactsSection | 분석 결과 | Section | Section ID로 매칭 (선택, 동적 생성 가능) |
    
    ### 7.4 예시 인스턴스
    
    **NewTS 케이스 (38.769 → 38.291):**
    
    ```json
    {
      "@type": "TRImpact",
      "@id": "impact:38.769-38.291",
      "trImpactId": "38.769-38.291",
      "impactType": "NewTS",
      "impactDescription": "TR 38.769 연구 결과로 TS 38.291 (Ambient IoT) 신규 생성",
      "impactOfTR": { "@id": "tr:38.769" },
      "impactsSpec": { "@id": "spec:38.291" }
    }
    
    ```
    
    **NewSection 케이스 (38.885 → 38.211 Section 8):**
    
    ```json
    {
      "@type": "TRImpact",
      "@id": "impact:38.885-38.211-S8",
      "trImpactId": "38.885-38.211-S8",
      "impactType": "NewSection",
      "affectedSection": "8",
      "impactDescription": "TR 38.885 V2X 연구 결과로 TS 38.211에 Section 8 (Sidelink) 추가",
      "impactOfTR": { "@id": "tr:38.885" },
      "impactsSpec": { "@id": "spec:38.211" },
      "impactsSection": { "@id": "section:38.211-8" }
    }
    
    ```
    
    **ExtendSection 케이스 (38.843 → 38.214 Section 5.2):**
    
    ```json
    {
      "@type": "TRImpact",
      "@id": "impact:38.843-38.214-S5.2",
      "trImpactId": "38.843-38.214-S5.2",
      "impactType": "ExtendSection",
      "affectedSection": "5.2",
      "impactDescription": "TR 38.843 AI/ML 연구 결과로 TS 38.214 Section 5.2 (CSI reporting) 확장",
      "impactOfTR": { "@id": "tr:38.843" },
      "impactsSpec": { "@id": "spec:38.214" },
      "impactsSection": { "@id": "section:38.214-5.2" }
    }
    
    ```
    
    ---
    
    ### 8. 생성 순서
    
    ```
    [1단계 - 기존 확인]
    Phase-1 Spec 인스턴스 확인
    Phase-1 Release 인스턴스 확인
    Phase-2 WorkItem 인스턴스 확인
    Phase-3 Section 인스턴스 확인
        │
        ▼
    [2단계 - 동적 인스턴스 생성 (필요시)]
    TR/TRImpact가 참조하는 Spec/Section 확인
        │
        ├─ Spec: Phase-1에 존재 → 기존 인스턴스 사용
        ├─ Spec: Phase-1에 없음 → 최소 Spec 인스턴스 생성
        ├─ Section: Phase-3에 존재 → 기존 인스턴스 사용
        ├─ Section: Phase-3에 없음 → 최소 Section 인스턴스 생성
        │
        ▼
    [3단계 - TechnicalReport 생성]
    TR 문서 파싱 ([P5-V01]개)
        │
        ├─ trNumber, trVersion, trTitle, trStatus 추출
        ├─ scope, conclusions 요약 추출
        ├─ studyItemRpNumber, workItemRpNumber 추출 (있는 경우)
        ├─ targetRelease 연결
        ├─ relatedToWorkItem 연결 (있는 경우)
        ├─ referencesTR 연결 (있는 경우)
        │
        ▼
    [4단계 - TRImpact 생성]
    TR-TS 영향 매핑 (legacy CSV stopgap; SPECTRA-native = grounded LLM)
        │
        ├─ NoChange인 경우 → TRImpact 생성 안 함
        ├─ NewTS/NewSection/ExtendSection인 경우:
        │   ├─ TRImpact 인스턴스 생성
        │   ├─ impactOfTR 연결
        │   ├─ impactsSpec 연결 (동적 생성 가능)
        │   ├─ impactsSection 연결 (있는 경우, 동적 생성 가능)
        │
        ▼
    [5단계 - TR.hasTRImpact 연결]
    TechnicalReport.hasTRImpact 업데이트
        │
        ▼
    [6단계 - 역관계 자동 생성]
    referencedByTR ← referencesTR
    specImpactedBy ← impactsSpec
    sectionImpactedBy ← impactsSection
    hasRelatedTR ← relatedToWorkItem
    impactOfTR ← hasTRImpact
    ```
    
    ---
    
    ### 9. 역관계 자동 생성
    
    | 정방향 생성 시 | 역방향 자동 생성 |
    | --- | --- |
    | TR -[referencesTR]-> TR | TR -[referencedByTR]-> TR |
    | TR -[hasTRImpact]-> TRImpact | TRImpact -[impactOfTR]-> TR |
    | TRImpact -[impactsSpec]-> Spec | Spec -[specImpactedBy]-> TRImpact |
    | TRImpact -[impactsSection]-> Section | Section -[sectionImpactedBy]-> TRImpact |
    | TR -[relatedToWorkItem]-> WorkItem | WorkItem -[hasRelatedTR]-> TR |
    
    **Neo4j 구현:**
    
    ```
    // referencesTR 생성 시 referencedByTR 자동 생성
    MATCH (tr1:TechnicalReport)-[r:referencesTR]->(tr2:TechnicalReport)
    MERGE (tr2)-[:referencedByTR]->(tr1)
    
    // hasTRImpact 생성 시 impactOfTR 자동 생성
    MATCH (tr:TechnicalReport)-[r:hasTRImpact]->(impact:TRImpact)
    MERGE (impact)-[:impactOfTR]->(tr)
    
    // impactsSpec 생성 시 specImpactedBy 자동 생성
    MATCH (impact:TRImpact)-[r:impactsSpec]->(spec:Spec)
    MERGE (spec)-[:specImpactedBy]->(impact)
    
    // impactsSection 생성 시 sectionImpactedBy 자동 생성
    MATCH (impact:TRImpact)-[r:impactsSection]->(sec:Section)
    MERGE (sec)-[:sectionImpactedBy]->(impact)
    
    // relatedToWorkItem 생성 시 hasRelatedTR 자동 생성
    MATCH (tr:TechnicalReport)-[r:relatedToWorkItem]->(wi:WorkItem)
    MERGE (wi)-[:hasRelatedTR]->(tr)
    
    ```
    
    ---
    
    ### 10. 검증 규칙
    
    ### 10.1 무결성 검증
    
    | 검증 항목 | 규칙 | 오류 처리 |
    | --- | --- | --- |
    | TR ID 중복 | trNumber 유일 | 오류 로그 + 스킵 |
    | TRImpact ID 중복 | trImpactId 유일 | 오류 로그 + 스킵 |
    | 자기 참조 | referencesTR 대상 ≠ 자신 | 무시 (Irreflexive) |
    
    ### 10.2 필수 속성 검증
    
    | 클래스 | 필수 Data Property | 필수 Object Property |
    | --- | --- | --- |
    | TechnicalReport | trNumber, trVersion, trTitle, trStatus | targetRelease |
    | TRImpact | trImpactId, impactType | impactOfTR, impactsSpec |
    
    ### 10.3 참조 무결성 검증
    
    | 검증 항목 | 규칙 | 오류 처리 |
    | --- | --- | --- |
    | targetRelease 존재 | 대상 Release가 Phase-1에 존재 | 오류 로그 |
    | relatedToWorkItem 존재 | 대상 WorkItem이 Phase-2에 존재 | 경고 로그 (선택 속성) |
    | referencesTR 존재 | 대상 TR이 Phase-5에 존재 | 경고 로그 (선택 속성) |
    | impactsSpec 존재 | 대상 Spec 존재 (동적 생성 가능) | 동적 생성 |
    | impactsSection 존재 | 대상 Section 존재 (동적 생성 가능) | 동적 생성 |
    
    ### 10.4 Enum 유효성 검증
    
    | 속성 | 허용 값 |
    | --- | --- |
    | trStatus | Draft, Completed, Living |
    | impactType | NewTS, NewSection, ExtendSection, NoChange |
    
    ### 10.5 패턴 유효성 검증
    
    | 속성 | 패턴 | 예시 |
    | --- | --- | --- |
    | trNumber | `^\d{2}\.\d{3}(-\d+)?$` | 38.769 ✅, 38.760-1 ✅, 38.7 ❌ |
    | trVersion | `^\d+\.\d+\.\d+$` | 19.0.0 ✅ |
    | studyItemRpNumber | `^RP-\d{6}$` | RP-213599 ✅ |
    | workItemRpNumber | `^RP-\d{6}$` | RP-213599 ✅ |
    
    ### 10.6 통계 검증
    
    | 검증 항목 | 기대값 |
    | --- | --- |
    | TechnicalReport 총 수 | [P5-V01]개 |
    | TRImpact 총 수 | [P5-V02]개 |
    | targetRelease 연결 | [P5-V01]개 (100%) |
    | hasTRImpact 연결 | Completed TR 대상 (분포 — Appendix A 참조) |
    
    ---
    
    ### 11. 요약
    
    ### 11.1 인스턴스 생성 명세
    
    | 클래스 | ID 패턴 | 데이터 소스 | 예상 수 |
    | --- | --- | --- | --- |
    | TechnicalReport | `{trNumber}` | TR 문서 | [P5-V01]개 |
    | TRImpact | `{trNumber}-{specNumber}[-S{section}]` | 분석 결과 | [P5-V02]개 |
    | Spec (동적 생성) | `{specNumber}` | TR 참조 | [P5-V03] (Spec+Section 합) |
    | Section (동적 생성) | `{specNumber}-{sectionNumber}` | TR 참조 | [P5-V03] (Spec+Section 합) |
    
    ### 11.2 관계 생성 요약
    
    | 관계 | 소스 | 대상 | 역관계 |
    | --- | --- | --- | --- |
    | targetRelease | TR | Release | - |
    | relatedToWorkItem | TR | WorkItem | hasRelatedTR |
    | referencesTR | TR | TR | referencedByTR |
    | hasTRImpact | TR | TRImpact | impactOfTR |
    | impactsSpec | TRImpact | Spec | specImpactedBy |
    | impactsSection | TRImpact | Section | sectionImpactedBy |
    
    ### 11.3 누적 인스턴스 현황
    
    | Phase | 클래스 |
    | --- | --- |
    | Phase-1 | Tdoc, CR, LS, Meeting, Company, Contact, WorkItem, AgendaItem, Release, Spec, WorkingGroup |
    | Phase-2 | Resolution, Agreement, Conclusion, WorkingAssumption, Summary, SessionNotes, Figure, Table, Chart |
    | Phase-3 | Section, TSTable, TSFigure |
    | Phase-4 | CRPack |
    | **Phase-5** | **TechnicalReport ([P5-V01]), TRImpact ([P5-V02]), 동적 생성 ([P5-V03])** |
    
    ---
    
    ### 12. 검증
    
    | 검증 항목 | 결과 | 비고 |
    | --- | --- | --- |
    | Phase 1-4 패턴과 일관성? | ✅ | ID 원칙, 매핑, 예시 형식 |
    | Cross-Reference 동적 생성? | ✅ | Spec, Section 동적 생성 규칙 |
    | NoChange 처리 명확? | ✅ | TRImpact 생성 안 함 |
    | 검증 규칙 완전성? | ✅ | 무결성, 참조, Enum, 패턴, 통계 |
    
    ---
    
    ## Phase-5 온톨로지 설계 완료
    
    | 항목 | 내용 |
    | --- | --- |
    | 클래스 | TechnicalReport, TRImpact |
    | Data Property | (목록 참조) |
    | Object Property (신규) | (목록 참조) |
    | Object Property (도메인 확장) | targetRelease |
    | Enum | TRStatus, ImpactType |
    | 인스턴스 | [P5-V01]+[P5-V02]+[P5-V03] |
    
    ---
    
    ## Appendix A: 기준 수치
    
    > 이 테이블이 Spec의 수치 권위 소스이다.
    > 
    
    > 새 미팅 데이터 추가 시 이 테이블만 수정한다.
    > 
    
    | ID | 항목 | 기준값 | 비고 |
    | --- | --- | --- | --- |
    | P5-V01 | TechnicalReport 인스턴스 수 | 26 | TR 문서 파싱 결과 |
    | P5-V02 | TRImpact 인스턴스 수 | 29 | NoChange 제외, TR-TS 영향 분석 기반 |
    | P5-V03 | 동적 생성 인스턴스 수 | 0 | Phase-1/3에 없는 Spec/Section 최소 생성. 영향 표의 TS 가 모두 Phase-1 에 있고 생성기는 Section 을 만들지 않는다 |
    
    ### A.2 구현 CQ 검증 결과
    
    > Spec Step 1의 CQ는 온톨로지 설계 근거이다.
    > 
    
    > 구현에서는 Spec §4의 CQ를 검증하였다. 번호 체계는 Spec §4와 일치한다.
    > 
    
    | CQ 그룹 | 개수 | 결과 | 비고 |
    | --- | --- | --- | --- |
    | CQ1 (TR 연구현황분석) | 4개 | 4/4 PASS |  |
    | CQ2 (TS 반영영향추적) | 5개 | 5/5 PASS | CQ2-6, CQ2-7 미구현 (향후 확장) |
    | CQ3 (기술별 영향범위) | 3개 | 3/3 PASS |  |
    | CQ4 (릴리스별 연구영향) | 3개 | 3/3 PASS |  |
    | CQ5 (TR 간 참조관계) | 3개 | 3/3 PASS | referencesTR 25건 (Phase-5.1) |
    | 데이터셋 | v2.0 | [P5-V01]+[P5-V02]+[P5-V03] 인스턴스 |  |
    
    ### A.3 OP 구현 현황
    
    > 전 OP 구현 완료. TTL 선언 및 Neo4j 적재 모두 완료.
    > 
    >
    | OP | TTL 선언 | Neo4j 적재 | 구현 상태 | 비고 |
    | --- | --- | --- | --- | --- |
    | hasTRImpact | ✅ | ✅ | 구현 완료 | 29건 |
    | impactOfTR | ✅ | ✅ | 구현 완료 | 29건 (inverse) |
    | impactsSpec | ✅ | ✅ | 구현 완료 | 29건 |
    | specImpactedBy | ✅ | ✅ | 구현 완료 | 29건 (inverse) |
    | impactsSection | ✅ | ✅ | 구현 완료 | 21건 |
    | sectionImpactedBy | ✅ | ✅ | 구현 완료 | 21건 (inverse) |
    | referencesTR | ✅ | ✅ | 구현 완료 | 25건. 13/26 TR에서 추출. Phase-5.1 완료 |
    | referencedByTR | ✅ | ✅ | 구현 완료 | 25건 (inverse, 자동 생성). Phase-5.1 완료 |
    | relatedToWorkItem | ✅ | ✅ | 구현 완료 | 26건 |
    | hasRelatedTR | ✅ | ✅ | 구현 완료 | 26건 (inverse) |
    | targetRelease | ✅ | ✅ | 구현 완료 | 26건. P1 최초 선언, P5 도메인 확장 |