# Additional37 original questions: fresh four-method evaluation

The exact37 questions and contracts were fixed before these predictions. This separate cohort adds to the historical404 questions, yielding441/560 original-question contracts and119 pending in its registered snapshot. Later admissions and earlier model results remain separate. No historical scores transfer.

| Method | N | Complete-record macro F1 | Exact output | Failures |
| --- | ---: | ---: | ---: | ---: |
| text2cypher | 37 | 0.4350 | 14/37 | 2 |
| text2sql | 37 | 0.5637 | 19/37 | 5 |
| single_retrieval | 37 | 0.0002 | 0/37 | 32 |
| iterative_retrieval | 37 | 0.0000 | 0/37 | 29 |

All37 IDs per method remain in the denominator, including parsing errors, query failures, empty answers and abstentions. The pinned model is Anthropic Claude Opus4.8 through OpenRouter, with no model/provider fallback or answer-quality retry. An identical transport retry is retained only when the predeclared transport policy permits it. Raw request payloads, every retained response attempt, usage, model outputs, execution artifacts, failure gates, strict scores and paired analysis are supplied. Authorization headers and configured credential bytes are absent.

Text2Cypher receives the frozen graph schema, and Text2SQL receives complete value-free physical SQLite DDL. Single and two-round retrieval retain the earlier bounded lexical retrieval protocol. No common supplemental source was supplied. Complete graph/text archive-cutoff equality and representativeness for all560 original questions are not established. These method differences and one model prohibit claims of a causal advantage of graph storage. Two nonblind AI semantic judgments are development diagnosis; human and independent expert validation remain0.

Offline replay uses no API or database execution:

```sh
python3 -B -S runtime/verify_authorized37_evaluation.py --evidence . --bundle ../original_core_overnight_repairs37 --out /tmp/authorized37-replay.json
```

All runtime programs are byte-identical to the pre-call registration. Their original local helper paths are preserved as provenance. Fresh live execution additionally requires restored pinned graphs, relational projections, retrieval corpus and credentials; the supplied command verifies saved outputs and strict scoring only. Local packaging, public push and fresh anonymous download verification are separate states.
