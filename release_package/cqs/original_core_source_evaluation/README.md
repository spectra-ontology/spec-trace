# Evaluation of additional repaired original questions

This additive experiment uses 5 original questions, disjoint from the preserved
371-question cohort. Their original English wording is unchanged. The contract,
gold, provider, model, and failure policy were fixed before model calls.
It is a separate measured cohort, not a representative sample of the full Core.
The combined admission ledger contains 391 of the original
560 IDs, with 169 pending.

All 5 IDs are retained for each method. Execution failures receive zero credit,
including failures on empty gold. Requested-field complete-record F1 and exact
output are reproduced by the frozen scorer, with paired bootstrap uncertainty.

| Method | N | Complete-record macro F1 | Exact output | Failures |
| --- | ---: | ---: | ---: | ---: |
| text2cypher | 5 | 0.4000 | 2/5 | 3 |
| text2sql | 5 | 0.0000 | 0/5 | 5 |
| single_retrieval | 5 | 0.2000 | 1/5 | 4 |
| iterative_retrieval | 5 | 0.2000 | 1/5 | 3 |

One model, `anthropic/claude-opus-4.8`, uses the Anthropic provider only, without
automatic provider/model fallback. These results do not replace historical model
results or demonstrate performance of other models. Text2SQL uses the audited actual value-free physical DDL.

Every method request, including follow-up retrieval, receives the same complete preserved common source input (62603 extra characters). This input lies outside the native retrieval context budget. Keep this information intervention separate from prior interfaces. No reference query, gold or repair review is provided.

There are 25 retained actual model responses. Known actual
cost is $7.000715; 0 attempts have unknown cost.
The text corpus and graph collection cutoffs/content are not established as equal.
Finite retrieval context does not establish complete population evidence.
AI review and read-only reference execution establish contract consistency within
the pinned sources. They do not establish complete factual coverage of raw archives.
There are zero completed independent human/expert reviews.

Raw requests, model responses, generated queries, executed rows, failure states,
usage receipts, source guards and code pins are retained under `run/` and `runtime/`.
Private originals remain unchanged; any public account-finance redaction is listed
in `public_redactions.json`. Model inputs and answer content are not redacted.

## Offline replay

From the public repository root, without credentials or database execution:

```bash
python3 -B -S release_package/cqs/original_core_source_evaluation/runtime/verify_additional_evaluation.py \
  --evidence release_package/cqs/original_core_source_evaluation \
  --bundle release_package/cqs/original_core_source_repairs \
  --parent release_package/cqs/original_core_repair \
  --out /tmp/spectra_additional_verification.json
```

Preparation, public upload, and fresh unauthenticated download verification are
separate states. This package alone does not certify upload or remote verification.
