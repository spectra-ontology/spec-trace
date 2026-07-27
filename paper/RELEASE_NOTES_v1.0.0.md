# SPECTRA v1.0.0 — initial public release of the SPECTRA ontology

**Release date**: 2026-04-27
**License**: CC-BY 4.0
**Persistent IRI**: https://w3id.org/spectra
**DOI**: 10.5281/zenodo.20034872 (this version) · 10.5281/zenodo.20034871 (concept, resolves to the newest deposit)

## What this release contains

- **`ontology/spectra.ttl`** — SPECTRA OWL 2 ontology (Turtle), 26 classes, 53 object properties, 81 data properties.
- **`docs/spectra.html`** — auto-generated human-readable documentation (PyLODE).
- **`shapes/spectra-core.shacl.ttl`** — minimal SHACL shapes covering core cardinality and range constraints (validatable with pySHACL or TopBraid).
- **`cqs/representative_cqs.md`** — curated subset of the 137 competency questions used to design and validate SPECTRA.
- **`queries/cypher/`** and **`queries/sparql/`** — executable Cypher and SPARQL translations of the representative CQs.
- **`examples/instantiation_snippet.ttl`** — small synthetic instantiation showing how the spine (Tdoc → Resolution → CR → Section → Spec) is expressed.
- **`CITATION.cff`**, **`codemeta.json`**, **`LICENSE`** — citation, software metadata, and license.

## Highlights

- **5-phase cumulative competency-question validation**: 25 + 34 + 45 + 15 + 18 = 137 distinct CQs, re-executed at each phase transition; three quality-assurance cases resolved before release.
- **Cross-WG schema stability**: the RAN1-designed schema covers RAN2–RAN5 with **0 additional classes, 1 additional object property, 2 genuinely new data properties** beyond the released SPECTRA elements.
- **OOPS! validation**: no critical pitfalls; two Important and two Minor findings, all justified by deliberate FOAF reuse and disjointness-parsimony decisions.
- **Vocabulary reuse**: Dublin Core (`dc:title`, `dc:description`, `dc:creator`, `dc:date`) and FOAF (`foaf:Person`, `foaf:Organization`).

## Non-redistributed components

The full 137-CQ suite, the operational parsing/loading pipeline, and the per-WG instantiated knowledge graphs are retained as internal validation evidence rather than redistributed; the underlying 3GPP Technical Documents are subject to 3GPP copyright. The original TDocs remain publicly accessible via the 3GPP portal (https://www.3gpp.org).

## Citation

See `CITATION.cff` for machine-readable citation metadata. The manuscript associated with this release:

> Choi, S., Lee, J. (2026). SPECTRA: A Traceability Ontology for the 3GPP RAN Standardization Process. Manuscript.
