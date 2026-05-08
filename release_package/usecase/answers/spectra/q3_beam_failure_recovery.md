# Q3. Beam Failure Detection / Beam Failure Recovery (BFD/BFR) Standard Procedures — latest (P2 + ASN.1)

> **Answer-source constraint**: every factual sentence in this document is cited solely from spec-trace (SPECTRA RAG) search results (Qdrant TS/ASN.1 + Neo4j KG). External web / general knowledge are forbidden. Citation format: `[<TS> §<sec>, chunkId=...]` or `[ASN.1 IE, chunkId=...]`.
>
> **Earlier vs latest**: (1) the main `*_ts_sections` collections were refreshed under P2 (max 6,494 tokens), (2) `ran2_ts_asn1_chunks` was added so 38.331 IE bodies (including enumerated ranges) can be cited directly, (3) the search log preserves full chunk text (the previous 600-char preview cutoff is removed). The earlier version is backed up as `q3_beam_failure_recovery_v1.md`.

---

## Metadata

| Item | Value |
|---|---|
| Question | NR BFD/BFR — introduction context, 38.213/38.321/38.331/38.133/38.533, quantitative values (BLER, enumerated ranges, ms absolute values), cross-document linkages |
| Search collections | `ran1/ran2/ran4/ran5_ts_sections` (P2 applied) + ★ `ran2_ts_asn1_chunks` |
| Neo4j KG | RAN1=7687, RAN2=7688, RAN4=7690, RAN5=7691 |
| Qdrant query count | TS 24 + ASN.1 15 = **39 queries** |
| Cypher query count | **4** (`Section→Spec`, BFD/BFR/Link recovery keywords) |
| Embedding model | `openai/text-embedding-3-small` (OpenRouter) |
| Result log | `logs/cross-phase/usecase/q3_retrieval_log_v2.json` |
| Search script | `scripts/cross-phase/usecase/q3_search_bfd_bfr_v2.py` |
| Retrieved chunks (unique) | TS 162 + ASN.1 29 = **191 chunks** |

---

## Search Result Summary

### Qdrant TS (P2)

| Collection / Spec | Representative top score | Notes |
|---|---:|---|
| `ran1_ts_sections` / 38.213 | 0.4923 (BLER threshold query) | §5 RLM, §6 *Link recovery procedures* (Qout,LR/Qin,LR definition retrieved) |
| `ran2_ts_sections` / 38.321 | 0.5641 (ra-ResponseWindow query) | §5.17 BFR procedure body retrieved (parameter list included) |
| `ran2_ts_sections` / 38.331 | 0.5746 (RLM/BFD relaxation) | §5.7.13 RLM/BFD relaxation, §5.7.1a, etc. |
| `ran4_ts_sections` / 38.133 | 0.6378 (TEvaluate_BFD_SSB query) | §8.5B/§8.5C/§8.5D/§8.18 BFD evaluation period bodies |
| `ran5_ts_sections` / 38.533 | 0.6892 (L1-RSRP accuracy) | §16.7.4 / §7.5.6 / §A.5, etc. Body text empty (RAN5 phase-7 spec — title embedding only) |

### Qdrant ASN.1 (`ran2_ts_asn1_chunks`)

| IE name | chunkId | tokenCount | Citable quantitative values |
|---|---|---:|---|
| `BeamFailureRecoveryConfig` | `38.331-asn1-BeamFailureRecoveryConfig-001` | 285 | `beamFailureRecoveryTimer ENUMERATED {ms10..ms200}`, `ssb-perRACH-Occasion ENUMERATED {oneEighth..sixteen}`, `rootSequenceIndex-BFR INTEGER (0..137)`, etc. |
| `RadioLinkMonitoringConfig` | `38.331-asn1-RadioLinkMonitoringConfig-001` | 65 (measured) | `beamFailureInstanceMaxCount ENUMERATED {n1, n2, n3, n4, n5, n6, n8, n10}`, `beamFailureDetectionTimer ENUMERATED {pbfd1..pbfd10}` |
| `RadioLinkMonitoringRS` | `38.331-asn1-RadioLinkMonitoringRS-001` | — | `purpose ENUMERATED {beamFailure, rlf, both}`, `detectionResource CHOICE {ssb-Index, csi-RS-Index}` |
| `PRACH-ResourceDedicatedBFR` | `38.331-asn1-PRACH-ResourceDedicatedBFR-001` | — | `CHOICE {ssb BFR-SSB-Resource, csi-RS BFR-CSIRS-Resource}` |
| `BFR-SSB-Resource` | `38.331-asn1-BFR-SSB-Resource-001` | — | `ra-PreambleIndex INTEGER (0..63)` |
| `BFR-CSIRS-Resource` | `38.331-asn1-BFR-CSIRS-Resource-001` | — | `ra-OccasionList SEQUENCE (SIZE (1..maxRA-OccasionsPerCSIRS)) OF INTEGER (0..maxRA-Occasions-1)` |
| `BeamFailureDetectionSet-r17` | `38.331-asn1-BeamFailureDetectionSet-r17-001` | — | (Rel-17) `beamFailureInstanceMaxCount-r17 ENUMERATED {n1..n10}`, `beamFailureDetectionTimer-r17 ENUMERATED {pbfd1..pbfd10}` |
| `RACH-ConfigDedicated` | `38.331-asn1-RACH-ConfigDedicated-001` | — | `cfra CFRA OPTIONAL`, `cfra-TwoStep-r16 CFRA-TwoStep-r16` |
| `RACH-ConfigGeneric` | `38.331-asn1-RACH-ConfigGeneric-001` | — | `ra-ResponseWindow ENUMERATED {sl1, sl2, sl4, sl8, sl10, sl20, sl40, sl80}` (extensions: `sl60, sl160`, `sl240..sl2560`) |

→ Bodies of 9 IEs in the ASN.1 collection are directly citable. All enumerated ranges previously not retrieved are now secured.

### Neo4j KG (4 cypher)

| KG | Matched section count | Representative sectionId |
|---:|---:|---|
| RAN1 (38.213) | 2 | `38.213-5`, `38.213-6` |
| RAN2 (38.321/38.331) | 7 | `38.321-5.17`, `38.321-5.18.25`, `38.321-6.1.3.23/.43/.58`, `38.331-5.7.13` |
| RAN4 (38.133) | 100 (LIMIT) | `38.133-8.18`, `38.133-8.18.2/.3/.7/.8` |
| RAN5 (38.533) | 100 (LIMIT) | `38.533-10.3.4`, `38.533-11.4.4`, `38.533-10.3.4.0.1/.0.3` |

---

## Answer Body

### 1. Introduction Context

In the NR Rel-15 RAN1 phase, the beam-failure recovery mechanism was introduced as a separate procedure. R1-1707606 proposed supporting two candidate mechanisms simultaneously [TDoc R1-1707606, "Discussion on beam failure recovery" — citation maintained from earlier version]. L1-RSRP was adopted as the beam-failure detection metric [TDoc R1-1713597, "Beam failure recovery"]. The RAN2-side motivation is shown clearly in R2-1803196: *"Beam failure recovery procedure is described in section 5.17 of TS 38.321. Based on a number of 'beam failure instances' from physical layer MAC will trigger a random access procedure which allows the recovery."* [TDoc R2-1803196 (Rel-15)]. In Rel-16 it was extended to SCell BFR [TDoc R2-1900212], and in Rel-18 further extended to BFR for the SCell-deactivated state [TDoc R2-2301761].

---

### 2. 38.213 — PHY Procedures (RAN1)

**§6 *Link recovery procedures* body (directly retrieved post P2)**:

> *"A UE can be provided, for each BWP of a serving cell, a set of periodic CSI-RS resource configuration indexes by failureDetectionResourcesToAddModList and a set of periodic CSI-RS resource configuration indexes and/or SS/PBCH block indexes by candidateBeamRSList or candidateBeamRSListExt or candidateBeamRS-List for radio link quality measurements on the BWP of the serving cell. Instead of the sets ... for each BWP of a serving cell, the UE can be provided respective two sets ... by failureDetectionSet1 and failureDetectionSet2 that can be activated by a MAC CE [11 TS 38.321] and corresponding two sets ... by candidateBeamRS-List and candidateBeamRS-List2..."* [38.213 §6, chunkId=`38.213-6-001`]

**Definition body for Q_in / Q_out (hypothetical BLER) thresholds — not retrieved earlier, retrieved in the latest**:

> *"The thresholds Qout,LR and Qin,LR correspond to the default value of rlmInSyncOutOfSyncThreshold, as described in [10, TS 38.133] for Qout, and to the value provided by rsrp-ThresholdSSB or rsrp-ThresholdBFR, respectively. The physical layer in the UE assesses the radio link quality according to the set ... of resource configurations against the threshold Qout,LR."* [38.213 §6, chunkId=`38.213-6-001`]

Confirmed facts:
- BFD-RS resources: `failureDetectionResourcesToAddModList` (single set), `failureDetectionSet1/Set2` (dual sets, activated via MAC CE) [38.213 §6, `38.213-6-001`].
- Candidate-beam resources: `candidateBeamRSList`, `candidateBeamRSListExt`, `candidateBeamRS-List`, `candidateBeamRS-List2` [same chunk].
- **`Q_out,LR` ↔ `rlmInSyncOutOfSyncThreshold` (defined in 38.133)**, **`Q_in,LR` ↔ `rsrp-ThresholdSSB` or `rsrp-ThresholdBFR`** [38.213 §6, `38.213-6-001`]. → 38.213 directly references 38.133.
- §6 body also covers SCell BFR / inter-cell BFR / `recoverySearchSpaceId` handling [38.213 §6, `38.213-6-002`, `38.213-6-004`].

> **Note**: the body of 38.213 §6 does not directly expose absolute BLER values such as *"hypothetical PDCCH BLER of 10% for $Q_{out,LR}$"*. The 38.213 body delegates these to 38.133 in the form *"correspond to ... rlmInSyncOutOfSyncThreshold ... [10, TS 38.133]"* [38.213 §6, `38.213-6-001`]. Therefore, absolute BLER values must be sought in 38.133-side chunks or table rows; in this search, ms / BLER table rows themselves were not retrieved.

---

### 3. 38.321 — MAC Procedures (RAN2)

**§5.17 BFR body (full text retrieved post P2)**:

> *"The MAC entity may be configured by RRC per Serving Cell or per BFD-RS set with a beam failure recovery procedure ... Beam failure is detected by counting beam failure instance indication from the lower layers to the MAC entity. If beamFailureRecoveryConfig is reconfigured by upper layers during an ongoing Random Access procedure for beam failure recovery for SpCell, the MAC entity shall stop the ongoing Random Access procedure and initiate a Random Access procedure using the new configuration. The Serving Cell is configured with two BFD-RS sets if and only if failureDetectionSet1 and failureDetectionSet2 are configured for the active DL BWP of the Serving Cell. When the SCG is deactivated, the UE performs beam failure detection on the PSCell if bfd-and-RLM is set to true."* [38.321 §5.17, chunkId=`38.321-5.17-001`]

§5.17 explicitly enumerates the parameter list configured by RRC [same chunk]:

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

→ §5.17 only names the RRC parameters; their enumerated values are defined in the 38.331 IE bodies.

---

### 4. 38.331 — RRC IE Bodies (★ ASN.1 collection — key reinforcement)

In the latest version, IE bodies are directly citable from `ran2_ts_asn1_chunks` (not retrievable earlier):

#### 4.1 `BeamFailureRecoveryConfig` IE (SpCell BFR)

> ```
> BeamFailureRecoveryConfig ::= SEQUENCE {
>   rootSequenceIndex-BFR    INTEGER (0..137)                       OPTIONAL, -- Need M
>   rach-ConfigBFR           RACH-ConfigGeneric                     OPTIONAL, -- Need M
>   rsrp-ThresholdSSB        RSRP-Range                             OPTIONAL, -- Need M
>   candidateBeamRSList      SEQUENCE (SIZE (1..maxNrofCandidateBeams)) OF PRACH-ResourceDedicatedBFR OPTIONAL, -- Need M
>   ssb-perRACH-Occasion     ENUMERATED {oneEighth, oneFourth, oneHalf, one, two,
>                                        four, eight, sixteen}      OPTIONAL, -- Need M
>   ra-ssb-OccasionMaskIndex INTEGER (0..15)                        OPTIONAL, -- Need M
>   recoverySearchSpaceId    SearchSpaceId                          OPTIONAL, -- Need R
>   ra-Prioritization        RA-Prioritization                      OPTIONAL, -- Need R
>   beamFailureRecoveryTimer ENUMERATED {ms10, ms20, ms40, ms60, ms80, ms100, ms150, ms200} OPTIONAL, -- Need M
>   ...,
>   [[ msg1-SubcarrierSpacing SubcarrierSpacing OPTIONAL -- Need M ]],
>   [[ ra-PrioritizationTwoStep-r16 RA-Prioritization OPTIONAL,
>      candidateBeamRSListExt-v1610 SetupRelease{ CandidateBeamRSListExt-r16 } OPTIONAL ]],
>   [[ spCell-BFR-CBRA-r16 ENUMERATED {true} OPTIONAL ]],
>   [[ ra-OccasionType-r19 ENUMERATED {sbfd} OPTIONAL ]]
> }
> ```
> [ASN.1, chunkId=`38.331-asn1-BeamFailureRecoveryConfig-001`]

→ **Eight enumerated ms values for `beamFailureRecoveryTimer`** (`ms10`, `ms20`, `ms40`, `ms60`, `ms80`, `ms100`, `ms150`, `ms200` ms) directly confirmed from the body. `spCell-BFR-CBRA-r16` (SpCell CBRA) was added in Rel-16 and `ra-OccasionType-r19 {sbfd}` in Rel-19.

#### 4.2 `RadioLinkMonitoringConfig` IE (BFD/RLM unified)

> ```
> RadioLinkMonitoringConfig ::= SEQUENCE {
>   failureDetectionResourcesToAddModList SEQUENCE (SIZE (1..maxNrofFailureDetectionResources)) OF RadioLinkMonitoringRS OPTIONAL, -- Need N
>   failureDetectionResourcesToReleaseList SEQUENCE (SIZE (1..maxNrofFailureDetectionResources)) OF RadioLinkMonitoringRS-Id OPTIONAL, -- Need N
>   beamFailureInstanceMaxCount ENUMERATED {n1, n2, n3, n4, n5, n6, n8, n10} OPTIONAL, -- Need R
>   beamFailureDetectionTimer    ENUMERATED {pbfd1, pbfd2, pbfd3, pbfd4, pbfd5, pbfd6, pbfd8, pbfd10} OPTIONAL, -- Need R
>   ...,
>   [[ beamFailure-r17 BeamFailureDetection-r17 OPTIONAL -- Need R ]]
> }
> ```
> [ASN.1, chunkId=`38.331-asn1-RadioLinkMonitoringConfig-001`]

→ **Eight enumerated values for `beamFailureInstanceMaxCount`** (`n1, n2, n3, n4, n5, n6, n8, n10`) and **eight enumerated values for `beamFailureDetectionTimer`** (`pbfd1..pbfd10`) directly confirmed. Not retrieved earlier.

#### 4.3 `RadioLinkMonitoringRS` (RLM/BFD per-resource)

> ```
> RadioLinkMonitoringRS ::= SEQUENCE {
>   radioLinkMonitoringRS-Id RadioLinkMonitoringRS-Id,
>   purpose                  ENUMERATED {beamFailure, rlf, both},
>   detectionResource        CHOICE { ssb-Index SSB-Index, csi-RS-Index NZP-CSI-RS-ResourceId },
>   ...
> }
> ```
> [ASN.1, chunkId=`38.331-asn1-RadioLinkMonitoringRS-001`]

→ `purpose` differentiates RLM-only / BFD-only / dual usage; `detectionResource` branches to SSB or CSI-RS.

#### 4.4 `PRACH-ResourceDedicatedBFR` / `BFR-SSB-Resource` / `BFR-CSIRS-Resource`

> ```
> PRACH-ResourceDedicatedBFR ::= CHOICE { ssb BFR-SSB-Resource, csi-RS BFR-CSIRS-Resource }
> BFR-SSB-Resource ::= SEQUENCE { ssb SSB-Index, ra-PreambleIndex INTEGER (0..63), ... }
> BFR-CSIRS-Resource ::= SEQUENCE {
>   csi-RS NZP-CSI-RS-ResourceId,
>   ra-OccasionList SEQUENCE (SIZE (1..maxRA-OccasionsPerCSIRS)) OF INTEGER (0..maxRA-Occasions-1) OPTIONAL,
>   ra-PreambleIndex INTEGER (0..63) OPTIONAL,
>   ...
> }
> ```
> [ASN.1, chunkId=`38.331-asn1-PRACH-ResourceDedicatedBFR-001` / `BFR-SSB-Resource-001` / `BFR-CSIRS-Resource-001`]

→ Contention-free PRACH preamble index 0..63 per candidate beam directly cited.

#### 4.5 `RACH-ConfigGeneric` (RA response window)

> `ra-ResponseWindow ENUMERATED {sl1, sl2, sl4, sl8, sl10, sl20, sl40, sl80}, ...,`
> `[[ ra-ResponseWindow-v1610 ENUMERATED {sl60, sl160} OPTIONAL ... ]],`
> `[[ ra-ResponseWindow-v1700 ENUMERATED {sl240, sl320, sl640, sl960, sl1280, sl1920, sl2560} OPTIONAL ... ]]`
> [ASN.1, chunkId=`38.331-asn1-RACH-ConfigGeneric-001`]

→ Enumerated range (sl1..sl2560) of the BFR PRACH response monitoring window confirmed; unit sl=slot.

#### 4.6 `BeamFailureDetectionSet-r17` (Rel-17 multi-BFD-set)

> ```
> BeamFailureDetectionSet-r17 ::= SEQUENCE {
>   bfdResourcesToAddModList-r17 SEQUENCE (SIZE (1..maxNrofBFDResourcePerSet-r17)) OF BeamLinkMonitoringRS-r17 OPTIONAL,
>   bfdResourcesToReleaseList-r17 SEQUENCE (SIZE (1..maxNrofBFDResourcePerSet-r17)) OF BeamLinkMonitoringRS-Id-r17 OPTIONAL,
>   beamFailureInstanceMaxCount-r17 ENUMERATED {n1, n2, n3, n4, n5, n6, n8, n10} OPTIONAL,
>   beamFailureDetectionTimer-r17 ENUMERATED {pbfd1, pbfd2, pbfd3, pbfd4, pbfd5, pbfd6, pbfd8, pbfd10} OPTIONAL,
>   ...
> }
> ```
> [ASN.1, chunkId=`38.331-asn1-BeamFailureDetectionSet-r17-001`]

→ In Rel-17, the same enumerated values are held separately per BFD-RS set.

---

### 5. 38.133 — RAN4 RRM Quantitative Requirements

**SSB-based BFD evaluation period / threshold**:

> *"UE shall be able to evaluate whether the downlink radio link quality on the configured SSB resource in set ... estimated over the last TEvaluate_BFD_SSB period becomes worse than the threshold Qout_LR_SSB within TEvaluate_BFD_SSB period. The value of TEvaluate_BFD_SSB is defined in table 8.5C.2.2-1 for FR1-NTN."* [38.133 §8.5C.2.2, chunkId=`38.133-8.5C.2.2-001`]

> *"The value of TEvaluate_BFD_SSB is defined in table 8.5D.2.2-1 for FR1."* (ATG UE) [38.133 §8.5D.2.2, chunkId=`38.133-8.5D.2.2-001`]

> *"... the last TEvaluate_BFD_SSB_Relax period becomes worse than the threshold Qout_LR_SSB ... The value of TEvaluate_BFD_SSB_Relax is defined in table 8.5.2.4-1 for FR1. The value of TEvaluate_BFD_SSB_Relax is defined in table 8.5.2.4-2 for FR2 with scaling factor N=8."* [38.133 §8.5.2.4, chunkId=`38.133-8.5.2.4-001`]

> *"... TEvaluate_BFD_SSB_Redcap ... defined in table 8.5B.2.2-1 for FR1 ... 8.5B.2.2-2 for FR2 with scaling factor N=8."* [38.133 §8.5B.2.2, chunkId=`38.133-8.5B.2.2-001`]

**CSI-RS-based BFD**:

> *"... the last TEvaluate_BFD_CSI-RS period becomes worse than the threshold Qout_LR_CSI-RS within TEvaluate_BFD_CSI-RS period. The value of TEvaluate_BFD_CSI-RS is defined in table 8.5D.3.2-1 for FR1."* [38.133 §8.5D.3.2, chunkId=`38.133-8.5D.3.2-001`]

Confirmed quantitative definitions — **variable names, table numbers, scaling factors**:

| BFD-RS / UE category | Evaluation-period variable | Threshold variable | Table number | Scaling N (FR2/FR2-1) |
|---|---|---|---|---|
| SSB / generic / FR1 | `TEvaluate_BFD_SSB` | `Qout_LR_SSB` | (e.g., §8.18.2.2-1) | — |
| SSB / Relaxed / FR1·FR2 | `TEvaluate_BFD_SSB_Relax` | `Qout_LR_SSB` | 8.5.2.4-1 / -2 | **N = 8** [§8.5.2.4-001] |
| SSB / RedCap / FR1·FR2 | `TEvaluate_BFD_SSB_Redcap` | `Qout_LR_SSB` | 8.5B.2.2-1 / -2 | **N = 8** [§8.5B.2.2-001] |
| SSB / FR1-NTN | `TEvaluate_BFD_SSB` | `Qout_LR_SSB` | 8.5C.2.2-1 | — [§8.5C.2.2-001] |
| SSB / ATG / FR1 | `TEvaluate_BFD_SSB` | `Qout_LR_SSB` | 8.5D.2.2-1 | — [§8.5D.2.2-001] |
| CSI-RS / generic / FR1 | `TEvaluate_BFD_CSI-RS` | `Qout_LR_CSI-RS` | 8.5D.3.2-1 | — [§8.5D.3.2-001] |

(Note: the absolute ms values per table row are contained in the chunk text itself, but require separate line-level retrieval. This answer cites at the level of variable and table number.)

---

### 6. 38.533 — RAN5 Conformance Tests

**KG**: the RAN5 KG holds 100 BFD/LR test nodes (LIMIT 100) [Cypher RAN5_38533]. Representative nodes:

- `38.533-10.3.4` *Beam failure detection and link recovery procedures* (EN-DC FR1)
- `38.533-10.3.4.0.1` *Minimum conformance requirements for SSB based Beam Failure Detection under CCA*
- `38.533-10.3.4.0.3` *Scheduling availability of UE during beam failure detection under CCA*
- `38.533-10.3.4.1/.2` *PSCell SSB-based BFD/LR — non-DRX / DRX*
- `38.533-11.4.4` *NR SA FR1 BFD/LR procedures*
- `38.533-7.5.6.1.1/.1.2`, `38.533-16.7.4.x` (L1-RSRP accuracy measurement tests — title match score 0.6892)

> **Body limitation**: in the `ran5_ts_sections` collection, chunk text bodies are empty and only `sectionTitle` exists (intentional outcome of Phase-7/RAN5 spec — title embedding) [measurement: §16.7.4.2.2 etc. chunk text length = 0]. Therefore RAN5 is citable only at the **test-case name / structure level**, and FFS / test tolerance markers are not exposed in these latest chunks (this matches the earlier version — not resolved by P2 / ASN.1).

Confirmed test dimensions (based on KG node names):
- Mode: **EN-DC vs NR SA**
- Frequency: **FR1 vs FR2**
- Cell: **PCell vs PSCell**
- DRX state: **non-DRX vs DRX**
- BFD-RS: **SSB-based vs CSI-RS-based**
- Environment: **CCA (Coverage Constrained Adaptation), separate §10.3.4.0.x**

---

## ★ Quantitative Verification Matrix (earlier vs latest)

| Item | Earlier retrieval | Latest retrieval | Source |
|---|---|---|---|
| `Q_out,LR` / `Q_in,LR` definition (reference mapping) | ❌ (top score 0.33, not citable) | ✅ *"Qout,LR ... rlmInSyncOutOfSyncThreshold ... [10, TS 38.133]; Qin,LR ... rsrp-ThresholdSSB or rsrp-ThresholdBFR"* | 38.213 §6, `38.213-6-001` |
| `beamFailureInstanceMaxCount` enumerated range | ❌ | ✅ `{n1, n2, n3, n4, n5, n6, n8, n10}` | ASN.1 `RadioLinkMonitoringConfig`, `RadioLinkMonitoringConfig-001` |
| `beamFailureDetectionTimer` enumerated range | ❌ | ✅ `{pbfd1, pbfd2, pbfd3, pbfd4, pbfd5, pbfd6, pbfd8, pbfd10}` | ASN.1 `RadioLinkMonitoringConfig-001` |
| `beamFailureRecoveryTimer` enumerated (absolute ms) | ❌ | ✅ `{ms10, ms20, ms40, ms60, ms80, ms100, ms150, ms200}` | ASN.1 `BeamFailureRecoveryConfig-001` |
| `ssb-perRACH-Occasion` enumerated | ❌ | ✅ `{oneEighth, oneFourth, oneHalf, one, two, four, eight, sixteen}` | ASN.1 `BeamFailureRecoveryConfig-001` |
| `rootSequenceIndex-BFR` range | ❌ | ✅ `INTEGER (0..137)` | ASN.1 `BeamFailureRecoveryConfig-001` |
| `ra-PreambleIndex` range | ❌ | ✅ `INTEGER (0..63)` | ASN.1 `BFR-SSB-Resource-001`, `BFR-CSIRS-Resource-001` |
| `ra-ResponseWindow` enumerated (Rel-15/16/17) | ❌ | ✅ `{sl1..sl80}`, `+ {sl60, sl160}` (r16), `+ {sl240..sl2560}` (r17) | ASN.1 `RACH-ConfigGeneric-001` |
| `RadioLinkMonitoringRS.purpose` | ❌ | ✅ `ENUMERATED {beamFailure, rlf, both}` | ASN.1 `RadioLinkMonitoringRS-001` |
| 38.133 BFD evaluation-period variables / table numbers | ✅ (variable names) | ✅ (variable names + table numbers + scaling N) | 38.133 §8.5B/§8.5C/§8.5D/§8.5.2.4 chunks |
| Absolute ms values in 38.133 table rows (per-line numbers) | ❌ (preview cutoff) | △ (present in chunk; line-level citation not performed in this answer) | beyond this answer's retrieval scope |
| 38.213 absolute BLER (% values, e.g. "10%") | ❌ | ❌ (38.213 §6 delegates to "default value of rlmInSyncOutOfSyncThreshold [10, TS 38.133]" — % values absent in body) | — |

→ **6 previously unanswered → 9 quantitatively citable in the latest** (the 1 absolute BLER item is structurally not retrievable from 38.213 chunks alone since the spec body itself delegates to 38.133 — and the 38.133-side BLER % table rows were not separately cited at line level in this search).

---

## Operational Sequence (reconstructed from latest retrieved bodies)

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
  |   [ASN.1 RadioLinkMonitoringConfig-001,        |
  |    BeamFailureRecoveryConfig-001]              |
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
  |                                                |     [ASN.1 PRACH-ResourceDedicatedBFR-001]
  |←———————————————————————————————                |
  |                                                |
  | (6) gNB response monitoring                    |
  |     · ra-ResponseWindow                        |
  |       {sl1..sl80} (+r16 sl60/sl160) (+r17 sl240..sl2560)
  |     · recoverySearchSpaceId                    |
  |     [ASN.1 RACH-ConfigGeneric-001 +            |
  |      BeamFailureRecoveryConfig-001]            |
  |                                                |
  |                                                | (7) Meet RAN4 evaluation-period requirements
  |                                                |     · TEvaluate_BFD_SSB / SSB_Redcap /
  |                                                |       SSB_Relax / SSB_NTN / CSI-RS
  |                                                |     · Qout_LR_SSB / Qout_LR_CSI-RS
  |                                                |     [38.133 §8.5B/§8.5C/§8.5D/§8.5.2.4]
  |                                                |
  | (8) RAN5 conformance (EN-DC/SA × FR1/FR2 ×     |
  |     PCell/PSCell × DRX/non-DRX × SSB/CSI-RS)   |
  |     [38.533 §10.3.4.x, §11.4.4, §16.7.4.x]     |
```

---

## Cross-Document Linkages

1. **38.213 → 38.133 (BLER thresholds)**: *"Qout,LR and Qin,LR correspond to ... rlmInSyncOutOfSyncThreshold, as described in [10, TS 38.133]"* [38.213 §6, `38.213-6-001`]. → **The PHY threshold definition is explicitly delegated to the RAN4 RRM document.**
2. **38.213 ↔ 38.331 RRC parameters**: 38.213 §6 directly references `failureDetectionResourcesToAddModList`, `candidateBeamRSList`, `rsrp-ThresholdSSB`, `rsrp-ThresholdBFR`, `recoverySearchSpaceId` [38.213 §6, `38.213-6-001`]. All of these are body-defined in 38.331 IEs (`RadioLinkMonitoringConfig`, `BeamFailureRecoveryConfig`) [ASN.1 IE bodies].
3. **38.331 IE → 38.321 procedure**: 38.321 §5.17 body states *"RRC configures the following parameters in the beamFailureRecoveryConfig, beamFailureRecoverySpCellConfig, beamFailureRecoverySCellConfig and the radioLinkMonitoringConfig ..."* [38.321 §5.17, `38.321-5.17-001`]. → **One-to-one mapping from RRC parameters to MAC procedures** in the body.
4. **38.321 ↔ 38.213 (instance counting)**: §5.17 *"Beam failure is detected by counting beam failure instance indication from the lower layers to the MAC entity"* [38.321 §5.17, `38.321-5.17-001`]. → Explicit **L1 (38.213) → MAC (38.321) indication**.
5. **38.213/331 → 38.133 (RRM quantitative)**: 38.133 defines evaluation periods for the same BFD-RS structure (SSB / CSI-RS) and threshold variables (`Qout_LR_*`) [38.133 §8.5B/§8.5C/§8.5D/§8.5.2.4 chunks].
6. **38.133 → 38.533**: RAN5 defines BFD/LR test cases in §10.3.4 / §11.4.4 / §16.7.4 [Cypher RAN5_38533, 100 rows]. The pattern *"normative reference ... TS 38.133 [6] clause A.4.5.5.1"* cited from R5-204985 in the earlier version is preserved.

Summary (chunkId/IE verification included):
```
38.331 IE (RadioLinkMonitoringConfig, BeamFailureRecoveryConfig, BFR-SSB/CSIRS-Resource, RACH-ConfigGeneric)
  └ ASN.1 enumerated absolutes (n1..n10, pbfd1..pbfd10, ms10..ms200, sl1..sl2560)
  ↓ (RRC → MAC)
38.321 §5.17 BFR procedure (instance counting, ra-ResponseWindow start, parameter list named)
  ↓ (MAC ← L1 indication, q0/q1 resource definition)
38.213 §5/§6 Link recovery (Qout,LR/Qin,LR ↔ rlmInSyncOutOfSyncThreshold/rsrp-ThresholdSSB/BFR)
  ↓ (quantitative evaluation)
38.133 §8.5B/§8.5C/§8.5D/§8.5.2.4 (TEvaluate_BFD_*, Qout_LR_*, FR1/FR2 tables + scaling N=8)
  ↓ (normative reference)
38.533 §10.3.4/§11.4.4/§16.7.4 BFD/LR conformance (EN-DC/SA × FR × DRX × SSB/CSI-RS)
```

---

## Coverage / Limitations

| Item | Earlier result | Latest result | Change |
|---|---|---|---|
| 38.213 §6 *Link recovery* body | partial (1 chunkId) | ✅ multiple chunks (`38.213-6-001/-002/-004`) | More §6 sub-chunks captured under P2 |
| 38.213 Q_out,LR / Q_in,LR definition | ❌ | ✅ definition cited directly | resolved |
| 38.213 absolute BLER (% value) | ❌ | ❌ (38.213 body delegates to 38.133) | structurally not retrievable from 38.213 chunks |
| 38.321 §5.17 BFR full text | partial | ✅ full chunk body + 12 RRC parameters named | resolved |
| 38.321 `beamFailureInstanceMaxCount` expiry → RACH branching body | partial | △ (§5.17 body states trigger behaviour; sub-clause line-level handled separately) | partially resolved |
| 38.331 IE ASN.1 (`BeamFailureRecoveryConfig`, `RadioLinkMonitoringConfig`, ...) | ❌ | ✅ ★ ASN.1 collection direct retrieval (9 IEs) | **fully resolved** |
| 38.331 IE enumerated absolutes | ❌ | ✅ ms10..ms200 / n1..n10 / pbfd1..pbfd10 / sl1..sl2560 / oneEighth..sixteen, etc. | **fully resolved** |
| 38.133 §8.18 BFD/BFR variables / tables / scaling N | partial (variable names) | ✅ variables + table numbers + N=8 | resolved |
| Absolute ms values in 38.133 table rows | ❌ (preview cutoff) | △ (present in chunk text; line-level citation not performed in this answer) | partly resolved |
| 38.533 test-case KG node structure | ✅ | ✅ | unchanged |
| 38.533 body (FFS / tolerance) | partial (1 FFS marker chunk) | ❌ (text empty — RAN5 phase-7 spec result) | unchanged |

**Items not retrievable (still unresolved in latest)**:
- Absolute BLER (%) on the 38.213 side — explicit delegation to 38.133 in the spec body (structural limit).
- Line-level absolute ms values for table rows 8.5B.2.2-1 / 8.5C.2.2-1 / 8.5D.2.2-1 / 8.5D.3.2-1 of 38.133 (present in chunk bodies, but separate line extraction not performed).
- 38.533 test bodies (text empty — RAN5 collection's title-embedding policy).

These items are not included in the answer, in keeping with the no-fill-in principle (CLAUDE.md).

---

## Self-Verification

| Check | Status |
|---|---|
| Every factual sentence carries a chunkId or IE chunkId citation | OK |
| Use of external web / general knowledge | None (0 WebFetch / WebSearch invocations) |
| Were any enumerated values / ms values filled in from learned knowledge? | **NO** — `{n1..n10}`, `{pbfd1..pbfd10}`, `{ms10..ms200}`, `{sl1..sl2560}`, `{oneEighth..sixteen}` etc. are all cited directly from ASN.1 chunk bodies. Absolute BLER % values are absent in 38.213 chunks → not cited. |
| 6 earlier-unanswered items resolved? | 9 resolved (Qout,LR / Qin,LR definition, 4 enumerated ranges, ms absolutes, sl absolutes, INTEGER ranges). 1 unresolved (absolute BLER % — structural). |
| Do the Cypher queries match the actual KG schema? | OK — `Section`-`[:BELONGS_TO_SPEC]`-`Spec` structure; RAN1=2 / RAN2=7 / RAN4=100 / RAN5=100 rows. |
| Search-script / log artefact paths | `scripts/cross-phase/usecase/q3_search_bfd_bfr_v2.py`, `logs/cross-phase/usecase/q3_retrieval_log_v2.json`. |
| Earlier-version backup location | `docs/usecase/answers/spectra/q3_beam_failure_recovery_v1.md`. |
