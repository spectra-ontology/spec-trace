# Current original Core contract index

This is the single entry point for the current original-question repairs.
All 560 original IDs are retained: 402 have passed the stated repair checks,
and 158 remain pending with their itemized reasons. Original English wording
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
included in these 402 unchanged original questions.

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

`index_manifest.json` records the current 402-item index. `manifest.json`
describes the preserved 400-item download only. The separate
[latest additions manifest](latest_additions_manifest.json) pins the current
index and both new one-question repair/evaluation packages. Its
[inventory](latest_additions_inventory.json) and
[download](latest_additions.tar.gz) preserve their exact evidence bytes.
`verify_latest_additions.py` downloads that pinned release anonymously and
replays the two new contracts, two evaluations, current index and blank
human-review inputs. Older model experiments are outside this download's
replay scope.

```sh
python3 -B -S release_package/cqs/current_core/verify_latest_additions.py \
  --commit EXACT_40_CHARACTER_RELEASE_COMMIT \
  --manifest-sha256 EXACT_SHA256_OF_LATEST_ADDITIONS_MANIFEST \
  --out-dir /your/fresh/latest-additions
```

The named-agreement task retains an `admitted: false` proposal-stage field.
Completed admission is recorded by its `validation_status: validated`,
pinned reviews, native capture, scorer checks and bundle manifest. The
current index uses those verified completion records; frozen proposal
metadata is retained rather than rewritten after evaluation.

```sh
python3 -B -S release_package/cqs/current_core/verify_download.py \
  --commit e89d2769de3e1740f50411fe2333d33341b77873 \
  --manifest-sha256 f09422274860088fca875a928560ea581b413f752aebe8726a17ddbea4ed3485 \
  --out-dir /your/fresh/review-evidence
```

This replays saved evidence without model calls or database execution. It
does not repeat the complete historical 371-item model experiment or count
prepared forms as completed expert reviews.
