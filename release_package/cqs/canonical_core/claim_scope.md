# Evidence and validation scope

| Claim | Evidence | Limit |
| --- | --- | --- |
| Every original Core ID is accounted for. | [migration](migration.jsonl), original answer contract and benchmark under `provenance/` | The original 624-question release is preserved; this bundle addresses its 560 Core IDs. |
| Revised question, query and graded output roles are explicit. | [tasks](canonical_tasks.jsonl), exact definitions and scoped AI reviews under `provenance/` | Revised-definition consistency is not certification of the original question or domain meaning. |
| Required-field gold is derived from complete captured query output. | `reference_outputs/`, [gold](canonical_reference_gold.jsonl), five execution summaries | Offline verification rechecks captured output; it does not query a live database or establish external truth. |
| Named roles, values, types, cardinality and order follow each contract. | [scorer](scorer.py), unit tests, [technical verification](provenance/adversarial_validation.json) | Synthetic counterexamples and reference self-checks are not model performance. |
| 383 proposed clarifications and 177 substantive variants are distinguished. | `original_intent_change`, original/revised questions, change rationales and migration | The 177 variants leave their original interpretation unresolved. All tasks still require author semantic review. |

The local technical pipeline and AI contract cross-review passed for the revised
definitions in this bundle. No independent 3GPP expert review, practitioner-authored
question study, missing-information abstention experiment, transfer outside RAN,
new model evaluation or SQL/SPARQL parity test was performed for these revisions.
The two catalog questions use an explicitly supplied uncurated internal input.
Historical scores and the separate 31-question and 36-variant analyses retain
their own tasks and predictions. They are not results for this revised Core.

The manifest pins captured files and graph restoration identifiers. It does
not constitute independent attestation or certify absence of arbitrary external
property mutations. New model predictions require the matching definition hash;
the scoring CLI cannot establish how those predictions were generated.
