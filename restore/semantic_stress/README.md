# Stored-SQL relational contract stress

This offline check makes the benchmark's disposition contract observable under synthetic counterexamples. It adds separately marked disposition rows to disposable in-memory database copies and re-executes stored SQL. Both independently written reference SQL directions retain the original gold, while reference queries with the relevant guard removed return additional rows. This distinguishes snapshot result correctness from robustness to these particular counterexamples.

`original/` preserves the experiment and reference-SQL scripts byte for byte. `reproduce.py` adapts filesystem paths to this release in a disposable workspace. It uses the Python standard library, makes no model or network calls, and reads released databases, benchmark items and stored responses without modifying them. The output includes hashes of released inputs and the logical-to-release path mapping. Dependencies already used by the release suffice; this check itself requires SQLite 3.37.2, as bundled with the `/usr/bin/python3` used for the reference run.

From the release root, run the fast default pilot:

```sh
/usr/bin/python3 -B restore/semantic_stress/reproduce.py \
  --out /tmp/spectra-semantic-pilot.json
```

The pilot runs the fixed RAN1 full-chain anchor and Opus SQL run A. In the checked release it took about 0.1 seconds and retained gold under all three perturbations. Both reference directions and all three removed-predicate controls passed. The optional full run executes the fixed 35-anchor design with the original 60-second query cap:

```sh
/usr/bin/python3 -B restore/semantic_stress/reproduce.py --full \
  --out /tmp/spectra-semantic-full.json
```

The reference full run took 1,183.756 seconds. Runtime and baseline timeout eligibility can vary with machine load; outputs retain these measurements separately from row changes. Result paths must be outside the release directory. `--release PATH` and `--work-parent PATH` support other read-only release locations and disposable-workspace placement.

## Fixed design and checks

The exploratory sample was fixed before full-run outcome inspection: choose the minimum SHA-256 of `semantic-scope-contract-stress|itemId` within each working-group/family pair. This selects 35 anchors across five WGs and seven families. Twenty-five anchors depend on disposition eligibility; ten pack-lookup anchors are negative controls and have separate summaries. Thirteen stored conditions comprise ten Opus SQL runs and three Codex SQL information conditions. Each stored query enters the stress comparison only when its actual baseline execution equals the original gold on the specified engine.

Each perturbation is applied separately and rolled back before the next. Synthetic identifiers begin with `synthetic:scope-stress/`, and the inserted evidence path is `synthetic:relational-contract-only`. Source records, gold, questions and stored responses stay unchanged. The full reference file records 74 unchanged input hashes, 280 gold-preserving directional-reference executions and 75 effective removed-predicate controls.

| Scenario | Inserted code / status / scope | Contract interpretation |
|---|---|---|
| `status_only` | ambiguous / pending / whole_target | Explicitly outside the builder contract; relational guard diagnostic |
| `scope_only` | partially_agreed / source_verified / subdocument | Builder-compatible tuple type |
| `combined` | ambiguous / pending / undetermined | Builder-compatible tuple type |

Direct inspection of the builder established `ambiguous → pending/undetermined`, so the combined scenario was revised before the full run, independently of stored-query outcomes. Actual source-verified subdocument counts in RAN1–RAN5 are 1,339, 218, 24, 11 and 15. All observed pending rows have undetermined scope. A synthetic `source_verified` literal denotes a relational test value: these inserted rows are synthetic counterexamples, rather than source-verified historical records or a claim of full SHACL conformity. The three scenarios therefore test three explicit contracts rather than an unconstrained 2×2 population design.

## Reference results

`reference_full.json` preserves the full original measurement. Among 325 selected active query instances (25 anchors × 13 conditions), 283 were baseline exact. Forty had different baseline rows and two reached the baseline time cap; every exclusion has its reason recorded. The 40 comprise 25 Codex schema-only instances and five each from Opus runs A, C and E. The two caps occur in Opus runs B and D.

| Scenario | Eligible active instances | Retained original gold | Different row sets | Stress errors / timeouts | Active execution seconds |
|---|---:|---:|---:|---:|---:|
| Status-only diagnostic | 283 | 283 | 0 | 0 / 0 | 262.219 |
| Scope-only | 283 | 273 | 10 | 0 / 0 | 259.655 |
| Combined | 283 | 283 | 0 | 0 / 0 | 260.361 |

All ten row changes occur in Opus run D, in the five disposition-dependent families of RAN1 and RAN2. They add rows while retaining every original gold row. Opus run D has 24 eligible active instances and retains gold on 14 under scope-only stress. Codex schema-only has no eligible active instance, so it has no active robustness result. The separately reported 130 negative-control instances retain gold in each scenario.

These counterexamples show that particular snapshot-correct queries can include additional results after a scope change. Passing a finite perturbation set establishes gold retention under those perturbations; it does not prove semantic equivalence or literal inclusion of particular predicates. The fixed exploratory sample diagnoses stored-query behavior and does not estimate a corpus-wide failure rate, source-record truth, or a new historical benchmark score.

## Provenance and output fields

- `manifest.json`: hashes of the two unmodified source files and full reference JSON.
- `reference_full.json`: per-item reference checks and injected rows, per-query baseline and stress results, exclusions, runtime, environment and original-input hashes.
- `summaryDispositionFamilies`: the active 25-anchor results, separated from `summaryNegativeControls`.
- `releaseReproduction`: added by the adapter, with released-input hashes, unchanged-input verification and the path mapping used by the run.

Reference SHA-256: experiment `822f327a526aef3e4a0f32e71775614df0b1fa2a59e872da17d91d1f939d6f4a`; reference SQL `1880441e022d7895fbc6f67bcce44427e44fd50c35715dd09518229add5c296e`; full result `60332a41b131c292a884c9e130b401df56d81c45c2660ad14a691f4024c05815`.
