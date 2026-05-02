---
name: Bug — verify_release.py failure or release-package inconsistency
about: Report a reproducibility-script failure, a SHACL-conformance regression, or a documentation/data mismatch
title: "[BUG] <one-line summary>"
labels: bug
assignees: ''
---

## What failed?

- [ ] `tests/verify_release.py` reported a non-PASS check
- [ ] SHACL validation against `shapes/spectra-core.shacl.ttl` produced violations on a release artifact
- [ ] A number in the paper does not match `validation/*.json`
- [ ] A file referenced in `validation/validation_manifest.md` is missing
- [ ] An example query (Cypher / SPARQL) does not return the documented row

## Reproduction steps

```bash
# Exact commands you ran:

```

## Expected vs. observed

**Expected** (from paper / `ARTIFACT.md` / `validation_manifest.md`):

**Observed** (from your run):

## Environment

- OS:
- Python version:
- `rdflib` version:
- `pyshacl` version:
- Neo4j version (if applicable):

## Attached evidence

<!-- Paste the relevant section of stdout/stderr, or attach the failing JSON/TTL fragment. -->
