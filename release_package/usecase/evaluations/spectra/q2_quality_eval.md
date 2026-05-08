# Q2 Quality Evaluation — TCI-state Rel-15~Rel-20

## Evaluation Metadata

- Evaluation date: 2026-04-29
- Initial answer: `docs/usecase/answers/tracer/q2_tci_state_rel15_to_rel20.md` (247 lines)
- Retrieval log: `logs/cross-phase/usecase/q2_retrieval_log.json` (ts_queries=14, tdoc_queries=48, neo4j RAN1/RAN2)
- The initial answer must not be modified (preserved as the original for GPT comparison). This evaluation only cross-checks against external authoritative sources.
- Web sources used:
  - 3GPP RAN1 Rel-18 page — https://www.3gpp.org/technologies/ran1-rel18
  - 3GPP Release 18 — https://www.3gpp.org/specifications-technologies/releases/release-18
  - 3GPP Release 19 / RAN Rel-19 Status — https://www.3gpp.org/specifications-technologies/releases/release-19, https://www.3gpp.org/technologies/ran-rel-19
  - ETSI TS 138 321 V17.5.0 (Rel-17) — https://www.etsi.org/deliver/etsi_ts/138300_138399/138321/17.05.00_60/ts_138321v170500p.pdf
  - ETSI TS 138 321 V18.1.0 / V18.5.0 / V18.6.0 (Rel-18) — https://www.etsi.org/deliver/etsi_ts/138300_138399/138321/18.05.00_60/ts_138321v180500p.pdf, https://www.etsi.org/deliver/etsi_ts/138300_138399/138321/18.06.00_60/ts_138321v180600p.pdf
  - ETSI TS 138 321 V16.1.0 (Rel-16) — https://www.etsi.org/deliver/etsi_ts/138300_138399/138321/16.01.00_60/ts_138321v160100p.pdf
  - ETSI TS 138 214 V17.1.0 (Rel-17) — https://www.etsi.org/deliver/etsi_ts/138200_138299/138214/17.01.00_60/ts_138214v170100p.pdf
  - 3GPP TS 38.214 V15.1.0 / V16.x.0 (panel.castle.cloud / atis mirrors) — https://panel.castle.cloud/view_spec/38214-f10/
  - sharetechnote QCL/TCI — https://www.sharetechnote.com/html/5G/5G_QCL.html
  - sharetechnote MAC CE TCI — https://www.sharetechnote.com/html/5G/5G_MAC_CE_TCI_State_PDSCH.html
  - Ofinno Unified Beam Management whitepaper — https://ofinno.com/wp-content/uploads/2021/09/Ofinno-Unified-Beam-Management-Whitepaper.pdf
  - 5G-Advanced Rel-19 / Qualcomm material — https://www.qualcomm.com/content/dam/qcomm-martech/dm-assets/documents/5G-A-Rel-19-Presentation.pdf
  - Itecspec 38.321 §5.18 / 38.331 IE — https://itecspec.com/spec/3gpp-38-321-5-18-handling-of-mac-ces/, https://itecspec.com/spec/3gpp-38-331-6-3-2-radio-resource-control-information-elements/

## Five-axis scores (0–5)

| Axis | Score | Summary of evidence |
|---|---:|---|
| A1 Accuracy | 4.6 | The cited facts (§5.1.5 body, §6.1.3.14/24/47/70/71, §5.18.23/33, `dl-OrJointTCI-StateList-r17`, simultaneousU-TCI-UpdateList*) all match ETSI/3GPP authoritative sources. The Rel-15/Rel-17/Rel-18 key changes are accurate. Minor deduction: the initial answer asserts that "§6.1.3.14 has been operational since Rel-15", but while the clause is indeed part of the Rel-15 NR body, the spec body itself does not explicitly state "first introduced under that clause number". |
| A2 Coverage | 4.0 | 22 of 24 cells filled. The two empty cells are Rel-19 38.214 body changes and Rel-19 38.306 capability items — the initial answer marks them honestly as "not found (dataset limitation)". The 4 Rel-20 cells are explicitly noted as "no spec body change identified". The Rel-19 NR MIMO Phase 5 (RP-242394) is confirmed as an active WI in authoritative sources, but the absence of body chunks for the spec change is justified by Phase-7 dataset limitations. |
| A3 Citation Integrity | 5.0 | All 12 cited chunkIds from the answer exist in `ts_queries.hits.chunkId` of the retrieval log (12/12). All 31 cited TDocs exist in `tdoc_queries.hits.tdocNumber` (31/31), with release/meeting/agendaItem/title metadata matching the answer's notation precisely. Neo4j Section citations (TCI-State, TCI-UL-State, TCI-ActivatedConfig, LTM-TCI-Info, CandidateTCI-State, §5.18.36/§6.1.3.76/§6.1.3.77, etc.) are verifiable in the RAN2 KG. |
| A4 Hallucination Control | 4.8 | Rel-19 spec body additions, Rel-20 spec body changes, and 38.331 IE body chunks are all marked as "not found / dataset limitation". 6G overview discussions are not exaggerated as spec changes. Minor: the "operational since Rel-15" attribution for §6.1.3.14 is a release attribution not directly quoted in the chunk body, qualifying as a weak hallucination (1 instance). |
| A5 Cross-Doc Linkage | 4.7 | All 5 linkages of the TCI flow (RRC IE → MAC-CE activation → PHY QCL application → UE capability) are verified through retrieved bodies via direct cross-references — 38.214 §5.1.5 references 38.321 §6.1.3.70, RRC parameter names cited, 38.306 capability cited. The mapping that Rel-17 unified TCI spans three specs is also accurate. The fact that 38.331 IE bodies are evidenced only via Neo4j Section nodes (because chunks are absent) is a recognized limitation. |
| **Overall** | **4.6 / 5** | 100% citation integrity, accurate accuracy/cross-doc linkage, fewer than 1 hallucination. The dataset limitations (no Rel-19/20 spec body chunks, no 38.331 IE body chunks) are all explicitly marked in the initial answer — honest non-answers. |

## Release × document 24-cell matrix verification

Notation — filled (✅) / honestly limited (⚠️) / unanswered (❌). Comments include the authoritative source verdict and the initial answer's accuracy.

| Rel | 38.214 | 38.321 | 38.331 | 38.306 |
|---|---|---|---|---|
| Rel-15 | ✅ §5.1.5 TCI-State list (`PDSCH-Config`) — matches authoritative sources (panel.castle.cloud V15.1.0, ATIS Rel-15 mirror). | ✅ §6.1.3.14 PDSCH TCI activation MAC CE — V15.x body confirmed by authoritative sources. (However the "since Rel-15" release attribution is not quoted directly from the body → A4 deduction.) | ✅ `TCI-State`/`TCI-StateId` IE registration (Neo4j Section node). Authority: `tci-StatesToAddModList` definition inside 38.331 §6.3.2 PDSCH-Config. The absence of identifiable ASN.1 body chunks is marked as a limitation. | ✅ `maxNumberConfiguredTCIstatesPerCC` capability (cited via 38.214 §5.1.5). Only the 38.306 §4.2.15.7.1 BandNR table header is retrieved (limitation noted). |
| Rel-16 | ✅ Cross-reference to 38.321 §6.1.3.70 — "8 sets of TCI states to DCI codepoint" — matches authoritative sources. | ✅ §6.1.3.24 Enhanced PDSCH TCI activation (eLCID) — V16.1.0 body exists (ETSI). | ⚠️ `tci-PresentInDCI`/`tci-PresentDCI-1-2` mentions — confirmed by authoritative sources. The IE body chunk is not identifiable; the answer routes around this by cross-quoting from the 38.214 §5.1.5 body — limitation noted. | ⚠️ Exact rows of the Rel-16 capability item names (`maxNumberActiveTCI-PerBWP`) are not chunk-identifiable — the initial answer marks this as a limitation. |
| Rel-17 | ✅ `dl-OrJointTCI-StateList-r17` (joint vs. separate split) — matches the Ofinno whitepaper and ETSI 38.214 V17.1.0. | ✅ §5.18.23/§6.1.3.47 Unified TCI MAC CE (`simultaneousU-TCI-UpdateList1..4`) — exact match with ETSI 38.321 V17.5.0. | ✅ `TCI-UL-State`/`TCI-UL-StateId` IE Neo4j-registered. Authority: 38.331 RRC IE definitions (Rel-17 separate UL TCI). | ⚠️ The exact Rel-17 unified TCI capability row is not identifiable — limitation noted. |
| Rel-18 | ✅ joint/separate mode split, `tci-SeparateTCI-UpdateMultiActiveTCI-Per…`. Authority: Ofinno, 3GPP RAN1 Rel-18 page (multi-TRP unified TCI extension). | ✅ §5.18.33 Enhanced Unified TCI MAC CE, §6.1.3.70 (Joint TCI), §6.1.3.71 (Separate TCI) — exact match with ETSI V18.5.0/V18.6.0. | ✅ `TCI-ActivatedConfig`, `LTM-TCI-Info` IE registered (Neo4j). Authority: aligns with the Rel-18 LTM (L1/L2 mobility) WI content. | ⚠️ A trace of an r18 capability item is retrieved (`additionalTime-CB-8TxPUSCH-r18`), but the exact row of the unified-TCI-only capability remains a limitation. |
| Rel-19 | ⚠️ The initial answer marks "no separate § addition identified, limitation noted". Authority: NR MIMO Phase 5 (RP-242394) is an active WI, but the absence of spec body change chunks is justified by the dataset state. | ✅ §5.18.36 Candidate Cell TCI / §6.1.3.76 / §6.1.3.77 Cross-RRH TCI — verified via Neo4j Section nodes. Authority: aligns with the Rel-19 mTRP/inter-cell extension direction. | ✅ `CandidateTCI-State`/`CandidateTCI-UL-State` IE registered — candidate cell TCI defined as an RRC IE. Authority: aligns with the Rel-19 NR MIMO Phase 5 direction. | ⚠️ No r19 capability item is directly identifiable — limitation noted. |
| Rel-20 | ⚠️ "No spec body change identified, only 6G overview discussions retrieved" — honest non-answer. Authority: 3GPP Rel-20 is in the 6G IMT-2030 phase prior to spec body changes, so the dataset's absence is justified. | ⚠️ Same. | ⚠️ Same. | ⚠️ Same. |

Summary: of 24 cells, 13 are filled (✅) and 11 are honestly limited (⚠️), 0 are unanswered (❌). All answerable cells are accurate; all unanswered cells are marked as limitations.

## Claim-by-claim authoritative verification

| # | Initial claim (summary) | Cited chunk / TDoc | Authoritative verdict | Comment |
|---|---|---|---|---|
| 1 | TCI-State list within PDSCH-Config, M depends on `maxNumberConfiguredTCIstatesPerCC` | `38.214-5.1.5-001` | Exact match with panel.castle.cloud V15.1.0 | Rel-15 introduction confirmed |
| 2 | The activation command described in 38.321 §6.1.3.70 maps up to 8 sets of TCI states to a DCI codepoint | `38.214-5.1.5-003` | Matches Itecspec 38.321 §5.18 and the sharetechnote MAC CE TCI explanation | Cross-reference accurate |
| 3 | `dl-OrJointTCI-StateList-r17`, `dl-OrJointTCI-StateList`, `tci-SeparateTCI-UpdateMultiActiveTCI-Per…` | `38.214-5.1.5-005`/`-007`/`-003` | Matches the Ofinno whitepaper and the search result name "DLorJoint-TCIState-r17" | Rel-17/18 unified TCI split accurate |
| 4 | §6.1.3.14 TCI States Activation/Deactivation for UE-specific PDSCH MAC CE — "MAC subheader with LCID, variable size" | `38.321-6.1.3.14-001` | Matches the body of ETSI 138 321 V16.1.0/V17.5.0/V18.x.0 §6.1.3.14 | "Rel-15 operation" — release attribution is not quoted directly from the body (slight A4 deduction) |
| 5 | §6.1.3.24 Enhanced PDSCH TCI activation — "MAC PDU subheader with eLCID" | `38.321-6.1.3.24-001` | Matches the ETSI Rel-16+ body | Rel-16 mTRP context accurate |
| 6 | §5.18.23 Unified TCI States Activation/Deactivation — `simultaneousU-TCI-UpdateList1..4` | `38.321-5.18.23-001` | Exact match with the body of ETSI V17.5.0 (verbatim search match) | Rel-17 unified TCI accurate |
| 7 | §5.18.33 Enhanced Unified TCI States Activation/Deactivation MAC CE | `38.321-5.18.33-001` | Matches the body of ETSI V18.x.0 | Rel-18 enhanced split accurate |
| 8 | §6.1.3.70 Enhanced Unified TCI for Joint TCI States / §6.1.3.71 for Separate TCI States | `38.321-6.1.3.70-001`/`-71-001` | Matches the body of ETSI V18.5.0/V18.6.0 §6.1.3.70/71 | joint/separate split accurate |
| 9 | 38.331 IEs: TCI-State, TCI-StateId, TCI-UL-State, TCI-UL-StateId, TCI-ActivatedConfig, LTM-TCI-Info, CandidateTCI-State, CandidateTCI-UL-State | Neo4j RAN2 Section nodes | Matches the Itecspec 38.331 §6.3.2 RRC IE definition locations | Absence of ASN.1 body chunks is honestly marked as a dataset limitation |
| 10 | 38.306 §4.2.15.7.1 BandNR / §4.2.7.4 CA-ParametersNR / §4.2.7.7 FeatureSetUplink / §4.2.23.6.1 capability-table cluster | `38.306-4.2.15.7.1-001`, `38.306-4.2.7.7-001`, etc. | Matches the section title classification of authoritative sources | Identification of exact capability rows is marked as a limitation given the chunk preview cutoff |
| 11 | RAN1 Rel-15 R1-1718541, R1-1720662 "Beam management for NR" ai=7.2.2.3 | TDoc payload | Matches the retrieval log meta | Rel-15 introduction discussion accurate |
| 12 | RAN1 Rel-16 R1-1813443/1903044/1905027 "Enhancements on Multi-beam Operation" ai=7.2.8.3 | TDoc payload | Match | Rel-16 eMIMO WI accurate |
| 13 | RAN1 Rel-17 R1-2100273/2103504/2109103 ai=8.1.1 | TDoc payload | Match | Rel-17 feMIMO WI accurate |
| 14 | RAN2 Rel-17 R2-2110534/2110622 "Inter-Cell Beam Management" ai=8.17.2 / R2-2200599 "RRC aspects for feMIMO" | TDoc payload | Match | Rel-17 inter-cell BM based on unified TCI accurate |
| 15 | RAN1 Rel-18 R1-2300932 ai=9.1.1.1 "Unified TCI Framework for Multi-TRP" | TDoc payload | Matches authoritative verification (3GPP Rel-18 unified TCI multi-TRP extension) | |
| 16 | RAN1 Rel-19 R1-2402686/2404815/2408118 "asymmetric DL sTRP/UL mTRP" ai=9.2.4 | TDoc payload | Match | Aligns with Rel-19 NR MIMO Phase 5 (RP-242394) direction |
| 17 | RAN2 Rel-19 R2-2508663 "MAC issues for MIMO" + RP-242394 citation | TDoc payload | Match | RP-242394 = NR MIMO Phase 5 (Samsung rapporteur) confirmed |
| 18 | Rel-20 R1-2505125/2506063/2506358 6G overview, R2-2508085/2508849 6G mobility ai=10.4 | TDoc payload | Match | Honestly tagged as a discussion stage |

## Hallucinations found

Approximately **1 instance** (slight deduction):

1. "38.321 §6.1.3.14 — PDSCH TCI activation MAC CE operational since Rel-15."
   - The clause body is part of the first Rel-15 NR body (authoritatively confirmed). However, the chunk body does not contain a direct "Rel-15" release attribution. A release attribution inferred from KG/spec history is presented as if it were directly quoted from the body → a weak hallucination.

No speculation is observed in the Rel-19/Rel-20 areas. The initial answer marks every such cell as "not found / limitation / dataset limitation". No 6G discussion is upgraded to a spec change.

## Coverage gaps

Of the 24 matrix cells, 11 are unanswered (Rel-15 exact capability row, Rel-16 capability, Rel-16 38.331 IE body, Rel-17 capability, Rel-18 capability, Rel-19 38.214 body, Rel-19 38.306 capability, 4 Rel-20 cells) — all marked as "dataset limitation" by the initial answer.

Information that exists in authoritative sources but is missing from the initial answer:

- **3GPP Rel-17 unified TCI WID** = RP-211661 (LG Electronics rapporteur). The initial answer establishes the unified TCI introduction flow via RAN2 inter-cell BM discussions like R2-2110534/2110622, but the RP-WID itself is not cited (the SPECTRA RAG TDoc collection prioritization may not include RP-WIDs).
- **3GPP Rel-18 LTM WID** (RP-213588 etc.) — the initial answer retrieves only RAN2 discussions like R2-2207753; no RP-WID citation.
- **Rel-19 NR MIMO Phase 5 WID** (RP-242394) — the initial answer cites RP-242394 directly from the body of R2-2508663 (✅).

→ Although authoritative sources list the RP-WIDs explicitly, the SPECTRA RAG search results do not contain dominant RP-WID chunks, so the answer cannot quote them. This is justified by dataset limitations.

## Authoritative source key facts vs. initial answer

1. **Rel-17 Unified TCI framework**
   - Authority (Ofinno, 3GPP RAN1 Rel-18 page): Rel-17 introduced unified TCI for single-TRP, with two modes — joint TCI (single DL/UL when beam correspondence is assumed) and separate TCI (DL/UL separated). Rel-18 extends this to multi-TRP.
   - Initial answer: Cites §5.18.23 / §6.1.3.47 unified TCI MAC CE, `dl-OrJointTCI-StateList-r17`, joint/separate split — all accurate. ✅

2. **Rel-18 inter-cell beam management & LTM**
   - Authority: Rel-18 introduces L1/L2 mobility mechanisms. Non-serving cell beam management/TA acquisition is added. Unified TCI extends to multi-TRP.
   - Initial answer: §5.18.33 Enhanced Unified TCI MAC CE, §6.1.3.70/71 joint/separate, LTM-TCI-Info IE registration, R1-2309110/2309111 FL summary citation. ✅

3. **Rel-19 mTRP / TCI extension**
   - Authority: NR MIMO Phase 5 (RP-242394, Samsung). Asymmetric DL sTRP/UL mTRP scenario extension.
   - Initial answer: §5.18.36 Candidate Cell TCI, §6.1.3.76/77 Cross-RRH TCI MAC CE nodes, CandidateTCI-State IE, R1-2402686/2404815/2408118 + R2-2508663 (citing RP-242394) — all accurate. ✅

## Overall judgment

- **Trustworthy releases**: Rel-15, Rel-16, Rel-17, Rel-18 — all support spec body chunks + TDocs + Neo4j IE retrieval, and match authoritative sources.
- **Partially trustworthy release**: Rel-19 — RAN2-side MAC CE/IE Neo4j registration is robust, but RAN1 spec body § addition chunks are absent. The asymmetric sTRP/UL mTRP discussion is clear.
- **Weak release (justified non-answer)**: Rel-20 — only 6G overview discussions are retrieved; no spec body changes are identified — root cause is the dataset not yet reflecting the 6G entry phase. The initial answer marks every cell as a limitation.

## System improvement recommendations (RAG perspective)

1. **38.331 ASN.1 IE body chunking improvement (current weakness)**
   - The RAN2 KG registers IE Section nodes (`TCI-State`, `TCI-UL-State`, `TCI-ActivatedConfig`, `LTM-TCI-Info`, `CandidateTCI-State`, `CandidateTCI-UL-State`, etc.), but the ASN.1 IE definition bodies are not retrieved from the `ran2_ts_sections` Qdrant chunks → split IE bodies into "field-level chunks" (e.g., `tci-StatesToAddModList`, `qcl-Type1`, `qcl-Type2`, `referenceSignal`). Add ASN.1 semantic-unit splitting to the Phase-7 RAN2 chunking policy.

2. **Strengthen 38.306 capability table row-level chunks**
   - The currently retrieved chunks expose only the table header (`Definitions for parameters | Per | M | …`). Row-level chunks for exact capability items such as `maxNumberConfiguredTCIstatesPerCC`, `maxNumberActiveTCI-PerBWP`, and unified-TCI-cap rows are needed. Add a "table row-level chunk split" policy to the Phase-7 38.306 table parsing.

3. **TCI-related sectioning strategy**
   - 38.214 §5.1.5 is split into a single large chunk (`-001` ~ `-007`) of 7 pieces, making per-Rel separation difficult. Sub-chunk splitting by release tag (`-r17`, `-r18`, `-r19`) or release-aware metadata is needed. The body contains release tags such as `dl-OrJointTCI-StateList-r17`, but per-chunk retrieval cannot answer release-by-release questions.

4. **Strengthen the RP-WID collection**
   - `ran1_tdoc_chunks`/`ran2_tdoc_chunks` are meeting-centric TDoc collections. Reinforcing RP-WIDs (RP-211661, RP-213588, RP-242394, etc.) as a separate collection or KG metadata would let questions about WID introduction backgrounds quote RP-WIDs directly.

5. **Rel-20 data loading timing**
   - Rel-20 is entering the 6G IMT-2030 phase. Re-loading is needed when spec body change chunks accumulate (estimated 2027–2028). Currently the Rel-20 answer is correctly tagged as "discussion only", so system integrity is preserved.

6. **Release attribution metadata**
   - Even if a chunk body lacks a release indicator (e.g., "Rel-15"), adding metadata that links the chunk to spec history (version 18.x.0, 17.x.0, etc.) into the chunk payload would let attributions like "operational since Rel-15" be backed by direct evidence.

---

## Weakness root-cause classification (D / O / R)

> **D**: Limitations in the 3GPP data itself (timing, completeness) — solved by time
> **O**: Missing KG/ontology modeling — schema enhancement required
> **R**: Limitations of the chunking/embedding/indexing in the VDB build stage — pipeline enhancement required

| # | Weakness | D / O / R | Evidence | Improvement potential |
|---|---|:---:|---|---|
| 1 | Rel-20 TCI-state spec changes not loaded (Rel-20 row of the 24-cell matrix) | **D** | 3gpp.org Rel-20 timeline: Stage-2 freeze 2026-09, Stage-3 freeze 2027-03. The dataset's last meeting RAN1#123/RAN2#132 (2025-Q3~Q4) contains no Rel-20 spec body additions — consistent with the authoritative timeline. | (Resolved by time) |
| 2 | 38.331 `TCI-State` IE / `tci-StatesToAddModList` ASN.1 body not retrieved | **R + O** | (R) 38.331 is chunked per clause and the IE block is not separated from the sectionTitle. (O) The KG has IE nodes only partially; field-level entries like `qcl-Type1`/`qcl-Type2` are missing from `IE`/`RRCParameter` modeling. | High — IE-body-level chunking + full-set KG IE node modeling |
| 3 | 38.306 `maxNumberConfiguredTCIstatesPerCC` / `maxNumberActiveTCI-PerBWP` capability rows not retrieved | **R + O** | (R) 38.306 capability tables are not chunked per row (only the header is exposed). (O) `Capability`/`FeatureGroup` labels are not modeled. | High — table row-level chunking |
| 4 | Core RAN2 TCI introduction discussions in Rel-15 not retrieved (TA and other side topics dominate) | **R** | Rel-15 RAN2-side TCI introduction discussions are scattered, so keyword matching is weak. Release filter + keywords alone do not surface relevant chunks. | Medium — query expansion |
| 5 | Rel-19 38.214/38.306 bodies have weak separate chunk previews | **D + R** | (D) Rel-19 ASN.1 freeze is between 2025-Q4 and 2026-Q1, so the dataset partially reflects it. (R) IE-level chunking of Rel-19 new IEs has not been applied. | Time + IE-level chunking |
| 6 | RP-WID body cannot be cited directly (per-Rel introduction background) | **R** | RP-* TDocs (Plenary) are not loaded as a separate collection; discussions cite RP numbers as references. | Medium — create a `ranX_rp_tdocs` collection |
| 7 | Chunk payload lacks spec version metadata | **R + O** | (R) Qdrant payload has no `specVersion` field (all N/A) — cannot tell whether a chunk is V16/V17/V18 from metadata. (O) Spec ↔ Version graph edges are not modeled. | High — payload schema enhancement |
| 8 | Weak inference behind "operational since Rel-15" for §6.1.3.14 (1 hallucination instance) | **(authoring)** | The initial answer infers a release attribution rather than quoting directly from the chunk body. Not a system limitation — would be directly citable if payload version metadata were available. | (Enhancement needed; tied to #7) |
| 9 | Rel-17 unified TCI framework body / Rel-18 inter-cell BM | **(none)** | No data limitation — every claim is retrieved-grounded. | (D responsibility = 0) |

**Totals**: D 1 (Rel-20 justified non-answer), R 1, R+O 3, D+R 1, authoring 1, no-data-limitation 1.

**Improvement priority**:
1. (P1, R+O) 38.331 IE-level chunking + full-set KG IE nodes — common to Q1/Q2/Q4
2. (P1, R+O) 38.306 capability table row-level chunking
3. (P1, R+O) Add a `specVersion` field to the chunk payload — release attribution can be quoted directly
4. (P2, R) Create a separate RP-WID collection
5. (P4, D) Rel-20 spec body loading is naturally resolved after 2026-09 (Stage-2 freeze) ~ 2027-03 (Stage-3 freeze)
