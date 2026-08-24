# SPECTRA Artifact Reproducibility Checklist

This is a reviewer-friendly checklist to verify the SPECTRA artifact in
about ten minutes, on a vanilla Python environment, without access to
internal 3GPP corpora.

## Required tools

```bash
pip install rdflib pyshacl
# Optional: Protégé (open ontology/spectra.ttl), Neo4j (run cypher/)
```

## Fast path: one-shot verification (recommended)

```bash
python3 tests/verify_release.py
# Prints one [PASS]/[FAIL] line per check and ends with a summary of the form:
#   === Summary: <passed>/<total> checks passed ===
# Exit code 0 only if every executed check passes. On a full checkout
# (Zenodo body-text TTLs downloaded into kg/per_wg/) the verifier runs
# 48 checks; on a Git-only checkout the five per-WG body-text checks in
# section 8b print [SKIP] instead (they defer to the Zenodo deposit per
# the GitHub/Zenodo split) and drop out of the total.
```

This single command runs all eleven labelled check sections (1, 1b, 2, 2b,
3, 4, 5, 6, 7, 8, 8b: ontology triples, docs-copy byte-identity, SHACL
conformance on the instantiation snippet, SHACL conformance on the
metadata-only process-KG union, end-to-end SPARQL, SpectraCQ benchmark
counts and gold integrity, structural metrics, validation-manifest
references, synthetic-instantiation sanity, release directory inventory,
per-WG body-text and schema KGs) and returns
exit 0 only if every executed check passes. If you only have time for one
check, run this one.

The remainder of this document explains the same checks individually for
reviewers who want to inspect each step.

## Run order

### 1. Verify the ontology parses

```bash
python3 -c "import rdflib; g=rdflib.Graph(); g.parse('ontology/spectra.ttl', format='turtle'); print(f'Triples: {len(g)}')"
# Expected: Triples: 914
```

### 2. Reproduce the structural metrics in the paper

```bash
python3 tests/reproduce_structural_metrics.py
# Expected: every row prints ✓; exit code 0
# Reproduces paper Table 3 (Ontology structural metrics):
#   Classes 32 / OPs 53 / DPs 81 / Functional 20 / IFP 2 / Inverse pairs 15
#   Irreflexive 6 / Asymmetric 2 / subclass 15 / triples 914
```

### 3. Validate the SHACL shapes against the synthetic instantiation

```bash
pyshacl -s shapes/spectra-core.shacl.ttl examples/instantiation_snippet.ttl
# Expected: "Conforms: True"
```

### 4. Run the multi-hop traceability SPARQL on the end-to-end synthetic example

```bash
python3 tests/test_e2e_sparql.py
# Expected:
#   "Total: 933 triples"
#   "Result: {'tdocNumber': 'R1-2599998', ..., 'meetingNumber': 'RAN1#121'}"
#   "PASS"
```

### 5. Inspect the SpectraCQ v2.0 scored benchmark

```bash
python3 -c "
import json
with open('cqs/spectra_cq_v2.0/questions.json') as f:
    d = json.load(f)
m = d['metadata']
print(f'Released: {m[\"released_scored_cqs\"]} / Authored: {m[\"authored_cqs\"]} / Held out: {m[\"held_cqs\"]}')
print(f'By WG: {m[\"released_by_wg\"]}')
print(f'Gold PASS: {sum(1 for c in d[\"cqs\"] if c[\"gold\"][\"status\"]==\"PASS\")}')
"
# Expected:
#   Released: 624 / Authored: 654 / Held out: 30
#   By WG: {'RAN1': 142, 'RAN2': 128, 'RAN3': 123, 'RAN4': 117, 'RAN5': 114}
#   Gold PASS: 624
```

### 6. Inspect 21 representative queries

```bash
ls queries/cypher/  # 15 files
ls queries/sparql/  # 6 files
# All files non-empty; MULTI_HOP_traceability available in both formats.
```

### 7. Inspect validation evidence

```bash
ls validation/
# 12 JSON evidence files + cq_replay/ + chart_parser_fidelity_note.md
#   + validation_manifest.md
# Every paper number is mapped to its evidence file in validation_manifest.md.
# validation/cq_replay/ holds the benchmark reproducibility evidence:
# scratch-reload graph counts, per-WG load reports, 624/624 gold replay
# results, and 142/142 SPARQL row-count parity on the released RAN1 CQs.
```

## Reviewer trust path

The four artifacts above (TTL parse, structural metrics, SHACL conformance,
e2e SPARQL) reproduce the *publicly verifiable* part of the paper's
quantitative claims (the ontology structural-metrics table, the synthetic
multi-hop traceability example, and the SpectraCQ v2.0 benchmark contents).

The remaining design-phase numbers (RAN1 instance counts, cross-WG schema
diff, cross-WG query counts, OOPS scan output) are pre-computed snapshots
shipped under `validation/*.json`; each has an entry in
`validation/validation_manifest.md` mapping the paper claim to its
JSON field. These come from the internal build pipeline and are shipped
as evidence rather than re-derived here.

The benchmark gold sets, by contrast, *are* re-derivable from the release
alone: load the released per-WG TTLs into a scratch Neo4j and re-run the
624 reference Cypher queries. `validation/cq_replay/` records exactly such
a reload — graph counts, per-WG load reports, a 624/624 gold match, and
142/142 SPARQL row-count parity covering all released RAN1 CQs.

## Estimated time

- Steps 1-4: ~3 minutes (one-time `pip install` aside)
- Steps 5-7: ~2 minutes
- Reading `validation_manifest.md` to spot-check 5 numbers: ~5 minutes

Total: ~10 minutes.
