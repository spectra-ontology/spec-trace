# Completed competency-query reproduction

The supplied CQ views support a completed execution of all 654 authored questions
on both the source graphs and separately restored graphs. Both executions produce
644 `PASS` and 10 `NO_DATA` outcomes. Query identities, row counts, declared minimum
checks and guard outcomes match for every question. The [summary](summary.json)
links these results to the execution receipts, restored-content fingerprints and
per-question analyses.

| Group | Questions per graph | PASS | NO_DATA | Different row multisets | Different ordered-row hashes |
|---|---:|---:|---:|---:|---:|
| RAN1 | 145 | 137 | 8 | 23 | 37 |
| RAN2 | 132 | 130 | 2 | 10 | 16 |
| RAN3 | 129 | 129 | 0 | 10 | 20 |
| RAN4 | 125 | 125 | 0 | 5 | 10 |
| RAN5 | 123 | 123 | 0 | 2 | 9 |
| Total | 654 | 644 | 10 | 50 | 92 |

The [strict comparison](comparison-all654.json) retains all 50 row-multiset and
92 ordered-row hash differences. Complete graph enumeration verifies both actual
selections for each of the 50 questions against the unchanged query: equal sort
keys at a `LIMIT` boundary, selections without a complete ordering, or unordered
collection members account for these differences. The analyses preserve strict
inequality and the original measured outcomes. The saved diagnostic rows have
[100 matching bindings](strict-diagnostic-row-bindings-all5.json) to the actual
source and restored execution receipts; the [independent check](independent_checks/resource_closure_cq_rows.json)
checks both ordered and multiset hashes.

Per-group analyses provide the concrete candidate populations and selection checks:
[RAN1](RAN1-selection-boundary-root.json),
[RAN2](RAN2-selection-boundary-root.json),
[RAN3](RAN3-row-difference-independent-classification.json),
[RAN4](RAN4-row-difference-independent-classification.json), and
[RAN5](RAN5-selection-boundary-cq.json).

The five restored views contain 2,325,599 nodes and 11,840,212 relationships.
Full projected-content fingerprints, relative native node order, observed ordered
label populations and 238 schema-token observations per group are checked against
the captured source inputs. The [independent payload check](independent_checks/resource_closure_cq_payloads.json)
streams all ten compressed shards; the [restore-receipt check](independent_checks/resource_closure_cq_restore_receipts.json)
connects those fingerprints to the actual database restorations. RAN1's separately
recorded schema-token repair supplies the source-known empty-population tokens;
its initial execution and the subsequent corrected restoration receipt are retained.

[Source](fresh-original-all654.json) and [restored](fresh-restored-all654.json)
collections retain their member-receipt hashes. The RAN5 source classification
applies the original validator's explicit `expected_min_rows=0` rule offline to
four saved empty results; [initial](original-RAN5.json) and
[corrected](original-RAN5-classification-corrected.json) receipts retain the same
measured rows and guard outcomes. The [independent assertion check](independent_checks/resource_closure_cq_status_recheck.json)
reclassifies all 1,308 source and restored records from their declared conditions.

These are fresh executions of the captured current process graphs. The 25 archived
execution receipts retain their original bytes and recorded historical bindings.
The [standalone definition contract](../definition_contract.json) identifies all
25 current definition files and 654 question/query records. Evidence files retain
execution-time path labels; the release-relative artifact index in `summary.json`
locates their supplied copies. The [runner guide](../../../restore/competency_queries/README.md)
provides input verification, restoration, execution and strict comparison commands.
The [19 adversarial regression checks](independent_checks/cq_portable_final_staging_regression.json)
exercise the final portable code and input contract.
