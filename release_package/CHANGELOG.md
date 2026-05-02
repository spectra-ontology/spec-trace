# Changelog

All notable changes to the SPECTRA release package are documented in this file.
Version numbers follow [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026 (camera-ready, pending Zenodo DOI mint)

First public release accompanying the ISWC 2026 Resources Track submission
*"SPECTRA: A Traceability Ontology for the 3GPP RAN Standardization Process"*.

### Included

- **Ontology** (`ontology/spectra.ttl`): 26 classes, 53 object properties, 81
  data properties, 887 triples; PROV-O alignment as 6 optional
  `rdfs:subClassOf` axioms; reuses Dublin Core, DCTERMS, FOAF.
- **SHACL shapes** (`shapes/spectra-core.shacl.ttl`): 8 `sh:NodeShape`s
  covering the lifecycle classes; cardinality and range constraints captured
  portably; rationales for shape relaxations (`presentedAt`, `modifies`,
  `originatedFrom`, `sentTo`) annotated inline.
- **PyLODE HTML documentation** (`docs/spectra.html`).
- **SpectraCQ v1.0** (`cqs/spectra_cq_v1.0/`): 137 competency questions ×
  {phase, category, NL question, schema area, executable Cypher, verdict};
  separately citable under CC-BY 4.0 with its own CITATION.bib.
- **Representative queries** (`queries/`): 15 Cypher + 6 SPARQL examples
  (132/137 SpectraCQ Cypher queries are 1:1 portable to SPARQL via the same
  schema; the 6 SPARQL examples illustrate this for the most-cited
  scenarios).
- **Synthetic and metadata-only examples**: end-to-end synthetic 4-hop
  traceability scenario (`examples/end_to_end/`); metadata-only real-world
  mini sample of one RAN1 meeting (`examples/real_world_mini/`); cross-WG
  process KG over RAN1–RAN5 (`examples/process_kg/`; LS routing 195K
  triples, CR routing 1.25M triples, RAN1 TDoc structural metadata 991K
  triples; 2.44M-triple union conforms to the SHACL shapes with zero
  violations).
- **Per-WG body-text KGs** (`kg/per_wg/`): sentence-level rendered text
  retained with 3GPP attribution per the project's Terms-of-Use note,
  following the same redistribution framing as TSpec-LLM
  (Nikbakht et al., 2024) and the GSMA `telecom-kg-rel19` release.
- **Sanitized parsing pipeline source** (`pipeline/`): 5-stage recipe
  (scrape → metadata parse → CR/TR document parse via `python-docx` →
  SHACL → bulk Neo4j load); company-internal monitoring/auth wrappers
  removed.
- **Reproducibility tests** (`tests/verify_release.py`): 25/25
  deterministic checks across 9 sections (TTL parse + 887 triples;
  instantiation snippet SHACL conformance; process-KG union SHACL
  conformance; end-to-end SPARQL; SpectraCQ counts/verdict; structural
  metrics; manifest references; anonymization scope; release directory
  inventory). Depends only on `rdflib` and `pyshacl`; runs in any
  Python 3.10+ environment with no Samsung-internal infrastructure
  required.
- **Validation evidence** (`validation/`): 10 JSON files +
  `validation_manifest.md` mapping every quantitative claim in the paper
  to its supporting evidence file.
- **Croissant metadata** (`cqs/spectra_cq_v1.0/croissant.json`):
  ML Commons Croissant 1.0 dataset description for the SpectraCQ
  competency-benchmark dataset, enabling discovery in dataset registries
  (Hugging Face, Zenodo, Google Dataset Search).
- **License**: two-tier — SPECTRA-authored components under CC-BY 4.0;
  bundled per-WG body-text KGs are 3GPP-derived literals retained with
  3GPP attribution under applicable ETSI/3GPP terms (see `LICENSE`).

### Not bundled

- **Raw Neo4j instance dumps** (`.dump`): exceed the Zenodo size cap;
  regenerable from `kg/per_wg/` plus `pipeline/`.
- **VectorDB embeddings** (used internally for retrieval-augmented CQ
  answering): planned for a subsequent minor release; regenerable
  deterministically from the bundled body-text KGs and a documented
  embedding configuration.

### Conventions

- Version numbers in this changelog refer to the release package
  (`release_package/`); SpectraCQ has its own version number tracked in
  `cqs/spectra_cq_v1.0/citation.bib`.
- Authoritative version of the ontology is in the file header of
  `ontology/spectra.ttl` (the `owl:versionInfo` triple).
