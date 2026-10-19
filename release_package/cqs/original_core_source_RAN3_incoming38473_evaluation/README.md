# RAN3 incoming-impact source experiment: saved model outputs

This is a separate, single-question experiment for unchanged original question
`RAN3_P4_CQ2-3`, using the [source-enriched RAN3 graph](../original_core_source_RAN3_incoming38473/README.md).
It adds **zero** validated questions to the original 560-question benchmark and
does not change that benchmark's frozen graph, predictions or scores.

The first five paid requests used `anthropic/claude-opus-4.8`, Anthropic only,
without provider fallback. All five returned HTTP 200 on their first attempt,
with normal completion and a total reported cost of **USD 0.383310**.
The first-attempt results are preserved, including two execution failures
and two answer parsing failures. Each method has **N = 1**.

| Method | Complete-record F1 | Exact | Execution errors | Answer parse errors |
|---|---:|---:|---:|---:|
| Text2Cypher | 0 | 0 | 1 | 0 |
| Text2SQL | 0 | 0 | 1 | 0 |
| Single retrieval | 0 | 0 | 0 | 1 |
| Two-round retrieval | 0 | 0 | 0 | 1 |

The structured requests explicitly returned `abstain:false`. Their execution
wrapper subsequently marked failed executions as abstentions; these are
execution failures, not model-declared abstentions. The retrieval replies
contain prose and fenced JSON, which the frozen whole-content JSON parser
rejects. Their embedded objects do not replace the original parser results.

## Execution and input limitations

The initial Cypher wrapper incorrectly required a stopped, owned container to
be running before starting it. A separately recorded infrastructure-only
replay fixes that lifecycle check and executes the **identical saved Cypher**
without another model call or query change. Its diagnostic F1 and exact match
are both 1. This supplemental result remains separate from the first-attempt
table and does not replace its zero or constitute a new model sample.

The SQL prompt describes 45 relationship names without the physical `rel_`
prefix while its instruction refers to `rel_TYPE` tables. The saved SQL uses
an absent unprefixed table and fails. This input contradiction recurs from
the already disclosed [original SQL interface limitation](../original_core_evaluation/README.md).
These results therefore do not isolate intrinsic method capability.
The posthoc physical DDL and its validation controls are included for diagnosis;
they were not substituted into the saved request. The earlier
[SQL interface intervention](../original_core_sql_interface_evaluation/README.md)
is a separate experiment and supplies no replacement prediction here.

All four methods use facts from the same separate enriched whole graph.
Structured interfaces and bounded lexical retrieval expose those facts
differently. The generic retrieval corpus contains every node, property and
directed edge, without a question, reference answer or selected-ID whitelist.
Search uses at most 160 candidates per round and twelve context documents,
each bounded to 4,000 characters, with a 48,000-character total context limit.
Corpus completeness does not establish complete answer exposure in a context.
No causal storage advantage or general performance improvement is claimed.

## Offline verification

Use Python 3; this saved-output check needs no network, API key, source database,
Neo4j or third-party Python package. Choose a new output directory:

```sh
python3 -B -I verify_package.py --output /path/to/new-output
```

The command checks the archive hash, extracts only ordinary relative files,
and runs the included verifier in isolation. It rehashes all 88 included frozen
evidence files, checks 32 of the 35 original pre-call pinned inputs, rebuilds
all five exact prompts, checks raw responses and costs, and recomputes the
first-attempt and separate supplemental scores. The three large derived
Turtle, SQLite and FTS artifacts are deliberately omitted and are **not**
reconstructed or freshly verified by this command. Use the separate source
bundle's recipes for those artifacts.

The original runtime bytes remain unchanged. For this offline import only,
the verifier skips the frozen retrieval module's two unused host-environment
assignments, `ROOT` and `CORPUS_DIR`, so replay also works outside a Git checkout.
Historical absolute paths in saved records are provenance, not replay inputs.
Original pre-call and audit failures remain included.

The first portable-verifier audit found missing trust pins and a checkout
dependency. Its failures are preserved in `audit/portable_verifier_independent_v1.json`.
The corrected verifier passed three isolated executions and rejected thirteen
evidence corruptions, including internally repinned changes, in the second
audit. These are nonblind AI/software checks; no human or domain-expert
evaluation is claimed. Original 3GPP sources retain their own attribution
and terms.
