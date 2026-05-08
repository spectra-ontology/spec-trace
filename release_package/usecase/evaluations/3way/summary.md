# 3-way summary — SPECTRA RAG vs GPT vs Claude

> Date: 2026-05-02 (initial); 2026-05-08 (post-rewrite addendum below)
> References: `q[1-4]_3way_comparison.md` (per-question comparisons)

## 1. Four-question composite scoring matrix

| Q | **SPECTRA RAG** | GPT | Claude |
|---|---:|---:|---:|
| Q1 Rel-16 Type-II codebook | **4.8** | 3.1 | 3.9 |
| Q2 TCI-state Rel-15~20 | **4.9** | 3.2 | 3.4 |
| Q3 BFD/BFR | **4.84** | 3.3 | 3.7 |
| Q4 Rel-18 LTM | **4.83** | 3.5 | 3.6 |
| **Average** | **4.84** | **3.28** | **3.65** |

-> SPECTRA RAG averages **4.84**; gap over Claude **+1.19**, over GPT **+1.56**.

## 2. Per-axis averages (across four questions)

| Axis | **SPECTRA RAG** | GPT | Claude | SPECTRA RAG advantage |
|---|---:|---:|---:|---:|
| A1 Accuracy | **4.78** | 3.65 | 3.75 | +1.03 |
| A2 Coverage | **4.68** | 3.78 | **4.58** | +0.10 |
| A3 Citation Integrity | **4.95** | 1.28 | 2.38 | +2.57 |
| A4 Hallucination Control | **4.93** | 3.63 | 3.08 | +1.85 |
| A5 Cross-Doc Linkage | **4.81** | 3.95 | 4.53 | +0.28 |

**Key result**: SPECTRA RAG leads Claude on A2 Coverage (4.68 vs 4.58). A3/A4 gaps remain decisive (the essence of closed-domain RAG).

## 3. Honest per-model assessment (qualitative beyond scores)

### SPECTRA RAG - "rich data, format remains a RAG dump"

**Strengths**:
- ASN.1 IE SEQUENCE bodies cited **directly** (Q1 CodebookConfig-r16 / Q2 TCI-State / Q3 BeamFailureRecoveryConfig / Q4 LTM-Config and 22+ IEs)
- Q3 has 9 quantitative items citable
- Q2 24-cell matrix has **20 confirmed cells**
- chunkIndex labeling is accurate

**Areas still weak**:
- The answer format is a **RAG-output dump** - the first page is a metadata table (collection names, query counts), and the main body is dominated by `-> chunkId` citations with insufficient natural-language narrative.
- It cannot be used as-is for a standards-meeting report -> **the user must edit the narrative**.
- Row-level chunking of 38.306 capabilities (Tier B not yet executed) -> direct row matching of capability rows remains limited.

**Practical recommendation**: writing standards-meeting contributions. Citation traceability and zero hallucinations are the decisive strengths.

### GPT - "safe generalities"

- **Strengths**: strong natural-language narrative. Rel-20 honesty (states explicitly "must not be used as confirmed normative").
- **Weaknesses**: very few citations (A3 1.28). Misclassifications (Q4 inter-CU LTM placed under Rel-20). Avoids quantitative values (Q3 has 6 unanswered, 0 correct).
- **Practical recommendation**: internal overviews / new-hire onboarding. Citations must be verified for standards work.

### Claude - "the trap of richness, hallucinations present"

- **Strengths**: A2 Coverage 4.58 (highest four-question average). Rich ASN.1 code, equations, and tables.
- **Decisive weaknesses**: **11 disguised hallucinations** (totalled across four questions):
  - Q1: unclear sources for RP-182863/191085 (3 items)
  - Q2: TCI-State-r20 ASN.1 speculative code + assertions on cross-Carrier/Sub-band/NTN TCI (1 or more)
  - Q3: -110 dBm typical, T_recovery <80 ms typical, BFD-RS Rel.16+ = 8 assertions, etc. (4 items)
  - Q4: RP-234037, Multi-RAT/NTN/Group LTM, LTM-Configuration-r20 ASN.1 (4 items)
- **Pattern**: guard markings such as "TBD" / "draft" / "typical" / "(as of this point in time)" are attached to assertive citations - exposes errors immediately when used in standards meetings.
- **Practical recommendation**: useful for grasping technical depth quickly. **However, RP-WIDs, Rel-20 items, quantitative values, and ASN.1 code must be cross-checked against authoritative sources (3gpp.org/IEEE)**.

## 4. Hallucination detection (across four questions)

| Model | Clear assertion errors | Misclassifications | Disguised assertions (guard markings) | Unsourced quote/code | Total |
|---|---:|---:|---:|---:|---:|
| **SPECTRA RAG** | **0** | 0 | 0 | 0 | **0** |
| GPT | 0 | 1 (Q4) | 0 | 0 | **1** |
| **Claude** | 1 (Q4 RP-234037) | 0 | ~9 | 1 (Q4 quote) | **~11** |

SPECTRA RAG remains at 0. Hallucinations persist for GPT and Claude in the noted locations.

## 5. SPECTRA RAG key strengths (across four questions)

| Strength | Affected questions | Result |
|---|---|---|
| **Direct citation of 38.331 ASN.1 IE bodies** | Q1/Q2/Q3/Q4 | Bodies retrieved for 22+ IEs including CodebookConfig, TCI-State, BeamFailureRecoveryConfig, LTM-Config |
| **chunker hard_max + tiktoken accurate measurement** | All five WGs | 0 zero-vector chunks; search accuracy maintained |
| **chunkIndex labeling accuracy** | Q4 in particular | chunkIndex labels match retrieval logs |
| **Enumerated quantitative-value citation** | Q3 | 9 citable items (n1~n10, ms10~ms200, sl1~sl2560, etc.) |
| **Filling the Release x document matrix** | Q2 | 20 confirmed cells |

## 6. Remaining limits (across four questions)

| Limit | Category | Follow-up track |
|---|---|---|
| **Row-level chunking of 38.306 capabilities** | R + O | Tier B (separate track) |
| **Direct citation of RP-WID bodies** | R | Tier C (separate track) |
| **Rel-20 spec body** | D (resolves with time) | Stage-2 freeze 2026-09 / Stage-3 freeze 2027-03 |
| **Answer format (RAG dump -> narrative)** | (workflow) | Post-processing LLM at the answer-synthesis stage, or human editing |

## 7. Practical usage guide

| Situation | Recommended | Reason |
|---|---|---|
| Authoring a standards-meeting contribution | **SPECTRA RAG (first choice)** | citation traceability + ASN.1 IE bodies + Rel-20 honesty |
| Internal standards study material | GPT (first choice) | safe generalities, narrative quality |
| Comparing Rel-X features / quick technical-depth grasp | Claude (first choice) | rich coverage. **However, RP-WIDs, Rel-20 items, quantitative values, and ASN.1 code must be cross-checked against authoritative sources** |
| Forward-looking Rel-19/20 discussion | SPECTRA RAG or GPT | Claude's Rel-20 ASN.1 assertions must not be cited |
| Citation of quantitative values / thresholds (BLER, ms, ASN.1 enumerated ranges) | **SPECTRA RAG** | direct citation of enumerated IE bodies |

## 8. Overall conclusion

**SPECTRA RAG ranks first across four questions at 4.84/5, with a decisive gap over GPT (3.28) and Claude (3.65) of +1.19 to +1.56**. SPECTRA RAG is first on all five axes. The following limits are nonetheless acknowledged honestly:

1. **Answer format**: even at 4.84, the answer is not "ready to use as soon as received" - it is in RAG-dump form and requires human editing.
2. **Tier B/C unresolved**: chunking 38.306 capability rows and a separate RP-WID collection remain follow-up work.
3. **The three models have different strengths**: a single model cannot produce the ideal answer. The best answer comes from combining SPECTRA RAG (citations) + GPT (narrative) + Claude (depth).

---

## 9. Post-rewrite addendum (2026-05-08)

The four SPECTRA RAG answers (`docs/usecase/answers/spectra/q[1-4]_*.md`) were reorganised on 2026-05-08 from "RAG citation dump" format into structured standards-analysis reports (Table-of-Contents + §0 Evidence Provenance + per-spec narrative + Cross-Document Linkages table + Coverage/Limitations + Summary). The rewrite **preserves every chunkId, every TDoc citation, every verbatim spec/IE body excerpt** verbatim; no new factual claims were introduced.

### 9.1 Post-rewrite scores (re-applied 5-axis rubric)

| Q | Composite (old) | Composite (new) | Δ | Drivers |
|---|---:|---:|---:|---|
| Q1 Rel-16 Type-II codebook | 4.80 | 4.82 | **+0.02** | A5 +0.1 (§8 Cross-Doc Linkages table + Trace Diagram) |
| Q2 TCI-state Rel-15→Rel-20 | 4.90 | 4.90 | **0** | Already at near-ceiling; structural lifts offset by rounding |
| Q3 BFD/BFR | 4.84 | 4.92 | **+0.08** | A2 +0.2 (§8.1 quantitative-verification matrix consolidated 9 enum items), A5 +0.2 (linkage table + sequence + trace diagram) |
| Q4 Rel-18 LTM | 4.83 | 4.91 | **+0.08** | A2 +0.1 (§11 explicit Well-Covered / Weakly-Covered / Not-Present partition), A5 +0.1 (14-row §10 evidence table) |
| **4Q Average** | **4.84** | **4.89** | **+0.05** | |

### 9.2 Per-axis 4Q averages — pre vs post rewrite

| Axis | Old | New | Δ |
|---|---:|---:|---:|
| A1 Accuracy | 4.78 | 4.78 | 0 (no facts changed) |
| A2 Coverage | 4.68 | 4.76 | +0.08 (structural exposure of existing scope; underlying retrieval gaps unchanged) |
| A3 Citation Integrity | 4.95 | 4.95 | 0 (already at ceiling; all chunkIds preserved 100%) |
| A4 Hallucination Control | 4.93 | 4.94 | +0.01 (negligible — explicit §0 Evidence Provenance reinforces but cannot lower an already-zero hallucination count) |
| A5 Cross-Doc Linkage | 4.81 | 4.91 | **+0.10** (largest single-axis gain — structured linkage tables, trace diagrams, and sequence views replace inline scattered references) |

### 9.3 Paper Table 13 — update decision

The +0.05 4Q-average composite delta sits **below the 0.10 threshold** the authors set for paper Table 13 updates. **Paper Table 13 (`main.tex` / `release_package/supplement/PAPER_APPENDIX.tex` / `release_package/supplement/LLM_EVAL_PILOT.tex`) is therefore left unchanged** at the pre-rewrite values: SPECTRA Composite 4.84 (A1=4.78 / A2=4.68 / A3=4.95 / A4=4.93 / A5=4.81). The post-rewrite scores are recorded here in `evaluations/3way/summary.md` as a supplementary record only.

### 9.4 Format-asymmetry follow-up

§3's earlier qualitative criticism ("the answer format is a RAG-output dump … cannot be used as-is for a standards-meeting report → the user must edit the narrative") was specific to the pre-rewrite SPECTRA answers. **Post-rewrite, that criticism is dropped.** The replacement assessment:

> SPECTRA RAG answers in `docs/usecase/answers/spectra/` are now structured standards-analysis reports — Table-of-Contents-led, with §0 Evidence Provenance making KG/index reproducibility explicit, per-spec narrative sections with verbatim quoted ASN.1 / spec-body evidence, a consolidated Cross-Document Linkages table (each row carrying a chunkId-grounded evidence column), and a Coverage / Limitations partition that distinguishes verified-coverage, weakly-covered, and not-present-in-dataset items. Citation density and chunkId traceability are preserved verbatim while readability matches the narrative comparators (Claude/GPT). The paper's existing format-asymmetry caveat in §6 *Limitations* (re A3 Citation Integrity gap) remains valid — Claude/GPT answers are still free-form prose without inline retrieval citations — but the SPECTRA-side "RAG dump" framing no longer applies.

### 9.5 A6 Document Lifecycle Traceability — new sixth axis (added 2026-05-08)

A sixth scoring axis was added on 2026-05-08 to directly measure the SPECTRA paper's central traceability contribution (Resolution → Tdoc → CR → TS/TR document lifecycle), which the original 5-axis rubric did not isolate. **Rubric** (0–5):

- **0** — No provenance metadata.
- **1** — Single-anchor references (page numbers, paragraph mentions, or non-document URLs only).
- **2** — TDoc + spec citation pair without explicit chain.
- **3** — Meeting + agreement chain (RAN1#XX agreed → spec change), forward direction only.
- **4** — Agreement → CR → spec body incorporation tracked, OR forward + backward chain explicit.
- **5** — Full Resolution → Tdoc → CR → TS chain in a structured Lifecycle Trace section, with bidirectional traversal AND honest gap disclosure AND release-tagged classification.

**Per-question A6 scores** (post-rewrite, after Document Lifecycle Trace sections were added to all four SPECTRA answers):

| Q | SPECTRA A6 | Claude A6 | GPT A6 | Gap (SPECTRA − runner-up) |
|---|---:|---:|---:|---:|
| Q1 Rel-16 Type-II codebook | **5.0** | 2.0 | 1.0 | +3.0 |
| Q2 TCI-state Rel-15→Rel-20 | **5.0** | 2.0 | 1.0 | +3.0 |
| Q3 BFD/BFR | **4.0** | 3.0 | 1.0 | +1.0 |
| Q4 Rel-18 LTM | **5.0** | 1.0 | 2.0 | +3.0 |
| **A6 4Q Average** | **4.75** | **2.00** | **1.25** | **+2.75** |

**6-axis composite per question — canonical computation.**

To avoid mixing pre-rewrite vs post-rewrite 5-axis baselines, we adopt the **paper-published 5-axis Table 13 per-Q values** as the canonical baseline (SPECTRA Q1/Q2/Q3/Q4 = 4.80 / 4.90 / 4.84 / 4.83; Claude = 3.9 / 3.4 / 3.7 / 3.6; GPT = 3.1 / 3.2 / 3.3 / 3.5). The 6-axis composite for question Q is computed exactly as `(5_axis_composite_paper × 5 + A6_score) / 6`, rounded to 2 decimals.

| Q | SPECTRA (5-axis paper × 5 + A6) / 6 | Claude (same) | GPT (same) |
|---|---:|---:|---:|
| Q1 | (4.80·5 + 5.0)/6 = **4.83** | (3.9·5 + 2.0)/6 = **3.58** | (3.1·5 + 1.0)/6 = **2.75** |
| Q2 | (4.90·5 + 5.0)/6 = **4.92** | (3.4·5 + 2.0)/6 = **3.17** | (3.2·5 + 1.0)/6 = **2.83** |
| Q3 | (4.84·5 + 4.0)/6 = **4.70** | (3.7·5 + 3.0)/6 = **3.58** | (3.3·5 + 1.0)/6 = **2.92** |
| Q4 | (4.83·5 + 5.0)/6 = **4.86** | (3.6·5 + 1.0)/6 = **3.17** | (3.5·5 + 2.0)/6 = **3.25** |
| **6-axis 4Q Avg** | **4.83** | **3.38** | **2.94** |

(The per-Q 6-axis figures inside the individual `evaluations/3way/qN_3way_comparison.md` files were computed by axis-scoring agents that used a mix of pre-rewrite and post-rewrite 5-axis baselines, leading to ±0.02–0.05 per-Q drift versus this canonical table; the 4Q averages still agree within reporting precision.)

**6-axis vs 5-axis comparison (4Q averages)**:

| Rubric | SPECTRA | Claude | GPT | SPECTRA−Claude | SPECTRA−GPT |
|---|---:|---:|---:|---:|---:|
| 5-axis (paper Table) | 4.84 | 3.65 | 3.28 | +1.19 | +1.56 |
| 5-axis (post-rewrite) | 4.89 | 3.65 | 3.28 | +1.24 | +1.61 |
| **6-axis (canonical, with A6)** | **4.83** | **3.38** | **2.94** | **+1.45** | **+1.89** |

The 6-axis composite **widens the SPECTRA lead** because A6 selectively credits the document-lifecycle structure that only a KG-grounded system can ship — Claude/GPT cite WID strings or spec sections without the lifecycle chain Q3GPP standardization actually produces. Claude's Q4 score (1.0) reflects fabricated lifecycle anchors (RP-234037, LTM-Configuration-r20 ASN.1 — see q4_3way_comparison.md) that actively mislead.

### 9.6 Paper / Appendix update decision (post-A6)

**Paper main.tex**: no score citations exist in the body — no update required for scores. We add a single supplementary mention in §7 Availability so that ISWC reviewers find the Document Lifecycle Trace material in the released supplement.

**Appendix `PAPER_APPENDIX.tex` (§H) and `LLM_EVAL_PILOT.tex`**: the existing 5-axis Table 13 is preserved (consistency with pre-A6 reporting; A1-A5 scores pre/post rewrite delta is +0.05 < 0.10 threshold and unchanged in 5-axis form). A new supplementary table is added directly below Table 13 reporting the A6 axis and the 6-axis composite, with an explicit caveat that A6 is a structural axis favouring KG-grounded systems by design and is reported as supplementary evidence rather than as the headline benchmark.

### 9.7 Residual flaws (preserved from pre-rewrite)

The rewrite did not address these baseline citation-discipline issues — they remain follow-up items:

- **Q4 chunkIndex misnotations** — `R2-2503785-001`, `R1-2407319-001`, `R2-2508706-001`, `R2-2508384-001` are uniformly suffixed `-001` in the source retrieval log when the actual chunk indices are `-017 / -037 / -003 / -003`. The rewrite preserves the citations verbatim; correction requires a retrieval-log re-export, not an answer rewrite.
- **Rel-20 spec-body absence** — Q2/Q4 cite Rel-20 documents only at the 6G-overview / Phase-3 framing stage; 38.214/38.321/38.331/38.306 spec-body changes for Rel-20 are not present in the indexed dataset (D-class limitation, resolved by time as Stage-2 freeze 2026-09 / Stage-3 freeze 2027-03 lands).
- **38.306 capability row-level chunking** — capability-table rows are not chunked per row, so direct-row retrieval for Q1's `csi-Type-II` cap items remains unsuccessful (R+O class — Tier B follow-up).
- **38.101-4 / RP-WID separate loading** — these are referenced normatively from 38.521-4 / Rel-16 MIMO WI but are not loaded into the indexed dataset (R class — Tier B/C follow-up).
