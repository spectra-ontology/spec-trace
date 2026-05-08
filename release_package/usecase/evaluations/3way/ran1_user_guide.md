# RAN1 user-side work guide — Phase-7 Spec correction (code is already completed by Claude)

> **Correction (2026-04-29)**: an earlier version incorrectly partitioned all of RAN1 to user-side work. The accurate protection scope is **Spec body only** (CLAUDE.md "RAN1 code is editable by Claude; only Spec is in user authority").
>
> **Items completed by Claude in this session**:
> - RAN1 chunker code patch (`scripts/phase-7/RAN1/ts-parser/01_parse_ts_sections.py`)
> - RAN1 chunks.json P1.2 split applied (5 splits across 38.212/38.213/38.214, 1~3 each)
> - RAN1 main collection re-indexed (`ran1_ts_sections`: 952 -> 1,002 chunks, P1+P2 cumulative)
> - RAN1 verification (validate_chunk_quality.py PASS, post-P2 max 6,473 tokens, violations=0)
> - count_tokens replaced by tiktoken-based accurate measurement (was `len/4` estimation, now actual)
>
> **User-side direct work (Spec only)**:
> - `docs/RAN1/phase-7/specs/tdoc_vectordb_specs(TS).md` add P7-V11/V12 + ASN.1 V2 policy (if needed)

## RAN1 Spec correction guide (user-side direct)

Adding the following to `docs/RAN1/phase-7/specs/tdoc_vectordb_specs(TS).md` completes the 5 WG consistency.

### Content to add (within the chunking-policy table or §3.x)

```markdown
| **[P7-V11] HARD_MAX (added 2026-04-29)** | **6,500 tokens (P2 corrected value of 2026-04-29; previously 7,500)** | **Every chunk (absolute upper bound)** | **Embedding model 8,192-token limit minus a safety margin. If a single paragraph exceeds HARD_MAX, force-split by row or by characters. Enforce violations=0 at the P7 completion gate.** |
| **[P7-V12] EMBEDDING_MODEL** | **`openai/text-embedding-3-small`** | **Embedding stage** | **Max 8,192 tokens. When the chunker is changed, verify alignment with this model's limit.** |

> **[Background for the new P7-V11/V12 (2026-04-29)]**: the four-question usecase evaluation revealed a chunker defect — only paragraph-unit splits were performed and large tables could not be split. RAN1 was affected by 6 cases (small), but across all 5 WGs the count totals 748. Use the shared library `scripts/cross-phase/common/chunker.py` across the 5 WGs.
> **Verification**: `validate_chunk_quality.py --wg RAN1` PASS (post-P2 max 6,473 tokens, violations=0).
> **References**: `docs/cross-phase/standards/chunking_standards.md`, `docs/usecase/evaluations/3way/root_cause_analysis.md`
```

### ASN.1 V2 policy (not applicable to RAN1)

RAN1 is a PHY spec set with almost no ASN.1 IE bodies. There is no need to create a separate `ran1_ts_asn1_chunks` collection.
While the other WGs' specs have an ASN.1 V2 section added, the RAN1 spec does not require it (not applicable).

## Time required

- Adding the two table rows above plus a single explanatory paragraph to the Spec body: about 5 minutes

## Verification (after applying)

```bash
python3 scripts/cross-phase/validation/validate_chunk_quality.py --wg RAN1
# Expected result: G1+G2 PASS (already passing; unchanged regardless of the spec correction)
```

## References

- Root cause from this session: [root_cause_analysis.md](root_cause_analysis.md)
- Five-layer improvement plan: [systemic_improvement_plan.md](systemic_improvement_plan.md)
- Chunking standards: `docs/cross-phase/standards/chunking_standards.md`
- Lessons: `docs/common/implementation_process.md` lessons 53/54

---

## Additional items to apply (P3, 2026-05-02)

The P3 work landed the following new policies in RAN2~5 phase-7 specs. Adding the following to the RAN1 spec completes full 5 WG consistency (RAN1 has almost no ASN.1 / IE descriptions / capability tables, so all are recorded as "not applicable").

```markdown
| P7-V13 | ASN.1 IE body V2 policy | (Not applicable) | 2026-05-02. RAN1 is a PHY spec set with almost no ASN.1 IEs -> separate collection not applicable |
| P7-V14 | IE field descriptions V2 policy | (Not applicable) | 2026-05-02. RAN1 has no IE field-description patterns -> not applicable |
| P7-V15 | Capability row-level V2 policy | (Not applicable) | 2026-05-02. RAN1 has no 38.306-style capability tables -> not applicable |
```

### New standards documents (drafted by Claude, user review recommended)

- `docs/cross-phase/standards/extraction_policy.md` — PRESERVE allowlist, EXCLUDE policy, 4-tier search collections, Phase completion gates (G1~G5)
- `docs/cross-phase/standards/reembedding_policy.md` — Step 0 selective-feasibility-first policy

### Spec correction time (RAN1)

- Adding the three rows P7-V13/V14/V15: about 2 minutes
