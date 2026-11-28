# Repeated SQL and Cypher submissions on SPECTRA

This study joins each submitted SQL or Cypher query to its benchmark question, native execution outcome and expected answer set. It covers eight model configurations on two workloads across five 3GPP working groups.

| Workload | Input and repetitions | Recorded positions |
| --- | --- | ---: |
| Full workload | 667 questions from seven families. Four Codex and four Claude Code configurations, ten repetitions per language, one working group per session. Every configuration was assigned the same schema-only task packet within each language and group. | 106,720 |
| Matched value-domain study | 50 fixed questions (35 main, 15 order extension). Each language and model receives a schema and scope mapping with or without categorical value domains. Codex has two repetitions and Claude Code has ten per condition. | 9,600 |

The full study contains 800 sessions. A repetition pools five working-group batches and uses the same 667 questions. The matched study contains 192 sessions of 50 assigned questions each. Repetitions measure variability on these fixed questions. The shared A/B repetitions support the matched comparison across both cohorts. All configurations requested medium effort. The run table records the observed model and effort when the session receipt contains them. For full-workload Claude runs it also counts nonempty packet lines and lines absent from the recorded tool output. Execution used SQLite 3.37.2 and Neo4j 5.26.0 with a 60-second query limit and at most 2,000 returned rows. The historical prompt experiments have their own exposure conditions and run counts in [the experiment guide](../../EXPERIMENTS.md).

## Inspect and verify the results

Run the commands from this study directory. The first command uses the Python standard library and this directory alone. The second also checks the scorer, native adapter, database descriptors, question families, working groups, packet IDs, gold answer sets and solver-packet hashes against the surrounding public release.

```sh
python3 -B verify.py
python3 -B verify.py --release ../..
```

[summary.json](summary.json) reports the number of exact answers, denominator, pooled rate and range across repetitions for each model, language and input condition. Each histogram counts how many distinct questions were exact in 0, 1, … repetitions. The paired domain results count question-level gains and losses on the same 50 questions. [runs.json](runs.json) lists the corresponding session counts and submission flags. Each workload file stores one line per scheduled question position. The two workloads overlap on main questions and have separate identifiers for their runs.

| File | Use |
| --- | --- |
| [full667.jsonl.gz](full667.jsonl.gz), [matched50.jsonl.gz](matched50.jsonl.gz) | Join a run and canonical question ID to its packet ID, family, working group, exact score, execution status and returned answer-set fingerprint. |
| [queries.jsonl.gz](queries.jsonl.gz) | Look up the exact submitted SQL or Cypher string by its SHA-256 digest. Reused strings share a dictionary entry. |
| [items.json](items.json) | Match question IDs and expected answer-set fingerprints to the released [main questions](../../benchmark/items_final/gate) and [matched questions](../matched_domains/gold/selected_items.json). |
| [packet_sources.json](packet_sources.json) | Locate and hash-check the ten full-workload solver packets in [packets](packets) and four [matched textual packets](../codex_model_comparison/frozen/packets). |
| [first_writes.jsonl.gz](first_writes.jsonl.gz) | Inspect the reconstructed first query and independent native replays of both versions at 75 changed positions in three batches. The delivered query is available by digest from the query dictionary. |
| [verify.py](verify.py), [replay.py](replay.py) | Recompute rates from the archived fingerprints or rerun selected queries on the matching native engine. |

The exact score is one when the returned identity-normalized row set equals the gold set. The fingerprint uses the released [row-set scorer](../matched_domains/rescore.py) to normalize cells, including the field-specific meeting identifier rule, and SHA-256 over the sorted distinct rows in compact UTF-8 JSON. The empty set has its own fingerprint. A missing submission or failed execution has a null returned-set fingerprint and scores zero. In the full workload, the row-limit error label records the executor's 2,000-row check. This distinction preserves correct empty answers. Download and retain the compressed files byte-for-byte for the checksums.

The full-workload primary series includes delivered outputs. The two Claude Haiku SQL batches flagged in [runs.json](runs.json) contain a later file write. The sensitivity result in [summary.json](summary.json) omits both affected **whole repetitions**. For matched comparisons, pair the same model, language and repetition across the two value-domain conditions. Each paired input must have complete exposure for an input-controlled comparison. Also require both runs to conform to the first-output protocol when examining the output-controlled comparison. The delivered-response digest identifies the collected file. Two Codex Luna matched batches have 50 unanswered first-submission positions each. One delivered an invalid file and the other assembled a valid later file after its first output. Three Claude Haiku matched batches also have 50 unanswered positions each. The run table records the validity of the delivered file and compliance with the first-output rule separately. Full-workload native input-token counts may be null when the harness supplied no measurement under the recorded first-submission boundary.

## Repeat a native execution

The [database archive](../../sqlite) supplies the SQLite files. Decompress the compressed exports and put the five RAN databases in the directory named by `SQLITE_DIR`. The adapter checks their content hashes and opens them read-only. This example replays one saved SQL query and compares the returned answer-set fingerprint to the archived outcome.

```sh
python3 -B replay.py --release ../.. --study full667 \
  --run gpt-6.2-sol__sql__RAN1_A --id RAN1-full_chain-R1-2112940 \
  --sqlite-dir "$SQLITE_DIR"
```

For Cypher, restore the corresponding graph according to the [Neo4j restore guide](../codex_model_comparison/native_restore/README.md). Set `NEO4J_USER` and `NEO4J_PASSWORD` for your read-only connection and `RAN1_BOLT_URI` to the restored group's URI. The adapter checks the engine version and the working-group graph population. The same question can then be replayed in Cypher.

```sh
python3 -B replay.py --release ../.. --study full667 \
  --run gpt-6.2-sol__cypher__RAN1_A --id RAN1-full_chain-R1-2112940 \
  --bolt "RAN1=$RAN1_BOLT_URI"
```

Add `--first-write` on one of the three reconstructed batches to replay its first query version. The exact totals for the delivered and reconstructed batches coincide (20, 19 and 47). At 20 SQL positions the first query produced an execution error and the delivered query returned a different answer set from gold. Omit `--id` to replay a whole batch. A mixed-working-group matched Cypher batch needs a separate `--bolt RANn=URI` argument for each of the five groups. A zero exit status indicates that all inspected answer-set fingerprints matched. The replay reports any differing question IDs, including a query whose runtime crossed the execution limit.

## What changed the returned rows

The [SQL output-field diagnostic](IDENTIFIER_PROJECTION.md) reconstructs saved answer sets using the display fields named in the questions. The Cypher pack-origin diagnostic binds the pack named in each of 20 RAN3 questions. Verify the query edits and answer sets against the release, or supply a read-only RAN3 Bolt URI for native replay. The Figure 3 panel reads the per-repetition counts in the full-workload summary. It was rendered with Python 3.10.12 and Matplotlib 3.10.8.

```sh
python3 -B verify_pack_anchor.py --release ../..
python3 -B verify_pack_anchor.py --release ../.. --bolt "$RAN3_BOLT_URI"
python3 -B plot_repeats.py summary.json repeat_accuracy.pdf
```
