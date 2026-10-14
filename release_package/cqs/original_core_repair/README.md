# Original-question-preserving Core repairs

This supplement retains each admitted item's exact original English question.
The query and requested-field scoring contract are inspected by two separate AI
reviews against seven fixed semantic units, followed by captured native output
and actual scorer controls. These checks are not independent human or 3GPP
expert validation, nor proof that every frozen-graph fact is correct.

| Accounting | Items |
| --- | ---: |
| Original Core IDs in disposition ledger | 560 |
| Admitted original-question-preserving repairs | 371 |
| Original query retained; scorer repaired | 119 |
| Query and scorer repaired; English question retained | 252 |
| Pending | 189 |
| Blocked | 0 |

The 350-item scientific cohort remains frozen under manifest
`18b301baac1bdacffd7b9f93917f3362c516d54ed5ad2ed7826c7df96e57edb5`. The 21 further repairs are disjoint from
that cohort and require a separate evaluation; merging these definitions does
not silently extend an existing experiment. [Frozen cohort pins](provenance/frozen_evaluation_350.json)
record both scopes. This repair package contains reference evidence and scorer
checks, not model predictions or performance results.

[All 560 dispositions](all_core_dispositions.jsonl) expose every unresolved ID.
Only pass IDs occur in [tasks](tasks.jsonl) and [gold](reference_gold.jsonl).
The admitted set overlaps all 31 historical diagnostic IDs and includes
340 other IDs. Those historical predictions and scores do not transfer
to the repaired contracts; the separate 36 changed-question variants are not
added. The sibling canonical_core contains different proposed question wording
and is not evidence of original-Core alignment. Full-Core completion is not claimed.

[Review guide](REVIEW_GUIDE.md), [per-working-group changes](changes/), and
[readable dispositions](DISPOSITIONS.md) show the original questions and queries,
repaired queries, required answer fields, native receipts, and recorded AI reviews.
Unasked titles, counts, or arbitrary sorting keys are not required answer fields.
Explicit top-k queries retain the entire eligible ranking pool: every item above
the cutoff is required and any appropriate subset at the tied cutoff is accepted.
Answer ordering is required only where the question asks for it.

Two maximum-frequency tasks also carry complete frozen-source frequency pools.
The offline verifier derives all maximum ties from those retained pools and
compares them to actual native requested-field gold. This checks stored frozen
graph evidence, not raw-archive truth or expert validation. The historical
derivation scripts retain local source paths; rerunning them requires those graphs.

```bash
cd release_package/cqs/original_core_repair
python3 -B -S verify_release.py
python3 -B -S -m unittest test_scorer test_native_order test_predictions test_boundary_ties
python3 -B -S score_predictions.py --predictions predictions.jsonl
```

The first two commands check stored evidence and scorer behavior offline; they
do not execute a database or generate model answers. Predictions must provide
the exact repair_sha256 and named requested-field records. Wrong values, missing
asked fields, incompatible types, duplicate identities, and invalid cardinality
receive no complete-record credit. Human/expert reviews completed: zero.
