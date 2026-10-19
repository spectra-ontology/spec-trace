# Two additional original questions: fresh four-method evaluation

The exact two questions and contracts were fixed before these predictions. This separate cohort adds to the previously published 478 questions, yielding 480/560 original-question contracts and 80 nonadmitted in its registered snapshot. Later admissions and earlier model results remain separate. No historical scores transfer.

| Method | N | Complete-record macro F1 | Exact output | Failures |
| --- | ---: | ---: | ---: | ---: |
| text2cypher | 2 | 0.0000 | 0/2 | 0 |
| text2sql | 2 | 0.0000 | 0/2 | 1 |
| single_retrieval | 2 | 0.0000 | 0/2 | 0 |
| iterative_retrieval | 2 | 0.0000 | 0/2 | 1 |

Both IDs in every method remain in the denominator, including parsing errors, query failures, empty answers and abstentions. The pinned model is Anthropic Claude Opus4.8 through OpenRouter, with no model/provider fallback or answer-quality retry. An identical transport retry is retained only when the predeclared transport policy permits it. Raw request payloads, every retained response attempt, usage, model outputs, execution artifacts, failure gates, strict scores and paired analysis are supplied. Authorization headers and configured credential bytes are absent.

Text2Cypher receives the frozen graph schema, and Text2SQL receives complete value-free physical SQLite DDL. Single and two-round retrieval retain the registered AUTH37 byte-identical bounded lexical retrieval protocol. No common supplemental source was supplied. Complete graph/text archive-cutoff equality and representativeness for all560 original questions are not established. These method differences and one model prohibit claims of a causal advantage of graph storage. Two nonblind AI semantic judgments are development diagnosis; human and independent expert validation remain0.

Offline replay uses no API or database execution:

```sh
python3 -B -S runtime/verify_authorized_incremental19_evaluation.py --evidence . --bundle ../original_core_overnight_repairs19 --out /tmp/authorized_incremental19-replay.json
```

The registered generation, adapter and analysis programs are byte-identical to their pre-call pins. The separately registered two-question wrapper and guarded native scheduler retain their own source receipts and package hashes. Original local helper paths are preserved as provenance. Fresh live execution additionally requires restored pinned graphs, relational projections, retrieval corpus and credentials; the supplied command verifies saved outputs and strict scoring only. Local packaging, public push and fresh anonymous download verification are separate states.

RAN5 records requested change targets as complete nested spec sets for every recorded release, including empty sets; this does not assert approval or actual standard incorporation. RAN2 records explicit comeback flags under the original default10 selection, including conditional reopeners; this does not assert a currently open decision or fulfilled condition. Sequence disagreements, omitted physical outcomes, opposing interpretations and scope limits remain in the companion repair bundle. Its answer-bearing source verification fixtures were not supplied to model prompts or retrieval. No historical additive484 coverage is claimed.
