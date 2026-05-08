# System-level systemic improvement plan — recurrence-prevention focus

> **Motivation**: user request — "anchor the improvements verified in PoC into the official baseline (spec) / implementation / docs so they do not recur. Not patchwork; if we rebuild from raw data starting at Phase-0, this issue must not reoccur."
> Date: 2026-04-29 (revised: RAN1 separation + wording fix)
> References: [root_cause_analysis.md](root_cause_analysis.md), [p1_poc_results.md](p1_poc_results.md)

## 0. Core principles (per user direction)

1. **Mandatory rebuild-scenario verification**: the pass criterion for every action is "If we restart from raw data at Phase-0 today, does this issue recur?"
2. **No patchwork**: post-processing only `chunks.json` without amending the chunker code/spec means recurrence on rebuild -> spec, implementation, and docs must all be updated.
3. **No edits to RAN1** (CLAUDE.md principle): RAN1 spec / implementation / step docs are not editable by Claude. **The user edits these directly**. Claude provides only a RAN1 guide.
4. **Wording fix**: not "data loss". The data (docx source) is preserved; the omission occurred at the **chunking step (Indexing gap)**.

## 1. The real scope of the problem (5 WG combined audit)

The earlier analysis focused on RAN2; a 5 WG audit reveals a **system-level** flaw:

### Distribution of huge chunks (Qdrant measurements)

| Collection | Total chunks | >7.5K tokens (over embedding limit) | >30K tokens (severe) | Notes |
|---|---:|---:|---:|---|
| `ran1_ts_sections` | 952 | 6 | 0 | RAN1 PHY spec — healthy |
| `ran2_ts_sections` | 2,315 | 8 | 2 | 38.306 BandNR 100K tokens |
| `ran3_ts_sections` | 3,529 | 6 | 0 | Healthy |
| `ran4_ts_sections` | 15,778 | **30** | **3** | 38.101-1 inter-band config 38K tokens |
| `ran5_ts_sections` | 9,929 | **698** | 0 | Many huge tables in test specs |
| **Total** | 32,503 | **748** | **5** | |

-> The four-question evaluation revealed only **the tip of the iceberg**. Across all 5 WGs, 748 chunks lose search accuracy due to exceeding the embedding limit.

### Chunker policy defects (common across 5 WGs)

| Defect | Location | Impact |
|---|---|---|
| **Paragraph-only split, no hard_max** | 5 WG `01_parse_ts_sections.py` `split_giant_section()` | A huge table = a single paragraph -> not splittable -> 748 chunks exceed the embedding limit |
| **Blanket ASN.1 skip policy** | RAN2/3/4/5 (RAN1 excluded) `is_asn1_heading()` | 38.331 alone has 760 sections; thousands of IE-body sections missing across 5 WGs |
| **No chunk-size validation in the Phase-7 completion gate** | 5 WG `validation/01_validate_search.py` | Huge chunks pass without warnings |

### Structural root causes

1. **Phase-7 chunkers are separate code per WG** (RAN1/RAN2/RAN3/RAN4/RAN5) -> the same defect is duplicated five times ([CLAUDE.md "phase-6/10/11 code duplication is intended"](../../../../CLAUDE.md) — a side-effect of that policy here)
2. **No common chunker library** -> a fix in one place fails to synchronize across 5 WGs
3. **The 8K-token limit of the embedding model (text-embedding-3-small) is not stated in the chunker spec**
4. **No automated chunk-quality validation**

## 2. 5-layer improvement design

### Layer 0: Evaluation verification (already complete)

[p1_poc_results.md](p1_poc_results.md):
- **P1.2 PoC**: 8 huge chunks of 38.306 -> 229 chunks split, score +5.3%, eType-II capability bodies retrieved directly
- **P1.1 PoC**: 22 LTM IEs of 38.331 loaded into a separate collection, score +8.0%, ASN.1 bodies retrieved directly

-> Effect verified. Proceed with full rollout.

### Layer 1: Immediate code changes (today)

#### 1.1 New shared chunker library (`scripts/cross-phase/common/chunker.py`)

> "Needing to fix the same defect in 5 WGs simultaneously = no shared library" is the real cause. Fixing each WG separately invites future drift.

**Responsibilities**:
- `split_giant_section_v2(paragraphs, hard_max=7500, target=2000, overlap=100)` — paragraph-unit + hard_max enforced
- `split_text_by_rows_or_chars(text, target=2000)` — force-split a giant paragraph by row/character
- `extract_asn1_ies(docx_path) -> list[dict]` — extract ASN.1 IE SEQUENCE/CHOICE from docx (for separate collections)
- `validate_chunk_size(chunks, hard_max=7500) -> dict` — return validation results

**Application**: replace 5 WG `01_parse_ts_sections.py` `split_giant_section` with imports.

#### 1.2 ASN.1 policy change — separate collection instead of skip

Change the existing `is_asn1_heading() -> continue` flow to:
1. Upon detecting an ASN.1 section, only record sectionTitle/level in main chunks (heading entry)
2. Generate IE-unit chunks from the body via `extract_asn1_ies()`
3. Load into a separate collection `ran{N}_ts_asn1_chunks`

**Apply to**: RAN2/3/4/5 (skip RAN1 because ASN.1 is rare)

#### 1.3 Immediate re-indexing (5 WGs)

- Run the existing chunker -> regenerate chunks.json
- In-place Qdrant update (preserve existing collection IDs; refresh vector + payload only)
- Add new collection `ran{N}_ts_asn1_chunks`

**Cost estimate**:
- Chunk splitting: ~32K -> ~35K chunks (small increase)
- ASN.1 IEs: ~1,500 across 5 WGs
- Embedding cost <= about $0.5

### Layer 2: Spec corrections in 5 WGs (today / tomorrow)

Add to each WG's `docs/RAN{N}/phase-7/specs/tdoc_vectordb_specs(TS).md`:

#### 2.1 Strengthening P7-V06/V07 (chunk-split thresholds)

Existing:
```
[P7-V06] SPLIT_THRESHOLD = 10,000 tokens
[P7-V07] SPLIT_TARGET = 2,000 tokens
```

Updated:
```
[P7-V06] SPLIT_THRESHOLD = 10,000 tokens (paragraph-unit split trigger)
[P7-V07] SPLIT_TARGET = 2,000 tokens (split target)
[P7-V11 new] HARD_MAX = 7,500 tokens (8,192 embedding limit minus a safety margin).
              If a single paragraph exceeds HARD_MAX, force-split by row or by characters.
[P7-V12 new] EMBEDDING_MODEL = openai/text-embedding-3-small (max 8,192 tokens).
              When the chunker is changed, verify alignment with this model's limit.
```

#### 2.2 ASN.1 policy change (RAN2/3/4/5)

Existing (`§2.6.3 RAN2 phase-7 spec`):
> Exclude 760 ASN.1 definition sections (51% of 38.331). Reason: degraded embedding quality.

Updated:
```
§2.6.3 [updated] ASN.1-definition-section policy (Spec V2)

Earlier policy: excluded from main chunks (V1).
New policy (V2, updated 2026-04-29):
  - main chunks (`ran{N}_ts_sections`): preserve only ASN.1 headings (level + parent); body excluded
  - separate collection (`ran{N}_ts_asn1_chunks`): IE-unit body (SEQUENCE/CHOICE/ENUMERATED) loaded
  - At search time: if the user query contains an IE-name pattern (e.g., "LTM-Config IE"), search the separate collection first

Limits of the V1 policy:
  - 0 retrievals from 38.331/38.355 ASN.1 bodies -> queries like "What fields does LTM-Config IE contain?" are unanswerable
  - Coverage weakness against external LLMs (Claude) (detected in the four-question usecase evaluation)
  - Detailed verification: docs/usecase/evaluations/3way/p1_poc_results.md

Effect of V2 (38.331 LTM 22 IE PoC):
  - Average search-score improvement +8.0%
  - ASN.1 SEQUENCE bodies citable directly
  - False positives removed (e.g., the "LTM-CSI-ReportConfig" query previously returned §5.5.1 Introduction; after the change it returns the LTM-CSI-ReportConfig-r18 IE accurately)
```

### Layer 3: Recurrence-prevention automation (this week)

#### 3.1 Chunk-quality validation script

`scripts/cross-phase/validation/validate_chunk_quality.py`:

```python
"""Auto-validate chunk quality of 5 WG TS Section VectorDBs.

Validation items:
  1. Chunk tokenCount distribution (max <= HARD_MAX=7500)
  2. Enforce zero chunks above the embedding limit (-> FAIL)
  3. Regression test for core ASN.1 IEs (LTM-Config, CodebookConfig, TCI-State, etc., must be searchable)
  4. Auto-classify root cause when huge chunks are detected (single paragraph / table / Annex body, etc.)
"""
```

**P7 completion gate**: PASS of this script is a precondition for declaring Phase-7 complete.

#### 3.2 ASN.1 IE regression test

`scripts/cross-phase/validation/validate_asn1_retrieval.py`:

```python
"""Regression test for searchability of core ASN.1 IEs.

Test items (5 WGs):
  - 38.331 LTM-Config-r18 -> ran2_ts_asn1_chunks search -> top-3 hit
  - 38.331 CodebookConfig -> ran2_ts_asn1_chunks search -> top-3 hit
  - 38.331 TCI-State -> ran2_ts_asn1_chunks search -> top-3 hit
  - 38.413 NGAP IE -> ran3_ts_asn1_chunks search -> top-3 hit
  - and so on
"""
```

#### 3.3 CI/CD integration

- Auto-validation when the chunker code changes (pre-commit hook)
- Auto-check chunk quality when a new spec is added

### Layer 4: Documenting lessons (this week)

#### 4.1 Add lessons to `docs/common/implementation_process.md`

```markdown
### Lesson 33: Enforce embedding-model limits when authoring chunkers (2026-04-29)

**Symptom**: misses on 38.306 csi-Type-II capability and 38.331 LTM-Config IE bodies in the four-question usecase evaluation (Q1~Q4).

**Diagnosis**:
- The chunker `split_giant_section` only performs paragraph-unit splits
- A huge table = a single paragraph -> not splittable
- 38.306 §4.2.7.2 BandNR = a 100,571-token chunk loaded as-is
- text-embedding-3-small caps at 8,192 tokens -> only the first 8% is embedded
- An audit across 5 WGs found 748 chunks above the limit

**Lesson**:
1. **Chunkers must enforce embedding-model limits as hard_max**. Paragraph-unit split alone is insufficient.
2. **Use a 5 WG shared chunker library** — code duplicated five times will reproduce the same defect five times.
3. **Add chunk-size distribution validation to the Phase-7 completion gate**.

**PoC outcomes**:
- 38.306 chunks 99 -> 229 split, score +5.3%, eType-II capability bodies retrieved directly
- 38.331 LTM 22 IEs in a separate collection, score +8.0%, ASN.1 bodies retrieved directly

**Reference**: docs/usecase/evaluations/3way/p1_poc_results.md
```

#### 4.2 Add a lesson to `docs/common/implementation_process.md` (ASN.1 policy)

```markdown
### Lesson 34: Blanket ASN.1 exclusion creates search weaknesses (2026-04-29)

**Symptom**: in Q4, LTM-Config IE bodies; in Q1, CodebookConfig IE bodies; in Q2, TCI-State IE bodies — all not retrieved.

**Diagnosis**:
- The Phase-7 chunkers in RAN2/3/4/5 blanket-skip ASN.1 sections (with dash-prefixed headings)
- Spec §2.6.3 documents "degraded embedding quality" as the reason
- However, an external LLM (Claude) answers ASN.1 IE bodies richly — creating a Coverage gap

**Lesson**:
1. **ASN.1 bodies are also a search target**. Separate them from main chunks and load them in a separate collection.
2. **Embedding-quality concerns can be compensated by sparse(BM25) hybrid retrieval**.
3. **IE names are themselves search keywords** — exact matching is essential.

**PoC outcomes**:
- 38.331 LTM 22 IEs in a separate collection -> +8.0% score
- "LTM-CSI-ReportConfig measurement reporting configuration" query: BEFORE 0.5628 -> AFTER 0.7144 (+0.152)

**Reference**: docs/usecase/evaluations/3way/p1_poc_results.md
```

#### 4.3 Add: `docs/cross-phase/standards/chunking_standards.md`

Common chunking standards across 5 WGs:
- HARD_MAX = 7,500 tokens (8K embedding limit minus a safety margin)
- SPLIT_THRESHOLD = 10,000 tokens (split trigger)
- SPLIT_TARGET = 2,000 tokens (split target)
- SPLIT_OVERLAP = 100 tokens
- Huge-paragraph handling: tables (many pipe separators) -> row-unit split, non-tables -> char-unit sliding window
- ASN.1 sections: separated from main chunks; loaded into the separate `ran{N}_ts_asn1_chunks`
- Auto chunk-quality validation (P7 completion gate)

### Layer 5: Strengthen the Phase-7 completion gate in 5 WGs (this week)

`scripts/cross-phase/validation/p7_completion_gate.py`:

```python
"""Auto-validate Phase-7 completion.

PASSing this gate is required to declare Phase-7 "Complete".

Validation items:
  G1. All chunk tokenCount <= 7500 (HARD_MAX)
  G2. Separate ASN.1 IE collections present (RAN2/3/4/5)
  G3. Core IE regression tests PASS (5 WGs)
  G4. CQ retrieval accuracy (existing)
  G5. Spec matrix (P7-V01~V12) matches measurements

Usage:
  python3 p7_completion_gate.py --wg RAN2
  python3 p7_completion_gate.py --all
"""
```

## 3. Execution order + responsibility matrix (RAN1 separated)

| Step | Action | Artifact | Responsible | Impact |
|---|---|---|---|---|
| **S1** | Author the shared chunker.py (cross-phase) | `scripts/cross-phase/common/chunker.py` | **Claude** | Affects 5 WGs; unrelated to RAN1 spec |
| **S2** | Chunk-quality validation script + ASN.1 regression test (cross-phase) | `scripts/cross-phase/validation/validate_chunk_quality.py`, `validate_asn1_retrieval.py` | **Claude** | Recurrence prevention |
| **S3** | Regenerate RAN2/3/4/5 chunks.json + Qdrant re-indexing + new ASN.1 collections | `vectordb/parsed/ts/RAN{2-5}/.../chunks_v2.json` + 4 Qdrant collections | **Claude** | Immediate effect |
| **S4** | Edit RAN2/3/4/5 phase-7 chunker code | Import the chunker into `scripts/phase-7/RAN{2-5}/ts-parser/01_parse_ts_sections.py` | **Claude** | Recurrence prevention |
| **S5** | Update RAN2/3/4/5 phase-7 specs | `docs/RAN{2-5}/phase-7/specs/tdoc_vectordb_specs(TS).md` | **Claude** | Official baseline |
| **S6** | Add lessons + new chunking standards | `docs/common/implementation_process.md` lessons 33/34, `docs/cross-phase/standards/chunking_standards.md` | **Claude** | Standards |
| **S7** | P7 completion-gate script + apply to RAN2/3/4/5 | `p7_completion_gate.py` | **Claude** | CI/CD |
| **S8** | Re-evaluate RAN2/3/4/5 usecase (Q1~Q4 score measurement) | Updated scores | **Claude** | Effect verification |
| **S9 [user task]** | Same work for RAN1 (chunker edit + spec correction + re-indexing) | (User uses S1~S2 artifacts to apply) | **User** | RAN1 (PHY spec; little ASN.1 impact) |

### S9 user-task guide (RAN1)

Because Claude cannot edit RAN1 spec/implementation, the following is collected in a **separate guide document** (`ran1_user_guide.md`):
- How to apply the chunker to the RAN1 phase-7 chunker (import change)
- A draft RAN1 phase-7 spec correction (P7-V11/V12 added)
- Commands to regenerate RAN1 chunks.json
- Commands to re-index RAN1 Qdrant collections
- How to confirm the RAN1 P7 gate passes

-> Provided in a form the user can apply within 5~30 minutes.

### RAN1 impact assessment (to prioritize work)

| Item | RAN1 measurement | Severity |
|---|---|---|
| `ran1_ts_sections` chunks >7.5K tokens | 6 | Low (vs RAN5's 698) |
| `ran1_ts_sections` chunks >30K tokens | 0 | None |
| ASN.1 skip logic | 0 lines | RAN1 is a PHY spec set with very little ASN.1 — legitimate |
| ASN.1 IE-body miss impact | Negligible | RAN1 is dominated by equations/tables rather than IEs |

-> **RAN1 impact is limited**. The user may apply this systemic improvement to RAN1 after seeing the RAN2/3/4/5 effects.

## 4. Cost / time estimate

| Item | Time | Cost |
|---|---|---|
| S1~S2 code authoring | 4 hours | $0 |
| S3 chunks.json regeneration | 1 hour (script) + 30 min (run) | $0 |
| S4 Qdrant re-indexing (5 WGs, 32K + 1.5K ASN.1 chunks) | 2 hours | **< $0.5** (OpenRouter embedding) |
| S5 chunker code edits | 2 hours | $0 |
| S6 5 WG spec updates | 3 hours | $0 |
| S7~S8 docs | 2 hours | $0 |
| S9 gate integration | 3 hours | $0 |
| S10 re-evaluation | 4 hours (4Q x 5 WGs) | < $0.1 |
| **Total** | **about 21 hours (3 days)** | **< $0.6** |

## 5. Effect simulation (when re-running the four-question usecase evaluation)

| Axis | Current | P1 PoC | After full S1~S5 | After S6~S9 anchored |
|---|---:|---:|---:|---:|
| A1 Accuracy | 4.55 | 4.55 | 4.65 | 4.70 |
| A2 Coverage | 3.95 | 4.10 (PoC partial) | **4.65** | 4.75 |
| A3 Citation Integrity | 4.83 | 4.83 | 4.83 | 4.90 |
| A4 Hallucination Control | 4.85 | 4.85 | 4.95 | 4.95 |
| A5 Cross-Doc Linkage | 4.58 | 4.58 | 4.75 | 4.80 |
| **Overall** | **4.55** | **4.58** | **4.77** | **4.82** |

**Key takeaways**:
- A2 Coverage improves the most (3.95 -> 4.75)
- Surpasses Claude's 4.58 Coverage
- Sustained Citation/Hallucination gap keeps the overall lead robust

## 6. Core principles (the essence of recurrence prevention)

### 6.1 "5 WG code duplication creates immediate drift"

[CLAUDE.md "phase-6/10/11 code duplication is intended"](../../../../CLAUDE.md) prioritizes **per-WG independence**. However, common logic that is **directly tied to model limits** (e.g., the chunker) must be made into a library. When authoring a new feature like a Phase-7:
- **Identify shared-library candidates**: embedding limits, chunk-size policies, filter policies, etc.
- **Explicitly decide common-across-5-WGs vs intentional separation** + record in the spec

### 6.2 "Specify the embedding model in the spec"

Going forward, when the embedding model is changed (e.g., text-embedding-3-large with 16K tokens), HARD_MAX should auto-update — the spec specifies the model and the chunker references the spec.

### 6.3 "Completion gates from the external user's viewpoint"

When announcing "Phase-7 ALL PASS", more than CQ-only verification is needed:
- Chunk quality (size distribution)
- Core IE regression
- Verify weaknesses against external LLMs

-> As today's PoC shows, **a Phase-7 that only passes CQ may still have large weaknesses from the external user's viewpoint**.

### 6.4 "Make external comparison evaluations a recurring workflow"

Integrate usecase evaluation (3-way comparison) into the recurring regression suite:
- Quarterly: refresh GPT/Claude answers + compare
- Identify weaknesses -> P1 actions -> re-evaluate
- Automate the entire cycle

## 7. Next steps (today)

After approving this plan, proceed immediately:
1. S1: Author the shared chunker.py (start now)
2. S3: Regenerate 5 WG chunks.json (after S1)
3. S4: Qdrant re-indexing (after S3)
4. S2: Validation scripts (in parallel with S4)

**Proceed with S5~S10 after confirming verification results**.
