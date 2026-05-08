# Summary of Rel.18 LTM (L1/L2 Triggered Mobility) standardization items

> This document organizes Rel.18 LTM, L1/L2 Triggered Mobility, from the perspective of 38.300, 38.331, 38.321, 38.214, 38.133, and 38.306, and explains the cross-document linkages, including extension directions in Rel.19/Rel.20, as a first-pass analysis.
> Since Rel.20 is still ongoing, it is not described as final frozen normative behavior but as a directional summary based on disclosed scope and draft CRs.

---

## 1. Motivation

The conventional handover is RRC-based.

```text
Measurement report
  ↓
Network handover decision
  ↓
RRCReconfiguration
  ↓
UE synchronizes with the target cell
  ↓
RACH
  ↓
RRCReconfigurationComplete
```

This structure is reliable but has large interruption time. In particular, in high-speed mobility, FR2, small-cell, and dense deployments, handover latency becomes a performance bottleneck.

The purpose of Rel.18 LTM is to **prepare target/candidate cell configurations in advance**, and at the actual switching moment to **execute the cell switch quickly via lower-layer signaling such as MAC CE**.

---

## 2. The core concepts of LTM

```text
RRC phase
  Provides the candidate cell configuration to the UE in advance

Preparation phase
  Prepares candidate TCI states, CSI-RS/SSB resources, early DL sync, and optional early UL TA

Execution phase
  Indicates target configuration ID / TCI / TA / NCC, etc., via MAC CE

Completion phase
  Completes target-cell access via RACH or RACH-less
```

LTM is not a complete replacement for the conventional handover; it is closer to **a structure that pushes the execution part of handover into the lower layers**.

That is:

```text
Conventional HO:
  RRC performs the bulk of the procedure at the switching point

LTM:
  RRC prepares candidate configurations in advance
  MAC CE quickly triggers the switch
```

---

## 3. Cross-document structure

```text
38.300
  Describes the LTM concept and the overall procedure
      ↓
38.331
  RRC configuration related to LTM candidate cell configuration, candidate TCI, CSI resources, and early sync
      ↓
38.214
  Candidate cell L1 measurement/reporting and application of TCI/QCL assumption
      ↓
38.321
  LTM Cell Switch Command MAC CE, Enhanced LTM MAC CE, Candidate Cell TCI MAC CE
      ↓
38.133
  Mobility interruption time and RRM requirements
      ↓
38.306
  UE reports as capability whether it supports LTM, early sync, candidate cells/beams/reporting
```

The key point is the following.

```text
38.331 installs the "possible target candidates" on the UE in advance.
38.321 MAC CE indicates "switch to this candidate now".
38.214 defines which TCI/QCL/measurement assumption to apply at that moment.
38.133 specifies how fast and how reliably the switch must occur.
38.306 sets the upper bound of how far the UE can support this.
```

---

## 4. 38.300: LTM concepts and procedures

The intra-gNB LTM procedure in 38.300 can be summarized as follows.

```text
1. UE transmits an L3 measurement report
2. The serving gNB chooses candidate target cells
3. RRCReconfiguration provides the candidate cell configuration
4. UE stores the candidate configuration
5. UE performs early DL sync for the candidate cell
6. If needed, performs early UL sync / acquires TA
7. UE performs L1 measurement reporting
8. gNB sends a MAC CE cell switch command
9. UE applies the target configuration ID, TCI, TA, etc.
10. RACH-less if a valid TA exists; otherwise RACH-based access
11. UE completes via RRCReconfigurationComplete or UL data
```

The important concepts in 38.300 are the following.

| Concept | Meaning |
|---|---|
| Candidate cell configuration | The RRC configuration for the target candidate cells |
| Early DL sync | Securing DL timing/sync for the candidate cell in advance |
| Early UL sync | Securing the target UL timing or TA in advance |
| RACH-less LTM | Cell switch without random access if a valid TA exists |
| RACH-based LTM | Random access is performed if there is no valid TA or it is needed |
| L1 measurement report | Uses candidate cell quality for lower-layer decision-making |
| Cell Switch Command | The MAC CE that actually triggers the switch |

The essence of LTM is **preparing candidates in advance and executing them quickly via MAC CE**.

---

## 5. 38.331: RRC parameters

In 38.331, the LTM-related RRC parameters serve the role of pre-installing candidate configurations on the UE.

| RRC IE/parameter | Role |
|---|---|
| `LTM-Config` | The container for the entire LTM configuration |
| `LTM-CandidateConfig` | The RRCReconfiguration candidate per candidate cell |
| Candidate cell PCI | Identifies the candidate target cell |
| Early UL sync config | Settings for quickly aligning UL timing with the target cell |
| no-reset / TA-related ID | Controls related to MAC reset and TA preservation/reuse |
| LTM CSI resource config | CSI-RS/SSB resources used for candidate cell L1 measurement/reporting |
| `LTM-TCI-Info` | TCI information to apply at LTM activation/cell switch |
| Candidate TCI state | Beam/QCL assumption to use at the target/candidate cell |

The RRC configuration as a procedure looks like this.

```text
RRCReconfiguration
  ↓
Provide LTM-Config
  ↓
Store per-candidate-cell configuration
  ↓
Configure CSI-RS/SSB resources for candidate cell measurement
  ↓
Configure candidate TCI states
  ↓
Provide settings that enable early DL/UL sync
```

In other words, 38.331 takes care of the **preparation phase** of LTM.

---

## 6. 38.321: MAC CE behavior

38.321 contains the LTM Cell Switch Command MAC CE and the Enhanced LTM Cell Switch Command MAC CE.

The MAC CE is the execution trigger and conveys the following information.

| MAC CE information | Meaning |
|---|---|
| Target configuration ID | Which of the candidates pre-provided by RRC to switch to |
| Candidate TCI state | Beam/QCL assumption to use at the target/candidate cell |
| TA or TA-related information | Whether RACH-less is possible and the UL timing |
| NCC/security-related information | Security context for the target switch |
| RACH/RACH-less indicator | Whether random access is required |
| SR configuration | UL control procedure right after the switch |
| Lower-layer TCI information | Beam/TCI information to be applied immediately after the switch |

The MAC CE-based execution flow is as follows.

```text
1. The UE has already stored the LTM candidate config via RRC
2. gNB sends the MAC CE Cell Switch Command
3. The UE reads the target configuration ID
4. Applies the corresponding candidate config
5. Applies the indicated TCI/TA/NCC information
6. RACH-less switch if a valid TA exists
7. RACH-based switch if there is no valid TA
8. After the switch, completes via UL data or RRCReconfigurationComplete
```

The role of 38.321 is to take care of the **LTM execution phase**.

---

## 7. 38.214: L1 measurement and reporting

In LTM, the UE must perform L1 measurements for the target/candidate cells. The measurement targets are typically the candidate cell's SSB or CSI-RS, and L1-RSRP reporting is used in the cell-switch decision.

From the 38.214 perspective, the following is important.

```text
Candidate cell CSI-RS/SSB measurement
  ↓
L1-RSRP report
  ↓
gNB decides the MAC CE cell switch command
  ↓
The UE applies the QCL assumption based on CandidateTCI-State or the indicated TCI
```

The important roles in 38.214 are as follows.

| Item | Meaning |
|---|---|
| L1-RSRP measurement | Measures candidate cell/beam quality |
| CSI-RS/SSB-based measurement | Evaluates beam quality of target/candidate cells |
| TCI/QCL assumption | Which beam/spatial assumption to apply during the switch |
| CandidateTCI-State | TCI to be used at the target/candidate cell during LTM cell switch |
| Relationship with DCI/MAC CE TCI indication | Determines the PDCCH/PDSCH reception assumption right after the switch |

In other words, 38.214 covers the **PHY behavior of measurements and beam assumptions** in LTM.

---

## 8. 38.133: RRM requirements

The performance crux of LTM is **reducing the mobility interruption time**.

The performance requirements are linked to the following items.

| Item | Meaning |
|---|---|
| Mobility interruption time | The time during which DL/UL data is interrupted during the cell switch |
| Early DL sync availability | Whether the target cell DL timing can be aligned in advance |
| Early UL sync / TA validity | Whether RACH-less switch is possible |
| L1 measurement/reporting latency | Speed of judging target quality before the MAC CE trigger |
| RACH-based vs RACH-less | Differences in interruption depending on access method |
| Processing time | Time the UE needs from MAC CE reception until target config is applied |

The difference between conventional handover and LTM is the following.

```text
Conventional RRC handover:
  Interruption arises from RRC signaling + synchronization + RACH + completion

LTM:
  RRC preparation is done in advance
  Execution is performed quickly via MAC CE and lower-layer sync
  If a valid TA exists, RACH-less further reduces interruption
```

Therefore, the LTM-related RRM requirements in 38.133 are linked to **switching time, measurement time, sync preparation status, and conditions for RACH-less**.

---

## 9. 38.306: UE capability

LTM imposes a heavy implementation burden on the UE. While maintaining the serving cell, the UE must also handle candidate cell measurements, candidate TCI, early sync, TA, and possibly RACH-less switching.

Therefore, capability includes items such as the following.

| Capability category | Meaning |
|---|---|
| Number of supported LTM candidate cells | How many candidate cell configurations can be stored/managed |
| Number of supported candidate beams/TCIs | Number of beam candidates per candidate cell |
| L1 measurement/reporting capability | Level of L1-RSRP reporting support for LTM |
| Early DL sync capability | Whether target cell sync can be performed in advance |
| Early UL sync capability | Whether target cell UL timing/TA can be prepared in advance |
| RACH-less LTM capability | Whether RACH-less switches based on a valid TA are supported |
| CLTM capability | Whether Rel.19 conditional LTM is supported |

The capability linkage is as follows.

```text
If UE does not support LTM capability
  → gNB must not provide LTM candidate config

If UE has a limit on the number of candidate cells
  → The number of LTM-CandidateConfig entries in RRC must remain within capability

If UE does not support RACH-less
  → gNB must focus configuration on RACH-based LTM

If UE does not support early UL sync
  → TA-based fast switch procedures must be restricted
```

In other words, 38.306 sets, in LTM, **the upper bound on the feature scope the network can configure**.

---

## 10. Rel.19 extension: CLTM

One of the central extensions in Rel.19 is **CLTM, Conditional LTM**.

Existing Rel.18 LTM is closer to a structure where the gNB indicates "switch to the target now" via MAC CE. CLTM moves toward UE evaluating conditions received via RRC and, when those conditions are met, executing the cell switch through lower-layer procedures.

```text
Rel.18 LTM:
  RRC prepares candidate config
  gNB MAC CE issues the cell switch command
  UE switches to the target cell

Rel.19 CLTM:
  RRC prepares candidate config + execution conditions
  UE evaluates L1/L3 conditions
  When conditions are met, UE switches to the target cell
```

The CLTM procedure can be summarized as follows.

```text
1. RRC provides the CLTM candidate configuration and execution conditions
2. UE stores the configuration and starts evaluating the conditions
3. Early DL sync may be performed
4. When the L1/L3 condition is satisfied, the UE switches to the target cell
5. RACH-less is possible if a valid TA exists
6. CFRA/CBRA or other RACH-based access if no valid TA exists
7. In CLTM, no LTM MAC CE is needed; the UE executes when the condition is met
8. MAC reset is performed at execution
```

The differences between Rel.18 LTM and Rel.19 CLTM are as follows.

| Item | Rel.18 LTM | Rel.19 CLTM |
|---|---|---|
| Execution trigger | gNB MAC CE cell switch command | UE executes when conditions are met |
| Candidate configuration | RRC preconfiguration | RRC conditional configuration |
| Measurement | Based on L1/L3 measurement | L1/L3 condition evaluation |
| RACH-less | Possible if a valid TA exists | Possible if a valid TA exists |
| MAC CE | Core execution trigger | LTM MAC CE not needed for CLTM execution |
| Purpose | Fast network-controlled mobility | Faster conditional lower-layer mobility |

The reasons why this extended procedure was needed in Rel.19:

```text
If gNB has to indicate the switch timing every time via MAC CE
  → Signaling delay and scheduling dependency exist

If the UE evaluates conditions and executes itself
  → Faster mobility is possible
  → Interruption can be reduced in high-speed mobility / FR2 / small-cell environments
```

---

## 11. Rel.20 extension directions

Since Rel.20 is still ongoing, it must not be described as definitive normative spec. However, based on the disclosed scope and draft CRs, the following directions are visible.

| Extension direction | Need |
|---|---|
| Additional improvements to lower-layer triggered mobility | Improve interruption time and robustness of LTM/CLTM |
| Coupling SCell activation with LTM | Reduce activation delay not just for the serving cell but also for secondary cells in CA/DC environments |
| DC/inter-CU LTM | Extend LTM applicability into multi-node, inter-gNB, inter-CU mobility |
| Refining conditional LTM RRM requirements | Clarify how quickly and reliably the UE must judge condition satisfaction and switch delay |
| Cleanup of RACH-based conditional LTM state | Resolve cleanup of activated TCI state, candidate state, MAC/RRC state after a switch |
| Mobility enhancement phase 4 | Improve coverage and stability of the Rel.18/19 mobility features |

The Rel.20 direction summarized in one line:

```text
Rel.18 LTM:
  Network-controlled lower-layer cell switch

Rel.19 CLTM:
  Condition-based UE-triggered lower-layer cell switch

Rel.20:
  Extension of lower-layer mobility into more complex deployments such as CA/DC/inter-CU/SCell activation
```

---

## 12. Final summary

```text
Latency problem of conventional RRC handover
  → Rel.18 LTM: RRC preconfiguration + MAC CE cell switch
  → 38.300 covers the concept/procedure
  → 38.331 configures candidate config/TCI/CSI resources
  → 38.321 handles LTM MAC CE execution
  → 38.214 handles L1 measurement/reporting and QCL/TCI assumptions
  → 38.133 specifies interruption/RRM requirements
  → 38.306 specifies UE capability
  → Rel.19 CLTM: UE-triggered lower-layer mobility when conditions are met
  → Rel.20: extends to SCell/DC/inter-CU/conditional LTM performance
```

The core idea of LTM is **prepare handover via RRC in advance, and execute it quickly at L1/L2**. As we move into Rel.19/20, this structure expands from network-controlled LTM to conditional/UE-triggered mobility, and into CA/DC/inter-CU environments.

---

## References

- 3GPP TS 38.300: NR overall description
- 3GPP TS 38.331: Radio Resource Control protocol specification
- 3GPP TS 38.321: Medium Access Control protocol specification
- 3GPP TS 38.214: Physical layer procedures for data
- 3GPP TS 38.133: Requirements for support of radio resource management
- 3GPP TS 38.306: UE radio access capabilities
- Qualcomm, 3GPP Release 19/20 overview materials
