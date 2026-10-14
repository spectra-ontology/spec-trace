# Original-question-preserving Core repairs

This bundle repairs answer contracts while retaining the exact English questions
from the original SpectraCQ Core release. Each admitted item has two separate
AI semantic judgments against the original question, exact-query captured native
output from the pinned archived graph restoration, and requested-field scorer
checks. These are AI-assisted checks, not human author or independent 3GPP expert
validation. No new model predictions or performance results are included.

| Accounting | Items |
| --- | ---: |
| Original Core IDs, all visible in the disposition ledger | 560 |
| Admitted original-question-preserving repairs | 300 |
| Original reference query retained; answer contract repaired | 118 |
| Reference query and answer contract repaired; question retained | 182 |
| Pending original meaning, second review or technical admission | 257 |
| Blocked by a recorded semantic or technical issue | 3 |

Use the admitted set when preparing a new evaluation. Unresolved original items
are outside this set; they are not silently admitted or counted as verified.
The original 31-question diagnostic keeps its original scoring and prediction
scope. This repaired set is a new contract validation, not an increase in that
unchanged diagnostic, and the separate 36 changed-question tasks are not added.
The admitted set overlaps the historical 31 on 31 IDs
and includes 269 IDs outside it. These set relationships do not
permit adding their validation counts or transferring historical scores.
The sibling `canonical_core/` provides revised definitions for all 560 IDs,
including changed-question variants; those are not evidence that all original
questions align. Full-original-Core completion is **not claimed** here.

## Inspect the changes

[Review guide](REVIEW_GUIDE.md) links the original wording, original and repaired
queries, required answer roles and types, native outputs and both AI judgments.
[Readable dispositions](DISPOSITIONS.md) and [all 560 records](all_core_dispositions.jsonl)
retain the remaining issues.
[Tasks](tasks.jsonl), [native-derived gold](reference_gold.jsonl) and
[per-item scorer checks](provenance/scorer_checks.jsonl) are machine-readable.
Reference rows include all returned values; only the fields actually requested
by the question are mandatory answers. Unrequested titles or ordering metadata
are not silently made required answer fields.
When an unchanged query has a nonbinding output cap, its complete-answer claim
is checked against a separate uncapped capture on the same frozen graph. The
uncapped query, output and receipt are included as a completeness witness; this
is a check of the pinned snapshot, not a guarantee about future graphs.
The [frozen import inventory](provenance/frozen_ttl_import_manifest.json) and
[RAN1/RAN2 source scan](provenance/ran12_source_semantics.json) retain population
checks used in the semantic reviews. The scan's measurement script is preserved
with its historical local paths; rerunning it requires the corresponding archived
body graphs and shipped loader. It is not part of the offline replay commands.

```bash
cd release_package/cqs/original_core_repair
python3 -B -S verify_release.py
python3 -B -S -m unittest test_scorer test_native_order test_predictions
```

These commands verify stored evidence and scorer behavior offline. They do not
rerun queries or independently attest graph content or domain utility. Historical
model scores and rankings cannot be transferred to repaired definitions. New
predictions must carry the exact `repair_sha256` of their admitted definition:

```bash
python3 -B -S score_predictions.py --predictions predictions.jsonl
```

Each prediction is a JSON record with `id`, `repair_sha256` and `records` (a list
of named answer records). Wrong counts, missing asked fields or incompatible
types receive no complete-record credit. Both requested-field matching and
cardinality/order rules are enforced. Source ordering metadata may determine
answer sequence without itself becoming an asked answer field. No historical
whole-row F1 is relabeled as performance under this contract.
