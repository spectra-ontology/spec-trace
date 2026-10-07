# Typed contracts and prospective task references

This package supplies named-record output contracts, traceable source audits,
and freshly executed typed reference answers for explicit graph tasks. The
[compiled prospective definitions](prospective_task_definitions_v2.json) and
[frozen reference execution](prospective_reference_gold_frozen_v2.json) account
for all 40 selected IDs: **36 satisfy the declared execution conditions**,
three exceed the 2,000-row budget, and one lacks a resolved task definition.
The released **624 original questions and queries are unchanged**. These new
variants and their reference answers are separate from the original benchmark.

Use [README_frozen_ttl_import.md](README_frozen_ttl_import.md) to obtain and
restore the released source, replay references, and compare a prediction.
The [gold-free source schema](source_schema_frozen_v1.json) supplies labels,
relationship triples and property types. Gold values, reference queries, row
counts and source-audit answers belong only in evaluation inputs.

## Which evidence each file supplies

| File | Use and measured scope |
|---|---|
| [contract_ledger.jsonl](contract_ledger.jsonl) | Original question/query/gold/key/annotation comparisons for Core560; typed output roles and unresolved issues. |
| [validation_ledger_final_v1.json](validation_ledger_final_v1.json) | Final ledger hash, all 47 direct contracts' structure/source-anchor checks, initial25 saved-gold applicability, and 36/40 reference eligibility. The earlier validation file is preserved. |
| [prospective_selection_v1.json](prospective_selection_v1.json) | Forty IDs fixed before new model outcomes, two per WG × released-track stratum; no replacements after eligibility checks. |
| [prospective_task_definitions_v2.json](prospective_task_definitions_v2.json) | Explicit output fields, types, populations and tie/cap rules, retaining original questions and queries alongside the new variants. |
| [prospective_reference_gold_frozen_v2.json](prospective_reference_gold_frozen_v2.json) | Native typed rows from read-only execution over checksum-pinned deposited TTL restorations; eligibility and all four blocked dispositions. |
| [frozen_ttl_import_manifest_v1.json](frozen_ttl_import_manifest_v1.json) | Source checksums and actual restoration fidelity measurements for all five WGs. |

## Original-question audit: 25 and 47 are different counts

The ledger screens all **560 Core** items automatically, including the **141**
previously annotated as record or mapping outputs. This syntax/annotation
screening is not a direct question-meaning audit. The initial **25** were frozen
by original-ID/task-type coverage before comparison and retain exactly their
original selection. They include 21 RAN1 items, are not representative, and
contain 188 saved reference rows. Adding the selected RAN1/RAN2/RAN3 prospective
24 yields **47 distinct directly compared original items**, with two overlaps.
The remaining 513 ledger entries have automatic screening only.

The initial25 ID-list SHA256 is
`01ec13799ce7fdddb6b7288bda968460462d6e9a904b42f0bad3dae76f98afe6`;
the independent prospective40 selection-file SHA256 is
`279439364181d3470ab823da25f10cb87452fe4a99cd2df8ae1d35a7bfb2e53e`.
Prediction/score artifacts were not used for selection or these audits; authors
already knew earlier aggregate research results. Released track labels describe
the selection strata and do not certify measured retrieval depth.

All 47 direct contracts pass structural/source-anchor checks. **45** have named
typed output definitions and **two** remain unresolved. A `ready` output
definition does not validate the original query's complete scope or gold meaning.
The initial25 raw saved-gold checks give **21 applicable and four blocked**:
three contain numeric outputs stored as canonical strings, and one lacks the
requested TDoc-count output. Numeric parsing and requested-field projections
are recorded separately as conditional transformations, preserving raw rows.
Aliased/nested outputs retain their original returned column and JSON path.

## Concrete original-contract findings

| Item | Finding and retained disposition |
|---|---|
| RAN1_P1_CQ3-4 | Question asks approved count/share; old key selected total. Both requested fields are defined; status/filter meaning remains unresolved. |
| RAN1_P1_CQ2-5 | Category must stay paired with affected clauses. Clauses alone cannot satisfy the requested record. |
| RAN1_P1_CQ1-9 | Full agenda hierarchy cannot be certified from a TDoc-mediated ten-row query. Hierarchy/description roles are explicit; population remains unresolved. |
| RAN1_P2_CQ3-2 | Query counts Agreement nodes while the question asks referenced TDocs. The old count is not relabeled as TDoc gold. |
| RAN1_P1_CQ1-7 | Original purpose alternatives disagree with the query's Decision filter; mismatch remains unresolved. |
| RAN1_P2_CQ5-6 | Trend needs meeting/count pairs and chronological handling. Missing meetings and zero-filled values are not invented. |
| RAN1_P3_P3-S8-CQ04 | External feature-catalog consistency is not answered by a disjoint-edge listing. No Boolean answer or unrelated substitute task is forced. |

The scorer preserves field roles, collection semantics, types and multiplicity.
Extra returned columns are not silently made mandatory. For unresolved original
contracts it reports conditional named-record matching while retaining
`exact = null` and the unresolved reasons.

## Prospective reference eligibility

Eligibility requires an explicit new task and complete, type-valid reference
execution within 30 seconds and 2,000 rows. Empty formal query results can be
eligible and are tracked separately from evidence-based abstention. All 40
selected IDs remain in the accounting:

| Disposition | IDs / reason |
|---|---|
| Eligible | 36 new formal task variants, complete typed reference execution. |
| Unresolved definition | RAN1_P3_P3-S8-CQ04; external feature catalog and matching procedure are absent. |
| Row budget exceeded | RAN1_P2_CQ3-1, RAN2_P3_CQ1-1, RAN3_P1_CQ1-4. Full source QA counts are respectively 2,483, 5,834 and 5,948; retained capped rows are not complete gold. |

The three `frozen_source_qa_RAN*_v1.json` files preserve source/field/population
checks for the RAN1/RAN2/RAN3 definitions before compilation. The compiled v2
records subsequent definition amendments. Original RAN3 query replay also
preserves six full-field matches and two diagnostics: tied LIMIT10 selection,
and differing order of the same twelve nested impact records. These checks
are source diagnostics, not model scores. Current execution status comes from
the separate frozen reference file, rather than historical definition-audit
markers.

The 36/40 eligibility result applies to this balanced prospective cohort and
new formal graph tasks. It does not certify original-question correctness or
estimate Core560-wide performance. Human, independent practitioner and 3GPP
expert validation remain **zero**; source restoration does not establish
external facts or causation. Old predictions cannot be reused as performance
on new variants. SQL can express these structured tasks, so any later comparison
must describe access conditions without claiming a graph-engine advantage.
