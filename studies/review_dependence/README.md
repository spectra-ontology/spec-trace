# Review-dependent gold and subset-score replay

This workflow connects the public identity-review receipts to the benchmark's exact gold evidence and recomputes the complete stored-response sensitivity. It reconstructs **242 of 1,640 gold evidence rows in 99 of 667 items**, comprising **53 RAN1 and 46 RAN2 items**, from all 358,062 released disposition records. Every dependent gold evidence row has `source_verified` status.

The replay compares all **37 conditions × 2 scoring rules × 4 subsets = 296 complete score cells** with the original analysis. Each comparison includes the correct count, subset denominator and share. Question hashes, missing/duplicate/stale response counts and separately recorded electronic meetings retain the published scoring contract.

Run from the public checkout with Python 3.10 or later and its standard library. Use a new scratch output directory:

```sh
free -h
python3 -B studies/review_dependence/replay.py \
  --release . --output work/review_dependence
```

Absolute script, release and output paths also work. The program reads public release paths directly, streams the five plain/compressed JSON-LD files, expands compressed SQLite partitions in disposable scratch, and reads meeting labels through immutable read-only connections. It extracts only the two pure condition-file constructors from the released analyzer. The independently implemented row-set scorer then runs without historical workspace setup. Its receipt binds every consumed public input and verifies unchanged bytes after execution.

| Output | Content |
|---|---|
| `review_dependence.json` | Complete population counts and the 99 item identifiers. |
| `gold_dependence_trace.jsonl` | Each gold-linked disposition, exact item/evidence index, assignment rule, source path/hash/locator, and public review receipt/index. |
| `sensitivity.json` | All 296 subset counts, correct counts and shares under identity and recorded scoring. |
| `reference_comparison.json` | Full comparison with the original score summary. |
| `relation_regression.json` | Aggregate ordering and individual-run examples that distinguish strict ordering from ties or reversals. |
| `replay_receipt.json` | Runtime, implementation/reference hashes, input before/after hashes, elapsed time and peak RSS. |

The four historical subset names are `all` (667 items), `withoutScriptless` (621), `withoutAnyReview` (568), and `onlyDependent` (99). `withoutScriptless` denotes exclusion of the 46 RAN2 review-dependent items. The public replay counts dependence from released records and receipts; the original reason-text origin audit remains a separate build-input provenance analysis.

Under the identity rule, excluding all 99 dependent items preserves the aggregate method ordering: mean Cypher accuracy exceeds mean raw-text search, which exceeds mean SQL accuracy. The per-run relation is recorded separately: SQL run D changes from above raw-search mean to below it, and Cypher run I becomes tied with raw-search mean. The regression output checks both examples and the aggregate statement. All four subsets, including the RAN2-only exclusion, retain their actual scores.

`reference_sensitivity.json` preserves the original numeric analysis byte for byte. Its relative historical paths and source hashes record provenance. The current public command obtains its inputs from the checkout selected by `--release`. `reference_origin.json` identifies that original summary and the data-projection boundary. `measurement/` contains the executed public-layout replay outputs and their full comparison. This workflow uses stored responses and obtains zero fresh model responses.
