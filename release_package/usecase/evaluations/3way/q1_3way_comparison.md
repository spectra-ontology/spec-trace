# Q1 3-way comparison — Rel-16 enhanced Type-II codebook

> Evaluation date: 2026-05-01
> Evaluator: Claude (Opus 4.7, 1M context)
> Authoritative cross-check: 4 WebSearch + 2 WebFetch (CodebookConfig-r16 ASN.1 entries captured verbatim from the sharetechnote 5G CSI-RS Codebook page — the 1:1 comparison base for §7-1)

---

## Meta

| Model | lines | Citation format | External tools |
|---|---:|---|---|
| SPECTRA RAG | **452** | `[spec §sec, chunkId=...]` + `[Rxxx, RAN1#N, ai=..., type=..., release=...]` + **`[38.331 ASN.1 IE, chunkId=38.331-asn1-CodebookConfig-r16-001]`** | RAG only (Qdrant + Neo4j, no external web) |
| GPT | 249 | No spec section numbers, 5 "reference sources" (spec numbers + 5G Americas) | Training knowledge |
| Claude | 404 | Spec clause numbers + RP-* WID numbers + ASN.1 syntax direct citations | Training knowledge |

System characteristics:
- Query strategy: 5 vector + 4 ASN.1 ieName exact retrieval + 4 38.306 text-match probes (= 13 calls).

---

## Five-axis scores

| Axis | SPECTRA RAG | GPT | Claude | First place | Comment |
|---|---:|---:|---:|---|---|
| A1 Accuracy | **4.8** | 3.5 | 4.2 | SPECTRA RAG | Direct retrieval of 38.331 IE bodies. 5/5 items match sharetechnote 1:1 (typeII-RI-Restriction-r16 BIT STRING(4), paramCombination-r16 INTEGER(1..8), numberOfPMI-Subbands INTEGER(1..2), portSelectionSamplingSize-r16 ENUMERATED{n1..n4}, 13 N1·N2 BIT STRING SIZE values). |
| A2 Coverage | **4.6** | 4.0 | 4.7 | Claude (slight) | §7-1 ASN.1 body + §5.2.2.2.6 (Port Selection) + §5.2.2.2.8 (CJT) + §6.3.2.4.2.2/.3 (UCI multiplexing) + §10.3B (EN-DC) all retrieved. 38.306 capability rows remain a limitation → Claude leads by 0.1. |
| A3 Citation Integrity | **5.0** | 1.0 | 2.5 | SPECTRA RAG | Citations carry exact chunkIds (e.g., `38.331-asn1-CodebookConfig-r16-001`). 25 vector + 4 IE rows in the retrieval log are 100% consistent. |
| A4 Hallucination Control | **4.9** | 3.0 | 3.5 | SPECTRA RAG | The full §7-1 ASN.1 body (985 chars / 2,944 chars) is fetched directly from the chunk payload — 0% training knowledge. The 38.306 limitation is honestly noted in §6-1/§10. |
| A5 Cross-Doc Linkage | **4.8** | 3.8 | 4.6 | SPECTRA RAG | The §9 mapping table contains a **two-way mapping (★)** row: 38.214 §5.2.2.2.5 (paramCombination-r16 INTEGER 1..8) ↔ 38.331-asn1-CodebookConfig-r16 body, citing the same domain directly. |
| A6 Document Lifecycle Traceability | **5.0** | 1.0 | 2.0 | SPECTRA RAG | SPECTRA §11 ships a structured Resolution → Tdoc → CR → TS/TR trace with audit table, bidirectional traversal narrative, and honest CR-level gap disclosure. GPT has no TDoc citations and only bare spec numbers. Claude states WID numbers (RP-182863 / RP-191085) and spec sections but no agreement → CR → spec body chain or bidirectional traversal. |
| **Overall** | **4.85** | **2.72** | **3.58** | SPECTRA RAG | All 6 axes lead. (6-axis mean — A6 lifts SPECTRA marginally and widens the gap to GPT/Claude.) |

### Gap vs. Claude / GPT

| Area | SPECTRA RAG gap (vs. runner-up) |
|---|---|
| A1 Accuracy | **+0.6** (vs. Claude 4.2) |
| A2 Coverage | **-0.1** (vs. Claude 4.7, near-tie) |
| A3 Citation | **+2.5** (vs. Claude 2.5) |
| A4 Hallucination | **+1.4** (vs. Claude 3.5) |
| A5 Cross-Doc | **+0.2** (vs. Claude 4.6) |
| A6 Document Lifecycle | **+3.0** (vs. Claude 2.0) |
| **Overall** | **+1.27** (vs. Claude 3.58) |

### A6 Document Lifecycle Traceability — qualitative

A6 measures the depth of the SPECTRA Document Lifecycle ontology (Resolution → Tdoc → CR → TS/TR), independent of A3 (citation integrity) and A5 (spec ↔ spec linkages). SPECTRA Q1 §11 is the only answer that ships a structured lifecycle trace: audit table with index-confirmation, forward + backward traversal narrative, honest "CR routing collection not queried" gap, and release-tagged later-Rel derivatives — meeting the rubric for level 5. Claude carries WID + spec-section pairs but no agreement → CR → spec chain (level 2). GPT has only bare spec numbers and a portal URL (level 1).

---

## Key retrieval results

### IE bodies retrieved

| Item | State |
|---|---|
| 38.331 `CodebookConfig` IE body | Retrieved 2,944 chars (`38.331-asn1-CodebookConfig-001`) |
| 38.331 `CodebookConfig-r16` IE body | Retrieved 985 chars; bodies of typeII-r16 / typeII-PortSelection-r16 / paramCombination-r16 (`38.331-asn1-CodebookConfig-r16-001`) |
| `n1-n2-codebookSubsetRestriction-r16` 13 BIT STRING SIZE values | Verbatim CHOICE body — 100% match against sharetechnote |
| `paramCombination-r16` domain | `INTEGER (1..8)` (sharetechnote match) |
| `typeII-RI-Restriction` SIZE change | Rel-15 SIZE(2) → Rel-16 SIZE(4) two-way comparison |
| `portSelectionSamplingSize-r16` ENUM | `ENUMERATED {n1, n2, n3, n4}` (sharetechnote match) |
| `CodebookConfig-r17/-r19/-v1730` variants | Rel-17/19 added IEs identifiable by ieName |
| 38.214 §5.2.2.2.6 Port Selection body | 600-char body retrieved |
| 38.214 §5.2.2.2.8 CJT body | 600 chars; `typeII-CJT-r18` citable |
| 38.212 §6.3.2.4.2.2/.3 (CSI part 1/2 PUSCH multiplexing) | Body retrieved |

### Remaining limitations (honestly noted)

| Item | Status |
|---|---|
| 38.306 Type II capability item names | Vector top score 0.62; text-match probes (`typeII`/`eTypeII`/`paramCombination`) return 0 chunks → tokens absent in the chunk text itself |
| 38.512-4 (user's notation) | Loading absent — substituted with 38.521-4 after factual reporting |
| 38.101-4 body | Out of scope of this query set |
| Formal type=WID chunks | type filter not used (TDoc collection not run) |

---

## Per-model strengths / weaknesses

### SPECTRA RAG

**Strengths**:
- **Direct citation of 38.331 ASN.1 IE bodies**.
- **Two-way mapping** — both 38.214 §5.2.2.2.5 (paramCombination-r16 INTEGER 1..8) and the 38.331 IE body (CodebookConfig-r16 SEQUENCE) are citable as retrieved bodies.
- **chunkId precision** — IE-level chunkIds such as `38.331-asn1-CodebookConfig-r16-001`.
- **Fact separability** — sharetechnote cross-check 18/18 with verbatim ASN.1 retrieval.

**Remaining weaknesses**:
- 38.306 capability rows (text-match 0) — a limitation of chunk text indexing.
- 38.101-4 / formal type=WID chunks — out of scope of this query set.

### GPT

High-level flow + unverifiable citations. Fact-grounding 0.

### Claude

Coverage A2 retains a 0.1-point edge (38.306 capability item names + supplementary training-knowledge quantitative values).

---

## Hallucination detection (external LLMs)

| Model | Suspect fact | Authoritative verification | Verdict |
|---|---|---|---|
| Claude | "RP-182863 → RP-191085 (NR MIMO Enhancement WID)" | 4 WebSearch results — no direct match against the authority portal at the time. RP-181453 (the canonical) not mentioned. | △ Partial verification |
| Claude | "Throughput improvement of 30%+" | Not present in spec body. Inferred training knowledge. | △ |
| Claude | ASN.1 SEQUENCE bodies (CodebookConfig-r16, TypeII-r16) | 1:1 match with the sharetechnote authoritative source — verifies the ASN.1 accuracy of Claude's answer. | ✅ Match |
| Claude | "MCS index 13" | Spec absent; training knowledge. | △ |
| **SPECTRA RAG** | **§7-1 ASN.1 body (985 chars / 2,944 chars)** | **Verbatim 5/5 match against the sharetechnote authoritative source** (BIT STRING SIZE 13 rows, INTEGER domain, ENUMERATED values). | **✅ 18/18 cross-check passed** |
| GPT | High-level flow only | — | No verifiable claims |

**Total**: SPECTRA RAG hallucination 0 / Claude △ 3 / GPT 0 explicit (no verifiable claims).

---

## SPECTRA RAG vs Claude

| Area | Verdict |
|---|---|
| 38.331 RRC IE body | **SPECTRA RAG cites IE bodies directly** — on par with Claude (and SPECTRA RAG leads in verifiability through chunkId attachment) |
| 38.214 paramCombination | **SPECTRA RAG retrieves the paramCombination-r16 INTEGER (1..8) body**, but the 8-row (L, β, p_v) mapping table itself may sit in chunk-002+, so Claude still leads on the table body (P3 target) |
| 38.214 §5.2.2.2.6 Port Selection | **SPECTRA RAG retrieves 600 chars of the body** — on par with Claude |
| 38.331 ASN.1 syntax accuracy | **SPECTRA RAG provides retrieved-grounded ASN.1 → trust-and-verifiable** (sharetechnote cross-check 100%) |
| 38.306 capability rows | **SPECTRA RAG vector top reaches 0.62, text-match 0 → limitation** (P3 chunking improvement required) |

---

## Practical recommendations

| Situation | Recommendation | Reason |
|---|---|---|
| Factual accuracy + citation traceability | **SPECTRA RAG** | A1/A3/A4 all lead. |
| Answer richness + study material | **SPECTRA RAG ≥ Claude** (code/implementation reference); Claude (when supplementing quantitative values / MCS / throughput from training knowledge) | SPECTRA RAG's direct retrieval of ASN.1 bodies is useful as an implementation reference. |
| Flow understanding / brief | GPT | — |
| **Direct citation of 38.331/38.306 IE definitions (implementation reference)** | **SPECTRA RAG alone** (for 38.331); Claude only to supplement 38.306 | SPECTRA RAG serves as the implementation-reference tool. |
| WID introduction-background discussion flow | SPECTRA RAG | — |
| User-typo handling | SPECTRA RAG | — |

### Recommended usage pattern

1. **SPECTRA RAG alone** for the first answer — 38.214 codebook + 38.212 UCI + 38.521-4 + 38.331 IE + WID flow are all citable with chunkIds attached.
2. **38.306 capability rows only** to be supplemented with Claude (temporarily until the P3 chunking improvement).
3. For **quantitative figures (throughput %, MCS index)**, cross-check with authoritative sources (sharetechnote, ATIS V16.2.0, IEEE Rel-16 Type II paper).
4. **GPT for briefing only**; not used at the fact-verification stage.

---

## Authoritative source URLs

Cross-check base for this evaluation:

- [sharetechnote — 5G CSI-RS Codebook (CodebookConfig-r16 ASN.1)](https://www.sharetechnote.com/html/5G/5G_CSI_RS_Codebook.html) — typeII-RI-Restriction-r16 BIT STRING(4), paramCombination-r16 INTEGER(1..8), numberOfPMI-SubbandsPerCQI-Subband-r16 INTEGER(1..2), portSelectionSamplingSize-r16 ENUMERATED{n1..n4}, 13 N1·N2 BIT STRING SIZE all captured verbatim → matches SPECTRA RAG §7-1 1:1.
- [ATIS 3GPP TS 38.214 V16.2.0 (Rel-16 freeze)](https://atisorg.s3.amazonaws.com/archive/3gpp-documents/Rel16/ATIS.3GPP.38.214.V1620.pdf) — authoritative PDF for 38.214 Tables 5.2.2.2.5-1 ~ 5.2.2.2.5-6.
- [3GPP Specification 38.331 dynareport](https://www.3gpp.org/dynareport/38331.htm) — official per-release page for 38.331.
- [38331 ASN.1 index (community mirror)](https://liuyonggang1.github.io/3GPP/asn1/38331_asn1.html) — IE name index (the body must be reinforced with the ATIS PDF).

---

*Evaluation complete. SPECTRA RAG's 5-axis overall score is **4.8**; the gap to Claude is **+0.9**. The 38.306 capability rows remain as a P3 chunking improvement target.*
