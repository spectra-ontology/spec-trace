# NR TCI-State Standard Evolution Analysis Report (Rel.15 ~ Rel.20)

## Table of Contents
1. [Overview of the TCI-State Concept](#1-overview-of-the-tci-state-concept)
2. [Rel.15 — Introduction of the TCI-State](#2-rel15--introduction-of-the-tci-state)
3. [Rel.16 — Multi-TRP and URLLC Extensions](#3-rel16--multi-trp-and-urllc-extensions)
4. [Rel.17 — Unified TCI Framework](#4-rel17--unified-tci-framework)
5. [Rel.18 — UL Tx Switching, MIMO Evolution, and LTM Coupling](#5-rel18--ul-tx-switching-mimo-evolution-and-ltm-coupling)
6. [Rel.19 — Coupling with AI/ML-based Beam Management](#6-rel19--coupling-with-aiml-based-beam-management)
7. [Rel.20 — Direction of Evolution](#7-rel20--direction-of-evolution)
8. [Cross-Document Structure (Integrated Across Releases)](#8-cross-document-structure-integrated-across-releases)

---

## 1. Overview of the TCI-State Concept

A **TCI (Transmission Configuration Indicator) State** is the core framework in NR that abstracts **the spatial and large-scale parameter relationship between DL/UL signals**. It encapsulates the following two pieces of information:

- **QCL (Quasi Co-Location) relationship**: The relationship by which channel properties are shared between one RS and another RS
- **Beam identifier**: An indication of which spatial filter (=beam) the UE should use

Four QCL types are defined:
- **Type A**: Doppler shift, Doppler spread, average delay, delay spread
- **Type B**: Doppler shift, Doppler spread
- **Type C**: Doppler shift, average delay
- **Type D**: Spatial Rx parameter (=beam)

**Type D** is effectively the "beam" information and plays a central role in the FR2 (mmWave) bands.

---

## 2. Rel.15 — Introduction of the TCI-State

### 2.1 Motivation (WID: RP-170739, RP-181433)

The NR Rel.15 SI/WI considered mmWave-band (FR2) operation from the start, and presented the following requirement:

> *"Specify mechanism to support analog beamforming-based transmission and reception, including beam indication for both downlink and uplink."*

LTE assumed omni-directional transmission based on cell-specific reference signals, but in NR **beamforming must be the default**. The framework introduced for this is the TCI-state.

### 2.2 38.214 — QCL Assumption (Rel.15)

#### 2.2.1 PDSCH QCL Source (Clause 5.1.5)

The UE assumes that the DM-RS port of the PDSCH is QCL'd with the following RS:
- The TCI-state indicated by DCI (one of M candidates)
- If the TCI field is absent in DCI, a default rule applies (the TCI of the most recently activated CORESET)

**In Rel.15, the PDSCH TCI field exists only in DCI Format 1_1**.

#### 2.2.2 PDCCH QCL Source (Clause 5.1.5)

For each CORESET, a TCI-state list is configured by RRC, then 1 is activated by MAC-CE:
- CORESET 0 (PBCH-config): QCL'd with the SS/PBCH block (default)
- CORESET >0: Candidates are configured via TCI-StatesPDCCH-ToAddList → 1 is activated by MAC-CE

#### 2.2.3 CSI-RS QCL

Each NZP-CSI-RS-Resource is associated with a TCI-state via `qcl-InfoPeriodicCSI-RS` or via dynamic activation.

### 2.3 38.321 — MAC-CE Procedures (Rel.15)

| MAC-CE | LCID | Function |
|---|---|---|
| TCI States Activation/Deactivation for UE-specific PDSCH MAC CE | 53 | Activate 8 out of 64 RRC-configured candidates (3-bit indication possible) |
| TCI State Indication for UE-specific PDCCH MAC CE | 52 | Activate 1 TCI per CORESET |
| Aperiodic CSI Trigger State Subselection MAC CE | 47 | CSI trigger state selection |

#### Example MAC-CE format (PDSCH TCI Activation):

```
| Serving Cell ID (5 bits) | BWP ID (2 bits) | R |
| T0 (1) | T1 (1) | T2 (1) | T3 (1) | T4 (1) | T5 (1) | T6 (1) | T7 (1) |  ← 64-bit bitmap
| TCI state IDs ...                                                       |
```

After receiving the TCI activation command, it must be applied **within 3 ms (HARQ-ACK + processing delay)**.

### 2.4 38.331 — RRC Parameters (Rel.15)

```asn1
TCI-State ::= SEQUENCE {
    tci-StateId         TCI-StateId,
    qcl-Type1           QCL-Info,
    qcl-Type2           QCL-Info  OPTIONAL,
    ...
}

QCL-Info ::= SEQUENCE {
    cell                ServCellIndex  OPTIONAL,
    bwp-Id              BWP-Id  OPTIONAL,
    referenceSignal     CHOICE {
        csi-rs              NZP-CSI-RS-ResourceId,
        ssb                 SSB-Index
    },
    qcl-Type            ENUMERATED {typeA, typeB, typeC, typeD},
    ...
}
```

Key rules:
- A TCI-state holds at most 2 QCL relations (qcl-Type1 mandatory, qcl-Type2 optional)
- For FR2 operation, qcl-Type2 must be typeD
- `tci-StatesToAddModList`: up to 64 candidates
- `tci-StatesToReleaseList`: deletion list

### 2.5 38.306 — UE Capability (Rel.15)

```
maxNumberConfiguredTCIStatesPerCC: { n4, n8, n16, n32, n64, n128 }
maxNumberActiveTCI-PerBWP: { n1, n2, n4, n8 }
```

- The number of TCIs that can be simultaneously activated by MAC-CE among the 64 RRC candidates (declared per UE band)
- FR1: typically n1 or n2; FR2: n4 or n8

---

## 3. Rel.16 — Multi-TRP and URLLC Extensions

### 3.1 Motivation (WID: RP-193133, NR MIMO Enhancement)

Rel.16 extended the TCI framework with two main motivations:

1. **Multi-TRP support**: Apply two TCI-states simultaneously to transmit the same PDSCH from two TRPs
2. **URLLC**: Improve reliability through PDSCH repetition

### 3.2 38.214 — QCL Assumption Extensions

#### 3.2.1 Simultaneous Application of Two TCI-States for Multi-TRP (Clause 5.1.5)

The TCI-field codepoints in DCI Format 1_1 can now be **mapped to two TCI-states**:

- Each TCI state applies to half of the PDSCH's layers (NCJT, scheme 1a)
- Or each TRP uses different time/frequency resources (FDM scheme 2a/2b, TDM scheme 3, 4)

Five Multi-TRP schemes are defined:
- **Scheme 1a (SDM)**: Two TRPs transmit different layers (NCJT)
- **Scheme 2a/2b (FDM)**: Different frequency resources
- **Scheme 3 (TDM intra-slot)**: Different mini-slots within the same slot
- **Scheme 4 (TDM inter-slot)**: Different slots

#### 3.2.2 PDCCH Repetition

Different TCIs are applied to two CORESETs, and MO (monitoring occasion) linking allows the same DCI to be received twice → soft combining.

### 3.3 38.321 — MAC-CE Extensions

New MAC-CE: **Enhanced TCI States Activation/Deactivation for UE-specific PDSCH MAC CE** (LCID 49):
- Two TCI states can be mapped to a single codepoint
- 8 codepoints × 2 TCIs = up to 16 TCIs simultaneously active

### 3.4 38.331 — RRC Extensions

```asn1
PDCCH-Config ::= SEQUENCE {
    ...,
    [[
    monitoringCapabilityConfig-r16   ENUMERATED {r15monitoringcapability, r16monitoringcapability}
    ]]
}

PDSCH-Config ::= SEQUENCE {
    ...,
    [[
    repetitionSchemeConfig-r16       SetupRelease { RepetitionSchemeConfig-r16 } OPTIONAL,
    enableTwoQCLTypeDForBFD-RS-r17   ENUMERATED {enabled} OPTIONAL  -- (this is Rel.17)
    ]]
}

RepetitionSchemeConfig-r16 ::= CHOICE {
    fdm-TDM-r16    SetupRelease { FDM-TDM-r16 },
    slotBased-r16  SetupRelease { SlotBased-r16 }
}
```

### 3.5 38.306 — Capability Extensions

```
maxNumberSimultaneousTCI-States-NCJT-r16
maxNumberConfiguredTCI-StatePoolsPerBWP-NCJT-r16
mTRP-PDSCH-r16
mTRP-PDCCH-r16
```

---

## 4. Rel.17 — Unified TCI Framework

### 4.1 Motivation (WID: RP-202147 / RP-211583, FeMIMO)

The biggest limitation in Rel.15/16 was that **DL and UL beam indications were separated**:
- DL: TCI-state (PDCCH/PDSCH/CSI-RS)
- UL: Spatial Relation Info (PUCCH/SRS) or SRI (PUSCH)

This caused:
- Even when the same beam should be applied to DL and UL, separate RRC + MAC-CE signaling was required
- Difficult panel-by-panel management for multi-panel UE operation
- Increased beam-switching latency

The **Unified TCI Framework** provides a unified structure that indicates both DL and UL through a single framework.

### 4.2 38.214 — Unified TCI

#### 4.2.1 Joint TCI vs Separate TCI

Two modes are defined:
- **Joint TCI**: A single TCI applies to both DL and UL
- **Separate TCI**: DL TCI and UL TCI are separate

#### 4.2.2 New TCI-state Types (Extending Clause 5.1.5)

| Type | Applies to |
|---|---|
| Joint TCI | PDCCH, PDSCH, CSI-RS, PUCCH, PUSCH, SRS (all) |
| DL-only TCI | PDCCH, PDSCH, CSI-RS |
| UL-only TCI | PUCCH, PUSCH, SRS |

In addition to DCI Formats 1_1 and 1_2, TCI indication can also be done via **new codepoints in DCI Format 1_1/1_2** or via **DCI Format 1_1 with a non-scheduling DL grant**.

#### 4.2.3 PDCCH Order TCI Indication

In particular, "DCI without DL assignment" (a purely beam-indication DCI) is introduced → enables faster beam switching than MAC-CE.

### 4.3 38.321 — MAC-CE Extensions

**Unified TCI States Activation/Deactivation MAC CE** (LCID 56):
- Joint TCI list and separate TCI list are managed separately
- Up to 64 → 8 active

### 4.4 38.331 — RRC Extensions

```asn1
PDSCH-Config ::= SEQUENCE {
    ...,
    [[
    unifiedTCI-StateType-r17        ENUMERATED { joint, separate } OPTIONAL,
    dl-OrJointTCI-StateList-r17     SEQUENCE (SIZE (1..maxNrofTCIs-r17)) OF TCI-State OPTIONAL,
    ul-TCI-StateList-r17            SEQUENCE (SIZE (1..maxNrofTCIs-r17)) OF TCI-UL-State-r17 OPTIONAL
    ]]
}

TCI-UL-State-r17 ::= SEQUENCE {
    tci-UL-StateId          TCI-UL-StateId-r17,
    bwp-Id                  BWP-Id  OPTIONAL,
    referenceSignal         CHOICE {
        ssb         SSB-Index,
        csi-rs      NZP-CSI-RS-ResourceId,
        srs         SRS-ResourceId-r17     -- For UL, SRS can also be a reference
    },
    ul-PowerControl-r17     PowerControl-r17  OPTIONAL,
    pathlossReferenceRS-Id  PathlossReferenceRS-Id-r17  OPTIONAL
}
```

Key differences:
- UL TCI **can use an SRS resource as a reference** (a natural source for UL beamforming)
- Pathloss RS and power control parameters are integrated into the TCI

### 4.5 38.306 — Capability

```
unifiedTCI-StateMode-r17: { joint, separate, both }
maxNumActiveTCI-StatesPerCC-r17
beamSwitchTiming-r17
ul-TCI-r17
```

The UE reports which mode it supports (joint or separate) and the simultaneous active-TCI count.

### 4.6 Beam Application Time

A core new concept in Rel.17: **beam application time T_BAT**
- DCI reception → ACK → indicated TCI is applied after T_BAT
- T_BAT is reported as the UE capability `beamAppTime-r17` (1, 3, 7 slots, etc.)

---

## 5. Rel.18 — UL Tx Switching, MIMO Evolution, and LTM Coupling

### 5.1 Motivation (WID: RP-234037, NR_MIMO_evolution_Ph4)

Rel.18 extended unified TCI into the following areas:

1. **Multi-cell beam management**: Apply a single TCI to multiple serving cells (CA scenario)
2. **L1/L2 Triggered Mobility (LTM)**: Move cell change away from RRC reconfig to MAC-CE/DCI (see separate report)
3. **Multi-panel UE**: TCI extensions for simultaneous multi-panel transmission

### 5.2 38.214 — Extensions

#### 5.2.1 Multi-cell TCI

A single TCI activation MAC-CE applies the same TCI to multiple CCs:
- Efficient when multiple CCs in the same frequency band use the same beam
- The list of cells to be updated together is defined in `simultaneousTCI-UpdateList` (RRC)

#### 5.2.2 Multi-panel Simultaneous Transmission (STxMP)

UE simultaneously transmits PUSCH from two panels:
- Two SRS resource sets, two TCIs active
- A panel selection field is added to DCI

#### 5.2.3 Integration with LTM

In LTM, the TCI of a candidate cell is preconfigured via RRC → activated by MAC-CE/DCI. LTM itself is covered in a separate report.

### 5.3 38.321 — MAC-CE Extensions

- **Unified TCI States Activation/Deactivation MAC CE for multiple cells** (additional LCID)
- **LTM cell switch command MAC CE** (additional LCID) — separate report

### 5.4 38.331 — RRC Extensions

```asn1
PDSCH-Config ::= SEQUENCE {
    ...,
    [[
    -- Rel.18 multi-cell TCI
    simultaneousU-TCI-UpdateList1-r18       SEQUENCE OF ServCellIndex OPTIONAL,
    simultaneousU-TCI-UpdateList2-r18       SEQUENCE OF ServCellIndex OPTIONAL,
    simultaneousU-TCI-UpdateList3-r18       SEQUENCE OF ServCellIndex OPTIONAL,
    simultaneousU-TCI-UpdateList4-r18       SEQUENCE OF ServCellIndex OPTIONAL
    ]]
}
```

Each list defines a CC group to be updated simultaneously. Up to four groups can be operated.

### 5.5 38.306 — Capability

```
multiCellPdcch-PdschTciStateUpdate-r18
multiPanelMTRP-PUSCH-r18
unifiedTCI-MultiCellSet-r18
```

---

## 6. Rel.19 — Coupling with AI/ML-based Beam Management

### 6.1 Motivation (WID: RP-234039, AI/ML for NR Air Interface)

In Rel.19, AI/ML for beam management is being progressed in earnest as SI/WI, and the TCI framework is extended in the following directions (reflecting status as of writing):

1. **AI/ML-based beam prediction**: Predict the best beam from partial measurements → compress TCI candidates
2. **Spatial domain prediction**: Measure only Set B (subset) of Set A (full) → AI recommends Set A's TCI
3. **Temporal domain prediction**: Predict future beams from past measurements → fast TCI changes

### 6.2 38.214 — Changes

#### 6.2.1 AI/ML CSI/Beam Reporting

Define new reporting quantities:
- `cri-ssb-AI-prediction`: Reports AI model input/output
- The UE can actively propose TCI recommendations

### 6.3 38.321 — MAC-CE

AI/ML model activation/deactivation MAC-CE (working assumption):
- Activate/deactivate by model ID
- The TCI activation MAC-CE retains the existing framework but includes AI recommendation results

### 6.4 38.331 — RRC

```asn1
-- (Rel.19 working draft level)
AI-ML-Configuration-r19 ::= SEQUENCE {
    modelId                 AI-ML-ModelId-r19,
    functionalityType       ENUMERATED { beamPrediction, csiCompression, ... },
    inputConfiguration      ...,
    outputConfiguration     ...
}
```

(Since Rel.19 is at the completion stage at the time of writing, some details may change once finalized.)

### 6.5 38.306 — Capability

```
ai-ml-BeamPrediction-r19
ai-ml-Spatial-r19
ai-ml-Temporal-r19
maxNumber-ai-ml-Models-r19
```

---

## 7. Rel.20 — Direction of Evolution

### 7.1 Ongoing Work (Based on the TSG-RAN Work Plan)

Rel.20 is in the SI stage at the time of writing, and the main TCI-related candidates are:

1. **Cross-Carrier TCI**: Use an RS measured on a different carrier as a TCI reference in CA operation
2. **Sub-band Specific TCI**: Apply different TCIs per sub-band within a BWP (frequency-selective beamforming)
3. **AI/ML Mature**: Extend the AI/ML beam management of Rel.19 into a normative feature
4. **TCI in NTN environments**: Dynamic TCI reflecting satellite/UE motion in non-terrestrial networks

### 7.2 Potential RRC Extensions

```asn1
TCI-State-r20 ::= SEQUENCE {
    ...,
    crossCarrierRefRS-r20       OPTIONAL,
    subbandTCI-Application-r20  OPTIONAL,
    ntn-DopplerComp-r20         OPTIONAL
}
```

(Spec area not yet finalized)

---

## 8. Cross-Document Structure (Integrated Across Releases)

### 8.1 Per-Release Evolution Matrix

| Element | Rel.15 | Rel.16 | Rel.17 | Rel.18 | Rel.19 | Rel.20 |
|---|---|---|---|---|---|---|
| **TCI applies to** | DL-only (CSI-RS, PDCCH, PDSCH) | + Multi-TRP | + Unified DL/UL | + Multi-cell, Multi-panel | + AI/ML recommendation | + Cross-carrier, Sub-band |
| **Activation method** | RRC + MAC-CE (PDCCH), DCI (PDSCH) | + 2-TCI codepoint | + DCI w/o DL grant, T_BAT | + LTM coupling | + AI model based | + Various |
| **38.214 core clause** | 5.1.5 (QCL) | 5.1.5 + Multi-TRP | 5.1.5 + Unified | + Multi-cell | + AI/ML | TBD |
| **New 38.321 MAC-CE** | TCI Activation (PDSCH/PDCCH) | Enhanced PDSCH TCI (2-TCI) | Unified TCI Activation | Multi-cell TCI, LTM | AI/ML model | TBD |
| **38.331 core IE** | TCI-State, QCL-Info | RepetitionSchemeConfig | unifiedTCI-StateType, TCI-UL-State | simultaneousU-TCI-UpdateList | AI-ML-Config | TBD |
| **38.306 core capability** | maxNumberActiveTCI-PerBWP | mTRP-PDSCH/PDCCH | unifiedTCI-StateMode, beamAppTime | multiCellPdcch-PdschTciStateUpdate | ai-ml-BeamPrediction | TBD |

### 8.2 Cross-Document Flow (Example: Rel.17 Unified TCI)

```
                [WID: RP-211583, FeMIMO]
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
   [38.214 §5.1.5]   [38.321 MAC-CE]  [38.331 RRC]
   - Joint/Separate  - Unified TCI    - unifiedTCI-StateType
     TCI definition    Activation       - New TCI-UL-State
   - T_BAT defined     MAC-CE         - dl-OrJointTCI-StateList
                                       - ul-TCI-StateList
          │               │               │
          └───────┬───────┴───────────────┘
                  ▼
          [38.306 Capability]
          - unifiedTCI-StateMode (joint/separate)
          - beamAppTime
          - ul-TCI
                  │
                  ▼
          [38.133 RRM Test]
          - TCI activation latency requirement
          - Beam application time test
```

### 8.3 Key Consistency Checkpoints

In each release, the following must be aligned across documents:

1. **TCI ID space**:
   - 38.331's `tci-StateId` (0~127) ↔ width of the TCI ID field in the 38.321 MAC-CE ↔ indication rules in 38.214
   - In Rel.17, joint/UL use a separate ID space

2. **Number of active TCIs**:
   - 38.306 capability `maxNumberActiveTCI-PerBWP` ≤ 38.331 RRC max configurable ≤ 38.321 MAC-CE bitmap length

3. **DCI codepoints and active TCIs**:
   - DCI TCI field = 3 bits → 8 codepoints → maps 8 of the TCIs activated by MAC-CE
   - From Rel.16+, codepoints can map to 1 or 2 TCIs

4. **QCL Type D rule**:
   - "qcl-Type2 = typeD only when FR2", defined in 38.214 §5.1.5, is reflected in RRC validation in 38.331

### 8.4 Evolution of Beam Switching Timeline

| Release | Beam-switching method | Latency (typical) |
|---|---|---|
| Rel.15 | RRC reconfig + MAC-CE activation + DCI indication | ~10 ms |
| Rel.16 | + 2-TCI MAC-CE (multi-TRP) | ~10 ms (similar) |
| Rel.17 | Unified TCI + DCI w/o DL grant + T_BAT | ~3 ms (T_BAT shortened) |
| Rel.18 | LTM (MAC-CE/DCI based cell switch) | <100 ms (cell change) |
| Rel.19 | AI/ML predicted TCI | proactive (predictable) |

---

## 9. Conclusion

The NR TCI-state framework has evolved along the following axes:

1. **Coverage Expansion**: DL-only → DL+UL Unified → Multi-cell, Multi-panel
2. **Latency Reduction**: RRC → MAC-CE → DCI → AI/ML prediction
3. **Granularity**: Per-BWP → Per-cell-group → Per-subband (Rel.20)
4. **Intelligence**: Measurement-based → AI/ML-inference based

In particular, Rel.17's Unified TCI Framework is an architectural turning point in NR beam management; Rel.18 LTM, Rel.19 AI/ML, and Rel.20's future extensions are all built on top of this framework.

---

*Document references: TS 38.214, 38.321, 38.331, 38.306, 38.133 (Rel.15 ~ Rel.19), RP-170739, RP-181433, RP-193133, RP-211583, RP-234037, RP-234039*
