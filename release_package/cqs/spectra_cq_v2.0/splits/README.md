# SpectraCQ canonical splits

Four canonical splits over the 624-question SpectraCQ key, so that scores
reported by different users are comparable. Splits are released as
identifier lists: re-scoring the gold does not invalidate them.

| split | train | dev | test | what it isolates |
|---|---|---|---|---|
| `standard_60_20_20/` | 374 | 125 | 125 | 60/20/20 stratified over the 20 (working group x track) strata |
| `template_disjoint/` | 375 | 125 | 124 | whole leakage groups move together, so no query shape and no question string spans a boundary |
| `cross_wg_heldout_ran5/` | 382 | 128 | 114 | RAN5 held out in full; all 114 RAN5 questions are in test |
| `challenge_subset.txt` | — | — | 33 | evaluation-only subset, not a partition |

Each split directory holds `train.txt`, `dev.txt`, `test.txt`: one question
identifier per line, sorted. The three parts of each split partition the
624-question key exactly.

## Annotation-derived contract subsets

The four `contract_exact_*` identifier lists are evaluation subsets of SpectraCQ-Core, not
splits: they partition nothing, and `rebuild_splits.py` neither rebuilds nor
checks them; `rebuild_contract_splits.py` does both (see Rebuilding). Each
holds one identifier per line, sorted.

A Core item enters the 208-item subset when no contract flag is set in
`../answer_contract.jsonl` and every column with a recorded `required`
verdict in `../contract_demand_provenance.jsonl` is the scored answer column,
`answer_columns[0]`. An item may have no recorded `required` column. These
are conditions on the released annotations, not an independent validation
of everything the question asks. The `contract_exact_*` filenames are kept
for compatibility.

`contract_exact_script_fixed_133.txt` lists the 133 items of the 208 for
which every column verdict made by a language model falls on the scored
answer column and no phrase verdict is recorded. Membership is invariant to
changing those model verdicts while keeping the rule verdicts, flags and
scored answer column fixed. The rules and flags can still miss a requested
count, relationship attribute or ordering requirement. By working group it
holds RAN1 20, RAN2 23, RAN3 25,
RAN4 32 and RAN5 33; by track, lookup 47, aggregation 65, relational 13 and
multihop 8; by answer type, scalar_set 105 and ranked_top_k 28.
`paper/baseline/score_core.py`, at the repository root, preserves this subset as
its historical compatibility default and scores all Core with `--set core`.
Neither path certifies every requirement of the original natural-language question.

`contract_exact_asked_208.txt` lists the 208 items satisfying the recorded
conditions above: 117 have exactly the scored answer column marked
`required` and 91 have no column marked `required`. By working group it
holds RAN1 40, RAN2 41, RAN3 40, RAN4 45
and RAN5 42; by track, lookup 69, aggregation 90, relational 38 and multihop
11; by answer type, scalar_set 155 and ranked_top_k 53.
`python3 paper/baseline/score_core.py --set contract_exact_asked_208` scores
it.

`contract_exact_241.txt` and `contract_exact_rule_only_149.txt` are
superseded. The 241 are the Core items whose `contract_disposition` is 1,
that is, with no contract flag set. A column-demand flag
(`question_names_extra_columns` or `mapping_answer`) is set exactly when a
the annotations mark two or more returned columns as required, so
disposition 1 bounds the recorded column-demand count, not the column's
identity: in 33 of the 241 the one column marked `required` is not the
scored answer column. By working group the 241 hold RAN1
48, RAN2 47, RAN3 42, RAN4 53 and RAN5 51; by track, lookup 77, aggregation
107, relational 44 and multihop 13, against lookup 178, aggregation 179,
relational 154 and multihop 49 over all 560 Core items. The 149 are the items
of the 241 in which no column or phrase verdict was made by a language model
(`method` in `../contract_demand_provenance.jsonl`). By working group they
hold RAN1 24, RAN2 27, RAN3 26, RAN4 37 and RAN5 35; by track, lookup 50,
aggregation 75, relational 16 and multihop 8; by answer type, scalar_set 115
and ranked_top_k 34. Of the 33, 17 are among the 149; the other 132 of the
149 all lie in the 133. Both lists stay so that earlier scores on them can be
reproduced with `--set contract_exact_241` and
`--set contract_exact_rule_only_149`.

The 132-item rule-only diagnostic subset is the intersection of the
preserved 149 and 133 lists. It has no separately authored membership file;
it removes the 17 items with a recorded off-answer-column demand from the
legacy 149. Neither the 132 nor the 133 is a human-validated semantic subset.
`paper/baseline/analyse_contract_subsets.py` at the repository root derives
the 132 without a new membership file and reports the 133/208/132 scores,
declared-type and column-position sensitivities, and optional paired
bootstrap comparisons with the best original text run reselected per draw.
The [recorded 30-population analysis](../../../../paper/baseline/results/contract_subset_analysis.json)
contains the actual identifiers, input/source hashes and 10,000-draw seed-0
intervals. The [baseline README](../../../../paper/baseline/README.md) gives
the reproduction commands and `--ids PATH` for a separately fixed Core list.

The scoring key is the reference query's declared answer-column value set.
It does not grade other returned columns, row multiplicity or row order.
For example, `RAN4_P1_CQ5-1` asks for node counts by label but its scored
column is `label`, and `RAN5_P1_CQ1-5` asks for Samsung's TDocs newest first
but the set score ignores their order. Both are in the 133. The subset
conditions therefore cannot establish that all count, routing or ranking
requirements are scored.

Names and labels in the frozen annotations are historical; the membership
conditions do not validate natural-language questions. The
[annotation diagnostic](../contract_annotation_diagnostics.json), produced
by [audit_demand_annotations.py](audit_demand_annotations.py), enumerates
unscored returned fields and query syntax over all Core items and the 133/208
subsets, with three source-grounded examples. Syntactic signals do not measure
semantic error prevalence and are not independent practitioner validation.

## AI-assisted field-coverage diagnostic

`field_coverage_reviewed_ids.txt` contains the 67 items that both recorded
AI reviews of all 133 candidates marked `field_aligned`. The
[review record](../field_coverage_review.json) includes the fixed protocol,
source hashes and both judgments with question/query anchors. Each review
saw the question, reference query, returned columns and declared answer
column, with predictions, scores, annotation labels and the other review
hidden. The intersection was frozen before its subset was scored; any
`mismatch` or `ambiguous` judgment excluded the item, with no later
score-based adjudication. The other 66 items are exclusions under this
procedure, not 66 independently confirmed semantic errors.

These are two isolated Codex AI reviews, not human or 3GPP expert validation.
Their judgments may share errors; the exact model snapshot was not recorded.
This diagnostic does not replace Core, the 133/208 or the Core scorer's
133-item compatibility default. Questions, gold and recorded outputs are
unchanged. By working group it has RAN1 7, RAN2 9, RAN3 15, RAN4 21 and
RAN5 15; by track, lookup 21, aggregation 42, relational 3 and multihop 1.
There are no declared tuple/mapping items, so results on this selected
cohort do not establish broad performance on multi-field answers or all tracks.
The cohort was selected for coverage by value-set scoring; it is not a random
or representative sample of Core.

From the repository root:

```bash
python3 release_package/cqs/spectra_cq_v2.0/splits/rebuild_field_coverage_subset.py --check
```

This checks the stored judgments, source/input anchors and their intersection
against the shipped identifier list. It does not repeat the AI reviews or
verify that their semantic judgments are true. The
[recorded analysis](../../../../paper/baseline/results/field_coverage_subset_analysis.json)
uses that fixed list with `analyse_contract_subsets.py --ids`, 10,000 paired
seed-0 resamples and the original 18 text runs; the
[baseline README](../../../../paper/baseline/README.md) gives the command and
the distinct answer-column and record-scoring definitions.

## Four-axis question/scoring diagnostic

The subsequent [review record](../question_scoring_scope_review.json) stores
the exact protocol, original input, two raw AI-review texts and their hashes
for all 133 candidates. It separates required fields, scope/roles,
cardinality/truncation and ordering/duplicates. Each axis is compatible,
incompatible or unclear; overall compatibility requires all four compatible,
any incompatible axis makes the item incompatible, and the remainder are
unclear. The [45 IDs](question_scoring_scope_reviewed_ids.txt) are the fixed
intersection of two overall-compatible lists, contained in the earlier 67.
The 67-item judgments, membership and analysis above are preserved.

Two fresh isolated Codex AI agents saw only the protocol and source-visible
question/query/columns, without predictions, scores, earlier judgments or
demand annotations. The designers already knew the parent Core/133/208/67
metrics. The recorded ID freeze is 2026-10-06 22:42:02 UTC, before the
new 45-item scoring; no score-based adjudication changed that list. These
fallible AI judgments are not human expert validation or full semantic
certification; the 88 exclusions include uncertainty and disagreements.

Composition is RAN1 5, RAN2 5, RAN3 8, RAN4 17 and RAN5 10; lookup 14,
aggregation 30, relational 1 and multihop 0, with no declared tuple/mapping
item. The original type labels are 40 `scalar_set` and 5 `ranked_top_k`;
set scoring ignores rank order, while the ordering axis concerns explicit
question requirements. The selected cohort is not representative of Core
and does not support broad multi-field or track claims. Original questions,
keys, outputs, canonical splits and the 133 scorer default are unchanged.

From the repository root:

```bash
python3 release_package/cqs/spectra_cq_v2.0/splits/rebuild_question_scoring_scope_subset.py --check
python3 -m unittest discover -s release_package/cqs/spectra_cq_v2.0/splits -p 'test_rebuild_question_scoring_scope_subset.py'
```

The checker pins the protocol/input hashes, reconstructs source fields from
the original benchmark and Core key, checks raw-review hashes, literal source
anchors, four-axis aggregation, status counts and exact intersection bytes.
It accepts an empty intersection as an empty file. It does not repeat the
reviews, prove their reasoning true or independently certify freeze chronology.
Its synthetic integrity tests are separate from baseline scoring checks.
The [recorded 45-item analysis](../../../../paper/baseline/results/question_scoring_scope_subset_analysis.json)
uses the same offline `--ids` path, original 18 text arms and paired seed-0
bootstrap protocol. The [baseline README](../../../../paper/baseline/README.md)
gives its measured values, comparator limits and reproduction command.
Its model ranks are compared with Core under the same scorer: answer-column
Spearman is 0.850000 (2/9 changed positions), full-record P is 0.583333
(6/9), and S/C are 0.600000 (6/9 each). Answer-column rank agreement does
not extend to full-record scoring.

The supplementary [structured-access analysis](../../../../paper/baseline/results/structured_access_core_analysis.json)
uses all 560 Core identifiers, not a success-filtered subset. It re-scores
retained SQL/Cypher outputs on the same repaired answer-column key and includes
failed queries as zero; it changes no split or subset membership. See the
baseline README for its paired interval and historical/provenance limits.

## Composition and audits

`composition.json` carries, for every split and every part, the per-track and
per-working-group composition, the stratification deviation, the leakage audit
(template, question string, gold answer set) and the contamination counts. It
also carries the challenge subset's five difficulty conditions, the per-
condition counts, and its composition by track and by working group.

`track_assignment.json` gives the track label of each of the 624 questions
(lookup 213, aggregation 195, relational 164, multihop 52). It is the
stratification axis of the standard and cross-group splits.

## Rebuilding

Membership is a deterministic function of the question identifier — a salted
SHA-256 key, not a random-number generator — so a rebuild reproduces the split
files byte for byte:

```bash
python3 rebuild_splits.py          # re-derives and verifies, exits non-zero on any mismatch
python3 rebuild_splits.py --write  # re-derives and rewrites the identifier lists
```

The rebuild reads only `../benchmark.jsonl` and `track_assignment.json`, both
of which ship here; it needs no database and no network.

`rebuild_contract_splits.py` rebuilds the four contract-exact lists from
`../answer_contract.jsonl`, `../contract_demand_provenance.jsonl` and
`../core_answer_gold.jsonl`, checks how those files agree with each other, and
compares each rebuilt list byte for byte with the shipped one. It needs no
database and no network:

```bash
python3 rebuild_contract_splits.py --check   # rebuilds and verifies, exits non-zero on any mismatch
python3 rebuild_contract_splits.py --write   # rebuilds and rewrites the four lists; writes nothing if the input files disagree
```
