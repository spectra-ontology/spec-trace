# Additional six original questions: fresh four-method evaluation

The exact six questions and contracts were fixed before these predictions. This separate cohort adds to the previously published 452 questions, yielding 458/560 original-question contracts and 102 pending in its registered snapshot. This cohort explicitly exposes the original source-side ranking keys to every method; the zero-call earlier freeze is retained in history. This prompt contract differs from earlier cohorts. Later admissions and earlier model results remain separate. No historical scores transfer.

| Method | N | Complete-record macro F1 | Exact output | Failures |
| --- | ---: | ---: | ---: | ---: |
| text2cypher | 6 | 0.6803 | 3/6 | 1 |
| text2sql | 6 | 0.3333 | 2/6 | 4 |
| single_retrieval | 6 | 0.0000 | 0/6 | 5 |
| iterative_retrieval | 6 | 0.0000 | 0/6 | 3 |

All six IDs in every method remain in the denominator, including parsing errors, query failures, empty answers and abstentions. The pinned model is Anthropic Claude Opus4.8 through OpenRouter, with no model/provider fallback or answer-quality retry. An identical transport retry is retained only when the predeclared transport policy permits it. Raw request payloads, every retained response attempt, usage, model outputs, execution artifacts, failure gates, strict scores and paired analysis are supplied. Authorization headers and configured credential bytes are absent.

Text2Cypher receives the frozen graph schema, and Text2SQL receives complete value-free physical SQLite DDL. Single and two-round retrieval retain the earlier bounded lexical retrieval protocol. No common supplemental source was supplied. Complete graph/text archive-cutoff equality and representativeness for all560 original questions are not established. These method differences and one model prohibit claims of a causal advantage of graph storage. Two nonblind AI semantic judgments are development diagnosis; human and independent expert validation remain0.

Offline replay uses no API or database execution:

```sh
python3 -B -S runtime/verify_authorized_incremental9_evaluation_v3.py --evidence . --bundle ../original_core_overnight_repairs9 --out /tmp/authorized_incremental9-replay.json
```

The eight registered evaluation runtime programs are byte-identical to their pre-call pins. Separate execution scheduling, packaging and replay helpers retain their own source receipts and package hashes. Original local helper paths are preserved as provenance. Fresh live execution additionally requires restored pinned graphs, relational projections, retrieval corpus and credentials; the supplied command verifies saved outputs and strict scoring only. Local packaging, public push and fresh anonymous download verification are separate states.
