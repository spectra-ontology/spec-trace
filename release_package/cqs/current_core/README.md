# Current original Core contract index

This is the single entry point for the current original-question repairs.
All 560 original IDs are retained: 400 have passed the stated repair checks,
and 160 remain pending with their itemized reasons. Original English wording
is unchanged. Ten already admitted IDs use separate full-ranking-pool repairs;
they add zero IDs. Every historical cohort, submission and model result is preserved.

`current_tasks.jsonl` links each admitted ID to its exact question, named-field
contract, gold source, repair hash and frozen bundle. `all_core_dispositions.jsonl`
also retains every unresolved original. Queries and scorers can be inspected
in the referenced bundles; the supplied index does not redefine their semantics.

Pass establishes AI-reviewed consistency with the pinned stored sources and
captured executions, including actual scorer controls. Independent human and
domain-expert validation are not complete. Incomplete raw-source relationships,
ambiguous editions/counting units and unsupported premises remain explicit.
The broader revised canonical Core is a different definition set and is not
included in these 400 unchanged original questions.

New model predictions remain under their actual cohort and input conditions.
The corrected SQL378 experiment uses the earlier contracts. Supplemental
ownership/catalog experiments add common source data to every method;
their extra information budget is explicit. Neither older scores nor these
different input interfaces are silently transferred to current contracts.

From the repository root, without credentials or database execution:

```sh
python3 -B -S release_package/cqs/current_core/verify_index.py
```

Preparation, public upload and external download/replay verification are
separate states. The paired raw-source and retrieval diagnostic is limited
to its fixed 23 items and does not certify the complete corpus.
