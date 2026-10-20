# Source-grounded process aggregates: first evaluation

These two unchanged Core questions extend the executable process benchmark with CR density across 23 retained spec editions and separate CR/Agreement counts across eight TS families. Their source-grounded references retain 31 native/SQL records, two separate nonblind AI reviews per item and 37 portable controls. The eight-family table includes two zero Agreement counts.

The separate N=2 first-response evaluation preserves all ten call stages and eight method outcomes:

| Method | N | Complete-record macro F1 | Exact output | Failures |
| --- | ---: | ---: | ---: | ---: |
| text2cypher | 2 | 0.0000 | 0/2 | 1 |
| text2sql | 2 | 0.0000 | 0/2 | 1 |
| single_retrieval | 2 | 0.0000 | 0/2 | 2 |
| iterative_retrieval | 2 | 0.0000 | 0/2 | 2 |


The model received the original English, requested output shape and method-specific schema or bounded retrieved context. The reference operations additionally use the preserved author context to select the retained latest edition and the eight-family TS domain. These results record that fixed prompt-to-reference protocol; they do not isolate ontology benefit or graph-storage advantage. The [input-scope evidence](input_scope_evidence.json) retains the actual request pins and operational choices in one place.

The model, methods, prompts, parsers and token settings are unchanged. All errors and abstentions remain in the denominator. Raw first responses, usage and costs are included; no quality rerolls or earlier-score transfers are used. Serial dispatch and a pinned operational credit-floor guard preserve the scientific payload. Human/expert validation remains zero.

Replay the saved outputs without API or database calls:

```sh
python3 -B -I runtime/verify_authorized_incremental30_evaluation.py --evidence . --bundle ../original_core_overnight_repairs30
```

The reference scope, original design and competing source interpretations remain in the [contract package](../original_core_overnight_repairs30/README.md). Source proofs, gold and review fixtures were not supplemental model inputs. Registration counts in the frozen authorization identify its original 497-to-499 scope; the current index records later publication state.
