# Explicit task contracts and recorded comparison

This companion makes requested records explicit while preserving the original
SpectraCQ release. Start with the [contract and source audit](README_contract_audit.md)
for the distinction between automatic screening of Core 560, direct comparison
of 47 original items and new formal task variants. No independent domain expert
validated question meaning or gold.

The [recorded comparison](matched_retrieval_measurement/README.md) uses 36
eligible variants selected from a fixed 40-item cohort. All three arms receive
the same output contracts and use strict named complete-record scoring.

| Access condition | Mean complete-record F1 | Exact outputs |
| --- | ---: | ---: |
| Single-pass text | 0.0000 | 0/36 |
| Two-round text | 0.0112 | 0/36 |
| Generated Cypher, original execution gate | 0.7834 | 27/36 |

The primary comparison retains three Cypher execution failures in its denominator.
An overly restrictive gate rejected anonymous read-only `CALL` subqueries.
The [separate execution replay](generated_read_query_replay_provenance_v1.json)
applies a fixed read-only plan gate to **all 36 unchanged saved queries**, with
no new model calls. It reaches 29/36 exact outputs; one newly executable query
still has a wrong complete record. The
[supplementary analysis](matched_retrieval_measurement/supplementary_execution_replay_analysis_v1.json)
preserves the original result and explains this operational correction.

To restore the graph, follow the [deposited-TTL guide](README_frozen_ttl_import.md).
It checks archival checksums and every label/relationship-type count in owned
isolated stores. For offline scoring, follow the comparison README; no model
or database calls are needed. Retained contexts support reader/output auditing.
The full text ranking corpus is not deposited here, and text/graph source-cutoff
equivalence remains unverified. Whole-graph access versus short text passages
does not isolate a causal representation or engine effect.

Three selected reference outputs exceeded the fixed 2,000-row cap and one
external-catalogue definition remained unresolved. Their dispositions are
retained with no replacements. All scored gold outputs are nonempty, so
operational empty predictions do not constitute a validated abstention test.
Outside-RAN transfer and independently authored practitioner questions remain
unevaluated. This companion does not replace all 624 original questions or
certify the complete original Core contract.
