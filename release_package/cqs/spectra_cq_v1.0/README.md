# SpectraCQ v1.0 — 137 Competency Questions for the SPECTRA Ontology

This dataset packages the 137 competency questions (CQs) used to design and
validate the SPECTRA ontology, together with their executable Cypher
translations against a SPECTRA-conformant Neo4j knowledge graph.

## Why SpectraCQ matters as a standalone resource

Even apart from the SPECTRA ontology, SpectraCQ v1.0 is the largest
publicly released CQ corpus elicited from practicing 3GPP standardization
engineers, with each CQ paired with an executable Cypher specification and
a per-CQ pass/fail verdict on a real-scale instantiated KG. It is reusable
as: (i) a benchmark for ontology coverage and CQ-to-query translation
research; (ii) a reference set for natural-language-to-Cypher / NL2KG
research targeting telecom standardization; and (iii) a teaching resource
for telecom-domain knowledge engineering. SpectraCQ is independently
citable via `citation.bib` and licensed under CC-BY 4.0.

## Distribution

- `questions.json` — 137 CQ entries with English question text, phase
  (P1..P5), category, schema area (classes + relationship types
  exercised), and a pointer to the Cypher file.
- `cypher/P{phase}_{id}.cypher` — 137 executable Cypher files (one per
  CQ).
- `LICENSE` — CC-BY 4.0.
- `citation.bib` — BibTeX citation entry for this dataset.

## Anonymization

Company names in the original (internal) dataset are mapped to anonymized
handles (`CompanyA`, `CompanyB`, ..., `CompanyJ`) so the dataset stays
reusable as a CQ-to-query benchmark across organisations and venues. (The
ISWC 2026 Resources Track is single-anonymous: authors are named, reviewers
are anonymous; the placeholder mapping is therefore a portability choice,
not a venue requirement.) The placeholder-to-real mapping is intentionally
not published in v1.0.

## Phase distribution

| Phase | Domain                | CQs |
|-------|-----------------------|----:|
| P1    | TDoc metadata         | 25  |
| P2    | Meeting resolutions   | 34  |
| P3    | TS structure          | 45  |
| P4    | CR documents          | 15  |
| P5    | Technical Reports     | 18  |
| **Total** |                   | **137** |

## How to use

```bash
# Inspect questions
jq '.cqs[0]' questions.json

# Run a single CQ against a SPECTRA-conformant Neo4j (example: P1_CQ1-1)
cypher-shell -u neo4j -p <pass> < cypher/P1_CQ1-1.cypher
```

## Companion releases

- SPECTRA OWL ontology (this dataset's schema): https://w3id.org/spectra
- Paper: "SPECTRA: A Traceability Ontology for the 3GPP RAN Standardization
  Process" (under review at ISWC 2026 Resources Track).

## Citation

See `citation.bib`. To cite this dataset:

```
Choi, S., Lee, J., Ahn, J. (2026). SpectraCQ: 137 Competency Questions
for the SPECTRA Ontology (v1.0) [Data set]. Zenodo.
DOI: <to be assigned upon Zenodo mint>
```

## License

CC-BY 4.0. You are free to share and adapt; please cite.
