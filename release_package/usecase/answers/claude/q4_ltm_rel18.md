# Rel.18 LTM (L1/L2 Triggered Mobility) Standard Analysis and Rel.19/20 Evolution Report

## Table of Contents
1. [Motivation for LTM](#1-motivation-for-ltm)
2. [38.300 — LTM Concept and Architecture](#2-38300--ltm-concept-and-architecture)
3. [38.331 — RRC Parameters](#3-38331--rrc-parameters)
4. [38.321 — MAC-CE Behavior](#4-38321--mac-ce-behavior)
5. [38.214 — L1 Measurement and Reporting](#5-38214--l1-measurement-and-reporting)
6. [38.133 — RRM Requirements](#6-38133--rrm-requirements)
7. [38.306 — UE Capability](#7-38306--ue-capability)
8. [Rel.19 — LTM Extensions](#8-rel19--ltm-extensions)
9. [Rel.20 — LTM Direction of Evolution](#9-rel20--ltm-direction-of-evolution)
10. [Cross-Document Linkages](#10-cross-document-linkages)

---

## 1. Motivation for LTM

### 1.1 Limitations of the Conventional Handover

The mobility techniques in use since NR Rel.15:

| Technique | Release | Latency | Issue |
|---|---|---|---|
| L3 Handover (RRC reconfig) | Rel.15 | 50~100 ms | RRC signaling is heavy; large interruption |
| Conditional Handover (CHO) | Rel.16 | 20~50 ms | Still at the RRC level |
| DAPS Handover | Rel.16 | ~ tens of ms | UL data lossless, but complex |

In particular, in **fast-changing beams in FR2** and **frequent cell changes in dense small-cell deployments**, the latencies above degrade user experience.

### 1.2 WID: RP-234037 (NR_Mob_enh_Ph4)

The Rel.18 mobility enhancement WID explicitly states the following as the core objective:

> *"Specify L1/L2-based inter-cell mobility (LTM) procedure to reduce mobility latency and interruption time, leveraging the existing beam management framework."*

### 1.3 Core Concept

The core idea of LTM is to **trigger cell change via MAC-CE or DCI without RRC reconfiguration**.

```
[Conventional HO]                  [LTM (Rel.18)]
                                   
RRC Reconfig (Source)              RRC Reconfig with candidate config (Source) [pre-configured]
   ↓                                   ↓ (in advance)
RRC Reconfig (Target)              Cell switch via MAC-CE or DCI
   ↓                                   ↓
~50 ms interruption                <20 ms interruption
```

### 1.4 What Differentiates LTM

- **Pre-configuration**: Candidate cells are configured in advance via RRC
- **Dynamic activation**: Cell switch is performed immediately via MAC-CE or DCI
- **Beam-cell unified management**: Beams and cells are managed in an integrated way on top of the TCI framework
- **Use of lower-layer measurements**: L1 measurements are used instead of L3 measurements

---

## 2. 38.300 — LTM Concept and Architecture

### 2.1 Position of LTM (Clause 9.2.x)

In 38.300, LTM is defined as follows:

> *"L1/L2 triggered mobility (LTM) is a mechanism for fast inter-cell mobility within a single Master Node (MN) where candidate target cells are pre-configured via RRC and the cell switch is triggered by L1/L2 signaling (MAC CE or DCI)."*

### 2.2 Architecture Assumptions

#### 2.2.1 Scope of Application
- **Intra-DU LTM**: Cell change within the same gNB-DU (lowest latency)
- **Intra-CU/Inter-DU LTM**: Between different DUs within the same gNB-CU (Rel.18 working assumption)
- **Inter-gNB**: Not supported in Rel.18 (Rel.19+ candidate)

#### 2.2.2 Source ↔ Target Cell Relationship
- Same or different frequency
- Same or different PCI (Physical Cell Identifier)
- Assumed to be managed by the same gNB-CU

### 2.3 LTM Procedure Overview (38.300 Clause 9.2.x)

```
[Step 1: Pre-configuration phase]
   Source cell ─── RRC Reconfiguration with candidate cell list ───> UE
                   (CandidateCellInfoListLTM)

[Step 2: Measurement phase]
   UE ─── L1 measurements on candidate cell SSB/CSI-RS ───> Source cell
        (per-cell L1-RSRP / L1-SINR reporting)

[Step 3: Cell switch trigger]
   Source cell ─── MAC-CE (LTM Cell Switch Command) ───> UE
        OR ─── DCI Format X (LTM trigger) ───> UE

[Step 4: Cell switch execution]
   UE: Apply target cell configuration (TCI, BWP, RACH, ...) without RRC reconfig

[Step 5: Optional RACH-less / RACH-based access]
   - RACH-less: TA reuse from pre-config
   - RACH-based: Random access on the target cell

[Step 6: Confirmation]
   UE ─── PDCCH received on the target cell ───> procedure complete
```

### 2.4 Relationship with Cell Groups

LTM operates within the **MCG (Master Cell Group)**. SCG (Secondary Cell Group) is outside the scope of Rel.18 LTM and is a candidate for review in future releases.

---

## 3. 38.331 — RRC Parameters

### 3.1 CandidateCellInfoListLTM-r18

This is the core LTM RRC IE. The source cell pre-configures candidate cells on the UE.

```asn1
CandidateCellInfoListCPC-LTM-r18 ::= SEQUENCE (SIZE (1..maxNrofCandidateCells-r18)) 
    OF CandidateCellInfo-LTM-r18

CandidateCellInfo-LTM-r18 ::= SEQUENCE {
    physCellId-r18              PhysCellId,
    ssbFrequency-r18            ARFCN-ValueNR  OPTIONAL,
    candidateConfigId-r18       CandidateCellConfigId-r18,
    rrcReconfiguration-r18      OCTET STRING (CONTAINING RRCReconfiguration),
    -- The above is similar to existing CHO
    
    -- New LTM portion
    ltm-CellId-r18              LTM-CellId-r18,
    ltm-CandidateConfig-r18     LTM-CandidateConfig-r18,
    ...
}

LTM-CandidateConfig-r18 ::= SEQUENCE {
    rach-ConfigGenericLTM-r18       RACH-ConfigGenericLTM-r18  OPTIONAL,
    timingAdjustmentLTM-r18         INTEGER (-127..128)  OPTIONAL,  -- TA pre-config
    ssbToTrack-r18                  SEQUENCE OF SSB-Index  OPTIONAL,
    csiRS-ResourceList-r18          SEQUENCE OF NZP-CSI-RS-ResourceId  OPTIONAL,
    tciStateList-r18                SEQUENCE OF TCI-StateId  OPTIONAL,
    ...
}
```

### 3.2 IEs Related to LTM Activation

```asn1
PDCCH-Config ::= SEQUENCE {
    ...,
    [[
    -- Rel.18
    candidateCellSwitchTriggerConfig-r18    SetupRelease { CandidateCellSwitchTriggerConfig-r18 } OPTIONAL
    ]]
}

CandidateCellSwitchTriggerConfig-r18 ::= SEQUENCE {
    triggerMethod-r18           ENUMERATED { mac-CE, dci, both },
    targetCellList-r18          SEQUENCE OF LTM-CellId-r18,
    cellSwitchTimer-r18         ENUMERATED {ms10, ms20, ...} OPTIONAL,
    ...
}
```

### 3.3 L1 Measurement Configuration Extensions

```asn1
CSI-MeasConfig ::= SEQUENCE {
    ...,
    [[
    candidateCellMeasConfigLTM-r18  SEQUENCE OF CandidateCellMeasLTM-r18  OPTIONAL
    ]]
}

CandidateCellMeasLTM-r18 ::= SEQUENCE {
    candidateCellId-r18         LTM-CellId-r18,
    measResource-r18            CHOICE {
        ssb         SSB-Index,
        csi-rs      NZP-CSI-RS-ResourceId
    },
    reportConfig-r18            CSI-ReportConfigId
}
```

### 3.4 Summary of Key IE Meanings

| IE | Meaning |
|---|---|
| `CandidateCellInfoListCPC-LTM-r18` | Pre-configured candidate cell list (up to 8 or 16) |
| `LTM-CandidateConfig-r18` | Per-candidate RACH, TA, TCI, BWP configuration |
| `candidateCellSwitchTriggerConfig-r18` | Selection of trigger method (MAC-CE / DCI) |
| `cellSwitchTimer-r18` | Switch procedure timeout |
| `candidateCellMeasConfigLTM-r18` | Candidate cell SSB/CSI-RS L1 measurement configuration |
| `timingAdjustmentLTM-r18` | TA pre-config (for RACH-less switch) |
| `ssbToTrack-r18` | SSB index to monitor at the candidate cell |

---

## 4. 38.321 — MAC-CE Behavior

### 4.1 New MAC-CE: LTM Cell Switch Command MAC CE

The following MAC-CE is defined in 38.321 Clause 5.x.y (LCID is separately allocated; new in R18):

```
| R | R | T  | Candidate Cell Configuration ID (5 bits) |   ← octet 1
| TCI State ID  (7 bits)               | R                |   ← octet 2
| BWP ID (2)| R | R | R | R | R | R              |        ← octet 3 (optional)
...
```

#### Field meanings:
- **T (Type)**: Switch type (RACH-less / RACH-based)
- **Candidate Cell Configuration ID**: Which of the pre-configured candidates to use
- **TCI State ID**: The beam to activate (refers to the target cell's TCI list)
- **BWP ID**: BWP to activate at the target cell

### 4.2 LTM Procedure (MAC View) — Clause 5.x

```
[T = 0]: MAC-CE for LTM cell switch received
[T = T1]: MAC-CE processing begins (after HARQ ACK)
[T = T1 + T_apply]: LTM cell switch is applied
   - Maintain RRC connection of source cell (PHY moves to target)
   - Apply target cell PHY/MAC config
   - TCI activation (the indicated TCI within target)
   - BWP switch (the target's indicated BWP)
   
[T = T1 + T_apply + T_RACH (optional)]: RACH procedure (when necessary)
   - RACH-less when timingAdjustmentLTM is used
   - Otherwise, 4-step RA
   
[T = T1 + T_total]: Begin PDCCH monitoring on the target cell
```

T_apply is defined in 38.133 (typical: a few ms ~ tens of ms).

### 4.3 RACH-less LTM

While the UE is in the source cell, it is informed of the TA for candidate cells in advance:
- `timingAdjustmentLTM-r18`: Either derived from the existing source TA or explicit
- If TA can be corrected via SSB/CSI-RS measurements at the target cell, RACH can be skipped

### 4.4 LTM and Its Relationship with BFR/Beam Management

After LTM cell switch:
- **TCI re-activation** is required (38.321 unified TCI activation MAC CE)
- The BFR procedure is reset to the new cell context
- The beamFailureInstanceMaxCount counter is reset

### 4.5 DCI-Triggered LTM

In addition to MAC-CE, **DCI-based triggers** are introduced (some Rel.18 working assumptions → final spec to be confirmed):
- A new DCI Format or use of reserved fields in existing DCI
- Lower trigger latency than MAC-CE
- However, payload is small, so only simple triggers are possible (full configuration relies on RRC pre-config)

---

## 5. 38.214 — L1 Measurement and Reporting

### 5.1 Candidate Cell L1 Measurement (Extension of Clause 5.1.6)

L1 measurements the UE performs for LTM candidate cells:

#### 5.1.1 Measurement Targets
- Candidate cell SSB (SS-RSRP, SS-SINR)
- Candidate cell CSI-RS (CSI-RSRP, CSI-SINR)
- The candidate cell's RSs are located in time/frequency resources pre-informed by the source cell

#### 5.1.2 Measurement Period
- SSB: candidate cell SSB periodicity (typical 20 ms)
- CSI-RS: per RRC `periodicityAndOffset`
- Measurement window: can be defined by the source cell (UE measurement gap may be used)

### 5.2 L1 Reporting for LTM (Extension of Clause 5.2.1.4)

#### 5.2.1 Report Quantity Extension

LTM-related quantities are added to the existing CSI-ReportConfig's `reportQuantity`:

```
reportQuantity ENUMERATED {
    none, cri-RI-PMI-CQI, ...,
    cri-RSRP-r17,
    -- Rel.18 new
    cri-RSRP-Index-r18,                  -- per-cell
    ssb-Index-RSRP-LTM-r18,
    cell-Quality-LTM-r18                 -- aggregated cell-level
}
```

#### 5.2.2 Per-Cell L1 Report

The UE reports the following per candidate cell:
- Cell ID (or candidate config ID)
- The best SSB index or CSI-RS resource index
- Corresponding L1-RSRP (or L1-SINR)

#### 5.2.3 Reporting Trigger
- **Periodic**: Periodic reporting on PUCCH
- **Aperiodic**: Triggered by DCI or MAC-CE
- **Event-triggered**: When a candidate cell's L1-RSRP exceeds the source by a certain dB margin (Rel.18 enhancement)

### 5.3 Bypassing L3 Filtering

Since LTM aims at fast switching, **L3 filtering (smoothing) is bypassed**:
- Existing L3 measurement: applies layer-3 filter to SS-RSRP (smoothing on the order of hundreds of ms ~ seconds)
- LTM L1 measurement: reports immediately without filtering (a few ms ~ tens of ms)

### 5.4 Resource Mapping Assumptions

The UE must know the location of the candidate cell's SSB/CSI-RS based on the source cell's frame structure:
- `ssbFrequency-r18`: SSB frequency of the candidate cell
- The candidate cell's SCS, slot offset, etc., are provided in advance via RRC

---

## 6. 38.133 — RRM Requirements

### 6.1 Candidate Cell Measurement Requirements (Clause 9.x)

#### 6.1.1 Measurement Period

The UE must be able to measure the candidate cell's RSRP within the following time:

$$T_{\text{LTM\_meas}} = N \cdot T_{\text{SSB}} + T_{\text{processing}}$$

where N is the number of SSB samples (typical 1~5) and T_SSB is the SSB periodicity.

Typical values: **20~100 ms** (FR1), **40~200 ms** (FR2)

#### 6.1.2 Measurement Accuracy

Accuracy of L1-RSRP measurements at candidate cells:
- ±6 dB (FR1, normal condition)
- ±9 dB (FR2)

### 6.2 LTM Cell Switch Latency Requirements

#### 6.2.1 Total Switch Time

```
T_total = T_signaling + T_apply + T_RACH (if applicable) + T_PDCCH_acquisition
```

Typical requirements per component:
- T_signaling: MAC-CE reception + ACK = ~5 ms
- T_apply: applying target cell config = ~10 ms (FR1), ~15 ms (FR2)
- T_RACH (RACH-based): ~10 ms additional
- T_RACH (RACH-less): 0 ms
- T_PDCCH_acquisition: ~few ms

**Target total**: 20~30 ms (RACH-less), 40~50 ms (RACH-based)

This is a 50%+ reduction compared with the existing L3 HO (50~100 ms).

#### 6.2.2 Interruption Time

User plane (PDCCH/PDSCH) interruption duration:
- LTM RACH-less: ≤ 15 ms (FR1)
- LTM RACH-based: ≤ 30 ms (FR1)
- These are quantified in 38.133

### 6.3 Measurement Capability Requirements

The UE must perform source-cell measurements and candidate-cell measurements simultaneously:
- Same frequency: no additional burden
- Different frequency (intra-band): minor impact
- Different frequency (inter-band): measurement gap may be used

### 6.4 Number of Candidate Cells

Number of candidate cells the UE can monitor simultaneously:
- Minimum 4 cells
- 8 or 16 depending on UE capability `maxNumberCandidateCellsLTM-r18`

### 6.5 Test Configuration Example (38.133)

| Parameter | Value |
|---|---|
| Source cell SS-RSRP | -90 dBm |
| Candidate cell A SS-RSRP | -85 dBm (5 dB stronger) |
| Cell switch trigger | MAC-CE at T = T0 |
| Required: T_total | < 30 ms (RACH-less) |
| Pass criterion | UE acquires PDCCH on target by T0 + 30 ms |

---

## 7. 38.306 — UE Capability

### 7.1 LTM Capability Fields

```
ltm-r18: ENUMERATED { supported }
ltm-IntraDU-r18: ENUMERATED { supported }
ltm-InterDU-r18: ENUMERATED { supported }  -- optional, separate
ltm-RACHless-r18: ENUMERATED { supported }
ltm-MAC-CE-r18: ENUMERATED { supported }
ltm-DCI-r18: ENUMERATED { supported }
maxNumberCandidateCellsLTM-r18: ENUMERATED { n4, n8, n16 }
maxNumberCandidateConfigsLTM-r18: ENUMERATED { n8, n16, n32 }
```

### 7.2 Per-Band Capability

The UE reports the following per band:
- `ltm-Supported-FR1` / `ltm-Supported-FR2`
- `ltm-MeasurementCapability`: number of candidates that can be measured simultaneously
- `ltm-CellSwitchInterruptionTime`: switching time category

### 7.3 Cross-Capability Conditions

Use of LTM requires the following accompanying capabilities:
- `unifiedTCI-StateMode-r17` (depends on Rel.17 unified TCI)
- `tciState-r17` (DL/UL unified TCI)
- `bwp-Operation` (BWP switching capability)

---

## 8. Rel.19 — LTM Extensions

### 8.1 Motivation (WID: NR_Mob_enh_Ph5, RP-234041 / RP-242630, etc.)

Rel.18 LTM was a first step limited to intra-CU. Rel.19 extends in the following directions:

1. **Inter-CU LTM**: Fast cell switch between different gNB-CUs
2. **SCG LTM**: Apply LTM to the Secondary Cell Group
3. **Conditional LTM (CLTM)**: Hybrid of CHO and LTM — UE triggers autonomously
4. **AI/ML-based LTM trigger**: Proactive LTM based on measurement prediction

### 8.2 38.331 Extensions

```asn1
-- Rel.19 working draft
LTM-Configuration-r19 ::= SEQUENCE {
    interCU-Support-r19         BOOLEAN,
    candidateCellInfoSCG-r19    SEQUENCE OF CandidateCellInfo-LTM-SCG-r19  OPTIONAL,
    conditionalLTM-r19          ConditionalLTM-Config-r19  OPTIONAL,
    ...
}

ConditionalLTM-Config-r19 ::= SEQUENCE {
    triggerCondition-r19    SEQUENCE {
        l1RsrpThreshold-r19     RSRP-Range,
        timeToTrigger-r19       INTEGER (0..1024)  -- in ms
    },
    autoExecute-r19         BOOLEAN
}
```

### 8.3 38.321 Extensions

- **Inter-CU LTM MAC-CE**: Accompanies a context transfer procedure between source CU and target CU
- **Conditional LTM MAC-CE**: UE autonomously switches cells when a condition is met (similar to CHO but at the L1/L2 level)

### 8.4 38.214 Extensions

L1 measurement extensions:
- **AI/ML-aided measurement prediction**: Predict candidate cell quality from partial measurements
- **Reduced measurement overhead**: Subset measurement

### 8.5 38.133 Extensions

- Inter-CU LTM latency requirements (typical 30~50 ms)
- SCG LTM latency
- Trigger evaluation time for Conditional LTM

### 8.6 38.306 Extensions

```
ltm-InterCU-r19
ltm-SCG-r19
ltm-Conditional-r19
ltm-AIAssisted-r19
```

---

## 9. Rel.20 — LTM Direction of Evolution

### 9.1 Rel.20 SI/WI Progress (As of the Time of Writing)

LTM-related work that is ongoing or candidate in Rel.20:

1. **Multi-RAT LTM**: NR-DC, NR-LTE inter-RAT LTM
2. **NTN LTM**: LTM in satellite environments (considering large propagation delay)
3. **Group-based LTM**: Multiple UEs cell-switch together (V2X, IIoT scenarios)
4. **LTM with full AI/ML**: Fully autonomous prediction-based LTM

### 9.2 Potential RRC Extensions (TBD)

```asn1
-- Rel.20 candidates (not finalized)
LTM-Configuration-r20 ::= SEQUENCE {
    interRAT-LTM-r20            ENUMERATED { supported, notSupported }  OPTIONAL,
    ntn-LTM-r20                 NTN-LTM-Config-r20  OPTIONAL,
    groupLTM-r20                Group-LTM-Config-r20  OPTIONAL,
    aiml-LTM-r20                AI-ML-LTM-Config-r20  OPTIONAL,
    ...
}
```

### 9.3 NTN-Environment Specifics

LTM in NTN (Non-Terrestrial Network) requires special considerations:
- The satellite moves quickly, so the source cell itself changes rapidly
- Large rate of TA change → RACH-less LTM is more attractive
- Doppler shift compensation must be integrated into the LTM procedure

---

## 10. Cross-Document Linkages

### 10.1 LTM End-to-End Flow and Document Mapping

```
[Phase 0: Setup]
   ┌────────────────────────────────────────┐
   │ 38.300 §9.2:                            │
   │ Architecture, intra/inter-DU defs       │
   │ Source ↔ Target relationship defined    │
   └─────────────────────┬──────────────────┘
                         │
   ┌─────────────────────▼──────────────────┐
   │ 38.331:                                 │
   │ - CandidateCellInfoListCPC-LTM-r18      │
   │ - LTM-CandidateConfig (RACH, TA, TCI)   │
   │ - candidateCellMeasConfigLTM-r18        │
   │ - candidateCellSwitchTriggerConfig-r18  │
   └─────────────────────┬──────────────────┘
                         │ Pre-configuration done
                         │
[Phase 1: Measurement]   │
                         ▼
   ┌────────────────────────────────────────┐
   │ 38.214 §5.1.6, §5.2:                    │
   │ - Candidate cell SSB/CSI-RS L1 meas.    │
   │ - Reports such as cri-RSRP-Index-r18    │
   │ - Per-cell, per-beam L1-RSRP            │
   └─────────────────────┬──────────────────┘
                         │
   ┌─────────────────────▼──────────────────┐
   │ 38.133 §9.x:                            │
   │ - Measurement period (T_LTM_meas)       │
   │ - Accuracy ±6/±9 dB                     │
   └─────────────────────┬──────────────────┘
                         │
[Phase 2: Trigger]       │
                         ▼
   ┌────────────────────────────────────────┐
   │ 38.321:                                 │
   │ - LTM Cell Switch MAC-CE                │
   │ - Candidate config ID, TCI ID, BWP ID   │
   │ - Trigger handling → cell switch begins │
   └─────────────────────┬──────────────────┘
                         │
[Phase 3: Execution]     │
                         ▼
   ┌────────────────────────────────────────┐
   │ 38.321 + 38.214 + 38.211:               │
   │ - Apply target cell PHY config          │
   │ - TCI activation (Unified TCI)          │
   │ - BWP switch                            │
   │ - RACH (optional) or RACH-less          │
   └─────────────────────┬──────────────────┘
                         │
   ┌─────────────────────▼──────────────────┐
   │ 38.133:                                 │
   │ - Verify T_apply, T_total requirements  │
   │ - Interruption time bound               │
   └─────────────────────┬──────────────────┘
                         │
[Phase 4: Capability     │
         Validation]     │
                         ▼
   ┌────────────────────────────────────────┐
   │ 38.306:                                 │
   │ - UE declares LTM support              │
   │ - Number of candidates, switching class │
   └────────────────────────────────────────┘
```

### 10.2 Key Consistency Matrix

| Item | 38.300 | 38.331 | 38.321 | 38.214 | 38.133 | 38.306 |
|---|---|---|---|---|---|---|
| Candidate cell definition | concept | CandidateCellInfo IE | (consumes) | meas config | meas requirement | maxNumberCandidate |
| Cell switch trigger | concept | triggerMethod (mac-CE/dci) | MAC-CE format | — | latency req | trigger support |
| Pre-config TA | concept | timingAdjustmentLTM | (consumes) | — | TA accuracy | RACH-less support |
| TCI application | TCI framework | tciStateList | Unified TCI activation | TCI-state | TCI activation latency | unifiedTCI-StateMode |
| L1 measurement | concept | measResource | (handles reporting) | report quantity | meas period | L1 measurement |
| Interruption time | concept | cellSwitchTimer | timer handling | — | bound definition | interruption class |

### 10.3 Dependency Tree

```
LTM (Rel.18)
  │
  ├─[depends on]─ Unified TCI Framework (Rel.17)
  │                  └─ TCI-State, MAC-CE activation
  │
  ├─[depends on]─ BWP Operation (Rel.15)
  │                  └─ BWP switching mechanism
  │
  ├─[depends on]─ Beam Management (Rel.15+)
  │                  └─ L1-RSRP measurement, reporting
  │
  ├─[extends]──── Conditional Handover (Rel.16)
  │                  └─ pre-configuration concept
  │
  └─[interacts with]─ BFR (Rel.15+)
                       └─ Beam failure → potential LTM trigger
```

### 10.4 Rel.18 → Rel.19 → Rel.20 Evolution Matrix

| Aspect | Rel.18 (Initial LTM) | Rel.19 (Extended) | Rel.20 (Future) |
|---|---|---|---|
| **Scope (38.300)** | Intra-CU (intra/inter-DU) | + Inter-CU, SCG | + Inter-RAT, NTN, Group |
| **RRC (38.331)** | CandidateCellInfoListCPC-LTM | + ConditionalLTM-Config, SCG candidate | + NTN-LTM, Group-LTM |
| **MAC-CE (38.321)** | LTM Cell Switch MAC CE | + Inter-CU MAC CE, Conditional LTM | + AI-driven MAC CE |
| **L1 Meas (38.214)** | Per-cell L1-RSRP | + AI/ML-aided prediction | + Full AI inference |
| **RRM (38.133)** | Intra-DU latency requirements | + Inter-CU, SCG latency | + NTN, group latency |
| **Capability (38.306)** | ltm-IntraDU, ltm-RACHless | + ltm-InterCU, ltm-Conditional | + ltm-AIML, ltm-NTN |

### 10.5 Concrete Execution Scenario (Example: FR2 RACH-less LTM)

```
T = -1000 ms: Source cell sends RRC Reconfiguration to UE
              - Candidate Cell A, B, C info (PCI, frequency, SSB, ...)
              - LTM-CandidateConfig (TA pre-config, TCI, BWP)
              - candidateCellMeasConfigLTM activated

T = -500 ms ~ T = 0 ms: UE measures candidate cells L1-RSRP
              - Cell A: -100 dBm
              - Cell B: -85 dBm (best)
              - Cell C: -110 dBm
              - Reports cri-RSRP-Index-r18 over PUCCH/PUSCH

T = 0 ms: gNB sends LTM Cell Switch MAC CE
          - Candidate Config ID = 2 (Cell B)
          - TCI State ID = 5
          - BWP ID = 1
          - Type = RACH-less

T = 1 ms: UE sends MAC-CE HARQ ACK

T = 5 ms: UE begins applying the LTM procedure
          - Stop source cell PHY
          - Apply target cell B's PHY config (TCI 5, BWP 1)
          - Apply timingAdjustmentLTM (TA = -25 samples, etc.)

T = 12 ms: UE begins PDCCH monitoring on target cell B

T = 18 ms: First PDCCH received (DCI on target cell)
=> Total = 18 ms < 30 ms (38.133 spec for RACH-less LTM) ✓
=> Interruption time = 12 ms < 15 ms ✓
```

---

## 11. Conclusion

### 11.1 Standardization Significance of LTM

LTM represents an architectural transformation in NR mobility:

1. **L3 → L1/L2 Mobility**: Reduces cell-change latency by 50%+
2. **Pre-configuration paradigm**: Shifts the burden of dynamic decision-making to RRC-level pre-processing
3. **Beam-cell unified management**: Integrates beam and cell management on top of the TCI framework
4. **Foundation for future enhancements**: Becomes the base for AI/ML mobility and NTN mobility

### 11.2 Cross-Document Design Philosophy

LTM is not defined in a single document; it is a model example of **cross-layer design**:

- Concept (38.300) → RRC config (38.331) → MAC procedure (38.321) → PHY measurement (38.214) → RRM bound (38.133) → Capability (38.306)
- Each layer carries clear responsibility and a well-defined interface, and consistency across layers is guaranteed at the spec level.

### 11.3 Future Evolution

As we move into Rel.19/20:
- **Spatial scope expansion**: intra-CU → inter-CU → inter-RAT → NTN
- **Enhanced intelligence**: rule-based → AI/ML-predicted
- **Group operation**: per-UE → per-group (V2X, IIoT)

These evolutions all extend the **"pre-configure + L1/L2 trigger"** paradigm established by Rel.18 LTM.

---

*Document references: TS 38.300 v18.x, TS 38.331 v18.x, TS 38.321 v18.x, TS 38.214 v18.x, TS 38.133 v18.x, TS 38.306 v18.x, RP-234037, RP-234041*

*Note: This report reflects the situation at the time of writing (April 2026), where Rel.18 is frozen, Rel.19 is at the frozen or finalization stage, and Rel.20 is undergoing SI/WI. The detailed Rel.19/20 spec contents may change at the time of final publication.*
