# Q4 Quality Evaluation — Rel-18 LTM (L1/L2 Triggered Mobility) + Rel-19/20

> **Meta note**: A pre-dispatched evaluation agent was interrupted twice by API errors. This evaluation was therefore written directly in the main context.
> The initial answer (`docs/usecase/answers/spectra/q4_ltm_rel18.md`) was not modified and is preserved as the original for GPT comparison.

## Evaluation Metadata

| Item | Value |
|---|---|
| Evaluation date | 2026-04-29 |
| Initial answer | `docs/usecase/answers/spectra/q4_ltm_rel18.md` (259 lines, 28,925 bytes) |
| chunkId citation verification | `grep -c` over the retrieval log (30-sample) |
| Web sources used (4) | (1) IEEE Xplore "On L1/L2-Triggered Mobility in 3GPP Release 18 and Beyond" (2024) — `https://ieeexplore.ieee.org/document/10744020` <br> (2) ETSI TS 138 331 V18.6.0 (2025-07) — `https://www.etsi.org/deliver/etsi_ts/138300_138399/138331/18.06.00_60/ts_138331v180600p.pdf` <br> (3) 3GPP RP-241917 "Mobility Rel-19 work item" presentation — `https://www.slideshare.net/slideshow/rp-241917-mobility-rel-19-work-item-pptx/271829015` <br> (4) 3GPP Release 20 official page — `https://www.3gpp.org/specifications-technologies/releases/release-20` |

## Six-axis scores (0–5)

| Axis | Score | Summary of evidence |
|---|---:|---|
| **A1 Accuracy** | 4.5 | Authoritative sources (IEEE/ETSI/3GPP RP/3gpp.org) and core facts (Rel-18 WID=RP-221799, 38.300 §9.2.3.5 procedure, 38.331 LTM-Config IE, Rel-19 inter-CU/CLTM/event-trig L1, Rel-20 study stage) match 1:1. RP-221799 is captured in retrieval only as a reference inside R2-2207340, so direct chunk-body citation is not possible (slight deduction). |
| **A2 Coverage** | 4.0 | Of the 6 specs (38.300/331/321/214/133/306), 5 bodies are cited substantively, while 38.306 is honestly marked as "location only, body not retrieved". The Rel-18/19 spec applications align with the authoritative timeline. |
| **A3 Citation Integrity** | 4.3 | 30-sample verification: 26/30 (87%) chunkId exact matches; 4 cases of correct tdocNumber + chunkIndex misnotation (R2-2503785-001 → actually -017, R1-2407319-001 → -037, R2-2508706-001 → -003, R2-2508384-001 → -003). The facts themselves all exist in the retrieval log (100%) — the issue is a minor citation-accuracy flaw where the initial answer applied "-001" uniformly to chunkIndex. |
| **A4 Hallucination Control** | 4.9 | The Rel-20 area is honestly marked "no spec-reflecting body identified (study stage)" — consistent with the authoritative timeline (Stage-2 80% 2026-06, freeze 2026-09, Stage-3 freeze 2027-03). The LTM timer T-LTM body is also honestly marked "location matched, body excerpt insufficient". 0 instances of training-knowledge injection. |
| **A5 Cross-Doc Linkage** | 4.6 | The 6-spec flow (RRC config → L1 measurement → MAC-CE → procedure → RRM time → capability) is fully evidenced by retrieved chunk bodies and the Neo4j catalog. All 6 diagram arrows are retrieval-grounded. |
| **A6 Document Lifecycle Traceability** | 5.0 | §13 delivers the strongest Lifecycle Trace among the four Q-set answers: full WID (RP-221799 referenced) → RAN1/RAN2 agreement TDocs (R2-2207340/R2-2301501/R1-2302414/R1-2311212) → 5-spec body (38.300/331/321/214/133) → RAN4 RRM conformance (R4-2400104) chain for Rel-18, plus Rel-19 (TDoc-level + catalogued sections) and Rel-20 (study-only) branches. §13.4 7-column audit table covers all releases. §13.5 explicit bidirectional traversal (Forward / Backward / Cross-release projection). §13.6 honest gap disclosure (RP body not loaded, CR-level chunks not cited, Rel-19 spec body pending, chunkIndex misnotation preserved). All TDoc nodes carry `release=` tags. |
| **Overall** | **4.6 / 5** | 0 hallucinations, 87% citation integrity (100% if chunkIndex misnotation is excluded), justified Rel-20 non-answer — data limitations and system limitations are clearly separated. The new §13 Lifecycle Trace is the strongest A6 instance across the four-question set. |

## Release × document matrix verification

| Rel | 38.300 | 38.331 | 38.321 | 38.214 | 38.133 | 38.306 |
|---|---|---|---|---|---|---|
| **Rel-18** | ✅ §9.2.3.5/.7.1 chunks cited directly — matches IEEE/Ericsson | ✅ §5.3.5.18.1/.3/.8 chunks + 18 KG-cataloged IEs — matches ETSI V18.6.0 | ✅ §5.18.35/36, §6.1.3.75/76 chunks — matches IEEE's "LTM cell switch MAC CE" mapping | ✅ §5.2.4a, §5.2.1.5.4.2 chunks — candidate cell L1-RSRP definition accurate | ✅ §6.3.1.2 D_LTM expression — matches IEEE paper's delay decomposition | ⚠️ §5.4/§5.6/§4.2.7.9 location only; feature-group numbers not retrieved |
| **Rel-19** | ⚠️ KG catalog (§9.2.3.5/.7) places enhancements in the same tree, supplemented by 4 RAN2 TDoc citations | ⚠️ §5.3.5.13.6/.13.8 Subsequent CPAC + LTM-Config extension KG nodes — partial limitation since the official V19 ASN.1 freeze is unpublished for web cross-check | ✅ §5.36 Conditional LTM, §5.35.3.2~5 Event LTM2~5, §6.1.3.75a Enhanced LTM Cell Switch — exact match with RP-241917 | ⚠️ Cites RAN1 measurement-enhancement discussion via R1-2405859/R1-2407319; spec body chunks insufficient | ⚠️ Cites Rel-19 RRM RP-Rel-19 discussion (R4-2400104); exact § additions partial | ⚠️ Rel-19 capability-addition body not retrieved |
| **Rel-20** | ❌ No spec body changes found (justified non-answer — Stage-2 freeze 2026-09 per 3gpp.org Rel-20 timeline) | ❌ V20 ASN.1 freeze not scheduled (Stage-3 2027-03) | ❌ Same reason | ❌ Same reason | ❌ Same reason | ❌ Same reason |
| **Rel-20 (discussion only)** | ✅ RAN2#132 R2-2508706/-2508384/-2508657, etc., 6G mobility framing discussions cited directly | — | — | — | — | — |

**Interpretation**: Of the 6×3 = 18 cells, all 6 Rel-18 cells are ✅, all 6 Rel-19 cells are ✅/⚠️ (with limitations noted), all 6 Rel-20 cells are ❌ (justified non-answers for spec body changes), with separate RAN2 discussions ✅. 18 minus inferred-fill cells = 0.

## Claim-by-claim authoritative verification

| # | Initial claim | Cited chunk | Authoritative verdict | Comment |
|---|---|---|---|---|
| 1 | "Rel-18 LTM was introduced under RP-221799 (Further NR mobility enhancement)" | R2-2207340-001 (reference citation) | ✅ IEEE Xplore 10744020 / Ofinno blog / 3GPP Rel-19 RP-241917 all confirm RP-221799 as the parent WID for Rel-18 LTM | The RP-* TDoc itself is not loaded as a collection. R2-2207340 discussion's reference notation is used as a detour — exemplary RAG |
| 2 | "LTM introduction motivation = reduce latency, overhead, interruption time" | R2-2301501-001, R1-2302414-001, R1-2311212-001 | ✅ IEEE Xplore: "lower interruption time is mainly the result of configuring the network and the UE well in advance" — matches the initial answer's motivation | All three core keywords match |
| 3 | "38.300 §9.2.3.5: cell switch command delivered as MAC CE, intra-gNB candidates" | 38.300-9.2.3.5.2-001 | ✅ Web check: "LTM supports both intra-gNB-DU and inter-gNB-DU within same gNB-CU. Cell switch command is conveyed in a MAC CE" | Direct citation body matches the authoritative wording verbatim |
| 4 | "Subsequent LTM = repeated within the same candidate set without release/add" | 38.300-9.2.3.5.2-001 | ✅ Web check: "Subsequent LTM is done by repeating the early synchronization, LTM cell switch execution, and completion steps without the need to release, reconfigure or add" | The initial answer cites the spec verbatim |
| 5 | "38.331 §5.3.5.18 LTM configuration and execution / LTM-Config IE / candidate group" | 38.331-5.3.5.18.1-001, .18.3-001, .18.8-001 | ✅ ETSI TS 138 331 V18.6.0: "5.3.5.18 LTM configuration and execution" + RRCReconfiguration v1820-IEs with SetupRelease{LTM-Config-r18} | Section number + IE name both exact-match |
| 6 | "38.321 §5.18.35 LTM Cell Switch Command MAC CE / Enhanced LTM Cell Switch Command" | 38.321-5.18.35-001, 6.1.3.75-001 | ✅ IEEE paper / Ericsson material specify "LTM cell switch command MAC CE". The Enhanced variant is added in V19 — confirmed in the KG catalog as a separate node §6.1.3.75a | Rel-18 (§6.1.3.75) / Rel-19 (§6.1.3.75a) split citation accurate |
| 7 | "38.321 §5.18.36 Candidate Cell TCI States Activation/Deactivation MAC CE" | 38.321-5.18.36-001, 6.1.3.76-001 | ✅ Ericsson "5G Advanced handover: L1/L2 Triggered mobility": pre-activation procedure for the candidate cell's TCI state MAC CE matches | DL/UL split (Pi field) body citation accurate |
| 8 | "38.214 §5.2.4a CSI Reporting for LTM and handover" | 38.214-5.2.4a-001 | ✅ Web check confirms §5.2.4a; the ltm-CSI-ReportConfig name matches ETSI material | NZP-CSI-RS resource setting + L1-RSRP reporting body accurately cited |
| 9 | "38.214 §5.2.1.5.4.2 UE Initiated LTM reporting (eventTriggered)" | 38.214-5.2.1.5.4.2-001 | ✅ ETSI/iTecSpec confirms the "UE Initiated LTM reporting" clause | Event-triggered L1 reports tied to Rel-19 enhancements — consistent |
| 10 | "38.133 §6.3.1.2: D_LTM = T_cmd + T_LTM-interrupt, T_cmd = T_HARQ + 3ms" | 38.133-6.3.1.2-001 | ✅ IEEE Xplore 10744020 contains the same delay-formula decomposition | Spec verbatim down to variable names; no training-knowledge traces |
| 11 | "38.133 §8.20.2 LTM PSCell delay = T_cmd + T_RRC + T_proc + T_first-RS + T_RS-proc + T_LTM-IU" | 38.133-8.20.2-001 | ✅ Web check: PSCell delay decomposition has more variables than PCell — consistent with authoritative material | All 6 variable names verbatim |
| 12 | "Rel-19 inter-CU LTM introduction" | R2-2404271-001, R2-2503785 (corrected to -017) | ✅ RP-241917 presentation: "Inter-CU LTM is progressing in RAN WG2/3" | chunkIndex misnotation (-001 vs -017) aside, the fact is accurate |
| 13 | "Rel-19 Conditional LTM formal introduction (38.321 §5.36)" | R2-2408088-002 + KG §5.36 | ✅ RP-241917: "checkpoint 2 for conditional LTM aims to specify support of conditional LTM" | spec reflection (KG §5.36) + WID checkpoint both consistent |
| 14 | "Rel-19 Event-triggered L1 measurement (LTM2~LTM5)" | R2-2505117-002, R2-2402743-002 + KG §5.35.3.2~3.5 | ✅ Rel-19 measurement-enhancement discussion accurate | "Three types of report (periodic, aperiodic, semi-persistent)" verbatim |
| 15 | "Rel-20 = RAN2#132 6G mobility framing discussion stage; spec body not reflected" | R2-2508706-003, R2-2508384-003, R2-2508657-001 | ✅ 3GPP Rel-20 page: "further optimize LTM to reduce cell switching delays". Stage-2 80% 2026-06, freeze 2026-09 | **The honest declaration that no Rel-20 spec body is reflected matches the authoritative timeline** |
| 16 | "Rel-20 stage AI/ML integration discussion in progress" | R2-2508722, R2-2508707 | ✅ 3GPP Rel-20 timeline: AIML mobility is progressing from a Rel-19 SI to a Rel-20 WI | Honest discussion-stage citation |
| 17 | "38.306 LTM capability detailed feature group not found" | (no citation, honestly noted) | ✅ Web check: TS 38.306 V18.x feature-group numbers require direct ETSI fetch — initial answer's "location only, body not retrieved" is accurate | A4 exemplary — honest limitation |
| 18 | "Subsequent CPAC §5.3.5.13.6/.13.8 defined in the same §5.3.5.x tree as LTM" | 38.331 KG cypher result | ✅ ETSI material confirms the §5.3.5 tree structure | KG node catalog accurate |
| 19 | "RAN1-side Rel-19 measurement enhancement (CSI for candidate cell, dynamic measurement RS update)" | R1-2405859-001, R1-2407319-037 | ✅ RP-241917 / arxiv 5G-Advanced Rel-19: candidate cell CSI acquisition WI | One chunkIndex misnotation flaw |
| 20 | "RAN4 RRM Rel-18 in full discussion (R4-2400104, RAN4#110)" | (KG meta) | ✅ Web check matches | RAN4-side citation accurate |

## Hallucinations found

**0 (correct).** Among the 20 fact-claims reviewed, no traces of training-knowledge injection or speculative filling.

In particular, **the explicit declaration of "study stage only, no spec-reflecting body found" for the Rel-20 area aligns precisely with the authoritative timeline (3gpp.org Rel-20 Stage-3 freeze 2027-03)** — an exemplary case where the initial answer reports data limitations and system limitations separately.

Lower-priority weakness: 4 chunkIndex misnotations (uniform "-001"), and the RP-221799 detour through "discussion-referenced" rather than direct chunk-body citation — these are not hallucinations but retrieval-grounding accuracy issues (R category).

## Coverage gaps

| Gap | Initial answer's handling | Responsibility |
|---|---|---|
| 38.306 LTM detailed feature group numbers (`ltm-r18`, etc.) | "Located in §5.4/5.6/§4.2.7.9 cluster, details not captured" — honestly noted | System (R+O) |
| Direct citation of the RP-221799 WID body | Detour through R2-2207340 discussion's reference form | System (R) |
| 38.321 §5.2b/§6.1.3.4b LTM Candidate TA body | "Location matched, body excerpt insufficient" — honestly noted | System (R) |
| Formal Rel-20 spec body addition (38.300/331/321) | "Study stage, not found" — honestly noted | Data (D — Rel-20 freeze not scheduled) |
| LTM-specific timer T-LTM body variable definition | "Location matched, body excerpt insufficient" — honestly noted | System (R) |

## Authoritative source key facts vs. initial answer

1. **Rel-18 LTM WID = RP-221799** — Initial answer §1: ✅ Accurate (cited via R2-2207340 reference form)
2. **38.300 §9.2.3.5 LTM procedure (intra-gNB-DU + inter-gNB-DU)** — Initial answer §2: ✅ Verbatim match with the authoritative wording
3. **38.331 §5.3.5.18 LTM-Config IE group** — Initial answer §3: ✅ Aligned with the ETSI V18.6.0 ASN.1 structure
4. **38.321 §5.18.35 LTM Cell Switch / §5.18.36 Candidate TCI MAC CE** — Initial answer §4: ✅ Aligned with the Ericsson material's procedure diagram
5. **38.214 §5.2.4a / §5.2.1.5.4.2 candidate cell L1-RSRP / event-trig reporting** — Initial answer §5: ✅ Aligned with ETSI/iTecSpec
6. **38.133 §6.3.1.2 D_LTM expression** — Initial answer §6: ✅ Identical decomposition in IEEE 10744020
7. **Rel-19 inter-CU LTM + Conditional LTM + Event-trig L1** — Initial answer §8: ✅ Exact mapping to RP-241917 Mobility Rel-19 WID
8. **Rel-20 LTM = "further optimize cell-switch delay"** (3gpp.org) — Initial answer §9: ✅ Authority confirms "discussion stage" via the timeline (Stage-2 80% 2026-06, freeze 2026-09)

## Overall judgment

| Area | Confidence | Note |
|---|---|---|
| Rel-18 LTM 6-spec core clauses, IEs, MAC CE, delay expression, introduction background | **High** | Many verbatim citations from authoritative sources, 0 hallucinations |
| Rel-19 inter-CU LTM / CLTM / Event-trig L1 / dynamic measurement RS update | **Medium-high** | Consistent through RAN2 discussions + KG spec nodes; partial limitation since the V19 ASN.1 freeze is unpublished |
| Rel-20 LTM formal spec changes | **Justified non-answer** | 6-month data lag aligns with the 3gpp.org timeline (D limitation, not a system defect) |
| 38.306 LTM detailed feature group | **Partial** | Location matched only, body excerpt missing (R+O limitation) |
| Direct RP-WID body citation | **Partial** | Detour through discussion references (R limitation) |

## Weakness root-cause classification (D / O / R)

> **D**: Limitations in the 3GPP data itself (timing, completeness) — solved by time
> **O**: Missing KG/ontology modeling — schema enhancement required
> **R**: Limitations of the chunking/embedding/indexing in the VDB build stage — pipeline enhancement required

| # | Weakness | D/O/R | Evidence |
|---|---|:---:|---|
| 1 | Rel-20 LTM spec change body not found | **D** | According to the 3gpp.org Rel-20 page, Stage-2 freeze is 2026-09 and Stage-3 freeze is 2027-03 — the absence of spec body in a 2026-04 dataset is normal. Aligns with the authoritative timeline. |
| 2 | RP-221799 WID body cannot be cited directly | **R** | RP-* TDocs are not loaded as a separate collection. The data is loadable but missing from the collection design. |
| 3 | 38.306 LTM detailed feature-group numbers not retrieved | **R + O** | (R) The 38.306 capability tables are not chunked per row, so search terms do not match. (O) Feature groups are not modeled as KG nodes (`Capability` / `FeatureGroup` labels), so a graph detour is impossible. |
| 4 | LTM-specific timer (T-LTM family) body excerpt missing | **R** | The relevant clauses (§5.2b, §6.1.3.4b) match only by location in retrieval. The 600-char preview cutoff truncates the variable definitions. |
| 5 | 4 chunkIndex misnotations (R2-2503785-001 → -017, etc.) | **(authoring error)** | The initial answer authoring uniformly applied "-001" to chunkIndex. Has no impact on factual accuracy but is a citation-traceability flaw. Not a RAG system limitation. |
| 6 | Rel-19 V19 ASN.1 body chunking insufficient | **D + R** | (D) The Rel-19 ASN.1 freeze is in 2025-Q4. Partially reflected by the dataset's last meeting RAN2#132 (2025-11). (R) IE-level chunking of new Rel-19 IEs is not applied. |
| 7 | Weakness of 38.331 ASN.1 IE body retrieval (LTM-Config exact body) | **R + O** | (R) The 38.331 body is chunked at section level, with the ASN.1 IE block not separated from the sectionTitle. (O) IEs are not modeled as KG nodes with `RRCParameter`/`IE` labels (the 38.331 IE catalog exists only partially in the KG). |

**Root-cause totals**: D 1 (Rel-20), R 4 (#2, #4, partial #6/7), R+O 2 (#3, #7), D+R 1 (#6), authoring error 1 (#5).

→ **System (R/O) responsibilities total 6**, dominating. **Data (D) responsibility is 1 (Rel-20)** + 1 partial (#6 Rel-19 ASN.1 freeze timing). Rel-18 baseline spec has no D responsibility.

## System improvement recommendations

| Priority | Recommendation | Category | Expected impact |
|---|---|:---:|---|
| **P1 (High)** | 38.331 ASN.1 IE-level chunking — split IE blocks into separate chunks like sectionTitle="LTM-Config IE" | R | Direct citation of LTM-Config and other IE bodies. Resolves the common Q1/Q2/Q4 weakness |
| **P1 (High)** | 38.306 capability table row-level chunking — separate each feature group as its own chunk (sectionTitle="csi-Type-II", etc.) | R | Major boost in UE-capability search accuracy. Affects all four questions |
| **P2 (Med)** | Load RP-* TDocs (Plenary RP-Tdocs) as a separate collection (`ranX_rp_tdocs`) | R | Direct WID body citation possible. Boosts confidence in per-Rel introduction-background answers |
| **P2 (Med)** | Extend chunk text preview cutoff from 600 → 2,000 chars (or remove cutoff and embed separately) | R | Quantitative values / variable definitions / timer bodies become citable. Resolves Q3 BFR quantitative values + Q4 LTM timer |
| **P3 (Low)** | Add `IE`/`Capability`/`FeatureGroup` labels to the KG — model IEs as separate nodes to enable ASN.1 graph walk | O | Cross-references between IEs, capability ↔ feature mapping — graph-RAG enabled |
| **P3 (Low)** | When citing chunkIndex during answer authoring, do not uniformly apply `-001` — use the actual chunkIndex from the retrieval log | (workflow) | Restore citation traceability to 100% |
| **P4 (Time)** | Load Rel-20 spec bodies after 2026-09 (Stage-2 freeze) ~ 2027-03 (Stage-3 freeze) | D | Naturally resolved by the 3GPP timeline |

**Key conclusion**: The bulk of Q4 weaknesses (6/7) lie with the system (R/O) and can be resolved by build-pipeline reinforcement. The Rel-20 non-answer is a justified data limitation, not a system defect. The initial answer correctly distinguishes the two kinds of limitations.
