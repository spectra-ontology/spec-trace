# Semantic-witness selection comparison

Witness selection exposes **162 of 200 named SQL mistakes**, compared with **93 of the same 200 controls** for anchors chosen by the same fixed hash rule before the final witness filters. Both arms contain the same 66 WG/stratum tasks, task families and operator-control names. The complete reference answers agree with separately derived Python sets in all 132 executions. All 400 control executions succeed.

| Fixed control group | Controls per arm | Witness anchors | Hash baseline |
|---|---:|---:|---:|
| All existing controls | 200 | 162 (81.0%) | 93 (46.5%) |
| Controls required by each witness predicate | 113 | 113 | 56 |
| Other existing controls | 87 | 49 | 37 |

The paired outcomes are 92 controls distinguished by both selections, 70 by the witness selection alone, one by the baseline alone, and 37 by neither. The baseline-only case is the release-blind membership control for the RAN4 general conjunction cell; its complete inputs and outputs remain in the results. The sum of distinct wrong-output classes across labelled tasks is 161 versus 79. Witness tasks use 65 distinct `(WG, family, anchor)` combinations and 198 distinct anchor/control combinations; baseline tasks use 66 and 200. Repetitions remain in the fixed paired denominator. Eighteen pairs share the same anchor.

The comparison retains the original enumerator's actual cohorts, pack membership and typed identities. Document-pair candidates share a typed section; section-pair candidates co-occur on a member. The baseline removes the final witness predicates within those candidate universes. All 95 original cells remain recorded, including 29 unavailable cells and all 15 unavailable maximum-release cells. The 66 paired cells are the original available cells. Required-control results validate their declared witness properties; the other 87 controls provide a separate comparison of additional mistake coverage. These measurements describe semantic sensitivity to the named controls on this fixed cohort and hash rule.

The [protocol](protocol.json), [registration receipt](protocol_freeze.json), [complete selections](measurement/selection.json), [SQL and full output sets](measurement/execution.json), [summary](measurement/summary.json) and [analysis](analysis.json) preserve the design and results. Five `measurement/candidate_universe_*.jsonl.gz` files contain every original pre-predicate candidate call: 2,269,290 candidate/cell memberships across all 95 cells. The [selection receipt](measurement/selection_freeze.json) freezes all five universes and both complete anchor selections before reference or control execution. [Final hashes](measurement/freeze.json) bind the measured outputs. Original predicate fields retain the original enumerator's short-circuit semantics; actual control behaviour is recorded in `execution.json`.

The first preparation attempt encountered a meeting identifier with a missing descriptive metadata row. [Version 1](failed_preparation_v1/) preserves its code, protocol, registration and pre-measurement failure receipt. Its [archive references](failed_preparation_v1/candidate_archive_references.json) record the original compressed hashes and verified byte-equivalence to the five current archives, sharing their identical uncompressed contents in the public package. Complete version-1 archive bytes remain preserved in the internal registration record. Version 2 retains that exact cohort and supplies a question-label fallback in a local rendering view. Candidate identities, hash rankings, gold, database bytes and SQL templates are preserved. The amendment was registered with zero reference or control executions.

The [independent checker](independent/check.py) imports neither the measurement builder nor its gold functions. It reconstructs all candidate multisets and hash minima from raw relations, checks paired SQL structures, derives reference and control semantics independently, and replays all 132 references and 400 controls. Its [receipt](independent/receipt.json) records **2,530 passing checks and zero failures**, including execution with RAN1 read from its released plain-file path. Each arm has 174 controls with independently derived complete Python rowsets and 26 ungrouped aggregation controls checked against their relationally admissible code/count values and exact stored SQLite outputs. The recorded engine condition is Python 3.10.12 with SQLite 3.37.2. The study obtains zero fresh model responses.

Output-based discrimination follows established semantic evaluation work. [Zhong, Yu and Klein (EMNLP 2020)](https://aclanthology.org/2020.emnlp-main.29/) select small suites of generated databases to distinguish altered SQL queries. This study holds the actual released databases and existing controls fixed and measures anchor selection; the [primary-source comparison](prior_work_review.json) records that relationship and the reading scope.

Run the measurement from the release root with the Python standard library and SQLite 3.37.2. The script reads the existing `sqlite/` exports, expands compressed partitions temporarily, checks input hashes, opens immutable read-only connections and writes only the new output directory. The [release guide](../../README.md) describes the database exports and restoration paths.

```sh
free -h
python3 -c "import sqlite3; print(sqlite3.sqlite_version)"
python3 -B studies/witness_selection_value/measure.py \
  --release . --output work/witness_selection_measurement
```

Use a new output directory. The default protocol is beside `measure.py`; the original builder and its pinned inputs are read from `studies/semantic_witnesses` beneath `--release`. The packaged script and registered protocol retain their measured bytes and digests. Explicit path arguments select the public layout. Fresh replay receipts record their own timings, compression metadata and file hashes; selected anchors, SQL and complete normalized rowsets are the reproducibility targets.

For the independent check, first prepare the execution databases with the existing [semantic-witness guide](../semantic_witnesses/README.md). RAN1 is read directly from the release, while the four compressed partitions are restored into the work directory:

```sh
free -h
python3 -B studies/semantic_witnesses/independent_witness_validation.py \
  --study studies/semantic_witnesses --release . \
  --database-directory work/semantic_databases \
  --output work/semantic_independent.json
python3 -B studies/witness_selection_value/independent/check.py \
  --experiment studies/witness_selection_value --release . \
  --database-directory work/semantic_databases \
  --out work/witness_selection_independent.json
```

The independent checker writes the specified new receipt and checks the existing frozen study. The [portable replay receipt](portable_replay.json) records the executed public measurement command and its agreement with the frozen selections and outputs.

## Exact full-candidate policy census

The [full-candidate census](full_candidate_sensitivity/README.md) evaluates all 2,269,290 frozen candidate/cell memberships and preserves both original anchor arms. For the same 200 known controls across 66 available cells, uniform witness-eligible anchors have 80.77% expected discrimination, compared with 48.76% for uniform anchors from each pre-predicate universe. Equal-cell weighting gives 80.82% and 49.19%. The original deterministic 162/200 versus 93/200 comparison remains separately recorded.

The 113 direct controls confirm the eligibility properties by construction. Among the 87 other known controls, the control-slot expectation increases from 43.50% to 55.78%; equal-cell means over the 49 nonempty cells increase from 40.13% to 47.33%. Their exact cell contrasts include 16 positive, 17 zero and 16 negative means. The complete finite-policy distributions preserve overlapping supports, so the result concerns average discrimination under the stated policies rather than every-anchor dominance. All 29 unavailable cells remain `NA` for eligible selection.

Follow the [external temporary-copy command](full_candidate_sensitivity/README.md#cold-replay-from-an-external-temporary-copy) with SQLite 3.37.2. The runner reads the 15 pinned release inputs and the included enumerator and writes only a fresh child of the external copied bundle. The shipped `run/` preserves all candidate annotations, exact fractions/PMFs and complete SQL audit.
