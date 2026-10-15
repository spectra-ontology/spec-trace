# Current original Core contract index

This is the single entry point for the current original-question repairs.
All 560 original IDs are retained: 464 have passed the stated repair checks,
and 96 remain pending with their itemized reasons. Original English wording
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
included in these 464 unchanged original questions.

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

The compact [review evidence download](review_evidence.tar.gz) preserves the
400-item snapshot at commit `e89d2769de3e1740f50411fe2333d33341b77873`.
Later original-question repairs are separate, pinned bundles linked by this
index; their model results remain separate. The archive's exact hashes and
file membership are in [manifest.json](manifest.json) and
[archive_inventory.json](archive_inventory.json). The byte-identical duplicate
paths are restored as independent regular files by the supplied verifier.

```sh
python3 -B -S release_package/cqs/current_core/verify_download.py \
  --commit e89d2769de3e1740f50411fe2333d33341b77873 \
  --manifest-sha256 f09422274860088fca875a928560ea581b413f752aebe8726a17ddbea4ed3485 \
  --out-dir /your/fresh/review-evidence
```

This replays saved evidence without model calls or database execution. It
does not repeat the complete historical 371-item model experiment or count
prepared forms as completed expert reviews.

The preserved [Core402 additions manifest](latest_additions_manifest.json) and
[archive](latest_additions.tar.gz) retain the earlier 402-item index snapshot
and its two measured one-item cohorts. Their verifier replays that snapshot;
it does not certify the later current index.

The [observed-trend manifest](observed_trend_manifest.json) and
[download](observed_trend.tar.gz) preserve the earlier 404-item index, all 560
blank source-first review forms, and the disjoint two-item
[repair bundle](../original_core_observed_trend_repair/README.md). The compact
archive uses the byte-preserved Core402 download as a pinned dependency.
Its verifier checks the full 58 source Meeting nodes per WG, exact agenda
Resolution-node counts, native membership, requested fields, ordinal ties,
and all 30 scorer controls. Source ordinal order and graph-observed zero
counts do not establish real-world inactivity, calendar chronology, stable
agenda descriptions, or complete raw-archive coverage. Independent human
and expert reviews remain incomplete; completed reviews number zero.

```sh
python3 -B -S release_package/cqs/current_core/verify_observed_trend_download.py \
  --commit EXACT_40_CHARACTER_RELEASE_COMMIT \
  --manifest-sha256 EXACT_SHA256_OF_OBSERVED_TREND_MANIFEST \
  --out-dir /your/fresh/observed-trend
```

The named-agreement task retains an `admitted: false` proposal-stage field.
Completed admission is recorded by its `validation_status: validated`,
pinned reviews, native capture, scorer checks and bundle manifest. The
current index uses those verified completion records; frozen proposal
metadata is retained rather than rewritten after evaluation.

The two observed-trend ledger entries retain their earlier `reason` and
`continuation_triage` records as history. Their current top-level `status:
pass` and `current_bundle` link to the completed reviews, native captures,
and scorer checks. Historical pending flags describe the earlier inspection,
not the current admission state.

Local preparation, offline replay, public upload, and fresh anonymous
download verification are separate states. Model predictions for these two
new contracts have a separate frozen evaluation when actually completed;
prior scores are not transferred. The compact archive verifier does not
repeat older model experiments.

The [additional37 bundle](../original_core_overnight_repairs37/README.md) preserves the exact cohort authorized before fresh model evaluation. Its 37 unchanged original questions add to the preserved404 index: 441 of560 now pass and119 remain pending in this snapshot. All37 have two separate nonblind AI semantic judgments,26,211 complete native rows, full-field independent SQL agreement and283 replayable scorer controls. Source-fidelity limitations remain explicit. Human/expert reviews and complete physical archive validation are not claimed. The repair bundle has no predictions. Its [fresh four-method evaluation](../original_core_overnight_evaluation37/README.md) uses separately frozen inputs and all 37 IDs per method; raw responses, costs, failures and offline scoring replay are retained.

The [two later original-question repairs](../original_core_overnight_repairs2/README.md) add the complete recorded Resolution-to-Section trace and CR-target layout. This separate cohort raises the current index to 443/560, with 117 pending; its [fresh four-method evaluation](../original_core_overnight_evaluation2/README.md) retains both IDs per method. The earlier 37-item cohort and all its predictions remain unchanged.

Runtime provenance clarification: the eight evaluation programs listed in each pre-call protocol retain their exact registered bytes. Additional scheduling helpers, packaging code and saved-output replay code have separate copy receipts or package hashes. The earlier 37-item evaluation README phrase “all runtime programs” refers to those eight registered evaluation programs, rather than every later audit or scheduling helper in its runtime directory. No generation, query, score or cohort bytes change with this clarification.

The [three recorded title-and-table repairs](../original_core_overnight_repairs3/README.md) add PDCCH, PUSCH and SRS Section-title searches with each direct table-ID set, including empty sets. This separate cohort raises the current index to 446/560, with 114 pending; its [fresh four-method evaluation](../original_core_overnight_evaluation3/README.md) retains all three IDs per method. Earlier cohorts and all their predictions remain unchanged.

The [one recorded TS-comparison repair](../original_core_overnight_repairs1/README.md) compares the top five TS families by CR count with their section counts using the original explicit eight-family domain. This separate cohort raises the current index to 447/560, with 113 pending; its [fresh four-method evaluation](../original_core_overnight_evaluation1/README.md) retains the one ID in every method. Earlier cohorts and all their predictions remain unchanged.

The [Rel-19 recorded-document survey](../original_core_overnight_repairs4/README.md) adds one unchanged original question and all 5,948 recorded matching TDoc identities. This cohort raises the current index to 448/560, with 112 pending; its [fresh four-method evaluation](../original_core_overnight_evaluation4/README.md) retains the one ID in every method. Actual speech, full physical-source truth, and human or expert validation are not established.

The Rel-19 survey evaluation retains five requests, six transport attempts, five received HTTP200 response bodies, $0.294875 known cost and one read-timeout attempt of unknown cost. The first response body was not received; its identical transport retry follows the frozen policy. No answer-quality retry was performed.

The separate original-question cohort 5 adds `RAN1_P3_CQ038`: Return the top 10 most-referenced sections and how many CRs modified each (stability of core sections). Its complete retained reference pool and fresh four-method evaluation are in `release_package/cqs/original_core_overnight_repairs5` and `release_package/cqs/original_core_overnight_evaluation5`. The current index is 449/560, with 111 pending. Earlier cohorts and measurements remain separate; human and expert validation remain incomplete.

For cohort5, all four measured requested-record F1 scores are0. The generated graph and SQL queries ranked by CR modification count rather than the original most-referenced-section rank; one retrieval abstained and the other returned a partial answer. Every first response and execution is preserved without answer-quality regeneration.

The separate original-question cohort 6 adds `RAN2_P2_CQ3-2`: Rank the main contributors to spec 38.331 (RRC ownership). Its complete retained reference pool and fresh four-method evaluation are in `release_package/cqs/original_core_overnight_repairs6` and `release_package/cqs/original_core_overnight_evaluation6`. The current index is 450/560, with 110 pending. Earlier cohorts and measurements remain separate; human and expert validation remain incomplete.

The separate original-question cohort 7 adds `RAN5_P3_CQ5-2`: Show each company's CR contributions per RAN5 spec (contribution matrix). Its complete retained reference pool and fresh four-method evaluation are in `release_package/cqs/original_core_overnight_repairs7` and `release_package/cqs/original_core_overnight_evaluation7`. The current index is 451/560, with 109 pending. Earlier cohorts and measurements remain separate; human and expert validation remain incomplete.

The separate [ZTE documentary TDoc-count repair](../original_core_overnight_repairs8/README.md) and its [fresh four-method evaluation](../original_core_overnight_evaluation8/README.md) add one unchanged original question: 452/560 now pass and108 remain pending. The count uses distinct recorded TDocs cited by Resolutions, with17 actual controls (seven basic and ten count-unit/type/multiplicity controls). It does not establish causal effectiveness, approval or incorporation. All five first-call responses are retained; requested-record F1 is1/1/0/0 for Cypher/SQL/single/two-round retrieval. No quality retry was performed.

The separate [six original documentary and recorded-role repairs](../original_core_overnight_repairs9/README.md) and their [fresh four-method evaluation](../original_core_overnight_evaluation9/README.md) bring the current index to 458/560, with 102 pending. All 442 reference-pool records and 126 controls are retained (49 generic, 65 additional saved actual controls and 12 explicitly synthetic controls). Before any model call, the new cohort protocol exposed the declared source ordering keys to every method; the zero-call earlier protocol and the preregistered correction remain preserved. This prompt protocol differs from earlier cohorts. All 30 first-call responses, four-method failures and abstentions are retained; no quality retry was performed. These recorded documentary paths and marker/role contracts do not establish causal adoption or current-world issue finality.

The separate [two documentary-reference and exact-share repairs](../original_core_overnight_repairs10/README.md) and their [fresh four-method evaluation](../original_core_overnight_evaluation10/README.md) bring the current index to 460/560, with 100 pending. All234 reference-pool records,15 generic controls and63 additional saved control replays are retained. The saved20/root24 share sets overlap; they are not44 independent cases. There are31 source-free checks (six tie fixtures and25 protocol integration checks). Before any model call, every method received the same declared exact rational-share representation, without rounding tolerance; source ordering disclosure is preserved. All10 first-call responses and eight method items, including failures and abstentions, remain unchanged. No quality retry was performed. Documentary references do not establish causal adoption.

The separate [three recorded-status and documentary-share repairs](../original_core_overnight_repairs11/README.md) and their [fresh four-method evaluation](../original_core_overnight_evaluation11/README.md) bring this index snapshot to 463/560, with 97 pending. Five complete native reference records,23 generic scorer controls and50 additional actual source controls are retained; seven separate synthetic boundary/lexical checks and the source-free runtime checks are development diagnostics, not independent population samples. Samsung requires both Tdoc count and exact share, while Huawei requires exact share. All15 first-call responses and12 method outcomes, including errors and abstentions, are retained with no quality retry. Original source ordering keys and the exact-share public representation were exposed before calls. Recorded documentary links do not establish causal adoption. The later local CQ2-2 admission is excluded from this immutable three-question cohort.

The separate [recorded cross-spec impact repair](../original_core_overnight_repairs12/README.md) and its [fresh four-method evaluation](../original_core_overnight_evaluation12/README.md) bring this index snapshot to 464/560, with 96 pending. Ten complete native reference records retain both affected specification identity and distinct CR count, with 10 generic scorer controls and 13 additional saved controls. All five first-call responses and four method outcomes, including errors and abstentions, are preserved with no quality retry. Recorded MODIFIES and the three AFFECTS metadata relationships do not establish actual normative change, causal impact or approval. The original register/source-cover inconsistencies remain disclosed.
