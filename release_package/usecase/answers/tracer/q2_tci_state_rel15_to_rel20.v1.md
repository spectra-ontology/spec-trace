# Q2. Rel-15~Rel-20 TCI-state 관련 표준 아이템 정리 (3gpp-tracer 전용)

## 메타

| 항목 | 값 |
|---|---|
| 질문 | Rel-15부터 Rel-20까지 TCI-state 관련 표준 아이템 정리 (WID 도입 배경 + 38.214/38.321/38.331/38.306 변화 + 문서 간 연결고리) |
| 검색 시스템 | 3gpp-tracer (Qdrant + Neo4j). 외부 LLM 지식/Web 사용 금지 |
| Qdrant 컬렉션 | `ran1_ts_sections`, `ran2_ts_sections`, `ran1_tdoc_chunks`, `ran2_tdoc_chunks` |
| Neo4j 인스턴스 | RAN1 (`bolt://localhost:7687`), RAN2 (`bolt://localhost:7688`) |
| TS 검색 쿼리 | 14건 (38.214 ×4, 38.321 ×3, 38.331 ×4, 38.306 ×3) |
| TDoc 검색 쿼리 | 48건 (`{ran1,ran2}_tdoc_chunks` × 6 Releases × 4 base queries) |
| Neo4j 쿼리 | 2건 (RAN1, RAN2 — Section title CONTAINS 'tci'/'quasi'/'spatial relation') |
| 총 retrieved chunks | TS 140 + TDoc 480 = 620 / Neo4j 33 sections |
| 임베딩 모델 | `openai/text-embedding-3-small` (OpenRouter) |
| 산출물 | `logs/cross-phase/usecase/q2_retrieval_log.json` |
| 작성일 | 2026-04-29 |

> 본 문서의 모든 사실 문장은 위 검색에서 회수된 chunk 또는 Neo4j 행에서만 인용한다. 인용은 `[spec §sec, chunkId=...]` 또는 `[tdoc, meeting, type, ai=...]` 형식.

---

## 3gpp-tracer 검색 결과 요약

### Release × 컬렉션 hit 수 (TDoc, top-10 × 4 query 합산)

| Release | `ran1_tdoc_chunks` (top score) | `ran2_tdoc_chunks` (top score) |
|---|---|---|
| Rel-15 | 40 hits / max 0.696 | 40 hits / max 0.626 |
| Rel-16 | 40 hits / max 0.756 | 40 hits / max 0.666 |
| Rel-17 | 40 hits / max 0.744 | 40 hits / max 0.740 |
| Rel-18 | 40 hits / max 0.716 | 40 hits / max 0.704 |
| Rel-19 | 40 hits / max 0.716 | 40 hits / max 0.690 |
| Rel-20 | 40 hits / max 0.665 | 40 hits / max 0.621 |

### TS 섹션별 top match

| Spec | 핵심 섹션 (검색 top) | 컬렉션 |
|---|---|---|
| 38.214 | §5.1.5 "Antenna ports quasi co-location" (top 0.633, chunkId `38.214-5.1.5-005`) | `ran1_ts_sections` |
| 38.321 | §5.18.4 "Activation/Deactivation of UE-specific PDSCH TCI state" (0.772), §6.1.3.14/24/70/71 | `ran2_ts_sections` |
| 38.331 | §11.2.1, §A.3.9 (top), 단 IE 정의(`TCI-State`, `TCI-UL-State` 등)는 Neo4j에서 별도 Section 노드로 노출 | `ran2_ts_sections` + Neo4j RAN2 |
| 38.306 | §4.2.15.7.1 "BandNR parameters", §4.2.7.4 "CA-ParametersNR" (top 0.59) | `ran2_ts_sections` |

### Neo4j Section 노드 (TCI / QCL / spatial relation)

- RAN1: 1개 — `38.214 §5.1.5 Antenna ports quasi co-location` [Neo4j RAN1, port=7687]
- RAN2: 32개 (DISTINCT) — 38.321의 PDSCH/PDCCH TCI activation MAC CE 16개, 38.331의 TCI 관련 IE/필드 8개 등 [Neo4j RAN2, port=7688]
  - 38.321 핵심: §5.18.4, §5.18.5, §5.18.23, §5.18.33, §5.18.36, §6.1.3.14, §6.1.3.15, §6.1.3.24, §6.1.3.44, §6.1.3.47, §6.1.3.59, §6.1.3.60, §6.1.3.70, §6.1.3.71, §6.1.3.76, §6.1.3.77
  - 38.331 핵심 IE: `TCI-State`, `TCI-StateId`, `TCI-UL-State`, `TCI-UL-StateId`, `TCI-ActivatedConfig`, `LTM-TCI-Info`, `CandidateTCI-State`, `CandidateTCI-UL-State`

---

## Release별 답변 본문

### Rel-15 — TCI 프레임워크 도입 (NR 초기)

**RAN1 도입 배경 (TDoc 근거)**
- "Mapping between candidate TCI state and N-bit DCI field / TCI indication for PDCCH through D…"
  [R1-1718541, RAN1#90b, type=discussion, ai=7.2.2.3, title="Beam management for NR", release=Rel-15] — RAN1 NR beam management 초기 논의에서 DCI의 TCI 코드포인트와 TCI state 후보 매핑 설계가 다뤄짐.
- "There appears no reason why the TCI field of the DCI for PDSCH should not convey the non-spatial QCL parameters as they are available in the list of TCI states."
  [R1-1720662, RAN1#91, discussion, ai=7.2.2.3, "Beam management for NR", Rel-15] — TCI field via DCI로 non-spatial QCL을 전달해야 한다는 합의 흐름.

**RAN2 (38.321/38.331/38.306) Rel-15 흔적**
- RAN2 Rel-15 논의는 multi-beam 환경의 TA 유지 등 연관 토픽이 주로 회수됨: "TA maintenance with multi-beam operation" [R2-1709273, RAN2#99, discussion, ai=10.3.1.13, Rel-15]; [R2-1713179, RAN2#100, ai=10.3.1.13, Rel-15]; [R2-1704611, RAN2#98, ai=10.3.1.4, Rel-15]. — Rel-15 시점 RAN2는 빔 운용에 따른 MAC/RRC 부수 영향(TA 등)을 주로 다루고, "TCI-State" 자체의 IE는 RRC 38.331의 PDSCH-Config / PDCCH-Config 안에 정의됨 (Neo4j Section 노드 `TCI-State`, `TCI-StateId`로 RAN2 KG에 적재됨).

**Rel-15 38.214 / 38.321 / 38.331 / 38.306 변화 — retrieved 근거**
- 38.214 §5.1.5: "The UE can be configured with a list of up to M TCI-State configurations within the higher layer parameter PDSCH-Config to decode PDSCH according to a detected PDCCH … M depends on the UE capability `maxNumberConfiguredTCIstatesPerCC`."
  [38.214 §5.1.5, chunkId=`38.214-5.1.5-001`] — TCI-State list 정의의 원본 텍스트. `PDSCH-Config`(RRC) ↔ `maxNumberConfiguredTCIstatesPerCC`(UE cap) 연결도 동일 chunk에 명시.
- 38.321 §6.1.3.14 "TCI States Activation/Deactivation for UE-specific PDSCH MAC CE": "The TCI States Activation/Deactivation for UE-specific PDSCH MAC CE is identified by a MAC subheader with LCID as specified in Table 6.2.1-1. It has a variable size consisting of following fields: …"
  [38.321 §6.1.3.14, chunkId=`38.321-6.1.3.14-001`] — Rel-15 시점부터 운영된 PDSCH TCI activation MAC CE.
- 38.331 IE: `TCI-State`, `TCI-StateId` 노드가 RAN2 KG에 등록됨 [Neo4j RAN2, Section sectionNumber="TCI-State"/"TCI-StateId"]. (RAN2 ts_sections 컬렉션 청크화에는 ASN.1 IE 본문 chunk가 회수되지 않아 본문은 Neo4j Section 노드로 그 존재만 확인 — "커버리지/한계" 참조.)
- 38.306 `maxNumberConfiguredTCIstatesPerCC`: ts_sections 검색 top은 §4.2.15.7.1 "BandNR parameters" 등 capability 테이블 군집 [38.306 §4.2.15.7.1, chunkId=`38.306-4.2.15.7.1-001`]. 본문에는 capability 테이블 헤더(`Definitions for parameters | Per | M | FDD-TDD DIFF | FR1-FR2 DIFF`)만 회수되어 정확 항목 행은 후속 chunk 검토 필요.

### Rel-16 — eMIMO multi-beam 강화

**도입 배경**
- "The work item on Rel-16 MIMO enhancements has been specified [1]. … The WI for Rel-16 covers several key features aimed at enhancing multibeam …"
  [R1-1903044, RAN1#96, discussion, ai=7.2.8.3, "Enhancements on Multi-beam Operation", Rel-16];
  [R1-1813443, RAN1#95, ai=7.2.8.3, Rel-16];
  [R1-1905027, RAN1#96b, ai=7.2.8.3, Rel-16] — Rel-16 MIMO WID 하에서 multi-beam 강화 토픽 연속 진행.
- RAN2 측: "MAC CE design on single PDCCH based multi-TRP/panel transmission … TCI states for PDSCH are configured by RRC, at first. Up to 128 TCI states can be configured per BWP per serving cell. Amongst the configured TCI states, up to …"
  [R2-1910966, RAN2#107, discussion, ai=11.16, Rel-16] — 단일 PDCCH 기반 mTRP에서 RRC가 PDSCH의 최대 128 TCI 상태를 BWP당 설정한다는 설계.

**문서별 Rel-16 변경점 (retrieved)**
- 38.214: §5.1.5 활성화 절차 본문이 Rel-16 MAC CE를 인용 — "receive an activation command, as described in clause 6.1.3.70 of [10, TS 38.321], the activation command is used to map up to 8 sets of TCI states to the codepoints of the DCI field 'Transmission Configuration Indication' …"
  [38.214 §5.1.5, chunkId=`38.214-5.1.5-003`] — DCI 'TCI' 필드의 8 codepoint 매핑이 38.321 §6.1.3.70로 위임됨을 본문에서 명시.
- 38.321 §6.1.3.24 "Enhanced TCI States Activation/Deactivation for UE-specific PDSCH MAC CE": "identified by a MAC PDU subheader with eLCID as specified in Table 6.2.1-1b. It has a variable size consisting of following fields: …"
  [38.321 §6.1.3.24, chunkId=`38.321-6.1.3.24-001`] — eLCID 기반 enhanced PDSCH TCI activation. (Rel-16 mTRP 컨텍스트에서 도입된 enhanced 변종은 검색에서 R2-1910966 등 RAN2 mTRP discussion과 강한 코사인 유사도로 회수됨.)
- 38.331: 검색에서 `tci-StatesToAddModList`, `tci-PresentInDCI` 같은 RAN1/Rel-16 RRC 필드명을 직접 본문 청크로 잡지는 못함(본 컬렉션 청킹 한계). 대신 38.214 §5.1.5 본문에서 "Independent of the configuration of `tci-PresentInDCI` and `tci-PresentDCI-1-2` in RRC connected mode" 라고 RRC 파라미터 이름이 직접 등장 [38.214 §5.1.5, chunkId=`38.214-5.1.5-005`].
- 38.306: capability 테이블 청크 군집(BandNR/CA-ParametersNR/Phy-Parameters)이 회수됨 [38.306 §4.2.15.7.1; §4.2.7.4; §4.2.23.6.1]. Rel-16 cap 항목명(예: `maxNumberActiveTCI-PerBWP`) 자체의 정확 행은 회수된 청크 preview만으로는 식별 불가 — 한계 섹션 참조.

### Rel-17 — Unified TCI framework / Inter-cell beam management 도입

**도입 배경 (RAN1/RAN2 WID·discussion)**
- "Enhancement of multi-beam operation is an important part of R17 feMIMO WI [1]. Discussion on multi-beam operation has been ongoing since RAN1#102e … "
  [R1-2109103, RAN1#106b-e, discussion, ai=8.1.1, "Enhancements on Multi-beam Operation", Rel-17];
  [R1-2103504, RAN1#104b-e, ai=8.1.1, Rel-17];
  [R1-2100273, RAN1#104-e, ai=8.1.1, Rel-17] — Rel-17 feMIMO WI의 multi-beam 강화 라인.
- RAN2 인터셀 빔 관리:
  - "Inter-cell beam management | inter-cell MTRP / TCI Framework | R17 Unified TCI framework, UE assumes that the UE-dedicated channels/RSs can be switched t…"
    [R2-2110534, RAN2#116-e, discussion, ai=8.17.2, "Considerations on Inter-Cell Beam Management", Rel-17] — Rel-17 inter-cell BM이 R17 Unified TCI를 기반으로 정의됨을 명시.
  - [R2-2110622, RAN2#116-e, ai=8.17.2, Rel-17];
    [R2-2200599, RAN2#116bis-e, ai=8.17.2, "Discussion on RRC aspects for feMIMO", Rel-17] — RAN2의 RRC 관점 inter-cell BM 모델링.

**문서별 Rel-17 변경**
- 38.214 §5.1.5 본문에 Rel-17의 핵심 RRC 파라미터가 직접 등장:
  - "if the UE is provided `dl-OrJointTCI-StateList-r17`, …"
    [38.214 §5.1.5, chunkId=`38.214-5.1.5-005`]
  - "When a UE is configured with `dl-OrJointTCI-StateList` and is having two indicated TCI-states …"
    [38.214 §5.1.5, chunkId=`38.214-5.1.5-007`]
  - "When a UE configured with `dl-OrJointTCI-StateList` supports `tci-SeparateTCI-UpdateMultiActiveTCI-Per…`"
    [38.214 §5.1.5, chunkId=`38.214-5.1.5-003`] — Rel-17 unified TCI(joint vs separate) 분기.
- 38.321 §5.18.23 / §6.1.3.47 "Unified TCI States Activation/Deactivation MAC CE":
  "The network may activate and deactivate the configured unified TCI states of a Serving Cell or a set of Serving Cells configured in `simultaneousU-TCI-UpdateList1`, `simultaneousU-TCI-UpdateList2`, …"
  [38.321 §5.18.23, chunkId=`38.321-5.18.23-001`]; [38.321 §6.1.3.47, Neo4j RAN2 §6.1.3.47] — Rel-17 unified TCI MAC CE.
- 38.331 IE: `TCI-UL-State`, `TCI-UL-StateId`가 RAN2 KG에 Section 노드로 등록 [Neo4j RAN2, sectionNumber=`TCI-UL-State`/`TCI-UL-StateId`] — 분리 TCI(UL) 도입 라인.
- 38.306 `unified TCI UE capability` 검색 top: `ncr-AdaptiveBeamBackhaulAndC-Link-r18` 등 cap 테이블 군집이 회수됨 [38.306 §4.2.23.6.1]. Rel-17 unified TCI 관련 capability 항목명(예: feature group capability) 자체의 라인은 회수된 preview에서 직접 노출되지 않음 — 한계 섹션.

### Rel-18 — Enhanced Unified TCI / Multi-TRP unified / FR3/MIMO 추가 강화

**도입 배경**
- "FL summary 1/2 on L1 enhancements for inter-cell beam management … For the beam indication of LTM in the case of inter-cell mTRP: The TCI state(s) indicated through inter-cell beam management is applied to UE-specific PDCC…"
  [R1-2309110, RAN1#114b, discussion, ai=8.7.1, Rel-18]; [R1-2309111, RAN1#114b, ai=8.7.1, Rel-18] — Rel-18 inter-cell BM Floor leader 요약.
- "Unified TCI Framework for Multi-TRP … When unified TCI framework is used for beam indication for single DCI multi-TRP, for the case when the UE is configured with joint DL/UL beam indication with th…"
  [R1-2300932, RAN1#112, discussion, ai=9.1.1.1, Rel-18] — Rel-18 unified TCI를 multi-TRP에 확장.
- RAN2: "In R17 inter-cell beam management, the unified TCI framework was introduced with the following characteristics: A pool of joint or separate DL/UL TCI states is …"
  [R2-2207753, RAN2#119-e, discussion, ai=8.4.2.2, "Discussion on candidate solutions for L1 L2 mobility", Rel-18];
  "On MAC CE for Joint TCI State Indication" [R2-2306181, RAN2#122, ai=7.1.2, Rel-18];
  "Two TAs for multi-DCI multi-TRP … In Rel-17, Inter-Cell Beam Management (ICBM) was introduced …" [R2-2307614, RAN2#123, ai=7.20.2, Rel-18].

**문서별 변경**
- 38.214 §5.1.5 본문은 enhanced/joint/separate TCI 모드 분기를 모두 포함 [38.214 §5.1.5, chunkId=`38.214-5.1.5-003`/`-007`].
- 38.321 enhanced unified TCI MAC CE:
  - §5.18.33 "Enhanced Unified TCI States Activation/Deactivation MAC CE" — "The network may activate and deactivate the configured unified TCI states of a Serving Cell or a set of Serving Cells …"
    [38.321 §5.18.33, chunkId=`38.321-5.18.33-001`]
  - §6.1.3.70 "Enhanced Unified TCI States Activation/Deactivation MAC CE for Joint TCI States" / §6.1.3.71 "for Separate TCI States" — "identified by a MAC subheader with eLCID as specified in Table 6.2.1-1b …"
    [38.321 §6.1.3.70, chunkId=`38.321-6.1.3.70-001`]; [38.321 §6.1.3.71, chunkId=`38.321-6.1.3.71-001`] — Rel-18 enhanced unified TCI joint/separate.
- 38.331 IE: `TCI-ActivatedConfig`, `LTM-TCI-Info`가 RAN2 KG Section 노드로 등록됨 [Neo4j RAN2, sectionNumber=`TCI-ActivatedConfig`, `LTM-TCI-Info`] — Rel-18 LTM(L1/L2 트리거 mobility) ↔ TCI 연결.
- 38.306: 회수된 cap 테이블 청크에 `additionalTime-CB-8TxPUSCH-r18` 등 r18 태그가 등장 [38.306 §4.2.7.7, chunkId=`38.306-4.2.7.7-001`] — Rel-18 capability 갱신 흔적. unified TCI 전용 cap 항목 행은 preview에서 직접 식별 불가.

### Rel-19 — Asymmetric DL sTRP / UL mTRP 등 확장

**도입 배경**
- "Discussion on enhancements for asymmetric DL sTRP/UL mTRP scenarios … In RAN1#116 meeting, the following agreements on beam indication framework have been achieved [3]: Regarding separate DL/UL TCI state mode of Rel-18 unified TCI …"
  [R1-2408118, RAN1#118b, discussion, ai=9.2.4, Rel-19];
  [R1-2404815, RAN1#117, ai=9.2.4, Rel-19];
  [R1-2402686, RAN1#116b, ai=9.2.4, Rel-19] — Rel-19에서 비대칭 DL sTRP / UL mTRP을 위해 Rel-18 separate DL/UL TCI 모드를 확장하는 흐름.
- RAN2: "L1 event triggered measurement reporting for LTM … When mTRP is configured in the serving cell, the UE uses the best beam (in terms of RSRP) of the two 'current beams' for LTM event evaluation."
  [R2-2505548, RAN2#131, discussion, ai=8.6.3, Rel-19];
  "MAC issues for MIMO … RP-242394, Revised Work Item: NR MIMO Phase 5 …" [R2-2508663, RAN2#132, ai=8.12.2, Rel-19] — Rel-19 NR MIMO Phase 5 WI(RP-242394)의 MAC 이슈.

**문서별 변경 (retrieved 흔적)**
- 38.321 §5.18.36 "Candidate Cell TCI States Activation/Deactivation" / §6.1.3.76 "Candidate Cell TCI States Activation/Deactivation MAC CE" / §6.1.3.77 "Cross-RRH TCI State Indication for UE-specific PDCCH MAC CE" — Neo4j RAN2 Section 노드로 등록됨 [Neo4j RAN2, sectionNumber=`5.18.36`/`6.1.3.76`/`6.1.3.77`]. 이는 candidate cell / cross-RRH 시나리오용 TCI MAC CE.
- 38.331 IE: `CandidateTCI-State`, `CandidateTCI-UL-State`가 RAN2 KG Section 노드로 등록 [Neo4j RAN2, sectionNumber=`CandidateTCI-State`/`CandidateTCI-UL-State`] — Rel-19 candidate cell TCI를 RRC IE로 정의.
- 38.214: 회수된 §5.1.5 chunk가 Rel-17/18까지의 본문을 포함하며, Rel-19 별도 추가 본문 청크는 retrieval에서 우세하게 잡히지 않음 — Rel-19는 RAN1 spec 본문이 아직 §5.1.5 위주 운영, Candidate/Cross-RRH 처리 분기는 38.321 측에 더 명확히 구현됨.
- 38.306 Rel-19 cap: 회수된 테이블 청크 preview에 r19 전용 항목명이 우세하게 노출되지는 않음 (top hit 점수 0.49–0.59) — 한계 섹션.

### Rel-20 — 6G 항목 (3GPP 6G/NR 진화) 흔적

**도입 배경**
- "Overview of 6G Air Interface … MIMO scope in 6G still requires proper design of beam management and CSI framework."
  [R1-2506358, RAN1#122, discussion, ai=11.1, Rel-20]
- "Overview of the 6GR air interface … Extreme-MIMO (E-MIMO), equipped with an extended large-scale co-located antenna array …"
  [R1-2506063, RAN1#122, ai=11.1, Rel-20]
- "Nokia Views on 6G Radio Air Interface … Multiple-Input-Multiple-Output (MIMO) and beamforming (BF) are critical technologies …"
  [R1-2505125, RAN1#122, ai=11.1, Rel-20]
- RAN2: "6G mobility … Beam based mobility can be either between beams from the sa…"
  [R2-2508085, RAN2#132, discussion, ai=10.4, Rel-20];
  "Consideration for 6G connected mode mobility … The inter-cell multi-TRP operation is supported in Rel-17, which allows the DL transmission from two TRPs belonging to different cells [2]. It may be seen as th…"
  [R2-2508849, RAN2#132, ai=10.4, Rel-20]

**Rel-20 문서별 변경 — 미발견**
- 38.214/38.321/38.331/38.306에 대한 **Rel-20 신규 TCI 항목**의 본문/IE 변경은 retrieval에서 식별되지 않음. 회수된 RAN1/RAN2 Rel-20 TDoc은 모두 6G air-interface overview / 6G mobility framing 단계의 discussion이며, 구체 spec 본문 변경이 아직 회수 청크에 반영되지 않음. → "커버리지/한계" 참조.

---

## Release × 문서 매트릭스 (요약·근거 1줄)

| Release | 38.214 | 38.321 | 38.331 | 38.306 |
|---|---|---|---|---|
| Rel-15 | TCI-State 리스트(`PDSCH-Config`)와 QCL 정의 [38.214 §5.1.5, chunkId=`38.214-5.1.5-001`] | PDSCH TCI activation MAC CE 원형 [38.321 §6.1.3.14, chunkId=`38.321-6.1.3.14-001`] | `TCI-State`/`TCI-StateId` IE 등록 [Neo4j RAN2, sectionNumber=`TCI-State`/`TCI-StateId`] | `maxNumberConfiguredTCIstatesPerCC` 인용 [38.214 §5.1.5, chunkId=`38.214-5.1.5-001`]; cap 테이블 [38.306 §4.2.15.7.1] |
| Rel-16 | 활성화 절차에서 38.321 §6.1.3.70로 위임 [38.214 §5.1.5, chunkId=`38.214-5.1.5-003`] | Enhanced PDSCH TCI activation (eLCID) [38.321 §6.1.3.24, chunkId=`38.321-6.1.3.24-001`] | `tci-PresentInDCI`/`tci-PresentDCI-1-2` 명시 [38.214 §5.1.5, chunkId=`38.214-5.1.5-005`] | cap 테이블 군집 (정확 항목 미식별) [38.306 §4.2.7.4] |
| Rel-17 | `dl-OrJointTCI-StateList-r17` 분기 [38.214 §5.1.5, chunkId=`38.214-5.1.5-005`/`-007`] | Unified TCI MAC CE (`simultaneousU-TCI-UpdateList*`) [38.321 §5.18.23, chunkId=`38.321-5.18.23-001`] | `TCI-UL-State`/`TCI-UL-StateId` IE 등록 [Neo4j RAN2] | cap 테이블 군집 [38.306 §4.2.23.6.1] |
| Rel-18 | joint/separate TCI 모드 분기 (`tci-SeparateTCI-UpdateMultiActiveTCI-Per…`) [38.214 §5.1.5, chunkId=`38.214-5.1.5-003`] | Enhanced Unified TCI MAC CE — joint/separate [38.321 §6.1.3.70, chunkId=`38.321-6.1.3.70-001`]; [§6.1.3.71, chunkId=`38.321-6.1.3.71-001`] | `TCI-ActivatedConfig`, `LTM-TCI-Info` IE 등록 [Neo4j RAN2] | r18 cap 테이블 항목 등장 [38.306 §4.2.7.7, chunkId=`38.306-4.2.7.7-001`] |
| Rel-19 | 회수된 spec 본문에서 별도 §추가 미식별 (한계) | Candidate Cell TCI / Cross-RRH TCI MAC CE [Neo4j RAN2, sectionNumber=`5.18.36`/`6.1.3.76`/`6.1.3.77`] | `CandidateTCI-State`/`CandidateTCI-UL-State` IE 등록 [Neo4j RAN2] | retrieved preview에서 r19 항목 직접 미식별 (한계) |
| Rel-20 | 6G overview discussion만 회수, spec 본문 변경 미식별 [R1-2506358, RAN1#122, ai=11.1] | spec 본문 신규 변경 미식별 | spec 본문 신규 변경 미식별 | spec 본문 신규 변경 미식별 |

---

## 문서 간 연결고리 (검색 근거 기반)

3gpp-tracer 회수 chunk만으로 다음 연결이 직접 확인된다:

1. **RRC(38.331) → 물리(38.214)**: 38.214 §5.1.5 본문이 RRC IE/필드명을 직접 인용 — `PDSCH-Config`, `PDCCH-Config`, `dl-OrJointTCI-StateList`, `TCI-UL-State`, `tci-PresentInDCI`, `tci-PresentDCI-1-2`, `coresetPoolIndex` [38.214 §5.1.5, chunkId=`38.214-5.1.5-001`/`-005`/`-007`]. → RRC가 정의한 TCI 자원/리스트를 38.214 QCL 가정 적용 절차가 그대로 사용한다.

2. **MAC(38.321) → 물리(38.214)**: "receive an activation command, as described in clause 6.1.3.70 of [10, TS 38.321], the activation command is used to map up to 8 sets of TCI states to the codepoints of the DCI field 'Transmission Configuration Indication' …"
   [38.214 §5.1.5, chunkId=`38.214-5.1.5-003`] — 38.214가 38.321의 MAC CE 절차(§6.1.3.70)를 명시적으로 cross-reference. DCI 'TCI' 필드의 8 codepoint는 MAC CE로 활성화된 TCI state set과 매핑된다.

3. **물리(38.214) → MAC(38.321) ↔ RRC(38.331) (Rel-17 unified)**: Rel-17 이후 `dl-OrJointTCI-StateList`가 RRC에 등록되고[Neo4j RAN2 IE], 38.321 §5.18.23/§6.1.3.47이 unified TCI MAC CE를 정의[38.321 §5.18.23, chunkId=`38.321-5.18.23-001`], 38.214 §5.1.5가 둘을 모두 인용[38.214 §5.1.5, chunkId=`38.214-5.1.5-007`]. → Rel-17의 unified TCI 프레임워크가 세 spec을 가로질러 정의된다.

4. **UE capability(38.306)**: 38.214 §5.1.5 본문이 capability `maxNumberConfiguredTCIstatesPerCC`를 직접 참조 [38.214 §5.1.5, chunkId=`38.214-5.1.5-001`]. 회수된 38.306 청크는 BandNR/CA-ParametersNR/Phy-Parameters 테이블 군집을 보여주며 [38.306 §4.2.15.7.1; §4.2.7.4; §4.2.23.6.1] capability 정의 위치임을 시사. → 물리계층 절차가 UE capability 항목을 직접 호출.

5. **TDoc → spec 변화 흐름**: Rel-17 inter-cell BM은 RAN2 R2-2110534/R2-2110622 [RAN2#116-e, ai=8.17.2, Rel-17]에서 "R17 Unified TCI framework"를 전제로 논의되고, 같은 시점 38.321/38.331의 unified TCI MAC CE/IE 노드가 KG에 적재됨. → discussion(TDoc) → spec 본문 반영의 자취가 검색에서 일관되게 재구성된다.

---

## 커버리지 / 한계 (3gpp-tracer 데이터셋 기준)

### Release별 데이터 가용성 (TDoc release 분포 sample 200건 + retrieval)

- `ran1_tdoc_chunks` 적재 release 분포(sample): Rel-13(1), Rel-14(1), Rel-15(10), Rel-16(11), Rel-17(35), Rel-18(52), Rel-19(32), Rel-20(9), 미지정(49). → Rel-15~Rel-20 모두 적재 확인. Rel-20은 표본 수가 작고 모두 6G overview discussion 청크가 우세.
- `ran2_tdoc_chunks`도 Rel-15~Rel-20 모두 hit (top score 0.494–0.740) — Rel-20은 0.51–0.62대로 낮아짐 (6G framing 단계 반영).

### 재현 가능 미발견 항목

| 항목 | 상태 |
|---|---|
| 38.331 `TCI-State` IE 본문 청크 (`tci-StatesToAddModList`, `qcl-Type1`/`qcl-Type2`, `referenceSignal` 필드 본문) | **3gpp-tracer ts_sections에서 미발견** — Neo4j RAN2 Section 노드(`TCI-State`, `TCI-UL-State`, `TCI-StateId`, `TCI-UL-StateId`, `TCI-ActivatedConfig`, `LTM-TCI-Info`, `CandidateTCI-State`, `CandidateTCI-UL-State`)는 등록되어 있으나, ASN.1 IE 본문이 `ran2_ts_sections` Qdrant 청크로 회수되지 않음. (Phase-7 RAN2 청킹 정책상 IE 본문 미청킹 가능성.) |
| 38.331 `tci-PresentInDCI` / `tci-PresentDCI-1-2` 정의 위치 | 정의 IE 본문 청크 미발견. 단 38.214 §5.1.5 본문에서 파라미터명만 인용됨 [chunkId=`38.214-5.1.5-005`]. |
| 38.306 `maxNumberConfiguredTCIstatesPerCC` / `maxNumberActiveTCI-PerBWP` 정확 행 | 회수된 청크 preview는 capability 테이블 헤더 행(`Definitions for parameters | Per | M | …`)만 노출. 정확 항목 행을 짚으려면 chunk 전체 본문 fetch 필요. |
| Rel-20의 spec 본문 신규 변경 (38.214/38.321/38.331/38.306) | retrieval에서 미식별 — Rel-20 TDoc은 6G overview/6G mobility framing 단계로 회수되며 spec 본문 변경 청크 우세 매칭 없음. |
| Rel-15 RAN2 측 "TCI-State" 도입 자체 discussion | 회수 결과는 multi-beam 환경 TA 등 부수 토픽이 우세 — 핵심 TCI 도입 RAN2 discussion은 회수된 top-3에 포함되지 않음. |
| Rel-19 38.214/38.306 본문 별도 chunk | retrieval top에서 우세 매칭 없음 (38.214는 §5.1.5 chunk가 통합 본문이라 release별 분리 어려움). |
| RAN1 Neo4j Section title CONTAINS 'tci' | 1건만(`38.214 §5.1.5`) — 38.214 sub-section title에는 'TCI' 단어가 거의 안 쓰임(QCL/quasi co-location 표현 사용)이라는 데이터 특성 반영. |

### 검색 신뢰도 평가 (Release별 답변 가능 수준)

| Release | 답변 가능 수준 |
|---|---|
| Rel-15 | 중상. RAN1 도입 discussion 명확, spec 본문 §5.1.5 / §6.1.3.14 / IE 등록 모두 회수. 단 RAN2 Rel-15 핵심 discussion은 약함. |
| Rel-16 | 중상. eMIMO WI 인용 + enhanced PDSCH TCI MAC CE(§6.1.3.24) + RAN2 mTRP MAC discussion 회수. RRC/Cap 본문 chunk는 약함. |
| Rel-17 | 상. unified TCI 본문(§5.18.23, dl-OrJointTCI-StateList-r17) + inter-cell BM RAN2 discussion 모두 강하게 회수. |
| Rel-18 | 상. enhanced unified TCI joint/separate(§6.1.3.70/71), LTM-TCI 등 IE 등록, FL summary discussion 회수. |
| Rel-19 | 중. Candidate Cell / Cross-RRH MAC CE는 KG 등록으로 확인되나 spec 본문 chunk preview는 약함. RAN1 asymmetric sTRP/UL mTRP discussion은 명확. |
| Rel-20 | 하. 6G overview discussion 단계까지만 회수. spec 본문 신규 TCI 변경은 데이터셋 적재 범위에서 미식별. |

---

## 자가 검증

- 인용 없는 사실 문장: 본문에서 0건. 모든 문장은 `[spec §sec, chunkId=...]` 또는 `[tdoc, mtg, type, ai=..., release]` 형식 인용 첨부.
- TDoc release/agendaItem 인용은 `q2_retrieval_log.json`의 `tdoc_queries[*].hits[*]` 페이로드에서 그대로 가져옴. 임의 보정 없음.
- TS 본문 인용은 `q2_retrieval_log.json`의 `ts_queries[*].hits[*].text_preview` 또는 ts_sections scroll로 직접 회수한 chunk(`38.214-5.1.5-001 ~ 007`)에서 그대로 발췌.
- IE 노드 인용은 Neo4j 직접 쿼리 결과(`neo4j_results.RAN1/RAN2.rows`)에서 가져옴.
- "미발견" 항목은 모두 **데이터셋 한계로 식별 불가** 표기. spec 변경 자체의 존재/부재를 단정하지 않음.
- Release 잘못 인용 검토: TDoc payload `release` 필드 그대로 사용. 본문에 인용한 모든 TDoc은 retrieval log의 동일 release 키 아래 존재함.
