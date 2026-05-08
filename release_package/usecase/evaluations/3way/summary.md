# 3-way summary — SPECTRA RAG vs GPT vs Claude

> Date: 2026-05-02
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
