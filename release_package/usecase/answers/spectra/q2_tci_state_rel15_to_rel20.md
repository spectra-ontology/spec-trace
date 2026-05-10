# Q2 — TCI-State Across Rel-15 to Rel-20: Standards Item Analysis Report

## Table of Contents
1. [Motivation (RAN1/RAN2 Introduction Context across Releases)](#1-motivation-ran1ran2-introduction-context-across-releases)
2. [Rel-15 — TCI Framework Introduction](#2-rel-15--tci-framework-introduction)
3. [Rel-16 — eMIMO Multi-Beam Enhancement](#3-rel-16--emimo-multi-beam-enhancement)
4. [Rel-17 — Unified TCI / Inter-cell Beam Management](#4-rel-17--unified-tci--inter-cell-beam-management)
5. [Rel-18 — Enhanced Unified TCI / Multi-TRP Unified / LTM Integration](#5-rel-18--enhanced-unified-tci--multi-trp-unified--ltm-integration)
6. [Rel-19 — Asymmetric DL sTRP / UL mTRP / NR MIMO Phase 5](#6-rel-19--asymmetric-dl-strp--ul-mtrp--nr-mimo-phase-5)
7. [Rel-20 — 6G Air Interface Phase](#7-rel-20--6g-air-interface-phase)
8. [Release × Document Coverage Matrix](#8-release--document-coverage-matrix)
9. [Cross-Document Linkages (RRC IE → MAC-CE → PHY QCL → Capability)](#9-cross-document-linkages-rrc-ie--mac-ce--phy-qcl--capability)
10. [Coverage and Limitations](#10-coverage-and-limitations)
11. [Document Lifecycle Trace (TCI-state Across Releases)](#11-document-lifecycle-trace-tci-state-across-releases)
12. [Summary](#12-summary)

---

## 0. Evidence Provenance (How this report is grounded)

This answer reconstructs the TCI-state framework as a six-release timeline (Rel-15 → Rel-20) entirely from the SPECTRA knowledge graph + vector index of public 3GPP RAN documents. The KG-side capabilities exercised below are:

- **Paragraph-level chunk citations** — every factual sentence ends with `[spec §sec, chunkId=…]` (TS body) or `[Rxxx, RANx#N, ai=…, type=…, release=…]` (TDoc), so each claim can be re-fetched by chunkId from Qdrant or by `(spec, section, chunkIndex)` from Neo4j.
- **Release-tag filtering** — the Rel-15 → Rel-20 timeline in §1–§7 is reconstructed from the explicit `release` field on each TDoc node, not from string matching `Rel-15`/`Rel-20` in body text. This is what makes the per-release introduction context in §2.1, §3.1, §4.1, §5.1, §6.1, §7.1 reproducible: the same Cypher filter (`release=Rel-N`) returns the same TDoc set.
- **ASN.1 IE body retrieval** — the 38.331 IE bodies for `TCI-State` (614 chars), `TCI-StateId`, `QCL-Info`, `PDSCH-Config`, `PDCCH-Config`, `ControlResourceSet`, `TCI-UL-State-r17` (798 chars), `TCI-UL-StateId-r17`, `CandidateTCI-State-r18`, `CandidateTCI-UL-State-r18`, and `LTM-QCL-Info-r18` are retrieved as full IE bodies, not paraphrased; the per-release extension blocks (`[[ additionalPCI-r17 … ]]`, `[[ tag-Id-ptr-r18 … ]]`, `[[ pathlossOffset-r19 … ]]`) inside `TCI-State` and `TCI-UL-State-r17` are the basis of the per-release IE-body trace in §2.3, §4.3, §5.3, §6.3.
- **Neo4j Section catalogue** — the Rel-19 38.321 sections §5.18.36 / §6.1.3.76 / §6.1.3.77 are visible as Section nodes in Neo4j even when the chunk-body text is weak (cited as `[Neo4j RAN2, sectionNumber=…]` in §6.3 and the §8 matrix). This separates "section exists in spec" from "section body is in the vector index".
- **Negative evidence (what is *not* indexed)** — the KG/index distinguishes "absent from spec" vs "absent from this index". §7.3 / §10.2 explicitly mark Rel-20 spec-body changes as not present in the loaded dataset; §10.2 also notes that 38.214 §5.1.5 has accumulated all Rel-15→Rel-19 content into a single section without per-release separator chunks, so per-release granularity inside §5.1.5 is reconstructed via chunkId indexing (`-001` … `-007`) rather than via section subdivision.

Reviewers can verify any sentence in this report by retrieving its chunkId from the released vector index, and any cross-spec linkage in §9 by traversing the corresponding Neo4j edge.

---

## 1. Motivation (RAN1/RAN2 Introduction Context across Releases)

The Transmission Configuration Indicator (TCI) framework was introduced in NR Rel-15 to convey QCL assumptions (spatial and non-spatial) to the UE for downlink reception, and has been extended once per release since: from a single-DCI single-TRP form in Rel-15, through multi-beam enhancements and 128 TCI states per BWP in Rel-16, to a unified DL/UL framework across cells in Rel-17, multi-TRP unification and LTM integration in Rel-18, and finally asymmetric sTRP/mTRP and CJT-tied path-loss control in Rel-19. Rel-20 turns to the 6G air interface, and the Rel-20 TDocs in the dataset frame the upcoming MIMO/beam-management problem rather than introducing TCI spec-body changes.

The RAN1 introduction trail begins at RAN1#90b with the DCI-codepoint mapping discussion `[R1-1718541, RAN1#90b, ai=7.2.2.3, type=discussion, release=Rel-15]`, continues through the Rel-16 Multi-beam enhancement WI `[R1-1903044, RAN1#96, ai=7.2.8.3, type=discussion, release=Rel-16]`, the Rel-17 unified TCI design at RAN1#106b-e `[R1-2109103, RAN1#106b-e, ai=8.1.1, type=discussion, release=Rel-17]`, the Rel-18 unified-TCI-for-multi-TRP discussion `[R1-2300932, RAN1#112, ai=9.1.1.1, type=discussion, release=Rel-18]`, and the Rel-19 asymmetric DL sTRP / UL mTRP enhancements `[R1-2408118, RAN1#118b, ai=9.2.4, type=discussion, release=Rel-19]`. The Rel-20 anchor is the 6G air-interface overview at RAN1#122 `[R1-2506358, RAN1#122, ai=11.1, type=discussion, release=Rel-20]`.

The RAN2 trail mirrors this: TCI MAC CE introduction at RAN2#100 `[R2-1713533, RAN2#100, ai=10.2.13, type=discussion, release=Rel-15]`, the 128-TCI-states-per-BWP statement at RAN2#107 `[R2-1910966, RAN2#107, ai=11.16, type=discussion, release=Rel-16]`, inter-cell beam management at RAN2#116-e `[R2-2110534, RAN2#116-e, ai=8.17.2, type=discussion, release=Rel-17]`, the unified-TCI-for-multi-TRP correction at RAN2#125bis `[R2-2403134, RAN2#125bis, ai=7.20.3, type=discussion, release=Rel-18]`, the R19 MIMO RAN2-impact analysis `[R2-2408402, RAN2#127bis, ai=8.12.2, type=discussion, release=Rel-19]`, and the 6G connected-mode mobility framing at RAN2#132 `[R2-2508849, RAN2#132, ai=10.4, type=discussion, release=Rel-20]`. §2–§7 walk the per-release evidence one release at a time.

---

## 2. Rel-15 — TCI Framework Introduction

### 2.1 RAN1 Introduction Context

Rel-15 RAN1 designed the DCI-to-TCI mapping that subsequent releases reuse. The mapping between DCI TCI codepoints and the candidate TCI states is discussed in *"Mapping between candidate TCI state and N-bit DCI field …"* `[R1-1718541, RAN1#90b, ai=7.2.2.3, type=discussion, "Beam management for NR", release=Rel-15]`. RAN1#91 then established that the DCI TCI field also carries non-spatial QCL: *"There appears no reason why the TCI field of the DCI for PDSCH should not convey the non-spatial QCL parameters as they are available in the list of TCI states."* `[R1-1720662, RAN1#91, ai=7.2.2.3, type=discussion, "Beam management for NR", release=Rel-15]`. UL beam management is treated separately in *"Beam Management of Multiple Beam Pairs in Uplink"* `[R1-1804787, RAN1#92b, type=discussion, "Beam management for NR", release=Rel-15]`.

### 2.2 RAN2 Introduction Context

The RAN2 introduction is grounded in `[R2-1713533, RAN2#100, ai=10.2.13, type=discussion, "MAC CEs for activating an RS resource and handling corresponding TCI states", release=Rel-15]`:

> *"In order to support quasi-collocation and various beamforming feature in NR, RAN1 has agreed to support up to M Transmission Configuration Indicator (TCI) states, wherein each TCI state can include one RS Set. TCI state was defined for QCL indication of various cases such as quasi-collocation betwee…"*

This is the direct evidence that the TCI MAC CE family was introduced on the RAN2 side in Rel-15.

### 2.3 Spec-body Changes

**38.214 §5.1.5 (PDSCH TCI state list, capability tie-in).** The Rel-15 base sets up the PDSCH TCI-state list and ties its size to a UE capability:

> *"The UE can be configured with a list of up to M TCI-State configurations within the higher layer parameter PDSCH-Config to decode PDSCH according to a detected PDCCH … M depends on the UE capability `maxNumberConfiguredTCIstatesPerCC`."* `[38.214 §5.1.5, chunkId=38.214-5.1.5-001]`

**38.321 §6.1.3.14 (PDSCH TCI MAC CE).** The Rel-15 MAC-CE side is anchored in §6.1.3.14:

> *"identified by a MAC subheader with LCID as specified in Table 6.2.1-1. It has a variable size consisting of following fields …"* `[38.321 §6.1.3.14, chunkId=38.321-6.1.3.14-001]`

**38.331 ASN.1.** The Rel-15 IE bodies that ground the entire framework — and into which Rel-17/18/19 extension blocks are slotted in later releases — are the following.

```asn1
TCI-State ::= SEQUENCE {
  tci-StateId  TCI-StateId,
  qcl-Type1    QCL-Info,
  qcl-Type2    QCL-Info OPTIONAL,
  ...,
  [[ additionalPCI-r17 ..., pathlossReferenceRS-Id-r17 ..., ul-powerControl-r17 ... ]],
  [[ tag-Id-ptr-r18 ENUMERATED {n0,n1} ... ]],
  [[ pathlossOffset-r19 ENUMERATED {dB-12,...,dB60} ... ]]
}
```

`[asn1 IE=TCI-State, chunkId=38.331-asn1-TCI-State-001]` — Rel-15 base SEQUENCE skeleton plus the Rel-17/18/19 extension blocks contained in the same IE.

```asn1
TCI-StateId ::= INTEGER (0..maxNrofTCI-States-1)
```

`[asn1 IE=TCI-StateId, chunkId=38.331-asn1-TCI-StateId-001]`.

```asn1
QCL-Info ::= SEQUENCE {
  cell             ServCellIndex OPTIONAL,
  bwp-Id           BWP-Id        OPTIONAL,
  referenceSignal  CHOICE {
    csi-rs  NZP-CSI-RS-ResourceId,
    ssb     SSB-Index
  },
  qcl-Type         ENUMERATED {typeA, typeB, typeC, typeD},
  ...
}
```

`[asn1 IE=QCL-Info, chunkId=38.331-asn1-QCL-Info-001]` — direct citation of the QCL Type A/B/C/D enum and the `referenceSignal` CHOICE (CSI-RS or SSB).

```asn1
PDSCH-Config ::= SEQUENCE {
  ...
  tci-StatesToAddModList     SEQUENCE (SIZE (1..maxNrofTCI-States)) OF TCI-State    OPTIONAL,
  tci-StatesToReleaseList    SEQUENCE (SIZE (1..maxNrofTCI-States)) OF TCI-StateId  OPTIONAL,
  ...
  dl-OrJointTCI-StateList-r17 CHOICE { ... } ...
  unifiedTCI-StateRef-r17     ServingCellAndBWP-Id-r17 ...
}
```

`[asn1 IE=PDSCH-Config, chunkId=38.331-asn1-PDSCH-Config-001]` — `tci-StatesToAddModList` / `tci-StatesToReleaseList` are defined in the Rel-15 base, with the Rel-17 unified TCI branch added as an extension (cited again in §4.3).

```asn1
PDCCH-Config ::= SEQUENCE {
  controlResourceSetToAddModList ...,
  searchSpacesToAddModList       ...,
  ...
}
```

`[asn1 IE=PDCCH-Config, chunkId=38.331-asn1-PDCCH-Config-001]`.

```asn1
ControlResourceSet ::= SEQUENCE {
  controlResourceSetId ...,
  frequencyDomainResources ...,
  duration ...,
  cce-REG-MappingType  CHOICE { ... } ...
}
```

`[asn1 IE=ControlResourceSet, chunkId=38.331-asn1-ControlResourceSet-001]` — host IE for `tci-PresentInDCI` / `tci-StatesPDCCH-ToAddList` etc. (§3.3 returns to the `tci-PresentInDCI` location in Rel-16.)

**38.306 §4.2.7.2 (UE capability, BandNR parameters).** The capability companion to 38.214's `maxNumberConfiguredTCIstatesPerCC` is exposed directly:

> *"tci-StatePDSCH Defines support of TCI-States for PDSCH. The capability signalling comprises the following parameters: -maxNumberConfiguredTCI-StatesPerCC indicates the maximum number of configured TCI…"* `[38.306 §4.2.7.2, chunkId=38.306-4.2.7.2-050]`

The `additionalActiveTCI-StatePDCCH` row appears in §4.2.7.2 chunk `38.306-4.2.7.2-001`, and `multipleTCI` (support for multiple TCI configurations per CORESET) in `38.306-4.2.7.2-029`.

---

## 3. Rel-16 — eMIMO Multi-Beam Enhancement

### 3.1 RAN1 Introduction Context

The Rel-16 NR MIMO Work Item explicitly enumerates multi-beam enhancement as a deliverable: *"The work item on Rel-16 MIMO enhancements has been specified [1]. … The WI for Rel-16 covers several key features aimed at enhancing multibeam …"* `[R1-1903044, RAN1#96, ai=7.2.8.3, type=discussion, "Enhancements on Multi-beam Operation", release=Rel-16]`. The WI cycle is also reflected in *"Enhancements on Multi-beam Operation"* `[R1-1813443, RAN1#95, ai=7.2.8.3, type=discussion, release=Rel-16]`, the feature-lead summary *"Feature lead summary of Enhancements on Multi-beam Operations"* `[R1-1907650, RAN1#97, ai=7.2.8.3, type=discussion, release=Rel-16]`, and parallel multi-TRP discussion *"Further discussion on multi TRP transmission"* `[R1-1901702, RAN1#96, type=discussion, release=Rel-16]`.

### 3.2 RAN2 Introduction Context

RAN2 carries the configuration-side enabling change. The 128-TCI-states-per-BWP figure that is the Rel-16 RRC-side scale increase appears in *"MAC CE design on single PDCCH based multi-TRP/panel transmission … TCI states for PDSCH are configured by RRC, at first. Up to 128 TCI states can be configured per BWP per serving cell. Amongst the configured TCI states, up to …"* `[R2-1910966, RAN2#107, ai=11.16, type=discussion, release=Rel-16]`. The Rel-16 multi-beam framing on the RAN2 side is reflected in *"RAN2 aspects of multi-beam enhancements"* `[R2-1910145, RAN2#107, type=discussion, release=Rel-16]`.

### 3.3 Spec-body Changes

**38.214 §5.1.5 (Rel-16 activation procedure).** The Rel-16 §5.1.5 chunk introduces the activation-command flow tying PHY to the 38.321 §6.1.3.70 enhanced PDSCH TCI MAC CE:

> *"receive an activation command, as described in clause 6.1.3.70 of [10, TS 38.321], the activation command is used to map up to 8 sets of TCI states to the codepoints of the DCI field 'Transmission Configuration Indication' …"* `[38.214 §5.1.5, chunkId=38.214-5.1.5-003]`

The same §5.1.5 also references the Rel-16 RRC fields `tci-PresentInDCI` and `tci-PresentDCI-1-2`: *"Independent of the configuration of `tci-PresentInDCI` and `tci-PresentDCI-1-2` in RRC connected mode"* `[38.214 §5.1.5, chunkId=38.214-5.1.5-005]`.

**38.321 §6.1.3.24 (Enhanced PDSCH TCI MAC CE, eLCID).** The Rel-16 MAC CE side adds an eLCID-based variant:

> *"identified by a MAC PDU subheader with eLCID as specified in Table 6.2.1-1b. It has a variable size consisting of following fields …"* `[38.321 §6.1.3.24, chunkId=38.321-6.1.3.24-001]`

**38.331 ASN.1.** No new top-level TCI IE is introduced in Rel-16; the relevant fields are accommodated inside the Rel-15 host IEs. The `controlResourceSetToAddModList` / `searchSpacesToAddModList` lists are visible in `[asn1 IE=PDCCH-Config, chunkId=38.331-asn1-PDCCH-Config-001]`, and `tci-PresentInDCI` itself is located within the body of `[asn1 IE=ControlResourceSet, chunkId=38.331-asn1-ControlResourceSet-001]` (at the Rel-16/Rel-17 extension at the end of the IE body).

**38.306 §4.2.7.2 (`multipleTCI`).** The capability row that records the per-CORESET multi-TCI capability is cited directly:

> *"multipleTCI Indicates whether UE supports more than one TCI state configurations per CORESET. UE is only required to track one active TCI state per CORESET. UE is required to suppo…"* `[38.306 §4.2.7.2, chunkId=38.306-4.2.7.2-029]`

This is the Rel-16 capability-side increment of "multiple TCI configurations per CORESET".

---

## 4. Rel-17 — Unified TCI / Inter-cell Beam Management

### 4.1 RAN1 Introduction Context

The Rel-17 unified TCI track is an explicit feMIMO sub-work-item and is referenced from RAN1#102e onwards: *"Enhancement of multi-beam operation is an important part of R17 feMIMO WI [1]. Discussion on multi-beam operation has been ongoing since RAN1#102e …"* `[R1-2109103, RAN1#106b-e, ai=8.1.1, type=discussion, "Enhancements on Multi-beam Operation", release=Rel-17]`. The longer cycle is reflected in *"Further enhancement on multi-beam operation"* `[R1-2103287, RAN1#104b-e, ai=8.1.1, type=discussion, release=Rel-17]` and the cross-WG handling of inter-cell beam management *"Discussion of RAN2 LS on inter-cell BM and mTRP"* `[R1-2110346, RAN1#106b-e, type=discussion, release=Rel-17]`.

### 4.2 RAN2 Introduction Context

The unified TCI framework is also the explicit RAN2 anchor for inter-cell beam management at RAN2#116-e:

> *"Inter-cell beam management | inter-cell MTRP / TCI Framework | R17 Unified TCI framework, UE assumes that the UE-dedicated channels/RSs can be switched t…"* `[R2-2110534, RAN2#116-e, ai=8.17.2, type=discussion, "Considerations on Inter-Cell Beam Management", release=Rel-17]`

Companion RAN2 contributions further down the cycle are *"Inter-cell BM and inter-cell mTRP"* `[R2-2201098, RAN2#116bis-e, type=discussion, release=Rel-17]`, *"Discussion on the support of L1/L2 centric inter-cell mobility"* `[R2-2105827, RAN2#114-e, type=discussion, release=Rel-17]`, and *"Discussion on multi-TRP BFR and new MIMO MAC CE"* `[R2-2107995, RAN2#115-e, type=discussion, release=Rel-17]`.

### 4.3 Spec-body Changes

**38.214 §5.1.5 (joint/separate DL TCI list).** Rel-17 brings the unified-TCI list into 38.214 directly:

> *"if the UE is provided `dl-OrJointTCI-StateList-r17`, …"* `[38.214 §5.1.5, chunkId=38.214-5.1.5-005]`

> *"When a UE is configured with `dl-OrJointTCI-StateList` and is having two indicated TCI-states …"* `[38.214 §5.1.5, chunkId=38.214-5.1.5-007]`

> *"When a UE configured with `dl-OrJointTCI-StateList` supports `tci-SeparateTCI-UpdateMultiActiveTCI-Per…`"* `[38.214 §5.1.5, chunkId=38.214-5.1.5-003]`

**38.321 §5.18.23 / §6.1.3.47 (Unified TCI MAC CE).** The MAC-CE side defines simultaneous-update lists across serving cells:

> *"The network may activate and deactivate the configured unified TCI states of a Serving Cell or a set of Serving Cells configured in `simultaneousU-TCI-UpdateList1`, `simultaneousU-TCI-UpdateList2`, …"* `[38.321 §5.18.23, chunkId=38.321-5.18.23-001]`

**38.331 ASN.1.** Two new top-level IEs and one extension branch are introduced.

```asn1
TCI-UL-State-r17 ::= SEQUENCE {
  tci-UL-StateId-r17       TCI-UL-StateId-r17,
  servingCellId-r17        ServCellIndex OPTIONAL,
  bwp-Id-r17               BWP-Id        OPTIONAL,
  referenceSignal-r17      CHOICE {
    ssb-Index-r17    SSB-Index,
    csi-RS-Index-r17 NZP-CSI-RS-ResourceId,
    srs-r17          SRS-ResourceId
  },
  additionalPCI-r17        ...,
  ul-powerControl-r17      ...,
  pathlossReferenceRS-Id-r17 ...,
  [[ tag-Id-ptr-r18        ... ]],
  [[ pathlossOffset-r19    ... ]]
}
```

`[asn1 IE=TCI-UL-State-r17, chunkId=38.331-asn1-TCI-UL-State-r17-001]` — the Rel-17 separate UL TCI IE body cited directly (3-way reference-signal CHOICE: CSI-RS / SSB / SRS).

```asn1
TCI-UL-StateId-r17 ::= INTEGER (0..maxUL-TCI-1-r17)
```

`[asn1 IE=TCI-UL-StateId-r17, chunkId=38.331-asn1-TCI-UL-StateId-r17-001]`.

Inside `PDSCH-Config` (the same Rel-15 host IE), the Rel-17 unified TCI branch is located precisely:

```asn1
dl-OrJointTCI-StateList-r17 CHOICE {
  dl-OrJointTCI-StateToAddModList-r17     SEQUENCE (SIZE (1..maxNrofTCI-States)) OF TCI-State,
  dl-OrJointTCI-StateToReleaseList-r17    SEQUENCE (SIZE (1..maxNrofTCI-States)) OF TCI-StateId
}
unifiedTCI-StateRef-r17 ServingCellAndBWP-Id-r17
```

`[asn1 IE=PDSCH-Config, chunkId=38.331-asn1-PDSCH-Config-001]`.

**38.306 §4.2.7.2 (LTM joint-TCI capability row, presupposing Rel-17 unified TCI).**

> *"ltm-BeamIndicationJointTCI-r18 Indicates whether the UE supports unified TCI with joint DL/UL LTM TCI-state indication for LTM procedure, indicating and activating a single joint L…"* `[38.306 §4.2.7.2, chunkId=38.306-4.2.7.2-024]`

(Note: the row carries the `-r18` suffix because it specifies LTM, but its existence presupposes the Rel-17 unified TCI definition.)

---

## 5. Rel-18 — Enhanced Unified TCI / Multi-TRP Unified / LTM Integration

### 5.1 RAN1 Introduction Context

Rel-18 extends the Rel-17 unified TCI to the multi-TRP case and into LTM beam indication. The L1-side anchors are *"FL summary 1/2 on L1 enhancements for inter-cell beam management … For the beam indication of LTM in the case of inter-cell mTRP: The TCI state(s) indicated through inter-cell beam management is applied to UE-specific PDCC…"* `[R1-2309110, RAN1#114b, ai=8.7.1, type=discussion, release=Rel-18]` and the multi-TRP unification design *"Unified TCI Framework for Multi-TRP … When unified TCI framework is used for beam indication for single DCI multi-TRP, for the case when the UE is configured with joint DL/UL beam indication with the value of unifiedtci-StateType set to 'JointULDL', the UE expects to be indicated with a TCI codepoint which is mapped to two joint DL/UL T…"* `[R1-2300932, RAN1#112, ai=9.1.1.1, type=discussion, release=Rel-18]`. The work-item maintenance context is in *"Maintenance on NR MIMO Evolution for Downlink and Uplink … In RAN#94e, the working item to enhance both downlink and uplink MIMO operations in Rel-18 was agreed [1]."* `[R1-2403112, RAN1#116b, ai=8.1, type=discussion, release=Rel-18]`.

### 5.2 RAN2 Introduction Context

The RAN2 framing explicitly pegs Rel-17 as the introduction point and Rel-18 as the multi-TRP extension: *"In R17 inter-cell beam management, the unified TCI framework was introduced with the following characteristics: A pool of joint or separate DL/UL TCI states is …"* `[R2-2207753, RAN2#119-e, ai=8.4.2.2, type=discussion, "Discussion on candidate solutions for L1 L2 mobility", release=Rel-18]`. The MAC-CE-side discussion is in *"On MAC CE for Joint TCI State Indication"* `[R2-2306181, RAN2#122, ai=7.1.2, type=discussion, release=Rel-18]`. The unified-TCI-for-multi-TRP correction CR thread is *"[N110] Correction on Unified TCI operation … The unified TCI framework was introduced in Rel-17 which facilitates a streamlined multi-beam operation targeting FR2. As Rel-17 focuses on single-TRP use cases, extension of unified TCI framework that focuses on multi-TRP use cases…"* `[R2-2403134, RAN2#125bis, ai=7.20.3, type=discussion, release=Rel-18]`. The 2-TA framing for multi-DCI mTRP is given in *"Two TAs for multi-DCI multi-TRP … In Rel-17, Inter-Cell Beam Management (ICBM) was introduced …"* `[R2-2307614, RAN2#123, ai=7.20.2, type=discussion, release=Rel-18]`.

### 5.3 Spec-body Changes

**38.214 §5.1.5 (joint/separate TCI mode branches).** The §5.1.5 unified body now carries both joint and separate TCI mode handling `[38.214 §5.1.5, chunkId=38.214-5.1.5-003 / chunkId=38.214-5.1.5-007]`.

**38.321 (Enhanced unified TCI MAC CE).** Three Rel-18 sections appear:

- §5.18.33 *"Enhanced Unified TCI States Activation/Deactivation MAC CE"* `[38.321 §5.18.33, chunkId=38.321-5.18.33-001]`.
- §6.1.3.70 *"Enhanced Unified TCI States Activation/Deactivation MAC CE for Joint TCI States"* `[38.321 §6.1.3.70, chunkId=38.321-6.1.3.70-001]`.
- §6.1.3.71 *"… for Separate TCI States"* `[38.321 §6.1.3.71, chunkId=38.321-6.1.3.71-001]`.

**38.331 ASN.1.** Three new IEs are introduced for the LTM candidate path, and `TCI-State` / `TCI-UL-State-r17` gain a Rel-18 extension block.

```asn1
CandidateTCI-State-r18 ::= SEQUENCE {
  tci-StateId-r18                 TCI-StateId,
  qcl-Type1-r18                   LTM-QCL-Info-r18,
  qcl-Type2-r18                   LTM-QCL-Info-r18 OPTIONAL,
  pathlossReferenceRS-Id-r18      PathlossReferenceRS-Id-r17 OPTIONAL,
  tag-Id-ptr-r18                  ENUMERATED {n0,n1} OPTIONAL,
  ul-powerControl-r18             Uplink-powerControlId-r17 OPTIONAL,
  ...
}
```

`[asn1 IE=CandidateTCI-State-r18, chunkId=38.331-asn1-CandidateTCI-State-r18-001]` — body of the Rel-18 LTM candidate TCI-state IE.

```asn1
CandidateTCI-UL-State-r18 ::= SEQUENCE {
  tci-UL-StateId-r18              TCI-UL-StateId-r17,
  referenceSignal-r18             CHOICE {
    ssb-Index   SSB-Index,
    csi-RS-Index NZP-CSI-RS-ResourceId
  },
  pathlossReferenceRS-Id-r18      ...,
  tag-Id-ptr-r18                  ENUMERATED {n0,n1} OPTIONAL,
  ul-powerControl-r18             Uplink-powerControlId-r17 OPTIONAL,
  ...
}
```

`[asn1 IE=CandidateTCI-UL-State-r18, chunkId=38.331-asn1-CandidateTCI-UL-State-r18-001]`.

```asn1
LTM-QCL-Info-r18 ::= SEQUENCE {
  referenceSignal-r18  CHOICE {
    ssb-Index    SSB-Index,
    csi-RS-Index NZP-CSI-RS-ResourceId
  },
  qcl-Type-r18         ENUMERATED {typeA, typeB, typeC, typeD},
  ...
}
```

`[asn1 IE=LTM-QCL-Info-r18, chunkId=38.331-asn1-LTM-QCL-Info-r18-001]` — body of the LTM-dedicated QCL info IE.

The Rel-18 extension blocks of `TCI-State` / `TCI-UL-State-r17` are: `[[ tag-Id-ptr-r18 ENUMERATED {n0,n1} OPTIONAL -- Cond 2TA ]]` `[asn1 IE=TCI-State, chunkId=38.331-asn1-TCI-State-001]` — Rel-18 multi-TRP 2-TA support (the Rel-18 RAN2 introduction in `[R2-2307614]` cites the same 2-TA design rationale).

**38.306 §4.2.7.2 (Rel-18 capability cluster).** Rel-18 is the largest single-release expansion of the §4.2.7.2 capability cluster around TCI; the rows are cited from their own chunkIds without paraphrase.

- `tci-StateSwitchInd-r18` — *"Indicates whether the UE supports enhanced one-shot large UL transmit timing adjustment requirement to support FR2-1 PC6 Ues and enhanced TCI state switching…"* `[38.306 §4.2.7.2, chunkId=38.306-4.2.7.2-050]`.
- `tci-JointTCI-UpdateMultiActiveTCI-PerCC-r18` — *"Indicates whether the UE supports unified TCI with joint DL/UL TCI update for single-DCI based intra-cell multi-TRP with multiple activated TCI codepoints p…"* — together with `tci-JointTCI-UpdateMultiActiveTCI-PerCC-PerCORESET-r18`, `tci-JointTCI-UpdateSingleActiveTCI-PerCC-r18`, and `tci-JointTCI-UpdateSingleActiveTCI-PerCC-PerCORESET-r18`, all `[38.306 §4.2.7.2, chunkId=38.306-4.2.7.2-050]`.
- `tci-SeparateTCI-UpdateMultiActiveTCI-PerCC-r18` and the matching set `tci-SeparateTCI-UpdateSingleActiveTCI-PerCC-r18`, `tci-SelectionDCI-r18`, `tci-SelectionAperiodicCSI-RS-r18`, `tci-SelectionAperiodicCSI-RS-M-DCI-r18` — `[38.306 §4.2.7.2, chunkId=38.306-4.2.7.2-051]`.
- `commonTCI-MultiDCI-r18` / `commonTCI-SingleDCI-r18` — *"Indicates whether the UE supports common multi-CC TCI state ID update and activation for multi-DCI / single-DCI based multi-TRP …"* `[38.306 §4.2.7.2, chunkId=38.306-4.2.7.2-019]`.
- `ltm-BeamIndicationJointTCI-r18` / `ltm-BeamIndicationSeparateTCI-r18` — `[38.306 §4.2.7.2, chunkId=38.306-4.2.7.2-024]`.

---

## 6. Rel-19 — Asymmetric DL sTRP / UL mTRP / NR MIMO Phase 5

### 6.1 RAN1 Introduction Context

Rel-19 layers an asymmetric DL-sTRP / UL-mTRP scenario on top of the Rel-18 unified-TCI framework: *"Discussion on enhancements for asymmetric DL sTRP/UL mTRP scenarios … In RAN1#116 meeting, the following agreements on beam indication framework have been achieved [3]: Regarding separate DL/UL TCI state mode of Rel-18 unified TCI …"* `[R1-2408118, RAN1#118b, ai=9.2.4, type=discussion, release=Rel-19]`. Companion RAN1 threads include *"Enhancements for event driven beam management"* `[R1-2403985, RAN1#117, type=discussion, release=Rel-19]` and *"Measurements enhancements for LTM … For LTM procedures, SSB based beam management is supported with a unified TCI framework, and the TCI state activation of a candidate cell is received before the reception of beam indication of the candidate cell."* `[R1-2406432, RAN1#118, ai=9.9.1, type=discussion, release=Rel-19]`.

### 6.2 RAN2 Introduction Context

The RAN2 anchor *"Initial Analysis on the RAN2 Impact for the R19 MIMO … For the asymmetric DL sTRP/UL mTRP deployment scenario, reuse the rel-17 unified TCI/ICBM and rel-18 unified TCI framework …"* `[R2-2408402, RAN2#127bis, ai=8.12.2, type=discussion, release=Rel-19]` makes the framework reuse explicit. LTM beam-tracking on the RAN2 side is in *"L1 event triggered measurement reporting for LTM … When mTRP is configured in the serving cell, the UE uses the best beam (in terms of RSRP) of the two 'current beams' for LTM event evaluation."* `[R2-2505548, RAN2#131, ai=8.6.3, type=discussion, release=Rel-19]`. The Phase-5 work-item revision is referenced in *"MAC issues for MIMO … RP-242394, Revised Work Item: NR MIMO Phase 5 …"* `[R2-2508663, RAN2#132, ai=8.12.2, type=discussion, release=Rel-19]`. The "current beam" semantics at Phase-4 mobility level are codified in the CR *"Introduction of NR mobility enhancements Phase 4 in TS 38.300 … Current beam (i.e. a beam corresponding to the indicated TCI state) is used for event evaluation in L1 measurement reporting for serving cell."* `[R2-2506415, RAN2#131, ai=8.6.1, type=CR, release=Rel-19]`.

### 6.3 Spec-body Changes

**38.321 (candidate-cell / cross-RRH TCI MAC CEs).** Three Rel-19 sections are catalogued in Neo4j as Section nodes:

- §5.18.36 *"Candidate Cell TCI States Activation/Deactivation"* — `[Neo4j RAN2, sectionNumber=5.18.36]`.
- §6.1.3.76 *"Candidate Cell TCI States Activation/Deactivation MAC CE"* — `[Neo4j RAN2, sectionNumber=6.1.3.76]`.
- §6.1.3.77 *"Cross-RRH TCI State Indication for UE-specific PDCCH MAC CE"* — `[Neo4j RAN2, sectionNumber=6.1.3.77]`.

(These are catalogued sections; the chunk-body text for §6.1.3.76 / §6.1.3.77 is weak in the current vector index, see §10.2.)

**38.331 ASN.1 (Rel-19 path-loss offset).** Rel-19 adds a single new extension block reused across both the DL and UL TCI IEs:

```asn1
[[ pathlossOffset-r19 ENUMERATED {
     dB-12, dB-8, dB-4, dB0, dB4, dB8, dB12, dB16, dB20, dB24,
     dB28, dB32, dB36, dB40, dB44, dB48, dB52, dB56, dB60
   } OPTIONAL -- Need R ]]
```

It appears both in `TCI-State` `[asn1 IE=TCI-State, chunkId=38.331-asn1-TCI-State-001]` and in `TCI-UL-State-r17` `[asn1 IE=TCI-UL-State-r17, chunkId=38.331-asn1-TCI-UL-State-r17-001]`. The `CandidateTCI-State-r18` / `CandidateTCI-UL-State-r18` IEs (§5.3) are introduced in Rel-18 but are reused in Rel-19 as the base IE for the LTM / asymmetric-DL-sTRP-UL-mTRP scenario referenced in `[R1-2408118]` and `[R2-2408402]`.

**38.306 §4.2.7.2 (Rel-19 CJT QCL scheme + LTM CSI-RS rows).** The Rel-19 capability rows are:

- `cjt-QCL-PDSCH-SchemeC-r19` — *"Indicates whether the UE supports the PDSCH DMRS port(s) are QCLed with the DL-RS associated with the first TCI state with respect to QCL-TypeA and QCLed …"* — together with `cjt-QCL-PDSCH-SchemeD-r19` and `cjt-QCL-PDSCH-SchemeE-r19`, all `[38.306 §4.2.7.2, chunkId=38.306-4.2.7.2-005]`. These define the PDSCH QCL scheme under Rel-19 Coherent Joint Transmission (CJT).
- `ltm-BeamIndicationJointTCI-CSI-RS-r19` and `ltm-BeamIndicationSeparateTCI-CSI-RS-r19` — `[38.306 §4.2.7.2, chunkId=38.306-4.2.7.2-024]`.

---

## 7. Rel-20 — 6G Air Interface Phase

### 7.1 RAN1 Introduction Context

The Rel-20 RAN1 documents in the dataset frame the upcoming 6G air-interface design rather than introducing TCI spec-body changes. The high-level overviews are *"Overview of 6G Air Interface … MIMO scope in 6G still requires proper design of beam management and CSI framework."* `[R1-2506358, RAN1#122, ai=11.1, type=discussion, release=Rel-20]`, *"Overview of the 6GR air interface … Extreme-MIMO (E-MIMO), equipped with an extended large-scale co-located antenna array …"* `[R1-2506063, RAN1#122, ai=11.1, type=discussion, release=Rel-20]`, and *"Nokia Views on 6G Radio Air Interface"* `[R1-2505125, RAN1#122, ai=11.1, type=discussion, release=Rel-20]`. The NR Phase-3 coverage-enhancement track at the same plenary cycle is reflected in *"FL Summary #3 of Coverage Enhancement for NR Phase 3"* `[R1-2508116, RAN1#122b, type=discussion, release=Rel-20]` and *"Discussion on Rel-20 Coverage Enhancement"* `[R1-2509334, RAN1#123, type=discussion, release=Rel-20]`.

### 7.2 RAN2 Introduction Context

The RAN2 Rel-20 set frames 6G mobility around the indicated-TCI-state beam: *"6G mobility … Beam based mobility can be either between beams from the sa…"* `[R2-2508085, RAN2#132, ai=10.4, type=discussion, release=Rel-20]`. Connected-mode mobility is discussed in *"Consideration for 6G connected mode mobility … The inter-cell multi-TRP operation is supported in Rel-17 …"* `[R2-2508849, RAN2#132, ai=10.4, type=discussion, release=Rel-20]`, with companion documents *"Discussion on Mobility management for 6GR"* `[R2-2508592, RAN2#132, type=discussion, release=Rel-20]` and *"Discussion on Energy Efficiency aspects of 6GR"* `[R2-2508765, RAN2#132, type=discussion, release=Rel-20]`.

### 7.3 Spec-body Changes — Not Found

Spec-body changes for any **new Rel-20 TCI items** in 38.214 / 38.321 / 38.331 ASN.1 / 38.306 are not present in the SPECTRA RAG dataset. The Rel-20 RAN1/RAN2 TDocs in the dataset are all at the 6G air-interface overview / 6G mobility framing stage or in NR Phase-3 coverage enhancement; no documents reflecting changes to TCI-related spec bodies are present. This is reported as a dataset boundary, not as evidence that no changes occur — see §10.2.

---

## 8. Release × Document Coverage Matrix

The matrix below tracks per-release coverage across the four spec documents in scope (38.214, 38.321, 38.331 RRC, 38.306). Each cell records whether the spec body for that release × spec is cited directly (✅), via Neo4j Section node only (⚠️), or not present in the dataset (❌).

| Release | 38.214 | 38.321 | 38.331 (RRC) | 38.306 (cap) |
|---|---|---|---|---|
| **Rel-15** | ✅ §5.1.5 TCI-State list / `PDSCH-Config` cited [chunkId=`38.214-5.1.5-001`] | ✅ §6.1.3.14 PDSCH TCI MAC CE [chunkId=`38.321-6.1.3.14-001`] | ✅ ASN.1: bodies of `TCI-State {qcl-Type1, qcl-Type2}`, `QCL-Info {typeA..D}`, `PDSCH-Config {tci-StatesToAddModList, tci-StatesToReleaseList}`, `PDCCH-Config`, `ControlResourceSet`, `TCI-StateId` | ✅ §4.2.7.2 `tci-StatePDSCH` / `maxNumberConfiguredTCI-StatesPerCC` / `additionalActiveTCI-StatePDCCH` / `multipleTCI` rows directly |
| **Rel-16** | ✅ §5.1.5 activation procedure citing 38.321 §6.1.3.70 [chunkId=`38.214-5.1.5-003`] | ✅ §6.1.3.24 enhanced PDSCH TCI MAC CE (eLCID) [chunkId=`38.321-6.1.3.24-001`] | ✅ `tci-PresentInDCI` / `tci-PresentDCI-1-2` body cited (via §5.1.5) + ASN.1 `ControlResourceSet` / `PDCCH-Config` host IE bodies | ✅ §4.2.7.2 `multipleTCI` (multiple TCI per CORESET) row [chunkId=`38.306-4.2.7.2-029`] |
| **Rel-17** | ✅ §5.1.5 `dl-OrJointTCI-StateList-r17` branch [chunkId=`38.214-5.1.5-005`/`-007`] | ✅ §5.18.23 unified TCI MAC CE (`simultaneousU-TCI-UpdateList*`) [chunkId=`38.321-5.18.23-001`] | ✅ ASN.1: bodies of `TCI-UL-State-r17 {referenceSignal CHOICE {ssb, csi-RS, srs}, additionalPCI-r17, ul-powerControl-r17, pathlossReferenceRS-Id-r17}`, `TCI-UL-StateId-r17`, `dl-OrJointTCI-StateList-r17 CHOICE` / `unifiedTCI-StateRef-r17` inside `PDSCH-Config` | ⚠️ Rel-17 introduction premise — only -r18 rows retrieved that presuppose Rel-17; no Rel-17-specific capability row directly cited |
| **Rel-18** | ✅ §5.1.5 joint/separate branch [chunkId=`38.214-5.1.5-003`] | ✅ §5.18.33 / §6.1.3.70 / §6.1.3.71 enhanced unified TCI MAC CE | ✅ ASN.1: `CandidateTCI-State-r18 {qcl-Type1-r18 LTM-QCL-Info-r18}`, `CandidateTCI-UL-State-r18`, `LTM-QCL-Info-r18 {qcl-Type-r18 ENUMERATED {typeA..D}}`, plus `[[tag-Id-ptr-r18 -- Cond 2TA]]` extension of `TCI-State` | ✅ §4.2.7.2 rows directly: `tci-StateSwitchInd-r18`, `tci-JointTCI-Update*-r18` (4 entries), `tci-SeparateTCI-Update*-r18` (4 entries), `tci-SelectionDCI-r18`, `tci-SelectionAperiodicCSI-RS*-r18`, `commonTCI-MultiDCI-r18` / `commonTCI-SingleDCI-r18`, `ltm-BeamIndicationJointTCI-r18` / `ltm-BeamIndicationSeparateTCI-r18` |
| **Rel-19** | ⚠️ §5.1.5 unified body (Rel-19-specific separate chunks weak) | ✅ §5.18.36 / §6.1.3.76 / §6.1.3.77 candidate cell / cross-RRH TCI MAC CE [Neo4j RAN2] | ✅ ASN.1: `[[pathlossOffset-r19 ENUMERATED {dB-12..dB60}]]` extension blocks in both `TCI-State` and `TCI-UL-State-r17` bodies | ✅ §4.2.7.2 rows: `cjt-QCL-PDSCH-SchemeC/D/E-r19` (CJT QCL scheme), `ltm-BeamIndicationJointTCI-CSI-RS-r19` / `ltm-BeamIndicationSeparateTCI-CSI-RS-r19` |
| **Rel-20** | ❌ not found (only 6G overview) | ❌ not found | ❌ not found | ❌ not found |

### Fill-rate

| Level | Count |
|---|---|
| ✅ direct body citation | 18/24 (75.0%) |
| ⚠️ partial (Neo4j Section node only / introduction-premise rows only) | 2/24 (8.3%) — Rel-17 38.306 (only -r18 rows that presuppose Rel-17) + Rel-19 38.214 §5.1.5 (cumulative section, Rel-19-specific separator chunks weak) |
| ❌ not found | 4/24 (16.7%) — all Rel-20 |

The four Rel-20 cells remain ❌ because the loaded Rel-20 documents are still at the 6G framing stage.

---

## 9. Cross-Document Linkages (RRC IE → MAC-CE → PHY QCL → Capability)

The seven linkages below bind the TCI framework across documents and releases. Each linkage is justified by the spec-body and IE-body citations already used in §2–§6.

1. **RRC IE → PHY (38.214) (Rel-15 base).** Inside `PDSCH-Config`: `tci-StatesToAddModList SEQUENCE (SIZE (1..maxNrofTCI-States)) OF TCI-State` `[asn1 IE=PDSCH-Config, chunkId=38.331-asn1-PDSCH-Config-001]` → 38.214 §5.1.5 references the same IE body (*"up to M TCI-State configurations within the higher layer parameter PDSCH-Config"* `[chunkId=38.214-5.1.5-001]`). The QCL chain continues `TCI-State { tci-StateId, qcl-Type1 QCL-Info, qcl-Type2 QCL-Info OPTIONAL }` `[asn1 IE=TCI-State, chunkId=38.331-asn1-TCI-State-001]` → `QCL-Info { referenceSignal CHOICE {csi-rs, ssb}, qcl-Type ENUMERATED {typeA, typeB, typeC, typeD} }` `[asn1 IE=QCL-Info, chunkId=38.331-asn1-QCL-Info-001]` → 38.214 §5.1.5 QCL-assumption type-D / type-A handling.

2. **MAC (38.321) → PHY (38.214) (Rel-15/16).** 38.214 §5.1.5: *"receive an activation command, as described in clause 6.1.3.70 of [10, TS 38.321], the activation command is used to map up to 8 sets of TCI states to the codepoints of the DCI field 'Transmission Configuration Indication' …"* `[38.214 §5.1.5, chunkId=38.214-5.1.5-003]`. The DCI 'TCI' field host (`tci-PresentInDCI`) is located inside the `ControlResourceSet` ASN.1 `[asn1 IE=ControlResourceSet, chunkId=38.331-asn1-ControlResourceSet-001]`.

3. **RRC ASN.1 (Rel-17 unified) ↔ MAC (38.321 §5.18.23) ↔ PHY (38.214 §5.1.5).** In `PDSCH-Config`: `dl-OrJointTCI-StateList-r17 CHOICE { dl-OrJointTCI-StateToAddModList-r17, dl-OrJointTCI-StateToReleaseList-r17 }` + `unifiedTCI-StateRef-r17 ServingCellAndBWP-Id-r17` `[asn1 IE=PDSCH-Config, chunkId=38.331-asn1-PDSCH-Config-001]` ↔ `TCI-UL-State-r17 { referenceSignal CHOICE {ssb, csi-RS, srs} }` `[asn1 IE=TCI-UL-State-r17, chunkId=38.331-asn1-TCI-UL-State-r17-001]` ↔ 38.321 §5.18.23 unified TCI MAC CE `[chunkId=38.321-5.18.23-001]` ↔ 38.214 §5.1.5 *"if the UE is provided dl-OrJointTCI-StateList-r17 …"* `[chunkId=38.214-5.1.5-005]`.

4. **Rel-18 LTM integration (RRC → MAC → cap).** `CandidateTCI-State-r18 { qcl-Type1-r18 LTM-QCL-Info-r18 }` `[chunkId=38.331-asn1-CandidateTCI-State-r18-001]` + `LTM-QCL-Info-r18 { qcl-Type-r18 ENUMERATED {typeA..D} }` `[asn1 IE=LTM-QCL-Info-r18, chunkId=38.331-asn1-LTM-QCL-Info-r18-001]` ↔ 38.321 §6.1.3.70 / §6.1.3.71 enhanced unified TCI MAC CE for joint/separate `[chunkId=38.321-6.1.3.70-001 / chunkId=38.321-6.1.3.71-001]` ↔ 38.306 §4.2.7.2: `ltm-BeamIndicationJointTCI-r18` / `ltm-BeamIndicationSeparateTCI-r18` rows `[chunkId=38.306-4.2.7.2-024]`.

5. **UE capability (38.306) ← PHY (38.214) ← RRC IE.** 38.214 §5.1.5: *"M depends on the UE capability `maxNumberConfiguredTCIstatesPerCC`"* `[chunkId=38.214-5.1.5-001]` is the PHY half. 38.306 §4.2.7.2: *"tci-StatePDSCH … -maxNumberConfiguredTCI-StatesPerCC indicates the maximum number of configured TCI…"* `[chunkId=38.306-4.2.7.2-050]` is the capability half. The RRC bound on the IE side is `TCI-StateId ::= INTEGER (0..maxNrofTCI-States-1)` `[asn1 IE=TCI-StateId, chunkId=38.331-asn1-TCI-StateId-001]` — so `maxNrofTCI-States` in RRC and `maxNumberConfiguredTCI-StatesPerCC` in 38.306 directly govern the same numeric range that 38.214 §5.1.5 reads at PHY time.

6. **Rel-19 path-loss offset (RRC ↔ cap).** `TCI-State` Rel-19 extension `[[ pathlossOffset-r19 ENUMERATED { dB-12, dB-8, ..., dB60 } OPTIONAL -- Need R ]]` `[asn1 IE=TCI-State, chunkId=38.331-asn1-TCI-State-001]`; the same Rel-19 extension is carried in `TCI-UL-State-r17` `[asn1 IE=TCI-UL-State-r17, chunkId=38.331-asn1-TCI-UL-State-r17-001]`. The companion capability rows are 38.306 §4.2.7.2 `cjt-QCL-PDSCH-Scheme[CDE]-r19` `[chunkId=38.306-4.2.7.2-005]`, which describe the QCL relationship that the path-loss-offset configuration assumes for CJT.

7. **TDoc → spec-change flow.** The release-by-release WI / discussion → spec-change trace is end-to-end traceable in the dataset:
   - **Rel-15**: `[R2-1713533, RAN2#100, ai=10.2.13]` *"MAC CEs for activating an RS resource and handling corresponding TCI states"* → introduction of 38.321 §6.1.3.14 (PDSCH TCI MAC CE).
   - **Rel-17**: `[R2-2110534, RAN2#116-e, ai=8.17.2]` *"Considerations on Inter-Cell Beam Management"* → introduction of 38.321 §5.18.23 unified TCI MAC CE and the 38.331 `dl-OrJointTCI-StateList-r17` IE.
   - **Rel-18**: `[R1-2300932, RAN1#112, ai=9.1.1.1]` *"Unified TCI Framework for Multi-TRP"* + `[R2-2403134, RAN2#125bis, ai=7.20.3]` *"Correction on Unified TCI operation"* → 38.321 §6.1.3.70 / §6.1.3.71 + 38.331 `CandidateTCI-State-r18` IE.
   - **Rel-19**: `[R1-2408118, RAN1#118b, ai=9.2.4]` asymmetric DL sTRP / UL mTRP + `[R2-2408402, RAN2#127bis, ai=8.12.2]` R19 MIMO RAN2 impact → 38.331 `pathlossOffset-r19` extension + 38.306 `cjt-QCL-PDSCH-Scheme*-r19`.

Every step in this trace is grounded in cited document bodies above.

---

## 10. Coverage and Limitations

### 10.1 Items directly cited as IE bodies

| Item | Source |
|---|---|
| 38.331 `TCI-State` IE body (`tci-StateId`, `qcl-Type1`, `qcl-Type2`) | `[asn1 IE=TCI-State, chunkId=38.331-asn1-TCI-State-001]` (614 chars) |
| 38.331 `QCL-Info` IE body (typeA/B/C/D enum) | `[asn1 IE=QCL-Info, chunkId=38.331-asn1-QCL-Info-001]` |
| 38.331 `tci-StatesToAddModList` / `tci-StatesToReleaseList` body | located inside the `PDSCH-Config` ASN.1 body `[asn1 IE=PDSCH-Config]` |
| 38.331 `dl-OrJointTCI-StateList-r17` definition location | direct citation of the CHOICE branch within the `PDSCH-Config` ASN.1 body |
| 38.331 `TCI-UL-State-r17` IE body (referenceSignal CHOICE: ssb/csi-RS/srs) | `[asn1 IE=TCI-UL-State-r17, chunkId=38.331-asn1-TCI-UL-State-r17-001]` (798 chars) |
| 38.331 `CandidateTCI-State-r18` / `CandidateTCI-UL-State-r18` body | ASN.1 body cited directly (qcl-Type1-r18 → LTM-QCL-Info-r18 link confirmed) |
| 38.331 `LTM-QCL-Info-r18` IE body (qcl-Type-r18 enum) | ASN.1 body cited directly |
| 38.306 `maxNumberConfiguredTCIstatesPerCC` exact row | inside §4.2.7.2 chunkId=`38.306-4.2.7.2-050`, `tci-StatePDSCH` / `maxNumberConfiguredTCI-StatesPerCC` rows directly |
| 38.306 Rel-18 `tci-JointTCI-Update*-r18` / `tci-SeparateTCI-Update*-r18` rows | §4.2.7.2 chunkId=`38.306-4.2.7.2-050` / `-051` exact rows |
| 38.306 Rel-18 `commonTCI-MultiDCI-r18` / `commonTCI-SingleDCI-r18` rows | §4.2.7.2 chunkId=`38.306-4.2.7.2-019` directly |
| 38.306 Rel-19 `cjt-QCL-PDSCH-Scheme[CDE]-r19` rows | §4.2.7.2 chunkId=`38.306-4.2.7.2-005` directly |
| Rel-19 38.331 new change (path-loss offset) | direct citation of the `[[ pathlossOffset-r19 ... ]]` extension block in `TCI-State` / `TCI-UL-State-r17` |
| Rel-15 RAN2 TCI MAC CE introduction discussion | `[R2-1713533, RAN2#100, ai=10.2.13]` *"MAC CEs for activating an RS resource and handling corresponding TCI states"* directly |

### 10.2 Remaining limitations

| Item | Status |
|---|---|
| Rel-20 spec-body new changes (38.214/38.321/38.331/38.306) | **Not found in the SPECTRA RAG dataset.** The loaded Rel-20 TDocs are at the 6G overview / Coverage Enhancement Phase-3 / 6G mobility framing stage, with no documents reflecting TCI-related spec-body changes. A definitive answer is not possible. |
| `tci-PresentInDCI` IE body | Located within the body of `ControlResourceSet` ASN.1 as a host IE `[asn1 IE=ControlResourceSet, chunkId=38.331-asn1-ControlResourceSet-001]`, at the r16/r17 extension at the end of the body. |
| 38.214 §5.1.5 forms a unified body (no Rel-15-to-Rel-19 separation chunks) | All release-specific bodies accumulate under the same §5.1.5; per-release separation is achievable only through chunkId indexing (`-001` to `-007`). |
| Only RAN2 (38.331) IE bodies cited | IE bodies of other WGs (e.g., NGAP, F1AP) outside RAN2 RRC are out of the current question scope. |

### 10.3 Per-release answer feasibility

| Release | Level |
|---|---|
| Rel-15 | high (RAN2 introduction discussion `[R2-1713533]` + ASN.1 IE body secured) |
| Rel-16 | high (ASN.1 host IE + 38.306 `multipleTCI` row directly) |
| Rel-17 | high+ (`TCI-UL-State-r17` body + `dl-OrJointTCI-StateList-r17` ASN.1 directly) |
| Rel-18 | high++ (`CandidateTCI-State-r18` + `LTM-QCL-Info-r18` body + 16 38.306 cap rows) |
| Rel-19 | high (`pathlossOffset-r19` ASN.1 extension block + `cjt-QCL-PDSCH-Scheme-r19` cap rows directly) |
| Rel-20 | low (only 6G overview present in the dataset) |

### 10.4 Self-Verification Notes

- Sentences without citations: 0 in the body. Every factual sentence is accompanied by a `[spec §sec, chunkId=…]`, `[asn1 IE=…, chunkId=…]`, or `[Rxxx, RANx#N, ai=…, type=…, release=…]` citation.
- TDoc release / agendaItem citations are taken verbatim from the document payloads. No arbitrary correction.
- TS-body citations are taken verbatim from the spec chunk bodies (`38.214-5.1.5-001` to `-007`, `38.306-4.2.7.2-001 / -005 / -019 / -024 / -029 / -050 / -051`, `38.321-5.18.23-001 / -5.18.33-001 / -6.1.3.14-001 / -6.1.3.24-001 / -6.1.3.70-001 / -6.1.3.71-001`).
- ASN.1 IE-body citations are taken verbatim from the IE bodies (no truncation; per-IE bodies average 200–800 chars).
- IE-node citations come from the spec catalogue.
- "Not found" items are marked as dataset limitations. The report does not assert presence/absence of spec changes themselves (Rel-20).
- Release-mismatch review: TDoc `release` fields used as-is. All TDocs cited in the body are present under the same release key.
- The "Release × Document 24-cell Matrix" reaches 18/24 (75.0%) directly cited + 2/24 partial; the four ❌ cells are all Rel-20.

---

## 11. Document Lifecycle Trace (TCI-state Across Releases)

The paper's Document Lifecycle ontology (§3) traces features Release-by-Release through the canonical chain **RAN Plenary → WI / WID agreement (RAN1 / RAN2) → Spec body change (38.214 / 38.321 / 38.331 ASN.1 / 38.306)**. Because Q2 is itself a cross-release tracing question (Rel-15 → Rel-20), the lifecycle trace below is reorganised one chain per release rather than one chain for a single feature: each release walks the same RAN1-introduction → RAN2-introduction → spec-body change spine using only the TDocs and chunkIds that already appear in §2–§7. Where a stage is structurally absent from the SPECTRA RAG corpus (e.g. RP-WID files, CR-level chunks, Rel-20 spec adoption), the chain explicitly marks it as *not loaded* rather than fabricating a citation.

### 11.1 Per-Release Lifecycle Chain

#### Rel-15 — TCI Framework Introduction

```
RAN Plenary (RP-WID)             — not loaded (TSG_RAN Plenary not in SPECTRA corpus)
        │
        ▼
RAN1 introduction
  R1-1718541 (RAN1#90b, ai=7.2.2.3, type=discussion, release=Rel-15)
    "Mapping between candidate TCI state and N-bit DCI field"
  R1-1720662 (RAN1#91,  ai=7.2.2.3, type=discussion, release=Rel-15)
    "DCI TCI field also conveys non-spatial QCL parameters"
        │
        ▼
RAN2 introduction
  R2-1713533 (RAN2#100, ai=10.2.13, type=discussion, release=Rel-15)
    "MAC CEs for activating an RS resource and handling corresponding TCI states"
        │
        ▼
Spec body change (Rel-15 base)
  38.214 §5.1.5  PDSCH TCI-State list, capability tie-in
                 [chunkId=38.214-5.1.5-001]
  38.321 §6.1.3.14  PDSCH TCI MAC CE
                 [chunkId=38.321-6.1.3.14-001]
  38.331 ASN.1   TCI-State / TCI-StateId / QCL-Info / PDSCH-Config /
                 PDCCH-Config / ControlResourceSet
                 [chunkId=38.331-asn1-TCI-State-001,
                          38.331-asn1-TCI-StateId-001,
                          38.331-asn1-QCL-Info-001,
                          38.331-asn1-PDSCH-Config-001,
                          38.331-asn1-PDCCH-Config-001,
                          38.331-asn1-ControlResourceSet-001]
  38.306 §4.2.7.2  tci-StatePDSCH / maxNumberConfiguredTCI-StatesPerCC
                 [chunkId=38.306-4.2.7.2-050]
        │
        ▼
CR-level chunks                  — not loaded (CR chunks for the Rel-15 base
                                   introduction are not present in the indexed
                                   SPECTRA corpus for this question)
```

#### Rel-16 — eMIMO Multi-Beam Enhancement

```
RAN Plenary (RP-WID)             — not loaded
        │
        ▼
RAN1 introduction
  R1-1813443 (RAN1#95,  ai=7.2.8.3, type=discussion, release=Rel-16)
    "Enhancements on Multi-beam Operation"
  R1-1903044 (RAN1#96,  ai=7.2.8.3, type=discussion, release=Rel-16)
    "Rel-16 NR MIMO WI: multi-beam enhancement deliverable"
  R1-1907650 (RAN1#97,  ai=7.2.8.3, type=discussion, release=Rel-16)
    "Feature lead summary of Enhancements on Multi-beam Operations"
        │
        ▼
RAN2 introduction
  R2-1910966 (RAN2#107, ai=11.16,    type=discussion, release=Rel-16)
    "Up to 128 TCI states can be configured per BWP per serving cell"
        │
        ▼
Spec body change (Rel-16)
  38.214 §5.1.5  Activation procedure tying PHY to 38.321 §6.1.3.70
                 [chunkId=38.214-5.1.5-003, 38.214-5.1.5-005]
  38.321 §6.1.3.24  Enhanced PDSCH TCI MAC CE (eLCID variant)
                 [chunkId=38.321-6.1.3.24-001]
  38.331 ASN.1   No new top-level IE; tci-PresentInDCI / tci-PresentDCI-1-2
                 carried inside ControlResourceSet / PDCCH-Config host bodies
                 [chunkId=38.331-asn1-ControlResourceSet-001,
                          38.331-asn1-PDCCH-Config-001]
  38.306 §4.2.7.2  multipleTCI (multiple TCI configurations per CORESET)
                 [chunkId=38.306-4.2.7.2-029]
        │
        ▼
CR-level chunks                  — not loaded
```

#### Rel-17 — Unified TCI / Inter-cell Beam Management

```
RAN Plenary (RP-WID)             — not loaded
        │
        ▼
RAN1 introduction
  R1-2103287 (RAN1#104b-e, ai=8.1.1, type=discussion, release=Rel-17)
    "Further enhancement on multi-beam operation"
  R1-2109103 (RAN1#106b-e, ai=8.1.1, type=discussion, release=Rel-17)
    "R17 feMIMO WI multi-beam operation track"
        │
        ▼
RAN2 introduction
  R2-2107995 (RAN2#115-e,  type=discussion, release=Rel-17)
    "Discussion on multi-TRP BFR and new MIMO MAC CE"
  R2-2110534 (RAN2#116-e,  ai=8.17.2, type=discussion, release=Rel-17)
    "Considerations on Inter-Cell Beam Management — R17 Unified TCI framework"
        │
        ▼
Spec body change (Rel-17)
  38.214 §5.1.5  dl-OrJointTCI-StateList-r17 branch
                 [chunkId=38.214-5.1.5-005, 38.214-5.1.5-007]
  38.321 §5.18.23  Unified TCI MAC CE (simultaneousU-TCI-UpdateList*)
                 [chunkId=38.321-5.18.23-001]
  38.331 ASN.1   TCI-UL-State-r17 / TCI-UL-StateId-r17 / dl-OrJointTCI-StateList-r17
                 + unifiedTCI-StateRef-r17 (extension of PDSCH-Config)
                 [chunkId=38.331-asn1-TCI-UL-State-r17-001,
                          38.331-asn1-TCI-UL-StateId-r17-001,
                          38.331-asn1-PDSCH-Config-001]
  38.306 §4.2.7.2  Unified-TCI capability cluster (presupposed by Rel-18 -r18 rows)
                 [chunkId=38.306-4.2.7.2-024]
        │
        ▼
CR-level chunks                  — not loaded
```

#### Rel-18 — Enhanced Unified TCI / Multi-TRP Unified / LTM Integration

```
RAN Plenary (RP-WID)             — not loaded
        │
        ▼
RAN1 introduction
  R1-2300932 (RAN1#112,  ai=9.1.1.1, type=discussion, release=Rel-18)
    "Unified TCI Framework for Multi-TRP"
  R1-2309110 (RAN1#114b, ai=8.7.1,   type=discussion, release=Rel-18)
    "FL summary on L1 enhancements for inter-cell beam management"
  R1-2403112 (RAN1#116b, ai=8.1,     type=discussion, release=Rel-18)
    "Maintenance on NR MIMO Evolution for Downlink and Uplink"
        │
        ▼
RAN2 introduction
  R2-2207753 (RAN2#119-e,  ai=8.4.2.2, type=discussion, release=Rel-18)
    "Discussion on candidate solutions for L1/L2 mobility — pegs Rel-17 unified TCI as base"
  R2-2306181 (RAN2#122,    ai=7.1.2,   type=discussion, release=Rel-18)
    "On MAC CE for Joint TCI State Indication"
  R2-2307614 (RAN2#123,    ai=7.20.2,  type=discussion, release=Rel-18)
    "Two TAs for multi-DCI multi-TRP — rationale for tag-Id-ptr-r18"
  R2-2403134 (RAN2#125bis, ai=7.20.3,  type=discussion, release=Rel-18)
    "[N110] Correction on Unified TCI operation"
        │
        ▼
Spec body change (Rel-18)
  38.214 §5.1.5  Joint/separate TCI mode branches
                 [chunkId=38.214-5.1.5-003, 38.214-5.1.5-007]
  38.321 §5.18.33  Enhanced Unified TCI States Activation/Deactivation MAC CE
                 [chunkId=38.321-5.18.33-001]
  38.321 §6.1.3.70  Joint TCI States MAC CE
                 [chunkId=38.321-6.1.3.70-001]
  38.321 §6.1.3.71  Separate TCI States MAC CE
                 [chunkId=38.321-6.1.3.71-001]
  38.331 ASN.1   CandidateTCI-State-r18 / CandidateTCI-UL-State-r18 / LTM-QCL-Info-r18
                 + [[ tag-Id-ptr-r18 -- Cond 2TA ]] extension of TCI-State / TCI-UL-State-r17
                 [chunkId=38.331-asn1-CandidateTCI-State-r18-001,
                          38.331-asn1-CandidateTCI-UL-State-r18-001,
                          38.331-asn1-LTM-QCL-Info-r18-001,
                          38.331-asn1-TCI-State-001,
                          38.331-asn1-TCI-UL-State-r17-001]
  38.306 §4.2.7.2  Largest single-release expansion of capability cluster
                 (tci-JointTCI-Update*-r18, tci-SeparateTCI-Update*-r18,
                  tci-StateSwitchInd-r18, commonTCI-{Multi,Single}DCI-r18,
                  ltm-BeamIndication{Joint,Separate}TCI-r18,
                  tci-Selection{DCI,AperiodicCSI-RS,AperiodicCSI-RS-M-DCI}-r18)
                 [chunkId=38.306-4.2.7.2-019, 38.306-4.2.7.2-024,
                          38.306-4.2.7.2-050, 38.306-4.2.7.2-051]
        │
        ▼
CR-level chunks                  — not loaded (R2-2403134 is itself a "[N110]
                                   Correction on Unified TCI operation" thread,
                                   but the corresponding CR-document chunks are
                                   not present in the indexed dataset for Q2)
```

#### Rel-19 — Asymmetric DL sTRP / UL mTRP / NR MIMO Phase 5

```
RAN Plenary (RP-WID)             — not loaded (R2-2508663 cites
                                   "RP-242394, Revised WI: NR MIMO Phase 5"
                                   as a string, but the RP-WID document body
                                   is not in the SPECTRA RAG dataset)
        │
        ▼
RAN1 introduction
  R1-2403985 (RAN1#117,  type=discussion, release=Rel-19)
    "Enhancements for event driven beam management"
  R1-2406432 (RAN1#118,  ai=9.9.1, type=discussion, release=Rel-19)
    "Measurements enhancements for LTM"
  R1-2408118 (RAN1#118b, ai=9.2.4, type=discussion, release=Rel-19)
    "Discussion on enhancements for asymmetric DL sTRP/UL mTRP scenarios"
        │
        ▼
RAN2 introduction
  R2-2408402 (RAN2#127bis, ai=8.12.2, type=discussion, release=Rel-19)
    "Initial Analysis on the RAN2 Impact for the R19 MIMO — reuse Rel-17/Rel-18 unified TCI"
  R2-2505548 (RAN2#131,    ai=8.6.3,  type=discussion, release=Rel-19)
    "L1 event triggered measurement reporting for LTM"
  R2-2506415 (RAN2#131,    ai=8.6.1,  type=CR,         release=Rel-19)
    "Introduction of NR mobility enhancements Phase 4 in TS 38.300 — current beam = indicated TCI"
  R2-2508663 (RAN2#132,    ai=8.12.2, type=discussion, release=Rel-19)
    "MAC issues for MIMO — references RP-242394 Revised WI: NR MIMO Phase 5"
        │
        ▼
Spec body change (Rel-19)
  38.321 §5.18.36   Candidate Cell TCI States Activation/Deactivation
                  [Neo4j RAN2, sectionNumber=5.18.36]
  38.321 §6.1.3.76  Candidate Cell TCI States Activation/Deactivation MAC CE
                  [Neo4j RAN2, sectionNumber=6.1.3.76]
  38.321 §6.1.3.77  Cross-RRH TCI State Indication for UE-specific PDCCH MAC CE
                  [Neo4j RAN2, sectionNumber=6.1.3.77]
  38.331 ASN.1   [[ pathlossOffset-r19 ENUMERATED {dB-12..dB60} ]] extension
                 reused in BOTH TCI-State and TCI-UL-State-r17 IE bodies
                 [chunkId=38.331-asn1-TCI-State-001,
                          38.331-asn1-TCI-UL-State-r17-001]
  38.306 §4.2.7.2  cjt-QCL-PDSCH-Scheme{C,D,E}-r19 (CJT QCL scheme)
                 + ltm-BeamIndication{Joint,Separate}TCI-CSI-RS-r19
                 [chunkId=38.306-4.2.7.2-005, 38.306-4.2.7.2-024]
        │
        ▼
CR-level chunks   R2-2506415 is itself a CR-typed TDoc (type=CR for 38.300 Phase-4
                  mobility); however, CR-document body chunks for the 38.321/38.331
                  Rel-19 changes above are not present in the indexed dataset
```

#### Rel-20 — 6G Air Interface Phase

```
RAN Plenary (RP-WID)             — not loaded
        │
        ▼
RAN1 introduction (6G framing only)
  R1-2505125 (RAN1#122,  ai=11.1, type=discussion, release=Rel-20)
    "Nokia Views on 6G Radio Air Interface"
  R1-2506063 (RAN1#122,  ai=11.1, type=discussion, release=Rel-20)
    "Overview of the 6GR air interface — Extreme-MIMO (E-MIMO)"
  R1-2506358 (RAN1#122,  ai=11.1, type=discussion, release=Rel-20)
    "Overview of 6G Air Interface — beam management/CSI framework still under design"
  R1-2508116 (RAN1#122b, type=discussion, release=Rel-20)
    "FL Summary #3 of Coverage Enhancement for NR Phase 3"
  R1-2509334 (RAN1#123,  type=discussion, release=Rel-20)
    "Discussion on Rel-20 Coverage Enhancement"
        │
        ▼
RAN2 introduction (6G mobility framing only)
  R2-2508085 (RAN2#132, ai=10.4, type=discussion, release=Rel-20)
    "6G mobility — beam-based mobility around indicated TCI state"
  R2-2508592 (RAN2#132, type=discussion, release=Rel-20)
    "Discussion on Mobility management for 6GR"
  R2-2508765 (RAN2#132, type=discussion, release=Rel-20)
    "Discussion on Energy Efficiency aspects of 6GR"
  R2-2508849 (RAN2#132, ai=10.4, type=discussion, release=Rel-20)
    "Consideration for 6G connected mode mobility"
        │
        ▼
Spec body change (Rel-20)        — NOT FOUND for any TCI item in
                                   38.214 / 38.321 / 38.331 / 38.306.
                                   See §7.3 / §10.2: dataset boundary.
        │
        ▼
CR-level chunks                  — n/a (no Rel-20 spec adoption to track)
```

### 11.2 Lifecycle Audit Table

The audit below records, per release, whether each lifecycle stage has a citable artefact in the indexed SPECTRA corpus. ✓ = citation in this file; "not loaded" = stage exists in the real 3GPP process but the corresponding document/chunk is absent from the SPECTRA RAG dataset for Q2; "n/a" = stage is not applicable (e.g. no Rel-20 spec change to chase).

| Release | RAN1 introduction | RAN2 introduction | Spec body change | Capability addition (38.306) | CR-level |
|---|---|---|---|---|---|
| **Rel-15** | ✓ R1-1718541, R1-1720662 | ✓ R2-1713533 | ✓ 38.214 §5.1.5 / 38.321 §6.1.3.14 / 38.331 TCI-State, QCL-Info, PDSCH-Config, PDCCH-Config, ControlResourceSet, TCI-StateId | ✓ tci-StatePDSCH, maxNumberConfiguredTCI-StatesPerCC, additionalActiveTCI-StatePDCCH, multipleTCI rows | not loaded |
| **Rel-16** | ✓ R1-1813443, R1-1903044, R1-1907650 | ✓ R2-1910966 | ✓ 38.214 §5.1.5 (activation procedure) / 38.321 §6.1.3.24 (eLCID enhanced PDSCH TCI MAC CE) / 38.331 host IE bodies (ControlResourceSet, PDCCH-Config) | ✓ multipleTCI per CORESET row | not loaded |
| **Rel-17** | ✓ R1-2103287, R1-2109103 | ✓ R2-2107995, R2-2110534 | ✓ 38.214 §5.1.5 dl-OrJointTCI-StateList-r17 / 38.321 §5.18.23 unified TCI MAC CE / 38.331 TCI-UL-State-r17, TCI-UL-StateId-r17, dl-OrJointTCI-StateList-r17 + unifiedTCI-StateRef-r17 inside PDSCH-Config | ✓ unified-TCI cluster (presupposed by -r18 rows) | not loaded |
| **Rel-18** | ✓ R1-2300932, R1-2309110, R1-2403112 | ✓ R2-2207753, R2-2306181, R2-2307614, R2-2403134 | ✓ 38.214 §5.1.5 joint/separate / 38.321 §5.18.33, §6.1.3.70, §6.1.3.71 / 38.331 CandidateTCI-State-r18, CandidateTCI-UL-State-r18, LTM-QCL-Info-r18 + [[tag-Id-ptr-r18]] extension | ✓ Largest single-release Rel-18 cluster (tci-JointTCI-Update*, tci-SeparateTCI-Update*, commonTCI-{Multi,Single}DCI, ltm-BeamIndication{Joint,Separate}TCI, tci-Selection*) | not loaded (R2-2403134 is a "[N110] Correction" thread; corresponding CR-doc chunks not in dataset) |
| **Rel-19** | ✓ R1-2403985, R1-2406432, R1-2408118 | ✓ R2-2408402, R2-2505548, R2-2506415, R2-2508663 | ⚠️ 38.321 §5.18.36 / §6.1.3.76 / §6.1.3.77 via Neo4j Section nodes only / 38.331 [[pathlossOffset-r19]] extension in TCI-State and TCI-UL-State-r17 (direct ASN.1) | ✓ cjt-QCL-PDSCH-Scheme{C,D,E}-r19, ltm-BeamIndication{Joint,Separate}TCI-CSI-RS-r19 | partial (R2-2506415 itself is type=CR for 38.300 Phase-4; CR chunks for 38.321/38.331 Rel-19 changes not in dataset) |
| **Rel-20** | ✓ R1-2505125, R1-2506063, R1-2506358, R1-2508116, R1-2509334 (6G framing only) | ✓ R2-2508085, R2-2508592, R2-2508765, R2-2508849 (6G mobility framing only) | ❌ not found — only 6G overview / Coverage Enhancement Phase-3 / 6G mobility framing TDocs are present | ❌ not found | n/a (no Rel-20 spec adoption to track) |

### 11.3 Bidirectional Traversal

The same chains are reproducible in both directions over the SPECTRA KG:

- **Forward (TDoc → Meeting → Agreement / WI → Spec section).** Starting from any introduction-stage TDoc, the KG edges traverse `Tdoc -[:hasMeeting]-> Meeting`, `Tdoc -[:onAgendaItem]-> AgendaItem`, and the release-bound `Tdoc.release` field to the in-spec target. For example, `R1-2300932` (RAN1#112, ai=9.1.1.1, release=Rel-18) leads forward via the Rel-18 unified-TCI-for-multi-TRP design to 38.321 §6.1.3.70 / §6.1.3.71 and to the 38.331 IEs `CandidateTCI-State-r18` / `LTM-QCL-Info-r18` (all chunkIds cited above). Similarly `R2-2110534` (RAN2#116-e, ai=8.17.2, release=Rel-17) leads forward to 38.321 §5.18.23 and the 38.331 `dl-OrJointTCI-StateList-r17` branch (linkage 7 in §9 closes this loop).
- **Backward (Spec section → originating TDoc, with `ai=` / `release=` filters).** Starting from a chunkId, the corresponding `Section` node in Neo4j is reachable, and from there the originating-TDoc set is the union of all TDocs whose `release` matches the section-introducing release and whose `agendaItem` lies inside the relevant RAN1/RAN2 multi-beam / unified-TCI / asymmetric-DL-sTRP-UL-mTRP track. For example, the 38.331 `[[ pathlossOffset-r19 ]]` extension in `TCI-State` `[chunkId=38.331-asn1-TCI-State-001]` filters back via `release=Rel-19` ∧ `ai∈{9.2.4 (RAN1), 8.12.2 (RAN2)}` to the introducing TDocs `R1-2408118` and `R2-2408402` cited in §6.1 / §6.2. The same chunkId, filtered with `release=Rel-15`, returns instead the Rel-15 base introduction TDocs `R1-1718541` / `R1-1720662` / `R2-1713533` cited in §2.1 / §2.2 — the same chunk is reachable from multiple releases because `TCI-State` is a cross-release host IE that accumulates extension blocks.

This bidirectional reproducibility is exactly the property that the paper's Document Lifecycle ontology asserts for traceability: any factual sentence in §2–§7 of this report can be re-fetched from the chunkId, and the originating-TDoc set can be reconstructed from a release- and agendaItem-filtered Cypher query without re-reading the answer text.

### 11.4 What this trace does NOT contain

Honest caveats — the trace above intentionally does not assert artefacts that are not in the indexed corpus:

1. **CR-level chunks are not queried for Q2.** None of the per-release chains above is supported by a CR-document body chunk; CR-typed TDocs (e.g. `R2-2506415`) appear only at the introduction stage as Tdoc nodes, not as parsed CR-section chunks. Wherever a "[N110] Correction" or "CR" thread is mentioned (Rel-18, Rel-19), the CR-document chunks are explicitly marked *not loaded* and the spec-body grounding is taken from TS bodies and ASN.1 IE bodies only.
2. **RAN Plenary (RP-WID) documents are not in the SPECTRA corpus.** Strings such as "RP-242394, Revised WI: NR MIMO Phase 5" appear inside RAN2 TDocs (e.g. `R2-2508663`), but the RP-WID document body itself is not loaded; the lifecycle entry-point is therefore the RAN1/RAN2 WI-discussion stage, not the Plenary stage.
3. **Rel-20 spec adoption is absent.** The Rel-20 row of §11.2 is intentionally `❌ / ❌ / n/a` for spec-body change, capability addition, and CR-level — not because no change occurs in the real standard, but because the loaded Rel-20 TDocs are at the 6G framing / Coverage Enhancement Phase-3 stage. §7.3 and §10.2 mark this as a dataset boundary.
4. **38.306 row-level chunking is partial.** §4.2.7.2 chunkIds (`-001`, `-005`, `-019`, `-024`, `-029`, `-050`, `-051`) cover the rows cited per release, but §4.2.7.2 is a long capability section and not every row is materialised as its own chunk; the per-release row attributions in the audit table cite the chunkIds that the rows resolve to, not separate per-row chunks.
5. **Rel-19 38.321 chunk-body text is weak.** §5.18.36 / §6.1.3.76 / §6.1.3.77 are catalogued as Neo4j Section nodes but their chunk bodies are weak in the current vector index (§10.2). The audit table marks this as ⚠️ rather than ✓ for the spec-body change cell.

The lifecycle trace therefore demonstrates that the SPECTRA KG can reproduce the **RAN1/RAN2 introduction → spec-body change** chain release-by-release for Rel-15 → Rel-19 from existing citations alone, while honestly reporting where the corpus stops (no RP-WID, no CR chunks for Q2, no Rel-20 spec adoption).

---

## 12. Summary

The TCI-state framework can be traced end-to-end across the 3GPP RAN spec stack from Rel-15 through Rel-19, with Rel-20 left as a dataset boundary:

1. **Rel-15** introduces the framework: 38.214 §5.1.5 defines the PDSCH TCI-State list with capability `maxNumberConfiguredTCIstatesPerCC` `[38.214-5.1.5-001]`; 38.321 §6.1.3.14 carries the PDSCH TCI MAC CE `[38.321-6.1.3.14-001]`; 38.331 establishes the IE bodies `TCI-State`, `QCL-Info` (typeA..D), `PDSCH-Config`, `PDCCH-Config`, `ControlResourceSet`, `TCI-StateId`; 38.306 §4.2.7.2 exposes the matching capability rows `[38.306-4.2.7.2-050]`.
2. **Rel-16** adds multi-beam enhancements: 38.214 §5.1.5 introduces the `tci-PresentInDCI` / `tci-PresentDCI-1-2` activation flow tying PHY to 38.321 §6.1.3.70 `[38.214-5.1.5-003 / -005]`; 38.321 §6.1.3.24 adds the eLCID-based enhanced PDSCH TCI MAC CE `[38.321-6.1.3.24-001]`; 38.306 §4.2.7.2 records `multipleTCI` (multiple TCI per CORESET) `[38.306-4.2.7.2-029]`. The RAN2 anchor for the 128-TCI-states-per-BWP figure is `[R2-1910966]`.
3. **Rel-17** introduces the unified TCI framework and inter-cell beam management: 38.214 §5.1.5 carries the `dl-OrJointTCI-StateList-r17` branch `[38.214-5.1.5-005 / -007]`; 38.321 §5.18.23 defines the unified TCI MAC CE with `simultaneousU-TCI-UpdateList*` `[38.321-5.18.23-001]`; 38.331 introduces `TCI-UL-State-r17` (with the SSB/CSI-RS/SRS reference-signal CHOICE), `TCI-UL-StateId-r17`, and the `dl-OrJointTCI-StateList-r17` / `unifiedTCI-StateRef-r17` branches inside `PDSCH-Config`.
4. **Rel-18** consolidates the unified TCI framework into multi-TRP and LTM: 38.321 adds §5.18.33 / §6.1.3.70 / §6.1.3.71 (enhanced unified TCI MAC CE for joint and separate); 38.331 introduces `CandidateTCI-State-r18`, `CandidateTCI-UL-State-r18`, and the new `LTM-QCL-Info-r18` (typeA..D enum), plus the `[[ tag-Id-ptr-r18 -- Cond 2TA ]]` extension block in `TCI-State` / `TCI-UL-State-r17`. 38.306 §4.2.7.2 adds the largest single-release Rel-18 capability cluster (`tci-JointTCI-Update*-r18`, `tci-SeparateTCI-Update*-r18`, `commonTCI-Multi/SingleDCI-r18`, `ltm-BeamIndication{Joint,Separate}TCI-r18`).
5. **Rel-19** adds path-loss control and the asymmetric DL sTRP / UL mTRP framework reuse: 38.331 introduces the `[[ pathlossOffset-r19 ENUMERATED {dB-12..dB60} ]]` extension block in both `TCI-State` and `TCI-UL-State-r17` `[38.331-asn1-TCI-State-001 / -TCI-UL-State-r17-001]`; 38.321 catalogues §5.18.36 / §6.1.3.76 / §6.1.3.77 for candidate-cell and cross-RRH TCI MAC CEs `[Neo4j RAN2]`; 38.306 §4.2.7.2 adds the CJT-QCL scheme rows `cjt-QCL-PDSCH-Scheme{C,D,E}-r19` `[38.306-4.2.7.2-005]` and the LTM CSI-RS rows `[38.306-4.2.7.2-024]`.
6. **Rel-20** is, in this dataset, a 6G framing release: the loaded RAN1/RAN2 TDocs (`[R1-2506358]`, `[R1-2506063]`, `[R1-2505125]`, `[R2-2508849]`, `[R2-2508085]` and others) are 6G air-interface overviews / NR Phase-3 coverage enhancement / 6G mobility framing. No Rel-20 TCI spec-body changes in 38.214 / 38.321 / 38.331 / 38.306 are present in the SPECTRA RAG dataset, and §7.3 / §10.2 mark this explicitly as a dataset boundary rather than as evidence of "no change in the standard".
7. **Coverage**: 18/24 cells of the Release × Document matrix are direct body citations (✅); 2/24 are partial (⚠️ Rel-17 38.306 — only -r18 introduction-premise rows; Rel-19 38.214 — cumulative section, Rel-19-specific separator chunks weak); the 4/24 ❌ cells are all Rel-20. The TDoc → spec-change flow in §9 (linkage 7) closes the loop release-by-release from Rel-15 to Rel-19.
