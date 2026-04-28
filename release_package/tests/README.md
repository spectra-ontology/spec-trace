# SPECTRA reproducibility tests

Two scripts that any third party can run with rdflib + pyshacl to verify
the publicly-released numbers in the paper:

- **`reproduce_structural_metrics.py`** — recomputes the metrics in
  `validation/structural_metrics.json` (and §6.2 / Table 4 of the paper)
  directly from `ontology/spectra.ttl`.
- **`test_e2e_sparql.py`** — loads the synthetic end-to-end example,
  runs the multi-hop traceability SPARQL query, and verifies the
  expected return row (`R1-2599998 / RAN1#121`).

Run:
```bash
pip install rdflib pyshacl
python3 tests/reproduce_structural_metrics.py
python3 tests/test_e2e_sparql.py
pyshacl -s shapes/spectra-core.shacl.ttl examples/instantiation_snippet.ttl
```

All three should exit with status 0.
