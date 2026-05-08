# Q4 — Rel-18 LTM (Layer-1/Layer-2 Triggered Mobility) and Rel-19/20 Extensions: Standards Item Analysis Report

## Table of Contents
1. [Motivation (Rel-18 WI Perspective and Rel-19/20 Direction)](#1-motivation-rel-18-wi-perspective-and-rel-1920-direction)
2. [38.300 — LTM Procedure (Architecture and C-Plane Flow)](#2-38300--ltm-procedure-architecture-and-c-plane-flow)
3. [38.331 — RRC: LTM-Config / Candidate Cell / L3-Trigger](#3-38331--rrc-ltm-config--candidate-cell--l3-trigger)
4. [38.321 — MAC: LTM Cell Switch and Candidate-TCI Activation MAC CEs](#4-38321--mac-ltm-cell-switch-and-candidate-tci-activation-mac-ces)
5. [38.214 — Candidate-Cell L1 Measurement and Reporting](#5-38214--candidate-cell-l1-measurement-and-reporting)
6. [38.133 — LTM Cell-Switch Delay and RRM Tests](#6-38133--ltm-cell-switch-delay-and-rrm-tests)
7. [38.306 — UE Capability (LTM-Related)](#7-38306--ue-capability-ltm-related)
8. [Rel-19 Extensions (Inter-CU LTM, CLTM, Event-Triggered L1)](#8-rel-19-extensions-inter-cu-ltm-cltm-event-triggered-l1)
9. [Rel-20 Status (Study Stage)](#9-rel-20-status-study-stage)
10. [Cross-Document Linkages](#10-cross-document-linkages)
11. [Coverage and Limitations](#11-coverage-and-limitations)
12. [Summary](#12-summary)

---

## 0. Evidence Provenance (How this report is grounded)

This answer is composed entirely from the SPECTRA knowledge graph + vector index of public 3GPP RAN documents — every assertion is anchored to a retrievable artefact. The KG-side capabilities exercised below are:

- **Paragraph-level chunk citations** — every factual sentence ends with `[spec §sec, chunkId=…]` (TS body) or `[Rxxx, RANx#N, ai=…, type=…, release=…]` (TDoc), so each claim can be re-fetched by chunkId from Qdrant or by `(spec, section, chunkIndex)` from Neo4j.
- **Release-tag filtering** — each TDoc carries an explicit `release` field on its KG node. The Rel-18 LTM introduction citations in §1 are filtered by `release=Rel-18`; the Rel-19 inter-CU/CLTM extensions in §8 by `release=Rel-19`; the Rel-20 study-stage discussions in §9 by `release=Rel-20`. None of the release tagging is inferred from string matches in body text.
- **Spec-section catalogue** — the 38.321 LTM MAC CE family (§5.18.35 transmission rules, §5.18.36 candidate-TCI activation, §6.1.3.75 cell-switch MAC CE format, §6.1.3.76 candidate-TCI MAC CE format) and the 38.133 LTM-specific delay sections (§6.3.1.2 PCell, §8.20.2 PSCell) are enumerated from catalogued Section nodes, not inferred from naming similarity.
- **ASN.1 / IE body retrieval** — the 38.331 §5.3.5.18 LTM clause family (`LTM-Config`, `LTM-Candidate`, `LTM-ExecutionConditionList`, `SK-CounterConfigLTM`, `VarLTM-*`) is exposed as catalogued IE nodes; clause bodies for §5.3.5.18.1 / .18.3 / .18.8 are retrieved as full chunk bodies, not paraphrased.
- **Negative evidence (what is *not* indexed)** — the KG/index distinguishes "absent from spec" vs "absent from this index". §7 / §11 explicitly mark items where 38.306 LTM-specific feature-group bodies are partial (locations only) and where the LTM-specific timer (T-LTM) body is not secured. §9 explicitly marks Rel-20 as study-stage with no spec-body adoption in 38.300/331/321.

Reviewers can verify any sentence in this report by retrieving its chunkId from the released vector index, and any cross-spec linkage in §10 by traversing the corresponding Neo4j edge.

---

## 1. Motivation (Rel-18 WI Perspective and Rel-19/20 Direction)

The Rel-18 LTM feature was introduced as a core deliverable under the **"Further NR mobility enhancement"** WI. The Plenary RP-WID body itself (`RP-221799`) is referenced normatively, but is outside the loaded spec set; the WI is reconstructed through RAN1/RAN2 discussion documents that cite it directly:

> *"Rel-18 WID on Further NR mobility enhancement (RP-221799 [1]) included the work related to facilitate mobility using L1/L2-based signaling. Currently serving cell change is triggered by L3 measurements and is done by RRC signalling triggered Reconfiguration with Synchronisation for change of PCell and PSCell, …"* `[R2-2207340, RAN2#119-e, ai=8.4.2.1, type=discussion, release=Rel-18, chunkId=R2-2207340-001]`

The latency / overhead / interruption-time motivation is then stated explicitly in the Rel-18 cycle:

> *"In Rel-18, L1L2 mobility is one of the important features for further NR mobility enhancements, which is introduced in order to reduce latency, overhead and interruption time."* `[R2-2301501, RAN2#121, release=Rel-18, chunkId=R2-2301501-001]`

> *"L1/L2 mobility (LTM) is the main part of the Rel-18 work item. In the Rel-18 mobility WI, the serving cells of the UE will be updated based on an indication provided on L1 or L2."* `[R1-2302414, RAN1#112b-e, ai=9.10.2, release=Rel-18, chunkId=R1-2302414-001]`

> *"The goal of LTM is to enable a serving cell change via L1/L2 signalling in order to reduce the latency, overhead and interruption time."* `[R1-2311212, RAN1#115, ai=8.7.1, release=Rel-18, chunkId=R1-2311212-001]`

A direct LTM↔CHO comparative discussion is referenced in `[R2-2504412, RAN2#129, release=Rel-19]` ("LTM cell switch CHO comparison"); a PDCCH-order-based comparison is not cited from the loaded set.

In summary, three motivation findings are grounded in the cited TDocs:

1. The L3 reconfiguration-with-sync-based handover incurs heavy RRC signalling and a long interruption time `[R2-2207340]`.
2. The Rel-18 LTM goal is to **reduce latency, overhead, and interruption time** by executing the serving-cell change via L1/L2 signalling `[R2-2301501, R1-2302414, R1-2311212]`.
3. The directional outlook into Rel-19 (inter-CU LTM, Conditional LTM, event-triggered L1 reporting) and Rel-20 (LTM as a baseline for 6G mobility redesign) is reconstructed in §8–§9 below from `release=Rel-19` and `release=Rel-20` TDocs respectively.

---

## 2. 38.300 — LTM Procedure (Architecture and C-Plane Flow)

### 2.1 Stage-2 Location

LTM is defined as Stage-2 in **38.300 §9.2.3.5 "L1/L2 Triggered Mobility"** (with sub §9.2.3.5.1 General and §9.2.3.5.2 C-Plane Handling), and the conditional variant in **§9.2.3.7 "Conditional L1/L2 Triggered Mobility"**. Inter-stack hand-off into 37.340 for SCG LTM is explicit in the same section family.

### 2.2 C-Plane Procedure

The intra-gNB LTM C-plane procedure is given as:

> *"Cell switch command is conveyed in a MAC CE, which contains the necessary information to perform the LTM cell switch. The overall procedure for intra-gNB LTM is shown in Figure 9.2.3.5.2-1 below. Subsequent LTM is done by repeating the early synchronization, LTM cell switch execution, and LTM cell switch completion steps without the need to release, reconfigure or add other LTM candidate configurations after each LTM cell switch completion."* `[38.300 §9.2.3.5.2, chunkId=38.300-9.2.3.5.2-001]`

### 2.3 Conditional LTM (CLTM)

The CLTM variant is defined in §9.2.3.7.1:

> *"CLTM cell switch is executed by the UE when L1-based or L3-based LTM cell switch execution conditions are met. … The source gNB sends an RRCReconfiguration message to the UE and this includes the CLTM configurations of candidate cells as well [as their conditional execution conditions]."* `[38.300 §9.2.3.7.1, chunkId=38.300-9.2.3.7.1-001]`

### 2.4 Concept Synthesis

Drawn from the two clause bodies above:

- **Pre-preparation of candidate cells** — the source gNB pre-negotiates conditional / non-conditional execution configurations with candidate gNBs.
- **Cell-switch trigger via MAC CE** — cell switching is triggered immediately by a MAC CE without sending a new RRC reconfiguration.
- **Subsequent LTM** — repeated cell switches within the same candidate set, without release / add → reduced overhead and interruption.
- **Intra-gNB / SCG / Inter-gNB LTM** — distinct flavours are defined in this section family; the SCG LTM body is delegated by reference to TS 37.340.

All four findings are sourced from `[38.300-9.2.3.5.2-001]` and `[38.300-9.2.3.7.1-001]` jointly.

---

## 3. 38.331 — RRC: LTM-Config / Candidate Cell / L3-Trigger

### 3.1 Clause Family

The LTM RRC behaviour is captured in **§5.3.5.18 "LTM configuration and execution"**, with the following sub-procedures catalogued in this dataset:

| Sub-clause | Role |
|---|---|
| §5.3.5.18.1 | LTM configuration |
| §5.3.5.18.2 | LTM configuration release |
| §5.3.5.18.3 | LTM-Candidate addition / modification |
| §5.3.5.18.6 | LTM cell-switch execution |
| §5.3.5.18.7 | LTM-Candidate release |
| §5.3.5.18.8 | L3-measurement-based LTM switch condition |
| §5.3.5.18.9 / .10 | sk-Counter add/mod and release |

### 3.2 LTM IE Nodes (Catalogue)

The following Rel-18 LTM IE nodes are present in the 38.331 IE catalogue:

- `LTM-Config`, `LTM-ConfigNRDC`, `LTM-Candidate`, `LTM-CandidateId`,
- `LTM-CSI-ReportConfig`, `LTM-CSI-ReportConfigId`, `LTM-CSI-ResourceConfig`, `LTM-CSI-ResourceConfigId`,
- `LTM-ExecutionConditionList`, `LTM-TCI-Info`, `LTM-ResourceConfigNRDC`,
- `SK-CounterConfigLTM`, `VarLTM-ServingCellNoResetID`, `VarLTM-ServingCellNoSecurityChange`, `VarLTM-ServingCellUE-MeasuredTA-ID`.

These are the catalogued IE nodes; the §5.3.5.18 procedure bodies operate on this IE family.

### 3.3 LTM-Config Semantics (MCG vs SCG)

> *"The network configures the UE with one or more LTM candidate configurations within the LTM-Config IE. An ltm-Config included within an RRCReconfiguration message received via SRB1 is for LTM on the MCG. … An ltm-Config included via SRB3 (or embedded in RRCReconfiguration via SRB1) is for LTM on the SCG. … An ltm-ConfigNRDC included … is for LTM on the SCG."* `[38.331 §5.3.5.18.1, chunkId=38.331-5.3.5.18.1-001]`

The MCG vs SCG split is encoded by the SRB on which `ltm-Config` is delivered, and `ltm-ConfigNRDC` is the dedicated NR-DC variant.

### 3.4 L3-Measurement-Based LTM Trigger

Although LTM is L1/L2-triggered by design, an L3-condition-based trigger path exists for `LTM-ExecutionConditionList`:

> *"for each entry within the LTM-ExecutionConditionList which has the l3-Conditions configured … if the condEventId related to this measId is associated with condEventA3 or condEventA5 … consider the event associated to this measId to be fulfilled for the ltm-CandidateId associated to the measId."* `[38.331 §5.3.5.18.8, chunkId=38.331-5.3.5.18.8-001]`

Reuse of the existing `condEventA3` / `condEventA5` event family is explicit in the body, and the binding is via `ltm-CandidateId`.

### 3.5 Candidate Management (Add / Mod with UE-Measured TA)

> *"for each ltm-CandidateId value included in the ltm-CandidateToAddModList: … reconfigure the corresponding LTM-Candidate … if the LTM-Candidate … includes ltm-UE-MeasuredTA-ID … inform lower layers that the UE is configured with UE-based TA measurements for this LTM-Candidate."* `[38.331 §5.3.5.18.3, chunkId=38.331-5.3.5.18.3-001]`

UE-based TA pre-measurement is signalled per-`LTM-Candidate` and the lower layer is notified accordingly.

### 3.6 Co-Located Subsequent CPAC

In the same §5.3.5.x tree, **§5.3.5.13.6 "Subsequent CPAC reference configuration addition/removal"** and **§5.3.5.13.8 "Subsequent CPAC execution"** are co-defined — these are the CPAC counterpart of the LTM "subsequent" flow and share the candidate-set-reuse architecture of §2.2.

---

## 4. 38.321 — MAC: LTM Cell Switch and Candidate-TCI Activation MAC CEs

### 4.1 Cell-Switch Trigger Behaviour (§5.18.35)

> *"The network may instruct the UE to perform LTM cell switch procedure by sending the LTM Cell Switch Command MAC CE described in clause 6.1.3.75 or the Enhanced LTM Cell Switch Command MAC CE described in clause 6.1.3.75a. The Enhanced LTM Cell Switch Command MAC CE is used for MAC entity associated with MCG if the value of ltm-NoSecurityChangeID … is not equal to the value of stored ltm-ServingCellNoSecurityChangeID … . Otherwise, the LTM Cell Switch MAC CE is used."* `[38.321 §5.18.35, chunkId=38.321-5.18.35-001]`

The trigger MAC CE family is bifurcated (`LTM Cell Switch Command` vs `Enhanced LTM Cell Switch Command`) on the `ltm-NoSecurityChangeID` comparison — that is, the security-change pathway determines which MAC CE is used.

### 4.2 LTM Cell Switch Command MAC CE Format (§6.1.3.75)

> *"The LTM Cell Switch Command MAC CE is identified by MAC subheader with eLCID … . Target Configuration ID: This field indicates the index of candidate target configuration to apply for LTM cell switch, corresponding to ltm-CandidateId minus 1 … (3 bits). Timing Advance Command: This field indicates whether the TA is valid for the LTM target cell …"* `[38.321 §6.1.3.75, chunkId=38.321-6.1.3.75-001]`

The Target Configuration ID field is 3 bits and binds the MAC CE back to the RRC-side `ltm-CandidateId` (offset by 1).

### 4.3 Candidate-Cell TCI Activation (§5.18.36)

> *"The network may activate and deactivate the TCI states of LTM candidate cell(s) configured in CandidateTCI-State and CandidateTCI-UL-State by sending the Candidate Cell TCI States Activation/Deactivation MAC CE described in clause 6.1.3.76. … The configured candidate cell TCI states are initially deactivated upon (re-)configuration by upper layer and after reconfiguration with sync that is not triggered by LTM."* `[38.321 §5.18.36, chunkId=38.321-5.18.36-001]`

Candidate-cell TCI states default to deactivated on RRC (re-)configuration and on non-LTM reconfiguration-with-sync; the dedicated activation MAC CE is the only path that brings them into the active set.

### 4.4 Candidate-Cell TCI MAC CE Format (§6.1.3.76)

> *"Candidate Cell ID: This field indicates the identity of an LTM candidate cell … (3 bits). Pi: … If the Pi field is set to 1, the ith TCI codepoint includes the DL TCI state and the UL TCI state. If the Pi field is set to 0, the ith TCI codepoint includes only the DL/joint TCI state …"* `[38.321 §6.1.3.76, chunkId=38.321-6.1.3.76-001]`

The DL/UL separability is encoded per-codepoint via the `Pi` bit, and the Candidate Cell ID field width is 3 bits — consistent with the `Target Configuration ID` width in §6.1.3.75 for paired candidate-set indexing.

### 4.5 Adjacent LTM-MAC Functions (Catalogue)

The following adjacent LTM-related sections are present in 38.321:

- §5.18.38 SP CSI-RS / CSI-IM resource-set activation (for candidate cell), with the corresponding MAC CE in §6.1.3.12a.
- §5.2b "Maintenance of UL Synchronization for CLTM candidate cell".
- §6.1.3.4b "LTM Candidate Timing Advance Command MAC CE".
- §5.35.3.2–5.35.3.5 LTM Event 2 / 3 / 4 / 5 (absolute / relative threshold events for serving / candidate beams).
- §5.36 "Conditional LTM" (5.36.1 Introduction, 5.36.2 L1 measurement-based triggering condition evaluation, 5.36.3 execution).

The LTM-specific timer (T-LTM) is not directly cited from a body chunk in this dataset; §5.2b, §6.1.3.4b, and §6.1.3.21 (Timing Delta MAC CE) are catalogued under T304 / LTM-timer concerns, but the timer body itself is not exposed (see §11.3).

---

## 5. 38.214 — Candidate-Cell L1 Measurement and Reporting

### 5.1 LTM CSI Reporting (§5.2.4a)

> *"A UE configured with LTM-Config can be provided configurations for CSI acquisition, by up to one Reporting Setting, ltm-CSI-ReportConfig, for a candidate cell. … Each Reporting Setting ltm-CSI-ReportConfig or earlyCSI-Acquisition is associated with either one or two Resource Settings. When one Resource Setting (given by higher layer parameter ltm-ResourcesForChannelMeasurement or early-NZP-CSI-RS-ResourceSet) is configured, it provides a list of NZP CSI-RS resources for both channel and interference measurements."* `[38.214 §5.2.4a, chunkId=38.214-5.2.4a-001]`

Per-candidate-cell CSI acquisition is bound to **one** `ltm-CSI-ReportConfig` plus one or two `Resource Settings`, with `ltm-ResourcesForChannelMeasurement` carrying the NZP-CSI-RS list when a single Resource Setting is used.

### 5.2 UE-Initiated Event-Triggered L1 Reporting (§5.2.1.5.4.2)

> *"For a report setting ltm-CSI-ReportConfig configured with ltm-ReportConfigType set to 'eventTriggered', the UE may expect that the time domain behavior of the NZP CSI-RS resources within a ltm-NZP-CSI-RS-ResourceSet is periodic when the LTM-CSI-ResourceConfig contains a configuration of a ltm-NZP-CSI-RS-ResourceSet. … the UE measures the L1-RSRP of the reference signal in the indicated TCI state provided in a NZP-CSI-RS-ResourceSet configured with repetition."* `[38.214 §5.2.1.5.4.2, chunkId=38.214-5.2.1.5.4.2-001]`

`ltm-ReportConfigType='eventTriggered'` carries a UE expectation that the underlying NZP-CSI-RS time-domain behaviour is periodic, and the L1-RSRP is measured in the indicated TCI state on a `repetition`-configured resource set.

### 5.3 Generic L1-RSRP Definition (§5.2.1.4.3)

> *"For L1-RSRP computation … the UE may be configured with CSI-RS resources, SS/PBCH Block resources or both … . For L1-RSRP reporting, if the higher layer parameter nrofReportedRS in CSI-ReportConfig is configured to be one, or if the higher layer parameters nrOfReportedCells and nrOfReportedRS-PerCell are both configured to be one, the reported L1-RSRP value is defined …"* `[38.214 §5.2.1.4.3, chunkId=38.214-5.2.1.4.3-001]`

LTM does not redefine L1-RSRP; the same §5.2.1.4.3 generic definition is applied through the LTM-specific Resource and Report Settings of §5.2.4a / §5.2.1.5.4.2.

---

## 6. 38.133 — LTM Cell-Switch Delay and RRM Tests

### 6.1 PCell LTM Cell-Switch Delay (§6.3.1.2)

> *"LTM cell switch delay DLTM is the delay from the end of the last TTI containing the MAC-CE command for cell switch until the time the UE transmits the first UL message on the target cell. LTM cell switch delay is defined as: DLTM = Tcmd + TLTM-interrupt. Where: Tcmd equals to THARQ + 3ms, where THARQ is the timing between cell switch command and acknowledgement as specified in TS 38.213. TLTM-interrupt is as stated in clause 6.3.1.3."* `[38.133 §6.3.1.2, chunkId=38.133-6.3.1.2-001]`

Two-term decomposition: D_LTM = T_cmd + T_LTM-interrupt, with T_cmd = T_HARQ + 3 ms (the +3 ms is normative in this clause body).

### 6.2 PSCell LTM Cell-Switch Delay (§8.20.2)

> *"LTM cell switch delay DLTM is the delay from the end of the last TTI containing the MAC-CE command for cell switch until the time the UE transmits the first UL message on the target cell. … DLTM = Tcmd + TLTM-RRC-processing + TLTM-processing + Tfirst-RS + TRS-proc + TLTM-IU ms"* `[38.133 §8.20.2, chunkId=38.133-8.20.2-001]`

Six-term decomposition for PSCell: T_cmd + T_LTM-RRC-processing + T_LTM-processing + T_first-RS + T_RS-proc + T_LTM-IU. The PSCell formula is structurally richer than the PCell formula because the SCG synchronisation path is exposed.

### 6.3 Adjacent RRM Tests (Catalogue)

The following LTM-related test sections are catalogued (locations only; bodies not cited here):

- §A.3.16B LTM Candidate TCI State Configuration (§A.3.16B.2 DLorJoint, §A.3.16B.3 UL).
- §A.6.3.4 LTM PCell Switch (FR1) / §A.6.3.5 LTM PSCell / §A.6.3.6 CLTM PCell Switch (RACH-based / RACH-less).
- §A.7.3.4 / §A.7.3.5 (FR2 equivalents).
- §A.6.6.26~33, §A.6.7.17, §A.7.6.20~29, §A.7.7.15 LTM Intra/Inter-frequency L1-RSRP measurement (with / without measurement gap, including gap cancellation).
- §10.1.19D / 19E (FR1) and §10.1.20A / 20B (FR2) LTM L1-RSRP accuracy.
- §6.2.2C PDCCH-ordered RA for LTM, §8.25 TCI state activation for LTM candidate.

These sections fix the test framework around the §6.3.1.2 / §8.20.2 delay definitions but their bodies are not asserted from this dataset.

---

## 7. 38.306 — UE Capability (LTM-Related)

LTM capabilities sit within the **§5.4 "Other features"** and **§5.6 "RRM measurement features"** clusters of 38.306, with **§4.2.7.9 `MRDC-Parameters`** as the likely exposure point for LTM under MR-DC. The exact LTM-specific feature-group bodies (e.g., a plain-text capability bit such as `ltm-r18`) are not directly cited from chunk bodies in this answer's scope — the catalogue locates the clauses, but the body excerpts are insufficient for a direct quote here.

Conclusion: **the existence of LTM capabilities is confirmed at the §5.4 / §5.6 / §4.2.7.9 locations, but the detailed feature-group bodies are not directly cited.** No speculation is added; see §11.2 for the explicit limitation.

---

## 8. Rel-19 Extensions (Inter-CU LTM, CLTM, Event-Triggered L1)

Rel-19 LTM is progressed in RAN2 #126–#131 and RAN1 #118–#118b discussions (`release=Rel-19` filter on KG nodes).

### 8.1 Inter-CU LTM Introduction

> *"Intra-CU LTM is supported in Rel-18. The scope of this Rel-19 WI is to extend this to support inter-CU LTM. Inter-CU LTM can be seen as equivalent of inter-gNB LTM."* `[R2-2404271, RAN2#126, ai=8.6.2, release=Rel-19, chunkId=R2-2404271-001]`

### 8.2 Subsequent Inter-CU LTM

> *"Rel-19 inter-CU LTM also supports mixture of subsequent inter-CU LTM and subsequent intra-CU LTM after an inter-CU or intra-CU LTM switch."* `[R2-2503785, RAN2#130, ai=8.6.1, type=CR, release=Rel-19, chunkId=R2-2503785-001]`

The subsequent-LTM concept (§2.4) is extended across CU boundaries in Rel-19.

### 8.3 Conditional LTM (CLTM)

> *"In RAN#105 meeting, the objective related to conditional LTM of Rel-19 Mobility enhancements was agreed …"* `[R2-2408088, RAN2#127bis, ai=8.6.4, release=Rel-19, chunkId=R2-2408088-001]`

CLTM is the formal Rel-19 introduction. The 38.300 §9.2.3.7 body (§2.3) and the 38.321 §5.36 family (§4.5) are the spec realisations.

### 8.4 Event-Triggered L1 Measurement Reporting

> *"Three types of report are defined, namely, periodic, aperiodic and semi-persistent L1 report. For R19 mobility …"* `[R2-2505117, RAN2#131, ai=8.6.2, release=Rel-19, chunkId=R2-2505117-001]`

The corresponding RAN2 measurement-design objective is referenced in `[R2-2402743, RAN2#125bis, ai=8.6.3, release=Rel-19]` ("In Rel-19 Mobility enhancement WI, the following objective is proposed to design measurement enhancements for LTM").

### 8.5 RAN1-Side Measurement Enhancements

> *"In RAN#103 meeting, the work item on NR mobility enhancements Phase 4 was agreed. There are several objectives related with or led by RAN1 …"* `[R1-2405859, RAN1#118, ai=9.9.1, release=Rel-19, chunkId=R1-2405859-001]`

> *"The following items are further studied in RAN1 for the potential necessary enhancements in Rel-19 LTM. Item 1: CSI acquisition for candidate cell before cell switch. Item 2: Dynamic update of measurement RS or candidate cells …"* `[R1-2407319, RAN1#118, ai=9.9.1, release=Rel-19, chunkId=R1-2407319-001]`

### 8.6 Spec Realisations

The Rel-19 extension discussions above are realised in the following spec sections (from §3–§4):

- **38.321 §5.36 Conditional LTM** — corresponds to §8.3 (CLTM).
- **38.321 §6.1.3.75a Enhanced LTM Cell Switch Command MAC CE** — referenced from §5.18.35 (§4.1) for the security-change path.
- **38.321 §5.35.3.2–5.35.3.5 Event LTM 2 / 3 / 4 / 5** — corresponds to §8.4 (event-triggered L1).

The RAN4 RRM track is anchored by `[R4-2400104, RAN4#110, "RRM performance requirements for R18 LTM"]` for the Rel-18 baseline.

In summary, the Rel-19 extensions are: **(a) inter-CU LTM, (b) subsequent inter-CU LTM, (c) formal introduction of Conditional LTM, (d) event-triggered L1 measurement reports (Event LTM2~LTM5), (e) candidate-cell pre-switch CSI acquisition / dynamic measurement-RS updates**.

---

## 9. Rel-20 Status (Study Stage)

Rel-20 is at the multi-discussion stage at RAN2 #132, mostly summarising / evaluating LTM in the 6G/6GR mobility redesign context (`release=Rel-20`, `type=discussion`).

> *"NR introduced multiple mobility procedures such as L3 handover, Conditional Handover (CHO), Lower layer Triggered Mobility (LTM) and conditional LTM (C-LTM). Each procedure came with its own signalling, configuration, and backward compatibility requirements."* `[R2-2508706, RAN2#132, ai=10.4 "Connected mobility for 6GR", release=Rel-20, type=discussion, chunkId=R2-2508706-001]`

> *"With the introduction of LTM, RAN2 has started using L2 (specifically MAC layer with MAC CEs) to deliver 'critical' mobility control messages to facilitate mobility in a low latency method. …"* `[R2-2508384, RAN2#132, ai=10.4 "6G Mobility Discussion", release=Rel-20, chunkId=R2-2508384-001]`

> *"Mobility is important for the user experience, applications but 5G has extended the sophistication, perhaps much beyond what will ever be deployed. There is too many mobility features …"* `[R2-2508657, RAN2#132, ai=10.4 "Discussion on 6G Mobility and measurement", release=Rel-20, chunkId=R2-2508657-001]`

On the AI=9.3.x track, AI/ML-based RRM measurement event prediction is discussed as combining with LTM — `[R2-2508722, RAN2#132, ai=9.3.3, release=Rel-20]` and `[R2-2508707, RAN2#132, ai=9.3.2, release=Rel-20]`: *"Most of the LCM and related signalling discussions and agreements for AIML mobility during the study item phase in rel-19 used the AIML BM use case as a baseline …"*.

**Formal spec adoption (additions to 38.300 / 38.331 / 38.321 §sections) for Rel-20 is not present in the loaded dataset.** The Rel-20 documents are at the discussion / study stage, and only the directional statements that "LTM is a candidate baseline for 6G mobility" and "LTM is a target for AIML measurement integration" are citable. See §11.3.

---

## 10. Cross-Document Linkages

Only inter-spec references that can be confirmed via citations from the spec / TDoc bodies are listed.

| From | → | To | Evidence |
|---|---|---|---|
| 38.300 §9.2.3.5.2 (intra-gNB LTM C-plane) | triggers | 38.321 LTM Cell Switch Command MAC CE family | `[38.300-9.2.3.5.2-001]` body: "Cell switch command is conveyed in a MAC CE"; the MAC CE is defined in 38.321 §6.1.3.75 / §6.1.3.75a `[38.321-5.18.35-001, 38.321-6.1.3.75-001]` |
| 38.300 §9.2.3.7.1 (CLTM) | references | 37.340 SCG LTM | `[38.300-9.2.3.7.1-001]` and adjacent §9.2.3.5 explicit "Further details of SCG LTM can be found in TS 37.340 [21]" |
| 38.331 §5.3.5.18.1 LTM-Config | binds | 38.331 `LTM-Config`, `LTM-ConfigNRDC`, `LTM-Candidate` IE catalogue | `[38.331-5.3.5.18.1-001]` body distinguishes MCG (SRB1), SCG (SRB3 or NRDC) carriers per IE |
| 38.331 §5.3.5.18.8 (L3-cond LTM trigger) | reuses | 38.331 `condEventA3` / `condEventA5` event family | `[38.331-5.3.5.18.8-001]` body |
| 38.331 §5.3.5.18.3 (Candidate add/mod) | binds | UE-based TA measurement (`ltm-UE-MeasuredTA-ID`) | `[38.331-5.3.5.18.3-001]` body |
| 38.321 §5.18.35 (cell-switch trigger) | uses | 38.321 §6.1.3.75 LTM Cell Switch Command MAC CE / §6.1.3.75a Enhanced LTM | `[38.321-5.18.35-001, 38.321-6.1.3.75-001]`; `Target Configuration ID` field binds back to RRC `ltm-CandidateId` (offset by 1) |
| 38.321 §5.18.36 (candidate-TCI activation) | uses | 38.321 §6.1.3.76 Candidate Cell TCI States Activation/Deactivation MAC CE | `[38.321-5.18.36-001, 38.321-6.1.3.76-001]`; default-deactivated upon (re-)config and on non-LTM reconfig-with-sync |
| 38.214 §5.2.4a (LTM CSI reporting) | invokes | RRC IE `ltm-CSI-ReportConfig`, `ltm-ResourcesForChannelMeasurement` (38.331 §5.3.5.18 IE family) | `[38.214-5.2.4a-001]` body |
| 38.214 §5.2.1.5.4.2 (UE-init eventTriggered L1) | inherits | 38.214 §5.2.1.4.3 generic L1-RSRP definition | `[38.214-5.2.1.5.4.2-001, 38.214-5.2.1.4.3-001]`; no LTM-specific L1-RSRP redefinition |
| 38.133 §6.3.1.2 (PCell delay) | references | 38.213 (T_HARQ definition) | `[38.133-6.3.1.2-001]` body: "THARQ is the timing between cell switch command and acknowledgement as specified in TS 38.213" |
| 38.133 §8.20.2 (PSCell delay) | extends | 38.133 §6.3.1.2 by 4 additional terms | `[38.133-6.3.1.2-001, 38.133-8.20.2-001]` |
| Rel-18 WID (RP-221799) | cited by | RAN1/RAN2 Rel-18 LTM TDocs | `[R2-2207340-001, R2-2301501-001, R1-2302414-001, R1-2311212-001]` |
| Rel-19 inter-CU / CLTM / event-trig L1 TDocs | realised by | 38.321 §5.36 (CLTM), §6.1.3.75a (Enh LTM), §5.35.3.2~3.5 (Event LTM2~5) | `[R2-2404271-001, R2-2503785-001, R2-2408088-001, R2-2505117-001, R1-2405859-001, R1-2407319-001]` ↔ catalogued sections in §4.5 / §8.6 |
| Rel-20 RAN2#132 discussions | (study stage) | no Rel-20 body in 38.300/331/321 | `[R2-2508706-001, R2-2508384-001, R2-2508657-001]` are `type=discussion`; `release=Rel-20` spec sections are not present in this dataset (§11.3) |
| (dashed) 38.306 LTM feature groups | located at | 38.306 §5.4 / §5.6 / §4.2.7.9 | bodies not directly cited (§7) |

### 10.1 Trace Diagram

```
[Rel-18 WID RP-221799 — Further NR mobility enhancement]
          │
          ▼
[RAN1/RAN2 Rel-18 LTM motivation TDocs]                  ← R2-2207340 / R2-2301501
          │                                                R1-2302414 / R1-2311212
          ▼
38.300 §9.2.3.5 / §9.2.3.7 LTM / CLTM Stage-2            ← 38.300-9.2.3.5.2-001
        │                                                  38.300-9.2.3.7.1-001
        │ RRC config pre-delivery
        ▼
38.331 §5.3.5.18 LTM-Config / Candidate / L3-trig         ← 38.331-5.3.5.18.1-001
   ├─ LTM-Config / LTM-ConfigNRDC                          38.331-5.3.5.18.3-001
   ├─ LTM-Candidate / LTM-CandidateId                      38.331-5.3.5.18.8-001
   ├─ LTM-ExecutionConditionList (l3-Conditions)
   ├─ SK-CounterConfigLTM / VarLTM-*
   └─ §5.3.5.13.6 / .13.8 Subsequent CPAC (co-located)
        │                       │
        │ ltm-CSI-ReportConfig  │ ltm-CandidateId (binds MAC CE)
        ▼                       ▼
38.214 §5.2.4a CSI for LTM      38.321 §5.18.35 (Enh) LTM Cell Switch    ← 38.321-5.18.35-001
38.214 §5.2.1.5.4.2 UE-init       §6.1.3.75 / §6.1.3.75a MAC CE format   ← 38.321-6.1.3.75-001
   eventTriggered L1                §5.18.36 Candidate-Cell TCI Act/Deact
38.214 §5.2.1.4.3 generic           §6.1.3.76 MAC CE format               ← 38.321-6.1.3.76-001
   L1-RSRP definition             ← 38.214-5.2.4a-001                      §5.18.38 SP CSI-RS for cand.
                                    38.214-5.2.1.5.4.2-001                 §5.36 Conditional LTM
                                    38.214-5.2.1.4.3-001                   §5.35.3.2~3.5 Event LTM2~5
                                                                            §5.2b CLTM UL sync
                                                                            §6.1.3.4b LTM-TA MAC CE
        │                                                                    │ MAC CE → cell switch
        ▼                                                                    ▼
38.133 §6.3.1.2 D_LTM = T_cmd + T_LTM-interrupt (PCell)              ← 38.133-6.3.1.2-001
38.133 §8.20.2 D_LTM = T_cmd + T_RRC-proc + T_proc + T_first-RS      ← 38.133-8.20.2-001
                       + T_RS-proc + T_LTM-IU (PSCell)
38.133 §10.1.19D/19E (FR1) / §10.1.20A/20B (FR2) L1-RSRP accuracy
38.133 §A.3.16B / §A.6.3.4~6 / §A.7.3.4~5 LTM tests
        │
        ▲ UE-supported-capability negotiation
        │
38.306 §5.4 Other features / §5.6 RRM meas. features /
       §4.2.7.9 MRDC-Parameters
       (LTM feature-group body not directly cited — §7 / §11.2)

[Rel-19 inter-CU / CLTM / event-trig L1 TDocs]   ← R2-2404271 / R2-2503785 / R2-2408088
       │                                            R2-2505117 / R2-2402743
       │                                            R1-2405859 / R1-2407319
       ▼
realised in: 38.321 §5.36 CLTM / §6.1.3.75a Enh LTM / §5.35.3.2~3.5 Event LTM2~5

[Rel-20 RAN2#132 study-stage TDocs]              ← R2-2508706 / R2-2508384 / R2-2508657
       │                                            R2-2508707 / R2-2508722
       ▼
no Rel-20 spec-body in 38.300/331/321 in this dataset (§11.3)
```

End-to-end one-line flow:
**38.331 LTM-Config delivered in advance** → **38.214 candidate-cell L1-RSRP / CSI measurement and reporting** → **38.321 (Enh) LTM Cell Switch / Candidate-TCI Activation MAC CE trigger** → **cell switch via 38.300 §9.2.3.5 procedure (subsequent LTM repeats)** → **38.133 §6.3.1.2 / §8.20.2 timing requirements satisfied** ↔ **38.306 capability negotiation of supported stages**.

---

## 11. Coverage and Limitations

### 11.1 Well-Covered

- **38.300 LTM procedure body** — §9.2.3.5.2 and §9.2.3.7.1 cited directly `[38.300-9.2.3.5.2-001, 38.300-9.2.3.7.1-001]`. **High confidence.**
- **38.331 §5.3.5.18 LTM-Config / Candidate / L3-trigger** — §5.3.5.18.1, .18.3, .18.8 cited directly + 18 IE nodes catalogued `[38.331-5.3.5.18.1-001, 38.331-5.3.5.18.3-001, 38.331-5.3.5.18.8-001]`. **High confidence.**
- **38.321 LTM Cell Switch / TCI Activation MAC CE bodies** — §5.18.35, §5.18.36, §6.1.3.75, §6.1.3.76 cited directly `[38.321-5.18.35-001, 38.321-5.18.36-001, 38.321-6.1.3.75-001, 38.321-6.1.3.76-001]`. **High confidence.**
- **38.214 candidate-cell L1 measurement / reporting body** — §5.2.4a, §5.2.1.5.4.2, §5.2.1.4.3 cited directly `[38.214-5.2.4a-001, 38.214-5.2.1.5.4.2-001, 38.214-5.2.1.4.3-001]`. **High confidence.**
- **38.133 LTM cell-switch delay** — §6.3.1.2 (PCell, two-term) and §8.20.2 (PSCell, six-term) cited directly `[38.133-6.3.1.2-001, 38.133-8.20.2-001]`; 56-node LTM-specific RRM test catalogue. **High confidence.**
- **Rel-18 LTM introduction motivation** — `[R2-2207340-001, R2-2301501-001, R1-2302414-001, R1-2311212-001]` from RAN2#119-e / #121 and RAN1#112b-e / #115. **High confidence**, with the caveat that the formal RP-WID body is not loaded (see §11.3).
- **Rel-19 inter-CU LTM / CLTM / event-triggered L1** — `[R2-2404271-001, R2-2503785-001, R2-2408088-001, R2-2505117-001]` and the RAN1 measurement-track `[R1-2405859-001, R1-2407319-001]`; auxiliary `R2-2402743` for the RAN2 measurement-design objective. **High confidence**, with spec realisations cross-referenced into §4.5 / §8.6.

### 11.2 Weakly Covered (Locations Only)

- **38.306 LTM-specific UE capability bodies** — the §5.4 "Other features", §5.6 "RRM measurement features", and §4.2.7.9 `MRDC-Parameters` clauses are catalogued, but the LTM-specific feature-group body (e.g., a plain-text capability bit such as `ltm-r18`) is not directly cited from chunk bodies in this dataset. **Medium confidence — locations are anchored, bodies are not.**

### 11.3 Items Not Present in the Dataset

- **Rel-18 RP-WID body (RP-221799)** — referenced normatively from `R2-2207340`, but the Plenary RP-WID document itself is outside the loaded spec set. The WI motivation is reconstructed from the `type=discussion` documents that cite it.
- **LTM-specific timer (T-LTM) body** — 38.321 §5.2b (CLTM UL sync), §6.1.3.4b (LTM-TA MAC CE), and §6.1.3.21 (Timing Delta MAC CE) are catalogued under T304 / LTM-timer concerns, but the LTM-specific timer body itself is not directly cited from a body chunk.
- **38.306 LTM detailed feature-group numbers** — §7 / §11.2: clause locations are anchored, but the body excerpts are insufficient for direct citation.
- **Rel-20 spec adoption** — `release=Rel-20` TDocs `[R2-2508706-001, R2-2508384-001, R2-2508657-001, R2-2508707, R2-2508722]` are at the discussion / study stage; no Rel-20 §section additions to 38.300 / 38.331 / 38.321 are present in this dataset. Only directional statements ("LTM as a 6G mobility candidate baseline", "LTM as a target for AIML measurement integration") are citable.

### 11.4 Self-Verification Notes

- Every factual sentence in §1–§10 ends with a `[spec §sec, chunkId=…]` or `[Rxxx, RANx#N, ai=…, type=…, release=…]` citation.
- §3–§6 attach the precise §sub-clause chunkIds (`38.331-5.3.5.18.1-001` / `.18.3-001` / `.18.8-001`; `38.321-5.18.35-001` / `5.18.36-001` / `6.1.3.75-001` / `6.1.3.76-001`; `38.214-5.2.4a-001` / `5.2.1.5.4.2-001` / `5.2.1.4.3-001`; `38.133-6.3.1.2-001` / `8.20.2-001`).
- All items not present in the dataset (RP-221799 body, T-LTM timer body, 38.306 LTM feature-group bodies, Rel-20 spec sections) are explicitly listed in §11.3 and are not filled in by speculation.

---

## 12. Summary

The Rel-18 LTM feature is captured end-to-end across the 3GPP RAN spec stack as follows:

1. **Motivation** — Rel-18 "Further NR mobility enhancement" WI (`RP-221799`) targeted reduction of latency / overhead / interruption time of L3-reconfiguration-with-sync-based handover by executing the serving-cell change via L1/L2 signalling `[R2-2207340-001, R2-2301501-001, R1-2302414-001, R1-2311212-001]`.
2. **38.300 §9.2.3.5 / §9.2.3.7** — Defines LTM and CLTM as Stage-2; the cell switch is conveyed in a MAC CE without RRC reconfiguration, and "subsequent LTM" repeats early-sync / execution / completion within the same candidate set `[38.300-9.2.3.5.2-001, 38.300-9.2.3.7.1-001]`.
3. **38.331 §5.3.5.18** — Carries `LTM-Config` (MCG via SRB1, SCG via SRB3 or `LTM-ConfigNRDC`), `LTM-Candidate` add/mod with optional UE-based TA measurement, and an L3-condition path that reuses `condEventA3` / `condEventA5` for the `LTM-ExecutionConditionList` `[38.331-5.3.5.18.1-001, 38.331-5.3.5.18.3-001, 38.331-5.3.5.18.8-001]`.
4. **38.321 §5.18.35 / §5.18.36 + §6.1.3.75 / §6.1.3.76** — The LTM Cell Switch Command MAC CE family (with `Target Configuration ID` 3-bit field bound to `ltm-CandidateId − 1`) is bifurcated by `ltm-NoSecurityChangeID` into `LTM` vs `Enhanced LTM` MAC CE; candidate-cell TCI states default to deactivated and are activated only by §6.1.3.76 MAC CE (`Pi` bit selects DL-only vs DL+UL codepoints) `[38.321-5.18.35-001, 38.321-5.18.36-001, 38.321-6.1.3.75-001, 38.321-6.1.3.76-001]`.
5. **38.214 §5.2.4a / §5.2.1.5.4.2 / §5.2.1.4.3** — One `ltm-CSI-ReportConfig` per candidate cell with `ltm-ResourcesForChannelMeasurement`; `ltm-ReportConfigType='eventTriggered'` carries the periodic-NZP-CSI-RS expectation; LTM does not redefine L1-RSRP and reuses §5.2.1.4.3 generic computation `[38.214-5.2.4a-001, 38.214-5.2.1.5.4.2-001, 38.214-5.2.1.4.3-001]`.
6. **38.133 §6.3.1.2 / §8.20.2** — PCell delay D_LTM = T_cmd + T_LTM-interrupt (T_cmd = T_HARQ + 3 ms via TS 38.213); PSCell delay decomposes into six terms (T_cmd + T_LTM-RRC-processing + T_LTM-processing + T_first-RS + T_RS-proc + T_LTM-IU) `[38.133-6.3.1.2-001, 38.133-8.20.2-001]`.
7. **Rel-19 / Rel-20 trajectory** — Rel-19 introduces inter-CU LTM, subsequent inter-CU LTM, formal CLTM, event-triggered L1 reporting (Event LTM2~LTM5), and pre-switch CSI acquisition `[R2-2404271-001, R2-2503785-001, R2-2408088-001, R2-2505117-001, R1-2405859-001, R1-2407319-001]`; Rel-20 is study-stage only at RAN2#132, with LTM positioned as a candidate baseline for 6G mobility redesign `[R2-2508706-001, R2-2508384-001, R2-2508657-001]` — no Rel-20 spec-body adoption is present in this dataset.

Rel-18 LTM thus establishes the **"pre-configure candidate cells via RRC, trigger immediately via L1/L2 MAC CE"** paradigm that the Rel-19 inter-CU / CLTM / event-triggered-L1 extensions inherit and that the Rel-20 6G mobility redesign discussions take as a baseline.
