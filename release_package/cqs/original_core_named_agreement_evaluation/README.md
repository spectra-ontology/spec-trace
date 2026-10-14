# Evaluation of the explicit named-draft agreement repair

The single item `RAN1_P2_CQ2-2` preserves its original English question. The
original RAN1 report explicitly agrees the draft CR in `R1-2001110`, and the
frozen graph identifies that Agreement as `AGR-100-6.1-001`. This source check
supports this particular graph reference and its requested-field scoring contract.
It does not establish causality for other citation edges or normative incorporation.

The text methods actually retrieve the explicit agreement passage. Their final
contexts expose the source chunk identity `AGR-100-e-6.1-001#0`, while the pinned
graph business identifier is absent from those passages. C returns that chunk
identifier and D returns `AGR-100-e-6.1`; both receive zero under the previously
frozen exact-identifier scorer. These zeros are **not evidence that the methods
failed to retrieve the agreement** or that graph storage caused better reasoning.
The source identity difference limits comparison across interfaces. Outputs,
contracts and scores are preserved; no post-output normalization or regeneration
was applied. The actual five request checks and context evidence are in
[run/input_access_audit.json](run/input_access_audit.json).

This additive experiment uses 1 original questions, disjoint from the preserved
371-question cohort. Their original English wording is unchanged. The contract,
gold, provider, model, and failure policy were fixed before model calls.
It is a separate measured cohort, not a representative sample of the full Core.
The combined admission ledger contains 401 of the original
560 IDs, with 159 pending.

All 1 IDs are retained for each method. Execution failures receive zero credit,
including failures on empty gold. Requested-field complete-record F1 and exact
output are reproduced by the frozen scorer, with paired bootstrap uncertainty.

| Method | N | Complete-record macro F1 | Exact output | Failures |
| --- | ---: | ---: | ---: | ---: |
| text2cypher | 1 | 1.0000 | 1/1 | 0 |
| text2sql | 1 | 1.0000 | 1/1 | 0 |
| single_retrieval | 1 | 0.0000 | 0/1 | 0 |
| iterative_retrieval | 1 | 0.0000 | 0/1 | 0 |

One model, `anthropic/claude-opus-4.8`, uses the Anthropic provider only, without
automatic provider/model fallback. These results do not replace historical model
results or demonstrate performance of other models. Text2SQL uses the audited actual value-free physical DDL.



There are 5 retained actual model responses. Known actual
cost is $0.271995; 0 attempts have unknown cost.
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
python3 -B -S release_package/cqs/original_core_named_agreement_evaluation/runtime/verify_additional_evaluation.py \
  --evidence release_package/cqs/original_core_named_agreement_evaluation \
  --bundle release_package/cqs/original_core_named_agreement_repairs \
  --parent release_package/cqs/original_core_repair \
  --out /tmp/spectra_additional_verification.json
```

Preparation, public upload, and fresh unauthenticated download verification are
separate states. This package alone does not certify upload or remote verification.
