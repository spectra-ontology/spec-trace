# Additional one original questions: fresh four-method evaluation

The exact one question and contracts were fixed before these predictions. This separate cohort adds to the previously published 450 questions, yielding 451/560 original-question contracts and 109 pending in its registered snapshot. Later admissions and earlier model results remain separate. No historical scores transfer.

| Method | N | Complete-record macro F1 | Exact output | Failures |
| --- | ---: | ---: | ---: | ---: |
| text2cypher | 1 | 0.0000 | 0/1 | 1 |
| text2sql | 1 | 0.0000 | 0/1 | 1 |
| single_retrieval | 1 | 0.0000 | 0/1 | 1 |
| iterative_retrieval | 1 | 0.0000 | 0/1 | 1 |

The ID in every method remain in the denominator, including parsing errors, query failures, empty answers and abstentions. The pinned model is Anthropic Claude Opus4.8 through OpenRouter, with no model/provider fallback or answer-quality retry. An identical transport retry is retained only when the predeclared transport policy permits it. Raw request payloads, every retained response attempt, usage, model outputs, execution artifacts, failure gates, strict scores and paired analysis are supplied. Authorization headers and configured credential bytes are absent.

Text2Cypher receives the frozen graph schema, and Text2SQL receives complete value-free physical SQLite DDL. Single and two-round retrieval retain the earlier bounded lexical retrieval protocol. No common supplemental source was supplied. Complete graph/text archive-cutoff equality and representativeness for all560 original questions are not established. These method differences and one model prohibit claims of a causal advantage of graph storage. Two nonblind AI semantic judgments are development diagnosis; human and independent expert validation remain0.

Offline replay uses no API or database execution:

```sh
python3 -B -S runtime/verify_authorized_incremental7_evaluation_v1.py --evidence . --bundle ../original_core_overnight_repairs7 --out /tmp/authorized_incremental7-replay.json
```

The 9 registered evaluation runtime programs match their explicit pre-call pins. This new matrix-only scope exposes the complete-axis sparse records:[{matrix:...}] declaration in the actual public task and both adapter prompts. The declared additive decoder normalizes that representation and dense native records through the unchanged typed-value kernel and byte-identical original scorer base. Missing answer axes are never inferred from gold or source values. Previous cohort runtime bytes stay unchanged. Separate execution scheduling, packaging and replay helpers retain their own source receipts and package hashes. Original local helper paths are preserved as provenance. Fresh live execution additionally requires restored pinned graphs, relational projections, retrieval corpus and credentials; the supplied command verifies saved outputs and strict scoring only. Local packaging, public push and fresh anonymous download verification are separate states.
