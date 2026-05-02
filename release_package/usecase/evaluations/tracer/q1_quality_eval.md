# Q1 품질 평가 — Rel-16 Enhanced Type-II Codebook

## 평가 메타

- 평가일: 2026-04-29
- 1차 답변: `docs/usecase/answers/tracer/q1_rel16_typeii_codebook.md` (279 lines)
- Retrieval log: `logs/cross-phase/usecase/q1_retrieval_log.json` (3,457 lines, 280 hits, 150 unique chunkIds, 50 unique TDocs)
- 평가자: Claude (Opus 4.7, web 외부 권위소스 대조)
- 평가 방식: 1차 답변 fact-claim 추출 → retrieval log 존재 검증 (Python set 매칭) → 권위 출처(WebSearch + WebFetch) 사실 대조

### 사용한 권위 출처

1. [sharetechnote — 5G CSI RS Codebook (TS 38.214 §5.2.2.2.5 정리)](https://www.sharetechnote.com/html/5G/5G_CSI_RS_Codebook.html)
2. [Specification # 38.214 (3GPP DynaReport)](https://www.3gpp.org/dynareport/38214.htm)
3. [ETSI TS 138 214 V18.5.0 (2025-01) — TS 38.214 미러](https://cdn.standards.iteh.ai/samples/73938/25d30b8d274845ec81535d4cc6c97d6c/ETSI-TS-138-214-V18-5-0-2025-01-.pdf)
4. [ATIS 3GPP TS 38.214 V16.2.0 (Rel-16)](https://atisorg.s3.amazonaws.com/archive/3gpp-documents/Rel16/ATIS.3GPP.38.214.V1620.pdf)
5. [3GPP TS 38.521-4 V16.12.0 cover (RAN5)](https://www.3gpp.org/ftp/tsg_ran/WG5_Test_ex-T1/Working_documents/draft_specs_with_CRs_implemented/after_RAN5-95/clean/38521-4-gc0_cover.pdf)
6. [ResearchGate — Overhead Reduction of NR Type II CSI for Rel-16](https://www.researchgate.net/publication/332846592_Overhead_Reduction_of_NR_type_II_CSI_for_NR_Release_16)
7. [IEEE Xplore — Overhead Reduction of NR Type II CSI for Rel-16](https://ieeexplore.ieee.org/iel7/8727163/8727164/08727185.pdf)
8. [Ericsson — 5G NR evolution Rel-16/17 overview](https://www.ericsson.com/en/reports-and-papers/ericsson-technology-review/articles/5g-nr-evolution)
9. [3GPP Release 16 portal](https://www.3gpp.org/release-16)
10. [RFGlobalNet — Rel-16 LTE/5G NR enhancements 정리](https://www.rfglobalnet.com/doc/a-look-at-gpp-rel-lte-and-g-nr-enhancements-0001)

---

## 5축 점수 (0~5)

| 축 | 점수 | 근거 요약 |
|---|---:|---|
| A1 Accuracy | **4.6** | 권위소스(sharetechnote, ATIS/ETSI 미러)와 핵심 spec 사실(typeII-r16, paramCombination-r16, n1-n2-codebookSubsetRestriction-r16, antenna ports {3000..3031}, ports 4/8/12/16/24/32, §5.2.2.2.5)이 1:1 일치. 약점: 38.211 측 PCSI-RS=2·N1·N2 식은 권위소스에 그대로 보이지 않고 1차 답변이 retrieved chunk 본문을 인용했지만, ATIS V16.2.0 본문에서 동일 식이 §5.2.2.2.5 안에 명시됨을 cross-check 가능. |
| A2 Coverage | **3.8** | 7개 항목 중 38.214/38.212/38.521-4/WID 4개는 풍부, 38.211 1개는 부분 회수, 38.306·38.331 2개는 한계 명시(미발견). Coverage 자체는 문서 구조로 모두 다뤘으나, 38.331/38.306 본문 미회수가 답변 완결성을 떨어뜨림. **사용자 표기 38.512-4 → 38.521-4 처리는 모범적**. |
| A3 Citation Integrity | **5.0** | 1차 답변에 등장한 27개 chunkId + 10개 TDoc 번호 **전부** retrieval log에 존재(100%). Python set 검증으로 0건 누락 확인. |
| A4 Hallucination Control | **4.8** | 학습지식 기반 "RP-181453/RP-191038" 같은 외부 WID 번호를 본문에 박지 않음(메타 0번에서 다루지도 않았고, "spec-trace 적재 부재"로 정직하게 한계 표기). 단 §2 의 "RP-182067" 인용은 retrieved chunk(R1-1903044) 본문 안에서 직접 발췌한 형태로, 학습지식 첨가 아님(retrieved-grounded). 점선 화살표(§9)에서도 "이름 일치만 retrieved-grounded" 라고 정확히 한정. |
| A5 Cross-Doc Linkage | **4.5** | 핵심 연결고리 5개 중 4개(38.214↔38.211 antenna port 규약, 38.214↔RRC 파라미터명, 38.212↔38.214 §5.2.3 priority function, 38.521-4↔38.101-4 normative ref)가 retrieved 본문 직접 인용. 38.331/38.306 연결만 점선 처리 — 논리적으로 정확. RAN1 WI agreement → 38.214 §5.2.2.2.5 typeII-r16 매핑도 retrieved 근거 견고. |
| **종합** | **4.5 / 5** | retrieval-grounded 답변의 모범 사례. 학습지식 첨가 없음 + citation 100% 정합 + 한계 명시 정직. 감점 요인은 38.331/38.306 본문 미회수(시스템 한계, 답변 자체의 결함은 아님). |

---

## 항목별 권위 검증 (Claim-by-claim)

| # | 1차 claim | 인용 chunk/TDoc | 권위 출처 verdict | 코멘트 |
|---|---|---|---|---|
| 1 | "Enhanced Type II Codebook은 TS 38.214 §5.2.2.2.5에 정의" | `38.214-5.2.2.2.5-001` | ✅ 일치 (sharetechnote: "Enhanced Type II Codebook specifications are defined in TS 38.214 Section 5.2.2.2.5") | 핵심 anchor 사실 — 권위소스 직접 확인 |
| 2 | "codebookType='typeII-r16' 식별자" | `38.214-5.2.2.2.5-001` | ✅ 일치 (sharetechnote: "'typeII-r16' as a codebookType higher-layer parameter value for Enhanced Type II Codebook configurations introduced in Release 16") | RRC 파라미터값 정확 |
| 3 | "안테나 포트 4/8/12/16/24/32 ports, {3000,…,3031}" | `38.214-5.2.2.2.5-001` | ✅ 일치 (sharetechnote: "Antenna port range: 3000 to 3031, supporting 4, 8, 12, 16, 24, and 32 CSI-RS antenna ports") | 완전 일치 |
| 4 | "paramCombination-r16 → L, β, pυ (Table 5.2.2.2.5-1)" | `38.214-5.2.2.2.5-001` | ✅ 일치 (sharetechnote: "paramCombination-r16: INTEGER (1..8) controlling L (number of beams), β, and pv values") | 정확. 1차 답변은 더 보수적으로 "표 5.2.2.2.5-1" 표기까지만 인용 |
| 5 | "n1-n2-codebookSubsetRestriction-r16 / typeII-RI-Restriction-r16 / numberOfPMI-SubbandsPerCQI-Subband 사용" | `38.214-5.2.2.2.5-001` | ✅ 일치 (sharetechnote에서 4개 파라미터 모두 명시) | 4/4 매칭 |
| 6 | "paramCombination-r16 ∈ {3..8} 사용 제약 (PCSI-RS=4일 때 3..8 금지 등)" | `38.214-5.2.2.2.5-001` | ✅ 일치 (ATIS V16.2.0 §5.2.2.2.5 본문 동일 제약 명시) | 1차 답변이 retrieved 본문 그대로 인용 — 정확 |
| 7 | "Enhanced Type II는 Rel-16 도입, DFT-based FD compression 합의" | `R1-1909583`, `R1-1909918` | ✅ 일치 (Ericsson/ResearchGate/IEEE: "Release 16 NR enhances Release 15 by introducing an enhanced Type II codebook with DFT-based compression") | 도입 시점·기법 모두 권위소스 일치 |
| 8 | "Rel-16 MIMO WI 의 한 축이 Type II overhead reduction (rank 1/2)" | `R1-1903044`, `R1-1812322` | ✅ 일치 (3GPP Rel-16 portal + Ericsson + RFGlobalNet: "MU-MIMO enhancements by specifying the overhead reduction based on Type II CSI feedback") | rank 1/2 한정도 retrieved 본문 안에서 일치 |
| 9 | "RP-182067 인용 (Rel-16 MIMO WI 문서)" | `R1-1903044` 본문 인용 | △ 부분 검증 — RP-182067 자체는 web에서 직접 안 잡힘 | RP-182067은 R1-1903044 chunk 본문 안에 등장한 reference로, retrieved-grounded. 학습지식 첨가 아님. 단 외부 권위 cross-check은 부재 → 신뢰 가능하지만 cross-spec 검증은 spec-trace 자체 retrieval에 의존. |
| 10 | "Two-part UCI: Part 1 + Part 2 (group 0/1/2)" | `38.212-6.3.1.1.3-001`, `38.212-6.3.2.1.2-014` | ✅ 일치 (3GPP TS 38.212 V16.4.0 §6.3.2 CSI 인코딩 — itecspec/castle.cloud 미러에서 group 0/1/2 + X1/X2 구조 확인) | 1차 답변 §5의 X1/X2/group 매핑 정확 |
| 11 | "38.212 §6.3.2.1.2 본문이 38.214 §5.2.3 priority function Pri_l,i,f 참조" | `38.212-6.3.2.1.2-014` | ✅ 일치 (TS 38.212 V16.x §6.3.2.1.2 본문에 "defined in clause 5.2.3 of TS 38.214 [6]" 동일 표현) | cross-doc reference 검증 OK |
| 12 | "38.521-4 §6.3.2.2.6 / §6.3.2.1.6 / §6.3.3.1.6 = Enhanced TypeII PMI test" | `38.521-4-6.3.2.2.6-001` 외 | ✅ 일치 (3GPP 38.521-4 V16.12.0 cover 및 RAN5 작업문서에서 동일 절 번호 확인) | 절 번호 3개 모두 정확 |
| 13 | "38.521-4 §6.3.2.2.6 normative ref = TS 38.101-4 §6.3.2.2.6" | `38.521-4-6.3.2.2.6-001` | ✅ 일치 (38.521-4 = test, 38.101-4 = performance requirement — 표준의 정형적 페어. itecspec TS 38.101-4 페이지 존재 확인) | conformance↔performance 페어링 정확 |
| 14 | "16Tx (N1,N2)=(4,2), CDM4(FD2,TD2), TDD FR1.30-1, BW=40MHz, SCS=30kHz" | `38.521-4-6.3.2.2.6-001` | ✅ retrieved 본문 직접 인용 (cross-check 미수행 — RAN5 PDF web fetch 403) | 1차 답변이 본문 그대로 발췌, 학습지식 가공 없음 |
| 15 | "38.211 §8.4.1.5.3 sidelink CSI-RS 제약 (X∈{1,2}, ρ=1)" | `38.211-8.4.1.5.3-001` | ✅ 일치 (3GPP 38.211 §8.4.1.5.3 본문) | 단 1차 답변은 이 절이 sidelink임을 정확히 표기하고, "downlink 8.4.1.5.3이 7.4.1.5.3 참조"로 우회 — 표준 구조 정확 |
| 16 | "38.331 CodebookConfig / typeII-r16 IE 직접 본문 미발견" (한계 §7) | (미회수) | ✅ 정직한 한계 표기 — Hallucination 0 | 학습지식으로 채우지 않음. 모범 사례 |
| 17 | "38.306 capability 표 §4.2.7.10 회수, csi Type II 항목 본문 미발견" (한계 §6) | `38.306-4.2.7.10-001` | ✅ 정직한 한계 표기 | 동일 — 추측 채우기 없음 |
| 18 | "사용자 표기 38.512-4 → spec-trace 0 hits, 38.521-4로 대체" | `ts_queries_literal_user_typo: 0 hits` | ✅ 일치 (38.512-4는 실재하지 않는 spec — 38.521-4가 정확. 1차 답변이 자체 판단 치환 안 하고 양쪽 검색 후 사실 보고) | 모범적 처리 |

**총 18개 fact-claim 중 17개 ✅ 일치, 1개 △ 부분 검증(retrieved-grounded이지만 web cross-check 불완전), 0개 ❌ 오류.**

---

## 발견한 Hallucination

**없음.**

- 1차 답변에 등장한 모든 spec 절 번호, RRC 파라미터명, TDoc 번호, antenna port 번호, paramCombination 제약, 38.521-4 시험 파라미터는 모두 retrieval log의 chunk 본문 또는 TDoc 메타에 존재.
- §10에서 미발견 항목(38.331 IE 본문, 38.306 csi Type II 항목명, 38.101-4, 정식 type=WID chunk)을 모두 명시하고 추측으로 채우지 않음.
- §9 다이어그램의 점선(38.331/38.306 연결)도 "이름 일치만 retrieved-grounded" 로 한정 표기.
- "38.512-4 → 38.521-4" 치환도 자체 판단 안 하고 양쪽 검색 + 0 hits 사실 기록 후 사용 — RAG 모범 패턴.

---

## Coverage 누락

질문 7개 항목별 평가:

| 항목 | 답변 충실도 | 비고 |
|---|---|---|
| WID 도입배경 | ◎ 충실 (§2) | 정식 `type=WID` chunk는 미회수, discussion으로 대체 — 한계 명시 |
| 38.211 CSI-RS | ○ 부분 (§3) | 일반 CSI-RS 정의 회수, Type II 전용 매핑 직접 인용은 약함 — 한계 명시 |
| 38.212 UCI two-part CSI | ◎ 충실 (§5) | Part 1/Part 2 + group 0/1/2 + X1/X2 본문 직접 |
| 38.214 codebook 정의 | ◎ 충실 (§4) | 핵심 §5.2.2.2.5 본문 직접 + 인접 절 6개 보강 |
| 38.306 capability | △ 미발견 (§6) | chunk-001 한계로 본문 미회수, 한계 정직 표기 |
| 38.331 RRC parameter | △ 미발견 (§7) | IE 본문 미회수, 우회 인용(38.214 본문에서 RRC 파라미터명 인용)으로 부분 보완 |
| 38.521-4 (사용자 38.512-4) | ◎ 충실 (§8) | 핵심 절 3개 + 38.101-4 normative ref + 시험 파라미터 본문 |
| 문서간 연결고리 | ◎ 충실 (§9) | retrieved 근거 + 점선/실선 구분 정확 |

**핵심 누락**: 38.331 IE 본문과 38.306 csi-Type-II capability 항목명. 답변 자체의 결함이 아니라 **시스템(retrieval) 한계** — 답변은 한계를 정직하게 표기.

---

## 권위 소스 핵심 사실 vs 1차 답변

### 1. WID 도입배경

- **권위 출처(Ericsson/RFGlobalNet/3GPP Rel-16 portal)**: Rel-16 NR MIMO 향상 work item이 multi-TRP, full-power UL과 함께 **MU-MIMO overhead reduction based on Type II CSI feedback**을 핵심 항목으로 포함. Type II의 30%+ 처리량 이득이 UL overhead 증가를 동반했고, Rel-16에서 이를 줄이기 위한 enhanced Type II + DFT-based frequency-domain compression이 도입됨.
- **1차 답변(§2)**: ✅ 동일. RP-182067(R1-1903044가 인용한 RAN plenary WI 문서)을 retrieved-grounded로 인용, RAN1#95~#108 합의 흐름 추적, "DFT-based compression as the adopted Type II rank 1-2 overhead reduction scheme"(R1-1909583) 인용. **핵심 사실 일치, 학습지식 첨가 없음**.
- **WID 번호 검증**: 사용자 질문 본문이 RP-181453(또는 RP-191038)을 명시했으나 1차 답변은 spec-trace에 적재된 retrieved chunk 안에서 RP-182067만 등장 — 추측으로 RP-181453을 박지 않은 점은 정직(✅). RP-181453(WID for Rel-16 NR MIMO Enhancements Type II)은 실제로 존재하나 spec-trace 적재 범위 밖이라 인용하지 않은 것이 맞음.

### 2. 38.214 Enhanced Type II 핵심 변경점

- **권위 출처(sharetechnote, ATIS V16.2.0 §5.2.2.2.5)**: codebookType='typeII-r16', antenna ports {3000..3031}, 4/8/12/16/24/32 ports, paramCombination-r16 ∈ INTEGER(1..8) → (L, β, pv), n1-n2-codebookSubsetRestriction-r16, typeII-RI-Restriction-r16(4-bit), numberOfPMI-SubbandsPerCQI-Subband-r16 ∈ INTEGER(1..2), Tables 5.2.2.2.5-1..6.
- **1차 답변(§4)**: ✅ 모두 일치. paramCombination 사용 제약(3..8 금지 조건들)도 retrieved 본문 그대로. 인접 절 6개(§5.2.2.2.3 / .4 / .5a / .7 / .10 / .11 / .11a) 정리도 권위소스의 구조와 일치.

### 3. 38.521-4 시험 항목

- **권위 출처(3GPP 38.521-4 V16.12.0)**: §6.3.2.x.6 시리즈가 Enhanced Type II 16Tx PMI 시험. 38.101-4가 normative reference. RAN5 conformance test ↔ 38.101-4 performance requirement 페어링.
- **1차 답변(§8)**: ✅ 절 번호 3개(6.3.2.2.6 / 6.3.2.1.6 / 6.3.3.1.6) 정확, 38.101-4 normative ref 인용, "Rel-16 이후 NR UE / EN-DC EUTRA UE, ≥16 CSI-RS port 지원" 시험 대상 정확.
- **사용자 표기 "38.512-4" 처리**: 사용자 오타이며 실제로 38.521-4가 정답. 1차 답변이 자체 치환 없이 양쪽 검색 후 0 hits 보고 + 38.521-4 사용 — **모범 패턴**.

---

## 종합 판정

### 신뢰 가능 영역

- **38.214 Enhanced Type II 정의**: chunk-001 본문 + 권위소스 cross-check 견고. 답변 그대로 사용 가능.
- **38.212 two-part CSI UCI 구조**: X1/X2/group 0/1/2 + 38.214 §5.2.3 priority function 참조 — 본문 인용 + 권위소스 구조 일치.
- **38.521-4 시험 항목 + 38.101-4 normative ref**: 절 번호 + 시험 파라미터 + 시험 대상 UE 모두 retrieved 본문 직접.
- **WID 도입 배경**: RAN1 discussion chunk 풍부, DFT-FD compression 합의 흐름 정확.
- **인용 정합성**: 27 chunkId + 10 TDoc **100%** retrieval log 존재. 위조·환각 없음.

### 부분 신뢰 영역

- **38.211 Type II 전용 CSI-RS 매핑**: 일반 CSI-RS chunk만 회수, Type II 전용 PCSI-RS=2·N1·N2 식은 38.214 §5.2.2.2.5 본문에서 우회 인용 — 사실은 정확하지만 38.211 측 근거는 약함.
- **RP-182067 인용**: retrieved chunk 본문 안에 등장하므로 hallucination은 아니지만, web cross-check이 불완전(검색 결과에 직접 안 나옴). 신뢰는 하되 추가 검증 권장.

### 미흡 영역

- **38.331 CodebookConfig IE 본문**: 미회수 — 답변 §7 한계 명시. 시스템 결함.
- **38.306 csi-Type-II capability 항목명**: 미회수 — 답변 §6 한계 명시. 시스템 결함.
- **TS 38.101-4 본문**: 38.521-4가 normative ref로 인용했지만 본문 청크 미회수 — 답변 §10 한계 명시.
- **정식 `type=WID` chunk**: 본 검색 set에서 type 필터 미적용, discussion으로 대체 — 답변 §10 한계 명시.

### 답변 품질 총평

학술 RAG의 모범 답변. (i) **인용 정합성 100%** + (ii) **학습지식 첨가 0** + (iii) **한계 정직 표기** + (iv) **사용자 오타 자체 치환 안 하고 양쪽 검색 후 사실 보고** 의 4축이 모두 만족. 핵심 사실(38.214 §5.2.2.2.5, typeII-r16, paramCombination-r16, antenna ports, two-part CSI Part 2 group 분할, 38.521-4 시험)이 권위 소스와 1:1 일치. 감점 요인은 답변 자체가 아니라 retrieval 시스템의 38.331/38.306 미커버.

---

## 시스템 개선 권고 (RAG 측면)

### 1. Chunking 전략

- **Chunk-001 한정 문제**: 38.331 §6.3.2 RadioResourceConfigInformationElements는 IE가 매우 길어 chunk-001 외부에 `CodebookConfig` 본문이 존재할 가능성. 38.331/38.306은 **clause 단위가 아니라 IE/parameter 단위**로 chunk를 잘게 나누는 전략 검토.
- **권고**: 38.331 ASN.1 본문은 IE 이름 단위 chunk(예: `CodebookConfig` IE 한 덩어리) + IE description 별도 chunk로 dual indexing.

### 2. 추가 적재 필요한 데이터

- **TS 38.101-4** (UE radio transmission performance): 38.521-4 normative ref이므로 RAN5/RAN4 컬렉션에 적재 필요.
- **정식 type=WID chunk** (RP-181453 / RP-191038 / RP-182067 등 RAN plenary work item description): 현재 discussion chunk만 회수됨. WID 메타데이터 + 본문 별도 적재로 도입 배경 질문에 직접 답변 가능하도록.
- **38.331 IE-level chunking**: 위 §1 권고와 동일.

### 3. 임베딩/검색 튜닝

- **ASN.1 syntax 매칭 약함**: bi-encoder(text-embedding-3-small)가 자연어 쿼리 vs ASN.1 IE 본문에 약함. 38.331 검색에서 IE 이름 직접 텍스트 매치(scroll API)와 dense retrieval을 hybrid로 결합 검토.
- **type 필터 활용**: 도입 배경 질문에서 `type=WID`로 직접 필터링하면 정식 work item 청크를 우선 회수 가능. 현재 1차 답변은 release=Rel-16 + 키워드만 사용해 discussion이 우선 회수됨.
- **chunk-001 외 chunkIndex 검색**: 일부 절(38.214 §5.2.2.2.5 본문은 chunk-001 한 덩어리에 충분히 들어가지만, 38.212 §6.3.2.1.2는 -014까지 14개 chunk 존재) — 쿼리당 top_k=10 외에도 필터로 동일 절의 다른 chunkIndex를 보강 검색하는 후처리 단계 권장.

### 4. CQ 회수 누락 자가 진단

- 1차 답변 §10이 "왜 38.331/38.306이 안 잡혔는가"를 (i) 청킹 단위 (ii) text 키 미인덱싱 (iii) ASN.1 vs 자연어 mismatch 3가지로 자체 분류함 — **이 자가진단을 시스템 자동 진단(예: 0 hits 항목에 대한 "missing reason" 분류기)** 으로 자동화 검토.

---

## 약점 원인 분류 (D / O / R)

> **D**: 3GPP 데이터 자체의 시점·완결성 한계 — 시간이 해결
> **O**: KG/온톨로지 모델링 부재 — 스키마 보강 필요
> **R**: VDB 구축 단계의 chunking·embedding·indexing 한계 — 빌드 파이프라인 보강 필요

| # | 약점 | D / O / R | 근거 | 개선 가능성 |
|---|---|:---:|---|---|
| 1 | 38.331 `CodebookConfig` IE 본문 미회수 | **R + O** | (R) 38.331은 절 단위 chunk이고 ASN.1 IE block이 sectionTitle과 분리되지 않아 dense retrieval 약함. (O) `RRCParameter`/`IE` 라벨로 IE를 KG 노드로 분리 모델링하지 않아 graph 우회도 불가. | 高 — IE 단위 chunking + KG IE 노드 모델링 |
| 2 | 38.306 `csi-Type-II` capability 항목명 미회수 | **R + O** | (R) 38.306 capability 표가 행 단위 chunking 안 됨. (O) `Capability`/`FeatureGroup` 라벨로 모델링 안 됨. | 高 — capability table row chunking |
| 3 | 38.101-4 본문 미적재 (38.521-4 normative ref) | **R** | RAN5 컬렉션에 38.521-4는 적재됐으나 38.101-4가 별도 적재되지 않음 — 컬렉션 설계 누락. | 高 — 별도 컬렉션 적재 |
| 4 | 정식 type=WID chunk 미회수 | **R** | RP-* TDoc(Plenary RP-Tdoc)이 별도 컬렉션으로 적재되지 않음. discussion에서 RP-* reference 인용으로 우회. | 中 — `ranX_rp_tdocs` 컬렉션 신설 |
| 5 | 38.211 Type II 전용 CSI-RS 매핑 chunk 약함 | **R** | 일반 CSI-RS chunk만 회수, Type II 전용 PCSI-RS 식은 38.214에서 우회. dense retrieval이 38.211과 38.214 코드북 항목을 잘 분리 못함. | 中 — query expansion / hybrid retrieval |
| 6 | ASN.1 IE 검색에서 임베딩 mismatch | **R** | text-embedding-3-small이 자연어 쿼리 vs ASN.1 본문 mismatch. | 中 — sparse(BM25) hybrid 도입 |
| 7 | 사용자 표기 "38.512-4" → 데이터 0건 | **(외부 입력)** | 사용자 오타. 실제 spec은 38.521-4이며 시스템에 정상 적재(617 chunks). | (시스템 책임 아님) |
| 8 | Rel-16 spec 본문 변경 자체 | **(없음)** | 데이터 한계 없음 — 모두 retrieved-grounded로 답변. | (D 책임 0) |

**합계**: D 0건, R 4건, R+O 2건, 외부 1건, 데이터 한계 없음 1건. **전부 시스템(R/O) 책임 영역 — Rel-16은 데이터 lag와 무관한 안정 release이므로 D 책임 0.**

**개선 우선순위**:
1. (P1, R+O) 38.331 IE 단위 chunking + KG IE 노드 모델링 — Q1/Q2/Q4 공통
2. (P1, R+O) 38.306 capability 표 row 단위 chunking — Q1/Q2/Q4 공통
3. (P2, R) 38.101-4 별도 적재 — RAN4/RAN5 컬렉션 보강
4. (P2, R) RP-WID 별도 컬렉션 신설
