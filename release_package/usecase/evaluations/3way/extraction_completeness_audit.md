# Regular-process extraction completeness — full audit across 5 WGs x 12 phases (2026-05-02)

> **Motivation**: a user observation — IE field-description omissions (RAN2 docx 755 vs our 0 chunks) -> investigate whether the same pattern exists in other phases/WGs, identify the root cause, and design a solution.
> References: `logs/cross-phase/usecase/regular_process_audit.md` (detailed code audit), `logs/cross-phase/usecase/extraction_audit_all_phases.json` (raw quantitative measurements)

## 1. Result summary (TL;DR)

> **2026-05-04 correction**: an earlier draft did not consult RAN1 spec §2.2 (Out of Scope) / §2.3 (KG vs VectorDB boundary) and **misclassified intended designs as "defects"**. After consulting the spec, **the actual defects are limited to the missing HARD_MAX and a few PATTERN gaps**. The metadata-only separation in phases 3/4/5, per spec, is not a defect.

**Initial quantitative measurement**: phase-7 results show 51~100% omission across 6 patterns -> verified across other phases -> **the actual defects are the missing HARD_MAX + IE/Capability pattern gaps**. Not a missing-data problem (everything is in docx). Responsibility: insufficient policy anchoring.

| Category | Omission ratio | Representative example |
|---|---:|---|
| IE field-descriptions tables (`XXX field descriptions`) | RAN2 99.7% | Field semantics for LTM-Config / CodebookConfig / TCI-State |
| IE-definition headers (`XXX information element`) | RAN2 100% | 642 -> 0 |
| Capability "UE supports" pattern | RAN2 87% | 38.306 1,162 -> 150 |
| Test-case bodies (Test purpose/Procedure) | RAN4 83% / RAN5 54% | 38.521-3 715, etc. |
| RP-WID reference (Plenary) | 99.98% | 12,587 across 5 WGs -> 2 |
| ASN.1 SEQUENCE/CHOICE definitions | RAN2 19% / RAN3 33% | Some NGAP/XnAP/F1AP |

## 2. 5 WG x 5 collections quantitative matrix (measurements)

`scripts/cross-phase/validation/audit_extraction_completeness.py --all --all-collections`

### 2.1 docx totals vs collection load (chunk units)

| WG | A_field_desc | B_asn1_def | C_capability | D_test_purpose | E_ie_header | F_rp_wid |
|---|---|---|---|---|---|---|
| RAN1 | docx=0 -> load=0 (legitimate) | 0 (legitimate) | 0 (legitimate) | 0 (legitimate) | 2 -> ts_main 2 (100%) | docx=1,026 -> **0 (0%)** |
| **RAN2** | **755 -> 2 (0.3%)** | 2,622 -> 2,124 (81%) | **1,174 -> 150 (13%)** | 0 (legitimate) | **642 -> 0 (0%)** | **3,340 -> 1 (0%)** |
| RAN3 | 0 (legitimate, different keywords) | 4,319 -> 2,886 (67%) | 0 (legitimate) | 0 (legitimate) | 150 -> 150 (100%) | **1,987 -> 0 (0%)** |
| RAN4 | 0 (legitimate) | 0 (legitimate) | 0 (legitimate) | **1,704 -> 291 (17%)** | 14 -> 13 (93%) | **6,210 -> 1 (0%)** |
| RAN5 | 3 -> 11 (split duplication) | 911 -> 4,854 (split) | 64 -> 12 (19%) | **922 -> 421 (46%)** | 13 -> 27 (split) | **24 -> 0 (0%)** |

**Note on interpretation**: some RAN5 patterns exceed 100% — chunk-split duplicate counting. Even so, the RAN2 omissions (0%, 13%, 0%) / RAN4 D_test_purpose (17%) / 5 WG F_rp_wid (0%) are clear omissions.

### 2.2 Notable findings per phase-6/7/8/9 collection

| Pattern | RAN2 ts_main | RAN2 ts_asn1 | RAN2 tdoc | **RAN2 cr** | RAN2 tr |
|---|---:|---:|---:|---:|---:|
| A_field_desc | 2 | 0 | 507 | **16,141** | 0 |
| B_asn1_def | 19 | 2,105 | 17,169 | **23,763** | 2 |
| E_ie_header | 0 | 0 | 11,672 | **19,661** | 0 |

-> **The CR collection contains plenty of IE-description patterns** (because CRs cite spec bodies). In other words, **there is partial bypass via the CR collection today**, but it is **scattered and unsystematic**. Its accuracy is lower than direct loading of the IE-description tables.

## 3. Per-phase processing (code audit + spec correction — 2026-05-04)

> §3 corrects items the earlier draft classified as "defects" without consulting the RAN1 spec, after consulting the policy. See `logs/cross-phase/usecase/regular_process_audit.md` for the full correction table.

### 3.1 Intended designs (not defects)

| Phase | Processing | RAN1 spec policy |
|---|---|---|
| phase-0 | TSG_RAN Plenary not collected | `data_collection_scope.md` §2.1 no-collection decision |
| phase-3 | Body text not stored in KG (metadata only) | spec §2.2: "Section body text = VectorDB scope; Out of Scope" |
| phase-3 | ASN.1 definition sections excluded at the section level | spec §3.9.4 explicit policy (recovered via separate collection) |
| phase-4 | CR Track Changes body not stored in KG | spec §2.2: "Track Changes change blocks = VectorDB scope" |
| phase-5 | Scope/Conclusions `[:800]` excerpt | spec §2: "1-10 sentence short summary metadata" — 800 chars approximates the policy |
| phase-6/7/8/9 | DROP Foreword/References/Change History etc. | each spec's explicit policy (search-noise removal) |
| phase-10/11 | Reuse other phases' parsers | intentional DRY design |

### 3.2 Actual policy gaps / implementation defects (hardening in progress)

| Phase | Item | Classification | Hardening |
|---|---|---|---|
| phase-3/7 | IE field-description tables not extracted separately | Policy gap (RAN2 38.331 docx 755 not retrieved) | P1.1b — `ran2_ts_ie_descriptions` 700 chunks (P7-V14 anchored) |
| phase-7 | 38.306 capability not split row-by-row | Policy gap | P1.1c — `ran2_ts_capabilities` 1,716 rows (P7-V15 anchored) |
| phase-6/8/9 | HARD_MAX missing (Spec V1 not reflected) | Implementation defect (5,041 violations) | P2.b v2 (after the chunker.py bug fix) — 0 violations (3.43M chunks at 100% compliance) |
| phase-7 (RAN2 38.331) | 7% pattern-matching miss for IE descriptions | Extraction-regex limit | In progress (55/755) |

### Phase-10/11 (incremental updates)

These phases **reuse** modules from phases 3/6/7/8/9 and therefore propagate every policy gap and implementation defect. That is, when new meetings are added, the same pattern applies — once the policy gaps are addressed by separate-collection augmentation + chunker.py fixes, phases 10/11 are covered automatically.

## 4. Root cause — corrected after spec consultation (2026-05-04)

> The earlier draft listed four root causes; after spec consultation, R1/R2/R4 were reclassified as intended designs. The actual root cause is R3 (insufficient back-port of the chunker policy) plus a few policy gaps.

### R1. ~~Policy inheritance across 5 RANs~~ -> **Intended design + a few policy gaps**

- The KG-VDB responsibility separation is a policy explicit in RAN1 spec §2.2/§2.3 and applied uniformly across phases.
- The IE-description tables of RAN2 38.331 are an unstated gap area -> hardened with the separate collection via P1.1b (P7-V14 anchored).
- The same applies to the test-case patterns of RAN5 38.5xx (P7-V16).
- **Policy gaps are not R1; they belong to a category of unspecified items in the spec**.

### R2. ~~KG-VDB responsibility-separation failure~~ -> **The separation premise is healthy; the cause is missing separate collections**

- The KG = metadata/structure, VDB = body separation is **explicit in the spec** (phase-3 §2.2, phase-4 §2.2, phase-5 §2 all explicit).
- The omitted areas (IE-description tables, capability rows) are not failures of the separation premise but **separate collections that were not specified in the spec**.
- Solution: anchor the 4-tier search system (main + asn1 + ie_descriptions + capabilities) + Spec V2 anchoring (P7-V13~V17).

### R3. **Chunker policy inconsistency** — the actual root cause

- HARD_MAX=6,500 (P2 policy) was applied only in phase-7; phases 6/8/9 did not adopt it -> 5,041 violations.
- Additionally, a stale `tokenCount` trust bug was identified in `split_existing_chunk` on 2026-05-04 -> P2.b v1 silently skipped 1,815 cases.
- **2026-05-04 chunker.py fix + P2.b v2 100% resolved** (0 violations on 3.43M chunks).

### R4. ~~Data-collection scope inconsistency~~ -> **Intentional no-collection decision**

- TSG_RAN Plenary no-collection was settled by ROI evaluation + user decision (`data_collection_scope.md` §2.1).
- Indirect citation is feasible today since 5 WG TDoc bodies cite RP-WID introductions.
- **Re-discussion forbidden** (decided 2026-05-04).

### Root cause summary (corrected)

-> The actual single root cause is **chunker.py HARD_MAX back-port + the stale tokenCount bug (R3)**, 100% resolved. Other items are intended designs or policy-gap hardening (separate-collection additions).

## 5. Root-cause solution (3-layer design)

### Layer 1: Immediate fixes (Today / This week)

| Action | Affected phase / WG | Cost |
|---|---|---|
| **L1.1 P1.1b**: extend P1.1 ASN.1 extractor with description-table extraction (regex + match table after IE name) | RAN2 38.331 +755 descriptions, RAN5 38.523 +3 | 2 hours + ~$0.005 embedding |
| **L1.2 chunker_v2 back-port**: phase-6/8/9 chunkers use cross-phase/common/chunker.py. Enforce HARD_MAX=6,500 | phase-6/8/9 x 5 WGs (10 collections) | 4 hours + ~$1.5 re-indexing |
| **L1.3 phase-3 body-text separation file**: parse_ts_docx.py emits body text into a separate file (`{spec}_body.json` or chunks.json) | 5 WG phase-3 | 4 hours |
| **L1.4 RP-WID collection** (optional, key 30~50 only): RP-221799, RP-211661, etc. + Phase-0 collection step | phase-0 | 2 hours + ~$0.01 embedding |

### Layer 2: Phase completion gates (recurrence prevention)

| Gate | Enforcement point |
|---|---|
| **G1: extraction-coverage audit** | At Phase-3/6/7/8/9 completion — `audit_extraction_completeness.py --wg X` PASS (each pattern miss < 20%) |
| **G2: chunk quality (already in place)** | At Phase-7 completion — `validate_chunk_quality.py --wg X` PASS (HARD_MAX 6,500) |
| **G3: cross-phase consistency** | At Phase-10/11 completion — verify the same defects do not recur in incremental data |

### Layer 3: Spec/standards anchoring (long term)

| Change | Location | Effect |
|---|---|---|
| **EXCLUDE_PATTERNS centralization** | New `docs/cross-phase/standards/extraction_policy.md` — DROP policy + PRESERVE allowlist (RP-WID, IE-description tables, etc.) | Consistency across 5 WGs when adding new policy |
| **Enforce a common chunker** | Forbid additional chunkers other than `scripts/cross-phase/common/chunker.py` (CI-enforced) | Drift prevention |
| **Spec data-collection categories** | `docs/cross-phase/standards/data_collection_scope.md` — document collection policies for each TSG_RAN/RAN1~5/CR/TR/RP-WID category | Prevent recurrence of phase-0 omissions |
| **Six-pattern regression ground truth** | `logs/cross-phase/baselines/extraction_completeness_baseline_*.json` (to be generated at the next audit measurement) | Auto-detect regressions on later regular-process changes |

## 6. User decision required (execution priority)

| Option | Time | Core value |
|---|---|---|
| **A**: L1.1 + L1.2 only (2 days) | 6 hours | Recover RAN2 38.331 IE descriptions (large impact on Q1/Q2/Q4) + stabilize phase-6/8/9 |
| **B**: A + L1.3 (3 days) | 1 day | Also enables IE-semantic queries from the KG — more fundamental fix |
| **C**: A + L1.4 (key 30 RP-WIDs only) (2.5 days) | 8 hours | Direct citation of introductions like RP-221799 |
| **D**: A+B+C+L2 (1 week) | 1 week | Anchor the gates — recurrence prevention complete |

**Claude recommendation**: **B (L1.1 + L1.2 + L1.3)** — phase-3/6/7/8/9 consistency is the core. RP-WID is a separate track (lower priority).

## 7. Alignment with the user's core requirement

> "Find a fundamentally sound solution"

This document covers:
1. Full audit (5 WGs x 12 phases)
2. Root-cause analysis (4 orthogonal causes)
3. 3-layer solution (immediate / gates / standards)
4. Recurrence-prevention automation (Layer 2 gates)
5. Quantitative measurement baseline (Layer 3 ground truth)

**Pending (user decision required)**:
- Which option (A/B/C/D) to execute

---

## 8. Artifact locations

- `scripts/cross-phase/validation/audit_extraction_completeness.py` — quantitative measurement tool (re-runnable)
- `logs/cross-phase/usecase/extraction_audit_all_phases.json` — 5 WGs x 5 collections raw data
- `logs/cross-phase/usecase/regular_process_audit.md` — 5 WGs x 12 phases code audit
- `docs/usecase/evaluations/3way/extraction_completeness_audit.md` — this document (summary)

## 9. Execution results (in progress 2026-05-02)

### 9.1 Option D selected — user direction "performance and accuracy first; cost/time irrelevant"

L1.1 (P1.1b/P1.1c) + L1.2 (chunker_v2 back-port P2/P2.b) + L2 (gates) + L3 (Spec/standards anchoring) all proceed.

### 9.2 P1.1b — IE field-descriptions separate collection (Layer 1)

| Collection | chunks | Status |
|---|---|---|
| `ran2_ts_ie_descriptions` | **700** | Newly created (700 chunks loaded from 38.331 docx 755; P7-V14 added) |
| `ran5_ts_ie_descriptions` | **3** | Newly created (consistency dimension; P7-V16 added) |

Tool: `scripts/cross-phase/usecase/improvements/p1_1b_extract_ie_descriptions.py` (camelCase IE name + "field descriptions" header pattern — case-sensitive).

### 9.3 P1.1c — Capability row-level separate collection (Layer 1)

| Collection | rows | Status |
|---|---|---|
| `ran2_ts_capabilities` | **1,716** | Newly created (38.306 §4.2.7.x/§5.4/§5.6 table rows split by row; P7-V15 added) |

Tool: `scripts/cross-phase/usecase/improvements/p1_1c_extract_capability_rows.py`.

### 9.4 P2.b — Selective re-processing of phase-6/8/9 collections (Layer 1, first application of the Step 0 policy)

Instead of full re-indexing ($30~50 and 24 hours), only HARD_MAX-violating chunks are split -> deleted -> upserted.

| Collection | violations -> split | upsert |
|---|---|---|
| ran1_tdoc_chunks | 61 -> 2 | 10 |
| ran1_cr_chunks | 65 -> 38 | (4 del + new upsert) |
| ran2_tdoc_chunks | 3 -> 0 | 0 (split infeasible, residual) |
| ran2_cr_chunks | **652 -> 623** | **10,083** |
| ran2_tr_sections | 17 -> 14 | 107 |
| ran3_cr_chunks | 42 -> 32 | 291 |
| ran4_tdoc_chunks | 498 -> 0 | 0 (split infeasible, residual) |
| ran4_cr_chunks | **3,500 -> 1,685** | **35,150** |
| ran4_tr_sections | 26 -> 11 | 83 |
| ran5_tdoc_chunks | 2 -> 0 | 0 (split infeasible, residual) |
| ran5_cr_chunks | 88 -> 52 | 283 |
| ran5_tr_sections | 12 -> 6 | 63 |

**Total**: 5,041 violations -> 46,070 new chunks (P2.b v1, 2026-05-02). After residual **2,579 (0.0753%)**, the chunker.py bug was identified -> P2.b v2 resolved 100%.

### 9.4.1 P2.b v1 results (2026-05-02)

| Collection | v1 residual | Max tokens |
|---|---:|---:|
| ran4_cr_chunks | 1,815 (70%) | 16,689 |
| ran4_tdoc_chunks | 498 (19%) | 8,596 |
| ran1_cr_chunks | 61 | 10,660 |
| ran1_tdoc_chunks | 59 | 7,884 |
| ran1_tr_sections | 42 | 10,530 |
| Other 9 collections | 104 | — |
| **Total** | **2,579** | — |

**Root cause** (identified 2026-05-04): `split_existing_chunk(chunk)` trusted the chunk payload's `tokenCount` field as-is. That field had been computed by an earlier chunker as `len/4` and is stale (actual 7,265 tokens, stored 3,079). As a result, the `token_count <= hard_max` condition was not violated and the function did not even attempt to split.

### 9.4.2 chunker.py bug fix (2026-05-04)

Two patches in `scripts/cross-phase/common/chunker.py`:

1. **`split_existing_chunk` always re-measures with tiktoken** (ignoring stale `tokenCount`)
2. **Added `_force_split_by_chars`** (last-resort char-level split when natural break points are absent — bisection adapts the chars/token ratio to enforce hard_max strictly)

### 9.4.3 P2.b v2 results (2026-05-04, after the chunker fix)

P2.b v2 re-execution:

| Collection | v1 residual | v2 split -> new | v2 residual |
|---|---:|---|---:|
| ran1_tdoc_chunks | 59 | 59 -> 178 | **0** |
| ran2_tdoc_chunks | 3 | 3 -> 7 | **0** |
| ran3_tdoc_chunks | 0 | — | **0** |
| ran4_tdoc_chunks | 498 | 498 -> 1,156 | **0** |
| ran5_tdoc_chunks | 2 | 2 -> 4 | **0** |
| ran1_cr_chunks | 61 | 61 -> 309 | **0** |
| ran2_cr_chunks | 29 | 29 -> 113 | **0** |
| ran3_cr_chunks | 10 | 10 -> 41 | **0** |
| ran4_cr_chunks | 1,815 | 1,815 -> 9,519 | **0** |
| ran5_cr_chunks | 36 | 36 -> 140 | **0** |
| ran1_tr_sections | 42 | 42 -> 182 | **0** |
| ran2_tr_sections | 3 | 3 -> 15 | **0** |
| ran3_tr_sections | 0 | — | **0** |
| ran4_tr_sections | 15 | 15 -> 74 | **0** |
| ran5_tr_sections | 6 | 6 -> 25 | **0** |
| **Total** | **2,579** | **2,579 -> 11,763** | **0 (0.0000%)** |

Among the 3,430,598 chunks across 15 collections, **0 violations** of HARD_MAX 6,500 tokens (100% compliance). Authoritative measurement: `logs/cross-phase/usecase/post_p2b_v2_violations.json`.

### 9.5 Final verification (Layer 2 gate)

`validate_chunk_quality.py --all` results:

| WG | ts_sections chunks | Max tok | Violations | ASN.1 V2 |
|---|---:|---:|---:|---|
| RAN1 | 1,002 | 6,473 | 0 | N/A |
| RAN2 | 2,451 | 6,431 | 0 | 2,365 |
| RAN3 | 3,560 | 5,612 | 0 | 2,995 |
| RAN4 | 16,248 | 6,476 | 0 | N/A (RF/EMC) |
| RAN5 | 26,814 | 6,494 | 0 | N/A (fewer than 3) |

**Overall PASS** — all 5 WG ts_sections collections at 100% compliance with the HARD_MAX 6,500 token cap.

### 9.6 Layer 3 — Spec/standards anchoring

- `docs/cross-phase/standards/extraction_policy.md` added (PRESERVE allowlist + EXCLUDE policy + 4-tier search + gates)
- `docs/cross-phase/standards/reembedding_policy.md` added (Step 0: selective-feasibility-first review)
- `CLAUDE.md` "Re-embedding decision checklist Step 0" added
- RAN2 phase-7 spec — P7-V13 (ASN.1 V2) / P7-V14 (IE descriptions V2) / P7-V15 (Capability V2) anchored
- RAN3 phase-7 spec — P7-V13 (ASN.1 V2) anchored, P7-V14/V15 marked N/A
- RAN4 phase-7 spec — P7-V09/V10/V11 marked N/A
- RAN5 phase-7 spec — P7-V16 (IE descriptions, 3 chunks) anchored, P7-V15/V17 marked N/A
- `docs/common/implementation_process.md` lessons 56 (IE description 99.7% omission) + 57 (re-embedding Step 0) added

### 9.7 Remaining items

- The RAN1 spec correction is a user task (CLAUDE.md "RAN1 Spec body modification forbidden"). The Appendix has been editable by Claude since 2026-05-04. See `docs/usecase/evaluations/3way/ran1_user_guide.md`.
- ~~TDoc residual~~: the 2026-05-04 chunker.py stale tokenCount bug fix resolved this to 0.
- ~~RP-WID body collection~~: **no-collection decision settled** (2026-05-04). See `docs/cross-phase/standards/data_collection_scope.md` §2.1. Re-discussion forbidden by ROI evaluation + user decision.
