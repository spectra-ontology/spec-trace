# Exact full-candidate sensitivity

This census quantifies anchor selection across all **2,269,290 frozen candidate/cell memberships** in the existing source-faithful databases. Within the same 66 available cells and 200 known SQL control slots, uniformly choosing witness-eligible anchors gives **80.77% expected discrimination**, compared with **48.76%** for uniform selection from each complete pre-predicate candidate universe. The complete 95-cell inventory retains the other 29 cells with empty eligible populations and `NA` eligible-policy results.

| Frozen control subset | Weight | Uniform pre-predicate U | Uniform eligible E | E minus U |
|---|---|---:|---:|---:|
| All 200 slots | Control slots | 48.76% | 80.77% | +32.01 percentage points |
| All 200 slots | Equal cell | 49.19% | 80.82% | +31.63 percentage points |
| 113 direct eligibility controls | Control slots | 52.81% | 100.00% | +47.19 percentage points |
| 113 direct eligibility controls | Equal cell | 50.88% | 100.00% | +49.12 percentage points |
| 87 other controls | Control slots | 43.50% | 55.78% | +12.28 percentage points |
| 87 other controls | Equal cell | 40.13% | 47.33% | +7.20 percentage points |

The 113 direct controls check the properties used to define eligibility; their 100% E result follows from that construction, and its replay confirms the contract. The separate 87-control subset measures additional named operations. Its 49 nonempty cells have **16 positive, 17 zero and 16 negative** E-minus-U cell means. All exact cell contrasts, including decreases, are in [cell_mean_contrasts.csv](cell_mean_contrasts.csv). Subset-empty cells retain `NA` and are omitted from that subset's equal-cell mean; the 29 unavailable cells carry zero primary comparison weight.

These are exact expectations under two explicitly defined finite policies. Each cell chooses one anchor uniformly from U or E, and all controls in that cell share that anchor. The joint policy distributions assume independent choices between cells. The original deterministic hash selection remains a separate fixed comparison: both original arms replay as **162/200** for witness anchors and **93/200** for hash anchors. The census does not treat that hash as an observed random sample. Integer histograms and rational arithmetic preserve the complete policy PMFs, bounds and 5th/50th/95th quantiles in [run/analysis.json](run/analysis.json); those quantiles describe the policy distribution rather than sampling confidence intervals.

The expectation result permits individual anchor comparisons to favor U. The all-control support lower bound `min(E) - max(U)` is `-19/200` under control-slot weighting and `-437/3960` under equal-cell weighting; the other-control bounds are `-25/87` and `-64/147`. Thus the supported claim concerns finite-policy averages, rather than dominance for every anchor or performance on unseen model errors.

## Frozen evidence

The census retains the original candidate universes, eligibility predicates, source database bytes, SQL operation names and both original selections. An independent raw-relation interpreter computes complete normalized rowsets for each known operation. Before new SQL audit, the runner freezes all **814** representatives of its declared eligibility/signature classes. Full-rowset SQL checks cover those representatives and all original **132 task slots / 400 control slots**. The recorded audit passes **4,540 query slots** using **1,955 unique SQL executions** after exact WG/SQL caching, with zero mismatches, errors or timeouts. Representative validation checks the declared symbolic branches; it is separate from executing SQL on every candidate.

| File | Purpose |
|---|---|
| [INPUT.json](INPUT.json) | Fifteen minimal release-relative inputs, their byte hashes, and the bundled enumerator pin |
| [protocol.json](protocol.json), [control_catalog.json](control_catalog.json) | Frozen population, policies, direct/other control mapping, validation and reporting contract |
| [run_census.py](run_census.py), [symbolic.py](symbolic.py), [exact_stats.py](exact_stats.py) | Frozen runner, raw-relation interpreter and exact policy aggregation |
| [analyze_portable.py](analyze_portable.py) | Bundled byte-pinned original raw candidate/property enumerator |
| [implementation_manifest.json](implementation_manifest.json), [execution_approval.json](execution_approval.json) | Local hash-bound implementation and execution provenance checked by the runner |
| [prior_work.md](prior_work.md), [feasibility.md](feasibility.md), [design_review.json](design_review.json), [pre_execution_receipt.json](pre_execution_receipt.json) | Preserved author design and primary-source comparison records |
| [run/](run/) | Complete original candidate annotations, signature inventory/freeze, full SQL audit, validation, exact probabilities/PMFs, execution receipt and output hashes |
| [execution_side_effect_correction.json](execution_side_effect_correction.json) | Correction of the original receipt's filesystem wording: dynamic imports in the first run created regenerable bytecode caches; pinned scientific inputs stayed unchanged |
| [retained_temporary_databases.json](retained_temporary_databases.json) | Restore pins for the four optional uncompressed temporary databases, which are excluded from this package |
| [portable_replay.json](portable_replay.json) | Executed external-copy cold replay, actual CLI/runtime and comparisons with all original scientific outputs |
| [SHA256SUMS](SHA256SUMS) | All files in this bundle except the manifest itself |

This is a posthoc AUTHOR measurement of already known controls and paired results. Frozen design documents retain their pre-execution state, and historical receipts retain their original machine paths. The completed scientific outputs are in `run/`. This package preparation is separate from the earlier independent resource review and preserves that review unchanged. No new human judgments or model responses are represented. The [prior-work record](prior_work.md) attributes output-based SQL distinction and describes this census's fixed-source scope.

## Cold replay from an external temporary copy

Use the Python standard library with **SQLite 3.37.2**; the recorded reference runtime is Python 3.10.12. On the reference Linux installation, `/usr/bin/python3` provides this engine. An activated table-replay virtual environment may use another SQLite version, so check the interpreter selected below. The runner checks the engine and its included local approval/code/input hashes before executing. No server, model or API credential is required.

Run this block from the **release root**, selecting `python3` linked to SQLite 3.37.2. It copies this study outside the release and writes a fresh child beneath that copy. `--out` must be beneath the copied runner directory and outside `--release`; an output directory beneath the published release fails the runner's contract.

```sh
free -h
TASK_RELEASE=$(pwd -P)
TASK_COLD=$(mktemp -d "${TMPDIR:-/tmp}/spectra-full-census.XXXXXX")
cp -a studies/witness_selection_value/full_candidate_sensitivity "$TASK_COLD/study"
python3 -B -c "import sys, sqlite3; print(sys.version.split()[0], sqlite3.sqlite_version); assert sqlite3.sqlite_version == '3.37.2'"
python3 -B "$TASK_COLD/study/run_census.py" --help
python3 -B "$TASK_COLD/study/run_census.py" \
  --release "$TASK_RELEASE" \
  --enumerator "$TASK_COLD/study/analyze_portable.py" \
  --protocol "$TASK_COLD/study/protocol.json" \
  --approval "$TASK_COLD/study/execution_approval.json" \
  --out "$TASK_COLD/study/replay"
```

Omitting `--materialized-db-dir` makes this a cold replay: the runner decompresses the four pinned SQLite gzip inputs into `replay/.databases/` and checks their uncompressed hashes. RAN1 is read from its released plain SQLite file. The 15 inputs in `INPUT.json` are sufficient; the raw parser sources and a private project checkout are additional reconstruction workflows. Keep `-B` on the command to suppress import bytecode caches.

Expected output is a `complete` receipt, all 95/66/29 cell statuses, validation `passed`, 2,269,290 recomputed memberships, the original 132/400 replay and the complete exact analysis. Compare `replay/analysis.json`, candidate annotations and SQL/full-rowset validation with `run/`. Fresh timings, absolute paths, timestamps and gzip container metadata belong to the executing machine. `replay/output_sha256.json` binds that run's actual outputs. The included approval is an existing local provenance receipt, so replay uses the supplied file without contacting an approval service.

The runner uses one process, a 4 GiB address-space cap, immutable read-only SQLite connections and a 60-second query cap. The complete original run took about 126 seconds and used 421,560 KiB maximum RSS on its recorded host; fresh receipts report the executing machine's own resource use. Preserve partial outputs and the failure receipt if any validation fails.

Project-authored files follow the release's [CC BY 4.0 license](LICENSE). Cite the SPECTRA paper and the authors identified in the release's `CITATION.cff`; the included source-work comparison retains the prior methods' attribution.
