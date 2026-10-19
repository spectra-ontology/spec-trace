# One additional original question: fresh four-method evaluation

The exact question and contract were fixed before these predictions. This separate cohort adds to the previously published 480 questions, yielding 481/560 original-question contracts and 79 nonadmitted in its registered snapshot. Later admissions and earlier model results remain separate. No historical scores transfer.

| Method | N | Complete-record macro F1 | Exact output | Failures |
| --- | ---: | ---: | ---: | ---: |
| text2cypher | 1 | 0.0045 | 0/1 | 0 |
| text2sql | 1 | 0.0000 | 0/1 | 0 |
| single_retrieval | 1 | 0.0000 | 0/1 | 1 |
| iterative_retrieval | 1 | 0.0000 | 0/1 | 1 |

The one ID in every method remains in the denominator, including parsing errors, query failures, empty answers and abstentions. The pinned model is Anthropic Claude Opus4.8 through OpenRouter, with no model/provider fallback or answer-quality retry. An identical transport retry is retained only when the predeclared transport policy permits it. Raw request payloads, every retained response attempt, usage, model outputs, execution artifacts, failure gates, strict scores and paired analysis are supplied. Authorization headers and configured credential bytes are absent.

Text2Cypher receives the frozen graph schema, and Text2SQL receives complete value-free physical SQLite DDL. Single and two-round retrieval retain the registered AUTH37 byte-identical bounded lexical retrieval protocol. No common supplemental source was supplied. Complete graph/text archive-cutoff equality and representativeness for all560 original questions are not established. These method differences and one model prohibit claims of a causal advantage of graph storage. Two nonblind AI semantic judgments are development diagnosis; human and independent expert validation remain0.

Offline replay uses no API or database execution:

```sh
python3 -B -S runtime/verify_authorized_incremental20_evaluation.py --evidence . --bundle ../original_core_overnight_repairs20 --out /tmp/authorized_incremental20-replay.json
```

The registered generation, adapter and analysis programs are byte-identical to their pre-call pins. The separately registered one-question wrapper and guarded native scheduler retain their own source receipts and package hashes. Original local helper paths are preserved as provenance. Fresh live execution additionally requires restored pinned graphs, relational projections, retrieval corpus and credentials; the supplied command verifies saved outputs and strict scoring only. Local packaging, public push and fresh anonymous download verification are separate states.

RAN3 records summaries from the approved meeting record, under the inherited first10 selection. The requested summary-only output is a multiset: ten CR occurrences include seven distinct summary values, and repeated values must retain their multiplicity. Output serialization order is unrequested while source selection order determines membership. The source-context interpretation, physical-session alternative, post-meeting outcomes, source-field defects and complete register/own-decision replay remain in the companion repair bundle. Its answer-bearing source verification fixtures were not supplied to prompts or retrieval. Historical factuality withdrawals, prior explicit RAN5 readmission, and14 clarification diagnostics remain separate. No historical additive coverage or transferred scores are claimed.
