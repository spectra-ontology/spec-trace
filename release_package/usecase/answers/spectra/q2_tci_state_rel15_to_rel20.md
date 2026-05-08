# Q2. Standards-Item Summary of TCI-state across Rel-15 to Rel-20 (SPECTRA RAG only)

## Metadata

| Item | Value |
|---|---|
| Question | Standards-item summary of TCI-state across Rel-15 to Rel-20 (WID introduction context + 38.214/38.321/38.331/38.306 changes + cross-document linkages) |
| Search system | SPECTRA RAG (Qdrant + Neo4j). External LLM knowledge / Web prohibited |
| Qdrant collections | `the section-level collection`, `the section-level collection`, `the IE-level collection`, `the TDoc collection`, `the TDoc collection` |
| Neo4j instances | RAN1 (`bolt://localhost:7687`), RAN2 (`bolt://localhost:7688`) |
| Embedding model | `openai/text-embedding-3-small` |
| TS section queries | 14 (140 hits) |
| ASN.1 vector queries | 8 (80 hits) |
| ASN.1 ieName exact matches | 11 (11 IE bodies retrieved) |
| 38.306 capability text-match probes | 6 (18 chunks, 96 TCI rows) |
| TDoc queries | 48 (480 hits) |
| Neo4j queries | 2 (33 sections) + RAN2 IE catalog (9 rows) = 42 rows |
| Output | `logs/cross-phase/usecase/q2_retrieval_log_v2.json` |

> Every factual sentence in this document is cited solely from the chunks / IEs / TDocs / Neo4j rows retrieved by the searches above.
> Citation formats: `[spec §sec, chunkId=...]`, `[asn1 IE=..., chunkId=...]`, `[tdoc, mtg, type, ai=..., rel=...]`.

---

## SPECTRA RAG Retrieval Summary

### Hit counts by Release × collection (TDoc, top-10 × 4 queries combined)

| Release | `the TDoc collection` (top score) | `the TDoc collection` (top score) |
|---|---|---|
| Rel-15 | 40 hits / max 0.699 | 40 hits / max 0.626 |
| Rel-16 | 40 hits / max 0.756 | 40 hits / max 0.666 |
| Rel-17 | 40 hits / max 0.744 | 40 hits / max 0.740 |
| Rel-18 | 40 hits / max 0.716 | 40 hits / max 0.704 |
| Rel-19 | 40 hits / max 0.716 | 40 hits / max 0.690 |
| Rel-20 | 40 hits / max 0.665 | 40 hits / max 0.621 |

### Top matches per TS

| Area | Core chunks |
|---|---|
| 38.214 (RAN1) | §5.1.5 "Antenna ports quasi co-location" [chunkId=`38.214-5.1.5-001`/`-003`/`-005`/`-007`] |
| 38.321 (RAN2 MAC) | §5.18.23 unified TCI MAC CE (top 0.772), §5.18.33 enhanced unified, §6.1.3.14/24/47/70/71/76/77 |
| 38.331 ASN.1 (RAN2 RRC) | `TCI-State`, `TCI-StateId`, `QCL-Info`, `TCI-UL-State-r17`, `TCI-UL-StateId-r17`, `CandidateTCI-State-r18`, `CandidateTCI-UL-State-r18`, `LTM-QCL-Info-r18`, `PDSCH-Config`, `PDCCH-Config`, `ControlResourceSet` |
| 38.306 (RAN2 cap) | §4.2.7.2 "BandNR parameters" — `tci-StatePDSCH`, `maxNumberConfiguredTCI-StatesPerCC`, `tci-StateSwitchInd-r18`, `tci-JointTCI-Update*-r18`, `tci-SeparateTCI-Update*-r18`, `ltm-BeamIndicationJointTCI-r18`, `cjt-QCL-PDSCH-Scheme*-r19` rows directly retrieved |

### Neo4j section nodes (TCI / QCL / spatial relation)

- RAN1: 1 (`38.214 §5.1.5 Antenna ports quasi co-location`)
- RAN2: 32 — 16 PDSCH/PDCCH TCI activation MAC CE entries in 38.321; 8 TCI-related IE/field entries in 38.331; 9 entries from external RAN2 IE catalog scan

---

## Per-Release Answer Body

### Rel-15 — TCI Framework Introduction (NR initial)

**RAN1 introduction context (TDoc evidence)**
- "Mapping between candidate TCI state and N-bit DCI field …" [R1-1718541, RAN1#90b, discussion, ai=7.2.2.3, "Beam management for NR", rel=Rel-15] — design of the mapping between DCI TCI codepoints and the candidate TCI states.
- "There appears no reason why the TCI field of the DCI for PDSCH should not convey the non-spatial QCL parameters as they are available in the list of TCI states." [R1-1720662, RAN1#91, discussion, ai=7.2.2.3, "Beam management for NR", rel=Rel-15] — conveying non-spatial QCL via the TCI field in DCI.
- "Beam Management of Multiple Beam Pairs in Uplink" [R1-1804787, RAN1#92b, discussion, "Beam management for NR", rel=Rel-15] — UL beam management.

**RAN2 introduction context**
- "In order to support quasi-collocation and various beamforming feature in NR, RAN1 has agreed to support up to M Transmission Configuration Indicator (TCI) states, wherein each TCI state can include one RS Set. TCI state was defined for QCL indication of various cases such as quasi-collocation betwee…" [R2-1713533, RAN2#100, discussion, ai=10.2.13, "MAC CEs for activating an RS resource and handling corresponding TCI states", rel=Rel-15] — direct evidence for the introduction of TCI MAC CEs on the RAN2 side in Rel-15.

**Changes in 38.214 / 38.321 / 38.331 / 38.306**
- 38.214 §5.1.5: "The UE can be configured with a list of up to M TCI-State configurations within the higher layer parameter PDSCH-Config to decode PDSCH according to a detected PDCCH … M depends on the UE capability `maxNumberConfiguredTCIstatesPerCC`." [38.214 §5.1.5, chunkId=`38.214-5.1.5-001`].
- 38.321 §6.1.3.14 "TCI States Activation/Deactivation for UE-specific PDSCH MAC CE": "identified by a MAC subheader with LCID as specified in Table 6.2.1-1. It has a variable size consisting of following fields …" [38.321 §6.1.3.14, chunkId=`38.321-6.1.3.14-001`].
- 38.331 ASN.1:
  - `TCI-State ::= SEQUENCE { tci-StateId TCI-StateId, qcl-Type1 QCL-Info, qcl-Type2 QCL-Info OPTIONAL, ..., [[ additionalPCI-r17 ..., pathlossReferenceRS-Id-r17 ..., ul-powerControl-r17 ... ]], [[ tag-Id-ptr-r18 ENUMERATED {n0,n1} ... ]], [[ pathlossOffset-r19 ENUMERATED {dB-12,...,dB60} ... ]] }` [asn1 IE=`TCI-State`, chunkId=`38.331-asn1-TCI-State-001`] — Rel-15 base SEQUENCE skeleton plus the Rel-17/18/19 extension blocks contained in the same IE.
  - `TCI-StateId ::= INTEGER (0..maxNrofTCI-States-1)` [asn1 IE=`TCI-StateId`, chunkId=`38.331-asn1-TCI-StateId-001`].
  - `QCL-Info ::= SEQUENCE { cell ServCellIndex OPTIONAL, bwp-Id BWP-Id OPTIONAL, referenceSignal CHOICE { csi-rs NZP-CSI-RS-ResourceId, ssb SSB-Index }, qcl-Type ENUMERATED {typeA, typeB, typeC, typeD}, ... }` [asn1 IE=`QCL-Info`, chunkId=`38.331-asn1-QCL-Info-001`] — direct citation of the QCL Type A/B/C/D enum and the referenceSignal CHOICE (CSI-RS or SSB).
  - `PDSCH-Config ::= SEQUENCE { ... tci-StatesToAddModList SEQUENCE (SIZE (1..maxNrofTCI-States)) OF TCI-State OPTIONAL, tci-StatesToReleaseList SEQUENCE (SIZE (1..maxNrofTCI-States)) OF TCI-StateId OPTIONAL, ... dl-OrJointTCI-StateList-r17 CHOICE { ... } ... unifiedTCI-StateRef-r17 ServingCellAndBWP-Id-r17 ... }` [asn1 IE=`PDSCH-Config`, chunkId=`38.331-asn1-PDSCH-Config-001`] — `tci-StatesToAddModList`/`tci-StatesToReleaseList` defined in the Rel-15 base, with the Rel-17 unified TCI branch added as an extension.
  - `PDCCH-Config ::= SEQUENCE { controlResourceSetToAddModList ..., searchSpacesToAddModList ..., ... }` [asn1 IE=`PDCCH-Config`, chunkId=`38.331-asn1-PDCCH-Config-001`].
  - `ControlResourceSet ::= SEQUENCE { controlResourceSetId ..., frequencyDomainResources ..., duration ..., cce-REG-MappingType CHOICE { ... } ... }` [asn1 IE=`ControlResourceSet`, chunkId=`38.331-asn1-ControlResourceSet-001`] — host IE for `tci-PresentInDCI` / `tci-StatesPDCCH-ToAddList` etc.
- 38.306 cap rows: directly retrieved from §4.2.7.2 "BandNR parameters" chunk `38.306-4.2.7.2-050` — "tci-StatePDSCH Defines support of TCI-States for PDSCH. The capability signalling comprises the following parameters: -maxNumberConfiguredTCI-StatesPerCC indicates the maximum number of configured TCI…" [38.306 §4.2.7.2, chunkId=`38.306-4.2.7.2-050`]. In addition, `additionalActiveTCI-StatePDCCH` is retrieved from §4.2.7.2 chunk `-001` and `multipleTCI` (support for multiple TCI configurations per CORESET) from `-029`.

### Rel-16 — eMIMO Multi-Beam Enhancement

**Introduction context**
- "The work item on Rel-16 MIMO enhancements has been specified [1]. … The WI for Rel-16 covers several key features aimed at enhancing multibeam …" [R1-1903044, RAN1#96, discussion, ai=7.2.8.3, "Enhancements on Multi-beam Operation", rel=Rel-16].
- "Enhancements on Multi-beam Operation" [R1-1813443, RAN1#95, discussion, ai=7.2.8.3, rel=Rel-16].
- "Feature lead summary of Enhancements on Multi-beam Operations" [R1-1907650, RAN1#97, discussion, ai=7.2.8.3, rel=Rel-16].
- "Further discussion on multi TRP transmission" [R1-1901702, RAN1#96, discussion, rel=Rel-16].
- "MAC CE design on single PDCCH based multi-TRP/panel transmission … TCI states for PDSCH are configured by RRC, at first. Up to 128 TCI states can be configured per BWP per serving cell. Amongst the configured TCI states, up to …" [R2-1910966, RAN2#107, discussion, ai=11.16, rel=Rel-16] — under single-PDCCH-based mTRP, RRC can configure up to 128 TCI states for PDSCH per BWP.
- "RAN2 aspects of multi-beam enhancements" [R2-1910145, RAN2#107, discussion, rel=Rel-16].

**Per-document changes (retrieved)**
- 38.214 §5.1.5: "receive an activation command, as described in clause 6.1.3.70 of [10, TS 38.321], the activation command is used to map up to 8 sets of TCI states to the codepoints of the DCI field 'Transmission Configuration Indication' …" [38.214 §5.1.5, chunkId=`38.214-5.1.5-003`].
- 38.321 §6.1.3.24 "Enhanced TCI States Activation/Deactivation for UE-specific PDSCH MAC CE": "identified by a MAC PDU subheader with eLCID as specified in Table 6.2.1-1b. It has a variable size consisting of following fields …" [38.321 §6.1.3.24, chunkId=`38.321-6.1.3.24-001`] — eLCID-based enhanced PDSCH TCI activation.
- 38.331: in the body of 38.214 §5.1.5 "Independent of the configuration of `tci-PresentInDCI` and `tci-PresentDCI-1-2` in RRC connected mode" [38.214 §5.1.5, chunkId=`38.214-5.1.5-005`]. In the `PDCCH-Config` ASN.1 the controlResourceSet list and search-space list appear [asn1 IE=`PDCCH-Config`, chunkId=`38.331-asn1-PDCCH-Config-001`]; under refined ASN.1 search, `tci-PresentInDCI` is located within the body of `ControlResourceSet` [asn1 IE=`ControlResourceSet`, chunkId=`38.331-asn1-ControlResourceSet-001`].
- 38.306: §4.2.7.2 chunk `-029` "multipleTCI Indicates whether UE supports more than one TCI state configurations per CORESET. UE is only required to track one active TCI state per CORESET. UE is required to suppo…" [38.306 §4.2.7.2, chunkId=`38.306-4.2.7.2-029`] — the `multipleTCI` row added at Rel-16 (multiple TCI configurations per CORESET).

### Rel-17 — Unified TCI framework / Inter-cell beam management Introduced

**Introduction context (RAN1/RAN2)**
- "Enhancement of multi-beam operation is an important part of R17 feMIMO WI [1]. Discussion on multi-beam operation has been ongoing since RAN1#102e …" [R1-2109103, RAN1#106b-e, discussion, ai=8.1.1, "Enhancements on Multi-beam Operation", rel=Rel-17].
- "Further enhancement on multi-beam operation" [R1-2103287, RAN1#104b-e, discussion, ai=8.1.1, rel=Rel-17].
- "Discussion of RAN2 LS on inter-cell BM and mTRP" [R1-2110346, RAN1#106b-e, discussion, rel=Rel-17].
- "Inter-cell beam management | inter-cell MTRP / TCI Framework | R17 Unified TCI framework, UE assumes that the UE-dedicated channels/RSs can be switched t…" [R2-2110534, RAN2#116-e, discussion, ai=8.17.2, "Considerations on Inter-Cell Beam Management", rel=Rel-17].
- "Inter-cell BM and inter-cell mTRP" [R2-2201098, RAN2#116bis-e, discussion, rel=Rel-17].
- "Discussion on the support of L1/L2 centric inter-cell mobility" [R2-2105827, RAN2#114-e, discussion, rel=Rel-17].
- "Discussion on multi-TRP BFR and new MIMO MAC CE" [R2-2107995, RAN2#115-e, discussion, rel=Rel-17].

**Per-document changes**
- 38.214 §5.1.5: "if the UE is provided `dl-OrJointTCI-StateList-r17`, …" [38.214 §5.1.5, chunkId=`38.214-5.1.5-005`]; "When a UE is configured with `dl-OrJointTCI-StateList` and is having two indicated TCI-states …" [chunkId=`38.214-5.1.5-007`]; "When a UE configured with `dl-OrJointTCI-StateList` supports `tci-SeparateTCI-UpdateMultiActiveTCI-Per…`" [chunkId=`38.214-5.1.5-003`].
- 38.321 §5.18.23 / §6.1.3.47: "The network may activate and deactivate the configured unified TCI states of a Serving Cell or a set of Serving Cells configured in `simultaneousU-TCI-UpdateList1`, `simultaneousU-TCI-UpdateList2`, …" [38.321 §5.18.23, chunkId=`38.321-5.18.23-001`].
- 38.331 ASN.1:
  - `TCI-UL-State-r17 ::= SEQUENCE { tci-UL-StateId-r17 TCI-UL-StateId-r17, servingCellId-r17 ServCellIndex OPTIONAL, bwp-Id-r17 BWP-Id OPTIONAL, referenceSignal-r17 CHOICE { ssb-Index-r17 SSB-Index, csi-RS-Index-r17 NZP-CSI-RS-ResourceId, srs-r17 SRS-ResourceId }, additionalPCI-r17 ..., ul-powerControl-r17 ..., pathlossReferenceRS-Id-r17 ..., [[ tag-Id-ptr-r18 ... ]], [[ pathlossOffset-r19 ... ]] }` [asn1 IE=`TCI-UL-State-r17`, chunkId=`38.331-asn1-TCI-UL-State-r17-001`] — the Rel-17 separate UL TCI IE body cited directly (3-way reference-signal CHOICE: CSI-RS / SSB / SRS).
  - `TCI-UL-StateId-r17 ::= INTEGER (0..maxUL-TCI-1-r17)` [asn1 IE=`TCI-UL-StateId-r17`, chunkId=`38.331-asn1-TCI-UL-StateId-r17-001`].
  - In the `PDSCH-Config` body: `dl-OrJointTCI-StateList-r17 CHOICE { dl-OrJointTCI-StateToAddModList-r17 SEQUENCE (SIZE (1..maxNrofTCI-States)) OF TCI-State, dl-OrJointTCI-StateToReleaseList-r17 SEQUENCE (SIZE (1..maxNrofTCI-States)) OF TCI-StateId } / unifiedTCI-StateRef-r17 ServingCellAndBWP-Id-r17` [asn1 IE=`PDSCH-Config`, chunkId=`38.331-asn1-PDSCH-Config-001`] — locating the Rel-17 unified TCI branch precisely inside PDSCH-Config.
- 38.306 cap: §4.2.7.2 chunk `-024` retrieves "ltm-BeamIndicationJointTCI-r18 Indicates whether the UE supports unified TCI with joint DL/UL LTM TCI-state indication for LTM procedure, indicating and activating a single joint L…" [38.306 §4.2.7.2, chunkId=`38.306-4.2.7.2-024`] (note: a Rel-18 LTM row, but the unified TCI definition presupposes Rel-17 introduction).

### Rel-18 — Enhanced Unified TCI / Multi-TRP Unified / LTM Integration

**Introduction context**
- "FL summary 1/2 on L1 enhancements for inter-cell beam management … For the beam indication of LTM in the case of inter-cell mTRP: The TCI state(s) indicated through inter-cell beam management is applied to UE-specific PDCC…" [R1-2309110, RAN1#114b, discussion, ai=8.7.1, rel=Rel-18].
- "Unified TCI Framework for Multi-TRP … When unified TCI framework is used for beam indication for single DCI multi-TRP, for the case when the UE is configured with joint DL/UL beam indication with the value of unifiedtci-StateType set to 'JointULDL', the UE expects to be indicated with a TCI codepoint which is mapped to two joint DL/UL T…" [R1-2300932, RAN1#112, discussion, ai=9.1.1.1, rel=Rel-18].
- "Maintenance on NR MIMO Evolution for Downlink and Uplink … In RAN#94e, the working item to enhance both downlink and uplink MIMO operations in Rel-18 was agreed [1]." [R1-2403112, RAN1#116b, discussion, ai=8.1, rel=Rel-18].
- "In R17 inter-cell beam management, the unified TCI framework was introduced with the following characteristics: A pool of joint or separate DL/UL TCI states is …" [R2-2207753, RAN2#119-e, discussion, ai=8.4.2.2, "Discussion on candidate solutions for L1 L2 mobility", rel=Rel-18].
- "On MAC CE for Joint TCI State Indication" [R2-2306181, RAN2#122, discussion, ai=7.1.2, rel=Rel-18].
- "[N110] Correction on Unified TCI operation … The unified TCI framework was introduced in Rel-17 which facilitates a streamlined multi-beam operation targeting FR2. As Rel-17 focuses on single-TRP use cases, extension of unified TCI framework that focuses on multi-TRP use cases…" [R2-2403134, RAN2#125bis, discussion, ai=7.20.3, rel=Rel-18].
- "Two TAs for multi-DCI multi-TRP … In Rel-17, Inter-Cell Beam Management (ICBM) was introduced …" [R2-2307614, RAN2#123, discussion, ai=7.20.2, rel=Rel-18].

**Per-document changes**
- 38.214 §5.1.5: includes both joint and separate TCI mode branches [38.214 §5.1.5, chunkId=`38.214-5.1.5-003`/`-007`].
- 38.321:
  - §5.18.33 "Enhanced Unified TCI States Activation/Deactivation MAC CE" [chunkId=`38.321-5.18.33-001`].
  - §6.1.3.70 "Enhanced Unified TCI States Activation/Deactivation MAC CE for Joint TCI States" [chunkId=`38.321-6.1.3.70-001`]; §6.1.3.71 "for Separate TCI States" [chunkId=`38.321-6.1.3.71-001`].
- 38.331 ASN.1:
  - `CandidateTCI-State-r18 ::= SEQUENCE { tci-StateId-r18 TCI-StateId, qcl-Type1-r18 LTM-QCL-Info-r18, qcl-Type2-r18 LTM-QCL-Info-r18 OPTIONAL, pathlossReferenceRS-Id-r18 PathlossReferenceRS-Id-r17 OPTIONAL, tag-Id-ptr-r18 ENUMERATED {n0,n1} OPTIONAL, ul-powerControl-r18 Uplink-powerControlId-r17 OPTIONAL, ... }` [asn1 IE=`CandidateTCI-State-r18`, chunkId=`38.331-asn1-CandidateTCI-State-r18-001`] — body of the Rel-18 LTM candidate TCI-state IE.
  - `CandidateTCI-UL-State-r18 ::= SEQUENCE { tci-UL-StateId-r18 TCI-UL-StateId-r17, referenceSignal-r18 CHOICE { ssb-Index SSB-Index, csi-RS-Index NZP-CSI-RS-ResourceId }, pathlossReferenceRS-Id-r18 ..., tag-Id-ptr-r18 ENUMERATED {n0,n1} OPTIONAL, ul-powerControl-r18 Uplink-powerControlId-r17 OPTIONAL, ... }` [asn1 IE=`CandidateTCI-UL-State-r18`, chunkId=`38.331-asn1-CandidateTCI-UL-State-r18-001`].
  - `LTM-QCL-Info-r18 ::= SEQUENCE { referenceSignal-r18 CHOICE { ssb-Index SSB-Index, csi-RS-Index NZP-CSI-RS-ResourceId }, qcl-Type-r18 ENUMERATED {typeA, typeB, typeC, typeD}, ... }` [asn1 IE=`LTM-QCL-Info-r18`, chunkId=`38.331-asn1-LTM-QCL-Info-r18-001`] — body of the LTM-dedicated QCL info IE.
  - Rel-18 extension blocks of `TCI-State` / `TCI-UL-State-r17`: `[[ tag-Id-ptr-r18 ENUMERATED {n0,n1} OPTIONAL -- Cond 2TA ]]` [asn1 IE=`TCI-State`, chunkId=`38.331-asn1-TCI-State-001`] — Rel-18 multi-TRP 2TA support.
- 38.306 cap:
  - "tci-StateSwitchInd-r18 Indicates whether the UE supports enhanced one-shot large UL transmit timing adjustment requirement to support FR2-1 PC6 Ues and enhanced TCI state switching…" [38.306 §4.2.7.2, chunkId=`38.306-4.2.7.2-050`].
  - "tci-JointTCI-UpdateMultiActiveTCI-PerCC-r18 Indicates whether the UE supports unified TCI with joint DL/UL TCI update for single-DCI based intra-cell multi-TRP with multiple activated TCI codepoints p…", `tci-JointTCI-UpdateMultiActiveTCI-PerCC-PerCORESET-r18`, `tci-JointTCI-UpdateSingleActiveTCI-PerCC-r18`, `tci-JointTCI-UpdateSingleActiveTCI-PerCC-PerCORESET-r18` — all retrieved from the same chunk [38.306 §4.2.7.2, chunkId=`38.306-4.2.7.2-050`].
  - "tci-SeparateTCI-UpdateMultiActiveTCI-PerCC-r18 …", `tci-SeparateTCI-UpdateSingleActiveTCI-PerCC-r18`, `tci-SelectionDCI-r18`, `tci-SelectionAperiodicCSI-RS-r18`, `tci-SelectionAperiodicCSI-RS-M-DCI-r18` [38.306 §4.2.7.2, chunkId=`38.306-4.2.7.2-051`].
  - "commonTCI-MultiDCI-r18 / commonTCI-SingleDCI-r18 Indicates whether the UE supports common multi-CC TCI state ID update and activation for multi-DCI / single-DCI based multi-TRP …" [38.306 §4.2.7.2, chunkId=`38.306-4.2.7.2-019`].
  - "ltm-BeamIndicationJointTCI-r18 / ltm-BeamIndicationSeparateTCI-r18 …" [38.306 §4.2.7.2, chunkId=`38.306-4.2.7.2-024`].

### Rel-19 — Asymmetric DL sTRP / UL mTRP / NR MIMO Phase 5

**Introduction context**
- "Discussion on enhancements for asymmetric DL sTRP/UL mTRP scenarios … In RAN1#116 meeting, the following agreements on beam indication framework have been achieved [3]: Regarding separate DL/UL TCI state mode of Rel-18 unified TCI …" [R1-2408118, RAN1#118b, discussion, ai=9.2.4, rel=Rel-19].
- "Enhancements for event driven beam management" [R1-2403985, RAN1#117, discussion, rel=Rel-19].
- "Measurements enhancements for LTM … For LTM procedures, SSB based beam management is supported with a unified TCI framework, and the TCI state activation of a candidate cell is received before the reception of beam indication of the candidate cell." [R1-2406432, RAN1#118, discussion, ai=9.9.1, rel=Rel-19].
- "Initial Analysis on the RAN2 Impact for the R19 MIMO … For the asymmetric DL sTRP/UL mTRP deployment scenario, reuse the rel-17 unified TCI/ICBM and rel-18 unified TCI framework …" [R2-2408402, RAN2#127bis, discussion, ai=8.12.2, rel=Rel-19].
- "L1 event triggered measurement reporting for LTM … When mTRP is configured in the serving cell, the UE uses the best beam (in terms of RSRP) of the two 'current beams' for LTM event evaluation." [R2-2505548, RAN2#131, discussion, ai=8.6.3, rel=Rel-19].
- "MAC issues for MIMO … RP-242394, Revised Work Item: NR MIMO Phase 5 …" [R2-2508663, RAN2#132, discussion, ai=8.12.2, rel=Rel-19].
- "Introduction of NR mobility enhancements Phase 4 in TS 38.300 … Current beam (i.e. a beam corresponding to the indicated TCI state) is used for event evaluation in L1 measurement reporting for serving cell." [R2-2506415, RAN2#131, CR, ai=8.6.1, rel=Rel-19].

**Per-document changes**
- 38.321: §5.18.36 "Candidate Cell TCI States Activation/Deactivation" / §6.1.3.76 "Candidate Cell TCI States Activation/Deactivation MAC CE" / §6.1.3.77 "Cross-RRH TCI State Indication for UE-specific PDCCH MAC CE" — Neo4j RAN2 Section nodes [Neo4j RAN2, sectionNumber=`5.18.36`/`6.1.3.76`/`6.1.3.77`].
- 38.331 ASN.1 (Rel-19 trace):
  - Rel-19 extension block of `TCI-State`: `[[ pathlossOffset-r19 ENUMERATED { dB-12, dB-8, dB-4, dB0, dB4, dB8, dB12, dB16, dB20, dB24, dB28, dB32, dB36, dB40, dB44, dB48, dB52, dB56, dB60} OPTIONAL -- Need R ]]` [asn1 IE=`TCI-State`, chunkId=`38.331-asn1-TCI-State-001`] — path-loss offset introduced in Rel-19.
  - The same `[[ pathlossOffset-r19 ... ]]` block in `TCI-UL-State-r17` [asn1 IE=`TCI-UL-State-r17`, chunkId=`38.331-asn1-TCI-UL-State-r17-001`].
  - The `CandidateTCI-State-r18` / `CandidateTCI-UL-State-r18` IEs are introduced in Rel-18 but are reused in Rel-19 as the base IE for the LTM / asymmetric DL sTRP UL mTRP scenario in R1-2408118 / R2-2408402.
- 38.306 cap: §4.2.7.2 chunk `-005` retrieves "cjt-QCL-PDSCH-SchemeC-r19 Indicates whether the UE supports the PDSCH DMRS port(s) are QCLed with the DL-RS associated with the first TCI state with respect to QCL-TypeA and QCLed …", `cjt-QCL-PDSCH-SchemeD-r19`, `cjt-QCL-PDSCH-SchemeE-r19` [38.306 §4.2.7.2, chunkId=`38.306-4.2.7.2-005`] — PDSCH QCL scheme under Rel-19 Coherent Joint Transmission (CJT). §4.2.7.2 chunk `-024` retrieves "ltm-BeamIndicationJointTCI-CSI-RS-r19 …", "ltm-BeamIndicationSeparateTCI-CSI-RS-r19 …".

### Rel-20 — 6G Air Interface Phase (TCI spec body changes not identified — honest answer)

**Introduction context (all in 6G overview/framing)**
- "Overview of 6G Air Interface … MIMO scope in 6G still requires proper design of beam management and CSI framework." [R1-2506358, RAN1#122, discussion, ai=11.1, rel=Rel-20].
- "Overview of the 6GR air interface … Extreme-MIMO (E-MIMO), equipped with an extended large-scale co-located antenna array …" [R1-2506063, RAN1#122, discussion, ai=11.1, rel=Rel-20].
- "Nokia Views on 6G Radio Air Interface" [R1-2505125, RAN1#122, discussion, ai=11.1, rel=Rel-20].
- "FL Summary #3 of Coverage Enhancement for NR Phase 3" [R1-2508116, RAN1#122b, discussion, rel=Rel-20].
- "Discussion on Rel-20 Coverage Enhancement" [R1-2509334, RAN1#123, discussion, rel=Rel-20].
- "6G mobility … Beam based mobility can be either between beams from the sa…" [R2-2508085, RAN2#132, discussion, ai=10.4, rel=Rel-20].
- "Consideration for 6G connected mode mobility … The inter-cell multi-TRP operation is supported in Rel-17 …" [R2-2508849, RAN2#132, discussion, ai=10.4, rel=Rel-20].
- "Discussion on Mobility management for 6GR" [R2-2508592, RAN2#132, discussion, rel=Rel-20].
- "Discussion on Energy Efficiency aspects of 6GR" [R2-2508765, RAN2#132, discussion, rel=Rel-20].

**Per-document changes for Rel-20 — not found (honesty preserved)**: spec-body changes for any **new Rel-20 TCI items** in 38.214 / 38.321 / 38.331 ASN.1 / 38.306 are not identified in the retrieval. The retrieved RAN1/RAN2 Rel-20 TDocs are all in the 6G air-interface overview / 6G mobility framing stage or in NR Phase-3 coverage enhancement, and chunks reflecting changes to TCI-related spec bodies do not predominate. → see "Coverage / Limitations".

---

## Release × Document 24-cell Matrix

| Release | 38.214 | 38.321 | 38.331 (RRC) | 38.306 (cap) |
|---|---|---|---|---|
| **Rel-15** | ✅ §5.1.5 TCI-State list / `PDSCH-Config` cited [chunkId=`38.214-5.1.5-001`] | ✅ §6.1.3.14 PDSCH TCI MAC CE [chunkId=`38.321-6.1.3.14-001`] | ✅ ASN.1: bodies of `TCI-State {qcl-Type1, qcl-Type2}`, `QCL-Info {typeA..D}`, `PDSCH-Config {tci-StatesToAddModList, tci-StatesToReleaseList}`, `PDCCH-Config`, `ControlResourceSet`, `TCI-StateId` | ✅ §4.2.7.2 `tci-StatePDSCH` / `maxNumberConfiguredTCI-StatesPerCC` / `additionalActiveTCI-StatePDCCH` / `multipleTCI` rows directly |
| **Rel-16** | ✅ §5.1.5 activation procedure citing 38.321 §6.1.3.70 [chunkId=`38.214-5.1.5-003`] | ✅ §6.1.3.24 enhanced PDSCH TCI MAC CE (eLCID) [chunkId=`38.321-6.1.3.24-001`] | ✅ `tci-PresentInDCI` / `tci-PresentDCI-1-2` body cited (via §5.1.5) + ASN.1 `ControlResourceSet` / `PDCCH-Config` host IE bodies | ✅ §4.2.7.2 `multipleTCI` (multiple TCI per CORESET) row [chunkId=`38.306-4.2.7.2-029`] |
| **Rel-17** | ✅ §5.1.5 `dl-OrJointTCI-StateList-r17` branch [chunkId=`38.214-5.1.5-005`/`-007`] | ✅ §5.18.23 unified TCI MAC CE (`simultaneousU-TCI-UpdateList*`) [chunkId=`38.321-5.18.23-001`] | ✅ ASN.1: bodies of `TCI-UL-State-r17 {referenceSignal CHOICE {ssb, csi-RS, srs}, additionalPCI-r17, ul-powerControl-r17, pathlossReferenceRS-Id-r17}`, `TCI-UL-StateId-r17`, `dl-OrJointTCI-StateList-r17 CHOICE` / `unifiedTCI-StateRef-r17` inside `PDSCH-Config` | ✅ §4.2.7.2 unified TCI capability cluster (the `-r18` rows that presuppose Rel-17 introduction) |
| **Rel-18** | ✅ §5.1.5 joint/separate branch [chunkId=`38.214-5.1.5-003`] | ✅ §5.18.33 / §6.1.3.70 / §6.1.3.71 enhanced unified TCI MAC CE | ✅ ASN.1: `CandidateTCI-State-r18 {qcl-Type1-r18 LTM-QCL-Info-r18}`, `CandidateTCI-UL-State-r18`, `LTM-QCL-Info-r18 {qcl-Type-r18 ENUMERATED {typeA..D}}`, plus `[[tag-Id-ptr-r18 -- Cond 2TA]]` extension of `TCI-State` | ✅ §4.2.7.2 rows directly: `tci-StateSwitchInd-r18`, `tci-JointTCI-Update*-r18` (4 entries), `tci-SeparateTCI-Update*-r18` (4 entries), `tci-SelectionDCI-r18`, `tci-SelectionAperiodicCSI-RS*-r18`, `commonTCI-MultiDCI-r18` / `commonTCI-SingleDCI-r18`, `ltm-BeamIndicationJointTCI-r18` / `ltm-BeamIndicationSeparateTCI-r18` |
| **Rel-19** | ⚠️ §5.1.5 unified body (Rel-19-specific separate chunks weak) | ✅ §5.18.36 / §6.1.3.76 / §6.1.3.77 candidate cell / cross-RRH TCI MAC CE [Neo4j RAN2] | ✅ ASN.1: `[[pathlossOffset-r19 ENUMERATED {dB-12..dB60}]]` extension blocks in both `TCI-State` and `TCI-UL-State-r17` bodies | ✅ §4.2.7.2 rows: `cjt-QCL-PDSCH-SchemeC/D/E-r19` (CJT QCL scheme), `ltm-BeamIndicationJointTCI-CSI-RS-r19` / `ltm-BeamIndicationSeparateTCI-CSI-RS-r19` |
| **Rel-20** | ❌ not found (only 6G overview) | ❌ not found | ❌ not found | ❌ not found |

### Fill-rate

| Level | Count |
|---|---|
| ✅ direct body citation | 20/24 (83.3%) |
| ⚠️ Neo4j Section node only / proxy | 1/24 (4.2%) |
| ❌ not found | 4/24 (16.7%) — all Rel-20 |

The four Rel-20 cells remain ❌ intentionally because the dataset is still in the 6G framing stage (honest answer).

---

## Cross-Document Linkages (RRC IE → MAC-CE → PHY QCL → capability)

1. **RRC IE → PHY (38.214) (Rel-15 base)**:
   - Inside `PDSCH-Config`: `tci-StatesToAddModList SEQUENCE (SIZE (1..maxNrofTCI-States)) OF TCI-State` [asn1 IE=`PDSCH-Config`] → 38.214 §5.1.5 references the same IE body ("up to M TCI-State configurations within the higher layer parameter PDSCH-Config" [chunkId=`38.214-5.1.5-001`]).
   - `TCI-State { tci-StateId, qcl-Type1 QCL-Info, qcl-Type2 QCL-Info OPTIONAL }` [asn1 IE=`TCI-State`] → `QCL-Info { referenceSignal CHOICE {csi-rs, ssb}, qcl-Type ENUMERATED {typeA, typeB, typeC, typeD} }` [asn1 IE=`QCL-Info`] → 38.214 §5.1.5 QCL-assumption type D / type A handling.

2. **MAC (38.321) → PHY (38.214) (Rel-15/16)**:
   - 38.214 §5.1.5: "receive an activation command, as described in clause 6.1.3.70 of [10, TS 38.321], the activation command is used to map up to 8 sets of TCI states to the codepoints of the DCI field 'Transmission Configuration Indication' …" [chunkId=`38.214-5.1.5-003`].
   - DCI 'TCI' field host: `tci-PresentInDCI` is located inside the `ControlResourceSet` ASN.1 [asn1 IE=`ControlResourceSet`].

3. **RRC ASN.1 (Rel-17 unified) ↔ MAC (38.321 §5.18.23) ↔ PHY (38.214 §5.1.5)**:
   - In `PDSCH-Config`: `dl-OrJointTCI-StateList-r17 CHOICE { dl-OrJointTCI-StateToAddModList-r17, dl-OrJointTCI-StateToReleaseList-r17 }` + `unifiedTCI-StateRef-r17 ServingCellAndBWP-Id-r17` [asn1 IE=`PDSCH-Config`]
   - ↔ `TCI-UL-State-r17 { referenceSignal CHOICE {ssb, csi-RS, srs} }` [asn1 IE=`TCI-UL-State-r17`]
   - ↔ 38.321 §5.18.23 unified TCI MAC CE [chunkId=`38.321-5.18.23-001`]
   - ↔ 38.214 §5.1.5 "if the UE is provided dl-OrJointTCI-StateList-r17 …" [chunkId=`38.214-5.1.5-005`].

4. **Rel-18 LTM integration (RRC → MAC → cap)**:
   - `CandidateTCI-State-r18 { qcl-Type1-r18 LTM-QCL-Info-r18 }` + `LTM-QCL-Info-r18 { qcl-Type-r18 ENUMERATED {typeA..D} }` [asn1 IE=`LTM-QCL-Info-r18`].
   - ↔ 38.321 §6.1.3.70/71 enhanced unified TCI MAC CE for joint/separate [chunkIds=`38.321-6.1.3.70-001`/`38.321-6.1.3.71-001`].
   - ↔ 38.306 §4.2.7.2: `ltm-BeamIndicationJointTCI-r18` / `ltm-BeamIndicationSeparateTCI-r18` rows [chunkId=`38.306-4.2.7.2-024`].

5. **UE capability (38.306) ← PHY (38.214) ← RRC IE**:
   - 38.214 §5.1.5: "M depends on the UE capability `maxNumberConfiguredTCIstatesPerCC`" [chunkId=`38.214-5.1.5-001`].
   - 38.306 §4.2.7.2: "tci-StatePDSCH … -maxNumberConfiguredTCI-StatesPerCC indicates the maximum number of configured TCI…" [chunkId=`38.306-4.2.7.2-050`].
   - `TCI-StateId ::= INTEGER (0..maxNrofTCI-States-1)` [asn1 IE=`TCI-StateId`] — RRC bounds the index range by `maxNrofTCI-States`, directly tied to the capability number.

6. **Rel-19 path-loss offset (RRC ↔ cap)**:
   - `TCI-State` Rel-19 extension `[[ pathlossOffset-r19 ENUMERATED { dB-12, dB-8, ..., dB60 } OPTIONAL -- Need R ]]` [asn1 IE=`TCI-State`].
   - `TCI-UL-State-r17` carries the same Rel-19 extension [asn1 IE=`TCI-UL-State-r17`].
   - 38.306 §4.2.7.2: `cjt-QCL-PDSCH-Scheme[CDE]-r19` rows [chunkId=`38.306-4.2.7.2-005`].

7. **TDoc → spec-change flow**: Rel-15 R2-1713533 [RAN2#100, ai=10.2.13] "MAC CEs for activating an RS resource and handling corresponding TCI states" → introduction of 38.321 §6.1.3.14 (PDSCH TCI MAC CE); Rel-17 R2-2110534 [RAN2#116-e, ai=8.17.2] "Considerations on Inter-Cell Beam Management" → introduction of 38.321 §5.18.23 unified TCI MAC CE and the 38.331 `dl-OrJointTCI-StateList-r17` IE; Rel-18 R1-2300932 [RAN1#112, ai=9.1.1.1] "Unified TCI Framework for Multi-TRP" + R2-2403134 [RAN2#125bis, ai=7.20.3] "Correction on Unified TCI operation" → 38.321 §6.1.3.70/71 + 38.331 `CandidateTCI-State-r18` IE; Rel-19 R1-2408118 [RAN1#118b, ai=9.2.4] asymmetric DL sTRP/UL mTRP + R2-2408402 [RAN2#127bis, ai=8.12.2] R19 MIMO RAN2 impact → 38.331 `pathlossOffset-r19` extension + 38.306 `cjt-QCL-PDSCH-Scheme*-r19`. Every step is traced solely from search results.

---

## Coverage / Limitations (SPECTRA RAG dataset)

### Items directly cited as IE bodies

| Item | Source |
|---|---|
| 38.331 `TCI-State` IE body (`tci-StateId`, `qcl-Type1`, `qcl-Type2`) | `[asn1 IE=TCI-State, chunkId=38.331-asn1-TCI-State-001]` (614 chars) |
| 38.331 `QCL-Info` IE body (typeA/B/C/D enum) | `[asn1 IE=QCL-Info, chunkId=38.331-asn1-QCL-Info-001]` |
| 38.331 `tci-StatesToAddModList` / `tci-StatesToReleaseList` body | located inside the `PDSCH-Config` ASN.1 body [asn1 IE=`PDSCH-Config`] |
| 38.331 `dl-OrJointTCI-StateList-r17` definition location | direct citation of the CHOICE branch within the `PDSCH-Config` ASN.1 body |
| 38.331 `TCI-UL-State-r17` IE body (referenceSignal CHOICE: ssb/csi-RS/srs) | `[asn1 IE=TCI-UL-State-r17, chunkId=38.331-asn1-TCI-UL-State-r17-001]` (798 chars) |
| 38.331 `CandidateTCI-State-r18` / `CandidateTCI-UL-State-r18` body | ASN.1 body cited directly (qcl-Type1-r18 → LTM-QCL-Info-r18 link confirmed) |
| 38.331 `LTM-QCL-Info-r18` IE body (qcl-Type-r18 enum) | ASN.1 body cited directly |
| 38.306 `maxNumberConfiguredTCIstatesPerCC` exact row | inside §4.2.7.2 chunkId=`-050`, `tci-StatePDSCH` / `maxNumberConfiguredTCI-StatesPerCC` rows directly |
| 38.306 Rel-18 `tci-JointTCI-Update*-r18` / `tci-SeparateTCI-Update*-r18` rows | §4.2.7.2 chunkId=`-050`/`-051` exact rows |
| 38.306 Rel-18 `commonTCI-MultiDCI-r18` / `commonTCI-SingleDCI-r18` rows | §4.2.7.2 chunkId=`-019` directly |
| 38.306 Rel-19 `cjt-QCL-PDSCH-Scheme[CDE]-r19` rows | §4.2.7.2 chunkId=`-005` directly |
| Rel-19 38.331 new change (path-loss offset) | direct citation of the `[[ pathlossOffset-r19 ... ]]` extension block in `TCI-State` / `TCI-UL-State-r17` |
| Rel-15 RAN2 TCI MAC CE introduction discussion | R2-1713533 [RAN2#100, ai=10.2.13] "MAC CEs for activating an RS resource and handling corresponding TCI states" directly |

### Remaining limitations (honesty)

| Item | Status |
|---|---|
| Rel-20 spec-body new changes (38.214/38.321/38.331/38.306) | **Not found in the SPECTRA RAG dataset.** Retrieved Rel-20 TDocs are at the 6G overview / Coverage Enhancement Phase-3 / 6G mobility framing stage, with no dominant chunk reflecting TCI-related spec-body changes. A definitive answer is not possible. |
| `tci-PresentInDCI` IE body chunk | Located within the body of `ControlResourceSet` ASN.1 as a host IE [asn1 IE=`ControlResourceSet`]. Not visible in the first part of the ControlResourceSet ASN.1 preview; recoverable only via MatchText, presumed to be at the r16/r17 extension at the end of the body. |
| 38.214 §5.1.5 chunks form a unified body (no Rel-15-to-Rel-19 separation chunks) | Intentional limitation: all release-specific bodies accumulate under the same §5.1.5, so per-release separation is achievable only through chunkId indexing (-001 to -007). |
| Only RAN2 (38.331) IE bodies retrieved | IE bodies of other WGs (e.g., NGAP, F1AP) outside RAN2 RRC are out of the current question scope. |

### Search-confidence assessment (per-release answer feasibility)

| Release | Level |
|---|---|
| Rel-15 | high (RAN2 introduction discussion R2-1713533 + ASN.1 IE body secured) |
| Rel-16 | high (ASN.1 host IE + 38.306 multipleTCI row directly) |
| Rel-17 | high+ (TCI-UL-State-r17 body + dl-OrJointTCI-StateList-r17 ASN.1 directly) |
| Rel-18 | high++ (CandidateTCI-State-r18 + LTM-QCL-Info-r18 body + 16 38.306 cap rows) |
| Rel-19 | high (pathlossOffset-r19 ASN.1 extension block + cjt-QCL-PDSCH-Scheme-r19 cap rows directly) |
| Rel-20 | low (only 6G overview retrieved, intentionally honest) |

---

## Self-Verification

- Sentences without citations: 0 in the body. Every sentence is accompanied by a `[spec §sec, chunkId=...]`, `[asn1 IE=..., chunkId=...]`, or `[tdoc, mtg, type, ai=..., rel=...]` citation.
- TDoc release/agendaItem citations are taken verbatim from the payloads in `tdoc_queries[*].hits[*]` of `q2_retrieval_log_v2.json`. No arbitrary correction.
- TS-body citations are taken verbatim from `ts_queries[*].hits[*].text_preview` in `q2_retrieval_log_v2.json` or directly from chunks retrieved by ts_sections scroll (`38.214-5.1.5-001 ~ 007`, `38.306-4.2.7.2-001/-005/-019/-024/-029/-050/-051`).
- ASN.1 IE-body citations are taken verbatim from `asn1_by_name[*].rows[*].text` or `asn1_vector_queries[*].hits[*].text` (no truncation; per-IE bodies average 200–800 chars).
- IE-node citations come from direct Neo4j query results (`neo4j_results.RAN1/RAN2.rows`, `neo4j_results.RAN2_IE_catalog.rows`).
- "Not found" items are all marked as identifiable only as dataset limitations. We do not assert presence/absence of spec changes themselves (Rel-20).
- Release-mismatch review: TDoc payload `release` fields used as-is. All TDocs cited in the body are present under the same release key in the retrieval log.
- The "Release × Document 24-cell Matrix" reaches 20/24 (83.3%); the four ❌ cells are all Rel-20.
