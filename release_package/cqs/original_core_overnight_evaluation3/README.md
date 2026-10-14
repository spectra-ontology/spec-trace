# Additional three original questions: fresh four-method evaluation

The exact three questions and contracts were fixed before these predictions. This separate cohort adds to the previously published 443 questions, yielding 446/560 original-question contracts and 114 pending in its registered snapshot. Later admissions and earlier model results remain separate. No historical scores transfer.

| Method | N | Complete-record macro F1 | Exact output | Failures |
| --- | ---: | ---: | ---: | ---: |
| text2cypher | 3 | 0.9471 | 2/3 | 0 |
| text2sql | 3 | 0.9471 | 2/3 | 0 |
| single_retrieval | 3 | 0.0000 | 0/3 | 3 |
| iterative_retrieval | 3 | 0.0000 | 0/3 | 2 |

All three IDs per method remain in the denominator, including parsing errors, query failures, empty answers and abstentions. The pinned model is Anthropic Claude Opus4.8 through OpenRouter, with no model/provider fallback or answer-quality retry. An identical transport retry is retained only when the predeclared transport policy permits it. Raw request payloads, every retained response attempt, usage, model outputs, execution artifacts, failure gates, strict scores and paired analysis are supplied. Authorization headers and configured credential bytes are absent.

Text2Cypher receives the frozen graph schema, and Text2SQL receives complete value-free physical SQLite DDL. Single and two-round retrieval retain the earlier bounded lexical retrieval protocol. No common supplemental source was supplied. Complete graph/text archive-cutoff equality and representativeness for all560 original questions are not established. These method differences and one model prohibit claims of a causal advantage of graph storage. Two nonblind AI semantic judgments are development diagnosis; human and independent expert validation remain0.

Offline replay uses no API or database execution:

```sh
python3 -B -S runtime/verify_authorized_incremental3_evaluation.py --evidence . --bundle ../original_core_overnight_repairs3 --out /tmp/authorized_incremental3-replay.json
```

The eight registered evaluation runtime programs are byte-identical to their pre-call pins. Separate execution scheduling, packaging and replay helpers retain their own source receipts and package hashes. Original local helper paths are preserved as provenance. Fresh live execution additionally requires restored pinned graphs, relational projections, retrieval corpus and credentials; the supplied command verifies saved outputs and strict scoring only. Local packaging, public push and fresh anonymous download verification are separate states.
