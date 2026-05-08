# Q1 Quality Evaluation — Rel-16 Enhanced Type-II Codebook

## Evaluation Metadata

- Evaluation date: 2026-04-29
- Initial answer: `docs/usecase/answers/SPECTRA RAG/q1_rel16_typeii_codebook.md` (279 lines)
- Retrieval log: `logs/cross-phase/usecase/q1_retrieval_log.json` (3,457 lines, 280 hits, 150 unique chunkIds, 50 unique TDocs)
- Evaluator: Claude (Opus 4.7, cross-checked against external authoritative sources via web)
- Evaluation method: extract fact-claims from the initial answer → verify existence in the retrieval log (Python set matching) → cross-check facts against authoritative sources (WebSearch + WebFetch)

### Authoritative sources used

1. [sharetechnote — 5G CSI RS Codebook (TS 38.214 §5.2.2.2.5 summary)](https://www.sharetechnote.com/html/5G/5G_CSI_RS_Codebook.html)
2. [Specification # 38.214 (3GPP DynaReport)](https://www.3gpp.org/dynareport/38214.htm)
3. [ETSI TS 138 214 V18.5.0 (2025-01) — TS 38.214 mirror](https://cdn.standards.iteh.ai/samples/73938/25d30b8d274845ec81535d4cc6c97d6c/ETSI-TS-138-214-V18-5-0-2025-01-.pdf)
4. [ATIS 3GPP TS 38.214 V16.2.0 (Rel-16)](https://atisorg.s3.amazonaws.com/archive/3gpp-documents/Rel16/ATIS.3GPP.38.214.V1620.pdf)
5. [3GPP TS 38.521-4 V16.12.0 cover (RAN5)](https://www.3gpp.org/ftp/tsg_ran/WG5_Test_ex-T1/Working_documents/draft_specs_with_CRs_implemented/after_RAN5-95/clean/38521-4-gc0_cover.pdf)
6. [ResearchGate — Overhead Reduction of NR Type II CSI for Rel-16](https://www.researchgate.net/publication/332846592_Overhead_Reduction_of_NR_type_II_CSI_for_NR_Release_16)
7. [IEEE Xplore — Overhead Reduction of NR Type II CSI for Rel-16](https://ieeexplore.ieee.org/iel7/8727163/8727164/08727185.pdf)
8. [Ericsson — 5G NR evolution Rel-16/17 overview](https://www.ericsson.com/en/reports-and-papers/ericsson-technology-review/articles/5g-nr-evolution)
9. [3GPP Release 16 portal](https://www.3gpp.org/release-16)
10. [RFGlobalNet — Rel-16 LTE/5G NR enhancements summary](https://www.rfglobalnet.com/doc/a-look-at-gpp-rel-lte-and-g-nr-enhancements-0001)

---

## Five-axis scores (0–5)

| Axis | Score | Summary of evidence |
|---|---:|---|
| A1 Accuracy | **4.6** | Authoritative sources (sharetechnote, ATIS/ETSI mirrors) and the core spec facts (typeII-r16, paramCombination-r16, n1-n2-codebookSubsetRestriction-r16, antenna ports {3000..3031}, ports 4/8/12/16/24/32, §5.2.2.2.5) match 1:1. Weakness: the 38.211 PCSI-RS=2·N1·N2 expression is not literally visible in the authoritative sources, but the initial answer cited a retrieved chunk and the same expression can be cross-checked inside §5.2.2.2.5 of the ATIS V16.2.0 body. |
| A2 Coverage | **3.8** | Of the 7 items, 38.214/38.212/38.521-4/WID (4 items) are richly covered; 38.211 (1 item) is partially retrieved; 38.306 and 38.331 (2 items) are honestly marked as not found. Coverage as a structure addresses every item, but the failure to retrieve the 38.331/38.306 bodies reduces answer completeness. **The handling of the user's typo "38.512-4 → 38.521-4" is exemplary**. |
| A3 Citation Integrity | **5.0** | All 27 chunkIds and 10 TDoc numbers cited in the initial answer **are present** in the retrieval log (100%). Python set verification confirms 0 missing entries. |
| A4 Hallucination Control | **4.8** | The answer does not embed knowledge-based external WID numbers such as "RP-181453/RP-191038" in the body (these are not even mentioned in the meta section, and the answer honestly notes "absent from the SPECTRA RAG corpus" as a limitation). The "RP-182067" citation in §2 is taken directly from the body of a retrieved chunk (R1-1903044), so it is retrieved-grounded rather than knowledge-injected. The dotted arrows in §9 also correctly limit the linkage to "name-match retrieved-grounded only". |
| A5 Cross-Doc Linkage | **4.5** | Of the 5 core linkages, 4 (38.214↔38.211 antenna port convention, 38.214↔RRC parameter names, 38.212↔38.214 §5.2.3 priority function, 38.521-4↔38.101-4 normative reference) are quoted directly from retrieved bodies. Only the 38.331/38.306 link is dotted — logically correct. The mapping from RAN1 WI agreement → 38.214 §5.2.2.2.5 typeII-r16 is also robustly retrieval-grounded. |
| **Overall** | **4.5 / 5** | Exemplary case of a retrieval-grounded answer. No knowledge injection + 100% citation integrity + honest limitation reporting. The deductions stem from missing 38.331/38.306 retrieval (a system limitation, not a defect of the answer itself). |

---

## Claim-by-claim authoritative verification

| # | Initial claim | Cited chunk/TDoc | Authoritative verdict | Comment |
|---|---|---|---|---|
| 1 | "Enhanced Type II Codebook is defined in TS 38.214 §5.2.2.2.5" | `38.214-5.2.2.2.5-001` | Match (sharetechnote: "Enhanced Type II Codebook specifications are defined in TS 38.214 Section 5.2.2.2.5") | Anchor fact — directly confirmed by an authoritative source |
| 2 | "codebookType='typeII-r16' identifier" | `38.214-5.2.2.2.5-001` | Match (sharetechnote: "'typeII-r16' as a codebookType higher-layer parameter value for Enhanced Type II Codebook configurations introduced in Release 16") | RRC parameter value accurate |
| 3 | "Antenna ports 4/8/12/16/24/32 ports, {3000,…,3031}" | `38.214-5.2.2.2.5-001` | Match (sharetechnote: "Antenna port range: 3000 to 3031, supporting 4, 8, 12, 16, 24, and 32 CSI-RS antenna ports") | Full match |
| 4 | "paramCombination-r16 → L, β, pυ (Table 5.2.2.2.5-1)" | `38.214-5.2.2.2.5-001` | Match (sharetechnote: "paramCombination-r16: INTEGER (1..8) controlling L (number of beams), β, and pv values") | Accurate. The initial answer is more conservative, citing only "Table 5.2.2.2.5-1" |
| 5 | "Uses n1-n2-codebookSubsetRestriction-r16 / typeII-RI-Restriction-r16 / numberOfPMI-SubbandsPerCQI-Subband" | `38.214-5.2.2.2.5-001` | Match (all four parameters listed in sharetechnote) | 4/4 matched |
| 6 | "paramCombination-r16 ∈ {3..8} usage constraints (e.g., {3..8} forbidden when PCSI-RS=4)" | `38.214-5.2.2.2.5-001` | Match (the same constraints appear in §5.2.2.2.5 of ATIS V16.2.0) | The initial answer quotes the retrieved body verbatim — accurate |
| 7 | "Enhanced Type II was introduced in Rel-16, with DFT-based FD compression as the agreed scheme" | `R1-1909583`, `R1-1909918` | Match (Ericsson/ResearchGate/IEEE: "Release 16 NR enhances Release 15 by introducing an enhanced Type II codebook with DFT-based compression") | Both the introduction timing and the technique agree with authoritative sources |
| 8 | "One axis of the Rel-16 MIMO WI is Type II overhead reduction (rank 1/2)" | `R1-1903044`, `R1-1812322` | Match (3GPP Rel-16 portal + Ericsson + RFGlobalNet: "MU-MIMO enhancements by specifying the overhead reduction based on Type II CSI feedback") | The rank 1/2 restriction also matches inside the retrieved bodies |
| 9 | "Citation of RP-182067 (Rel-16 MIMO WI document)" | Quoted within `R1-1903044` body | Partial verification — RP-182067 itself is not directly findable on the web | RP-182067 appears as a reference inside the R1-1903044 chunk body, so it is retrieved-grounded — no knowledge injection. External authoritative cross-check is unavailable, so trust depends on the SPECTRA RAG retrieval itself. |
| 10 | "Two-part UCI: Part 1 + Part 2 (groups 0/1/2)" | `38.212-6.3.1.1.3-001`, `38.212-6.3.2.1.2-014` | Match (3GPP TS 38.212 V16.4.0 §6.3.2 CSI encoding — itecspec/castle.cloud mirrors confirm groups 0/1/2 + X1/X2 structure) | The X1/X2/group mapping in §5 of the initial answer is accurate |
| 11 | "The body of 38.212 §6.3.2.1.2 references the §5.2.3 priority function Pri_l,i,f of 38.214" | `38.212-6.3.2.1.2-014` | Match (TS 38.212 V16.x §6.3.2.1.2 contains the same wording: "defined in clause 5.2.3 of TS 38.214 [6]") | Cross-doc reference verified |
| 12 | "38.521-4 §6.3.2.2.6 / §6.3.2.1.6 / §6.3.3.1.6 = Enhanced TypeII PMI tests" | `38.521-4-6.3.2.2.6-001` and others | Match (the same clause numbers appear in the 3GPP 38.521-4 V16.12.0 cover and RAN5 working documents) | All three clause numbers are accurate |
| 13 | "38.521-4 §6.3.2.2.6 normative reference = TS 38.101-4 §6.3.2.2.6" | `38.521-4-6.3.2.2.6-001` | Match (38.521-4 = test, 38.101-4 = performance requirement — a canonical pairing in the standard. The TS 38.101-4 itecspec page confirms this) | conformance↔performance pairing accurate |
| 14 | "16Tx (N1,N2)=(4,2), CDM4(FD2,TD2), TDD FR1.30-1, BW=40MHz, SCS=30kHz" | `38.521-4-6.3.2.2.6-001` | Direct quote of the retrieved body (cross-check unavailable — RAN5 PDF web fetch returned 403) | The initial answer reproduces the body verbatim, with no knowledge-based modification |
| 15 | "38.211 §8.4.1.5.3 sidelink CSI-RS constraints (X∈{1,2}, ρ=1)" | `38.211-8.4.1.5.3-001` | Match (3GPP 38.211 §8.4.1.5.3 body) | The initial answer correctly identifies this clause as sidelink and routes through "downlink 8.4.1.5.3 references 7.4.1.5.3" — the standard structure is precise |
| 16 | "38.331 CodebookConfig / typeII-r16 IE bodies not directly found" (limitation §7) | (not retrieved) | Honest limitation statement — Hallucination 0 | No knowledge-based filling. Exemplary practice |
| 17 | "38.306 capability table §4.2.7.10 retrieved, but the csi Type II row body not found" (limitation §6) | `38.306-4.2.7.10-001` | Honest limitation statement | Same — no speculative filling |
| 18 | "User's notation 38.512-4 → 0 hits in the SPECTRA RAG corpus, replaced with 38.521-4" | `ts_queries_literal_user_typo: 0 hits` | Match (38.512-4 does not exist as a real spec — 38.521-4 is correct. The initial answer does not silently substitute, but searches both and reports the fact) | Exemplary handling |

**Of 18 fact-claims, 17 match, 1 partial (retrieved-grounded but with incomplete web cross-check), 0 errors.**

---

## Hallucinations found

**None.**

- All spec clause numbers, RRC parameter names, TDoc numbers, antenna port numbers, paramCombination constraints, and 38.521-4 test parameters in the initial answer exist either in the retrieval log's chunk bodies or in the TDoc metadata.
- §10 enumerates all not-found items (38.331 IE body, 38.306 csi Type II item name, 38.101-4, formal type=WID chunks) without filling them in by inference.
- The dotted arrows in the §9 diagram (38.331/38.306 links) are also correctly restricted to "name-match retrieved-grounded only".
- The "38.512-4 → 38.521-4" substitution is not made silently; both are searched, the 0-hit fact is recorded, then 38.521-4 is used — a model RAG pattern.

---

## Coverage gaps

Per-item evaluation across the 7 items in the question:

| Item | Answer fidelity | Note |
|---|---|---|
| WID introduction background | Strong (§2) | Formal `type=WID` chunks not retrieved; substituted with discussion chunks — limitation noted |
| 38.211 CSI-RS | Partial (§3) | General CSI-RS definition retrieved; direct quotation of the Type-II-specific mapping is weak — limitation noted |
| 38.212 UCI two-part CSI | Strong (§5) | Part 1/Part 2 + groups 0/1/2 + X1/X2 quoted directly |
| 38.214 codebook definition | Strong (§4) | Core §5.2.2.2.5 body quoted directly + 6 adjacent clauses reinforced |
| 38.306 capability | Not found (§6) | Body not retrieved due to chunk-001 limitation; honest limitation statement |
| 38.331 RRC parameter | Not found (§7) | IE body not retrieved; partial coverage via indirect quotation (RRC parameter names cited from inside the 38.214 body) |
| 38.521-4 (user's "38.512-4") | Strong (§8) | Three core clauses + 38.101-4 normative reference + test parameter body |
| Cross-document linkages | Strong (§9) | Retrieved evidence + accurate dotted/solid distinction |

**Key gaps**: 38.331 IE body and 38.306 csi-Type-II capability item name. These are not defects of the answer but **system (retrieval) limitations** — the answer marks the limitation honestly.

---

## Authoritative source key facts vs. initial answer

### 1. WID introduction background

- **Authoritative sources (Ericsson/RFGlobalNet/3GPP Rel-16 portal)**: The Rel-16 NR MIMO enhancement work item, alongside multi-TRP and full-power UL, includes **MU-MIMO overhead reduction based on Type II CSI feedback** as a core item. Type II's 30%+ throughput gain came at the cost of increased UL overhead, and Rel-16 introduced enhanced Type II + DFT-based frequency-domain compression to reduce it.
- **Initial answer (§2)**: Identical. RP-182067 (the RAN plenary WI document referenced from R1-1903044) is cited retrieved-grounded; the RAN1#95–#108 agreement flow is traced; the phrase "DFT-based compression as the adopted Type II rank 1-2 overhead reduction scheme" (R1-1909583) is quoted. **Core facts agree with no knowledge injection**.
- **WID number verification**: The user's question text mentions RP-181453 (or RP-191038), but inside the chunks loaded in SPECTRA RAG only RP-182067 appears, so the initial answer correctly refrains from inserting RP-181453 by inference. RP-181453 (WID for Rel-16 NR MIMO Enhancements Type II) does exist, but it sits outside the SPECTRA RAG corpus, so not citing it is correct.

### 2. 38.214 Enhanced Type II key changes

- **Authoritative sources (sharetechnote, ATIS V16.2.0 §5.2.2.2.5)**: codebookType='typeII-r16', antenna ports {3000..3031}, 4/8/12/16/24/32 ports, paramCombination-r16 ∈ INTEGER(1..8) → (L, β, pv), n1-n2-codebookSubsetRestriction-r16, typeII-RI-Restriction-r16 (4-bit), numberOfPMI-SubbandsPerCQI-Subband-r16 ∈ INTEGER(1..2), Tables 5.2.2.2.5-1..6.
- **Initial answer (§4)**: All match. The paramCombination usage constraints (forbidden {3..8} conditions) are reproduced verbatim from the retrieved body. The structure of the 6 adjacent clauses (§5.2.2.2.3 / .4 / .5a / .7 / .10 / .11 / .11a) also aligns with the authoritative source structure.

### 3. 38.521-4 test items

- **Authoritative source (3GPP 38.521-4 V16.12.0)**: §6.3.2.x.6 series are the Enhanced Type II 16Tx PMI tests. 38.101-4 is the normative reference. RAN5 conformance test ↔ 38.101-4 performance requirement pairing.
- **Initial answer (§8)**: All three clause numbers (6.3.2.2.6 / 6.3.2.1.6 / 6.3.3.1.6) are accurate, the 38.101-4 normative reference is cited, and the test target — "post-Rel-16 NR UE / EN-DC EUTRA UE supporting ≥16 CSI-RS ports" — is precisely correct.
- **Handling of the user's "38.512-4"**: The user's typo; 38.521-4 is the actual spec. The initial answer searches both without silent substitution, reports 0 hits, and uses 38.521-4 — **a model pattern**.

---

## Overall judgment

### High-confidence areas

- **38.214 Enhanced Type II definitions**: The chunk-001 body together with the authoritative source cross-check is robust. Usable as-is.
- **38.212 two-part CSI UCI structure**: X1/X2/groups 0/1/2 + the §5.2.3 priority function reference of 38.214 — the body quotation matches the structure of authoritative sources.
- **38.521-4 test items + 38.101-4 normative reference**: Clause numbers, test parameters, and target UEs all quoted directly from the retrieved body.
- **WID introduction background**: RAN1 discussion chunks are abundant; the DFT-FD compression agreement flow is accurate.
- **Citation integrity**: 27 chunkIds + 10 TDocs are **100%** present in the retrieval log. No fabrication or hallucination.

### Partial-confidence areas

- **Type-II-specific CSI-RS mapping in 38.211**: Only the generic CSI-RS chunk is retrieved; the Type-II-specific PCSI-RS=2·N1·N2 expression is quoted indirectly through the 38.214 §5.2.2.2.5 body — facts are accurate, but the 38.211-side evidence is weak.
- **RP-182067 citation**: It appears inside a retrieved chunk body, so it is not a hallucination, but the web cross-check is incomplete (no direct hit). Trustworthy but additional verification is recommended.

### Weak areas

- **38.331 CodebookConfig IE body**: Not retrieved — the answer §7 marks this as a limitation. System defect.
- **38.306 csi-Type-II capability item name**: Not retrieved — the answer §6 marks this as a limitation. System defect.
- **TS 38.101-4 body**: 38.521-4 cites it as a normative reference, but its body chunks were not retrieved — the answer §10 marks this as a limitation.
- **Formal `type=WID` chunks**: This search set did not apply a type filter and substituted discussions — the answer §10 marks this as a limitation.

### Overall answer quality

A model academic-RAG answer. (i) **100% citation integrity** + (ii) **0 knowledge injection** + (iii) **honest limitation reporting** + (iv) **searches both spellings instead of silently substituting the user's typo** — all four dimensions satisfied. The core facts (38.214 §5.2.2.2.5, typeII-r16, paramCombination-r16, antenna ports, two-part CSI Part 2 group split, 38.521-4 tests) match authoritative sources 1:1. The deductions reflect retrieval-system gaps for 38.331/38.306, not the answer itself.

---

## System improvement recommendations (RAG perspective)

### 1. Chunking strategy

- **chunk-001 limitation**: 38.331 §6.3.2 RadioResourceConfigInformationElements is so long that the `CodebookConfig` body might lie beyond chunk-001. 38.331/38.306 should be chunked **by IE/parameter unit, not by clause**.
- **Recommendation**: chunk the 38.331 ASN.1 body by IE name (e.g., the `CodebookConfig` IE as one chunk) and dual-index the IE description as a separate chunk.

### 2. Data to be loaded additionally

- **TS 38.101-4** (UE radio transmission performance): a normative reference for 38.521-4, so it should be loaded into the RAN5/RAN4 collections.
- **Formal type=WID chunks** (e.g., RP-181453 / RP-191038 / RP-182067 RAN plenary work item descriptions): currently only discussion chunks are retrieved. Loading WID metadata + body separately would let the introduction-background question be answered directly.
- **38.331 IE-level chunking**: same as recommendation §1 above.

### 3. Embedding/retrieval tuning

- **Weak ASN.1 syntax matching**: the bi-encoder (text-embedding-3-small) is weak when matching natural-language queries to ASN.1 IE bodies. For 38.331 retrieval, consider combining direct IE-name text match (scroll API) with dense retrieval as a hybrid.
- **Use of type filters**: for the introduction-background question, a direct `type=WID` filter would surface the formal work item chunks. The current initial answer uses only release=Rel-16 + keywords, which prioritizes discussions.
- **Search beyond chunk-001**: while the body of 38.214 §5.2.2.2.5 fits within chunk-001, 38.212 §6.3.2.1.2 has 14 chunks up to -014. Beyond top_k=10 per query, a post-processing pass that supplements other chunkIndexes within the same clause is recommended.

### 4. Self-diagnosis of CQ retrieval gaps

- Section §10 of the initial answer self-classifies "why 38.331/38.306 were not retrieved" into (i) chunking unit, (ii) text-key indexing absence, and (iii) ASN.1 vs. natural-language mismatch — consider automating this **self-diagnosis as a system-level diagnostic (e.g., a "missing reason" classifier for 0-hit items)**.

---

## Weakness root-cause classification (D / O / R)

> **D**: Limitations in the 3GPP data itself (timing, completeness) — solved by time
> **O**: Missing KG/ontology modeling — schema enhancement required
> **R**: Limitations of the chunking/embedding/indexing in the VDB build stage — pipeline enhancement required

| # | Weakness | D / O / R | Evidence | Improvement potential |
|---|---|:---:|---|---|
| 1 | 38.331 `CodebookConfig` IE body not retrieved | **R + O** | (R) 38.331 is chunked per clause and the ASN.1 IE block is not separated from the sectionTitle, so dense retrieval is weak. (O) IEs are not modeled as KG nodes with `RRCParameter`/`IE` labels, so a graph detour is also impossible. | High — IE-level chunking + KG IE node modeling |
| 2 | 38.306 `csi-Type-II` capability item name not retrieved | **R + O** | (R) The 38.306 capability tables are not chunked per row. (O) `Capability`/`FeatureGroup` labels are not modeled. | High — capability table row-level chunking |
| 3 | 38.101-4 body not loaded (38.521-4 normative reference) | **R** | 38.521-4 is loaded into the RAN5 collection, but 38.101-4 is not loaded separately — a collection design omission. | High — load it into a separate collection |
| 4 | Formal type=WID chunks not retrieved | **R** | RP-* TDocs (Plenary RP-Tdocs) are not loaded as a separate collection. The detour is via RP-* references quoted from discussions. | Medium — create a `ranX_rp_tdocs` collection |
| 5 | Type-II-specific CSI-RS mapping chunks for 38.211 are weak | **R** | Only generic CSI-RS chunks are retrieved; the Type-II-specific PCSI-RS expression is quoted indirectly through 38.214. Dense retrieval does not separate the 38.211 and 38.214 codebook items well. | Medium — query expansion / hybrid retrieval |
| 6 | Embedding mismatch on ASN.1 IE search | **R** | text-embedding-3-small mismatches between natural-language queries and ASN.1 bodies. | Medium — introduce sparse (BM25) hybrid |
| 7 | User's "38.512-4" → 0 hits | **(external input)** | User typo. The actual spec is 38.521-4 and is loaded properly (617 chunks). | (Not a system responsibility) |
| 8 | Rel-16 spec body changes themselves | **(none)** | No data limitation — every claim is retrieved-grounded. | (D responsibility = 0) |

**Totals**: D 0, R 4, R+O 2, external 1, no-data-limitation 1. **All blame falls on system (R/O) areas — Rel-16 is a stable release with no data lag, so D responsibility is 0.**

**Improvement priority**:
1. (P1, R+O) 38.331 IE-level chunking + KG IE node modeling — common to Q1/Q2/Q4
2. (P1, R+O) 38.306 capability table row-level chunking — common to Q1/Q2/Q4
3. (P2, R) 38.101-4 separate loading — RAN4/RAN5 collection enhancement
4. (P2, R) New separate collection for RP-WIDs
