# Independent semantic verification

The [checker](check.py) reconstructs candidate universes, hash-selected anchors and query semantics directly from the five released SQLite databases. Its [executed receipt](receipt.json) records **2,530 checks passed, zero failed**, including 132 reference queries and 400 operator controls with exact agreement to the stored full rowsets. It uses independently written Python relation and set operations, importing the Python standard library alone.

The verification covers all 95 original cells, the same 66 available cell pairs, all 2,269,290 pre-predicate candidate/cell memberships, the unchanged selection salt, and matching reference/control SQL structures. Candidate multisets are checked with counts and two cryptographic commutative fingerprints. Every successful query contributes its complete rowset and every task's output-equivalence classes are reconstructed. Released source and execution-database hashes agree before and after the run.

Both arms' 66 reference answers are derived independently in Python. For controls, each arm has 174 complete Python rowset checks and 26 ungrouped aggregation checks. SQLite permits an arbitrary qualifying code value in those ungrouped queries; the checker validates its admissible code set and exact distinct-document count, then replays the recorded SQLite output. The execution uses Python 3.10.12 and SQLite 3.37.2 with immutable read-only database connections and per-query time caps.

The checked comparison is the fixed original available-cell cohort under one hash rule. Witness predicates validate their required 113 controls; the separately reported 87 other controls describe additional mistake coverage. Structural candidate restrictions, 29 unavailable cells, repeated anchors and the one baseline-only distinction remain in the results. The [study guide](../README.md) gives the measurements and interpretation.

Run from the release root after preparing RAN2–RAN5 in `work/semantic_databases` using the existing [semantic-witness guide](../../semantic_witnesses/README.md). The checker reads RAN1 directly from its released plain-file path when absent from that work directory. The final receipt includes an executed check of this layout.

```sh
free -h
python3 -B studies/witness_selection_value/independent/check.py \
  --experiment studies/witness_selection_value --release . \
  --database-directory work/semantic_databases \
  --out work/witness_selection_independent.json
```

The checker writes the specified receipt and preserves existing scientific outputs and database bytes. The current `receipt.json` is bound to the exact current checker SHA-256. A separate [public-path execution receipt](public_replay_receipt.json) records the completed command against this packaged layout; all checks, candidate anchors and complete output hashes agree with the original independent receipt. [Initial checker code](initial_check.py) and [initial execution metadata](initial_run_record.json) preserve the first successful verification history. Its original complete receipt was overwritten during the portability rerun; the initial record identifies metadata transcribed from the observed execution output, and the current receipt contains the later actual complete execution.
