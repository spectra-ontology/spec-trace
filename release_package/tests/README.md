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
