# 3-way summary — SPECTRA RAG vs GPT vs Claude

> Evaluation date: 2026-05-02 (initial pilot); 2026-05-08 (final consolidation)
> References: `q[1-4]_3way_comparison.md` (per-question comparisons)

## 1. Four-question composite scoring matrix (6-axis)

| Q | **SPECTRA RAG** | GPT | Claude |
|---|---:|---:|---:|
| Q1 Rel-16 Type-II codebook | **4.83** | 2.75 | 3.58 |
| Q2 TCI-state Rel-15→Rel-20 | **4.92** | 2.83 | 3.17 |
| Q3 BFD/BFR | **4.70** | 2.92 | 3.58 |
| Q4 Rel-18 LTM | **4.86** | 3.25 | 3.17 |
| **4Q Average** | **4.83** | **2.94** | **3.38** |

→ SPECTRA RAG averages **4.83**; gap over Claude **+1.45**, over GPT **+1.89**.

## 2. Per-axis 4Q averages

| Axis | **SPECTRA RAG** | GPT | Claude | SPECTRA RAG advantage |
|---|---:|---:|---:|---:|
| A1 Accuracy | **4.78** | 3.65 | 3.75 | +1.03 |
| A2 Coverage | **4.68** | 3.78 | 4.58 | +0.10 |
| A3 Citation Integrity | **4.95** | 1.28 | 2.38 | +2.57 |
| A4 Hallucination Control | **4.93** | 3.63 | 3.08 | +1.85 |
| A5 Cross-Doc Linkage | **4.81** | 3.95 | 4.53 | +0.28 |
| A6 Document Lifecycle Traceability | **4.75** | 1.25 | 2.00 | +2.75 |
| **Composite (6-axis)** | **4.83** | **2.94** | **3.38** | **+1.45** |

**Key result**: SPECTRA RAG leads on every axis. The decisive contributions are A3 Citation Integrity (+2.57), A6 Document Lifecycle Traceability (+2.75), and A4 Hallucination Control (+1.85).

## 3. Honest per-model assessment (qualitative beyond scores)

### SPECTRA RAG — rich data, structured standards-analysis reports

**Strengths**:
- ASN.1 IE SEQUENCE bodies cited **directly** (Q1 CodebookConfig-r16 / Q2 TCI-State / Q3 BeamFailureRecoveryConfig / Q4 LTM-Config and 22+ IEs)
- Q3 has 9 quantitative items citable
- Q2 24-cell matrix has **18 ✅ + 2 ⚠️ + 4 ❌ (Rel-20 honestly reported)**
- chunkIndex labeling is accurate
- Structured standards-analysis reports — Table-of-Contents-led, with §0 Evidence Provenance making KG/index reproducibility explicit, per-spec narrative sections with verbatim quoted ASN.1 / spec-body evidence, a consolidated Cross-Document Linkages table (each row carrying a chunkId-grounded evidence column), a Coverage / Limitations partition, and an explicit Document Lifecycle Trace section that walks Resolution → Tdoc → CR → TS/TR for each release in scope.

**Areas still weak**:
- Row-level chunking of 38.306 capabilities (Tier B not yet executed) → direct row matching of capability rows remains limited.
- Direct citation of RP-WID bodies (Tier C) — the WID layer is currently surfaced via discussion-document references rather than RP-* TDoc chunks.

**Practical recommendation**: writing standards-meeting contributions. Citation traceability, zero hallucinations, and the Document Lifecycle Trace are the decisive strengths.

### GPT — safe generalities

- **Strengths**: strong natural-language narrative. Rel-20 honesty (states explicitly "must not be used as confirmed normative").
- **Weaknesses**: very few citations (A3 1.28). Misclassifications (Q4 inter-CU LTM placed under Rel-20). Avoids quantitative values (Q3 has 6 unanswered, 0 correct). No TDoc / Resolution / CR provenance — A6 1.25 across 4Q is the lowest among the three systems.
- **Practical recommendation**: internal overviews / new-hire onboarding. Citations must be verified for standards work.

### Claude — the trap of richness, hallucinations present

- **Strengths**: A2 Coverage 4.58 (highest non-SPECTRA average). Rich ASN.1 code, equations, and tables.
- **Decisive weaknesses**: **11 unsupported claims** (canonical breakdown summing to exactly 11; matches the paper Appendix Table 5 surrounding text "the 11 unsupported quotes detected for Claude"):
  - Q1 — 3 items: RP-182863 / RP-191085 (WID numbers cited without authoritative grounding) + "Throughput improvement of 30%+" (training-knowledge claim, not in spec body)
  - Q2 — 1 item: speculative `TCI-State-r20` ASN.1 SEQUENCE block including `crossCarrierRefRS-r20` / `subbandTCI-Application-r20` / `ntn-DopplerComp-r20` (Rel-20 spec body does not exist)
  - Q3 — 3 items: "-110 dBm typical" (RRC threshold), "T_recovery < 80 ms typical FR2" (operational ballpark, not in 38.133), "BFD-RS Rel.16+ = 8" (default count)
  - Q4 — 4 items: RP-234037 (incorrect WID number for Rel-18 LTM), Multi-RAT LTM concept, NTN/Group LTM concept, speculative `LTM-Configuration-r20` ASN.1
  - **Total: 3 + 1 + 3 + 4 = 11**
- **Counting rule** (disclosed for reproducibility): "an unsupported claim is a distinct fabricated/under-grounded token, where (i) RP-* WID number pairs presented as `RP-X / RP-Y` with no archive citation count as 2 distinct items, (ii) a speculative ASN.1 SEQUENCE block under a hedged header (e.g., '(not yet finalized)') counts as 1 cluster regardless of how many `-rXX` sub-fields it contains, and (iii) a numeric value attributed to an RRC parameter without spec citation counts as 1 even when the value carries a guard like 'typical'." Stricter rule (hedge-aware, RP-pair clustered) gives 6; looser rule (split every `-r20` sub-field) gives 14+. The "11" reported in this paper uses the rule above.
- **Internal consistency note** (Q3): Claude's q3 answer contains an internal contradiction ("BFD-RS Rel.16+ up to 64 RSs" at one location vs "up to 8 or more" at another) — counted as one item ("BFD-RS Rel.16+ = 8") in the breakdown above; if the contradiction itself were counted separately the total would be 12.
- **Pattern**: guard markings such as "TBD" / "draft" / "typical" / "(as of this point in time)" are attached to assertive citations — exposes errors immediately when used in standards meetings.
- **Practical recommendation**: useful for grasping technical depth quickly. **However, RP-WIDs, Rel-20 items, quantitative values, and ASN.1 code must be cross-checked against authoritative sources (3gpp.org/IEEE)**.

## 4. Hallucination detection (across four questions)

| Model | Clear assertion errors | Misclassifications | Disguised assertions (guard markings) | Unsourced quote/code | Total |
|---|---:|---:|---:|---:|---:|
| **SPECTRA RAG** | **0** | 0 | 0 | 0 | **0** |
| GPT | 0 | 1 (Q4) | 0 | 0 | **1** |
| **Claude** | 1 (Q4 RP-234037) | 0 | 9 | 1 (Q4 LTM-Config-r20 quote) | **11** |

SPECTRA RAG remains at 0. Hallucinations persist for GPT and Claude in the noted locations.

## 5. SPECTRA RAG key strengths (across four questions)

| Strength | Affected questions | Result |
|---|---|---|
| **IE-level ASN.1 ingestion: each 38.331 IE body becomes a Qdrant chunk + a KG node simultaneously** | Q1/Q2/Q3/Q4 | 22+ IE bodies citable verbatim by IE name (e.g., `CodebookConfig-r16`, `TCI-State`, `TCI-UL-State-r17`, `CandidateTCI-State-r18`, `LTM-QCL-Info-r18`, `BeamFailureRecoveryConfig`, `RadioLinkMonitoringConfig`, `BeamFailureDetectionSet-r17`, `RACH-ConfigGeneric`, `LTM-Config`). The IE-level dual indexing (vector + ontology) is the structural differentiator versus other telecom KG resources in scope (TSpec-LLM, GSMA `telecom-kg-rel19`), which model the *content* of specifications without an IE-level RRC schema layer. |
| **Release-extension-block traceability via `[[ ... -rXX ]]` chunks** | Q2 (TCI-state Rel-15→Rel-20), Q3 (BeamFailureDetectionSet-r17), Q4 (LTM extensions) | Each IE preserves its release extension blocks (`[[ additionalPCI-r17 ... ]]`, `[[ tag-Id-ptr-r18 ... ]]`, `[[ pathlossOffset-r19 ... ]]`); per-release diff is auditable directly from the indexed chunk without a CR-by-CR docx diff. Spec-implementer value: a release-walkthrough that previously required manual CR review is now a KG/Qdrant query. |
| **Enumerated quantitative-value citation from IE bodies** | Q3 (BFD/BFR), Q1 (paramCombination), Q2 (TCI extensions) | 9 enum-bound thresholds citable verbatim (`beamFailureInstanceMaxCount {n1..n10}`, `beamFailureRecoveryTimer {ms10..ms200}`, `ra-ResponseWindow` Rel-15 baseline + Rel-16 `[[v1610: sl60, sl160]]` + Rel-17 `[[v1700: sl240..sl2560]]`, `paramCombination-r16 INTEGER (1..8)`, `n1-n2-codebookSubsetRestriction-r16` 13-element CHOICE, etc.). Claude relies on training memory and is correct on common IEs but fabricates `TCI-State-r20` / `LTM-Configuration-r20` (not in any released spec), which IE-level retrieval cannot generate. |
| **Document Lifecycle Trace section (Resolution → Tdoc → CR → TS/TR)** | Q1/Q2/Q3/Q4 | Per-question §11 (or §13 in Q4) walks the chain release-by-release with bidirectional traversal, audit table, release-tagged TDoc classification, and honest gap disclosure (CR chunks not loaded; RP-WID bodies indirect; Rel-20 spec adoption absent). The structural artefact A6 scores against. |
| **Filling the Release × document matrix** | Q2 | 18 ✅ + 2 ⚠️ + 4 ❌ (Rel-20 honestly reported) — Claude fills 24/24 only by speculating Rel-20 IE bodies. |
| **chunker hard_max + tiktoken accurate measurement** | All five WGs | 0 zero-vector chunks; search accuracy maintained — pipeline-level robustness for the IE-level chunking convention. |
| **chunkIndex labeling accuracy** | Q4 in particular | chunkIndex labels match retrieval logs (with one preserved audit-trail caveat in Q4 §13.6). |

## 6. Remaining limits (across four questions)

| Limit | Category | Follow-up track |
|---|---|---|
| **Row-level chunking of 38.306 capabilities** | R + O | Tier B (separate track) |
| **Direct citation of RP-WID bodies** | R | Tier C (separate track) |
| **Rel-20 spec body** | D (resolves with time) | Stage-2 freeze 2026-09 / Stage-3 freeze 2027-03 |
| **Q3 A6 capped at 4.0** | (lifecycle structure) | Rel-17 RAN1/RAN2 contribution layer is IE-only — no R1-/R2- TDoc citation, plus the Agreement → CR → spec-body link cites no CR number |

## 7. Practical usage guide

| Situation | Recommended | Reason |
|---|---|---|
| Authoring a standards-meeting contribution | **SPECTRA RAG (first choice)** | citation traceability + ASN.1 IE bodies + Document Lifecycle Trace + Rel-20 honesty |
| Internal standards study material | GPT (first choice) | safe generalities, narrative quality |
| Comparing Rel-X features / quick technical-depth grasp | Claude (first choice) | rich coverage. **However, RP-WIDs, Rel-20 items, quantitative values, and ASN.1 code must be cross-checked against authoritative sources** |
| Forward-looking Rel-19/20 discussion | SPECTRA RAG or GPT | Claude's Rel-20 ASN.1 assertions must not be cited |
| Citation of quantitative values / thresholds (BLER, ms, ASN.1 enumerated ranges) | **SPECTRA RAG** | direct citation of enumerated IE bodies |
| Document lifecycle reconstruction (Resolution → Tdoc → CR → TS) | **SPECTRA RAG** | only system with structured Lifecycle Trace + bidirectional traversal + gap disclosure |

## 8. Overall conclusion

**SPECTRA RAG ranks first across four questions at 4.83/5 (6-axis composite), with a decisive gap over Claude (3.38) of +1.45 and over GPT (2.94) of +1.89**. SPECTRA RAG leads on all six axes. The largest single-axis contributors to the lead are A6 Document Lifecycle Traceability (+2.75 over Claude), A3 Citation Integrity (+2.57), and A4 Hallucination Control (+1.85). The following limits are nonetheless acknowledged honestly:

1. **Tier B/C unresolved**: chunking 38.306 capability rows and a separate RP-WID collection remain follow-up work.
2. **The three models have different strengths**: a single model cannot produce the ideal answer. The best answer comes from combining SPECTRA RAG (citations + lifecycle), GPT (narrative), and Claude (depth).

## 9. Residual flaws (system-level follow-ups)

The following baseline citation-discipline issues are tracked as system-level follow-ups, not retrieval-stage fabrications:

- **Q4 chunkIndex misnotations** — `R2-2503785-001`, `R1-2407319-001`, `R2-2508706-001`, `R2-2508384-001` are uniformly suffixed `-001` in the source retrieval log when the actual chunk indices are `-017 / -037 / -003 / -003`. Correction requires a retrieval-log re-export.
- **Rel-20 spec-body absence** — Q2/Q4 cite Rel-20 documents only at the 6G-overview / Phase-3 framing stage; 38.214/38.321/38.331/38.306 spec-body changes for Rel-20 are not present in the indexed dataset (D-class limitation, resolved by time as Stage-2 freeze 2026-09 / Stage-3 freeze 2027-03 lands).
- **38.306 capability row-level chunking** — capability-table rows are not chunked per row, so direct-row retrieval for Q1's `csi-Type-II` cap items remains unsuccessful (R+O class — Tier B follow-up).
- **38.101-4 / RP-WID separate loading** — these are referenced normatively from 38.521-4 / Rel-16 MIMO WI but are not loaded into the indexed dataset (R class — Tier B/C follow-up).
