# Current original Core contract index

This is the single entry point for the current original-question repairs.
All 560 original IDs are retained: 443 have passed the stated repair checks,
and 117 remain pending with their itemized reasons. Original English wording
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
included in these 443 unchanged original questions.

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
