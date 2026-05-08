# 3-way summary — SPECTRA RAG (P2 + ASN.1) vs GPT vs Claude

> Date: 2026-05-02
> References: `summary.md` (earlier summary), `q[1-4]_3way_comparison_v2.md` (per-question current comparisons)

## 1. Four-question composite scoring matrix (earlier -> current)

| Q | SPECTRA RAG (earlier) | **SPECTRA RAG** | GPT (no change) | Claude (no change) |
|---|---:|---:|---:|---:|
| Q1 Rel-16 Type-II codebook | 4.5 | **4.8** | 3.1 | 3.9 |
| Q2 TCI-state Rel-15~20 | 4.6 | **4.9** | 3.2 | 3.4 |
| Q3 BFD/BFR | 4.6 | **4.84** | 3.3 | 3.7 |
| Q4 Rel-18 LTM | 4.5 | **4.83** | 3.5 | 3.6 |
| **Average** | **4.55** | **4.84** (+0.29) | **3.28** | **3.65** |

-> SPECTRA RAG averages **4.84**; gap over Claude **+1.19**, over GPT **+1.56** (compared with the earlier gaps of +0.90 and +1.27, this is a decisive widening).

## 2. Per-axis averages (across four questions, earlier vs current)

| Axis | SPECTRA RAG (earlier) | **SPECTRA RAG** | GPT | Claude | SPECTRA RAG advantage |
|---|---:|---:|---:|---:|---:|
| A1 Accuracy | 4.55 | **4.78** | 3.65 | 3.75 | +1.03 |
| A2 Coverage | 3.95 | **4.68** | 3.78 | **4.58** | +0.10 (Claude pursued) |
| A3 Citation Integrity | 4.83 | **4.95** | 1.28 | 2.38 | +2.57 |
| A4 Hallucination Control | 4.85 | **4.93** | 3.63 | 3.08 | +1.85 |
| A5 Cross-Doc Linkage | 4.58 | **4.81** | 3.95 | 4.53 | +0.28 |

**Key change**: A2 Coverage moves from 3.95 to 4.68 - with P2 + ASN.1, SPECTRA RAG overtakes Claude (4.58) for the first time. A3/A4 gaps remain decisive (the essence of closed-domain RAG).

## 3. Honest per-model assessment (qualitative beyond scores)

### SPECTRA RAG - "rich data, format remains a RAG dump"

**Key changes compared with earlier**:
- ASN.1 IE SEQUENCE bodies cited **directly** (Q1 CodebookConfig-r16 / Q2 TCI-State / Q3 BeamFailureRecoveryConfig / Q4 LTM-Config and 22+ IEs)
- Q3 quantitative values - **9 items now citable** (previously 6 unanswered)
- Q2 24-cell matrix moves from **13 confirmed -> 20 confirmed** (+7 cells)
- chunkIndex labeling accuracy improved (the prior `-001` blanket-labeling error resolved)

**Areas still weak**:
- The answer format is still a **RAG-output dump** - the first page is a metadata table (earlier vs current comparison, collection names, query counts), and the main body is dominated by `-> chunkId` citations with insufficient natural-language narrative.
- It cannot be used as-is for a standards-meeting report -> **the user must edit the narrative**.
- Row-level chunking of 38.306 capabilities (Tier B not yet executed) -> direct row matching of capability rows remains limited.

**Practical recommendation**: writing standards-meeting contributions. Citation traceability and zero hallucinations are the decisive strengths.

### GPT - "safe generalities, no change"

- Identical to earlier (not regenerated).
- **Strengths**: strong natural-language narrative. Rel-20 honesty (states explicitly "must not be used as confirmed normative").
- **Weaknesses**: very few citations (A3 1.28). Misclassifications (Q4 inter-CU LTM placed under Rel-20). Avoids quantitative values (Q3 has 6 unanswered, 0 correct).
- **Practical recommendation**: internal overviews / new-hire onboarding. Citations must be verified for standards work.

### Claude - "the trap of richness, hallucinations preserved"

- Identical to earlier (not regenerated).
- **Strengths**: A2 Coverage 4.58 (highest four-question average). Rich ASN.1 code, equations, and tables.
- **Decisive weaknesses**: **11 disguised hallucinations** (totalled across four questions):
  - Q1: unclear sources for RP-182863/191085 (3 items)
  - Q2: TCI-State-r20 ASN.1 speculative code + assertions on cross-Carrier/Sub-band/NTN TCI (1 or more)
  - Q3: -110 dBm typical, T_recovery <80 ms typical, BFD-RS Rel.16+ = 8 assertions, etc. (4 items)
  - Q4: RP-234037, Multi-RAT/NTN/Group LTM, LTM-Configuration-r20 ASN.1 (4 items)
- **Pattern**: guard markings such as "TBD" / "draft" / "typical" / "(as of this point in time)" are attached to assertive citations - exposes errors immediately when used in standards meetings.
- **Practical recommendation**: useful for grasping technical depth quickly. **However, RP-WIDs, Rel-20 items, quantitative values, and ASN.1 code must be cross-checked against authoritative sources (3gpp.org/IEEE)**.

## 4. Hallucination detection (across four questions, earlier = current)

| Model | Clear assertion errors | Misclassifications | Disguised assertions (guard markings) | Unsourced quote/code | Total |
|---|---:|---:|---:|---:|---:|
| **SPECTRA RAG** | **0** | 0 | 0 | 0 | **0** |
| GPT | 0 | 1 (Q4) | 0 | 0 | **1** |
| **Claude** | 1 (Q4 RP-234037) | 0 | ~9 | 1 (Q4 quote) | **~11** |

**Effect of P2 + current**: SPECTRA RAG remains at 0. GPT and Claude were not regenerated, so hallucinations persist in the same locations.

## 5. SPECTRA RAG key improvement areas (earlier -> current, across four questions)

| Improvement | Affected questions | Result |
|---|---|---|
| **Direct citation of 38.331 ASN.1 IE bodies** (P1.1 ASN.1 collection added + P2 chunker tiktoken) | Q1/Q2/Q3/Q4 | Bodies retrieved for 22+ IEs including CodebookConfig, TCI-State, BeamFailureRecoveryConfig, LTM-Config |
| **chunker hard_max + tiktoken accurate measurement** | All five WGs | 36 zero-vector chunks -> 0; search accuracy restored |
| **chunkIndex labeling accuracy** | Q4 in particular | 4 prior `-001` blanket-labeling errors resolved |
| **Enumerated quantitative-value citation** | Q3 | 6 unanswered -> 9 citable (n1~n10, ms10~ms200, sl1~sl2560, etc.) |
| **Filling the Release x document matrix** | Q2 | 13 confirmed -> 20 confirmed (+7 cells) |

## 6. Remaining limits (still unresolved in current version, across four questions)

| Limit | Category | Follow-up track |
|---|---|---|
| **Row-level chunking of 38.306 capabilities** | R + O | Tier B (separate track) |
| **Direct citation of RP-WID bodies** | R | Tier C (separate track) |
| **Rel-20 spec body** | D (resolves with time) | Stage-2 freeze 2026-09 / Stage-3 freeze 2027-03 |
| **Answer format (RAG dump -> narrative)** | (workflow) | Post-processing LLM at the answer-synthesis stage, or human editing |

## 7. Practical usage guide (current update)

| Situation | Recommended | Reason |
|---|---|---|
| Authoring a standards-meeting contribution | **SPECTRA RAG (first choice)** | citation traceability + ASN.1 IE bodies + Rel-20 honesty |
| Internal standards study material | GPT (first choice) | safe generalities, narrative quality |
| Comparing Rel-X features / quick technical-depth grasp | Claude (first choice) | rich coverage. **However, RP-WIDs, Rel-20 items, quantitative values, and ASN.1 code must be cross-checked against authoritative sources** |
| Forward-looking Rel-19/20 discussion | SPECTRA RAG or GPT | Claude's Rel-20 ASN.1 assertions must not be cited |
| Citation of quantitative values / thresholds (BLER, ms, ASN.1 enumerated ranges) | **SPECTRA RAG** | direct citation of enumerated bodies; ASN.1 collection is leveraged |

## 8. Overall conclusion

**SPECTRA RAG ranks first across four questions at 4.84/5, with a decisive gap over GPT (3.28) and Claude (3.65) of +1.19 to +1.56**. With P2 + ASN.1, the earlier Coverage weakness is resolved, and SPECTRA RAG is first on all five axes. The following limits are nonetheless acknowledged honestly:

1. **Answer format**: even at 4.84, the answer is not "ready to use as soon as received" - it is in RAG-dump form and requires human editing.
2. **Tier B/C unresolved**: chunking 38.306 capability rows and a separate RP-WID collection remain follow-up work.
3. **The three models have different strengths**: a single model cannot produce the ideal answer. The best answer comes from combining SPECTRA RAG (citations) + GPT (narrative) + Claude (depth).
