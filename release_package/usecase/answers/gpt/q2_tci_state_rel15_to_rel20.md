# Summary of TCI-state related standardization items from Rel.15 to Rel.20

> This document is a first-pass analysis of TCI-state related features from Rel.15 to Rel.20, focused on cross-document linkages, from the perspective of WID motivation, the QCL assumption in 38.214, the MAC CE procedures in 38.321, the RRC parameters in 38.331, and UE capability in 38.306.
> Rel.20 is still an ongoing area, so it is described not as frozen normative behavior but as an extension direction based on disclosed scope and draft CRs.

---

## 1. The essence of TCI-state

A TCI-state, in simple terms, is a state that tells you **"by which reference signal's beam/QCL relationship should this PDSCH/PDCCH/CSI-RS/UL transmission be interpreted"**.

QCL — quasi co-location — means that, between two antenna ports, the channel properties of one port can be used to estimate the channel properties of another port.

QCL types can be roughly understood as follows.

| QCL type | Included channel properties |
|---|---|
| Type A | Doppler shift, Doppler spread, average delay, delay spread |
| Type B | Doppler shift, Doppler spread |
| Type C | Doppler shift, average delay |
| Type D | spatial Rx parameter |

From a beam management standpoint, **QCL Type D** is particularly important. Type D is connected to which receive beam or spatial filter the UE should use.

---

## 2. Cross-document structure

```text
38.331
  Configures TCI-State / dl-OrJointTCI-StateList / ul-TCI-StateList
      ↓
38.321
  Activates/deactivates TCI states or maps DCI codepoints via MAC CE
      ↓
38.214
  UE applies the QCL assumption per the DCI's TCI field or default rules
      ↓
38.306
  UE reports as capability the supported number of TCI states, active TCI count, and unified TCI features
```

The key point is the following.

```text
RRC lays out the candidates.
MAC CE picks which of those candidates to actually activate.
DCI indicates which of the activated candidates applies to this transmission.
PHY applies the QCL assumption of that TCI-state.
UE capability sets the upper bound on this entire configuration.
```

---

## 3. Big-picture flow per release

| Release | Standard item viewpoint | 38.214 QCL/TCI | 38.321 MAC CE | 38.331 RRC parameters | 38.306 UE capability |
|---|---|---|---|---|---|
| Rel.15 | NR initial access/beam management baseline | Introduction of TCI-state and QCL assumption for PDSCH/PDCCH/CSI-RS | PDSCH TCI activation/deactivation, PDCCH TCI indication | `TCI-State`, `PDSCH-Config.tci-StatesToAddModList`, CORESET/search space related TCI | Number of configured TCI states, active TCI per BWP/CC |
| Rel.16 | MIMO/multi-TRP enhancement | Extension supporting application of multiple TCI states in single-DCI multi-TRP, etc. | Enhanced PDSCH TCI activation, multi-TRP related TCI mapping | simultaneous TCI update list, serving-cell common/group activation | multi-TRP/multi-TCI capability |
| Rel.17 | Unified TCI | Unifies DL TCI and UL spatial relation under a unified framework | unified TCI states activation/deactivation MAC CE | `dl-OrJointTCI-StateList`, `ul-TCI-StateList`, `unifiedTCI-StateType` | joint/separate unified TCI support |
| Rel.18 | Enhanced unified TCI, LTM coupling, advanced multi-TRP | DCI 1_1/1_2/1_3, joint/separate TCI, coupled with candidate-cell TCI | enhanced unified TCI, LTM cell switch, candidate cell TCI, BFD-RS indication | LTM candidate TCI, Rel.18 unified TCI capability extensions | multi-active TCI, CJT, per-CORESETPoolIndex, etc. |
| Rel.19 | LTM/CLTM and inter-cell beam management extensions | candidate TCI, CLTM, extended serving/candidate cell beam assumptions | Enhanced LTM, candidate cell TCI, CLTM-related procedures | CLTM/LTM candidate cells and conditional configuration | CLTM, enhanced mobility, eType-II/CJT, etc. capability extensions |
| Rel.20 | Ongoing. Mobility enhancement phase 4, additional LTM/CLTM extensions | Cannot yet be treated as frozen spec | conditional LTM, SCell activation, DC/inter-CU related extensions under discussion | Direction of extending conditional mobility/LTM candidate configuration | Rel.20 capability is fluid until final spec freeze |

---

## 4. Rel.15 baseline TCI

In Rel.15, TCI-state was the core of NR beam-based operation. RRC configures multiple TCI-states, MAC CE activates a subset of them, and the TCI field in DCI specifies which QCL assumption to apply when actually receiving PDSCH.

The flow is as follows.

```text
RRC: Configure n TCI-State candidates
  ↓
MAC CE: Map the active subset to DCI codepoints
  ↓
DCI: Indicate one codepoint
  ↓
PHY: Apply QCL Type A/B/C/D of the corresponding TCI-State
```

The basic Rel.15 structure is as follows.

| Document | Role |
|---|---|
| 38.331 | `TCI-State`, `PDSCH-Config.tci-StatesToAddModList`, CORESET-related TCI configuration |
| 38.321 | PDSCH TCI states activation/deactivation MAC CE |
| 38.214 | Apply QCL assumption based on the DCI TCI field or default TCI state during PDSCH reception |
| 38.306 | Reports capability for configured/active TCI state count and QCL Type-D |

The core purpose of Rel.15 TCI is **to indicate the PDSCH/PDCCH reception beam unambiguously and stably support beamformed NR operation**.

---

## 5. Rel.16: multi-TRP and enhanced TCI activation

In Rel.16, multi-TRP operation became important. In particular, in single-DCI multi-TRP, a single DCI must control PDSCH transmissions coming from multiple TRPs, so a structure that indicates only one TCI-state is no longer sufficient.

Summarized:

```text
Rel.15
  DCI codepoint → 1 TCI-state

Rel.16 multi-TRP
  DCI codepoint → TCI-state pair or multiple TCI states
  → Enables single-DCI multi-TRP PDSCH reception
```

The implications of the Rel.16 TCI extension are as follows.

| Item | Meaning |
|---|---|
| multi-TRP | Multiple TRPs transmit to the same UE |
| single-DCI multi-TRP | A single DCI controls transmissions across multiple TRPs |
| Multiple TCI-states | To distinguish per-TRP beam/QCL assumptions |
| Enhanced TCI activation | MAC CE extension to support mapping a DCI codepoint to multiple TCI-states |

The cross-document linkage is as follows.

```text
38.331
  Configure TCI candidates required for multi-TRP
      ↓
38.321
  Map codepoints to TCI pairs via the enhanced TCI activation MAC CE
      ↓
38.214
  Apply multiple TCI-states/QCL assumptions when receiving PDSCH
      ↓
38.306
  UE reports capability for multi-TRP / multi-TCI processing
```

---

## 6. Rel.17: Unified TCI

The important change in Rel.17 is **bundling DL beam indication and UL spatial relation under a unified TCI framework**.

Previously, the structure was roughly as follows.

```text
Previous:
  DL: TCI-State
  UL: spatial relation / SRS resource indicator and other separate structures
```

Under Rel.17 unified TCI, the following structure becomes possible.

```text
Rel.17:
  joint TCI: indicates DL beam and UL spatial filter together
  separate TCI: indicates DL TCI and UL TCI separately
```

In other words, unified TCI extends beam indication from a DL-centric form to a DL/UL common or separate structure.

| Document | Rel.17 unified TCI role |
|---|---|
| 38.331 | Configures `dl-OrJointTCI-StateList`, `ul-TCI-StateList`, `unifiedTCI-StateType`, etc. |
| 38.321 | unified TCI states activation/deactivation MAC CE |
| 38.214 | Application of joint/separate TCI, interpretation of DL QCL and UL spatial filter |
| 38.306 | Capability reporting for joint/separate unified TCI |

The benefit of this structure is the following.

```text
If DL beam management and UL spatial filter management are separated
  → Configuration/activation/signaling becomes complex

By introducing Unified TCI
  → DL/UL beam indications are unified under a consistent TCI framework
  → Beam-update efficiency improves in multi-TRP, FR2, and mobility environments
```

---

## 7. Rel.18: enhanced unified TCI, LTM, candidate-cell TCI

In Rel.18, unified TCI is connected to more complex mobility/multi-TRP situations.

In particular, with the introduction of LTM — L1/L2 Triggered Mobility — TCI-state goes beyond simple serving-cell beam indication and now covers **what beam/QCL assumption to apply when moving to a candidate target cell**.

Rel.18 features are as follows.

| Item | Meaning |
|---|---|
| Enhanced unified TCI | Couples joint/separate TCI structures with a wider variety of DCI/MAC CE structures |
| Multiple active TCI | Direction of handling multiple active beams/TCIs simultaneously |
| LTM candidate TCI | Pre-prepares the TCI-state to be used at a candidate target cell |
| Candidate cell TCI indication | Indicates the TCI of target/candidate cells via MAC CE |
| BFD-RS indication | Refined relationship between beam-failure-detection resources and TCI |

The document linkage is as follows.

```text
38.331
  Configure LTM candidate cell configuration and candidate TCI-state
      ↓
38.321
  LTM Cell Switch Command / Candidate Cell TCI State Indication MAC CE
      ↓
38.214
  Apply QCL assumption based on CandidateTCI-State or indicated TCI when LTM switches occur
      ↓
38.306
  Capability reporting for LTM, unified TCI, and multiple active TCI
```

The core of Rel.18 is that **TCI-state begins to be directly coupled with mobility execution**.

---

## 8. Rel.19: LTM/CLTM and inter-cell beam management extensions

In Rel.19, the structure of Rel.18 LTM is extended further. CLTM — Conditional LTM — is particularly important.

Rel.18 LTM is roughly the following structure.

```text
RRC prepares candidate config
  ↓
gNB issues a cell switch command via MAC CE
  ↓
UE quickly switches to the target cell
```

Rel.19 CLTM is closer to the following structure.

```text
RRC prepares candidate config and execution conditions
  ↓
UE evaluates conditions
  ↓
When the conditions are met, the UE executes lower-layer mobility
```

From the TCI-state viewpoint, the following items matter.

| Item | Meaning |
|---|---|
| Candidate cell TCI | Beam/QCL assumption to be used at the target candidate cell |
| CLTM condition | Trigger the switch when specific measurement conditions are met |
| Serving/candidate beam management | Manage serving and candidate cell beams simultaneously |
| Inter-cell beam management | Process beam transitions across cells more quickly at lower layers |
| CJT/multi-TRP coupling | Coordinated joint transmission and TCI extensions |

The document linkage is as follows.

```text
38.331
  Configure CLTM candidate config, conditions, and candidate TCI
      ↓
38.214
  Candidate cell measurement and QCL/TCI assumption
      ↓
38.321
  LTM/Enhanced LTM/Candidate Cell TCI related MAC CE
      ↓
38.306
  Capability reporting for CLTM, enhanced mobility, and candidate beam/TCI
```

---

## 9. Rel.20: ongoing extension directions

Since Rel.20 is still an ongoing area, it must not be written as if it were a finalized standard. However, based on the disclosed scope and draft CR direction, the following extensions are anticipated.

| Extension direction | Need |
|---|---|
| Mobility enhancement phase 4 | Improve coverage and robustness of Rel.18/19 LTM/CLTM |
| Additional improvements to lower-layer triggered mobility | Further reduce RRC handover latency |
| Coupling with SCell activation | Reduce SCell activation delay in CA environments |
| DC/inter-CU LTM | Extend LTM into dual-connectivity or inter-CU environments |
| Conditional LTM RRM requirements | Clarify delay and reliability requirements for UE-triggered mobility |
| Post-processing of RACH-based conditional LTM | Resolve issues around TCI state, MAC state, and RRC state cleanup after a switch |

In Rel.20, TCI-state is likely to be extended beyond simple beam indication into **a lower-layer control state coupled with mobility, candidate cells, SCell activation, and DC architecture**.

---

## 10. Final summary

```text
Rel.15 beam/QCL baseline
  → Rel.16 multi-TRP
  → Rel.17 unified TCI
  → Rel.18 enhanced unified TCI + LTM candidate TCI
  → Rel.19 CLTM/inter-cell beam management
  → Rel.20 mobility enhancement phase 4

38.331 configures TCI candidates
  → 38.321 MAC CE activation/mapping
  → 38.214 applies QCL assumption
  → 38.306 reports capability
```

TCI-state has evolved over releases as follows.

```text
Rel.15: DL beam/QCL indication
Rel.16: Multi-TRP multiple TCI
Rel.17: DL/UL unified TCI
Rel.18: LTM candidate-cell TCI coupled with mobility
Rel.19: CLTM/inter-cell beam management extensions
Rel.20: Lower-layer mobility, expanding into SCell/DC/inter-CU
```

---

## References

- 3GPP TS 38.214: Physical layer procedures for data
- 3GPP TS 38.321: Medium Access Control protocol specification
- 3GPP TS 38.331: Radio Resource Control protocol specification
- 3GPP TS 38.306: UE radio access capabilities
- 3GPP TS 38.300: NR overall description
- 5G Americas, 5G Advanced / 3GPP release overview materials
- Qualcomm, 3GPP Release 19/20 overview materials
