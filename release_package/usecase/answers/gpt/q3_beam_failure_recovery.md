# Summary of standard procedures for Beam Failure Detection and Beam Failure Recovery

> This document is a first-pass analysis of Beam Failure Detection and Beam Failure Recovery procedures, focused on cross-document linkages, from the perspective of motivation, related parameters, the behavior in 38.213/38.321/38.331, and the performance requirements in 38.133/38.533.

---

## 1. Motivation and need

In NR, especially in FR2/mmWave, beam-based transmission and reception is essential. However, the quality of the serving beam can degrade rapidly due to UE rotation, hand blockage, mobility, blockage, TRP switching, etc.

In such situations, if one waits all the way to RLF and then performs RRC re-establishment or handover, the interruption becomes large.

Therefore, BFD/BFR has the following purpose.

```text
Detect beam-quality degradation quickly at L1/MAC
  ↓
Search for candidate beams before RLF
  ↓
Request recovery via PRACH or MAC CE/SR
  ↓
Restore PDCCH/PDSCH/PUCCH/PUSCH operation on the new beam
```

In other words, BFD/BFR is **a procedure that prevents beam-level failures from escalating into cell-level failures**.

---

## 2. Cross-document structure

```text
38.331
  Configures BFD resources, candidate beams, thresholds, timers, and the recovery search space
      ↓
38.213
  Defines which RS the UE uses as BFD RS q0 and candidate RS q1, and how L1 link quality is evaluated
      ↓
38.321
  MAC counts the lower-layer BFI indications and triggers BFR based on timer/maxCount
      ↓
38.213
  For SpCell, performs PRACH-based link recovery and monitors recoverySearchSpaceId
      ↓
38.321
  For SCell, sends BFR MAC CE / truncated BFR MAC CE or SR
      ↓
38.133 / 38.533
  BFD/CBD evaluation time, scheduling restriction, conformance test
```

The key point is the following.

```text
38.331 provides the parameters.
38.213 defines how L1 decides on beam failure and candidate beam.
38.321 manages the BFI counter and recovery trigger at MAC.
38.133 specifies how quickly the UE must decide.
38.533 verifies that requirement through tests.
```

---

## 3. 38.331: main RRC parameters

The RRC parameters related to BFD/BFR are mostly split into those for **failure detection** and those for **recovery**.

---

### 3.1 Beam failure detection side

| Parameter | Meaning |
|---|---|
| `failureDetectionResourcesToAddModList` | RS list used for BFD. CSI-RS or SSB based |
| `failureDetectionResourcesToReleaseList` | Release of BFD resources |
| `failureDetectionSet1`, `failureDetectionSet2` | Distinguishes BFD resource sets |
| `beamFailureInstanceMaxCount` | How many accumulated lower-layer beam failure instances trigger BFR |
| `beamFailureDetectionTimer` | Timer to reset the BFI counter |
| `rlmInSyncOutOfSyncThreshold` | Threshold family used for Qout/Qin decisions |

In plain words:

```text
failureDetectionResources
  → Reference signals used to monitor whether the current beam has failed

beamFailureInstanceMaxCount
  → How many consecutive/accumulated bad evaluations are needed to declare beam failure

beamFailureDetectionTimer
  → If BFI does not accumulate enough within this period, the counter is reset
```

---

### 3.2 Beam failure recovery side

| Parameter | Meaning |
|---|---|
| `candidateBeamRSList` | List of candidate beam RSs for recovery |
| `rsrp-ThresholdSSB` | Threshold for SSB candidate beams |
| `rsrp-ThresholdBFR` | Threshold for BFR candidate beams |
| `recoverySearchSpaceId` | Search space the UE monitors for PDCCH after recovery |
| `beamFailureRecoveryTimer` | Validity timer for the BFR procedure |
| `rach-ConfigBFR` | RACH configuration for BFR |
| `ssb-perRACH-Occasion` | Mapping between SSBs and RACH occasions |
| `ra-ssb-OccasionMaskIndex` | RACH occasion mask |
| `schedulingRequestID-BFR` | SR ID linked when SR is used in SCell BFR |

In plain words:

```text
candidateBeamRSList
  → List of candidate beams that can be used for recovery

rsrp-ThresholdBFR
  → Minimum quality required to be considered a candidate beam

recoverySearchSpaceId
  → PDCCH search space where the gNB response is searched after the recovery request

rach-ConfigBFR
  → PRACH configuration used in SpCell BFR

schedulingRequestID-BFR
  → SR configuration used to obtain a transmission opportunity for the BFR MAC CE in SCell BFR
```

---

## 4. 38.213: L1 behavior

38.213 defines the PHY layer decision criteria for BFD/BFR.

The UE configures a BFD RS set `q0`. If RRC explicitly configures the BFD RS, that is used; otherwise the default BFD RS can be derived from the QCL Type-D RS of the active TCI-State, etc.

The candidate beam RS set `q1` is the RS set used to find recovery candidate beams.

```text
q0: RS set used to check whether the current serving beam/link has failed
q1: RS set used to find recovery candidate beams
Qout_LR: out-of-sync threshold from a link-recovery perspective
Qin_LR: in-sync/candidate threshold from a link-recovery perspective
```

The L1 procedure can be written as follows.

```text
1. The UE measures q0 RSs.
2. If the link quality of q0 is worse than Qout_LR, lower layers indicate BFI to MAC.
3. The UE measures q1 RSs to find candidate beams.
4. If a candidate beam's quality is above the threshold, it is selected as a recovery candidate.
5. For SpCell, PRACH-based link recovery is performed.
6. After recovery, the UE monitors PDCCH on the search space indicated by recoverySearchSpaceId.
```

---

## 5. 38.321: MAC procedure

38.321 defines how MAC handles a beam failure instance indication, i.e., a BFI raised from lower layers.

MAC uses the following parameters.

| MAC variable/parameter | Meaning |
|---|---|
| `BFI_COUNTER` | Cumulative beam failure instance counter |
| `beamFailureInstanceMaxCount` | When the counter reaches this value, BFR is triggered |
| `beamFailureDetectionTimer` | Timer to reset the BFI counter |
| `beamFailureRecoveryTimer` | Timer for the recovery procedure |
| Candidate beam information | Which beam to use for the recovery request |

The MAC procedure can be understood as follows.

```text
1. Lower layer delivers BFI to MAC
2. MAC increments BFI_COUNTER
3. beamFailureDetectionTimer starts/restarts
4. If BFI_COUNTER >= beamFailureInstanceMaxCount, BFR is triggered
5. If a candidate beam exists, the recovery procedure is performed
6. Different recovery paths are used for SpCell and SCell
```

---

## 6. Difference between SpCell BFR and SCell BFR

The recovery method differs between SpCell and SCell.

| Target | Recovery method |
|---|---|
| SpCell, i.e., PCell/PSCell | PRACH-based BFR. Monitors recoverySearchSpaceId |
| SCell | BFR MAC CE, truncated BFR MAC CE, or SR-based notification |

### 6.1 SpCell BFR

Since SpCell is PCell or PSCell, when failure occurs the control connection itself is at risk. Therefore, recovery is performed via PRACH.

```text
SpCell beam failure
  ↓
Select a candidate beam
  ↓
Transmit BFR PRACH preamble/resource
  ↓
Monitor PDCCH on recoverySearchSpaceId
  ↓
Receive gNB response and recover the beam
```

### 6.2 SCell BFR

Since SCell is a secondary cell, while the PCell control connection is alive, BFR information can be sent via MAC CE.

```text
SCell beam failure
  ↓
Select a candidate beam
  ↓
Trigger BFR MAC CE or truncated BFR MAC CE
  ↓
Trigger SR if needed
  ↓
Deliver BFR information to the gNB through PCell/PUCCH/PUSCH
```

In other words, SpCell BFR has a strong **connection-recovery flavor**, while SCell BFR has a stronger **secondary-cell beam status reporting/recovery request flavor**.

---

## 7. Summary of main parameters

| Parameter | Document | Meaning |
|---|---|---|
| `failureDetectionResourcesToAddModList` | 38.331 | RS list used for BFD |
| `beamFailureInstanceMaxCount` | 38.331/38.321 | Triggers BFR when the BFI counter reaches this value |
| `beamFailureDetectionTimer` | 38.331/38.321 | Timer that resets the BFI counter |
| `candidateBeamRSList` | 38.331 | RS list used to measure recovery candidate beams |
| `rsrp-ThresholdBFR` | 38.331/38.213 | Threshold for accepting a candidate beam |
| `recoverySearchSpaceId` | 38.331/38.213 | Search space to monitor the response PDCCH after BFR |
| `beamFailureRecoveryTimer` | 38.331/38.321 | BFR procedure validity timer |
| `rach-ConfigBFR` | 38.331 | RACH configuration for SpCell BFR |
| `schedulingRequestID-BFR` | 38.331/38.321 | Used for SR triggering in SCell BFR |
| `q0` | 38.213 | Beam-failure-detection RS set |
| `q1` | 38.213 | Candidate beam RS set |
| `Qout_LR` | 38.213/38.133 | Link-recovery out-of-sync threshold |
| `Qin_LR` | 38.213/38.133 | Candidate/in-sync threshold |

---

## 8. 38.133: RRM requirements

38.133 is the RRM requirement document and defines the timing requirements for BFD and candidate beam detection.

The performance requirements are roughly grouped as follows.

| Requirement category | Meaning |
|---|---|
| BFD evaluation time | Time allowed for the UE to decide that the serving beam has failed |
| Candidate beam detection time | Time allowed for the UE to find a recovery candidate beam |
| FR1/FR2 distinction | Differences in requirements depending on frequency range |
| SSB/CSI-RS-based distinction | Differences depending on whether the BFD RS is SSB or CSI-RS |
| DRX/non-DRX distinction | Differences in evaluation period depending on DRX behavior |
| Measurement restriction | Requirements when measurement-occasion restrictions apply |
| Scheduling restriction | Restrictions when PDSCH/PDCCH scheduling conditions are imposed |

In other words, 38.133 does not say "BFD/BFR procedures must exist"; it defines **how quickly the UE must decide on beam failure and candidate beam under given conditions**.

---

## 9. 38.533: Conformance test

38.533 is the document that verifies the RRM requirements of 38.133 through actual tests.

BFD/BFR-related tests roughly verify the following.

| Test category | Verification content |
|---|---|
| SSB-based BFD | SSB-based BFD/link recovery performance |
| CSI-RS-based BFD | CSI-RS-based BFD/link recovery performance |
| FR1/FR2 | BFD/BFR performance per band |
| DRX/non-DRX | BFD/BFR performance under DRX conditions |
| SpCell BFR | PCell/PSCell recovery procedure |
| SCell BFR | SCell BFR procedure based on MAC CE/SR |
| Candidate beam detection | Whether candidate beams are searched and meet the threshold |

The linkage is as follows.

```text
38.133
  Within how many ms must the UE decide on beam failure and candidate beam

38.533
  How that requirement is verified in a test-equipment environment
```

---

## 10. Final summary

```text
Beam blockage / beam degradation
  → 38.331 configures BFD RSs, candidate RSs, thresholds, and timers
  → 38.213 defines L1 decisions based on q0/q1 and Qout/Qin
  → 38.321 manages the BFI counter and BFR trigger
  → SpCell uses PRACH recovery, SCell uses BFR MAC CE/SR
  → 38.133/38.533 verify detection/recovery performance
```

BFD/BFR is **an L1/MAC/RRC-combined procedure for quickly detecting beam-level failures during NR beam operation and recovering them before they escalate into cell-level RLF**.

---

## References

- 3GPP TS 38.213: Physical layer procedures for control
- 3GPP TS 38.321: Medium Access Control protocol specification
- 3GPP TS 38.331: Radio Resource Control protocol specification
- 3GPP TS 38.133: Requirements for support of radio resource management
- 3GPP TS 38.533: NR User Equipment conformance specification; RRM
