# Review the revised Core contracts

The historical diagnostic covers 31 unchanged original questions. This supplement
instead provides an itemized revision for all 560 original Core IDs. It preserves
both wordings and queries and makes the requested answer fields explicit. The
separate 36-variant model evaluation remains a different analysis.

## What changed, and what was checked

| Change | Inspectable evidence | What the check establishes |
| --- | --- | --- |
| Explicit revised questions and population choices | Itemized pages below; original/revised queries, change rationale and definition hash in every entry | The choices are visible. They remain proposals awaiting author semantic review. |
| Counts and attributes accompany identifiers when requested | Each task's named fields, types, collection, cardinality and tie policy | The scorer checks the declared requested-field records; it does not give complete-record credit for a correct ID with a wrong count. |
| Complete captured reference outputs for every revised query | Every entry links its native rows and execution receipt; 332,153 rows in total | Gold can be checked against the captured archived-graph output. This is not external-world truth or independent expert validation. |
| Contract enforcement | [Recorded local gate: 68 regression tests and 5,490 per-item scorer checks](provenance/adversarial_validation.json); [scorer](scorer.py); 39 runnable scorer/CLI tests | Missing fields, wrong values and types are rejected as complete matches. These tests do not establish question meaning or model performance. |

The 5,490 per-item checks comprise 4,370 negative perturbations and 1,120
reference, unrequested-context and formal-empty controls. They test enforcement
of explicit contracts; they do not replace semantic review. Each entry also
reports byte-level question/query changes and any additional inputs.

## Itemized changes

| Working group | Original IDs | Proposed clarifications | Substantive variants | Retained native rows |
| --- | ---: | ---: | ---: | ---: |
| [RAN1](changes/RAN1.md) | 124 | 55 | 69 | 15,617 |
| [RAN2](changes/RAN2.md) | 114 | 76 | 38 | 52,195 |
| [RAN3](changes/RAN3.md) | 112 | 88 | 24 | 31,970 |
| [RAN4](changes/RAN4.md) | 107 | 83 | 24 | 111,176 |
| [RAN5](changes/RAN5.md) | 103 | 81 | 22 | 121,195 |
| Total | 560 | 383 | 177 | 332,153 |

The 383 clarification labels are proposed classifications, not 383 confirmed
original questions. The 177 variants make substantive scope or meaning choices
and leave the original interpretation unresolved. Author semantic review remains
pending for all tasks. No new model predictions or expert study are supplied.

## A concrete counting repair

[RAN3_P5_TR-CQ-1-4](changes/RAN3.md#ran3_p5_tr-cq-1-4) originally asked for the
status distribution of TRs, while its answer-column key retained only status
labels. The revised contract grades both `status` and `trCount`. The captured
reference contains `(Completed, 11)` and `(Draft, 1)`. A correct status with an
incorrect count receives no complete-record credit. This demonstrates scorer
behavior for the explicit revised graph-relative contract; it does not independently
validate the original question's intended population.

Inspect the [receipt](reference_outputs/RAN3_P5_TR-CQ-1-4/2e5b8bec396345d1d7a8618f28ab2bc8a647c99537e33fa9fad907ed8e95e3ee.json) and [two native rows](reference_outputs/RAN3_P5_TR-CQ-1-4/2e5b8bec396345d1d7a8618f28ab2bc8a647c99537e33fa9fad907ed8e95e3ee.jsonl).

## Another omitted-count case

[RAN4_P1_CQ5-1](changes/RAN4.md#ran4_p1_cq5-1) asks for node counts by label.
Its original query already returned labels and counts, but the historical
answer-column target retained labels. The revised contract requires `label`
and integer `nodeCount`, with multi-label nodes counted under each label.
This is a proposed clarification of the requested counting task, not proof
that every original question in this class has passed human semantic review.

## Verify or adopt the supplement

From this directory, run `python3 -B verify_release.py` and
`python3 -B -m unittest test_scorer test_cli`. These are offline checks, using
captured outputs; they do not start a database or rerun model generations.

The submitted whole-row result and original question diagnostic keep their
historical scope. Existing tracing-coverage limits remain, and two formal empty
reference answers do not measure model abstention. See [claim scope](claim_scope.md)
and [adoption requirements](adoption_plan.md) before treating revised definitions
as a primary evaluation. The existing paper, benchmark and frozen DOI archives
are preserved. This supplement supplies no revised-Core performance ranking.
