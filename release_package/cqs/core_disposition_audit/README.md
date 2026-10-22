# Core question coverage and evidence register

SPECTRA accounts for **all 560 original Core questions** through a disjoint, source-linked register. It connects executable contracts and completed specification diagnostics to the same immutable question identities.

| Classification | Questions | Evidence recorded |
| --- | ---: | --- |
| Contract verified | 522 | Original question, typed answer contract, source witnesses, native/SQL records, two separate AI reviews and scorer checks |
| Clarification required | 21 | Completed, conditional diagnostics identifying the input, metric or scope choice to state |
| Frozen-input-dependent source-role diagnostics | 17 | Completed source-role checks, original witnesses and reproducible input-dependency accounts |
| Evidence pending | 0 | Original identity and adjudication history retained |
| **Total** | **560** | [Machine-readable partition](partition/classification_overlay560.jsonl) |

[current_tasks.jsonl](../current_core/current_tasks.jsonl) selects the 522 active contracts. The legacy binary index records 522 admitted and 38 nonadmitted; this overlay connects executable contracts and completed diagnostic classifications. Classification updates keep answer admission and model scores separate.

## Reproduce the register

Run with Python 3 and its standard library:

```sh
python3 -B -I verify_package.py
```

The portable check verifies file commitments, included source evidence, independent SQLite/Python witness arithmetic and the complete disjoint partition. It makes no model or network calls. [provenance.json](provenance.json) pins the source snapshots, current index and measurement receipts.

[build_partition.py](build_partition.py) rebuilds the overlay from [baseline560_metadata.jsonl](baseline560_metadata.jsonl) and its seven declared candidate files. The [summary](partition/summary.json) reports the same totals.

## What the diagnostics make explicit

The question-first review policy derives requested meaning from the original English and preserved design context, then checks the executable query. Each completed diagnostic retains the authored query as competing authority. Where that query is adopted as the normative specification, its metric, order or cutoff fixes the operational task. Alternative measurements below are conditional probes, rather than replacement gold.

| Fixed source population | Reproducible diagnostic |
| --- | --- |
| RAN3 company contribution paths | Nokia has 161 distinct cited TDocs and 54 citing Resolutions; ZTE has 181 and 52. The unit determines their relative rank. |
| RAN4 company contribution paths | Qualcomm has 40 TDocs and 15 Resolutions; LG Electronics has 36 and 17. The top-ten membership also depends on the stated unit. |
| RAN3#93bis → #94 | ZTE’s Resolution count rises 16 → 19; its share among all Resolutions changes 16/126 → 19/214. |
| RAN4#87 → #88 | Samsung’s Resolution count rises 5 → 9; its all-Resolution share changes 5/51 → 9/95 and its TDoc-linked-Resolution share changes 5/40 → 9/49. |
| Direct Section/Table operands | Explicit area-weight choices change top-ten membership while preserving the operand population. |

The trend diagnostics retain Resolution as the requested unit and vary normalization. Company matching is literal. The released witnesses comprise the full emitted finite diagnostic projections: 4,160 rank paths, 18,577 trend paths and 3,942 Section-to-Spec operands, with their typed section edges.

The 21 clarification cases cover five metric choices, five required inputs, one result extent, three named study descriptions, one agenda description, one pack scope, two source-availability scopes, two cross-meeting agenda/technology scopes and one distinct-Spec selection rule. The 17 frozen-input-dependent cases map each reviewed question to the source attribution needed for complete answer construction. They preserve original evidence, retained relationships and the additional attribution requirements as reproducible diagnostics. These classifications apply to their stated snapshots and policies.

## Inspect a completed classification

| Evidence family | Released records |
| --- | --- |
| Metric, input and extent choices | [Metric cases](metric_classification_candidates.json), [input cases](missing_input_classification_candidates.json), [extent case](extent_classification_candidates.json), [diagnostic arithmetic](diagnostic_results.json) |
| Named study and agenda descriptions | [Study cases](conflicting_entity_description_candidates.json), [agenda cases](conflicting_agenda_description_candidates.json), [study XML evidence](sources/conflicting_TR_description_evidence/), [agenda evidence](sources/conflicting_agenda_description_evidence/) |
| Pack, source-availability and cross-meeting scopes | [Completed scope cases](completed_scope_classification_candidates.json), [pack evidence](sources/conflicting_pack_scope_evidence/), [availability evidence](sources/conflicting_source_availability_evidence/), [company/agenda evidence](sources/cross_meeting_agenda_scope_evidence/), [FL-summary evidence](sources/FL_summary_agenda_scope_evidence/) |
| Work Item-to-Spec membership | [Recorded paths, source CRs and selection diagnostics](sources/work_item_Spec_selection_evidence/) |
| Required source roles in frozen inputs | [Case records](unsupported_classification_candidates.json), [Agreement evidence](sources/agreement_source_loss_evidence/), [structural evidence](sources/structural_source_loss_evidence/), [additional source evidence](sources/additional_frozen_source_loss_evidence/) |
| Operative amendments and recorded decisions | [UCI evidence](sources/UCI_source_amendment_status_evidence/), [DCI evidence](sources/DCI_source_amendment_status_evidence/), [CSI-RS evidence](sources/CSI_RS_amendment_status_evidence/) |

Each evidence package retains the original question/query identity, relevant original-source witnesses, strongest alternative interpretation, separate nonblind AI reviews and executable checks. Review provenance records human/expert review n=0. A case’s evidence states precisely which source roles and finite projections were checked.

For an optional full-graph comparison, [reproduce_full_sqlite.py](reproduce_full_sqlite.py) runs the standalone source queries against restored immutable RAN1, RAN3 and RAN4 databases. [reproduce_extent.py](reproduce_extent.py) can additionally verify the retained RAN4 meeting counts against a restored RAN4 database. The [body-graph guide](../../kg/per_wg/README.md) describes reconstruction inputs.

The full register connects verified answers, explicit specification choices and bounded input dependencies to completed source-linked dispositions. Earlier evidence and model outcomes remain reproducible in their original cohorts.

[Approval-target tracing](sources/RAN4_approval_target_binding_evidence/) connects the original 38.133 Resolution-count question to its complete 216-member recorded frontier, operative source evidence and successful count-level recovery alternatives. Its sealed classification preserves the original query and both semantic reviews.

[NR-U study-to-section tracing](sources/NRU_new_section_role_evidence/) preserves original study, implementation CR and release-aware section identities, including source-specific new-clause evidence and the exact original question.

[Study-to-specification impact tracing](sources/TR_inverse_impact_history_evidence/) preserves the complete original TR/type question, original source roles, implementation CR witnesses and independently replayed graph evidence.

[RedCap study-to-Section source tracing](sources/RedCap_study_Section_effect_evidence/) connects study recommendations, recorded impact paths and actual normative amendments through original TS Section roles and independently replayed source evidence.

[LP-WUS implementation tracing](sources/LPWUS_actual_new_section_evidence/) connects both target specifications to original insertion-format witnesses, preserved author scope and independently replayed graph roles.

[Rel-18 study-to-TS tracing](sources/Rel18_actual_TS_impact_evidence/) connects the six-study release population to declared impact assertions, implementation candidates and source-certified normative changes through independently replayed evidence roles.
