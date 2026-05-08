# SPECTRA RAG Use Case Evaluation — 3-way RAG Answer Comparison on 4 Cross-WG Questions

## Purpose

For **four cross-WG integrated questions** that an in-house modem standards engineer might pose in practice, this study **compares answers from three systems using a 5-axis rubric**:

1. **SPECTRA RAG** — the spec-trace project's Neo4j (7687-7691) + Qdrant (6333) RAG. Strictly no external tools or learned knowledge.
2. **GPT** — OpenAI GPT answers (provided by user input).
3. **Claude** — Anthropic Claude answers (provided by user input).

## Folder Structure

```
docs/usecase/
├─ README.md                                 ← this document
├─ answers/                                  ← initial answers (all models, originals preserved)
│   ├─ spectra/                              ← 4 SPECTRA RAG answers
│   ├─ gpt/                                  ← 4 GPT answers
│   └─ claude/                               ← 4 Claude answers
└─ evaluations/                              ← evaluations
    ├─ spectra/                              ← SPECTRA RAG single-model evaluation (against authoritative sources)
    │   └─ q[1-4]_quality_eval.md            ← includes D/O/R classification
    └─ 3way/                                 ← SPECTRA vs GPT vs Claude 3-way comparison
        ├─ q[1-4]_3way_comparison.md         ← per-question 3-way comparison
        └─ summary.md                        ← 4Q synthesis + SPECTRA improvement priorities + practical usage guide
```

## Four Questions Under Evaluation

| # | Question | Related specs | Answers | Single eval | 3-way comparison |
|---|---|---|---|---|---|
| Q1 | Rel-16 enhanced Type-II codebook | 38.211/212/214/306/331/521-4 | [spectra](answers/spectra/q1_rel16_typeii_codebook.md) / [gpt](answers/gpt/q1_rel16_typeii_codebook.md) / [claude](answers/claude/q1_rel16_typeii_codebook.md) | [spectra_eval](evaluations/spectra/q1_quality_eval.md) | [3way](evaluations/3way/q1_3way_comparison.md) |
| Q2 | TCI-state Rel-15 to Rel-20 | 38.214/321/331/306 | [spectra](answers/spectra/q2_tci_state_rel15_to_rel20.md) / [gpt](answers/gpt/q2_tci_state_rel15_to_rel20.md) / [claude](answers/claude/q2_tci_state_rel15_to_rel20.md) | [spectra_eval](evaluations/spectra/q2_quality_eval.md) | [3way](evaluations/3way/q2_3way_comparison.md) |
| Q3 | Beam Failure Detection / Recovery | 38.213/321/331/133/533 | [spectra](answers/spectra/q3_beam_failure_recovery.md) / [gpt](answers/gpt/q3_beam_failure_recovery.md) / [claude](answers/claude/q3_beam_failure_recovery.md) | [spectra_eval](evaluations/spectra/q3_quality_eval.md) | [3way](evaluations/3way/q3_3way_comparison.md) |
| Q4 | Rel-18 LTM (L1/L2 Triggered Mobility) + Rel-19/20 | 38.300/214/321/331/133/306 | [spectra](answers/spectra/q4_ltm_rel18.md) / [gpt](answers/gpt/q4_ltm_rel18.md) / [claude](answers/claude/q4_ltm_rel18.md) | [spectra_eval](evaluations/spectra/q4_quality_eval.md) | [3way](evaluations/3way/q4_3way_comparison.md) |

**Recommended starting point**: [evaluations/3way/summary.md](evaluations/3way/summary.md) — 4Q synthesis + per-model consistent patterns + SPECTRA RAG improvement priorities + practical usage guide.

## Evaluation Workflow (3 Stages)

### Stage 1: Answer Generation (each model independent)
- **SPECTRA RAG**: four parallel multi-agent processes, OpenRouter embeddings + Qdrant top_k=10 + Neo4j Cypher. No external tools allowed, no learned knowledge added. All citations are verifiable through retrieval log JSON files.
- **GPT/Claude**: the user submitted the same questions externally and collected the answers.

### Stage 2: SPECTRA Single-Model Evaluation (`evaluations/spectra/`)
- Stage-1 answers are checked against authoritative sources (IEEE Xplore, ETSI TS, 3gpp.org, sharetechnote, Ofinno, Ericsson).
- 5-axis scoring + hallucination detection + coverage gaps + **D/O/R weakness root-cause classification**.

### Stage 3: 3-way Comparison (`evaluations/3way/`)
- SPECTRA vs GPT vs Claude answers compared on the same 5-axis rubric.
- Per-model strengths/weaknesses + hallucination detection patterns + SPECTRA improvement implications + practical usage conclusions.

## 5-Axis Evaluation Rubric

| Axis | Definition | Key discriminator |
|---|---|---|
| **A1 Accuracy** | Factual agreement with authoritative sources | Quantitative values / RP-WID numbers / spec section numbers |
| **A2 Coverage** | Completeness w.r.t. question items | IE bodies / capability rows / cross-document items |
| **A3 Citation Integrity** | Verifiability of cited facts | SPECTRA chunkId / GPT-Claude spec section numbers / ASN.1 code provenance |
| **A4 Hallucination Control** | Absence of injected learned knowledge | Honest marking of unfound regions, avoidance of speculative Rel-20 fill-ins |
| **A5 Cross-Doc Linkage** | Accuracy of inter-document mapping | RRC IE → MAC-CE → PHY → RRM → capability flow |

## Infrastructure State / Data Freshness (evaluation date 2026-04-29)

Pre-verified that all specs covered by the questions are loaded.

| Spec | Collection | chunks | Notes |
|---|---|---:|---|
| 38.211 | `ran1_ts_sections` | 196 | |
| 38.212 | `ran1_ts_sections` | 219 | |
| 38.213 | `ran1_ts_sections` | 164 | |
| 38.214 | `ran1_ts_sections` | 214 | |
| 38.300 | `ran2_ts_sections` | 466 | |
| 38.306 | `ran2_ts_sections` | 99 | (only capability table headers exposed — R weakness) |
| 38.321 | `ran2_ts_sections` | 288 | |
| 38.331 | `ran2_ts_sections` | 562 | (clause-level chunks; IE blocks not separately split — R weakness) |
| 38.133 | `ran4_ts_sections` | 7,301 | (weak row-level chunking for tables — R weakness) |
| 38.521-4 | `ran5_ts_sections` | 617 | (the user's notation "38.512-4" returns 0 hits; 38.521-4 is the actual spec) |
| 38.533 | `ran5_ts_sections` | 2,221 | (some clauses contain FFS markers — D weakness) |

| WG | Neo4j nodes | Latest meeting |
|---|---:|---:|
| RAN1 | 160,601 | RAN1 #123 |
| RAN2 | 141,126 | RAN2 #132 |
| RAN3 | 71,155 | RAN3 #130 |
| RAN4 | 234,022 | RAN4 #117 |
| RAN5 | 134,196 | RAN5 #110 |

Total Qdrant ~3.7M points (20 collections). Data lag is approximately 6 months (last meeting in 2025-Q4) — normal given the 3GPP meeting cadence. **Rel-20 spec bodies can be loaded only after the timeline milestones of 2026-09 (Stage-2 freeze) to 2027-03 (Stage-3 freeze).**

## Key Results of the 3-way Comparison

### 4Q Aggregate Score Matrix

| Q | SPECTRA | GPT | Claude | Winner |
|---|---:|---:|---:|---|
| Q1 Rel-16 Type-II codebook | **4.5** | 3.1 | 3.9 | SPECTRA |
| Q2 TCI-state Rel-15 to Rel-20 | **4.6** | 3.2 | 3.4 | SPECTRA |
| Q3 BFD/BFR | **4.6** | 3.3 | 3.7 | SPECTRA |
| Q4 Rel-18 LTM + Rel-19/20 | **4.5** | 3.5 | 3.6 | SPECTRA |
| **Average** | **4.55** | **3.28** | **3.65** | **SPECTRA** |

### Per-Axis Averages (4Q combined)

| Axis | SPECTRA | GPT | Claude | SPECTRA advantage/deficit |
|---|---:|---:|---:|---|
| **A1 Accuracy** | **4.55** | 3.65 | 3.75 | +0.80 |
| **A2 Coverage** | 3.95 | 3.78 | **4.58** | -0.63 (Claude leads) |
| **A3 Citation Integrity** | **4.83** | 1.28 | 2.38 | +2.45 |
| **A4 Hallucination Control** | **4.85** | 3.63 | 3.08 | +1.22 |
| **A5 Cross-Doc Linkage** | **4.58** | 3.95 | 4.53 | +0.05 |

**Conclusion**: Only on Coverage does Claude lead (+0.63); SPECTRA RAG leads on the remaining four axes. **The Citation Integrity gap is the largest** — an inherent strength of closed-domain RAG.

### Hallucination Detection (4Q combined)

| Model | Outright assertions | Misclassifications | Disguised assertions | Total |
|---|---:|---:|---:|---:|
| **SPECTRA** | 0 | 0 | 0 | **0** |
| **GPT** | 0 | 1 | 0 | **1** |
| **Claude** | 1 | 0 | ~9 | **~11** |

**Claude's disguised pattern**: attaching guard markers such as "TBD" / "draft" / "(as of the current date)" / "typical" / "default" to assertive citations (RP-234037, Rel-20 ASN.1, Multi-RAT LTM, etc.). Risky when cited in standards meetings.

### Per-Model Consistent Patterns

- **SPECTRA RAG**: + Honesty 4.85 (0 hallucinations) + Citation Integrity 100%; weakness = inability to retrieve IE bodies, capability rows, and quantitative values (system R/O limits)
- **GPT**: + good Rel-20 honesty, safe generalities; weakness = nearly absent citations + avoids quantitative values and detailed IEs
- **Claude**: + richest Coverage 4.58 (ASN.1 IE bodies / MAC-CE bodies); weakness = ~11 disguised hallucination patterns (fake RP-WID citations, speculative Rel-20 ASN.1, "typical" quantitative assertions)

## SPECTRA RAG System Improvement Priorities (D/O/R Classification)

> **D**: temporal limitation of 3GPP data itself (resolved by time) / **O**: missing KG modeling / **R**: VDB build limitation

### P1 (Immediate / affects all 4Q, expected to lift aggregate from 4.55 to ~4.85)

| # | Action | Class | Impact |
|---|---|:---:|---|
| **P1.1** | IE-level chunking of 38.331 ASN.1 + full set of KG IE nodes | R + O | Q1/Q2/Q3/Q4 — direct IE-body citation reaches Claude-level coverage while preserving SPECTRA citation integrity |
| **P1.2** | Row-level chunking of 38.306 capability tables + KG `Capability` label | R + O | Q1/Q2/Q4 — feature-group citations become possible |
| **P1.3** | Extend chunk text preview from 600 to 2000 characters (or remove the cutoff) | R | Q3/Q4 — BLER thresholds, timer values, and ms-level numbers become citable |
| **P1.4** | Add `specVersion` metadata to chunk payloads + Spec↔Version graph edges | R + O | Q2 — direct release attribution |

### P2 (Mid-term, affects some questions)

- P2.1: separate `ranX_rp_tdocs` collection for RP-WIDs + load WID body text (R) — common to all 4Q
- P2.2: row-level chunking of 38.133 RRM tables (R) — Q3
- P2.3: load 38.101-4 into the RAN4 collection (R) — Q1
- P2.4: full set of KG `IE` / `Capability` / `Procedure` nodes + `REFERENCES_CLAUSE` edge from IE→Procedure (O) — common to all 4Q
- P2.5: automatic chunk filter for FFS / Editor's note markers (R) — Q3

### P3 (Long-term, embedding/retrieval tuning)

- P3.1: hybrid sparse (BM25) + dense retrieval — improves ASN.1 IE name matching (R)
- P3.2: post-retrieval expansion to other chunkIndex values within the same clause (R)
- P3.3: stronger use of type filters (e.g., `type=WID`) (R)

### P4 (Resolved by time, D limit)

- Loading Rel-20 spec bodies — feasible after 2026-09 (Stage-2 freeze) to 2027-03 (Stage-3 freeze) (D)

## Practical Usage Guide (Recommendations by Scenario)

| Scenario | Recommended model | Rationale | Caveats |
|---|---|---|---|
| **Drafting standards meeting contributions** | **SPECTRA RAG (1st choice)** | Citation traceability + 0 hallucinations | 38.331 IE bodies are an unchunked region — cross-check Claude's answer against authoritative sources before use |
| **In-house standards study material / overview** | **GPT (1st choice)** | Safe generalities, honest about Rel-20 | Augment with other models for detailed IEs / quantitative values |
| **Rel-X feature comparison / implementation impact assessment** | **Claude (1st choice)** | Richest coverage | RP-WIDs, Rel-20 items, quantitative values, and ASN.1 code must be cross-checked against authoritative sources |
| **Forecasting Rel-19/20 future changes** | **SPECTRA RAG or GPT** | Timeline-consistent, honest | Do not cite Claude's Rel-20 ASN.1 / Multi-RAT LTM assertions |
| **New-hire onboarding** | GPT → Claude (for learning) | Stepwise study | Always verify against authoritative sources before using citations in practice |
| **Quantitative values / RRM ms citation** | **Authoritative sources directly (3gpp.org)** | All three LLMs are weak on quantitative values | After SPECTRA P1.3 reinforcement, SPECTRA becomes usable |

## Conclusion

### Essence of SPECTRA RAG's Advantage

1. **Citation Integrity** (4.83/5) — every fact verifiable 1:1 via chunkId
2. **Honesty** (0 hallucinations) — decisive contrast with Claude's 11 disguised assertions
3. **Rel-20 timeline alignment** — handles the data lag with honest non-answers

### Reinforcement Required for SPECTRA (regions where only Claude is rich)

1. 38.331 ASN.1 IE-body chunking (P1.1, R+O)
2. 38.306 capability row chunking (P1.2, R+O)
3. Extension of chunk preview cutoff (P1.3, R)

### Core Recommendation

**At present, SPECTRA RAG is preferred for standards work**. For 38.331 IEs / 38.306 capability rows / quantitative values, use Claude's answer as supplementary information cross-checked against authoritative sources. **After implementing the four P1 reinforcements, SPECTRA RAG will simultaneously achieve Claude-level richness and SPECTRA's unique honesty + citation traceability** — projected to lift the aggregate from 4.55 to ~4.85. Rel-20 spec bodies will be resolved naturally by the timeline.

## Artifact Summary

```
docs/usecase/
├─ README.md                              ← this document
├─ answers/  (12 files)
│   ├─ spectra/   q[1-4]_*.md
│   ├─ gpt/       q[1-4]_*.md
│   └─ claude/    q[1-4]_*.md
└─ evaluations/
    ├─ spectra/   q[1-4]_quality_eval.md  (incl. D/O/R, 4 files)
    └─ 3way/      q[1-4]_3way_comparison.md + summary.md  (5 files)

scripts/cross-phase/usecase/
├─ q[1-4]_search_*.py                     ← SPECTRA RAG search scripts (for reproducibility)

logs/cross-phase/usecase/
├─ q[1-4]_retrieval_log.json              ← SPECTRA RAG retrieval logs (for audit)
```
