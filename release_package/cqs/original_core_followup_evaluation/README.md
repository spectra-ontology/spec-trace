# Evaluation of additional repaired original questions

This additive experiment uses 8 original questions, disjoint from the preserved
371-question cohort. Their original English wording is unchanged. The contract,
gold, provider, model, and failure policy were fixed before model calls.
It is a separate measured cohort, not a representative sample of the full Core.
The combined admission ledger contains 386 of the original
560 IDs, with 174 pending.

All 8 IDs are retained for each method. Execution failures receive zero credit,
including failures on empty gold. Requested-field complete-record F1 and exact
output are reproduced by the frozen scorer, with paired bootstrap uncertainty.

| Method | N | Complete-record macro F1 | Exact output | Failures |
| --- | ---: | ---: | ---: | ---: |
| text2cypher | 8 | 0.6184 | 4/8 | 2 |
| text2sql | 8 | 0.2498 | 1/8 | 6 |
| single_retrieval | 8 | 0.0000 | 0/8 | 8 |
| iterative_retrieval | 8 | 0.0000 | 0/8 | 8 |

One model, `anthropic/claude-opus-4.8`, uses the Anthropic provider only, without
automatic provider/model fallback. These results do not replace historical model
results or demonstrate performance of other models. The Text2SQL arm here retains
the earlier schema interface. The separate corrected-DDL experiment must be reported
as an interface intervention, with its own full-cohort protocol and predictions.

There are 40 retained actual model responses. Known actual
cost is $1.968755; 0 attempts have unknown cost.
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
python3 -B -S release_package/cqs/original_core_followup_evaluation/runtime/verify_additional_evaluation.py \
  --evidence release_package/cqs/original_core_followup_evaluation \
  --bundle release_package/cqs/original_core_followup_repairs \
  --parent release_package/cqs/original_core_repair \
  --out /tmp/spectra_additional_verification.json
```

Preparation, public upload, and fresh unauthenticated download verification are
separate states. This package alone does not certify upload or remote verification.
