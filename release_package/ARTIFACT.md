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
# Expected last line:
#   === Summary: 25/25 checks passed ===
```

This single command runs all nine check sections (ontology triples, SHACL
conformance on instantiation snippet, SHACL conformance on process-KG union,
end-to-end SPARQL, SpectraCQ counts/verdict, structural metrics, manifest
references, anonymization scope, release directory inventory) and returns
exit 0 only if every check passes. If you only have time for one check,
run this one.

The remainder of this document explains the same checks individually for
reviewers who want to inspect each step.

## Run order

### 1. Verify the ontology parses

```bash
python3 -c "import rdflib; g=rdflib.Graph(); g.parse('ontology/spectra.ttl', format='turtle'); print(f'Triples: {len(g)}')"
# Expected: Triples: 887
```

### 2. Reproduce the structural metrics in the paper

```bash
python3 tests/reproduce_structural_metrics.py
# Expected: every row prints ✓; exit code 0
# Reproduces paper Table 3 (Ontology structural metrics):
#   Classes 26 / OPs 53 / DPs 81 / Functional 20 / IFP 2 / Inverse pairs 15
#   Irreflexive 6 / Asymmetric 2 / subclass 15 / triples 887
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
#   "Total: 937 triples"
#   "Result: {'tdocNumber': 'R1-2599998', ..., 'meetingNumber': 'RAN1#121'}"
#   "PASS"
```

### 5. Inspect the SpectraCQ v1.0 dataset

```bash
python3 -c "
import json
with open('cqs/spectra_cq_v1.0/questions.json') as f:
    d = json.load(f)
print(f'CQs: {d[\"metadata\"][\"total_cqs\"]}')
print(f'Phases: {d[\"metadata\"][\"phases\"]}')
print(f'PASS: {sum(1 for c in d[\"cqs\"] if c[\"verdict\"]==\"PASS\")}')
"
# Expected:
#   CQs: 137
#   Phases: {'P1': 25, 'P2': 34, 'P3': 45, 'P4': 15, 'P5': 18}
#   PASS: 137
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
# 10 JSON files + validation_manifest.md
# Every paper number is mapped to its evidence file in validation_manifest.md
```

## Reviewer trust path

The four artifacts above (TTL parse, structural metrics, SHACL conformance,
e2e SPARQL) reproduce the *publicly verifiable* part of the paper's
quantitative claims (Table "Structural metrics", §6.2 OOPS, the synthetic
multi-hop traceability example, and SpectraCQ v1.0 contents).

The remaining numbers (RAN1 instance counts, cross-WG schema diff,
cross-WG query counts, OOPS scan output) are pre-computed snapshots
shipped under `validation/*.json`; each has an entry in
`validation/validation_manifest.md` mapping the paper claim to its
JSON field. These cannot be re-derived without access to the internal
3GPP-licensed knowledge graphs.

## Estimated time

- Steps 1-4: ~3 minutes (one-time `pip install` aside)
- Steps 5-7: ~2 minutes
- Reading `validation_manifest.md` to spot-check 5 numbers: ~5 minutes

Total: ~10 minutes.
