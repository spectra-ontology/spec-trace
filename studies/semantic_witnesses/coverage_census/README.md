# Source-relation coverage census

This study reconstructs every identity, property and witness predicate for 2,269,290 candidates from the released membership, disposition and typed-section relations. All rows match the frozen candidate archives: 95 planned cells, 66 supported and 29 unavailable in this snapshot.

## Replay

Run from the release root with Python's standard library and SQLite 3.37.2:

```sh
/usr/bin/python3 -B studies/semantic_witnesses/coverage_census/analyze.py --release . --out work/coverage_census
```

The script reads the 26 files listed in `inputs.json`, materializes four gzip databases inside the output directory, opens databases read-only, checks input hashes before and after reading, and removes its temporary databases. Existing decompressed copies can be supplied with `--materialized-db-dir`. A cold execution uses about 125 MB of compressed inputs and took 39.45 seconds on the recorded machine. The execution receipt records the actual Python and SQLite versions.

`cells.csv` contains all 95 property/WG cells. `gate_counts.csv` gives marginal, prefix and first-failure counts for each declared gate. `cell_analysis.json` also records raw relation properties, complete joint predicate patterns, source-code locations and representative candidates. The [frozen protocols](../protocol.json) and [paired selection inputs](../../witness_selection_value/README.md) define the properties, candidate universes and original anchors.

## What the census explains

| Observation determining unavailable cells | Cells |
|---|---:|
| Per-document release projection preserves footprint cardinality | 15 |
| Release collisions have zero incidence within shared-typed pair candidates | 8 |
| Release-collision and three-region conjunction cohorts are disjoint | 2 |
| Multicode and duplicate pack cohorts are disjoint | 2 |
| Qualifying pack rows have zero duplicate excess | 2 |

The first observation covers all 39,901 linked documents. Of these, 341 carry sections from multiple releases: cardinality is preserved because a document's distinct full identities stay distinct after projecting `(spec,release,clause)` to `(spec,clause)`. SQLite permits projection collisions; this is a measured property of this materialization. Source-code locations explain a compatible construction mechanism under the recorded per-record spec/release resolution path.

Cross-document aliases coexist with this per-document property. Same-pack release-collision document pairs number 331, 1,255, 443, 5,858 and 8 in RAN1 to RAN5; after the pair universe's shared full-typed gate, the counts are 0, 0, 0, 13 and 0. RAN1/RAN5 conjunction candidates have 1,119/24 raw release collisions, with zero satisfying the joint three-region gate. The census therefore distinguishes source patterns, universe preconditions and final witness predicates.

## Interpretation and provenance

The counts characterize the fixed released snapshot and declared universe. Eligibility is exactly the conjunction of a property's protocol gates; it is a coverage measure for named distinctions. The study keeps all original anchors, reference SQL and controls fixed. The separate [first-query diagnostic](../first_queries/README.md) measures fresh SQL responses, and the [paired selection study](../../witness_selection_value/README.md) measures fixed-control detection.

[Zhong, Yu and Klein (EMNLP 2020)](https://aclanthology.org/2020.emnlp-main.29/) generates distinguishing databases and distills semantic test suites. This census uses that established distinction principle to explain which observed source relations support the declared distinctions on a source-faithful fixed database.

`execution_receipt.json` projects an actual root replay receipt, removing local execution directories and internal review-state metadata while preserving scientific measurements and input/code hashes. Its three scientific outputs byte-match the separate author replay. `SHA256SUMS` binds the files in this directory.
