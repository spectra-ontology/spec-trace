# Evaluation scopes and current evidence

Use the **31 original-question diagnostic** for qualified comparisons on unchanged
questions and the **36 formal variants** for explicit complete-record evaluation.
The historical 45-item diagnostic and Core 560 remain separate analyses.

| Scope | Evidence | Limits |
| --- | --- | --- |
| Current 31 original questions | Two AI contract checks and complete saved native execution; 27 retained runs of nine models rescored with released/V1 key | No multihop item; legacy answer-column scoring; no expert certification |
| Historical 45 original questions | Earlier four-axis AI compatibility review on 133 candidates | Different inputs and criteria; no multihop or declared tuple/mapping item; no expert certification |
| Separate 36 formal variants | Explicit named fields, types, roles and collections; complete-record single-pass, two-round text and Cypher comparison | Different tasks and scoring; unequal evidence access; source-cutoff equivalence unverified |
| Core 560 | Historical results, full-row sensitivity and full-Core retained SQL/Cypher reanalysis | Original question/scoring contract not fully consolidated |

The 31 and 45 share **15 IDs**; neither contains the other. The 31 share no
original-question IDs with the 36 variants. The
[scope relationship record](evaluation_scope_alignment_v1.json) pins the input
files and set comparisons. Do not combine their scores into a validation rate.

Table 14's original full-row F1 of 0.1637, versus answer-column F1 of 0.3519,
remains evidence about the original predictions. The separate variant F1 of
0.7834 does not improve or repair it. On 26 multi-field variants, Cypher F1 is
0.7385 with 18/26 exact outputs, retaining all three original query failures.

The original Table 14 whole-row snapshot was not retained. The public
[full-record replay](../../../paper/baseline/README.md#full-record-scoring) is
a later execution on the released graphs and reports 0.1649 for the same model
with the default key. It does not independently reproduce Table 14's 0.1637;
the different execution snapshots and scoring keys must remain distinguished.

Iterative retrieval was not evaluated in the historical rebuilt Core stacks.
The completed two-round comparator is on the separate 36 variants: F1 0.0112,
zero exact outputs. These results do not establish that the text arms received
all information needed. Contexts are retained, but the full ranking corpus is
not deposited. Whole-graph access versus capped text and unverified source
cutoffs do not isolate a causal graph-storage effect.

Independent practitioner questions and expert validation remain future work
beyond the camera-ready. No expert-validation or deployment result is reported.
All gold is nonempty; missing-information abstention and outside-RAN transfer
remain untested. The complete canonical Core contract remains unfinished.

Specification-clause prose and graph Section records are separate evidence
layers. In the checksum-pinned [graph schema](source_schema_frozen_v1.json),
Section nodes in all five working groups have structural fields and titles,
without a clause-body literal. The retained
[text-retrieval contexts](../../../paper/baseline/results/_rag_cache/) separately
contain TS-section excerpts from **all five working groups**, including RAN2–RAN5.
Their presence establishes neither complete clause-text coverage nor an
end-to-end graph-to-prose join. A RAN1-only clause-body description is therefore
not supported as a description of these public evidence layers.

Start with the [31-item replay](original_source_aligned/README.md),
[36-variant measurement](matched_retrieval_measurement/README.md), and
[historical analyses](../../../paper/baseline/README.md).
The [scenario provenance](../../validation/validation_manifest.md) records
Table 15's deployed270/released1249 discrepancy and its unknown cause.
The existing [traceability query](../../queries/cypher/MULTI_HOP_traceability.cypher)
joins clause-modifying CR rationale and TR impact targets by specification number,
supporting a shared-specification association, not a causal report-to-CR link.
Its historical header wording about reports having "shaped" a specification
does not establish influence on an individual CR or equality of release editions.
