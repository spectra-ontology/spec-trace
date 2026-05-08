# NR Beam Failure Detection (BFD) and Beam Failure Recovery (BFR) Standard Analysis Report

## Table of Contents
1. [Motivation and Need](#1-motivation-and-need)
2. [Core Concepts and Behavioral Overview](#2-core-concepts-and-behavioral-overview)
3. [38.213 — Physical Layer Behavior](#3-38213--physical-layer-behavior)
4. [38.321 — MAC Layer Procedures](#4-38321--mac-layer-procedures)
5. [38.331 — RRC Parameters](#5-38331--rrc-parameters)
6. [38.133 / 38.533 — UE Performance Requirements](#6-38133--38533--ue-performance-requirements)
7. [Per-Release Evolution](#7-per-release-evolution)
8. [Cross-Document Linkages](#8-cross-document-linkages)

---

## 1. Motivation and Need

### 1.1 Beam Blockage Problems in the NR FR2 Environment

NR is the first cellular standard to fully exploit mmWave bands (FR2: 24.25 ~ 52.6 GHz; FR2-2: ~71 GHz). Characteristics of these bands:

- **High path loss**: Free-space loss is 20+ dB higher than below 6 GHz → narrow beam transmission is essential
- **Sensitivity to blockage**: Tens of dB of instantaneous attenuation can occur due to a person's body, hand, vehicle, building, etc.
- **Dynamic environment**: The best beam changes rapidly due to UE rotation, movement, blocker passage, etc.

In such an environment, when the **currently used beam suddenly becomes invalid**, the conventional path is RLF (Radio Link Failure) → RRC re-establishment → connection drop, which is a heavy procedure. This is highly inefficient with respect to latency and throughput.

### 1.2 Need for Introduction

Two core requirements:

1. **Fast detection**: Detect beam invalidation on the order of milliseconds
2. **Fast recovery without RLF**: Recover quickly with a new beam without RRC reconfiguration

To address these, the **Beam Failure Recovery (BFR)** procedure was introduced from NR Rel.15. The core idea:

- The UE **continuously monitors the quality of the beam carrying the PDCCH**
- After a certain number of consecutive failures, **it sends a SCell-specific BFR request to the gNB**
- The gNB responds with a new beam → the same RRC state is maintained

### 1.3 Evolution Phases (Brief)

| Release | Main evolution |
|---|---|
| Rel.15 | Introduces PCell BFR (CFRA-based) |
| Rel.16 | Introduces SCell BFR (MAC-CE-based) and L1-RSRP-based candidate evaluation |
| Rel.17 | Unified BFR framework, BFR extensions in multi-TRP environments, multi-panel BFR |

Detailed evolution is covered in §7 of this report.

---

## 2. Core Concepts and Behavioral Overview

### 2.1 BFD-RS and Candidate Beam RS

The BFR procedure uses two kinds of RS sets:

#### (1) Beam Failure Detection RS (BFD-RS)
- Monitors the spatial QCL source RS (Type D) of the current PDCCH
- Beam failure is decided based on the L1 measurement of this RS
- RRC `failureDetectionResources` or implicit derivation

#### (2) Candidate Beam RS (CB-RS, q_1 set)
- The set of RSs that become candidates for the new beam upon beam failure
- Configured by the RRC `candidateBeamRSList`
- Evaluated based on L1-RSRP; beams above a threshold are selected and reported

### 2.2 The Four Phases of the BFR Procedure

```
   ┌──────────────────────────────┐
   │  Step 1: Beam Failure        │
   │  Instance Detection          │
   │  (PHY: 38.213)               │
   └──────────────┬───────────────┘
                  │ BFI indication
                  ▼
   ┌──────────────────────────────┐
   │  Step 2: Beam Failure        │
   │  Declaration                 │
   │  (MAC: 38.321)               │
   │  - Counter accumulation,     │
   │    timer management          │
   └──────────────┬───────────────┘
                  │ Failure declared
                  ▼
   ┌──────────────────────────────┐
   │  Step 3: Candidate Beam      │
   │  Identification              │
   │  (PHY+MAC)                   │
   └──────────────┬───────────────┘
                  │ Candidate selected
                  ▼
   ┌──────────────────────────────┐
   │  Step 4: BFRQ Transmission   │
   │  & gNB Response              │
   │  (CFRA / MAC-CE / DCI)       │
   └──────────────────────────────┘
```

---

## 3. 38.213 — Physical Layer Behavior

### 3.1 Beam Failure Instance (BFI) Detection — Clause 6

#### 3.1.1 Measurement Targets

The UE measures the L1 quality of the following RSs:
- The RS specified in the RRC `failureDetectionResources` (NZP-CSI-RS or SSB), **OR**
- If no explicit list exists, RSs derived from the TCI-state of all active CORESETs (QCL Type D source)

NR Rel.15: up to 2 RSs, Rel.16+: up to 64 RSs (BFD-RS list)

#### 3.1.2 Evaluation Criterion: Hypothetical BLER

The UE computes a **hypothetical PDCCH BLER** from the measured channel/noise estimates:

$$\text{BLER}_{\text{hypothetical}} = f(\text{SINR}_{\text{est}}, \text{PDCCH config})$$

Here, the PDCCH config assumes worst-case parameters (e.g., Aggregation Level 8; specific assumptions in Rel.15).

#### 3.1.3 Beam Failure Instance Decision

- If **BLER_hypothetical > Q_out_LR (e.g., 10%)**, a BFI is generated and indicated to the MAC layer
- The evaluation period T_evaluate_BFD equals the periodicity of the BFD-RS (typical: 5~40 ms)

### 3.2 Candidate Beam Identification — Clause 6

#### 3.2.1 Evaluation Targets

L1-RSRP measurements of the RSs defined in `candidateBeamRSList` (the q_1 set).

#### 3.2.2 Threshold

The RRC parameter `rsrp-ThresholdSSB` or `rsrp-ThresholdBFR` (typical: -110 dBm)

#### 3.2.3 Candidate Selection

Among the RSs whose L1-RSRP > threshold, **the RS index of the best RS** is indicated to the MAC layer.

### 3.3 BFRQ Transmission (Beam Failure Recovery Request)

#### Rel.15: PRACH-based BFRQ
- Uses a dedicated CFRA (Contention-Free Random Access) preamble
- Monitors the PDCCH corresponding to `recoverySearchSpaceId` of `BeamFailureRecoveryConfig` for the response

#### Rel.16: MAC-CE-based BFRQ (SCell)
- Upon SCell failure, transmits a MAC-CE on the PCell's PUSCH
- MAC-CE: `BFR MAC CE` (LCID 47 or fixed)

### 3.4 Recovery Response Window (38.213 Clause 9)

After transmitting the BFRQ, the UE monitors the PDCCH (DCI 1_0 with RA-RNTI or C-RNTI) during the following window:

$$\text{Window} = \text{BeamFailureRecoveryTimer} \text{ slots}$$

If the response is received within this window, recovery is successful. If not received, the BFRQ is retried or RLF is declared.

---

## 4. 38.321 — MAC Layer Procedures

### 4.1 PCell BFR (Rel.15) — Clause 5.17

#### 4.1.1 Variables and Counters

| Variable | Meaning | RRC configuration | Default behavior |
|---|---|---|---|
| BFI_COUNTER | Cumulative BFI count | (none, counter) | +1 per BFI |
| beamFailureInstanceMaxCount | Failure declaration threshold | RRC | 1, 2, 3, 4, 5, 6, 8, 10 |
| beamFailureDetectionTimer | BFI counter reset timer | RRC | pbfd1, pbfd2, ... pbfd10 (in slots) |

#### 4.1.2 Procedure

```
On receiving BFI indication from lower layers:
1. BFI_COUNTER += 1
2. Start/restart beamFailureDetectionTimer
3. IF BFI_COUNTER >= beamFailureInstanceMaxCount:
       Declare beam failure
       Start BFR procedure (random access for SpCell)

On beamFailureDetectionTimer expiry:
1. BFI_COUNTER = 0
```

#### 4.1.3 BFR Initiation (PCell)

- Trigger RA procedure (Random Access)
- Evaluate candidates with `candidateBeamRSList` inside `beamFailureRecoveryConfig`
- Send BFRQ via the PRACH preamble of the suitable beam
- Monitor PDCCH for the duration of `beamFailureRecoveryTimer`
- On timer expiry → fall back to ordinary RA

### 4.2 SCell BFR (Rel.16) — Clause 5.17.2

Unlike PCell BFR, since **PRACH may not exist on the SCell**, a MAC-CE-based procedure is used.

#### 4.2.1 BFR MAC CE Format (Truncated/Full BFR MAC CE)

```
| C7 | C6 | C5 | C4 | C3 | C2 | C1 | C0 |   ← octet 1: failed cell bitmap (excluding PCell, 0~7)
| AC | R  | Candidate RS ID (6 bits)    |   ← octet 2: per-cell candidate
...
```

- `C_i = 1`: beam failure on SCell i
- `AC = 1`: the candidate beam ID is valid
- `Candidate RS ID`: 6 bits → identifies up to 64 candidate RSs

#### 4.2.2 SCell BFR Procedure

```
1. Accumulate BFI_COUNTER_i on SCell i
2. BFI_COUNTER_i >= beamFailureInstanceMaxCount → declare SCell i failure
3. Trigger BFR for SCell i (request UL grant)
4. Compose the BFR MAC CE:
   - Set the C_i bit
   - Evaluate the candidate beam and include the RS ID
5. Transmit the BFR MAC CE on PUSCH (via PCell or anchor SCell)
6. Receive gNB response (BFR application confirmed via PDCCH)
```

#### 4.2.3 Truncated vs Full

- **Truncated BFR MAC CE** (LCID 47): Used when the UL grant is too small to include all SCell information
- **Full BFR MAC CE** (LCID 48): All 8 SCells possible

### 4.3 SR for BFR

When BFR is initiated without a UL grant, a **dedicated SR (Scheduling Request) for BFR** is used:
- `schedulingRequestId-BFR-r16` (RRC)
- When BFR occurs, the SR is transmitted immediately → gNB provides a UL grant

### 4.4 Recovery Success Conditions (38.321)

The BFR procedure terminates when the following conditions are met:
- **PCell**: A C-RNTI-scrambled DCI is received in the search space corresponding to `recoverySearchSpaceId`
- **SCell**: PDCCH for the corresponding SCell is received, or an explicit BFR confirm

---

## 5. 38.331 — RRC Parameters

### 5.1 BeamFailureRecoveryConfig (for PCell)

```asn1
BeamFailureRecoveryConfig ::= SEQUENCE {
    rootSequenceIndex-BFR           INTEGER (0..137)  OPTIONAL,
    rach-ConfigBFR                  RACH-ConfigGeneric  OPTIONAL,
    rsrp-ThresholdSSB               RSRP-Range  OPTIONAL,
    candidateBeamRSList             SEQUENCE (SIZE(1..maxNrofCandidateBeams)) OF PRACH-ResourceDedicatedBFR  OPTIONAL,
    ssb-perRACH-Occasion            ENUMERATED {oneEighth, oneFourth, oneHalf, one, two, four, eight, sixteen}  OPTIONAL,
    ra-ssb-OccasionMaskIndex        INTEGER (0..15)  OPTIONAL,
    recoverySearchSpaceId           SearchSpaceId  OPTIONAL,
    ra-Prioritization               RA-Prioritization  OPTIONAL,
    beamFailureRecoveryTimer        ENUMERATED {ms10, ms20, ms40, ms60, ms80, ms100, ms150, ms200}  OPTIONAL,
    msg1-SubcarrierSpacing          SubcarrierSpacing  OPTIONAL,
    ...
}
```

Meanings of key parameters:
- **`candidateBeamRSList`**: The q_1 set, the targets for measuring candidate beams during recovery
- **`rsrp-ThresholdSSB`**: Threshold for selecting candidates
- **`recoverySearchSpaceId`**: Search space monitored for the BFR response PDCCH
- **`beamFailureRecoveryTimer`**: Timer for waiting for the BFR response

### 5.2 BeamFailureRecoverySCellConfig (Rel.16, for SCell)

```asn1
BeamFailureRecoverySCellConfig-r16 ::= SEQUENCE {
    rsrp-ThresholdBFR-r16                    RSRP-Range  OPTIONAL,
    candidateBeamRSSCellList-r16             SEQUENCE (SIZE(1..maxNrofCandidateBeams-r16)) OF CandidateBeamRS-r16  OPTIONAL,
    beamFailureRecoveryTimer-r16             ENUMERATED {ms10, ms20, ms40, ms60, ms80, ms100, ms150, ms200}  OPTIONAL,
    ...
}

CandidateBeamRS-r16 ::= SEQUENCE {
    candidateBeamConfig-r16   CHOICE {
        ssb-r16        SSB-Index,
        csi-RS-r16     NZP-CSI-RS-ResourceId
    },
    servCellId                ServCellIndex  OPTIONAL  -- RSs from other cells are allowed
}
```

### 5.3 RadioLinkMonitoringConfig (BFD-RS Configuration)

```asn1
RadioLinkMonitoringConfig ::= SEQUENCE {
    failureDetectionResourcesToAddModList   SEQUENCE OF RadioLinkMonitoringRS  OPTIONAL,
    failureDetectionResourcesToReleaseList  SEQUENCE OF RadioLinkMonitoringRS-Id  OPTIONAL,
    beamFailureInstanceMaxCount             ENUMERATED {n1, n2, n3, n4, n5, n6, n8, n10}  OPTIONAL,
    beamFailureDetectionTimer               ENUMERATED {pbfd1, pbfd2, pbfd3, pbfd4, pbfd5, pbfd6, pbfd8, pbfd10}  OPTIONAL
}

RadioLinkMonitoringRS ::= SEQUENCE {
    radioLinkMonitoringRS-Id    RadioLinkMonitoringRS-Id,
    purpose                     ENUMERATED {beamFailure, rlf, both},
    detectionResource           CHOICE {
        ssb-Index   SSB-Index,
        csi-RS-Index NZP-CSI-RS-ResourceId
    }
}
```

Key points:
- **`purpose`**: The same RS can be used for both BFD and RLF detection
- Maximum number of RSs: Rel.15 = 2, Rel.16+ = up to 8 or more

### 5.4 SchedulingRequestResourceConfig with BFR

```asn1
SchedulingRequestResourceConfig ::= SEQUENCE {
    ...,
    schedulingRequestId         SchedulingRequestId,
    ...
}

-- BFR-dedicated SR
SchedulingRequestConfig ::= SEQUENCE {
    schedulingRequestToAddModList SEQUENCE OF SchedulingRequestToAddMod  OPTIONAL,
    ...
}
```

`schedulingRequestId-BFR-SCell-r16` is defined separately for SCell BFR.

---

## 6. 38.133 / 38.533 — UE Performance Requirements

### 6.1 38.133 — RRM Requirements

#### 6.1.1 BFD Performance (Clause 8.5)

The UE must detect a BFI within the following time:

$$T_{\text{Evaluate\_BFD\_SSB}} = \max(T_{\text{DRX}}, M \cdot T_{\text{SSB}})$$

where:
- T_SSB: SSB periodicity (typical 20 ms)
- M: implementation factor (1 or 5, depending on conditions)

#### 6.1.2 Candidate Beam Evaluation Time (Clause 8.5.4)

Time from L1-RSRP measurement until a suitable beam is identified:

$$T_{\text{search}} = \max(T_{\text{DRX}}, M_2 \cdot T_{\text{measurement period}})$$

#### 6.1.3 SCell BFR Recovery Time

Total time to complete the BFR procedure (Clause 8.5.x):
- BFI detection ~ candidate identification: as above
- BFRQ transmission ~ gNB response reception: scheduling-dependent
- Total typical: **tens of ms ~ within 100 ms**

#### 6.1.4 Test Configuration Example

| Parameter | Value |
|---|---|
| Cell A SS-RSRP | -100 dBm (BFD-RS source) |
| Cell A degrades to | -130 dBm (failure) |
| Candidate beam B SS-RSRP | -100 dBm |
| Threshold | -110 dBm |
| Required: T_recovery | < 80 ms (typical FR2) |

### 6.2 38.533 — Conformance Test

The RRM requirements of 38.133 are concretized in 38.533 as **conformance test cases**.

#### 6.2.1 BFD Test Case (Around 38.533 Clause 7.6)

Test purpose: Verify that the UE can accumulate BFIs within the defined time → declare beam failure.

```
Test setup:
- gNB attenuates the PCell main beam (CSI-RS 1) to -130 dBm
- Transmits a candidate beam (SSB B) at -100 dBm
- Time measured: from the attenuation moment to when the UE transmits the PRACH/MAC-CE BFRQ
- Pass criterion: T < specified bound
```

#### 6.2.2 SCell BFR Test Case

- BFI occurs on SCell → BFR MAC CE transmitted via PCell
- Measured: from SCell failure occurrence to MAC CE transmission to gNB confirmation

#### 6.2.3 False Alarm Test

The UE must not falsely declare BFR for a normal beam:
- Under good BFD-RS quality (-100 dBm), BFR must not occur for at least 90% of the time

### 6.3 Key RRM Parameters (Quantitative Reference)

Typical values per 38.133:

| Parameter | Value | Applies to |
|---|---|---|
| Q_out_LR (BLER threshold) | 10% | BFI determination |
| L1-RSRP threshold | -110 dBm (default) | Candidate selection |
| beamFailureInstanceMaxCount | 1~10 (RRC), typically 3 | Failure declaration |
| beamFailureDetectionTimer | 1~10 × evaluation period | Counter reset |
| beamFailureRecoveryTimer | 10~200 ms | Response wait |

---

## 7. Per-Release Evolution

### 7.1 Rel.15 — PCell BFR (Initial)

- **Scope**: PCell only
- **Mechanism**: PRACH-based CFRA
- **Limitation**: Failure on SCell risks immediate escalation to RLF

### 7.2 Rel.16 — SCell BFR

WID: RP-201305 (NR_eMIMO_2 / Mobility enhancements)

- **Scope**: PCell + SCell
- **New mechanism**: MAC-CE-based BFR for SCell
- **New items**:
  - BFR MAC CE (LCID 47, 48)
  - `BeamFailureRecoverySCellConfig`
  - SR-BFR resource

### 7.3 Rel.17 — Multi-TRP BFR + Unified BFR

WID: RP-211583 (FeMIMO)

- **Multi-TRP BFR**: Partial BFR when only one of two TRP beams fails
  - `failureDetectionSet1-r17`, `failureDetectionSet2-r17`
  - Per-TRP BFR MAC-CE
- **Unified BFR**: Integration with the Unified TCI framework
  - In a Joint TCI environment, BFR updates DL+UL beams simultaneously

### 7.4 Rel.18 — Multi-Panel BFR

WID: RP-234037

- **Multi-panel UE**: Switch to another panel when one panel fails
- **Per-panel BFD-RS, candidate beam**
- Coupling with LTM: BFR can be used as an LTM cell-switch trigger

---

## 8. Cross-Document Linkages

### 8.1 Procedure Flow and Document Mapping

```
[Phase 1: Detection]
   ┌─────────────────────────────────┐
   │ 38.213 §6:                       │
   │ - BFD-RS measurement             │
   │ - Hypothetical BLER computation  │
   │ - On BFI, MAC indication         │
   └────────────────┬────────────────┘
                    │
   ┌────────────────▼────────────────┐
   │ 38.321 §5.17:                    │
   │ - BFI_COUNTER management         │
   │ - beamFailureDetectionTimer      │
   │ - Declare failure on threshold   │
   └────────────────┬────────────────┘
                    │
[Phase 2: Recovery]│
                    ▼
   ┌─────────────────────────────────┐
   │ 38.213 §9:                       │
   │ - candidateBeamRS L1-RSRP meas.  │
   │ - Identify RSs above threshold   │
   └────────────────┬────────────────┘
                    │
   ┌────────────────▼────────────────┐
   │ 38.321 §5.17 / §5.4:             │
   │ - PCell: RA procedure            │
   │ - SCell: BFR MAC CE + SR-BFR     │
   └────────────────┬────────────────┘
                    │
   ┌────────────────▼────────────────┐
   │ 38.213 §10:                      │
   │ - BFR response window            │
   │ - recoverySearchSpaceId monitor  │
   └────────────────┬────────────────┘
                    │
[Phase 3: Validation]
                    ▼
   ┌─────────────────────────────────┐
   │ 38.133 §8.5 / 38.533 §7.6:       │
   │ - Time/Latency requirements      │
   │ - Conformance test               │
   └─────────────────────────────────┘
```

### 8.2 RRC ↔ MAC ↔ PHY ↔ RRM Consistency

| Item | 38.331 (RRC) | 38.321 (MAC) | 38.213 (PHY) | 38.133 (RRM) |
|---|---|---|---|---|
| BFD-RS configuration | `failureDetectionResourcesToAddModList` | (consumes) | Measurement target | Measurement-time requirements |
| Failure threshold | `beamFailureInstanceMaxCount` | BFI_COUNTER comparison | (BFI trigger) | — |
| Counter reset | `beamFailureDetectionTimer` | Timer management | — | Timer accuracy |
| Candidate RS | `candidateBeamRSList` | Candidate selection | L1-RSRP measurement | Evaluation time |
| RSRP threshold | `rsrp-ThresholdSSB` | Comparison | Threshold comparison | Measurement accuracy |
| Recovery search space | `recoverySearchSpaceId` | (consumes) | PDCCH monitoring | — |
| Response timer | `beamFailureRecoveryTimer` | Timer management | Window determination | Total recovery time |
| SCell BFR MAC-CE | LCID 47/48 (indirect) | Format definition | (UL transmission) | Total time |
| SR-BFR | `schedulingRequestId-BFR` | SR trigger | PUCCH SR resource | SR latency |

### 8.3 Key Consistency Checkpoints

#### Checkpoint 1: BFD-RS Consistency
- Specified in 38.331 `failureDetectionResources` (or applies the implicit derivation rule)
- 38.213 measures the BLER on the same RS
- 38.133 timing requirements are based on the same RS periodicity

#### Checkpoint 2: Counter/Timer Matching
- `beamFailureInstanceMaxCount` (e.g., n3) in 38.331 RRC
- 38.321 MAC declares failure when exactly n3 BFIs accumulate
- 38.213 PHY indicates per BFI detection cycle

#### Checkpoint 3: Recovery Response Verification
- 38.331 `recoverySearchSpaceId` defines the location of the response PDCCH
- 38.213 monitors PDCCH on that SearchSpace
- 38.321 ends the procedure on response reception

#### Checkpoint 4: Latency Budget
- 38.213 evaluation period (e.g., M × T_SSB)
- + 38.321 counter accumulation time
- + 38.213 BFRQ transmission + response window
- = 38.133 total recovery time requirement

The sum of all of the above must remain within the bound specified in 38.133 (e.g., 80 ms for FR2).

### 8.4 Concrete Execution Scenario (Example: FR2 PCell BFR)

```
T = 0 ms:    PCell BFD-RS (CSI-RS) signal degrades to -130 dBm
T = 5 ms:    UE detects the first BFI (38.213 §6, BLER > 10%)
T = 5 ms:    BFI_COUNTER = 1, beamFailureDetectionTimer starts (38.321)
T = 25 ms:   2nd BFI, COUNTER = 2
T = 45 ms:   3rd BFI, COUNTER = 3 = beamFailureInstanceMaxCount
             → Beam failure declared (38.321 §5.17)
T = 45 ms:   Begin candidate beam evaluation (38.213 §9)
T = 50 ms:   Candidate SSB B (-100 dBm > threshold) selected
T = 50 ms:   Transmit PRACH preamble (RA procedure)
T = 60 ms:   Receive PDCCH on recoverySearchSpaceId (gNB response)
T = 60 ms:   BFR procedure completed (38.321)
=> Total: 60 ms < 80 ms (38.133 spec) ✓
```

---

## 9. Conclusion

The NR Beam Failure Detection/Recovery procedure carries the following significance:

1. **Avoids RLF**: Recovers a beam on the order of milliseconds without the heavy procedure of RRC re-establishment
2. **Layered integrated design**: PHY measurement → MAC procedure → RRC config are tightly combined
3. **Per-release evolution**: Scope expands from PCell only → SCell → Multi-TRP → Multi-panel
4. **Operability in FR2**: Solves the most prominent FR2 weakness — blockage — at the cellular spec level

In particular, BFR forms the foundation for follow-on mobility technologies such as LTM (L1/L2 Triggered Mobility), and is evolving into proactive BFR with AI/ML-based beam prediction (Rel.19+).

---

*Document references: TS 38.213, TS 38.321, TS 38.331, TS 38.133, TS 38.533 (Rel.15 ~ Rel.18), RP-170739, RP-201305, RP-211583, RP-234037*
