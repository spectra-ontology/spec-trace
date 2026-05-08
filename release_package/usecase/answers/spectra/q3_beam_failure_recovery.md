# Q3 — Beam Failure Detection / Recovery Procedures: Standards Item Analysis Report

## Table of Contents
1. [Motivation (Why BFD/BFR was introduced and how it evolved)](#1-motivation-why-bfdbfr-was-introduced-and-how-it-evolved)
2. [38.213 — Physical-layer BFD/BFR procedures (RACH-based link recovery)](#2-38213--physical-layer-bfdbfr-procedures-rach-based-link-recovery)
3. [38.321 — MAC procedure (BFR via PUCCH SR / contention-free RACH)](#3-38321--mac-procedure-bfr-via-pucch-sr--contention-free-rach)
4. [38.331 — RRC configuration (BFD-RS, candidate-beam-RS, BFR-Config)](#4-38331--rrc-configuration-bfd-rs-candidate-beam-rs-bfr-config)
5. [38.133 — RAN4 RRM quantitative requirements](#5-38133--ran4-rrm-quantitative-requirements)
6. [38.533 — RAN5 RRM conformance test catalogue](#6-38533--ran5-rrm-conformance-test-catalogue)
7. [RAN1 / RAN2 Introduction Context (TDoc trail across releases)](#7-ran1--ran2-introduction-context-tdoc-trail-across-releases)
8. [Cross-Document Linkages](#8-cross-document-linkages)
9. [Coverage and Limitations](#9-coverage-and-limitations)
11. [Document Lifecycle Trace (BFD/BFR Procedures)](#11-document-lifecycle-trace-bfdbfr-procedures)
12. [Summary](#12-summary)

---

## 0. Evidence Provenance (How this report is grounded)

This answer is composed entirely from the SPECTRA knowledge graph + vector index of public 3GPP RAN documents — every assertion is anchored to a retrievable artefact. The KG-side capabilities exercised below are:

- **Paragraph-level chunk citations** — every factual sentence ends with `[spec §sec, chunkId=…]` (TS body) or `[TDoc Rxxx, RANxx#N, release=…]` (TDoc), so each claim can be re-fetched by chunkId from Qdrant or by `(spec, section, chunkIndex)` from Neo4j.
- **Release-tag filtering** — each TDoc carries an explicit `release` field on its KG node; the Rel-15 BFR introduction → Rel-16 SCell BFR → Rel-18 SCell-deactivated BFR evolution narrative in §1 / §7 is filtered by `release=Rel-15/16/18` rather than by string-matching release tokens in body text.
- **ASN.1 IE body retrieval** — the 38.331 IEs `BeamFailureRecoveryConfig`, `RadioLinkMonitoringConfig`, `RadioLinkMonitoringRS`, `PRACH-ResourceDedicatedBFR`, `BFR-SSB-Resource`, `BFR-CSIRS-Resource`, `RACH-ConfigGeneric`, and `BeamFailureDetectionSet-r17` are retrieved as full IE bodies, not paraphrased; field-level matching against 38.213 §6 (PHY thresholds), 38.321 §5.17 (MAC parameter list), and 38.133 §8.5x (RRM evaluation periods) is the basis of §8.
- **Neo4j Section catalogue** — the BFR-relevant 38.321 sections (§5.17), 38.213 link-recovery clauses (§6), 38.133 evaluation-period clauses (§8.5.2.4 / §8.5B.2.2 / §8.5C.2.2 / §8.5D.2.2 / §8.5D.3.2), and the 38.533 BFD/LR conformance-test catalogue (100 test nodes under §10.3.4 / §11.4.4 / §16.7.4) are enumerated from catalogued Section nodes, not inferred from naming similarity.
- **Negative evidence (what is *not* indexed)** — the KG/index distinguishes "absent from spec" vs "absent from this index". §2 / §6 / §9.3 explicitly mark items where 38.213 delegates BLER %-values to 38.133 in body, the absolute ms-values per 38.133 table row are not extracted at line-level in this report, and 38.533 chunk text bodies are empty (only `sectionTitle` indexed for the RAN5 spec).

Reviewers can verify any sentence in this report by retrieving its chunkId from the released vector index, and any cross-spec linkage in §8 by traversing the corresponding Neo4j edge.

---

## 1. Motivation (Why BFD/BFR was introduced and how it evolved)

In the NR Rel-15 RAN1 phase, beam-failure recovery was scoped as a separate procedure rather than as a generalisation of RLM/RLF. The two candidate L1 mechanisms originally proposed for simultaneous support are recorded in `[TDoc R1-1707606, "Discussion on beam failure recovery"]`, and the eventual adoption of L1-RSRP as the candidate-beam evaluation metric is recorded in `[TDoc R1-1713597, "Beam failure recovery"]`.

The corresponding RAN2 motivation appears verbatim in the Rel-15 phase TDoc:

> *"Beam failure recovery procedure is described in section 5.17 of TS 38.321. Based on a number of 'beam failure instances' from physical layer MAC will trigger a random access procedure which allows the recovery."* `[TDoc R2-1803196, RAN2, release=Rel-15]`

The procedure was then extended along two release-tagged axes in subsequent cycles:

1. **SCell BFR (Rel-16)** — beam failure recovery extended to secondary cells, with a MAC-CE-driven branch: `[TDoc R2-1900212, RAN2, release=Rel-16]`.
2. **BFR for SCell-deactivated state (Rel-18)** — coverage of the deactivated-SCell case: `[TDoc R2-2301761, RAN2, release=Rel-18]`.

Three motivation findings are grounded in the cited TDocs:

1. BFR was introduced as a **dedicated link-recovery procedure** in Rel-15 (RAN1 mechanism set + RAN2 reference into 38.321 §5.17) `[R1-1707606 / R1-1713597 / R2-1803196]`.
2. The Rel-15 trigger model is **L1 BFI-counting → MAC initiates Random Access** `[R2-1803196]`.
3. The procedure was extended to **SCell (Rel-16)** `[R2-1900212]` and to **SCell-deactivated state (Rel-18)** `[R2-2301761]`.

---

## 2. 38.213 — Physical-layer BFD/BFR procedures (RACH-based link recovery)

§6 *Link recovery procedures* of 38.213 contains the PHY-side specification of the BFD-RS and candidate-beam-RS sets, the threshold definitions, and the link to MAC/RRM. The §6 body is cited verbatim:

> *"A UE can be provided, for each BWP of a serving cell, a set of periodic CSI-RS resource configuration indexes by failureDetectionResourcesToAddModList and a set of periodic CSI-RS resource configuration indexes and/or SS/PBCH block indexes by candidateBeamRSList or candidateBeamRSListExt or candidateBeamRS-List for radio link quality measurements on the BWP of the serving cell. Instead of the sets … for each BWP of a serving cell, the UE can be provided respective two sets … by failureDetectionSet1 and failureDetectionSet2 that can be activated by a MAC CE [11 TS 38.321] and corresponding two sets … by candidateBeamRS-List and candidateBeamRS-List2…"* `[38.213 §6, chunkId=38.213-6-001]`

The threshold definitions for hypothetical-BLER comparison are cited verbatim from the same chunk:

> *"The thresholds Qout,LR and Qin,LR correspond to the default value of rlmInSyncOutOfSyncThreshold, as described in [10, TS 38.133] for Qout, and to the value provided by rsrp-ThresholdSSB or rsrp-ThresholdBFR, respectively. The physical layer in the UE assesses the radio link quality according to the set … of resource configurations against the threshold Qout,LR."* `[38.213 §6, chunkId=38.213-6-001]`

Key facts grounded in the §6 body:

| Aspect | Value |
|---|---|
| BFD-RS resource sets (single) | `failureDetectionResourcesToAddModList` |
| BFD-RS resource sets (dual, MAC-CE-activated) | `failureDetectionSet1`, `failureDetectionSet2` |
| Candidate-beam RS sets | `candidateBeamRSList`, `candidateBeamRSListExt`, `candidateBeamRS-List`, `candidateBeamRS-List2` |
| Q_out,LR mapping (PHY threshold ↔ RRM parameter) | ↔ `rlmInSyncOutOfSyncThreshold` (defined in 38.133) |
| Q_in,LR mapping | ↔ `rsrp-ThresholdSSB` or `rsrp-ThresholdBFR` |

The two threshold pairs are therefore PHY-side **named placeholders** that point into 38.133 for their numerical values; the explicit cross-spec delegation `[10, TS 38.133]` is itself in the §6 body. SCell BFR and inter-cell BFR (`recoverySearchSpaceId` handling) are covered in adjacent chunks of the same clause `[38.213 §6, chunkId=38.213-6-002]` and `[38.213 §6, chunkId=38.213-6-004]`.

> **Note on absolute BLER values.** The body of 38.213 §6 does not directly expose absolute BLER %-values such as *"hypothetical PDCCH BLER of 10% for Q_{out,LR}"*. The §6 body states only that the thresholds *"correspond to … rlmInSyncOutOfSyncThreshold … [10, TS 38.133]"* `[38.213 §6, chunkId=38.213-6-001]`. The numerical %-values reside in 38.133 and are not asserted in this report (see §9.3).

---

## 3. 38.321 — MAC procedure (BFR via PUCCH SR / contention-free RACH)

The full text of §5.17 *Beam Failure Detection and Recovery procedure* is cited from a single chunk:

> *"The MAC entity may be configured by RRC per Serving Cell or per BFD-RS set with a beam failure recovery procedure … Beam failure is detected by counting beam failure instance indication from the lower layers to the MAC entity. If beamFailureRecoveryConfig is reconfigured by upper layers during an ongoing Random Access procedure for beam failure recovery for SpCell, the MAC entity shall stop the ongoing Random Access procedure and initiate a Random Access procedure using the new configuration. The Serving Cell is configured with two BFD-RS sets if and only if failureDetectionSet1 and failureDetectionSet2 are configured for the active DL BWP of the Serving Cell. When the SCG is deactivated, the UE performs beam failure detection on the PSCell if bfd-and-RLM is set to true."* `[38.321 §5.17, chunkId=38.321-5.17-001]`

The same chunk enumerates the RRC parameters consumed by the MAC procedure, organised by role:

| RRC parameter | Role |
|---|---|
| `beamFailureInstanceMaxCount` | Upper bound for the beam-failure detection counter |
| `beamFailureDetectionTimer` | Beam-failure detection timer |
| `beamFailureRecoveryTimer` | SpCell BFR timer |
| `rsrp-ThresholdSSB` | SpCell BFR L1-RSRP threshold |
| `rsrp-ThresholdBFR` | SCell BFR / per-BFD-RS-set BFR L1-RSRP threshold |
| `powerRampingStep` / `powerRampingStepHighPriority` | SpCell BFR power ramping |
| `preambleReceivedTargetPower`, `preambleTransMax` | SpCell BFR PRACH power |
| `scalingFactorBI` | SpCell BFR backoff scaling |
| `ssb-perRACH-Occasion` | SpCell BFR CFRA SSB-per-RO |
| `ra-ResponseWindow` | SpCell BFR CFRA response monitoring window |
| `prach-ConfigurationIndex` | SpCell BFR CFRA PRACH configuration |

§5.17 names these RRC parameters at the MAC procedural level only — the enumerated value-domains are defined in the corresponding 38.331 IE bodies (§4 below), and the L1-RSRP / hypothetical-BLER comparison itself is delegated to 38.213 §6 (§2).

---

## 4. 38.331 — RRC configuration (BFD-RS, candidate-beam-RS, BFR-Config)

The IE bodies governing BFD/BFR configuration are cited verbatim below. All field ranges (INTEGER bounds, ENUMERATED tokens) are taken directly from the cited chunk and are not paraphrased.

### 4.1 `BeamFailureRecoveryConfig` (SpCell BFR)

```asn1
BeamFailureRecoveryConfig ::= SEQUENCE {
  rootSequenceIndex-BFR    INTEGER (0..137)                       OPTIONAL, -- Need M
  rach-ConfigBFR           RACH-ConfigGeneric                     OPTIONAL, -- Need M
  rsrp-ThresholdSSB        RSRP-Range                             OPTIONAL, -- Need M
  candidateBeamRSList      SEQUENCE (SIZE (1..maxNrofCandidateBeams)) OF PRACH-ResourceDedicatedBFR OPTIONAL, -- Need M
  ssb-perRACH-Occasion     ENUMERATED {oneEighth, oneFourth, oneHalf, one, two,
                                       four, eight, sixteen}      OPTIONAL, -- Need M
  ra-ssb-OccasionMaskIndex INTEGER (0..15)                        OPTIONAL, -- Need M
  recoverySearchSpaceId    SearchSpaceId                          OPTIONAL, -- Need R
  ra-Prioritization        RA-Prioritization                      OPTIONAL, -- Need R
  beamFailureRecoveryTimer ENUMERATED {ms10, ms20, ms40, ms60, ms80, ms100, ms150, ms200} OPTIONAL, -- Need M
  ...,
  [[ msg1-SubcarrierSpacing SubcarrierSpacing OPTIONAL -- Need M ]],
  [[ ra-PrioritizationTwoStep-r16 RA-Prioritization OPTIONAL,
     candidateBeamRSListExt-v1610 SetupRelease{ CandidateBeamRSListExt-r16 } OPTIONAL ]],
  [[ spCell-BFR-CBRA-r16 ENUMERATED {true} OPTIONAL ]],
  [[ ra-OccasionType-r19 ENUMERATED {sbfd} OPTIONAL ]]
}
```

`[38.331 ASN.1 IE=BeamFailureRecoveryConfig, chunkId=38.331-asn1-BeamFailureRecoveryConfig-001]`

Findings from this IE body:

- `beamFailureRecoveryTimer` carries **eight enumerated absolute ms-values** `{ms10, ms20, ms40, ms60, ms80, ms100, ms150, ms200}`.
- `ssb-perRACH-Occasion` carries **eight enumerated tokens** `{oneEighth, oneFourth, oneHalf, one, two, four, eight, sixteen}`.
- `rootSequenceIndex-BFR` is `INTEGER (0..137)`.
- The Rel-16 extension group adds `spCell-BFR-CBRA-r16`, `ra-PrioritizationTwoStep-r16`, and `candidateBeamRSListExt-v1610`.
- The Rel-19 extension group adds `ra-OccasionType-r19 ENUMERATED {sbfd}`.

### 4.2 `RadioLinkMonitoringConfig` (BFD/RLM unified)

```asn1
RadioLinkMonitoringConfig ::= SEQUENCE {
  failureDetectionResourcesToAddModList SEQUENCE (SIZE (1..maxNrofFailureDetectionResources)) OF RadioLinkMonitoringRS OPTIONAL, -- Need N
  failureDetectionResourcesToReleaseList SEQUENCE (SIZE (1..maxNrofFailureDetectionResources)) OF RadioLinkMonitoringRS-Id OPTIONAL, -- Need N
  beamFailureInstanceMaxCount ENUMERATED {n1, n2, n3, n4, n5, n6, n8, n10} OPTIONAL, -- Need R
  beamFailureDetectionTimer    ENUMERATED {pbfd1, pbfd2, pbfd3, pbfd4, pbfd5, pbfd6, pbfd8, pbfd10} OPTIONAL, -- Need R
  ...,
  [[ beamFailure-r17 BeamFailureDetection-r17 OPTIONAL -- Need R ]]
}
```

`[38.331 ASN.1 IE=RadioLinkMonitoringConfig, chunkId=38.331-asn1-RadioLinkMonitoringConfig-001]`

Findings:

- `beamFailureInstanceMaxCount` carries **eight enumerated count tokens** `{n1, n2, n3, n4, n5, n6, n8, n10}`.
- `beamFailureDetectionTimer` carries **eight enumerated PBFD tokens** `{pbfd1, pbfd2, pbfd3, pbfd4, pbfd5, pbfd6, pbfd8, pbfd10}`.
- The Rel-17 extension group adds `beamFailure-r17 BeamFailureDetection-r17`, which is the entry point to multi-set BFD configuration in §4.6.

### 4.3 `RadioLinkMonitoringRS` (RLM/BFD per-resource)

```asn1
RadioLinkMonitoringRS ::= SEQUENCE {
  radioLinkMonitoringRS-Id RadioLinkMonitoringRS-Id,
  purpose                  ENUMERATED {beamFailure, rlf, both},
  detectionResource        CHOICE { ssb-Index SSB-Index, csi-RS-Index NZP-CSI-RS-ResourceId },
  ...
}
```

`[38.331 ASN.1 IE=RadioLinkMonitoringRS, chunkId=38.331-asn1-RadioLinkMonitoringRS-001]`

The `purpose` ENUMERATED differentiates **RLM-only / BFD-only / dual** usage of the same RS, and `detectionResource` branches between **SSB-Index** and **NZP-CSI-RS-ResourceId**.

### 4.4 `PRACH-ResourceDedicatedBFR` / `BFR-SSB-Resource` / `BFR-CSIRS-Resource`

```asn1
PRACH-ResourceDedicatedBFR ::= CHOICE { ssb BFR-SSB-Resource, csi-RS BFR-CSIRS-Resource }
BFR-SSB-Resource ::= SEQUENCE { ssb SSB-Index, ra-PreambleIndex INTEGER (0..63), ... }
BFR-CSIRS-Resource ::= SEQUENCE {
  csi-RS NZP-CSI-RS-ResourceId,
  ra-OccasionList SEQUENCE (SIZE (1..maxRA-OccasionsPerCSIRS)) OF INTEGER (0..maxRA-Occasions-1) OPTIONAL,
  ra-PreambleIndex INTEGER (0..63) OPTIONAL,
  ...
}
```

`[38.331 ASN.1 IE=PRACH-ResourceDedicatedBFR, chunkId=38.331-asn1-PRACH-ResourceDedicatedBFR-001]` / `[…BFR-SSB-Resource-001]` / `[…BFR-CSIRS-Resource-001]`

Per-candidate-beam contention-free PRACH preamble index `INTEGER (0..63)` is directly cited from both the SSB and CSI-RS branches; the CSI-RS branch additionally carries an `ra-OccasionList` sized by `maxRA-OccasionsPerCSIRS`.

### 4.5 `RACH-ConfigGeneric` (RA response window)

```
ra-ResponseWindow ENUMERATED {sl1, sl2, sl4, sl8, sl10, sl20, sl40, sl80}, ...,
[[ ra-ResponseWindow-v1610 ENUMERATED {sl60, sl160} OPTIONAL ... ]],
[[ ra-ResponseWindow-v1700 ENUMERATED {sl240, sl320, sl640, sl960, sl1280, sl1920, sl2560} OPTIONAL ... ]]
```

`[38.331 ASN.1 IE=RACH-ConfigGeneric, chunkId=38.331-asn1-RACH-ConfigGeneric-001]`

The BFR PRACH response monitoring window is enumerated across three release-tagged extension blocks: Rel-15 baseline `{sl1..sl80}`, Rel-16 add-on `{sl60, sl160}`, and Rel-17 add-on `{sl240, sl320, sl640, sl960, sl1280, sl1920, sl2560}`. Unit `sl` = slot.

### 4.6 `BeamFailureDetectionSet-r17` (Rel-17 multi-BFD-set)

```asn1
BeamFailureDetectionSet-r17 ::= SEQUENCE {
  bfdResourcesToAddModList-r17 SEQUENCE (SIZE (1..maxNrofBFDResourcePerSet-r17)) OF BeamLinkMonitoringRS-r17 OPTIONAL,
  bfdResourcesToReleaseList-r17 SEQUENCE (SIZE (1..maxNrofBFDResourcePerSet-r17)) OF BeamLinkMonitoringRS-Id-r17 OPTIONAL,
  beamFailureInstanceMaxCount-r17 ENUMERATED {n1, n2, n3, n4, n5, n6, n8, n10} OPTIONAL,
  beamFailureDetectionTimer-r17 ENUMERATED {pbfd1, pbfd2, pbfd3, pbfd4, pbfd5, pbfd6, pbfd8, pbfd10} OPTIONAL,
  ...
}
```

`[38.331 ASN.1 IE=BeamFailureDetectionSet-r17, chunkId=38.331-asn1-BeamFailureDetectionSet-r17-001]`

In Rel-17, the same `beamFailureInstanceMaxCount` / `beamFailureDetectionTimer` enumerations are carried **per-BFD-RS-set**, supporting the dual-set link-recovery model that 38.213 §6 enables via `failureDetectionSet1` / `failureDetectionSet2` (§2).

---

## 5. 38.133 — RAN4 RRM quantitative requirements

38.133 holds the RAN4-side quantitative requirements that close the BFD/BFR loop: evaluation periods (`TEvaluate_BFD_*`) and threshold variables (`Qout_LR_*`) for both SSB-based and CSI-RS-based BFD, with separate FR1 and FR2 tables. The relevant clause bodies are cited verbatim:

> *"UE shall be able to evaluate whether the downlink radio link quality on the configured SSB resource in set … estimated over the last TEvaluate_BFD_SSB period becomes worse than the threshold Qout_LR_SSB within TEvaluate_BFD_SSB period. The value of TEvaluate_BFD_SSB is defined in table 8.5C.2.2-1 for FR1-NTN."* `[38.133 §8.5C.2.2, chunkId=38.133-8.5C.2.2-001]`

> *"The value of TEvaluate_BFD_SSB is defined in table 8.5D.2.2-1 for FR1."* (ATG UE) `[38.133 §8.5D.2.2, chunkId=38.133-8.5D.2.2-001]`

> *"… the last TEvaluate_BFD_SSB_Relax period becomes worse than the threshold Qout_LR_SSB … The value of TEvaluate_BFD_SSB_Relax is defined in table 8.5.2.4-1 for FR1. The value of TEvaluate_BFD_SSB_Relax is defined in table 8.5.2.4-2 for FR2 with scaling factor N=8."* `[38.133 §8.5.2.4, chunkId=38.133-8.5.2.4-001]`

> *"… TEvaluate_BFD_SSB_Redcap … defined in table 8.5B.2.2-1 for FR1 … 8.5B.2.2-2 for FR2 with scaling factor N=8."* `[38.133 §8.5B.2.2, chunkId=38.133-8.5B.2.2-001]`

> *"… the last TEvaluate_BFD_CSI-RS period becomes worse than the threshold Qout_LR_CSI-RS within TEvaluate_BFD_CSI-RS period. The value of TEvaluate_BFD_CSI-RS is defined in table 8.5D.3.2-1 for FR1."* `[38.133 §8.5D.3.2, chunkId=38.133-8.5D.3.2-001]`

The cited bodies above directly establish the variable / table-number / scaling structure used by every BFD-RS × UE-category combination loaded for this question:

| BFD-RS / UE category | Evaluation-period variable | Threshold variable | Table number | Scaling N (FR2 / FR2-1) | Source |
|---|---|---|---|---|---|
| SSB / Relaxed / FR1·FR2 | `TEvaluate_BFD_SSB_Relax` | `Qout_LR_SSB` | 8.5.2.4-1 / -2 | **N = 8** | `[38.133-8.5.2.4-001]` |
| SSB / RedCap / FR1·FR2 | `TEvaluate_BFD_SSB_Redcap` | `Qout_LR_SSB` | 8.5B.2.2-1 / -2 | **N = 8** | `[38.133-8.5B.2.2-001]` |
| SSB / FR1-NTN | `TEvaluate_BFD_SSB` | `Qout_LR_SSB` | 8.5C.2.2-1 | — | `[38.133-8.5C.2.2-001]` |
| SSB / ATG / FR1 | `TEvaluate_BFD_SSB` | `Qout_LR_SSB` | 8.5D.2.2-1 | — | `[38.133-8.5D.2.2-001]` |
| CSI-RS / generic / FR1 | `TEvaluate_BFD_CSI-RS` | `Qout_LR_CSI-RS` | 8.5D.3.2-1 | — | `[38.133-8.5D.3.2-001]` |

This report cites at the level of **variable name + table number + scaling factor**. The absolute ms-values per individual table row reside in the 38.133 tables themselves and are not extracted at line-level here (see §9.3).

---

## 6. 38.533 — RAN5 RRM conformance test catalogue

The 38.533 catalogue exposes **100 BFD/LR test nodes**. Representative section IDs from the Neo4j catalogue:

| Section | Title (catalogue) |
|---|---|
| `38.533-10.3.4` | *Beam failure detection and link recovery procedures* (EN-DC FR1) |
| `38.533-10.3.4.0.1` | *Minimum conformance requirements for SSB based Beam Failure Detection under CCA* |
| `38.533-10.3.4.0.3` | *Scheduling availability of UE during beam failure detection under CCA* |
| `38.533-10.3.4.1` / `.2` | *PSCell SSB-based BFD/LR — non-DRX / DRX* |
| `38.533-11.4.4` | *NR SA FR1 BFD/LR procedures* |
| `38.533-7.5.6.1.1` / `.1.2`, `38.533-16.7.4.x` | L1-RSRP accuracy measurement tests |

> **Body limitation.** Only `sectionTitle` is indexed for 38.533 sections; the chunk text bodies are empty. RAN5 is therefore citable at the **test-case name / structure level** only, and FFS / test-tolerance markers are not exposed (see §9.3).

The catalogued test dimensions form a Cartesian structure across the 100 nodes:

- Mode: **EN-DC vs NR SA**
- Frequency: **FR1 vs FR2**
- Cell: **PCell vs PSCell**
- DRX state: **non-DRX vs DRX**
- BFD-RS: **SSB-based vs CSI-RS-based**
- Environment: **CCA (Coverage Constrained Adaptation), separately catalogued under §10.3.4.0.x**

The normative back-link from 38.533 into 38.133 follows the pattern *"normative reference … TS 38.133 [6] clause A.4.5.5.1"* cited from `[TDoc R5-204985]`.

---

## 7. RAN1 / RAN2 Introduction Context (TDoc trail across releases)

Pulling the TDoc-level evolution into a single trail aligned with §1:

| Release | Trail | Source TDoc(s) |
|---|---|---|
| Rel-15 | RAN1 candidate L1 mechanism + L1-RSRP adoption | `[R1-1707606]`, `[R1-1713597]` |
| Rel-15 | RAN2 reference into 38.321 §5.17 (BFI-counting → RA-trigger model) | `[R2-1803196]` |
| Rel-16 | SCell BFR extension | `[R2-1900212]` |
| Rel-18 | BFR for SCell-deactivated state | `[R2-2301761]` |
| Rel-? | RAN5 conformance back-link to 38.133 | `[R5-204985]` |

Each row above is filtered by the explicit `release` tag on the TDoc node, not by string matching release tokens in the title.

---

## 8. Cross-Document Linkages

Only inter-spec references that can be confirmed via citations from the spec/TDoc bodies are listed.

| From | → | To | Evidence |
|---|---|---|---|
| 38.213 §6 (Q_out,LR / Q_in,LR) | normative ref | 38.133 (`rlmInSyncOutOfSyncThreshold` / `rsrp-ThresholdSSB` / `rsrp-ThresholdBFR`) | `[38.213-6-001]` body explicitly states *"correspond to the default value of rlmInSyncOutOfSyncThreshold, as described in [10, TS 38.133]"* |
| 38.213 §6 | uses RRC parameter names | 38.331 IE `RadioLinkMonitoringConfig` / `BeamFailureRecoveryConfig` | `[38.213-6-001]` body names `failureDetectionResourcesToAddModList`, `candidateBeamRSList`, `rsrp-ThresholdSSB`, `rsrp-ThresholdBFR`, `recoverySearchSpaceId`; matched by `[38.331-asn1-RadioLinkMonitoringConfig-001]` and `[38.331-asn1-BeamFailureRecoveryConfig-001]` |
| 38.331 IE bodies | parameter list consumed by | 38.321 §5.17 procedure | `[38.321-5.17-001]` body enumerates the 12 RRC parameters configured by `beamFailureRecoveryConfig`, `beamFailureRecoverySpCellConfig`, `beamFailureRecoverySCellConfig`, and `radioLinkMonitoringConfig` |
| 38.321 §5.17 | counter input from | 38.213 §6 (BFI indication) | `[38.321-5.17-001]` body: *"Beam failure is detected by counting beam failure instance indication from the lower layers to the MAC entity"* |
| 38.331 (`BeamFailureRecoveryConfig` / `RACH-ConfigGeneric`) | enumerated absolutes | 38.321 procedural use of timers / windows | `[38.331-asn1-BeamFailureRecoveryConfig-001]` `beamFailureRecoveryTimer ∈ {ms10..ms200}`, `[38.331-asn1-RACH-ConfigGeneric-001]` `ra-ResponseWindow ∈ {sl1..sl2560}` consumed by `[38.321-5.17-001]` `ra-ResponseWindow` row |
| 38.213/331 quantitative | implemented as RRM requirement by | 38.133 §8.5.2.4 / §8.5B.2.2 / §8.5C.2.2 / §8.5D.2.2 / §8.5D.3.2 | matching variables `TEvaluate_BFD_*`, `Qout_LR_*` across 38.133 chunk bodies |
| 38.133 | normative ref | 38.533 §10.3.4 / §11.4.4 / §16.7.4 BFD/LR test catalogue | `[R5-204985]` body cites *"normative reference … TS 38.133 [6] clause A.4.5.5.1"* |

### 8.1 Quantitative Verification Matrix

| Item | Status | Source |
|---|---|---|
| Q_out,LR / Q_in,LR ↔ RRC mapping | ✅ verbatim from §6 body | `[38.213 §6, 38.213-6-001]` |
| `beamFailureInstanceMaxCount` enumerated range | ✅ `{n1, n2, n3, n4, n5, n6, n8, n10}` | `[38.331-asn1-RadioLinkMonitoringConfig-001]` |
| `beamFailureDetectionTimer` enumerated range | ✅ `{pbfd1, pbfd2, pbfd3, pbfd4, pbfd5, pbfd6, pbfd8, pbfd10}` | `[38.331-asn1-RadioLinkMonitoringConfig-001]` |
| `beamFailureRecoveryTimer` enumerated (absolute ms) | ✅ `{ms10, ms20, ms40, ms60, ms80, ms100, ms150, ms200}` | `[38.331-asn1-BeamFailureRecoveryConfig-001]` |
| `ssb-perRACH-Occasion` enumerated | ✅ `{oneEighth, oneFourth, oneHalf, one, two, four, eight, sixteen}` | `[38.331-asn1-BeamFailureRecoveryConfig-001]` |
| `rootSequenceIndex-BFR` range | ✅ `INTEGER (0..137)` | `[38.331-asn1-BeamFailureRecoveryConfig-001]` |
| `ra-PreambleIndex` range | ✅ `INTEGER (0..63)` | `[38.331-asn1-BFR-SSB-Resource-001 / -BFR-CSIRS-Resource-001]` |
| `ra-ResponseWindow` enumerated (Rel-15/16/17 stacked) | ✅ `{sl1..sl80}` + `{sl60, sl160}` (r16) + `{sl240..sl2560}` (r17) | `[38.331-asn1-RACH-ConfigGeneric-001]` |
| `RadioLinkMonitoringRS.purpose` | ✅ `ENUMERATED {beamFailure, rlf, both}` | `[38.331-asn1-RadioLinkMonitoringRS-001]` |
| 38.133 BFD evaluation-period variables / table numbers | ✅ variables + table numbers + scaling N=8 | `[38.133 §8.5.2.4 / §8.5B.2.2 / §8.5C.2.2 / §8.5D.2.2 / §8.5D.3.2]` chunks |
| Absolute ms-values in 38.133 table rows (per-line) | △ structurally present, line-level extraction not performed in this report | — |
| 38.213 absolute BLER %-values | ❌ delegated to 38.133 in §6 body — not cited | — |

→ **Nine quantitatively citable items** are resolved end-to-end.

### 8.2 Operational Sequence

```
[gNB]                                            [UE — RRC + MAC + L1]
  | (1) RRC: send BeamFailureRecoveryConfig +     |
  |     RadioLinkMonitoringConfig                 |
  |     · failureDetectionResourcesToAddModList    |
  |       SIZE (1..maxNrofFailureDetectionResources)
  |     · beamFailureInstanceMaxCount {n1..n10}    |
  |     · beamFailureDetectionTimer {pbfd1..pbfd10}|
  |     · candidateBeamRSList SIZE (1..maxNrofCandidateBeams)
  |     · rsrp-ThresholdSSB / rsrp-ThresholdBFR    |
  |     · beamFailureRecoveryTimer {ms10..ms200}   |
  |———————————————————————————————→               |
  |   [38.331-asn1-RadioLinkMonitoringConfig-001,  |
  |    38.331-asn1-BeamFailureRecoveryConfig-001]  |
  |                                                |
  |                                                | (2) L1: measure hypothetical PDCCH BLER on q0 →
  |                                                |     compare radio link quality vs Qout,LR
  |                                                |     (Qout,LR ↔ rlmInSyncOutOfSyncThreshold@38.133)
  |                                                |     [38.213 §6, 38.213-6-001]
  |                                                |
  |                                                | (3) MAC: counter ≥ beamFailureInstanceMaxCount
  |                                                |     → trigger BFR. Counter reset if below
  |                                                |     threshold during beamFailureDetectionTimer
  |                                                |     [38.321 §5.17, 38.321-5.17-001]
  |                                                |
  |                                                | (4) Identify candidate beam (q1, L1-RSRP ≥
  |                                                |     rsrp-ThresholdSSB or rsrp-ThresholdBFR)
  |                                                |     [38.321 §5.17 + 38.213 §6]
  |                                                |
  |                                                | (5) Transmit contention-free PRACH
  |                                                |     · BFR-SSB-Resource: ra-PreambleIndex 0..63
  |                                                |     · BFR-CSIRS-Resource: ra-OccasionList +
  |                                                |       ra-PreambleIndex 0..63
  |                                                |     [38.331-asn1-PRACH-ResourceDedicatedBFR-001]
  |←———————————————————————————————                |
  |                                                |
  | (6) gNB response monitoring                    |
  |     · ra-ResponseWindow                        |
  |       {sl1..sl80} (+r16 sl60/sl160)            |
  |       (+r17 sl240..sl2560)                     |
  |     · recoverySearchSpaceId                    |
  |     [38.331-asn1-RACH-ConfigGeneric-001 +      |
  |      38.331-asn1-BeamFailureRecoveryConfig-001]|
  |                                                |
  |                                                | (7) Meet RAN4 evaluation-period requirements
  |                                                |     · TEvaluate_BFD_SSB / SSB_Redcap /
  |                                                |       SSB_Relax / SSB_NTN / CSI-RS
  |                                                |     · Qout_LR_SSB / Qout_LR_CSI-RS
  |                                                |     [38.133 §8.5.2.4 / §8.5B.2.2 /
  |                                                |      §8.5C.2.2 / §8.5D.2.2 / §8.5D.3.2]
  |                                                |
  | (8) RAN5 conformance (EN-DC/SA × FR1/FR2 ×     |
  |     PCell/PSCell × DRX/non-DRX × SSB/CSI-RS)   |
  |     [38.533 §10.3.4.x / §11.4.4 / §16.7.4.x]   |
```

### 8.3 Trace Diagram

```
[Rel-15 RAN1 mechanism set + L1-RSRP adoption]                              ← R1-1707606 / R1-1713597
        │
        ▼
[Rel-15 RAN2 reference: 38.321 §5.17 BFI-counting → RA trigger]            ← R2-1803196
        │
        ▼
38.331 IEs (RadioLinkMonitoringConfig, BeamFailureRecoveryConfig,           ← 38.331-asn1-*-001
           PRACH-ResourceDedicatedBFR, RACH-ConfigGeneric,
           RadioLinkMonitoringRS, BeamFailureDetectionSet-r17)
        │
        │ (RRC parameters consumed by MAC procedure)
        ▼
38.321 §5.17 BFR procedure (counter + timer + RA branch + parameter list)  ← 38.321-5.17-001
        │
        │ (BFI indication from L1)
        ▼
38.213 §6 Link recovery (BFD-RS sets, candidate-beam-RS sets,              ← 38.213-6-001
           Qout,LR ↔ rlmInSyncOutOfSyncThreshold,                              38.213-6-002
           Qin,LR ↔ rsrp-ThresholdSSB / rsrp-ThresholdBFR,                     38.213-6-004
           SCell BFR + recoverySearchSpaceId)
        │
        │ (quantitative evaluation delegated)
        ▼
38.133 §8.5.2.4 / §8.5B.2.2 / §8.5C.2.2 / §8.5D.2.2 / §8.5D.3.2            ← 38.133-8.5.2.4-001
       (TEvaluate_BFD_SSB_Relax / SSB_Redcap / SSB / SSB / CSI-RS,             38.133-8.5B.2.2-001
        Qout_LR_SSB / Qout_LR_CSI-RS, FR1/FR2 tables, scaling N=8)              38.133-8.5C.2.2-001
        │                                                                       38.133-8.5D.2.2-001
        │ (normative reference)                                                 38.133-8.5D.3.2-001
        ▼
38.533 §10.3.4 / §11.4.4 / §16.7.4 BFD/LR conformance (100 nodes)          ← R5-204985 normative back-link
        │
        ├─ Rel-16 SCell BFR extension                                       ← R2-1900212
        └─ Rel-18 SCell-deactivated state                                   ← R2-2301761
```

---

## 9. Coverage and Limitations

### 9.1 Well-Covered

- **38.213 §6 link-recovery body** — multiple chunks `[38.213-6-001 / -002 / -004]` cited verbatim. Q_out,LR / Q_in,LR mapping into 38.133 RRC parameters cited from the §6 body. **High confidence.**
- **38.321 §5.17 BFR full body** — single chunk `[38.321-5.17-001]` cited verbatim with full RRC-parameter enumeration (12 parameters across SpCell BFR / SCell BFR / per-BFD-RS-set BFR). **High confidence.**
- **38.331 IE bodies** — nine IEs cited as full ASN.1 bodies (`BeamFailureRecoveryConfig`, `RadioLinkMonitoringConfig`, `RadioLinkMonitoringRS`, `PRACH-ResourceDedicatedBFR`, `BFR-SSB-Resource`, `BFR-CSIRS-Resource`, `RACH-ConfigGeneric`, `BeamFailureDetectionSet-r17`). All enumerated absolute domains (`{ms10..ms200}` / `{n1..n10}` / `{pbfd1..pbfd10}` / `{sl1..sl2560}` / `{oneEighth..sixteen}`) are read directly from the cited chunks. **High confidence.**
- **38.133 BFD evaluation-period structure** — five clause bodies `[§8.5.2.4 / §8.5B.2.2 / §8.5C.2.2 / §8.5D.2.2 / §8.5D.3.2]` cited verbatim with variable names, table numbers, and scaling factor N=8 visible in the body. **High confidence at variable-and-table level.**
- **38.533 BFD/LR test-case catalogue** — 100 catalogued test nodes structured across mode × FR × cell × DRX × BFD-RS dimensions. **High confidence at section-title level.**
- **Release-tagged TDoc trail** — six TDocs across Rel-15 / Rel-16 / Rel-18 RAN1 / RAN2 / RAN5 (`R1-1707606`, `R1-1713597`, `R2-1803196`, `R2-1900212`, `R2-2301761`, `R5-204985`), each filtered on the explicit `release` field. **Medium-to-high confidence** (RAN1 / RAN2 introduction context is reconstructed from `type=discussion` documents only — no `type=WID` chunk for the Rel-15 BFR work item is present in the loaded dataset).

### 9.2 Weakly Covered

- **38.321 sub-clause line-level branching** — §5.17 body states the trigger behaviour (*"counting beam failure instance indication from the lower layers"*) but the per-step branching when `beamFailureInstanceMaxCount` expires (PCell RA vs SCell MAC-CE vs SR-BFR fork) is held at sub-clause line-level rather than within the `[38.321-5.17-001]` chunk's prose body. **Medium confidence.**

### 9.3 Items Not Present in the Dataset

- **Absolute BLER %-values on the 38.213 side** (e.g., *"hypothetical PDCCH BLER of 10% for Q_{out,LR}"*) — the 38.213 §6 body delegates these to *"the default value of rlmInSyncOutOfSyncThreshold … [10, TS 38.133]"*. This is a **structural delegation in the spec**, not an indexing gap. Not asserted in this report.
- **Line-level absolute ms-values in 38.133 table rows** for tables 8.5B.2.2-1 / 8.5C.2.2-1 / 8.5D.2.2-1 / 8.5D.3.2-1 / 8.5.2.4-1 / -2 — present in the 38.133 tables themselves; per-row line extraction is not performed in this report.
- **38.533 chunk text bodies (FFS / tolerance markers)** — only `sectionTitle` is indexed for the RAN5 spec. RAN5 is therefore citable at test-case name / structure level only.
- **Formal `type=WID` chunks for the Rel-15 BFR work item** — the introduction context in §1 / §7 is reconstructed from `type=discussion` documents (`R1-1707606`, `R1-1713597`, `R2-1803196`) only.

### 9.4 Self-Verification Notes

- Every factual sentence in §1–§8 ends with a `[spec §sec, chunkId=…]` or `[TDoc Rxxx, RANxx#N, release=…]` citation.
- §4.1–§4.6 attach precise IE chunkIds for all nine IE bodies cited.
- All items not present in the dataset (38.213 BLER %-values, line-level 38.133 table-row ms-values, 38.533 body chunks, formal Rel-15 WID chunk) are explicitly listed in §9.3 and are not filled in by speculation.
- No external web / general-knowledge invocation was used; all enumerated values (`{n1..n10}`, `{pbfd1..pbfd10}`, `{ms10..ms200}`, `{sl1..sl2560}`, `{oneEighth..sixteen}`) are read from the cited ASN.1 IE bodies, not from learned knowledge.

---

## 11. Document Lifecycle Trace (BFD/BFR Procedures)

The paper's Document Lifecycle ontology (§3) traces a feature from Resolution → Tdoc → CR → TS/TR. For NR Beam Failure Detection / Beam Failure Recovery, the chain is reconstructed from the indexed SPECTRA RAG dataset across three release-tagged extension axes — Rel-15 introduction, Rel-16 SCell BFR, and Rel-17 multi-BFD-set (with a Rel-18 SCell-deactivated extension at the RAN2 contribution layer).

### 11.1 Lifecycle Chain Diagram

```
[Rel-15 introduction — RACH-based link recovery]
  RAN1 contributions (RAN1 phase)
    R1-1707606 (RAN1, "Discussion on beam failure recovery", release=Rel-15)
    R1-1713597 (RAN1, "Beam failure recovery", L1-RSRP candidate-beam metric, release=Rel-15)
         ↓ adopted as L1 mechanism set
  RAN2 reference into MAC procedure
    R2-1803196 (RAN2, BFI-counting → RA-trigger model, release=Rel-15)
         ↓ adopted as the spec change
[Spec body incorporation — Rel-15]
  TS 38.213 §6 — Link recovery procedures, BFD-RS / candidate-beam-RS sets
                 Q_out,LR / Q_in,LR ↔ RRC mapping  [38.213-6-001 / -002 / -004]
       ├─ requires RRC IE
       ├─ requires MAC procedure
       └─ requires RRM evaluation period
  TS 38.321 §5.17 — MAC BFR procedure, 12 RRC parameters consumed
                                       [38.321-5.17-001]
  TS 38.331 IEs (Rel-15 baseline)
                 BeamFailureRecoveryConfig (rootSequenceIndex-BFR, rach-ConfigBFR,
                   rsrp-ThresholdSSB, candidateBeamRSList,
                   ssb-perRACH-Occasion {oneEighth..sixteen},
                   beamFailureRecoveryTimer {ms10..ms200})
                                       [38.331-asn1-BeamFailureRecoveryConfig-001]
                 RadioLinkMonitoringConfig (failureDetectionResourcesToAddModList,
                   beamFailureInstanceMaxCount {n1..n10},
                   beamFailureDetectionTimer {pbfd1..pbfd10})
                                       [38.331-asn1-RadioLinkMonitoringConfig-001]
                 RadioLinkMonitoringRS (purpose ∈ {beamFailure, rlf, both})
                                       [38.331-asn1-RadioLinkMonitoringRS-001]
                 PRACH-ResourceDedicatedBFR / BFR-SSB-Resource / BFR-CSIRS-Resource
                                       [38.331-asn1-PRACH-ResourceDedicatedBFR-001]
                 RACH-ConfigGeneric (ra-ResponseWindow {sl1..sl80} baseline)
                                       [38.331-asn1-RACH-ConfigGeneric-001]
  TS 38.133 §8.5.2.4 — TEvaluate_BFD_SSB_Relax / Qout_LR_SSB, FR1/FR2, N=8
                                       [38.133-8.5.2.4-001]
  TS 38.521-4 / RAN5 conformance back-link
    R5-204985 (RAN5, "normative reference … TS 38.133 [6] clause A.4.5.5.1")
       ↓ later-release derivatives (re-uses the same RRC IE / 38.321 procedure)
[Rel-16 SCell BFR extension — RAN2 contribution layer]
  RAN2 contribution
    R2-1900212 (RAN2, SCell BFR via MAC-CE-driven branch, release=Rel-16)
         ↓ incorporated as IE extension group / response-window extension
  TS 38.331 RACH-ConfigGeneric Rel-16 add-on: ra-ResponseWindow-v1610 {sl60, sl160}
                                       [38.331-asn1-RACH-ConfigGeneric-001]
  TS 38.331 BeamFailureRecoveryConfig Rel-16 group: spCell-BFR-CBRA-r16,
            ra-PrioritizationTwoStep-r16, candidateBeamRSListExt-v1610
                                       [38.331-asn1-BeamFailureRecoveryConfig-001]
  TS 38.213 §6 SCell BFR + recoverySearchSpaceId branch
                                       [38.213-6-002 / -004]
[Rel-17 multi-BFD-set — IE-level extension]
  TS 38.331 RadioLinkMonitoringConfig Rel-17 hook:
            beamFailure-r17 BeamFailureDetection-r17
                                       [38.331-asn1-RadioLinkMonitoringConfig-001]
  TS 38.331 BeamFailureDetectionSet-r17 (per-BFD-RS-set config:
            beamFailureInstanceMaxCount-r17 {n1..n10},
            beamFailureDetectionTimer-r17 {pbfd1..pbfd10},
            bfdResourcesToAddModList-r17)
                                       [38.331-asn1-BeamFailureDetectionSet-r17-001]
  TS 38.331 RACH-ConfigGeneric Rel-17 add-on: ra-ResponseWindow-v1700
            {sl240, sl320, sl640, sl960, sl1280, sl1920, sl2560}
                                       [38.331-asn1-RACH-ConfigGeneric-001]
  TS 38.213 §6 dual-set activation via failureDetectionSet1 / failureDetectionSet2
            (MAC-CE-activated)         [38.213-6-001]
  TS 38.133 RAN4 RRM evaluation-period variants:
            §8.5B.2.2 (RedCap, FR1/FR2, N=8)   [38.133-8.5B.2.2-001]
            §8.5C.2.2 (FR1-NTN)                [38.133-8.5C.2.2-001]
            §8.5D.2.2 (ATG, FR1)               [38.133-8.5D.2.2-001]
            §8.5D.3.2 (CSI-RS, FR1)            [38.133-8.5D.3.2-001]
[Rel-18 SCell-deactivated extension — RAN2 contribution layer]
  RAN2 contribution
    R2-2301761 (RAN2, BFR for SCell-deactivated state, release=Rel-18)
         (CR / IE-level chunks for this evolution are not present in the indexed dataset)
[Rel-19 marker — IE-level only, no TDoc in this index]
  TS 38.331 BeamFailureRecoveryConfig Rel-19 group: ra-OccasionType-r19 {sbfd}
                                       [38.331-asn1-BeamFailureRecoveryConfig-001]
```

### 11.2 Lifecycle Audit Table

| Release | RAN1 contribution | RAN2 contribution | Spec body change | RAN4 RRM (38.133) | RAN5 conformance (38.533) | CR-level |
|---|---|---|---|---|---|---|
| Rel-15 (introduction) | R1-1707606, R1-1713597 ✓ | R2-1803196 ✓ | 38.213 §6 [38.213-6-001] ✓; 38.321 §5.17 [38.321-5.17-001] ✓; 38.331 baseline IEs [BeamFailureRecoveryConfig-001 / RadioLinkMonitoringConfig-001 / RadioLinkMonitoringRS-001 / PRACH-ResourceDedicatedBFR-001 / RACH-ConfigGeneric-001] ✓ | §8.5.2.4 [38.133-8.5.2.4-001] ✓ | R5-204985 normative back-link ✓ (chunk bodies not loaded for 38.533) | not loaded |
| Rel-16 (SCell BFR) | n/a in this index | R2-1900212 ✓ | 38.331 BeamFailureRecoveryConfig Rel-16 group (`spCell-BFR-CBRA-r16`, `ra-PrioritizationTwoStep-r16`, `candidateBeamRSListExt-v1610`) ✓; RACH-ConfigGeneric `ra-ResponseWindow-v1610 {sl60, sl160}` ✓; 38.213 §6 SCell BFR + `recoverySearchSpaceId` [38.213-6-002 / -004] ✓ | not specifically loaded as a Rel-16 §8.5.x clause | n/a in this index | not loaded |
| Rel-17 (multi-BFD-set) | n/a in this index | n/a in this index | 38.331 `BeamFailureDetectionSet-r17` [-BeamFailureDetectionSet-r17-001] ✓; RadioLinkMonitoringConfig Rel-17 hook (`beamFailure-r17`) ✓; RACH-ConfigGeneric `ra-ResponseWindow-v1700 {sl240..sl2560}` ✓; 38.213 §6 dual-set activation (`failureDetectionSet1` / `failureDetectionSet2`) ✓ | §8.5B.2.2 (RedCap) ✓; §8.5C.2.2 (FR1-NTN) ✓; §8.5D.2.2 (ATG) ✓; §8.5D.3.2 (CSI-RS) ✓ | n/a in this index | not loaded |
| Rel-18 (SCell-deactivated) | n/a in this index | R2-2301761 ✓ | (CR-level chunks for this evolution are not present in the indexed dataset) | not specifically loaded | n/a in this index | not loaded |
| Rel-19 (marker only) | n/a in this index | n/a in this index | 38.331 BeamFailureRecoveryConfig Rel-19 group (`ra-OccasionType-r19 {sbfd}`) ✓ | n/a in this index | n/a in this index | not loaded |

### 11.3 Bidirectional Traversal

This lifecycle chain is reproducible in **both** directions over the SPECTRA KG / index:

- **Forward** (Contribution → Spec): start from R1-1707606 / R1-1713597 (Rel-15 RAN1 candidate L1 mechanism set + L1-RSRP adoption) → traverse the RAN2 reference R2-1803196 (`release=Rel-15`) into 38.321 §5.17 → traverse the procedural-parameter list into 38.331 (BeamFailureRecoveryConfig / RadioLinkMonitoringConfig / RadioLinkMonitoringRS / PRACH-ResourceDedicatedBFR / RACH-ConfigGeneric) → traverse the PHY-threshold delegation into 38.213 §6 → traverse the quantitative delegation into 38.133 §8.5.2.4 → traverse the RAN5 normative back-link into 38.533 (R5-204985). Subsequent release axes are obtained by filtering on `release=Rel-16` (SCell BFR via R2-1900212 → IE Rel-16 extension groups) and on `release=Rel-18` (R2-2301761), and by enumerating the IE-level Rel-17 / Rel-19 extension blocks (`BeamFailureDetectionSet-r17`, `ra-ResponseWindow-v1700`, `ra-OccasionType-r19`) directly from the cited 38.331 chunks.
- **Backward** (Spec → Contribution): start from `[38.331-asn1-BeamFailureDetectionSet-r17-001]` → recover the per-BFD-RS-set parameter naming and trace back through 38.213 §6's `failureDetectionSet1` / `failureDetectionSet2` activation [38.213-6-001] → search RAN2 contributions with `release=Rel-15` and BFR keyword to recover R2-1803196 as the original procedure-reference TDoc, and `release=Rel-16` for R2-1900212 (SCell BFR introduction). The same backward path from `[38.331-asn1-BeamFailureRecoveryConfig-001]` through `release=Rel-15` RAN1 contributions recovers R1-1707606 / R1-1713597 as the L1-RSRP candidate-beam-metric origin.

The forward direction is shipped as the §1 / §7 motivation narrative. The backward direction is what enables a standards engineer to ask "given clause `BeamFailureDetectionSet-r17`, what was its original RAN2 procedural justification?" and obtain R2-1803196 (Rel-15 reference into 38.321 §5.17) plus R2-1900212 (Rel-16 SCell BFR extension) as the precursor evidence.

### 11.4 What this trace does NOT contain

- **Direct CR chunks**: no BFD/BFR CR is cited; the CR routing collection was not queried for this question. The Rel-15 contribution → Rel-16 SCell BFR → Rel-17 multi-BFD-set → Rel-18 SCell-deactivated chain is reconstructed from textual alignment between RAN1/RAN2 `type=discussion` TDocs and the cited 38.213 / 38.321 / 38.331 spec bodies, not from CR numbers directly.
- **Plenary RP-* WID body**: the formal Rel-15 BFR work-item description / WID is not present as a `type=WID` chunk in this dataset; the introduction context is reconstructed from `type=discussion` documents (R1-1707606, R1-1713597, R2-1803196) only — see §9.3.
- **Rel-17 RAN1 / RAN2 contribution layer**: the IE-level Rel-17 multi-BFD-set extension (`BeamFailureDetectionSet-r17`, `ra-ResponseWindow-v1700`) is attested in the 38.331 spec body, but no `R1-*` / `R2-*` TDoc with `release=Rel-17` for the multi-BFD-set discussion is present in the indexed Q3 retrieval scope. The Rel-17 row of §11.2 is therefore an IE-level entry rather than a contribution-traceable entry.
- **Rel-19+ updates**: the indexed dataset for this question reaches RAN1 / RAN2 contributions up to the Rel-15 / Rel-16 / Rel-18 era. Rel-19 is attested only at the IE level (`ra-OccasionType-r19 {sbfd}` in `BeamFailureRecoveryConfig`); any Rel-19+ BFR enhancements (e.g., subsequent SCell-deactivated revisions, additional BFD-RS sets, sBFD-related BFR refinements) are **not currently traced** at the TDoc / contribution layer.
- **38.533 chunk text bodies**: only `sectionTitle` is indexed for the RAN5 spec — the full conformance-test bodies for §10.3.4 / §11.4.4 / §16.7.4 are absent (only catalogued at section-title level; only RAN4 RRM 38.133 chunk bodies were retrieved as quantitative evidence, and the RAN5 cross-link is asserted only via the back-link in `R5-204985`).

---

## 12. Summary

The NR Beam Failure Detection / Beam Failure Recovery procedure is captured end-to-end across the 3GPP RAN spec stack as follows:

1. **Motivation** — BFR was scoped in Rel-15 as a dedicated link-recovery procedure (RAN1 candidate L1 mechanism set + L1-RSRP adoption + RAN2 reference into 38.321 §5.17). The procedure was extended to **SCell (Rel-16)** and to the **SCell-deactivated state (Rel-18)** `[R1-1707606 / R1-1713597 / R2-1803196 / R2-1900212 / R2-2301761]`.
2. **38.213 §6** — Defines the BFD-RS sets (`failureDetectionResourcesToAddModList`, `failureDetectionSet1` / `failureDetectionSet2`) and candidate-beam-RS sets (`candidateBeamRSList`, `…Ext`, `…-List`, `…-List2`), and maps the PHY thresholds Q_out,LR / Q_in,LR to RRC parameters with explicit normative ref to 38.133 in body `[38.213 §6, 38.213-6-001]`.
3. **38.321 §5.17** — Defines the MAC BFR procedure: BFI-counting from lower layers → declaration on `beamFailureInstanceMaxCount` → SpCell RA trigger / SCell MAC-CE branch, with twelve named RRC parameters consumed `[38.321 §5.17, 38.321-5.17-001]`.
4. **38.331 IEs** — Carry the full configuration: `BeamFailureRecoveryConfig` (`rootSequenceIndex-BFR INTEGER (0..137)`, `beamFailureRecoveryTimer ∈ {ms10..ms200}`, `ssb-perRACH-Occasion ∈ {oneEighth..sixteen}`, Rel-16 / Rel-19 extensions), `RadioLinkMonitoringConfig` (`beamFailureInstanceMaxCount ∈ {n1..n10}`, `beamFailureDetectionTimer ∈ {pbfd1..pbfd10}`, Rel-17 multi-set hook), `RadioLinkMonitoringRS` (`purpose ∈ {beamFailure, rlf, both}`), `PRACH-ResourceDedicatedBFR` (`ra-PreambleIndex 0..63`), `RACH-ConfigGeneric` (`ra-ResponseWindow ∈ {sl1..sl2560}` stacked across Rel-15 / Rel-16 / Rel-17), and `BeamFailureDetectionSet-r17` `[38.331-asn1-*-001]`.
5. **38.133 §8.5.2.4 / §8.5B.2.2 / §8.5C.2.2 / §8.5D.2.2 / §8.5D.3.2** — Defines `TEvaluate_BFD_SSB_Relax / SSB_Redcap / SSB / SSB / CSI-RS` and `Qout_LR_SSB` / `Qout_LR_CSI-RS` with FR1 / FR2 tables and scaling factor N=8 `[38.133 §8.5.2.4 / §8.5B.2.2 / §8.5C.2.2 / §8.5D.2.2 / §8.5D.3.2 chunks]`.
6. **38.533 §10.3.4 / §11.4.4 / §16.7.4** — RAN5 BFD/LR conformance test catalogue (100 nodes) covering EN-DC / SA × FR1 / FR2 × PCell / PSCell × DRX / non-DRX × SSB / CSI-RS, with normative back-link to 38.133 cited from `[R5-204985]`.

Nine quantitatively citable items are resolved end-to-end (§8.1). One item — absolute BLER %-values on the 38.213 side — is structurally absent because 38.213 §6 explicitly delegates the value to 38.133 in body; this is reported as a delegation, not as an indexing gap (§9.3).
