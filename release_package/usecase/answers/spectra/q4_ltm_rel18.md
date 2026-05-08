# Q4. Rel-18 LTM (L1/L2 Triggered Mobility) — Standards-Item Summary

> **Source**: SPECTRA RAG (Qdrant + Neo4j) only. No external search. All factual sentences are cited from chunks in the
> retrieval log `logs/cross-phase/usecase/q4_retrieval_log.json`.

---

## Metadata

| Item | Value |
|---|---|
| Question | Standards-item summary of Rel-18 LTM (38.300/331/321/214/133/306) + Rel-19/20 extensions + cross-document linkages |
| Embedding model | `openai/text-embedding-3-small` (OpenRouter) |
| Qdrant collections | `the section-level collection`, `the section-level collection`, `the section-level collection`, `the TDoc collection`, `the TDoc collection`, `the TDoc collection`, `ran1_cr_chunks`, `ran2_cr_chunks` |
| Neo4j | RAN1=7687, RAN2=7688, RAN4=7690 |
| Query count | TS 33 + TDoc 27 + Cypher 3 = **63** |
| Hits | TS 330, TDoc 270, Cypher rows 102 (44+2+56) |
| Top-k | 10 |

---

## SPECTRA RAG Retrieval Summary

### Hits per collection (vector search totals)

| Collection | Queries | Hits |
|---|---:|---:|
| the section-level collection (38.300/331/321/306) | 22 | 220 |
| the section-level collection (38.214) | 6 | 60 |
| the section-level collection (38.133) | 5 | 50 |
| the TDoc collection | 15 | 150 |
| the TDoc collection | 4 | 40 |
| the TDoc collection | 3 | 30 |
| ran2_cr_chunks | 3 | 30 |
| ran1_cr_chunks | 2 | 20 |
| **Total** | **60** | **600** |

### Release-tag distribution (TDoc search results)

| Release | hits |
|---|---:|
| Rel-18 | 94 |
| Rel-19 | 70 |
| Rel-20 | 30 |
| (no release tag = CR / some discussions) | 61 |
| Rel-15/16/17/14 (unrelated backfill) | 15 |

### Neo4j Section catalog (LTM-related core nodes)

| Spec | Core LTM sections / IE nodes (Cypher measurements) |
|---|---|
| 38.300 | 9.2.3.5 `L1/L2 Triggered Mobility`, 9.2.3.7 `Conditional L1/L2 Triggered Mobility` |
| 38.331 | 5.3.5.18 `LTM configuration and execution` (sub 5.3.5.18.1–10), 5.3.5.13.6/.13.8 `Subsequent CPAC`, IE group `LTM-Config / LTM-Candidate / LTM-CSI-ReportConfig / LTM-ResourceConfigNRDC / LTM-ConfigNRDC / SK-CounterConfigLTM / VarLTM-*` |
| 38.321 | 5.18.35 `(Enhanced) LTM Cell Switch Command`, 5.18.36 `Candidate Cell TCI States Activation/Deactivation`, 5.18.38 SP CSI-RS/CSI-IM for candidate cell, 5.2b `Maintenance of UL Synchronization for CLTM candidate cell`, 5.35.3.2–5.35.3.5 `Event LTM2~LTM5`, 5.36 `Conditional LTM`, 6.1.3.4b `LTM Candidate Timing Advance Command MAC CE`, 6.1.3.75 `LTM Cell Switch Command MAC CE`, 6.1.3.75a `Enhanced LTM Cell Switch Command MAC CE`, 6.1.3.76 `Candidate Cell TCI States Activation/Deactivation MAC CE`, 6.1.3.12a `SP CSI-RS/CSI-IM Resource Set Activation/Deactivation for Candidate Cell MAC CE` |
| 38.214 | 5.2.1.5.4.2 `UE Initiated LTM reporting`, 5.2.4a `CSI Reporting for LTM and handover` |
| 38.133 | 6.3 `L1/L2-Triggered Mobility` (6.3.1 LTM PCell, 6.3.1.2 LTM Cell Switch delay, 6.3.2 Conditional L1/L2-Triggered Mobility, 6.3.2.2 CLTM Cell Switch delay), 6.2.2C `PDCCH ordered Random Access for LTM`, 8.20 `LTM PSCell Cell Switch`, 8.25 `TCI state activation for LTM candidate cell`, 10.1.19D/19E/20A/20B `LTM Intra/Inter-frequency L1-RSRP accuracy (FR1/FR2)`, A.3.16B `LTM Candidate TCI State Configuration`, A.6.3.4/A.6.3.5/A.6.3.6 `LTM PCell/PSCell/CLTM PCell Switch` tests, A.6.6.26~33 / A.6.7.17 / A.7.6.20~29 / A.7.7.15 `LTM L1-RSRP measurement` tests |
| 38.306 | 5.4 `Other features`, 5.6 `RRM measurement features`, 4.2.7.9 `MRDC-Parameters` (LTM-related capabilities exposed) |

> The exact LTM-specific feature-group names in 38.306 were not directly retrieved as chunk bodies in this search; only the locational fact "they belong to the §5.4 Other features / §5.6 RRM measurement features cluster" is citable. Detailed feature-group numbers are **not found within SPECTRA RAG's search scope**.

---

## Answer Body

### 1. Rel-18 LTM Introduction Context — TDoc Evidence

According to SPECTRA RAG search results, Rel-18 LTM was introduced as a core deliverable under the **"Further NR mobility enhancement"** WI initiated at RAN#... (the Plenary RP-WID number is not directly retrieved in this search).
- "Rel-18 WID on Further NR mobility enhancement (RP-221799 [1]) included the work related to facilitate mobility using L1/L2-based signaling. Currently serving cell change is triggered by L3 measurements and is done by RRC signalling triggered Reconfiguration with Synchronisation for change of PCell and PSCell, …" [R2-2207340, RAN2#119-e, type=discussion, rel=Rel-18, AI=8.4.2.1, chunkId=R2-2207340-001]
- "In Rel-18, L1L2 mobility is one of the important features for further NR mobility enhancements, which is introduced in order to reduce latency, overhead and interruption time." [R2-2301501, RAN2#121, rel=Rel-18, chunkId=R2-2301501-001]
- "L1/L2 mobility (LTM) is the main part of the Rel-18 work item. In the Rel-18 mobility WI, the serving cells of the UE will be updated based on an indication provided on L1 or L2." [R1-2302414, RAN1#112b-e, rel=Rel-18, AI=9.10.2, chunkId=R1-2302414-001]
- "The goal of LTM is to enable a serving cell change via L1/L2 signalling in order to reduce the latency, overhead and interruption time." [R1-2311212, RAN1#115, rel=Rel-18, AI=8.7.1, chunkId=R1-2311212-001]

That is, within this retrieval scope, the LTM introduction motivation can be cited clearly as **(a) the latency / overhead / interruption-time limitations of RRC reconfiguration-with-sync-based L3 handover, (b) executing serving-cell change via L1/L2 signalling**. Comparative bodies vs CHO are matched in R2-2504412 (RAN2#129, Rel-19) "LTM cell switch CHO comparison", but the body text is not refined enough for direct citation. PDCCH-order-based comparison is insufficient for direct citation.

### 2. 38.300 — LTM Concept (Stage-2)

- Location: **38.300 §9.2.3.5 "L1/L2 Triggered Mobility"** (sub §9.2.3.5.1 General, §9.2.3.5.2 C-Plane Handling), **§9.2.3.7 "Conditional L1/L2 Triggered Mobility"** [Neo4j RAN2_LTM_sections, port=7688].
- C-plane procedure definition:
  > "Cell switch command is conveyed in a MAC CE, which contains the necessary information to perform the LTM cell switch. The overall procedure for intra-gNB LTM is shown in Figure 9.2.3.5.2-1 below. Subsequent LTM is done by repeating the early synchronization, LTM cell switch execution, and LTM cell switch completion steps without the need to release, reconfigure or add other LTM candidate configurations after each LTM cell switch completion." [38.300 §9.2.3.5.2, chunkId=38.300-9.2.3.5.2-001]
- CLTM procedure definition:
  > "CLTM cell switch is executed by the UE when L1-based or L3-based LTM cell switch execution conditions are met. … The source gNB sends an RRCReconfiguration message to the UE and this includes the CLTM configurations of candidate cells as well [as their conditional execution conditions]." [38.300 §9.2.3.7.1, chunkId=38.300-9.2.3.7.1-001]
- Core concept summary (all derived from the above two chunks):
  - **Pre-preparation of candidate cells**: the source gNB pre-negotiates conditional / non-conditional execution configurations with candidate gNBs.
  - **Cell-switch trigger via MAC CE**: cell switching is triggered immediately by a MAC CE without sending a new RRC reconfiguration.
  - **Subsequent LTM**: repeated cell switches within the same candidate set, without release/add → reduced overhead/interruption.
  - **Intra-gNB / SCG / Inter-gNB LTM** distinctions exist (37.340 reference is explicit: "Further details of SCG LTM can be found in TS 37.340 [21]").

### 3. 38.331 — RRC Parameters / IEs

- Core clause: **§5.3.5.18 "LTM configuration and execution"** (5.3.5.18.1 LTM configuration, .2 release, .3 add/mod, .6 execution, .7 release, .8 L3-meas based switch condition, .9/.10 sk-Counter add/mod/release) [Neo4j RAN2 cypher].
- Core IE nodes (Neo4j):
  - `LTM-Config`, `LTM-ConfigNRDC`, `LTM-Candidate`, `LTM-CandidateId`,
  - `LTM-CSI-ReportConfig`, `LTM-CSI-ReportConfigId`, `LTM-CSI-ResourceConfig`, `LTM-CSI-ResourceConfigId`,
  - `LTM-ExecutionConditionList`, `LTM-TCI-Info`, `LTM-ResourceConfigNRDC`,
  - `SK-CounterConfigLTM`, `VarLTM-ServingCellNoResetID`, `VarLTM-ServingCellNoSecurityChange`, `VarLTM-ServingCellUE-MeasuredTA-ID`.
- LTM-Config semantics:
  > "The network configures the UE with one or more LTM candidate configurations within the LTM-Config IE. An ltm-Config included within an RRCReconfiguration message received via SRB1 is for LTM on the MCG. … An ltm-Config included via SRB3 (or embedded in RRCReconfiguration via SRB1) is for LTM on the SCG. … An ltm-ConfigNRDC included … is for LTM on the SCG." [38.331 §5.3.5.18.1, chunkId=38.331-5.3.5.18.1-001]
- L3-based LTM trigger procedure:
  > "for each entry within the LTM-ExecutionConditionList which has the l3-Conditions configured … if the condEventId related to this measId is associated with condEventA3 or condEventA5 … consider the event associated to this measId to be fulfilled for the ltm-CandidateId associated to the measId." [38.331 §5.3.5.18.8, chunkId=38.331-5.3.5.18.8-001]
- Candidate management:
  > "for each ltm-CandidateId value included in the ltm-CandidateToAddModList: … reconfigure the corresponding LTM-Candidate … if the LTM-Candidate … includes ltm-UE-MeasuredTA-ID … inform lower layers that the UE is configured with UE-based TA measurements for this LTM-Candidate." [38.331 §5.3.5.18.3, chunkId=38.331-5.3.5.18.3-001]
- Relation to subsequent CPAC:
  - §5.3.5.13.6 `Subsequent CPAC reference configuration addition/removal` and §5.3.5.13.8 `Subsequent CPAC execution` are co-defined in the same 5.3.5.x tree as LTM [Neo4j RAN2 cypher].

### 4. 38.321 — MAC Procedures / MAC CEs

- LTM cell-switch trigger (MAC CE transmission/reception):
  > "The network may instruct the UE to perform LTM cell switch procedure by sending the LTM Cell Switch Command MAC CE described in clause 6.1.3.75 or the Enhanced LTM Cell Switch Command MAC CE described in clause 6.1.3.75a. The Enhanced LTM Cell Switch Command MAC CE is used for MAC entity associated with MCG if the value of ltm-NoSecurityChangeID … is not equal to the value of stored ltm-ServingCellNoSecurityChangeID … . Otherwise, the LTM Cell Switch MAC CE is used." [38.321 §5.18.35, chunkId=38.321-5.18.35-001]
- MAC CE format:
  > "The LTM Cell Switch Command MAC CE is identified by MAC subheader with eLCID … . Target Configuration ID: This field indicates the index of candidate target configuration to apply for LTM cell switch, corresponding to ltm-CandidateId minus 1 … (3 bits). Timing Advance Command: This field indicates whether the TA is valid for the LTM target cell …" [38.321 §6.1.3.75, chunkId=38.321-6.1.3.75-001]
- Pre-activation of candidate-cell beams (TCI state):
  > "The network may activate and deactivate the TCI states of LTM candidate cell(s) configured in CandidateTCI-State and CandidateTCI-UL-State by sending the Candidate Cell TCI States Activation/Deactivation MAC CE described in clause 6.1.3.76. … The configured candidate cell TCI states are initially deactivated upon (re-)configuration by upper layer and after reconfiguration with sync that is not triggered by LTM." [38.321 §5.18.36, chunkId=38.321-5.18.36-001]
- Candidate-cell TCI MAC CE format (multi-codepoint, DL/UL separable):
  > "Candidate Cell ID: This field indicates the identity of an LTM candidate cell … (3 bits). Pi: … If the Pi field is set to 1, the ith TCI codepoint includes the DL TCI state and the UL TCI state. If the Pi field is set to 0, the ith TCI codepoint includes only the DL/joint TCI state …" [38.321 §6.1.3.76, chunkId=38.321-6.1.3.76-001]
- Additional LTM-MAC functions (Neo4j catalog):
  - §5.18.38 SP CSI-RS/CSI-IM resource-set activation (for candidate cell) + §6.1.3.12a MAC CE.
  - §5.2b `Maintenance of UL Synchronization for CLTM candidate cell`.
  - §6.1.3.4b `LTM Candidate Timing Advance Command MAC CE`.
  - §5.35.3.2–5.35.3.5 LTM Event 2/3/4/5 (absolute / relative threshold events for serving / candidate beams).
  - §5.36 `Conditional LTM` (5.36.1 Introduction, 5.36.2 L1 measurement-based triggering condition evaluation, 5.36.3 execution).
- T304 / timers: "T304 LTM timer MAC" queries match 38.321 §5.2b (UL sync) / §6.1.3.4b (TA MAC CE) / §6.1.3.21 (Timing Delta MAC CE) — **a body excerpt of an LTM-specific timer was not retrieved within this search**.

### 5. 38.214 — UE L1 Measurement / Reporting

- Location: **§5.2.4a "CSI Reporting for LTM and handover"**, **§5.2.1.5.4.2 "UE Initiated LTM reporting"** (Neo4j RAN1 cypher confirms these as the exact LTM nodes in 38.214).
- Configuration of CSI / L1-RSRP measurements for candidate cells:
  > "A UE configured with LTM-Config can be provided configurations for CSI acquisition, by up to one Reporting Setting, ltm-CSI-ReportConfig, for a candidate cell. … Each Reporting Setting ltm-CSI-ReportConfig or earlyCSI-Acquisition is associated with either one or two Resource Settings. When one Resource Setting (given by higher layer parameter ltm-ResourcesForChannelMeasurement or early-NZP-CSI-RS-ResourceSet) is configured, it provides a list of NZP CSI-RS resources for both channel and interference measurements." [38.214 §5.2.4a, chunkId=38.214-5.2.4a-001]
- UE-initiated event-triggered L1 reporting:
  > "For a report setting ltm-CSI-ReportConfig configured with ltm-ReportConfigType set to 'eventTriggered', the UE may expect that the time domain behavior of the NZP CSI-RS resources within a ltm-NZP-CSI-RS-ResourceSet is periodic when the LTM-CSI-ResourceConfig contains a configuration of a ltm-NZP-CSI-RS-ResourceSet. … the UE measures the L1-RSRP of the reference signal in the indicated TCI state provided in a NZP-CSI-RS-ResourceSet configured with repetition." [38.214 §5.2.1.5.4.2, chunkId=38.214-5.2.1.5.4.2-001]
- Generic L1-RSRP definition (LTM uses the same definition):
  > "For L1-RSRP computation … the UE may be configured with CSI-RS resources, SS/PBCH Block resources or both … . For L1-RSRP reporting, if the higher layer parameter nrofReportedRS in CSI-ReportConfig is configured to be one, or if the higher layer parameters nrOfReportedCells and nrOfReportedRS-PerCell are both configured to be one, the reported L1-RSRP value is defined …" [38.214 §5.2.1.4.3, chunkId=38.214-5.2.1.4.3-001]

### 6. 38.133 — RRM Requirements

- Generic clause: **§6.3 "L1/L2-Triggered Mobility"**, §6.3.1 LTM PCell, §6.3.2 Conditional LTM. Additionally **§8.20 LTM PSCell**, **§8.25 TCI state activation for LTM candidate**, **§6.2.2C PDCCH ordered RA for LTM**, **§10.1.19D/19E (FR1) / §10.1.20A/20B (FR2) LTM L1-RSRP accuracy** [Neo4j RAN4 cypher results].
- LTM cell-switch delay definition (PCell):
  > "LTM cell switch delay DLTM is the delay from the end of the last TTI containing the MAC-CE command for cell switch until the time the UE transmits the first UL message on the target cell. LTM cell switch delay is defined as: DLTM = Tcmd + TLTM-interrupt. Where: Tcmd equals to THARQ + 3ms, where THARQ is the timing between cell switch command and acknowledgement as specified in TS 38.213. TLTM-interrupt is as stated in clause 6.3.1.3." [38.133 §6.3.1.2, chunkId=38.133-6.3.1.2-001]
- LTM cell-switch delay definition (PSCell, more granular decomposition):
  > "LTM cell switch delay DLTM is the delay from the end of the last TTI containing the MAC-CE command for cell switch until the time the UE transmits the first UL message on the target cell. … DLTM = Tcmd + TLTM-RRC-processing + TLTM-processing + Tfirst-RS + TRS-proc + TLTM-IU ms" [38.133 §8.20.2, chunkId=38.133-8.20.2-001]
- Additional RRM tests (Neo4j catalog — bodies not cited; locations only):
  - §A.3.16B LTM Candidate TCI State Configuration / §A.3.16B.2 DLorJoint / §A.3.16B.3 UL.
  - §A.6.3.4 LTM PCell Switch (FR1) / §A.6.3.5 LTM PSCell / §A.6.3.6 CLTM PCell Switch (RACH-based / RACH-less).
  - §A.7.3.4 / §A.7.3.5 (FR2 equivalent).
  - §A.6.6.26~33, §A.6.7.17, §A.7.6.20~29, §A.7.7.15 LTM Intra/Inter-frequency L1-RSRP measurement (with/without measurement gap, including gap cancellation).

### 7. 38.306 — UE Capability

- Within this retrieval scope, LTM capabilities were located in the **§5.4 "Other features"** and **§5.6 "RRM measurement features"** clusters [38.306 §5.4 / §5.6 search], but the exact feature-group numbers (e.g., a plain-text capability bit such as `ltm-r18`) were not secured as chunk-body citations.
- §4.2.7.9 `MRDC-Parameters` was matched on the LTM intra-DU / inter-DU queries [38.306 §4.2.7.9, level=4] → presumably the exposure point for LTM capabilities under MR-DC, but the body excerpt is insufficient in this retrieval.
- Conclusion: **the existence of LTM capabilities is confirmed, but the detailed IE / feature-group is not secured within this SPECTRA RAG search scope**. Not citable from the body → no speculation.

### 8. Rel-19 Extensions (derivable from SPECTRA RAG data)

Rel-19 LTM is explicitly progressed in RAN2 #126–#131 / RAN1 #118–#118b discussions (TDoc search release="Rel-19" returns 70 hits).
- **Inter-CU LTM introduction**: "Intra-CU LTM is supported in Rel-18. The scope of this Rel-19 WI is to extend this to support inter-CU LTM. Inter-CU LTM can be seen as equivalent of inter-gNB LTM." [R2-2404271, RAN2#126, rel=Rel-19, AI=8.6.2, chunkId=R2-2404271-001]
- **Subsequent inter-CU LTM**: "Rel-19 inter-CU LTM also supports mixture of subsequent inter-CU LTM and subsequent intra-CU LTM after an inter-CU or intra-CU LTM switch." [R2-2503785, RAN2#130, rel=Rel-19, type=CR, AI=8.6.1, chunkId=R2-2503785-001]
- **Conditional LTM (CLTM)**: "In RAN#105 meeting, the objective related to conditional LTM of Rel-19 Mobility enhancements was agreed …" [R2-2408088, RAN2#127bis, rel=Rel-19, AI=8.6.4, chunkId=R2-2408088-001].
- **Event-triggered L1 measurement reporting**: "Three types of report are defined, namely, periodic, aperiodic and semi-persistent L1 report. For R19 mobility …" [R2-2505117, RAN2#131, rel=Rel-19, AI=8.6.2, chunkId=R2-2505117-001]; "In Rel-19 Mobility enhancement WI, the following objective is proposed to design measurement enhancements for LTM" [R2-2402743, RAN2#125bis, rel=Rel-19, AI=8.6.3].
- **Measurement enhancements on the RAN1 side**: "In RAN#103 meeting, the work item on NR mobility enhancements Phase 4 was agreed. There are several objectives related with or led by RAN1 …" [R1-2405859, RAN1#118, rel=Rel-19, AI=9.9.1, chunkId=R1-2405859-001]; FL summary: "The following items are further studied in RAN1 for the potential necessary enhancements in Rel-19 LTM. Item 1: CSI acquisition for candidate cell before cell switch. Item 2: Dynamic update of measurement RS or candidate cells …" [R1-2407319, RAN1#118, rel=Rel-19, AI=9.9.1, chunkId=R1-2407319-001].
- **38.321 §5.36 Conditional LTM**, the *Enhanced* path of §5.18.35 (`Enhanced LTM Cell Switch Command MAC CE`, §6.1.3.75a), §5.35.3.2~5.35.3.5 Event LTM2~LTM5 — these **actual spec realisations** matching the above RAN2 discussions are confirmed in the Neo4j catalog.

In summary, the Rel-19 extensions can be cited directly within this retrieval scope as **(a) inter-CU LTM, (b) subsequent inter-CU LTM, (c) formal introduction of Conditional LTM, (d) event-triggered L1 measurement reports (Event LTM2~LTM5), (e) candidate-cell pre-switch CSI acquisition / dynamic measurement-RS updates**.

### 9. Rel-20 Extensions (derivable from SPECTRA RAG data — early discussion stage in 6G context)

Rel-20 is at the multi-discussion stage at RAN2 #132 (release="Rel-20" 30 hits), mostly **summarising / evaluating LTM in the 6G/6GR mobility redesign context**.
- "NR introduced multiple mobility procedures such as L3 handover, Conditional Handover (CHO), Lower layer Triggered Mobility (LTM) and conditional LTM (C-LTM). Each procedure came with its own signalling, configuration, and backward compatibility requirements." [R2-2508706, RAN2#132, rel=Rel-20, type=discussion, AI=10.4 "Connected mobility for 6GR", chunkId=R2-2508706-001]
- "With the introduction of LTM, RAN2 has started using L2 (specifically MAC layer with MAC CEs) to deliver 'critical' mobility control messages to facilitate mobility in a low latency method. …" [R2-2508384, RAN2#132, rel=Rel-20, AI=10.4 "6G Mobility Discussion", chunkId=R2-2508384-001]
- "Mobility is important for the user experience, applications but 5G has extended the sophistication, perhaps much beyond what will ever be deployed. There is too many mobility features …" [R2-2508657, RAN2#132, rel=Rel-20, AI=10.4 "Discussion on 6G Mobility and measurement", chunkId=R2-2508657-001]
- On the AI=9.3.x track, **AI/ML-based RRM measurement event prediction** is discussed as combining with LTM — "Most of the LCM and related signalling discussions and agreements for AIML mobility during the study item phase in rel-19 used the AIML BM use case as a baseline …" [R2-2508722 / R2-2508707, RAN2#132, rel=Rel-20, AI=9.3.2/9.3.3].

→ **Formal spec adoption (additions to 38.300/331/321 §sections)** for Rel-20 is **not found** in this retrieval scope. So far the data are loaded only at the **discussion/study stage**, and only the directional statements that "LTM is a candidate baseline for 6G mobility / target for AIML measurement integration" are citable.

---

## Cross-Document Linkage Diagram

```
              ┌─────────────────────────────────────────────────────────┐
              │ 38.300 §9.2.3.5 / §9.2.3.7  (Stage-2 LTM / CLTM)         │
              │  - intra-gNB LTM, SCG LTM, CLTM flow, MAC CE trigger    │
              └───────────────┬─────────────────────────┬───────────────┘
                              │ RRC config pre-delivery  │ Inter-DU/SCG/Inter-CU
                              ▼                          │
        ┌───────────────────────────────────────┐        │
        │ 38.331 §5.3.5.18 + LTM-* IE group     │        │
        │  LTM-Config / LTM-Candidate /         │        │
        │  LTM-CSI-ReportConfig /               │        │
        │  LTM-ExecutionConditionList /         │        │
        │  SK-CounterConfigLTM / VarLTM-*       │        │
        │  §5.3.5.13.6/.13.8 Subsequent CPAC    │        │
        └─────┬───────────────┬─────────────────┘        │
              │ ltm-CSI-ReportConfig etc.          │      │
              │ (RS / measurement-reporting setup) │      │
              ▼                                     ▼      ▼
   ┌────────────────────────────────┐   ┌────────────────────────────────┐
   │ 38.214 §5.2.4a CSI for LTM     │   │ 38.321 §5.18.35 (Enh) LTM      │
   │ 38.214 §5.2.1.5.4.2 UE-init    │   │   Cell Switch Command          │
   │   eventTriggered L1 report     │   │ 38.321 §5.18.36 Candidate TCI  │
   │ 38.214 §5.2.1.4.3 generic      │   │   States Act/Deact MAC CE      │
   │   L1-RSRP definition           │   │ 38.321 §5.18.38 SP CSI-RS for  │
   │                                │   │   candidate cell               │
   │   ▶ candidate cell L1-RSRP /   │   │ 38.321 §5.36 Conditional LTM   │
   │     CSI results reported via   │──▶│ 38.321 §5.35.3.2~3.5 Event     │
   │     L1/L2                      │   │   LTM2~LTM5 (L1 evt-trig)      │
   │                                │   │ 38.321 §5.2b CLTM UL sync      │
   │                                │   │ 38.321 §6.1.3.4b LTM-TA MAC CE │
   └────────────────────────────────┘   └──────────┬─────────────────────┘
                                                   │ MAC CE → immediate cell switch
                                                   ▼
                          ┌─────────────────────────────────────────────┐
                          │ 38.133 §6.3 L1/L2-Triggered Mobility         │
                          │  §6.3.1.2 LTM PCell switch delay             │
                          │   DLTM = Tcmd + TLTM-interrupt               │
                          │  §8.20.2 LTM PSCell switch delay             │
                          │   DLTM = Tcmd + T_RRC + T_proc + Tfirst-RS   │
                          │          + T_RS-proc + T_LTM-IU              │
                          │  §10.1.19D/19E/20A/20B L1-RSRP accuracy      │
                          │  §A.3.16B / §A.6.3.4~6 / §A.7.3.4~5 tests    │
                          └─────────────────────────────────────────────┘
                                                   ▲
                                                   │ UE supported-capability negotiation
                                                   │
                          ┌─────────────────────────────────────────────┐
                          │ 38.306 §5.4 Other features /                │
                          │        §5.6 RRM measurement features /      │
                          │        §4.2.7.9 MRDC-Parameters             │
                          │  ▶ LTM support flags / FR1·FR2 / intra-DU·  │
                          │    inter-DU·inter-CU stage-by-stage UE caps │
                          │    (detailed feature numbers not in this    │
                          │     retrieval)                              │
                          └─────────────────────────────────────────────┘
```

Flow (one-line summary):
**38.331 LTM-Config delivered in advance** → **38.214 candidate-cell L1-RSRP / CSI measurement and reporting** → **38.321 (Enh)LTM Cell Switch / Candidate TCI Activation MAC CE trigger** → **cell switch via 38.300 §9.2.3.5 procedure (subsequent LTM repeats)** → **38.133 §6.3 timing / accuracy requirements satisfied** ↔ **38.306 capability negotiation of supported stages**.

---

## Coverage / Limitations

| Item | Status | Evidence |
|---|---|---|
| 38.300 LTM procedure body | OK | §9.2.3.5.2, §9.2.3.7.1 chunks cited directly |
| 38.331 LTM-Config / candidate / L3-trigger body | OK | §5.3.5.18.1, .18.3, .18.8 chunks cited directly + 18 Neo4j nodes |
| 38.321 LTM Cell Switch / TCI activation MAC CE body | OK | §5.18.35, §5.18.36, §6.1.3.75, §6.1.3.76 chunks cited directly |
| 38.214 candidate-cell L1 measurement / reporting body | OK | §5.2.4a, §5.2.1.5.4.2, §5.2.1.4.3 chunks cited directly |
| 38.133 LTM cell-switch delay definition body | OK | §6.3.1.2, §8.20.2 chunks cited directly + 56-node LTM-specific test catalog |
| 38.306 LTM UE capability detailed IEs | **partial — locations only** | §5.4 / §5.6 / §4.2.7.9 matched; **detailed feature-group bodies not secured** |
| Rel-18 introduction motivation (latency / overhead / interruption) | OK | R2-2207340, R2-2301501, R1-2302414, R1-2311212 |
| Exact body of the Rel-18 RP-WID | **not secured** | R2-2207340 references RP-221799. RP-* TDocs themselves are outside the retrieval scope |
| Rel-19 inter-CU LTM / CLTM / event-trig L1 | OK | R2-2404271, R2-2503785, R2-2408088, R2-2505117, R2-2402743 |
| Rel-19 RAN1 measurement enhancement | OK | R1-2405859, R1-2407319 (FL summary) |
| Rel-20 spec adoption | **not secured (study stage)** | only RAN2#132 discussions (R2-2508706, R2-2508384, R2-2508657, etc.). New §sections in 38.300/331/321 for Rel-20 are not detected in this retrieval |
| RAN4 RRM Rel-18 substantive discussion | OK | R4-2400104 (RAN4#110, "RRM performance requirements for R18 LTM") |
| 38.306 LTM UE capability detailed feature group | **not found** | chunk body not secured within this retrieval scope |
| LTM-specific timer (T-LTM) body | **not secured** | 38.321 §5.2b / §6.1.3.4b matched at locations only; insufficient body excerpts |

### Answer feasibility
Using SPECTRA RAG search results alone, **the core clauses, IEs, MAC CEs, delay formulae, and introduction motivation across the six specs (38.300/331/321/214/133/306) for Rel-18 LTM are answerable via direct citations**. **Rel-19 extensions (inter-CU LTM, Conditional LTM, event-triggered L1 reporting, candidate-cell CSI acquisition) are also answerable consistently using RAN1/RAN2 TDocs + Neo4j spec nodes**. However, **Rel-20 is citable only up to the discussion stage at RAN2#132**; spec-body adoption is not found. **The 38.306 LTM detailed feature-group numbers and the LTM-specific timer body** cannot be cited definitively from this retrieval — additional queries or direct loading of spec bodies are required.

---

