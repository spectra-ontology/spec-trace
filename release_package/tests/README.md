# SPECTRA reproducibility tests

Scripts that any third party can run to verify the publicly-released
numbers. The first three need only `rdflib` + `pyshacl`; the benchmark
verifier's `--full` mode additionally needs a scratch Neo4j instance.

- **`reproduce_structural_metrics.py`** — recomputes the metrics in
  `validation/structural_metrics.json` (and §6.2 / Table 4 of the paper)
  directly from `ontology/spectra.ttl`.
- **`test_e2e_sparql.py`** — loads the synthetic end-to-end example,
  runs the multi-hop traceability SPARQL query, and verifies the
  expected return row (`R1-2599998 / RAN1#121`).
- **`verify_release.py`** — file-level release gate. Takes no arguments,
  writes nothing, and prints one line per check plus a summary. Checks
  that need the body-text deposit report `[SKIP]` in a Git-only
  checkout.
- **`verify_benchmark.py`** — benchmark gate, described below.
- **`reproduce_scenario_counts.py`**: recount of the cross-WG query counts on the released graphs, described below.

Run:
```bash
pip install rdflib pyshacl
python3 tests/reproduce_structural_metrics.py
python3 tests/test_e2e_sparql.py
python3 tests/verify_release.py
pyshacl -s shapes/spectra-core.shacl.ttl examples/instantiation_snippet.ttl
```

All four should exit with status 0.

## `verify_benchmark.py`

Two modes, run from the repository root:

```bash
# No database required; this is also what a bare invocation runs.
python3 release_package/tests/verify_benchmark.py --quick

# Reloads the released graphs and re-derives every published answer set.
python3 release_package/tests/verify_benchmark.py --full --wg all \
    --bolt bolt://HOST:PORT --user neo4j --password PASSWORD
```

`--quick` runs 52 checks: the 48 file-level checks of `verify_release.py`
plus four benchmark-specific ones — the Croissant sha256 of
`questions.json`, and the file counts of `cqs/spectra_cq_v2.0/cypher/`
(624), `sparql/` (142) and `gold/` (5). Of those 52, 47 apply to a
Git-only checkout; the remaining five need the body-text deposit from
Zenodo (see `kg/per_wg/README.md`). A Git-only run therefore ends in
`=== QUICK: 47/47 checks passed ===`.

`--full` loads `kg/per_wg/RAN{1..5}-body.ttl` into the target store and
re-derives all 624 published answer sets, so it needs the Zenodo deposit
as well as a database. **`--full` wipes the database it connects to.**
For that reason `--bolt` and `--password` have no defaults: point the run
at a scratch instance, never at a store whose contents matter. `--wg`
restricts the run to one Working Group.

Machine-readable output goes to the directory named by `--out`
(`verifier_output/` under the current working directory by default):
`verifier_modes.json` for either mode, and for `--full` also
`verifier_full_replay_detail.json` plus the loader's per-WG reports.
Nothing inside `release_package/` is written by a run.

Drift between the paper's figures and the released files surfaces as a
failed check.

## `reproduce_scenario_counts.py`

Recounts, on the five body-text graphs of the deposit, the 18 cross-WG
query counts of `validation/cross_wg_use_evidence.json` (measured on the
deployed per-WG KGs) and compares the result with
`validation/released_graph_scenario_counts.json`. Standard library only, no
database. Put the deposit's RAN1-body.ttl to RAN5-body.ttl files in
`kg/per_wg/` (see `kg/per_wg/README.md`), or name their directory:

```bash
python3 tests/reproduce_scenario_counts.py
python3 tests/reproduce_scenario_counts.py --ttl-dir /path/to/deposit
```

Exit status 0 when every field agrees with the shipped JSON, 1 on a
difference, 2 when the graph files are missing. In the shipped JSON,
17 of the 18 counts are the same on both graphs; `compared_with_deployed`
lists all 18, and the one that differs is the RAN3 count of change
requests on TS 38.300 (270 deployed, 1,249 released).
