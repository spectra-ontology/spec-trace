# Strict named-record evaluation

For current 31 / historical 45 / separate 36 / Core 560 scope relationships,
see the [evaluation scope guide](README_evaluation_scopes.md).

For complete-record comparisons, start with the [recorded comparison](matched_retrieval_measurement/README.md).
It uses 36 eligible formal task variants selected from a fixed 40-item cohort.
All three arms receive the same named-field output contracts. Complete-record F1
and exact output match are primary; partial field credit is secondary.

From the repository root, replay the retained outputs without model or database calls:

```bash
python3 -B release_package/cqs/contract_repair_v1/matched_retrieval_measurement/matched_analysis.py \
  --require-complete --out /tmp/spectra-strict-record-replay.json
```

Use a new output filename; the script refuses to overwrite a report.

For comparisons on the original unchanged questions, start with the
[31-item source-aligned retained-output diagnostic](original_source_aligned/README.md)
before interpreting full-Core or historical annotation-subset scores. Its admission
rule was fixed before reading retained predictions: both source-evidenced AI audits
must judge the full original scoring contract aligned, native reference execution
must be complete, and the declared released/V1 answer-column sets must agree with
source outputs. The fixed cohort contains 11 lookup, 13 aggregation and 7 relational
items, with no multihop item. Native completion concerns the saved reference query;
its original LIMIT clauses and source gaps remain. It re-scores the unchanged 27 original runs of nine
models with the legacy canonical-string value-set scorer, without reconstructing
named records, roles, types, order or multiplicity. V1 is primary; V2 sensitivity
uses the whole identical cohort. This does not recover the paper's default Core/V2
headline or replace the strict 36-variant comparison above.

From the repository root, reproduce the recorded diagnostic without model,
database or retrieval calls and without writing a report:

```bash
python3 -I -B release_package/cqs/contract_repair_v1/original_source_aligned/score_source_aligned_retained_portable_v1.py \
  --bundle release_package/cqs/contract_repair_v1/original_source_aligned \
  --public-root . \
  --expected-manifest-sha256 ef37ec7f075c7d51d87406d20e6c55f050213ef9942eab6cf53cb27277f29813
```

The [all-560 audit dispositions](source_alignment_audit_v1/semantic_alignment_audit_report_v1.json)
and [345-file audit manifest](source_alignment_audit_v1/portable_export_manifest_v1.json)
preserve every original item and all 112 attempts. Both audit receipts were usable
for 480 items; 80 retain one or both unavailable raters and are excluded from cohort
admission, without replacement or performance-based selection. Usable receipts do
not imply alignment. Three admitted items retain differences in coarse role aliases;
their diagnostics stay visible and the fixed 31-item cohort is not reselected.
These are fallible AI judgments, not human/domain-expert validation, a representative
sample or a repair of all Core questions. Gold is nonempty; missing-information
abstention remains untested. Historical graph/text evidence access and source cutoffs
are unequal or unverified. The [offline audit verifier and resource appendix](source_alignment_audit_resources_v1/README.md)
and its [verifier script](source_alignment_audit_resources_v1/verify_semantic_alignment_audit_export_v1.py)
explain the public checks and the retained private-capture hash commitments.

The original
[Core questions](../spectra_cq_v2.0/README.md), their value-set scoring and the
133-item scorer compatibility default remain [historical analyses](../../../paper/baseline/README.md).
They are separate from this strict formal-variant comparison.

The [contract and source audit](README_contract_audit.md) distinguishes automatic
screening of Core 560, direct comparison of 47 original items and formal task
variants. No independent domain expert validated question meaning or gold.

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
