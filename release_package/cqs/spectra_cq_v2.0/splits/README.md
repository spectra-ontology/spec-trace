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

## Contract-exact subsets

Four identifier lists here are evaluation subsets of SpectraCQ-Core, not
splits: they partition nothing, and `rebuild_splits.py` neither rebuilds nor
checks them; `rebuild_contract_splits.py` does both (see Rebuilding). Each
holds one identifier per line, sorted.

A Core item holds as asked when no contract flag is set in
`../answer_contract.jsonl` and every returned column its question demands
(verdict `required` in `../contract_demand_provenance.jsonl`) is the scored
answer column, `answer_columns[0]`. A question may demand no column.

`contract_exact_script_fixed_133.txt` lists the 133 items that hold as asked
whatever a language model decided: they hold as asked, every column verdict
made by a language model falls on the scored answer column, and no phrase
verdict is recorded. By working group it holds RAN1 20, RAN2 23, RAN3 25,
RAN4 32 and RAN5 33; by track, lookup 47, aggregation 65, relational 13 and
multihop 8; by answer type, scalar_set 105 and ranked_top_k 28.
`paper/baseline/score_core.py`, at the repository root, scores this subset by
default and all of Core with `--set core`.

`contract_exact_asked_208.txt` lists the 208 items that hold as asked under
the recorded verdicts: 117 demand exactly the scored answer column and 91
demand no column. By working group it holds RAN1 40, RAN2 41, RAN3 40, RAN4 45
and RAN5 42; by track, lookup 69, aggregation 90, relational 38 and multihop
11; by answer type, scalar_set 155 and ranked_top_k 53.
`python3 paper/baseline/score_core.py --set contract_exact_asked_208` scores
it.

`contract_exact_241.txt` and `contract_exact_rule_only_149.txt` are
superseded. The 241 are the Core items whose `contract_disposition` is 1,
that is, with no contract flag set. A column-demand flag
(`question_names_extra_columns` or `mapping_answer`) is set exactly when a
question demands two or more returned columns, so disposition 1 bounds how
many columns are demanded, not which: in 33 of the 241 the one demanded
column is not the scored answer column. By working group the 241 hold RAN1
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
