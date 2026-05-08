# RAN1 Phase-7 Spec body correction guide (user-side direct application)

> **Date**: 2026-05-04
> **Authority**: editing the RAN1 spec **body (§1~§N)** is reserved to the user. Claude cannot author it.
> **Target file**: `docs/RAN1/phase-7/specs/tdoc_vectordb_specs(TS).md`
> **This guide**: a Claude-authored auxiliary change proposal. Apply directly after user review.

---

## 1. Motivation for the change

Reflect into the RAN1 spec the policies landed in the RAN2~5 phase-7 specs between 2026-04-29 and 2026-05-04, completing 5 WG consistency.

New policies landed (in RAN2~5):
- **HARD_MAX 6,500 tokens** (chunker_v2, P2 policy)
- **EMBEDDING_MODEL = `openai/text-embedding-3-small`**
- **ASN.1 IE body V2 policy** (separate collections in RAN2/3; not applicable to RAN1)
- **IE field descriptions V2 policy** (separate collection in RAN2; not applicable to RAN1)
- **Capability row-level V2 policy** (separate collection in RAN2; not applicable to RAN1)

RAN1 is a PHY domain spec set, so the ASN.1 / IE / capability patterns are absent — recorded as N/A.

---

## 2. Where to add and which IDs to use

### 2.1 Currently used IDs in the RAN1 phase-7 spec (for reference)

| Used ID | Item |
|---|---|
| P7-V01 | Total section count |
| P7-V02 | Void section count |
| P7-V03 | Container section count |
| P7-V04 | Very large section count (10K+) |
| P7-V05 | Total chunk count |
| P7-V06 | Split threshold |
| P7-V07 | Split-size target |
| P7-V08 | Overlap |
| P7-V09 | Minimum chunk |
| P7-V10 | Target TS count |
| P7-V11 | Total processed sections |
| P7-V12 | Section token-bin distribution |
| P7-V13 | Very large (10K+) section inventory |
| P7-V14 | Per-spec chunks distribution |

-> The next available ID starts from **P7-V15**.

### 2.2 Insertion location

Append **5 rows** to the end of the table `## Appendix A: Reference numbers` in `docs/RAN1/phase-7/specs/tdoc_vectordb_specs(TS).md`, immediately after the current P7-V14 row (after line 1393).

---

## 3. Rows to add (copy verbatim)

```markdown
    | P7-V15 | HARD_MAX (absolute upper bound) | 6,500 tokens | Added 2026-04-29; chunker.py stale tokenCount bug fixed 2026-05-04. Safety margin based on the embedding model limit (8,192). If a single paragraph exceeds HARD_MAX, force-split by row or by characters (`scripts/cross-phase/common/chunker.py::split_existing_chunk` + `_force_split_by_chars`). Adjustable when the embedding model changes. Authoritative measurement: `logs/cross-phase/usecase/post_p2b_v2_violations.json` (3.43M chunks, zero violations) |
    | P7-V16 | EMBEDDING_MODEL | `openai/text-embedding-3-small` | Added 2026-04-29. Max 8,192 tokens. When the chunker is changed, verify alignment with this model's limit. Policy basis: `docs/cross-phase/standards/extraction_policy.md` |
    | P7-V17 | ASN.1 IE body V2 policy | (Not applicable) | Reviewed 2026-05-02. RAN1 is a PHY spec set (38.201/38.202/38.211/38.212/38.213/38.214/38.215/38.291) with no ASN.1 IE definitions -> separate collection not applicable (`docs/cross-phase/standards/extraction_policy.md` §1.3). RAN2/3 are applied. |
    | P7-V18 | IE field descriptions V2 policy | (Not applicable) | Reviewed 2026-05-02. The RAN1 PHY spec set has no 38.331-style IE field-description tables -> not applicable. RAN2 38.331 is applied (700 chunks); RAN5 38.523-1/3 is applied (3 chunks). |
    | P7-V19 | Capability row-level V2 policy | (Not applicable) | Reviewed 2026-05-02. RAN1 has no 38.306-style capability tables -> not applicable. RAN2 38.306 is applied (1,716 rows). |
```

> Note on indentation: use the same 4-space indentation as the other rows of the table, with a leading `|`.
> Notion rendering: every line except the first (`- **phase-7:`) starts with 4 spaces — these rows must follow the same convention.

---

## 4. How to apply

### 4.1 GUI editing (recommended)

1. Open `docs/RAN1/phase-7/specs/tdoc_vectordb_specs(TS).md`.
2. Paste the 5 rows from §3 right after line 1393 (`P7-V14 | per-spec chunks distribution ...`).
3. Save.

### 4.2 Verification (after applying)

```bash
# Confirm line count (5 lines added)
wc -l "docs/RAN1/phase-7/specs/tdoc_vectordb_specs(TS).md"

# Confirm presence up to P7-V19
grep "P7-V1[5-9]" "docs/RAN1/phase-7/specs/tdoc_vectordb_specs(TS).md"
```

---

## 5. Body §3 (chunking-policy table) — optional addition

If you wish to cite P7-V15/V16 in the body of `§3.2 Chunking-policy table` or an equivalent location, add the following rows:

```markdown
    | HARD_MAX (absolute upper bound) | [P7-V15] tokens | All chunks | If a single paragraph exceeds, force-split by row or by characters. Adjustable when the embedding model changes |
    | EMBEDDING_MODEL | [P7-V16] | Embedding stage | Max 8,192 tokens |
```

> **Optional**: deciding whether to cite in the body is a matter of spec consistency. The RAN2/3/5 specs cite P7-V11/V12 in their body. Add the same in RAN1 if you want identical consistency.

---

## 6. Impact of the change (for reference)

- **This change** does not alter the spec semantics (only documents policy)
- The code already enforces the policy via `chunker.py` + phase-6/8/9 parser hooks (no impact on RAN1 data)
- Measured: all 1,002 chunks of RAN1 ts_sections are below HARD_MAX 6,500 (max 6,473) — zero violations

---

## 7. RAN2~5 landed status (for reference)

| WG | HARD_MAX | EMBEDDING | ASN.1 V2 | IE desc V2 | Cap V2 |
|---|---|---|---|---|---|
| RAN2 | P7-V12 | (presupposed policy) | P7-V13 applied | P7-V14 applied | P7-V15 applied |
| RAN3 | P7-V12 | (presupposed policy) | P7-V13 applied | N/A | N/A |
| RAN4 | P7-V08 | (presupposed policy) | N/A | N/A | N/A |
| RAN5 | P7-V14 | (presupposed policy) | N/A | P7-V16 applied | N/A |
| RAN1 | **P7-V15 (to be added)** | **P7-V16 (to be added)** | P7-V17 N/A | P7-V18 N/A | P7-V19 N/A |

> The differences in ID numbering across WGs are a natural result of the IDs already in use in each spec — only intra-spec consistency must be maintained.

---

## 8. Application checklist

- [ ] Append the 5 rows of §3 to the end of the Appendix A table (after P7-V14)
- [ ] (Optional) Add the citation rows for P7-V15/V16 to the body §3 chunking-policy table
- [ ] Notion synchronization (verify indentation)
- [ ] Verify after git commit
