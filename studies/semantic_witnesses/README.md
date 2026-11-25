# Released-record semantic witness study

The released records instantiate **66 prespecified witness cells across all six analytical operators and a conjunction-to-aggregation composition**. Each selected task has a complete Python set answer and an independently expressed reference SQL result; all 66 pairs agree. Executing the 113 controls required by the witness predicates produces 113 outputs differing from their corresponding gold sets. The workload supplies concrete data that distinguish grouping omission, raw row counts, set-operation substitution, incomplete conjunction, dropped ties, recorded-link presence versus absence, and selected release-blind membership errors.

The [protocol](protocol.json) was recorded before pool enumeration, anchor selection and measurement SQL execution. Nineteen semantic strata across five WGs define 95 planned cells. Every eligible candidate identity and its witness properties are retained in `measurement/pool_*.jsonl.gz`. A fixed hash rule selects one anchor from each available cell. The 66 tasks use 65 distinct family/anchor combinations; repeated anchors remain recorded. The [selection and gold](measurement/selection_and_gold.json), [execution receipt](measurement/execution.json) and [freeze manifest](measurement/freeze.json) preserve the complete outputs and input bindings. The earlier frozen 30-item pilot and its model scores are separate evidence. The original witness census obtains zero fresh model responses. A separately frozen [first-query follow-up](first_queries/README.md) supplies one new Codex session with all 66 questions, schema and complete categorical domains; its first SQL responses match 66/66 full gold sets under SQLite 3.37.2, with zero execution feedback and an unrecorded exact provider model identifier.

The availability census is as follows. Every zero denotes an unavailable planned cell, which remains in the result.

| Prespecified stratum | RAN1 | RAN2 | RAN3 | RAN4 | RAN5 |
|---|---:|---:|---:|---:|---:|
| Pack, multiple codes | 11 | 9 | 4 | 11 | 14 |
| Pack, duplicate count witness | 273 | 508 | 2 | 1 | 0 |
| Pack, both properties | 6 | 7 | 0 | 0 | 0 |
| Resolution meeting, multiple codes | 61 | 61 | 56 | 61 | 38 |
| Resolution meeting, duplicate count witness | 58 | 55 | 18 | 13 | 1 |
| Resolution meeting, both properties | 58 | 55 | 18 | 13 | 1 |
| Intersection with three nonempty set regions | 39 | 342 | 705 | 407 | 1,020 |
| Intersection with release-sensitive membership | 0 | 0 | 0 | 13 | 0 |
| Directed difference with three nonempty set regions | 78 | 684 | 1,410 | 814 | 2,040 |
| Directed difference with release-sensitive membership | 0 | 0 | 0 | 26 | 0 |
| Conjunction with both and each single-link region | 143 | 290 | 566 | 1,008 | 3,744 |
| Conjunction with release-sensitive membership | 0 | 14 | 8 | 367 | 0 |
| Maximum with varying positive counts | 268 | 458 | 318 | 834 | 1,010 |
| Maximum with actual ties and varying positive counts | 54 | 96 | 66 | 334 | 252 |
| Maximum whose result changes after release collapse | 0 | 0 | 0 | 0 | 0 |
| Maximum whose winner set changes after release collapse | 0 | 0 | 0 | 0 | 0 |
| Tied maximum whose result changes after release collapse | 0 | 0 | 0 | 0 | 0 |
| Mixed recorded-link absence and presence | 70 | 334 | 181 | 438 | 691 |
| Conjunction followed by disposition aggregation | 140 | 290 | 566 | 923 | 3,738 |

These counts describe distinct anchors within each stratum. Strata overlap by design. The complete [machine-readable census](candidate_pool_counts.tsv) and per-cell failed-predicate counts preserve their respective candidate universes.

Three examples illustrate the measured distinctions. For RAN1 pack `RP-191942`, the correct histogram is `(agreed,9)` and `(conditionally_agreed,1)`; omitting grouping returns `(agreed,10)`, while raw row counting returns `(agreed,12)` and `(conditionally_agreed,1)`. For RAN1 pack `RP-253018`, `R1-2509603` and `R1-2509604` both have four typed sections; `LIMIT 1` drops one actual winner. For RAN2 pack `RP-221756`, requiring `38.306/Rel-17/4.2.19` and `38.306/Rel-17/4.2.9a` returns `R2-2206559`; release-blind matching additionally admits `R2-2206558`.

All **200 executed operator-error controls** complete successfully: 188 in the frozen initial receipt and 12 in a [supplementary receipt](supplementary_omitted_controls.json). Of these, 162 return a different set and 38 retain the gold set on their selected data. The required 113 controls were selected through explicit counterexample predicates; their successful distinction validates those declared properties. The other 87 controls quantify which additional mistakes the same anchors expose. [Control reconciliation](semantic_control_reconciliation.json) separates these groups and records zero executed reference-identical controls. The builder defines six correctly matching `INTERSECT` controls and explicitly excludes them from intersection-task execution. It also defines 12 directed-difference single-side controls that the initial execution subset omits; `execute_defined_controls.py` executes those controls with the frozen anchors and gold, preserving the initial receipt.

| Task family | Tasks | Required controls distinguished | All controls distinguished |
|---|---:|---:|---:|
| Disposition histograms, explicit pack or meeting cohort | 26 | 33/33 | 42/52 |
| Typed intersection | 6 | 16/16 | 25/30 |
| Directed typed difference | 6 | 16/16 | 31/36 |
| Typed conjunction | 8 | 18/18 | 27/32 |
| Maximum distinct-section footprint | 10 | 10/10 | 17/30 |
| Recorded-link absence | 5 | 10/10 | 10/10 |
| Conjunction followed by disposition aggregation | 5 | 10/10 | 10/10 |

Release identity is exposed by five selected membership tasks: intersection and directed difference in RAN4, and conjunction in RAN2, RAN3 and RAN4. All 15 maximum-release cells remain unavailable under the prespecified requirements. The data support these operation-specific observations; a per-document maximum claim uses its corresponding count and tie witnesses. There are 29 unavailable cells overall, with their full identities and failed predicates retained in the selection receipt.

Execution uses Python 3.10.12 and SQLite 3.37.2, read-only immutable connections, a 60-second query cap, 16 MiB SQLite caches and a 2 GiB process address-space cap. The sequential initial run takes 8.92 seconds with peak RSS 276,028 KiB. All five released source hashes and execution-database hashes match their original pinned values before and after both initial and supplementary runs. Actual references and controls produce zero SQL errors or timeouts. A separate [independent checker](independent_witness_validation.py), importing neither the builder nor its gold functions, reconstructs all 95 eligible candidate identity sets, hash-min selections and all 66 gold sets directly from raw relations. Its [receipt](independent_witness_validation.json) passes 671 checks, including every original and supplementary SQL output. The original frozen receipt retains the independent-validation status recorded at its creation; this later check supplies the completed validation evidence.

The [primary-work comparison](prior_work_review.json) connects this design to [SemBench](https://doi.org/10.14778/3811243.3811249), [Bench-U](https://www.vldb.org/pvldb/vol19/p2398-deng.pdf) and [distilled SQL test suites](https://aclanthology.org/2020.emnlp-main.29.pdf). Operator variation, composition and query mutation retain that attribution. This study contributes measured semantic coverage and replayable witnesses for this released source-bound process resource. Its evidence concerns the named query distinctions and their actual data support; model accuracy and engineer-question distributions have their own study designs.

Run from the package root with Python 3.10 and SQLite 3.37.2 for the recorded engine condition. These commands use the Python standard library. Check `python3 -c "import sqlite3; print(sqlite3.sqlite_version)"` before execution. First reconstruct the pools, gold and all 266 executed SQL outputs independently; this also decompresses the four compressed databases into the new work directory:

```sh
free -h
mkdir -p work
python3 -B studies/semantic_witnesses/independent_witness_validation.py \
  --study studies/semantic_witnesses --release . \
  --database-directory work/semantic_databases \
  --output work/semantic_independent.json
```

Successful execution reports 671 passing checks and zero failures. The published checker and receipt retain their original implementation hash. Explicit path arguments select this public layout. The 66 reference executions and 200 operator-error executions are separate from the 30-item first-response model pilot.

Replay into a new output directory from the package root:

```sh
free -h
python3 -B studies/semantic_witnesses/build_semantic_witnesses.py \
  --release . \
  --database-directory work/semantic_databases \
  --original-pin studies/semantic_witnesses/original_pilot_input.json \
  --output work/semantic_measurement
```

The release directory supplies RAN1 directly. The independent check prepares the decompressed RAN2 through RAN5 databases; all execution databases must match the source pins. `database_inputs.json` is a portable projection of the five original source/database hash records. The historical freeze binds the exact earlier input file, supplied as `original_pilot_input.json`; the builder bytes and supplemental executor bytes also match their respective recorded implementation hashes. This standalone measurement uses the original pinned database exports and preserves every selected anchor and outcome. Its compressed candidate pools are independently readable with standard Python `gzip` and `json`. Fresh replay receipts carry their own timings, compression metadata and file hashes; exact candidate identities, hash-selected anchors and row sets are the deterministic comparison targets.

Replay the supplementary controls against a pinned measurement directory:

```sh
free -h
python3 -B studies/semantic_witnesses/execute_defined_controls.py \
  --measurement studies/semantic_witnesses/measurement \
  --release . \
  --database-directory work/semantic_databases \
  --output work/semantic_supplement.json
```

The supplemental receipt calls its own execution script hash `builder_sha256`. That field identifies `execute_defined_controls.py`; the initial freeze separately identifies `build_semantic_witnesses.py`. Original receipts and source observations are preserved.
