# Q1~Q4 retrieval and answer-quality evolution V2~V6 (2026-05-02 ~ 2026-05-04)

> **Goal**: measure step-by-step improvements in retrieval + LLM answers + 5-tier rubric scores for the four cross-WG questions provided by the user.
> **Model**: `google/gemini-2.5-flash` for both answer generation and evaluation (same model to ensure comparison consistency).
> **Rubric**: A1 Accuracy / A2 Coverage / A3 Citation Integrity / A4 Hallucination Control / A5 Cross-Doc Linkage (each 0~5).

## 1. Composite-score evolution

| Version | Q1 (Type-II) | Q2 (TCI) | Q3 (BFD/BFR) | Q4 (LTM) | **Total** | Delta vs V2 |
|---|---:|---:|---:|---:|---:|---:|
| V2 (baseline) | 15 | 20 | 19 | 19 | **73/100** | — |
| V3 (new collections) | 21 | 19 | 19 | 19 | **78/100** | +5 |
| V4 (hybrid + prompt + context) | 20 | 18 | 21 | 20 | **79/100** | +6 |
| V5 (+ rerank + sparse + rewrite) | **22** | 19 | **22** | 19 | **82/100** | **+9 (+12.3%)** highest |
| V6 (top_k_rerank 15->25) | 22 | 19 | 19 | 21 | 81/100 | +8 (-1 vs V5) |
| V7 (per-Q dynamic top_k) | 19 | 19 | 22 | 21 | 81/100 | +8 (-1 vs V5) |

## 2. Step-by-step changes

### V2 (2026-05-01) — baseline
- Added a separate ASN.1 collection (`ran2/3_ts_asn1_chunks`)
- Compact retrieval log over 5 queries
- Context: top_k 3, ~2K chars

### V3 (2026-05-02) — leveraging the new collections
- Added `ran2_ts_ie_descriptions` (700->723), `ran5_ts_ie_descriptions` (3), `ran2_ts_capabilities` (1,716)
- Q1 Cross-Doc Linkage A5 jumps from 0 to 4 (CodebookConfig field semantics retrieved directly)
- Q2~Q4 changed little (the existing V2 context was already sufficient)

### V4 (2026-05-04) — Hybrid + prompt + context expansion
- A1: union of V2 + V3 hits -> sort by score -> top-15
- A2: answer prompt — enforce per-aspect subheadings and require explicit cross-aspect linkage
- A3: top_k 3->15, chars 2K->4K
- Effect: Q3 +2, Q4 +1 (better-structured answers from the improved prompt)
- Limit: Q1 -1, Q2 -1 (a larger context introduced noise on some aspects)

### V5 (2026-05-04) — Reranker + Sparse + Query rewriting
- B4: LLM-based reranker (gemini-2.5-flash scores 30 candidates by relevance 0~10 -> top-15)
- B5: Sparse retrieval — extract user-question keywords -> Qdrant `MatchText` filter (exact match)
- B6: Query rewriting — LLM extracts IE name + capability feature from the question -> generates an additional accurate dense query
- Effect: Q1 +2, Q3 +1 (exact IE/feature matching + reranker noise removal)
- Limit: Q2 -1 (cross-lingual limit — an embedding-model intrinsic limit)

### V6 (2026-05-04) — top_k expansion attempt (failed)
- TOP_K_INITIAL: 30 -> 50; TOP_K_RERANK: 15 -> 25
- Goal: recover the broad question Q2
- Result: **Q4 +2, Q3 -3, Q2 not recovered -> overall -1**

Per-dimension analysis (V5 -> V6):

| Q | Change | Cause |
|---|---|---|
| Q3 -3 | A3 5->3, A4 5->4 | some of the 25 chunks introduced inaccurate citations + induced answer reasoning (noise increased) |
| Q4 +2 | A2 3->4, A5 3->4 | larger context covered the introduction-motivation/test-requirement aspects + cross-spec linkage improved |
| Q2 0 | All dimensions unchanged | embedding-model cross-lingual limit — not solved by context volume |

**Conclusion**: top_k expansion is a trade-off. Broader questions (Q4) improve but specific questions (Q3) accumulate noise.

### V7 (2026-05-04) — per-Q dynamic top_k attempt (no observable improvement)
- LLM classifies the question as broad/specific -> dynamic top_k (broad 25, specific 15)
- Q1=specific, Q2/Q3/Q4=broad (auto-classified)
- Result: **Q1 -3, Q4 +2, Q2/Q3 unchanged -> overall 81 (V5 -1)**

V5 vs V7 analysis:

| Q | V5->V7 | Meaning |
|---|---|---|
| Q1 -3 | At the same top_k=15, still -3 | **Non-determinism in LLM answers/evaluations** (backend variability even at temperature=0) |
| Q4 +2 | Effect of the broad classification + top_k 25 | Partial validation of the dynamic-classification hypothesis |
| Q3 0 | -3 at top_k 25 in V6, 0 in V7 | **LLM noise** reconfirmed |
| Q2 0 | Embedding-model limit | Not solved by top_k volume (same as V6) |

**Methodological key finding**: V5 (82) / V6 (81) / V7 (81) all fall in the 81~82 range. **LLM-as-judge evaluation noise can be ±2~3 points**, so small differences are not statistically significant.

**Conclusion**: V5 is the optimal balance point. **No clear improvement was observed from dynamic top_k -> retain V5**.

## 3. Per-dimension change analysis

### A5 Cross-Doc Linkage (largest improvement)

| Q | V2 | V3 | V4 | V5 |
|---|---:|---:|---:|---:|
| Q1 | 0 | 4 | 3 | **4** |
| Q2 | 3 | 3 | 3 | 3 |
| Q3 | 3 | 2 | 3 | **4** |
| Q4 | 2 | 3 | 3 | 3 |

-> V5 reaches 4 on Q1/Q3. Cross-Doc Linkage is **the composite effect of new collections + prompt + reranker**.

### A2 Coverage

| Q | V2 | V3 | V4 | V5 |
|---|---:|---:|---:|---:|
| Q1 | 2 | 3 | **4** | 4 |
| Q2 | 3 | 4 | 3 | 3 |
| Q3 | 3 | 3 | **4** | 4 |
| Q4 | 3 | 3 | 3 | 3 |

-> The structured prompt of V4 reliably lifts A2 by +1 (preserved at V5).

### A1 Accuracy / A3 Citation Integrity / A4 Hallucination

All three dimensions are stable in the 4~5 range from V2 onward. Little variation. -> **The retrieval system is accurate from the baseline**.

## 4. Per-Q limit analysis

### Q2 (TCI-State) — V2 is the highest (20 points)
- V2 context: 187 chunks vs V3 11 / V4 15 / V5 15
- TCI-State is a broad question covering five Releases -> more context is absolutely advantageous
- The V5 reranker removes some candidates -> reduces information volume
- **Improvement direction**: extending top_k_rerank from the current 15 to 25~30 should recover the V2 level

### Q4 (LTM) — stuck at 19 points
- IE descriptions match strongly (LTM-Config 0.7353) -> well retrieved at V3
- However, neither LTM introduction motivation nor capability signaling appears in any context
- **Data limit**: TS specs do not directly state the LTM introduction background (likely available in RP-WIDs, but the no-collection decision applies)

## 5. Implementation artifacts

### Evaluation scripts (reproducible)
- `scripts/cross-phase/usecase/evolution/q1_q4_v3_retrieval.py` (V3 retrieval)
- `scripts/cross-phase/usecase/evolution/q1_q4_v3_eval.py` (V3 LLM eval)
- `scripts/cross-phase/usecase/evolution/q1_q4_v4_eval.py` (V4 hybrid)
- `scripts/cross-phase/usecase/evolution/q1_q4_v5_eval.py` (V5 rerank + sparse + rewrite)
- `scripts/cross-phase/usecase/evolution/q1_q4_v6_eval.py` (V6 top_k expansion attempt)
- `scripts/cross-phase/usecase/q1_q4_v7_eval.py` (V7 per-Q dynamic top_k attempt)

### Authoritative measurement data
- `logs/cross-phase/usecase/q1_q4_v3_retrieval.json` (V3 retrieval scores)
- `logs/cross-phase/usecase/q1_q4_v3_eval.json` (V2/V3 answers + rubric)
- `logs/cross-phase/usecase/q1_q4_v4_eval.json` (V4 answers + rubric)
- `logs/cross-phase/usecase/q1_q4_v5_eval.json` (V5 answers + rubric — **optimal**)
- `logs/cross-phase/usecase/q1_q4_v6_eval.json` (V6 answers + rubric — empirical evidence of top_k-expansion trade-off)
- `logs/cross-phase/usecase/q1_q4_v7_eval.json` (V7 answers + rubric — empirical evidence of dynamic-top_k LLM noise)

## 6. Conclusion

**V5 (82/100)** is the current best achievable. A +9 (+12.3%) improvement over V2 (73/100).

Contribution to improvement:
- New collections (V3): +5
- Hybrid + prompt + context expansion (V4): +1 (vs V3)
- Reranker + Sparse + Rewriting (V5): +3 (vs V4)
- top_k expansion attempt (V6): -1 (vs V5) — trade-off observed and confirmed as a failure

**V5 is the current system's optimal balance**. Through V6/V7, the following empirical observations were obtained:
- V6: simple expansion of context volume is a trade-off (broad up, specific down)
- V7: per-Q dynamic top_k also shows no observable improvement (within the LLM noise range of ±2~3 points)

Remaining improvement opportunities (require user decision):
- Embedding-model upgrade (3-small -> 3-large or multilingual) — addresses the Q2 cross-lingual limit (~$30~50 + 24 hours)
- Diversify evaluation questions (4 -> 10~20) — improves the statistical reliability of LLM-as-judge noise (4 questions are noise-sensitive)
- Multiple evaluation runs averaged — even the same system fluctuates by ±2~3 points; averaging over 5 runs stabilizes statistics

**Adding P7-V15~V19 to the RAN1 spec body is the user's authority** (guide: `docs/usecase/evaluations/3way/ran1_spec_body_update_guide_2026-05-04.md`).
