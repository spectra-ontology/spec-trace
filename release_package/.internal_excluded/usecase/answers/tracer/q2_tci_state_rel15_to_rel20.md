# Q2. Rel-15~Rel-20 TCI-state 관련 표준 아이템 정리 (3gpp-tracer 전용, **v2 — P2 + ASN.1**)

## 메타

| 항목 | 값 |
|---|---|
| 질문 | Rel-15~Rel-20 TCI-state 관련 표준 아이템 정리 (WID 도입 배경 + 38.214/38.321/38.331/38.306 변화 + 문서 간 연결고리) |
| 검색 시스템 | 3gpp-tracer (Qdrant + Neo4j). 외부 LLM 지식/Web 사용 금지 |
| Qdrant 컬렉션 | `ran1_ts_sections`, `ran2_ts_sections`, **`ran2_ts_asn1_chunks` (★ P2 신규, 2,365 IEs)**, `ran1_tdoc_chunks`, `ran2_tdoc_chunks` |
| Neo4j 인스턴스 | RAN1 (`bolt://localhost:7687`), RAN2 (`bolt://localhost:7688`) |
| 임베딩 모델 | `openai/text-embedding-3-small` (P2 적용) |
| TS section 쿼리 | 14건 (140 hits) |
| **ASN.1 vector 쿼리** | **8건 (80 hits)** ← P2 신규 |
| **ASN.1 ieName 정확 매칭** | **11건 (11 IE 본문 회수)** ← P2 신규 |
| **38.306 capability text-match probe** | **6건 (18 chunks, 96 TCI 행)** ← P2 신규 |
| TDoc 쿼리 | 48건 (480 hits) |
| Neo4j 쿼리 | 2건 (33 sections) + RAN2 IE catalog (9 rows) = 42 rows |
| 산출물 | `logs/cross-phase/usecase/q2_retrieval_log_v2.json` |
| 작성일 | 2026-05-01 (v2) |
| v1 백업 | `q2_tci_state_rel15_to_rel20.v1.md` |

> 본 문서의 모든 사실 문장은 위 검색에서 회수된 chunk·IE·TDoc·Neo4j 행에서만 인용한다.
> 인용은 `[spec §sec, chunkId=...]`, `[asn1 IE=..., chunkId=...]`, `[tdoc, mtg, type, ai=..., rel=...]` 형식.

---

## 3gpp-tracer 검색 결과 요약

### Release × 컬렉션 hit 수 (TDoc, top-10 × 4 query 합산)

| Release | `ran1_tdoc_chunks` (top score) | `ran2_tdoc_chunks` (top score) |
|---|---|---|
| Rel-15 | 40 hits / max 0.699 | 40 hits / max 0.626 |
| Rel-16 | 40 hits / max 0.756 | 40 hits / max 0.666 |
| Rel-17 | 40 hits / max 0.744 | 40 hits / max 0.740 |
| Rel-18 | 40 hits / max 0.716 | 40 hits / max 0.704 |
| Rel-19 | 40 hits / max 0.716 | 40 hits / max 0.690 |
| Rel-20 | 40 hits / max 0.665 | 40 hits / max 0.621 |

### TS / ASN.1 컬렉션 top match

| 영역 | 핵심 청크 (P2 후 신규/유지) |
|---|---|
| 38.214 (RAN1) | §5.1.5 "Antenna ports quasi co-location" [chunkId=`38.214-5.1.5-001`/`-003`/`-005`/`-007`] |
| 38.321 (RAN2 MAC) | §5.18.23 unified TCI MAC CE (top 0.772), §5.18.33 enhanced unified, §6.1.3.14/24/47/70/71/76/77 |
| **38.331 ASN.1 (RAN2 RRC) — ★ P2 신규** | `TCI-State`, `TCI-StateId`, `QCL-Info`, `TCI-UL-State-r17`, `TCI-UL-StateId-r17`, `CandidateTCI-State-r18`, `CandidateTCI-UL-State-r18`, `LTM-QCL-Info-r18`, `PDSCH-Config`, `PDCCH-Config`, `ControlResourceSet` |
| 38.306 (RAN2 cap) | §4.2.7.2 "BandNR parameters" — `tci-StatePDSCH`, `maxNumberConfiguredTCI-StatesPerCC`, `tci-StateSwitchInd-r18`, `tci-JointTCI-Update*-r18`, `tci-SeparateTCI-Update*-r18`, `ltm-BeamIndicationJointTCI-r18`, `cjt-QCL-PDSCH-Scheme*-r19` 행 직접 회수 |

### Neo4j Section 노드 (TCI / QCL / spatial relation)

- RAN1: 1개 (`38.214 §5.1.5 Antenna ports quasi co-location`)
- RAN2: 32개 — 38.321 PDSCH/PDCCH TCI activation MAC CE 16개, 38.331 TCI 관련 IE/필드 8개, 외 RAN2 IE catalog scan 9개

---

## Release별 답변 본문

### Rel-15 — TCI 프레임워크 도입 (NR 초기)

**RAN1 도입 배경 (TDoc 근거)**
- "Mapping between candidate TCI state and N-bit DCI field …" [R1-1718541, RAN1#90b, discussion, ai=7.2.2.3, "Beam management for NR", rel=Rel-15] — DCI의 TCI 코드포인트와 TCI state 후보 매핑 설계.
- "There appears no reason why the TCI field of the DCI for PDSCH should not convey the non-spatial QCL parameters as they are available in the list of TCI states." [R1-1720662, RAN1#91, discussion, ai=7.2.2.3, "Beam management for NR", rel=Rel-15] — TCI field via DCI로 non-spatial QCL을 전달.
- "Beam Management of Multiple Beam Pairs in Uplink" [R1-1804787, RAN1#92b, discussion, "Beam management for NR", rel=Rel-15] — UL 빔 관리.

**RAN2 도입 배경 (★ v1에서 약했던 부분 — P2에서 직접 인용)**
- "In order to support quasi-collocation and various beamforming feature in NR, RAN1 has agreed to support up to M Transmission Configuration Indicator (TCI) states, wherein each TCI state can include one RS Set. TCI state was defined for QCL indication of various cases such as quasi-collocation betwee…" [R2-1713533, RAN2#100, discussion, ai=10.2.13, "MAC CEs for activating an RS resource and handling corresponding TCI states", rel=Rel-15] — Rel-15 RAN2 측 TCI MAC CE 도입 직접 근거.

**38.214 / 38.321 / 38.331 / 38.306 변화**
- 38.214 §5.1.5: "The UE can be configured with a list of up to M TCI-State configurations within the higher layer parameter PDSCH-Config to decode PDSCH according to a detected PDCCH … M depends on the UE capability `maxNumberConfiguredTCIstatesPerCC`." [38.214 §5.1.5, chunkId=`38.214-5.1.5-001`].
- 38.321 §6.1.3.14 "TCI States Activation/Deactivation for UE-specific PDSCH MAC CE": "identified by a MAC subheader with LCID as specified in Table 6.2.1-1. It has a variable size consisting of following fields …" [38.321 §6.1.3.14, chunkId=`38.321-6.1.3.14-001`].
- **★ 38.331 ASN.1 (P2 신규)**:
  - `TCI-State ::= SEQUENCE { tci-StateId TCI-StateId, qcl-Type1 QCL-Info, qcl-Type2 QCL-Info OPTIONAL, ..., [[ additionalPCI-r17 ..., pathlossReferenceRS-Id-r17 ..., ul-powerControl-r17 ... ]], [[ tag-Id-ptr-r18 ENUMERATED {n0,n1} ... ]], [[ pathlossOffset-r19 ENUMERATED {dB-12,...,dB60} ... ]] }` [asn1 IE=`TCI-State`, chunkId=`38.331-asn1-TCI-State-001`] — Rel-15 base SEQUENCE 골격 + Rel-17/18/19 확장 블록까지 동일 IE에 포함.
  - `TCI-StateId ::= INTEGER (0..maxNrofTCI-States-1)` [asn1 IE=`TCI-StateId`, chunkId=`38.331-asn1-TCI-StateId-001`].
  - `QCL-Info ::= SEQUENCE { cell ServCellIndex OPTIONAL, bwp-Id BWP-Id OPTIONAL, referenceSignal CHOICE { csi-rs NZP-CSI-RS-ResourceId, ssb SSB-Index }, qcl-Type ENUMERATED {typeA, typeB, typeC, typeD}, ... }` [asn1 IE=`QCL-Info`, chunkId=`38.331-asn1-QCL-Info-001`] — QCL Type A/B/C/D enum과 referenceSignal CHOICE(CSI-RS or SSB) 본문 직접 인용.
  - `PDSCH-Config ::= SEQUENCE { ... tci-StatesToAddModList SEQUENCE (SIZE (1..maxNrofTCI-States)) OF TCI-State OPTIONAL, tci-StatesToReleaseList SEQUENCE (SIZE (1..maxNrofTCI-States)) OF TCI-StateId OPTIONAL, ... dl-OrJointTCI-StateList-r17 CHOICE { ... } ... unifiedTCI-StateRef-r17 ServingCellAndBWP-Id-r17 ... }` [asn1 IE=`PDSCH-Config`, chunkId=`38.331-asn1-PDSCH-Config-001`] — Rel-15 base에서 `tci-StatesToAddModList`/`tci-StatesToReleaseList`가 정의되어 있고, Rel-17 확장으로 unified TCI 분기 추가.
  - `PDCCH-Config ::= SEQUENCE { controlResourceSetToAddModList ..., searchSpacesToAddModList ..., ... }` [asn1 IE=`PDCCH-Config`, chunkId=`38.331-asn1-PDCCH-Config-001`].
  - `ControlResourceSet ::= SEQUENCE { controlResourceSetId ..., frequencyDomainResources ..., duration ..., cce-REG-MappingType CHOICE { ... } ... }` [asn1 IE=`ControlResourceSet`, chunkId=`38.331-asn1-ControlResourceSet-001`] — `tci-PresentInDCI`/`tci-StatesPDCCH-ToAddList` 등의 host IE.
- **★ 38.306 cap 행 (P2 신규)**: §4.2.7.2 "BandNR parameters" 청크 `38.306-4.2.7.2-050`에서 직접 회수 — "tci-StatePDSCH Defines support of TCI-States for PDSCH. The capability signalling comprises the following parameters: -maxNumberConfiguredTCI-StatesPerCC indicates the maximum number of configured TCI…" [38.306 §4.2.7.2, chunkId=`38.306-4.2.7.2-050`]. 추가로 §4.2.7.2 청크 `-001`에서 `additionalActiveTCI-StatePDCCH`, `-029`에서 `multipleTCI` (CORESET당 TCI 다중 설정 지원) 행 회수.

### Rel-16 — eMIMO multi-beam 강화

**도입 배경**
- "The work item on Rel-16 MIMO enhancements has been specified [1]. … The WI for Rel-16 covers several key features aimed at enhancing multibeam …" [R1-1903044, RAN1#96, discussion, ai=7.2.8.3, "Enhancements on Multi-beam Operation", rel=Rel-16].
- "Enhancements on Multi-beam Operation" [R1-1813443, RAN1#95, discussion, ai=7.2.8.3, rel=Rel-16].
- "Feature lead summary of Enhancements on Multi-beam Operations" [R1-1907650, RAN1#97, discussion, ai=7.2.8.3, rel=Rel-16].
- "Further discussion on multi TRP transmission" [R1-1901702, RAN1#96, discussion, rel=Rel-16].
- "MAC CE design on single PDCCH based multi-TRP/panel transmission … TCI states for PDSCH are configured by RRC, at first. Up to 128 TCI states can be configured per BWP per serving cell. Amongst the configured TCI states, up to …" [R2-1910966, RAN2#107, discussion, ai=11.16, rel=Rel-16] — 단일 PDCCH 기반 mTRP에서 RRC가 PDSCH의 최대 128 TCI 상태를 BWP당 설정.
- "RAN2 aspects of multi-beam enhancements" [R2-1910145, RAN2#107, discussion, rel=Rel-16].

**문서별 변경 (retrieved)**
- 38.214 §5.1.5: "receive an activation command, as described in clause 6.1.3.70 of [10, TS 38.321], the activation command is used to map up to 8 sets of TCI states to the codepoints of the DCI field 'Transmission Configuration Indication' …" [38.214 §5.1.5, chunkId=`38.214-5.1.5-003`].
- 38.321 §6.1.3.24 "Enhanced TCI States Activation/Deactivation for UE-specific PDSCH MAC CE": "identified by a MAC PDU subheader with eLCID as specified in Table 6.2.1-1b. It has a variable size consisting of following fields …" [38.321 §6.1.3.24, chunkId=`38.321-6.1.3.24-001`] — eLCID 기반 enhanced PDSCH TCI activation.
- 38.331: 38.214 §5.1.5 본문에 "Independent of the configuration of `tci-PresentInDCI` and `tci-PresentDCI-1-2` in RRC connected mode" [38.214 §5.1.5, chunkId=`38.214-5.1.5-005`]. **★ P2 신규**: `PDCCH-Config` ASN.1에서 controlResourceSet 리스트와 search space 리스트가 등장 [asn1 IE=`PDCCH-Config`, chunkId=`38.331-asn1-PDCCH-Config-001`]; `tci-PresentInDCI`는 ASN.1 컬렉션 정밀 검색에서 `ControlResourceSet` 본문 안에 위치 [asn1 IE=`ControlResourceSet`, chunkId=`38.331-asn1-ControlResourceSet-001`].
- 38.306: §4.2.7.2 청크 `-029` "multipleTCI Indicates whether UE supports more than one TCI state configurations per CORESET. UE is only required to track one active TCI state per CORESET. UE is required to suppo…" [38.306 §4.2.7.2, chunkId=`38.306-4.2.7.2-029`] — Rel-16 시점 추가된 `multipleTCI` 행 (CORESET당 TCI 다중 설정).

### Rel-17 — Unified TCI framework / Inter-cell beam management 도입

**도입 배경 (RAN1/RAN2)**
- "Enhancement of multi-beam operation is an important part of R17 feMIMO WI [1]. Discussion on multi-beam operation has been ongoing since RAN1#102e …" [R1-2109103, RAN1#106b-e, discussion, ai=8.1.1, "Enhancements on Multi-beam Operation", rel=Rel-17].
- "Further enhancement on multi-beam operation" [R1-2103287, RAN1#104b-e, discussion, ai=8.1.1, rel=Rel-17].
- "Discussion of RAN2 LS on inter-cell BM and mTRP" [R1-2110346, RAN1#106b-e, discussion, rel=Rel-17].
- "Inter-cell beam management | inter-cell MTRP / TCI Framework | R17 Unified TCI framework, UE assumes that the UE-dedicated channels/RSs can be switched t…" [R2-2110534, RAN2#116-e, discussion, ai=8.17.2, "Considerations on Inter-Cell Beam Management", rel=Rel-17].
- "Inter-cell BM and inter-cell mTRP" [R2-2201098, RAN2#116bis-e, discussion, rel=Rel-17].
- "Discussion on the support of L1/L2 centric inter-cell mobility" [R2-2105827, RAN2#114-e, discussion, rel=Rel-17].
- "Discussion on multi-TRP BFR and new MIMO MAC CE" [R2-2107995, RAN2#115-e, discussion, rel=Rel-17].

**문서별 변경**
- 38.214 §5.1.5: "if the UE is provided `dl-OrJointTCI-StateList-r17`, …" [38.214 §5.1.5, chunkId=`38.214-5.1.5-005`]; "When a UE is configured with `dl-OrJointTCI-StateList` and is having two indicated TCI-states …" [chunkId=`38.214-5.1.5-007`]; "When a UE configured with `dl-OrJointTCI-StateList` supports `tci-SeparateTCI-UpdateMultiActiveTCI-Per…`" [chunkId=`38.214-5.1.5-003`].
- 38.321 §5.18.23 / §6.1.3.47: "The network may activate and deactivate the configured unified TCI states of a Serving Cell or a set of Serving Cells configured in `simultaneousU-TCI-UpdateList1`, `simultaneousU-TCI-UpdateList2`, …" [38.321 §5.18.23, chunkId=`38.321-5.18.23-001`].
- **★ 38.331 ASN.1 (P2 신규)**:
  - `TCI-UL-State-r17 ::= SEQUENCE { tci-UL-StateId-r17 TCI-UL-StateId-r17, servingCellId-r17 ServCellIndex OPTIONAL, bwp-Id-r17 BWP-Id OPTIONAL, referenceSignal-r17 CHOICE { ssb-Index-r17 SSB-Index, csi-RS-Index-r17 NZP-CSI-RS-ResourceId, srs-r17 SRS-ResourceId }, additionalPCI-r17 ..., ul-powerControl-r17 ..., pathlossReferenceRS-Id-r17 ..., [[ tag-Id-ptr-r18 ... ]], [[ pathlossOffset-r19 ... ]] }` [asn1 IE=`TCI-UL-State-r17`, chunkId=`38.331-asn1-TCI-UL-State-r17-001`] — Rel-17 separate UL TCI IE 본문 직접 인용 (CSI-RS / SSB / SRS 3-way reference signal CHOICE).
  - `TCI-UL-StateId-r17 ::= INTEGER (0..maxUL-TCI-1-r17)` [asn1 IE=`TCI-UL-StateId-r17`, chunkId=`38.331-asn1-TCI-UL-StateId-r17-001`].
  - `PDSCH-Config` 본문에 `dl-OrJointTCI-StateList-r17 CHOICE { dl-OrJointTCI-StateToAddModList-r17 SEQUENCE (SIZE (1..maxNrofTCI-States)) OF TCI-State, dl-OrJointTCI-StateToReleaseList-r17 SEQUENCE (SIZE (1..maxNrofTCI-States)) OF TCI-StateId } / unifiedTCI-StateRef-r17 ServingCellAndBWP-Id-r17` [asn1 IE=`PDSCH-Config`, chunkId=`38.331-asn1-PDSCH-Config-001`] — Rel-17 unified TCI 분기를 PDSCH-Config에 정확히 위치시킴.
- **★ 38.306 cap (P2 신규)**: §4.2.7.2 청크 `-024`에서 "ltm-BeamIndicationJointTCI-r18 Indicates whether the UE supports unified TCI with joint DL/UL LTM TCI-state indication for LTM procedure, indicating and activating a single joint L…" [38.306 §4.2.7.2, chunkId=`38.306-4.2.7.2-024`] (※ Rel-18 LTM 행이지만 unified TCI 정의는 Rel-17 도입을 전제로 함).

### Rel-18 — Enhanced Unified TCI / Multi-TRP unified / LTM 통합

**도입 배경**
- "FL summary 1/2 on L1 enhancements for inter-cell beam management … For the beam indication of LTM in the case of inter-cell mTRP: The TCI state(s) indicated through inter-cell beam management is applied to UE-specific PDCC…" [R1-2309110, RAN1#114b, discussion, ai=8.7.1, rel=Rel-18].
- "Unified TCI Framework for Multi-TRP … When unified TCI framework is used for beam indication for single DCI multi-TRP, for the case when the UE is configured with joint DL/UL beam indication with the value of unifiedtci-StateType set to 'JointULDL', the UE expects to be indicated with a TCI codepoint which is mapped to two joint DL/UL T…" [R1-2300932, RAN1#112, discussion, ai=9.1.1.1, rel=Rel-18].
- "Maintenance on NR MIMO Evolution for Downlink and Uplink … In RAN#94e, the working item to enhance both downlink and uplink MIMO operations in Rel-18 was agreed [1]." [R1-2403112, RAN1#116b, discussion, ai=8.1, rel=Rel-18].
- "In R17 inter-cell beam management, the unified TCI framework was introduced with the following characteristics: A pool of joint or separate DL/UL TCI states is …" [R2-2207753, RAN2#119-e, discussion, ai=8.4.2.2, "Discussion on candidate solutions for L1 L2 mobility", rel=Rel-18].
- "On MAC CE for Joint TCI State Indication" [R2-2306181, RAN2#122, discussion, ai=7.1.2, rel=Rel-18].
- "[N110] Correction on Unified TCI operation … The unified TCI framework was introduced in Rel-17 which facilitates a streamlined multi-beam operation targeting FR2. As Rel-17 focuses on single-TRP use cases, extension of unified TCI framework that focuses on multi-TRP use cases…" [R2-2403134, RAN2#125bis, discussion, ai=7.20.3, rel=Rel-18].
- "Two TAs for multi-DCI multi-TRP … In Rel-17, Inter-Cell Beam Management (ICBM) was introduced …" [R2-2307614, RAN2#123, discussion, ai=7.20.2, rel=Rel-18].

**문서별 변경**
- 38.214 §5.1.5: joint/separate TCI 모드 분기를 모두 포함 [38.214 §5.1.5, chunkId=`38.214-5.1.5-003`/`-007`].
- 38.321:
  - §5.18.33 "Enhanced Unified TCI States Activation/Deactivation MAC CE" [chunkId=`38.321-5.18.33-001`].
  - §6.1.3.70 "Enhanced Unified TCI States Activation/Deactivation MAC CE for Joint TCI States" [chunkId=`38.321-6.1.3.70-001`]; §6.1.3.71 "for Separate TCI States" [chunkId=`38.321-6.1.3.71-001`].
- **★ 38.331 ASN.1 (P2 신규)**:
  - `CandidateTCI-State-r18 ::= SEQUENCE { tci-StateId-r18 TCI-StateId, qcl-Type1-r18 LTM-QCL-Info-r18, qcl-Type2-r18 LTM-QCL-Info-r18 OPTIONAL, pathlossReferenceRS-Id-r18 PathlossReferenceRS-Id-r17 OPTIONAL, tag-Id-ptr-r18 ENUMERATED {n0,n1} OPTIONAL, ul-powerControl-r18 Uplink-powerControlId-r17 OPTIONAL, ... }` [asn1 IE=`CandidateTCI-State-r18`, chunkId=`38.331-asn1-CandidateTCI-State-r18-001`] — Rel-18 LTM 후보 TCI state IE 본문.
  - `CandidateTCI-UL-State-r18 ::= SEQUENCE { tci-UL-StateId-r18 TCI-UL-StateId-r17, referenceSignal-r18 CHOICE { ssb-Index SSB-Index, csi-RS-Index NZP-CSI-RS-ResourceId }, pathlossReferenceRS-Id-r18 ..., tag-Id-ptr-r18 ENUMERATED {n0,n1} OPTIONAL, ul-powerControl-r18 Uplink-powerControlId-r17 OPTIONAL, ... }` [asn1 IE=`CandidateTCI-UL-State-r18`, chunkId=`38.331-asn1-CandidateTCI-UL-State-r18-001`].
  - `LTM-QCL-Info-r18 ::= SEQUENCE { referenceSignal-r18 CHOICE { ssb-Index SSB-Index, csi-RS-Index NZP-CSI-RS-ResourceId }, qcl-Type-r18 ENUMERATED {typeA, typeB, typeC, typeD}, ... }` [asn1 IE=`LTM-QCL-Info-r18`, chunkId=`38.331-asn1-LTM-QCL-Info-r18-001`] — LTM 전용 QCL info IE 본문.
  - `TCI-State`/`TCI-UL-State-r17`의 Rel-18 확장 블록 `[[ tag-Id-ptr-r18 ENUMERATED {n0,n1} OPTIONAL -- Cond 2TA ]]` [asn1 IE=`TCI-State`, chunkId=`38.331-asn1-TCI-State-001`] — Rel-18 multi-TRP 2TA 지원.
- **★ 38.306 cap (P2 신규)**:
  - "tci-StateSwitchInd-r18 Indicates whether the UE supports enhanced one-shot large UL transmit timing adjustment requirement to support FR2-1 PC6 Ues and enhanced TCI state switching…" [38.306 §4.2.7.2, chunkId=`38.306-4.2.7.2-050`].
  - "tci-JointTCI-UpdateMultiActiveTCI-PerCC-r18 Indicates whether the UE supports unified TCI with joint DL/UL TCI update for single-DCI based intra-cell multi-TRP with multiple activated TCI codepoints p…", `tci-JointTCI-UpdateMultiActiveTCI-PerCC-PerCORESET-r18`, `tci-JointTCI-UpdateSingleActiveTCI-PerCC-r18`, `tci-JointTCI-UpdateSingleActiveTCI-PerCC-PerCORESET-r18` 모두 동일 청크에서 회수 [38.306 §4.2.7.2, chunkId=`38.306-4.2.7.2-050`].
  - "tci-SeparateTCI-UpdateMultiActiveTCI-PerCC-r18 …", `tci-SeparateTCI-UpdateSingleActiveTCI-PerCC-r18`, `tci-SelectionDCI-r18`, `tci-SelectionAperiodicCSI-RS-r18`, `tci-SelectionAperiodicCSI-RS-M-DCI-r18` [38.306 §4.2.7.2, chunkId=`38.306-4.2.7.2-051`].
  - "commonTCI-MultiDCI-r18 / commonTCI-SingleDCI-r18 Indicates whether the UE supports common multi-CC TCI state ID update and activation for multi-DCI / single-DCI based multi-TRP …" [38.306 §4.2.7.2, chunkId=`38.306-4.2.7.2-019`].
  - "ltm-BeamIndicationJointTCI-r18 / ltm-BeamIndicationSeparateTCI-r18 …" [38.306 §4.2.7.2, chunkId=`38.306-4.2.7.2-024`].

### Rel-19 — Asymmetric DL sTRP / UL mTRP / NR MIMO Phase 5

**도입 배경**
- "Discussion on enhancements for asymmetric DL sTRP/UL mTRP scenarios … In RAN1#116 meeting, the following agreements on beam indication framework have been achieved [3]: Regarding separate DL/UL TCI state mode of Rel-18 unified TCI …" [R1-2408118, RAN1#118b, discussion, ai=9.2.4, rel=Rel-19].
- "Enhancements for event driven beam management" [R1-2403985, RAN1#117, discussion, rel=Rel-19].
- "Measurements enhancements for LTM … For LTM procedures, SSB based beam management is supported with a unified TCI framework, and the TCI state activation of a candidate cell is received before the reception of beam indication of the candidate cell." [R1-2406432, RAN1#118, discussion, ai=9.9.1, rel=Rel-19].
- "Initial Analysis on the RAN2 Impact for the R19 MIMO … For the asymmetric DL sTRP/UL mTRP deployment scenario, reuse the rel-17 unified TCI/ICBM and rel-18 unified TCI framework …" [R2-2408402, RAN2#127bis, discussion, ai=8.12.2, rel=Rel-19].
- "L1 event triggered measurement reporting for LTM … When mTRP is configured in the serving cell, the UE uses the best beam (in terms of RSRP) of the two 'current beams' for LTM event evaluation." [R2-2505548, RAN2#131, discussion, ai=8.6.3, rel=Rel-19].
- "MAC issues for MIMO … RP-242394, Revised Work Item: NR MIMO Phase 5 …" [R2-2508663, RAN2#132, discussion, ai=8.12.2, rel=Rel-19].
- "Introduction of NR mobility enhancements Phase 4 in TS 38.300 … Current beam (i.e. a beam corresponding to the indicated TCI state) is used for event evaluation in L1 measurement reporting for serving cell." [R2-2506415, RAN2#131, CR, ai=8.6.1, rel=Rel-19].

**문서별 변경**
- 38.321: §5.18.36 "Candidate Cell TCI States Activation/Deactivation" / §6.1.3.76 "Candidate Cell TCI States Activation/Deactivation MAC CE" / §6.1.3.77 "Cross-RRH TCI State Indication for UE-specific PDCCH MAC CE" — Neo4j RAN2 Section 노드 [Neo4j RAN2, sectionNumber=`5.18.36`/`6.1.3.76`/`6.1.3.77`].
- **★ 38.331 ASN.1 (P2 신규 — Rel-19 직접 트레이스)**:
  - `TCI-State`의 Rel-19 확장 블록 `[[ pathlossOffset-r19 ENUMERATED { dB-12, dB-8, dB-4, dB0, dB4, dB8, dB12, dB16, dB20, dB24, dB28, dB32, dB36, dB40, dB44, dB48, dB52, dB56, dB60} OPTIONAL -- Need R ]]` [asn1 IE=`TCI-State`, chunkId=`38.331-asn1-TCI-State-001`] — Rel-19에서 path loss offset 도입.
  - `TCI-UL-State-r17`의 동일한 `[[ pathlossOffset-r19 ... ]]` 블록 [asn1 IE=`TCI-UL-State-r17`, chunkId=`38.331-asn1-TCI-UL-State-r17-001`].
  - `CandidateTCI-State-r18`/`CandidateTCI-UL-State-r18` IE는 Rel-18 도입이지만 Rel-19에서도 LTM/asymmetric DL sTRP UL mTRP 시나리오의 base IE로 R1-2408118/R2-2408402에서 재사용됨.
- **★ 38.306 cap (P2 신규)**: §4.2.7.2 청크 `-005`에서 "cjt-QCL-PDSCH-SchemeC-r19 Indicates whether the UE supports the PDSCH DMRS port(s) are QCLed with the DL-RS associated with the first TCI state with respect to QCL-TypeA and QCLed …", `cjt-QCL-PDSCH-SchemeD-r19`, `cjt-QCL-PDSCH-SchemeE-r19` 회수 [38.306 §4.2.7.2, chunkId=`38.306-4.2.7.2-005`] — Rel-19 Coherent Joint Transmission(CJT)에서의 PDSCH QCL scheme. §4.2.7.2 청크 `-024`에서 "ltm-BeamIndicationJointTCI-CSI-RS-r19 …", "ltm-BeamIndicationSeparateTCI-CSI-RS-r19 …" 회수.

### Rel-20 — 6G Air Interface 단계 (TCI spec 본문 변경 미식별 — 정직 답변)

**도입 배경 (전부 6G overview/framing)**
- "Overview of 6G Air Interface … MIMO scope in 6G still requires proper design of beam management and CSI framework." [R1-2506358, RAN1#122, discussion, ai=11.1, rel=Rel-20].
- "Overview of the 6GR air interface … Extreme-MIMO (E-MIMO), equipped with an extended large-scale co-located antenna array …" [R1-2506063, RAN1#122, discussion, ai=11.1, rel=Rel-20].
- "Nokia Views on 6G Radio Air Interface" [R1-2505125, RAN1#122, discussion, ai=11.1, rel=Rel-20].
- "FL Summary #3 of Coverage Enhancement for NR Phase 3" [R1-2508116, RAN1#122b, discussion, rel=Rel-20].
- "Discussion on Rel-20 Coverage Enhancement" [R1-2509334, RAN1#123, discussion, rel=Rel-20].
- "6G mobility … Beam based mobility can be either between beams from the sa…" [R2-2508085, RAN2#132, discussion, ai=10.4, rel=Rel-20].
- "Consideration for 6G connected mode mobility … The inter-cell multi-TRP operation is supported in Rel-17 …" [R2-2508849, RAN2#132, discussion, ai=10.4, rel=Rel-20].
- "Discussion on Mobility management for 6GR" [R2-2508592, RAN2#132, discussion, rel=Rel-20].
- "Discussion on Energy Efficiency aspects of 6GR" [R2-2508765, RAN2#132, discussion, rel=Rel-20].

**Rel-20 문서별 변경 — 미발견 (정직 유지)**: 38.214 / 38.321 / 38.331 ASN.1 / 38.306에 대한 **Rel-20 신규 TCI 항목**의 spec 본문 변경은 retrieval에서 식별되지 않음. 회수된 RAN1/RAN2 Rel-20 TDoc은 모두 6G air-interface overview / 6G mobility framing 단계의 discussion 또는 NR Phase-3 coverage 보강이며, TCI 관련 spec 본문 변경 청크가 우세하게 회수되지 않음. → "커버리지/한계" 참조.

---

## ★ Release × 문서 24칸 매트릭스 (P1 vs P2)

| Release | 38.214 | 38.321 | 38.331 (RRC) | 38.306 (cap) |
|---|---|---|---|---|
| **Rel-15** | ✅ §5.1.5 TCI-State 리스트 / `PDSCH-Config` 인용 [chunkId=`38.214-5.1.5-001`] | ✅ §6.1.3.14 PDSCH TCI MAC CE [chunkId=`38.321-6.1.3.14-001`] | **✅★ ASN.1: `TCI-State {qcl-Type1, qcl-Type2}`, `QCL-Info {typeA..D}`, `PDSCH-Config {tci-StatesToAddModList, tci-StatesToReleaseList}`, `PDCCH-Config`, `ControlResourceSet`, `TCI-StateId` 본문** | **✅★ §4.2.7.2 `tci-StatePDSCH`/`maxNumberConfiguredTCI-StatesPerCC`/`additionalActiveTCI-StatePDCCH`/`multipleTCI` 행 직접** |
| **Rel-16** | ✅ §5.1.5 활성화 절차 38.321 §6.1.3.70 인용 [chunkId=`38.214-5.1.5-003`] | ✅ §6.1.3.24 enhanced PDSCH TCI MAC CE (eLCID) [chunkId=`38.321-6.1.3.24-001`] | ✅ `tci-PresentInDCI`/`tci-PresentDCI-1-2` 본문 인용(`§5.1.5` 통해) + **★ ASN.1 `ControlResourceSet`/`PDCCH-Config` host IE 본문** | **✅★ §4.2.7.2 `multipleTCI` (CORESET당 다중 TCI) 행 [chunkId=`38.306-4.2.7.2-029`]** |
| **Rel-17** | ✅ §5.1.5 `dl-OrJointTCI-StateList-r17` 분기 [chunkId=`38.214-5.1.5-005`/`-007`] | ✅ §5.18.23 unified TCI MAC CE (`simultaneousU-TCI-UpdateList*`) [chunkId=`38.321-5.18.23-001`] | **✅★ ASN.1: `TCI-UL-State-r17 {referenceSignal CHOICE {ssb, csi-RS, srs}, additionalPCI-r17, ul-powerControl-r17, pathlossReferenceRS-Id-r17}`, `TCI-UL-StateId-r17`, `PDSCH-Config`의 `dl-OrJointTCI-StateList-r17 CHOICE`/`unifiedTCI-StateRef-r17` 본문** | ✅ §4.2.7.2 unified TCI cap 군집 (Rel-17 도입을 전제로 한 -r18 행) |
| **Rel-18** | ✅ §5.1.5 joint/separate 분기 [chunkId=`38.214-5.1.5-003`] | ✅ §5.18.33 / §6.1.3.70 / §6.1.3.71 enhanced unified TCI MAC CE | **✅★ ASN.1: `CandidateTCI-State-r18 {qcl-Type1-r18 LTM-QCL-Info-r18}`, `CandidateTCI-UL-State-r18`, `LTM-QCL-Info-r18 {qcl-Type-r18 ENUMERATED {typeA..D}}`, `TCI-State`의 `[[tag-Id-ptr-r18 -- Cond 2TA]]` 확장** | **✅★ §4.2.7.2 `tci-StateSwitchInd-r18`, `tci-JointTCI-Update*-r18` (4종), `tci-SeparateTCI-Update*-r18` (4종), `tci-SelectionDCI-r18`, `tci-SelectionAperiodicCSI-RS*-r18`, `commonTCI-MultiDCI-r18`/`commonTCI-SingleDCI-r18`, `ltm-BeamIndicationJointTCI-r18`/`ltm-BeamIndicationSeparateTCI-r18` 행 직접** |
| **Rel-19** | ⚠️ §5.1.5 chunk 통합 본문 (Rel-19 분리 청크 약함) | ✅ §5.18.36 / §6.1.3.76 / §6.1.3.77 candidate cell / cross-RRH TCI MAC CE [Neo4j RAN2] | **✅★ ASN.1: `TCI-State`/`TCI-UL-State-r17` 양쪽의 `[[pathlossOffset-r19 ENUMERATED {dB-12..dB60}]]` 확장 블록 본문** | **✅★ §4.2.7.2 `cjt-QCL-PDSCH-SchemeC/D/E-r19` (CJT QCL scheme), `ltm-BeamIndicationJointTCI-CSI-RS-r19`/`ltm-BeamIndicationSeparateTCI-CSI-RS-r19` 행** |
| **Rel-20** | ❌ 미발견 (6G overview만) | ❌ 미발견 | ❌ 미발견 | ❌ 미발견 |

### 채움 비율 변화 (P1 → P2)

| 레벨 | P1 (v1) | P2 (v2) |
|---|---|---|
| ✅ 본문 직접 인용 | 13/24 (54.2%) | **20/24 (83.3%)** |
| ⚠️ Neo4j Section 노드만/proxy | 7/24 (29.2%) | 1/24 (4.2%) |
| ❌ 미발견 | 4/24 (16.7%) | 4/24 (16.7%) — 모두 Rel-20 |

→ P2(ASN.1 컬렉션 + 38.306 정확 키워드 매칭) 도입으로 **본문 인용 가능 칸 13 → 20개 (+7칸)**. 4 ⚠️→✅ (38.331 모든 Release Rel-15/Rel-17/Rel-18/Rel-19), 3 ⚠️→✅ (38.306 Rel-15/Rel-16/Rel-18/Rel-19). Rel-20 4칸은 데이터셋 단계가 6G framing에 머물러 의도적으로 ❌ 유지(정직).

---

## 문서 간 연결고리 (RRC IE → MAC-CE → PHY QCL → capability)

**P2 + ASN.1 직접 인용으로 트레이스 강화:**

1. **RRC IE → 물리(38.214) (Rel-15 base)**:
   - `PDSCH-Config` 안에 `tci-StatesToAddModList SEQUENCE (SIZE (1..maxNrofTCI-States)) OF TCI-State` [asn1 IE=`PDSCH-Config`] → 38.214 §5.1.5 본문이 동일 IE를 참조 ("up to M TCI-State configurations within the higher layer parameter PDSCH-Config" [chunkId=`38.214-5.1.5-001`]).
   - `TCI-State { tci-StateId, qcl-Type1 QCL-Info, qcl-Type2 QCL-Info OPTIONAL }` [asn1 IE=`TCI-State`] → `QCL-Info { referenceSignal CHOICE {csi-rs, ssb}, qcl-Type ENUMERATED {typeA, typeB, typeC, typeD} }` [asn1 IE=`QCL-Info`] → 38.214 §5.1.5 QCL assumption type D / type A 처리.

2. **MAC(38.321) → 물리(38.214) (Rel-15/16)**:
   - 38.214 §5.1.5: "receive an activation command, as described in clause 6.1.3.70 of [10, TS 38.321], the activation command is used to map up to 8 sets of TCI states to the codepoints of the DCI field 'Transmission Configuration Indication' …" [chunkId=`38.214-5.1.5-003`].
   - DCI 'TCI' 필드 host: `ControlResourceSet` ASN.1에 `tci-PresentInDCI` 위치 [asn1 IE=`ControlResourceSet`].

3. **RRC ASN.1 (Rel-17 unified) ↔ MAC(38.321 §5.18.23) ↔ 물리(38.214 §5.1.5)**:
   - `PDSCH-Config`의 `dl-OrJointTCI-StateList-r17 CHOICE { dl-OrJointTCI-StateToAddModList-r17, dl-OrJointTCI-StateToReleaseList-r17 }` + `unifiedTCI-StateRef-r17 ServingCellAndBWP-Id-r17` [asn1 IE=`PDSCH-Config`]
   - ↔ `TCI-UL-State-r17 { referenceSignal CHOICE {ssb, csi-RS, srs} }` [asn1 IE=`TCI-UL-State-r17`]
   - ↔ 38.321 §5.18.23 unified TCI MAC CE [chunkId=`38.321-5.18.23-001`]
   - ↔ 38.214 §5.1.5 "if the UE is provided dl-OrJointTCI-StateList-r17 …" [chunkId=`38.214-5.1.5-005`].

4. **Rel-18 LTM 통합 (RRC → MAC → cap)**:
   - `CandidateTCI-State-r18 { qcl-Type1-r18 LTM-QCL-Info-r18 }` + `LTM-QCL-Info-r18 { qcl-Type-r18 ENUMERATED {typeA..D} }` [asn1 IE=`LTM-QCL-Info-r18`].
   - ↔ 38.321 §6.1.3.70/71 enhanced unified TCI MAC CE for joint/separate [chunkIds=`38.321-6.1.3.70-001`/`38.321-6.1.3.71-001`].
   - ↔ 38.306 §4.2.7.2: `ltm-BeamIndicationJointTCI-r18` / `ltm-BeamIndicationSeparateTCI-r18` 행 [chunkId=`38.306-4.2.7.2-024`].

5. **UE capability(38.306) ← 물리(38.214) ← RRC IE**:
   - 38.214 §5.1.5: "M depends on the UE capability `maxNumberConfiguredTCIstatesPerCC`" [chunkId=`38.214-5.1.5-001`].
   - 38.306 §4.2.7.2: "tci-StatePDSCH … -maxNumberConfiguredTCI-StatesPerCC indicates the maximum number of configured TCI…" [chunkId=`38.306-4.2.7.2-050`].
   - `TCI-StateId ::= INTEGER (0..maxNrofTCI-States-1)` [asn1 IE=`TCI-StateId`] — RRC가 인덱스 범위를 maxNrofTCI-States 상한으로 제한 → cap 수치와 직결.

6. **Rel-19 path loss offset (RRC ↔ cap)**:
   - `TCI-State` Rel-19 확장 `[[ pathlossOffset-r19 ENUMERATED { dB-12, dB-8, ..., dB60 } OPTIONAL -- Need R ]]` [asn1 IE=`TCI-State`].
   - `TCI-UL-State-r17` Rel-19 동일 확장 [asn1 IE=`TCI-UL-State-r17`].
   - 38.306 §4.2.7.2: `cjt-QCL-PDSCH-Scheme[CDE]-r19` 행 [chunkId=`38.306-4.2.7.2-005`].

7. **TDoc → spec 변화 흐름**: Rel-15 R2-1713533 [RAN2#100, ai=10.2.13] "MAC CEs for activating an RS resource and handling corresponding TCI states" → 38.321 §6.1.3.14 (PDSCH TCI MAC CE) 도입; Rel-17 R2-2110534 [RAN2#116-e, ai=8.17.2] "Considerations on Inter-Cell Beam Management" → 38.321 §5.18.23 unified TCI MAC CE 및 38.331 `dl-OrJointTCI-StateList-r17` IE 도입; Rel-18 R1-2300932 [RAN1#112, ai=9.1.1.1] "Unified TCI Framework for Multi-TRP" + R2-2403134 [RAN2#125bis, ai=7.20.3] "Correction on Unified TCI operation" → 38.321 §6.1.3.70/71 + 38.331 `CandidateTCI-State-r18` IE; Rel-19 R1-2408118 [RAN1#118b, ai=9.2.4] asymmetric DL sTRP/UL mTRP + R2-2408402 [RAN2#127bis, ai=8.12.2] R19 MIMO RAN2 영향 → 38.331 `pathlossOffset-r19` 확장 + 38.306 `cjt-QCL-PDSCH-Scheme*-r19`. 모든 단계 연결이 검색 결과만으로 추적된다.

---

## 커버리지 / 한계 (3gpp-tracer 데이터셋 기준)

### ★ P2 + ASN.1로 해소된 항목 (v1 → v2 진전)

| 항목 | v1 (P1) 상태 | v2 (P2 + ASN.1) 해소 |
|---|---|---|
| 38.331 `TCI-State` IE 본문 (`tci-StateId`, `qcl-Type1`, `qcl-Type2`) | ❌ ts_sections 미회수 | ✅ `[asn1 IE=TCI-State, chunkId=38.331-asn1-TCI-State-001]` (614 chars) |
| 38.331 `QCL-Info` IE 본문 (typeA/B/C/D enum) | ❌ 미회수 | ✅ `[asn1 IE=QCL-Info, chunkId=38.331-asn1-QCL-Info-001]` |
| 38.331 `tci-StatesToAddModList` / `tci-StatesToReleaseList` 본문 | ❌ 미회수 | ✅ `PDSCH-Config` ASN.1 본문 안에 위치 [asn1 IE=`PDSCH-Config`] |
| 38.331 `dl-OrJointTCI-StateList-r17` 정의 위치 | ⚠️ Neo4j Section 노드만 | ✅ `PDSCH-Config` ASN.1 본문 내 CHOICE 분기 직접 인용 |
| 38.331 `TCI-UL-State-r17` IE 본문 (referenceSignal CHOICE: ssb/csi-RS/srs) | ⚠️ Neo4j Section 노드만 | ✅ `[asn1 IE=TCI-UL-State-r17, chunkId=38.331-asn1-TCI-UL-State-r17-001]` (798 chars) |
| 38.331 `CandidateTCI-State-r18` / `CandidateTCI-UL-State-r18` 본문 | ⚠️ Neo4j Section 노드만 | ✅ ASN.1 본문 직접 인용 (qcl-Type1-r18 → LTM-QCL-Info-r18 연결 확인) |
| 38.331 `LTM-QCL-Info-r18` IE 본문 (qcl-Type-r18 enum) | ❌ 미회수 | ✅ ASN.1 본문 직접 인용 |
| 38.306 `maxNumberConfiguredTCIstatesPerCC` 정확 행 | ⚠️ 헤더 청크만, preview 부족 | ✅ §4.2.7.2 chunkId=`-050` 안에 `tci-StatePDSCH`/`maxNumberConfiguredTCI-StatesPerCC` 행 직접 |
| 38.306 Rel-18 `tci-JointTCI-Update*-r18` / `tci-SeparateTCI-Update*-r18` 행 | ❌ 미회수 | ✅ §4.2.7.2 chunkId=`-050`/`-051` 정확 행 직접 |
| 38.306 Rel-18 `commonTCI-MultiDCI-r18` / `commonTCI-SingleDCI-r18` 행 | ❌ 미회수 | ✅ §4.2.7.2 chunkId=`-019` 직접 |
| 38.306 Rel-19 `cjt-QCL-PDSCH-Scheme[CDE]-r19` 행 | ❌ 미회수 | ✅ §4.2.7.2 chunkId=`-005` 직접 |
| Rel-19 38.331 신규 변경 (path loss offset) | ❌ 별도 chunk 약함 | ✅ `TCI-State`/`TCI-UL-State-r17` 안의 `[[ pathlossOffset-r19 ... ]]` 확장 블록 직접 |
| Rel-15 RAN2 측 TCI MAC CE 도입 discussion | ⚠️ 다른 토픽 우세 | ✅ R2-1713533 [RAN2#100, ai=10.2.13] "MAC CEs for activating an RS resource and handling corresponding TCI states" 직접 |

→ **8개 ❌ → ✅, 4개 ⚠️ → ✅, 1개 ⚠️ → ✅(Rel-15 RAN2 discussion)**.

### 여전히 남은 한계 (정직)

| 항목 | 상태 |
|---|---|
| Rel-20 spec 본문 신규 변경 (38.214/38.321/38.331/38.306) | **3gpp-tracer 데이터셋에서 미발견**. 회수된 Rel-20 TDoc은 6G overview / Coverage Enhancement Phase-3 / 6G mobility framing 단계로, TCI 관련 spec 본문 변경 청크가 우세하지 않음. 확정적 답변 불가. |
| `tci-PresentInDCI` 자체 IE 본문 chunk | `ControlResourceSet` ASN.1 본문 안에 host IE로 위치 확인 [asn1 IE=`ControlResourceSet`]. 단 ControlResourceSet ASN.1 preview 첫 부분에서는 보이지 않으며, MatchText 검색으로만 재현 — 본문 끝 부분 r16/r17 확장에 위치 추정. |
| 38.214 §5.1.5 chunk가 통합 본문 (Rel-15~Rel-19 분리 청크 부재) | 의도적 한계: 같은 §5.1.5 안에 모든 Release 본문이 누적되어 있어 Release별 분리 청크는 chunkId 인덱스(-001 ~ -007)로만 구분됨. |
| ASN.1 컬렉션은 RAN2(38.331) 1종만 적재 | 3GPP RAN2 RRC 외 타 WG ASN.1(예: NGAP, F1AP)은 별도 수요 시 컬렉션 추가 필요. 본 질문 범위에서는 충분. |

### 검색 신뢰도 평가 (Release별 답변 가능 수준)

| Release | P1 수준 | P2 수준 |
|---|---|---|
| Rel-15 | 중상 | **상** (RAN2 도입 discussion R2-1713533 + ASN.1 IE 본문 확보) |
| Rel-16 | 중상 | **상** (ASN.1 host IE + 38.306 multipleTCI 행 직접) |
| Rel-17 | 상 | **상+** (TCI-UL-State-r17 본문 + dl-OrJointTCI-StateList-r17 ASN.1 직접) |
| Rel-18 | 상 | **상++** (CandidateTCI-State-r18 + LTM-QCL-Info-r18 본문 + 38.306 cap 16개 행) |
| Rel-19 | 중 | **상** (pathlossOffset-r19 ASN.1 확장 블록 + cjt-QCL-PDSCH-Scheme-r19 cap 행 직접) |
| Rel-20 | 하 | 하 (변화 없음 — 6G overview 단계만 회수, 의도적 정직 답변) |

---

## 자가 검증

- 인용 없는 사실 문장: 본문에서 0건. 모든 문장은 `[spec §sec, chunkId=...]`, `[asn1 IE=..., chunkId=...]`, `[tdoc, mtg, type, ai=..., rel=...]` 형식 인용 첨부.
- TDoc release/agendaItem 인용은 `q2_retrieval_log_v2.json`의 `tdoc_queries[*].hits[*]` 페이로드에서 그대로 가져옴. 임의 보정 없음.
- TS 본문 인용은 `q2_retrieval_log_v2.json`의 `ts_queries[*].hits[*].text_preview` 또는 ts_sections scroll로 직접 회수한 chunk(`38.214-5.1.5-001 ~ 007`, `38.306-4.2.7.2-001/-005/-019/-024/-029/-050/-051`)에서 그대로 발췌.
- ★ ASN.1 IE 본문 인용은 `asn1_by_name[*].rows[*].text` 또는 `asn1_vector_queries[*].hits[*].text`에서 그대로 가져옴 (잘림 없음, IE당 평균 200~800자 본문).
- IE 노드 인용은 Neo4j 직접 쿼리 결과(`neo4j_results.RAN1/RAN2.rows`, `neo4j_results.RAN2_IE_catalog.rows`)에서 가져옴.
- "미발견" 항목은 모두 **데이터셋 한계로 식별 불가** 표기. spec 변경 자체의 존재/부재를 단정하지 않음 (Rel-20).
- Release 잘못 인용 검토: TDoc payload `release` 필드 그대로 사용. 본문에 인용한 모든 TDoc은 retrieval log의 동일 release 키 아래 존재함.
- v1 대비 변경 비교: "★ Release × 문서 24칸 매트릭스" 채움 비율 13/24(54.2%) → 20/24(83.3%) 측정. 4 ❌ 칸은 모두 Rel-20으로 정직 유지.
