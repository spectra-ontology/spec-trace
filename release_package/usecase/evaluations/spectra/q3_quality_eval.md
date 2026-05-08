# Q3 Quality Evaluation — Beam Failure Detection/Recovery

## Evaluation Metadata

- Evaluation date: 2026-04-29
- Initial answer: `docs/usecase/answers/SPECTRA RAG/q3_beam_failure_recovery.md` (323 lines)
- Retrieval log: `logs/cross-phase/usecase/q3_retrieval_log.json` (TS 27 queries / 270 hits, TDoc 12 queries / 120 hits, Cypher 4 entries)
- Evaluation method: every fact-claim in the initial answer is verified along three axes — (a) existence in the retrieval log, (b) agreement with authoritative sources, (c) whether items the answer flagged as "preview cutoff, not retrieved" were filled in from training knowledge
- Authoritative web sources used:
  - [3GPP TS 38.213 V16.0.0 (castle.cloud mirror)](https://panel.castle.cloud/view_spec/38213-g00/pdf/)
  - [Award Solutions — Is Beam Failure a Connection Drop in 5G Part 1](https://www.awardsolutions.com/portal/resources/beam-failure-part-1)
  - [ShareTechnote — 5G/NR Beam Failure Recovery](https://www.sharetechnote.com/html/5G/5G_BeamFailureRecovery.html)
  - [TechSpec — 38.321 §5.17 Beam Failure Detection and Recovery](https://itecspec.com/spec/3gpp-38-321-5-17-beam-failure-detection-and-recovery-procedure/)
  - [TechSpec — 38.300 §9.2.8 Beam failure detection and recovery](https://itecspec.com/spec/3gpp-38-300-9-2-8-beam-failure-detection-and-recovery/)
  - [WirelessBrew — BFD/BFR procedure 5G NR](https://wirelessbrew.com/5g-nr/5g-mac-layer/beam-failure-detection-and-recovery-procedure-in-5g-nr/)
  - [Justia Patent — SCell BFR Patent #11,909,488](https://patents.justia.com/patent/11909488)
  - [Award Solutions — RLM/BFD thresholds](https://www.awardsolutions.com/portal/resources/beam-failure-part-1)

---

## Five-axis scores (0–5)

| Axis | Score | Summary of evidence |
|---|---:|---|
| A1 Accuracy | 4.5 | Procedures, names, IEs, and variable names all match authoritative sources. Quantitative values (BLER %, ms, enumerated ranges) were intentionally omitted from citations → 0 fabricated numbers. Weakness: although 38.133 chunks were retrieved, the Q_out_LR / Q_in_LR definitions (hypothetical PDCCH BLER 10%/2%) are only marked as "weak direct chunk match", without deeper exploration of whether the values appear in chunk bodies. |
| A2 Coverage | 4.0 | All 6 items (introduction background / 38.213 / 38.321 / 38.331 / 38.133 / 38.533 / linkages) are addressed. Sequence diagram + linkage figure are excellent. Limitation: enumerated ranges (`n1~n10`, `pbfd1~pbfd10`) and ms-unit row of the evaluation period table, although flagged as present in retrieval, end up with 0 actual citations → the user's "quantitative values" axis is satisfied at only ~40%. |
| A3 Citation Integrity | 5.0 | Of the 16 chunks/TDocs cited in the initial answer, **16/16 exist in the retrieval log**. The body quotes match the `text_preview`/`content_preview` of the retrieval log verbatim. R1-1707606, R1-1713597, R2-1803196, R2-1900212, R2-2301761, R2-2407883, R5-204985, 38.213-6-001, 38.321-5.17-001, 38.321-5.1.4-001, 38.133-8.18.2.2-001, 38.133-8.5B.2.2-001, 38.133-8.5D.3.2-001, 38.533-17.5.2.1-001, 38.533-7.5.6.1.2-001, 38.321-6.1.3.30-001 — all verified |
| A4 Hallucination Control | 5.0 | **Top score on the core evaluation axis**. None of the five quantitative items the answer self-flagged as "not retrieved" (BLER 10%/2%, beamFailureInstanceMaxCount range, beamFailureDetectionTimer range, ms row of Table 8.18.2.2-1, 38.533 test tolerance) were filled in. The self-check table explicitly states "**NO** — only variable names and definitions are quoted from chunks; ms-unit values in the rows are not exposed in the preview, so the body does not cite them." Zero training-knowledge leakage |
| A5 Cross-Doc Linkage | 4.5 | The 8-step BFR sequence (RRC config → L1 q0 measurement → MAC instance counting → contention-free PRACH → ra-ResponseWindow → RAN4 evaluation period → RAN5 conformance) is illustrated together with 5 explicit linkage citations. The 38.331↔38.321 link is strongly evidenced via the verbatim quote in R2-2407883: "See also TS 38.321 [3], clause 5.17". Weakness: the L1 indication mechanism from 38.213 → 38.321 is connected only via R2-1803196 (a RAN2 analysis document); chunks like "MAC reports beam failure instance" inside the 38.213 body are not directly cited (the RAN1 spec's PHY indication definition was retrieved weakly) |
| **Overall** | **4.6 / 5** | Citation integrity and hallucination control are perfect; accuracy/coverage/linkage each lose 0.5 due to the policy of not citing quantitative values. The initial answer exemplifies the SPECTRA RAG principle of "only cite facts actually retrieved by the search" |

---

## Quantitative-value verification (BFR core)

| Parameter | Authoritative value | Initial answer handling | Assessment |
|---|---|---|---|
| Q_out,LR BLER threshold | 10% (hypothetical PDCCH, DCI format 1_0, CCE aggregation level 8, 2-symbol CORESET) [Award Solutions, ShareTechnote, TS 38.213 mirror] | Body omits the value; flagged as "coverage limitation: top score 0.33, weak direct chunk match" | ⚠️ Unanswered but accurate (no fabricated value) |
| Q_in,LR BLER threshold | 2% (hypothetical PDCCH, DCI 1_0, CCE aggregation 4) [Award Solutions, ShareTechnote] | Body omits the value | ⚠️ Unanswered but accurate |
| beamFailureInstanceMaxCount range | `{n1, n2, n3, n4, n5, n6, n8, n10}` [ShareTechnote, WirelessBrew] | Variable name only ("BFR triggered when counter ≥ beamFailureInstanceMaxCount" — handled via R2-1803196 citation), enumerated range withheld | ⚠️ Unanswered but accurate |
| beamFailureDetectionTimer range | `{pbfd1, pbfd2, pbfd3, pbfd4, pbfd5, pbfd6, pbfd8, pbfd10}` [ShareTechnote] | Both variable name and range withheld in the body (chunk score low → not in search; recorded in §self-check / "SPECTRA RAG not found" list) | ⚠️ Unanswered (accurate) |
| ra-ResponseWindow range | `{sl1, sl2, sl4, sl8, sl10, sl20, sl40, sl80}` [ShareTechnote] | Only the variable name and link cited (within `BeamFailureRecoveryConfig`); range withheld | ⚠️ Unanswered (accurate) |
| BFD evaluation period (38.133 §8.18.2.2-1) | TEvaluate_BFD_SSB FR1 table body. FR2-1 N=2/4/6, FR2 N=8 [TS 38.133 mirror, retrieval log preview] | Variable name and N values (2,4,6) cited verbatim from chunk. The absolute ms values in table rows are withheld due to preview cutoff — flagged in the §coverage/limitations table | ✅ Partially answered, accurate |
| Qout_LR_SSB threshold (38.133) | RAN4-defined DL link quality threshold (consistent with 38.213 Q_out,LR). 38.133 §8.18.2.2 body variable [retrieval log 8.18.2.2-001] | Variable name cited accurately; absolute value withheld | ✅ Variable-name citation accurate |
| BFR test tolerance (38.533) | 38.533 §17.5.2.1 PC3 / f ≤ 40.8 GHz. §7.5.6.1.2 is *Editor's note: incomplete, FFS, Test tolerance analysis is missing* [retrieval log] | Includes FFS marker verbatim, declares "no definite citation possible" | ✅ Limitation noted accurately |
| BFR PRACH form | Contention-free Random Access Preamble; ra-ResponseWindow inside BeamFailureRecoveryConfig [TS 38.321 §5.1.4] | "BFR PRACH is sent contention-free, response monitoring is controlled by ra-ResponseWindow inside BeamFailureRecoveryConfig" — verbatim from 38.321 §5.1.4 chunk | ✅ Accurate |
| L1-RSRP measurement metric | NR BFD measurement metric is L1-RSRP [R1-1713597] | Verbatim citation of R1-1713597 Proposal 1 | ✅ Accurate |
| Release where SCell BFR was introduced | Rel-16 [Intel patent, RAN1/RAN2 agreement, Justia patent #11,909,488] | R2-1900212 Rel-16 cited — "Current Rel-15 BFR is useless in support of beam failure on the SCell" verbatim | ✅ Accurate |

---

## Claim-by-claim authoritative verification

| # | Initial claim | Cited chunk | Authoritative verdict | Comment |
|---:|---|---|---|---|
| 1 | "In the NR Rel-15 RAN1 phase, a beam-failure recovery mechanism was introduced as a separate procedure" | R1-1707606 (Rel-15) | ✅ Match | Confirmed in the retrieval log: release="Rel-15", agendaItem=7.1.2.2.2 |
| 2 | "Both Mechanism 1 and 2 are supported" — Proposal #1 body | R1-1707606 | ✅ Match | content_preview verbatim match |
| 3 | "L1-RSRP as the measurement metric to detect beam failure" — Proposal 1 | R1-1713597 | ✅ Match | Found exactly in the content_preview. Authoritative sources (ShareTechnote, Award Solutions) also confirm L1-RSRP as the metric |
| 4 | "Beam failure recovery procedure is described in section 5.17 of TS 38.321 ... a number of beam failure instances ... will trigger a random access procedure" | R2-1803196 | ✅ Match | content_preview verbatim |
| 5 | "Current Rel-15 BFR is useless in support of beam failure on the SCell" | R2-1900212 (Rel-16) | ✅ Match | Motivation for Rel-16 SCell BFR introduction. Consistent with patent #11,909,488 |
| 6 | "When the beam of SCell changes while the SCell is deactivated... Allow UE to trigger beam failure recovery on SCell..." | R2-2301761 (Rel-18) | ✅ Match | Rel-18 enhancement accurate |
| 7 | 38.213 §6 q0/q1 resource definitions (`failureDetectionResourcesToAddModList`, `candidateBeamRSList`) | 38.213-6-001 | ✅ Match | text_preview verbatim. Aligns with the TS 38.213 authoritative source |
| 8 | 38.321 §5.17 "MAC entity may be configured by RRC per Serving Cell or per BFD-RS set with a beam failure recovery procedure" | 38.321-5.17-001 | ✅ Match | Procedure aligns with the TechSpec authoritative source |
| 9 | 38.321 §5.1.4 "contention-free Random Access Preamble for beam failure recovery request ... start the ra-ResponseWindow configured in BeamFailureRecoveryConfig" | 38.321-5.1.4-001 | ✅ Match | text_preview verbatim |
| 10 | 38.331 IE `BeamFailureRecoveryRSConfig` "See also TS 38.321 [3], clause 5.17" + `rsrp-ThresholdBFR-r16  RSRP-Range` | R2-2407883 | ✅ Match | content_preview contains the ASN.1 fragment as-is. RSRP-Range type accurate |
| 11 | 38.133 §8.18.2.2 "TEvaluate_BFD_SSB ... Qout_LR_SSB ... FR2 with scaling factor N, where N=2,4,6 in FR2-1" | 38.133-8.18.2.2-001 | ✅ Match | text_preview verbatim. FR2-1 N values are accurate |
| 12 | 38.133 §8.5B.2.2 "TEvaluate_BFD_SSB_Redcap" RedCap variant | 38.133-8.5B.2.2-001 | ✅ Match | text_preview verbatim |
| 13 | 38.133 §8.5D.3.2 "TEvaluate_BFD_CSI-RS ... Qout_LR_CSI-RS" | 38.133-8.5D.3.2-001 | ✅ Match | text_preview verbatim |
| 14 | 38.533 §17.5.2.1 "verify ... UE properly detects SSB-based beam failure in the set q0 ... PC3, f ≤ 40.8 GHz" | 38.533-17.5.2.1-001 | ✅ Match | text_preview verbatim. The Editor's Note also exists in the chunk |
| 15 | 38.533 §7.5.6.1.2 "Editor's note: incomplete ... FFS ... Test tolerance analysis is missing" | 38.533-7.5.6.1.2-001 | ✅ Match | text_preview verbatim. Used as the basis for the initial answer's avoidance of quantitative citation — appropriate |
| 16 | "The normative reference for this requirement is TS 38.133 [6] clause A.4.5.5.1" | R5-204985 (Rel-16) | ✅ Match | content_preview verbatim |

---

## Hallucinations found

**0 instances.**

Core analysis:
- The initial answer **withholds every quantitative core value the user asked about** (BLER %, beamFailureInstanceMaxCount range, beamFailureDetectionTimer range, 38.133 table ms rows, 38.533 tolerance).
- Item #4 of the §self-check table — "Did the answer fill in arbitrary timer/counter/threshold values from training knowledge? **NO**" — is confirmed accurate by authoritative checking.
- The bullets under §"SPECTRA RAG not found (or insufficient retrieval confidence) — excluded from the answer" function as honest limitation reports.
- Even very famous values that the LLM almost certainly knows from training (`Q_out=10%`, `Q_in=2%`, `n1~n10`, `pbfd1~pbfd10`) are not leaked at all — exemplary adherence to the SPECTRA RAG principle.

**Latent risk areas (verified to be non-hallucinations)**:
- §1 "RAN2-side introduction motivation ... in beamforming-based NR operation, RLF→RRC re-establishment is too late a recovery path" — this causal inference is not a direct chunk-body citation. However, it is a reasonable summary derivable from R2-1803196's "based on a number of beam failure instances ... will trigger a random access procedure which allows the recovery", and aligns with the authoritative source ([TechSpec 38.300 §9.2.8](https://itecspec.com/spec/3gpp-38-300-9-2-8-beam-failure-detection-and-recovery/)) → not a hallucination, an appropriate summary.
- §5 "BFD-RS type (SSB / CSI-RS) × UE type (regular / RedCap) × frequency (FR1 / FR2/FR2-1) — a separate evaluation period variable and table is defined" — derivable directly from three chunks (38.133-8.18.2.2-001 / 8.5B.2.2-001 / 8.5D.3.2-001). Accurate.

---

## Coverage gaps

Per the user's 6 question items:

| Item | Fulfillment | Note |
|---|:---:|---|
| Introduction background/motivation | ✅ Full | R1-1707606/R1-1713597/R2-1803196 + Rel-15→16→18 evolution noted |
| 38.213 PHY procedure | ⚠️ Partial | q0/q1 resource definitions accurately quoted. However the core definition — *Q_out,LR is defined as hypothetical PDCCH BLER 10%* — is unanswered (chunk score 0.33 noted as insufficient retrieval) |
| 38.321 MAC procedure | ✅ Mostly Full | §5.17 BFR procedure + §5.1.4 BFR PRACH + ra-ResponseWindow all cited. Missing: the BFI_COUNTER reset-on-expiry mechanism — chunk score low, unanswered |
| 38.331 RRC parameter | ⚠️ Partial | The `BeamFailureRecoveryRSConfig` IE is partially cited via R2-2407883. Key gap: the §6.3 `BeamFailureRecoveryConfig` IE's ASN.1 enumerated ranges (`n1~n10`, `pbfd1~pbfd10`, `sl1~sl80`). The initial answer notes the same pattern as the RAN1 Phase-7 IE-vs-procedure embedding limitation — a systemic limitation |
| 38.133 RRM requirements | ⚠️ Partial | Variable names, structure, FR1/FR2 split are accurate. Absolute ms values in the table rows are withheld because of the preview cutoff |
| 38.533 testing | ✅ Mostly Full | EN-DC/NR SA, FR1/FR2, PCell/PSCell, DRX splits + test case KG nodes all cited. Missing: quantitative tolerance values (the spec itself is FFS — incomplete) — not avoidance |
| Cross-document linkages | ✅ Full | 5 explicit links + sequence diagram + workflow figure. Excellent |

**One key gap**: The Q_out,LR / Q_in,LR BLER 10% / 2% definitions — very clear in authoritative sources and present in the body of 38.213 §5/§6. The initial answer does not dig deeper to check whether the values appear inside the retrieved chunk text (38.213-5-001). The SPECTRA RAG search engine's embedding semantic space matches "Q_out / Q_in definitions" weakly — this is a system improvement target.

---

## Authoritative source key facts vs. initial answer

1. **BFR introduction (Rel-15)** — Authority (Justia patent, RAN1 agreement): adopted in NR Rel-15 RAN1 #88bis/#89/AdHoc#2. **Initial answer**: cites R1-1707606 (Rel-15), R1-1713597, R1-1717606 (RAN1 #90b) concretely. Match ✅.

2. **38.213 §6 BFD/BFR PHY** — Authority: Q_out,LR (BLER 10%, DCI 1_0 + CCE aggregation 8, 2-symbol CORESET), Q_in,LR (BLER 2%, DCI 1_0 + CCE aggregation 4). q0 (BFD-RS), q1 (candidate beam RS). **Initial answer**: q0/q1 resource definitions verbatim ✅. BLER quantitative values withheld ⚠️ (intentional — weak chunk match, honestly reported).

3. **38.321 §5.17 BFR MAC** — Authority (TechSpec): "Beam failure is detected by counting beam failure instance indication from lower layers... if BFI_COUNTER >= beamFailureInstanceMaxCount, RA is triggered". **Initial answer**: chunk verbatim citation ✅. The BFI_COUNTER expiration branch is unanswered because of the low §6.1.3.30 chunk score.

4. **SCell BFR (Rel-16)** — Authority (Justia patent #11,909,488, RAN1/RAN2 agreement): SCell BFR operates via BFR MAC CE transmission (different from PCell/PSCell PRACH). **Initial answer**: cites R2-1900212 Rel-16 introduction motivation + lists `38.321-6.1.3.23 BFR MAC CEs`, `38.321-6.1.3.43 Enhanced BFR MAC CEs` in the §3 KG nodes ✅. The fact that SCell BFR uses a MAC CE instead of PRACH is not explicitly explained in the body ⚠️ (inferable from KG node names).

5. **38.133 RRM measurement times** — Authority: TS 38.133 §8.18.2.2 Tables 8.18.2.2-1/-2 contain ms-unit rows. FR1/FR2/FR2-1 differences. **Initial answer**: variable names, N values (2,4,6), structure all accurate ✅. Absolute ms-row values withheld ⚠️ (preview cutoff).

---

## Overall judgment

- **Trustworthy areas (usable as-is)**:
  - Procedures/names/IEs/relations
  - BFR sequence diagram
  - Cross-document linkages (especially 38.331↔38.321 IE-procedure linkage)
  - Release evolution (Rel-15 PCell/PSCell BFR → Rel-16 SCell BFR → Rel-17/18 enhancement)
  - q0/q1 resources, contention-free PRACH, ra-ResponseWindow
  - 38.133 evaluation-period variable system (SSB/CSI-RS × regular/RedCap × FR1/FR2/FR2-1)
  - 38.533 test-case branching structure

- **Partially trustworthy areas (need re-search)**:
  - 38.331 IE ASN.1 enumerated ranges (`n1~n10`, `pbfd1~pbfd10`, `sl1~sl80`) — clear in authoritative sources
  - The behavioral difference that SCell BFR uses MAC CE instead of PRACH — the initial answer only labels the KG node

- **Weak areas (quantitative values)**:
  - Q_out,LR / Q_in,LR BLER thresholds (10% / 2%) — explicitly required by the user
  - 38.133 Tables 8.18.2.2-1 / 8.5B.2.2-1 / 8.5D.3.2-1 absolute ms values
  - 38.533 test tolerance (the spec itself is FFS — separable responsibility)

**Initial answer assessment**: Exemplary adherence to the SPECTRA RAG principle of "only cite facts actually retrieved by the search". 16/16 citation integrity and 0 hallucinations are decisive strengths. The shortcomings are systemic — quantitative-value chunks were not retrieved precisely by the search engine, not a failure of the LLM to hold back. From an honesty perspective the answer scores top marks.

---

## System improvement recommendations (RAG perspective)

1. **Extend chunk preview cutoff**: 600 chars (`text_preview` / `content_preview`) → 2,000 chars. ms rows like Table 8.18.2.2-1 of 38.133 are present in the chunk body but cut off in the preview → answerable facts are processed as "unanswered" (false negatives). Even if log files grow, accuracy comes first.

2. **Filter or flag 38.533 FFS-marker chunks**: chunks like §7.5.6.1.2 contain *Editor's note: incomplete, FFS* markers. Either lower their retrieval priority or mark them with `is_ffs_placeholder=true` metadata. Currently the top-1 hit is an FFS chunk, preventing quantitative citation.

3. **Separate ASN.1 IE chunking for 38.331**: §6.3 IE definitions sit in a different embedding semantic space from §5 procedure bodies (the same limitation as RAN1 Phase-7). Mark IE chunks with `chunk_type=asn1_ie` and prefix the IE name explicitly in the embedded text (e.g., "IE BeamFailureRecoveryConfig: ..."). This enables matching enumerated ranges (`n1, n2, ...`).

4. **Strengthen embedding for 38.213 §6 BLER definitions**: the fact that an authoritatively-aligned fact is retrieved with top score 0.33 in SPECTRA RAG indicates an embedding-quality issue. Add keywords like "hypothetical PDCCH BLER" to chunk metadata or chunk at finer sub-section granularity.

5. **Full-text fetch fallback for cited TDocs**: when a chunk_id is retrieved but the 600-char preview lacks the core body, add a fallback API call during the answer stage to fetch the chunk's full text. Automatically reinforce cases where the initial answer skipped chunks with "in this excerpt".

6. **Reinforce cross-spec linkage cypher**: the KG currently has weak explicit `REFERENCES_CLAUSE` relations for 38.331 IE → 38.321 §5.17 (the initial answer notes "the KG is at clause level, no IE-level nodes"). Extract direct IE→Procedure edges in phase-3/4.

---

## Weakness root-cause classification (D / O / R)

> **D**: Limitations in the 3GPP data itself (timing, completeness) — solved by time
> **O**: Missing KG/ontology modeling — schema enhancement required
> **R**: Limitations of the chunking/embedding/indexing in the VDB build stage — pipeline enhancement required

| # | Weakness | D / O / R | Evidence | Improvement potential |
|---|---|:---:|---|---|
| 1 | 38.213 Q_out,LR / Q_in,LR BLER quantitative values (10% / 2%) not retrieved | **R** | The 38.213 §6 BFD definition chunk's BLER thresholds are cut off by the 600-char preview cutoff. Even if chunks are retrieved by dense retrieval, "10%"/"2%" do not surface. Embedding quality is partly to blame (top score 0.33). | High — extend the preview cutoff from 600 → 2,000 chars |
| 2 | 38.331 `beamFailureInstanceMaxCount` (n1~n10) / `beamFailureDetectionTimer` (pbfd1~pbfd10) enumerated-range bodies not retrieved | **R + O** | (R) The 38.331 IE block is not separated from the sectionTitle, weakening dense retrieval of the IE body. (O) The `RRCParameter` label does not separate IEs in modeling, blocking a graph detour. | High — IE-level chunking + KG IE nodes |
| 3 | 38.321 `BFI_COUNTER` expiration branch / SCell BFR's MAC-CE-instead-of-PRACH usage | **R + O** | (R) 38.321 §5.17 SCell BFR is chunked per clause, but the body excerpt is insufficient. (O) The cross-clause edge connecting the MAC CE 6.1.3.x to the BFR procedure node is unmodeled. | Medium — add IE→Procedure REFERENCES_CLAUSE edges |
| 4 | 38.133 tables (8.18.x / 8.5B.x / 8.5D.x) ms quantitative-value rows not retrieved | **R** | (R) 38.133 RRM tables are not chunked per row. ms absolute values are cut off by the preview cutoff. | High — table-row chunking + preview extension |
| 5 | 38.533 BFR test tolerance quantitative values not retrieved (FFS marker present) | **D + R** | (D) Some clauses of 38.533 V18.x are marked *FFS / Editor's note: incomplete*, so the 3GPP source itself is unfinished. (R) No filtering of FFS-marker chunks. | (D partial — solved by time) + (R reinforce filtering) |
| 6 | BFR introduction RP-WID body cannot be cited directly | **R** | RP-* TDocs are not loaded as a separate collection; discussions cite RP numbers as references. | Medium — create a `ranX_rp_tdocs` collection |
| 7 | KG lacks direct edges from IE to procedure clause | **O** | The KG has only clause-level nodes with partial IE-level nodes. Explicit `REFERENCES_CLAUSE` relations like `BeamFailureRecoveryConfig` IE → 38.321 §5.17 are weak. | Medium — extract IE→Procedure edges in phase-3/4 |
| 8 | BFR procedure flow / parameter variable names / cross-doc linkages | **(none)** | No data limitation — procedures/names are cited accurately retrieved-grounded. | (D responsibility = 0) |

**Totals**: D 1 partial (#5 38.533 FFS), R 3, R+O 2, O 1, D+R 1. **System (R/O) responsibility dominates**; the 38.533 FFS marker is the only D piece (the 3GPP source itself is incomplete), but every other quantitative-value gap is a system limitation.

**Improvement priority**:
1. (P1, R) Extend chunk preview from 600 → 2,000 chars — resolves Q3 quantitative values + Q4 LTM timer in one stroke
2. (P1, R+O) 38.331 IE-level chunking + KG IE nodes — common to Q1/Q2/Q3/Q4
3. (P1, R) 38.133 RRM table row-level chunking — enables ms absolute-value citation
4. (P2, R) FFS-marker chunk filtering — 38.533 spec quality gate
5. (P2, O) Extract IE→Procedure `REFERENCES_CLAUSE` edges — graph-RAG strengthening
6. (P2, R) New separate RP-WID collection
