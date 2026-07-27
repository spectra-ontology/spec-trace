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
